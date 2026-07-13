"""Focused tests for the autonomous bug-hunt progress generator."""

from collections.abc import Sequence
from pathlib import Path

from scripts import bug_hunt


def _write(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def test_generator_writes_autonomous_progress_and_preserves_existing_run(
    tmp_path: Path,
    monkeypatch,
) -> None:
    full_sha = "1234567890abcdef1234567890abcdef12345678"
    short_sha = "1234567"
    package_root = tmp_path / bug_hunt.DEFAULT_PACKAGE_DIR
    _write(package_root / "__init__.py", "")
    _write(package_root / "module.py", "VALUE = None\n")
    _write(package_root / "testing" / "client.py", "class Client:\n    pass\n")
    current_dir = tmp_path / bug_hunt.SHADOW_DIR
    stripped = _write(
        current_dir / "django_strawberry_framework__module.stripped.py",
        "VALUE = None\n",
    )
    _write(
        current_dir / "django_strawberry_framework__module.overview.md",
        "# Overview\n",
    )
    _write(
        tmp_path / bug_hunt.DICTA_PATH,
        "## Package questions\n\n- Could state escape its request?\n",
    )

    def fake_run_git(args: Sequence[str]) -> str:
        responses = {
            ("rev-parse", "--show-toplevel"): f"{tmp_path}\n",
            ("rev-parse", "HEAD"): f"{full_sha}\n",
            ("rev-parse", "--short", full_sha): f"{short_sha}\n",
        }
        return responses[tuple(args)]

    refreshes: list[tuple[str, str, Path]] = []

    def fake_refresh(commit: str, package_dir: str, target_dir: Path) -> None:
        refreshes.append((commit, package_dir, target_dir))

    monkeypatch.setattr(bug_hunt, "_run_git", fake_run_git)
    monkeypatch.setattr(bug_hunt, "_refresh_historical_package_snapshot", fake_refresh)

    assert bug_hunt.main([]) == 0
    output = tmp_path / bug_hunt.BUG_HUNT_DIR / f"bug_hunt.{short_sha}.md"
    report = output.read_text(encoding="utf-8")

    assert f"# Bug hunt: {short_sha}" in report
    assert "Status: in-progress" in report
    assert "Mode: autonomous" in report
    assert f"Baseline commit: `{full_sha}`" in report
    assert "Could state escape its request?" in report
    assert "Break things, break things, break things" in report
    assert "every extreme, test the opposite extreme" in report
    assert "Do not clean up scratch probes" in report
    assert "Clean layers often fail only when several reasonable assumptions stack" in report
    assert "- [ ] django_strawberry_framework/module.py" in report
    assert "Use django_strawberry_framework/module.py as the entry point" in report
    assert "- [ ] django_strawberry_framework/testing/client.py" in report
    assert "Baseline shadow: none (live file added or absent at hunt baseline)" in report
    assert "- [ ] django_strawberry_framework/__init__.py" not in report
    assert "- [ ] Package integration" in report
    assert "including public exports and `__init__.py` files" in report
    assert "- [ ] Final test gate" in report
    assert report.index(stripped.name) < report.index("Package integration")
    assert report.index("Package integration") < report.index("Final test gate")
    assert refreshes == [(full_sha, bug_hunt.DEFAULT_PACKAGE_DIR, current_dir.resolve())]

    assert bug_hunt.main([]) == 3
    assert len(refreshes) == 1

    output.write_text("stale progress\n", encoding="utf-8")
    assert bug_hunt.main(["--force"]) == 0
    assert "stale progress" not in output.read_text(encoding="utf-8")
    assert len(refreshes) == 2
