"""In-process wiring + error-mapping tests for the kanban GraphQL mutation surface (WS-3B).

Executed against the composed project ``config.schema`` via ``execute_sync`` with a
real GraphQL document (per AGENTS.md), never by calling resolver methods directly.
The live HTTP counterpart lives in ``examples/fakeshop/test_query/test_kanban_mutations_api.py``;
this tier pins the thin-wrapper wiring (a mutation calls its service and the write
lands) and the service-error -> ``{ ok, errors }`` envelope mapping that the
``_ServiceErrorMixin`` resolver seams add on top of the framework's plain-form pipeline.
"""

from __future__ import annotations

import sys

import pytest
from django.contrib.auth import get_user_model
from django.test import RequestFactory
from schema_reload import reload_all_project_schemas
from strawberry import relay

from apps.kanban import factories as kf
from apps.kanban import models


@pytest.fixture(scope="module")
def project_schema():
    """Rebuild the full project schema (all apps) so ``config.schema`` binds the kanban mutations."""
    reload_all_project_schemas()
    return sys.modules["config.schema"].schema


@pytest.fixture
def staff_context(db):
    """A bare-``HttpRequest`` context carrying a staff user (``IsStaffUser`` authorizes it)."""
    request = RequestFactory().post("/graphql/")
    request.user = get_user_model().objects.create_user(
        username="agent",
        password="x",
        is_staff=True,
    )
    return request


@pytest.fixture(autouse=True)
def _lookups(db):
    """Seed the lookup rows the services resolve by key."""
    for key in (
        "backlog",
        "todo",
        "wip",
        "done",
    ):
        kf.make_status(key)
    kf.make_priority("medium")
    kf.make_relative_size("s", order=1)
    kf.make_section("scope")
    kf.make_card_reference_kind("dependency")
    kf.make_card_reference_kind("related")
    kf.make_actor("maintainer")
    kf.make_attempt_outcome("succeeded")
    kf.make_verification_kind("manual")


def _card_gid(card: models.Card) -> str:
    return str(relay.GlobalID(type_name=models.Card._meta.label_lower, node_id=str(card.pk)))


def _run(
    schema,
    context,
    document,
    variables,
):
    return schema.execute_sync(document, variable_values=variables, context_value=context)


_SET_STATUS = (
    "mutation($d: SetCardStatusFormInput!) { setCardStatus(data: $d) "
    "{ ok errors { field messages codes } } }"
)


@pytest.mark.django_db
def test_set_card_status_happy_path_writes_transition(project_schema, staff_context):
    card = kf.make_card(status=kf.make_status("todo"))

    result = _run(
        project_schema,
        staff_context,
        _SET_STATUS,
        {"d": {"cardId": _card_gid(card), "statusKey": "wip", "actorKey": "maintainer"}},
    )

    assert result.errors is None, result.errors
    assert result.data["setCardStatus"] == {"ok": True, "errors": []}
    card.refresh_from_db()
    assert card.status.key == "wip"
    assert card.transitions.filter(to_status__key="wip").exists()


@pytest.mark.django_db
def test_set_card_status_illegal_transition_maps_validation_error(project_schema, staff_context):
    # todo -> done is not an allowed transition (the 2F state-machine guard raises
    # a Django ``ValidationError``); it must surface in the envelope, not as a
    # top-level GraphQL error, and the card must stay put.
    card = kf.make_card(status=kf.make_status("todo"))

    result = _run(
        project_schema,
        staff_context,
        _SET_STATUS,
        {"d": {"cardId": _card_gid(card), "statusKey": "done", "actorKey": "maintainer"}},
    )

    assert result.errors is None, result.errors
    payload = result.data["setCardStatus"]
    assert payload["ok"] is False
    assert payload["errors"], payload
    assert "Illegal kanban card status transition" in payload["errors"][0]["messages"][0]
    card.refresh_from_db()
    assert card.status.key == "todo"


@pytest.mark.django_db
def test_set_card_status_unknown_lookup_carries_service_code(project_schema, staff_context):
    card = kf.make_card(status=kf.make_status("todo"))

    result = _run(
        project_schema,
        staff_context,
        _SET_STATUS,
        {"d": {"cardId": _card_gid(card), "statusKey": "nope", "actorKey": "maintainer"}},
    )

    assert result.errors is None, result.errors
    payload = result.data["setCardStatus"]
    assert payload["ok"] is False
    assert payload["errors"][0]["codes"] == ["unknown_lookup"]
    assert payload["errors"][0]["field"] == "__all__"


@pytest.mark.django_db
def test_set_card_status_permission_denied_without_staff(project_schema):
    # No request in context -> no user -> IsStaffUser denies; the framework maps a
    # denied write to a top-level GraphQL error (never the envelope).
    card = kf.make_card(status=kf.make_status("todo"))

    result = project_schema.execute_sync(
        _SET_STATUS,
        variable_values={
            "d": {"cardId": _card_gid(card), "statusKey": "wip", "actorKey": "maintainer"},
        },
    )

    assert result.errors, "an unauthorized write must raise a top-level error"
    card.refresh_from_db()
    assert card.status.key == "todo"


@pytest.mark.django_db
def test_create_card_from_spec_creates_card(project_schema, staff_context):
    version = kf.make_target_version("9.9.9")

    result = _run(
        project_schema,
        staff_context,
        "mutation($d: CreateCardFromSpecFormInput!) { createCardFromSpec(data: $d) "
        "{ ok errors { field messages } } }",
        {
            "d": {
                "title": "Wired card",
                "targetVersion": version.number,
                "relativeSize": "s",
                "priority": "medium",
            },
        },
    )

    assert result.errors is None, result.errors
    assert result.data["createCardFromSpec"] == {"ok": True, "errors": []}
    assert models.Card.objects.filter(title="Wired card").exists()


@pytest.mark.django_db
def test_move_card_number_out_of_range_maps_service_code(project_schema, staff_context):
    kf.make_card(number=1)
    card = kf.make_card(number=2)

    result = _run(
        project_schema,
        staff_context,
        "mutation($d: MoveCardNumberFormInput!) { moveCardNumber(data: $d) "
        "{ ok errors { field messages codes } } }",
        {"d": {"cardId": _card_gid(card), "number": 99}},
    )

    assert result.errors is None, result.errors
    payload = result.data["moveCardNumber"]
    assert payload["ok"] is False
    assert payload["errors"][0]["codes"] == ["card_number_out_of_range"]


@pytest.mark.django_db
def test_add_and_remove_dependency(project_schema, staff_context):
    dependency = kf.make_card(number=1)
    dependent = kf.make_card(number=2)

    add = _run(
        project_schema,
        staff_context,
        "mutation($d: AddDependencyFormInput!) { addDependency(data: $d) { ok errors { field } } }",
        {"d": {"sourceCardId": _card_gid(dependent), "targetCardId": _card_gid(dependency)}},
    )
    assert add.errors is None, add.errors
    assert add.data["addDependency"]["ok"] is True
    assert models.CardReference.objects.filter(
        source_card=dependent,
        target_card=dependency,
        kind__key="dependency",
    ).exists()

    remove = _run(
        project_schema,
        staff_context,
        "mutation($d: RemoveDependencyFormInput!) { removeDependency(data: $d) "
        "{ ok errors { field } } }",
        {"d": {"sourceCardId": _card_gid(dependent), "targetCardId": _card_gid(dependency)}},
    )
    assert remove.errors is None, remove.errors
    assert remove.data["removeDependency"]["ok"] is True
    assert not models.CardReference.objects.filter(
        source_card=dependent,
        target_card=dependency,
    ).exists()


@pytest.mark.django_db
def test_verify_card_item_stamps_verification(project_schema, staff_context):
    item = kf.make_card_item(section=kf.make_section("scope"))

    result = _run(
        project_schema,
        staff_context,
        "mutation($d: VerifyCardItemFormInput!) { verifyCardItem(data: $d) "
        "{ ok errors { field } } }",
        {"d": {"itemId": item.pk, "actorKey": "maintainer", "kindKey": "manual"}},
    )

    assert result.errors is None, result.errors
    assert result.data["verifyCardItem"]["ok"] is True
    item.refresh_from_db()
    assert item.is_complete is True
    assert item.verified_at is not None
    assert item.verification_kind.key == "manual"


@pytest.mark.django_db
def test_record_and_finish_work_attempt(project_schema, staff_context):
    card = kf.make_card()

    opened = _run(
        project_schema,
        staff_context,
        "mutation($d: RecordWorkAttemptFormInput!) { recordWorkAttempt(data: $d) "
        "{ ok errors { field } } }",
        {"d": {"cardId": _card_gid(card), "actorKey": "maintainer", "summary": "try one"}},
    )
    assert opened.errors is None, opened.errors
    assert opened.data["recordWorkAttempt"]["ok"] is True
    attempt = models.WorkAttempt.objects.get(card=card)
    assert attempt.outcome_id is None

    finished = _run(
        project_schema,
        staff_context,
        "mutation($d: FinishWorkAttemptFormInput!) { finishWorkAttempt(data: $d) "
        "{ ok errors { field } } }",
        {"d": {"attemptId": attempt.pk, "outcomeKey": "succeeded"}},
    )
    assert finished.errors is None, finished.errors
    assert finished.data["finishWorkAttempt"]["ok"] is True
    attempt.refresh_from_db()
    assert attempt.outcome.key == "succeeded"
    assert attempt.ended_at is not None


@pytest.mark.django_db
def test_record_decision_board_level(project_schema, staff_context):
    result = _run(
        project_schema,
        staff_context,
        "mutation($d: RecordDecisionFormInput!) { recordDecision(data: $d) "
        "{ ok errors { field } } }",
        {"d": {"actorKey": "maintainer", "question": "Ship it?", "choice": "yes"}},
    )

    assert result.errors is None, result.errors
    assert result.data["recordDecision"]["ok"] is True
    assert models.Decision.objects.filter(question="Ship it?", card__isnull=True).exists()


@pytest.mark.django_db
def test_set_card_files_predicted_and_invalid_root(project_schema, staff_context):
    card = kf.make_card(status=kf.make_status("todo"))
    path = "django_strawberry_framework/mutations_ws3b_probe.py"

    ok = _run(
        project_schema,
        staff_context,
        "mutation($d: SetCardFilesFormInput!) { setCardFiles(data: $d) { ok errors { field } } }",
        {"d": {"cardId": _card_gid(card), "kind": "predicted", "paths": [path]}},
    )
    assert ok.errors is None, ok.errors
    assert ok.data["setCardFiles"]["ok"] is True
    assert card.path_links.filter(path__path=path, kind="predicted").exists()

    bad = _run(
        project_schema,
        staff_context,
        "mutation($d: SetCardFilesFormInput!) { setCardFiles(data: $d) "
        "{ ok errors { field messages codes } } }",
        {"d": {"cardId": _card_gid(card), "kind": "predicted", "paths": ["outside/root/foo.py"]}},
    )
    assert bad.errors is None, bad.errors
    payload = bad.data["setCardFiles"]
    assert payload["ok"] is False
    assert payload["errors"][0]["codes"] == ["tracked_path_outside_roots"]
