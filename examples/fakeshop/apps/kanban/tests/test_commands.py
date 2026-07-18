"""Kanban command tests for the merged import_card_files workflow (and aliases)."""

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
    kf.make_section("dependencies_note")
    kf.make_card_reference_kind("dependency")
    kf.make_relative_size("s", order=1)


@pytest.fixture
def beta_version():
    return kf.make_target_version("9.9.9", milestone=kf.make_milestone("beta"))


def _write_json(tmp_path, payload: dict) -> str:
    path = tmp_path / "cards.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return str(path)


# --- merged command: --kind changed --------------------------------------


@pytest.mark.django_db
def test_import_card_files_changed_dry_run_rolls_back(tmp_path, beta_version):
    card = kf.make_card(title="Existing card", target_version=beta_version)
    path = _write_json(
        tmp_path,
        {"cards": [{"card": card.title, "files": [TRACKED_FILE]}]},
    )

    out = StringIO()
    call_command("import_card_files", path, "--kind", "changed", "--dry-run", stdout=out)

    assert "Dry run" in out.getvalue()
    assert not card.changed_files.exists()


@pytest.mark.django_db
def test_import_card_files_changed_replaces_existing_links(tmp_path, beta_version):
    card = kf.make_card(title="Existing card", target_version=beta_version)
    services.set_card_changed_files(card, [TRACKED_FILE])
    path = _write_json(
        tmp_path,
        {"cards": [{"number": card.number, "files": [OTHER_TRACKED_FILE]}]},
    )

    out = StringIO()
    call_command("import_card_files", path, "--kind", "changed", stdout=out)

    assert "Updated" in out.getvalue()
    assert list(card.changed_files.values_list("path", flat=True)) == [OTHER_TRACKED_FILE]
    assert list(card.path_links.values_list("kind", flat=True)) == [models.CARD_PATH_LINK_CHANGED]


@pytest.mark.django_db
def test_import_card_files_changed_clears_links(tmp_path, beta_version):
    card = kf.make_card(title="Existing card", target_version=beta_version)
    services.set_card_changed_files(card, [TRACKED_FILE])
    path = _write_json(tmp_path, {"cards": [{"card": card.title, "files": []}]})

    call_command("import_card_files", path, "--kind", "changed", stdout=StringIO())

    assert not card.changed_files.exists()


@pytest.mark.django_db
def test_import_card_files_missing_files_key_errors(tmp_path, beta_version):
    card = kf.make_card(title="Existing card", target_version=beta_version)
    path = _write_json(tmp_path, {"cards": [{"card": card.title}]})

    with pytest.raises(CommandError, match='"files"'):
        call_command("import_card_files", path, "--kind", "changed", stdout=StringIO())


@pytest.mark.django_db
def test_import_card_files_requires_kind(tmp_path, beta_version):
    card = kf.make_card(title="Existing card", target_version=beta_version)
    path = _write_json(tmp_path, {"cards": [{"card": card.title, "files": []}]})

    with pytest.raises(CommandError):
        call_command("import_card_files", path, stdout=StringIO())


# --- merged command: --kind predicted ------------------------------------


@pytest.mark.django_db
def test_import_card_files_predicted_dry_run_rolls_back(tmp_path, beta_version):
    card = kf.make_card(title="Future card", target_version=beta_version)
    path = _write_json(
        tmp_path,
        {"cards": [{"card": card.title, "files": [PLANNED_PACKAGE_DIR]}]},
    )

    out = StringIO()
    call_command("import_card_files", path, "--kind", "predicted", "--dry-run", stdout=out)

    assert "Dry run" in out.getvalue()
    assert not card.changed_files.exists()
    assert not models.TrackedPath.objects.filter(path=PLANNED_PACKAGE_DIR).exists()


@pytest.mark.django_db
def test_import_card_files_predicted_replaces_idempotently(tmp_path, beta_version):
    card = kf.make_card(title="Future card", target_version=beta_version)
    path = _write_json(
        tmp_path,
        {
            "cards": [
                {
                    "number": card.number,
                    "files": [PLANNED_PACKAGE_DIR, PLANNED_TEST_FILE, TRACKED_FILE],
                },
            ],
        },
    )

    call_command("import_card_files", path, "--kind", "predicted", stdout=StringIO())
    out = StringIO()
    call_command("import_card_files", path, "--kind", "predicted", stdout=out)

    assert "Updated" in out.getvalue()
    assert list(card.changed_files.values_list("path", flat=True)) == [
        PLANNED_PACKAGE_DIR,
        TRACKED_FILE,
        PLANNED_TEST_FILE,
    ]
    assert models.TrackedPath.objects.filter(path=PLANNED_PACKAGE_DIR).count() == 1
    kinds = set(card.path_links.values_list("kind", flat=True))
    assert kinds == {models.CARD_PATH_LINK_PREDICTED}


@pytest.mark.django_db
def test_import_card_files_predicted_marks_directories(tmp_path, beta_version):
    card = kf.make_card(title="Future card", target_version=beta_version)
    path = _write_json(
        tmp_path,
        {"cards": [{"card": card.title, "files": [PLANNED_PACKAGE_DIR, PLANNED_TEST_FILE]}]},
    )

    call_command("import_card_files", path, "--kind", "predicted", stdout=StringIO())

    planned_dir = models.TrackedPath.objects.get(path=PLANNED_PACKAGE_DIR)
    assert planned_dir.path.endswith("/")
    assert planned_dir.is_directory is True
    assert planned_dir.is_current is False
    planned_file = models.TrackedPath.objects.get(path=PLANNED_TEST_FILE)
    assert planned_file.is_directory is False
    assert planned_file.is_current is False


@pytest.mark.django_db
def test_import_card_files_predicted_rejects_done_card(tmp_path, beta_version):
    card = kf.make_card(
        title="Shipped card",
        target_version=beta_version,
        status=kf.make_status("done"),
    )
    path = _write_json(
        tmp_path,
        {"cards": [{"card": card.title, "files": [PLANNED_PACKAGE_DIR]}]},
    )

    with pytest.raises(CommandError, match="done card"):
        call_command("import_card_files", path, "--kind", "predicted", stdout=StringIO())

    assert not card.changed_files.exists()


@pytest.mark.django_db
def test_import_card_files_predicted_rejects_path_outside_roots(tmp_path, beta_version):
    card = kf.make_card(title="Future card", target_version=beta_version)
    path = _write_json(
        tmp_path,
        {"cards": [{"card": card.title, "files": ["docs/GLOSSARY.md"]}]},
    )

    with pytest.raises(CommandError, match="allowed roots"):
        call_command("import_card_files", path, "--kind", "predicted", stdout=StringIO())

    assert not card.changed_files.exists()


@pytest.mark.django_db
def test_import_card_files_wraps_validation_error_as_command_error(
    tmp_path,
    beta_version,
    monkeypatch,
):
    """A signal-guard ValidationError surfaces as CommandError, not a raw traceback."""
    from django.core.exceptions import ValidationError

    card = kf.make_card(title="Guarded card", target_version=beta_version)

    def _raise(*args, **kwargs):
        raise ValidationError("guard says no")

    monkeypatch.setattr(services, "set_card_changed_files", _raise)
    monkeypatch.setattr(services, "set_card_predicted_files", _raise)

    changed = _write_json(tmp_path, {"cards": [{"card": card.title, "files": []}]})
    with pytest.raises(CommandError, match="guard says no"):
        call_command("import_card_files", changed, "--kind", "changed", stdout=StringIO())

    predicted = _write_json(tmp_path, {"cards": [{"card": card.title, "files": []}]})
    with pytest.raises(CommandError, match="guard says no"):
        call_command("import_card_files", predicted, "--kind", "predicted", stdout=StringIO())


# --- deprecated aliases (legacy JSON keys, pinned kind) -------------------


@pytest.mark.django_db
def test_changed_files_alias_uses_legacy_key(tmp_path, beta_version):
    card = kf.make_card(title="Existing card", target_version=beta_version)
    path = _write_json(
        tmp_path,
        {"cards": [{"card": card.title, "changed_files": [TRACKED_FILE]}]},
    )

    call_command("import_card_changed_files", path, stdout=StringIO())

    assert list(card.changed_files.values_list("path", flat=True)) == [TRACKED_FILE]
    assert list(card.path_links.values_list("kind", flat=True)) == [models.CARD_PATH_LINK_CHANGED]


@pytest.mark.django_db
def test_predicted_files_alias_uses_legacy_key(tmp_path, beta_version):
    card = kf.make_card(title="Future card", target_version=beta_version)
    path = _write_json(
        tmp_path,
        {"cards": [{"card": card.title, "predicted_files": [PLANNED_PACKAGE_DIR]}]},
    )

    call_command("import_card_predicted_files", path, stdout=StringIO())

    assert list(card.changed_files.values_list("path", flat=True)) == [PLANNED_PACKAGE_DIR]
    assert list(card.path_links.values_list("kind", flat=True)) == [
        models.CARD_PATH_LINK_PREDICTED,
    ]


@pytest.mark.django_db
def test_changed_files_alias_missing_legacy_key_errors(tmp_path, beta_version):
    card = kf.make_card(title="Existing card", target_version=beta_version)
    path = _write_json(tmp_path, {"cards": [{"card": card.title, "files": [TRACKED_FILE]}]})

    with pytest.raises(CommandError, match='"changed_files"'):
        call_command("import_card_changed_files", path, stdout=StringIO())
