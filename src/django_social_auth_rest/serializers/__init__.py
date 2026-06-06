"""
django_social_auth_rest.serializers
====================================

This module defines the serializers for handling social authentication
and account linking/unlinking in the Django application.
"""

from django.contrib.auth import get_user_model
from rest_framework import serializers
from uuid import uuid4

from ..models import SocialAccountLinked


User = get_user_model()


# ===========================================================
# LINK STATUS SERIALIZERS
# ===========================================================


class ProviderWithLinkedStatusSerializer(serializers.Serializer):
    """Serializer for representing a social authentication provider along with its linked status."""

    label = serializers.CharField()
    is_linked = serializers.BooleanField()


class SocialAccountLinkedSerializer(serializers.Serializer):
    """Serializer for representing the linked status of all social authentication providers for a user."""

    providers = ProviderWithLinkedStatusSerializer(many=True)


# ===========================================================
# BASE SERIALIZERS
# ===========================================================


class BaseAuthStateSerializer(serializers.Serializer):
    """Base serializer for handling the state parameter in social authentication flows."""

    state = serializers.CharField(read_only=True)


class BaseSocialAuthSerializer(serializers.Serializer):
    """Base serializer for handling social authentication flows."""

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
    """Base serializer for handling account unlinking flows."""

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
