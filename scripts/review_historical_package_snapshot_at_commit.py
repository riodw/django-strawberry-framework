"""Generate stripped/overview shadow files for a package snapshot.

Enumerates every ``.py`` file under a target package directory at a given
commit and runs ``review_inspect`` against each file's content as it existed
*at that commit* (the working tree is never read). Outputs land in
``docs/shadow/current/`` with the usual ``a__b__c`` stem scheme. This is a
single flat folder (one snapshot, no old/new sides) and is this script's
dedicated, fixed output location: each run is rendered and validated in a
temporary sibling, then published as one complete replacement (including an
empty result), while the diff helper's sibling
``docs/shadow/{old,new,diff}/`` folders are left untouched -- each script owns
and replaces only its own folder(s) under ``docs/shadow/``, so the two never
clobber each other.

Use this when you want a static review snapshot of the entire package at
some historical checkout, without actually checking that commit out and
without limiting the file set to whatever happens to have changed since.
Paths containing ``test`` are excluded to match the diff helper's contract,
and that exclusion is real rather than theoretical: it removes the whole
``django_strawberry_framework/testing/`` subpackage from every snapshot, so a
consumer of this folder must not read a missing stem as a file that did not
exist at the commit. :func:`snapshot_excludes` is the single source of that
rule; ask it rather than re-deriving the predicate.

``review_inspect.main`` is imported and called in-process so the
orchestrator does not pay Python / ``uv`` startup cost per file.

This module is also the canonical home for the shared review-orchestration
plumbing -- the git helpers and the ``_materialize_and_inspect`` primitive that
renders ``commit:path`` through ``review_inspect`` into an output dir. The diff
helper (``review_changed_python_diffs_against_head``) imports these rather than
duplicating them.

Usage:
    uv run python scripts/review_historical_package_snapshot_at_commit.py <commit-hash> [--package-dir DIR]

The ``uv run`` prefix is required so the script sees the project's virtual
environment (it imports ``review_inspect`` and the inspector depends on the
project's pinned Python / dependency versions). Run from anywhere inside
the repository; the orchestrator resolves ``git rev-parse --show-toplevel``
and writes outputs under ``docs/shadow/current/`` at the repo root.

Example:
    uv run python scripts/review_historical_package_snapshot_at_commit.py \
        9096519590040fa25484e05b6a104cb5652b9676 \
        --package-dir examples/fakeshop/apps/library
"""

from __future__ import annotations

import argparse
import contextlib
import io
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Sequence
from pathlib import Path

if __package__:
    from scripts.review_inspect import main as review_inspect_main
else:
    from review_inspect import main as review_inspect_main

SHADOW_DIR = Path("docs/shadow/current")
DEFAULT_PACKAGE_DIR = "django_strawberry_framework"


def normalize_package_dir(repo_root: Path, package_dir: str) -> str:
    """Return a safe repo-relative package directory.

    Resolve the filesystem directory once before it becomes a Git pathspec:
    this rejects absolute/outside paths, follows existing symlinks so they
    cannot escape the repository, and removes spellings that would make the
    live and historical inventories disagree.
    """
    candidate = Path(package_dir)
    if candidate.is_absolute():
        raise ValueError("--package-dir must be relative to the repository root")
    resolved = (repo_root / candidate).resolve()
    try:
        relative = resolved.relative_to(repo_root.resolve())
    except ValueError as error:
        raise ValueError("--package-dir must stay inside the repository root") from error
    return relative.as_posix() if relative.parts else "."


def _run_git(args: Sequence[str]) -> str:
    """Run ``git --no-pager <args>`` and return its stdout."""
    result = subprocess.run(
        ["git", "--no-pager", *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def _validate_commit(commit: str) -> None:
    """Exit with code 2 if ``commit`` does not resolve to a real commit."""
    try:
        subprocess.run(
            [
                "git",
                "rev-parse",
                "--verify",
                "--quiet",
                f"{commit}^{{commit}}",
            ],
            check=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError:
        print(f"Not a valid commit hash: {commit}", file=sys.stderr)
        sys.exit(2)


def snapshot_excludes(path: str) -> bool:
    """Return whether ``path`` is outside every snapshot this script writes.

    The one home for the snapshot's inclusion rule, so a caller that needs to
    explain a missing stem cannot drift from the rule that produced it. A path
    is excluded when it is not Python, when it is an ``__init__.py``, or when it
    contains ``test`` -- the last clause matches the diff helper's contract and
    also drops ``django_strawberry_framework/testing/``, which is ordinary
    package source rather than a test tree.
    """
    return not path.endswith(".py") or "test" in path or Path(path).name == "__init__.py"


def _tree_paths_at_commit(commit: str, package_dir: str) -> list[str]:
    """Return exact repo-relative paths below ``package_dir`` at ``commit``.

    ``--full-tree`` plus a top-level literal pathspec makes the result
    independent of the caller's current directory and prevents pathspec magic
    in a directory name. NUL framing preserves Unicode and control characters
    in tracked filenames without Git's quoting layer changing their spelling.
    """
    pathspec = ":(top,literal)" if package_dir == "." else f":(top,literal){package_dir}"
    output = _run_git(
        [
            "ls-tree",
            "-r",
            "-z",
            "--name-only",
            "--full-tree",
            commit,
            "--",
            pathspec,
        ],
    )
    return [path for path in output.split("\0") if path]


def _package_python_files_at_commit(commit: str, package_dir: str) -> list[str]:
    """Return every snapshot-eligible ``.py`` path under ``package_dir`` at ``commit``.

    Uses ``git ls-tree -r`` so the working tree is never consulted; eligibility
    is :func:`snapshot_excludes`.
    """
    return [
        path for path in _tree_paths_at_commit(commit, package_dir) if not snapshot_excludes(path)
    ]


def _stem_for(path: str) -> str:
    """Convert ``a/b/c.py`` into the ``a__b__c`` stem used by review artifacts."""
    return Path(path).with_suffix("").as_posix().replace("/", "__")


def _file_at_commit(commit: str, path: str) -> str | None:
    """Return the file contents at ``commit:path``, or ``None`` if absent there.

    The ``cat-file -e`` guard lets the diff helper reuse this for added/deleted
    files; the snapshot caller feeds only paths from ``git ls-tree``, so it never
    reaches the ``None`` branch.
    """
    exists = subprocess.run(
        [
            "git",
            "cat-file",
            "-e",
            f"{commit}:{path}",
        ],
        capture_output=True,
        check=False,
    )
    if exists.returncode != 0:
        return None
    return _run_git(["show", f"{commit}:{path}"])


def _inspect_quiet(target: Path, output_dir: Path, root: Path) -> None:
    """Invoke ``review_inspect.main`` while silencing its stdout chatter."""
    with contextlib.redirect_stdout(io.StringIO()):
        exit_code = review_inspect_main(
            [
                str(target),
                "--output-dir",
                str(output_dir),
                "--root",
                str(root),
            ],
        )
    if exit_code != 0:
        raise RuntimeError(
            f"review_inspect failed for {target} (exit code {exit_code}).",
        )


def _clear_shadow_output(output_dir: Path) -> None:
    """Delete existing shadow output before writing a fresh snapshot."""
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)
        return
    for child in sorted(output_dir.iterdir()):
        if child.is_dir():
            for nested in sorted(child.rglob("*"), reverse=True):
                if nested.is_file() or nested.is_symlink():
                    nested.unlink()
                else:
                    nested.rmdir()
            child.rmdir()
        else:
            child.unlink()


def _validate_staged_snapshot(output_dir: Path, paths: Sequence[str]) -> None:
    """Require one complete stripped/overview pair for every eligible path."""
    paths_by_stem: dict[str, list[str]] = {}
    for path in paths:
        paths_by_stem.setdefault(_stem_for(path), []).append(path)
    collisions = {stem: collided for stem, collided in paths_by_stem.items() if len(collided) > 1}
    if collisions:
        raise RuntimeError(f"snapshot artifact names collide: {collisions!r}")
    expected = {
        name
        for path in paths
        for name in (f"{_stem_for(path)}.stripped.py", f"{_stem_for(path)}.overview.md")
    }
    actual = {entry.name for entry in output_dir.iterdir()}
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise RuntimeError(
            "snapshot staging produced an incomplete artifact set: "
            f"missing={missing!r}, extra={extra!r}",
        )


def _publish_staged_snapshot(staging_dir: Path, output_dir: Path) -> None:
    """Replace ``output_dir`` with a complete staged snapshot, with rollback."""
    backup_root: Path | None = None
    backup_dir: Path | None = None
    if output_dir.exists() or output_dir.is_symlink():
        backup_root = Path(
            tempfile.mkdtemp(
                prefix=f".{output_dir.name}-backup-",
                dir=output_dir.parent,
            ),
        )
        backup_dir = backup_root / output_dir.name
        output_dir.replace(backup_dir)
    cleanup_backup = False
    try:
        staging_dir.replace(output_dir)
    except BaseException as publish_error:
        if backup_dir is not None:
            try:
                backup_dir.replace(output_dir)
            except BaseException as restore_error:
                raise RuntimeError(
                    "snapshot publication and rollback both failed; "
                    f"the previous snapshot remains at {backup_dir}: {restore_error}",
                ) from publish_error
        cleanup_backup = True
        raise
    else:
        cleanup_backup = True
    finally:
        if backup_root is not None and cleanup_backup:
            shutil.rmtree(backup_root)


def _materialize_and_inspect(commit: str, path: str, out_dir: Path) -> None:
    """Render ``commit:path`` through ``review_inspect`` into ``out_dir``.

    Mirroring the repo-relative path under a temp root lets ``review_inspect``
    derive the same stable ``a__b__c`` stem the file would get from the working
    tree, so output names stay consistent across snapshots and diffs. When the
    file is absent at ``commit`` (an added file, from the diff helper's view) an
    empty ``*.stripped.py`` placeholder is written so a downstream diff renders.

    Shared primitive: both this orchestrator and the diff helper build on it.
    """
    contents = _file_at_commit(commit, path)
    if contents is None:
        (out_dir / f"{_stem_for(path)}.stripped.py").write_text("")
        return
    with tempfile.TemporaryDirectory() as tmp:
        tmp_root = Path(tmp)
        tmp_target = tmp_root / path
        tmp_target.parent.mkdir(parents=True, exist_ok=True)
        tmp_target.write_text(contents)
        _inspect_quiet(tmp_target, out_dir, tmp_root)


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate stripped/overview shadow files for every .py file under "
            "a package directory at the given commit."
        ),
    )
    parser.add_argument("commit_hash", help="Commit hash to snapshot.")
    parser.add_argument(
        "--package-dir",
        default=DEFAULT_PACKAGE_DIR,
        help=(
            f"Repo-relative directory to scan recursively. Defaults to {DEFAULT_PACKAGE_DIR!r}."
        ),
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the orchestrator and return an exit code."""
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    _validate_commit(args.commit_hash)

    repo_root = Path(_run_git(["rev-parse", "--show-toplevel"]).strip()).resolve()
    try:
        package_dir = normalize_package_dir(repo_root, args.package_dir)
    except ValueError as error:
        print(str(error), file=sys.stderr)
        return 2
    out_dir = repo_root / SHADOW_DIR

    paths = _package_python_files_at_commit(args.commit_hash, package_dir)
    out_dir.parent.mkdir(parents=True, exist_ok=True)
    staging_dir = Path(
        tempfile.mkdtemp(
            prefix=f".{out_dir.name}-staging-",
            dir=out_dir.parent,
        ),
    )
    try:
        for path in paths:
            _materialize_and_inspect(args.commit_hash, path, staging_dir)
        _validate_staged_snapshot(staging_dir, paths)
        _publish_staged_snapshot(staging_dir, out_dir)
    finally:
        if staging_dir.exists():
            shutil.rmtree(staging_dir)
    if not paths:
        print(
            f"No snapshot-eligible .py files under {package_dir!r} at {args.commit_hash}; "
            f"published an empty {SHADOW_DIR.as_posix()}/.",
            file=sys.stderr,
        )
        return 0

    print(
        f"Wrote {len(paths)} snapshots from {args.commit_hash} to {SHADOW_DIR.as_posix()}/",
    )
    for entry in sorted(out_dir.iterdir()):
        print(entry.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
