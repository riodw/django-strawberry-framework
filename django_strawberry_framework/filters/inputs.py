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
from typing import TYPE_CHECKING, Annotated, Any

import strawberry
from django_filters import ChoiceFilter, Filter, TypedChoiceFilter
from django_filters import RangeFilter as _DjangoRangeFilter
from django_filters.filters import BaseCSVFilter
from strawberry import UNSET, relay

from ..conf import settings
from ..exceptions import ConfigurationError
from ..utils.input_values import is_inactive_value
from ..utils.inputs import (
    GeneratedInputFieldSpec,
    build_strawberry_input_class,
    clear_generated_input_namespace,
    graphql_camel_name,
    iter_set_subclasses,
    materialize_generated_input_class,
)
from ..utils.strings import pascal_case
from .base import (
    ArrayFilter,
    GlobalIDFilter,
    GlobalIDMultipleChoiceFilter,
    ListFilter,
    RangeFilter,
    TypedFilter,
)

# Domain-local aliases for the shared generated-input substrate (the mechanics
# are single-sited in ``utils/inputs.py`` per the 0.0.9 DRY pass). Tests and
# ``factories.py`` import these spec-027 Decision 9 names from this module, so
# they stay addressable here.
FieldSpec = GeneratedInputFieldSpec
build_input_class = build_strawberry_input_class
_camel_case = graphql_camel_name
_iter_filterset_subclasses = iter_set_subclasses

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
# Decision 3 Layer 5 / H3 of rev4 feedback. Strawberry's auto-camel-case
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
# onto the form-data keys ``django-filter`` recognizes); ``inputs.py``
# consumes it locally via ``_build_logic_fields`` to emit the
# self-referential ``and_`` / ``or_`` / ``not_`` fields whose GraphQL
# surface names land through ``strawberry.field(name=...)`` because
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
_field_specs: dict[tuple[type[FilterSet], str], FieldSpec] = {}


# Ledger of materialized input class names per spec-027 Decision 9.
# ``materialize_input_class`` writes a ``name -> input_class`` entry;
# ``clear_filter_input_namespace`` walks the snapshot keys to ``delattr``
# the matching module global and reset the ledger. The stored value is
# the materialized input class (NOT the FilterSet) so the clear path can
# call ``delattr`` against the module's global by the same name without
# an extra lookup.
_materialized_names: dict[str, type] = {}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


# Pascal-case helper for input-class names. Delegates the case conversion to
# the shared ``utils.strings.pascal_case`` (single source of truth) and only
# adds the load-bearing no-word-character guard documented below. Mirrors
# ``sets_mixins.py::ClassBasedTypeNameMixin.type_name_for``, which pairs the
# same shared helper with its own sibling guard for the indirect callers; this
# wrapper is the ``RangeFilter``-specific counterpart for the direct caller.
def _pascal_case(name: str) -> str:
    """Return ``name`` converted to ``PascalCase`` via ``utils.strings.pascal_case``.

    Raises ``ConfigurationError`` for inputs that contain no
    word-character tokens (e.g. ``"_"``, ``""``, ``"__"``); the shared
    helper returns ``""`` for such input, which would silently collide on
    the downstream ``RangeInputType`` naming. Raising here surfaces the
    real cause at the call site -- the one behaviour this thin wrapper adds
    on top of ``utils.strings.pascal_case``.

    Direct caller today: ``_build_range_input_class`` only. Indirect
    callers (``_input_type_name_for``, ``_build_input_fields``'s
    operator-bag class naming) route through
    ``sets_mixins.py::ClassBasedTypeNameMixin.type_name_for`` and trip
    its sibling no-word-character guard rather than this one - so the
    error message below names the ``RangeFilter`` consumer specifically.
    """
    pascal = pascal_case(name)
    if not pascal:
        raise ConfigurationError(
            f"_pascal_case received {name!r} which contains no word "
            "characters; rename the RangeFilter's `field_name=` so its "
            "name has at least one alphanumeric token.",
        )
    return pascal


def _input_type_name_for(filterset_class: type[FilterSet]) -> str:
    """Return the canonical Strawberry input-class name for ``filterset_class``.

    Thin delegate to ``FilterSet.type_name_for()`` (the shared
    ``ClassBasedTypeNameMixin``): every ``FilterSet`` subclass ``Foo``
    produces a Strawberry input class named ``FooInputType``. Kept as a
    helper so its callers -- ``filter_input_type`` (``__init__.py``),
    ``FilterArgumentsFactory`` (``factories.py``), and ``_build_input_fields``
    (this module) -- stay pinned to one derivation site even though the
    spec-027 Decision 9 (lines 1023-1030) naming rule now lives on the mixin
    (shared with the future order / aggregate sets).
    """
    return filterset_class.type_name_for()


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
            f"ChoiceFilter on {filter_instance!r} is not backed by a Django "
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


def convert_filter_to_input_annotation(
    filter_instance: Filter,
    model_field: Any,
    owner_definition: DjangoTypeDefinition | None = None,
) -> Any:
    """Return the Strawberry annotation for a resolved ``django-filter`` filter.

    Implements the Decision-4 M1 conversion table. Branch order is
    most-specific to least-specific: the Relay-aware primitives first
    (they subclass ``Filter`` / ``MultipleChoiceFilter`` and would
    otherwise fall through to scalar / list), then the typed-filter
    family (``RangeFilter`` / ``ListFilter`` / ``ArrayFilter``), then
    ``ChoiceFilter``, then the scalar catch-all. ``method=...`` filters
    that do not match any branch raise ``ConfigurationError``.
    """
    required = bool(filter_instance.extra.get("required", False))

    if isinstance(filter_instance, GlobalIDMultipleChoiceFilter):
        annotation = list[str]
    elif isinstance(filter_instance, GlobalIDFilter):
        annotation = str
    elif isinstance(filter_instance, BaseCSVFilter):
        # django-filter expands ``Meta.fields`` ``in`` / ``range`` lookups
        # into ``BaseInFilter`` / ``BaseRangeFilter`` (both ``BaseCSVFilter``
        # subclasses) whose form field consumes a LIST of values, not a
        # scalar. Without this branch they fell through to the scalar
        # catch-all and the generated input was a single value -- the
        # runtime CSV field then mis-parsed a lone scalar as a 1-element
        # list. Our own ``RangeFilter`` primitive (a ``{start, end}`` input)
        # is a separate, non-CSV class handled by the branch below. The element
        # type is model-field-driven so a CSV ``in`` over a choice column keeps
        # its enum and a 64-bit column keeps ``BigInt`` (not ``str`` / ``Int``).
        annotation = list[_element_annotation(filter_instance, model_field, owner_definition)]
    elif isinstance(filter_instance, (RangeFilter, _DjangoRangeFilter)):
        inner = _scalar_from_model_field(model_field)
        annotation = _build_range_input_class(filter_instance, inner)
    elif isinstance(filter_instance, (ListFilter, ArrayFilter)):
        annotation = list[_element_annotation(filter_instance, model_field, owner_definition)]
    elif isinstance(filter_instance, TypedFilter):
        annotation = _element_annotation(filter_instance, model_field, owner_definition)
    elif isinstance(filter_instance, (ChoiceFilter, TypedChoiceFilter)):
        type_name = _owner_type_name(owner_definition) or "Filter"
        annotation = _choice_enum_from_filter(filter_instance, type_name, model_field)
    else:
        # Catch-all scalar branch. ``Filter(method=...)`` filters land
        # here when their ``field_class`` is a recognized form field; an
        # unknown form-field shape raises per spec-027 line 595.
        form_field = getattr(filter_instance, "field", None)
        method = getattr(filter_instance, "method", None)
        if method is not None and form_field is None:
            raise ConfigurationError(
                f"Filter(method={method!r}) on {filter_instance!r} exposes no "
                "form field; declare an explicit `Filter(method=..., field_class=...)` "
                "or wrap the method on a typed filter primitive.",
            )
        if getattr(filter_instance, "lookup_expr", None) == "isnull":
            # ``isnull`` is a boolean predicate regardless of the column type;
            # the model field (the column's value type) is irrelevant here.
            annotation = bool
        else:
            annotation = _element_annotation(filter_instance, model_field, owner_definition)

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

    if isinstance(filter_instance, GlobalIDMultipleChoiceFilter):
        return [_encode_global_id_input(item) for item in raw_value]
    if isinstance(filter_instance, GlobalIDFilter):
        return _encode_global_id_input(raw_value)
    if isinstance(filter_instance, BaseCSVFilter):
        # ``in`` / ``range`` generated CSV filters consume a list; unwrap
        # any enum members per element (parity with ``ListFilter`` below).
        return [_unwrap_enum_member(item) for item in raw_value]
    if isinstance(filter_instance, (RangeFilter, _DjangoRangeFilter)):
        return _normalize_range_value(filter_instance, raw_value, field_name=field_name)
    if isinstance(filter_instance, (ChoiceFilter, TypedChoiceFilter)):
        return _unwrap_enum_member(raw_value)
    if isinstance(filter_instance, (ListFilter, ArrayFilter)):
        return [_unwrap_enum_member(item) for item in raw_value]
    return _unwrap_enum_member(raw_value)


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


def _build_range_input_class(filter_instance: RangeFilter, inner: type) -> type:
    """Return a Strawberry input dataclass with ``start: T | None`` and ``end: T | None``.

    The class is cached on the filter instance so repeated converter
    calls do not produce divergent Strawberry input types. The class
    name derives from the filter's ``field_name`` so introspection-time
    error messages name a meaningful type.
    """
    cached = getattr(filter_instance, "_range_input_cls", None)
    if cached is not None:
        return cached
    field_name = getattr(filter_instance, "field_name", "field") or "field"
    cls_name = f"{_pascal_case(field_name)}RangeInputType"
    cls = build_input_class(
        cls_name,
        [("start", inner | None, {"default": None}), ("end", inner | None, {"default": None})],
    )
    filter_instance._range_input_cls = cls  # type: ignore[attr-defined]
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

    The annotations follow the H2-of-rev4 INSIDE-list shape: the
    ``Annotated[...]`` wraps the forward-reference string directly, and
    the ``list[...]`` (for ``and_`` / ``or_``) wraps the
    ``Annotated[...]`` -- NOT the other way around. The GraphQL surface
    names (``and`` / ``or`` / ``not``) come through
    ``strawberry.field(name=...)`` because the underlying tokens are
    Python keywords and cannot be dataclass field names.
    """
    self_ref = Annotated[type_name, strawberry.lazy(INPUTS_MODULE_PATH)]
    list_ref = list[self_ref]
    return [
        ("and_", list_ref | None, {"name": "and"}),
        ("or_", list_ref | None, {"name": "or"}),
        ("not_", self_ref | None, {"name": "not"}),
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
        if "__" in filter_name:
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
    # (``connection_field.py::_get_trimmed_filterset_class``); because this
    # package emits a single Strawberry input type here, the same
    # ``is_expanded_child`` rule is just a skip in this loop, so the hidden
    # operator-bag classes are never built in the first place.
    hide_flat_filters = bool(getattr(settings, "HIDE_FLAT_FILTERS", False))

    triples: list[tuple[str, Any, dict[str, Any]]] = []
    for top_name, lookup_bag in grouped.items():
        # A flat relational traversal path (``category__name``,
        # ``entries__property__category__name``) is an "expanded child" of a
        # declared ``RelatedFilter`` -- its first path segment names the
        # relation. Such paths are reachable through the nested branch already;
        # hide them when ``HIDE_FLAT_FILTERS`` is set (upstream parity:
        # ``connection_field.py:238-242``).
        if (
            hide_flat_filters
            and "__" in top_name
            and top_name.split("__", 1)[0] in related_filters
        ):
            continue
        python_attr = top_name.replace("__", "_")
        graphql_name = _camel_case(python_attr)
        rel_filter = related_filters.get(top_name)
        if rel_filter is not None:
            target_fs = rel_filter.filterset
            if target_fs is None:
                continue
            target_name = _input_type_name_for(target_fs)
            inner = Annotated[target_name, strawberry.lazy(INPUTS_MODULE_PATH)]
            field_kwargs: dict[str, Any] = {}
            if python_attr != graphql_name:
                field_kwargs["name"] = graphql_name
            triples.append(
                (python_attr, inner | None, field_kwargs),
            )
            _field_specs[(filterset_cls, python_attr)] = FieldSpec(
                python_attr=python_attr,
                graphql_name=graphql_name,
                django_source_path=top_name,
            )
            continue

        # Leaf path: build a per-field operator-bag input class.
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
            )
            leaf_kwargs: dict[str, Any] = {}
            if lookup_python_attr != lookup_graphql_name:
                leaf_kwargs["name"] = lookup_graphql_name
            bag_specs.append(
                (lookup_python_attr, annotation, leaf_kwargs),
            )
        bag_class = build_input_class(bag_name, bag_specs)
        outer_kwargs: dict[str, Any] = {}
        if python_attr != graphql_name:
            outer_kwargs["name"] = graphql_name
        triples.append(
            (python_attr, bag_class | None, outer_kwargs),
        )
        # ``django_source_path`` is the form-key prefix the normalizer emits
        # into ``django-filter`` form data. For autogen filters whose form
        # key derives from the field name (``name`` / ``name__icontains``)
        # we use the filter's ``field_name``. For declared filters whose
        # form key is the explicit class-attribute name (e.g.
        # ``email_must_have_at_sign``) we use ``top_name`` so the
        # downstream form receives the correct key.
        if top_name in getattr(filterset_cls, "declared_filters", {}):
            django_source_path = top_name
        else:
            django_source_path = sample_filter.field_name
        _field_specs[(filterset_cls, python_attr)] = FieldSpec(
            python_attr=python_attr,
            graphql_name=graphql_name,
            django_source_path=django_source_path,
        )
    return triples


def _model_field_for_filter(filterset_cls: type[FilterSet], filter_instance: Filter) -> Any:
    """Resolve the Django model field a filter targets (or ``None``)."""
    from django.core.exceptions import FieldDoesNotExist

    model = getattr(getattr(filterset_cls, "_meta", None), "model", None)
    if model is None:
        return None
    field_name = getattr(filter_instance, "field_name", None)
    if not field_name:
        return None
    # ``field_name`` may carry ``__``-separated relation traversals; walk
    # one ``_meta.get_field`` at a time so the final hop's model field is
    # returned (e.g. ``galaxy__name`` resolves through ``galaxy`` to
    # ``Galaxy.name``).
    parts = field_name.split("__")
    cursor_model = model
    field = None
    for part in parts:
        try:
            field = cursor_model._meta.get_field(part)
        except FieldDoesNotExist:
            # A typo in a declared ``Filter(field_name=...)`` reaches here;
            # the broader ``except Exception`` previously masked unrelated
            # ``_meta.get_field`` failures. ``FieldDoesNotExist`` matches
            # Django's documented contract for unknown names; any other
            # failure now surfaces loudly instead of degrading to ``None``.
            return None
        if (
            getattr(field, "is_relation", False)
            and getattr(field, "related_model", None) is not None
        ):
            cursor_model = field.related_model
    return field


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

    Thin family wrapper over
    ``utils/inputs.py::materialize_generated_input_class`` pinning the
    filter-side module path, family label, and ledger. See that helper for the
    Strawberry ``LazyType.resolve_type`` contract, the ``(name, cls)``
    idempotency clause, and the distinct-class collision raise (spec-027
    Decision 9).
    """
    materialize_generated_input_class(
        name,
        cls,
        module_path=INPUTS_MODULE_PATH,
        family_label="FilterSet",
        ledger=_materialized_names,
    )


def clear_filter_input_namespace() -> None:
    """Reset the filter-input ledger and per-filterset binding state for a fresh build.

    Clears the bookkeeping that prevents stale-state leakage across
    consumer-side autouse-reload fixtures: ``_materialized_names``
    (forces ``materialize_input_class`` to re-emit on the next
    finalize), ``_field_specs`` (per-(filterset, field) provenance for
    the normalizer), the ``FilterArgumentsFactory`` class-level caches
    (``input_object_types`` / ``_type_filterset_registry``), and every
    ``FilterSet`` subclass's phase-2.5 binding state
    (``_owner_definition`` / ``_expanded_filters`` /
    ``_is_expanding_filters``). After the clear, a follow-up
    ``finalize_django_types()`` call rebuilds every input class from
    scratch against the freshly-cleared registry, so a new build's
    converter emits fresh enums without colliding with prior-build
    enums under the same GraphQL type name.

    **Materialized class objects are intentionally left parked in
    ``filters.inputs.__dict__``.** ``materialize_input_class`` already
    overwrites the module global via ``setattr`` on the next finalize
    pass, so the parked class is replaced in place once the rebuild
    runs. Stripping the class via ``delattr`` here would break any
    ``strawberry.lazy(...)`` LazyType held by a consumer module whose
    autouse-reload fixture did NOT also reload the holder
    (e.g., ``test_scalars_api.py``'s per-app fixture, by README
    contract, reloads only its own app's schema - ``apps.library.schema``
    keeps its cached ``filter_input_type(filters.BranchFilter)`` LazyType
    references, which would resolve to ``AttributeError`` if the
    matching module global had been deleted). Leaving the class object
    parked lets the LazyType resolve to the prior class until the next
    finalize replaces it, and the ledger reset still drives the rebuild.

    The helper short-circuits cleanly when the module is not in
    ``sys.modules`` (e.g., a process that imported ``registry`` alone
    and never reached ``filters.inputs``) - the ledger and the
    per-filterset map still get reset so a subsequent import / build
    starts from a clean slate. The factory / FilterSet clears use
    cycle-safe imports so a partial-load environment (factories / sets
    not yet imported) tolerates the call without raising.

    Delegates the lifecycle to
    ``utils/inputs.py::clear_generated_input_namespace``, which reads the
    per-filterset binding attrs from ``FilterSet._lifecycle`` (the
    ``SetLifecycleAttrs`` descriptor: ``_owner_definition`` / ``_expanded_filters``
    / ``_is_expanding_filters``) rather than a re-spelled tuple.
    """
    clear_generated_input_namespace(
        materialized_names=_materialized_names,
        field_specs=_field_specs,
        factory_module="django_strawberry_framework.filters.factories",
        factory_class_name="FilterArgumentsFactory",
        collision_registry_attr="_type_filterset_registry",
        set_module="django_strawberry_framework.filters.sets",
        set_class_name="FilterSet",
    )
