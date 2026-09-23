"""Resolve every ``path::Symbol`` source reference against the tree it names.

AGENTS.md rule 27 requires source refs in code comments, docstrings and standing
docs to be symbol paths (``path::QualifiedName``) rather than line numbers, and
requires a rename to grep-sweep ``::OldName`` in the same change. Nothing enforced
the second half: a citation whose symbol was renamed or deleted stayed a plausible
sentence, and the rot was only ever found by hand during a spec reconciliation.

This gate resolves both halves. For every ``<path>.py::<Symbol>`` reference it
locates the file, parses it, and asserts the symbol is actually defined (or
imported, so re-export citations such as ``__init__.py::SomeName`` resolve).

What resolves: a name bound at module or class scope (``def``, ``class``,
assignment, import), reached through ``if`` / ``try`` bodies, bare or qualified by
its enclosing classes. Inside a function body only nested ``def`` / ``class``
names are recorded (a closure such as a resolver factory's inner function is a
real citable callable); a function-local variable is not a citable symbol. A
dunder (``Class.__init_subclass__``, ``__all__``) is one symbol and is resolved
like any other name; only a trailing ``_`` or ``.`` on a non-dunder names a
family of symbols by prefix and is skipped. A citation wrapped across two lines
(``path.py::`` at a line end with the symbol on the next line, or a path split
after a ``/``) is joined and checked at the line it starts on.

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

``docs/`` is deliberately out of the gate. The spec archive is a historical record
reconciled per-card during a residual cycle, not a surface a commit should gate on.
``--cited-by`` reads the standing ``docs/`` markdown anyway, marked ungated, because
a rename or a reword strands those citers too.

The whole corpus is swept on every run (``pass_filenames: false``): a rename in the
file you are committing rots citations in files you are not, so a staged-paths-only
sweep would be blind to the failure this gate exists to catch. ``--paths`` exists for
a reviewer holding one file, never for the hook.

Reviewer flags (none changes the default run):

* ``--paths PATH...`` checks only the citations found in the named files (any
  ``.py`` or ``.md``; resolution still runs against the whole tree). A named
  ``KANBAN.md`` keeps its soft rule; every other named file is fail-closed.
* ``--json`` prints every checked citation with its file, line, kind (``symbol`` /
  ``dunder`` / ``substring``), resolved flag, target file and, for a failure, the
  "now lives in" hint. The summary line goes to stderr so stdout stays JSON.
* ``--substrings`` also checks ``path::Symbol #"unique substring"`` (the text must
  occur inside the symbol's source span) and ``path #"substring"`` (anywhere in the
  file). A pinpoint that occurs more than once is a warning, not a failure.
* ``--cited-by PATH[::Symbol]`` lists every file and line that cites that path (or
  that symbol, or a member of it) across the gate corpus and the standing ``docs/``
  markdown (per-cycle ``rev-*`` / ``review-*`` / ``dry-*`` / ``bld-*`` /
  ``bug_hunt-*`` artifacts, ``docs/SPECS/`` and scratch folders excluded), each row
  marked ``gated`` or ``ungated``. Run it before renaming a symbol or rewording a
  cited line.

Usage::

    uv run python scripts/check_citations.py
    uv run python scripts/check_citations.py --paths <file>... --substrings --json
    uv run python scripts/check_citations.py --cited-by <path>::<Symbol>

Exit code ``0`` when every citation resolves, ``1`` when any does not, ``2`` on a
caller-correctable error. ``--cited-by`` is a query and exits ``0`` on any answer.
"""

from __future__ import annotations

import argparse
import ast
import fnmatch
import json
import os
import re
import sys
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
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
        "tests/test_check_citations.py",
        "tests/test_export_dry_review.py",
        "tests/test_prove_failability.py",
        "tests/test_review_changed_python_diffs.py",
        "tests/test_review_inspect.py",
    },
)

# `mutations/resolvers.py::resolve_` and `filters/sets.py::FilterSet.` name a family
# of symbols by prefix, not one symbol; they are outside what this gate can resolve.
# A dunder also ends in `_` but is one symbol (see `is_family`).
FAMILY_SUFFIXES = ("_", ".")
DUNDER_RE = re.compile(r"__[A-Za-z0-9]\w*?__")

CITATION_RE = re.compile(r"([\w][\w./]*\.py)::([A-Za-z_][\w.]*)")

# `path.py::` closing one line, the symbol opening the next (after indentation, an
# optional comment marker and optional code-span backticks).
WRAPPED_SYMBOL_RE = re.compile(
    r"([\w][\w./]*\.py)::`*[ \t]*\r?\n[ \t]*(?:#[ \t]*)?`*([A-Za-z_][\w.]*)",
)
# A path split after a `/`: `utils/` closing one line, `querysets.py::x` the next.
WRAPPED_PATH_RE = re.compile(
    r"([\w][\w./]*/)[ \t]*\r?\n[ \t]*(?:#[ \t]*)?(([\w./]*\.py)::([A-Za-z_][\w.]*))",
)
# `path::Symbol #"text"` and `path #"text"`, quoted text on one source line.
SUBSTRING_RE = re.compile(
    r"([\w][\w./-]*\.(?:py|md|toml|ya?ml|json|html|csv|txt|cfg|ini))"
    r"(?:::([A-Za-z_][\w.]*))?[ \t]+#\"([^\"\n]+)\"",
)

# `--cited-by` reads standing docs but not the per-cycle artifacts that close with
# their cycle, the spec archive, or untracked scratch folders.
DOCS_ROOT = "docs"
PER_CYCLE_ARTIFACTS = (
    "rev-*.md",
    "review-*.md",
    "dry-*.md",
    "bld-*.md",
    "bug_hunt-*.md",
)
EXCLUDED_DOCS_DIRS = frozenset(
    {
        "SPECS",
        "shadow",
        "temp-tests",
        "worker-memory",
    },
)

# Directories never walked when resolving a non-`.py` pinpoint target by suffix.
PRUNED_DIRS = frozenset({"node_modules", "__pycache__", "htmlcov"})

KIND_SYMBOL = "symbol"
KIND_DUNDER = "dunder"
KIND_SUBSTRING = "substring"


class CitationCheckError(RuntimeError):
    """A caller-correctable citation-check error."""


@dataclass(frozen=True)
class Citation:
    """One citation found in a source text."""

    line: int
    cited: str
    symbol: str | None
    kind: str
    substring: str | None = None

    @property
    def text(self) -> str:
        """Return the citation as it would be written in a source."""
        base = f"{self.cited}::{self.symbol}" if self.symbol else self.cited
        return f'{base} #"{self.substring}"' if self.substring is not None else base


@dataclass(frozen=True)
class Outcome:
    """The resolution verdict for one citation in one source file."""

    source: str
    citation: Citation
    resolved: bool
    violation: bool
    target: str | None
    candidates: tuple[str, ...]
    hint: tuple[str, ...] = ()
    message: str | None = None
    warning: str | None = None

    def as_json(self) -> dict[str, object]:
        """Return the JSON-ready record for ``--json``."""
        return {
            "file": self.source,
            "line": self.citation.line,
            "cite": self.citation.text,
            "path": self.citation.cited,
            "symbol": self.citation.symbol,
            "substring": self.citation.substring,
            "kind": self.citation.kind,
            "resolved": self.resolved,
            "violation": self.violation,
            "target": self.target,
            "candidates": list(self.candidates),
            "now_lives_in": list(self.hint),
            "message": self.message,
            "warning": self.warning,
        }


def iter_python_sources() -> tuple[Path, ...]:
    """Return every first-party ``.py`` file, sorted."""
    found: list[Path] = []
    for tree in SOURCE_TREES:
        found.extend((REPO_ROOT / tree).rglob("*.py"))
    return tuple(sorted(found))


def iter_standing_docs() -> tuple[Path, ...]:
    """Return the standing ``docs/`` markdown ``--cited-by`` reads, sorted."""
    docs = REPO_ROOT / DOCS_ROOT
    found: list[Path] = []
    for path in docs.rglob("*.md"):
        parts = path.relative_to(docs).parts
        if EXCLUDED_DOCS_DIRS.intersection(parts[:-1]):
            continue
        if any(fnmatch.fnmatch(path.name, pattern) for pattern in PER_CYCLE_ARTIFACTS):
            continue
        found.append(path)
    return tuple(sorted(found))


def _add(names: set[str], prefix: str, name: str) -> None:
    """Record ``name`` both bare and qualified by its enclosing ``prefix``."""
    names.add(name)
    names.add(prefix + name)


def _bind(
    names: set[str],
    spans: dict[str, list[tuple[int, int, str]]] | None,
    prefix: str,
    name: str,
    node: ast.stmt,
) -> None:
    """Record ``name`` and, when spans are collected, the lines ``node`` covers."""
    _add(names, prefix, name)
    if spans is None:
        return
    decorators = getattr(node, "decorator_list", ())
    start = min([node.lineno, *(decorator.lineno for decorator in decorators)])
    span = (start, node.end_lineno or node.lineno, prefix + name)
    for key in {name, prefix + name}:
        spans.setdefault(key, []).append(span)


def _collect(
    node: ast.AST,
    names: set[str],
    prefix: str,
    *,
    in_function: bool = False,
    spans: dict[str, list[tuple[int, int, str]]] | None = None,
) -> None:
    """Walk one scope, recording every name it binds.

    Recurses into classes (so ``Class.method`` resolves), into ``if`` / ``try``
    bodies (module-level soft-import fallbacks bind real names), and into function
    bodies for nested ``def`` / ``class`` only (a closure is a citable callable).
    Any other binding inside a function body is a local and is not recorded.

    Args:
        node: The scope to walk.
        names: The set every bound name is added to, bare and qualified.
        prefix: The dotted qualifier of the enclosing classes and functions.
        in_function: Whether ``node`` sits inside a function body.
        spans: When given, maps each recorded name to its ``(start, end,
            qualified name)`` line spans.
    """
    for child in ast.iter_child_nodes(node):
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            _bind(names, spans, prefix, child.name, child)
            _collect(
                child,
                names,
                f"{prefix}{child.name}.",
                in_function=in_function or not isinstance(child, ast.ClassDef),
                spans=spans,
            )
        elif isinstance(child, (ast.If, ast.Try)):
            _collect(child, names, prefix, in_function=in_function, spans=spans)
        elif in_function:
            continue
        elif isinstance(child, ast.Assign):
            for target in child.targets:
                for inner in ast.walk(target):
                    if isinstance(inner, ast.Name):
                        _bind(names, spans, prefix, inner.id, child)
        elif isinstance(child, ast.AnnAssign):
            if isinstance(child.target, ast.Name):
                _bind(names, spans, prefix, child.target.id, child)
        elif isinstance(child, (ast.Import, ast.ImportFrom)):
            # A re-export is a real citable symbol: `types/__init__.py::DjangoType`
            # names the binding this module publishes, not where it was defined.
            for alias in child.names:
                bound = alias.asname or alias.name.split(".", 1)[0]
                _bind(names, spans, prefix, bound, child)


_SYMBOL_CACHE: dict[Path, frozenset[str]] = {}
_SPAN_CACHE: dict[Path, dict[str, tuple[tuple[int, int, str], ...]]] = {}
_OTHER_FILE_INDEX: dict[Path, dict[str, tuple[Path, ...]]] = {}


def _parse(path: Path) -> ast.Module | None:
    """Parse ``path``, or return ``None`` when it cannot vouch for any symbol."""
    try:
        return ast.parse(path.read_text(encoding="utf-8-sig"))
    except (SyntaxError, ValueError, OSError):
        return None


def module_symbols(path: Path) -> frozenset[str]:
    """Return every symbol ``path`` binds at module or class scope (cached)."""
    cached = _SYMBOL_CACHE.get(path)
    if cached is not None:
        return cached
    tree = _parse(path)
    # An unparseable module cannot vouch for a symbol; treat it as empty rather
    # than failing the run, so one broken file does not mask every real finding.
    collected: set[str] = set()
    if tree is not None:
        _collect(tree, collected, "")
    names = frozenset(collected)
    _SYMBOL_CACHE[path] = names
    return names


def module_spans(path: Path) -> dict[str, tuple[tuple[int, int, str], ...]]:
    """Return every recorded name's ``(start, end, qualified name)`` spans (cached)."""
    cached = _SPAN_CACHE.get(path)
    if cached is not None:
        return cached
    tree = _parse(path)
    spans: dict[str, list[tuple[int, int, str]]] = {}
    if tree is not None:
        _collect(tree, set(), "", spans=spans)
    frozen = {name: tuple(found) for name, found in spans.items()}
    _SPAN_CACHE[path] = frozen
    return frozen


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


def _other_file_index() -> dict[str, tuple[Path, ...]]:
    """Map every trailing sub-path of every non-``.py`` repo file to its files (cached)."""
    cached = _OTHER_FILE_INDEX.get(REPO_ROOT)
    if cached is not None:
        return cached
    index: dict[str, list[Path]] = {}
    for directory, subdirs, files in os.walk(REPO_ROOT):
        subdirs[:] = sorted(
            name for name in subdirs if not name.startswith(".") and name not in PRUNED_DIRS
        )
        for name in sorted(files):
            if name.endswith(".py"):
                continue
            path = Path(directory) / name
            parts = path.relative_to(REPO_ROOT).parts
            for start in range(len(parts)):
                index.setdefault("/".join(parts[start:]), []).append(path)
    frozen = {suffix: tuple(paths) for suffix, paths in index.items()}
    _OTHER_FILE_INDEX[REPO_ROOT] = frozen
    return frozen


def candidate_files(cited: str, source: Path, index: dict[str, tuple[Path, ...]]) -> list[Path]:
    """Return every file a pinpoint's ``cited`` could name, ``.py`` or not."""
    if cited.endswith(".py"):
        return candidate_paths(cited, source, index)
    ordered = [
        source.parent / cited,
        REPO_ROOT / cited,
        REPO_ROOT / DOCS_ROOT / cited,
        REPO_ROOT / PACKAGE_ROOT / cited,
        *(REPO_ROOT / tree / cited for tree in SOURCE_TREES),
    ]
    candidates = [path for path in ordered if path.is_file()]
    if not candidates:
        candidates = list(_other_file_index().get(cited, ()))
    unique: list[Path] = []
    for path in candidates:
        if path not in unique:
            unique.append(path)
    return unique


def is_family(symbol: str) -> bool:
    """Return whether ``symbol`` names a family of symbols by prefix, not one symbol."""
    last = symbol.rsplit(".", 1)[-1]
    return symbol.endswith(FAMILY_SUFFIXES) and not DUNDER_RE.fullmatch(last)


def _symbol_kind(symbol: str) -> str:
    """Return ``dunder`` when the symbol's last segment is a dunder, else ``symbol``."""
    return KIND_DUNDER if DUNDER_RE.fullmatch(symbol.rsplit(".", 1)[-1]) else KIND_SYMBOL


def _line_of(text: str, offset: int) -> int:
    """Return the 1-based line number of ``offset`` in ``text``."""
    return text.count("\n", 0, offset) + 1


def iter_citation_records(text: str, *, substrings: bool = False) -> Iterator[Citation]:
    """Yield every checkable citation in ``text``, in source order.

    Args:
        text: The source text to scan.
        substrings: Also yield ``#"substring"`` pinpoints as ``substring`` records.

    Yields:
        One ``Citation`` per checkable reference; upstream and family citations
        are skipped.
    """
    found: list[tuple[int, Citation]] = []
    continuations: set[int] = set()
    for match in WRAPPED_PATH_RE.finditer(text):
        continuations.add(match.start(2))
        cited = match.group(1) + match.group(3)
        found.append((match.start(), _symbol_citation(text, match.start(), cited, match.group(4))))
    for match in WRAPPED_SYMBOL_RE.finditer(text):
        found.append(
            (match.start(), _symbol_citation(text, match.start(), match.group(1), match.group(2))),
        )
    for match in CITATION_RE.finditer(text):
        if match.start() in continuations:
            continue
        found.append(
            (match.start(), _symbol_citation(text, match.start(), match.group(1), match.group(2))),
        )
    if substrings:
        for match in SUBSTRING_RE.finditer(text):
            cited, symbol, substring = match.group(1), match.group(2), match.group(3)
            record = Citation(
                _line_of(text, match.start()),
                cited,
                symbol,
                KIND_SUBSTRING,
                substring,
            )
            found.append((match.start(), record))
    found.sort(key=lambda item: (item[0], item[1].kind == KIND_SUBSTRING))
    for _, citation in found:
        if citation.cited.startswith(UPSTREAM_PREFIXES):
            continue
        if citation.kind != KIND_SUBSTRING and is_family(citation.symbol or ""):
            continue
        yield citation


def _symbol_citation(
    text: str,
    offset: int,
    cited: str,
    symbol: str,
) -> Citation:
    """Build a ``symbol`` or ``dunder`` record starting at ``offset``."""
    return Citation(_line_of(text, offset), cited, symbol, _symbol_kind(symbol))


def iter_citations(text: str) -> Iterator[tuple[int, str, str]]:
    """Yield ``(line number, cited path, symbol)`` for every checkable citation."""
    for citation in iter_citation_records(text):
        yield citation.line, citation.cited, citation.symbol or ""


def symbol_homes(symbol: str, corpus: Sequence[Path]) -> list[str]:
    """Return the files that DO define ``symbol`` -- the fix hint for a rotted cite."""
    return [str(path.relative_to(REPO_ROOT)) for path in corpus if symbol in module_symbols(path)]


def _relative(path: Path) -> str:
    """Return ``path`` relative to the repo root."""
    return str(path.relative_to(REPO_ROOT))


def _symbol_outcome(
    citation: Citation,
    relative: str,
    source: Path,
    corpus: Sequence[Path],
    index: dict[str, tuple[Path, ...]],
    *,
    require_file: bool,
) -> Outcome:
    """Resolve one ``symbol`` or ``dunder`` citation."""
    cited, symbol = citation.cited, citation.symbol or ""
    candidates = candidate_paths(cited, source, index)
    names = tuple(_relative(path) for path in candidates)
    if not candidates:
        message = None
        if require_file:
            message = (
                f"{relative}:{citation.line}: cites `{cited}::{symbol}` -- no such file. "
                f"Prefix an upstream ref with its package (`django_graphene_filters/"
                f"{cited}`), or correct the path."
            )
        return Outcome(relative, citation, False, require_file, None, names, message=message)
    for path in candidates:
        if symbol in module_symbols(path):
            return Outcome(relative, citation, True, False, _relative(path), names)
    homes = symbol_homes(symbol, corpus)
    where = ", ".join(homes[:2]) if homes else "nowhere in the tree"
    message = (
        f"{relative}:{citation.line}: cites `{cited}::{symbol}` -- "
        f"`{cited}` defines no `{symbol}`. Now lives in: {where}."
    )
    return Outcome(relative, citation, False, True, None, names, tuple(homes), message)


def _enclosing_symbols(path: Path, substring: str) -> tuple[str, ...]:
    """Return ``path::Qualified`` for the innermost symbol holding ``substring``."""
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    offset = text.find(substring)
    if offset < 0 or path.suffix != ".py":
        return ()
    line = _line_of(text, offset)
    spans = {span for found in module_spans(path).values() for span in found}
    holding = sorted(
        (span for span in spans if span[0] <= line <= span[1]),
        key=lambda span: (-span[0], span[1]),
    )
    if not holding:
        return (_relative(path),)
    return (f"{_relative(path)}::{holding[0][2]}",)


def _substring_outcome(
    citation: Citation,
    relative: str,
    source: Path,
    corpus: Sequence[Path],
    index: dict[str, tuple[Path, ...]],
    *,
    require_file: bool,
) -> Outcome:
    """Resolve one ``#"substring"`` pinpoint."""
    cited, symbol, substring = citation.cited, citation.symbol, citation.substring or ""
    at = f"{relative}:{citation.line}: cites `{citation.text}` --"
    candidates = candidate_files(cited, source, index)
    names = tuple(_relative(path) for path in candidates)
    if not candidates:
        message = f"{at} no such file." if require_file else None
        return Outcome(relative, citation, False, require_file, None, names, message=message)

    regions: list[tuple[Path, str]] = []
    for path in candidates:
        lines = path.read_text(encoding="utf-8-sig", errors="replace").splitlines()
        if symbol is None:
            regions.append((path, "\n".join(lines)))
            continue
        if path.suffix != ".py":
            continue
        for start, end, _ in module_spans(path).get(symbol, ()):
            regions.append((path, "\n".join(lines[start - 1 : end])))
    if not regions:
        homes = tuple(symbol_homes(symbol or "", corpus))
        where = ", ".join(homes[:2]) if homes else "nowhere in the tree"
        message = f"{at} `{cited}` defines no `{symbol}`. Now lives in: {where}."
        return Outcome(relative, citation, False, True, None, names, homes, message)

    counts: dict[Path, int] = {}
    for path, region in regions:
        counts[path] = counts.get(path, 0) + region.count(substring)
    holding = [path for path, count in counts.items() if count]
    if not holding:
        scope = f"`{cited}::{symbol}`" if symbol else f"`{cited}`"
        hint = tuple(name for path in candidates for name in _enclosing_symbols(path, substring))
        where = ", ".join(hint[:2]) if hint else "nowhere in the cited file"
        message = f"{at} the quoted text does not occur in {scope}. Now lives in: {where}."
        return Outcome(relative, citation, False, True, None, names, hint, message)
    warning = None
    if all(counts[path] > 1 for path in holding):
        warning = (
            f"{at} the quoted text occurs {counts[holding[0]]} times in "
            f"`{_relative(holding[0])}`; a pinpoint should be unique."
        )
    return Outcome(relative, citation, True, False, _relative(holding[0]), names, warning=warning)


def evaluate_source(
    source: Path,
    corpus: Sequence[Path],
    index: dict[str, tuple[Path, ...]],
    *,
    require_file: bool,
    substrings: bool = False,
) -> list[Outcome]:
    """Return one ``Outcome`` per citation found in ``source``.

    Args:
        source: The file whose citations are checked.
        corpus: Every first-party ``.py`` file, for the "now lives in" hint.
        index: ``suffix_index`` over ``corpus``.
        require_file: Fail a citation whose file half resolves to nothing.
        substrings: Also check ``#"substring"`` pinpoints.

    Returns:
        The outcomes in source order.

    Raises:
        CitationCheckError: ``source`` cannot be read.
    """
    relative = _relative(source)
    try:
        text = source.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError) as error:
        raise CitationCheckError(f"{relative}: {error}") from error
    resolve = {KIND_SUBSTRING: _substring_outcome}
    return [
        resolve.get(citation.kind, _symbol_outcome)(
            citation,
            relative,
            source,
            corpus,
            index,
            require_file=require_file,
        )
        for citation in iter_citation_records(text, substrings=substrings)
    ]


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
    outcomes = evaluate_source(source, corpus, index, require_file=require_file)
    violations = [outcome.message for outcome in outcomes if outcome.message is not None]
    return violations, len(outcomes)


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
    scope = parser.add_mutually_exclusive_group()
    scope.add_argument(
        "--paths",
        nargs="+",
        metavar="PATH",
        help="Check only the citations in these files; resolution still uses the whole tree.",
    )
    scope.add_argument(
        "--cited-by",
        metavar="PATH[::Symbol]",
        help="List every citer of this path or symbol, gate corpus plus standing docs/.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print every citation as JSON on stdout; the summary line goes to stderr.",
    )
    parser.add_argument(
        "--substrings",
        action="store_true",
        help='Also check `path::Symbol #"text"` and `path #"text"` pinpoints.',
    )
    return parser.parse_args(argv)


def _named_sources(paths: Sequence[str]) -> list[tuple[Path, bool]]:
    """Resolve ``--paths`` into ``(file, require_file)`` pairs.

    Raises:
        CitationCheckError: A named path is missing or outside the repo.
    """
    named: list[tuple[Path, bool]] = []
    for raw in paths:
        path = _repo_path(raw)
        if not path.is_file():
            raise CitationCheckError(f"{raw}: no such file.")
        entry = (path, _relative(path) not in MARKDOWN_SOURCES)
        if entry not in named:
            named.append(entry)
    return named


def _repo_path(raw: str) -> Path:
    """Return ``raw`` as an absolute path inside the repo.

    Raises:
        CitationCheckError: ``raw`` lies outside the repo.
    """
    given = Path(raw)
    if given.is_absolute():
        path = given.resolve()
    elif (REPO_ROOT / given).exists() or not (Path.cwd() / given).exists():
        path = (REPO_ROOT / given).resolve()
    else:
        path = (Path.cwd() / given).resolve()
    root = REPO_ROOT.resolve()
    if not path.is_relative_to(root):
        raise CitationCheckError(f"{raw}: outside the repository at {REPO_ROOT}.")
    return REPO_ROOT / path.relative_to(root)


def _gate_sources(corpus: Sequence[Path]) -> list[tuple[Path, bool]]:
    """Return the CI corpus as ``(file, require_file)`` pairs.

    Raises:
        CitationCheckError: A gated markdown source is missing.
    """
    sources = [(path, True) for path in corpus if _relative(path) not in SYNTHETIC_SOURCES]
    for name in MARKDOWN_SOURCES:
        markdown = REPO_ROOT / name
        if not markdown.is_file():
            raise CitationCheckError(f"{name} is missing; the citation gate expects it.")
        sources.append((markdown, False))
    return sources


def _report(outcomes: Sequence[Outcome], scope: str, *, as_json: bool) -> int:
    """Print the check result and return its exit code."""
    violations = [outcome.message for outcome in outcomes if outcome.violation and outcome.message]
    warnings = [outcome.warning for outcome in outcomes if outcome.warning]
    checked = len(outcomes)
    if violations:
        summary = (
            f"FAIL: {len(violations)} unresolvable citation(s) of {checked} checked ({scope}):"
        )
    else:
        summary = f"OK: {checked} citations resolve ({scope})."
    if as_json:
        payload = {
            "checked": checked,
            "violations": len(violations),
            "warnings": len(warnings),
            "scope": scope,
            "citations": [outcome.as_json() for outcome in outcomes],
        }
        print(json.dumps(payload, indent=2))
        print(summary.removesuffix(":"), file=sys.stderr)
        return 1 if violations else 0
    print(summary)
    for violation in violations:
        print(f"  - {violation}")
    if warnings:
        print(f"WARN: {len(warnings)} ambiguous pinpoint(s):")
        for warning in warnings:
            print(f"  - {warning}")
    if violations:
        print(
            "\nFix: repoint the citation at the symbol's current home, or delete it. "
            "AGENTS.md rule 27 -- renaming a symbol means grep-sweeping `::OldName` in "
            "the same change.",
        )
        return 1
    return 0


def _parse_target(spec: str) -> tuple[Path, str, str | None]:
    """Split a ``--cited-by`` argument into ``(file, relative path, symbol)``.

    Raises:
        CitationCheckError: The symbol half is not a dotted identifier.
    """
    raw, separator, symbol = spec.partition("::")
    if separator and not re.fullmatch(r"[A-Za-z_][\w]*(\.[A-Za-z_][\w]*)*", symbol):
        raise CitationCheckError(f"{spec}: `::` must be followed by a dotted symbol name.")
    path = _repo_path(raw)
    return path, _relative(path), symbol or None


def _cites_target(
    citation: Citation,
    candidates: Sequence[Path],
    target: Path,
    relative: str,
    symbol: str | None,
) -> bool:
    """Return whether ``citation`` cites ``target`` (and ``symbol`` when given)."""
    if target.is_file():
        names_file = target in candidates
    else:
        # A deleted or moved target has no candidates; match its spelled path.
        names_file = relative == citation.cited or relative.endswith("/" + citation.cited)
    if not names_file:
        return False
    if symbol is None:
        return True
    if citation.symbol is not None:
        return citation.symbol == symbol or citation.symbol.startswith(symbol + ".")
    if citation.kind != KIND_SUBSTRING or target.suffix != ".py" or not target.is_file():
        return False
    lines = target.read_text(encoding="utf-8-sig", errors="replace").splitlines()
    return any(
        (citation.substring or "") in "\n".join(lines[start - 1 : end])
        for start, end, _ in module_spans(target).get(symbol, ())
    )


def cited_by(spec: str, *, as_json: bool) -> int:
    """Print every citer of ``spec`` (``PATH[::Symbol]``) and return ``0``.

    Args:
        spec: The cited path, optionally ``::`` and a dotted symbol.
        as_json: Print the rows as JSON on stdout, summary on stderr.

    Returns:
        ``0``; the listing is a query, not a gate.
    """
    target, relative, symbol = _parse_target(spec)
    corpus = iter_python_sources()
    index = suffix_index(corpus)
    sources = [(path, True, require) for path, require in _gate_sources(corpus)]
    sources.extend((path, False, True) for path in iter_standing_docs())
    rows: list[tuple[Outcome, bool]] = []
    for source, in_gate, require_file in sources:
        for outcome in evaluate_source(
            source,
            corpus,
            index,
            require_file=require_file,
            substrings=True,
        ):
            candidates = [REPO_ROOT / name for name in outcome.candidates]
            if _cites_target(outcome.citation, candidates, target, relative, symbol):
                rows.append((outcome, in_gate and outcome.citation.kind != KIND_SUBSTRING))
    gated = sum(1 for _, is_gated in rows if is_gated)
    unresolved = sum(1 for outcome, _ in rows if not outcome.resolved)
    summary = (
        f"{len(rows)} citing site(s) of `{spec}` ({gated} gated, {len(rows) - gated} "
        f"ungated, {unresolved} unresolved) across {len(sources)} file(s) searched."
    )
    if as_json:
        records = [{**outcome.as_json(), "gated": is_gated} for outcome, is_gated in rows]
        print(json.dumps({"target": spec, "citers": records}, indent=2))
        print(summary, file=sys.stderr)
        return 0
    for outcome, is_gated in rows:
        status = "resolved" if outcome.resolved else "unresolved"
        if len(outcome.candidates) > 1:
            status += f", ambiguous ({len(outcome.candidates)} candidates)"
        print(
            f"{outcome.source}:{outcome.citation.line}: `{outcome.citation.text}` "
            f"[{'gated' if is_gated else 'ungated'}] {status} ({outcome.citation.kind})",
        )
    print(summary)
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Sweep the corpus and report every citation whose target no longer exists."""
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if args.cited_by is not None:
        return cited_by(args.cited_by, as_json=args.json)
    corpus = iter_python_sources()
    if not corpus:
        raise CitationCheckError(f"No .py sources found under {REPO_ROOT}.")
    index = suffix_index(corpus)

    named = args.paths is not None
    sources = _named_sources(args.paths) if named else _gate_sources(corpus)
    outcomes: list[Outcome] = []
    python_checked = 0
    for source, require_file in sources:
        found = evaluate_source(
            source,
            corpus,
            index,
            require_file=require_file,
            substrings=args.substrings,
        )
        outcomes.extend(found)
        if source.suffix == ".py":
            python_checked += sum(1 for item in found if item.citation.kind != KIND_SUBSTRING)

    pinpoints = sum(1 for item in outcomes if item.citation.kind == KIND_SUBSTRING)
    if named:
        scope = f"{len(outcomes)} in {len(sources)} named file(s)"
    else:
        markdown_checked = len(outcomes) - pinpoints - python_checked
        scope = f"{python_checked} in {len(corpus)} .py files, {markdown_checked} in KANBAN.md"
    if args.substrings:
        scope += f"; {pinpoints} of them substring pinpoints"
    return _report(outcomes, scope, as_json=args.json)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except CitationCheckError as error:
        print(error, file=sys.stderr)
        raise SystemExit(2) from error
