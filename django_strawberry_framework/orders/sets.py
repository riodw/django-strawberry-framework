"""``OrderSet`` + ``OrderSetMetaclass`` - declaration, validation, and the apply pipeline.

The metaclass is a verbatim port of
``django_graphene_filters/orderset.py::OrderSetMetaclass``; ``OrderSet``
mixes the cookbook's cycle-safe ``get_fields`` (the Layer-4 expansion)
over ``ClassBasedTypeNameMixin`` from ``..sets_mixins``.

Slice 1 shipped the class skeleton + ``get_fields()`` Layer-4 expansion
with the ``"__all__"`` branch raising ``NotImplementedError``. Slice 2
expands the file to:

- Replace the ``"__all__"`` placeholder with the
  ``_get_concrete_field_names_for_order`` walk per spec-028 Revision 4 B4.
- Add the resolver-facing classmethod pair ``apply_sync`` /
  ``apply_async`` (no ``apply(...)`` dispatcher per Spec DoD 4(c)).
- Add the classmethod permission pipeline
  (``_run_permission_checks`` / ``_active_permission_targets`` /
  ``_active_permission_field_paths`` / ``_invoke_permission_method`` /
  ``_request_from_info``) that drives active-input-only per-field
  ``check_<field>_permission`` dispatch per Spec Decision 8 step 6.
- Add the cookbook-style ``get_flat_orders`` classmethod walking the
  normalized data structure.
"""

from __future__ import annotations

from collections import OrderedDict
from functools import lru_cache
from typing import TYPE_CHECKING, Any, ClassVar

from django.core.exceptions import FieldDoesNotExist
from django.db import models

from ..exceptions import ConfigurationError
from ..sets_mixins import (
    ClassBasedTypeNameMixin,
    SetLifecycleAttrs,
    collect_related_declarations,
    expanded_once,
    should_cache_expansion,
)
from ..utils.permissions import (
    active_permission_targets,
    extract_branch_value,
    invoke_permission_method,
    request_from_info,
    run_active_input_permission_checks,
    verbatim_path,
)
from ..utils.relations import is_many_side_relation_kind, relation_kind
from ..utils.strings import flatten_lookup_path
from .base import RelatedOrder
from .inputs import Ordering, _field_specs, normalize_input_value

if TYPE_CHECKING:  # pragma: no cover - type-checking-only import.
    from ..types.definition import DjangoTypeDefinition


@lru_cache(maxsize=2048)
def _path_traverses_to_many(model: type, field_path: str) -> bool:
    """Return whether an ORM ``field_path`` traverses a to-many relation from ``model``.

    Walks the ``__``-separated path segment by segment. A segment that is a
    to-many relation (reverse FK or forward/reverse M2M -- the
    ``is_many_side_relation_kind`` set) means a raw ``order_by("rel__col")``
    would add a fan-out JOIN that multiplies parent rows (one row per matching
    child). Stops at the first non-relation segment (a terminal scalar column)
    or an unresolvable segment (a transform / lookup), neither of which can
    multiply. Used by ``OrderSet._resolve_order_expressions`` to decide between
    a direct ``order_by`` and the row-preserving aggregate form.

    The answer is pure model metadata for a ``(model, field_path)`` pair, so it
    is cached across requests. The bounded size keeps dynamic test models and
    generated path variants from growing the process without limit; eviction only
    recomputes the same metadata walk.
    """
    current = model
    for segment in field_path.split("__"):
        try:
            field = current._meta.get_field(segment)
        except FieldDoesNotExist:
            return False
        if not getattr(field, "is_relation", False):
            return False
        if is_many_side_relation_kind(relation_kind(field)):
            return True
        related = getattr(field, "related_model", None)
        if related is None:
            return False
        current = related
    return False


class OrderSetMetaclass(type):
    """Discover ``RelatedOrder`` declarations and bind them to the new class.

    Direct port of
    ``django_graphene_filters/orderset.py::OrderSetMetaclass``. Inherited
    ``related_orders`` are collected in MRO order with the current class's
    own declarations overriding same-named inherited ones (standard Python
    MRO semantics); every collected ``RelatedOrder`` is bound back to the
    new class via ``bind_orderset``.
    """

    def __new__(
        cls: type[OrderSetMetaclass],
        name: str,
        bases: tuple,
        attrs: dict,
    ) -> OrderSetMetaclass:
        """Build the class, collect ``RelatedOrder`` declarations, bind owner."""
        new_class = super().__new__(cls, name, bases, attrs)

        # Collect the ``RelatedOrder`` declarations and bind each to the new
        # class via the shared set-family collector (the 0.0.9 DRY pass,
        # ``docs/feedback.md`` Major 3). The plain ``type`` metaclass does no MRO
        # merge, so ``inherit_from_bases=True`` copies each base's
        # ``related_orders`` first (reversed MRO -> later bases win) before the
        # class body's own ``attrs`` override - the cookbook lines 30-38 behavior.
        collect_related_declarations(
            new_class,
            bases,
            own_items=attrs.items(),
            declaration_type=RelatedOrder,
            collection_attr="related_orders",
            inherit_from_bases=True,
        )
        return new_class


class OrderSet(ClassBasedTypeNameMixin, metaclass=OrderSetMetaclass):
    """Consumer-facing ``OrderSet`` foundation.

    Layer-3 + Layer-4 + resolver-API port of
    ``django_graphene_filters/orderset.py::AdvancedOrderSet``. Inherits
    ``type_name_for`` from ``ClassBasedTypeNameMixin`` (the shared
    ``{cls.__name__}InputType`` naming rule) and gets its
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
    # Slice 3 per spec-028 Decision 6. The slot's existence is the Slice 1
    # contract; the binding write lands in Slice 3. Same shape as the
    # filter side's ``FilterSet._owner_definition``.
    _owner_definition: DjangoTypeDefinition | None = None

    # Cache for fully-resolved fields per Layer 4 of spec-028 Decision 3.
    _expanded_fields = None
    # Recursion guard around ``get_fields`` so a self-referential
    # ``RelatedOrder`` does not blow the stack. The slot stays in place
    # for future defensive use even though the Slice 2 expansion removes
    # the explicit reentry-branch test from ``_expand_meta_fields`` (per
    # the planning-pass disposition -- the branch was structurally
    # unreachable through the planned Slice 2 surface).
    _is_expanding_fields = False

    # Family binding-state descriptor: the single source for the lifecycle attr
    # names ``get_fields`` (via ``expanded_once``) and ``registry.clear()`` (via
    # ``clear_order_input_namespace``'s ``binding_attrs``) reference, instead of
    # re-spelling the tuple (the 0.0.9 DRY pass, ``docs/feedback.md`` Major 3).
    # Mirrors ``FilterSet._lifecycle`` with the order-side slot names.
    _lifecycle: ClassVar[SetLifecycleAttrs] = SetLifecycleAttrs(
        owner="_owner_definition",
        cache="_expanded_fields",
        guard="_is_expanding_fields",
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
        ``_get_concrete_field_names_for_order`` (Slice 2's deliverable
        per spec-028 Decision 3 / Revision 4 B4).
        """

        def _build() -> OrderedDict:
            fields = cls._expand_meta_fields()
            for k, v in getattr(cls, "related_orders", {}).items():
                fields[k] = v

            # The two-condition cache-write gate (own ``related_orders`` +
            # no unresolved string lazy targets) is single-sited in
            # ``sets_mixins.should_cache_expansion`` (DRY review A8).
            if should_cache_expansion(
                cls,
                related_attr="related_orders",
                target_slot="_orderset",
            ):
                cls._expanded_fields = fields
            return fields

        # The class-level expansion cache + reentry-guard skeleton is shared with
        # ``FilterSet.get_filters`` through ``sets_mixins.expanded_once`` (the
        # 0.0.9 DRY pass, ``docs/feedback.md`` Major 3). The order side passes no
        # ``on_reentry``: its expansion never re-enters ``get_fields`` (the
        # filter side's self-referential-cycle fallback has no order analogue).
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
        per spec-028 Revision 4 B4 -- forward FK columns are included,
        M2M managers and reverse FKs are excluded).
        """
        fields: OrderedDict = OrderedDict()
        meta = getattr(cls, "Meta", None)
        if meta is None:
            return fields
        meta_fields = getattr(meta, "fields", None)
        if meta_fields is None:
            return fields
        if meta_fields == "__all__":
            # Local import dodges any circular-import risk between
            # ``orders/sets.py`` and ``orders/inputs.py`` (the
            # ``_build_input_fields`` adapter imports ``OrderSet`` from
            # ``.sets``; this local import keeps the runtime cycle inert).
            from .inputs import _get_concrete_field_names_for_order

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
    # Resolver-facing API (Slice 2 / spec-028 Decision 8)
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
    def _request_from_info(cls, info: Any) -> Any:
        """Resolve the Django request from ``info.context``.

        Canonical Strawberry-Django shape: ``info.context.request``. The
        wrapper-less alternative ``isinstance(info.context, HttpRequest)``
        is detected so consumers running a bare-HttpRequest context (the
        Django test client default) work without bespoke wiring. Any
        other shape raises ``ConfigurationError``. Thin delegate to
        ``utils/permissions.py::request_from_info`` (single-sited with the
        filter side per the 0.0.9 DRY pass).
        """
        return request_from_info(info, family_label="OrderSet")

    @staticmethod
    def _extract_branch_value(input_value: Any, field_name: str) -> Any:
        """Return the value at ``field_name`` on a dataclass-or-dict input.

        Collapses ``None`` to "branch not supplied" so the active-branch
        caller treats absent branches uniformly. Mirror of
        ``FilterSet._extract_branch_value`` minus the
        ``strawberry.UNSET`` collapse -- order inputs default unsupplied
        fields to ``None`` rather than UNSET (the apply pipeline never
        sees an UNSET sentinel from the resolver layer because the
        ``order_input_type`` argument shape is ``list[<T>!] | None``,
        not a struct of UNSET-defaulted attributes). Thin delegate to
        ``utils/permissions.py::extract_branch_value`` (no ``unset_sentinel``,
        so the sentinel check is a harmless ``value is None`` no-op).
        """
        return extract_branch_value(input_value, field_name)

    @classmethod
    def _active_permission_field_paths(cls, input_value: Any) -> list[str]:
        """Return the base django source path for each active top-level leaf.

        Drives ``_run_permission_checks``'s per-field gate dispatch. Emits one
        entry per supplied leaf field -- its ``django_source_path`` -- so
        ``check_<field>_permission`` fires once for a field regardless of which
        input list element populates it. ``RelatedOrder`` branches are excluded
        (they fire via the related-branch loop); ``None`` values are skipped
        (active-input-only). Thin delegate to
        ``_active_permission_targets``'s ``LEAF`` half; the order side has no
        logical operator keys and falls back to the python-attr token verbatim
        when a field has no field-spec entry (e.g. permission checks invoked
        outside the apply pipeline before the bind populates ``_field_specs``).
        """
        return cls._active_permission_targets(input_value)[0]

    @classmethod
    def _active_permission_targets(
        cls,
        input_value: Any,
    ) -> tuple[list[str], list[tuple[str, RelatedOrder, Any]]]:
        """Single-pass ``(leaf source paths, active related branches)`` for one level.

        The fused traversal ``_run_permission_checks`` consumes (feedback H3):
        one ``iter_active_fields`` walk yields both the per-field gate paths and
        the active ``RelatedOrder`` branches, instead of two full walks. Thin
        delegate to ``utils/permissions.py::active_permission_targets`` with the
        order family's config (``handle_top_level_list=True`` for the top-level
        list input shape); ``_active_permission_field_paths`` takes the ``LEAF``
        half.
        """
        return active_permission_targets(
            cls,
            input_value,
            field_specs=_field_specs,
            related_attr="related_orders",
            logic_keys=frozenset(),
            fallback_path=verbatim_path,
            handle_top_level_list=True,
        )

    @staticmethod
    def _invoke_permission_method(
        bare_instance: Any,
        field_path: str,
        request: Any,
        *,
        fired: set[str] | None = None,
    ) -> None:
        """Call ``check_<field_path>_permission(request)`` if defined.

        Thin delegate to ``utils/permissions.py::invoke_permission_method``
        (single-sited with the filter side). When ``fired`` is supplied, the
        method name is recorded after a successful fire and subsequent calls
        with the same name skip the attribute lookup -- the per-class set keyed
        out of ``_run_permission_checks``'s shared ``_fired`` map.
        """
        invoke_permission_method(bare_instance, field_path, request, fired=fired)

    @classmethod
    def _run_permission_checks(
        cls,
        input_value: Any,
        request: Any,
        *,
        _fired: dict[type, set[str]] | None = None,
        _bare: Any = None,
    ) -> None:
        """Fire ``check_<field>_permission(request)`` for fields in the input.

        Active-input-only per spec-028 Decision 8 step 6 -- a declared
        ``check_*`` gate that is not exercised by this call leaves the
        queryset untouched. Recurses into the child orderset for each
        active ``RelatedOrder`` branch so the cookbook's
        nested-permission contract holds.

        The order side has NO ``and`` / ``or`` / ``not`` operator-bag
        recursion -- spec-028 Decision 8 line 686 ("no operator-bag, no
        form validation"). The filter side's depth-counter recursion
        cap has no analogue here either: only the related-branch
        recursion remains, and it terminates naturally at the depth of
        the consumer's declared ``RelatedOrder`` chain.

        Permission methods are called via a bare instance allocated
        with ``object.__new__(cls)``; this matches the cookbook
        contract (per-field gates are written as regular
        ``def check_X_permission(self, request)`` methods) without
        requiring a fully-constructed ``OrderSet`` instance.

        Dedup contract: ``_fired`` maps each ``OrderSet`` class to the
        set of ``check_*_permission`` method names that have already
        fired against THAT class in this top-level call. Shared across
        the related-branch recursion (different classes), so a gate
        fires at most once per class regardless of how many input list
        elements reference the same field path.

        Double-dispatch contract: for an active ``RelatedOrder`` branch
        named ``shelf`` both gates fire -- the parent's
        ``check_shelf_permission`` (the per-branch gate on the owning
        orderset) AND the child orderset's own ``check_*_permission``
        gates. They live in different per-class dedup sets, so both
        fire once.
        """
        if input_value is None:
            return
        if _fired is None:
            _fired = {}
        bare = _bare if _bare is not None else object.__new__(cls)
        # Fire the per-field and per-branch gates -- the active-input core shared
        # with the filter side (``utils/permissions.py``): the active-field gate
        # loop, the active-related-branch loop (recurse into the child orderset's
        # own ``_run_permission_checks`` then fire the parent's per-branch gate),
        # and the per-class ``_fired`` dedup. The order side has no logical
        # ``and`` / ``or`` / ``not`` recursion (spec-028 Decision 8) and no depth
        # cap, so this is the whole body.
        run_active_input_permission_checks(
            cls,
            input_value,
            request,
            fired=_fired,
            bare=bare,
            target_attr="orderset",
        )

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
          -- DISTINCT ON deferred to ``0.0.9``).
        - return shape changed from ``list[str]`` (cookbook's
          ``"-name"`` bare-string form) to
          ``list[tuple[str, Ordering | None]]`` (Spec Decision 5's
          ``OrderBy``-via-``Ordering.resolve`` discipline).

        ``prefix`` exists for cookbook-shape symmetry: callers who pass
        pre-walked normalized data (the output of
        ``normalize_input_value``) get a pass-through that re-applies
        the prefix per element. Slice 2's apply pipeline calls
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
        (``docs/feedback.md`` P1-B). Scalar columns and to-one relation paths
        (forward FK / O2O, reverse O2O -- which never multiply) are ordered
        directly, unchanged.

        NULLS positioning carries onto the aggregate's ``OrderBy`` because the
        alias is resolved through the same ``Ordering.resolve``; mixed scalar +
        to-many terms in one ``orderBy`` annotate independently and compose.
        """
        model = getattr(getattr(cls, "Meta", None), "model", None)
        annotations: dict[str, Any] = {}
        expressions: list = []
        for index, (field_path, direction) in enumerate(flat_orders):
            if direction is None:
                continue
            if model is not None and _path_traverses_to_many(model, field_path):
                # ``flatten_lookup_path``: LOOKUP_SEP must never survive into a
                # generated alias (DRY review A9 - one owner for the mangle).
                alias = f"_dst_order_{index}_{flatten_lookup_path(field_path)}"
                aggregate = models.Min if "ASC" in direction.name else models.Max
                annotations[alias] = aggregate(field_path)
                expressions.append(direction.resolve(alias))
            else:
                expressions.append(direction.resolve(field_path))
        return annotations, expressions

    @classmethod
    def _apply_orderings(cls, input_value: Any, queryset: models.QuerySet) -> models.QuerySet:
        """Apply the normalized orderings to ``queryset`` - the un-colored tail (DRY review D1).

        The shared body behind ``apply_sync`` / ``apply_async`` (the order-side
        mirror of the filter side's ``_apply_common_prelude`` /
        ``_apply_common_finalize`` split): normalize the input -> empty-out ->
        ``get_flat_orders`` -> ``_resolve_order_expressions`` (``None``
        directions filtered; to-many paths ordered via the row-preserving
        ``Min`` / ``Max`` aggregate annotation) -> conditional
        ``annotate(**annotations)`` -> ``order_by(*expressions)``; a term-less
        input returns ``queryset`` unchanged. Pure Python parsing + queryset-
        method calls that do no I/O, so the sync and async colorings differ
        ONLY in the permission-check coloring they run before this.
        """
        data = cls._normalize_input(input_value)
        if not data:
            return queryset
        flat_orders = cls.get_flat_orders(data)
        annotations, expressions = cls._resolve_order_expressions(flat_orders)
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
           multiplied (``docs/feedback.md`` P1-B); ``None`` directions are
           filtered (Spec Decision 13 -- null-direction edge case).
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

        Wraps ``_run_permission_checks`` in
        ``sync_to_async(thread_sensitive=True)`` so a consumer's
        ``check_*_permission`` hook that performs a blocking ORM read
        does not block the event loop. ``get_flat_orders`` and
        ``queryset.order_by(...)`` are NOT wrapped -- they are
        pure-Python parsing + a queryset-method call that does no I/O
        (per spec-028 Decision 8 step 7 + N7 of rev1).

        The order side has NO equivalent of the filter side's
        ``_derive_related_visibility_querysets_async`` /
        ``_collect_nested_visibility_querysets_async`` work because
        ordering does not re-derive child querysets per branch -- the
        flat ``order_by`` clause already references the relation paths
        directly via Django's ORM walker.
        """
        from asgiref.sync import sync_to_async

        request = cls._request_from_info(info)
        await sync_to_async(cls._run_permission_checks, thread_sensitive=True)(
            input_value,
            request,
        )
        return cls._apply_orderings(input_value, queryset)
