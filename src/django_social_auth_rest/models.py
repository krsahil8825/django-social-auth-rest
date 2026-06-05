"""
django_social_auth_rest.models
===============================

This module helps to manage the social account linking for users in the Django application.
"""

from django.contrib.auth import get_user_model
from django.db import models


User = get_user_model()


class SocialAccountProvider(models.TextChoices):
    """Enum to represent supported social account providers."""

    GOOGLE = "google", "Google"
    GITHUB = "github", "GitHub"


class SocialAccountLinked(models.Model):
    """Model to represent a linked social account for a user."""

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    provider = models.CharField(max_length=20, choices=SocialAccountProvider.choices)
    provider_user_id = models.CharField(max_length=255, db_index=True)
    linked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["provider", "provider_user_id"],
                name="unique_provider_account",
            ),
            models.UniqueConstraint(
                fields=["user", "provider"],
                name="unique_user_provider",
            ),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.provider}"
