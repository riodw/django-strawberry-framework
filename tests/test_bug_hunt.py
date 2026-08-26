"""Focused tests for the autonomous bug-hunt progress generator."""

import subprocess
from collections.abc import Sequence
from pathlib import Path

import pytest

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
    _write(package_root / "module.py", "VALUE = None\n")
    _write(package_root / "testing" / "client.py", "class Client:\n    pass\n")
    _write(package_root / "testing" / "fresh.py", "FRESH = None\n")
    _write(package_root / "added.py", "NEW = None\n")
    _write(package_root / "orphaned.py", "ORPHANED = None\n")
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
    # The baseline holds ``module.py``, ``orphaned.py``, and
    # ``testing/client.py`` but neither ``added.py`` nor ``testing/fresh.py``, so
    # file age is established by the listing rather than assumed from the path.
    baseline_listing = (
        f"{pkg}/__init__.py\0{pkg}/module.py\0{pkg}/orphaned.py\0{pkg}/testing/client.py\0"
    )

    def fake_run_git(args: Sequence[str]) -> str:
        responses = {
            ("rev-parse", "--show-toplevel"): f"{tmp_path}\n",
            ("rev-parse", "HEAD"): f"{full_sha}\n",
        }
        return responses[tuple(args)]

    refreshes: list[tuple[str, str, Path]] = []

    def fake_refresh(commit: str, package_dir: str, target_dir: Path) -> None:
        refreshes.append((commit, package_dir, target_dir))

    monkeypatch.setattr(bug_hunt, "_run_git", fake_run_git)
    monkeypatch.setattr(snapshot, "_run_git", lambda args: baseline_listing)
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
    assert (
        "Baseline shadow: none (file existed at the hunt baseline and is snapshot-eligible, "
        "so this shadow is missing unexpectedly -- treat the snapshot as incomplete)" in report
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

    outside_output = tmp_path.parent / f"{tmp_path.name}-outside.md"
    assert bug_hunt.main(["--output", str(outside_output)]) == 0
    assert outside_output.is_file()


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
    _write(package_root / "module.py", "VALUE = None\n")
    _write(tmp_path / bug_hunt.DICTA_PATH, "\n   \n")

    def fake_run_git(args: Sequence[str]) -> str:
        responses = {
            ("rev-parse", "--show-toplevel"): f"{tmp_path}\n",
            ("rev-parse", "HEAD"): "1234567890abcdef1234567890abcdef12345678\n",
        }
        return responses[tuple(args)]

    monkeypatch.setattr(bug_hunt, "_run_git", fake_run_git)
    monkeypatch.setattr(
        snapshot,
        "_run_git",
        lambda args: f"{bug_hunt.DEFAULT_PACKAGE_DIR}/module.py\0",
    )
    monkeypatch.setattr(bug_hunt, "_refresh_historical_package_snapshot", lambda *args: None)

    assert bug_hunt.main([]) == 0
    report = (tmp_path / bug_hunt.BUG_HUNT_DIR / "bug_hunt-0_0_13.md").read_text(encoding="utf-8")

    assert "## Package questions" in report
    assert "No maintainer-authored probing questions were supplied" in report


@pytest.mark.parametrize(
    ("content", "expected"),
    [
        (None, "No maintainer-authored probing questions were supplied"),
        ("\ufeff \n", "No maintainer-authored probing questions were supplied"),
        ("Probe hostile state.", "Probe hostile state."),
        ("## Package questions\n\nAlready wrapped.", "Already wrapped."),
    ],
)
def test_dicta_always_renders_one_package_questions_section(
    tmp_path: Path,
    content: str | None,
    expected: str,
) -> None:
    dicta = tmp_path / "dicta.md"
    if content is not None:
        _write(dicta, content)

    rendered = bug_hunt._read_dicta(dicta)

    assert rendered.count("## Package questions") == 1
    assert expected in rendered
    assert rendered.endswith("\n")


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
            "django_strawberry_framework/__init__.py\0"
            "django_strawberry_framework/testing/client.py\0"
            "django_strawberry_framework/views.py\0"
            "django_strawberry_framework/py.typed\0"
        )

    monkeypatch.setattr(snapshot, "_run_git", fake_run_git)
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
            "-z",
            "--name-only",
            "--full-tree",
            "abc123",
            "--",
            ":(top,literal)django_strawberry_framework",
        ),
    ]


def test_shadow_inputs_require_baseline_eligibility_and_a_complete_pair(tmp_path: Path) -> None:
    root = tmp_path
    current = root / bug_hunt.SHADOW_DIR
    old = "django_strawberry_framework/old.py"
    new = "django_strawberry_framework/new.py"
    excluded = "django_strawberry_framework/testing/client.py"
    partial = "django_strawberry_framework/partial.py"
    baseline = frozenset({old, excluded, partial})
    for source in (old, new, excluded):
        stem = Path(source).with_suffix("").as_posix().replace("/", "__")
        _write(current / f"{stem}.stripped.py", "VALUE = None\n")
        _write(current / f"{stem}.overview.md", "# Overview\n")
    partial_stem = Path(partial).with_suffix("").as_posix().replace("/", "__")
    _write(current / f"{partial_stem}.stripped.py", "VALUE = None\n")

    stripped, overview = bug_hunt._shadow_inputs(root, current, old, baseline)

    assert stripped is not None
    assert overview is not None
    assert bug_hunt._shadow_inputs(root, current, new, baseline) == (None, None)
    assert bug_hunt._shadow_inputs(root, current, excluded, baseline) == (None, None)
    assert bug_hunt._shadow_inputs(root, current, partial, baseline) == (None, None)


def test_snapshot_empty_inventory_publishes_an_empty_owned_directory(
    tmp_path: Path,
    monkeypatch,
) -> None:
    out_dir = tmp_path / snapshot.SHADOW_DIR
    _write(out_dir / "stale.stripped.py", "stale\n")
    _write(out_dir / "stale.overview.md", "stale\n")
    monkeypatch.setattr(snapshot, "_validate_commit", lambda commit: None)

    def fake_run_git(args: Sequence[str]) -> str:
        if args[0] == "rev-parse":
            return f"{tmp_path}\n"
        return ""

    monkeypatch.setattr(snapshot, "_run_git", fake_run_git)

    assert snapshot.main(["abc123", "--package-dir", "testing"]) == 0
    assert list(out_dir.iterdir()) == []


def test_snapshot_failure_never_publishes_partial_staging(tmp_path: Path, monkeypatch) -> None:
    out_dir = tmp_path / snapshot.SHADOW_DIR
    _write(out_dir / "previous.stripped.py", "previous\n")
    _write(out_dir / "previous.overview.md", "previous\n")
    paths = ["package/one.py", "package/two.py"]
    monkeypatch.setattr(snapshot, "_validate_commit", lambda commit: None)

    def fake_run_git(args: Sequence[str]) -> str:
        if args[0] == "rev-parse":
            return f"{tmp_path}\n"
        return "\0".join([*paths, ""])

    def fake_materialize(commit: str, path: str, target: Path) -> None:
        stem = snapshot._stem_for(path)
        _write(target / f"{stem}.stripped.py", path)
        if path == paths[1]:
            raise RuntimeError("inspection failed")
        _write(target / f"{stem}.overview.md", path)

    monkeypatch.setattr(snapshot, "_run_git", fake_run_git)
    monkeypatch.setattr(snapshot, "_materialize_and_inspect", fake_materialize)

    with pytest.raises(RuntimeError, match="inspection failed"):
        snapshot.main(["abc123", "--package-dir", "package"])

    assert {path.name for path in out_dir.iterdir()} == {
        "previous.overview.md",
        "previous.stripped.py",
    }


def test_snapshot_validation_rejects_colliding_flat_artifact_names(tmp_path: Path) -> None:
    staging = tmp_path / "staging"
    staging.mkdir()
    stem = "package__a__b"
    _write(staging / f"{stem}.stripped.py", "VALUE = None\n")
    _write(staging / f"{stem}.overview.md", "# Overview\n")

    with pytest.raises(RuntimeError, match="artifact names collide"):
        snapshot._validate_staged_snapshot(
            staging,
            ["package/a/b.py", "package/a__b.py"],
        )


def test_snapshot_publish_failure_restores_the_previous_snapshot(
    tmp_path: Path,
    monkeypatch,
) -> None:
    output = tmp_path / "current"
    staging = tmp_path / "staging"
    _write(output / "previous", "previous\n")
    _write(staging / "next", "next\n")
    replace = Path.replace

    def fail_staging_publish(source: Path, target: Path) -> Path:
        if source == staging:
            raise OSError("publish failed")
        return replace(source, target)

    monkeypatch.setattr(Path, "replace", fail_staging_publish)

    with pytest.raises(OSError, match="publish failed"):
        snapshot._publish_staged_snapshot(staging, output)

    assert (output / "previous").read_text() == "previous\n"
    assert not list(tmp_path.glob(".current-backup-*"))


def test_snapshot_rollback_failure_preserves_the_recovery_directory(
    tmp_path: Path,
    monkeypatch,
) -> None:
    output = tmp_path / "current"
    staging = tmp_path / "staging"
    _write(output / "previous", "previous\n")
    _write(staging / "next", "next\n")
    replace = Path.replace

    def fail_publish_and_rollback(source: Path, target: Path) -> Path:
        if source == staging:
            raise OSError("publish failed")
        if source.parent.name.startswith(".current-backup-") and target == output:
            raise OSError("rollback failed")
        return replace(source, target)

    monkeypatch.setattr(Path, "replace", fail_publish_and_rollback)

    with pytest.raises(RuntimeError, match="previous snapshot remains"):
        snapshot._publish_staged_snapshot(staging, output)

    backups = list(tmp_path.glob(".current-backup-*"))
    assert len(backups) == 1
    assert (backups[0] / "current" / "previous").read_text() == "previous\n"


def test_git_tree_inventory_is_rooted_literal_and_nul_framed(tmp_path: Path, monkeypatch) -> None:
    subprocess.run(["git", "init", str(tmp_path)], check=True, capture_output=True)
    nested = tmp_path / "nested"
    nested.mkdir()
    sources = {
        "package[scope]/caf\u00e9.py": "CAFE = None\n",
        "package[scope]/line\nbreak.py": "BREAK = None\n",
        "package[scope]/testing.py": "EXCLUDED = None\n",
    }
    for path, content in sources.items():
        _write(tmp_path / path, content)
    subprocess.run(
        [
            "git",
            "-C",
            str(tmp_path),
            "add",
            "--all",
        ],
        check=True,
    )
    subprocess.run(
        [
            "git",
            "-C",
            str(tmp_path),
            "-c",
            "user.name=Bug Hunt",
            "-c",
            "user.email=bug-hunt@example.invalid",
            "commit",
            "-m",
            "fixture",
        ],
        check=True,
        capture_output=True,
    )
    monkeypatch.chdir(nested)

    baseline = bug_hunt._baseline_python_paths("HEAD", "package[scope]")
    eligible = snapshot._package_python_files_at_commit("HEAD", "package[scope]")

    assert baseline == frozenset(sources)
    assert eligible == ["package[scope]/caf\u00e9.py", "package[scope]/line\nbreak.py"]


def test_package_dir_normalization_rejects_paths_outside_the_repository(
    tmp_path: Path,
) -> None:
    package = tmp_path / "package"
    package.mkdir()
    outside = tmp_path.parent / f"{tmp_path.name}-outside-package"
    outside.mkdir(exist_ok=True)
    link = tmp_path / "linked-package"
    link.symlink_to(outside, target_is_directory=True)

    assert snapshot.normalize_package_dir(tmp_path, "package/../package") == "package"
    with pytest.raises(ValueError, match="relative"):
        snapshot.normalize_package_dir(tmp_path, str(outside))
    with pytest.raises(ValueError, match="inside"):
        snapshot.normalize_package_dir(tmp_path, "linked-package")


def test_target_release_overrides_the_package_version(tmp_path: Path, monkeypatch) -> None:
    package_root = tmp_path / bug_hunt.DEFAULT_PACKAGE_DIR
    _write(package_root / "__init__.py", '__version__ = "0.0.13"\n')
    _write(package_root / "module.py", "VALUE = None\n")

    def fake_run_git(args: Sequence[str]) -> str:
        responses = {
            ("rev-parse", "--show-toplevel"): f"{tmp_path}\n",
            ("rev-parse", "HEAD"): "1234567890abcdef1234567890abcdef12345678\n",
        }
        return responses[tuple(args)]

    monkeypatch.setattr(bug_hunt, "_run_git", fake_run_git)
    monkeypatch.setattr(
        snapshot,
        "_run_git",
        lambda args: f"{bug_hunt.DEFAULT_PACKAGE_DIR}/module.py\0",
    )
    monkeypatch.setattr(
        bug_hunt,
        "_refresh_historical_package_snapshot",
        lambda *args: None,
    )

    assert bug_hunt.main(["--target-release", "0.0.14"]) == 0
    output = tmp_path / bug_hunt.BUG_HUNT_DIR / "bug_hunt-0_0_14.md"
    assert "# Bug hunt: 0.0.14" in output.read_text(encoding="utf-8")


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
