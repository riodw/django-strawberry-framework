"""Report the import-time cost of ``django_strawberry_framework`` per module.

Runs ``python -X importtime -c "import django_strawberry_framework"`` in a
fresh child process of the same interpreter, so nothing the report itself
imported is already cached, parses the child's stderr and prints the top
``--top`` package modules by cumulative and by self time, then the top
top-level import names by summed self time (third-party and stdlib, e.g.
``django``, ``strawberry``, ``psycopg`` - an optional dependency shows up
there like any other row when it is installed and imported).

Every figure is the minimum across ``--rounds`` measured children, taken per
module: import time is noisy upward (page cache, scheduler), never downward.
``--warmup`` discarded children run first so the measured rounds read
compiled ``.pyc`` files instead of timing the bytecode compiler.

The child prints the package ``__file__`` it imported; the report refuses a
package outside the tree holding this script, the same rule
``_bench_common.bootstrap_fakeshop_django`` enforces for the benches. Django
is never configured, so the figure is the package import alone.

Usage::

    uv run python scripts/importtime_report.py
    uv run python scripts/importtime_report.py --top 15 --rounds 7 --json importtime.json
"""

from __future__ import annotations

import argparse
import platform
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from _bench_common import REPO_ROOT, assert_package_in_tree, build_report, git_head, write_report

PACKAGE = "django_strawberry_framework"
_CHILD_CODE = f"import {PACKAGE} as package; print(package.__file__)"
_LINE_PREFIX = "import time:"


@dataclass(frozen=True)
class ImportRow:
    """One ``-X importtime`` line: a module and its self / cumulative microseconds."""

    name: str
    self_us: int
    cumulative_us: int
    depth: int


def parse_importtime(stderr: str) -> list[ImportRow]:
    """Parse ``-X importtime`` stderr into rows, skipping the header and other output.

    Each line reads ``import time: <self> | <cumulative> | <indent><module>``;
    the indent (two spaces per level) is the nesting depth under the
    importing module.
    """
    rows: list[ImportRow] = []
    for line in stderr.splitlines():
        if not line.startswith(_LINE_PREFIX):
            continue
        fields = line[len(_LINE_PREFIX) :].split("|", 2)
        if len(fields) != 3:
            continue
        self_text, cumulative_text, raw_name = fields
        try:
            self_us = int(self_text.strip())
            cumulative_us = int(cumulative_text.strip())
        except ValueError:
            continue
        name = raw_name.lstrip(" ")
        indent = len(raw_name) - len(name) - 1
        rows.append(
            ImportRow(
                name=name.strip(),
                self_us=self_us,
                cumulative_us=cumulative_us,
                depth=max(indent, 0) // 2,
            ),
        )
    return rows


def is_package_module(name: str) -> bool:
    """Report whether ``name`` is the package or one of its submodules."""
    return name == PACKAGE or name.startswith(f"{PACKAGE}.")


def min_across_rounds(rounds: list[list[ImportRow]]) -> dict[str, dict[str, int]]:
    """Take each module's minimum self and cumulative time across rounds.

    A module missing from some round keeps the minimum of the rounds that saw it.
    """
    merged: dict[str, dict[str, int]] = {}
    for rows in rounds:
        for row in rows:
            entry = merged.setdefault(
                row.name,
                {"cumulative_us": row.cumulative_us, "self_us": row.self_us},
            )
            entry["cumulative_us"] = min(entry["cumulative_us"], row.cumulative_us)
            entry["self_us"] = min(entry["self_us"], row.self_us)
    return merged


def summarize(merged: dict[str, dict[str, int]], top: int) -> dict[str, Any]:
    """Build the report body: package totals, top package modules, top-level groups."""
    package_rows = {name: times for name, times in merged.items() if is_package_module(name)}
    groups: dict[str, int] = {}
    for name, times in merged.items():
        if is_package_module(name):
            continue
        top_level = name.split(".", 1)[0]
        groups[top_level] = groups.get(top_level, 0) + times["self_us"]

    def _rows(items: dict[str, dict[str, int]], key: str) -> list[dict[str, Any]]:
        ordered = sorted(items.items(), key=lambda item: (-item[1][key], item[0]))
        return [{"module": name, **times} for name, times in ordered[:top]]

    return {
        "package_cumulative_us": package_rows.get(PACKAGE, {}).get("cumulative_us"),
        "package_modules": len(package_rows),
        "package_self_us": sum(times["self_us"] for times in package_rows.values()),
        "top_by_cumulative": _rows(package_rows, "cumulative_us"),
        "top_by_self": _rows(package_rows, "self_us"),
        "top_level_self": [
            {"name": name, "self_us": self_us}
            for name, self_us in sorted(groups.items(), key=lambda item: (-item[1], item[0]))[:top]
        ],
    }


def _run_child() -> tuple[str, str]:
    """Run one fresh interpreter under ``-X importtime``; return (package file, stderr).

    Raises:
        RuntimeError: the child failed to import the package.
    """
    completed = subprocess.run(
        [
            sys.executable,
            "-X",
            "importtime",
            "-c",
            _CHILD_CODE,
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        msg = f"child import failed ({completed.returncode}): {completed.stderr[-2000:]}"
        raise RuntimeError(msg)
    return completed.stdout.strip(), completed.stderr


def _ms(us: int | None) -> str:
    return "?" if us is None else f"{us / 1000:.1f}"


def main() -> int:
    """Parse args, run the children, and print the import-time report."""
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--top", type=int, default=20, help="rows per table (default 20)")
    parser.add_argument("--rounds", type=int, default=5, help="measured children (default 5)")
    parser.add_argument("--warmup", type=int, default=1, help="discarded children (default 1)")
    parser.add_argument("--json", dest="json_path", help="also write the report as JSON here")
    args = parser.parse_args()
    if args.rounds < 1 or args.top < 1 or args.warmup < 0:
        parser.error("--rounds and --top must be at least 1, --warmup at least 0")

    for _ in range(args.warmup):
        _run_child()
    package_files: set[str] = set()
    rounds: list[list[ImportRow]] = []
    for _ in range(args.rounds):
        package_file, stderr = _run_child()
        package_files.add(package_file)
        rounds.append(parse_importtime(stderr))
    if len(package_files) != 1:
        msg = f"children imported different package files: {sorted(package_files)}"
        raise RuntimeError(msg)
    package_file = package_files.pop()
    repo_root = REPO_ROOT
    provenance = {
        "git_head": git_head(repo_root),
        "interpreter": sys.executable,
        "package_file": str(Path(package_file).resolve()),
        "platform": platform.platform(),
        "python": platform.python_version(),
        "repo_root": str(repo_root),
    }
    print("provenance")
    print(f"  package      {provenance['package_file']}")
    print(f"  tree         {repo_root} (git HEAD {provenance['git_head']})")
    print(f"  interpreter  {sys.executable} (python {provenance['python']})")
    print(f"  platform     {provenance['platform']}")
    assert_package_in_tree(package_file, repo_root)

    body = summarize(min_across_rounds(rounds), args.top)
    print(
        f"\nimport {PACKAGE}: min of {args.rounds} rounds ({args.warmup} warmup), times in ms",
    )
    print(
        f"package cumulative {_ms(body['package_cumulative_us'])} | package self "
        f"{_ms(body['package_self_us'])} over {body['package_modules']} modules",
    )
    for title, rows in (
        ("top package modules by cumulative", body["top_by_cumulative"]),
        ("top package modules by self", body["top_by_self"]),
    ):
        print(f"\n{title}")
        print(f"  {'cumulative':>10} {'self':>8}  module")
        for row in rows:
            print(f"  {_ms(row['cumulative_us']):>10} {_ms(row['self_us']):>8}  {row['module']}")
    print("\ntop-level import names outside the package by summed self time")
    for row in body["top_level_self"]:
        print(f"  {_ms(row['self_us']):>10}  {row['name']}")

    if args.json_path:
        write_report(
            args.json_path,
            build_report(
                tool="importtime_report",
                provenance=provenance,
                params={"rounds": args.rounds, "top": args.top, "warmup": args.warmup},
                rows=body["top_by_cumulative"],
                failures=[],
            )
            | {"summary": body},
        )
        print(f"wrote {args.json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
