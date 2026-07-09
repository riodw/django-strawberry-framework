"""Application workflows for the kanban app."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from django.db import models as django_models
from django.db import transaction
from django.db.models import Max

from apps.kanban import models
from apps.kanban.constants import (
    TRACKED_DIRECTORY_PATHS,
    TRACKED_FILE_PATHS,
    TRACKED_PATH_SET,
)

DEFAULT_STATUS_KEY = "todo"
DEPENDENCY_NOTE_SECTION_KEY = "dependencies_note"
DEPENDENCY_REFERENCE_KIND_KEY = "dependency"
DONE_STATUS_KEY = "done"
# Roots a card-linked path may live under: the package plus the four deliberate
# test locations (mirrors scripts/build_kanban_tracked_path_constants.py).
TRACKED_ROOTS = (
    "django_strawberry_framework/",
    "tests/",
    "examples/fakeshop/test_query/",
    "examples/fakeshop/tests/",
)
APP_TESTS_ROOT_RE = re.compile(r"^examples/fakeshop/apps/[^/]+/tests/")


class KanbanServiceError(ValueError):
    """A caller-correctable kanban workflow error."""


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
    return _lookup_by(model, key, using, field="key")


def _lookup_by(
    model: type[django_models.Model],
    key: str,
    using: str | None,
    *,
    field: str,
):
    try:
        return _manager(model, using).get(**{field: key})
    except model.DoesNotExist:
        valid = ", ".join(
            sorted(_manager(model, using).values_list(field, flat=True).distinct()),
        )
        raise KanbanServiceError(
            f"Unknown {model.__name__} {field}={key!r}. Valid values: {valid}",
        ) from None


def _normalize_tracked_path(value: object, *, field_name: str) -> str:
    """Return a canonical repo-relative tracked path string.

    Directory paths keep their trailing ``/``; that trailing slash is the
    file/directory discriminator everywhere downstream.
    """
    if not isinstance(value, str):
        raise KanbanServiceError(f'"{field_name}" paths must be strings.')
    path = value.strip().replace("\\", "/")
    if not path:
        raise KanbanServiceError(f'"{field_name}" paths must not be empty.')
    if path.startswith("/") or path.startswith("../") or "/../" in path or path.endswith("/.."):
        raise KanbanServiceError(f"Tracked path must be repo-relative: {value!r}.")
    if not (any(path.startswith(root) for root in TRACKED_ROOTS) or APP_TESTS_ROOT_RE.match(path)):
        roots = ", ".join(repr(root) for root in TRACKED_ROOTS)
        raise KanbanServiceError(
            f"Tracked path must live under one of the allowed roots "
            f"({roots}, 'examples/fakeshop/apps/*/tests/'): {path!r}.",
        )
    return path


def _tracked_paths(values: object, *, field_name: str) -> list[str]:
    """Return sorted unique normalized tracked paths from importer input."""
    if values in (None, ""):
        return []
    if not isinstance(values, list):
        raise KanbanServiceError(f'"{field_name}" must be a list of repo-relative paths.')
    return sorted({_normalize_tracked_path(value, field_name=field_name) for value in values})


def sync_tracked_paths_from_constants(*, using: str | None = None) -> None:
    """Synchronize TrackedPath rows from the generated constants allowlist."""
    manager = _manager(models.TrackedPath, using)
    current = dict.fromkeys(TRACKED_FILE_PATHS, False)
    current.update(dict.fromkeys(TRACKED_DIRECTORY_PATHS, True))
    existing_paths = set(manager.filter(path__in=current).values_list("path", flat=True))
    for path in sorted(set(current) - existing_paths):
        manager.create(path=path, is_current=True, is_directory=current[path])
    manager.filter(path__in=current, is_current=False).update(is_current=True)
    manager.exclude(path__in=current).filter(is_current=True).update(is_current=False)


def tracked_paths_for_paths(
    paths: object,
    *,
    using: str | None = None,
) -> list[models.TrackedPath]:
    """Resolve importer path strings to known TrackedPath rows (no row creation)."""
    normalized_paths = _tracked_paths(paths, field_name="changed_files")
    if not normalized_paths:
        return []

    sync_tracked_paths_from_constants(using=using)
    manager = _manager(models.TrackedPath, using)
    existing_paths = set(
        manager.filter(path__in=normalized_paths).values_list("path", flat=True),
    )
    unknown_paths = sorted(
        path
        for path in normalized_paths
        if path not in TRACKED_PATH_SET and path not in existing_paths
    )
    if unknown_paths:
        valid_count = len(TRACKED_PATH_SET)
        unknown = ", ".join(repr(path) for path in unknown_paths)
        raise KanbanServiceError(
            f"Unknown tracked path(s): {unknown}. "
            f"Use one of the {valid_count} generated tracked paths or an existing "
            "historical TrackedPath row.",
        )
    return list(manager.filter(path__in=normalized_paths).order_by("path"))


def planned_tracked_paths_for_paths(
    paths: object,
    *,
    using: str | None = None,
    field_name: str = "predicted_files",
) -> list[models.TrackedPath]:
    """Resolve predicted path strings, creating planned rows for unknown paths.

    Unknown paths must still live under an allowed root; new rows are created
    with ``is_current=False`` (planned) and ``is_directory`` derived from the
    trailing ``/``.
    """
    normalized_paths = _tracked_paths(paths, field_name=field_name)
    if not normalized_paths:
        return []

    sync_tracked_paths_from_constants(using=using)
    manager = _manager(models.TrackedPath, using)
    for path in normalized_paths:
        manager.get_or_create(
            path=path,
            defaults={"is_current": False, "is_directory": path.endswith("/")},
        )
    return list(manager.filter(path__in=normalized_paths).order_by("path"))


def set_card_changed_files(card: models.Card, paths: object) -> None:
    """Replace a DONE card's actually-changed tracked paths (strict allowlist)."""
    using = _database_alias(card)
    card.changed_files.set(tracked_paths_for_paths(paths, using=using))


def set_card_predicted_files(
    card: models.Card,
    paths: object,
    *,
    field_name: str = "predicted_files",
) -> None:
    """Replace a non-DONE card's predicted tracked paths (may create planned rows).

    DONE cards record what actually shipped; predictions on them are rejected so
    the strict :func:`set_card_changed_files` path stays the only writer there.
    """
    if card.status.key == DONE_STATUS_KEY:
        raise KanbanServiceError(
            f"Cannot set predicted files on done card {card.card_id!r}; "
            "use changed-file imports for shipped cards.",
        )
    using = _database_alias(card)
    card.changed_files.set(
        planned_tracked_paths_for_paths(paths, using=using, field_name=field_name),
    )


def _require_fields(spec: dict[str, Any], fields: tuple[str, ...]) -> None:
    for field in fields:
        if not spec.get(field):
            raise KanbanServiceError(f'Card is missing required field "{field}".')


def resolve_card(identifier: object, *, using: str | None = None) -> models.Card:
    """Resolve a card by exact title, then by integer board number."""
    card_manager = _manager(models.Card, using)
    if isinstance(identifier, str):
        card = card_manager.filter(title=identifier).first()
        if card is not None:
            return card
    if isinstance(identifier, int) or (isinstance(identifier, str) and identifier.isdigit()):
        card = card_manager.filter(number=int(identifier)).first()
        if card is not None:
            return card
    raise KanbanServiceError(
        f"Cannot resolve card reference: {identifier!r} (use the card title).",
    )


def _target_number(spec: dict[str, Any], using: str | None) -> int:
    if spec.get("number") is not None:
        try:
            return int(spec["number"])
        except (TypeError, ValueError) as error:
            raise KanbanServiceError('"number" must be an integer when provided.') from error
    if spec.get("after") is not None:
        return resolve_card(spec["after"], using=using).number + 1
    highest = _manager(models.Card, using).order_by("-number").first()
    return (highest.number + 1) if highest else 1


def _order_or_empty(order: int | None) -> int:
    return -1 if order is None else order


def _next_card_item_order(card: models.Card, section: models.Section, using: str | None) -> int:
    max_order = (
        _manager(models.CardItem, using)
        .filter(card=card, section=section)
        .aggregate(value=Max("order"))["value"]
    )
    return _order_or_empty(max_order) + 1


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
    *,
    raw_text: str = "",
) -> models.CardReference:
    """Create a card reference; ``order`` is assigned per source_card by ``save()``."""
    using = _database_alias(source_card, target_card, kind)
    return _manager(models.CardReference, using).create(
        source_card=source_card,
        target_card=target_card,
        kind=kind,
        raw_text=raw_text,
    )


def add_dependency_note(
    card: models.Card,
    target_card: models.Card,
    note: str = "",
    *,
    order: int | None = None,
) -> DependencyNote:
    """Create a dependency reference and its rendered prose bullet.

    The reference's ``order`` is assigned per source_card by
    ``CardReference.save()``; the prose item appends within its section.
    """
    using = _database_alias(card, target_card)
    kind = _lookup(models.CardReferenceKind, DEPENDENCY_REFERENCE_KIND_KEY, using)
    section = _lookup(models.Section, DEPENDENCY_NOTE_SECTION_KEY, using)

    with transaction.atomic(using=using):
        reference = append_card_reference(
            source_card=card,
            target_card=target_card,
            kind=kind,
            raw_text=note,
        )
        item = append_card_item(
            card=card,
            section=section,
            text=note,
            order=order,
        )
    return DependencyNote(reference=reference, item=item)


def _create_labels(card: models.Card, labels: list[str], using: str | None) -> None:
    for label_key in labels:
        card.labels.add(_lookup(models.Label, label_key, using))


def _create_parity_claims(
    card: models.Card,
    parity_claims: list[dict[str, str]],
    using: str | None,
) -> None:
    for claim in parity_claims:
        _manager(models.ParityClaim, using).create(
            card=card,
            upstream=_lookup(models.Upstream, claim["upstream"], using),
            level=_lookup(models.ParityLevel, claim["level"], using),
        )


def _create_sections(
    card: models.Card,
    sections: dict[str, list[str | dict[str, Any]]],
    using: str | None,
) -> None:
    for section_key, bullets in sections.items():
        section = _lookup(models.Section, section_key, using)
        for order, bullet in enumerate(bullets):
            if isinstance(bullet, dict):
                text = bullet.get("text", "")
                done = bool(bullet.get("done", False))
            else:
                text = bullet
                done = False
            append_card_item(
                card=card,
                section=section,
                text=text,
                order=order,
                is_complete=done,
            )


def _create_dependencies(
    card: models.Card,
    dependencies: list[dict[str, str]],
    using: str | None,
) -> None:
    for order, dependency in enumerate(dependencies):
        add_dependency_note(
            card=card,
            target_card=resolve_card(dependency["card"], using=using),
            note=dependency.get("note", ""),
            order=order,
        )


def _create_references(
    card: models.Card,
    references: list[dict[str, str]],
    using: str | None,
) -> None:
    for reference in references:
        append_card_reference(
            source_card=card,
            target_card=resolve_card(reference["target"], using=using),
            kind=_lookup(models.CardReferenceKind, reference.get("kind", "related"), using),
            raw_text=reference.get("text", ""),
        )


def create_card_from_spec(spec: dict[str, Any], *, using: str | None = None) -> models.Card:
    """Create a kanban card and all child rows from a structured card spec."""
    _require_fields(spec, ("title", "target_version", "relative_size"))
    title = spec["title"]
    if _manager(models.Card, using).filter(title=title).exists():
        raise KanbanServiceError(f"A card titled {title!r} already exists.")
    if isinstance(spec.get("sections"), dict) and "dependencies" in spec["sections"]:
        raise KanbanServiceError(
            'Put dependencies under the top-level "dependencies" key, not "sections".',
        )

    status_key = spec.get("status", DEFAULT_STATUS_KEY)
    if status_key == DONE_STATUS_KEY:
        raise KanbanServiceError(
            'Kanban card creation cannot create "done" cards because done cards require '
            "a linked spec doc. Import the card before marking it done.",
        )

    with transaction.atomic(using=using):
        target_version = _lookup_by(
            models.TargetVersion,
            spec["target_version"],
            using,
            field="number",
        )
        card = _manager(models.Card, using).create(
            title=title,
            number=_target_number(spec, using),
            status=_lookup(models.Status, status_key, using),
            milestone=target_version.milestone,
            target_version=target_version,
            priority=_lookup(models.Priority, spec["priority"], using)
            if spec.get("priority")
            else None,
            relative_size=_lookup(models.RelativeSize, spec["relative_size"], using),
            planning_note=spec.get("planning_note", ""),
        )
        _create_labels(card, spec.get("labels", []), using)
        _create_parity_claims(card, spec.get("parity", []), using)
        _create_sections(card, spec.get("sections", {}), using)
        _create_dependencies(card, spec.get("dependencies", []), using)
        _create_references(card, spec.get("references", []), using)
        # Created cards are never "done", so their linked paths are predictions.
        set_card_predicted_files(card, spec.get("changed_files", []), field_name="changed_files")
    return card
