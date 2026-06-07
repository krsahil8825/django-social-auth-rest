"""
django_social_auth_rest.urls.google
===================================

URL patterns for Google authentication endpoints.
"""

from rest_framework.routers import DefaultRouter

from ..views.google import GoogleAuthViewSet


router = DefaultRouter()
router.register(
    r"google",
    GoogleAuthViewSet,
    basename="google-auth",
)

urlpatterns = router.urls
