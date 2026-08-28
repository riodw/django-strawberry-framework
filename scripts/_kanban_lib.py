"""Shared plumbing for the kanban / glossary / tree render + import scripts.

Holds the helpers that were previously duplicated across (or imported through)
``build_kanban_html.py``: Django bootstrap, the in-process GraphQL fetch, git
invocation, and version parsing. The individual ``build_*`` scripts import from
here (some via a back-compat re-export in ``build_kanban_html``) so there is one
canonical copy of each.

Concurrency: :func:`configure_django` installs a SQLite ``busy_timeout`` on every
connection so a render running while a parallel session writes ``db.sqlite3`` waits
for the lock instead of failing immediately with ``database is locked``.

Alternate database: set ``DJANGO_STRAWBERRY_KANBAN_DB`` to point the default SQLite
alias at a migrated copy of ``db.sqlite3`` (see ``config.settings``) so the renderers
can run against a copy without touching the live board file.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from collections.abc import Callable, Container, Sequence
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
FAKESHOP_ROOT = REPO_ROOT / "examples" / "fakeshop"

# Wait this long for a competing writer to release a SQLite lock before erroring.
# Parallel claude sessions write ``db.sqlite3``; a render must queue behind them,
# not crash with ``database is locked``.
SQLITE_BUSY_TIMEOUT_MS = 5000

# Stored board prose keeps a placeholder rather than a literal, because a card id is
# a recomputed ordinal that drifts on every renumber. The two exports resolve the
# same placeholders by different routes, so both must agree on what is resolvable.
CARD_REF_RE = re.compile(r"\{\{card_ref:(\d+)\}\}")
PLACEHOLDER_RE = re.compile(r"\{\{[^{}]*\}\}")

# The tokens the board-wide computed set fills. Only ``BoardDoc`` bodies carry them:
# neither export resolves a computed token inside card text, so one there is a defect.
COMPUTED_TOKEN_NAMES = frozenset(
    {
        "active_version",
        "last_refreshed",
        "in_progress_intro",
        "relative_size_scale",
    },
)


def unresolvable_placeholders(
    text: str,
    *,
    reference_orders: Container[int],
    computed_tokens: Container[str] = frozenset(),
) -> list[str]:
    r"""Return every ``{{...}}`` in ``text`` that no renderer can resolve, in order.

    ``KANBAN.md`` substitutes placeholders at build time and must end with none
    left; ``KANBAN.html`` embeds them verbatim for the Vue shell to resolve
    client-side against the same FK-backed references. That asymmetry is by
    design, and it is why the HTML build cannot simply assert the absence of
    placeholders the way the markdown build does - it ships 371 of them on
    purpose. What neither export can survive is a placeholder that resolves
    NOWHERE: the shell matches ``{{card_ref:(\d+)}}``, so a non-numeric index
    never matches and an out-of-range one resolves to nothing, and both paths
    return the token itself - printing ``{{card_ref:N}}`` to the reader instead
    of failing. Checking both exports through this one function is what keeps
    the markdown build from rejecting prose the HTML build silently publishes.
    """
    unresolvable: list[str] = []
    for token in PLACEHOLDER_RE.findall(text or ""):
        card_ref = CARD_REF_RE.fullmatch(token)
        if card_ref is not None:
            if int(card_ref.group(1)) not in reference_orders:
                unresolvable.append(token)
        elif token[2:-2] not in computed_tokens:
            unresolvable.append(token)
    return unresolvable


def placeholder_defects(
    cards: Sequence[dict[str, Any]],
    board_docs: Sequence[dict[str, Any]],
) -> list[str]:
    """Return one ``site: token`` message per unresolvable placeholder in the board.

    Names the row it found, because the token alone does not locate it: the same
    ``{{card_ref:N}}`` can be stored on any of ~1,300 card items.
    """
    defects: list[str] = []
    for card in cards:
        orders = {reference["order"] for reference in card.get("outgoingReferences", [])}
        sites: list[tuple[str, str]] = [
            (f"card {card['cardId']} planningNote", card.get("planningNote", "")),
        ]
        sites += [
            (
                f"card {card['cardId']} item order={item['order']} section={item['section']['key']}",
                item["text"],
            )
            for item in card.get("items", [])
        ]
        sites += [
            (
                f"card {card['cardId']} reference order={reference['order']} rawText",
                reference.get("rawText", ""),
            )
            for reference in card.get("outgoingReferences", [])
        ]
        for label, text in sites:
            defects += [
                f"{label}: {token}"
                for token in unresolvable_placeholders(text, reference_orders=orders)
            ]

    for doc in board_docs:
        orders = {reference["order"] for reference in doc.get("cardReferences", [])}
        defects += [
            f"board doc {doc['key']!r} body: {token}"
            for token in unresolvable_placeholders(
                doc.get("body", ""),
                reference_orders=orders,
                computed_tokens=COMPUTED_TOKEN_NAMES,
            )
        ]
    return defects


class GitCommandError(RuntimeError):
    """A ``git`` invocation failed (caller-correctable)."""


def _install_sqlite_busy_timeout() -> None:
    """Apply ``PRAGMA busy_timeout`` to current and future SQLite connections."""
    from django.db import connections
    from django.db.backends.signals import connection_created

    def _apply(connection: Any) -> None:
        if connection.vendor != "sqlite":
            return
        with connection.cursor() as cursor:
            cursor.execute(f"PRAGMA busy_timeout = {SQLITE_BUSY_TIMEOUT_MS};")

    def _on_connect(connection: Any, **_kwargs: Any) -> None:
        _apply(connection)

    connection_created.connect(_on_connect, dispatch_uid="kanban_scripts_busy_timeout")
    for connection in connections.all():
        if connection.connection is not None:
            _apply(connection)


def configure_django() -> None:
    """Load the fakeshop Django settings for the in-process GraphQL request.

    Mutates process state without undoing it: prepends ``FAKESHOP_ROOT`` to
    ``sys.path`` and sets ``DJANGO_SETTINGS_MODULE``. Fine for these top-level
    build scripts (one process, exits after writing its artifact); if this module
    is ever imported into a longer-lived process, isolate or restore these instead.

    Also installs a SQLite ``busy_timeout`` so a render tolerates a concurrent
    writer holding the DB lock (see :data:`SQLITE_BUSY_TIMEOUT_MS`).
    """
    sys.path.insert(0, str(FAKESHOP_ROOT))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

    import django

    django.setup()
    _install_sqlite_busy_timeout()


def run_git(args: Sequence[str], *, error_cls: type[Exception] = GitCommandError) -> str:
    """Run ``git --no-pager <args>`` and return stdout.

    ``error_cls`` lets a caller surface failures as its own caller-correctable
    exception type (so a script's ``__main__`` exit-code handling is unchanged).
    """
    try:
        result = subprocess.run(
            ["git", "--no-pager", *args],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as error:
        message = error.stderr.strip() or f"git {' '.join(args)} failed."
        raise error_cls(message) from error
    return result.stdout


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


def version_tuple(text: str | None) -> tuple[int, ...]:
    """Parse a ``"X.Y.Z"`` version string to a comparable int tuple (digits only).

    Tolerant of empty / suffixed segments (``"1.0.0 (stable)"`` -> ``(1, 0, 0)``);
    a missing or empty version yields ``(0,)`` so an unbounded floor sorts low.
    Shared by every kanban export so they order versions identically - a suffixed
    version string must not render on one side and crash the other.
    """
    parts: list[int] = []
    for segment in (text or "").split("."):
        digits = "".join(ch for ch in segment if ch in "0123456789")
        if not digits:
            break
        try:
            parts.append(int(digits))
        except ValueError:
            break
    return tuple(parts) or (0,)


def cli_exit(main_fn: Callable[[], int]) -> None:
    """Run a script ``main`` and translate errors into a uniform exit code.

    Exit codes across the render scripts: ``0`` success / fresh, ``1`` stale
    (``--check``), ``2`` on a caller-correctable rendering or fetch error. Raises
    ``SystemExit`` (never returns).
    """
    try:
        raise SystemExit(main_fn())
    except (RuntimeError, TypeError, OSError) as error:
        print(error, file=sys.stderr)
        raise SystemExit(2) from error
