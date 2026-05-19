"""Canonical metadata object for collected ``DjangoType`` classes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from django.db import models

from ..optimizer.field_meta import FieldMeta
from ..optimizer.hints import OptimizerHint


@dataclass
class DjangoTypeDefinition:
    """Collected metadata for a model-backed ``DjangoType`` subclass."""

    origin: type
    model: type[models.Model]
    name: str | None
    description: str | None
    fields_spec: tuple[str, ...] | Literal["__all__"] | None
    exclude_spec: tuple[str, ...] | None
    selected_fields: tuple[Any, ...]
    field_map: dict[str, FieldMeta]
    optimizer_hints: dict[str, OptimizerHint]
    has_custom_get_queryset: bool
    consumer_authored_fields: frozenset[str] = frozenset()
    consumer_annotated_relation_fields: frozenset[str] = frozenset()
    # TODO(spec-015 Slice 1, rev2 L1 — grouped-by-style ordering):
    # Insert here, between the two annotated-* sets and the two
    # assigned-* sets (annotated-relation, annotated-scalar, assigned-
    # relation, assigned-scalar). The existing two assigned-* lines
    # below stay where they are — the cosmetic re-order lands in the
    # same commit:
    #
    #     consumer_annotated_scalar_fields: frozenset[str] = frozenset()
    #
    # Tests in tests/types/test_definition_order.py
    # (test_annotation_only_scalar_override_populates_definition_metadata
    # and the rev6 L2 cross-type cache test) read this set directly.
    consumer_assigned_relation_fields: frozenset[str] = frozenset()
    consumer_assigned_scalar_fields: frozenset[str] = frozenset()
    primary: bool = False
    # TODO(deferred specs; see docs/FEATURES.md): tighten ``Any | None`` to the
    # concrete classes once filtersets/ordersets/aggregates/fields/search ship;
    # update or remove this anchor in the same change that lands each slice.
    filterset_class: Any | None = None
    orderset_class: Any | None = None
    aggregate_class: Any | None = None
    fields_class: Any | None = None
    search_fields: tuple[str, ...] = ()
    # Populated by ``_validate_meta``; consumed by ``finalize_django_types()``
    # Phase 2.5 (Slice 4) as the finalizer's source of truth for base injection.
    interfaces: tuple[type, ...] = ()
    finalized: bool = False
