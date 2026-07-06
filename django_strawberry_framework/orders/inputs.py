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
provenance ledger (``_field_specs``), and the module-global
materialization / namespace-clear pair (``materialize_input_class`` /
``clear_order_input_namespace``).

Slice 3 wires ``registry.clear()`` to call ``clear_order_input_namespace``
plus the separate ``_helper_referenced_ordersets.clear()`` block per
spec-028 Decision 9 line 775.
"""

from __future__ import annotations

import enum
from typing import TYPE_CHECKING, Annotated, Any

import strawberry
from django.db.models import F
from django.db.models.expressions import OrderBy

from ..utils.input_values import RELATED, SetInputTraversal, iter_active_fields
from ..utils.inputs import (
    GeneratedInputFieldSpec,
    build_strawberry_input_class,
    clear_generated_input_namespace,
    iter_set_subclasses,
    materialize_generated_input_class,
)
from ..utils.strings import graphql_camel_name

if TYPE_CHECKING:  # pragma: no cover - type-checking-only imports.
    from ..types.definition import DjangoTypeDefinition
    from .sets import OrderSet

# Domain-local aliases for the shared generated-input substrate (the mechanics
# are single-sited in ``utils/inputs.py`` per the 0.0.9 DRY pass). Tests and
# ``factories.py`` import these spec-028 Decision 9 names from this module, so
# they stay addressable here.
FieldSpec = GeneratedInputFieldSpec
build_input_class = build_strawberry_input_class
_camel_case = graphql_camel_name
_iter_orderset_subclasses = iter_set_subclasses


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

    Portability note (``docs/feedback.md``): a bare ``ASC`` / ``DESC`` over a
    NULLABLE column defers NULL placement to the backend - SQLite sorts NULLs
    first on ``ASC``, Postgres / MySQL sort them last - so the NULL partition
    (and thus the page boundaries of a connection paged over a nullable column)
    differs across databases, and the test suite runs on SQLite. This does NOT
    break cursor stability WITHIN one backend (positional cursors only need a
    stable order across requests on the same database); use the explicit
    ``ASC_NULLS_FIRST`` / ``ASC_NULLS_LAST`` (and ``DESC_*``) variants for a
    backend-independent NULL partition.
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
        # Every order field is optional (``inner | None`` / ``Ordering | None``):
        # pass ``default=None`` explicitly now that an omitted ``default`` means
        # required (``utils/inputs.py`` / ``docs/feedback.md`` Finding 2).
        field_kwargs: dict[str, Any] = {"default": None}
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

    The dataclass-vs-dict walk, the top-level ``list[<T>]`` flattening, the
    ``None`` active-input skip, the ``_field_specs`` lookup, and the
    leaf-vs-related classification are the shared traversal mechanics owned by
    ``utils/input_values.py::iter_active_fields`` (the 0.0.9 DRY pass,
    ``docs/feedback.md`` Major 1). This function keeps only the order-side leaf
    semantics: a ``RelatedOrder`` branch recurses into the target orderset with
    the django source path as a prefix (e.g. ``shelf`` -> ``shelf__code``); a
    leaf appends ``(django_source_path, Ordering | None)``. ``handle_top_level_list``
    is set because the resolver-facing order argument shape is
    ``list[<T>OrderInputType] | None``.
    """
    config = SetInputTraversal(
        field_specs=_field_specs,
        related_attr="related_orders",
        handle_top_level_list=True,
    )
    result: list[tuple[str, Ordering | None]] = []
    for field in iter_active_fields(orderset_cls, input_value, config):
        if field.spec is None:
            continue  # Defensive -- should be impossible after a finalize.
        if field.kind == RELATED:
            # ``RelatedOrder`` branch -- recurse into the target orderset and
            # prefix every child path with this branch's django source path.
            child_orderset = field.related_obj.orderset
            if child_orderset is None:
                continue
            prefix = field.spec.django_source_path
            for child_path, child_dir in normalize_input_value(child_orderset, field.raw_value):
                result.append((f"{prefix}__{child_path}", child_dir))
        else:
            # Leaf -- ``raw_value`` is an ``Ordering`` member (``None`` was
            # already skipped as inactive by the classifier).
            result.append((field.spec.django_source_path, field.raw_value))
    return result


def materialize_input_class(name: str, input_cls: type) -> None:
    """Set ``input_cls`` as a real module global of ``orders.inputs`` under ``name``.

    Thin family wrapper over
    ``utils/inputs.py::materialize_generated_input_class`` pinning the
    order-side module path, family label, and ledger. See that helper for the
    Strawberry ``LazyType.resolve_type`` contract, the ``(name, input_cls)``
    idempotency clause, and the distinct-class collision raise (spec-028
    Decision 9).
    """
    materialize_generated_input_class(
        name,
        input_cls,
        module_path=INPUTS_MODULE_PATH,
        family_label="OrderSet",
        ledger=_materialized_names,
    )


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
    environment) -- the shared substrate's cycle-safe imports tolerate
    the call without raising.

    Delegates the lifecycle to
    ``utils/inputs.py::clear_generated_input_namespace``, which reads the
    per-orderset binding attrs from ``OrderSet._lifecycle`` (the
    ``SetLifecycleAttrs`` descriptor: ``_owner_definition`` / ``_expanded_fields``
    / ``_is_expanding_fields``) rather than a re-spelled tuple.
    """
    clear_generated_input_namespace(
        materialized_names=_materialized_names,
        field_specs=_field_specs,
        factory_module="django_strawberry_framework.orders.factories",
        factory_class_name="OrderArgumentsFactory",
        collision_registry_attr="_type_orderset_registry",
        set_module="django_strawberry_framework.orders.sets",
        set_class_name="OrderSet",
    )
