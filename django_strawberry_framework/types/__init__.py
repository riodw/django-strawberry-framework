"""Type-system subsystem: ``DjangoType``, converters, and relation resolvers.

This subpackage re-exports the consumer-facing ``DjangoType`` class so
``from django_strawberry_framework.types import DjangoType`` works the same
way the previous flat ``types.py`` module did. Internal helpers
(``convert_scalar``, ``convert_relation``, ``convert_choices_to_enum``,
``_make_relation_resolver``, ``_attach_relation_resolvers``) stay reachable
via their dotted submodule paths but are not exposed here.

Dependency direction: this subpackage consumes ``django_strawberry_framework
.optimizer`` (FieldMeta, OptimizerHint, plan helpers, framework-wide
logger).  The optimizer subpackage must not import back from ``types/``;
shared primitives belong in ``optimizer/`` or in a sibling utility module.
"""

from .base import DjangoType

__all__ = ("DjangoType",)
