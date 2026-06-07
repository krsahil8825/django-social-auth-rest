"""
django_social_auth_rest.serializers.google
==========================================

Serializers for Google authentication workflows.

This module provides serializers for authenticating users with Google,
linking Google accounts to existing users, and unlinking previously
connected Google accounts.
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.db import transaction, IntegrityError

from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from rest_framework import serializers

from . import BaseSocialAuthSerializer, BaseUnlinkAuthSerializer
from .. import conf
from ..models import SocialAccountLinked, SocialAccountProvider
from ..utils import is_user_deleted


User = get_user_model()


class BaseGoogleAuthSerializer(BaseSocialAuthSerializer):
    """
    Base serializer for Google authentication flows.

    Handles Google ID token validation and exposes verified user
    information for downstream authentication and account-linking
    operations.
    """

    token = serializers.CharField(write_only=True)

    def validate_token(self, value):
        """
        Validate a Google ID token and extract the authenticated
        user's profile information.
        """

        try:
            user_info = id_token.verify_oauth2_token(
                value,
                google_requests.Request(),
                conf.GOOGLE_CLIENT_ID,
            )

        except ValueError:
            raise serializers.ValidationError("Invalid Google token.")

        email = user_info.get("email")

        if not email:
            raise serializers.ValidationError("Email not found.")

        if not user_info.get("email_verified"):
            raise serializers.ValidationError("Google email is not verified.")

        self.user_info = user_info

        return value


class LoginGoogleAuthSerializer(BaseGoogleAuthSerializer):
    """
    Authenticate a user through Google.

    Returns an existing linked user when available or creates a new
    user account and Google association when necessary.
    """

    def create(self, validated_data):
        """
        Resolve or create a user account from the authenticated
        Google identity.
        """

        email = self.user_info["email"]

        provider_user_id = self.user_info["sub"]

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
                    raise serializers.ValidationError("Account has been deleted.")

                return user

            # Create new user and link social account

            first_name, last_name = self._get_first_and_last_name(
                self.user_info.get("given_name"),
                self.user_info.get("family_name"),
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
                    provider=SocialAccountProvider.GOOGLE,
                    provider_user_id=provider_user_id,
                )
            except IntegrityError:
                raise serializers.ValidationError(
                    "Your Google account is already linked to another user."
                )

            return user


class LinkGoogleAuthSerializer(BaseGoogleAuthSerializer):
    """
    Link a Google account to an authenticated user.
    """

    def create(self, validated_data):
        """
        Create a Google account association for the authenticated user.
        """

        provider_user_id = self.user_info["sub"]

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
                raise serializers.ValidationError(
                    "This Google account is already linked to another user."
                )

            user = self.context["request"].user

            if is_user_deleted(user):
                raise serializers.ValidationError("Account has been deleted.")

            try:
                SocialAccountLinked.objects.create(
                    user=user,
                    provider=SocialAccountProvider.GOOGLE,
                    provider_user_id=provider_user_id,
                )
            except IntegrityError:
                raise serializers.ValidationError(
                    "Your Google account is already linked to another user."
                )

            return user


class UnlinkGoogleAuthSerializer(BaseUnlinkAuthSerializer):
    """
    Remove the Google account association from the authenticated user.
    """

    PROVIDER = SocialAccountProvider.GOOGLE
