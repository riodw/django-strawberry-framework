"""Build the single-file kanban dashboard from the fakeshop GraphQL endpoint."""

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
DEFAULT_HTML_PATH = FAKESHOP_ROOT / "kanban_board.html"
DATA_BLOCK_RE = re.compile(
    r"(?s)<!-- KANBAN_DATA_START -->.*?<!-- KANBAN_DATA_END -->",
)

STATIC_KANBAN_QUERY = """
query StaticKanbanCards {
  allCards {
    id
    uuid {
      id
    }
    title
    number
    planningNote
    summary
    body
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
      note
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
  description
  createdDate
  updatedDate
}

fragment TargetVersionFields on TargetVersionType {
  id
  uuid {
    id
  }
  number
  shippedOn
  gitRef
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
  homepage
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

fragment CardLinkFields on CardType {
  id
  uuid {
    id
  }
  title
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
        help="HTML file to update. Defaults to examples/fakeshop/kanban_board.html.",
    )
    return parser.parse_args()


def configure_django() -> None:
    """Load the fakeshop Django settings for the in-process GraphQL request."""
    sys.path.insert(0, str(FAKESHOP_ROOT))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

    import django

    django.setup()


def fetch_cards() -> list[dict[str, Any]]:
    """Fetch all kanban cards through the real ``/graphql/`` route."""
    from django.test import Client

    response = Client(HTTP_HOST="localhost").post(
        "/graphql/",
        data={"query": STATIC_KANBAN_QUERY},
        content_type="application/json",
    )
    if response.status_code != 200:
        body = response.content.decode("utf-8", errors="replace")
        raise RuntimeError(f"GraphQL request failed with HTTP {response.status_code}:\n{body}")

    payload = response.json()
    if payload.get("errors"):
        raise RuntimeError(json.dumps(payload["errors"], indent=2, sort_keys=True))

    cards = payload["data"]["allCards"]
    if not isinstance(cards, list):
        raise TypeError("GraphQL response did not include data.allCards as a list.")
    return cards


def render_data_block(cards: list[dict[str, Any]]) -> str:
    """Render the replaceable dashboard data block."""
    encoded = json.dumps(cards, ensure_ascii=True, separators=(",", ":"))
    encoded = encoded.replace("</", "<\\/")
    return (
        "<!-- KANBAN_DATA_START -->\n"
        "<script>\n"
        f"window.KANBAN_CARDS = {encoded};\n"
        "</script>\n"
        "<!-- KANBAN_DATA_END -->"
    )


def embed_cards(html_path: Path, cards: list[dict[str, Any]]) -> None:
    """Replace the marked data block in ``html_path``."""
    html = html_path.read_text(encoding="utf-8")
    updated, replacements = DATA_BLOCK_RE.subn(lambda _match: render_data_block(cards), html)
    if replacements != 1:
        raise RuntimeError(f"Expected exactly one kanban data block in {html_path}.")
    html_path.write_text(updated, encoding="utf-8")


def main() -> None:
    """Build the dashboard."""
    args = parse_args()
    configure_django()
    cards = fetch_cards()
    embed_cards(args.html, cards)
    print(f"Wrote {len(cards)} cards to {args.html}")


if __name__ == "__main__":
    main()
