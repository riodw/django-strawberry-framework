# Build: Slice 2 — Spec reconstruction + rationale authoring (card `DONE-024-0.0.7`)

Spec reference: `docs/SPECS/spec-024-django_trac_37064_hardening-0_0_7.md` (rewritten in place by this slice; it was a 1,618-byte card-snapshot stub carrying no contract)
Status: final-accepted

Inputs consumed, all three read in full including every review section:

- `docs/builder/bld-slice-1a-024-planned_vs_head.md` (planned-vs-HEAD gap audit)
- `docs/builder/bld-slice-1b-024-divergence_and_floor.md` (post-ship divergence catalog, contract flips, floor run)
- `docs/builder/bld-slice-3-024-rename_rot_sweep.md` (rename-rot sweep and citation repair)

Read-only inputs: `docs/builder/temp-tests/PLAN-024.md`, `docs/builder/temp-tests/TEMP-024.md`, and the eight subject source/test files.

HEAD at this pass: `f466863a`. It touches none of card 024's six surface files, so no count inherited from a Slice 1 artifact needed re-deriving on that account — though every count restated below was re-derived anyway.

## Plan (Worker 1)

### DRY analysis

**Helper inventory checked** — not applicable in its usual form: this slice writes no Python and proposes no helper. The package-wide AST inventory was not refreshed because the slice adds zero lines of logic to any `.py` file; `worker-1.md` `### Package-wide helper inventory before helper planning` gates *helper planning*, and there is none.

The DRY question this slice does face is documentary, and both reviews raised it. Slice 1a states its deferred items in three places; Slice 1b states the same eight changes twice, once as a divergence catalog and once as contract flips, and that duplication is what let two of its entries disagree. **Resolution: single-source in the output.** Each contract flip is stated exactly once as contract in the spec and exactly once as a retired claim in the rationale, cross-referenced by Decision anchor rather than restated. The deferred-work catalog below is one list, not a per-artifact union of three lists pasted together.

### Implementation steps

1. Read the three Slice 1 artifacts in full, the recovered planning documents, the eight subject files, and the shape references `docs/SPECS/spec-023-multi_db-0_0_7.md` and `docs/SPECS/appx/spec-023-multi_db-0_0_7-rationale.md`.
2. Re-derive the escalated decision's deciding measurement from the blobs, decide it, and record both the decision and the rejected reading.
3. Rewrite `docs/SPECS/spec-024-django_trac_37064_hardening-0_0_7.md` as a clean current contract in the section shape spec-023 uses, keeping the filename (spec-021 links to it by that name).
4. Author `docs/SPECS/appx/spec-024-django_trac_37064_hardening-0_0_7-rationale.md`, keyed to the spec by Decision heading and anchor.
5. Verify: glossary check, markdown scaffold, disk-exists on every link-def path, anchor resolution, symbol resolution, hash reachability.
6. Final-verify Slices 1a, 1b, and 3; append a final-verification section to each and set `Status:`.
7. Assemble the deferred-work catalog as the union of all three artifacts' lists, re-derived rather than copied.

### Test additions / updates

None, and none are owed. This slice writes two Markdown files and touches no `.py` file, so there is no behaviour to pin. The focused scope is re-run as a regression check that the tree is green at close, not as new coverage.

### Implementation discretion items

None. The one question that could have been delegated — where the rationale's change record starts — is explicitly *not* discretionary: `docs/builder/BUILD.md` `## Spec reconciliation` makes it the custodian's, and it is decided under `### Spec changes made (Worker 1 only)` below.

### Spec slice checklist (verbatim)

Not applicable. The archived spec was a card-snapshot stub with no `## Slice checklist` to copy; the whole point of this slice is that the spec had no contract to check against. The build plan records the same fact under `## The input contract (recovered, not invented)`.

---

## Build report (Worker 1, acting as author under the cycle's recorded dispatch deviation)

### Files touched

- `docs/SPECS/spec-024-django_trac_37064_hardening-0_0_7.md` — **rewritten in place**, filename unchanged. 1,618 bytes -> 42,077 bytes (`wc -c`, measured at close).
- `docs/SPECS/appx/spec-024-django_trac_37064_hardening-0_0_7-rationale.md` — **new**, 46,443 bytes (`wc -c`, measured at close).
- `docs/builder/bld-slice-2-024-spec_reconciliation.md` — this artifact (new).
- `docs/builder/bld-slice-1a-024-planned_vs_head.md`, `docs/builder/bld-slice-1b-024-divergence_and_floor.md`, `docs/builder/bld-slice-3-024-rename_rot_sweep.md` — one appended `## Final verification (Worker 1)` section each, and the top-level `Status:` set to `final-accepted`. No body or review section was altered.
- `docs/builder/worker-memory/worker-1-024.md` — one appended entry (gitignored).

**No `.py` file was written.** `git status --short` at close shows one dirty `.py` under this cycle, `django_strawberry_framework/_strawberry_patches.py`, which is Slice 3's one-line repair and was neither touched nor reverted here. `django_strawberry_framework/optimizer/hints.py` and `tests/optimizer/test_hints.py` are a concurrent cycle's, as are the `spec-021` / `spec-022` edits and the `025` / `026` build plans that appeared during this pass. The terms CSV was not touched: this rewrite introduced no new glossary term, and `check_spec_glossary.py` still reports `OK: 2 terms`.

### Tests added or updated

None (this slice writes Markdown only).

### The spec, as rewritten

Eleven numbered Decisions, in the section shape `docs/SPECS/spec-023-multi_db-0_0_7.md` uses, scaled to a relative-size-**S** card. Each states the contract that exists at HEAD directly. **No amendment block, no retraction paragraph, no "as of review round N", no "originally X, now Y" survives anywhere in the spec** — every reversal is stated as the corrected contract and its history lives in the companion.

| Decision | Contract stated |
|---|---|
| 1 | A private patch module per third-party dependency, dispatched from `ready()` behind function-local imports. |
| 2 | The install target is `SimpleTestCase` — Django's definition site — so the hierarchy inherits it. |
| 3 | The replacement reimplements upstream's loop behind one `isinstance` guard, reading the pair list through one helper. |
| 4 | Fail-closed validation in three tiers; a missing `_DatabaseFailure` **raises** rather than no-opping; unreadable source is drift. |
| 5 | Exactly two audited upstream bodies with their Django ranges; the **validated body source** is the discriminator, not `hasattr`; widening the set is an audit, not a version bump. |
| 6 | `APPLY_UPSTREAM_PATCHES` in both bool and per-dependency-mapping forms, read as `apply()`'s first statement. |
| 7 | Idempotent, self-healing, and reload-safe via the stamped owner/original attributes. |
| 8 | The wrap-time helper's return contract, its non-interpolating `TypeError`, and the deliberate asymmetry that it degrades where `apply()` aborts — with the test that pins it. |
| 9 | Submodule export only; `__all__` unchanged by this card, stated without a count. |
| 10 | Coverage lives in the package test tree, with the reason it cannot live in the live tier. |
| 11 | Joint `0.0.7` cut. |

Plus `## Problem statement`, `## Current state`, `## Goals`, `## Non-goals`, `## Borrowing posture`, `## User-facing API` (with the worked `setUp`/`tearDown` shape and the three error shapes), `## Implementation plan`, `## Edge cases and constraints`, `## Test plan` (this card's 31 tests enumerated by contract, distinguished from the 36-test focused run scope, plus the floor-verification scope; the section originally claimed 36 as the card's own population and was corrected under M1), `## Doc updates`, `## Risks and open questions`, `## Out of scope`, and a 12-item `## Definition of done` reflecting what actually shipped.

Two facts the spec states that the recovered documents did not, both because they are contract at HEAD and neither is history: the `django_strawberry_framework.testing` import path (the `test/` -> `testing/` rename appears nowhere in the spec, only in the rationale as the reason), and the gate-before-validation ordering, which is what makes `{"django": False}` a working recovery path from a drifted-pin abort.

### The rationale, as authored

Provenance section states plainly that this was a **reconstruction, not an extraction**, and why: there was nothing to move. It names both recovered planning documents, records that both were deleted at `d1d19ca2` and recovered from `d1d19ca2^`, and records that both recovered copies are byte-identical to their `d1d19ca2^` blobs. It also names the weakness a reconstruction has that a move does not — where a commit message does not state a cause, the cause is an inference — and every such entry says so in place.

Then: the change-record decision and the reading rejected; the 21-commit change record with in-tag / post-tag marked per row; eleven per-Decision entries each carrying **alternatives rejected with the reason each lost**, **changes the Decision underwent with the commit that made them**, and **claims the Decision may no longer make**; a consolidated `## Claims the spec may no longer make`; and `## Verified against the shipped code`.

The four the task named specifically, all present:

- **The "no settings escape hatch" reversal**, with its justification ("strictly defensive — never makes Django's behaviour worse") named as the half that **collapsed**, and the moment it collapsed identified: the patch became able to refuse to boot. The surviving true use of that sentence — in `_patched_remove_databases_failures`'s own docstring, describing the replacement body — is distinguished from the retired one.
- **The fail-loud reversal**: the planned INFO-notice no-op became a hard `RuntimeError` at `48f9f65d`, with both retired tests named (`test_apply_no_ops_when_database_failure_symbol_missing`, `test_apply_logs_missing_symbol_notice_only_once`) and the note that they were deleted, not renamed.
- **The discriminator's history**: `hasattr(cls, …)` documented as a *feature* at `eb2a1764` and named a *bug* at `18550f5d`, ten days later, with the sentence the task asked for stated explicitly — a future "simplification" back to `hasattr` reintroduces a known defect — and the mechanism given as the reason: `_add_databases_failures` ignores a 6.1 subclass's legacy attribute and wraps the feature list, so cleanup must read that same list to stay symmetric.
- **Every other contract flip** the artifacts establish: the install target, the import path, the unconditional-patch stance, any-body-superseded -> audited-only, the `_PATCH_APPLIED` flag, and the `TypeError` interpolation.

### Validation run

- `uv run ruff format` / `ruff check --fix` — **not run**: this slice touched no `.py` file. Ruff's write mode is not run on Markdown.
- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-024-django_trac_37064_hardening-0_0_7.md` -> `OK: 2 terms - all have glossary entries and at least one spec link.`, **exit 0**.
- `uv run python scripts/check_trailing_commas.py --check` on both new files -> **exit 0**, silent.
- `uv run pytest tests/test_django_patches.py tests/testing/test_wrap.py tests/test_apps.py tests/test_strawberry_patches.py --no-cov -q` -> **91 passed in 2.60s**, 0 failures, 0 collection errors. No `--cov*` flag was used anywhere in this pass.
- `git status --short` at close — the entries attributable to this pass are the two spec files, this artifact, and the three appended final-verification sections. Nothing else. Nothing reverted, nothing tidied.

### Verification performed on the two authored files

Every one of these was run against the files as written, not assumed.

| Check | Instrument | Result |
|---|---|---|
| Link-def paths exist on disk | resolve each `[ref]: path` against the file's own directory | **0 missing**, both files |
| In-page anchors resolve | GitHub-slug every heading; resolve every `](#…)` | **0 broken**, both files |
| Cross-file anchors resolve | same, across the spec/rationale pair | **0 broken** (11 rationale-side Decision anchors from the spec, 11 spec-side from the rationale) |
| Reference-style only, one `<!-- LINK DEFINITIONS -->` block, all 10 canonical group headers in order, alphabetical within group | `check_trailing_commas.py --check` | **pass** |
| Undefined ref-id uses | set difference of uses against defs | **0**, both files |
| Backticked identifiers resolve whole-token at HEAD | AST index of every name defined/bound/attributed in every non-`docs` `.py`, resolved against every backticked span outside fenced blocks | **0 invented names.** Every non-resolving span is an upstream Django/`unittest`/`debug_toolbar` symbol (`_add_databases_failures`, `setUpClass`, `tearDownClass`, `tearDown`, `wrap_cursor`), a settings-key or dependency-name **string** (`APPLY_UPSTREAM_PATCHES`, `cross_web`), a Python keyword/literal, or a deliberately-cited retired symbol |
| Retired symbols appear only in the rationale | whole-token search of both files | `_PATCH_APPLIED`, `_missing_symbol_logged`, `test_apply_no_ops_when_database_failure_symbol_missing`, `test_apply_logs_missing_symbol_notice_only_once` -> **0 occurrences in the spec, all in the rationale**, every one in retirement-describing prose |
| Every `path::Symbol` citation resolves | AST-parse the cited file, resolve the qualified name | **0 unresolved**, both files |
| Every test name cited exists | resolve against the three test modules | **31 distinct names cited in the spec, all live**; the 2 retired names are in the rationale only |
| Every `#"substring"` citation is unique in its target | count occurrences in the cited file | **12 citation occurrences** (8 in the spec, 4 in the rationale) over **7 distinct (target, substring) pairs**; each pair resolves to **exactly 1** occurrence in its named file. The figure originally recorded here, 4, was the count of the *path-qualified* citations only (`conf.py #"UPSTREAM_PATCH_DEPENDENCIES = frozenset("`, `_django_patches.py #"WIDENING…"` x2, `__init__.py #"__all__ = ("`); the other 8 occurrences are `AGENTS.md`-anchored. Corrected under L2 |
| Every commit hash is HEAD-reachable | `git merge-base --is-ancestor <sha> HEAD` per distinct 8-hex token | **27 distinct tokens, 27 reachable, 0 orphans** |
| No raw `path:NN` in either file | search for a `.py:` or `.md:` line-number form | **0** |

### Counts re-derived for this pass rather than inherited

`docs/builder/BUILD.md` `## Claims are proven mechanically, never accepted on prose`: every number written into the two permanent files was measured while it was being written, as **occurrences** from the shortest distinctive token.

- HEAD test counts: `tests/test_django_patches.py` **21**, `tests/testing/test_wrap.py` **7**, `tests/test_apps.py` **8** = **36**, reconciling with the 36-item focused run.
- Surface population: `--follow` union over the six files = **23**, minus `b972cd84` / `dfa035b4` (2026-05-21, pre-ship `AppConfig` work) = **21**; split **6 in-tag / 15 post-tag** measured per commit with `git merge-base --is-ancestor <sha> 0.0.7`.
- Test-count progression, per commit on the extracted blob: **6, 10, 11, 12, 13, 13, 17, 17, 20, 21** across `300e2811`, `7014125a`, `744fd28d`, `e82df83d`, `c7cb5f5c`, `48f9f65d`, `0d655bde`, `136c5476`, `eb2a1764`, `18550f5d`. `c7cb5f5c` owns the 12 -> 13 step and `48f9f65d` is net zero — the correction Slice 1's own apply-changes pass found, and it reproduces.
- Wrap decomposition: **4** (`61973f8d`) **+ 2** (`7014125a`) **+ 1** (`f7fbead4`) = 7 at HEAD.
- `_django_patches.py`: **91** lines at `300e2811`, **406** at HEAD.
- Stub size: **1,618** bytes (`git show HEAD:<spec path> | wc -c`). The dead `1,536` figure was not inherited from any document.
- Audited set size: **2** members; both discriminator read branches present.

### Failability proofs

`None; this pass introduced no new boundary.` The slice edits Markdown only — no guard, gate, rejection path, or invariant is added, moved, or altered, which is the "doc edits" exemption in `docs/builder/BUILD.md` `### What needs a proof, and what does not`. The obligation that does apply is the stated-count rule, discharged above.

### Hot-path budget

`Not applicable; plan declares no hot path.` The build plan's `## Declarations` sets the cycle's hot-path declaration to `none`, and this slice changes no code.

### Floor verification

`Owned by Slice 1b per the plan's declaration.` It was run there and independently re-executed in full by that slice's review, and is accepted at final verification without a second run — `worker-1.md` `## Final test-run gate` makes the gate the backstop confirming a floor run happened, not a second owner, and rebuilding `/tmp/dsf-floor-024` would destroy the artifact a later reader re-derives from. No `uv pip install` was issued by this pass, into that venv or the shared `.venv`.

### Implementation notes

- **The spec was written from the artifacts' `### Notes for Worker 1` sections and then checked against source, not the other way round.** Two of the notes needed correcting on the way in and both are recorded under `### Spec changes made (Worker 1 only)`.
- **Decision granularity was chosen to make the reversals addressable.** The escape hatch and the fail-closed validation could have been one Decision — they are one mechanism in the code, since the gate exists to recover from the abort. They are two, because the rationale's job is to be looked up by decision, and "no settings key" and "degrade on a missing symbol" are two separately-reversed claims a reader will arrive with. The spec states their coupling in both directions rather than merging them.
- **In-page anchors stayed inline** and cross-file anchors are reference-style, per `START.md`'s explicit carve-out. Every rationale Decision is reachable from its spec Decision by a `[Decision N][rationale-dN]` def and back by `[Decision N][spec-024-dN]`.
- **Every heading slug was computed and resolved rather than guessed.** A dotted version in a heading slugs to `007`, and an em dash surrounded by spaces slugs to a double hyphen; both bite silently.

### Notes for Worker 3

- The diff is two Markdown files plus three appended final-verification sections. There is nothing to review in source.
- The three highest-value things to re-derive: the two-line `PLAN-024.md` upper-bound diff against its `7014125a` blob (it decides the change-record start point); the backticked-symbol sweep over both authored files (this cycle has already caught two invented or stale symbol names in its own artifacts); and the deferred-work catalog's counts, every one of which is a claim.
- One correction to a Slice 3 finding is recorded in the catalog below rather than applied silently — it makes that finding's number *more* right, not less.

### Notes for Worker 1

None owed to a later custodian pass: this slice is the custodian pass. Nothing was found that requires a `.py` change, so no escalation is raised under this heading. The one source-shaped item found — the duplicated docstring fragment in `_strawberry_patches.py` — is pre-existing at HEAD, is not rename rot, and is routed to the deferred-work catalog rather than repaired, since repairing it here would broaden this slice past a Markdown-only contract.

### Spec changes made (Worker 1 only)

The whole spec is a change: `docs/SPECS/spec-024-django_trac_37064_hardening-0_0_7.md` went from a 1,618-byte card-snapshot stub carrying no contract to a full builder-format spec. The filename is unchanged, deliberately — `docs/SPECS/spec-021-apps-0_0_7.md` links to it by that name and that link resolves at close. Rather than enumerate every sentence, the entries below record the **decisions taken while writing it**, which is what a later reader cannot recover from the diff.

#### 1. The escalated decision: where the rationale's change record starts

**Decided: the change record starts at the ship commit `300e2811` (2026-05-23).** Every commit that moved the surface is in the record, each marked in-release or post-tag.

**Rejected: the record starts at the recovered plan's baseline `7014125a`.** Two reasons.

- *The record's subject is the card, not the recovered document.* Card `DONE-024-0.0.7` shipped `300e2811`. A change record whose origin is set by which deleted file happened to survive in git is a record of that file, not of the card. Slice 1a's reading is internally sound — the plan does post-date `7014125a`, so from the plan's point of view those four changes are not divergences — but it answers a different question from the one the rationale exists to answer.
- *It silently loses two contract flips.* `7014125a` retargeted the install from `TransactionTestCase` to `SimpleTestCase` and replaced the `_PATCH_APPLIED` flag with `_patch_is_installed()`. Both are claims a reader of the shipped `0.0.7` artifact would still hit. Under the rejected reading they either vanish or must be re-stated as "the plan already describes the corrected form" — a chronology hedge about a deleted document, which is exactly the shape `docs/builder/BUILD.md` `## Spec rationale extraction` forbids the spec and this file exists to hold properly instead.

**Cost of the chosen reading, accepted:** the record opens with four days of in-release churn the plan never saw. That is handled by marking in-tag membership per row, which is a measurement (6 of the 21 surface commits are ancestors of tag `0.0.7`) rather than a framing.

**The deciding measurement, re-derived by this pass rather than inherited from either artifact.** Read-only, into a scratch path outside the repo, no `stash` / `checkout` / `restore` / `worktree`:

```shell
git show 7014125a:docs/TEMP-trac-37064-test-plan.md         > <scratch>/temp-7014125a.md
git show 7014125a:docs/PLAN-trac-37064-database-teardown.md > <scratch>/plan-7014125a.md
git show 'd1d19ca2^:docs/TEMP-trac-37064-test-plan.md'      > <scratch>/temp-final.md
git show 'd1d19ca2^:docs/PLAN-trac-37064-database-teardown.md' > <scratch>/plan-final.md
diff <scratch>/temp-7014125a.md docs/builder/temp-tests/TEMP-024.md   # rc=0, identical
diff <scratch>/plan-7014125a.md docs/builder/temp-tests/PLAN-024.md   # rc=1, hunks 92c92 and 115c115
diff <scratch>/temp-final.md    docs/builder/temp-tests/TEMP-024.md   # rc=0
diff <scratch>/plan-final.md    docs/builder/temp-tests/PLAN-024.md   # rc=0
```

`TEMP-024.md` is byte-identical to its `7014125a` blob. `PLAN-024.md` differs from its `7014125a` blob by exactly two lines — `92c92`, an `AGENTS.md` line-number citation rewritten to the symbol-qualified form (`df547235`), and `115c115`, a `spec-019-…` path gaining its `SPECS/` prefix (`974189ad`). Line 92 sits **inside decision D-4's own bullet** and line 115 **inside DoD item 9's version-target sub-bullet**; what neither *changes* is a decision's content, a DoD item's content, or a test name. Both recovered files are byte-identical to their `d1d19ca2^` blobs, so the recovery is faithful. **Both planning documents therefore describe the tree at exactly `7014125a`.**

**The consequence, carried into the rationale under Decision 4:** the log-once **sentinel** (`744fd28d`, 2026-05-26T15:09, after the plan's last content-bearing write at 10:21) was never in the planned contract. What the plan promised was the missing-symbol *no-op with one INFO notice* — `7014125a`'s state, where the docstring claimed "a single INFO-level notice" over an `apply()` that logged on every call. The sentinel was built to make an already-shipped claim true, and was deleted six weeks later. The rationale describes it that way and never as a planned deliverable.

#### 2. Corrections applied to the artifacts' notes on the way into the spec

- **Slice 1a's item 7 plural, fixed** (the Low its third review left open). The spec states that `_captured_upstream_descriptor` compares the **owner attribute** against the `_PATCH_OWNER` value and returns the **original attribute's** value when the comparison holds — only one of the two attributes is matched against anything. Re-read from `django_strawberry_framework/_django_patches.py::_captured_upstream_descriptor`, not from the note.
- **Slice 1a's item 9 honoured:** the `__all__` claim is stated **without a count**, as "no symbol from this card entered the root `__all__`, not at the ship and not since". The rationale carries the reason a count would be rot. One correction to the note's own vocabulary: `__all__` in `django_strawberry_framework/__init__.py` is a **tuple**, not a list; the rationale says tuple.
- **Slice 1b's `docs/TREE.md` line numbers were not carried**, per its own non-transferable flag. The spec states the obligation as prose with the three package modules named by full path.
- **Slice 1a's L1 wording was not inherited.** The two-line `PLAN-024.md` delta is described as "mechanical reference rewrites carrying no contract", with the replacement wording naming where the two lines sit and what they leave unchanged.
- **The dead `1,536`-byte figure was not inherited from any document.** Re-measured: `git show HEAD:<spec path> | wc -c` -> **1618**.

#### 3. Deliberately not stated in the spec

- Any chronology. No amendment block, no "as of", no "originally X, now Y", no revision history. Every reversal reads as the corrected contract.
- Any commit hash. The spec names no commit; all 27 live in the rationale and the change record.
- The `test/` -> `testing/` rename, the log-once sentinel, the `_PATCH_APPLIED` flag, the single-body pin, and the `hasattr` discriminator. All five are retired states and all five are in the rationale. **Four of the five were kept out of the spec; the single-body pin was not, and the claim that none is in the spec was false when it was written** (M2). `## Risks and open questions` carried "the single-body pin of the day matched neither shape", which is a retired contract state of this spec. The apply-changes pass rewrote that bullet to state the present pin behaviour and the Django `6.1` fact without the timeline, so the claim is now true; it is recorded here as corrected, not as having held. Re-derived over the spec as it now stands, occurrences not matching lines: `_PATCH_APPLIED` **0**, `_missing_symbol_logged` **0**, `test_apply_no_ops_when_database_failure_symbol_missing` **0**, `test_apply_logs_missing_symbol_notice_only_once` **0**, `logger` **0**, `single-body` **0**, `single pin` **0**, `test/` **0**. `hasattr` is **2 occurrences, both on one line**, stated as a prohibition on a future change rather than as history, and stays.
- A member count for the root `__all__`, or any other number a card that does not own the list would be asserting with a silent verification date.

### Deferred work catalog

Items 1-6 are the union of all three Slice 1 artifacts' deferred lists; item 7 was raised by this cycle's apply-changes pass while fixing M1. **Neither cohort's list is complete alone** — 1a and 1b overlap only on `docs/GLOSSARY.md`, and Slice 3's is disjoint from both. Every count below was **re-derived at this pass**, not copied; two of them moved, and both are noted in place. A catalog is a claim.

Everything here is outside this cycle's maintainer-set scope (spec files and `.py` files only, no closeout or agentflow edits) or outside card 024's ownership.

1. **`CHANGELOG.md`'s `0.0.7` hardening entry carries two claims that are false at HEAD, and sits under the wrong heading.** The entry says consumers need "no settings key" — `APPLY_UPSTREAM_PATCHES` exists — and that "a log-once sentinel suppresses repeated missing-symbol notices" — the sentinel arrived at `744fd28d` and was deleted at `48f9f65d`; `grep -c logger django_strawberry_framework/_django_patches.py` -> **0**. It also landed under `### Added` where the recovered plan's DoD item 9 asked for `### Fixed`. Re-measured at this pass: both false clauses are present, in a single bullet under `## [0.0.7]` -> `### Added`. Low. `CHANGELOG.md` is baseline-dirty and excluded by this cycle's scope.
2. **`docs/GLOSSARY.md`'s `## Django Trac #37064 hardening` entry is stale.** Re-read at this pass: it says "no `conftest.py` workaround, no base test class to inherit, **no settings key required**" — true only on that last word — and describes the patch as unconditional. The audited-body pin, the fail-loud `RuntimeError`, and `APPLY_UPSTREAM_PATCHES` are absent from it entirely. The `safe_wrap_connection_method` entry was not audited by this cycle. Worth a wording pass when the GLOSSARY surface is next in scope. Note `docs/GLOSSARY.md` is DB-generated: the fix is a DB edit plus a re-render, never a hand edit.
3. **`docs/TREE.md` is an unstated consumer of card 024's module summary lines — and the population is larger than the artifacts state.** Slice 1b recorded two module summary lines. Re-derived at this pass by matching each module's own docstring first line against `docs/TREE.md`: **six distinct summary lines, twelve occurrences** (each renders twice, once per view) — `django_strawberry_framework/_django_patches.py`, `django_strawberry_framework/apps.py`, `django_strawberry_framework/testing/_wrap.py` (set by `4a25bf42`), and `tests/test_apps.py`, `tests/test_django_patches.py`, `tests/testing/test_wrap.py` (set by `7c2a63ed`). A docstring edit to any of the six needs a `build_tree_md.py` regenerate in the same change. The spec states the obligation for the three package modules; the test-module half belongs to whichever pass next owns `docs/TREE.md`.
4. **Seven citation defects in `.py` docstrings and comments belonging to other cards.** All are `.py` files, so all are *eligible* work a future cycle can pick up; none is card 024's, because `AGENTS.md` #"Source refs in docs and code comments use symbol paths never line numbers" binds the sweep to the change that renamed the symbol. Counts re-derived at this pass, occurrences not matching lines, over `django_strawberry_framework/`, `tests/`, `examples/`, `scripts/`:
   - `django_strawberry_framework/utils/relations.py #"mutations/inputs.py::_select_editable_fields"` — **1**. `_select_editable_fields` has **never been defined at any revision**; a never-true citation.
   - `django_strawberry_framework/utils/relations.py #"mutations/resolvers.py::_index_relation_fields"` — **1**. Same shape: never defined anywhere in history.
   - `django_strawberry_framework/utils/querysets.py #"mutations/resolvers.py::_raw_pk_relation_error"` — **1** in the package. Defined once and removed at `e9c13f55` without the sweep.
   - `django_strawberry_framework/utils/querysets.py #"mutations/resolvers.py::_relation_membership_error"` — **2**. Same commit, same omission.
   - `django_strawberry_framework/utils/querysets.py #"forms/resolvers.py::_visible_related_object"` — **1**. The symbol exists but in a different module (`django_strawberry_framework/types/resolvers.py::_visible_related_object`); a wrong-module citation, which resolves for a human and not for a tool.
   - `django_strawberry_framework/consumers.py #"auth/mutations.py::logout"` — **1**. The symbol is `logout_mutation`; there is no bare `logout`.
   - The renamed optimizer test — **3 occurrences in 2 files**: `tests/test_list_field.py` (2) and `examples/fakeshop/test_query/test_scalars_api.py` (1). This is Slice 3's review correction, and re-deriving it turned up one more thing worth carrying: an **unanchored substring** sweep over the same declared corpus returns **7 occurrences in 4 files** — `tests/test_list_field.py` 2, `examples/fakeshop/test_query/test_scalars_api.py` 2, `tests/optimizer/test_extension.py` 2, `tests/test_permissions.py` 1 — of which only the 3 above are rot; the rest cite live `…_selection_plan_shape` / `…_for_each_alias_plan_shape` names. The **4** originally recorded here was the unanchored sweep run over a two-file corpus (`tests/test_list_field.py`, `examples/fakeshop/test_query/test_scalars_api.py`), not over the corpus this item declares; the number and the corpus disagreed, which is the defect M3 names. Both figures re-derived at this pass with `grep -ro` (occurrences) and `grep -rEo '…([^A-Za-z0-9_]|$)'` (end-anchored) over `django_strawberry_framework/`, `tests/`, `examples/`, `scripts/`. Anchoring the sweep at the identifier's end is what separates the retired bare name from the live suffixed ones — the same instrument trap as `_unpatched` in Slice 3's own table, one directory over.
5. **Contract-level, escalated to the maintainer — no gate in this process resolves a symbol citation.** `eb2a1764` passed tests, ruff, and review and still shipped a dangling cross-module citation that survived four months. `AGENTS.md` rule 27 states the obligation and nothing mechanically enforces it. Three paths, the maintainer's to choose between: (a) commit the reviewer's `scripts/check_citations.py` and wire it as a pre-commit hook, making the rule mechanical the way `check_trailing_commas.py` and `check_spec_glossary.py` already are — `scripts/` sits outside the coverage gate, so this adds no coverage obligation; (b) commit it CI-only, catching it before merge rather than before commit; (c) accept per-cycle re-derivation. **The measured cost of (c) in this cycle alone is nine citation defects in three kinds:** one in-scope repair, seven out-of-scope findings, and one invented symbol name (`_PATCH_ORIGINAL`) produced *inside* this cycle by a pass whose subject was citation correctness — caught only by a throwaway resolver written for the review. No worker may decide this.
6. **A pre-existing duplicated docstring fragment in a writable file.** `django_strawberry_framework/_strawberry_patches.py #"Three lifecycles, and one that left"` opens with a dangling truncated clause — `independent upstream *bugs* that do not retire together:` stands alone immediately before the complete sentence that contains it. Confirmed present at HEAD at this pass, so it is pre-existing and not in any of this cycle's diffs. It is a copy-paste artifact rather than rename rot, so Slice 3 correctly declined it as outside its contract, and this slice declines it as outside a Markdown-only contract. The fix is a one-line deletion and it needs an owner: whichever pass next owns that docstring.

7. **`docs/SPECS/spec-021-apps-0_0_7.md` claims the three `ready()` tests in `tests/test_apps.py` as its own deliverable; git says card 024 contributed them.** Raised by M1's fix and left as a cross-surface inconsistency rather than partial-fixed, because `spec-021` is baseline-dirty from a concurrent cycle and outside this cycle's scope. Measured at this pass: `tests/test_apps.py` held **5** tests at `300e2811^`; `300e2811` added `test_djangostrawberryframeworkconfig_defines_ready_for_django_patches`, `136c5476` added `test_ready_dispatches_all_three_patch_appliers_and_refires_safely`, and `18550f5d` added `test_ready_reinstalls_patches_after_their_modules_reload` — all three are card 024 surface commits already in the rationale's change record. `spec-021`'s Slice-2 step ("Ship `tests/test_apps.py` containing ... and the three tests pinning `ready()` and its dispatch") and its DoD item 4 ("contains the 8 tests listed in the Test plan ... and 3 pinning `ready()`") both read as spec-021 deliverables. `spec-024` now states its own population as **31** and names the other five as spec-021's, so the two specs disagree about who delivered the three. The maintainer's call: either `spec-021` reframes the three as a file-content fact contributed by the sibling card (its own line 350 already says the `ready()` body "arrives with sibling card `DONE-024-0.0.7`"), or `spec-024` gives them up. A spec-only correction on the un-editable side would be worse than uniformly-wrong, so nothing was changed there.

---

## Review (Worker 3)

Reviewed: `docs/SPECS/spec-024-django_trac_37064_hardening-0_0_7.md` (42,077 bytes, 11 Decisions),
`docs/SPECS/appx/spec-024-django_trac_37064_hardening-0_0_7-rationale.md` (46,443 bytes), and this
artifact's plan, build report, escalated-decision record, and deferred-work catalog. HEAD at this pass
is `ddf8bbaf` (moved again mid-cycle from `f466863a`); it touches none of card 024's six surface files.
Concurrent cycles 025 and 026 are visibly live in the tree and are out of scope.

**Every mechanical gate below was re-run, not accepted.** Failability proofs: none owed and none
re-run — the slice writes Markdown only and introduces no boundary, so the re-run set is legally empty
per `docs/builder/BUILD.md` `### What needs a proof, and what does not`. No `--cov*` flag was used.
No source file was mutated; the transient-mutation carve-out was not exercised.

### High: None.

### Medium:

**M1 — the spec's Test plan and DoD 9 claim a whole test module a sibling spec owns.**
`docs/SPECS/spec-024-django_trac_37064_hardening-0_0_7.md` `## Test plan` opens "36 tests across three
modules", carries the heading "### `tests/test_apps.py` — 8 tests", and DoD item 9 repeats "36 tests".
`docs/SPECS/spec-021-apps-0_0_7.md` `### tests/test_apps.py (new)` enumerates the same **eight** tests
as its own ("Eight tests"), and its DoD item 4 states the file "contains the 8 tests listed in the Test
plan". Five of those eight — `test_djangostrawberryframeworkconfig_importable_from_apps_module`,
`…_is_appconfig_subclass`, `…_pins_name_and_verbose_name`, `…_resolves_through_django_app_registry`,
`…_defines_no_extra_appconfig_attributes` — pin spec-021's Decisions 2 / 5 / 8 and have no relation to
Trac #37064; spec-024's own prose names only the other three. Re-derived by collected node ids:
`tests/test_django_patches.py` **21**, `tests/testing/test_wrap.py` **7**, `tests/test_apps.py` **8**
(36 collected), of which card 024's own population is **31**. 36 is the correct *focused-run scope*,
which is what both Slice 1 artifacts measured ("36 = 21 + 7 + 8"); the spec converts a run scope into a
card test-plan claim. Recommended: state the run scope as 36 and the card-owned population as 31, or
retitle the section to the three `ready()` tests this card is responsible for and leave the other five
attributed to spec-021 (Decision 7 may keep citing
`tests/test_apps.py::test_ready_reinstalls_patches_after_their_modules_reload` — citing a sibling's test
as pinning a shared behaviour is not the problem).

**M2 — the spec narrates one piece of its own history, and this artifact asserts it does not.**
`docs/SPECS/spec-024-django_trac_37064_hardening-0_0_7.md` `## Risks and open questions`,
#"The pin will fire again": "Django `6.1` removed `SimpleTestCase._disallowed_connection_methods` and
**the single-body pin of the day** matched neither shape". That names a retired contract state of this
spec and requires the reader to hold a timeline to parse it — the shape `docs/builder/BUILD.md`
`## Spec rationale extraction` forbids ("the spec reads as a clean current contract, as though it had
been right from the start"). The risk argument survives without it: the pin fired on `6.1`, and the
resolution was an audit. Independently, this artifact's `#### 3. Deliberately not stated in the spec`
lists "the single-body pin" among five retired states and states "all five are in the rationale and
**none is in the spec**". That completeness claim is false at the one item; the other four re-derive
clean (`_PATCH_APPLIED` 0 / `_missing_symbol_logged` 0 / retired test names 0 / `logger` 0 in the spec,
and the `…test` and `hasattr` mentions that do appear are stated as prohibitions of a future change,
not as history — those two are correct). Both halves are Worker 1's to fix: the spec sentence and the
artifact's claim about it.

**M3 — a deferred-catalog count contradicts the catalog's own declared corpus.**
`### Deferred work catalog` item 4 declares its corpus explicitly — "over `django_strawberry_framework/`,
`tests/`, `examples/`, `scripts/`" — and its last bullet then says "a **substring** sweep returns **4**,
because a fourth site cites the live `…_for_each_alias_plan_shape` name". Re-derived at that declared
corpus, the substring `test_optimizer_elides_forward_fk_id_only_selection` returns **7 occurrences in 4
files**: `tests/test_list_field.py` 2 (both rot), `examples/fakeshop/test_query/test_scalars_api.py` 2
(one rot at the `…selection` citation, one live `…_for_each_alias_plan_shape` citation),
`tests/optimizer/test_extension.py` 2 (two live `def`s, including `…_selection_plan_shape`), and
`tests/test_permissions.py` 1 (a live `…_selection_plan_shape` citation). 4 is the answer for the
narrower corpus {`test_list_field.py`, `test_scalars_api.py`} — the instrument's corpus, not the
bullet's. The load-bearing half is exact and re-derives: end-anchored, **3 occurrences in 2 files**
(`tests/test_list_field.py:1316`, `:1328`, `examples/fakeshop/test_query/test_scalars_api.py:839`), and
the correction to Slice 3's number stands. Fix the illustrative number or scope it in place.

### Low:

**L1 — unused link definition.** The spec defines `[spec-024-terms]:
appx/spec-024-django_trac_37064_hardening-0_0_7-terms.csv` and never uses it; set difference of uses
against defs is `{spec-024-terms}` in the spec and empty in the rationale (undefined refs: 0 in both).
The file exists on disk. `docs/SPECS/spec-023-multi_db-0_0_7.md` uses its equivalent def in DoD item 1;
either cite the companion the same way or drop the def.

**L2 — the citation-uniqueness row's population is a quarter of its subject.** The build report's
verification table records "Every `#"substring"` citation is unique in its target — 4 citations, each
exactly 1 occurrence". Four is the count of *path-qualified* citations (`conf.py #"UPSTREAM_PATCH_…"`,
`_django_patches.py #"WIDENING…"` x2, `__init__.py #"__all__ = ("`). The two files carry **13** `#"…"`
citation occurrences — 9 in the spec, 4 in the rationale — the other 9 being `AGENTS.md`-anchored
(`#"Test placement:"`, `#"Test through real usage, prefer the example project"` x3, `#"Add a settings
key only when the feature that needs it lands"` x2, `#"Source refs in docs and code comments use symbol
paths never line numbers"` x2). No defect: all seven distinct targets resolve to exactly 1 occurrence in
their named file, re-derived. The row understates its own population, which is the failure mode that
lets a later pass re-run the wrong instrument.

**L3 — "three instances" is three categories over nine occurrences.** Catalog item 5: "The measured
cost of (c) in this cycle alone is now three instances, not two: one in-scope repair, seven
out-of-scope findings, and one invented symbol name". The enumeration is right beside the number and
every part of it re-derives, but 1 + 7 + 1 is nine occurrences in three kinds. Say kinds.

**L4 — one change-record row uses the committer date where every other row's two dates coincide.**
`52d97ec0` is `%ad` 2026-05-29 / `%cd` 2026-05-30; the rationale's table says 2026-05-30. Every other
one of the 21 rows has identical author and committer dates, so the convention is invisible to a reader
and unfalsifiable from the table. Either use `%ad` throughout or state the convention.

### DRY findings

None. The slice's stated DRY resolution — single-source each contract flip once as contract in the
spec and once as a retired claim in the rationale, cross-referenced by anchor rather than restated —
holds under inspection: the eight flips appear once each in `## Claims the spec may no longer make`
(items 1-8 map to flips 1, 2, 5, 4, 7, 8, 3 and the Decision-3/10 group), each expanded exactly once
under its Decision, and neither file restates a flip in a second vocabulary the way
`bld-slice-1b`'s divergence catalog and contract-flip section did. No existence challenge is raised:
the spec/rationale pair is the shape `BUILD.md` `## Spec rationale extraction` mandates, and the
per-Decision keying is what makes the rationale a lookup instrument rather than an archive.

### Mechanical gates re-run

| Gate | Result |
|---|---|
| `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-024-…md` | `OK: 2 terms` — **exit 0** |
| `uv run python scripts/check_trailing_commas.py --check` | **exit 0**, silent |
| 10 canonical `START.md` group headers, exact order, present when empty | **pass**, both files |
| Defs alphabetical within each group | **pass**, both files |
| Every link-def path disk-exists-checked (resolved from each file's own directory) | **0 missing**, both files |
| Undefined ref-ids | **0**, both files |
| Unused ref-ids | **1** in the spec (L1); 0 in the rationale |
| In-page `](#…)` anchors | **0 broken**, both files (after fixing my own slugger: GitHub keeps `_`, so `#decision-6--apply_upstream_patches-…` resolves) |
| Cross-file anchors, incl. the 11+11 spec/rationale Decision pairs and the 4 `GLOSSARY.md` anchors | **0 broken** |
| Raw `path:NN` | **0** in both files |
| Commit hashes HEAD-reachable (`git merge-base --is-ancestor <sha> HEAD`) | **27 distinct, 27 reachable, 0 orphans**; **0** hashes in the spec, all 27 in the rationale |
| Backticked identifiers resolve whole-token at HEAD (AST index of names defined/bound/attributed plus docstring-embedded tokens, over every non-`docs` `.py`) | **0 invented names.** Spec residue is the `WIDENING…` comment words (comments are not indexed), the `_PATCH_*` glob, two `…`-elided test-name suffixes (both resolve when unelided), and the spec's own filename stem. Rationale residue is 4 deliberately-cited retired names, hash fragments, and `wc` / `oneline` / `trac` |
| Every `path::Symbol` citation resolves by AST | **20 distinct, 20 resolve** |
| Every `#"substring"` citation unique in its target | **7 distinct targets, 1 occurrence each** (see L2 on the recorded population) |
| Script-rendered citation targets (`docs/TREE.md`, `KANBAN.md`, `docs/GLOSSARY.md`) | **0** — the `docs/TREE.md` obligation is stated as prose with the three modules named by full path, which is the correct avoidance of the regeneration trap |
| Test counts by collected node ids (not `def` lines) | `test_django_patches.py` **21**, `test_wrap.py` **7**, `test_apps.py` **8**, **36 collected** |
| Focused scope green | `pytest tests/test_django_patches.py tests/testing/test_wrap.py tests/test_apps.py tests/test_strawberry_patches.py --no-cov -q` -> **91 passed**, 0 failures, 0 collection errors |
| Public-surface check | `git diff -- django_strawberry_framework/__init__.py` — **empty**; `__all__` and the re-export list unchanged, as Decision 9 and DoD 8 require |
| CHANGELOG sanity | Not applicable; this slice does not touch `CHANGELOG.md` |

### The spec against source, Decision by Decision

Every Decision was walked against `django_strawberry_framework/_django_patches.py`, `apps.py`,
`conf.py`, `testing/_wrap.py`, `testing/__init__.py`, and the three test modules. **All eleven describe
code that exists at HEAD, accurately.** The probes the dispatch named specifically:

- **Install target and inheritance (D2).** `apply()` assigns
  `SimpleTestCase._remove_databases_failures`; `TransactionTestCase` / `TestCase` / a direct
  `SimpleTestCase` subclass are covered through the MRO, and all four cited tests exist.
- **Three-tier fail-closed validation (D4).** `_validate_upstream_shape` raises on
  `_DatabaseFailure is None`, on a non-`classmethod` descriptor, on a missing `__func__`, on a signature
  that is not exactly one `POSITIONAL_OR_KEYWORD` parameter, and on a body outside the audited set —
  with `(OSError, TypeError)` from `inspect.getsource` folded into the drift arm rather than exempted.
  A missing `_DatabaseFailure` **raises**; there is no logger in the module (`grep -c logger` -> **0**).
  All three messages name `APPLY_UPSTREAM_PATCHES = {"django": False}`, and the fourth defence-in-depth
  raise in `_disallowed_connection_methods` is present.
- **Two audited bodies (D5).** `_AUDITED_REMOVE_DATABASES_FAILURES_SOURCES` is a 2-tuple; the ranges
  match the constants' own leading comment; the discriminator is the module-level
  `_validated_remove_databases_failures_source` assigned by `apply()` from `_validate_upstream_shape`'s
  return, compared against the two named constants — **not** `hasattr` on the class. Set size is
  asserted in-suite (`assert len(_AUDITED_…) == len(audited)` with `audited` a 2-tuple), both read
  branches driven synthetically.
- **Reload-safe capture (D7).** The spec gets right the thing an earlier artifact in this cycle got
  wrong in both halves: `_PATCH_OWNER_ATTRIBUTE` and `_PATCH_ORIGINAL_ATTRIBUTE` are attribute-name
  constants, `_PATCH_OWNER` is the owner **value**, and only the owner attribute is compared while the
  original attribute is read and returned. The rationale's Decision 7 entry states the same distinction
  in its own words.
- **`APPLY_UPSTREAM_PATCHES` (D6).** Both shapes honoured in
  `conf.py::upstream_patches_enabled`; whole-mapping validation on every read; `ConfigurationError` on
  every off-contract shape. The gate is `apply()`'s **first** statement, ahead of validation — verified
  by reading `apply()`, and it is what makes `{"django": False}` a working recovery from a drift abort.
- **The asymmetry (D8).** `safe_wrap_connection_method` shares `_is_database_failure`, which returns
  `False` when `_DatabaseFailure is None`, so the helper installs and returns `True` where `apply()`
  raises. Pinned by `…_installs_when_database_failure_symbol_missing`. The `TypeError` does not
  interpolate `wrapper`.
- **History sweep.** Every hit of `originally` / `previously` / `formerly` / `used to` / `no longer` /
  `changed` / `reversed` / `since` / `now` / `initially` / `later` in the spec was judged individually.
  All are present-tense contract language or `Rationale companion —` pointer lines, which are the
  house shape (`spec-023` uses the same, including "the posture this Decision started from"). **One
  genuine leak**, M2 above.

### The rationale as a review instrument

Every entry names its spec Decision by heading **and** anchor (`Spec text: [Decision N][spec-024-dN]`,
all 11 resolving in both directions), and every one carries alternatives-rejected-with-why,
changes-undergone-with-the-commit, and claims-no-longer-makeable. Decision 11 omits the last heading and
says so under `Changes this Decision underwent` ("None. The open question closed once and stayed
closed") — correct, not a gap. The provenance section is the strongest part of the file: it declares
the reconstruction-not-move distinction up front and flags in place where a cause is an inference
rather than a commit-message fact (`48f9f65d` is exactly such an entry and says so).

**Retired-claims coverage is complete against Slice 1b's eight flips.** Flip 1 -> claim 1, flip 2 ->
claim 2, flip 5 -> claim 3, flip 4 -> claim 4, flip 7 -> claim 5, flip 8 -> claim 6, flip 3 -> claim 7,
flip 6 -> Decision 5's second bullet. The highest-value one carries its consequence explicitly: "A
future contributor who replaces the validated-source comparison with a `hasattr` read reintroduces a
known defect that shipped and survived ten days", with the mechanism (`_add_databases_failures` ignores
a `6.1` subclass's legacy attribute and wraps the feature list, so cleanup must read the same list) and
both dates — documented as a *feature* at `eb2a1764`, named a *bug* at `18550f5d`.

### Counts and claims re-derived independently

- **Change record population.** `git log --follow` union over the six surface files = **23**, minus
  `b972cd84` / `dfa035b4` (both 2026-05-21, pre-ship `apps.py` work) = **21**. In-tag membership
  against `72f6cd9b`: the first six are ancestors, `52d97ec0` onward are not — **6 in-tag / 15
  post-tag**, exactly as stated.
- **Test-count progression**, per commit on the extracted blob: **6, 10, 11, 12, 13, 13, 17, 17, 20,
  21**. `c7cb5f5c` owns the 12 -> 13 step; `48f9f65d` is net zero, and the name-set `diff` confirms it
  is -2/+2 rather than no change: removed
  `test_apply_no_ops_when_database_failure_symbol_missing` and
  `test_apply_logs_missing_symbol_notice_only_once`, added
  `test_apply_fails_loudly_when_database_failure_symbol_missing` and
  `test_apply_fails_loudly_when_upstream_method_signature_changes` — precisely the replacement pair the
  rationale's Decision 4 names.
- **Wrap decomposition.** `tests/test/test_wrap.py` 4 (`61973f8d`) -> 6 (`7014125a`); renamed to
  `tests/testing/test_wrap.py` at `e145ba36` still 6; 7 at `f7fbead4`. **4 + 2 + 1 = 7** at HEAD.
- **Module growth.** `_django_patches.py` **91** lines at `300e2811`, **406** at HEAD.
- **Stub size.** `git show HEAD:<spec path> | wc -c` -> **1618**. The dead `1,536` appears nowhere in
  either authored file.
- **31 test names cited in the spec, all live**, and both retired names appear only in the rationale.
- **The `_strawberry_patches.py` docstring fragment** (catalog item 6) reproduces at HEAD: the
  truncated clause "independent upstream *bugs* that do not retire together:" stands alone one line
  before the complete sentence containing it. It is a duplication, not a transposition; the fix is a
  one-line deletion.
- **Catalog items 1, 2, 3, 4 (six of seven bullets), 6** all reproduce exactly. `docs/TREE.md` carries
  **six distinct summary lines, twelve occurrences** (each module's docstring first line appears
  exactly twice), re-derived by matching each module's own docstring first line — confirming Worker 1's
  move off Slice 1b's "two". The six citation-defect counts re-derive as 1 / 1 / 1 / 2 / 1 / 1, and the
  symbol claims hold (`_select_editable_fields` and `_index_relation_fields` are defined nowhere;
  `_visible_related_object` lives at `django_strawberry_framework/types/resolvers.py`, not
  `forms/resolvers.py`; the auth symbol is `logout_mutation`, not `logout`). Item 1's two false
  `CHANGELOG.md` clauses are both present in one bullet under `## [0.0.7]` -> `### Added`. Item 5's
  `conftest.py` sub-claims hold: `git log --all --diff-filter=D -- conftest.py tests/conftest.py` is
  empty and the repo-root `conftest.py` was created at `57cbd32a` (2026-07-07). The one bullet that
  does not reproduce is M3.

### Task 3's escalated decision: reasoning and record

**The deciding measurement reproduces exactly**, re-derived read-only into a scratch path outside the
repo (no `stash` / `checkout` / `restore` / `worktree`): `TEMP-024.md` is byte-identical to its
`7014125a` blob (`rc=0`); `PLAN-024.md` differs from its `7014125a` blob at exactly `92c92` and
`115c115` — an `AGENTS.md` line-number citation rewritten to the `#"…"` form, and a `spec-019-…` path
gaining its `SPECS/` prefix; both recovered files are byte-identical to their `d1d19ca2^` blobs. The
commit attributions hold: `git log --follow` on the PLAN document shows exactly `df547235` ("Replace
line-NN references repo-wide with symbol-qualified paths") and `974189ad` between `7014125a` and the
deletion at `d1d19ca2`, and nothing else. So the recovered documents describe the tree at exactly
`7014125a`.

**The rejected reading and its stated costs hold up.** Both flips the rejection would lose are real at
the ship: `git show 300e2811:…/_django_patches.py` installs on `TransactionTestCase` and carries
`_PATCH_APPLIED` as a first-call-wins global. So a record starting at the plan's baseline would drop
two claims a reader of the shipped `0.0.7` artifact still hits, and the only way to keep them is the
chronology hedge the rationale names. The accepted cost — four days of in-release churn the plan never
saw — is discharged by a measurement (6 of 21 in-tag) rather than a framing, and I reproduced that
measurement. I do not disagree with the decision; the reasoning is sound and the record is complete,
including the consequence carried into Decision 4 (the log-once sentinel post-dates the plan's last
content-bearing write and was never a planned deliverable), which the `744fd28d` row and the Decision 4
entry both state consistently.

### What looks solid

- The spec is a genuine contract document, not a summary of the artifacts. Two facts it states that
  neither recovered planning document did — the `django_strawberry_framework.testing` import path and
  the gate-before-validation ordering — are contract at HEAD and are stated as contract, with the
  `test/` -> `testing/` rename kept out of the spec and put in the rationale as the reason.
- The Decision-granularity call (4 and 6 kept separate because "no settings key" and "degrade on a
  missing symbol" are two separately-reversed claims a reader will arrive with, with the coupling
  stated in both directions) is the right instinct for a file whose job is to be looked up.
- Decision 9's refusal to state an `__all__` member count, with the reason recorded in the rationale
  ("a count of its members written into a permanent spec by a card that does not own it would be rot
  with a verification date on it"), is exactly the discipline that has been failing in this repo's
  recent cycles.
- Every heading slug was computed rather than guessed; the two traps this repo has hit before (a dotted
  version slugging to `007`, a spaced em dash slugging to a double hyphen) are both handled correctly
  and both appear in live anchors.

### Temp tests

None written. Verification was mechanical (link/anchor/symbol/citation/hash resolvers and blob diffs
under `/private/tmp/.../scratchpad/`) plus one focused `pytest` run for pass/fail confirmation. No
behaviour needed pinning, so nothing is owed promotion.

### Notes for Worker 1 (spec reconciliation)

- M1 and M2 both require spec edits and only Worker 1 may make them. M2's second half is an edit to
  this artifact's own `#### 3` list.
- M3, L2, L3, L4 are artifact-side and do not touch the two permanent files.
- Nothing found requires a `.py` change. The deferred catalog's routing is correct: items 1-4 and 6 are
  outside this cycle's scope or outside card 024's ownership, and item 5 is genuinely contract-level
  (`BUILD.md` `### Contract-level findings are escalated as maintainer decisions before dispatch`) —
  no gate in this process resolves a symbol citation, and this cycle produced a fresh instance of that
  failure inside a pass whose subject was citation correctness.

### Review outcome

`revision-needed` — three Medium findings, two of which (M1, M2) sit in the permanently-archived spec.
Everything else in this slice is accepted: every Decision matches source, the rationale is keyed and
complete against all eight contract flips, the escalated decision's reasoning and record hold up under
independent re-derivation, and every mechanical gate is green apart from the one unused ref-id.

---

## Apply-changes pass (Worker 1) — build report

Fixes for the review's 3 Medium and 4 Low findings. HEAD at this pass: `f466863a` at start of read; the tree remains concurrent (spec-021 / spec-022 / optimizer edits and the 025 / 026 build plans are other cycles'). **No `.py` source or test file was written, and none is owed — all three Mediums are claims about code, not defects in it.**

Files written: `docs/SPECS/spec-024-django_trac_37064_hardening-0_0_7.md`, `docs/SPECS/appx/spec-024-django_trac_37064_hardening-0_0_7-rationale.md`, this artifact (body fixes + this report + `Status:`), and `docs/builder/worker-memory/worker-1-024.md` (appended). The review section above was not touched.

### Spec changes made (Worker 1 only)

| # | Section edited | Change | Reason | Finding |
|---|---|---|---|---|
| 1 | `spec-024` `## Test plan`, opening paragraph | Replaced "36 tests across three modules" with two separately-named quantities: **31 tests this card owns** (21 + 7 + 3) and the **36-test focused scope** the three modules collect whole, with an explicit sentence that the two answer different questions and are not interchangeable | 36 was a run scope promoted into a population claim; the spec must not let a later reader collapse the two again | M1 |
| 2 | `spec-024` `## Test plan`, third subsection heading and its opening | Retitled "### `tests/test_apps.py` — 8 tests" to "— 3 of the module's 8 tests" and added a sentence naming the other five as `spec-021`'s `AppConfig`-shape tests, unrelated to Trac #37064 | The section headed eight tests while its body described only three | M1 |
| 3 | `spec-024` `## Definition of done` item 9 | Restated as "this card's 31 tests ... are green ... as is the 36-test focused scope those three modules collect whole", pointing at `## Test plan` | DoD repeated the 36 as a card claim | M1 |
| 4 | `spec-024` `## Risks and open questions`, the `**The pin will fire again.**` bullet | Rewrote to state the present contract (a body outside the audited set aborts `ready()`) and to give Django `6.1`'s removal of `SimpleTestCase._disallowed_connection_methods` as the external fact it is; the clause "the single-body pin **of the day** matched neither shape" is gone | A retired contract state of this spec, which `docs/builder/BUILD.md` `## Spec rationale extraction` forbids the spec to carry. The retired single-body pin was already in the rationale (Decision 5's `eb2a1764` change bullet and its third rejected alternative), so nothing was moved, only removed | M2 |
| 5 | `spec-024` `## Key glossary references` | Added one sentence citing `[spec-024-terms]` — the companion CSV binding both project-specific terms to their `docs/GLOSSARY.md` headings, validated by `scripts/check_spec_glossary.py` | The def existed and was never used; `START.md` reserves defs for links the body makes. Used rather than dropped, matching `docs/SPECS/spec-023-multi_db-0_0_7.md`'s treatment of its own terms companion | L1 |
| 6 | `spec-024-…-rationale.md` `## Change record`, `52d97ec0` row | Date `2026-05-30` -> **`2026-05-29`** (the author date) | The row's claim rests on when the change was made | L4 |
| 7 | `spec-024-…-rationale.md` `## Change record`, preamble | Added the convention explicitly: every date is the author date (`git log --format=%ad --date=short`), and `52d97ec0` is the only one of the 21 whose committer date differs | The convention was invisible and unfalsifiable from the table | L4 |

Artifact-side fixes in this file's own body (no permanent file touched): `#### 3. Deliberately not stated in the spec` (M2's second half), the verification table's citation-uniqueness row (L2), catalog item 4's substring count (M3), catalog item 5's "three instances" (L3), the `### The spec, as rewritten` sentence that described the Test plan as "36 tests enumerated by contract" (M1 follow-on), and new catalog item 7 (M1's cross-surface residual).

### Card 024's test population, re-derived

The reviewer's 31 was not adopted; it was re-derived from git, and it reproduces.

| Measurement | Instrument | Result |
|---|---|---|
| `tests/test_apps.py` before card 024's ship | `git show 300e2811^:tests/test_apps.py \| grep -c 'def test'` | **5** — the four positive-shape tests plus the consolidated negative, i.e. exactly `spec-021`'s "4 positive shape + 1 consolidated negative-shape" |
| the three rows card 024 added | `git show <sha>:tests/test_apps.py` name-set diff per commit | `300e2811` +`test_djangostrawberryframeworkconfig_defines_ready_for_django_patches`; `136c5476` +`test_ready_dispatches_all_three_patch_appliers_and_refires_safely`; `18550f5d` +`test_ready_reinstalls_patches_after_their_modules_reload`. All three are already rows in the rationale's change record |
| module ownership | `git log --follow --diff-filter=A` | `tests/test_django_patches.py` created by `300e2811` (card 024's ship); `tests/testing/test_wrap.py` created by `61973f8d` (card 024's Phase 4). Both wholly this card's |
| HEAD counts | `grep -c 'def test'` | 21 / 7 / 8 |
| focused run scope | `pytest … --collect-only` on the three modules | **36 collected** |

**Card 024's population = 21 + 7 + 3 = 31. The focused run scope = 36.** Both are now stated in the spec, distinguished, and neither is used for the other's job.

### Findings closed, and the one disagreement

- **M1 — closed**, with a residual deferred. The spec no longer claims the five `AppConfig`-shape tests. `spec-021` was read but not edited (read-only, baseline-dirty, out of scope); the surviving cross-surface disagreement — `spec-021`'s Slice-2 step and DoD 4 read the three `ready()` tests as its own deliverable — is recorded as **deferred-work catalog item 7** for the maintainer rather than partial-fixed on the one editable side.
- **M2 — closed**, both halves: the spec sentence rewritten, and this artifact's false completeness claim corrected to record what actually held (four of five) rather than restated as if it had.
- **M3 — closed** by scoping the number in place: the unanchored sweep is now reported at the corpus the item declares (**7 occurrences in 4 files**) with the instrument that produced the old **4** named (the same sweep over a two-file corpus). The load-bearing end-anchored **3 occurrences in 2 files** re-derived unchanged.
- **L1 — closed** by using the def.
- **L2 — closed, with a disagreement on the number.** The finding's population of **13** does not reproduce. Measured over both files with `#"(?:[^"]|\n)*?"` (multi-line tolerant, occurrences not matching lines): **8 in the spec, 4 in the rationale = 12 occurrences**, over **7 distinct (target, substring) pairs**, each resolving to exactly 1 occurrence in its named file. The finding's own enumeration sums to 12 as well — 4 path-qualified (`conf.py` x1, `_django_patches.py` x2 across the two files, `__init__.py` x1) plus 8 `AGENTS.md`-anchored (`#"Test placement:"` 1, `#"Test through real usage…"` 3, `#"Add a settings key…"` 2, `#"Source refs…"` 2) — so the 13 and the "9 in the spec" are a transcription slip, not a different corpus. The row now records 12; the defect the finding names (the row understated its own population) stands and is fixed.
- **L3 — closed**, restated as "nine citation defects in three kinds".
- **L4 — closed**, with the convention stated rather than left implicit.

### Gates re-run after the edits

| Gate | Result |
|---|---|
| `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-024-…md` | `OK: 2 terms` — **exit 0** |
| `uv run python scripts/check_trailing_commas.py --check` | **exit 0**, silent |
| 10 canonical `START.md` group headers, exact order | **pass**, both files |
| Defs alphabetical within group | **pass**, both files |
| Every link-def path disk-exists-checked from the file's own directory | **0 missing**, both files |
| Undefined ref-ids | **0**, both files |
| Unused ref-ids | **0**, both files (was 1 in the spec) |
| In-page `](#…)` anchors | **0 broken**, both files — including the three the M1 fix added (`#test-plan`, `#floor-verification`, `#definition-of-done`) |
| Cross-file anchors (11+11 Decision pairs, glossary, `spec-020`) | **0 broken** |
| Raw `path:NN` | **0**, both files |
| Commit hashes HEAD-reachable | **27 distinct in the rationale, 27 reachable; 0 in the spec** |
| Backticked symbols introduced by this pass resolve whole-token at HEAD | `_remove_databases_failures`, `_disallowed_connection_methods`, the three test-module paths, the three added test names, `scripts/check_spec_glossary.py` — **all resolve**; no new symbol invented |
| `#"substring"` citations unique in target | **7 distinct pairs, 1 occurrence each**, re-derived per target |
| Focused scope green | `pytest tests/test_django_patches.py tests/testing/test_wrap.py tests/test_apps.py tests/test_strawberry_patches.py --no-cov -q` -> **91 passed**, 0 failures. No `--cov*` flag anywhere in this pass |

**Slugger note, carried from the earlier pass and re-learned here:** a slugger that strips `_` reports every `#decision-6--apply_upstream_patches-…` anchor as broken. GitHub keeps `_`; it deletes the em dash, which is what turns a spaced em dash into a double hyphen. Both files' anchors are clean under the corrected instrument.

### Failability proofs

`None; this pass introduced no new boundary.` Markdown only — the `docs/builder/BUILD.md` `### What needs a proof, and what does not` doc-edits exemption. The obligation that does apply is the stated-count rule, discharged above: every number written or rewritten in this pass was measured at the moment it was written, and the one number inherited from the review (L2's 13) did not survive re-derivation.

### Hot-path budget

`Not applicable; plan declares no hot path.`

### Floor verification

`Owned by Slice 1b per the plan's declaration.` Unchanged by this pass; no venv was created or mutated.

---

## Re-review (Worker 3)

Subject: the seven fixes recorded in `### Spec changes made (Worker 1 only)` and
`### Findings closed, and the one disagreement`, plus regression over the mechanical suite. The prior
pass's accepted findings (11 Decisions against source, 8 contract flips, Task 3's deciding measurement,
the 21-commit population, the gate suite) were not redone; the gates were.

HEAD at this pass: `ddf8bbaf`. **Every number below was measured at this pass, not adopted.** No
`--cov*` flag was used. No permanent file, no `.py` file, and no prior section of this artifact was
written by me; the only files I wrote are this section, `docs/builder/worker-memory/worker-3-024.md`,
and two throwaway resolvers under `docs/builder/temp-tests/024-slice2-rereview/`.

### High: None.

### Medium: None.

### Low:

**L5 — the apply-changes report's stated HEAD is one commit stale, and it is behind the review it
answers.** `## Apply-changes pass (Worker 1) — build report` opens "HEAD at this pass: `f466863a` at
start of read", but the review section directly above it already records `ddf8bbaf`, and HEAD is
`ddf8bbaf` now. Verified harmless before grading: `git diff --name-only f466863a HEAD` is thirteen
`docs/` files from cycles 023 / 020 / 021 and touches none of card 024's six surface files, all 27
rationale hashes are still HEAD-reachable, and every count in the pass re-derives at `ddf8bbaf` (below).
Graded Low because the drift-detection habit this cycle has run five times — re-read HEAD, prove the
intervening commits miss the surface — is what makes an inherited count safe, and a pass that reports a
HEAD older than the artifact it is answering has not run it. Not held: nothing downstream is wrong.

### M1 — re-derived independently, not adopted

The population claim reproduces from git in every part.

| Claim | My instrument | Result |
|---|---|---|
| `tests/test_apps.py` held 5 tests before card 024 | `git show 300e2811^:tests/test_apps.py` | **5**, and the five names are exactly `spec-021`'s four positive-shape tests plus `…_defines_no_extra_appconfig_attributes` |
| card 024 added three | per-commit name-set `diff` of `<sha>^` against `<sha>` | `300e2811` 5 -> 6 (`test_djangostrawberryframeworkconfig_defines_ready_for_django_patches`), `136c5476` 6 -> 7 (`test_ready_dispatches_all_three_patch_appliers_and_refires_safely`), `18550f5d` 7 -> 8 (`test_ready_reinstalls_patches_after_their_modules_reload`) |
| the other two modules are wholly this card's | `git log --follow --diff-filter=A` | `tests/test_django_patches.py` created by `300e2811` (the ship); `tests/testing/test_wrap.py` created by `61973f8d` (Phase 4). Both card 024 commits, both already rows in the change record |
| HEAD counts | `git show HEAD:<f> \| grep -c 'def test'` | 21 / 7 / 8 |
| run scope | `pytest --collect-only -q --no-cov` on the three modules | **36 collected** — so the two instruments agree and no parametrization hides behind the `def` count |

**21 + 7 + 3 = 31 owned; 36 run scope.** Confirmed.

**The spec now separates them structurally, not just numerically**, which is the part that had to hold:
`## Test plan` states the two quantities in two separate paragraphs, says in as many words that they
"answer different questions and are not interchangeable", and assigns each a job — 36 is what
[Floor verification](#floor-verification) and DoD 9 execute, 31 is what every ownership claim is stated
against. The subsection heading is "3 of the module's 8 tests" and its body names the other five as
`spec-021`'s. DoD 9 carries both quantities with the roles kept apart and points back at `## Test plan`.
Swept the whole spec for a surviving collapse: the only occurrences of 36 / 31 / "8 tests" are those
four sites and they are mutually consistent. A later reader cannot re-collapse them without deleting a
sentence that forbids it.

Also checked, since a renumbered Test plan is where an enumeration goes wrong: the section names **24**
distinct `test_*` identifiers and **all 24 resolve** to a `def` in the three modules; the per-group
counts in the 21-test subsection sum to 21.

Catalog item 7 (the deferred residual) is accurate: `docs/SPECS/spec-021-apps-0_0_7.md` Slice-2 step 2
and DoD item 4 both claim the three `ready()` tests, while the same file's `KANBAN.md` doc-update bullet
already says the `ready()` body "arrives with sibling card `DONE-024-0.0.7`". Read read-only; not
edited. Deferring rather than half-fixing the editable side is the right call.

### M2 — re-derived, and the history sweep re-run over the whole spec

`of the day` — **0 occurrences**. The `## Risks and open questions` bullet now opens with the present
contract (an edited upstream body puts the installed body outside the audited set, `ready()` raises, the
package refuses to boot) and gives `6.1`'s removal of `SimpleTestCase._disallowed_connection_methods` as
an external upstream fact. No retired state of *this spec* remains, and no timeline has to be applied to
read it.

**Sweep re-run independently** over the whole spec for `originally|previously|formerly|used to|no longer|
was|were|had been|changed|reversed|since|as of|initially|later|once|until|earlier|at first|of the day|
historically|before` — 14 lines hit, every one judged:

- **Present-tense mechanism, not chronology** (7): "the attribute is **no longer** a `_DatabaseFailure`
  and teardown raises" (runtime state); "**Before** installing anything it calls `_validate_upstream_shape`"
  and "the `isinstance` test ... **before** the `setattr`" (ordering); "reverted the class attribute
  **since** the prior call" and "`_DatabaseFailure` **was** already at the named attribute" (runtime);
  "**since** otherwise `ready()` has already refused to boot" (causal).
- **`Rationale companion —` pointer lines** (4, incl. the Status line): the house shape `spec-023` uses,
  and the deliberative layer is exactly where BUILD.md `## Spec rationale extraction` puts it.
- **Legitimate scope statements** (2): "not at the ship and not since" bounds the `__all__` claim rather
  than narrating a reversal; "the `django_strawberry_framework.testing` subpackage **later** grew a
  test-client family under a different card" is a non-goal about a sibling card's surface.
- **The former leak** (1): fixed, as above.

**Worker 1's `hasattr` reading is correct** and I verified it rather than inherited it: 2 occurrences,
both on the single line 201, and both are prohibitions on a future implementation — "never
`hasattr(cls, …)`" and "the `hasattr` form looks more robust and is not" — with the mechanism given
(a `6.1` subclass may declare the legacy attribute, but `_add_databases_failures` ignores it and wraps
the feature list). Nothing there asks the reader to hold a timeline. It stays.

**The corrected completeness claim in `#### 3` is now true**, and it is corrected the right way — it
records that four of five held and one did not, rather than restating the list as though it had always
been right. Every zero it asserts re-derives over the spec as it stands (occurrences, not lines):
`_PATCH_APPLIED` 0, `_missing_symbol_logged` 0, `test_apply_no_ops_when_database_failure_symbol_missing`
0, `test_apply_logs_missing_symbol_notice_only_once` 0, `logger` 0, `single-body` 0, `single pin` 0,
`test/` 0, `hasattr` 2.

### M3, L1, L3, L4 — re-derived

- **M3 closed.** At the corpus item 4 declares (`django_strawberry_framework/`, `tests/`, `examples/`,
  `scripts/`), the unanchored substring returns **7 occurrences in 4 files** — `test_scalars_api.py` 2,
  `tests/optimizer/test_extension.py` 2, `tests/test_list_field.py` 2, `tests/test_permissions.py` 1 —
  and the old **4** is exactly the same sweep over `{test_list_field.py, test_scalars_api.py}`, which I
  reproduced at 4. Both instruments are now named in the bullet (`grep -ro` for occurrences, an
  end-anchored `grep -rEo` for the rot). The load-bearing end-anchored figure re-derives unchanged at
  **3 occurrences in 2 files**, and reading the seven sites confirms the triage: three cite the retired
  bare name, four cite live `…_selection_plan_shape` / `…_for_each_alias_plan_shape`. Count and corpus
  now agree, which is the whole of what M3 asked.
- **L1 closed by use, not deletion.** `[spec-024-terms]` is cited in `## Key glossary references`, in a
  sentence that says what the CSV binds and which script validates it — the `spec-023` treatment. Unused
  ref-ids in the spec are now **0**.
- **L3 closed.** Item 5 reads "nine citation defects in three kinds", with the 1 / 7 / 1 enumeration
  intact beside it.
- **L4 closed, convention stated.** `52d97ec0` is `%ad` 2026-05-29 and the row says 2026-05-29. I pulled
  `%ad` and `%cd` for all 21 rows: **every row's table date equals its author date**, and `52d97ec0` is
  **the only** row whose committer date differs (2026-05-30) — so the preamble's claim is not just a
  convention statement, it is a true and now-falsifiable one.

### L2 — the recorded disagreement, adjudicated

**Ruling: Worker 1 is upheld; the review's 13 is overruled.** Measured independently over both files
with a multi-line-tolerant `#"(?:[^"]|\n)*?"`, counting occurrences rather than matching lines:

| | occurrences |
|---|---|
| `spec-024-…-0_0_7.md` | **8** |
| `…-rationale.md` | **4** |
| **total** | **12** |
| distinct substrings | **7** |
| distinct `(target, substring)` pairs | **7** |

The 8 in the spec are `#"Test placement:"`, `#"Test through real usage…"` x2, `#"Add a settings key…"`,
`#"Source refs…"`, `#"UPSTREAM_PATCH_DEPENDENCIES = frozenset("`, `#"WIDENING…"`, `#"__all__ = ("`; the
4 in the rationale are `#"WIDENING…"`, `#"Source refs…"`, `#"Add a settings key…"`,
`#"Test through real usage…"`. Every one of the 7 pairs resolves to **exactly 1** occurrence in its
named file, re-counted per target (`AGENTS.md` x4, `conf.py`, `_django_patches.py`, `__init__.py`).

The review's own enumeration sums to 12 (4 path-qualified + 8 `AGENTS.md`-anchored), so its headline
"13 — 9 in the spec" is a transcription slip inside the finding, not a different corpus or a different
instrument. **The defect the finding named is real and remains fixed**: the row recorded 4, which was the
path-qualified subset only. The row now records 12 over 7 pairs and names what the old 4 counted.

Method note for the record: my instrument is multi-line tolerant because one spec citation wraps, and a
line-based `grep -c` would undercount it. That is the same occurrences-vs-lines rule that produced M3 one
document over.

### Regression — mechanical suite re-run in full

| Gate | Result |
|---|---|
| `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-024-…md` | `OK: 2 terms` — **exit 0** |
| `uv run python scripts/check_trailing_commas.py --check` | **exit 0**, silent |
| 10 canonical group headers, exact order, present when empty | **pass**, both files |
| Defs alphabetical within group | **pass**, both files |
| Every link-def path disk-exists-checked from the file's own directory | **0 missing**, both files |
| Undefined ref-ids | **0**, both files |
| Unused ref-ids | **0**, both files (the spec's 1 is closed) |
| In-page `](#…)` anchors | spec **29 uses / 0 broken**; rationale **16 / 0** |
| Cross-file anchors resolved through the def block (22 Decision pairs, 3 `GLOSSARY.md`, `spec-020`) | **0 broken** |
| Raw `path:NN` | **0**, both files |
| Commit hashes HEAD-reachable | rationale **27 distinct, 27 reachable**; spec **0 hashes** |
| Backticked identifiers whole-token at HEAD (AST index of defs/binds/attrs/args/aliases + docstring string constants, over every non-`docs` `.py`) | **0 invented names.** Residue is the `WIDENING THIS SET IS AN AUDIT, NOT A VERSION BUMP` comment words (comments are not AST-indexed), the `_PATCH_*` glob, the spec's own filename stem, two `…`-elided wrap-test suffixes (both resolve unelided at `tests/testing/test_wrap.py:164` and `:190`), and in the rationale the hashes, `wc` / `oneline` / `trac` / `TEMP`, and 4 deliberately-cited retired names (all 4 confirmed **0** live occurrences under `django_strawberry_framework/` + `tests/`) |
| Every `path::Symbol` citation resolves by AST | **20 distinct, 20 resolve** |
| Every `#"substring"` citation unique in its target | **7 pairs, 1 occurrence each** (see L2) |
| Focused scope green | `pytest tests/test_django_patches.py tests/testing/test_wrap.py tests/test_apps.py tests/test_strawberry_patches.py --no-cov -q` -> **91 passed** |

**No new dangling anchor and no new ref-id.** The three in-page anchors the M1 fix introduced
(`#test-plan`, `#floor-verification`, `#definition-of-done`) all resolve, and the one def the L1 fix put
into use closes the last unused ref-id, so the spec is now 0-undefined / 0-unused where it was 0/1.

**Slugger trap — confirmed, not inherited.** My checker slugs by GitHub's rule (lowercase, drop every
character that is not `\w`, space, or hyphen, then space -> hyphen). `\w` includes `_`, so
the heading `## Decision 6 — APPLY_UPSTREAM_PATCHES is the escape hatch` (with the symbol backticked in the file) slugs to
`decision-6--apply_upstream_patches-is-the-escape-hatch`, which is the def's fragment exactly: the em
dash is deleted and its two flanking spaces become the double hyphen. Verified by hand on that one
heading before trusting the run. Worker 1's account of the trap is right, and a slugger that strips `_`
would have indicted all 9 of these anchors falsely — the same false positive my own first run produced
in the prior pass.

Observation, not a finding: the rationale has four heading slugs repeated once per Decision
(`derivation`, `alternatives-considered-and-rejected`, `changes-this-decision-underwent`,
`claims-this-decision-may-no-longer-make`). GitHub disambiguates with `-1`…`-10` suffixes and no link in
either file targets them — every cross-reference goes to the `## Decision N` heading, which is unique.
Nothing to fix; recorded so a later resolver does not report it as new.

### DRY findings

None. No new prose was introduced that restates a contract already stated elsewhere: the M1 fix adds one
quantity and one distinguishing sentence, the M2 fix is net-subtractive, and the L1 fix cites a companion
file rather than restating its contents.

### Temp tests

Two throwaway resolvers under `docs/builder/temp-tests/024-slice2-rereview/` (`check_md.py` — link
defs, group headers, alphabetization, disk-exists, undefined/unused refs, in-page and cross-file
anchors, raw `path:NN`; `symcheck.py` — the AST identifier index). Gitignored, nothing owed promotion:
they pin no package behaviour.

### Notes for Worker 1

- L5 is the only open item and needs no edit to either permanent file. If the artifact is amended at
  all, state the HEAD the pass actually ran against.
- Deferred-catalog item 7 stays the maintainer's call; nothing in this pass changes its shape.
- Nothing found requires a `.py` change, a spec change, or a rationale change.

### Re-review outcome

`review-accepted` — no High, no Medium. All three Mediums and all four Lows are closed, each verified by
re-derivation rather than by reading the fix report: M1's population reproduces from the pre-ship blob
and three per-commit name-set diffs and the spec now makes the two quantities structurally
un-collapsible; M2's leak is gone with the whole-spec sweep re-run and every remaining hit judged, and
the artifact's completeness claim is corrected honestly rather than restated; M3's count and corpus
agree with both instruments named; L1 is closed by use; L3 and L4 are exact, L4's stated convention
being true across all 21 rows. **On L2 the builder is upheld: 12 occurrences over 7 pairs, not 13** —
the finding's headline contradicted its own enumeration. Both permanent files are archive-ready.

---

## Final verification (Worker 1)

HEAD at this pass: `ddf8bbaf` ("finish 23"), re-read at pass start rather than inherited. That is the
same HEAD the re-review recorded, so nothing this pass carries forward needed a second reachability
re-derivation on account of a moved HEAD — but it was re-run anyway (below), because a reachability
list is a claim.

**Slice contract, from the build plan's `## Checklist`:** rewrite the stub as a contract that matches
HEAD; author the rationale companion carrying every explanation, rejected alternative, change record,
and retired claim. Audited against the two files on disk, not against the report.

- **The stub is a contract.** `docs/SPECS/spec-024-django_trac_37064_hardening-0_0_7.md` carries 11
  numbered Decisions, `## Problem statement`, `## Current state`, `## Goals`, `## Non-goals`,
  `## Borrowing posture`, `## User-facing API` with the worked `setUp`/`tearDown` shape and the three
  error shapes, `## Implementation plan`, `## Edge cases and constraints`, `## Test plan`,
  `## Doc updates`, `## Risks and open questions`, `## Out of scope`, and a 12-item
  `## Definition of done`. Read end to end at this pass. **It carries no chronology anywhere** — no
  amendment block, no "as of", no "originally X, now Y" — and **0 commit hashes** (measured: `grep`
  for a backticked 8-hex token returns 0 distinct in the spec, 27 in the rationale).
- **The rationale is keyed to the spec's Decisions and to nothing else.** Eleven `## Decision N`
  sections, each carrying derivation, rejected alternatives with the reason each lost, the changes the
  Decision underwent with the commit that made them, and the claims it may no longer make; plus
  `## Provenance of this record`, the 21-row `## Change record`, the consolidated
  `## Claims the spec may no longer make`, and `## Verified against the shipped code`. Every spec
  Decision has a `Rationale companion —` pointer and every rationale Decision points back; **11 + 11
  cross-file Decision anchors, 0 broken**, re-resolved at this pass.
- **The escalated Task 3 decision is made and its rejected reading is recorded.** `#### 1. The
  escalated decision: where the rationale's change record starts` names the chosen origin
  (`300e2811`, the ship), the rejected origin (the recovered plan's baseline `7014125a`), two reasons
  the rejected reading loses, the accepted cost of the chosen one, and the deciding measurement with
  the exact read-only commands. The rationale carries the same decision at
  `### Where the change record starts, and the reading rejected` — stated as a choice with its
  rejected alternative, which is what that file is for. **The rejected reading survives in the
  permanent record**, which was the point of escalating it rather than letting a cohort default win.
- **Counts re-derived at this pass, not inherited:** 27 distinct 8-hex tokens in the rationale, **27
  HEAD-reachable at `ddf8bbaf`, 0 orphans** (`git merge-base --is-ancestor <sha> HEAD` per token);
  `tests/test_apps.py` is **5** tests at `300e2811^` and **8** at HEAD, so card 024's three and
  `spec-021`'s five reconcile; **31** owned vs **36** run scope both re-derive.

### L5 — disposed

**Accepted as recorded; no edit made, and none is owed.** The re-review graded it Low, verified it
harmless before grading, and said explicitly that nothing downstream is wrong. Re-checked at this pass
rather than accepted: `git diff --name-only f466863a ddf8bbaf` is 13 `docs/` files and touches none of
card 024's six surface files; all 27 rationale hashes are reachable at `ddf8bbaf`; both permanent files
are unchanged by anything between the two commits.

Deliberately **not** amending the apply-changes report's `HEAD at this pass:` line. That report is a
record of what that pass did, and `docs/builder/BUILD.md` `### The review document is evidence, not
contract` applies in both directions — a pass's own build report is the record of that pass, and
back-dating its stated HEAD to a commit it did not read would make the record less true, not more.
The finding stands where it is, with the re-review's verification beside it, which is the correct
disposition for a Low that names a habit rather than a defect. **The habit itself is honoured here:**
this section states the HEAD it ran against and re-derives the reachability rather than inheriting it.

### Spec changes made (Worker 1 only)

One, exposed by the integration pass's consistency scan and recorded in full in
`docs/builder/bld-integration-024.md` `### Spec changes made (Worker 1 only)`: the `docs/TREE.md`
regenerate obligation named three of this card's six TREE-feeding modules. Both sites now name all six.
Nothing else in either permanent file was edited by this pass.

Status: final-accepted.
