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
    relativeSizeHigh {
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
      id
      uuid {
        id
      }
      key
      color
      createdDate
      updatedDate
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
  allKanbanReferenceSources {
    ...CardReferenceSourceFields
  }
  allKanbanBoardDocKinds {
    ...BoardDocKindFields
  }
  allKanbanLabels {
    ...LabelFields
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

fragment CardReferenceSourceFields on CardReferenceSourceType {
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

fragment LabelFields on LabelType {
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
  source {
    ...CardReferenceSourceFields
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
  source {
    ...CardReferenceSourceFields
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
    "allKanbanReferenceSources": "referenceSources",
    "allKanbanBoardDocKinds": "boardDocKinds",
    "allKanbanLabels": "labels",
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


def fetch_dashboard_data() -> dict[str, Any]:
    """Fetch the kanban dashboard payload through the real ``/graphql/`` route."""
    from apps.kanban import models as kanban_models

    data = fetch_graphql_data(
        STATIC_KANBAN_QUERY,
        required_lists=("allCards", "allKanbanBoardDocs", *LOOKUP_FIELDS),
    )

    lookups = {}
    for graphql_name, payload_name in LOOKUP_FIELDS.items():
        lookups[payload_name] = data[graphql_name]

    return {
        "cards": data["allCards"],
        "boardDocs": data["allKanbanBoardDocs"],
        "lookups": lookups,
        "blockingReferenceKindKeys": sorted(kanban_models.BLOCKING_REFERENCE_KIND_KEYS),
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
