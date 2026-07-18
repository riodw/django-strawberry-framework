"""Kanban signal tests for dependencies, done-card guards, blocking, and ordering.

A curated set covering the non-trivial signal logic: the dependency-reference
<-> ``dependencies`` M2M sync, the done-card spec/glossary guards, the
dependency-must-precede-dependent ordering rule, board-number renumbering, and
``is_blocked`` derivation. Data is built through the shared kanban factories;
the done-card lifecycle is encapsulated in ``_make_card``.
"""

import pytest
from django.core.exceptions import ValidationError
from django.db import transaction

from apps.kanban import factories as kf
from apps.kanban import models

_VERSION_NUMBERS = {"alpha": "0.0.1", "beta": "0.1.0"}


def _spec_for(card: models.Card) -> models.SpecDoc:
    return kf.make_spec_doc(card=card, name=f"spec-{card.number:03d}")


def _make_card(
    *,
    number: int,
    title: str,
    status: str = "todo",
    version: str = "alpha",
) -> models.Card:
    """Build a card via factories, handling the done-requires-spec lifecycle.

    A card's milestone is derived from its target version (no stored FK).
    """
    target_version = kf.make_target_version(
        _VERSION_NUMBERS[version],
        milestone=kf.make_milestone(version),
    )
    common = {"number": number, "title": title, "target_version": target_version}
    if status == "done":
        card = kf.make_card(status=kf.make_status("todo"), **common)
        _spec_for(card)
        kf.make_card_glossary_term(card=card)
        # The status state machine forbids todo -> done; bridge through wip.
        card.status = kf.make_status("wip")
        card.save(update_fields=["status"])
        card.status = kf.make_status("done")
        card.save(update_fields=["status"])
        card.refresh_from_db()
        return card
    return kf.make_card(status=kf.make_status(status), **common)


# ---------------------------------------------------------------------------
# Done-card guards
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_done_card_requires_spec_on_save():
    # ``wip`` so ``wip -> done`` is a legal transition and the done-content guard
    # (not the state-machine guard) is what fires.
    card = _make_card(number=1, title="No spec", status="wip")

    card.status = kf.make_status("done")

    with pytest.raises(ValidationError, match="linked spec doc"):
        card.save(update_fields=["status"])


@pytest.mark.django_db
def test_done_card_requires_glossary_link_on_save():
    card = _make_card(number=1, title="No glossary link", status="wip")
    _spec_for(card)

    card.status = kf.make_status("done")

    with pytest.raises(ValidationError, match="glossary link"):
        card.save(update_fields=["status"])


@pytest.mark.django_db
def test_done_card_last_glossary_link_cannot_be_deleted_or_moved():
    card = _make_card(number=1, title="Protected glossary", status="done")
    other_card = _make_card(number=2, title="Other card")
    link = card.glossary_links.get()

    # Each protected op touches the DB before its pre_save/pre_delete signal
    # raises, which marks the test transaction broken. Wrap each in atomic() so
    # the failure rolls back to a savepoint and the next assertion can still run.
    with pytest.raises(ValidationError, match="Cannot delete"), transaction.atomic():
        link.delete()

    link.card = other_card
    with pytest.raises(ValidationError, match="Cannot move"), transaction.atomic():
        link.save(update_fields=["card"])


@pytest.mark.django_db
def test_done_card_spec_cannot_be_deleted():
    card = _make_card(number=1, title="Protected spec", status="done")

    with pytest.raises(ValidationError, match="Cannot delete"):
        card.spec.delete()


# ---------------------------------------------------------------------------
# Dependency edges (CardReference is the single source of truth)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_dependency_reference_surfaces_as_dependency_card_and_back():
    target = _make_card(number=1, title="Target", status="done")
    source = _make_card(number=2, title="Source")

    reference = models.CardReference.objects.create(
        source_card=source,
        target_card=target,
        kind=kf.make_card_reference_kind("dependency"),
    )

    assert source.dependency_cards.filter(pk=target.pk).exists()

    reference.delete()

    assert not source.dependency_cards.filter(pk=target.pk).exists()


@pytest.mark.django_db
def test_add_dependency_service_creates_dependency_reference():
    from apps.kanban import services

    target = _make_card(number=1, title="Target", status="done")
    source = _make_card(number=2, title="Source")
    kf.make_card_reference_kind("dependency")

    services.add_dependency(source, target)

    reference = models.CardReference.objects.get(source_card=source, target_card=target)
    assert reference.kind.key == "dependency"
    assert source.dependency_cards.filter(pk=target.pk).exists()


@pytest.mark.django_db
def test_related_card_reference_is_not_a_dependency_edge():
    source = _make_card(number=1, title="Source")
    target = _make_card(number=2, title="Target")

    models.CardReference.objects.create(
        source_card=source,
        target_card=target,
        kind=kf.make_card_reference_kind("related"),
    )

    assert not source.dependency_cards.filter(pk=target.pk).exists()


@pytest.mark.django_db
def test_dependency_cycle_is_rejected_on_reference_save():
    first = _make_card(number=1, title="First")
    second = _make_card(number=2, title="Second")
    dependency_kind = kf.make_card_reference_kind("dependency")

    models.CardReference.objects.create(
        source_card=second,
        target_card=first,
        kind=dependency_kind,
    )

    with pytest.raises(ValidationError):
        models.CardReference.objects.create(
            source_card=first,
            target_card=second,
            kind=dependency_kind,
        )


@pytest.mark.django_db
def test_blocked_by_reference_kind_derives_blocked_state():
    dependency = _make_card(number=1, title="Dependency")
    dependent = _make_card(number=2, title="Dependent")

    models.CardReference.objects.create(
        source_card=dependent,
        target_card=dependency,
        kind=kf.make_card_reference_kind("blocked_by"),
    )

    dependent.refresh_from_db()
    assert dependent.is_blocked
    assert dependent.dependency_cards.filter(pk=dependency.pk).exists()


# ---------------------------------------------------------------------------
# Dependency-ordering rule + board-number renumbering
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_dependency_edge_must_point_to_an_earlier_card():
    source = _make_card(number=1, title="Source")
    target = _make_card(number=2, title="Target")

    with pytest.raises(ValidationError, match="before dependent"):
        models.CardReference.objects.create(
            source_card=source,
            target_card=target,
            kind=kf.make_card_reference_kind("dependency"),
        )


@pytest.mark.django_db
def test_direct_number_edit_on_existing_card_raises():
    """Moving an existing card via save() is rejected; the service is the writer."""
    card = _make_card(number=1, title="First")
    _make_card(number=2, title="Second")

    card.number = 2

    with pytest.raises(ValidationError, match="move_card_number"):
        card.save(update_fields=["number"])

    card.refresh_from_db()
    assert card.number == 1


@pytest.mark.django_db
def test_direct_number_edit_raises_on_full_save_too():
    """The guard fires on a full save() (no update_fields) as well."""
    card = _make_card(number=1, title="First")
    _make_card(number=2, title="Second")

    card.number = 2

    with pytest.raises(ValidationError, match="move_card_number"):
        card.save()


@pytest.mark.django_db
def test_card_insert_shifts_existing_numbers():
    first = _make_card(number=1, title="First")
    second = _make_card(number=2, title="Second")

    inserted = _make_card(number=1, title="Inserted")

    first.refresh_from_db()
    second.refresh_from_db()
    assert inserted.number == 1
    assert first.number == 2
    assert second.number == 3


@pytest.mark.django_db
def test_card_insert_rejects_number_gap():
    _make_card(number=1, title="First")
    _make_card(number=2, title="Second")

    with pytest.raises(ValidationError, match="between 1 and 3"):
        _make_card(number=4, title="Gap")


@pytest.mark.django_db
def test_sparse_source_card_numbers_can_be_materialized_directly():
    first = _make_card(number=21, title="Source row 21")
    second = _make_card(number=24, title="Source row 24")

    assert first.number == 21
    assert second.number == 24


@pytest.mark.django_db
def test_unchanged_number_save_is_allowed():
    """A save() that does not change the stored number passes the move guard."""
    card = _make_card(number=1, title="First")

    card.save(update_fields=["number"])

    card.refresh_from_db()
    assert card.number == 1


@pytest.mark.django_db
def test_card_delete_compacts_following_numbers():
    """The post_delete receiver delegates gap-compaction to the service."""
    first = _make_card(number=1, title="First")
    second = _make_card(number=2, title="Second")
    third = _make_card(number=3, title="Third")

    second.delete()

    first.refresh_from_db()
    third.refresh_from_db()
    assert first.number == 1
    assert third.number == 2


@pytest.mark.django_db
def test_card_delete_compacts_multiple_following_numbers():
    """Deleting a low card shifts every higher card down by one (multi-row gap)."""
    cards = [
        _make_card(number=index, title=f"Row {index}")
        for index in (
            1,
            2,
            3,
            4,
            5,
        )
    ]

    cards[1].delete()  # delete number 2

    remaining = list(models.Card.objects.order_by("number").values_list("title", "number"))
    assert remaining == [
        ("Row 1", 1),
        ("Row 3", 2),
        ("Row 4", 3),
        ("Row 5", 4),
    ]


# ---------------------------------------------------------------------------
# Reference edit paths: the raise-only guard fires on UPDATE, not only create
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_dependency_reference_retarget_to_valid_card_is_allowed():
    target_a = _make_card(number=1, title="Target A")
    target_b = _make_card(number=2, title="Target B")
    source = _make_card(number=3, title="Source")
    dependency_kind = kf.make_card_reference_kind("dependency")
    reference = models.CardReference.objects.create(
        source_card=source,
        target_card=target_a,
        kind=dependency_kind,
    )

    reference.target_card = target_b
    reference.save(update_fields=["target_card"])

    reference.refresh_from_db()
    assert reference.target_card == target_b
    assert source.dependency_cards.filter(pk=target_b.pk).exists()


@pytest.mark.django_db
def test_reference_kind_change_to_dependency_creating_cycle_is_rejected():
    first = _make_card(number=1, title="First")
    second = _make_card(number=2, title="Second")
    dependency_kind = kf.make_card_reference_kind("dependency")
    related_kind = kf.make_card_reference_kind("related")
    models.CardReference.objects.create(
        source_card=second,
        target_card=first,
        kind=dependency_kind,
    )
    # A harmless related edge in the opposite direction; retyping it to a
    # dependency would close a cycle (first -> second -> first).
    related = models.CardReference.objects.create(
        source_card=first,
        target_card=second,
        kind=related_kind,
    )

    related.kind = dependency_kind
    with pytest.raises(ValidationError):
        related.save(update_fields=["kind"])


@pytest.mark.django_db
def test_updating_dependency_reference_in_place_is_allowed():
    """The edge under edit is excluded from its own cycle search (exclude_reference_id)."""
    first = _make_card(number=1, title="First")
    second = _make_card(number=2, title="Second")
    reference = models.CardReference.objects.create(
        source_card=second,
        target_card=first,
        kind=kf.make_card_reference_kind("dependency"),
    )

    reference.raw_text = "edited note"
    reference.save(update_fields=["raw_text"])

    reference.refresh_from_db()
    assert reference.raw_text == "edited note"


# ---------------------------------------------------------------------------
# Done-card spec / glossary REASSIGN guards
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_done_card_spec_cannot_be_reassigned():
    done_card = _make_card(number=1, title="Shipped card", status="done")
    other_card = _make_card(number=2, title="Other card")
    spec = done_card.spec

    spec.card = other_card
    with pytest.raises(ValidationError, match="Cannot move a spec doc"):
        spec.save(update_fields=["card"])


@pytest.mark.django_db
def test_done_card_glossary_link_can_be_reassigned_when_another_remains():
    """Moving one glossary link off a done card is allowed while a second stays."""
    done_card = _make_card(number=1, title="Two-link card", status="done")
    other_card = _make_card(number=2, title="Recipient card")
    # ``_make_card(status="done")`` seeds exactly one glossary link; add a second
    # so the reassign leaves the done card with a surviving link (positive branch).
    kf.make_card_glossary_term(card=done_card)
    links = list(done_card.glossary_links.order_by("order"))
    assert len(links) == 2

    moved = links[0]
    moved.card = other_card
    moved.save(update_fields=["card"])

    moved.refresh_from_db()
    assert moved.card == other_card
    assert done_card.glossary_links.count() == 1


@pytest.mark.django_db
def test_changed_files_add_creates_cardpathlink_uuid_side_row():
    # A raw M2M .add() inserts the through row with bulk_create (no post_save),
    # so the UUID side-row is created by the m2m_changed post_add receiver.
    card = _make_card(number=1, title="Add-path card")
    path = models.TrackedPath.objects.create(
        path="django_strawberry_framework/types/base.py",
        state=models.TRACKED_PATH_CURRENT,
    )
    card.changed_files.add(path)

    link = models.CardPathLink.objects.get(card=card, path=path)
    assert link.uuid is not None
    assert link.uuid.id is not None
