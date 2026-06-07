"""
django_social_auth_rest.utils
============================

Utility helpers used throughout the social authentication workflow.
"""

from django.contrib.auth.models import User

from . import conf


def is_user_deleted(user: User) -> bool:
    """
    Determine whether the given user is marked as deleted.
    If no user deletion field is configured, this will always return ``False``.
    """

    field_name = conf.SOCIAL_AUTH_USER_DELETED_FIELD

    if not field_name:
        return False

    return bool(getattr(user, field_name, False))
