"""Type-system subsystem - ``DjangoType``, field/relation conversion, Relay integration, and finalization.

This subpackage re-exports the consumer-facing ``DjangoType`` class so
``from django_strawberry_framework.types import DjangoType`` is the canonical
import path for the consumer-facing ``DjangoType``; the folder layout (seven
sibling modules) is an internal implementation detail. Internal helpers
(``convert_scalar``, ``convert_choices_to_enum``, ``_make_relation_resolver``,
``_attach_relation_resolvers``) stay reachable via their dotted submodule
paths but are not exposed here.

The three re-exports (``DjangoType``, ``SyncMisuseError``, and
``finalize_django_types``) are also exposed at the top-level package
(``django_strawberry_framework``); this folder ``__init__.py`` is the
dotted-path convenience surface for consumers that prefer
``from django_strawberry_framework.types import DjangoType``.

Dependency direction: this subpackage consumes ``django_strawberry_framework
.optimizer`` (FieldMeta, OptimizerHint, plan helpers, framework-wide
logger).  The dependency is one-way at module-import time: the optimizer
subpackage must not import from ``types/`` at the top of any module.  The
single sanctioned exception is an in-function lazy read -
``optimizer/walker.py``'s ``origin_has_custom_id_resolver`` fallback imports
``types.definition`` inside the function to dodge the package-init cycle - a
leaf read that does not reintroduce module-load coupling.  Shared primitives
otherwise belong in ``optimizer/`` or in a sibling utility module.  This
subpackage also consumes leaf helpers from ``..utils`` (``snake_case``,
``pascal_case``, ``RelationKind``, ``relation_kind``); the inverse direction
is bounded by the same rule.
"""

from .base import DjangoType
from .finalizer import finalize_django_types
from .relay import SyncMisuseError

__all__ = ("DjangoType", "SyncMisuseError", "finalize_django_types")
