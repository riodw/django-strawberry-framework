"""Canonical metadata object for collected ``DjangoType`` classes."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

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
        - ``orderset_class`` lands in spec-028 Slice 3 as the ordering
          sidecar mirror of ``filterset_class``. It stays absent until the
          finalizer can apply ``Meta.orderset_class`` end to end; adding the
          slot without the binding pass would violate the deferred-Meta-key
          promotion gate.
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
    # TODO(spec-028-orders-0_0_8 Slice 3): add
    # ``orderset_class: type | None = None`` beside ``filterset_class``.
    # Pseudocode:
    #   - populate it from ``DjangoType.__init_subclass__`` after
    #     ``Meta.orderset_class`` promotion.
    #   - consume it only from ``types.finalizer._bind_ordersets``.
    #   - do not read it from the optimizer or relation resolver paths.
    finalized: bool = False
    # Per-instance memoization of ``related_target_for(field_name)``
    # results. Sentinel key ``"__missing__"`` is unused; we cache the
    # full ``(target_definition, model_field) | None`` tuple keyed by
    # field name. Populated lazily on first call. Definitions are
    # created fresh by ``DjangoType.__init_subclass__`` after every
    # ``registry.clear()`` so stale-cache contamination is bounded to
    # consumer code holding references to discarded definitions —
    # which would surface the same staleness on any direct attribute
    # read.
    _related_target_cache: dict[str, Any] = field(default_factory=dict, repr=False)

    @property
    def graphql_type_name(self) -> str:
        """Return the GraphQL type name Strawberry emits for this definition.

        Strawberry derives the surface name as ``self.name`` when set,
        falling back to ``self.origin.__name__``. Centralized here so
        every call site that needs the same derivation rule reads from
        one source — the alternative was three inline copies in
        ``finalizer.py``, ``filters/base.py``, and ``filters/inputs.py``
        which would silently diverge across renames.
        """
        return self.name if self.name is not None else self.origin.__name__

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
        # In-function imports: dodge the `definition -> registry -> definition`
        # module-load cycle (registry imports DjangoTypeDefinition lazily under
        # TYPE_CHECKING). Do NOT hoist to module top.
        from django.core.exceptions import FieldDoesNotExist

        from ..registry import registry

        # Memoize the lookup per field name. ``_meta.get_field`` is
        # cheap but not free, and the registry lookup involves two
        # dict probes (``primary_for`` + ``get``) plus a third
        # (``get_definition``); on the filter-evaluation hot path this
        # adds up. Cache only valid post-finalize: pre-finalize the
        # registry can still mutate (consumer declares more
        # DjangoTypes), so populating the cache with a transient
        # ``None`` would lock in a wrong answer. ``finalized`` flips
        # exactly once and is the package's "registry is stable now"
        # signal.
        cache_ok = registry.is_finalized()
        if cache_ok and field_name in self._related_target_cache:
            return self._related_target_cache[field_name]

        try:
            model_field = self.model._meta.get_field(field_name)
        except FieldDoesNotExist:
            result = None
        else:
            if not getattr(model_field, "is_relation", False):
                result = None
            else:
                target_model = getattr(model_field, "related_model", None)
                if target_model is None:
                    result = None
                else:
                    target_type = registry.primary_for(target_model) or registry.get(target_model)
                    if target_type is None:
                        result = None
                    else:
                        target_definition = registry.get_definition(target_type)
                        result = (
                            (target_definition, model_field)
                            if target_definition is not None
                            else None
                        )

        if cache_ok:
            self._related_target_cache[field_name] = result
        return result
