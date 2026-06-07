"""
django_social_auth_rest.email
=============================

Utilities for loading email classes used by the social authentication
workflow.
"""

from django.utils.module_loading import import_string

from .conf import SOCIAL_AUTH_ACCOUNT_CREATION_EMAIL_CLASS


def get_account_creation_email_class():
    """
    Return the configured account creation email class.

    Returns ``None`` when no account creation email class has been
    configured.

    Expected usage:

        >>> EmailClass = get_account_creation_email_class()
        ... if EmailClass and user.last_login is None:
        ...     if EmailClass:
        ...         EmailClass(
        ...             request=request,
        ...             context={"user": user},
        ...         ).send(
        ...             to=[user.email]
        ...         )
    """

    if not SOCIAL_AUTH_ACCOUNT_CREATION_EMAIL_CLASS:
        return None

    return import_string(SOCIAL_AUTH_ACCOUNT_CREATION_EMAIL_CLASS)
