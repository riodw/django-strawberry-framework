"""Filter primitives + `RelatedFilter`.

Layers 1 and 2 of the six-layer pipeline (spec-027 Decision 3) plus the
five parity-floor primitives (spec-027 Decision 4):

- `Filter` re-exported from `django_filters` for surface continuity.
- `TypedFilter` -> `ArrayFilter` / `RangeFilter` / `ListFilter`: ports of
  the matching `graphene_django/filter/filters/*.py` primitive minus the
  Graphene `_input_type` constructor argument (the Strawberry-side
  annotation is derived later by `convert_filter_to_input_annotation`).
- `GlobalIDFilter` / `GlobalIDMultipleChoiceFilter`: ports of the matching
  Graphene primitive with the decode step substituted to
  `strawberry.relay.GlobalID.from_id(value)` per Decision 4 M6.
- `LazyRelatedClassMixin`: re-exported from the package-root
  `sets_mixins` module (shared with the future order / aggregate sets);
  imported here so `RelatedFilter` and the `filters` public surface keep
  exposing it unchanged.
- `RelatedFilter`: collapsed port of the cookbook's
  `BaseRelatedFilter` + `RelatedFilter(BaseRelatedFilter, ModelChoiceFilter)`
  pair into a single consumer-facing class so the public surface matches
  the spec's single-symbol promise (spec-027 Decision 2).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.core.exceptions import ValidationError
from django.forms import Field, MultipleChoiceField
from django_filters import Filter, ModelChoiceFilter, MultipleChoiceFilter
from django_filters.constants import EMPTY_VALUES
from django_filters.filters import FilterMethod
from graphql import GraphQLError
from strawberry import relay

from ..sets_mixins import LazyRelatedClassMixin

# ``filters -> types`` is the documented safe (acyclic) import direction:
# ``types/relay.py`` module-top imports are stdlib/django/strawberry/``..exceptions``
# only — it reaches into ``filters`` / ``registry`` solely via in-function imports —
# so a module-top ``filters/base.py -> types/relay.py`` import does not close a load
# cycle (spec-031 Slice 2 plan). These are the single source of truth for the
# strategy->payload-shape mapping shared with the encoder and the Slice-3 decoder.
from ..types.relay import MODEL_LABEL_STRATEGIES, TYPE_NAME_STRATEGIES

if TYPE_CHECKING:  # pragma: no cover - type-checking-only import.
    from django.http import HttpRequest
    from django_filters.filterset import BaseFilterSet

    from ..types.definition import DjangoTypeDefinition


class TypedFilter(Filter):
    """Base marker for `ArrayFilter` / `RangeFilter` / `ListFilter`.

    Port of `graphene_django/filter/filters/typed_filter.py::TypedFilter`
    with the Graphene-only `_input_type` constructor argument dropped.
    The Strawberry-side annotation derives from the resolved filter
    instance at materialization time via `convert_filter_to_input_annotation`;
    there is no Graphene-style `input_type` property.
    """


class ArrayFilterMethod(FilterMethod):
    """Treat empty list as a real value; defer the rest to `FilterMethod`."""

    def __call__(self, qs: Any, value: Any) -> Any:
        """Apply the custom method, treating empty list as a real value."""
        if value is None:
            return qs
        return self.method(qs, self.f.field_name, value)


class ArrayFilter(TypedFilter):
    """Filter shaped for PostgreSQL `ArrayField` columns.

    Port of `graphene_django/filter/filters/array_filter.py::ArrayFilter`.
    The custom `method` setter swaps in `ArrayFilterMethod` so a
    consumer-supplied `method=` callable does not short-circuit on
    empty-list input — the empty list is a valid filter value here, unlike
    the default `FilterMethod` contract.

    Empty-list contract:
        `[]` is intentionally treated as a real value (not an
        `EMPTY_VALUES` short-circuit). The downstream meaning depends
        entirely on the bound `lookup_expr`:

        - `__contains=[]` matches every row on Postgres `ArrayField`
          (every list contains the empty list as a subset).
        - `__overlap=[]` matches no rows (empty overlap is vacuously
          false).
        - `__contained_by=[]` matches only rows whose array is empty.

        Consumers who want "any-of these values" semantics should bind
        `lookup_expr="overlap"` and pass `[value, ...]`; passing `[]`
        to `overlap` is a deliberate "match nothing" request. Consumers
        who want "no constraint" semantics should not send the filter
        at all (or send `None`, which short-circuits to the unfiltered
        queryset).
    """

    @TypedFilter.method.setter
    def method(self, value: Any) -> None:
        """Swap in `ArrayFilterMethod` when a consumer `method=` is set."""
        TypedFilter.method.fset(self, value)
        if value is not None:
            self.filter = ArrayFilterMethod(self)

    def filter(self, qs: Any, value: Any) -> Any:
        """Apply the lookup; `[]` is a real value (not `EMPTY_VALUES`-ish)."""
        if value in EMPTY_VALUES and value != []:
            return qs
        if self.distinct:
            qs = qs.distinct()
        lookup = f"{self.field_name}__{self.lookup_expr}"
        return self.get_method(qs)(**{lookup: value})


def validate_range(value: Any) -> None:
    """Reject range values whose length is not exactly two.

    Validator is only invoked by Django when the value is non-empty (the
    standard form-field contract); a one-element or three-element list
    raises `ValidationError(code="invalid")`.
    """
    if len(value) != 2:
        raise ValidationError(
            "Invalid range specified: it needs to contain 2 values.",
            code="invalid",
        )


class RangeField(Field):
    """`forms.Field` whose default validator is `validate_range`."""

    default_validators = [validate_range]
    empty_values = [None]


class RangeFilter(TypedFilter):
    """Filter that consumes a two-element list via `RangeField`."""

    field_class = RangeField


class ListFilterMethod(FilterMethod):
    """Treat empty list as a real value; defer the rest to `FilterMethod`."""

    def __call__(self, qs: Any, value: Any) -> Any:
        """Apply the custom method, treating empty list as a real value."""
        if value is None:
            return qs
        return self.method(qs, self.f.field_name, value)


class ListFilter(TypedFilter):
    """Filter that accepts a list-shaped input (e.g. `__in` lookups).

    Port of `graphene_django/filter/filters/list_filter.py::ListFilter`:
    an empty list short-circuits to `qs.none()` (or the original queryset
    when `exclude=True`) instead of being normalized into a "no value
    supplied" pass-through.
    """

    @TypedFilter.method.setter
    def method(self, value: Any) -> None:
        """Swap in `ListFilterMethod` when a consumer `method=` is set."""
        TypedFilter.method.fset(self, value)
        if value is not None:
            self.filter = ListFilterMethod(self)

    def filter(self, qs: Any, value: Any) -> Any:
        """Short-circuit empty-list inputs to `qs.none()` (or `qs` when excluding)."""
        if value is not None and len(value) == 0:
            return qs if self.exclude else qs.none()
        return super().filter(qs, value)


def _target_definition_for(filter_instance: Filter) -> DjangoTypeDefinition | None:
    """Resolve the owner/target ``DjangoTypeDefinition`` for a GlobalID-aware filter.

    Walks the runtime ``parent.<filterset>._owner_definition`` binding that
    the finalizer's phase 2.5 wires per spec-027 L566-567 + L603 +
    L1057. Two routing branches:

    1. **Own-PK branch.** When ``filter_instance.field_name`` matches the
       owning model's PK column name (``_meta.pk.name``), the relevant
       definition is the owning ``DjangoType`` (the OWNER itself is the
       Relay node — its PK gets a GlobalID).
    2. **Relation branch.** Otherwise the field name resolves through
       ``owner_definition.related_target_for(<base_field>)`` — where
       ``<base_field>`` is the parent-relation prefix in expanded child
       filter names like ``"genres__id"`` (the ``RelatedFilter`` expansion
       contract per spec-027 L988); the relevant definition is the target
       ``DjangoType``.

    Returns ``None`` when no owner is bound (Slice-1 + Slice-2 unit-test
    contexts) or when the lookup cannot resolve a target; the filter then
    decodes the GlobalID without type-name validation per spec-027 L1057.
    The resolution of WHICH definition (own-PK vs relation) stays single-sited
    here so the strategy-aware acceptance check in ``_decode_and_validate_global_id``
    consumes a single definition (spec-031 Decision 13).
    """
    parent = getattr(filter_instance, "parent", None)
    owner = getattr(parent, "_owner_definition", None) if parent is not None else None
    if owner is None:
        return None
    field_name = filter_instance.field_name or ""
    head, _sep, _tail = field_name.partition("__")
    pk_name = getattr(owner.model._meta.pk, "name", None)
    if head == pk_name or field_name == pk_name:
        return owner
    target = owner.related_target_for(head)
    if target is None:
        return None
    target_definition, _model_field = target
    return target_definition


def _accepted_globalid_type_names(definition: DjangoTypeDefinition | None) -> set[str] | None:
    """Return the accepted ``type_name`` payload(s) for a resolved definition's strategy.

    Strategy-aware target validation keyed on the resolved owner/target
    definition's recorded ``effective_globalid_strategy`` (spec-031 Decision 13) —
    the same field decode reads, so encode, decode, and filter validation all
    agree on one contract:

    - ``model`` → the model label only (``definition.model._meta.label_lower``).
    - ``type`` → the ``graphql_type_name`` only (pre-0.0.9 behavior).
    - ``type+model`` → either the model label or the ``graphql_type_name``.
    - ``callable`` / ``custom`` (the framework cannot compute the label), or an
      unbound owner / unresolvable target (``definition is None``), or an absent
      (``None``) ``effective_globalid_strategy`` (a non-finalized / non-Relay
      definition) → ``None`` (node-id-only fallback; the ``type_name`` guard is
      skipped). The filter is defense-in-depth, not the uniform-error contract
      decode owns, so it never raises for an unknown/absent strategy — it falls
      back to node-id-only, mirroring the existing unbound-owner fallback.
    """
    if definition is None:
        return None
    strategy = definition.effective_globalid_strategy
    accepted: set[str] = set()
    if strategy in MODEL_LABEL_STRATEGIES:
        accepted.add(definition.model._meta.label_lower)
    if strategy in TYPE_NAME_STRATEGIES:
        accepted.add(definition.graphql_type_name)
    return accepted or None


def _decode_and_validate_global_id(
    value: Any,
    filter_instance: Filter,
    *,
    index: int | None = None,
) -> str:
    """Decode `value` to a node id and validate its `type_name` per strategy.

    Accepts both raw `str` and `strawberry.relay.GlobalID` objects per
    spec-027 L602. The accepted `type_name` payload(s) are strategy-aware
    (spec-031 Decision 13): under the resolved owner/target definition's
    recorded `effective_globalid_strategy`, an emitted model-label ID
    round-trips while the old bare GraphQL type name is rejected (and vice
    versa for the `type` strategy). Raises `GraphQLError("GlobalID type
    mismatch: filter expects <expected> but received <actual>")` when the
    decoded `type_name` is not in the accepted set for the three framework
    strategies (spec-027 L603). `callable` / `custom` types, an unbound owner,
    or an unresolvable target fall back to node-id-only (the `type_name` guard
    is skipped). `GlobalIDMultipleChoiceFilter` passes `index` so the rejected
    list element is named in the error message per spec-027 L605.
    """
    decoded = value if isinstance(value, relay.GlobalID) else relay.GlobalID.from_id(value)
    definition = _target_definition_for(filter_instance)
    accepted = _accepted_globalid_type_names(definition)
    if accepted is not None and decoded.type_name not in accepted:
        suffix = "" if index is None else f" at index {index}"
        expected = " or ".join(sorted(accepted))
        raise GraphQLError(
            f"GlobalID type mismatch: filter expects {expected} but received {decoded.type_name}{suffix}",
        )
    return decoded.node_id


class GlobalIDFilter(Filter):
    """Filter that decodes a Relay GlobalID before delegating to `Filter`.

    Port of `graphene_django/filter/filters/global_id_filter.py::GlobalIDFilter`
    with the decode substituted to `strawberry.relay.GlobalID.from_id(value)`
    per spec-027 Decision 4 M6. The Graphene-only
    `GlobalIDFormField` / `GlobalIDMultipleChoiceField` dependencies drop
    away; the default `forms.CharField` (inherited via `Filter.field_class`)
    is used.

    Accepts both raw `str` and `strawberry.relay.GlobalID` objects per
    spec-027 L602. Validates the decoded `type_name` against the expected
    target GraphQL type (resolved through the parent filterset's
    `_owner_definition.related_target_for(field_name)`, or the owner
    itself when the filter targets the own PK) per spec-027 L603; a
    mismatch raises `GraphQLError("GlobalID type mismatch...")` before
    any queryset clause runs.
    """

    def filter(self, qs: Any, value: Any) -> Any:
        """Decode + validate the GlobalID; delegate to `Filter.filter` with `node_id`."""
        if value is None:
            return super().filter(qs, None)
        node_id = _decode_and_validate_global_id(value, self)
        return super().filter(qs, node_id)


class _GlobalIDMultipleChoiceField(MultipleChoiceField):
    """`MultipleChoiceField` that skips fixed-`choices` validation.

    `MultipleChoiceField.valid_value` rejects any submitted value that
    is not in `self.choices` -- and a `GlobalIDMultipleChoiceFilter`
    has no static choice set (its `choices` default to `[]`), so the
    stock field rejected EVERY GlobalID at form-clean time before the
    filter's own decode/validate could run. GlobalID list elements are
    decoded and type-checked in `GlobalIDMultipleChoiceFilter.filter`
    (per spec-027 L605), not against a fixed set, so this field accepts
    any submitted value and defers validation to the filter. Mirrors
    graphene-django's `GlobalIDMultipleChoiceField`.
    """

    def valid_value(self, value: Any) -> bool:  # noqa: ARG002 - signature fixed by Django.
        """Accept any value; GlobalID validation happens in the filter."""
        return True


class GlobalIDMultipleChoiceFilter(MultipleChoiceFilter):
    """Multi-value sibling of `GlobalIDFilter`.

    Validates every list element independently per spec-027 L605; a
    single wrong-type element rejects the whole input with the offending
    index named in the error message.

    Uses `_GlobalIDMultipleChoiceField` so the form-clean step does not
    reject submitted GlobalIDs against an empty `choices` set (the stock
    `MultipleChoiceField` would); decode + type validation run in
    `filter` instead.
    """

    field_class = _GlobalIDMultipleChoiceField

    def filter(self, qs: Any, value: Any) -> Any:
        """Decode + validate every GlobalID; delegate to the parent filter."""
        if value is None:
            return super().filter(qs, None)
        node_ids = [
            _decode_and_validate_global_id(item, self, index=idx) for idx, item in enumerate(value)
        ]
        return super().filter(qs, node_ids)


class RelatedFilter(LazyRelatedClassMixin, ModelChoiceFilter):
    """`ModelChoiceFilter` that traverses into another `FilterSet`.

    Collapsed port of `django_graphene_filters/filters.py::BaseRelatedFilter`
    + `django_graphene_filters/filters.py::RelatedFilter` into a single
    consumer-facing class per spec-027 Decision 2 (single-symbol public
    surface). The lazy-resolution logic (`bind_filterset`, `.filterset`
    property, target-model-derived queryset) carries over from the
    cookbook unchanged.

    Target acceptance shapes:

    - A `FilterSet` class.
    - An absolute import path (e.g. ``"apps.library.filters.ShelfFilter"``).
    - An unqualified class name resolved against the owning filterset's
      module (e.g. ``"ShelfFilter"`` when both filtersets live in the
      same file).
    """

    def __init__(
        self,
        filterset: str | type[BaseFilterSet],
        *args,
        **kwargs,
    ) -> None:
        """Bind the target `filterset` and record explicit-queryset intent.

        Rejects `lookups=` with `TypeError` before delegating to
        `ModelChoiceFilter.__init__`. The kwarg was a verbatim port of
        an upstream cookbook artifact with no readers in this package
        and was removed in 0.0.7; the explicit guard runs ahead of
        `super().__init__` because `django_filters.Filter.__init__`
        silently absorbs unknown kwargs into `self.extra`, which would
        otherwise mask the dead-state shape under a different name.
        """
        if "lookups" in kwargs:
            raise TypeError(
                "`RelatedFilter` does not accept `lookups=`; the kwarg was "
                "removed in 0.0.7 because it had no readers.",
            )
        self._has_explicit_queryset = kwargs.get("queryset") is not None
        super().__init__(*args, **kwargs)
        self._filterset = filterset

    def bind_filterset(self, filterset: type[BaseFilterSet]) -> None:
        """Bind the owning `FilterSet` once; subsequent calls are no-ops.

        Idempotent so the metaclass `__new__` can re-bind every related
        filter on subclass creation without clobbering a deliberate
        override.

        Silent-no-op contract:
            A second call with a DIFFERENT ``filterset`` (the rare case
            of a module-level ``RelatedFilter`` instance shared across
            two ``FilterSet`` subclasses) is also silenced here. The
            strict cross-owner mismatch detection runs later at
            finalize time in
            ``types/finalizer.py::_bind_filterset_owner`` (subpass 1 of
            finalizer phase 2.5's ``_bind_filtersets`` umbrella; H2-rev8
            check), so a real divergent-owner reuse still surfaces a
            ``ConfigurationError`` with both owners named — just not at
            class-creation time.

        Unqualified-string caveat:
            ``bound_filterset`` is the resolution scope for an UNQUALIFIED
            string target (``RelatedFilter("ShelfFilter")``) — the
            ``.filterset`` property resolves the name against
            ``bound_filterset.__module__``. Because re-bind is a no-op, a
            single ``RelatedFilter`` INSTANCE shared across two subclasses
            (defined on a base ``FilterSet`` and inherited) keeps the FIRST
            subclass's module as that scope, so a second subclass in a
            different module that meant a same-named-but-different
            ``ShelfFilter`` would resolve to the first's. Use a class object
            or an absolute import path for a shared/inherited
            ``RelatedFilter``, or declare it per subclass.
        """
        if not hasattr(self, "bound_filterset"):
            self.bound_filterset = filterset

    @property
    def filterset(self) -> type[BaseFilterSet]:
        """Resolve `self._filterset` lazily on first access.

        Re-stores the resolved class so the next access is a plain
        attribute read; setter remains usable when a caller wants to
        substitute the target.
        """
        self._filterset = self.resolve_lazy_class(
            self._filterset,
            getattr(self, "bound_filterset", None),
        )
        return self._filterset

    @filterset.setter
    def filterset(self, value: type[BaseFilterSet]) -> None:
        self._filterset = value

    def get_queryset(self, request: HttpRequest) -> Any:
        """Derive the queryset from the target filterset's `Meta.model`.

        When no explicit `queryset=` was supplied at construction time,
        falls back to `target_filterset._meta.model._default_manager.all()`
        — the cookbook's documented auto-derivation contract. An explicit
        queryset is preserved verbatim.
        """
        queryset = super().get_queryset(request)
        if queryset is None:
            target = self.filterset
            model = getattr(getattr(target, "_meta", None), "model", None)
            if model is not None:
                return model._default_manager.all()
        return queryset
