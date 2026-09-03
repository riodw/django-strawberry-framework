"""Build ``KANBAN.md`` from the shared kanban dashboard payload.

``KANBAN.md`` is the agent-facing export; ``KANBAN.html`` is the human-facing one.
Both render the same deep-sorted payload (``_kanban_lib``), but the markdown drops
surfaces that only add reading cost for an agent: the ``snapshot`` and
``board-columns`` reference docs, the WIP/DONE spec map (every card already carries
its ``Spec:`` line), and each card's ``note`` section (process provenance), plus
``verified_upstream`` once a card is Done (the shipped spec holds that evidence).
``MD_OMITTED_DOC_KEYS``, ``MD_OMITTED_SECTION_KEYS`` and
``MD_OMITTED_DONE_SECTION_KEYS`` name the omissions; the HTML export keeps them all.
Glossary links are derived, not stored: every ``GlossaryTerm`` title is searched for
in each card's own text and the first mention per card becomes the link, so a term is
linked exactly where the prose names it. In place of the spec map the markdown gets a
``## Card index``: one row per rendered card, in board order, self-linking to the
card's anchor.

The export is one pass: :func:`plan_board` routes every card to its column
(``COLUMN_ROUTES``), picks the active version and fills the computed tokens once, and
every renderer, the dropped-card guard and the write summary read that :class:`Board`.
"""

from __future__ import annotations

import re
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from itertools import groupby
from pathlib import Path
from typing import Any, NamedTuple

try:
    from _kanban_lib import (
        CARD_REF_RE,
        PLACEHOLDER_RE,
        REPO_ROOT,
        build_dashboard_snapshot,
        check_freshness,
        cli_exit,
        configure_django,
        fetch_dashboard_data,
        finalize_markdown,
        placeholder_defects,
        render_parser,
        version_tuple,
    )
except ModuleNotFoundError:  # imported as ``scripts.build_kanban_md`` (repo root on path)
    from scripts._kanban_lib import (
        CARD_REF_RE,
        PLACEHOLDER_RE,
        REPO_ROOT,
        build_dashboard_snapshot,
        check_freshness,
        cli_exit,
        configure_django,
        fetch_dashboard_data,
        finalize_markdown,
        placeholder_defects,
        render_parser,
        version_tuple,
    )

DEFAULT_MD_PATH = REPO_ROOT / "KANBAN.md"
KANBAN_HTML_PATH = "KANBAN.html"
GLOSSARY_MD_PATH = "docs/GLOSSARY.md"
LINK_DEFINITIONS_KEY = "link-definitions"
PREAMBLE_DOC_KIND_KEY = "preamble"
COLUMN_DOC_KIND_KEY = "column"
DEFINITION_OF_DONE_SECTION_KEY = "definition_of_done"
# Board docs and card sections the markdown export omits (the HTML export keeps them).
MD_OMITTED_DOC_KEYS = frozenset({"snapshot", "board-columns"})
MD_OMITTED_SECTION_KEYS = frozenset({"note"})
MD_OMITTED_DONE_SECTION_KEYS = frozenset({"verified_upstream"})
# A glossary term is inlined only as a standalone token: not glued to an identifier
# character, a dotted/``::``-qualified path, or a path separator on either side.
TERM_BOUNDARY_BEFORE = r"(?<![A-Za-z0-9_.:/\-])"
TERM_BOUNDARY_AFTER = r"(?![A-Za-z0-9_.:/\-])"
# Regions a term match may not straddle: an existing link or a ``#"substring"``
# citation pinpoint (any overlap rejects -- the pinpoint must stay byte-exact), and an
# inline code span (a match must contain the whole span or none of it, so a term is
# linked when it IS the span, never when it sits inside a longer literal).
LINK_SPAN_RE = re.compile(r"\[[^\]]*\]\([^)]*\)|#\"[^\"\n]*\"")
CODE_SPAN_RE = re.compile(r"`[^`\n]+`")


# --------------------------------------------------------------------------------------
# Column routing
# --------------------------------------------------------------------------------------


class Placement(NamedTuple):
    """The facts column routing reads off a card, plus the board's active version."""

    status: str
    milestone: str
    version: str
    active: str


# ``column key -> rule``, first match wins; a card no rule claims is unrouted (backlog,
# never rendered). Any in-flight (``wip``) card belongs in the In progress column
# whether or not it targets the board's headline active version: routing on
# ``version == active`` alone dropped a second concurrent wip version straight through
# to the never-rendered backlog bucket.
COLUMN_ROUTES: tuple[tuple[str, Callable[[Placement], bool]], ...] = (
    ("done", lambda facts: facts.status == "done"),
    ("backlog", lambda facts: facts.status == "backlog"),
    (
        "in-progress",
        lambda facts: (
            facts.status == "wip" or (bool(facts.active) and facts.version == facts.active)
        ),
    ),
    ("to-do-alpha-010", lambda facts: facts.status == "todo" and facts.milestone == "alpha"),
    (
        "to-do-beta-100",
        lambda facts: facts.status == "todo" and facts.milestone in {"beta", "stable"},
    ),
)
UNROUTED_COLUMN_KEY = "backlog"
# Columns listed newest card first.
DESCENDING_COLUMN_KEYS = frozenset({"done"})


def card_key(card: dict[str, Any]) -> str:
    """The card id, read from ``cardId`` (``Card.card_id``) rather than recomputed here."""
    return card["cardId"]


def versions_for(cards: list[dict[str, Any]], status: str) -> list[str]:
    """Distinct target versions of the cards in ``status``, ascending."""
    return sorted(
        {
            card["targetVersion"]["number"]
            for card in cards
            if card["status"]["key"] == status and card.get("targetVersion")
        },
        key=version_tuple,
    )


def active_version(cards: list[dict[str, Any]]) -> str:
    """Return the version currently in progress.

    The lowest ``wip`` target version names the active version, falling back to the
    latest shipped version when the board has no ``wip`` card. It only steers which
    *todo* cards are pulled forward into the In progress column; ``wip`` cards land
    there unconditionally (see ``COLUMN_ROUTES``).
    """
    wip_versions = versions_for(cards, "wip")
    if wip_versions:
        return wip_versions[0]
    done_versions = versions_for(cards, "done")
    return done_versions[-1] if done_versions else ""


def card_column_key(card: dict[str, Any], active: str) -> str:
    """Return the board column key that owns ``card`` (see ``COLUMN_ROUTES``)."""
    facts = Placement(
        status=card["status"]["key"],
        milestone=(card.get("milestone") or {}).get("key", ""),
        version=(card.get("targetVersion") or {}).get("number", ""),
        active=active,
    )
    return next((key for key, rule in COLUMN_ROUTES if rule(facts)), UNROUTED_COLUMN_KEY)


# --------------------------------------------------------------------------------------
# Board plan
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Board:
    """The markdown export's single pass over the payload.

    ``docs`` are the board docs in render order with the link-definitions doc and the
    md-omitted docs removed; ``column_docs`` is its card-bearing subset. Cards are
    routed once into ``cards_by_column`` and the computed tokens are filled once.
    """

    cards: list[dict[str, Any]]
    docs: list[dict[str, Any]]
    column_docs: list[dict[str, Any]]
    link_definitions: dict[str, Any] | None
    cards_by_column: dict[str, list[dict[str, Any]]]
    computed: dict[str, str]
    doc_count: int

    def column_cards(self, column_key: str) -> list[dict[str, Any]]:
        """Cards of one column in display order (payload order is by number)."""
        cards = self.cards_by_column.get(column_key, [])
        return cards[::-1] if column_key in DESCENDING_COLUMN_KEYS else cards

    @property
    def exported_cards(self) -> list[dict[str, Any]]:
        """Every card under a rendered column doc, board order."""
        return [card for doc in self.column_docs for card in self.column_cards(doc["key"])]


def render_relative_size_scale(sizes: list[dict[str, Any]]) -> str:
    """Render the ``## Relative size`` bullet scale from the (order-sorted) lookup rows."""
    return "\n".join(
        f"- **{size['label']}** - {size['description']}"
        for size in sizes
        if size.get("description")
    )


def compute_tokens(
    dashboard_data: dict[str, Any],
    active: str,
    *,
    has_in_progress: bool,
) -> dict[str, str]:
    """Derive the board-wide computed placeholders from the card/doc data.

    These are facts the DB already knows, so the prose stores a ``{{token}}``
    placeholder instead of a frozen literal - the renderer fills it from the live data
    and it can never go stale. The KANBAN.html Vue app resolves the same tokens
    client-side, so both exports stay consistent.
    """
    dates = [card.get("updatedDate") for card in dashboard_data["cards"]]
    dates += [doc.get("updatedDate") for doc in dashboard_data["boardDocs"]]
    dates = [date for date in dates if date]
    return {
        "active_version": active,
        "last_refreshed": max(dates)[:10] if dates else "",
        "in_progress_intro": "" if has_in_progress else "No cards in progress.",
        "relative_size_scale": render_relative_size_scale(
            dashboard_data["lookups"].get("relativeSizes", []),
        ),
    }


def plan_board(dashboard_data: dict[str, Any]) -> Board:
    """Route the cards, select the docs and fill the tokens; expects a deep-sorted payload."""
    cards = dashboard_data["cards"]
    active = active_version(cards)
    cards_by_column: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for card in cards:
        cards_by_column[card_column_key(card, active)].append(card)

    all_docs = dashboard_data["boardDocs"]
    link_def_docs = [doc for doc in all_docs if doc["key"] == LINK_DEFINITIONS_KEY]
    if len(link_def_docs) > 1:
        # The payload is namespace-filtered to ``kanban`` upstream, so exactly one
        # link-definitions doc reaches here today. Guard the invariant rather than let a
        # loosened filter make the pick silently order-dependent.
        raise RuntimeError(
            f"Expected at most one {LINK_DEFINITIONS_KEY!r} board doc, found {len(link_def_docs)}.",
        )
    docs = [
        doc
        for doc in all_docs
        if doc["key"] != LINK_DEFINITIONS_KEY and doc["key"] not in MD_OMITTED_DOC_KEYS
    ]
    return Board(
        cards=cards,
        docs=docs,
        column_docs=[doc for doc in docs if doc["kind"]["key"] == COLUMN_DOC_KIND_KEY],
        link_definitions=link_def_docs[0] if link_def_docs else None,
        cards_by_column=dict(cards_by_column),
        computed=compute_tokens(
            dashboard_data,
            active,
            has_in_progress=bool(cards_by_column.get("in-progress")),
        ),
        doc_count=len(all_docs),
    )


# --------------------------------------------------------------------------------------
# Text helpers
# --------------------------------------------------------------------------------------


def resolve_card_refs(
    text: str,
    references: list[dict[str, Any]],
    *,
    card_field: str,
    site: str,
) -> str:
    """Replace ``{{card_ref:N}}`` placeholders from FK-backed reference rows.

    ``N`` indexes ``references`` by ``order`` and resolves to the *current* id of the
    card under ``card_field`` (``card`` on a ``BoardDoc`` reference, ``targetCard`` on
    a card's outgoing reference). The card id is a deliberately unstable, recomputed
    ordinal, so prose stores the stable placeholder and the id is resolved at render
    time - never a literal id snapshot that would drift on the next renumber. ``site``
    names the owner in the error when a placeholder has no backing row.
    """
    by_order = {reference["order"]: reference for reference in references}

    def replace(match: re.Match[str]) -> str:
        reference = by_order.get(int(match.group(1)))
        if reference is None:
            raise RuntimeError(
                f"{site} references card_ref:{match.group(1)}, "
                "but no reference with that order exists on it.",
            )
        return card_key(reference[card_field])

    return CARD_REF_RE.sub(replace, text)


def resolve_computed_tokens(text: str, computed: dict[str, str]) -> str:
    """Replace every ``{{token}}`` from :func:`compute_tokens` in ``text``."""
    for token, value in computed.items():
        text = text.replace(f"{{{{{token}}}}}", value)
    return text


def bullet_lines(prefix: str, text: str) -> list[str]:
    """Render possibly multi-line text as one markdown bullet."""
    lines = (text or "").strip().splitlines()
    if not lines:
        return []
    rendered = [f"{prefix} {lines[0]}"]
    rendered.extend(f"  {line}" if line else "" for line in lines[1:])
    return rendered


def block(heading: str, body: list[str]) -> list[str]:
    """A heading over ``body`` with the blank lines markdown wants; nothing when empty."""
    return (
        [
            heading,
            "",
            *body,
            "",
        ]
        if body
        else []
    )


def fetch_glossary_terms() -> list[dict[str, Any]]:
    """Load every glossary term the inliner may link (title + anchor), from the DB."""
    from apps.glossary.models import GlossaryTerm

    return [
        {"title": title, "anchor": anchor}
        for title, anchor in GlossaryTerm.objects.values_list("title", "anchor")
    ]


def term_pattern(title: str) -> re.Pattern[str]:
    """Match a glossary title as written (own backticks) or in its bare form."""
    variants = {title, title.replace("`", "")}
    alternation = "|".join(
        re.escape(variant) for variant in sorted(variants, key=len, reverse=True)
    )
    return re.compile(TERM_BOUNDARY_BEFORE + "(?:" + alternation + ")" + TERM_BOUNDARY_AFTER)


Spans = list[tuple[int, int]]


class GlossaryInliner:
    r"""Link the first in-text mention of every glossary term inside one card.

    Derived, not stored: the whole glossary is searched against the card's text, so a
    link lands exactly where the prose names the term and nowhere else. One link per
    term per card, longest title first so ``Meta.fields`` never fires inside
    ``Meta.fields_class``. A match may not overlap an existing link or a ``#"..."``
    citation pinpoint at all, and may not cut a code span in half; it may swallow a
    whole span (a backticked ``Foo`` becomes a linked span) or several (a backticked
    ``BigInt`` followed by ``scalar``).
    """

    def __init__(self, glossary_terms: list[dict[str, Any]]) -> None:
        self._pending = {
            term["anchor"]: (term, term_pattern(term["title"]))
            for term in sorted(glossary_terms, key=lambda term: -len(term["title"]))
        }

    def inline(self, text: str) -> str:
        """Return ``text`` with every still-unlinked term's first mention linked."""
        protected = self._protected(text)
        for anchor in list(self._pending):
            term, pattern = self._pending[anchor]
            match = self._find(pattern, text, protected)
            if match is None:
                continue
            del self._pending[anchor]
            link = f"[{match.group(0)}]({GLOSSARY_MD_PATH}#{term['anchor']})"
            text = text[: match.start()] + link + text[match.end() :]
            protected = self._protected(text)
        return text

    @staticmethod
    def _protected(text: str) -> tuple[Spans, Spans]:
        """The (link-or-pinpoint, code-span) regions of ``text``."""
        links = [(m.start(), m.end()) for m in LINK_SPAN_RE.finditer(text)]
        spans = [(m.start(), m.end()) for m in CODE_SPAN_RE.finditer(text)]
        return links, spans

    @staticmethod
    def _find(
        pattern: re.Pattern[str],
        text: str,
        protected: tuple[Spans, Spans],
    ) -> re.Match[str] | None:
        links, spans = protected
        for match in pattern.finditer(text):
            lo, hi = match.span()
            if any(a < hi and lo < b for a, b in links):
                continue
            if any(a < hi and lo < b and not (lo <= a and b <= hi) for a, b in spans):
                continue
            return match
        return None


# --------------------------------------------------------------------------------------
# Renderers
# --------------------------------------------------------------------------------------


def doc_body(doc: dict[str, Any], computed: dict[str, str]) -> str:
    """A board doc's body with card refs and computed tokens resolved, stripped."""
    text = resolve_card_refs(
        doc.get("body", ""),
        doc.get("cardReferences", []),
        card_field="card",
        site=f"Board doc {doc['key']!r}",
    )
    return resolve_computed_tokens(text, computed).strip()


def render_doc(doc: dict[str, Any], computed: dict[str, str]) -> list[str]:
    """Render one ordered board-prose document."""
    body = doc_body(doc, computed)
    if doc["key"] == LINK_DEFINITIONS_KEY:
        return [body]
    lines: list[str] = []
    if doc.get("title"):
        heading = "#" if doc["kind"]["key"] == PREAMBLE_DOC_KIND_KEY else "##"
        lines += [f"{heading} {doc['title']}", ""]
    if body:
        lines += [body, ""]
    return lines


def render_card_index(board: Board) -> list[str]:
    """Render the ``## Card index``: every rendered card, board order, self-linked.

    Markdown-only. Rows follow the same column order and per-column sort the card
    bodies use, so the index reads top-to-bottom exactly as the board does.
    """
    rows = [
        f"| [`{card_key(card)}`](#{card['slug']}) | {card['title']} | {doc['title']} |"
        for doc in board.column_docs
        for card in board.column_cards(doc["key"])
    ]
    return block(
        "## Card index",
        [
            "Every card on the board, in board order. Links jump to the card.",
            "",
            "| Card | Title | Column |",
            "| --- | --- | --- |",
            *rows,
        ],
    )


def tracked_path_link(link: dict[str, Any]) -> str:
    """Return a Markdown link or planned/historical marker for one tracked-path link.

    A non-current path reads as ``planned`` on a ``predicted`` link (the file does not
    exist yet) and ``historical`` on a ``changed`` one (the file once existed).
    """
    path = link["path"]["path"]
    if link["path"].get("isCurrent", True):
        return f"[`{path}`]({path})"
    marker = "planned" if link["kind"] == "predicted" else "historical"
    return f"`{path}` ({marker})"


def render_tracked_paths(card: dict[str, Any]) -> list[str]:
    """Render the tracked paths linked to one card.

    The link ``kind`` (``changed`` vs ``predicted``), not the card's status, decides
    whether these are package files (actually changed) or predicted files -- the
    through model carries the distinction per link.
    """
    links = card.get("pathLinks", [])
    planned = all(link["kind"] == "predicted" for link in links)
    heading = "#### Predicted files" if planned else "#### Package files"
    return block(heading, [f"- {tracked_path_link(link)}" for link in links])


def parity_text(card: dict[str, Any]) -> str:
    """One ``emoji label (level)`` entry per parity claim, comma-joined."""
    return ", ".join(
        f"{claim['upstream']['emoji']} {claim['upstream']['label']} ({claim['level']['label']})".strip()
        for claim in card.get("parityClaims", [])
    )


def spec_link(card: dict[str, Any]) -> str:
    """A Markdown link to the card's DB-backed spec path (``SpecDoc.path``), or ``""``."""
    path = (card.get("spec") or {}).get("path", "")
    return f"[{Path(path).name}]({path})" if path else ""


def card_meta_lines(card: dict[str, Any]) -> list[str]:
    """The ``- Label: value`` bullets under a card heading, empty values skipped."""
    meta = (
        ("Priority", (card.get("priority") or {}).get("label", "")),
        ("Parity", parity_text(card)),
        ("Status", (card.get("status") or {}).get("label", "")),
        ("Relative size", (card.get("relativeSize") or {}).get("label", "")),
        ("Labels", ", ".join(f"`{label['key']}`" for label in card.get("labels", []))),
        ("Spec", spec_link(card)),
    )
    return [f"- {label}: {value}" for label, value in meta if value]


def card_item_lines(card: dict[str, Any], card_text: Callable[[str], str]) -> list[str]:
    """One ``####`` block per item section, in section order (items arrive pre-sorted)."""
    omitted = set(MD_OMITTED_SECTION_KEYS)
    if card["status"]["key"] == "done":
        omitted |= MD_OMITTED_DONE_SECTION_KEYS
    lines: list[str] = []
    for section_key, grouped in groupby(
        card.get("items", []),
        key=lambda item: item["section"]["key"],
    ):
        items = list(grouped)
        if section_key in omitted:
            continue
        body: list[str] = []
        for item in items:
            prefix = "-"
            if section_key == DEFINITION_OF_DONE_SECTION_KEY:
                prefix = "- [x]" if item["isComplete"] else "- [ ]"
            body += bullet_lines(prefix, card_text(item["text"]))
        lines += block(f"#### {items[0]['section']['label']}", body)
    return lines


def card_reference_lines(card: dict[str, Any], card_text: Callable[[str], str]) -> list[str]:
    """The ``#### Card references`` block: one bullet per outgoing reference."""
    body: list[str] = []
    for reference in card.get("outgoingReferences", []):
        target_card = reference["targetCard"]
        target = f"`{card_key(target_card)}` - {target_card['title']}"
        kind = reference["kind"]["label"]
        text = card_text(reference.get("rawText", "").strip())
        if text:
            body += bullet_lines(f"- {kind}:", f"{text} -> {target}")
        else:
            body.append(f"- {kind}: {target}")
    return block("#### Card references", body)


def render_card(card: dict[str, Any], glossary_terms: list[dict[str, Any]]) -> list[str]:
    """Render a kanban card with its lookup metadata and child rows."""
    glossary = GlossaryInliner(glossary_terms)

    def card_text(text: str) -> str:
        resolved = resolve_card_refs(
            text,
            card.get("outgoingReferences", []),
            card_field="targetCard",
            site=f"Card {card_key(card)!r}",
        )
        return glossary.inline(resolved)

    planning_note = (card.get("planningNote") or "").strip()
    return [
        f'<a id="{card["slug"]}"></a>',
        f"### [{card_key(card)} - {card['title']}]({KANBAN_HTML_PATH}#{card['slug']})",
        "",
        *card_meta_lines(card),
        "",
        *render_tracked_paths(card),
        *block("#### Planning note", [card_text(planning_note)] if planning_note else []),
        *block(
            "#### Dependencies",
            [f"- `{card_key(dep)}` - {dep['title']}" for dep in card.get("dependencies", [])],
        ),
        *card_item_lines(card, card_text),
        *card_reference_lines(card, card_text),
    ]


def render_markdown(board: Board, glossary_terms: list[dict[str, Any]]) -> str:
    """Render the complete kanban board markdown."""
    first_column_doc = board.column_docs[0] if board.column_docs else None
    rendered: list[str] = []
    rendered_card_ids: set[Any] = set()
    for doc in board.docs:
        if doc is first_column_doc:
            rendered += render_card_index(board)
        rendered += render_doc(doc, board.computed)
        if doc in board.column_docs:
            for card in board.column_cards(doc["key"]):
                rendered += render_card(card, glossary_terms)
                rendered_card_ids.add(card["id"])
    if board.link_definitions is not None:
        rendered += render_doc(board.link_definitions, board.computed)

    # Every routed card must have actually been rendered. This catches a card routed to
    # a column key with no ``column`` board doc behind it (a renamed or deleted doc, or
    # the earlier wip-version misroute), which would otherwise drop cards from the
    # export while ``main()`` still reports them as written.
    expected_card_ids = {
        card["id"]
        for column_key, cards in board.cards_by_column.items()
        if column_key != UNROUTED_COLUMN_KEY
        for card in cards
    }
    dropped = expected_card_ids - rendered_card_ids
    if dropped:
        raise RuntimeError(
            f"{len(dropped)} routed card(s) were not rendered (ids {sorted(dropped)}): "
            "the card's column key has no ``column`` board doc in the payload.",
        )

    text = finalize_markdown(rendered)

    # No placeholder may survive resolution: a leftover ``{{card_ref:N}}`` points at a
    # missing reference row, and a leftover ``{{token}}`` is a typo in board-doc prose
    # with no matching computed value. Either would ship a raw brace into the doc. The
    # token alone does not locate the row that stores it, so report the sites too --
    # ``placeholder_defects`` grades the same prose the HTML build embeds verbatim, so a
    # string rejected here can never be one that export publishes unresolved.
    leftovers = sorted(set(PLACEHOLDER_RE.findall(text)))
    if leftovers:
        sites = placeholder_defects(board.cards, board.docs)
        detail = "".join(f"\n  - {site}" for site in sites)
        raise RuntimeError(
            f"KANBAN.md still contains unresolved placeholders: {leftovers}."
            + (
                f" Stored at:{detail}"
                if sites
                else " No stored row carries them; the defect is in a renderer."
            ),
        )
    return text


def main() -> int:
    """Build the markdown board."""
    args = render_parser(
        "Render KANBAN.md from the same GraphQL payload used by KANBAN.html.",
        flag="--md",
        default=DEFAULT_MD_PATH,
    ).parse_args()
    configure_django()
    board = plan_board(build_dashboard_snapshot(fetch_dashboard_data()))
    markdown = render_markdown(board, fetch_glossary_terms())

    if args.check:
        return check_freshness(args.md, markdown, script="scripts/build_kanban_md.py")

    args.md.write_text(markdown, encoding="utf-8")
    exported = len(board.exported_cards)
    print(
        f"Wrote {exported} cards (excluded {len(board.cards) - exported} backlog cards) "
        f"and {board.doc_count} board docs to {args.md}",
    )
    return 0


if __name__ == "__main__":
    cli_exit(main)
