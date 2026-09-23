"""Run manifest-driven failability proofs: mutate a boundary, run, restore, prove.

Mechanizes ``docs/builder/BUILD.md`` "Failability proofs: prove the test can
fail". A passing suite is evidence only if it could have failed, so each new
boundary owes one loop: transiently remove the boundary, observe which test
rows fail, restore, and prove the restore by byte comparison.

The loop was previously prose in three documents executed by hand, which is
how a proof gets written from memory and how a revert gets asserted rather than
proved. Everything this script emits is measured in the same process that made
the mutation.

Deliberate properties, each one a hand-run failure mode this encodes away:

* **No ``git``.** Not for the mutation, not for the restore, not for the proof.
  The working tree is legitimately dirty during a build, so an empty
  ``git diff`` is unachievable and ``git checkout -- <path>`` would destroy the
  builder's own change. The restore target is a copy taken *before* mutating.
* **Anchors, not line numbers.** A proof entry locates its site by an exact
  substring that must match **exactly once**. Zero or several matches aborts
  that entry before anything is written, so a mutation can never stack or land
  somewhere unintended.
* **Node ids, not just a count.** "The number of failing rows" is
  scope-sensitive: a wider focused scope inflates it, which silently moves a
  boundary across the mandatory independent re-run floor. Recording the node ids
  and the scope as run makes two independent measurements comparable by set
  difference instead of by number.
* **One mutation live at a time**, restored in a ``finally``, with the restore
  proved by byte comparison before the next entry starts. A restore that cannot
  be proved stops the run loudly instead of continuing.
* **A crash leaves evidence.** While a mutation is live, an
  ``ACTIVE-MUTATION.json`` marker in the scratch directory names the mutated
  file and the pristine copy that restores it.
* **The pre-mutation baseline is not optional.** ``BUILD.md`` "What gets
  recorded" requires the pre-mutation state of the same scope, so every scope is
  run unmutated first and already-failing rows are differenced out. In a tree
  legitimately dirty with several cohorts' work, one pre-existing failing row
  inflates the count and can make a genuinely 0-row boundary read as pinned -
  the exact fail-open the acceptance rule exists to catch. ``--no-baseline``
  exists for a quick local probe and then refuses ``--output``: a report missing
  a mandatory field is not an ``ARTIFACT.md`` record.
* **Collection or setup errors invalidate the count.** Rows that never ran
  cannot fail, so an error-bearing run is not evidence of anything - it is
  reported as an invalid count and fails the exit code, never footnoted.
* **A pytest exit code outside ``{0, 1}`` is an invalid count too**, in the
  baseline run and the mutant run alike. Exit ``5`` (nothing collected - a
  mistyped scope path or a node id that no longer exists), ``4`` (usage error),
  ``2`` (interrupted) and ``3`` (internal error) each emit zero ``FAILED``
  lines, which is textually indistinguishable from "the boundary is unpinned".
  Recording that as a measured 0 and handing it the ``why 0`` slot is how a
  scope typo becomes an accepted harness limitation, so the exit code is read as
  a validity channel and routed through the same machinery as a collection
  error. A baseline that could not run is no reference to difference against.
* **A narrowed run says so in its own report.** ``--only`` selects a subset, and
  the emitted block used to be textually identical to a complete run's - so
  ``--only 3 --output`` produced a record covering one boundary of twenty that
  reads as an ``ARTIFACT.md`` ``### Failability proofs`` subsection, which
  requires one entry per new boundary. ``--only`` is not refused ``--output``
  the way ``--no-baseline`` is, because it has a legitimate use the other lacks
  (Worker 3's mandatory independent re-run covers a *subset*, and that re-run is
  recorded): a narrowed run is a truthful record of fewer boundaries, whereas a
  baseline-less one is a record missing a mandatory field. Instead the block is
  labelled **PARTIAL RECORD** immediately under its heading, again as its last
  line, and structurally in the ``#`` column - which carries manifest positions,
  not sequence numbers - and it names every manifest entry it did not prove.
* **The record names the file that was actually mutated**, and a ``label`` whose
  leading path segment disagrees with ``target`` is refused. ``label`` is free
  manifest text while ``target`` is separately resolved, so an entry labelled
  ``package/views.py::Mixin.method`` carrying ``"target": "tests/test_views.py"``
  emitted a record claiming a production boundary had been removed while the
  mutation landed in a test file. A label need not carry a path at all (a bare
  symbol is a legitimate shape), so absence is accepted and only disagreement is
  refused - and the resolved target is rendered in the block either way.
* **A scope may not stop the run early.** ``-x`` (bundled or alone),
  ``--exitfirst`` and ``--maxfail`` are refused alongside ``--cov``: the rows
  after the cut never run and cannot fail, so the recorded count belongs to a
  different row set than the scope it names, and the cut falls in a different
  place in the unmutated run than in the mutated one. Because the fragment
  travels in the recorded scope, an independent re-run reproduces the same wrong
  number - two measurements agreeing on it rather than differing.

Manifest format (JSON; every string field may also be given as a list of
lines, which is joined with newlines so multi-line blocks stay readable)::

    {
      "scratch_root": "/tmp/failability-proofs",       // optional
      "proofs": [
        {
          "label": "package/views.py::Mixin.method",   // symbol-qualified path; a
                                                     // leading path must be the target
          "target": "package/views.py",                // repo-relative
          "anchor": ["        if not gate(request):", "            return"],
          "replacement": "        return",             // or "delete": true
          "mutation": "the gate body replaced by a no-op",   // optional prose;
                                                     // ACCOMPANIES the derived
                                                     // anchor -> replacement,
                                                     // never replaces it
          "scope": ["tests/test_views.py"]              // pytest arguments
        }
      ]
    }

Every field below is optional, and an entry that uses none of them is graded
exactly as above.

* ``"expect_failing": [<node id or glob>, ...]`` declares the failing set the
  mutation must produce. When present it replaces the row-count grading: the
  verdict is "observed attributable failures == declared set" (every pattern
  matches at least one attributable failing row, every attributable failing
  row matches some pattern; a pattern matches a node id when it is equal to it
  or ``fnmatch`` matches it). The weakly-pinned and re-run-floor arithmetic is
  not applied, so one query-count test failing ``assert 6 == 1`` is a complete
  proof when it is the row the proof names. ``[]`` is a behaviour-preservation
  proof: the mutation (usually a revert) must make no row fail.
* ``"pre_image": "<file>"`` with ``target`` replaces the target's bytes
  wholesale with a saved pre-image (for example ``git show <base>:<path>``
  written to a file by the caller). Refused when the pre-image equals the
  current bytes.
* ``"reverse_patch": "<file>"`` reverts a unified diff (``git diff <base> --
  <paths>`` saved to a file) with a pure-Python hunk applier: each hunk's
  post-image must occur in the current file exactly once (several occurrences
  are resolved only by the hunk header's own position), and is replaced by its
  pre-image. With ``target`` only that file's section is applied; without it
  every file section in the diff becomes a site. A diff that creates or deletes
  a file is refused.
* ``"sites": [<site>, ...]`` mutates several places together: each site is an
  object with ``target`` plus exactly one of ``anchor`` (with ``replacement`` or
  ``delete``), ``pre_image`` or ``reverse_patch``. All sites are applied before
  the mutant run and every mutated file is restored and byte-compared in the
  ``finally``. An entry with ``sites`` carries no top-level ``target``,
  ``anchor``, ``replacement``, ``delete``, ``pre_image`` or ``reverse_patch``.
  Several anchor sites may share a target (applied in order); a pre-image or
  reverse-patch site may not share its target with another site.

``pre_image`` and ``reverse_patch`` paths are resolved against the manifest's
directory when relative.

Every run carries a small pytest plugin written into the scratch root (``-p``
plus ``PYTHONPATH``), so what the record says the run imported is observed by
the pytest process itself, never by a sibling interpreter: the package
``__file__``, every configured database ``NAME``, ``sys.executable`` and the
working directory, from the controller and every xdist worker, plus the crash
line (``path:line: message``) of every failing row. A run whose package
``__file__`` lies outside the repository root measured another tree and is an
invalid count. Pristine and mutated files are recorded by git blob id
(computed as ``git hash-object`` computes it, without invoking git).

Usage::

    uv run python scripts/prove_failability.py <manifest.json>
    uv run python scripts/prove_failability.py <manifest.json> --check-anchors-only
    uv run python scripts/prove_failability.py <manifest.json> --only B --only 4
    uv run python scripts/prove_failability.py <manifest.json> --no-baseline
    uv run python scripts/prove_failability.py <manifest.json> --output proofs.md
    uv run --directory "$WS" python "$WS/scripts/prove_failability.py" <manifest.json>
        --workspace "$WS" --scratch-root <scratch>/proofs --json <scratch>/proofs.json

``--workspace PATH`` refuses to run unless the repository root this script
resolves from its own location is PATH or lies under it, and holds no ``.git``
(a workspace copy is taken without one), so the shared checkout cannot be
mutated by a command meant for a copy; it also makes a run without observed
provenance an invalid count. ``--json PATH`` writes the machine-readable
record: every site's full mutation text and unified diff, blob ids before,
mutated and after, both runs' exit codes, failing and erroring ids, crash
lines, provenance and wall time, the declared and observed sets, and the
verdict.

Exit codes: ``0`` every entry proved, no boundary weakly pinned, every declared
``expect_failing`` met, and no collection or setup error; ``1`` at least one
entry is weakly pinned, misses its declared ``expect_failing``, carries a
collection/setup error or a pytest exit code outside ``{0, 1}`` (so its count is
not a valid count), or its anchor did not match exactly once, or the manifest is
unusable, or ``--output`` was asked for without a baseline, or ``--workspace``
refused the root; ``3`` a restore could not be proved (the tree may still hold a
mutation - read the marker file the run leaves behind; the partial report is
still written to ``--output`` and ``--json``).
"""

from __future__ import annotations

import argparse
import dataclasses
import difflib
import filecmp
import fnmatch
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from itertools import takewhile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCRATCH_DIRECTORY_NAME = "failability-proofs"
PRISTINE_DIRECTORY_NAME = "pristine"
ACTIVE_MARKER_NAME = "ACTIVE-MUTATION.json"
RESTORE_FAILED_MARKER_NAME = "RESTORE-FAILED.json"
# ``--no-cov`` is mandatory: pytest.ini's addopts turn coverage on, and coverage
# gating belongs to the full-suite run, not to this tool. ``--color=no`` and
# ``-p no:cacheprovider`` keep the captured output parseable and keep the run
# from writing cache state into the repo. ``--tb=line`` puts each failing row's
# crash line (``path:line: message``) in the raw log beside the probe's
# per-row record of the same line.
PYTEST_COMMAND = (
    "uv",
    "run",
    "pytest",
    "--no-cov",
    "--color=no",
    "-p",
    "no:cacheprovider",
    "--tb=line",
    "-q",
    "-rfE",
)
PACKAGE_NAME = "django_strawberry_framework"
PROBE_DIRECTORY_NAME = "probe"
RUNS_DIRECTORY_NAME = "runs"
PROBE_MODULE_NAME = "prove_failability_probe"
PROBE_OUTPUT_ENV = "PROVE_FAILABILITY_PROBE_OUTPUT"
PROBE_PACKAGE_ENV = "PROVE_FAILABILITY_PROBE_PACKAGE"
JSON_SCHEMA_VERSION = 1
# The plugin every run loads with ``-p``. It runs inside the pytest process (and
# inside every xdist worker), which is the only place that can say which package
# the tests imported: a sibling ``python -c`` resolves ``sys.path`` differently
# and has printed the scratch copy while pytest imported the shared checkout.
# Row outcomes are recorded only by the process that reports them (the xdist
# controller, or the single process without xdist), so no row is counted twice.
PROBE_SOURCE = '''"""pytest plugin written by scripts/prove_failability.py; records what the run saw."""

import importlib
import json
import os
import sys

_CONFIGS = []


def _is_worker():
    return bool(_CONFIGS) and hasattr(_CONFIGS[0], "workerinput")


def _emit(record):
    path = os.environ.get("PROVE_FAILABILITY_PROBE_OUTPUT")
    if not path:
        return
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\\n")


def _crash(report):
    longrepr = report.longrepr
    crash = getattr(longrepr, "reprcrash", None)
    if crash is not None:
        return f"{crash.path}:{crash.lineno}: {crash.message}"
    if isinstance(longrepr, tuple) and len(longrepr) == 3:
        return f"{longrepr[0]}:{longrepr[1]}: {longrepr[2]}"
    lines = str(longrepr).strip().splitlines()
    return lines[-1] if lines else ""


def pytest_configure(config):
    _CONFIGS.append(config)


def pytest_runtest_logreport(report):
    if _is_worker() or not report.failed:
        return
    kind = "failed" if report.when == "call" else "error"
    _emit({"kind": kind, "nodeid": report.nodeid, "when": report.when, "crash": _crash(report)})


def pytest_collectreport(report):
    if _is_worker() or not report.failed:
        return
    _emit({"kind": "error", "nodeid": report.nodeid, "when": "collect", "crash": _crash(report)})


def pytest_sessionfinish(session):
    record = {
        "kind": "provenance",
        "role": "worker" if _is_worker() else "controller",
        "executable": sys.executable,
        "cwd": os.getcwd(),
        "rootpath": str(session.config.rootpath),
    }
    package = os.environ.get("PROVE_FAILABILITY_PROBE_PACKAGE", "")
    module = sys.modules.get(package)
    record["package_imported_by_run"] = module is not None
    if module is None and package:
        try:
            module = importlib.import_module(package)
        except Exception as error:
            record["error"] = f"import {package}: {error!r}"
    record["package_file"] = getattr(module, "__file__", None)
    try:
        from django.conf import settings

        record["databases"] = {
            alias: str(options.get("NAME")) for alias, options in settings.DATABASES.items()
        }
    except Exception as error:
        record["error"] = f"{record.get('error', '')} databases: {error!r}".strip()
    _emit(record)
'''
FORBIDDEN_SCOPE_FRAGMENT = "--cov"
# Fragments that stop the run early. A truncated run reports a count for a row set
# that is not the scope it names, with a countable exit code and every recorded field
# present. Measured against a real 9-row scope: ``-n0 -x`` grades a 4-row boundary as
# 1 row (**WEAKLY PINNED**) and ``-n0 --maxfail=3`` grades it 3 rows (inside Worker
# 3's re-run floor), both at exit 1, and both report "pre-existing failing rows
# excluded: 1 / 3" where 5 rows were already failing. Because the fragment travels in
# the recorded scope, Worker 3's independent re-run reproduces the same wrong number -
# two measurements agreeing is exactly what the set-difference design reads as
# corroboration, so this is the one corruption that machinery cannot catch. Under this
# repo's default ``-n auto`` addopts the same fragments interrupt the session (exit 2)
# and are already an invalid count; refusing them closes the sequential case, which
# ``pytest.ini`` documents as supported ("Pass ``-n0`` ... for a fast single-test run").
TRUNCATING_SCOPE_OPTIONS = ("--exitfirst", "--maxfail")
TRUNCATING_SHORT_FLAG = "x"
# Short flags that take no value, used only to find where a bundled single-dash
# argument stops being flags and starts being a value: ``-xvs`` is three flags, while
# ``-rfE`` and ``-ktest_expiry`` glue a value onto a value-taking flag. Scanning the
# whole argument for ``x`` would refuse the latter, so the walk stops at the first
# letter that is not listed here and can therefore only ever under-refuse.
VALUELESS_SHORT_FLAGS = "xvqsl"
WEAKLY_PINNED_MAXIMUM = 1
MANDATORY_RERUN_FLOOR = 3
# Which of the two readings of a zero-row result applies is a judgement about the
# harness, not a measurement, so the tool emits the slot and refuses to guess.
ZERO_ROW_PLACEHOLDER = (
    "why 0: <fill in - weakly pinned (nothing pins the boundary; the fix is more or "
    "better-targeted rows) or a harness-impossible interleaving (the harness cannot exhibit "
    "the failure at all; assert the invariant at the production call site and record the "
    "harness limitation)>"
)
# A zero produced by a run that could not measure is not a zero-row result, so it
# must NOT be handed the slot above: both of that slot's readings are readings of
# a measurement, and filling it in with "harness-impossible interleaving" is
# exactly how a mistyped scope becomes an accepted boundary.
NO_COUNT_TO_EXPLAIN = (
    "no `why 0` is asked for here: this run produced no valid count, so there is no zero-row "
    "result to explain. Weakly pinned and harness-impossible are both readings of a "
    "MEASUREMENT and neither applies to a measurement that was never obtained - fix the run "
    "named above and re-measure"
)
# pytest's exit codes. Only 0 (everything passed) and 1 (tests failed) mean "the
# scope ran and reported on itself"; 2, 3, 4 and 5 all emit zero ``FAILED`` lines
# for reasons that have nothing to do with the mutated boundary, which reads
# identically to "nothing pins it". The exit code is therefore a validity channel
# and not a diagnostic, and is routed through ``invalid_count_reason``.
COUNTABLE_RETURN_CODES = frozenset({0, 1})
NO_TESTS_COLLECTED_RETURN_CODE = 5
RETURN_CODE_READINGS = {
    2: "pytest was interrupted",
    3: "pytest hit an internal error",
    4: "pytest rejected the invocation as a usage error",
    NO_TESTS_COLLECTED_RETURN_CODE: "pytest collected no test at all",
}
ENTRY_KEYS = frozenset(
    {
        "label",
        "target",
        "anchor",
        "replacement",
        "delete",
        "mutation",
        "scope",
        "expect_failing",
        "pre_image",
        "reverse_patch",
        "sites",
    },
)
SITE_KEYS = frozenset(
    {
        "target",
        "anchor",
        "replacement",
        "delete",
        "pre_image",
        "reverse_patch",
    },
)
MANIFEST_KEYS = frozenset({"proofs", "scratch_root"})
ANCHOR_KIND = "anchor"
PRE_IMAGE_KIND = "pre_image"
REVERSE_PATCH_KIND = "reverse_patch"
HUNK_HEADER = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")
NO_NEWLINE_MARKER = "\\ No newline at end of file"


class ManifestError(Exception):
    """The manifest is not a usable set of proof entries."""


class RestoreProofError(Exception):
    """A mutated file could not be restored, or the restore could not be proved."""


class SiteError(Exception):
    """A mutation site cannot be applied to the file as it stands; nothing was written."""


PatchLine = tuple[str, bool]


@dataclass(frozen=True)
class PatchHunk:
    """One unified-diff hunk: both sides as ``(content, ends_with_newline)`` lines."""

    new_start: int
    old_lines: tuple[PatchLine, ...]
    new_lines: tuple[PatchLine, ...]


@dataclass(frozen=True)
class MutationSite:
    """One place an entry mutates: an anchor replacement, a pre-image, or a reverse patch."""

    target: Path
    kind: str = ANCHOR_KIND
    anchor: str = ""
    replacement: str | None = None
    source: Path | None = None
    hunks: tuple[PatchHunk, ...] = ()

    @property
    def relative_target(self) -> str:
        """Return the target path relative to the repository root."""
        return self.target.relative_to(REPO_ROOT).as_posix()

    def describe(self) -> str:
        """Return a one-line rendering of what this site writes."""
        if self.kind == PRE_IMAGE_KIND:
            return f"`{self.relative_target}` replaced wholesale by the pre-image `{self.source}`"
        if self.kind == REVERSE_PATCH_KIND:
            return (
                f"`{self.relative_target}`: {len(self.hunks)} hunk(s) of `{self.source}` "
                "reverted (post-image -> pre-image)"
            )
        return _describe_mutation(self.anchor, self.replacement)

    def apply(self, text: str) -> str:
        """Return ``text`` with this site's mutation applied, or raise :class:`SiteError`."""
        if self.kind == PRE_IMAGE_KIND:
            assert self.source is not None
            image = self.source.read_bytes().decode("utf-8")
            if image == text:
                raise SiteError(
                    f"the pre-image {self.source} is identical to {self.relative_target} as it "
                    "stands, so it would mutate nothing",
                )
            return image
        if self.kind == REVERSE_PATCH_KIND:
            return _reverse_hunks(text, self.hunks, self.relative_target)
        occurrences = text.count(self.anchor)
        if occurrences != 1:
            raise SiteError(
                f"anchor matched {occurrences} times (must match exactly once); "
                "no mutation was applied",
            )
        return text.replace(self.anchor, "" if self.replacement is None else self.replacement, 1)


@dataclass(frozen=True)
class ProofEntry:
    """One boundary's proof: where to mutate, how, and what to run.

    ``manifest_position`` is the entry's 1-based position in the manifest it was
    parsed from, and is what the report's ``#`` column shows: under ``--only``
    the rows then carry their manifest positions instead of sequence numbers, so
    a one-row table drawn from a twenty-entry manifest cannot read as entry 1 of
    1. ``0`` means "not from a manifest" and falls back to the sequence number.

    ``mutation`` is always *derived* from ``anchor`` and ``replacement`` - the
    bytes this entry actually wrote. ``prose`` is the manifest's optional
    free-text description, which is the builder's claim about those bytes and is
    only ever rendered *beside* them (see :attr:`mutation_applied`).

    ``sites`` holds every place the entry mutates; empty means the single
    anchor site spelled by ``target``/``anchor``/``replacement``, which is how
    the original manifest shape and a hand-built entry are read.
    ``expect_failing`` is the declared failing set, or ``None`` for row-count
    grading.
    """

    label: str
    target: Path
    anchor: str
    replacement: str | None
    mutation: str
    scope: tuple[str, ...]
    manifest_position: int = 0
    prose: str = ""
    sites: tuple[MutationSite, ...] = ()
    expect_failing: tuple[str, ...] | None = None

    @property
    def mutation_sites(self) -> tuple[MutationSite, ...]:
        """Return every site this entry mutates, in application order."""
        if self.sites:
            return self.sites
        return (MutationSite(self.target, ANCHOR_KIND, self.anchor, self.replacement),)

    @property
    def targets(self) -> tuple[Path, ...]:
        """Return each distinct mutated file once, in first-mutation order."""
        return tuple(dict.fromkeys(site.target for site in self.mutation_sites))

    @property
    def relative_target(self) -> str:
        """Return the target path relative to the repository root."""
        return self.target.relative_to(REPO_ROOT).as_posix()

    @property
    def relative_targets(self) -> tuple[str, ...]:
        """Return every mutated file relative to the repository root."""
        return tuple(target.relative_to(REPO_ROOT).as_posix() for target in self.targets)

    @property
    def scope_as_run(self) -> str:
        """Return the exact pytest invocation this entry runs."""
        return " ".join((*PYTEST_COMMAND, *self.scope))

    @property
    def mutation_applied(self) -> str:
        """Return the mutation as the record must show it: derived bytes, then any prose.

        ``BUILD.md`` "What gets recorded" requires the **exact mutation
        applied** and rules that "a mutation must remove the boundary, not
        merely perturb code near it". The manifest's free-text ``mutation`` was
        rendered *instead of* the derived anchor-to-replacement text, so an entry
        claiming "the Host-validation gate deleted" printed exactly that while
        its anchor may only have touched an adjacent line - and the report
        carried no rendering of the real bytes, leaving no reader able to audit
        the claim against what was written. The derived text is therefore never
        replaceable; prose may only accompany it.
        """
        if not self.prose:
            return self.mutation
        return f"{self.mutation} - builder's description (unverified prose): {self.prose}"


@dataclass(frozen=True)
class Provenance:
    """What one pytest process (controller, worker, or the only one) observed about itself."""

    role: str
    package_file: str | None
    package_imported_by_run: bool
    databases: tuple[tuple[str, str], ...]
    executable: str
    cwd: str
    rootpath: str
    error: str | None = None

    def describe(self) -> str:
        """Return the one-line provenance rendering the record carries."""
        databases = ", ".join(f"{alias}=`{name}`" for alias, name in self.databases) or "none"
        text = (
            f"{self.role}: package `__file__` `{self.package_file}` "
            f"({'imported by the run' if self.package_imported_by_run else 'imported by probe'}); "
            f"database NAME {databases}; python `{self.executable}`; cwd `{self.cwd}`"
        )
        if self.error:
            text += f"; probe error: {self.error}"
        return text


@dataclass(frozen=True)
class RunOutcome:
    """What one focused pytest run reported.

    ``crash_lines`` maps each failing or erroring node id to its crash line, and
    ``provenance`` is one record per pytest process, both observed by the probe
    plugin inside the run; ``log_path`` holds the raw stdout and stderr.
    """

    failed_node_ids: tuple[str, ...]
    error_node_ids: tuple[str, ...]
    summary: str
    return_code: int
    crash_lines: tuple[tuple[str, str], ...] = ()
    provenance: tuple[Provenance, ...] = ()
    wall_seconds: float | None = None
    log_path: str | None = None

    def crash_line(self, node_id: str) -> str | None:
        """Return the crash line the probe recorded for ``node_id``, if any."""
        return dict(self.crash_lines).get(node_id)

    @property
    def is_countable(self) -> bool:
        """Whether this run's ``FAILED`` lines are a row count at all.

        A run that collected nothing (exit 5), was interrupted (2), errored
        internally (3) or was refused as a usage error (4) emits zero ``FAILED``
        lines. That output is textually identical to a clean run of a boundary
        nothing pins, and the exit code is the only thing that tells the two
        apart - so it is read here rather than merely captured.
        """
        return self.return_code in COUNTABLE_RETURN_CODES


@dataclass(frozen=True)
class FileRecord:
    """One mutated file's identity before, during and after the mutation.

    Blob ids are ``git hash-object`` ids computed from the bytes, so a reader
    can compare them with ``git ls-tree``/``git hash-object`` output directly.
    """

    relative_target: str
    pristine: str
    blob_before: str
    blob_mutated: str
    blob_after: str
    sha256_before: str
    sha256_after: str
    diff: str
    restore_proof: str


@dataclass(frozen=True)
class Expectation:
    """How the attributable failing set compares with a declared ``expect_failing``."""

    declared: tuple[str, ...]
    missing: tuple[str, ...]
    unexpected: tuple[str, ...]
    missing_but_failing_at_baseline: tuple[str, ...]

    @property
    def is_met(self) -> bool:
        """Whether every declared pattern matched and no undeclared row failed."""
        return not self.missing and not self.unexpected


def _pattern_matches(pattern: str, node_id: str) -> bool:
    """Return whether an ``expect_failing`` pattern names ``node_id``.

    Equality first: a parametrized id carries ``[...]``, which ``fnmatch`` would
    read as a character class and fail to match literally.
    """
    return pattern == node_id or fnmatch.fnmatchcase(node_id, pattern)


@dataclass(frozen=True)
class ProofResult:
    """One entry's full record: the run, the restore proof, or why neither happened.

    ``files`` records every mutated file's blob ids and diff. With
    ``provenance_required`` (``--workspace``) a run the probe observed nothing
    about is an invalid count.
    """

    entry: ProofEntry
    outcome: RunOutcome | None
    restore_proof: str
    failure: str | None
    baseline: RunOutcome | None = None
    pre_existing_node_ids: tuple[str, ...] = ()
    files: tuple[FileRecord, ...] = ()
    provenance_required: bool = False

    @property
    def expectation(self) -> Expectation | None:
        """Return the declared-set comparison, or ``None`` when nothing was declared or run."""
        declared = self.entry.expect_failing
        if declared is None or self.outcome is None:
            return None
        observed = self.attributable_node_ids
        missing = tuple(
            pattern
            for pattern in declared
            if not any(_pattern_matches(pattern, node) for node in observed)
        )
        return Expectation(
            declared=declared,
            missing=missing,
            unexpected=tuple(
                node
                for node in observed
                if not any(_pattern_matches(pattern, node) for pattern in declared)
            ),
            missing_but_failing_at_baseline=tuple(
                pattern
                for pattern in missing
                if any(_pattern_matches(pattern, node) for node in self.pre_existing_node_ids)
            ),
        )

    @property
    def is_expectation_unmet(self) -> bool:
        """Whether a VALID count contradicts the declared ``expect_failing`` set."""
        if self.failure is not None or self.invalid_count_reason is not None:
            return False
        expectation = self.expectation
        return expectation is not None and not expectation.is_met

    @property
    def failed_count(self) -> int:
        """Return the number of failing rows attributable to the mutation."""
        if self.outcome is None:
            return 0
        return len(self.attributable_node_ids)

    @property
    def attributable_node_ids(self) -> tuple[str, ...]:
        """Return failing node ids minus any that were already failing at baseline."""
        if self.outcome is None:
            return ()
        pre_existing = set(self.pre_existing_node_ids)
        return tuple(node for node in self.outcome.failed_node_ids if node not in pre_existing)

    @property
    def error_count(self) -> int:
        """Return the collection/setup error count across both runs of this scope."""
        total = 0
        if self.outcome is not None:
            total += len(self.outcome.error_node_ids)
        if self.baseline is not None:
            total += len(self.baseline.error_node_ids)
        return total

    @property
    def invalid_count_reasons(self) -> tuple[str, ...]:
        """Return every reason this entry's row count is not a count at all.

        Rows that never ran cannot fail, so a run carrying collection or setup
        errors - or one that never collected, was interrupted, blew up
        internally, or was refused as a usage error - reports few or **0**
        failures for a boundary that may have been removed catastrophically. The
        direction of the corruption is fail-open in every one of those cases.
        ``BUILD.md`` "What gets recorded" therefore rules such a proof out
        entirely ("not a valid count") rather than footnoting it, which is why
        this is a verdict and an exit status and not a note.

        Both runs are judged. The pre-mutation run is the reference the mutant's
        failure set is differenced against, so a baseline that could not run is
        no reference to difference against.
        """
        if self.outcome is None:
            return ()
        reasons: list[str] = []
        parts = []
        if self.outcome.error_node_ids:
            parts.append(f"{len(self.outcome.error_node_ids)} in the mutant run")
        if self.baseline is not None and self.baseline.error_node_ids:
            parts.append(f"{len(self.baseline.error_node_ids)} in the baseline run")
        if parts:
            reasons.append(
                f"{self.error_count} collection/setup error(s) ({', '.join(parts)}); rows that "
                "never ran cannot fail, so this is not a valid count: resolve the errors and "
                "re-run, or the scope was wrong",
            )
        uncountable = [
            (position, run.return_code)
            for position, run in (
                ("the mutant run", self.outcome),
                ("the baseline run", self.baseline),
            )
            if run is not None and not run.is_countable
        ]
        codes = {code for _, code in uncountable}
        if len(uncountable) == 2 and len(codes) == 1:
            # Both runs failed the same way - a mistyped scope collects nothing in
            # either - so say it once instead of printing the same paragraph twice
            # under two headings, which is how a reader learns to skim a verdict.
            shared_code = uncountable[0][1]
            reasons.append(
                _uncountable_run_reason("both the mutant and the baseline run", shared_code),
            )
        else:
            reasons.extend(
                _uncountable_run_reason(position, code) for position, code in uncountable
            )
        for position, run in (
            ("the mutant run", self.outcome),
            ("the baseline run", self.baseline),
        ):
            if run is not None:
                reasons.extend(self._provenance_reasons(position, run))
        return tuple(reasons)

    def _provenance_reasons(self, position: str, run: RunOutcome) -> list[str]:
        """Return why ``run`` did not measure the tree this script mutated, if it did not."""
        reasons = []
        foreign = sorted(
            {
                record.package_file
                for record in run.provenance
                if record.package_file is not None
                and not _is_within(Path(record.package_file).resolve(), REPO_ROOT)
            },
        )
        if foreign:
            reasons.append(
                f"{position} imported {PACKAGE_NAME} from {', '.join(foreign)}, outside the tree "
                f"under proof {REPO_ROOT}, so it measured another checkout and not the mutation",
            )
        if self.provenance_required and not any(record.package_file for record in run.provenance):
            reasons.append(
                f"{position} reported no package `__file__` from inside pytest, and --workspace "
                "requires the record to show which tree the run imported",
            )
        return reasons

    @property
    def invalid_count_reason(self) -> str | None:
        """Return every invalidating reason as one sentence, or ``None`` if the count holds."""
        return "; and ".join(self.invalid_count_reasons) or None

    @property
    def is_weakly_pinned(self) -> bool:
        """Whether a VALID count shows removing this boundary failed 0 or 1 rows.

        An invalid count is not a small count. "0 rows failed" and "no count was
        obtainable" prescribe opposite actions - more or better-targeted rows,
        versus fix the run - so an uncountable run must not additionally claim
        the boundary is weakly pinned. Nothing is softened by this: an invalid
        count fails the exit status on its own.
        """
        if self.failure is not None or self.outcome is None:
            return False
        if self.invalid_count_reason is not None or self.entry.expect_failing is not None:
            return False
        return self.failed_count <= WEAKLY_PINNED_MAXIMUM

    @property
    def is_inside_rerun_floor(self) -> bool:
        """Whether a VALID count puts this boundary inside Worker 3's mandatory re-run floor.

        A declared ``expect_failing`` replaces the row-count grading, so neither
        threshold applies to it.
        """
        if self.failure is not None or self.outcome is None:
            return False
        if self.invalid_count_reason is not None or self.entry.expect_failing is not None:
            return False
        return self.failed_count <= MANDATORY_RERUN_FLOOR


def _uncountable_run_reason(position: str, code: int) -> str:
    """Return why a run's pytest exit code means its ``FAILED`` lines are not a count.

    Exit 5 gets its own wording deliberately: "your scope matched no tests" is a
    different operator action - correct the scope - from "your run blew up", and
    the two must not collapse into one generic sentence that leaves the reader
    guessing which of them happened.
    """
    reading = RETURN_CODE_READINGS.get(code, "pytest exited outside its documented code set")
    if code == NO_TESTS_COLLECTED_RETURN_CODE:
        consequence = (
            "the scope matched no test at all, so what is reported below measures a mistyped "
            "path or a node id that no longer exists and NOT a boundary the suite fails to "
            "pin; correct the scope and re-run"
        )
    else:
        consequence = (
            "the run did not complete, so rows that never ran cannot fail and this is not a "
            "valid count; fix the run and re-run"
        )
    if "baseline" in position:
        consequence += (
            " (and the pre-mutation run is the reference the mutant's failure set is differenced "
            "against, so this invalidates the difference as well)"
        )
    return f"{position} exited {code} ({reading}); {consequence}"


def _join_lines(value: object, field: str, label: str) -> str:
    """Return ``value`` as text, joining a list of lines with newlines."""
    if isinstance(value, str):
        return value
    if isinstance(value, list) and all(isinstance(line, str) for line in value):
        return "\n".join(value)
    raise ManifestError(f"{label}: {field!r} must be a string or a list of strings")


def _resolve_target(raw_target: object, label: str) -> Path:
    """Return the mutation target, refusing anything outside the repository."""
    if not isinstance(raw_target, str) or not raw_target:
        raise ManifestError(f"{label}: 'target' must be a non-empty string")
    candidate = Path(raw_target)
    resolved = (candidate if candidate.is_absolute() else REPO_ROOT / candidate).resolve()
    if resolved != REPO_ROOT and REPO_ROOT not in resolved.parents:
        raise ManifestError(f"{label}: target {resolved} is outside the repository {REPO_ROOT}")
    if not resolved.is_file():
        raise ManifestError(f"{label}: target {resolved} is not a file")
    return resolved


def _claimed_label_path(label: str) -> str | None:
    """Return the path a label's leading segment claims, or ``None`` when it claims none.

    ``AGENTS.md`` "Source references in docs and code comments" gives a label three
    shapes, two of which lead with a repo-relative path:

    * ``path::QualifiedName`` and ``path::QualifiedName #"unique substring"`` - the
      claim is everything before the first ``::``.
    * ``path #"unique substring"`` - the claim is everything before the first ``#``.
    * a bare symbol (``GraphQLView.dispatch``), a bare symbol with a substring
      pointer, or free prose - no path claim at all.

    A leading segment counts as a claim when it contains ``/`` (nothing but a path is
    spelled that way, so a typo'd path is still a claim and still checkable) or when it
    names an existing file - the same is-a-file test :func:`_resolve_target` applies, so
    a top-level ``conftest.py::fixture`` is checked while ``Mixin.method`` is not.
    Absence of a claim is never an error; only disagreement with the target is.
    """
    if "::" in label:
        head = label.split("::", 1)[0].strip()
    elif "#" in label:
        head = label.split("#", 1)[0].strip()
    else:
        return None
    if not head:
        return None
    if "/" in head:
        return head
    return head if _repo_relative(head).is_file() else None


def _repo_relative(raw_path: str) -> Path:
    """Return ``raw_path`` interpreted against the repository root unless it is absolute."""
    candidate = Path(raw_path)
    return candidate if candidate.is_absolute() else REPO_ROOT / candidate


def _is_within(path: Path, root: Path) -> bool:
    """Return whether ``path`` is ``root`` or lies under it (both already resolved)."""
    return path == root or root in path.parents


def _refuse_label_targets_disagreement(label: str, targets: Sequence[Path]) -> None:
    """Refuse a label whose leading path names none of an entry's mutated files."""
    if len(targets) == 1:
        _refuse_label_target_disagreement(label, targets[0])
        return
    claimed = _claimed_label_path(label)
    if claimed is None or _repo_relative(claimed).resolve() in targets:
        return
    named = ", ".join(repr(target.relative_to(REPO_ROOT).as_posix()) for target in targets)
    raise ManifestError(
        f"{label!r}: the label's leading path {claimed!r} is not the mutation target of any "
        f"site ({named}). Correct whichever is wrong, or drop the path prefix and label the "
        "entry by bare symbol.",
    )


def _refuse_label_target_disagreement(label: str, target: Path) -> None:
    """Refuse a label whose leading path names a file other than the mutated one.

    The label is free text and the target is separately resolved, so nothing tied the
    two together: an entry labelled ``package/views.py::Mixin.method`` with
    ``"target": "tests/test_views.py"`` produced a record claiming a production boundary
    had been removed while the mutation landed in a test file. Every other file identity
    in the record is derived from the target, and the label is the one the reader
    believes, so the disagreement is fail-open in the worst possible direction.
    """
    claimed = _claimed_label_path(label)
    if claimed is None or _repo_relative(claimed).resolve() == target:
        return
    raise ManifestError(
        f"{label!r}: the label's leading path {claimed!r} is not the mutation target "
        f"{target.relative_to(REPO_ROOT).as_posix()!r}. The label is what a reader of the "
        "record takes for the file whose boundary was removed, so a label naming one file "
        "while the bytes land in another is a false record. Correct whichever is wrong, or "
        "drop the path prefix and label the entry by bare symbol.",
    )


def _refuse_unusable_scope_argument(argument: str, label: str) -> None:
    """Refuse a scope argument that turns coverage on or truncates the row set mid-run."""
    if FORBIDDEN_SCOPE_FRAGMENT in argument:
        raise ManifestError(
            f"{label}: {argument!r} is forbidden - proofs run with --no-cov only",
        )
    bundled_flags = ""
    if argument.startswith("-") and not argument.startswith("--"):
        bundled_flags = "".join(
            takewhile(lambda letter: letter in VALUELESS_SHORT_FLAGS, argument[1:]),
        )
    if TRUNCATING_SHORT_FLAG in bundled_flags or argument.startswith(TRUNCATING_SCOPE_OPTIONS):
        raise ManifestError(
            f"{label}: {argument!r} is forbidden - it stops the run early, so the rows after "
            "the cut never run and cannot fail, and the count that is recorded is a count of a "
            "different row set than the scope it names. The cut also falls in a different place "
            "in the unmutated and the mutated run, which is the one difference the two-run set "
            "difference is there to measure. Give the whole scope and let it finish.",
        )


def _resolve_scratch_root(raw_root: str | None) -> Path:
    """Return the scratch root, refusing any location inside the repository."""
    if raw_root:
        resolved = Path(raw_root).expanduser().resolve()
    else:
        resolved = Path(tempfile.gettempdir()).resolve() / DEFAULT_SCRATCH_DIRECTORY_NAME
    if resolved == REPO_ROOT or REPO_ROOT in resolved.parents:
        raise ManifestError(
            f"scratch root {resolved} is inside the repository {REPO_ROOT}; "
            "pristine copies must live outside the tree under proof",
        )
    (resolved / PRISTINE_DIRECTORY_NAME).mkdir(parents=True, exist_ok=True)
    return resolved


def _resolve_input_file(
    raw_value: object,
    field: str,
    label: str,
    base: Path,
) -> Path:
    """Return a ``pre_image``/``reverse_patch`` input file, relative paths against ``base``."""
    if not isinstance(raw_value, str) or not raw_value:
        raise ManifestError(f"{label}: {field!r} must be a non-empty path string")
    candidate = Path(raw_value).expanduser()
    resolved = (candidate if candidate.is_absolute() else base / candidate).resolve()
    if not resolved.is_file():
        raise ManifestError(f"{label}: {field} {resolved} is not a file")
    return resolved


def _parse_site(
    raw: dict,
    label: str,
    base: Path,
    *,
    entry_label: str | None = None,
) -> tuple[MutationSite, ...]:
    """Return the site(s) one manifest mapping spells; a reverse patch may spell several.

    ``entry_label`` is checked against the resolved target as soon as it is
    known, so the original single-site shape refuses in its original order.
    """
    kinds = [key for key in (ANCHOR_KIND, PRE_IMAGE_KIND, REVERSE_PATCH_KIND) if key in raw]
    if len(kinds) > 1:
        raise ManifestError(
            f"{label}: give exactly one of 'anchor', 'pre_image' or 'reverse_patch', not {kinds}",
        )
    if kinds and kinds[0] != ANCHOR_KIND:
        stray = sorted({"replacement", "delete"} & set(raw))
        if stray:
            raise ManifestError(
                f"{label}: {stray} belong to an anchor site; a {kinds[0]!r} site takes only "
                f"'target' and {kinds[0]!r}",
            )
    if PRE_IMAGE_KIND in raw:
        target = _resolve_target(raw.get("target"), label)
        if entry_label is not None:
            _refuse_label_target_disagreement(entry_label, target)
        source = _resolve_input_file(raw[PRE_IMAGE_KIND], PRE_IMAGE_KIND, label, base)
        return (MutationSite(target, PRE_IMAGE_KIND, source=source),)
    if REVERSE_PATCH_KIND in raw:
        source = _resolve_input_file(raw[REVERSE_PATCH_KIND], REVERSE_PATCH_KIND, label, base)
        sections = _parse_unified_diff(source.read_bytes().decode("utf-8"), f"{label}: {source}")
        if "target" not in raw:
            return tuple(
                MutationSite(
                    _resolve_target(path, label),
                    REVERSE_PATCH_KIND,
                    source=source,
                    hunks=hunks,
                )
                for path, hunks in sections.items()
            )
        target = _resolve_target(raw.get("target"), label)
        if entry_label is not None:
            _refuse_label_target_disagreement(entry_label, target)
        relative = target.relative_to(REPO_ROOT).as_posix()
        if relative not in sections:
            raise ManifestError(
                f"{label}: {source} has no hunk for {relative!r}; it covers {sorted(sections)}",
            )
        return (MutationSite(target, REVERSE_PATCH_KIND, source=source, hunks=sections[relative]),)
    target = _resolve_target(raw.get("target"), label)
    if entry_label is not None:
        _refuse_label_target_disagreement(entry_label, target)
    if "anchor" not in raw:
        raise ManifestError(f"{label}: 'anchor' is required")
    anchor = _join_lines(raw["anchor"], "anchor", label)
    if not anchor:
        raise ManifestError(f"{label}: 'anchor' must not be empty")
    deletes = bool(raw.get("delete", False))
    if deletes and "replacement" in raw:
        raise ManifestError(f"{label}: give either 'replacement' or 'delete', not both")
    if not deletes and "replacement" not in raw:
        raise ManifestError(f"{label}: give either 'replacement' or 'delete': true")
    replacement = None if deletes else _join_lines(raw["replacement"], "replacement", label)
    return (MutationSite(target, ANCHOR_KIND, anchor, replacement),)


def _parse_sites(raw_entry: dict, label: str, base: Path) -> tuple[MutationSite, ...]:
    """Return every site an entry mutates, refusing a target two sites cannot share."""
    if "sites" not in raw_entry:
        sites = _parse_site(raw_entry, label, base, entry_label=label)
    else:
        clashing = sorted(set(raw_entry) & SITE_KEYS)
        if clashing:
            raise ManifestError(
                f"{label}: an entry with 'sites' carries no top-level {clashing}; move them "
                "into a site",
            )
        raw_sites = raw_entry["sites"]
        if not isinstance(raw_sites, list) or not raw_sites:
            raise ManifestError(f"{label}: 'sites' must be a non-empty list of site objects")
        collected: list[MutationSite] = []
        for index, raw_site in enumerate(raw_sites, 1):
            site_label = f"{label}: sites[{index}]"
            if not isinstance(raw_site, dict):
                raise ManifestError(f"{site_label}: each site must be an object")
            unknown = sorted(set(raw_site) - SITE_KEYS)
            if unknown:
                raise ManifestError(
                    f"{site_label}: unknown key(s) {unknown}; expected {sorted(SITE_KEYS)}",
                )
            collected.extend(_parse_site(raw_site, site_label, base))
        sites = tuple(collected)
    for target in dict.fromkeys(site.target for site in sites):
        sharing = [site for site in sites if site.target == target]
        if len(sharing) > 1 and any(site.kind != ANCHOR_KIND for site in sharing):
            raise ManifestError(
                f"{label}: {target.relative_to(REPO_ROOT).as_posix()!r} is named by "
                f"{len(sharing)} sites and at least one is a pre-image or reverse patch; a "
                "wholesale or diff-located mutation cannot be ordered against another site on "
                "the same file, so give that file one site",
            )
    return sites


def _parse_entry(raw_entry: object, position: int, base: Path | None = None) -> ProofEntry:
    """Return one validated :class:`ProofEntry` from its manifest mapping.

    ``base`` resolves relative ``pre_image``/``reverse_patch`` paths; it is the
    manifest's directory when read through :func:`load_manifest`.
    """
    label = f"proofs[{position}]"
    if not isinstance(raw_entry, dict):
        raise ManifestError(f"{label}: each proof entry must be an object")
    unknown = sorted(set(raw_entry) - ENTRY_KEYS)
    if unknown:
        raise ManifestError(f"{label}: unknown key(s) {unknown}; expected {sorted(ENTRY_KEYS)}")
    raw_label = raw_entry.get("label")
    if not isinstance(raw_label, str) or not raw_label:
        raise ManifestError(f"{label}: 'label' must be a non-empty string")
    label = raw_label
    sites = _parse_sites(raw_entry, label, base if base is not None else Path.cwd())
    targets = tuple(dict.fromkeys(site.target for site in sites))
    _refuse_label_targets_disagreement(label, targets)
    single_anchor = "sites" not in raw_entry and sites[0].kind == ANCHOR_KIND
    raw_scope = raw_entry.get("scope")
    if not isinstance(raw_scope, list) or not raw_scope:
        raise ManifestError(f"{label}: 'scope' must be a non-empty list of pytest arguments")
    scope = []
    for argument in raw_scope:
        if not isinstance(argument, str) or not argument:
            raise ManifestError(f"{label}: every 'scope' argument must be a non-empty string")
        _refuse_unusable_scope_argument(argument, label)
        scope.append(argument)
    mutation = raw_entry.get("mutation")
    if mutation is not None and not isinstance(mutation, str):
        raise ManifestError(f"{label}: 'mutation' must be a string when given")
    expect_failing = None
    if "expect_failing" in raw_entry:
        raw_expected = raw_entry["expect_failing"]
        if not isinstance(raw_expected, list) or not all(
            isinstance(pattern, str) and pattern for pattern in raw_expected
        ):
            raise ManifestError(
                f"{label}: 'expect_failing' must be a list of non-empty node ids or glob "
                "patterns ([] declares that nothing may fail)",
            )
        expect_failing = tuple(raw_expected)
    first = sites[0]
    if single_anchor:
        derived = _describe_mutation(first.anchor, first.replacement)
    elif len(sites) == 1:
        derived = first.describe()
    else:
        derived = "; ".join(
            f"site {index} `{site.relative_target}`: {site.describe()}"
            for index, site in enumerate(sites, 1)
        )
    return ProofEntry(
        label=label,
        target=first.target,
        anchor=first.anchor,
        replacement=first.replacement,
        # Derived, never taken from the manifest: 'mutation' is prose about the
        # bytes and cannot stand in for the bytes (see ProofEntry.mutation_applied).
        mutation=derived,
        scope=tuple(scope),
        manifest_position=position,
        prose=mutation or "",
        sites=() if single_anchor else sites,
        expect_failing=expect_failing,
    )


def _diff_side_path(raw: str) -> str:
    """Return the path of a ``---``/``+++`` header, without any timestamp suffix."""
    return raw.split("\t", 1)[0].strip()


def _parse_unified_diff(text: str, label: str) -> dict[str, tuple[PatchHunk, ...]]:
    """Return each file section of a unified diff as ``{post-image path: hunks}``.

    ``a/``/``b/`` prefixes are dropped when both sides carry them (``git diff``'s
    default). Lines outside a file header or hunk (``diff --git``, ``index``,
    mode lines) are ignored; a section that creates or deletes a file, or carries
    no hunk (a binary change), is refused.
    """
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    sections: dict[str, list[PatchHunk]] = {}
    current: list[PatchHunk] | None = None
    index = 0
    while index < len(lines):
        line = lines[index]
        if (
            line.startswith("--- ")
            and index + 1 < len(lines)
            and lines[index + 1].startswith("+++ ")
        ):
            old_path = _diff_side_path(line[4:])
            new_path = _diff_side_path(lines[index + 1][4:])
            if "/dev/null" in (old_path, new_path):
                raise ManifestError(
                    f"{label}: the section {old_path} -> {new_path} creates or deletes a file, "
                    "which a reverse patch does not revert; mutate that file with a pre-image",
                )
            if old_path.startswith("a/") and new_path.startswith("b/"):
                new_path = new_path[2:]
            current = sections.setdefault(new_path, [])
            index += 2
            continue
        match = HUNK_HEADER.match(line)
        if match is None:
            index += 1
            continue
        if current is None:
            raise ManifestError(f"{label}: a hunk header precedes every ---/+++ file header")
        hunk, index = _read_hunk(lines, index, match, label)
        current.append(hunk)
    if not sections:
        raise ManifestError(f"{label}: no ---/+++ file section found; not a unified diff")
    empty = sorted(path for path, hunks in sections.items() if not hunks)
    if empty:
        raise ManifestError(f"{label}: no hunk for {empty} (a binary or mode-only change)")
    return {path: tuple(hunks) for path, hunks in sections.items()}


def _read_hunk(
    lines: Sequence[str],
    index: int,
    match: re.Match[str],
    label: str,
) -> tuple[PatchHunk, int]:
    """Return the hunk whose header ``match`` read at ``lines[index]``, and the next index."""
    old_count = int(match.group(2)) if match.group(2) is not None else 1
    new_count = int(match.group(4)) if match.group(4) is not None else 1
    old: list[list] = []
    new: list[list] = []
    previous: tuple[list, ...] = ()
    index += 1
    while index < len(lines):
        line = lines[index]
        if line.startswith("\\"):
            # "\ No newline at end of file" qualifies the line before it, on its sides.
            for side_line in previous:
                side_line[1] = False
            index += 1
            continue
        if len(old) >= old_count and len(new) >= new_count:
            break
        tag, content = (line[:1], line[1:]) if line else (" ", "")
        if tag == " ":
            previous = ([content, True], [content, True])
            old.append(previous[0])
            new.append(previous[1])
        elif tag == "-":
            previous = ([content, True],)
            old.append(previous[0])
        elif tag == "+":
            previous = ([content, True],)
            new.append(previous[0])
        else:
            raise ManifestError(f"{label}: malformed hunk line {line!r} under {match.group(0)!r}")
        index += 1
    if len(old) != old_count or len(new) != new_count:
        raise ManifestError(
            f"{label}: hunk {match.group(0)!r} is truncated ({len(old)}/{old_count} pre-image, "
            f"{len(new)}/{new_count} post-image lines)",
        )
    return (
        PatchHunk(
            new_start=int(match.group(3)),
            old_lines=tuple((content, newline) for content, newline in old),
            new_lines=tuple((content, newline) for content, newline in new),
        ),
        index,
    )


def _split_patch_lines(text: str) -> list[PatchLine]:
    """Return ``text`` as ``(content, ends_with_newline)`` lines, split on newlines only."""
    if not text:
        return []
    parts = text.split("\n")
    if parts[-1] == "":
        return [(part, True) for part in parts[:-1]]
    return [(part, True) for part in parts[:-1]] + [(parts[-1], False)]


def _reverse_hunks(text: str, hunks: Sequence[PatchHunk], relative_target: str) -> str:
    """Return ``text`` with every hunk's post-image replaced by its pre-image.

    A hunk is located by content: its post-image must occur exactly once, and
    several occurrences are resolved only by the header's own position (shifted
    by the hunks already reverted above it). Anything else raises
    :class:`SiteError` before a byte is written.
    """
    lines = _split_patch_lines(text)
    offset = 0
    for number, hunk in enumerate(hunks, 1):
        post = list(hunk.new_lines)
        expected = (hunk.new_start - 1 if post else hunk.new_start) + offset
        if post:
            starts = [
                start
                for start in range(len(lines) - len(post) + 1)
                if lines[start : start + len(post)] == post
            ]
        else:
            starts = [expected] if 0 <= expected <= len(lines) else []
        found = len(starts)
        if found > 1:
            starts = [start for start in starts if start == expected]
        if len(starts) != 1:
            raise SiteError(
                f"reverse-patch hunk {number} for {relative_target} does not apply: its "
                f"post-image occurs {found} time(s) in the file as it stands"
                + (" and none at the hunk header's position" if found > 1 else "")
                + "; no mutation was applied",
            )
        start = starts[0]
        lines[start : start + len(post)] = list(hunk.old_lines)
        offset += len(hunk.old_lines) - len(post)
    reverted = "".join(content + ("\n" if newline else "") for content, newline in lines)
    if reverted == text:
        raise SiteError(
            f"the reverse patch leaves {relative_target} unchanged, so it would mutate nothing",
        )
    return reverted


def _describe_mutation(anchor: str, replacement: str | None) -> str:
    """Return a one-line rendering of the bytes this mutation replaces, from the bytes."""
    if replacement is None:
        return f"deleted: `{_one_line(anchor)}`"
    return f"`{_one_line(anchor)}` -> `{_one_line(replacement)}`"


def _one_line(text: str, limit: int = 120) -> str:
    """Return ``text`` collapsed to one whitespace-normalized line, truncated."""
    collapsed = " ".join(text.split())
    if len(collapsed) <= limit:
        return collapsed
    return collapsed[: limit - 3] + "..."


def load_manifest(manifest_path: Path) -> tuple[tuple[ProofEntry, ...], str | None]:
    """Return the manifest's proof entries and its optional scratch-root override."""
    try:
        document = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ManifestError(f"{manifest_path}: invalid JSON: {error}") from error
    if not isinstance(document, dict):
        raise ManifestError(f"{manifest_path}: the manifest must be a JSON object")
    unknown = sorted(set(document) - MANIFEST_KEYS)
    if unknown:
        raise ManifestError(f"{manifest_path}: unknown key(s) {unknown}")
    raw_proofs = document.get("proofs")
    if not isinstance(raw_proofs, list) or not raw_proofs:
        raise ManifestError(f"{manifest_path}: 'proofs' must be a non-empty list")
    scratch_root = document.get("scratch_root")
    if scratch_root is not None and not isinstance(scratch_root, str):
        raise ManifestError(f"{manifest_path}: 'scratch_root' must be a string when given")
    base = manifest_path.resolve().parent
    entries = tuple(
        _parse_entry(raw, position, base) for position, raw in enumerate(raw_proofs, 1)
    )
    labels = [entry.label for entry in entries]
    duplicates = sorted({label for label in labels if labels.count(label) > 1})
    if duplicates:
        raise ManifestError(f"{manifest_path}: duplicate label(s) {duplicates}")
    return entries, scratch_root


def select_entries(
    entries: Sequence[ProofEntry],
    selectors: Sequence[str],
) -> tuple[ProofEntry, ...]:
    """Return the entries matching ``selectors`` (1-based index or label substring)."""
    if not selectors:
        return tuple(entries)
    selected: list[ProofEntry] = []
    for selector in selectors:
        if selector.isdigit():
            index = int(selector)
            if not 1 <= index <= len(entries):
                raise ManifestError(f"--only {selector}: no such entry (1-{len(entries)})")
            matches = [entries[index - 1]]
        else:
            matches = [entry for entry in entries if selector in entry.label]
            if not matches:
                raise ManifestError(f"--only {selector!r}: matched no entry label")
        for match in matches:
            if match not in selected:
                selected.append(match)
    return tuple(selected)


@dataclass(frozen=True)
class ManifestSelection:
    """How much of the manifest a run covered, and by what selector it was narrowed.

    This exists because the fail-open is in the *record*, not in the run.
    ``--only`` is a legitimate flag - Worker 3's mandatory independent re-run
    covers a subset by design - but the block it emitted was indistinguishable
    from a complete run's, and Worker 3 audits the record rather than the command
    line. A subset run is honest evidence once it is labelled as a subset, so the
    report carries the selection rather than the tool refusing the flag.
    """

    manifest_total: int
    selectors: tuple[str, ...]
    omitted_labels: tuple[str, ...]

    @property
    def selected_total(self) -> int:
        """Return how many manifest entries this run selected."""
        return self.manifest_total - len(self.omitted_labels)

    @property
    def is_partial(self) -> bool:
        """Whether any manifest entry went unproved (selectors that cover all are not partial)."""
        return bool(self.omitted_labels)

    @property
    def selector_text(self) -> str:
        """Return the ``--only`` selectors as they were given on the command line."""
        if not self.selectors:
            return "no selector"
        return " ".join(f"--only {selector}" for selector in self.selectors)


def describe_selection(
    entries: Sequence[ProofEntry],
    selected: Sequence[ProofEntry],
    selectors: Sequence[str],
) -> ManifestSelection:
    """Return which of ``entries`` the run covers and which it leaves unproved."""
    chosen = {entry.label for entry in selected}
    return ManifestSelection(
        manifest_total=len(entries),
        selectors=tuple(selectors),
        omitted_labels=tuple(entry.label for entry in entries if entry.label not in chosen),
    )


def _sha256(path: Path) -> str:
    """Return the hex SHA-256 of ``path``'s bytes."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_blob_id(data: bytes) -> str:
    """Return the id ``git hash-object`` gives ``data``, computed without invoking git."""
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


@dataclass(frozen=True)
class RunCapture:
    """Where one run's probe plugin lives and writes, and where its raw output is kept."""

    probe_directory: Path
    probe_output: Path
    log_path: Path


def _new_capture(scratch_root: Path, entry: ProofEntry, run_name: str) -> RunCapture:
    """Return a fresh capture for one run, writing the probe plugin into the scratch root."""
    probe_directory = scratch_root / PROBE_DIRECTORY_NAME
    probe_directory.mkdir(parents=True, exist_ok=True)
    probe_file = probe_directory / f"{PROBE_MODULE_NAME}.py"
    if not probe_file.is_file() or probe_file.read_text(encoding="utf-8") != PROBE_SOURCE:
        probe_file.write_text(PROBE_SOURCE, encoding="utf-8")
    runs = scratch_root / RUNS_DIRECTORY_NAME
    runs.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(entry.label.encode("utf-8")).hexdigest()[:8]
    stem = f"{entry.manifest_position:03d}-{digest}-{run_name}"
    capture = RunCapture(
        probe_directory=probe_directory,
        probe_output=runs / f"{stem}.probe.jsonl",
        log_path=runs / f"{stem}.log",
    )
    capture.probe_output.unlink(missing_ok=True)
    return capture


def _read_probe(path: Path) -> tuple[tuple[tuple[str, str], ...], tuple[Provenance, ...]]:
    """Return the crash lines and provenance records the probe plugin wrote."""
    if not path.is_file():
        return (), ()
    crashes: dict[str, str] = {}
    provenance: list[Provenance] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        if not raw_line.strip():
            continue
        record = json.loads(raw_line)
        if record.get("kind") == "provenance":
            observed = Provenance(
                role=str(record.get("role")),
                package_file=record.get("package_file"),
                package_imported_by_run=bool(record.get("package_imported_by_run")),
                databases=tuple(sorted((record.get("databases") or {}).items())),
                executable=str(record.get("executable")),
                cwd=str(record.get("cwd")),
                rootpath=str(record.get("rootpath")),
                error=record.get("error"),
            )
            if observed not in provenance:
                provenance.append(observed)
        else:
            crashes.setdefault(str(record.get("nodeid")), str(record.get("crash")))
    return tuple(crashes.items()), tuple(provenance)


def _parse_run_output(stdout: str) -> tuple[tuple[str, ...], tuple[str, ...], str]:
    """Return failing node ids, erroring node ids, and the summary line."""
    failed: list[str] = []
    errored: list[str] = []
    summary = ""
    for raw_line in stdout.splitlines():
        line = raw_line.rstrip()
        if line.startswith("FAILED "):
            node_id = line[len("FAILED ") :].split(" - ", 1)[0].strip()
            if node_id and node_id not in failed:
                failed.append(node_id)
        elif line.startswith("ERROR "):
            node_id = line[len("ERROR ") :].split(" - ", 1)[0].strip()
            if node_id and node_id not in errored:
                errored.append(node_id)
        elif line.strip():
            summary = line.strip()
    return tuple(failed), tuple(errored), summary


def _run_scope(entry: ProofEntry, capture: RunCapture | None = None) -> RunOutcome:
    """Run one entry's focused pytest scope and return what it reported.

    With ``capture`` the run loads the probe plugin (``-p`` plus ``PYTHONPATH``)
    and its raw stdout and stderr are kept at ``capture.log_path``, headed by the
    exact argv and the environment additions.
    """
    command = [*PYTEST_COMMAND, *entry.scope]
    environment = None
    if capture is not None:
        command = [
            *PYTEST_COMMAND,
            "-p",
            PROBE_MODULE_NAME,
            *entry.scope,
        ]
        inherited = os.environ.get("PYTHONPATH")
        python_path = str(capture.probe_directory)
        if inherited:
            python_path += os.pathsep + inherited
        additions = {
            "PYTHONPATH": python_path,
            PROBE_OUTPUT_ENV: str(capture.probe_output),
            PROBE_PACKAGE_ENV: PACKAGE_NAME,
        }
        environment = {**os.environ, **additions}
    started = time.monotonic()
    completed = subprocess.run(
        command,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
        env=environment,
    )
    wall_seconds = round(time.monotonic() - started, 2)
    failed, errored, summary = _parse_run_output(completed.stdout)
    if not summary:
        summary = (completed.stderr.strip().splitlines() or ["<no output>"])[-1]
    if capture is None:
        return RunOutcome(
            failed_node_ids=failed,
            error_node_ids=errored,
            summary=summary,
            return_code=completed.returncode,
            wall_seconds=wall_seconds,
        )
    header = [f"argv: {json.dumps(command)}", f"cwd: {REPO_ROOT}"]
    header.extend(f"env: {name}={value}" for name, value in additions.items())
    capture.log_path.write_text(
        "\n".join(header)
        + f"\nexit code: {completed.returncode}\n\n--- stdout ---\n{completed.stdout}"
        + f"\n--- stderr ---\n{completed.stderr}",
        encoding="utf-8",
    )
    crash_lines, provenance = _read_probe(capture.probe_output)
    return RunOutcome(
        failed_node_ids=failed,
        error_node_ids=errored,
        summary=summary,
        return_code=completed.returncode,
        crash_lines=crash_lines,
        provenance=provenance,
        wall_seconds=wall_seconds,
        log_path=str(capture.log_path),
    )


def _write_marker(path: Path, payload: dict[str, object]) -> None:
    """Write a scratch marker naming a live mutation or a failed restore."""
    payload = dict(payload, written_at=datetime.now(timezone.utc).isoformat())
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _restore_and_prove(target: Path, pristine: Path) -> str:
    """Restore ``target`` from ``pristine`` and return the byte-comparison proof.

    Every failure mode of the restore itself - the copy raising, the read
    raising, the bytes differing - becomes a :class:`RestoreProofError`, so the
    caller has exactly one exception to treat as "the tree may still be
    mutated" and cannot mistake an ``OSError`` for an ordinary run failure.
    """
    try:
        shutil.copyfile(pristine, target)
        target_digest = _sha256(target)
        pristine_digest = _sha256(pristine)
    except OSError as error:
        raise RestoreProofError(
            f"{target} could not be restored from the pristine copy {pristine}: {error}",
        ) from error
    identical = filecmp.cmp(str(pristine), str(target), shallow=False)
    if not identical or target_digest != pristine_digest:
        raise RestoreProofError(
            f"{target} does NOT match the pristine copy {pristine} after restore: "
            f"sha256 {target_digest} vs {pristine_digest}",
        )
    return (
        f"filecmp.cmp(shallow=False) True; sha256 {target_digest[:16]}... == "
        f"{pristine_digest[:16]}... (vs pre-mutation copy)"
    )


def execute_entry(
    entry: ProofEntry,
    scratch_root: Path,
    *,
    capture_baseline: bool = True,
    anchors_only: bool = False,
    provenance_required: bool = False,
) -> ProofResult:
    """Prove one boundary: plan every site, copy, baseline, mutate, run, restore, compare.

    ``capture_baseline`` defaults to ``True`` because the pre-mutation state of
    the same scope is a mandatory recorded field, not an option: without it the
    attributable count is the raw failure set, and one pre-existing failing row
    silently inflates it.

    Every site is applied in memory before anything is written, so an anchor
    that does not match exactly once, a reverse patch that does not apply, or a
    pre-image identical to the file aborts the entry with nothing mutated. The
    copies are taken before anything is written and every mutated file is
    restored in a ``finally``, so no return path and no exception leaves a
    mutation live. A restore that cannot be proved raises
    :class:`RestoreProofError` rather than being reported as one entry's failure.
    """
    try:
        plan = _plan_files(entry)
    except SiteError as error:
        return ProofResult(
            entry=entry,
            outcome=None,
            restore_proof="not applicable; nothing was mutated",
            failure=str(error),
        )
    if anchors_only:
        return ProofResult(
            entry=entry,
            outcome=None,
            restore_proof="not applicable; --check-anchors-only",
            failure=None,
        )
    pristines: list[Path] = []
    for planned in plan:
        pristine = (
            scratch_root / PRISTINE_DIRECTORY_NAME / _pristine_name_for(entry, planned.target)
        )
        try:
            shutil.copy2(planned.target, pristine)
        except OSError as error:
            # Nothing has been mutated yet, so this is one entry's failure and not a
            # tree emergency - but it must never become "mutate first, copy later".
            return ProofResult(
                entry=entry,
                outcome=None,
                restore_proof="not applicable; nothing was mutated",
                failure=(
                    f"the pre-mutation copy to {pristine} failed ({error}); nothing was mutated"
                ),
            )
        pristines.append(pristine)
    baseline = (
        _run_scope(entry, _new_capture(scratch_root, entry, "baseline"))
        if capture_baseline
        else None
    )
    pre_existing = baseline.failed_node_ids if baseline is not None else ()
    marker = scratch_root / ACTIVE_MARKER_NAME
    _write_marker(marker, _marker_payload(entry, plan, pristines))
    mutated_blobs: dict[Path, str] = {}
    try:
        for planned in plan:
            planned.target.write_bytes(planned.mutated)
            mutated_blobs[planned.target] = git_blob_id(planned.target.read_bytes())
        outcome = _run_scope(entry, _new_capture(scratch_root, entry, "mutant"))
    finally:
        files = _restore_every_file(entry, plan, pristines, mutated_blobs, scratch_root)
        marker.unlink(missing_ok=True)
    return ProofResult(
        entry=entry,
        outcome=outcome,
        restore_proof="; ".join(
            record.restore_proof
            if len(files) == 1
            else f"`{record.relative_target}`: {record.restore_proof}"
            for record in files
        ),
        failure=None,
        baseline=baseline,
        pre_existing_node_ids=pre_existing,
        files=files,
        provenance_required=provenance_required,
    )


@dataclass(frozen=True)
class PlannedFile:
    """One file an entry will write: its bytes now and the bytes every site on it produces."""

    target: Path
    original: bytes
    mutated: bytes
    sites: tuple[MutationSite, ...]


def _plan_files(entry: ProofEntry) -> tuple[PlannedFile, ...]:
    """Return every file the entry mutates with its mutated bytes, writing nothing.

    Anchor sites read the file as text the way the original single-site loop
    did; a pre-image or reverse patch reads its bytes exactly, since each owns
    its file alone. A failing site is named by position when there are several.
    """
    sites = entry.mutation_sites
    planned = []
    for target in entry.targets:
        on_target = tuple(site for site in sites if site.target == target)
        original = target.read_bytes()
        if all(site.kind == ANCHOR_KIND for site in on_target):
            text = target.read_text(encoding="utf-8")
        else:
            text = original.decode("utf-8")
        for site in on_target:
            try:
                text = site.apply(text)
            except SiteError as error:
                if len(sites) == 1:
                    raise
                number = sites.index(site) + 1
                raise SiteError(f"site {number} (`{site.relative_target}`): {error}") from error
        planned.append(PlannedFile(target, original, text.encode("utf-8"), on_target))
    return tuple(planned)


def _marker_payload(
    entry: ProofEntry,
    plan: Sequence[PlannedFile],
    pristines: Sequence[Path],
) -> dict[str, object]:
    """Return the live-mutation marker: the first file at top level, every file under ``files``."""
    files = [
        {
            "mutated_file": str(planned.target),
            "restore_from": str(pristine),
            "restore_with": f"cp {pristine} {planned.target}",
        }
        for planned, pristine in zip(plan, pristines, strict=True)
    ]
    return {"label": entry.label, **files[0], "files": files}


def _restore_every_file(
    entry: ProofEntry,
    plan: Sequence[PlannedFile],
    pristines: Sequence[Path],
    mutated_blobs: dict[Path, str],
    scratch_root: Path,
) -> tuple[FileRecord, ...]:
    """Restore and byte-prove every planned file, attempting all before raising.

    A file whose restore cannot be proved does not stop the others from being
    restored; the first failure is raised once every file has been attempted,
    and the marker names every file that failed.
    """
    records = []
    failures: list[tuple[PlannedFile, Path, RestoreProofError]] = []
    for planned, pristine in zip(plan, pristines, strict=True):
        try:
            proof = _restore_and_prove(planned.target, pristine)
        except RestoreProofError as error:
            failures.append((planned, pristine, error))
            continue
        restored = planned.target.read_bytes()
        records.append(
            FileRecord(
                relative_target=planned.target.relative_to(REPO_ROOT).as_posix(),
                pristine=str(pristine),
                blob_before=git_blob_id(planned.original),
                blob_mutated=mutated_blobs.get(planned.target, "not written"),
                blob_after=git_blob_id(restored),
                sha256_before=hashlib.sha256(planned.original).hexdigest(),
                sha256_after=hashlib.sha256(restored).hexdigest(),
                diff=_unified_diff(planned),
                restore_proof=proof,
            ),
        )
    if failures:
        first_planned, first_pristine, first_error = failures[0]
        _write_marker(
            scratch_root / RESTORE_FAILED_MARKER_NAME,
            {
                "label": entry.label,
                "mutated_file": str(first_planned.target),
                "restore_from": str(first_pristine),
                "detail": str(first_error),
                "files": [
                    {
                        "mutated_file": str(planned.target),
                        "restore_from": str(pristine),
                        "detail": str(error),
                    }
                    for planned, pristine, error in failures
                ],
            },
        )
        raise first_error
    return tuple(records)


def _unified_diff(planned: PlannedFile) -> str:
    """Return the full unified diff from a file's pre-mutation bytes to its mutated bytes."""
    relative = planned.target.relative_to(REPO_ROOT).as_posix()
    return "".join(
        difflib.unified_diff(
            planned.original.decode("utf-8", errors="replace").splitlines(keepends=True),
            planned.mutated.decode("utf-8", errors="replace").splitlines(keepends=True),
            fromfile=f"a/{relative}",
            tofile=f"b/{relative}",
        ),
    )


def _pristine_name(entry: ProofEntry) -> str:
    """Return a collision-free scratch filename for one entry's pristine copy."""
    return _pristine_name_for(entry, entry.target)


def _pristine_name_for(entry: ProofEntry, target: Path) -> str:
    """Return a collision-free scratch filename for one of an entry's mutated files."""
    flattened = target.relative_to(REPO_ROOT).as_posix().replace("/", "__")
    digest = hashlib.sha256(entry.label.encode("utf-8")).hexdigest()[:8]
    return f"{digest}__{flattened}"


def _verdict(result: ProofResult) -> str:
    """Return the acceptance verdict for one proved boundary."""
    if result.failure is not None:
        return f"**ENTRY ERROR** - {result.failure}"
    if result.outcome is None:
        if result.entry.sites:
            return "every site applies to the file as it stands (no run; --check-anchors-only)"
        return "anchor matches exactly once (no run; --check-anchors-only)"
    notes = []
    invalid = result.invalid_count_reason
    if invalid is not None:
        notes.append(f"**INVALID COUNT - {invalid}**")
    expectation = result.expectation
    if expectation is not None and invalid is None:
        notes.append(_expectation_verdict(expectation, result.failed_count))
    if result.is_weakly_pinned:
        notes.append("**WEAKLY PINNED - revision-needed**")
    if result.is_inside_rerun_floor:
        notes.append("inside Worker 3's mandatory re-run floor (<= 3 rows)")
    if not notes:
        notes.append("pinned")
    return "; ".join(notes)


def _expectation_verdict(expectation: Expectation, failed_count: int) -> str:
    """Return the verdict for a declared ``expect_failing`` set against a valid count."""
    if expectation.is_met and not expectation.declared:
        return "behaviour preserved: no row failed, as `expect_failing: []` declares"
    if expectation.is_met:
        return (
            f"pinned: the {failed_count} failing row(s) are exactly the declared `expect_failing`"
        )
    parts = []
    if expectation.missing:
        missing = ", ".join(f"`{pattern}`" for pattern in expectation.missing)
        parts.append(f"declared but not failing: {missing}")
    if expectation.missing_but_failing_at_baseline:
        already = ", ".join(f"`{p}`" for p in expectation.missing_but_failing_at_baseline)
        parts.append(f"of those, already failing before the mutation: {already}")
    if expectation.unexpected:
        unexpected = ", ".join(f"`{node}`" for node in expectation.unexpected)
        parts.append(f"failing but not declared: {unexpected}")
    return f"**EXPECTATION NOT MET - revision-needed** ({'; '.join(parts)})"


@dataclass(frozen=True)
class ReportContext:
    """Where the run happened: the tree mutated, the declared workspace, the scratch root."""

    repo_root: Path
    workspace: Path | None
    scratch_root: Path

    def describe(self) -> str:
        """Return the record's workspace line."""
        workspace = f"`{self.workspace}`" if self.workspace is not None else "not given"
        return (
            f"Workspace: repository root mutated `{self.repo_root}`; `--workspace` {workspace}; "
            f"scratch root `{self.scratch_root}`."
        )


def render_report(
    results: Sequence[ProofResult],
    *,
    anchors_only: bool = False,
    abort: str | None = None,
    selection: ManifestSelection | None = None,
    context: ReportContext | None = None,
) -> str:
    """Return the markdown block for a build report's failability-proof subsection.

    ``abort`` names a restore that could not be proved. The partial record is
    still rendered (and still written to ``--output``): a run that stopped with a
    possibly-live mutation is exactly what the next reader must see first.

    ``selection`` says how much of the manifest ran. When ``--only`` narrowed it,
    the notice goes directly under the heading AND on the block's last line, and
    the ``#`` column switches to manifest positions - the two ends are where a
    pasted block loses text, and the column puts the fact in the data rather than
    only in prose. A run covering every manifest entry says nothing extra: the
    absence of the notice is only meaningful if it is never noise.
    """
    lines = ["### Failability proofs", ""]
    if selection is not None and selection.is_partial:
        lines.extend(_partial_record_notice(selection))
    lines.append(
        "Procedure, mechanized by `scripts/prove_failability.py`: the target is copied to a "
        "scratch path OUTSIDE the repo before any mutation; the mutation site is located by an "
        "exact anchor asserted to match exactly once (any other count aborts the entry without "
        "writing); the same focused scope is run unmutated first, so rows already failing before "
        "the mutation are differenced out of the count; both runs' pytest exit codes are read, "
        "because a run that collected nothing or blew up emits no `FAILED` lines and would "
        "otherwise be recorded as a measured zero; both runs use `--no-cov`; the file is "
        "restored from the pre-mutation copy in a `finally` and the restore is proved by "
        "`filecmp.cmp(shallow=False)` plus a SHA-256 comparison. One boundary at a time, "
        "restored before the next. `git` is never invoked - the tree is legitimately dirty, so "
        "an empty `git diff` is unachievable and forcing one would destroy the build's own work.",
    )
    lines.append("")
    if context is not None:
        lines.append(context.describe())
        lines.append("")
    if abort is not None:
        lines.append(
            "**RUN ABORTED - A RESTORE COULD NOT BE PROVED; THE WORKING TREE MAY STILL HOLD A "
            f"MUTATION.** {abort} Entries after the aborted one were not attempted, so this is a "
            "PARTIAL record and not an acceptable proof of anything.",
        )
        lines.append("")
    if anchors_only:
        lines.append("Anchor validation only; no mutation was applied and no scope was run.")
        lines.append("")
    if selection is not None and selection.is_partial:
        lines.append(
            f"The `#` column below is the entry's position in the {selection.manifest_total}-entry "
            f"manifest, not a row number: {selection.selected_total} of those entries ran.",
        )
        lines.append("")
    # ``File mutated`` is the target as resolved and written to, and it is a column of
    # its own because the boundary label beside it is free manifest text: an entry
    # labelled `package/views.py::Mixin.method` with `"target": "tests/test_views.py"`
    # used to render a record whose every file identity was the unchecked label, so a
    # mutation that landed in a test file read as a removed production boundary. The
    # label is now refused when it disagrees (see _refuse_label_target_disagreement),
    # and the value that falsifies it is rendered rather than merely computed.
    lines.append(
        "| # | Boundary | File mutated | Mutation applied | Rows failed | Errors | "
        "Scope as run | Restore proof |",
    )
    lines.append("|---|---|---|---|---|---|---|---|")
    for position, result in enumerate(results, 1):
        count = "n/a" if result.outcome is None else f"**{result.failed_count}**"
        errors = "n/a" if result.outcome is None else str(result.error_count)
        if result.invalid_count_reason is not None:
            count += " (NOT A VALID COUNT)"
            errors = f"**{errors}**"
        mutated_files = ", ".join(f"`{path}`" for path in result.entry.relative_targets)
        lines.append(
            f"| {_row_number(result, position)} | `{result.entry.label}` | "
            f"{mutated_files} | {result.entry.mutation_applied} | {count} | "
            f"{errors} | `{result.entry.scope_as_run}` | {result.restore_proof} |",
        )
    if not results:
        lines.append("| - | _(no entry completed)_ | - | - | - | - | - | - |")
    lines.append("")
    lines.append("Verdicts:")
    lines.append("")
    for position, result in enumerate(results, 1):
        lines.append(
            f"{_row_number(result, position)}. `{result.entry.label}` - {_verdict(result)}",
        )
    if not results:
        lines.append("- (none)")
    lines.append("")
    lines.append("Failing node ids, per boundary (the count above is `len()` of this list):")
    lines.append("")
    for position, result in enumerate(results, 1):
        lines.append(f"{_row_number(result, position)}. `{result.entry.label}`")
        # Named again beside the count and the restore proof: the label heading this
        # list is manifest text, and this is the file the bytes were written to.
        for relative_target in result.entry.relative_targets:
            lines.append(f"   - file mutated: `{relative_target}`")
        if result.outcome is None:
            lines.append("   - no run")
            continue
        lines.append(f"   - pytest summary: `{result.outcome.summary}`")
        lines.append(f"   - pytest exit code: {result.outcome.return_code}")
        lines.append(f"   - {_baseline_line(result)}")
        lines.append(f"   - collection/setup errors: {result.error_count}")
        if result.invalid_count_reason is not None:
            lines.append(f"   - **NOT A VALID COUNT**: {result.invalid_count_reason}")
        if result.entry.expect_failing is not None:
            declared = ", ".join(f"`{p}`" for p in result.entry.expect_failing) or "none"
            lines.append(f"   - declared `expect_failing`: {declared}")
        for node_id in result.attributable_node_ids or ("(none)",):
            lines.append(f"   - `{node_id}`{_crash_suffix(result.outcome, node_id)}")
        for node_id in result.outcome.error_node_ids:
            lines.append(f"   - ERROR `{node_id}`{_crash_suffix(result.outcome, node_id)}")
        if result.failed_count == 0 and result.entry.expect_failing is None:
            invalid = result.invalid_count_reason is not None
            lines.append(f"   - {NO_COUNT_TO_EXPLAIN if invalid else ZERO_ROW_PLACEHOLDER}")
        for name, run in (("mutant", result.outcome), ("baseline", result.baseline)):
            if run is not None:
                lines.extend(_run_provenance_lines(name, run))
        for record in result.files:
            lines.extend(_file_record_lines(record))
    if not results:
        lines.append("- (none)")
    lines.append("")
    lines.append(
        "A boundary whose removal fails 0 or 1 rows is **weakly pinned** and is "
        "`revision-needed` per `docs/builder/BUILD.md` - the fix is more or better-targeted "
        "rows, never a weaker boundary. A boundary at 3 rows or fewer is inside Worker 3's "
        "mandatory independent re-run floor. A proof carrying collection or setup errors, or "
        "whose pytest run exited anything but 0 or 1 (nothing collected, interrupted, internal "
        "error, usage error), is not a valid count at all - and a 0 from such a run is not a "
        "zero-row result: resolve it and re-run.",
    )
    lines.append("")
    lines.append(
        "Every `<fill in ...>` above is a judgement no tool can make and MUST be replaced by "
        "hand before this subsection is submitted: weakly pinned and harness-impossible are "
        "the two possible readings of a zero-row result and they prescribe opposite responses "
        "(more rows, versus a production-call-site invariant assertion plus a recorded harness "
        "limitation), so a record that does not name one reads as self-contradictory.",
    )
    if selection is not None and selection.is_partial:
        lines.append("")
        lines.append(
            f"**Reminder, PARTIAL RECORD: this block covers {selection.selected_total} of "
            f"{selection.manifest_total} manifest entries (`{selection.selector_text}`)** and is "
            "not a complete `### Failability proofs` subsection on its own. Repeated here because "
            "a notice only at the top is lost the moment the block is pasted from part-way down.",
        )
    return "\n".join(lines) + "\n"


def _row_number(result: ProofResult, position: int) -> int:
    """Return the entry's manifest position, or its position here when it has none."""
    return result.entry.manifest_position or position


def _crash_suffix(run: RunOutcome, node_id: str) -> str:
    """Return `` - crash: `<location>: <line>` `` for a row the probe saw fail, else nothing.

    The markdown carries one line: pytest's ``assert ...`` line when the message
    has one (an assertion with a custom message puts it on a later line), else
    the first line. ``--json`` carries the message whole.
    """
    crash = run.crash_line(node_id)
    if not crash:
        return ""
    first, *rest = crash.splitlines() or [""]
    assertion = next((line.strip() for line in rest if line.strip().startswith("assert ")), None)
    shown = first if assertion is None else f"{first.split(': ', 1)[0]}: {assertion}"
    more = f" (+{len(rest)} more line(s) in --json)" if rest else ""
    return f" - crash: `{shown}`{more}"


def _run_provenance_lines(name: str, run: RunOutcome) -> list[str]:
    """Return one run's provenance, wall time and raw-log lines."""
    wall = "not measured" if run.wall_seconds is None else f"{run.wall_seconds} s"
    lines = [f"   - {name} run: wall time {wall}; raw log `{run.log_path or 'not kept'}`"]
    if not run.provenance:
        lines.append(f"   - {name} run provenance: not observed inside pytest")
    lines.extend(f"   - {name} run provenance, {record.describe()}" for record in run.provenance)
    return lines


def _file_record_lines(record: FileRecord) -> list[str]:
    """Return one mutated file's blob ids, restore proof and full mutation diff."""
    lines = [
        f"   - `{record.relative_target}` git blob before `{record.blob_before}`, mutated "
        f"`{record.blob_mutated}`, after restore `{record.blob_after}`",
        f"   - `{record.relative_target}` mutation as applied:",
        "",
        "     ```diff",
    ]
    lines.extend(f"     {line}".rstrip() for line in record.diff.splitlines())
    lines.extend(["     ```", ""])
    return lines


def _partial_record_notice(selection: ManifestSelection) -> list[str]:
    """Return the notice that a ``--only`` run's report is a subset of the manifest."""
    lines = [
        f"**PARTIAL RECORD - `--only` NARROWED THIS RUN: {selection.selected_total} of "
        f"{selection.manifest_total} manifest entries were selected by "
        f"`{selection.selector_text}`, and the other {len(selection.omitted_labels)} were NOT "
        "proved.** `docs/builder/ARTIFACT.md` `### Failability proofs` requires one entry per new "
        "boundary the pass introduced, so this block does not satisfy that requirement on its own: "
        "it is evidence for the entries listed below and for nothing else. Re-run without `--only` "
        "for a complete record, or say beside this block where the remaining boundaries' proofs "
        "are - a Worker 3 independent re-run of a subset is exactly that case, and already owes "
        "the artifact a statement of which boundaries it re-ran and which it accepted on Worker "
        "2's record.",
        "",
        "Manifest entries this run did NOT prove:",
        "",
    ]
    lines.extend(f"- `{label}`" for label in selection.omitted_labels)
    lines.append("")
    return lines


def _baseline_line(result: ProofResult) -> str:
    """Return the pre-mutation-state line, which is a mandatory recorded field."""
    if result.baseline is None:
        return (
            "pre-mutation state of this scope: **NOT CAPTURED** (`--no-baseline`); this record "
            "omits a field `docs/builder/ARTIFACT.md` requires and is not a compliant proof"
        )
    return (
        f"pre-mutation (unmutated) state of this scope: `{result.baseline.summary}` "
        f"(pytest exit code {result.baseline.return_code}); pre-existing failing rows excluded "
        f"from the count: {len(result.pre_existing_node_ids)}"
    )


def _run_record(run: RunOutcome | None) -> dict[str, object] | None:
    """Return one run as JSON data."""
    if run is None:
        return None
    return {
        "return_code": run.return_code,
        "countable": run.is_countable,
        "summary": run.summary,
        "failed": list(run.failed_node_ids),
        "errors": list(run.error_node_ids),
        "crash_lines": dict(run.crash_lines),
        "provenance": [
            {**dataclasses.asdict(record), "databases": dict(record.databases)}
            for record in run.provenance
        ],
        "wall_seconds": run.wall_seconds,
        "log_path": run.log_path,
    }


def _site_record(site: MutationSite) -> dict[str, object]:
    """Return one mutation site's full, untruncated input as JSON data."""
    return {
        "kind": site.kind,
        "target": site.relative_target,
        "anchor": site.anchor if site.kind == ANCHOR_KIND else None,
        "replacement": site.replacement,
        "delete": site.kind == ANCHOR_KIND and site.replacement is None,
        "source": None if site.source is None else str(site.source),
        "hunks": len(site.hunks),
    }


def _entry_record(result: ProofResult, position: int) -> dict[str, object]:
    """Return one entry's complete record as JSON data."""
    expectation = result.expectation
    return {
        "position": _row_number(result, position),
        "label": result.entry.label,
        "prose": result.entry.prose or None,
        "mutation": result.entry.mutation,
        "targets": list(result.entry.relative_targets),
        "sites": [_site_record(site) for site in result.entry.mutation_sites],
        "scope": list(result.entry.scope),
        "scope_as_run": result.entry.scope_as_run,
        "files": [dataclasses.asdict(record) for record in result.files],
        "restore_proof": result.restore_proof,
        "baseline": _run_record(result.baseline),
        "mutant": _run_record(result.outcome),
        "pre_existing_failed": list(result.pre_existing_node_ids),
        "attributable_failed": list(result.attributable_node_ids),
        "failed_count": result.failed_count,
        "error_count": result.error_count,
        "expect_failing": (
            None if result.entry.expect_failing is None else list(result.entry.expect_failing)
        ),
        "expectation": (
            None
            if expectation is None
            else {
                "met": expectation.is_met,
                "missing": list(expectation.missing),
                "unexpected": list(expectation.unexpected),
                "missing_but_failing_at_baseline": list(
                    expectation.missing_but_failing_at_baseline,
                ),
            }
        ),
        "invalid_count_reasons": list(result.invalid_count_reasons),
        "weakly_pinned": result.is_weakly_pinned,
        "inside_rerun_floor": result.is_inside_rerun_floor,
        "failure": result.failure,
        "verdict": _verdict(result),
    }


def build_json_report(
    results: Sequence[ProofResult],
    *,
    context: ReportContext,
    manifest_path: Path,
    exit_code: int,
    anchors_only: bool = False,
    abort: str | None = None,
    selection: ManifestSelection | None = None,
) -> dict[str, object]:
    """Return the machine-readable record of a run: the data the markdown renders, whole."""
    manifest_bytes = manifest_path.read_bytes() if manifest_path.is_file() else b""
    return {
        "schema_version": JSON_SCHEMA_VERSION,
        "tool": "scripts/prove_failability.py",
        "written_at": datetime.now(timezone.utc).isoformat(),
        "repo_root": str(context.repo_root),
        "workspace": None if context.workspace is None else str(context.workspace),
        "scratch_root": str(context.scratch_root),
        "manifest": str(manifest_path.resolve()),
        "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "pytest_command": list(PYTEST_COMMAND),
        "anchors_only": anchors_only,
        "aborted": abort,
        "selection": (
            None
            if selection is None
            else {
                "manifest_total": selection.manifest_total,
                "selectors": list(selection.selectors),
                "omitted_labels": list(selection.omitted_labels),
                "partial": selection.is_partial,
            }
        ),
        "exit_code": exit_code,
        "entries": [_entry_record(result, position) for position, result in enumerate(results, 1)],
    }


def _exit_code(results: Sequence[ProofResult]) -> int:
    """Return ``1`` when any entry is unproved, weak, invalid or misses its expectation."""
    for result in results:
        if (
            result.failure is not None
            or result.is_weakly_pinned
            or result.invalid_count_reason is not None
            or result.is_expectation_unmet
        ):
            return 1
    return 0


def _refuse_outside_workspace(raw_workspace: Path) -> str | None:
    """Return why this script's repository root is not inside ``raw_workspace``, if it is not."""
    workspace = raw_workspace.expanduser().resolve()
    if not _is_within(REPO_ROOT, workspace):
        return (
            f"--workspace {workspace}: this script's repository root {REPO_ROOT} is not inside "
            "it, so the run would mutate a tree other than the workspace. Run the copy's own "
            "script: uv run --directory <ws> python <ws>/scripts/prove_failability.py ..."
        )
    if (REPO_ROOT / ".git").exists():
        return (
            f"--workspace {workspace}: the repository root {REPO_ROOT} holds a .git, so it is a "
            "checkout and not a workspace copy (the copy is taken with --exclude .git)"
        )
    return None


def _build_parser() -> argparse.ArgumentParser:
    """Return the command-line parser."""
    parser = argparse.ArgumentParser(
        description=(
            "Run manifest-driven failability proofs: mutate a boundary, run its focused "
            "scope, restore from a pre-mutation copy, and prove the restore by byte comparison."
        ),
    )
    parser.add_argument("manifest", type=Path, help="path to the JSON proof manifest")
    parser.add_argument(
        "--only",
        action="append",
        default=[],
        metavar="SELECTOR",
        help=(
            "run only entries matching this 1-based index or label substring (repeatable). The "
            "emitted report is then labelled PARTIAL RECORD and names every entry it did not "
            "prove: --output is still allowed (an independent re-run of a subset is what this "
            "flag is for), but a narrowed block is not a complete ARTIFACT.md subsection"
        ),
    )
    parser.add_argument(
        "--scratch-root",
        default=None,
        help="directory for pristine copies and markers; must be OUTSIDE the repository",
    )
    parser.add_argument(
        "--baseline",
        action="store_true",
        dest="force_baseline",
        help=(
            "accepted for compatibility and now redundant: the unmutated baseline run is the "
            "default. Given together with --no-baseline it wins, because it asks for the field"
        ),
    )
    parser.add_argument(
        "--no-baseline",
        action="store_false",
        dest="baseline",
        default=True,
        help=(
            "skip the unmutated run (quick local probe only): the count then includes rows that "
            "were already failing, so --output is refused - the record would omit a mandatory "
            "field required by docs/builder/ARTIFACT.md"
        ),
    )
    parser.add_argument(
        "--check-anchors-only",
        action="store_true",
        help="verify every anchor matches exactly once; mutate nothing and run nothing",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="also write the markdown report to this path",
    )
    parser.add_argument(
        "--json",
        type=Path,
        default=None,
        dest="json_output",
        metavar="PATH",
        help=(
            "also write the machine-readable record to this path: full mutation text and diff, "
            "blob ids, both runs' ids, crash lines, provenance, expectation and verdict"
        ),
    )
    parser.add_argument(
        "--workspace",
        type=Path,
        default=None,
        metavar="PATH",
        help=(
            "refuse to run unless this script's repository root is PATH or lies under it and "
            "holds no .git; a run then needs provenance observed inside pytest to count"
        ),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run every selected proof entry and emit the markdown (and optional JSON) report."""
    arguments = _build_parser().parse_args(argv)
    capture_baseline = arguments.baseline or arguments.force_baseline
    if not capture_baseline and arguments.output is not None and not arguments.check_anchors_only:
        print(
            "--no-baseline cannot be combined with --output: the pre-mutation state of the "
            "scope is a mandatory field of the recorded proof (docs/builder/ARTIFACT.md "
            "'### Failability proofs'), and a report that omits it is not a compliant record. "
            "Drop --no-baseline, or drop --output and read the run on stderr.",
            file=sys.stderr,
        )
        return 1
    workspace = None
    if arguments.workspace is not None:
        refusal = _refuse_outside_workspace(arguments.workspace)
        if refusal is not None:
            print(f"workspace refused: {refusal}", file=sys.stderr)
            return 1
        workspace = arguments.workspace.expanduser().resolve()
    try:
        entries, manifest_scratch_root = load_manifest(arguments.manifest)
        selected = select_entries(entries, arguments.only)
        scratch_root = _resolve_scratch_root(arguments.scratch_root or manifest_scratch_root)
    except ManifestError as error:
        print(f"manifest error: {error}", file=sys.stderr)
        return 1
    selection = describe_selection(entries, selected, arguments.only)
    context = ReportContext(repo_root=REPO_ROOT, workspace=workspace, scratch_root=scratch_root)
    print(f"repository root: {REPO_ROOT}", file=sys.stderr)
    print(f"scratch root: {scratch_root}", file=sys.stderr)
    if selection.is_partial:
        print(
            f"PARTIAL RUN: --only selected {selection.selected_total} of "
            f"{selection.manifest_total} manifest entries; the report is labelled PARTIAL RECORD "
            "and names the entries it did not prove.",
            file=sys.stderr,
        )
    results: list[ProofResult] = []
    for position, entry in enumerate(selected, 1):
        targets = ", ".join(entry.relative_targets)
        print(
            f"[{position}/{len(selected)}] {entry.label}\n"
            f"    target: {targets}\n"
            f"    scope:  {entry.scope_as_run}",
            file=sys.stderr,
        )
        try:
            result = execute_entry(
                entry,
                scratch_root,
                capture_baseline=capture_baseline,
                anchors_only=arguments.check_anchors_only,
                provenance_required=workspace is not None,
            )
        except RestoreProofError as error:
            marker = scratch_root / RESTORE_FAILED_MARKER_NAME
            print("\n" + "!" * 78, file=sys.stderr)
            print("RESTORE FAILED - THE WORKING TREE MAY STILL HOLD A MUTATION", file=sys.stderr)
            print(f"  {error}", file=sys.stderr)
            print(f"  marker: {marker}", file=sys.stderr)
            print("Run aborted; remaining entries were not attempted.", file=sys.stderr)
            print("!" * 78 + "\n", file=sys.stderr)
            abort = f"Entry `{entry.label}`: {error} Marker: `{marker}`."
            report = render_report(
                results,
                anchors_only=arguments.check_anchors_only,
                abort=abort,
                selection=selection,
                context=context,
            )
            print(report)
            _write_report(report, arguments.output, label="partial report")
            _write_json(
                arguments.json_output,
                build_json_report(
                    results,
                    context=context,
                    manifest_path=arguments.manifest,
                    exit_code=3,
                    anchors_only=arguments.check_anchors_only,
                    abort=abort,
                    selection=selection,
                ),
                label="partial JSON record",
            )
            return 3
        results.append(result)
        for name, run in (("baseline", result.baseline), ("mutant", result.outcome)):
            for record in run.provenance if run is not None else ():
                print(f"    {name} provenance, {record.describe()}", file=sys.stderr)
        print(f"    -> {_verdict(result)}", file=sys.stderr)
    report = render_report(
        results,
        anchors_only=arguments.check_anchors_only,
        selection=selection,
        context=context,
    )
    print(report)
    _write_report(report, arguments.output, label="report")
    exit_code = _exit_code(results)
    _write_json(
        arguments.json_output,
        build_json_report(
            results,
            context=context,
            manifest_path=arguments.manifest,
            exit_code=exit_code,
            anchors_only=arguments.check_anchors_only,
            selection=selection,
        ),
        label="JSON record",
    )
    return exit_code


def _write_json(output: Path | None, document: dict[str, object], *, label: str) -> None:
    """Write the JSON record to ``output`` when one was asked for."""
    if output is None:
        return
    output.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
    print(f"{label} written to {output}", file=sys.stderr)


def _write_report(report: str, output: Path | None, *, label: str) -> None:
    """Write the rendered report to ``output`` when one was asked for."""
    if output is None:
        return
    output.write_text(report, encoding="utf-8")
    print(f"{label} written to {output}", file=sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())
