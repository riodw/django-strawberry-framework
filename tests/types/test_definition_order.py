"""Acceptance tests for definition-order-independent DjangoType relations."""

import sys
import types
import uuid

import pytest
import strawberry
from apps.library.models import Book, Genre, MembershipCard, Patron, Shelf
from apps.products.models import Category, Entry, Item, Property
from django.db import models
from strawberry import relay

from django_strawberry_framework import DjangoType, finalize_django_types
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.registry import registry
from django_strawberry_framework.types.base import _build_annotations


class _FakeUnsupportedField(models.Field):
    """One-line Django Field subclass with no SCALAR_MAP match.

    Pins the unsupported-field-type bypass test for spec-015 Slice 1
    Decision 7a — the consumer's annotation override is a recourse
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
        field for field in type_cls.__strawberry_definition__.fields if field.python_name == field_name
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
    # under spec-014 Slice 4's always-defer contract, regardless of whether
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
    # under spec-014 Slice 4's always-defer contract.
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
            fields = ("id", "title", "shelf", "genres")

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
            fields = ("id", "name", "items", "properties")

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category", "entries")

    class EntryType(DjangoType):
        class Meta:
            model = Entry
            fields = ("id", "value", "item", "property")

    class PropertyType(DjangoType):
        class Meta:
            model = Property
            fields = ("id", "name", "category", "entries")

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


def test_decorator_relation_field_override_routes_schema_query_through_consumer_resolver():
    """A decorator override survives finalization and executes inside a schema query."""

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

    class CategoryType(DjangoType):
        @strawberry.field
        def items(self) -> list[ItemType]:
            return [Item(id=1, name="manual")]

        class Meta:
            model = Category
            fields = ("id", "name", "items")

    @strawberry.type
    class Query:
        @strawberry.field
        def categories(self) -> list[CategoryType]:
            return [Category(id=1, name="category")]

    finalize_django_types()
    schema = strawberry.Schema(query=Query)
    result = schema.execute_sync("{ categories { items { name } } }")

    assert result.errors is None
    assert result.data == {"categories": [{"items": [{"name": "manual"}]}]}


def test_relation_field_class_attribute_shadowing_raises():
    """Unsupported class attributes cannot silently shadow relation fields."""
    with pytest.raises(ConfigurationError, match="shadows a Django relation field"):

        class CategoryType(DjangoType):
            items = None

            class Meta:
                model = Category
                fields = ("id", "name", "items")


def test_assigned_scalar_field_override_keeps_consumer_resolver():
    """A ``strawberry.field(resolver=...)`` assigned to a scalar column wins.

    Pins the Medium fix from ``rev-types__base.md``: previously
    ``_consumer_assigned_relation_fields`` only collected relation
    names, so a consumer assigning a ``StrawberryField`` to a scalar
    column (e.g. ``name``) was silently overwritten by the auto-
    synthesized ``str`` annotation. The widened guard collects scalar
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
    # assignment — the field name does not appear in the generated
    # annotations dict.
    assert "name" not in CategoryType.__annotations__

    finalize_django_types()
    name_field = _strawberry_field(CategoryType, "name")
    assert name_field.base_resolver is not None
    assert name_field.base_resolver.wrapped_func.__qualname__.endswith("CategoryType.name")


# ---------------------------------------------------------------------------
# Spec-015 Slice 1: annotation-only scalar override matrix completion.
#
# Four core override tests pin the new annotation-only scalar override
# path; four converter-bypass tests pin Decision 7a's "consumer is
# authoritative" contract; eleven Relay-collision tests pin Decision 7's
# H1 guard (five reject + six accept).
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
# Relay collision tests (Decision 7) — five reject + six accept.
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
            id: "MissingType"  # noqa: F821 — deliberately unresolved

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
            id: "NotNodeID[int]"  # noqa: F821 — token regex rejects this prefix

            class Meta:
                model = Category
                fields = ("id", "name")
                interfaces = (relay.Node,)

    msg = str(exc_info.value)
    assert "relay.NodeID" in msg
    assert "GlobalID" in msg

    with pytest.raises(ConfigurationError) as exc_info:

        class CategoryNodeMy(DjangoType):
            id: "MyNodeID[int]"  # noqa: F821 — token regex rejects this prefix

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
        items: list["AdminItemType"]  # noqa: F821 — deliberately unresolved sibling

        class Meta:
            model = Category
            fields = ("id", "name", "items")
            interfaces = (relay.Node,)

    # Class creation succeeded — the rev6 H1 fail-soft fix accepts the
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

    # Guard did not fire — the child's own __annotations__ has no "id" key
    # because Python does not promote inherited annotations into the
    # subclass's dict.
    assert "id" not in dict(ChildRelayType.__dict__.get("__annotations__", {}))

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
    """Unsupported class attributes cannot silently shadow scalar fields either."""
    with pytest.raises(ConfigurationError, match="shadows a Django scalar field"):

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
# Slice 3 (spec-014-meta_primary-0_0_6.md) — ambiguity-audit interaction
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
