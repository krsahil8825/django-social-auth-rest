"""
django_social_auth_rest.views
=============================

This module defines the views for the django_social_auth_rest app
"""

from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from . import conf

from ..models import (
    SocialAccountLinked,
    SocialAccountProvider,
)

from ..serializers import (
    SocialAccountLinkedSerializer,
)

from ..throttle import SocialAuthThrottle


# ===========================================
# SOCIAL LINK STATUS VIEWS
# ===========================================


class SocialAccountLinkedAPIView(GenericAPIView):
    """API view to check which social accounts are linked to the authenticated user."""

    permission_classes = [IsAuthenticated]
    serializer_class = SocialAccountLinkedSerializer

    def get(self, request, *args, **kwargs):
        user = request.user

        linked_accounts = SocialAccountLinked.objects.filter(user=user)
        linked_providers = {account.provider for account in linked_accounts}

        providers_status = []

        for provider in SocialAccountProvider:
            if not conf.PROVIDER_ENABLED.get(provider.value, False):
                continue

            providers_status.append(
                {
                    "label": provider.label,
                    "is_linked": provider.value in linked_providers,
                }
            )

        serializer = self.get_serializer({"providers": providers_status})

        return Response(serializer.data, status=status.HTTP_200_OK)


# ===========================================
# BASE VIEWS
# ===========================================


class BaseSocialAuthViewSet(GenericViewSet):
    """Base viewset for handling social authentication flows."""

    public_actions = []
    protected_actions = []

    throttle_classes = [SocialAuthThrottle]

    def get_permissions(self):
        """Return the appropriate permissions based on the action."""

        if self.action in self.public_actions:
            return [AllowAny()]
        elif self.action in self.protected_actions:
            return [IsAuthenticated()]
        return super().get_permissions()
