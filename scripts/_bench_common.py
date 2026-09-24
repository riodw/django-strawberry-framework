"""Shared bootstrap, provenance and measurement plumbing for the measurement scripts.

Owns the in-process fakeshop Django bring-up every measurement script needs:
the example-project ``sys.path`` seam, the settings module, the database tail
chosen by ``mode``, ``django.setup()`` and the ``migrate --run-syncdb`` pass.
A figure is admissible evidence only when the process that produced it names
the package it imported and the database it opened, so the bootstrap prints
and returns that provenance and refuses to run when either points outside the
tree the script lives in.

A path names a location, not the bytes measured there, so the provenance also
fingerprints content: ``package_digest`` hashes every ``.py`` file of the
imported package and ``instrument_ids`` gives the git blob id of the running
script and of this module. Two runs are the same instrument on the same tree
only when their package digest and every instrument id match. The git HEAD
beside them is supplementary: a workspace copy without ``.git`` reads
``unavailable``, and a dirty working tree runs bytes HEAD does not hold.

Also owns the pieces several scripts share after bring-up: the query-count
capture, the plan-cache reset, the glossary seeder, per-round timing
summaries and the ``--json`` document shape. Django imports stay
function-local so the module imports without a configured project.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import statistics
import subprocess
import sys
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, get_args

if TYPE_CHECKING:
    from collections.abc import Iterator, Sequence

REPO_ROOT = Path(__file__).resolve().parent.parent
FAKESHOP = REPO_ROOT / "examples" / "fakeshop"
TRACKED_DB = FAKESHOP / "db.sqlite3"
BENCH_COMMON = Path(__file__).resolve()

BootstrapMode = Literal["sqlite-memory", "pg"]
BOOTSTRAP_MODES: tuple[str, ...] = get_args(BootstrapMode)


def memory_db_name(alias: str) -> str:
    """Return the shared-cache in-memory SQLite name for ``alias``.

    A bare ``:memory:`` database is private to one connection, so a resolver
    running on an executor thread would open an empty database with no tables.
    A named shared-cache URI (Django's SQLite backend opens with ``uri=True``)
    gives every connection in the process the same tables and rows, while the
    database still lives only as long as the process.
    """
    return f"file:dsf-bench-{alias}?mode=memory&cache=shared"


def is_memory_db_name(name: object) -> bool:
    """Report whether a resolved SQLite ``NAME`` is an in-memory database."""
    text = str(name)
    return text == ":memory:" or "mode=memory" in text


@dataclass(frozen=True)
class BenchProvenance:
    """Identify the tree, package, content, database and versions one measurement ran against.

    ``instrument_ids`` pairs each instrument file's path (relative to the tree
    when inside it) with its git blob id, sorted by path.
    """

    package_file: str
    package_digest: str
    instrument_ids: tuple[tuple[str, str], ...]
    repo_root: str
    git_head: str
    settings_module: str
    db_alias: str
    db_vendor: str
    db_name: str
    python: str
    django: str
    strawberry: str
    platform: str

    def as_dict(self) -> dict[str, Any]:
        """Return the provenance as a plain dict for a ``--json`` header."""
        return {**asdict(self), "instrument_ids": dict(self.instrument_ids)}

    def lines(self) -> list[str]:
        """Return the human-readable header block printed before any figure."""
        return [
            "provenance",
            f"  package   {self.package_file}",
            f"  digest    {self.package_digest}",
            *(f"  script    {path} blob {blob}" for path, blob in self.instrument_ids),
            f"  tree      {self.repo_root} (git HEAD {self.git_head}, supplementary)",
            f"  settings  {self.settings_module}",
            f"  database  alias={self.db_alias} vendor={self.db_vendor} NAME={self.db_name}",
            f"  versions  python {self.python}, django {self.django}, "
            f"strawberry-graphql {self.strawberry}",
            f"  platform  {self.platform}",
        ]


def git_head(root: Path = REPO_ROOT) -> str:
    """Return the checkout's HEAD sha, or ``unavailable`` for a copy without ``.git``.

    A workspace copy made by rsync or ``git archive`` carries no repository,
    and a dirty working tree runs bytes no commit holds, so the sha is
    supplementary; ``package_digest`` and ``instrument_ids`` identify the
    content a figure measured.
    """
    if not (root / ".git").exists():
        return "unavailable"
    try:
        completed = subprocess.run(
            [
                "git",
                "-C",
                str(root),
                "rev-parse",
                "HEAD",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return "unavailable"
    return completed.stdout.strip() or "unavailable"


def git_blob_id(path: str | Path) -> str:
    """Return the git blob id of the file at ``path``, the id ``git hash-object`` prints.

    The id is ``sha1(b"blob <size>" + NUL + bytes)``, computed without a
    repository, so a workspace copy without ``.git`` still names the exact
    bytes of the instrument it ran.
    """
    data = Path(path).read_bytes()
    header = b"blob %d\0" % len(data)
    return hashlib.sha1(header + data, usedforsecurity=False).hexdigest()


def package_digest(package_root: str | Path) -> str:
    """Return a sha256 over every ``.py`` file under ``package_root``.

    Each file contributes its path relative to ``package_root`` (POSIX form)
    and its bytes, both length-prefixed so two different trees never feed the
    hash the same byte stream; files are taken in sorted path order, so the
    file-system enumeration order cannot move the digest. Compiled ``.pyc``
    files and non-Python data are outside the population.

    Raises:
        ValueError: ``package_root`` holds no ``.py`` file, so the digest
            would fingerprint an empty population.
    """
    root = Path(package_root)
    files = sorted((path.relative_to(root).as_posix(), path) for path in root.rglob("*.py"))
    if not files:
        msg = f"no .py file under {root}; nothing to fingerprint"
        raise ValueError(msg)
    digest = hashlib.sha256()
    for relative, path in files:
        name = relative.encode("utf-8")
        data = path.read_bytes()
        digest.update(len(name).to_bytes(8, "big"))
        digest.update(name)
        digest.update(len(data).to_bytes(8, "big"))
        digest.update(data)
    return f"sha256:{digest.hexdigest()}"


def running_script() -> Path | None:
    """Return the resolved path of the ``__main__`` script, or ``None`` without one."""
    main_file = getattr(sys.modules.get("__main__"), "__file__", None)
    return Path(main_file).resolve() if main_file else None


def instrument_ids(script: Path | None, root: Path = REPO_ROOT) -> dict[str, str]:
    """Map the running ``script`` and this module to their git blob ids, sorted by path.

    Paths inside ``root`` are keyed relative to it, so two workspace copies of
    one tree produce the same keys. ``script`` of ``None`` (``python -c``, a
    REPL) is recorded as ``__main__: unavailable`` rather than omitted.
    """

    def _key(path: Path) -> str:
        resolved = path.resolve()
        base = root.resolve()
        return (
            resolved.relative_to(base).as_posix()
            if resolved.is_relative_to(base)
            else str(resolved)
        )

    ids = {_key(BENCH_COMMON): git_blob_id(BENCH_COMMON)}
    if script is None:
        ids["__main__"] = "unavailable"
    else:
        ids[_key(script)] = git_blob_id(script)
    return dict(sorted(ids.items()))


def _distribution_version(name: str) -> str:
    from importlib.metadata import PackageNotFoundError, version

    try:
        return version(name)
    except PackageNotFoundError:
        return "unknown"


def assert_package_in_tree(package_file: str | Path, root: Path = REPO_ROOT) -> None:
    """Refuse a package imported from outside the tree that holds this script.

    An editable install resolves ``django_strawberry_framework`` to whichever
    checkout the venv was built from, so a script run from a workspace copy
    can silently measure the shared checkout instead of the copy's change.

    Raises:
        RuntimeError: ``package_file`` does not lie under ``root``.
    """
    resolved = Path(package_file).resolve()
    if not resolved.is_relative_to(root.resolve()):
        msg = (
            f"django_strawberry_framework was imported from {resolved}, outside the "
            f"running tree {root}. Run the script with that tree as cwd "
            "(uv run --directory <tree>) so its own venv installs its own package."
        )
        raise RuntimeError(msg)


def assert_not_tracked_db(name: object, tracked: Path = TRACKED_DB) -> None:
    """Refuse a database ``NAME`` that resolves to the tracked fakeshop fixture.

    The tracked ``db.sqlite3`` holds the board and glossary rows and is written
    by concurrent sessions; a migrate or a seeding teardown against it destroys
    committed rows.

    Raises:
        RuntimeError: ``name`` is the tracked database file.
    """
    if is_memory_db_name(name) or not str(name):
        return
    if Path(str(name)).resolve() == tracked.resolve():
        msg = (
            f"database NAME {name} is the tracked fixture {tracked}; a measurement "
            "must never open it."
        )
        raise RuntimeError(msg)


def bootstrap_fakeshop_django(mode: BootstrapMode) -> BenchProvenance:
    """Configure Django for the fakeshop example project, check provenance, migrate.

    ``mode`` selects the database tail:

    - ``"sqlite-memory"``: replace every configured alias with a shared-cache
      in-memory SQLite database BEFORE any connection opens, whatever
      ``FAKESHOP_PG_DSN`` / ``FAKESHOP_SHARDED`` / ``DJANGO_STRAWBERRY_KANBAN_DB``
      selected, so no tracked database file is read or written.
    - ``"pg"``: require ``FAKESHOP_PG_DSN`` (the settings module's Postgres
      branch) and refuse a non-Postgres vendor; the lateral strategy only
      executes on Postgres.

    The provenance header prints before ``migrate`` so a refused or failing run
    still names the tree it would have measured.

    Returns:
        The provenance of this process.

    Raises:
        ValueError: ``mode`` is not one of ``BOOTSTRAP_MODES``.
        RuntimeError: the package or the database lies outside this tree's rules.
    """
    if mode not in BOOTSTRAP_MODES:
        msg = f"unknown bootstrap mode {mode!r}; expected one of {BOOTSTRAP_MODES}"
        raise ValueError(msg)
    sys.path.insert(0, str(FAKESHOP))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    if mode == "pg" and not os.environ.get("FAKESHOP_PG_DSN"):
        sys.exit(
            "FAKESHOP_PG_DSN is required: the lateral strategy only executes on "
            "Postgres, so there is nothing to compare on SQLite. Start the "
            "throwaway server (docker compose -f docker-compose.postgres.yml up -d) "
            "and re-run with FAKESHOP_PG_DSN=postgres://fakeshop:fakeshop@127.0.0.1:5432/fakeshop.",
        )

    if mode == "sqlite-memory":
        from django.conf import settings

        for alias in list(settings.DATABASES):
            settings.DATABASES[alias] = {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": memory_db_name(alias),
            }
    import django

    django.setup()

    from django.db import connection, connections

    import django_strawberry_framework

    if mode == "pg" and connection.vendor != "postgresql":
        sys.exit(f"Expected a postgresql connection, got {connection.vendor!r}.")
    package_file = Path(django_strawberry_framework.__file__).resolve()
    provenance = BenchProvenance(
        package_file=str(package_file),
        package_digest=package_digest(package_file.parent),
        instrument_ids=tuple(instrument_ids(running_script()).items()),
        repo_root=str(REPO_ROOT),
        git_head=git_head(),
        settings_module=os.environ["DJANGO_SETTINGS_MODULE"],
        db_alias=connection.alias,
        db_vendor=connection.vendor,
        db_name=str(connection.settings_dict["NAME"]),
        python=platform.python_version(),
        django=django.get_version(),
        strawberry=_distribution_version("strawberry-graphql"),
        platform=platform.platform(),
    )
    print("\n".join(provenance.lines()), flush=True)
    assert_package_in_tree(provenance.package_file)
    for alias in connections:
        name = connections[alias].settings_dict["NAME"]
        assert_not_tracked_db(name)
        if mode == "sqlite-memory" and not is_memory_db_name(name):
            msg = f"sqlite-memory mode resolved alias {alias!r} to NAME {name}, not in-memory"
            raise RuntimeError(msg)

    from django.core.management import call_command

    call_command("migrate", run_syncdb=True, verbosity=0)
    return provenance


@contextmanager
def capture_queries(alias: str = "default") -> Iterator[Any]:
    """Count the SQL one block of work issues on ``alias``.

    Wraps ``django.test.utils.CaptureQueriesContext`` so every script counts
    queries one way: it forces the debug cursor for the block only and reads
    the captured list, independent of ``settings.DEBUG``. The connection's
    query log is cleared first: it is a bounded deque that fakeshop's
    ``DEBUG = True`` fills during timed loops, and a full log makes the
    context's before/after slice read zero. It sees only the calling thread's
    connection, so the counted work must run synchronously
    (``schema.execute_sync``).

    Yields:
        The context; ``len(ctx)`` is the query count and
        ``ctx.captured_queries`` the ``{"sql", "time"}`` entries.
    """
    from django.db import connections
    from django.test.utils import CaptureQueriesContext

    connection = connections[alias]
    connection.queries_log.clear()
    with CaptureQueriesContext(connection) as ctx:
        yield ctx


def reset_plan_cache(optimizer: Any) -> None:
    """Return the optimizer to a cold start: no cached plan, no cached document key.

    ``cache_clear`` empties the extension's plan cache and counters;
    ``clear_document_key_cache`` empties the module-level memo every extension
    shares, without which a "cold" request still skips printing its document.
    """
    from django_strawberry_framework.optimizer.extension import clear_document_key_cache

    optimizer.cache_clear()
    clear_document_key_cache()


def seed_glossary_terms(count: int) -> dict[str, int]:
    """Ensure ``count`` glossary terms exist, each carrying one row per relation.

    ``apps.products.services.seed_data`` seeds only the catalog, so without
    this every glossary query a script runs resolves an empty list. Term ``i``
    gets one alias, one category membership, one source link, one outgoing
    link to term ``i - 1`` (so the previous term gets the matching incoming
    link) and term ``i - 1`` as a related term. Row counts are deterministic;
    Faker text is not. Rows come from ``apps.glossary.factories``.

    Returns:
        The total rows present per glossary model the candidates select.
    """
    from apps.glossary import factories, models

    terms = list(models.GlossaryTerm.objects.order_by("id"))
    while len(terms) < count:
        term = factories.make_glossary_term()
        factories.make_glossary_alias(term=term)
        factories.make_glossary_category_membership(term=term)
        factories.make_glossary_source_link(term=term)
        if terms:
            previous = terms[-1]
            factories.make_glossary_term_link(source_term=term, target_term=previous)
            term.related_terms.add(previous)
        terms.append(term)
    return {
        "GlossaryTerm": models.GlossaryTerm.objects.count(),
        "GlossaryAlias": models.GlossaryAlias.objects.count(),
        "GlossaryCategoryMembership": models.GlossaryCategoryMembership.objects.count(),
        "GlossarySourceLink": models.GlossarySourceLink.objects.count(),
        "GlossaryTermLink": models.GlossaryTermLink.objects.count(),
    }


def summarize_rounds(rounds: Sequence[Sequence[float]]) -> dict[str, float]:
    """Summarize repeated timing rounds as ``min``, ``median`` and ``spread``.

    One round's median moves by more than most code changes between two
    identical runs, so a figure is reported with the variation across rounds
    beside it: ``min`` is the fastest sample of any round, ``median`` the
    median of the per-round medians, ``spread`` the range of those medians and
    ``spread_pct`` that range as a percentage of ``median``.

    Raises:
        ValueError: no round, or an empty round.
    """
    if not rounds or any(not samples for samples in rounds):
        msg = "summarize_rounds needs at least one non-empty round"
        raise ValueError(msg)
    medians = [statistics.median(samples) for samples in rounds]
    median = statistics.median(medians)
    spread = max(medians) - min(medians)
    return {
        "min": min(min(samples) for samples in rounds),
        "median": median,
        "spread": spread,
        "spread_pct": (spread / median * 100.0) if median else 0.0,
    }


def build_report(
    *,
    tool: str,
    provenance: dict[str, str],
    params: dict[str, Any],
    rows: list[dict[str, Any]],
    failures: list[str],
) -> dict[str, Any]:
    """Assemble the ``--json`` document every measurement script writes.

    One shape across scripts lets a before/after pair be compared field by
    field: ``header`` holds ``tool``, ``provenance`` and the run ``params``
    (iterations, rounds, seeding); ``rows`` holds one entry per measured shape
    in run order; ``status`` is ``failed`` whenever ``failures`` names a row
    that errored or was skipped.
    """
    return {
        "failures": list(failures),
        "header": {"params": dict(params), "provenance": dict(provenance), "tool": tool},
        "rows": list(rows),
        "status": "failed" if failures else "ok",
    }


def write_report(path: str | Path, report: dict[str, Any]) -> None:
    """Write ``report`` as JSON with sorted keys so two runs diff line by line."""
    Path(path).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_graphql_document(path: str | Path) -> str:
    """Read a GraphQL operation file for a ``--query`` flag."""
    return Path(path).read_text(encoding="utf-8")


def parse_variables(raw: str | None) -> dict[str, Any] | None:
    """Parse a ``--variables`` JSON object, refusing any other JSON value.

    Raises:
        TypeError: ``raw`` is JSON but not an object.
    """
    if raw is None:
        return None
    value = json.loads(raw)
    if not isinstance(value, dict):
        msg = f"--variables must be a JSON object, got {type(value).__name__}"
        raise TypeError(msg)
    return value


def root_row_count(data: Any) -> int | None:
    """Return the length of the first root list (or connection ``edges``) in ``data``.

    A query-count verdict is evidence only when the parent rows under it grew,
    so scripts print this beside every count.
    """
    if not isinstance(data, dict):
        return None
    for value in data.values():
        if isinstance(value, list):
            return len(value)
        if isinstance(value, dict) and isinstance(value.get("edges"), list):
            return len(value["edges"])
    return None
