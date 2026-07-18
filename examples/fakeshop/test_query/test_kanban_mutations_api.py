"""Live GraphQL HTTP tests for the kanban write surface (WS-3B).

Exercises every kanban mutation over a real ``/graphql/`` request per the
``test_query/README.md`` live-first mandate: each mutation gets a happy path plus a
representative failure path across the three failure classes the surface must map
(illegal status transition, unknown lookup, permission denied). Writes are staff-only
(``IsStaffUser``), so the happy paths log in a staff user via ``force_login`` (the
``test_library_api`` / ``test_products_api`` idiom); the permission-denied path posts
anonymously and asserts a top-level GraphQL error with no board mutation.
"""

from __future__ import annotations

import pytest
from apps.kanban import factories as kf
from apps.kanban import models
from django.contrib.auth import get_user_model
from django.test import Client
from graphql_client import post_graphql as _post_graphql
from strawberry import relay


@pytest.fixture(autouse=True)
def _lookups(db):
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


def _staff_client() -> Client:
    user = get_user_model().objects.create_user(
        username="staff_agent",
        password="pw",
        is_staff=True,
    )
    client = Client()
    client.force_login(user)
    return client


def _card_gid(card: models.Card) -> str:
    return str(relay.GlobalID(type_name=models.Card._meta.label_lower, node_id=str(card.pk)))


def _run(query: str, variables: dict, *, client: Client) -> dict:
    """POST a mutation and return the parsed payload (top-level and envelope both readable)."""
    response = _post_graphql(query, client=client, variables=variables)
    assert response.status_code == 200
    return response.json()


_SET_STATUS = (
    "mutation($d: SetCardStatusFormInput!) { setCardStatus(data: $d) "
    "{ ok errors { field messages codes } } }"
)


@pytest.mark.django_db
def test_set_card_status_happy_path():
    card = kf.make_card(status=kf.make_status("todo"))
    client = _staff_client()

    payload = _run(
        _SET_STATUS,
        {"d": {"cardId": _card_gid(card), "statusKey": "wip", "actorKey": "maintainer"}},
        client=client,
    )

    assert "errors" not in payload, payload
    assert payload["data"]["setCardStatus"] == {"ok": True, "errors": []}
    card.refresh_from_db()
    assert card.status.key == "wip"


@pytest.mark.django_db
def test_set_card_status_illegal_transition_returns_envelope():
    card = kf.make_card(status=kf.make_status("todo"))
    client = _staff_client()

    payload = _run(
        _SET_STATUS,
        {"d": {"cardId": _card_gid(card), "statusKey": "done", "actorKey": "maintainer"}},
        client=client,
    )

    assert "errors" not in payload, payload
    envelope = payload["data"]["setCardStatus"]
    assert envelope["ok"] is False
    assert "Illegal kanban card status transition" in envelope["errors"][0]["messages"][0]
    card.refresh_from_db()
    assert card.status.key == "todo"


@pytest.mark.django_db
def test_set_card_status_permission_denied_anonymous():
    card = kf.make_card(status=kf.make_status("todo"))

    payload = _run(
        _SET_STATUS,
        {"d": {"cardId": _card_gid(card), "statusKey": "wip", "actorKey": "maintainer"}},
        client=Client(),
    )

    assert payload.get("errors"), payload
    card.refresh_from_db()
    assert card.status.key == "todo"


@pytest.mark.django_db
def test_create_card_from_spec_happy_path():
    version = kf.make_target_version("9.9.9")
    client = _staff_client()

    payload = _run(
        "mutation($d: CreateCardFromSpecFormInput!) { createCardFromSpec(data: $d) "
        "{ ok errors { field messages } } }",
        {
            "d": {
                "title": "Live card",
                "targetVersion": version.number,
                "relativeSize": "s",
                "priority": "medium",
            },
        },
        client=client,
    )

    assert "errors" not in payload, payload
    assert payload["data"]["createCardFromSpec"]["ok"] is True
    assert models.Card.objects.filter(title="Live card").exists()


@pytest.mark.django_db
def test_create_card_from_spec_duplicate_title_envelope():
    version = kf.make_target_version("9.9.9")
    kf.make_card(title="Dup card")
    client = _staff_client()

    payload = _run(
        "mutation($d: CreateCardFromSpecFormInput!) { createCardFromSpec(data: $d) "
        "{ ok errors { field messages codes } } }",
        {
            "d": {"title": "Dup card", "targetVersion": version.number, "relativeSize": "s"},
        },
        client=client,
    )

    assert "errors" not in payload, payload
    envelope = payload["data"]["createCardFromSpec"]
    assert envelope["ok"] is False
    assert envelope["errors"][0]["codes"] == ["duplicate_card_title"]


@pytest.mark.django_db
def test_move_card_number_happy_path():
    kf.make_card(number=1)
    card = kf.make_card(number=2)
    kf.make_card(number=3)
    client = _staff_client()

    payload = _run(
        "mutation($d: MoveCardNumberFormInput!) { moveCardNumber(data: $d) "
        "{ ok errors { field codes } } }",
        {"d": {"cardId": _card_gid(card), "number": 1}},
        client=client,
    )

    assert "errors" not in payload, payload
    assert payload["data"]["moveCardNumber"]["ok"] is True
    card.refresh_from_db()
    assert card.number == 1


@pytest.mark.django_db
def test_move_card_number_out_of_range_envelope():
    card = kf.make_card(number=1)
    client = _staff_client()

    payload = _run(
        "mutation($d: MoveCardNumberFormInput!) { moveCardNumber(data: $d) "
        "{ ok errors { field codes } } }",
        {"d": {"cardId": _card_gid(card), "number": 99}},
        client=client,
    )

    envelope = payload["data"]["moveCardNumber"]
    assert envelope["ok"] is False
    assert envelope["errors"][0]["codes"] == ["card_number_out_of_range"]


@pytest.mark.django_db
def test_add_dependency_happy_path():
    dependency = kf.make_card(number=1)
    dependent = kf.make_card(number=2)
    client = _staff_client()

    payload = _run(
        "mutation($d: AddDependencyFormInput!) { addDependency(data: $d) { ok errors { field } } }",
        {"d": {"sourceCardId": _card_gid(dependent), "targetCardId": _card_gid(dependency)}},
        client=client,
    )

    assert "errors" not in payload, payload
    assert payload["data"]["addDependency"]["ok"] is True
    assert models.CardReference.objects.filter(
        source_card=dependent,
        target_card=dependency,
        kind__key="dependency",
    ).exists()


@pytest.mark.django_db
def test_add_dependency_invalid_kind_envelope():
    dependency = kf.make_card(number=1)
    dependent = kf.make_card(number=2)
    client = _staff_client()

    payload = _run(
        "mutation($d: AddDependencyFormInput!) { addDependency(data: $d) "
        "{ ok errors { field codes } } }",
        {
            "d": {
                "sourceCardId": _card_gid(dependent),
                "targetCardId": _card_gid(dependency),
                "kind": "related",
            },
        },
        client=client,
    )

    envelope = payload["data"]["addDependency"]
    assert envelope["ok"] is False
    assert envelope["errors"][0]["codes"] == ["invalid_dependency_kind"]


@pytest.mark.django_db
def test_remove_dependency_happy_path():
    dependency = kf.make_card(number=1)
    dependent = kf.make_card(number=2)
    kf.make_card_reference(
        source_card=dependent,
        target_card=dependency,
        kind=kf.make_card_reference_kind("dependency"),
    )
    client = _staff_client()

    payload = _run(
        "mutation($d: RemoveDependencyFormInput!) { removeDependency(data: $d) "
        "{ ok errors { field } } }",
        {"d": {"sourceCardId": _card_gid(dependent), "targetCardId": _card_gid(dependency)}},
        client=client,
    )

    assert "errors" not in payload, payload
    assert payload["data"]["removeDependency"]["ok"] is True
    assert not models.CardReference.objects.filter(
        source_card=dependent,
        target_card=dependency,
    ).exists()


@pytest.mark.django_db
def test_set_card_item_complete_happy_path():
    item = kf.make_card_item(section=kf.make_section("scope"), is_complete=False)
    client = _staff_client()

    payload = _run(
        "mutation($d: SetCardItemCompleteFormInput!) { setCardItemComplete(data: $d) "
        "{ ok errors { field } } }",
        {"d": {"itemId": item.pk, "complete": True}},
        client=client,
    )

    assert "errors" not in payload, payload
    assert payload["data"]["setCardItemComplete"]["ok"] is True
    item.refresh_from_db()
    assert item.is_complete is True


@pytest.mark.django_db
def test_verify_card_item_happy_path():
    item = kf.make_card_item(section=kf.make_section("scope"))
    client = _staff_client()

    payload = _run(
        "mutation($d: VerifyCardItemFormInput!) { verifyCardItem(data: $d) "
        "{ ok errors { field } } }",
        {"d": {"itemId": item.pk, "actorKey": "maintainer", "kindKey": "manual"}},
        client=client,
    )

    assert "errors" not in payload, payload
    assert payload["data"]["verifyCardItem"]["ok"] is True
    item.refresh_from_db()
    assert item.verified_at is not None
    assert item.verification_kind.key == "manual"


@pytest.mark.django_db
def test_verify_card_item_unknown_kind_envelope():
    item = kf.make_card_item(section=kf.make_section("scope"))
    client = _staff_client()

    payload = _run(
        "mutation($d: VerifyCardItemFormInput!) { verifyCardItem(data: $d) "
        "{ ok errors { field codes } } }",
        {"d": {"itemId": item.pk, "actorKey": "maintainer", "kindKey": "nope"}},
        client=client,
    )

    envelope = payload["data"]["verifyCardItem"]
    assert envelope["ok"] is False
    assert envelope["errors"][0]["codes"] == ["unknown_lookup"]


@pytest.mark.django_db
def test_record_and_finish_work_attempt_happy_path():
    card = kf.make_card()
    client = _staff_client()

    opened = _run(
        "mutation($d: RecordWorkAttemptFormInput!) { recordWorkAttempt(data: $d) "
        "{ ok errors { field } } }",
        {"d": {"cardId": _card_gid(card), "actorKey": "maintainer", "summary": "attempt"}},
        client=client,
    )
    assert "errors" not in opened, opened
    assert opened["data"]["recordWorkAttempt"]["ok"] is True
    attempt = models.WorkAttempt.objects.get(card=card)

    finished = _run(
        "mutation($d: FinishWorkAttemptFormInput!) { finishWorkAttempt(data: $d) "
        "{ ok errors { field } } }",
        {"d": {"attemptId": attempt.pk, "outcomeKey": "succeeded"}},
        client=client,
    )
    assert "errors" not in finished, finished
    assert finished["data"]["finishWorkAttempt"]["ok"] is True
    attempt.refresh_from_db()
    assert attempt.outcome.key == "succeeded"


@pytest.mark.django_db
def test_finish_work_attempt_unknown_outcome_envelope():
    attempt = kf.make_work_attempt(card=kf.make_card(), actor=kf.make_actor("maintainer"))
    client = _staff_client()

    payload = _run(
        "mutation($d: FinishWorkAttemptFormInput!) { finishWorkAttempt(data: $d) "
        "{ ok errors { field codes } } }",
        {"d": {"attemptId": attempt.pk, "outcomeKey": "nope"}},
        client=client,
    )

    envelope = payload["data"]["finishWorkAttempt"]
    assert envelope["ok"] is False
    assert envelope["errors"][0]["codes"] == ["unknown_lookup"]


@pytest.mark.django_db
def test_record_decision_happy_path():
    client = _staff_client()

    payload = _run(
        "mutation($d: RecordDecisionFormInput!) { recordDecision(data: $d) "
        "{ ok errors { field } } }",
        {"d": {"actorKey": "maintainer", "question": "Ship?", "choice": "yes"}},
        client=client,
    )

    assert "errors" not in payload, payload
    assert payload["data"]["recordDecision"]["ok"] is True
    assert models.Decision.objects.filter(question="Ship?").exists()


@pytest.mark.django_db
def test_set_card_files_predicted_happy_path():
    card = kf.make_card(status=kf.make_status("todo"))
    path = "django_strawberry_framework/mutations_ws3b_live_probe.py"
    client = _staff_client()

    payload = _run(
        "mutation($d: SetCardFilesFormInput!) { setCardFiles(data: $d) { ok errors { field } } }",
        {"d": {"cardId": _card_gid(card), "kind": "predicted", "paths": [path]}},
        client=client,
    )

    assert "errors" not in payload, payload
    assert payload["data"]["setCardFiles"]["ok"] is True
    assert card.path_links.filter(path__path=path, kind="predicted").exists()


@pytest.mark.django_db
def test_set_card_files_outside_root_envelope():
    card = kf.make_card(status=kf.make_status("todo"))
    client = _staff_client()

    payload = _run(
        "mutation($d: SetCardFilesFormInput!) { setCardFiles(data: $d) "
        "{ ok errors { field codes } } }",
        {"d": {"cardId": _card_gid(card), "kind": "predicted", "paths": ["outside/root/foo.py"]}},
        client=client,
    )

    envelope = payload["data"]["setCardFiles"]
    assert envelope["ok"] is False
    assert envelope["errors"][0]["codes"] == ["tracked_path_outside_roots"]
