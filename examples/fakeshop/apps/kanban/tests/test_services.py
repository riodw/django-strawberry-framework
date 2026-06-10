"""Service-level workflows for the kanban app."""

import pytest
from django.core.exceptions import ValidationError

from apps.kanban import factories as kf
from apps.kanban import models, services


@pytest.fixture(autouse=True)
def _service_lookups(db):
    kf.make_status("todo")
    kf.make_planning_state("planned")
    kf.make_priority("medium")
    kf.make_severity("medium")
    kf.make_section("scope")
    kf.make_section("definition_of_done")
    kf.make_section("dependencies_note")
    kf.make_card_reference_kind("dependency")
    kf.make_card_reference_kind("related")
    kf.make_label("filters")
    kf.make_label("search")
    kf.make_relative_size("s", rank=1)
    kf.make_relative_size("m", rank=2)
    kf.make_upstream("graphene_django")
    kf.make_parity_level("required")


@pytest.fixture
def beta_version():
    return kf.make_target_version("9.9.9", milestone=kf.make_milestone("beta"))


@pytest.mark.django_db
def test_create_card_from_spec_builds_card_and_children(beta_version):
    dependency = kf.make_card(number=1, title="Dependency")
    related = kf.make_card(number=2, title="Related")

    card = services.create_card_from_spec(
        {
            "title": "Service card",
            "target_version": beta_version.number,
            "relative_size": "s",
            "priority": "medium",
            "severity": "medium",
            "labels": ["filters", "search"],
            "parity": [{"upstream": "graphene_django", "level": "required"}],
            "dependencies": [{"card": dependency.title, "note": "shared machinery"}],
            "sections": {
                "scope": ["scope bullet"],
                "definition_of_done": [{"text": "done bullet", "done": True}],
            },
            "references": [{"target": related.title, "kind": "related", "text": "see also"}],
        },
    )

    assert card.title == "Service card"
    assert card.target_version == beta_version
    assert card.milestone == beta_version.milestone
    assert card.relative_size.key == "s"
    assert sorted(card.labels.values_list("key", flat=True)) == ["filters", "search"]
    assert card.parity_claims.get().upstream.key == "graphene_django"
    assert card.dependencies.get() == dependency
    assert card.items.get(section__key="dependencies_note").text == "shared machinery"
    assert card.items.get(section__key="scope").text == "scope bullet"
    assert card.items.get(section__key="definition_of_done").is_complete is True
    assert list(card.outgoing_references.values_list("target_card__title", "kind__key")) == [
        ("Dependency", "dependency"),
        ("Related", "related"),
    ]


@pytest.mark.django_db
def test_create_card_from_spec_rolls_back_invalid_dependency(beta_version):
    later_dependency = kf.make_card(number=2, title="Later dependency")

    with pytest.raises(ValidationError, match="before dependent"):
        services.create_card_from_spec(
            {
                "title": "Invalid service card",
                "number": 1,
                "target_version": beta_version.number,
                "relative_size": "m",
                "dependencies": [{"card": later_dependency.title, "note": "not earlier"}],
            },
        )

    later_dependency.refresh_from_db()
    assert later_dependency.number == 2
    assert not models.Card.objects.filter(title="Invalid service card").exists()
    assert not models.CardItem.objects.filter(text="not earlier").exists()
