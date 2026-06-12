"""Application workflows for the kanban app."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from django.db import models as django_models
from django.db import transaction
from django.db.models import Max

from apps.kanban import models
from apps.kanban.constants import PACKAGE_FILE_PATH_SET, PACKAGE_FILE_PATHS

DEFAULT_PLANNING_STATE_KEY = "planned"
DEFAULT_STATUS_KEY = "todo"
DEPENDENCY_NOTE_SECTION_KEY = "dependencies_note"
DEPENDENCY_REFERENCE_KIND_KEY = "dependency"
DONE_STATUS_KEY = "done"
PACKAGE_PATH_PREFIX = "django_strawberry_framework/"


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


def _normalize_package_file_path(value: object) -> str:
    """Return a canonical repo-relative package path string."""
    if not isinstance(value, str):
        raise KanbanServiceError("Package file paths must be strings.")
    path = value.strip().replace("\\", "/")
    if not path:
        raise KanbanServiceError("Package file paths must not be empty.")
    if path.startswith("/") or path.startswith("../") or "/../" in path:
        raise KanbanServiceError(f"Package file path must be repo-relative: {value!r}.")
    if not path.startswith(PACKAGE_PATH_PREFIX):
        raise KanbanServiceError(
            f"Package file path must start with {PACKAGE_PATH_PREFIX!r}: {path!r}.",
        )
    return path


def _package_file_paths(values: object) -> list[str]:
    """Return sorted unique normalized package paths from importer input."""
    if values in (None, ""):
        return []
    if not isinstance(values, list):
        raise KanbanServiceError('"changed_files" must be a list of package file paths.')
    return sorted({_normalize_package_file_path(value) for value in values})


def sync_package_files_from_constants(*, using: str | None = None) -> None:
    """Synchronize PackageFile rows from the generated constants allowlist."""
    manager = _manager(models.PackageFile, using)
    current_paths = set(PACKAGE_FILE_PATHS)
    existing_paths = set(manager.filter(path__in=current_paths).values_list("path", flat=True))
    for path in sorted(current_paths - existing_paths):
        manager.create(path=path, is_current=True)
    manager.filter(path__in=current_paths, is_current=False).update(is_current=True)
    manager.exclude(path__in=current_paths).filter(is_current=True).update(is_current=False)


def package_files_for_paths(
    paths: object,
    *,
    using: str | None = None,
) -> list[models.PackageFile]:
    """Resolve importer path strings to PackageFile rows."""
    normalized_paths = _package_file_paths(paths)
    if not normalized_paths:
        return []

    sync_package_files_from_constants(using=using)
    manager = _manager(models.PackageFile, using)
    existing_paths = set(
        manager.filter(path__in=normalized_paths).values_list("path", flat=True),
    )
    unknown_paths = sorted(
        path
        for path in normalized_paths
        if path not in PACKAGE_FILE_PATH_SET and path not in existing_paths
    )
    if unknown_paths:
        valid_count = len(PACKAGE_FILE_PATH_SET)
        unknown = ", ".join(repr(path) for path in unknown_paths)
        raise KanbanServiceError(
            f"Unknown package file path(s): {unknown}. "
            f"Use one of the {valid_count} generated package paths or an existing "
            "historical PackageFile row.",
        )
    return list(manager.filter(path__in=normalized_paths).order_by("path"))


def set_card_changed_files(card: models.Card, paths: object) -> None:
    """Replace a card's linked package files from importer path strings."""
    using = _database_alias(card)
    card.changed_files.set(package_files_for_paths(paths, using=using))


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
            severity=_lookup(models.Severity, spec["severity"], using)
            if spec.get("severity")
            else None,
            relative_size=_lookup(models.RelativeSize, spec["relative_size"], using),
            planning_state=_lookup(
                models.PlanningState,
                spec.get("planning_state", DEFAULT_PLANNING_STATE_KEY),
                using,
            ),
            planning_note=spec.get("planning_note", ""),
        )
        _create_labels(card, spec.get("labels", []), using)
        _create_parity_claims(card, spec.get("parity", []), using)
        _create_sections(card, spec.get("sections", {}), using)
        _create_dependencies(card, spec.get("dependencies", []), using)
        _create_references(card, spec.get("references", []), using)
        set_card_changed_files(card, spec.get("changed_files", []))
    return card
