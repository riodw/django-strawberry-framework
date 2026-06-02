# ruff: noqa: ERA001
"""Order input namespace, direction enum, and input-data adapters.

Generated order input classes MUST become real globals of this module
because ``strawberry.lazy("django_strawberry_framework.orders.inputs")``
resolves through ``module.__dict__`` (spec-028 Decision 9). This module
pairs the constant (``INPUTS_MODULE_PATH``) and the public direction enum
(``Ordering``) with the module-global materialization /
ledger pair (``materialize_input_class`` / ``_materialized_names``), the
Slice 2 input-data adapters (``_build_input_fields`` /
``convert_order_field_to_input_annotation`` / ``normalize_input_value`` /
``build_input_class``), the ``Meta.fields = "__all__"`` helper
(``_get_concrete_field_names_for_order``), the per-(orderset, attr)
provenance ledger (``_field_specs``), and the namespace-clear pair
(``clear_order_input_namespace`` / ``_iter_orderset_subclasses``).

Slice 3 wires ``registry.clear()`` to call ``clear_order_input_namespace``
plus the separate ``_helper_referenced_ordersets.clear()`` block per
spec-028 Decision 9 line 775.
"""

from __future__ import annotations

import enum
import sys
from collections import OrderedDict
from dataclasses import dataclass
from typing import TYPE_CHECKING, Annotated, Any

import strawberry
from django.db.models import F
from django.db.models.expressions import OrderBy

from ..exceptions import ConfigurationError

if TYPE_CHECKING:  # pragma: no cover - type-checking-only imports.
    from ..types.definition import DjangoTypeDefinition
    from .sets import OrderSet


# Module path the ``strawberry.lazy(...)`` marker references; pinned as a
# single constant so the factory, every per-resolver
# ``Annotated[..., strawberry.lazy(...)]`` reference, and
# ``materialize_input_class`` all stay in sync. Mirrors
# ``django_strawberry_framework/filters/inputs.py::INPUTS_MODULE_PATH``.
INPUTS_MODULE_PATH: str = "django_strawberry_framework.orders.inputs"


@strawberry.enum
class Ordering(enum.Enum):
    """Direction enum for ordering leaves per spec-028 Decision 5.

    Members map one-to-one to Django ``OrderBy`` expressions via
    ``resolve(value)``. ``NULLS_FIRST`` / ``NULLS_LAST`` variants set the
    matching Django sentinel kwarg to ``True``; the bare ``ASC`` / ``DESC``
    members set BOTH ``nulls_first`` and ``nulls_last`` to ``None`` so the
    database's default null-ordering applies (per spec-028 Decision 5's
    True-or-None semantics).
    """

    ASC = "ASC"
    DESC = "DESC"
    ASC_NULLS_FIRST = "ASC_NULLS_FIRST"
    ASC_NULLS_LAST = "ASC_NULLS_LAST"
    DESC_NULLS_FIRST = "DESC_NULLS_FIRST"
    DESC_NULLS_LAST = "DESC_NULLS_LAST"

    def resolve(self, value: str) -> OrderBy:
        """Translate this direction into a Django ``OrderBy`` expression.

        ``value`` is the ORM field path (e.g. ``"title"`` or
        ``"shelf__code"``). The result is ``F(value).asc(...)`` or
        ``F(value).desc(...)`` with ``nulls_first`` / ``nulls_last``
        sentinels derived from the enum member's name. The
        ``True``-or-``None`` ternary matches Django's sentinel semantics:
        passing ``None`` lets the database choose, while ``True`` forces
        the corresponding clause.
        """
        nulls_first = True if "NULLS_FIRST" in self.name else None
        nulls_last = True if "NULLS_LAST" in self.name else None
        if "ASC" in self.name:
            return F(value).asc(nulls_first=nulls_first, nulls_last=nulls_last)
        return F(value).desc(nulls_first=nulls_first, nulls_last=nulls_last)


@dataclass(frozen=True)
class FieldSpec:
    """Per-generated-input-field metadata.

    Carries the three names ``normalize_input_value`` and
    ``materialize_input_class`` need to map between the Strawberry input
    dataclass field, the GraphQL wire-format name, and the ORM lookup
    path on the Django model (mirrors
    ``django_strawberry_framework/filters/inputs.py::FieldSpec``).
    """

    python_attr: str
    graphql_name: str
    django_source_path: str


# Provenance table populated by ``_build_input_fields`` and consulted at
# runtime by ``normalize_input_value`` (and indirectly by
# ``OrderSet._active_permission_field_paths``). Keyed by
# ``(OrderSet subclass, python_attr)``; emptied by
# ``clear_order_input_namespace``.
_field_specs: dict[tuple[type[OrderSet], str], FieldSpec] = {}


# Ledger of materialized input class names per spec-028 Decision 9.
# ``materialize_input_class`` writes a ``name -> input_class`` entry;
# Slice 3's ``registry.clear()`` will route through
# ``clear_order_input_namespace`` to reset the ledger (module globals
# stay parked per the parked-globals lifecycle). The stored value is the
# materialized input class (NOT the source ``OrderSet``) so the clear
# path can call ``delattr`` against the module's global by the same name
# without an extra lookup. Mirrors
# ``django_strawberry_framework/filters/inputs.py::_materialized_names``
# but lives in a disjoint per-subsystem namespace per spec-028 Decision 9.
_materialized_names: dict[str, type] = {}


def _input_type_name_for(orderset_class: type) -> str:
    """Return the canonical Strawberry input-class name for ``orderset_class``.

    Thin delegate to ``OrderSet.type_name_for()`` (the shared
    ``ClassBasedTypeNameMixin``): every ``OrderSet`` subclass ``Foo``
    produces a Strawberry input class named ``FooInputType``. Kept as a
    helper so its callers -- ``OrderArgumentsFactory`` and
    ``order_input_type`` -- stay pinned to one derivation site.

    Annotated as ``type`` rather than ``type[OrderSet]`` to avoid the
    circular import here (the mixin guarantees ``type_name_for`` is in
    the MRO at runtime).
    """
    return orderset_class.type_name_for()


def _get_concrete_field_names_for_order(model: Any) -> list[str]:
    """Return every column-backed field name for ``model``.

    Backs ``OrderSet._expand_meta_fields`` when ``Meta.fields = "__all__"``
    per spec-028 Decision 3 line 452 + spec-028 Revision 4 B4. The
    cookbook's ``get_concrete_field_names`` at
    ``django_graphene_filters/mixins.py`` uses ``hasattr(f, "column")``
    alone, but empirically against Django 6.0.5 ``ManyToManyField``
    exposes ``.column = None`` so ``hasattr`` returns ``True`` -- the M2M
    field would slip in. The extra ``not f.many_to_many`` clause is a
    deliberate divergence from the cookbook's empirical code that aligns
    with the cookbook's documented intent ("excludes reverse relations,
    many-to-many managers, and other virtual fields").

    Returned list includes forward ``ForeignKey`` / ``OneToOneField``
    columns (their ``<field>_id`` column is on the model's own table)
    and excludes reverse FKs (no ``column`` attribute) and M2M managers.
    """
    return [
        f.name
        for f in model._meta.get_fields()
        if hasattr(f, "column") and not getattr(f, "many_to_many", False)
    ]


def _camel_case(name: str) -> str:
    """Lowercase the head, then ``PascalCase`` the rest (``shelf_code`` -> ``shelfCode``)."""
    parts = [part for part in name.split("_") if part]
    if not parts:
        return name
    head, *rest = parts
    return head + "".join(part.capitalize() for part in rest)


def convert_order_field_to_input_annotation(
    model_field: Any,
    owner_definition: DjangoTypeDefinition | None = None,
) -> Any:
    """Return the Strawberry annotation for an order leaf field.

    Per spec-028 Decision 5: the ordering converter always returns
    ``Ordering | None`` regardless of the underlying model field type
    -- the only legal input value for a leaf is a direction, NOT the
    field's value, so the converter does not differentiate scalar /
    choice / FK / PK / ``BigIntegerField`` columns.

    The ``model_field`` and ``owner_definition`` arguments are unused at
    the body level today; they are kept in the signature for
    forward-compatibility (Spec Decision 12 -- a future DISTINCT ON
    extension or per-type direction enum in ``0.0.9`` would consult
    them) and for shape-symmetry with
    ``filters/inputs.py::convert_filter_to_input_annotation``.
    """
    del model_field, owner_definition  # reserved for future-extension (see docstring).
    return Ordering | None


def build_input_class(name: str, field_specs: list[tuple[str, Any, dict[str, Any] | None]]) -> type:
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
    the metadata through the ``@strawberry.input`` decoration. Direct
    port of ``filters/inputs.py::build_input_class`` -- same shape, no
    order-specific divergence justified.
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


def _build_input_fields(
    orderset_cls: type[OrderSet],
    owner_definition: DjangoTypeDefinition | None = None,
) -> list[tuple[str, Any, dict[str, Any]]]:
    """Return per-field input triples for an orderset's GraphQL input.

    Walks ``orderset_cls.get_fields()`` (Layer-4 expansion). Each entry
    is either a ``RelatedOrder`` instance (related branch) or ``None``
    (leaf). For each entry emit one triple:

    - ``RelatedOrder`` -> forward-reference ``Annotated[...,
      strawberry.lazy(INPUTS_MODULE_PATH)] | None`` keyed on the target
      orderset's class-derived input type name.
    - leaf -> ``Ordering | None`` (Spec Decision 5).

    Populates ``_field_specs`` so the runtime ``normalize_input_value``
    walker can reconstruct the ORM path from each Strawberry input
    dataclass attribute. The ``shelf__code`` flat-shorthand path (per
    Spec Edge cases line 980) maps python attr ``shelf_code`` ->
    GraphQL alias ``shelfCode`` -> django source path ``shelf__code``.

    Mirror of ``filters/inputs.py::_build_input_fields`` with three
    deliberate simplifications: no per-field operator-bag class build
    (every leaf is ``Ordering | None``), no ``_build_logic_fields`` call
    (no ``and_`` / ``or_`` / ``not_`` operator bag on the order side),
    no ``HIDE_FLAT_FILTERS`` skip (the order side does not expose flat
    ``*__lookup`` paths through ``django-filter`` expansion).
    """
    del owner_definition  # reserved -- see ``convert_order_field_to_input_annotation``.
    all_fields = orderset_cls.get_fields()
    triples: list[tuple[str, Any, dict[str, Any]]] = []
    for top_name, related_or_none in all_fields.items():
        python_attr = top_name.replace("__", "_")
        graphql_name = _camel_case(python_attr)
        field_kwargs: dict[str, Any] = {}
        if python_attr != graphql_name:
            field_kwargs["name"] = graphql_name
        if related_or_none is not None:
            target_os = related_or_none.orderset
            if target_os is None:
                # ``RelatedOrder(None, ...)`` placeholder -- skip silently
                # (cookbook lines 124-130).
                continue
            target_name = _input_type_name_for(target_os)
            inner = Annotated[target_name, strawberry.lazy(INPUTS_MODULE_PATH)]
            triples.append((python_attr, inner | None, field_kwargs))
            _field_specs[(orderset_cls, python_attr)] = FieldSpec(
                python_attr=python_attr,
                graphql_name=graphql_name,
                django_source_path=related_or_none.field_name or top_name,
            )
        else:
            # Leaf field: ``Ordering | None`` regardless of model-field
            # type per Spec Decision 5. ``model_field`` discovery is a
            # future-extension affordance the converter ignores today.
            annotation = convert_order_field_to_input_annotation(None, None)
            triples.append((python_attr, annotation, field_kwargs))
            _field_specs[(orderset_cls, python_attr)] = FieldSpec(
                python_attr=python_attr,
                graphql_name=graphql_name,
                django_source_path=top_name,
            )
    return triples


def normalize_input_value(
    orderset_cls: type[OrderSet],
    input_value: Any,
) -> list[tuple[str, Ordering | None]]:
    """Flatten a Strawberry order input value into ``(field_path, direction)`` tuples.

    The function consumes the Strawberry input dataclass (post-
    deserialization, post-Strawberry-type-coercion) and produces a flat
    ``[(field_path, Ordering | None), ...]`` list. ``None`` directions
    are preserved -- the apply pipeline filters them in its
    ``direction.resolve(...)`` comprehension. Per Spec Decision 13:

    - top-level ``list[<T>OrderInputType] | None`` -> recurse on each
      element and concatenate.
    - per-element ``<T>OrderInputType`` -> walk the dataclass's fields
      via the ``_field_specs`` map; ``None`` attribute values short-
      circuit (active-input-only scope per Spec Decision 8 step 6).
    - ``RelatedOrder`` branch -> recurse into the child orderset with
      the django source path as a prefix (e.g. ``shelf`` ->
      ``shelf__code``).

    Mirror of ``filters/inputs.py::normalize_input_value`` with the
    operator-bag layer removed (no ``GlobalIDFilter`` /
    ``BaseCSVFilter`` / ``RangeFilter`` / ``ChoiceFilter`` /
    ``ListFilter`` branches -- ordering has no leaf-shape divergence
    per Spec Decision 5).
    """
    if input_value is None:
        return []
    if isinstance(input_value, list):
        result: list[tuple[str, Ordering | None]] = []
        for element in input_value:
            result.extend(normalize_input_value(orderset_cls, element))
        return result
    # Single dataclass element. Walk its fields against the orderset's
    # ``_field_specs`` map.
    related_orders = getattr(orderset_cls, "related_orders", OrderedDict())
    dataclass_fields = getattr(input_value, "__dataclass_fields__", None)
    if dataclass_fields is None:
        return []
    result = []
    for python_attr in dataclass_fields:
        value = getattr(input_value, python_attr, None)
        if value is None:
            continue
        spec = _field_specs.get((orderset_cls, python_attr))
        if spec is None:
            continue  # Defensive -- should be impossible after a finalize.
        # ``RelatedOrder`` branches recurse into the target orderset.
        # The python-attr <-> related-orders key match uses ``top_name``
        # rules: ``RelatedOrder`` keys never contain ``__`` (their python
        # attr equals the top name), so a plain ``in`` check suffices.
        if python_attr in related_orders:
            child_orderset = related_orders[python_attr].orderset
            if child_orderset is None:
                continue
            prefix = spec.django_source_path
            for child_path, child_dir in normalize_input_value(child_orderset, value):
                result.append((f"{prefix}__{child_path}", child_dir))
        else:
            # Leaf -- value is an ``Ordering`` member (or None, already
            # short-circuited above).
            result.append((spec.django_source_path, value))
    return result


def materialize_input_class(name: str, input_cls: type) -> None:
    """Set ``input_cls`` as a real module global of ``orders.inputs`` under ``name``.

    Strawberry's ``LazyType.resolve_type`` reads
    ``sys.modules[<module>].__dict__[name]`` to materialize an
    ``Annotated[<name>, strawberry.lazy(<module>)]`` reference; this
    helper is the single entry point that pins ``input_cls`` at the
    matching ``__dict__`` slot per spec-028 Decision 9.

    Idempotent on the ``(name, input_cls)`` pair: re-materializing the
    same class under the same name is a no-op (Decision 9 lifecycle
    clause -- supports partial-finalize recovery without a sentinel pass).
    A collision against a different class under the same ``name`` raises
    ``ConfigurationError`` naming both qualified class names so the
    consumer sees the offending pair instead of a cryptic schema-build
    error.
    """
    existing = _materialized_names.get(name)
    if existing is input_cls:
        return
    if existing is not None:
        raise ConfigurationError(
            f"{name!r} is materialized by two distinct OrderSet input classes: "
            f"{existing.__module__}.{existing.__qualname__} vs "
            f"{input_cls.__module__}.{input_cls.__qualname__}. Rename one orderset "
            "so its class-derived input type name is unique.",
        )
    module = sys.modules[INPUTS_MODULE_PATH]
    setattr(module, name, input_cls)
    _materialized_names[name] = input_cls


def _iter_orderset_subclasses(root: type) -> list[type]:
    """Return every concrete subclass of ``root`` (depth-first, dedup by identity).

    Uses ``type.__subclasses__()`` which only yields LIVE subclasses;
    garbage-collected definitions silently drop. That is the correct
    contract for a test-isolation clear -- a definition that has
    already been collected has no state to reset. Mirror of
    ``filters/inputs.py::_iter_filterset_subclasses``.
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


def clear_order_input_namespace() -> None:
    """Reset the order-input ledger and per-orderset binding state for a fresh build.

    Clears the bookkeeping that prevents stale-state leakage across
    consumer-side autouse-reload fixtures: ``_materialized_names``
    (forces ``materialize_input_class`` to re-emit on the next
    finalize), ``_field_specs`` (per-(orderset, field) provenance for
    the normalizer), the ``OrderArgumentsFactory`` class-level caches
    (``input_object_types`` / ``_type_orderset_registry``), and every
    ``OrderSet`` subclass's phase-2.5 binding state
    (``_owner_definition`` / ``_expanded_fields`` /
    ``_is_expanding_fields``). After the clear, a follow-up
    ``finalize_django_types()`` call rebuilds every input class from
    scratch against the freshly-cleared registry.

    **Materialized class objects are intentionally left parked in
    ``orders.inputs.__dict__``** per spec-028 Revision 4 B2.
    ``materialize_input_class`` already overwrites the module global
    via ``setattr`` on the next finalize pass, so the parked class is
    replaced in place once the rebuild runs. Stripping the class via
    ``delattr`` here would break any ``strawberry.lazy(...)`` LazyType
    held by a consumer module whose autouse-reload fixture did NOT
    also reload the holder.

    **Does NOT touch ``_helper_referenced_ordersets``.** Per spec-028
    Decision 9 line 775, the ledger lives in ``orders/__init__.py``
    co-located with its only writer (``order_input_type``); the clear
    block in ``registry.clear()`` (Slice 3) carries TWO separate steps
    -- one for ``clear_order_input_namespace``, one for the ledger.

    The helper short-circuits cleanly when the factory / orderset
    modules are not in ``sys.modules`` (e.g., a partial-load
    environment) -- each subpass is wrapped in a local-import-with-
    pass-on-ImportError block.
    """
    _materialized_names.clear()
    _field_specs.clear()

    # OrderArgumentsFactory's class-level caches hold the built input
    # classes; stale entries here would cause ``_ensure_built`` to skip
    # rebuild and surface prior-build input classes against a freshly-
    # cleared registry.
    try:
        from .factories import OrderArgumentsFactory
    except ImportError:
        pass
    else:
        OrderArgumentsFactory.input_object_types.clear()
        OrderArgumentsFactory._type_orderset_registry.clear()

    # Every OrderSet subclass carries phase-2.5 binding state at the
    # class level; that state survives a ``registry.clear()`` call and
    # would otherwise force the rebuild down a stale-owner path on the
    # next finalize even though the caller intended a clean rebuild.
    # Symmetric with the factory guard above: on a broken import this
    # ``pass``es rather than ``return``s so this phase never short-
    # circuits a later cleanup added after it.
    try:
        from .sets import OrderSet
    except ImportError:
        pass
    else:
        for subclass in _iter_orderset_subclasses(OrderSet):
            # ``delattr`` on the subclass so an inherited default (the
            # ``OrderSet`` base's ``_owner_definition = None``) is
            # restored rather than masked. Each attribute is removed
            # only when set directly on the subclass
            # (``in subclass.__dict__``) so a subclass that never had a
            # binding tolerates the clear.
            for attr in ("_owner_definition", "_expanded_fields", "_is_expanding_fields"):
                if attr in subclass.__dict__:
                    delattr(subclass, attr)
