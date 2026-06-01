"""Signal-level invariants for the kanban board app."""

import pytest
from django.core.exceptions import ValidationError

from apps.kanban import models


def _spec_for(card: models.Card) -> models.SpecDoc:
    return models.SpecDoc.objects.create(
        card=card,
        name=f"spec-{card.number:03d}",
        url=f"https://github.com/example/spec-{card.number:03d}.md",
    )


def _board_parts():
    statuses = {
        "done": models.Status.objects.create(key="done", label="Done"),
        "todo": models.Status.objects.create(key="todo", label="To Do"),
    }
    planning_states = {
        "planned": models.PlanningState.objects.create(key="planned", label="Planned"),
    }
    alpha = models.Milestone.objects.create(key="alpha", label="Alpha")
    beta = models.Milestone.objects.create(key="beta", label="Beta")
    return {
        "alpha": alpha,
        "beta": beta,
        "size": models.RelativeSize.objects.create(key="m", label="M"),
        "states": planning_states,
        "statuses": statuses,
        "version_alpha": models.TargetVersion.objects.create(number="0.0.1", milestone=alpha),
        "version_beta": models.TargetVersion.objects.create(number="0.1.0", milestone=beta),
    }


def _card(
    parts,
    *,
    number: int,
    title: str,
    status: str = "todo",
    state: str = "planned",
    version: str = "alpha",
    milestone: models.Milestone | None = None,
) -> models.Card:
    requested_status = parts["statuses"][status]
    create_status = parts["statuses"]["todo"] if status == "done" else requested_status
    card = models.Card.objects.create(
        title=title,
        number=number,
        status=create_status,
        milestone=milestone,
        target_version=parts[f"version_{version}"],
        relative_size=parts["size"],
        planning_state=parts["states"][state],
    )
    if status == "done":
        _spec_for(card)
        card.status = requested_status
        card.save(update_fields=["status"])
        card.refresh_from_db()
    return card


def _reference_kind() -> models.CardReferenceKind:
    return models.CardReferenceKind.objects.create(key="dependency", label="Dependency")


def _blocked_by_reference_kind() -> models.CardReferenceKind:
    return models.CardReferenceKind.objects.create(key="blocked_by", label="Blocked by")


def _related_reference_kind() -> models.CardReferenceKind:
    return models.CardReferenceKind.objects.create(key="related", label="Related")


def _reference_source() -> models.CardReferenceSource:
    return models.CardReferenceSource.objects.create(
        key="dependencies_section",
        label="Dependencies section",
    )


@pytest.mark.django_db
def test_card_milestone_follows_target_version():
    parts = _board_parts()
    card = _card(
        parts,
        number=1,
        title="Retargeted",
        version="beta",
        milestone=parts["alpha"],
    )

    card.refresh_from_db()
    assert card.milestone == parts["beta"]


@pytest.mark.django_db
def test_done_card_requires_spec_on_save():
    parts = _board_parts()
    card = _card(parts, number=1, title="No spec")

    card.status = parts["statuses"]["done"]

    with pytest.raises(ValidationError, match="linked spec doc"):
        card.save(update_fields=["status"])


@pytest.mark.django_db
def test_done_card_with_spec_can_save():
    parts = _board_parts()
    card = _card(parts, number=1, title="Has spec")
    _spec_for(card)

    card.status = parts["statuses"]["done"]
    card.save(update_fields=["status"])

    card.refresh_from_db()
    assert card.status.key == "done"
    assert card.spec.name == "spec-001"


@pytest.mark.django_db
def test_done_card_spec_cannot_be_deleted():
    parts = _board_parts()
    card = _card(parts, number=1, title="Protected spec", status="done")

    with pytest.raises(ValidationError, match="Cannot delete"):
        card.spec.delete()


@pytest.mark.django_db
def test_done_card_spec_cannot_be_moved_to_another_card():
    parts = _board_parts()
    done_card = _card(parts, number=1, title="Done card", status="done")
    other_card = _card(parts, number=2, title="Other card")
    spec = done_card.spec

    spec.card = other_card

    with pytest.raises(ValidationError, match="Cannot move"):
        spec.save(update_fields=["card"])


@pytest.mark.django_db
def test_card_reference_syncs_to_dependency_edge_and_back():
    parts = _board_parts()
    source = _card(parts, number=1, title="Source")
    target = _card(parts, number=2, title="Target", status="done")

    reference = models.CardReference.objects.create(
        source_card=source,
        target_card=target,
        kind=_reference_kind(),
        source=_reference_source(),
    )

    assert source.dependencies.filter(pk=target.pk).exists()

    reference.delete()

    assert not source.dependencies.filter(pk=target.pk).exists()


@pytest.mark.django_db
def test_direct_dependency_add_creates_normalized_reference():
    parts = _board_parts()
    source = _card(parts, number=1, title="Source")
    target = _card(parts, number=2, title="Target", status="done")

    source.dependencies.add(target)

    reference = models.CardReference.objects.get(source_card=source, target_card=target)
    assert reference.kind.key == "dependency"
    assert reference.source.key == "dependencies_section"


@pytest.mark.django_db
def test_related_card_reference_does_not_create_dependency_edge():
    parts = _board_parts()
    source = _card(parts, number=1, title="Source")
    target = _card(parts, number=2, title="Target")

    models.CardReference.objects.create(
        source_card=source,
        target_card=target,
        kind=_related_reference_kind(),
        source=_reference_source(),
    )

    assert not source.dependencies.filter(pk=target.pk).exists()


@pytest.mark.django_db
def test_dependency_cycle_is_rejected_from_dependency_edge():
    parts = _board_parts()
    first = _card(parts, number=1, title="First")
    second = _card(parts, number=2, title="Second")

    first.dependencies.add(second)

    with pytest.raises(ValidationError):
        second.dependencies.add(first)


@pytest.mark.django_db
def test_self_dependency_is_rejected_from_card_reference():
    parts = _board_parts()
    card = _card(parts, number=1, title="Self")

    with pytest.raises(ValidationError):
        models.CardReference.objects.create(
            source_card=card,
            target_card=card,
            kind=_reference_kind(),
            source=_reference_source(),
        )


@pytest.mark.django_db
def test_dependency_reference_does_not_store_or_derive_blocked_badge():
    parts = _board_parts()
    dependency = _card(parts, number=1, title="Dependency")
    dependent = _card(parts, number=2, title="Dependent")

    dependent.dependencies.add(dependency)

    dependent.refresh_from_db()
    assert dependent.status.key == "todo"
    assert dependent.planning_state.key == "planned"
    assert not dependent.is_blocked
    assert not dependent.labels.filter(key="blocked").exists()
    assert not models.Label.objects.filter(key="blocked").exists()

    _spec_for(dependency)
    dependency.status = parts["statuses"]["done"]
    dependency.save(update_fields=["status"])

    dependent.refresh_from_db()
    assert dependent.status.key == "todo"
    assert dependent.planning_state.key == "planned"
    assert not dependent.is_blocked
    assert not dependent.labels.filter(key="blocked").exists()


@pytest.mark.django_db
def test_blocked_by_reference_kind_derives_blocked_state():
    parts = _board_parts()
    dependency = _card(parts, number=1, title="Dependency")
    dependent = _card(parts, number=2, title="Dependent")

    models.CardReference.objects.create(
        source_card=dependent,
        target_card=dependency,
        kind=_blocked_by_reference_kind(),
        source=_reference_source(),
    )

    dependent.refresh_from_db()
    assert dependent.is_blocked
    assert dependent.dependencies.filter(pk=dependency.pk).exists()
