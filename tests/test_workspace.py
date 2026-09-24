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
import subprocess
from pathlib import Path

import pytest

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
    monkeypatch.setattr(workspace, "_running_postgres", lambda _root: None)
    monkeypatch.setattr(workspace, "_free_bytes", lambda _path: workspace.MIN_FREE_BYTES * 2)
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


def test_copy_edits_reports_changes_additions_and_deletions_but_not_caches(
    repo: Path,
    tmp_path: Path,
) -> None:
    copy = tmp_path / "copy"
    manifest = {"entries": workspace.mirror_tree(repo, copy)}
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
    manifest = {"entries": workspace.mirror_tree(repo, tmp_path / "copy")}
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
        {"synced_at": "t", "tree_digest": "d", "package_digest": "p"},
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
    monkeypatch.setattr(workspace, "_free_bytes", lambda _path: workspace.MIN_FREE_BYTES - 1)

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


def _probe(copy: Path, **databases: dict) -> dict:
    return {
        "executable": str(copy / ".venv" / "bin" / "python"),
        "package_file": str(copy / PACKAGE / "__init__.py"),
        "databases": databases,
    }


def _sqlite(name: object) -> dict:
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
    postgres = {"ENGINE": "django.db.backends.postgresql", "NAME": "fakeshop"}

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
    monkeypatch.setattr(workspace, "workspace_base", lambda _root: layout.base)
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
    monkeypatch.setattr(postgres, "_docker", lambda *args, **_kw: answers[args[0]])

    assert postgres.find() == ("bbbbbbbbbbbb", "5432", workspace.COMPOSE_PROJECT)


def test_postgres_exact_match_never_takes_slot10_for_slot1(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    statements: list[str] = []
    postgres = workspace.Postgres(tmp_path)
    monkeypatch.setattr(
        postgres,
        "sql",
        lambda statement, database="postgres": statements.append(statement) or "",
    )

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
    capsys: pytest.CaptureFixture,
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
