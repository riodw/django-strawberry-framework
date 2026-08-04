"""Strawberry schema extensions supplied by django-strawberry-framework.

The home of the package's ``SchemaExtension``s.

:class:`~django_strawberry_framework.extensions.debug.DjangoDebugExtension` - the
development-only response-extensions debug surface - is deliberately NOT
re-exported from the package root: the root's public surface is the always-on
schema-building API, and the subpackage import path itself signals "not part
of the default recipe"::

    from django_strawberry_framework.extensions import DjangoDebugExtension

:class:`~django_strawberry_framework.extensions.resource_policy.DjangoResourcePolicyExtension`
and
:class:`~django_strawberry_framework.extensions.error_policy.DjangoErrorPolicyExtension`
are the opposite case and ARE root-exported: ``DjangoSchema`` installs both on
every schema it builds, so they are part of the default recipe rather than an
opt-in, and the explicit imports exist only for a consumer assembling a plain
``strawberry.Schema``.

Eager re-export (docstring + explicit re-export + ``__all__``, the
``utils/__init__.py`` / ``testing/__init__.py`` shape): every import below is
a hard dependency, so there is no soft-dependency boundary to defend and no
lazy-export machinery.
"""

from django_strawberry_framework.extensions.debug import DjangoDebugExtension
from django_strawberry_framework.extensions.error_policy import (
    DjangoErrorPolicyExtension,
)
from django_strawberry_framework.extensions.resource_policy import (
    DjangoResourcePolicyExtension,
)

__all__ = ["DjangoDebugExtension", "DjangoErrorPolicyExtension", "DjangoResourcePolicyExtension"]
