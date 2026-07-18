"""Tests for the Phase 2 work-tracking dimension.

Covers the status state machine (``services.set_card_status`` + the signal
guard), ``CardTransition`` logging, the ``WorkAttempt`` lifecycle, ``Decision``
supersession, ``CardItem`` verification fields, the 2G ``blocked_by``
``resolved_at`` hook, and the ``Card.is_ready`` derivation (2H).
"""

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.kanban import factories as kf
from apps.kanban import models, services


@pytest.fixture(autouse=True)
def _worklog_lookups(db):
    kf.make_status("backlog")
    kf.make_status("todo")
    kf.make_status("wip")
    kf.make_status("done")
    kf.make_card_reference_kind("dependency")
    kf.make_card_reference_kind("blocked_by")


# ---------------------------------------------------------------------------
# 2F: status state machine + CardTransition logging
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_set_card_status_records_transition():
    actor = kf.make_actor()
    card = kf.make_card(status=kf.make_status("todo"))

    transition = services.set_card_status(card, "wip", actor=actor, note="starting")

    card.refresh_from_db()
    assert card.status.key == "wip"
    assert transition.from_status.key == "todo"
    assert transition.to_status.key == "wip"
    assert transition.actor == actor
    assert transition.note == "starting"
    assert list(card.transitions.values_list("to_status__key", flat=True)) == ["wip"]


@pytest.mark.django_db
def test_set_card_status_accepts_actor_key():
    kf.make_actor("maintainer")
    card = kf.make_card(status=kf.make_status("todo"))

    transition = services.set_card_status(card, "wip", actor="maintainer")

    assert transition.actor.key == "maintainer"


@pytest.mark.django_db
def test_set_card_status_illegal_transition_raises_and_writes_nothing():
    actor = kf.make_actor()
    card = kf.make_card(status=kf.make_status("todo"))

    with pytest.raises(ValidationError, match="Illegal kanban card status transition"):
        services.set_card_status(card, "done", actor=actor)

    card.refresh_from_db()
    assert card.status.key == "todo"
    assert not card.transitions.exists()


@pytest.mark.django_db
def test_set_card_status_rejects_no_op():
    actor = kf.make_actor()
    card = kf.make_card(status=kf.make_status("todo"))

    with pytest.raises(services.KanbanServiceError, match="already in status"):
        services.set_card_status(card, "todo", actor=actor)


@pytest.mark.django_db
def test_signal_guard_rejects_illegal_direct_status_write():
    card = kf.make_card(status=kf.make_status("todo"))

    card.status = kf.make_status("done")
    with pytest.raises(ValidationError, match="Illegal kanban card status transition"):
        card.save(update_fields=["status"])


@pytest.mark.django_db
def test_reopen_transition_is_allowed():
    actor = kf.make_actor()
    card = kf.make_card(status=kf.make_status("done"))

    transition = services.set_card_status(card, "todo", actor=actor)

    assert transition.from_status.key == "done"
    assert transition.to_status.key == "todo"


# ---------------------------------------------------------------------------
# 2B: WorkAttempt lifecycle
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_work_attempt_lifecycle():
    card = kf.make_card()
    attempt = kf.make_work_attempt(card=card, summary="first try")

    assert attempt.outcome is None
    assert attempt.ended_at is None

    attempt.outcome = kf.make_attempt_outcome("succeeded")
    attempt.ended_at = timezone.now()
    attempt.save(update_fields=["outcome", "ended_at"])
    attempt.refresh_from_db()

    assert attempt.outcome.key == "succeeded"
    assert attempt.ended_at is not None
    assert attempt.uuid is not None


# ---------------------------------------------------------------------------
# 2C: Decision supersession
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_decision_supersedes_chain():
    first = kf.make_decision(card=None, question="Use signals?", choice="Yes")
    second = kf.make_decision(
        card=None,
        question="Use signals?",
        choice="No, services",
        supersedes=first,
    )

    assert first.card is None
    assert second.supersedes == first
    assert list(first.superseded_by_set.all()) == [second]


# ---------------------------------------------------------------------------
# 2E: CardItem verification fields
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_card_item_verification_fields():
    item = kf.make_card_item()
    assert item.verified_at is None
    assert item.verified_by is None
    assert item.verification_kind is None

    actor = kf.make_actor()
    kind = kf.make_verification_kind("coverage_gate")
    item.verified_at = timezone.now()
    item.verified_by = actor
    item.verification_kind = kind
    item.save(update_fields=["verified_at", "verified_by", "verification_kind"])
    item.refresh_from_db()

    assert item.verified_at is not None
    assert item.verified_by == actor
    assert item.verification_kind.key == "coverage_gate"


# ---------------------------------------------------------------------------
# 2G: blocked_by resolved_at on done-flip + is_blocked respects it
# ---------------------------------------------------------------------------


def _make_done(card, actor):
    """Satisfy the done-card guards (spec + glossary) then flip wip -> done."""
    kf.make_spec_doc(card=card)
    kf.make_card_glossary_term(card=card)
    services.set_card_status(card, "wip", actor=actor)
    services.set_card_status(card, "done", actor=actor)


def _blocked_pair():
    """A source card blocked_by a target card (source.number > target.number)."""
    target = kf.make_card(number=1, title="Blocking target", status=kf.make_status("todo"))
    source = kf.make_card(number=2, title="Blocked source", status=kf.make_status("todo"))
    reference = models.CardReference.objects.create(
        source_card=source,
        target_card=target,
        kind=kf.make_card_reference_kind("blocked_by"),
    )
    return source, target, reference


@pytest.mark.django_db
def test_done_flip_resolves_incoming_blocked_by_reference():
    source, target, reference = _blocked_pair()
    source.refresh_from_db()
    assert source.is_blocked is True

    _make_done(target, kf.make_actor())

    reference.refresh_from_db()
    assert reference.resolved_at is not None
    source.refresh_from_db()
    assert source.is_blocked is False


@pytest.mark.django_db
def test_reopen_unresolves_incoming_blocked_by_reference():
    source, target, reference = _blocked_pair()
    actor = kf.make_actor()
    _make_done(target, actor)
    source.refresh_from_db()
    assert source.is_blocked is False

    services.set_card_status(target, "todo", actor=actor)

    reference.refresh_from_db()
    assert reference.resolved_at is None
    source.refresh_from_db()
    assert source.is_blocked is True


@pytest.mark.django_db
def test_is_blocked_respects_resolved_at_even_when_target_not_done():
    source, _target, reference = _blocked_pair()
    source.refresh_from_db()
    assert source.is_blocked is True

    reference.resolved_at = timezone.now()
    reference.save(update_fields=["resolved_at"])

    source.refresh_from_db()
    assert source.is_blocked is False


# ---------------------------------------------------------------------------
# 2H: is_ready derivation
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_is_ready_true_for_unblocked_todo_card():
    card = kf.make_card(status=kf.make_status("todo"))
    assert card.is_ready is True


@pytest.mark.django_db
def test_is_ready_false_for_non_todo_card():
    card = kf.make_card(status=kf.make_status("wip"))
    assert card.is_ready is False


@pytest.mark.django_db
def test_is_ready_false_with_undone_dependency():
    dependency = kf.make_card(number=1, title="Dep", status=kf.make_status("todo"))
    dependent = kf.make_card(number=2, title="Waiting", status=kf.make_status("todo"))
    models.CardReference.objects.create(
        source_card=dependent,
        target_card=dependency,
        kind=kf.make_card_reference_kind("dependency"),
    )

    dependent.refresh_from_db()
    assert dependent.is_ready is False

    _make_done(dependency, kf.make_actor())
    dependent.refresh_from_db()
    assert dependent.is_ready is True


@pytest.mark.django_db
def test_is_ready_false_when_blocked():
    source, _target, _reference = _blocked_pair()
    source.refresh_from_db()
    assert source.is_blocked is True
    assert source.is_ready is False


# ---------------------------------------------------------------------------
# Sanctioned CardItem writers: set_item_complete / verify_item
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_set_item_complete_round_trip():
    item = kf.make_card_item()
    assert item.is_complete is False

    services.set_item_complete(item)
    item.refresh_from_db()
    assert item.is_complete is True

    services.set_item_complete(item, False)
    item.refresh_from_db()
    assert item.is_complete is False


@pytest.mark.django_db
def test_verify_item_stamps_provenance_and_completes():
    item = kf.make_card_item()
    actor = kf.make_actor()
    kf.make_verification_kind("test_run")

    services.verify_item(item, actor=actor, kind="test_run")

    item.refresh_from_db()
    assert item.is_complete is True
    assert item.verified_at is not None
    assert item.verified_by == actor
    assert item.verification_kind.key == "test_run"


@pytest.mark.django_db
def test_verify_item_accepts_instances_and_explicit_timestamp():
    item = kf.make_card_item()
    actor = kf.make_actor("agent-session", kind=models.ACTOR_AGENT)
    kind = kf.make_verification_kind("manual")
    at = timezone.now()

    services.verify_item(item, actor=actor, kind=kind, at=at)

    item.refresh_from_db()
    assert item.verified_at == at
    assert item.verification_kind == kind


@pytest.mark.django_db
def test_verify_item_rejects_unknown_kind():
    item = kf.make_card_item()

    with pytest.raises(services.KanbanServiceError) as excinfo:
        services.verify_item(item, actor=kf.make_actor(), kind="vibes")
    assert excinfo.value.code == "unknown_lookup"


@pytest.mark.django_db
def test_verify_item_rejects_missing_actor():
    item = kf.make_card_item()
    kf.make_verification_kind("test_run")

    with pytest.raises(services.KanbanServiceError) as excinfo:
        services.verify_item(item, actor=None, kind="test_run")
    assert excinfo.value.code == "invalid_actor"


# ---------------------------------------------------------------------------
# Sanctioned work-tracking writers: record_attempt / finish_attempt / record_decision
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_record_and_finish_attempt():
    card = kf.make_card()
    actor = kf.make_actor()
    kf.make_attempt_outcome("succeeded")

    attempt = services.record_attempt(card, actor=actor, summary="try one", evidence="log")

    assert attempt.card == card
    assert attempt.actor == actor
    assert attempt.summary == "try one"
    assert attempt.evidence == "log"
    assert attempt.outcome is None
    assert attempt.ended_at is None
    assert attempt.started_at is not None

    finished = services.finish_attempt(attempt, outcome_key="succeeded", summary="it worked")

    finished.refresh_from_db()
    assert finished.outcome.key == "succeeded"
    assert finished.ended_at is not None
    assert finished.summary == "it worked"


@pytest.mark.django_db
def test_record_attempt_accepts_actor_key_and_started_at():
    kf.make_actor("agent-1", kind=models.ACTOR_AGENT)
    started = timezone.now()

    attempt = services.record_attempt(
        kf.make_card(),
        actor="agent-1",
        summary="resumed",
        started_at=started,
    )

    assert attempt.actor.key == "agent-1"
    assert attempt.started_at == started


@pytest.mark.django_db
def test_finish_attempt_keeps_summary_and_accepts_explicit_end():
    attempt = kf.make_work_attempt(summary="original")
    kf.make_attempt_outcome("failed")
    ended = timezone.now()

    services.finish_attempt(attempt, outcome_key="failed", ended_at=ended)

    attempt.refresh_from_db()
    assert attempt.summary == "original"
    assert attempt.ended_at == ended
    assert attempt.outcome.key == "failed"


@pytest.mark.django_db
def test_finish_attempt_rejects_unknown_outcome():
    attempt = kf.make_work_attempt()

    with pytest.raises(services.KanbanServiceError) as excinfo:
        services.finish_attempt(attempt, outcome_key="shrugged")
    assert excinfo.value.code == "unknown_lookup"


@pytest.mark.django_db
def test_record_decision_board_level_and_supersession():
    actor = kf.make_actor()

    first = services.record_decision(
        actor=actor,
        question="Signals or services?",
        choice="Signals",
    )
    second = services.record_decision(
        actor=actor,
        question="Signals or services?",
        choice="Services",
        rationale="Signals cannot log transitions.",
        supersedes=first,
    )

    assert first.card is None
    assert second.supersedes == first
    assert second.rationale == "Signals cannot log transitions."
    assert list(first.superseded_by_set.all()) == [second]


@pytest.mark.django_db
def test_record_decision_scoped_to_card():
    card = kf.make_card()

    decision = services.record_decision(
        actor=kf.make_actor(),
        question="Scope?",
        choice="Just this card",
        card=card,
    )

    assert decision.card == card
    assert decision.decided_at is not None
    assert decision.uuid is not None
