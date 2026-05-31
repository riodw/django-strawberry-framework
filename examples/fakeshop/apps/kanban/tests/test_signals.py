"""Signal-level invariants for the kanban board app."""

import pytest
from django.core.exceptions import ValidationError

from apps.kanban import models


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
    return models.Card.objects.create(
        title=title,
        number=number,
        status=parts["statuses"][status],
        milestone=milestone,
        target_version=parts[f"version_{version}"],
        relative_size=parts["size"],
        planning_state=parts["states"][state],
    )


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
