"""Resolve every ``path::Symbol`` source reference against the tree it names.

AGENTS.md rule 27 requires source refs in code comments, docstrings and standing
docs to be symbol paths (``path::QualifiedName``) rather than line numbers, and
requires a rename to grep-sweep ``::OldName`` in the same change. Nothing enforced
the second half: a citation whose symbol was renamed or deleted stayed a plausible
sentence, and the rot was only ever found by hand during a spec reconciliation.

This gate resolves both halves. For every ``<path>.py::<Symbol>`` reference it
locates the file, parses it, and asserts the symbol is actually defined (or
imported, so re-export citations such as ``__init__.py::SomeName`` resolve).

Two corpora, deliberately different strictness:

* **First-party ``.py`` sources** (``django_strawberry_framework/``, ``tests/``,
  ``examples/``, ``scripts/``) are fail-closed: an unresolvable *file* is a
  violation too, because a bare upstream basename is exactly the ambiguity rule 27
  exists to remove -- cite ``django_graphene_filters/connection_field.py::x``, not
  ``connection_field.py::x``.
* **``KANBAN.md``** fails only on real rot -- a cited file that exists whose symbol
  does not. TODO cards legitimately cite files that are not written yet, and parity
  cards cite upstream trees that are not vendored here, so an unresolvable file
  carries no signal on the board.

``docs/`` is deliberately out of scope. The spec archive is a historical record
reconciled per-card during a residual cycle, not a surface a commit should gate on.

The whole corpus is swept on every run (``pass_filenames: false``): a rename in the
file you are committing rots citations in files you are not, so a staged-paths-only
sweep would be blind to the failure this gate exists to catch.

Usage::

    uv run python scripts/check_citations.py

Exit code ``0`` when every citation resolves, ``1`` when any does not, ``2`` on a
caller-correctable error.
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from collections.abc import Iterator, Sequence
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# The first-party trees. A citation's file half is resolved against these (plus the
# citing file's own directory), so `utils/querysets.py::visible_related_object`
# resolves from anywhere without spelling the package prefix every time.
SOURCE_TREES = (
    "django_strawberry_framework",
    "tests",
    "examples",
    "scripts",
)
PACKAGE_ROOT = "django_strawberry_framework"

# Markdown files inside the gate, checked under the softer "real rot only" rule.
MARKDOWN_SOURCES = ("KANBAN.md",)

# Path prefixes naming a tree that is not vendored here. Citations under them are
# upstream references (graphene-django parity notes, Django internals) and can only
# be resolved against a checkout this repo does not own.
UPSTREAM_PREFIXES = (
    "channels/",
    "django/",
    "django_graphene_filters/",
    "graphene/",
    "graphene_django/",
    "graphql/",
    "main/",
    "packages/",
    "strawberry/",
    "strawberry_django/",
)

# Files whose `path::Symbol` strings are test fixtures or documentation examples
# rather than claims about this tree.
SYNTHETIC_SOURCES = frozenset(
    {
        "scripts/check_citations.py",
        "scripts/prove_failability.py",
        "tests/test_export_dry_review.py",
        "tests/test_prove_failability.py",
    },
)

# `mutations/resolvers.py::resolve_` and `filters/sets.py::FilterSet.` name a family
# of symbols by prefix, not one symbol; they are outside what this gate can resolve.
FAMILY_SUFFIXES = ("_", ".")

CITATION_RE = re.compile(r"([\w][\w./]*\.py)::([A-Za-z_][\w.]*)")


class CitationCheckError(RuntimeError):
    """A caller-correctable citation-check error."""


def iter_python_sources() -> tuple[Path, ...]:
    """Return every first-party ``.py`` file, sorted."""
    found: list[Path] = []
    for tree in SOURCE_TREES:
        found.extend((REPO_ROOT / tree).rglob("*.py"))
    return tuple(sorted(found))


def _add(names: set[str], prefix: str, name: str) -> None:
    """Record ``name`` both bare and qualified by its enclosing ``prefix``."""
    names.add(name)
    names.add(prefix + name)


def _collect(node: ast.AST, names: set[str], prefix: str) -> None:
    """Walk one scope, recording every name it binds.

    Recurses into classes (so ``Class.method`` resolves) and into ``if`` / ``try``
    bodies (module-level soft-import fallbacks bind real names). Function bodies are
    not descended: a local inside a function is not a citable symbol.
    """
    for child in ast.iter_child_nodes(node):
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            _add(names, prefix, child.name)
            _collect(child, names, f"{prefix}{child.name}.")
        elif isinstance(child, ast.Assign):
            for target in child.targets:
                for inner in ast.walk(target):
                    if isinstance(inner, ast.Name):
                        _add(names, prefix, inner.id)
        elif isinstance(child, ast.AnnAssign):
            if isinstance(child.target, ast.Name):
                _add(names, prefix, child.target.id)
        elif isinstance(child, (ast.Import, ast.ImportFrom)):
            # A re-export is a real citable symbol: `types/__init__.py::DjangoType`
            # names the binding this module publishes, not where it was defined.
            for alias in child.names:
                bound = alias.asname or alias.name.split(".", 1)[0]
                _add(names, prefix, bound)
        elif isinstance(child, (ast.If, ast.Try)):
            _collect(child, names, prefix)


_SYMBOL_CACHE: dict[Path, frozenset[str]] = {}


def module_symbols(path: Path) -> frozenset[str]:
    """Return every symbol ``path`` binds at module or class scope (cached)."""
    cached = _SYMBOL_CACHE.get(path)
    if cached is not None:
        return cached
    try:
        tree = ast.parse(path.read_text(encoding="utf-8-sig"))
    except (SyntaxError, ValueError, OSError):
        # An unparseable module cannot vouch for a symbol; treat it as empty rather
        # than failing the run, so one broken file does not mask every real finding.
        names: frozenset[str] = frozenset()
    else:
        collected: set[str] = set()
        _collect(tree, collected, "")
        names = frozenset(collected)
    _SYMBOL_CACHE[path] = names
    return names


def suffix_index(corpus: Sequence[Path]) -> dict[str, tuple[Path, ...]]:
    """Map every trailing sub-path of every corpus file to the files carrying it.

    Built once so resolving a bare ``querysets.py`` is a dict hit rather than a
    match against all several-hundred corpus paths per citation.
    """
    index: dict[str, list[Path]] = {}
    for path in corpus:
        parts = path.relative_to(REPO_ROOT).parts
        for start in range(len(parts)):
            index.setdefault("/".join(parts[start:]), []).append(path)
    return {suffix: tuple(paths) for suffix, paths in index.items()}


def candidate_paths(cited: str, source: Path, index: dict[str, tuple[Path, ...]]) -> list[Path]:
    """Return every file ``cited`` could name, nearest spelling first.

    A citation resolves if ANY candidate defines the symbol: two packages can hold a
    ``permissions.py``, and guessing one of them would invent rot that is not there.
    """
    ordered = [
        source.parent / cited,
        REPO_ROOT / cited,
        REPO_ROOT / PACKAGE_ROOT / cited,
        *(REPO_ROOT / tree / cited for tree in SOURCE_TREES),
    ]
    candidates = [path for path in ordered if path.is_file()]
    candidates.extend(index.get(cited, ()))
    unique: list[Path] = []
    for path in candidates:
        if path not in unique:
            unique.append(path)
    return unique


def iter_citations(text: str) -> Iterator[tuple[int, str, str]]:
    """Yield ``(line number, cited path, symbol)`` for every checkable citation."""
    for match in CITATION_RE.finditer(text):
        cited, symbol = match.group(1), match.group(2)
        if cited.startswith(UPSTREAM_PREFIXES) or symbol.endswith(FAMILY_SUFFIXES):
            continue
        yield text.count("\n", 0, match.start()) + 1, cited, symbol


def symbol_homes(symbol: str, corpus: Sequence[Path]) -> list[str]:
    """Return the files that DO define ``symbol`` -- the fix hint for a rotted cite."""
    return [str(path.relative_to(REPO_ROOT)) for path in corpus if symbol in module_symbols(path)]


def check_source(
    source: Path,
    corpus: Sequence[Path],
    index: dict[str, tuple[Path, ...]],
    *,
    require_file: bool,
) -> tuple[list[str], int]:
    """Return ``(violations, citations checked)`` for one file.

    ``require_file`` fails a citation whose file half resolves to nothing. It is on
    for first-party ``.py`` sources and off for the board, where a card may cite a
    file that is planned or upstream.
    """
    relative = str(source.relative_to(REPO_ROOT))
    try:
        text = source.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError) as error:
        raise CitationCheckError(f"{relative}: {error}") from error

    violations: list[str] = []
    checked = 0
    for line, cited, symbol in iter_citations(text):
        checked += 1
        candidates = candidate_paths(cited, source, index)
        if not candidates:
            if require_file:
                violations.append(
                    f"{relative}:{line}: cites `{cited}::{symbol}` -- no such file. "
                    f"Prefix an upstream ref with its package (`django_graphene_filters/"
                    f"{cited}`), or correct the path.",
                )
            continue
        if any(symbol in module_symbols(path) for path in candidates):
            continue
        homes = symbol_homes(symbol, corpus)
        where = ", ".join(homes[:2]) if homes else "nowhere in the tree"
        violations.append(
            f"{relative}:{line}: cites `{cited}::{symbol}` -- "
            f"`{cited}` defines no `{symbol}`. Now lives in: {where}.",
        )
    return violations, checked


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Resolve every path::Symbol source reference against the tree.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Accepted for parity with the other gates; the run is always read-only.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """Sweep the corpus and report every citation whose target no longer exists."""
    parse_args(sys.argv[1:] if argv is None else argv)
    corpus = iter_python_sources()
    if not corpus:
        raise CitationCheckError(f"No .py sources found under {REPO_ROOT}.")
    index = suffix_index(corpus)

    violations: list[str] = []
    checked = 0
    for source in corpus:
        if str(source.relative_to(REPO_ROOT)) in SYNTHETIC_SOURCES:
            continue
        found, count = check_source(source, corpus, index, require_file=True)
        violations.extend(found)
        checked += count
    python_checked = checked

    for name in MARKDOWN_SOURCES:
        markdown = REPO_ROOT / name
        if not markdown.is_file():
            raise CitationCheckError(f"{name} is missing; the citation gate expects it.")
        found, count = check_source(markdown, corpus, index, require_file=False)
        violations.extend(found)
        checked += count

    scope = f"{python_checked} in {len(corpus)} .py files, {checked - python_checked} in KANBAN.md"
    if violations:
        print(f"FAIL: {len(violations)} unresolvable citation(s) of {checked} checked ({scope}):")
        for violation in violations:
            print(f"  - {violation}")
        print(
            "\nFix: repoint the citation at the symbol's current home, or delete it. "
            "AGENTS.md rule 27 -- renaming a symbol means grep-sweeping `::OldName` in "
            "the same change.",
        )
        return 1

    print(f"OK: {checked} citations resolve ({scope}).")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except CitationCheckError as error:
        print(error, file=sys.stderr)
        raise SystemExit(2) from error
