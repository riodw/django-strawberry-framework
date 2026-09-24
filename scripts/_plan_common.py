"""Plan-file plumbing shared by the DRY, REVIEW and bug-hunt plan generators.

``docs/dry/export_dry_review.py``, ``scripts/review_plan.py`` and
``scripts/bug_hunt.py`` each write one release-keyed plan into the tree. The
release rule and the ``__version__`` read are shared by all three; path display,
safe atomic writes and the ``## Cycle baseline`` block by the DRY and REVIEW
planners. Everything is standard library, so a workspace copy that excludes
``docs/`` still imports it.
"""

from __future__ import annotations

import datetime
import os
import re
import subprocess
import tempfile
from pathlib import Path

#: A dotted-digit release such as ``0.0.15``.
RELEASE_PATTERN = re.compile(r"^\d+(?:\.\d+)+$")
#: The package's single ``__version__`` literal, either quote style, optional comment.
VERSION_PATTERN = re.compile(
    r"""(?m)^__version__\s*=\s*(?P<quote>["'])(?P<version>[^"']+)(?P=quote)\s*(?:#.*)?$""",
)


def display_path(path: Path, root: Path) -> Path:
    """Return ``path`` relative to ``root`` when possible, else absolute."""
    resolved = path.resolve()
    try:
        return resolved.relative_to(root.resolve())
    except ValueError:
        return resolved


def resolve_path(path: Path, root: Path) -> Path:
    """Resolve a CLI path relative to the configured root."""
    return path.resolve() if path.is_absolute() else (root / path).resolve()


def validate_date(value: str | None) -> str:
    """Return an ISO date, defaulting to today, or fail with a useful error."""
    if value is None:
        return datetime.date.today().isoformat()
    try:
        return datetime.date.fromisoformat(value).isoformat()
    except ValueError as exc:
        raise ValueError(f"invalid ISO date {value!r}; expected YYYY-MM-DD") from exc


def overwrite_error(path: Path) -> str:
    """Return the standard safe-overwrite diagnostic."""
    return f"output already exists: {path.as_posix()} (pass --force to replace it)"


def atomic_write(path: Path, content: str, *, force: bool) -> None:
    """Atomically write UTF-8 ``content``, refusing an overwrite unless forced."""
    if path.exists() and not force:
        raise FileExistsError(overwrite_error(path))
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
                raise FileExistsError(overwrite_error(path)) from exc
            Path(temp_name).unlink()
        temp_name = None
    finally:
        if temp_name is not None:
            temp_path = Path(temp_name)
            if temp_path.exists():
                temp_path.unlink()


def artifact_name(prefix: str, relative_path: Path) -> str:
    """Return the artifact name for one source file or package folder."""
    slug = relative_path.as_posix().removesuffix(".py").replace("/", "__")
    return f"{prefix}-{slug}.md"


def package_version(package_root: Path) -> str:
    """Read ``__version__`` from the package ``__init__.py``.

    Raises:
        ValueError: the file is unreadable or carries no ``__version__`` literal.
    """
    init_path = package_root / "__init__.py"
    try:
        source = init_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(
            f"cannot read the release from {init_path.as_posix()}; pass --target-release",
        ) from exc
    match = VERSION_PATTERN.search(source)
    if match is None:
        raise ValueError(
            f"no __version__ literal in {init_path.as_posix()}; pass --target-release",
        )
    return match.group("version")


def git_status_short(root: Path) -> str | None:
    """Return ``git status --short`` for ``root``, or ``None`` outside a usable checkout."""
    try:
        result = subprocess.run(
            [
                "git",
                "-C",
                str(root),
                "--no-pager",
                "status",
                "--short",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return result.stdout


def cycle_baseline_block(status_output: str | None) -> list[str]:
    """Render the concurrent-work inventory captured at generation time.

    Every path listed is dirty or untracked before the cycle begins, so no item
    may edit, revert, tidy, or claim it. An empty or unavailable listing is
    stated rather than omitted, so a missing section reads as lost, not clean.
    """
    if status_output is None:
        body = ["`git status --short` unavailable at generation; Worker 0 records it at start."]
    elif status_output.strip():
        body = ["```text", status_output.rstrip("\n"), "```"]
    else:
        body = ["Clean tree at generation."]
    return [
        "## Cycle baseline",
        "",
        "`git status --short` at generation. Every path below is concurrent work: never edited, "
        "reverted,",
        "tidied, or attributed to an item. Worker 0 appends the `CYCLE_BASELINE` stash object "
        "once at",
        "start and nothing afterwards; drift goes on `Drift:` lines under the run heading.",
        "",
        *body,
    ]
