# Build artifact contract

This file is the **artifact contract** referenced by [BUILD.md][build-md]: `BUILD.md` defines the build process, this file defines the file that process writes. Every build-cycle artifact — `bld-slice-<N>-<short_slug>.md`, `bld-review-<R>-<short_slug>.md`, `bld-integration.md`, `bld-final.md` under `docs/builder/` — starts as a copy of the fenced template below and accumulates the full back-and-forth for that slice or cohort. The artifact is the contract that flows between workers: everything inter-worker happens through this file plus the working-tree diff, and the `Status:` line defined here is what Worker 0 reads to drive dispatch. It is a standing doc, tracked alongside `BUILD.md` and the four `worker-*.md` role files; the per-cycle artifacts it governs are not.

## Status field ownership

The artifact's `Status:` line is set by exactly one worker per transition:

- `planned` — Worker 1 sets this when the artifact is first created. New artifacts always start with `Status: planned`.
- `built` — Worker 2 sets this at the end of every build pass (including re-passes after a Worker 3 rejection).
- `revision-needed` — set by Worker 3 (review surfaces unresolved findings) or Worker 1 (final verification rejects); either triggers Worker 0 to spawn Worker 2 again. **Worker 2 may also set it, for one case only:** the structural-drift pause (`worker-2.md` "Plan-vs-implementation drift"), where the right answer changes a plan-level architectural call. That one routes to Worker **1** for a plan revision, not back to Worker 2 — the setter is what distinguishes the three, so the build report must name which pause it is.
- `review-accepted` — set by Worker 3 when accepting the diff; signals Worker 0 to spawn Worker 1 for final verification. May carry Medium-or-higher findings escalated to Worker 1 (`worker-3.md` `### Acceptance gate`); Worker 1's final verification owns the decision.
- `final-accepted` — set by Worker 1 at the end of final verification; signals Worker 0 to mark the checklist box.

Worker 0 never writes to `Status:`. Worker 0 reads it to drive dispatch.

````text
# Build: Slice <N> — <slice title>

Spec reference: `docs/spec-<NNN>-<topic>-<0_0_X>.md` (lines <start>-<end>)
Status: planned | built | revision-needed | review-accepted | final-accepted

## Plan (Worker 1)

### DRY analysis

- What patterns from the existing codebase can be reused? Cite file:line.
- What new shared helper or module is justified? What is its single responsibility?
- What duplication does this slice risk introducing? How does the plan avoid it?

### Implementation steps

1. Step one. Cite the file:line touched.
2. Step two.
3. ...

Line numbers are pin-at-write-time navigational hints. Verify against the current source before editing — another worker's pass may have shifted the file since this plan was written.

### Test additions / updates

- Which tests prove the slice? Pin the path and assertion shape.
- Are temp/scratch tests appropriate for development? Note them here for Worker 3.

### Implementation discretion items

Items where Worker 1 has **assessed the design and decided** the choice is Worker 2's (a stylistic preference between two equally valid shapes, a private kwarg name, the order of two independent setup steps). This makes discretion explicit; it is not an architectural escape hatch. If Worker 1 cannot resolve a question from the spec and the codebase, stop the planning pass and escalate to the maintainer.

### Spec slice checklist (verbatim)

**In a review round, this heading is replaced by `### Dispatched findings checklist`** — one `- [ ]` box per finding dispatched to this cohort, in this same position and under the identical tick-and-audit discipline described below. See `BUILD.md` `## Review rounds`, "Dispatched findings checklist", for how the boxes are written and cohorted.

The spec's nested sub-bullets for this slice from `## Slice checklist`, copied verbatim as `- [ ]` boxes (preserve exact text, nested sub-bullets, inline citations). **Worker 2 ticks each box `- [x]` in the same build report that lands its contract** (and on re-passes), so progress is visible incrementally rather than only at the end; it ticks ONLY a box whose contract actually landed in its diff, and leaves a deferred or unbuilt sub-check `- [ ]` with the deferral stated in the build report. **Worker 1 audits these boxes at final verification**, no longer being the original ticker: confirm each `- [x]` truly landed (un-tick and set `revision-needed` otherwise), tick any landed box Worker 2 left open, and for any remaining `- [ ]` record a one-line deferral reason under `### Spec changes made (Worker 1 only)` or set `revision-needed`. Silently un-ticked-and-undeferred boxes block `final-accepted`. Worker 3 walks the list during review: a sub-check silently un-addressed in the diff is a Medium finding, and so is a box ticked with no matching implementation.

- [ ] (verbatim sub-check #1)
- [ ] (verbatim sub-check #2)
- ...

---

## Build report (Worker 2)

### Files touched

- `path/to/file.py` — what changed and why
- ...

### Tests added or updated

- `tests/path/test_x.py::test_name` — what it pins

### Validation run

- `uv run ruff format <files this pass touched>` — pass/fail (scoped to your own files, never `.`)
- `uv run ruff check --fix <the same files>` — pass/fail
- `git status --short` after both ruff invocations — every modified file must be slice-intended and appear in `### Files touched`. Anything else is a **stop-and-report**, never a revert: this tree can carry a concurrent session's uncommitted work, so `git checkout -- path` to tidy unexpected churn destroys someone else's change. Scoping the write-mode runs above is what stops the churn existing; if it appears anyway, say so in the build report rather than cleaning it up.
- Focused test commands run, if any (no `--cov*` flags — see "Coverage is the maintainer's gate, not a worker's tool")

### Failability proofs

One entry per new boundary / guard / gate / rejection path this pass introduced, carrying every field "What gets recorded" requires (see "Failability proofs: prove the test can fail"). Write `None; this pass introduced no new boundary.` when that is true — keep the heading either way. `scripts/prove_failability.py --output` emits this subsection with every measured field already filled in; the only thing left by hand is the **why 0** judgement on a zero-row entry, which it emits as a `why 0: <fill in — …>` placeholder because weakly-pinned versus harness-impossible is not a measurement.

- `path/to/file.py::Symbol` — mutation applied: <what was removed, inverted, or weakened>; scope as run: <the exact pytest invocation>; pre-mutation state of that scope: <green, or the node ids the mutant's set is differenced against>; failing node ids: <listed, one per row — the count is their `len()`, never asserted>; collection/setup errors: <N; a valid count requires 0>; revert proved by byte-comparison: <command and result>.

A boundary whose removal fails 0 or 1 rows is **weakly pinned** and is `revision-needed`, not a recorded exception. A proof carrying collection or setup errors is no valid count at all. Every zero-row entry carries a one-line **why 0** naming which case it is; when the harness is what cannot exhibit the failure, name the limitation and record the production-call-site invariant assertion that replaced the wire-level one.

### Hot-path budget

Required when the plan declares this slice hot-path (see "Hot-path budget"). Write `Not applicable; plan declares no hot path.` otherwise.

- metric measured, exact command or snippet, iteration count and statistic, number before, number after, delta.

### Floor verification

Required when the plan's floor-verification scope assigns this slice's floor run to this pass (see "Floor verification" — the declaration names the owner; the final test-run gate is the backstop, not a second owner). Write `Not applicable; plan declares floor-verification scope none.` or `Owned by the final gate per the plan's declaration.` otherwise. Never install into the shared `.venv`.

- scratch venv path (outside the repo), resolved versions as read by `uv pip list --python <venv>/bin/python`, the focused scope run, pass/fail.

### Implementation notes

Design choices the plan did not explicitly fix — `__dict__` vs `vars()`, the shape of a shared helper, the fixture pattern chosen, a tuple-of-pairs vs parallel-list constant, the import path of a third-party utility. One bullet per non-trivial decision with a one-line "why this shape." Worker 3 reads these to follow the reasoning without reverse-engineering the diff; Worker 1 reads them at final verification to spot drift from the plan.

If a decision is structural enough to count as plan-vs-implementation drift (see `worker-2.md` "Plan-vs-implementation drift"), surface it in `### Notes for Worker 1 (spec reconciliation)` instead — that is the louder signal.

### Notes for Worker 3

Anything Worker 3 should know before reviewing (shadow file used, unusual control flow, etc.).

### Notes for Worker 1 (spec reconciliation)

If the implementation surfaced a spec gap, conflict, or unstated assumption, record it here. Worker 1 reads this section during final verification and decides whether to edit the spec.

---

## Review (Worker 3)

### High:

#### Issue name

Issue summary, why it matters, and the recommended change.

```path/to/file.py:NN:MM
Relevant excerpt or pseudo-diff context.
```

### Medium:

### Low:

### DRY findings

- Duplication observed (cite file:line in both sites)
- Repeated literal / key / tuple
- Near-copy of existing helper that should be consolidated

### Public-surface check

Confirm `git diff -- django_strawberry_framework/__init__.py` does not change `__all__` or the re-export list, OR confirm any change is authorized by the active spec (cite the spec line). Definition-of-done items typically pin "no new public exports"; this check makes that explicit per review.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

If the slice's diff includes a change to `CHANGELOG.md`, read the new entry end-to-end and confirm:

- the version line matches `pyproject.toml` and `django_strawberry_framework/__init__.py`
- `### Added` / `### Changed` / `### Fixed` / `### Removed` headings used are the ones the active spec authorizes
- the wording matches the canonical phrasings the plan committed to (or reads coherently against the actual behavior shipped)
- nothing overstates or understates the change

If the slice does not touch `CHANGELOG.md`, write `Not applicable; slice did not modify CHANGELOG.md.`.

### Documentation / release sanity (only when the slice touches docs, release metadata, KANBAN, or archived specs)

If the slice's diff includes documentation, release metadata, KANBAN movement, or spec archival, read the changed files end-to-end and confirm:

- version strings, shipped/planned statuses, and card IDs match the active spec and the package version after the slice
- moved KANBAN cards are removed from their old section and appear in the target section exactly once
- Markdown links introduced or moved by the slice point at existing files or documented future files
- active-spec archival, if planned, preserves the historical record and leaves the live follow-up source of truth in the durable doc named by the spec
- when the slice copies verbatim text from the spec (e.g. KANBAN card bodies, CHANGELOG entries, GLOSSARY.md entry text), confirm character-for-character via `diff` against the spec source; for fenced-code drop-ins where the inner fence backtick count matches the outer, confirm the outer fence used four backticks (or another non-conflicting form) so markdown rendering is intact
- no obsolete "coming soon", "planned", or old-version wording remains in files the slice deliberately updated
- when the slice regenerates a **script-rendered** doc (a tree/index rendered from source module docstrings), confirm the feeding docstrings carry no **staging** language — "planned", "Slice N", "after Slice N", `TODO(` — that would render now-shipped behavior as unbuilt; the docstring fix and the regenerate land in the SAME change (a hand-edit of the generated doc is reverted by the next render). Distinguish staging docstrings (scrub) from provenance comments citing a spec as design rationale (keep, per `AGENTS.md` "shipped behavior folds into `docs/TREE.md`")

If the slice does not touch those surfaces, write `Not applicable; slice did not modify docs/release/KANBAN/archive surfaces.`.

### What looks solid

- Thing one.
- Thing two.

### Temp test verification

- Temp test files used during review (cite paths).
- Disposition: kept and promoted to a permanent test, deleted, or noted for follow-up.

### Notes for Worker 1 (spec reconciliation)

Flag anything Worker 1 should weigh during final verification (spec ambiguity, possible spec edit, follow-up slice candidate).

### Review outcome

`review-accepted` (every High/Medium/Low finding addressed or intentionally rejected with a recorded reason) or `revision-needed`. Setting this also updates the artifact's top-level `Status:` line.

---

## Re-pass sections

Each Worker 2 re-pass appends `## Build report (Worker 2, pass <N>)` at the same top level (NOT nested); each Worker 3 re-review appends `## Review (Worker 3, pass <N>)` the same way. The artifact reads as a linear pass / review / pass / review sequence; never edit prior entries.

---

## Final verification (Worker 1)

- Spec slice checklist: every `- [ ]` in the Plan's `### Spec slice checklist (verbatim)` is `- [x]` (the contract landed), or has a one-line deferral reason under `### Spec changes made (Worker 1 only)`. Silently un-ticked boxes block `final-accepted`.
- DRY check across this slice and prior accepted slices: any new duplication?
- Existing tests still pass: `uv run pytest <focused scope>`.
- Spec reconciliation: does the spec need a Worker 1 edit to reflect what landed?
- Final status: `final-accepted` or `revision-needed`.

### Summary

A short summary of what this slice shipped.

### Spec changes made (Worker 1 only)

If the spec was edited as part of this slice, cite the spec lines and a one-line reason per change.
````

If a severity has no issues, keep the heading and write `None.` under it. Do not include speculative defects.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

[build-md]: BUILD.md

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
