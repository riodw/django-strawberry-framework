"""Parse ``KANBAN.md`` into the kanban models (phase 2 of the plan).

This is example-app code, not framework code: a small, tolerant, line-oriented
parser that turns the board-as-prose into board-as-data. It is intentionally
best-effort on the full board — the *target schema* is the point. Determinism is
pinned by ``examples/fakeshop/tests/test_kanban_import.py`` against a fixed
excerpt.

Idempotency: lookups upsert on ``key``; cards upsert on ``title`` (the board's
own stable identifier). Re-running updates in place. All creates go through
``.save()`` / ``.objects.create()`` so the ``UUIDModel`` ``post_save`` signal
fires (``bulk_create`` would skip it).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from django.db import transaction

from . import models

CardIdentity = tuple[str, int, str]


@dataclass(frozen=True)
class CardItemSnapshot:
    """One parsed bullet item before it is reconciled into the database."""

    section_key: str
    text: str
    order: int


@dataclass(frozen=True)
class ParityClaimSnapshot:
    """One parsed parity edge before it becomes a ``ParityClaim`` row."""

    upstream_key: str
    level_key: str


@dataclass(frozen=True)
class CardReferenceSnapshot:
    """One parsed card-to-card reference before it becomes a FK edge."""

    target_key: CardIdentity
    kind_key: str
    source_key: str
    raw_text: str
    order: int


@dataclass(frozen=True)
class CardSnapshot:
    """One parsed kanban card with only stable natural keys, never DB objects."""

    status_key: str
    milestone_key: str | None
    number: int
    target_version: str
    title: str
    priority_key: str | None = None
    severity_key: str | None = None
    size_low_key: str | None = None
    size_high_key: str | None = None
    planning_state_key: str = "planned"
    planning_note: str = ""
    spec_path: str | None = None
    items: tuple[CardItemSnapshot, ...] = ()
    parity_claims: tuple[ParityClaimSnapshot, ...] = ()
    references: tuple[CardReferenceSnapshot, ...] = ()

    @property
    def id_key(self) -> CardIdentity:
        return (self.status_key, self.number, self.target_version)

    @property
    def dependency_keys(self) -> frozenset[CardIdentity]:
        """Dependency-like references that should backfill ``Card.dependencies``."""
        return frozenset(
            reference.target_key
            for reference in self.references
            if reference.kind_key in _DEPENDENCY_REFERENCE_KIND_KEYS
        )


@dataclass(frozen=True)
class BoardSnapshot:
    """A parsed board snapshot ready to reconcile into the kanban tables."""

    cards: tuple[CardSnapshot, ...]

    @property
    def target_versions(self) -> tuple[str, ...]:
        """Distinct target-version numbers in first-seen board order."""
        return tuple(dict.fromkeys(card.target_version for card in self.cards))

    @property
    def spec_paths(self) -> tuple[str, ...]:
        """Distinct spec paths referenced by cards, in first-seen board order."""
        return tuple(dict.fromkeys(card.spec_path for card in self.cards if card.spec_path))


# ---------------------------------------------------------------------------
# Canonical lookup seed data
# ---------------------------------------------------------------------------

_STATUSES = [
    ("todo", "To Do"),
    ("wip", "WIP"),
    ("blocked", "Blocked"),
    ("done", "Done"),
]
# Ordered most- to least-urgent. Includes the compound + critical labels the
# real board actually uses (e.g. "medium-high", "low-medium", "critical").
_PRIORITIES = [
    ("critical", "Critical"),
    ("high", "High"),
    ("medium-high", "Medium-high"),
    ("medium", "Medium"),
    ("low-medium", "Low-medium"),
    ("low", "Low"),
]
_SEVERITIES = [
    ("major", "Major"),
    ("medium", "Medium"),
    ("low", "Low"),
]
_SIZES = [
    ("xs", "XS"),
    ("s", "S"),
    ("m", "M"),
    ("l", "L"),
    ("xl", "XL"),
]
_PLANNING = [
    ("planned", "Planned"),
    ("needs_spec", "Needs spec"),
    ("in_progress", "In progress"),
    ("blocked", "Blocked"),
    ("shipped", "Shipped"),
]
_MILESTONES = [
    (
        "alpha",
        "Alpha (pre-0.1.0)",
        "0.0.6",
        "0.1.0",
    ),
    (
        "beta",
        "Beta (pre-1.0.0)",
        "0.1.1",
        "1.0.0",
    ),
    (
        "stable",
        "Stable (post-1.0.0)",
        "1.0.0",
        "",
    ),
]
_UPSTREAMS = [
    ("graphene_django", "graphene-django", "⚛️"),
    ("strawberry_django", "strawberry-graphql-django", "🍓"),
]
_PARITY_LEVELS = [
    ("required", "Required"),
    ("adjacent", "Parity-adjacent"),
]
_SECTIONS = [
    ("scope", "Scope"),
    ("definition_of_done", "Definition of done"),
    ("foundation_seam", "Foundation-slice seam"),
    ("files_touched", "Files likely touched"),
    ("verified_upstream", "Verified in upstream"),
    ("arch_posture", "Architectural posture"),
    ("why_it_matters", "Why it matters"),
    ("dependencies_note", "Dependencies"),
    ("other", "Other"),
]
_CARD_REFERENCE_KINDS = [
    ("dependency", "Dependency"),
    ("blocked_by", "Blocked by"),
    ("related", "Related"),
]
_CARD_REFERENCE_SOURCES = [
    ("dependencies_section", "Dependencies section"),
    ("planning_note", "Planning note"),
]
_DEPENDENCY_REFERENCE_KIND_KEYS = frozenset({"dependency", "blocked_by"})

# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

_CARD_HEADER_RE = re.compile(
    r"^###\s+"
    r"(?P<status>TODO|WIP|BLOCKED|DONE)"
    r"(?:-(?P<milestone>ALPHA|BETA|STABLE))?"
    r"-(?P<number>\d{3})"
    r"-(?P<version>\d+\.\d+\.\d+)"
    r"\s+[—-]\s+(?P<title>.+?)\s*$",
)
# Any card-id reference (used to resolve `Dependencies` bullets to other cards).
# Captures the full identity (status, number, version) because NNN alone is NOT
# unique across the board -- DONE and TODO cards keep independent NNN sequences,
# so e.g. DONE-046-0.0.7 and a TODO-046-1.0.0 can coexist.
_CARD_ID_REF_RE = re.compile(
    r"(?P<status>TODO|WIP|BLOCKED|DONE)(?:-(?:ALPHA|BETA|STABLE))?-(?P<number>\d{3})-(?P<version>\d+\.\d+\.\d+)",
)
_LABEL_RE = re.compile(
    r"^(?P<label>Priority|Parity|Severity|Status|Relative size|Spec):\s*(?P<value>.+?)\s*$",
)
_SECTION_RE = re.compile(r"^(?P<name>[A-Z][^:]*):\s*$")
_BULLET_RE = re.compile(r"^[-*]\s+(?P<text>.+?)\s*$")
# First backtick-wrapped ``…​.md`` path on a ``Spec:`` line (handles both the
# bare ``Spec: `path` `` and the reference-style ``Spec: [`path`][ref]`` forms).
_SPEC_PATH_RE = re.compile(r"`([^`]+\.md)`")
_GITHUB_BLOB_BASE = "https://github.com/riodw/django-strawberry-framework/blob/main/"

_SIZE_KEYS = {
    "xs",
    "s",
    "m",
    "l",
    "xl",
}
_PRIORITY_KEYS = {key for key, _label in _PRIORITIES}
_SEVERITY_KEYS = {key for key, _label in _SEVERITIES}
_SECTION_BY_PREFIX = [
    ("definition of done", "definition_of_done"),
    ("foundation", "foundation_seam"),
    ("files", "files_touched"),
    ("verified in", "verified_upstream"),
    ("architectural", "arch_posture"),
    ("why ", "why_it_matters"),
    ("scope", "scope"),
    ("dependencies", "dependencies_note"),
]


def _milestone_for_version(version: str) -> str:
    if version.startswith("0.0.") or version == "0.1.0":
        return "alpha"
    if version.startswith("0.1."):
        return "beta"
    if version == "1.0.0" or version.startswith("1."):
        return "stable"
    return "alpha"


def _first_token(value: str) -> str:
    """First whitespace token, lowered and stripped of markdown emphasis / backticks."""
    parts = value.strip().split()
    return parts[0].strip("*_`").lower() if parts else ""


def _priority_key(value: str) -> str | None:
    token = _first_token(value)
    return token if token in _PRIORITY_KEYS else None


def _severity_key(value: str) -> str | None:
    token = _first_token(value)
    return token if token in _SEVERITY_KEYS else None


def _size_keys(value: str) -> tuple[str | None, str | None]:
    token = value.strip().split()[0] if value.strip() else ""
    token = token.replace("–", "-").replace("—", "-")
    parts = [p.strip().lower() for p in token.split("-") if p.strip().lower() in _SIZE_KEYS]
    if not parts:
        return (None, None)
    if len(parts) == 1:
        return (parts[0], None)
    return (parts[0], parts[1])


def _planning_key(value: str) -> str:
    head = re.split(r"[;,(]", value.strip().lower())[0].strip()
    mapping = {
        "needs spec": "needs_spec",
        "in progress": "in_progress",
        "wip": "in_progress",
        "blocked": "blocked",
        "shipped": "shipped",
        "done": "shipped",
        "planned": "planned",
    }
    for prefix, key in mapping.items():
        if head.startswith(prefix):
            return key
    return "planned"


def _parity_claims(value: str) -> tuple[ParityClaimSnapshot, ...]:
    level = "adjacent" if "adjacent" in value.lower() else "required"
    claims = []
    if "⚛" in value:
        claims.append(ParityClaimSnapshot(upstream_key="graphene_django", level_key=level))
    if "🍓" in value:
        claims.append(ParityClaimSnapshot(upstream_key="strawberry_django", level_key=level))
    return tuple(claims)


def _section_key(name: str) -> str:
    low = name.strip().lower()
    for prefix, key in _SECTION_BY_PREFIX:
        if low.startswith(prefix):
            return key
    return "other"


def _identity_from_card_id_match(match: re.Match[str]) -> CardIdentity:
    return (match["status"].lower(), int(match["number"]), match["version"])


def _reference_kind_for_text(text: str) -> str:
    lowered = text.lower()
    if "blocked on" in lowered or "blocked by" in lowered:
        return "blocked_by"
    if "gated on" in lowered or "depends on" in lowered or "dependency" in lowered:
        return "dependency"
    return "related"


def _title_reference_aliases(title: str) -> tuple[str, ...]:
    aliases = [title]
    without_backticks = title.replace("`", "")
    if without_backticks != title:
        aliases.append(without_backticks)
    return tuple(dict.fromkeys(alias for alias in aliases if alias))


def _reference_snapshots_from_text(
    text: str,
    *,
    source_key: str,
    source_card_key: CardIdentity,
    title_identity_pairs: list[tuple[str, CardIdentity]],
    start_order: int,
    kind_key: str | None = None,
) -> tuple[CardReferenceSnapshot, ...]:
    """Find card references in a text fragment and order them by source position."""
    candidates: list[tuple[int, CardIdentity, str]] = []
    seen_targets: set[CardIdentity] = set()

    for match in _CARD_ID_REF_RE.finditer(text):
        target_key = _identity_from_card_id_match(match)
        if target_key == source_card_key or target_key in seen_targets:
            continue
        seen_targets.add(target_key)
        candidates.append((match.start(), target_key, kind_key or _reference_kind_for_text(text)))

    for title, target_key in title_identity_pairs:
        if target_key == source_card_key or target_key in seen_targets or title not in text:
            continue
        seen_targets.add(target_key)
        candidates.append(
            (text.index(title), target_key, kind_key or _reference_kind_for_text(text)),
        )

    return tuple(
        CardReferenceSnapshot(
            target_key=target_key,
            kind_key=candidate_kind_key,
            source_key=source_key,
            raw_text=text,
            order=start_order + order,
        )
        for order, (_position, target_key, candidate_kind_key) in enumerate(
            sorted(candidates, key=lambda candidate: candidate[0]),
        )
    )


def parse_board_snapshot(markdown: str) -> BoardSnapshot:
    """Split ``markdown`` into a normalized board snapshot (no DB access)."""
    lines = markdown.splitlines()
    # Find card header line indices.
    headers = [i for i, line in enumerate(lines) if _CARD_HEADER_RE.match(line)]
    title_identity_pairs: list[tuple[str, CardIdentity]] = []
    for start in headers:
        header = _CARD_HEADER_RE.match(lines[start])
        assert header is not None
        identity = (header["status"].lower(), int(header["number"]), header["version"])
        for title_alias in _title_reference_aliases(header["title"].strip()):
            title_identity_pairs.append((title_alias, identity))

    cards: list[CardSnapshot] = []
    for idx, start in enumerate(headers):
        end = headers[idx + 1] if idx + 1 < len(headers) else len(lines)
        # Stop at the next ``## `` (board-section) header inside the slice.
        block = []
        for line in lines[start + 1 : end]:
            if line.startswith("## "):
                break
            block.append(line)
        header = _CARD_HEADER_RE.match(lines[start])
        assert header is not None
        status_key = header["status"].lower()
        milestone_key = header["milestone"].lower() if header["milestone"] else None
        number = int(header["number"])
        target_version = header["version"]
        title = header["title"].strip()
        id_key = (status_key, number, target_version)
        priority_key = None
        severity_key = None
        size_low_key = None
        size_high_key = None
        planning_state_key = "planned"
        planning_note = ""
        spec_path = None
        parity_claims: tuple[ParityClaimSnapshot, ...] = ()
        items: list[CardItemSnapshot] = []
        references: list[CardReferenceSnapshot] = []
        current_section = "other"
        order_by_section: dict[str, int] = {}
        reference_order_by_source: dict[str, int] = {}
        for line in block:
            label = _LABEL_RE.match(line)
            if label:
                name, value = label["label"], label["value"]
                if name == "Priority":
                    priority_key = _priority_key(value)
                elif name == "Severity":
                    severity_key = _severity_key(value)
                elif name == "Relative size":
                    size_low_key, size_high_key = _size_keys(value)
                elif name == "Status":
                    planning_state_key = _planning_key(value)
                    planning_note = value.strip()
                    planning_references = _reference_snapshots_from_text(
                        planning_note,
                        source_key="planning_note",
                        source_card_key=id_key,
                        title_identity_pairs=title_identity_pairs,
                        start_order=reference_order_by_source.get("planning_note", 0),
                    )
                    references.extend(planning_references)
                    reference_order_by_source["planning_note"] = reference_order_by_source.get(
                        "planning_note",
                        0,
                    ) + len(planning_references)
                elif name == "Parity":
                    parity_claims = _parity_claims(value)
                elif name == "Spec":
                    match = _SPEC_PATH_RE.search(value)
                    if match:
                        spec_path = match.group(1)
                continue
            section = _SECTION_RE.match(line)
            if section:
                current_section = _section_key(section["name"])
                continue
            bullet = _BULLET_RE.match(line.lstrip())
            if bullet:
                text = bullet["text"].strip()
                order = order_by_section.get(current_section, 0)
                order_by_section[current_section] = order + 1
                items.append(
                    CardItemSnapshot(
                        section_key=current_section,
                        text=text,
                        order=order,
                    ),
                )
                if current_section == "dependencies_note":
                    dependency_references = _reference_snapshots_from_text(
                        text,
                        source_key="dependencies_section",
                        source_card_key=id_key,
                        title_identity_pairs=title_identity_pairs,
                        start_order=reference_order_by_source.get("dependencies_section", 0),
                        kind_key="dependency",
                    )
                    references.extend(dependency_references)
                    reference_order_by_source["dependencies_section"] = (
                        reference_order_by_source.get("dependencies_section", 0)
                        + len(dependency_references)
                    )
        cards.append(
            CardSnapshot(
                status_key=status_key,
                milestone_key=milestone_key,
                number=number,
                target_version=target_version,
                title=title,
                priority_key=priority_key,
                severity_key=severity_key,
                size_low_key=size_low_key,
                size_high_key=size_high_key,
                planning_state_key=planning_state_key,
                planning_note=planning_note,
                spec_path=spec_path,
                items=tuple(items),
                parity_claims=parity_claims,
                references=tuple(references),
            ),
        )
    return BoardSnapshot(cards=tuple(cards))


def parse_cards(markdown: str) -> tuple[CardSnapshot, ...]:
    """Return only the parsed card snapshots for consumers that do not need the board."""
    return parse_board_snapshot(markdown).cards


def parse_card_dicts(markdown: str) -> list[dict]:
    """Legacy dict-shaped parser output retained for ad hoc debugging code."""
    return [_card_snapshot_to_dict(card) for card in parse_cards(markdown)]


def _card_snapshot_to_dict(card: CardSnapshot) -> dict:
    return {
        "status": card.status_key,
        "milestone": card.milestone_key,
        "number": card.number,
        "version": card.target_version,
        "title": card.title,
        "priority": card.priority_key,
        "severity": card.severity_key,
        "size_low": card.size_low_key,
        "size_high": card.size_high_key,
        "planning_state": card.planning_state_key,
        "planning_note": card.planning_note,
        "parity": [(claim.upstream_key, claim.level_key) for claim in card.parity_claims],
        "spec_path": card.spec_path,
        "items": [(item.section_key, item.text, item.order) for item in card.items],
        "references": [
            (
                reference.target_key,
                reference.kind_key,
                reference.source_key,
                reference.raw_text,
                reference.order,
            )
            for reference in card.references
        ],
        "dep_keys": set(card.dependency_keys),
        "id_key": card.id_key,
    }


# ---------------------------------------------------------------------------
# DB loading
# ---------------------------------------------------------------------------


def _seed_lookups() -> dict[str, dict]:
    """Idempotently create the canonical lookup rows; return ``{kind: {key: obj}}``."""
    out: dict[str, dict] = {}

    def upsert(model, rows, **extra_per_row):
        table = {}
        for order, row in enumerate(rows):
            key, label = row[0], row[1]
            defaults = {"label": label, "order": order}
            defaults.update(extra_per_row.get(key, {}))
            obj, _ = model.objects.update_or_create(key=key, defaults=defaults)
            table[key] = obj
        return table

    out["status"] = upsert(models.Status, _STATUSES)
    out["priority"] = upsert(models.Priority, _PRIORITIES)
    out["severity"] = upsert(models.Severity, _SEVERITIES)
    out["size"] = upsert(
        models.RelativeSize,
        _SIZES,
        **{key: {"rank": rank} for rank, (key, _label) in enumerate(_SIZES)},
    )
    out["planning"] = upsert(models.PlanningState, _PLANNING)
    out["parity_level"] = upsert(models.ParityLevel, _PARITY_LEVELS)
    out["section"] = upsert(models.Section, _SECTIONS)
    out["reference_kind"] = upsert(models.CardReferenceKind, _CARD_REFERENCE_KINDS)
    out["reference_source"] = upsert(models.CardReferenceSource, _CARD_REFERENCE_SOURCES)

    milestones = {}
    for order, (
        key,
        label,
        floor,
        ceiling,
    ) in enumerate(_MILESTONES):
        obj, _ = models.Milestone.objects.update_or_create(
            key=key,
            defaults={
                "label": label,
                "order": order,
                "version_floor": floor,
                "version_ceiling": ceiling,
            },
        )
        milestones[key] = obj
    out["milestone"] = milestones

    upstreams = {}
    for order, (key, label, emoji) in enumerate(_UPSTREAMS):
        obj, _ = models.Upstream.objects.update_or_create(
            key=key,
            defaults={"label": label, "order": order, "emoji": emoji},
        )
        upstreams[key] = obj
    out["upstream"] = upstreams
    return out


def _spec_for(spec_path: str | None) -> models.SpecDoc | None:
    """Upsert a ``SpecDoc`` for a parsed spec path, or ``None`` if absent.

    The name is the file stem (stable across re-imports); the URL points at the
    file on GitHub's default branch.
    """
    if not spec_path:
        return None
    spec, _ = models.SpecDoc.objects.update_or_create(
        name=Path(spec_path).stem,
        defaults={"url": _GITHUB_BLOB_BASE + spec_path.lstrip("/")},
    )
    return spec


def _reconcile_items(card, snapshot: CardSnapshot, lookups: dict) -> int:
    """Update/create/delete a card's items, preserving UUIDs for stable rows.

    Items are matched on ``(section, order)`` so an unchanged row is updated in
    place -- never deleted -- which keeps its ``UUIDModel`` side row (and thus
    the UUID) stable across re-imports. Returns the resulting item count.
    """
    existing = {(it.section_id, it.order): it for it in card.items.all()}
    is_complete = snapshot.status_key == "done"
    desired: set[tuple[int, int]] = set()
    for item_snapshot in snapshot.items:
        section = lookups["section"][item_snapshot.section_key]
        key = (section.id, item_snapshot.order)
        desired.add(key)
        item = existing.get(key)
        if item is None:
            models.CardItem.objects.create(
                card=card,
                section=section,
                text=item_snapshot.text,
                order=item_snapshot.order,
                is_complete=is_complete,
            )
        elif item.text != item_snapshot.text or item.is_complete != is_complete:
            item.text = item_snapshot.text
            item.is_complete = is_complete
            item.save(
                update_fields=["text", "is_complete", "updated_date"],
            )
    for key, item in existing.items():
        if key not in desired:
            item.delete()
    return len(snapshot.items)


def _reconcile_parity(card, snapshot: CardSnapshot, lookups: dict) -> int:
    """Update/create/delete a card's parity claims; return the resulting count."""
    desired_upstream_ids: set[int] = set()
    for claim_snapshot in snapshot.parity_claims:
        upstream = lookups["upstream"][claim_snapshot.upstream_key]
        desired_upstream_ids.add(upstream.id)
        models.ParityClaim.objects.update_or_create(
            card=card,
            upstream=upstream,
            defaults={"level": lookups["parity_level"][claim_snapshot.level_key]},
        )
    card.parity_claims.exclude(upstream_id__in=desired_upstream_ids).delete()
    return len(snapshot.parity_claims)


def _reconcile_references(
    cards_by_key: dict[CardIdentity, models.Card],
    snapshot: BoardSnapshot,
    lookups: dict,
) -> tuple[int, int]:
    """Update card reference rows and derive the compatibility dependency M2M."""
    reference_count = 0
    dependency_edge_count = 0

    for card_snapshot in snapshot.cards:
        card = cards_by_key[card_snapshot.id_key]
        existing = {
            (reference.source_id, reference.order): reference
            for reference in card.outgoing_references.all()
        }
        desired: set[tuple[int, int]] = set()
        dependency_targets: dict[int, models.Card] = {}

        for reference_snapshot in card_snapshot.references:
            target = cards_by_key.get(reference_snapshot.target_key)
            if target is None or target.pk == card.pk:
                continue
            kind = lookups["reference_kind"][reference_snapshot.kind_key]
            source = lookups["reference_source"][reference_snapshot.source_key]
            key = (source.id, reference_snapshot.order)
            desired.add(key)

            reference = existing.get(key)
            if reference is None:
                models.CardReference.objects.create(
                    source_card=card,
                    target_card=target,
                    kind=kind,
                    source=source,
                    raw_text=reference_snapshot.raw_text,
                    order=reference_snapshot.order,
                )
            else:
                dirty_fields = []
                if reference.target_card_id != target.id:
                    reference.target_card = target
                    dirty_fields.append("target_card")
                if reference.kind_id != kind.id:
                    reference.kind = kind
                    dirty_fields.append("kind")
                if reference.raw_text != reference_snapshot.raw_text:
                    reference.raw_text = reference_snapshot.raw_text
                    dirty_fields.append("raw_text")
                if dirty_fields:
                    reference.save(update_fields=[*dirty_fields, "updated_date"])

            if reference_snapshot.kind_key in _DEPENDENCY_REFERENCE_KIND_KEYS:
                dependency_targets[target.id] = target
            reference_count += 1

        for key, reference in existing.items():
            if key not in desired:
                reference.delete()

        card.dependencies.set(dependency_targets.values())
        dependency_edge_count += len(dependency_targets)

    return reference_count, dependency_edge_count


def read_board_snapshot(
    markdown: str | None = None,
    path: str | Path | None = None,
) -> BoardSnapshot:
    """Read markdown from the provided source and return a normalized snapshot."""
    if markdown is None:
        board_path = Path(path) if path else _default_kanban_path()
        markdown = Path(board_path).read_text(encoding="utf-8")
    return parse_board_snapshot(markdown)


@transaction.atomic
def import_board_snapshot(snapshot: BoardSnapshot) -> dict:
    """Reconcile the kanban models against a parsed board snapshot.

    A *sync*, not an append-only upsert: cards / items / parity claims that are
    no longer present in the parsed board are removed, and stable child rows are
    updated in place so their ``UUIDModel`` side rows (and the UUIDs they carry)
    survive a re-import. Returns counts for the resulting graph, not just newly
    created rows. All writes go through ``.save()`` / ``.objects.create()`` so
    the ``UUIDModel`` ``post_save`` signal fires (``bulk_create`` would skip it).
    """
    lookups = _seed_lookups()

    versions: dict[str, models.TargetVersion] = {}
    for version_number in snapshot.target_versions:
        milestone = lookups["milestone"][_milestone_for_version(version_number)]
        versions[version_number], _ = models.TargetVersion.objects.update_or_create(
            number=version_number,
            defaults={"milestone": milestone},
        )

    cards_by_key: dict[CardIdentity, models.Card] = {}
    seen_titles: list[str] = []
    item_count = 0
    parity_count = 0

    for card_snapshot in snapshot.cards:
        card, _ = models.Card.objects.update_or_create(
            title=card_snapshot.title,
            defaults={
                "number": card_snapshot.number,
                "status": lookups["status"][card_snapshot.status_key],
                "milestone": lookups["milestone"][card_snapshot.milestone_key]
                if card_snapshot.milestone_key
                else None,
                "target_version": versions[card_snapshot.target_version],
                "priority": lookups["priority"][card_snapshot.priority_key]
                if card_snapshot.priority_key
                else None,
                "severity": lookups["severity"][card_snapshot.severity_key]
                if card_snapshot.severity_key
                else None,
                "relative_size": lookups["size"][card_snapshot.size_low_key or "m"],
                "relative_size_high": lookups["size"][card_snapshot.size_high_key]
                if card_snapshot.size_high_key
                else None,
                "planning_state": lookups["planning"][card_snapshot.planning_state_key],
                "planning_note": card_snapshot.planning_note,
                "spec": _spec_for(card_snapshot.spec_path),
            },
        )
        cards_by_key[card_snapshot.id_key] = card
        seen_titles.append(card_snapshot.title)
        item_count += _reconcile_items(card, card_snapshot, lookups)
        parity_count += _reconcile_parity(card, card_snapshot, lookups)

    # Reconcile: drop cards no longer on the board (cascades their items, parity
    # claims, dependency edges, and UUID side rows), then the spec / version rows
    # nothing references anymore.
    models.Card.objects.exclude(title__in=seen_titles).delete()
    models.SpecDoc.objects.filter(card__isnull=True).delete()
    models.TargetVersion.objects.filter(cards__isnull=True).delete()

    # Second pass: resolve self-referential references by card id/title. The
    # compatibility ``dependencies`` M2M is derived from dependency-like rows.
    reference_count, dep_edges = _reconcile_references(cards_by_key, snapshot, lookups)

    return {
        "cards": len(cards_by_key),
        "items": item_count,
        "parity_claims": parity_count,
        "card_references": reference_count,
        "dependency_edges": dep_edges,
        "target_versions": len(versions),
    }


def import_board(markdown: str | None = None, path: str | Path | None = None) -> dict:
    """Read a board source, normalize it to a snapshot, then reconcile the DB."""
    return import_board_snapshot(read_board_snapshot(markdown=markdown, path=path))


def _default_kanban_path() -> Path:
    # settings BASE_DIR == examples/fakeshop; the board lives at the repo root.
    from django.conf import settings

    return Path(settings.BASE_DIR).parent.parent / "KANBAN.md"
