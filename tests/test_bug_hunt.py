"""Focused tests for the autonomous bug-hunt progress generator."""

from collections.abc import Sequence
from pathlib import Path

from scripts import bug_hunt
from scripts import review_historical_package_snapshot_at_commit as snapshot


def _write(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def test_generator_writes_autonomous_progress_and_preserves_existing_run(
    tmp_path: Path,
    monkeypatch,
) -> None:
    full_sha = "1234567890abcdef1234567890abcdef12345678"
    release = "0.0.13"
    package_root = tmp_path / bug_hunt.DEFAULT_PACKAGE_DIR
    _write(package_root / "__init__.py", f'__version__ = "{release}"\n')
    _write(tmp_path / "pyproject.toml", f'[project]\nversion = "{release}"\n')
    _write(package_root / "module.py", "VALUE = None\n")
    _write(package_root / "testing" / "client.py", "class Client:\n    pass\n")
    _write(package_root / "testing" / "fresh.py", "FRESH = None\n")
    _write(package_root / "added.py", "NEW = None\n")
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

    pkg = bug_hunt.DEFAULT_PACKAGE_DIR
    # The baseline holds ``module.py`` and ``testing/client.py`` but neither
    # ``added.py`` nor ``testing/fresh.py``, so file age is established by the listing
    # rather than assumed from the path.
    baseline_listing = f"{pkg}/__init__.py\n{pkg}/module.py\n{pkg}/testing/client.py\n"

    def fake_run_git(args: Sequence[str]) -> str:
        responses = {
            ("rev-parse", "--show-toplevel"): f"{tmp_path}\n",
            ("rev-parse", "HEAD"): f"{full_sha}\n",
            (
                "ls-tree",
                "-r",
                "--name-only",
                full_sha,
                "--",
                pkg,
            ): baseline_listing,
        }
        return responses[tuple(args)]

    refreshes: list[tuple[str, str, Path]] = []

    def fake_refresh(commit: str, package_dir: str, target_dir: Path) -> None:
        refreshes.append((commit, package_dir, target_dir))

    monkeypatch.setattr(bug_hunt, "_run_git", fake_run_git)
    monkeypatch.setattr(bug_hunt, "_refresh_historical_package_snapshot", fake_refresh)

    assert bug_hunt.main([]) == 0
    output = tmp_path / bug_hunt.BUG_HUNT_DIR / "bug_hunt-0_0_13.md"
    report = output.read_text(encoding="utf-8")

    assert f"# Bug hunt: {release}" in report
    assert "Status: in-progress" in report
    assert "Mode: autonomous" in report
    assert f"Baseline commit: `{full_sha}`" in report
    assert "Could state escape its request?" in report
    assert "Break things, break things, break things" in report
    assert "every extreme, test the opposite extreme" in report
    assert "Do not clean up scratch probes" in report
    assert "leave it intact so Worker 0 can independently verify it" in report
    assert "Report evidence, changed files, tests, and validation to Worker 0" in report
    assert "layers often fail only when several reasonable assumptions stack together" in report
    assert "- [ ] django_strawberry_framework/module.py" in report
    assert "Use django_strawberry_framework/module.py as the entry point" in report
    assert "- [ ] django_strawberry_framework/testing/client.py" in report
    # Exclusion and age are independent facts, so all three reachable combinations
    # must stay distinguishable in one report.
    assert (
        "Baseline shadow: none (path excluded from the snapshot by its 'test' path filter, not new)"
        in report
    )
    assert "Baseline shadow: none (live file added since the hunt baseline)" in report
    assert (
        "Baseline shadow: none (live file added since the hunt baseline; its path is also "
        "excluded by the snapshot's 'test' filter)" in report
    )
    assert "- [ ] django_strawberry_framework/__init__.py" not in report
    assert "- [ ] Package integration" in report
    assert "including public exports and `__init__.py` files" in report
    assert "- [ ] Final test gate" in report
    assert "    - Owner: Worker 0" in report
    assert report.index(stripped.name) < report.index("Package integration")
    assert report.index("Package integration") < report.index("Final test gate")
    assert refreshes == [(full_sha, bug_hunt.DEFAULT_PACKAGE_DIR, current_dir.resolve())]

    assert bug_hunt.main([]) == 3
    assert len(refreshes) == 1

    output.write_text("stale progress\n", encoding="utf-8")
    assert bug_hunt.main(["--force"]) == 0
    assert "stale progress" not in output.read_text(encoding="utf-8")
    assert len(refreshes) == 2


def test_empty_dicta_still_renders_the_package_questions_section(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """An empty maintainer dicta means "no questions", never a missing section.

    ``dicta.md`` is maintainer-owned and stays in the tree between hunts, so the
    empty file is the resting state; substituting the fallback only for a missing
    path dropped the heading entirely from the generated progress file.
    """
    package_root = tmp_path / bug_hunt.DEFAULT_PACKAGE_DIR
    _write(package_root / "__init__.py", '__version__ = "0.0.13"\n')
    _write(tmp_path / "pyproject.toml", '[project]\nversion = "0.0.13"\n')
    _write(package_root / "module.py", "VALUE = None\n")
    _write(tmp_path / bug_hunt.DICTA_PATH, "\n   \n")

    def fake_run_git(args: Sequence[str]) -> str:
        if args[0] == "ls-tree":
            return f"{bug_hunt.DEFAULT_PACKAGE_DIR}/module.py\n"
        responses = {
            ("rev-parse", "--show-toplevel"): f"{tmp_path}\n",
            ("rev-parse", "HEAD"): "1234567890abcdef1234567890abcdef12345678\n",
        }
        return responses[tuple(args)]

    monkeypatch.setattr(bug_hunt, "_run_git", fake_run_git)
    monkeypatch.setattr(bug_hunt, "_refresh_historical_package_snapshot", lambda *args: None)

    assert bug_hunt.main([]) == 0
    report = (tmp_path / bug_hunt.BUG_HUNT_DIR / "bug_hunt-0_0_13.md").read_text(encoding="utf-8")

    assert "## Package questions" in report
    assert "No maintainer-authored probing questions were supplied" in report


def test_snapshot_exclusion_rule_is_shared_with_the_snapshot_helper() -> None:
    """The generator explains a missing stem with the rule that produced it."""
    assert snapshot.snapshot_excludes("django_strawberry_framework/testing/client.py")
    assert snapshot.snapshot_excludes("django_strawberry_framework/__init__.py")
    assert snapshot.snapshot_excludes("django_strawberry_framework/README.md")
    assert not snapshot.snapshot_excludes("django_strawberry_framework/views.py")


def test_no_shadow_reason_reads_exclusion_and_age_independently() -> None:
    """Neither fact may be inferred from the other, so all four cases are named.

    A path-only classifier calls every ``testing/`` file old and a baseline-only
    classifier calls every excluded file new; both produce a confidently wrong
    orientation line for the file a hunter is about to read.
    """
    baseline = frozenset(
        {"django_strawberry_framework/testing/relay.py", "django_strawberry_framework/views.py"},
    )

    assert (
        bug_hunt._no_shadow_reason("django_strawberry_framework/testing/relay.py", baseline)
        == "path excluded from the snapshot by its 'test' path filter, not new"
    )
    assert bug_hunt._no_shadow_reason(
        "django_strawberry_framework/testing/new_after_baseline.py",
        baseline,
    ) == (
        "live file added since the hunt baseline; its path is also excluded by the "
        "snapshot's 'test' filter"
    )
    assert (
        bug_hunt._no_shadow_reason("django_strawberry_framework/brand_new.py", baseline)
        == "live file added since the hunt baseline"
    )
    # Eligible and present at the baseline should have produced a shadow; say so
    # rather than inventing a cause for it.
    assert bug_hunt._no_shadow_reason("django_strawberry_framework/views.py", baseline) == (
        "file existed at the hunt baseline and is snapshot-eligible, so this shadow is "
        "missing unexpectedly -- treat the snapshot as incomplete"
    )


def test_baseline_python_paths_reads_the_commit_unfiltered(monkeypatch) -> None:
    """Age comes from the commit's full listing, not the snapshot's eligible set."""
    calls: list[tuple[str, ...]] = []

    def fake_run_git(args: Sequence[str]) -> str:
        calls.append(tuple(args))
        return (
            "django_strawberry_framework/__init__.py\n"
            "django_strawberry_framework/testing/client.py\n"
            "django_strawberry_framework/views.py\n"
            "django_strawberry_framework/py.typed\n"
        )

    monkeypatch.setattr(bug_hunt, "_run_git", fake_run_git)
    paths = bug_hunt._baseline_python_paths("abc123", "django_strawberry_framework")

    # Excluded-from-snapshot paths must still register as existing, or the classifier
    # cannot tell an old ``testing/`` file from a new one.
    assert "django_strawberry_framework/testing/client.py" in paths
    assert "django_strawberry_framework/__init__.py" in paths
    assert "django_strawberry_framework/py.typed" not in paths
    assert calls == [
        (
            "ls-tree",
            "-r",
            "--name-only",
            "abc123",
            "--",
            "django_strawberry_framework",
        ),
    ]


def test_target_release_overrides_mismatched_package_versions(tmp_path: Path, monkeypatch) -> None:
    package_root = tmp_path / bug_hunt.DEFAULT_PACKAGE_DIR
    _write(package_root / "__init__.py", '__version__ = "0.0.12"\n')
    _write(package_root / "module.py", "VALUE = None\n")
    _write(tmp_path / "pyproject.toml", '[project]\nversion = "0.0.13"\n')

    def fake_run_git(args: Sequence[str]) -> str:
        if args[0] == "ls-tree":
            return f"{bug_hunt.DEFAULT_PACKAGE_DIR}/module.py\n"
        responses = {
            ("rev-parse", "--show-toplevel"): f"{tmp_path}\n",
            ("rev-parse", "HEAD"): "1234567890abcdef1234567890abcdef12345678\n",
        }
        return responses[tuple(args)]

    monkeypatch.setattr(bug_hunt, "_run_git", fake_run_git)
    monkeypatch.setattr(
        bug_hunt,
        "_refresh_historical_package_snapshot",
        lambda *args: None,
    )

    assert bug_hunt.main(["--target-release", "0.0.14"]) == 0
    output = tmp_path / bug_hunt.BUG_HUNT_DIR / "bug_hunt-0_0_14.md"
    assert "# Bug hunt: 0.0.14" in output.read_text(encoding="utf-8")


def test_generator_rejects_mismatched_package_versions(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    package_root = tmp_path / bug_hunt.DEFAULT_PACKAGE_DIR
    _write(package_root / "__init__.py", '__version__ = "0.0.12"\n')
    _write(tmp_path / "pyproject.toml", '[project]\nversion = "0.0.13"\n')

    def fake_run_git(args: Sequence[str]) -> str:
        responses = {
            ("rev-parse", "--show-toplevel"): f"{tmp_path}\n",
            ("rev-parse", "HEAD"): "1234567890abcdef1234567890abcdef12345678\n",
        }
        return responses[tuple(args)]

    monkeypatch.setattr(bug_hunt, "_run_git", fake_run_git)

    assert bug_hunt.main([]) == 1
    assert "version mismatch" in capsys.readouterr().err


def test_generator_rejects_invalid_target_release(tmp_path: Path, monkeypatch, capsys) -> None:
    def fake_run_git(args: Sequence[str]) -> str:
        responses = {
            ("rev-parse", "--show-toplevel"): f"{tmp_path}\n",
            ("rev-parse", "HEAD"): "1234567890abcdef1234567890abcdef12345678\n",
        }
        return responses[tuple(args)]

    monkeypatch.setattr(bug_hunt, "_run_git", fake_run_git)

    assert bug_hunt.main(["--target-release", "0_0_14"]) == 1
    assert "invalid release '0_0_14'" in capsys.readouterr().err
    assert bug_hunt.main(["--target-release", ""]) == 1
    assert "invalid release ''" in capsys.readouterr().err


def test_python_310_fallback_reads_only_the_project_table(tmp_path: Path, monkeypatch) -> None:
    _write(
        tmp_path / "pyproject.toml",
        "version = \"9.9.9\"\n\n[project]\nversion = '0.0.13'\n\n[tool.example]\n",
    )
    monkeypatch.setattr(bug_hunt, "tomllib", None)

    assert bug_hunt._pyproject_version(tmp_path) == "0.0.13"
