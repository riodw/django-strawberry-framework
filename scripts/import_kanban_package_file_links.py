#!/usr/bin/env python
"""Import kanban card package-file links from the attribution ledger."""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
FAKESHOP_ROOT = REPO_ROOT / "examples" / "fakeshop"
DEFAULT_ATTRIBUTION_PATH = REPO_ROOT / "package-spec-attribution.md"
PACKAGE_PATH_PREFIX = "django_strawberry_framework/"

CARD_HEADING_RE = re.compile(
    r"^## (?P<card_id>DONE-(?P<number>\d{3})-[^\s]+) (?P<title>.+)$",
)
UNIQUE_COUNT_RE = re.compile(r"^Unique package files: (?P<count>\d+)$")
PACKAGE_FILE_RE = re.compile(r"- `(?P<path>django_strawberry_framework/[^`]+)`")


class AttributionImportError(RuntimeError):
    """A caller-correctable attribution import error."""


class DryRunRollbackError(Exception):
    """Internal sentinel used to roll back the dry-run transaction."""


@dataclass(frozen=True)
class CardAttribution:
    """One DONE card and the package files attributed to it."""

    card_id: str
    number: int
    title: str
    files: tuple[str, ...]


@dataclass
class MutableCardAttribution:
    """Mutable parser state for one card section."""

    card_id: str
    number: int
    title: str
    unique_count: int | None = None
    listed_files: set[str] = field(default_factory=set)
    commit_files: set[str] = field(default_factory=set)

    def build(self) -> CardAttribution:
        """Return validated immutable attribution data."""
        listed_files = tuple(sorted(self.listed_files))
        commit_files = tuple(sorted(self.commit_files))
        if not listed_files:
            raise AttributionImportError(f"{self.card_id} has no package files.")
        if self.unique_count is None:
            raise AttributionImportError(f"{self.card_id} is missing a unique-file count.")
        if len(listed_files) != self.unique_count:
            raise AttributionImportError(
                f"{self.card_id} unique-file count says {self.unique_count}, "
                f"but the Files block contains {len(listed_files)} path(s).",
            )
        if listed_files != commit_files:
            listed_only = sorted(set(listed_files) - set(commit_files))
            commit_only = sorted(set(commit_files) - set(listed_files))
            raise AttributionImportError(
                f"{self.card_id} Files block does not match commit-detail file union. "
                f"Listed-only: {listed_only}; commit-only: {commit_only}.",
            )
        return CardAttribution(
            card_id=self.card_id,
            number=self.number,
            title=self.title,
            files=listed_files,
        )


def run_git(args: Sequence[str]) -> str:
    """Run ``git --no-pager <args>`` and return stdout."""
    try:
        result = subprocess.run(
            ["git", "--no-pager", *args],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as error:
        message = error.stderr.strip() or f"git {' '.join(args)} failed."
        raise AttributionImportError(message) from error
    return result.stdout


def historical_package_paths() -> frozenset[str]:
    """Return every package path that appears in git history."""
    output = run_git(
        [
            "log",
            "--all",
            "--format=",
            "--name-only",
            "--",
            PACKAGE_PATH_PREFIX,
        ],
    )
    paths = {
        line.strip()
        for line in output.splitlines()
        if line.strip().startswith(PACKAGE_PATH_PREFIX)
    }
    return frozenset(paths)


def parse_attribution(path: Path) -> list[CardAttribution]:
    """Parse DONE-card file attribution sections from ``package-spec-attribution.md``."""
    if not path.is_file():
        raise AttributionImportError(f"Attribution file not found: {path}")

    cards: list[CardAttribution] = []
    current: MutableCardAttribution | None = None
    mode: str | None = None

    def finish_current() -> None:
        nonlocal current
        if current is not None:
            cards.append(current.build())
            current = None

    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            finish_current()
            mode = None
            match = CARD_HEADING_RE.match(line)
            if match:
                current = MutableCardAttribution(
                    card_id=match.group("card_id"),
                    number=int(match.group("number")),
                    title=match.group("title"),
                )
            continue

        if current is None:
            continue

        unique_count_match = UNIQUE_COUNT_RE.match(line)
        if unique_count_match:
            current.unique_count = int(unique_count_match.group("count"))
            continue
        if line == "Files:":
            mode = "files"
            continue
        if line == "Commit detail:":
            mode = "commit"
            continue

        path_match = PACKAGE_FILE_RE.search(line)
        if path_match is None:
            continue
        package_path = path_match.group("path")
        if mode == "files":
            current.listed_files.add(package_path)
        elif mode == "commit":
            current.commit_files.add(package_path)

    finish_current()
    if not cards:
        raise AttributionImportError(f"No DONE card attribution sections found in {path}.")
    return cards


def validate_paths_against_git(cards: Sequence[CardAttribution]) -> None:
    """Ensure every attributed path is a package file known to git history."""
    known_paths = historical_package_paths()
    attributed_paths = {package_path for card in cards for package_path in card.files}
    unknown_paths = sorted(attributed_paths - known_paths)
    if unknown_paths:
        raise AttributionImportError(
            "Attribution contains package paths that do not appear in git history: "
            + ", ".join(unknown_paths),
        )


def setup_django() -> None:
    """Load the fakeshop Django app."""
    sys.path.insert(0, str(FAKESHOP_ROOT))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

    import django

    django.setup()


def import_links(cards: Sequence[CardAttribution], *, dry_run: bool) -> None:
    """Import package-file links into the kanban app."""
    setup_django()

    from apps.kanban import models, services
    from apps.kanban.constants import PACKAGE_FILE_PATH_SET
    from django.db import transaction

    all_paths = sorted({package_path for card in cards for package_path in card.files})
    historical_paths = [path for path in all_paths if path not in PACKAGE_FILE_PATH_SET]
    updated: list[str] = []

    try:
        with transaction.atomic():
            services.sync_package_files_from_constants()
            for path in historical_paths:
                package_file, _ = models.PackageFile.objects.get_or_create(
                    path=path,
                    defaults={"is_current": False},
                )
                if package_file.is_current:
                    package_file.is_current = False
                    package_file.save(update_fields=["is_current", "updated_date"])

            for attribution in cards:
                card = services.resolve_card(attribution.number)
                if card.status.key != services.DONE_STATUS_KEY:
                    raise AttributionImportError(
                        f"{attribution.card_id} resolved to non-DONE card: {card}",
                    )
                services.set_card_changed_files(card, list(attribution.files))
                updated.append(f"{card.card_id} - {card.title}: {len(attribution.files)} file(s)")

            if dry_run:
                raise DryRunRollbackError
    except DryRunRollbackError:
        print("Dry run - rolled back. Would update:")
    else:
        print("Updated:")

    for line in updated:
        print(f"  {line}")
    print(f"Cards: {len(cards)}")
    print(f"Unique package files: {len(all_paths)}")
    print(f"Historical package files seeded: {len(historical_paths)}")


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Import kanban changed-file links from package-spec-attribution.md.",
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_ATTRIBUTION_PATH,
        help="Attribution markdown file to parse.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and report the import without writing database changes.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """Parse, validate, and import package-file links."""
    args = parse_args(sys.argv[1:] if argv is None else argv)
    cards = parse_attribution(args.input)
    validate_paths_against_git(cards)
    import_links(cards, dry_run=args.dry_run)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AttributionImportError as error:
        print(error, file=sys.stderr)
        raise SystemExit(2) from error
