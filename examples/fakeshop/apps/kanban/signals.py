"""Signal receivers that keep the kanban board's derived state coherent."""

from __future__ import annotations

from contextlib import contextmanager

from django.core.exceptions import ValidationError
from django.db import models as django_models
from django.db import transaction
from django.db.models import Max
from django.db.models.signals import m2m_changed, post_delete, post_save, pre_delete, pre_save
from django.dispatch import receiver
from django.utils import timezone

from apps.kanban import models

DEFAULT_REFERENCE_KIND_KEY = "dependency"
DEFAULT_REFERENCE_KIND_LABEL = "Dependency"
DEFAULT_REFERENCE_SOURCE_KEY = "dependencies_section"
DEFAULT_REFERENCE_SOURCE_LABEL = "Dependencies section"
DONE_STATUS_KEY = "done"
DONE_CARD_SPEC_ERROR = "Done kanban cards require a linked spec doc."
DONE_CARD_GLOSSARY_ERROR = "Done kanban cards require at least one glossary link."
SPEC_CARD_REQUIRED_ERROR = "Kanban spec docs must be linked to a card."
DONE_CARD_SPEC_REASSIGN_ERROR = "Cannot move a spec doc away from a done kanban card."
DONE_CARD_SPEC_DELETE_ERROR = "Cannot delete a spec doc linked to a done kanban card."
DONE_CARD_GLOSSARY_REASSIGN_ERROR = "Cannot move the last glossary link away from a done card."
DONE_CARD_GLOSSARY_DELETE_ERROR = "Cannot delete the last glossary link from a done card."
DEPENDENCY_REFERENCE_KIND_KEYS = models.DEPENDENCY_REFERENCE_KIND_KEYS
DEPENDENCY_SYNC_FLAG = "_kanban_syncing_dependency_edges"
CARD_ORDER_SYNC_FLAG = "_kanban_syncing_card_order"
CARD_ORDER_REQUESTED_NUMBER_ATTR = "_kanban_requested_card_number"
CARD_ORDER_OLD_NUMBER_ATTR = "_kanban_old_card_number"
CARD_NUMBER_REQUIRED_ERROR = "Kanban cards require a board number."
CARD_NUMBER_POSITIVE_ERROR = "Kanban card number must be at least 1."
CARD_NUMBER_RANGE_ERROR = "Kanban card number must be between 1 and {limit}."
CARD_DEPENDENCY_ORDER_ERROR = "Kanban card dependencies must appear before dependent cards."


UUID_LINKED_MODELS = (
    models.Milestone,
    models.Status,
    models.Priority,
    models.Severity,
    models.RelativeSize,
    models.PlanningState,
    models.Upstream,
    models.ParityLevel,
    models.Section,
    models.CardReferenceKind,
    models.CardReferenceSource,
    models.BoardDocKind,
    models.TargetVersion,
    models.SpecDoc,
    models.Card,
    models.CardReference,
    models.CardGlossaryTerm,
    models.ParityClaim,
    models.CardItem,
    models.Label,
    models.BoardDoc,
    models.BoardDocCardReference,
)


def _manager(model: type[django_models.Model], using: str | None):
    return model.objects.using(using) if using else model.objects


def _target_milestone_id(card: models.Card, using: str | None) -> int | None:
    if card.target_version_id is None:
        return None
    return (
        _manager(models.TargetVersion, using)
        .filter(pk=card.target_version_id)
        .values_list("milestone_id", flat=True)
        .get()
    )


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


def _card_identifier(card: models.Card) -> str:
    milestone = ""
    if card.status.key != "done" and card.milestone_id:
        milestone = f"-{card.milestone.key.upper()}"
    return f"{card.status.key.upper()}{milestone}-{card.number:03d}-{card.target_version.number}"


def _has_dependency_path(start_card_id: int, target_card_id: int, using: str | None) -> bool:
    seen: set[int] = set()
    frontier = {start_card_id}
    card_manager = _manager(models.Card, using)
    while frontier:
        if target_card_id in frontier:
            return True
        seen.update(frontier)
        next_ids = set(
            card_manager.filter(pk__in=frontier).values_list("dependencies__pk", flat=True),
        )
        next_ids.discard(None)
        frontier = next_ids - seen
    return False


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


def _normalize_card_number(number: int | str | None) -> int:
    if number is None:
        raise ValidationError(CARD_NUMBER_REQUIRED_ERROR)
    try:
        return int(number)
    except (TypeError, ValueError):
        raise ValidationError(CARD_NUMBER_REQUIRED_ERROR) from None


def _highest_card_number(using: str | None) -> int:
    highest = _manager(models.Card, using).aggregate(max_number=Max("number"))["max_number"]
    return highest or 0


def _stored_card_number(card_id: int, using: str | None) -> int | None:
    return _manager(models.Card, using).filter(pk=card_id).values_list("number", flat=True).first()


def _validate_card_number(number: int, *, limit: int | None = None) -> None:
    if number < 1:
        raise ValidationError(CARD_NUMBER_POSITIVE_ERROR)
    if limit is not None and number > limit:
        raise ValidationError(CARD_NUMBER_RANGE_ERROR.format(limit=limit))


def _project_neighbor_number(number: int, old_number: int, requested_number: int) -> int:
    if requested_number < old_number and requested_number <= number < old_number:
        return number + 1
    if old_number < requested_number and old_number < number <= requested_number:
        return number - 1
    return number


def _validate_card_move_dependency_order(
    card_id: int,
    old_number: int,
    requested_number: int,
    using: str | None,
) -> None:
    card_manager = _manager(models.Card, using)
    dependency_numbers = card_manager.filter(dependents__pk=card_id).values_list(
        "number",
        flat=True,
    )
    for dependency_number in dependency_numbers:
        final_dependency_number = _project_neighbor_number(
            dependency_number,
            old_number,
            requested_number,
        )
        if final_dependency_number >= requested_number:
            raise ValidationError(CARD_DEPENDENCY_ORDER_ERROR)

    dependent_numbers = card_manager.filter(dependencies__pk=card_id).values_list(
        "number",
        flat=True,
    )
    for dependent_number in dependent_numbers:
        final_dependent_number = _project_neighbor_number(
            dependent_number,
            old_number,
            requested_number,
        )
        if final_dependent_number <= requested_number:
            raise ValidationError(CARD_DEPENDENCY_ORDER_ERROR)


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


def _validate_dependency_edge(source_card_id: int, target_card_id: int, using: str | None) -> None:
    if source_card_id == target_card_id:
        raise ValidationError("A kanban card cannot depend on itself.")
    if _has_dependency_path(target_card_id, source_card_id, using):
        raise ValidationError("Kanban card dependencies cannot contain cycles.")
    _validate_dependency_order(source_card_id, target_card_id, using)


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


@contextmanager
def _card_order_sync(card: models.Card):
    previous = getattr(card, CARD_ORDER_SYNC_FLAG, None)
    setattr(card, CARD_ORDER_SYNC_FLAG, True)
    try:
        yield
    finally:
        if previous is None:
            delattr(card, CARD_ORDER_SYNC_FLAG)
        else:
            setattr(card, CARD_ORDER_SYNC_FLAG, previous)


def _is_card_order_sync(instance: models.Card) -> bool:
    return bool(getattr(instance, CARD_ORDER_SYNC_FLAG, False))


def _set_card_order_request(
    card: models.Card,
    *,
    requested_number: int,
    old_number: int | None,
) -> None:
    setattr(card, CARD_ORDER_REQUESTED_NUMBER_ATTR, requested_number)
    setattr(card, CARD_ORDER_OLD_NUMBER_ATTR, old_number)


def _clear_card_order_request(card: models.Card) -> None:
    for attribute in (CARD_ORDER_REQUESTED_NUMBER_ATTR, CARD_ORDER_OLD_NUMBER_ATTR):
        if hasattr(card, attribute):
            delattr(card, attribute)


def _save_card_number(card: models.Card, number: int, using: str | None) -> None:
    card.number = number
    with _card_order_sync(card):
        card.save(update_fields=["number", "updated_date"], using=using)


def _prepare_card_order(
    card: models.Card,
    update_fields: frozenset[str] | None,
    using: str | None,
) -> None:
    if update_fields is not None and "number" not in update_fields:
        return

    requested_number = _normalize_card_number(card.number)
    card.number = requested_number

    max_number = _highest_card_number(using)
    if card.pk is None:
        _validate_card_number(requested_number)
        if requested_number <= max_number:
            _set_card_order_request(
                card,
                requested_number=requested_number,
                old_number=None,
            )
            card.number = max_number + 2
        return

    old_number = _stored_card_number(card.pk, using)
    if old_number is None:
        _validate_card_number(requested_number)
        if requested_number <= max_number:
            _set_card_order_request(
                card,
                requested_number=requested_number,
                old_number=None,
            )
            card.number = max_number + 2
        return
    if requested_number == old_number:
        return

    _validate_card_number(requested_number)
    _validate_card_move_dependency_order(card.pk, old_number, requested_number, using)
    _set_card_order_request(
        card,
        requested_number=requested_number,
        old_number=old_number,
    )
    card.number = max_number + 1


def _shift_cards_after_insert(
    inserted_card: models.Card,
    requested_number: int,
    using: str | None,
) -> None:
    queryset = (
        _manager(models.Card, using)
        .filter(number__gte=requested_number)
        .exclude(pk=inserted_card.pk)
        .order_by("-number")
    )
    for card in queryset:
        _save_card_number(card, card.number + 1, using)


def _shift_cards_after_move(
    moved_card: models.Card,
    old_number: int,
    requested_number: int,
    using: str | None,
) -> None:
    card_manager = _manager(models.Card, using).exclude(pk=moved_card.pk)
    if requested_number < old_number:
        queryset = card_manager.filter(
            number__gte=requested_number,
            number__lt=old_number,
        ).order_by("-number")
        delta = 1
    else:
        queryset = card_manager.filter(
            number__gt=old_number,
            number__lte=requested_number,
        ).order_by("number")
        delta = -1
    for card in queryset:
        _save_card_number(card, card.number + delta, using)


def _sync_card_order_after_save(card: models.Card, using: str | None) -> None:
    if _is_card_order_sync(card):
        return

    requested_number = getattr(card, CARD_ORDER_REQUESTED_NUMBER_ATTR, None)
    if requested_number is None:
        return
    old_number = getattr(card, CARD_ORDER_OLD_NUMBER_ATTR, None)

    try:
        with transaction.atomic(using=using):
            if old_number is None:
                _shift_cards_after_insert(card, requested_number, using)
            else:
                _shift_cards_after_move(card, old_number, requested_number, using)
            _save_card_number(card, requested_number, using)
    finally:
        _clear_card_order_request(card)


def _compact_card_numbers_after_delete(card: models.Card, using: str | None) -> None:
    queryset = _manager(models.Card, using).filter(number__gt=card.number).order_by("number")
    for shifted_card in queryset:
        _save_card_number(shifted_card, shifted_card.number - 1, using)


@contextmanager
def _dependency_sync(card: models.Card):
    previous = getattr(card, DEPENDENCY_SYNC_FLAG, None)
    setattr(card, DEPENDENCY_SYNC_FLAG, True)
    try:
        yield
    finally:
        if previous is None:
            delattr(card, DEPENDENCY_SYNC_FLAG)
        else:
            setattr(card, DEPENDENCY_SYNC_FLAG, previous)


def _is_dependency_sync(instance: models.Card) -> bool:
    return bool(getattr(instance, DEPENDENCY_SYNC_FLAG, False))


def _dependency_edge_exists(
    source_card: models.Card,
    target_card: models.Card,
    using: str | None,
) -> bool:
    return _manager(models.Card, using).filter(pk=source_card.pk, dependencies=target_card).exists()


def _kind_is_dependency_reference(kind_id: int | None, using: str | None) -> bool:
    if kind_id is None:
        return False
    return (
        _manager(models.CardReferenceKind, using)
        .filter(pk=kind_id, key__in=DEPENDENCY_REFERENCE_KIND_KEYS)
        .exists()
    )


def _dependency_reference_exists(
    source_card_id: int,
    target_card_id: int,
    using: str | None,
) -> bool:
    return (
        _manager(models.CardReference, using)
        .filter(
            source_card_id=source_card_id,
            target_card_id=target_card_id,
            kind__key__in=DEPENDENCY_REFERENCE_KIND_KEYS,
        )
        .exists()
    )


def _default_reference_kind(using: str | None) -> models.CardReferenceKind:
    kind, _ = _manager(models.CardReferenceKind, using).get_or_create(
        key=DEFAULT_REFERENCE_KIND_KEY,
        defaults={"label": DEFAULT_REFERENCE_KIND_LABEL},
    )
    return kind


def _default_reference_source(using: str | None) -> models.CardReferenceSource:
    source, _ = _manager(models.CardReferenceSource, using).get_or_create(
        key=DEFAULT_REFERENCE_SOURCE_KEY,
        defaults={"label": DEFAULT_REFERENCE_SOURCE_LABEL},
    )
    return source


def _next_reference_order(
    source_card: models.Card,
    source: models.CardReferenceSource,
    using: str | None,
) -> int:
    max_order = (
        _manager(models.CardReference, using)
        .filter(source_card=source_card, source=source)
        .aggregate(Max("order"))["order__max"]
    )
    if max_order is None:
        return 0
    return max_order + 1


def _ensure_reference_for_dependency(
    source_card: models.Card,
    target_card: models.Card,
    using: str | None,
) -> None:
    if _dependency_reference_exists(source_card.pk, target_card.pk, using):
        return
    kind = _default_reference_kind(using)
    source = _default_reference_source(using)
    _manager(models.CardReference, using).create(
        source_card=source_card,
        target_card=target_card,
        kind=kind,
        source=source,
        raw_text=f"Manual dependency: `{_card_identifier(target_card)}`.",
        order=_next_reference_order(source_card, source, using),
    )


def _delete_default_references(source_card_id: int, target_card_id: int, using: str | None) -> None:
    kind = _manager(models.CardReferenceKind, using).filter(key=DEFAULT_REFERENCE_KIND_KEY).first()
    source = (
        _manager(models.CardReferenceSource, using).filter(key=DEFAULT_REFERENCE_SOURCE_KEY).first()
    )
    if kind is None or source is None:
        return
    _manager(models.CardReference, using).filter(
        source_card_id=source_card_id,
        target_card_id=target_card_id,
        kind=kind,
        source=source,
    ).delete()


def _restore_dependency_if_references_remain(
    source_card_id: int,
    target_card_id: int,
    using: str | None,
) -> None:
    if not _dependency_reference_exists(source_card_id, target_card_id, using):
        return
    card_manager = _manager(models.Card, using)
    source_card = card_manager.filter(pk=source_card_id).first()
    target_card = card_manager.filter(pk=target_card_id).first()
    if source_card is None or target_card is None:
        return
    if _dependency_edge_exists(source_card, target_card, using):
        return
    with _dependency_sync(source_card):
        source_card.dependencies.add(target_card)


def _remove_dependency_if_unreferenced(
    source_card_id: int,
    target_card_id: int,
    using: str | None,
) -> None:
    if _dependency_reference_exists(source_card_id, target_card_id, using):
        return
    card_manager = _manager(models.Card, using)
    source_card = card_manager.filter(pk=source_card_id).first()
    target_card = card_manager.filter(pk=target_card_id).first()
    if source_card is None or target_card is None:
        return
    if not _dependency_edge_exists(source_card, target_card, using):
        return
    with _dependency_sync(source_card):
        source_card.dependencies.remove(target_card)


def _dependency_edges_from_pk_set(
    instance: models.Card,
    pk_set: set[int],
    *,
    reverse: bool,
) -> list[tuple[int, int]]:
    if reverse:
        return [(pk, instance.pk) for pk in pk_set]
    return [(instance.pk, pk) for pk in pk_set]


def _dependency_edges_for_clear(
    instance: models.Card,
    using: str | None,
    *,
    reverse: bool,
) -> list[tuple[int, int]]:
    card_manager = _manager(models.Card, using)
    if reverse:
        source_ids = card_manager.filter(dependencies=instance).values_list("pk", flat=True)
        return [(source_id, instance.pk) for source_id in source_ids]
    target_ids = card_manager.filter(pk=instance.pk).values_list("dependencies__pk", flat=True)
    return [(instance.pk, target_id) for target_id in target_ids if target_id is not None]


@receiver(pre_save, sender=models.Card, dispatch_uid="kanban_prepare_card_save")
def prepare_card_save(
    sender,
    instance: models.Card,
    update_fields: frozenset[str] | None,
    using: str | None,
    **kwargs,
) -> None:
    if _is_card_order_sync(instance):
        return
    instance.milestone_id = _target_milestone_id(instance, using)
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
    if _is_card_order_sync(instance):
        return

    _sync_card_order_after_save(instance, using)
    if (
        update_fields is not None
        and {"target_version", "target_version_id"} & set(update_fields)
        and "milestone" not in update_fields
    ):
        _manager(models.Card, using).filter(pk=instance.pk).update(
            milestone_id=instance.milestone_id,
            updated_date=timezone.now(),
        )


@receiver(post_delete, sender=models.Card, dispatch_uid="kanban_compact_card_order_after_delete")
def compact_card_order_after_delete(
    sender,
    instance: models.Card,
    using: str | None,
    **kwargs,
) -> None:
    _compact_card_numbers_after_delete(instance, using)


@receiver(pre_save, sender=models.CardReference, dispatch_uid="kanban_prepare_card_reference")
def prepare_card_reference(
    sender,
    instance: models.CardReference,
    using: str | None,
    **kwargs,
) -> None:
    if instance.source_card_id is not None and instance.target_card_id is not None:
        _validate_reference_edge(
            instance.source_card_id,
            instance.target_card_id,
            instance.kind_id,
            using,
            exclude_reference_id=instance.pk,
        )
    if instance.pk is None:
        instance._kanban_old_reference_edge = None
        return
    instance._kanban_old_reference_edge = (
        _manager(models.CardReference, using)
        .filter(pk=instance.pk)
        .values_list("source_card_id", "target_card_id", "kind_id")
        .first()
    )


@receiver(post_save, sender=models.CardReference, dispatch_uid="kanban_sync_reference_dependency")
def sync_reference_dependency(
    sender,
    instance: models.CardReference,
    using: str | None,
    **kwargs,
) -> None:
    old_reference = getattr(instance, "_kanban_old_reference_edge", None)
    new_edge = (instance.source_card_id, instance.target_card_id)
    is_dependency_reference = _kind_is_dependency_reference(instance.kind_id, using)
    if old_reference is not None:
        old_edge = (old_reference[0], old_reference[1])
        if _kind_is_dependency_reference(old_reference[2], using) and (
            old_edge != new_edge or not is_dependency_reference
        ):
            _remove_dependency_if_unreferenced(old_edge[0], old_edge[1], using)

    if not is_dependency_reference:
        return
    if not _dependency_edge_exists(instance.source_card, instance.target_card, using):
        with _dependency_sync(instance.source_card):
            instance.source_card.dependencies.add(instance.target_card)


@receiver(
    post_delete,
    sender=models.CardReference,
    dispatch_uid="kanban_delete_reference_dependency",
)
def delete_reference_dependency(
    sender,
    instance: models.CardReference,
    using: str | None,
    **kwargs,
) -> None:
    if not _kind_is_dependency_reference(instance.kind_id, using):
        return
    _remove_dependency_if_unreferenced(instance.source_card_id, instance.target_card_id, using)


@receiver(
    m2m_changed,
    sender=models.Card.dependencies.through,
    dispatch_uid="kanban_sync_dependency_references",
)
def sync_dependency_references(
    sender,
    instance: models.Card,
    action: str,
    reverse: bool,
    pk_set: set[int] | None,
    using: str | None,
    **kwargs,
) -> None:
    if _is_dependency_sync(instance):
        return

    if action == "pre_add" and pk_set:
        for source_card_id, target_card_id in _dependency_edges_from_pk_set(
            instance,
            pk_set,
            reverse=reverse,
        ):
            _validate_dependency_edge(source_card_id, target_card_id, using)
        return

    if action == "post_add" and pk_set:
        card_by_id = _manager(models.Card, using).in_bulk(pk_set | {instance.pk})
        for source_card_id, target_card_id in _dependency_edges_from_pk_set(
            instance,
            pk_set,
            reverse=reverse,
        ):
            _ensure_reference_for_dependency(
                card_by_id[source_card_id],
                card_by_id[target_card_id],
                using,
            )
        return

    if action == "pre_clear":
        instance._kanban_cleared_dependency_edges = _dependency_edges_for_clear(
            instance,
            using,
            reverse=reverse,
        )
        return

    if action == "post_clear":
        dependency_edges = getattr(instance, "_kanban_cleared_dependency_edges", [])
    elif action == "post_remove" and pk_set:
        dependency_edges = _dependency_edges_from_pk_set(instance, pk_set, reverse=reverse)
    else:
        return

    for source_card_id, target_card_id in dependency_edges:
        _delete_default_references(source_card_id, target_card_id, using)
        _restore_dependency_if_references_remain(source_card_id, target_card_id, using)


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
