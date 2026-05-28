"""Canonical metadata object for collected ``DjangoType`` classes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from django.db import models

from ..optimizer.field_meta import FieldMeta
from ..optimizer.hints import OptimizerHint


@dataclass
class DjangoTypeDefinition:
    """Collected metadata for a model-backed ``DjangoType`` subclass.

    The dataclass is the canonical metadata record consumed by the
    registry, optimizer, finalizer, relay interface injection, and
    relation resolvers. It has a single construction site in
    ``DjangoType.__init_subclass__`` (``types/base.py``).

    Invariants:
        - ``field_map`` is built and owned by
          ``DjangoType.__init_subclass__`` and treated as immutable by
          every reader (walker, extension, resolvers, finalizer). The
          ``dict`` type is a runtime convenience, not a license to
          mutate post-construction.
        - ``selected_fields`` carries Django field instances in
          ``Model._meta.get_fields()`` selection order; readers may
          rely on that order for stable iteration.
        - ``finalized`` flips exactly once, in
          ``finalize_django_types()`` (``types/finalizer.py``), and
          gates the re-finalization short-circuit; no other site may
          assign it.
        - The four ``consumer_*_fields`` frozensets are the four-corner
          override contract (annotated-vs-assigned x relation-vs-scalar)
          described in ``types/base.py``; their union,
          ``consumer_authored_fields``, is the short-circuit input
          ``_build_annotations`` reads to skip auto-synthesis for any
          name the consumer authored.
        - ``primary`` is a write-once introspection mirror of
          ``registry._primaries[model]``, owned by
          ``DjangoType.__init_subclass__`` (``types/base.py``) and never
          mutated post-construction. No package code reads it; the
          runtime "is this the primary?" predicate is
          ``registry.primary_for(model)`` (``registry.py``). Consumers
          may read ``definition.primary`` for introspection only.
    """

    origin: type
    model: type[models.Model]
    name: str | None
    description: str | None
    fields_spec: tuple[str, ...] | Literal["__all__"] | None
    exclude_spec: tuple[str, ...] | None
    selected_fields: tuple[models.Field, ...]
    field_map: dict[str, FieldMeta]
    optimizer_hints: dict[str, OptimizerHint]
    has_custom_get_queryset: bool
    consumer_authored_fields: frozenset[str] = frozenset()
    consumer_annotated_relation_fields: frozenset[str] = frozenset()
    consumer_annotated_scalar_fields: frozenset[str] = frozenset()
    consumer_assigned_relation_fields: frozenset[str] = frozenset()
    consumer_assigned_scalar_fields: frozenset[str] = frozenset()
    primary: bool = False
    interfaces: tuple[type, ...] = ()
    # ``interfaces`` is populated by ``_validate_meta``; consumed by
    # ``finalize_django_types()`` as the finalizer's source of truth for
    # base injection.
    # TODO(spec-021-filters-0_0_8 Slice 3): Add the filter sidecar slot and
    # relation-target lookup that owner-aware FilterSet binding requires.
    # Pseudocode:
    #   filterset_class: type | None = None  # noqa: ERA001
    #   def related_target_for(self, field_name):
    #       field = self.model._meta.get_field(field_name) or return None
    #       if field is not a relation: return None
    #       target_model = field.related_model or field.remote_field.model  # noqa: ERA001
    #       target_type = registry.primary_for(target_model) or only registry type
    #       return (registry.get_definition(target_type), field)  # noqa: ERA001
    finalized: bool = False
