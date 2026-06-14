"""
django_social_auth_rest.serializers.google
==========================================

Serializers for Google authentication workflows.

This module provides serializers for authenticating users with Google,
linking Google accounts to existing users, and unlinking previously
connected Google accounts.
"""

import logging

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.db import IntegrityError, transaction

from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from rest_framework import serializers

from . import BaseSocialAuthSerializer, BaseUnlinkAuthSerializer
from .. import conf
from ..models import SocialAccountLinked, SocialAccountProvider
from ..utils import is_user_deleted


logger = logging.getLogger(__name__)

User = get_user_model()


class BaseGoogleAuthSerializer(BaseSocialAuthSerializer):
    """
    Base serializer for Google authentication flows.

    Validates Google ID tokens and exposes verified user
    information for downstream operations.
    """

    token = serializers.CharField(write_only=True)

    def validate_token(self, value):
        """Validate a Google ID token."""

        try:
            user_info = id_token.verify_oauth2_token(
                value,
                google_requests.Request(),
                conf.GOOGLE_CLIENT_ID,
            )

        except ValueError as exc:
            logger.warning(
                "Google ID token validation failed: %s",
                exc,
            )
            raise serializers.ValidationError(
                {"message": "Google authentication could not be completed."}
            )

        email = user_info.get("email")

        if not email:
            logger.warning("Google ID token did not contain an email address.")
            raise serializers.ValidationError(
                {"message": "Unable to retrieve your Google email address."}
            )

        if not user_info.get("email_verified"):
            logger.warning(
                "Google account email is not verified. sub=%s",
                user_info.get("sub"),
            )
            raise serializers.ValidationError(
                {"message": "Your Google account email address is not verified."}
            )

        self._user_info = user_info

        return value


class LoginGoogleAuthSerializer(BaseGoogleAuthSerializer):
    """
    Authenticate a user using a Google account.

    Returns an existing linked user when available or creates a new
    user account and Google association when necessary.
    """

    def create(self, validated_data):
        """Resolve or create a user account from the Google identity."""

        user_info = self._user_info

        self._user_info = None  # Clear reference to user info after use

        email = user_info["email"]
        provider_user_id = user_info["sub"]

        with transaction.atomic():
            social_link = (
                SocialAccountLinked.objects.select_related("user")
                .filter(
                    provider=SocialAccountProvider.GOOGLE,
                    provider_user_id=provider_user_id,
                )
                .first()
            )

            # If social account is already linked, return the associated user

            if social_link:
                user = social_link.user

                if is_user_deleted(user):
                    logger.warning(
                        "Login attempt for deleted account. user_id=%s provider=google",
                        user.pk,
                    )
                    raise serializers.ValidationError(
                        {"message": "This account is no longer available."}
                    )

                return user

            # Create new user and link social account

            first_name, last_name = self._get_first_and_last_name(
                user_info.get("given_name"),
                user_info.get("family_name"),
                email,
            )

            try:
                user, created = User.objects.get_or_create(
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
                logger.warning(
                    "IntegrityError during user creation. Retrying lookup for email=%s",
                    email,
                )
                user = User.objects.get(email=email)
                created = False

            if created:
                logger.info(
                    "Created user through Google authentication. user_id=%s email=%s",
                    user.pk,
                    email,
                )

            if is_user_deleted(user):
                logger.warning(
                    "Login attempt for deleted account. user_id=%s provider=google",
                    user.pk,
                )
                raise serializers.ValidationError(
                    {"message": "This account is no longer available."}
                )

            try:
                SocialAccountLinked.objects.create(
                    user=user,
                    provider=SocialAccountProvider.GOOGLE,
                    provider_user_id=provider_user_id,
                    email_linked=email,
                )

                logger.info(
                    "Linked Google account. user_id=%s sub=%s",
                    user.pk,
                    provider_user_id,
                )

            except IntegrityError:
                logger.warning(
                    "Google account is already linked. sub=%s",
                    provider_user_id,
                )
                raise serializers.ValidationError(
                    {
                        "message": "This Google account is already linked to another user."
                    }
                )

            return user


class LinkGoogleAuthSerializer(BaseGoogleAuthSerializer):
    """Link a Google account to an authenticated user."""

    def create(self, validated_data):
        """Create a Google account association for the authenticated user."""

        user_info = self._user_info

        self._user_info = None  # Clear reference to user info after use

        provider_user_id = user_info["sub"]

        with transaction.atomic():
            social_link = (
                SocialAccountLinked.objects.select_related("user")
                .filter(
                    provider=SocialAccountProvider.GOOGLE,
                    provider_user_id=provider_user_id,
                )
                .first()
            )

            if social_link:
                logger.warning(
                    "Google account is already linked. "
                    "sub=%s existing_user_id=%s attempted_by=%s",
                    provider_user_id,
                    social_link.user_id,
                    self.context["request"].user.pk,
                )
                raise serializers.ValidationError(
                    {
                        "message": "This Google account is already linked to another user."
                    }
                )

            user = self.context["request"].user

            if is_user_deleted(user):
                logger.warning(
                    "Link attempt for deleted account. user_id=%s provider=google",
                    user.pk,
                )
                raise serializers.ValidationError(
                    {"message": "This account is no longer available."}
                )

            try:
                SocialAccountLinked.objects.create(
                    user=user,
                    provider=SocialAccountProvider.GOOGLE,
                    provider_user_id=provider_user_id,
                    email_linked=user_info["email"],
                )

                logger.info(
                    "Linked Google account. user_id=%s sub=%s",
                    user.pk,
                    provider_user_id,
                )

            except IntegrityError:
                logger.warning(
                    "Failed to link Google account due to an integrity "
                    "constraint. sub=%s user_id=%s",
                    provider_user_id,
                    user.pk,
                )
                raise serializers.ValidationError(
                    {
                        "message": "This Google account is already linked to another user."
                    }
                )

            return user


class UnlinkGoogleAuthSerializer(BaseUnlinkAuthSerializer):
    """Remove the Google account association from the authenticated user."""

    PROVIDER = SocialAccountProvider.GOOGLE
