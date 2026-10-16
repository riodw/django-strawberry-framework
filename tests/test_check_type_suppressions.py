"""Script tests for the ``check-type-suppressions`` gate in ``scripts/check_type_suppressions.py``.

Pins what the gate refuses (a ``# pyright: ignore[...]`` naming a locked rule, alone or
beside other rules or after another comment, and every file-level ``# pyright:``
directive), what it leaves alone (an unlocked rule's ignore, a bare ignore, which
basedpyright's own ``reportIgnoreCommentWithoutRule`` refuses, and comment text quoted
in a string or docstring), the exit codes, and that the tree itself passes. The script
inspects source files, not a GraphQL request, so there is no live sibling in
``examples/fakeshop/test_query/``.
"""

from pathlib import Path

import pytest

from scripts import check_type_suppressions as cts


def _messages(source: str) -> list[tuple[int, str]]:
    return [(v.line, v.message) for v in cts.comment_violations("probe.py", source)]


@pytest.mark.parametrize(
    "line",
    [
        "x = f()  # pyright: ignore[reportUnusedVariable]",
        "x = f()  # pyright: ignore[reportArgumentType, reportUnusedVariable]",
        "x = f()  # noqa: F841  # pyright: ignore[reportUnusedVariable]",
        "x = f()  #pyright:ignore[ reportUnusedVariable ]",
    ],
)
def test_an_ignore_naming_a_locked_rule_is_refused(line: str) -> None:
    """The locked rule is reported on the comment's line, whatever else the comment names."""
    assert _messages(f"import os\n{line}\n") == [
        (2, "`reportUnusedVariable` is locked: fix the diagnostic, never suppress it"),
    ]


@pytest.mark.parametrize(
    "directive",
    [
        "basic",
        "standard",
        "reportAttributeAccessIssue=false",
        "strict",
    ],
)
def test_every_file_level_directive_is_refused(directive: str) -> None:
    """pyproject.toml owns rule levels; no file may raise or lower one by comment."""
    assert _messages(f"# pyright: {directive}\nx = 1\n") == [
        (1, f"file-level `# pyright: {directive}` directive (pyproject.toml owns rule levels)"),
    ]


@pytest.mark.parametrize(
    "source",
    [
        "x = f()  # pyright: ignore[reportArgumentType]\n",
        "x = f()  # pyright: ignore\n",
        's = "# pyright: basic"\n',
        '"""Quote ``# pyright: ignore[reportUnusedVariable]`` in prose."""\n',
        "# basedpyright: the reason line above a suppression\n",
    ],
)
def test_what_the_gate_leaves_alone(source: str) -> None:
    """An unlocked rule's ignore, a bare ignore, and quoted comment text are not violations."""
    assert _messages(source) == []


def test_main_exits_one_and_lists_each_violation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A violating file fails the run with its ``path:line`` and the summary line."""
    monkeypatch.setattr(cts, "REPO_ROOT", tmp_path)
    _ = (tmp_path / "bad.py").write_text("x = 1  # pyright: ignore[reportRedeclaration]\n")
    _ = (tmp_path / "good.py").write_text("x = 1\n")

    assert cts.main(["bad.py", "good.py", "notes.md"]) == 1
    assert capsys.readouterr().out.splitlines() == [
        "bad.py:1: `reportRedeclaration` is locked: fix the diagnostic, never suppress it",
        "type-suppressions: checked 2 file(s); violations 1",
    ]


def test_main_exits_two_when_a_file_cannot_be_read(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A missing or untokenizable file is a measurement failure, not a pass."""
    monkeypatch.setattr(cts, "REPO_ROOT", tmp_path)

    assert cts.main(["missing.py"]) == 2


def test_the_tracked_tree_has_no_locked_suppression() -> None:
    """Every git-tracked ``.py`` file passes, as the CI lint step requires."""
    assert cts.main([]) == 0
