#!/usr/bin/env python
"""Count the Django model classes declared anywhere under ``tests/``.

A plain grep for ``models.Model`` misses a multi-table-inheritance or proxy
child whose base is another model, so the census parses every module with
``ast`` and closes over bases: a class is a model when a base resolves to
Django's ``Model`` or to a model class, whether that class is declared in the
same file or imported. Imported bases are resolved by module import path
(``from apps.library.models import Shelf``, ``from apps.library import models
as library_models`` then ``library_models.Shelf``, relative imports) against
the repository root and ``examples/fakeshop``, and the imported module is
itself censused the same way, so a proxy of a real fakeshop model counts.
Models built with ``type(name, (models.Model,), attrs)`` count too. Nested
declarations (models built inside a test function or fixture) are counted
because ``ast.walk`` visits every scope.

Output is plain text: ``TOTAL N`` then one ``<count>  <path>`` line per file,
largest first, paths relative to ``tests/``.
"""

from __future__ import annotations

import ast
import collections
import functools
from collections.abc import Callable, Iterator
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TESTS_ROOT = REPO_ROOT / "tests"
IMPORT_ROOTS = (REPO_ROOT, REPO_ROOT / "examples" / "fakeshop")
DJANGO_MODEL_MODULES = frozenset({"django.db.models", "django.db.models.base"})
MODEL_BASE_MODULES = ("models", "djmodels", "dj_models")
FUNCTIONS = (ast.FunctionDef, ast.AsyncFunctionDef)
SCOPES = (ast.Module, *FUNCTIONS, ast.ClassDef)

ModelNode = ast.ClassDef | ast.Call


def _module_file(dotted: str) -> Path | None:
    """Return the first-party source file for ``dotted``, or ``None`` when it has none."""
    rel = Path(*dotted.split("."))
    for root in IMPORT_ROOTS:
        for candidate in (root / rel.with_suffix(".py"), root / rel / "__init__.py"):
            if candidate.is_file():
                return candidate
    return None


def _package_of(path: Path) -> str | None:
    """Return the dotted package that holds ``path``, for resolving relative imports."""
    resolved = path.resolve()
    for root in IMPORT_ROOTS:
        try:
            rel = resolved.relative_to(root)
        except ValueError:
            continue
        return ".".join(rel.parent.parts)
    return None


def _import_map(tree: ast.Module, path: Path | None) -> dict[str, tuple[str, str | None]]:
    """Map each bound name to ``(module, attribute)``; ``attribute`` is ``None`` for a module."""
    bound: dict[str, tuple[str, str | None]] = {}
    package = _package_of(path) if path is not None else None
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.asname:
                    bound[alias.asname] = (alias.name, None)
                else:
                    head = alias.name.split(".")[0]
                    bound[head] = (head, None)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if node.level:
                if package is None:
                    continue
                parts = package.split(".") if package else []
                parts = parts[: len(parts) - (node.level - 1)] if node.level > 1 else parts
                module = ".".join([*parts, module] if module else parts)
            for alias in node.names:
                bound[alias.asname or alias.name] = (module, alias.name)
    return bound


def _is_model_in(module: str, attr: str) -> bool:
    """Return whether ``module.attr`` is Django's ``Model`` or a first-party model class."""
    if module in DJANGO_MODEL_MODULES and attr == "Model":
        return True
    source = _module_file(module)
    return source is not None and attr in _top_level_models(source)


def _resolves_to_model(
    expr: ast.expr,
    local_model: Callable[[str], bool | None],
    imports: dict[str, tuple[str, str | None]],
) -> bool:
    """Return whether the base expression ``expr`` names a model class."""
    text = ast.unparse(expr)
    head, _, tail = text.rpartition(".")
    if not head:
        known = local_model(tail)
        if known is not None:
            return known
        if tail in imports:
            module, attr = imports[tail]
            return attr is not None and _is_model_in(module, attr)
        return False
    if tail == "Model" and head in MODEL_BASE_MODULES:
        return True
    first, _, rest = head.partition(".")
    if first not in imports:
        return False
    module, attr = imports[first]
    dotted = ".".join(part for part in (module, attr, rest) if part)
    return _is_model_in(dotted, tail)


def _type_call_model(
    node: ast.Call,
    local_model: Callable[[str], bool | None],
    imports: dict[str, tuple[str, str | None]],
) -> bool:
    """Return whether ``node`` is ``type(name, (<model base>, ...), attrs)``."""
    return (
        isinstance(node.func, ast.Name)
        and node.func.id == "type"
        and len(node.args) == 3
        and isinstance(node.args[1], ast.Tuple)
        and any(_resolves_to_model(elt, local_model, imports) for elt in node.args[1].elts)
    )


def _census_tree(tree: ast.Module, path: Path | None) -> tuple[list[ModelNode], set[str]]:
    """Return every model node in ``tree`` plus the names of its top-level model classes.

    A bare base name resolves lexically, as Python binds it: the nearest visible scope
    (the innermost one, then enclosing non-class scopes) declaring a class of that name
    decides, by its last declaration before the use, or its final one once the use sits
    inside a function; a plain class shadows a same-named model or import. A function is
    assumed to run after its enclosing scope finished executing, so it sees final bindings;
    a call made mid-module before a later rebinding is out of reach of a static census.
    """
    imports = _import_map(tree, path)
    parent = {child: node for node in ast.walk(tree) for child in ast.iter_child_nodes(node)}

    def scopes(node: ast.AST) -> Iterator[ast.AST]:
        """Yield the scopes enclosing ``node``, innermost first.

        Only a body opens a scope: a function's or class's header (defaults, decorators,
        annotations, bases, keywords) runs in the enclosing one.
        """
        child = node
        while child in parent:
            node = parent[child]
            if isinstance(node, ast.Module) or (isinstance(node, SCOPES) and child in node.body):
                yield node
            child = node

    classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
    declared: dict[tuple[ast.AST, str], list[ast.ClassDef]] = {}
    for node in classes:
        declared.setdefault((next(scopes(node)), node.name), []).append(node)
    models: set[ast.ClassDef] = set()

    def position(node: ModelNode) -> tuple[int, int]:
        """Return where ``node`` starts; ``ast.walk`` order is breadth-first, not textual."""
        return node.lineno, node.col_offset

    def lookup(node: ModelNode, name: str) -> bool | None:
        """Return whether ``name`` seen from ``node`` is a local model, ``None`` if undeclared."""
        running = True
        for index, scope in enumerate(scopes(node)):
            if index == 0 or not isinstance(scope, ast.ClassDef):
                bound = [
                    decl
                    for decl in declared.get((scope, name), [])
                    if not running or position(decl) < position(node)
                ]
                if bound:
                    return max(bound, key=position) in models
            running = running and not isinstance(scope, FUNCTIONS)
        return None

    changed = True
    while changed:
        changed = False
        for node in classes:
            local_model = functools.partial(lookup, node)
            if node not in models and any(
                _resolves_to_model(base, local_model, imports) for base in node.bases
            ):
                models.add(node)
                changed = True
    found: list[ModelNode] = [node for node in classes if node in models]
    found.extend(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and _type_call_model(node, functools.partial(lookup, node), imports)
    )
    top_level = {
        name
        for (scope, name), decls in declared.items()
        if scope is tree and max(decls, key=position) in models
    }
    return found, top_level


@functools.cache
def _top_level_models(path: Path) -> frozenset[str]:
    """Return the module-level model class names ``path`` declares."""
    return frozenset(_census_tree(ast.parse(path.read_text()), path)[1])


def model_classes(source: str, path: Path | None = None) -> list[ModelNode]:
    """Return every model declaration in ``source`` (class or ``type()`` call) by base closure."""
    return _census_tree(ast.parse(source), path)[0]


def model_name(node: ModelNode) -> str:
    """Return the declared name of a model node, ``<type()>`` for a non-literal name."""
    if isinstance(node, ast.ClassDef):
        return node.name
    first = node.args[0]
    if isinstance(first, ast.Constant) and isinstance(first.value, str):
        return first.value
    return "<type()>"


def census(root: Path = TESTS_ROOT) -> collections.Counter[str]:
    """Return ``{path relative to root: model count}`` for every file with a model."""
    counts: collections.Counter[str] = collections.Counter()
    for path in sorted(root.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        found = len(model_classes(path.read_text(), path))
        if found:
            counts[path.relative_to(root).as_posix()] = found
    return counts


def main() -> None:
    """Print the census total and the per-file counts."""
    counts = census()
    print("TOTAL", sum(counts.values()))
    for rel, count in sorted(counts.items(), key=lambda item: (-item[1], item[0])):
        print(f"{count:4d}  {rel}")


if __name__ == "__main__":
    main()
