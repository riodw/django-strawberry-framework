"""Library model tests for string rendering, relation traversal, inheritance, and per-shelf title uniqueness.

Mirrors the products model tests so the library app carries its own coverage:
__str__ rendering, forward/reverse relation traversal, and a uniqueness rule.
"""

import datetime

import pytest
from django.db import IntegrityError, transaction

from apps.library.models import (
    Book,
    Branch,
    BranchNote,
    BranchSignage,
    CirculationDesk,
    DeskProfile,
    DeskShift,
    Genre,
    LendingDesk,
    Loan,
    MembershipCard,
    OpenVenue,
    Patron,
    ProxyBranch,
    RepairTicket,
    SelfServeDesk,
    Shelf,
    Venue,
    VenueBadge,
    VenueSponsor,
    VisibleBranch,
)


@pytest.mark.django_db
def test_str_representations_and_relations():
    branch = Branch.objects.create(name="Central", city="Metropolis")
    shelf = Shelf.objects.create(code="A-1", branch=branch, topic="scifi")
    genre = Genre.objects.create(name="Speculative")
    book = Book.objects.create(title="Kindred", shelf=shelf)
    book.genres.add(genre)
    patron = Patron.objects.create(name="Ada", email="ada@example.com")
    card = MembershipCard.objects.create(patron=patron, barcode="BC-001")
    loan = Loan.objects.create(book=book, patron=patron)

    assert str(branch) == "Central"
    assert str(shelf) == "A-1"
    assert str(genre) == "Speculative"
    assert str(book) == "Kindred"
    assert str(patron) == "Ada"
    assert str(card) == "BC-001"
    assert str(loan) == "Kindred to Ada"

    # Relations resolve in both directions.
    assert list(branch.shelves.all()) == [shelf]
    assert list(shelf.books.all()) == [book]
    assert list(book.genres.all()) == [genre]
    assert list(genre.books.all()) == [book]
    assert patron.card == card
    assert list(book.loans.all()) == [loan]
    assert list(patron.loans.all()) == [loan]


@pytest.mark.django_db
def test_book_title_unique_per_shelf():
    branch = Branch.objects.create(name="B1")
    shelf = Shelf.objects.create(code="X", branch=branch)
    Book.objects.create(title="Dune", shelf=shelf)
    with pytest.raises(IntegrityError), transaction.atomic():
        Book.objects.create(title="Dune", shelf=shelf)


@pytest.mark.django_db
def test_branch_note_str_and_proxy_targeted_relation():
    """``BranchNote.branch`` is declared to the ``ProxyBranch`` proxy, not ``Branch``.

    The forward side resolves to a proxy instance and the reverse ``notes``
    accessor hangs off the proxy, while the rows live in the concrete
    ``Branch`` table - the table identity the prefetch-child seal proves a
    relation by.
    """
    branch = ProxyBranch.objects.create(name="Proxy Central", city="Boston")
    note = BranchNote.objects.create(branch=branch, body="shelving audit")

    assert str(note) == "shelving audit"
    assert BranchNote._meta.get_field("branch").related_model is ProxyBranch
    assert note.branch == branch
    assert list(branch.notes.all()) == [note]
    # The proxy reads the concrete parent's table, so the same row is a Branch.
    assert Branch.objects.get(pk=branch.pk).name == "Proxy Central"


@pytest.mark.django_db
def test_venue_inheritance_chain_shares_the_venue_row():
    """Each ``Venue`` subclass level adds a table; the inherited columns stay on ``Venue``."""
    kiosk = SelfServeDesk.objects.create(
        name="Lobby Kiosk",
        opened_on=datetime.date(2022, 1, 1),
        window_count=1,
        kiosk_code="K-1",
    )

    assert str(kiosk) == "Lobby Kiosk"
    assert kiosk._meta.pk.name == "lendingdesk_ptr"
    assert LendingDesk._meta.pk.name == "venue_ptr"
    assert Venue.objects.get(pk=kiosk.pk).name == "Lobby Kiosk"
    assert LendingDesk.objects.get(pk=kiosk.pk).window_count == 1
    assert Venue.objects.get(pk=kiosk.pk).lendingdesk.selfservedesk == kiosk


@pytest.mark.django_db
def test_open_venue_manager_hides_unopened_venues():
    """The ``OpenVenue`` proxy's default manager keeps only venues with an opening date."""
    opened = Venue.objects.create(name="Annex", opened_on=datetime.date(2020, 1, 1))
    Venue.objects.create(name="Planned Wing")

    assert list(OpenVenue.objects.values_list("pk", flat=True)) == [opened.pk]
    assert Venue.objects.count() == 2
    assert OpenVenue._default_manager.model is OpenVenue


@pytest.mark.django_db
def test_venue_reverse_relations_use_default_accessors_and_close_a_nullable_cycle():
    """No ``related_name`` on the three reverse relations; ``lead_ticket`` points back."""
    venue = Venue.objects.create(name="Annex")
    ticket = RepairTicket.objects.create(code="T-1", venue=venue)
    badge = VenueBadge.objects.create(code="STEP-FREE", venue=venue)
    sponsor = VenueSponsor.objects.create(name="Acme")
    sponsor.venues.add(venue)
    venue.lead_ticket = ticket
    venue.save()

    assert (str(ticket), str(badge), str(sponsor)) == ("T-1", "STEP-FREE", "Acme")
    assert list(venue.repairticket_set.all()) == [ticket]
    assert venue.venuebadge == badge
    assert list(venue.venuesponsor_set.all()) == [sponsor]
    assert Venue.objects.get(pk=venue.pk).lead_ticket.venue == venue
    assert Venue._meta.get_field("repairticket").get_accessor_name() == "repairticket_set"
    assert Venue._meta.get_field("lead_ticket").null is True
    ticket.delete()
    assert Venue.objects.get(pk=venue.pk).lead_ticket is None


@pytest.mark.django_db
def test_visible_branch_manager_filters_while_the_forward_descriptor_does_not():
    """``BranchSignage.branch`` loads a city-less branch the proxy's manager hides."""
    branch = Branch.objects.create(name="Outpost", city="")
    sign = BranchSignage.objects.create(code="S-1", branch_id=branch.pk)

    assert str(sign) == "S-1"
    assert BranchSignage._meta.get_field("branch").related_model is VisibleBranch
    assert not VisibleBranch.objects.filter(pk=branch.pk).exists()
    assert BranchSignage.objects.get(pk=sign.pk).branch.name == "Outpost"


@pytest.mark.django_db
def test_circulation_desk_carries_every_relation_kind():
    """Forward FK / O2O / M2M, a generic key, a generic relation, and named reverses."""
    branch = Branch.objects.create(name="Main", city="Metro")
    shelf = Shelf.objects.create(code="A-1", branch=branch)
    genre = Genre.objects.create(name="Reference")
    desk = CirculationDesk.objects.create(name="Front", branch=branch, shelf=shelf)
    desk.genres.add(genre)
    desk.content_object = genre
    desk.save()
    shift = DeskShift.objects.create(name="Morning", desk=desk)
    profile = DeskProfile.objects.create(code="LATE-OPENING", desk=desk)
    tag = desk.tags.create(tag="accessible")

    assert (str(desk), str(shift), str(profile)) == ("Front", "Morning", "LATE-OPENING")
    assert CirculationDesk.objects.get(pk=desk.pk).content_object == genre
    assert list(desk.children.all()) == [shift]
    assert desk.profile == profile
    assert list(desk.genres.all()) == [genre]
    assert list(desk.tags.all()) == [tag]
    assert shelf.circulation_desk == desk
    assert list(branch.circulation_desks.all()) == [desk]


@pytest.mark.django_db
def test_book_archive_genres_is_not_editable():
    """``archive_genres`` is a forward M2M kept out of forms by ``editable=False``."""
    branch = Branch.objects.create(name="B1")
    book = Book.objects.create(title="Dune", shelf=Shelf.objects.create(code="X", branch=branch))
    genre = Genre.objects.create(name="Classic")
    book.archive_genres.add(genre)

    assert Book._meta.get_field("archive_genres").editable is False
    assert list(book.archive_genres.all()) == [genre]
    assert list(genre.books.all()) == []
