"""Kanban command tests for card and changed-file import workflows."""

import json
from io import StringIO

import pytest
from django.core.management import call_command

from apps.kanban import factories as kf
from apps.kanban import models, services

PACKAGE_FILE = "django_strawberry_framework/types/base.py"
OTHER_PACKAGE_FILE = "django_strawberry_framework/optimizer/walker.py"


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
                    "changed_files": [PACKAGE_FILE],
                },
            ],
        },
    )

    out = StringIO()
    call_command("import_cards", path, stdout=out)

    card = models.Card.objects.get(title="Imported changed files")
    assert "Created" in out.getvalue()
    assert list(card.changed_files.values_list("path", flat=True)) == [PACKAGE_FILE]


@pytest.mark.django_db
def test_import_card_changed_files_command_dry_run_rolls_back(tmp_path, beta_version):
    card = kf.make_card(title="Existing card", target_version=beta_version)
    path = _write_json(
        tmp_path,
        {
            "cards": [{"card": card.title, "changed_files": [PACKAGE_FILE]}],
        },
    )

    out = StringIO()
    call_command("import_card_changed_files", path, "--dry-run", stdout=out)

    assert "Dry run" in out.getvalue()
    assert not card.changed_files.exists()


@pytest.mark.django_db
def test_import_card_changed_files_command_replaces_existing_links(tmp_path, beta_version):
    card = kf.make_card(title="Existing card", target_version=beta_version)
    services.set_card_changed_files(card, [PACKAGE_FILE])
    path = _write_json(
        tmp_path,
        {
            "cards": [{"number": card.number, "changed_files": [OTHER_PACKAGE_FILE]}],
        },
    )

    out = StringIO()
    call_command("import_card_changed_files", path, stdout=out)

    assert "Updated" in out.getvalue()
    assert list(card.changed_files.values_list("path", flat=True)) == [OTHER_PACKAGE_FILE]
