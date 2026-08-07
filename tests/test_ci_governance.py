"""Governance tests for the CI workflow definitions.

The least-privilege posture in ``.github/workflows/`` is invisible to the rest of
the suite: nothing imports a workflow, so a permission scope quietly widening, an
action pin decaying back to a mutable tag, or a new job landing without a timeout
would all pass CI. These tests assert the posture structurally instead, so the
governance contract is enforced rather than reviewed by eye.

Coverage note: the assertions target YAML under ``.github/``, not
``django_strawberry_framework``, so this module adds no package coverage surface.
"""

import re
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKFLOW_DIR = REPO_ROOT / ".github" / "workflows"

# A reviewed, immutable pin is a full 40-character commit SHA. A tag -- ``@v6``,
# ``@v6.1.0``, ``@main`` -- is mutable by definition, so the action's contents can
# change under a pin that still reads the same.
FULL_SHA = re.compile(r"^[0-9a-f]{40}$")

# Local composite actions (``./.github/actions/...``) are part of this repository
# and therefore already covered by the commit under review.
LOCAL_ACTION_PREFIX = "./"


def _workflow_paths():
    paths = sorted(WORKFLOW_DIR.glob("*.yml")) + sorted(WORKFLOW_DIR.glob("*.yaml"))
    assert paths, f"no workflow files found under {WORKFLOW_DIR}"
    return paths


def _load(path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


WORKFLOW_PATHS = _workflow_paths()
WORKFLOW_IDS = [path.name for path in WORKFLOW_PATHS]


def _jobs(workflow):
    return workflow.get("jobs") or {}


def _steps(job):
    return job.get("steps") or []


@pytest.mark.parametrize("path", WORKFLOW_PATHS, ids=WORKFLOW_IDS)
def test_workflow_parses(path):
    """Every workflow is loadable YAML with at least one job."""
    workflow = _load(path)
    assert isinstance(workflow, dict), f"{path.name}: workflow is not a mapping"
    assert _jobs(workflow), f"{path.name}: declares no jobs"


@pytest.mark.parametrize("path", WORKFLOW_PATHS, ids=WORKFLOW_IDS)
def test_workflow_declares_top_level_read_only_permissions(path):
    """Each workflow pins a read-only default GITHUB_TOKEN scope.

    Without an explicit block the token inherits the repository default, which
    may be write-all. Declaring ``contents: read`` at the top level makes any
    wider grant an explicit, reviewable job-level override.
    """
    workflow = _load(path)
    permissions = workflow.get("permissions")
    assert permissions == {"contents": "read"}, (
        f"{path.name}: top-level permissions must be exactly "
        f"{{'contents': 'read'}}, got {permissions!r}"
    )


@pytest.mark.parametrize("path", WORKFLOW_PATHS, ids=WORKFLOW_IDS)
def test_no_job_grants_repository_write(path):
    """No job may grant ``contents: write``.

    Nothing in this repository's CI pushes commits, tags, or releases. A
    ``contents: write`` grant would therefore be unused authority handed to every
    step in the job, including third-party actions and the dependency tree they
    install.
    """
    workflow = _load(path)
    for name, job in _jobs(workflow).items():
        permissions = (job or {}).get("permissions")
        if not isinstance(permissions, dict):
            continue
        assert permissions.get("contents") != "write", (
            f"{path.name}: job {name!r} grants contents: write; no CI job here "
            "pushes to the repository"
        )


@pytest.mark.parametrize("path", WORKFLOW_PATHS, ids=WORKFLOW_IDS)
def test_every_job_declares_a_timeout(path):
    """Every job bounds its own wall-clock time.

    Each job here either installs dependencies from the network or runs the test
    suite. Without ``timeout-minutes`` a hung download or a deadlocked test holds
    a runner for GitHub's six-hour default.
    """
    workflow = _load(path)
    for name, job in _jobs(workflow).items():
        job = job or {}
        if "uses" in job:
            # A reusable-workflow call cannot set timeout-minutes; the timeout
            # belongs to the jobs inside the called workflow.
            continue
        timeout = job.get("timeout-minutes")
        assert isinstance(timeout, int) and timeout > 0, (
            f"{path.name}: job {name!r} has no positive timeout-minutes (got {timeout!r})"
        )


@pytest.mark.parametrize("path", WORKFLOW_PATHS, ids=WORKFLOW_IDS)
def test_every_job_declares_a_runner(path):
    """Every job says what it runs on, so the whole file stays schedulable.

    ``runs-on`` is required, and omitting it does not fail the one job: GitHub
    refuses to parse the WORKFLOW, so a push that should have deployed reports
    an invalid-file error and nothing runs at all. That is worth a structural
    assertion rather than review, because the property is invisible from inside
    the suite and the omission is easy to introduce: this test exists because an
    edit meant to raise one job's ``timeout-minutes`` replaced the adjacent
    ``runs-on`` line along with it, and the timeout assertion above -- the one
    property the edit happened to preserve -- passed over the result.
    """
    workflow = _load(path)
    for name, job in _jobs(workflow).items():
        job = job or {}
        if "uses" in job:
            # A reusable-workflow call names no runner; the called workflow's own
            # jobs declare theirs, exactly as they declare their timeouts.
            continue
        runs_on = job.get("runs-on")
        assert runs_on, f"{path.name}: job {name!r} declares no runs-on (got {runs_on!r})"


@pytest.mark.parametrize("path", WORKFLOW_PATHS, ids=WORKFLOW_IDS)
def test_every_external_action_is_pinned_to_a_full_commit_sha(path):
    """Third-party and first-party actions alike are pinned by commit SHA.

    ``actions/checkout@v6`` re-resolves on every run, so the code executing in
    CI is whatever the tag points at today. A full-SHA pin is the only immutable
    reference GitHub offers.
    """
    workflow = _load(path)
    for name, job in _jobs(workflow).items():
        for index, step in enumerate(_steps(job or {})):
            uses = (step or {}).get("uses")
            if not uses or uses.startswith(LOCAL_ACTION_PREFIX):
                continue
            _, separator, reference = uses.partition("@")
            assert separator, f"{path.name}: job {name!r} step {index} 'uses: {uses}' has no ref"
            assert FULL_SHA.match(reference), (
                f"{path.name}: job {name!r} step {index} pins {uses!r} to a "
                "mutable ref; use a full 40-character commit SHA with a "
                "trailing '# vX.Y.Z' comment"
            )


@pytest.mark.parametrize("path", WORKFLOW_PATHS, ids=WORKFLOW_IDS)
def test_pinned_actions_keep_a_readable_version_comment(path):
    """A SHA pin carries a ``# vX.Y.Z`` comment so a reader can tell what it is.

    Asserted against the raw text, because YAML parsing discards comments.
    """
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped.startswith("- uses:") and not stripped.startswith("uses:"):
            continue
        _, _, value = stripped.partition("uses:")
        value = value.strip()
        if value.startswith(LOCAL_ACTION_PREFIX):
            continue
        _, separator, reference = value.partition("@")
        if not separator or not FULL_SHA.match(reference.split()[0].strip('"')):
            continue
        assert "#" in value, f"{path.name}: SHA-pinned {value!r} has no version comment"


@pytest.mark.parametrize("path", WORKFLOW_PATHS, ids=WORKFLOW_IDS)
def test_checkout_steps_do_not_persist_credentials(path):
    """No checkout persists its credential into ``.git/config``.

    ``actions/checkout`` writes an extraheader credential by default, leaving a
    usable token in the workspace for every later step. No job here pushes, so
    the credential has no consumer and only widens the blast radius of a
    compromised dependency.
    """
    workflow = _load(path)
    for name, job in _jobs(workflow).items():
        for index, step in enumerate(_steps(job or {})):
            uses = (step or {}).get("uses") or ""
            if not uses.startswith("actions/checkout@"):
                continue
            options = (step or {}).get("with") or {}
            assert options.get("persist-credentials") is False, (
                f"{path.name}: job {name!r} step {index} checks out without "
                "'persist-credentials: false'"
            )


def test_container_images_are_pinned_by_digest():
    """Every container image started by a workflow is digest-pinned.

    A ``postgres:16`` tag is rebuilt upstream and silently becomes a different
    image; only a ``@sha256:`` digest names one reviewed image. Matched over the
    workflow text -- images appear in ``run:`` scripts and ``services:`` blocks
    alike -- with comments stripped first, so prose naming a tag is not mistaken
    for a reference that actually starts a container.
    """
    image_reference = re.compile(r"\b(postgres|ghcr\.io/[\w./-]+)(:[\w.-]+|@sha256:[0-9a-f]{64})")
    for path in WORKFLOW_PATHS:
        executable = "\n".join(
            line.split("#", 1)[0] for line in path.read_text(encoding="utf-8").splitlines()
        )
        for match in image_reference.finditer(executable):
            name, reference = match.group(1), match.group(2)
            assert reference.startswith("@sha256:"), (
                f"{path.name}: image {name}{reference} is tag-pinned; pin it by @sha256: digest"
            )


def test_dependabot_covers_python_and_github_actions():
    """Dependabot keeps both the Python resolution and the action SHAs current.

    The ``github-actions`` entry is what stops full-SHA pins from going stale:
    an immutable pin never picks up an upstream fix on its own.
    """
    config = yaml.safe_load(
        (REPO_ROOT / ".github" / "dependabot.yml").read_text(encoding="utf-8"),
    )
    ecosystems = {entry["package-ecosystem"] for entry in config["updates"]}
    assert {"uv", "github-actions"} <= ecosystems, (
        f"dependabot.yml must cover the 'uv' and 'github-actions' ecosystems, got {ecosystems}"
    )


def test_dependency_audit_workflow_runs_on_pull_request_and_a_schedule():
    """The audit is both diff-triggered and clock-triggered.

    A PR-only audit cannot see a vulnerability published against a dependency
    that is already locked; a schedule-only audit lets one merge first.
    """
    workflow = _load(WORKFLOW_DIR / "dependency-audit.yml")
    triggers = workflow[True] if True in workflow else workflow["on"]
    assert "pull_request" in triggers, "dependency audit must run on pull requests"
    assert triggers.get("schedule"), "dependency audit must run on a schedule"
