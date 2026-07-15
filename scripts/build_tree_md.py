"""Render the generated portion of ``docs/TREE.md`` from docstrings + kanban predictions.

Current trees come from module docstrings and folder ``__init__.py`` docstrings.
The target-layout sections additionally merge in the planned ``TrackedPath``
rows linked from WIP/TODO kanban cards (``examples/fakeshop/db.sqlite3``), so
the future package/test shape renders from the same DB the board exports use.
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from collections.abc import Iterable, Iterator, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, TypeVar

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MD_PATH = REPO_ROOT / "docs" / "TREE.md"
DEFAULT_PACKAGE_DIR = REPO_ROOT / "django_strawberry_framework"
DELIMITER = "## django_strawberry_framework (current on-disk layout)"
COMMENT_COLUMN = 34
IGNORED_TREE_FILENAMES = frozenset(
    {
        "__init__.py",
    },
)
IGNORED_TREE_DIRNAMES = frozenset(
    {"__pycache__", "migrations"},
)
TREE_BRANCH = "\u251c\u2500\u2500 "
TREE_LAST = "\u2514\u2500\u2500 "
TREE_PIPE = "\u2502   "
TREE_SPACE = "    "
FAKESHOP_APP_NAMES = (
    "accounts",
    "glossary",
    "kanban",
    "library",
    "products",
    "scalars",
)
TEST_LAYOUT_INTRO = [
    "## Test layout",
    "",
    "Tests live in four deliberate places, each chosen by what the test is proving. "
    "The root `tests/` tree protects package internals and repository tooling; its "
    "subsystem directories broadly mirror `django_strawberry_framework/`. "
    "`examples/fakeshop/apps/<app>/tests/` protects "
    "one Django app at a time without live HTTP. `examples/fakeshop/tests/` protects "
    "project-level fakeshop behavior that belongs to no single app. "
    "`examples/fakeshop/test_query/` is the live `/graphql/` acceptance surface.",
    "",
    "**Coverage priority.** If a package line can be covered by a real fakeshop "
    "GraphQL request, put that test in `examples/fakeshop/test_query/`. Use the "
    "non-live fakeshop trees for services, models, admin, commands, URLs, or "
    "in-process schema execution. Use root `tests/` for repository tooling, package "
    "internals, invalid configuration, registry/finalizer mechanics, and paths "
    "unreachable through a realistic GraphQL request. Mock only when the real path "
    "is impossible. These "
    "placement rules are pinned in [`AGENTS.md`][agents].",
    "",
    "### Current test trees",
]
LINK_DEFINITIONS = """<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../AGENTS.md
[readme]: ../README.md

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
"""
T = TypeVar("T")


class TreeRenderError(ValueError):
    """A caller-correctable TREE.md rendering error."""


@dataclass(frozen=True)
class TreePosition:
    """Connector state for one child inside a text tree."""

    line_prefix: str
    child_prefix: str


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Render the dynamic django_strawberry_framework section of docs/TREE.md.",
    )
    parser.add_argument(
        "--md",
        type=Path,
        default=DEFAULT_MD_PATH,
        help="Markdown file to update. Defaults to docs/TREE.md.",
    )
    parser.add_argument(
        "--package-dir",
        type=Path,
        default=DEFAULT_PACKAGE_DIR,
        help="Package directory to render. Defaults to django_strawberry_framework/.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit with status 1 if docs/TREE.md is not already up to date.",
    )
    return parser.parse_args()


def python_docstring(path: Path) -> str:
    """Return the parsed module docstring for a Python source file."""
    try:
        module = ast.parse(path.read_text())
    except SyntaxError as error:
        raise TreeRenderError(f"{path} cannot be parsed: {error}") from error

    docstring = ast.get_docstring(module)
    if not docstring:
        raise TreeRenderError(f"{path} is missing a module docstring.")
    return docstring


def paragraphs_from_text(text: str) -> list[str]:
    """Collapse blank-line-separated prose paragraphs into single lines."""
    paragraphs = []
    current = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            if current:
                paragraphs.append(" ".join(current))
                current = []
            continue
        current.append(line)
    if current:
        paragraphs.append(" ".join(current))
    return paragraphs


def first_sentence_from_text(text: str, *, strip_markup: bool = False) -> str:
    """Return the first sentence from already-collapsed prose."""
    text = text.strip()
    if strip_markup:
        text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
        text = re.sub(r"``([^`]+)``", r"\1", text)
        text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\s+", " ", text)
    match = re.match(r"(.+?[.!?])(?:\s|$)", text)
    return match.group(1) if match else text


def python_docstring_paragraphs(path: Path) -> list[str]:
    """Return collapsed module-docstring paragraphs for a Python source file."""
    return paragraphs_from_text(python_docstring(path))


def first_python_docstring_sentence(path: Path) -> str:
    """Return the first module-docstring line from a Python source file."""
    docstring = python_docstring(path)
    sentence = next((line.strip() for line in docstring.splitlines() if line.strip()), "")
    if not sentence:
        raise TreeRenderError(f"{path} has an empty module docstring.")
    if not sentence.endswith("."):
        raise TreeRenderError(f"{path} first docstring line must be a sentence.")
    return sentence


def markdown_paragraphs(path: Path) -> list[str]:
    """Return collapsed prose paragraphs from markdown, ignoring headings and fences."""
    paragraphs = []
    current = []
    in_fence = False
    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if line.startswith("```"):
            if current:
                paragraphs.append(" ".join(current))
                current = []
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if not line or line.startswith("#") or line.startswith("<!--") or line.startswith("- "):
            if current:
                paragraphs.append(" ".join(current))
                current = []
            continue
        current.append(line)
    if current:
        paragraphs.append(" ".join(current))
    return paragraphs


def first_non_python_sentence(path: Path) -> str:
    """Return a useful first sentence for documented non-Python tree files."""
    if path.name == "py.typed":
        return ""
    if path.suffix != ".md":
        return ""

    for paragraph in markdown_paragraphs(path):
        return first_sentence_from_text(paragraph, strip_markup=True)
    return ""


def file_summary(path: Path) -> str:
    """Return the tree-comment summary for a file."""
    if path.suffix == ".py":
        return first_python_docstring_sentence(path)
    return first_non_python_sentence(path)


def prose_paragraphs(path: Path) -> list[str]:
    """Return prose paragraphs for files that contribute detail sections."""
    if path.suffix == ".py":
        return python_docstring_paragraphs(path)
    if path.suffix == ".md":
        return markdown_paragraphs(path)
    return []


def detail_paragraphs(path: Path) -> list[str]:
    """Return prose paragraphs after the summary sentence used by tree comments."""
    paragraphs = prose_paragraphs(path)
    if len(paragraphs) <= 1:
        return []
    return paragraphs[1:]


def command_summary(path: Path) -> str:
    """Return the role-section summary for one management command module."""
    summary = first_python_docstring_sentence(path)
    redundant_prefix = f"manage.py {path.stem} - "
    if summary.startswith(redundant_prefix):
        summary = summary.removeprefix(redundant_prefix)
    if summary:
        return f"{summary[0].upper()}{summary[1:]}"
    return summary


def management_command_files(app_dir: Path) -> list[Path]:
    """Return documented management command modules for one fakeshop app."""
    commands_dir = app_dir / "management" / "commands"
    if not commands_dir.is_dir():
        return []
    return [
        child
        for child in sorted_children(commands_dir)
        if child.is_file() and child.suffix == ".py"
    ]


def render_management_commands(app_dir: Path) -> list[str]:
    """Render management command summaries for one app role section."""
    command_files = management_command_files(app_dir)
    if not command_files:
        return []

    lines = ["Management commands:"]
    for command_file in command_files:
        lines.append(f"- `manage.py {command_file.stem}` - {command_summary(command_file)}")
    lines.append("")
    return lines


def folder_description(path: Path) -> str:
    """Return the folder description stored in ``path / "__init__.py"``."""
    init_path = path / "__init__.py"
    if not init_path.exists():
        return ""
    return first_python_docstring_sentence(init_path)


def comment_line(
    prefix: str,
    label: str,
    description: str,
    *,
    align_comment: bool = True,
) -> str:
    """Render one tree line with an optional aligned description comment."""
    line = f"{prefix}{label}"
    if not description:
        return line
    if not align_comment:
        return f"{line}    # {description}"
    if len(line) >= COMMENT_COLUMN:
        return f"{line}  # {description}"
    return f"{line:<{COMMENT_COLUMN}}# {description}"


def file_entry(prefix: str, path: Path, *, label: str | None = None) -> str:
    """Render one file entry for a tree."""
    return comment_line(
        prefix,
        label or path.name,
        file_summary(path),
    )


def directory_entry(
    prefix: str,
    path: Path,
    *,
    label: str | None = None,
    description: str | None = None,
) -> str:
    """Render one directory entry for a tree."""
    summary = folder_description(path) if description is None else description
    return comment_line(
        prefix,
        label or f"{path.name}/",
        summary,
        align_comment=False,
    )


def tree_position(prefix: str, index: int, count: int) -> TreePosition:
    """Return connector prefixes for a child at ``index`` of ``count``."""
    is_last = index == count - 1
    connector = TREE_LAST if is_last else TREE_BRANCH
    child_indent = TREE_SPACE if is_last else TREE_PIPE
    return TreePosition(
        line_prefix=f"{prefix}{connector}",
        child_prefix=f"{prefix}{child_indent}",
    )


def iter_tree_positions(items: Sequence[T], prefix: str = "") -> Iterator[tuple[T, TreePosition]]:
    """Pair items with the connector state they need inside a tree."""
    count = len(items)
    for index, item in enumerate(items):
        yield item, tree_position(prefix, index, count)


def sorted_children(path: Path, *, ignored_dirnames: frozenset[str] = frozenset()) -> list[Path]:
    """Return visible child paths in deterministic tree order."""
    excluded_dirnames = IGNORED_TREE_DIRNAMES | ignored_dirnames
    children = [
        child
        for child in path.iterdir()
        if (
            (child.is_dir() and child.name not in excluded_dirnames)
            or (child.is_file() and child.name not in IGNORED_TREE_FILENAMES)
        )
        and child.suffix != ".pyc"
    ]
    files = sorted((child for child in children if child.is_file()), key=lambda child: child.name)
    dirs = sorted((child for child in children if child.is_dir()), key=lambda child: child.name)
    return files + dirs


def render_children(
    path: Path,
    prefix: str = "",
    *,
    ignored_dirnames: frozenset[str] = frozenset(),
) -> list[str]:
    """Render children under ``path`` using tree connector glyphs."""
    lines = []
    children = sorted_children(path, ignored_dirnames=ignored_dirnames)
    for child, position in iter_tree_positions(children, prefix):
        if child.is_dir():
            lines.append(
                directory_entry(
                    position.line_prefix,
                    child,
                ),
            )
            lines.extend(
                render_children(
                    child,
                    position.child_prefix,
                    ignored_dirnames=ignored_dirnames,
                ),
            )
        else:
            lines.append(
                file_entry(
                    position.line_prefix,
                    child,
                ),
            )
    return lines


def render_tree(
    root_dir: Path,
    *,
    root_label: str | None = None,
    root_description: str | None = None,
) -> list[str]:
    """Render one filesystem tree from docstrings and folder descriptions."""
    root_dir = root_dir.resolve()
    if not root_dir.is_dir():
        raise TreeRenderError(f"Tree root does not exist: {root_dir}")

    label = root_label or f"{root_dir.name}/"
    description = folder_description(root_dir) if root_description is None else root_description
    tree_lines = [
        directory_entry(
            "",
            root_dir,
            label=label,
            description=description,
        ),
    ]
    tree_lines.extend(render_children(root_dir))
    return tree_lines


def fenced_tree(source: str, tree_lines: list[str]) -> list[str]:
    """Render one source label plus fenced tree block."""
    return [
        "",
        f"Source: `{source}`",
        "",
        "```text",
        *tree_lines,
        "```",
        "",
    ]


def render_package_tree(package_dir: Path) -> list[str]:
    """Render the current package tree as markdown lines."""
    package_dir = package_dir.resolve()
    return fenced_tree(
        f"{package_dir.relative_to(REPO_ROOT)}/",
        render_tree(package_dir),
    )


# ---------------------------------------------------------------------------
# Target layouts (current filesystem merged with planned WIP/TODO card paths)
# ---------------------------------------------------------------------------

PACKAGE_ROOT_PREFIX = "django_strawberry_framework/"
TEST_ROOT_PREFIXES = ("tests/", "examples/fakeshop/test_query/", "examples/fakeshop/tests/")
APP_TESTS_ROOT_RE = re.compile(r"^examples/fakeshop/apps/[^/]+/tests/")
TEST_ROOT_DESCRIPTIONS = {
    "examples/fakeshop/tests/": (
        "Project/config-level fakeshop tests that belong to no single app and do not use "
        "live /graphql HTTP."
    ),
    "examples/fakeshop/test_query/": (
        "Live GraphQL HTTP tests for fakeshop's consumer-visible API."
    ),
}
PLANNED_PATH_DESCRIPTIONS = {
    "django_strawberry_framework/aggregates/": (
        "Declarative AggregateSet output types with related, permissioned, "
        "selection-aware sync/async statistics."
    ),
    "django_strawberry_framework/fieldset/": (
        "FieldSet computed fields, resolver overrides, field permissions, and "
        "optimizer dependencies."
    ),
    "django_strawberry_framework/permissions/": (
        "Cascade-permission package migration plus opt-in node-sentinel redaction "
        "(``Meta.redaction_mode``)."
    ),
}
TARGET_PATH_REPLACEMENTS = {
    "django_strawberry_framework/permissions/": ("django_strawberry_framework/permissions.py",),
}


@dataclass(frozen=True)
class PlannedPath:
    """One planned repository path owned by a WIP/TODO kanban card."""

    path: str
    is_directory: bool
    card_id: str
    card_title: str

    @property
    def description(self) -> str:
        """Return the tree-comment annotation for this planned entry."""
        summary = PLANNED_PATH_DESCRIPTIONS.get(self.path, self.card_title)
        return f"planned by {self.card_id} - {summary}"


@dataclass
class TargetNode:
    """One entry of a merged current+planned tree."""

    name: str
    is_dir: bool
    description: str
    children: dict[str, TargetNode] = field(default_factory=dict)


def fetch_planned_paths() -> list[PlannedPath]:
    """Return planned TrackedPath rows linked from WIP/TODO kanban cards.

    Backlog cards and DONE-card historical paths never qualify: only
    ``is_current=False`` rows with at least one ``wip``/``todo`` card link are
    planned, and the lowest-numbered linking card owns the annotation.
    """
    from build_kanban_html import configure_django

    configure_django()
    from apps.kanban.models import TrackedPath

    rows = (
        TrackedPath.objects.filter(
            is_current=False,
            cards__status__key__in=("wip", "todo"),
        )
        .distinct()
        .order_by("path")
        .prefetch_related("cards__status", "cards__milestone", "cards__target_version")
    )
    return _planned_paths_from_rows(rows)


def _planned_paths_from_rows(rows: Iterable[Any]) -> list[PlannedPath]:
    """Build planned entries from TrackedPath rows, skipping paths already on disk.

    A row whose path already exists in the working tree has effectively shipped -
    only its card status lags - so it must not be annotated as a planned entry.
    The lowest-numbered ``wip``/``todo`` card owns each surviving entry.
    """
    planned = []
    for row in rows:
        if (REPO_ROOT / row.path).exists():
            continue
        owner = min(
            (card for card in row.cards.all() if card.status.key in ("wip", "todo")),
            key=lambda card: card.number,
        )
        planned.append(
            PlannedPath(
                path=row.path,
                is_directory=row.is_directory,
                card_id=owner.card_id,
                card_title=owner.title,
            ),
        )
    return planned


def planned_path_root(path: str) -> str | None:
    """Return the package/test root that owns a planned path, or ``None``."""
    if path.startswith(PACKAGE_ROOT_PREFIX):
        return PACKAGE_ROOT_PREFIX
    for root in TEST_ROOT_PREFIXES:
        if path.startswith(root):
            return root
    match = APP_TESTS_ROOT_RE.match(path)
    return match.group(0) if match else None


def filesystem_target_node(path: Path, *, label: str, description: str) -> TargetNode:
    """Build the merged-tree node structure for one on-disk directory."""
    node = TargetNode(name=label, is_dir=True, description=description)
    for child in sorted_children(path):
        if child.is_dir():
            node.children[f"{child.name}/"] = filesystem_target_node(
                child,
                label=f"{child.name}/",
                description=folder_description(child),
            )
        else:
            node.children[child.name] = TargetNode(
                name=child.name,
                is_dir=False,
                description=file_summary(child),
            )
    return node


def insert_planned_path(root_node: TargetNode, root_prefix: str, planned: PlannedPath) -> None:
    """Graft one planned path into a filesystem-backed target tree.

    Intermediate directories that do not exist yet inherit the planned
    annotation; segments that already exist on disk keep their docstring
    description.
    """
    segments = planned.path.removeprefix(root_prefix).rstrip("/").split("/")
    node = root_node
    for index, segment in enumerate(segments):
        is_dir = planned.is_directory or index < len(segments) - 1
        name = f"{segment}/" if is_dir else segment
        child = node.children.get(name)
        if child is None:
            child = TargetNode(name=name, is_dir=is_dir, description=planned.description)
            node.children[name] = child
        node = child


def remove_target_replacements(
    root_node: TargetNode,
    root_prefix: str,
    planned: PlannedPath,
) -> None:
    """Remove current paths explicitly superseded by one planned target path."""
    for replaced_path in TARGET_PATH_REPLACEMENTS.get(planned.path, ()):
        segments = replaced_path.removeprefix(root_prefix).rstrip("/").split("/")
        node = root_node
        for segment in segments[:-1]:
            child = node.children.get(f"{segment}/")
            if child is None:
                break
            node = child
        else:
            node.children.pop(segments[-1], None)


def render_target_children(node: TargetNode, prefix: str = "") -> list[str]:
    """Render merged-tree children using the same connector glyphs as render_children."""
    files = sorted(
        (child for child in node.children.values() if not child.is_dir),
        key=lambda child: child.name,
    )
    dirs = sorted(
        (child for child in node.children.values() if child.is_dir),
        key=lambda child: child.name,
    )
    lines = []
    for child, position in iter_tree_positions(files + dirs, prefix):
        lines.append(
            comment_line(
                position.line_prefix,
                child.name,
                child.description,
                align_comment=not child.is_dir,
            ),
        )
        if child.is_dir:
            lines.extend(render_target_children(child, position.child_prefix))
    return lines


def render_target_tree(
    root_dir: Path,
    root_prefix: str,
    planned_paths: Sequence[PlannedPath],
    *,
    root_description: str | None = None,
) -> list[str]:
    """Render one merged current+planned tree rooted at ``root_prefix``."""
    root_dir = root_dir.resolve()
    if not root_dir.is_dir():
        raise TreeRenderError(f"Tree root does not exist: {root_dir}")

    description = folder_description(root_dir) if root_description is None else root_description
    root_node = filesystem_target_node(root_dir, label=root_prefix, description=description)
    for planned in planned_paths:
        remove_target_replacements(root_node, root_prefix, planned)
        insert_planned_path(root_node, root_prefix, planned)
    return [
        comment_line("", root_node.name, root_node.description, align_comment=False),
        *render_target_children(root_node),
    ]


def render_target_package_layout(
    package_dir: Path,
    planned_paths: Sequence[PlannedPath],
) -> list[str]:
    """Render the target package layout section (current tree + planned paths)."""
    package_planned = [
        planned
        for planned in planned_paths
        if planned_path_root(planned.path) == PACKAGE_ROOT_PREFIX
    ]
    return [
        "## django_strawberry_framework (target package layout)",
        "",
        "The current package tree merged with every not-yet-existing path linked from "
        "a WIP/TODO card in [`KANBAN.md`](../KANBAN.md). Each planned entry names the "
        "card that introduces it; backlog cards and DONE-card historical paths are "
        "ignored.",
        *fenced_tree(
            f"{PACKAGE_ROOT_PREFIX} (+ planned card paths)",
            render_target_tree(package_dir.resolve(), PACKAGE_ROOT_PREFIX, package_planned),
        ),
    ]


def render_target_test_shape(planned_paths: Sequence[PlannedPath]) -> list[str]:
    """Render the target test shape section for test roots with planned paths."""
    planned_by_root: dict[str, list[PlannedPath]] = {}
    for planned in planned_paths:
        root = planned_path_root(planned.path)
        if root and root != PACKAGE_ROOT_PREFIX:
            planned_by_root.setdefault(root, []).append(planned)

    lines = [
        "",
        "### Target test shape",
        "",
        "The current test trees merged with the not-yet-existing test paths linked "
        "from WIP/TODO cards, annotated the same way as the target package layout. "
        "Test roots without planned additions match their current trees above.",
    ]
    for root in sorted(planned_by_root):
        lines.extend(
            fenced_tree(
                f"{root} (+ planned card paths)",
                render_target_tree(
                    REPO_ROOT / root,
                    root,
                    planned_by_root[root],
                    root_description=TEST_ROOT_DESCRIPTIONS.get(root),
                ),
            ),
        )
    return lines


def render_app_test_tree(apps_dir: Path) -> list[str]:
    """Render every fakeshop per-app ``tests/`` package under one parent tree."""
    apps_dir = apps_dir.resolve()
    if not apps_dir.is_dir():
        raise TreeRenderError(f"Fakeshop apps directory does not exist: {apps_dir}")

    app_dirs = sorted(path for path in apps_dir.iterdir() if (path / "tests").is_dir())
    root_lines = [
        directory_entry(
            "",
            apps_dir,
            label="examples/fakeshop/apps/",
            description="Per-Django-app, non-live tests that stay beside the app they protect.",
        ),
    ]
    for app_dir, position in iter_tree_positions(app_dirs):
        root_lines.append(directory_entry(position.line_prefix, app_dir, description=""))

        tests_dir = app_dir / "tests"
        root_lines.append(
            directory_entry(
                f"{position.child_prefix}{TREE_LAST}",
                tests_dir,
            ),
        )
        root_lines.extend(render_children(tests_dir, f"{position.child_prefix}{TREE_SPACE}"))
    return fenced_tree("examples/fakeshop/apps/*/tests/", root_lines)


def render_test_layout(planned_paths: Sequence[PlannedPath]) -> list[str]:
    """Render the generated test layout section."""
    examples_tests = REPO_ROOT / "examples" / "fakeshop" / "tests"
    examples_query_tests = REPO_ROOT / "examples" / "fakeshop" / "test_query"
    return [
        "",
        *TEST_LAYOUT_INTRO,
        *fenced_tree(
            "tests/",
            render_tree(REPO_ROOT / "tests"),
        ),
        *render_app_test_tree(REPO_ROOT / "examples" / "fakeshop" / "apps"),
        *fenced_tree(
            "examples/fakeshop/tests/",
            render_tree(
                examples_tests,
                root_label="examples/fakeshop/tests/",
                root_description=TEST_ROOT_DESCRIPTIONS["examples/fakeshop/tests/"],
            ),
        ),
        *fenced_tree(
            "examples/fakeshop/test_query/",
            render_tree(
                examples_query_tests,
                root_label="examples/fakeshop/test_query/",
                root_description=TEST_ROOT_DESCRIPTIONS["examples/fakeshop/test_query/"],
            ),
        ),
        *render_target_test_shape(planned_paths),
    ]


def render_fakeshop_project_tree(project_dir: Path) -> list[str]:
    """Render the high-level fakeshop project shape."""
    project_dir = project_dir.resolve()
    if not project_dir.is_dir():
        raise TreeRenderError(f"Fakeshop project directory does not exist: {project_dir}")

    config_dir = project_dir / "config"
    apps_dir = project_dir / "apps"
    root_files = [
        child
        for child in sorted_children(project_dir)
        if child.is_file() and child.suffix == ".py"
    ]
    tree_lines = [
        directory_entry(
            "",
            project_dir,
            label="examples/fakeshop/",
            description=first_non_python_sentence(project_dir / "README.md"),
        ),
    ]
    tree_lines.extend(file_entry(TREE_BRANCH, root_file) for root_file in root_files)
    tree_lines.extend(
        [
            directory_entry(
                TREE_BRANCH,
                config_dir,
            ),
            *render_children(config_dir, TREE_PIPE),
            directory_entry(
                TREE_LAST,
                apps_dir,
            ),
        ],
    )

    app_entries = FAKESHOP_APP_NAMES
    for entry, position in iter_tree_positions(app_entries, TREE_SPACE):
        tree_lines.append(
            directory_entry(
                position.line_prefix,
                apps_dir / entry,
            ),
        )
        tree_lines.extend(
            render_children(
                apps_dir / entry,
                position.child_prefix,
                ignored_dirnames=frozenset({"tests"}),
            ),
        )

    return tree_lines


def render_fakeshop_app_details(project_dir: Path) -> list[str]:
    """Render app responsibility paragraphs from app package docstrings."""
    apps_dir = project_dir / "apps"
    lines = ["### App roles", ""]
    for paragraph in detail_paragraphs(apps_dir / "__init__.py"):
        lines.extend([paragraph, ""])

    for app_name in FAKESHOP_APP_NAMES:
        paragraphs = detail_paragraphs(apps_dir / app_name / "__init__.py")
        if not paragraphs:
            continue
        lines.extend([f"`apps.{app_name}/`", ""])
        for paragraph in paragraphs:
            lines.extend([paragraph, ""])
        lines.extend(render_management_commands(apps_dir / app_name))
    return lines


def render_fakeshop_project() -> list[str]:
    """Render the fakeshop example-project section."""
    project_dir = REPO_ROOT / "examples" / "fakeshop"
    return [
        "",
        "## Fakeshop example project",
        "",
        "### Project tree",
        *fenced_tree(
            "examples/fakeshop/",
            render_fakeshop_project_tree(project_dir),
        ),
        *render_fakeshop_app_details(project_dir),
    ]


def render_generated_tail(package_dir: Path) -> list[str]:
    """Render every section owned by this script after the package delimiter."""
    planned_paths = fetch_planned_paths()
    return [
        *render_package_tree(package_dir),
        *render_target_package_layout(package_dir, planned_paths),
        *render_test_layout(planned_paths),
        *render_fakeshop_project(),
        LINK_DEFINITIONS,
    ]


def render_tree_doc(md_path: Path, package_dir: Path) -> str:
    """Return a full ``docs/TREE.md`` document with a regenerated dynamic tail."""
    current = md_path.read_text()
    marker_index = current.find(DELIMITER)
    if marker_index == -1:
        raise TreeRenderError(f"{md_path} is missing delimiter line: {DELIMITER}")

    marker_end = marker_index + len(DELIMITER)
    if marker_end < len(current) and current[marker_end] not in {"\n", "\r"}:
        raise TreeRenderError(f"{md_path} delimiter must be on its own line: {DELIMITER}")

    line_end = current.find("\n", marker_end)
    preserved = f"{current[:marker_end]}\n" if line_end == -1 else current[: line_end + 1]
    generated = "\n".join(render_generated_tail(package_dir)).rstrip()
    return f"{preserved}{generated}\n"


def main() -> int:
    """CLI entry point."""
    args = parse_args()
    rendered = render_tree_doc(args.md, args.package_dir)
    current = args.md.read_text()
    if args.check:
        if current != rendered:
            print(f"{args.md} is not up to date; run scripts/build_tree_md.py.", file=sys.stderr)
            return 1
        print(f"{args.md} is up to date.")
        return 0

    args.md.write_text(rendered)
    print(f"Wrote {args.md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
