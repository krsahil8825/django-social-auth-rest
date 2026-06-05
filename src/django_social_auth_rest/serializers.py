"""
django_social_auth_rest.serializers
====================================

This module defines the serializers for handling social authentication 
and account linking/unlinking in the Django application.
"""

from django.conf import settings as django_settings
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.core.signing import BadSignature, SignatureExpired
from django.db import transaction, IntegrityError

from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from rest_framework import serializers
from uuid import uuid4
import requests as web_requests

from .models import SocialAccountLinked, SocialAccountProvider
from .tokens import verify_state_token


User = get_user_model()


# ===========================================================
# LINK STATUS SERIALIZERS
# ===========================================================


class ProviderWithLinkedStatusSerializer(serializers.Serializer):
    label = serializers.CharField()
    is_linked = serializers.BooleanField()


class SocialAccountLinkedSerializer(serializers.Serializer):
    providers = ProviderWithLinkedStatusSerializer(many=True)


# ===========================================================
# BASE SERIALIZERS
# ===========================================================


class BaseSocialAuthSerializer(serializers.Serializer):
    access = serializers.CharField(read_only=True)
    refresh = serializers.CharField(read_only=True)

    @staticmethod
    def _generate_unique_username(email: str) -> str:
        """Generate a unique username based on the email address."""

        base_username = email.split("@")[0]
        username = base_username

        while User.objects.filter(username=username).exists():
            username = f"{base_username}_{uuid4().hex[:8]}"

        return username

    @staticmethod
    def _get_first_and_last_name(first_name: str, last_name: str, email: str):
        if first_name and last_name:
            return first_name, last_name
        elif first_name and not last_name:
            return first_name, first_name
        else:
            username_part = email.split("@")[0]
            return username_part, username_part


class BaseUnlinkAuthSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True)

    PROVIDER = None

    def validate(self, attrs):
        if self.PROVIDER is None:
            raise NotImplementedError("PROVIDER must be defined in the subclass.")

        user = self.context["request"].user

        if user.is_deleted:
            raise serializers.ValidationError("Account has been deleted.")

        if not user.has_usable_password():
            raise serializers.ValidationError("Password is not set for this account.")

        if not SocialAccountLinked.objects.filter(
            user=user,
            provider=self.PROVIDER,
        ).exists():
            raise serializers.ValidationError(
                f"No linked {self.PROVIDER} account found."
            )

        if not user.check_password(attrs["password"]):
            raise serializers.ValidationError("Incorrect password.")

        return attrs

    def unlink(self):
        user = self.context["request"].user

        SocialAccountLinked.objects.filter(
            user=user,
            provider=self.PROVIDER,
        ).delete()

        return user


# ===========================================================
# GOOGLE SERIALIZERS
# ===========================================================


class BaseGoogleAuthSerializer(BaseSocialAuthSerializer):
    token = serializers.CharField(write_only=True)

    def validate_token(self, value):
        try:
            user_info = id_token.verify_oauth2_token(
                value,
                google_requests.Request(),
                django_settings.GOOGLE_CLIENT_ID,
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


class GoogleAuthSerializer(BaseGoogleAuthSerializer):
    def create(self, validated_data):
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

                if user.is_deleted:
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

            if user.is_deleted:
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
    def create(self, validated_data):

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

            if user.is_deleted:
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


class GoogleUnlinkAuthSerializer(BaseUnlinkAuthSerializer):
    PROVIDER = SocialAccountProvider.GOOGLE


# ===========================================================
# GITHUB SERIALIZERS
# ===========================================================


class GithubAuthStateSerializer(serializers.Serializer):
    state = serializers.CharField(read_only=True)


class BaseGithubAuthSerializer(BaseSocialAuthSerializer):
    code = serializers.CharField(write_only=True)
    state = serializers.CharField(write_only=True)

    GITHUB_ACCESS_TOKEN_URL = "https://github.com/login/oauth/access_token"
    GITHUB_USER_URL = "https://api.github.com/user"
    GITHUB_EMAILS_URL = "https://api.github.com/user/emails"

    @staticmethod
    def _get_access_token(code: str) -> str:
        """Exchange GitHub code for access token."""

        response = web_requests.post(
            BaseGithubAuthSerializer.GITHUB_ACCESS_TOKEN_URL,
            headers={
                "Accept": "application/json",
            },
            data={
                "client_id": django_settings.GITHUB_CLIENT_ID,
                "client_secret": django_settings.GITHUB_CLIENT_SECRET,
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
        """Fetch authenticated GitHub user."""

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
        """Fetch user's primary verified GitHub email."""

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


class GithubAuthSerializer(BaseGithubAuthSerializer):
    def create(self, validated_data):
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

                if user.is_deleted:
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

            if user.is_deleted:
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
    def create(self, validated_data):
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
            if user.is_deleted:
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


class GithubUnlinkAuthSerializer(BaseUnlinkAuthSerializer):
    PROVIDER = SocialAccountProvider.GITHUB
