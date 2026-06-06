"""Service-level workflows for the kanban app."""

import pytest
from django.core.exceptions import ValidationError
from django.db import transaction

from apps.kanban import factories as kf
from apps.kanban import models, services


@pytest.fixture(autouse=True)
def _dependency_note_lookups(db):
    kf.make_card_reference_kind("dependency")
    kf.make_card_reference_source("dependencies_section")
    kf.make_section("dependencies_note")


@pytest.mark.django_db
def test_append_card_item_uses_next_section_order():
    card = kf.make_card(title="Card")
    section = kf.make_section("scope")

    first = services.append_card_item(card, section, "first")
    second = services.append_card_item(card, section, "second")

    assert first.order == 0
    assert second.order == 1
    assert list(card.items.filter(section=section).values_list("text", flat=True)) == [
        "first",
        "second",
    ]


@pytest.mark.django_db
def test_append_card_reference_uses_next_source_order():
    source_card = kf.make_card(number=1, title="Source")
    first_target = kf.make_card(number=2, title="First target")
    second_target = kf.make_card(number=3, title="Second target")
    kind = kf.make_card_reference_kind("related")
    source = kf.make_card_reference_source("planning_note")

    first = services.append_card_reference(
        source_card,
        first_target,
        kind,
        source,
        raw_text="first",
    )
    second = services.append_card_reference(
        source_card,
        second_target,
        kind,
        source,
        raw_text="second",
    )

    assert first.order == 0
    assert second.order == 1
    assert list(
        source_card.outgoing_references.filter(source=source).values_list("raw_text", flat=True),
    ) == ["first", "second"]


@pytest.mark.django_db
def test_add_dependency_note_creates_reference_edge_and_prose():
    dependency = kf.make_card(number=1, title="Dependency")
    card = kf.make_card(number=2, title="Dependent")

    note = services.add_dependency_note(card, dependency, "shared machinery")

    assert note.reference.source_card == card
    assert note.reference.target_card == dependency
    assert note.reference.kind.key == "dependency"
    assert note.reference.source.key == "dependencies_section"
    assert note.reference.raw_text == "shared machinery"
    assert note.reference.order == 0
    assert card.dependencies.filter(pk=dependency.pk).exists()

    assert note.item.card == card
    assert note.item.section.key == "dependencies_note"
    assert note.item.text == "shared machinery"
    assert note.item.order == 0
    assert note.item.is_complete is False


@pytest.mark.django_db
def test_add_dependency_note_appends_after_existing_note():
    first_dependency = kf.make_card(number=1, title="First dependency")
    second_dependency = kf.make_card(number=2, title="Second dependency")
    card = kf.make_card(number=3, title="Dependent")

    services.add_dependency_note(card, first_dependency, "first")
    second_note = services.add_dependency_note(card, second_dependency, "second")

    assert second_note.reference.order == 1
    assert second_note.item.order == 1
    assert list(
        card.outgoing_references.filter(source__key="dependencies_section").values_list(
            "raw_text",
            flat=True,
        ),
    ) == ["first", "second"]
    assert list(
        card.items.filter(section__key="dependencies_note").values_list("text", flat=True),
    ) == ["first", "second"]


@pytest.mark.django_db
def test_add_dependency_note_rejects_out_of_order_dependency_without_prose():
    card = kf.make_card(number=1, title="Dependent")
    later_dependency = kf.make_card(number=2, title="Later dependency")

    with pytest.raises(ValidationError, match="before dependent"), transaction.atomic():
        services.add_dependency_note(card, later_dependency, "invalid")

    assert not models.CardReference.objects.exists()
    assert not models.CardItem.objects.exists()
