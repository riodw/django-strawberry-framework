"""`FilterSetMetaclass` and `FilterSet` foundation (Slice 1).

Layers 3 and 4 of the spec-021 six-layer pipeline plus the
Decision-8 / M1-of-rev5 named-helper decomposition of `apply_sync` /
`apply_async` / `apply`. The metaclass is a verbatim port of
`django_graphene_filters/filterset.py::FilterSetMetaclass`; `FilterSet`
mixes the cookbook's cycle-safe `get_filters` into a
`django_filters.filterset.BaseFilterSet` subclass per spec-021 Decision 5.

The Decision-4 owner-aware Relay-vs-scalar conditional lives only inside
`filter_for_field` / `filter_for_lookup` to keep the runtime override as
the single source of truth (Slice 2's factory derives shape from the
resolved filter instances, not from a parallel map).
"""

from __future__ import annotations

import copy
from collections import OrderedDict
from typing import TYPE_CHECKING, Any, ClassVar

from django.db import models
from django.http import HttpRequest
from django_filters import filterset
from django_filters.utils import get_model_field
from graphql import GraphQLError
from strawberry import UNSET

from ..exceptions import ConfigurationError
from ..registry import registry
from ..sets_mixins import ClassBasedTypeNameMixin
from ..types.relay import (
    SyncMisuseError,
    _apply_get_queryset_async,
    _apply_get_queryset_sync,
    implements_relay_node,
)
from .base import GlobalIDFilter, GlobalIDMultipleChoiceFilter, RelatedFilter
from .inputs import _LOGIC_KEYS, LOOKUP_NAME_MAP, _field_specs, normalize_input_value

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
        if meta_class and hasattr(meta_class, "filter_fields") and not hasattr(meta_class, "fields"):
            meta_class.fields = meta_class.filter_fields

        new_class = super().__new__(cls, name, bases, attrs)

        new_class.related_filters = OrderedDict(
            [
                (filter_name, f)
                for filter_name, f in new_class.declared_filters.items()
                if isinstance(f, RelatedFilter)
            ],
        )

        for f in new_class.related_filters.values():
            f.bind_filterset(new_class)

        return new_class


def _expand_related_filter(
    filter_name: str,
    f: RelatedFilter,
) -> OrderedDict[str, Any]:
    """Expand `f` against its target filterset's resolved filters.

    Verbatim port of the cookbook's `expand_related_filter`. The
    per-field deep-copy avoids mutating the target filterset's
    instances when the parent rebinds `field_name` to the relation
    path. Module-level helper because the expansion has no metaclass
    state — moving it off the metaclass keeps the call site
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
    spec-021 Decision 5; the cookbook's lazy-resolution Layers 3 and 4
    are folded in via `FilterSetMetaclass` and `get_filters`. The
    Decision-8 / M1-of-rev5 named helpers decompose `apply_sync` and
    `apply_async` so each step can be exercised in isolation; `apply`
    stays as a thin dispatcher that translates the typed
    `SyncMisuseError` from `_apply_get_queryset_sync` into a
    `RuntimeError` consumers can match on.

    `_owner_definition` is the seam Slice 3 binds at finalizer phase 2.5
    per H4 of rev4. Slice 1 ships the slot declared `None` and the
    fallback branch in `filter_for_field` / `filter_for_lookup` that
    consults `registry.primary_for(...)` so package-internal tests can
    exercise the Relay-vs-scalar conditional before owner binding lands.
    """

    # Slice-3 binding seam — populated by `finalize_django_types` phase 2.5.
    _owner_definition: DjangoTypeDefinition | None = None

    # Cache for fully-resolved filters per Layer 4 of Decision 3.
    _expanded_filters = None
    # Recursion guard around `get_filters` so a self-referential
    # `RelatedFilter` does not blow the stack.
    _is_expanding_filters = False

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

    # ``ClassBasedTypeNameMixin`` naming suffixes. The root input type keeps
    # the mixin's default ``"InputType"`` (``FooFilter`` -> ``FooFilterInputType``);
    # the per-field operator bag overrides to ``"FilterInputType"``
    # (``FooFilter`` + ``Bar`` -> ``FooFilterBarFilterInputType``), matching the
    # names ``inputs.py`` produced inline before the naming rule was shared.
    _field_type_suffix: str = "FilterInputType"

    # ------------------------------------------------------------------
    # Layer 4 — cycle-safe filter expansion (cookbook port).
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
            from different threads can race on the flag — the second
            thread sees ``_is_expanding_filters=True`` and short-
            circuits to ``super().get_filters()``, yielding the
            unexpanded set. Tests that need to call ``get_filters()``
            from multiple threads must serialize the call themselves;
            do not introduce a ``threading.local`` here without first
            confirming a real consumer call path requires it.
        """
        if cls.__dict__.get("_expanded_filters") is not None:
            return cls.__dict__["_expanded_filters"]

        if cls.__dict__.get("_is_expanding_filters", False):
            return super().get_filters()

        cls._is_expanding_filters = True
        try:
            all_filters = super().get_filters()
            if cls._meta.model is not None:
                related_filters_val = getattr(cls, "related_filters", OrderedDict())
                for filter_name, f in related_filters_val.items():
                    expanded = _expand_related_filter(filter_name, f)
                    all_filters.update(expanded)
            # TODO(spec-021-filters-0_0_8 Meta.search_fields card 0.1.2):
            # wire `construct_search(all_filters)` from
            # `django_strawberry_framework.filters.inputs.LOOKUP_PREFIXES` here.

            # Cache only when both conditions hold:
            # 1. `related_filters` is on this class (not inherited from
            #    `FilterSet` itself, which carries the empty OrderedDict
            #    `FilterSetMetaclass.__new__` set on the in-flight class
            #    AFTER `super().__new__` returns).
            # 2. Every `_filterset` is a real class (no unresolved string
            #    forward references remain).
            if "related_filters" in cls.__dict__ and all(
                not isinstance(f._filterset, str) for f in cls.related_filters.values()
            ):
                cls._expanded_filters = all_filters
                cls.base_filters = all_filters
            return all_filters
        finally:
            cls._is_expanding_filters = False

    @classmethod
    def get_fields(cls) -> OrderedDict:
        """Expand per-field ``"__all__"`` and narrow the top-level ``"__all__"`` sweep.

        Two overrides over ``django-filter``'s ``get_fields``:

        - **Per-field ``"__all__"``** (dict form, e.g. ``{"name": "__all__"}``):
          ``django-filter`` expands only the top-level ``fields = "__all__"``
          and passes a per-field ``"__all__"`` value through verbatim — which
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
                    fields[field_name] = _lookups_for_field(get_model_field(model, field_name))

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
        m2m_names = {f.name for f in model._meta.get_fields() if isinstance(f, models.ManyToManyField)}
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

        Own-PK branch (spec-021 L566-567 + L607): when ``field`` is the
        owning model's primary key AND the owning ``DjangoType`` itself
        implements ``relay.Node``, the field becomes ``GlobalIDFilter`` —
        the OWNER is the Relay node so its PK column is a GlobalID over
        the wire.
        """
        default = super().filter_for_field(field, field_name, lookup_expr)
        if cls._is_own_pk_under_relay_owner(field):
            # The owner's own PK is a GlobalID over the wire. Honor the
            # lookup cardinality: an ``in`` lookup consumes a LIST of
            # GlobalIDs (multi-choice), every other lookup a single one.
            # Without this split ``id: {in: [...]}`` collapsed to a single
            # ``GlobalIDFilter`` and silently dropped to a scalar input.
            own_pk_filter_class = (
                GlobalIDMultipleChoiceFilter if default.lookup_expr == "in" else GlobalIDFilter
            )
            return own_pk_filter_class(
                field_name=default.field_name,
                lookup_expr=default.lookup_expr,
                **default.extra,
            )
        target_type = cls._resolve_relation_target_type(field, field_name)
        if target_type is None or not implements_relay_node(target_type):
            return default
        relay_filter_class = cls._relay_filter_class_for_field(field)
        return relay_filter_class(
            field_name=default.field_name,
            lookup_expr=default.lookup_expr,
            **default.extra,
        )

    @classmethod
    def filter_for_lookup(cls, field: Any, lookup_type: str) -> tuple[Any, dict[str, Any]]:
        """Mirror `filter_for_field`'s Relay-vs-scalar conditional per-lookup.

        Non-relation fields defer to the upstream pair-return shape unless
        the field is the owner's own PK and the owner is Relay-Node-shaped
        (own-PK branch per spec-021 L566-567). For relation fields a
        Relay-Node-shaped target maps to a ``(GlobalIDFilter, params)``
        pair (or ``GlobalIDMultipleChoiceFilter`` for multi-valued
        relations); otherwise the upstream return is passed through.
        """
        default_class, params = super().filter_for_lookup(field, lookup_type)
        if cls._is_own_pk_under_relay_owner(field):
            # Own-PK GlobalID, cardinality by lookup: ``in`` -> list of
            # GlobalIDs (multi-choice), otherwise a single GlobalID.
            if lookup_type == "in":
                return GlobalIDMultipleChoiceFilter, params
            return GlobalIDFilter, params
        if not field.is_relation:
            return default_class, params
        target_type = cls._resolve_relation_target_type(field, getattr(field, "name", None))
        if target_type is None or not implements_relay_node(target_type):
            return default_class, params
        return cls._relay_filter_class_for_field(field), params

    @classmethod
    def _is_own_pk_under_relay_owner(cls, field: Any) -> bool:
        """Return True iff ``field`` is the owning model's PK and owner is Relay.

        Own-PK branch per spec-021 L566-567 + L607: when a ``FilterSet``
        whose owning ``DjangoType`` implements ``relay.Node`` filters on
        its own primary key, the wire shape is a Relay GlobalID — so the
        filter for that PK is ``GlobalIDFilter`` rather than the scalar
        upstream default. Resolves only when ``_owner_definition`` is
        bound (Slice 3 phase-2.5 binding) so package-internal tests that
        run pre-binding keep the upstream shape.
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
        `ManyToOneRel`, reverse M2M `ManyToManyRel`) — every Django
        relation field that sets `many_to_many=True` or `one_to_many=True`
        — map to `GlobalIDMultipleChoiceFilter`; single-valued relations
        (forward `ForeignKey` / `OneToOneField` and reverse `OneToOneRel`)
        map to `GlobalIDFilter`. This mirrors `django-filter`'s upstream
        choice between `ModelChoiceFilter` and `ModelMultipleChoiceFilter`
        and matches Decision 4's parity-floor split between the two
        Relay-aware primitives.
        """
        if getattr(field, "many_to_many", False) or getattr(field, "one_to_many", False):
            return GlobalIDMultipleChoiceFilter
        return GlobalIDFilter

    @classmethod
    def _resolve_relation_target_type(
        cls,
        field: Any,
        field_name: str | None,
    ) -> type | None:
        """Look up the registered target `DjangoType` for a relation field.

        Consults `_owner_definition.related_target_for(...)` when the
        Slice-3 binding has landed; otherwise falls back to
        `registry.primary_for(field.related_model)`. Non-relation fields
        return `None`.
        """
        if not getattr(field, "is_relation", False):
            return None
        owner = cls._owner_definition
        if owner is not None and field_name is not None:
            # Owner-aware path (Slice-3 binding has landed): resolve the
            # target `DjangoType` through `owner.related_target_for(...)`.
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

    @classmethod
    def _normalize_input(cls, input_value: Any) -> dict[str, Any]:
        """Translate a Strawberry input dataclass into `django-filter` form data.

        Slice 2 completes the per-primitive value normalization: each
        scalar attr passes through ``normalize_input_value`` so
        ``relay.GlobalID`` -> ``node_id``, Strawberry enum -> ``.value``,
        and ``RangeFilter`` -> positional ``{name}_0`` / ``{name}_1``
        keys all land in ``data`` correctly. Related-branch keys (the
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
        if input_value is None or input_value is UNSET:
            return {}
        if isinstance(input_value, dict):
            items = list(input_value.items())
        else:
            dataclass_fields = getattr(input_value, "__dataclass_fields__", None)
            if dataclass_fields is None:
                return {}
            items = [(name, getattr(input_value, name)) for name in dataclass_fields]

        # Related-branch keys are owned by the apply pipeline's
        # `_apply_related_constraints` step (which constrains the parent
        # queryset before instantiation); leaving them in the form-data
        # dict would cause `django-filter`'s form validation to reject
        # the nested-dict shape.
        related_filters = getattr(cls, "related_filters", {}) or {}
        related_keys = set(related_filters.keys())

        all_filters = cls.get_filters() if cls._meta.model is not None else {}

        data: dict[str, Any] = {}
        logic_lookup = dict(_LOGIC_KEYS)
        for python_attr, raw_value in items:
            # Strawberry input dataclasses default unsupplied fields to
            # ``strawberry.UNSET``; treat it the same as ``None`` so the
            # form sees only consumer-supplied keys.
            if raw_value is None or raw_value is UNSET:
                continue
            if python_attr in logic_lookup:
                data[logic_lookup[python_attr]] = raw_value
                continue
            if python_attr in related_keys:
                # Related branches travel through `_apply_related_constraints`,
                # not the parent form.
                continue
            spec = _field_specs.get((cls, python_attr))
            django_source_path = spec.django_source_path if spec is not None else None
            # Per spec-021 L518-605 (Slice 2's per-field operator bag), top-
            # level scalar fields wrap a nested ``<Field>FilterInputType``
            # dataclass whose attrs map to ``django-filter`` lookups
            # (``exact`` / ``i_contains`` / ``in_`` / ...). Iterate the bag
            # to produce ``<source>__<lookup>`` form-data keys.
            bag_items = cls._operator_bag_items(raw_value)
            if bag_items is not None:
                base_path = django_source_path or cls._form_key_for_python_attr(python_attr)
                for lookup_attr, lookup_value in bag_items:
                    # Mirror the outer loop's UNSET guard so a partially-
                    # supplied operator bag (e.g.
                    # ``title: { exact: UNSET, icontains: "foo" }``) does
                    # not leak the UNSET sentinel through to
                    # ``normalize_input_value``; a Strawberry input
                    # dataclass defaults every unsupplied lookup to
                    # ``UNSET`` rather than ``None``, so this is the
                    # common case for any consumer who fills some but
                    # not all lookups.
                    if lookup_value is None or lookup_value is UNSET:
                        continue
                    django_lookup = cls._form_key_for_python_attr(lookup_attr)
                    form_key = base_path if django_lookup == "exact" else f"{base_path}__{django_lookup}"
                    filter_instance = all_filters.get(form_key) or all_filters.get(
                        f"{base_path}__{django_lookup}",
                    )
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
                        data[form_key] = normalized
                continue
            form_key = django_source_path or cls._form_key_for_python_attr(python_attr)
            filter_instance = all_filters.get(form_key)
            if filter_instance is None:
                data[form_key] = raw_value
                continue
            normalized = normalize_input_value(filter_instance, raw_value, field_name=form_key)
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

        Slice 2's ``_build_input_fields`` wraps each scalar field's
        lookups in a nested ``<Field>FilterInputType`` dataclass. The
        normalizer detects that shape via ``__dataclass_fields__``;
        ``RelatedFilter`` boundary values are handled separately via
        ``_apply_related_constraints`` so this helper does NOT see them.
        Returns ``None`` for scalar inputs that are not operator bags.
        """
        if isinstance(raw_value, (str, bytes, int, float, bool)):
            return None
        if isinstance(raw_value, (list, tuple, set, frozenset)):
            return None
        dataclass_fields = getattr(raw_value, "__dataclass_fields__", None)
        if dataclass_fields is None:
            return None
        return [(name, getattr(raw_value, name)) for name in dataclass_fields]

    @staticmethod
    def _form_key_for_python_attr(python_attr: str) -> str:
        """Map a Strawberry dataclass attr back to a `django-filter` form key.

        Walks `LOOKUP_NAME_MAP` once for `(python_attr, ...)` matches.
        Falls through to the attr name verbatim when no lookup pair
        rewrites it. Used by ``_normalize_input`` both at the top-level
        scalar branch and inside the per-field operator-bag iteration
        (mapping ``i_contains`` -> ``icontains`` etc.); the two callers
        share this single helper rather than duplicating the walk.
        """
        for django_lookup, (mapped_python_attr, _) in LOOKUP_NAME_MAP.items():
            if mapped_python_attr == python_attr:
                return django_lookup
        return python_attr

    @classmethod
    def _request_from_info(cls, info: Any) -> Any:
        """Resolve the Django request from `info.context` (M8 of rev5).

        Canonical Strawberry-Django shape: `info.context.request`. The
        wrapper-less alternative `isinstance(info.context, HttpRequest)`
        is detected so consumers running a bare-HttpRequest context (the
        Django test client default) work without bespoke wiring. Any
        other shape raises `ConfigurationError`.
        """
        context = getattr(info, "context", None)
        if context is None:
            raise ConfigurationError(
                "FilterSet.apply requires `info.context`; received `info` without a context.",
            )
        request = getattr(context, "request", None)
        if request is not None:
            return request
        if isinstance(context, HttpRequest):
            return context
        raise ConfigurationError(
            f"FilterSet.apply could not resolve a Django HttpRequest from `info.context` "
            f"(got {type(context).__name__}). Expected `info.context.request` or a bare HttpRequest.",
        )

    @classmethod
    def _iter_active_related_branches(
        cls,
        input_value: Any,
    ) -> list[tuple[str, RelatedFilter, Any]]:
        """List `(field_name, related_filter, child_input)` for present branches.

        Active-branch scoping (M4 of rev3) — a `RelatedFilter` is "active"
        when its key is present in the input, regardless of the inner
        value's emptiness. Inactive branches are skipped end-to-end
        (visibility derivation, constraint application, permission
        recursion) so an empty filter does not pre-constrain the parent
        queryset.
        """
        related_filters = getattr(cls, "related_filters", {})
        if not related_filters:
            return []
        active: list[tuple[str, RelatedFilter, Any]] = []
        for field_name, related_filter in related_filters.items():
            child_input = cls._extract_branch_value(input_value, field_name)
            if child_input is None:
                continue
            active.append((field_name, related_filter, child_input))
        return active

    @staticmethod
    def _extract_branch_value(input_value: Any, field_name: str) -> Any:
        """Return the value at `field_name` on a dataclass-or-dict input.

        Strawberry input dataclasses default unsupplied fields to
        ``strawberry.UNSET`` rather than ``None``; collapse that sentinel
        to ``None`` so the active-branch caller treats UNSET the same as
        a missing key (no permission gate, no constraint application).
        """
        if input_value is None:
            return None
        if isinstance(input_value, dict):
            value = input_value.get(field_name)
        else:
            value = getattr(input_value, field_name, None)
        if value is UNSET:
            return None
        return value

    @classmethod
    def _derive_related_visibility_querysets_sync(
        cls,
        input_value: Any,
        info: Any,
    ) -> dict[str, models.QuerySet]:
        """Run each active branch's target ``get_queryset(...)`` then recurse.

        Reuses ``django_strawberry_framework/types/relay.py::_apply_get_queryset_sync``
        — the existing helper handles the sync-misuse detection and
        raises ``SyncMisuseError`` (a ``ConfigurationError`` and
        ``RuntimeError`` subclass); ``apply``'s catch-and-rethrow
        translates that into a ``RuntimeError`` consumers can match
        on via the actionable "use apply_async instead" message.

        After the visibility hook runs, the child filterset's
        ``apply_sync`` is invoked against the visibility-scoped queryset
        so nested input clauses (e.g. ``shelves: { code: { iContains:
        "A" } }``) narrow the child queryset BEFORE the parent's
        ``<rel>__in=<intersected>`` clause is computed (spec-021 L668-678).
        """
        result: dict[str, models.QuerySet] = {}
        for field_name, related_filter, child_input in cls._iter_active_related_branches(
            input_value,
        ):
            target_type = cls._target_type_for_related_filter(related_filter)
            child_filterset = related_filter.filterset
            if target_type is None or child_filterset is None:
                continue
            child_model = child_filterset._meta.model
            child_base = child_model._default_manager.all()
            scoped = _apply_get_queryset_sync(target_type, child_base, info)
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
        for field_name, related_filter, child_input in cls._iter_active_related_branches(
            input_value,
        ):
            target_type = cls._target_type_for_related_filter(related_filter)
            child_filterset = related_filter.filterset
            if target_type is None or child_filterset is None:
                continue
            child_model = child_filterset._meta.model
            child_base = child_model._default_manager.all()
            scoped = await _apply_get_queryset_async(target_type, child_base, info)
            result[field_name] = await child_filterset.apply_async(child_input, scoped, info)
        return result

    @staticmethod
    def _target_type_for_related_filter(related_filter: RelatedFilter) -> type | None:
        """Resolve the `DjangoType` whose ``get_queryset()`` scopes the branch.

        Prefer the child filterset's *bound owner* — the type the consumer
        explicitly wired via ``Meta.filterset_class`` (``_owner_definition``,
        bound at finalizer phase 2.5) — over a model-only registry lookup. When a
        child model has more than one registered ``DjangoType`` and the child
        filterset is bound to a non-primary one, a model-only lookup resolves the
        *primary* type and runs ITS ``get_queryset()`` against the non-primary's
        filterset, scoping the related branch by the wrong visibility hook (a
        silent row-leak). ``definition.origin`` is the same ``DjangoType`` class
        the registry stores (``types/base.py`` registers ``cls`` with
        ``origin=cls``), so both branches hand ``_apply_get_queryset_*`` an object
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

        Active-input-only per M2 of rev5 — a declared `check_*` gate that
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
            once — the per-class set keyed on the child dedups the
            re-entry from the second arm.

        Double-dispatch contract:
            For an active ``RelatedFilter`` branch named ``shelves``
            both gates fire — the parent's ``check_shelves_permission``
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
        if input_value is None or input_value is UNSET:
            return
        if _depth > cls._MAX_LOGIC_DEPTH:
            raise ConfigurationError(
                f"FilterSet {cls.__qualname__}: logical-branch nesting exceeded "
                f"_MAX_LOGIC_DEPTH={cls._MAX_LOGIC_DEPTH}. Flatten the filter input "
                "or split into multiple queries.",
            )

        if _fired is None:
            _fired = {}
        class_fired = _fired.setdefault(cls, set())
        bare = _bare if _bare is not None else object.__new__(cls)

        normalized = cls._normalize_input(input_value)
        # Permission gates are keyed on the SOURCE FIELD, not the
        # lookup-expanded form key: ``check_<field>_permission`` gates a
        # field across ALL its lookups (``exact`` / ``icontains`` /
        # ``in`` / ``range`` / ...). Iterating ``normalized``'s flattened
        # form keys would build ``check_<field>_<lookup>_permission`` and
        # silently skip the gate for every non-``exact`` lookup -- only
        # ``exact`` lands a suffix-free form key (``name``), so the gate
        # fired for it by accident while ``name__icontains`` etc. slipped
        # past ungated. ``_active_permission_field_paths`` strips back to
        # the per-field source path so the gate fires once per field.
        for field_path in cls._active_permission_field_paths(input_value):
            cls._invoke_permission_method(bare, field_path, request, fired=class_fired)

        for field_name, related_filter, child_input in cls._iter_active_related_branches(input_value):
            child_filterset = related_filter.filterset
            if child_filterset is not None and hasattr(child_filterset, "_run_permission_checks"):
                # Child filterset is a different class; it keys its own
                # per-class set inside the shared ``_fired`` map (so a
                # same-class child re-entered from sibling branches still
                # dedups) and allocates its own bare instance.
                child_filterset._run_permission_checks(child_input, request, _fired=_fired)
            # Per-branch permission gate on the parent — fires e.g.
            # `check_shelves_permission` when the `shelves` branch is
            # active. Child filterset's own field gates fire via the
            # recursive call above. Deduped against the parent's
            # per-class set so an ``or: [{shelves: ...}, {shelves: ...}]``
            # shape fires the parent's per-branch gate once.
            cls._invoke_permission_method(bare, field_name, request, fired=class_fired)

        # Recurse into logical branches (and, or, not) to check permissions
        # of any nested field/lookup clauses. Same cls → reuse ``bare`` and
        # the shared ``_fired`` map.
        and_branches = normalized.get("and") or []
        for child_input in and_branches:
            cls._run_permission_checks(child_input, request, _fired=_fired, _bare=bare, _depth=_depth + 1)

        or_branches = normalized.get("or") or []
        for child_input in or_branches:
            cls._run_permission_checks(child_input, request, _fired=_fired, _bare=bare, _depth=_depth + 1)

        not_branch = normalized.get("not")
        if not_branch is not None:
            cls._run_permission_checks(not_branch, request, _fired=_fired, _bare=bare, _depth=_depth + 1)

    @staticmethod
    def _invoke_permission_method(
        bare_instance: Any,
        field_path: str,
        request: Any,
        *,
        fired: set[str] | None = None,
    ) -> None:
        """Call `check_<field_path>_permission(request)` if defined on `bare_instance`.

        When ``fired`` is supplied, the method-name is recorded after a
        successful fire and subsequent calls with the same name skip the
        attribute lookup entirely. The dedup is scoped to the supplied
        set — ``_run_permission_checks`` passes the per-class set keyed
        out of its shared ``_fired`` map.
        """
        method_name = f"check_{field_path.replace('__', '_')}_permission"
        if fired is not None and method_name in fired:
            return
        method = getattr(bare_instance, method_name, None)
        if callable(method):
            method(request)
            if fired is not None:
                fired.add(method_name)

    @classmethod
    def _active_permission_field_paths(cls, input_value: Any) -> list[str]:
        """Return the base Django source path for each active top-level field.

        Drives ``_run_permission_checks``'s per-field gate dispatch. Emits
        one entry per supplied top-level field -- its ``django_source_path``
        (the lookup-free source field, e.g. ``name`` for both ``name`` and
        ``name__icontains``) -- so ``check_<field>_permission`` fires once
        for a field no matter which lookups the consumer populated. This
        is the fix for the form-key dispatch bug: the per-field operator
        bag means a single top-level field carries many lookups, and the
        gate must key on the field, not the lookup.

        Logic keys (``and`` / ``or`` / ``not``) and ``RelatedFilter``
        branches are excluded here -- the former are walked by the
        logical-branch recursion, the latter by the related-branch loop
        (each fires its own per-branch gate). ``UNSET`` / ``None`` values
        are skipped: a Strawberry input dataclass defaults unsupplied
        fields to ``UNSET``, and only consumer-supplied fields are gated
        (active-input-only contract, M2 of rev5).
        """
        if input_value is None or input_value is UNSET:
            return []
        if isinstance(input_value, dict):
            items = list(input_value.items())
        else:
            dataclass_fields = getattr(input_value, "__dataclass_fields__", None)
            if dataclass_fields is None:
                return []
            items = [(name, getattr(input_value, name)) for name in dataclass_fields]

        logic_lookup = dict(_LOGIC_KEYS)
        related_keys = set(getattr(cls, "related_filters", {}) or {})
        paths: list[str] = []
        for python_attr, raw_value in items:
            if raw_value is None or raw_value is UNSET:
                continue
            if python_attr in logic_lookup or python_attr in related_keys:
                continue
            spec = _field_specs.get((cls, python_attr))
            paths.append(
                spec.django_source_path if spec is not None else cls._form_key_for_python_attr(python_attr),
            )
        return paths

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
                method_name = f"check_{field_path.replace('__', '_')}_permission"
                method = getattr(self, method_name, None)
                if callable(method):
                    method(request)
            return
        # No explicit set supplied — fall through to the active-input
        # variant. `_run_permission_checks` is a classmethod; route the
        # currently-bound form data (already a dict) through it.
        type(self)._run_permission_checks(self.data or {}, request)

    @classmethod
    def _validate_form_or_raise(cls, filterset_instance: FilterSet) -> None:
        """Raise `GraphQLError` with the canonical extensions payload.

        Decision 8 step 6 plus M10 of rev5 — `BaseFilterSet.qs` silently
        falls through to `filter_queryset` when the form has errors, so
        the explicit `is_valid()` call here is what turns a malformed
        input into a structured GraphQL response.
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
    # Slice 4a — tree-form logic substrate (`filter_queryset` override).
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
        # starts at 0.
        depth = getattr(self, "_logic_depth", 0)
        q = type(self)._evaluate_logic_tree(qs, self.data or {}, request=self.request, _depth=depth)
        return qs.filter(q)

    @classmethod
    def _evaluate_logic_tree(
        cls,
        queryset: models.QuerySet,
        tree_data: Any,
        request: Any = None,
        *,
        _depth: int = 0,
    ) -> models.Q:
        """Build the ``Q`` expression for the ``and`` / ``or`` / ``not`` branches.

        Recursion terminates naturally when ``tree_data`` carries no
        logical keys -- an empty ``Q()`` is the identity element for
        ``qs.filter(...)`` and the no-op for an empty sub-branch list.
        ``_depth`` is the recursion-cap counter shared with
        ``_q_for_branch``; both helpers cap at ``cls._MAX_LOGIC_DEPTH``.
        """
        q = models.Q()
        if not isinstance(tree_data, dict) or not tree_data:
            return q
        if _depth > cls._MAX_LOGIC_DEPTH:
            raise ConfigurationError(
                f"FilterSet {cls.__qualname__}: logical-branch nesting exceeded "
                f"_MAX_LOGIC_DEPTH={cls._MAX_LOGIC_DEPTH}. Flatten the filter input "
                "or split into multiple queries.",
            )

        and_branches = tree_data.get("and") or []
        for child_input in and_branches:
            q &= cls._q_for_branch(queryset, child_input, request=request, _depth=_depth + 1)

        or_branches = tree_data.get("or") or []
        if or_branches:
            or_q = models.Q()
            for child_input in or_branches:
                or_q |= cls._q_for_branch(queryset, child_input, request=request, _depth=_depth + 1)
            q &= or_q

        not_branch = tree_data.get("not")
        if not_branch is not None:
            q &= ~cls._q_for_branch(queryset, not_branch, request=request, _depth=_depth + 1)

        return q

    @classmethod
    def _q_for_branch(
        cls,
        queryset: models.QuerySet,
        child_input: Any,
        request: Any = None,
        *,
        _depth: int = 0,
    ) -> models.Q:
        """Materialize one nested-branch input into a ``pk__in`` ``Q``.

        Normalizes the Strawberry input via the existing
        ``_normalize_input`` classmethod, then builds a sibling
        ``FilterSet`` instance against the parent ``queryset``. Reading
        ``.qs`` triggers ``BaseFilterSet``'s leaf-clause path against the
        child's normalized data AND re-enters this override for any
        deeper ``and`` / ``or`` / ``not`` keys the branch carries.

        ``_depth`` is stashed on the sibling instance via
        ``_logic_depth`` so ``filter_queryset`` can carry the counter
        across django-filter's ``.qs`` machinery into the next
        ``_evaluate_logic_tree`` call. Without this hand-off the depth
        counter would reset at every nesting level (the recursion path
        crosses through django-filter's ``BaseFilterSet`` which we do
        not own and cannot pass kwargs through).
        """
        child_data = cls._normalize_input(child_input)
        child_set = cls(data=child_data, queryset=queryset, request=request)
        child_set._logic_depth = _depth
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

        M4-of-rev3 + H3-of-rev8 — the explicit `RelatedFilter(queryset=...)`
        constraint AND-intersects with the visibility-scoped child qs
        from step 3, then `parent_qs.filter(<rel>__in=<intersected>)` runs
        ONCE for every active branch. Inactive branches do not constrain
        the parent.
        """
        constrained = parent_qs
        for field_name, related_filter, _ in cls._iter_active_related_branches(input_value):
            child_qs = child_qs_by_branch.get(field_name)
            explicit = related_filter.extra.get("queryset") if related_filter._has_explicit_queryset else None
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
                # rhs.model``) — proxies and multi-table-inheritance
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
            constrained = constrained.filter(**{f"{related_filter.field_name}__in": intersected})
        return constrained

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
        data = cls._normalize_input(input_value)
        child_qs_by_branch = cls._derive_related_visibility_querysets_sync(input_value, info)
        request = cls._request_from_info(info)
        constrained = cls._apply_related_constraints(input_value, queryset, child_qs_by_branch)
        filterset_instance = cls(data=data, queryset=constrained, request=request)
        cls._run_permission_checks(input_value, request)
        cls._validate_form_or_raise(filterset_instance)
        return filterset_instance.qs

    @classmethod
    async def apply_async(
        cls,
        input_value: Any,
        queryset: models.QuerySet,
        info: Any,
    ) -> models.QuerySet:
        """Async sibling of `apply_sync` awaiting the visibility step."""
        data = cls._normalize_input(input_value)
        child_qs_by_branch = await cls._derive_related_visibility_querysets_async(input_value, info)
        request = cls._request_from_info(info)
        constrained = cls._apply_related_constraints(input_value, queryset, child_qs_by_branch)
        filterset_instance = cls(data=data, queryset=constrained, request=request)
        cls._run_permission_checks(input_value, request)
        cls._validate_form_or_raise(filterset_instance)
        return filterset_instance.qs

    @classmethod
    def apply(
        cls,
        input_value: Any,
        queryset: models.QuerySet,
        info: Any,
    ) -> models.QuerySet:
        """Thin dispatcher — picks `apply_sync` and translates sync-misuse.

        Decision 8 / M5 of rev6 — catches the typed ``SyncMisuseError``
        raised by ``_apply_get_queryset_sync`` and rethrows as
        ``RuntimeError`` with the actionable "use apply_async instead"
        message consumers can match on. Class-based dispatch closes the
        round-3 loop: no substring-matching against a constant string.
        """
        try:
            return cls.apply_sync(input_value, queryset, info)
        except SyncMisuseError as exc:
            raise RuntimeError(
                f"FilterSet.apply called against async get_queryset; use apply_async instead. ({exc})",
            ) from exc
