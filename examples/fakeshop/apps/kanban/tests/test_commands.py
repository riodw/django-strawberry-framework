"""Kanban command tests for card, changed-file, and predicted-file import workflows."""

import json
from io import StringIO

import pytest
from django.core.management import CommandError, call_command

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
def _command_lookups(db):
    kf.make_status("todo")
    kf.make_planning_state("planned")
    kf.make_section("dependencies_note")
    kf.make_card_reference_kind("dependency")
    kf.make_relative_size("s", rank=1)


@pytest.fixture
def beta_version():
    return kf.make_target_version("9.9.9", milestone=kf.make_milestone("beta"))


def _write_json(tmp_path, payload: dict) -> str:
    path = tmp_path / "cards.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return str(path)


@pytest.mark.django_db
def test_import_cards_command_accepts_changed_files(tmp_path, beta_version):
    path = _write_json(
        tmp_path,
        {
            "cards": [
                {
                    "title": "Imported changed files",
                    "target_version": beta_version.number,
                    "relative_size": "s",
                    "changed_files": [TRACKED_FILE],
                },
            ],
        },
    )

    out = StringIO()
    call_command("import_cards", path, stdout=out)

    card = models.Card.objects.get(title="Imported changed files")
    assert "Created" in out.getvalue()
    assert list(card.changed_files.values_list("path", flat=True)) == [TRACKED_FILE]


@pytest.mark.django_db
def test_import_card_changed_files_command_dry_run_rolls_back(tmp_path, beta_version):
    card = kf.make_card(title="Existing card", target_version=beta_version)
    path = _write_json(
        tmp_path,
        {
            "cards": [{"card": card.title, "changed_files": [TRACKED_FILE]}],
        },
    )

    out = StringIO()
    call_command("import_card_changed_files", path, "--dry-run", stdout=out)

    assert "Dry run" in out.getvalue()
    assert not card.changed_files.exists()


@pytest.mark.django_db
def test_import_card_changed_files_command_replaces_existing_links(tmp_path, beta_version):
    card = kf.make_card(title="Existing card", target_version=beta_version)
    services.set_card_changed_files(card, [TRACKED_FILE])
    path = _write_json(
        tmp_path,
        {
            "cards": [{"number": card.number, "changed_files": [OTHER_TRACKED_FILE]}],
        },
    )

    out = StringIO()
    call_command("import_card_changed_files", path, stdout=out)

    assert "Updated" in out.getvalue()
    assert list(card.changed_files.values_list("path", flat=True)) == [OTHER_TRACKED_FILE]


@pytest.mark.django_db
def test_import_card_predicted_files_command_dry_run_rolls_back(tmp_path, beta_version):
    card = kf.make_card(title="Future card", target_version=beta_version)
    path = _write_json(
        tmp_path,
        {
            "cards": [{"card": card.title, "predicted_files": [PLANNED_PACKAGE_DIR]}],
        },
    )

    out = StringIO()
    call_command("import_card_predicted_files", path, "--dry-run", stdout=out)

    assert "Dry run" in out.getvalue()
    assert not card.changed_files.exists()
    assert not models.TrackedPath.objects.filter(path=PLANNED_PACKAGE_DIR).exists()


@pytest.mark.django_db
def test_import_card_predicted_files_command_replaces_idempotently(tmp_path, beta_version):
    card = kf.make_card(title="Future card", target_version=beta_version)
    path = _write_json(
        tmp_path,
        {
            "cards": [
                {
                    "number": card.number,
                    "predicted_files": [PLANNED_PACKAGE_DIR, PLANNED_TEST_FILE, TRACKED_FILE],
                },
            ],
        },
    )

    call_command("import_card_predicted_files", path, stdout=StringIO())
    out = StringIO()
    call_command("import_card_predicted_files", path, stdout=out)

    assert "Updated" in out.getvalue()
    assert list(card.changed_files.values_list("path", flat=True)) == [
        PLANNED_PACKAGE_DIR,
        TRACKED_FILE,
        PLANNED_TEST_FILE,
    ]
    assert models.TrackedPath.objects.filter(path=PLANNED_PACKAGE_DIR).count() == 1


@pytest.mark.django_db
def test_import_card_predicted_files_command_marks_directories(tmp_path, beta_version):
    card = kf.make_card(title="Future card", target_version=beta_version)
    path = _write_json(
        tmp_path,
        {
            "cards": [
                {"card": card.title, "predicted_files": [PLANNED_PACKAGE_DIR, PLANNED_TEST_FILE]},
            ],
        },
    )

    call_command("import_card_predicted_files", path, stdout=StringIO())

    planned_dir = models.TrackedPath.objects.get(path=PLANNED_PACKAGE_DIR)
    assert planned_dir.path.endswith("/")
    assert planned_dir.is_directory is True
    assert planned_dir.is_current is False
    planned_file = models.TrackedPath.objects.get(path=PLANNED_TEST_FILE)
    assert planned_file.is_directory is False
    assert planned_file.is_current is False


@pytest.mark.django_db
def test_import_card_predicted_files_command_rejects_done_card(tmp_path, beta_version):
    card = kf.make_card(
        title="Shipped card",
        target_version=beta_version,
        status=kf.make_status("done"),
    )
    path = _write_json(
        tmp_path,
        {
            "cards": [{"card": card.title, "predicted_files": [PLANNED_PACKAGE_DIR]}],
        },
    )

    with pytest.raises(CommandError, match="done card"):
        call_command("import_card_predicted_files", path, stdout=StringIO())

    assert not card.changed_files.exists()


@pytest.mark.django_db
def test_import_card_predicted_files_command_rejects_path_outside_roots(tmp_path, beta_version):
    card = kf.make_card(title="Future card", target_version=beta_version)
    path = _write_json(
        tmp_path,
        {
            "cards": [{"card": card.title, "predicted_files": ["docs/GLOSSARY.md"]}],
        },
    )

    with pytest.raises(CommandError, match="allowed roots"):
        call_command("import_card_predicted_files", path, stdout=StringIO())

    assert not card.changed_files.exists()
