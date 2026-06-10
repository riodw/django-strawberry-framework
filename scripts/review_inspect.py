"""Create static review aids for a Python source file.

The target file is parsed as text/AST only. It is never imported or executed,
so this helper is safe for files that touch Django settings, registries, or
Strawberry type creation at import time.

The generated shadow file strips comments and docstring statements, then
replaces remaining string-literal contents so review passes can focus on
executable structure. Marker detection uses that stripped view to avoid
comment/docstring false positives, while rendered marker lines still cite the
original source text.
"""

from __future__ import annotations

import argparse
import ast
import io
import re
import sys
import tokenize
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
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
    "_optimizer_field_map",
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
        self._record_docstring(node, node.name)
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
    )
    parser.add_argument("target", nargs="?", type=Path, help="Python file to inspect.")
    parser.add_argument(
        "--all",
        action="store_true",
        help="Inspect every .py file under django_strawberry_framework/ recursively.",
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
        help="Root used to compute stable output names. Defaults to the current directory.",
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
    # inline-comment removal does not leave whitespace garbage.  Line
    # numbers are preserved because we rebuild line-for-line.
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


def _render_overview(
    target: Path,
    shadow_path: Path,
    visitor: _StaticVisitor,
    comment_records: Sequence[_CommentRecord],
    marker_records: Sequence[_MarkerRecord],
    markers: Sequence[str],
    outline_only: bool,
) -> str:
    sections = [
        f"# Static review overview: `{target}`",
        "",
        "## Safety",
        "",
        "- The target module was parsed statically; it was not imported or executed.",
        "- Shadow-file line numbers are not canonical. Use original source line numbers in review artifacts.",
        f"- Shadow file: `{shadow_path}`",
        "",
        "## Quick scan",
        "",
        _render_quick_scan(visitor, comment_records, marker_records, markers, outline_only),
        "",
        "## Imports",
        "",
        _render_imports(visitor.imports),
        "",
        "## Symbols",
        "",
        _render_symbols(visitor.symbols),
        "",
        "## Control-flow hotspots",
        "",
        _render_hotspots(visitor.hotspots),
        "",
        "## Django / ORM markers",
        "",
        _render_markers(marker_records),
    ]
    if not outline_only:
        sections.extend(
            [
                "",
                "## Calls of interest",
                "",
                _render_calls(visitor.calls, markers),
                "",
                "## Comments and docstrings",
                "",
                _render_comments_and_docstrings(comment_records, visitor.docstrings),
                "",
                "## Repeated string literals",
                "",
                _render_literals(visitor.duplicate_literals),
            ],
        )
    return "\n".join(sections).rstrip() + "\n"


def _render_imports(records: Sequence[_ImportRecord]) -> str:
    if not records:
        return "None."
    return "\n".join(
        f"- line {record.lineno}: `{record.text}` ({record.category})" for record in records
    )


def _render_quick_scan(
    visitor: _StaticVisitor,
    comments: Sequence[_CommentRecord],
    marker_records: Sequence[_MarkerRecord],
    markers: Sequence[str],
    outline_only: bool,
) -> str:
    duplicate_count = sum(1 for count in visitor.duplicate_literals.values() if count > 1)
    lines = [
        f"- imports: {len(visitor.imports)}",
        f"- symbols: {len(visitor.symbols)}",
        f"- control-flow hotspots: {len(visitor.hotspots)}",
        f"- executable marker lines: {len(marker_records)}",
    ]
    if not outline_only:
        lines.extend(
            [
                f"- calls of interest: {len(_interesting_calls(visitor.calls, markers))}",
                f"- TODO comments: {sum(1 for record in comments if 'TODO' in record.text.upper())}",
                f"- repeated string literals: {duplicate_count}",
            ],
        )
    return "\n".join(lines)


def _render_symbols(records: Sequence[_SymbolRecord]) -> str:
    if not records:
        return "None."
    lines = []
    for record in records:
        parent = f" in `{record.parent}`" if record.parent else ""
        args = f"({record.args})" if record.kind != "class" else ""
        lines.append(
            f"- lines {record.lineno}-{record.end_lineno}: `{record.kind} {record.name}{args}`{parent}",
        )
    return "\n".join(lines)


def _with_truncation_notice(lines: Sequence[str], limit: int) -> list[str]:
    rendered = list(lines[:limit])
    hidden = len(lines) - limit
    if hidden > 0:
        rendered.append(f"- ... ({hidden} more not shown)")
    return rendered


def _render_hotspots(records: Sequence[_HotspotRecord]) -> str:
    if not records:
        return "None."
    return "\n".join(
        f"- line {record.lineno}: `{record.name}` spans {record.lines} lines "
        f"and {record.branches} branch nodes"
        for record in records
    )


def _render_markers(records: Sequence[_MarkerRecord]) -> str:
    if not records:
        return "None."
    lines = [
        "Matched against comment- and string-stripped code; rendered text is the original source line.",
        "",
    ]
    lines.extend(
        _with_truncation_notice(
            [
                f"- line {record.lineno}: `{record.marker}` in `{record.text}`"
                for record in records
            ],
            limit=50,
        ),
    )
    return "\n".join(lines)


def _interesting_calls(
    records: Sequence[_CallRecord],
    markers: Sequence[str],
) -> list[_CallRecord]:
    return [
        record
        for record in records
        if any(marker in record.name for marker in markers) or record.name in CALLS_OF_INTEREST
    ]


def _render_calls(records: Sequence[_CallRecord], markers: Sequence[str]) -> str:
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
            limit=20,
        ),
    )
    lines.extend(
        ["", "Line items:"],
    )
    lines.extend(
        _with_truncation_notice(
            [f"- line {record.lineno}: `{record.name}()`" for record in interesting],
            limit=75,
        ),
    )
    return "\n".join(lines)


def _render_comments_and_docstrings(
    comments: Sequence[_CommentRecord],
    docstrings: Sequence[_DocstringRecord],
) -> str:
    lines: list[str] = []
    if docstrings:
        lines.append("Docstrings:")
        lines.extend(
            f"- lines {record.lineno}-{record.end_lineno}: `{record.owner}` — {record.summary}"
            for record in docstrings
        )
    else:
        lines.append("Docstrings: none.")

    todo_comments = [record for record in comments if "TODO" in record.text.upper()]
    lines.append("")
    if todo_comments:
        lines.append("TODO comments:")
        lines.extend(f"- line {record.lineno}: `{record.text}`" for record in todo_comments)
    else:
        lines.append("TODO comments: none.")

    if comments:
        lines.append("")
        lines.append("Comment inventory:")
        lines.extend(
            _with_truncation_notice(
                [f"- line {record.lineno}: `{record.text}`" for record in comments],
                limit=40,
            ),
        )
    return "\n".join(lines)


def _render_literals(counter: Counter[str]) -> str:
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
    lines.extend(_with_truncation_notice(literal_lines, limit=25))
    return "\n".join(lines)


def _target_files_for_all(package_root: Path) -> list[Path]:
    return sorted(path for path in package_root.rglob("*.py") if path.is_file())


def _inspect_target(
    target: Path,
    args: argparse.Namespace,
    markers: Sequence[str],
    output_dir: Path,
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

    stem = _stable_stem(target, args.root)
    shadow_path = output_dir / f"{stem}.stripped.py"
    overview_path = output_dir / f"{stem}.overview.md"

    shadow_path.write_text(stripped, encoding="utf-8")
    overview = _render_overview(
        target,
        shadow_path,
        visitor,
        _comments(source),
        _markers(source_lines, stripped.splitlines(), markers),
        markers,
        args.outline_only,
    )
    overview_path.write_text(overview, encoding="utf-8")

    if args.stdout:
        print(overview, end="")
    else:
        print(f"Wrote {shadow_path}")
        print(f"Wrote {overview_path}")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run the review inspection helper."""
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

    if args.all:
        package_root = (args.root / _ALL_TARGET_ROOT).resolve()
        if not package_root.is_dir():
            print(f"Package directory does not exist: {package_root}", file=sys.stderr)
            return 2
        targets = _target_files_for_all(package_root)
        if not targets:
            print(f"No Python files found under {package_root}", file=sys.stderr)
            return 2
        for target in targets:
            exit_code = _inspect_target(target, args, markers, output_dir)
            if exit_code != 0:
                return exit_code
        if not args.stdout:
            print(f"Wrote inspections for {len(targets)} files under {package_root}")
        return 0

    return _inspect_target(args.target.resolve(), args, markers, output_dir)


if __name__ == "__main__":
    raise SystemExit(main())
