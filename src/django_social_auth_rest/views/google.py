"""
django_social_auth_rest.views.google
====================================

Views for Google authentication workflows.

This module provides endpoints for user authentication, account
linking, and account unlinking using Google.
"""

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from . import BaseSocialAuthViewSet
from ..emails import get_account_creation_email_class
from ..serializers.google import (
    LoginGoogleAuthSerializer,
    LinkGoogleAuthSerializer,
    UnlinkGoogleAuthSerializer,
)


class GoogleAuthViewSet(BaseSocialAuthViewSet):
    """
    Viewset for Google authentication and account management actions.
    """

    public_actions = ["login"]
    protected_actions = ["link", "unlink"]

    def get_serializer_class(self):
        """
        Return the serializer associated with the current action.
        """

        if self.action == "login":
            return LoginGoogleAuthSerializer
        elif self.action == "link":
            return LinkGoogleAuthSerializer
        elif self.action == "unlink":
            return UnlinkGoogleAuthSerializer

        return super().get_serializer_class()

    @action(detail=False, methods=["post"])
    def login(self, request):
        """
        Authenticate a user with Google and return JWT credentials.
        """

        serializer = self.get_serializer(data=request.data)

        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = RefreshToken.for_user(user)

        EmailClass = get_account_creation_email_class()

        if EmailClass and user.last_login is None:
            EmailClass(
                request=request,
                context={"user": user},
            ).send(to=[user.email])

        serializer = self.get_serializer(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            }
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["post"])
    def link(self, request):
        """
        Link a Google account to the authenticated user.
        """

        serializer = self.get_serializer(data=request.data)

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            status=status.HTTP_204_NO_CONTENT,
        )

    @action(detail=False, methods=["post"])
    def unlink(self, request):
        """
        Remove the Google account association from the authenticated user.
        """

        serializer = self.get_serializer(data=request.data)

        serializer.is_valid(raise_exception=True)
        serializer.unlink()

        return Response(
            status=status.HTTP_204_NO_CONTENT,
        )
