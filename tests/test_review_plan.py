"""Repo-tooling tests for the REVIEW plan generator, scope lister and reconciler.

Keeps the plan-shape, scope-grouping and reconcile contracts for
``scripts/review_plan.py`` against throwaway git repositories under ``tmp_path``,
never against this checkout's state. A live ``/graphql/`` request has no wire
shape for generated plans or git listings, so none of these rows can move.
There is no live sibling in ``examples/fakeshop/test_query/``.
"""

import json
import subprocess
from pathlib import Path

import pytest

from scripts import review_plan

PACKAGE = review_plan.PACKAGE_DIR


def _write(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.com",
            "-c",
            "commit.gpgsign=false",
            "-c",
            "core.hooksPath=/dev/null",
            *args,
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def _commit_all(root: Path, message: str) -> None:
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", message)


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    package = root / PACKAGE
    _write(
        package / "__init__.py",
        '__version__ = "0.1.2"\n\n\ndef __getattr__(name):\n    raise AttributeError(name)\n',
    )
    _write(package / "alpha.py", "ALPHA = 1\n")
    _write(package / "sub" / "__init__.py", "")
    _write(package / "sub" / "beta.py", "".join(f"BETA_{n} = {n}\n" for n in range(20)))
    _write(package / "sub" / "deep" / "gamma.py", "GAMMA = 3\n")
    _write(root / "README.md", "readme\n")
    _git(root, "init", "-q")
    _commit_all(root, "initial")
    return root


def _plan(root: Path, output: Path, *extra: str) -> int:
    return review_plan.main(
        [
            "--root",
            str(root),
            "plan",
            "--output",
            str(output),
            "--generated-date",
            "2026-01-02",
            *extra,
        ],
    )


def _headings(text: str) -> list[str]:
    return [line for line in text.splitlines() if line.startswith("## ")]


def test_plan_renders_review_shape_in_order(repo: Path, tmp_path: Path) -> None:
    output = tmp_path / "out" / "review-0_1_2.md"

    assert _plan(repo, output) == 0
    text = output.read_text(encoding="utf-8")

    header = text.split("\n\n## Cycle baseline", 1)[0]
    assert header.splitlines()[:6] == [
        "# REVIEW plan: 0.1.2",
        "",
        "Status: planned",
        "Mode: autonomous",
        "Run: 0.1.2 2026-01-02-1",
        "Scope: package",
    ]
    assert _headings(text) == [
        "## Cycle baseline",
        "## Bench baseline",
        "## How to work one item",
        "## Package root",
        "## sub/",
        "## sub/deep/",
        "## sub/deep/ integration",
        "## sub/ integration",
        "## Project",
        "## Decisions",
        "## Owned changes",
        "## Outcomes",
    ]
    assert "Clean tree at generation." in text
    assert "CYCLE_BASELINE=<Worker 0 fills" in text
    assert text.count('| `uv run --directory "$WS" ') == 3
    assert "| Path | Item | Axis | Symbols changed |" in text

    checkboxes = [line for line in text.splitlines() if line.startswith("- [ ] ")]
    assert checkboxes == [
        "- [ ] alpha.py",
        "- [ ] sub/beta.py",
        "- [ ] sub/deep/gamma.py",
        "- [ ] sub/deep/ integration",
        "- [ ] sub/ integration",
        "- [ ] Project integration",
        "- [ ] Final gate",
    ]
    gamma_item = (
        "- [ ] sub/deep/gamma.py\n"
        "    - Status: pending\n"
        "    - Path class:\n"
        "    - Artifacts: rev-sub__deep__gamma.md, rev-sub__deep__gamma.performance.md, "
        "rev-sub__deep__gamma.mechanics.md, rev-sub__deep__gamma.comments.md\n"
    )
    assert gamma_item in text
    assert "Artifacts: rev-sub.md, rev-sub.performance.md" in text
    assert "Artifacts: rev-project.md, rev-project.performance.md" in text
    assert "`__init__.py` (defines `__getattr__`), `sub/__init__.py`" in text
    assert "## Out of scope this run" not in text

    parsed = {item.label: item for item in review_plan.parse_plan(text)}
    assert len(parsed) == 7
    assert parsed["Project integration"].artifacts == (
        "rev-project.md",
        "rev-project.performance.md",
        "rev-project.mechanics.md",
        "rev-project.comments.md",
    )
    assert parsed["Final gate"].artifacts == ()


def test_plan_scope_lists_the_rest_as_out_of_scope(repo: Path, tmp_path: Path) -> None:
    output = tmp_path / "review.md"

    assert _plan(repo, output, "--scope", f"{PACKAGE}/sub/deep", "--scope", "alpha.py") == 0
    text = output.read_text(encoding="utf-8")

    assert "Scope: sub/deep/, alpha.py" in text
    in_run, out_of_run = text.split("## Out of scope this run", 1)
    assert "- [ ] alpha.py\n    - Status: pending" in in_run
    assert "- [ ] sub/deep/gamma.py\n    - Status: pending" in in_run
    assert "## sub/deep/ integration" in in_run
    assert "## Final gate" in in_run
    assert "## Project\n" not in in_run
    assert "- [ ] sub/beta.py\n    - Status: out-of-scope" in out_of_run
    assert "- [ ] sub/ integration\n    - Status: out-of-scope" in out_of_run
    assert "- [ ] Project integration\n    - Status: out-of-scope" in out_of_run
    assert _headings(out_of_run)[-3:] == ["## Decisions", "## Owned changes", "## Outcomes"]


@pytest.mark.parametrize(
    "scope",
    [
        f"{PACKAGE}/missing",
        "sub/__init__.py",
        "alph",
        "README.md",
    ],
)
def test_plan_scope_fails_closed_on_unmatched_path(
    repo: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    scope: str,
) -> None:
    output = tmp_path / "review.md"

    assert _plan(repo, output, "--scope", scope) == 2
    assert not output.exists()
    assert "matches no inventory file" in capsys.readouterr().err


def test_plan_ignores_untracked_sources(repo: Path, tmp_path: Path) -> None:
    _write(repo / PACKAGE / "scratch.py", "SCRATCH = 1\n")
    output = tmp_path / "review.md"

    assert _plan(repo, output) == 0
    text = output.read_text(encoding="utf-8")

    assert "- [ ] scratch.py" not in text
    assert f"?? {PACKAGE}/scratch.py" in text


def test_plan_refuses_overwrite_and_force_continues_run_numbering(
    repo: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    output = tmp_path / "review.md"
    assert _plan(repo, output) == 0
    first = output.read_text(encoding="utf-8")

    assert _plan(repo, output) == 2
    assert "pass --force to replace it" in capsys.readouterr().err
    assert output.read_text(encoding="utf-8") == first

    assert _plan(repo, output, "--force") == 0
    assert "Run: 0.1.2 2026-01-02-2" in output.read_text(encoding="utf-8")


def test_plan_defaults_output_to_the_release_path(repo: Path) -> None:
    assert (
        review_plan.main(
            [
                "--root",
                str(repo),
                "plan",
                "--generated-date",
                "2026-01-02",
            ],
        )
        == 0
    )
    assert (repo / "docs" / "review" / "review-0_1_2.md").is_file()

    target = [
        "--root",
        str(repo),
        "plan",
        "--target-release",
        "0.2.0",
    ]
    assert review_plan.main(target) == 0
    assert (repo / "docs" / "review" / "review-0_2_0.md").is_file()


def test_plan_refuses_colliding_artifact_names(repo: Path, tmp_path: Path) -> None:
    _write(repo / PACKAGE / "project.py", "PROJECT = 1\n")
    _commit_all(repo, "collide")

    assert _plan(repo, tmp_path / "review.md") == 2
    assert not (tmp_path / "review.md").exists()


def test_scope_groups_committed_dirty_and_renamed(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _git(repo, "tag", "0.1.1")
    package = repo / PACKAGE
    _write(package / "alpha.py", "ALPHA = 2\n")
    _write(package / "__init__.py", '__version__ = "0.1.2"\n')
    _write(package / "sub" / "fresh.py", "FRESH = 1\n")
    _git(repo, "mv", f"{PACKAGE}/sub/beta.py", f"{PACKAGE}/sub/beta_renamed.py")
    _commit_all(repo, "change")
    _write(package / "sub" / "deep" / "gamma.py", "GAMMA = 4\n")
    _write(package / "sub" / "untracked.py", "UNTRACKED = 1\n")
    _write(repo / "README.md", "changed\n")

    report = review_plan.build_scope(repo, None)

    assert report.since == "0.1.1"
    committed = {entry["path"]: entry for entry in report.committed}
    assert {path: entry["status"] for path, entry in committed.items()} == {
        f"{PACKAGE}/__init__.py": "M",
        f"{PACKAGE}/alpha.py": "M",
        f"{PACKAGE}/sub/fresh.py": "A",
    }
    alpha = f"{PACKAGE}/alpha.py"
    assert committed[alpha]["blob"] == _git(repo, "rev-parse", f"HEAD:{alpha}").strip()
    assert committed[f"{PACKAGE}/__init__.py"]["init"] is True
    assert [(entry["old"], entry["new"], entry["where"]) for entry in report.renames] == [
        (f"{PACKAGE}/sub/beta.py", f"{PACKAGE}/sub/beta_renamed.py", "committed"),
    ]
    dirty = {entry["path"]: entry for entry in report.dirty}
    gamma = f"{PACKAGE}/sub/deep/gamma.py"
    assert {path: entry["status"] for path, entry in dirty.items()} == {
        gamma: " M",
        f"{PACKAGE}/sub/untracked.py": "??",
    }
    assert dirty[gamma]["worktree_blob"] == _git(repo, "hash-object", gamma).strip()

    assert (
        review_plan.main(
            [
                "--root",
                str(repo),
                "scope",
                "--json",
            ],
        )
        == 0
    )
    data = json.loads(capsys.readouterr().out)
    assert (len(data["committed"]), len(data["dirty"]), len(data["renames"])) == (3, 2, 1)
    assert data["folders"] == ["(package root)", "sub/", "sub/deep/"]

    assert (
        review_plan.main(
            [
                "--root",
                str(repo),
                "scope",
                "--since",
                "HEAD",
            ],
        )
        == 0
    )
    text = capsys.readouterr().out
    assert "Committed (HEAD..HEAD): 0" in text
    assert "Dirty or untracked (concurrent work, not committed): 2" in text


def test_scope_without_a_reachable_tag_fails(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert review_plan.main(["--root", str(repo), "scope"]) == 2
    assert "pass --since" in capsys.readouterr().err


def test_reconcile_is_clean_on_a_fresh_plan(
    repo: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    plan = tmp_path / "review.md"
    assert _plan(repo, plan, "--scope", "sub") == 0
    before = plan.read_text(encoding="utf-8")

    assert (
        review_plan.main(
            [
                "--root",
                str(repo),
                "reconcile",
                "--plan",
                str(plan),
            ],
        )
        == 0
    )
    assert "plan matches the inventory" in capsys.readouterr().out
    assert plan.read_text(encoding="utf-8") == before


def test_reconcile_reports_added_gone_renamed_and_missing_artifacts(
    repo: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    plan = tmp_path / "review.md"
    assert _plan(repo, plan) == 0
    text = plan.read_text(encoding="utf-8")
    text = text.replace(
        "- [ ] alpha.py\n    - Status: pending",
        "- [ ] alpha.py\n    - Status: reviewing",
    )
    text = text.replace("- [ ] sub/ integration\n", "- [x] sub/ integration\n")
    text = text.replace(
        "- [ ] Project integration\n    - Status: pending",
        "- [ ] Project integration\n    - Status: reviewing",
    )
    plan.write_text(text, encoding="utf-8")
    _write(tmp_path / "rev-sub.md", "main\n")

    package = repo / PACKAGE
    _git(repo, "mv", f"{PACKAGE}/sub/beta.py", f"{PACKAGE}/sub/beta_moved.py")
    _git(repo, "rm", "-q", f"{PACKAGE}/sub/deep/gamma.py")
    _write(package / "added.py", "ADDED = 1\n")
    _write(package / "extra" / "loose.py", "LOOSE = 1\n")
    _commit_all(repo, "drift")
    _write(package / "sub" / "untracked.py", "UNTRACKED = 1\n")

    report = review_plan.build_reconcile(repo, plan)

    assert report.added == [
        "added.py (tracked)",
        "extra/loose.py (tracked)",
        "sub/untracked.py (untracked)",
    ]
    assert report.gone == ["sub/deep/gamma.py"]
    assert [(old, new) for old, new, _ in report.renamed] == [
        ("sub/beta.py", "sub/beta_moved.py"),
    ]
    assert report.folders_added == ["extra"]
    assert report.folders_gone == ["sub/deep"]
    assert report.missing_artifacts == [
        ("alpha.py", "rev-alpha.md"),
        ("sub/ integration", "rev-sub.performance.md"),
        ("sub/ integration", "rev-sub.mechanics.md"),
        ("sub/ integration", "rev-sub.comments.md"),
        ("Project integration", "rev-project.md"),
    ]

    assert (
        review_plan.main(
            [
                "--root",
                str(repo),
                "reconcile",
                "--plan",
                str(plan),
            ],
        )
        == 1
    )
    out = capsys.readouterr().out
    assert "Items whose file was renamed: 1" in out
    assert "sub/beta.py -> sub/beta_moved.py" in out


def test_reconcile_skips_closed_items(repo: Path, tmp_path: Path) -> None:
    plan = tmp_path / "review.md"
    assert _plan(repo, plan) == 0
    _git(repo, "rm", "-q", f"{PACKAGE}/alpha.py")
    _commit_all(repo, "remove")
    text = plan.read_text(encoding="utf-8").replace(
        "- [ ] alpha.py\n    - Status: pending",
        "- [ ] alpha.py\n    - Status: closed (removed from the package)",
    )
    plan.write_text(text, encoding="utf-8")

    assert review_plan.build_reconcile(repo, plan).clean
