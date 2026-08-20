"""Order input namespace, direction enum, and input-data adapters.

Generated order input classes MUST become real globals of this module
because ``strawberry.lazy("django_strawberry_framework.orders.inputs")``
resolves through ``module.__dict__`` (spec-028 Decision 9). This module
pairs the constant (``INPUTS_MODULE_PATH``) and the public direction enum
(``Ordering``) with the module-global materialization / ledger /
namespace-clear trio (``materialize_input_class`` / ``_materialized_names`` /
``clear_order_input_namespace``), the input-data adapters
(``_build_input_fields`` / ``convert_order_field_to_input_annotation`` /
``normalize_input_value`` / ``build_input_class``), the
``Meta.fields = "__all__"`` helper (``_get_concrete_field_names_for_order``),
and the per-(orderset, attr) provenance ledger (``_field_specs``).

``clear_order_input_namespace`` registers into ``registry.clear()`` via
``register_subsystem_clear`` (owner ``orders.input_namespace``,
``before_bind=True``). The separate ``_helper_referenced_ordersets`` ledger
in ``orders/__init__.py`` clears through its own registration (owner
``orders.helper_references``) per spec-028 Decision 9 -- not via a
cycle-safe local import inside ``TypeRegistry.clear``.
"""

from __future__ import annotations

import enum
from typing import TYPE_CHECKING, Any

import strawberry
from django.db.models import F
from django.db.models.expressions import OrderBy

from ..registry import register_subsystem_clear
from ..utils.input_values import (
    RELATED,
    SetInputTraversal,
    is_inactive_value,
    iter_active_fields,
    iter_input_items,
)
from ..utils.inputs import (
    GeneratedInputFieldSpec,
    build_strawberry_input_class,
    emit_set_input_field_triples,
    iter_set_subclasses,
    make_set_input_namespace,
    set_input_type_name,
)
from ..utils.strings import graphql_camel_name

if TYPE_CHECKING:  # pragma: no cover - type-checking-only imports.
    from ..types.definition import DjangoTypeDefinition
    from .sets import OrderSet

# Domain-local aliases for the shared generated-input substrate (the mechanics
# are single-sited in ``utils/inputs.py``). Tests and
# ``factories.py`` import these spec-028 Decision 9 names from this module, so
# they stay addressable here.
FieldSpec = GeneratedInputFieldSpec
build_input_class = build_strawberry_input_class
_camel_case = graphql_camel_name
_iter_orderset_subclasses = iter_set_subclasses
_input_type_name_for = set_input_type_name


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

    Portability note: a bare ``ASC`` / ``DESC`` over a NULLABLE column defers
    NULL placement to the backend - SQLite sorts NULLs first on ``ASC``,
    Postgres / MySQL sort them last - so the NULL partition (and thus the page
    boundaries of a connection paged over a nullable column) differs across
    databases, and the test suite runs on SQLite. This does NOT break cursor
    stability WITHIN one backend (positional cursors only need a stable order
    across requests on the same database); use the explicit ``ASC_NULLS_FIRST``
    / ``ASC_NULLS_LAST`` (and ``DESC_*``) variants for a backend-independent
    NULL partition.
    """

    ASC = "ASC"
    DESC = "DESC"
    ASC_NULLS_FIRST = "ASC_NULLS_FIRST"
    ASC_NULLS_LAST = "ASC_NULLS_LAST"
    DESC_NULLS_FIRST = "DESC_NULLS_FIRST"
    DESC_NULLS_LAST = "DESC_NULLS_LAST"

    @property
    def is_ascending(self) -> bool:
        """Whether this member is an ascending direction (including NULLS variants).

        Single source for the ASC / DESC discrimination that ``resolve`` and
        ``OrderSet._resolve_order_expressions`` (Min vs Max aggregate for
        to-many terms) both need. Anchored on the member-name prefix so every
        ``ASC_*`` variant classifies as ascending while every ``DESC_*``
        variant classifies as descending, without a parallel membership table.
        A prefix test (not substring membership) keeps the rule precise if
        future members embed ``ASC`` elsewhere in the name.
        """
        return self.name.startswith("ASC")

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
        if self.is_ascending:
            return F(value).asc(nulls_first=nulls_first, nulls_last=nulls_last)
        return F(value).desc(nulls_first=nulls_first, nulls_last=nulls_last)


# Provenance table populated by ``_build_input_fields`` and consulted at
# runtime by ``normalize_input_value`` (and indirectly by
# ``OrderSet._active_permission_field_paths``). Keyed by
# ``(OrderSet subclass, python_attr)``; emptied by
# ``clear_order_input_namespace``.
#
# Decision-9 namespace lifecycle. Mechanics live in
# ``utils/inputs.py::make_set_input_namespace`` (heavy clear). This module
# keeps the spec-named public wrappers and a ledger disjoint from
# ``filters.inputs`` per spec-028 Decision 9. ``clear_order_input_namespace``
# leaves class objects parked in ``orders.inputs.__dict__``.
_materialized_names: dict[str, type]
_field_specs: dict[tuple[type[OrderSet], str], FieldSpec]
(
    _materialized_names,
    _field_specs,
    _materialize_input,
    _clear_input_namespace,
) = make_set_input_namespace(
    INPUTS_MODULE_PATH,
    "OrderSet",
    factory_module="django_strawberry_framework.orders.factories",
    factory_class_name="OrderArgumentsFactory",
    collision_registry_attr="_type_orderset_registry",
    set_module="django_strawberry_framework.orders.sets",
    set_class_name="OrderSet",
)


def _get_concrete_field_names_for_order(model: Any) -> list[str]:
    """Return every column-backed field name for ``model``.

    Backs ``OrderSet._expand_meta_fields`` when ``Meta.fields = "__all__"``
    per spec-028 Decision 3. The cookbook's ``get_concrete_field_names``
    at ``django_graphene_filters/mixins.py`` uses ``hasattr(f, "column")``
    alone, but Django's virtual ``GenericRelation`` and
    ``GenericForeignKey`` descriptors also expose ``column = None``.
    Checking that the column is a real database column (rather than merely
    an attribute) keeps those virtual fields out alongside reverse
    relations and many-to-many managers.

    Returned list includes forward ``ForeignKey`` / ``OneToOneField``
    columns (their ``<field>_id`` column is on the model's own table)
    and excludes reverse FKs (no ``column`` attribute) and M2M managers.
    """
    return [
        f.name
        for f in model._meta.get_fields()
        if getattr(f, "column", None) is not None and not getattr(f, "many_to_many", False)
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
    the body level; they are kept in the signature for shape-symmetry
    with ``filters/inputs.py::convert_filter_to_input_annotation``, not
    for a DISTINCT ON extension -- per spec-028 Decision 12 no DISTINCT
    ON surface ships.
    """
    del model_field, owner_definition  # unused; kept for shape-symmetry (see docstring).
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
    - leaf -> ``Ordering | None`` (spec-028 Decision 5).

    Populates ``_field_specs`` so the runtime ``normalize_input_value``
    walker can reconstruct the ORM path from each Strawberry input
    dataclass attribute. The ``shelf__code`` flat-shorthand path (per
    spec-028 Edge cases) maps python attr ``shelf_code`` ->
    GraphQL alias ``shelfCode`` -> django source path ``shelf__code``.

    Mirror of ``filters/inputs.py::_build_input_fields`` with three
    deliberate simplifications: no per-field operator-bag class build
    (every leaf is ``Ordering | None``), no ``_build_logic_fields`` call
    (no ``and_`` / ``or_`` / ``not_`` operator bag on the order side),
    no ``HIDE_FLAT_FILTERS`` skip (the order side does not expose flat
    ``*__lookup`` paths through ``django-filter`` expansion).
    """
    del owner_definition  # reserved -- see ``convert_order_field_to_input_annotation``.

    def _leaf_of(top_name: str, _python_attr: str, _entry: Any) -> tuple[Any, str]:
        # Leaf field: ``Ordering | None`` regardless of model-field type per
        # spec-028 Decision 5. ``model_field`` discovery is a future-extension
        # affordance the converter ignores today.
        return convert_order_field_to_input_annotation(None, None), top_name

    # The per-field emission scaffold (python-attr flatten -> camel-case ->
    # optional kwargs -> related lazy-ref with the ``RelatedOrder(None, ...)``
    # placeholder skip vs leaf -> triple + ``FieldSpec``) is single-sited in
    # ``utils/inputs.py::emit_set_input_field_triples``; the
    # closures carry the order-family semantics (fixed ``Ordering | None``
    # leaves, ``field_name or top_name`` related source paths).
    return emit_set_input_field_triples(
        orderset_cls,
        list(orderset_cls.get_fields().items()),
        related_target_of=lambda _top_name, entry: (
            (True, entry.orderset) if entry is not None else (False, None)
        ),
        related_source_path_of=lambda top_name, entry: entry.field_name or top_name,
        leaf_of=_leaf_of,
        input_type_name_for=_input_type_name_for,
        module_path=INPUTS_MODULE_PATH,
        field_specs=_field_specs,
    )


def normalize_input_value(
    orderset_cls: type[OrderSet],
    input_value: Any,
) -> list[tuple[str, Ordering | None]]:
    """Flatten a Strawberry order input value into ``(field_path, direction)`` tuples.

    The function consumes the Strawberry input dataclass (post-
    deserialization, post-Strawberry-type-coercion) and produces a flat
    ``[(field_path, Ordering | None), ...]`` list. ``None`` directions
    are preserved -- the apply pipeline filters them in its
    ``direction.resolve(...)`` comprehension. Per spec-028 Decision 13:

    - top-level ``list[<T>OrderInputType] | None`` -> recurse on each
      element and concatenate.
    - per-element ``<T>OrderInputType`` -> walk the dataclass's fields
      via the ``_field_specs`` map; ``None`` attribute values short-
      circuit (active-input-only scope per spec-028 Decision 8 step 6). Thus
      an omitted field and an explicit GraphQL ``null`` direction have
      identical no-op semantics: neither contributes an ordering term
      nor fires that field's permission gate.
    - ``RelatedOrder`` branch -> recurse into the child orderset with
      the django source path as a prefix (e.g. ``shelf`` ->
      ``shelf__code``).

    Mirror of ``filters/inputs.py::normalize_input_value`` with the
    operator-bag layer removed (no ``GlobalIDFilter`` /
    ``BaseCSVFilter`` / ``RangeFilter`` / ``ChoiceFilter`` /
    ``ListFilter`` branches -- ordering has no leaf-shape divergence
    per spec-028 Decision 5).

    The dataclass-vs-dict walk, the top-level ``list[<T>]`` flattening, the
    ``None`` active-input skip, the ``_field_specs`` lookup, and the
    leaf-vs-related classification are the shared traversal mechanics owned by
    ``utils/input_values.py::iter_active_fields``. This function
    keeps only the order-side leaf semantics: a ``RelatedOrder`` branch recurses into
    the target orderset with the django source path as a prefix (e.g. ``shelf`` ->
    ``shelf__code``); a leaf appends ``(django_source_path, Ordering | None)``.
    ``handle_top_level_list`` is set because the resolver-facing order argument shape
    is ``list[<T>OrderInputType] | None``.
    """
    # Direct callers may provide the mapping shape without first constructing
    # an ``OrderArgumentsFactory`` input class. Build the provenance entries
    # lazily so path-shorthand fields (``shelf_code`` -> ``shelf__code``)
    # and related branches still normalize correctly instead of being
    # silently discarded when ``field.spec`` is absent.
    _ensure_field_specs(orderset_cls, input_value)

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


def _ensure_field_specs(orderset_cls: type[OrderSet], input_value: Any) -> None:
    """Populate provenance before direct normalization or permission checks."""

    def _has_active_fields(value: Any) -> bool:
        if is_inactive_value(value):
            return False
        if isinstance(value, list):
            return any(_has_active_fields(element) for element in value)
        items = iter_input_items(value)
        if items is None:
            return False
        return any(not is_inactive_value(raw_value) for _, raw_value in items)

    if not _has_active_fields(input_value):
        return
    meta = getattr(orderset_cls, "Meta", None)
    if getattr(meta, "model", None) is not None and not any(
        owner is orderset_cls for owner, _ in _field_specs
    ):
        _build_input_fields(orderset_cls)


def materialize_input_class(name: str, input_cls: type) -> None:
    """Set ``input_cls`` as a real module global of ``orders.inputs`` under ``name``.

    Thin family wrapper over the ``make_set_input_namespace`` materializer.
    See ``utils/inputs.py::materialize_generated_input_class`` for the
    Strawberry ``LazyType.resolve_type`` contract, the ``(name, input_cls)``
    idempotency clause, and the distinct-class collision raise
    (spec-028 Decision 9).
    """
    _materialize_input(name, input_cls)


def clear_order_input_namespace() -> None:
    """Reset the order-input ledger and per-orderset binding state for a fresh build.

    Thin family wrapper over the ``make_set_input_namespace`` heavy clear
    (ledger, ``_field_specs``, ``OrderArgumentsFactory`` caches, every
    ``OrderSet`` subclass's ``_lifecycle`` binding attrs). Does NOT touch
    ``_helper_referenced_ordersets`` -- that ledger lives in
    ``orders/__init__.py`` and clears through its own
    ``register_subsystem_clear`` row (owner ``orders.helper_references``).
    """
    _clear_input_namespace()


register_subsystem_clear(
    clear_order_input_namespace,
    owner="orders.input_namespace",
    before_bind=True,
)
