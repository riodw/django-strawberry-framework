"""``FilterSet`` + ``FilterSetMetaclass`` - declaration, validation, and the apply pipeline.

Layers 3 and 4 of the spec-027 six-layer pipeline plus the
Decision-8 / M1-of-rev5 named-helper decomposition of `apply_sync` /
`apply_async` / `apply`. The metaclass is a verbatim port of
`django_graphene_filters/filterset.py::FilterSetMetaclass`; `FilterSet`
mixes the cookbook's cycle-safe `get_filters` into a
`django_filters.filterset.BaseFilterSet` subclass per spec-027 Decision 5.

The Decision-4 owner-aware Relay-vs-scalar conditional lives only inside
`filter_for_field` / `filter_for_lookup` to keep the runtime override as
the single source of truth (the factory derives shape from the
resolved filter instances, not from a parallel map).
"""

from __future__ import annotations

import copy
from collections import OrderedDict
from collections.abc import Iterator
from typing import TYPE_CHECKING, Any, ClassVar, NoReturn

from asgiref.sync import sync_to_async
from django.db import models
from django_filters import filterset
from django_filters.utils import get_model_field
from graphql import GraphQLError
from strawberry import UNSET

from ..exceptions import ConfigurationError
from ..registry import registry
from ..sets_mixins import (
    ClassBasedTypeNameMixin,
    SetLifecycleAttrs,
    collect_related_declarations,
    expanded_once,
    should_cache_expansion,
)
from ..types.relay import implements_relay_node
from ..utils.input_values import (
    LOGIC,
    RELATED,
    SetInputTraversal,
    is_inactive_value,
    iter_active_fields,
)
from ..utils.permissions import (
    active_permission_targets,
    active_related_branches,
    extract_branch_value,
    invoke_permission_method,
    iter_input_items,
    request_from_info,
    run_active_input_permission_checks,
)
from ..utils.querysets import (
    SyncMisuseError,
    apply_type_visibility_async,
    apply_type_visibility_sync,
)
from ..utils.relations import (
    is_many_side_relation_kind,
    path_traverses_to_many,
    relation_kind,
)
from .base import GlobalIDFilter, GlobalIDMultipleChoiceFilter, IntegerInFilter, RelatedFilter
from .inputs import _LOGIC_KEYS, LOOKUP_NAME_MAP, _field_specs, normalize_input_value

# Python-attr tokens of the logical operator keys (``and_`` / ``or_`` / ``not_``),
# excluded from the active-permission field walk (they recurse separately).
_LOGIC_PYTHON_ATTRS: frozenset[str] = frozenset(python_attr for python_attr, _wire in _LOGIC_KEYS)

if TYPE_CHECKING:  # pragma: no cover - type-checking-only import.
    from ..types.definition import DjangoTypeDefinition


# Process-lifetime memo for ``_lookups_for_field``, keyed by field CLASS.
# A field class's concrete-lookup set is fixed by its registered class lookups
# (Django computes ``Field.get_lookups()`` from the class MRO), so it is stable
# across every instance of that class AND across ``registry.clear()`` (which
# recreates DjangoTypes / FilterSets, never Django's field classes). It
# therefore needs no clear hook -- the keys are Django field classes, not
# package types.
_lookups_for_field_class_cache: dict[type, list[str]] = {}

# Reverse of ``LOOKUP_NAME_MAP``'s ``django_lookup -> (python_attr, ...)``
# direction, built once at import so ``_form_key_for_python_attr`` is an O(1)
# dict lookup instead of an O(n) linear scan on every normalized field. Built
# from a ``reversed`` view so the FIRST ``django_lookup`` wins when two map to
# the same ``python_attr`` -- matching the original first-match-wins scan.
_FORM_KEY_BY_PYTHON_ATTR: dict[str, str] = {
    python_attr: django_lookup
    for django_lookup, (python_attr, _) in reversed(LOOKUP_NAME_MAP.items())
}

# ``python_attr -> django-filter wire key`` for the logical operators, built once
# at import: ``_LOGIC_KEYS`` is a frozen module constant, so ``_normalize_input``
# re-derived an identical dict every call before this hoist (feedback L2).
_LOGIC_WIRE_BY_PYTHON_ATTR: dict[str, str] = dict(_LOGIC_KEYS)

# The filter-normalize traversal config is request-independent (it references the
# same module-level ``_field_specs`` map by reference, which ``inputs.py`` mutates
# in place at bind), so it is a module singleton rather than rebuilt per
# ``_normalize_input`` call (feedback L2).
_NORMALIZE_TRAVERSAL: SetInputTraversal = SetInputTraversal(
    field_specs=_field_specs,
    related_attr="related_filters",
    logic_keys=_LOGIC_PYTHON_ATTRS,
    unset_sentinel=UNSET,
)


def _read_qs(filterset_instance: Any) -> models.QuerySet:
    """Return ``filterset_instance.qs`` (helper for ``sync_to_async``).

    ``BaseFilterSet.qs`` is a cached property whose evaluation triggers
    ``filter_queryset`` (sync) and may iterate leaf-clause ORM. ``apply_async``
    routes the read through ``sync_to_async(thread_sensitive=True)`` to keep
    the synchronous ORM work off the event-loop thread; this tiny wrapper
    exists because ``sync_to_async`` wants a callable, not an attribute read.
    """
    return filterset_instance.qs


def _lookups_for_field(model_field: models.Field | None) -> list[str]:
    """Return every concrete (non-transform) lookup valid for ``model_field``.

    Backs the per-field ``Meta.fields = {"<field>": "__all__"}`` shorthand
    (``graphene-django`` / cookbook ``filter_fields`` parity). ``django-filter``
    expands only the TOP-LEVEL ``fields = "__all__"``; a per-field ``"__all__"``
    value is passed through verbatim and would otherwise be mis-read as a
    literal lookup expression, so ``FilterSet.get_fields`` expands it through
    this helper.

    Django's ``Field.get_lookups()`` returns both ``Lookup`` and ``Transform``
    registrations. Transforms (``year`` / ``month`` / ``date`` / ``time`` / ...
    on temporal fields, ``unaccent`` on PostgreSQL text) are EXCLUDED: the
    cookbook's ``lookups_for_field`` expands each transform into a nested
    ``<transform>__<sublookup>`` tree consumed by Graphene's tree-shaped input
    builder, but this package's per-field operator-bag input shape (one flat
    ``<Field>FilterInputType`` bag of lookup attributes) has no nested-transform
    form. ``"__all__"`` therefore yields the flat comparison / membership /
    pattern lookups (``exact`` / ``iexact`` / ``contains`` / ``icontains`` /
    ``gt`` / ``lt`` / ``in`` / ``range`` / ``isnull`` / ``regex`` / ...); a
    consumer who wants a transform (e.g. ``created__year``) declares it as an
    explicit lookup expression instead.

    Memoized by ``type(model_field)`` (see ``_lookups_for_field_class_cache``):
    the lookup set is class-determined, so same-typed fields share one crawl.
    A COPY is returned so a caller mutating the list cannot corrupt the cache.
    """
    if model_field is None:
        return []
    field_class = type(model_field)
    cached = _lookups_for_field_class_cache.get(field_class)
    if cached is None:
        cached = [
            lookup_expr
            for lookup_expr, lookup in model_field.get_lookups().items()
            if not issubclass(lookup, models.Transform)
        ]
        _lookups_for_field_class_cache[field_class] = cached
    return list(cached)


class FilterSetMetaclass(filterset.FilterSetMetaclass):
    """Discover `RelatedFilter` declarations and bind them to the new class.

    Direct port of `django_graphene_filters/filterset.py::FilterSetMetaclass`.
    Expansion of related filters into per-lookup ORM paths is deferred to
    `FilterSet.get_filters` so circular `RelatedFilter` references
    declared in the same module are legal.
    """

    def __new__(
        cls: type[FilterSetMetaclass],
        name: str,
        bases: tuple,
        attrs: dict[str, Any],
    ) -> FilterSetMetaclass:
        """Build the class, collect `RelatedFilter`s, and bind them to the owner."""
        # Allow consumers to use `filter_fields` as a synonym for `fields`
        # under `Meta`; matches the cookbook's `graphene-django` alias.
        meta_class = attrs.get("Meta")
        if (
            meta_class
            and hasattr(meta_class, "filter_fields")
            and not hasattr(meta_class, "fields")
        ):
            meta_class.fields = meta_class.filter_fields

        new_class = super().__new__(cls, name, bases, attrs)

        # Collect the ``RelatedFilter`` declarations and bind each to the new
        # class via the shared set-family collector (the 0.0.9 DRY pass,
        # ``docs/feedback.md`` Major 3). ``declared_filters`` is already MRO-merged
        # by ``django_filters``' metaclass, so ``inherit_from_bases=False`` - only
        # the ``isinstance`` filter runs (the order side merges from bases itself).
        collect_related_declarations(
            new_class,
            bases,
            own_items=new_class.declared_filters.items(),
            declaration_type=RelatedFilter,
            collection_attr="related_filters",
            inherit_from_bases=False,
        )

        return new_class


def _expand_related_filter(filter_name: str, f: RelatedFilter) -> OrderedDict[str, Any]:
    """Expand `f` against its target filterset's resolved filters.

    Verbatim port of the cookbook's `expand_related_filter`. The
    per-field deep-copy avoids mutating the target filterset's
    instances when the parent rebinds `field_name` to the relation
    path. Module-level helper because the expansion has no metaclass
    state - moving it off the metaclass keeps the call site
    (``get_filters``) free of ``cls.__class__.expand_related_filter
    (cls, ...)`` indirection that obscured the function's purpose.
    """
    expanded: OrderedDict = OrderedDict()
    target_filterset = f.filterset
    if not target_filterset:
        return expanded
    target_filters = target_filterset.get_filters()
    for child_name, field in target_filters.items():
        new_name = f"{filter_name}__{child_name}"
        field_copy = copy.deepcopy(field)
        field_copy.field_name = f"{f.field_name}__{field.field_name}"
        expanded[new_name] = field_copy
    return expanded


class FilterSet(ClassBasedTypeNameMixin, filterset.BaseFilterSet, metaclass=FilterSetMetaclass):
    """Consumer-facing `FilterSet` foundation.

    Subclasses `django_filters.filterset.BaseFilterSet` directly per
    spec-027 Decision 5; the cookbook's lazy-resolution Layers 3 and 4
    are folded in via `FilterSetMetaclass` and `get_filters`. The
    Decision-8 / M1-of-rev5 named helpers decompose `apply_sync` and
    `apply_async` so each step can be exercised in isolation; `apply`
    stays as a thin dispatcher that translates the typed
    `SyncMisuseError` from `apply_type_visibility_sync` into a
    `RuntimeError` consumers can match on.

    `_owner_definition` is the binding seam populated by
    `finalize_django_types` phase 2.5 per H4 of rev4; the slot declared
    `None` and the fallback branch in `filter_for_field` /
    `filter_for_lookup` that consults `registry.primary_for(...)` keeps
    package-internal tests able to exercise the Relay-vs-scalar
    conditional before owner binding lands.
    """

    # Binding seam - populated by `finalize_django_types` phase 2.5.
    _owner_definition: DjangoTypeDefinition | None = None

    # Cache for fully-resolved filters per Layer 4 of Decision 3.
    _expanded_filters = None
    # Recursion guard around `get_filters` so a self-referential
    # `RelatedFilter` does not blow the stack.
    _is_expanding_filters = False

    # Family binding-state descriptor: the single source for the lifecycle attr
    # names `get_filters` (via `expanded_once`) and `registry.clear()` (via
    # `clear_filter_input_namespace`'s `binding_attrs`) reference, instead of
    # re-spelling the tuple (the 0.0.9 DRY pass, `docs/feedback.md` Major 3).
    _lifecycle: ClassVar[SetLifecycleAttrs] = SetLifecycleAttrs(
        owner="_owner_definition",
        cache="_expanded_filters",
        guard="_is_expanding_filters",
    )

    # Logical-branch (`and` / `or` / `not`) recursion-depth cap. Declared
    # as a `ClassVar` so a consumer with a legitimate deeper-nesting case
    # (machine-generated queries, faceted search) can subclass and raise
    # the cap without monkey-patching a module constant. Eight levels
    # covers every realistic consumer-driven graph; beyond it a typed
    # `ConfigurationError` surfaces the misuse at the source instead of a
    # Python `RecursionError`.
    _MAX_LOGIC_DEPTH: ClassVar[int] = 8

    # Depth hand-off channel for the tree-form logic recursion. Set on a
    # sibling instance by `_q_for_branch` so `filter_queryset` can read
    # the counter back across django-filter's `.qs` boundary (which we do
    # not own and cannot thread kwargs through). Declared here so the
    # attribute is discoverable to static analysis / `__slots__` / typing
    # and the default is explicit on every instance.
    _logic_depth: int = 0

    # Resolver-``info`` hand-off channel, threaded the same way as
    # `_logic_depth`: set by `apply_sync` / `apply_async` on the top-level
    # instance and by `_q_for_branch` on each sibling so nested logical
    # branches can re-derive their `RelatedFilter` visibility across the
    # `.qs` boundary. `None` for instances built outside the apply pipeline
    # (they carry no related branches to re-derive).
    _apply_info: Any = None

    # Pre-derived nested-branch visibility map. Populated by ``apply_async``
    # via ``_collect_nested_visibility_querysets_async``, which walks every
    # ``and`` / ``or`` / ``not`` arm BEFORE the top-level ``.qs`` read and
    # awaits each branch's target ``get_queryset``. ``_q_for_branch`` then
    # looks up by ``id(child_input)`` instead of calling the sync derive,
    # which would raise ``SyncMisuseError`` mid-``.qs`` if the target type's
    # ``get_queryset`` is async-only. ``None`` for instances built by
    # ``apply_sync`` or outside the apply pipeline (sync path stays sync).
    _nested_qs_by_branch_id: dict[int, dict[str, models.QuerySet]] | None = None

    # ``ClassBasedTypeNameMixin`` naming suffixes. The root input type keeps
    # the mixin's default ``"InputType"`` (``FooFilter`` -> ``FooFilterInputType``);
    # the per-field operator bag overrides to ``"FilterInputType"``
    # (``FooFilter`` + ``Bar`` -> ``FooFilterBarFilterInputType``), matching the
    # names ``inputs.py`` produced inline before the naming rule was shared.
    _field_type_suffix: str = "FilterInputType"

    # ------------------------------------------------------------------
    # Layer 4 - cycle-safe filter expansion (cookbook port).
    # ------------------------------------------------------------------

    @classmethod
    def get_filters(cls) -> OrderedDict:
        """Return declared + Meta-derived + related-expanded filters.

        Direct port of `AdvancedFilterSet.get_filters`. Two reasons the
        guard reads `cls.__dict__` directly instead of `getattr`:

        - A subclass must not inherit its parent's completed
          `_expanded_filters` cache via MRO.
        - The metaclass calls `super().__new__()` before stamping
          `related_filters` onto the new class, and the upstream
          `super().__new__()` call triggers `get_filters()`; the
          `__dict__`-based guard prevents the in-flight class from
          caching a half-built result.

        Single-threaded contract:
            ``_is_expanding_filters`` is a class-level reentrancy
            flag, not a thread-local one. Expansion runs during
            ``finalize_django_types()`` (single-threaded by design)
            and once per class for the lifetime of the registry, so
            the flag's read/write is never contended at runtime.
            Parallel test runs that exercise the same FilterSet class
            from different threads can race on the flag - the second
            thread sees ``_is_expanding_filters=True`` and short-
            circuits to ``super().get_filters()``, yielding the
            unexpanded set. Tests that need to call ``get_filters()``
            from multiple threads must serialize the call themselves;
            do not introduce a ``threading.local`` here without first
            confirming a real consumer call path requires it.
        """
        # Capture ``super().get_filters`` HERE (in the classmethod body, where
        # zero-arg ``super()`` resolves ``cls`` + the ``__class__`` cell) rather
        # than inside ``_build`` / ``on_reentry``: the metaclass calls
        # ``get_filters()`` DURING ``FilterSet``'s own creation, before the module
        # global ``FilterSet`` is bound, so a ``super(FilterSet, cls)`` lookup in a
        # nested function would ``NameError`` (and a zero-arg ``super()`` in a
        # no-arg nested function / lambda has no positional to bind).
        get_base = super().get_filters

        def _build() -> OrderedDict:
            all_filters = get_base()
            if cls._meta.model is not None:
                related_filters_val = getattr(cls, "related_filters", OrderedDict())
                for filter_name, f in related_filters_val.items():
                    expanded = _expand_related_filter(filter_name, f)
                    all_filters.update(expanded)
            # TODO(spec-027-filters-0_0_8 Meta.search_fields card 0.1.2):
            # wire `construct_search(all_filters)` from
            # `django_strawberry_framework.filters.inputs.LOOKUP_PREFIXES` here.

            # The two-condition cache-write gate (own `related_filters` +
            # no unresolved string lazy targets) is single-sited in
            # `sets_mixins.should_cache_expansion` (DRY review A8).
            if should_cache_expansion(
                cls,
                related_attr="related_filters",
                target_slot="_filterset",
            ):
                cls._expanded_filters = all_filters
                cls.base_filters = all_filters
            return all_filters

        # The class-level expansion cache + reentry-guard skeleton is shared with
        # `OrderSet.get_fields` through `sets_mixins.expanded_once` (the 0.0.9 DRY
        # pass, `docs/feedback.md` Major 3). `on_reentry` returns the unexpanded
        # `super().get_filters()` when this class is already mid-expansion, so a
        # self-referential `RelatedFilter` neither blows the stack nor caches a
        # half-built result.
        return expanded_once(
            cls,
            cache_attr=cls._lifecycle.cache,
            guard_attr=cls._lifecycle.guard,
            build=_build,
            on_reentry=get_base,
        )

    @classmethod
    def get_fields(cls) -> OrderedDict:
        """Expand per-field ``"__all__"`` and narrow the top-level ``"__all__"`` sweep.

        Two overrides over ``django-filter``'s ``get_fields``:

        - **Per-field ``"__all__"``** (dict form, e.g. ``{"name": "__all__"}``):
          ``django-filter`` expands only the top-level ``fields = "__all__"``
          and passes a per-field ``"__all__"`` value through verbatim - which
          is then mis-read as a literal lookup expression. We expand each such
          value to the field's concrete lookups via `_lookups_for_field`
          (transforms excluded; see that helper). This is the cookbook /
          ``graphene-django`` ``filter_fields = {"field": "__all__"}`` parity.
        - **Top-level ``"__all__"`` narrowing** (M3-of-rev4): ``django-filter``
          treats the PK as a non-filterable column and includes M2M in the
          ``"__all__"`` sweep; the package's preferred shape is the opposite
          (PK is a canonical filter; M2M needs an explicit `RelatedFilter`).

        The upstream method is named ``get_fields`` (no underscore prefix);
        we override the same name so `super().get_filters()`'s internal call
        routes through both narrowings.
        """
        fields = super().get_fields()
        model = cls._meta.model
        meta_fields = getattr(cls._meta, "fields", None)

        # Per-field ``"__all__"`` expansion (dict form). Runs before the
        # top-level branch below; the two shapes are mutually exclusive
        # (``meta_fields`` is either the ``"__all__"`` string or a dict).
        if model is not None and isinstance(meta_fields, dict):
            for field_name in list(fields):
                if fields[field_name] == "__all__":
                    model_field = get_model_field(model, field_name)
                    lookups = _lookups_for_field(model_field)
                    if cls._is_own_pk_under_relay_owner(model_field):
                        # A Relay node's own PK is a GlobalID over the wire, so
                        # only equality / membership / null are meaningful.
                        # Ordering and pattern lookups (``range`` / ``gt`` /
                        # ``contains`` / ...) have no GlobalID semantics and are
                        # dropped from the generated surface rather than emitted
                        # as corrupt ``String`` inputs (spec-027 H1).
                        lookups = [lk for lk in lookups if lk in ("exact", "in", "isnull")]
                    fields[field_name] = lookups

        if meta_fields != "__all__":
            return fields

        if model is None:  # pragma: no cover - unreachable defensive guard.
            # ``super().get_fields()`` above already dereferences
            # ``self._meta.model._meta`` for the ``"__all__"`` shorthand and
            # raises ``AttributeError`` when the model is ``None``; control
            # never reaches this guard for that field shape. Kept as a
            # forward-defensive no-op in case the upstream contract changes.
            return fields

        # ADD the PK if upstream excluded it (typically the auto-id column).
        pk_field = model._meta.pk
        if pk_field is not None and pk_field.name not in fields:
            fields[pk_field.name] = ["exact"]

        # REMOVE every ManyToManyField from the swept dict.
        m2m_names = {
            f.name for f in model._meta.get_fields() if isinstance(f, models.ManyToManyField)
        }
        for name in list(fields):
            if name in m2m_names:
                del fields[name]

        return fields

    # ------------------------------------------------------------------
    # Decision-4 owner-aware Relay-vs-scalar conditional.
    # ------------------------------------------------------------------

    @classmethod
    def filter_for_field(
        cls,
        field: Any,
        field_name: str,
        lookup_expr: str | None = None,
    ) -> Any:
        """Pick the Relay-aware filter for Relay-Node-shaped relation targets.

        Decision-4 conditional. Resolves the relation target via
        `_owner_definition.related_target_for(field_name)` (Slice-3
        binding) and falls back to `registry.primary_for(target_model)`
        when the owner has not been bound yet. A target type implementing
        `relay.Node` produces `GlobalIDMultipleChoiceFilter` for
        multi-valued relations (M2M / reverse FK / reverse M2M) and
        `GlobalIDFilter` for single-valued relations (forward FK /
        OneToOne); non-Relay targets and non-relation fields defer to the
        upstream default unchanged.

        Own-PK branch (spec-027 L566-567 + L607): when ``field`` is the
        owning model's primary key AND the owning ``DjangoType`` itself
        implements ``relay.Node``, the field becomes ``GlobalIDFilter`` -
        the OWNER is the Relay node so its PK column is a GlobalID over
        the wire.

        Generated flat leaves whose ORM path crosses a reverse FK or M2M
        relation are marked ``distinct=True`` before any Relay-aware
        replacement. A fan-out JOIN can otherwise return the same parent
        once per matching child, corrupting list rows and connection counts.
        """
        default = super().filter_for_field(field, field_name, lookup_expr)
        requires_distinct = default.distinct or path_traverses_to_many(
            cls._meta.model,
            field_name,
        )
        default.distinct = requires_distinct
        if cls._is_own_pk_under_relay_owner(field):
            # The owner's own PK is a GlobalID over the wire. Honor the
            # lookup cardinality: an ``in`` lookup consumes a LIST of
            # GlobalIDs (multi-choice), every other lookup a single one.
            # Without this split ``id: {in: [...]}`` collapsed to a single
            # ``GlobalIDFilter`` and silently dropped to a scalar input.
            # ``isnull`` is a Boolean predicate, not a GlobalID, so pass the
            # upstream filter through unchanged (spec-027 H1).
            if default.lookup_expr == "isnull":
                return default
            own_pk_filter_class = (
                GlobalIDMultipleChoiceFilter if default.lookup_expr == "in" else GlobalIDFilter
            )
            # ``**default.extra`` is safe to forward even to
            # ``GlobalIDMultipleChoiceFilter``: ``default`` is the upstream
            # SCALAR filter for the PK column (a NumberFilter-shaped default),
            # so ``.extra`` carries no ``queryset=`` and no incompatible
            # ``ModelChoiceField`` kwargs. ``GlobalIDMultipleChoiceFilter``
            # backs onto ``_GlobalIDMultipleChoiceField`` (a plain
            # ``MultipleChoiceField``, NOT a model-backed field), which needs
            # no ``queryset`` and accepts an empty ``choices`` set, so the
            # forwarded extras can never leave it under-configured.
            return own_pk_filter_class(
                field_name=default.field_name,
                lookup_expr=default.lookup_expr,
                distinct=requires_distinct,
                **default.extra,
            )
        target_type = cls._resolve_relation_target_type(field, field_name)
        if target_type is None or not implements_relay_node(target_type):
            return default
        relay_filter_class = cls._relay_filter_class_for_field(field)
        return relay_filter_class(
            field_name=default.field_name,
            lookup_expr=default.lookup_expr,
            distinct=requires_distinct,
            **default.extra,
        )

    @classmethod
    def filter_for_lookup(cls, field: Any, lookup_type: str) -> tuple[Any, dict[str, Any]]:
        """Mirror `filter_for_field`'s Relay-vs-scalar conditional per-lookup.

        Non-relation fields defer to the upstream pair-return shape unless
        the field is the owner's own PK and the owner is Relay-Node-shaped
        (own-PK branch per spec-027 L566-567). For relation fields a
        Relay-Node-shaped target maps to a ``(GlobalIDFilter, params)``
        pair (or ``GlobalIDMultipleChoiceFilter`` for multi-valued
        relations); otherwise the upstream return is passed through.
        """
        default_class, params = super().filter_for_lookup(field, lookup_type)
        if cls._is_own_pk_under_relay_owner(field):
            # Own-PK GlobalID. A Relay node's wire id supports only equality
            # (``exact`` -> a single GlobalID), membership (``in`` -> a list of
            # GlobalIDs), and null (``isnull`` -> the upstream Boolean; a
            # GlobalID cannot represent ``true``). Any other lookup has no
            # GlobalID ordering / pattern semantics. This guard is
            # authoritative once the owner is bound (finalizer phase 2.5):
            # ``_is_own_pk_under_relay_owner`` keys off ``cls._owner_definition``,
            # which is ``None`` during class creation, so the check is inert
            # then and becomes authoritative at finalize (not only the
            # ``get_fields`` ``"__all__"`` narrowing). An explicit
            # ``Meta.fields`` list that names an unsupported lookup is rejected
            # here so it cannot silently generate a corrupt GlobalID-shaped
            # input (spec-027 H1).
            if lookup_type == "in":
                return GlobalIDMultipleChoiceFilter, params
            if lookup_type == "isnull":
                return default_class, params
            if lookup_type == "exact":
                return GlobalIDFilter, params
            field_name = getattr(field, "name", "<pk>")
            raise ConfigurationError(
                f"{cls.__name__}: lookup {lookup_type!r} is not supported on the "
                f"Relay node's own primary key {field_name!r}; a GlobalID supports "
                "only 'exact', 'in', and 'isnull'. Remove it from Meta.fields.",
            )
        if not field.is_relation:
            if lookup_type == "in" and isinstance(field, models.IntegerField):
                # An element-binding integer ``__in`` routes through IntegerInFilter:
                # it drops out-of-range members (an out-of-range value overflows the
                # backend at bind) and matches NOTHING when a non-empty list fully
                # drops, instead of django-filter's empty-value skip that would widen
                # a restrictive ``in`` to no constraint (feedback). Own-PK Relay ``in``
                # is handled above (GlobalIDMultipleChoiceFilter); a non-integer column
                # carries no binding-range limit so it keeps the upstream filter.
                return IntegerInFilter, params
            return default_class, params
        target_type = cls._resolve_relation_target_type(field, getattr(field, "name", None))
        if target_type is None or not implements_relay_node(target_type):
            return default_class, params
        return cls._relay_filter_class_for_field(field), params

    @classmethod
    def _is_own_pk_under_relay_owner(cls, field: Any) -> bool:
        """Return True iff ``field`` is the owning model's PK and owner is Relay.

        Own-PK branch per spec-027 L566-567 + L607: when a ``FilterSet``
        whose owning ``DjangoType`` implements ``relay.Node`` filters on
        its own primary key, the wire shape is a Relay GlobalID - so the
        filter for that PK is ``GlobalIDFilter`` rather than the scalar
        upstream default. Resolves only when ``_owner_definition`` is
        bound (finalizer phase-2.5 binding) so package-internal tests
        that run pre-binding keep the upstream shape.
        """
        owner = cls._owner_definition
        if owner is None:
            return False
        if getattr(field, "is_relation", False):
            return False
        model = getattr(getattr(cls, "_meta", None), "model", None)
        if model is None:
            return False
        pk = getattr(model._meta, "pk", None)
        if pk is None or field is not pk:
            return False
        owner_type = getattr(owner, "origin", None)
        return owner_type is not None and implements_relay_node(owner_type)

    @staticmethod
    def _relay_filter_class_for_field(field: Any) -> type:
        """Pick the Relay-aware filter class matching the relation cardinality.

        Multi-valued relations (`ManyToManyField`, reverse FK
        `ManyToOneRel`, reverse M2M `ManyToManyRel`) - every Django
        relation field that sets `many_to_many=True` or `one_to_many=True`
        - map to `GlobalIDMultipleChoiceFilter`; single-valued relations
        (forward `ForeignKey` / `OneToOneField` and reverse `OneToOneRel`)
        map to `GlobalIDFilter`. This mirrors `django-filter`'s upstream
        choice between `ModelChoiceFilter` and `ModelMultipleChoiceFilter`
        and matches Decision 4's parity-floor split between the two
        Relay-aware primitives.

        The many-side test is the shared cardinality classifier in
        ``utils/relations.py`` (``is_many_side_relation_kind(relation_kind(field))``),
        the same call the optimizer walker, the order set family, and the
        relation resolvers route through, so the "rendered as a GraphQL list"
        decision cannot drift between the filter family and its siblings.
        """
        if is_many_side_relation_kind(relation_kind(field)):
            return GlobalIDMultipleChoiceFilter
        return GlobalIDFilter

    @classmethod
    def _resolve_relation_target_type(cls, field: Any, field_name: str | None) -> type | None:
        """Look up the registered target `DjangoType` for a relation field.

        Consults `_owner_definition.related_target_for(...)` when the
        finalizer phase-2.5 binding has landed; otherwise falls back to
        `registry.primary_for(field.related_model)`. Non-relation fields
        return `None`.
        """
        if not getattr(field, "is_relation", False):
            return None
        owner = cls._owner_definition
        if owner is not None and field_name is not None:
            # Owner-aware path (finalizer phase-2.5 binding has landed): resolve
            # the target `DjangoType` through `owner.related_target_for(...)`.
            # The pair's first member is a `DjangoTypeDefinition`, whose
            # registered `DjangoType` class is its `.origin` attribute --
            # NOT `.type` / `.type_cls`, which the definition never
            # exposes (a stale read there silently returned `None` and
            # dropped every owner-aware resolution to the registry
            # fallback). Mirrors `_is_own_pk_under_relay_owner` /
            # `_target_type_for_related_filter`, which both read `.origin`.
            resolved = getattr(owner, "related_target_for", None)
            if callable(resolved):
                pair = resolved(field_name)
                if pair is not None:
                    target_definition, _ = pair
                    return getattr(target_definition, "origin", None)
        related_model = getattr(field, "related_model", None)
        if related_model is None:
            return None
        # `registry.primary_for(...)` returns the explicitly-declared
        # primary type only; fall back to `registry.get(...)` for the
        # single-type-no-primary case (the common shape today).
        return registry.primary_for(related_model) or registry.get(related_model)

    # ------------------------------------------------------------------
    # Decision-8 / M1-of-rev5 apply pipeline.
    # ------------------------------------------------------------------

    @staticmethod
    def _iter_input_items(input_value: Any) -> list[tuple[str, Any]] | None:
        """Walk a dict or Strawberry-input dataclass into ``(name, value)`` pairs.

        Thin delegate to ``utils/permissions.py::iter_input_items`` (single-sited
        with the order side per the 0.0.9 DRY pass). Returns ``None`` for an
        input that is neither a dict nor a Strawberry-input dataclass, ``[]`` for
        a walkable-but-empty input.
        """
        return iter_input_items(input_value)

    @classmethod
    def _normalize_input(cls, input_value: Any) -> dict[str, Any]:
        """Translate a Strawberry input dataclass into `django-filter` form data.

        Per-primitive value normalization: each scalar attr passes
        through ``normalize_input_value`` so ``relay.GlobalID`` ->
        ``node_id``, Strawberry enum -> ``.value``, and
        ``filters.base.RangeFilter`` -> positional ``{name}_0`` /
        ``{name}_1`` keys all land in ``data`` correctly (``RangeFilter``
        is not imported here -- the symbol lives in ``filters.base`` and
        is referenced for shape-documentation; the actual range patch
        comes back from ``inputs.py::_normalize_range_value``). Related-
        branch keys (the
        ``shelves`` / ``books`` / etc. names declared via
        ``RelatedFilter``) are STRIPPED from the form-data dict before
        the parent's form sees it -- ``django-filter``'s form only owns
        the leaf lookup keys for the parent filterset, and any nested
        dict in those positions would fail validation. ``_apply_related_constraints``
        handles those branches separately via the ``<rel>__in=<intersected>``
        clause earlier in the apply pipeline.

        GlobalID type-name validation happens at queryset-evaluation
        time inside ``GlobalIDFilter.filter`` /
        ``GlobalIDMultipleChoiceFilter.filter``, which read the owner
        via ``filter_instance.parent._owner_definition``. The owner is
        therefore not threaded as a parameter here.
        """
        if is_inactive_value(input_value, unset_sentinel=UNSET):
            return {}
        items = cls._iter_input_items(input_value)
        if items is None:
            return {}

        all_filters = cls.get_filters() if cls._meta.model is not None else {}

        # The dataclass-vs-dict walk, the ``None`` / ``UNSET`` active-input skip,
        # the ``_field_specs`` lookup, and the leaf / related / logic
        # classification are the shared traversal mechanics owned by
        # ``utils/input_values.py::iter_active_fields`` (the 0.0.9 DRY pass,
        # ``docs/feedback.md`` Major 1). Each yielded ``ActiveField`` is
        # dispatched here by ``kind``: ``LOGIC`` copies the raw sub-tree under
        # its ``django-filter`` wire key, ``RELATED`` is stripped (owned by
        # ``_apply_related_constraints``, since the parent form cannot validate a
        # nested-dict shape), and ``LEAF`` runs the per-field operator-bag /
        # range normalization that stays local to the filter family.
        data: dict[str, Any] = {}
        for field in iter_active_fields(cls, input_value, _NORMALIZE_TRAVERSAL):
            if field.kind == LOGIC:
                data[_LOGIC_WIRE_BY_PYTHON_ATTR[field.python_attr]] = field.raw_value
                continue
            if field.kind == RELATED:
                # Related branches travel through `_apply_related_constraints`,
                # not the parent form.
                continue
            django_source_path = field.spec.django_source_path if field.spec is not None else None
            # Per spec-027 L518-605 (per-field operator bag), top-
            # level scalar fields wrap a nested ``<Field>FilterInputType``
            # dataclass whose attrs map to ``django-filter`` lookups
            # (``exact`` / ``i_contains`` / ``in_`` / ...). Iterate the bag
            # to produce ``<source>__<lookup>`` form-data keys.
            bag_items = cls._operator_bag_items(field.raw_value)
            if bag_items is not None:
                base_path = django_source_path or cls._form_key_for_python_attr(field.python_attr)
                for lookup_attr, lookup_value in bag_items:
                    # Mirror the classifier's active-input rule so a partially-
                    # supplied operator bag (e.g.
                    # ``title: { exact: UNSET, icontains: "foo" }``) does
                    # not leak the UNSET sentinel through to
                    # ``normalize_input_value``; a Strawberry input
                    # dataclass defaults every unsupplied lookup to
                    # ``UNSET`` rather than ``None``, so this is the
                    # common case for any consumer who fills some but
                    # not all lookups.
                    if is_inactive_value(lookup_value, unset_sentinel=UNSET):
                        continue
                    django_lookup = cls._form_key_for_python_attr(lookup_attr)
                    suffixed_key = f"{base_path}__{django_lookup}"
                    # ``exact`` registers under the bare ``base_path`` form key but
                    # may also be declared explicitly as ``base_path__exact``, so it
                    # probes both; every other lookup only ever lives under its
                    # suffixed key, so ``form_key`` and ``suffixed_key`` coincide and
                    # a single lookup suffices.
                    form_key = base_path if django_lookup == "exact" else suffixed_key
                    filter_instance = all_filters.get(form_key)
                    if filter_instance is None and form_key != suffixed_key:
                        filter_instance = all_filters.get(suffixed_key)
                    if filter_instance is None:
                        data[form_key] = lookup_value
                        continue
                    normalized = normalize_input_value(
                        filter_instance,
                        lookup_value,
                        field_name=form_key,
                    )
                    if isinstance(normalized, dict):
                        data.update(normalized)
                    else:
                        # An element-binding integer ``__in`` is range-coerced (and
                        # empty-aware) by ``IntegerInFilter`` at filter time, not here
                        # (``filter_for_lookup`` routes it there), so the normalized
                        # list passes straight through.
                        data[form_key] = normalized
                continue
            form_key = django_source_path or cls._form_key_for_python_attr(field.python_attr)
            filter_instance = all_filters.get(form_key)
            if filter_instance is None:
                data[form_key] = field.raw_value
                continue
            normalized = normalize_input_value(
                filter_instance,
                field.raw_value,
                field_name=form_key,
            )
            if isinstance(normalized, dict):
                # Range-filter patch: multiple positional form keys for
                # one Strawberry attribute.
                data.update(normalized)
            else:
                data[form_key] = normalized
        return data

    @staticmethod
    def _operator_bag_items(raw_value: Any) -> list[tuple[str, Any]] | None:
        """Return the ``(lookup_attr, value)`` pairs of a per-field operator bag.

        ``_build_input_fields`` wraps each scalar field's lookups in a
        nested ``<Field>FilterInputType`` dataclass. The normalizer
        detects that shape via ``__dataclass_fields__`` (the same sniff
        used at the three call sites that walk Strawberry input dataclasses:
        ``_normalize_input``, ``_operator_bag_items``, and
        ``_active_permission_field_paths``); we sniff
        ``__dataclass_fields__`` instead of testing ``isinstance(..., dataclass)``
        because Strawberry's ``@strawberry.input`` decorator stamps real
        ``dataclass`` machinery on the class -- ``dataclasses.is_dataclass``
        would also match, but the attribute sniff is faster and matches
        the shape upstream uses to introspect input classes.
        ``RelatedFilter`` boundary values are handled separately via
        ``_apply_related_constraints`` so this helper does NOT see them.
        Returns ``None`` for scalar inputs that are not operator bags.
        """
        if isinstance(
            raw_value,
            (
                str,
                bytes,
                int,
                float,
                bool,
            ),
        ):
            return None
        if isinstance(
            raw_value,
            (
                list,
                tuple,
                set,
                frozenset,
            ),
        ):
            return None
        # A dict reaches a direct ``apply_*`` caller in two shapes that
        # must NOT be conflated:
        #   * an operator bag - ``{"i_contains": "x", "gt": 3}`` - whose
        #     keys are per-field lookup attrs; this is the shape that, when
        #     passed as a dict, used to fall through to the scalar branch
        #     where ``normalize_input_value`` splatted the raw dict into
        #     the form data as unknown keys the form silently ignored (the
        #     explicit-filter-applies-nothing bug);
        #   * a multi-key filter VALUE - a ``RangeFilter``'s
        #     ``{"start": 1, "end": 5}`` - whose keys are NOT lookup attrs
        #     and which the scalar branch must hand to
        #     ``normalize_input_value`` so it produces the positional
        #     ``{<field>_0, <field>_1}`` patch.
        # Disambiguate by the keys: a dict is an operator bag only when
        # EVERY key names a known lookup attr (``_FORM_KEY_BY_PYTHON_ATTR``
        # - ``start`` / ``end`` are absent). Strawberry-input dataclass
        # bags (the schema-driven path) always delegate unchanged.
        if isinstance(raw_value, dict):
            if raw_value and all(key in _FORM_KEY_BY_PYTHON_ATTR for key in raw_value):
                return list(raw_value.items())
            return None
        return FilterSet._iter_input_items(raw_value)

    @staticmethod
    def _form_key_for_python_attr(python_attr: str) -> str:
        """Map a Strawberry dataclass attr back to a `django-filter` form key.

        Looks the attr up in the precomputed ``_FORM_KEY_BY_PYTHON_ATTR``
        reverse map (built once from ``LOOKUP_NAME_MAP`` at import).
        Falls through to the attr name verbatim when no lookup pair
        rewrites it. Used by ``_normalize_input`` both at the top-level
        scalar branch and inside the per-field operator-bag iteration
        (mapping ``i_contains`` -> ``icontains`` etc.); the two callers
        share this single helper rather than duplicating the walk.
        """
        return _FORM_KEY_BY_PYTHON_ATTR.get(python_attr, python_attr)

    @classmethod
    def _request_from_info(cls, info: Any) -> Any:
        """Resolve the Django request from `info.context` (M8 of rev5).

        Canonical Strawberry-Django shape: `info.context.request`. The
        wrapper-less alternative `isinstance(info.context, HttpRequest)`
        is detected so consumers running a bare-HttpRequest context (the
        Django test client default) work without bespoke wiring. Any
        other shape raises `ConfigurationError`. Thin delegate to
        ``utils/permissions.py::request_from_info`` (single-sited with the
        order side per the 0.0.9 DRY pass).
        """
        return request_from_info(info, family_label="FilterSet")

    @classmethod
    def _iter_active_related_branches(
        cls,
        input_value: Any,
    ) -> list[tuple[str, RelatedFilter, Any]]:
        """List `(field_name, related_filter, child_input)` for present branches.

        Active-branch scoping (M4 of rev3) - a `RelatedFilter` is "active"
        when its key is present in the input, regardless of the inner
        value's emptiness. Inactive branches are skipped end-to-end
        (visibility derivation, constraint application, permission
        recursion) so an empty filter does not pre-constrain the parent
        queryset.

        Both ``strawberry.UNSET`` (the Strawberry input-dataclass default
        for unsupplied fields) and ``None`` collapse to "branch not
        supplied" via ``_extract_branch_value``; only the consumer-
        supplied branches reach the caller. Thin delegate to
        ``utils/permissions.py::active_related_branches`` (single-sited with
        the order side per the 0.0.9 DRY pass); the filter side has no
        top-level list shape, so ``handle_top_level_list`` stays ``False``.
        """
        return active_related_branches(
            cls,
            input_value,
            related_attr="related_filters",
            unset_sentinel=UNSET,
        )

    @staticmethod
    def _extract_branch_value(input_value: Any, field_name: str) -> Any:
        """Return the value at `field_name` on a dataclass-or-dict input.

        Strawberry input dataclasses default unsupplied fields to
        ``strawberry.UNSET`` rather than ``None``; collapse that sentinel
        to ``None`` so the active-branch caller treats UNSET the same as
        a missing key. Thin delegate to
        ``utils/permissions.py::extract_branch_value`` with
        ``unset_sentinel=UNSET``.
        """
        return extract_branch_value(input_value, field_name, unset_sentinel=UNSET)

    @classmethod
    def _iter_visibility_steps(
        cls,
        input_value: Any,
    ) -> Iterator[tuple[str, Any, type[FilterSet], Any, models.QuerySet]]:
        """Yield the pre-await state each visibility derive method needs.

        Returns ``(field_name, target_type, child_filterset, child_input,
        child_base)`` for every active related branch. A branch whose
        ``target_type`` or ``child_filterset`` cannot be resolved raises
        ``ConfigurationError`` instead of being skipped: the branch is
        ACTIVE (the consumer supplied input for it), so skipping would
        drop the constraint entirely and silently return unfiltered
        parent rows - a filter the consumer believes is applied doing
        nothing. The same misconfiguration is also caught earlier, at
        finalize time, by ``_bind_filtersets`` subpass 2.5 for every
        schema-wired filterset; this runtime guard covers direct
        ``apply_sync`` / ``apply_async`` callers that never finalize.
        Composes with ``_iter_active_related_branches`` (per-branch yield
        shape) so the two iterators chain naturally without materializing
        intermediate lists.
        """
        for field_name, related_filter, child_input in cls._iter_active_related_branches(
            input_value,
        ):
            target_type = cls._target_type_for_related_filter(related_filter)
            child_filterset = related_filter.filterset
            if target_type is None or child_filterset is None:
                child_model = getattr(getattr(child_filterset, "_meta", None), "model", None)
                target_label = getattr(child_model, "__qualname__", "<unresolved>")
                reason = (
                    f"no DjangoType is registered for its target model {target_label}"
                    if child_filterset is not None
                    else "its target FilterSet could not be resolved"
                )
                raise ConfigurationError(
                    f"FilterSet {cls.__qualname__}: related filter branch "
                    f"{field_name!r} is present in the filter input but {reason}. "
                    "The branch's visibility scoping runs the target type's "
                    "get_queryset (spec-027 Decision 8 step 3); skipping it would "
                    "silently return unfiltered rows. Register a DjangoType for "
                    "the target model or remove the RelatedFilter.",
                )
            child_model = child_filterset._meta.model
            child_base = child_model._default_manager.all()
            yield field_name, target_type, child_filterset, child_input, child_base

    @classmethod
    def _derive_related_visibility_querysets_sync(
        cls,
        input_value: Any,
        info: Any,
    ) -> dict[str, models.QuerySet]:
        """Run each active branch's target ``get_queryset(...)`` then recurse.

        Reuses ``django_strawberry_framework/utils/querysets.py::apply_type_visibility_sync``
        - the existing helper handles the sync-misuse detection and
        raises ``SyncMisuseError`` (a ``ConfigurationError`` and
        ``RuntimeError`` subclass); ``apply``'s catch-and-rethrow
        translates that into a ``RuntimeError`` consumers can match
        on via the actionable "use apply_async instead" message.

        After the visibility hook runs, the child filterset's
        ``apply_sync`` is invoked against the visibility-scoped queryset
        so nested input clauses (e.g. ``shelves: { code: { iContains:
        "A" } }``) narrow the child queryset BEFORE the parent's
        ``<rel>__in=<intersected>`` clause is computed (spec-027 L668-678).
        """
        result: dict[str, models.QuerySet] = {}
        for (
            field_name,
            target_type,
            child_filterset,
            child_input,
            child_base,
        ) in cls._iter_visibility_steps(input_value):
            scoped = apply_type_visibility_sync(target_type, child_base, info)
            result[field_name] = child_filterset.apply_sync(child_input, scoped, info)
        return result

    @classmethod
    async def _derive_related_visibility_querysets_async(
        cls,
        input_value: Any,
        info: Any,
    ) -> dict[str, models.QuerySet]:
        """Async sibling of `_derive_related_visibility_querysets_sync`."""
        result: dict[str, models.QuerySet] = {}
        for (
            field_name,
            target_type,
            child_filterset,
            child_input,
            child_base,
        ) in cls._iter_visibility_steps(input_value):
            scoped = await apply_type_visibility_async(target_type, child_base, info)
            result[field_name] = await child_filterset.apply_async(child_input, scoped, info)
        return result

    @classmethod
    def _raise_logic_depth_exceeded(cls) -> NoReturn:
        """Raise the canonical depth-cap ``ConfigurationError`` for this FilterSet.

        Single source of truth for the consumer-visible message shared by
        ``_collect_nested_visibility_querysets_async``, ``_run_permission_checks``,
        and ``_evaluate_logic_tree`` -- all three cap at ``cls._MAX_LOGIC_DEPTH``
        and surface the identical typed error.
        """
        raise ConfigurationError(
            f"FilterSet {cls.__qualname__}: logical-branch nesting exceeded "
            f"_MAX_LOGIC_DEPTH={cls._MAX_LOGIC_DEPTH}. Flatten the filter input "
            "or split into multiple queries.",
        )

    @classmethod
    async def _collect_nested_visibility_querysets_async(
        cls,
        input_value: Any,
        info: Any,
        *,
        _depth: int = 0,
    ) -> dict[int, dict[str, models.QuerySet]]:
        """Pre-walk logical branches and derive each branch's visibility map.

        Returns a map keyed by ``id(child_input)`` -- the same Python object
        identity ``_q_for_branch`` will later receive from
        ``_evaluate_logic_tree`` (preserved by ``_normalize_input``, which
        copies the child dicts verbatim into ``self.data``). ``apply_async``
        calls this BEFORE the top-level ``.qs`` read; ``_q_for_branch``
        consults the stash via the sibling instance's
        ``_nested_qs_by_branch_id`` and skips the sync derive that would
        otherwise raise ``SyncMisuseError`` mid-``.qs`` when a nested
        branch's target ``get_queryset`` is async-only.

        Both the Strawberry-side keys (``and_`` / ``or_`` / ``not_``) and
        the normalized wire-side keys (``and`` / ``or`` / ``not``) are
        walked via ``_extract_branch_value`` so a consumer who hands a
        pre-normalized dict still gets pre-derived maps; the walker
        recurses so deeper nesting (``or: [{or: [...]}]``) also lands in
        the stash before the sync ``_q_for_branch`` ever runs.

        Logical-branch nesting under ``apply_async`` is capped by the same
        ``_MAX_LOGIC_DEPTH`` guard ``_evaluate_logic_tree`` enforces -- a
        pre-walk that exceeds the cap signals the same consumer-side
        misuse and surfaces the same typed ``ConfigurationError`` here
        rather than waiting for the sync recursion to discover it.
        """
        result: dict[int, dict[str, models.QuerySet]] = {}
        if is_inactive_value(input_value, unset_sentinel=UNSET):
            return result
        if _depth > cls._MAX_LOGIC_DEPTH:
            cls._raise_logic_depth_exceeded()
        # Walk each logical sub-branch (``and_`` / ``or_`` / ``not_`` on the
        # Strawberry side; the dict-side input may already carry the
        # normalized ``and`` / ``or`` / ``not`` keys when a consumer hands a
        # raw dict). Each child_input gets its OWN visibility derive plus a
        # recursive walk so deeply-nested branches all carry pre-derived
        # maps before the sync ``_q_for_branch`` ever runs.
        for _python_attr, _wire_key in _LOGIC_KEYS:
            branch_value = cls._extract_branch_value(input_value, _python_attr)
            if branch_value is None:
                branch_value = cls._extract_branch_value(input_value, _wire_key)
            if branch_value is None:
                continue
            children = (
                [branch_value]
                if _wire_key == "not"
                else list(branch_value)
                if branch_value
                else []
            )
            for child_input in children:
                if is_inactive_value(child_input, unset_sentinel=UNSET):
                    continue
                result[id(child_input)] = await cls._derive_related_visibility_querysets_async(
                    child_input,
                    info,
                )
                # Recurse so deeper nesting (``or: [{or: [...]}]``) also
                # lands in the stash.
                nested = await cls._collect_nested_visibility_querysets_async(
                    child_input,
                    info,
                    _depth=_depth + 1,
                )
                result.update(nested)
        return result

    @staticmethod
    def _target_type_for_related_filter(related_filter: RelatedFilter) -> type | None:
        """Resolve the `DjangoType` whose ``get_queryset()`` scopes the branch.

        Prefer the child filterset's *bound owner* - the type the consumer
        explicitly wired via ``Meta.filterset_class`` (``_owner_definition``,
        bound at finalizer phase 2.5) - over a model-only registry lookup. When a
        child model has more than one registered ``DjangoType`` and the child
        filterset is bound to a non-primary one, a model-only lookup resolves the
        *primary* type and runs ITS ``get_queryset()`` against the non-primary's
        filterset, scoping the related branch by the wrong visibility hook (a
        silent row-leak). ``definition.origin`` is the same ``DjangoType`` class
        the registry stores (``types/base.py`` registers ``cls`` with
        ``origin=cls``), so both branches hand ``apply_type_visibility_*`` an object
        exposing ``get_queryset``.

        This mirrors ``_resolve_relation_target_type`` (already owner-aware); the
        registry lookup is the fallback for the unbound / single-type-per-model
        case.
        """
        child_filterset = related_filter.filterset
        child_owner = getattr(child_filterset, "_owner_definition", None)
        owner_type = getattr(child_owner, "origin", None) if child_owner is not None else None
        if owner_type is not None:
            return owner_type
        child_model = getattr(getattr(child_filterset, "_meta", None), "model", None)
        if child_model is None:
            return None
        return registry.primary_for(child_model) or registry.get(child_model)

    @classmethod
    def _run_permission_checks(
        cls,
        input_value: Any,
        request: Any,
        *,
        _fired: dict[type, set[str]] | None = None,
        _bare: Any = None,
        _depth: int = 0,
    ) -> None:
        """Fire `check_<field>_permission(request)` for fields in the input.

        Active-input-only per M2 of rev5 - a declared `check_*` gate that
        is not exercised by this call leaves the queryset untouched.
        Recurses into the child filterset for each active `RelatedFilter`
        branch so the cookbook's nested-permission contract holds, and
        into ``and`` / ``or`` / ``not`` sub-trees so a logically-nested
        field is gated the same as a top-level one.

        Permission methods are called via a bare instance allocated with
        ``object.__new__(cls)``; this matches the cookbook contract
        (per-field gates are written as regular ``def
        check_X_permission(self, request)`` methods on the filterset)
        without requiring a fully-constructed `FilterSet` instance. The
        bare instance is threaded through the same-class logical-branch
        recursion via ``_bare`` so it is allocated once per class per
        top-level call; a child ``RelatedFilter`` filterset (a different
        class) allocates its own.

        Dedup contract:
            ``_fired`` maps each ``FilterSet`` class to the set of
            ``check_*_permission`` method names that have already fired
            against THAT class in this top-level call. The map is shared
            across BOTH the logical-branch recursion (same class) AND
            the child-filterset recursion (different class), so a gate
            fires at most once per class regardless of how many sibling
            ``and`` / ``or`` / ``not`` arms reference it. Concretely,
            ``or: [{shelves: {published: true}}, {shelves: {published:
            false}}]`` fires the parent's ``check_shelves_permission``
            once AND the child ``ShelfFilter.check_published_permission``
            once - the per-class set keyed on the child dedups the
            re-entry from the second arm.

        Double-dispatch contract:
            For an active ``RelatedFilter`` branch named ``shelves``
            both gates fire - the parent's ``check_shelves_permission``
            (the per-branch gate on the owning filterset) AND the child
            filterset's own ``check_*_permission`` gates. They live in
            different per-class dedup sets, so both fire once. That
            parent-vs-child split is intentional; a consumer who logs
            from each gate sees one entry per (class, field) pair, not
            one per logical-branch occurrence.

        Recursion-depth guard:
            ``_depth`` caps the logical-branch nesting at
            ``cls._MAX_LOGIC_DEPTH``; a pathologically-deep input raises
            ``ConfigurationError`` instead of blowing the stack.
        """
        if is_inactive_value(input_value, unset_sentinel=UNSET):
            return
        if _depth > cls._MAX_LOGIC_DEPTH:
            cls._raise_logic_depth_exceeded()

        if _fired is None:
            _fired = {}
        bare = _bare if _bare is not None else object.__new__(cls)

        # Fire the per-field and per-branch gates -- the active-input core
        # shared with the order side (``utils/permissions.py``). Gates key on
        # the SOURCE FIELD (one fire per field across all its lookups) and the
        # parent's per-branch ``check_<relation>_permission``; the child
        # filterset recursion + per-class ``_fired`` dedup live in the core.
        # ``normalized`` is read here only to drive the filter-only logical
        # ``and`` / ``or`` / ``not`` recursion below.
        normalized = cls._normalize_input(input_value)
        run_active_input_permission_checks(
            cls,
            input_value,
            request,
            fired=_fired,
            bare=bare,
            target_attr="filterset",
        )

        # Recurse into logical branches (and, or, not) to check permissions
        # of any nested field/lookup clauses. Same cls -> reuse ``bare`` and
        # the shared ``_fired`` map.
        and_branches = normalized.get("and") or []
        for child_input in and_branches:
            cls._run_permission_checks(
                child_input,
                request,
                _fired=_fired,
                _bare=bare,
                _depth=_depth + 1,
            )

        or_branches = normalized.get("or") or []
        for child_input in or_branches:
            cls._run_permission_checks(
                child_input,
                request,
                _fired=_fired,
                _bare=bare,
                _depth=_depth + 1,
            )

        not_branch = normalized.get("not")
        if not_branch is not None:
            cls._run_permission_checks(
                not_branch,
                request,
                _fired=_fired,
                _bare=bare,
                _depth=_depth + 1,
            )

    @staticmethod
    def _invoke_permission_method(
        bare_instance: Any,
        field_path: str,
        request: Any,
        *,
        fired: set[str] | None = None,
    ) -> None:
        """Call `check_<field_path>_permission(request)` if defined on `bare_instance`.

        Thin delegate to ``utils/permissions.py::invoke_permission_method``
        (single-sited with the order side). When ``fired`` is supplied, the
        method name is recorded after a successful fire and subsequent calls
        with the same name skip the attribute lookup -- the per-class set keyed
        out of ``_run_permission_checks``'s shared ``_fired`` map.
        """
        invoke_permission_method(bare_instance, field_path, request, fired=fired)

    @classmethod
    def _active_permission_field_paths(cls, input_value: Any) -> list[str]:
        """Return the base Django source path for each active top-level field.

        Drives ``_run_permission_checks``'s per-field gate dispatch. Emits one
        entry per supplied top-level field -- its ``django_source_path`` (the
        lookup-free source field, e.g. ``name`` for both ``name`` and
        ``name__icontains``) -- so ``check_<field>_permission`` fires once for a
        field no matter which lookups the consumer populated. Logic keys
        (``and_`` / ``or_`` / ``not_``) and ``RelatedFilter`` branches are
        excluded (walked by the logical-branch recursion / related-branch loop
        respectively); ``UNSET`` / ``None`` values are skipped (active-input-only
        contract, M2 of rev5). Thin delegate to
        ``_active_permission_targets``'s ``LEAF`` half; the filter side excludes
        the logical operator attrs and falls back to the form-key map for fields
        with no field-spec entry.
        """
        return cls._active_permission_targets(input_value)[0]

    @classmethod
    def _active_permission_targets(
        cls,
        input_value: Any,
    ) -> tuple[list[str], list[tuple[str, RelatedFilter, Any]]]:
        """Single-pass ``(leaf source paths, active related branches)`` for one level.

        The fused traversal ``_run_permission_checks`` consumes (feedback H3):
        one ``iter_active_fields`` walk yields both the per-field gate paths and
        the active ``RelatedFilter`` branches, instead of two full walks. Thin
        delegate to ``utils/permissions.py::active_permission_targets`` with the
        filter family's config; ``_active_permission_field_paths`` keeps its
        public shape by taking the ``LEAF`` half.
        """
        return active_permission_targets(
            cls,
            input_value,
            field_specs=_field_specs,
            related_attr="related_filters",
            logic_keys=_LOGIC_PYTHON_ATTRS,
            fallback_path=cls._form_key_for_python_attr,
            unset_sentinel=UNSET,
        )

    def check_permissions(self, request: Any, requested_fields: set[str] | None = None) -> None:
        """Backward-compatible thin delegate to `_run_permission_checks`.

        Cookbook callers reach for the bound-method form; the active-input
        normalization happens in `_run_permission_checks` so both entry
        points share one source of truth.
        """
        # When the cookbook caller has already normalized to a set of
        # field-path strings, walk it directly so behavior matches the
        # cookbook's contract for explicit callers.
        if requested_fields:
            for field_path in requested_fields:
                self._invoke_permission_method(self, field_path, request)
            return
        # No explicit set supplied - fall through to the active-input
        # variant. `_run_permission_checks` is a classmethod; route the
        # currently-bound form data (already a dict) through it.
        type(self)._run_permission_checks(self.data or {}, request)

    @classmethod
    def _validate_form_or_raise(cls, filterset_instance: FilterSet) -> None:
        """Raise `GraphQLError` with the canonical extensions payload.

        Decision 8 step 6 plus M10 of rev5 - `BaseFilterSet.qs` silently
        falls through to `filter_queryset` when the form has errors, so
        the explicit `is_valid()` call here is what turns a malformed
        input into a structured GraphQL response.

        Classmethod-with-self-instance shape: ``apply_sync`` /
        ``apply_async`` / ``_q_for_branch`` all reach this validator via
        ``cls._validate_form_or_raise(filterset_instance)``. The method
        is declared a classmethod so subclasses can override the
        validation policy (e.g. inject custom GraphQL-error metadata)
        without rebinding the instance method on every sibling filterset
        a recursive branch builds; the instance is passed explicitly so
        the override sees both the policy-owning class (``cls``) and the
        actual filterset whose form to validate.
        """
        if filterset_instance.form.is_valid():
            return
        raise GraphQLError(
            "Invalid filter input",
            extensions={
                "code": "FILTER_INVALID",
                "errors": filterset_instance.errors.get_json_data(),
            },
        )

    # ------------------------------------------------------------------
    # Tree-form logic substrate (`filter_queryset` override).
    # ------------------------------------------------------------------

    def filter_queryset(self, queryset: models.QuerySet) -> models.QuerySet:
        """Compose the tree-form ``and`` / ``or`` / ``not`` keys on top of the leaves.

        Decision-8 step 8 + Definition-of-done item 4(d). The flat leaf
        clauses are handled bit-for-bit by ``BaseFilterSet.filter_queryset``
        via the inherited ``super().filter_queryset(queryset)`` call; this
        override only adds the tree-form composition step on top.

        Tree keys are read off ``self.data`` rather than
        ``self.form.cleaned_data`` because ``django-filter``'s auto-built
        form declares only the leaf-filter fields, so ``cleaned_data``
        drops the ``and`` / ``or`` / ``not`` slots.
        ``_normalize_input`` already emits the wire keys at the top level
        of ``self.data``.

        Per-branch composition uses ``Q(pk__in=child_qs.values("pk"))``
        against a sibling ``cls(data=child_data, queryset=queryset)``
        instantiation. The sibling reuses the parent's already
        visibility-scoped and ``RelatedFilter``-constrained queryset, so
        the visibility-before-filter ordering pinned by H3 of rev8
        carries through to every recursive level by construction.
        """
        qs = super().filter_queryset(queryset)
        # ``_logic_depth`` is stashed on instances built by
        # ``_q_for_branch``; for the top-level instance (constructed by
        # ``apply_sync`` / ``apply_async``) it is unset and the counter
        # starts at 0. ``_apply_info`` is stashed the same way so nested
        # branches can re-derive their ``RelatedFilter`` visibility +
        # constraints (B1 of the pre-merge review); it is ``None`` for
        # instances built outside the apply pipeline, which carry no
        # related branches to re-derive. ``_nested_qs_by_branch_id`` is
        # populated only under ``apply_async``; when present, every nested
        # ``child_input`` already carries an awaited visibility map keyed by
        # ``id(child_input)`` so ``_q_for_branch`` can skip the sync derive
        # that would otherwise raise ``SyncMisuseError`` on an async-only
        # target ``get_queryset``.
        depth = getattr(self, "_logic_depth", 0)
        info = getattr(self, "_apply_info", None)
        nested_map = getattr(self, "_nested_qs_by_branch_id", None)
        q = type(self)._evaluate_logic_tree(
            qs,
            self.data or {},
            request=self.request,
            info=info,
            _depth=depth,
            _nested_qs_by_branch_id=nested_map,
        )
        return qs.filter(q)

    @classmethod
    def _evaluate_logic_tree(
        cls,
        queryset: models.QuerySet,
        tree_data: Any,
        request: Any = None,
        info: Any = None,
        *,
        _depth: int = 0,
        _nested_qs_by_branch_id: dict[int, dict[str, models.QuerySet]] | None = None,
    ) -> models.Q:
        """Build the ``Q`` expression for the ``and`` / ``or`` / ``not`` branches.

        Recursion terminates naturally when ``tree_data`` carries no
        logical keys -- an empty ``Q()`` is the identity element for
        ``qs.filter(...)`` and the no-op for an empty sub-branch list.
        ``_depth`` is the recursion-cap counter shared with
        ``_q_for_branch``; both helpers cap at ``cls._MAX_LOGIC_DEPTH``.
        ``_nested_qs_by_branch_id`` carries the pre-derived async
        visibility maps produced by ``_collect_nested_visibility_querysets_async``
        (None on the sync path).
        """
        q = models.Q()
        if not isinstance(tree_data, dict) or not tree_data:
            return q
        if _depth > cls._MAX_LOGIC_DEPTH:
            cls._raise_logic_depth_exceeded()

        and_branches = tree_data.get("and") or []
        for child_input in and_branches:
            q &= cls._q_for_branch(
                queryset,
                child_input,
                request=request,
                info=info,
                _depth=_depth + 1,
                _nested_qs_by_branch_id=_nested_qs_by_branch_id,
            )

        or_branches = tree_data.get("or") or []
        if or_branches:
            or_q = models.Q()
            for child_input in or_branches:
                or_q |= cls._q_for_branch(
                    queryset,
                    child_input,
                    request=request,
                    info=info,
                    _depth=_depth + 1,
                    _nested_qs_by_branch_id=_nested_qs_by_branch_id,
                )
            q &= or_q

        not_branch = tree_data.get("not")
        if not_branch is not None:
            q &= ~cls._q_for_branch(
                queryset,
                not_branch,
                request=request,
                info=info,
                _depth=_depth + 1,
                _nested_qs_by_branch_id=_nested_qs_by_branch_id,
            )

        return q

    @classmethod
    def _q_for_branch(
        cls,
        queryset: models.QuerySet,
        child_input: Any,
        request: Any = None,
        info: Any = None,
        *,
        _depth: int = 0,
        _nested_qs_by_branch_id: dict[int, dict[str, models.QuerySet]] | None = None,
    ) -> models.Q:
        """Materialize one nested-branch input into a ``pk__in`` ``Q``.

        Re-applies this branch's ``RelatedFilter`` visibility scoping +
        constraints exactly as ``apply_sync`` does at the top level, THEN
        normalizes the Strawberry input and builds a sibling ``FilterSet``
        instance against the constrained ``queryset``. Reading ``.qs``
        triggers ``BaseFilterSet``'s leaf-clause path against the child's
        normalized data AND re-enters this override for any deeper
        ``and`` / ``or`` / ``not`` keys the branch carries.

        The related re-application is essential: ``_normalize_input``
        STRIPS related-branch keys from the child's form data (the parent
        form cannot validate the nested-dict shape), so without deriving
        and applying them here a related branch nested inside a logical
        clause -- ``or: [{shelves: {code: {iContains: "X"}}}]`` -- would
        silently widen to the whole parent queryset (B1 of the pre-merge
        review). Under ``apply_async`` the nested visibility map is
        pre-derived via ``_collect_nested_visibility_querysets_async`` and
        threaded through ``_nested_qs_by_branch_id`` keyed by
        ``id(child_input)``; that stash is consumed by ``.get(id(...))``
        here so an async-only target ``get_queryset`` no longer raises
        ``SyncMisuseError`` mid-``.qs``. Under ``apply_sync`` the stash is
        ``None`` and the helper falls back to the sync derive, which keeps
        the documented sync-misuse error on the pure-sync path.

        ``_depth`` and ``_apply_info`` are stashed on the sibling instance
        so ``filter_queryset`` can carry the recursion counter and the
        resolver ``info`` across django-filter's ``.qs`` machinery into the
        next ``_evaluate_logic_tree`` call. Without this hand-off the depth
        counter would reset at every nesting level and deeper branches
        would lose the ``info`` needed to re-derive their related
        visibility (the recursion path crosses through django-filter's
        ``BaseFilterSet`` which we do not own and cannot pass kwargs
        through). ``_nested_qs_by_branch_id`` is stashed on the sibling
        too so a deeper ``_q_for_branch`` call (via the sibling's own
        ``filter_queryset`` -> ``_evaluate_logic_tree``) can keep
        consulting the pre-derived map.

        Perf note (M-filters-6 review, accepted as-is): constructing the
        sibling ``cls(...)`` per branch triggers django-filter's
        ``BaseFilterSet.__init__`` deepcopy of ``base_filters``, so cost
        scales with branches x filters. This is correctness-neutral and
        bounded by ``_MAX_LOGIC_DEPTH``; not optimized here because doing so
        means reaching into upstream's per-instance copy semantics. Profile
        before optimizing if a deeply-nested query ever shows up hot.
        """
        if _nested_qs_by_branch_id is not None:
            child_qs_by_branch = _nested_qs_by_branch_id.get(id(child_input))
            if child_qs_by_branch is None:
                # Defensive fallback: the pre-pass walks every reachable
                # logical branch, but a consumer who short-circuits past
                # the walker (e.g. by calling ``_q_for_branch`` directly)
                # still gets a correct result via the sync derive. Apply
                # the same async/sync caveat the docstring names.
                child_qs_by_branch = cls._derive_related_visibility_querysets_sync(
                    child_input,
                    info,
                )
        else:
            child_qs_by_branch = cls._derive_related_visibility_querysets_sync(child_input, info)
        constrained = cls._apply_related_constraints(child_input, queryset, child_qs_by_branch)
        child_data = cls._normalize_input(child_input)
        child_set = cls(data=child_data, queryset=constrained, request=request)
        child_set._logic_depth = _depth
        child_set._apply_info = info
        child_set._nested_qs_by_branch_id = _nested_qs_by_branch_id
        cls._validate_form_or_raise(child_set)
        return models.Q(pk__in=child_set.qs.values("pk"))

    @classmethod
    def _apply_related_constraints(
        cls,
        input_value: Any,
        parent_qs: models.QuerySet,
        child_qs_by_branch: dict[str, models.QuerySet],
    ) -> models.QuerySet:
        """Constrain `parent_qs` by each active branch's intersected child qs.

        M4-of-rev3 + H3-of-rev8 - the explicit `RelatedFilter(queryset=...)`
        constraint AND-intersects with the visibility-scoped child qs
        from step 3, then a ``pk__in=<parent-pk subquery>`` restriction
        built from ``<rel>__in=<intersected>`` runs ONCE for every active
        branch. Inactive branches do not constrain the parent.
        """
        constrained = parent_qs
        for field_name, related_filter, _ in cls._iter_active_related_branches(input_value):
            child_qs = child_qs_by_branch.get(field_name)
            explicit = (
                related_filter.extra.get("queryset")
                if related_filter._has_explicit_queryset
                else None
            )
            if child_qs is None and explicit is None:
                continue
            if child_qs is not None and explicit is not None:
                # Django raises an opaque ``TypeError: Cannot combine
                # queries on two different base models`` from
                # ``Query.combine`` if the consumer-supplied
                # ``RelatedFilter(queryset=...)`` is keyed on a
                # different model class than the target filterset's
                # ``_meta.model``. Surface a typed ``ConfigurationError``
                # naming the filter and both models so a GraphQL consumer
                # gets an actionable message instead of the raw
                # ``TypeError``.
                #
                # The comparison uses ``is`` identity because Django's
                # own ``Query.combine`` does the same (``self.model !=
                # rhs.model``) - proxies and multi-table-inheritance
                # children carry distinct ``model`` identities even
                # though they share a database table with their
                # concrete parent. Consumers who need to mix
                # proxy / concrete must pass an explicit queryset of
                # the target filterset's exact ``_meta.model`` class.
                if explicit.model is not child_qs.model:
                    raise ConfigurationError(
                        f"RelatedFilter {cls.__qualname__}.{field_name}: "
                        f"the explicit ``queryset=`` is keyed on "
                        f"{explicit.model.__qualname__} but the target "
                        f"filterset is keyed on "
                        f"{child_qs.model.__qualname__}. Pass a queryset "
                        f"of {child_qs.model.__qualname__} instances to "
                        "``RelatedFilter(queryset=...)``; proxy and "
                        "multi-table-inheritance children are NOT "
                        "accepted because Django's queryset ``&`` "
                        "operator rejects mixed model classes.",
                    )
                intersected = explicit & child_qs
            else:
                intersected = child_qs if child_qs is not None else explicit
            # Build the parent restriction against the relation's ORM path
            # (``related_filter.field_name``), NOT the declared attribute name the
            # loop iterates by. The two diverge whenever a consumer gives a
            # ``RelatedFilter`` a friendlier GraphQL name than its ORM accessor
            # (e.g. ``visible_shelves = RelatedFilter(ShelfFilter, field_name="shelves")``);
            # keying off the declared name would emit ``<declared>__in`` against a
            # non-existent relation and Django would raise ``FieldError``.
            # ``child_qs_by_branch`` stays keyed by the declared name (see
            # ``_derive_related_visibility_querysets_*``), so only this final
            # ``.filter(...)`` switches to the ORM path.
            #
            # The restriction is wrapped as ``pk__in=<parent-pk subquery>``
            # rather than filtering ``<rel>__in=<intersected>`` directly: for
            # a many-side relation (reverse FK / M2M) the direct form JOINs
            # the child table onto the parent queryset, so a parent with N
            # matching children comes back N times - duplicate nodes in
            # lists / connections and corrupted pagination counts. The pk
            # subquery collapses those duplicates inside the ``IN`` clause
            # (no ``.distinct()``, which would mutate consumer-visible
            # queryset state) and matches the ``Q(pk__in=...)`` shape
            # ``_q_for_branch`` already emits, so a related branch answers
            # identically whether it appears directly or nested under
            # ``and`` / ``or`` / ``not``. The subquery derives from
            # ``constrained`` itself (not a fresh manager) so custom
            # default-manager filtering and the queryset's database alias
            # carry through unchanged.
            matching_parent_pks = constrained.filter(
                **{f"{related_filter.field_name}__in": intersected},
            ).values("pk")
            constrained = constrained.filter(pk__in=matching_parent_pks)
        return constrained

    @classmethod
    def _apply_common_prelude(
        cls,
        input_value: Any,
        queryset: models.QuerySet,
        info: Any,
        child_qs_by_branch: dict[str, models.QuerySet],
    ) -> tuple[FilterSet, Any]:
        """Build the filterset_instance + request shared by apply_sync / apply_async.

        Captures the verbatim normalize / request / constraints / ctor /
        ``_apply_info`` stash sequence both apply paths run identically.
        The async-only ``_nested_qs_by_branch_id`` stash stays inline in
        ``apply_async`` (no sync analog) - callers attach it on the
        returned instance.
        """
        data = cls._normalize_input(input_value)
        request = cls._request_from_info(info)
        constrained = cls._apply_related_constraints(input_value, queryset, child_qs_by_branch)
        filterset_instance = cls(data=data, queryset=constrained, request=request)
        filterset_instance._apply_info = info
        return filterset_instance, request

    @classmethod
    def _apply_common_finalize(
        cls,
        filterset_instance: FilterSet,
        input_value: Any,
        request: Any,
    ) -> models.QuerySet:
        """Run the perm check + form validate + ``.qs`` read trailer.

        Sync ``apply_sync`` calls this directly; async ``apply_async``
        wraps the single call in ``sync_to_async(..., thread_sensitive=True)``
        so a consumer's ``check_*_permission`` hook / custom ``method=``
        filter body / leaf-clause ORM evaluation does not block the
        event loop. The thread-sensitive shape mirrors how Django wraps
        consumer sync hooks on its own async paths.
        """
        cls._run_permission_checks(input_value, request)
        cls._validate_form_or_raise(filterset_instance)
        return filterset_instance.qs

    @classmethod
    def apply_sync(
        cls,
        input_value: Any,
        queryset: models.QuerySet,
        info: Any,
    ) -> models.QuerySet:
        """Sync resolver entry point (Decision 8 / H3 of rev8).

        Steps run in the order pinned by H3 of rev8: derive visibility
        querysets, resolve the request, apply related constraints
        BEFORE constructing the filterset (so the constraints land in
        `self.queryset` and propagate through to `.qs`), then permission
        check, form validate, and return the materialized queryset.
        """
        child_qs_by_branch = cls._derive_related_visibility_querysets_sync(input_value, info)
        filterset_instance, request = cls._apply_common_prelude(
            input_value,
            queryset,
            info,
            child_qs_by_branch,
        )
        return cls._apply_common_finalize(filterset_instance, input_value, request)

    @classmethod
    async def apply_async(
        cls,
        input_value: Any,
        queryset: models.QuerySet,
        info: Any,
    ) -> models.QuerySet:
        """Async sibling of `apply_sync` awaiting every blocking step.

        Steps:
            1. Await the top-level ``_derive_related_visibility_querysets_async``
               so every active ``RelatedFilter`` branch's target
               ``get_queryset`` runs on the async path.
            2. Pre-walk every ``and`` / ``or`` / ``not`` arm via
               ``_collect_nested_visibility_querysets_async`` so nested
               branches whose target type's ``get_queryset`` is async-only
               get their visibility maps awaited BEFORE the sync ``.qs``
               read fans into ``_q_for_branch``. Without this step,
               ``_q_for_branch``'s sync derive would raise
               ``SyncMisuseError`` mid-``.qs``.
            3. Build the filterset via ``_apply_common_prelude`` (shared
               with ``apply_sync``) and stash the nested-visibility map
               on the instance - the async-only step with no sync analog.
            4. Route ``_apply_common_finalize`` (perm check + form
               validate + ``.qs`` read) through a single
               ``sync_to_async(thread_sensitive=True)`` so a consumer's
               ``check_*_permission`` hook that performs a blocking ORM
               read does not block the event loop. The thread-sensitive
               shape mirrors how Django wraps consumer sync hooks on its
               own async paths.
        """
        child_qs_by_branch = await cls._derive_related_visibility_querysets_async(
            input_value,
            info,
        )
        nested_qs_by_branch_id = await cls._collect_nested_visibility_querysets_async(
            input_value,
            info,
        )
        filterset_instance, request = cls._apply_common_prelude(
            input_value,
            queryset,
            info,
            child_qs_by_branch,
        )
        filterset_instance._nested_qs_by_branch_id = nested_qs_by_branch_id
        return await sync_to_async(cls._apply_common_finalize, thread_sensitive=True)(
            filterset_instance,
            input_value,
            request,
        )

    @classmethod
    def apply(
        cls,
        input_value: Any,
        queryset: models.QuerySet,
        info: Any,
    ) -> models.QuerySet:
        """Thin dispatcher - picks `apply_sync` and translates sync-misuse.

        Decision 8 / M5 of rev6 - catches the typed ``SyncMisuseError``
        raised by ``apply_type_visibility_sync`` and rethrows as
        ``RuntimeError`` with the actionable "use apply_async instead"
        message consumers can match on. Class-based dispatch closes the
        round-3 loop: no substring-matching against a constant string.
        """
        try:
            return cls.apply_sync(input_value, queryset, info)
        except SyncMisuseError as exc:
            # ``from exc`` already records the original ``SyncMisuseError``
            # on ``__cause__``; standard traceback machinery surfaces it.
            # Avoid duplicating the cause's ``str()`` in the message here
            # (the cause prints once via the chain, twice if both included).
            raise RuntimeError(
                "FilterSet.apply called against async get_queryset; use apply_async instead.",
            ) from exc
