"""Render the generated portion of ``docs/TREE.md`` from package docstrings."""

from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MD_PATH = REPO_ROOT / "docs" / "TREE.md"
DEFAULT_PACKAGE_DIR = REPO_ROOT / "django_strawberry_framework"
DELIMITER = "## django_strawberry_framework (current on-disk layout)"
COMMENT_COLUMN = 34
TREE_BRANCH = "\u251c\u2500\u2500 "
TREE_LAST = "\u2514\u2500\u2500 "
TREE_PIPE = "\u2502   "
TREE_SPACE = "    "
FAKESHOP_APP_NAMES = (
    "glossary",
    "kanban",
    "library",
    "products",
    "scalars",
)
FAKESHOP_CONFIG_FILES = (
    "__init__.py",
    "settings.py",
    "schema.py",
    "urls.py",
    "wsgi.py",
)
TEST_LAYOUT_INTRO = [
    "## Test layout",
    "",
    "Tests live in four deliberate places, each chosen by what the test is proving. "
    "The root `tests/` tree protects package internals and mirrors "
    "`django_strawberry_framework/`. `examples/fakeshop/apps/<app>/tests/` protects "
    "one Django app at a time without live HTTP. `examples/fakeshop/tests/` protects "
    "project-level fakeshop behavior that belongs to no single app. "
    "`examples/fakeshop/test_query/` is the live `/graphql/` acceptance surface.",
    "",
    "**Coverage priority.** If a package line can be covered by a real fakeshop "
    "GraphQL request, put that test in `examples/fakeshop/test_query/`. Use the "
    "non-live fakeshop trees for services, models, admin, commands, URLs, or "
    "in-process schema execution. Use root `tests/` for package internals, invalid "
    "configuration, registry/finalizer mechanics, and paths unreachable through a "
    "realistic GraphQL request. Mock only when the real path is impossible. These "
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


class TreeRenderError(ValueError):
    """A caller-correctable TREE.md rendering error."""


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


def first_docstring_sentence(path: Path) -> str:
    """Return the first module-docstring sentence from a Python source file."""
    if path.suffix != ".py":
        return first_non_python_sentence(path)

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


def detail_paragraphs(path: Path) -> list[str]:
    """Return prose paragraphs after the summary sentence used by tree comments."""
    if path.suffix == ".py":
        paragraphs = python_docstring_paragraphs(path)
    elif path.suffix == ".md":
        paragraphs = markdown_paragraphs(path)
    else:
        return []

    if len(paragraphs) <= 1:
        return []
    return paragraphs[1:]


def folder_description(path: Path) -> str:
    """Return the folder description stored in ``path / "__init__.py"``."""
    init_path = path / "__init__.py"
    if not init_path.exists():
        return ""
    return first_docstring_sentence(init_path)


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


def sorted_children(path: Path) -> list[Path]:
    """Return visible child paths in deterministic tree order."""
    children = [
        child
        for child in path.iterdir()
        if child.name != "__pycache__" and child.name != "__init__.py"
    ]
    files = sorted((child for child in children if child.is_file()), key=lambda child: child.name)
    dirs = sorted((child for child in children if child.is_dir()), key=lambda child: child.name)
    return files + dirs


def render_children(path: Path, prefix: str = "") -> list[str]:
    """Render children under ``path`` using tree connector glyphs."""
    lines = []
    children = sorted_children(path)
    for index, child in enumerate(children):
        is_last = index == len(children) - 1
        connector = TREE_LAST if is_last else TREE_BRANCH
        child_prefix = f"{prefix}{connector}"
        next_prefix = f"{prefix}{TREE_SPACE if is_last else TREE_PIPE}"
        if child.is_dir():
            lines.append(
                comment_line(
                    child_prefix,
                    f"{child.name}/",
                    folder_description(child),
                    align_comment=False,
                ),
            )
            lines.extend(render_children(child, next_prefix))
        else:
            lines.append(
                comment_line(
                    child_prefix,
                    child.name,
                    first_docstring_sentence(child),
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
        comment_line(
            "",
            label,
            description,
            align_comment=False,
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


def render_app_test_tree(apps_dir: Path) -> list[str]:
    """Render every fakeshop per-app ``tests/`` package under one parent tree."""
    apps_dir = apps_dir.resolve()
    if not apps_dir.is_dir():
        raise TreeRenderError(f"Fakeshop apps directory does not exist: {apps_dir}")

    app_dirs = sorted(path for path in apps_dir.iterdir() if (path / "tests").is_dir())
    root_lines = [
        comment_line(
            "",
            "examples/fakeshop/apps/",
            "Per-Django-app, non-live tests that stay beside the app they protect.",
            align_comment=False,
        ),
    ]
    for app_index, app_dir in enumerate(app_dirs):
        app_is_last = app_index == len(app_dirs) - 1
        app_connector = TREE_LAST if app_is_last else TREE_BRANCH
        app_prefix = TREE_SPACE if app_is_last else TREE_PIPE
        root_lines.append(f"{app_connector}{app_dir.name}/")

        tests_dir = app_dir / "tests"
        root_lines.append(
            comment_line(
                f"{app_prefix}{TREE_LAST}",
                "tests/",
                folder_description(tests_dir),
                align_comment=False,
            ),
        )
        root_lines.extend(render_children(tests_dir, f"{app_prefix}{TREE_SPACE}"))
    return fenced_tree("examples/fakeshop/apps/*/tests/", root_lines)


def render_test_layout() -> list[str]:
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
                root_description=(
                    "Example-project tests for fakeshop behavior without live /graphql HTTP."
                ),
            ),
        ),
        *fenced_tree(
            "examples/fakeshop/test_query/",
            render_tree(
                examples_query_tests,
                root_label="examples/fakeshop/test_query/",
                root_description=("Live GraphQL HTTP tests for fakeshop's consumer-visible API."),
            ),
        ),
    ]


def render_fakeshop_project_tree(project_dir: Path) -> list[str]:
    """Render the high-level fakeshop project shape."""
    project_dir = project_dir.resolve()
    if not project_dir.is_dir():
        raise TreeRenderError(f"Fakeshop project directory does not exist: {project_dir}")

    config_dir = project_dir / "config"
    apps_dir = project_dir / "apps"
    tree_lines = [
        comment_line(
            "",
            "examples/fakeshop/",
            first_non_python_sentence(project_dir / "README.md"),
            align_comment=False,
        ),
        comment_line(
            TREE_BRANCH,
            "manage.py",
            first_docstring_sentence(project_dir / "manage.py"),
        ),
        comment_line(
            TREE_BRANCH,
            "config/",
            folder_description(config_dir),
            align_comment=False,
        ),
    ]

    for index, filename in enumerate(FAKESHOP_CONFIG_FILES):
        is_last = index == len(FAKESHOP_CONFIG_FILES) - 1
        connector = TREE_LAST if is_last else TREE_BRANCH
        description = (
            "" if filename == "__init__.py" else first_docstring_sentence(config_dir / filename)
        )
        tree_lines.append(
            comment_line(
                f"{TREE_PIPE}{connector}",
                filename,
                description,
            ),
        )

    tree_lines.append(
        comment_line(
            TREE_LAST,
            "apps/",
            folder_description(apps_dir),
            align_comment=False,
        ),
    )

    app_entries = ("__init__.py", *FAKESHOP_APP_NAMES)
    for index, entry in enumerate(app_entries):
        is_last = index == len(app_entries) - 1
        connector = TREE_LAST if is_last else TREE_BRANCH
        if entry == "__init__.py":
            tree_lines.append(
                comment_line(
                    f"{TREE_SPACE}{connector}",
                    entry,
                    "",
                ),
            )
            continue
        tree_lines.append(
            comment_line(
                f"{TREE_SPACE}{connector}",
                f"{entry}/",
                folder_description(apps_dir / entry),
                align_comment=False,
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
    return [
        *render_package_tree(package_dir),
        *render_test_layout(),
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
