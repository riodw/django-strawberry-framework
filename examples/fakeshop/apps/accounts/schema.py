"""Fakeshop GraphQL auth surface (spec-040).

The app is schema-only: it declares the example ``UserType`` over the stock
``auth.User`` plus the four opt-in auth fields, and adds no models or services.
Live behavior is earned in ``examples/fakeshop/test_query/test_auth_api.py``.

``UserType``'s field selection IS the authenticated read surface (spec-040
Decision 8): whatever this type selects is what ``login`` / ``register`` / ``me``
return, so it selects explicitly - never ``fields = "__all__"`` - and keeps
``password`` and the privilege columns (``is_staff`` / ``is_superuser``) off.
"""

import strawberry
from django.conf import settings
from django.contrib.auth import get_user_model
from strawberry import relay

from django_strawberry_framework import DjangoType
from django_strawberry_framework.auth import (
    current_user,
    login_mutation,
    logout_mutation,
    register_mutation,
)


class UserType(DjangoType):
    """The authenticated read surface for ``login`` / ``register`` / ``me``.

    Default-OFF acceptance flag ``FAKESHOP_TEST_USER_LAST_LOGIN`` (the
    ``FAKESHOP_TEST_LOAN_CONNECTION`` idiom): when set, ``last_login`` joins
    the selected columns so a live login can observe the post-login value the
    ``user_logged_in`` signal writes. Read in the ``Meta`` body so a
    project-schema reload under ``override_settings`` re-executes it; when the
    flag is absent the type stays the shipped identity trio.
    """

    class Meta:
        model = get_user_model()
        fields = ("id", "username", "email")
        if getattr(settings, "FAKESHOP_TEST_USER_LAST_LOGIN", False):
            fields = (
                "id",
                "username",
                "email",
                "last_login",
            )
        interfaces = (relay.Node,)


@strawberry.type
class Query:
    """Accounts query surface: the nullable session actor."""

    me = current_user()


@strawberry.type
class Mutation:
    """Accounts mutation surface: the session-auth trio at the AllowAny default."""

    login = login_mutation()
    logout = logout_mutation()
    register = register_mutation()
