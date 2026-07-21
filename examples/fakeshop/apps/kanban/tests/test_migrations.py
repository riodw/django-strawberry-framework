"""Kanban data-migration contract tests."""

import importlib
from types import SimpleNamespace

import pytest
from django.apps import apps

from apps.kanban import factories as kf
from apps.kanban import models

pytestmark = pytest.mark.django_db


def _remove_other_section() -> None:
    migration = importlib.import_module(
        "apps.kanban.migrations.0016_remove_other_section",
    )
    schema_editor = SimpleNamespace(connection=SimpleNamespace(alias="default"))
    migration._remove(apps, schema_editor)


def test_remove_other_section_fails_loudly_while_items_remain():
    other = kf.make_section("other")
    kf.make_card_item(section=other)

    with pytest.raises(RuntimeError, match="still owns 1 card item"):
        _remove_other_section()

    assert models.Section.objects.filter(pk=other.pk).exists()


def test_remove_other_section_deletes_empty_lookup_and_is_idempotent():
    other = kf.make_section("other")

    _remove_other_section()
    _remove_other_section()

    assert not models.Section.objects.filter(pk=other.pk).exists()
