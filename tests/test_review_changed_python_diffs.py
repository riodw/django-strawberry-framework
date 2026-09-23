"""Repo-tooling tests for the commit-vs-HEAD stripped diff helper.

Keeps the CLI, git-inventory and output-location contracts of
``scripts/review_changed_python_diffs_against_head.py``: which side is read
from where, how renames pair, what ``--list`` prints and what ``--prose``
captures. Every row builds a throwaway git repository under ``tmp_path`` and
runs the script from inside it, so the shared checkout's ``docs/shadow/`` is
never written. A live ``/graphql/`` request has no wire shape for git listings
or generated diff files, so none of these rows can move; there is no live
sibling in ``examples/fakeshop/test_query/``.
"""

import json
import subprocess
from pathlib import Path

import pytest

from scripts import review_changed_python_diffs_against_head as diffs


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        [
            "git",
            "-c",
            "commit.gpgsign=false",
            "-c",
            "tag.gpgsign=false",
            "-c",
            "core.hooksPath=/dev/null",
            *args,
        ],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _write(repo: Path, path: str, content: str) -> None:
    target = repo / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def _commit(repo: Path, message: str) -> str:
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", message)
    return _git(repo, "rev-parse", "HEAD")


@pytest.fixture
def repo(tmp_path: Path, monkeypatch) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    for key, value in {
        "GIT_AUTHOR_NAME": "Test",
        "GIT_AUTHOR_EMAIL": "test@example.com",
        "GIT_COMMITTER_NAME": "Test",
        "GIT_COMMITTER_EMAIL": "test@example.com",
    }.items():
        monkeypatch.setenv(key, value)
    _git(root, "init", "-q", "-b", "main")
    monkeypatch.chdir(root)
    return root


BASE_MODULE = '''"""Module docstring."""


def load(queryset):
    """Load related rows."""
    # Follow the author relation.
    return queryset.select_related("author")
'''


def test_module_imports_as_scripts_package_member() -> None:
    assert callable(diffs.main)
    assert Path("docs/shadow/diff") == diffs.OUTPUT_DIFF


def test_output_dir_receives_all_three_folders_and_docs_shadow_is_untouched(
    repo: Path,
    tmp_path: Path,
) -> None:
    _write(repo, "pkg/mod.py", BASE_MODULE)
    base = _commit(repo, "base")
    _write(repo, "pkg/mod.py", BASE_MODULE + "\n\nVALUE = 1\n")
    _commit(repo, "edit")
    out = tmp_path / "out"

    assert diffs.main([base, "--output-dir", str(out)]) == 0

    assert sorted(entry.name for entry in out.iterdir()) == ["diff", "new", "old"]
    diff_text = (out / "diff" / "pkg__mod.diff").read_text()
    assert "+VALUE = 1\n" in diff_text
    assert "--- old/pkg__mod.stripped.py" in diff_text
    assert (out / "old" / "pkg__mod.stripped.py").is_file()
    assert (out / "new" / "pkg__mod.overview.md").is_file()
    assert not (repo / "docs").exists()


def test_new_side_is_head_by_default_and_working_tree_only_when_asked(
    repo: Path,
    tmp_path: Path,
) -> None:
    _write(repo, "pkg/mod.py", BASE_MODULE)
    base = _commit(repo, "base")
    _write(repo, "pkg/mod.py", BASE_MODULE + "\n\nCOMMITTED = 1\n")
    _commit(repo, "edit")
    _write(repo, "pkg/mod.py", BASE_MODULE + "\n\nCOMMITTED = 1\nDIRTY = 2\n")
    _write(repo, "pkg/untracked.py", "UNTRACKED = 3\n")

    assert diffs.main([base, "--output-dir", str(tmp_path / "head")]) == 0
    assert (
        diffs.main(
            [
                base,
                "--against",
                "worktree",
                "--output-dir",
                str(tmp_path / "wt"),
            ],
        )
        == 0
    )

    head_diff = (tmp_path / "head" / "diff" / "pkg__mod.diff").read_text()
    assert "+COMMITTED = 1\n" in head_diff
    assert "DIRTY" not in head_diff
    assert not head_diff.startswith("#")
    assert not (tmp_path / "head" / "diff" / "pkg__untracked.diff").exists()

    worktree_diff = (tmp_path / "wt" / "diff" / "pkg__mod.diff").read_text()
    assert worktree_diff.startswith(diffs.WORKTREE_HEADER)
    assert "+DIRTY = 2\n" in worktree_diff
    assert "+UNTRACKED = 3\n" in (tmp_path / "wt" / "diff" / "pkg__untracked.diff").read_text()


def test_rename_reads_old_side_from_the_pre_rename_path(repo: Path, tmp_path: Path) -> None:
    _write(repo, "pkg/before.py", BASE_MODULE)
    base = _commit(repo, "base")
    _git(repo, "mv", "pkg/before.py", "pkg/after.py")
    _write(repo, "pkg/after.py", BASE_MODULE.replace('"author"', '"editor"'))
    _commit(repo, "rename")

    changes = diffs._changed_python_files(base)
    assert changes == [diffs._Change("R", "pkg/after.py", "pkg/before.py")]

    out = tmp_path / "out"
    assert (
        diffs.main(
            [
                base,
                "--output-dir",
                str(out),
                "--keep-literals",
            ],
        )
        == 0
    )
    diff_text = (out / "diff" / "pkg__after.diff").read_text()
    assert "--- old/pkg__before.stripped.py" in diff_text
    assert '-    return queryset.select_related("author")\n' in diff_text
    assert '+    return queryset.select_related("editor")\n' in diff_text
    assert "\n+def load" not in diff_text
    assert "\n def load(queryset):\n" in diff_text


def test_include_flags_admit_init_and_test_paths(repo: Path) -> None:
    _write(repo, "pkg/__init__.py", "")
    _write(repo, "pkg/testing/client.py", "")
    base = _commit(repo, "base")
    _write(repo, "pkg/__init__.py", "__all__ = ()\n")
    _write(repo, "pkg/testing/client.py", "CLIENT = 1\n")
    _commit(repo, "edit")

    assert diffs._changed_python_files(base) == []
    included = diffs._changed_python_files(base, include_tests=True, include_init=True)
    assert [change.path for change in included] == ["pkg/__init__.py", "pkg/testing/client.py"]


def test_list_json_reports_changes_head_blobs_and_dirty_group(repo: Path, capsys) -> None:
    _write(repo, "pkg/mod.py", BASE_MODULE)
    _write(repo, "pkg/gone.py", "GONE = 1\n")
    _commit(repo, "base")
    _git(repo, "tag", "v1")
    _write(repo, "pkg/mod.py", BASE_MODULE + "\nEDIT = 1\n")
    _write(repo, "pkg/added.py", "ADDED = 1\n")
    (repo / "pkg" / "gone.py").unlink()
    head = _commit(repo, "edit")
    _write(repo, "pkg/added.py", "ADDED = 2\n")
    _write(repo, "pkg/new.py", "NEW = 1\n")

    assert diffs.main(["--list", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)

    assert payload["base"] == "v1"
    assert payload["head"] == head
    assert payload["changed"] == [
        {
            "status": "A",
            "path": "pkg/added.py",
            "old_path": None,
            "head_blob": _git(repo, "rev-parse", "HEAD:pkg/added.py"),
        },
        {
            "status": "D",
            "path": "pkg/gone.py",
            "old_path": None,
            "head_blob": None,
        },
        {
            "status": "M",
            "path": "pkg/mod.py",
            "old_path": None,
            "head_blob": _git(repo, "rev-parse", "HEAD:pkg/mod.py"),
        },
    ]
    dirty = {row["path"]: row for row in payload["dirty"]}
    assert set(dirty) == {"pkg/added.py", "pkg/new.py"}
    assert dirty["pkg/added.py"]["status"] == " M"
    assert dirty["pkg/added.py"]["worktree_blob"] == _git(repo, "hash-object", "pkg/added.py")
    assert dirty["pkg/new.py"]["status"] == "??"
    assert dirty["pkg/new.py"]["head_blob"] is None
    assert not (repo / "docs").exists()


def test_prose_captures_a_docstring_only_change_and_skips_code_changes(
    repo: Path,
    tmp_path: Path,
) -> None:
    _write(repo, "pkg/mod.py", BASE_MODULE)
    base = _commit(repo, "base")
    edited = BASE_MODULE.replace("Load related rows.", "Load the author row.").replace(
        '"author"',
        '"editor"',
    )
    _write(repo, "pkg/mod.py", edited)
    _commit(repo, "edit")
    out = tmp_path / "out"

    args = [
        base,
        "--output-dir",
        str(out),
        "--prose",
        "--collapse-blank",
        "--keep-literals",
    ]
    assert diffs.main(args) == 0

    prose = (out / "diff" / "pkg__mod.prose.diff").read_text()
    assert "@@ -5,1 +5,1 @@ pkg/mod.py::load\n" in prose
    assert '-    """Load related rows."""\n' in prose
    assert '+    """Load the author row."""\n' in prose
    assert "editor" not in prose
    code = (out / "diff" / "pkg__mod.diff").read_text()
    assert '+    return queryset.select_related("editor")\n' in code
    assert "Load" not in code
    assert "\n+\n" not in code
