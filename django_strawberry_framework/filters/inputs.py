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
(``_build_input_fields`` / ``_build_logic_fields`` /
``construct_search``), and the module-global materialization /
namespace-clear pair (``materialize_input_class`` /
``clear_filter_input_namespace``).
"""

from __future__ import annotations

import datetime
import decimal
import enum
import uuid
from collections import OrderedDict
from collections.abc import Callable, Iterator
from typing import TYPE_CHECKING, Annotated, Any

import strawberry
from django_filters import ChoiceFilter, Filter, TypedChoiceFilter
from django_filters import RangeFilter as _DjangoRangeFilter
from django_filters.filters import BaseCSVFilter
from django_filters.utils import get_model_field
from strawberry import UNSET, relay

from ..conf import hide_flat_filters_setting
from ..exceptions import ConfigurationError
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
from ..utils.strings import graphql_camel_name, pascal_case_or_raise
from .base import (
    ArrayFilter,
    GlobalIDFilter,
    GlobalIDMultipleChoiceFilter,
    ListFilter,
    RangeFilter,
    TypedFilter,
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

if TYPE_CHECKING:  # pragma: no cover - type-checking-only imports.
    from ..types.definition import DjangoTypeDefinition
    from .sets import FilterSet


# Module path the ``strawberry.lazy(...)`` marker references; pinned as a
# single constant so the factory, ``_build_logic_fields``, and
# ``filter_input_type`` (in ``__init__.py``) all stay in sync.
INPUTS_MODULE_PATH: str = "django_strawberry_framework.filters.inputs"


# Search-prefix vocabulary for the future `Meta.search_fields` card per
# spec-027 Decision 3 Layer 5; consumed by `construct_search` below.
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
# here. Consumed by `FilterSet._normalize_input` (mapping Strawberry-input
# dataclass attrs back to `django-filter`'s form-data keys),
# `_build_input_fields` (for `strawberry.field(name=...)` emission), and
# `normalize_input_value` (for the runtime symmetric).
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


# Logical-operator keys per the cookbook's tree-form contract. Single
# source of truth for the ``and_`` / ``or_`` / ``not_`` Python-attr <->
# ``and`` / ``or`` / ``not`` GraphQL-name pairing. ``sets.py`` imports
# this tuple for ``FilterSet._normalize_input`` (mapping the Python attrs
# onto the form-data keys ``django-filter`` recognizes); ``_build_logic_fields``
# iterates the same pairs to emit the self-referential input fields whose
# GraphQL surface names land through ``optional_field_kwargs`` because
# ``and`` / ``or`` / ``not`` cannot be dataclass field names.
_LOGIC_KEYS: tuple[tuple[str, str], ...] = (("and_", "and"), ("or_", "or"), ("not_", "not"))


# Provenance table populated by ``_build_input_fields`` and consulted at
# runtime by ``FilterSet._normalize_input`` and ``normalize_input_value``.
# Cleanup contract: keyed by ``(FilterSet subclass, python_attr)`` and
# emptied ONLY by ``clear_filter_input_namespace`` (driven by
# ``registry.clear()``). A consumer test suite that reloads model / filter
# modules WITHOUT routing through ``registry.clear()`` retains stale entries
# from the prior build; the filter test files' ``_isolate_registry`` autouse
# fixture clears this map explicitly for exactly that reason.
#
# Decision-9 namespace lifecycle. Mechanics live in
# ``utils/inputs.py::make_set_input_namespace`` (heavy clear: ledger +
# field_specs + factory caches + ``_lifecycle`` binding). This module keeps
# the spec-named public wrappers and the disjoint per-subsystem ledgers.
# ``clear_filter_input_namespace`` leaves class objects parked in
# ``filters.inputs.__dict__`` -- ``setattr`` on the next materialize replaces
# them in place. Stripping via ``delattr`` would break ``strawberry.lazy(...)``
# holders whose autouse reload did not also reload the consumer module.
_materialized_names: dict[str, type]
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


def _safe_repr(value: Any) -> str:
    """Render a diagnostic value without allowing a hostile ``__repr__`` to escape."""
    try:
        return repr(value)
    except BaseException:
        try:
            type_name = type(value).__name__
        except BaseException:
            type_name = "object"
        if not isinstance(type_name, str):
            type_name = "object"
        return f"<unprintable {type_name}>"


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
            f"_pascal_case received {_safe_repr(bad)} which contains no word "
            "characters; rename the RangeFilter's `field_name=` so its "
            "name has at least one alphanumeric token.",
        ),
    )


def _scalar_from_form_field(form_field: Any) -> type:
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
    # table at spec-027 Decision 4 M1 lists CharField as a recognized
    # shape, and a future reader who inspects this function should see
    # that the mapping is intentional, not an accidental fallthrough.
    if isinstance(form_field, forms.CharField):
        return str
    return str


def _scalar_from_model_field(model_field: Any) -> Any:
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

    return scalar_for_field(model_field)


def _choice_enum_from_filter(
    filter_instance: ChoiceFilter,
    type_name: str,
    model_field: Any,
) -> Any:
    """Derive a Strawberry enum from a ``ChoiceFilter``'s underlying choice source.

    Per spec-027 Decision 4 M5 (line 591), a ``ChoiceFilter`` whose source
    is not a Django ``Choices``-derived enum raises ``ConfigurationError``
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
            f"ChoiceFilter on {_safe_repr(filter_instance)} is not backed by a Django "
            "`Choices`-derived enum; wrap the choices through "
            "`django.db.models.TextChoices` / `IntegerChoices` or register a "
            "custom scalar via `SCALAR_MAP`.",
        )
    return convert_choices_to_enum(model_field, type_name)


def _element_annotation(
    filter_instance: Filter,
    model_field: Any,
    owner_definition: DjangoTypeDefinition | None,
) -> Any:
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
# coerced on the other (spec-051 C3). ``TypedFilter`` is convert-only: List /
# Array / Range already matched, so normalize returns ``MRO_CONTINUE`` and
# falls through to ChoiceFilter / the catch-all. Last entry is ``object`` (the
# original ``else``): convert's method-filter / ``isnull`` / scalar arm,
# normalize's unwrap. A duck-typed non-``Filter`` still reaches that arm so
# hostile-``__repr__`` diagnostics stay typed ``ConfigurationError``.
_FILTER_INPUT_KIND_TYPES: tuple[type | tuple[type, ...], ...] = (
    GlobalIDMultipleChoiceFilter,
    GlobalIDFilter,
    BaseCSVFilter,
    (RangeFilter, _DjangoRangeFilter),
    (ListFilter, ArrayFilter),
    TypedFilter,
    (ChoiceFilter, TypedChoiceFilter),
    object,
)


def _filter_input_prechecks(
    *handlers: Callable[[Any], Any],
) -> list[tuple[type | tuple[type, ...], Callable[[Any], Any]]]:
    """Zip the shared kind order with per-pass handlers.

    ``zip(..., strict=True)`` fails loud if convert or normalize forgets a
    handler when the kind table grows.
    """
    return list(zip(_FILTER_INPUT_KIND_TYPES, handlers, strict=True))


def _unexpected_filter_dispatch(obj: Any) -> ConfigurationError:
    """Fallthrough factory for the filter-input ``convert_with_mro`` riders.

    Last precheck is ``object`` (the original ``else``), so a real dispatch
    never reaches here. The factory keeps ``convert_with_mro``'s raising
    contract if a handler returns ``MRO_CONTINUE`` all the way through.
    """
    return ConfigurationError(
        f"internal: filter input dispatch reached fallthrough for {_safe_repr(obj)}",
    )


def convert_filter_to_input_annotation(
    filter_instance: Filter,
    model_field: Any,
    owner_definition: DjangoTypeDefinition | None = None,
    filterset_cls: type[FilterSet] | None = None,
) -> Any:
    """Return the Strawberry annotation for a resolved ``django-filter`` filter.

    Implements the Decision-4 M1 conversion table. Kind order is
    ``_FILTER_INPUT_KIND_TYPES`` (most-specific first): Relay-aware primitives,
    then Range / List / Array, then bare ``TypedFilter``, then
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

    def _gid_multi(_filter: Filter) -> Any:
        return list[str]

    def _gid(_filter: Filter) -> Any:
        return str

    def _csv(matched: Filter) -> Any:
        # django-filter expands ``Meta.fields`` ``in`` / ``range`` lookups
        # into ``BaseInFilter`` / ``BaseRangeFilter`` (both ``BaseCSVFilter``
        # subclasses) whose form field consumes a LIST of values, not a
        # scalar. The element type is model-field-driven so a CSV ``in`` over
        # a choice column keeps its enum and a 64-bit column keeps ``BigInt``.
        return list[_element_annotation(matched, model_field, owner_definition)]

    def _range(matched: Filter) -> Any:
        inner = _scalar_from_model_field(model_field)
        return _build_range_input_class(matched, inner, filterset_cls)

    def _list(matched: Filter) -> Any:
        return list[_element_annotation(matched, model_field, owner_definition)]

    def _typed(matched: Filter) -> Any:
        return _element_annotation(matched, model_field, owner_definition)

    def _choice(matched: Filter) -> Any:
        type_name = _owner_type_name(owner_definition) or "Filter"
        return _choice_enum_from_filter(matched, type_name, model_field)

    def _catchall(matched: Filter) -> Any:
        # Catch-all scalar branch. ``Filter(method=...)`` filters land
        # here when their ``field_class`` is a recognized form field; an
        # unknown form-field shape raises per spec-027 line 595.
        form_field = getattr(matched, "field", None)
        method = getattr(matched, "method", None)
        if method is not None and form_field is None:
            raise ConfigurationError(
                f"Filter(method={_safe_repr(method)}) on {_safe_repr(matched)} exposes no "
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
        annotation = annotation | None
    return annotation


def normalize_input_value(
    filter_instance: Filter,
    raw_value: Any,
    field_name: str | None = None,
) -> Any:
    """Translate a Strawberry-shaped input value into ``django-filter`` form-data.

    Returns one of three shapes:

    - a scalar value (``str`` / ``int`` / wire-form GlobalID string /
      enum ``.value``) when the filter consumes a single form-data key.
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

    Per the spec-027 Implementation-discretion item, the
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

    def _gid_multi(_filter: Filter) -> Any:
        return [_encode_global_id_input(item) for item in raw_value]

    def _gid(_filter: Filter) -> Any:
        return _encode_global_id_input(raw_value)

    def _csv(_filter: Filter) -> Any:
        # ``in`` / ``range`` generated CSV filters consume a list; unwrap
        # any enum members per element (parity with ``ListFilter`` below).
        return [_unwrap_enum_member(item) for item in raw_value]

    def _range(matched: Filter) -> Any:
        return _normalize_range_value(matched, raw_value, field_name=field_name)

    def _list(_filter: Filter) -> Any:
        return [_unwrap_enum_member(item) for item in raw_value]

    def _typed(_filter: Filter) -> object:
        return MRO_CONTINUE

    def _choice(_filter: Filter) -> Any:
        return _unwrap_enum_member(raw_value)

    def _catchall(_filter: Filter) -> Any:
        return _unwrap_enum_member(raw_value)

    return convert_with_mro(
        filter_instance,
        isinstance_prechecks=_filter_input_prechecks(
            _gid_multi,
            _gid,
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


# ---------------------------------------------------------------------------
# Range / GlobalID / Enum value helpers
# ---------------------------------------------------------------------------


def _encode_global_id_input(value: Any) -> Any:
    """Return the wire-form GlobalID string for a ``relay.GlobalID``-or-string.

    ``normalize_input_value`` feeds GlobalID-aware filters their form-data
    value. A ``relay.GlobalID`` OBJECT (the shape a direct-Python
    ``apply_sync`` / ``apply_async`` caller passes) MUST keep its
    ``type_name`` so ``GlobalIDFilter.filter`` /
    ``GlobalIDMultipleChoiceFilter.filter`` can validate it against the
    target GraphQL type (spec-027 L603) before any queryset clause runs.
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


def _unwrap_enum_member(value: Any) -> Any:
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


def _build_range_input_class(
    filter_instance: RangeFilter,
    inner: type,
    filterset_cls: type[FilterSet] | None = None,
) -> type:
    """Return a Strawberry input dataclass with ``start: T | None`` and ``end: T | None``.

    Classes are cached on the filter instance by their full generation identity:
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
    cache = getattr(filter_instance, "_range_input_classes", None)
    if cache is None:
        cache = {}
        filter_instance._range_input_classes = cache  # type: ignore[attr-defined]
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
    filter_instance: RangeFilter,
    raw_value: Any,
    field_name: str | None = None,
) -> dict[str, Any]:
    """Return the positional form-data patch ``{<name>_0, <name>_1}`` for a RangeFilter.

    Per spec-027 Decision 4 line 594: Django's ``RangeWidget.value_from_datadict``
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
    start = (
        getattr(raw_value, "start", None)
        if not isinstance(raw_value, dict)
        else raw_value.get("start")
    )
    end = (
        getattr(raw_value, "end", None)
        if not isinstance(raw_value, dict)
        else raw_value.get("end")
    )
    # Drop ``None``-valued axes so partial-range inputs surface only the
    # supplied positional key. Django's ``RangeWidget.value_from_datadict``
    # treats a missing key the same as a ``None``-valued one, but emitting
    # ``{<name>_0: None}`` to the form-data dict surfaces "axis supplied,
    # value is None" to any caller walking ``data.keys()`` -- the explicit
    # ``is not None`` rigor mirrors ``normalize_input_value``'s ``raw_value
    # is None or raw_value is UNSET`` entry guard.
    patch: dict[str, Any] = {}
    if start is not None:
        patch[f"{base}_0"] = start
    if end is not None:
        patch[f"{base}_1"] = end
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


def _build_logic_fields(type_name: str) -> list[tuple[str, Any, dict[str, Any]]]:
    """Return ``(python_attr, annotation, field_kwargs)`` triples for ``and_`` / ``or_`` / ``not_``.

    Names come from ``_LOGIC_KEYS`` (the same pairing ``FilterSet._normalize_input``
    consumes) so a new logical operator cannot land in the runtime map without
    also being emitted on the generated input. The annotations follow the
    INSIDE-list shape: the ``Annotated[...]`` wraps the
    forward-reference string directly, and the ``list[...]`` (for ``and_`` /
    ``or_``) wraps the ``Annotated[...]`` -- NOT the other way around.
    ``not_`` is a single self-ref. GraphQL surface names ride through
    ``optional_field_kwargs`` -> ``strawberry.field(name=...)`` because the
    wire tokens are Python keywords and cannot be dataclass field names.
    """
    self_ref = Annotated[type_name, strawberry.lazy(INPUTS_MODULE_PATH)]
    list_ref = list[self_ref]
    # ``and_`` / ``or_`` take a list of filter inputs; ``not_`` takes one. Arity
    # is the only per-key divergence from ``_LOGIC_KEYS``'s name pairing.
    list_attrs = frozenset({"and_", "or_"})
    return [
        (
            python_attr,
            (list_ref if python_attr in list_attrs else self_ref) | None,
            optional_field_kwargs(python_attr, wire_name),
        )
        for python_attr, wire_name in _LOGIC_KEYS
    ]


def _build_input_fields(
    filterset_cls: type[FilterSet],
    owner_definition: DjangoTypeDefinition | None = None,
) -> list[tuple[str, Any, dict[str, Any]]]:
    """Return per-field input triples for a filterset's top-level GraphQL input.

    Walks ``filterset_cls.get_filters()`` (Layer-4 expansion), groups
    entries by their top-level GraphQL field name, and emits one entry
    per group: a forward-reference ``Annotated[...]`` for
    ``RelatedFilter`` boundaries OR a per-field operator-bag dataclass
    for leaf paths. Populates ``_field_specs`` for the runtime
    normalizer.
    """
    from .base import RelatedFilter as _RelatedFilter

    all_filters = filterset_cls.get_filters()
    related_filters = getattr(filterset_cls, "related_filters", OrderedDict())
    declared_filters = getattr(filterset_cls, "declared_filters", {})
    grouped: OrderedDict[str, OrderedDict[str, Filter]] = OrderedDict()
    for filter_name, filter_instance in all_filters.items():
        # Skip expanded RelatedFilter entries (e.g., `self_link__self_link`
        # under a self-referential filterset). The top-level
        # `RelatedFilter` forward-ref already exposes the same target;
        # the expanded duplicate would otherwise reach the leaf branch
        # and trip the `ChoiceFilter` guard. The top-level
        # `self_link` itself is handled below via the
        # `related_filters` lookup.
        if "__" in filter_name and isinstance(filter_instance, _RelatedFilter):
            continue
        # Top-level GraphQL field for ``<root>__<lookup>``-shaped keys is
        # the part before the LAST ``__``; the per-lookup token is what
        # follows. ``django-filter`` expansion produces flat keys like
        # ``galaxy__name`` (no lookup suffix when only ``exact``) -- we
        # still group them under ``galaxy_name`` flattened.
        if filter_name in declared_filters:
            # A declared filter's class attribute is also the form-field key.
            # Keep the complete name even when it happens to end in its own
            # lookup token (e.g. ``name__exact``). Treating that suffix as an
            # auto-generated lookup collapses the input onto ``name`` and the
            # normalizer then emits ``name`` instead of the declared form key
            # ``name__exact``; django-filter silently ignores the value.
            head, lookup_token = filter_name, filter_instance.lookup_expr
        elif "__" in filter_name:
            head, _, lookup_token = filter_name.rpartition("__")
            # If the trailing token is not the filter's actual lookup expression,
            # it belongs to the path.
            if lookup_token != filter_instance.lookup_expr:
                head, lookup_token = filter_name, filter_instance.lookup_expr
        else:
            head, lookup_token = filter_name, filter_instance.lookup_expr
        grouped.setdefault(head, OrderedDict())[lookup_token] = filter_instance

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

    def _visible_entries() -> Iterator[tuple[str, OrderedDict[str, Filter]]]:
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
        for top_name, lookup_bag in grouped.items():
            if (
                hide_flat_filters
                and "__" in top_name
                and top_name.split("__", 1)[0] in related_filters
            ):
                continue
            yield top_name, lookup_bag

    def _related_target_of(top_name: str, _lookup_bag: Any) -> tuple[bool, Any]:
        rel_filter = related_filters.get(top_name)
        if rel_filter is None:
            return False, None
        return True, rel_filter.filterset

    def _leaf_of(top_name: str, python_attr: str, lookup_bag: Any) -> tuple[Any, str]:
        # Leaf path: build a per-field operator-bag input class. Every
        # operator-bag leaf is optional (``optional_field_kwargs`` - the
        # Finding 2 required-by-default rule).
        sample_filter = next(iter(lookup_bag.values()))
        bag_name = filterset_cls.type_name_for(python_attr)
        bag_specs: list[tuple[str, Any, dict[str, Any]]] = []
        for lookup, leaf_filter in lookup_bag.items():
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
        # ``django_source_path`` is the form-key prefix the normalizer emits
        # into ``django-filter`` form data. For autogen filters whose form
        # key derives from the field name (``name`` / ``name__icontains``)
        # we use the filter's ``field_name``. For declared filters whose
        # form key is the explicit class-attribute name (e.g.
        # ``email_must_have_at_sign``) we use ``top_name`` so the
        # downstream form receives the correct key.
        django_source_path = top_name if top_name in declared_filters else sample_filter.field_name
        return bag_class | None, django_source_path

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


def _model_field_for_filter(filterset_cls: type[FilterSet], filter_instance: Filter) -> Any:
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
    model = getattr(getattr(filterset_cls, "_meta", None), "model", None)
    if model is None:
        return None
    field_name = getattr(filter_instance, "field_name", None)
    if not field_name:
        return None
    return get_model_field(model, field_name)


def construct_search(all_filters: dict[str, Any]) -> dict[str, str]:
    """Translate ``LOOKUP_PREFIXES``-vocabulary keys into a ``{name: lookup}`` map.

    Landed now even though the ``Meta.search_fields`` card is deferred to
    ``0.1.2`` -- the prefix vocabulary constant ``LOOKUP_PREFIXES`` would
    otherwise be dead code. The prefix-translation tests in
    ``tests/filters/test_inputs.py`` exercise the helper directly.
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


def materialize_input_class(name: str, cls: type) -> None:
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
    ``FilterSet`` subclass's ``_lifecycle`` binding attrs). Materialized
    class objects stay parked in ``filters.inputs.__dict__`` so held
    ``strawberry.lazy(...)`` LazyTypes keep resolving across autouse reloads
    that do not also reload the holder (e.g. ``test_scalars_api.py`` reloads
    only its own app's schema).
    """
    _clear_input_namespace()


register_subsystem_clear(
    clear_filter_input_namespace,
    owner="filters.input_namespace",
    before_bind=True,
)
