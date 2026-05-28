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
from typing import TYPE_CHECKING, Any

from django.db import models
from django.http import HttpRequest
from django_filters import filterset
from graphql import GraphQLError
from strawberry import UNSET

from ..exceptions import ConfigurationError
from ..registry import registry
from ..types.relay import (
    _SYNC_MISUSE_SENTINEL,
    _apply_get_queryset_async,
    _apply_get_queryset_sync,
    implements_relay_node,
)
from .base import GlobalIDFilter, GlobalIDMultipleChoiceFilter, RelatedFilter
from .inputs import _LOGIC_KEYS, LOOKUP_NAME_MAP, _field_specs, normalize_input_value

if TYPE_CHECKING:  # pragma: no cover - type-checking-only import.
    from ..types.definition import DjangoTypeDefinition


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

    @classmethod
    def expand_related_filter(
        cls,
        new_class: FilterSetMetaclass,
        filter_name: str,
        f: RelatedFilter,
    ) -> dict[str, Any]:
        """Expand `f` against its target filterset's resolved filters.

        Verbatim port of the cookbook's `expand_related_filter`. The
        per-field deep-copy avoids mutating the target filterset's
        instances when the parent rebinds `field_name` to the relation
        path.
        """
        expanded = OrderedDict()
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


class FilterSet(filterset.BaseFilterSet, metaclass=FilterSetMetaclass):
    """Consumer-facing `FilterSet` foundation.

    Subclasses `django_filters.filterset.BaseFilterSet` directly per
    spec-021 Decision 5; the cookbook's lazy-resolution Layers 3 and 4
    are folded in via `FilterSetMetaclass` and `get_filters`. The
    Decision-8 / M1-of-rev5 named helpers decompose `apply_sync` and
    `apply_async` so each step can be exercised in isolation; `apply`
    stays as a thin dispatcher that translates the sync-misuse
    `ConfigurationError` from `_apply_get_queryset_sync` into a
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
                    expanded = cls.__class__.expand_related_filter(cls, filter_name, f)
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
        """Include the PK and exclude M2M when `Meta.fields == "__all__"`.

        M3-of-rev4 narrowing: `django-filter`'s default treats the PK as
        a non-filterable column and includes M2M in the `"__all__"`
        sweep; the package's preferred shape is the opposite (PK is a
        canonical filter; M2M cannot be filtered without an explicit
        `RelatedFilter`). Only runs when `Meta.fields == "__all__"`; the
        explicit-dict case follows the upstream behavior unchanged.

        The upstream method is named ``get_fields`` (no underscore
        prefix); we override the same name so `super().get_filters()`'s
        internal call routes through our narrowing.
        """
        fields = super().get_fields()
        meta_fields = getattr(cls._meta, "fields", None)
        if meta_fields != "__all__":
            return fields

        model = cls._meta.model
        if model is None:
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
            return GlobalIDFilter(
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
        owner_type = getattr(owner, "origin", None) or getattr(owner, "type", None)
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
            # TODO(spec-021-filters-0_0_8 Slice 3): consult
            # `owner.related_target_for(field_name)` once the method
            # lands; for now the fallback below is the only reachable
            # branch.
            resolved = getattr(owner, "related_target_for", None)
            if callable(resolved):
                pair = resolved(field_name)
                if pair is not None:
                    target_definition, _ = pair
                    return getattr(target_definition, "type", None) or getattr(
                        target_definition,
                        "type_cls",
                        None,
                    )
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
        if input_value is None:
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
                    if lookup_value is None:
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
        raises ``ConfigurationError`` with ``_SYNC_MISUSE_SENTINEL`` in its
        message; ``apply``'s catch-and-rethrow translates that into a
        ``RuntimeError`` consumers can match on.

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
        """Resolve the `DjangoType` registered against the branch's model."""
        child_filterset = related_filter.filterset
        child_model = getattr(getattr(child_filterset, "_meta", None), "model", None)
        if child_model is None:
            return None
        return registry.primary_for(child_model) or registry.get(child_model)

    @classmethod
    def _run_permission_checks(cls, input_value: Any, request: Any) -> None:
        """Fire `check_<field>_permission(request)` for fields in the input.

        Active-input-only per M2 of rev5 — a declared `check_*` gate that
        is not exercised by this call leaves the queryset untouched.
        Recurses into the child filterset for each active `RelatedFilter`
        branch so the cookbook's nested-permission contract holds.

        Permission methods are called via a bare instance allocated with
        ``object.__new__(cls)``; this matches the cookbook contract
        (per-field gates are written as regular ``def
        check_X_permission(self, request)`` methods on the filterset)
        without requiring a fully-constructed `FilterSet` instance.
        """
        if input_value is None:
            return

        bare = object.__new__(cls)
        normalized = cls._normalize_input(input_value)
        for form_key in normalized:
            if form_key in {"and", "or", "not"}:
                continue
            cls._invoke_permission_method(bare, form_key, request)

        for field_name, related_filter, child_input in cls._iter_active_related_branches(input_value):
            child_filterset = related_filter.filterset
            if child_filterset is not None and hasattr(child_filterset, "_run_permission_checks"):
                child_filterset._run_permission_checks(child_input, request)
            # Per-branch permission gate on the parent — fires e.g.
            # `check_shelves_permission` when the `shelves` branch is
            # active. Child filterset's own field gates fire via the
            # recursive call above.
            cls._invoke_permission_method(bare, field_name, request)

    @staticmethod
    def _invoke_permission_method(bare_instance: Any, field_path: str, request: Any) -> None:
        """Call `check_<field_path>_permission(request)` if defined on `bare_instance`."""
        method_name = f"check_{field_path.replace('__', '_')}_permission"
        method = getattr(bare_instance, method_name, None)
        if callable(method):
            method(request)

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
        q = type(self)._evaluate_logic_tree(qs, self.data or {})
        return qs.filter(q)

    @classmethod
    def _evaluate_logic_tree(cls, queryset: models.QuerySet, tree_data: Any) -> models.Q:
        """Build the ``Q`` expression for the ``and`` / ``or`` / ``not`` branches.

        Recursion terminates naturally when ``tree_data`` carries no
        logical keys -- an empty ``Q()`` is the identity element for
        ``qs.filter(...)`` and the no-op for an empty sub-branch list.
        """
        q = models.Q()
        if not isinstance(tree_data, dict) or not tree_data:
            return q

        and_branches = tree_data.get("and") or []
        for child_input in and_branches:
            q &= cls._q_for_branch(queryset, child_input)

        or_branches = tree_data.get("or") or []
        if or_branches:
            or_q = models.Q()
            for child_input in or_branches:
                or_q |= cls._q_for_branch(queryset, child_input)
            q &= or_q

        not_branch = tree_data.get("not")
        if not_branch is not None:
            q &= ~cls._q_for_branch(queryset, not_branch)

        return q

    @classmethod
    def _q_for_branch(cls, queryset: models.QuerySet, child_input: Any) -> models.Q:
        """Materialize one nested-branch input into a ``pk__in`` ``Q``.

        Normalizes the Strawberry input via the existing
        ``_normalize_input`` classmethod, then builds a sibling
        ``FilterSet`` instance against the parent ``queryset``. Reading
        ``.qs`` triggers ``BaseFilterSet``'s leaf-clause path against the
        child's normalized data AND re-enters this override for any
        deeper ``and`` / ``or`` / ``not`` keys the branch carries.
        """
        child_data = cls._normalize_input(child_input)
        child_set = cls(data=child_data, queryset=queryset, request=None)
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
                intersected = explicit & child_qs
            else:
                intersected = child_qs if child_qs is not None else explicit
            constrained = constrained.filter(**{f"{field_name}__in": intersected})
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

        Decision 8 / M5 of rev6 — catches both `RuntimeError` (in case a
        future raise site uses the canonical class) and
        `ConfigurationError` (the existing class
        `_apply_get_queryset_sync` raises today). When the exception's
        message carries `_SYNC_MISUSE_SENTINEL`, the dispatcher rethrows
        as `RuntimeError` with the clearer-message shape consumers can
        match on. Any other exception propagates unchanged.
        """
        try:
            return cls.apply_sync(input_value, queryset, info)
        except (RuntimeError, ConfigurationError) as exc:
            if _SYNC_MISUSE_SENTINEL in str(exc):
                raise RuntimeError(
                    f"FilterSet.apply called against async get_queryset; use apply_async instead. ({exc})",
                ) from exc
            raise
