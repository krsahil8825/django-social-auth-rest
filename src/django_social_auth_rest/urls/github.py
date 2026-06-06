"""
django_social_auth_rest.urls.github
===================================

This module defines the URL patterns for GitHub social authentication endpoints
in the django_social_auth_rest app, mapping API endpoints to their corresponding views.
"""

from rest_framework.routers import DefaultRouter
from ..views.github import GithubAuthViewSet

router = DefaultRouter()
router.register(r"github", GithubAuthViewSet, basename="github-auth")

urlpatterns = router.urls
