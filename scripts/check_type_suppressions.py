"""Hold basedpyright suppressions to the locks and budget ``pyproject.toml`` sets.

basedpyright can only be told whether ignore comments are read at all: it has no
per-rule switch, keeps no count, and a file-level ``pyright:`` comment can lower any
rule for a whole file. This gate closes all three over every git-tracked ``.py`` file:

1. an ignore comment naming a rule ``[tool.basedpyright]`` marks ``# Locked``. Each
   locked rule is on and has no suppression in the tree, so its diagnostics are fixed
   at the root, never silenced;
2. any file-level ``pyright:`` directive (``basic``, ``reportFoo=false``, ...).
   ``[tool.basedpyright]`` owns every rule's level, file by file through its execution
   environments;
3. the budget. ``[tool.type-suppressions]`` sets how many ``typing.cast`` calls the
   tree holds (``cast``) and how many ignore comments name each unlocked rule
   (``[tool.type-suppressions.ignores]``; a rule it does not name has a budget of
   zero). A count above its budget is a new suppression: fix the diagnostic instead. A
   count below it is a cleared one: lower the budget to the count, so the cleared
   suppression cannot come back.

Only comment tokens are read, so a docstring or string that quotes a comment is not a
suppression; a ``cast`` call is one the AST resolves to ``typing.cast`` or
``typing_extensions.cast`` under any import alias.

Usage::

    uv run python scripts/check_type_suppressions.py

Exit code ``1`` (each violation listed) on any violation, ``2`` when a file cannot be
read or parsed or ``pyproject.toml`` holds no valid lock and budget.
"""

from __future__ import annotations

import argparse
import ast
import io
import re
import subprocess
import sys
import tokenize
from collections import Counter
from pathlib import Path
from typing import TYPE_CHECKING, NamedTuple

import tomli

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator, Mapping, Sequence

    from typing_extensions import TypeIs

REPO_ROOT = Path(__file__).resolve().parents[1]

#: ``report<Rule> = "<level>"  # Locked`` in ``[tool.basedpyright]``.
_LOCKED_LINE = re.compile(r'^(report\w+)\s*=\s*"\w+"\s*#\s*Locked\b', re.MULTILINE)

# basedpyright reads a directive at the start of a comment or after a further ``#``
# inside one (a ruff suppression, then the ignore).
_PYRIGHT_COMMENT = re.compile(r"(?:^|#)\s*pyright:\s*(?P<body>.*)")
_IGNORE = re.compile(r"ignore\s*(?:\[(?P<rules>[^\]]*)\])?")

#: The modules whose ``cast`` the budget counts.
_CAST_MODULES = frozenset({"typing", "typing_extensions"})


class BudgetError(ValueError):
    """``pyproject.toml`` holds no valid lock and budget."""


class Budget(NamedTuple):
    """The suppressions ``pyproject.toml`` allows."""

    #: Rules no ignore comment may name.
    locked: frozenset[str]
    #: How many ignore comments name each unlocked rule.
    ignores: Mapping[str, int]
    #: How many ``typing.cast`` calls the tree holds.
    casts: int
    #: The ``[tool.type-suppressions]`` header's line, where a count violation points.
    line: int


class Violation(NamedTuple):
    """One suppression the budget refuses: where it is and what it does."""

    path: str
    line: int
    message: str


def _is_toml_table(value: object) -> TypeIs[dict[str, object]]:
    """Return whether a decoded TOML value is a table (TOML table keys are always strings)."""
    return isinstance(value, dict)


def _count(value: object, *, minimum: int, name: str) -> int:
    """Return ``value`` as a budget count of at least ``minimum``, else raise."""
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise BudgetError(f"`{name}` must be an integer of at least {minimum}, not {value!r}")
    return value


def load_budget(pyproject: Path) -> Budget:
    """Read the locked rules and the budget from ``pyproject``.

    Raises:
        BudgetError: No rule is locked, a table is missing, a count is not a positive
            integer, or a locked rule carries a budget.

    """
    text = pyproject.read_text(encoding="utf-8")
    start = text.index("\n[tool.basedpyright]\n")
    end = text.find("\n[", start + 1)
    locked = frozenset(_LOCKED_LINE.findall(text[start : end if end != -1 else None]))
    if not locked:
        raise BudgetError("`[tool.basedpyright]` marks no rule `# Locked`")
    # ``tomli.loads`` returns ``dict[str, Any]``; this alias hands the walk an ``object``.
    toml_loads: Callable[[str], dict[str, object]] = tomli.loads
    table: object = toml_loads(text)
    for key in ("tool", "type-suppressions"):
        if not _is_toml_table(table) or key not in table:
            raise BudgetError("no `[tool.type-suppressions]` table")
        table = table[key]
    ignores = table.get("ignores") if _is_toml_table(table) else None
    if not _is_toml_table(table) or not _is_toml_table(ignores):
        raise BudgetError("no `[tool.type-suppressions.ignores]` table")
    budget = {rule: _count(count, minimum=1, name=rule) for rule, count in ignores.items()}
    if both := sorted(locked & budget.keys()):
        raise BudgetError(f"locked and budgeted: {', '.join(both)}")
    casts = _count(table.get("cast"), minimum=0, name="cast")
    header = text.find("\n[tool.type-suppressions]\n")
    return Budget(locked, budget, casts, text.count("\n", 0, header) + 2 if header != -1 else 1)


def _pyright_comments(source: str) -> Iterator[tuple[int, str]]:
    """Yield ``(line, body)`` for each ``pyright:`` directive among ``source``'s comments."""
    for token in tokenize.generate_tokens(io.StringIO(source).readline):
        if token.type != tokenize.COMMENT:
            continue
        for segment in token.string.split("#")[1:]:
            if (match := _PYRIGHT_COMMENT.match(f"#{segment}")) is not None:
                yield token.start[0], match.group("body").strip()


def ignored_rules(source: str) -> Iterator[tuple[int, str]]:
    """Yield ``(line, rule)`` for each rule an ignore comment in ``source`` names."""
    for line, body in _pyright_comments(source):
        if (ignore := _IGNORE.match(body)) is not None and ignore.group("rules"):
            for rule in ignore.group("rules").split(","):
                yield line, rule.strip()


def comment_violations(path: str, source: str, locked: frozenset[str]) -> Iterator[Violation]:
    """Yield every file-level directive and every ignore of a ``locked`` rule in ``source``."""
    for line, body in _pyright_comments(source):
        if _IGNORE.match(body) is None:
            yield Violation(
                path,
                line,
                f"file-level `# pyright: {body}` directive (pyproject.toml owns rule levels)",
            )
    for line, rule in ignored_rules(source):
        if rule in locked:
            yield Violation(
                path,
                line,
                f"`{rule}` is locked: fix the diagnostic, never suppress it",
            )


def cast_calls(source: str) -> int:
    """Count the calls in ``source`` that resolve to ``typing.cast``, under any alias."""
    tree = ast.parse(source)
    names: set[str] = set()
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module in _CAST_MODULES:
            names.update(
                alias.asname or alias.name for alias in node.names if alias.name == "cast"
            )
        elif isinstance(node, ast.Import):
            modules.update(
                alias.asname or alias.name for alias in node.names if alias.name in _CAST_MODULES
            )
    return sum(
        isinstance(node, ast.Call)
        and (
            (isinstance(node.func, ast.Name) and node.func.id in names)
            or (
                isinstance(node.func, ast.Attribute)
                and node.func.attr == "cast"
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id in modules
            )
        )
        for node in ast.walk(tree)
    )


def budget_violations(
    ignores: Mapping[str, int],
    casts: int,
    budget: Budget,
) -> Iterator[Violation]:
    """Yield each count, unlocked rule by rule then ``cast``, that differs from ``budget``."""
    counts = {**dict.fromkeys(budget.ignores, 0), **ignores}
    for rule in sorted(counts.keys() - budget.locked):
        allowed = budget.ignores.get(rule, 0)
        yield from _over_or_under(budget, f"`{rule}` ignore comments", counts[rule], allowed)
    yield from _over_or_under(budget, "`typing.cast` calls", casts, budget.casts)


def _over_or_under(
    budget: Budget,
    subject: str,
    count: int,
    allowed: int,
) -> Iterator[Violation]:
    """Yield the violation for ``count`` against ``allowed``, if they differ."""
    if count > allowed:
        fix = "fix the new diagnostic instead of suppressing it"
    elif count < allowed:
        fix = f"lower the budget to {count}" if count else "drop it from the budget"
    else:
        return
    yield Violation("pyproject.toml", budget.line, f"{subject}: {count}, budget {allowed}: {fix}")


def tracked_python_files() -> list[str]:
    """Every git-tracked ``.py`` file, repo-relative."""
    result = subprocess.run(
        ["git", "ls-files", "*.py"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.split()


def main(argv: Sequence[str] | None = None) -> int:
    """Check every tracked ``.py`` file against ``pyproject.toml``'s locks and budget."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    _ = parser.parse_args(argv)
    try:
        budget = load_budget(REPO_ROOT / "pyproject.toml")
    except (OSError, ValueError, tomli.TOMLDecodeError) as error:
        print(f"pyproject.toml: {error}", file=sys.stderr)
        return 2
    paths = tracked_python_files()
    violations: list[Violation] = []
    ignores: Counter[str] = Counter()
    casts = 0
    for path in paths:
        try:
            source = (REPO_ROOT / path).read_text(encoding="utf-8")
            violations.extend(comment_violations(path, source, budget.locked))
            ignores.update(rule for _, rule in ignored_rules(source))
            casts += cast_calls(source)
        except (
            OSError,
            UnicodeDecodeError,
            SyntaxError,
            tokenize.TokenError,
        ) as error:
            print(f"{path}: cannot check: {error}", file=sys.stderr)
            return 2
    violations.extend(budget_violations(ignores, casts, budget))
    for violation in violations:
        print(f"{violation.path}:{violation.line}: {violation.message}")
    print(
        f"type-suppressions: checked {len(paths)} file(s); ignore comments "
        f"{ignores.total()}, casts {casts}; violations {len(violations)}",
    )
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
