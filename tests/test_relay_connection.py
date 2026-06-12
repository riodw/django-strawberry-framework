"""Relation-as-Connection tests for cursor conformance and Relay field upgrades.

Covers the ``Meta.relation_shapes`` Phase-2.5 synthesis surface
(``docs/spec-032-full_relay-0_0_9.md`` Decisions 6/7; Decision 11 pins the
card-named two-file split). The ``Meta``-key *validation* tests sit with the
other Meta validation in ``tests/types/test_base.py``. Package-internal by
spec mandate: finalization ``ConfigurationError``s cannot appear in the
example schema, and the synthesized-relation shape variants need cardinality
fixtures the fakeshop graph lacks until Slice 6 promotes ``BookType`` (the
live nested-connection proofs land there).

Pre-``033`` posture (Decision 12): the synthesized connections derive an
empty optimizer plan, so every execution assertion here pins behavior (rows,
pagination, argument presence) - never SQL shape.

The Slice-4 cursor-contract conformance mirror also runs here (the live
primary copies run in ``examples/fakeshop/test_query/test_library_api.py``
against the shipped ``allLibraryGenresConnection``): the synthesized-relation
variants need cardinality fixtures the fakeshop graph lacks until Slice 6.
"""

import pytest
import strawberry
from apps.library.models import Book, Branch, Genre, Loan, Shelf
from apps.products import services
from apps.products.models import Category, Item, Property
from django.db import connection as db_connection
from django.db import models as djmodels
from strawberry import relay

from django_strawberry_framework import (
    DjangoType,
    finalize_django_types,
    strawberry_config,
)
from django_strawberry_framework.connection import _connection_type_cache
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.filters import FilterSet, filter_input_type
from django_strawberry_framework.orders import OrderSet
from django_strawberry_framework.registry import registry


@pytest.fixture(autouse=True)
def _isolate_global_registry():
    """Clear the global registry and the connection-type cache around each test.

    Connection classes are cached on ``target_type`` identity; function-scope
    ``DjangoType`` fixtures are recreated fresh each test, so clearing the
    cache keeps a discarded class from leaking into a later test's identity
    check (the ``tests/test_connection.py`` fixture shape).
    """
    registry.clear()
    _connection_type_cache.clear()
    yield
    registry.clear()
    _connection_type_cache.clear()


def _make_type(
    name,
    model,
    fields,
    *,
    node=True,
    meta_extra=None,
    namespace_extra=None,
):
    """Declare a ``DjangoType`` over ``model`` (Relay-Node-shaped by default)."""
    meta_attrs = {"model": model, "fields": fields}
    if node:
        meta_attrs["interfaces"] = (relay.Node,)
    if meta_extra:
        meta_attrs.update(meta_extra)
    namespace = {"Meta": type("Meta", (), meta_attrs)}
    if namespace_extra:
        namespace.update(namespace_extra)
    return type(name, (DjangoType,), namespace)


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


# =============================================================================
# spec-032 Slice 4 - cursor-contract conformance on the synthesized relation
# connection (Decision 9). The live PRIMARY matrix runs against the shipped
# root ``allLibraryGenresConnection``; this mirror exercises the same matrix
# through the relation-manager-seeded pipeline on a reverse-FK cardinality
# fixture (``Shelf.books``) the fakeshop graph lacks until Slice 6,
# parametrized over the implicit ``"both"`` default and the narrowed
# ``"connection"`` shape. Behavior-only assertions (rows, cursors,
# ``pageInfo``) - never SQL shape (pre-``033`` posture).
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
