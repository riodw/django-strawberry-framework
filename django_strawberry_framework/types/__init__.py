"""Type-system subsystem: ``DjangoType``, converters, and relation resolvers.

This subpackage re-exports the consumer-facing ``DjangoType`` class so
``from django_strawberry_framework.types import DjangoType`` is the canonical
import path for the consumer-facing ``DjangoType``; the folder layout (seven
sibling modules) is an internal implementation detail. Internal helpers
(``convert_scalar``, ``convert_choices_to_enum``, ``_make_relation_resolver``,
``_attach_relation_resolvers``) stay reachable via their dotted submodule
paths but are not exposed here.

Both re-exports (``DjangoType`` and ``finalize_django_types``) are also
exposed at the top-level package (``django_strawberry_framework``); this
folder ``__init__.py`` is the dotted-path convenience surface for consumers
that prefer ``from django_strawberry_framework.types import DjangoType``.

Dependency direction: this subpackage consumes ``django_strawberry_framework
.optimizer`` (FieldMeta, OptimizerHint, plan helpers, framework-wide
logger).  The optimizer subpackage must not import back from ``types/``;
shared primitives belong in ``optimizer/`` or in a sibling utility module.
This subpackage also consumes leaf helpers from ``..utils`` (``snake_case``,
``pascal_case``, ``RelationKind``, ``relation_kind``); the inverse direction
is forbidden by the same rule.
"""

from .base import DjangoType
from .finalizer import finalize_django_types

__all__ = ("DjangoType", "finalize_django_types")
