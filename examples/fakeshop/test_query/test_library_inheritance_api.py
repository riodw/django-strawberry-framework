"""Live GraphQL HTTP tests for the library inheritance, proxy, and relation-shape surface.

Each row reads one shape off the wire and, where the claim is a cost or a
query shape, off the SQL the request emitted:

- Multi-table inheritance: ``LendingDesk`` and ``SelfServeDesk`` project their
  inherited ``Venue`` columns through the parent-link join in one statement,
  order by the inherited ``opened_on`` column, and are hidden with their
  ``Venue`` row because the visibility cascade walks the ``<parent>_ptr``
  link (transitively for the two-level chain).
- Reverse relations declared without ``related_name``:
  ``VenueType.repairticket`` / ``venuebadge`` / ``venuesponsor`` resolve
  through Django's default accessors, each batched once, and the rows the
  badge and sponsor hooks hide are absent from those accessors and from both
  roots.
- The nullable ``Venue.lead_ticket`` <-> ``RepairTicket.venue`` cycle:
  ``VenueType`` cascades over the nullable key (a venue with no lead ticket
  stays visible, one whose lead ticket is hidden does not) and
  ``RepairTicketType`` does not cascade back, so the walk never re-enters.
- Proxies with a filtering default manager: ``allLibraryOpenVenues`` is the
  ``OpenVenue`` manager's rows, and a ``BranchSignage`` row declared to the
  ``VisibleBranch`` proxy is hidden when that manager hides its branch.
- ``CirculationDesk``, one model carrying every relation kind: its reverse
  ``children`` / ``profile`` resolve, and its cascade scoped to ``branch`` /
  ``shelf`` serves rows despite the generic foreign key a full walk refuses.
- A multi-column forward ``ForeignObject``: ``ShelfLabel.shelf`` is held in
  ``branch`` and ``shelf_code``; the ``"__all__"`` ``ShelfLabelOrder`` publishes
  it after its carriers, a ``shelf`` term orders by both carriers in one
  statement, and a label on a shelf ``ShelfType`` hides, or naming no shelf at
  all, stays listed and sorts as one with none; behind the to-many
  ``BranchOrder.shelf_labels`` hop each carrier is aggregated per branch and
  correlated to the label's own carrier columns.
- Write-input requiredness: ``Book.archive_genres`` (``editable=False``) is
  absent from both generated ``Book`` inputs, and ``MediaSpecimen``'s optional
  file columns are optional through the ``blank`` arm and the ``null`` arm
  separately.
"""

import datetime
import re

import pytest
from apps.library import models
from apps.products.services import create_users
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.db import connection
from django.test import Client
from django.test.utils import CaptureQueriesContext
from graphql_client import assert_graphql_success


def _sql_from_table(captured: CaptureQueriesContext, table: str) -> list[str]:
    """Return captured SQL whose OUTER ``FROM`` is ``table``, not a subquery's."""
    return [
        entry["sql"]
        for entry in captured.captured_queries
        if entry["sql"].split(" FROM ", 1)[-1].startswith(f'"{table}"')
    ]


def _select_list(sql: str) -> str:
    """Return the projection of ``sql``: the text between ``SELECT`` and the first ``FROM``."""
    return sql.split(" FROM ", 1)[0]


def _seed_desks() -> None:
    """Three lending desks, one under a closed venue, and two kiosks, one closed."""
    models.LendingDesk.objects.create(
        name="North Desk",
        opened_on=datetime.date(2020, 1, 1),
        window_count=2,
    )
    models.LendingDesk.objects.create(
        name="Closed East Desk",
        opened_on=datetime.date(2019, 1, 1),
        window_count=1,
    )
    models.LendingDesk.objects.create(
        name="South Desk",
        opened_on=datetime.date(2021, 1, 1),
        window_count=3,
    )
    models.SelfServeDesk.objects.create(
        name="Lobby Kiosk",
        opened_on=datetime.date(2022, 1, 1),
        window_count=0,
        kiosk_code="K-1",
    )
    models.SelfServeDesk.objects.create(
        name="Closed Annex Kiosk",
        opened_on=datetime.date(2018, 1, 1),
        window_count=0,
        kiosk_code="K-2",
    )


def _introspect_input_fields(type_name: str) -> dict[str, dict[str, object]]:
    """Return ``{field name: type}`` for the input object ``type_name`` over HTTP."""
    data = assert_graphql_success(
        f'{{ __type(name: "{type_name}") {{ inputFields {{ name type {{ kind name ofType '
        "{ kind name } } } } }",
    )
    return {field["name"]: field["type"] for field in data["__type"]["inputFields"]}


@pytest.mark.django_db
def test_lending_desk_projects_inherited_columns_through_the_parent_link_join():
    """``name`` is read from ``library_venue`` in the same statement as ``windowCount``.

    ``LendingDesk`` stores only ``window_count`` on its own table; ``name`` and
    ``opened_on`` live on ``library_venue`` behind the ``venue_ptr`` parent
    link. The optimizer's projection names the inherited column, so the page is
    one ``library_lendingdesk`` statement joining ``library_venue`` - and the
    unselected inherited ``opened_on`` is not projected.
    """
    _seed_desks()

    with CaptureQueriesContext(connection) as captured:
        data = assert_graphql_success("{ allLibraryLendingDesks { name windowCount } }")

    assert data["allLibraryLendingDesks"] == [
        {"name": "North Desk", "windowCount": 2},
        {"name": "South Desk", "windowCount": 3},
        {"name": "Lobby Kiosk", "windowCount": 0},
    ], data
    desk_sql = _sql_from_table(captured, "library_lendingdesk")
    assert len(desk_sql) == 1, captured.captured_queries
    assert len(captured.captured_queries) == 1, captured.captured_queries
    assert 'INNER JOIN "library_venue"' in desk_sql[0], desk_sql[0]
    projection = _select_list(desk_sql[0])
    assert '"library_venue"."name"' in projection, projection
    assert '"library_lendingdesk"."window_count"' in projection, projection
    assert '"library_venue"."opened_on"' not in projection, projection


@pytest.mark.django_db
def test_self_serve_desk_reads_both_parent_tables_in_one_statement():
    """A two-level chain joins both parent tables and projects a column from each.

    ``SelfServeDesk`` extends ``LendingDesk``, which extends ``Venue``, so
    ``kioskCode`` is local, ``windowCount`` one parent link away and ``name``
    two. One statement carries all three, and the unselected ``opened_on``
    stays out of the projection.
    """
    _seed_desks()

    with CaptureQueriesContext(connection) as captured:
        data = assert_graphql_success(
            "{ allLibrarySelfServeDesks { name windowCount kioskCode } }",
        )

    assert data["allLibrarySelfServeDesks"] == [
        {"name": "Lobby Kiosk", "windowCount": 0, "kioskCode": "K-1"},
    ], data
    assert len(captured.captured_queries) == 1, captured.captured_queries
    sql = captured.captured_queries[0]["sql"]
    assert 'INNER JOIN "library_lendingdesk"' in sql, sql
    assert 'INNER JOIN "library_venue"' in sql, sql
    projection = _select_list(sql)
    assert '"library_venue"."name"' in projection, projection
    assert '"library_lendingdesk"."window_count"' in projection, projection
    assert '"library_venue"."opened_on"' not in projection, projection


@pytest.mark.django_db
def test_lending_desks_order_by_the_inherited_opened_on_column():
    """``orderBy: openedOn`` sorts desks by the parent table's column, in each direction.

    ``opened_on`` is declared on ``Venue``; ``LendingDeskOrder`` publishes it,
    and the ``ORDER BY`` names ``library_venue`` rather than the child table.
    Both directions are read so a lost direction cannot pass.
    """
    _seed_desks()

    with CaptureQueriesContext(connection) as captured:
        descending = assert_graphql_success(
            "{ allLibraryLendingDesks(orderBy: [{ openedOn: DESC }]) { name } }",
        )
    # Read the capture before the next request: Django clears the query log on
    # every ``request_started``, and the capture slices that log lazily.
    (sql,) = _sql_from_table(captured, "library_lendingdesk")
    ascending = assert_graphql_success(
        "{ allLibraryLendingDesks(orderBy: [{ openedOn: ASC }]) { name } }",
    )

    assert [row["name"] for row in descending["allLibraryLendingDesks"]] == [
        "Lobby Kiosk",
        "South Desk",
        "North Desk",
    ], descending
    assert [row["name"] for row in ascending["allLibraryLendingDesks"]] == [
        "North Desk",
        "South Desk",
        "Lobby Kiosk",
    ], ascending
    assert 'ORDER BY "library_venue"."opened_on" DESC' in sql, sql


@pytest.mark.django_db
def test_parent_link_cascade_hides_a_desk_whose_venue_is_hidden():
    """A desk under a closed ``Venue`` is hidden through the ``<parent>_ptr`` cascade.

    ``VenueType.get_queryset`` hides venues named ``Closed ...``;
    ``LendingDeskType`` cascades over ``venue_ptr`` and ``SelfServeDeskType``
    over ``lendingdesk_ptr`` into it, so the closed desk and the closed kiosk
    drop out of both roots while their rows still exist. A parent link is never
    null, so the desk statement tests ``venue_ptr_id`` membership with no
    ``IS NULL`` branch beside it.
    """
    _seed_desks()

    with CaptureQueriesContext(connection) as captured:
        desks = assert_graphql_success("{ allLibraryLendingDesks { name } }")
    (desk_sql,) = _sql_from_table(captured, "library_lendingdesk")
    kiosks = assert_graphql_success("{ allLibrarySelfServeDesks { name } }")

    assert [row["name"] for row in desks["allLibraryLendingDesks"]] == [
        "North Desk",
        "South Desk",
        "Lobby Kiosk",
    ], desks
    assert [row["name"] for row in kiosks["allLibrarySelfServeDesks"]] == ["Lobby Kiosk"], kiosks
    assert models.LendingDesk.objects.filter(name="Closed East Desk").exists()
    assert models.SelfServeDesk.objects.filter(name="Closed Annex Kiosk").exists()
    assert '"library_lendingdesk"."venue_ptr_id" IN (SELECT' in desk_sql, desk_sql
    assert '"library_lendingdesk"."venue_ptr_id" IS NULL' not in desk_sql, desk_sql


@pytest.mark.django_db
def test_venue_reverse_relations_without_related_name_resolve_through_default_accessors():
    """``repairticket`` / ``venuebadge`` / ``venuesponsor`` read the default accessors.

    None of the three relations declares ``related_name``, so each is published
    under its query name while rows live behind ``repairticket_set``,
    ``venuebadge`` and ``venuesponsor_set``. The page is one venue statement
    and one prefetch per relation (each target's hook keeps the badge out of
    a join); the withdrawn ``VOID-`` ticket stays hidden and a venue with no
    badge answers ``null``.
    """
    annex = models.Venue.objects.create(name="Annex")
    depot = models.Venue.objects.create(name="Depot")
    models.RepairTicket.objects.create(code="T-1", venue=annex)
    models.RepairTicket.objects.create(code="T-2", venue=annex)
    models.RepairTicket.objects.create(code="VOID-3", venue=annex)
    models.RepairTicket.objects.create(code="T-4", venue=depot)
    models.VenueBadge.objects.create(code="STEP-FREE", venue=annex)
    acme = models.VenueSponsor.objects.create(name="Acme")
    acme.venues.add(annex, depot)
    models.VenueSponsor.objects.create(name="Globex").venues.add(annex)

    with CaptureQueriesContext(connection) as captured:
        data = assert_graphql_success(
            """
            query {
              allLibraryVenues {
                name
                repairticket { code }
                venuebadge { code }
                venuesponsor { name }
              }
            }
            """,
        )

    assert data["allLibraryVenues"] == [
        {
            "name": "Annex",
            "repairticket": [{"code": "T-1"}, {"code": "T-2"}],
            "venuebadge": {"code": "STEP-FREE"},
            "venuesponsor": [{"name": "Acme"}, {"name": "Globex"}],
        },
        {
            "name": "Depot",
            "repairticket": [{"code": "T-4"}],
            "venuebadge": None,
            "venuesponsor": [{"name": "Acme"}],
        },
    ], data
    assert len(captured.captured_queries) == 4, captured.captured_queries
    assert len(_sql_from_table(captured, "library_venue")) == 1, captured.captured_queries
    assert len(_sql_from_table(captured, "library_repairticket")) == 1, captured.captured_queries
    assert len(_sql_from_table(captured, "library_venuebadge")) == 1, captured.captured_queries
    assert len(_sql_from_table(captured, "library_venuesponsor")) == 1, captured.captured_queries


def _seed_withdrawn_badge_and_sponsor() -> None:
    """Two venues, each with a visible and a withdrawn row on the no-``related_name`` relations.

    ``Annex`` holds the visible ``STEP-FREE`` badge and ``Depot`` the withdrawn
    ``VOID-RAMP`` one; both venues are funded by the visible ``Acme`` and the
    withdrawn ``Withdrawn Initech``.
    """
    annex = models.Venue.objects.create(name="Annex")
    depot = models.Venue.objects.create(name="Depot")
    models.VenueBadge.objects.create(code="STEP-FREE", venue=annex)
    models.VenueBadge.objects.create(code="VOID-RAMP", venue=depot)
    models.VenueSponsor.objects.create(name="Acme").venues.add(annex, depot)
    models.VenueSponsor.objects.create(name="Withdrawn Initech").venues.add(annex, depot)


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("query", "visible", "expected"),
    [
        (
            "{ allLibraryVenues { name venuebadge { code } venuesponsor { name } } }",
            ("STEP-FREE", "Acme"),
            {
                "allLibraryVenues": [
                    {
                        "name": "Annex",
                        "venuebadge": {"code": "STEP-FREE"},
                        "venuesponsor": [{"name": "Acme"}],
                    },
                    {"name": "Depot", "venuebadge": None, "venuesponsor": [{"name": "Acme"}]},
                ],
            },
        ),
        (
            "{ allLibraryVenueBadges { code venue { name } } }",
            ("STEP-FREE",),
            {"allLibraryVenueBadges": [{"code": "STEP-FREE", "venue": {"name": "Annex"}}]},
        ),
        (
            "{ allLibraryVenueSponsors { name venues { name } } }",
            ("Acme",),
            {
                "allLibraryVenueSponsors": [
                    {"name": "Acme", "venues": [{"name": "Annex"}, {"name": "Depot"}]},
                ],
            },
        ),
    ],
    ids=["reverse-relations-from-venue", "badge-root", "sponsor-root"],
)
def test_withdrawn_badges_and_sponsors_are_absent_from_every_read_path(
    query: str,
    visible: tuple[str, ...],
    expected: dict[str, object],
):
    """A withdrawn badge or sponsor is absent from the wire, never an error.

    ``VenueBadgeType`` hides ``VOID-`` badges and ``VenueSponsorType`` hides
    ``Withdrawn`` sponsors. Through the reverse accessors a venue whose only
    badge is withdrawn answers ``null`` and the sponsor list drops the
    withdrawn sponsor; the roots drop both rows outright.
    """
    _seed_withdrawn_badge_and_sponsor()
    assert models.VenueBadge.objects.filter(code="VOID-RAMP", venue__name="Depot").exists()
    assert models.VenueSponsor.objects.filter(
        name="Withdrawn Initech",
        venues__name="Annex",
    ).exists()

    data = assert_graphql_success(query)

    assert all(marker in str(data) for marker in visible), data
    assert "VOID-RAMP" not in str(data), data
    assert "Withdrawn" not in str(data), data
    assert data == expected, data


@pytest.mark.django_db
def test_nullable_lead_ticket_cycle_cascades_one_way():
    """The nullable half of the ``Venue`` <-> ``RepairTicket`` cycle keeps unled venues.

    ``VenueType`` cascades over ``lead_ticket``: ``Shed``, whose lead ticket is
    withdrawn, is hidden; ``Depot``, which has no lead ticket, stays visible
    through the ``IS NULL`` disjunct a nullable edge adds. ``RepairTicketType``
    does not cascade back over ``venue``, so the request resolves instead of
    raising the cycle error, and ``leadTicket { venue }`` walks the cycle back
    to its own venue.
    """
    annex = models.Venue.objects.create(name="Annex")
    models.Venue.objects.create(name="Depot")
    shed = models.Venue.objects.create(name="Shed")
    annex.lead_ticket = models.RepairTicket.objects.create(code="T-1", venue=annex)
    annex.save()
    shed.lead_ticket = models.RepairTicket.objects.create(code="VOID-9", venue=shed)
    shed.save()

    with CaptureQueriesContext(connection) as captured:
        data = assert_graphql_success(
            "{ allLibraryVenues { name leadTicket { code venue { name } } } }",
        )

    # ``Venue`` declares no ordering, so the rows compare by name, never by storage order.
    assert sorted(data["allLibraryVenues"], key=lambda row: row["name"]) == [
        {"name": "Annex", "leadTicket": {"code": "T-1", "venue": {"name": "Annex"}}},
        {"name": "Depot", "leadTicket": None},
    ], data
    # The root venues, their lead tickets, and the tickets' venues: one statement each.
    assert len(captured.captured_queries) == 3, captured.captured_queries
    root_sql = captured.captured_queries[0]["sql"]
    assert _select_list(root_sql).endswith('"library_venue"."lead_ticket_id"'), root_sql
    assert '"library_venue"."lead_ticket_id" IS NULL' in root_sql, root_sql


@pytest.mark.django_db
def test_open_venues_are_the_proxy_default_manager_rows():
    """``allLibraryOpenVenues`` serves ``OpenVenue.objects``, which hides unopened venues.

    ``OpenVenueType`` declares no hook, so the only filter is the proxy's
    default manager; the same unopened row is served by ``allLibraryVenues``,
    whose seed is ``Venue``'s plain manager.
    """
    models.Venue.objects.create(name="Annex", opened_on=datetime.date(2020, 5, 1))
    models.Venue.objects.create(name="Planned Wing")

    open_venues = assert_graphql_success("{ allLibraryOpenVenues { name openedOn } }")
    all_venues = assert_graphql_success("{ allLibraryVenues { name } }")

    assert open_venues["allLibraryOpenVenues"] == [
        {"name": "Annex", "openedOn": "2020-05-01"},
    ], open_venues
    assert [row["name"] for row in all_venues["allLibraryVenues"]] == [
        "Annex",
        "Planned Wing",
    ], all_venues


@pytest.mark.django_db
def test_signage_on_a_city_less_branch_is_hidden_by_the_proxy_default_manager():
    """The cascade composes a proxy target from its default manager, not its base manager.

    ``BranchSignage.branch`` is declared to ``VisibleBranch``, whose default
    manager hides city-less branches, and ``VisibleBranchType`` declares no
    hook. The sign on the city-less branch is hidden over the wire although
    ``sign.branch`` still loads that branch through the forward descriptor's
    base manager.
    """
    main = models.Branch.objects.create(name="Main", city="Metro")
    outpost = models.Branch.objects.create(name="Outpost", city="")
    models.BranchSignage.objects.create(code="S-MAIN", branch_id=main.pk)
    hidden = models.BranchSignage.objects.create(code="S-OUTPOST", branch_id=outpost.pk)

    data = assert_graphql_success("{ allLibraryBranchSignage { code branch { name } } }")

    assert data["allLibraryBranchSignage"] == [
        {"code": "S-MAIN", "branch": {"name": "Main"}},
    ], data
    assert models.BranchSignage.objects.get(pk=hidden.pk).branch.name == "Outpost"
    assert not models.VisibleBranch.objects.filter(pk=outpost.pk).exists()


@pytest.mark.django_db
def test_circulation_desk_publishes_children_and_profile_under_a_scoped_cascade():
    """Every relation kind on one model; the explicit reverse names resolve.

    ``DeskShift.desk`` and ``DeskProfile.desk`` publish on the desk as
    ``children`` and ``profile``. The desk also carries a generic foreign key
    (set on ``Front``) and a generic relation, both outside ``Meta.fields``;
    ``CirculationDeskType`` cascades with ``fields=["branch", "shelf"]``, so the
    request is served instead of refused over the generic key, and the desk on
    the ``restricted`` branch is hidden from an anonymous viewer while a staff
    viewer sees it.
    """
    create_users(1)
    main = models.Branch.objects.create(name="Main", city="Metro")
    vault = models.Branch.objects.create(name="Vault", city="restricted")
    genre = models.Genre.objects.create(name="Reference")
    front = models.CirculationDesk.objects.create(
        name="Front",
        branch=main,
        shelf=models.Shelf.objects.create(code="A-1", branch=main),
        content_type=ContentType.objects.get_for_model(models.Genre),
        object_id=genre.pk,
    )
    front.genres.add(genre)
    models.CirculationDesk.objects.create(
        name="Vault Desk",
        branch=vault,
        shelf=models.Shelf.objects.create(code="V-1", branch=vault),
    )
    models.DeskShift.objects.create(name="Morning", desk=front)
    models.DeskShift.objects.create(name="Evening", desk=front)
    models.DeskProfile.objects.create(code="LATE-OPENING", desk=front)
    document = """
    query {
      allLibraryCirculationDesks {
        name
        branch { name }
        shelf { code }
        genres { name }
        children { name }
        profile { code }
      }
    }
    """

    anonymous = assert_graphql_success(document)
    staff_client = Client()
    staff_client.force_login(get_user_model().objects.get(username="staff_1"))
    staff = assert_graphql_success(document, client=staff_client)

    assert anonymous["allLibraryCirculationDesks"] == [
        {
            "name": "Front",
            "branch": {"name": "Main"},
            "shelf": {"code": "A-1"},
            "genres": [{"name": "Reference"}],
            "children": [{"name": "Morning"}, {"name": "Evening"}],
            "profile": {"code": "LATE-OPENING"},
        },
    ], anonymous
    assert [row["name"] for row in staff["allLibraryCirculationDesks"]] == [
        "Front",
        "Vault Desk",
    ], staff


def _seed_shelf_labels() -> None:
    """Four labels over two branches, one naming the ``secret`` shelf, inserted out of order.

    ``Central`` is created first, so its primary key sorts before ``Annex``'s
    although its name sorts after. Carrier order is ``(branch, shelf_code)``:
    ``central-a1``, ``central-c3``, ``annex-b2``, ``annex-s9``, which neither
    insertion order nor ``shelf_code`` alone reproduces.
    """
    central = models.Branch.objects.create(name="Central")
    annex = models.Branch.objects.create(name="Annex")
    for branch, code, topic in (
        (central, "A1", ""),
        (central, "C3", ""),
        (annex, "B2", ""),
        (annex, "S9", "secret"),
    ):
        models.Shelf.objects.create(branch=branch, code=code, topic=topic)
    for text, branch, code in (
        ("annex-b2", annex, "B2"),
        ("central-c3", central, "C3"),
        ("annex-s9", annex, "S9"),
        ("central-a1", central, "A1"),
    ):
        models.ShelfLabel.objects.create(text=text, branch=branch, shelf_code=code)


def _shelf_label_texts(
    direction: str,
    client: Client | None = None,
) -> tuple[list[str], list[str]]:
    """Return the label texts ordered by ``shelf`` in ``direction`` and the label statements."""
    with CaptureQueriesContext(connection) as captured:
        data = assert_graphql_success(
            f"{{ allLibraryShelfLabels(orderBy: [{{shelf: {direction}}}]) {{ text }} }}",
            client=client,
        )
    texts = [row["text"] for row in data["allLibraryShelfLabels"]]
    return texts, _sql_from_table(captured, "library_shelflabel")


#: Every ``Ordering`` member: the bare pair defers ``NULL`` placement to the
#: database, the four ``NULLS`` members fix it on every backend.
_DIRECTIONS = (
    "ASC",
    "ASC_NULLS_FIRST",
    "ASC_NULLS_LAST",
    "DESC",
    "DESC_NULLS_FIRST",
    "DESC_NULLS_LAST",
)


def _ordered_with_missing(direction: str, present: list[str], missing: str) -> list[str]:
    """``present`` (given ascending) in ``direction``, with the row ordering as ``NULL`` placed.

    A ``NULLS`` member places it where it says. A bare ``ASC`` / ``DESC`` leaves
    it to the database (``orders/inputs.py::Ordering``), which Django names
    ``nulls_order_largest``: PostgreSQL sorts ``NULL`` above every value, so
    last ascending and first descending, and SQLite below every value.
    """
    ascending = direction.startswith("ASC")
    if direction.endswith("NULLS_FIRST"):
        missing_first = True
    elif direction.endswith("NULLS_LAST"):
        missing_first = False
    else:
        missing_first = ascending != connection.features.nulls_order_largest
    ordered = present if ascending else present[::-1]
    return [missing, *ordered] if missing_first else [*ordered, missing]


def test_shelf_label_order_input_publishes_the_foreign_object_beside_its_carriers() -> None:
    """``"__all__"`` publishes the multi-column ``shelf`` relation as an order leaf.

    ``ShelfLabelOrder`` declares ``fields = "__all__"``. ``shelf`` has no column
    of its own (its value is the ``branch`` / ``shelf_code`` pair), and it is
    published after its carriers in model field order, like every other field.
    """
    fields = _introspect_input_fields("ShelfLabelOrderInputType")

    assert list(fields) == [
        "id",
        "text",
        "branch",
        "shelfCode",
        "shelf",
    ], fields
    assert fields["shelf"] == {"kind": "ENUM", "name": "Ordering", "ofType": None}, fields


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("direction", "expected"),
    [
        (
            "ASC",
            [
                "central-a1",
                "central-c3",
                "annex-b2",
                "annex-s9",
            ],
        ),
        (
            "DESC",
            [
                "annex-s9",
                "annex-b2",
                "central-c3",
                "central-a1",
            ],
        ),
    ],
    ids=["asc", "desc"],
)
def test_shelf_labels_order_by_shelf_sorts_by_both_carriers(
    direction: str,
    expected: list[str],
) -> None:
    """A ``shelf`` term orders by ``branch_id`` then ``shelf_code``, each in the term's direction.

    The relation is ordered the way Django's ``order_by("shelf")`` orders it:
    one key per carrier column in link order, never ``Shelf``'s own columns.
    The viewer is staff, so ``ShelfType`` hides no shelf and each carrier keeps
    its value; the page is one ``library_shelflabel`` statement.
    """
    create_users(1)
    _seed_shelf_labels()
    staff_client = Client()
    staff_client.force_login(get_user_model().objects.get(username="staff_1"))

    texts, label_sql = _shelf_label_texts(direction, staff_client)

    assert texts == expected, texts
    assert len(label_sql) == 1, label_sql
    order_clause = label_sql[0].split(" ORDER BY ", 1)[1]
    assert re.findall(
        r'"library_shelflabel"\."(branch_id|shelf_code)" ELSE NULL END (ASC|DESC)',
        order_clause,
    ) == [("branch_id", direction), ("shelf_code", direction)], order_clause


@pytest.mark.django_db
@pytest.mark.parametrize("direction", _DIRECTIONS)
def test_shelf_labels_order_a_hidden_shelf_as_a_missing_one(direction: str) -> None:
    """A label on a shelf ``ShelfType`` hides from the viewer sorts as one with no shelf.

    Anonymous viewers do not see the ``secret`` shelf, so both of
    ``annex-s9``'s carriers order as ``NULL``, where the direction places a
    ``NULL``. The label itself stays listed.
    """
    _seed_shelf_labels()

    texts, label_sql = _shelf_label_texts(direction)

    assert texts == _ordered_with_missing(
        direction,
        ["central-a1", "central-c3", "annex-b2"],
        "annex-s9",
    ), texts
    assert len(label_sql) == 1, label_sql


@pytest.mark.django_db
@pytest.mark.parametrize("direction", _DIRECTIONS)
def test_shelf_labels_keep_a_label_naming_no_shelf_and_sort_it_as_missing(direction: str) -> None:
    """A label whose ``(branch, shelf_code)`` matches no shelf stays listed and sorts as missing.

    No database constraint holds a ``ForeignObject``, so ``central-zz`` names a
    shelf that does not exist. ``ShelfType`` declares ``get_queryset``, so each
    carrier is read under a visibility test; the test correlates on the link's
    carrier / target columns, adds no join to ``library_shelf`` and so drops no
    label, and the label with no shelf reads ``NULL`` on both carriers, placed
    where the direction places a ``NULL``. The viewer is staff, so every
    existing shelf keeps its value.
    """
    create_users(1)
    _seed_shelf_labels()
    models.ShelfLabel.objects.create(
        text="central-zz",
        branch=models.Branch.objects.get(name="Central"),
        shelf_code="ZZ",
    )
    staff_client = Client()
    staff_client.force_login(get_user_model().objects.get(username="staff_1"))

    texts, label_sql = _shelf_label_texts(direction, staff_client)

    assert texts == _ordered_with_missing(
        direction,
        [
            "central-a1",
            "central-c3",
            "annex-b2",
            "annex-s9",
        ],
        "central-zz",
    ), texts
    assert len(label_sql) == 1, label_sql
    assert "JOIN" not in label_sql[0], label_sql[0]


@pytest.mark.django_db
@pytest.mark.parametrize("direction", _DIRECTIONS)
def test_branches_order_by_label_shelves_aggregate_each_carrier_behind_the_labels(
    direction: str,
) -> None:
    """``shelfLabels: { shelf: ... }`` orders branches by one aggregate per carrier, keeping every branch.

    ``BranchOrder.shelf_labels`` is a to-many hop, so the ``shelf`` term is
    ``Min`` / ``Max`` of each carrier (``branch_id``, then ``shelf_code``) over
    a branch's labels. ``ShelfType`` hides the ``secret`` shelf from this
    anonymous viewer, and each aggregate's visibility test correlates the
    shelf's ``(branch, code)`` to the label's own carriers through the label
    join, adding no join to ``library_shelf``: ``Vault``'s only label names a
    shelf that does not exist, so both its aggregates are ``NULL`` and it sorts
    where the direction places a ``NULL``, still listed. One statement serves
    the page.
    """
    _seed_shelf_labels()
    vault = models.Branch.objects.create(name="Vault")
    models.ShelfLabel.objects.create(text="vault-zz", branch=vault, shelf_code="ZZ")

    with CaptureQueriesContext(connection) as captured:
        data = assert_graphql_success(
            f"{{ allLibraryBranches(orderBy: [{{shelfLabels: {{shelf: {direction}}}}}]) "
            "{ name } }",
        )

    assert [row["name"] for row in data["allLibraryBranches"]] == _ordered_with_missing(
        direction,
        ["Central", "Annex"],
        "Vault",
    ), data
    assert len(captured.captured_queries) == 1, captured.captured_queries
    # Django 6 quotes the subquery alias (``"U0"``); 5.2 does not.
    branch_sql = captured.captured_queries[0]["sql"].replace('"U0"', "U0")
    correlation = (
        'U0."branch_id" = ("library_shelflabel"."branch_id") '
        'AND U0."code" = ("library_shelflabel"."shelf_code")'
    )
    assert branch_sql.count(correlation) == 2, branch_sql
    assert 'JOIN "library_shelf"' not in branch_sql, branch_sql


@pytest.mark.parametrize(
    "input_name",
    ["BookInput", "BookPartialInput"],
    ids=["create", "partial"],
)
def test_book_write_inputs_omit_the_non_editable_archive_genres(input_name: str) -> None:
    """``archiveGenres`` is absent from the generated ``Book`` input; ``genres`` is present.

    ``Book.archive_genres`` is a forward many-to-many declared
    ``editable=False``. The editable ``genres`` beside it is the control: a
    generator that stopped reading ``editable`` would publish both.
    """
    fields = _introspect_input_fields(input_name)

    assert "genres" in fields, fields
    assert "archiveGenres" not in fields, fields


@pytest.mark.parametrize("name", ["optionalAttachment", "spareImage"], ids=["blank", "null"])
def test_media_specimen_create_input_requiredness_reads_blank_and_null_separately(
    name: str,
) -> None:
    """Each optional file column is optional through its own arm of the requiredness rule.

    ``optionalAttachment`` is ``blank=True`` only and ``spareImage`` is
    ``null=True`` only, and each renders as a nullable ``Upload``; the required
    ``attachment`` control is pinned by
    ``test_uploads_api.py::test_media_specimen_input_exposes_upload_over_http``.
    """
    fields = _introspect_input_fields("MediaSpecimenInput")

    assert fields[name] == {"kind": "SCALAR", "name": "Upload", "ofType": None}, fields
