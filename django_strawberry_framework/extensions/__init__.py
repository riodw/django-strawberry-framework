"""Strawberry schema extensions supplied by django-strawberry-framework.

The home of the package's specialized, opt-in ``SchemaExtension``s. The one
current export is :class:`~django_strawberry_framework.extensions.debug.DjangoDebugExtension`
- the development-only response-extensions debug surface. Deliberately NOT
re-exported from the package root: the root's public surface is the always-on
schema-building API, and the subpackage import path itself signals "not part
of the default recipe"::

    from django_strawberry_framework.extensions import DjangoDebugExtension

Eager re-export (docstring + explicit re-export + ``__all__``, the
``utils/__init__.py`` / ``testing/__init__.py`` shape): every import below is
a hard dependency, so there is no soft-dependency boundary to defend and no
lazy-export machinery.
"""

from django_strawberry_framework.extensions.debug import DjangoDebugExtension

__all__ = ["DjangoDebugExtension"]
