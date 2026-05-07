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

# TODO(spec-foundation 0.0.4): re-export ``finalize_django_types`` from
# the new ``types/finalizer.py`` module and add it to ``__all__`` so
# ``from django_strawberry_framework.types import finalize_django_types``
# works alongside ``from django_strawberry_framework.types import
# DjangoType``. Symmetry with the package-root re-export in
# ``django_strawberry_framework/__init__.py`` is required by
# ``docs/spec-foundation.md`` "Phased implementation order" step 11.
from .base import DjangoType

__all__ = ("DjangoType",)
