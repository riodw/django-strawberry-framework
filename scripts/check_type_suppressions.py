"""Fail on a basedpyright suppression the repo has locked out.

basedpyright can only be told whether ``# pyright: ignore[...]`` comments are read at
all; it has no per-rule switch, and a file-level ``# pyright:`` comment can lower any
rule for a whole file. This gate closes both:

1. a ``# pyright: ignore[...]`` naming a rule in ``LOCKED_RULES``. Each locked rule
   is on and has no suppression in the tree, so its diagnostics are fixed at the
   root, never silenced. A rule leaves the set only by a deliberate edit here;
2. any file-level ``# pyright:`` directive (``# pyright: basic``,
   ``# pyright: reportFoo=false``, ...). ``[tool.basedpyright]`` in
   ``pyproject.toml`` owns every rule's level, file by file through its execution
   environments.

Only comment tokens are read, so a docstring or string that quotes a comment is not
a suppression.

Usage::

    uv run python scripts/check_type_suppressions.py [paths ...]

With no paths it checks every git-tracked ``.py`` file. Exit code ``1`` (each
violation listed) on any violation, ``2`` when a file cannot be read or tokenized.
"""

from __future__ import annotations

import argparse
import io
import re
import subprocess
import sys
import tokenize
from pathlib import Path
from typing import TYPE_CHECKING, NamedTuple

if TYPE_CHECKING:
    from collections.abc import Iterator, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]

#: Rules no ``# pyright: ignore[...]`` may name: switched on in every execution
#: environment and fixed at the root everywhere they fire.
LOCKED_RULES = frozenset(
    {
        "reportAbstractUsage",
        "reportAssertAlwaysTrue",
        "reportAssertTypeFailure",
        "reportCallInDefaultInitializer",
        "reportConstantRedefinition",
        "reportDuplicateImport",
        "reportEmptyAbstractUsage",
        "reportIgnoreCommentWithoutRule",
        "reportImplicitAbstractClass",
        "reportImplicitRelativeImport",
        "reportIncompleteStub",
        "reportInconsistentConstructor",
        "reportInconsistentOverload",
        "reportInvalidAbstractMethod",
        "reportInvalidStringEscapeSequence",
        "reportInvalidStubStatement",
        "reportInvalidTypeVarUse",
        "reportMatchNotExhaustive",
        "reportMissingImports",
        "reportMissingModuleSource",
        "reportMissingParameterType",
        "reportMissingTypeStubs",
        "reportNoOverloadImplementation",
        "reportOperatorIssue",
        "reportOptionalCall",
        "reportOptionalContextManager",
        "reportOptionalIterable",
        "reportOptionalOperand",
        "reportOptionalSubscript",
        "reportOverlappingOverload",
        "reportPossiblyUnboundVariable",
        "reportPrivateImportUsage",
        "reportPrivateLocalImportUsage",
        "reportRedeclaration",
        "reportSelfClsDefault",
        "reportSelfClsParameterName",
        "reportTypeCommentUsage",
        "reportTypedDictNotRequiredAccess",
        "reportUnboundVariable",
        "reportUnhashable",
        "reportUnknownLambdaType",
        "reportUnnecessaryCast",
        "reportUnnecessaryContains",
        "reportUnnecessaryTypeIgnoreComment",
        "reportUnsupportedDunderAll",
        "reportUntypedClassDecorator",
        "reportUntypedNamedTuple",
        "reportUnusedClass",
        "reportUnusedCoroutine",
        "reportUnusedExcept",
        "reportUnusedExpression",
        "reportUnusedParameter",
        "reportUnusedVariable",
        "reportWildcardImportFromLibrary",
    },
)

# basedpyright reads a ``pyright:`` comment at the start of a comment or after a
# further ``#`` inside one (a ruff suppression, then ``# pyright: ignore[...]``).
_PYRIGHT_COMMENT = re.compile(r"(?:^|#)\s*pyright:\s*(?P<body>.*)")
_IGNORE = re.compile(r"ignore\s*(?:\[(?P<rules>[^\]]*)\])?")


class Violation(NamedTuple):
    """One locked-out suppression: where it is and what it does."""

    path: str
    line: int
    message: str


def comment_violations(path: str, source: str) -> Iterator[Violation]:
    """Yield every locked-out suppression among ``source``'s comment tokens."""
    for token in tokenize.generate_tokens(io.StringIO(source).readline):
        if token.type != tokenize.COMMENT:
            continue
        for segment in token.string.split("#")[1:]:
            match = _PYRIGHT_COMMENT.match(f"#{segment}")
            if match is None:
                continue
            body = match.group("body").strip()
            ignore = _IGNORE.match(body)
            if ignore is None:
                yield Violation(
                    path,
                    token.start[0],
                    f"file-level `# pyright: {body}` directive (pyproject.toml owns rule levels)",
                )
                continue
            named = {rule.strip() for rule in (ignore.group("rules") or "").split(",")}
            for rule in sorted(named & LOCKED_RULES):
                yield Violation(
                    path,
                    token.start[0],
                    f"`{rule}` is locked: fix the diagnostic, never suppress it",
                )


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


class _Arguments(argparse.Namespace):
    """The parsed command line."""

    paths: list[str]


def main(argv: Sequence[str] | None = None) -> int:
    """Check ``argv``'s paths (every tracked ``.py`` file without any) and report."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    _ = parser.add_argument("paths", nargs="*", help="files to check (default: every tracked .py)")
    arguments = parser.parse_args(argv, namespace=_Arguments())
    if arguments.paths:
        paths = [path for path in arguments.paths if path.endswith(".py")]
    else:
        paths = tracked_python_files()
    violations: list[Violation] = []
    for path in paths:
        try:
            source = (REPO_ROOT / path).read_text(encoding="utf-8")
            violations.extend(comment_violations(path, source))
        except (
            OSError,
            UnicodeDecodeError,
            SyntaxError,
            tokenize.TokenError,
        ) as error:
            print(f"{path}: cannot check: {error}", file=sys.stderr)
            return 2
    for violation in violations:
        print(f"{violation.path}:{violation.line}: {violation.message}")
    print(f"type-suppressions: checked {len(paths)} file(s); violations {len(violations)}")
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
