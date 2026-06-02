"""Model-level invariants for the kanban app (not reachable from a live query).

Covers the ``UUIDModel`` one-hot check constraint (docs/feedback.md M1): exactly
one of its O2O link fields must be non-null.
"""

import uuid as uuid_module

import pytest
from django.db import IntegrityError, transaction

from apps.glossary import models as glossary_models
from apps.kanban import models


def _card_required_parts():
    """Create the required FK rows for card invariant tests."""
    status = models.Status.objects.create(key="todo", label="To Do")
    alpha = models.Milestone.objects.create(key="alpha", label="Alpha")
    version = models.TargetVersion.objects.create(number="0.0.1", milestone=alpha)
    size = models.RelativeSize.objects.create(key="m", label="M")
    state = models.PlanningState.objects.create(key="planned", label="Planned")
    return {
        "status": status,
        "target_version": version,
        "relative_size": size,
        "planning_state": state,
    }


def _glossary_term(anchor: str):
    status, _created = glossary_models.GlossaryStatus.objects.get_or_create(
        key="shipped",
        defaults={"label": "Shipped"},
    )
    return glossary_models.GlossaryTerm.objects.create(
        title=f"`{anchor}`",
        title_sort=anchor,
        anchor=anchor,
        status=status,
        status_text="shipped (`0.0.8`)",
    )


@pytest.mark.django_db
def test_uuidmodel_accepts_exactly_one_link():
    """The normal path: creating a linked model yields a valid one-hot UUID row."""
    status = models.Status.objects.create(key="z", label="Z")
    row = status.uuid
    assert isinstance(row.id, uuid_module.UUID)
    set_links = [name for name in models._UUID_LINK_NAMES if getattr(row, f"{name}_id") is not None]
    assert set_links == ["status"]


@pytest.mark.django_db
def test_uuidmodel_rejects_zero_links():
    """A registry row with no link violates the one-hot constraint."""
    with pytest.raises(IntegrityError), transaction.atomic():
        models.UUIDModel.objects.create()


@pytest.mark.django_db
def test_uuidmodel_rejects_multiple_links():
    """A registry row linked to two domain rows violates the one-hot constraint."""
    status = models.Status.objects.create(key="x", label="X")
    label = models.Label.objects.create(key="y")
    # Free the O2O slots the signal auto-filled so the failure below is the
    # one-hot check (two non-null links), not O2O uniqueness.
    models.UUIDModel.objects.filter(status=status).delete()
    models.UUIDModel.objects.filter(label=label).delete()
    with pytest.raises(IntegrityError), transaction.atomic():
        models.UUIDModel.objects.create(status=status, label=label)


@pytest.mark.django_db
def test_target_version_number_is_required():
    """A target version cannot be stored without the actual X.Y.Z value."""
    alpha = models.Milestone.objects.create(key="alpha", label="Alpha")

    with pytest.raises(IntegrityError), transaction.atomic():
        models.TargetVersion.objects.create(number="", milestone=alpha)


@pytest.mark.django_db
def test_card_target_version_is_required():
    """A card cannot be stored without its planned or shipped version."""
    status = models.Status.objects.create(key="todo", label="To Do")
    size = models.RelativeSize.objects.create(key="m", label="M")
    state = models.PlanningState.objects.create(key="planned", label="Planned")

    with pytest.raises(IntegrityError), transaction.atomic():
        models.Card.objects.create(
            title="No version",
            number=1,
            status=status,
            relative_size=size,
            planning_state=state,
        )


@pytest.mark.django_db
def test_card_number_is_required():
    """A card cannot be stored without its board sequence number."""
    required_parts = _card_required_parts()

    with pytest.raises(IntegrityError), transaction.atomic():
        models.Card.objects.create(
            title="No number",
            **required_parts,
        )


@pytest.mark.django_db
def test_card_number_must_be_positive():
    """A card sequence number starts at one, not zero."""
    required_parts = _card_required_parts()

    with pytest.raises(IntegrityError), transaction.atomic():
        models.Card.objects.create(
            title="Zero number",
            number=0,
            **required_parts,
        )


@pytest.mark.django_db
def test_card_milestone_is_required():
    """The derived milestone is still a required stored FK."""
    required_parts = _card_required_parts()

    with pytest.raises(IntegrityError), transaction.atomic():
        models.Card.objects.bulk_create(
            [
                models.Card(
                    title="No milestone",
                    number=1,
                    **required_parts,
                ),
            ],
        )


@pytest.mark.django_db
def test_card_number_is_globally_unique():
    """The NNN sequence cannot be reused across statuses or target versions."""
    todo = models.Status.objects.create(key="todo", label="To Do")
    wip = models.Status.objects.create(key="wip", label="In Progress")
    alpha = models.Milestone.objects.create(key="alpha", label="Alpha")
    version_1 = models.TargetVersion.objects.create(number="0.0.1", milestone=alpha)
    version_2 = models.TargetVersion.objects.create(number="0.0.2", milestone=alpha)
    size = models.RelativeSize.objects.create(key="m", label="M")
    state = models.PlanningState.objects.create(key="planned", label="Planned")

    models.Card.objects.create(
        title="First",
        number=1,
        status=todo,
        target_version=version_1,
        relative_size=size,
        planning_state=state,
    )

    with pytest.raises(IntegrityError), transaction.atomic():
        models.Card.objects.create(
            title="Second",
            number=1,
            status=wip,
            target_version=version_2,
            relative_size=size,
            planning_state=state,
        )


@pytest.mark.django_db
def test_spec_doc_card_is_required():
    """A spec doc cannot be stored without the card it belongs to."""
    with pytest.raises(IntegrityError), transaction.atomic():
        models.SpecDoc.objects.bulk_create(
            [
                models.SpecDoc(
                    name="orphan",
                    url="https://github.com/example/orphan.md",
                ),
            ],
        )


@pytest.mark.django_db
def test_board_doc_card_reference_is_fk_backed_and_ordered_per_doc():
    """Board prose card mentions point at cards instead of storing live card ids."""
    kind = models.BoardDocKind.objects.create(key="reference", label="Reference")
    doc = models.BoardDoc.objects.create(key="snapshot", kind=kind, title="Snapshot")
    status = models.Status.objects.create(key="todo", label="To Do")
    alpha = models.Milestone.objects.create(key="alpha", label="Alpha")
    version = models.TargetVersion.objects.create(number="0.0.1", milestone=alpha)
    size = models.RelativeSize.objects.create(key="m", label="M")
    state = models.PlanningState.objects.create(key="shipped", label="Shipped")
    card = models.Card.objects.create(
        title="Stored card",
        number=1,
        status=status,
        target_version=version,
        relative_size=size,
        planning_state=state,
    )

    reference = models.BoardDocCardReference.objects.create(
        doc=doc,
        card=card,
        raw_text="DONE-001-0.0.1",
        order=0,
    )

    assert reference.uuid.boarddoccardreference == reference
    with pytest.raises(IntegrityError), transaction.atomic():
        models.BoardDocCardReference.objects.create(
            doc=doc,
            card=card,
            raw_text="DONE-001-0.0.1",
            order=0,
        )


@pytest.mark.django_db
def test_card_glossary_terms_are_fk_backed_and_ordered_per_card():
    """Kanban cards link to canonical glossary terms with stable UUID rows."""
    card = models.Card.objects.create(
        title="Glossary linked card",
        number=1,
        **_card_required_parts(),
    )
    filterset = _glossary_term("filterset")
    orderset = _glossary_term("orderset")

    link = models.CardGlossaryTerm.objects.create(
        card=card,
        term=filterset,
        raw_text="FilterSet",
        order=0,
    )

    assert link.uuid.cardglossaryterm == link
    with pytest.raises(IntegrityError), transaction.atomic():
        models.CardGlossaryTerm.objects.create(
            card=card,
            term=filterset,
            raw_text="FilterSet duplicate",
            order=1,
        )
    with pytest.raises(IntegrityError), transaction.atomic():
        models.CardGlossaryTerm.objects.create(
            card=card,
            term=orderset,
            raw_text="OrderSet",
            order=0,
        )
