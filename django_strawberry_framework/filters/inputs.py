"""Filter input namespace, lookup-name scaffolding, and shape converters.

Generated input classes MUST become real globals of this module because
``strawberry.lazy("django_strawberry_framework.filters.inputs")`` resolves
through ``module.__dict__`` (spec-027 Decision 9). The module pairs the
constants (``LOOKUP_PREFIXES`` / ``LOOKUP_NAME_MAP`` / ``FieldSpec`` /
``_field_specs`` / ``_materialized_names``) with the
filter-instance -> Strawberry-annotation converter pair
(``convert_filter_to_input_annotation`` /
``normalize_input_value``), the dataclass builder
(``build_input_class``), the per-filterset operator-bag helpers
(``filter_lookup_table`` / ``_build_input_fields`` / ``_build_logic_fields``
/ ``construct_search``), and the module-global materialization /
namespace-clear pair (``materialize_input_class`` /
``clear_filter_input_namespace``).
"""

from __future__ import annotations

import datetime
import decimal
import enum
import uuid
from collections import OrderedDict
from collections.abc import Callable, Iterator, Mapping
from dataclasses import dataclass
from types import GenericAlias, MappingProxyType
from typing import TYPE_CHECKING, Annotated, cast
from weakref import WeakKeyDictionary

import strawberry
from django.db import models
from django_filters import (
    ChoiceFilter,
    Filter,
    ModelChoiceFilter,
    ModelMultipleChoiceFilter,
    TypedChoiceFilter,
)
from django_filters import RangeFilter as _DjangoRangeFilter
from django_filters.filters import BaseCSVFilter
from django_filters.utils import get_model_field
from strawberry import UNSET, relay

from ..conf import hide_flat_filters_setting
from ..exceptions import ConfigurationError, _safe_arg_repr, _safe_type_name
from ..registry import register_subsystem_clear
from ..utils.converters import MRO_CONTINUE, convert_with_mro
from ..utils.input_values import is_inactive_value
from ..utils.inputs import (
    GeneratedInputFieldSpec,
    build_strawberry_input_class,
    emit_set_input_field_triples,
    iter_set_subclasses,
    make_set_input_namespace,
    optional_field_kwargs,
    set_input_type_name,
)
from ..utils.strings import flatten_lookup_path, graphql_camel_name, pascal_case_or_raise
from .base import (
    BLANK_CHOICE,
    ArrayFilter,
    EnumChoiceFilter,
    GlobalIDFilter,
    GlobalIDMultipleChoiceFilter,
    ListFilter,
    RangeFilter,
    RelatedFilter,
    RelationPkFilter,
    RelationPkMultipleFilter,
    TypedFilter,
    _bound_field_name,
    model_choice_identity_column,
    relation_identity_column,
)

# Domain-local aliases for the shared generated-input substrate (the mechanics
# are single-sited in ``utils/inputs.py``). Tests and
# ``factories.py`` import these spec-027 Decision 9 names from this module, so
# they stay addressable here.
FieldSpec = GeneratedInputFieldSpec
build_input_class = build_strawberry_input_class
_camel_case = graphql_camel_name
_iter_filterset_subclasses = iter_set_subclasses
_input_type_name_for = set_input_type_name

if TYPE_CHECKING:
    from typing import Protocol

    from django_filters.filterset import FilterSetOptions

    from ..types.definition import DjangoTypeDefinition
    from ..utils.typing import ConcreteField, ModelField
    from .sets import FilterSet

    class _TypeForm(Protocol):
        """A runtime annotation value (a class, ``NewType``, or scalar) that ``| None`` widens."""

        def __or__(self, other: None, /) -> object: ...


# Module path the ``strawberry.lazy(...)`` marker references; pinned as a
# single constant so the factory, ``_build_logic_fields``, and
# ``filter_input_type`` (in ``__init__.py``) all stay in sync.
INPUTS_MODULE_PATH: str = "django_strawberry_framework.filters.inputs"


# Search-prefix vocabulary for the future `Meta.search_fields` card per
# spec-027 Decision 2; consumed by `construct_search` below.
LOOKUP_PREFIXES: dict[str, str] = {
    "^": "istartswith",
    "=": "iexact",
    "@": "search",
    "$": "iregex",
}


# `django-filter` lookup -> (python_attr, graphql_name) pair per spec-027
# Decision 3 Layer 5. Strawberry's auto-camel-case
# cannot transform `icontains` to `iContains` (no underscore to split on),
# and the Python keyword `in` cannot be a dataclass field - both are pinned
# here. Consumed by `filter_lookup_table` (keying each head's lookups by their
# Python attr, the names `FilterSet._normalize_input` reads), by
# `_build_input_fields` (for `strawberry.field(name=...)` emission), and by
# `FilterSet._operator_bag_items` (recognizing a hand-built operator bag).
LOOKUP_NAME_MAP: dict[str, tuple[str, str]] = {
    "exact": ("exact", "exact"),
    "iexact": ("i_exact", "iExact"),
    "contains": ("contains", "contains"),
    "icontains": ("i_contains", "iContains"),
    "startswith": ("starts_with", "startsWith"),
    "istartswith": ("i_starts_with", "iStartsWith"),
    "endswith": ("ends_with", "endsWith"),
    "iendswith": ("i_ends_with", "iEndsWith"),
    "regex": ("regex", "regex"),
    "iregex": ("i_regex", "iRegex"),
    "gt": ("gt", "gt"),
    "gte": ("gte", "gte"),
    "lt": ("lt", "lt"),
    "lte": ("lte", "lte"),
    "isnull": ("is_null", "isNull"),
    "in": ("in_", "in"),
    "range": ("range", "range"),
    "date": ("date", "date"),
    "year": ("year", "year"),
    "month": ("month", "month"),
    "day": ("day", "day"),
    "week_day": ("week_day", "weekDay"),
    "quarter": ("quarter", "quarter"),
    "hour": ("hour", "hour"),
    "minute": ("minute", "minute"),
    "second": ("second", "second"),
}


def _compose_and(branch_qs: list[models.Q]) -> models.Q:
    """Compose branch Q objects with logical AND."""
    q = models.Q()
    for branch_q in branch_qs:
        q &= branch_q
    return q


def _compose_or(branch_qs: list[models.Q]) -> models.Q:
    """Compose branch Q objects with logical OR."""
    if not branch_qs:
        return models.Q()
    q = models.Q()
    for branch_q in branch_qs:
        q |= branch_q
    return q


def _compose_not(branch_qs: list[models.Q]) -> models.Q:
    """Compose branch Q objects with logical NOT."""
    if not branch_qs:
        return models.Q()
    return ~branch_qs[0]


@dataclass(frozen=True, slots=True)
class LogicOperatorDescriptor:
    """Authoritative descriptor for a filter logical operator.

    Encapsulates the Python attribute name, wire name, cardinality (sequence vs
    single-element), and Django Q composition semantics in a single immutable record.
    """

    python_attr: str
    wire_name: str
    is_sequence: bool
    compose: Callable[[list[models.Q]], models.Q]


LOGIC_OP_AND = LogicOperatorDescriptor(
    python_attr="and_",
    wire_name="and",
    is_sequence=True,
    compose=_compose_and,
)

LOGIC_OP_OR = LogicOperatorDescriptor(
    python_attr="or_",
    wire_name="or",
    is_sequence=True,
    compose=_compose_or,
)

LOGIC_OP_NOT = LogicOperatorDescriptor(
    python_attr="not_",
    wire_name="not",
    is_sequence=False,
    compose=_compose_not,
)

LOGIC_OPERATORS: tuple[LogicOperatorDescriptor, ...] = (LOGIC_OP_AND, LOGIC_OP_OR, LOGIC_OP_NOT)

LOGIC_OPERATORS_BY_WIRE: Mapping[str, LogicOperatorDescriptor] = MappingProxyType(
    {op.wire_name: op for op in LOGIC_OPERATORS},
)

LOGIC_OPERATORS_BY_PYTHON_ATTR: Mapping[str, LogicOperatorDescriptor] = MappingProxyType(
    {op.python_attr: op for op in LOGIC_OPERATORS},
)


# Provenance table populated by ``_build_input_fields`` and consulted at
# runtime by ``FilterSet._normalize_input`` and ``normalize_input_value``.
# Cleanup contract: keyed by ``(FilterSet subclass, python_attr)`` and
# emptied ONLY by ``clear_filter_input_namespace`` (driven by
# ``registry.clear()``). A consumer test suite that reloads model / filter
# modules WITHOUT routing through ``registry.clear()`` retains stale entries
# from the prior build; the filter test files' ``_isolate_registry`` autouse
# fixture clears this map explicitly for exactly that reason.
#
# spec-027 Decision 9 namespace lifecycle. Mechanics live in
# ``utils/inputs.py::make_set_input_namespace`` (heavy clear: ledger +
# field_specs + factory caches + ``_lifecycle`` binding). This module keeps
# the spec-named public wrappers and the disjoint per-subsystem ledgers.
# ``clear_filter_input_namespace`` leaves class objects parked in
# ``filters.inputs.__dict__``, per the parked-globals lifecycle stated on
# ``utils/inputs.py::make_input_namespace``.
_materialized_names: dict[str, type[object]]
_field_specs: dict[tuple[type[FilterSet], str], FieldSpec]
(
    _materialized_names,
    _field_specs,
    _materialize_input,
    _clear_input_namespace,
) = make_set_input_namespace(
    INPUTS_MODULE_PATH,
    "FilterSet",
    factory_module="django_strawberry_framework.filters.factories",
    factory_class_name="FilterArgumentsFactory",
    collision_registry_attr="_type_filterset_registry",
    set_module="django_strawberry_framework.filters.sets",
    set_class_name="FilterSet",
)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


# Pascal-case helper for input-class names. The conversion AND the
# no-word-character emptiness check both live in the shared
# ``utils.strings.pascal_case_or_raise`` (single-sited, shared with
# ``sets_mixins.py::ClassBasedTypeNameMixin.type_name_for``); this wrapper
# only supplies the ``RangeFilter``-specific error.
def _pascal_case(name: str) -> str:
    """Return ``name`` converted to ``PascalCase``, raising on a token-less input.

    Delegates to ``utils.strings.pascal_case_or_raise``; an input with no
    word-character tokens (e.g. ``"_"``, ``""``, ``"__"``) would silently
    collide on the downstream ``RangeInputType`` naming, so it raises
    ``ConfigurationError`` instead. Direct caller today:
    ``_build_range_input_class`` only. Indirect callers
    (``_input_type_name_for``, ``_build_input_fields``'s operator-bag class
    naming) route through
    ``sets_mixins.py::ClassBasedTypeNameMixin.type_name_for`` and trip the
    same shared guard with its own error - so the error message below names
    the ``RangeFilter`` consumer specifically.
    """
    return pascal_case_or_raise(
        name,
        make_error=lambda bad: ConfigurationError(
            f"_pascal_case received {_safe_arg_repr(bad)} which contains no word "
            "characters; rename the RangeFilter's `field_name=` so its "
            "name has at least one alphanumeric token.",
        ),
    )


def _scalar_from_form_field(form_field: object) -> _TypeForm:
    """Pick a Strawberry-compatible scalar for a Django form field.

    Used by ``convert_filter_to_input_annotation`` for the
    ``CharFilter`` / ``NumberFilter`` / ``BooleanFilter`` catch-all
    branch. Form-field class -> Python scalar mapping derived by direct
    inspection of ``django.forms``; ``CharField`` is the catch-all (it's
    what every text-shaped filter falls through to).
    """
    from django import forms

    if isinstance(form_field, forms.NullBooleanField):
        return bool
    if isinstance(form_field, forms.BooleanField):
        return bool
    # ``DecimalField`` and ``FloatField`` BOTH subclass ``IntegerField`` in
    # ``django.forms`` (the form-field hierarchy differs from the model-field
    # one, where they descend straight from ``Field``). They MUST be matched
    # before the ``IntegerField`` catch below; otherwise a decimal- or
    # float-backed filter mis-maps to ``int``. ``DecimalField`` and
    # ``FloatField`` are siblings (neither subclasses the other), so the
    # order between them is immaterial.
    if isinstance(form_field, forms.DecimalField):
        return decimal.Decimal
    if isinstance(form_field, forms.FloatField):
        return float
    if isinstance(form_field, forms.IntegerField):
        return int
    if isinstance(form_field, forms.DateTimeField):
        return datetime.datetime
    if isinstance(form_field, forms.DateField):
        return datetime.date
    if isinstance(form_field, forms.TimeField):
        return datetime.time
    if isinstance(form_field, forms.UUIDField):
        return uuid.UUID
    # Both ``CharField`` and the catch-all map to ``str``. The explicit
    # ``CharField`` branch is kept for documentation: the conversion
    # table in spec-027 Decision 4 lists ``CharFilter`` as a recognized
    # shape, and a future reader who inspects this function should see
    # that the mapping is intentional, not an accidental fallthrough.
    if isinstance(form_field, forms.CharField):
        return str
    return str


def _scalar_from_model_field(model_field: ModelField | None) -> _TypeForm:
    """Map a Django model field to its scalar via the shared ``SCALAR_MAP`` lookup.

    Delegates to ``types.converters.scalar_for_field`` -- a LOCAL import, to
    avoid the top-level cycle through ``converters`` (same pattern as
    ``_choice_enum_from_filter``) -- so a filter input and the selected
    ``DjangoType`` field resolve a column to the SAME GraphQL scalar, including
    consumer-registered ``SCALAR_MAP`` entries and the ``BigInt`` scalar for
    64-bit columns. An unsupported field raises the same ``ConfigurationError``
    as field selection rather than silently degrading to ``str``. ``None`` (a
    method filter with no backing model field) keeps the ``str`` fallback.
    """
    if model_field is None:
        return str
    from ..types.converters import scalar_for_field

    # A ``SCALAR_MAP`` value is a registered runtime annotation (a class or ``NewType``).
    # basedpyright: ``TypeForm`` also admits forms with no runtime ``__or__`` (a string forward
    # reference), which no ``SCALAR_MAP`` entry is
    return cast("_TypeForm", scalar_for_field(model_field))  # pyright: ignore[reportInvalidCast]


def _relation_identity_annotation(
    filter_instance: Filter,
    model_field: ModelField | None,
) -> _TypeForm:
    """Type a raw-pk relation leaf from the target's primary-key column.

    The scalar comes from ``filters/base.py::relation_identity_column`` through the
    shared ``SCALAR_MAP`` lookup, so the input agrees with how a ``DjangoType`` types
    that key (``Int``, ``UUID``, ``BigInt``, ...). A raw-pk filter whose ``field_name``
    resolves no relation on its ``FilterSet`` model has no column to type from.
    """
    column = relation_identity_column(model_field)
    if column is None:
        raise ConfigurationError(
            f"{_safe_type_name(filter_instance)} on {_safe_arg_repr(filter_instance)} names "
            f"{_safe_arg_repr(getattr(filter_instance, 'field_name', None))}, which is not a "
            "relation to a model on its FilterSet; name a relation key in Meta.fields, or "
            "filter the related row's own fields through a RelatedFilter.",
        )
    return _scalar_from_model_field(column)


def _model_choice_takes_list(filter_instance: Filter) -> bool:
    """Whether a consumer model-choice filter's form field cleans a list of values.

    ``ModelMultipleChoiceFilter`` does, and so does django-filter's CSV wrapper around
    a ``ModelChoiceFilter`` (``filter_for_lookup`` builds
    ``ConcreteInFilter(BaseInFilter, <filter_class>)`` for an ``in`` lookup), whose
    ``BaseCSVField`` cleans each member through the model-choice field.
    """
    return isinstance(filter_instance, (ModelMultipleChoiceFilter, BaseCSVFilter))


def _model_choice_identity_annotation(
    filter_instance: Filter,
    model_field: ModelField | None,
    filterset_cls: type[FilterSet] | None,
) -> _TypeForm:
    """Type one value of a consumer model-choice filter from the column its form cleans.

    The column is ``filters/base.py::model_choice_identity_column``'s (the ``queryset``
    model's primary key or ``to_field_name`` field, or the ``field_name`` relation's
    target for a callable ``queryset``) through the shared ``SCALAR_MAP`` lookup. The
    filter keeps its own form field, so its ``queryset`` still validates every value.
    """
    column = model_choice_identity_column(filter_instance, model_field)
    if column is None:
        owner = filterset_cls.__name__ if filterset_cls is not None else "FilterSet"
        raise ConfigurationError(
            f"{owner}: {_safe_type_name(filter_instance)} on "
            f"{_safe_arg_repr(getattr(filter_instance, 'field_name', None))} has no model "
            "queryset (its queryset is callable or unset) and its field_name names no "
            "relation on the FilterSet model, so there is no column to type its input "
            "from. Pass a model queryset, or point field_name at a relation.",
        )
    return _scalar_from_model_field(column)


def _choice_enum_from_filter(
    filter_instance: Filter,
    type_name: str,
    model_field: ModelField | None,
) -> type[enum.Enum]:
    """Derive a Strawberry enum from a ``ChoiceFilter``'s underlying choice source.

    Per spec-027 Decision 4, a ``ChoiceFilter`` whose source is not a
    Django ``Choices``-derived enum raises ``ConfigurationError``
    (the consumer is expected to wrap the choices through the existing
    converter pipeline). When the underlying model field is available
    the pipeline at ``types.converters.convert_choices_to_enum`` is
    consulted so the GraphQL enum is shared with any sibling
    ``DjangoType`` reading the same column.

    ``model_field`` is threaded as a parameter rather than stashed on
    the filter instance - keeps the filter stateless and avoids the
    "side-effect on a filter during input-class construction" trap.
    """
    # Local import to avoid a top-level cycle through ``types.converters``.
    from ..types.converters import convert_choices_to_enum

    if model_field is None or not getattr(model_field, "choices", None):
        raise ConfigurationError(
            f"ChoiceFilter on {_safe_arg_repr(filter_instance)} is not backed by a Django "
            "`Choices`-derived enum; wrap the choices through "
            "`django.db.models.TextChoices` / `IntegerChoices` or register a "
            "custom scalar via `SCALAR_MAP`.",
        )
    # Past the guard the field declares truthy ``choices``, which only a concrete
    # ``Field`` carries (a reverse ``ForeignObjectRel`` has no ``choices``).
    return convert_choices_to_enum(cast("ConcreteField", model_field), type_name)


def _element_annotation(
    filter_instance: Filter,
    model_field: ModelField | None,
    owner_definition: DjangoTypeDefinition | None,
) -> _TypeForm:
    """Single-element Strawberry type with the MODEL FIELD as source of truth.

    A backing model field's choices become the shared GraphQL enum and its
    column type becomes the scalar (including the ``BigInt`` scalar for 64-bit
    columns). The ``django-filter`` form field is consulted ONLY as the
    fallback for a custom ``method=`` filter with no backing model field --
    otherwise ``django-filter``'s ``NumberFilter`` form (a ``DecimalField``)
    mis-types integer columns and a CSV ``in`` over a choice column collapses
    to ``str``. Callers that need a different shape for a specific lookup (e.g.
    ``isnull`` is always boolean) handle that before calling this.

    Known contract limit: a custom ``method=`` filter has no backing
    ``model_field``, so its element type is inferred from the
    ``django-filter`` form field and a CSV/list ``method=`` filter therefore
    yields ``list[str]`` even when the column it ultimately queries is an
    ``int``. To get a typed element on a method filter, back it with a model
    field (``field_name=``) or declare the input annotation explicitly.
    """
    if model_field is not None and getattr(model_field, "choices", None):
        type_name = _owner_type_name(owner_definition) or "Filter"
        return _choice_enum_from_filter(filter_instance, type_name, model_field)
    if model_field is not None:
        return _scalar_from_model_field(model_field)
    form_field = getattr(filter_instance, "field", None)
    return (
        _scalar_from_form_field(form_field)
        if form_field is not None
        else _scalar_from_model_field(model_field)
    )


# ---------------------------------------------------------------------------
# Public converter pair
# ---------------------------------------------------------------------------


# Most-specific-first filter-class order. Convert and normalize both walk this
# via ``convert_with_mro`` so a new primitive cannot be typed on one ladder and
# coerced on the other (spec-053 C3). The consumer model-choice pair sits after
# the package relation primitives and before ``BaseCSVFilter`` (its ``in``
# wrapper is both) and ``ChoiceFilter`` (which ``ModelChoiceFilter``
# subclasses). ``TypedFilter`` is convert-only: List /
# Array / Range already matched, so normalize returns ``MRO_CONTINUE`` and
# falls through to ChoiceFilter / the catch-all. Last entry is ``object`` (the
# original ``else``): convert's method-filter / ``isnull`` / scalar arm,
# normalize's unwrap. A duck-typed non-``Filter`` still reaches that arm so
# hostile-``__repr__`` diagnostics stay typed ``ConfigurationError``.
_FILTER_INPUT_KIND_TYPES: tuple[type[object] | tuple[type[object], ...], ...] = (
    GlobalIDMultipleChoiceFilter,
    GlobalIDFilter,
    RelationPkMultipleFilter,
    RelationPkFilter,
    (ModelMultipleChoiceFilter, ModelChoiceFilter),
    BaseCSVFilter,
    (RangeFilter, _DjangoRangeFilter),
    (ListFilter, ArrayFilter),
    TypedFilter,
    (ChoiceFilter, TypedChoiceFilter),
    object,
)


def _filter_input_prechecks(
    *handlers: Callable[[Filter], object],
) -> list[tuple[type[object] | tuple[type[object], ...], Callable[[Filter], object]]]:
    """Zip the shared kind order with per-pass handlers.

    ``zip(..., strict=True)`` fails loud if convert or normalize forgets a
    handler when the kind table grows.
    """
    return list(zip(_FILTER_INPUT_KIND_TYPES, handlers, strict=True))


def _unexpected_filter_dispatch(obj: object) -> ConfigurationError:
    """Fallthrough factory for the filter-input ``convert_with_mro`` riders.

    Last precheck is ``object`` (the original ``else``), so a real dispatch
    never reaches here. The factory keeps ``convert_with_mro``'s raising
    contract if a handler returns ``MRO_CONTINUE`` all the way through.
    """
    return ConfigurationError(
        f"internal: filter input dispatch reached fallthrough for {_safe_arg_repr(obj)}",
    )


def convert_filter_to_input_annotation(
    filter_instance: Filter,
    model_field: ModelField | None,
    owner_definition: DjangoTypeDefinition | None = None,
    filterset_cls: type[FilterSet] | None = None,
) -> object:
    """Return the Strawberry annotation for a resolved ``django-filter`` filter.

    Implements the spec-027 Decision 4 conversion table. Kind order is
    ``_FILTER_INPUT_KIND_TYPES`` (most-specific first): Relay-aware primitives,
    then the raw-pk relation pair (typed from the target key column), then a
    consumer ``ModelChoiceFilter`` / ``ModelMultipleChoiceFilter`` (typed from the
    column its form field cleans), then CSV, then
    Range / List / Array, then bare ``TypedFilter``, then
    ``ChoiceFilter``, then the ``object`` catch-all (the original ``else``).
    ``method=...`` filters
    that expose no form field raise ``ConfigurationError``.

    Dispatch rides ``utils/converters.py::convert_with_mro`` with the same
    kind table ``normalize_input_value`` uses.

    ``filterset_cls`` (the owning ``FilterSet`` for a leaf built through
    ``_build_input_fields``) qualifies the nested ``RangeFilter`` sub-input
    class name so two filtersets sharing a ``field_name`` cannot mint two
    distinct classes under one GraphQL type name (spec-027 forward path; see
    ``_build_range_input_class``). ``None`` (direct converter callers) keeps the
    unqualified ``<Field>RangeInputType`` name.
    """
    required = bool(filter_instance.extra.get("required", False))

    def _gid_multi(_filter: Filter) -> object:
        return list[str]

    def _gid(_filter: Filter) -> object:
        return str

    def _pk_multi(matched: Filter) -> object:
        return GenericAlias(list, (_relation_identity_annotation(matched, model_field),))

    def _pk(matched: Filter) -> object:
        return _relation_identity_annotation(matched, model_field)

    def _model_choice(matched: Filter) -> object:
        element = _model_choice_identity_annotation(matched, model_field, filterset_cls)
        return GenericAlias(list, (element,)) if _model_choice_takes_list(matched) else element

    def _csv(matched: Filter) -> object:
        # django-filter expands ``Meta.fields`` ``in`` / ``range`` lookups
        # into ``BaseInFilter`` / ``BaseRangeFilter`` (both ``BaseCSVFilter``
        # subclasses) whose form field consumes a LIST of values, not a
        # scalar. The element type is model-field-driven so a CSV ``in`` over
        # a choice column keeps its enum and a 64-bit column keeps ``BigInt``.
        return GenericAlias(list, (_element_annotation(matched, model_field, owner_definition),))

    def _range(matched: Filter) -> object:
        inner = _scalar_from_model_field(model_field)
        return _build_range_input_class(matched, inner, filterset_cls)

    def _list(matched: Filter) -> object:
        return GenericAlias(list, (_element_annotation(matched, model_field, owner_definition),))

    def _typed(matched: Filter) -> object:
        return _element_annotation(matched, model_field, owner_definition)

    def _choice(matched: Filter) -> object:
        type_name = _owner_type_name(owner_definition) or "Filter"
        return _choice_enum_from_filter(matched, type_name, model_field)

    def _catchall(matched: Filter) -> object:
        # Catch-all scalar branch. ``Filter(method=...)`` filters land
        # here when their ``field_class`` is a recognized form field; an
        # unknown form-field shape raises per spec-027 Decision 4.
        form_field = getattr(matched, "field", None)
        method = getattr(matched, "method", None)
        if method is not None and form_field is None:
            raise ConfigurationError(
                f"Filter(method={_safe_arg_repr(method)}) on {_safe_arg_repr(matched)} exposes no "
                "form field; declare an explicit `Filter(method=..., field_class=...)` "
                "or wrap the method on a typed filter primitive.",
            )
        if getattr(matched, "lookup_expr", None) == "isnull":
            # ``isnull`` is a boolean predicate regardless of the column type;
            # the model field (the column's value type) is irrelevant here.
            return bool
        return _element_annotation(matched, model_field, owner_definition)

    annotation = convert_with_mro(
        filter_instance,
        isinstance_prechecks=_filter_input_prechecks(
            _gid_multi,
            _gid,
            _pk_multi,
            _pk,
            _model_choice,
            _csv,
            _range,
            _list,
            _typed,
            _choice,
            _catchall,
        ),
        scalar_registry={},
        fallthrough_error_factory=_unexpected_filter_dispatch,
    )
    if not required:
        # Every precheck handler above returns a runtime annotation (a class, ``NewType``,
        # or scalar), and the registry is empty.
        annotation = cast("_TypeForm", annotation) | None
    return annotation


def normalize_input_value(
    filter_instance: Filter,
    raw_value: object,
    field_name: str | None = None,
) -> object:
    """Translate a Strawberry-shaped input value into ``django-filter`` form-data.

    Returns one of three shapes:

    - a scalar value (``str`` / ``int`` / wire-form GlobalID string /
      enum ``.value``) when the filter consumes a single form-data key;
      the ``BLANK`` member (value ``""``) of a generated choice ``exact``
      (``EnumChoiceFilter``) becomes ``BLANK_CHOICE``, so it filters
      ``= ''`` while a raw ``""`` keeps django-filter's empty-value skip.
      A GlobalID is kept in its base64 wire form (not pre-decoded to a
      bare ``node_id``) so the bound filter can validate its
      ``type_name`` before decoding;
    - a ``list`` (for ``GlobalIDMultipleChoiceFilter`` / ``ListFilter`` /
      ``ArrayFilter``) when ``django-filter`` consumes a list;
    - a ``dict[str, Any]`` patch the caller merges into the form-data
      dict when the filter consumes more than one positional form-data
      key (``RangeFilter`` -> ``{<field>_0, <field>_1}``).

    Kind order is ``_FILTER_INPUT_KIND_TYPES``, the same table convert
    walks. ``TypedFilter`` is convert-only: normalize returns
    ``MRO_CONTINUE`` so ChoiceFilter / the unwrap catch-all can still
    fire. ``None`` from unwrap (an enum member whose ``.value`` is
    ``None``) is a successful result, not a continue signal.

    Per spec-027 Decision 4's ``normalize_input_value`` contract, the
    multi-key return shape lets the ``_normalize_input`` caller merge
    the patch without inventing a sentinel-pair object.
    """
    # Defensive short-circuit against ``strawberry.UNSET`` reaching the
    # branches below: every branch indexes / iterates / coerces
    # ``raw_value`` and would either raise ``TypeError`` (UNSET is not
    # iterable) or silently pass the UNSET sentinel into ``data``. Every
    # caller MUST treat UNSET as "not supplied" - same as ``None`` - so
    # this entry point is the single defensive line every future caller
    # benefits from.
    if is_inactive_value(raw_value, unset_sentinel=UNSET):
        return None

    def _gid_multi(_filter: Filter) -> object:
        items = _require_list_container(_filter, raw_value, "GlobalID list")
        return [_encode_global_id_input(item) for item in items]

    def _gid(_filter: Filter) -> object:
        return _encode_global_id_input(raw_value)

    def _pk_multi(_filter: Filter) -> object:
        items = _require_list_container(_filter, raw_value, "primary-key list")
        return [_unwrap_enum_member(item) for item in items]

    def _pk(_filter: Filter) -> object:
        return _unwrap_enum_member(raw_value)

    def _model_choice(matched: Filter) -> object:
        # The consumer's model-choice form field cleans the raw value(s) itself.
        if not _model_choice_takes_list(matched):
            return _unwrap_enum_member(raw_value)
        items = _require_list_container(matched, raw_value, "model-choice list")
        return [_unwrap_enum_member(item) for item in items]

    def _csv(_filter: Filter) -> object:
        # ``in`` / ``range`` generated CSV filters consume a list; unwrap
        # any enum members per element (parity with ``ListFilter`` below).
        items = _require_list_container(_filter, raw_value, "CSV membership list")
        return [_unwrap_enum_member(item) for item in items]

    def _range(matched: Filter) -> object:
        return _normalize_range_value(matched, raw_value, field_name=field_name)

    def _list(_filter: Filter) -> object:
        items = _require_list_container(_filter, raw_value, "list input")
        return [_unwrap_enum_member(item) for item in items]

    def _typed(_filter: Filter) -> object:
        return MRO_CONTINUE

    def _choice(matched: Filter) -> object:
        value = _unwrap_enum_member(raw_value)
        if (
            isinstance(matched, EnumChoiceFilter)
            and isinstance(raw_value, enum.Enum)
            and isinstance(value, str)
            and value == ""
        ):
            # The enum's ``BLANK`` member: a value, never django-filter's empty skip.
            # A raw ``""`` (not a member) stays ``""`` and keeps that skip.
            return BLANK_CHOICE
        return value

    def _catchall(_filter: Filter) -> object:
        return _unwrap_enum_member(raw_value)

    return convert_with_mro(
        filter_instance,
        isinstance_prechecks=_filter_input_prechecks(
            _gid_multi,
            _gid,
            _pk_multi,
            _pk,
            _model_choice,
            _csv,
            _range,
            _list,
            _typed,
            _choice,
            _catchall,
        ),
        scalar_registry={},
        fallthrough_error_factory=_unexpected_filter_dispatch,
    )


def _require_list_container(
    filter_instance: Filter,
    raw_value: object,
    shape: str,
) -> list[object] | tuple[object, ...]:
    """Fail loud when a list-consuming normalize arm receives another container.

    ``GlobalIDMultipleChoiceFilter`` / ``BaseCSVFilter`` (``in`` / ``range``)
    / ``ListFilter`` / ``ArrayFilter`` normalize by iterating ``raw_value``.
    The schema declares every such input as a GraphQL list, so the wire can
    only deliver a list; the reachable non-list shapes are direct-Python
    ``apply_sync`` caller mistakes. The previous arms SPLATTED whatever they
    were handed: a ``{'start': 1, 'end': 5}`` patch normalized to its KEYS
    (``['start', 'end']``) and a string normalized to its CHARACTERS -- both
    silently dropped the intended predicate and poisoned the form-data dict
    with junk members. The shape is invalid, not merely iterable, so it
    raises the typed ``ConfigurationError`` (fail loud, never a silent
    keys-for-values swap). Returns ``raw_value``, narrowed to the list or
    tuple it proved, for the arm to iterate.
    """
    if not isinstance(raw_value, (list, tuple)):
        raise ConfigurationError(
            f"{filter_instance.__class__.__name__} consumes a list of values for its "
            f"{filter_instance.field_name!r} input, but received a non-list container "
            f"({_safe_type_name(raw_value)} {_safe_arg_repr(raw_value)}) for the {shape}; "
            "send a list (the GraphQL schema already rejects this shape over the wire).",
        )
    return raw_value


# ---------------------------------------------------------------------------
# Range / GlobalID / Enum value helpers
# ---------------------------------------------------------------------------


def _encode_global_id_input(value: object) -> object:
    """Return the wire-form GlobalID string for a ``relay.GlobalID``-or-string.

    ``normalize_input_value`` feeds GlobalID-aware filters their form-data
    value. A ``relay.GlobalID`` OBJECT (the shape a direct-Python
    ``apply_sync`` / ``apply_async`` caller passes) MUST keep its
    ``type_name`` so ``GlobalIDFilter.filter`` /
    ``GlobalIDMultipleChoiceFilter.filter`` can validate it against the
    target GraphQL type (spec-027 Decision 4) before any queryset clause runs.
    The previous implementation eagerly decoded the object down to its
    bare ``node_id`` here -- stripping the ``type_name`` *before*
    validation, so a wrong-type GlobalID object silently passed the gate.
    Re-encoding to the base64 wire string preserves the type, survives
    the ``django-filter`` form ``clean`` step, and lets the bound filter
    run the canonical decode-and-validate path. A ``str`` value is
    already wire-form and passes through unchanged, so the GraphQL string
    path is untouched.
    """
    if isinstance(value, relay.GlobalID):
        return relay.to_base64(value.type_name, value.node_id)
    return value


def _unwrap_enum_member(value: object) -> object:
    """Return ``value.value`` for an ``enum.Enum`` member; passthrough otherwise.

    Structural ``isinstance(value, enum.Enum)`` rather than duck-typing on
    ``.value`` / ``.name``: a ``@strawberry.enum`` decorates a Python
    ``enum.Enum``, so its members ARE ``enum.Enum`` instances. The structural
    check also correctly unwraps a member whose ``.value`` is legitimately
    ``None`` (the prior value-truthiness guard returned such a member
    un-unwrapped), and it never misfires on plain objects that merely expose a
    ``.value`` attribute (e.g. ``decimal.Decimal``).

    Single-level unwrap - nested-list / nested-dict inputs are not
    recursively unwrapped. No current consumer produces such shapes (the
    Django converter pipeline yields flat scalars / lists from the
    `django-filter` form-field hierarchy); a future nested-shape
    ``ListFilter`` would need its own per-level walk.
    """
    if isinstance(value, enum.Enum):
        return value.value
    return value


# Range sub-input classes built per filter instance, keyed by generation identity
# (see ``_build_range_input_class``). Weak keys tie each cache to its filter's
# lifetime without writing an attribute onto the upstream ``Filter`` object.
_RANGE_INPUT_CLASSES: WeakKeyDictionary[
    Filter,
    dict[tuple[type[FilterSet] | None, str, _TypeForm], type[object]],
] = WeakKeyDictionary()


def _build_range_input_class(
    filter_instance: Filter,
    inner: _TypeForm,
    filterset_cls: type[FilterSet] | None = None,
) -> type[object]:
    """Return a Strawberry input dataclass with ``start: T | None`` and ``end: T | None``.

    Classes are cached per filter instance by their full generation identity:
    owning filterset, Django field path, and inner scalar. A single declared
    filter instance can be converted first without an owner (a direct converter
    call) and later through its owning filterset; one unkeyed cache slot would
    return the earlier unqualified class and defeat owner-scoped naming. Including
    ``inner`` also prevents a reused/mutated filter from retaining a class whose
    axes expose the wrong scalar.

    The class name is qualified by the owning ``FilterSet`` when one is
    supplied -- ``f"{filterset_cls.__name__}{Pascal(field_name)}RangeInputType"``
    -- mirroring the per-field operator-bag naming
    (``ClassBasedTypeNameMixin.type_name_for``). Without this qualifier the name
    derived from ``field_name`` alone, so two filtersets that share a
    ``field_name`` for a ``RangeFilter`` (e.g. both filter a ``price`` column)
    each mint a DISTINCT sub-input class under the SAME GraphQL type name.
    Because these nested classes are embedded directly in the annotation (NOT
    materialized through Decision 9's ``_materialized_names`` ledger, and NOT
    checked by the arguments-factory collision registry), Strawberry does not
    reject the clash -- it SILENTLY keeps whichever class it registers first and
    drops the other, so a filterset whose ``RangeFilter`` resolves a different
    scalar (a ``date`` range vs an ``int`` range) is advertised with the wrong
    axis type over the wire. spec-027 assumed a duplicate-type
    error would surface; it does not, so the per-filterset-scoped name (the
    documented forward path) is applied here. ``None`` (direct converter callers
    that build no schema) keeps the unqualified ``<Field>RangeInputType`` name.
    """
    field_name = getattr(filter_instance, "field_name", "field") or "field"
    cache_key = (filterset_cls, field_name, inner)
    cache = _RANGE_INPUT_CLASSES.setdefault(filter_instance, {})
    cached = cache.get(cache_key)
    if cached is not None:
        return cached
    prefix = filterset_cls.__name__ if filterset_cls is not None else ""
    cls_name = f"{prefix}{_pascal_case(field_name)}RangeInputType"
    cls = build_input_class(
        cls_name,
        [("start", inner | None, {"default": None}), ("end", inner | None, {"default": None})],
    )
    cache[cache_key] = cls
    return cls


def _normalize_range_value(
    filter_instance: Filter,
    raw_value: object,
    field_name: str | None = None,
) -> dict[str, object]:
    """Return the positional form-data patch ``{<name>_0, <name>_1}`` for a RangeFilter.

    Per spec-027 Decision 4: Django's ``RangeWidget.value_from_datadict``
    reads positional keys ``name_0`` / ``name_1`` (NOT named ``_from`` /
    ``_to`` keys). The patch's key prefix is the form-data field name
    (``filter_instance.field_name`` for direct filters; the caller may
    override via ``field_name`` for the dataclass-attribute case where
    the Strawberry attr differs from the django-filter form-key).

    Partial-range inputs surface only the supplied positional key
    (``{<name>_0}`` for start-only, ``{<name>_1}`` for end-only, ``{}``
    for neither). Omitting ``None``-valued axes preserves the form-data
    "axis not supplied" convention ``django-filter`` consumes and keeps
    the patch keys load-bearing for any caller walking ``data.keys()``.
    """
    base = field_name or filter_instance.field_name or "range"
    start: object = (
        getattr(raw_value, "start", None)
        if not isinstance(raw_value, dict)
        else raw_value.get("start")
    )
    end: object = (
        getattr(raw_value, "end", None)
        if not isinstance(raw_value, dict)
        else raw_value.get("end")
    )
    # Drop ``None``- and ``UNSET``-valued axes so partial-range inputs surface only
    # the supplied positional key. Django's ``RangeWidget.value_from_datadict``
    # treats a missing key the same as a ``None``-valued one, but emitting
    # ``{<name>_0: None}`` or ``{<name>_0: UNSET}`` to the form-data dict surfaces
    # "axis supplied, value is inactive" to any caller walking ``data.keys()`` and
    # leaks ``UNSET`` into form-field cleaning -- the explicit
    # ``is_inactive_value`` rigor mirrors ``normalize_input_value``'s ``raw_value
    # is None or raw_value is UNSET`` entry guard.
    patch: dict[str, object] = {}
    if not is_inactive_value(start, unset_sentinel=UNSET):
        patch[f"{base}_0"] = _unwrap_enum_member(start)
    if not is_inactive_value(end, unset_sentinel=UNSET):
        patch[f"{base}_1"] = _unwrap_enum_member(end)
    return patch


def _owner_type_name(owner_definition: DjangoTypeDefinition | None) -> str | None:
    """Return the GraphQL type name for ``owner_definition`` (or ``None``).

    Delegates to ``DjangoTypeDefinition.graphql_type_name`` so the three
    callers (this helper, ``filters/base.py::_accepted_globalid_type_names``,
    ``types/finalizer.py::_bind_filterset_owner``) share one derivation
    rule and cannot drift across renames.
    """
    return owner_definition.graphql_type_name if owner_definition is not None else None


# ---------------------------------------------------------------------------
# Logical-operator + input-field builders
# ---------------------------------------------------------------------------


def _build_logic_fields(type_name: str) -> list[tuple[str, object, dict[str, object]]]:
    """Return ``(python_attr, annotation, field_kwargs)`` triples for logical operators.

    Operators come from ``LOGIC_OPERATORS`` so adding an operator automatically
    emits the field on the generated input without parallel edits. The annotations
    follow the INSIDE-list shape: the ``Annotated[...]`` wraps the
    forward-reference string directly, and the ``list[...]`` (for sequence operators)
    wraps the ``Annotated[...]`` -- NOT the other way around. Non-sequence operators
    use a single self-ref. GraphQL surface names ride through
    ``optional_field_kwargs`` -> ``strawberry.field(name=...)`` because the
    wire tokens are Python keywords and cannot be dataclass field names.
    """
    # basedpyright: it models an ``Annotated[...]`` value as the bare special form, which has
    # no ``__or__``; the runtime ``Annotated`` alias widens with ``| None`` below.
    self_ref = cast("_TypeForm", Annotated[type_name, strawberry.lazy(INPUTS_MODULE_PATH)])  # pyright: ignore[reportInvalidCast]
    list_ref = GenericAlias(list, (self_ref,))
    return [
        (
            op.python_attr,
            (list_ref if op.is_sequence else self_ref) | None,
            optional_field_kwargs(op.python_attr, op.wire_name),
        )
        for op in LOGIC_OPERATORS
    ]


# One bag lookup's django-filter form key (its ``get_filters()`` name) and filter.
FormKeyedFilter = tuple[str, Filter]


@dataclass(frozen=True)
class FilterLookupTable:
    """Every operator-bag lookup's django-filter form key, decided once per filter set.

    ``heads`` maps ``head -> lookup token -> (form key, filter)`` in
    ``get_filters()`` order; ``_build_input_fields`` emits one input field per
    head from it. ``by_input_attr`` maps ``input attr -> lookup attr -> (form
    key, filter)``, keyed by each head's own spelling and by its flattened
    generated-input attr; ``FilterSet._normalize_input`` reads it. Both views
    hold the same entries, so the generated input and the form data it
    normalizes to cannot disagree. ``gate_paths`` maps the same keys to the
    head's ``check_<path>_permission`` path: a declared head, and an expansion
    of a child's declared filter, gates on its own name (``shelf__home_branch``
    fires ``check_shelf_home_branch_permission`` and, through the relation walk,
    the child's ``check_home_branch_permission``, as the nested spelling does);
    any other head gates on its filter's ``field_name`` (the ORM path), so
    ``name`` and ``name__icontains`` share the ``name`` gate. ``source`` is the
    ``get_filters()`` result the table was built from: the cache is valid only
    while that object is.
    """

    source: Mapping[str, Filter]
    heads: Mapping[str, Mapping[str, FormKeyedFilter]]
    by_input_attr: Mapping[str, Mapping[str, FormKeyedFilter]]
    gate_paths: Mapping[str, str]


def _is_expanded_declared_filter(filter_instance: Filter) -> bool:
    """Whether ``filter_instance`` is a ``RelatedFilter`` expansion of a declared child filter."""
    from .sets import filter_generation_provenance

    record = filter_generation_provenance(filter_instance)
    return record is not None and record.origin == "declared" and bool(record.expanded_from)


def _group_filters_by_head(
    filterset_cls: type[FilterSet],
    all_filters: Mapping[str, Filter],
) -> OrderedDict[str, OrderedDict[str, FormKeyedFilter]]:
    """Group ``get_filters()`` by input head, keeping each lookup's own form key.

    A declared filter, and a ``RelatedFilter`` expansion of a child's declared
    filter, is its own head: its name is its form key even when it ends in its
    own lookup token (``name__exact``). A generated ``<path>__<lookup>`` entry
    joins the ``<path>`` head under ``<lookup>``. Two filters claiming one
    ``(head, lookup)`` slot would leave one unreachable from the generated
    input, so that raises.
    """
    declared_filters = getattr(filterset_cls, "declared_filters", {})
    grouped: OrderedDict[str, OrderedDict[str, FormKeyedFilter]] = OrderedDict()
    for filter_name, filter_instance in all_filters.items():
        # Skip expanded RelatedFilter entries (e.g., `self_link__self_link`
        # under a self-referential filterset). The top-level
        # `RelatedFilter` forward-ref already exposes the same target;
        # the expanded duplicate would otherwise reach the leaf branch
        # and trip the `ChoiceFilter` guard.
        if "__" in filter_name and isinstance(filter_instance, RelatedFilter):
            continue
        lookup_expr = filter_instance.lookup_expr
        if filter_name in declared_filters or _is_expanded_declared_filter(filter_instance):
            head, lookup_token = filter_name, lookup_expr
        else:
            # django-filter names a generated filter ``<path>__<lookup>``, or the
            # bare ``<path>`` for ``exact``; a trailing token that is not the
            # filter's own lookup belongs to the path.
            head, _, lookup_token = filter_name.rpartition("__")
            if not head or lookup_token != lookup_expr:
                head, lookup_token = filter_name, lookup_expr
        bag = grouped.setdefault(head, OrderedDict())
        prior = bag.get(lookup_token)
        if prior is not None:
            raise ConfigurationError(
                f"{filterset_cls.__qualname__}: filters {prior[0]!r} and {filter_name!r} "
                f"both bind the {lookup_token!r} lookup of input field {head!r}, so one "
                "would be unreachable from the generated input. Rename one filter or "
                "drop one via Meta.fields / Meta.exclude.",
            )
        bag[lookup_token] = (filter_name, filter_instance)
    return grouped


def filter_lookup_table(filterset_cls: type[FilterSet]) -> FilterLookupTable:
    """Return ``filterset_cls``'s ``FilterLookupTable``, built once per ``get_filters()`` result.

    The flattened generated-input attr of a ``<path>__<field>`` head is an alias
    only when no head is literally spelled that way (a head's own spelling wins);
    two heads sharing one alias raise, since one would be unreachable.
    """
    all_filters = filterset_cls.get_filters()
    cached = filterset_cls._lookup_table
    if cached is not None and cached.source is all_filters:
        return cached
    heads = _group_filters_by_head(filterset_cls, all_filters)
    declared_filters = getattr(filterset_cls, "declared_filters", {})
    by_input_attr: dict[str, Mapping[str, FormKeyedFilter]] = {}
    gate_paths: dict[str, str] = {}
    for head, bag in heads.items():
        by_input_attr[head] = {
            LOOKUP_NAME_MAP.get(token, (token, token))[0]: entry for token, entry in bag.items()
        }
        _form_key, sample_filter = next(iter(bag.values()))
        # A declared head gates on its own name; so does an expansion of a child's
        # declared filter, whose flat spelling must fire the gates its nested twin
        # fires (``utils/permissions.py::_fire_flat_relation_path_gates`` walks the
        # relation hops and fires the child's ``check_<name>_permission``).
        gate_paths[head] = (
            head
            if head in declared_filters or _is_expanded_declared_filter(sample_filter)
            else _bound_field_name(sample_filter)
        )
    alias_heads: dict[str, str] = {}
    for head in heads:
        input_attr = flatten_lookup_path(head)
        if input_attr in heads:
            continue
        prior_head = alias_heads.setdefault(input_attr, head)
        if prior_head != head:
            raise ConfigurationError(
                f"{filterset_cls.__qualname__}: filters {prior_head!r} and {head!r} both "
                f"generate the input attribute {input_attr!r} (Django path separators "
                "flatten to '_'), so one would be unreachable. Rename one filter or "
                "drop one via Meta.fields / Meta.exclude.",
            )
        by_input_attr[input_attr] = by_input_attr[head]
        gate_paths[input_attr] = gate_paths[head]
    table = FilterLookupTable(
        source=all_filters,
        heads=heads,
        by_input_attr=by_input_attr,
        gate_paths=gate_paths,
    )
    filterset_cls._lookup_table = table
    return table


def _build_input_fields(
    filterset_cls: type[FilterSet],
    owner_definition: DjangoTypeDefinition | None = None,
) -> list[tuple[str, object, dict[str, object]]]:
    """Return per-field input triples for a filterset's top-level GraphQL input.

    Emits one entry per head of ``filter_lookup_table`` (the grouped Layer-4
    ``get_filters()`` expansion): a forward-reference ``Annotated[...]`` for
    ``RelatedFilter`` boundaries OR a per-field operator-bag dataclass for leaf
    paths, one bag attr per lookup the table holds. Populates ``_field_specs``
    for the active-field walk and the permission gates.
    """
    # The metaclass stores ``related_filters`` from
    # ``sets_mixins.py::collect_related_declarations`` (``RelatedFilter`` only).
    related_filters: Mapping[str, RelatedFilter] = getattr(
        filterset_cls,
        "related_filters",
        OrderedDict(),
    )
    lookup_table = filter_lookup_table(filterset_cls)

    # ``HIDE_FLAT_FILTERS`` (default ``False`` -- matches
    # ``django-graphene-filters``'s ``conf.py`` default) controls whether the
    # flat relational traversal fields (``categoryName``, deep
    # ``entriesPropertyCategoryName``, ...) are emitted. When hidden, the
    # relation is filtered only through its nested ``RelatedFilter`` branch
    # (``category: { name: { ... } }``) -- the strawberry-django shape. When
    # shown, BOTH the flat and nested shapes appear (graphene-django parity).
    # Upstream achieves this with a throwaway trimmed-subclass + a separate
    # flat-args merge on the connection field
    # (``django_graphene_filters/connection_field.py::_get_trimmed_filterset_class``);
    # because this package emits a single Strawberry input type here, the same
    # ``is_expanded_child`` rule is just a skip in this loop, so the hidden
    # operator-bag classes are never built in the first place. The key is read
    # through its ``conf.py`` named reader; truthiness coercion is this
    # consumer's own semantics (the reader stays thin).
    hide_flat_filters = bool(hide_flat_filters_setting())

    def _visible_entries() -> Iterator[tuple[str, Mapping[str, FormKeyedFilter]]]:
        """Yield the grouped entries minus the ``HIDE_FLAT_FILTERS`` expanded children.

        A flat relational traversal path (``category__name``,
        ``entries__property__category__name``) is an "expanded child" of a
        declared ``RelatedFilter`` - its first path segment names the relation.
        Such paths are reachable through the nested branch already; hide them
        when ``HIDE_FLAT_FILTERS`` is set -- the same ``is_expanded_child``
        skip upstream applies inside
        ``django_graphene_filters/connection_field.py::_get_trimmed_filterset_class``.
        This pre-filter stays filter-family semantics, BEFORE the shared
        emission scaffold.
        """
        for top_name, lookup_bag in lookup_table.heads.items():
            if (
                hide_flat_filters
                and "__" in top_name
                and top_name.split("__", 1)[0] in related_filters
            ):
                continue
            yield top_name, lookup_bag

    def _related_target_of(
        top_name: str,
        _lookup_bag: Mapping[str, FormKeyedFilter],
    ) -> tuple[bool, type[FilterSet] | None]:
        rel_filter = related_filters.get(top_name)
        if rel_filter is None:
            return False, None
        return True, rel_filter.filterset

    def _leaf_of(
        top_name: str,
        python_attr: str,
        lookup_bag: Mapping[str, FormKeyedFilter],
    ) -> tuple[object, str]:
        # Leaf path: build a per-field operator-bag input class. Every
        # operator-bag leaf is optional (``optional_field_kwargs``); an
        # omitted ``default`` would build a REQUIRED field.
        bag_name = filterset_cls.type_name_for(python_attr)
        bag_specs: list[tuple[str, object, dict[str, object]]] = []
        for lookup, (_form_key, leaf_filter) in lookup_bag.items():
            lookup_python_attr, lookup_graphql_name = LOOKUP_NAME_MAP.get(lookup, (lookup, lookup))
            model_field = _model_field_for_filter(filterset_cls, leaf_filter)
            annotation = convert_filter_to_input_annotation(
                leaf_filter,
                model_field,
                owner_definition,
                filterset_cls,
            )
            bag_specs.append(
                (
                    lookup_python_attr,
                    annotation,
                    optional_field_kwargs(lookup_python_attr, lookup_graphql_name),
                ),
            )
        bag_class = build_input_class(bag_name, bag_specs)
        # The ``FieldSpec`` source path is the head's permission gate path;
        # the form keys the normalizer emits come from the lookup table.
        return bag_class | None, lookup_table.gate_paths[top_name]

    # The per-field emission scaffold (python-attr flatten -> camel-case ->
    # optional kwargs -> related lazy-ref vs leaf -> triple + ``FieldSpec``) is
    # single-sited in ``utils/inputs.py::emit_set_input_field_triples``; the
    # closures above carry the filter-family semantics.
    return emit_set_input_field_triples(
        filterset_cls,
        _visible_entries(),
        related_target_of=_related_target_of,
        related_source_path_of=lambda top_name, _lookup_bag: top_name,
        leaf_of=_leaf_of,
        input_type_name_for=_input_type_name_for,
        module_path=INPUTS_MODULE_PATH,
        field_specs=_field_specs,
    )


def _model_field_for_filter(
    filterset_cls: type[FilterSet],
    filter_instance: Filter,
) -> ModelField | None:
    """Resolve the Django model field a filter targets (or ``None``).

    Folder-owned path walk: delegates to ``django_filters.utils.get_model_field``
    -- the same ``__``-separated relation traversal ``filters/base.py``
    (``IntegerInFilter``) and ``filters/sets.py`` (``get_fields`` ``"__all__"``
    expansion) already use -- so a typo / missing hop returns ``None`` and a
    nested path (e.g. ``galaxy__name``) yields the terminal field under one
    rule. The filterset / ``field_name`` guards stay here because the converter
    receives a filter instance, not a bare ``(model, path)`` pair.

    Contract note: ``get_model_field`` raises ``RuntimeError`` when a relation
    hop is still an *unresolved* lazy string (``field.remote_field.model`` has
    no ``_meta``) -- i.e. Django's app registry is not populated. That state is
    unreachable here: this helper runs only under ``_build_input_fields`` during
    ``finalize_django_types()``, which Django guarantees runs after
    ``apps.populate()`` has resolved every FK. A raise therefore signals a
    genuine "``FilterSet`` loaded before Django setup" misconfiguration and MUST
    surface loudly rather than degrade to ``None`` (which would silently treat a
    real relation as an unknown field). The reachable ``None`` path -- typo /
    missing hop -- is preserved unchanged.
    """
    # django-filter's metaclass stores ``_meta = FilterSetOptions(...)`` on every filterset.
    meta: FilterSetOptions | None = getattr(filterset_cls, "_meta", None)
    model: type[models.Model] | None = getattr(meta, "model", None)
    if model is None:
        return None
    field_name: str | None = getattr(filter_instance, "field_name", None)
    if not field_name:
        return None
    return get_model_field(model, field_name)


def construct_search(all_filters: Mapping[str, object]) -> dict[str, str]:
    """Translate ``LOOKUP_PREFIXES``-vocabulary keys into a ``{name: lookup}`` map.

    No package code calls it yet: the ``Meta.search_fields`` consumer surface is
    spec-060's, and its wiring point is the ``TODO(spec-060 Slice 1)`` anchor in
    ``filters/sets.py``. It is the one consumer of ``LOOKUP_PREFIXES``. The
    prefix-translation tests in ``tests/filters/test_inputs.py`` exercise the
    helper directly.
    """
    result: dict[str, str] = {}
    for filter_name in all_filters:
        prefix = filter_name[:1]
        if prefix in LOOKUP_PREFIXES:
            result[filter_name[1:]] = LOOKUP_PREFIXES[prefix]
    return result


# ---------------------------------------------------------------------------
# Module-global materialization (spec-027 Decision 9)
# ---------------------------------------------------------------------------


def materialize_input_class(name: str, cls: type[object]) -> None:
    """Set ``cls`` as a real module global of ``filters.inputs`` under ``name``.

    Thin family wrapper over the ``make_set_input_namespace`` materializer.
    See ``utils/inputs.py::materialize_generated_input_class`` for the
    Strawberry ``LazyType.resolve_type`` contract, the ``(name, cls)``
    idempotency clause, and the distinct-class collision raise (spec-027
    Decision 9).
    """
    _materialize_input(name, cls)


def clear_filter_input_namespace() -> None:
    """Reset the filter-input ledger and per-filterset binding state for a fresh build.

    Thin family wrapper over the ``make_set_input_namespace`` heavy clear
    (ledger, ``_field_specs``, ``FilterArgumentsFactory`` caches, every
    ``FilterSet`` subclass's ``_lifecycle`` binding attrs). Materialized class
    objects stay parked in ``filters.inputs.__dict__`` per the parked-globals
    lifecycle stated on ``utils/inputs.py::make_input_namespace`` - which is what
    keeps held ``strawberry.lazy(...)`` LazyTypes resolving across an autouse
    reload that does not also reload the holder (``test_scalars_api.py`` reloads
    only its own app's schema).
    """
    _clear_input_namespace()


register_subsystem_clear(
    clear_filter_input_namespace,
    owner="filters.input_namespace",
    before_bind=True,
)
