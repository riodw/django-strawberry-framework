"""Kanban service tests for structured card creation and rollback behavior."""

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
    kf.make_relative_size("s", rank=1)
    kf.make_relative_size("m", rank=2)
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
        is_current=False,
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
