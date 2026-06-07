"""
django_social_auth_rest.models
==============================

Database models for storing social account associations and provider
definitions used by the authentication system.
"""

from django.contrib.auth import get_user_model
from django.db import models


User = get_user_model()


class SocialAccountProvider(models.TextChoices):
    """
    Supported social authentication providers.
    """

    GOOGLE = "google", "Google"
    GITHUB = "github", "GitHub"
    # more providers can be added here in the future


class SocialAccountLinked(models.Model):
    """
    Stores the association between a user account and a social
    authentication provider account.
    """

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
        """
        Return a human-readable representation of the linked account.
        """

        return f"{self.user.email} - {self.provider}"
