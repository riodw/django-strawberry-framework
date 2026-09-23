"""Script tests for the ``source-layout`` gate in ``scripts/check_trailing_commas.py``.

Pins the anchored exclusion set (per-cycle docs/ artifacts and scratch subtrees
stay out; the standing docs beside them, tracked ``.py`` under ``docs/`` and a
same-named directory outside ``docs/`` are checked), the always-printed summary
line, the failure on a named path that contributes nothing, the ``--json``
document shape, the no-write guarantee of ``--diff``, and one positive plus one
negative control for the comma-layout and markdown-scaffold rules. Every case
runs against a throwaway tree under ``tmp_path`` with ``REPO_ROOT`` pointed at
it. The script inspects source files, not a GraphQL request, so there is no live
sibling in ``examples/fakeshop/test_query/``.
"""

import json
from pathlib import Path

import pytest

from scripts import check_trailing_commas as ctc

SCAFFOLD = "\n".join([ctc.LINK_DEF_HEADER, "", *ctc.LINK_DEF_CATEGORIES]) + "\n"
CLEAN_MD = "# Title\n\nBody.\n\n" + SCAFFOLD
CLEAN_PY = "VALUE = [1, 2]\n"


@pytest.fixture
def repo(tmp_path, monkeypatch):
    """A throwaway repo root with its own pyproject, git filter disabled, cwd inside it."""
    (tmp_path / "pyproject.toml").write_text("[tool.ruff]\nline-length = 99\n", encoding="utf-8")
    monkeypatch.setattr(ctc, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(ctc, "git_visible_scope", lambda: None)
    monkeypatch.chdir(tmp_path)
    ctc.line_length.cache_clear()
    yield tmp_path
    ctc.line_length.cache_clear()


def _write(root: Path, relative: str, text: str) -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _summary(stdout: str) -> str:
    return stdout.strip().splitlines()[-1]


EXCLUDED = (
    "docs/review/rev-optimizer__walker.mechanics.md",
    "docs/review/review-0_0_15.md",
    "docs/dry/dry-0_0_15.md",
    "docs/dry/dry-file-walker.md",
    "docs/builder/bld-final.md",
    "docs/builder/build-050-thing-0_0_15.md",
    "docs/bug_hunt/bug_hunt-0_0_15.md",
    "docs/review/temp-tests/test_probe.py",
    "docs/builder/temp-tests/nested/test_probe.py",
    "docs/dry/worker-memory/worker-1.md",
    "docs/shadow/current/walker.py",
    "docs/shadow/diff/walker.md",
    "docs/feedback.md",
)
CHECKED = (
    "docs/review/REVIEW.md",
    "docs/review/worker-0.md",
    "docs/dry/DRY.md",
    "docs/dry/export_dry_review.py",
    "docs/bug_hunt/HUNT.md",
    "docs/bug_hunt/dicta.md",
    "docs/builder/BUILD.md",
    "docs/builder/worker-3.md",
    "docs/README.md",
    # A per-cycle NAME outside its anchored subtree is ordinary source.
    "tests/review/rev-notes.md",
    "django_strawberry_framework/builder/review-helpers.py",
    "examples/fakeshop/apps/dry/dry-run.py",
    # ``*`` never crosses ``/``: a directory named like an artifact is not one.
    "docs/review/rev-cycle/notes.md",
)


@pytest.mark.parametrize("relative", EXCLUDED)
def test_per_cycle_artifact_is_excluded(repo, relative):
    """Per-cycle artifacts and scratch subtrees under docs/ are excluded by anchored path."""
    assert ctc.is_excluded(_write(repo, relative, "x\n"))


@pytest.mark.parametrize("relative", CHECKED)
def test_standing_doc_and_same_named_source_are_checked(repo, relative):
    """Standing docs, tracked docs/ .py and same-named dirs elsewhere stay in the gate."""
    assert not ctc.is_excluded(_write(repo, relative, "x\n"))


def test_walk_partitions_checked_and_excluded(repo):
    """A tree walk processes exactly CHECKED and counts exactly EXCLUDED."""
    for relative in (*EXCLUDED, *CHECKED):
        _write(repo, relative, "x\n")
    selection = ctc.select_files(["."], ctc.SUFFIXES)
    assert {path.as_posix() for path in selection.files} == set(CHECKED)
    assert {path.as_posix() for path in selection.excluded} == set(EXCLUDED)
    assert selection.skipped == []
    assert selection.unmatched == []


def test_named_excluded_file_is_reported_not_checked(repo, capsys):
    """A per-cycle artifact handed in by name prints the excluded line and is counted."""
    _write(repo, "docs/review/review-0_0_15.md", "no footer\n")
    assert ctc.main(["--check", "docs/review/review-0_0_15.md"]) == 0
    captured = capsys.readouterr()
    assert "docs/review/review-0_0_15.md: excluded from the source-layout rules" in captured.err
    assert _summary(captured.out).startswith("source-layout: checked 0 file(s); excluded 1;")


def test_summary_counts_checked_excluded_and_violations(repo, capsys):
    """The summary line is printed on every run and counts each population."""
    _write(repo, "pkg/clean.py", CLEAN_PY)
    _write(repo, "pkg/wide.py", "def f(a, b, c, d):\n    return a\n")
    _write(repo, "docs/guide.md", CLEAN_MD)
    _write(repo, "docs/review/rev-scratch.md", "no footer\n")
    assert ctc.main(["--check", "."]) == 1
    assert _summary(capsys.readouterr().out) == (
        "source-layout: checked 3 file(s); excluded 1; ignored 0; "
        "violations 1 (layout 1, non-ASCII 0); errors 0"
    )


def test_clean_run_still_prints_summary(repo, capsys):
    """Negative control: a clean run exits 0 and still states its population."""
    _write(repo, "pkg/clean.py", CLEAN_PY)
    assert ctc.main(["--check", "pkg/clean.py"]) == 0
    assert _summary(capsys.readouterr().out) == (
        "source-layout: checked 1 file(s); excluded 0; ignored 0; "
        "violations 0 (layout 0, non-ASCII 0); errors 0"
    )


@pytest.mark.parametrize(
    ("setup", "argument", "reason"),
    [
        (None, "missing.md", "matches nothing"),
        (None, "missing_dir", "matches nothing"),
        ("empty_dir/.keep", "empty_dir", "directory yielded no checkable file (0 excluded)"),
        ("docs/shadow/a.py", "docs/shadow", "directory yielded no checkable file (1 excluded)"),
    ],
)
def test_path_contributing_nothing_fails(
    repo,
    capsys,
    setup,
    argument,
    reason,
):
    """A named path that yields no file is an error under --check, not a silent pass."""
    if setup is not None:
        _write(repo, setup, "x\n")
    assert ctc.main(["--check", argument]) == 1
    captured = capsys.readouterr()
    assert f"{argument}: {reason} -- NOT checked" in captured.err
    assert _summary(captured.out).endswith("errors 1")


def test_unsupported_suffix_is_ignored_not_failed(repo, capsys):
    """An existing file no rule covers is reported as ignored and does not fail the run."""
    assert ctc.main(["--check", "pyproject.toml"]) == 0
    captured = capsys.readouterr()
    assert "pyproject.toml: no source-layout rule covers this suffix -- ignored" in captured.err
    assert "ignored 1;" in _summary(captured.out)


def test_json_document_shape(repo, capsys):
    """--json prints one document: summary, path lists and uniform per-violation records."""
    _write(repo, "pkg/wide.py", f"def f(a, b, c, d):\n    return 'caf{chr(0xE9)}'\n")
    _write(repo, "docs/guide.md", "# Guide\n")
    _write(repo, "docs/dry/dry-0_0_15.md", "no footer\n")
    argv = [
        "--check",
        "--json",
        "pkg",
        "docs",
        "missing.md",
    ]
    assert ctc.main(argv) == 1
    document = json.loads(capsys.readouterr().out)
    assert set(document) == {
        "mode",
        "paths",
        "summary",
        "checked",
        "excluded",
        "ignored",
        "violations",
        "errors",
    }
    assert document["mode"] == "check"
    assert document["paths"] == argv[2:]
    assert document["summary"] == {
        "checked": 2,
        "excluded": 1,
        "ignored": 0,
        "violations": 3,
        "errors": 1,
        "fixed": 0,
        "exit": 1,
    }
    assert document["excluded"] == ["docs/dry/dry-0_0_15.md"]
    keys = {
        "file",
        "line",
        "rule",
        "message",
        "fixable",
    }
    assert all(set(record) == keys for record in document["violations"] + document["errors"])
    by_rule = {(v["file"], v["rule"]): (v["line"], v["fixable"]) for v in document["violations"]}
    assert by_rule == {
        ("docs/guide.md", "md-scaffold"): (2, True),
        ("pkg/wide.py", "explode"): (1, True),
        ("pkg/wide.py", "non-ascii"): (2, False),
    }
    assert [(e["file"], e["rule"]) for e in document["errors"]] == [
        ("missing.md", "unmatched-path"),
    ]


def test_diff_prints_fix_without_writing(repo, capsys):
    """--diff shows the rewrite --fix would make and leaves the file byte-identical."""
    path = _write(repo, "docs/guide.md", "# Guide\n")
    before = path.read_bytes()
    assert ctc.main(["--diff", "docs/guide.md"]) == 1
    out = capsys.readouterr().out
    assert path.read_bytes() == before
    assert "--- a/docs/guide.md" in out
    assert f"+{ctc.LINK_DEF_HEADER}" in out
    assert f"+{ctc.LINK_DEF_CATEGORIES[-1]}" in out


def test_diff_rejects_fix(repo):
    """--diff writes nothing, so pairing it with --fix is a usage error."""
    with pytest.raises(SystemExit):
        ctc.main(["--fix", "--diff", "."])


def test_fix_writes_what_diff_showed(repo, capsys):
    """Positive control for --diff: --fix on the same file does write the scaffold."""
    path = _write(repo, "docs/guide.md", "# Guide\n")
    assert ctc.main(["--fix", "docs/guide.md"]) == 0
    written = path.read_text(encoding="utf-8")
    assert written.startswith(f"# Guide\n\n{ctc.LINK_DEF_HEADER}\n")
    assert ctc._scaffold_in_canonical_order(written) is None
    assert "Fixed 1 file(s)." in capsys.readouterr().out


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("def f(a, b, c, d):\n    return a\n", [(1, "explode")]),
        ("def f(a, b, c):\n    return a\n", []),
    ],
)
def test_comma_layout_threshold(repo, source, expected):
    """A single-line four-parameter def must explode; three parameters stay inline."""
    assert ctc._analyze(source, ctc.threshold_for(Path("pkg/mod.py")))[2] == expected


@pytest.mark.parametrize(
    ("text", "missing"),
    [
        ("# Guide\n", ctc.LINK_DEF_HEADER),
        ("# Guide\n\n" + SCAFFOLD.replace("<!-- tests/ -->\n", ""), "<!-- tests/ -->"),
        (CLEAN_MD, None),
    ],
)
def test_markdown_scaffold(repo, text, missing):
    """The first missing scaffold marker is reported; the canonical footer passes."""
    assert ctc._scaffold_in_canonical_order(text) == missing
