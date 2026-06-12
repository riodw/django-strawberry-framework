#!/usr/bin/env python
"""List package Python files changed by each reachable commit.

The report is intentionally narrow: it scans commit history and records only
``*.py`` paths under ``django_strawberry_framework/``. It is meant to feed a
spec-attribution pass where a reviewer maps package source changes back to the
design spec or card that owned them.

By default the script walks every commit reachable from ``HEAD`` in reverse
topological order and omits commits that did not touch package Python files.
Merge commits are compared to their first parent, which answers the practical
question "what did this commit add to the current branch?". Use
``--merge-diff all-parents`` when auditing merge commits themselves.

Examples:
    uv run python scripts/list_package_python_changes_by_commit.py
    uv run python scripts/list_package_python_changes_by_commit.py --format json
    uv run python scripts/list_package_python_changes_by_commit.py --output package-history.md
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections.abc import Iterable, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path

DEFAULT_PACKAGE_DIR = "django_strawberry_framework"
DEFAULT_REVISION = "HEAD"


class GitHistoryError(RuntimeError):
    """A caller-correctable git history problem."""


@dataclass(frozen=True)
class ChangedFile:
    """One package Python path changed by a commit."""

    status: str
    path: str
    old_path: str | None = None

    @property
    def status_kind(self) -> str:
        """Return the stable one-letter status kind."""
        return self.status[:1]

    def sort_key(self) -> tuple[str, str, str]:
        """Return a deterministic display sort key."""
        return (self.path, self.old_path or "", self.status)


@dataclass(frozen=True)
class CommitChange:
    """One commit and its relevant package Python changes."""

    commit: str
    short_commit: str
    committed_at: str
    author_name: str
    subject: str
    parent_count: int
    files: list[ChangedFile]


def run_git(args: Sequence[str], *, cwd: Path | None = None) -> str:
    """Run ``git --no-pager <args>`` and return stdout."""
    try:
        result = subprocess.run(
            ["git", "--no-pager", *args],
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as error:
        stderr = error.stderr.strip()
        message = stderr or f"git {' '.join(args)} failed with exit code {error.returncode}"
        raise GitHistoryError(message) from error
    return result.stdout


def repo_root() -> Path:
    """Return the current repository root."""
    return Path(run_git(["rev-parse", "--show-toplevel"]).strip())


def is_shallow_repository(root: Path) -> bool:
    """Return whether the repository history is shallow."""
    return run_git(["rev-parse", "--is-shallow-repository"], cwd=root).strip() == "true"


def validate_revision(root: Path, revision: str) -> str:
    """Return the full commit hash for ``revision`` or raise a clear error."""
    try:
        return run_git(
            ["rev-parse", "--verify", f"{revision}^{{commit}}"],
            cwd=root,
        ).strip()
    except GitHistoryError as error:
        raise GitHistoryError(f"Not a valid commit revision: {revision}") from error


def normalize_package_dir(package_dir: str) -> str:
    """Return a git-style repo-relative package path."""
    normalized = package_dir.replace("\\", "/").strip().strip("/")
    if normalized.startswith("./"):
        normalized = normalized[2:]
    if not normalized:
        raise GitHistoryError("--package-dir must not be empty.")
    return normalized


def reachable_commits(root: Path, revision: str) -> list[str]:
    """Return every commit reachable from ``revision``, oldest first."""
    output = run_git(
        [
            "rev-list",
            "--reverse",
            "--topo-order",
            revision,
        ],
        cwd=root,
    )
    return [line for line in output.splitlines() if line]


def commit_parents(root: Path, commit: str) -> list[str]:
    """Return parent commit hashes for ``commit``."""
    output = run_git(
        [
            "show",
            "-s",
            "--format=%P",
            commit,
        ],
        cwd=root,
    ).strip()
    return output.split() if output else []


def commit_metadata(
    root: Path,
    commit: str,
    parent_count: int,
    files: list[ChangedFile],
) -> CommitChange:
    """Return commit metadata plus the relevant package changes."""
    output = run_git(
        [
            "show",
            "-s",
            "--format=%H%x00%h%x00%cI%x00%an%x00%s",
            commit,
        ],
        cwd=root,
    ).rstrip("\n")
    full_hash, short_hash, committed_at, author_name, subject = output.split("\0", 4)
    return CommitChange(
        commit=full_hash,
        short_commit=short_hash,
        committed_at=committed_at,
        author_name=author_name,
        subject=subject,
        parent_count=parent_count,
        files=files,
    )


def is_package_python_path(path: str, package_dir: str) -> bool:
    """Return whether ``path`` is a Python file under ``package_dir``."""
    normalized_package = package_dir.rstrip("/")
    return path.startswith(f"{normalized_package}/") and path.endswith(".py")


def parse_name_status_z(output: str, package_dir: str) -> list[ChangedFile]:
    """Parse ``git diff-tree --name-status -z`` output into package Python changes."""
    fields = output.split("\0")
    if fields and fields[-1] == "":
        fields.pop()

    changes: list[ChangedFile] = []
    index = 0
    while index < len(fields):
        status = fields[index]
        index += 1
        if status.startswith(("R", "C")):
            old_path = fields[index]
            new_path = fields[index + 1]
            index += 2
            if is_package_python_path(old_path, package_dir) or is_package_python_path(
                new_path,
                package_dir,
            ):
                changes.append(
                    ChangedFile(
                        status=status,
                        path=new_path,
                        old_path=old_path,
                    ),
                )
            continue

        path = fields[index]
        index += 1
        if is_package_python_path(path, package_dir):
            changes.append(ChangedFile(status=status, path=path))

    return sorted(changes, key=ChangedFile.sort_key)


def diff_tree_against(
    root: Path,
    commit: str,
    parent: str | None,
    package_dir: str,
) -> list[ChangedFile]:
    """Return package Python changes for ``commit`` against one parent or the empty tree."""
    base_args = [
        "diff-tree",
        "--no-commit-id",
        "--name-status",
        "-r",
        "-z",
        "-M",
    ]
    args = [*base_args, "--root", commit] if parent is None else [*base_args, parent, commit]
    output = run_git([*args, "--", package_dir], cwd=root)
    return parse_name_status_z(output, package_dir)


def dedupe_changes(changes: Iterable[ChangedFile]) -> list[ChangedFile]:
    """Return changes deduped by path pair and status kind."""
    deduped: dict[tuple[str, str | None, str], ChangedFile] = {}
    for change in changes:
        deduped.setdefault((change.path, change.old_path, change.status_kind), change)
    return sorted(deduped.values(), key=ChangedFile.sort_key)


def changed_files_for_commit(
    root: Path,
    commit: str,
    package_dir: str,
    merge_diff: str,
) -> tuple[int, list[ChangedFile]]:
    """Return relevant package Python changes for ``commit``."""
    parents = commit_parents(root, commit)
    if not parents:
        return 0, diff_tree_against(root, commit, None, package_dir)
    if len(parents) == 1 or merge_diff == "first-parent":
        return len(parents), diff_tree_against(root, commit, parents[0], package_dir)

    all_parent_changes: list[ChangedFile] = []
    for parent in parents:
        all_parent_changes.extend(diff_tree_against(root, commit, parent, package_dir))
    return len(parents), dedupe_changes(all_parent_changes)


def collect_history(
    root: Path,
    revision: str,
    package_dir: str,
    merge_diff: str,
    include_empty: bool,
) -> tuple[str, int, list[CommitChange]]:
    """Collect commit-by-commit package Python changes."""
    resolved_revision = validate_revision(root, revision)
    commits = reachable_commits(root, resolved_revision)
    commit_changes: list[CommitChange] = []
    for commit in commits:
        parent_count, files = changed_files_for_commit(root, commit, package_dir, merge_diff)
        if files or include_empty:
            commit_changes.append(commit_metadata(root, commit, parent_count, files))
    return resolved_revision, len(commits), commit_changes


def render_change(change: ChangedFile) -> str:
    """Render one changed path for Markdown output."""
    if change.old_path is None:
        return f"`{change.status}` `{change.path}`"
    return f"`{change.status}` `{change.old_path}` -> `{change.path}`"


def render_markdown(
    revision: str,
    package_dir: str,
    commits_scanned: int,
    commits: Sequence[CommitChange],
) -> str:
    """Render commit history as Markdown."""
    lines = [
        "# django_strawberry_framework Python changes by commit",
        "",
        f"Revision: `{revision}`",
        f"Scope: `{package_dir.rstrip('/')}/**/*.py`",
        f"Commits scanned: {commits_scanned}",
        f"Commits with matching changes: {sum(bool(commit.files) for commit in commits)}",
        "",
    ]
    for number, commit in enumerate(commits, start=1):
        lines.extend(
            [
                (
                    f"## {number}. `{commit.short_commit}` - {commit.committed_at} - "
                    f"{commit.subject}"
                ),
                "",
                f"Full commit: `{commit.commit}`",
                f"Author: {commit.author_name}",
                f"Parents: {commit.parent_count}",
                "",
            ],
        )
        if commit.files:
            lines.extend(f"- {render_change(change)}" for change in commit.files)
        else:
            lines.append("- No package Python changes.")
        lines.append("")
    return "\n".join(lines)


def render_json(
    revision: str,
    package_dir: str,
    commits_scanned: int,
    commits: Sequence[CommitChange],
) -> str:
    """Render commit history as stable JSON."""
    payload = {
        "revision": revision,
        "package_dir": package_dir.rstrip("/"),
        "scope": f"{package_dir.rstrip('/')}/**/*.py",
        "commits_scanned": commits_scanned,
        "commits_with_matching_changes": sum(bool(commit.files) for commit in commits),
        "commits": [asdict(commit) for commit in commits],
    }
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "List every commit's changed Python files under django_strawberry_framework/."
        ),
    )
    parser.add_argument(
        "--revision",
        default=DEFAULT_REVISION,
        help="Commit revision whose reachable history should be scanned. Defaults to HEAD.",
    )
    parser.add_argument(
        "--package-dir",
        default=DEFAULT_PACKAGE_DIR,
        help=(f"Repo-relative package directory to scan. Defaults to {DEFAULT_PACKAGE_DIR}/."),
    )
    parser.add_argument(
        "--format",
        choices=("markdown", "json"),
        default="markdown",
        help="Output format. Defaults to markdown.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Write the report to this path instead of stdout.",
    )
    parser.add_argument(
        "--include-empty",
        action="store_true",
        help="Include commits that did not touch package Python files.",
    )
    parser.add_argument(
        "--allow-shallow",
        action="store_true",
        help=(
            "Allow running in a shallow clone. Without this, shallow history is rejected "
            "because the report cannot prove it started at the project beginning."
        ),
    )
    parser.add_argument(
        "--merge-diff",
        choices=("first-parent", "all-parents"),
        default="first-parent",
        help=(
            "How to list files for merge commits. Defaults to first-parent, matching "
            "what landed on the current branch."
        ),
    )
    return parser.parse_args(argv)


def write_report(report: str, output: Path | None) -> None:
    """Write ``report`` to ``output`` or stdout."""
    if output is None:
        print(report, end="")
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the history report."""
    args = parse_args(sys.argv[1:] if argv is None else argv)
    root = repo_root()
    package_dir = normalize_package_dir(args.package_dir)
    if is_shallow_repository(root) and not args.allow_shallow:
        raise GitHistoryError(
            "Repository history is shallow; run `git fetch --unshallow` or pass "
            "`--allow-shallow` if a partial report is acceptable.",
        )

    revision, commits_scanned, commits = collect_history(
        root,
        args.revision,
        package_dir,
        args.merge_diff,
        args.include_empty,
    )
    if args.format == "json":
        report = render_json(revision, package_dir, commits_scanned, commits)
    else:
        report = render_markdown(revision, package_dir, commits_scanned, commits)
    write_report(report, args.output)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except GitHistoryError as error:
        print(error, file=sys.stderr)
        raise SystemExit(2) from error
