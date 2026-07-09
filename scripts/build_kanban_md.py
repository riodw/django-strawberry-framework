"""Build ``KANBAN.md`` from the shared kanban dashboard payload."""

from __future__ import annotations

import argparse
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

from build_kanban_html import configure_django, fetch_dashboard_data

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MD_PATH = REPO_ROOT / "KANBAN.md"
KANBAN_HTML_PATH = "KANBAN.html"
GITHUB_BLOB_URL = "https://github.com/riodw/django-strawberry-framework/blob/main"
CARD_REF_RE = re.compile(r"\{\{card_ref:(\d+)\}\}")
LINK_DEFINITIONS_KEY = "link-definitions"
COLUMN_DOC_KEYS = {
    "in-progress",
    "to-do-alpha-010",
    "to-do-beta-100",
    "done",
}


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Render KANBAN.md from the same GraphQL payload used by KANBAN.html.",
    )
    parser.add_argument(
        "--md",
        type=Path,
        default=DEFAULT_MD_PATH,
        help="Markdown file to write. Defaults to the repository-root KANBAN.md.",
    )
    return parser.parse_args()


def finalize_markdown(lines: list[str]) -> str:
    """Normalize rendered markdown lines into one trailing-newline document."""
    text = "\n".join(line.rstrip() for line in lines).strip()
    return f"{text}\n"


def card_key(card: dict[str, Any]) -> str:
    """Return the kanban card id for ``card``.

    Reads the ``cardId`` GraphQL field (sourced from ``Card.card_id`` in the
    model layer) instead of recomputing the ``<STATUS>[-<MILESTONE>]-NNN-X.Y.Z``
    format here - single source of truth shared with ``Card.__str__`` and the
    KANBAN.html renderer.
    """
    return card["cardId"]


def card_url(card: dict[str, Any]) -> str:
    """Return the relative dashboard URL for ``card``."""
    return f"{KANBAN_HTML_PATH}#{card['slug']}"


def spec_path_from_url(url: str) -> str:
    """Return the repo path from a GitHub ``blob/main`` URL."""
    prefix = f"{GITHUB_BLOB_URL}/"
    if not url.startswith(prefix):
        return ""
    return url.removeprefix(prefix)


def spec_paths_for_card(card: dict[str, Any]) -> list[str]:
    """Return the DB-backed spec path for ``card``, when it has one."""
    spec = card.get("spec")
    if not spec:
        return []
    db_path = spec_path_from_url(spec.get("url", ""))
    return [db_path] if db_path else []


def spec_link(path: str) -> str:
    """Return a Markdown link to a repository spec path."""
    return f"[{Path(path).name}]({path})"


def glossary_term_link(term: dict[str, Any]) -> str:
    """Return a Markdown link to a glossary term anchor."""
    return f"[{term['title']}](docs/GLOSSARY.md#{term['anchor']})"


def tracked_path_link(tracked_path: dict[str, Any], *, planned: bool) -> str:
    """Return a Markdown link or planned/historical marker for a tracked path.

    Non-current paths read as ``historical`` on DONE cards (the file once
    existed) and ``planned`` on WIP/TODO cards (the file does not exist yet).
    """
    path = tracked_path["path"]
    if tracked_path.get("isCurrent", True):
        return f"[`{path}`]({path})"
    marker = "planned" if planned else "historical"
    return f"`{path}` ({marker})"


def active_version(cards: list[dict[str, Any]]) -> str:
    """Return the version currently in progress.

    Derived from ``status`` alone: the single ``wip`` card names the active
    version, so the ``## In progress`` column no longer needs a per-card flag.
    Falls back to the latest shipped version when the board has no ``wip`` card.
    """
    wip_versions = sorted(
        {
            card["targetVersion"]["number"]
            for card in cards
            if card["status"]["key"] == "wip" and card.get("targetVersion")
        },
        key=_version_key,
    )
    if wip_versions:
        return wip_versions[0]
    done_versions = sorted(
        {
            card["targetVersion"]["number"]
            for card in cards
            if card["status"]["key"] == "done" and card.get("targetVersion")
        },
        key=_version_key,
    )
    return done_versions[-1] if done_versions else ""


def card_column_key(card: dict[str, Any], active: str) -> str:
    """Return the board column key that owns ``card``.

    ``active`` is the board's in-progress version (see :func:`active_version`):
    a non-Done card sharing it belongs to the ``## In progress`` column.
    """
    status = card["status"]["key"]
    milestone = card["milestone"]["key"] if card.get("milestone") else ""
    version = card["targetVersion"]["number"] if card.get("targetVersion") else ""
    if status == "done":
        return "done"
    if status == "backlog":
        return "backlog"
    if active and version == active:
        return "in-progress"
    if status == "todo" and milestone == "alpha":
        return "to-do-alpha-010"
    if status == "todo" and milestone in {"beta", "stable"}:
        return "to-do-beta-100"
    return "backlog"


def sorted_column_cards(column_key: str, cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return cards in the display order for one board column."""
    return sorted(
        cards,
        key=lambda value: value["number"],
        reverse=column_key == "done",
    )


def size_label(card: dict[str, Any]) -> str:
    """Render a card's relative size."""
    relative_size = card.get("relativeSize")
    if not relative_size:
        return ""
    return relative_size["label"]


def resolve_card_refs(text: str, doc: dict[str, Any]) -> str:
    """Replace ``{{card_ref:N}}`` placeholders using FK-backed doc references."""
    references = {reference["order"]: reference for reference in doc.get("cardReferences", [])}

    def replace(match: re.Match[str]) -> str:
        reference = references.get(int(match.group(1)))
        if reference is None:
            return match.group(0)
        return card_key(reference["card"])

    return CARD_REF_RE.sub(replace, text)


def resolve_card_refs_for_card(text: str, card: dict[str, Any]) -> str:
    """Replace ``{{card_ref:N}}`` placeholders using a card's FK-backed references.

    The card-side mirror of :func:`resolve_card_refs` (which serves ``BoardDoc``
    bodies): ``N`` indexes the card's ``outgoingReferences`` by ``order`` and
    resolves to the *current* id of the referenced target card. The card id is a
    deliberately unstable, recomputed ordinal, so prose stores the stable
    placeholder and the id is resolved at render time from the reference FK --
    never a literal id snapshot that would drift on the next renumber.
    """
    references = {
        reference["order"]: reference for reference in card.get("outgoingReferences", [])
    }

    def replace(match: re.Match[str]) -> str:
        reference = references.get(int(match.group(1)))
        if reference is None:
            return match.group(0)
        return card_key(reference["targetCard"])

    return CARD_REF_RE.sub(replace, text)


def bullet_lines(prefix: str, text: str) -> list[str]:
    """Render possibly multi-line text as one markdown bullet."""
    lines = (text or "").strip().splitlines()
    if not lines:
        return []
    rendered = [f"{prefix} {lines[0]}"]
    rendered.extend(f"  {line}" if line else "" for line in lines[1:])
    return rendered


def _version_key(version: str) -> tuple[int, ...]:
    """Sort key for a dotted ``X.Y.Z`` version (so ``0.0.10`` > ``0.0.9``)."""
    return tuple(int(part) for part in version.split("."))


def render_relative_size_scale(dashboard_data: dict[str, Any]) -> str:
    """Render the ``## Relative size`` bullet scale from the RelativeSize table.

    The five rows (and their effort blurbs) live in the lookup table, so the
    scale is derived rather than frozen in the board prose. Sorted by ``rank``.
    """
    sizes = sorted(
        dashboard_data["lookups"].get("relativeSizes", []),
        key=lambda size: size.get("rank", 0),
    )
    return "\n".join(
        f"- **{size['label']}** - {size['description']}"
        for size in sizes
        if size.get("description")
    )


def compute_tokens(dashboard_data: dict[str, Any]) -> dict[str, str]:
    """Derive the board-wide computed placeholders from the card/doc data.

    These are facts the DB already knows, so the prose stores a ``{{token}}``
    placeholder instead of a frozen literal - the renderer fills it from the
    live data and it can never go stale. The KANBAN.html Vue app resolves the
    same tokens client-side, so both exports stay consistent.
    """
    cards = dashboard_data["cards"]

    active = active_version(cards)
    has_in_progress = any(card_column_key(card, active) == "in-progress" for card in cards)
    dates = [card.get("updatedDate") for card in cards]
    dates += [doc.get("updatedDate") for doc in dashboard_data["boardDocs"]]
    dates = [date for date in dates if date]
    last_refreshed = max(dates)[:10] if dates else ""

    return {
        "active_version": active,
        "last_refreshed": last_refreshed,
        "in_progress_intro": "" if has_in_progress else "No cards in progress.",
        "relative_size_scale": render_relative_size_scale(dashboard_data),
    }


def resolve_computed_tokens(text: str, computed: dict[str, str]) -> str:
    """Replace every ``{{token}}`` from :func:`compute_tokens` in ``text``."""
    for token, value in computed.items():
        text = text.replace(f"{{{{{token}}}}}", value)
    return text


def render_doc(doc: dict[str, Any], computed: dict[str, str]) -> list[str]:
    """Render one ordered board-prose document."""
    if doc["key"] == LINK_DEFINITIONS_KEY:
        return [resolve_computed_tokens(resolve_card_refs(doc["body"], doc), computed).strip()]

    lines = []
    if doc.get("title"):
        heading = "#" if doc["kind"]["key"] == "preamble" else "##"
        lines.extend([f"{heading} {doc['title']}", ""])

    body = resolve_computed_tokens(resolve_card_refs(doc.get("body", ""), doc), computed).strip()
    if body:
        lines.extend([body, ""])
    return lines


def render_spec_map(dashboard_data: dict[str, Any]) -> list[str]:
    """Render the WIP/DONE card-to-spec map."""
    cards = [card for card in dashboard_data["cards"] if card["status"]["key"] in {"wip", "done"}]
    cards = sorted(
        cards,
        key=lambda card: (
            0 if card["status"]["key"] == "wip" else 1,
            -int(card["number"]) if card["status"]["key"] == "done" else int(card["number"]),
        ),
    )
    lines = [
        "## WIP / DONE spec map",
        "",
        "| Card | Spec file |",
        "| --- | --- |",
    ]
    for card in cards:
        specs = spec_paths_for_card(card)
        spec_text = (
            "<br>".join(spec_link(path) for path in specs) if specs else "No dedicated spec"
        )
        lines.append(f"| `{card_key(card)}` - {card['title']} | {spec_text} |")
    lines.append("")
    return lines


def render_glossary_terms(card: dict[str, Any]) -> list[str]:
    """Render the card-to-glossary term table."""
    glossary_links = sorted(
        card.get("glossaryLinks", []),
        key=lambda link: link["order"],
    )
    if not glossary_links:
        return []

    lines = [
        "#### Glossary terms",
        "",
        "| Term | Status |",
        "| --- | --- |",
    ]
    for glossary_link in glossary_links:
        term = glossary_link["term"]
        lines.append(f"| {glossary_term_link(term)} | {term['statusText']} |")
    lines.append("")
    return lines


def render_tracked_paths(card: dict[str, Any]) -> list[str]:
    """Render the tracked paths linked to one card.

    DONE cards list the files they actually changed; WIP/TODO cards list the
    paths they are predicted to touch.
    """
    changed_files = sorted(
        card.get("changedFiles", []),
        key=lambda tracked_path: tracked_path["path"],
    )
    if not changed_files:
        return []

    planned = card["status"]["key"] != "done"
    heading = "#### Predicted files" if planned else "#### Package files"
    lines = [heading, ""]
    lines.extend(
        f"- {tracked_path_link(tracked_path, planned=planned)}" for tracked_path in changed_files
    )
    lines.append("")
    return lines


def render_card(card: dict[str, Any]) -> list[str]:
    """Render a kanban card with its lookup metadata and child rows."""
    slug = card["slug"]
    lines = [
        f'<a id="{slug}"></a>',
        f"### [{card_key(card)} - {card['title']}]({card_url(card)})",
        "",
    ]

    if card.get("priority"):
        lines.append(f"- Priority: {card['priority']['label']}")
    parity_claims = sorted(
        card.get("parityClaims", []),
        key=lambda claim: claim["upstream"]["order"],
    )
    if parity_claims:
        parity = ", ".join(
            f"{claim['upstream']['emoji']} {claim['upstream']['label']} ({claim['level']['label']})".strip()
            for claim in parity_claims
        )
        lines.append(f"- Parity: {parity}")
    if card.get("status"):
        lines.append(f"- Status: {card['status']['label']}")
    size = size_label(card)
    if size:
        lines.append(f"- Relative size: {size}")
    labels = sorted(card.get("labels", []), key=lambda label: label["key"])
    if labels:
        lines.append("- Labels: " + ", ".join(f"`{label['key']}`" for label in labels))
    specs = spec_paths_for_card(card)
    if specs:
        label = "Spec" if len(specs) == 1 else "Specs"
        lines.append(f"- {label}: " + ", ".join(spec_link(path) for path in specs))
    lines.append("")

    lines.extend(render_glossary_terms(card))
    lines.extend(render_tracked_paths(card))

    planning_note = card.get("planningNote") or ""
    if planning_note:
        lines.extend(
            [
                "#### Planning note",
                "",
                resolve_card_refs_for_card(planning_note.strip(), card),
                "",
            ],
        )

    dependencies = sorted(
        card.get("dependencies", []),
        key=lambda dependency: dependency["number"],
    )
    if dependencies:
        lines.extend(["#### Dependencies", ""])
        for dependency in dependencies:
            lines.append(f"- `{card_key(dependency)}` - {dependency['title']}")
        lines.append("")

    item_groups = defaultdict(lambda: {"section": None, "items": []})
    for item in card.get("items", []):
        section = item["section"]
        group = item_groups[section["key"]]
        group["section"] = section
        group["items"].append(item)
    for group in sorted(item_groups.values(), key=lambda value: value["section"]["order"]):
        section = group["section"]
        lines.extend([f"#### {section['label']}", ""])
        for item in sorted(group["items"], key=lambda value: value["order"]):
            if section["key"] == "definition_of_done":
                marker = "[x]" if item["isComplete"] else "[ ]"
                lines.extend(
                    bullet_lines(
                        f"- {marker}",
                        resolve_card_refs_for_card(item["text"], card),
                    ),
                )
            else:
                lines.extend(
                    bullet_lines(
                        "-",
                        resolve_card_refs_for_card(item["text"], card),
                    ),
                )
        lines.append("")

    references = sorted(
        card.get("outgoingReferences", []),
        key=lambda reference: reference["order"],
    )
    if references:
        lines.extend(["#### Card references", ""])
        for reference in references:
            target_card = reference["targetCard"]
            target = f"`{card_key(target_card)}` - {target_card['title']}"
            kind = reference["kind"]["label"]
            text = resolve_card_refs_for_card(
                reference.get("rawText", "").strip(),
                card,
            )
            if text:
                lines.extend(bullet_lines(f"- {kind}: {text} ->", target))
            else:
                lines.append(f"- {kind}: {target}")
        lines.append("")

    return lines


def render_markdown(dashboard_data: dict[str, Any]) -> str:
    """Render the complete kanban board markdown."""
    docs = sorted(dashboard_data["boardDocs"], key=lambda doc: doc["order"])
    link_definitions = next((doc for doc in docs if doc["key"] == LINK_DEFINITIONS_KEY), None)
    docs = [doc for doc in docs if doc["key"] != LINK_DEFINITIONS_KEY]

    cards_by_column = defaultdict(list)
    active = active_version(dashboard_data["cards"])
    for card in dashboard_data["cards"]:
        cards_by_column[card_column_key(card, active)].append(card)

    computed = compute_tokens(dashboard_data)
    rendered = []
    rendered_card_ids = set()
    for doc in docs:
        if doc["kind"]["key"] == "column" and doc["key"] not in COLUMN_DOC_KEYS:
            continue
        rendered.extend(render_doc(doc, computed))
        if doc["key"] == "board-columns":
            rendered.extend(render_spec_map(dashboard_data))
        if doc["key"] in COLUMN_DOC_KEYS:
            for card in sorted_column_cards(doc["key"], cards_by_column.get(doc["key"], [])):
                rendered.extend(render_card(card))
                rendered_card_ids.add(card["id"])

    if link_definitions is not None:
        rendered.extend(render_doc(link_definitions, computed))

    return finalize_markdown(rendered)


def main() -> None:
    """Build the markdown board."""
    args = parse_args()
    configure_django()
    dashboard_data = fetch_dashboard_data()
    markdown = render_markdown(dashboard_data)
    args.md.write_text(markdown, encoding="utf-8")
    active = active_version(dashboard_data["cards"])
    exported_card_count = sum(
        1 for card in dashboard_data["cards"] if card_column_key(card, active) != "backlog"
    )
    excluded_card_count = len(dashboard_data["cards"]) - exported_card_count
    print(
        "Wrote "
        f"{exported_card_count} cards "
        f"(excluded {excluded_card_count} backlog cards) and "
        f"{len(dashboard_data['boardDocs'])} board docs to {args.md}",
    )


if __name__ == "__main__":
    main()
