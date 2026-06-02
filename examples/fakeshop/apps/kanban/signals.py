"""Signal receivers that keep the kanban board's derived state coherent."""

from __future__ import annotations

from contextlib import contextmanager

from django.core.exceptions import ValidationError
from django.db import models as django_models
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
SPEC_CARD_REQUIRED_ERROR = "Kanban spec docs must be linked to a card."
DONE_CARD_SPEC_REASSIGN_ERROR = "Cannot move a spec doc away from a done kanban card."
DONE_CARD_SPEC_DELETE_ERROR = "Cannot delete a spec doc linked to a done kanban card."
DEPENDENCY_REFERENCE_KIND_KEYS = models.DEPENDENCY_REFERENCE_KIND_KEYS
DEPENDENCY_SYNC_FLAG = "_kanban_syncing_dependency_edges"


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


def _validate_done_card_has_spec(card: models.Card, using: str | None) -> None:
    if _status_is_done(card.status_id, using) and not _card_has_spec(card, using):
        raise ValidationError(DONE_CARD_SPEC_ERROR)


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


def _validate_dependency_edge(source_card_id: int, target_card_id: int, using: str | None) -> None:
    if source_card_id == target_card_id:
        raise ValidationError("A kanban card cannot depend on itself.")
    if _has_dependency_path(target_card_id, source_card_id, using):
        raise ValidationError("Kanban card dependencies cannot contain cycles.")


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
def prepare_card_save(sender, instance: models.Card, using: str | None, **kwargs) -> None:
    instance.milestone_id = _target_milestone_id(instance, using)
    _validate_done_card_has_spec(instance, using)


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


@receiver(post_save, sender=models.Card, dispatch_uid="kanban_sync_card_after_save")
def sync_card_after_save(
    sender,
    instance: models.Card,
    created: bool,
    update_fields: frozenset[str] | None,
    using: str | None,
    **kwargs,
) -> None:
    if (
        update_fields is not None
        and {"target_version", "target_version_id"} & set(update_fields)
        and "milestone" not in update_fields
    ):
        _manager(models.Card, using).filter(pk=instance.pk).update(
            milestone_id=instance.milestone_id,
            updated_date=timezone.now(),
        )


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
