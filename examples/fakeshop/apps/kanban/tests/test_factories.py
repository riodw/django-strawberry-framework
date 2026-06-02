"""Tests for the kanban test-data factories.

Each factory must persist a valid instance with its required FKs resolved and
its unique fields auto-populated, and must accept overrides.
"""

import pytest

from apps.kanban import factories


@pytest.mark.django_db
def test_lookup_factories_get_or_create_by_key():
    first = factories.make_status()
    second = factories.make_status()
    # Same key -> same canonical row reused (not a duplicate).
    assert first.pk == second.pk
    assert first.key == "todo"
    # Explicit key + label override creates a distinct row.
    done = factories.make_status("done", label="Done!")
    assert done.key == "done"
    assert done.label == "Done!"
    assert done.pk != first.pk


@pytest.mark.django_db
def test_relative_size_and_upstream_carry_extra_fields():
    size = factories.make_relative_size("l", rank=3)
    assert (size.key, size.rank) == ("l", 3)
    upstream = factories.make_upstream()
    assert upstream.emoji == "⚛️"


@pytest.mark.django_db
def test_make_card_fills_required_fks_and_unique_number():
    card = factories.make_card()
    assert card.pk is not None
    # milestone derived from the target version.
    assert card.milestone_id == card.target_version.milestone_id
    assert card.status.key == "todo"
    assert card.planning_state.key == "planned"
    # A second card gets a distinct number and title.
    other = factories.make_card()
    assert other.number != card.number
    assert other.title != card.title
    # The UUID side-row is materialized by the signal.
    assert card.uuid is not None


@pytest.mark.django_db
def test_make_card_accepts_overrides():
    wip = factories.make_status("wip")
    card = factories.make_card(title="Explicit title", status=wip, number=999)
    assert card.title == "Explicit title"
    assert card.status.key == "wip"
    assert card.number == 999


@pytest.mark.django_db
def test_make_card_with_done_status_creates_required_spec():
    card = factories.make_card(status=factories.make_status("done"))
    assert card.status.key == "done"
    assert card.spec.name.startswith(f"spec-{card.number:03d}-")


@pytest.mark.django_db
def test_make_card_item_orders_within_card_and_section():
    card = factories.make_card()
    section = factories.make_section()
    first = factories.make_card_item(card=card, section=section)
    second = factories.make_card_item(card=card, section=section)
    assert (first.order, second.order) == (0, 1)


@pytest.mark.django_db
def test_make_card_reference_defaults_to_related_no_m2m():
    reference = factories.make_card_reference()
    assert reference.kind.key == "related"
    # related references do not create a dependency edge.
    assert not reference.source_card.dependencies.exists()


@pytest.mark.django_db
def test_make_card_reference_dependency_kind_syncs_m2m():
    source, target = factories.make_card(), factories.make_card()
    factories.make_card_reference(
        source_card=source,
        target_card=target,
        kind=factories.make_card_reference_kind("dependency"),
        source=factories.make_card_reference_source("dependencies_section"),
    )
    assert list(source.dependencies.all()) == [target]


@pytest.mark.django_db
def test_make_parity_claim_and_spec_doc():
    claim = factories.make_parity_claim()
    assert claim.upstream.key == "graphene_django"
    assert claim.level.key == "required"
    spec = factories.make_spec_doc()
    assert spec.card.spec == spec


@pytest.mark.django_db
def test_make_card_glossary_term_links_both_ends():
    link = factories.make_card_glossary_term()
    assert link.card_id is not None
    assert link.term_id is not None


@pytest.mark.django_db
def test_make_board_doc_and_card_reference():
    ref = factories.make_board_doc_card_reference()
    assert ref.doc.namespace == "kanban"
    assert ref.card_id is not None


@pytest.mark.django_db
def test_make_label_unique_keys():
    a = factories.make_label()
    b = factories.make_label()
    assert a.key != b.key
