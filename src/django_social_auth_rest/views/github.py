"""
django_social_auth_rest.views.github
====================================

Views for GitHub authentication workflows.

This module provides endpoints for GitHub OAuth state generation,
user authentication, account linking, and account unlinking.
"""

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from . import BaseSocialAuthViewSet
from ..emails import get_account_creation_email_class
from ..models import SocialAccountProvider
from ..serializers.github import (
    StateGithubAuthSerializer,
    LoginGithubAuthSerializer,
    LinkGithubAuthSerializer,
    UnlinkGithubAuthSerializer,
)
from ..tokens import generate_state_token


class GithubAuthViewSet(BaseSocialAuthViewSet):
    """
    Viewset for GitHub authentication and account management actions.
    """

    public_actions = ["login", "state"]
    protected_actions = ["link", "unlink"]

    def get_serializer_class(self):
        """
        Return the serializer associated with the current action.
        """

        if self.action == "state":
            return StateGithubAuthSerializer
        elif self.action == "login":
            return LoginGithubAuthSerializer
        elif self.action == "link":
            return LinkGithubAuthSerializer
        elif self.action == "unlink":
            return UnlinkGithubAuthSerializer

        return super().get_serializer_class()

    @action(detail=False, methods=["get"])
    def state(self, request, *args, **kwargs):
        """
        Generate an OAuth state token for GitHub authentication.
        """

        serializer = self.get_serializer(
            {"state": generate_state_token(SocialAccountProvider.GITHUB)}
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["post"])
    def login(self, request, *args, **kwargs):
        """
        Authenticate a user with GitHub and return JWT credentials.
        """

        serializer = self.get_serializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        user = serializer.save()

        EmailClass = get_account_creation_email_class()

        if user.last_login is None:
            EmailClass(
                request=request,
                context={"user": user},
            ).send(to=[user.email])

        refresh = RefreshToken.for_user(user)

        serializer = self.get_serializer(
            {"access": str(refresh.access_token), "refresh": str(refresh)}
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["post"])
    def link(self, request, *args, **kwargs):
        """
        Link a GitHub account to the authenticated user.
        """

        serializer = self.get_serializer(data=request.data)

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            status=status.HTTP_204_NO_CONTENT,
        )

    @action(detail=False, methods=["post"])
    def unlink(self, request, *args, **kwargs):
        """
        Remove the GitHub account association from the authenticated user.
        """

        serializer = self.get_serializer(data=request.data)

        serializer.is_valid(raise_exception=True)
        serializer.unlink()

        return Response(
            status=status.HTTP_204_NO_CONTENT,
        )
