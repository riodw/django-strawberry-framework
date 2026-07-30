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

Usage::

    uv run python scripts/prove_failability.py <manifest.json>
    uv run python scripts/prove_failability.py <manifest.json> --check-anchors-only
    uv run python scripts/prove_failability.py <manifest.json> --only B --only 4
    uv run python scripts/prove_failability.py <manifest.json> --no-baseline
    uv run python scripts/prove_failability.py <manifest.json> --output proofs.md

Exit codes: ``0`` every entry proved, no boundary weakly pinned, and no
collection or setup error; ``1`` at least one entry is weakly pinned, carries a
collection/setup error or a pytest exit code outside ``{0, 1}`` (so its count is
not a valid count), or its anchor did not match exactly once, or the manifest is
unusable, or ``--output`` was asked for without a baseline; ``3`` a restore
could not be proved (the tree may still hold a mutation - read the marker file
the run leaves behind; the partial report is still written to ``--output``).
"""

from __future__ import annotations

import argparse
import filecmp
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
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
# from writing cache state into the repo.
PYTEST_COMMAND = (
    "uv",
    "run",
    "pytest",
    "--no-cov",
    "--color=no",
    "-p",
    "no:cacheprovider",
    "--tb=no",
    "-q",
    "-rfE",
)
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
    },
)
MANIFEST_KEYS = frozenset({"proofs", "scratch_root"})


class ManifestError(Exception):
    """The manifest is not a usable set of proof entries."""


class RestoreProofError(Exception):
    """A mutated file could not be restored, or the restore could not be proved."""


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
    """

    label: str
    target: Path
    anchor: str
    replacement: str | None
    mutation: str
    scope: tuple[str, ...]
    manifest_position: int = 0
    prose: str = ""

    @property
    def relative_target(self) -> str:
        """Return the target path relative to the repository root."""
        return self.target.relative_to(REPO_ROOT).as_posix()

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
class RunOutcome:
    """What one focused pytest run reported."""

    failed_node_ids: tuple[str, ...]
    error_node_ids: tuple[str, ...]
    summary: str
    return_code: int

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
class ProofResult:
    """One entry's full record: the run, the restore proof, or why neither happened."""

    entry: ProofEntry
    outcome: RunOutcome | None
    restore_proof: str
    failure: str | None
    baseline: RunOutcome | None = None
    pre_existing_node_ids: tuple[str, ...] = ()

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
        return tuple(reasons)

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
        if self.invalid_count_reason is not None:
            return False
        return self.failed_count <= WEAKLY_PINNED_MAXIMUM

    @property
    def is_inside_rerun_floor(self) -> bool:
        """Whether a VALID count puts this boundary inside Worker 3's mandatory re-run floor."""
        if self.failure is not None or self.outcome is None:
            return False
        if self.invalid_count_reason is not None:
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


def _parse_entry(raw_entry: object, position: int) -> ProofEntry:
    """Return one validated :class:`ProofEntry` from its manifest mapping."""
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
    target = _resolve_target(raw_entry.get("target"), label)
    _refuse_label_target_disagreement(label, target)
    if "anchor" not in raw_entry:
        raise ManifestError(f"{label}: 'anchor' is required")
    anchor = _join_lines(raw_entry["anchor"], "anchor", label)
    if not anchor:
        raise ManifestError(f"{label}: 'anchor' must not be empty")
    deletes = bool(raw_entry.get("delete", False))
    if deletes and "replacement" in raw_entry:
        raise ManifestError(f"{label}: give either 'replacement' or 'delete', not both")
    if not deletes and "replacement" not in raw_entry:
        raise ManifestError(f"{label}: give either 'replacement' or 'delete': true")
    replacement = None if deletes else _join_lines(raw_entry["replacement"], "replacement", label)
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
    return ProofEntry(
        label=label,
        target=target,
        anchor=anchor,
        replacement=replacement,
        # Derived, never taken from the manifest: 'mutation' is prose about the
        # bytes and cannot stand in for the bytes (see ProofEntry.mutation_applied).
        mutation=_describe_mutation(anchor, replacement),
        scope=tuple(scope),
        manifest_position=position,
        prose=mutation or "",
    )


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
    entries = tuple(_parse_entry(raw, position) for position, raw in enumerate(raw_proofs, 1))
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


def _run_scope(entry: ProofEntry) -> RunOutcome:
    """Run one entry's focused pytest scope and return what it reported."""
    completed = subprocess.run(
        [*PYTEST_COMMAND, *entry.scope],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    failed, errored, summary = _parse_run_output(completed.stdout)
    if not summary:
        summary = (completed.stderr.strip().splitlines() or ["<no output>"])[-1]
    return RunOutcome(
        failed_node_ids=failed,
        error_node_ids=errored,
        summary=summary,
        return_code=completed.returncode,
    )


def _write_marker(path: Path, payload: dict[str, str]) -> None:
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
) -> ProofResult:
    """Prove one boundary: copy, verify the anchor, baseline, mutate, run, restore, compare.

    ``capture_baseline`` defaults to ``True`` because the pre-mutation state of
    the same scope is a mandatory recorded field, not an option: without it the
    attributable count is the raw failure set, and one pre-existing failing row
    silently inflates it.

    The copy is taken before anything is written and the restore runs in a
    ``finally``, so no return path and no exception leaves the mutation live. A
    restore that cannot be proved raises :class:`RestoreProofError` rather than
    being reported as one entry's failure.
    """
    original_text = entry.target.read_text(encoding="utf-8")
    occurrences = original_text.count(entry.anchor)
    if occurrences != 1:
        return ProofResult(
            entry=entry,
            outcome=None,
            restore_proof="not applicable; nothing was mutated",
            failure=(
                f"anchor matched {occurrences} times (must match exactly once); "
                "no mutation was applied"
            ),
        )
    if anchors_only:
        return ProofResult(
            entry=entry,
            outcome=None,
            restore_proof="not applicable; --check-anchors-only",
            failure=None,
        )
    pristine = scratch_root / PRISTINE_DIRECTORY_NAME / _pristine_name(entry)
    try:
        shutil.copy2(entry.target, pristine)
    except OSError as error:
        # Nothing has been mutated yet, so this is one entry's failure and not a
        # tree emergency - but it must never become "mutate first, copy later".
        return ProofResult(
            entry=entry,
            outcome=None,
            restore_proof="not applicable; nothing was mutated",
            failure=f"the pre-mutation copy to {pristine} failed ({error}); nothing was mutated",
        )
    baseline = _run_scope(entry) if capture_baseline else None
    pre_existing = baseline.failed_node_ids if baseline is not None else ()
    marker = scratch_root / ACTIVE_MARKER_NAME
    _write_marker(
        marker,
        {
            "label": entry.label,
            "mutated_file": str(entry.target),
            "restore_from": str(pristine),
            "restore_with": f"cp {pristine} {entry.target}",
        },
    )
    try:
        replacement = "" if entry.replacement is None else entry.replacement
        entry.target.write_text(
            original_text.replace(entry.anchor, replacement, 1),
            encoding="utf-8",
        )
        outcome = _run_scope(entry)
    finally:
        try:
            restore_proof = _restore_and_prove(entry.target, pristine)
        except RestoreProofError as error:
            _write_marker(
                scratch_root / RESTORE_FAILED_MARKER_NAME,
                {
                    "label": entry.label,
                    "mutated_file": str(entry.target),
                    "restore_from": str(pristine),
                    "detail": str(error),
                },
            )
            raise
        marker.unlink(missing_ok=True)
    return ProofResult(
        entry=entry,
        outcome=outcome,
        restore_proof=restore_proof,
        failure=None,
        baseline=baseline,
        pre_existing_node_ids=pre_existing,
    )


def _pristine_name(entry: ProofEntry) -> str:
    """Return a collision-free scratch filename for one entry's pristine copy."""
    flattened = entry.relative_target.replace("/", "__")
    digest = hashlib.sha256(entry.label.encode("utf-8")).hexdigest()[:8]
    return f"{digest}__{flattened}"


def _verdict(result: ProofResult) -> str:
    """Return the acceptance verdict for one proved boundary."""
    if result.failure is not None:
        return f"**ENTRY ERROR** - {result.failure}"
    if result.outcome is None:
        return "anchor matches exactly once (no run; --check-anchors-only)"
    notes = []
    invalid = result.invalid_count_reason
    if invalid is not None:
        notes.append(f"**INVALID COUNT - {invalid}**")
    if result.is_weakly_pinned:
        notes.append("**WEAKLY PINNED - revision-needed**")
    if result.is_inside_rerun_floor:
        notes.append("inside Worker 3's mandatory re-run floor (<= 3 rows)")
    if not notes:
        notes.append("pinned")
    return "; ".join(notes)


def render_report(
    results: Sequence[ProofResult],
    *,
    anchors_only: bool = False,
    abort: str | None = None,
    selection: ManifestSelection | None = None,
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
        lines.append(
            f"| {_row_number(result, position)} | `{result.entry.label}` | "
            f"`{result.entry.relative_target}` | {result.entry.mutation_applied} | {count} | "
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
        lines.append(f"   - file mutated: `{result.entry.relative_target}`")
        if result.outcome is None:
            lines.append("   - no run")
            continue
        lines.append(f"   - pytest summary: `{result.outcome.summary}`")
        lines.append(f"   - pytest exit code: {result.outcome.return_code}")
        lines.append(f"   - {_baseline_line(result)}")
        lines.append(f"   - collection/setup errors: {result.error_count}")
        if result.invalid_count_reason is not None:
            lines.append(f"   - **NOT A VALID COUNT**: {result.invalid_count_reason}")
        for node_id in result.attributable_node_ids or ("(none)",):
            lines.append(f"   - `{node_id}`")
        for node_id in result.outcome.error_node_ids:
            lines.append(f"   - ERROR `{node_id}`")
        if result.failed_count == 0:
            invalid = result.invalid_count_reason is not None
            lines.append(f"   - {NO_COUNT_TO_EXPLAIN if invalid else ZERO_ROW_PLACEHOLDER}")
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
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run every selected proof entry and emit the markdown report."""
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
    try:
        entries, manifest_scratch_root = load_manifest(arguments.manifest)
        selected = select_entries(entries, arguments.only)
        scratch_root = _resolve_scratch_root(arguments.scratch_root or manifest_scratch_root)
    except ManifestError as error:
        print(f"manifest error: {error}", file=sys.stderr)
        return 1
    selection = describe_selection(entries, selected, arguments.only)
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
        print(
            f"[{position}/{len(selected)}] {entry.label}\n"
            f"    target: {entry.relative_target}\n"
            f"    scope:  {entry.scope_as_run}",
            file=sys.stderr,
        )
        try:
            result = execute_entry(
                entry,
                scratch_root,
                capture_baseline=capture_baseline,
                anchors_only=arguments.check_anchors_only,
            )
        except RestoreProofError as error:
            marker = scratch_root / RESTORE_FAILED_MARKER_NAME
            print("\n" + "!" * 78, file=sys.stderr)
            print("RESTORE FAILED - THE WORKING TREE MAY STILL HOLD A MUTATION", file=sys.stderr)
            print(f"  {error}", file=sys.stderr)
            print(f"  marker: {marker}", file=sys.stderr)
            print("Run aborted; remaining entries were not attempted.", file=sys.stderr)
            print("!" * 78 + "\n", file=sys.stderr)
            report = render_report(
                results,
                anchors_only=arguments.check_anchors_only,
                abort=f"Entry `{entry.label}`: {error} Marker: `{marker}`.",
                selection=selection,
            )
            print(report)
            _write_report(report, arguments.output, label="partial report")
            return 3
        results.append(result)
        print(f"    -> {_verdict(result)}", file=sys.stderr)
    report = render_report(
        results,
        anchors_only=arguments.check_anchors_only,
        selection=selection,
    )
    print(report)
    _write_report(report, arguments.output, label="report")
    unproved = [result for result in results if result.failure is not None]
    weak = [result for result in results if result.is_weakly_pinned]
    invalid = [result for result in results if result.invalid_count_reason is not None]
    return 1 if unproved or weak or invalid else 0


def _write_report(report: str, output: Path | None, *, label: str) -> None:
    """Write the rendered report to ``output`` when one was asked for."""
    if output is None:
        return
    output.write_text(report, encoding="utf-8")
    print(f"{label} written to {output}", file=sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())
