"""
django_social_auth_rest.utils
==============================

This module contains utility functions for the django_social_auth_rest app.
"""

from django.contrib.auth.models import User
from . import conf


def is_user_deleted(user: User) -> bool:
    """Check whether a user is marked as deleted."""

    field_name = conf.SOCIAL_AUTH_USER_DELETED_FIELD

    if not field_name:
        return False

    return bool(getattr(user, field_name, False))
