"""
django_social_auth_rest.serializers
===================================

Base serializers used throughout the social authentication workflow.

This module provides shared serializer implementations for provider
link-status reporting, OAuth state handling, authentication flows,
and account unlinking operations.
"""

from django.contrib.auth import get_user_model
from rest_framework import serializers
from uuid import uuid4

from ..models import SocialAccountLinked
from ..utils import is_user_deleted


User = get_user_model()


# ===========================================================
# LINK STATUS SERIALIZERS
# ===========================================================


class ProviderWithLinkedStatusSerializer(serializers.Serializer):
    """
    Represents a social authentication provider and whether it is
    currently linked to the user's account.
    """

    label = serializers.CharField()
    is_linked = serializers.BooleanField()


class SocialAccountLinkedSerializer(serializers.Serializer):
    """
    Serializer used to return the linked status of all supported
    social authentication providers for a user.
    """

    providers = ProviderWithLinkedStatusSerializer(many=True)


# ===========================================================
# BASE SERIALIZERS
# ===========================================================


class BaseAuthStateSerializer(serializers.Serializer):
    """
    Base serializer that exposes an OAuth state token used during
    social authentication flows.
    """

    state = serializers.CharField(read_only=True)


class BaseSocialAuthSerializer(serializers.Serializer):
    """
    Base serializer for social authentication providers.

    Provides common fields and helper utilities used when creating
    or authenticating users through external identity providers.
    """

    access = serializers.CharField(read_only=True)
    refresh = serializers.CharField(read_only=True)

    @staticmethod
    def _generate_unique_username(email: str) -> str:
        """
        Generate a unique username derived from the email address.

        If the generated username already exists, a random suffix is
        appended until a unique value is found.
        """

        base_username = email.split("@")[0]
        username = base_username

        while User.objects.filter(username=username).exists():
            username = f"{base_username}_{uuid4().hex[:8]}"

        return username

    @staticmethod
    def _get_first_and_last_name(first_name: str, last_name: str, email: str):
        """
        Determine suitable first and last name values from the
        provider response.

        Falls back to the email username when name information is
        unavailable.
        """

        if first_name and last_name:
            return first_name, last_name
        elif first_name and not last_name:
            return first_name, first_name
        else:
            username_part = email.split("@")[0]
            return username_part, username_part


class BaseUnlinkAuthSerializer(serializers.Serializer):
    """
    Base serializer for unlinking a social authentication provider
    from a user account.

    Subclasses must define the provider identifier through the
    ``PROVIDER`` attribute.
    """

    password = serializers.CharField(write_only=True)

    PROVIDER = None

    def validate(self, attrs):
        """
        Validate that the provider is linked, the account is active,
        and the supplied password matches the authenticated user.
        """

        if self.PROVIDER is None:
            raise NotImplementedError("PROVIDER must be defined in the subclass.")

        user = self.context["request"].user

        if is_user_deleted(user):
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
        """
        Remove the configured social provider association from the
        authenticated user's account.
        """

        user = self.context["request"].user

        SocialAccountLinked.objects.filter(
            user=user,
            provider=self.PROVIDER,
        ).delete()

        return user
