"""Generate source-driven DRY plans, static dossiers, and completeness checks.

The script has three modes:

``plan``
    Inventory the current package source and build a file-by-file DRY review
    plan with folder and project integration passes.

``audit``
    Build the one-stop evidence dossier for a new deep DRY review. It discovers
    Python targets without importing them, inventories every requested symbol,
    maps exact imports and candidate references across configurable scan roots,
    detects exact duplicate function bodies and repeated literals, searches
    caller-supplied concepts, records exclusions and parse failures, and emits
    deterministic Markdown.

``check``
    Gate a completed review: every targeted definition (class, method,
    function, and optionally constant) and every required topic must be named.

Fresh source-driven plan::

    python docs/dry/export_dry_review.py plan \
      --target-release 0.0.14

New deep-review workflow::

    python docs/dry/export_dry_review.py audit \
      --target django_strawberry_framework/utils \
      --context docs/spec-044-debug_extension-0_0_14.md \
      --exclude docs/feedback.md \
      --search-term force_debug_cursor \
      --output docs/dry/dry-audit.md

    python docs/dry/export_dry_review.py check \
      --target django_strawberry_framework/utils \
      --review docs/feedback2.md \
      --require-topic SchemaExtension

All Python inspection is static. Target and scan files are parsed as text/AST
only and are never imported or executed.
"""

from __future__ import annotations

import argparse
import ast
import datetime
import fnmatch
import hashlib
import os
import re
import sys
import tempfile
from collections import Counter, defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

RELEASE_PATTERN = re.compile(r"^\d+(?:\.\d+)+$")
DEFAULT_EXCLUDES = (
    ".git/**",
    ".mypy_cache/**",
    ".pytest_cache/**",
    ".ruff_cache/**",
    ".venv/**",
    "**/__pycache__/**",
    "build/**",
    "dist/**",
    "docs/shadow/**",
    "htmlcov/**",
    "venv/**",
)
DEFAULT_SCAN_ROOTS = (
    "django_strawberry_framework",
    "tests",
    "examples",
    "scripts",
)
MAX_SIGNATURE_LENGTH = 180
MAX_SOURCE_TEXT_LENGTH = 180


@dataclass(frozen=True)
class SymbolRecord:
    """One statically defined target symbol."""

    path: Path
    qualified_name: str
    leaf_name: str
    kind: str
    signature: str
    lineno: int
    end_lineno: int
    doc_summary: str | None
    decorators: tuple[str, ...]

    @property
    def locator(self) -> str:
        """Return the symbol-qualified locator used by reports and checks."""
        return f"{self.path.as_posix()}::{self.qualified_name}"


@dataclass(frozen=True)
class ImportRecord:
    """One import statement and its best-effort resolved module."""

    path: Path
    lineno: int
    module: str
    names: tuple[str, ...]
    text: str


@dataclass(frozen=True)
class ReferenceRecord:
    """One exact import or candidate AST reference to a target symbol."""

    path: Path
    lineno: int
    kind: str
    text: str


@dataclass(frozen=True)
class FunctionBodyRecord:
    """One function/method body eligible for exact-duplicate grouping."""

    path: Path
    qualified_name: str
    fingerprint: str
    node_count: int
    lineno: int

    @property
    def locator(self) -> str:
        """Return a stable function locator."""
        return f"{self.path.as_posix()}::{self.qualified_name}"


@dataclass(frozen=True)
class LiteralRecord:
    """One non-docstring string literal occurrence."""

    path: Path
    lineno: int
    value: str


@dataclass(frozen=True)
class SearchHit:
    """One literal concept-search match."""

    path: Path
    lineno: int
    text: str


@dataclass
class ParsedPythonFile:
    """Static source/AST metadata for one Python file."""

    path: Path
    source: str
    lines: list[str]
    tree: ast.Module
    module_name: str
    symbols: list[SymbolRecord]
    imports: list[ImportRecord]
    function_bodies: list[FunctionBodyRecord]
    literals: list[LiteralRecord]


@dataclass
class DiscoveryResult:
    """Files accepted and excluded during one discovery pass."""

    files: list[Path]
    excluded: list[Path]


@dataclass
class AuditResult:
    """All evidence needed to render one DRY audit dossier."""

    root: Path
    target_files: list[Path]
    scan_files: list[Path]
    target_records: list[ParsedPythonFile]
    scan_records: list[ParsedPythonFile]
    excluded: list[Path]
    failures: dict[Path, str]
    references: dict[str, list[ReferenceRecord]]
    reverse_imports: dict[str, list[ImportRecord]]
    duplicate_groups: list[list[FunctionBodyRecord]]
    repeated_literals: list[tuple[str, list[LiteralRecord]]]
    searches: dict[str, list[SearchHit]]
    context_files: list[Path]
    exclude_patterns: tuple[str, ...]

    @property
    def target_symbols(self) -> list[SymbolRecord]:
        """Return every target symbol in deterministic order."""
        return sorted(
            (symbol for record in self.target_records for symbol in record.symbols),
            key=lambda item: (item.path.as_posix(), item.lineno, item.qualified_name),
        )

    @property
    def target_failures(self) -> dict[Path, str]:
        """Return parse/read failures that make the target inventory incomplete."""
        targets = set(self.target_files)
        return {path: error for path, error in self.failures.items() if path in targets}


@dataclass(frozen=True)
class ReviewCheckResult:
    """Completeness result for a finished review document."""

    symbol_count: int
    missing_symbols: tuple[SymbolRecord, ...]
    missing_topics: tuple[str, ...]

    @property
    def ok(self) -> bool:
        """Return whether the review satisfies every configured gate."""
        return not self.missing_symbols and not self.missing_topics


def _display_path(path: Path, root: Path) -> Path:
    """Return ``path`` relative to ``root`` when possible, else absolute."""
    resolved = path.resolve()
    try:
        return resolved.relative_to(root.resolve())
    except ValueError:
        return resolved


def _resolve_path(path: Path, root: Path) -> Path:
    """Resolve a CLI path relative to the configured root."""
    return path.resolve() if path.is_absolute() else (root / path).resolve()


def _compact(text: str, *, limit: int = MAX_SOURCE_TEXT_LENGTH) -> str:
    """Collapse whitespace and truncate a source/report fragment."""
    compact = " ".join(text.split())
    if len(compact) <= limit:
        return compact
    return f"{compact[: limit - 3]}..."


def _code_span(text: str) -> str:
    """Return a Markdown code span that tolerates backticks in ``text``."""
    delimiter = "``" if "`" in text else "`"
    return f"{delimiter}{text}{delimiter}"


def _validate_date(value: str | None) -> str:
    """Return an ISO date, defaulting to today, or fail with a useful error."""
    if value is None:
        return datetime.date.today().isoformat()
    try:
        return datetime.date.fromisoformat(value).isoformat()
    except ValueError as exc:
        raise ValueError(f"invalid ISO date {value!r}; expected YYYY-MM-DD") from exc


def _atomic_write(path: Path, content: str, *, force: bool) -> None:
    """Atomically write UTF-8 ``content``, refusing an overwrite unless forced."""
    if path.exists() and not force:
        raise FileExistsError(_overwrite_error(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    existing_mode = path.stat().st_mode & 0o777 if path.exists() else 0o644
    temp_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as stream:
            temp_name = stream.name
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temp_name, existing_mode)
        if force:
            os.replace(temp_name, path)
        else:
            try:
                os.link(temp_name, path)
            except FileExistsError as exc:
                raise FileExistsError(_overwrite_error(path)) from exc
            Path(temp_name).unlink()
        temp_name = None
    finally:
        if temp_name is not None:
            temp_path = Path(temp_name)
            if temp_path.exists():
                temp_path.unlink()


def _overwrite_error(path: Path) -> str:
    """Return the standard safe-overwrite diagnostic."""
    return f"output already exists: {path.as_posix()} (pass --force to replace it)"


def _default_output(target_release: str) -> Path:
    """Return ``docs/dry/dry-<release-underscored>.md``."""
    return Path(f"docs/dry/dry-{target_release.replace('.', '_')}.md")


def _artifact_name(prefix: str, relative_path: Path) -> str:
    """Return the artifact name for one source file or package folder."""
    slug = relative_path.as_posix().removesuffix(".py").replace("/", "__")
    return f"{prefix}-{slug}.md"


def _render_source_plan(
    package_root: Path,
    *,
    target_release: str,
    generated_date: str,
    mode: str,
) -> tuple[str, int, int]:
    """Render a fresh plan from the current package source inventory."""
    source_files = sorted(path for path in package_root.rglob("*.py") if path.is_file())
    if not source_files:
        raise ValueError(f"no Python files found under {package_root.as_posix()}")

    grouped: dict[Path, list[Path]] = defaultdict(list)
    for source_file in source_files:
        grouped[source_file.parent].append(source_file)

    lines = [
        f"# System-wide DRY review plan: {target_release}",
        "",
        f"Target: `{package_root.as_posix()}/`",
        f"Generated: {generated_date}",
        f"Mode: {mode}",
        "Workflow: `docs/dry/DRY.md`",
        "Cycle baseline: record before dispatch",
        "",
        "Fresh source review. Do not import findings from prior build, review, or DRY artifacts.",
    ]

    folder_count = 0

    def append_folder(folder: Path) -> None:
        nonlocal folder_count
        relative_folder = folder.relative_to(package_root)
        heading = "Package root" if relative_folder == Path(".") else relative_folder.as_posix()
        lines.extend(["", f"## {heading}", ""])
        for source_file in grouped[folder]:
            relative_file = source_file.relative_to(package_root)
            artifact = _artifact_name("dry-file", relative_file)
            lines.append(
                f"- [ ] File `{relative_file.as_posix()}` — [{artifact}]({artifact})",
            )
        for child in sorted(candidate for candidate in grouped if candidate.parent == folder):
            append_folder(child)
        if relative_folder != Path("."):
            folder_count += 1
            artifact = _artifact_name("dry-folder", relative_folder)
            lines.extend(["", f"## {relative_folder.as_posix()} integration", ""])
            lines.append(
                f"- [ ] Folder integration `{relative_folder.as_posix()}/` — "
                f"[{artifact}]({artifact})",
            )

    append_folder(package_root)

    lines.extend(
        [
            "",
            "## Project",
            "",
            "- [ ] Project integration — [dry-project.md](dry-project.md)",
            "- [ ] Final test gate",
            "",
        ],
    )
    return "\n".join(lines), len(source_files), folder_count


def _matches_exclude(path: Path, root: Path, patterns: Sequence[str]) -> bool:
    """Return whether ``path`` matches any repo-relative exclusion glob."""
    display = _display_path(path, root).as_posix()
    return any(
        fnmatch.fnmatchcase(display, pattern)
        or Path(display).match(pattern)
        or (pattern.endswith("/**") and fnmatch.fnmatchcase(display, pattern[:-3]))
        for pattern in patterns
    )


def _discover_python(
    inputs: Sequence[Path],
    *,
    root: Path,
    excludes: Sequence[str],
) -> DiscoveryResult:
    """Discover Python files under inputs while pruning excluded directories."""
    accepted: set[Path] = set()
    excluded: set[Path] = set()
    for raw_path in inputs:
        path = _resolve_path(raw_path, root)
        if not path.exists():
            raise ValueError(f"path does not exist: {_display_path(path, root).as_posix()}")
        if path.is_file():
            if path.suffix != ".py":
                raise ValueError(f"target/scan file is not Python: {path.as_posix()}")
            if _matches_exclude(path, root, excludes):
                excluded.add(path)
            else:
                accepted.add(path)
            continue

        for current, directory_names, file_names in os.walk(path):
            current_path = Path(current)
            kept_directories: list[str] = []
            for directory_name in directory_names:
                child = current_path / directory_name
                if _matches_exclude(child, root, excludes):
                    excluded.add(child)
                else:
                    kept_directories.append(directory_name)
            directory_names[:] = kept_directories
            for file_name in file_names:
                child = current_path / file_name
                if child.suffix != ".py":
                    continue
                if _matches_exclude(child, root, excludes):
                    excluded.add(child)
                else:
                    accepted.add(child)
    return DiscoveryResult(sorted(accepted), sorted(excluded))


def _validate_explicit_paths(
    paths: Sequence[Path],
    *,
    root: Path,
    excludes: Sequence[str],
    label: str,
) -> None:
    """Reject an explicitly supplied path that itself matches an exclusion."""
    rejected = [
        _display_path(_resolve_path(path, root), root)
        for path in paths
        if _matches_exclude(_resolve_path(path, root), root, excludes)
    ]
    if rejected:
        listed = ", ".join(path.as_posix() for path in rejected)
        raise ValueError(f"explicit {label} path matched --exclude and was not read: {listed}")


def _module_name(path: Path, root: Path) -> str:
    """Return a best-effort dotted module name for a Python path."""
    display = _display_path(path, root)
    parts = list(display.with_suffix("").parts)
    if parts and parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def _doc_summary(node: ast.AST) -> str | None:
    """Return the first compact line of a node's docstring."""
    docstring = ast.get_docstring(node, clean=True)
    if not docstring:
        return None
    return _compact(docstring.splitlines()[0])


def _decorators(node: ast.AST) -> tuple[str, ...]:
    """Return rendered decorators for a class or function definition."""
    decorator_list = getattr(node, "decorator_list", ())
    return tuple(ast.unparse(decorator) for decorator in decorator_list)


def _signature(node: ast.AST) -> str:
    """Return a compact class/function/constant signature."""
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        prefix = "async " if isinstance(node, ast.AsyncFunctionDef) else ""
        rendered = f"{prefix}({ast.unparse(node.args)})"
        if node.returns is not None:
            rendered += f" -> {ast.unparse(node.returns)}"
        return _compact(rendered, limit=MAX_SIGNATURE_LENGTH)
    if isinstance(node, ast.ClassDef):
        bases = [ast.unparse(base) for base in node.bases]
        bases.extend(
            f"{keyword.arg}={ast.unparse(keyword.value)}"
            for keyword in node.keywords
            if keyword.arg is not None
        )
        return f"({', '.join(bases)})" if bases else ""
    return ""


def _is_docstring_statement(node: ast.AST) -> bool:
    """Return whether an AST statement is a string docstring."""
    return (
        isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Constant)
        and isinstance(node.value.value, str)
    )


def _function_fingerprint(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> tuple[str, int]:
    """Return an exact body fingerprint and nontrivial AST-node count."""
    body = list(node.body)
    if body and _is_docstring_statement(body[0]):
        body.pop(0)
    wrapper = ast.Module(body=body, type_ignores=[])
    payload = f"{type(node).__name__}:{ast.dump(wrapper, include_attributes=False)}"
    node_count = sum(1 for _item in ast.walk(wrapper))
    return hashlib.sha256(payload.encode()).hexdigest(), node_count


def _constant_name(node: ast.AST) -> str | None:
    """Return a module-level uppercase assignment name, if any."""
    if (
        isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
    ):
        name = node.targets[0].id
        return name if name.isupper() else None
    if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
        name = node.target.id
        return name if name.isupper() else None
    return None


def _constant_signature(node: ast.Assign | ast.AnnAssign) -> str:
    """Return a compact module-constant annotation/value."""
    annotation = ast.unparse(node.annotation) if isinstance(node, ast.AnnAssign) else None
    value = node.value
    rendered = ast.unparse(value) if value is not None else ""
    prefix = f": {annotation}" if annotation else ""
    suffix = f" = {rendered}" if rendered else ""
    return _compact(prefix + suffix, limit=MAX_SIGNATURE_LENGTH)


def _collect_symbols_and_bodies(
    tree: ast.Module,
    path: Path,
    *,
    include_nested: bool,
    include_constants: bool,
) -> tuple[list[SymbolRecord], list[FunctionBodyRecord]]:
    """Collect target symbols and all duplicate-eligible function bodies."""
    symbols: list[SymbolRecord] = []
    function_bodies: list[FunctionBodyRecord] = []

    def visit_body(
        body: Sequence[ast.stmt],
        parents: tuple[str, ...],
        *,
        inside_function: bool,
    ) -> None:
        for node in body:
            if isinstance(node, ast.ClassDef):
                qualified = ".".join((*parents, node.name))
                symbols.append(
                    SymbolRecord(
                        path,
                        qualified,
                        node.name,
                        "class" if not parents else "nested class",
                        _signature(node),
                        node.lineno,
                        node.end_lineno or node.lineno,
                        _doc_summary(node),
                        _decorators(node),
                    ),
                )
                visit_body(node.body, (*parents, node.name), inside_function=False)
                continue
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                qualified = ".".join((*parents, node.name))
                if not inside_function or include_nested:
                    if not parents:
                        kind = (
                            "async function"
                            if isinstance(node, ast.AsyncFunctionDef)
                            else "function"
                        )
                    elif inside_function:
                        kind = "nested function"
                    else:
                        kind = (
                            "async method" if isinstance(node, ast.AsyncFunctionDef) else "method"
                        )
                    symbols.append(
                        SymbolRecord(
                            path,
                            qualified,
                            node.name,
                            kind,
                            _signature(node),
                            node.lineno,
                            node.end_lineno or node.lineno,
                            _doc_summary(node),
                            _decorators(node),
                        ),
                    )
                fingerprint, node_count = _function_fingerprint(node)
                function_bodies.append(
                    FunctionBodyRecord(path, qualified, fingerprint, node_count, node.lineno),
                )
                if include_nested:
                    visit_body(node.body, (*parents, node.name), inside_function=True)
                continue
            if not parents and include_constants:
                name = _constant_name(node)
                if name is not None:
                    symbols.append(
                        SymbolRecord(
                            path,
                            name,
                            name,
                            "constant",
                            _constant_signature(node),  # type: ignore[arg-type]
                            node.lineno,
                            node.end_lineno or node.lineno,
                            None,
                            (),
                        ),
                    )

    visit_body(tree.body, (), inside_function=False)
    return symbols, function_bodies


def _resolved_from_module(
    path: Path,
    root: Path,
    node: ast.ImportFrom,
) -> str:
    """Resolve a relative ``from`` import to a best-effort dotted module."""
    if node.level == 0:
        return node.module or ""
    current = _module_name(path, root).split(".")
    if path.name != "__init__.py" and current:
        current.pop()
    remove = node.level - 1
    if remove:
        current = current[:-remove] if remove <= len(current) else []
    if node.module:
        current.extend(node.module.split("."))
    return ".".join(current)


def _collect_imports(tree: ast.Module, path: Path, root: Path, source: str) -> list[ImportRecord]:
    """Collect imports with resolved module names and source text."""
    records: list[ImportRecord] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                text = ast.get_source_segment(source, node) or f"import {alias.name}"
                records.append(
                    ImportRecord(path, node.lineno, alias.name, (alias.name,), _compact(text)),
                )
        elif isinstance(node, ast.ImportFrom):
            module = _resolved_from_module(path, root, node)
            names = tuple(alias.name for alias in node.names)
            text = (
                ast.get_source_segment(source, node) or f"from {module} import {', '.join(names)}"
            )
            records.append(ImportRecord(path, node.lineno, module, names, _compact(text)))
    return sorted(records, key=lambda record: (record.lineno, record.module, record.names))


class _LiteralVisitor(ast.NodeVisitor):
    """Collect non-docstring string literals."""

    def __init__(self, path: Path, minimum_length: int) -> None:
        self.path = path
        self.minimum_length = minimum_length
        self.records: list[LiteralRecord] = []

    def _visit_definition(self, node: ast.AST) -> None:
        """Visit every AST field while omitting only the leading docstring."""
        for field, value in ast.iter_fields(node):
            if field == "body" and isinstance(value, list):
                for index, statement in enumerate(value):
                    if index == 0 and _is_docstring_statement(statement):
                        continue
                    self.visit(statement)
            elif isinstance(value, ast.AST):
                self.visit(value)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, ast.AST):
                        self.visit(item)

    def visit_Module(self, node: ast.Module) -> None:
        """Visit module contents without the module docstring."""
        self._visit_definition(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Visit class contents without the class docstring."""
        self._visit_definition(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit function contents without the function docstring."""
        self._visit_definition(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Visit async-function contents without the function docstring."""
        self._visit_definition(node)

    def visit_Constant(self, node: ast.Constant) -> None:
        """Record a sufficiently long string literal."""
        if isinstance(node.value, str) and len(node.value) >= self.minimum_length:
            self.records.append(LiteralRecord(self.path, node.lineno, node.value))


def _parse_python_file(
    path: Path,
    *,
    root: Path,
    include_nested: bool,
    include_constants: bool,
    literal_min_length: int,
) -> ParsedPythonFile:
    """Read and statically parse one Python file."""
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=path.as_posix())
    display = _display_path(path, root)
    symbols, function_bodies = _collect_symbols_and_bodies(
        tree,
        display,
        include_nested=include_nested,
        include_constants=include_constants,
    )
    imports = _collect_imports(tree, display, Path("."), source)
    literal_visitor = _LiteralVisitor(display, literal_min_length)
    literal_visitor.visit(tree)
    return ParsedPythonFile(
        display,
        source,
        source.splitlines(),
        tree,
        _module_name(path, root),
        symbols,
        imports,
        function_bodies,
        literal_visitor.records,
    )


def _parse_python_files(
    files: Sequence[Path],
    *,
    root: Path,
    include_nested: bool,
    include_constants: bool,
    literal_min_length: int,
) -> tuple[list[ParsedPythonFile], dict[Path, str]]:
    """Parse files independently, returning records and nonfatal failures."""
    records: list[ParsedPythonFile] = []
    failures: dict[Path, str] = {}
    for path in files:
        display = _display_path(path, root)
        try:
            records.append(
                _parse_python_file(
                    path,
                    root=root,
                    include_nested=include_nested,
                    include_constants=include_constants,
                    literal_min_length=literal_min_length,
                ),
            )
        except (OSError, UnicodeError, SyntaxError) as exc:
            failures[display] = f"{type(exc).__name__}: {exc}"
    return records, failures


def _line_text(record: ParsedPythonFile, lineno: int) -> str:
    """Return one compact source line, tolerating malformed AST positions."""
    if 1 <= lineno <= len(record.lines):
        return _compact(record.lines[lineno - 1])
    return ""


def _target_module_symbols(
    target_records: Sequence[ParsedPythonFile],
) -> dict[str, dict[str, SymbolRecord]]:
    """Return ``module -> top-level symbol name -> record``."""
    result: dict[str, dict[str, SymbolRecord]] = {}
    for record in target_records:
        result[record.module_name] = {
            symbol.qualified_name: symbol
            for symbol in record.symbols
            if "." not in symbol.qualified_name
        }
    return result


def _collect_references(
    target_records: Sequence[ParsedPythonFile],
    scan_records: Sequence[ParsedPythonFile],
) -> tuple[dict[str, list[ReferenceRecord]], dict[str, list[ImportRecord]]]:
    """Collect exact imports, unambiguous name uses, and reverse import edges."""
    symbols = [symbol for record in target_records for symbol in record.symbols]
    by_leaf: dict[str, list[SymbolRecord]] = defaultdict(list)
    by_locator = {symbol.locator: symbol for symbol in symbols}
    for symbol in symbols:
        by_leaf[symbol.leaf_name].append(symbol)

    module_symbols = _target_module_symbols(target_records)
    target_modules = set(module_symbols)
    references: dict[str, list[ReferenceRecord]] = defaultdict(list)
    reverse_imports: dict[str, list[ImportRecord]] = defaultdict(list)

    for record in scan_records:
        seen: set[tuple[str, int, str, str]] = set()
        imported_aliases: dict[str, str] = {}
        for node in ast.walk(record.tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in target_modules:
                        import_record = ImportRecord(
                            record.path,
                            node.lineno,
                            alias.name,
                            (alias.name,),
                            _line_text(record, node.lineno),
                        )
                        reverse_imports[alias.name].append(import_record)
                        if alias.asname:
                            imported_aliases[alias.asname] = alias.name
            elif isinstance(node, ast.ImportFrom):
                module = _resolved_from_module(
                    record.path,
                    Path("."),
                    node,
                )
                if module in target_modules:
                    import_record = ImportRecord(
                        record.path,
                        node.lineno,
                        module,
                        tuple(alias.name for alias in node.names),
                        _line_text(record, node.lineno),
                    )
                    reverse_imports[module].append(import_record)
                    for alias in node.names:
                        symbol = module_symbols[module].get(alias.name)
                        if symbol is None:
                            continue
                        key = (symbol.locator, node.lineno, "exact import", record.path.as_posix())
                        if key not in seen:
                            seen.add(key)
                            references[symbol.locator].append(
                                ReferenceRecord(
                                    record.path,
                                    node.lineno,
                                    "exact import",
                                    _line_text(record, node.lineno),
                                ),
                            )
                for alias in node.names:
                    imported_module = f"{module}.{alias.name}" if module else alias.name
                    if imported_module not in target_modules:
                        continue
                    import_record = ImportRecord(
                        record.path,
                        node.lineno,
                        imported_module,
                        (alias.name,),
                        _line_text(record, node.lineno),
                    )
                    reverse_imports[imported_module].append(import_record)
                    imported_aliases[alias.asname or alias.name] = imported_module

        for node in ast.walk(record.tree):
            leaf: str | None = None
            kind = ""
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                leaf = node.id
                kind = "name"
            elif isinstance(node, ast.Attribute):
                leaf = node.attr
                kind = "attribute"
                if isinstance(node.value, ast.Name) and node.value.id in imported_aliases:
                    module = imported_aliases[node.value.id]
                    symbol = module_symbols[module].get(leaf)
                    if symbol is not None:
                        key = (
                            symbol.locator,
                            node.lineno,
                            "exact module attribute",
                            record.path.as_posix(),
                        )
                        if key not in seen:
                            seen.add(key)
                            references[symbol.locator].append(
                                ReferenceRecord(
                                    record.path,
                                    node.lineno,
                                    "exact module attribute",
                                    _line_text(record, node.lineno),
                                ),
                            )
                        continue
            if leaf is None or len(by_leaf.get(leaf, ())) != 1:
                continue
            symbol = by_leaf[leaf][0]
            if record.path == symbol.path and node.lineno == symbol.lineno:
                continue
            key = (symbol.locator, node.lineno, kind, record.path.as_posix())
            if key in seen:
                continue
            seen.add(key)
            references[symbol.locator].append(
                ReferenceRecord(record.path, node.lineno, kind, _line_text(record, node.lineno)),
            )

    for locator in by_locator:
        references.setdefault(locator, [])
    return (
        {
            locator: sorted(items, key=lambda item: (item.path.as_posix(), item.lineno, item.kind))
            for locator, items in references.items()
        },
        {
            module: sorted(items, key=lambda item: (item.path.as_posix(), item.lineno))
            for module, items in reverse_imports.items()
        },
    )


def _duplicate_groups(
    records: Sequence[ParsedPythonFile],
    *,
    minimum_nodes: int,
) -> list[list[FunctionBodyRecord]]:
    """Return exact duplicate nontrivial function-body groups."""
    grouped: dict[str, list[FunctionBodyRecord]] = defaultdict(list)
    for record in records:
        for body in record.function_bodies:
            if body.node_count >= minimum_nodes:
                grouped[body.fingerprint].append(body)
    groups = [items for items in grouped.values() if len(items) > 1]
    return sorted(
        (sorted(items, key=lambda item: (item.path.as_posix(), item.lineno)) for items in groups),
        key=lambda items: (-len(items), items[0].locator),
    )


def _repeated_literals(
    records: Sequence[ParsedPythonFile],
) -> list[tuple[str, list[LiteralRecord]]]:
    """Return repeated non-docstring string literals and their locations."""
    grouped: dict[str, list[LiteralRecord]] = defaultdict(list)
    for record in records:
        for literal in record.literals:
            grouped[literal.value].append(literal)
    repeated = [(value, locations) for value, locations in grouped.items() if len(locations) > 1]
    return sorted(repeated, key=lambda item: (-len(item[1]), item[0]))


def _search_sources(
    terms: Sequence[str],
    python_records: Sequence[ParsedPythonFile],
    contexts: dict[Path, str],
    *,
    case_sensitive: bool,
) -> dict[str, list[SearchHit]]:
    """Search parsed Python and context text for literal terms."""
    sources = {record.path: record.source for record in python_records}
    sources.update(contexts)
    result: dict[str, list[SearchHit]] = {}
    for term in terms:
        needle = term if case_sensitive else term.casefold()
        hits: list[SearchHit] = []
        for path, source in sorted(sources.items(), key=lambda item: item[0].as_posix()):
            for lineno, line in enumerate(source.splitlines(), start=1):
                haystack = line if case_sensitive else line.casefold()
                if needle in haystack:
                    hits.append(SearchHit(path, lineno, _compact(line)))
        result[term] = hits
    return result


def build_audit(
    *,
    root: Path,
    targets: Sequence[Path],
    scan_roots: Sequence[Path],
    contexts: Sequence[Path] = (),
    exclude_patterns: Sequence[str] = DEFAULT_EXCLUDES,
    search_terms: Sequence[str] = (),
    include_nested: bool = False,
    include_constants: bool = False,
    case_sensitive: bool = False,
    duplicate_min_nodes: int = 8,
    literal_min_length: int = 20,
    output: Path | None = None,
) -> AuditResult:
    """Build a complete static DRY audit without writing its report."""
    root = root.resolve()
    if any(not term for term in search_terms):
        raise ValueError("--search-term values must not be empty")
    _validate_explicit_paths(
        targets,
        root=root,
        excludes=exclude_patterns,
        label="target",
    )
    target_discovery = _discover_python(targets, root=root, excludes=exclude_patterns)
    if not target_discovery.files:
        raise ValueError("no target Python files remain after discovery/exclusions")

    effective_scan_roots = list(scan_roots)
    if not effective_scan_roots:
        effective_scan_roots = [
            Path(path) for path in DEFAULT_SCAN_ROOTS if _resolve_path(Path(path), root).exists()
        ]
    scan_discovery = _discover_python(effective_scan_roots, root=root, excludes=exclude_patterns)
    scan_files = set(scan_discovery.files)
    scan_files.update(target_discovery.files)
    if output is not None:
        scan_files.discard(output.resolve())

    scan_records, failures = _parse_python_files(
        sorted(scan_files),
        root=root,
        include_nested=include_nested,
        include_constants=include_constants,
        literal_min_length=literal_min_length,
    )
    target_display = {_display_path(path, root) for path in target_discovery.files}
    target_records = [record for record in scan_records if record.path in target_display]

    context_sources: dict[Path, str] = {}
    context_files: list[Path] = []
    for raw_context in contexts:
        context = _resolve_path(raw_context, root)
        if not context.is_file():
            raise ValueError(f"context file does not exist: {context.as_posix()}")
        if _matches_exclude(context, root, exclude_patterns):
            raise ValueError(
                f"context file matched --exclude and was not read: "
                f"{_display_path(context, root).as_posix()}",
            )
        display = _display_path(context, root)
        context_sources[display] = context.read_text(encoding="utf-8")
        context_files.append(display)

    references, reverse_imports = _collect_references(target_records, scan_records)
    duplicate_groups = _duplicate_groups(scan_records, minimum_nodes=duplicate_min_nodes)
    repeated_literals = _repeated_literals(scan_records)
    searches = _search_sources(
        search_terms,
        scan_records,
        context_sources,
        case_sensitive=case_sensitive,
    )
    excluded = {
        _display_path(path, root)
        for path in (*target_discovery.excluded, *scan_discovery.excluded)
    }
    return AuditResult(
        root=root,
        target_files=sorted(target_display),
        scan_files=sorted(record.path for record in scan_records),
        target_records=sorted(target_records, key=lambda record: record.path.as_posix()),
        scan_records=sorted(scan_records, key=lambda record: record.path.as_posix()),
        excluded=sorted(excluded),
        failures=failures,
        references=references,
        reverse_imports=reverse_imports,
        duplicate_groups=duplicate_groups,
        repeated_literals=repeated_literals,
        searches=searches,
        context_files=sorted(context_files),
        exclude_patterns=tuple(exclude_patterns),
    )


def _render_evidence(
    records: Sequence[ImportRecord | ReferenceRecord | SearchHit | LiteralRecord],
    *,
    maximum: int,
) -> list[str]:
    """Render bounded location/text evidence with an omission notice."""
    lines: list[str] = []
    for record in records[:maximum]:
        text = getattr(record, "text", None)
        location = f"{record.path.as_posix()}:{record.lineno}"
        suffix = f" — {_code_span(text)}" if text else ""
        kind = getattr(record, "kind", None)
        kind_prefix = f"{kind}: " if kind else ""
        lines.append(f"- {kind_prefix}{_code_span(location)}{suffix}")
    if len(records) > maximum:
        lines.append(f"- … {len(records) - maximum} more occurrence(s) omitted.")
    return lines


def render_audit_markdown(
    audit: AuditResult,
    *,
    generated_date: str,
    maximum_evidence: int = 25,
) -> str:
    """Render a deterministic, self-contained DRY audit dossier."""
    lines = [
        "# DRY audit dossier",
        "",
        f"Generated: {generated_date}",
        f"Root: `{audit.root.as_posix()}`",
        f"Targets: {len(audit.target_files)} Python file(s)",
        f"Scan scope: {len(audit.scan_files)} parsed Python file(s)",
        f"Target definitions: {len(audit.target_symbols)}",
        f"Context files: {len(audit.context_files)}",
        f"Parse/read failures: {len(audit.failures)}",
        "",
        "This is static evidence, not an automated refactoring verdict. Candidate "
        "references are intentionally broad and must be confirmed against semantics.",
        "",
        "## Scope",
        "",
        "### Target files",
        "",
    ]
    lines.extend(f"- `{path.as_posix()}`" for path in audit.target_files)
    lines.extend(["", "### Context files", ""])
    lines.extend(
        (f"- `{path.as_posix()}`" for path in audit.context_files),
    )
    if not audit.context_files:
        lines.append("- None.")
    lines.extend(["", "### Exclusion patterns", ""])
    lines.extend(f"- `{pattern}`" for pattern in audit.exclude_patterns)
    lines.extend(["", "### Excluded paths observed", ""])
    lines.extend(
        (f"- `{path.as_posix()}`" for path in audit.excluded[:maximum_evidence]),
    )
    if len(audit.excluded) > maximum_evidence:
        lines.append(f"- … {len(audit.excluded) - maximum_evidence} more path(s) omitted.")
    if not audit.excluded:
        lines.append("- None observed.")

    lines.extend(["", "## Target inventory", ""])
    for record in audit.target_records:
        lines.extend(
            [
                f"### `{record.path.as_posix()}`",
                "",
                f"- Module: `{record.module_name}`",
                f"- Lines: {len(record.lines)}",
                f"- Definitions: {len(record.symbols)}",
                f"- Imports: {len(record.imports)}",
                "",
            ],
        )
        if not record.symbols:
            lines.append("- No class/function/constant definitions.")
        for symbol in record.symbols:
            signature = f" {_code_span(symbol.signature)}" if symbol.signature else ""
            doc = f" — {symbol.doc_summary}" if symbol.doc_summary else ""
            decorators = (
                " — decorators: "
                + ", ".join(_code_span(f"@{decorator}") for decorator in symbol.decorators)
                if symbol.decorators
                else ""
            )
            lines.append(
                f"- **{symbol.kind}** `{symbol.qualified_name}`{signature} "
                f"({symbol.path.as_posix()}:{symbol.lineno}){decorators}{doc}",
            )
        lines.extend(["", "Imports:", ""])
        lines.extend(
            (
                f"- `{item.path.as_posix()}:{item.lineno}` — {_code_span(item.text)}"
                for item in record.imports
            ),
        )
        if not record.imports:
            lines.append("- None.")
        lines.append("")

    lines.extend(["## Reverse imports", ""])
    for target in audit.target_records:
        imports = audit.reverse_imports.get(target.module_name, [])
        lines.extend([f"### `{target.module_name}`", ""])
        lines.extend(_render_evidence(imports, maximum=maximum_evidence))
        if not imports:
            lines.append("- No direct from-importers found.")
        lines.append("")

    lines.extend(["## Symbol reference candidates", ""])
    leaf_counts = Counter(symbol.leaf_name for symbol in audit.target_symbols)
    for symbol in audit.target_symbols:
        references = audit.references.get(symbol.locator, [])
        lines.extend(
            [
                f"### `{symbol.locator}`",
                "",
                f"- Candidate occurrences: {len(references)}",
            ],
        )
        if leaf_counts[symbol.leaf_name] > 1:
            lines.append(
                f"- `{symbol.leaf_name}` is shared by {leaf_counts[symbol.leaf_name]} target "
                "definitions; ambiguous leaf-only uses are intentionally suppressed.",
            )
        lines.extend(_render_evidence(references, maximum=maximum_evidence))
        if not references:
            lines.append("- No exact import or unambiguous AST candidate found.")
        lines.append("")

    lines.extend(["## Exact duplicate function bodies", ""])
    if not audit.duplicate_groups:
        lines.append("- No nontrivial exact duplicate bodies found.")
    for index, group in enumerate(audit.duplicate_groups, start=1):
        lines.append(f"### Candidate group {index} ({len(group)} copies)")
        lines.append("")
        lines.extend(
            f"- `{record.locator}` ({record.path.as_posix()}:{record.lineno}; "
            f"{record.node_count} AST nodes)"
            for record in group
        )
        lines.append("")

    lines.extend(["## Repeated non-docstring literals", ""])
    if not audit.repeated_literals:
        lines.append("- No repeated literals at the configured minimum length.")
    for value, occurrences in audit.repeated_literals[:maximum_evidence]:
        lines.append(f"### {len(occurrences)}x {_code_span(_compact(value, limit=100))}")
        lines.append("")
        lines.extend(_render_evidence(occurrences, maximum=maximum_evidence))
        lines.append("")
    if len(audit.repeated_literals) > maximum_evidence:
        lines.append(
            f"- … {len(audit.repeated_literals) - maximum_evidence} additional repeated "
            "literal group(s) omitted.",
        )

    lines.extend(["", "## Concept searches", ""])
    if not audit.searches:
        lines.append("- No `--search-term` values supplied.")
    for term, hits in audit.searches.items():
        lines.extend([f"### `{term}` ({len(hits)} hits)", ""])
        lines.extend(_render_evidence(hits, maximum=maximum_evidence))
        if not hits:
            lines.append("- No matches.")
        lines.append("")

    lines.extend(["## Parse/read failures", ""])
    if not audit.failures:
        lines.append("- None.")
    else:
        for path, error in sorted(audit.failures.items(), key=lambda item: item[0].as_posix()):
            target_marker = (
                " **TARGET — inventory incomplete**" if path in audit.target_files else ""
            )
            lines.append(f"- `{path.as_posix()}`{target_marker}: {_code_span(error)}")

    lines.extend(
        [
            "",
            "## Review handoff",
            "",
            "Before closing the review:",
            "",
            "- Read every target file in full.",
            "- Resolve every target parse failure.",
            "- Classify each reference and duplicate candidate as real reuse, deliberate "
            "non-reuse, already shared, or false positive.",
            "- Search additional domain concepts discovered during reading.",
            "- Record positive reuse and tempting-but-wrong reuse.",
            "- Run this script's `check` mode against the finished review with every "
            "load-bearing topic passed as `--require-topic`.",
            "",
        ],
    )
    return "\n".join(lines)


def check_review(
    *,
    root: Path,
    targets: Sequence[Path],
    review: Path,
    required_topics: Sequence[str] = (),
    exclude_patterns: Sequence[str] = DEFAULT_EXCLUDES,
    include_nested: bool = False,
    include_constants: bool = False,
    case_sensitive_topics: bool = False,
) -> ReviewCheckResult:
    """Verify that a completed review names every target symbol and topic."""
    root = root.resolve()
    if any(not topic for topic in required_topics):
        raise ValueError("--require-topic values must not be empty")
    review_path = _resolve_path(review, root)
    if not review_path.is_file():
        raise ValueError(f"review file does not exist: {review_path.as_posix()}")
    if _matches_exclude(review_path, root, exclude_patterns):
        raise ValueError(
            "explicit review path matched --exclude and was not read: "
            f"{_display_path(review_path, root).as_posix()}",
        )
    _validate_explicit_paths(
        targets,
        root=root,
        excludes=exclude_patterns,
        label="target",
    )
    review_text = review_path.read_text(encoding="utf-8")
    discovery = _discover_python(targets, root=root, excludes=exclude_patterns)
    records, failures = _parse_python_files(
        discovery.files,
        root=root,
        include_nested=include_nested,
        include_constants=include_constants,
        literal_min_length=sys.maxsize,
    )
    if failures:
        details = "; ".join(f"{path.as_posix()}: {error}" for path, error in failures.items())
        raise ValueError(f"target inventory is incomplete: {details}")

    symbols = sorted(
        (symbol for record in records for symbol in record.symbols),
        key=lambda item: (item.path.as_posix(), item.lineno, item.qualified_name),
    )
    coverage_names = [
        symbol.qualified_name if "." in symbol.qualified_name else symbol.leaf_name
        for symbol in symbols
    ]
    coverage_name_counts = Counter(coverage_names)
    missing_symbols: list[SymbolRecord] = []
    for symbol in symbols:
        needle = symbol.qualified_name if "." in symbol.qualified_name else symbol.leaf_name
        required_needle = symbol.locator if coverage_name_counts[needle] > 1 else needle
        if required_needle not in review_text:
            missing_symbols.append(symbol)

    topic_haystack = review_text if case_sensitive_topics else review_text.casefold()
    missing_topics = tuple(
        topic
        for topic in required_topics
        if (topic if case_sensitive_topics else topic.casefold()) not in topic_haystack
    )
    return ReviewCheckResult(len(symbols), tuple(missing_symbols), missing_topics)


def _add_target_arguments(parser: argparse.ArgumentParser) -> None:
    """Add arguments shared by audit/check target discovery."""
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="Repository/root directory used to resolve paths (default: current directory).",
    )
    parser.add_argument(
        "--target",
        type=Path,
        action="append",
        required=True,
        help="Python file or directory to inventory; repeatable.",
    )
    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        help="Repo-relative glob that must not be read; repeatable.",
    )
    parser.add_argument(
        "--no-default-excludes",
        action="store_true",
        help="Disable built-in VCS, environment, cache, build, and docs/shadow exclusions.",
    )
    parser.add_argument(
        "--include-nested",
        action="store_true",
        help="Inventory nested local functions in addition to module/class definitions.",
    )
    parser.add_argument(
        "--include-constants",
        action="store_true",
        help="Also inventory module-level UPPER_CASE constants.",
    )


def _build_parser() -> argparse.ArgumentParser:
    """Build the plan/audit/check CLI parser."""
    parser = argparse.ArgumentParser(
        description="Generate DRY plans/audits and gate completed DRY reviews.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    plan = subparsers.add_parser(
        "plan",
        help="Generate a fresh file-by-file plan from the current package source.",
    )
    plan.add_argument("--root", type=Path, default=Path.cwd())
    plan.add_argument(
        "--package-root",
        type=Path,
        default=Path("django_strawberry_framework"),
    )
    plan.add_argument("--target-release", required=True)
    plan.add_argument(
        "--mode",
        choices=("autonomous", "pause-after-each-item"),
        default="autonomous",
    )
    plan.add_argument("--output", type=Path)
    plan.add_argument("--force", action="store_true")
    plan.add_argument("--generated-date")

    audit = subparsers.add_parser(
        "audit",
        help="Generate a static cross-file DRY evidence dossier.",
    )
    _add_target_arguments(audit)
    audit.add_argument(
        "--scan-root",
        type=Path,
        action="append",
        default=[],
        help=(
            "Python file/directory searched for uses and duplicates; repeatable. "
            "Defaults to package/tests/examples/scripts roots that exist."
        ),
    )
    audit.add_argument(
        "--context",
        type=Path,
        action="append",
        default=[],
        help="Non-Python context file included only in concept searches; repeatable.",
    )
    audit.add_argument(
        "--search-term",
        action="append",
        default=[],
        help="Literal concept to search across parsed Python/context files; repeatable.",
    )
    audit.add_argument("--case-sensitive", action="store_true")
    audit.add_argument("--duplicate-min-nodes", type=int, default=8)
    audit.add_argument("--literal-min-length", type=int, default=20)
    audit.add_argument("--max-evidence", type=int, default=25)
    audit.add_argument("--output", type=Path)
    audit.add_argument("--stdout", action="store_true")
    audit.add_argument("--force", action="store_true")
    audit.add_argument("--generated-date")

    check = subparsers.add_parser(
        "check",
        help="Verify a completed review covers every definition and required topic.",
    )
    _add_target_arguments(check)
    check.add_argument("--review", type=Path, required=True)
    check.add_argument("--require-topic", action="append", default=[])
    check.add_argument("--case-sensitive-topics", action="store_true")
    return parser


def _effective_excludes(args: argparse.Namespace) -> tuple[str, ...]:
    """Return default plus caller-supplied exclusion patterns."""
    defaults = () if args.no_default_excludes else DEFAULT_EXCLUDES
    return (*defaults, *args.exclude)


def _run_plan(args: argparse.Namespace) -> int:
    """Generate a fresh plan from current package source."""
    root = args.root.resolve()
    package_root = _resolve_path(args.package_root, root)
    if not package_root.is_dir():
        raise ValueError(f"--package-root is not a directory: {package_root.as_posix()}")
    target_release = args.target_release
    if not RELEASE_PATTERN.fullmatch(target_release):
        raise ValueError(
            f"invalid --target-release {target_release!r}; expected dotted digits such as 0.0.14",
        )
    output = _resolve_path(args.output or _default_output(target_release), root)
    if output.exists() and not args.force:
        raise FileExistsError(_overwrite_error(output))
    content, file_count, folder_count = _render_source_plan(
        package_root,
        target_release=target_release,
        generated_date=_validate_date(args.generated_date),
        mode=args.mode,
    )
    _atomic_write(output, content, force=args.force)
    print(
        f"Wrote {_display_path(output, root)} "
        f"({file_count} file item(s), {folder_count} folder integration item(s))",
    )
    return 0


def _run_audit(args: argparse.Namespace) -> int:
    """Execute dossier generation."""
    if args.stdout == (args.output is not None):
        raise ValueError("pass exactly one of --output or --stdout")
    if args.duplicate_min_nodes < 1:
        raise ValueError("--duplicate-min-nodes must be >= 1")
    if args.literal_min_length < 1:
        raise ValueError("--literal-min-length must be >= 1")
    if args.max_evidence < 1:
        raise ValueError("--max-evidence must be >= 1")

    root = args.root.resolve()
    output = _resolve_path(args.output, root) if args.output is not None else None
    if output is not None and output.exists() and not args.force:
        raise FileExistsError(_overwrite_error(output))
    audit = build_audit(
        root=root,
        targets=args.target,
        scan_roots=args.scan_root,
        contexts=args.context,
        exclude_patterns=_effective_excludes(args),
        search_terms=args.search_term,
        include_nested=args.include_nested,
        include_constants=args.include_constants,
        case_sensitive=args.case_sensitive,
        duplicate_min_nodes=args.duplicate_min_nodes,
        literal_min_length=args.literal_min_length,
        output=output,
    )
    report = render_audit_markdown(
        audit,
        generated_date=_validate_date(args.generated_date),
        maximum_evidence=args.max_evidence,
    )
    if args.stdout:
        print(report)
    else:
        assert output is not None
        _atomic_write(output, report, force=args.force)
        print(
            f"Wrote {_display_path(output, root)} "
            f"({len(audit.target_files)} target file(s), "
            f"{len(audit.target_symbols)} definition(s), "
            f"{len(audit.scan_files)} parsed scan file(s))",
        )
    if audit.target_failures:
        print("Target inventory is incomplete; see Parse/read failures.", file=sys.stderr)
        return 1
    return 0


def _run_check(args: argparse.Namespace) -> int:
    """Execute completed-review coverage checks."""
    result = check_review(
        root=args.root,
        targets=args.target,
        review=args.review,
        required_topics=args.require_topic,
        exclude_patterns=_effective_excludes(args),
        include_nested=args.include_nested,
        include_constants=args.include_constants,
        case_sensitive_topics=args.case_sensitive_topics,
    )
    if result.ok:
        print(
            f"OK: {result.symbol_count} target definition(s) and "
            f"{len(args.require_topic)} required topic(s) are covered.",
        )
        return 0
    print(
        f"FAILED: {len(result.missing_symbols)} definition(s) and "
        f"{len(result.missing_topics)} required topic(s) are missing.",
        file=sys.stderr,
    )
    for symbol in result.missing_symbols:
        print(f"  missing definition: {symbol.locator}", file=sys.stderr)
    for topic in result.missing_topics:
        print(f"  missing topic: {topic}", file=sys.stderr)
    return 1


def main(argv: Sequence[str] | None = None) -> int:
    """Run the selected DRY toolkit mode and return a process exit code."""
    raw_argv = sys.argv[1:] if argv is None else argv
    args = _build_parser().parse_args(raw_argv)
    try:
        if args.command == "plan":
            return _run_plan(args)
        if args.command == "audit":
            return _run_audit(args)
        if args.command == "check":
            return _run_check(args)
    except (FileExistsError, OSError, UnicodeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    raise AssertionError(f"unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
