"""
django_social_auth_rest.serializers.github
==========================================

Serializers for GitHub authentication workflows.

This module provides serializers for generating OAuth state tokens,
authenticating users with GitHub, linking GitHub accounts to existing
users, and unlinking previously connected GitHub accounts.
"""

import logging

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.core.signing import BadSignature, SignatureExpired
from django.db import IntegrityError, transaction

from rest_framework import serializers
import requests as web_requests

from . import (
    BaseAuthStateSerializer,
    BaseSocialAuthSerializer,
    BaseUnlinkAuthSerializer,
)
from .. import conf
from ..models import SocialAccountLinked, SocialAccountProvider
from ..tokens import verify_state_token
from ..utils import is_user_deleted


logger = logging.getLogger(__name__)

User = get_user_model()


class StateGithubAuthSerializer(BaseAuthStateSerializer):
    """Generate a GitHub OAuth state token."""

    pass


class BaseGithubAuthSerializer(BaseSocialAuthSerializer):
    """
    Base serializer for GitHub authentication flows.

    Handles OAuth state validation and provides helper methods for
    exchanging authorization codes and retrieving GitHub account data.
    """

    code = serializers.CharField(write_only=True)
    state = serializers.CharField(write_only=True)

    GITHUB_ACCESS_TOKEN_URL = "https://github.com/login/oauth/access_token"
    GITHUB_USER_URL = "https://api.github.com/user"
    GITHUB_EMAILS_URL = "https://api.github.com/user/emails"

    @staticmethod
    def _get_access_token(code: str) -> str:
        """Exchange a GitHub authorization code for an access token."""

        try:
            response = web_requests.post(
                BaseGithubAuthSerializer.GITHUB_ACCESS_TOKEN_URL,
                headers={"Accept": "application/json"},
                data={
                    "client_id": conf.GITHUB_CLIENT_ID,
                    "client_secret": conf.GITHUB_CLIENT_SECRET,
                    "code": code,
                },
                timeout=15,
            )
            response.raise_for_status()

        except web_requests.Timeout:
            raise serializers.ValidationError(
                "GitHub took too long to respond. Please try again."
            )

        except web_requests.HTTPError as exc:
            logger.warning(
                "GitHub token exchange failed with HTTP error: %s",
                exc,
            )
            raise serializers.ValidationError(
                "Unable to contact GitHub. Please try again later."
            )

        except web_requests.RequestException as exc:
            logger.warning(
                "GitHub token exchange request failed: %s",
                exc,
            )
            raise serializers.ValidationError(
                "Unable to contact GitHub. Please try again later."
            )

        data = response.json()

        if data.get("error"):
            logger.warning(
                "GitHub token exchange rejected by provider. error=%s description=%s",
                data.get("error"),
                data.get("error_description"),
            )
            raise serializers.ValidationError(
                "GitHub authentication could not be completed."
            )

        access_token = data.get("access_token")

        if not access_token:
            logger.error(
                "GitHub token exchange response did not contain an access token."
            )
            raise serializers.ValidationError(
                "GitHub authentication could not be completed."
            )

        return access_token

    @staticmethod
    def _get_user_data(access_token: str) -> dict:
        """Retrieve profile information for the authenticated GitHub user."""

        try:
            response = web_requests.get(
                BaseGithubAuthSerializer.GITHUB_USER_URL,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json",
                },
                timeout=15,
            )
            response.raise_for_status()

        except web_requests.Timeout:
            raise serializers.ValidationError(
                "GitHub took too long to respond. Please try again."
            )

        except web_requests.HTTPError as exc:
            logger.warning(
                "Failed to retrieve GitHub user profile: %s",
                exc,
            )
            raise serializers.ValidationError(
                "Unable to retrieve your GitHub profile information."
            )

        except web_requests.RequestException as exc:
            logger.warning(
                "GitHub profile request failed: %s",
                exc,
            )
            raise serializers.ValidationError(
                "Unable to retrieve your GitHub profile information."
            )

        return response.json()

    @staticmethod
    def _get_primary_verified_email(access_token: str) -> str:
        """Retrieve the primary verified email address for the GitHub account."""

        try:
            response = web_requests.get(
                BaseGithubAuthSerializer.GITHUB_EMAILS_URL,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json",
                },
                timeout=15,
            )
            response.raise_for_status()

        except web_requests.Timeout:
            raise serializers.ValidationError(
                "GitHub took too long to respond. Please try again."
            )

        except web_requests.HTTPError as exc:
            logger.warning(
                "Failed to retrieve GitHub email addresses: %s",
                exc,
            )
            raise serializers.ValidationError(
                "Unable to retrieve your verified GitHub email address."
            )

        except web_requests.RequestException as exc:
            logger.warning(
                "GitHub email request failed: %s",
                exc,
            )
            raise serializers.ValidationError(
                "Unable to retrieve your verified GitHub email address."
            )

        emails = response.json()

        primary_email = next(
            (
                email.get("email")
                for email in emails
                if email.get("primary") and email.get("verified")
            ),
            None,
        )

        if not primary_email:
            raise serializers.ValidationError(
                "Your GitHub account does not have a primary verified email address."
            )

        return primary_email.lower().strip()

    def validate(self, attrs):
        """
        Validate the OAuth state token and exchange the authorization
        code for a GitHub access token.
        """

        try:
            verify_state_token(
                attrs.get("state"),
                SocialAccountProvider.GITHUB.value,
            )
        except (BadSignature, SignatureExpired) as exc:
            raise serializers.ValidationError(
                "Invalid or expired authentication state."
            ) from exc

        self._access_token = self._get_access_token(attrs.get("code"))

        return attrs


class LoginGithubAuthSerializer(BaseGithubAuthSerializer):
    """
    Authenticate a user using a GitHub account.

    Returns an existing linked user when available or creates a new
    user account and GitHub association when necessary.
    """

    def create(self, validated_data):
        """Resolve or create a user account from the GitHub identity."""

        access_token = self._access_token
        # Clear the access token from the serializer instance to prevent accidental reuse in subsequent operations.
        self._access_token = None

        github_user = self._get_user_data(access_token)

        provider_user_id = github_user.get("id")

        if not provider_user_id:
            raise serializers.ValidationError(
                "GitHub did not return a valid account identifier."
            )

        provider_user_id = str(provider_user_id)

        with transaction.atomic():
            social_link = (
                SocialAccountLinked.objects.select_related("user")
                .filter(
                    provider=SocialAccountProvider.GITHUB,
                    provider_user_id=provider_user_id,
                )
                .first()
            )

            if social_link:
                user = social_link.user

                if is_user_deleted(user):
                    raise serializers.ValidationError(
                        "This account is no longer available."
                    )

                return user

            email = self._get_primary_verified_email(access_token)

            full_name = (github_user.get("name") or "").strip()
            name_parts = full_name.split(maxsplit=1)

            first_name, last_name = self._get_first_and_last_name(
                name_parts[0] if len(name_parts) > 0 else None,
                name_parts[1] if len(name_parts) > 1 else None,
                email,
            )

            try:
                user, _ = User.objects.get_or_create(
                    email=email,
                    defaults={
                        "username": self._generate_unique_username(email),
                        "first_name": first_name,
                        "last_name": last_name,
                        "is_active": True,
                        "password": make_password(None),
                    },
                )
            except IntegrityError:
                user = User.objects.get(email=email)

            if is_user_deleted(user):
                raise serializers.ValidationError(
                    "This account is no longer available."
                )

            try:
                SocialAccountLinked.objects.create(
                    user=user,
                    provider=SocialAccountProvider.GITHUB,
                    provider_user_id=provider_user_id,
                )
            except IntegrityError:
                raise serializers.ValidationError(
                    "This GitHub account is already linked to another user."
                )

            return user


class LinkGithubAuthSerializer(BaseGithubAuthSerializer):
    """Link a GitHub account to an authenticated user."""

    def create(self, validated_data):
        """Create a GitHub account association for the authenticated user."""

        access_token = self._access_token
        self._access_token = None

        provider_user_id = self._get_user_data(access_token).get("id")

        if not provider_user_id:
            raise serializers.ValidationError(
                "GitHub did not return a valid account identifier."
            )

        provider_user_id = str(provider_user_id)

        with transaction.atomic():
            social_link = (
                SocialAccountLinked.objects.select_related("user")
                .filter(
                    provider=SocialAccountProvider.GITHUB,
                    provider_user_id=provider_user_id,
                )
                .first()
            )

            if social_link:
                raise serializers.ValidationError(
                    "This GitHub account is already linked to another user."
                )

            user = self.context["request"].user

            if is_user_deleted(user):
                raise serializers.ValidationError(
                    "This account is no longer available."
                )

            try:
                SocialAccountLinked.objects.create(
                    user=user,
                    provider=SocialAccountProvider.GITHUB,
                    provider_user_id=provider_user_id,
                )
            except IntegrityError:
                raise serializers.ValidationError(
                    "This GitHub account is already linked to another user."
                )

            return user


class UnlinkGithubAuthSerializer(BaseUnlinkAuthSerializer):
    """Remove the GitHub account association from the authenticated user."""

    PROVIDER = SocialAccountProvider.GITHUB
