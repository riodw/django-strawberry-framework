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
from pathlib import Path

from django.db import transaction

from . import models

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


def _parity_claims(value: str) -> list[tuple[str, str]]:
    level = "adjacent" if "adjacent" in value.lower() else "required"
    claims = []
    if "⚛" in value:
        claims.append(("graphene_django", level))
    if "🍓" in value:
        claims.append(("strawberry_django", level))
    return claims


def _section_key(name: str) -> str:
    low = name.strip().lower()
    for prefix, key in _SECTION_BY_PREFIX:
        if low.startswith(prefix):
            return key
    return "other"


def parse_cards(markdown: str) -> list[dict]:
    """Split ``markdown`` into a list of parsed-card dicts (no DB access)."""
    lines = markdown.splitlines()
    # Find card header line indices.
    headers = [i for i, line in enumerate(lines) if _CARD_HEADER_RE.match(line)]
    cards: list[dict] = []
    for idx, start in enumerate(headers):
        end = headers[idx + 1] if idx + 1 < len(headers) else len(lines)
        # Stop at the next ``## `` (board-section) header inside the slice.
        block = []
        for line in lines[start + 1 : end]:
            if line.startswith("## "):
                break
            block.append(line)
        header = _CARD_HEADER_RE.match(lines[start])
        card = {
            "status": header["status"].lower(),
            "milestone": header["milestone"].lower() if header["milestone"] else None,
            "number": int(header["number"]),
            "version": header["version"],
            "title": header["title"].strip(),
            "priority": None,
            "severity": None,
            "size_low": None,
            "size_high": None,
            "planning_state": "planned",
            "planning_note": "",
            "parity": [],
            "spec_path": None,
            "items": [],  # list of (section_key, text)
            "dep_keys": set(),  # {(status, number, version)} parsed from Dependencies bullets
        }
        card["id_key"] = (card["status"], card["number"], card["version"])
        current_section = "other"
        order_by_section: dict[str, int] = {}
        for line in block:
            label = _LABEL_RE.match(line)
            if label:
                name, value = label["label"], label["value"]
                if name == "Priority":
                    card["priority"] = _priority_key(value)
                elif name == "Severity":
                    card["severity"] = _severity_key(value)
                elif name == "Relative size":
                    card["size_low"], card["size_high"] = _size_keys(value)
                elif name == "Status":
                    card["planning_state"] = _planning_key(value)
                    card["planning_note"] = value.strip()
                elif name == "Parity":
                    card["parity"] = _parity_claims(value)
                elif name == "Spec":
                    match = _SPEC_PATH_RE.search(value)
                    if match:
                        card["spec_path"] = match.group(1)
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
                card["items"].append(
                    (current_section, text, order),
                )
                if current_section == "dependencies_note":
                    for ref in _CARD_ID_REF_RE.finditer(text):
                        card["dep_keys"].add(
                            (ref["status"].lower(), int(ref["number"]), ref["version"]),
                        )
        cards.append(card)
    return cards


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


def _reconcile_items(card, data: dict, lookups: dict) -> int:
    """Update/create/delete a card's items, preserving UUIDs for stable rows.

    Items are matched on ``(section, order)`` so an unchanged row is updated in
    place -- never deleted -- which keeps its ``UUIDModel`` side row (and thus
    the UUID) stable across re-imports. Returns the resulting item count.
    """
    existing = {(it.section_id, it.order): it for it in card.items.all()}
    is_complete = data["status"] == "done"
    desired: set[tuple[int, int]] = set()
    for section_key, text, order in data["items"]:
        section = lookups["section"][section_key]
        key = (section.id, order)
        desired.add(key)
        item = existing.get(key)
        if item is None:
            models.CardItem.objects.create(
                card=card,
                section=section,
                text=text,
                order=order,
                is_complete=is_complete,
            )
        elif item.text != text or item.is_complete != is_complete:
            item.text = text
            item.is_complete = is_complete
            item.save(
                update_fields=["text", "is_complete", "updated_date"],
            )
    for key, item in existing.items():
        if key not in desired:
            item.delete()
    return len(data["items"])


def _reconcile_parity(card, data: dict, lookups: dict) -> int:
    """Update/create/delete a card's parity claims; return the resulting count."""
    desired_upstream_ids: set[int] = set()
    for upstream_key, level_key in data["parity"]:
        upstream = lookups["upstream"][upstream_key]
        desired_upstream_ids.add(upstream.id)
        models.ParityClaim.objects.update_or_create(
            card=card,
            upstream=upstream,
            defaults={"level": lookups["parity_level"][level_key]},
        )
    card.parity_claims.exclude(upstream_id__in=desired_upstream_ids).delete()
    return len(data["parity"])


@transaction.atomic
def import_board(markdown: str | None = None, path: str | Path | None = None) -> dict:
    """Reconcile the kanban models against ``markdown`` (the source of truth).

    A *sync*, not an append-only upsert: cards / items / parity claims that are
    no longer present in the parsed board are removed, and stable child rows are
    updated in place so their ``UUIDModel`` side rows (and the UUIDs they carry)
    survive a re-import. Returns counts for the resulting graph, not just newly
    created rows. All writes go through ``.save()`` / ``.objects.create()`` so
    the ``UUIDModel`` ``post_save`` signal fires (``bulk_create`` would skip it).
    """
    if markdown is None:
        board_path = Path(path) if path else _default_kanban_path()
        markdown = Path(board_path).read_text(encoding="utf-8")

    lookups = _seed_lookups()
    parsed = parse_cards(markdown)

    versions: dict[str, models.TargetVersion] = {}
    cards_by_key: dict[tuple, models.Card] = {}
    seen_titles: list[str] = []
    item_count = 0
    parity_count = 0

    for data in parsed:
        version_number = data["version"]
        if version_number not in versions:
            milestone = lookups["milestone"][_milestone_for_version(version_number)]
            versions[version_number], _ = models.TargetVersion.objects.update_or_create(
                number=version_number,
                defaults={"milestone": milestone},
            )

        card, _ = models.Card.objects.update_or_create(
            title=data["title"],
            defaults={
                "number": data["number"],
                "status": lookups["status"][data["status"]],
                "milestone": lookups["milestone"][data["milestone"]] if data["milestone"] else None,
                "target_version": versions[version_number],
                "priority": lookups["priority"][data["priority"]] if data["priority"] else None,
                "severity": lookups["severity"][data["severity"]] if data["severity"] else None,
                "relative_size": lookups["size"][data["size_low"] or "m"],
                "relative_size_high": lookups["size"][data["size_high"]]
                if data["size_high"]
                else None,
                "planning_state": lookups["planning"][data["planning_state"]],
                "planning_note": data["planning_note"],
                "spec": _spec_for(data["spec_path"]),
            },
        )
        cards_by_key[data["id_key"]] = card
        seen_titles.append(data["title"])
        item_count += _reconcile_items(card, data, lookups)
        parity_count += _reconcile_parity(card, data, lookups)

    # Reconcile: drop cards no longer on the board (cascades their items, parity
    # claims, dependency edges, and UUID side rows), then the spec / version rows
    # nothing references anymore.
    models.Card.objects.exclude(title__in=seen_titles).delete()
    models.SpecDoc.objects.filter(card__isnull=True).delete()
    models.TargetVersion.objects.filter(cards__isnull=True).delete()

    # Second pass: resolve self-referential dependency edges by referenced card id.
    dep_edges = 0
    for data in parsed:
        card = cards_by_key[data["id_key"]]
        card.dependencies.clear()
        targets = [
            cards_by_key[k] for k in data["dep_keys"] if k in cards_by_key and k != data["id_key"]
        ]
        if targets:
            card.dependencies.add(*targets)
            dep_edges += len(targets)

    return {
        "cards": len(cards_by_key),
        "items": item_count,
        "parity_claims": parity_count,
        "dependency_edges": dep_edges,
        "target_versions": len(versions),
    }


def _default_kanban_path() -> Path:
    # settings BASE_DIR == examples/fakeshop; the board lives at the repo root.
    from django.conf import settings

    return Path(settings.BASE_DIR).parent.parent / "KANBAN.md"
