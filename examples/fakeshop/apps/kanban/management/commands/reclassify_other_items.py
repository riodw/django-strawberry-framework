"""manage.py reclassify_other_items - move ``other`` card items to real sections.

Executes the signed-off Phase 0.5 reclassification (see
``kanban-section-other-report.md``): a JSON mapping file assigns each of the 378
card items currently parked in the dumping-ground ``other`` section to one of
eleven real target sections. This command applies that mapping and nothing else.

The mapping is the sole source of truth (built by resolving the report's
``(card, order)`` pairs to ``CardItem`` uuids); this command never re-runs the
classification heuristics. Every write goes through ``.update()`` (not
``.save()``) so the ``updated_date`` audit column and the model ``save`` signal
side effects do not fire -- the same pattern migration 0005 uses for pure data
repairs.

Idempotency: an item is moved only while it still lives in ``other``; a re-run
skips items already relocated. Processing is deterministic (sorted by
``(card_number, orig_order)``) so re-runs and the ``--rollback`` inverse behave
predictably. Item ``text`` travels verbatim -- ``{{card_ref:N}}`` placeholders
resolve against ``CardReference.order``, never ``CardItem.order``, so moving an
item cannot break a placeholder.

Usage::

    uv run python examples/fakeshop/manage.py reclassify_other_items \\
        --mapping section-other-mapping.json
    uv run python examples/fakeshop/manage.py reclassify_other_items \\
        --mapping section-other-mapping.json --dry-run
    uv run python examples/fakeshop/manage.py reclassify_other_items \\
        --mapping section-other-mapping.json --rollback

Mapping schema: a JSON array of objects, each with ``carditem_uuid``,
``card_number``, ``orig_order``, ``target_section_key``, ``text_prefix``.
"""

import argparse
import json
import pathlib

from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.db import connections, transaction

from apps.kanban import models

OTHER_KEY = "other"

# Mirror scripts/_kanban_lib.py: wait for a competing writer to release the
# SQLite lock instead of failing immediately with ``database is locked``.
SQLITE_BUSY_TIMEOUT_MS = 5000


class _DryRunRollbackError(Exception):
    """Internal sentinel used to roll back the transaction in --dry-run mode."""


class Command(BaseCommand):
    """Move card items out of the ``other`` section per a signed-off mapping."""

    help = "Reclassify the parked ``other`` card items into their real sections."

    def add_arguments(self, parser: CommandParser) -> None:
        """Register --mapping, --dry-run, --rollback, and --compact/--no-compact."""
        parser.add_argument(
            "--mapping",
            required=True,
            help="Path to the section-other-mapping.json file.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Validate and report the plan without writing to the database.",
        )
        parser.add_argument(
            "--rollback",
            action="store_true",
            help="Reverse the mapping: move items back into ``other``.",
        )
        parser.add_argument(
            "--compact",
            action=argparse.BooleanOptionalAction,
            default=True,
            help="Renumber surviving ``other`` items per card contiguously from 0.",
        )

    def _load(self, path: str) -> list[dict]:
        """Read and lightly validate the mapping file."""
        file_path = pathlib.Path(path)
        if not file_path.is_file():
            raise CommandError(f"Mapping file not found: {path}")
        try:
            payload = json.loads(file_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise CommandError(f"Invalid JSON in {path}: {error}") from error
        if not isinstance(payload, list) or not payload:
            raise CommandError("Mapping must be a non-empty JSON array.")
        uuids = {row["carditem_uuid"] for row in payload}
        if len(uuids) != len(payload):
            raise CommandError("Mapping contains duplicate carditem_uuid rows.")
        return sorted(payload, key=lambda row: (row["card_number"], row["orig_order"]))

    def _sections(self, keys: set[str]) -> dict[str, models.Section]:
        """Resolve every target key (plus ``other``) to a ``Section`` row."""
        wanted = keys | {OTHER_KEY}
        found = {s.key: s for s in models.Section.objects.filter(key__in=wanted)}
        missing = wanted - set(found)
        if missing:
            raise CommandError(
                f"Missing Section rows (run migration 0015 first): {sorted(missing)}",
            )
        return found

    def _next_order(self, card_id: int, section_id: int) -> int:
        """Return ``max(order) + 1`` within one ``(card, section)`` (0 if empty)."""
        highest = (
            models.CardItem.objects.filter(card_id=card_id, section_id=section_id)
            .order_by("-order")
            .values_list("order", flat=True)
            .first()
        )
        return 0 if highest is None else highest + 1

    def _move(
        self,
        rows: list[dict],
        sections: dict[str, models.Section],
        rollback: bool,
    ) -> list[str]:
        """Apply the mapping (forward or reverse); return moved-item descriptions."""
        moved: list[str] = []
        other = sections[OTHER_KEY]
        for row in rows:
            try:
                item = models.CardItem.objects.select_related("section", "card").get(
                    uuid__id=row["carditem_uuid"],
                )
            except models.CardItem.DoesNotExist:
                continue
            target = sections[row["target_section_key"]]
            if rollback:
                # Only pull back items still sitting where we placed them.
                if item.section_id != target.id:
                    continue
                destination = other
            else:
                # Idempotent: skip anything already relocated out of ``other``.
                if item.section.key != OTHER_KEY:
                    continue
                destination = target
            next_order = self._next_order(item.card_id, destination.id)
            models.CardItem.objects.filter(pk=item.pk).update(
                section=destination,
                order=next_order,
            )
            moved.append(
                f"card {row['card_number']} #{row['orig_order']} "
                f"-> {destination.key} #{next_order}",
            )
        return moved

    def _compact(self, card_ids: set[int], sections: dict[str, models.Section]) -> int:
        """Renumber each card's surviving ``other`` items contiguously from 0."""
        other = sections[OTHER_KEY]
        renumbered = 0
        for card_id in sorted(card_ids):
            survivors = list(
                models.CardItem.objects.filter(
                    card_id=card_id,
                    section_id=other.id,
                ).order_by("order", "id"),
            )
            for new_order, item in enumerate(survivors):
                if item.order != new_order:
                    models.CardItem.objects.filter(pk=item.pk).update(order=new_order)
                    renumbered += 1
        return renumbered

    def handle(self, *args: object, **options: object) -> None:
        """Move the mapped items inside one transaction; honor --dry-run."""
        rows = self._load(options["mapping"])
        dry_run = options["dry_run"]
        rollback = options["rollback"]
        compact = options["compact"]
        sections = self._sections({row["target_section_key"] for row in rows})
        card_ids = {row["card_number"] for row in rows}
        # ``card_number`` is the human number; resolve to pk-space card ids.
        card_pks = set(
            models.Card.objects.filter(number__in=card_ids).values_list("id", flat=True),
        )

        alias = "default"
        with connections[alias].cursor() as cursor:
            cursor.execute(f"PRAGMA busy_timeout = {SQLITE_BUSY_TIMEOUT_MS};")

        moved: list[str] = []
        compacted = 0
        try:
            with transaction.atomic(using=alias):
                moved = self._move(rows, sections, rollback)
                if compact:
                    compacted = self._compact(card_pks, sections)
                if dry_run:
                    raise _DryRunRollbackError
        except _DryRunRollbackError:
            self.stdout.write(
                self.style.WARNING(
                    f"Dry run - rolled back. Would move {len(moved)} item(s), "
                    f"compact {compacted} order(s).",
                ),
            )
            for line in moved:
                self.stdout.write(f"  {line}")
            return

        verb = "Rolled back" if rollback else "Moved"
        self.stdout.write(
            self.style.SUCCESS(
                f"{verb} {len(moved)} item(s); renumbered {compacted} ``other`` order(s).",
            ),
        )
