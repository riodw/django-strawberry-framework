"""manage.py import_card_files - replace kanban card package/path links.

One JSON file describes one or more existing cards and the tracked files each
card links to. ``--kind changed`` records the files a DONE card actually changed
(strict allowlist); ``--kind predicted`` records the paths a WIP/TODO card is
predicted to touch (unknown paths under an approved root become planned
``TrackedPath`` rows). The command resolves cards through the kanban service
layer and replaces each card's linked file set exactly.

This single command supersedes the former ``import_card_changed_files`` /
``import_card_predicted_files`` pair (retired). The merged JSON key is
``files``.

Usage::

    uv run python examples/fakeshop/manage.py import_card_files <file.json> --kind changed
    uv run python examples/fakeshop/manage.py import_card_files <file.json> --kind predicted --dry-run

JSON schema::

    {
      "cards": [
        {
          "card": "Filtering subsystem",
          "files": [
            "django_strawberry_framework/filters/base.py"
          ]
        }
      ]
    }

Each entry identifies its card by a stable id (``uuid`` or ``slug`` -- the ids
the exports publish) or by ``card`` / ``title`` / ``number``. ``files`` is
required; pass ``[]`` to clear links.
"""

import json
import pathlib

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.db import transaction

from apps.kanban import models, services


class _DryRunRollbackError(Exception):
    """Internal sentinel used to roll back the transaction in --dry-run mode."""


class Command(BaseCommand):
    """Replace changed- or predicted-file links on existing kanban cards."""

    help = "Replace changed- or predicted-file links for existing kanban cards."

    # Aliases pin these; the merged command leaves ``fixed_kind`` unset so the
    # kind arrives via ``--kind`` and reads files from the canonical ``files`` key.
    fixed_kind: str | None = None
    files_key: str = "files"

    def add_arguments(self, parser: CommandParser) -> None:
        """Register the positional JSON path, --dry-run, and (unless pinned) --kind."""
        parser.add_argument("path", type=str, help="Path to the card/file JSON file.")
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Validate and report the plan without writing to the database.",
        )
        if self.fixed_kind is None:
            parser.add_argument(
                "--kind",
                required=True,
                choices=[models.CARD_PATH_LINK_CHANGED, models.CARD_PATH_LINK_PREDICTED],
                help="Whether the listed files are changed (DONE cards) or predicted.",
            )

    def _kind(self, options: dict) -> str:
        """Return the effective link kind (pinned by an alias or from --kind)."""
        return self.fixed_kind if self.fixed_kind is not None else options["kind"]

    def _validate_spec(self, spec: object) -> dict:
        """Return a card spec dict after validating replacement-command shape."""
        if not isinstance(spec, dict):
            raise CommandError('Each entry in "cards" must be an object.')
        if self.files_key not in spec:
            raise CommandError(
                f'Each entry must include "{self.files_key}"; use [] to clear links.',
            )
        return spec

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

    def _apply(
        self,
        card: models.Card,
        kind: str,
        paths: object,
    ) -> None:
        """Replace the card's linked files for the requested kind."""
        if kind == models.CARD_PATH_LINK_CHANGED:
            services.set_card_changed_files(card, paths)
        else:
            services.set_card_predicted_files(card, paths, field_name=self.files_key)

    def handle(self, *args: object, **options: object) -> None:
        """Load JSON and replace card-file links inside one transaction."""
        specs = self._load(options["path"])
        dry_run = options["dry_run"]
        kind = self._kind(options)
        updated: list[str] = []
        try:
            with transaction.atomic():
                for raw in specs:
                    spec = self._validate_spec(raw)
                    try:
                        card = services.resolve_card(spec)
                        self._apply(card, kind, spec.get(self.files_key, []))
                    except services.KanbanServiceError as error:
                        raise CommandError(str(error)) from error
                    except ValidationError as error:
                        # Signal guards raise django ValidationError; surface it
                        # as a CommandError instead of a raw traceback.
                        raise CommandError("; ".join(error.messages)) from error
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
