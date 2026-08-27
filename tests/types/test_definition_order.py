"""Acceptance tests for definition-order-independent DjangoType relation finalization."""

import importlib
import sys
import types
import uuid
from typing import Annotated, get_args

import pytest
import strawberry
from apps.library.models import Book, Genre, MembershipCard, Patron, Shelf
from apps.products.models import Category, Entry, Item, Property
from django.db import models
from strawberry import relay
from strawberry.types.lazy_type import StrawberryLazyReference

from django_strawberry_framework import DjangoType, auto, finalize_django_types
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.registry import registry
from django_strawberry_framework.types.base import _build_annotations

# Dotted path of the module holding the ``strawberry.lazy`` relation-override
# target. Bound once for the ``sys.modules`` eviction and the assertions; the
# ``strawberry.lazy("...")`` calls in the tests keep the literal, because a
# consumer writes a literal there and that literal is what is under test.
_LAZY_TARGET_MODULE = "tests.types.fixtures.lazy_relation_target_module"


class _FakeUnsupportedField(models.Field):
    """One-line Django Field subclass with no SCALAR_MAP match.

    Pins the unsupported-field-type bypass test for spec-015
    Decision 7a - the consumer's annotation override is a recourse
    parallel to ``Meta.exclude`` for unsupported scalar field types.
    """


@pytest.fixture(autouse=True)
def _isolate_registry():
    """Drop registry state on entry/exit so each test starts clean."""
    registry.clear()
    yield
    registry.clear()


def _strawberry_field(type_cls: type, field_name: str):
    """Return a finalized Strawberry field by Python name.

    Tests intentionally inspect Strawberry internals such as
    ``base_resolver.wrapped_func`` to pin resolver attachment; if Strawberry
    changes this field shape, these tests should fail loudly.
    """
    return next(
        field
        for field in type_cls.__strawberry_definition__.fields
        if field.python_name == field_name
    )


def test_reverse_fk_resolves_when_parent_declared_before_child():
    """Category.items starts pending and resolves to list[ItemType] at finalization."""

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name", "items")

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    # Pre-finalize: every auto-synthesized relation is the pending sentinel
    # under spec-014's always-defer contract, regardless of whether
    # the target type happens to already be registered.
    assert CategoryType.__annotations__["items"].__name__ == "PendingRelationAnnotation"
    assert ItemType.__annotations__["category"].__name__ == "PendingRelationAnnotation"

    finalize_django_types()

    assert CategoryType.__annotations__["items"] == list[ItemType]
    assert ItemType.__annotations__["category"] is CategoryType


def test_reverse_fk_resolves_when_child_declared_before_parent():
    """Item.category starts pending and resolves once CategoryType exists."""

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name", "items")

    # Pre-finalize: every auto-synthesized relation is the pending sentinel
    # under spec-014's always-defer contract.
    assert ItemType.__annotations__["category"].__name__ == "PendingRelationAnnotation"
    assert CategoryType.__annotations__["items"].__name__ == "PendingRelationAnnotation"

    finalize_django_types()

    assert ItemType.__annotations__["category"] is CategoryType
    assert CategoryType.__annotations__["items"] == list[ItemType]


def test_one_to_one_forward_and_reverse_relations_resolve():
    """Forward OneToOne and reverse OneToOne get concrete final annotations."""

    class MembershipCardType(DjangoType):
        class Meta:
            model = MembershipCard
            fields = ("id", "barcode", "patron")

    class PatronType(DjangoType):
        class Meta:
            model = Patron
            fields = ("id", "name", "card")

    finalize_django_types()

    assert MembershipCardType.__annotations__["patron"] is PatronType
    assert PatronType.__annotations__["card"] == (MembershipCardType | None)


def test_many_to_many_forward_and_reverse_relations_resolve():
    """Forward/reverse M2M and an adjacent FK resolve across declaration order."""

    class BookType(DjangoType):
        class Meta:
            model = Book
            fields = (
                "id",
                "title",
                "shelf",
                "genres",
            )

    class GenreType(DjangoType):
        class Meta:
            model = Genre
            fields = ("id", "name", "books")

    class ShelfType(DjangoType):
        class Meta:
            model = Shelf
            fields = ("id", "code", "books")

    finalize_django_types()

    assert BookType.__annotations__["shelf"] is ShelfType
    assert BookType.__annotations__["genres"] == list[GenreType]
    assert GenreType.__annotations__["books"] == list[BookType]
    assert ShelfType.__annotations__["books"] == list[BookType]


def test_multi_cycle_finalizes_every_edge():
    """A fakeshop multi-cycle resolves every pending FK and reverse FK edge."""

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = (
                "id",
                "name",
                "items",
                "properties",
            )

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = (
                "id",
                "name",
                "category",
                "entries",
            )

    class EntryType(DjangoType):
        class Meta:
            model = Entry
            fields = (
                "id",
                "value",
                "item",
                "property",
            )

    class PropertyType(DjangoType):
        class Meta:
            model = Property
            fields = (
                "id",
                "name",
                "category",
                "entries",
            )

    finalize_django_types()

    assert CategoryType.__annotations__["items"] == list[ItemType]
    assert CategoryType.__annotations__["properties"] == list[PropertyType]
    assert ItemType.__annotations__["category"] is CategoryType
    assert ItemType.__annotations__["entries"] == list[EntryType]
    assert EntryType.__annotations__["item"] is ItemType
    assert EntryType.__annotations__["property"] is PropertyType
    assert PropertyType.__annotations__["category"] is CategoryType
    assert PropertyType.__annotations__["entries"] == list[EntryType]


def test_unresolved_target_raises_with_source_field_and_target():
    """Finalization fails loudly when a selected relation target was never registered."""

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    with pytest.raises(ConfigurationError) as exc_info:
        finalize_django_types()

    msg = str(exc_info.value)
    assert "Cannot finalize Django types" in msg
    assert "Item.category -> Category" in msg
    assert "no registered DjangoType" in msg


def test_annotation_only_relation_override_keeps_generated_resolver():
    """Annotation-only overrides keep the generated many-side resolver."""

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

    class CategoryType(DjangoType):
        items: list[ItemType]

        class Meta:
            model = Category
            fields = ("id", "name", "items")

    definition = CategoryType.__django_strawberry_definition__
    assert definition.consumer_authored_fields == frozenset({"items"})
    assert definition.consumer_annotated_relation_fields == frozenset({"items"})
    assert definition.consumer_assigned_relation_fields == frozenset()

    finalize_django_types()

    items_field = _strawberry_field(CategoryType, "items")
    assert items_field.base_resolver is not None
    assert items_field.base_resolver.wrapped_func.__name__ == "resolve_items"


def test_assigned_relation_field_override_keeps_consumer_resolver():
    """Assigned Strawberry relation fields suppress generated relation resolvers."""

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

    class CategoryType(DjangoType):
        @strawberry.field
        def items(self) -> list[ItemType]:
            return []

        class Meta:
            model = Category
            fields = ("id", "name", "items")

    definition = CategoryType.__django_strawberry_definition__
    assert definition.consumer_authored_fields == frozenset({"items"})
    assert definition.consumer_annotated_relation_fields == frozenset()
    assert definition.consumer_assigned_relation_fields == frozenset({"items"})

    finalize_django_types()

    items_field = _strawberry_field(CategoryType, "items")
    assert items_field.base_resolver is not None
    assert items_field.base_resolver.wrapped_func.__qualname__.endswith("CategoryType.items")


def test_assigned_relation_field_resolver_kwarg_override_keeps_consumer_resolver():
    """An ``= strawberry.field(resolver=...)`` relation assignment keeps its resolver.

    Spec-010's third listed manual-annotation shape, distinct from the
    ``@strawberry.field`` decorator form above: the annotated assignment puts
    the name in both relation sets, and finalization neither rewrites the
    annotation nor attaches a generated resolver over the assigned field.
    """

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

    def category_items(root) -> list[ItemType]:
        return []

    class CategoryType(DjangoType):
        items: list[ItemType] = strawberry.field(resolver=category_items)

        class Meta:
            model = Category
            fields = ("id", "name", "items")

    definition = CategoryType.__django_strawberry_definition__
    assert definition.consumer_authored_fields == frozenset({"items"})
    # The annotated assignment is the one shape that lands in BOTH relation
    # sets; each line pins one of them and neither substitutes for the other.
    assert definition.consumer_annotated_relation_fields == frozenset({"items"})
    assert definition.consumer_assigned_relation_fields == frozenset({"items"})
    assert definition.consumer_assigned_scalar_fields == frozenset()

    # The consumer's annotation survives collection unrewritten: a rewrite
    # would leave ``PendingRelationAnnotation`` or a synthesized class here.
    assert CategoryType.__annotations__["items"] == list[ItemType]

    # No pending relation was recorded. Read before finalization, which
    # discards resolved records - afterwards "never recorded" and "recorded
    # and resolved" are indistinguishable.
    assert [
        pending
        for pending in registry.iter_pending_relations()
        if pending.source_type is CategoryType
    ] == []

    finalize_django_types()

    items_field = _strawberry_field(CategoryType, "items")
    assert items_field.base_resolver is not None
    # The pin for the consumer-assigned relation skip that
    # ``types/finalizer.py::finalize_django_types`` hands to
    # ``types/resolvers.py::_attach_relation_resolvers``: identity with the
    # consumer's own function, which flips to the generated relation resolver
    # the moment that skip stops holding. The SDL below is byte-identical
    # either way, so it corroborates the shape and never pins it.
    assert items_field.base_resolver.wrapped_func is category_items

    @strawberry.type
    class Query:
        @strawberry.field
        def categories(self) -> list[CategoryType]:
            return []

    schema = strawberry.Schema(query=Query)
    assert "items: [ItemType!]!" in schema.as_str()


def test_cross_module_lazy_relation_override_types_the_field_as_the_referenced_class():
    """A hand-written ``Annotated[..., strawberry.lazy(...)]`` relation override wins.

    The second shape of spec-010's manual annotation contract: the consumer's
    annotation reaches the class unrewritten, no pending relation is recorded
    for the field, the generated many-side resolver is still attached, and a
    real schema builds with the field typed as the class the lazy reference
    names - resolved through the module path, never through this module's
    namespace.
    """
    # Drop any previously-imported fixture module object so the import below
    # re-executes (and re-registers) under the cleared registry, as
    # ``test_filterset_class_resolves_across_module_boundary`` explains.
    # ``importlib.import_module`` rather than ``from ... import ...``: the
    # latter is satisfied by the still-set parent-package attribute and would
    # hand back the stale module without repopulating ``sys.modules``, leaving
    # the fresh execution to happen inside the schema build below - after
    # finalization, where registration is refused.
    sys.modules.pop(_LAZY_TARGET_MODULE, None)
    lazy_relation_target_module = importlib.import_module(_LAZY_TARGET_MODULE)

    class CategoryType(DjangoType):
        # ``LazyItemType`` is deliberately not imported into this module: the
        # reference resolves through the lazy module path, which is the whole
        # point of the escape hatch.
        items: list[
            Annotated[
                "LazyItemType",  # noqa: F821
                strawberry.lazy("tests.types.fixtures.lazy_relation_target_module"),
            ]
        ]

        class Meta:
            model = Category
            fields = ("id", "name", "items")

    definition = CategoryType.__django_strawberry_definition__
    assert definition.consumer_annotated_relation_fields == frozenset({"items"})
    assert definition.consumer_assigned_relation_fields == frozenset()

    # The consumer's annotation object survives collection: a rewrite would
    # leave ``PendingRelationAnnotation`` or a concrete class here instead.
    lazy_reference = get_args(CategoryType.__annotations__["items"])[0].__metadata__[0]
    assert isinstance(lazy_reference, StrawberryLazyReference)
    assert lazy_reference.module == _LAZY_TARGET_MODULE

    # No pending relation was recorded. Read before finalization, which
    # discards resolved records - afterwards "never recorded" and "recorded
    # and resolved" are indistinguishable.
    assert [
        pending
        for pending in registry.iter_pending_relations()
        if pending.source_type is CategoryType
    ] == []

    finalize_django_types()

    items_field = _strawberry_field(CategoryType, "items")
    assert items_field.base_resolver is not None
    assert items_field.base_resolver.wrapped_func.__name__ == "resolve_items"

    @strawberry.type
    class Query:
        @strawberry.field
        def categories(self) -> list[CategoryType]:
            return []

    schema = strawberry.Schema(query=Query)
    assert (
        schema.get_type_by_name("LazyItemType").origin is lazy_relation_target_module.LazyItemType
    )
    assert "items: [LazyItemType!]!" in schema.as_str()


def test_cross_module_lazy_relation_override_wins_over_the_registered_primary_type():
    """The lazily referenced type wins even when another type is the model's primary.

    Discriminates the override from the auto-synthesis path: with a
    ``Meta.primary = True`` type registered for the same Django model,
    synthesis and the consumer's annotation name different classes, so a
    regression that dropped the override would type the field as the primary.
    """
    sys.modules.pop(_LAZY_TARGET_MODULE, None)
    lazy_relation_target_module = importlib.import_module(_LAZY_TARGET_MODULE)

    class PrimaryItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")
            primary = True

    class CategoryType(DjangoType):
        # ``LazyItemType`` is deliberately not imported into this module: the
        # reference resolves through the lazy module path, which is the whole
        # point of the escape hatch.
        items: list[
            Annotated[
                "LazyItemType",  # noqa: F821
                strawberry.lazy("tests.types.fixtures.lazy_relation_target_module"),
            ]
        ]

        class Meta:
            model = Category
            fields = ("id", "name", "items")

    definition = CategoryType.__django_strawberry_definition__
    assert definition.consumer_annotated_relation_fields == frozenset({"items"})
    assert definition.consumer_assigned_relation_fields == frozenset()

    lazy_reference = get_args(CategoryType.__annotations__["items"])[0].__metadata__[0]
    assert isinstance(lazy_reference, StrawberryLazyReference)
    assert lazy_reference.module == _LAZY_TARGET_MODULE

    assert [
        pending
        for pending in registry.iter_pending_relations()
        if pending.source_type is CategoryType
    ] == []

    finalize_django_types()

    items_field = _strawberry_field(CategoryType, "items")
    assert items_field.base_resolver is not None
    assert items_field.base_resolver.wrapped_func.__name__ == "resolve_items"

    @strawberry.type
    class Query:
        @strawberry.field
        def categories(self) -> list[CategoryType]:
            return []

    schema = strawberry.Schema(query=Query)
    assert (
        schema.get_type_by_name("LazyItemType").origin is lazy_relation_target_module.LazyItemType
    )
    assert "items: [LazyItemType!]!" in schema.as_str()
    assert "PrimaryItemType" not in schema.as_str()


def test_relation_field_class_attribute_shadowing_raises():
    """Unsupported class attributes cannot silently shadow relation fields.

    The error is attributed to the consumer's ``DjangoType`` subclass
    (``CategoryType``), not the underlying Django model - the shadow lives on
    the class attribute, which is the consumer-visible site, so a stack-trace
    grep for the offending site lands on the right class.
    """
    with pytest.raises(
        ConfigurationError,
        match=r"CategoryType\.items shadows a Django relation field",
    ):

        class CategoryType(DjangoType):
            items = None

            class Meta:
                model = Category
                fields = ("id", "name", "items")


def test_assigned_scalar_field_override_keeps_consumer_resolver():
    """A ``strawberry.field(resolver=...)`` assigned to a scalar column wins.

    Were ``_consumer_assigned_relation_fields`` to collect relation names
    only, a consumer assigning a ``StrawberryField`` to a scalar column
    (e.g. ``name``) would be silently overwritten by the
    auto-synthesized ``str`` annotation. The guard collects scalar
    assignments too and ``_build_annotations`` skips them.
    """

    class CategoryType(DjangoType):
        @strawberry.field
        def name(self) -> str:
            return "overridden"

        class Meta:
            model = Category
            fields = ("id", "name")

    definition = CategoryType.__django_strawberry_definition__
    assert definition.consumer_assigned_scalar_fields == frozenset({"name"})
    assert "name" in definition.consumer_authored_fields
    # The synthesized scalar annotation must not shadow the consumer
    # assignment - the field name does not appear in the generated
    # annotations dict.
    assert "name" not in CategoryType.__annotations__

    finalize_django_types()
    name_field = _strawberry_field(CategoryType, "name")
    assert name_field.base_resolver is not None
    assert name_field.base_resolver.wrapped_func.__qualname__.endswith("CategoryType.name")


# ---------------------------------------------------------------------------
# Field-surface audit (finalizer ``_audit_field_surface``): empty surface +
# camel-case name collision between two distinct fields. Both are misconfigs
# Strawberry catches only late - the empty case as a generic ``ValueError``, the
# collision case as a SILENT field drop - so the finalizer fails loud first with
# DjangoType attribution. Sibling of the synthesized-connection camel guard.
# ---------------------------------------------------------------------------


def test_camel_case_field_collision_raises():
    """Two columns whose names default-camel-case to one GraphQL name fail loud.

    ``foo_bar`` and ``fooBar`` are distinct Django columns that both camel-case to
    ``fooBar``; Strawberry keeps one and SILENTLY drops the other. The field-surface
    audit catches the collision at finalize and names both colliding fields.
    """

    class CamelCollide(models.Model):
        foo_bar = models.IntegerField()
        fooBar = models.IntegerField()  # noqa: N815 - intentional collision fixture

        class Meta:
            managed = False
            app_label = "test_field_surface"

    class CamelCollideType(DjangoType):
        class Meta:
            model = CamelCollide
            fields = ("foo_bar", "fooBar")

    with pytest.raises(ConfigurationError) as exc:
        finalize_django_types()
    message = str(exc.value)
    assert "fooBar" in message
    assert "foo_bar" in message
    assert "collide" in message


def test_explicit_graphql_field_name_collision_raises():
    """An explicit Strawberry name participates in the settled-surface audit."""

    class ExplicitNameCollision(models.Model):
        foo_bar = models.IntegerField()

        class Meta:
            app_label = "test_field_surface"
            managed = False

    class ExplicitNameCollisionType(DjangoType):
        @strawberry.field(name="fooBar")
        def custom(self) -> int:
            return 1

        class Meta:
            model = ExplicitNameCollision
            fields = ("foo_bar",)

    with pytest.raises(ConfigurationError) as exc:
        finalize_django_types()
    message = str(exc.value)
    assert "custom" in message
    assert "foo_bar" in message
    assert "collide" in message


def test_relay_suppressed_pk_does_not_collide_with_real_consumer_field():
    """A selected pk removed by Relay is not part of the settled GraphQL surface."""

    class RenamedPrimaryKey(models.Model):
        legacy_id = models.AutoField(primary_key=True)

        class Meta:
            app_label = "test_field_surface"
            managed = False

    class RenamedPrimaryKeyType(DjangoType):
        @strawberry.field
        def legacyId(self) -> str:
            return "visible"

        class Meta:
            model = RenamedPrimaryKey
            fields = ("legacy_id",)
            interfaces = (relay.Node,)

    finalize_django_types()

    field_names = {
        field.graphql_name or field.python_name
        for field in RenamedPrimaryKeyType.__strawberry_definition__.fields
    }
    assert field_names == {"id", "legacyId"}


def test_relation_connection_does_not_collide_with_relay_suppressed_pk():
    """A generated connection may reuse the Python name of a suppressed pk column."""

    class Target(models.Model):
        name = models.CharField(max_length=20)

        class Meta:
            app_label = "test_field_surface"
            managed = False

    class Source(models.Model):
        items_connection = models.AutoField(primary_key=True)
        items = models.ManyToManyField(Target)

        class Meta:
            app_label = "test_field_surface"
            managed = False

    class TargetType(DjangoType):
        class Meta:
            model = Target
            fields = ("id", "name")
            interfaces = (relay.Node,)

    class SourceType(DjangoType):
        class Meta:
            model = Source
            fields = ("items_connection", "items")
            interfaces = (relay.Node,)

    finalize_django_types()

    field_names = {
        field.graphql_name or field.python_name
        for field in SourceType.__strawberry_definition__.fields
    }
    assert field_names == {"id", "items_connection"}


def test_relay_interface_field_prevents_false_empty_surface():
    """The inherited Relay id is a real field even when no model field is selected."""

    class RelayOnlyModel(models.Model):
        class Meta:
            app_label = "test_field_surface"
            managed = False

    class RelayOnlyType(DjangoType):
        class Meta:
            model = RelayOnlyModel
            fields = ()
            interfaces = (relay.Node,)

    finalize_django_types()

    field_names = {
        field.graphql_name or field.python_name
        for field in RelayOnlyType.__strawberry_definition__.fields
    }
    assert field_names == {"id"}


def test_empty_field_surface_raises():
    """A DjangoType with no GraphQL fields (``Meta.fields = ()``) fails loud at finalize.

    Strawberry would otherwise raise the generic ``Type <X> must define one or more
    fields`` with no DjangoType attribution; the audit names the type and its model.
    """

    class EmptySurface(models.Model):
        name = models.CharField(max_length=10)

        class Meta:
            managed = False
            app_label = "test_field_surface"

    class EmptySurfaceType(DjangoType):
        class Meta:
            model = EmptySurface
            fields = ()

    with pytest.raises(ConfigurationError) as exc:
        finalize_django_types()
    message = str(exc.value)
    assert "EmptySurfaceType" in message
    assert "no GraphQL fields" in message


# ---------------------------------------------------------------------------
# Annotation-only scalar override matrix completion (spec-015).
#
# Four core override tests pin the new annotation-only scalar override
# path; four converter-bypass tests pin Decision 7a's "consumer is
# authoritative" contract; eleven Relay-collision tests pin Decision 7's
# collision guard (five reject + six accept).
# ---------------------------------------------------------------------------


def test_annotation_only_scalar_field_override_wins_over_synthesized():
    """A consumer ``description: int`` annotation survives __init_subclass__ and finalize."""

    class CategoryType(DjangoType):
        description: int

        class Meta:
            model = Category
            fields = ("id", "name", "description")

    assert CategoryType.__annotations__["description"] is int

    finalize_django_types()

    assert CategoryType.__annotations__["description"] is int
    assert _strawberry_field(CategoryType, "description").type is int


def test_annotation_only_scalar_override_populates_definition_metadata():
    """``DjangoTypeDefinition`` carries the new ``consumer_annotated_scalar_fields`` set."""

    class CategoryType(DjangoType):
        description: int

        class Meta:
            model = Category
            fields = ("id", "name", "description")

    definition = CategoryType.__django_strawberry_definition__
    assert definition.consumer_annotated_scalar_fields == frozenset({"description"})
    assert definition.consumer_authored_fields >= frozenset({"description"})
    assert definition.consumer_assigned_scalar_fields == frozenset()


def test_annotation_only_scalar_override_does_not_emit_synthesized_annotation():
    """``_build_annotations``'s synthesized dict skips the overridden field."""

    class CategoryType(DjangoType):
        description: int

        class Meta:
            model = Category
            fields = ("id", "name", "description")

    definition = CategoryType.__django_strawberry_definition__
    synthesized, _pending = _build_annotations(
        CategoryType,
        definition.selected_fields,
        source_model=Category,
        field_map=definition.field_map,
        consumer_authored_fields=definition.consumer_authored_fields,
        interfaces=definition.interfaces,
    )
    assert "description" not in synthesized


def test_annotation_only_scalar_override_survives_strawberry_finalization():
    """End-to-end: the consumer annotation surfaces in the GraphQL schema as ``Int!``."""

    class CategoryType(DjangoType):
        description: int

        class Meta:
            model = Category
            fields = ("id", "name", "description")

    finalize_django_types()

    @strawberry.type
    class Query:
        @strawberry.field
        def category(self) -> CategoryType:
            return Category(id=1, name="x", description=42)

    schema = strawberry.Schema(query=Query)
    query = '{ __type(name: "CategoryType") { fields { name type { kind name ofType { kind name } } } } }'
    result = schema.execute_sync(query)
    assert result.errors is None, result.errors
    fields = {f["name"]: f["type"] for f in result.data["__type"]["fields"]}
    description_type = fields["description"]
    assert description_type["kind"] == "NON_NULL"
    assert description_type["ofType"]["name"] == "Int"


# ---------------------------------------------------------------------------
# ``field: auto`` - declare-but-infer (the fifth corner of the override surface).
# ---------------------------------------------------------------------------


def test_auto_annotation_synthesizes_model_inferred_scalar_type():
    """``name: auto`` keeps the field selected but infers its type from the model."""

    class CategoryType(DjangoType):
        name: auto

        class Meta:
            model = Category
            fields = ("id", "name", "description")

    finalize_django_types()

    # Resolved to the model-inferred scalar, not the ``auto`` sentinel / ``Any``.
    assert CategoryType.__annotations__["name"] is str
    assert _strawberry_field(CategoryType, "name").type is str


def test_auto_annotation_is_not_a_consumer_override():
    """An ``auto`` field routes back into synthesis, not the consumer-authored union."""

    class CategoryType(DjangoType):
        name: auto

        class Meta:
            model = Category
            fields = ("id", "name", "description")

    definition = CategoryType.__django_strawberry_definition__
    assert "name" not in definition.consumer_annotated_scalar_fields
    assert "name" not in definition.consumer_authored_fields


def test_auto_annotation_emits_synthesized_annotation():
    """Unlike a real override, an ``auto`` field IS present in the synthesized dict."""

    class CategoryType(DjangoType):
        name: auto

        class Meta:
            model = Category
            fields = ("id", "name", "description")

    definition = CategoryType.__django_strawberry_definition__
    synthesized, _pending = _build_annotations(
        CategoryType,
        definition.selected_fields,
        source_model=Category,
        field_map=definition.field_map,
        consumer_authored_fields=definition.consumer_authored_fields,
        interfaces=definition.interfaces,
    )
    assert synthesized["name"] is str


def test_auto_annotation_survives_strawberry_finalization():
    """End-to-end: ``name: auto`` surfaces in the schema as the inferred ``String!``."""

    class CategoryType(DjangoType):
        name: auto

        class Meta:
            model = Category
            fields = ("id", "name", "description")

    finalize_django_types()

    @strawberry.type
    class Query:
        @strawberry.field
        def category(self) -> CategoryType:
            return Category(id=1, name="x", description="y")

    schema = strawberry.Schema(query=Query)
    query = '{ __type(name: "CategoryType") { fields { name type { kind name ofType { kind name } } } } }'
    result = schema.execute_sync(query)
    assert result.errors is None, result.errors
    fields = {f["name"]: f["type"] for f in result.data["__type"]["fields"]}
    name_type = fields["name"]
    assert name_type["kind"] == "NON_NULL"
    assert name_type["ofType"]["name"] == "String"


def test_auto_annotation_on_relation_field_synthesizes_relation():
    """``items: auto`` defers the reverse-FK relation to finalization like bare selection."""

    class CategoryType(DjangoType):
        items: auto

        class Meta:
            model = Category
            fields = ("id", "name", "items")

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

    definition = CategoryType.__django_strawberry_definition__
    assert "items" not in definition.consumer_annotated_relation_fields
    assert "items" not in definition.consumer_authored_fields

    finalize_django_types()

    assert CategoryType.__annotations__["items"] == list[ItemType]


def test_auto_annotation_on_unselected_field_raises():
    """``auto`` never adds a field: an unselected ``auto`` name is rejected at creation."""

    with pytest.raises(ConfigurationError, match=r"annotated `auto` but not selected"):

        class CategoryType(DjangoType):
            description: auto

            class Meta:
                model = Category
                fields = ("id", "name")


def test_auto_annotation_combined_with_assigned_field_raises():
    """``auto`` (infer type) cannot coexist with an assigned resolver/type."""

    with pytest.raises(ConfigurationError, match="cannot combine with an assigned resolver"):

        class CategoryType(DjangoType):
            description: auto = strawberry.field(resolver=lambda root: 0)

            class Meta:
                model = Category
                fields = ("id", "name", "description")


# ---------------------------------------------------------------------------
# Converter-bypass regressions (Decision 7a).
# ---------------------------------------------------------------------------


def test_annotation_override_of_unsupported_scalar_field_type_is_allowed():
    """A consumer ``myfield: str`` annotation lets an unsupported scalar build."""

    class UnsupportedFieldOwner(models.Model):
        myfield = _FakeUnsupportedField()

        class Meta:
            app_label = "test_spec015_unsupported"

    # Baseline: without the override, convert_scalar's MRO walk fails.
    with pytest.raises(ConfigurationError):

        class BaselineType(DjangoType):
            class Meta:
                model = UnsupportedFieldOwner
                fields = ("myfield",)

    class UnsupportedOwnerType(DjangoType):
        myfield: str

        class Meta:
            model = UnsupportedFieldOwner
            fields = ("myfield",)

    definition = UnsupportedOwnerType.__django_strawberry_definition__
    assert "myfield" in definition.consumer_annotated_scalar_fields
    finalize_django_types()


def test_annotation_override_of_grouped_choices_field_is_allowed():
    """A consumer ``status: str`` annotation bypasses grouped-choices rejection."""

    class GroupedChoiceOwner(models.Model):
        status = models.CharField(
            max_length=32,
            choices=[("group1", [("a", "A"), ("b", "B")])],
        )

        class Meta:
            app_label = "test_spec015_grouped_choices"

    class GroupedChoiceOwnerType(DjangoType):
        status: str

        class Meta:
            model = GroupedChoiceOwner
            fields = ("status",)

    finalize_django_types()
    assert registry.get_enum(GroupedChoiceOwner, "status") is None


def test_annotation_override_does_not_populate_shared_enum_cache_for_co_resident_types():
    """One overriding + one non-overriding type share enum from the non-overriding side alone."""

    class CoResidentChoiceOwner(models.Model):
        status = models.CharField(max_length=32, choices=[("a", "A"), ("b", "B")])

        class Meta:
            app_label = "test_spec015_co_resident"

    class OverrideType(DjangoType):
        status: str

        class Meta:
            model = CoResidentChoiceOwner
            primary = True
            fields = ("status",)

    class NonOverrideType(DjangoType):
        class Meta:
            model = CoResidentChoiceOwner
            fields = ("status",)

    finalize_django_types()

    cached = registry.get_enum(CoResidentChoiceOwner, "status")
    assert cached is not None

    @strawberry.type
    class Query:
        @strawberry.field
        def override(self) -> OverrideType:
            return CoResidentChoiceOwner(status="a")

        @strawberry.field
        def non_override(self) -> NonOverrideType:
            return CoResidentChoiceOwner(status="a")

    schema = strawberry.Schema(query=Query)
    query = (
        '{ __type(name: "OverrideType") { fields { name type { kind name '
        "ofType { kind name } } } } "
        '__overrideTwo: __type(name: "NonOverrideType") { fields { name type '
        "{ kind name ofType { kind name } } } } }"
    )
    result = schema.execute_sync(query)
    assert result.errors is None, result.errors

    override_fields = {f["name"]: f["type"] for f in result.data["__type"]["fields"]}
    override_status = override_fields["status"]
    assert override_status["kind"] == "NON_NULL"
    assert override_status["ofType"]["name"] == "String"

    non_override_fields = {f["name"]: f["type"] for f in result.data["__overrideTwo"]["fields"]}
    non_override_status = non_override_fields["status"]
    assert non_override_status["kind"] == "NON_NULL"
    assert non_override_status["ofType"]["name"] == cached.__name__


# ---------------------------------------------------------------------------
# Relay collision tests (Decision 7) - five reject + six accept.
# ---------------------------------------------------------------------------


def test_consumer_id_annotation_on_relay_node_type_raises():
    """``id: int`` on a ``Meta.interfaces = (relay.Node,)`` type raises at class creation."""
    with pytest.raises(ConfigurationError) as exc_info:

        class CategoryNode(DjangoType):
            id: int

            class Meta:
                model = Category
                fields = ("id", "name")
                interfaces = (relay.Node,)

    msg = str(exc_info.value)
    assert "relay.NodeID" in msg
    assert "GlobalID" in msg


def test_consumer_id_annotation_on_direct_relay_node_subclass_raises():
    """``id: int`` on a direct ``relay.Node`` subclass raises (no ``Meta.interfaces``)."""
    with pytest.raises(ConfigurationError) as exc_info:

        class DirectRelayChild(DjangoType, relay.Node):
            id: int

            class Meta:
                model = Category
                fields = ("id", "name")

    msg = str(exc_info.value)
    assert "relay.NodeID" in msg
    assert "GlobalID" in msg


def test_consumer_id_assigned_strawberry_field_on_relay_node_type_raises():
    """Assigned ``id = strawberry.field(resolver=...)`` raises; message names the workarounds."""
    with pytest.raises(ConfigurationError) as exc_info:

        class CategoryNode(DjangoType):
            id = strawberry.field(resolver=lambda root: "x")

            class Meta:
                model = Category
                fields = ("id", "name")
                interfaces = (relay.Node,)

    msg = str(exc_info.value)
    assert "resolve_id" in msg
    assert "relay.NodeID" in msg
    assert ("display_id" in msg) or ("sibling field" in msg)


def test_consumer_id_unresolved_non_nodeid_string_on_relay_node_type_raises():
    """``id: "MissingType"`` (unresolved, non-NodeID) raises via the fail-soft regex reject."""
    with pytest.raises(ConfigurationError) as exc_info:

        class CategoryNode(DjangoType):
            id: "MissingType"  # noqa: F821 - deliberately unresolved

            class Meta:
                model = Category
                fields = ("id", "name")
                interfaces = (relay.Node,)

    msg = str(exc_info.value)
    assert "relay.NodeID" in msg
    assert "GlobalID" in msg


def test_consumer_id_typo_lookalike_nodeid_string_on_relay_node_type_raises():
    """Prefixed-substring lookalikes (e.g. ``"NotNodeID[int]"``) are rejected by the token regex."""
    with pytest.raises(ConfigurationError) as exc_info:

        class CategoryNodeNot(DjangoType):
            id: "NotNodeID[int]"  # noqa: F821 - token regex rejects this prefix

            class Meta:
                model = Category
                fields = ("id", "name")
                interfaces = (relay.Node,)

    msg = str(exc_info.value)
    assert "relay.NodeID" in msg
    assert "GlobalID" in msg

    with pytest.raises(ConfigurationError) as exc_info:

        class CategoryNodeMy(DjangoType):
            id: "MyNodeID[int]"  # noqa: F821 - token regex rejects this prefix

            class Meta:
                model = Category
                fields = ("id", "name")
                interfaces = (relay.Node,)

    msg = str(exc_info.value)
    assert "relay.NodeID" in msg
    assert "GlobalID" in msg


def test_consumer_id_relay_nodeid_annotation_on_relay_node_type_is_accepted():
    """``id: relay.NodeID[int]`` (direct form) is the documented escape hatch."""

    class CategoryNode(DjangoType):
        id: relay.NodeID[int]

        class Meta:
            model = Category
            fields = ("id", "name")
            interfaces = (relay.Node,)

    finalize_django_types()

    @strawberry.type
    class Query:
        @strawberry.field
        def category(self) -> CategoryNode:
            return Category(id=1, name="x")

    strawberry.Schema(query=Query)


def test_consumer_id_resolved_string_relay_nodeid_annotation_on_relay_node_type_is_accepted_end_to_end():
    """``id: "relay.NodeID[int]"`` with ``relay`` importable in module scope succeeds end-to-end."""

    class CategoryNode(DjangoType):
        id: "relay.NodeID[int]"

        class Meta:
            model = Category
            fields = ("id", "name")
            interfaces = (relay.Node,)

    finalize_django_types()

    @strawberry.type
    class Query:
        @strawberry.field
        def category(self) -> CategoryNode:
            return Category(id=1, name="x")

    schema = strawberry.Schema(query=Query)
    query = '{ __type(name: "CategoryNode") { fields { name type { kind name ofType { kind name } } } } }'
    result = schema.execute_sync(query)
    assert result.errors is None, result.errors
    fields = {f["name"]: f["type"] for f in result.data["__type"]["fields"]}
    id_type = fields["id"]
    assert id_type["kind"] == "NON_NULL"
    assert id_type["ofType"]["name"] == "ID"


def test_consumer_id_unresolved_nodeid_shaped_string_on_relay_node_type_passes_guard_only():
    """Unresolved-but-NodeID-shaped string passes the guard; downstream resolution is consumer's."""
    stub_name = f"spec015_unresolved_relay_stub_{uuid.uuid4().hex}"
    sys.modules[stub_name] = types.ModuleType(stub_name)
    assert "relay" not in sys.modules[stub_name].__dict__
    try:

        def _body(ns):
            ns["__module__"] = stub_name
            ns["__annotations__"] = {"id": "relay.NodeID[int]"}

            class _Meta:
                model = Category
                interfaces = (relay.Node,)

            ns["Meta"] = _Meta

        types.new_class("UnresolvedRelayChild", (DjangoType,), {}, _body)
    finally:
        sys.modules.pop(stub_name, None)
        registry.clear()


def test_consumer_id_resolved_relay_nodeid_with_unresolved_sibling_annotation_is_accepted():
    """Resolved ``id: relay.NodeID[int]`` + unresolved sibling annotation is accepted."""

    class CategoryNode(DjangoType):
        id: relay.NodeID[int]
        items: list["AdminItemType"]  # noqa: F821 - deliberately unresolved sibling

        class Meta:
            model = Category
            fields = ("id", "name", "items")
            interfaces = (relay.Node,)

    # Class creation succeeded - the fail-soft annotation walk accepts the
    # directly-resolved NodeID-marked id even when another annotation on
    # the same class fails to resolve.
    assert CategoryNode is not None


def test_consumer_non_id_scalar_override_on_relay_node_type_is_accepted():
    """A non-``id`` scalar override on a Relay-Node-shaped type does not collide with ``Node.id``."""

    class CategoryNode(DjangoType):
        description: int

        class Meta:
            model = Category
            fields = ("id", "name", "description")
            interfaces = (relay.Node,)

    assert CategoryNode.__annotations__["description"] is int


def test_inherited_id_annotation_on_relay_node_subclass_is_handled_by_pk_suppression():
    """Inherited ``id: int`` slips past the guard; pk-suppression keeps Strawberry happy."""

    class BaseWithId(DjangoType):
        id: int

    class ChildRelayType(BaseWithId):
        class Meta:
            model = Category
            fields = ("id", "name")
            interfaces = (relay.Node,)

    # Guard did not fire - the child's own __annotations__ has no "id" key
    # because Python does not promote inherited annotations into the
    # subclass's dict.
    # Raw ``__dict__`` on purpose: the subclass's OWN dict is the subject here.
    assert "id" not in dict(
        ChildRelayType.__dict__.get("__annotations__", {}),  # noqa: RUF063, RUF100
    )

    finalize_django_types()

    @strawberry.type
    class Query:
        @strawberry.field
        def category(self) -> ChildRelayType:
            return Category(id=1, name="x")

    schema = strawberry.Schema(query=Query, types=[ChildRelayType])
    query = '{ __type(name: "ChildRelayType") { fields { name type { kind name ofType { kind name } } } } }'
    result = schema.execute_sync(query)
    assert result.errors is None, result.errors
    fields = {f["name"]: f["type"] for f in result.data["__type"]["fields"]}
    id_type = fields["id"]
    assert id_type["kind"] == "NON_NULL"
    assert id_type["ofType"]["name"] == "ID"


def test_scalar_field_class_attribute_shadowing_raises():
    """Unsupported class attributes cannot silently shadow scalar fields either.

    Pins the same ``cls.__name__`` attribution as the relation case so a
    cosmetic refactor of the message can't silently switch back to the Django
    model's name.
    """
    with pytest.raises(
        ConfigurationError,
        match=r"CategoryType\.name shadows a Django scalar field",
    ):

        class CategoryType(DjangoType):
            name = 42

            class Meta:
                model = Category
                fields = ("id", "name")


def test_same_module_string_forward_reference_annotation_survives_finalization():
    """A same-module string relation override is resolved by Strawberry after finalization."""

    class StringItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

    globals()["StringItemType"] = StringItemType
    try:

        class StringCategoryType(DjangoType):
            items: list["StringItemType"]

            class Meta:
                model = Category
                fields = ("id", "name", "items")

        globals()["StringCategoryType"] = StringCategoryType
        finalize_django_types()

        items_field = _strawberry_field(StringCategoryType, "items")
        assert items_field.base_resolver is not None
        assert items_field.base_resolver.wrapped_func.__name__ == "resolve_items"
    finally:
        globals().pop("StringCategoryType", None)
        globals().pop("StringItemType", None)


# ---------------------------------------------------------------------------
# Ambiguity-audit interaction (spec-018-meta_primary-0_0_6.md)
# with relation resolution. The raise-at-finalize and once-per-build
# regression tests live in ``tests/test_registry.py``; this file hosts the
# audit-success paths and the audit-vs-unresolved-target ordering test.
# ---------------------------------------------------------------------------


def test_finalize_succeeds_when_model_has_multiple_types_one_primary():
    """``finalize_django_types`` succeeds when one of the multi-type entries is primary."""

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

    class AdminItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")
            primary = True

    finalize_django_types()

    assert registry.is_finalized() is True
    assert registry.primary_for(Item) is AdminItemType


def test_finalize_succeeds_when_model_has_single_type_no_primary():
    """Backward-compat: a single registered type with no primary still finalizes cleanly."""

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

    finalize_django_types()

    assert registry.is_finalized() is True
    assert registry.primary_for(Item) is None
    assert registry.get(Item) is ItemType


def test_finalize_ambiguity_error_fires_before_unresolved_target_error():
    """The ambiguity audit runs before pending-relation resolution.

    Sets up both conditions in one test: two ``DjangoType`` subclasses on
    ``Item`` (neither primary) AND a relation to ``Category`` whose
    ``DjangoType`` is not registered (would otherwise raise the
    unresolved-target error). The audit MUST raise first.
    """

    class ItemTypeA(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    class ItemTypeB(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    with pytest.raises(ConfigurationError) as exc_info:
        finalize_django_types()

    msg = str(exc_info.value)
    assert "Models with multiple registered DjangoType subclasses and no primary" in msg
    assert "Cannot finalize Django types" not in msg
    assert "no registered DjangoType" not in msg


def test_filterset_class_resolves_across_module_boundary():
    """``Meta.filterset_class`` from two sibling modules resolves under one finalize call.

    Imports both fixture modules under fresh ``sys.modules`` keys so the
    module bodies (which declare ``DjangoType`` plus ``FilterSet`` and
    register them against the global registry) run inside this test
    after the autouse-fixture ``registry.clear()``. Pins the spec-027
    contract that the finalizer's filter-binding pass works across
    module boundaries without ``ImportError``.
    """
    # Drop any previously-imported fixture module objects so the next
    # import triggers a fresh execution that re-registers under the
    # cleared registry. ``importlib.reload`` would leak the prior
    # module's registered classes against the registry.
    for stem in ("tests.types.fixtures.shelf_module", "tests.types.fixtures.branch_module"):
        sys.modules.pop(stem, None)

    from tests.types.fixtures import branch_module, shelf_module

    finalize_django_types()

    assert registry.is_finalized() is True
    branch_def = branch_module.BranchType.__django_strawberry_definition__
    shelf_def = shelf_module.ShelfType.__django_strawberry_definition__
    assert branch_def.filterset_class is branch_module.BranchFilter
    assert shelf_def.filterset_class is shelf_module.ShelfFilter
    # Owner binding from finalize phase 2.5 wires the back-reference.
    assert branch_module.BranchFilter._owner_definition is branch_def
    assert shelf_module.ShelfFilter._owner_definition is shelf_def
