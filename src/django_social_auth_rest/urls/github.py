"""
django_social_auth_rest.urls.github
===================================

URL patterns for GitHub authentication endpoints.
"""

from rest_framework.routers import DefaultRouter

from ..views.github import GithubAuthViewSet


router = DefaultRouter()
router.register(
    r"github",
    GithubAuthViewSet,
    basename="github-auth",
)

urlpatterns = router.urls
