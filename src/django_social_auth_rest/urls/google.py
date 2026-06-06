"""
django_social_auth_rest.urls.google
===================================

This module defines the URL patterns for Google social authentication endpoints
in the django_social_auth_rest app, mapping API endpoints to their corresponding views.
"""

from rest_framework.routers import DefaultRouter
from ..views.google import GoogleAuthViewSet

router = DefaultRouter()
router.register(r"google", GoogleAuthViewSet, basename="google-auth")

urlpatterns = router.urls
