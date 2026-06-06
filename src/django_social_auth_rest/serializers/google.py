from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.db import transaction, IntegrityError

from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from rest_framework import serializers

from . import BaseSocialAuthSerializer, BaseUnlinkAuthSerializer
from .. import conf
from ..models import SocialAccountLinked, SocialAccountProvider


User = get_user_model()


class BaseGoogleAuthSerializer(BaseSocialAuthSerializer):
    token = serializers.CharField(write_only=True)

    def validate_token(self, value):
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


class UnlinkGoogleAuthSerializer(BaseUnlinkAuthSerializer):
    PROVIDER = SocialAccountProvider.GOOGLE
