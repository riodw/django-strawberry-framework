"""``OrderSet`` + ``OrderSetMetaclass`` - declaration, validation, and the apply pipeline.

The metaclass is a verbatim port of
``django_graphene_filters/orderset.py::OrderSetMetaclass``; ``OrderSet``
mixes the cookbook's cycle-safe ``get_fields`` (the Layer-4 expansion)
over ``ClassBasedTypeNameMixin`` from ``..sets_mixins``.

On top of that skeleton the module carries:

- The ``"__all__"`` expansion via the
  ``_get_concrete_field_names_for_order`` walk per spec-028.
- The resolver-facing classmethod pair ``apply_sync`` /
  ``apply_async`` (no ``apply(...)`` dispatcher per Spec DoD 4(c)).
- The classmethod permission pipeline, inherited from
  ``ActiveInputPermissionMixin`` (``_run_permission_checks`` /
  ``_active_permission_targets`` / ``_active_permission_field_paths`` /
  ``_invoke_permission_method`` / ``_request_from_info``) that drives
  active-input-only per-field ``check_<field>_permission`` dispatch per
  Spec Decision 8 step 6.
- The cookbook-style ``get_flat_orders`` classmethod walking the
  normalized data structure.
"""

from __future__ import annotations

from collections import OrderedDict
from typing import TYPE_CHECKING, Any, ClassVar

from django.db import models

from ..exceptions import ConfigurationError
from ..sets_mixins import (
    ActiveInputPermissionAttrs,
    ActiveInputPermissionMixin,
    ClassBasedTypeNameMixin,
    SetLifecycleAttrs,
    collect_related_declarations,
    expanded_once,
    should_cache_expansion,
)
from ..utils.inputs import promote_set_meta_fields, read_set_meta_fields
from ..utils.querysets import run_in_one_sync_boundary
from ..utils.relations import path_traverses_to_many as _path_traverses_to_many
from ..utils.strings import flatten_lookup_path
from .base import RelatedOrder
from .inputs import (
    Ordering,
    _field_specs,
    _get_concrete_field_names_for_order,
    normalize_input_value,
)

if TYPE_CHECKING:  # pragma: no cover - type-checking-only import.
    from ..types.definition import DjangoTypeDefinition


class OrderSetMetaclass(type):
    """Discover ``RelatedOrder`` declarations and bind them to the new class.

    Direct port of
    ``django_graphene_filters/orderset.py::OrderSetMetaclass``. Inherited
    ``related_orders`` are collected in MRO order with the current class's
    own declarations overriding same-named inherited ones (standard Python
    MRO semantics); every collected ``RelatedOrder`` is bound back to the
    new class via ``bind_orderset``. ``Meta.fields`` resolution is
    ``utils/inputs.py::promote_set_meta_fields`` (no cookbook synonym;
    shared write-back with ``FilterSetMetaclass``).
    """

    def __new__(
        cls: type[OrderSetMetaclass],
        name: str,
        bases: tuple,
        attrs: dict,
    ) -> OrderSetMetaclass:
        """Build the class, collect ``RelatedOrder`` declarations, bind owner."""
        # No cookbook ``order_fields`` synonym (``fields_alias=None``); the
        # call still goes through the shared write-back so FilterSet / OrderSet
        # class Meta cannot grow divergent field-fingerprint rules.
        promote_set_meta_fields(attrs.get("Meta"))
        new_class = super().__new__(cls, name, bases, attrs)

        # Collect the ``RelatedOrder`` declarations and bind each to the new
        # class via the shared set-family collector. The
        # plain ``type`` metaclass does no MRO merge, so
        # ``inherit_from_bases=True`` copies each base's ``related_orders``
        # first (reverse iteration lets earlier bases win) before the class
        # body's own ``attrs`` override - the cookbook lines 30-38 behavior.
        collect_related_declarations(
            new_class,
            bases,
            own_items=attrs.items(),
            declaration_type=RelatedOrder,
            collection_attr="related_orders",
            inherit_from_bases=True,
        )
        return new_class


class OrderSet(ClassBasedTypeNameMixin, ActiveInputPermissionMixin, metaclass=OrderSetMetaclass):
    """Consumer-facing ``OrderSet`` foundation.

    Layer-3 + Layer-4 + resolver-API port of
    ``django_graphene_filters/orderset.py::AdvancedOrderSet``. Inherits
    ``type_name_for`` from ``ClassBasedTypeNameMixin`` (the shared
    ``{cls.__name__}InputType`` naming rule), the Decision-8 permission
    facade from ``ActiveInputPermissionMixin``, and its
    ``related_orders`` collection via ``OrderSetMetaclass``.

    The resolver-facing surface is the classmethod pair ``apply_sync`` /
    ``apply_async`` per spec-028 Decision 8 step 7. Each carries ``info``
    end-to-end so per-field ``check_<field>_permission`` gates and
    active-input-only scope run consistently. There is **no**
    ``apply(...)`` dispatcher (Spec DoD 4(c) -- the filter side's
    ``apply`` exists to translate a sync-misuse ``RuntimeError`` raised
    when a ``RelatedFilter`` target declares an async ``get_queryset``;
    the order side has no equivalent code path).

    The order side does NOT override ``_field_type_suffix`` -- the
    cookbook's upstream ``AdvancedOrderSet`` keeps the default
    ``"InputType"`` for both root and per-field suffixes (the cookbook
    declares both explicitly at the same value; this port relies on the
    mixin defaults instead). This is the deliberate divergence from
    ``FilterSet`` (which overrides to ``"FilterInputType"`` for the
    per-field operator-bag types); the order side has no per-field
    operator bag.
    """

    # Binding seam - populated by ``finalize_django_types`` phase 2.5 in
    # per spec-028 Decision 6. The slot's existence is the contract here;
    # the binding write lands with the field factory. Same shape as the
    # filter side's ``FilterSet._owner_definition``.
    _owner_definition: DjangoTypeDefinition | None = None

    # Cache for fully-resolved fields per Layer 4 of spec-028 Decision 3.
    _expanded_fields = None
    # Recursion guard around ``get_fields`` so a self-referential
    # ``RelatedOrder`` does not blow the stack. The slot stays in place
    # for future defensive use even though the expansion removes
    # the explicit reentry-branch test from ``_expand_meta_fields`` (per
    # the planning-pass disposition -- the branch was structurally
    # unreachable through the shipped surface).
    _is_expanding_fields = False

    # Family binding-state descriptor: the single source for the lifecycle attr
    # names ``get_fields`` (via ``expanded_once``) and ``registry.clear()`` (via
    # ``clear_order_input_namespace``'s ``binding_attrs``) reference, instead of
    # re-spelling the tuple.
    # Mirrors ``FilterSet._lifecycle`` with the order-side slot names.
    _lifecycle: ClassVar[SetLifecycleAttrs] = SetLifecycleAttrs(
        owner="_owner_definition",
        cache="_expanded_fields",
        guard="_is_expanding_fields",
    )

    # Family permission-facade config: shared with ``FilterSet`` through
    # ``ActiveInputPermissionMixin``. Order inputs are a top-level list with
    # ``None`` (not ``UNSET``) for omitted fields, no operator-bag logic keys.
    _permission: ClassVar[ActiveInputPermissionAttrs] = ActiveInputPermissionAttrs(
        family_label="OrderSet",
        related_attr="related_orders",
        target_attr="orderset",
        field_specs=_field_specs,
        handle_top_level_list=True,
    )

    @classmethod
    def get_fields(cls) -> OrderedDict:
        """Return ``Meta.fields`` expansion merged with ``related_orders``.

        Direct port of
        ``django_graphene_filters/orderset.py::AdvancedOrderSet.get_fields``
        (cookbook lines 265-285) with the same two-condition cache write
        gate the filter side uses at ``FilterSet.get_filters``:

        - ``cls.__dict__.get("_expanded_fields")`` is checked directly
          (NOT via ``getattr``) so a subclass does not inherit a parent's
          completed cache via MRO.
        - the cache is only written when ``related_orders`` is on this
          class's ``__dict__`` AND every ``_orderset`` is a real class
          (no unresolved string forward references remain).

        ``Meta.fields = "__all__"`` expands via
        ``_get_concrete_field_names_for_order``
        (spec-028 Decision 3).
        """

        def _build() -> OrderedDict:
            fields = cls._expand_meta_fields()
            for k, v in getattr(cls, "related_orders", {}).items():
                fields[k] = v

            # The two-condition cache-write gate (own ``related_orders`` +
            # no unresolved string lazy targets) is single-sited in
            # ``sets_mixins.should_cache_expansion``.
            if should_cache_expansion(
                cls,
                related_attr="related_orders",
                target_slot="_orderset",
            ):
                cls._expanded_fields = fields
            return fields

        # The class-level expansion cache + reentry-guard skeleton is shared with
        # ``FilterSet.get_filters`` through ``sets_mixins.expanded_once``.
        # The order side passes no ``on_reentry``: its
        # expansion never re-enters ``get_fields`` (the filter side's
        # self-referential-cycle fallback has no order analogue).
        return expanded_once(
            cls,
            cache_attr=cls._lifecycle.cache,
            guard_attr=cls._lifecycle.guard,
            build=_build,
        )

    @classmethod
    def _expand_meta_fields(cls) -> OrderedDict:
        """Expand ``Meta.fields`` into an ``OrderedDict`` keyed by field name.

        Supports list / tuple form (``["title", "subtitle"]``) and the
        ``"__all__"`` shorthand (every column-backed model field name
        per spec-028 -- forward FK columns are included,
        M2M managers and reverse FKs are excluded). Unordered ``set`` /
        ``frozenset`` declarations expand in the same ``repr``-sorted order
        Layer-6 factory kwargs hash (``read_set_meta_fields``).
        """
        fields: OrderedDict = OrderedDict()
        meta = getattr(cls, "Meta", None)
        # Shared reader with Layer-6 factory kwargs: synonym resolve + unordered
        # ``set`` / ``frozenset`` canonicalization. No write-back here -- the
        # metaclass owns alias promotion; expansion must not mutate class Meta.
        meta_fields = read_set_meta_fields(meta)
        if meta_fields is None:
            return fields
        if meta_fields == "__all__":
            # ``_get_concrete_field_names_for_order`` is imported at module
            # level with the other ``.inputs`` symbols; ``inputs.py`` only
            # TYPE_CHECKING-imports ``OrderSet``, so the runtime cycle stays
            # inert without a deferred local import.
            model = getattr(meta, "model", None)
            if model is None:
                raise ConfigurationError(
                    f"{cls.__name__}.Meta.fields = '__all__' requires Meta.model "
                    "so the column-backed field names can be derived from "
                    "model._meta.get_fields().",
                )
            for name in _get_concrete_field_names_for_order(model):
                fields[name] = None
            return fields
        # Cookbook line 279-280: "Works for both dict (iterates keys) and
        # list/tuple (iterates values)." Order's ``Meta.fields`` is
        # list-only per spec-028 Decision 3 Layer 4, but the iteration
        # pattern works either way.
        for k in meta_fields:
            fields[k] = None
        return fields

    # ------------------------------------------------------------------
    # Resolver-facing API (spec-028 Decision 8)
    # ------------------------------------------------------------------

    @classmethod
    def _normalize_input(cls, input_value: Any) -> list[tuple[str, Ordering | None]]:
        """Delegate to ``normalize_input_value`` so callers see one entry point.

        Thin classmethod-shaped delegate kept for parity with
        ``FilterSet._normalize_input``. The filter side's classmethod
        returns a dict (form-data shape); the order side returns a
        flat ``[(field_path, Ordering | None), ...]`` list because the
        order pipeline produces ``OrderBy`` expressions directly rather
        than threading form-data through ``django-filter``'s form
        machinery.
        """
        return normalize_input_value(cls, input_value)

    @classmethod
    def get_flat_orders(
        cls,
        order_data: list[tuple[str, Ordering | None]],
        prefix: str = "",
    ) -> list[tuple[str, Ordering | None]]:
        """Walk normalized order data into flat ``(field_path, direction)`` tuples.

        Port of
        ``django_graphene_filters/orderset.py::AdvancedOrderSet.get_flat_orders``
        (cookbook lines 115-170) with two adaptations:

        - cookbook's DISTINCT ON tuple-half dropped (spec-028 Decision 12
          -- no DISTINCT ON surface ships).
        - return shape changed from ``list[str]`` (cookbook's
          ``"-name"`` bare-string form) to
          ``list[tuple[str, Ordering | None]]`` (Spec Decision 5's
          ``OrderBy``-via-``Ordering.resolve`` discipline).

        ``prefix`` exists for cookbook-shape symmetry: callers who pass
        pre-walked normalized data (the output of
        ``normalize_input_value``) get a pass-through that re-applies
        the prefix per element. The apply pipeline calls
        ``cls._normalize_input(input_value)`` first and then
        ``cls.get_flat_orders(data)`` against the normalized data, so
        ``prefix`` is empty in the common path. Future callers that
        walk a partially-prefixed subtree can pass an explicit prefix
        (e.g., ``"shelf__"``) and the helper concatenates it.
        """
        result: list[tuple[str, Ordering | None]] = []
        for field_path, direction in order_data:
            result.append((f"{prefix}{field_path}", direction))
        return result

    @classmethod
    def _resolve_order_expressions(
        cls,
        flat_orders: list[tuple[str, Ordering | None]],
        *,
        model: type[models.Model],
    ) -> tuple[dict[str, Any], list]:
        """Build ``(annotations, order_expressions)`` from flat ``(path, direction)`` pairs.

        A term whose ``field_path`` traverses a **to-many** relation (reverse FK
        or M2M -- ``_path_traverses_to_many``) is ordered by an AGGREGATE of the
        child column rather than the raw fan-out path: ``Min`` for an ascending
        direction, ``Max`` for a descending one, applied through an
        ``.annotate(<alias>=Min/Max(path))`` and then ordered by ``<alias>``. A
        raw ``order_by("rel__col")`` across a to-many relation adds a JOIN that
        multiplies parent rows (one per matching child), which silently
        duplicates / skips nodes under the connection's positional cursors and
        inflates ``totalCount``; the aggregate keeps exactly one row per parent
        (the annotation forces a GROUP BY on the parent), so cursors index
        distinct nodes and ``.count()`` counts distinct parents
        (``spec-030-connection_field-0_0_9`` P1-B). Scalar columns and to-one
        relation paths (forward FK / O2O, reverse O2O -- which never
        multiply) are ordered directly, unchanged.

        NULLS positioning carries onto the aggregate's ``OrderBy`` because the
        alias is resolved through the same ``Ordering.resolve``; mixed scalar +
        to-many terms in one ``orderBy`` annotate independently and compose.

        Connection pagination preserves this shape without stacking incompatible
        query layers. A root ``DjangoConnectionField`` applies this grouped
        queryset before its normal cursor slice. A synthesized nested relation
        connection carrying ``orderBy:`` is deliberately not window/lateral
        planned and runs the per-parent connection pipeline instead. Therefore a
        to-many aggregate order never sits below the optimizer's
        ``_dst_row_number`` window annotation; both SQLite and PostgreSQL execute
        the grouped root page or the unwindowed nested fallback directly.

        ``model`` is the concrete ``queryset.model`` supplied by
        ``_apply_orderings``. Order paths execute against that queryset, so its
        model is the only authoritative metadata root: ``Meta.model`` may be
        absent for a related-only set, or may name a base model while a valid
        direct caller applies the set to a concrete descendant carrying
        additional relations. Inferring from class/binding metadata makes
        correctness depend on declaration history and can miss a concrete
        to-many path, leaving the raw fan-out join this method exists to prevent.
        """
        annotations: dict[str, Any] = {}
        expressions: list = []
        for index, (field_path, direction) in enumerate(flat_orders):
            if direction is None:
                continue
            if _path_traverses_to_many(model, field_path):
                # ``flatten_lookup_path``: LOOKUP_SEP must never survive into a
                # generated alias (one owner for the mangle).
                alias = f"_dst_order_{index}_{flatten_lookup_path(field_path)}"
                # Ascending vs descending: ``Ordering.is_ascending`` (same rule
                # ``Ordering.resolve`` uses) picks Min / Max for the aggregate.
                aggregate = models.Min if direction.is_ascending else models.Max
                annotations[alias] = aggregate(field_path)
                expressions.append(direction.resolve(alias))
            else:
                expressions.append(direction.resolve(field_path))
        return annotations, expressions

    @classmethod
    def _apply_orderings(cls, input_value: Any, queryset: models.QuerySet) -> models.QuerySet:
        """Apply the normalized orderings to ``queryset`` - the un-colored tail.

        The shared body behind ``apply_sync`` / ``apply_async`` (the order-side
        mirror of the filter side's ``_apply_common_prelude`` /
        ``_apply_common_finalize`` split): normalize the input -> empty-out ->
        ``get_flat_orders`` -> ``_resolve_order_expressions`` (``None``
        directions filtered; to-many paths ordered via the row-preserving
        ``Min`` / ``Max`` aggregate annotation) -> conditional
        ``annotate(**annotations)`` -> ``order_by(*expressions)``; a term-less
        input returns ``queryset`` unchanged. Omitted fields and explicit
        GraphQL ``null`` directions both produce no term, preserving any
        pre-existing queryset order. Pure Python parsing + queryset-method calls
        that do no I/O, so the sync and async colorings differ ONLY in the
        permission-check coloring they run before this.
        """
        data = cls._normalize_input(input_value)
        if not data:
            return queryset
        flat_orders = cls.get_flat_orders(data)
        annotations, expressions = cls._resolve_order_expressions(
            flat_orders,
            model=queryset.model,
        )
        if not expressions:
            return queryset
        if annotations:
            queryset = queryset.annotate(**annotations)
        return queryset.order_by(*expressions)

    @classmethod
    def apply_sync(
        cls,
        input_value: Any,
        queryset: models.QuerySet,
        info: Any,
    ) -> models.QuerySet:
        """Sync resolver entry point per spec-028 Decision 8.

        Steps:

        1. Resolve the request via ``_request_from_info``.
        2. Run per-field / per-branch permission checks BEFORE any
           ``order_by(...)`` clause touches the queryset (Spec Decision
           8 step 6 -- denial gates raise pre-mutation).
        3. Normalize the input into a flat
           ``[(field_path, Ordering | None), ...]`` list.
        4. Convert each ``(field_path, direction)`` pair into a Django
           ``OrderBy`` expression via ``_resolve_order_expressions`` --
           scalar / to-one paths order directly via
           ``direction.resolve(field_path)``, while a to-many path orders by an
           aggregate annotation (``Min`` / ``Max``) so the parent row is not
           multiplied (``spec-030-connection_field-0_0_9`` P1-B); ``None``
           directions are filtered (Spec Decision 13 -- null-direction
           edge case).
        5. ``annotate(**annotations)`` (when any to-many term produced one) then
           ``order_by(*expressions)`` when at least one expression survived;
           otherwise return ``queryset`` unchanged.
        """
        request = cls._request_from_info(info)
        cls._run_permission_checks(input_value, request)
        return cls._apply_orderings(input_value, queryset)

    @classmethod
    async def apply_async(
        cls,
        input_value: Any,
        queryset: models.QuerySet,
        info: Any,
    ) -> models.QuerySet:
        """Async sibling of ``apply_sync`` per spec-028 Decision 8 sync/async-split.

        Wraps ``_run_permission_checks`` in ``run_in_one_sync_boundary``
        so a consumer's ``check_*_permission`` hook that performs a
        blocking ORM read does not block the event loop.
        ``get_flat_orders`` and ``queryset.order_by(...)`` are NOT
        wrapped -- they are pure-Python parsing + a queryset-method call
        that does no I/O (per spec-028 Decision 8 step 7).

        The order side has NO equivalent of the filter side's
        ``_derive_related_visibility_querysets_async`` /
        ``_collect_nested_visibility_querysets_async`` work because
        ordering does not re-derive child querysets per branch -- the
        flat ``order_by`` clause already references the relation paths
        directly via Django's ORM walker.
        """
        request = cls._request_from_info(info)
        await run_in_one_sync_boundary(cls._run_permission_checks, input_value, request)
        return cls._apply_orderings(input_value, queryset)
