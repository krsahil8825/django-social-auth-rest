from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("", RedirectView.as_view(pattern_name="docs", permanent=False)),
    path("admin/", admin.site.urls),
    path("api/social-auth/", include("django_social_auth_rest.urls")),
    path("api/social-auth/", include("django_social_auth_rest.urls.github")),
    path("api/social-auth/", include("django_social_auth_rest.urls.google")),
    path("api/djoser/", include("djoser.urls")),
    path("api/djoser/", include("djoser.urls.jwt")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="docs",
    ),
]
