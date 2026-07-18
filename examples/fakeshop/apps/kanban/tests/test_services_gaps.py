"""Service-layer gap coverage for branches the main service suite leaves open.

Kept in a separate module from ``test_services.py`` (concurrently owned) and
scoped to WS-3D's list: the ``_database_alias`` multi-database guard, the
``_target_number`` ``after`` branch, the ``create_card_from_spec`` rejection
branches (duplicate title / born-done / dependencies-in-sections), and the
``sync_tracked_paths_from_constants`` current<->historical flip in both
directions.
"""

import pytest

from apps.kanban import factories as kf
from apps.kanban import models, services
from apps.kanban.constants import TRACKED_FILE_PATHS


@pytest.fixture(autouse=True)
def _service_lookups(db):
    kf.make_status("todo")
    kf.make_status("done")
    kf.make_priority("medium")
    kf.make_relative_size("s", order=1)
    kf.make_section("scope")


@pytest.fixture
def alpha_version():
    return kf.make_target_version("0.0.8", milestone=kf.make_milestone("alpha"))


# ---------------------------------------------------------------------------
# _database_alias: reject objects spanning databases
# ---------------------------------------------------------------------------


def test_database_alias_rejects_objects_from_different_databases():
    left = models.Card(number=1)
    left._state.db = "default"
    right = models.Card(number=2)
    right._state.db = "other"

    with pytest.raises(ValueError, match="same database"):
        services._database_alias(left, right)


def test_database_alias_returns_none_for_unsaved_objects():
    assert services._database_alias(models.Card(number=1)) is None


# ---------------------------------------------------------------------------
# _target_number: the "after" branch
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_create_card_from_spec_after_places_card_below_reference(alpha_version):
    kf.make_card(number=1, title="Anchor card")

    card = services.create_card_from_spec(
        {
            "title": "Trailing card",
            "target_version": alpha_version.number,
            "relative_size": "s",
            "after": "Anchor card",
        },
    )

    assert card.number == 2


# ---------------------------------------------------------------------------
# create_card_from_spec: rejection branches
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_create_card_from_spec_rejects_duplicate_title(alpha_version):
    kf.make_card(number=1, title="Existing title")

    with pytest.raises(services.KanbanServiceError) as excinfo:
        services.create_card_from_spec(
            {
                "title": "Existing title",
                "target_version": alpha_version.number,
                "relative_size": "s",
            },
        )
    assert excinfo.value.code == "duplicate_card_title"


@pytest.mark.django_db
def test_create_card_from_spec_rejects_done_status(alpha_version):
    with pytest.raises(services.KanbanServiceError) as excinfo:
        services.create_card_from_spec(
            {
                "title": "Born done card",
                "target_version": alpha_version.number,
                "relative_size": "s",
                "status": "done",
            },
        )
    assert excinfo.value.code == "cannot_create_done_card"
    assert not models.Card.objects.filter(title="Born done card").exists()


@pytest.mark.django_db
def test_create_card_from_spec_rejects_dependencies_in_sections(alpha_version):
    with pytest.raises(services.KanbanServiceError) as excinfo:
        services.create_card_from_spec(
            {
                "title": "Misfiled dependencies card",
                "target_version": alpha_version.number,
                "relative_size": "s",
                "sections": {"dependencies": ["should be top-level"]},
            },
        )
    assert excinfo.value.code == "dependencies_in_sections"


# ---------------------------------------------------------------------------
# sync_tracked_paths_from_constants: current <-> historical flip-back
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_sync_tracked_paths_flips_historical_back_to_current_and_current_out():
    allowlisted = TRACKED_FILE_PATHS[0]
    # A path in the allowlist that is currently marked historical must flip back
    # to current when it reappears in the generated constants.
    historical_but_allowlisted = models.TrackedPath.objects.create(
        path=allowlisted,
        state=models.TRACKED_PATH_HISTORICAL,
    )
    # A path NOT in the allowlist that is marked current must flip to historical.
    current_but_dropped = models.TrackedPath.objects.create(
        path="django_strawberry_framework/dropped_module.py",
        state=models.TRACKED_PATH_CURRENT,
    )
    # A planned row (not in the allowlist) must be left untouched.
    planned = models.TrackedPath.objects.create(
        path="django_strawberry_framework/planned_module.py",
        state=models.TRACKED_PATH_PLANNED,
    )

    services.sync_tracked_paths_from_constants()

    historical_but_allowlisted.refresh_from_db()
    current_but_dropped.refresh_from_db()
    planned.refresh_from_db()
    assert historical_but_allowlisted.state == models.TRACKED_PATH_CURRENT
    assert current_but_dropped.state == models.TRACKED_PATH_HISTORICAL
    assert planned.state == models.TRACKED_PATH_PLANNED
