"""Script tests for clean_up generated-artifact deletion boundaries."""

from pathlib import Path

from scripts import clean_up


def _write(root: Path, relative_path: str) -> Path:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("generated", encoding="utf-8")
    return path


def test_clean_up_targets_current_generated_artifacts(tmp_path, monkeypatch):
    monkeypatch.setattr(clean_up, "REPO_ROOT", tmp_path)

    deleted_paths = {
        "docs/shadow/current",
        "docs/review/temp-tests/repro.py",
        "docs/review/worker-memory/worker-0.md",
        "docs/review/rev-generated.py",
        "docs/review/review-generated.py",
        "docs/builder/temp-tests/probe.py",
        "docs/builder/worker-memory/worker-1.md",
        "docs/dry/worker-memory/worker-2.md",
        "docs/builder/bld-final.md",
        "docs/builder/bld-generated.py",
        "docs/builder/review-generated.py",
        "docs/bug_hunt/bug_hunt.abc123.md",
    }
    kept_paths = {
        "docs/review/rev-permanent.md",
        "docs/review/review-0_0_8.md",
        "docs/builder/BUILD.md",
        "docs/builder/build-027-filters-0_0_8.md",
        "docs/builder/worker-0.md",
        "docs/bug_hunt/HUNT.md",
        "docs/bug_hunt/dicta.md",
    }

    _write(tmp_path, "docs/shadow/current/module.py")
    for relative_path in deleted_paths - {"docs/shadow/current"}:
        _write(tmp_path, relative_path)
    for relative_path in kept_paths:
        _write(tmp_path, relative_path)

    deleted = {path.relative_to(tmp_path).as_posix() for path in clean_up.clean_up()}

    assert deleted == deleted_paths
    for relative_path in deleted_paths:
        assert not (tmp_path / relative_path).exists()
    for relative_path in kept_paths:
        assert (tmp_path / relative_path).exists()
    assert (tmp_path / "docs/review/worker-memory").exists()
    assert (tmp_path / "docs/builder/worker-memory").exists()
    assert (tmp_path / "docs/dry/worker-memory").exists()
