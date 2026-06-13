"""``DjangoTypeDefinition`` - canonical metadata for collected ``DjangoType`` classes."""

from __future__ import annotations

from collections.abc import Callable
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
          ``Meta.filterset_class``; consumed by
          ``finalize_django_types()`` phase 2.5 to bind the owning
          ``DjangoTypeDefinition`` on the FilterSet and to materialize
          the generated Strawberry input class as a module global of
          ``django_strawberry_framework.filters.inputs``.
        - ``orderset_class`` is the per-owner ``OrderSet`` sidecar
          populated by ``DjangoType.__init_subclass__`` from
          ``Meta.orderset_class``; consumed by
          ``finalize_django_types()`` phase 2.5 to bind the owning
          ``DjangoTypeDefinition`` on the OrderSet and to materialize
          the generated Strawberry input class as a module global of
          ``django_strawberry_framework.orders.inputs``.
        - ``connection`` is the normalized ``Meta.connection`` value
          (``{"total_count": bool} | None``) populated by
          ``DjangoType.__init_subclass__`` from the validated ``Meta``
          (spec-030 Decision 8); consumed by
          ``connection.py::_connection_type_for`` to decide whether to
          emit the per-target ``<TypeName>Connection`` carrying the
          opt-in ``totalCount`` field.
        - ``relation_shapes`` is the normalized ``Meta.relation_shapes`` value
          (``dict[str, str] | None``, values in ``{"list", "connection",
          "both"}``) normalized by ``types/base.py::_validate_relation_shapes``
          (plus the stage-2 target validator
          ``_validate_relation_shape_targets``), populated by
          ``DjangoType.__init_subclass__`` (spec-032 Decision 7); consumed by
          the ``finalize_django_types()`` Phase-2.5 relation-as-Connection
          synthesis (``types/finalizer.py::_synthesize_relation_connections``)
          to resolve each eligible many-side relation's shape (absent keys
          default to ``"both"``).
        - ``relation_connections`` maps each synthesized relation
          connection's GENERATED Python attribute name to the UNDERLYING
          relation field name (``{"books_connection": "books"}``). Written
          once per attached sibling by the Phase-2.5 synthesis
          (``types/finalizer.py::_synthesize_relation_connections``); the
          suppressed shapes (``"list"`` narrowing, non-Node target,
          consumer-authored) record nothing, so the slot's keys are exactly
          the connections that genuinely exist. Read by
          ``optimizer/walker.py::_walk_selections`` to recognize a nested
          ``<field>Connection`` selection through definition metadata - the
          same channel it uses for ``field_map`` / ``optimizer_hints`` -
          without reaching into ``connection.py`` internals or the
          ``_dst_synthesized_relation_connection`` field marker (spec-033
          Decision 3). Lookup normalizes via the SAME ``snake_case(sel.name)``
          the field-map lookup uses.
        - ``globalid_strategy`` is the raw normalized ``Meta.globalid_strategy``
          value (``"model"`` / ``"type"`` / ``"type+model"`` / a callable /
          ``None``) populated by ``DjangoType.__init_subclass__`` from the
          validated ``Meta`` (spec-031 Decision 6); ``None`` means the per-type
          opt-in is absent and the precedence resolver
          (``types/relay.py::_resolve_globalid_strategy``) falls through to the
          ``RELAY_GLOBALID_STRATEGY`` setting then the ``"model"`` default.
        - ``effective_globalid_strategy`` is the finalization-time encode/decode
          classification string (``"model"`` / ``"type"`` / ``"type+model"`` /
          ``"callable"`` / ``"custom"``), distinct from the raw
          ``globalid_strategy`` slot above (a raw callable value and the resolved
          ``"callable"`` classification string are different things - spec-031
          Decision 10). It is set exactly once by the
          Phase-2.5 ``install_globalid_typename_resolver`` step
          (``types/relay.py``), read by ``decode_global_id`` and the
          strategy-aware ``GlobalID`` filter, and doubles as that step's
          re-entrancy guard (a non-``None`` value means "already processed in a
          prior partial finalize - skip"). ``None`` means "not a
          framework-decodable Relay-Node type" (the install step runs for Relay
          types only): decode rejects such a candidate (spec-031 Decision 8) and
          the filter falls back to node-id-only validation (spec-031 Decision 13).
        - ``related_target_for(field_name)`` resolves the
          ``(target_definition, model_field)`` pair the Decision-4
          owner-aware FK/PK conditional consults; the lookup walks
          ``self.model._meta`` and resolves the target ``DjangoType``
          via ``registry.get(target_model)`` (which itself honors
          ``Meta.primary`` as its first return state, then falls back
          to the single-registered-type rule). Returns ``None`` for
          non-relation fields and for fields not present on the model.
        - ``has_custom_id_resolver_for(pk_name)`` memoizes the
          custom id resolver check used by the optimizer's FK-id
          elision guard. It reports both an ``origin`` MRO-level
          ``resolve_id`` / ``resolve_{pk_name}`` override (ignoring the
          framework-installed Relay default) and a ``relay.NodeID``
          annotation pointing off the pk column; both inputs are stable
          for a definition's lifetime.
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
    orderset_class: type | None = None
    connection: dict | None = None
    # Per-relation shape declaration; values pre-normalized to
    # {"list", "connection", "both"} (spec-032 Decision 7). See the
    # invariants docstring above.
    relation_shapes: dict[str, str] | None = None
    # Walker-readable synthesis slot (spec-033 Decision 3): maps each
    # synthesized connection's GENERATED Python attribute name to the
    # UNDERLYING relation field name (``{"books_connection": "books"}``).
    # See the invariants docstring above for the full read/write contract.
    relation_connections: dict[str, str] | None = None
    globalid_strategy: str | Callable[..., str] | None = None
    # Finalization-set encode/decode classification (spec-031 Decision 10).
    # Unlike the raw ``globalid_strategy`` slot above (populated at class
    # creation), it is set exactly once by the Phase-2.5 typename resolver
    # install (``types/relay.py::install_globalid_typename_resolver``) and
    # doubles as its re-entrancy guard. ``None`` => not a framework-decodable
    # Relay-Node type.
    effective_globalid_strategy: str | None = None
    finalized: bool = False
    # Per-instance memoization of ``related_target_for(field_name)``
    # results. Cache stores the full
    # ``(target_definition, model_field) | None`` tuple keyed by field
    # name (a ``None`` value IS a valid cached result; no in-band
    # sentinel is required). Populated lazily on first call. Definitions are
    # created fresh by ``DjangoType.__init_subclass__`` after every
    # ``registry.clear()`` so stale-cache contamination is bounded to
    # consumer code holding references to discarded definitions -
    # which would surface the same staleness on any direct attribute
    # read.
    _related_target_cache: dict[str, Any] = field(default_factory=dict, repr=False)
    # Per-instance memoization of ``has_custom_id_resolver_for(pk_name)``.
    # Values are keyed by concrete model primary-key field name and include
    # negative results; use membership checks instead of ``dict.get`` so
    # ``False`` remains a valid cached answer.
    _custom_id_resolver_cache: dict[str, bool] = field(default_factory=dict, repr=False)

    @property
    def graphql_type_name(self) -> str:
        """Return the GraphQL type name Strawberry emits for this definition.

        Strawberry derives the surface name as ``self.name`` when set,
        falling back to ``self.origin.__name__``. Centralized here so
        every call site that needs the same derivation rule reads from
        one source - the alternative was three inline copies in
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
        Django relation field - forward FK / OneToOne / M2M, reverse FK
        / OneToOne / M2M). The target ``DjangoType`` is resolved via
        ``registry.get(target_model)`` - the registry's own first
        return state honors ``Meta.primary`` declarations, and the
        fallback path preserves the single-type-no-primary rule.
        Returns ``None`` when no ``DjangoType`` is registered for the
        target model.
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
                    target_type = registry.get(target_model)
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

    def has_custom_id_resolver_for(self, pk_name: str) -> bool:
        """Return whether ``origin`` resolves its id from something other than ``pk_name``.

        Reports the two shapes that make pk-only FK-id elision unsafe:

        - a consumer ``resolve_id`` / ``resolve_{pk_name}`` override (the
          framework-installed Relay default is *not* counted); or
        - a ``relay.NodeID`` annotation pointing at a non-pk column, so the
          GlobalID is built from a column the FK-id stub does not carry.

        Memoized per ``pk_name``; both inputs (MRO class attributes and the
        ``NodeID`` annotation) are stable for the definition's lifetime.
        """
        if pk_name in self._custom_id_resolver_cache:
            return self._custom_id_resolver_cache[pk_name]

        result = origin_has_custom_id_resolver(self.origin, pk_name)
        self._custom_id_resolver_cache[pk_name] = result
        return result


def origin_has_custom_id_resolver(origin: type, pk_name: str) -> bool:
    """Return whether ``origin`` customizes id resolution away from ``pk_name``.

    Shared by ``DjangoTypeDefinition.has_custom_id_resolver_for`` (the memoized
    hot path) and the optimizer's definition-less fallback so the two cannot
    drift. See ``has_custom_id_resolver_for`` for the two shapes detected.
    """
    resolver_names = (pk_name, f"resolve_{pk_name}")
    if any(
        _class_has_custom_id_resolver(cls, name)
        for cls in getattr(origin, "__mro__", ())
        for name in resolver_names
    ):
        return True
    return _resolves_id_off_pk(origin, pk_name)


def _resolves_id_off_pk(origin: type, pk_name: str) -> bool:
    """Return whether a Relay ``NodeID`` maps the id to a non-``pk_name`` column.

    A consumer ``relay.NodeID[...]`` annotation on a non-pk field (e.g.
    ``slug: relay.NodeID[str]``) makes the GlobalID derive from a column the
    FK-id elision stub does not populate, so eliding would silently encode the
    field default instead of the real id. Non-Relay targets (no
    ``resolve_id_attr``) resolve ``id`` straight from the pk and are always
    safe; a Relay target with no ``NodeID`` annotation resolves to ``"pk"`` and
    is likewise safe.
    """
    from strawberry import relay
    from strawberry.relay.exceptions import NodeIDAnnotationError

    if not (isinstance(origin, type) and issubclass(origin, relay.Node)):
        return False
    try:
        id_attr = origin.resolve_id_attr()
    except NodeIDAnnotationError:
        # No ``NodeID`` annotation: the framework default resolves to "pk".
        return False
    return id_attr not in ("pk", pk_name)


def _class_has_custom_id_resolver(type_cls: type, name: str) -> bool:
    """Return whether ``type_cls`` defines a consumer id resolver marker."""
    class_dict = getattr(type_cls, "__dict__", {})
    if name not in class_dict:
        return False
    if name != "resolve_id":
        return True
    descriptor = class_dict[name]
    return not _is_framework_relay_id_resolver(descriptor)


def _is_framework_relay_id_resolver(value: Any) -> bool:
    """Return whether ``value`` is the framework-installed Relay id resolver."""
    from strawberry import relay

    from .relay import _resolve_id_default

    resolver_func = getattr(value, "__func__", value)
    node_default = getattr(relay.Node, "resolve_id", None)
    node_default_func = getattr(node_default, "__func__", None)
    return resolver_func is _resolve_id_default or (
        node_default_func is not None and resolver_func is node_default_func
    )
