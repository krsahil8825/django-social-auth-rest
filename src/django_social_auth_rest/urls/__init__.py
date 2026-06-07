"""
django_social_auth_rest.urls
============================

URL patterns for social authentication endpoints.
"""

from django.urls import path

from ..views import (
    SocialAccountLinkedAPIView,
)

urlpatterns = [
    path(
        "linked-accounts/",
        SocialAccountLinkedAPIView.as_view(),
        name="linked-accounts",
    ),
]
