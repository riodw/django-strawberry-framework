"""Repo-tooling tests for the agentflow workspace tool's copies, pool, evidence and cleanup.

Keeps the contracts of ``scripts/workspace.py`` against throwaway git
repositories and workspace roots under ``tmp_path``, never against this
checkout's copies or a running Postgres. The rows that matter most are the ones
whose failure would let a measurement read the wrong tree: the copy listing,
the exact mirror, the scrubbed environment, the provenance check, the per-copy
database match and the cleanup that must leave nothing. A live ``/graphql/``
request has no wire shape for workspace copies, so none of these rows can
move there. There is no live sibling in ``examples/fakeshop/test_query/``.
"""

import json
import os
import re
import subprocess
from pathlib import Path

import pytest
import yaml

from scripts import workspace

PACKAGE = workspace.PACKAGE_DIR


def _write(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.com",
            "-c",
            "commit.gpgsign=false",
            "-c",
            "core.hooksPath=/dev/null",
            *args,
        ],
        check=True,
        capture_output=True,
        text=True,
        env=workspace.clean_env(),
    )
    return result.stdout


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    _write(root / PACKAGE / "__init__.py", "VALUE = 1\n")
    _write(root / PACKAGE / "core.py", "CORE = 2\n")
    _write(root / "examples" / "fakeshop" / "db.sqlite3", "tracked db\n")
    _write(root / ".gitignore", ".python-version\nignored.txt\noutput/\ntemp-tests/\n")
    _write(root / ".python-version", "3.14\n")
    _git(root, "init", "-q")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "initial")
    return root


@pytest.fixture
def layout(repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> workspace.Layout:
    monkeypatch.delenv(workspace.SLOTS_ENV, raising=False)

    def _no_running_postgres(_root: Path) -> None:
        return None

    def _ample_free_bytes(_path: Path) -> int:
        return workspace.MIN_FREE_BYTES * 2

    monkeypatch.setattr(workspace, "_running_postgres", _no_running_postgres)
    monkeypatch.setattr(workspace, "_free_bytes", _ample_free_bytes)
    return workspace.Layout(repo, tmp_path / "ws" / workspace.repo_key(repo), "review")


# --------------------------------------------------------------------------------------------
# Addresses and environment
# --------------------------------------------------------------------------------------------


def test_address_takes_flow_first_role_last_and_the_item_between() -> None:
    address = workspace.Address.parse(
        "review/django_strawberry_framework/optimizer/walker.py/perf-1",
    )

    assert (address.flow, address.item, address.role) == (
        "review",
        "django_strawberry_framework/optimizer/walker.py",
        "perf-1",
    )
    assert str(address) == "review/django_strawberry_framework/optimizer/walker.py/perf-1"
    assert address.evidence_slug == "django_strawberry_framework__optimizer__walker.py"


@pytest.mark.parametrize(
    "text",
    [
        "review/role",
        "Review/item/role",
        "review/../role",
        "review/item/.",
        "review/it em/role",
    ],
)
def test_address_refuses_what_is_not_flow_item_role(text: str) -> None:
    with pytest.raises(workspace.WorkspaceError):
        workspace.Address.parse(text)


def test_item_ref_keeps_slashes_in_the_item() -> None:
    ref = workspace.ItemRef.parse("hunt/pkg/filters/sets.py")

    assert (ref.flow, ref.item) == ("hunt", "pkg/filters/sets.py")
    with pytest.raises(workspace.WorkspaceError):
        workspace.ItemRef.parse("hunt")


def test_clean_env_scrubs_every_redirect_and_keeps_the_rest() -> None:
    caller = {
        "PATH": "/bin",
        "HOME": "/home/x",
        "DJANGO_STRAWBERRY_KANBAN_DB": "/repo/examples/fakeshop/db.sqlite3",
        "FAKESHOP_PG_DSN": "postgres://elsewhere",
        "GIT_INDEX_FILE": "/scratch/idx",
        "UV_PROJECT_ENVIRONMENT": "/repo/.venv",
        "VIRTUAL_ENV": "/repo/.venv",
        "PYTHONPATH": "/repo",
        "PYTEST_ADDOPTS": "-x",
        "UV_CACHE_DIR": "/cache",
    }

    env = workspace.clean_env(caller, FAKESHOP_SHARDED="1")

    assert env == {
        "PATH": "/bin",
        "HOME": "/home/x",
        "UV_CACHE_DIR": "/cache",
        "FAKESHOP_SHARDED": "1",
    }


# --------------------------------------------------------------------------------------------
# Layout
# --------------------------------------------------------------------------------------------


def test_workspace_base_is_keyed_per_checkout_and_honours_the_root_override(
    repo: Path,
    tmp_path: Path,
) -> None:
    base = workspace.workspace_base(repo, {workspace.ROOT_ENV: str(tmp_path / "roots")})
    other = workspace.workspace_base(
        tmp_path / "other",
        {workspace.ROOT_ENV: str(tmp_path / "roots")},
    )

    assert base == (tmp_path / "roots").resolve() / workspace.repo_key(repo)
    assert base != other


def test_workspace_base_refuses_a_root_inside_the_repository(repo: Path) -> None:
    with pytest.raises(workspace.WorkspaceError, match="recurse"):
        workspace.workspace_base(repo, {workspace.ROOT_ENV: str(repo / "hunt-ws")})


def test_check_shared_checkout_refuses_a_copy(repo: Path, tmp_path: Path) -> None:
    workspace.check_shared_checkout(repo)
    copy = tmp_path / "flow" / "slots" / "slot-1"
    copy.mkdir(parents=True)
    _write(tmp_path / "flow" / workspace.MARKER_NAME, "{}")

    with pytest.raises(workspace.WorkspaceError, match="shared checkout"):
        workspace.check_shared_checkout(copy)
    with pytest.raises(workspace.WorkspaceError, match="no .git"):
        workspace.check_shared_checkout((tmp_path / "plain").resolve())


@pytest.mark.parametrize(("raw", "expected"), [("", 4), ("1", 1), ("9", 9)])
def test_pool_size_reads_the_slots_override(raw: str, expected: int) -> None:
    assert workspace.pool_size({workspace.SLOTS_ENV: raw}) == expected


@pytest.mark.parametrize("raw", ["0", "-2", "four"])
def test_pool_size_refuses_a_non_positive_cap(raw: str) -> None:
    with pytest.raises(workspace.WorkspaceError):
        workspace.pool_size({workspace.SLOTS_ENV: raw})


def test_database_names_are_per_copy_and_fit_postgres_identifiers(repo: Path) -> None:
    layout = workspace.Layout(repo, Path("/unused"), "review")
    name = layout.db_name("slot-12")

    assert name.startswith(layout.db_prefix)
    assert name.endswith("_review_slot12")
    assert layout.db_name("slot-1") != layout.db_name("slot-10")
    assert len(f"test_{name}_gw63") <= 63  # NAMEDATALEN - 1


# --------------------------------------------------------------------------------------------
# The copy listing and the mirror
# --------------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("name", "excluded"),
    [
        ("output/report.txt", True),
        ("docs/shadow/current/a.py", True),
        ("docs/review/temp-tests/x/probe.py", True),
        ("docs/dry/worker-memory/w1.md", True),
        ("hunt-ws/item/pkg/a.py", True),
        ("docs/review/REVIEW.md", False),
        ("django_strawberry_framework/core.py", False),
        ("scripts/workspace.py", False),
    ],
)
def test_is_excluded_drops_cycle_scratch_and_parked_copies(name: str, excluded: bool) -> None:
    assert workspace.is_excluded(name) is excluded


def test_wanted_files_is_the_git_listing_plus_python_version_minus_scratch(repo: Path) -> None:
    _write(repo / "untracked.py", "NEW = 1\n")
    _write(repo / "ignored.txt", "ignored\n")
    _write(repo / "output" / "run.txt", "out\n")
    _write(repo / "hunt-ws" / "item" / "copy.py", "parked\n")
    (repo / PACKAGE / "core.py").unlink()

    wanted = workspace.wanted_files(repo)

    assert sorted(wanted) == [
        ".gitignore",
        ".python-version",
        f"{PACKAGE}/__init__.py",
        "examples/fakeshop/db.sqlite3",
        "untracked.py",
    ]


def test_wanted_files_refuses_a_listing_without_the_package(tmp_path: Path) -> None:
    root = tmp_path / "empty"
    _write(root / "README.md", "x\n")
    _git(root, "init", "-q")

    with pytest.raises(workspace.WorkspaceError, match="refusing to copy"):
        workspace.wanted_files(root)


def test_mirror_makes_an_exact_copy_and_a_resync_restores_a_dirtied_one(
    repo: Path,
    tmp_path: Path,
) -> None:
    copy = tmp_path / "copy"
    first = workspace.mirror_tree(repo, copy)
    _write(copy / ".venv" / "bin" / "python", "kept\n")
    _write(copy / PACKAGE / "core.py", "CORE = 'mutated'\n")
    _write(copy / "examples" / "fakeshop" / "db.sqlite3", "written by a probe\n")
    _write(copy / "extra" / "probe.py", "leftover\n")
    _write(copy / PACKAGE / "__pycache__" / "core.cpython-314.pyc", "cache\n")

    second = workspace.mirror_tree(repo, copy)

    assert workspace.tree_digest(first) == workspace.tree_digest(second)
    assert (copy / PACKAGE / "core.py").read_text(encoding="utf-8") == "CORE = 2\n"
    assert (copy / "examples" / "fakeshop" / "db.sqlite3").read_text(
        encoding="utf-8",
    ) == "tracked db\n"
    assert not (copy / "extra").exists()
    assert not (copy / PACKAGE / "__pycache__").exists()
    assert (copy / ".venv" / "bin" / "python").read_text(encoding="utf-8") == "kept\n"
    on_disk = sorted(
        path.relative_to(copy).as_posix()
        for path in copy.rglob("*")
        if path.is_file() and ".venv" not in path.parts
    )
    assert on_disk == sorted(second)


def test_mirror_replaces_a_file_that_became_a_directory(repo: Path, tmp_path: Path) -> None:
    copy = tmp_path / "copy"
    workspace.mirror_tree(repo, copy)
    (repo / PACKAGE / "core.py").unlink()
    _write(repo / PACKAGE / "core.py" / "inner.py", "INNER = 1\n")

    entries = workspace.mirror_tree(repo, copy)

    assert f"{PACKAGE}/core.py/inner.py" in entries
    assert (copy / PACKAGE / "core.py" / "inner.py").is_file()


def test_mirror_copies_a_relative_symlink_and_refuses_an_absolute_one_into_the_tree(
    repo: Path,
    tmp_path: Path,
) -> None:
    (repo / "link.py").symlink_to(f"{PACKAGE}/core.py")
    copy = tmp_path / "copy"
    workspace.mirror_tree(repo, copy)

    assert os.readlink(copy / "link.py") == f"{PACKAGE}/core.py"

    (repo / "link.py").unlink()
    (repo / "link.py").symlink_to(repo / PACKAGE / "core.py")
    with pytest.raises(workspace.WorkspaceError, match="absolute path"):
        workspace.mirror_tree(repo, tmp_path / "copy2")


def test_tree_digest_moves_with_content_and_not_with_order() -> None:
    entries = {
        "a.py": [
            "h1",
            1,
            0,
            0,
        ],
        "b.py": [
            "h2",
            1,
            0,
            0,
        ],
    }
    reordered = {
        "b.py": [
            "h2",
            9,
            9,
            9,
        ],
        "a.py": [
            "h1",
            9,
            9,
            9,
        ],
    }
    changed = {
        "a.py": [
            "h1",
            1,
            0,
            0,
        ],
        "b.py": [
            "h3",
            1,
            0,
            0,
        ],
    }

    assert workspace.tree_digest(entries) == workspace.tree_digest(reordered)
    assert workspace.tree_digest(entries) != workspace.tree_digest(changed)


def _manifest(entries: dict[str, list[str | int]]) -> workspace._Manifest:
    """A slot manifest holding ``entries`` and placeholder sync stamps."""
    return {
        "synced_at": "t",
        "tree_digest": "d",
        "package_digest": "p",
        "entries": entries,
    }


def test_copy_edits_reports_changes_additions_and_deletions_but_not_caches(
    repo: Path,
    tmp_path: Path,
) -> None:
    copy = tmp_path / "copy"
    manifest = _manifest(workspace.mirror_tree(repo, copy))
    assert workspace.copy_edits(copy, manifest) == []

    _write(copy / PACKAGE / "core.py", "CORE = 3\n")
    _write(copy / "new_probe.py", "x\n")
    (copy / ".python-version").unlink()
    _write(copy / PACKAGE / "__pycache__" / "x.pyc", "c\n")
    _write(copy / ".coverage", "c\n")
    _write(copy / ".venv" / "lib" / "site.py", "v\n")

    assert workspace.copy_edits(copy, manifest) == [
        ".python-version",
        f"{PACKAGE}/core.py",
        "new_probe.py",
    ]


def test_shared_moves_reports_what_the_shared_tree_changed_since_the_sync(
    repo: Path,
    tmp_path: Path,
) -> None:
    manifest = _manifest(workspace.mirror_tree(repo, tmp_path / "copy"))
    assert workspace.shared_moves(repo, manifest) == []

    _write(repo / PACKAGE / "core.py", "CORE = 'edited by Worker-2'\n")
    _write(repo / "added.py", "x\n")

    assert workspace.shared_moves(repo, manifest) == ["added.py", f"{PACKAGE}/core.py"]


# --------------------------------------------------------------------------------------------
# Pool
# --------------------------------------------------------------------------------------------


def _address(role: str, item: str = "pkg/a.py") -> workspace.Address:
    return workspace.Address("review", item, role)


def test_bind_reuses_an_address_and_gives_each_new_address_its_own_copy(
    layout: workspace.Layout,
) -> None:
    first = workspace.bind(layout, _address("perf-1"))
    workspace._mark_synced(
        layout,
        first.slot,
        _manifest({}),
    )
    again = workspace.bind(layout, _address("perf-1"))
    second = workspace.bind(layout, _address("mech-1"))
    refreshed = workspace.bind(layout, _address("perf-1"), fresh=True)

    assert (first.slot, first.needs_sync) == ("slot-1", True)
    assert (again.slot, again.needs_sync) == ("slot-1", False)
    assert (second.slot, second.needs_sync) == ("slot-2", True)
    assert refreshed.needs_sync is True
    assert (layout.flow_dir / workspace.MARKER_NAME).exists()


def test_an_unfinished_sync_resyncs_on_the_next_run(layout: workspace.Layout) -> None:
    workspace.bind(layout, _address("perf-1"))

    assert workspace.bind(layout, _address("perf-1")).needs_sync is True


def test_bind_refuses_when_every_copy_is_bound_and_release_frees_them(
    layout: workspace.Layout,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(workspace.SLOTS_ENV, "2")
    workspace.bind(layout, _address("before"))
    workspace.bind(layout, _address("perf-1"))

    with pytest.raises(workspace.WorkspaceError, match="release review/<item>"):
        workspace.bind(layout, _address("before", item="pkg/b.py"))

    released = workspace.release(layout, "pkg/a.py")
    reused = workspace.bind(layout, _address("before", item="pkg/b.py"))

    assert released == ["slot-1 review/pkg/a.py/before", "slot-2 review/pkg/a.py/perf-1"]
    assert (reused.slot, reused.needs_sync) == ("slot-1", True)


def test_bind_refuses_a_new_copy_below_the_free_disk_guard(
    layout: workspace.Layout,
    monkeypatch: pytest.MonkeyPatch,
) -> None:

    def _short_free_bytes(_path: Path) -> int:
        return workspace.MIN_FREE_BYTES - 1

    monkeypatch.setattr(workspace, "_free_bytes", _short_free_bytes)

    with pytest.raises(workspace.WorkspaceError, match="GB free"):
        workspace.bind(layout, _address("perf-1"))


def test_release_of_one_role_keeps_the_item_and_its_other_copies(layout: workspace.Layout) -> None:
    workspace.bind(layout, _address("before"))
    workspace.bind(layout, _address("perf-1"))

    assert workspace.release(layout, "pkg/a.py", roles=["perf-1"]) == [
        "slot-2 review/pkg/a.py/perf-1",
    ]
    assert workspace.bind(layout, _address("before")).slot == "slot-1"


def test_release_keep_frees_a_phase_and_spares_the_pinned_copy(layout: workspace.Layout) -> None:
    workspace.bind(layout, _address("before"))
    workspace.bind(layout, _address("performance"))
    workspace.bind(layout, _address("mechanics"))
    with workspace.file_lock(layout.pool_lock):
        state = workspace._load_state(layout)
        state["items"]["pkg/a.py"] = {"item_baseline": "abc", "at": "t"}
        workspace._write_json(layout.state_path, state)

    released = workspace.release(layout, "pkg/a.py", keep=["before"])

    assert released == ["slot-2 review/pkg/a.py/performance", "slot-3 review/pkg/a.py/mechanics"]
    state = workspace._load_state(layout)
    assert state["slots"]["slot-1"] is not None
    assert state["slots"]["slot-1"]["role"] == "before"
    assert state["items"]["pkg/a.py"]["item_baseline"] == "abc"


def test_release_refuses_while_a_command_runs_in_the_copy(layout: workspace.Layout) -> None:
    binding = workspace.bind(layout, _address("perf-1"))

    with workspace.file_lock(layout.slot_lock(binding.slot)):
        with pytest.raises(workspace.LockBusyError, match="still runs"):
            workspace.release(layout, "pkg/a.py")
    assert workspace.release(layout, "pkg/a.py") == ["slot-1 review/pkg/a.py/perf-1"]


def test_release_of_a_flow_that_never_ran_creates_nothing(layout: workspace.Layout) -> None:
    assert workspace.release(layout, "pkg/a.py") == []
    assert not layout.flow_dir.exists()


# --------------------------------------------------------------------------------------------
# Cleanup
# --------------------------------------------------------------------------------------------


def test_gc_removes_the_flow_folder_and_its_empty_parent(
    layout: workspace.Layout,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(workspace.ROOT_ENV, raising=False)
    binding = workspace.bind(layout, _address("perf-1"))
    _write(binding.directory / "file.txt", "x\n")
    _write(layout.run_log, "{}\n")

    report = workspace.gc(layout)

    assert not layout.flow_dir.exists()
    assert not layout.base.exists()
    assert not layout.base.parent.exists()
    assert report[0].startswith(f"removed {layout.flow_dir}")


def test_gc_keeps_a_root_override_folder(
    layout: workspace.Layout,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(workspace.ROOT_ENV, str(layout.base.parent))
    workspace.bind(layout, _address("perf-1"))

    workspace.gc(layout)

    assert not layout.base.exists()
    assert layout.base.parent.exists()


def test_gc_refuses_a_folder_it_did_not_create(layout: workspace.Layout) -> None:
    _write(layout.flow_dir / "someone-elses.txt", "x\n")

    with pytest.raises(workspace.WorkspaceError, match="marker"):
        workspace.gc(layout)
    assert (layout.flow_dir / "someone-elses.txt").exists()


def test_gc_refuses_while_a_command_runs_unless_forced(layout: workspace.Layout) -> None:
    binding = workspace.bind(layout, _address("perf-1"))

    with workspace.file_lock(layout.slot_lock(binding.slot)):
        with pytest.raises(workspace.LockBusyError, match="slot-1"):
            workspace.gc(layout)
        assert layout.flow_dir.exists()
        workspace.gc(layout, force=True)
    assert not layout.flow_dir.exists()


# --------------------------------------------------------------------------------------------
# Provenance and audit
# --------------------------------------------------------------------------------------------


def _probe(copy: Path, **databases: workspace._ProbeDatabase) -> workspace._ProbeResult:
    return {
        "executable": str(copy / ".venv" / "bin" / "python"),
        "package_file": str(copy / PACKAGE / "__init__.py"),
        "databases": databases,
    }


def _sqlite(name: object) -> workspace._ProbeDatabase:
    return {"ENGINE": "django.db.backends.sqlite3", "NAME": str(name)}


def test_provenance_accepts_the_copys_package_interpreter_and_databases(tmp_path: Path) -> None:
    copy = tmp_path / "slot-1"
    found = _probe(
        copy,
        default=_sqlite(copy / "examples" / "fakeshop" / "db.sqlite3"),
        shard_b=_sqlite(copy / "examples" / "fakeshop" / "db_shard_b.sqlite3"),
    )

    assert workspace.provenance_faults(found, copy, "sharded", None) == []


def test_provenance_refuses_the_shared_package_and_the_tracked_database(
    repo: Path,
    tmp_path: Path,
) -> None:
    copy = tmp_path / "slot-1"
    found = _probe(copy, default=_sqlite(repo / "examples" / "fakeshop" / "db.sqlite3"))
    found["package_file"] = str(repo / PACKAGE / "__init__.py")
    found["executable"] = str(repo / ".venv" / "bin" / "python")

    faults = workspace.provenance_faults(found, copy, "default", None)

    assert len(faults) == 3  # package, interpreter, database
    assert all(str(copy) in fault or ".venv" in fault for fault in faults)


def test_provenance_refuses_a_postgres_database_that_is_not_the_copys(tmp_path: Path) -> None:
    copy = tmp_path / "slot-1"
    postgres: workspace._ProbeDatabase = {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "fakeshop",
    }

    faults = workspace.provenance_faults(
        _probe(copy, default=postgres),
        copy,
        "pg",
        "ws_x_review_slot1",
    )

    assert faults == [
        "alias 'default' opens Postgres 'fakeshop', not 'ws_x_review_slot1'",
        "cell pg did not select 'ws_x_review_slot1' for the default alias",
    ]


def test_audit_binds_cited_run_ids_and_fails_unknown_or_foreign_ones(
    layout: workspace.Layout,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:

    def _layout_base(_root: Path) -> Path:
        return layout.base

    monkeypatch.setattr(workspace, "workspace_base", _layout_base)
    copy = layout.slot_dir("slot-1")
    good = {
        "run_id": "review-20260924T120000-aaaaaa",
        "address": "review/pkg/a.py/perf-1",
        "directory": str(copy),
        "package_file": str(copy / PACKAGE / "__init__.py"),
        "package_digest": "sha256:" + "0" * 64,
        "databases": {"default": str(copy / "examples" / "fakeshop" / "db.sqlite3")},
        "cell": "default",
        "exit": 0,
        "copy_edits": [],
        "shared_moves": ["pkg/a.py"],
    }
    foreign = {
        **good,
        "run_id": "review-20260924T120001-bbbbbb",
        "package_file": str(layout.repo_root / PACKAGE / "__init__.py"),
    }
    _write(layout.run_log, "".join(json.dumps(run) + "\n" for run in (good, foreign)))
    record = _write(
        tmp_path / "rev.md",
        "Proof: review-20260924T120000-aaaaaa, again review-20260924T120000-aaaaaa;\n"
        "review-20260924T120001-bbbbbb and review-20260101T000000-cccccc.\n",
    )

    lines, ok = workspace.audit_record(layout.repo_root, record)

    assert ok is False
    assert lines[0].endswith("3 run id(s) cited")
    assert lines[1].startswith("  ok   review-20260924T120000-aaaaaa")
    assert "shared=moved 1" in lines[1]
    assert lines[2].startswith("  FAIL review-20260924T120001-bbbbbb")
    assert lines[3].startswith("  FAIL review-20260101T000000-cccccc: no run log entry")


# --------------------------------------------------------------------------------------------
# Postgres identity and database matching
# --------------------------------------------------------------------------------------------


def test_postgres_finds_the_fakeshop_container_by_identity_not_port(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    inspect = [
        {
            "Id": "aaaaaaaaaaaa1111",
            "Config": {"Env": ["POSTGRES_USER=medtrics", "POSTGRES_DB=medtrics"], "Labels": {}},
            "NetworkSettings": {"Ports": {"5432/tcp": [{"HostPort": "2345"}]}},
        },
        {
            "Id": "bbbbbbbbbbbb2222",
            "Config": {
                "Env": ["POSTGRES_USER=fakeshop", "POSTGRES_DB=fakeshop"],
                "Labels": {"com.docker.compose.project": workspace.COMPOSE_PROJECT},
            },
            "NetworkSettings": {"Ports": {"5432/tcp": [{"HostPort": "5432"}]}},
        },
    ]
    answers = {"ps": "aaaaaaaaaaaa\nbbbbbbbbbbbb\n", "inspect": json.dumps(inspect)}
    postgres = workspace.Postgres(tmp_path)

    def _answer(*args: str, **_kw: object) -> str:
        return answers[args[0]]

    monkeypatch.setattr(postgres, "_docker", _answer)

    assert postgres.find() == ("bbbbbbbbbbbb", "5432", workspace.COMPOSE_PROJECT)


def test_postgres_exact_match_never_takes_slot10_for_slot1(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    statements: list[str] = []
    postgres = workspace.Postgres(tmp_path)

    def _record_statement(statement: str, database: str = "postgres") -> str:
        statements.append(statement)
        return ""

    monkeypatch.setattr(postgres, "sql", _record_statement)

    postgres.databases("ws_abc_review_slot1", exact=True)

    assert statements == [
        "SELECT datname FROM pg_database WHERE datname IN "
        "('ws_abc_review_slot1', 'test_ws_abc_review_slot1') "
        "OR datname LIKE 'test\\_ws\\_abc\\_review\\_slot1\\_gw%' ORDER BY datname",
    ]


# --------------------------------------------------------------------------------------------
# Gate
# --------------------------------------------------------------------------------------------


def test_gate_copy_git_lists_what_the_shared_tree_lists_and_reports_its_changes(
    repo: Path,
    tmp_path: Path,
) -> None:
    _write(repo / "untracked.py", "NEW = 1\n")
    _write(repo / PACKAGE / "core.py", "CORE = 'dirty'\n")
    gate_dir = tmp_path / "gate"
    workspace.mirror_tree(repo, gate_dir, preserved=workspace.PRESERVED | {".git"})

    head = workspace.build_gate_git(repo, gate_dir)

    assert head == _git(repo, "rev-parse", "HEAD").strip()
    assert _git(gate_dir, "ls-files", "-co", "--exclude-standard") == _git(
        repo,
        "ls-files",
        "-co",
        "--exclude-standard",
    )
    assert _git(gate_dir, "status", "--short") == _git(repo, "status", "--short")


def test_the_lint_gate_suite_runs_the_ci_lint_job_commands_in_order() -> None:
    """``gate``'s lint suite is the ``lint`` job of ``django.yml``, command for command.

    Every ``run:`` line of that job past its setup (``uv python install``,
    ``uv sync``) is a ``uv run`` command, and the suite runs each one without the
    prefix, in the workflow's order; a step added to the workflow and not here
    would let a gate pass that CI fails.
    """
    workflow = workspace.REPO_ROOT / ".github" / "workflows" / "django.yml"
    job = yaml.safe_load(workflow.read_text(encoding="utf-8"))["jobs"]["lint"]
    lines = [
        line.strip()
        for step in job["steps"]
        for line in str(step.get("run", "")).splitlines()
        if line.strip()
    ]
    setup = [line for line in lines if line.startswith("uv python install") or line == "uv sync"]
    commands = [line for line in lines if line not in setup]

    assert len(setup) == 2
    assert all(line.startswith("uv run ") for line in commands)
    assert tuple(line.removeprefix("uv run ") for line in commands) == workspace.LINT_COMMANDS
    arguments, cell = workspace.GATE_SUITES["lint"]
    assert arguments == ("sh", "-exc", "\n".join(workspace.LINT_COMMANDS))
    assert cell == "default"


def _ci_floor_node() -> tuple[dict[str, str], list[str]]:
    """The push/PR compatibility node of ``django.yml``'s ``test`` job and its ``run:`` lines."""
    workflow = workspace.REPO_ROOT / ".github" / "workflows" / "django.yml"
    job = yaml.safe_load(workflow.read_text(encoding="utf-8"))["jobs"]["test"]
    lists = re.findall(r"fromJSON\('(\[.*?\])'\)", job["strategy"]["matrix"]["include"], re.S)
    push_nodes = json.loads(lists[-1])
    floor = [node for node in push_nodes if node.get("compatibility_only") == "1"]
    lines = [
        line.strip()
        for step in job["steps"]
        for line in str(step.get("run", "")).splitlines()
        if line.strip()
    ]
    assert len(floor) == 1
    return floor[0], lines


def test_floor_pins_are_the_pyproject_lower_bounds(tmp_path: Path) -> None:
    pyproject = _write(
        tmp_path / "pyproject.toml",
        "[project]\n"
        'requires-python = ">=3.10,<4.0"\n'
        "dependencies = [\n"
        '    "django>=5.2.16",\n'
        "    \"Strawberry_Graphql[debug] >= 0.322.2, <1 ; python_version >= '3.10'\",\n"
        '    "graphql-core>=3.2.0,<3.3",\n'
        "]\n",
    )

    assert workspace.floor_pins(pyproject) == {
        "python": "3.10",
        "Django": "5.2.16",
        "strawberry-graphql": "0.322.2",
    }


@pytest.mark.parametrize(
    ("dependencies", "match"),
    [
        ('"Django>=5.2.16"', "lists no strawberry-graphql"),
        ('"Django==5.2.16", "strawberry-graphql>=0.322.2"', "states no >= floor"),
    ],
)
def test_floor_pins_refuse_a_pyproject_without_a_floor(
    tmp_path: Path,
    dependencies: str,
    match: str,
) -> None:
    pyproject = _write(
        tmp_path / "pyproject.toml",
        f'[project]\nrequires-python = ">=3.10"\ndependencies = [{dependencies}]\n',
    )

    with pytest.raises(workspace.WorkspaceError, match=match):
        workspace.floor_pins(pyproject)


def test_the_floor_pins_are_the_points_build_md_and_the_ci_floor_cell_state() -> None:
    """``pyproject.toml``'s lower bounds, BUILD.md's floor policy and CI's floor node agree.

    The gate reads its pins from ``pyproject.toml``; BUILD.md "Floor
    verification" records the exact point a floor run installs. Were the policy
    ever to name a point other than the lower bound, this row fails rather than
    the gate silently testing a different floor from CI.
    """
    pins = workspace.floor_pins(workspace.REPO_ROOT / "pyproject.toml")
    build = (workspace.REPO_ROOT / "docs" / "builder" / "BUILD.md").read_text(encoding="utf-8")
    stated = re.search(
        r"The supported floor is Django \*\*([^*]+)\*\* on Python \*\*([^*]+)\*\* "
        r"with strawberry-graphql \*\*([^*]+)\*\*",
        build,
    )
    node, _lines = _ci_floor_node()

    assert stated is not None
    assert stated.groups() == (pins["Django"], pins["python"], pins["strawberry-graphql"])
    assert (node["django"], node["python"], node["strawberry"]) == (
        pins["Django"],
        pins["python"],
        pins["strawberry-graphql"],
    )


def test_the_floor_gate_suite_installs_and_runs_what_the_ci_floor_cell_does(
    tmp_path: Path,
) -> None:
    """The floor suite is the ``test`` job's floor node: its install and its coverage-free run.

    That job syncs the lock at the floor Python, installs Django over it with
    ``--upgrade-package Django``, then strawberry-graphql, and runs pytest with
    ``addopts`` that drop ``--cov``; the suite does each of those against its
    own virtualenv and only adds ``-p no:cacheprovider``.
    """
    _node, lines = _ci_floor_node()
    ci_addopts = re.findall(r'addopts="(-[^"]*)"', "\n".join(lines))
    pins = {"python": "3.10", "Django": "5.2.16", "strawberry-graphql": "0.322.2"}
    venv = tmp_path / "gate-floor"
    python = str(venv / "bin" / "python")

    commands = workspace.floor_install_commands(tmp_path / "gate", venv, pins)

    assert "uv sync --python ${{ matrix.python }}" in lines
    assert 'uv pip install --upgrade-package Django "Django==${{ matrix.django }}"' in lines
    assert 'uv pip install "strawberry-graphql==${{ matrix.strawberry }}"' in lines
    pip = [
        "uv",
        "pip",
        "install",
        "--directory",
        str(tmp_path / "gate"),
        "--python",
        python,
        "-q",
    ]
    assert commands == [
        [
            "uv",
            "sync",
            "--directory",
            str(tmp_path / "gate"),
            "--frozen",
            "--python",
            "3.10",
            "-q",
        ],
        [
            *pip,
            "--upgrade-package",
            "Django",
            "Django==5.2.16",
        ],
        [*pip, "strawberry-graphql==0.322.2"],
    ]
    arguments, cell = workspace.GATE_SUITES[workspace.FLOOR_SUITE]
    no_cov = [opts for opts in ci_addopts if "--cov" not in opts]
    assert len(no_cov) == 1
    assert arguments == (
        "pytest",
        "-p",
        "no:cacheprovider",
        "-o",
        f"addopts={no_cov[0]}",
    )
    assert cell == "default"
    assert list(workspace.GATE_SUITES)[:3] == ["lint", "default", "floor"]


def _gate_copy_inputs(layout: workspace.Layout, lock: str = "lock v1\n") -> None:
    _write(
        layout.gate_dir / "pyproject.toml",
        '[project]\nrequires-python = ">=3.10"\n'
        'dependencies = ["Django>=5.2.16", "strawberry-graphql>=0.322.2"]\n',
    )
    _write(layout.gate_dir / "uv.lock", lock)


def _record_installs(
    monkeypatch: pytest.MonkeyPatch,
    layout: workspace.Layout,
    fail_on: str | None = None,
) -> list[tuple[list[str], dict[str, str]]]:
    """Replace the build commands' subprocess layer; ``uv sync`` lays down the interpreter."""
    calls: list[tuple[list[str], dict[str, str]]] = []

    def _run_checked(command: list[str], env: dict[str, str]) -> None:
        calls.append((list(command), env))
        if fail_on is not None and fail_on in command:
            msg = f"{' '.join(command)} failed (1): no such release"
            raise workspace.WorkspaceError(msg)
        if command[:2] == ["uv", "sync"]:
            _write(layout.floor_venv / "bin" / "python", "interpreter\n")

    monkeypatch.setattr(workspace, "_run_checked", _run_checked)
    return calls


def test_the_floor_venv_is_built_once_and_rebuilt_when_its_inputs_move(
    layout: workspace.Layout,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _gate_copy_inputs(layout)
    calls = _record_installs(monkeypatch, layout)

    built = workspace.ensure_floor_venv(layout)
    _write(layout.floor_venv / "lib" / "leftover.py", "x\n")
    reused = workspace.ensure_floor_venv(layout)

    assert built["reused"] is False
    assert built["pins"] == {"python": "3.10", "Django": "5.2.16", "strawberry-graphql": "0.322.2"}
    assert built["python"] == str(layout.floor_venv / "bin" / "python")
    assert [command[:3] for command, _env in calls] == [
        ["uv", "sync", "--directory"],
        ["uv", "pip", "install"],
        ["uv", "pip", "install"],
    ]
    assert all(env["UV_PROJECT_ENVIRONMENT"] == str(layout.floor_venv) for _c, env in calls)
    assert reused == {**built, "reused": True}
    assert len(calls) == 3

    _gate_copy_inputs(layout, lock="lock v2\n")
    rebuilt = workspace.ensure_floor_venv(layout)

    assert rebuilt["reused"] is False
    assert rebuilt["key"] != built["key"]
    assert len(calls) == 6
    assert not (layout.floor_venv / "lib" / "leftover.py").exists()


def test_a_floor_pin_move_rebuilds_the_floor_venv(
    layout: workspace.Layout,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _gate_copy_inputs(layout)
    calls = _record_installs(monkeypatch, layout)
    built = workspace.ensure_floor_venv(layout)
    _write(
        layout.gate_dir / "pyproject.toml",
        '[project]\nrequires-python = ">=3.10"\n'
        'dependencies = ["Django>=5.2.17", "strawberry-graphql>=0.322.2"]\n',
    )

    rebuilt = workspace.ensure_floor_venv(layout)

    assert rebuilt["key"] != built["key"]
    assert calls[-2][0][-1] == "Django==5.2.17"


def test_a_failed_floor_build_writes_no_key_so_the_next_gate_rebuilds(
    layout: workspace.Layout,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _gate_copy_inputs(layout)
    _record_installs(monkeypatch, layout, fail_on="strawberry-graphql==0.322.2")

    with pytest.raises(workspace.WorkspaceError, match="no such release"):
        workspace.ensure_floor_venv(layout)
    assert (layout.floor_venv / "bin" / "python").exists()
    assert not (layout.floor_venv / workspace.FLOOR_KEY_NAME).exists()

    calls = _record_installs(monkeypatch, layout)
    again = workspace.ensure_floor_venv(layout)

    assert again["reused"] is False
    assert len(calls) == 3


def test_summarize_suite_reads_summary_collected_and_coverage() -> None:
    log = (
        "12 workers [3456 items]\n"
        "TOTAL                         9000      0   100%\n"
        "Required test coverage of 100% reached. Total coverage: 100.00%\n"
        "===== 3450 passed, 6 skipped in 88.12s (0:01:28) =====\n"
    )

    assert workspace.summarize_suite(log) == {
        "summary": "3450 passed, 6 skipped in 88.12s (0:01:28)",
        "collected": 3456,
        "coverage": [
            "TOTAL                         9000      0   100%",
            "Required test coverage of 100% reached. Total coverage: 100.00%",
        ],
    }


# --------------------------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------------------------


def test_run_refuses_a_uv_command_with_the_refusal_exit_code(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert (
        workspace.main(
            [
                "run",
                "review/pkg/a.py/perf-1",
                "--cell",
                "pg",
                "--",
                "uv",
                "run",
                "x",
            ],
        )
        == 125
    )

    assert "follows `uv run`" in capsys.readouterr().err


def test_run_refuses_a_missing_command() -> None:
    assert workspace.main(["run", "review/pkg/a.py/perf-1"]) == workspace.REFUSED


def test_only_run_and_prove_take_a_command_after_the_separator() -> None:
    with pytest.raises(SystemExit):
        workspace.main(
            [
                "baseline",
                "review/pkg/a.py",
                "--",
                "x",
            ],
        )
