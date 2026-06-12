"""manage.py import_card_changed_files - replace kanban card package-file links.

One JSON file describes one or more existing cards and the package files each
card changed. The command resolves cards through the kanban service layer,
validates paths against the generated package-file constants plus historical
``PackageFile`` rows, and replaces each card's linked file set exactly.

Usage::

    uv run python examples/fakeshop/manage.py import_card_changed_files <file.json>
    uv run python examples/fakeshop/manage.py import_card_changed_files <file.json> --dry-run

JSON schema::

    {
      "cards": [
        {
          "card": "Filtering subsystem",
          "changed_files": [
            "django_strawberry_framework/filters/base.py"
          ]
        }
      ]
    }

``card`` may be a title or a board number. ``title`` and ``number`` are accepted
as aliases when a producer wants explicit field names.
"""

import json
import pathlib

from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.db import transaction

from apps.kanban import services


class _DryRunRollbackError(Exception):
    """Internal sentinel used to roll back the transaction in --dry-run mode."""


def _card_identifier(spec: dict) -> object:
    """Return the card identifier from one import spec."""
    for field in ("card", "title", "number"):
        if field in spec:
            return spec[field]
    raise CommandError('Each entry must include "card", "title", or "number".')


def _validate_spec(spec: object) -> dict:
    """Return a card spec dict after validating replacement-command shape."""
    if not isinstance(spec, dict):
        raise CommandError('Each entry in "cards" must be an object.')
    if "changed_files" not in spec:
        raise CommandError('Each entry must include "changed_files"; use [] to clear links.')
    return spec


class Command(BaseCommand):
    """Replace package-file links on existing kanban cards."""

    help = "Replace changed-file links for existing kanban cards."

    def add_arguments(self, parser: CommandParser) -> None:
        """Register the positional JSON path and the --dry-run flag."""
        parser.add_argument("path", type=str, help="Path to the card/file JSON file.")
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Validate and report the plan without writing to the database.",
        )

    def _load(self, path: str) -> list[dict]:
        file_path = pathlib.Path(path)
        if not file_path.is_file():
            raise CommandError(f"File not found: {path}")
        try:
            payload = json.loads(file_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise CommandError(f"Invalid JSON in {path}: {error}") from error
        cards = payload.get("cards") if isinstance(payload, dict) else None
        if not isinstance(cards, list) or not cards:
            raise CommandError('JSON must be an object with a non-empty "cards" array.')
        return cards

    def handle(self, *args: object, **options: object) -> None:
        """Load JSON and replace changed-file links inside one transaction."""
        specs = self._load(options["path"])
        dry_run = options["dry_run"]
        updated: list[str] = []
        try:
            with transaction.atomic():
                for spec in specs:
                    spec = _validate_spec(spec)
                    identifier = _card_identifier(spec)
                    try:
                        card = services.resolve_card(identifier)
                        services.set_card_changed_files(card, spec.get("changed_files", []))
                    except services.KanbanServiceError as error:
                        raise CommandError(str(error)) from error
                    updated.append(str(card))
                if dry_run:
                    raise _DryRunRollbackError
        except _DryRunRollbackError:
            self.stdout.write(self.style.WARNING("Dry run - rolled back. Would update:"))
            for line in updated:
                self.stdout.write(f"  {line}")
            return

        for line in updated:
            self.stdout.write(self.style.SUCCESS(f"Updated {line}"))
