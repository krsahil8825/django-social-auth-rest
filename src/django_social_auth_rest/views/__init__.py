"""
django_social_auth_rest.views
=============================

Views used by the social authentication system.

This module provides endpoints for social account management and
shared view classes used by provider-specific authentication views.
"""

from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from .. import conf

from ..models import (
    SocialAccountLinked,
)

from ..serializers import (
    SocialAccountLinkedSerializer,
)

from ..throttle import SocialAuthAnonThrottle, SocialAuthUserThrottle


# ===========================================================
# Social account status views
# ===========================================================


class SocialAccountLinkedAPIView(GenericAPIView):
    """
    Return the link status of all enabled social authentication
    providers for the authenticated user.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = SocialAccountLinkedSerializer

    def get(self, request, *args, **kwargs):
        """
        Retrieve the social account link status for the current user.
        """

        linked_providers = set(
            SocialAccountLinked.objects.filter(user=request.user).values_list(
                "provider", flat=True
            )
        )

        providers_status = [
            {
                "label": provider.label,
                "is_linked": provider.value in linked_providers,
            }
            for provider in conf.ENABLED_PROVIDERS
        ]

        serializer = self.get_serializer({"providers": providers_status})

        return Response(serializer.data, status=status.HTTP_200_OK)


# ===========================================================
# Base views
# ===========================================================


class BaseSocialAuthViewSet(GenericViewSet):
    """
    Base viewset for social authentication providers.

    Handles permission selection and request throttling for provider
    authentication, account linking, and unlinking actions.
    """

    public_actions = []
    protected_actions = []

    throttle_classes = [SocialAuthAnonThrottle, SocialAuthUserThrottle]

    def get_permissions(self):
        """
        Return permissions based on the current action.
        """

        if self.action in self.public_actions:
            return [AllowAny()]

        elif self.action in self.protected_actions:
            return [IsAuthenticated()]

        return super().get_permissions()
