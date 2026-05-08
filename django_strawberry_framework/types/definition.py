"""Canonical metadata object for collected ``DjangoType`` classes."""

from __future__ import annotations

from dataclasses import dataclass, field
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
    consumer_assigned_relation_fields: frozenset[str] = frozenset()
    filterset_class: Any | None = None
    orderset_class: Any | None = None
    aggregate_class: Any | None = None
    fields_class: Any | None = None
    search_fields: tuple[str, ...] = ()
    # TODO(0.0.5 relay interfaces; see docs/spec-relay_interfaces.md):
    # populate this from accepted ``Meta.interfaces`` and keep it as the
    # finalizer's source of truth for Phase 2.5 base injection.
    interfaces: tuple[type, ...] = ()
    finalized: bool = field(default=False)
