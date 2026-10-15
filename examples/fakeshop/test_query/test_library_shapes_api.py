"""Live GraphQL HTTP tests for the library relation shapes the optimizer plans specially.

One shape per planner rule, each read off the wire and off the SQL the request emitted:

- Relay id projection when the primary key IS a relation: ``PatronProfile.patron``
  is the one-to-one key, so ``PatronProfileType``'s id has to be built from the
  ``patron_id`` column instead of a lazy load of the related row.
- Digit-boundary names round-tripping to their real Django columns:
  ``Edition.isbn_10`` on a scalar, ``Edition.publisher_2`` on a forward key.
- Explicitly named fields resolving per published name: ``PatronProfileType``
  publishes ``address_2`` as ``secondaryAddress`` and ``postal_code`` as
  ``secondary_address``, two columns whose names differ only by casing convention.
- Forward-key id elision when the target's key is neither named ``id`` nor
  camel-case-stable: ``Printing.edition`` answers ``edition { isbn13 }`` from
  ``printing.edition_id``, and refuses to elide once a non-key edition column is
  selected.
- No elision through a ``to_field`` key: ``PatronProfile.favorite_genre`` stores
  the genre name, so ``favoriteGenre { id }`` still reads ``library_genre``.
- No elision into a custom ``relay.NodeID``: ``PublisherType`` publishes
  ``house_code`` as its node id, so ``publisher { id }`` still reads
  ``library_publisher``.
- A digit-boundary reverse accessor carrying a planned nested window:
  ``Publisher.printings_2`` pages as ``printings2Connection`` off one
  ``ROW_NUMBER() OVER (PARTITION BY ...)`` statement.
- A child default manager no strategy can window: ``AnnotationManager`` returns a
  distinct queryset, so ``PatronProfileType.annotationsConnection`` is left
  unplanned by ``optimizer/nested_planner.py`` and resolves per parent.
- A random child order the window cannot reproduce: ``Book`` ordered by ``"?"``
  or ``Random()`` - from a ``BookType.get_queryset`` hook (directly, reversed,
  under a composition, behind an annotation alias, a transform of one or an ``F``
  to one, in a ``When`` condition reading one) or from ``Meta.ordering`` - leaves
  ``GenreType.booksConnection`` unplanned, so each genre's page is one per-parent
  statement holding one random draw, structured exactly like the same window
  under a column order.
- Mixed-case Django names, whose published spelling reverses to a name the model
  lacks: ``Distributor.displayName`` projects its own column, the forward key
  ``Consignment.distributorRef`` plans one ``JOIN``, and its reverse
  ``consignmentItems`` loads through one prefetch on ``distributorRef_id``, the
  relation counts held at one and three parents.
- A model with no default order at all: ``ReadingListEntry`` clears its abstract
  parent's title ordering with ``ordering = None``, so a connection over entries
  with no ``orderBy:`` pages in primary-key order at the root and inside the
  nested window, while ``ReadingList`` keeps the title order it inherits; a
  resolver returning ``ReadingList.objects.order_by()`` switches that inherited
  order off, and its connection pages in primary-key order instead.
"""

from collections.abc import Callable

import pytest
import strawberry
from apps.library import models
from apps.library import schema as library_schema
from django.db import connection
from django.db.models import Case, F, FloatField, Q, QuerySet, Value, When
from django.db.models.functions import Abs, Random
from django.test.utils import CaptureQueriesContext, register_lookup
from graphql_client import JSONObject, assert_graphql_success
from strawberry.relay.utils import to_base64

from django_strawberry_framework.testing.relay import decode_global_id, global_id_for


def _sql_from_table(captured: CaptureQueriesContext, table: str) -> list[str]:
    """Return captured SQL whose ``FROM`` is exactly ``table`` (not a prefix match)."""
    needle = f'FROM "{table}"'
    return [entry["sql"] for entry in captured.captured_queries if needle in entry["sql"]]


def _sql_touching(captured: CaptureQueriesContext, table: str) -> list[str]:
    """Return captured SQL naming ``table`` anywhere - a ``FROM`` or a ``JOIN``."""
    needle = f'"{table}"'
    return [entry["sql"] for entry in captured.captured_queries if needle in entry["sql"]]


def _seed_two_patron_profiles() -> tuple[models.PatronProfile, models.PatronProfile]:
    """Two patrons with profiles; only the first carries a ``favorite_genre``."""
    genre = models.Genre.objects.create(name="Speculative")
    ada = models.Patron.objects.create(name="Ada")
    grace = models.Patron.objects.create(name="Grace")
    first = models.PatronProfile.objects.create(
        patron=ada,
        address_2="Flat 2",
        postal_code="02139",
        favorite_genre=genre,
    )
    second = models.PatronProfile.objects.create(
        patron=grace,
        address_2="Suite 7",
        postal_code="10001",
    )
    return first, second


def _seed_publishing_graph() -> tuple[models.Publisher, models.Publisher]:
    """Two publishers, one edition each, and press runs attributed to both houses."""
    first = models.Publisher.objects.create(name="Gollancz", house_code="HOUSE-G")
    second = models.Publisher.objects.create(name="Orbit", house_code="HOUSE-O")
    first_edition = models.Edition.objects.create(
        isbn_13="9780000000001",
        isbn_10="0000000001",
        imprint="Gollancz SF",
        publisher=first,
        publisher_2=second,
    )
    second_edition = models.Edition.objects.create(
        isbn_13="9780000000002",
        isbn_10="0000000002",
        imprint="Orbit Classics",
        publisher=second,
    )
    for run_size in (100, 200, 300):
        models.Printing.objects.create(
            edition=first_edition,
            publisher_2=first,
            run_size=run_size,
        )
    for run_size in (400, 500):
        models.Printing.objects.create(
            edition=second_edition,
            publisher_2=second,
            run_size=run_size,
        )
    return first, second


@pytest.mark.django_db
def test_patron_profile_relay_id_is_built_from_the_relation_primary_key_column() -> None:
    """A model whose primary key IS a relation mints its Relay id from the key column.

    ``PatronProfile.patron`` is a ``OneToOneField(primary_key=True)``, so the
    field name and the column an id projection must read (``patron_id``) differ.
    The page is one statement against ``library_patronprofile``: reading the id
    off the related row would cost a lazy ``library_patron`` load per edge.
    """
    first, second = _seed_two_patron_profiles()

    with CaptureQueriesContext(connection) as captured:
        data = assert_graphql_success(
            "{ allLibraryPatronProfilesConnection { edges { node { id } } } }",
        )

    edges = data["allLibraryPatronProfilesConnection"]["edges"]
    assert [edge["node"]["id"] for edge in edges] == [
        global_id_for(library_schema.PatronProfileType, first.patron_id),
        global_id_for(library_schema.PatronProfileType, second.patron_id),
    ], edges
    profile_sql = _sql_from_table(captured, "library_patronprofile")
    assert len(profile_sql) == 1, profile_sql
    assert "patron_id" in profile_sql[0], profile_sql[0]
    assert _sql_touching(captured, "library_patron") == [], captured.captured_queries


@pytest.mark.django_db
def test_edition_digit_boundary_names_project_their_own_django_columns() -> None:
    """``isbn10`` and ``publisher2`` resolve to the ``isbn_10`` / ``publisher_2_id`` columns.

    Both published names lose their ``<word>_<digit>`` boundary on the way to
    camelCase, so a name resolved by un-camel-casing alone would miss the model
    field. The values on the wire are the seeded ones and the root projection
    carries both real column names.
    """
    _seed_publishing_graph()

    with CaptureQueriesContext(connection) as captured:
        data = assert_graphql_success(
            "{ allLibraryEditions { isbn13 isbn10 publisher2 { name } } }",
        )

    assert data["allLibraryEditions"] == [
        {"isbn13": "9780000000001", "isbn10": "0000000001", "publisher2": {"name": "Orbit"}},
        {"isbn13": "9780000000002", "isbn10": "0000000002", "publisher2": None},
    ], data
    edition_sql = _sql_from_table(captured, "library_edition")
    assert len(edition_sql) == 1, edition_sql
    assert "isbn_10" in edition_sql[0], edition_sql[0]
    assert "publisher_2_id" in edition_sql[0], edition_sql[0]


@pytest.mark.django_db
def test_patron_profile_explicitly_named_fields_each_return_their_own_column() -> None:
    """``secondaryAddress`` and ``secondary_address`` are two columns, not one.

    ``PatronProfileType`` names ``address_2`` and ``postal_code`` with
    ``strawberry.field(name=...)``; the two published names normalize to the same
    string under a casing convention, so both are selected in ONE document - a
    resolution that matched on a normalized name would answer them alike.
    """
    _seed_two_patron_profiles()

    data = assert_graphql_success(
        """
        query {
          allLibraryPatronProfilesConnection {
            edges { node { secondaryAddress secondary_address } }
          }
        }
        """,
    )

    edges = data["allLibraryPatronProfilesConnection"]["edges"]
    assert [edge["node"] for edge in edges] == [
        {"secondaryAddress": "Flat 2", "secondary_address": "02139"},
        {"secondaryAddress": "Suite 7", "secondary_address": "10001"},
    ], edges


@pytest.mark.django_db
def test_printing_edition_key_only_selection_is_answered_from_the_stored_key_column() -> None:
    """``edition { isbn13 }`` is served from ``printing.edition_id`` alone.

    ``Edition``'s primary key is the text column ``isbn_13`` - not named ``id``
    and not camel-case-stable - so the elision has to resolve the target's real
    primary-key name before it can answer the selection from the source row.
    ``library_edition`` is neither joined nor prefetched.
    """
    _seed_publishing_graph()

    with CaptureQueriesContext(connection) as captured:
        data = assert_graphql_success(
            """
            query {
              allLibraryPrintingsConnection {
                edges { node { runSize edition { isbn13 } } }
              }
            }
            """,
        )

    edges = data["allLibraryPrintingsConnection"]["edges"]
    assert [edge["node"]["edition"]["isbn13"] for edge in edges] == [
        "9780000000001",
        "9780000000001",
        "9780000000001",
        "9780000000002",
        "9780000000002",
    ], edges
    printing_sql = _sql_from_table(captured, "library_printing")
    assert len(printing_sql) == 1, printing_sql
    assert "edition_id" in printing_sql[0], printing_sql[0]
    assert _sql_touching(captured, "library_edition") == [], captured.captured_queries


@pytest.mark.django_db
def test_printing_edition_non_key_selection_reads_the_edition_table() -> None:
    """The same relation joins the moment a non-key edition column is selected.

    The elision is scoped to a selection the source row can answer; ``imprint``
    is not the edition's primary key, so ``library_edition`` is read.
    """
    _seed_publishing_graph()

    with CaptureQueriesContext(connection) as captured:
        data = assert_graphql_success(
            """
            query {
              allLibraryPrintingsConnection {
                edges { node { edition { imprint } } }
              }
            }
            """,
        )

    edges = data["allLibraryPrintingsConnection"]["edges"]
    assert {edge["node"]["edition"]["imprint"] for edge in edges} == {
        "Gollancz SF",
        "Orbit Classics",
    }, edges
    assert _sql_touching(captured, "library_edition") != [], captured.captured_queries


@pytest.mark.django_db
def test_patron_profile_favorite_genre_id_still_reads_the_genre_table() -> None:
    """A ``to_field`` key cannot answer ``favoriteGenre { id }`` from the source row.

    ``PatronProfile.favorite_genre`` is declared ``to_field="name"``, so the
    stored column carries the genre's NAME, not its primary key; the id a client
    receives is built from the genre's own key and the genre row has to be read.
    """
    _seed_two_patron_profiles()
    genre = models.Genre.objects.get(name="Speculative")

    with CaptureQueriesContext(connection) as captured:
        data = assert_graphql_success(
            """
            query {
              allLibraryPatronProfilesConnection {
                edges { node { favoriteGenre { id } } }
              }
            }
            """,
        )

    edges = data["allLibraryPatronProfilesConnection"]["edges"]
    assert [edge["node"]["favoriteGenre"] for edge in edges] == [
        {"id": global_id_for(library_schema.GenreType, genre.pk)},
        None,
    ], edges
    assert _sql_touching(captured, "library_genre") != [], captured.captured_queries


@pytest.mark.django_db
def test_edition_publisher_id_still_reads_the_publisher_table_for_its_node_id() -> None:
    """A custom ``relay.NodeID`` moves the id payload off the stored key column.

    ``PublisherType`` declares ``house_code: relay.NodeID[str]``, so the id a
    client receives is built from a column ``edition.publisher_id`` does not
    carry: the relation keeps its read of ``library_publisher``, and the id
    decodes to the house code rather than to the publisher's primary key.
    """
    first, _second = _seed_publishing_graph()

    with CaptureQueriesContext(connection) as captured:
        data = assert_graphql_success("{ allLibraryEditions { publisher { id } } }")

    ids = [row["publisher"]["id"] for row in data["allLibraryEditions"]]
    assert ids[0] == global_id_for(library_schema.PublisherType, first.house_code), ids
    target_type, node_id = decode_global_id(ids[0])
    assert target_type is library_schema.PublisherType, target_type
    assert node_id == first.house_code, node_id
    assert node_id != str(first.pk), node_id
    assert _sql_touching(captured, "library_publisher") != [], captured.captured_queries


@pytest.mark.django_db
def test_publisher_printings_2_connection_pages_from_one_partitioned_window() -> None:
    """The ``<word>_<digit>`` reverse accessor pages off ONE window statement.

    ``Publisher.printings_2`` publishes as ``printings2Connection``; the nested
    planner resolves the accessor to the ``printings_2`` relation over the
    ``publisher_2_id`` column and plans a single ``ROW_NUMBER() OVER (PARTITION
    BY ...)`` fetch for both parents. Two publishers are seeded because one
    parent collapses to a plain filtered ``LIMIT`` on the single-parent fast
    path, which would carry no window at all.
    """
    _seed_publishing_graph()

    with CaptureQueriesContext(connection) as captured:
        data = assert_graphql_success(
            """
            query {
              allLibraryPublishersConnection {
                edges {
                  node {
                    name
                    printings2Connection(first: 2) {
                      edges { node { runSize } }
                      pageInfo { hasNextPage }
                    }
                  }
                }
              }
            }
            """,
        )

    nodes = [edge["node"] for edge in data["allLibraryPublishersConnection"]["edges"]]
    assert [node["name"] for node in nodes] == ["Gollancz", "Orbit"], nodes
    pages = [
        (
            [edge["node"]["runSize"] for edge in node["printings2Connection"]["edges"]],
            node["printings2Connection"]["pageInfo"]["hasNextPage"],
        )
        for node in nodes
    ]
    assert pages == [([100, 200], True), ([400, 500], False)], pages
    printing_sql = _sql_from_table(captured, "library_printing")
    assert len(printing_sql) == 1, printing_sql
    windowed = printing_sql[0].upper()
    assert "ROW_NUMBER() OVER (" in windowed, printing_sql[0]
    assert "PARTITION BY" in windowed, printing_sql[0]
    assert "PUBLISHER_2_ID" in windowed, printing_sql[0]


@pytest.mark.django_db
def test_patron_profile_annotations_connection_is_left_unplanned_and_fetched_per_parent() -> None:
    """A distinct default manager leaves the whole nested relation unplanned.

    ``AnnotationManager.get_queryset`` returns ``.distinct()``, which
    ``optimizer/nested_fetch.py::unwindowable_child_queryset_reason`` classifies
    as unwindowable: SQL evaluates window functions before ``DISTINCT``, so the
    planner refuses the relation outright rather than emit an over-counted
    window. Observably that is no ``OVER (`` anywhere in the annotation SQL and
    one ``library_annotation`` statement per parent - with the pages still
    correct, which is what makes the refusal a fallback rather than a hole.
    """
    first, second = _seed_two_patron_profiles()
    for body in ("first note", "second note", "third note"):
        models.Annotation.objects.create(profile=first, body=body)
    models.Annotation.objects.create(profile=second, body="only note")

    with CaptureQueriesContext(connection) as captured:
        data = assert_graphql_success(
            """
            query {
              allLibraryPatronProfilesConnection {
                edges {
                  node {
                    annotationsConnection(first: 2) {
                      edges { node { body } }
                      pageInfo { hasNextPage }
                    }
                  }
                }
              }
            }
            """,
        )

    nodes = [edge["node"] for edge in data["allLibraryPatronProfilesConnection"]["edges"]]
    pages = [
        (
            [edge["node"]["body"] for edge in node["annotationsConnection"]["edges"]],
            node["annotationsConnection"]["pageInfo"]["hasNextPage"],
        )
        for node in nodes
    ]
    assert pages == [(["first note", "second note"], True), (["only note"], False)], pages
    annotation_sql = _sql_from_table(captured, "library_annotation")
    assert len(annotation_sql) == len(nodes), annotation_sql
    assert not any("OVER (" in sql.upper() for sql in annotation_sql), annotation_sql


def _seed_distributors(count: int) -> list[models.Distributor]:
    """``count`` distributors with one consignment each, both numbered from zero."""
    distributors: list[models.Distributor] = []
    for index in range(count):
        distributor = models.Distributor.objects.create(displayName=f"Distributor {index}")
        models.Consignment.objects.create(label=f"Consignment {index}", distributorRef=distributor)
        distributors.append(distributor)
    return distributors


@pytest.mark.django_db
def test_distributor_mixed_case_scalar_projects_its_own_column() -> None:
    """``displayName`` is served by one statement projecting the ``displayName`` column.

    Strawberry publishes the Django name unchanged; reversing it gives
    ``display_name``, which names no field, so the selection resolves by its exact
    published name and the root projection carries the real column.
    """
    distributors = _seed_distributors(2)

    with CaptureQueriesContext(connection) as captured:
        data = assert_graphql_success("{ allLibraryDistributors { id displayName } }")

    assert sorted(data["allLibraryDistributors"], key=lambda row: row["id"]) == [
        {"id": distributor.pk, "displayName": distributor.displayName}
        for distributor in distributors
    ], data
    distributor_sql = _sql_touching(captured, "library_distributor")
    assert len(distributor_sql) == 1, captured.captured_queries
    assert '"displayName"' in distributor_sql[0], distributor_sql[0]


@pytest.mark.parametrize("distributor_count", [1, 3])
@pytest.mark.django_db
def test_consignment_mixed_case_forward_key_joins_its_target_in_one_statement(
    distributor_count: int,
) -> None:
    """``distributorRef { displayName }`` is one ``JOIN`` at every parent cardinality.

    ``distributorRef`` reverses to ``distributor_ref``, which names no relation;
    resolved by its published name, the key plans a ``select_related`` whose
    joined projection carries the target's mixed-case ``displayName`` column.
    """
    _seed_distributors(distributor_count)

    with CaptureQueriesContext(connection) as captured:
        data = assert_graphql_success(
            "{ allLibraryConsignments { label distributorRef { displayName } } }",
        )

    assert sorted(
        (row["label"], row["distributorRef"]["displayName"])
        for row in data["allLibraryConsignments"]
    ) == [(f"Consignment {index}", f"Distributor {index}") for index in range(distributor_count)]
    distributor_sql = _sql_touching(captured, "library_distributor")
    assert len(distributor_sql) == 1, captured.captured_queries
    assert _sql_from_table(captured, "library_consignment") == distributor_sql
    assert 'JOIN "library_distributor"' in distributor_sql[0], distributor_sql[0]
    assert '"displayName"' in distributor_sql[0], distributor_sql[0]


@pytest.mark.parametrize("distributor_count", [1, 3])
@pytest.mark.django_db
def test_distributor_mixed_case_reverse_relation_loads_through_one_prefetch(
    distributor_count: int,
) -> None:
    """``consignmentItems`` loads every parent's rows in one statement at every cardinality.

    The ``related_name`` ``consignmentItems`` reverses to ``consignment_items``,
    which names no relation; resolved by its published name it plans one prefetch
    filtered on the mixed-case ``distributorRef_id`` column.
    """
    _seed_distributors(distributor_count)

    with CaptureQueriesContext(connection) as captured:
        data = assert_graphql_success(
            "{ allLibraryDistributors { displayName consignmentItems { label } } }",
        )

    assert sorted(
        (row["displayName"], [item["label"] for item in row["consignmentItems"]])
        for row in data["allLibraryDistributors"]
    ) == [(f"Distributor {index}", [f"Consignment {index}"]) for index in range(distributor_count)]
    assert len(_sql_from_table(captured, "library_distributor")) == 1, captured.captured_queries
    consignment_sql = _sql_from_table(captured, "library_consignment")
    assert len(consignment_sql) == 1, captured.captured_queries
    assert '"distributorRef_id" IN (' in consignment_sql[0], consignment_sql[0]


def _seed_reading_lists() -> tuple[models.ReadingList, models.ReadingList]:
    """Two reading lists, each with entries added out of alphabetical order."""
    classics = models.ReadingList.objects.create(title="Classics")
    anthology = models.ReadingList.objects.create(title="Anthology")
    for title in ("Solaris", "Dune", "Anathem"):
        models.ReadingListEntry.objects.create(reading_list=classics, title=title)
    models.ReadingListEntry.objects.create(reading_list=anthology, title="Kindred")
    return classics, anthology


@pytest.mark.django_db
def test_reading_list_entries_connection_pages_in_primary_key_order_with_ordering_none() -> None:
    """A root connection over an ``ordering = None`` model pages in primary-key order.

    ``ReadingListEntry`` clears its abstract parent's ``Meta.ordering`` with
    ``None``, which Django accepts and treats as no default order. With no
    ``orderBy:`` and no ``Meta.cursor_field`` the connection's total order is the
    pk tiebreaker alone: the entries come back in insertion order, not by title.
    """
    _seed_reading_lists()

    with CaptureQueriesContext(connection) as captured:
        data = assert_graphql_success(
            """
            query {
              allLibraryReadingListEntriesConnection(first: 3) {
                edges { node { title } }
                pageInfo { hasNextPage }
              }
            }
            """,
        )

    page = data["allLibraryReadingListEntriesConnection"]
    assert [edge["node"]["title"] for edge in page["edges"]] == ["Solaris", "Dune", "Anathem"], (
        page
    )
    assert page["pageInfo"]["hasNextPage"] is True, page
    entry_sql = _sql_from_table(captured, "library_readinglistentry")
    assert len(entry_sql) == 1, captured.captured_queries
    assert 'ORDER BY "library_readinglistentry"."id" ASC' in entry_sql[0], entry_sql[0]


@pytest.mark.django_db
def test_reading_list_entries_nested_connection_windows_in_primary_key_order() -> None:
    """The nested window over an ``ordering = None`` child orders each partition by pk.

    Two parents so the nested planner builds its ``ROW_NUMBER() OVER (PARTITION
    BY ...)`` window rather than the single-parent fast path. The child model
    brings no default order, so the window orders by the pk tiebreaker alone;
    the parent ``ReadingList`` keeps the ``title`` order it inherits, which is
    why "Anthology" leads.
    """
    _seed_reading_lists()

    with CaptureQueriesContext(connection) as captured:
        data = assert_graphql_success(
            """
            query {
              allLibraryReadingListsConnection {
                edges {
                  node {
                    title
                    entriesConnection(first: 2) {
                      edges { node { title } }
                      pageInfo { hasNextPage }
                    }
                  }
                }
              }
            }
            """,
        )

    nodes = [edge["node"] for edge in data["allLibraryReadingListsConnection"]["edges"]]
    pages = [
        (
            node["title"],
            [edge["node"]["title"] for edge in node["entriesConnection"]["edges"]],
            node["entriesConnection"]["pageInfo"]["hasNextPage"],
        )
        for node in nodes
    ]
    assert pages == [
        ("Anthology", ["Kindred"], False),
        ("Classics", ["Solaris", "Dune"], True),
    ], pages
    entry_sql = _sql_from_table(captured, "library_readinglistentry")
    assert len(entry_sql) == 1, entry_sql
    windowed = entry_sql[0].upper()
    assert "ROW_NUMBER() OVER (" in windowed, entry_sql[0]
    assert "PARTITION BY" in windowed, entry_sql[0]
    assert 'ORDER BY "LIBRARY_READINGLISTENTRY"."ID" ASC' in windowed, entry_sql[0]


@pytest.mark.django_db
def test_reading_lists_connection_honors_a_cleared_default_ordering() -> None:
    """A source whose ``.order_by()`` cleared ``Meta.ordering`` pages in primary-key order.

    Django compiles no ``Meta.ordering`` once ``query.default_ordering`` is off,
    so the connection's total order is the pk tiebreaker alone: "Classics"
    (created first) leads, where the same model's plain connection leads with
    "Anthology" under the inherited title order.
    """
    _seed_reading_lists()

    with CaptureQueriesContext(connection) as captured:
        data = assert_graphql_success(
            """
            query {
              allLibraryReadingListsUnorderedConnection {
                edges { node { title } }
              }
            }
            """,
        )

    titles = [
        edge["node"]["title"]
        for edge in data["allLibraryReadingListsUnorderedConnection"]["edges"]
    ]
    assert titles == ["Classics", "Anthology"], titles
    list_sql = _sql_from_table(captured, "library_readinglist")
    assert len(list_sql) == 1, captured.captured_queries
    assert 'ORDER BY "library_readinglist"."id" ASC' in list_sql[0], list_sql[0]
    assert '"library_readinglist"."title" ASC' not in list_sql[0], list_sql[0]


#: Each genre's ``booksConnection`` page under one window shape, with every edge cursor
#: and the full ``pageInfo``: the page STRUCTURE, which no total order changes.
_SHUFFLED_BOOKS_QUERY = """
query {
  allLibraryGenresConnection {
    edges {
      node {
        name
        booksConnection(%s) {
          edges { cursor node { title } }
          pageInfo { hasNextPage hasPreviousPage startCursor endCursor }
        }
      }
    }
  }
}
"""

#: The four window shapes a nested page is planned under: forward, reversed, and each
#: bounded by a cursor.
_SHUFFLED_BOOKS_WINDOWS = {
    "first": "first: 2",
    "last": "last: 2",
    "first-after": f'first: 2, after: "{to_base64("arrayconnection", 0)}"',
    "last-before": f'last: 2, before: "{to_base64("arrayconnection", 3)}"',
}

_BookShuffle = Callable[[QuerySet[models.Book]], QuerySet[models.Book]]

#: A hook-side random order per row: ``"?"`` and the ``Random()`` expression, each
#: directly and reversed; ``Random()`` under a composition; ``Random()`` behind an
#: annotation alias - by name, descending, through a transform, under a name holding
#: ``__``, and through an ``F``; and a ``When`` condition reading ``Random()`` - through
#: a lookup on an alias, a ``Q`` combination, a negated ``Q`` beside a plain lookup, a
#: lookup value, and an alias of the ``Case``.
_RANDOM_BOOK_HOOK_ORDERS: dict[str, _BookShuffle] = {
    "hook-name": lambda books: books.order_by("?"),
    "hook-expression": lambda books: books.order_by(Random()),
    "hook-reversed-name": lambda books: books.order_by("?").reverse(),
    "hook-reversed-expression": lambda books: books.order_by(Random()).reverse(),
    "hook-composition": lambda books: books.order_by((Random() + Value(0.0)).asc()),
    "hook-alias": lambda books: books.annotate(shuffle=Random()).order_by("shuffle"),
    "hook-alias-descending": lambda books: books.annotate(shuffle=Random()).order_by(
        "-shuffle",
    ),
    "hook-alias-transform": lambda books: books.annotate(shuffle=Random()).order_by(
        "shuffle__abs",
    ),
    "hook-alias-transform-descending": lambda books: books.annotate(
        shuffle=Random(),
    ).order_by("-shuffle__abs"),
    "hook-alias-dunder": lambda books: books.annotate(shuffle__x=Random()).order_by(
        "shuffle__x",
    ),
    "hook-condition": lambda books: books.annotate(coin=Random()).order_by(
        Case(When(coin__gt=0.5, then=Value(1)), default=Value(0)).asc(),
    ),
    "hook-condition-q": lambda books: books.annotate(coin=Random()).order_by(
        Case(When(Q(coin__gt=0.7) | Q(coin__lt=0.3), then=Value(1)), default=Value(0)),
    ),
    "hook-condition-negated": lambda books: books.annotate(coin=Random()).order_by(
        Case(When(Q(title__gt="") & ~Q(coin__lt=0.3), then=Value(1)), default=Value(0)),
    ),
    "hook-condition-value": lambda books: books.order_by(
        Case(When(id__gt=Random() * 1000, then=Value(1)), default=Value(0)),
    ),
    "hook-condition-alias": lambda books: books.annotate(
        coin=Random(),
        heads=Case(When(coin__gt=0.5, then=Value(1)), default=Value(0)),
    ).order_by("heads"),
    "hook-reference": lambda books: books.annotate(shuffle=Random()).order_by(F("shuffle")),
    "hook-reference-descending": lambda books: books.annotate(shuffle=Random()).order_by(
        F("shuffle").desc(),
    ),
}

#: A ``Meta.ordering`` random order per row: the ``"?"`` name, the expression, and the
#: expression wrapped in a direction.
_RANDOM_BOOK_META_ORDERS: dict[str, tuple[object, ...]] = {
    "meta-name": ("?",),
    "meta-expression": (Random(),),
    "meta-composition": (Random().desc(),),
}


def _seed_shuffled_genres() -> dict[str, set[str]]:
    """Three genres holding five, one and no books; returns each genre's titles."""
    branch = models.Branch.objects.create(name="Central", city="Boston")
    shelf = models.Shelf.objects.create(code="A-1", topic="Fiction", branch=branch)
    shelved = {"Speculative": 5, "Poetry": 1, "Empty": 0}
    titles: dict[str, set[str]] = {}
    for name, count in shelved.items():
        genre = models.Genre.objects.create(name=name)
        titles[name] = {f"{name} {index}" for index in range(count)}
        for title in sorted(titles[name]):
            genre.books.add(models.Book.objects.create(title=title, shelf=shelf))
    return titles


def _shuffled_books_pages(window: str) -> tuple[dict[str, JSONObject], list[str]]:
    """Each genre's ``booksConnection`` page under ``window``, and the ``library_book`` SQL."""
    with CaptureQueriesContext(connection) as captured:
        data = assert_graphql_success(_SHUFFLED_BOOKS_QUERY % _SHUFFLED_BOOKS_WINDOWS[window])
    pages = {
        edge["node"]["name"]: edge["node"]["booksConnection"]
        for edge in data["allLibraryGenresConnection"]["edges"]
    }
    return pages, _sql_from_table(captured, "library_book")


def _page_structure(page: JSONObject) -> tuple[list[str], JSONObject]:
    """The order-independent half of a page: its edge cursors and its ``pageInfo``."""
    return [edge["cursor"] for edge in page["edges"]], page["pageInfo"]


@pytest.mark.parametrize("window", list(_SHUFFLED_BOOKS_WINDOWS))
@pytest.mark.parametrize("source", [*_RANDOM_BOOK_HOOK_ORDERS, *_RANDOM_BOOK_META_ORDERS])
@pytest.mark.django_db
def test_random_book_order_leaves_genre_books_connection_to_the_per_parent_pipeline(
    source: str,
    window: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A random child order is served per parent, one random draw per page.

    The nested window evaluates its order more than once in one statement - the
    row-number window, the reversed window of a ``last:`` page and the outer
    ``ORDER BY`` - and a random term is a new draw at each, while a bare ``"?"``
    cannot be a window order term at all. So ``booksConnection`` is left unplanned
    under every spelling: one ``library_book`` statement per genre (three), none a
    window, each ordering by the database's random function. Every page is then a
    slice of ONE permutation, so its edge cursors and ``pageInfo`` are exactly the
    ones the shipped primary-key order serves through its window first (one
    windowed statement), and its titles are distinct books of that genre.
    """
    titles = _seed_shuffled_genres()
    planned, planned_sql = _shuffled_books_pages(window)
    assert [len(planned_sql), "OVER (" in planned_sql[0]] == [1, True], planned_sql

    if source in _RANDOM_BOOK_HOOK_ORDERS:
        shuffle = _RANDOM_BOOK_HOOK_ORDERS[source]
        shipped_hook = library_schema.BookType.get_queryset

        def shuffled_hook(
            _cls: type[library_schema.BookType],
            queryset: QuerySet[models.Book],
            info: strawberry.Info[object, object],
        ) -> QuerySet[models.Book]:
            return shuffle(shipped_hook(queryset, info))

        monkeypatch.setattr(library_schema.BookType, "get_queryset", classmethod(shuffled_hook))
    else:
        monkeypatch.setattr(models.Book._meta, "ordering", _RANDOM_BOOK_META_ORDERS[source])
    # The transform rows order through ``abs``, which Django registers on no field by default.
    with register_lookup(FloatField, Abs):
        shuffled, shuffled_sql = _shuffled_books_pages(window)

    assert len(shuffled_sql) == len(titles), shuffled_sql
    assert [("OVER (" in sql, "RAND" in sql.upper()) for sql in shuffled_sql] == [
        (False, True),
    ] * len(titles), shuffled_sql
    for name, genre_titles in titles.items():
        served = [edge["node"]["title"] for edge in shuffled[name]["edges"]]
        assert len(set(served)) == len(served), (name, served)
        assert set(served) <= genre_titles, (name, served)
        assert _page_structure(shuffled[name]) == _page_structure(planned[name]), name


#: A ``When`` condition comparing a column to a string literal spelled like a random
#: order: ``"?"``, and the name of a random annotation. A condition reads a reference
#: only through ``F``, so neither literal is random.
_LITERAL_CONDITION_BOOK_ORDERS: dict[str, _BookShuffle] = {
    "question-mark": lambda books: books.order_by(
        Case(When(title="?", then=Value(1)), default=Value(0)),
        "pk",
    ),
    "annotation-name": lambda books: books.annotate(shuffle=Random()).order_by(
        Case(When(title="shuffle", then=Value(1)), default=Value(0)),
        "pk",
    ),
}


@pytest.mark.parametrize("window", list(_SHUFFLED_BOOKS_WINDOWS))
@pytest.mark.parametrize("source", list(_LITERAL_CONDITION_BOOK_ORDERS))
@pytest.mark.django_db
def test_string_literal_in_a_book_order_condition_keeps_genre_books_connection_windowed(
    source: str,
    window: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A condition's string literal is no random term: the nested window still plans.

    Every book's condition answers the default, so the order is the primary key
    and each genre's page, cursors and ``pageInfo`` equal the shipped order's,
    served from one windowed ``library_book`` statement.
    """
    _seed_shuffled_genres()
    planned, _ = _shuffled_books_pages(window)
    order = _LITERAL_CONDITION_BOOK_ORDERS[source]
    shipped_hook = library_schema.BookType.get_queryset

    def literal_hook(
        _cls: type[library_schema.BookType],
        queryset: QuerySet[models.Book],
        info: strawberry.Info[object, object],
    ) -> QuerySet[models.Book]:
        return order(shipped_hook(queryset, info))

    monkeypatch.setattr(library_schema.BookType, "get_queryset", classmethod(literal_hook))
    served, served_sql = _shuffled_books_pages(window)

    assert [len(served_sql), "OVER (" in served_sql[0]] == [1, True], served_sql
    assert served == planned
