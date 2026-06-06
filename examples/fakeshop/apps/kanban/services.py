"""Application workflows for the kanban app."""

from __future__ import annotations

from dataclasses import dataclass

from django.db import models as django_models
from django.db import transaction
from django.db.models import Max

from apps.kanban import models

DEPENDENCY_NOTE_SECTION_KEY = "dependencies_note"
DEPENDENCY_REFERENCE_KIND_KEY = "dependency"
DEPENDENCY_REFERENCE_SOURCE_KEY = "dependencies_section"


@dataclass(frozen=True)
class DependencyNote:
    """Rows created for a dependency note workflow."""

    reference: models.CardReference
    item: models.CardItem


def _manager(model: type[django_models.Model], using: str | None):
    return model.objects.using(using) if using else model.objects


def _database_alias(*instances: django_models.Model) -> str | None:
    aliases = {instance._state.db for instance in instances if instance._state.db is not None}
    if len(aliases) > 1:
        raise ValueError("Kanban services require objects from the same database.")
    return next(iter(aliases), None)


def _lookup(model: type[django_models.Model], key: str, using: str | None):
    return _manager(model, using).get(key=key)


def _order_or_empty(order: int | None) -> int:
    return -1 if order is None else order


def _next_card_item_order(card: models.Card, section: models.Section, using: str | None) -> int:
    max_order = (
        _manager(models.CardItem, using)
        .filter(card=card, section=section)
        .aggregate(value=Max("order"))["value"]
    )
    return _order_or_empty(max_order) + 1


def _next_card_reference_order(
    card: models.Card,
    source: models.CardReferenceSource,
    using: str | None,
) -> int:
    max_reference_order = (
        _manager(models.CardReference, using)
        .filter(source_card=card, source=source)
        .aggregate(value=Max("order"))["value"]
    )
    return _order_or_empty(max_reference_order) + 1


def append_card_item(
    card: models.Card,
    section: models.Section,
    text: str,
    *,
    is_complete: bool = False,
    order: int | None = None,
) -> models.CardItem:
    """Create a card section item, appending to the section when order is omitted."""
    using = _database_alias(card, section)
    item_order = _next_card_item_order(card, section, using) if order is None else order
    return _manager(models.CardItem, using).create(
        card=card,
        section=section,
        text=text,
        order=item_order,
        is_complete=is_complete,
    )


def append_card_reference(
    source_card: models.Card,
    target_card: models.Card,
    kind: models.CardReferenceKind,
    source: models.CardReferenceSource,
    *,
    raw_text: str = "",
    order: int | None = None,
) -> models.CardReference:
    """Create a card reference, appending within the source when order is omitted."""
    using = _database_alias(source_card, target_card, kind, source)
    reference_order = (
        _next_card_reference_order(source_card, source, using) if order is None else order
    )
    return _manager(models.CardReference, using).create(
        source_card=source_card,
        target_card=target_card,
        kind=kind,
        source=source,
        order=reference_order,
        raw_text=raw_text,
    )


def _next_dependency_note_order(
    card: models.Card,
    source: models.CardReferenceSource,
    section: models.Section,
    using: str | None,
) -> int:
    return max(
        _next_card_reference_order(card, source, using),
        _next_card_item_order(card, section, using),
    )


def add_dependency_note(
    card: models.Card,
    target_card: models.Card,
    note: str = "",
    *,
    order: int | None = None,
) -> DependencyNote:
    """Create a dependency reference and its rendered prose bullet."""
    using = _database_alias(card, target_card)
    kind = _lookup(models.CardReferenceKind, DEPENDENCY_REFERENCE_KIND_KEY, using)
    source = _lookup(models.CardReferenceSource, DEPENDENCY_REFERENCE_SOURCE_KEY, using)
    section = _lookup(models.Section, DEPENDENCY_NOTE_SECTION_KEY, using)
    note_order = (
        _next_dependency_note_order(card, source, section, using) if order is None else order
    )

    with transaction.atomic(using=using):
        reference = append_card_reference(
            source_card=card,
            target_card=target_card,
            kind=kind,
            source=source,
            raw_text=note,
            order=note_order,
        )
        item = append_card_item(
            card=card,
            section=section,
            text=note,
            order=note_order,
        )
    return DependencyNote(reference=reference, item=item)
