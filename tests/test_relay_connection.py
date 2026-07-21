"""Relation-as-Connection tests for synthesis, pagination, optimized windows, fallbacks, and cleanup.

Covers the ``Meta.relation_shapes`` Phase-2.5 synthesis surface
(``docs/spec-032-full_relay-0_0_9.md`` Decisions 6/7; Decision 11 pins the
card-named two-file split). The ``Meta``-key *validation* tests sit with the
other Meta validation in ``tests/types/test_base.py``. These stay package-side
because they assert what a live query cannot: finalization
``ConfigurationError``s never appear in the example schema, and the
fast-path / windowed-prefetch tests pin SQL shape, query counts, cached-plan
identity, and the per-parent fallback - the
``examples/fakeshop/test_query/README.md`` live-HTTP-first rule's
"keep when it asserts query planning / query count / construction-time
validation" clause. The shipped live nested-connection proofs (the
synthesized ``library`` relation connections and ``allLibraryGenresConnection``)
run in ``examples/fakeshop/test_query/test_library_api.py``.

Now that ``033`` has landed, the optimizer plans the synthesized connections
into windowed prefetches, so the fast-path tests here pin SQL shape and query
count; the optimizer-less behavior tests still pin rows / pagination /
argument presence on the per-parent fallback.
"""

from types import SimpleNamespace

import pytest
import strawberry
from apps.library.models import Book, Branch, Genre, Loan, Shelf
from apps.products import services
from apps.products.models import Category, Item, Property
from django.db import connection as db_connection
from django.db import models as djmodels
from django.http import HttpRequest
from strategy_schemas import make_django_type
from strawberry import relay

from django_strawberry_framework import (
    DjangoListField,
    DjangoOptimizerExtension,
    DjangoType,
    OptimizerHint,
    finalize_django_types,
    strawberry_config,
)
from django_strawberry_framework.connection import (
    _connection_type_cache,
    _connection_type_for,
)
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.filters import FilterSet, filter_input_type
from django_strawberry_framework.orders import OrderSet
from django_strawberry_framework.registry import registry
from django_strawberry_framework.types.finalizer import _register_relation_connection_teardown


def _path(*keys):
    """Build a graphql-core-style linked response path (integer keys are list indexes)."""
    path = None
    for key in keys:
        path = type("Path", (), {"key": key, "prev": path})()
    return path


@pytest.fixture(autouse=True)
def _isolate_global_registry(isolate_global_registry):
    """Every test here declares fresh ``DjangoType`` classes - opt the module
    into the shared registry/connection-cache isolation (``tests/conftest.py``)."""


# The shared declaration core (``examples/fakeshop/strategy_schemas.py``)
# already matches this module's historical signature exactly.
_make_type = make_django_type


def _schema_with_root(declaring_type, *, field_name="objs"):
    """Finalize and build a schema exposing ``field_name: [declaring_type!]!``.

    The root field lists every row of the declaring type's model in pk order
    so nested relation-connection queries have a deterministic parent set.
    """
    finalize_django_types()
    model = declaring_type.__django_strawberry_definition__.model

    def _resolver() -> list[declaring_type]:
        return list(model._default_manager.all().order_by("pk"))

    query_cls = strawberry.type(
        type(
            "Query",
            (),
            {
                "__annotations__": {field_name: list[declaring_type]},
                field_name: strawberry.field(resolver=_resolver),
            },
        ),
    )
    return strawberry.Schema(query=query_cls, config=strawberry_config())


def _field_args_block(sdl, field_name):
    """Return the SDL argument block of ``field_name``.

    The Relay pagination args carry descriptions, so graphql-core prints a
    connection field's arguments one per line - a single-line substring check
    cannot see them. Slices from ``<field_name>(`` to the closing ``): ``.
    """
    _, _, rest = sdl.partition(f"{field_name}(")
    block, _, _ = rest.partition("): ")
    return block


def _seed_library_books(titles, *, genre_name="fiction"):
    """Create one genre linked to one book per title (library inline-create rule)."""
    branch = Branch.objects.create(name="central")
    shelf = Shelf.objects.create(code="A1", branch=branch)
    genre = Genre.objects.create(name=genre_name)
    books = []
    for title in titles:
        book = Book.objects.create(title=title, shelf=shelf)
        book.genres.add(genre)
        books.append(book)
    return genre, books


# =============================================================================
# Default "both": connection siblings per eligible relation kind
# =============================================================================


def test_default_both_synthesizes_reverse_fk_connection_sibling():
    """A reverse-FK relation gains ``<field>Connection`` alongside the list field.

    No ``relation_shapes`` key: the implicit ``"both"`` default keeps
    ``items: [ItemType!]!`` and adds ``itemsConnection``. The bare connection
    (no target ``totalCount`` opt-in) carries no ``totalCount`` field - the
    type-level counter-fixture for the sidecar/totalCount test below.
    """
    _make_type("ItemType", Item, ("id", "name", "category"))
    category_type = _make_type("CategoryType", Category, ("id", "name", "items"))

    sdl = str(_schema_with_root(category_type))
    assert "items: [ItemType" in sdl
    assert "itemsConnection(" in sdl
    assert "totalCount" not in sdl


def test_default_both_synthesizes_m2m_connection_siblings():
    """Forward AND reverse M2M relations gain connection siblings under the default.

    ``Book.genres`` (forward M2M) and ``Genre.books`` (reverse M2M) both get
    ``<field>Connection`` alongside their list fields - with the reverse-FK
    case above, all three spec-named eligible kinds are pinned.
    """
    _make_type("BookType", Book, ("id", "title", "genres"))
    genre_type = _make_type("GenreType", Genre, ("id", "name", "books"))

    sdl = str(_schema_with_root(genre_type))
    assert "books: [BookType" in sdl
    assert "booksConnection(" in sdl
    assert "genres: [GenreType" in sdl
    assert "genresConnection(" in sdl


@pytest.mark.django_db(transaction=True)
def test_reverse_fk_without_related_name_resolves_list_and_connection():
    """A reverse FK with NO ``related_name`` resolves on both relation surfaces.

    Round-4 review S3: for such a relation, Django's ``ForeignObjectRel.name``
    is the related QUERY name (``"plainbook"``) while the instance attribute
    is ``get_accessor_name()`` (``"plainbook_set"``). Both the Phase-2 list
    resolver and the synthesized connection resolver used to
    ``getattr(root, field.name)`` and raised ``AttributeError`` - invisible to
    CI because every fakeshop fixture sets ``related_name``. Instance access
    now goes through ``utils.relations.instance_accessor``; the GraphQL field
    names stay query-name-derived (``plainbook`` / ``plainbookConnection``).

    Uses the ``managed=False`` + manual ``schema_editor`` pattern from
    ``tests/optimizer/test_relay_id_projection.py``; the app label must be an
    INSTALLED app (here ``products``) because Django only wires reverse
    relations into ``_meta.get_fields()`` for installed apps.
    """

    class PlainAuthor(djmodels.Model):
        name = djmodels.CharField(max_length=32)

        class Meta:
            app_label = "products"
            managed = False

    class PlainBook(djmodels.Model):
        title = djmodels.CharField(max_length=32)
        author = djmodels.ForeignKey(PlainAuthor, on_delete=djmodels.CASCADE)  # no related_name

        class Meta:
            app_label = "products"
            managed = False

    rel = PlainAuthor._meta.get_field("plainbook")
    assert rel.get_accessor_name() == "plainbook_set"  # the S3 split this test pins

    with db_connection.schema_editor() as schema_editor:
        schema_editor.create_model(PlainAuthor)
        schema_editor.create_model(PlainBook)
    try:
        _make_type("PlainBookType", PlainBook, ("id", "title"))
        author_type = _make_type("PlainAuthorType", PlainAuthor, ("id", "name", "plainbook"))
        schema = _schema_with_root(author_type)

        author = PlainAuthor.objects.create(name="a1")
        PlainBook.objects.create(title="b1", author=author)

        result = schema.execute_sync(
            "{ objs { name plainbook { title } "
            "plainbookConnection { edges { node { title } } } } }",
        )
        assert result.errors is None
        assert result.data["objs"] == [
            {
                "name": "a1",
                "plainbook": [{"title": "b1"}],
                "plainbookConnection": {"edges": [{"node": {"title": "b1"}}]},
            },
        ]
    finally:
        with db_connection.schema_editor() as schema_editor:
            schema_editor.delete_model(PlainBook)
            schema_editor.delete_model(PlainAuthor)


# =============================================================================
# Explicit shapes: "connection" / "list" narrowing
# =============================================================================


@pytest.mark.django_db
def test_shape_connection_suppresses_list():
    """``"connection"`` removes the list field; the connection resolves rows."""
    services.seed_data(2)
    _make_type("ItemType", Item, ("id", "name", "category"))
    category_type = _make_type(
        "CategoryType",
        Category,
        ("id", "name", "items"),
        meta_extra={"relation_shapes": {"items": "connection"}},
    )

    schema = _schema_with_root(category_type)
    sdl = str(schema)
    assert "itemsConnection(" in sdl
    assert "items: [" not in sdl

    result = schema.execute_sync(
        "{ objs { itemsConnection { edges { node { name } } } } }",
    )
    assert result.errors is None
    total_edges = sum(
        len(category["itemsConnection"]["edges"]) for category in result.data["objs"]
    )
    assert total_edges == Item.objects.count()


def test_shape_list_suppresses_connection():
    """``"list"`` synthesizes nothing - today's shipped shape stays as-is."""
    _make_type("ItemType", Item, ("id", "name", "category"))
    category_type = _make_type(
        "CategoryType",
        Category,
        ("id", "name", "items"),
        meta_extra={"relation_shapes": {"items": "list"}},
    )

    sdl = str(_schema_with_root(category_type))
    assert "items: [ItemType" in sdl
    assert "itemsConnection" not in sdl


# =============================================================================
# Non-Node targets: silent list-only default vs explicit fail-loud
# =============================================================================


def test_non_node_target_silently_list_only():
    """A non-Node target degrades silently to list-only under the implicit default.

    Decision 6: existing valid schemas (a Node-shaped declaring type over a
    registered non-Node target) must keep building when this card lands.
    """
    _make_type("LoanType", Loan, ("id", "note"), node=False)
    book_type = _make_type("BookType", Book, ("id", "title", "loans"))

    sdl = str(_schema_with_root(book_type))
    assert "loans: [LoanType" in sdl
    assert "loansConnection" not in sdl


@pytest.mark.parametrize("shape", ["connection", "both"])
def test_non_node_target_explicit_raises(shape):
    """An explicit ``"connection"`` / ``"both"`` over a non-Node target raises at finalize."""
    _make_type("LoanType", Loan, ("id", "note"), node=False)
    _make_type(
        "BookType",
        Book,
        ("id", "title", "loans"),
        meta_extra={"relation_shapes": {"loans": shape}},
    )

    with pytest.raises(ConfigurationError) as excinfo:
        finalize_django_types()
    message = str(excinfo.value)
    assert "BookType.Meta.relation_shapes['loans']" in message
    assert "LoanType is not Relay-Node-shaped" in message


# =============================================================================
# Consumer overrides and name collisions
# =============================================================================


def test_consumer_overridden_relation_skipped():
    """A consumer-authored relation is never upgraded under the implicit default.

    No ``relation_shapes`` entry for ``items``: the consumer annotation owns
    the field's shape, so the SDL carries the consumer's list field and no
    ``itemsConnection`` (an explicit entry would have raised at type
    creation - pinned in ``tests/types/test_base.py``).
    """
    item_type = _make_type("ItemType", Item, ("id", "name", "category"))
    category_type = _make_type(
        "CategoryType",
        Category,
        ("id", "name", "items"),
        namespace_extra={"__annotations__": {"items": list[item_type]}},
    )

    sdl = str(_schema_with_root(category_type))
    assert "items: [ItemType" in sdl
    assert "itemsConnection" not in sdl


def test_generated_name_collision_raises():
    """A consumer attribute named ``<field>_connection`` raises with the opt-out."""
    _make_type("ItemType", Item, ("id", "name", "category"))
    _make_type(
        "CategoryType",
        Category,
        ("id", "name", "items"),
        namespace_extra={"__annotations__": {"items_connection": str}},
    )

    with pytest.raises(ConfigurationError) as excinfo:
        finalize_django_types()
    message = str(excinfo.value)
    assert "'items_connection'" in message
    assert 'relation_shapes = {"items": "list"}' in message


def test_generated_name_graphql_camel_collision_raises():
    """A camelCase consumer attribute collides on the GraphQL surface (Revision 3 P3).

    ``itemsConnection`` and the generated ``items_connection`` are distinct
    Python names but the SAME default-camel-cased GraphQL name; the guard
    compares both surfaces and names both colliding identifiers.
    """
    _make_type("ItemType", Item, ("id", "name", "category"))
    _make_type(
        "CategoryType",
        Category,
        ("id", "name", "items"),
        namespace_extra={"__annotations__": {"itemsConnection": str}},
    )

    with pytest.raises(ConfigurationError) as excinfo:
        finalize_django_types()
    message = str(excinfo.value)
    assert "'items_connection'" in message
    assert "'itemsConnection'" in message
    assert 'relation_shapes = {"items": "list"}' in message


# =============================================================================
# Target-driven sidecar arguments + totalCount; visibility; pagination
# =============================================================================


def test_synthesized_connection_carries_sidecar_args_and_total_count():
    """The synthesized field carries the TARGET's sidecar args and ``totalCount`` opt-in.

    Type-level target-driven contract (Decision 6): ``ItemType`` declares
    ``filterset_class`` / ``orderset_class`` / ``connection`` so
    ``itemsConnection`` gets ``filter:`` / ``orderBy:`` arguments and a
    ``totalCount``-carrying connection type; ``PropertyType`` declares none,
    so ``propertiesConnection`` carries only the four Relay pagination args
    and no ``totalCount``.
    """

    class _ItemFilter(FilterSet):
        class Meta:
            model = Item
            fields = {"name": ["exact"]}

    class _ItemOrder(OrderSet):
        class Meta:
            model = Item
            fields = ["name"]

    _make_type(
        "ItemType",
        Item,
        ("id", "name", "category"),
        meta_extra={
            "filterset_class": _ItemFilter,
            "orderset_class": _ItemOrder,
            "connection": {"total_count": True},
        },
    )
    _make_type("PropertyType", Property, ("id", "name", "category"))
    category_type = _make_type(
        "CategoryType",
        Category,
        (
            "id",
            "name",
            "items",
            "properties",
        ),
    )

    sdl = str(_schema_with_root(category_type))
    items_args = _field_args_block(sdl, "itemsConnection")
    assert "filter:" in items_args
    assert "orderBy:" in items_args
    properties_args = _field_args_block(sdl, "propertiesConnection")
    assert "filter:" not in properties_args
    assert "orderBy:" not in properties_args
    # Only ItemType's connection type (the opt-in) carries totalCount.
    assert sdl.count("totalCount") == 1
    assert "ItemTypeConnection" in sdl


@pytest.mark.django_db
def test_synthesized_connection_runs_target_get_queryset():
    """The target's ``get_queryset`` visibility hook filters inside the nested connection."""
    _seed_library_books(["visible", "hidden"])

    def get_queryset(cls, queryset, info, **kwargs):
        return queryset.filter(title="visible")

    _make_type(
        "BookType",
        Book,
        ("id", "title", "genres"),
        namespace_extra={"get_queryset": classmethod(get_queryset)},
    )
    genre_type = _make_type("GenreType", Genre, ("id", "name", "books"))

    schema = _schema_with_root(genre_type)
    result = schema.execute_sync(
        "{ objs { booksConnection { edges { node { title } } } } }",
    )
    assert result.errors is None
    titles = [
        edge["node"]["title"]
        for genre in result.data["objs"]
        for edge in genre["booksConnection"]["edges"]
    ]
    assert titles == ["visible"]


@pytest.mark.django_db
def test_synthesized_connection_paginates():
    """``first:`` / ``pageInfo`` flow through the relation-manager-seeded pipeline.

    Behavior-only assertions (rows + ``pageInfo``) per the pre-``033``
    posture - the synthesized connection's optimizer plan is empty and no
    SQL shape is pinned.
    """
    _seed_library_books(["a", "b", "c"])
    _make_type("BookType", Book, ("id", "title", "genres"))
    genre_type = _make_type("GenreType", Genre, ("id", "name", "books"))

    schema = _schema_with_root(genre_type)
    result = schema.execute_sync(
        "{ objs { booksConnection(first: 2) {"
        " edges { node { title } } pageInfo { hasNextPage } } } }",
    )
    assert result.errors is None
    connection = result.data["objs"][0]["booksConnection"]
    assert [edge["node"]["title"] for edge in connection["edges"]] == ["a", "b"]
    assert connection["pageInfo"]["hasNextPage"] is True


@pytest.mark.django_db
def test_synthesized_connection_per_parent_query_cost(django_assert_num_queries):
    """Each parent row pays its own window query - the documented cost contract.

    Round-4 review minor: relation-seeded connections run per-parent (no
    cross-parent batching in the pre-``033`` posture), so a nested connection
    under an N-row parent list issues ``1 + N`` queries: the parent list, then
    one window query per parent (a ``totalCount`` selection would add one
    ``COUNT`` per parent on a countable target). Pinning the count documents
    the contract and surfaces any silent regression toward per-edge loading.
    """
    services.seed_data(2)
    _make_type("ItemType", Item, ("id", "name", "category"))
    category_type = _make_type("CategoryType", Category, ("id", "name", "items"))

    schema = _schema_with_root(category_type)
    parent_count = Category.objects.count()
    with django_assert_num_queries(1 + parent_count):
        result = schema.execute_sync(
            "{ objs { itemsConnection(first: 2) { edges { node { name } } } } }",
        )
    assert result.errors is None
    assert len(result.data["objs"]) == parent_count


# =============================================================================
# Partial-finalize re-entrancy
# =============================================================================


def test_synthesis_skips_already_attached_on_refinalize():
    """A rerun after a post-synthesis finalize failure skips the attached sibling.

    The re-entrancy marker path: the first ``finalize_django_types()`` attaches
    ``itemsConnection``, then raises in ``_bind_filtersets`` (an orphan
    ``filter_input_type`` reference, which runs AFTER the synthesis step).
    Wiring the orphan and re-finalizing must succeed - the rerun recognizes
    its own prior attachment via the marker instead of misreading it as a
    collision - and the SDL carries exactly one ``itemsConnection``.
    """

    class _PropertyFilter(FilterSet):
        class Meta:
            model = Property
            fields = {"name": ["exact"]}

    _make_type("ItemType", Item, ("id", "name", "category"))
    category_type = _make_type("CategoryType", Category, ("id", "name", "items"))
    filter_input_type(_PropertyFilter)  # Orphan: referenced but not wired.

    with pytest.raises(ConfigurationError, match="filter_input_type"):
        finalize_django_types()

    # Wire the orphan, then re-finalize through the schema builder.
    _make_type(
        "PropertyType",
        Property,
        ("id", "name"),
        node=False,
        meta_extra={"filterset_class": _PropertyFilter},
    )
    sdl = str(_schema_with_root(category_type))
    assert sdl.count("itemsConnection(") == 1


def test_connection_only_relation_stays_list_suppressed_on_refinalize():
    """A ``"connection"`` relation survives a partial-finalize rerun list-suppressed.

    The first ``finalize_django_types()`` synthesizes ``itemsConnection`` and
    removes the generated ``items`` list form, then raises in
    ``_bind_filtersets`` (an orphan ``filter_input_type``, which runs AFTER
    synthesis). On the rerun, Phase 2 must NOT reattach an unannotated ``items``
    resolver (it would otherwise survive: synthesis sees its own marker and
    skips before re-removing). The final SDL carries ``itemsConnection`` and no
    ``items`` field (spec-032 feedback P1).
    """

    class _PropertyFilter(FilterSet):
        class Meta:
            model = Property
            fields = {"name": ["exact"]}

    _make_type("ItemType", Item, ("id", "name", "category"))
    category_type = _make_type(
        "CategoryType",
        Category,
        ("id", "name", "items"),
        meta_extra={"relation_shapes": {"items": "connection"}},
    )
    filter_input_type(_PropertyFilter)  # Orphan: referenced but not wired.

    with pytest.raises(ConfigurationError, match="filter_input_type"):
        finalize_django_types()

    # Wire the orphan, then re-finalize through the schema builder.
    _make_type(
        "PropertyType",
        Property,
        ("id", "name"),
        node=False,
        meta_extra={"filterset_class": _PropertyFilter},
    )
    sdl = str(_schema_with_root(category_type))
    assert sdl.count("itemsConnection(") == 1
    assert "items: [" not in sdl


def test_registry_clear_preserves_replacement_for_synthesized_connection():
    """Identity-safe teardown leaves a later same-named consumer value untouched."""
    _make_type("ItemType", Item, ("id", "name", "category"))
    category_type = _make_type("CategoryType", Category, ("id", "name", "items"))
    finalize_django_types()

    replacement = object()
    category_type.items_connection = replacement
    registry.clear()

    assert category_type.items_connection is replacement


def test_relation_connection_teardown_restores_owned_annotations_in_place():
    """Teardown preserves the annotation-dict identity held by consumer tooling."""
    annotations = {"items": list[Item]}

    class CategoryType:
        __annotations__ = annotations

    field_obj = strawberry.field(resolver=lambda: None)
    CategoryType.items_connection = field_obj
    definition = SimpleNamespace(relation_connections={"items_connection": "items"})
    registry.register(Category, CategoryType)
    _register_relation_connection_teardown(
        CategoryType,
        definition,
        generated="items_connection",
        field_obj=field_obj,
        relation_name="items",
        shape="both",
        annotations=annotations,
        annotations_snapshot={"items": list[Item]},
        list_resolver=object(),
    )

    registry.unregister(CategoryType)

    assert CategoryType.__annotations__ is annotations
    assert CategoryType.__annotations__ == {"items": list[Item]}
    assert definition.relation_connections is None


def test_registry_clear_removes_synthesized_state_before_different_shape_rebuild():
    """A fresh same-named type rebuild cannot inherit the prior connection shape.

    The first lifecycle suppresses ``items`` in favor of ``itemsConnection``.
    ``registry.clear()`` removes the exact generated field and restores the
    resolved list annotation/resolver on the discarded class. A module-reload-
    shaped second lifecycle then declares same-named fresh classes with the
    explicit ``"list"`` shape and finalizes without a stale connection.
    """
    item_type = _make_type("ItemType", Item, ("id", "name", "category"))
    old_category_type = _make_type(
        "CategoryType",
        Category,
        ("id", "name", "items"),
        meta_extra={"relation_shapes": {"items": "connection"}},
    )
    finalize_django_types()
    old_definition = old_category_type.__django_strawberry_definition__

    assert "items_connection" in old_category_type.__dict__
    assert "items" not in old_category_type.__annotations__
    assert "items" not in old_category_type.__dict__

    registry.clear()

    assert "items_connection" not in old_category_type.__dict__
    assert "items_connection" not in old_category_type.__annotations__
    assert old_category_type.__annotations__["items"].__args__ == (item_type,)
    assert "items" in old_category_type.__dict__
    assert old_definition.relation_connections is None

    _make_type("ItemType", Item, ("id", "name", "category"))
    fresh_category_type = _make_type(
        "CategoryType",
        Category,
        ("id", "name", "items"),
        meta_extra={"relation_shapes": {"items": "list"}},
    )
    finalize_django_types()

    assert "items_connection" not in fresh_category_type.__dict__
    assert fresh_category_type.__django_strawberry_definition__.relation_connections is None


# =============================================================================
# spec-032 Slice 4 - cursor-contract conformance on the synthesized relation
# connection (Decision 9). The live PRIMARY matrix runs against the shipped
# root ``allLibraryGenresConnection``; this mirror exercises the same matrix
# through the relation-manager-seeded pipeline on a reverse-FK cardinality
# fixture (``Shelf.books``), parametrized over the implicit ``"both"`` default
# and the narrowed ``"connection"`` shape. These schemas run WITHOUT the
# optimizer (the per-parent pipeline baseline), so the assertions are
# behavior-only (rows, cursors, ``pageInfo``); the windowed SQL-shape pins live
# in the ``_genres_list_schema(optimizer=True)`` fast-path tests below.
# =============================================================================


def _shelf_books_connection_schema(shape):
    """Build the reverse-FK ``Shelf.books`` cardinality-fixture schema.

    ``shape == "connection"`` passes the explicit narrowing;
    ``shape == "both"`` passes no ``relation_shapes`` key so the implicit
    default path is the thing tested. Either way the nested field is
    ``booksConnection``.
    """
    _make_type("BookType", Book, ("id", "title"))
    shelf_type = _make_type(
        "ShelfType",
        Shelf,
        ("id", "code", "books"),
        meta_extra={"relation_shapes": {"books": shape}} if shape == "connection" else None,
    )
    return _schema_with_root(shelf_type)


def _books_connection(schema, args, selection):
    """Execute one nested ``booksConnection`` query; return the connection dict.

    Asserts the no-error property, so every caller pins at least
    query-succeeds; the single seeded shelf is the only root row.
    """
    suffix = f"({args})" if args else ""
    result = schema.execute_sync(
        f"{{ objs {{ booksConnection{suffix} {{ {selection} }} }} }}",
    )
    assert result.errors is None, result.errors
    return result.data["objs"][0]["booksConnection"]


@pytest.mark.django_db
@pytest.mark.parametrize("shape", ["both", "connection"])
def test_relation_connection_first_zero(shape):
    """``first: 0`` yields empty edges + well-formed ``pageInfo``.

    The Strawberry overfetch shape the live ``first: 0`` pin documents:
    rows exist past the zero window, so ``hasNextPage`` is true with a null
    ``endCursor`` (no edges).
    """
    _seed_library_books(["a", "b", "c"])
    schema = _shelf_books_connection_schema(shape)

    conn = _books_connection(
        schema,
        "first: 0",
        "edges { node { title } } pageInfo { hasNextPage endCursor }",
    )
    assert conn["edges"] == []
    assert conn["pageInfo"]["hasNextPage"] is True
    assert conn["pageInfo"]["endCursor"] is None


@pytest.mark.django_db
@pytest.mark.parametrize("shape", ["both", "connection"])
def test_relation_connection_first_overrun(shape):
    """``first: N`` past the remainder returns the actual remainder."""
    _seed_library_books(["a", "b", "c"])
    schema = _shelf_books_connection_schema(shape)

    conn = _books_connection(
        schema,
        "first: 10",
        "edges { node { title } } pageInfo { hasNextPage }",
    )
    assert [edge["node"]["title"] for edge in conn["edges"]] == ["a", "b", "c"]
    assert conn["pageInfo"]["hasNextPage"] is False


@pytest.mark.django_db
@pytest.mark.parametrize("shape", ["both", "connection"])
def test_relation_connection_stale_after_no_error(shape):
    """A deleted-row ``after`` cursor does NOT error (Revision 2 P1).

    Pins ONLY the no-error property - offset cursors encode a position, not
    row identity, so no skip / duplicate / next-row assertion is made.
    """
    _, books = _seed_library_books(
        [
            "a",
            "b",
            "c",
            "d",
        ],
    )
    schema = _shelf_books_connection_schema(shape)

    page_one = _books_connection(schema, "first: 2", "pageInfo { endCursor }")
    end_cursor = page_one["pageInfo"]["endCursor"]
    # Delete the row the cursor position points at (second in pk order).
    books[1].delete()

    # The helper's ``result.errors is None`` assertion IS the test.
    _books_connection(
        schema,
        f'first: 2, after: "{end_cursor}"',
        "edges { node { title } }",
    )


@pytest.mark.django_db
@pytest.mark.parametrize("shape", ["both", "connection"])
def test_relation_connection_first_and_last_rejected(shape):
    """``first`` + ``last`` together surface the shipped package guard error."""
    _seed_library_books(["a", "b", "c"])
    schema = _shelf_books_connection_schema(shape)

    result = schema.execute_sync(
        "{ objs { booksConnection(first: 1, last: 1) { edges { node { title } } } } }",
    )
    assert result.errors is not None
    assert "mutually exclusive" in str(result.errors[0])


@pytest.mark.django_db
@pytest.mark.parametrize("shape", ["both", "connection"])
def test_relation_connection_page_info_four_fields(shape):
    """All four ``pageInfo`` fields are correct across a forward page walk."""
    _seed_library_books(["a", "b", "c"])
    schema = _shelf_books_connection_schema(shape)
    selection = "edges { cursor } pageInfo { hasNextPage hasPreviousPage startCursor endCursor }"

    page_one = _books_connection(schema, "first: 2", selection)
    cursors = [edge["cursor"] for edge in page_one["edges"]]
    info_one = page_one["pageInfo"]
    assert info_one["hasNextPage"] is True
    assert info_one["hasPreviousPage"] is False
    assert info_one["startCursor"] == cursors[0]
    assert info_one["endCursor"] == cursors[1]

    page_two = _books_connection(
        schema,
        f'first: 2, after: "{info_one["endCursor"]}"',
        selection,
    )
    info_two = page_two["pageInfo"]
    assert info_two["hasNextPage"] is False
    assert info_two["hasPreviousPage"] is True


@pytest.mark.django_db
@pytest.mark.parametrize("shape", ["both", "connection"])
def test_relation_connection_has_next_page_when_edges_unrequested(shape):
    """A nested ``pageInfo``-only selection still computes ``hasNextPage``.

    Revision 6 P3: the observable inverse of an unrequested field - a
    windowed page reports true, an exact page reports false, with no
    ``edges`` selection in either query.
    """
    _seed_library_books(["a", "b", "c"])
    schema = _shelf_books_connection_schema(shape)

    windowed = _books_connection(schema, "first: 2", "pageInfo { hasNextPage }")
    assert windowed["pageInfo"]["hasNextPage"] is True

    exact = _books_connection(schema, "first: 3", "pageInfo { hasNextPage }")
    assert exact["pageInfo"]["hasNextPage"] is False


@pytest.mark.django_db
@pytest.mark.parametrize("shape", ["both", "connection"])
def test_relation_connection_backward_pagination_last_before(shape):
    """``last`` / ``before`` row identity through the relation-seeded pipeline."""
    _seed_library_books(
        [
            "a",
            "b",
            "c",
            "d",
            "e",
        ],
    )
    schema = _shelf_books_connection_schema(shape)

    tail = _books_connection(
        schema,
        "last: 2",
        "edges { node { title } } pageInfo { hasNextPage hasPreviousPage }",
    )
    assert [edge["node"]["title"] for edge in tail["edges"]] == ["d", "e"]
    assert tail["pageInfo"]["hasPreviousPage"] is True
    assert tail["pageInfo"]["hasNextPage"] is False

    full = _books_connection(schema, "first: 5", "edges { cursor node { title } }")
    last_row_cursor = full["edges"][-1]["cursor"]
    window = _books_connection(
        schema,
        f'last: 2, before: "{last_row_cursor}"',
        "edges { node { title } } pageInfo { hasNextPage hasPreviousPage }",
    )
    assert [edge["node"]["title"] for edge in window["edges"]] == ["c", "d"]
    # Rows exist on both sides of the window (overfetch sees "e"; slice
    # start > 0 sees "a" / "b").
    assert window["pageInfo"]["hasNextPage"] is True
    assert window["pageInfo"]["hasPreviousPage"] is True


# =============================================================================
# spec-033 Slice 2 - connection-class fast path (Decision 5). The walker's
# windowed prefetch (Slice 1) only lands on ``root`` when the PARENT queryset
# flows through ``DjangoOptimizerExtension``, so the fast-path schemas use a
# ``DjangoListField`` root (which the optimizer plans) with the extension
# installed. The existing ``_schema_with_root`` (a plain list resolver the
# optimizer never sees) stays the pipeline-path baseline - and
# ``test_synthesized_connection_per_parent_query_cost`` stays ``1 + N`` there.
# =============================================================================


def _genres_list_schema(*, optimizer=False, book_total_count=False, strictness="off"):
    """Build a ``DjangoListField(GenreType)`` root over the M2M ``Genre.books``.

    With ``optimizer`` installed the parent ``Genre`` queryset is planned, so
    the nested ``booksConnection`` window lands on each genre's
    ``_dst_books_connection`` ``to_attr`` and the fast path fires.
    ``book_total_count`` opts ``BookType`` into ``Meta.connection`` so the
    nested connection carries ``totalCount``. ``strictness`` (``"off"`` /
    ``"warn"`` / ``"raise"``) wires the B3 contract for the Slice-4 strictness
    pins; it is only meaningful with ``optimizer=True`` (no extension stashes
    no sentinel - the no-op baseline).
    """
    make_django_type(
        "BookType",
        Book,
        ("id", "title"),
        meta_extra={"connection": {"total_count": True}} if book_total_count else None,
    )
    genre_type = _make_type("GenreType", Genre, ("id", "name", "books"))
    finalize_django_types()
    query_cls = strawberry.type(
        type(
            "Query",
            (),
            {"__annotations__": {"objs": list[genre_type]}, "objs": DjangoListField(genre_type)},
        ),
    )
    extensions = [lambda: DjangoOptimizerExtension(strictness=strictness)] if optimizer else []
    return strawberry.Schema(query=query_cls, config=strawberry_config(), extensions=extensions)


def _genres_filterable_book_schema(*, strictness="raise"):
    """Build the same M2M genres list root but with ``BookType`` carrying a sidecar.

    A ``filterset_class`` on ``BookType`` means a nested ``booksConnection(filter:
    ...)`` selection is a Decision-6 sidecar fallback: the walker leaves it
    unplanned, so the resolver runs the per-parent pipeline and (with strictness
    active) fires the B3 contract with the filter/orderBy fallback reason.
    """

    class _BookFilter(FilterSet):
        class Meta:
            model = Book
            fields = {"title": ["exact"]}

    make_django_type(
        "BookType",
        Book,
        ("id", "title"),
        meta_extra={"filterset_class": _BookFilter},
    )
    genre_type = _make_type("GenreType", Genre, ("id", "name", "books"))
    finalize_django_types()
    query_cls = strawberry.type(
        type(
            "Query",
            (),
            {"__annotations__": {"objs": list[genre_type]}, "objs": DjangoListField(genre_type)},
        ),
    )
    return strawberry.Schema(
        query=query_cls,
        config=strawberry_config(),
        extensions=[lambda: DjangoOptimizerExtension(strictness=strictness)],
    )


def _genres_distinct_book_schema(*, optimizer=True, strictness="off"):
    """M2M genres list root whose ``BookType`` target ``get_queryset`` ``.distinct()``s.

    A ``.distinct()``-ing target is a Decision-6 DISTINCT fallback: the window's
    ``Count(1) OVER`` would over-count the pre-DISTINCT fan-out rows, so the
    walker leaves the nested ``booksConnection`` unplanned and the per-parent
    pipeline runs - which counts ``totalCount`` correctly via ``.distinct().count()``.
    ``BookType`` opts into ``Meta.connection`` so ``totalCount`` exists; the
    ``genres__isnull=False`` join is what fans rows out so DISTINCT is load-bearing.
    """

    class BookType(DjangoType):
        class Meta:
            model = Book
            fields = ("id", "title")
            interfaces = (relay.Node,)
            connection = {"total_count": True}

        @classmethod
        def get_queryset(cls, queryset, info):
            return queryset.filter(genres__isnull=False).distinct()

    genre_type = _make_type("GenreType", Genre, ("id", "name", "books"))
    finalize_django_types()
    query_cls = strawberry.type(
        type(
            "Query",
            (),
            {"__annotations__": {"objs": list[genre_type]}, "objs": DjangoListField(genre_type)},
        ),
    )
    extensions = [lambda: DjangoOptimizerExtension(strictness=strictness)] if optimizer else []
    return strawberry.Schema(query=query_cls, config=strawberry_config(), extensions=extensions)


def _exec(schema, query):
    """Execute and return the first parent's ``booksConnection`` dict (no errors)."""
    result = schema.execute_sync(query)
    assert result.errors is None, result.errors
    return result


@pytest.mark.django_db
def test_fast_path_single_query(django_assert_num_queries):
    """Parent page + one window query, zero per-parent queries (the cost contract).

    The optimizer-on mirror of ``test_synthesized_connection_per_parent_query_cost``:
    a nested connection under an N-row parent list pays a FIXED count (parent
    list + one batched window query) independent of parent count.
    """
    branch = Branch.objects.create(name="central")
    shelf = Shelf.objects.create(code="A1", branch=branch)
    for gi in range(4):
        genre = Genre.objects.create(name=f"g{gi}")
        for title in ("a", "b", "c"):
            book = Book.objects.create(title=f"g{gi}-{title}", shelf=shelf)
            book.genres.add(genre)

    schema = _genres_list_schema(optimizer=True)
    with django_assert_num_queries(2):
        result = _exec(
            schema,
            "{ objs { name booksConnection(first: 2) { edges { node { title } } } } }",
        )
    assert len(result.data["objs"]) == 4
    assert all(len(g["booksConnection"]["edges"]) == 2 for g in result.data["objs"])


@pytest.mark.django_db
def test_fast_path_through_schema_connection_extension(django_assert_num_queries):
    """The fast path survives Strawberry's ``ConnectionExtension.resolve`` wrapper.

    MANDATORY (spec-033 Decision 5, the through-schema mandate): execute the real ``relay.connection(...)`` field
    end to end. The resolver returns a ``_WindowedConnectionRows`` node wrapper
    and the generated connection class builds the Relay object - a direct helper
    call would miss the ``ConnectionExtension`` layer boundary. The fixed query
    count (parent + one window, no per-parent query) proves the fast path fired
    rather than the per-parent pipeline.
    """
    _seed_library_books(["a", "b", "c"])
    schema = _genres_list_schema(optimizer=True)
    with django_assert_num_queries(2):
        result = _exec(
            schema,
            "{ objs { booksConnection(first: 2) { edges { node { title } } } } }",
        )
    titles = [e["node"]["title"] for e in result.data["objs"][0]["booksConnection"]["edges"]]
    assert titles == ["a", "b"]


@pytest.mark.django_db
def test_divergent_aliases_one_window_query_per_alias(django_assert_num_queries):
    """Divergent aliases cost parents + ONE window query per alias (idea #2).

    ``a: booksConnection(first: 2)`` + ``b: booksConnection(first: 5)`` was the
    historical whole-relation fallback (O(parents x aliases) per-parent
    queries); the per-response-key scheme plans one window per key and the
    resolver routes each alias to its ``_dst_books$<key>_connection`` attr via
    ``info.path.key`` - so the count is FIXED (1 parent + 2 windows)
    independent of parent count, and each alias serves ITS OWN page bound.
    """
    branch = Branch.objects.create(name="central")
    shelf = Shelf.objects.create(code="A1", branch=branch)
    for gi in range(4):
        genre = Genre.objects.create(name=f"g{gi}")
        for title in ("a", "b", "c"):
            book = Book.objects.create(title=f"g{gi}-{title}", shelf=shelf)
            book.genres.add(genre)

    schema = _genres_list_schema(optimizer=True)
    with django_assert_num_queries(3):
        result = _exec(
            schema,
            "{ objs { "
            "a: booksConnection(first: 2) { edges { node { title } } } "
            "b: booksConnection(first: 5) { edges { node { title } } } "
            "} }",
        )
    assert len(result.data["objs"]) == 4
    for obj in result.data["objs"]:
        assert len(obj["a"]["edges"]) == 2  # a's window bound
        assert len(obj["b"]["edges"]) == 3  # b's window bound (3 of 5 available)


@pytest.mark.django_db
def test_divergent_aliases_wire_parity():
    """Divergent aliases: per-key windows and the pipeline are byte-identical.

    Full page, short page, cursors, and page flags - the optimizer-on wire
    payload for both aliases must equal the optimizer-less per-parent
    pipeline's, exactly like the shared-window parity pins.
    """
    _seed_library_books(
        [
            "a",
            "b",
            "c",
            "d",
        ],
    )
    selection = (
        "a: booksConnection(first: 2) { edges { cursor node { title } } "
        "pageInfo { hasNextPage hasPreviousPage startCursor endCursor } } "
        "b: booksConnection(first: 9) { edges { cursor node { title } } "
        "pageInfo { hasNextPage hasPreviousPage startCursor endCursor } }"
    )
    query = f"{{ objs {{ {selection} }} }}"

    fast = _exec(_genres_list_schema(optimizer=True), query)
    registry.clear()
    _connection_type_cache.clear()
    slow = _exec(_genres_list_schema(optimizer=False), query)
    assert fast.data == slow.data
    # And the fast payload is substantively right, not vacuously equal.
    fast_obj = fast.data["objs"][0]
    assert [e["node"]["title"] for e in fast_obj["a"]["edges"]] == ["a", "b"]
    assert fast_obj["a"]["pageInfo"]["hasNextPage"] is True
    assert [e["node"]["title"] for e in fast_obj["b"]["edges"]] == [
        "a",
        "b",
        "c",
        "d",
    ]
    assert fast_obj["b"]["pageInfo"]["hasNextPage"] is False


@pytest.mark.django_db
def test_divergent_alias_per_key_window_preferred_over_shared():
    """Rows under the per-key attr serve the alias even when the shared attr exists.

    The resolver probes ``_dst_books$<key>_connection`` FIRST and only falls
    back to the legacy shared ``_dst_books_connection``; planting DIFFERENT
    annotated rows under each proves the routing order (a desync here would
    silently serve another alias's window).
    """
    from django_strawberry_framework.optimizer.plans import WINDOW_ROW_NUMBER

    _seed_library_books(["a", "b", "c"])
    _make_type("BookType", Book, ("id", "title"))
    genre_type = _make_type("GenreType", Genre, ("id", "name", "books"))
    finalize_django_types()
    model = genre_type.__django_strawberry_definition__.model

    def _resolver() -> list[genre_type]:
        objs = list(model._default_manager.all().order_by("pk"))
        for obj in objs:
            books = list(obj.books.all().order_by("pk"))
            per_key = [books[1]]  # "b"
            shared = [books[0], books[2]]  # "a", "c"
            for number, row in enumerate(per_key, start=1):
                setattr(row, WINDOW_ROW_NUMBER, number)
            for number, row in enumerate(shared, start=1):
                setattr(row, WINDOW_ROW_NUMBER, number)
            # ``$``-delimited attrs are not identifier syntax - set via
            # ``setattr``, exactly as Django's prefetch machinery lands them.
            setattr(obj, "_dst_books$x_connection", per_key)
            obj._dst_books_connection = shared
        return objs

    query_cls = strawberry.type(
        type(
            "Query",
            (),
            {
                "__annotations__": {"objs": list[genre_type]},
                "objs": strawberry.field(resolver=_resolver),
            },
        ),
    )
    schema = strawberry.Schema(query=query_cls, config=strawberry_config())
    result = schema.execute_sync(
        "{ objs { x: booksConnection(first: 2) { edges { node { title } } } } }",
    )
    assert result.errors is None, result.errors
    titles = [e["node"]["title"] for e in result.data["objs"][0]["x"]["edges"]]
    assert titles == ["b"]  # the per-key window, not the shared ["a", "c"]


@pytest.mark.django_db
def test_divergent_mixed_sidecar_serves_each_alias_correctly():
    """A sidecar alias resolves per-parent while its divergent sibling is windowed.

    ``a`` (filtered) takes the per-parent pipeline and narrows correctly; ``b``
    (plain page) is served from its per-key window - one alias's fallback shape
    must not corrupt the other's rows.
    """
    _seed_library_books(["apple", "banana", "avocado"])
    schema = _genres_filterable_book_schema(strictness="off")
    result = schema.execute_sync(
        "{ objs { "
        'a: booksConnection(filter: { title: { exact: "banana" } }) '
        "{ edges { node { title } } } "
        "b: booksConnection(first: 5) { edges { node { title } } } "
        "} }",
        context_value=HttpRequest(),
    )
    assert result.errors is None, result.errors
    obj = result.data["objs"][0]
    assert [e["node"]["title"] for e in obj["a"]["edges"]] == ["banana"]
    assert [e["node"]["title"] for e in obj["b"]["edges"]] == ["apple", "banana", "avocado"]


@pytest.mark.django_db
def test_divergent_aliases_strictness_raise_planned_keys_silent():
    """Plain divergent aliases are PLANNED - strictness ``"raise"`` stays silent."""
    _seed_library_books(["a", "b", "c"])
    schema = _genres_list_schema(optimizer=True, strictness="raise")
    result = schema.execute_sync(
        "{ objs { "
        "a: booksConnection(first: 2) { edges { node { title } } } "
        "b: booksConnection(first: 5) { edges { node { title } } } "
        "} }",
    )
    assert result.errors is None, result.errors
    obj = result.data["objs"][0]
    assert len(obj["a"]["edges"]) == 2
    assert len(obj["b"]["edges"]) == 3


@pytest.mark.django_db
def test_divergent_mixed_sidecar_strictness_flags_only_the_sidecar_key():
    """Under ``"raise"``, only the sidecar alias flags - its planned sibling is silent.

    Per-key strictness visibility (idea #2): the sidecar key stays a real,
    flagged per-parent access with the actionable filter/orderBy reason; the
    planned sibling's identity was recorded, so it never flags.
    """
    _seed_library_books(["apple", "banana", "avocado"])
    schema = _genres_filterable_book_schema(strictness="raise")
    result = schema.execute_sync(
        "{ objs { "
        'a: booksConnection(filter: { title: { exact: "banana" } }) '
        "{ edges { node { title } } } "
        "b: booksConnection(first: 5) { edges { node { title } } } "
        "} }",
        context_value=HttpRequest(),
    )
    # The sidecar alias raises with the actionable reason...
    assert result.errors is not None
    messages = [str(e.original_error or e) for e in result.errors]
    assert any("selection carries filter/orderBy" in m for m in messages), messages
    # ...and it is the ONLY flag: the planned sibling never fires the checker.
    assert len([m for m in messages if "Unplanned N+1" in m]) == 1


@pytest.mark.django_db
def test_distinct_target_fallback_reports_correct_total_count():
    """A ``.distinct()`` target falls back per-parent AND reports the right ``totalCount``.

    Earns the executed second clause of the walker's plan-shape pin
    ``test_distinct_child_queryset_left_unplanned_for_correct_total_count``: the
    ``genres__isnull=False`` join fans each multi-genre book into several rows, so
    a window ``Count(1) OVER`` would report the inflated pre-DISTINCT total; the
    per-parent fallback instead counts ``.distinct()`` and reports the true book
    count. Run with the optimizer ON so the DISTINCT guard is what routes the
    selection to the counting fallback.
    """
    branch = Branch.objects.create(name="central")
    shelf = Shelf.objects.create(code="A1", branch=branch)
    fiction = Genre.objects.create(name="fiction")
    scifi = Genre.objects.create(name="scifi")
    # fiction holds {a, b, c} = 3 distinct books; a and c are ALSO in scifi, so the
    # genres-join fans fiction's rows out to a(2) + b(1) + c(2) = 5 pre-DISTINCT.
    for title, extra in (("a", scifi), ("b", None), ("c", scifi)):
        book = Book.objects.create(title=title, shelf=shelf)
        book.genres.add(fiction)
        if extra is not None:
            book.genres.add(extra)

    schema = _genres_distinct_book_schema(optimizer=True)
    result = _exec(schema, "{ objs { name booksConnection { totalCount } } }")
    by_name = {g["name"]: g["booksConnection"]["totalCount"] for g in result.data["objs"]}
    # True distinct count (3), NOT the inflated 5 a pre-DISTINCT Count(1) OVER reports.
    assert by_name["fiction"] == 3


@pytest.mark.django_db
@pytest.mark.parametrize(
    "args",
    ["first: 2", "first: 10", 'first: 2, after: "YXJyYXljb25uZWN0aW9uOjA="'],
)
def test_fast_path_wire_parity_with_pipeline(args):
    """Identical edges / cursors / pageInfo for the same data, optimizer on vs off.

    The core parity matrix: the fast path (optimizer installed, window consumed)
    and the per-parent pipeline (no optimizer) must produce byte-identical wire
    results across forward windows, overruns, and ``after:`` continuation.
    """
    _seed_library_books(
        [
            "a",
            "b",
            "c",
            "d",
        ],
    )
    selection = (
        f"booksConnection({args}) {{ edges {{ cursor node {{ title }} }} "
        f"pageInfo {{ hasNextPage hasPreviousPage startCursor endCursor }} }}"
    )
    query = f"{{ objs {{ {selection} }} }}"

    # The seeded rows persist across both schema builds in one test transaction;
    # only the registry / connection-cache need clearing between the two
    # ``DjangoType`` declarations (re-seeding would collide on unique fields).
    fast = _exec(_genres_list_schema(optimizer=True), query)
    registry.clear()
    _connection_type_cache.clear()
    slow = _exec(_genres_list_schema(optimizer=False), query)
    assert fast.data == slow.data


@pytest.mark.django_db
def test_fast_path_wire_parity_last_only():
    """Reversed (``last``-only) window maps to the SAME cursors and page flags.

    Slice 1 keeps ``_dst_row_number`` forward (a separate
    ``_dst_row_number_reversed`` drives only the plan-time row filter), so the
    fast path's positional cursor (``_dst_row_number - 1``) and forward page-flag
    comparisons land on the pipeline's values for a ``last``-only page too.
    """
    _seed_library_books(
        [
            "a",
            "b",
            "c",
            "d",
            "e",
        ],
    )
    selection = (
        "booksConnection(last: 2) { edges { cursor node { title } } "
        "pageInfo { hasNextPage hasPreviousPage startCursor endCursor } }"
    )
    query = f"{{ objs {{ {selection} }} }}"

    fast = _exec(_genres_list_schema(optimizer=True), query)
    fast_conn = fast.data["objs"][0]["booksConnection"]
    assert [e["node"]["title"] for e in fast_conn["edges"]] == ["d", "e"]
    assert fast_conn["pageInfo"]["hasPreviousPage"] is True
    assert fast_conn["pageInfo"]["hasNextPage"] is False

    registry.clear()
    _connection_type_cache.clear()
    slow = _exec(_genres_list_schema(optimizer=False), query)
    assert fast.data == slow.data


@pytest.mark.django_db(transaction=True)
def test_fast_path_non_pk_ordering_applies_explicit_deterministic_order_by():
    """A non-pk-ordered child: the windowed prefetch's outer ORDER BY carries the pk tiebreaker.

    The shipped parity tests order ``Book`` by pk, where DB-natural (rowid) order
    coincides with the window order and cannot expose a missing
    ``queryset.order_by``. Even here, where the child orders by a non-pk
    ``Meta.ordering`` (``title``), SQLite's window sort emits rows in title order
    and Django propagates ``Meta.ordering`` to the outer query on its own - so a
    wire comparison cannot catch the bug on SQLite. What the fix uniquely adds is
    the **deterministic order** applied to the queryset: the outer ORDER BY gains
    the pk tiebreaker (``ORDER BY <title>, <pk>``) instead of the single
    ``Meta.ordering`` column, which is what keeps fast-path cursors stable across
    rows that tie on ``title``. This asserts that two-column outer order directly
    on the prefetch SQL (the deterministic regression, Revision 3) and pins
    optimizer-on vs optimizer-off wire parity for the distinct-title case.
    """
    from django.test.utils import CaptureQueriesContext

    class OConnTag(djmodels.Model):
        name = djmodels.CharField(max_length=32)

        class Meta:
            app_label = "products"
            managed = False

    class OConnPost(djmodels.Model):
        title = djmodels.CharField(max_length=32)
        tag = djmodels.ForeignKey(OConnTag, related_name="posts", on_delete=djmodels.CASCADE)

        class Meta:
            app_label = "products"
            managed = False
            ordering = ["title"]

    with db_connection.schema_editor() as schema_editor:
        schema_editor.create_model(OConnTag)
        schema_editor.create_model(OConnPost)
    try:
        tag = OConnTag.objects.create(name="t")
        for title in (
            "d",
            "a",
            "c",
            "b",
        ):  # pk order (d,a,c,b) != title order (a,b,c,d)
            OConnPost.objects.create(title=title, tag=tag)
        # A SECOND parent keeps the prefetch multi-parent so the windowed body
        # runs: the single-parent degenerate fast path
        # (optimizer/single_parent_fetch.py) would otherwise serve a plain
        # filtered LIMIT (no ROW_NUMBER) for a lone parent, which this test
        # cannot inspect for the outer ORDER BY tiebreaker. The fast path applies
        # the SAME deterministic order; here we pin the windowed path explicitly.
        other = OConnTag.objects.create(name="u")
        for title in ("z", "y"):
            OConnPost.objects.create(title=title, tag=other)

        query = (
            "{ objs { postsConnection(first: 2) { edges { cursor node { title } } "
            "pageInfo { startCursor endCursor } } } }"
        )

        def _build(*, optimizer):
            type(
                "OConnPostType",
                (DjangoType,),
                {
                    "Meta": type(
                        "Meta",
                        (),
                        {
                            "model": OConnPost,
                            "fields": ("id", "title"),
                            "interfaces": (relay.Node,),
                        },
                    ),
                },
            )
            tag_type = _make_type("OConnTagType", OConnTag, ("id", "name", "posts"))
            finalize_django_types()
            query_cls = strawberry.type(
                type(
                    "Query",
                    (),
                    {
                        "__annotations__": {"objs": list[tag_type]},
                        "objs": DjangoListField(tag_type),
                    },
                ),
            )
            extensions = [lambda: DjangoOptimizerExtension()] if optimizer else []
            return strawberry.Schema(
                query=query_cls,
                config=strawberry_config(),
                extensions=extensions,
            )

        with CaptureQueriesContext(db_connection) as ctx:
            fast = _exec(_build(optimizer=True), query)
        window_sql = next(
            q["sql"] for q in ctx.captured_queries if "ROW_NUMBER" in q["sql"].upper()
        )
        # The outer query (after the row-number filter) must order by the FULL
        # deterministic tuple - title AND the pk tiebreaker. Without the explicit
        # `queryset.order_by`, Django still propagates the single Meta.ordering
        # column, so the regression signal is the SECOND sort column (the comma),
        # not the mere presence of ORDER BY.
        tail = window_sql.upper().split('"_DST_ROW_NUMBER" <=')[-1]
        assert "ORDER BY" in tail, window_sql
        outer_order = tail.split("ORDER BY", 1)[-1]
        assert "," in outer_order, window_sql  # title + pk, not title alone

        registry.clear()
        _connection_type_cache.clear()
        slow = _exec(_build(optimizer=False), query)
        assert fast.data == slow.data
        titles = [e["node"]["title"] for e in fast.data["objs"][0]["postsConnection"]["edges"]]
        assert titles == ["a", "b"]
    finally:
        with db_connection.schema_editor() as schema_editor:
            schema_editor.delete_model(OConnPost)
            schema_editor.delete_model(OConnTag)


@pytest.mark.django_db
def test_fast_path_cursor_round_trips_to_fallback_after():
    """A fast-path ``endCursor`` fed to ``after:`` on an optimizer-less execution continues.

    The cursor-parity invariant's observable proof (Decision 4): the fast path's
    positional offset cursors are format-compatible with the pipeline's, so a
    page-1 ``endCursor`` captured under the optimizer drives a correct page-2
    ``after:`` with the optimizer absent.
    """
    _seed_library_books(
        [
            "a",
            "b",
            "c",
            "d",
        ],
    )
    fast = _exec(
        _genres_list_schema(optimizer=True),
        "{ objs { booksConnection(first: 2) { pageInfo { endCursor } } } }",
    )
    end_cursor = fast.data["objs"][0]["booksConnection"]["pageInfo"]["endCursor"]

    registry.clear()
    _connection_type_cache.clear()
    page_two = _exec(
        _genres_list_schema(optimizer=False),
        f'{{ objs {{ booksConnection(first: 2, after: "{end_cursor}") '
        f"{{ edges {{ node {{ title }} }} }} }} }}",
    )
    titles = [e["node"]["title"] for e in page_two.data["objs"][0]["booksConnection"]["edges"]]
    assert titles == ["c", "d"]


@pytest.mark.django_db(transaction=True)
def test_fast_path_fires_for_reverse_fk_without_related_name(django_assert_num_queries):
    """The fast path fires for a reverse FK without ``related_name``.

    Decision 5: the resolver receives the relation FIELD NAME (``windowbook``),
    not the accessor (``windowbook_set``), so its ``_dst_<field>_connection`` probe
    matches the ``to_attr`` the walker keyed on the field name. The fixed query
    count (parent + one window) proves the fast path fired rather than silently
    falling back because the probe missed.

    Uses its own ``WindowAuthor`` / ``WindowBook`` ``managed=False`` models (not
    the ``PlainAuthor`` / ``PlainBook`` of the behavior-only test above) so the
    two reverse-FK fixtures never collide in Django's app registry when both run.
    """

    class WindowAuthor(djmodels.Model):
        name = djmodels.CharField(max_length=32)

        class Meta:
            app_label = "products"
            managed = False

    class WindowBook(djmodels.Model):
        title = djmodels.CharField(max_length=32)
        author = djmodels.ForeignKey(WindowAuthor, on_delete=djmodels.CASCADE)  # no related_name

        class Meta:
            app_label = "products"
            managed = False

    assert WindowAuthor._meta.get_field("windowbook").get_accessor_name() == "windowbook_set"

    with db_connection.schema_editor() as schema_editor:
        schema_editor.create_model(WindowAuthor)
        schema_editor.create_model(WindowBook)
    try:
        type(
            "WindowBookType",
            (DjangoType,),
            {
                "Meta": type(
                    "Meta",
                    (),
                    {
                        "model": WindowBook,
                        "fields": ("id", "title"),
                        "interfaces": (relay.Node,),
                    },
                ),
            },
        )
        author_type = _make_type("WindowAuthorType", WindowAuthor, ("id", "name", "windowbook"))
        finalize_django_types()
        query_cls = strawberry.type(
            type(
                "Query",
                (),
                {
                    "__annotations__": {"objs": list[author_type]},
                    "objs": DjangoListField(author_type),
                },
            ),
        )
        schema = strawberry.Schema(
            query=query_cls,
            config=strawberry_config(),
            extensions=[lambda: DjangoOptimizerExtension()],
        )
        for ai in range(3):
            author = WindowAuthor.objects.create(name=f"a{ai}")
            for ti in range(3):
                WindowBook.objects.create(title=f"a{ai}-b{ti}", author=author)

        with django_assert_num_queries(2):
            result = _exec(
                schema,
                "{ objs { name windowbookConnection(first: 2) { edges { node { title } } } } }",
            )
        assert len(result.data["objs"]) == 3
        assert all(len(a["windowbookConnection"]["edges"]) == 2 for a in result.data["objs"])
    finally:
        with db_connection.schema_editor() as schema_editor:
            schema_editor.delete_model(WindowBook)
            schema_editor.delete_model(WindowAuthor)


@pytest.mark.django_db
def test_fast_path_total_count_from_annotation_no_query(django_assert_num_queries):
    """A fast-path ``totalCount`` reads ``_dst_total_count`` - zero extra COUNT queries."""
    _seed_library_books(
        [
            "a",
            "b",
            "c",
            "d",
            "e",
        ],
    )
    schema = _genres_list_schema(optimizer=True, book_total_count=True)
    with django_assert_num_queries(2):  # parent + window only; no per-relation COUNT
        result = _exec(
            schema,
            "{ objs { booksConnection(first: 2) { totalCount edges { node { title } } } } }",
        )
    assert result.data["objs"][0]["booksConnection"]["totalCount"] == 5


@pytest.mark.django_db
def test_fast_path_has_next_page_without_edges_on_window(django_assert_num_queries):
    """``hasNextPage`` is correct on the WINDOW path even when ``edges`` is unrequested.

    The Relay invariant (spec-032 Goal 4 / DoD: "the connection MUST resolve
    ``hasNextPage`` correctly even when the consumer didn't request ``edges``")
    asserted on the exact path spec-033 introduces - the others assert it only on
    the root field and the optimizer-less per-parent fallback. A nested
    ``booksConnection { pageInfo { hasNextPage } }`` with no ``edges`` is
    recognized by field name, window-planned as a scalar-only projection, and
    serves ``hasNextPage`` from the UNCONDITIONALLY-annotated ``_dst_total_count``
    - so it is correct WITHOUT ``edges`` AND WITHOUT the ``totalCount`` opt-in
    (``book_total_count=False`` here), and it costs one batched window query (no
    per-parent fallback, no per-relation COUNT).
    """
    _seed_library_books(
        [
            "a",
            "b",
            "c",
            "d",
            "e",
        ],
    )
    schema = _genres_list_schema(optimizer=True)  # NO totalCount opt-in
    with django_assert_num_queries(2):  # parent + window only; no edges, no fallback
        result = _exec(
            schema,
            "{ objs { booksConnection(first: 2) { pageInfo { hasNextPage } } } }",
        )
    # 5 books, first: 2 -> a further page exists.
    assert result.data["objs"][0]["booksConnection"]["pageInfo"]["hasNextPage"] is True


@pytest.mark.django_db
def test_fast_path_has_no_next_page_at_boundary_without_edges_on_window(django_assert_num_queries):
    """The boundary twin: ``first >= total`` -> ``hasNextPage`` False on the window path.

    Pins that the scalar-only window's ``hasNextPage`` is not hard-wired True: 5
    books with ``first: 5`` exhausts the window, so ``hasNextPage`` is False -
    still served from the annotation with no ``edges`` selected.
    """
    _seed_library_books(
        [
            "a",
            "b",
            "c",
            "d",
            "e",
        ],
    )
    schema = _genres_list_schema(optimizer=True)
    with django_assert_num_queries(2):
        result = _exec(
            schema,
            "{ objs { booksConnection(first: 5) { pageInfo { hasNextPage } } } }",
        )
    assert result.data["objs"][0]["booksConnection"]["pageInfo"]["hasNextPage"] is False


@pytest.mark.django_db
def test_fast_path_total_count_without_edges_on_window(django_assert_num_queries):
    """``totalCount`` alone (no ``edges``) reads ``_dst_total_count`` on the window path.

    The totalCount-only sibling of the pageInfo-only pin: a nested
    ``booksConnection { totalCount }`` with no ``edges`` is the scalar-only window
    projection, served from the annotation in a single batched window query - the
    existing ``totalCount`` window pins all also select ``edges``.
    """
    _seed_library_books(
        [
            "a",
            "b",
            "c",
            "d",
            "e",
        ],
    )
    schema = _genres_list_schema(optimizer=True, book_total_count=True)
    with django_assert_num_queries(2):  # parent + window only; no edges, no per-relation COUNT
        result = _exec(
            schema,
            "{ objs { booksConnection(first: 2) { totalCount } } }",
        )
    assert result.data["objs"][0]["booksConnection"]["totalCount"] == 5


@pytest.mark.django_db
def test_fast_path_total_count_marker_bypasses_non_queryset_guard():
    """``totalCount`` over the wrapper does NOT raise the non-queryset count guard.

    The ``_WindowedConnectionRows`` marker is not a ``QuerySet``; the totalCount
    variant must branch on it BEFORE ``_guard_total_count_countable`` / ``.count()``
    (Decision 5), so selecting ``totalCount`` over a fast-path window resolves
    cleanly instead of raising the M1 non-queryset ``GraphQLError``.
    """
    _seed_library_books(["a", "b", "c"])
    schema = _genres_list_schema(optimizer=True, book_total_count=True)
    result = schema.execute_sync(
        "{ objs { booksConnection(first: 2) { totalCount edges { node { title } } } } }",
    )
    assert result.errors is None, result.errors
    assert result.data["objs"][0]["booksConnection"]["totalCount"] == 3


@pytest.mark.django_db
@pytest.mark.parametrize("args", ["first: 0", 'after: "YXJyYXljb25uZWN0aW9uOjk5"'])
def test_fast_path_ambiguous_empty_served_from_marker_row(args, django_assert_num_queries):
    """``first: 0`` (``limit == 0``) and overshot ``after:`` (``offset > 0``) serve from markers.

    The marker-row disambiguation (connection window rigor, workstream C):
    these shapes historically fell back per-parent (the empty window was
    ambiguous); the window now keeps each partition's row 1, so the empty page
    is served with the TRUE ``totalCount`` / ``pageInfo`` - byte-identical to
    the pipeline - in the fixed two-query cost with NO per-parent fallback.
    """
    _seed_library_books(["a", "b", "c"])
    selection = (
        f"booksConnection({args}) {{ edges {{ node {{ title }} }} totalCount "
        f"pageInfo {{ hasNextPage hasPreviousPage }} }}"
    )
    query = f"{{ objs {{ {selection} }} }}"

    with django_assert_num_queries(2):  # parent + window; the fallback never fires.
        fast = _exec(_genres_list_schema(optimizer=True, book_total_count=True), query)
    registry.clear()
    _connection_type_cache.clear()
    slow = _exec(_genres_list_schema(optimizer=False, book_total_count=True), query)
    assert fast.data == slow.data
    # The marker carries the true totalCount (3), never a spurious 0 from
    # inferring "the window is empty so the parent is empty".
    assert fast.data["objs"][0]["booksConnection"]["totalCount"] == 3


@pytest.mark.django_db(transaction=True)
async def test_async_fast_path_last_zero_falls_back_for_total_count_and_pageinfo(monkeypatch):
    """The async fallback mirror rides the ``last: 0`` quirk UNDER ASYNC execution.

    ``last: 0`` is the one remaining always-fallback shape after the
    marker-row disambiguation (workstream C): upstream ``ListConnection``
    slices ``edges[-0:]`` - the WHOLE list - so only the per-parent pipeline
    reproduces it (the walker plans nothing for it; feedback2 P0-3). Driven
    by ``await schema.execute(...)``, the per-parent queryset resolves
    through ``ListConnection`` asynchronously, so
    ``_consume_fallback``'s ``super().resolve_connection`` returns a coroutine
    - exercising the async ``_attach_count_async`` fallback branch
    (``connection.py::_consume_fallback #"return _attach_count_async("``). The
    sync ``last: 0`` parity test covers the ``_attach_count_sync`` sibling.
    """
    from asgiref.sync import sync_to_async

    # The optimizer extension runs the parent (genre) prefetch with sync ORM on
    # the event-loop thread; unblock Django's async-safety guard for it. The
    # nested booksConnection fallback still resolves through ListConnection
    # ASYNC (strawberry's async execution), so this does not collapse the
    # awaitable branch into the sync one.
    monkeypatch.setenv("DJANGO_ALLOW_ASYNC_UNSAFE", "true")
    await sync_to_async(_seed_library_books)(["a", "b", "c"])
    schema = await sync_to_async(_genres_list_schema)(optimizer=True, book_total_count=True)
    selection = (
        "booksConnection(last: 0) { edges { node { title } } totalCount "
        "pageInfo { hasNextPage hasPreviousPage } }"
    )
    result = await schema.execute(f"{{ objs {{ {selection} }} }}")
    assert result.errors is None, result.errors
    conn = result.data["objs"][0]["booksConnection"]
    # Upstream's edges[-0:] quirk: ALL edges, served through the fallback.
    assert [e["node"]["title"] for e in conn["edges"]] == ["a", "b", "c"]
    assert conn["totalCount"] == 3


@pytest.mark.django_db
def test_fast_path_last_zero_quirk_parity_via_fallback():
    """``last: 0`` falls back per-parent and reproduces upstream's serve-all quirk.

    Upstream ``ListConnection`` slices ``edges[-last:]`` for the ``last``-only
    branch, and ``edges[-0:]`` is the WHOLE list - so ``last: 0`` returns every
    edge. The walker leaves this shape FULLY UNPLANNED (feedback2 P0-3: a
    reversed window would always come back empty and be discarded, paying a
    dead query per request while its resolver keys silenced strictness), so
    the per-parent pipeline - the only path that reproduces the quirk - runs
    directly and stays byte-identical to the optimizer-off answer.
    """
    _seed_library_books(["a", "b", "c"])
    query = (
        "{ objs { booksConnection(last: 0) { edges { node { title } } totalCount "
        "pageInfo { hasNextPage hasPreviousPage } } } }"
    )
    from django.test.utils import CaptureQueriesContext

    with CaptureQueriesContext(db_connection) as captured:
        fast = _exec(_genres_list_schema(optimizer=True, book_total_count=True), query)
    # feedback2 P0-3: the walker plans NOTHING for ``last: 0``. One parent
    # query + the single genre's per-parent pipeline (a count query for
    # ``totalCount`` + the edges query) = 3, with NO dead window query
    # riding along (pre-fix this was 4: the discarded reversed window ran
    # first on every request).
    assert len(captured) == 3
    assert not any("_dst_row_number" in entry["sql"] for entry in captured)
    registry.clear()
    _connection_type_cache.clear()
    slow = _exec(_genres_list_schema(optimizer=False, book_total_count=True), query)
    assert fast.data == slow.data
    conn = fast.data["objs"][0]["booksConnection"]
    assert [e["node"]["title"] for e in conn["edges"]] == ["a", "b", "c"]


@pytest.mark.django_db
def test_fast_path_genuinely_empty_parent_serves_zero(django_assert_num_queries):
    """A parent with no related rows is fast-pathed: totalCount 0, no fallback query.

    Empty window with ``offset == 0`` and a positive bound proves the parent
    genuinely has none, so the fast path serves ``totalCount = 0`` / no cursors /
    both flags ``False`` without a per-parent fallback query.
    """
    branch = Branch.objects.create(name="central")
    Shelf.objects.create(code="A1", branch=branch)
    Genre.objects.create(name="empty")  # genre with zero books
    schema = _genres_list_schema(optimizer=True, book_total_count=True)
    with django_assert_num_queries(2):  # parent + the (empty) window; no fallback
        result = _exec(
            schema,
            "{ objs { booksConnection(first: 2) { totalCount edges { node { title } } "
            "pageInfo { hasNextPage hasPreviousPage } } } }",
        )
    conn = result.data["objs"][0]["booksConnection"]
    assert conn["edges"] == []
    assert conn["totalCount"] == 0
    assert conn["pageInfo"] == {"hasNextPage": False, "hasPreviousPage": False}


@pytest.mark.django_db
@pytest.mark.parametrize("args", ["first: 0", 'first: 2, after: "YXJyYXljb25uZWN0aW9uOjk5"'])
def test_fast_path_zero_children_parent_serves_under_ambiguous_shapes(
    args,
    django_assert_num_queries,
):
    """A zero-children parent is served (not fallen back) under the marker shapes.

    Workstream C's other half: with markers planned, an EMPTY window under
    ``first: 0`` / overshot ``after:`` now PROVES the parent has no children
    (a parent with children would have kept its row 1), so the fast path
    serves ``totalCount 0`` in the fixed two-query cost. Byte parity with the
    pipeline pins the flag arithmetic - notably ``hasPreviousPage`` is True
    for the overshot ``after:`` even with zero children, because upstream
    ``ListConnection`` computes ``start > 0`` before looking at the data.
    """
    branch = Branch.objects.create(name="central")
    Shelf.objects.create(code="A1", branch=branch)
    Genre.objects.create(name="empty")  # genre with zero books
    selection = (
        f"booksConnection({args}) {{ totalCount edges {{ node {{ title }} }} "
        f"pageInfo {{ hasNextPage hasPreviousPage }} }}"
    )
    query = f"{{ objs {{ {selection} }} }}"
    with django_assert_num_queries(2):  # parent + the (empty) window; no fallback
        fast = _exec(_genres_list_schema(optimizer=True, book_total_count=True), query)
    registry.clear()
    _connection_type_cache.clear()
    slow = _exec(_genres_list_schema(optimizer=False, book_total_count=True), query)
    assert fast.data == slow.data
    conn = fast.data["objs"][0]["booksConnection"]
    assert conn["edges"] == []
    assert conn["totalCount"] == 0


@pytest.mark.django_db
def test_fast_path_ignores_window_when_sidecar_kwargs_present():
    """A ``filter:`` argument makes the resolver ignore the window and run the pipeline.

    The defensive belt (Decision 5): even if the walker desyncs and plans a
    window, a sidecar-carrying selection must NOT consume it (which would serve
    unfiltered wrong data) - the resolver refuses the window when its own
    ``filter`` / ``order_by`` kwargs are present and runs the filtered pipeline.
    """

    class _BookFilter(FilterSet):
        class Meta:
            model = Book
            fields = {"title": ["exact"]}

    make_django_type(
        "BookType",
        Book,
        ("id", "title"),
        meta_extra={"filterset_class": _BookFilter},
    )
    genre_type = _make_type("GenreType", Genre, ("id", "name", "books"))
    finalize_django_types()
    query_cls = strawberry.type(
        type(
            "Query",
            (),
            {"__annotations__": {"objs": list[genre_type]}, "objs": DjangoListField(genre_type)},
        ),
    )
    schema = strawberry.Schema(
        query=query_cls,
        config=strawberry_config(),
        extensions=[lambda: DjangoOptimizerExtension()],
    )
    _seed_library_books(["apple", "banana", "avocado"])
    result = schema.execute_sync(
        '{ objs { booksConnection(filter: { title: { exact: "banana" } }) '
        "{ edges { node { title } } } } }",
        context_value=HttpRequest(),
    )
    assert result.errors is None, result.errors
    titles = [e["node"]["title"] for e in result.data["objs"][0]["booksConnection"]["edges"]]
    assert titles == ["banana"]  # the filter narrowed; the unfiltered window was refused


@pytest.mark.django_db
def test_fallback_when_annotations_missing():
    """A ``to_attr`` list whose rows lack the window annotations is not consumed.

    A consumer's own prefetch (or any non-window attribute) at the package-reserved
    name without ``_dst_row_number`` / ``_dst_total_count`` must fall through to
    the pipeline - the annotation-presence probe is upstream's integrity check.
    """
    _seed_library_books(["a", "b", "c"])
    _make_type("BookType", Book, ("id", "title"))
    genre_type = _make_type("GenreType", Genre, ("id", "name", "books"))
    finalize_django_types()
    model = genre_type.__django_strawberry_definition__.model

    def _resolver() -> list[genre_type]:
        objs = list(model._default_manager.all().order_by("pk"))
        # Plant an UNANNOTATED list at the package-reserved to_attr (a consumer
        # prefetch shape); the resolver must NOT consume it as a window.
        for obj in objs:
            obj._dst_books_connection = list(obj.books.all())
        return objs

    query_cls = strawberry.type(
        type(
            "Query",
            (),
            {
                "__annotations__": {"objs": list[genre_type]},
                "objs": strawberry.field(resolver=_resolver),
            },
        ),
    )
    schema = strawberry.Schema(query=query_cls, config=strawberry_config())
    result = schema.execute_sync(
        "{ objs { booksConnection(first: 2) { edges { node { title } } } } }",
    )
    assert result.errors is None, result.errors
    titles = [e["node"]["title"] for e in result.data["objs"][0]["booksConnection"]["edges"]]
    assert titles == ["a", "b"]


@pytest.mark.django_db
def test_fallback_when_no_optimizer_installed():
    """No optimizer -> no window planned -> per-parent pipeline, byte-identical results."""
    _seed_library_books(["a", "b", "c"])
    query = "{ objs { booksConnection(first: 2) { edges { node { title } } pageInfo { hasNextPage } } } }"
    no_opt = _exec(_genres_list_schema(optimizer=False), query)
    conn = no_opt.data["objs"][0]["booksConnection"]
    assert [e["node"]["title"] for e in conn["edges"]] == ["a", "b"]
    assert conn["pageInfo"]["hasNextPage"] is True


@pytest.mark.django_db
def test_outer_total_count_predicate_ignores_nested_total_count():
    """A nested connection's ``totalCount`` does not fire the OUTER connection's count.

    Re-affirmation (spec-033 Edge cases: the outer-``totalCount`` direct-children-scoped
    rule) now that nested ``totalCount`` is a
    fast-path read: a two-level selection of the nested ``totalCount`` must not
    make the root connection's ``_total_count_requested`` predicate fire (no
    spurious outer COUNT, no outer non-queryset guard raise). The root here is a
    ``DjangoConnectionField`` (its own ``totalCount`` opt-in) whose ``totalCount``
    is NOT selected - only the nested one is.
    """
    _seed_library_books(["a", "b", "c"])
    make_django_type(
        "BookType",
        Book,
        ("id", "title"),
        meta_extra={"connection": {"total_count": True}},
    )
    genre_type = _make_type(
        "GenreType",
        Genre,
        ("id", "name", "books"),
        meta_extra={"connection": {"total_count": True}},
    )
    finalize_django_types()
    from django_strawberry_framework import DjangoConnectionField

    conn_type = _connection_type_for(genre_type)
    query_cls = strawberry.type(
        type(
            "Query",
            (),
            {"__annotations__": {"objs": conn_type}, "objs": DjangoConnectionField(genre_type)},
        ),
    )
    schema = strawberry.Schema(
        query=query_cls,
        config=strawberry_config(),
        extensions=[lambda: DjangoOptimizerExtension()],
    )
    # Only the NESTED totalCount is selected; the outer one is not. The outer
    # predicate must stay False (its direct children are edges + the nested
    # connection), so no spurious root COUNT fires and no outer non-queryset
    # guard raises.
    result = schema.execute_sync(
        "{ objs { edges { node { name booksConnection(first: 2) "
        "{ totalCount edges { node { title } } } } } } }",
    )
    assert result.errors is None, result.errors
    genre_node = result.data["objs"]["edges"][0]["node"]
    assert genre_node["booksConnection"]["totalCount"] == 3


# =============================================================================
# Slice 4: strictness wiring for connection paths (spec-033 Decision 8).
#
# The synthesized relation-connection resolver consults the union-published
# optimizer sentinels via the PARAMETERIZED ``types/resolvers.py::_check_n1``
# (kind="connection_to_attr") before the per-parent fallback pipeline. An
# unplanned, unserved nested-connection access fires the B3 contract -
# ``OptimizerError`` under ``"raise"``, a logged warning under ``"warn"`` -
# through the SAME machinery list relations use. These pins need an
# optimizer-installed, strictness-active schema (the fakeshop project schema
# runs strictness-off), so they live here, not in the live suite (Test plan).
#
# The sidecar-filtered ``booksConnection(filter: ...)`` is the clearest
# live-reachable fallback shape: the walker leaves it unplanned (Decision 6),
# so the resolver runs per-parent and is visible to strictness.
# =============================================================================


@pytest.mark.django_db
def test_strictness_raise_unplanned_nested_connection():
    """``"raise"`` + optimizer + a fallback nested connection -> ``OptimizerError``.

    The flagged message NAMES the generated relation field (the ``field_name``
    stem, the relation field name ``books`` the walker keyed the would-be plan
    under), exactly as a plain list relation's strictness flag reads.
    """
    from django_strawberry_framework.exceptions import OptimizerError

    _seed_library_books(["apple", "banana", "avocado"])
    schema = _genres_filterable_book_schema(strictness="raise")
    result = schema.execute_sync(
        '{ objs { booksConnection(filter: { title: { exact: "banana" } }) '
        "{ edges { node { title } } } } }",
        context_value=HttpRequest(),
    )
    assert result.errors is not None
    messages = [str(e.original_error or e) for e in result.errors]
    assert any(isinstance(e.original_error, OptimizerError) for e in result.errors)
    assert any("Unplanned N+1: books" in m for m in messages)


@pytest.mark.django_db
def test_strictness_raise_malformed_cursor_surfaces_pagination_error_not_optimizer_error():
    """A malformed nested ``after:`` cursor raises the PAGINATION error, not ``OptimizerError``.

    Error-locality regression (spec-033 Decision 4 step f / Decision 8): a
    malformed cursor leaves the connection unwindowed so the per-parent pipeline
    can raise its own cursor-validation error. Under strictness ``"raise"`` the
    walker must still record the resolver key for this fallback, or the B3 check
    preempts the real error with a spurious ``OptimizerError("Unplanned N+1")``.
    The user should see the cursor error, not an optimizer defect.
    """
    from django_strawberry_framework.exceptions import OptimizerError

    _seed_library_books(["a", "b", "c"])
    schema = _genres_list_schema(optimizer=True, strictness="raise")
    result = schema.execute_sync(
        '{ objs { booksConnection(first: 2, after: "not-a-valid-cursor") '
        "{ edges { node { title } } } } }",
        context_value=HttpRequest(),
    )
    assert result.errors is not None
    # The surfaced error is the pipeline's pagination/cursor error - NOT an N+1.
    assert not any(isinstance(e.original_error, OptimizerError) for e in result.errors)
    assert not any("Unplanned N+1" in str(e.original_error or e) for e in result.errors)


@pytest.mark.django_db
def test_sidecar_fallback_is_flagged_with_reason():
    """A sidecar fallback's ``"raise"`` message carries an ACTIONABLE reason.

    Decision 6 consistency pin (Risks bullet "include the fallback reason in the
    message"): a consumer who legitimately filters a nested connection gets a
    per-parent fallback that strictness flags - the message must explain WHY
    (the filter/orderBy wording) so it does not look like an optimizer defect.
    """
    _seed_library_books(["apple", "banana", "avocado"])
    schema = _genres_filterable_book_schema(strictness="raise")
    result = schema.execute_sync(
        '{ objs { booksConnection(filter: { title: { exact: "banana" } }) '
        "{ edges { node { title } } } } }",
        context_value=HttpRequest(),
    )
    assert result.errors is not None
    messages = [str(e.original_error or e) for e in result.errors]
    assert any("selection carries filter/orderBy" in m for m in messages), messages


@pytest.mark.django_db
def test_strictness_warn_logs_once_per_occurrence(caplog):
    """``"warn"`` + a fallback nested connection -> logged warning, execution CONTINUES.

    The query still resolves correctly (warn does not abort); the resolver
    logger emits a warning naming the field. Pinned via ``caplog``.
    """
    _seed_library_books(["apple", "banana", "avocado"])
    schema = _genres_filterable_book_schema(strictness="warn")
    caplog.set_level("WARNING", logger="django_strawberry_framework")
    result = schema.execute_sync(
        '{ objs { booksConnection(filter: { title: { exact: "banana" } }) '
        "{ edges { node { title } } } } }",
        context_value=HttpRequest(),
    )
    assert result.errors is None, result.errors
    # Warn continues: the filtered page is still served correctly.
    titles = [e["node"]["title"] for e in result.data["objs"][0]["booksConnection"]["edges"]]
    assert titles == ["banana"]
    assert any("Potential N+1 on books" in r.getMessage() for r in caplog.records), [
        r.getMessage() for r in caplog.records
    ]


@pytest.mark.django_db
def test_strictness_warn_nested_fallback_preserves_parent_plan_context():
    """A warn-mode nested fallback does not corrupt the parent's PLANNED siblings.

    The Slice-1 union-publish foundation: a nested fallback connection's own
    optimizer publish must not shrink the parent ``DST_OPTIMIZER_PLANNED`` set.
    A planned parent-level relation sibling (``books``, the plain list field)
    selected alongside the fallback nested connection must NOT warn or raise -
    its planned key survives the nested pipeline's publish.
    """
    _seed_library_books(["apple", "banana", "avocado"])
    # ``GenreType`` exposes both the list sibling ``books`` (planned) and the
    # connection sibling ``booksConnection``; selecting the planned list field
    # alongside a sidecar-filtered connection must leave the list field silent.
    schema = _genres_filterable_book_schema(strictness="raise")
    result = schema.execute_sync(
        "{ objs { books { title } "
        '  booksConnection(filter: { title: { exact: "banana" } }) '
        "{ edges { node { title } } } } }",
        context_value=HttpRequest(),
    )
    # The sidecar connection raises (it is the unplanned access), but the planned
    # ``books`` list sibling never does - its planned key was not clobbered.
    assert result.errors is not None
    messages = [str(e.original_error or e) for e in result.errors]
    assert all("Unplanned N+1: books@" not in m for m in messages)
    # The only flag is the connection field's, keyed on ``books`` (field name) -
    # never the list sibling under the same name with a different runtime path.
    assert any("Unplanned N+1: books (" in m for m in messages), messages


@pytest.mark.django_db
def test_nested_fallback_does_not_clobber_fk_id_elisions():
    """A planned forward-FK sibling still elides after a nested fallback publishes.

    The ``DST_OPTIMIZER_FK_ID_ELISIONS`` union (Slice 1) must survive the nested
    fallback pipeline's own publish: a query selecting an elided forward-FK
    (``shelf { id }`` on each book) alongside a fallback nested connection
    resolves with no spurious strictness flag on the FK-id resolver and no extra
    per-row query for the elided FK.
    """
    from django_strawberry_framework.exceptions import OptimizerError

    branch = Branch.objects.create(name="central")
    shelf = Shelf.objects.create(code="A1", branch=branch)
    genre = Genre.objects.create(name="fiction")
    for title in ("apple", "banana"):
        book = Book.objects.create(title=title, shelf=shelf)
        book.genres.add(genre)

    # ``BookType`` exposes its forward FK ``shelf`` (a ``{ id }``-only selection
    # elides it) and the M2M ``genres`` (the fallback nested connection target).
    type(
        "ShelfType",
        (DjangoType,),
        {
            "Meta": type(
                "Meta",
                (),
                {"model": Shelf, "fields": ("id",), "interfaces": (relay.Node,)},
            ),
        },
    )

    class _GenreFilter(FilterSet):
        class Meta:
            model = Genre
            fields = {"name": ["exact"]}

    type(
        "GenreType",
        (DjangoType,),
        {
            "Meta": type(
                "Meta",
                (),
                {
                    "model": Genre,
                    "fields": ("id", "name"),
                    "interfaces": (relay.Node,),
                    "filterset_class": _GenreFilter,
                },
            ),
        },
    )
    book_type = _make_type(
        "BookType",
        Book,
        (
            "id",
            "title",
            "shelf",
            "genres",
        ),
    )
    finalize_django_types()
    query_cls = strawberry.type(
        type(
            "Query",
            (),
            {"__annotations__": {"objs": list[book_type]}, "objs": DjangoListField(book_type)},
        ),
    )
    schema = strawberry.Schema(
        query=query_cls,
        config=strawberry_config(),
        extensions=[lambda: DjangoOptimizerExtension(strictness="raise")],
    )
    # ``shelf { id }`` is FK-id elided (planned); ``genresConnection(filter:)`` is
    # a sidecar fallback. The elided FK must NOT spuriously flag after the nested
    # connection's pipeline publishes its own plan.
    result = schema.execute_sync(
        "{ objs { shelf { id } "
        '  genresConnection(filter: { name: { exact: "fiction" } }) '
        "{ edges { node { name } } } } }",
        context_value=HttpRequest(),
    )
    assert result.errors is not None
    messages = [str(e.original_error or e) for e in result.errors]
    # The only flag is the unplanned connection; the elided ``shelf`` FK is silent.
    assert all("Unplanned N+1: shelf" not in m for m in messages), messages
    assert any(isinstance(e.original_error, OptimizerError) for e in result.errors)
    assert any("Unplanned N+1: genres (" in m for m in messages), messages


@pytest.mark.django_db
def test_strictness_silent_when_window_served():
    """``"raise"`` + a WINDOW-PLANNED nested connection -> no raise, no warn.

    The fast path served the rows under ``_dst_books_connection`` (the ``to_attr``
    is present on each parent), so ``_check_n1``'s connection lazy probe returns
    "not lazy" and the contract is silent. Wire result correct.
    """
    _seed_library_books(["apple", "banana", "avocado"])
    schema = _genres_list_schema(optimizer=True, strictness="raise")
    result = schema.execute_sync(
        "{ objs { booksConnection(first: 2) { edges { node { title } } } } }",
    )
    assert result.errors is None, result.errors
    titles = [e["node"]["title"] for e in result.data["objs"][0]["booksConnection"]["edges"]]
    assert titles == ["apple", "banana"]


@pytest.mark.django_db
def test_strictness_silent_when_off():
    """``"off"`` (optimizer installed) -> neither raise nor warn on a fallback.

    ``DST_OPTIMIZER_STRICTNESS == "off"`` is the resolver's no-op: no sentinel is
    stashed (the publish gates on ``strictness != "off"``), so ``_check_n1``'s
    prelude returns immediately even on the unplanned sidecar fallback.
    """
    _seed_library_books(["apple", "banana", "avocado"])
    schema = _genres_filterable_book_schema(strictness="off")
    result = schema.execute_sync(
        '{ objs { booksConnection(filter: { title: { exact: "banana" } }) '
        "{ edges { node { title } } } } }",
        context_value=HttpRequest(),
    )
    assert result.errors is None, result.errors
    titles = [e["node"]["title"] for e in result.data["objs"][0]["booksConnection"]["edges"]]
    assert titles == ["banana"]


@pytest.mark.django_db
def test_strictness_silent_no_optimizer():
    """No optimizer installed -> no sentinel stashed -> ``_check_n1`` is a no-op.

    The byte-identical pre-card behavior (and the root-shaped no-op of
    Implementation step 5): with no extension, ``DST_OPTIMIZER_PLANNED`` is never
    stashed, so the prelude returns before any probe - the per-parent pipeline
    runs exactly as before, no flag.
    """
    _seed_library_books(["apple", "banana", "avocado"])
    # No-optimizer variant: the plain list schema installs no extension at all,
    # so no sentinel is ever stashed (``strictness="raise"`` is inert here).
    schema = _genres_list_schema(optimizer=False, strictness="raise")
    result = schema.execute_sync(
        "{ objs { booksConnection(first: 2) { edges { node { title } } } } }",
    )
    assert result.errors is None, result.errors
    titles = [e["node"]["title"] for e in result.data["objs"][0]["booksConnection"]["edges"]]
    assert titles == ["apple", "banana"]


def test_strictness_silent_when_planned():
    """A planned connection key short-circuits BEFORE the ``to_attr`` probe.

    The load-bearing resolver-key parity (Implementation step 2): the resolver-
    side ``_check_n1`` builds ``resolver_key(declaring_type, relation_field_name,
    runtime_path)`` - the IDENTICAL shape the walker emits
    (``walker.py::_plan_connection_relation`` #"resolver_key(type_cls,
    relation_field_name, runtime_path)"). When that exact key is in
    ``DST_OPTIMIZER_PLANNED`` the resolver is silent even with the ``to_attr``
    ABSENT on ``root`` (the planned short-circuit beats the connection probe), so
    a window-planned connection never false-flags. A divergent key
    (generated ``books_connection`` name, or the target type) would miss the
    planned set and spuriously fire - this asserts the match directly.
    """
    from types import SimpleNamespace

    from django_strawberry_framework.exceptions import OptimizerError
    from django_strawberry_framework.optimizer.plans import resolver_key
    from django_strawberry_framework.types.resolvers import _check_n1

    class GenreType:
        pass

    # The walker keys a planned connection under (declaring type, RELATION FIELD
    # NAME, runtime path) - matched here at resolve time off ``info.path``.
    info = SimpleNamespace(
        context={
            "dst_optimizer_planned": {
                resolver_key(GenreType, "books", ("objs", "booksConnection")),
            },
            "dst_optimizer_strictness": "raise",
        },
        path=_path("objs", 0, "booksConnection"),
    )
    # ``to_attr`` absent on root (no window served), yet planned -> silent. The
    # call mirrors the connection.py consultation exactly.
    _check_n1(
        info,
        SimpleNamespace(),
        "books",
        GenreType,
        kind="connection_to_attr",
        to_attr="_dst_books_connection",
        reason="not window-planned; resolving per-parent",
    )

    # Sanity counter-proof: the SAME shape with the key absent DOES fire, so the
    # silence above is the planned-key match, not an inert no-op.
    info_unplanned = SimpleNamespace(
        context={"dst_optimizer_planned": set(), "dst_optimizer_strictness": "raise"},
        path=_path("objs", 0, "booksConnection"),
    )
    with pytest.raises(OptimizerError, match=r"Unplanned N\+1: books \("):
        _check_n1(
            info_unplanned,
            SimpleNamespace(),
            "books",
            GenreType,
            kind="connection_to_attr",
            to_attr="_dst_books_connection",
            reason="not window-planned; resolving per-parent",
        )


# ---------------------------------------------------------------------------
# Conditional ``_dst_total_count`` (connection window rigor, workstream B).
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_fast_path_count_less_window_serves_cheap_page(django_assert_num_queries):
    """A window planned WITHOUT the count still fast-paths the cheap page shape.

    ``edges`` + ``hasPreviousPage`` + cursors derive from ``_dst_row_number``
    alone, so the walker drops ``_dst_total_count`` (workstream B) and the
    relaxed row probe (``_window_rows_are_annotated``) still hands the rows to
    the fast path - fixed two-query cost, correct page, no per-parent
    fallback. The window SQL carries no count aggregate.
    """
    _seed_library_books(["a", "b", "c"])
    schema = _genres_list_schema(optimizer=True)
    query = (
        "{ objs { booksConnection(first: 2) { "
        "edges { cursor node { title } } pageInfo { hasPreviousPage startCursor } } } }"
    )
    from django.test.utils import CaptureQueriesContext

    with django_assert_num_queries(2), CaptureQueriesContext(db_connection) as captured:
        result = _exec(schema, query)
    conn = result.data["objs"][0]["booksConnection"]
    assert [e["node"]["title"] for e in conn["edges"]] == ["a", "b"]
    assert conn["pageInfo"]["hasPreviousPage"] is False
    assert conn["pageInfo"]["startCursor"] == conn["edges"][0]["cursor"]
    # The SQL-negative pin: the count window never compiled.
    window_sql = captured[1]["sql"]
    assert "_dst_row_number" in window_sql
    assert "_dst_total_count" not in window_sql


def test_count_less_window_with_count_observer_falls_back_defensively():
    """A count-less window whose selection OBSERVES the count returns ``None``.

    The workstream-B defensive tail in ``_resolve_from_window``, narrowed by
    The count-policy overhaul leaves only a ``totalCount``
    observer (``want_count=True``) on a window that carries no count annotation.
    Plan-time (``connection_count_required``) and resolve-time (``want_count``)
    share the selection walk, so this is unreachable live until they DRIFT -
    which is exactly when serving a fabricated count must lose to the per-parent
    fallback. The count-free ``hasNextPage`` shapes that USED to fall back here
    (bounded forward offset page, unbounded forward, reversed ``last: N``) are
    now SERVED count-free by the probe or the constant-False ``hasNextPage``
    (A1 / A2, covered in the live tier). ``want_count`` is NEVER exempt, so the
    guard still fires here; checked before any edge is built, so a stub ``cls``
    proves the early return.
    """
    from types import SimpleNamespace

    from django_strawberry_framework.connection import (
        _resolve_from_window,
        _WindowedConnectionRows,
    )

    inert_info = SimpleNamespace(selected_fields=[])

    # Plain forward page, ``totalCount`` requested, count annotation absent: the
    # count cannot be fabricated, so fall back per-parent.
    window = _WindowedConnectionRows(
        rows=[SimpleNamespace(_dst_row_number=1), SimpleNamespace(_dst_row_number=2)],
        fallback=lambda: None,
    )
    assert (
        _resolve_from_window(
            object,
            window,
            info=inert_info,
            offset=0,
            limit=2,
            want_count=True,
        )
        is None
    )

    # Marker-only page (offset > 0, page empty) with ``totalCount`` requested but
    # no count annotation: still drift - the empty-page count is observed and
    # cannot be inferred. (The SAME shape count-FREE is now SERVED, not dropped -
    # see the live edges-only / unbounded overshoot pins.)
    marker_only = _WindowedConnectionRows(
        rows=[SimpleNamespace(_dst_row_number=1)],
        fallback=lambda: None,
    )
    assert (
        _resolve_from_window(
            object,
            marker_only,
            info=inert_info,
            offset=5,
            limit=2,
            want_count=True,
        )
        is None
    )


# ---------------------------------------------------------------------------
# Consumer-assigned relation gate under strictness (workstream D).
# ---------------------------------------------------------------------------


def _shelves_with_consumer_books_schema(*, strictness="raise", books_hint=None):
    """Root ``objs: [ShelfType]`` where the consumer owns ``ShelfType.books``.

    The consumer resolver re-queries the relation (``order_by(...)[:2]``), so
    nested generated resolvers under its returned instances run against FRESH
    rows - the N+1 shape the workstream-D gate makes strictness-visible. The
    nested probe is the many-side ``loans`` (a reverse FK): Django's related
    manager seeds each child's FORWARD FK cache with the parent
    (known-related-objects), so a ``books { shelf }`` access never lazy-loads
    - the many side has no such seeding and is the real N+1.
    ``books_hint`` opts back in via ``Meta.optimizer_hints``.
    """

    class LoanType(DjangoType):
        class Meta:
            model = Loan
            fields = ("id", "note")

    class BookType(DjangoType):
        class Meta:
            model = Book
            fields = ("id", "title", "loans")

    def _curated_books(root) -> list[BookType]:
        return list(root.books.order_by("title")[:2])

    meta_ns = {"model": Shelf, "fields": ("id", "code", "books")}
    if books_hint is not None:
        meta_ns["optimizer_hints"] = {"books": books_hint}
    shelf_type = type(
        "ShelfType",
        (DjangoType,),
        {
            "__annotations__": {},
            "books": strawberry.field(resolver=_curated_books),
            "Meta": type("Meta", (), meta_ns),
        },
    )
    finalize_django_types()
    query_cls = strawberry.type(
        type(
            "Query",
            (),
            {"__annotations__": {"objs": list[shelf_type]}, "objs": DjangoListField(shelf_type)},
        ),
    )
    return strawberry.Schema(
        query=query_cls,
        config=strawberry_config(),
        extensions=[lambda: DjangoOptimizerExtension(strictness=strictness)],
    )


@pytest.mark.django_db
def test_consumer_assigned_relation_subtree_n1_visible_under_strictness():
    """The N+1 under a consumer-owned relation FIRES under strictness ``"raise"``.

    The workstream-D fix (strawberry-django #697 bug class): the walker used
    to record ``planned_resolver_keys`` for the consumer-owned relation's
    walked subtree, so the nested ``shelf`` accesses on the consumer
    resolver's FRESH instances short-circuited ``_check_n1`` and the real
    per-book lazy loads were SILENT under strictness. With the selection left
    fully unplanned, strictness sees them - the consumer's documented recourse
    is an explicit ``OptimizerHint`` (the sibling test).
    """
    branch = Branch.objects.create(name="central")
    shelf = Shelf.objects.create(code="A1", branch=branch)
    for title in ("a", "b"):
        Book.objects.create(title=title, shelf=shelf)

    schema = _shelves_with_consumer_books_schema(strictness="raise")
    result = schema.execute_sync(
        "{ objs { code books { title loans { note } } } }",
        context_value=HttpRequest(),
    )
    assert result.errors, "the unplanned subtree access must be strictness-visible"
    assert "Unplanned N+1" in str(result.errors[0])


@pytest.mark.django_db
def test_consumer_assigned_relation_with_hint_is_planned_and_silent():
    """``OptimizerHint.prefetch_related()`` opts the delegating resolver back in.

    With the hint declared, the walker plans the relation per the hint and
    records the resolver keys, so strictness stays silent - the documented
    migration for consumers whose resolver delegates to the relation.
    """
    branch = Branch.objects.create(name="central")
    shelf = Shelf.objects.create(code="A1", branch=branch)
    for title in ("a", "b"):
        Book.objects.create(title=title, shelf=shelf)

    schema = _shelves_with_consumer_books_schema(
        strictness="raise",
        books_hint=OptimizerHint.prefetch_related(),
    )
    result = schema.execute_sync(
        "{ objs { code books { title loans { note } } } }",
        context_value=HttpRequest(),
    )
    assert result.errors is None, result.errors
    titles = [b["title"] for b in result.data["objs"][0]["books"]]
    assert titles == ["a", "b"]


@pytest.mark.django_db
def test_fast_path_last_zero_visible_under_strictness():
    """``last: 0`` is a REAL per-parent fallback and strictness must see it.

    feedback2 P0-3: pre-fix the walker planned a reversed window for
    ``last: 0`` and recorded ``planned_resolver_keys``; the window was then
    discarded at resolve time and the per-parent fallback ran SILENTLY under
    ``strictness="raise"`` - a planned-then-fallback strictness hole. Fully
    unplanned, the shape now raises like every other Decision-6 fallback.
    """
    from django.http import HttpRequest

    _seed_library_books(["a", "b"])
    schema = _genres_list_schema(optimizer=True, book_total_count=True, strictness="raise")
    result = schema.execute_sync(
        "{ objs { booksConnection(last: 0) { totalCount } } }",
        context_value=HttpRequest(),
    )
    assert result.errors is not None
    assert any("Unplanned N+1" in str(error) for error in result.errors)


def test_resolve_from_window_last_zero_stays_a_defensive_guard():
    """The resolve-side ``last: 0`` guard survives as the defensive tail.

    The walker no longer plans the shape (feedback2 P0-3), so no live path
    reaches this branch - but ``_resolve_from_window`` must not ASSUME
    walker behavior (direct callers, plan/resolve drift). An empty reversed
    ``limit == 0`` window still refuses to serve (upstream's ``edges[-0:]``
    quirk needs the pipeline).
    """
    from django_strawberry_framework.connection import (
        _resolve_from_window,
        _WindowedConnectionRows,
    )

    window = _WindowedConnectionRows(rows=[], fallback=lambda: None)
    assert (
        _resolve_from_window(
            object,
            window,
            info=None,
            offset=0,
            limit=0,
            reverse=True,
            want_count=False,
        )
        is None
    )


def _windowed_book_connection_class(*, total_count=False):
    """A real generated ``<TypeName>Connection`` class for direct-call pins."""
    book_type = make_django_type(
        "BookType",
        Book,
        ("id", "title"),
        meta_extra={"connection": {"total_count": True}} if total_count else None,
    )
    finalize_django_types()
    return _connection_type_for(book_type)


@pytest.mark.django_db
def test_consume_window_unservable_window_runs_the_sync_fallback():
    """The unservable-window tail of ``_consume_window`` is a defensive layer.

    No live path produces it anymore (``last: 0`` is fully unplanned since
    feedback2 P0-3, and the ambiguous-empty shapes serve from markers), but
    the resolve side must not ASSUME walker behavior: a window the resolver
    refuses (here: the reversed ``last: 0`` quirk shape) recovers the
    carried per-parent queryset and runs the shipped sync pipeline.
    """
    from types import SimpleNamespace

    from django_strawberry_framework.connection import (
        _consume_window,
        _WindowedConnectionRows,
    )

    connection_cls = _windowed_book_connection_class()
    window = _WindowedConnectionRows(rows=[], fallback=lambda: Book.objects.none())
    conn = _consume_window(
        connection_cls,
        window,
        # The shipped pipeline probes ``info.selected_fields`` for the
        # edges-resolution shortcut; an empty selection list is enough.
        info=SimpleNamespace(selected_fields=[]),
        before=None,
        after=None,
        first=None,
        last=0,
        max_results=100,
        want_count=False,
    )
    assert conn.edges == []


@pytest.mark.django_db(transaction=True)
async def test_consume_window_unservable_window_runs_the_async_fallback():
    """The async sibling: an async-iterable fallback routes through
    ``_attach_count_async`` (the awaitable arm of ``_consume_fallback``)."""
    from types import SimpleNamespace

    from django_strawberry_framework.connection import (
        _consume_window,
        _WindowedConnectionRows,
    )

    connection_cls = _windowed_book_connection_class()

    async def _no_rows():
        return
        yield  # unreachable; makes this an async generator

    window = _WindowedConnectionRows(rows=[], fallback=_no_rows)
    conn = await _consume_window(
        connection_cls,
        window,
        info=SimpleNamespace(selected_fields=[]),
        before=None,
        after=None,
        first=None,
        last=0,
        max_results=100,
        want_count=False,
    )
    assert conn.edges == []
