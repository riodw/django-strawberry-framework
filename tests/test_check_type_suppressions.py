"""Script tests for the ``check-type-suppressions`` gate in ``scripts/check_type_suppressions.py``.

Pins what the gate refuses (an ignore comment naming a locked rule, alone or beside other
rules or after another comment; every file-level ``pyright:`` directive; an ignore or
``typing.cast`` count off its budget either way), what it leaves alone (an unlocked rule's
ignore, a bare ignore, which basedpyright's own ``reportIgnoreCommentWithoutRule`` refuses,
comment text quoted in a string or docstring, a ``cast`` that is not ``typing``'s), how
``pyproject.toml`` is read, the exit codes, and that the tree itself passes. The script
inspects source files, not a GraphQL request, so there is no live sibling in
``examples/fakeshop/test_query/``.
"""

import re
from pathlib import Path

import pytest

from scripts import check_type_suppressions as cts

_LOCKED = frozenset({"reportUnusedVariable", "reportRedeclaration"})

_PYPROJECT = """\
[tool.other]
reportOutside = "error"  # Locked

[tool.basedpyright]
reportRedeclaration = "error"  # Locked
reportAny = "none"

[[tool.basedpyright.executionEnvironments]]
reportAfter = "error"  # Locked

[tool.type-suppressions]
cast = 1

[tool.type-suppressions.ignores]
reportArgumentType = 2
"""


_FIX = "fix the new diagnostic instead of suppressing it"


def _messages(source: str) -> list[tuple[int, str]]:
    return [(v.line, v.message) for v in cts.comment_violations("probe.py", source, _LOCKED)]


def _budget(**ignores: int) -> cts.Budget:
    return cts.Budget(_LOCKED, ignores, casts=2, line=9)


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
def test_what_the_comment_check_leaves_alone(source: str) -> None:
    """An unlocked rule's ignore, a bare ignore, and quoted comment text are not violations."""
    assert _messages(source) == []


def test_ignored_rules_names_each_rule_once_per_comment() -> None:
    """A comment naming two rules counts once for each; a bare ignore and a string count none."""
    source = (
        "a = f()  # pyright: ignore[reportArgumentType, reportCallIssue]\n"
        "b = f()  # noqa: F841  # pyright: ignore[reportArgumentType]\n"
        "c = f()  # pyright: ignore\n"
        's = "# pyright: ignore[reportCallIssue]"\n'
    )

    assert list(cts.ignored_rules(source)) == [
        (1, "reportArgumentType"),
        (1, "reportCallIssue"),
        (2, "reportArgumentType"),
    ]


def test_cast_calls_counts_typing_cast_under_every_alias() -> None:
    """``typing.cast`` counts however it is imported; a same-named function of another module does not."""
    source = (
        "import typing\n"
        "import typing_extensions as te\n"
        "from typing import cast\n"
        "from typing_extensions import cast as widen\n"
        "from mylib import cast as other\n"
        "a = cast(int, x)\n"
        "b = typing.cast(int, x)\n"
        "c = te.cast(int, x)\n"
        "d = widen(int, x)\n"
        "e = other(int, x)\n"
        "f = mylib.cast(int, x)\n"
    )

    assert cts.cast_calls(source) == 4


@pytest.mark.parametrize(
    ("ignores", "casts", "expected"),
    [
        ({"reportArgumentType": 2}, 2, []),
        (
            {"reportArgumentType": 3},
            2,
            [f"`reportArgumentType` ignore comments: 3, budget 2: {_FIX}"],
        ),
        (
            {"reportArgumentType": 1},
            2,
            ["`reportArgumentType` ignore comments: 1, budget 2: lower the budget to 1"],
        ),
        ({}, 2, ["`reportArgumentType` ignore comments: 0, budget 2: drop it from the budget"]),
        (
            {"reportArgumentType": 2, "reportCallIssue": 1},
            2,
            [f"`reportCallIssue` ignore comments: 1, budget 0: {_FIX}"],
        ),
        ({"reportArgumentType": 2, "reportUnusedVariable": 4}, 2, []),
        ({"reportArgumentType": 2}, 3, [f"`typing.cast` calls: 3, budget 2: {_FIX}"]),
        (
            {"reportArgumentType": 2},
            1,
            ["`typing.cast` calls: 1, budget 2: lower the budget to 1"],
        ),
    ],
    ids=[
        "even",
        "over",
        "under",
        "cleared",
        "unbudgeted",
        "locked-skipped",
        "casts-over",
        "casts-under",
    ],
)
def test_budget_violations_hold_every_count_to_its_budget(
    ignores: dict[str, int],
    casts: int,
    expected: list[str],
) -> None:
    """Over and under both fail; an unlisted rule's budget is zero; a locked rule is left to the sites."""
    violations = list(cts.budget_violations(ignores, casts, _budget(reportArgumentType=2)))

    assert [v.message for v in violations] == expected
    assert {(v.path, v.line) for v in violations} <= {("pyproject.toml", 9)}


def test_load_budget_reads_the_marked_lines_and_the_table(tmp_path: Path) -> None:
    """Only ``# Locked`` lines inside ``[tool.basedpyright]`` lock a rule; the table sets the counts."""
    pyproject = tmp_path / "pyproject.toml"
    _ = pyproject.write_text(_PYPROJECT)

    assert cts.load_budget(pyproject) == cts.Budget(
        frozenset({"reportRedeclaration"}),
        {"reportArgumentType": 2},
        casts=1,
        line=11,
    )


@pytest.mark.parametrize(
    ("old", "new", "message"),
    [
        (
            'reportRedeclaration = "error"  # Locked',
            'reportRedeclaration = "error"',
            "marks no rule",
        ),
        (
            "[tool.type-suppressions.ignores]\n",
            "[tool.other.ignores]\n",
            "no `[tool.type-suppressions.ignores]`",
        ),
        ("cast = 1", "cast = -1", "`cast` must be an integer of at least 0"),
        (
            "reportArgumentType = 2",
            "reportArgumentType = 0",
            "`reportArgumentType` must be an integer of at least 1",
        ),
        (
            "reportArgumentType = 2",
            "reportRedeclaration = 2",
            "locked and budgeted: reportRedeclaration",
        ),
    ],
    ids=[
        "no-lock",
        "no-ignores",
        "negative-cast",
        "zero-rule",
        "locked-budgeted",
    ],
)
def test_load_budget_refuses_an_invalid_budget(
    tmp_path: Path,
    old: str,
    new: str,
    message: str,
) -> None:
    """No lock, a missing table, a count below its minimum, or a budgeted locked rule is refused."""
    pyproject = tmp_path / "pyproject.toml"
    _ = pyproject.write_text(_PYPROJECT.replace(old, new))

    with pytest.raises(cts.BudgetError, match=re.escape(message)):
        _ = cts.load_budget(pyproject)


def test_main_exits_one_and_lists_each_violation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A violating tree fails the run with each ``path:line`` and the summary line."""
    monkeypatch.setattr(cts, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(cts, "tracked_python_files", lambda: ["bad.py", "good.py"])
    _ = (tmp_path / "pyproject.toml").write_text(_PYPROJECT)
    _ = (tmp_path / "bad.py").write_text(
        "x = 1  # pyright: ignore[reportRedeclaration]\n"
        "y = f()  # pyright: ignore[reportArgumentType]\n",
    )
    _ = (tmp_path / "good.py").write_text("from typing import cast\n\nz = cast(int, 1)\n")

    assert cts.main([]) == 1
    assert capsys.readouterr().out.splitlines() == [
        "bad.py:1: `reportRedeclaration` is locked: fix the diagnostic, never suppress it",
        "pyproject.toml:11: `reportArgumentType` ignore comments: 1, budget 2: lower the budget to 1",
        "type-suppressions: checked 2 file(s); ignore comments 2, casts 1; violations 2",
    ]


@pytest.mark.parametrize(
    ("files", "pyproject"),
    [(["missing.py"], _PYPROJECT), ([], _PYPROJECT.replace("cast = 1", "cast = true"))],
    ids=["missing-file", "invalid-budget"],
)
def test_main_exits_two_when_it_cannot_measure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    files: list[str],
    pyproject: str,
) -> None:
    """A missing file or an invalid budget is a measurement failure, not a pass."""
    monkeypatch.setattr(cts, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(cts, "tracked_python_files", lambda: files)
    _ = (tmp_path / "pyproject.toml").write_text(pyproject)

    assert cts.main([]) == 2


def test_the_tracked_tree_is_on_budget() -> None:
    """Every git-tracked ``.py`` file passes and meets the budget, as the CI lint step requires."""
    assert cts.main([]) == 0
