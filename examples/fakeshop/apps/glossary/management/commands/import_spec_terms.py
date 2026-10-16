"""Import spec companion CSVs into glossary mentions and done-card links.

The writing run makes every done card's ``GlossarySpecMention`` and ``CardGlossaryTerm``
rows equal its terms CSV and writes only the rows that differ, so a repeat run writes
nothing and an unchanged row keeps its ``updated_date``. Mention rows at a spec path no
done card's spec resolves to (left behind by a spec archive or a reopened card) are
deleted. ``--check`` compares every column the writing run sets and names, in one run,
every done card it cannot plan (missing CSV, repeated or unknown anchor, a spec another
done card already resolves to) and every row the writing run would create, update or
delete: it passes exactly when the writing run would write nothing. While any done card
cannot be planned the writing run writes nothing and fails, and ``--dry-run`` lists
everything and then fails the same way.
"""

from __future__ import annotations

import csv
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.db import transaction
from typing_extensions import override

from apps.glossary import models as glossary_models
from apps.kanban import models as kanban_models

REPO_ROOT = Path(__file__).resolve().parents[6]
SPEC_PATH_MARKER = "docs/"
# Subfolder holding an archived spec's companion files, beside the archived spec
COMPANION_DIRNAME = "appx"


@dataclass(frozen=True)
class TermRow:
    """One resolved row from a spec's ``*-terms.csv`` file."""

    term_text: str
    anchor: str
    notes: str
    order: int
    term: glossary_models.GlossaryTerm


@dataclass(frozen=True)
class CardPlan:
    """The CSV-backed glossary plan for one done kanban card."""

    card: kanban_models.Card
    spec_path: str
    terms_path: Path
    rows: tuple[TermRow, ...]


@dataclass(frozen=True)
class CardDelta:
    """The writes that make one done card's rows equal its plan.

    ``links_to_move`` are the kept links whose ``order`` changes; the writing run parks
    them, and the links it deletes, above ``free_order`` first, so no write meets the
    ``(card, order)`` unique constraint on its way to the planned order.
    """

    plan: CardPlan
    mentions_to_create: tuple[TermRow, ...]
    mentions_to_update: tuple[tuple[glossary_models.GlossarySpecMention, TermRow], ...]
    mentions_to_delete: tuple[glossary_models.GlossarySpecMention, ...]
    links_to_create: tuple[TermRow, ...]
    links_to_update: tuple[tuple[kanban_models.CardGlossaryTerm, TermRow], ...]
    links_to_delete: tuple[kanban_models.CardGlossaryTerm, ...]
    free_order: int

    @property
    def is_empty(self) -> bool:
        """Return whether the card's rows already equal its plan."""
        return not (
            self.mentions_to_create
            or self.mentions_to_update
            or self.mentions_to_delete
            or self.links_to_create
            or self.links_to_update
            or self.links_to_delete
        )

    @property
    def links_to_move(self) -> tuple[kanban_models.CardGlossaryTerm, ...]:
        """Return the kept links whose ``order`` changes."""
        return tuple(link for link, row in self.links_to_update if link.order != row.order)

    def describe(self) -> str:
        """Name every row the writing run would create, update or delete."""
        parts = [
            *_describe_rows(
                "GlossarySpecMention",
                self.mentions_to_create,
                [(row, _mention_diff(mention, row)) for mention, row in self.mentions_to_update],
                [mention.term.anchor for mention in self.mentions_to_delete],
            ),
            *_describe_rows(
                "CardGlossaryTerm",
                self.links_to_create,
                [(row, _link_diff(link, row)) for link, row in self.links_to_update],
                [link.term.anchor for link in self.links_to_delete],
            ),
        ]
        return f"{self.plan.card} ({self.plan.spec_path}): " + "; ".join(parts)


def _describe_rows(
    model_name: str,
    created: tuple[TermRow, ...],
    updated: list[tuple[TermRow, tuple[str, ...]]],
    deleted: list[str],
) -> list[str]:
    """Return one clause per kind of write owed to ``model_name`` rows."""
    parts: list[str] = []
    if created:
        parts.append(f"{model_name} missing {', '.join(row.anchor for row in created)}")
    if deleted:
        parts.append(f"{model_name} extra {', '.join(deleted)}")
    if updated:
        changed = ", ".join(f"{row.anchor} ({'/'.join(fields)})" for row, fields in updated)
        parts.append(f"{model_name} changed {changed}")
    return parts


def _mention_diff(mention: glossary_models.GlossarySpecMention, row: TermRow) -> tuple[str, ...]:
    """Return the ``GlossarySpecMention`` fields whose value differs from ``row``."""
    return tuple(
        name
        for name, current, planned in (
            ("term_text", mention.term_text, row.term_text),
            ("notes", mention.notes, row.notes),
            ("order", mention.order, row.order),
        )
        if current != planned
    )


def _link_diff(link: kanban_models.CardGlossaryTerm, row: TermRow) -> tuple[str, ...]:
    """Return the ``CardGlossaryTerm`` fields whose value differs from ``row``."""
    return tuple(
        name
        for name, current, planned in (
            ("raw_text", link.raw_text, row.term_text),
            ("order", link.order, row.order),
        )
        if current != planned
    )


def _report(headline: str, problems: list[str]) -> str:
    """Return ``headline`` followed by one indented line per problem."""
    return "\n".join([headline, *(f"  - {problem}" for problem in problems)])


def _spec_path_from_url(url: str) -> str:
    """Return the repo-relative spec path embedded in a stored spec URL."""
    if SPEC_PATH_MARKER not in url:
        return ""
    return url[url.index(SPEC_PATH_MARKER) :]


def _terms_path(repo_root: Path, spec_path: str) -> Path:
    """Return the companion ``*-terms.csv`` path for ``spec_path``.

    A live spec keeps its companion beside it; an archived one keeps it in the
    spec directory's ``appx/`` subfolder. The sibling wins when it exists, so a
    missing companion is reported at the authoring location.
    """
    path = repo_root / spec_path
    sibling = path.with_name(f"{path.stem}-terms.csv")
    if sibling.is_file():
        return sibling
    archived = path.parent / COMPANION_DIRNAME / sibling.name
    return archived if archived.is_file() else sibling


def _resolve_spec_path(repo_root: Path, spec_path: str) -> str:
    """Resolve archived spec moves by basename when a stored DB URL is stale."""
    direct = repo_root / spec_path
    if direct.exists():
        return spec_path

    basename = Path(spec_path).name
    matches = sorted((repo_root / "docs").glob(f"**/{basename}"))
    if not matches:
        return spec_path
    if len(matches) > 1:
        match_list = ", ".join(str(match.relative_to(repo_root)) for match in matches)
        raise CommandError(f"Spec path {spec_path!r} is ambiguous by basename: {match_list}")
    return matches[0].relative_to(repo_root).as_posix()


class Command(BaseCommand):
    """Import DONE-card spec term CSVs into the glossary and kanban tables."""

    help = (
        "Import DONE-card spec companion CSVs into GlossarySpecMention rows and "
        "reconcile each done card's CardGlossaryTerm links to match, writing only "
        "the rows that differ."
    )

    @override
    def add_arguments(self, parser: CommandParser) -> None:
        """Register command arguments."""
        _ = parser.add_argument(
            "--repo-root",
            type=Path,
            default=REPO_ROOT,
            help="Repository root containing docs/. Defaults to the current checkout.",
        )
        _ = parser.add_argument(
            "--check",
            action="store_true",
            help=(
                "Validate DB rows against the CSVs without writing; fails naming every "
                "unplannable done card and every row the writing run would change."
            ),
        )
        _ = parser.add_argument(
            "--dry-run",
            action="store_true",
            help=(
                "Report what would be imported without writing; fails while a done card "
                "cannot be planned."
            ),
        )

    def _load_rows(self, terms_path: Path) -> tuple[TermRow, ...]:
        if not terms_path.is_file():
            raise CommandError(f"Missing terms CSV: {terms_path}")

        rows: list[TermRow] = []
        problems: list[str] = []
        seen_anchors: set[str] = set()
        with terms_path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for order, row in enumerate(reader):
                term_text = (row.get("term") or "").strip()
                anchor = (row.get("anchor") or "").strip()
                notes = (row.get("notes") or "").strip()
                if not term_text or not anchor:
                    continue
                if anchor in seen_anchors:
                    problems.append(f"Duplicate glossary anchor {anchor!r} in {terms_path}")
                    continue
                seen_anchors.add(anchor)
                try:
                    term = glossary_models.GlossaryTerm.objects.get(anchor=anchor)
                except glossary_models.GlossaryTerm.DoesNotExist:
                    problems.append(f"Missing GlossaryTerm anchor {anchor!r} for {terms_path}")
                    continue
                rows.append(
                    TermRow(
                        term_text=term_text,
                        anchor=anchor,
                        notes=notes,
                        order=order,
                        term=term,
                    ),
                )
        if problems:
            raise CommandError("\n".join(problems))
        if not rows:
            raise CommandError(f"No terms loaded from {terms_path}")
        return tuple(rows)

    def _plan_card(self, repo_root: Path, card: kanban_models.Card) -> CardPlan:
        spec = getattr(card, "spec", None)
        if spec is None:
            raise CommandError(f"Done card {card} has no linked spec doc.")
        spec_path = _spec_path_from_url(spec.url)
        if not spec_path:
            raise CommandError(f"Done card {card} spec URL has no repo docs/ path: {spec.url}")
        spec_path = _resolve_spec_path(repo_root, spec_path)
        terms_path = _terms_path(repo_root, spec_path)
        return CardPlan(
            card=card,
            spec_path=spec_path,
            terms_path=terms_path,
            rows=self._load_rows(terms_path),
        )

    def _plan_or_problem(self, repo_root: Path, card: kanban_models.Card) -> CardPlan | str:
        """Return the card's plan, or the reason it cannot be planned."""
        try:
            return self._plan_card(repo_root, card)
        except CommandError as error:
            return str(error)

    def _plan_done_cards(self, repo_root: Path) -> tuple[tuple[CardPlan, ...], tuple[str, ...]]:
        """Return every done card's plan and the reason each unplannable card fails."""
        cards = (
            kanban_models.Card.objects.filter(status__key="done")
            .select_related("spec")
            .order_by("number")
        )
        plans: list[CardPlan] = []
        problems: list[str] = []
        planned_by_path: dict[str, CardPlan] = {}
        for card in cards:
            outcome = self._plan_or_problem(repo_root, card)
            if isinstance(outcome, str):
                problems.append(outcome)
            elif outcome.spec_path in planned_by_path:
                # Both cards would own one spec's mention rows, so neither sync is sound.
                problems.append(
                    f"Done card {card} resolves to spec {outcome.spec_path}, already planned "
                    f"for done card {planned_by_path[outcome.spec_path].card}.",
                )
            else:
                planned_by_path[outcome.spec_path] = outcome
                plans.append(outcome)
        return tuple(plans), tuple(problems)

    def _card_delta(self, plan: CardPlan) -> CardDelta:
        mentions = {
            mention.term.anchor: mention
            for mention in glossary_models.GlossarySpecMention.objects.filter(
                spec_path=plan.spec_path,
            )
            .select_related("term")
            .order_by("order")
        }
        links = {
            link.term.anchor: link
            for link in plan.card.glossary_links.select_related("term").order_by("order")
        }
        planned = {row.anchor for row in plan.rows}
        return CardDelta(
            plan=plan,
            mentions_to_create=tuple(row for row in plan.rows if row.anchor not in mentions),
            mentions_to_update=tuple(
                (mentions[row.anchor], row)
                for row in plan.rows
                if row.anchor in mentions and _mention_diff(mentions[row.anchor], row)
            ),
            mentions_to_delete=tuple(
                mention for anchor, mention in mentions.items() if anchor not in planned
            ),
            links_to_create=tuple(row for row in plan.rows if row.anchor not in links),
            links_to_update=tuple(
                (links[row.anchor], row)
                for row in plan.rows
                if row.anchor in links and _link_diff(links[row.anchor], row)
            ),
            links_to_delete=tuple(link for anchor, link in links.items() if anchor not in planned),
            free_order=1
            + max(
                [link.order for link in links.values()] + [row.order for row in plan.rows],
            ),
        )

    def _orphan_mentions(
        self,
        plans: tuple[CardPlan, ...],
    ) -> dict[str, list[glossary_models.GlossarySpecMention]]:
        """Return mention rows, by spec path, whose path no done card's spec resolves to."""
        orphans: defaultdict[str, list[glossary_models.GlossarySpecMention]] = defaultdict(list)
        for mention in (
            glossary_models.GlossarySpecMention.objects.exclude(
                spec_path__in=[plan.spec_path for plan in plans],
            )
            .select_related("term")
            .order_by("spec_path", "order")
        ):
            orphans[mention.spec_path].append(mention)
        return dict(orphans)

    def _apply_mentions(self, delta: CardDelta) -> None:
        _ = glossary_models.GlossarySpecMention.objects.filter(
            pk__in=[mention.pk for mention in delta.mentions_to_delete],
        ).delete()
        for mention, row in delta.mentions_to_update:
            fields = _mention_diff(mention, row)
            mention.term_text = row.term_text
            mention.notes = row.notes
            mention.order = row.order
            mention.save(update_fields=[*fields, "updated_date"])
        for row in delta.mentions_to_create:
            _ = glossary_models.GlossarySpecMention.objects.create(
                spec_path=delta.plan.spec_path,
                term=row.term,
                term_text=row.term_text,
                notes=row.notes,
                order=row.order,
            )

    def _apply_links(self, delta: CardDelta) -> None:
        # Park every link that gives up its position above the highest order in use, so
        # each later write lands on a free ``(card, order)`` slot.
        for offset, link in enumerate((*delta.links_to_move, *delta.links_to_delete)):
            _ = kanban_models.CardGlossaryTerm.objects.filter(pk=link.pk).update(
                order=delta.free_order + offset,
            )
        for link, row in delta.links_to_update:
            fields = _link_diff(link, row)
            link.raw_text = row.term_text
            link.order = row.order
            link.save(update_fields=[*fields, "updated_date"])
        for row in delta.links_to_create:
            _ = kanban_models.CardGlossaryTerm.objects.create(
                card=delta.plan.card,
                term=row.term,
                raw_text=row.term_text,
                order=row.order,
            )
        # Deleted last: a done card must keep at least one glossary link at every step.
        _ = kanban_models.CardGlossaryTerm.objects.filter(
            pk__in=[link.pk for link in delta.links_to_delete],
        ).delete()

    @override
    def handle(self, *args: object, **options: object) -> None:
        """Sync or validate done-card glossary links from companion CSVs."""
        repo_root = options["repo_root"]
        # ``add_arguments`` parses ``--repo-root`` to a ``Path``, but ``call_command``
        # hands a keyword option through unparsed, so the value is checked here.
        if not isinstance(repo_root, Path):
            raise CommandError(f"--repo-root must be a Path, got {type(repo_root).__name__}.")
        plans, unplanned = self._plan_done_cards(repo_root.resolve())
        deltas = [delta for delta in map(self._card_delta, plans) if not delta.is_empty]
        # An unplannable card's spec path is unknown, so its mention rows would read as
        # orphans; orphans are named and reaped only once every done card plans.
        orphans = {} if unplanned else self._orphan_mentions(plans)
        differences = [delta.describe() for delta in deltas] + [
            f"{spec_path}: GlossarySpecMention extra "
            f"{', '.join(mention.term.anchor for mention in mentions)} "
            "(no done card's spec resolves to this path)"
            for spec_path, mentions in orphans.items()
        ]
        card_count = len(plans) + len(unplanned)

        if options["check"]:
            if unplanned or differences:
                counts: list[str] = []
                if unplanned:
                    counts.append(
                        f"{len(unplanned)} done card(s) cannot be planned "
                        "(fix each reason listed)",
                    )
                if differences:
                    counts.append(
                        f"{len(differences)} glossary sync difference(s) "
                        "(run import_spec_terms to write them)",
                    )
                raise CommandError(
                    _report(
                        f"{'; '.join(counts)} across {card_count} done card(s):",
                        [*unplanned, *differences],
                    ),
                )
            self.stdout.write(
                self.style.SUCCESS(f"OK: {card_count} done cards have glossary links."),
            )
            return

        if options["dry_run"]:
            self.stdout.write(f"Would import glossary terms for {len(plans)} done card(s):")
            for plan in plans:
                self.stdout.write(
                    f"  {plan.card}: {len(plan.rows)} term(s) from {plan.terms_path}",
                )
            self.stdout.write(f"{len(unplanned)} done card(s) cannot be planned:")
            for problem in unplanned:
                self.stdout.write(f"  - {problem}")
            self.stdout.write(f"{len(differences)} difference(s) to write:")
            for difference in differences:
                self.stdout.write(f"  - {difference}")
            if unplanned:
                raise CommandError(
                    f"{len(unplanned)} done card(s) cannot be planned; the writing run would "
                    "write nothing.",
                )
            return

        if unplanned:
            raise CommandError(
                _report(
                    f"{len(unplanned)} done card(s) cannot be planned; nothing written:",
                    list(unplanned),
                ),
            )

        with transaction.atomic():
            for delta in deltas:
                self._apply_mentions(delta)
                self._apply_links(delta)
            _ = glossary_models.GlossarySpecMention.objects.filter(
                pk__in=[mention.pk for mentions in orphans.values() for mention in mentions],
            ).delete()

        self.stdout.write(
            self.style.SUCCESS(
                f"Imported glossary terms for {len(plans)} done card(s); "
                f"{len(differences)} difference(s) written.",
            ),
        )
