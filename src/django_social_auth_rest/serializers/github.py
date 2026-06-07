"""
django_social_auth_rest.serializers.github
==========================================

Serializers for GitHub authentication workflows.

This module provides serializers for generating OAuth state tokens,
authenticating users with GitHub, linking GitHub accounts to existing
users, and unlinking previously connected GitHub accounts.
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.core.signing import BadSignature, SignatureExpired
from django.db import transaction, IntegrityError

from rest_framework import serializers
import requests as web_requests

from . import (
    BaseSocialAuthSerializer,
    BaseUnlinkAuthSerializer,
    BaseAuthStateSerializer,
)
from .. import conf
from ..models import SocialAccountLinked, SocialAccountProvider
from ..tokens import verify_state_token
from ..utils import is_user_deleted


User = get_user_model()


class StateGithubAuthSerializer(BaseAuthStateSerializer):
    """
    Serializer used to generate and expose a GitHub OAuth state token.
    """

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
        """
        Exchange a GitHub authorization code for an access token.
        """

        response = web_requests.post(
            BaseGithubAuthSerializer.GITHUB_ACCESS_TOKEN_URL,
            headers={
                "Accept": "application/json",
            },
            data={
                "client_id": conf.GITHUB_CLIENT_ID,
                "client_secret": conf.GITHUB_CLIENT_SECRET,
                "code": code,
            },
            timeout=15,
        )

        response.raise_for_status()

        data = response.json()

        if data.get("error"):
            raise serializers.ValidationError(
                f"GitHub token exchange error: {data.get('error_description', 'Failed to authenticate with GitHub.')}"
            )

        access_token = data.get("access_token")

        if not access_token:
            raise serializers.ValidationError(
                "Access token not found in GitHub response."
            )

        return access_token

    @staticmethod
    def _get_user_data(access_token: str) -> dict:
        """
        Retrieve profile information for the authenticated GitHub user.
        """

        response = web_requests.get(
            BaseGithubAuthSerializer.GITHUB_USER_URL,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
            },
            timeout=15,
        )

        response.raise_for_status()

        return response.json()

    @staticmethod
    def _get_primary_verified_email(access_token: str) -> str:
        """
        Retrieve the user's primary verified email address from GitHub.
        """

        response = web_requests.get(
            BaseGithubAuthSerializer.GITHUB_EMAILS_URL,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
            },
            timeout=15,
        )

        response.raise_for_status()

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
            raise serializers.ValidationError("No primary verified GitHub email found.")

        return primary_email.lower().strip()

    def validate(self, attrs):
        """
        Validate the OAuth state token and exchange the authorization
        code for a GitHub access token.
        """

        try:
            verify_state_token(attrs.get("state"), SocialAccountProvider.GITHUB.value)
        except (BadSignature, SignatureExpired) as exc:
            raise serializers.ValidationError("Invalid state token.") from exc

        try:
            self.access_token = self._get_access_token(attrs.get("code"))

        except web_requests.Timeout:
            raise serializers.ValidationError(
                "GitHub request timed out. Please try again."
            )

        except web_requests.RequestException:
            raise serializers.ValidationError(
                "Failed to exchange code for access token."
            )

        return attrs


class LoginGithubAuthSerializer(BaseGithubAuthSerializer):
    """
    Authenticate a user through GitHub.

    Returns an existing linked user when available or creates a new
    user account and GitHub association when necessary.
    """

    def create(self, validated_data):
        """
        Resolve or create a user account from the authenticated
        GitHub identity.
        """

        github_user = self._get_user_data(self.access_token)

        provider_user_id = github_user.get("id")

        if not provider_user_id:
            raise serializers.ValidationError("GitHub user ID not found.")

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

            # Existing linked account

            if social_link:
                user = social_link.user

                if is_user_deleted(user):
                    raise serializers.ValidationError("Account has been deleted.")

                return user

            # No linked account, create new user and link social account
            
            email = self._get_primary_verified_email(self.access_token)

            full_name = (github_user.get("name") or "").strip()

            name_parts = full_name.split(maxsplit=1)

            first_name, last_name = self._get_first_and_last_name(
                name_parts[0] if len(name_parts) > 0 else None,
                name_parts[1] if len(name_parts) > 1 else None,
                email,
            )

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

            if is_user_deleted(user):
                raise serializers.ValidationError("Account has been deleted.")

            try:
                SocialAccountLinked.objects.create(
                    user=user,
                    provider=SocialAccountProvider.GITHUB,
                    provider_user_id=provider_user_id,
                )
            except IntegrityError:
                raise serializers.ValidationError(
                    "Your GitHub account is already linked to another user."
                )

            return user


class LinkGithubAuthSerializer(BaseGithubAuthSerializer):
    """
    Link a GitHub account to an authenticated user.
    """

    def create(self, validated_data):
        """
        Create a GitHub account association for the authenticated user.
        """

        provider_user_id = self._get_user_data(self.access_token).get("id")

        if not provider_user_id:
            raise serializers.ValidationError("GitHub user ID not found.")

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
                raise serializers.ValidationError("Account has been deleted.")

            try:
                SocialAccountLinked.objects.create(
                    user=user,
                    provider=SocialAccountProvider.GITHUB,
                    provider_user_id=provider_user_id,
                )
            except IntegrityError:
                raise serializers.ValidationError(
                    "Your GitHub account is already linked to another user."
                )

            return user


class UnlinkGithubAuthSerializer(BaseUnlinkAuthSerializer):
    """
    Remove the GitHub account association from the authenticated user.
    """

    PROVIDER = SocialAccountProvider.GITHUB
