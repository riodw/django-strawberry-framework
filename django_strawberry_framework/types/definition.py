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
        - ``filterset_class`` is the per-owner ``FilterSet`` sidecar
          populated by ``DjangoType.__init_subclass__`` from
          ``Meta.filterset_class`` once promoted out of
          ``DEFERRED_META_KEYS``; consumed by
          ``finalize_django_types()`` phase 2.5 to bind the owning
          ``DjangoTypeDefinition`` on the FilterSet and to materialize
          the generated Strawberry input class as a module global of
          ``django_strawberry_framework.filters.inputs``.
        - ``related_target_for(field_name)`` resolves the
          ``(target_definition, model_field)`` pair the Decision-4
          owner-aware FK/PK conditional consults; the lookup walks
          ``self.model._meta`` and resolves the target ``DjangoType``
          via ``registry.primary_for(target_model)`` with a
          ``registry.get(target_model)`` fallback. Returns ``None`` for
          non-relation fields and for fields not present on the model.
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
    filterset_class: type | None = None
    finalized: bool = False

    def related_target_for(
        self,
        field_name: str,
    ) -> tuple[DjangoTypeDefinition, models.Field] | None:
        """Return ``(target_definition, model_field)`` for a relation field.

        Walks ``self.model._meta.get_field(field_name)``; returns
        ``None`` when the field does not exist on the model (caught
        ``FieldDoesNotExist``) and ``None`` when the resolved field is
        not a relation. For a relation, resolves the target model via
        ``field.related_model`` (the canonical attribute on every
        Django relation field — forward FK / OneToOne / M2M, reverse FK
        / OneToOne / M2M). The target ``DjangoType`` is resolved via
        ``registry.primary_for(target_model) or registry.get(target_model)``
        so the owner-aware Decision-4 lookup honors ``Meta.primary``
        declarations without losing the single-type-no-primary fallback.
        Returns ``None`` when no ``DjangoType`` is registered for the
        target model.

        Local imports for ``registry`` and ``FieldDoesNotExist`` keep
        ``types/definition.py`` free of module-load cycles back through
        ``registry`` (which imports ``DjangoTypeDefinition`` lazily
        under ``TYPE_CHECKING``).
        """
        from django.core.exceptions import FieldDoesNotExist

        from ..registry import registry

        try:
            field = self.model._meta.get_field(field_name)
        except FieldDoesNotExist:
            return None
        if not getattr(field, "is_relation", False):
            return None
        target_model = getattr(field, "related_model", None)
        if target_model is None:
            return None
        target_type = registry.primary_for(target_model) or registry.get(target_model)
        if target_type is None:
            return None
        target_definition = registry.get_definition(target_type)
        if target_definition is None:
            return None
        return (target_definition, field)
