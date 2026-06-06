"""manage.py import_cards — create kanban cards from a JSON file.

One JSON file describes one or more cards. The command resolves every lookup by
key, derives the milestone from the target version, chooses each card's requested
board position, and wires labels, parity, dependencies, section bullets, and card
references — handling the card-order and dependency/reference signal sync so
callers never touch the models or the DB directly.

Usage::

    uv run python examples/fakeshop/manage.py import_cards <file.json>
    uv run python examples/fakeshop/manage.py import_cards <file.json> --dry-run

After a real import, regenerate the rendered board::

    uv run python scripts/build_kanban_md.py
    uv run python scripts/build_kanban_html.py

JSON schema (see ``apps/kanban/card_import.example.json`` for a filled template)::

    {
      "cards": [
        {
          "title": "...",                  # required, unique
          "target_version": "0.1.2",       # required, TargetVersion.number
          "relative_size": "m",            # required, RelativeSize.key
          "relative_size_high": null,      # optional, RelativeSize.key (ranges)
          "status": "todo",                # optional (default "todo"; not "done")
          "priority": "medium",            # optional, Priority.key
          "severity": "medium",            # optional, Severity.key
          "planning_state": "planned",     # optional (default "planned")
          "planning_note": "...",          # optional
          "labels": ["filters"],           # optional, Label.key list
          "parity": [                      # optional
            {"upstream": "graphene_django", "level": "required"}
          ],
          "after": "Filtering subsystem",  # optional: insert after this card
          "number": 46,                    # optional: explicit board number
          "dependencies": [                # optional (drives M2M + refs + prose)
            {"card": "Filtering subsystem", "note": "why it depends"}
          ],
          "sections": {                    # optional, section_key -> [bullets]
            "scope": ["..."],
            "definition_of_done": [
              "plain bullet",
              {"text": "checkbox bullet", "done": false}
            ]
          },
          "references": [                  # optional, advanced extra refs
            {"target": "...", "kind": "related", "text": "..."}
          ]
        }
      ]
    }

Notes:

- ``after`` / ``number`` are both optional; omit both to append at the board end.
  ``number`` wins if both are given.
- Card identifiers (``after``, ``dependencies[].card``, ``references[].target``)
  match a card by exact ``title`` first, then by integer board ``number``.
- ``dependencies`` is the single source for a dependency edge: it creates the
  dependency-kind ``CardReference`` (which auto-syncs the ``dependencies`` M2M
  via signals) AND the rendered "Dependencies" prose bullet. Do not also list a
  ``dependencies`` key under ``sections``.
"""

import json
import pathlib

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.db import transaction

from apps.kanban import services


class _DryRunRollbackError(Exception):
    """Internal sentinel used to roll back the transaction in --dry-run mode."""


def _validation_error_message(error: ValidationError) -> str:
    return "; ".join(error.messages)


class Command(BaseCommand):
    """Create one or more kanban cards from a JSON description file."""

    help = "Create kanban cards from a JSON file (see --help for the schema)."

    def add_arguments(self, parser: CommandParser) -> None:
        """Register the positional JSON path and the --dry-run flag."""
        parser.add_argument("path", type=str, help="Path to the card JSON file.")
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Validate and report the plan without writing to the database.",
        )

    # -- helpers ----------------------------------------------------------

    def _load(self, path: str) -> list[dict]:
        file_path = pathlib.Path(path)
        if not file_path.is_file():
            raise CommandError(f"File not found: {path}")
        try:
            payload = json.loads(file_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            raise CommandError(f"Invalid JSON in {path}: {e}") from e
        cards = payload.get("cards") if isinstance(payload, dict) else None
        if not isinstance(cards, list) or not cards:
            raise CommandError('JSON must be an object with a non-empty "cards" array.')
        return cards

    # -- entrypoint -------------------------------------------------------

    def handle(self, *args: object, **options: object) -> None:
        """Load the JSON file and create each card inside one transaction."""
        cards = self._load(options["path"])
        dry_run = options["dry_run"]
        created: list[str] = []
        try:
            with transaction.atomic():
                for spec in cards:
                    try:
                        card = services.create_card_from_spec(spec)
                    except services.KanbanServiceError as error:
                        raise CommandError(str(error)) from error
                    except ValidationError as error:
                        title = spec.get("title", "<missing title>")
                        raise CommandError(
                            f"Invalid kanban card {title!r}: {_validation_error_message(error)}",
                        ) from error
                    created.append(str(card))
                if dry_run:
                    raise _DryRunRollbackError
        except _DryRunRollbackError:
            self.stdout.write(self.style.WARNING("Dry run — rolled back. Would create:"))
            for line in created:
                self.stdout.write(f"  {line}")
            return

        for line in created:
            self.stdout.write(self.style.SUCCESS(f"Created {line}"))
        self.stdout.write(
            "Now regenerate the board: "
            "uv run python scripts/build_kanban_md.py && "
            "uv run python scripts/build_kanban_html.py",
        )
