"""The sanctioned write API for the kanban app.

Every validated mutation of board state flows through a function here: card
creation, status moves (with :class:`~apps.kanban.models.CardTransition`
logging), board-number moves and delete-compaction (the renumbering engine),
dependency edges, tracked-path links, per-bullet completion / verification, and
the work-tracking writers (attempts and decisions). ``signals.py`` is demoted to
raise-only guards plus UUID side-row wiring, so a direct ORM ``save()`` that
would corrupt an invariant is rejected and pointed back here.

Caller-correctable failures raise :class:`KanbanServiceError`, which carries a
stable ``code`` string (e.g. ``"already_in_status"``, ``"unknown_lookup"``) so
callers -- management commands, future GraphQL mutations -- can branch on the
failure without string-matching the message.
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from typing import Any

from django.db import models as django_models
from django.db import transaction
from django.db.models import Max
from django.utils import timezone
from django.utils.text import slugify

from apps.kanban import models
from apps.kanban.constants import (
    TRACKED_DIRECTORY_PATHS,
    TRACKED_FILE_PATHS,
    TRACKED_PATH_SET,
)

DEFAULT_STATUS_KEY = "todo"
DEPENDENCY_NOTE_SECTION_KEY = "dependencies_note"
DEPENDENCY_REFERENCE_KIND_KEY = "dependency"
# Shared with signals.py via the single home in models.py.
DONE_STATUS_KEY = models.DONE_STATUS_KEY
CARD_DEPENDENCY_ORDER_MESSAGE = "Kanban card dependencies must appear before dependent cards."
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
    """A caller-correctable kanban workflow error carrying a stable ``code``.

    ``code`` is a machine-stable identifier for the failure class (e.g.
    ``"unknown_lookup"``, ``"illegal_transition"``) so callers branch on it
    instead of the human-readable message. It defaults to ``"kanban_error"`` for
    the rare raise that has no more specific class.
    """

    def __init__(self, message: str, *, code: str = "kanban_error"):
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class DependencyNote:
    """Rows created for a dependency note workflow."""

    reference: models.CardReference
    item: models.CardItem


# The alias-aware manager helper lives once in models.py; both services.py and
# signals.py bind to it here so the lookup cannot drift between the two modules.
_manager = models.manager


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
            code="unknown_lookup",
        ) from None


def _normalize_tracked_path(value: object, *, field_name: str) -> str:
    """Return a canonical repo-relative tracked path string.

    Directory paths keep their trailing ``/``; that trailing slash is the
    file/directory discriminator everywhere downstream.
    """
    if not isinstance(value, str):
        raise KanbanServiceError(
            f'"{field_name}" paths must be strings.',
            code="invalid_tracked_path",
        )
    path = value.strip().replace("\\", "/")
    if not path:
        raise KanbanServiceError(
            f'"{field_name}" paths must not be empty.',
            code="invalid_tracked_path",
        )
    if path.startswith("/") or path.startswith("../") or "/../" in path or path.endswith("/.."):
        raise KanbanServiceError(
            f"Tracked path must be repo-relative: {value!r}.",
            code="invalid_tracked_path",
        )
    if not (any(path.startswith(root) for root in TRACKED_ROOTS) or APP_TESTS_ROOT_RE.match(path)):
        roots = ", ".join(repr(root) for root in TRACKED_ROOTS)
        raise KanbanServiceError(
            f"Tracked path must live under one of the allowed roots "
            f"({roots}, 'examples/fakeshop/apps/*/tests/'): {path!r}.",
            code="tracked_path_outside_roots",
        )
    return path


def _tracked_paths(values: object, *, field_name: str) -> list[str]:
    """Return sorted unique normalized tracked paths from importer input."""
    if values in (None, ""):
        return []
    if not isinstance(values, list):
        raise KanbanServiceError(
            f'"{field_name}" must be a list of repo-relative paths.',
            code="invalid_tracked_path",
        )
    return sorted({_normalize_tracked_path(value, field_name=field_name) for value in values})


def sync_tracked_paths_from_constants(*, using: str | None = None) -> None:
    """Synchronize TrackedPath rows from the generated constants allowlist.

    Paths in the allowlist are marked ``current``; rows that were ``current`` but
    have dropped out of the allowlist become ``historical`` (they once existed).
    ``planned`` rows are left untouched -- they name paths that do not exist yet.
    """
    manager = _manager(models.TrackedPath, using)
    current = dict.fromkeys(TRACKED_FILE_PATHS, False)
    current.update(dict.fromkeys(TRACKED_DIRECTORY_PATHS, True))
    existing_paths = set(manager.filter(path__in=current).values_list("path", flat=True))
    for path in sorted(set(current) - existing_paths):
        manager.create(
            path=path,
            state=models.TRACKED_PATH_CURRENT,
            is_directory=current[path],
        )
    manager.filter(path__in=current).exclude(state=models.TRACKED_PATH_CURRENT).update(
        state=models.TRACKED_PATH_CURRENT,
    )
    manager.exclude(path__in=current).filter(state=models.TRACKED_PATH_CURRENT).update(
        state=models.TRACKED_PATH_HISTORICAL,
    )


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
            code="unknown_tracked_path",
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
    with ``state="planned"`` and ``is_directory`` derived from the trailing ``/``.
    """
    normalized_paths = _tracked_paths(paths, field_name=field_name)
    if not normalized_paths:
        return []

    sync_tracked_paths_from_constants(using=using)
    manager = _manager(models.TrackedPath, using)
    for path in normalized_paths:
        manager.get_or_create(
            path=path,
            defaults={"state": models.TRACKED_PATH_PLANNED, "is_directory": path.endswith("/")},
        )
    return list(manager.filter(path__in=normalized_paths).order_by("path"))


def set_card_changed_files(card: models.Card, paths: object) -> None:
    """Replace a DONE card's actually-changed tracked paths (strict allowlist).

    Links carry ``kind=changed`` (the files the card actually changed).
    """
    using = _database_alias(card)
    card.changed_files.set(
        tracked_paths_for_paths(paths, using=using),
        through_defaults={"kind": models.CARD_PATH_LINK_CHANGED},
    )
    # ``through_defaults`` only applies ``kind`` to newly-created links; links
    # retained across a re-import keep their old kind, so a predicted->changed
    # flip would be lost. Force the kind on every surviving link.
    card.path_links.exclude(kind=models.CARD_PATH_LINK_CHANGED).update(
        kind=models.CARD_PATH_LINK_CHANGED,
    )


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
            code="predicted_files_on_done_card",
        )
    using = _database_alias(card)
    card.changed_files.set(
        planned_tracked_paths_for_paths(paths, using=using, field_name=field_name),
        through_defaults={"kind": models.CARD_PATH_LINK_PREDICTED},
    )
    # ``through_defaults`` only applies ``kind`` to newly-created links; force the
    # kind on retained links too so a changed->predicted flip is not lost.
    card.path_links.exclude(kind=models.CARD_PATH_LINK_PREDICTED).update(
        kind=models.CARD_PATH_LINK_PREDICTED,
    )


def _default_priority(using: str | None) -> models.Priority:
    """Return the lowest-``order`` Priority row (the default for cards omitting one).

    ``Card.priority`` is non-null, so a card spec without an explicit priority
    falls back to the highest-ranked (lowest ``order``) priority.
    """
    priority = _manager(models.Priority, using).order_by("order", "pk").first()
    if priority is None:
        raise KanbanServiceError(
            "Cannot create a card: no Priority rows exist to default to.",
            code="no_default_priority",
        )
    return priority


def _require_fields(spec: dict[str, Any], fields: tuple[str, ...]) -> None:
    for field in fields:
        if not spec.get(field):
            raise KanbanServiceError(
                f'Card is missing required field "{field}".',
                code="missing_required_field",
            )


def _resolve_by_title(card_manager, title: str) -> models.Card | None:
    """Resolve a card by its (today-unique) title.

    Uses ``.get()`` so a future duplicate title fails loudly with
    ``code="ambiguous_card"`` rather than silently picking the first row.
    """
    try:
        return card_manager.get(title=title)
    except models.Card.DoesNotExist:
        return None
    except models.Card.MultipleObjectsReturned as error:
        raise KanbanServiceError(
            f"Card title {title!r} is ambiguous; multiple cards share it.",
            code="ambiguous_card",
        ) from error


def _resolve_by_uuid(card_manager, value: object) -> models.Card:
    """Resolve a card by its UUIDModel primary key (reached via the ``uuid`` O2O)."""
    try:
        parsed = uuid.UUID(str(value))
    except (ValueError, AttributeError, TypeError) as error:
        raise KanbanServiceError(
            f"Invalid card uuid: {value!r}.",
            code="unresolvable_card",
        ) from error
    card = card_manager.filter(uuid__id=parsed).first()
    if card is None:
        raise KanbanServiceError(
            f"Cannot resolve card uuid: {value!r}.",
            code="unresolvable_card",
        )
    return card


def _resolve_by_slug(card_manager, value: object) -> models.Card:
    """Resolve a card by its derived slug (``slugify(title).replace('-', '_')``).

    ``slug`` is a pure function of ``title`` and is not stored, so it cannot be
    reversed by a query. The board is tiny (63 cards), so a single linear scan of
    ``(id, title)`` re-slugifying each title is fine and deterministic.
    """
    target = str(value)
    for pk, title in card_manager.values_list("id", "title"):
        if slugify(title).replace("-", "_") == target:
            return card_manager.get(pk=pk)
    raise KanbanServiceError(
        f"Cannot resolve card slug: {value!r}.",
        code="unresolvable_card",
    )


def _resolve_card_scalar(identifier: object, card_manager) -> models.Card:
    """Resolve a card by exact title, then by integer board number."""
    if isinstance(identifier, str):
        card = _resolve_by_title(card_manager, identifier)
        if card is not None:
            return card
    number = None
    if isinstance(identifier, int) and not isinstance(identifier, bool):
        number = identifier
    elif isinstance(identifier, str) and identifier.isdigit():
        # ``isdigit`` accepts unicode digits and arbitrarily long strings that
        # ``int`` rejects (superscripts, >4300 digits); fall through to the
        # unresolvable error rather than leaking the ValueError.
        try:
            number = int(identifier)
        except ValueError:
            number = None
    if number is not None:
        card = card_manager.filter(number=number).first()
        if card is not None:
            return card
    raise KanbanServiceError(
        f"Cannot resolve card reference: {identifier!r} (use the card title).",
        code="unresolvable_card",
    )


def resolve_card(identifier: object, *, using: str | None = None) -> models.Card:
    """Resolve a card from a stable id, a scalar, or an import-spec mapping.

    Accepts an ``int`` board number, a ``str`` title (or digit-string number), or
    a mapping carrying one of ``uuid`` / ``slug`` (the stable ids the exports
    publish, tried first) or ``card`` / ``title`` / ``number``. Unknown ids raise
    ``code="unresolvable_card"``; a duplicate title raises ``code="ambiguous_card"``.
    """
    card_manager = _manager(models.Card, using)
    if isinstance(identifier, dict):
        if "uuid" in identifier:
            return _resolve_by_uuid(card_manager, identifier["uuid"])
        if "slug" in identifier:
            return _resolve_by_slug(card_manager, identifier["slug"])
        for key in ("card", "title", "number"):
            if key in identifier:
                return _resolve_card_scalar(identifier[key], card_manager)
        raise KanbanServiceError(
            'Card spec must include one of "uuid", "slug", "card", "title", or "number".',
            code="unresolvable_card",
        )
    return _resolve_card_scalar(identifier, card_manager)


def _target_number(spec: dict[str, Any], using: str | None) -> int:
    if spec.get("number") is not None:
        try:
            return int(spec["number"])
        except (TypeError, ValueError) as error:
            raise KanbanServiceError(
                '"number" must be an integer when provided.',
                code="invalid_card_number",
            ) from error
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


def add_dependency(
    source_card: models.Card,
    target_card: models.Card,
    *,
    kind: str = DEPENDENCY_REFERENCE_KIND_KEY,
    raw_text: str = "",
) -> models.CardReference:
    """Add a dependency edge from ``source_card`` to ``target_card``.

    The sanctioned write API for card-to-card dependency edges. Cycle detection
    and the lower-number-ordering rule are enforced by the ``CardReference``
    ``pre_save`` guard, so direct ORM writes stay safe too. ``kind`` must be a
    dependency-shaped reference kind (``dependency`` or ``blocked_by``).
    """
    if kind not in models.DEPENDENCY_REFERENCE_KIND_KEYS:
        valid = ", ".join(sorted(models.DEPENDENCY_REFERENCE_KIND_KEYS))
        raise KanbanServiceError(
            f"add_dependency kind must be one of: {valid} (got {kind!r}).",
            code="invalid_dependency_kind",
        )
    using = _database_alias(source_card, target_card)
    kind_row = _lookup(models.CardReferenceKind, kind, using)
    return append_card_reference(
        source_card=source_card,
        target_card=target_card,
        kind=kind_row,
        raw_text=raw_text,
    )


def remove_dependency(
    source_card: models.Card,
    target_card: models.Card,
    *,
    kind: str | None = None,
) -> int:
    """Remove dependency edge(s) from ``source_card`` to ``target_card``.

    Deletes matching dependency-shaped ``CardReference`` rows. When ``kind`` is
    omitted, every dependency/blocked_by edge between the two cards is removed.
    Returns the number of references deleted.
    """
    using = _database_alias(source_card, target_card)
    queryset = _manager(models.CardReference, using).filter(
        source_card=source_card,
        target_card=target_card,
        kind__key__in=models.DEPENDENCY_REFERENCE_KIND_KEYS,
    )
    if kind is not None:
        queryset = queryset.filter(kind__key=kind)
    count = queryset.count()
    queryset.delete()
    return count


# ---------------------------------------------------------------------------
# Board-number renumbering engine (moved out of signals.py)
# ---------------------------------------------------------------------------


def _project_neighbor_number(number: int, old_number: int, requested_number: int) -> int:
    """Where a neighbour at ``number`` lands after the moved card goes to ``requested``."""
    if requested_number < old_number and requested_number <= number < old_number:
        return number + 1
    if old_number < requested_number and old_number < number <= requested_number:
        return number - 1
    return number


def _dependency_numbers(card_id: int, using: str | None) -> list[int]:
    """Board numbers of the cards ``card_id`` depends on (outgoing dependency edges)."""
    return list(
        _manager(models.Card, using)
        .filter(
            incoming_references__source_card_id=card_id,
            incoming_references__kind__key__in=models.DEPENDENCY_REFERENCE_KIND_KEYS,
        )
        .distinct()
        .values_list("number", flat=True),
    )


def _dependent_numbers(card_id: int, using: str | None) -> list[int]:
    """Board numbers of the cards that depend on ``card_id`` (reverse edges)."""
    return list(
        _manager(models.Card, using)
        .filter(
            outgoing_references__target_card_id=card_id,
            outgoing_references__kind__key__in=models.DEPENDENCY_REFERENCE_KIND_KEYS,
        )
        .distinct()
        .values_list("number", flat=True),
    )


def _validate_move_dependency_order(
    card_id: int,
    old_number: int,
    requested_number: int,
    using: str | None,
) -> None:
    """Reject a move that would place a dependency at/after its dependent card.

    Projects every dependency and dependent through the shift the move induces
    and checks the lower-number-first ordering still holds afterwards.
    """
    for dependency_number in _dependency_numbers(card_id, using):
        final = _project_neighbor_number(dependency_number, old_number, requested_number)
        if final >= requested_number:
            raise KanbanServiceError(CARD_DEPENDENCY_ORDER_MESSAGE, code="dependency_order")
    for dependent_number in _dependent_numbers(card_id, using):
        final = _project_neighbor_number(dependent_number, old_number, requested_number)
        if final <= requested_number:
            raise KanbanServiceError(CARD_DEPENDENCY_ORDER_MESSAGE, code="dependency_order")


def move_card_number(card: models.Card, number: int, *, using: str | None = None) -> models.Card:
    """Move ``card`` to board ``number``, shifting neighbours to keep the sequence gap-free.

    The sanctioned writer for board-number changes on an existing card. A direct
    ``card.save()`` that changes ``number`` is rejected by the
    ``prepare_card_save`` guard, which points here. Neighbour rows are shifted
    with per-row ``.update()`` (never ``save()``), so their ``updated_date`` and
    the ``Card`` signals do not churn on every reorder.

    Validation raises :class:`KanbanServiceError`: ``card_number_out_of_range``
    for an out-of-range / gap-inducing target, ``dependency_order`` when the move
    would break the dependency-before-dependent ordering.
    """
    using = using if using is not None else _database_alias(card)
    try:
        requested = int(number)
    except (TypeError, ValueError) as error:
        raise KanbanServiceError(
            '"number" must be an integer.',
            code="invalid_card_number",
        ) from error
    card_manager = _manager(models.Card, using)
    with transaction.atomic(using=using):
        old_number = card_manager.filter(pk=card.pk).values_list("number", flat=True).first()
        if old_number is None:
            raise KanbanServiceError(
                f"Cannot move card pk={card.pk!r}: it has no stored board number.",
                code="unknown_card",
            )
        max_number = card_manager.aggregate(value=Max("number"))["value"] or 0
        if requested < 1 or requested > max_number:
            raise KanbanServiceError(
                f"Card number must be between 1 and {max_number} (got {requested}).",
                code="card_number_out_of_range",
            )
        if requested == old_number:
            card.number = requested
            return card
        _validate_move_dependency_order(card.pk, old_number, requested, using)
        # Park the moved card above the sequence so shifting a neighbour into the
        # vacated slot cannot transiently collide with the unique ``number``.
        card_manager.filter(pk=card.pk).update(number=max_number + 1)
        if requested < old_number:
            neighbors = (
                card_manager.filter(number__gte=requested, number__lt=old_number)
                .exclude(pk=card.pk)
                .order_by("-number")
            )
            delta = 1
        else:
            neighbors = (
                card_manager.filter(number__gt=old_number, number__lte=requested)
                .exclude(pk=card.pk)
                .order_by("number")
            )
            delta = -1
        for neighbor_pk, neighbor_number in list(neighbors.values_list("pk", "number")):
            card_manager.filter(pk=neighbor_pk).update(number=neighbor_number + delta)
        card_manager.filter(pk=card.pk).update(number=requested)
    card.number = requested
    return card


def compact_card_numbers(card: models.Card, *, using: str | None = None) -> None:
    """Close the gap a just-deleted ``card`` left, shifting higher numbers down by one.

    Called by the ``post_delete`` receiver (the signal delegates here). Shifts
    with per-row ``.update()`` in ascending order, so each vacated slot is filled
    before the next row moves and the unique ``number`` never collides.
    """
    using = using if using is not None else _database_alias(card)
    card_manager = _manager(models.Card, using)
    rows = list(
        card_manager.filter(number__gt=card.number).order_by("number").values_list("pk", "number"),
    )
    for shifted_pk, shifted_number in rows:
        card_manager.filter(pk=shifted_pk).update(number=shifted_number - 1)


def _resolve_actor(actor: object, using: str | None) -> models.Actor:
    """Resolve an ``Actor`` from an instance or a ``key`` string."""
    if isinstance(actor, models.Actor):
        return actor
    if isinstance(actor, str):
        return _lookup(models.Actor, actor, using)
    raise KanbanServiceError("An Actor instance or key is required.", code="invalid_actor")


def set_card_status(
    card: models.Card,
    status_key: str,
    *,
    actor: object,
    note: str = "",
) -> models.CardTransition:
    """Move a card to ``status_key``, recording a :class:`~models.CardTransition`.

    The sanctioned writer for card status changes (2F). The transition legality
    is enforced by the ``prepare_card_save`` signal guard (the state machine), so
    this service does not re-validate; it adds atomic transition logging and the
    dependency-resolution hook (2G). When a card flips to ``done``, every
    unresolved incoming ``blocked_by`` edge is stamped ``resolved_at`` (the edge
    is preserved, not retyped), clearing the block on the cards that waited on it.
    When a ``done`` card is reopened, those stamps are cleared again so the
    edges become live blocks.

    ``actor`` is an :class:`~models.Actor` instance or its ``key``. Raises
    ``ValidationError`` on an illegal transition and ``KanbanServiceError`` when
    the card is already in the requested status.
    """
    using = _database_alias(card)
    actor_row = _resolve_actor(actor, using)
    new_status = _lookup(models.Status, status_key, using)
    with transaction.atomic(using=using):
        card.refresh_from_db()
        from_status = card.status
        if from_status.pk == new_status.pk:
            raise KanbanServiceError(
                f"Card {card.card_id!r} is already in status {status_key!r}.",
                code="already_in_status",
            )
        card.status = new_status
        card.save(update_fields=["status", "updated_date"])
        if new_status.key == DONE_STATUS_KEY:
            _manager(models.CardReference, using).filter(
                target_card=card,
                kind__key__in=models.BLOCKING_REFERENCE_KIND_KEYS,
                resolved_at__isnull=True,
            ).update(resolved_at=timezone.now())
        elif from_status.key == DONE_STATUS_KEY:
            # Reopen: the card has un-shipped, so incoming ``blocked_by`` edges
            # it previously resolved become live blocks again. Clearing the
            # stamp keeps ``is_blocked`` and ``is_ready`` consistent.
            _manager(models.CardReference, using).filter(
                target_card=card,
                kind__key__in=models.BLOCKING_REFERENCE_KIND_KEYS,
                resolved_at__isnull=False,
            ).update(resolved_at=None)
        return _manager(models.CardTransition, using).create(
            card=card,
            from_status=from_status,
            to_status=new_status,
            actor=actor_row,
            note=note,
        )


# ---------------------------------------------------------------------------
# CardItem progress + verification writers
# ---------------------------------------------------------------------------


def set_item_complete(
    item: models.CardItem,
    complete: bool = True,
    *,
    actor: object = None,
) -> models.CardItem:
    """Set a card item's ``is_complete`` checkbox (the general per-bullet flag).

    ``actor`` is accepted for call-site symmetry with :func:`verify_item`; a bare
    completion carries no verification provenance, so it is not persisted here --
    record who verified a bullet (and how) with :func:`verify_item`.
    """
    item.is_complete = complete
    item.save(update_fields=["is_complete", "updated_date"])
    return item


def verify_item(
    item: models.CardItem,
    *,
    actor: object,
    kind: object,
    at: object = None,
) -> models.CardItem:
    """Record auditable verification of a card item and mark it complete.

    Stamps ``verified_at`` / ``verified_by`` / ``verification_kind`` and forces
    ``is_complete=True`` -- a verified bullet is by definition done. ``actor`` is
    an :class:`~models.Actor` instance or key; ``kind`` a
    :class:`~models.VerificationKind` instance or key; ``at`` defaults to now.
    """
    using = _database_alias(item)
    actor_row = _resolve_actor(actor, using)
    kind_row = (
        kind
        if isinstance(kind, models.VerificationKind)
        else _lookup(models.VerificationKind, kind, using)
    )
    item.verified_at = at if at is not None else timezone.now()
    item.verified_by = actor_row
    item.verification_kind = kind_row
    item.is_complete = True
    item.save(
        update_fields=[
            "verified_at",
            "verified_by",
            "verification_kind",
            "is_complete",
            "updated_date",
        ],
    )
    return item


# ---------------------------------------------------------------------------
# Work-tracking writers (attempts + decisions)
# ---------------------------------------------------------------------------


def record_attempt(
    card: models.Card,
    *,
    actor: object,
    summary: str,
    evidence: str = "",
    started_at: object = None,
) -> models.WorkAttempt:
    """Open a :class:`~models.WorkAttempt` on ``card`` (a try, still in progress).

    The attempt has a null ``outcome`` / ``ended_at`` until :func:`finish_attempt`
    closes it. ``started_at`` defaults to the model's ``timezone.now`` default.
    """
    using = _database_alias(card)
    actor_row = _resolve_actor(actor, using)
    fields: dict[str, Any] = {
        "card": card,
        "actor": actor_row,
        "summary": summary,
        "evidence": evidence,
    }
    if started_at is not None:
        fields["started_at"] = started_at
    return _manager(models.WorkAttempt, using).create(**fields)


def finish_attempt(
    attempt: models.WorkAttempt,
    *,
    outcome_key: str,
    summary: str | None = None,
    ended_at: object = None,
) -> models.WorkAttempt:
    """Close a :class:`~models.WorkAttempt`, stamping its outcome and ``ended_at``.

    ``outcome_key`` names an :class:`~models.AttemptOutcome` row; ``summary``
    overwrites the running summary when provided; ``ended_at`` defaults to now.
    """
    using = _database_alias(attempt)
    outcome = _lookup(models.AttemptOutcome, outcome_key, using)
    attempt.outcome = outcome
    attempt.ended_at = ended_at if ended_at is not None else timezone.now()
    update_fields = ["outcome", "ended_at", "updated_date"]
    if summary is not None:
        attempt.summary = summary
        update_fields.append("summary")
    attempt.save(update_fields=update_fields)
    return attempt


def record_decision(
    *,
    actor: object,
    question: str,
    choice: str,
    rationale: str = "",
    card: models.Card | None = None,
    supersedes: models.Decision | None = None,
) -> models.Decision:
    """Record a design :class:`~models.Decision`, board-level or scoped to a card.

    ``card`` is null for a board-level decision; ``supersedes`` links the earlier
    decision this one replaces (surfaced in reverse as ``superseded_by_set``).
    """
    instances = [
        instance
        for instance in (card, supersedes, actor)
        if isinstance(instance, django_models.Model)
    ]
    using = _database_alias(*instances)
    actor_row = _resolve_actor(actor, using)
    return _manager(models.Decision, using).create(
        card=card,
        actor=actor_row,
        question=question,
        choice=choice,
        rationale=rationale,
        supersedes=supersedes,
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
        raise KanbanServiceError(
            f"A card titled {title!r} already exists.",
            code="duplicate_card_title",
        )
    if isinstance(spec.get("sections"), dict) and "dependencies" in spec["sections"]:
        raise KanbanServiceError(
            'Put dependencies under the top-level "dependencies" key, not "sections".',
            code="dependencies_in_sections",
        )

    status_key = spec.get("status", DEFAULT_STATUS_KEY)
    if status_key == DONE_STATUS_KEY:
        raise KanbanServiceError(
            'Kanban card creation cannot create "done" cards because done cards require '
            "a linked spec doc. Import the card before marking it done.",
            code="cannot_create_done_card",
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
            target_version=target_version,
            priority=(
                _lookup(models.Priority, spec["priority"], using)
                if spec.get("priority")
                else _default_priority(using)
            ),
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
