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

from .. import conf

from ..models import (
    SocialAccountLinked,
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
