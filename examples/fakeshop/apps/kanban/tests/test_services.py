"""Kanban service tests for card resolution, creation, tracked paths, validation, and rollback."""

import pytest
from django.core.exceptions import ValidationError

from apps.kanban import factories as kf
from apps.kanban import models, services

TRACKED_FILE = "django_strawberry_framework/types/base.py"
OTHER_TRACKED_FILE = "django_strawberry_framework/optimizer/walker.py"
# Paths under allowed roots that are deliberately absent from the generated
# allowlist (constants.py), so the importer treats them as planned/predicted
# rows (is_current=False). Keep these fictional: if a real package or test dir
# ever claims these paths they will land in constants.py, and
# sync_tracked_paths_from_constants will flip is_current to True, breaking the
# planned-row assertions below.
PLANNED_PACKAGE_DIR = "django_strawberry_framework/planned_only/"
PLANNED_TEST_FILE = "tests/planned_only/test_planned_only.py"


@pytest.fixture(autouse=True)
def _service_lookups(db):
    kf.make_status("todo")
    kf.make_priority("medium")
    kf.make_section("scope")
    kf.make_section("definition_of_done")
    kf.make_section("dependencies_note")
    kf.make_card_reference_kind("dependency")
    kf.make_card_reference_kind("related")
    kf.make_label("filters")
    kf.make_label("search")
    kf.make_relative_size("s", order=1)
    kf.make_relative_size("m", order=2)
    kf.make_upstream("graphene_django")
    kf.make_parity_level("required")


@pytest.fixture
def beta_version():
    return kf.make_target_version("9.9.9", milestone=kf.make_milestone("beta"))


@pytest.mark.django_db
@pytest.mark.parametrize("identifier", ["\u00b2", "1" * 5000])
def test_resolve_card_digit_like_invalid_reference_raises_service_error(identifier):
    with pytest.raises(services.KanbanServiceError, match="Cannot resolve card reference"):
        services.resolve_card(identifier)


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
def test_create_card_from_spec_links_changed_files(beta_version):
    card = services.create_card_from_spec(
        {
            "title": "Changed files card",
            "target_version": beta_version.number,
            "relative_size": "s",
            "changed_files": [OTHER_TRACKED_FILE, TRACKED_FILE],
        },
    )

    assert list(card.changed_files.values_list("path", flat=True)) == [
        OTHER_TRACKED_FILE,
        TRACKED_FILE,
    ]


@pytest.mark.django_db
def test_create_card_from_spec_deduplicates_changed_files(beta_version):
    card = services.create_card_from_spec(
        {
            "title": "Deduped changed files card",
            "target_version": beta_version.number,
            "relative_size": "s",
            "changed_files": [TRACKED_FILE, TRACKED_FILE],
        },
    )

    assert list(card.changed_files.values_list("path", flat=True)) == [TRACKED_FILE]


@pytest.mark.django_db
def test_create_card_from_spec_creates_planned_rows_for_future_paths(beta_version):
    """New cards are never done, so unknown paths under allowed roots become planned rows."""
    card = services.create_card_from_spec(
        {
            "title": "Predicted files card",
            "target_version": beta_version.number,
            "relative_size": "s",
            "changed_files": [PLANNED_PACKAGE_DIR, PLANNED_TEST_FILE],
        },
    )

    planned_dir = card.changed_files.get(path=PLANNED_PACKAGE_DIR)
    assert planned_dir.is_current is False
    assert planned_dir.is_directory is True
    planned_file = card.changed_files.get(path=PLANNED_TEST_FILE)
    assert planned_file.is_current is False
    assert planned_file.is_directory is False


@pytest.mark.django_db
def test_create_card_from_spec_rejects_path_outside_allowed_roots(beta_version):
    with pytest.raises(services.KanbanServiceError, match="allowed roots"):
        services.create_card_from_spec(
            {
                "title": "Out-of-root changed file card",
                "target_version": beta_version.number,
                "relative_size": "s",
                "changed_files": ["docs/GLOSSARY.md"],
            },
        )

    assert not models.Card.objects.filter(title="Out-of-root changed file card").exists()


@pytest.mark.django_db
def test_create_card_from_spec_rejects_escaping_path(beta_version):
    with pytest.raises(services.KanbanServiceError, match="repo-relative"):
        services.create_card_from_spec(
            {
                "title": "Escaping changed file card",
                "target_version": beta_version.number,
                "relative_size": "s",
                "changed_files": ["django_strawberry_framework/../secrets.py"],
            },
        )


@pytest.mark.django_db
def test_create_card_from_spec_accepts_historical_changed_file(beta_version):
    historical = models.TrackedPath.objects.create(
        path="django_strawberry_framework/old_module.py",
        state=models.TRACKED_PATH_HISTORICAL,
    )

    card = services.create_card_from_spec(
        {
            "title": "Historical changed file card",
            "target_version": beta_version.number,
            "relative_size": "s",
            "changed_files": [historical.path],
        },
    )

    assert card.changed_files.get() == historical
    historical.refresh_from_db()
    assert historical.is_current is False


@pytest.mark.django_db
def test_set_card_changed_files_rejects_unknown_path(beta_version):
    """The DONE-card surface stays strict: no planned-row creation."""
    card = kf.make_card(title="Strict changed files card", target_version=beta_version)

    with pytest.raises(services.KanbanServiceError, match="Unknown tracked path"):
        services.set_card_changed_files(card, ["django_strawberry_framework/not_real.py"])

    assert not card.changed_files.exists()
    assert not models.TrackedPath.objects.filter(
        path="django_strawberry_framework/not_real.py",
    ).exists()


@pytest.mark.django_db
def test_set_card_predicted_files_rejects_done_card(beta_version):
    card = kf.make_card(
        title="Shipped card",
        target_version=beta_version,
        status=kf.make_status("done"),
    )

    with pytest.raises(services.KanbanServiceError, match="done card"):
        services.set_card_predicted_files(card, [PLANNED_PACKAGE_DIR])

    assert not card.changed_files.exists()


@pytest.mark.django_db
def test_set_card_predicted_files_keeps_current_rows_current(beta_version):
    """Predicting a path that already exists links the current row unchanged."""
    card = kf.make_card(title="Mixed prediction card", target_version=beta_version)

    services.set_card_predicted_files(card, [TRACKED_FILE, PLANNED_PACKAGE_DIR])

    current = card.changed_files.get(path=TRACKED_FILE)
    assert current.is_current is True
    assert current.is_directory is False


@pytest.mark.django_db
def test_add_and_remove_dependency_round_trip(beta_version):
    target = kf.make_card(number=1, title="Dep target", target_version=beta_version)
    source = kf.make_card(number=2, title="Dep source", target_version=beta_version)

    services.add_dependency(source, target)
    assert source.dependency_cards.filter(pk=target.pk).exists()

    removed = services.remove_dependency(source, target)
    assert removed == 1
    assert not source.dependency_cards.filter(pk=target.pk).exists()


@pytest.mark.django_db
def test_add_dependency_rejects_non_dependency_kind(beta_version):
    target = kf.make_card(number=1, title="Kind target", target_version=beta_version)
    source = kf.make_card(number=2, title="Kind source", target_version=beta_version)

    with pytest.raises(services.KanbanServiceError, match="add_dependency kind"):
        services.add_dependency(source, target, kind="related")


@pytest.mark.django_db
def test_set_card_changed_files_links_carry_changed_kind(beta_version):
    card = kf.make_card(title="Changed-kind card", target_version=beta_version)
    services.set_card_changed_files(card, [TRACKED_FILE])

    link = models.CardPathLink.objects.get(card=card)
    assert link.kind == models.CARD_PATH_LINK_CHANGED
    assert link.path.path == TRACKED_FILE


@pytest.mark.django_db
def test_set_card_predicted_files_links_carry_predicted_kind(beta_version):
    card = kf.make_card(title="Predicted-kind card", target_version=beta_version)
    services.set_card_predicted_files(card, [PLANNED_PACKAGE_DIR])

    link = models.CardPathLink.objects.get(card=card)
    assert link.kind == models.CARD_PATH_LINK_PREDICTED


@pytest.mark.django_db
def test_set_card_changed_files_link_has_uuid_side_row(beta_version):
    # M2M .set() inserts through rows with bulk_create (no post_save), so the
    # UUID side-row must be created by the m2m_changed receiver, not create_uuid_row.
    card = kf.make_card(title="Uuid side-row card", target_version=beta_version)
    services.set_card_changed_files(card, [TRACKED_FILE])

    link = models.CardPathLink.objects.get(card=card)
    assert link.uuid is not None
    assert link.uuid.id is not None


@pytest.mark.django_db
def test_set_card_changed_files_flips_predicted_link_to_changed(beta_version):
    # A predicted->changed re-import must flip the kind on the retained link;
    # .set(through_defaults=...) alone leaves the old kind on surviving rows.
    card = kf.make_card(title="Flip predicted card", target_version=beta_version)
    services.set_card_predicted_files(card, [TRACKED_FILE])
    assert models.CardPathLink.objects.get(card=card).kind == models.CARD_PATH_LINK_PREDICTED

    services.set_card_changed_files(card, [TRACKED_FILE])
    link = models.CardPathLink.objects.get(card=card)
    assert link.kind == models.CARD_PATH_LINK_CHANGED
    assert link.uuid is not None


@pytest.mark.django_db
def test_set_card_predicted_files_flips_changed_link_to_predicted(beta_version):
    # The reverse direction: changed->predicted flip on a retained link.
    card = kf.make_card(title="Flip changed card", target_version=beta_version)
    services.set_card_changed_files(card, [TRACKED_FILE])
    assert models.CardPathLink.objects.get(card=card).kind == models.CARD_PATH_LINK_CHANGED

    services.set_card_predicted_files(card, [TRACKED_FILE])
    assert models.CardPathLink.objects.get(card=card).kind == models.CARD_PATH_LINK_PREDICTED


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


# ---------------------------------------------------------------------------
# move_card_number / compact_card_numbers (the renumbering engine)
# ---------------------------------------------------------------------------


def _numbers_by_title(*titles: str) -> list[int]:
    return [models.Card.objects.get(title=title).number for title in titles]


@pytest.fixture
def three_cards():
    return [kf.make_card(number=index, title=f"Board card {index}") for index in (1, 2, 3)]


@pytest.mark.django_db
def test_move_card_number_down_shifts_intermediate_cards_up(three_cards):
    _first, _second, third = three_cards

    moved = services.move_card_number(third, 1)

    assert moved.number == 1
    assert _numbers_by_title("Board card 3", "Board card 1", "Board card 2") == [1, 2, 3]


@pytest.mark.django_db
def test_move_card_number_up_shifts_intermediate_cards_down(three_cards):
    first, _second, _third = three_cards

    services.move_card_number(first, 3)

    assert _numbers_by_title("Board card 2", "Board card 3", "Board card 1") == [1, 2, 3]


@pytest.mark.django_db
def test_move_card_number_to_middle(three_cards):
    first, _second, _third = three_cards

    services.move_card_number(first, 2)

    assert _numbers_by_title("Board card 2", "Board card 1", "Board card 3") == [1, 2, 3]


@pytest.mark.django_db
def test_move_card_number_same_slot_is_a_no_op(three_cards):
    _first, second, _third = three_cards

    services.move_card_number(second, 2)

    assert _numbers_by_title("Board card 1", "Board card 2", "Board card 3") == [1, 2, 3]


@pytest.mark.django_db
def test_move_card_number_does_not_churn_neighbor_updated_date(three_cards):
    _first, second, third = three_cards
    before = models.Card.objects.get(pk=second.pk).updated_date

    services.move_card_number(third, 1)

    after = models.Card.objects.get(pk=second.pk).updated_date
    assert after == before


@pytest.mark.django_db
def test_move_card_number_rejects_out_of_range_target(three_cards):
    first, _second, _third = three_cards

    with pytest.raises(services.KanbanServiceError, match="between 1 and 3") as excinfo:
        services.move_card_number(first, 4)
    assert excinfo.value.code == "card_number_out_of_range"

    with pytest.raises(services.KanbanServiceError, match="between 1 and 3"):
        services.move_card_number(first, 0)

    assert _numbers_by_title("Board card 1", "Board card 2", "Board card 3") == [1, 2, 3]


@pytest.mark.django_db
def test_move_card_number_rejects_non_integer():
    card = kf.make_card(number=1, title="Board card 1")

    with pytest.raises(services.KanbanServiceError, match="integer") as excinfo:
        services.move_card_number(card, "not-a-number")
    assert excinfo.value.code == "invalid_card_number"


@pytest.mark.django_db
def test_move_card_number_rejects_unsaved_card():
    kf.make_card(number=1, title="Board card 1")
    ghost = models.Card(number=99)

    with pytest.raises(services.KanbanServiceError, match="no stored board number") as excinfo:
        services.move_card_number(ghost, 1)
    assert excinfo.value.code == "unknown_card"


@pytest.mark.django_db
def test_move_card_number_rejects_dependency_reordering(three_cards):
    first, second, _third = three_cards
    services.add_dependency(second, first)

    with pytest.raises(services.KanbanServiceError, match="before dependent") as excinfo:
        services.move_card_number(first, 3)
    assert excinfo.value.code == "dependency_order"

    with pytest.raises(services.KanbanServiceError, match="before dependent"):
        services.move_card_number(second, 1)

    assert _numbers_by_title("Board card 1", "Board card 2", "Board card 3") == [1, 2, 3]


@pytest.mark.django_db
def test_move_card_number_allows_dependency_preserving_move(three_cards):
    first, _second, third = three_cards
    services.add_dependency(third, first)

    services.move_card_number(third, 2)

    assert _numbers_by_title("Board card 1", "Board card 3", "Board card 2") == [1, 2, 3]


@pytest.mark.django_db
def test_compact_card_numbers_closes_the_delete_gap(three_cards):
    _first, second, _third = three_cards

    second.delete()

    assert list(models.Card.objects.order_by("number").values_list("number", flat=True)) == [1, 2]


# ---------------------------------------------------------------------------
# Error codes
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_service_error_codes_are_stable():
    with pytest.raises(services.KanbanServiceError) as unresolvable:
        services.resolve_card("no such card")
    assert unresolvable.value.code == "unresolvable_card"

    with pytest.raises(services.KanbanServiceError) as unknown_lookup:
        services.set_card_status(kf.make_card(), "nope", actor=kf.make_actor())
    assert unknown_lookup.value.code == "unknown_lookup"

    with pytest.raises(services.KanbanServiceError) as missing_field:
        services.create_card_from_spec({"title": "Codes card"})
    assert missing_field.value.code == "missing_required_field"


@pytest.mark.django_db
def test_tracked_path_error_codes(beta_version):
    card = kf.make_card(title="Code paths card", target_version=beta_version)

    with pytest.raises(services.KanbanServiceError) as outside:
        services.set_card_predicted_files(card, ["docs/GLOSSARY.md"])
    assert outside.value.code == "tracked_path_outside_roots"

    with pytest.raises(services.KanbanServiceError) as unknown:
        services.set_card_changed_files(card, ["django_strawberry_framework/not_real.py"])
    assert unknown.value.code == "unknown_tracked_path"

    with pytest.raises(services.KanbanServiceError) as invalid:
        services.set_card_predicted_files(card, ["../escape.py"])
    assert invalid.value.code == "invalid_tracked_path"


@pytest.mark.django_db
def test_resolve_card_by_uuid(beta_version):
    card = kf.make_card(title="Uuid card", target_version=beta_version)

    resolved = services.resolve_card({"uuid": str(card.uuid.id)})

    assert resolved.pk == card.pk


@pytest.mark.django_db
def test_resolve_card_by_slug(beta_version):
    card = kf.make_card(title="Slug Target Card", target_version=beta_version)

    resolved = services.resolve_card({"slug": card.slug})

    assert resolved.pk == card.pk


@pytest.mark.django_db
def test_resolve_card_unknown_uuid_raises_unresolvable():
    import uuid as uuid_module

    with pytest.raises(services.KanbanServiceError) as error:
        services.resolve_card({"uuid": str(uuid_module.uuid4())})
    assert error.value.code == "unresolvable_card"


@pytest.mark.django_db
def test_resolve_card_invalid_uuid_raises_unresolvable():
    with pytest.raises(services.KanbanServiceError) as error:
        services.resolve_card({"uuid": "not-a-uuid"})
    assert error.value.code == "unresolvable_card"


@pytest.mark.django_db
def test_resolve_card_unknown_slug_raises_unresolvable(beta_version):
    kf.make_card(title="Present card", target_version=beta_version)

    with pytest.raises(services.KanbanServiceError) as error:
        services.resolve_card({"slug": "no_such_slug"})
    assert error.value.code == "unresolvable_card"


@pytest.mark.django_db
def test_resolve_card_spec_without_identifier_raises_unresolvable():
    with pytest.raises(services.KanbanServiceError) as error:
        services.resolve_card({"files": []})
    assert error.value.code == "unresolvable_card"


@pytest.mark.django_db
def test_resolve_card_by_spec_card_key(beta_version):
    card = kf.make_card(title="Keyed card", target_version=beta_version)

    resolved = services.resolve_card({"card": card.title, "files": []})

    assert resolved.pk == card.pk


@pytest.mark.django_db
def test_resolve_card_ambiguous_title_raises(beta_version, monkeypatch):
    """Titles are unique today, so this path is unreachable in practice.

    We force ``MultipleObjectsReturned`` to prove that a future duplicate title
    fails loudly with code="ambiguous_card" rather than silently picking a row.
    """
    card = kf.make_card(title="Ambiguous card", target_version=beta_version)

    def _raise_multiple(**kwargs):
        raise models.Card.MultipleObjectsReturned

    monkeypatch.setattr(models.Card.objects, "get", _raise_multiple)

    with pytest.raises(services.KanbanServiceError) as error:
        services.resolve_card(card.title)
    assert error.value.code == "ambiguous_card"
