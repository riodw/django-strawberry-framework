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
  through Django's default accessors, each batched once.
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
- Write-input requiredness: ``Book.archive_genres`` (``editable=False``) is
  absent from both generated ``Book`` inputs, and ``MediaSpecimen``'s optional
  file columns are optional through the ``blank`` arm and the ``null`` arm
  separately.
"""

import datetime

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


def _introspect_input_fields(type_name: str) -> dict[str, dict]:
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
    (the badge joined into it), one ticket prefetch and one sponsor prefetch;
    the withdrawn ``VOID-`` ticket stays hidden and a venue with no badge
    answers ``null``.
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
    assert len(captured.captured_queries) == 3, captured.captured_queries
    assert len(_sql_from_table(captured, "library_venue")) == 1, captured.captured_queries
    assert len(_sql_from_table(captured, "library_repairticket")) == 1, captured.captured_queries
    assert len(_sql_from_table(captured, "library_venuesponsor")) == 1, captured.captured_queries


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

    assert data["allLibraryVenues"] == [
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


@pytest.mark.parametrize(
    "input_name",
    ["BookInput", "BookPartialInput"],
    ids=["create", "partial"],
)
def test_book_write_inputs_omit_the_non_editable_archive_genres(input_name):
    """``archiveGenres`` is absent from the generated ``Book`` input; ``genres`` is present.

    ``Book.archive_genres`` is a forward many-to-many declared
    ``editable=False``. The editable ``genres`` beside it is the control: a
    generator that stopped reading ``editable`` would publish both.
    """
    fields = _introspect_input_fields(input_name)

    assert "genres" in fields, fields
    assert "archiveGenres" not in fields, fields


@pytest.mark.parametrize("name", ["optionalAttachment", "spareImage"], ids=["blank", "null"])
def test_media_specimen_create_input_requiredness_reads_blank_and_null_separately(name):
    """Each optional file column is optional through its own arm of the requiredness rule.

    ``optionalAttachment`` is ``blank=True`` only and ``spareImage`` is
    ``null=True`` only, and each renders as a nullable ``Upload``; the required
    ``attachment`` control is pinned by
    ``test_uploads_api.py::test_media_specimen_input_exposes_upload_over_http``.
    """
    fields = _introspect_input_fields("MediaSpecimenInput")

    assert fields[name] == {"kind": "SCALAR", "name": "Upload", "ofType": None}, fields
