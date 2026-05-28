# ruff: noqa: ERA001
"""Filter input namespace, lookup-name scaffolding, and shape converters.

Generated input classes MUST become real globals of this module because
``strawberry.lazy("django_strawberry_framework.filters.inputs")`` resolves
through ``module.__dict__`` (spec-021 Decision 9). Slice 1 landed the
constants (``LOOKUP_PREFIXES`` / ``LOOKUP_NAME_MAP`` / ``FieldSpec`` /
``_field_specs`` / ``_materialized_names``); Slice 2 adds the
filter-instance -> Strawberry-annotation converter pair
(``convert_filter_to_input_annotation`` /
``normalize_input_value``), the dataclass builder
(``build_input_class``), and the per-filterset operator-bag helpers
(``_build_input_fields`` / ``_build_logic_fields`` /
``construct_search``). Slice 3 lands ``materialize_input_class`` and
``clear_filter_input_namespace`` on top.
"""

from __future__ import annotations

import datetime
import decimal
import uuid
from collections import OrderedDict
from dataclasses import dataclass
from typing import TYPE_CHECKING, Annotated, Any

import strawberry
from django.db import models
from django_filters import ChoiceFilter, Filter, TypedChoiceFilter
from django_filters import RangeFilter as _DjangoRangeFilter
from strawberry import UNSET, relay

from ..exceptions import ConfigurationError
from .base import (
    ArrayFilter,
    GlobalIDFilter,
    GlobalIDMultipleChoiceFilter,
    ListFilter,
    RangeFilter,
    TypedFilter,
)

if TYPE_CHECKING:  # pragma: no cover - type-checking-only imports.
    from ..types.definition import DjangoTypeDefinition
    from .sets import FilterSet


# Module path the ``strawberry.lazy(...)`` marker references; pinned as a
# single constant so the factory, ``_build_logic_fields``, and
# ``filter_input_type`` (in ``__init__.py``) all stay in sync.
INPUTS_MODULE_PATH: str = "django_strawberry_framework.filters.inputs"


# Search-prefix vocabulary for the future `Meta.search_fields` card per
# spec-021 Decision 3 Layer 5; consumed by `construct_search` below.
LOOKUP_PREFIXES: dict[str, str] = {
    "^": "istartswith",
    "=": "iexact",
    "@": "search",
    "$": "iregex",
}


# `django-filter` lookup -> (python_attr, graphql_name) pair per spec-021
# Decision 3 Layer 5 / H3 of rev4 feedback. Strawberry's auto-camel-case
# cannot transform `icontains` to `iContains` (no underscore to split on),
# and the Python keyword `in` cannot be a dataclass field — both are pinned
# here. Slice 1 consumes this map via `FilterSet._normalize_input` to map
# Strawberry-input dataclass attrs back to `django-filter`'s form-data keys;
# Slice 2 consumes it via `_build_input_fields` (for
# `strawberry.field(name=...)` emission) and `normalize_input_value` (for
# the runtime symmetric).
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
_LOGIC_KEYS: tuple[tuple[str, str], ...] = (
    ("and_", "and"),
    ("or_", "or"),
    ("not_", "not"),
)


@dataclass(frozen=True)
class FieldSpec:
    """Per-generated-input-field metadata.

    Carries the three names ``normalize_input_value`` and (Slice 3's)
    ``materialize_input_class`` need to map between the Strawberry input
    dataclass field, the GraphQL wire-format name, and the
    `django-filter` lookup path on the Django ORM (per spec-021 M5 of
    rev8).
    """

    python_attr: str
    graphql_name: str
    django_source_path: str


# Provenance table populated by ``_build_input_fields`` and consulted at
# runtime by ``FilterSet._normalize_input`` and ``normalize_input_value``.
_field_specs: dict[tuple[type[FilterSet], str], FieldSpec] = {}


# Ledger of materialized input class names per spec-021 Decision 9.
# Slice 3's ``materialize_input_class`` writes a ``name -> input_class``
# entry; ``clear_filter_input_namespace`` walks the snapshot keys to
# ``delattr`` the matching module global and reset the ledger. The
# stored value is the materialized input class (NOT the FilterSet) so
# the clear path can call ``delattr`` against the module's global by
# the same name without an extra lookup.
_materialized_names: dict[str, type] = {}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


# Pascal-case helper for input-class names. The cookbook uses
# ``stringcase.pascalcase``; the package has no ``stringcase`` dependency
# so a local one-liner suffices: ``galaxy__name`` -> ``GalaxyName``.
def _pascal_case(name: str) -> str:
    """Return ``name`` converted to ``PascalCase`` (treats ``_`` as a separator).

    Raises ``ConfigurationError`` for inputs that contain no
    word-character tokens (e.g. ``"_"``, ``""``, ``"__"``); the result
    would otherwise be an empty string and silently collide on the
    downstream ``f"{bag_name}{...}FilterInputType"`` naming, producing
    a generic ``"FilterInputType"`` that the BFS factory's collision
    check would then flag indirectly. Raising here surfaces the real
    cause at the call site.
    """
    parts = [part.capitalize() for part in name.replace("__", "_").split("_") if part]
    if not parts:
        raise ConfigurationError(
            f"_pascal_case received {name!r} which contains no word "
            "characters; rename the filter / field so its name has at "
            "least one alphanumeric token.",
        )
    return "".join(parts)


def _input_type_name_for(filterset_class: type[FilterSet]) -> str:
    """Return the canonical Strawberry input-class name for ``filterset_class``.

    Single source of truth for the spec-021 Decision 9 (lines 1023-1030)
    class-derived naming convention: every ``FilterSet`` subclass ``Foo``
    produces a Strawberry input class named ``FooInputType``. Consumed by
    ``filter_input_type`` (``__init__.py``), ``FilterArgumentsFactory``
    (``factories.py``), and ``_build_input_fields`` (this module) so the
    five derivation sites stay pinned to one helper.
    """
    return f"{filterset_class.__name__}InputType"


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
    if isinstance(form_field, forms.IntegerField):
        # ``DecimalField`` and ``FloatField`` subclass ``IntegerField`` -- no.
        # ``DecimalField`` extends ``IntegerField`` via ``Field`` only; the
        # explicit checks below catch them first.
        return int
    if isinstance(form_field, forms.FloatField):
        return float
    if isinstance(form_field, forms.DecimalField):
        return decimal.Decimal
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
    # table at spec-021 Decision 4 M1 lists CharField as a recognized
    # shape, and a future reader who inspects this function should see
    # that the mapping is intentional, not an accidental fallthrough.
    if isinstance(form_field, forms.CharField):
        return str
    return str


def _scalar_from_model_field(model_field: Any) -> type:
    """Map a Django model field to a Python scalar via ``to_python``.

    Falls back to the model field's form-field shape when ``model_field``
    is ``None`` (e.g., a custom-method filter without a backing field).
    """
    if model_field is None:
        return str
    # Mirror ``types.converters.SCALAR_MAP`` for the common cases. We do
    # NOT import ``SCALAR_MAP`` here because ``inputs.py`` is a leaf
    # module and ``converters.py`` already has heavy imports; replicating
    # the small subset of mappings the filter-input converter needs is
    # cheaper than carrying the cycle risk.
    if isinstance(model_field, models.BooleanField):
        return bool
    if isinstance(
        model_field,
        (
            models.AutoField,
            models.IntegerField,
            models.BigAutoField,
            models.SmallAutoField,
            models.BigIntegerField,
            models.SmallIntegerField,
            models.PositiveIntegerField,
            models.PositiveSmallIntegerField,
            models.PositiveBigIntegerField,
        ),
    ):
        return int
    if isinstance(model_field, models.FloatField):
        return float
    if isinstance(model_field, models.DecimalField):
        return decimal.Decimal
    if isinstance(model_field, models.DateTimeField):
        return datetime.datetime
    if isinstance(model_field, models.DateField):
        return datetime.date
    if isinstance(model_field, models.TimeField):
        return datetime.time
    if isinstance(model_field, models.UUIDField):
        return uuid.UUID
    return str


def _choice_enum_from_filter(
    filter_instance: ChoiceFilter,
    type_name: str,
    model_field: Any,
) -> Any:
    """Derive a Strawberry enum from a ``ChoiceFilter``'s underlying choice source.

    Per spec-021 Decision 4 M5 (line 591), a ``ChoiceFilter`` whose source
    is not a Django ``Choices``-derived enum raises ``ConfigurationError``
    (the consumer is expected to wrap the choices through the existing
    converter pipeline). When the underlying model field is available
    the pipeline at ``types.converters.convert_choices_to_enum`` is
    consulted so the GraphQL enum is shared with any sibling
    ``DjangoType`` reading the same column.

    ``model_field`` is threaded as a parameter rather than stashed on
    the filter instance — keeps the filter stateless and avoids the
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
    elif isinstance(filter_instance, (RangeFilter, _DjangoRangeFilter)):
        inner = _scalar_from_model_field(model_field)
        annotation = _build_range_input_class(filter_instance, inner)
    elif isinstance(filter_instance, (ListFilter, ArrayFilter)):
        annotation = list[_scalar_from_model_field(model_field)]
    elif isinstance(filter_instance, TypedFilter):
        annotation = _scalar_from_model_field(model_field)
    elif isinstance(filter_instance, (ChoiceFilter, TypedChoiceFilter)):
        type_name = _owner_type_name(owner_definition) or "Filter"
        annotation = _choice_enum_from_filter(filter_instance, type_name, model_field)
    else:
        # Catch-all scalar branch. ``Filter(method=...)`` filters land
        # here when their ``field_class`` is a recognized form field; an
        # unknown form-field shape raises per spec-021 line 595.
        form_field = getattr(filter_instance, "field", None)
        method = getattr(filter_instance, "method", None)
        if method is not None and form_field is None:
            raise ConfigurationError(
                f"Filter(method={method!r}) on {filter_instance!r} exposes no "
                "form field; declare an explicit `Filter(method=..., field_class=...)` "
                "or wrap the method on a typed filter primitive.",
            )
        annotation = (
            _scalar_from_form_field(form_field)
            if form_field is not None
            else _scalar_from_model_field(
                model_field,
            )
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

    - a scalar value (``str`` / ``int`` / decoded ``node_id`` / enum
      ``.value``) when the filter consumes a single form-data key;
    - a ``list`` (for ``GlobalIDMultipleChoiceFilter`` / ``ListFilter`` /
      ``ArrayFilter``) when ``django-filter`` consumes a list;
    - a ``dict[str, Any]`` patch the caller merges into the form-data
      dict when the filter consumes more than one positional form-data
      key (``RangeFilter`` -> ``{<field>_0, <field>_1}``).

    Per the Implementation discretion item (Slice 2 plan step 2), the
    multi-key return shape lets the ``_normalize_input`` caller merge
    the patch without inventing a sentinel-pair object.
    """
    # Defensive short-circuit against ``strawberry.UNSET`` reaching the
    # branches below: every branch indexes / iterates / coerces
    # ``raw_value`` and would either raise ``TypeError`` (UNSET is not
    # iterable) or silently pass the UNSET sentinel into ``data``. Every
    # caller MUST treat UNSET as "not supplied" — same as ``None`` — so
    # this entry point is the single defensive line every future caller
    # benefits from.
    if raw_value is None or raw_value is UNSET:
        return None

    if isinstance(filter_instance, GlobalIDMultipleChoiceFilter):
        return [_decode_global_id(item) for item in raw_value]
    if isinstance(filter_instance, GlobalIDFilter):
        return _decode_global_id(raw_value)
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


def _decode_global_id(value: Any) -> Any:
    """Return the underlying ``node_id`` for a ``relay.GlobalID``-or-string."""
    if isinstance(value, relay.GlobalID):
        return value.node_id
    return value


def _unwrap_enum_member(value: Any) -> Any:
    """Return ``value.value`` for a Strawberry-enum member; passthrough otherwise."""
    member_value = getattr(value, "value", None)
    if member_value is not None and hasattr(value, "name"):
        # Strawberry-enum members have both ``.name`` and ``.value``; the
        # ``hasattr`` check distinguishes them from plain wrapper objects
        # that happen to expose ``.value`` (e.g. ``decimal.Decimal``).
        return member_value
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
        [
            ("start", inner | None, {"default": None}),
            ("end", inner | None, {"default": None}),
        ],
    )
    filter_instance._range_input_cls = cls  # type: ignore[attr-defined]
    return cls


def _normalize_range_value(
    filter_instance: RangeFilter,
    raw_value: Any,
    field_name: str | None = None,
) -> dict[str, Any]:
    """Return the positional form-data patch ``{<name>_0, <name>_1}`` for a RangeFilter.

    Per spec-021 Decision 4 line 594: Django's ``RangeWidget.value_from_datadict``
    reads positional keys ``name_0`` / ``name_1`` (NOT named ``_from`` /
    ``_to`` keys). The patch's key prefix is the form-data field name
    (``filter_instance.field_name`` for direct filters; the caller may
    override via ``field_name`` for the dataclass-attribute case where
    the Strawberry attr differs from the django-filter form-key).
    """
    base = field_name or filter_instance.field_name or "range"
    start = getattr(raw_value, "start", None) if not isinstance(raw_value, dict) else raw_value.get("start")
    end = getattr(raw_value, "end", None) if not isinstance(raw_value, dict) else raw_value.get("end")
    return {f"{base}_0": start, f"{base}_1": end}


def _owner_type_name(owner_definition: DjangoTypeDefinition | None) -> str | None:
    """Return the GraphQL type name for ``owner_definition`` (or ``None``).

    Delegates to ``DjangoTypeDefinition.graphql_type_name`` so the three
    callers (this helper, ``filters/base.py::_expected_global_id_type_name``,
    ``types/finalizer.py::_bind_filterset_owner``) share one derivation
    rule and cannot drift across renames.
    """
    return owner_definition.graphql_type_name if owner_definition is not None else None


# ---------------------------------------------------------------------------
# Input class construction
# ---------------------------------------------------------------------------


def build_input_class(
    name: str,
    field_specs: list[tuple[str, Any, dict[str, Any] | None]],
) -> type:
    """Construct a ``@strawberry.input``-decorated dataclass.

    ``field_specs`` is a list of ``(python_attr, annotation, field_kwargs)``
    triples. ``field_kwargs`` may carry ``name=`` for the GraphQL alias,
    ``default=`` for the dataclass default (defaults to ``None``), and
    ``description=`` for the Strawberry field description.

    The class is constructed via ``type(name, (), namespace)`` rather
    than ``dataclasses.make_dataclass`` because ``make_dataclass``
    replaces any ``strawberry.field(...)`` default with a plain
    ``dataclasses.Field`` and strips the strawberry-specific metadata
    (the ``name=`` alias would be lost). Setting the ``strawberry.field``
    as a class-level attribute alongside ``__annotations__`` preserves
    the metadata through the ``@strawberry.input`` decoration.
    """
    namespace: dict[str, Any] = {"__annotations__": {}}
    for python_attr, annotation, raw_kwargs in field_specs:
        kwargs = dict(raw_kwargs or {})
        default = kwargs.pop("default", None)
        strawberry_field_kwargs: dict[str, Any] = {}
        if "name" in kwargs:
            strawberry_field_kwargs["name"] = kwargs.pop("name")
        if "description" in kwargs:
            strawberry_field_kwargs["description"] = kwargs.pop("description")
        namespace["__annotations__"][python_attr] = annotation
        if strawberry_field_kwargs:
            namespace[python_attr] = strawberry.field(default=default, **strawberry_field_kwargs)
        else:
            namespace[python_attr] = default
    cls = type(name, (), namespace)
    return strawberry.input(cls)


# ---------------------------------------------------------------------------
# Logical-operator + input-field builders
# ---------------------------------------------------------------------------


def _build_logic_fields(
    type_name: str,
) -> list[tuple[str, Any, dict[str, Any]]]:
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

    triples: list[tuple[str, Any, dict[str, Any]]] = []
    for top_name, lookup_bag in grouped.items():
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
            triples.append((python_attr, inner | None, field_kwargs))
            _field_specs[(filterset_cls, python_attr)] = FieldSpec(
                python_attr=python_attr,
                graphql_name=graphql_name,
                django_source_path=top_name,
            )
            continue

        # Leaf path: build a per-field operator-bag input class.
        sample_filter = next(iter(lookup_bag.values()))
        bag_name = f"{filterset_cls.__name__}{_pascal_case(python_attr)}FilterInputType"
        bag_specs: list[tuple[str, Any, dict[str, Any]]] = []
        for lookup, leaf_filter in lookup_bag.items():
            lookup_python_attr, lookup_graphql_name = LOOKUP_NAME_MAP.get(lookup, (lookup, lookup))
            model_field = _model_field_for_filter(filterset_cls, leaf_filter)
            annotation = convert_filter_to_input_annotation(leaf_filter, model_field, owner_definition)
            leaf_kwargs: dict[str, Any] = {}
            if lookup_python_attr != lookup_graphql_name:
                leaf_kwargs["name"] = lookup_graphql_name
            bag_specs.append((lookup_python_attr, annotation, leaf_kwargs))
        bag_class = build_input_class(bag_name, bag_specs)
        outer_kwargs: dict[str, Any] = {}
        if python_attr != graphql_name:
            outer_kwargs["name"] = graphql_name
        triples.append((python_attr, bag_class | None, outer_kwargs))
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


def _camel_case(name: str) -> str:
    """Lowercase the head, then ``PascalCase`` the rest (``galaxy_name`` -> ``galaxyName``)."""
    parts = [part for part in name.split("_") if part]
    if not parts:
        return name
    head, *rest = parts
    return head + "".join(part.capitalize() for part in rest)


def _model_field_for_filter(filterset_cls: type[FilterSet], filter_instance: Filter) -> Any:
    """Resolve the Django model field a filter targets (or ``None``)."""
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
        except Exception:  # pragma: no cover - defensive: bad lookup path
            return None
        if getattr(field, "is_relation", False) and getattr(field, "related_model", None) is not None:
            cursor_model = field.related_model
    return field


def construct_search(all_filters: dict[str, Any]) -> dict[str, str]:
    """Translate ``LOOKUP_PREFIXES``-vocabulary keys into a ``{name: lookup}`` map.

    Spec sub-bullet 4 for Slice 2 lands the helper now even though the
    ``Meta.search_fields`` card is ``0.1.2`` -- the prefix vocabulary
    constant ``LOOKUP_PREFIXES`` would otherwise be dead code. Slice 2's
    tests exercise the prefix translation directly.
    """
    result: dict[str, str] = {}
    for filter_name in all_filters:
        prefix = filter_name[:1]
        if prefix in LOOKUP_PREFIXES:
            result[filter_name[1:]] = LOOKUP_PREFIXES[prefix]
    return result


# ---------------------------------------------------------------------------
# Module-global materialization (spec-021 Decision 9)
# ---------------------------------------------------------------------------


def materialize_input_class(name: str, cls: type) -> None:
    """Set ``cls`` as a real module global of ``filters.inputs`` under ``name``.

    Strawberry's ``LazyType.resolve_type`` reads
    ``sys.modules[<module>].__dict__[name]`` to materialize an
    ``Annotated[<name>, strawberry.lazy(<module>)]`` reference; this
    helper is the single entry point that pins ``cls`` at the matching
    ``__dict__`` slot per spec-021 Decision 9.

    Idempotent on the ``(name, cls)`` pair: re-materializing the same
    class under the same name is a no-op (Decision 9 lifecycle clause —
    supports partial-finalize recovery without a sentinel pass). A
    collision against a different class under the same ``name`` raises
    ``ConfigurationError`` naming both qualified class names so the
    consumer sees the offending pair instead of a cryptic schema-build
    error.
    """
    import sys

    existing = _materialized_names.get(name)
    if existing is cls:
        return
    if existing is not None:
        raise ConfigurationError(
            f"{name!r} is materialized by two distinct FilterSet input classes: "
            f"{existing.__module__}.{existing.__qualname__} vs "
            f"{cls.__module__}.{cls.__qualname__}. Rename one filterset so its "
            "class-derived input type name is unique.",
        )
    module = sys.modules[INPUTS_MODULE_PATH]
    setattr(module, name, cls)
    _materialized_names[name] = cls


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
    contract, reloads only its own app's schema — ``apps.library.schema``
    keeps its cached ``filter_input_type(filters.BranchFilter)`` LazyType
    references, which would resolve to ``AttributeError`` if the
    matching module global had been deleted). Leaving the class object
    parked lets the LazyType resolve to the prior class until the next
    finalize replaces it, and the ledger reset still drives the rebuild.

    The helper short-circuits cleanly when the module is not in
    ``sys.modules`` (e.g., a process that imported ``registry`` alone
    and never reached ``filters.inputs``) — the ledger and the
    per-filterset map still get reset so a subsequent import / build
    starts from a clean slate. The factory / FilterSet clears use
    local imports so a partial-load environment (factories / sets not
    yet imported) tolerates the call without raising.
    """
    _materialized_names.clear()
    _field_specs.clear()

    # FilterArgumentsFactory's class-level caches hold the built input
    # classes; stale entries here cause `_ensure_built` to skip rebuild
    # and surface prior-build input classes (with prior-build enum
    # annotations) against a freshly-cleared registry.
    try:
        from .factories import FilterArgumentsFactory
    except ImportError:
        pass
    else:
        FilterArgumentsFactory.input_object_types.clear()
        FilterArgumentsFactory._type_filterset_registry.clear()

    # Every FilterSet subclass carries the phase-2.5 binding state at
    # the class level; that state survives a `registry.clear()` and
    # would otherwise force `_bind_filterset_owner` down the multi-owner
    # strict-equality branch on the next finalize even though the
    # caller intended a clean rebuild.
    try:
        from .sets import FilterSet
    except ImportError:
        return
    for subclass in _iter_filterset_subclasses(FilterSet):
        # `delattr` on the subclass so an inherited default (the
        # `FilterSet` base's `_owner_definition = None`) is restored
        # rather than masked. Each attribute is removed only when set
        # directly on the subclass (``in subclass.__dict__``) so a
        # subclass that never had a binding tolerates the clear.
        for attr in ("_owner_definition", "_expanded_filters", "_is_expanding_filters"):
            if attr in subclass.__dict__:
                delattr(subclass, attr)


def _iter_filterset_subclasses(root: type) -> list[type]:
    """Return every concrete subclass of ``root`` (depth-first, dedup by identity).

    Uses ``type.__subclasses__()`` which only yields LIVE subclasses;
    garbage-collected definitions silently drop. That is the correct
    contract for a test-isolation clear — a definition that has
    already been collected has no state to reset. However: long-running
    test runners that keep filterset references through fixture
    lifetimes accumulate filtersets across tests; each carries
    ``_expanded_filters`` / ``base_filters`` on ``__dict__``. If
    integration suites ever run thousands of fixture-based filtersets,
    profile this walk and consider weak-referencing the helper-tracked
    set instead of relying on ``__subclasses__()`` traversal.
    """
    seen: set[type] = set()
    result: list[type] = []
    stack: list[type] = list(root.__subclasses__())
    while stack:
        cls = stack.pop()
        if cls in seen:
            continue
        seen.add(cls)
        result.append(cls)
        stack.extend(cls.__subclasses__())
    return result
