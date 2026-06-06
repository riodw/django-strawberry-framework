"""Signal-level invariants for the kanban board app.

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
    state: str = "planned",
    version: str = "alpha",
    milestone: models.Milestone | None = None,
) -> models.Card:
    """Build a card via factories, handling the done-requires-spec lifecycle."""
    target_version = kf.make_target_version(
        _VERSION_NUMBERS[version],
        milestone=kf.make_milestone(version),
    )
    common = {
        "number": number,
        "title": title,
        "target_version": target_version,
        "planning_state": kf.make_planning_state(state),
        "milestone": milestone or target_version.milestone,
    }
    if status == "done":
        card = kf.make_card(status=kf.make_status("todo"), **common)
        _spec_for(card)
        kf.make_card_glossary_term(card=card)
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
    card = _make_card(number=1, title="No spec")

    card.status = kf.make_status("done")

    with pytest.raises(ValidationError, match="linked spec doc"):
        card.save(update_fields=["status"])


@pytest.mark.django_db
def test_done_card_requires_glossary_link_on_save():
    card = _make_card(number=1, title="No glossary link")
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
# Dependency reference <-> M2M sync
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_card_reference_syncs_to_dependency_edge_and_back():
    target = _make_card(number=1, title="Target", status="done")
    source = _make_card(number=2, title="Source")

    reference = models.CardReference.objects.create(
        source_card=source,
        target_card=target,
        kind=kf.make_card_reference_kind("dependency"),
    )

    assert source.dependencies.filter(pk=target.pk).exists()

    reference.delete()

    assert not source.dependencies.filter(pk=target.pk).exists()


@pytest.mark.django_db
def test_direct_dependency_add_creates_normalized_reference():
    target = _make_card(number=1, title="Target", status="done")
    source = _make_card(number=2, title="Source")

    source.dependencies.add(target)

    reference = models.CardReference.objects.get(source_card=source, target_card=target)
    assert reference.kind.key == "dependency"


@pytest.mark.django_db
def test_related_card_reference_does_not_create_dependency_edge():
    source = _make_card(number=1, title="Source")
    target = _make_card(number=2, title="Target")

    models.CardReference.objects.create(
        source_card=source,
        target_card=target,
        kind=kf.make_card_reference_kind("related"),
    )

    assert not source.dependencies.filter(pk=target.pk).exists()


@pytest.mark.django_db
def test_dependency_cycle_is_rejected_from_dependency_edge():
    first = _make_card(number=1, title="First")
    second = _make_card(number=2, title="Second")

    second.dependencies.add(first)

    with pytest.raises(ValidationError):
        first.dependencies.add(second)


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
    assert dependent.dependencies.filter(pk=dependency.pk).exists()


# ---------------------------------------------------------------------------
# Dependency-ordering rule + board-number renumbering
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_dependency_edge_must_point_to_an_earlier_card():
    source = _make_card(number=1, title="Source")
    target = _make_card(number=2, title="Target")

    with pytest.raises(ValidationError, match="before dependent"):
        source.dependencies.add(target)


@pytest.mark.django_db
def test_dependent_card_cannot_move_before_dependency():
    dependency = _make_card(number=1, title="Dependency")
    dependent = _make_card(number=2, title="Dependent")
    dependent.dependencies.add(dependency)

    dependent.number = 1

    with pytest.raises(ValidationError, match="before dependent"):
        dependent.save(update_fields=["number"])


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
def test_card_move_rejects_number_gap():
    card = _make_card(number=1, title="First")
    _make_card(number=2, title="Second")

    card.number = 3

    with pytest.raises(ValidationError, match="between 1 and 2"):
        card.save(update_fields=["number"])
