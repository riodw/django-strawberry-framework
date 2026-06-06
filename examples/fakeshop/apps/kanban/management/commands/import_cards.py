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
            {"target": "...", "kind": "related",
             "source": "card_item", "text": "..."}
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
  ``dependencies_section`` reference (which auto-syncs the ``dependencies`` M2M
  via signals) AND the rendered "Dependencies" prose bullet. Do not also list a
  ``dependencies`` key under ``sections``.
"""

import json
import pathlib

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.db import transaction

from apps.kanban import models, services

DEFAULT_STATUS = "todo"
DEFAULT_PLANNING_STATE = "planned"


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

    def _lookup(
        self,
        model,
        key: str,
        field: str = "key",
    ):
        """Resolve a lookup row by ``key``; raise a CommandError listing valid keys."""
        try:
            return model.objects.get(**{field: key})
        except model.DoesNotExist:
            valid = ", ".join(
                sorted(model.objects.values_list(field, flat=True).distinct()),
            )
            raise CommandError(
                f"Unknown {model.__name__} {field}={key!r}. Valid values: {valid}",
            ) from None

    def _resolve_card(self, identifier) -> models.Card:
        """Resolve a card by exact title, then by integer board number."""
        if isinstance(identifier, str):
            card = models.Card.objects.filter(title=identifier).first()
            if card is not None:
                return card
        if isinstance(identifier, int) or (isinstance(identifier, str) and identifier.isdigit()):
            card = models.Card.objects.filter(number=int(identifier)).first()
            if card is not None:
                return card
        raise CommandError(f"Cannot resolve card reference: {identifier!r} (use the card title).")

    def _target_number(self, spec: dict) -> int:
        """Compute the requested board number for a new card."""
        if spec.get("number") is not None:
            try:
                return int(spec["number"])
            except (TypeError, ValueError) as error:
                raise CommandError('"number" must be an integer when provided.') from error
        elif spec.get("after") is not None:
            return self._resolve_card(spec["after"]).number + 1
        else:
            highest = models.Card.objects.order_by("-number").first()
            return (highest.number + 1) if highest else 1

    # -- per-card creation -----------------------------------------------

    def _create_card(self, spec: dict) -> models.Card:
        for required in ("title", "target_version", "relative_size"):
            if not spec.get(required):
                raise CommandError(f'Card is missing required field "{required}".')
        title = spec["title"]
        if models.Card.objects.filter(title=title).exists():
            raise CommandError(f"A card titled {title!r} already exists.")
        if isinstance(spec.get("sections"), dict) and "dependencies" in spec["sections"]:
            raise CommandError(
                'Put dependencies under the top-level "dependencies" key, not "sections".',
            )

        status_key = spec.get("status", DEFAULT_STATUS)
        if status_key == "done":
            raise CommandError(
                'Card imports cannot create "done" cards because done cards require '
                "a linked spec doc. Import the card before marking it done.",
            )

        target_version = self._lookup(models.TargetVersion, spec["target_version"], field="number")
        size_high = None
        if spec.get("relative_size_high"):
            size_high = self._lookup(models.RelativeSize, spec["relative_size_high"])

        card = models.Card.objects.create(
            title=title,
            number=self._target_number(spec),
            status=self._lookup(models.Status, status_key),
            milestone=target_version.milestone,
            target_version=target_version,
            priority=self._lookup(models.Priority, spec["priority"])
            if spec.get("priority")
            else None,
            severity=self._lookup(models.Severity, spec["severity"])
            if spec.get("severity")
            else None,
            relative_size=self._lookup(models.RelativeSize, spec["relative_size"]),
            relative_size_high=size_high,
            planning_state=self._lookup(
                models.PlanningState,
                spec.get("planning_state", DEFAULT_PLANNING_STATE),
            ),
            planning_note=spec.get("planning_note", ""),
        )

        for label_key in spec.get("labels", []):
            card.labels.add(self._lookup(models.Label, label_key))

        for claim in spec.get("parity", []):
            models.ParityClaim.objects.create(
                card=card,
                upstream=self._lookup(models.Upstream, claim["upstream"]),
                level=self._lookup(models.ParityLevel, claim["level"]),
            )

        self._create_sections(card, spec.get("sections", {}))
        self._create_dependencies(card, spec.get("dependencies", []))
        self._create_references(card, spec.get("references", []))
        return card

    def _create_sections(self, card: models.Card, sections: dict) -> None:
        for section_key, bullets in sections.items():
            section = self._lookup(models.Section, section_key)
            for order, bullet in enumerate(bullets):
                if isinstance(bullet, dict):
                    text, done = bullet.get("text", ""), bool(bullet.get("done", False))
                else:
                    text, done = bullet, False
                services.append_card_item(
                    card=card,
                    section=section,
                    text=text,
                    order=order,
                    is_complete=done,
                )

    def _create_dependencies(self, card: models.Card, dependencies: list) -> None:
        """Create dependency notes through the kanban app workflow service."""
        if not dependencies:
            return
        for order, dependency in enumerate(dependencies):
            target = self._resolve_card(dependency["card"])
            note = dependency.get("note", "")
            services.add_dependency_note(
                card=card,
                target_card=target,
                note=note,
                order=order,
            )

    def _create_references(self, card: models.Card, references: list) -> None:
        for reference in references:
            source = self._lookup(models.CardReferenceSource, reference["source"])
            services.append_card_reference(
                source_card=card,
                target_card=self._resolve_card(reference["target"]),
                kind=self._lookup(models.CardReferenceKind, reference.get("kind", "related")),
                source=source,
                raw_text=reference.get("text", ""),
            )

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
                        card = self._create_card(spec)
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
