"""
django_social_auth_rest.email
=============================

This module defines the email-related functionality for the django_social_auth_rest
app, including email sending and configuration.
"""

from django.utils.module_loading import import_string

from .conf import SOCIAL_AUTH_ACCOUNT_CREATION_EMAIL_CLASS


def get_account_creation_email_class():
    """
    Get the email class to be used for account creation emails.

    Expected usage:

        EmailClass = get_account_creation_email_class()
        if EmailClass and user.last_login is None:
            if EmailClass:
                EmailClass(
                    request=request,
                    context={"user": user},
                ).send(
                    to=[user.email]
                )

    Returns:
        type | None: The configured email class, or None if no
        account creation email class is configured.
    """

    if not SOCIAL_AUTH_ACCOUNT_CREATION_EMAIL_CLASS:
        return None

    return import_string(SOCIAL_AUTH_ACCOUNT_CREATION_EMAIL_CLASS)
