"""Hand the REVIEW, HUNT and DRY agentflows disposable workspace copies, so workers only review.

A scratch directory is not a sandbox: a probe there still imports the shared
package and opens the tracked ``examples/fakeshop/db.sqlite3``. Every
measurement, mutation and bench run therefore happens in a copy of the shared
tree with its own virtualenv and its own databases. This script owns all of
that. A worker names one address, ``<flow>/<item>/<role>`` (the item may
itself hold slashes, such as a package path), and never builds, checks or
deletes a copy by hand.

Worker commands
    ``run <address> [--cell default|sharded|pg] [--fresh] -- <command...>``
        Run ``<command>`` inside the address's copy through
        ``uv run --frozen --group pg``. ``<command>`` is what would follow
        ``uv run``: ``pytest <node> --no-cov``,
        ``python scripts/count_queries.py ...``. Paths inside it resolve
        against the copy. The first run of an address binds it to a copy
        synced from the shared tree as it stands at that moment; later runs
        reuse that copy as it stands, edits included. ``--fresh`` resyncs it
        from the shared tree first.
    ``prove <address> <manifest> [--cell ...] [--fresh] [-- <extra args>]``
        ``run`` of ``scripts/prove_failability.py`` in its workspace form:
        ``--workspace`` is the copy; ``--scratch-root`` and ``--json`` sit
        under this flow's evidence folder, never inside the copy.
    ``path <address>``
        Print the copy's directory, binding it first when unbound, so a
        worker can read or edit files there.

Worker-0 commands
    ``baseline <flow>/<item>``
        Print ``ITEM_BASELINE=<sha>`` (``git stash create``, or the
        ``git rev-parse HEAD`` sha when the tree is clean) and bind the
        address ``<flow>/<item>/before`` now. That is the one copy that must
        predate the item's first edit.
    ``release <flow>/<item> [--role <role>]... [--keep <role>]...``
        Return the item's copies to the pool; their Postgres databases are
        dropped. ``--keep before`` frees one phase's copies for the next while
        the pinned pre-edit copy stays. A release refuses while a command
        still runs in a copy it would free.
    ``audit <record.md>...``
        Resolve every run id a record cites against the run log. For each id
        it prints the address, cell, exit code and package digest, and whether
        the copy had been edited or the shared tree had moved. An id with no
        log entry, or whose package or database lay outside its copy, fails
        the audit.
    ``gate <flow> [--suites default,sharded,pg]``
        Run the final gate suites in a gate copy that carries a git index, as
        CI's jobs do: the full default suite (coverage floor), the sharded
        suite and the Postgres database-touching suite. The result is written
        to ``evidence/gate-<run id>.json`` and bound to the ``git stash
        create`` sha, the blob ids of ``pyproject.toml`` and ``uv.lock`` and
        each suite's cell.
    ``status [<flow>]``
        Print copies, bindings, active runs, disk use and Postgres leases.
    ``gc <flow> [--force]``
        Delete everything the flow holds: copies, gate copy, run log, proof
        scratch and its Postgres databases. The Postgres container is stopped
        when this script started it and no database of any flow remains. Run
        it after ``## Outcomes`` records what the evidence showed.

Every run prints a provenance header on stderr before its output and a footer
after it. The header gives the run id, address, copy, the package file the
copy imports and its digest, the cell and the database ``NAME`` of every
alias. It also says whether the copy is ``fresh`` or ``modified`` since its
sync, and whether the shared tree has moved since. Stdout carries only the
command's own output. Every run is appended to ``evidence/runs.jsonl`` and
its full output kept in ``evidence/logs/<run id>.log``. A record cites the run
id; ``audit`` checks it.

Layout: ``$TMPDIR/dsf-ws/<sha16 of the repo root>/<flow>/`` holds
``slots/slot-N/`` (the copies), ``gate/``, ``evidence/`` and ``state.json``.
It lives outside the repository, keyed per checkout (so a git worktree gets
its own), and is harness-agnostic. ``DSF_WS_ROOT`` replaces
``$TMPDIR/dsf-ws``; a root inside the repository is refused, since copies of
a tree holding its own copies recurse. ``DSF_WS_SLOTS`` caps each flow's pool
(default 4: three parallel roles and the pinned ``before``). New copies are
refused below 6 GB free.

Guarantees, each one a hand-run failure this encodes away:

* **Exact copies.** The copy is the shared tree's ``git ls-files -co
  --exclude-standard`` listing plus ``.python-version``. Cycle scratch is left
  out: ``output/``, ``docs/shadow/``, ``temp-tests/``, ``worker-memory/`` and
  any ``*-ws`` folder a harness parked in the tree. A resync mirrors that set
  byte for byte, deletes every other file except ``.venv`` (caches included),
  runs ``uv sync --frozen --group pg`` and asserts the copy's package digest
  equals the shared tree's. A shared file that changes mid-copy restarts the
  sync.
* **Copies are reset in place, never cloned.** A virtualenv's entry scripts
  name their own interpreter by absolute path. A cloned ``.venv/bin/pytest``
  would therefore import the other copy's package. Reuse keeps each copy at
  its own path.
* **A clean environment.** Every command runs without the caller's
  ``FAKESHOP_*``, ``DJANGO_*``, ``PYTEST_*``, ``COVERAGE_*`` and ``GIT_*``
  variables, ``PYTHONPATH``, ``VIRTUAL_ENV`` and the ``uv`` project
  redirects. An inherited ``DJANGO_STRAWBERRY_KANBAN_DB`` would point the
  copy's ``default`` alias at the tracked database; an inherited
  ``GIT_INDEX_FILE`` would make the copy listing read a private index.
* **Provenance is observed, not asserted.** Before the command runs, a probe
  under the same interpreter, cwd and cell resolves where the package would
  import from and every alias's ``NAME``. The command is refused when the
  package lies outside the copy, a SQLite database lies outside the copy, or
  the Postgres ``NAME`` is not the copy's own database.
* **One Postgres database per copy.** ``--cell pg`` starts the
  ``docker-compose.postgres.yml`` container when no fakeshop container runs.
  A running container is identified by its ``POSTGRES_USER`` and
  ``POSTGRES_DB``, never by port: another project's Postgres may publish the
  same container port. Each copy gets its own database
  ``ws_<repo>_<flow>_<slot>``, so pytest's ``test_<NAME>_gwN`` databases
  never collide across copies, flows or checkouts. The databases themselves
  are the leases every harness sees.
* **Evidence outlives reuse.** The run log, logs and proof scratch sit beside
  the copies, not inside them, so resyncing a copy for the next address keeps
  the evidence the last one produced.
* **Cleanup leaves nothing.** ``release`` unbinds copies and drops their
  databases. ``gc`` removes the flow folder, its databases, and the empty
  parent folders. A crashed run's lock dies with its process; a crashed sync
  resyncs on the address's next run.

Exit codes: ``run`` and ``prove`` return the command's own exit code. ``125``
means this script refused before the command ran (bad address, full pool,
wrong provenance, Postgres unavailable), with the reason on stderr. The other
commands return ``0`` on success and ``1`` on a failed audit, a failed gate
suite or a refusal.

POSIX only (``fcntl`` locks). Run from the shared checkout's root as
``uv run python scripts/workspace.py ...``, never from inside a copy.
"""

from __future__ import annotations

import argparse
import contextlib
import dataclasses
import datetime
import fcntl
import hashlib
import json
import os
import re
import secrets
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path
from typing import TYPE_CHECKING, BinaryIO

try:
    import _bench_common
except ModuleNotFoundError:  # imported as ``scripts.workspace`` (repo root on path)
    from scripts import _bench_common

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_DIR = "django_strawberry_framework"
COMPOSE_FILE = "docker-compose.postgres.yml"

ROOT_ENV = "DSF_WS_ROOT"
SLOTS_ENV = "DSF_WS_SLOTS"
DEFAULT_SLOTS = 4
MIN_FREE_BYTES = 6 * 1024**3
REFUSED = 125
MARKER_NAME = ".dsf-ws"

#: Listing entries under these prefixes are cycle output, never tree content.
EXCLUDED_PREFIXES = ("output/", "docs/shadow/")
#: A listing entry with any of these path segments is scratch or a parked copy.
EXCLUDED_SEGMENTS = frozenset(
    {
        "temp-tests",
        "worker-memory",
        "__pycache__",
        ".pytest_cache",
    },
)
#: Gitignored files the copy still needs.
EXTRA_FILES = (".python-version",)
#: Top-level entries a resync keeps in place instead of mirroring.
PRESERVED = frozenset({".venv"})
#: Files a command leaves behind that do not count as editing the copy.
GENERATED_SEGMENTS = frozenset(
    {
        "__pycache__",
        ".pytest_cache",
        ".ruff_cache",
        ".mypy_cache",
        "htmlcov",
    },
)

SCRUBBED_PREFIXES = (
    "FAKESHOP_",
    "DJANGO_",
    "PYTEST_",
    "COVERAGE_",
    "GIT_",
)
SCRUBBED_NAMES = frozenset(
    {
        "PYTHONPATH",
        "PYTHONHOME",
        "PYTHONSTARTUP",
        "VIRTUAL_ENV",
        "CONDA_PREFIX",
        "UV_PROJECT_ENVIRONMENT",
        "UV_PROJECT",
        "UV_WORKING_DIRECTORY",
        "UV_NO_SYNC",
        "UV_FROZEN",
        "UV_LOCKED",
    },
)

CELLS = ("default", "sharded", "pg")
PG_USER = "fakeshop"
PG_PASSWORD = "fakeshop"  # the throwaway compose container's documented credential
PG_PORT = "5432/tcp"
COMPOSE_PROJECT = "dsf-ws-postgres"

#: Each gate suite: pytest arguments and the cell it runs in (REVIEW.md "Final gate").
GATE_SUITES: dict[str, tuple[tuple[str, ...], str]] = {
    "default": (("pytest",), "default"),
    "sharded": (("pytest", "-o", "addopts=-v -n auto --dist loadscope"), "sharded"),
    "pg": (
        (
            "pytest",
            "-o",
            "addopts=-v -n 12 --dist loadscope",
            "-m",
            "django_db or pg",
        ),
        "pg",
    ),
}

FLOW_PATTERN = re.compile(r"^[a-z][a-z0-9]{0,15}$")
SEGMENT_PATTERN = re.compile(r"^[A-Za-z0-9_@+][A-Za-z0-9._@+-]*$")
RUN_ID_PATTERN = re.compile(r"\b([a-z][a-z0-9]{0,15})-(\d{8}T\d{6})-([0-9a-f]{6})\b")
SUMMARY_PATTERN = re.compile(r"^=+ (?P<summary>.+ in [\d.]+s(?: \([^)]*\))?) =+$")
COLLECTED_PATTERN = re.compile(r"\[(\d+) items?\]|collected (\d+) items?")

PROBE = """
import importlib, importlib.util, json, os, sys
sys.path.insert(0, os.path.join(os.getcwd(), "examples", "fakeshop"))
spec = importlib.util.find_spec("django_strawberry_framework")
settings = importlib.import_module("config.test_settings")
print(json.dumps({
    "executable": sys.executable,
    "package_file": spec.origin if spec else None,
    "databases": {
        alias: {"ENGINE": conf.get("ENGINE", ""), "NAME": str(conf.get("NAME", ""))}
        for alias, conf in settings.DATABASES.items()
    },
}))
"""


class WorkspaceError(Exception):
    """A refusal: the command never ran, and the message says why."""


class LockBusyError(WorkspaceError):
    """A copy's lock is held: a command is still running in it."""


# --------------------------------------------------------------------------------------------
# Addresses
# --------------------------------------------------------------------------------------------


def _check_flow(flow: str, text: str) -> None:
    if not FLOW_PATTERN.fullmatch(flow):
        msg = f"{text!r}: flow {flow!r} must be lowercase letters and digits, at most 16"
        raise WorkspaceError(msg)


def _check_segments(segments: Sequence[str], text: str) -> None:
    for segment in segments:
        if not SEGMENT_PATTERN.fullmatch(segment) or segment in {".", ".."}:
            msg = f"{text!r}: segment {segment!r} is not a plain name"
            raise WorkspaceError(msg)


@dataclasses.dataclass(frozen=True)
class ItemRef:
    """``<flow>/<item>``; the item may hold slashes."""

    flow: str
    item: str

    @classmethod
    def parse(cls, text: str) -> ItemRef:
        """Parse ``<flow>/<item>``."""
        parts = text.strip("/").split("/")
        if len(parts) < 2:  # flow + at least one item segment
            msg = f"{text!r}: expected <flow>/<item>"
            raise WorkspaceError(msg)
        _check_flow(parts[0], text)
        _check_segments(parts[1:], text)
        return cls(parts[0], "/".join(parts[1:]))


@dataclasses.dataclass(frozen=True)
class Address:
    """``<flow>/<item>/<role>``: the first segment is the flow, the last the role."""

    flow: str
    item: str
    role: str

    @classmethod
    def parse(cls, text: str) -> Address:
        """Parse ``<flow>/<item>/<role>``."""
        parts = text.strip("/").split("/")
        if len(parts) < 3:  # flow + item + role
            msg = f"{text!r}: expected <flow>/<item>/<role>"
            raise WorkspaceError(msg)
        _check_flow(parts[0], text)
        _check_segments(parts[1:], text)
        return cls(parts[0], "/".join(parts[1:-1]), parts[-1])

    def __str__(self) -> str:
        """Return the address as ``<flow>/<item>/<role>``."""
        return f"{self.flow}/{self.item}/{self.role}"

    @property
    def evidence_slug(self) -> str:
        """Return a one-segment folder name for this address's item."""
        return self.item.replace("/", "__")


# --------------------------------------------------------------------------------------------
# Environment, git, locks
# --------------------------------------------------------------------------------------------


def clean_env(base: dict[str, str] | None = None, **extra: str) -> dict[str, str]:
    """Return ``base`` (default ``os.environ``) without every redirecting variable, plus ``extra``."""
    source = os.environ if base is None else base
    env = {
        name: value
        for name, value in source.items()
        if name not in SCRUBBED_NAMES and not name.startswith(SCRUBBED_PREFIXES)
    }
    env.update(extra)
    return env


def _git(repo_root: Path, *args: str) -> str:
    completed = subprocess.run(
        [
            "git",
            "-C",
            str(repo_root),
            *args,
        ],
        capture_output=True,
        env=clean_env(),
        check=False,
    )
    if completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", "replace").strip()
        msg = f"git {' '.join(args)} failed ({completed.returncode}): {detail}"
        raise WorkspaceError(msg)
    return completed.stdout.decode("utf-8", "surrogateescape")


def baseline_sha(repo_root: Path) -> str:
    """Return ``git stash create``, or the ``HEAD`` sha when the tree has no tracked change."""
    return (
        _git(repo_root, "stash", "create").strip() or _git(repo_root, "rev-parse", "HEAD").strip()
    )


@contextlib.contextmanager
def file_lock(path: Path, *, blocking: bool = True) -> Iterator[None]:
    """Hold an exclusive ``flock`` on ``path``; the kernel drops it if the process dies."""
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_RDWR | os.O_CREAT, 0o644)
    try:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | (0 if blocking else fcntl.LOCK_NB))
        except BlockingIOError:
            msg = f"{path} is held: a command is still running there"
            raise LockBusyError(msg) from None
        yield
    finally:
        os.close(descriptor)


def lock_is_busy(path: Path) -> bool:
    """Report whether another process holds ``path``'s lock."""
    if not path.exists():
        return False
    try:
        with file_lock(path, blocking=False):
            return False
    except LockBusyError:
        return True


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def new_run_id(flow: str) -> str:
    """Return ``<flow>-<UTC timestamp>-<6 hex>``, the id a record cites."""
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S")
    return f"{flow}-{stamp}-{secrets.token_hex(3)}"


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def _read_json(path: Path, default: object) -> object:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


# --------------------------------------------------------------------------------------------
# Layout
# --------------------------------------------------------------------------------------------


def repo_key(repo_root: Path) -> str:
    """Return the 16-hex key that separates one checkout's workspaces from another's."""
    return hashlib.sha256(str(repo_root.resolve()).encode("utf-8")).hexdigest()[:16]


def check_shared_checkout(repo_root: Path) -> None:
    """Refuse a root that is a workspace copy rather than the shared checkout."""
    for parent in (repo_root, *repo_root.parents):
        if (parent / MARKER_NAME).exists():
            msg = f"{repo_root} is inside a workspace folder; run this from the shared checkout"
            raise WorkspaceError(msg)
    if not (repo_root / ".git").exists():
        msg = f"{repo_root} has no .git; run this from the shared checkout, not a copy"
        raise WorkspaceError(msg)


def workspace_base(repo_root: Path, environ: dict[str, str] | None = None) -> Path:
    """Return ``<root>/<repo key>``, refusing any root inside the repository."""
    source = os.environ if environ is None else environ
    raw = source.get(ROOT_ENV)
    parent = Path(raw).expanduser() if raw else Path(tempfile.gettempdir()) / "dsf-ws"
    base = parent.resolve() / repo_key(repo_root)
    if _is_within(base, repo_root):
        msg = (
            f"workspace root {base} is inside the repository {repo_root}; copies of a tree "
            f"that holds its own copies recurse. Point {ROOT_ENV} outside it."
        )
        raise WorkspaceError(msg)
    return base


def pool_size(environ: dict[str, str] | None = None) -> int:
    """Return the per-flow copy cap from ``DSF_WS_SLOTS`` (default 4)."""
    raw = (os.environ if environ is None else environ).get(SLOTS_ENV, "")
    if not raw:
        return DEFAULT_SLOTS
    if not raw.isdigit() or int(raw) < 1:
        msg = f"{SLOTS_ENV}={raw!r} must be a positive integer"
        raise WorkspaceError(msg)
    return int(raw)


@dataclasses.dataclass(frozen=True)
class Layout:
    """Where one flow's copies, locks, state and evidence live."""

    repo_root: Path
    base: Path
    flow: str

    @classmethod
    def for_flow(cls, flow: str, repo_root: Path = REPO_ROOT) -> Layout:
        """Return the layout for ``flow`` under this checkout's workspace root."""
        _check_flow(flow, flow)
        return cls(repo_root, workspace_base(repo_root), flow)

    @property
    def flow_dir(self) -> Path:
        """The flow's folder; ``gc`` removes exactly this."""
        return self.base / self.flow

    @property
    def state_path(self) -> Path:
        """Bindings and item baselines."""
        return self.flow_dir / "state.json"

    @property
    def pool_lock(self) -> Path:
        """Guards ``state.json``."""
        return self.flow_dir / "pool.lock"

    @property
    def evidence(self) -> Path:
        """Run log, per-run logs, proof scratch and gate results."""
        return self.flow_dir / "evidence"

    @property
    def run_log(self) -> Path:
        """One JSON line per run."""
        return self.evidence / "runs.jsonl"

    @property
    def gate_dir(self) -> Path:
        """The gate copy, outside the pool."""
        return self.flow_dir / "gate"

    def slot_dir(self, slot: str) -> Path:
        """Return one copy's directory."""
        return self.flow_dir / "slots" / slot

    def slot_lock(self, slot: str) -> Path:
        """Return the lock a run holds on its copy."""
        return self.flow_dir / "slots" / f"{slot}.lock"

    def manifest_path(self, slot: str) -> Path:
        """Return the record of what the copy was last synced to."""
        return self.flow_dir / "slots" / f"{slot}.manifest.json"

    def db_name(self, slot: str) -> str:
        """Return the copy's own Postgres database name."""
        return f"ws_{repo_key(self.repo_root)[:12]}_{self.flow}_{slot.replace('-', '')}"

    @property
    def db_prefix(self) -> str:
        """Every database this flow owns starts with this (after an optional ``test_``)."""
        return f"ws_{repo_key(self.repo_root)[:12]}_{self.flow}_"

    def ensure_marked(self) -> None:
        """Create the flow folder with the marker that lets ``gc`` prove it owns it."""
        self.flow_dir.mkdir(parents=True, exist_ok=True)
        marker = self.flow_dir / MARKER_NAME
        if not marker.exists():
            _write_json(marker, {"repo_root": str(self.repo_root), "flow": self.flow})


# --------------------------------------------------------------------------------------------
# Mirroring the shared tree
# --------------------------------------------------------------------------------------------


def is_excluded(name: str) -> bool:
    """Report whether a listing entry is cycle scratch or a parked copy, not tree content."""
    if name.startswith(EXCLUDED_PREFIXES):
        return True
    parts = name.split("/")
    return any(part in EXCLUDED_SEGMENTS or part.endswith("-ws") for part in parts[:-1])


def wanted_files(repo_root: Path) -> dict[str, Path]:
    """Return ``{relative name: path}`` for every file a copy must hold.

    Raises:
        WorkspaceError: the listing does not include the package's
            ``__init__.py``, so it enumerated something other than this tree.
    """
    listing = _git(repo_root, "ls-files", "-z", "-co", "--exclude-standard")
    names = {name for name in listing.split("\0") if name}
    names.update(name for name in EXTRA_FILES if os.path.lexists(repo_root / name))
    result: dict[str, Path] = {}
    for name in sorted(names):
        path = repo_root / name
        if is_excluded(name) or not os.path.lexists(path):
            continue
        if path.is_dir() and not path.is_symlink():
            continue
        result[name] = path
    if f"{PACKAGE_DIR}/__init__.py" not in result:
        msg = f"git listed no {PACKAGE_DIR}/__init__.py under {repo_root}; refusing to copy"
        raise WorkspaceError(msg)
    return result


def file_hash(path: Path) -> str:
    """Return a sha1 of a file's bytes, or of a symlink's target text."""
    if path.is_symlink():
        target = os.readlink(path).encode("utf-8", "surrogateescape")
        return "link:" + hashlib.sha1(target, usedforsecurity=False).hexdigest()
    digest = hashlib.sha1(usedforsecurity=False)
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _stat_key(path: Path) -> tuple[int, int] | None:
    try:
        status = os.lstat(path)
    except FileNotFoundError:
        return None
    return (status.st_size, status.st_mtime_ns)


def _same_entry(destination: Path, source: Path, source_hash: str) -> bool:
    if not os.path.lexists(destination):
        return False
    if source.is_symlink() != destination.is_symlink() or destination.is_dir():
        return False
    if not source.is_symlink() and os.lstat(destination).st_size != os.lstat(source).st_size:
        return False
    return file_hash(destination) == source_hash


def _copy_entry(source: Path, destination: Path, repo_root: Path) -> None:
    if os.path.lexists(destination):
        if destination.is_dir() and not destination.is_symlink():
            shutil.rmtree(destination)
        else:
            destination.unlink()
    parent = destination.parent
    if os.path.lexists(parent) and not parent.is_dir():
        parent.unlink()
    parent.mkdir(parents=True, exist_ok=True)
    if source.is_symlink():
        target = os.readlink(source)
        if os.path.isabs(target) and _is_within(Path(target), repo_root):
            msg = f"{source} links into the shared tree by absolute path; a copy would share it"
            raise WorkspaceError(msg)
        os.symlink(target, destination)
    else:
        shutil.copy2(source, destination)


def _remove_unwanted(
    destination: Path,
    wanted: dict[str, Path],
    preserved: frozenset[str],
) -> None:
    for directory, dirnames, filenames in os.walk(destination):
        here = Path(directory)
        relative_dir = here.relative_to(destination).as_posix()
        prefix = "" if relative_dir == "." else f"{relative_dir}/"
        keep_dirs = []
        for name in dirnames:
            relative = f"{prefix}{name}"
            if not prefix and name in preserved:
                continue
            if (here / name).is_symlink():
                (here / name).unlink()
                continue
            if relative in wanted:
                shutil.rmtree(here / name)
                continue
            keep_dirs.append(name)
        dirnames[:] = keep_dirs
        for name in filenames:
            relative = f"{prefix}{name}"
            if not prefix and name in preserved:
                continue
            if relative not in wanted:
                (here / name).unlink()


def _prune_empty_dirs(destination: Path, preserved: frozenset[str]) -> None:
    for directory, _dirnames, _filenames in os.walk(destination, topdown=False):
        here = Path(directory)
        if here == destination:
            continue
        top = here.relative_to(destination).parts[0]
        if top in preserved:
            continue
        with contextlib.suppress(OSError):
            here.rmdir()


def tree_digest(entries: dict[str, list]) -> str:
    """Return a sha256 over every ``(name, content hash)`` pair, in name order."""
    digest = hashlib.sha256()
    for name in sorted(entries):
        digest.update(f"{name}\0{entries[name][0]}\n".encode("utf-8", "surrogateescape"))
    return f"sha256:{digest.hexdigest()}"


def mirror_tree(
    repo_root: Path,
    destination: Path,
    *,
    preserved: frozenset[str] = PRESERVED,
    attempts: int = 3,
) -> dict[str, list]:
    """Make ``destination`` an exact copy of the shared tree's wanted files.

    Returns ``{name: [content hash, size, shared mtime_ns, copy mtime_ns]}``,
    the manifest drift reports compare against.

    Raises:
        WorkspaceError: the shared tree kept changing during every attempt.
    """
    raced: list[str] = []
    for _attempt in range(attempts):
        wanted = wanted_files(repo_root)
        destination.mkdir(parents=True, exist_ok=True)
        _remove_unwanted(destination, wanted, preserved)
        entries: dict[str, list] = {}
        raced = []
        for name, source in wanted.items():
            before = _stat_key(source)
            source_hash = file_hash(source)
            target = destination / name
            if not _same_entry(target, source, source_hash):
                _copy_entry(source, target, repo_root)
                if file_hash(target) != source_hash:
                    raced.append(name)
            after = _stat_key(source)
            if before != after or after is None:
                raced.append(name)
                continue
            copied = _stat_key(target)
            entries[name] = [
                source_hash,
                after[0],
                after[1],
                copied[1] if copied else 0,
            ]
        _prune_empty_dirs(destination, preserved)
        if not raced:
            return entries
    msg = f"the shared tree kept changing while it was copied: {sorted(set(raced))[:5]}"
    raise WorkspaceError(msg)


def _uv_sync(destination: Path) -> None:
    command = [
        "uv",
        "sync",
        "--directory",
        str(destination),
        "--frozen",
        "--group",
        "pg",
        "-q",
    ]
    completed = subprocess.run(command, capture_output=True, env=clean_env(), check=False)
    if completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", "replace").strip()
        msg = f"uv sync failed in {destination} ({completed.returncode}): {detail}"
        raise WorkspaceError(msg)


def sync_copy(
    repo_root: Path,
    destination: Path,
    *,
    preserved: frozenset[str] = PRESERVED,
) -> dict[str, object]:
    """Mirror, ``uv sync`` and digest-check one copy; return its manifest."""
    entries = mirror_tree(repo_root, destination, preserved=preserved)
    _uv_sync(destination)
    copy_digest = _bench_common.package_digest(destination / PACKAGE_DIR)
    shared_digest = _bench_common.package_digest(repo_root / PACKAGE_DIR)
    if copy_digest != shared_digest:
        msg = (
            f"package digest of {destination} ({copy_digest}) differs from the shared tree's "
            f"({shared_digest}); a package file changed during the sync, run again"
        )
        raise WorkspaceError(msg)
    return {
        "synced_at": _now(),
        "tree_digest": tree_digest(entries),
        "package_digest": copy_digest,
        "entries": entries,
    }


def _is_generated(relative: str) -> bool:
    parts = relative.split("/")
    return any(part in GENERATED_SEGMENTS for part in parts) or parts[-1].startswith(".coverage")


def copy_edits(
    destination: Path,
    manifest: dict,
    preserved: frozenset[str] = PRESERVED,
) -> list[str]:
    """Return the names a copy changed, added or deleted since its sync, caches excluded."""
    entries: dict[str, list] = manifest.get("entries", {})
    changed = []
    for name, (
        content_hash,
        size,
        _shared_mtime,
        copy_mtime,
    ) in entries.items():
        path = destination / name
        key = _stat_key(path)
        if key is None or (key != (size, copy_mtime) and file_hash(path) != content_hash):
            changed.append(name)
    for directory, dirnames, filenames in os.walk(destination):
        here = Path(directory)
        relative_dir = here.relative_to(destination).as_posix()
        prefix = "" if relative_dir == "." else f"{relative_dir}/"
        dirnames[:] = [
            name
            for name in dirnames
            if not (not prefix and name in preserved) and name not in GENERATED_SEGMENTS
        ]
        for name in filenames:
            relative = f"{prefix}{name}"
            if relative not in entries and not _is_generated(relative):
                changed.append(relative)
    return sorted(changed)


def shared_moves(repo_root: Path, manifest: dict) -> list[str]:
    """Return the names the shared tree changed, added or deleted since the copy's sync."""
    entries: dict[str, list] = manifest.get("entries", {})
    wanted = wanted_files(repo_root)
    moved = sorted(set(wanted) ^ set(entries))
    for name in set(wanted) & set(entries):
        content_hash, size, shared_mtime, _copy_mtime = entries[name]
        key = _stat_key(wanted[name])
        if key != (size, shared_mtime) and file_hash(wanted[name]) != content_hash:
            moved.append(name)
    return sorted(moved)


# --------------------------------------------------------------------------------------------
# Postgres
# --------------------------------------------------------------------------------------------


class Postgres:
    """The fakeshop compose container, found by identity, and the per-copy databases in it."""

    def __init__(self, repo_root: Path) -> None:
        """Bind to the checkout whose compose file starts the container."""
        self.repo_root = repo_root
        self._container: tuple[str, str, str] | None = None

    def _docker(self, *args: str, check: bool = True) -> str:
        if shutil.which("docker") is None:
            msg = "docker is not on PATH, so the Postgres cell cannot run"
            raise WorkspaceError(msg)
        completed = subprocess.run(
            ["docker", *args],
            capture_output=True,
            env=clean_env(),
            check=False,
        )
        if check and completed.returncode != 0:
            detail = completed.stderr.decode("utf-8", "replace").strip()
            msg = f"docker {args[0]} failed ({completed.returncode}): {detail}"
            raise WorkspaceError(msg)
        return completed.stdout.decode("utf-8", "replace")

    def attach(self) -> bool:
        """Remember the running fakeshop container; report whether one runs."""
        self._container = self.find()
        return self._container is not None

    def find(self) -> tuple[str, str, str] | None:
        """Return ``(container id, host port, compose project)`` of the fakeshop container."""
        ids = self._docker("ps", "-q").split()
        if not ids:
            return None
        found = []
        for info in json.loads(self._docker("inspect", *ids)):
            env = set(info.get("Config", {}).get("Env") or [])
            if f"POSTGRES_USER={PG_USER}" not in env or f"POSTGRES_DB={PG_USER}" not in env:
                continue
            bindings = (info.get("NetworkSettings", {}).get("Ports") or {}).get(PG_PORT) or []
            if not bindings:
                continue
            labels = info.get("Config", {}).get("Labels") or {}
            project = labels.get("com.docker.compose.project", "")
            found.append((info["Id"][:12], bindings[0]["HostPort"], project))
        if len(found) > 1:
            msg = f"{len(found)} fakeshop Postgres containers run ({found}); stop all but one"
            raise WorkspaceError(msg)
        return found[0] if found else None

    def ensure(self) -> tuple[str, str, str]:
        """Return the running container, starting the compose one when none runs."""
        if self._container is None:
            self._container = self.find()
        if self._container is None:
            compose = self.repo_root / COMPOSE_FILE
            self._docker(
                "compose",
                "-p",
                COMPOSE_PROJECT,
                "-f",
                str(compose),
                "up",
                "-d",
                "--wait",
            )
            self._container = self.find()
            if self._container is None:
                msg = f"docker compose started {COMPOSE_FILE} but no fakeshop container is found"
                raise WorkspaceError(msg)
        user = self.sql("SELECT current_user").strip()
        if user != PG_USER:
            msg = f"container {self._container[0]} answers as {user!r}, not {PG_USER!r}"
            raise WorkspaceError(msg)
        return self._container

    def sql(self, statement: str, database: str = "postgres") -> str:
        """Run one statement through ``psql`` inside the container."""
        container = self._container or self.find()
        if container is None:
            msg = "no fakeshop Postgres container runs"
            raise WorkspaceError(msg)
        return self._docker(
            "exec",
            container[0],
            "psql",
            "-U",
            PG_USER,
            "-d",
            database,
            "-v",
            "ON_ERROR_STOP=1",
            "-tAc",
            statement,
        )

    def dsn(self, database: str) -> str:
        """Return the DSN of ``database`` on the running container."""
        _container, port, _project = self.ensure()
        return f"postgres://{PG_USER}:{PG_PASSWORD}@127.0.0.1:{port}/{database}"

    def recreate(self, database: str) -> None:
        """Drop ``database`` and every pytest database derived from it, then create it empty."""
        self.drop_matching(database, exact=True)
        self.sql(f'CREATE DATABASE "{database}"')

    def databases(self, prefix: str = "ws_", *, exact: bool = False) -> list[str]:
        """Return the container's databases named ``prefix...`` or ``test_prefix...``.

        With ``exact`` the name is ``prefix`` itself, plus the ``test_<prefix>``
        and ``test_<prefix>_gwN`` databases pytest-django derives from it, so
        ``slot1`` never matches ``slot10``.
        """
        escaped = prefix.replace("_", r"\_")
        if exact:
            clause = (
                f"datname IN ('{prefix}', 'test_{prefix}') "
                f"OR datname LIKE 'test\\_{escaped}\\_gw%'"
            )
        else:
            clause = f"datname LIKE '{escaped}%' OR datname LIKE 'test\\_{escaped}%'"
        rows = self.sql(f"SELECT datname FROM pg_database WHERE {clause} ORDER BY datname")
        return [row for row in rows.splitlines() if row]

    def drop_matching(self, prefix: str, *, exact: bool = False) -> list[str]:
        """Drop every database ``databases`` returns for ``prefix``; return their names."""
        names = self.databases(prefix, exact=exact)
        for name in names:
            self.sql(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')
        return names

    def stop_if_idle(self) -> str:
        """Stop the container when this script started it and no workspace database remains."""
        container = self.find()
        if container is None:
            return "no fakeshop Postgres container runs"
        self._container = container
        remaining = self.databases()
        if remaining:
            return f"Postgres kept: {len(remaining)} workspace database(s) remain"
        if container[2] != COMPOSE_PROJECT:
            return f"Postgres kept: container {container[0]} was not started by this script"
        compose = self.repo_root / COMPOSE_FILE
        self._docker("compose", "-p", COMPOSE_PROJECT, "-f", str(compose), "down")
        return f"Postgres stopped: container {container[0]}"


def _running_postgres(repo_root: Path) -> Postgres | None:
    """Return a handle when docker answers and a fakeshop container runs, else ``None``."""
    postgres = Postgres(repo_root)
    try:
        return postgres if postgres.attach() else None
    except WorkspaceError:
        return None


# --------------------------------------------------------------------------------------------
# The copy pool, bindings and syncs
# --------------------------------------------------------------------------------------------


def _load_state(layout: Layout) -> dict:
    state = _read_json(layout.state_path, None)
    if state is None:
        state = {
            "version": 1,
            "repo_root": str(layout.repo_root),
            "slots": {},
            "items": {},
        }
    return state


@dataclasses.dataclass(frozen=True)
class Binding:
    """One address bound to one copy."""

    slot: str
    directory: Path
    needs_sync: bool


def _free_bytes(path: Path) -> int:
    probe = path
    while not probe.exists():
        probe = probe.parent
    return shutil.disk_usage(probe).free


def bind(layout: Layout, address: Address, *, fresh: bool = False) -> Binding:
    """Bind ``address`` to a copy: its existing one, a free warm one, or a new one.

    Raises:
        WorkspaceError: every copy is bound to another address, or a new copy
            would drop free disk below the guard.
    """
    layout.ensure_marked()
    with file_lock(layout.pool_lock):
        state = _load_state(layout)
        slots: dict[str, dict | None] = state["slots"]
        for slot, bound in slots.items():
            if bound and bound["address"] == str(address):
                needs = fresh or bound.get("status") != "ready"
                return Binding(slot, layout.slot_dir(slot), needs)
        free = sorted((slot for slot, bound in slots.items() if not bound), key=_slot_number)
        if free:
            slot = free[0]
        elif len(slots) < pool_size():
            if _free_bytes(layout.base) < MIN_FREE_BYTES:
                msg = f"under {MIN_FREE_BYTES // 1024**3} GB free at {layout.base}; no new copy"
                raise WorkspaceError(msg)
            slot = f"slot-{max((_slot_number(name) for name in slots), default=0) + 1}"
        else:
            listing = ", ".join(f"{slot} {bound['address']}" for slot, bound in slots.items())
            msg = (
                f"{layout.flow}: all {len(slots)} copies are bound ({listing}). Release a "
                f"finished item: uv run python scripts/workspace.py release {layout.flow}/<item>"
            )
            raise WorkspaceError(msg)
        slots[slot] = {
            "address": str(address),
            "item": address.item,
            "role": address.role,
            "bound_at": _now(),
            "status": "syncing",
        }
        _write_json(layout.state_path, state)
        return Binding(slot, layout.slot_dir(slot), True)


def _slot_number(name: str) -> int:
    return int(name.rpartition("-")[2])


def _mark_synced(layout: Layout, slot: str, manifest: dict) -> None:
    with file_lock(layout.pool_lock):
        state = _load_state(layout)
        bound = state["slots"].get(slot)
        if bound:
            bound.update(
                status="ready",
                synced_at=manifest["synced_at"],
                tree_digest=manifest["tree_digest"],
                package_digest=manifest["package_digest"],
            )
            _write_json(layout.state_path, state)


def sync_slot(layout: Layout, slot: str) -> dict:
    """Resync one copy from the shared tree and drop its Postgres databases."""
    postgres = _running_postgres(layout.repo_root)
    if postgres is not None:
        postgres.drop_matching(layout.db_name(slot), exact=True)
    manifest = sync_copy(layout.repo_root, layout.slot_dir(slot))
    _write_json(layout.manifest_path(slot), manifest)
    _mark_synced(layout, slot, manifest)
    return manifest


# --------------------------------------------------------------------------------------------
# Running a command
# --------------------------------------------------------------------------------------------


def cell_env(layout: Layout, slot: str, cell: str) -> tuple[dict[str, str], str | None]:
    """Return the clean environment for ``cell`` and the copy's Postgres database, if any."""
    if cell == "default":
        return clean_env(), None
    if cell == "sharded":
        return clean_env(FAKESHOP_SHARDED="1"), None
    database = layout.db_name(slot)
    postgres = Postgres(layout.repo_root)
    postgres.ensure()
    if not postgres.databases(database, exact=True):
        postgres.recreate(database)
    return clean_env(FAKESHOP_PG_DSN=postgres.dsn(database)), database


def probe(directory: Path, env: dict[str, str]) -> dict:
    """Resolve, inside the copy, where the package imports from and each alias's database."""
    command = [
        "uv",
        "run",
        "--directory",
        str(directory),
        "--frozen",
        "--group",
        "pg",
    ]
    completed = subprocess.run(
        [
            *command,
            "python",
            "-c",
            PROBE,
        ],
        capture_output=True,
        env=env,
        check=False,
    )
    if completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", "replace").strip()
        msg = f"the provenance probe failed in {directory}: {detail}"
        raise WorkspaceError(msg)
    return json.loads(completed.stdout.decode("utf-8").strip().splitlines()[-1])


def provenance_faults(
    found: dict,
    directory: Path,
    cell: str,
    database: str | None,
) -> list[str]:
    """Return why a probe result is not this copy's provenance; empty when it is."""
    faults = []
    package = found.get("package_file")
    if not package or not _is_within(Path(package), directory):
        faults.append(f"package would import from {package}, outside {directory}")
    executable = found.get("executable") or ""
    if not _is_within(Path(executable).parent, directory / ".venv"):
        faults.append(f"interpreter {executable} is not the copy's .venv")
    for alias, conf in found.get("databases", {}).items():
        name, engine = conf["NAME"], conf["ENGINE"]
        if "postgresql" in engine:
            if cell != "pg" or name != database:
                faults.append(f"alias {alias!r} opens Postgres {name!r}, not {database!r}")
        elif not _bench_common.is_memory_db_name(name) and not _is_within(Path(name), directory):
            faults.append(f"alias {alias!r} opens {name}, outside {directory}")
    if cell == "pg" and found.get("databases", {}).get("default", {}).get("NAME") != database:
        faults.append(f"cell pg did not select {database!r} for the default alias")
    return faults


def _pump(
    source: BinaryIO,
    sink: BinaryIO,
    log: BinaryIO,
    lock: threading.Lock,
) -> None:
    for chunk in iter(lambda: source.read1(1 << 16), b""):
        sink.write(chunk)
        sink.flush()
        with lock:
            log.write(chunk)


def stream(
    command: Sequence[str],
    env: dict[str, str],
    log_path: Path,
    header: str,
) -> int:
    """Run ``command``, copying its stdout and stderr through while logging both."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("wb") as log:
        log.write(header.encode("utf-8"))
        log.flush()
        process = subprocess.Popen(  # the worker's own command, in its copy
            list(command),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        lock = threading.Lock()
        pumps = [
            threading.Thread(
                target=_pump,
                args=(
                    process.stdout,
                    sys.stdout.buffer,
                    log,
                    lock,
                ),
            ),
            threading.Thread(
                target=_pump,
                args=(
                    process.stderr,
                    sys.stderr.buffer,
                    log,
                    lock,
                ),
            ),
        ]
        for pump in pumps:
            pump.start()
        code = process.wait()
        for pump in pumps:
            pump.join()
    return code


def _short(names: list[str], limit: int = 4) -> str:
    shown = ", ".join(names[:limit])
    return f"{shown}, +{len(names) - limit} more" if len(names) > limit else shown


def render_header(record: dict) -> str:
    """Return the provenance header a run prints before its output."""
    edits = record["copy_edits"]
    moves = record["shared_moves"]
    databases = ", ".join(f"{alias}={name}" for alias, name in record["databases"].items())
    lines = [
        f"workspace run {record['run_id']}",
        f"  address  {record['address']}",
        f"  copy     {record['directory']} ({record['slot']}, synced {record['synced_at']})",
        f"  package  {record['package_file']}",
        f"  digest   {record['package_digest']}",
        f"  cell     {record['cell']}: {databases}",
        f"  copy is  {'fresh' if not edits else f'modified: {len(edits)} ({_short(edits)})'}",
        "  shared   "
        + ("unmoved since sync" if not moves else f"moved: {len(moves)} ({_short(moves)})"),
        f"  command  {' '.join(record['command'])}",
        f"  log      {record['log']}",
    ]
    return "\n".join(lines) + "\n"


def execute(
    layout: Layout,
    address: Address,
    build_command: Callable[[Path, str], list[str]],
    *,
    cell: str = "default",
    fresh: bool = False,
) -> int:
    """Bind, sync when needed, probe, then run the command in the address's copy."""
    check_shared_checkout(layout.repo_root)
    binding = bind(layout, address, fresh=fresh)
    with file_lock(layout.slot_lock(binding.slot)):
        manifest = (
            sync_slot(layout, binding.slot)
            if binding.needs_sync or not layout.manifest_path(binding.slot).exists()
            else _read_json(layout.manifest_path(binding.slot), {})
        )
        env, database = cell_env(layout, binding.slot, cell)
        found = probe(binding.directory, env)
        faults = provenance_faults(found, binding.directory, cell, database)
        if faults:
            raise WorkspaceError("wrong tree: " + "; ".join(faults))
        run_id = new_run_id(layout.flow)
        command = build_command(binding.directory, run_id)
        log_path = layout.evidence / "logs" / f"{run_id}.log"
        record = {
            "run_id": run_id,
            "address": str(address),
            "item": address.item,
            "role": address.role,
            "slot": binding.slot,
            "directory": str(binding.directory),
            "synced_at": manifest.get("synced_at"),
            "tree_digest": manifest.get("tree_digest"),
            "package_file": found["package_file"],
            "package_digest": _bench_common.package_digest(binding.directory / PACKAGE_DIR),
            "cell": cell,
            "databases": {alias: conf["NAME"] for alias, conf in found["databases"].items()},
            "copy_edits": copy_edits(binding.directory, manifest),
            "shared_moves": shared_moves(layout.repo_root, manifest),
            "command": command,
            "log": str(log_path),
            "started": _now(),
        }
        header = render_header(record)
        sys.stderr.write(header)
        sys.stderr.flush()
        started = time.monotonic()
        uv_run = [
            "uv",
            "run",
            "--directory",
            str(binding.directory),
            "--frozen",
            "--group",
            "pg",
        ]
        code = stream([*uv_run, "--", *command], env, log_path, header)
        record.update(exit=code, seconds=round(time.monotonic() - started, 2))
    layout.evidence.mkdir(parents=True, exist_ok=True)
    with layout.run_log.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")
    sys.stderr.write(f"workspace run {record['run_id']} exit {code} in {record['seconds']}s\n")
    return code


def _worker_command(raw: Sequence[str]) -> list[str]:
    command = list(raw)
    if not command:
        msg = "no command given; put it after --"
        raise WorkspaceError(msg)
    if command[0] == "uv":
        msg = "give the command that follows `uv run`, not `uv ...`; the copy's uv run wraps it"
        raise WorkspaceError(msg)
    return command


# --------------------------------------------------------------------------------------------
# Worker-0: release, gc, status, audit, gate
# --------------------------------------------------------------------------------------------


def release(
    layout: Layout,
    item: str,
    roles: Sequence[str] = (),
    keep: Sequence[str] = (),
) -> list[str]:
    """Unbind the item's copies and drop their databases.

    ``roles`` limits the release to those roles; ``keep`` spares those roles,
    so ``keep=("before",)`` frees one phase's copies for the next phase while
    the pinned pre-edit copy stays. Only a whole-item release forgets the
    item's ``ITEM_BASELINE``.

    Raises:
        LockBusyError: a command still runs in one of them.
    """
    if not (layout.flow_dir / MARKER_NAME).exists():
        return []
    with file_lock(layout.pool_lock):
        state = _load_state(layout)
        chosen = [
            slot
            for slot, bound in state["slots"].items()
            if bound
            and bound["item"] == item
            and (not roles or bound["role"] in roles)
            and bound["role"] not in keep
        ]
        busy = [slot for slot in chosen if lock_is_busy(layout.slot_lock(slot))]
        if busy:
            msg = f"{layout.flow}/{item}: a command still runs in {', '.join(busy)}"
            raise LockBusyError(msg)
        postgres = _running_postgres(layout.repo_root)
        released = []
        for slot in chosen:
            if postgres is not None:
                postgres.drop_matching(layout.db_name(slot), exact=True)
            released.append(f"{slot} {state['slots'][slot]['address']}")
            state["slots"][slot] = None
        if not roles and not keep:
            state["items"].pop(item, None)
        if layout.state_path.exists():
            _write_json(layout.state_path, state)
    return released


def gc(layout: Layout, *, force: bool = False) -> list[str]:
    """Delete the flow folder and its databases; stop Postgres when this script owns it idle."""
    report = []
    flow_dir = layout.flow_dir
    if flow_dir.exists():
        if not (flow_dir / MARKER_NAME).exists():
            msg = f"{flow_dir} carries no {MARKER_NAME} marker; refusing to delete it"
            raise WorkspaceError(msg)
        locks = [*(flow_dir / "slots").glob("*.lock"), flow_dir / "gate.lock"]
        busy = [lock.stem for lock in locks if lock_is_busy(lock)]
        if busy and not force:
            msg = f"a command still runs in {', '.join(busy)}; wait, or pass --force"
            raise LockBusyError(msg)
    postgres = _running_postgres(layout.repo_root)
    if postgres is not None:
        dropped = postgres.drop_matching(layout.db_prefix)
        report.append(f"dropped {len(dropped)} Postgres database(s)")
    if flow_dir.exists():
        size = sum(
            path.lstat().st_size
            for path in flow_dir.rglob("*")
            if path.is_file() and not path.is_symlink()
        )
        shutil.rmtree(flow_dir)
        report.append(f"removed {flow_dir} ({size / 1024**2:.0f} MB)")
    # The default ``dsf-ws`` parent is this script's to remove; a DSF_WS_ROOT folder is not.
    parents = [layout.base] if os.environ.get(ROOT_ENV) else [layout.base, layout.base.parent]
    for parent in parents:
        with contextlib.suppress(OSError):
            parent.rmdir()
    if postgres is not None:
        report.append(postgres.stop_if_idle())
    return report


def status(repo_root: Path, flow: str | None) -> list[str]:
    """Describe every flow's copies, bindings, active runs and Postgres leases."""
    base = workspace_base(repo_root)
    lines = [f"root {base}"]
    flows = (
        [flow] if flow else sorted(p.name for p in base.glob("*") if (p / MARKER_NAME).exists())
    )
    for name in flows:
        layout = Layout(repo_root, base, name)
        state = _load_state(layout)
        lines.append(f"{name}: {len(state['slots'])} of {pool_size()} copies")
        for slot, bound in sorted(state["slots"].items(), key=lambda pair: _slot_number(pair[0])):
            running = " RUNNING" if lock_is_busy(layout.slot_lock(slot)) else ""
            where = f"{bound['address']} ({bound.get('status')})" if bound else "free (warm)"
            lines.append(f"  {slot}  {where}{running}")
        for item, entry in sorted(state["items"].items()):
            lines.append(f"  item {item}  ITEM_BASELINE={entry['item_baseline']}")
    postgres = _running_postgres(repo_root)
    if postgres is None:
        lines.append("postgres: no fakeshop container runs")
    else:
        leases = postgres.databases()
        container = postgres.find()
        lines.append(f"postgres: container {container[0]}, {len(leases)} workspace database(s)")
        lines.extend(f"  {name}" for name in leases)
    return lines


def load_runs(layout: Layout) -> dict[str, dict]:
    """Return every logged run of the flow by id."""
    if not layout.run_log.exists():
        return {}
    runs = {}
    for line in layout.run_log.read_text(encoding="utf-8").splitlines():
        if line.strip():
            record = json.loads(line)
            runs[record["run_id"]] = record
    return runs


def audit_record(repo_root: Path, record_path: Path) -> tuple[list[str], bool]:
    """Resolve every run id ``record_path`` cites; return report lines and whether all bind."""
    text = record_path.read_text(encoding="utf-8")
    cited = list(dict.fromkeys(match.group(0) for match in RUN_ID_PATTERN.finditer(text)))
    lines = [f"{record_path}: {len(cited)} run id(s) cited"]
    base = workspace_base(repo_root)
    runs: dict[str, dict] = {}
    for flow in {match.group(1) for match in RUN_ID_PATTERN.finditer(text)}:
        runs.update(load_runs(Layout(repo_root, base, flow)))
    ok = True
    for run_id in cited:
        run = runs.get(run_id)
        if run is None:
            lines.append(f"  FAIL {run_id}: no run log entry (never ran here, or gc removed it)")
            ok = False
            continue
        directory = Path(run["directory"])
        faults = []
        if not _is_within(Path(run["package_file"]), directory):
            faults.append(f"package {run['package_file']} outside {directory}")
        for alias, name in run["databases"].items():
            inside = _is_within(Path(name), directory) or _bench_common.is_memory_db_name(name)
            if not inside and not name.startswith("ws_"):
                faults.append(f"alias {alias} opened {name}")
        edits, moves = run["copy_edits"], run["shared_moves"]
        verdict = "FAIL" if faults else "ok  "
        ok = ok and not faults
        lines.append(
            f"  {verdict} {run_id}: {run['address']} cell={run['cell']} exit={run['exit']} "
            f"digest={run['package_digest'][:19]} copy={'fresh' if not edits else f'modified {len(edits)}'} "
            f"shared={'unmoved' if not moves else f'moved {len(moves)}'}"
            + (f" [{'; '.join(faults)}]" if faults else ""),
        )
    return lines, ok


def build_gate_git(repo_root: Path, gate_dir: Path) -> str:
    """Give the gate copy its own git index of ``HEAD``, borrowing the shared object store.

    The suite's census asks git for the committable file list. A standalone
    repository whose objects come from the shared store (read-only alternates)
    answers it without the copy touching the shared index or a worktree's
    ``gitdir`` pointer. ``HEAD`` is detached at the shared ``HEAD`` commit, so
    ``git status`` in the copy reports the working tree's changes against it.
    """
    git_dir = gate_dir / ".git"
    if git_dir.is_dir() and not git_dir.is_symlink():
        shutil.rmtree(git_dir)
    elif os.path.lexists(git_dir):
        git_dir.unlink()
    _git(gate_dir, "init", "-q")
    common = Path(
        _git(repo_root, "rev-parse", "--path-format=absolute", "--git-common-dir").strip(),
    )
    (git_dir / "objects" / "info").mkdir(parents=True, exist_ok=True)
    (git_dir / "objects" / "info" / "alternates").write_text(
        f"{common / 'objects'}\n",
        encoding="utf-8",
    )
    exclude = common / "info" / "exclude"
    if exclude.exists():
        (git_dir / "info").mkdir(parents=True, exist_ok=True)
        shutil.copy2(exclude, git_dir / "info" / "exclude")
    head = _git(repo_root, "rev-parse", "HEAD").strip()
    _git(gate_dir, "update-ref", "--no-deref", "HEAD", head)
    _git(gate_dir, "read-tree", head)
    return head


def summarize_suite(log_text: str) -> dict[str, object]:
    """Pull pytest's summary, collected count and coverage lines out of one suite's output."""
    summary = None
    collected = None
    coverage = []
    for line in log_text.splitlines():
        stripped = line.strip()
        match = SUMMARY_PATTERN.match(stripped)
        if match:
            summary = match.group("summary")
        found = COLLECTED_PATTERN.search(stripped)
        if found:
            collected = int(found.group(1) or found.group(2))
        if stripped.startswith("TOTAL ") or "Required test coverage" in stripped:
            coverage.append(stripped)
    return {"summary": summary, "collected": collected, "coverage": coverage}


def gate(layout: Layout, suites: Sequence[str]) -> int:
    """Run the gate suites in the gate copy; write and print the bound result."""
    check_shared_checkout(layout.repo_root)
    layout.ensure_marked()
    repo_root = layout.repo_root
    with file_lock(layout.flow_dir / "gate.lock", blocking=False):
        if not layout.gate_dir.exists() and _free_bytes(layout.base) < MIN_FREE_BYTES:
            msg = f"under {MIN_FREE_BYTES // 1024**3} GB free at {layout.base}; no gate copy"
            raise WorkspaceError(msg)
        bound_to = baseline_sha(repo_root)
        manifest = sync_copy(repo_root, layout.gate_dir, preserved=PRESERVED | {".git"})
        head = build_gate_git(repo_root, layout.gate_dir)
        result: dict[str, object] = {
            "flow": layout.flow,
            "at": _now(),
            "stash_create": bound_to,
            "head": head,
            "blobs": {
                name: _bench_common.git_blob_id(repo_root / name)
                for name in ("pyproject.toml", "uv.lock")
            },
            "tree_digest": manifest["tree_digest"],
            "package_digest": manifest["package_digest"],
            "suites": {},
        }
        uv_run = [
            "uv",
            "run",
            "--directory",
            str(layout.gate_dir),
            "--frozen",
            "--group",
            "pg",
        ]
        all_passed = True
        for suite in suites:
            arguments, cell = GATE_SUITES[suite]
            run_id = new_run_id(layout.flow)
            log_path = layout.evidence / "logs" / f"{run_id}.log"
            entry: dict[str, object] = {"run_id": run_id, "cell": cell, "command": list(arguments)}
            try:
                env, database = gate_env(layout, cell)
            except WorkspaceError as error:
                entry.update(exit=None, unverified=str(error))
                result["suites"][suite] = entry
                all_passed = False
                sys.stderr.write(f"gate {suite}: unverified: {error}\n")
                continue
            header = f"workspace gate {run_id} suite={suite} cell={cell} copy={layout.gate_dir}\n"
            sys.stderr.write(header)
            started = time.monotonic()
            code = stream([*uv_run, "--", *arguments], env, log_path, header)
            entry.update(
                exit=code,
                seconds=round(time.monotonic() - started, 2),
                database=database,
                log=str(log_path),
                **summarize_suite(log_path.read_text(encoding="utf-8", errors="replace")),
            )
            result["suites"][suite] = entry
            all_passed = all_passed and code == 0
            _append_gate_run(layout, entry, suite, manifest)
        if "pg" in suites:
            postgres = _running_postgres(repo_root)
            if postgres is not None:
                postgres.drop_matching(layout.db_name("gate"), exact=True)
        result_path = layout.evidence / f"gate-{new_run_id(layout.flow)}.json"
        _write_json(result_path, result)
    print(f"gate {layout.flow}: bound to {bound_to}; result {result_path}")
    for suite, entry in result["suites"].items():
        verdict = entry.get("unverified") or f"exit {entry['exit']}: {entry.get('summary')}"
        print(f"  {suite:<8} {entry['run_id']}  {verdict}")
        for line in entry.get("coverage", []):
            print(f"           {line}")
    return 0 if all_passed else 1


def gate_env(layout: Layout, cell: str) -> tuple[dict[str, str], str | None]:
    """Return the gate copy's environment for ``cell`` and its Postgres database, if any."""
    if cell != "pg":
        return cell_env(layout, "gate", cell)
    database = layout.db_name("gate")
    postgres = Postgres(layout.repo_root)
    postgres.ensure()
    postgres.recreate(database)
    return clean_env(FAKESHOP_PG_DSN=postgres.dsn(database)), database


def _append_gate_run(
    layout: Layout,
    entry: dict,
    suite: str,
    manifest: dict,
) -> None:
    record = {
        "run_id": entry["run_id"],
        "address": f"{layout.flow}/gate/{suite}",
        "item": "gate",
        "role": suite,
        "slot": "gate",
        "directory": str(layout.gate_dir),
        "synced_at": manifest["synced_at"],
        "tree_digest": manifest["tree_digest"],
        "package_file": str(layout.gate_dir / PACKAGE_DIR / "__init__.py"),
        "package_digest": manifest["package_digest"],
        "cell": entry["cell"],
        "databases": {"default": entry["database"]} if entry.get("database") else {},
        "copy_edits": [],
        "shared_moves": [],
        "command": entry["command"],
        "log": entry["log"],
        "exit": entry["exit"],
        "seconds": entry["seconds"],
    }
    layout.evidence.mkdir(parents=True, exist_ok=True)
    with layout.run_log.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")


# --------------------------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------------------------


def _cmd_run(args: argparse.Namespace) -> int:
    address = Address.parse(args.address)
    command = _worker_command(args.tail)
    layout = Layout.for_flow(address.flow)
    return execute(
        layout,
        address,
        lambda _directory, _run_id: command,
        cell=args.cell,
        fresh=args.fresh,
    )


def _cmd_prove(args: argparse.Namespace) -> int:
    address = Address.parse(args.address)
    manifest = Path(args.manifest).expanduser().resolve()
    if not manifest.is_file():
        msg = f"manifest {manifest} is not a file"
        raise WorkspaceError(msg)
    extra = list(args.tail)
    layout = Layout.for_flow(address.flow)
    scratch = layout.evidence / "proofs" / address.evidence_slug / address.role

    def build(directory: Path, run_id: str) -> list[str]:
        return [
            "python",
            "scripts/prove_failability.py",
            str(manifest),
            "--workspace",
            str(directory),
            "--scratch-root",
            str(scratch),
            "--json",
            str(scratch / f"{run_id}.json"),
            *extra,
        ]

    return execute(layout, address, build, cell=args.cell, fresh=args.fresh)


def _cmd_path(args: argparse.Namespace) -> int:
    address = Address.parse(args.address)
    layout = Layout.for_flow(address.flow)
    check_shared_checkout(layout.repo_root)
    binding = bind(layout, address)
    if binding.needs_sync or not layout.manifest_path(binding.slot).exists():
        with file_lock(layout.slot_lock(binding.slot)):
            sync_slot(layout, binding.slot)
    print(binding.directory)
    return 0


def _cmd_baseline(args: argparse.Namespace) -> int:
    ref = ItemRef.parse(args.item)
    layout = Layout.for_flow(ref.flow)
    check_shared_checkout(layout.repo_root)
    sha = baseline_sha(layout.repo_root)
    address = Address(ref.flow, ref.item, "before")
    binding = bind(layout, address, fresh=True)
    with file_lock(layout.slot_lock(binding.slot)):
        manifest = sync_slot(layout, binding.slot)
    with file_lock(layout.pool_lock):
        state = _load_state(layout)
        state["items"][ref.item] = {"item_baseline": sha, "at": _now()}
        _write_json(layout.state_path, state)
    print(f"ITEM_BASELINE={sha}")
    print(f"before: {address} -> {binding.directory} ({manifest['tree_digest']})")
    return 0


def _cmd_release(args: argparse.Namespace) -> int:
    ref = ItemRef.parse(args.item)
    released = release(Layout.for_flow(ref.flow), ref.item, args.role or (), args.keep or ())
    print(f"released {len(released)} copy(ies)" + "".join(f"\n  {line}" for line in released))
    return 0


def _cmd_gc(args: argparse.Namespace) -> int:
    for line in gc(Layout.for_flow(args.flow), force=args.force):
        print(line)
    return 0


def _cmd_status(args: argparse.Namespace) -> int:
    for line in status(REPO_ROOT, args.flow):
        print(line)
    return 0


def _cmd_audit(args: argparse.Namespace) -> int:
    all_ok = True
    for record in args.records:
        lines, ok = audit_record(REPO_ROOT, Path(record))
        print("\n".join(lines))
        all_ok = all_ok and ok
    return 0 if all_ok else 1


def _cmd_gate(args: argparse.Namespace) -> int:
    suites = [suite.strip() for suite in args.suites.split(",") if suite.strip()]
    unknown = sorted(set(suites) - set(GATE_SUITES))
    if unknown or not suites:
        msg = f"--suites takes a subset of {', '.join(GATE_SUITES)}; got {args.suites!r}"
        raise WorkspaceError(msg)
    return gate(Layout.for_flow(args.flow), suites)


def build_parser() -> argparse.ArgumentParser:
    """Return the command-line parser."""
    parser = argparse.ArgumentParser(
        description=__doc__.split("\n\n", 1)[0],
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    commands = parser.add_subparsers(dest="name", required=True)

    run = commands.add_parser(
        "run",
        help="run a command in the address's copy",
        usage="%(prog)s <address> [--cell CELL] [--fresh] -- <what follows `uv run`>",
    )
    run.add_argument("address", help="<flow>/<item>/<role>")
    run.add_argument("--cell", choices=CELLS, default="default")
    run.add_argument(
        "--fresh",
        action="store_true",
        help="resync the copy from the shared tree first",
    )
    run.set_defaults(handler=_cmd_run)

    prove = commands.add_parser(
        "prove",
        help="run prove_failability.py in the address's copy",
        usage="%(prog)s <address> <manifest> [--cell CELL] [--fresh] [-- <extra args>]",
    )
    prove.add_argument("address", help="<flow>/<item>/<role>")
    prove.add_argument("manifest", help="proof manifest (JSON)")
    prove.add_argument("--cell", choices=CELLS, default="default")
    prove.add_argument(
        "--fresh",
        action="store_true",
        help="resync the copy from the shared tree first",
    )
    prove.set_defaults(handler=_cmd_prove)

    path = commands.add_parser("path", help="print the address's copy directory")
    path.add_argument("address", help="<flow>/<item>/<role>")
    path.set_defaults(handler=_cmd_path)

    baseline = commands.add_parser("baseline", help="ITEM_BASELINE + the pinned before copy")
    baseline.add_argument("item", help="<flow>/<item>")
    baseline.set_defaults(handler=_cmd_baseline)

    release_parser = commands.add_parser("release", help="return an item's copies to the pool")
    release_parser.add_argument("item", help="<flow>/<item>")
    release_parser.add_argument(
        "--role",
        action="append",
        help="release only this role's copy (repeatable)",
    )
    release_parser.add_argument(
        "--keep",
        action="append",
        help="release every copy but this role's (repeatable), e.g. --keep before",
    )
    release_parser.set_defaults(handler=_cmd_release)

    audit = commands.add_parser("audit", help="bind every run id a record cites")
    audit.add_argument("records", nargs="+", help="record files to audit")
    audit.set_defaults(handler=_cmd_audit)

    gate_parser = commands.add_parser("gate", help="run the final gate suites in a gate copy")
    gate_parser.add_argument("flow")
    gate_parser.add_argument("--suites", default=",".join(GATE_SUITES))
    gate_parser.set_defaults(handler=_cmd_gate)

    status_parser = commands.add_parser("status", help="describe copies, runs and leases")
    status_parser.add_argument("flow", nargs="?")
    status_parser.set_defaults(handler=_cmd_status)

    gc_parser = commands.add_parser("gc", help="delete everything the flow holds")
    gc_parser.add_argument("flow")
    gc_parser.add_argument(
        "--force",
        action="store_true",
        help="delete even while a run holds a lock",
    )
    gc_parser.set_defaults(handler=_cmd_gc)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Dispatch one command; a refusal prints its reason and exits 125 (run/prove) or 1.

    Everything after the first ``--`` is the worker's command (``run``) or
    extra ``prove_failability.py`` arguments (``prove``), split off before
    parsing so options such as ``--cell`` may follow the address.
    """
    words = list(sys.argv[1:] if argv is None else argv)
    tail: list[str] = []
    if "--" in words:
        split = words.index("--")
        words, tail = words[:split], words[split + 1 :]
    parser = build_parser()
    args = parser.parse_args(words)
    args.tail = tail
    if tail and args.name not in {"run", "prove"}:
        parser.error(f"{args.name} takes nothing after --")
    try:
        return args.handler(args)
    except WorkspaceError as error:
        print(f"workspace: {error}", file=sys.stderr)
        return REFUSED if args.name in {"run", "prove"} else 1


if __name__ == "__main__":
    sys.exit(main())
