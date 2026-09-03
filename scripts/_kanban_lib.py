"""Shared plumbing for the kanban / glossary / tree render + import scripts.

One canonical copy of everything more than one ``build_*`` / ``check_*`` script needs:
Django bootstrap, the in-process GraphQL fetch, git invocation, version parsing, the
kanban dashboard payload (query, synthetic progress doc, truncation guard, deep sort),
and the render-CLI skeleton (``--<flag>`` + ``--check``). ``build_kanban_html.py`` and
``build_kanban_md.py`` are thin renderers over :func:`fetch_dashboard_data`.

Concurrency: :func:`configure_django` installs a SQLite ``busy_timeout`` on every
connection so a render running while a parallel session writes ``db.sqlite3`` waits
for the lock instead of failing immediately with ``database is locked``.

Alternate database: set ``DJANGO_STRAWBERRY_KANBAN_DB`` to point the default SQLite
alias at a migrated copy of ``db.sqlite3`` (see ``config.settings``) so the renderers
can run against a copy without touching the live board file.
"""

from __future__ import annotations

import argparse
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

# The render's own row bound, published for this process only (see
# :func:`configure_django`). The package default is ``max_list_rows = 100`` and a
# collection over it is truncated SILENTLY - the bound slices the result and
# returns a short page with no error, which is correct for a served API and wrong
# for an export that must reproduce the whole board. Card 52 crossed 100 items and
# one row vanished from both KANBAN.md and KANBAN.html while every freshness check
# still reported "up to date", because a ``--check`` compares the renderer against
# itself. This value only buys headroom; what makes it safe is
# :func:`truncation_defects`, which fails the build if any list is short of the
# database regardless of where the bound sits.
KANBAN_RENDER_MAX_LIST_ROWS = 5000

# The ``BoardDoc`` namespace the board exports carry. The table is shared with the
# glossary build, so a count over the whole table is not this export's ground truth.
KANBAN_DOC_NAMESPACE = "kanban"

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


SortKey = Callable[[dict[str, Any]], Any]

# Every per-card child list ``STATIC_KANBAN_QUERY`` selects, as
# ``payload key -> (ORM accessor, deterministic sort key)``. One table drives both the
# truncation census (:func:`board_row_counts`) and the deep sort
# (:func:`build_dashboard_snapshot`), so a new child list is one row here.
#
# The ORM accessor names the collection to count. The bound is a NESTED-collection
# bound: probed 2026-08-28 at ``max_list_rows = 10``, a card's ``items`` and
# ``glossaryLinks`` came back with 10 while ``allCards`` (71), ``allKanbanBoardDocs``
# (14) and ``allKanbanTrackedPaths`` (347) came back whole. So a top-level field is
# never truncated and every accessor below is - which is why this maps all of them
# rather than only the one that broke. ``items`` was merely the first over the line;
# ``glossaryLinks`` was at 53 of the old 100 and would have been next.
# ``dependencies`` / ``dependents`` are derived ``Card`` properties over the
# reference edges with no collection of their own to count, so they carry no accessor
# and stay outside the census.
CARD_CHILD_LISTS: dict[str, tuple[str | None, SortKey]] = {
    "items": ("items", lambda row: (row["section"]["order"], row["order"], row["id"])),
    "glossaryLinks": ("glossary_links", lambda row: (row["order"], row["id"])),
    "outgoingReferences": ("outgoing_references", lambda row: (row["order"], row["id"])),
    "incomingReferences": ("incoming_references", lambda row: (row["order"], row["id"])),
    "pathLinks": ("path_links", lambda row: row["path"]["path"]),
    "parityClaims": ("parity_claims", lambda row: (row["upstream"]["order"], row["id"])),
    "labels": ("labels", lambda row: row["key"]),
    "changedFiles": ("changed_files", lambda row: row["path"]),
    "dependencies": (None, lambda row: row["number"]),
    "dependents": (None, lambda row: row["number"]),
}

# The truncation census: ``payload key -> ORM accessor`` for every bounded child list.
CARD_NESTED_LISTS: dict[str, str] = {
    key: accessor for key, (accessor, _sort_key) in CARD_CHILD_LISTS.items() if accessor
}


def board_row_counts() -> dict[str, Any]:
    """Read the board's true per-card row counts straight from the ORM.

    Separated from :func:`truncation_defects` so the comparison is a pure function
    with no database of its own to stand up, and so the one part that can be wrong
    in a way tests cannot see - *which* rows are the right ground truth - is stated
    in one place. Counting the whole ``BoardDoc`` table is exactly that mistake and
    was the first draft of this guard: ``allKanbanBoardDocs`` returns the ``kanban``
    namespace only, so a table-wide count reports a permanent 5-row shortfall and
    the check fails on its own wrong ground truth rather than on a defect. The doc
    list is top-level and therefore unbounded, so it is not counted here at all.
    """
    from apps.kanban import models
    from django.db.models import Count

    counts: dict[str, dict[Any, int]] = {}
    for payload_key, accessor in CARD_NESTED_LISTS.items():
        counts[payload_key] = dict(
            models.Card.objects.values_list("number").annotate(total=Count(accessor)),
        )
    return counts


def truncation_defects(cards: Sequence[dict[str, Any]], expected: dict[str, Any]) -> list[str]:
    """Return one message per nested card list that came back short of ``expected``.

    The export is GraphQL-driven on purpose, so it inherits the package's row
    bounds - including the silent one. ``max_list_rows`` slices an over-large
    collection and returns it without an error or a flag, so a truncated board
    renders as a well-formed board that is simply missing rows, and the renderer
    cannot tell the difference from the payload alone. The database the request
    just read is the only available ground truth, so a mismatch against it is
    truncation rather than a race.

    Scoped to the nested lists (:data:`CARD_NESTED_LISTS`) because those are the
    only ones the bound reaches. Checking a top-level list here would read as
    coverage while being unable to fail - the shape that makes a guard worse than
    none, since it certifies the surface it never inspected.
    """
    defects: list[str] = []
    for card in cards:
        number = card.get("number")
        for payload_key in CARD_NESTED_LISTS:
            found = len(card.get(payload_key) or [])
            owed = expected.get(payload_key, {}).get(number, 0)
            if found != owed:
                defects.append(
                    f"card {number} {payload_key}: payload has {found}, database has {owed}",
                )
    return defects


def assert_nothing_truncated(cards: list[dict[str, Any]]) -> None:
    """Fail the build when a row bound silenced part of the board.

    Sits at the shared fetch rather than in either ``main``, because both exports
    read this one payload: a guard on the markdown side alone would let the HTML
    board publish the truncation, which is the same divergence
    ``assert_placeholders_resolve`` exists to prevent. It has to be an assertion
    rather than a wider bound, because a bound is a number someone eventually
    crosses - and crossing it is silent, so the freshness checks keep passing
    against a board that is quietly missing rows.
    """
    defects = truncation_defects(cards, board_row_counts())
    if defects:
        detail = "".join(f"\n  - {defect}" for defect in defects)
        raise RuntimeError(
            f"{len(defects)} board list(s) came back short of the database, so the "
            f"export would silently drop rows:{detail}\n"
            f"Raise KANBAN_RENDER_MAX_LIST_ROWS in scripts/_kanban_lib.py.",
        )


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


def _widen_render_row_bound() -> None:
    """Raise this process's ``max_list_rows`` before the schema is constructed.

    The bound is normalized ONCE, at ``DjangoSchema`` construction, and the
    fakeshop schema is built when the URLconf loads on the first request - so the
    setting has to be in place before then, which is why this runs inside
    ``configure_django`` rather than at the fetch. Scoped to the render process:
    the shipped ``config/settings.py`` keeps the package default, so the example
    app's served behavior and the tests that pin the 100-row cap are untouched.
    """
    from django.conf import settings as django_settings

    configured = dict(getattr(django_settings, "DJANGO_STRAWBERRY_FRAMEWORK", {}) or {})
    resource_policy = dict(configured.get("RESOURCE_POLICY", {}) or {})
    resource_policy["max_list_rows"] = KANBAN_RENDER_MAX_LIST_ROWS
    configured["RESOURCE_POLICY"] = resource_policy
    django_settings.DJANGO_STRAWBERRY_FRAMEWORK = configured


def configure_django() -> None:
    """Load the fakeshop Django settings for the in-process GraphQL request.

    Mutates process state without undoing it: prepends ``FAKESHOP_ROOT`` to
    ``sys.path`` and sets ``DJANGO_SETTINGS_MODULE``. Fine for these top-level
    build scripts (one process, exits after writing its artifact); if this module
    is ever imported into a longer-lived process, isolate or restore these instead.

    Also installs a SQLite ``busy_timeout`` so a render tolerates a concurrent
    writer holding the DB lock (see :data:`SQLITE_BUSY_TIMEOUT_MS`), and widens
    the row bound for this process only (see
    :data:`KANBAN_RENDER_MAX_LIST_ROWS`).
    """
    sys.path.insert(0, str(FAKESHOP_ROOT))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

    import django

    django.setup()
    _widen_render_row_bound()
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


# --------------------------------------------------------------------------------------
# Render CLI skeleton
# --------------------------------------------------------------------------------------


def render_parser(description: str, *, flag: str, default: Path) -> argparse.ArgumentParser:
    """Build the ``--<flag> PATH`` + ``--check`` parser every render script shares.

    Returned rather than parsed so a script can add its own arguments first.
    """
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        flag,
        type=Path,
        default=default,
        help=f"File to write. Defaults to {default.relative_to(REPO_ROOT)}.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit 1 if the file is not already up to date (0 fresh, 2 on error).",
    )
    return parser


def check_freshness(
    path: Path,
    rendered: str,
    *,
    script: str,
    current: Callable[[str], str] | None = None,
) -> int:
    """Report whether ``path`` already carries ``rendered``; ``1`` when stale, ``0`` fresh.

    ``current`` narrows the on-disk text to the part the script owns before comparing
    (the HTML build regenerates only its data block). A missing file is stale.
    """
    existing = path.read_text(encoding="utf-8") if path.is_file() else ""
    if current is not None:
        existing = current(existing)
    if existing != rendered:
        print(f"{path} is not up to date; run {script}.", file=sys.stderr)
        return 1
    print(f"{path} is up to date.")
    return 0


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


def finalize_markdown(lines: list[str]) -> str:
    """Normalize rendered markdown lines into one trailing-newline document.

    Each element may itself be a multi-line block (a rendered card body, a link
    block), so trailing whitespace is stripped per physical line after the join,
    not per element - stripping per element would leave interior lines ragged.
    """
    joined = "\n".join(lines)
    text = "\n".join(line.rstrip() for line in joined.split("\n")).strip()
    return f"{text}\n"


# --------------------------------------------------------------------------------------
# Kanban dashboard payload (shared by KANBAN.md and KANBAN.html)
# --------------------------------------------------------------------------------------

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

# The reference doc the synthetic progress doc is positioned after and clones its
# kind / namespace / timestamps from.
PROGRESS_ANCHOR_DOC_KEY = "snapshot"


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
    anchor: dict[str, Any],
    cards: list[dict[str, Any]],
    milestones: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build the synthetic, export-time ``Progress to <release>`` reference board doc.

    Clones the kind / namespace / timestamps from ``anchor`` (the ``snapshot``
    reference doc) so it groups with the other reference docs in both exports, and
    carries pre-resolved numbers in its body (literal markdown -- no client-side token
    recompute, so the KANBAN.html app renders it with no JS change). The
    road-to-release target and title are derived from the milestone ``versionCeiling``
    values (see :func:`release_version`).
    """
    target_release = release_version(milestones)
    release_label = ".".join(str(part) for part in target_release)
    metrics = compute_progress_metrics(cards, target_release)
    return {
        "id": "synthetic:progress-to-release",
        "uuid": {"id": "synthetic:progress-to-release"},
        "namespace": anchor.get("namespace", KANBAN_DOC_NAMESPACE),
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
    per-builder render change. Loud, not silent: raises when there is no ``snapshot``
    doc to anchor against, so a missing anchor fails the build instead of silently
    dropping the progress board.
    """
    from apps.kanban import models

    data = fetch_graphql_data(
        STATIC_KANBAN_QUERY,
        required_lists=("allCards", "allKanbanBoardDocs", *LOOKUP_FIELDS),
    )
    assert_nothing_truncated(data["allCards"])
    lookups = {
        payload_name: data[graphql_name] for graphql_name, payload_name in LOOKUP_FIELDS.items()
    }

    board_docs = data["allKanbanBoardDocs"]
    anchor_index = next(
        (
            index
            for index, doc in enumerate(board_docs)
            if doc.get("key") == PROGRESS_ANCHOR_DOC_KEY
        ),
        None,
    )
    if anchor_index is None:
        raise RuntimeError(
            f"No {PROGRESS_ANCHOR_DOC_KEY!r} board doc to anchor the synthetic progress board "
            f"against; the progress metrics cannot be positioned. Add a "
            f"{PROGRESS_ANCHOR_DOC_KEY!r} reference doc.",
        )
    progress = progress_board_doc(
        board_docs[anchor_index],
        data["allCards"],
        lookups["milestones"],
    )
    board_docs.insert(anchor_index + 1, progress)

    return {
        "cards": data["allCards"],
        "boardDocs": board_docs,
        "lookups": lookups,
        "blockingReferenceKindKeys": sorted(models.BLOCKING_REFERENCE_KIND_KEYS),
    }


def build_dashboard_snapshot(dashboard_data: dict[str, Any]) -> dict[str, Any]:
    """Deep-sort every list in the dashboard payload in place, returning it.

    Deterministic ordering (not resolver order) so the HTML data block diffs cleanly
    build over build, and so the markdown renderer can rely on the same order (items
    grouped by section, claims by upstream, paths by path) without re-sorting.
    """
    for card in dashboard_data["cards"]:
        for payload_key, (_accessor, sort_key) in CARD_CHILD_LISTS.items():
            card.get(payload_key, []).sort(key=sort_key)
    dashboard_data["cards"].sort(key=lambda card: card["number"])

    for doc in dashboard_data["boardDocs"]:
        doc.get("cardReferences", []).sort(key=lambda ref: (ref["order"], ref["id"]))
    dashboard_data["boardDocs"].sort(key=lambda doc: (doc["order"], doc["key"]))

    for name, rows in dashboard_data["lookups"].items():
        if name == "trackedPaths":
            rows.sort(key=lambda row: row["path"])
        else:
            rows.sort(key=lambda row: (row.get("order", 0), row["id"]))
    return dashboard_data
