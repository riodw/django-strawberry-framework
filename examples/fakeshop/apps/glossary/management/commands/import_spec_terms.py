"""Import spec companion CSVs into glossary mentions and done-card links."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.db import transaction

from apps.glossary import models as glossary_models
from apps.kanban import models as kanban_models

REPO_ROOT = Path(__file__).resolve().parents[6]
SPEC_PATH_MARKER = "docs/"


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


def _spec_path_from_url(url: str) -> str:
    """Return the repo-relative spec path embedded in a stored spec URL."""
    if SPEC_PATH_MARKER not in url:
        return ""
    return url[url.index(SPEC_PATH_MARKER) :]


def _terms_path(repo_root: Path, spec_path: str) -> Path:
    """Return the companion ``*-terms.csv`` path for ``spec_path``."""
    path = repo_root / spec_path
    return path.with_name(f"{path.stem}-terms.csv")


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
        "reconcile each done card's CardGlossaryTerm links to match."
    )

    def add_arguments(self, parser: CommandParser) -> None:
        """Register command arguments."""
        parser.add_argument(
            "--repo-root",
            type=Path,
            default=REPO_ROOT,
            help="Repository root containing docs/. Defaults to the current checkout.",
        )
        parser.add_argument(
            "--check",
            action="store_true",
            help="Validate DB rows against the CSVs without writing.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report what would be imported without writing.",
        )

    def _load_rows(self, terms_path: Path) -> tuple[TermRow, ...]:
        if not terms_path.is_file():
            raise CommandError(f"Missing terms CSV: {terms_path}")

        rows: list[TermRow] = []
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
                    raise CommandError(f"Duplicate glossary anchor {anchor!r} in {terms_path}")
                seen_anchors.add(anchor)
                try:
                    term = glossary_models.GlossaryTerm.objects.get(anchor=anchor)
                except glossary_models.GlossaryTerm.DoesNotExist:
                    raise CommandError(
                        f"Missing GlossaryTerm anchor {anchor!r} for {terms_path}",
                    ) from None
                rows.append(
                    TermRow(
                        term_text=term_text,
                        anchor=anchor,
                        notes=notes,
                        order=order,
                        term=term,
                    ),
                )
        if not rows:
            raise CommandError(f"No terms loaded from {terms_path}")
        return tuple(rows)

    def _plan_done_cards(self, repo_root: Path) -> tuple[CardPlan, ...]:
        cards = (
            kanban_models.Card.objects.filter(status__key="done")
            .select_related("spec")
            .order_by("number")
        )
        plans: list[CardPlan] = []
        for card in cards:
            spec = getattr(card, "spec", None)
            if spec is None:
                raise CommandError(f"Done card {card} has no linked spec doc.")
            spec_path = _spec_path_from_url(spec.url)
            if not spec_path:
                raise CommandError(f"Done card {card} spec URL has no repo docs/ path: {spec.url}")
            spec_path = _resolve_spec_path(repo_root, spec_path)
            terms_path = _terms_path(repo_root, spec_path)
            plans.append(
                CardPlan(
                    card=card,
                    spec_path=spec_path,
                    terms_path=terms_path,
                    rows=self._load_rows(terms_path),
                ),
            )
        return tuple(plans)

    def _assert_plan_matches_db(self, plan: CardPlan) -> None:
        expected = [row.anchor for row in plan.rows]
        mention_anchors = list(
            glossary_models.GlossarySpecMention.objects.filter(spec_path=plan.spec_path)
            .order_by("order")
            .values_list("term__anchor", flat=True),
        )
        if mention_anchors != expected:
            raise CommandError(
                f"GlossarySpecMention rows for {plan.spec_path} do not match "
                f"{plan.terms_path}: {mention_anchors!r} != {expected!r}",
            )

        link_anchors = list(
            plan.card.glossary_links.order_by("order").values_list("term__anchor", flat=True),
        )
        if link_anchors != expected:
            raise CommandError(
                f"Card glossary links for {plan.card} do not match {plan.terms_path}: "
                f"{link_anchors!r} != {expected!r}",
            )

    def _sync_spec_mentions(self, plan: CardPlan) -> None:
        term_ids = [row.term.pk for row in plan.rows]
        glossary_models.GlossarySpecMention.objects.filter(spec_path=plan.spec_path).exclude(
            term_id__in=term_ids,
        ).delete()
        for row in plan.rows:
            glossary_models.GlossarySpecMention.objects.update_or_create(
                spec_path=plan.spec_path,
                term=row.term,
                defaults={"term_text": row.term_text, "notes": row.notes, "order": row.order},
            )

    def _sync_card_links(self, plan: CardPlan) -> None:
        offset = plan.card.glossary_links.count() + len(plan.rows) + 1000
        for row in plan.rows:
            kanban_models.CardGlossaryTerm.objects.update_or_create(
                card=plan.card,
                term=row.term,
                defaults={"raw_text": row.term_text, "order": offset + row.order},
            )

        term_ids = [row.term.pk for row in plan.rows]
        plan.card.glossary_links.exclude(term_id__in=term_ids).delete()

        for row in plan.rows:
            plan.card.glossary_links.filter(term=row.term).update(
                raw_text=row.term_text,
                order=row.order,
            )

    def handle(self, *args: object, **options: object) -> None:
        """Sync or validate done-card glossary links from companion CSVs."""
        repo_root = options["repo_root"].resolve()
        plans = self._plan_done_cards(repo_root)

        if options["check"]:
            for plan in plans:
                self._assert_plan_matches_db(plan)
            self.stdout.write(
                self.style.SUCCESS(f"OK: {len(plans)} done cards have glossary links."),
            )
            return

        if options["dry_run"]:
            self.stdout.write(f"Would import glossary terms for {len(plans)} done card(s):")
            for plan in plans:
                self.stdout.write(
                    f"  {plan.card}: {len(plan.rows)} term(s) from {plan.terms_path}",
                )
            return

        with transaction.atomic():
            for plan in plans:
                self._sync_spec_mentions(plan)
                self._sync_card_links(plan)

        self.stdout.write(
            self.style.SUCCESS(f"Imported glossary terms for {len(plans)} done card(s)."),
        )
