"""
django_social_auth_rest.urls
============================

This module defines the URL patterns for the django_social_auth_rest app,
mapping API endpoints to their corresponding views.
"""

from django.urls import path

from ..views import (
    SocialAccountLinkedAPIView,
)

urlpatterns = [
    path(
        "linked-accounts/", SocialAccountLinkedAPIView.as_view(), name="linked-accounts"
    ),
]
