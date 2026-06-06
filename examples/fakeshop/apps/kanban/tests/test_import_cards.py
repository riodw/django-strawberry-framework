"""Tests for the ``import_cards`` management command.

Every test builds exactly the lookups and anchor cards it needs through the
kanban factories — nothing is read from a seeded database or a fixture snapshot,
and no real board card titles/numbers are hardcoded. Expectations are derived
from the objects the test created, so the suite survives board data changes.
"""

import json
from io import StringIO

import pytest
from django.core.management import CommandError, call_command

from apps.kanban import factories as kf
from apps.kanban import models

# Lookup keys the importer resolves a card spec against (the JSON references
# these by key; the importer does a strict ``.get(key=...)``).
_LOOKUP_KEYS = {
    "status": ("todo",),
    "planning_state": ("planned",),
    "section": ("scope", "definition_of_done", "dependencies_note"),
    "label": ("filters", "search", "public-api"),
    "card_reference_kind": ("dependency", "related"),
    "card_reference_source": ("dependencies_section", "card_item", "planning_note"),
}


@pytest.fixture(autouse=True)
def _lookups(db):
    """Create the lookup rows the importer JSON references, via factories.

    The importer matches lookups strictly by key, so the keys a card spec names
    must exist first. Sizes/versions/parity rows are created per-test as needed.
    """
    for key in _LOOKUP_KEYS["status"]:
        kf.make_status(key)
    for key in _LOOKUP_KEYS["planning_state"]:
        kf.make_planning_state(key)
    for key in _LOOKUP_KEYS["section"]:
        kf.make_section(key)
    for key in _LOOKUP_KEYS["label"]:
        kf.make_label(key)
    for key in _LOOKUP_KEYS["card_reference_kind"]:
        kf.make_card_reference_kind(key)
    for key in _LOOKUP_KEYS["card_reference_source"]:
        kf.make_card_reference_source(key)
    for key, rank in (("s", 1), ("m", 2), ("l", 3)):
        kf.make_relative_size(key, rank=rank)


@pytest.fixture
def beta_version():
    """A target version whose milestone the importer should derive onto the card."""
    return kf.make_target_version("9.9.9", milestone=kf.make_milestone("beta"))


def _write(tmp_path, payload):
    path = tmp_path / "cards.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return str(path)


def _minimal_card(version, **overrides):
    card = {"title": "Importer test card", "target_version": version, "relative_size": "m"}
    card.update(overrides)
    return {"cards": [card]}


@pytest.mark.django_db
def test_appends_minimal_card_at_board_end(tmp_path, beta_version):
    kf.make_card()  # an existing card so "append" has a board to extend
    highest = models.Card.objects.order_by("-number").first().number

    path = _write(tmp_path, _minimal_card(beta_version.number))
    call_command("import_cards", path, stdout=StringIO())

    card = models.Card.objects.get(title="Importer test card")
    assert card.number == highest + 1
    assert card.status.key == "todo"
    assert card.planning_state.key == "planned"
    # milestone derived from the version the test created — not a hardcoded value.
    assert card.milestone_id == beta_version.milestone_id
    assert card.target_version_id == beta_version.id


@pytest.mark.django_db
def test_insert_after_renumbers_following_cards(tmp_path, beta_version):
    anchor = kf.make_card()
    follower = kf.make_card()  # numbered after the anchor
    assert follower.number > anchor.number
    follower_before = follower.number

    path = _write(tmp_path, _minimal_card(beta_version.number, after=anchor.title))
    call_command("import_cards", path, stdout=StringIO())

    card = models.Card.objects.get(title="Importer test card")
    assert card.number == anchor.number + 1
    follower.refresh_from_db()
    assert follower.number == follower_before + 1


@pytest.mark.django_db
def test_dependencies_sync_m2m_reference_and_prose(tmp_path, beta_version):
    dependency = kf.make_card()
    payload = _minimal_card(
        beta_version.number,
        dependencies=[{"card": dependency.title, "note": "shared machinery"}],
    )
    path = _write(tmp_path, payload)
    call_command("import_cards", path, stdout=StringIO())

    card = models.Card.objects.get(title="Importer test card")
    # M2M edge auto-synced by the dependency-reference signal.
    assert list(card.dependencies.all()) == [dependency]
    # The dependencies_section reference exists exactly once (no collision).
    refs = card.outgoing_references.filter(source__key="dependencies_section")
    assert refs.count() == 1
    assert refs.first().raw_text == "shared machinery"
    # And the rendered prose bullet exists.
    assert card.items.filter(section__key="dependencies_note", text="shared machinery").exists()


@pytest.mark.django_db
def test_sections_labels_parity_and_checkbox_state(tmp_path, beta_version):
    kf.make_upstream("graphene_django")
    kf.make_parity_level("required")
    payload = _minimal_card(
        beta_version.number,
        labels=["filters", "search"],
        parity=[{"upstream": "graphene_django", "level": "required"}],
        sections={
            "scope": ["scope one"],
            "definition_of_done": ["todo item", {"text": "done item", "done": True}],
        },
    )
    path = _write(tmp_path, payload)
    call_command("import_cards", path, stdout=StringIO())

    card = models.Card.objects.get(title="Importer test card")
    assert sorted(label.key for label in card.labels.all()) == ["filters", "search"]
    assert card.parity_claims.get().upstream.key == "graphene_django"
    dod = card.items.filter(section__key="definition_of_done").order_by("order")
    assert [(item.text, item.is_complete) for item in dod] == [
        ("todo item", False),
        ("done item", True),
    ]


@pytest.mark.django_db
def test_dry_run_creates_nothing(tmp_path, beta_version):
    before = models.Card.objects.count()
    path = _write(tmp_path, _minimal_card(beta_version.number))
    out = StringIO()
    call_command("import_cards", path, "--dry-run", stdout=out)

    assert models.Card.objects.count() == before
    assert not models.Card.objects.filter(title="Importer test card").exists()
    assert "Dry run" in out.getvalue()


@pytest.mark.django_db
def test_multiple_cards_in_one_file(tmp_path, beta_version):
    payload = {
        "cards": [
            {"title": "Card one", "target_version": beta_version.number, "relative_size": "s"},
            {"title": "Card two", "target_version": beta_version.number, "relative_size": "l"},
        ],
    }
    path = _write(tmp_path, payload)
    call_command("import_cards", path, stdout=StringIO())

    assert models.Card.objects.filter(title__in=["Card one", "Card two"]).count() == 2


@pytest.mark.django_db
def test_unknown_lookup_key_raises_with_valid_values(tmp_path, beta_version):
    path = _write(tmp_path, _minimal_card(beta_version.number, relative_size="enormous"))
    with pytest.raises(CommandError, match="Unknown RelativeSize"):
        call_command("import_cards", path, stdout=StringIO())


@pytest.mark.django_db
def test_done_status_is_rejected_at_command_boundary(tmp_path, beta_version):
    path = _write(tmp_path, _minimal_card(beta_version.number, status="done"))
    with pytest.raises(CommandError, match='cannot create "done" cards'):
        call_command("import_cards", path, stdout=StringIO())


@pytest.mark.django_db
def test_duplicate_title_raises(tmp_path, beta_version):
    existing = kf.make_card()
    path = _write(tmp_path, _minimal_card(beta_version.number, title=existing.title))
    with pytest.raises(CommandError, match="already exists"):
        call_command("import_cards", path, stdout=StringIO())


@pytest.mark.django_db
def test_missing_required_field_raises(tmp_path):
    path = _write(tmp_path, {"cards": [{"title": "No version"}]})
    with pytest.raises(CommandError, match="required field"):
        call_command("import_cards", path, stdout=StringIO())


@pytest.mark.django_db
def test_dependencies_under_sections_is_rejected(tmp_path, beta_version):
    path = _write(tmp_path, _minimal_card(beta_version.number, sections={"dependencies": ["x"]}))
    with pytest.raises(CommandError, match="top-level"):
        call_command("import_cards", path, stdout=StringIO())


@pytest.mark.django_db
def test_unresolvable_dependency_card_raises(tmp_path, beta_version):
    payload = _minimal_card(
        beta_version.number,
        dependencies=[{"card": "No such card", "note": ""}],
    )
    path = _write(tmp_path, payload)
    with pytest.raises(CommandError, match="Cannot resolve card reference"):
        call_command("import_cards", path, stdout=StringIO())


@pytest.mark.django_db
def test_out_of_order_dependency_rolls_back_with_clear_error(tmp_path, beta_version):
    dependency = kf.make_card(title="Dependency")
    payload = _minimal_card(
        beta_version.number,
        number=1,
        dependencies=[{"card": dependency.title, "note": "must already be done"}],
    )
    path = _write(tmp_path, payload)

    with pytest.raises(CommandError, match="dependencies must appear before"):
        call_command("import_cards", path, stdout=StringIO())

    dependency.refresh_from_db()
    assert dependency.number == 1
    assert not models.Card.objects.filter(title="Importer test card").exists()


@pytest.mark.django_db
def test_bad_json_and_missing_file_raise(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("{ not json", encoding="utf-8")
    with pytest.raises(CommandError, match="Invalid JSON"):
        call_command("import_cards", str(bad), stdout=StringIO())
    with pytest.raises(CommandError, match="File not found"):
        call_command("import_cards", str(tmp_path / "nope.json"), stdout=StringIO())
