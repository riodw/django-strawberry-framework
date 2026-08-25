"""Governance tests for the CI workflow definitions.

This module is the home for standing repo-wide structural pins - properties of
the repository that no other test can see because nothing imports the artifact
carrying them. Two corpora sit under it: the least-privilege posture in
``.github/workflows/`` (nothing imports a workflow, so a permission scope quietly
widening, an action pin decaying back to a mutable tag, or a new job landing
without a timeout would all pass CI) and the first-party Python sources (whose
``extensions=`` construction shape is a per-request performance contract no
assertion inside a single test module can hold repo-wide). These tests assert
each posture structurally instead, so the governance contract is enforced rather
than reviewed by eye.

Coverage note: the assertions target YAML under ``.github/`` and the text of
first-party ``.py`` files, not ``django_strawberry_framework``'s runtime
behavior, so this module adds no package coverage surface.
"""

import ast
import re
import subprocess
from pathlib import Path

import pytest
import yaml

# The repo-wide Python sweep below borrows this repo's existing definition of the
# first-party source trees rather than re-listing them, so the two cannot drift
# apart. Its exact scope is the four trees named by ``check_citations``'s
# ``SOURCE_TREES``, which is NOT literally every first-party .py: three tracked
# modules (``conftest.py``, ``line_count.py``, ``docs/dry/export_dry_review.py``)
# sit outside those trees, so ``EXTRA_SOURCE_FILES`` below adds them back and the
# corpus census pins the union against git. Walking the trees rather than the
# filesystem also excludes the gitignored ``docs/*/temp-tests/`` scratch by
# construction, so the gate cannot pass in a clean CI checkout and fail on a
# developer machine.
from scripts.check_citations import SOURCE_TREES, iter_python_sources

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


# ---------------------------------------------------------------------------
# Standing pin: no active .py may construct a schema with a forbidden
# DjangoOptimizerExtension ``extensions=`` form (spec-029 Decision 3).
# ---------------------------------------------------------------------------

OPTIMIZER_EXTENSION = "DjangoOptimizerExtension"

#: The corrective form, quoted in every failure message.
OPTIMIZER_FIX = f"optimizer = {OPTIMIZER_EXTENSION}(...) then extensions=[lambda: optimizer]"


def _forbidden_optimizer_entries(source, label):
    """Yield ``(lineno, form, snippet)`` per forbidden optimizer ``extensions=`` entry.

    Takes source TEXT plus a label rather than a path, so the control rows below
    can feed it literal snippets - the controls are what pin the classifier, and
    a path-only signature would make them impossible to write.

    Two rules, matched on FORM rather than on a literal spelling (the spelling is
    what let this regression back in: a grep for ``lambda: DjangoOptimizerExtension()``
    misses every ``strictness=`` / ``nested_connection_strategy=`` variant):

    1. any ``lambda`` whose body constructs the optimizer;
    2. any bare optimizer class load that is an ELEMENT of a list or tuple
       literal and is not itself the callee of a call.
    """
    tree = ast.parse(source, filename=label)
    call_funcs = {id(node.func) for node in ast.walk(tree) if isinstance(node, ast.Call)}
    sequence_elements = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.List, ast.Tuple)):
            sequence_elements.update(id(element) for element in node.elts)
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Lambda):
            body = node.body
            if isinstance(body, ast.Call) and OPTIMIZER_EXTENSION in ast.unparse(body.func):
                found.append((node.lineno, "constructing lambda", ast.unparse(node)))
        if (
            isinstance(node, ast.Name)
            and node.id == OPTIMIZER_EXTENSION
            and isinstance(node.ctx, ast.Load)
            and id(node) not in call_funcs
            and id(node) in sequence_elements
        ):
            found.append((node.lineno, "bare class in a sequence", OPTIMIZER_EXTENSION))
    return sorted(found)


# Positive controls. A sweep instrument dies silently on shape drift, and a
# control that did not run reads identically to a passing proof - so every form
# the classifier claims to catch is exhibited here as a row of its own.
MUST_FLAG_SNIPPETS = [
    ("bare-single", "schema = Schema(query=Q, extensions=[DjangoOptimizerExtension])"),
    ("bare-tuple", "schema = Schema(query=Q, extensions=(DjangoOptimizerExtension,))"),
    (
        "bare-multi-element",
        "schema = Schema(query=Q, extensions=[DjangoDebugExtension, DjangoOptimizerExtension])",
    ),
    (
        "bare-multiline",
        "schema = Schema(\n    query=Q,\n    extensions=[\n        DjangoOptimizerExtension,\n    ],\n)",
    ),
    ("bare-assigned-to-a-variable", "extensions = [DjangoOptimizerExtension]"),
    (
        "lambda-no-args",
        "schema = Schema(query=Q, extensions=[lambda: DjangoOptimizerExtension()])",
    ),
    (
        "lambda-with-kwargs",
        'schema = Schema(query=Q, extensions=[lambda: DjangoOptimizerExtension(strictness="raise")])',
    ),
    (
        "lambda-in-a-conditional-expression",
        "extensions = [lambda: DjangoOptimizerExtension()] if optimizer else []",
    ),
    ("lambda-dotted", "extensions = [lambda: optimizer.DjangoOptimizerExtension()]"),
]

# Negative controls. Each is a form that LOOKS like the violation to a
# vocabulary-shaped sweep and is not one. Two are load-bearing: the debug
# extension's own docstring REQUIRES the bare class and forbids a pre-built
# instance, and the error-policy extension's says the two forms behave
# identically. A rule that flagged every bare-class entry would break the first.
MUST_NOT_FLAG_SNIPPETS = [
    ("factory-over-a-singleton", "extensions = [lambda: ext]"),
    ("factory-over-a-module-singleton", "extensions = [lambda: _optimizer]"),
    ("bare-debug-extension", "extensions = [DjangoDebugExtension]"),
    ("bare-error-policy-extension", "extensions = [DjangoErrorPolicyExtension]"),
    (
        "lambda-constructing-another-extension",
        "extensions = [lambda: DjangoDebugExtension(allow_unsafe_production=True)]",
    ),
    ("subclass-declaration", "class _CaptureExt(DjangoOptimizerExtension):\n    pass"),
    ("classmethod-call", "DjangoOptimizerExtension.check_schema(schema)"),
    ("identity-assertion", "assert DjangoOptimizerExtension is Other"),
    ("bare-instance-assignment", "ext = DjangoOptimizerExtension()\nextensions = [ext]"),
]


@pytest.mark.parametrize(
    "snippet",
    [snippet for _, snippet in MUST_FLAG_SNIPPETS],
    ids=[name for name, _ in MUST_FLAG_SNIPPETS],
)
def test_forbidden_optimizer_form_classifier_flags_every_forbidden_shape(snippet):
    """Each forbidden shape the sweep claims to catch is exhibited as its own row.

    These rows are the sweep's positive control. Without them the sweep can go
    green because the corpus is clean OR because the classifier stopped matching
    anything at all, and those two readings are indistinguishable from a passing
    run - which is exactly how four sweep instruments in this repo's history died
    silently on delimiter drift.
    """
    assert _forbidden_optimizer_entries(snippet, "<must-flag>"), (
        f"the forbidden-form classifier no longer flags this shape:\n{snippet}"
    )


@pytest.mark.parametrize(
    "snippet",
    [snippet for _, snippet in MUST_NOT_FLAG_SNIPPETS],
    ids=[name for name, _ in MUST_NOT_FLAG_SNIPPETS],
)
def test_forbidden_optimizer_form_classifier_ignores_the_permitted_shapes(snippet):
    """The negative control: only the optimizer's own two forbidden forms match.

    ``DjangoDebugExtension``'s docstring REQUIRES the bare class and forbids a
    pre-built instance; ``DjangoErrorPolicyExtension``'s says a bare class and a
    factory behave identically. Only the optimizer carries the shared
    instance-bound plan cache, so only the optimizer is in scope, and widening
    this rule to every bare-class entry would break a documented contract.
    """
    assert _forbidden_optimizer_entries(snippet, "<must-not-flag>") == [], (
        f"the forbidden-form classifier now over-flags this permitted shape:\n{snippet}"
    )


#: Tracked first-party modules that live OUTSIDE ``check_citations``'s source
#: trees. Without them the sweep would stop at those four trees while claiming
#: every first-party module, and the repo-root ``conftest.py`` is a plausible
#: home for a shared schema fixture. The census below is what keeps this tuple
#: honest: a new ``.py`` outside the trees fails that row by name instead of
#: silently sitting outside the gate.
EXTRA_SOURCE_FILES = ("conftest.py", "docs/dry/export_dry_review.py", "line_count.py")

#: Files whose presence in the corpus the forbidden-form gate's answer rests on:
#: the optimizer's own module, the module that defines the corpus, one file per
#: source tree, the file added by ``EXTRA_SOURCE_FILES``, and every module the
#: spec-029 repair edited. Named individually so a narrowed corpus fails by
#: saying WHICH files left, and so the failure survives a machine without git.
CORPUS_REACH_FILES = (
    "conftest.py",
    "django_strawberry_framework/optimizer/extension.py",
    "examples/fakeshop/strategy_schemas.py",
    "examples/fakeshop/test_query/test_products_visibility_api.py",
    "scripts/check_citations.py",
    "tests/forms/test_resolvers.py",
    "tests/mutations/test_resolvers.py",
    "tests/mutations/test_write_transaction.py",
    "tests/optimizer/test_extension.py",
    "tests/test_relay_connection.py",
    "tests/types/test_resolvers.py",
)

#: This module's own repo-relative path, derived rather than written down so a
#: rename cannot strand it. The census's oracle is asked about the checkout that
#: is executing this file, so an answer omitting it is not an answer about this
#: repository at all.
CENSUS_MODULE = Path(__file__).resolve().relative_to(REPO_ROOT).as_posix()

#: What any coherent ``git ls-files`` answer must report. The census subtracts the
#: sweep's corpus FROM this answer, so an answer enumerating nothing makes that
#: subtraction empty for EVERY corpus and the row can never fail again - and git
#: gives exactly that answer, at exit 0 and with no error to detect, whenever it
#: runs against a directory that is untracked-and-ignored inside an enclosing
#: repository (an export or vendored copy unpacked under another repo's ignored
#: path). Guard the ANSWER, not one spelling of the incoherent input: ``assert
#: answer`` refuses only the totally empty case while a partially enumerated one
#: walks straight through it, so the requirement is named files - this module,
#: plus every file the gate's answer already rests on.
ORACLE_REQUIRED_FILES = (CENSUS_MODULE, *CORPUS_REACH_FILES)

#: The one corpus region that is not a source tree: the tracked modules
#: ``EXTRA_SOURCE_FILES`` carries back in from outside them all. A label rather
#: than a path, so it can never be mistaken for one.
EXTRA_FILES_REGION = "outside-the-source-trees"

#: Every region the sweep's corpus is assembled from, in the vocabulary the
#: requirement above has to reach: this module, each source tree, and the files
#: outside them all. Derived from ``SOURCE_TREES`` and ``EXTRA_SOURCE_FILES``
#: instead of written down again - a fourth hardcoded list would need a fourth
#: thing to contradict it, which is the regress the rows below exist to end.
CORPUS_REGIONS = (CENSUS_MODULE, *SOURCE_TREES, EXTRA_FILES_REGION)


def _sweep_corpus():
    """Return every first-party ``.py`` file the forbidden-form sweep reads."""
    extra = (REPO_ROOT / name for name in EXTRA_SOURCE_FILES)
    return tuple(sorted({*iter_python_sources(), *(path for path in extra if path.is_file())}))


def _committable_python_files():
    """Return the ``.py`` paths a commit here could contain, repo-relative.

    ``--cached --others --exclude-standard`` is exactly "tracked, plus untracked
    but not ignored". It is an oracle for "first-party source" derived from git
    rather than from the sweep's own tree list, which is what makes the census
    below a measurement instead of a restatement of the corpus by itself.

    Three ways git can fail to answer, and none may reduce the census to nothing.
    A missing ``git`` raises here; a non-zero exit trips the assert below; and an
    exit-0 answer that enumerates nothing - what git returns when run against a
    directory that is untracked-and-ignored inside an enclosing repository - is
    refused by the caller through ``_unreported_required_files``. That third one
    reports no error of any kind: it is a coherent-LOOKING answer that happens to
    be wrong, which is the class no return code can catch.
    """
    completed = subprocess.run(
        [
            "git",
            "-C",
            str(REPO_ROOT),
            "ls-files",
            "-z",
            "--cached",
            "--others",
            "--exclude-standard",
            "--",
            "*.py",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, (
        f"git ls-files failed ({completed.returncode}); the corpus census cannot "
        f"be taken without it: {completed.stderr.strip()}"
    )
    return {name for name in completed.stdout.split("\0") if name}


def _unreported_required_files(answer):
    """Return the paths a coherent oracle answer must carry that ``answer`` lacks.

    A pure function over one git answer, so the control rows below can feed it
    answers the live tree cannot produce - an empty one, a truncated one. A guard
    whose whole job is to refuse an answer has no other exercise: while git
    answers correctly here, nothing would ever run the refusing branch, and a
    guard that never ran reads exactly like a guard that found nothing.
    """
    return sorted(set(ORACLE_REQUIRED_FILES) - set(answer))


def _unrepresented_corpus_regions(required):
    """Return the corpus regions ``required`` names no file inside.

    ``ORACLE_REQUIRED_FILES`` is the only hardcoded tuple this gate reads that
    feeds assertions without also feeding an answer: the census subtracts it, the
    reach rows iterate it, and nothing measures it - so halving it deletes rows in
    silence rather than failing one. This is its contradictor, and it writes down
    no data of its own, deriving what the requirement must reach from the two
    definitions the census already disagrees with.

    A pure function over one requirement tuple, so the rows below can feed it the
    narrowed requirements the shipped module never holds. A region is reached when
    the requirement names this module, a file inside that tree, or one of the
    modules carried in from outside every tree.
    """
    named = set(required)
    unrepresented = [] if CENSUS_MODULE in named else [CENSUS_MODULE]
    unrepresented.extend(
        tree for tree in SOURCE_TREES if not any(name.startswith(f"{tree}/") for name in named)
    )
    if not named.intersection(EXTRA_SOURCE_FILES):
        unrepresented.append(EXTRA_FILES_REGION)
    return unrepresented


def _forbidden_entries_in(paths):
    """Return one formatted violation string per forbidden entry found in ``paths``.

    Split out of the sweep so the find-and-format path can be exercised against a
    synthetic corpus. Once the sweep is green the live tree contains no violation
    by construction, so nothing else here would run this formatting - and a
    reporter that had stopped formatting anything would read exactly like a clean
    tree.
    """
    violations = []
    for path in paths:
        display = path.relative_to(REPO_ROOT) if path.is_relative_to(REPO_ROOT) else path
        violations.extend(
            f"{display}:{lineno}: {form}: {snippet}"
            for lineno, form, snippet in _forbidden_optimizer_entries(
                path.read_text(encoding="utf-8"),
                str(path),
            )
        )
    return violations


def test_the_sweep_corpus_covers_every_committable_python_file():
    """The corpus the gate walks is the corpus it claims to walk.

    ``for path in <corpus>`` then ``assert not violations`` is green both when the
    corpus is CLEAN and when the corpus has silently NARROWED - the fail-open
    shape where "cannot enumerate" becomes "permit". No other row here can tell
    those two readings apart: the classifier's control rows are fed literal
    snippets and never touch the corpus, and the sweep itself passes hardest when
    it sees nothing at all.

    Measured, not argued: dropping ``"tests"`` from ``check_citations``'s
    ``SOURCE_TREES`` removes 136 files from the sweep - most of the sites the
    spec-029 repair fixed - while ``check_citations`` itself stays green, because
    no citation happens to point into the files that left.

    Only the missing direction is asserted. A path the corpus holds and git does
    not list (local scratch inside a source tree) makes the gate stricter, never
    blinder; asserting equality instead would fail on a developer machine while
    passing in CI.

    The same fail-open shape one level up is why the oracle is checked before it
    is believed: this row subtracts the corpus FROM git's answer, so an answer
    that enumerates nothing leaves nothing missing whatever the corpus holds, and
    the row stops being able to fail. Checking that the answer carries the files
    it must carry is what keeps ``not missing`` a measurement.
    """
    committable = _committable_python_files()
    unreported = _unreported_required_files(committable)
    assert not unreported, (
        f"git enumerated {len(committable)} .py file(s) but not "
        + ", ".join(unreported)
        + " - so it did not answer about this repository (it reports nothing, at "
        "exit 0, when run inside an enclosing repo's ignored path) and the census "
        "below could not tell a complete corpus from an empty one"
    )
    swept = {str(path.relative_to(REPO_ROOT)) for path in _sweep_corpus()}
    missing = sorted(committable - swept)
    assert not missing, (
        f"{len(missing)} committable .py file(s) are outside the forbidden-form "
        "sweep's corpus, so the gate cannot see them:\n"
        + "\n".join(missing)
        + "\nAdd the tree to check_citations.SOURCE_TREES, or the file to "
        "EXTRA_SOURCE_FILES."
    )


def test_the_git_oracle_enumerates_this_module():
    """git answered about THIS repository, so the census has an oracle at all.

    Self-membership is the check that survives every way the answer can be wrong
    without being an error: this module is running and it is tracked, so any
    answer about this checkout carries it. An answer that does not is one git
    gave about some enclosing repository, and the census would read it as
    "nothing is missing from the corpus".
    """
    assert CENSUS_MODULE in _committable_python_files(), (
        f"git did not report {CENSUS_MODULE}, so the corpus census has no oracle; "
        "a checkout that is not itself a git repository answers exactly this way, "
        "at exit 0, with no error to detect"
    )


#: Answers no coherent oracle can give, each paired with a path it should have
#: reported. The last three are the load-bearing rows: a non-empty check accepts
#: all of them, which is why the guard requires named files rather than a size.
INCOHERENT_ORACLE_ANSWERS = [
    ("enumerates-nothing", (), CENSUS_MODULE),
    ("only-this-module", (CENSUS_MODULE,), "conftest.py"),
    ("only-one-load-bearing-file", ("conftest.py",), CENSUS_MODULE),
    ("every-load-bearing-file-but-this-module", CORPUS_REACH_FILES, CENSUS_MODULE),
]


@pytest.mark.parametrize(
    ("answer", "expected"),
    [(answer, expected) for _, answer, expected in INCOHERENT_ORACLE_ANSWERS],
    ids=[name for name, _, _ in INCOHERENT_ORACLE_ANSWERS],
)
def test_the_corpus_census_refuses_an_incoherent_oracle_answer(answer, expected):
    """An under-enumerating oracle is refused by name, not by size.

    These are the answers the live tree cannot produce, so nothing else here runs
    the refusing branch. Both halves matter: an empty answer is what git returns
    at exit 0 from inside an enclosing repository's ignored path, and a truncated
    answer is what a bare ``assert answer`` would wave through while the census it
    feeds silently stops measuring.
    """
    assert expected in _unreported_required_files(answer), (
        f"an oracle answer of {sorted(answer)} was accepted as complete even "
        f"though it does not report {expected}"
    )


def test_the_corpus_census_accepts_a_complete_oracle_answer():
    """The guard's negative direction: a complete answer is not refused."""
    assert _unreported_required_files(ORACLE_REQUIRED_FILES) == []


@pytest.mark.parametrize("region", CORPUS_REGIONS, ids=CORPUS_REGIONS)
def test_the_oracle_requirement_reaches_every_corpus_region(region):
    """What the oracle must report stays as wide as the corpus it is asked about.

    Measured, not argued: narrowing ``CORPUS_REACH_FILES`` to its ``conftest.py``
    entry alone deleted ten reach rows and cut this requirement from twelve files
    to two with nothing failing, and narrowing it to the optimizer module instead
    tripped exactly one row - and that one only because an incoherent-oracle
    control happens to hardcode ``"conftest.py"`` for an unrelated purpose.
    Protection that is a side effect of another row's literal is not a contract,
    so the requirement had no contradictor at all.

    These rows are it. They assert the structural property the requirement exists
    to hold - this module, every tree the corpus is walked from, and the modules
    carried in from outside them - so a narrowing fails by naming the region it
    cost. Not a count and not a copy of the tuple: a count gets "fixed" to the new
    number, and a copy is one more list needing a contradictor of its own.
    """
    assert region not in _unrepresented_corpus_regions(ORACLE_REQUIRED_FILES), (
        f"ORACLE_REQUIRED_FILES names nothing in {region}, so a corpus that lost "
        f"{region} entirely would still satisfy the census's oracle guard"
    )


#: Requirements too narrow to be a requirement, each paired with a region it
#: stops reaching. Built from the region vocabulary itself, so they keep narrowing
#: in a real direction if the corpus definitions later move.
NARROWED_REQUIREMENTS = [
    ("names-nothing", (), CENSUS_MODULE),
    ("only-this-module", (CENSUS_MODULE,), EXTRA_FILES_REGION),
    ("only-outside-the-trees", EXTRA_SOURCE_FILES, CENSUS_MODULE),
    (
        "every-tree-but-nothing-outside-them",
        (CENSUS_MODULE, *(f"{tree}/anything.py" for tree in SOURCE_TREES)),
        EXTRA_FILES_REGION,
    ),
    (
        "every-region-but-one-tree",
        (
            CENSUS_MODULE,
            *EXTRA_SOURCE_FILES,
            *(f"{tree}/anything.py" for tree in SOURCE_TREES[1:]),
        ),
        SOURCE_TREES[0],
    ),
]


@pytest.mark.parametrize(
    ("required", "expected"),
    [(required, expected) for _, required, expected in NARROWED_REQUIREMENTS],
    ids=[name for name, _, _ in NARROWED_REQUIREMENTS],
)
def test_a_narrowed_oracle_requirement_names_the_region_it_lost(required, expected):
    """A requirement that stopped covering a region is refused, by region.

    The refusing direction of the guard above, which the shipped requirement can
    never exercise: while ``ORACLE_REQUIRED_FILES`` is wide enough, nothing runs
    the branch that reports a region as unreached, and a branch that never ran
    reads exactly like one that found nothing.
    """
    assert expected in _unrepresented_corpus_regions(required), (
        f"a requirement of {sorted(required)} was accepted as reaching the whole "
        f"corpus even though it names nothing in {expected}"
    )


@pytest.mark.parametrize("relative", CORPUS_REACH_FILES, ids=CORPUS_REACH_FILES)
def test_the_sweep_corpus_reaches_each_load_bearing_file(relative):
    """Each file the gate's answer depends on is inside the corpus, by name.

    The census above catches any narrowing; these rows say which files a
    narrowing cost, and they hold without git. Two instruments rather than one
    written twice: different oracle, different failure text, and a whole-tree
    drop fails several of these at once.
    """
    assert REPO_ROOT / relative in _sweep_corpus(), (
        f"{relative} is not in the forbidden-form sweep's corpus; the gate's "
        "answer does not cover it"
    )


@pytest.mark.parametrize(
    ("entry", "form"),
    [
        ("extensions=[DjangoOptimizerExtension]", "bare class in a sequence"),
        (
            'extensions=[lambda: DjangoOptimizerExtension(strictness="raise")]',
            "constructing lambda",
        ),
    ],
    ids=["bare-class", "constructing-lambda"],
)
def test_the_sweep_reports_a_planted_violation_with_its_file_and_line(tmp_path, entry, form):
    """The find-and-format path is pinned independently of the live tree.

    The sweep's own row can only ever report success while the repository is
    clean, so the code that finds a violation and formats it into a readable
    location has no other exercise. A synthetic one-file corpus gives it one.
    """
    planted = tmp_path / "planted_schema.py"
    planted.write_text(f"# a planted corpus\n# line two\nschema = Schema(query=Q, {entry})\n")
    reported = _forbidden_entries_in([planted])
    assert len(reported) == 1, f"expected one violation from the planted file, got {reported}"
    assert reported[0].startswith(f"{planted}:3: {form}: "), reported[0]


def test_the_sweep_reports_nothing_for_a_planted_permitted_form(tmp_path):
    """The reporter's negative direction: a clean file yields no violation."""
    planted = tmp_path / "planted_schema.py"
    planted.write_text(
        "optimizer = DjangoOptimizerExtension()\nextensions = [lambda: optimizer]\n",
    )
    assert _forbidden_entries_in([planted]) == []


def test_no_active_source_uses_a_forbidden_optimizer_extensions_form():
    """No first-party ``.py`` builds a schema with a cold-cached optimizer.

    Two forms are forbidden (spec-029 Decision 3): the bare class
    ``extensions=[DjangoOptimizerExtension]`` and any constructing lambda
    ``extensions=[lambda: DjangoOptimizerExtension(...)]``. Strawberry's
    ``Schema.get_extensions`` runs each non-instance entry ONCE PER OPERATION, in
    both sync and async modes, so both forms hand every request a brand-new
    extension - and the optimizer's plan cache lives on the instance
    (``self._plan_cache``), giving it a structurally zero hit rate. The fix is a
    factory over a singleton scoped to that construction site:
    ``ext = DjangoOptimizerExtension(...)`` then ``extensions=[lambda: ext]``.

    This pin exists because the rule previously had no gate: spec-029 enforced it
    with a one-shot build-time grep, and four later cards reintroduced both forms
    across five patch releases with nothing noticing. A rule with no gate rots.

    Deliberate limits, considered rather than missed. The pin does NOT match the
    deprecated instance form ``extensions=[DjangoOptimizerExtension()]`` (already
    fatal at runtime, since Strawberry's ``DeprecationWarning`` meets
    ``pytest.ini``'s ``filterwarnings = error``), a SUBCLASS entry spelled under
    another name, or a named module-level function that constructs the optimizer;
    the last two would need name resolution and neither exists here.

    Its false-positive direction is deliberate too, and BOTH arms have one. The
    bare-class rule flags the class in ANY list or tuple literal, not only in an
    ``extensions=`` argument, so a future ``for cls in [DjangoOptimizerExtension,
    ...]:`` would trip it. The lambda rule matches the optimizer's name as a
    SUBSTRING of the unparsed callee, so a dotted spelling
    (``lambda: optimizer.DjangoOptimizerExtension()``) is caught on purpose and an
    affixed one (``lambda: MyDjangoOptimizerExtensionWrapper()``) is caught as a
    side effect. A false positive here is one loud, one-line-to-fix failure; a
    false negative is the rot this pin exists to stop. Repair the rule rather than
    deleting the test.

    What this row CANNOT see is its own corpus: it is green over an empty one.
    ``test_the_sweep_corpus_covers_every_committable_python_file`` and the
    per-file reach rows above are what make its silence mean something.
    """
    violations = _forbidden_entries_in(_sweep_corpus())
    assert not violations, (
        "forbidden DjangoOptimizerExtension extensions= form(s) in active source:\n"
        + "\n".join(violations)
        + f"\nUse a factory over a singleton scoped to that construction site: {OPTIMIZER_FIX}"
    )
