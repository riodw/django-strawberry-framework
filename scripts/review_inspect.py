r"""Create static review aids for a Python source file.

The target file is parsed as text/AST only. It is never imported or executed,
so this helper is safe for files that touch Django settings, registries, or
Strawberry type creation at import time.

The generated shadow file (``<stem>.stripped.py``) strips comments and docstring
statements, then replaces remaining string-literal contents with ``...`` so review
passes can focus on executable structure. Every transformation is line-preserving:
line N of the shadow file is line N of the source, so a line number read from
either file names the same source line. Marker detection uses that stripped view
to avoid comment/docstring false positives, while rendered marker lines still cite
the original source text.

The overview (``<stem>.overview.md``) names every line-bearing row twice: by its
line number and by its enclosing symbol, ``path::Qualified.Name`` inside a class
or function and ``path #"<line text>"`` for a module-level line. Those are the
citation forms AGENTS.md rule 27 requires outside per-cycle scratch, so a row can
be copied into a review record as it stands. Two heuristic sections follow the
inventory sections:

* ``## Performance leads`` lists per-row work (a database-shaped call or an
  ``await`` inside a ``for`` / ``while`` body or a comprehension), the functions
  reachable from hot-looking entry points (heuristic stated in the section), and
  work executed at import time (module- and class-body calls, ``settings`` reads,
  regex compiles).
* ``## Comments census`` lists every comment block and docstring with its
  enclosing symbol, first line, and lead flags (provenance vocabulary, test
  docstring prefixes, public symbols without a docstring, first lines without a
  closing period, ``path:NN`` cites). ``path::Symbol`` cites are listed, never
  resolved; ``scripts/check_citations.py`` owns resolution.

Every lead is a pointer for a reviewer, never a finding.

``--json PATH`` writes the same overview as one JSON document: a ``header``
(repo-relative path, ``git hash-object`` blob id, line count, generation time),
every overview section, and a ``symbols`` table with per-function/method/class
metrics (code lines, nesting depth, parameters, ``await`` count, database-shaped
calls, per-row calls, first-party callees, and approximate package callers for
module-level symbols). With ``--all`` the document is ``{"header", "files": [...]}``.

Usage::

    uv run python scripts/review_inspect.py django_strawberry_framework/optimizer/walker.py \
        --output-dir <scratch>/inspect --json <scratch>/inspect/walker.json
    uv run python scripts/review_inspect.py --all --output-dir <scratch>/inspect \
        --json <scratch>/inspect/package.json

Row caps apply only to the single-file text overview; ``--no-cap`` lifts them and
``--all`` never caps. A capped section prints the hidden and total row counts.
Exit code ``0`` on success, ``1`` on a SyntaxError, ``2`` on a caller-correctable
error.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import io
import json
import re
import subprocess
import sys
import tokenize
from collections import Counter, deque
from collections.abc import Callable, Iterator, Sequence
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import NamedTuple

DEFAULT_MARKERS = (
    "QuerySet",
    "select_related",
    "prefetch_related",
    "Prefetch",
    "only",
    "_meta",
    "get_queryset",
    "_prefetched_objects_cache",
    "fields_cache",
    "DjangoType",
    "OptimizationPlan",
    "OptimizerHint",
    "dst_optimizer_plan",
    "field_map",
)
CONTROL_FLOW_NODES = (
    ast.If,
    ast.For,
    ast.AsyncFor,
    ast.While,
    ast.Try,
    ast.ExceptHandler,
    ast.With,
    ast.AsyncWith,
    ast.Match,
    ast.BoolOp,
    ast.IfExp,
)
CALLS_OF_INTEREST = {
    # Reflective access and container coercion calls are worth eyeballing in review output.
    "dict",
    "frozenset",
    "getattr",
    "hasattr",
    "isinstance",
    "issubclass",
    "iter",
    "len",
    "list",
    "set",
    "setattr",
    "tuple",
}
# Attribute calls treated as database-shaped wherever they appear. ``.get`` and
# ``.count`` are special-cased in ``_orm_reason`` so ``dict.get(key)`` and
# ``list.count(item)`` stay out.
ORM_CALL_ATTRS = frozenset(
    {
        "aggregate",
        "annotate",
        "bulk_create",
        "bulk_update",
        "create",
        "delete",
        "exclude",
        "exists",
        "filter",
        "first",
        "get_or_create",
        "in_bulk",
        "iterator",
        "last",
        "refresh_from_db",
        "save",
        "select_for_update",
        "update_or_create",
        "values_list",
    },
)
THREAD_HOP_CALLS = frozenset({"sync_to_async", "database_sync_to_async"})
# Module-level calls that only declare typing or container shape; everything else
# at module or class-body level is listed as import-time work.
DECLARATIVE_CALLS = frozenset(
    {
        "NamedTuple",
        "NewType",
        "ParamSpec",
        "TypeVar",
        "TypedDict",
        "cast",
        "dataclasses.field",
        "dict",
        "field",
        "frozenset",
        "list",
        "namedtuple",
        "set",
        "tuple",
    },
)
HOT_ENTRY_NAME = re.compile(
    r"^_*(?:a?resolve(?:_\w+)?|get_queryset|__call__|on_\w+|a?connect|a?disconnect"
    r"|a?receive(?:_json)?|websocket_\w+|http_\w+|\w*walk\w*)$",
)
HOT_ENTRY_DECORATORS = frozenset(
    {
        "field",
        "mutation",
        "subscription",
        "sync_to_async",
        "database_sync_to_async",
    },
)
HOT_PATH_HEURISTIC = (
    "Entry points: a name matching `resolve` / `resolve_*` / `aresolve*`, `get_queryset`, "
    "`__call__`, an `on_*` hook, a connection or consumer handler (`connect`, `disconnect`, "
    "`receive`, `receive_json`, `websocket_*`, `http_*`), or a name containing `walk`; a "
    "parameter named `info`; or a decorator named `field` / `mutation` / `subscription` / "
    "`sync_to_async` / `database_sync_to_async` or under `strawberry.`. Reachability follows "
    "calls to same-module functions by bare name and to `self.` / `cls.` methods of the "
    "enclosing class; calls through other objects or modules are not followed."
)
PROVENANCE_PATTERNS = {
    "spec-": re.compile(r"\bspec-", re.IGNORECASE),
    "card": re.compile(r"\bcards?\b", re.IGNORECASE),
    "round": re.compile(r"\brounds?\b", re.IGNORECASE),
    "worker": re.compile(r"\bworkers?\b", re.IGNORECASE),
    "legacy": re.compile(r"\blegacy\b", re.IGNORECASE),
    "moved from": re.compile(r"\bmoved from\b", re.IGNORECASE),
    "no longer": re.compile(r"\bno longer\b", re.IGNORECASE),
    "previously": re.compile(r"\bpreviously\b", re.IGNORECASE),
    "now": re.compile(r"\bnow\b", re.IGNORECASE),
    "fix for": re.compile(r"\bfix for\b", re.IGNORECASE),
    "we": re.compile(r"\bwe\b", re.IGNORECASE),
}
LINE_CITE = re.compile(r"[\w./-]+\.(?:py|md|toml|ini|cfg|txt|html|json|yml|yaml):\d+")
SYMBOL_CITE = re.compile(r"[\w./-]+\.py::[A-Za-z_][\w.]*")
TEST_DOCSTRING_PREFIXES = ("tests that", "ensures")
_FSTRING_START = getattr(tokenize, "FSTRING_START", -1)
_FSTRING_END = getattr(tokenize, "FSTRING_END", -1)
_ALL_TARGET_ROOT = Path("django_strawberry_framework")
# Markers that are common substrings inside unrelated identifiers need tighter
# matching; ``only`` still intentionally covers the optimizer's ``only_fields``.
_TOKEN_BOUNDARY_MARKERS = {
    "_meta": re.compile(r"(?<![A-Za-z0-9_])_meta(?![A-Za-z0-9_])"),
    "only": re.compile(r"(?<![A-Za-z0-9_])(?:only|only_fields)(?![A-Za-z0-9_])"),
    "Prefetch": re.compile(r"(?<![A-Za-z0-9_])Prefetch(?![A-Za-z0-9_])"),
}
_SCOPE_NODES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
_NESTED_SCOPES = (
    ast.FunctionDef,
    ast.AsyncFunctionDef,
    ast.ClassDef,
    ast.Lambda,
)
_COMPREHENSIONS = (
    ast.ListComp,
    ast.SetComp,
    ast.GeneratorExp,
    ast.DictComp,
)
_TRY_STAR = getattr(ast, "TryStar", ast.Try)
_BLOCK_STATEMENTS = (
    ast.If,
    ast.For,
    ast.AsyncFor,
    ast.While,
    ast.With,
    ast.AsyncWith,
    ast.Try,
    _TRY_STAR,
    ast.Match,
)
_BLOCK_CHILDREN = (ast.stmt, ast.excepthandler, ast.match_case)
_CiteFn = Callable[[int], str]
_DocstringOwner = ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef


@dataclass(frozen=True)
class _ImportRecord:
    """Import statement metadata."""

    lineno: int
    text: str
    category: str


@dataclass(frozen=True)
class _SymbolRecord:
    """Class/function metadata."""

    kind: str
    name: str
    lineno: int
    end_lineno: int
    parent: str
    args: str


@dataclass(frozen=True)
class _CallRecord:
    """Function-call metadata."""

    lineno: int
    name: str


@dataclass(frozen=True)
class _CommentRecord:
    """Comment metadata."""

    lineno: int
    text: str


@dataclass(frozen=True)
class _DocstringRecord:
    """Docstring metadata."""

    owner: str
    lineno: int
    end_lineno: int
    summary: str


@dataclass(frozen=True)
class _MarkerRecord:
    """Source-line marker metadata."""

    lineno: int
    marker: str
    text: str


@dataclass(frozen=True)
class _HotspotRecord:
    """Function complexity metadata."""

    lineno: int
    name: str
    lines: int
    branches: int


class _LineRange(NamedTuple):
    """Source line range."""

    start: int
    end: int


class _TokenRange(NamedTuple):
    """Source range occupied by a token or token group."""

    start_line: int
    start_col: int
    end_line: int
    end_col: int


@dataclass(frozen=True)
class _Scope:
    """A class or function definition with its qualified name and full span.

    ``start`` is the first decorator line (the def line when undecorated) so a
    decorator row is attributed to the symbol it decorates.
    """

    qualname: str
    kind: str
    node: ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef
    start: int
    end: int
    class_qualname: str | None
    in_function: bool

    @property
    def is_public(self) -> bool:
        """Return whether every name segment is public and no function encloses it."""
        if self.in_function:
            return False
        return all(
            not part.startswith("_") or (part.startswith("__") and part.endswith("__"))
            for part in self.qualname.split(".")
        )

    @property
    def is_function(self) -> bool:
        """Return whether the scope is a function or method."""
        return not isinstance(self.node, ast.ClassDef)


@dataclass(frozen=True)
class _Loop:
    """Enclosing per-iteration context of a node."""

    kind: str
    lineno: int


@dataclass(frozen=True)
class _Lead:
    """A database-shaped call or ``await`` found inside a scope."""

    lineno: int
    call: str
    reason: str
    loop: _Loop | None


@dataclass
class _SymbolMetrics:
    """Per-symbol metrics for the JSON ``symbols`` table."""

    scope: _Scope
    docstring: str | None
    code_lines: int
    max_nesting_depth: int
    parameter_count: int
    positional_boolean_params: list[str]
    await_count: int
    db_calls: list[_Lead]
    per_row: list[_Lead]
    first_party_calls: list[str]
    local_callees: list[str]
    decorators: list[str]
    hot_reasons: list[str]
    callers: list[str] | None = None


@dataclass(frozen=True)
class _ImportTimeRecord:
    """A piece of work that runs when the module is imported."""

    lineno: int
    kind: str
    text: str


@dataclass(frozen=True)
class _CensusEntry:
    """One comment block, docstring, or missing public docstring."""

    kind: str
    lineno: int
    end_lineno: int
    owner: str | None
    first_line: str
    flags: dict[str, list[str]] = field(default_factory=dict)


class _Locator:
    """Map a source line to its innermost enclosing symbol and a citation string."""

    def __init__(
        self,
        rel_path: str,
        scopes: Sequence[_Scope],
        source_lines: Sequence[str],
    ) -> None:
        self.rel_path = rel_path
        self.source_lines = source_lines
        self._innermost: list[_Scope | None] = [None] * (len(source_lines) + 2)
        # Fill widest spans first so each line ends on its innermost scope.
        for scope in sorted(scopes, key=lambda item: item.end - item.start, reverse=True):
            for line in range(scope.start, min(scope.end, len(source_lines)) + 1):
                self._innermost[line] = scope

    def scope_at(self, lineno: int) -> _Scope | None:
        """Return the innermost class or function containing ``lineno``."""
        if 0 < lineno < len(self._innermost):
            return self._innermost[lineno]
        return None

    def symbol_cite(self, qualname: str) -> str:
        """Return ``path::qualname``."""
        return f"{self.rel_path}::{qualname}"

    def cite(self, lineno: int) -> str:
        """Return ``path::Qualified.Name`` or ``path #"<line text>"`` for ``lineno``."""
        scope = self.scope_at(lineno)
        if scope is not None:
            return self.symbol_cite(scope.qualname)
        return f'{self.rel_path} #"{self.line_text(lineno)}"'

    def line_text(self, lineno: int) -> str:
        """Return the longest double-quote-free piece of the stripped source line."""
        text = (
            self.source_lines[lineno - 1].strip() if 0 < lineno <= len(self.source_lines) else ""
        )
        if '"' not in text:
            return text
        return max((piece.strip() for piece in text.split('"')), key=len)


class _StaticVisitor(ast.NodeVisitor):
    """Collect static review metadata from an AST."""

    def __init__(
        self,
        source_lines: Sequence[str],
        long_function_lines: int,
        long_function_branches: int,
        markers: Sequence[str],
        first_party_prefixes: Sequence[str],
        literal_min_length: int,
    ) -> None:
        self.source_lines = source_lines
        self.long_function_lines = long_function_lines
        self.long_function_branches = long_function_branches
        self.markers = tuple(markers)
        self.first_party_prefixes = tuple(first_party_prefixes)
        self.literal_min_length = literal_min_length
        self.imports: list[_ImportRecord] = []
        self.symbols: list[_SymbolRecord] = []
        self.calls: list[_CallRecord] = []
        self.docstrings: list[_DocstringRecord] = []
        self.hotspots: list[_HotspotRecord] = []
        self.duplicate_literals: Counter[str] = Counter()
        self._parent_stack: list[str] = []

    def visit_Module(self, node: ast.Module) -> None:
        """Record the module docstring and then visit the module body."""
        self._record_docstring(node, "<module>")
        self._visit_children_excluding_docstring(node)

    def visit_Import(self, node: ast.Import) -> None:
        """Record an import statement."""
        names = ", ".join(
            alias.name if alias.asname is None else f"{alias.name} as {alias.asname}"
            for alias in node.names
        )
        self.imports.append(
            _ImportRecord(node.lineno, f"import {names}", self._categorize_import(names)),
        )
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Record a from-import statement."""
        module = "." * node.level + (node.module or "")
        names = ", ".join(
            alias.name if alias.asname is None else f"{alias.name} as {alias.asname}"
            for alias in node.names
        )
        self.imports.append(
            _ImportRecord(
                node.lineno,
                f"from {module} import {names}",
                self._categorize_import(module),
            ),
        )
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Record a class and then visit its body."""
        self._record_symbol("class", node, "")
        self._record_docstring(node, ".".join([*self._parent_stack, node.name]))
        self._parent_stack.append(node.name)
        self._visit_children_excluding_docstring(node)
        self._parent_stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Record a function and then visit its body."""
        self._visit_function("def", node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Record an async function and then visit its body."""
        self._visit_function("async def", node)

    def visit_Call(self, node: ast.Call) -> None:
        """Record a function call."""
        name = _call_name(node.func)
        if name is not None:
            self.calls.append(_CallRecord(node.lineno, name))
        self.generic_visit(node)

    def visit_Constant(self, node: ast.Constant) -> None:
        """Record duplicate string literals."""
        if isinstance(node.value, str):
            stripped = node.value.strip()
            if len(stripped) >= self.literal_min_length and stripped not in self.markers:
                self.duplicate_literals[stripped] += 1
        self.generic_visit(node)

    def _visit_function(self, kind: str, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        args = _format_args(node.args)
        self._record_symbol(kind, node, args)
        qualified_name = ".".join([*self._parent_stack, node.name])
        self._record_docstring(node, qualified_name)
        self._record_hotspot(node, qualified_name)
        self._parent_stack.append(node.name)
        self._visit_children_excluding_docstring(node)
        self._parent_stack.pop()

    def _record_symbol(
        self,
        kind: str,
        node: ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef,
        args: str,
    ) -> None:
        parent = ".".join(self._parent_stack)
        end_lineno = node.end_lineno or node.lineno
        self.symbols.append(_SymbolRecord(kind, node.name, node.lineno, end_lineno, parent, args))

    def _record_docstring(
        self,
        node: ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef,
        owner: str,
    ) -> None:
        expr = _docstring_expr(node)
        if expr is None:
            return
        value = ast.get_docstring(node, clean=True) or ""
        summary = value.splitlines()[0] if value else ""
        self.docstrings.append(
            _DocstringRecord(owner, expr.lineno, expr.end_lineno or expr.lineno, summary),
        )

    def _record_hotspot(self, node: ast.FunctionDef | ast.AsyncFunctionDef, name: str) -> None:
        end_lineno = node.end_lineno or node.lineno
        line_count = end_lineno - node.lineno + 1
        branch_count = _branch_count_excluding_nested(node)
        if line_count >= self.long_function_lines or branch_count >= self.long_function_branches:
            self.hotspots.append(_HotspotRecord(node.lineno, name, line_count, branch_count))

    def _visit_children_excluding_docstring(
        self,
        node: ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef,
    ) -> None:
        docstring = _docstring_expr(node)
        for child in ast.iter_child_nodes(node):
            if child is docstring:
                continue
            self.visit(child)

    def _categorize_import(self, module_or_names: str) -> str:
        if module_or_names.startswith("."):
            return "local"
        if module_or_names.startswith(self.first_party_prefixes):
            return "first-party"
        if module_or_names.startswith("django"):
            return "django"
        if module_or_names.startswith("strawberry"):
            return "strawberry"
        return "standard/third-party"


def _branch_count_excluding_nested(node: ast.FunctionDef | ast.AsyncFunctionDef) -> int:
    """Count branch nodes in a function without double-counting nested helpers."""
    branch_count = 0
    stack = list(ast.iter_child_nodes(node))
    while stack:
        child = stack.pop()
        if isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef | ast.Lambda | ast.ClassDef):
            continue
        if isinstance(child, CONTROL_FLOW_NODES):
            branch_count += 1
        stack.extend(ast.iter_child_nodes(child))
    return branch_count


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate static review aids for Python files without importing them.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("target", nargs="?", type=Path, help="Python file to inspect.")
    parser.add_argument(
        "--all",
        action="store_true",
        help="Inspect every .py file under django_strawberry_framework/ recursively (never capped).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("docs/shadow"),
        help="Directory for generated shadow and overview files.",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="Root used to compute stable output names, cited paths and the package root.",
    )
    parser.add_argument(
        "--outline-only",
        action="store_true",
        help="Write only imports, symbols, hotspots, and marker sections in the overview.",
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Print the overview to stdout in addition to writing output files.",
    )
    parser.add_argument(
        "--no-cap",
        action="store_true",
        help="List every row in capped sections instead of a '... more not shown' notice.",
    )
    parser.add_argument(
        "--json",
        type=Path,
        default=None,
        help="Also write the overview and the per-symbol table as JSON to this path.",
    )
    parser.add_argument(
        "--long-function-lines",
        type=int,
        default=40,
        help="Line-count threshold for reporting long functions.",
    )
    parser.add_argument(
        "--long-function-branches",
        type=int,
        default=8,
        help="Branch-count threshold for reporting branchy functions.",
    )
    parser.add_argument(
        "--marker",
        action="append",
        default=[],
        help="Additional source marker to include in the Django/ORM marker table. May be repeated.",
    )
    parser.add_argument(
        "--first-party-prefix",
        action="append",
        default=["django_strawberry_framework"],
        help="Import prefix treated as first-party. May be repeated.",
    )
    parser.add_argument(
        "--literal-min-length",
        type=int,
        default=8,
        help="Minimum string-literal length before duplicate-literal reporting.",
    )
    return parser.parse_args(argv)


def _stable_stem(path: Path, root: Path) -> str:
    target = path.resolve()
    resolved_root = root.resolve()
    try:
        relative = target.relative_to(resolved_root)
    except ValueError:
        relative = Path(target.name)
    without_suffix = relative.with_suffix("") if relative.suffix == ".py" else relative
    return "__".join(without_suffix.parts)


def _relative_path(path: Path, root: Path) -> str:
    """Return ``path`` relative to ``root`` in posix form, or its bare name outside it."""
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.name


def _strip_comments(source: str) -> str:
    tokens: list[tokenize.TokenInfo] = []
    reader = io.StringIO(source).readline
    for token in tokenize.generate_tokens(reader):
        if token.type == tokenize.COMMENT:
            continue
        tokens.append(token)
    rebuilt = tokenize.untokenize(tokens)
    # ``tokenize.untokenize`` preserves the (row, col) positions of tokens
    # that follow a removed comment by padding with spaces.  That leaves
    # comment-only lines as runs of spaces and code lines that had a
    # trailing inline comment with a long run of trailing spaces.  Strip
    # each line so comment-only lines render as true blank lines and
    # inline-comment removal does not leave whitespace garbage.  Rebuilding
    # line-for-line preserves line numbers.
    return "\n".join(line.rstrip() for line in rebuilt.split("\n"))


def _strip_string_literals(source: str) -> str:
    """Replace string literal tokens with ``...`` in a shadow source file.

    The helper intentionally preserves operators, names, and container shape:
    ``__all__ = ("A", "B")`` becomes ``__all__ = (..., ...)`` instead of
    losing the tuple structure. Multiline strings keep the original line count
    by replacing the first line with ``...`` and blanking the remaining span.
    """
    lines = source.splitlines(keepends=True)
    ranges: list[_TokenRange] = []
    reader = io.StringIO(source).readline
    fstring_depth = 0
    fstring_start: tuple[int, int] | None = None
    for token in tokenize.generate_tokens(reader):
        if token.type == tokenize.STRING:
            ranges.append(_TokenRange(token.start[0], token.start[1], token.end[0], token.end[1]))
            continue
        if token.type == _FSTRING_START:
            if fstring_depth == 0:
                fstring_start = token.start
            fstring_depth += 1
            continue
        if fstring_depth:
            if token.type == _FSTRING_START:
                fstring_depth += 1
            elif token.type == _FSTRING_END:
                fstring_depth -= 1
                if fstring_depth == 0 and fstring_start is not None:
                    ranges.append(
                        _TokenRange(
                            fstring_start[0],
                            fstring_start[1],
                            token.end[0],
                            token.end[1],
                        ),
                    )
                    fstring_start = None
            continue
    for token_range in sorted(ranges, reverse=True):
        _replace_range_with_ellipsis(lines, token_range)
    return "".join(lines)


def _replace_range_with_ellipsis(lines: list[str], token_range: _TokenRange) -> None:
    """Replace ``token_range`` in ``lines`` with ``...`` while preserving line count."""
    start_index = token_range.start_line - 1
    end_index = token_range.end_line - 1
    if start_index == end_index:
        lines[start_index] = (
            f"{lines[start_index][: token_range.start_col]}...{lines[start_index][token_range.end_col :]}"
        )
        return

    suffix = lines[end_index][token_range.end_col :]
    lines[start_index] = f"{lines[start_index][: token_range.start_col]}...{suffix}"
    for index in range(start_index + 1, end_index + 1):
        lines[index] = "\n" if lines[index].endswith("\n") else ""


def _remove_docstring_statements(source: str, tree: ast.AST) -> str:
    ranges = _docstring_statement_ranges(tree)
    if not ranges:
        return source

    lines = source.splitlines(keepends=True)
    for line_range in ranges:
        for index in range(line_range.start - 1, line_range.end):
            if 0 <= index < len(lines):
                lines[index] = "\n" if lines[index].endswith("\n") else ""
    return "".join(lines)


def _docstring_statement_ranges(tree: ast.AST) -> list[_LineRange]:
    ranges: list[_LineRange] = []
    for node in ast.walk(tree):
        if not isinstance(
            node,
            ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef,
        ):
            continue
        expr = _docstring_expr(node)
        if expr is not None:
            ranges.append(_LineRange(expr.lineno, expr.end_lineno or expr.lineno))
    return ranges


def _docstring_expr(
    node: ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef,
) -> ast.Expr | None:
    if not node.body:
        return None
    first = node.body[0]
    if not isinstance(first, ast.Expr):
        return None
    if isinstance(first.value, ast.Constant) and isinstance(first.value.value, str):
        return first
    return None


def _comments(source: str) -> list[_CommentRecord]:
    records: list[_CommentRecord] = []
    reader = io.StringIO(source).readline
    for token in tokenize.generate_tokens(reader):
        if token.type == tokenize.COMMENT:
            records.append(_CommentRecord(token.start[0], token.string.strip()))
    return records


def _markers(
    source_lines: Sequence[str],
    marker_lines: Sequence[str],
    markers: Sequence[str],
) -> list[_MarkerRecord]:
    records: list[_MarkerRecord] = []
    for lineno, marker_line in enumerate(marker_lines, start=1):
        if not marker_line.strip():
            continue
        source_line = source_lines[lineno - 1] if lineno <= len(source_lines) else marker_line
        for marker in markers:
            if _marker_matches(marker_line, marker):
                records.append(_MarkerRecord(lineno, marker, source_line.strip()))
    return records


def _marker_matches(line: str, marker: str) -> bool:
    pattern = _TOKEN_BOUNDARY_MARKERS.get(marker)
    if pattern is not None:
        return pattern.search(line) is not None
    return marker in line


def _call_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _call_name(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    if isinstance(node, ast.Call):
        return _call_name(node.func)
    return None


def _format_args(arguments: ast.arguments) -> str:
    names = [arg.arg for arg in arguments.posonlyargs]
    names.extend(arg.arg for arg in arguments.args)
    if arguments.vararg is not None:
        names.append(f"*{arguments.vararg.arg}")
    names.extend(arg.arg for arg in arguments.kwonlyargs)
    if arguments.kwarg is not None:
        names.append(f"**{arguments.kwarg.arg}")
    return ", ".join(names)


# --- Symbol scopes and scope-local walking -------------------------------------------


def _collect_scopes(tree: ast.Module) -> list[_Scope]:
    """Return every class and function definition in definition order."""
    scopes: list[_Scope] = []

    def visit(
        body: Sequence[ast.stmt],
        prefix: str,
        class_qualname: str | None,
        in_function: bool,
    ) -> None:
        for node in body:
            if isinstance(node, _SCOPE_NODES):
                qualname = f"{prefix}{node.name}"
                start = min([node.lineno, *(item.lineno for item in node.decorator_list)])
                scopes.append(
                    _Scope(
                        qualname=qualname,
                        kind=_scope_kind(node, class_qualname is not None and not in_function),
                        node=node,
                        start=start,
                        end=node.end_lineno or node.lineno,
                        class_qualname=class_qualname if not in_function else None,
                        in_function=in_function,
                    ),
                )
                is_class = isinstance(node, ast.ClassDef)
                visit(
                    node.body,
                    f"{qualname}.",
                    qualname if is_class else None,
                    in_function or not is_class,
                )
            else:
                visit(_nested_statements(node), prefix, class_qualname, in_function)

    visit(tree.body, "", None, False)
    return scopes


def _nested_statements(node: ast.AST) -> list[ast.stmt]:
    """Return statements nested in a compound statement's blocks (not in nested scopes)."""
    statements: list[ast.stmt] = []
    for name in ("body", "orelse", "finalbody"):
        statements.extend(getattr(node, name, None) or [])
    for handler in getattr(node, "handlers", None) or []:
        statements.extend(handler.body)
    for case in getattr(node, "cases", None) or []:
        statements.extend(case.body)
    return [statement for statement in statements if isinstance(statement, ast.stmt)]


def _scope_kind(node: ast.AST, is_method: bool) -> str:
    if isinstance(node, ast.ClassDef):
        return "class"
    prefix = "async " if isinstance(node, ast.AsyncFunctionDef) else ""
    return f"{prefix}{'method' if is_method else 'function'}"


def _walk_scope(
    node: ast.AST,
    loops: tuple[_Loop, ...] = (),
    depth: int = 0,
) -> Iterator[tuple[ast.AST, tuple[_Loop, ...], int]]:
    """Yield descendants of ``node`` in its own scope with enclosing loops and block depth.

    Nested functions, classes and lambdas are not entered. A ``for`` iterable and
    the first comprehension iterable are evaluated once, so they carry the outer
    loops; a loop body, a ``while`` test, comprehension conditions, later
    comprehension iterables and the element expression run per iteration.
    """
    if isinstance(node, _COMPREHENSIONS):
        inner = (*loops, _Loop("comprehension", node.lineno))
        for index, generator in enumerate(node.generators):
            yield from _walk_child(generator.iter, inner if index else loops, depth)
            yield from _walk_child(generator.target, inner, depth)
            for condition in generator.ifs:
                yield from _walk_child(condition, inner, depth)
        for name in ("elt", "key", "value"):
            value = getattr(node, name, None)
            if isinstance(value, ast.AST):
                yield from _walk_child(value, inner, depth)
        return
    for name, value in ast.iter_fields(node):
        children = value if isinstance(value, list) else [value]
        for child in children:
            if not isinstance(child, ast.AST):
                continue
            child_loops = loops
            if isinstance(node, ast.For | ast.AsyncFor) and name == "body":
                kind = "async for" if isinstance(node, ast.AsyncFor) else "for"
                child_loops = (*loops, _Loop(kind, node.lineno))
            elif isinstance(node, ast.While) and name in {"test", "body"}:
                child_loops = (*loops, _Loop("while", node.lineno))
            child_depth = depth
            if isinstance(node, _BLOCK_STATEMENTS) and isinstance(child, _BLOCK_CHILDREN):
                child_depth = depth + 1
            yield from _walk_child(child, child_loops, child_depth)


def _walk_child(
    node: ast.AST,
    loops: tuple[_Loop, ...],
    depth: int,
) -> Iterator[tuple[ast.AST, tuple[_Loop, ...], int]]:
    if isinstance(node, _NESTED_SCOPES):
        return
    yield node, loops, depth
    yield from _walk_scope(node, loops, depth)


def _walk_body(body: Sequence[ast.stmt]) -> Iterator[tuple[ast.AST, tuple[_Loop, ...], int]]:
    for statement in body:
        yield from _walk_child(statement, (), 0)


# --- Call classification --------------------------------------------------------------


def _orm_reason(call: ast.Call) -> str | None:
    """Return ``orm:<shape>`` when ``call`` is database-shaped by name and arity."""
    func = call.func
    if isinstance(func, ast.Attribute):
        if func.attr in ORM_CALL_ATTRS:
            return f"orm:.{func.attr}"
        if func.attr == "get" and (call.keywords or not call.args):
            return "orm:.get"
        if func.attr == "count" and not call.args and not call.keywords:
            return "orm:.count"
    name = _call_name(func) or ""
    if "objects" in name.split(".")[:-1]:
        return "orm:objects."
    return None


def _db_reason(call: ast.Call, markers: Sequence[str]) -> str | None:
    """Return why ``call`` counts as database work, or ``None``.

    ORM shapes (``ORM_CALL_ATTRS``, ``.get`` with keywords or no arguments, ``.count()``
    with no arguments, anything through ``objects.``), thread hops into the ORM
    (``sync_to_async``), then marker hits on the dotted call name.
    """
    reason = _orm_reason(call)
    if reason is not None:
        return reason
    name = _call_name(call.func)
    if name is None:
        return None
    if name.split(".")[-1] in THREAD_HOP_CALLS:
        return "thread-hop"
    for marker in markers:
        if _marker_matches(name, marker):
            return f"marker:{marker}"
    return None


def _decorator_names(node: ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef) -> list[str]:
    names = []
    for decorator in node.decorator_list:
        target = decorator.func if isinstance(decorator, ast.Call) else decorator
        names.append(_call_name(target) or ast.unparse(target))
    return names


def _hot_reasons(scope: _Scope) -> list[str]:
    if not scope.is_function:
        return []
    node = scope.node
    reasons = []
    if HOT_ENTRY_NAME.match(node.name):
        reasons.append(f"name `{node.name}`")
    arguments = node.args
    all_args = [*arguments.posonlyargs, *arguments.args, *arguments.kwonlyargs]
    if any(arg.arg == "info" for arg in all_args):
        reasons.append("`info` parameter")
    for decorator in _decorator_names(node):
        parts = decorator.split(".")
        if parts[-1] in HOT_ENTRY_DECORATORS or parts[0] == "strawberry":
            reasons.append(f"decorator `@{decorator}`")
    return reasons


def _is_bool_annotation(annotation: ast.expr | None) -> bool:
    if isinstance(annotation, ast.Name):
        return annotation.id == "bool"
    if isinstance(annotation, ast.Constant):
        return annotation.value == "bool"
    return False


def _positional_boolean_params(arguments: ast.arguments) -> list[str]:
    positional = [*arguments.posonlyargs, *arguments.args]
    defaults: list[ast.expr | None] = [None] * (len(positional) - len(arguments.defaults))
    defaults.extend(arguments.defaults)
    return [
        arg.arg
        for arg, default in zip(positional, defaults, strict=True)
        if _is_bool_annotation(arg.annotation)
        or (isinstance(default, ast.Constant) and isinstance(default.value, bool))
    ]


def _parameter_count(scope: _Scope) -> int:
    """Count parameters, excluding a method's leading ``self`` / ``cls``."""
    arguments = scope.node.args
    names = [arg.arg for arg in (*arguments.posonlyargs, *arguments.args)]
    if scope.kind.endswith("method") and names and names[0] in {"self", "cls"}:
        names = names[1:]
    count = len(names) + len(arguments.kwonlyargs)
    count += arguments.vararg is not None
    count += arguments.kwarg is not None
    return count


class _FirstPartyNames(NamedTuple):
    """Names a module can call that resolve inside the first-party package."""

    module_defs: frozenset[str]
    imported: dict[str, str]
    qualnames: frozenset[str]


def _first_party_names(
    tree: ast.Module,
    scopes: Sequence[_Scope],
    prefixes: Sequence[str],
) -> _FirstPartyNames:
    imported: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            module = "." * node.level + (node.module or "")
            if node.level or module.startswith(tuple(prefixes)):
                for alias in node.names:
                    imported[alias.asname or alias.name] = module
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith(tuple(prefixes)):
                    imported[alias.asname or alias.name.split(".")[0]] = alias.name
    module_defs = frozenset(
        scope.qualname for scope in scopes if "." not in scope.qualname and not scope.in_function
    )
    return _FirstPartyNames(module_defs, imported, frozenset(scope.qualname for scope in scopes))


def _resolve_call(
    name: str,
    scope: _Scope,
    names: _FirstPartyNames,
) -> tuple[str | None, str | None]:
    """Return ``(display, local qualname)`` for a first-party call target."""
    parts = name.split(".")
    head = parts[0]
    if head in {"self", "cls"} and len(parts) >= 2 and scope.class_qualname:
        candidate = f"{scope.class_qualname}.{parts[1]}"
        if candidate in names.qualnames:
            return name, candidate
        return None, None
    if head in names.module_defs:
        local = name if name in names.qualnames else head
        return name, local if local in names.qualnames else None
    if head in names.imported:
        return f"{name} (from {names.imported[head]})", None
    return None, None


def _symbol_metrics(
    scope: _Scope,
    stripped_lines: Sequence[str],
    markers: Sequence[str],
    names: _FirstPartyNames,
) -> _SymbolMetrics:
    node = scope.node
    docstring = ast.get_docstring(node, clean=True)
    code_lines = sum(1 for line in stripped_lines[scope.start - 1 : scope.end] if line.strip())
    max_depth = 0
    awaits = 0
    db_calls: list[_Lead] = []
    per_row: list[_Lead] = []
    first_party: dict[str, None] = {}
    local_callees: dict[str, None] = {}
    handled_calls: set[int] = set()
    for child, loops, depth in _walk_body(node.body):
        if isinstance(child, ast.stmt):
            max_depth = max(max_depth, depth)
        loop = loops[-1] if loops else None
        if isinstance(child, ast.Await):
            awaits += 1
            awaited = child.value
            label = _call_name(awaited.func) if isinstance(awaited, ast.Call) else None
            reason = "await"
            if isinstance(awaited, ast.Call):
                db = _db_reason(awaited, markers)
                if db is not None:
                    reason = f"await+{db}"
                    db_calls.append(_Lead(awaited.lineno, label or "?", db, loop))
                    handled_calls.add(id(awaited))
            if loop is not None:
                per_row.append(
                    _Lead(child.lineno, f"await {label or ast.unparse(awaited)}", reason, loop),
                )
        elif isinstance(child, ast.Call):
            name = _call_name(child.func)
            if name is not None:
                display, local = _resolve_call(name, scope, names)
                if display is not None:
                    first_party[display] = None
                if local is not None and local != scope.qualname:
                    local_callees[local] = None
            if id(child) in handled_calls:
                continue
            db = _db_reason(child, markers)
            if db is not None:
                db_calls.append(_Lead(child.lineno, name or "?", db, loop))
                if loop is not None:
                    per_row.append(_Lead(child.lineno, name or "?", db, loop))
    is_function = scope.is_function
    return _SymbolMetrics(
        scope=scope,
        docstring=docstring,
        code_lines=code_lines,
        max_nesting_depth=max_depth,
        parameter_count=_parameter_count(scope) if is_function else 0,
        positional_boolean_params=_positional_boolean_params(node.args) if is_function else [],
        await_count=awaits,
        db_calls=db_calls,
        per_row=per_row,
        first_party_calls=sorted(first_party),
        local_callees=list(local_callees),
        decorators=_decorator_names(node),
        hot_reasons=_hot_reasons(scope),
    )


# --- Package-wide reference index (approximate callers) -------------------------------


class _ReferenceIndex:
    """Name and attribute references across the package, keyed by basename.

    Static and approximate: any ``Name``, ``Attribute`` or imported alias whose
    basename matches counts, whatever object it resolves to at runtime.
    """

    def __init__(self, package_root: Path, root: Path) -> None:
        self.package_root = package_root
        self.sites: dict[str, list[tuple[str, int, str]]] = {}
        if not package_root.is_dir():
            return
        for path in sorted(package_root.rglob("*.py")):
            source = path.read_text(encoding="utf-8")
            try:
                tree = ast.parse(source, filename=str(path))
            except SyntaxError:
                continue
            rel_path = _relative_path(path, root)
            locator = _Locator(rel_path, _collect_scopes(tree), source.splitlines())
            for node in ast.walk(tree):
                if isinstance(node, ast.Name):
                    self._add(node.id, rel_path, node.lineno, locator)
                elif isinstance(node, ast.Attribute):
                    self._add(node.attr, rel_path, node.lineno, locator)
                elif isinstance(node, ast.ImportFrom):
                    for alias in node.names:
                        self._add(alias.name, rel_path, node.lineno, locator)

    def _add(
        self,
        name: str,
        rel_path: str,
        lineno: int,
        locator: _Locator,
    ) -> None:
        self.sites.setdefault(name, []).append((rel_path, lineno, locator.cite(lineno)))

    def callers(self, scope: _Scope, rel_path: str) -> list[str]:
        """Return deduplicated reference sites of ``scope`` outside its own span."""
        found: dict[str, None] = {}
        for site_path, lineno, where in self.sites.get(scope.node.name, []):
            if site_path == rel_path and scope.start <= lineno <= scope.end:
                continue
            found[where] = None
        return list(found)


# --- Performance leads ----------------------------------------------------------------


def _is_type_checking_if(node: ast.stmt) -> bool:
    if not isinstance(node, ast.If):
        return False
    test = node.test
    name = _call_name(test) if isinstance(test, ast.Name | ast.Attribute) else None
    return name is not None and name.split(".")[-1] == "TYPE_CHECKING"


def _import_time_statements(body: Sequence[ast.stmt]) -> Iterator[ast.stmt]:
    """Yield statements executed at import: module level and class bodies, not defs."""
    for statement in body:
        if isinstance(statement, ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        if isinstance(statement, ast.ClassDef):
            yield from _import_time_statements(statement.body)
            continue
        if _is_type_checking_if(statement):
            yield from _import_time_statements(statement.orelse)
            continue
        yield statement


def _import_time_work(tree: ast.Module) -> list[_ImportTimeRecord]:
    records: dict[tuple[int, str, str], None] = {}
    for statement in _import_time_statements(tree.body):
        for node, _loops, _depth in _walk_child(statement, (), 0):
            if isinstance(node, ast.Call):
                name = _call_name(node.func) or ast.unparse(node.func)
                if name in {"re.compile", "regex.compile"}:
                    records[(node.lineno, "regex-compile", name)] = None
                elif any(
                    isinstance(arg, ast.Name) and arg.id == "settings"
                    for arg in [*node.args, *(keyword.value for keyword in node.keywords)]
                ):
                    records[(node.lineno, "settings-read", name)] = None
                elif name not in DECLARATIVE_CALLS:
                    records[(node.lineno, "call", name)] = None
            elif (
                isinstance(node, ast.Attribute)
                and isinstance(node.value, ast.Name)
                and node.value.id == "settings"
            ):
                records[(node.lineno, "settings-read", f"settings.{node.attr}")] = None
    return [
        _ImportTimeRecord(lineno, kind, text)
        for lineno, kind, text in sorted(records, key=lambda item: item[0])
    ]


def _module_per_row(tree: ast.Module, markers: Sequence[str]) -> list[_Lead]:
    """Return per-row leads in module-level and class-body code."""
    leads = []
    for statement in _import_time_statements(tree.body):
        for node, loops, _depth in _walk_child(statement, (), 0):
            if not loops:
                continue
            if isinstance(node, ast.Await):
                leads.append(
                    _Lead(node.lineno, f"await {ast.unparse(node.value)}", "await", loops[-1]),
                )
            elif isinstance(node, ast.Call):
                reason = _db_reason(node, markers)
                if reason is not None:
                    leads.append(
                        _Lead(node.lineno, _call_name(node.func) or "?", reason, loops[-1]),
                    )
    return leads


def _hot_reachability(
    metrics: Sequence[_SymbolMetrics],
) -> tuple[list[_SymbolMetrics], dict[str, str]]:
    """Return hot entry points and ``{reachable qualname: entry qualname}``."""
    by_name = {item.scope.qualname: item for item in metrics}
    entries = [item for item in metrics if item.hot_reasons]
    reached: dict[str, str] = {}
    for entry in entries:
        queue = deque(entry.local_callees)
        while queue:
            qualname = queue.popleft()
            target = by_name.get(qualname)
            if target is None or not target.scope.is_function:
                continue
            if qualname in reached or target.hot_reasons:
                continue
            reached[qualname] = entry.scope.qualname
            queue.extend(target.local_callees)
    return entries, reached


# --- Comments census ------------------------------------------------------------------


def _comment_blocks(source: str) -> list[tuple[int, int, list[str]]]:
    """Group comments into blocks: consecutive full-line comments merge; inline ones stand alone."""
    source_lines = source.splitlines()
    blocks: list[tuple[int, int, list[str]]] = []
    previous_full_line = -2
    for token in tokenize.generate_tokens(io.StringIO(source).readline):
        if token.type != tokenize.COMMENT:
            continue
        lineno, col = token.start
        text = token.string.lstrip("#").strip()
        full_line = not source_lines[lineno - 1][:col].strip()
        if full_line and blocks and previous_full_line == lineno - 1:
            start, _end, texts = blocks[-1]
            blocks[-1] = (start, lineno, [*texts, text])
        else:
            blocks.append((lineno, lineno, [text]))
        previous_full_line = lineno if full_line else -2
    return blocks


def _text_flags(text: str) -> dict[str, list[str]]:
    flags: dict[str, list[str]] = {}
    provenance = [label for label, pattern in PROVENANCE_PATTERNS.items() if pattern.search(text)]
    if provenance:
        flags["provenance"] = provenance
    line_cites = LINE_CITE.findall(text)
    if line_cites:
        flags["line-cite"] = line_cites
    symbol_cites = SYMBOL_CITE.findall(text)
    if symbol_cites:
        flags["symbol-cite"] = symbol_cites
    return flags


def _comments_census(
    source: str,
    tree: ast.Module,
    scopes: Sequence[_Scope],
    locator: _Locator,
    is_test_module: bool,
) -> list[_CensusEntry]:
    entries: list[_CensusEntry] = []
    for start, end, texts in _comment_blocks(source):
        scope = locator.scope_at(start)
        first = next((text for text in texts if text), "")
        entries.append(
            _CensusEntry(
                "comment",
                start,
                end,
                scope.qualname if scope else None,
                first,
                _text_flags("\n".join(texts)),
            ),
        )
    owners: list[tuple[str | None, _DocstringOwner, _Scope | None]] = [(None, tree, None)]
    owners.extend((scope.qualname, scope.node, scope) for scope in scopes)
    for owner, node, scope in owners:
        expr = _docstring_expr(node)
        if expr is None:
            if scope is None or scope.is_public:
                lineno = scope.node.lineno if scope else 1
                entries.append(
                    _CensusEntry(
                        "missing-docstring",
                        lineno,
                        lineno,
                        owner,
                        "",
                        {"public-no-docstring": [owner or "<module>"]},
                    ),
                )
            continue
        text = ast.get_docstring(node, clean=True) or ""
        first = text.splitlines()[0].strip() if text else ""
        flags = _text_flags(text)
        if not first.endswith("."):
            flags["first-line-no-period"] = [first]
        name = owner.split(".")[-1] if owner else ""
        if (is_test_module or name.startswith("test")) and first.lower().startswith(
            TEST_DOCSTRING_PREFIXES,
        ):
            flags["test-docstring-prefix"] = [first.split(" ", 2)[0]]
        entries.append(
            _CensusEntry(
                "docstring",
                expr.lineno,
                expr.end_lineno or expr.lineno,
                owner,
                first,
                flags,
            ),
        )
    return sorted(entries, key=lambda entry: (entry.lineno, entry.kind))


# --- Analysis bundle ------------------------------------------------------------------


@dataclass
class _Analysis:
    """Everything one target contributes to the text overview and the JSON document."""

    target: Path
    rel_path: str
    shadow_path: Path
    source: str
    visitor: _StaticVisitor
    comment_records: list[_CommentRecord]
    marker_records: list[_MarkerRecord]
    markers: tuple[str, ...]
    locator: _Locator
    metrics: list[_SymbolMetrics]
    module_per_row: list[_Lead]
    import_time: list[_ImportTimeRecord]
    census: list[_CensusEntry]

    @property
    def per_row(self) -> list[tuple[str, _Lead]]:
        """Return every per-row lead with its citation, in line order."""
        rows = [(self.locator.cite(lead.lineno), lead) for lead in self.module_per_row]
        for item in self.metrics:
            rows.extend(
                (self.locator.symbol_cite(item.scope.qualname), lead) for lead in item.per_row
            )
        return sorted(rows, key=lambda row: row[1].lineno)


def _analyze(
    target: Path,
    source: str,
    tree: ast.Module,
    stripped: str,
    args: argparse.Namespace,
    markers: Sequence[str],
    shadow_path: Path,
    references: _ReferenceIndex | None,
) -> _Analysis:
    source_lines = source.splitlines()
    visitor = _StaticVisitor(
        source_lines,
        args.long_function_lines,
        args.long_function_branches,
        markers,
        args.first_party_prefix,
        args.literal_min_length,
    )
    visitor.visit(tree)
    rel_path = _relative_path(target, args.root)
    scopes = _collect_scopes(tree)
    locator = _Locator(rel_path, scopes, source_lines)
    stripped_lines = stripped.splitlines()
    names = _first_party_names(tree, scopes, args.first_party_prefix)
    metrics = [_symbol_metrics(scope, stripped_lines, markers, names) for scope in scopes]
    if references is not None:
        for item in metrics:
            if "." not in item.scope.qualname:
                item.callers = references.callers(item.scope, rel_path)
    is_test_module = target.name.startswith("test_") or "tests" in Path(rel_path).parts
    return _Analysis(
        target=target,
        rel_path=rel_path,
        shadow_path=shadow_path,
        source=source,
        visitor=visitor,
        comment_records=_comments(source),
        marker_records=_markers(source_lines, stripped_lines, markers),
        markers=tuple(markers),
        locator=locator,
        metrics=metrics,
        module_per_row=_module_per_row(tree, markers),
        import_time=_import_time_work(tree),
        census=_comments_census(source, tree, scopes, locator, is_test_module),
    )


# --- Text rendering -------------------------------------------------------------------


def _render_overview(analysis: _Analysis, outline_only: bool, cap: bool) -> str:
    visitor = analysis.visitor
    cite = analysis.locator.cite
    sections = [
        f"# Static review overview: `{analysis.target}`",
        "",
        "## Safety",
        "",
        "- The target module was parsed statically; it was not imported or executed.",
        "- Shadow-file line numbers match the source line-for-line; a line number from "
        "either file names the same source line.",
        "- Every row names its enclosing symbol as `path::Qualified.Name` (module-level "
        'rows as `path #"<line text>"`); cite that form in review artifacts.',
        f"- Shadow file: `{analysis.shadow_path}`",
        "",
        "## Quick scan",
        "",
        _render_quick_scan(analysis, outline_only),
        "",
        "## Imports",
        "",
        _render_imports(visitor.imports, cite),
        "",
        "## Symbols",
        "",
        _render_symbols(visitor.symbols, analysis.locator),
        "",
        "## Control-flow hotspots",
        "",
        _render_hotspots(visitor.hotspots, analysis.locator),
        "",
        "## Django / ORM markers",
        "",
        _render_markers(analysis.marker_records, cite, cap),
    ]
    if not outline_only:
        sections.extend(
            [
                "",
                "## Calls of interest",
                "",
                _render_calls(visitor.calls, analysis.markers, cite, cap),
                "",
                "## Comments and docstrings",
                "",
                _render_comments_and_docstrings(analysis, cap),
                "",
                "## Repeated string literals",
                "",
                _render_literals(visitor.duplicate_literals, cap),
                "",
                "## Performance leads",
                "",
                _render_performance_leads(analysis),
                "",
                "## Comments census",
                "",
                _render_census(analysis),
            ],
        )
    return "\n".join(sections).rstrip() + "\n"


def _render_imports(records: Sequence[_ImportRecord], cite: _CiteFn) -> str:
    if not records:
        return "None."
    return "\n".join(
        f"- line {record.lineno} `{cite(record.lineno)}`: `{record.text}` ({record.category})"
        for record in records
    )


def _render_quick_scan(analysis: _Analysis, outline_only: bool) -> str:
    visitor = analysis.visitor
    duplicate_count = sum(1 for count in visitor.duplicate_literals.values() if count > 1)
    lines = [
        f"- imports: {len(visitor.imports)}",
        f"- symbols: {len(visitor.symbols)}",
        f"- control-flow hotspots: {len(visitor.hotspots)}",
        f"- executable marker lines: {len(analysis.marker_records)}",
    ]
    if not outline_only:
        entries, reached = _hot_reachability(analysis.metrics)
        flagged = sum(1 for entry in analysis.census if entry.flags)
        todo_count = sum(1 for record in analysis.comment_records if "TODO" in record.text.upper())
        lines.extend(
            [
                f"- calls of interest: {len(_interesting_calls(visitor.calls, analysis.markers))}",
                f"- TODO comments: {todo_count}",
                f"- repeated string literals: {duplicate_count}",
                f"- per-row leads: {len(analysis.per_row)}",
                f"- hot entry points: {len(entries)} (+{len(reached)} reachable)",
                f"- import-time work: {len(analysis.import_time)}",
                f"- comments census: {len(analysis.census)} entries, {flagged} flagged",
            ],
        )
    return "\n".join(lines)


def _render_symbols(records: Sequence[_SymbolRecord], locator: _Locator) -> str:
    if not records:
        return "None."
    lines = []
    for record in records:
        qualname = f"{record.parent}.{record.name}" if record.parent else record.name
        args = f"({record.args})" if record.kind != "class" else ""
        lines.append(
            f"- lines {record.lineno}-{record.end_lineno} `{locator.symbol_cite(qualname)}`: "
            f"`{record.kind} {record.name}{args}`",
        )
    return "\n".join(lines)


def _with_truncation_notice(lines: Sequence[str], limit: int | None) -> list[str]:
    if limit is None:
        return list(lines)
    rendered = list(lines[:limit])
    hidden = len(lines) - limit
    if hidden > 0:
        rendered.append(
            f"- ... ({hidden} more not shown; {len(lines)} total; pass --no-cap to list all)",
        )
    return rendered


def _render_hotspots(records: Sequence[_HotspotRecord], locator: _Locator) -> str:
    if not records:
        return "None."
    return "\n".join(
        f"- line {record.lineno} `{locator.symbol_cite(record.name)}`: `{record.name}` spans "
        f"{record.lines} lines and {record.branches} branch nodes"
        for record in records
    )


def _render_markers(records: Sequence[_MarkerRecord], cite: _CiteFn, cap: bool) -> str:
    if not records:
        return "None."
    lines = [
        "Matched against comment- and string-stripped code; rendered text is the original source line.",
        "",
    ]
    lines.extend(
        _with_truncation_notice(
            [
                f"- line {record.lineno} `{cite(record.lineno)}`: `{record.marker}` in `{record.text}`"
                for record in records
            ],
            limit=50 if cap else None,
        ),
    )
    return "\n".join(lines)


def _interesting_calls(
    records: Sequence[_CallRecord],
    markers: Sequence[str],
) -> list[_CallRecord]:
    """Return calls whose dotted name hits a marker token or is in ``CALLS_OF_INTEREST``.

    Markers match with the same token boundaries as the marker table, so
    ``plan.merge_metadata_from()`` is not an ``_meta`` hit while
    ``model._meta.get_field()`` is. Rows come back in line order.
    """
    return sorted(
        (
            record
            for record in records
            if any(_marker_matches(record.name, marker) for marker in markers)
            or record.name in CALLS_OF_INTEREST
        ),
        key=lambda record: record.lineno,
    )


def _render_calls(
    records: Sequence[_CallRecord],
    markers: Sequence[str],
    cite: _CiteFn,
    cap: bool,
) -> str:
    if not records:
        return "None."
    interesting = _interesting_calls(records, markers)
    if not interesting:
        return "None."
    lines = ["Summary by call:"]
    lines.extend(
        _with_truncation_notice(
            [
                f"- {count}x `{name}()`"
                for name, count in Counter(record.name for record in interesting).most_common()
            ],
            limit=20 if cap else None,
        ),
    )
    lines.extend(
        ["", "Line items:"],
    )
    lines.extend(
        _with_truncation_notice(
            [
                f"- line {record.lineno} `{cite(record.lineno)}`: `{record.name}()`"
                for record in interesting
            ],
            limit=75 if cap else None,
        ),
    )
    return "\n".join(lines)


def _docstring_cite(analysis: _Analysis, record: _DocstringRecord) -> str:
    if record.owner == "<module>":
        return analysis.locator.cite(record.lineno)
    return analysis.locator.symbol_cite(record.owner)


def _render_comments_and_docstrings(analysis: _Analysis, cap: bool) -> str:
    comments = analysis.comment_records
    docstrings = analysis.visitor.docstrings
    cite = analysis.locator.cite
    lines: list[str] = []
    if docstrings:
        lines.append("Docstrings:")
        lines.extend(
            f"- lines {record.lineno}-{record.end_lineno} `{_docstring_cite(analysis, record)}` "
            f"- {record.summary}"
            for record in docstrings
        )
    else:
        lines.append("Docstrings: none.")

    todo_comments = [record for record in comments if "TODO" in record.text.upper()]
    lines.append("")
    if todo_comments:
        lines.append("TODO comments:")
        lines.extend(
            f"- line {record.lineno} `{cite(record.lineno)}`: `{record.text}`"
            for record in todo_comments
        )
    else:
        lines.append("TODO comments: none.")

    if comments:
        lines.append("")
        lines.append("Comment inventory:")
        lines.extend(
            _with_truncation_notice(
                [
                    f"- line {record.lineno} `{cite(record.lineno)}`: `{record.text}`"
                    for record in comments
                ],
                limit=40 if cap else None,
            ),
        )
    return "\n".join(lines)


def _render_literals(counter: Counter[str], cap: bool) -> str:
    duplicates = [(literal, count) for literal, count in counter.most_common() if count > 1]
    if not duplicates:
        return "None."
    lines = []
    literal_lines = []
    for literal, count in duplicates:
        compact = literal.replace("\n", "\\n")
        if len(compact) > 90:
            compact = f"{compact[:87]}..."
        literal_lines.append(f"- {count}x `{compact}`")
    lines.extend(_with_truncation_notice(literal_lines, limit=25 if cap else None))
    return "\n".join(lines)


def _render_performance_leads(analysis: _Analysis) -> str:
    locator = analysis.locator
    lines = [
        "Leads, not findings. Database-shaped calls: the Django / ORM markers plus "
        f"`.{'`, `.'.join(sorted(ORM_CALL_ATTRS))}`, `.get(` with keywords or no arguments, "
        "`.count()` with no arguments, anything through `objects.`, and `sync_to_async` hops.",
        "",
        "### Per-row work (database-shaped call or `await` inside a loop or comprehension)",
        "",
    ]
    per_row = analysis.per_row
    if per_row:
        lines.extend(
            f"- line {lead.lineno} `{where}`: `{lead.call}` ({lead.reason}) inside "
            f"{lead.loop.kind if lead.loop else '?'} at line {lead.loop.lineno if lead.loop else '?'}"
            for where, lead in per_row
        )
    else:
        lines.append("None.")
    entries, reached = _hot_reachability(analysis.metrics)
    lines.extend(
        [
            "",
            "### Hot-path reachability",
            "",
            HOT_PATH_HEURISTIC,
            "",
        ],
    )
    if entries:
        lines.extend(
            f"- entry `{locator.symbol_cite(item.scope.qualname)}` ({'; '.join(item.hot_reasons)})"
            for item in entries
        )
        lines.extend(
            f"- reachable `{locator.symbol_cite(qualname)}` via `{locator.symbol_cite(entry)}`"
            for qualname, entry in sorted(
                reached.items(),
                key=lambda pair: next(
                    item.scope.start for item in analysis.metrics if item.scope.qualname == pair[0]
                ),
            )
        )
    else:
        lines.append("None.")
    lines.extend(
        [
            "",
            "### Import-time work (module level and class bodies; `TYPE_CHECKING` blocks and "
            "declarative typing/container calls excluded)",
            "",
        ],
    )
    if analysis.import_time:
        lines.extend(
            f"- line {record.lineno} `{locator.cite(record.lineno)}`: `{record.text}` ({record.kind})"
            for record in analysis.import_time
        )
    else:
        lines.append("None.")
    return "\n".join(lines)


def _render_flags(flags: dict[str, list[str]]) -> str:
    if not flags:
        return ""
    parts = [f"{name}: {', '.join(values)}" for name, values in flags.items()]
    return f" [{'; '.join(parts)}]"


def _render_census(analysis: _Analysis) -> str:
    lines = [
        "Every comment block (consecutive full-line `#` comments merged; an inline comment "
        "stands alone), every docstring, and every public symbol without one. Flags are leads, "
        "not grades: provenance vocabulary, test docstrings opening `Tests that` / `Ensures`, "
        "first lines not ending in `.`, `path:NN` cites. `path::Symbol` cites are listed, "
        "not resolved (`scripts/check_citations.py` resolves them).",
        "",
    ]
    if not analysis.census:
        lines.append("None.")
        return "\n".join(lines)
    locator = analysis.locator
    for entry in analysis.census:
        where = locator.symbol_cite(entry.owner) if entry.owner else locator.cite(entry.lineno)
        if entry.kind == "comment":
            where = locator.cite(entry.lineno)
        span = (
            f"line {entry.lineno}"
            if entry.lineno == entry.end_lineno
            else f"lines {entry.lineno}-{entry.end_lineno}"
        )
        text = f": {entry.first_line}" if entry.first_line else ""
        lines.append(f"- {span} `{where}` {entry.kind}{text}{_render_flags(entry.flags)}")
    return "\n".join(lines)


# --- JSON rendering -------------------------------------------------------------------


def _blob_id(path: Path) -> tuple[str, str]:
    """Return ``(blob id, source)`` from ``git hash-object``, else the same sha1 computed here."""
    try:
        completed = subprocess.run(
            ["git", "hash-object", str(path)],
            cwd=path.parent,
            capture_output=True,
            text=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return _sha1_blob_id(path.read_bytes()), "sha1"
    return completed.stdout.strip(), "git"


def _sha1_blob_id(data: bytes) -> str:
    """Return the git blob id of ``data``: sha1 over the ``blob <len>`` NUL header plus the bytes."""
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def _lead_json(lead: _Lead) -> dict[str, object]:
    return {
        "line": lead.lineno,
        "call": lead.call,
        "reason": lead.reason,
        "loop": None if lead.loop is None else {"kind": lead.loop.kind, "line": lead.loop.lineno},
    }


def _symbol_json(item: _SymbolMetrics, locator: _Locator) -> dict[str, object]:
    scope = item.scope
    document: dict[str, object] = {
        "qualname": scope.qualname,
        "cite": locator.symbol_cite(scope.qualname),
        "kind": scope.kind,
        "is_public": scope.is_public,
        "has_docstring": item.docstring is not None,
        "docstring_first_line": (item.docstring or "").splitlines()[0] if item.docstring else None,
        "decorators": item.decorators,
        "start_line": scope.start,
        "def_line": scope.node.lineno,
        "end_line": scope.end,
        "code_lines": item.code_lines,
        "max_nesting_depth": item.max_nesting_depth,
        "parameter_count": item.parameter_count,
        "positional_boolean_params": item.positional_boolean_params,
        "await_count": item.await_count,
        "db_calls": [_lead_json(lead) for lead in item.db_calls],
        "per_row_calls": [_lead_json(lead) for lead in item.per_row],
        "first_party_calls": item.first_party_calls,
        "hot_entry_reasons": item.hot_reasons,
    }
    if item.callers is not None:
        document["callers"] = item.callers
        document["callers_approximate"] = True
    return document


def _analysis_json(analysis: _Analysis) -> dict[str, object]:
    visitor = analysis.visitor
    locator = analysis.locator
    cite = locator.cite
    blob, blob_source = _blob_id(analysis.target)
    interesting = _interesting_calls(visitor.calls, analysis.markers)
    entries, reached = _hot_reachability(analysis.metrics)
    return {
        "header": {
            "path": analysis.rel_path,
            "blob": blob,
            "blob_source": blob_source,
            "line_count": len(analysis.source.splitlines()),
            "generated_at": _now(),
            "shadow_path": str(analysis.shadow_path),
            "line_numbers": "shadow-file line numbers match the source line-for-line",
        },
        "imports": [
            {
                "line": r.lineno,
                "where": cite(r.lineno),
                "text": r.text,
                "category": r.category,
            }
            for r in visitor.imports
        ],
        "symbols": [_symbol_json(item, locator) for item in analysis.metrics],
        "hotspots": [
            {
                "line": r.lineno,
                "where": locator.symbol_cite(r.name),
                "lines": r.lines,
                "branches": r.branches,
            }
            for r in visitor.hotspots
        ],
        "markers": [
            {
                "line": r.lineno,
                "where": cite(r.lineno),
                "marker": r.marker,
                "text": r.text,
            }
            for r in analysis.marker_records
        ],
        "calls_of_interest": {
            "summary": dict(Counter(record.name for record in interesting).most_common()),
            "items": [
                {"line": r.lineno, "where": cite(r.lineno), "call": r.name} for r in interesting
            ],
        },
        "docstrings": [
            {
                "owner": r.owner,
                "where": _docstring_cite(analysis, r),
                "line": r.lineno,
                "end_line": r.end_lineno,
                "summary": r.summary,
            }
            for r in visitor.docstrings
        ],
        "comments": [
            {"line": r.lineno, "where": cite(r.lineno), "text": r.text}
            for r in analysis.comment_records
        ],
        "repeated_literals": [
            {"literal": literal, "count": count}
            for literal, count in visitor.duplicate_literals.most_common()
            if count > 1
        ],
        "performance_leads": {
            "heuristic": HOT_PATH_HEURISTIC,
            "per_row": [{"where": where, **_lead_json(lead)} for where, lead in analysis.per_row],
            "hot_entry_points": [
                {"where": locator.symbol_cite(item.scope.qualname), "reasons": item.hot_reasons}
                for item in entries
            ],
            "hot_reachable": [
                {"where": locator.symbol_cite(qualname), "via": locator.symbol_cite(entry)}
                for qualname, entry in reached.items()
            ],
            "import_time": [
                {
                    "line": r.lineno,
                    "where": cite(r.lineno),
                    "kind": r.kind,
                    "text": r.text,
                }
                for r in analysis.import_time
            ],
        },
        "comments_census": [
            {
                "kind": entry.kind,
                "line": entry.lineno,
                "end_line": entry.end_lineno,
                "owner": entry.owner,
                "where": cite(entry.lineno)
                if entry.kind == "comment" or entry.owner is None
                else locator.symbol_cite(entry.owner),
                "first_line": entry.first_line,
                "flags": entry.flags,
            }
            for entry in analysis.census
        ],
    }


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _write_json(path: Path, document: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")


# --- Entry points ---------------------------------------------------------------------


def _target_files_for_all(package_root: Path) -> list[Path]:
    return sorted(path for path in package_root.rglob("*.py") if path.is_file())


def _inspect_target(
    target: Path,
    args: argparse.Namespace,
    markers: Sequence[str],
    output_dir: Path,
    references: _ReferenceIndex | None = None,
    documents: list[dict[str, object]] | None = None,
) -> int:
    if not target.exists():
        print(f"Target does not exist: {target}", file=sys.stderr)
        return 2
    if target.suffix != ".py":
        print(f"Target must be a Python file: {target}", file=sys.stderr)
        return 2

    source = target.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source, filename=str(target))
    except SyntaxError as error:
        print(f"Could not parse {target}: {error}", file=sys.stderr)
        return 1

    stripped = _strip_comments(source)
    stripped = _remove_docstring_statements(stripped, tree)
    stripped = _strip_string_literals(stripped)

    stem = _stable_stem(target, args.root)
    shadow_path = output_dir / f"{stem}.stripped.py"
    overview_path = output_dir / f"{stem}.overview.md"

    shadow_path.write_text(stripped, encoding="utf-8")
    analysis = _analyze(target, source, tree, stripped, args, markers, shadow_path, references)
    cap = not (args.no_cap or args.all)
    overview = _render_overview(analysis, args.outline_only, cap)
    overview_path.write_text(overview, encoding="utf-8")
    if documents is not None:
        documents.append(_analysis_json(analysis))

    if args.stdout:
        print(overview, end="")
    else:
        print(f"Wrote {shadow_path}")
        print(f"Wrote {overview_path}")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run the review inspection helper.

    Args:
        argv: Command-line arguments without the program name; ``sys.argv[1:]`` when
            omitted.

    Returns:
        ``0`` on success, ``1`` when a target fails to parse, ``2`` on a
        caller-correctable error.
    """
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    if args.all and args.target is not None:
        print("Pass either --all or a single target file, not both.", file=sys.stderr)
        return 2
    if not args.all and args.target is None:
        print("Target is required unless --all is passed.", file=sys.stderr)
        return 2

    markers = (*DEFAULT_MARKERS, *args.marker)
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    package_root = (args.root / _ALL_TARGET_ROOT).resolve()
    references = _ReferenceIndex(package_root, args.root) if args.json is not None else None
    documents: list[dict[str, object]] | None = [] if args.json is not None else None

    if args.all:
        if not package_root.is_dir():
            print(f"Package directory does not exist: {package_root}", file=sys.stderr)
            return 2
        targets = _target_files_for_all(package_root)
        if not targets:
            print(f"No Python files found under {package_root}", file=sys.stderr)
            return 2
        for target in targets:
            exit_code = _inspect_target(target, args, markers, output_dir, references, documents)
            if exit_code != 0:
                return exit_code
        if documents is not None:
            _write_json(
                args.json.resolve(),
                {
                    "header": {
                        "root": _relative_path(package_root, args.root),
                        "file_count": len(documents),
                        "generated_at": _now(),
                    },
                    "files": documents,
                },
            )
        if not args.stdout:
            print(f"Wrote inspections for {len(targets)} files under {package_root}")
        return 0

    exit_code = _inspect_target(
        args.target.resolve(),
        args,
        markers,
        output_dir,
        references,
        documents,
    )
    if exit_code == 0 and documents:
        _write_json(args.json.resolve(), documents[0])
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
