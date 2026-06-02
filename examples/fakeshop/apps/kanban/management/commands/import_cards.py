"""manage.py import_cards — create kanban cards from a JSON file.

One JSON file describes one or more cards. The command resolves every lookup by
key, derives the milestone from the target version, inserts each card at the
requested board position (renumbering the cards after it), and wires labels,
parity, dependencies, section bullets, and card references — handling the
dependency/reference signal sync so callers never touch the models or the DB
directly.

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

from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.db import transaction

from apps.kanban import models

DEFAULT_STATUS = "todo"
DEFAULT_PLANNING_STATE = "planned"
DEPENDENCY_SECTION_KEY = "dependencies_note"


class _DryRunRollbackError(Exception):
    """Internal sentinel used to roll back the transaction in --dry-run mode."""


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
        """Compute the board number for a new card and make room if inserting."""
        if spec.get("number") is not None:
            number = int(spec["number"])
        elif spec.get("after") is not None:
            number = self._resolve_card(spec["after"]).number + 1
        else:
            highest = models.Card.objects.order_by("-number").first()
            return (highest.number + 1) if highest else 1
        # Insert: shift everything at/after this slot up by one, highest first.
        for existing in models.Card.objects.filter(number__gte=number).order_by("-number"):
            existing.number += 1
            existing.save(update_fields=["number"])
        return number

    def _next_ref_order(self, card: models.Card, source: models.CardReferenceSource) -> int:
        return card.outgoing_references.filter(source=source).count()

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
                models.CardItem.objects.create(
                    card=card,
                    section=section,
                    text=text,
                    order=order,
                    is_complete=done,
                )

    def _create_dependencies(self, card: models.Card, dependencies: list) -> None:
        """Create the dependency edge, its reference, and its rendered prose bullet.

        Creating a ``dependency``-kind / ``dependencies_section`` reference
        auto-adds the ``dependencies`` M2M edge via the kanban signal, so we
        never call ``dependencies.add()`` (which would create a duplicate
        reference and collide on the unique (card, source, order) key).
        """
        if not dependencies:
            return
        source = self._lookup(models.CardReferenceSource, "dependencies_section")
        kind = self._lookup(models.CardReferenceKind, "dependency")
        section = self._lookup(models.Section, DEPENDENCY_SECTION_KEY)
        for order, dependency in enumerate(dependencies):
            target = self._resolve_card(dependency["card"])
            note = dependency.get("note", "")
            models.CardReference.objects.create(
                source_card=card,
                target_card=target,
                kind=kind,
                source=source,
                order=order,
                raw_text=note,
            )
            models.CardItem.objects.create(
                card=card,
                section=section,
                text=note,
                order=order,
                is_complete=False,
            )

    def _create_references(self, card: models.Card, references: list) -> None:
        for reference in references:
            source = self._lookup(models.CardReferenceSource, reference["source"])
            models.CardReference.objects.create(
                source_card=card,
                target_card=self._resolve_card(reference["target"]),
                kind=self._lookup(models.CardReferenceKind, reference.get("kind", "related")),
                source=source,
                order=self._next_ref_order(card, source),
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
                    card = self._create_card(spec)
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
