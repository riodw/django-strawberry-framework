"""Build ``KANBAN.html`` from the shared kanban dashboard payload.

The Vue shell is hand-edited; only the marked data block regenerates. The payload
(``_kanban_lib.fetch_dashboard_data``) is deep-sorted before embedding so the block
diffs cleanly build over build; ``KANBAN.md`` (built separately) is the agent-facing
rendering of the same kanban DB.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

try:
    from _kanban_lib import (
        REPO_ROOT,
        build_dashboard_snapshot,
        check_freshness,
        cli_exit,
        configure_django,
        fetch_dashboard_data,
        placeholder_defects,
        render_parser,
    )
except ModuleNotFoundError:  # imported as ``scripts.build_kanban_html`` (repo root on path)
    from scripts._kanban_lib import (
        REPO_ROOT,
        build_dashboard_snapshot,
        check_freshness,
        cli_exit,
        configure_django,
        fetch_dashboard_data,
        placeholder_defects,
        render_parser,
    )

DEFAULT_HTML_PATH = REPO_ROOT / "KANBAN.html"
DATA_BLOCK_RE = re.compile(
    r"(?s)<!-- KANBAN_DATA_START -->.*?<!-- KANBAN_DATA_END -->",
)


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


def embedded_data_block(html: str) -> str:
    """Return the data block ``html`` currently carries (``""`` when it has none)."""
    match = DATA_BLOCK_RE.search(html)
    return match.group(0) if match else ""


def embed_dashboard_data(html_path: Path, data_block: str) -> None:
    """Replace the marked data block in ``html_path``."""
    html = html_path.read_text(encoding="utf-8")
    updated, replacements = DATA_BLOCK_RE.subn(lambda _match: data_block, html)
    if replacements != 1:
        raise RuntimeError(f"Expected exactly one kanban data block in {html_path}.")
    html_path.write_text(updated, encoding="utf-8")


def assert_placeholders_resolve(snapshot: dict[str, Any]) -> None:
    r"""Fail the build when the embedded prose carries a placeholder nothing resolves.

    Unlike ``KANBAN.md``, this export ships placeholders on purpose -- the Vue shell
    resolves them client-side from the same FK-backed references, so the tokens must
    survive into the data block. That is why this check grades resolvability rather
    than absence. Without it the two exports disagree: the markdown build refuses to
    write prose whose placeholder resolves nowhere, while this build embeds it happily
    and the shell's ``{{card_ref:(\d+)}}`` pattern -- which matches neither a
    non-numeric index nor an out-of-range one -- returns the token, printing a raw
    ``{{card_ref:N}}`` to the reader. A silently divergent pair of boards is the
    failure this exists to prevent.
    """
    defects = placeholder_defects(snapshot["cards"], snapshot["boardDocs"])
    if defects:
        detail = "".join(f"\n  - {defect}" for defect in defects)
        raise RuntimeError(
            f"{len(defects)} placeholder(s) resolve nowhere and would render "
            f"literally in KANBAN.html:{detail}",
        )


def main() -> int:
    """Build the HTML dashboard (or check its freshness)."""
    args = render_parser(
        "Embed kanban GraphQL JSON into the single-file dashboard.",
        flag="--html",
        default=DEFAULT_HTML_PATH,
    ).parse_args()
    configure_django()
    snapshot = build_dashboard_snapshot(fetch_dashboard_data())
    assert_placeholders_resolve(snapshot)
    data_block = render_data_block(snapshot)

    if args.check:
        return check_freshness(
            args.html,
            data_block,
            script="scripts/build_kanban_html.py",
            current=embedded_data_block,
        )

    embed_dashboard_data(args.html, data_block)
    print(
        "Wrote "
        f"{len(snapshot['cards'])} cards, "
        f"{len(snapshot['boardDocs'])} board docs, and "
        f"{len(snapshot['lookups'])} lookup arrays to {args.html}",
    )
    return 0


if __name__ == "__main__":
    cli_exit(main)
