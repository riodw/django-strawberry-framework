"""Build ``KANBAN.html`` from the fakeshop GraphQL endpoint."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
FAKESHOP_ROOT = REPO_ROOT / "examples" / "fakeshop"
DEFAULT_HTML_PATH = REPO_ROOT / "KANBAN.html"
DATA_BLOCK_RE = re.compile(
    r"(?s)<!-- KANBAN_DATA_START -->.*?<!-- KANBAN_DATA_END -->",
)

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
    severity {
      ...SeverityFields
    }
    relativeSize {
      ...RelativeSizeFields
    }
    planningState {
      ...PlanningStateFields
    }
    spec {
      id
      uuid {
        id
      }
      name
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
  allKanbanSeverities {
    ...SeverityFields
  }
  allKanbanRelativeSizes {
    ...RelativeSizeFields
  }
  allKanbanPlanningStates {
    ...PlanningStateFields
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

fragment SeverityFields on SeverityType {
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
  rank
  description
  createdDate
  updatedDate
}

fragment PlanningStateFields on PlanningStateType {
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
  planningState {
    id
    key
    label
    order
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
    return parser.parse_args()


def configure_django() -> None:
    """Load the fakeshop Django settings for the in-process GraphQL request.

    Mutates process state without undoing it: prepends ``FAKESHOP_ROOT`` to
    ``sys.path`` and sets ``DJANGO_SETTINGS_MODULE``. Fine for this top-level
    build script (one process, exits after writing the dashboard); if this
    module is ever imported into a longer-lived process, isolate or restore
    these instead.
    """
    sys.path.insert(0, str(FAKESHOP_ROOT))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

    import django

    django.setup()


LOOKUP_FIELDS = {
    "allKanbanStatuses": "statuses",
    "allKanbanMilestones": "milestones",
    "allKanbanTargetVersions": "targetVersions",
    "allKanbanPriorities": "priorities",
    "allKanbanSeverities": "severities",
    "allKanbanRelativeSizes": "relativeSizes",
    "allKanbanPlanningStates": "planningStates",
    "allKanbanUpstreams": "upstreams",
    "allKanbanParityLevels": "parityLevels",
    "allKanbanSections": "sections",
    "allKanbanReferenceKinds": "referenceKinds",
    "allKanbanBoardDocKinds": "boardDocKinds",
}


def fetch_graphql_data(query: str, *, required_lists: tuple[str, ...]) -> dict[str, Any]:
    """Fetch a GraphQL payload and validate required top-level list fields."""
    from django.test import Client

    response = Client(HTTP_HOST="localhost").post(
        "/graphql/",
        data={"query": query},
        content_type="application/json",
    )
    if response.status_code != 200:
        body = response.content.decode("utf-8", errors="replace")
        raise RuntimeError(f"GraphQL request failed with HTTP {response.status_code}:\n{body}")

    payload = response.json()
    if payload.get("errors"):
        raise RuntimeError(json.dumps(payload["errors"], indent=2, sort_keys=True))

    data = payload.get("data") or {}
    for key in required_lists:
        if not isinstance(data.get(key), list):
            raise TypeError(f"GraphQL response did not include data.{key} as a list.")
    return data


MILESTONE_ROWS = (
    ("alpha", "Alpha (`0.0.x`, parity)"),
    ("beta", "Beta (`0.1.x`)"),
    ("stable", "Stable (`1.0.0` cut)"),
)


def _pct(part: float, whole: float) -> float:
    """Percent ``part`` of ``whole``, one decimal, 0.0 when ``whole`` is 0."""
    return round(100 * part / whole, 1) if whole else 0.0


def compute_progress_metrics(cards: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate road-to-``1.0.0`` progress from the card set.

    Backlog cards are excluded (post-``1.0`` / deferred). Cards are counted raw and
    weighted by relative size (XS=1 .. XL=5) so the figure is not skewed by many tiny
    cards, then broken down per milestone. Pure derivation from the live board, so it
    can never go stale -- both exports recompute it on every build.
    """

    def rank(card: dict[str, Any]) -> int:
        # ``RelativeSize.rank`` is 0-indexed (XS=0 .. XL=4); weight by ``rank + 1``
        # (XS=1 .. XL=5) so an XS card still counts as 1 unit of work rather than
        # being invisible to the size-weighted figure.
        size = card.get("relativeSize")
        return size["rank"] + 1 if size else 0

    universe = [card for card in cards if (card.get("status") or {}).get("key") != "backlog"]
    done = [card for card in universe if card["status"]["key"] == "done"]

    milestones: dict[str, dict[str, int]] = {}
    for card in universe:
        key = (card.get("milestone") or {}).get("key", "?")
        bucket = milestones.setdefault(
            key,
            {
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

    rank_total = sum(rank(card) for card in universe)
    rank_done = sum(rank(card) for card in done)
    return {
        "cards_done": len(done),
        "cards_total": len(universe),
        "cards_pct": _pct(len(done), len(universe)),
        "weighted_pct": _pct(rank_done, rank_total),
        "milestones": milestones,
    }


def render_progress_markdown(metrics: dict[str, Any]) -> str:
    """Render the progress metrics as a markdown body (headline + per-milestone table)."""
    cards_pct = metrics["cards_pct"]
    crossed = "Past the 50% mark." if cards_pct >= 50 else "Not yet at the 50% mark."
    lines = [
        f"**{cards_pct}% complete** toward `1.0.0` - {metrics['cards_done']} of "
        f"{metrics['cards_total']} cards done ({metrics['weighted_pct']}% size-weighted). "
        f"{crossed} Backlog excluded; size-weighted by relative size (XS=1 .. XL=5).",
        "",
        "| Milestone | Cards done | Size-weighted |",
        "| --- | --- | --- |",
    ]
    for key, label in MILESTONE_ROWS:
        bucket = metrics["milestones"].get(key)
        if not bucket:
            continue
        cards = f"{bucket['done']}/{bucket['total']} ({_pct(bucket['done'], bucket['total'])}%)"
        lines.append(f"| {label} | {cards} | {_pct(bucket['rank_done'], bucket['rank_total'])}% |")
    alpha = metrics["milestones"].get("alpha")
    if alpha and alpha["total"]:
        lines.extend(
            [
                "",
                f"To the `0.1.0` parity milestone (Alpha complete): "
                f"**{_pct(alpha['done'], alpha['total'])}%**.",
            ],
        )
    return "\n".join(lines)


def progress_board_doc(
    board_docs: list[dict[str, Any]],
    cards: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """Build the synthetic, export-time ``Progress to 1.0.0`` reference board doc.

    Clones the kind / namespace / timestamps from the existing ``snapshot`` reference
    doc so it groups with the other reference docs in both exports, and carries
    pre-resolved numbers in its body (literal markdown -- no client-side token
    recompute, so the KANBAN.html app renders it with no JS change). Returns ``None``
    if there is no ``snapshot`` doc to anchor against.
    """
    anchor = next((doc for doc in board_docs if doc.get("key") == "snapshot"), None)
    if anchor is None:
        return None
    return {
        "id": "synthetic:progress-to-1-0-0",
        "uuid": {"id": "synthetic:progress-to-1-0-0"},
        "namespace": anchor.get("namespace", "kanban"),
        "key": "progress-to-1-0-0",
        "title": "Progress to 1.0.0",
        "order": anchor.get("order", 3) + 0.5,
        "body": render_progress_markdown(compute_progress_metrics(cards)),
        "includeHeading": True,
        "kind": anchor["kind"],
        "createdDate": anchor.get("createdDate"),
        "updatedDate": anchor.get("updatedDate"),
        "cardReferences": [],
    }


def fetch_dashboard_data() -> dict[str, Any]:
    """Fetch the kanban dashboard payload through the real ``/graphql/`` route.

    A synthetic ``Progress to 1.0.0`` board doc is injected right after the
    ``snapshot`` doc so both exports surface the road-to-``1.0.0`` metrics with no
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
    progress = progress_board_doc(board_docs, data["allCards"])
    if progress is not None:
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


def main() -> None:
    """Build the dashboard."""
    args = parse_args()
    configure_django()
    dashboard_data = fetch_dashboard_data()
    embed_dashboard_data(args.html, dashboard_data)
    print(
        "Wrote "
        f"{len(dashboard_data['cards'])} cards, "
        f"{len(dashboard_data['boardDocs'])} board docs, and "
        f"{len(dashboard_data['lookups'])} lookup arrays to {args.html}",
    )


if __name__ == "__main__":
    main()
