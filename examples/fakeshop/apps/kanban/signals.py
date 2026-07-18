"""Kanban signal receivers: guards + side-table wiring only.

``apps.kanban.services`` is the sanctioned write API (card creation, status and
board-number moves, dependency edges, work tracking). The receivers here do not
mutate board state beyond the automatic bits that must ride along with a write:

* **Raise-only guards** -- reject illegal status transitions, direct board-number
  edits (pointing the caller at ``services.move_card_number``), reference cycles
  / dependency mis-ordering, and done-card spec/glossary invariants -- so a
  direct ORM ``save()`` that bypasses the service layer still cannot corrupt an
  invariant.
* **The new-card board-number assignment** -- validating and shifting neighbours
  when a card is *created* at an occupied slot (the create path stays first-class;
  only *moves* of an existing card are delegated to the service).
* **UUID side-row creation** -- the ``post_save`` / ``m2m_changed`` wiring that
  materializes each linked row's ``UUIDModel`` registry entry.
* **Delete-compaction** -- delegated to ``services.compact_card_numbers``.
"""

from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Count, Max
from django.db.models.signals import (
    m2m_changed,
    post_delete,
    post_save,
    pre_delete,
    pre_save,
)
from django.dispatch import receiver

from apps.kanban import models

DONE_STATUS_KEY = models.DONE_STATUS_KEY
DONE_CARD_SPEC_ERROR = "Done kanban cards require a linked spec doc."
DONE_CARD_GLOSSARY_ERROR = "Done kanban cards require at least one glossary link."
SPEC_CARD_REQUIRED_ERROR = "Kanban spec docs must be linked to a card."
DONE_CARD_SPEC_REASSIGN_ERROR = "Cannot move a spec doc away from a done kanban card."
DONE_CARD_SPEC_DELETE_ERROR = "Cannot delete a spec doc linked to a done kanban card."
DONE_CARD_GLOSSARY_REASSIGN_ERROR = "Cannot move the last glossary link away from a done card."
DONE_CARD_GLOSSARY_DELETE_ERROR = "Cannot delete the last glossary link from a done card."
DEPENDENCY_REFERENCE_KIND_KEYS = models.DEPENDENCY_REFERENCE_KIND_KEYS
CARD_ORDER_REQUESTED_NUMBER_ATTR = "_kanban_requested_card_number"
CARD_NUMBER_REQUIRED_ERROR = "Kanban cards require a board number."
CARD_NUMBER_POSITIVE_ERROR = "Kanban card number must be at least 1."
CARD_NUMBER_RANGE_ERROR = "Kanban card number must be between 1 and {limit}."
CARD_NUMBER_MOVE_ERROR = (
    "Direct kanban card number edits are not allowed; use apps.kanban.services.move_card_number."
)
CARD_DEPENDENCY_ORDER_ERROR = "Kanban card dependencies must appear before dependent cards."

# The card status state machine (2F). Each tuple is an allowed
# ``(from_status_key, to_status_key)`` move; ``done -> todo`` is the reopen path.
# ``services.set_card_status`` is the sanctioned writer; this raise-only guard
# rejects illegal transitions from any write path (direct ORM or service).
STATUS_TRANSITIONS = frozenset(
    {
        ("backlog", "todo"),
        ("todo", "wip"),
        ("wip", "done"),
        ("wip", "todo"),
        ("todo", "backlog"),
        ("done", "todo"),
    },
)
CARD_STATUS_TRANSITION_ERROR = "Illegal kanban card status transition: {old} -> {new}."


UUID_LINKED_MODELS = (
    models.Milestone,
    models.Status,
    models.Priority,
    models.RelativeSize,
    models.Upstream,
    models.ParityLevel,
    models.Section,
    models.CardReferenceKind,
    models.BoardDocKind,
    models.TargetVersion,
    models.SpecDoc,
    models.TrackedPath,
    models.Card,
    models.CardReference,
    models.CardGlossaryTerm,
    models.ParityClaim,
    models.CardPathLink,
    models.CardItem,
    models.Label,
    models.BoardDoc,
    models.BoardDocCardReference,
    models.AttemptOutcome,
    models.VerificationKind,
    models.Actor,
    models.CardTransition,
    models.WorkAttempt,
    models.Decision,
)


# The alias-aware manager helper lives once in models.py (shared with services.py).
_manager = models.manager


def _status_is_done(status_id: int | None, using: str | None) -> bool:
    if status_id is None:
        return False
    return _manager(models.Status, using).filter(pk=status_id, key=DONE_STATUS_KEY).exists()


def _card_is_done(card_id: int | None, using: str | None) -> bool:
    if card_id is None:
        return False
    return _manager(models.Card, using).filter(pk=card_id, status__key=DONE_STATUS_KEY).exists()


def _card_has_spec(card: models.Card, using: str | None) -> bool:
    if card.pk is None:
        return False
    return _manager(models.SpecDoc, using).filter(card_id=card.pk).exists()


def _card_has_glossary_link(card: models.Card, using: str | None) -> bool:
    if card.pk is None:
        return False
    return _manager(models.CardGlossaryTerm, using).filter(card_id=card.pk).exists()


def _card_has_other_glossary_link(
    card_id: int | None,
    link_id: int | None,
    using: str | None,
) -> bool:
    if card_id is None:
        return False
    queryset = _manager(models.CardGlossaryTerm, using).filter(card_id=card_id)
    if link_id is not None:
        queryset = queryset.exclude(pk=link_id)
    return queryset.exists()


def _validate_done_card_has_spec(card: models.Card, using: str | None) -> None:
    if _status_is_done(card.status_id, using) and not _card_has_spec(card, using):
        raise ValidationError(DONE_CARD_SPEC_ERROR)


def _validate_done_card_has_glossary_link(card: models.Card, using: str | None) -> None:
    if _status_is_done(card.status_id, using) and not _card_has_glossary_link(card, using):
        raise ValidationError(DONE_CARD_GLOSSARY_ERROR)


def _delete_origin_is_card(origin) -> bool:
    return isinstance(origin, models.Card) or getattr(origin, "model", None) is models.Card


def _kind_is_dependency_reference(kind_id: int | None, using: str | None) -> bool:
    if kind_id is None:
        return False
    return (
        _manager(models.CardReferenceKind, using)
        .filter(pk=kind_id, key__in=DEPENDENCY_REFERENCE_KIND_KEYS)
        .exists()
    )


def _has_reference_path(
    start_card_id: int,
    target_card_id: int,
    using: str | None,
    *,
    exclude_reference_id: int | None = None,
) -> bool:
    seen: set[int] = set()
    frontier = {start_card_id}
    reference_manager = _manager(models.CardReference, using)
    reference_manager = reference_manager.filter(kind__key__in=DEPENDENCY_REFERENCE_KIND_KEYS)
    if exclude_reference_id is not None:
        reference_manager = reference_manager.exclude(pk=exclude_reference_id)
    while frontier:
        if target_card_id in frontier:
            return True
        seen.update(frontier)
        next_ids = set(
            reference_manager.filter(source_card_id__in=frontier).values_list(
                "target_card_id",
                flat=True,
            ),
        )
        frontier = next_ids - seen
    return False


def _stored_card_status_key(card_id: int, using: str | None) -> str | None:
    return (
        _manager(models.Card, using)
        .filter(pk=card_id)
        .values_list("status__key", flat=True)
        .first()
    )


def _validate_card_status_transition(
    instance: models.Card,
    update_fields: frozenset[str] | None,
    using: str | None,
) -> None:
    """Raise on an illegal status move (2F state machine).

    Only fires when an existing card's ``status`` actually changes. The OLD
    status is read from the DB (the same technique the number machinery uses),
    so the guard is independent of the in-memory instance state. New cards
    (``pk is None``) have no prior status and are not transitions -- a card may
    deliberately be born in any status (importers seed mid-flight cards; the
    done-card spec/glossary guards still apply to a born-``done`` card).
    """
    if instance.pk is None:
        return
    if update_fields is not None and "status" not in update_fields:
        return
    old_key = _stored_card_status_key(instance.pk, using)
    if old_key is None:
        return
    new_key = (
        _manager(models.Status, using)
        .filter(pk=instance.status_id)
        .values_list("key", flat=True)
        .first()
    )
    if new_key is None or new_key == old_key:
        return
    if (old_key, new_key) not in STATUS_TRANSITIONS:
        raise ValidationError(CARD_STATUS_TRANSITION_ERROR.format(old=old_key, new=new_key))


def _normalize_card_number(number: int | str | None) -> int:
    if number is None:
        raise ValidationError(CARD_NUMBER_REQUIRED_ERROR)
    try:
        return int(number)
    except (TypeError, ValueError):
        raise ValidationError(CARD_NUMBER_REQUIRED_ERROR) from None


def _card_number_state(using: str | None) -> tuple[int, bool]:
    state = _manager(models.Card, using).aggregate(
        count=Count("number"),
        max_number=Max("number"),
    )
    max_number = state["max_number"] or 0
    return max_number, max_number == 0 or state["count"] != max_number


def _stored_card_number(card_id: int, using: str | None) -> int | None:
    return _manager(models.Card, using).filter(pk=card_id).values_list("number", flat=True).first()


def _validate_card_number(number: int, *, limit: int | None = None) -> None:
    if number < 1:
        raise ValidationError(CARD_NUMBER_POSITIVE_ERROR)
    if limit is not None and number > limit:
        raise ValidationError(CARD_NUMBER_RANGE_ERROR.format(limit=limit))


def _validate_dependency_order(
    source_card_id: int,
    target_card_id: int,
    using: str | None,
) -> None:
    numbers = dict(
        _manager(models.Card, using)
        .filter(pk__in={source_card_id, target_card_id})
        .values_list("pk", "number"),
    )
    source_number = numbers.get(source_card_id)
    target_number = numbers.get(target_card_id)
    if source_number is None or target_number is None:
        return
    if source_number <= target_number:
        raise ValidationError(CARD_DEPENDENCY_ORDER_ERROR)


def _validate_reference_edge(
    source_card_id: int,
    target_card_id: int,
    kind_id: int | None,
    using: str | None,
    *,
    exclude_reference_id: int | None = None,
) -> None:
    if source_card_id == target_card_id:
        raise ValidationError("A kanban card reference cannot point at its own card.")
    if not _kind_is_dependency_reference(kind_id, using):
        return
    if _has_reference_path(
        target_card_id,
        source_card_id,
        using,
        exclude_reference_id=exclude_reference_id,
    ):
        raise ValidationError("Kanban card references cannot contain cycles.")
    _validate_dependency_order(source_card_id, target_card_id, using)


def _prepare_card_order(
    card: models.Card,
    update_fields: frozenset[str] | None,
    using: str | None,
) -> None:
    """Validate a card's board number on save; only the create path may assign one.

    New cards (no stored number yet) keep the first-class auto-append/insert
    behaviour: a number at an occupied slot parks the card above the sequence
    and flags it so :func:`sync_card_after_save` shifts the neighbours into
    place. Changing an EXISTING card's number via ``save()`` raises -- the
    renumbering engine lives in ``services.move_card_number`` (which shifts
    neighbours with per-row ``.update()`` so their ``updated_date`` and signals
    do not churn).
    """
    if update_fields is not None and "number" not in update_fields:
        return

    requested_number = _normalize_card_number(card.number)
    card.number = requested_number

    max_number, accepts_sparse_numbers = _card_number_state(using)
    old_number = None if card.pk is None else _stored_card_number(card.pk, using)
    if old_number is None:
        new_card_limit = None if accepts_sparse_numbers else max_number + 1
        _validate_card_number(requested_number, limit=new_card_limit)
        if requested_number <= max_number:
            setattr(card, CARD_ORDER_REQUESTED_NUMBER_ATTR, requested_number)
            card.number = max_number + 2
        return
    if requested_number == old_number:
        return
    raise ValidationError(CARD_NUMBER_MOVE_ERROR)


def _sync_card_order_after_insert(card: models.Card, using: str | None) -> None:
    """Shift neighbours up and settle a just-created card at its requested slot.

    Runs only for the create path (an existing card's number cannot change via
    ``save()``). Every shift is a per-row ``.update()``, so neighbour rows keep
    their ``updated_date`` and no ``Card`` signals fire for the shifts.
    """
    requested_number = getattr(card, CARD_ORDER_REQUESTED_NUMBER_ATTR, None)
    if requested_number is None:
        return

    card_manager = _manager(models.Card, using)
    try:
        with transaction.atomic(using=using):
            neighbors = list(
                card_manager.filter(number__gte=requested_number)
                .exclude(pk=card.pk)
                .order_by("-number")
                .values_list("pk", "number"),
            )
            for neighbor_pk, neighbor_number in neighbors:
                card_manager.filter(pk=neighbor_pk).update(number=neighbor_number + 1)
            card_manager.filter(pk=card.pk).update(number=requested_number)
            card.number = requested_number
    finally:
        delattr(card, CARD_ORDER_REQUESTED_NUMBER_ATTR)


@receiver(pre_save, sender=models.Card, dispatch_uid="kanban_prepare_card_save")
def prepare_card_save(
    sender,
    instance: models.Card,
    update_fields: frozenset[str] | None,
    using: str | None,
    **kwargs,
) -> None:
    _validate_card_status_transition(instance, update_fields, using)
    _validate_done_card_has_spec(instance, using)
    _validate_done_card_has_glossary_link(instance, using)
    _prepare_card_order(instance, update_fields, using)


@receiver(pre_save, sender=models.SpecDoc, dispatch_uid="kanban_validate_spec_doc_card")
def validate_spec_doc_card(
    sender,
    instance: models.SpecDoc,
    using: str | None,
    **kwargs,
) -> None:
    if instance.card_id is None:
        raise ValidationError(SPEC_CARD_REQUIRED_ERROR)
    if instance.pk is None:
        return
    old_card_id = (
        _manager(models.SpecDoc, using)
        .filter(pk=instance.pk)
        .values_list("card_id", flat=True)
        .first()
    )
    if old_card_id != instance.card_id and _card_is_done(old_card_id, using):
        raise ValidationError(DONE_CARD_SPEC_REASSIGN_ERROR)


@receiver(pre_delete, sender=models.SpecDoc, dispatch_uid="kanban_protect_done_card_spec")
def protect_done_card_spec(
    sender,
    instance: models.SpecDoc,
    using: str | None,
    **kwargs,
) -> None:
    if _delete_origin_is_card(kwargs.get("origin")):
        return
    if _card_is_done(instance.card_id, using):
        raise ValidationError(DONE_CARD_SPEC_DELETE_ERROR)


@receiver(
    pre_save,
    sender=models.CardGlossaryTerm,
    dispatch_uid="kanban_validate_card_glossary_term_card",
)
def validate_card_glossary_term_card(
    sender,
    instance: models.CardGlossaryTerm,
    using: str | None,
    **kwargs,
) -> None:
    if instance.pk is None:
        return
    old_card_id = (
        _manager(models.CardGlossaryTerm, using)
        .filter(pk=instance.pk)
        .values_list("card_id", flat=True)
        .first()
    )
    if old_card_id == instance.card_id:
        return
    if _card_is_done(old_card_id, using) and not _card_has_other_glossary_link(
        old_card_id,
        instance.pk,
        using,
    ):
        raise ValidationError(DONE_CARD_GLOSSARY_REASSIGN_ERROR)


@receiver(
    pre_delete,
    sender=models.CardGlossaryTerm,
    dispatch_uid="kanban_protect_done_card_glossary_link",
)
def protect_done_card_glossary_link(
    sender,
    instance: models.CardGlossaryTerm,
    using: str | None,
    **kwargs,
) -> None:
    if _delete_origin_is_card(kwargs.get("origin")):
        return
    if _card_is_done(instance.card_id, using) and not _card_has_other_glossary_link(
        instance.card_id,
        instance.pk,
        using,
    ):
        raise ValidationError(DONE_CARD_GLOSSARY_DELETE_ERROR)


@receiver(post_save, sender=models.Card, dispatch_uid="kanban_sync_card_after_save")
def sync_card_after_save(
    sender,
    instance: models.Card,
    created: bool,
    update_fields: frozenset[str] | None,
    using: str | None,
    **kwargs,
) -> None:
    _sync_card_order_after_insert(instance, using)


@receiver(post_delete, sender=models.Card, dispatch_uid="kanban_compact_card_order_after_delete")
def compact_card_order_after_delete(
    sender,
    instance: models.Card,
    using: str | None,
    **kwargs,
) -> None:
    """Delegate delete-compaction to the service layer (the receiver only wires it)."""
    from apps.kanban import services

    services.compact_card_numbers(instance, using=using)


@receiver(pre_save, sender=models.CardReference, dispatch_uid="kanban_prepare_card_reference")
def prepare_card_reference(
    sender,
    instance: models.CardReference,
    using: str | None,
    **kwargs,
) -> None:
    """Raise-only guard: reject self-references, cycles, and dependency mis-ordering.

    Runs for every ``CardReference`` write, including direct ORM writes that
    bypass ``services.add_dependency``, so the edge invariants hold everywhere.
    """
    if instance.source_card_id is not None and instance.target_card_id is not None:
        _validate_reference_edge(
            instance.source_card_id,
            instance.target_card_id,
            instance.kind_id,
            using,
            exclude_reference_id=instance.pk,
        )


@receiver(
    m2m_changed,
    sender=models.Card.changed_files.through,
    dispatch_uid="kanban_uuid_cardpathlink_m2m",
)
def create_card_path_link_uuid_rows(
    sender,
    instance,
    action: str,
    reverse: bool,
    model,
    pk_set,
    using: str | None = None,
    **kwargs,
) -> None:
    """Create ``UUIDModel`` side-rows for ``CardPathLink`` rows added via M2M writes.

    ``Card.changed_files`` has an explicit ``CardPathLink`` through model, so
    ``.add()`` / ``.set()`` insert through rows with ``bulk_create`` -- which does
    NOT emit ``post_save``, so ``create_uuid_row`` never fires for them. This
    ``m2m_changed`` ``post_add`` receiver backfills the missing side-rows for
    every M2M write path (services, admin, tests' ``.add()``), respecting the
    write's database alias. Rows created via ``.save()`` / ``.objects.create()``
    already have a side-row (from ``create_uuid_row``); the ``uuid__isnull``
    filter keeps this idempotent so neither path double-creates.
    """
    if action != "post_add":
        return
    link_manager = _manager(models.CardPathLink, using)
    if reverse:
        # ``instance`` is a TrackedPath; ``pk_set`` holds the added Card ids.
        links = link_manager.filter(path=instance, card_id__in=pk_set or ())
    else:
        # ``instance`` is a Card; ``pk_set`` holds the added TrackedPath ids.
        links = link_manager.filter(card=instance, path_id__in=pk_set or ())
    for link in links.filter(uuid__isnull=True):
        _manager(models.UUIDModel, using).create(cardpathlink=link)


def create_uuid_row(sender, instance, created: bool, using: str | None = None, **kwargs) -> None:
    """On first save of a linked model, create its ``UUIDModel`` side-row.

    ``bulk_create`` does not emit ``post_save``; importers must use
    ``.save()`` / ``.objects.create()`` for this to fire.
    """
    if created:
        _manager(models.UUIDModel, using).create(**{sender._meta.model_name: instance})


for uuid_linked_model in UUID_LINKED_MODELS:
    post_save.connect(
        create_uuid_row,
        sender=uuid_linked_model,
        dispatch_uid=f"kanban_uuid_{uuid_linked_model._meta.model_name}",
    )
