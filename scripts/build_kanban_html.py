"""Build ``KANBAN.html`` and the canonical ``KANBAN.json`` from the fakeshop GraphQL endpoint.

``KANBAN.json`` is the first-class, machine-diffable board snapshot: the same
dashboard payload embedded in ``KANBAN.html``, deep-sorted for stable diffs and
carrying an ``asOf`` block (the max ``updatedDate`` across the kanban tables plus a
render timestamp). Both artifacts derive from one :func:`fetch_dashboard_data` call.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path
from typing import Any

# Re-exported for back-compat: build_kanban_md / build_glossary_md / build_tree_md /
# check_alpha_parity import these names from this module.
try:
    from _kanban_lib import (
        cli_exit,
        configure_django,
        fetch_graphql_data,
        version_tuple,
    )
except ModuleNotFoundError:  # imported as ``scripts.build_kanban_html`` (repo root on path)
    from scripts._kanban_lib import (
        cli_exit,
        configure_django,
        fetch_graphql_data,
        version_tuple,
    )

REPO_ROOT = Path(__file__).resolve().parents[1]
FAKESHOP_ROOT = REPO_ROOT / "examples" / "fakeshop"
DEFAULT_HTML_PATH = REPO_ROOT / "KANBAN.html"
DEFAULT_JSON_PATH = REPO_ROOT / "KANBAN.json"
DATA_BLOCK_RE = re.compile(
    r"(?s)<!-- KANBAN_DATA_START -->.*?<!-- KANBAN_DATA_END -->",
)

__all__ = ["configure_django", "fetch_graphql_data", "version_tuple"]

STATIC_KANBAN_QUERY = """
query StaticKanbanDashboard {
  allCards {
    id
    uuid {
      id
    }
    title
    slug
    isBlocked
    cardId
    number
    planningNote
    createdDate
    updatedDate
    status {
      ...StatusFields
    }
    milestone {
      ...MilestoneFields
    }
    targetVersion {
      ...TargetVersionFields
    }
    priority {
      ...PriorityFields
    }
    relativeSize {
      ...RelativeSizeFields
    }
    spec {
      id
      uuid {
        id
      }
      name
      path
      url
      createdDate
      updatedDate
    }
    parityClaims {
      id
      uuid {
        id
      }
      createdDate
      updatedDate
      upstream {
        ...UpstreamFields
      }
      level {
        ...ParityLevelFields
      }
    }
    items {
      id
      uuid {
        id
      }
      text
      order
      isComplete
      createdDate
      updatedDate
      section {
        ...SectionFields
      }
    }
    outgoingReferences {
      ...OutgoingReferenceFields
    }
    incomingReferences {
      ...IncomingReferenceFields
    }
    dependencies {
      ...CardLinkFields
    }
    dependents {
      ...CardLinkFields
    }
    labels {
      ...CardBadgeFields
    }
    glossaryLinks {
      id
      uuid {
        id
      }
      rawText
      order
      createdDate
      updatedDate
      term {
        id
        title
        anchor
        statusText
      }
    }
    changedFiles {
      ...TrackedPathFields
    }
    pathLinks {
      id
      uuid {
        id
      }
      kind
      createdDate
      updatedDate
      path {
        ...TrackedPathFields
      }
    }
  }
  allKanbanBoardDocs {
    id
    uuid {
      id
    }
    key
    title
    order
    body
    createdDate
    updatedDate
    kind {
      ...BoardDocKindFields
    }
    cardReferences {
      id
      uuid {
        id
      }
      rawText
      order
      createdDate
      updatedDate
      card {
        ...CardLinkFields
      }
    }
  }
  allKanbanStatuses {
    ...StatusFields
  }
  allKanbanMilestones {
    ...MilestoneFields
  }
  allKanbanTargetVersions {
    ...TargetVersionFields
  }
  allKanbanPriorities {
    ...PriorityFields
  }
  allKanbanRelativeSizes {
    ...RelativeSizeFields
  }
  allKanbanUpstreams {
    ...UpstreamFields
  }
  allKanbanParityLevels {
    ...ParityLevelFields
  }
  allKanbanSections {
    ...SectionFields
  }
  allKanbanReferenceKinds {
    ...CardReferenceKindFields
  }
  allKanbanBoardDocKinds {
    ...BoardDocKindFields
  }
  allKanbanTrackedPaths {
    ...TrackedPathFields
  }
}

fragment StatusFields on StatusType {
  id
  uuid {
    id
  }
  key
  label
  order
  createdDate
  updatedDate
}

fragment MilestoneFields on MilestoneType {
  id
  uuid {
    id
  }
  key
  label
  order
  versionFloor
  versionCeiling
  createdDate
  updatedDate
}

fragment TargetVersionFields on TargetVersionType {
  id
  uuid {
    id
  }
  number
  major
  minor
  patch
  createdDate
  updatedDate
  milestone {
    id
    key
    label
    order
  }
}

fragment PriorityFields on PriorityType {
  id
  uuid {
    id
  }
  key
  label
  order
  createdDate
  updatedDate
}

fragment RelativeSizeFields on RelativeSizeType {
  id
  uuid {
    id
  }
  key
  label
  order
  description
  createdDate
  updatedDate
}

fragment UpstreamFields on UpstreamType {
  id
  uuid {
    id
  }
  key
  label
  order
  emoji
  createdDate
  updatedDate
}

fragment ParityLevelFields on ParityLevelType {
  id
  uuid {
    id
  }
  key
  label
  order
  createdDate
  updatedDate
}

fragment SectionFields on SectionType {
  id
  uuid {
    id
  }
  key
  label
  order
  createdDate
  updatedDate
}

fragment CardReferenceKindFields on CardReferenceKindType {
  id
  uuid {
    id
  }
  key
  label
  order
  createdDate
  updatedDate
}

fragment BoardDocKindFields on BoardDocKindType {
  id
  uuid {
    id
  }
  key
  label
  order
  createdDate
  updatedDate
}

fragment CardBadgeFields on LabelType {
  id
  uuid {
    id
  }
  key
  color
  createdDate
  updatedDate
}

fragment TrackedPathFields on TrackedPathType {
  id
  uuid {
    id
  }
  path
  isCurrent
  isDirectory
  createdDate
  updatedDate
}

fragment CardLinkFields on CardType {
  id
  uuid {
    id
  }
  title
  slug
  cardId
  number
  status {
    id
    key
    label
    order
  }
  milestone {
    id
    key
    label
    order
  }
  targetVersion {
    id
    number
  }
}

fragment OutgoingReferenceFields on CardReferenceType {
  id
  uuid {
    id
  }
  rawText
  order
  createdDate
  updatedDate
  kind {
    ...CardReferenceKindFields
  }
  targetCard {
    ...CardLinkFields
  }
}

fragment IncomingReferenceFields on CardReferenceType {
  id
  uuid {
    id
  }
  rawText
  order
  createdDate
  updatedDate
  kind {
    ...CardReferenceKindFields
  }
  sourceCard {
    ...CardLinkFields
  }
}
"""


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Embed kanban GraphQL JSON into the single-file dashboard.",
    )
    parser.add_argument(
        "--html",
        type=Path,
        default=DEFAULT_HTML_PATH,
        help="HTML file to update. Defaults to the repository-root KANBAN.html.",
    )
    parser.add_argument(
        "--json",
        type=Path,
        default=DEFAULT_JSON_PATH,
        dest="json_path",
        help="Canonical JSON snapshot to write. Defaults to the repository-root KANBAN.json.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit 1 if KANBAN.html / KANBAN.json are not already up to date (0 fresh, 2 on error).",
    )
    return parser.parse_args()


LOOKUP_FIELDS = {
    "allKanbanStatuses": "statuses",
    "allKanbanMilestones": "milestones",
    "allKanbanTargetVersions": "targetVersions",
    "allKanbanPriorities": "priorities",
    "allKanbanRelativeSizes": "relativeSizes",
    "allKanbanUpstreams": "upstreams",
    "allKanbanParityLevels": "parityLevels",
    "allKanbanSections": "sections",
    "allKanbanReferenceKinds": "referenceKinds",
    "allKanbanBoardDocKinds": "boardDocKinds",
    "allKanbanTrackedPaths": "trackedPaths",
}


def _pct(part: float, whole: float) -> float:
    """Percent ``part`` of ``whole``, one decimal, 0.0 when ``whole`` is 0."""
    return round(100 * part / whole, 1) if whole else 0.0


def release_version(milestones: list[dict[str, Any]]) -> tuple[int, ...]:
    """Return the road-to-release target version, derived from Milestone rows.

    The release boundary is the highest ``versionCeiling`` across the milestone
    lookup table (``alpha`` ceils at ``0.1.0``, ``beta`` at ``1.0.0``), so the
    ``1.0.0`` cut is read from the DB rather than frozen in a script constant -
    re-versioning a milestone reshapes the progress board on the next build with
    no code edit. Raises when no milestone carries a ceiling (the metric would
    otherwise silently compare against ``(0,)`` and count everything as shipped).
    """
    ceilings = [
        version_tuple(milestone["versionCeiling"])
        for milestone in milestones
        if milestone.get("versionCeiling")
    ]
    if not ceilings:
        raise RuntimeError(
            "No milestone carries a versionCeiling; cannot derive the road-to-release "
            "target version for the progress board.",
        )
    return max(ceilings)


def compute_progress_metrics(
    cards: list[dict[str, Any]],
    target_release: tuple[int, ...],
) -> dict[str, Any]:
    """Aggregate road-to-``1.0.0`` progress from the card set.

    Backlog cards are excluded (deferred / un-triaged). Cards are counted raw and
    weighted by relative size (XS=1 .. XL=5) so the figure is not skewed by many tiny
    cards, then broken down per milestone. Every label, ordering, the pre-/post-release
    split (``target_release``, itself derived from the milestone ``versionCeiling``
    values by :func:`release_version`), and the per-size weight (``RelativeSize.order``)
    are read from the live DB, so nothing here goes stale or has to be re-typed when a
    milestone is renamed or re-versioned -- both exports recompute it on every build.

    Two headline scopes are reported (the board surfaces both so neither misleads):

    - ``toward`` -- progress *toward* ``1.0.0``: cards whose ``targetVersion`` ships at
      or before ``1.0.0`` (the ``1.0.0`` release card itself counts -- it is the work
      that reaches ``1.0.0``). Card target version, not milestone, is the signal: a
      card's milestone is derived from its target version, but the boundary case (the
      ``1.0.0`` cut, filed under the post-``1.0.0`` ``stable`` milestone) belongs to
      the road to ``1.0.0``.
    - ``overall`` -- every non-backlog card regardless of target version (the full
      picture, including any post-``1.0.0`` work).

    The two coincide whenever no non-backlog card targets a post-``1.0.0`` version; the
    headline then shows a single figure (the dual line appears only once genuinely
    post-``1.0.0`` work is in flight).
    """

    def rank(card: dict[str, Any]) -> int:
        # ``RelativeSize.order`` is 0-indexed (XS=0 .. XL=4); weight by ``order + 1``
        # (XS=1 .. XL=5) so an XS card still counts as 1 unit of work rather than
        # being invisible to the size-weighted figure.
        size = card.get("relativeSize")
        return size["order"] + 1 if size else 0

    def targets_by_release(card: dict[str, Any]) -> bool:
        # The 1.0.0 release card ships exactly 1.0.0, so the boundary is inclusive
        # (``<=``). A card with no target version is treated as pre-release work.
        target = card.get("targetVersion") or {}
        number = target.get("number")
        return number is None or version_tuple(number) <= target_release

    universe = [card for card in cards if (card.get("status") or {}).get("key") != "backlog"]

    milestones: dict[str, dict[str, Any]] = {}
    for card in universe:
        milestone = card.get("milestone") or {}
        key = milestone.get("key", "?")
        bucket = milestones.setdefault(
            key,
            {
                "key": key,
                "label": milestone.get("label", key),
                "order": milestone.get("order", 0),
                "done": 0,
                "total": 0,
                "rank_done": 0,
                "rank_total": 0,
            },
        )
        bucket["total"] += 1
        bucket["rank_total"] += rank(card)
        if card["status"]["key"] == "done":
            bucket["done"] += 1
            bucket["rank_done"] += rank(card)

    def scope(predicate: Any) -> dict[str, Any]:
        members = [card for card in universe if predicate(card)]
        done = [card for card in members if card["status"]["key"] == "done"]
        rank_total = sum(rank(card) for card in members)
        return {
            "cards_done": len(done),
            "cards_total": len(members),
            "cards_pct": _pct(len(done), len(members)),
            "weighted_pct": _pct(sum(rank(card) for card in done), rank_total),
        }

    return {
        "toward": scope(targets_by_release),
        "overall": scope(lambda _card: True),
        "milestones": milestones,
    }


def render_progress_markdown(metrics: dict[str, Any], release_label: str) -> str:
    """Render the progress metrics as a markdown body (headline + per-milestone table).

    ``release_label`` is the road-to-release target version (e.g. ``"1.0.0"``),
    derived from the milestone ``versionCeiling`` values, not frozen in the prose.
    """
    toward = metrics["toward"]
    overall = metrics["overall"]
    cards_pct = toward["cards_pct"]
    crossed = "Past the 50% mark." if cards_pct >= 50 else "Not yet at the 50% mark."
    headline = (
        f"**{cards_pct}% complete** toward `{release_label}` - {toward['cards_done']} of "
        f"{toward['cards_total']} cards done ({toward['weighted_pct']}% size-weighted)."
    )
    # Surface the full-board figure too whenever a post-release milestone widens the
    # non-backlog set beyond the toward-release scope, so neither number misleads.
    if overall["cards_total"] != toward["cards_total"]:
        headline += (
            f" Across all non-backlog cards (incl. post-`{release_label}`), "
            f"{overall['cards_done']} of {overall['cards_total']} ({overall['cards_pct']}%, "
            f"{overall['weighted_pct']}% size-weighted)."
        )
    headline += f" {crossed} Backlog excluded; size-weighted by relative size (XS=1 .. XL=5)."

    lines = [
        headline,
        "",
        "| Milestone | Cards done | Size-weighted |",
        "| --- | --- | --- |",
    ]
    ordered = sorted(metrics["milestones"].values(), key=lambda bucket: bucket["order"])
    for bucket in ordered:
        cards = f"{bucket['done']}/{bucket['total']} ({_pct(bucket['done'], bucket['total'])}%)"
        weighted = f"{_pct(bucket['rank_done'], bucket['rank_total'])}%"
        lines.append(f"| {bucket['label']} | {cards} | {weighted} |")
    return "\n".join(lines)


def progress_board_doc(
    board_docs: list[dict[str, Any]],
    cards: list[dict[str, Any]],
    milestones: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build the synthetic, export-time ``Progress to <release>`` reference board doc.

    Clones the kind / namespace / timestamps from the existing ``snapshot`` reference
    doc so it groups with the other reference docs in both exports, and carries
    pre-resolved numbers in its body (literal markdown -- no client-side token
    recompute, so the KANBAN.html app renders it with no JS change).

    Loud, not silent: raises when there is no ``snapshot`` doc to anchor against, so a
    missing anchor fails the build instead of silently dropping the progress board.
    The road-to-release target and title are derived from the milestone
    ``versionCeiling`` values (see :func:`release_version`).
    """
    anchor = next((doc for doc in board_docs if doc.get("key") == "snapshot"), None)
    if anchor is None:
        raise RuntimeError(
            "No 'snapshot' board doc to anchor the synthetic progress board against; "
            "the progress metrics cannot be positioned. Add a 'snapshot' reference doc.",
        )
    target_release = release_version(milestones)
    release_label = ".".join(str(part) for part in target_release)
    metrics = compute_progress_metrics(cards, target_release)
    return {
        "id": "synthetic:progress-to-release",
        "uuid": {"id": "synthetic:progress-to-release"},
        "namespace": anchor.get("namespace", "kanban"),
        "key": "progress-to-release",
        "title": f"Progress to {release_label}",
        "order": anchor.get("order", 3) + 0.5,
        "body": render_progress_markdown(metrics, release_label),
        "includeHeading": True,
        "kind": anchor["kind"],
        "createdDate": anchor.get("createdDate"),
        "updatedDate": anchor.get("updatedDate"),
        "cardReferences": [],
    }


def fetch_dashboard_data() -> dict[str, Any]:
    """Fetch the kanban dashboard payload through the real ``/graphql/`` route.

    A synthetic ``Progress to <release>`` board doc is injected right after the
    ``snapshot`` doc so both exports surface the road-to-release metrics with no
    per-builder render change.
    """
    from apps.kanban import models

    data = fetch_graphql_data(
        STATIC_KANBAN_QUERY,
        required_lists=("allCards", "allKanbanBoardDocs", *LOOKUP_FIELDS),
    )

    lookups = {}
    for graphql_name, payload_name in LOOKUP_FIELDS.items():
        lookups[payload_name] = data[graphql_name]

    board_docs = data["allKanbanBoardDocs"]
    progress = progress_board_doc(board_docs, data["allCards"], lookups["milestones"])
    snapshot_index = next(
        (index for index, doc in enumerate(board_docs) if doc.get("key") == "snapshot"),
        len(board_docs) - 1,
    )
    board_docs.insert(snapshot_index + 1, progress)

    return {
        "cards": data["allCards"],
        "boardDocs": board_docs,
        "lookups": lookups,
        "blockingReferenceKindKeys": sorted(models.BLOCKING_REFERENCE_KIND_KEYS),
    }


def _sort_cards(cards: list[dict[str, Any]]) -> None:
    """Sort every per-card child list, then the cards themselves, in place.

    Deterministic ordering (not resolver order) so both the HTML data block and
    the KANBAN.json snapshot diff cleanly build over build.
    """
    for card in cards:
        card.get("items", []).sort(
            key=lambda item: (item["section"]["order"], item["order"], item["id"]),
        )
        card.get("parityClaims", []).sort(
            key=lambda claim: (claim["upstream"]["order"], claim["id"]),
        )
        card.get("outgoingReferences", []).sort(key=lambda ref: (ref["order"], ref["id"]))
        card.get("incomingReferences", []).sort(key=lambda ref: (ref["order"], ref["id"]))
        card.get("dependencies", []).sort(key=lambda dep: dep["number"])
        card.get("dependents", []).sort(key=lambda dep: dep["number"])
        card.get("labels", []).sort(key=lambda label: label["key"])
        card.get("glossaryLinks", []).sort(key=lambda link: (link["order"], link["id"]))
        card.get("pathLinks", []).sort(key=lambda link: link["path"]["path"])
        card.get("changedFiles", []).sort(key=lambda path: path["path"])
    cards.sort(key=lambda card: card["number"])


def _sort_board_docs(board_docs: list[dict[str, Any]]) -> None:
    """Sort board docs and their card references in place."""
    for doc in board_docs:
        doc.get("cardReferences", []).sort(key=lambda ref: (ref["order"], ref["id"]))
    board_docs.sort(key=lambda doc: (doc["order"], doc["key"]))


def _sort_lookups(lookups: dict[str, list[dict[str, Any]]]) -> None:
    """Sort each lookup array in place (by ``order`` where present, else path)."""
    for name, rows in lookups.items():
        if name == "trackedPaths":
            rows.sort(key=lambda row: row["path"])
        else:
            rows.sort(key=lambda row: (row.get("order", 0), row["id"]))


def build_dashboard_snapshot(dashboard_data: dict[str, Any]) -> dict[str, Any]:
    """Deep-sort every list in the dashboard payload in place, returning it."""
    _sort_cards(dashboard_data["cards"])
    _sort_board_docs(dashboard_data["boardDocs"])
    _sort_lookups(dashboard_data["lookups"])
    return dashboard_data


def _max_updated_date(snapshot: dict[str, Any]) -> str | None:
    """Return the maximum ``updatedDate`` across every row in the snapshot.

    ISO-8601 UTC strings (identical ``+00:00`` offset) compare lexicographically,
    so a plain ``max`` over the collected values is a correct as-of anchor.
    """
    best: str | None = None

    def walk(node: Any) -> None:
        nonlocal best
        if isinstance(node, dict):
            value = node.get("updatedDate")
            if isinstance(value, str) and (best is None or value > best):
                best = value
            for child in node.values():
                walk(child)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(snapshot)
    return best


def build_canonical_export(snapshot: dict[str, Any]) -> dict[str, Any]:
    """Wrap a (sorted) snapshot with the ``asOf`` block for the KANBAN.json artifact.

    ``asOf.maxUpdatedDate`` is data-derived and deterministic (the board's freshness
    anchor); ``asOf.generatedAt`` is the render wall-clock and is the ONLY field that
    varies between two runs over unchanged data (``--check`` ignores it).
    """
    return {
        "asOf": {
            "maxUpdatedDate": _max_updated_date(snapshot),
            "generatedAt": dt.datetime.now(dt.timezone.utc).isoformat(),
        },
        **snapshot,
    }


def render_json(export: dict[str, Any]) -> str:
    """Render the canonical KANBAN.json text (indented, key-sorted, newline-terminated)."""
    return json.dumps(export, ensure_ascii=True, indent=2, sort_keys=True) + "\n"


def render_data_block(dashboard_data: dict[str, Any]) -> str:
    """Render the replaceable dashboard data block."""
    encoded = json.dumps(dashboard_data, ensure_ascii=True, separators=(",", ":"))
    encoded = encoded.replace("</", "<\\/")
    return (
        "<!-- KANBAN_DATA_START -->\n"
        "<script>\n"
        f"window.KANBAN_DATA = {encoded};\n"
        "window.KANBAN_CARDS = window.KANBAN_DATA.cards;\n"
        "</script>\n"
        "<!-- KANBAN_DATA_END -->"
    )


def embed_dashboard_data(html_path: Path, dashboard_data: dict[str, Any]) -> None:
    """Replace the marked data block in ``html_path``."""
    html = html_path.read_text(encoding="utf-8")
    updated, replacements = DATA_BLOCK_RE.subn(
        lambda _match: render_data_block(dashboard_data),
        html,
    )
    if replacements != 1:
        raise RuntimeError(f"Expected exactly one kanban data block in {html_path}.")
    html_path.write_text(updated, encoding="utf-8")


def _strip_volatile(export: dict[str, Any]) -> dict[str, Any]:
    """Return ``export`` with the wall-clock ``asOf.generatedAt`` removed, for --check."""
    clone = dict(export)
    as_of = dict(clone.get("asOf", {}))
    as_of.pop("generatedAt", None)
    clone["asOf"] = as_of
    return clone


def _html_is_fresh(html_path: Path, data_block: str) -> bool:
    """Return whether ``html_path`` already carries the freshly rendered data block."""
    if not html_path.is_file():
        return False
    match = DATA_BLOCK_RE.search(html_path.read_text(encoding="utf-8"))
    return match is not None and match.group(0) == data_block


def _json_is_fresh(json_path: Path, export: dict[str, Any]) -> bool:
    """Return whether ``json_path`` matches ``export`` (ignoring the wall-clock field)."""
    if not json_path.is_file():
        return False
    try:
        current = json.loads(json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    return _strip_volatile(current) == _strip_volatile(export)


def main() -> int:
    """Build the HTML dashboard and the canonical KANBAN.json (or check freshness)."""
    args = parse_args()
    configure_django()
    snapshot = build_dashboard_snapshot(fetch_dashboard_data())
    data_block = render_data_block(snapshot)
    export = build_canonical_export(snapshot)

    if args.check:
        stale = [
            str(path)
            for path, fresh in (
                (args.html, _html_is_fresh(args.html, data_block)),
                (args.json_path, _json_is_fresh(args.json_path, export)),
            )
            if not fresh
        ]
        if stale:
            print(
                f"Stale (run scripts/build_kanban_html.py): {', '.join(stale)}",
                file=sys.stderr,
            )
            return 1
        print(f"{args.html} and {args.json_path} are up to date.")
        return 0

    embed_dashboard_data(args.html, snapshot)
    args.json_path.write_text(render_json(export), encoding="utf-8")
    print(
        "Wrote "
        f"{len(snapshot['cards'])} cards, "
        f"{len(snapshot['boardDocs'])} board docs, and "
        f"{len(snapshot['lookups'])} lookup arrays to {args.html} and {args.json_path}",
    )
    return 0


if __name__ == "__main__":
    cli_exit(main)
