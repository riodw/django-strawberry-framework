"""Signal-level invariants for the kanban board app.

Data is built through the shared kanban factories; the done-card lifecycle
(create-as-todo, attach spec and glossary link, flip to done) is encapsulated in
``_make_card`` so each test reads as a behavior assertion rather than setup
boilerplate.
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


@pytest.mark.django_db
def test_card_milestone_follows_target_version():
    card = _make_card(
        number=1,
        title="Retargeted",
        version="beta",
        milestone=kf.make_milestone("alpha"),
    )

    card.refresh_from_db()
    assert card.milestone == kf.make_milestone("beta")


@pytest.mark.django_db
def test_done_card_requires_spec_on_save():
    card = _make_card(number=1, title="No spec")

    card.status = kf.make_status("done")

    with pytest.raises(ValidationError, match="linked spec doc"):
        card.save(update_fields=["status"])


@pytest.mark.django_db
def test_done_card_with_spec_can_save():
    card = _make_card(number=1, title="Has spec")
    _spec_for(card)
    kf.make_card_glossary_term(card=card)

    card.status = kf.make_status("done")
    card.save(update_fields=["status"])

    card.refresh_from_db()
    assert card.status.key == "done"
    assert card.spec.name == "spec-001"
    assert card.glossary_links.exists()


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


@pytest.mark.django_db
def test_done_card_spec_cannot_be_moved_to_another_card():
    done_card = _make_card(number=1, title="Done card", status="done")
    other_card = _make_card(number=2, title="Other card")
    spec = done_card.spec

    spec.card = other_card

    with pytest.raises(ValidationError, match="Cannot move"):
        spec.save(update_fields=["card"])


@pytest.mark.django_db
def test_card_reference_syncs_to_dependency_edge_and_back():
    target = _make_card(number=1, title="Target", status="done")
    source = _make_card(number=2, title="Source")

    reference = models.CardReference.objects.create(
        source_card=source,
        target_card=target,
        kind=kf.make_card_reference_kind("dependency"),
        source=kf.make_card_reference_source("dependencies_section"),
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
    assert reference.source.key == "dependencies_section"


@pytest.mark.django_db
def test_related_card_reference_does_not_create_dependency_edge():
    source = _make_card(number=1, title="Source")
    target = _make_card(number=2, title="Target")

    models.CardReference.objects.create(
        source_card=source,
        target_card=target,
        kind=kf.make_card_reference_kind("related"),
        source=kf.make_card_reference_source("dependencies_section"),
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
def test_card_move_up_shifts_intervening_numbers():
    first = _make_card(number=1, title="First")
    second = _make_card(number=2, title="Second")
    third = _make_card(number=3, title="Third")

    third.number = 1
    third.save(update_fields=["number"])

    first.refresh_from_db()
    second.refresh_from_db()
    third.refresh_from_db()
    assert third.number == 1
    assert first.number == 2
    assert second.number == 3


@pytest.mark.django_db
def test_card_move_down_shifts_intervening_numbers():
    first = _make_card(number=1, title="First")
    second = _make_card(number=2, title="Second")
    third = _make_card(number=3, title="Third")

    first.number = 3
    first.save(update_fields=["number"])

    first.refresh_from_db()
    second.refresh_from_db()
    third.refresh_from_db()
    assert second.number == 1
    assert third.number == 2
    assert first.number == 3


@pytest.mark.django_db
def test_card_delete_compacts_following_numbers():
    first = _make_card(number=1, title="First")
    second = _make_card(number=2, title="Second")
    third = _make_card(number=3, title="Third")

    second.delete()

    first.refresh_from_db()
    third.refresh_from_db()
    assert first.number == 1
    assert third.number == 2


@pytest.mark.django_db
def test_card_create_allows_sparse_explicit_number():
    first = _make_card(number=1, title="First")

    sparse = _make_card(number=3, title="Sparse")

    first.refresh_from_db()
    assert first.number == 1
    assert sparse.number == 3


@pytest.mark.django_db
def test_card_move_past_end_shifts_following_numbers():
    first = _make_card(number=1, title="First")
    second = _make_card(number=2, title="Second")
    third = _make_card(number=3, title="Third")

    first.number = 99
    first.save(update_fields=["number"])

    first.refresh_from_db()
    second.refresh_from_db()
    third.refresh_from_db()
    assert second.number == 1
    assert third.number == 2
    assert first.number == 99


@pytest.mark.django_db
def test_dependency_edge_must_point_to_an_earlier_card():
    source = _make_card(number=1, title="Source")
    target = _make_card(number=2, title="Target")

    with pytest.raises(ValidationError, match="before dependent"):
        source.dependencies.add(target)


@pytest.mark.django_db
def test_dependency_reference_must_point_to_an_earlier_card():
    source = _make_card(number=1, title="Source")
    target = _make_card(number=2, title="Target")

    with pytest.raises(ValidationError, match="before dependent"):
        models.CardReference.objects.create(
            source_card=source,
            target_card=target,
            kind=kf.make_card_reference_kind("dependency"),
            source=kf.make_card_reference_source("dependencies_section"),
        )


@pytest.mark.django_db
def test_dependent_card_cannot_move_before_dependency():
    dependency = _make_card(number=1, title="Dependency")
    dependent = _make_card(number=2, title="Dependent")
    dependent.dependencies.add(dependency)

    dependent.number = 1

    with pytest.raises(ValidationError, match="before dependent"):
        dependent.save(update_fields=["number"])


@pytest.mark.django_db
def test_dependency_card_cannot_move_after_dependent():
    dependency = _make_card(number=1, title="Dependency")
    dependent = _make_card(number=2, title="Dependent")
    dependent.dependencies.add(dependency)

    dependency.number = 2

    with pytest.raises(ValidationError, match="before dependent"):
        dependency.save(update_fields=["number"])


@pytest.mark.django_db
def test_self_dependency_is_rejected_from_card_reference():
    card = _make_card(number=1, title="Self")

    with pytest.raises(ValidationError):
        models.CardReference.objects.create(
            source_card=card,
            target_card=card,
            kind=kf.make_card_reference_kind("dependency"),
            source=kf.make_card_reference_source("dependencies_section"),
        )


@pytest.mark.django_db
def test_dependency_reference_does_not_store_or_derive_blocked_badge():
    dependency = _make_card(number=1, title="Dependency")
    dependent = _make_card(number=2, title="Dependent")

    dependent.dependencies.add(dependency)

    dependent.refresh_from_db()
    assert dependent.status.key == "todo"
    assert dependent.planning_state.key == "planned"
    assert not dependent.is_blocked
    assert not dependent.labels.filter(key="blocked").exists()
    assert not models.Label.objects.filter(key="blocked").exists()

    _spec_for(dependency)
    kf.make_card_glossary_term(card=dependency)
    dependency.status = kf.make_status("done")
    dependency.save(update_fields=["status"])

    dependent.refresh_from_db()
    assert dependent.status.key == "todo"
    assert dependent.planning_state.key == "planned"
    assert not dependent.is_blocked
    assert not dependent.labels.filter(key="blocked").exists()


@pytest.mark.django_db
def test_blocked_by_reference_kind_derives_blocked_state():
    dependency = _make_card(number=1, title="Dependency")
    dependent = _make_card(number=2, title="Dependent")

    models.CardReference.objects.create(
        source_card=dependent,
        target_card=dependency,
        kind=kf.make_card_reference_kind("blocked_by"),
        source=kf.make_card_reference_source("dependencies_section"),
    )

    dependent.refresh_from_db()
    assert dependent.is_blocked
    assert dependent.dependencies.filter(pk=dependency.pk).exists()
