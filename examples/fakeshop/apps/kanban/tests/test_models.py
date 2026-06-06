"""Model-level invariants for the kanban app (not reachable from a live query).

Covers the ``UUIDModel`` one-hot check constraint (docs/feedback.md M1): exactly
one of its O2O link fields must be non-null, plus the card / spec / reference
required-field and uniqueness constraints.

Valid FK rows are built through the shared factories so these tests survive
lookup-table changes; the deliberately-broken rows (missing/zero fields) stay as
raw ``Model.objects.create`` calls because that is exactly what they assert.
"""

import uuid as uuid_module

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from apps.glossary import factories as gf
from apps.kanban import factories as kf
from apps.kanban import models


def _card_required_parts():
    """The required FK rows for a Card, built via factories."""
    return {
        "status": kf.make_status(),
        "target_version": kf.make_target_version(),
        "relative_size": kf.make_relative_size(),
        "planning_state": kf.make_planning_state(),
    }


@pytest.mark.django_db
def test_uuidmodel_accepts_exactly_one_link():
    """The normal path: creating a linked model yields a valid one-hot UUID row."""
    status = kf.make_status("z")
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
    status = kf.make_status("x")
    label = kf.make_label("y")
    # Free the O2O slots the signal auto-filled so the failure below is the
    # one-hot check (two non-null links), not O2O uniqueness.
    models.UUIDModel.objects.filter(status=status).delete()
    models.UUIDModel.objects.filter(label=label).delete()
    with pytest.raises(IntegrityError), transaction.atomic():
        models.UUIDModel.objects.create(status=status, label=label)


@pytest.mark.django_db
def test_target_version_number_is_required():
    """A target version cannot be stored without the actual X.Y.Z value."""
    alpha = kf.make_milestone("alpha")

    with pytest.raises(IntegrityError), transaction.atomic():
        models.TargetVersion.objects.create(number="", milestone=alpha)


@pytest.mark.django_db
def test_card_target_version_is_required():
    """A card cannot be stored without its planned or shipped version."""
    with pytest.raises(IntegrityError), transaction.atomic():
        models.Card.objects.create(
            title="No version",
            number=1,
            status=kf.make_status(),
            relative_size=kf.make_relative_size(),
            planning_state=kf.make_planning_state(),
        )


@pytest.mark.django_db
def test_card_number_is_required():
    """A card cannot be stored without its board sequence number."""
    with pytest.raises(ValidationError, match="require"), transaction.atomic():
        models.Card.objects.create(title="No number", **_card_required_parts())


@pytest.mark.django_db
def test_card_number_must_be_positive():
    """A card sequence number starts at one, not zero."""
    with pytest.raises(ValidationError, match="at least 1"), transaction.atomic():
        models.Card.objects.create(title="Zero number", number=0, **_card_required_parts())


@pytest.mark.django_db
def test_card_milestone_is_required():
    """The derived milestone is still a required stored FK."""
    # bulk_create bypasses the pre_save signal that would derive the milestone.
    with pytest.raises(IntegrityError), transaction.atomic():
        models.Card.objects.bulk_create(
            [models.Card(title="No milestone", number=1, **_card_required_parts())],
        )


@pytest.mark.django_db
def test_card_number_is_globally_unique():
    """The stored NNN sequence still has a DB backstop for signal-bypassing writes."""
    parts = _card_required_parts()
    parts["milestone"] = parts["target_version"].milestone

    with pytest.raises(IntegrityError), transaction.atomic():
        models.Card.objects.bulk_create(
            [
                models.Card(title="Duplicate one", number=1, **parts),
                models.Card(title="Duplicate two", number=1, **parts),
            ],
        )


@pytest.mark.django_db
def test_spec_doc_card_is_required():
    """A spec doc cannot be stored without the card it belongs to."""
    with pytest.raises(IntegrityError), transaction.atomic():
        models.SpecDoc.objects.bulk_create(
            [models.SpecDoc(name="orphan", url="https://github.com/example/orphan.md")],
        )


@pytest.mark.django_db
def test_board_doc_card_reference_is_fk_backed_and_ordered_per_doc():
    """Board prose card mentions point at cards instead of storing live card ids."""
    doc = kf.make_board_doc(
        kind=kf.make_board_doc_kind("reference"),
        key="snapshot",
        title="Snapshot",
    )
    card = kf.make_card()

    reference = kf.make_board_doc_card_reference(
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
    card = kf.make_card()
    filterset = gf.make_glossary_term(
        title="`filterset`",
        title_sort="filterset",
        anchor="filterset",
    )
    orderset = gf.make_glossary_term(title="`orderset`", title_sort="orderset", anchor="orderset")

    link = kf.make_card_glossary_term(card=card, term=filterset, raw_text="FilterSet", order=0)

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
