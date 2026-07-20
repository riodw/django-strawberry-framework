"""Build ``docs/GLOSSARY.md`` from the glossary app's GraphQL payload."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

try:
    from _kanban_lib import cli_exit
    from build_kanban_html import configure_django, fetch_graphql_data
    from build_kanban_md import finalize_markdown
except ModuleNotFoundError:  # imported as ``scripts.build_glossary_md`` (repo root on path)
    from scripts._kanban_lib import cli_exit
    from scripts.build_kanban_html import configure_django, fetch_graphql_data
    from scripts.build_kanban_md import finalize_markdown

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MD_PATH = REPO_ROOT / "docs" / "GLOSSARY.md"

STATIC_GLOSSARY_QUERY = """
query StaticGlossary {
  allGlossaryDocuments {
    id
    key
    title
    order
    body
    includeHeading
  }
  allGlossaryTerms {
    id
    title
    titleSort
    anchor
    statusText
    body
    entryOrder
    indexOrder
    status {
      id
      key
      label
      order
    }
  }
  allGlossaryCategoryMemberships {
    id
    order
    category {
      id
      key
      label
      order
    }
    term {
      id
      title
      anchor
    }
  }
  allGlossarySpecMentions {
    id
    specPath
    specName
    termText
    notes
    order
    term {
      id
      title
      anchor
    }
  }
}
"""


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Render docs/GLOSSARY.md from the glossary GraphQL payload.",
    )
    parser.add_argument(
        "--md",
        type=Path,
        default=DEFAULT_MD_PATH,
        help="Markdown file to write. Defaults to docs/GLOSSARY.md.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit 1 if docs/GLOSSARY.md is not already up to date (0 fresh, 2 on error).",
    )
    return parser.parse_args()


def fetch_glossary_data() -> dict[str, Any]:
    """Fetch glossary data through the real ``/graphql/`` route."""
    data = fetch_graphql_data(
        STATIC_GLOSSARY_QUERY,
        required_lists=(
            "allGlossaryDocuments",
            "allGlossaryTerms",
            "allGlossaryCategoryMemberships",
            "allGlossarySpecMentions",
        ),
    )
    return {
        "documents": data["allGlossaryDocuments"],
        "terms": data["allGlossaryTerms"],
        "categoryMemberships": data["allGlossaryCategoryMemberships"],
        "specMentions": data["allGlossarySpecMentions"],
    }


def term_link(term: dict[str, Any], *, label: str | None = None) -> str:
    """Render an in-page markdown link for a glossary term."""
    return f"[{label or term['title']}](#{term['anchor']})"


def render_document(doc: dict[str, Any]) -> list[str]:
    """Render one non-term document section."""
    lines = []
    if doc["includeHeading"]:
        lines.extend([f"## {doc['title']}", ""])
    body = doc.get("body", "").strip()
    if body:
        lines.extend([body, ""])
    return lines


def render_index(terms: list[dict[str, Any]]) -> list[str]:
    """Render the generated alphabetical index."""
    lines = [
        "## Index",
        "",
        "Alphabetical lookup. Each row links to the entry; the status column reflects current availability.",
        "",
        "| Entry | Status |",
        "|---|---|",
    ]
    for term in sorted(terms, key=lambda value: (value["indexOrder"], value["titleSort"])):
        lines.append(f"| {term_link(term)} | {term['statusText']} |")
    lines.append("")
    return lines


def render_browse(
    memberships: list[dict[str, Any]],
) -> list[str]:
    """Render the generated category browser."""
    grouped: dict[str, dict[str, Any]] = {}
    for membership in memberships:
        category = membership["category"]
        bucket = grouped.setdefault(
            category["key"],
            {"category": category, "memberships": []},
        )
        bucket["memberships"].append(membership)

    lines = [
        "## Browse by category",
        "",
        "For readers exploring rather than looking up a specific term:",
        "",
    ]
    for bucket in sorted(grouped.values(), key=lambda value: value["category"]["order"]):
        category = bucket["category"]
        links = [
            term_link(membership["term"])
            for membership in sorted(bucket["memberships"], key=lambda value: value["order"])
        ]
        # Separator lifted into a name: a backslash escape inside an f-string
        # ``{...}`` expression is a syntax error before Python 3.12 (floor is 3.10).
        joined = " \u00b7 ".join(links)
        lines.append(f"- **{category['label']}:** {joined}.")
    lines.extend(["", "---", ""])
    return lines


def render_term(term: dict[str, Any]) -> list[str]:
    """Render one glossary term entry."""
    lines = [
        f"## {term['title']}",
        "",
        f"**Status:** {term['statusText']}.",
        "",
    ]
    body = term.get("body", "").strip()
    if body:
        lines.extend([body, ""])

    return lines


def render_terms(terms: list[dict[str, Any]]) -> list[str]:
    """Render all glossary term entries."""
    lines = []
    for term in sorted(terms, key=lambda value: (value["entryOrder"], value["titleSort"])):
        lines.extend(render_term(term))
    return lines


def render_markdown(glossary_data: dict[str, Any]) -> str:
    """Render the complete glossary markdown export."""
    docs = {doc["key"]: doc for doc in glossary_data["documents"]}
    terms = glossary_data["terms"]
    memberships = glossary_data["categoryMemberships"]

    rendered = []
    preamble = docs.get("preamble")
    if preamble is not None:
        rendered.extend(render_document(preamble))

    for key in ("status-legend", "public-exports"):
        doc = docs.get(key)
        if doc is not None:
            rendered.extend(render_document(doc))

    rendered.extend(render_index(terms))
    rendered.extend(render_browse(memberships))
    rendered.extend(render_terms(terms))

    for doc in sorted(docs.values(), key=lambda value: value["order"]):
        if doc["key"] in {
            "preamble",
            "status-legend",
            "public-exports",
            "link-definitions",
        }:
            continue
        rendered.extend(render_document(doc))

    link_definitions = docs.get("link-definitions")
    if link_definitions is not None and link_definitions.get("body"):
        rendered.append(link_definitions["body"].strip())

    return finalize_markdown(rendered)


def main() -> int:
    """Build the glossary markdown export (or check its freshness)."""
    args = parse_args()
    configure_django()
    glossary_data = fetch_glossary_data()
    markdown = render_markdown(glossary_data)

    if args.check:
        current = args.md.read_text(encoding="utf-8") if args.md.exists() else ""
        if current != markdown:
            print(
                f"{args.md} is not up to date; run scripts/build_glossary_md.py.",
                file=sys.stderr,
            )
            return 1
        print(f"{args.md} is up to date.")
        return 0

    args.md.write_text(markdown, encoding="utf-8")

    mentioned_specs = {mention["specPath"] for mention in glossary_data["specMentions"]}
    print(
        "Wrote "
        f"{len(glossary_data['terms'])} terms, "
        f"{len(glossary_data['categoryMemberships'])} category memberships, "
        f"{len(glossary_data['specMentions'])} spec mentions across "
        f"{len(mentioned_specs)} specs to {args.md}",
    )
    return 0


if __name__ == "__main__":
    cli_exit(main)
