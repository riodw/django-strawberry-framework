# Build: Review round 1 — R1 rationale extraction + spec reconciliation

Spec reference: `docs/SPECS/spec-021-apps-0_0_7.md` (whole file; 513 lines / 97,518 bytes at `HEAD` `51eb47ba`, 64,813 bytes after final verification)
Rationale reference: `docs/SPECS/appx/spec-021-apps-0_0_7-rationale.md` (created by this round; 80,506 bytes after final verification)
Plan reference: `docs/builder/build-021-apps-0_0_7.md` `## Verified findings`
Status: final-accepted

## Plan (Worker 1)

R1 of a **review round** (`BUILD.md` `## Review rounds`), whose worker sequence the plan declares as Worker 1 → Worker 3 → Worker 1 with **no Worker 2**: only Worker 1 may mutate the spec, and Worker 2 may never read the rationale file, so R1's build phase is Worker 1's by role contract. Isolation is intact — a separate Worker 3 reviews this pass and a fresh Worker 1 invocation performs final verification.

### DRY analysis

**Helper inventory checked.** Not applicable in the code sense — this cohort writes no `.py` and adds no helper, constant, validation branch, coercion utility or test helper. `BUILD.md` `### When to run the helper during build` scopes `scripts/review_inspect.py` to source logic; the plan's pre-flight step 2 already recorded the skip for the same reason, and nothing in this pass changes it. The package-wide AST inventory was therefore not refreshed: it exists to prevent duplicated *implementation* shapes, and this cohort produces prose.

The DRY question that does apply is **duplication between the spec and the rationale file**, and it is the one the move exists to prevent:

- **Existing patterns reused.** `docs/SPECS/appx/spec-020-list_field-0_0_7-rationale.md` is the immediate predecessor and the closest model. Its conventions are followed structurally — a `## Provenance of this record` section with measured `wc -c` before/after counts, the Moved / Reconciled-in-place / Kept-deliberately / Deleted-outright lists, the anchors-slug-rendered-text note, per-Decision keying with reference-style headings, a `## Claims the spec may no longer make` table, and the ten canonical link-definition group headers. Its *content* is not reused.
- **New shared shape justified.** None. There is one cohort, so `worker-1.md` `### DRY analysis shape`'s shared-shape assignment rule has nothing to assign.
- **Duplication risk avoided.** The single real risk is a **copy** rather than a move — text landing in the rationale file while surviving in the spec. Prevented mechanically rather than by care: the post-edit sweep counts the moved vocabulary in the spec and requires zero (`revN Xn` attributions, `Alternatives considered`, `Revision history`, `Risks and open questions`, `spec-016`), recorded under `### Validation run`. The second risk is the rationale file re-stating a contract the spec already carries; the guard is that every rationale entry is keyed to a spec section or Decision and says what *changed*, not what *is*.

### Implementation steps

1. Read `django_strawberry_framework/apps.py` and the three `_*_patches.py` module docstrings at `HEAD` before writing any replacement contract for Decision 4. Read `tests/test_apps.py` at `HEAD` and enumerate its test functions rather than taking a count from the dispatch prompt.
2. Verify every provenance commit F1 cites (`300e2811`, `7014125a`, `c7cb5f5c`, `136c5476`) with `git log -1`.
3. Re-derive the card ids behind F4's `(017, 018, 019, 045)` against `KANBAN.md` rather than translating them.
4. Rewrite `docs/SPECS/spec-021-apps-0_0_7.md`: shipped status line, rationale pointer, Decision 4 inverted to the shipped contract with every falsified site reconciled, the test surface re-pinned to what was measured, the renumber residue corrected, and the deliberative layer cut.
5. Create `docs/SPECS/appx/spec-021-apps-0_0_7-rationale.md` carrying every cut passage, keyed to the spec section or Decision it belongs to.
6. Sweep both files: in-page anchors, cross-file anchors from the rationale into the spec, reference-link definitions used/defined, disk existence of every path, and every `#"substring"` citation the pass writes or keeps.
7. Run `check_spec_glossary.py` and the markdown scaffold check scoped to the two files; record `git status --short`.

Line numbers in this artifact are pin-at-write-time navigational hints against `HEAD` `51eb47ba`.

### Test additions / updates

None. This cohort writes no `.py`; the plan forbids source and test edits, and its `## Verified findings` conclusion is that no code was skipped, dropped or deviated. The eight tests in `tests/test_apps.py` are **read** as evidence for F2 and are not modified.

### Implementation discretion items

- The exact section ordering inside the rationale file, provided every entry stays keyed to a spec section or Decision.
- Whether a moved `Justification:` block's positive argument is re-set as body prose in the spec or restated in the rationale — decided per block on whether the argument changes how the thing is built.

### Dispatched findings checklist

One box per finding dispatched to R1, quoted as `docs/builder/build-021-apps-0_0_7.md` `## Verified findings` states it, with the symbol-qualified evidence Worker 0 recorded.

- [x] **F1 — HOLDS. Decision 4 ("No `ready()` hook in `0.0.7`") is falsified by the shipped code.** Spec claim: "`DjangoStrawberryFrameworkConfig.__dict__` MUST NOT contain a `ready` key", propagated to the Slice 1 checklist "Do NOT implement `ready()`", the Slice 2 negative-shape sub-bullet, `## Test plan`, `## Edge cases and constraints`, `## Risks and open questions`, `## Goals` item 3, `## Non-goals` item 1, `## Borrowing posture` ("No `ready()`"), and Definition of done items 1 and 6. `HEAD`: `django_strawberry_framework/apps.py::DjangoStrawberryFrameworkConfig.ready` exists and dispatches three appliers — `_django_patches.apply()`, `_strawberry_patches.apply()`, `_cross_web_patches.apply()` — all gated by the `APPLY_UPSTREAM_PATCHES` setting (`django_strawberry_framework/conf.py #"APPLY_UPSTREAM_PATCHES_KEY"`). Provenance `300e2811`, `7014125a`, `c7cb5f5c`, `136c5476`. "Not a code defect. The later contract is the correct one."
- [x] **F2 — HOLDS. The pinned test surface is stale (5 tests / four forbidden keys).** Spec claim: the `## Implementation plan` table and Definition of done item 4 say **5** tests; `## Test plan` and the Slice 2 checklist pin the forbidden-key set as `{"ready", "label", "default_auto_field", "default"}`. `HEAD` `tests/test_apps.py`: the forbidden set is three keys — `label`, `default_auto_field`, `default`; `"ready"` was removed with an in-file comment naming the supersession. Three tests exist that the spec does not describe: `tests/test_apps.py::test_djangostrawberryframeworkconfig_defines_ready_for_django_patches`, `::test_ready_dispatches_all_three_patch_appliers_and_refires_safely`, `::test_ready_reinstalls_patches_after_their_modules_reload`. **Correction to the finding's own count, measured this pass: the file carries 8 test functions, not 7** — see `### Notes for Worker 1 (spec reconciliation)`.
- [x] **F3 — HOLDS. Spec status line says `draft`.** "`Status: draft (revision 6, post-rev5 build-readiness audit).` on a card that shipped in `0.0.7` and whose spec is archived under `docs/SPECS/`."
- [x] **F4 — HOLDS. Renumber residue in the spec's own references.** "`docs/SPECS/spec-021-apps-0_0_7.md` link definition `[spec-016]: spec-020-list_field-0_0_7.md` — the ref-id names the pre-renumber number while its target names the post-renumber filename; the body then reads `spec-016` Decision 10 in six places while the `Predecessors:` line names `spec-020`." And: "`## Risks and open questions`'s 'Last-card-to-ship version bump policy' names 'the four remaining `0.0.7` WIP cards (017, 018, 019, 045)' — pre-renumber ids, while `### Decision 6` in the same spec names the post-renumber `DONE-022/023/025`."
- [x] **F7 — HOLDS. The rationale file does not exist.** "`docs/SPECS/appx/spec-021-apps-0_0_7-rationale.md` is absent while all 25 sibling specs have one. The spec still carries a 23-bullet inline `Revision history`, a `Justification:` block under seven Decisions, an `Alternatives considered (and rejected):` list under six, a four-item `## Risks and open questions`, and ~45 `(revN Xn)` attribution parentheticals through the checklist, decisions, edge cases, test plan, doc updates and DoD." **Corrections to the finding's own counts, measured this pass: eight `Justification:` blocks (all eight Decisions), seven `Alternatives considered` lists (Decision 5 has none), and 53 `(revN Xn)` parentheticals outside the revision-history block** — see `### Notes for Worker 1 (spec reconciliation)`.

---

## Build report (Worker 1, standing in for Worker 2 per the plan's declared R1 sequence)

### Files touched

- `docs/SPECS/spec-021-apps-0_0_7.md` — rewritten. Shipped status line and a rationale pointer replace the `draft` line (F3, F7). Decision 4 inverted from "No `ready()` hook in `0.0.7`" to "`ready()` applies the upstream patches", and every one of the eighteen sites the old claim reached was reconciled (F1). The test surface was re-pinned to the eight tests measured in `tests/test_apps.py`, and the forbidden-key set narrowed to three (F2). The `[spec-016]` ref-id and all seventeen `spec-016` token occurrences became `spec-020` (F4). The whole deliberative layer was cut (F7). Five stale `#"substring"` citations that no longer resolved were repaired.
- `docs/SPECS/appx/spec-021-apps-0_0_7-rationale.md` — **created** (F7). Carries the moved revision history, the rejected alternatives per Decision, the moved `Justification:` blocks, the moved `## Risks and open questions`, the `## Renumber residue` record, a `## Claims the spec may no longer make` table of thirteen rows, and a `## Left open by this pass` section.
- `docs/builder/bld-review-1-rationale_and_spec_reconciliation.md` — this artifact.
- `docs/builder/worker-memory/worker-1.md` — memory entry appended.

**Measured byte counts (`wc -c`):**

| File | Before | After |
|---|---|---|
| `docs/SPECS/spec-021-apps-0_0_7.md` | 97,518 | 64,868 |
| `docs/SPECS/appx/spec-021-apps-0_0_7-rationale.md` | 0 (did not exist) | 60,403 |

The spec shed 32,650 bytes; the rationale file is 60,403. It is larger than the shed amount because it is not only a destination: it also records what this pass changed and why, the eighteen-site reconciliation table for F1, the chronology of the four provenance commits, and the count corrections above — none of which existed in the spec to be moved.

### Half A — the rationale MOVE

Populations were enumerated before their sizes were stated, and each was measured against `git show HEAD:docs/SPECS/spec-021-apps-0_0_7.md` written to a scratch path outside the repo.

| Population | Measured at `HEAD` | Command | Disposition |
|---|---|---|---|
| `Revision history` inline block | lines 8-33 (26 lines), revisions 1-6 plus two "Informational" entries | `grep -n '^Revision history\|^## Key glossary'` | moved whole |
| `(revN Xn)` attribution parentheticals outside that block | **53** occurrences across 34 lines | `sed -n '35,513p' … \| grep -oiE 'rev[0-9]+ [HML][0-9]+' \| wc -l` | moved as change records, one per round per decision |
| standalone `Justification:` blocks | **8** (Decisions 1-8; lines 213, 245, 261, 276, 295, 305, 322, 337) | `grep -n '^Justification:$'` | moved; positive arguments re-set as spec body prose where they change how the thing is built |
| `Alternatives considered (and rejected):` lists | **7** (Decisions 1, 2, 3, 4, 6, 7, 8; Decision 5 has none) | `grep -n 'Alternatives considered'` | moved whole |
| inline `Justification:` clauses in `## Borrowing posture` | 4 (lines 141, 142, 143, 150) | `grep -n 'Justification'` minus the block lines | reconciled in place: label and attributions cut, reasoning kept |
| inline `Justification:` clauses in `## Doc updates` / Slice 3 | 4 (lines 73, 423, 425, 427) | same | **kept with label** — build obligations, not deliberation |
| `## Risks and open questions` items | 4 | `awk '/^## Risks/,/^## Out of scope/' \| grep -c '^- \*\*'` | moved whole |

Total `Justification:` occurrences at `HEAD` was 16 = 8 blocks + 4 Borrowing-posture + 4 Doc-updates; the remaining spec carries 4, all Doc-updates/Slice-3 obligations.

**Rules for the move, discharged.** Every Decision keeps a one-line pointer to the rationale file (the preamble paragraph names it once for the whole spec, and each rationale entry is keyed back by heading and anchor). Prose the current contract falsifies was **deleted, not moved** — enumerated in the rationale's "Deleted outright" list: the `draft` status line, everything asserting no `ready()`, the `docs/README.md` heading-bump and surgical-removal mechanics, the `docs/TREE.md` `[alpha]`-tag instruction, three broken citations, and the `Django>=5.2` restatement. The move was verified rather than assumed; see `### Validation run`.

**Anchors.** The rationale file's Decision headings are reference-style, so the rendered heading — and therefore the slug — is the link label alone. All eight cross-file targets were re-derived by slugging the spec's actual headings and differencing the used set, not by transcription. **Three anchors in the spec had never resolved before this pass**, across 20 uses, and were repaired as a side effect of the rewrite — measured by running the same sweep over `git show HEAD:docs/SPECS/spec-021-apps-0_0_7.md` in a scratch path outside the repo: `#decision-4--no-readyhook-in-0_0_7` (11 uses; two defects at once — a dotted version slugs to `007`, and `hook` is its own token), `#decision-6--joint-0_0_7-cut` (7 uses; the same dotted-version defect), and `#slice-3--promotion--docs` (2 uses; `Slice 3: Promotion + docs` is a checklist list item, not a heading, so it never had a slug — both uses now point at `#slice-checklist`, the heading that contains it). All three now resolve, and so does every other anchor in both files.

### Half B — spec reconciliation

Recorded in full under `### Spec changes made (Worker 1 only)`.

### Tests added or updated

None. This cohort writes no source or tests; `tests/test_apps.py` was read as evidence for F2 and is unmodified.

### Validation run

- `uv run ruff format .` / `uv run ruff check --fix .` — **not applicable**; this pass touches no `.py` file. Both are per-`.py` gates and running them repo-wide would reformat files this cohort does not own.
- Markdown scaffold check, scoped to this cohort's two `.md` files: `uv run python scripts/check_trailing_commas.py --check docs/SPECS/spec-021-apps-0_0_7.md docs/SPECS/appx/spec-021-apps-0_0_7-rationale.md` → exit 0. Both files carry the `<!-- LINK DEFINITIONS -->` delimiter and all ten canonical group headers in order, verified by reading as well as by the script.
- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-021-apps-0_0_7.md` → `OK: 12 terms - all have glossary entries and at least one spec link.`, exit 0. Same result as the plan's pre-flight step 6, so the move stranded no term. One term needed re-homing to keep it that way: `DjangoListField` was carried **only** by Decision 3's rejected-alternatives list, which moved; it is now a normative bullet in Decision 3 stating the export discriminator.
- **Move-completeness sweep over the rewritten spec** (occurrences, not matching lines):
  - `grep -oiE 'rev[0-9]+ [HML][0-9]+' … | wc -l` → **0** (was 73 whole-file / 53 outside the revision block)
  - `grep -oiE '\brev[0-9]|revision [0-9]' … | wc -l` → **0** (catches the `rev1-rev5` / `revision 6` spellings the first pattern misses)
  - `grep -c 'Revision history\|Risks and open questions'` → **0**
  - `grep -oc 'Alternatives considered'` → **0**
  - `grep -o 'spec-016' … | wc -l` → **0** (was **17 occurrences across 10 lines**; `grep -c` reports 10 and would have understated the population by 7)
  - `grep -o 'Justification:' … | wc -l` → **4**, all Doc-updates / Slice-3 no-edit obligations, verified by line (50, 359, 361, 363)
- **In-page anchor sweep, both files**, by slugging every heading outside fenced blocks and differencing the `](#…)` uses: rationale — 27 headings, 3 distinct anchors used, all resolve. Spec — 31 headings, 15 distinct anchors used, all resolve except one **false positive**: `(#django-appconfig)` is not an in-page anchor but part of the `#"substring"` citation `docs/GLOSSARY.md #"[Django `AppConfig`](#django-appconfig)"`, which resolves in `docs/GLOSSARY.md` (4 occurrences there).
- **Cross-file anchor sweep**, rationale → spec: all 8 `[spec-021-dN]` definitions resolve against slugs re-derived from the spec's current headings.
- **Reference-link integrity, both files:** no undefined use and no unused definition in the spec; in the rationale every `][ref]` use is defined and every definition used. Every non-URL path in both link blocks was disk-exists-checked, including the new `appx/spec-021-apps-0_0_7-rationale.md` target from the spec and the four `../`-relative targets from `appx/`.
- **Citation resolution, every `#"substring"` written or kept:** `django_strawberry_framework/conf.py #"Import-time side effect: install the signal receiver"` (1), `#"Package settings, read from the host project's"` (1), `pyproject.toml #"Django>=5.2"` (resolves as a substring of `Django>=5.2.16`), `examples/fakeshop/config/settings.py #"\"django_strawberry_framework\","` (1), `docs/TREE.md #"## Test layout"` / `#"## django_strawberry_framework (current on-disk layout)"` / `#"## django_strawberry_framework (target package layout)"` / `#"## strawberry_django"` / `#"## graphene_django"` (all present), `docs/GLOSSARY.md #"[Django `AppConfig`](#django-appconfig)"` (4).
- `git status --short` after the edits:

```
 M docs/SPECS/spec-021-apps-0_0_7.md
 D docs/builder/build-020-list_field-0_0_7.md
?? docs/SPECS/appx/spec-021-apps-0_0_7-rationale.md
?? docs/builder/DONE/build-020-list_field-0_0_7.md
?? docs/builder/build-021-apps-0_0_7.md
```

Every path this cohort wrote is in its writable list. The `build-020` deletion and its `DONE/` copy are the plan's declared baseline-dirty concurrent-session paths (`AGENTS.md` rule 34 — neither edited nor reverted). `docs/builder/build-021-apps-0_0_7.md` is Worker 0's own plan for this cycle, untracked because it is new. `docs/builder/worker-memory/` is gitignored, so this artifact and the memory file do not appear here; the artifact is added by the same write that sets `Status: built`. Nothing unexpected; nothing reverted.

- No `pytest` run with any `--cov*` flag. One read-only collection was run to measure F2's population: `uv run pytest tests/test_apps.py --no-cov --collect-only -q` → `8 tests collected`.

### Failability proofs

None; this pass introduced no new boundary.

### Hot-path budget

Not applicable; plan declares no hot path.

### Floor verification

Not applicable; plan declares floor-verification scope none.

### Implementation notes

- **Decision 4's replacement was written from the source, not from the dispatch prompt.** `django_strawberry_framework/apps.py` and all three `_*_patches.py` module docstrings were read first. Three facts the prompt did not carry came out of that reading and are now in the spec because a builder would otherwise get them wrong: the three imports inside `ready()` are **function-local** (so importing the module outside Django pulls in no patch module — which is what keeps the Edge-cases re-import bullet true); the `APPLY_UPSTREAM_PATCHES` gate lives inside each `apply()` and **not** in `ready()`, so the dispatcher is unconditional and the gate is per dependency; and each `apply()` is self-healing across a module reload, which is what the third `ready()` test exists to pin.
- **The patch inventory is deliberately not restated.** `ready()`'s own docstring says each patch module's docstring is the single source of truth for what it hardens and that the dispatcher repeats none of it. Decision 4 adopts the same rule and says so — a spec-side copy of that inventory would be a second thing to keep true, which is the exact failure this round is closing.
- **Decision 4's negative half was kept, not deleted with the positive claim.** Four things `ready()` still does not do (no `finalize_django_types`, no consumer-type imports, no `setting_changed` receiver, no checks/signals/commands) are what the Non-goals, the three forbidden keys and Goal 3 all rest on. Deleting the whole Decision would have stranded those.
- **Decision 4's heading changed, so its anchor did.** Every use was retargeted, and the old anchor is recorded as having been broken *before* this pass for an unrelated reason (dotted-version slugging), so a reviewer does not read the change as this pass breaking it.
- **The `## Current state` `conf.py` bullet gained a sentence rather than losing one.** The bullet's import-time-not-`ready()` argument is true of the settings singleton and was being read as a general argument against `ready()` work; it now says explicitly that it does not generalize, because the patch dispatch has the opposite requirement.
- **Slice checklist boxes were left `- [ ]`.** They record a shipped card's slice plan, and the `Status:` line is the source of truth for completion; ticking them retroactively would assert an audit this pass did not perform. Consistent with `docs/GLOSSARY.md`-generation memory that a Done card's boxes stay unticked.
- **The `## Implementation plan` "Total expected delta: ~95 lines" sentence was deleted rather than re-estimated.** It summed three estimates the table already carries, and a shipped spec does not need a forecast of its own size.
- **Definition of done item 8 ("package coverage stays at 100%") was deliberately left unchanged.** It states the repository's standing CI gate — a true completion criterion — and is not in tension with item 13's rule that a *worker* does not assert coverage. Both were read together before either was touched.

### Notes for Worker 3

- The diff is large and almost entirely prose. The highest-value read is the F1 reconciliation table in the rationale file's Decision 4 entry: it lists all eighteen sites the falsified claim reached with was/now for each, and is the instrument for checking the fix is not partial. Auditing it against the spec is cheaper than re-deriving the site list.
- Three counts in the build plan's own `## Verified findings` are wrong and are corrected here with the measurement beside each: F2's "7 test functions" (it is 8), F7's "seven Decisions" with a `Justification:` block (it is all eight), and F7's "six" `Alternatives considered` lists (it is seven). F7's "~45" attribution parentheticals is approximately right; the measured figure outside the revision-history block is 53. `docs/builder/build-021-apps-0_0_7.md` is Worker 0's file and was **not** edited.
- The one in-page anchor the sweep flags in the spec is a false positive: `(#django-appconfig)` is inside a `#"substring"` citation into `docs/GLOSSARY.md`, not a link. Re-derive rather than accepting; the sweep script is in the session scratchpad, not the repo.
- `check_spec_glossary.py` exits 0, but that is a weaker signal than it looks: it proves each of the 12 terms has **at least one** link. `DjangoListField` had exactly one, in text this pass moved out, and would have gone unlinked if the re-home had been missed. Worth a look at where each term's surviving carrier is.
- Nothing under `django_strawberry_framework/`, `tests/` or `examples/` was touched, so `git diff -- django_strawberry_framework/__init__.py` is empty and the public-surface check is trivially satisfied.

### Notes for Worker 1 (spec reconciliation)

Carried forward for the final-verification pass and, where marked, for the `### Deferred work catalog` in `bld-final.md`.

- **Three count corrections against the build plan's `## Verified findings`**, each measured this pass, none of which changes any finding's direction:
  - F2 states the `HEAD` file carries **7** test functions. It carries **8** (`grep -c '^def test_' tests/test_apps.py` → 8; `pytest --collect-only -q` → `8 tests collected`). F2's paired claim — three tests the spec does not describe — is correct: 8 − 4 positive − 1 negative = 3. The total was wrong while the delta was right, which is what a count-by-subtraction looks like when only the subtrahend was measured.
  - F7 states a `Justification:` block under **seven** Decisions. It is **eight** — all of them (`grep -n '^Justification:$'` → lines 213, 245, 261, 276, 295, 305, 322, 337).
  - F7 states an `Alternatives considered (and rejected):` list under **six** Decisions. It is **seven** — Decisions 1, 2, 3, 4, 6, 7, 8; Decision 5 is the only one without (`grep -n 'Alternatives considered'` → 7 lines).
- **For R2 (do not act on it here — `docs/GLOSSARY.md` and `KANBAN.md` are R2's).** The spec's `## Doc updates` section now prescribes the corrected target text for both DB-backed bodies, so R2 has a satisfiable target rather than a prescription it must reinterpret: the GLOSSARY entry body should name the **three**-applier dispatch and the `APPLY_UPSTREAM_PATCHES` gate and should *not* restate which upstream bug each module fixes (each patch module's docstring owns that); the KANBAN Done body should read "plus a `ready()` body that dispatches the package's three upstream-patch appliers" in place of "no `ready()` body in 0.0.7".
- **`CHANGELOG.md`'s `[0.0.7]` `### Added` entry carries the same understatement and is in neither cohort's ownership.** It says the `ready()` body "imports `django_strawberry_framework._django_patches` and calls `apply()`" — one applier, where three ship. That was accurate when `300e2811` landed and was falsified by `c7cb5f5c`. `AGENTS.md` forbids `CHANGELOG.md` edits without explicit instruction, and this cycle grants none. **Deferred-work catalog candidate.**
- **`[spec-016]` / `[spec-017]` ref-id residue survives in five sibling files** — `docs/SPECS/spec-022-export_schema-0_0_7.md`, `docs/SPECS/spec-023-multi_db-0_0_7.md`, `docs/SPECS/spec-025-scalar_map_helper-0_0_7.md`, `docs/SPECS/spec-027-filters-0_0_8.md` and `KANBAN.md`. Every definition resolves (the targets are post-renumber filenames), so nothing is broken; it is a naming inconsistency each file's own next cycle owns. Not this cohort's writable set. **Deferred-work catalog candidate.**
- **`docs/SPECS/spec-022-export_schema-0_0_7.md` still carries `Status: draft (revision 5, post-rev4 feedback).`** on a card `KANBAN.md` lists as `DONE-022-0.0.7`, shipped in the same `0.0.7` release. Same defect class as F3, on a spec this cycle does not own. Noticed while modelling F3's replacement on the sibling archived specs. **Deferred-work catalog candidate.**
- **`docs/SPECS/spec-025-scalar_map_helper-0_0_7.md`'s status line says "Only the final test-run gate remains"** on a shipped card. Same class. **Deferred-work catalog candidate.**
- **Decision 6 bundles four cards; `KANBAN.md` records `0.0.7` as having shipped seven** (`DONE-020` through `DONE-026`). The Decision's four is the WIP set at authoring time excluding the already-shipped `DONE-020-0.0.7`; `DONE-024-0.0.7` and `DONE-026-0.0.7` joined the release afterwards. The version-bump policy is unaffected, so the Decision was left stating its bundle and the discrepancy is recorded in the rationale rather than "corrected" into a claim the Decision never made. Flagged in case final verification prefers the other resolution.

---

## Final verification (Worker 1)

Pending — performed by a fresh Worker 1 invocation after Worker 3's review.

### Spec changes made (Worker 1 only)

Every edit to `docs/SPECS/spec-021-apps-0_0_7.md`, with the cited passage, a one-line reason, and the finding that triggered it.

| # | Spec passage (as it read at `HEAD`) | Change | Reason | Finding |
|---|---|---|---|---|
| 1 | `Status: draft (revision 6, post-rev5 build-readiness audit).` | → `Status: shipped (`0.0.7`, 2026-05-27); archived. Card `DONE-021-0.0.7`.` | The card shipped and the spec is archived; modelled on `spec-020`'s shipped status line. | F3 |
| 2 | preamble, after `Predecessors:` | Added the rationale-pointer paragraph naming `spec-021-apps-0_0_7-rationale.md`. | `worker-1.md` rule 1 — a reader who cannot see that deliberation exists re-litigates settled alternatives. | F7 |
| 3 | `Revision history (kept inline so the spec is self-contained):` block, lines 8-33 | Deleted from the spec; moved whole to the rationale. | The deliberative layer leaves the spec. | F7 |
| 4 | 53 `(revN Xn)` parentheticals across 34 lines, lines 35-466 | Deleted; each change recorded once, under the decision it touched, in the rationale. | An attribution is not an argument; carrying it per sentence multiplies its cost by the spawn count. | F7 |
| 5 | `Justification:` blocks under Decisions 1-8 | Label and chronology cut; the positive arguments re-set as body prose where they change how the thing is built, otherwise moved. | `worker-1.md` — implementation-relevant rationale stays. | F7 |
| 6 | `Alternatives considered (and rejected):` under Decisions 1, 2, 3, 4, 6, 7, 8 | Moved whole to the rationale, keyed per Decision. | Rejected alternatives are the rationale file's core content. | F7 |
| 7 | `## Risks and open questions`, four items | Section deleted; moved whole with each item's resolution recorded. | Every pair had resolved by the ship; one was falsified four days before it. | F7, F4 |
| 8 | `### Decision 4 — No `ready()` hook in `0.0.7``, "`__dict__` MUST NOT contain a `ready` key" | Retitled `### Decision 4 — `ready()` applies the upstream patches`; body rewritten to the shipped dispatch, the gate's placement, idempotence, reload behavior, and an explicit "what `ready()` does NOT do" list. | The shipped code inverted it inside the same release; the spec states the current contract directly, with no amendment block. | F1 |
| 9 | Slice 1 sub-bullet "Do NOT implement `ready()` … do NOT set `default_auto_field` … `label` … `default`" | Split into a positive `ready()`-dispatch sub-bullet and a three-attribute forbiddance sub-bullet. | A checklist Worker 0 copies verbatim must not instruct the opposite of the contract. | F1 |
| 10 | Slice 2 negative-shape sub-bullet, four-key set | Narrowed to three keys with `"ready"` named as deliberately absent; a third sub-bullet added for the three `ready()` tests. | Matches `tests/test_apps.py` at `HEAD`. | F1, F2 |
| 11 | `## Goals` item 3, "by omitting `ready()`, `default_auto_field`, and any signal / check / management-command wiring" | Rewritten: the hook exists for exactly the patch dispatch; the `AGENTS.md` rule restated as "a hook lands with the feature that needs it, never ahead of one". | The rule was never violated — its antecedent came true. | F1 |
| 12 | `## Goals` item 2, "the four-test plan … plus the one consolidated negative-shape test" | Rewritten to the eight tests that shipped. | Measured, not estimated. | F2 |
| 13 | `## Non-goals` item 1, "`ready()` body — checks, signals, …" | Scoped to "a `ready()` body **beyond the upstream-patch dispatch**"; a new Non-goal added for the patch content itself. | The four exclusions remain true; only the blanket prohibition was false. | F1 |
| 14 | `## Borrowing posture` "**No `ready()`.**" bullet, and the heading "borrow the AppConfig shape verbatim" | Bullet replaced with "**One deliberate behavioral divergence: `ready()`**"; "verbatim" dropped from the heading. | With `ready()` and two docstrings the shape is not verbatim, and the sub-bullets already say which parts diverge. | F1 |
| 15 | `## Problem statement`, "no hook for future Django-integration work (a `ready()` site for a check, …)" and the shipping-bar paragraph | Rewritten: the hook is for work that must run once the app registry is populated; the shipping-bar paragraph names the `ready()` override. | The hook is no longer hypothetical. | F1 |
| 16 | `## Current state` `conf.py` bullet | Kept, plus one sentence: the import-time constraint is specific to the settings singleton and does not generalize. | Without it the bullet reads as an argument against any `ready()` work — which is how Decision 4 used it. | F1 |
| 17 | `## Current state` bullet, "`apps.py` … lists `apps.py # [alpha] Django AppConfig` with the `[alpha]` tag" | Rewritten to "the target layout … already reserves the path"; `docs/TREE.md` citation retargeted to the section heading. | The tag is gone and the cited substring resolved nowhere. | F1 |
| 18 | `## Test plan`, five tests / four forbidden keys | Rewritten to eight tests: four positive kept verbatim, the negative-shape narrowed to three keys, three `ready()` tests added, each described by what it distinguishes. | Measured against `tests/test_apps.py`. | F2 |
| 19 | `## Implementation plan` table, Slice 1 `+10 / -0`, Slice 2 "5" tests `+60 / -0`; "Total expected delta: ~95 lines" | → `+45 / -0`, 8 tests, `+185 / -0`; total-delta sentence deleted. | `wc -l` gives 43 and 184; the total summed estimates the table already carries. | F2 |
| 20 | `## Edge cases` — `INSTALLED_APPS` ordering bullet | "Because this card adds no `ready()` body" replaced with the real reason (process-global replacements, no cross-app state, idempotent `apply()`). | Conclusion unchanged, premise corrected. | F1 |
| 21 | `## Edge cases` — "`AppConfig.ready` is called during `django.setup()`" bullet | Rewritten: the patches are installed before any row runs, so an observing test must revert the slots first and restore in a `finally`. | The one transferable instruction for any later card testing an app-load side effect. | F1 |
| 22 | `## Edge cases` — coverage bullet, "two attribute assignments and a docstring" | Adds the `ready()` override and the three tests that cover it. | The class body grew a method. | F1 |
| 23 | `## Edge cases` — re-import bullet, "the module just defines a class" | Adds that the patch-module imports are function-local. | That is *why* the claim is still true. | F1 |
| 24 | `## Edge cases` — Multiple-AppConfigs bullet, four-key set | Narrowed to three keys; the dual-edit requirement kept. | Matches the shipped test. | F1, F2 |
| 25 | `## Edge cases` — "already pins `Django>=5.2`" | → `Django>=5.2.16`. | `pyproject.toml` pins `Django>=5.2.16`; the `#"Django>=5.2"` citation still resolves as a substring and was kept. | citation sweep |
| 26 | `## Doc updates` — GLOSSARY body, "no `ready()` body in `0.0.7`" | → the three-applier dispatch and the gate, with an instruction not to restate the patch inventory. | Gives R2 a satisfiable target. | F1 |
| 27 | `## Doc updates` — `docs/README.md` heading-bump and surgical-removal bullets | Replaced with the landed obligation (add the shipped bullet; remove only the `Django AppConfig` mention from the forward-looking list). | The `(0.0.6)` heading and the `Coming in 0.1.0` bullet no longer exist; the obligation is satisfied and the mechanics are recorded in the rationale. | F1 |
| 28 | `## Doc updates` — `docs/TREE.md` bullets and their `#"apps.py                  # Django AppConfig"` citation | Restated to the landed shape; citations retargeted to the two section headings. | The cited substring resolved nowhere after the TREE regenerate. | citation sweep |
| 29 | `## Doc updates` — KANBAN Done body text, "no `ready()` body in `0.0.7` (deferred to the card that needs one)" | → "plus a `ready()` body that dispatches the package's three upstream-patch appliers". | Gives R2 a satisfiable target. | F1 |
| 30 | `## Doc updates` — CHANGELOG entry text, "No `ready()` body in `0.0.7`." | → "the `ready()` body applies the package's upstream patches at app-load time". | The prescribed text was false. | F1 |
| 31 | `## Out of scope` — "a future card would land its own AppConfig `ready()` body" | → "would extend `ready()`"; a new first bullet added putting the patch modules' content out of scope, naming `DONE-024-0.0.7`. | Decision 4 now points at three modules this card does not own. | F1 |
| 32 | Definition of done item 1, "no `ready()` body" | Clause removed; the other four absences kept. | The absence is false at `HEAD`. | F1 |
| 33 | Definition of done item 4, "the 5 tests … `{"ready", "label", "default_auto_field", "default"}`" | → 8 tests, three forbidden keys, the three `ready()` tests named. | Measured. | F2 |
| 34 | Definition of done item 6, four absences all pinned by the consolidated test | → three absences pinned by the consolidated test; the `ready()` override and behavior pinned by its own three tests. | Matches the shipped test file. | F1 |
| 35 | Definition of done item 9 | "`ready()` included" made explicit. | Two of the five doc surfaces still understate the dispatch. | F1 |
| 36 | `## Key glossary references` — `docs/TREE.md #"single-file Layer-3 module tests"` and `#"apps.py                  # Django AppConfig"`; `## Current state` and Decision 1's `#"once it earns 3+ files"` | All retargeted to `docs/TREE.md #"## Test layout"` / `#"## django_strawberry_framework (current on-disk layout)"` / `#"## …(target package layout)"`. | None of the three substrings survives the TREE regenerate. | citation sweep |
| 37 | `## Current state` and Decision 4 — `django_strawberry_framework/conf.py #"Library settings."` | → `#"Package settings, read from the host project's"`. | The module docstring's first line was rewritten; the rev5 M1 anchor no longer resolved. | citation sweep |
| 38 | Link definition `[spec-016]: spec-020-list_field-0_0_7.md` and all 17 `spec-016` token occurrences (10 lines: 6, 10, 53, 72, 74, 269, 303, 307, 436, 497) | Ref-id renamed to `[spec-020]`; every use and every bare-prose mention now names `spec-020`. Remaining count: 0. | The ref-id named the pre-renumber number while its target named the post-renumber file. | F4 |
| 39 | Risks entry "the four remaining `0.0.7` WIP cards (017, 018, 019, 045)" | Carried into the rationale with the corrected ids `DONE-021`, `DONE-022`, `DONE-023`, `DONE-025`, re-derived against `KANBAN.md`'s release line and Done-column spec table, not translated. | A card list is a claim; re-derive before rewriting. | F4 |
| 40 | Anchors `#decision-4--no-readyhook-in-0_0_7` (11 uses), `#decision-6--joint-0_0_7-cut` (7 uses) and `#slice-3--promotion--docs` (2 uses) | Retargeted to `#decision-4--ready-applies-the-upstream-patches`, `#decision-6--joint-007-cut` and `#slice-checklist`. | All three had **never** resolved — a dotted version slugs to `007`, `hook` is its own token, and `Slice 3: Promotion + docs` is a list item with no slug. Repaired as a side effect of the rewrite, not broken by it. | F1, anchor sweep |
| 41 | Link definitions | Added `[spec-021-rationale]`, `[spec-024]`, `[readme-root]`; `[readme]` disambiguated (it named both `docs/README.md` and `README.md` at `HEAD`). | The `[readme]` collision made two "no edits to `README.md`" bullets link to `docs/README.md`. | F7, link sweep |
| 42 | Decision 3 | Added a normative bullet naming [`DjangoListField`][gloss] as the contrasting export decision. | Re-homes the term whose only glossary-link carrier was the moved rejected-alternatives list. | F7 |

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[gloss]: ../GLOSSARY.md#djangolistfield

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->

---

## Review (Worker 3)

Reviewed: the working-tree diff of `docs/SPECS/spec-021-apps-0_0_7.md` (modified) and `docs/SPECS/appx/spec-021-apps-0_0_7-rationale.md` (new), against `git show HEAD:docs/SPECS/spec-021-apps-0_0_7.md` written to a scratch path outside the repo, `django_strawberry_framework/apps.py`, `django_strawberry_framework/conf.py`, `tests/test_apps.py`, and the plan's `## Verified findings`. No `git stash` / `checkout` / `restore` / `worktree` was used at any point.

**Tree drift since the build report's `git status --short`:** one further concurrent-session path (`docs/feedback.md`) is now modified. Not this cohort's, not edited, not reverted (`AGENTS.md` rule 34). The three declared baseline-dirty paths are unchanged.

**Independent re-derivations performed** (numbers were re-measured, never accepted):

| Claim | Where stated | Re-derived | Verdict |
|---|---|---|---|
| spec `HEAD` 97,518 -> 64,868 bytes; rationale 60,403 | artifact + rationale | `wc -c` | correct |
| 53 `(revN Xn)` outside the revision block, 73 whole-file | artifact `Half A` | `sed -n '35,513p' … \| grep -oiE 'rev[0-9]+ [HML][0-9]+' \| wc -l` -> 53; whole file -> 73 | correct |
| 8 standalone `Justification:` blocks; 7 `Alternatives considered` lists; 16 total `Justification` occurrences | artifact + plan corrections | `grep -c '^Justification:$'` -> 8; `grep -c 'Alternatives considered'` -> 7; `grep -o 'Justification' \| wc -l` -> 16 | correct |
| 17 `spec-016` occurrences across 10 lines; 6 body uses with `spec-016` as the visible label; 3 bare-prose mentions | rationale `## Renumber residue` | 17 occurrences / 10 lines; 7 `][spec-016]` uses of which the `Predecessors:` one renders as `spec-020`, leaving 6; token arithmetic 6*2 + 1 + 1 + 3 = 17 | correct, exactly |
| 8 test functions in `tests/test_apps.py` | artifact count correction | `grep -c '^def test_'` -> 8 | correct (the plan's 7 was wrong; the correction is right) |
| spec: 31 headings, 15 distinct in-page anchors, one `(#django-appconfig)` false positive | artifact `### Validation run` | own slugger + use-extractor: 31 headings, 15 distinct, 14 resolve, the 15th is inside `docs/GLOSSARY.md #"[Django `AppConfig`](#django-appconfig)"` | correct |
| rationale: 27 headings, 3 distinct in-page anchors, all resolve | same | 27 / 3 / all resolve (`-renumber-residue`, `decision-4--ready-applies-the-upstream-patches`, `provenance-of-this-record`) | correct |
| 8 `[spec-021-dN]` cross-file anchors resolve into the spec | same | all 8 match current spec slugs | correct |
| Three anchors were **already broken at `HEAD`**, 11 / 7 / 2 uses | artifact `Half A` + row 40 | slugged the `HEAD` copy: real slugs were `decision-4--no-ready-hook-in-007` and `decision-6--joint-007-cut`, and `Slice 3: Promotion + docs` is a list item with no slug; uses at `HEAD` were 11, 7, 2 | correct; the pre-existing-at-`HEAD` attribution holds and all three now resolve |
| "eighteen sites" reached by the falsified claim | artifact + `### Notes for Worker 3` | the rationale's own table carries **19** data rows, and is missing at least one further site | **wrong** — see Medium 2 |
| "This file is smaller than that [32,650]" | rationale `## Provenance of this record` | 60,403 vs 32,650 | **wrong by 27,753 bytes** — see High 1 |

**Dispatched findings checklist walk** (`BUILD.md` `### Dispatched findings checklist`): F1, F2, F3, F4, F7 are all ticked `- [x]`.

- **F1 — tick stands.** I searched the rewritten spec independently rather than reading the table: `grep` for `ready` intersected with every negation spelling (`no ready`, `not … ready`, `MUST NOT`, `omit`, `defines no`, `adds no`, `absent`, `without`) returns no surviving assertion, implication, or dependency on "no `ready()`". The four-key forbidden set is gone (`"ready"` now appears only as a *required* key). Section-level `diff` of the `HEAD` heading list against the current one shows exactly three changes — two heading rewrites and `## Risks and open questions` removed — so no section was silently lost. The **fix is complete**; what is wrong is the record of it (Medium 2).
- **F2 — tick stands.** Spec now says eight tests everywhere it counts them (Goals 2, Implementation-plan table, Test plan, DoD 4); the three forbidden keys match `tests/test_apps.py`; the three `ready()` test names match the file.
- **F3 — tick stands.** `Status: shipped (`0.0.7`, 2026-05-27); archived. Card `DONE-021-0.0.7`.` is byte-shaped identically to `spec-020`'s and `spec-019`'s, and `KANBAN.md #"`0.0.7` shipped 2026-05-27 with seven cards"` confirms the date.
- **F4 — tick is over-broad.** The two sub-items the finding names (the `[spec-016]` ref-id, the Risks card list) are both fixed and re-derived clean. But the same defect class survives untouched in this spec's own `## Out of scope` and `## Explicitly do not borrow` — see Medium 3.
- **F7 — tick stands.** The rationale file exists, is keyed per Decision by heading and anchor, and every moved population measures 0 in the spec.

**Rationale-file read before reviewing** (`BUILD.md` `### Who reads it, and when`). It stopped me re-raising two things: deleting Decision 4 outright, and enumerating the patch inventory in the Decision — both are recorded as rejected with their reasons, and both reasons hold.

### High:

#### The rationale file's byte accounting is inverted, and the sentence is false by 27,753 bytes

`docs/SPECS/appx/spec-021-apps-0_0_7-rationale.md` `## Provenance of this record`:

```docs/SPECS/appx/spec-021-apps-0_0_7-rationale.md:17
The spec shed 32,650 bytes. This file is smaller than that, and the difference is not a copy
that went missing: it is the `(revN Xn)` attributions themselves …, the sentences that only
repeated a contract stated elsewhere in the spec, and the passages the shipped code falsifies,
which were **deleted** rather than moved …
```

Measured: `wc -c docs/SPECS/appx/spec-021-apps-0_0_7-rationale.md` -> **60,403**. The shed is `97,518 - 64,868` = **32,650**. The file is **larger** by 27,753 bytes, not smaller. The paragraph's whole explanatory logic runs the wrong way: it explains a deficit that does not exist and therefore explains nothing about the surplus that does.

Two things make this worse than a typo. First, the same pass's build report states the opposite in plain terms — "It is larger than the shed amount because it is not only a destination" — so one pass shipped contradictory accounts of one measurement, and the false one is in the **standing doc** while the true one is in a per-cycle scratchpad that closes with the cycle. Second, the paragraph declines to state the number at all ("A byte count of this file written by the pass that is still writing it would be a guess"), which is the right instinct, and then asserts a *comparison against that unstated number* — which is the same guess wearing a different grammatical form. `BUILD.md` `## Claims are proven mechanically, never accepted on prose` names this exact shape: measure as you write the number.

**Recommended change.** Replace the sentence with the measured figure and the true accounting: the file is 60,403 bytes, larger than the 32,650 shed, because it is not only a destination — it also carries the F1 site table, the four-commit chronology, the count corrections, and the `## Provenance` / `## Claims the spec may no longer make` / `## Left open by this pass` apparatus, none of which existed in the spec to be moved. Keep the deletion-not-move explanation, but as an explanation of why the *move* alone does not account for the shed, not of a deficit.

**Test expectation:** none (no behavior). Verification is `wc -c` on both files, quoted in the corrected paragraph.

### Medium:

#### The F1 reconciliation table declares itself exhaustive and is not; three counts keyed to it are wrong

`docs/SPECS/appx/spec-021-apps-0_0_7-rationale.md` `### [Decision 4 …]`, the table introduced by "a partial claim fix is this cycle's dominant defect, so the list is exhaustive". The table has **19** data rows (lines 175-193). Against that:

- The build report and `### Notes for Worker 3` both say **eighteen** ("every one of the eighteen sites", "the eighteen-site reconciliation table", "it lists all eighteen sites"). Nineteen.
- `## Provenance of this record` says Decision 4's falsification "reached **ten** further sites". It reached eighteen further sites by the table's own count.
- `### `## Edge cases and constraints`` says "**Four of the seven** bullets asserted or assumed the absence of `ready()`; all four are reconciled in the table". `## Edge cases and constraints` has **eight** bullets at `HEAD` and eight now, and **five** of them were F1-touched.

The fifth Edge-cases bullet is the substantive half of this finding. At `HEAD` the **Multiple AppConfigs in `apps.py`** bullet carried the four-key set `{"ready", "label", "default_auto_field", "default"}`; the spec now carries the three-key set, so **the fix landed** — but the site appears in neither the "exhaustive" table nor any `Changed by R1` prose. Two further F1-tagged sites (`## Problem statement`'s hook clause and shipping-bar paragraph; `## Current state`'s `conf.py` bullet) are recorded in the rationale's own `### `## Problem statement` and `## Current state`` entry but are likewise absent from the list that claims to be exhaustive.

Why it matters beyond arithmetic: the artifact tells the next reader that this table "is the instrument for checking the fix is not partial" and that "auditing it against the spec is cheaper than re-deriving the site list". An instrument that omits a site it covered, under a banner declaring itself complete, is worse than no instrument — the next pass will trust it and stop looking. That is the same failure mode this whole round exists to close, one level up.

**Recommended change.** Add the `## Edge cases` Multiple-AppConfigs row and the two `## Problem statement` / `## Current state` rows to the table (or drop the word "exhaustive" and point at the per-section entries as the completing half — but then say so). Correct the three counts to the table's own row count, measured at the time of writing. Correct "seven bullets" to eight.

#### F4's renumber residue survives in this spec's own `## Out of scope`, and contradicts itself inside one file

F4 is "renumber residue in the spec's own references". The two sites the finding names are fixed. Four more are not:

```docs/SPECS/spec-021-apps-0_0_7.md:372:375
- Channels ASGI router ([`DjangoGraphQLProtocolRouter`][…]): `TODO-ALPHA-029` for `0.0.12`.
- [Debug-toolbar middleware][…]: `TODO-ALPHA-031` for `0.0.12`.
- [Response-extensions debug middleware][…]: `TODO-ALPHA-032` for `0.0.12`.
- Test-client helpers ([`TestClient`][…], [`GraphQLTestCase`][…]): `TODO-ALPHA-033` for `0.0.12`.
```

Re-derived against `KANBAN.md`: `029` is now `DONE-029-0.0.9` (`DjangoType` consumer-DX cleanup), `031` is `DONE-031-0.0.9` (GlobalID encoding), `032` is `DONE-032-0.0.9` (full Relay), `033` is `DONE-033-0.0.9` (connection-aware optimizer). None of the four ids denotes the feature the bullet attaches it to, and the `0.0.12` targets are wrong twice over — `docs/GLOSSARY.md` records both `DjangoGraphQLProtocolRouter` and `Debug-toolbar middleware` as **shipped (`0.0.14`)**. So four bullets in the archived spec name shipped work as future work under card ids belonging to other cards.

The file also contradicts itself: line 132 attributes `TODO-ALPHA-029` to the **debug-toolbar**, while line 372 attributes it to the **Channels ASGI router** and line 373 gives the debug-toolbar `031`. One of those was already wrong before the renumber.

This is `ARTIFACT.md`'s Documentation / release sanity bullet twice: "version strings, shipped/planned statuses, and card IDs match … the package version after the slice", and "no obsolete 'coming soon', 'planned', or old-version wording remains in files the slice deliberately updated". The pass rewrote this file end to end.

**Recommended change.** Re-derive each of the five ids against `KANBAN.md` (never translate them — the same discipline row 39 of the spec-changes table already applied to the Risks card list) and restate each bullet with the current card id and the version it actually shipped in, or state it as shipped and drop the card id. Fix the line-132 / line-373 contradiction in the same edit. If the maintainer would rather leave a shipped spec's out-of-scope pointers frozen at authoring time, that is a defensible call — but it has to be **recorded**, and `## Renumber residue` currently reads as though the spec's own residue is closed.

#### The citation sweep's completeness claim is false; ten kept `#"substring"` citations do not resolve

`### Validation run` states: "**Citation resolution, every `#"substring"` written or kept**", then enumerates eleven. The file carries **37** `#"` citations. Every one in the bracketed-path form — `[`AGENTS.md`][agents] #"…"`, `[`KANBAN.md`][kanban] #"…"`, `[`docs/builder/BUILD.md`][build] #"…"` — was skipped by the sweep, and ten of them do not resolve:

| Citation | Status |
|---|---|
| `AGENTS.md #"Add settings keys only when the feature that needs them lands"` (x3) | `AGENTS.md:20` reads "Add a settings key only when the feature that needs it lands; never preemptively" — paraphrase, not substring |
| `AGENTS.md #"always recommend the root-cause fix over the surface patch"` | `AGENTS.md:5` reads "Always give the root-cause fix even when slower" — paraphrase |
| `AGENTS.md #"Do not update CHANGELOG.md unless explicitly instructed"` (x2) | `AGENTS.md:21` reads "No CHANGELOG.md updates unless told" — paraphrase |
| `AGENTS.md #"Test placement: three test trees with no overlap"` | paraphrase |
| `KANBAN.md #"`0.0.7` is the active patch"` | `KANBAN.md:64` now reads "`0.0.14` is the active patch" — genuinely stale |
| `KANBAN.md #"The last `0.0.7` card to ship owns the version bump from `0.0.6` per Decision 10"` | absent from `KANBAN.md` |
| `KANBAN.md #"### DONE-021-0.0.7 — `apps.py` and Django app config"` | `KANBAN.md:4016` renders `### [DONE-021-0.0.7 - …](…)` — hyphen not em-dash, and bracketed |
| `docs/builder/BUILD.md #"The spec's nested sub-bullets for this slice from `## Slice checklist`"` | that text lives in `ARTIFACT.md:52`, not `BUILD.md` |
| `docs/builder/BUILD.md #"`uv run ruff format .` — pass/fail"` and `#"`uv run ruff check --fix .` — pass/fail"` | that text lives in `ARTIFACT.md:73-74`, and now reads `<files this pass touched>` |

All ten are **pre-existing at `HEAD`** — I confirmed each against the read-only `HEAD` copy — and the `AGENTS.md` paraphrase form is a repo-wide convention shared by **23** archived specs, so repairing that class is emphatically not this cohort's job. The defect is the **claim**, which reads as a completed sweep and will be treated as one: `BUILD.md` `## Claims are proven mechanically, never accepted on prose` grades an unverified claim of this shape Medium on its own.

**Recommended change.** Narrow the sentence to what was actually swept ("every `path #"substring"` citation in bare-path form"), and add one bullet recording the bracketed-path class: the count, that it is pre-existing at `HEAD`, that the `AGENTS.md` sub-class spans 23 specs and is out of scope, and that the four non-`AGENTS.md` ones (two stale `KANBAN.md`, two mis-targeted at `BUILD.md` instead of `ARTIFACT.md`) are either repaired here or routed to the deferred-work catalog. The four are inside this cohort's writable file and cost one edit each.

#### `## Left open by this pass` omits a same-class falsified claim in a sibling spec

The section says "Two items this round did not close, recorded so the next pass does not have to re-derive them." A third exists and is closer to F1 than either of the two listed:

```docs/SPECS/spec-022-export_schema-0_0_7.md:98
The predecessor [`docs/SPECS/spec-021-apps-0_0_7.md`][spec-017]'s
[Decision 4][spec-017-decision-4--no-readyhook-in-0-0-7] deliberately deferred any
[`Django AppConfig`][glossary-django-appconfig] `ready()` body.
```

`spec-022` is a `DONE-022-0.0.7` card in the same release. It asserts, in its own body and again at line 478, the exact claim `300e2811` falsified — and it asserts it *about the file R1 just rewrote*, so after this pass the two specs openly contradict each other. Its ref-id `[spec-017-decision-4--no-readyhook-in-0-0-7]` also targets `#decision-4--no-readyhook-in-0_0_7`, which never resolved (verified against the `HEAD` copy: the real slug was `decision-4--no-ready-hook-in-007`), so this pass did not break it — but a reader who diffs the two will assume it did.

The recorded residue for those five sibling files is the **ref-id naming inconsistency**, described as "nothing is broken … a naming inconsistency each file's own next cycle owns". That description is true of `spec-023` / `spec-025` / `spec-027` / `KANBAN.md` and **false of `spec-022`**, which carries a substantive false claim on top of the naming residue. A catalog is a claim; this one under-describes its own population.

**Recommended change.** Add a third bullet to `## Left open by this pass` naming `spec-022` lines 98 and 478 specifically, the false claim (not merely the ref-id), and the dead anchor with its pre-existing-at-`HEAD` attribution — and mirror it into `### Notes for Worker 1 (spec reconciliation)` so it reaches `bld-final.md`'s `### Deferred work catalog`. Editing `spec-022` is correctly outside this cohort's ownership; recording it accurately is not.

### Low:

#### Rationale link definitions are not alphabetical within their group

`docs/SPECS/appx/spec-021-apps-0_0_7-rationale.md`, `<!-- docs/SPECS/ -->` group: `spec-020`, `spec-021-d1` … `spec-021-d8`, `spec-021`. `[spec-021]` sorts before `[spec-021-d1]` and must come first. `START.md` "Markdown link convention" requires alphabetical ordering within each group; `scripts/check_trailing_commas.py --check` passes because it validates the scaffold, not the ordering, so the script's exit 0 is not evidence here. The spec's own block is correctly ordered in every group — I checked both files mechanically.

#### A live source comment cites this card by its pre-renumber spec number

`tests/test_apps.py` #"The spec-017 "no ready() body in" attributes the superseded stance to `spec-017`. Post-renumber, `docs/SPECS/spec-017-deferred_scalars-0_0_6.md` is an unrelated spec, so the comment now points a reader at the wrong document; the stance belongs to `spec-021`. Not load-bearing (the comment's substance is right), and `tests/` is outside both cohorts' ownership — the plan forbids source and test edits. Recording it as a deferred-catalog item is the whole of the ask.

### DRY findings

The two files are the corpus; the move's point is that content is not duplicated between them.

- **No duplication between spec and rationale.** Mechanically checked: zero exact-duplicate sentences over 90 characters, and zero pairs above 0.85 similarity across the two files. This is the strongest single piece of evidence that the pass performed a MOVE rather than a copy, and it is a better instrument than the vocabulary sweeps the artifact records, because it catches a passage that was reworded on the way across.
- **Same argument told twice within the rationale, defensibly.** The `## Provenance of this record` "Deleted outright" list and the `## Claims the spec may no longer make` table both narrate the `docs/TREE.md` `[alpha]` tag, the `conf.py #"Library settings."` anchor, the two dead `docs/TREE.md` substrings, the `docs/README.md` heading-bump, and the `Django>=5.2` restatement — five items, twice each. The table is explicitly framed as "An index of the retractions above", which is a legitimate index-vs-body relationship rather than duplication, so I am **not** raising it as a defect. Flagging it only so the next editor knows that correcting one of those five means correcting two places.
- **The five-file `[spec-016]` / `[spec-017]` residue is stated three times** — `## Renumber residue`, `## Left open by this pass`, and the artifact's `### Notes for Worker 1`. Two of the three are in the same file. Collapsing `## Left open by this pass`'s bullet to a pointer at `## Renumber residue` would remove one, and Medium 5 requires touching that bullet anyway.
- **Existence challenge: none raised.** This cohort creates no abstraction, helper, registry, or indirection layer — it produces prose. The one structural question worth asking, whether the rationale file should exist at all, is settled by `BUILD.md` `## Spec rationale extraction` and by 25 sibling specs already carrying one.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` returns **zero lines**. `__all__` and the re-export list are untouched. Consistent with the plan's declaration that no cohort in this cycle writes package source, and with `git status --short`, which shows no path under `django_strawberry_framework/`, `tests/`, or `examples/` in this cohort's diff.

### CHANGELOG sanity

Not applicable; slice did not modify CHANGELOG.md.

(The spec's *prescribed* CHANGELOG text was corrected — spec-changes row 30 — but `CHANGELOG.md` itself is untouched and is out of both cohorts' ownership. The live `[0.0.7]` entry's own understatement is verified real under `### Notes for Worker 1` below.)

### Documentation / release sanity

Applicable and load-bearing — the diff is an archived spec plus its new companion. Walked bullet by bullet against `ARTIFACT.md`:

- **Version strings, shipped statuses, card IDs.** `Status: shipped (`0.0.7`, 2026-05-27); archived. Card `DONE-021-0.0.7`.` matches `KANBAN.md:62` ("`0.0.7` shipped 2026-05-27 with seven cards", `DONE-021-0.0.7` named) and is byte-shaped identically to `spec-020`'s and `spec-019`'s status lines. Version strings in the file: 57 `0.0.7`, 3 `0.0.6`, 4 `0.0.12`. **The four `0.0.12`s are wrong** — see Medium 3.
- **KANBAN card movement.** Not applicable; this cohort moves no card (R2 owns the DB-backed surfaces).
- **Links point at existing files.** All 28 spec definitions and all 14 rationale definitions were disk-exists-checked from each file's own directory, including the new `appx/spec-021-apps-0_0_7-rationale.md` target and the rationale's four `../` and `../../` hops. Zero misses, zero undefined uses, zero unused definitions in either file. Both carry the `<!-- LINK DEFINITIONS -->` delimiter and all ten canonical group headers in the exact required order. The `[readme]` / `[readme-root]` collision is genuinely fixed: `[readme]` -> `../README.md` (i.e. `docs/README.md`) under `<!-- docs/ -->`, `[readme-root]` -> `../../README.md` under `<!-- Root -->`, and both "No edits to `README.md`" bullets (spec lines 50 and 359) now use `[readme-root]`. Ordering is clean in every spec group; one rationale group is not — Low 1.
- **Archival preserves the historical record; live follow-up state stays in the durable docs.** Satisfied. Every population cut from the spec is either in the rationale or in its `Deleted outright` list with a reason, and the section-level `diff` against `HEAD` confirms no section vanished unaccounted. Live follow-ups are routed rather than dropped: the two DB-backed bodies to R2, `CHANGELOG.md` and the sibling-file residue to the deferred catalog. `docs/SPECS/appx/spec-021-apps-0_0_7-terms.csv` already existed and is untouched, so the spec's two tracked siblings are now both present.
- **Verbatim-copy check.** The spec prescribes text for the GLOSSARY entry, the KANBAN Done body and the CHANGELOG entry; none is copied *from* the spec into another file by this diff, so there is nothing to `diff` character-for-character this pass. R2 inherits that obligation, and the artifact's note to R2 correctly gives it a satisfiable target.
- **No obsolete "planned" / "coming soon" / old-version wording.** The three `planned for 0.0.7` occurrences are quotations of the `docs/GLOSSARY.md` status value that Slice 3 flips — correct, not stale. `## Current state`'s present-tense framing ("Django currently synthesizes an implicit `AppConfig`") describes the pre-card world, which is what the section is for and matches the sibling archived specs. **`## Out of scope`'s four future-tense bullets are genuinely obsolete** — Medium 3.
- **Script-rendered docs.** Not applicable; this cohort regenerates nothing. The spec's `docs/TREE.md` citations were retargeted to section headings precisely because the regenerate had rewritten the previously-cited lines, which is the right direction (a heading is stable across regenerates; a rendered description is not).

### What looks solid

- **The move is a move, proven independently of the pass's own instruments.** Zero cross-file sentence duplication above 90 characters at any similarity threshold down to 0.85. Every moved population measures 0 in the rewritten spec under patterns I chose rather than the ones the artifact recorded: `rev1`-`rev6`, `revision`, `superseded`, `formerly`, `previously`, `originally`, `no longer`, `used to`, `Alternatives considered`, `Revision history`, `Risks and open questions`. The spec nowhere narrates its own history. The two survivors are correct: the preamble's one-line rationale pointer, which `BUILD.md` requires, and the four `## Doc updates` / Slice-3 `Justification:` labels, which are build obligations and are explicitly reasoned about in the rationale's `Reconciled in place` list rather than left as an oversight.
- **F1's fix — as distinct from its record — is complete.** I re-derived the population from the `HEAD` copy rather than from the table, and found no site where the falsified claim survives in any spelling.
- **The count corrections are the pass's best work.** Three of the plan's own `## Verified findings` numbers were wrong (7 vs 8 test functions, seven vs eight `Justification:` blocks, six vs seven `Alternatives considered` lists). The pass measured them, corrected them, recorded the command beside each, and correctly did **not** edit Worker 0's plan. All three corrections re-derive exactly. The diagnosis attached to the test-count error — "the total was wrong while the delta was right, which is what a count-by-subtraction looks like when only the subtrahend was measured" — is the kind of note that stops the next recurrence, not just this one.
- **The pre-existing-at-`HEAD` anchor attribution is exactly right, and was the easiest claim in the diff to fake.** Three anchors, 11 / 7 / 2 uses, all three broken at `HEAD` for two independent reasons (a dotted version slugging to `007`, and `hook` being its own token) plus a third that was never a heading at all. Every number and every diagnosis reproduces against the read-only `HEAD` copy. Retargeting `#slice-3--promotion--docs` to `#slice-checklist` — the heading that *contains* the list item — rather than inventing a heading is the correct call.
- **Decision 4's replacement is verified against source, not against the prompt.** I read `django_strawberry_framework/apps.py` and `conf.py::upstream_patches_enabled` independently. Every claim holds: function-local imports (so `import django_strawberry_framework.apps` outside Django pulls in no patch module, which is what keeps the re-import edge case true); dispatch order `django` -> `strawberry` -> `cross_web`; the `APPLY_UPSTREAM_PATCHES` gate inside each `apply()` and **not** in `ready()` (confirmed at `_django_patches.py:397`, `_strawberry_patches.py:789`, `_cross_web_patches.py:342`); the per-dependency mapping form `{"django": False}` leaving the others installed (confirmed in the `upstream_patches_enabled` docstring); idempotence and reload-healing. The `## Implementation notes` bullet naming these as "three facts the prompt did not carry" is accurate — they are not derivable from the dispatch prompt, and a reader of the old spec would have got all three wrong.
- **Keeping Decision 4's negative half was the right structural call.** Deleting the Decision with its falsified positive claim would have stranded the Non-goals, the three forbidden keys, Goal 3, and the `finalize_django_types` argument, all of which rest on it. The explicit "what `ready()` does NOT do" list preserves the discipline through the inversion, and the rationale records the delete-it-outright alternative with that reason.
- **The `## Current state` `conf.py` bullet gained a sentence instead of losing one.** The import-time-not-`ready()` argument is true of the settings singleton and was being read as a general argument against `ready()` work — which is exactly how the old Decision 4 used it. Saying explicitly that it does not generalize is the fix that stops the next author re-deriving the wrong conclusion from a true premise.
- **`DjangoListField`'s re-home was caught, and the note about why `check_spec_glossary.py` exiting 0 is a weak signal is correct.** The term's only glossary-link carrier was inside Decision 3's rejected-alternatives list, which moved; the checker only proves *at least one* link exists, so it would have stayed green if the term had been left with zero carriers in a *different* spec's sweep. I re-ran it: `OK: 12 terms`. Turning the rejected alternative into a normative bullet — the export discriminator is whether consumers write the symbol by hand — is a better outcome than a link-preserving mention, because it states the rule the next card applies.
- **Slice-checklist boxes correctly left `- [ ]`.** Ticking a shipped card's boxes retroactively would assert an audit this pass did not perform, and the `Status:` line is the source of truth. Consistent with prior practice on Done cards.
- **DoD item 8 correctly left alone.** "Package coverage stays at 100%" states the repository's standing CI gate and is not in tension with item 13's rule that a *worker* does not assert coverage. The note that both were read together before either was touched is the right level of care for a pair that looks contradictory at a glance.

### Temp test verification

- No temp tests were written. `docs/builder/temp-tests/r1/` is unused and remains empty. This cohort changes no executable behavior, so a temp test could demonstrate nothing an assertion about prose cannot.
- Verification instead ran through three throwaway Python scripts held in the session scratchpad **outside the repository** (heading-slugger, in-page-anchor-use extractor, link-definition/disk-exists/alphabetical checker) plus the read-only `HEAD` copy of the spec, also outside the repository. Nothing was written inside the tree by this review.
- `scripts/review_inspect.py`: **skipped**, recorded reason — `BUILD.md` `### When to run the helper during build` scopes it to `.py` files, and this cohort's diff contains none. Same reason the plan's pre-flight step 2 recorded the skip.
- Focused `pytest`: **not run**, and none is owed. No `--cov*` flag was used anywhere in this pass.
- Failability proofs: **none owed and none recorded**. The diff introduces no boundary, guard, gate, or rejection path — it introduces prose. `BUILD.md` `### What needs a proof, and what does not` scopes the obligation to boundaries, and Worker 3's mandatory re-run floor is therefore an empty set, which `worker-3.md` permits only in exactly this case. My source carve-out was not exercised: no production file was mutated, at any point, for any reason.
- Hot-path budget: not applicable; the plan declares no hot path and no cohort touches executable code.
- Floor verification: not applicable; the plan declares floor-verification scope `none`, and this diff touches no Django / Strawberry / channels integration seam.

### Notes for Worker 1 (spec reconciliation)

**On the three deferrals R1 already recorded — I verified each rather than endorsing it, and all three are real:**

1. **`CHANGELOG.md`'s `[0.0.7]` entry understates the dispatch. CONFIRMED.** The live entry reads "The `ready()` body imports `django_strawberry_framework._django_patches` and calls `apply()` to install the Django Trac #37064 hardening at app-load time" — one applier where three ship. Accurate when `300e2811` landed, falsified by `c7cb5f5c`. `AGENTS.md` forbids `CHANGELOG.md` edits without instruction and this cycle grants none. **Belongs in `bld-final.md`'s `### Deferred work catalog`, not this cycle.** One caveat for whoever writes the catalog: the same `[0.0.7]` section labels this card `017-appspy_and_django_app_config-0.0.7`, pre-renumber — same defect class, same section, and `KANBAN.md:364` already records a *separate* renumber problem in that section ("14 occurrences across 7 distinct" pre-renumber card labels). Do not state the CHANGELOG residue's population from R1's one-line description; re-derive it.
2. **`[spec-016]` / `[spec-017]` ref-id residue in five sibling files. CONFIRMED, but the described population is wrong in one direction and the description is wrong for one file.** Every one of the five carries a mismatched definition (`spec-022:732-738`, `spec-023:673-675`, `spec-025:709-710`, `spec-027:1267-1268`, `KANBAN.md:5286`). Two cautions for the catalog: (a) raw `grep -c 'spec-01[67]'` over those files massively overstates it — `spec-016-fieldmeta_consolidation-0_0_6.md` and `spec-017-deferred_scalars-0_0_6.md` are *real current filenames*, so most token hits are legitimate references to different specs; the residue is the **definition lines whose ref-id and target disagree**, which is 7 in `spec-022`, 3 in `spec-023`, 2 each in `spec-025` / `spec-027`, 1 in `KANBAN.md`. (b) The claim "nothing is broken" is true of four of the five and **false of `spec-022`** — see Medium 5. **Belongs in the deferred catalog**, with the population re-derived as definition lines.
3. **`spec-022` and `spec-025` carry non-shipped `Status:` lines. CONFIRMED.** `spec-022:4` reads `Status: draft (revision 5, post-rev4 feedback).` on a card `KANBAN.md` lists as `DONE-022-0.0.7`; `spec-025:4` reads "Only the final test-run gate remains" on a shipped card. Both are F3's defect class on specs this cycle does not own. Worth noting that `spec-023:4` is already correct, so the pattern is not uniform and each file needs its own look. **Deferred catalog.**

**New items this review adds, none of which the round recorded:**

4. **`spec-022` asserts the claim F1 retired, about this very spec** (`spec-022:98` and `:478`). Medium 5 above. This is materially more than the naming residue item 2 describes, and after this pass the two `0.0.7` specs contradict each other in writing. Its `[spec-017-decision-4--no-readyhook-in-0-0-7]` definition also targets an anchor that never resolved (verified against the `HEAD` copy — not broken by this pass, but a reader will assume it was). **Deferred catalog, and worth flagging to the maintainer as the highest-value of the four, because it is a false statement rather than a naming inconsistency.**
5. **`tests/test_apps.py` cites `spec-017` for this card** — Low 2 above. Post-renumber that number names an unrelated spec. `tests/` is outside every cohort's ownership this cycle. **Deferred catalog.**
6. **The spec's own `## Out of scope` renumber residue** — Medium 3. Unlike items 2-5 this one is **inside R1's writable set**, so it is a fix for this cycle rather than a catalog entry, unless the maintainer's call is to freeze a shipped spec's forward pointers at authoring time — in which case the decision needs recording in the rationale, since `## Renumber residue` currently implies the spec's own residue is closed.

**On Decision 6's four-card bundle vs `KANBAN.md`'s seven** — R1 left the Decision stating its authoring-time bundle and recorded the discrepancy in the rationale rather than "correcting" it into a claim the Decision never made. **I endorse that resolution.** Decision 6's subject is the version-bump policy, which is unaffected by which cards later joined the release, and rewriting the bundle would make the Decision assert something it never decided. The rationale's note is the right place for it. No action needed; recorded so final verification does not re-open it.

**Escalated: none.** Every finding above is resolvable inside R1's own writable set or is a recording obligation; none turns on spec context Worker 2 could not supply, and none is a contract-level question for the maintainer — except the one explicitly offered as such in Medium 3 (freeze vs re-derive the out-of-scope card pointers), which needs a decision only if Worker 1 declines the re-derive.

**Routing note.** `Status: revision-needed` on this cohort routes to **Worker 1**, not Worker 2 — the plan declares R1's sequence as Worker 1 -> Worker 3 -> Worker 1 with no Worker 2, because only Worker 1 may mutate a spec and Worker 2 may never read a rationale file. Isolation is preserved: the revision pass is a build pass, and a fresh Worker 1 invocation still owns final verification afterwards.

### Review outcome

`revision-needed`.

The **substantive work is right**: the MOVE is a genuine move with zero cross-file duplication, F1's reconciliation is complete against a population I re-derived from `HEAD` rather than from the pass's own table, Decision 4's replacement is verified true against `apps.py` and `conf.py`, the three anchors really were broken at `HEAD`, and the three count corrections against the build plan all reproduce exactly.

What fails is the **record of that work**, and it fails in the one way this cycle exists to close. A pass whose entire product is accurate prose shipped a byte-accounting sentence that is false by 27,753 bytes and contradicts its own build report (High 1); a site table that declares itself exhaustive while omitting a site it fixed, with three separate counts keyed to it wrong (Medium 2); a completed-sweep claim covering eleven of thirty-seven citations (Medium 4); a "left open" catalog that under-describes its own population (Medium 5); and one part of a dispatched finding's own defect class left in the spec with no deferral and an internal contradiction (Medium 3).

Each is a claim that reads as measured and is not. `BUILD.md` grades that Medium on its own; High 1 earns its tier by being false rather than merely unverified, by living in the standing doc while the true version lives in a scratchpad that closes with the cycle, and by making the move's completeness unauditable from the record a future reader will actually have.

All five are correctable inside `docs/SPECS/spec-021-apps-0_0_7.md` and `docs/SPECS/appx/spec-021-apps-0_0_7-rationale.md`. None requires re-doing the move.

---

## Build report (Worker 1, pass 2 — apply-changes)

Closes the five findings Worker 3 set `revision-needed` on. Every one was the same defect — a claim that reads as measured and was not — so each is closed by measuring first and writing the measurement with the command beside the number, never by restating the claim. No prior artifact entry was edited.

### Files touched

- `docs/SPECS/appx/spec-021-apps-0_0_7-rationale.md` — the byte accounting rewritten around the real numbers (High 1); the F1 site table re-derived from `HEAD` with its population defined before it is counted (Medium 2); the `## Edge cases` bullet counts re-measured; the `## Renumber residue` entry given the spec's own `## Out of scope` residue with the re-derivation and the freeze-vs-re-derive decision; a whole-spec citation sweep in all three syntactic forms added to `## Provenance of this record` (Medium 4); `## Left open by this pass` given a third bullet for `spec-022` and the sibling-file population restated as definition lines (Medium 5); the `<!-- docs/SPECS/ -->` link definitions re-sorted (Low 1).
- `docs/SPECS/spec-021-apps-0_0_7.md` — `## Out of scope`'s four renumber-residue bullets re-derived against `KANBAN.md` and restated, the `## Borrowing posture` mention that contradicted them corrected, and seven stale `#"substring"` citations repaired (Medium 3, Medium 4). Two new link definitions: `[artifact]`, `[spec-020-decision-10]`.
- `docs/builder/bld-review-1-rationale_and_spec_reconciliation.md` — this entry.
- `docs/builder/worker-memory/worker-1.md` — memory entry appended.

The artifact's two header reference lines carried pass 1's byte figures, which this pass falsified by editing both files; they now read the measured post-pass sizes. That is the file header, not a prior entry — no entry above `## Build report (Worker 1, pass 2 — apply-changes)` was altered.

**Measured byte counts (`wc -c`, taken after the last edit of this pass):**

| File | At `HEAD` `51eb47ba` | After this pass |
|---|---|---|
| `docs/SPECS/spec-021-apps-0_0_7.md` | 97,518 | 64,941 |
| `docs/SPECS/appx/spec-021-apps-0_0_7-rationale.md` | 0 (did not exist) | 74,395 |

The spec's shed across both R1 passes is 32,577 bytes; the rationale file is 74,395, larger by 41,818. The rationale states the same four figures, and they converge: the paragraph asserting them was written with fixed-width placeholders, the file measured, and the digits substituted at equal width so the substitution could not move the number it reports.

### Tests added or updated

None; this cohort writes no tests.

### Validation run

- `uv run ruff format .` / `uv run ruff check --fix .` — **not applicable**; no `.py` file was touched.
- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-021-apps-0_0_7.md` → `OK: 12 terms - all have glossary entries and at least one spec link.`, **exit 0**. Unchanged from pass 1: no glossary carrier moved, and the reference-integrity check below confirms no definition went unused.
- Markdown scaffold check on this cohort's own two files: `uv run python scripts/check_trailing_commas.py --check docs/SPECS/spec-021-apps-0_0_7.md docs/SPECS/appx/spec-021-apps-0_0_7-rationale.md` → **exit 0**.
- **Citation sweep, all three syntactic forms, both files.** The instrument that produced Medium 4 was anchored on a literal path and therefore never matched the reference-style form; this one extracts every `#"…"` occurrence and recovers its target from either shape. Spec at `HEAD`: **37** citations, 23 resolve, **14 do not**. After this pass: **36** citations, **29 resolve, 7 do not** — and all 7 are the `AGENTS.md` paraphrase class, which spans **25 files / 101 occurrences / 22 distinct substrings across `docs/SPECS/`, of which zero resolve**; 23 of those files are outside this cohort, so the class is left as written and recorded. The 7 repaired occurrences: 1 `BUILD.md`→`ARTIFACT.md` retarget, 2 ruff-gate citations re-homed on `AGENTS.md`, 2 `KANBAN.md` heading citations re-spelled to the rendered bracketed/hyphenated form, 1 `KANBAN.md` version-scoped sentence replaced by the stable `#"### In progress"` heading, and 1 `KANBAN.md` quotation of a sentence that is not in `KANBAN.md` and never was — retired in favour of a direct link to `spec-020`'s Decision 10.
- **In-page anchor sweep, both files, re-run after the last edit** by slugging every heading outside fenced blocks (reference-style headings slug to their label alone; a code-span heading beginning `##` keeps a leading hyphen) and differencing the `](#…)` uses. Spec: 31 headings, 15 distinct anchors used, all resolve except the known false positive `(#django-appconfig)`, which is inside the `docs/GLOSSARY.md` citation and not a link. Rationale: 27 headings, 6 distinct anchors used, all resolve — including the three added this pass (`#-renumber-residue`, `#claims-the-spec-may-no-longer-make`, `#left-open-by-this-pass`).
- **Cross-file anchors, rationale → spec:** all 8 `[spec-021-dN]` definitions re-derived against the spec's current heading slugs — all resolve.
- **Reference-link integrity:** no undefined use and no unused definition in either file (the two apparent "undefined" hits in the rationale, `0-9` and `a-z0-9-`, are character classes inside code spans in the re-derivation commands, not links). Every non-URL definition path disk-exists-checked from its own file's directory, including the two added to the spec.
- **Link-definition ordering re-checked in every group of both files.** The rationale's `<!-- docs/SPECS/ -->` group was the one defect (`[spec-021]` sorted after `[spec-021-d8]`); it is now first. All other groups in both files were already correct.
- `git status --short` after the edits:

```
 M docs/SPECS/spec-021-apps-0_0_7.md
 D docs/builder/build-020-list_field-0_0_7.md
?? docs/SPECS/appx/spec-021-apps-0_0_7-rationale.md
?? docs/builder/DONE/build-020-list_field-0_0_7.md
?? docs/builder/bld-review-1-rationale_and_spec_reconciliation.md
?? docs/builder/build-021-apps-0_0_7.md
```

Both paths this pass wrote are in its writable list and both appear in `### Files touched`. The `build-020` deletion and its `DONE/` copy are the plan's declared baseline-dirty concurrent-session paths (`AGENTS.md` rule 34 — neither edited nor reverted). `build-021` is Worker 0's plan. One further `docs/` path is modified by a concurrent session — the same one Worker 3's review recorded as tree drift; not this cohort's, not edited, not reverted. `docs/builder/worker-memory/` is gitignored. Nothing unexpected; nothing reverted.

- No `pytest` was run, with or without any `--cov*` flag. Nothing in this pass depends on a test run: the eight-test population was already measured in pass 1 and no claim about it changed.

### Failability proofs

None; this pass introduced no new boundary.

### Hot-path budget

Not applicable; plan declares no hot path.

### Floor verification

Not applicable; plan declares floor-verification scope none.

### Implementation notes

- **High 1 was not closed by flipping the sentence's polarity.** The paragraph's whole explanatory logic ran the wrong way: it explained a deficit that does not exist. It now states both measured sizes, states the surplus, says what produces it (the material this file carries that never existed in the spec to be moved — the reconciliation table, the commit chronology, the count corrections, the citation sweep, the provenance/claims/left-open apparatus), and then keeps the deletion-not-move argument in its correct role, as the reason the *move* alone does not account for the shed. The old paragraph's one right instinct — refusing to guess a number — is preserved by the mechanism described above rather than by declining to state it.
- **The F1 table was re-derived, not patched.** Adding the omitted row to a table whose count was inherited would have reproduced the defect one level down. The population is now defined in the rationale before it is counted (a spec passage at `HEAD` that asserts the absence of a `ready()` body, enumerates `"ready"` among the forbidden keys, or states a count the shipped `ready()` falsifies), derived from the union of two instruments, and enumerated in spec order. **It is 30 sites, not 19 and not 18.** The four passages that carry the `ready` token and are deliberately *not* sites are named, so a reader can re-derive the boundary rather than trust it.
- **Neither instrument alone finds the population, and the record says so.** Token-grep over the body finds 37 lines and misses three sites (the `## Implementation plan` cell, the `## Edge cases` coverage bullet, the `## User-facing API` registry sentence); the count-grep finds 9 lines and misses most of the rest. One site — `## Borrowing posture`'s "We do not borrow this" bullet, whose argument closed on "the future-card seam (a `ready()` site reserved for later cards)" — is in neither the artifact's nor the review's site list and was found by reading the section. A finding's grep vocabulary is not its population.
- **All five `## Out of scope` / `## Borrowing posture` card ids were re-derived by feature against `KANBAN.md`, never by number.** As numbers, `029` / `031` / `032` / `033` now name `DONE-029-0.0.9`, `DONE-031-0.0.9`, `DONE-032-0.0.9`, `DONE-033-0.0.9` — none of which is the feature its bullet describes. By feature they are `DONE-041-0.0.14` (Channels ASGI router), `DONE-042-0.0.14` (debug-toolbar middleware), `DONE-043-0.0.14` (test-client helpers) and `DONE-044-0.0.14` (response-extensions debug middleware) — the four cards of the joint `0.0.14` cut, each recorded `shipped (`0.0.14`)` in `docs/GLOSSARY.md`. **The version was wrong on all four bullets, not two**: none shipped in `0.0.12`. The intra-file contradiction is closed in the same edit — `## Borrowing posture` named `029` as the debug toolbar while `## Out of scope` gave `029` to the router and `031` to the toolbar; both now name `DONE-042-0.0.14`.
- **The freeze-vs-re-derive choice offered in Medium 3 was decided, and recorded.** The spec's forward pointers are re-derived rather than frozen at authoring time, because a bullet naming shipped work as future work under another card's id misinforms every reader who follows it. The decision and its reason are in the rationale's `## Renumber residue` entry, which no longer implies the spec's own residue is closed while leaving it open.
- **Nothing in the spec narrates its own history.** The corrections state the current contract flat: the out-of-scope bullets name a card and a shipped version, the repaired citations simply cite the resolving text, and Decision 6 links `spec-020`'s Decision 10 instead of quoting a sentence about it. Every chronology this pass produced went into the rationale, keyed to the section or Decision it belongs to.
- **The `[spec-016]` / `[spec-017]` population was re-derived before being repeated**, not carried forward from either the round's own note or the review's. It is **15 mismatched definition lines** — 7 `spec-022`, 3 `spec-023`, 2 `spec-025`, 2 `spec-027`, 1 `KANBAN.md` — matched as `^\[(spec-01[67][a-z0-9-]*)\]:` against each definition's target, with the two self-consistent `-rationale` definitions in `spec-016` and `spec-017` themselves discarded as false positives. A raw token grep over the same five files reports **104**, because `spec-016-…-0_0_6.md` and `spec-017-…-0_0_6.md` are real current filenames.

### Notes for Worker 3

- The two highest-value reads are the rationale's `## Provenance of this record` (the byte accounting and the citation sweep, both fully stated with their instruments) and the Decision 4 entry's population paragraph immediately above the table. The table is only trustworthy because the paragraph above it says what a member is; audit that definition first, then the rows.
- Three counts in this pass are worth re-deriving independently because they contradict earlier statements in this artifact, all of which stand as written in their own (immutable) entries: the F1 site count is **30**, against "eighteen" in the pass-1 build report and "19 data rows" in the review; `## Edge cases` has **8** bullets of which **5** were F1-touched, against "four of the seven"; and the spec's citation population is **37 before / 36 after**, against the pass-1 claim of a completed sweep over eleven.
- The `(#django-appconfig)` hit in the spec's anchor sweep remains a false positive for the same reason as in pass 1 — it is inside a `docs/GLOSSARY.md` citation, not a link.
- Nothing under `django_strawberry_framework/`, `tests/` or `examples/` was touched; `git diff -- django_strawberry_framework/__init__.py` is empty and the public-surface check is trivially satisfied.

### Notes for Worker 1 (spec reconciliation)

Carried forward for the final-verification pass and, where marked, for `bld-final.md`'s `### Deferred work catalog`. The pass-1 entry's three items stand; Worker 3 confirmed all three and corrected two of the descriptions, and both corrections are re-derived here rather than repeated.

1. **`CHANGELOG.md`'s `[0.0.7]` `### Added` entry understates the dispatch — one applier where three ship.** Accurate when `300e2811` landed, falsified by `c7cb5f5c`. `AGENTS.md` forbids `CHANGELOG.md` edits without instruction and this cycle grants none. **Deferred-work catalog.** Caveat for whoever writes the catalog: the same `[0.0.7]` section labels this card `017-appspy_and_django_app_config-0.0.7`, pre-renumber, and `KANBAN.md` separately records a pre-renumber-label problem in that file. Do not state either population from a one-line description — re-derive both.
2. **`[spec-016]` / `[spec-017]` ref-id residue across five files. Population re-derived this pass: 15 mismatched definition lines** — `spec-022` 7, `spec-023` 3, `spec-025` 2, `spec-027` 2, `KANBAN.md` 1. **Not ~100**: a raw `grep -o 'spec-01[67]'` over those five files reports 104 occurrences, most of them legitimate references to the real `spec-016-fieldmeta_consolidation-0_0_6.md` and `spec-017-deferred_scalars-0_0_6.md`. Two hits that look like residue are not: those two specs' own `[spec-01N-rationale]` definitions point at correctly-named `appx/` companions. **Deferred catalog, stated as definition lines.**
3. **"Nothing is broken" is true of four of those five files and false of `spec-022`.** Verified this pass: `spec-022` states in two places that this spec's Decision 4 "deliberately deferred any `Django AppConfig` `ready()` body" — the claim `300e2811` falsified inside the same `0.0.7` release — so after R1 the two `0.0.7` specs contradict each other in writing. Its `[spec-017-decision-4--no-readyhook-in-0-0-7]` definition also targets an anchor that never resolved (the real `HEAD` slug was `decision-4--no-ready-hook-in-007`), so this pass did not break it, though a reader diffing the two files will assume it did. **This is a false statement, not a naming inconsistency, and is the highest-value of the sibling items.** It is now recorded in the rationale's `## Left open by this pass` as well. **Deferred catalog.**
4. **`spec-022` and `spec-025` carry non-shipped `Status:` lines** — `spec-022` reads `Status: draft (revision 5, post-rev4 feedback).` on a card `KANBAN.md` lists as `DONE-022-0.0.7`; `spec-025` reads "Only the final test-run gate remains" on a shipped card. `spec-023`'s is already correct, so the pattern is not uniform and each file needs its own look. F3's defect class on specs this cycle does not own. **Deferred catalog.**
5. **`tests/test_apps.py` cites `spec-017` for this card in a source comment.** Post-renumber that number names an unrelated spec. **Routed, not fixed here:** Worker 0 records it as finding **F8** and dispatched it to **R2**, which has a Worker 2; `tests/` is outside this cohort's writable set and the file was not touched. Recorded so the catalog does not double-count it.
6. **The `AGENTS.md` paraphrase-citation convention.** 25 files under `docs/SPECS/` carry 101 such citations across 22 distinct substrings and **not one resolves**; 23 of those files are outside this cohort. It is a convention, not rot — `AGENTS.md` is deliberately terse and reworded — but no sweep of any spec's citations can be honestly reported as complete without naming it. **Deferred catalog as a repo-wide decision**, not a per-spec fix.
7. **Decision 6's four-card bundle vs `KANBAN.md`'s seven `0.0.7` cards.** Left as the authoring-time bundle, with the discrepancy in the rationale; Worker 3 endorsed that resolution. Recorded so final verification does not re-open it. **No action.**

### Dispatched findings checklist

- [x] **High 1 — the rationale's byte accounting is inverted.** Closed by measuring both files after the last edit and rewriting the paragraph's accounting logic around the real direction; the stated figures (64,941 / 74,395 / shed 32,577 / surplus 41,818) are the `wc -c` readings of the final files.
- [x] **Medium 2 — the F1 site table declares itself exhaustive and is not; three counts keyed to it are wrong.** Closed by re-deriving the population from `HEAD` with its definition stated, enumerating 30 sites in spec order, and correcting the dependent counts (`ten further sites` → 29; `four of the seven` Edge-cases bullets → five of eight).
- [x] **Medium 3 — F4 renumber residue in the spec's own `## Out of scope`, with an intra-file contradiction.** Closed by re-deriving all five ids by feature against `KANBAN.md`, restating each bullet with its current card id and actual shipped version (`0.0.14`, not `0.0.12`, on all four), fixing the `## Borrowing posture` contradiction in the same edit, and recording the freeze-vs-re-derive decision in the rationale.
- [x] **Medium 4 — the citation sweep's completeness claim is false.** Closed by sweeping all 37 in every syntactic form, repairing the 7 stale occurrences inside this cohort's own file, and recording the `AGENTS.md` paraphrase class with its measured repo-wide population instead of restating an unsupported completeness claim.
- [x] **Medium 5 — `## Left open by this pass` omits `spec-022`'s falsified Decision 4.** Closed by adding the third bullet naming the false claim (not merely the ref-id) and the dead anchor with its pre-existing-at-`HEAD` attribution, restating the sibling population as definition lines, and mirroring both into `### Notes for Worker 1` above.
- [x] **Low 1 — rationale link definitions not alphabetical within their group.** Closed; `[spec-021]` now precedes `[spec-021-d1]`, and every group in both files was re-checked.
- [x] **Low 2 — `tests/test_apps.py`'s `spec-017` provenance comment.** **Routed, not fixed.** Worker 0 records it as F8 and dispatched it to R2; `tests/` is outside this cohort's writable set and the file is untouched. Recorded in `### Notes for Worker 1` item 5.

---

## Review (Worker 3, pass 2)

Reviewed: the working-tree diff of `docs/SPECS/spec-021-apps-0_0_7.md` (modified) and `docs/SPECS/appx/spec-021-apps-0_0_7-rationale.md` (new), against `git show HEAD:docs/SPECS/spec-021-apps-0_0_7.md` written to a scratch path **outside** the repo, plus `django_strawberry_framework/apps.py`, `django_strawberry_framework/conf.py`, `tests/test_apps.py`, `KANBAN.md`, `CHANGELOG.md`, `docs/GLOSSARY.md`, `AGENTS.md`, and the four sibling specs the deferrals name. `HEAD` is `51eb47ba`. No `git stash` / `checkout` / `restore` / `worktree` at any point.

**Method for this pass, stated because the dispatch turns on it.** Every population below was derived from the read-only `HEAD` copy with patterns I chose, **before** reading the corresponding table or paragraph in the diff. Where my number and the pass's agree I name the instrument; where they disagree the disagreement is the finding.

**Tree drift:** one further concurrent-session `docs/` path is modified beyond the three declared baseline-dirty ones. Not this cohort's; not edited, not reverted (`AGENTS.md` rule 34). `tests/test_apps.py` is **untouched** — `git diff --stat -- tests/test_apps.py` is empty and `git status --short tests/` is empty, so F8 is correctly left to R2 and is not re-raised here.

### Independent re-derivations

| Claim | Where stated | My instrument | Result | Verdict |
|---|---|---|---|---|
| spec 64,941 / rationale 74,395 / `HEAD` 97,518 | header, build report, rationale table | `wc -c` on all three now | 64,941 / 74,395 / 97,518 | correct |
| shed 32,577; rationale larger by 41,818 | build report + rationale L18 | `97518-64941`, `74395-32577` | 32,577 / 41,818 | correct |
| "the same four figures … converge" | build report | `grep -n '32,650\|32,577'` on the rationale | rationale L20 still reads **32,650** | **wrong** — High 1 below |
| F1 instrument (a): 37 body lines / 52 pre-strip / 63 whole-file | rationale population paragraph | the exact recorded pipeline | 37 / 52 / 63 | correct, exactly |
| F1 instrument (b): 9 lines | same | the exact recorded grep | lines 10, 13, 19, 66, 106, 356, 372, 391, 457 | correct, exactly |
| "instrument (a) alone misses three sites" | same | mapped all 37 `HEAD` line numbers onto the 30 rows | (a) misses **seven** rows; (a)∪(b) still misses **five** | **wrong** — Medium 1 |
| "the table below carries every member" (30 rows) | Decision 4 entry | row count + re-derivation from `HEAD` | 30 rows counted; one further reconciled site absent | **incomplete** — Medium 2 |
| four passages deliberately not sites | same | read each at `HEAD` | Key-glossary x2, Non-goals x2 — all four still true at `HEAD` | correct |
| `029/031/032/033` → `DONE-041/042/043/044-0.0.14`, version wrong on all four | build report + rationale | `grep -n 'DONE-04[1-5]-' KANBAN.md`; `docs/GLOSSARY.md` status rows | 041 router, 042 toolbar, 043 test client, 044 response-extensions, all `0.0.14`, all `shipped (0.0.14)` | correct, exactly |
| the `## Borrowing posture` / `## Out of scope` contradiction is closed | build report | `grep -o 'DONE-[0-9]\{3\}-0\.0\.[0-9]*\|TODO-ALPHA-[0-9]*'` over the spec | both sites now `DONE-042-0.0.14`; zero `TODO-ALPHA` / `WIP-ALPHA` tokens remain | correct |
| post-repair spec: 36 citations, 29 resolve, 7 fail, all the `AGENTS.md` class | `### Validation run` | own three-form sweep (bare path, backticked, reference-style) | 36 / 29 / 7, and all 7 are `AGENTS.md` paraphrases | correct, exactly |
| the 7 repairs now resolve | same | same sweep | all 7 repaired occurrences resolve | correct |
| `HEAD` spec: 37 citations, 23 resolve, 14 do not | build report `### Validation run` | the pass's own cited command on the `HEAD` copy | **68** occurrences, 23 resolve, 45 do not | **wrong corpus** — Medium 3 |
| `AGENTS.md` class: 25 files / 101 occurrences / 22 distinct / zero resolving | rationale L63 | own sweep over `docs/SPECS/**/*.md` | 23 / 109 / 15, and **two distinct substrings resolve** | **does not reproduce** — Low 1 |
| sibling residue = 15 mismatched definition lines, 7/3/2/2/1 | build report + rationale + notes | `^\[(spec-01[67][a-z0-9-]*)\]:` vs target, over `docs/SPECS` + `KANBAN.md` | 15: `spec-022` 7, `spec-023` 3, `spec-025` 2, `spec-027` 2, `KANBAN.md` 1 | correct, exactly |
| raw token grep reports 104 over those five files | same | `grep -o 'spec-01[67]'` over the five | 104 | correct |
| "discarding the two self-consistent hits" | rationale `## Renumber residue` | same sweep, consistent side | **18** self-consistent definitions exist | imprecise — Low 2 |
| `spec-022` asserts the retired claim "in two places" | rationale `## Left open`, notes item 3 | `grep -n 'ready()' docs/SPECS/spec-022-…` | **three**: `:98`, `:130` (`## Non-goals`), `:478` | **understated** — Medium 4 |
| `spec-022` / `spec-025` non-shipped `Status:`; `spec-023` correct | notes item 4 | `sed -n '4p'` on each | confirmed, all three | correct |
| rationale link definitions now alphabetical in every group | build report | own group-parser + sort over both files | zero out-of-order groups in either file | correct — Low 1 of pass 1 closed |
| `check_spec_glossary` / scaffold check | `### Validation run` | re-ran both | `OK: 12 terms`, exit 0; scaffold exit 0 | correct |
| 8 test functions, three-key forbidden set, three `ready()` test names | F2 closure | `grep -n '^def test_'`, read the file | 8 functions; `{"label","default_auto_field","default"}`; all eight names match the spec character-for-character | correct |

### Dispatched findings checklist walk (pass 2's own seven boxes)

- **High 1 — `- [x]` does not stand.** The paragraph's *logic* is now right and every figure it states except one is measured. One is not: see High 1.
- **Medium 2 — `- [x]` does not stand.** The re-derivation is a real improvement over patching the old table, and the population *is* defined before it is counted, which is what the dispatch asked for. Two things in it are still wrong: Medium 1 and Medium 2.
- **Medium 3 — `- [x]` stands.** Re-derived independently and completely: all four features, all four current card ids, all four shipped versions, the intra-file contradiction, and the freeze-vs-re-derive decision with its reason recorded in `## Renumber residue`.
- **Medium 4 — `- [x]` stands for the repair, not for the population.** The seven repairs land and resolve; the sweep is genuinely three-form now. The `HEAD` attribution of `37 / 23 / 14` is wrong (Medium 3 below) and the repo-wide class figures do not reproduce (Low 1).
- **Medium 5 — `- [x]` does not stand.** The `spec-022` bullet exists and correctly calls the claim false rather than a naming residue, which was the substance of the finding. Its population is one site short (Medium 4 below).
- **Low 1 — `- [x]` stands.** Verified mechanically in every group of both files.
- **Low 2 — `- [x]` (routed) stands.** `tests/test_apps.py` is byte-identical to `HEAD`; the comment is F8 and belongs to R2.

The plan's own `### Dispatched findings checklist` (F1, F2, F3, F4, F7) is all `- [x]` and every tick now holds, including **F4**, which pass 1's review called over-broad — the `## Out of scope` half is closed this pass.

### High:

#### The byte-accounting paragraph still carries pass 1's falsified shed figure, two lines after stating the correct one

`docs/SPECS/appx/spec-021-apps-0_0_7-rationale.md` `## Provenance of this record`:

```docs/SPECS/appx/spec-021-apps-0_0_7-rationale.md:18:20
L18: The spec shed 32,577 bytes. **This file is larger than that, by 41,818 bytes** …
L20: The move alone does **not** account for the shed, and in the opposite direction:
     some of the 32,650 bytes went nowhere.
```

`32,650` is `97,518 - 64,868` — the **pass-1** shed, computed against a spec size this pass falsified by editing the file. The measured shed is `32,577` (`97,518 - 64,941`, re-derived here). One paragraph states the shed twice, 73 bytes apart.

Why this is High rather than a typo. The pass did not merely miss an occurrence; it asserted a mechanism that makes missing one impossible: "*the paragraph asserting them was written with fixed-width placeholders, the file measured, and the digits substituted at equal width so the substitution could not move the number it reports*", and "*The rationale states the same four figures, and they converge*". The paragraph states **five** figures and the fifth does not converge — so the closure evidence for High 1 is itself falsified by the file it describes. This is the same defect High 1 named (a byte number that is false, in the standing doc, while the true one lives in a per-cycle scratchpad that closes with the cycle), surviving the pass that existed to close it.

**Recommended change.** `32,650` → `32,577` at `docs/SPECS/appx/spec-021-apps-0_0_7-rationale.md` `## Provenance of this record` #"some of the 32,650 bytes went nowhere". Then re-grep the whole file for every four-or-more-digit numeral and check each against a `wc -c` taken after the edit — the substitution mechanism is only as good as its occurrence list, and that list is what failed.

**Test expectation:** none (no behavior). Verification is `grep -c '32,650'` → 0 and `wc -c` on both files.

### Medium:

#### The F1 population derivation understates what neither grep found, so a reader who re-derives gets 25 of 30 rows and concludes the table is inflated

`docs/SPECS/appx/spec-021-apps-0_0_7-rationale.md` `### [Decision 4 …]`, **Population** paragraph:

> Instrument (a) alone misses three sites (the `## Implementation plan` table cell, the `## Edge cases` coverage bullet, and the `## User-facing API` registry sentence, which was found by reading the section rather than by either grep)

Both instruments reproduce **exactly** — (a) returns 37/52/63 and (b) returns the nine named lines, verified against the read-only `HEAD` copy. What is wrong is the accounting of what they miss. I mapped all 37 of instrument (a)'s `HEAD` line numbers onto the table's 30 rows; the mapping closes perfectly (32 lines → 16 rows, plus the 4 declared non-sites at `HEAD` lines 40, 41, 115, 118, plus the moved Risks item at 435 = 37). That leaves **seven rows instrument (a) does not reach**, not three:

| Row | `HEAD` site | Carries a `ready` token? | Found by |
|---|---|---|---|
| 9 | `### From strawberry_django — borrow the AppConfig shape verbatim` (L126) | no | reading |
| 12 | `## User-facing API` — `INSTALLED_APPS` walkthrough (L176) | no | reading |
| 13 | `## User-facing API` — registry-lookup closing sentence (L205) | no | reading (**named**) |
| 16 | `## Implementation plan` Slice 2 cell (L356) | no | instrument (b) |
| 20 | `## Edge cases` — re-import bullet (L371) | no | reading |
| 21 | `## Edge cases` — coverage bullet (L372) | no | instrument (b) |
| 30 | `## Definition of done` item 9 (L462) | no | reading |

So (a)∪(b) still misses **five** rows, of which the paragraph names one. The paragraph exists so a reader can re-derive rather than trust; run as written, it recovers 25 rows and leaves five looking unsourced — which reads as an inflated count, the opposite of the reassurance intended. `docs/builder/BUILD.md` `## Claims are proven mechanically, never accepted on prose` grades a claim of this shape Medium on its own, and this one is inside the derivation that the artifact's `### Notes for Worker 3` tells the next reader to "audit first, then the rows".

**Recommended change.** Restate as measured: instrument (a) reaches 23 of the 30 rows; instrument (b) adds 2; **5 were found only by reading**, and name all five (rows 9, 12, 13, 20, 30) rather than one. That is a stronger record than the current sentence, not a weaker one — it is the concrete evidence for the paragraph's own thesis that a finding's grep vocabulary is not its population.

#### The table still omits a site it fixed, under a sentence saying it carries every member

Same paragraph: "*the population is defined before it is counted, and the table below carries every member*". `## Goals` item 1 is not among the 30 rows, and is not among the four passages explicitly declared **not** sites — yet it was an F1 site and this pass reconciled it.

At `HEAD`, `## Goals` item 1 (L105) ended:

```docs/SPECS/spec-021-apps-0_0_7.md:105
… the docstrings are documentation, not behavior, and are exempt from the
negative-shape iteration accordingly (rev4 L2). **Nothing else.**
```

"Nothing else", closing an enumeration of two behavioral attributes and two docstrings, asserts that the class body carries nothing further — which is the first limb of the stated population ("*asserts `apps.py` ships no `ready()` body*"), and which the `ready()` override falsifies. The current spec's Goal 1 ends at "…accordingly." with `Nothing else.` removed, so the pass treated it as falsified and fixed it. The line carries no `ready` token and no count, so neither instrument reaches it; it was reconciled by reading and then not recorded.

This is pass 1's Medium 2 recurring after the re-derivation that was supposed to end it, and it matters for the same reason: the artifact tells the next reader this table is the instrument for checking the fix is not partial. An instrument that omits a site it covered, under a banner of completeness, stops the next pass looking.

**Recommended change.** Add the `## Goals` item 1 row (was: "…exempt from the negative-shape iteration accordingly. **Nothing else.**"; now: the closing absolute dropped, because the class body also carries the `ready()` override) and correct the count to 31, or say plainly that the table carries the sites the two instruments and the reading pass found and that the four declared non-sites plus the moved Risks item complete the `HEAD` accounting. Either is honest; "carries every member" beside a 30 that is 31 is not. Whichever is chosen, re-run the row-to-`HEAD`-line mapping afterwards — the mapping is what surfaced this, and it is cheap.

#### The citation population `37 / 23 / 14` is attributed to `HEAD` and is not `HEAD`'s; the corpus it does describe no longer exists

`### Validation run` (pass 2): "**Spec at `HEAD`: 37 citations, 23 resolve, 14 do not.**" `### Notes for Worker 3`: "the spec's citation population is **37 before / 36 after**". The rationale, `## Provenance of this record`: "The spec carried **37** `#"substring"` citations before this repair (`grep -o '#"' … | wc -l` -> 37)".

Run the pass's own cited command against the read-only `HEAD` copy:

```
grep -o '#"' <HEAD copy> | wc -l   ->  68
```

and my three-form resolver over the same file returns **68 occurrences, 23 resolving, 45 not**. `37` is not `HEAD`'s count under any reading I could construct: 53 outside the moved `Revision history` block, 32 distinct substrings, 68 occurrences.

`37` is nonetheless a real number — it is the count in **pass 1's output spec**, the intermediate file that existed between the two passes. The arithmetic closes exactly: the move dropped 31 citations (68 − 37), all of them non-resolving (45 − 31 = 14), leaving 23 resolving on both sides, and 37 − 1 retired = the 36 the current file carries with 7 failing. The measurement was sound; only its corpus is misnamed, and the corpus it names is a file no future reader can obtain — `HEAD` gives 68, the working tree gives 36, and pass 1's output is gone.

This is the prompt's own test: a count whose corpus is undefined is not re-derivable however correct it happens to be.

**Recommended change.** In the rationale, name the corpus in the sentence: the spec carried 37 citations **immediately before this pass's repair** (i.e. after the pass-1 move), of which 23 resolved and 14 did not; **at `HEAD` the same command returns 68, of which 23 resolve** — the extra 31 all sat in the moved `Revision history` block and none of them resolved, which is why the resolving count is stable across the move. That version is re-derivable from the two files a reader actually has, and it is a better story: it shows the move removed only broken citations.

#### `## Left open by this pass` names two `spec-022` sites; there are three, and the unnamed one is the sharpest

`docs/SPECS/appx/spec-021-apps-0_0_7-rationale.md` `## Left open by this pass`, second bullet: "*At `spec-022`'s `## Problem statement`-adjacent predecessor paragraph and again in its `## Borrowing posture` mirror bullet*" — i.e. `spec-022:98` and `:478`. A third exists, in `## Non-goals`:

```docs/SPECS/spec-022-export_schema-0_0_7.md:130
- A second [`Django AppConfig`][…] hook for the command. … See the
  [`docs/SPECS/spec-021-apps-0_0_7.md`][spec-017] [Decision 4][…] `ready()`-body
  deferral, which is preserved here.
```

`:478` is the weakest of the three — it mirrors a *posture* ("do the minimum the parity story needs"), which survives the inversion. `:130` asserts the deferral as a live fact and says it "is preserved here", which is exactly as false as `:98` and is the site a reader chasing the contradiction would land on. The bullet is otherwise right, and its central correction — that `spec-022` carries a false statement rather than a naming residue — is confirmed and is the highest-value sibling item.

Recording it accurately is the whole ask; `spec-022` is correctly outside this cohort. But this is the third time in this cycle that a self-reported population has been short by one, and the catalog entry is what the next cycle will act on.

**Recommended change.** Name all three sites by section (`## Problem statement`-adjacent predecessor paragraph, `## Non-goals` command-hook bullet, `## Borrowing posture` mirror), grade them (two false assertions, one surviving posture mirror), and mirror the correction into `### Notes for Worker 1` item 3 so `bld-final.md`'s catalog inherits the right population.

### Low:

#### The `AGENTS.md` paraphrase class's repo-wide figures do not reproduce, and its "not one resolves" is contradicted by this pass's own repair

`docs/SPECS/appx/spec-021-apps-0_0_7-rationale.md` `## Provenance of this record`: "*Across `docs/SPECS/`, **25 files carry 101 such citations spanning 22 distinct substrings, and not one of the 22 resolves***".

My sweep over `docs/SPECS/**/*.md` (reference-style and bare-path forms, targets resolved through each file's own definition block) gives **23 files / 109 occurrences / 15 distinct**, and two of the fifteen **do** resolve against `AGENTS.md` — one of them being `` #"`uv run ruff format .` and `uv run ruff check --fix .` after every edit" ``, the substring this pass introduced into `spec-021` as its repair for the two ruff-gate citations. A class defined as "the paraphrase citations" makes "not one resolves" true by construction and the count a count of failures; a class defined as "AGENTS.md citations" makes the claim false. The paragraph does not say which, and the divergence in every digit says the corpus rule differs from mine somewhere.

The **classification is sound and I confirm it independently**: all 7 surviving citations in `spec-021` are `AGENTS.md` paraphrases, all 7 fail identically against the `HEAD` copy, and the same spellings recur across many sibling specs — so "pre-existing convention, out of this cohort's scope" is a real judgement, not a way to stop counting. Only the digits are unreproducible, and they are headed for the deferred catalog as a repo-wide decision.

**Recommended change.** State the corpus rule in the sentence (which files, which target-detection, whether the count is occurrences or distinct substrings, and whether "paraphrase" is defined as "does not resolve"), or drop the four digits and say the class spans most archived specs and is repo-wide. Flag in `### Notes for Worker 1` that the catalog must re-derive it — the same instruction already attached to the `CHANGELOG.md` item.

#### The 15-definition-line derivation says it discarded two self-consistent hits; there are eighteen

Same file, `### `## Renumber residue``: "*discarding the two self-consistent hits (`spec-016`'s and `spec-017`'s own `-rationale` definitions …)*". The population is right — **15**, and the 7/3/2/2/1 split reproduces file-for-file — and the two definitions it names are real. But the sweep it describes returns 33 `^\[spec-01[67]…\]:` definitions across `docs/SPECS` + `KANBAN.md`, of which **18** are self-consistent, not 2: nine more in `appx/spec-016-…-rationale.md`, two in `appx/spec-017-…-rationale.md`, plus `spec-004-rationale`, `spec-018` and `spec-037`. A reader re-running the instrument sees 18 discards where the text promised 2 and cannot tell whether they diverged.

**Recommended change.** "discarding the 18 definitions whose ref-id and target agree — including `spec-016`'s and `spec-017`'s own `-rationale` definitions, which point at correctly-named `appx/` companions".

#### `## Implementation plan` states `+45` / `+185` over measurements of 43 / 184

`docs/SPECS/spec-021-apps-0_0_7.md` `## Implementation plan` gives Slice 1 `+45 / -0` and Slice 2 `+185 / -0`. `wc -l` now: `django_strawberry_framework/apps.py` **43**, `tests/test_apps.py` **184** — and pass 1's own spec-changes row 19 records exactly that ("`wc -l` gives 43 and 184") while writing 45 and 185 into the table. Nothing is false — the column header is "Approx. line delta" and a shipped spec's estimate column is allowed to be an estimate — but the pass held the measurement and wrote a different number into a spec whose entire reconciliation theme is that estimates get replaced by measurements.

**Recommended change.** Either write 43 / 184, or leave the column as the authoring-time forecast it originally was (`+10` / `+60`) and say so. Writing a third number that is neither is the one option with no reading under which it is right.

### DRY findings

- **The MOVE is still a move, re-proved independently.** Over both files, with fenced blocks stripped and sentences longer than 90 characters compared pairwise: **zero exact duplicates and zero pairs above 0.85 similarity** (284 long sentences in the spec, 313 in the rationale). Pass 2 rewrote substantial parts of both files and reintroduced no cross-file duplicate in either direction. This remains the strongest instrument available here, because it survives rewording in a way no vocabulary sweep does.
- **The spec never narrates its own history.** `grep -noiE 'rev[0-9]|revision|superseded|formerly|previously|originally|corrected|no longer|used to|Alternatives considered|Revision history|Risks and open questions'` over the whole spec returns **two hits, both on line 8** — the required rationale-pointer paragraph. Pass 2's new prose (the four `## Out of scope` bullets, the repaired citations, Decision 6's direct link to `spec-020`'s Decision 10) states the current fact flat and puts every chronology in the rationale, exactly as `### Implementation notes` claims.
- **The `[spec-016]` / `[spec-017]` residue is still stated three times** — `## Renumber residue`, `## Left open by this pass`, and `### Notes for Worker 1`. Pass 1's review flagged this; pass 2 did not collapse it, and the three statements have now diverged in precision (the `## Renumber residue` and notes copies carry the instrument, the `## Left open` copy does not). Medium 4 requires touching one of them anyway. Not a defect on its own — an index-vs-body relationship is legitimate — but two of the three live in one file, and the divergence is what makes it worth naming.
- **Existence challenge: none raised.** This cohort creates no abstraction, helper, registry or indirection; it produces prose, and the rationale file's existence is settled by `BUILD.md` `## Spec rationale extraction` and 25 sibling specs.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` returns **zero lines**. `__all__` and the re-export list are unchanged. `git status --short` shows no path under `django_strawberry_framework/`, `tests/` or `examples/` attributable to this cohort, and `tests/test_apps.py` is byte-identical to `HEAD`.

### CHANGELOG sanity

Not applicable; slice did not modify CHANGELOG.md.

(The spec's *prescribed* CHANGELOG text was corrected in pass 1; `CHANGELOG.md` itself is untouched. Its live `[0.0.7]` understatement is re-verified under `### Notes for Worker 1` below.)

### Documentation / release sanity

Applicable — the diff is an archived spec plus its new companion. Walked bullet by bullet against `docs/builder/ARTIFACT.md`:

- **Version strings, shipped statuses, card IDs.** `Status: shipped (`0.0.7`, 2026-05-27); archived. Card `DONE-021-0.0.7`.` matches `KANBAN.md`'s release line. Every card id in the spec now resolves to the feature its bullet names, verified against `KANBAN.md` card-by-card: `DONE-020`, `DONE-021`, `DONE-022`, `DONE-023`, `DONE-024`, `DONE-025`, `DONE-041`, `DONE-042` (x2), `DONE-043`, `DONE-044`. **Zero `TODO-ALPHA` / `WIP-ALPHA` tokens and zero `0.0.12` strings survive** — pass 1's Medium 3 is fully closed, including the intra-file contradiction. All four `0.0.14` attributions are corroborated by `docs/GLOSSARY.md`'s status rows (`shipped (0.0.14)` for all four).
- **KANBAN card movement.** Not applicable; this cohort moves no card.
- **Links point at existing files.** All definitions in both files disk-exists-checked from each file's own directory: **zero missing paths, zero undefined uses, zero unused definitions**. Both files carry `<!-- LINK DEFINITIONS -->` and all ten canonical group headers in the exact required order, and **every group in both files is alphabetical** — pass 1's Low 1 is closed, and the two spec definitions added this pass (`[artifact]`, `[spec-020-decision-10]`) sit in the right groups in the right order. The two apparent undefined refs in the rationale (`0-9`, `a-z0-9-`) are character classes inside code spans in the re-derivation commands, as the build report says.
- **Anchors.** Spec: 31 headings, 15 distinct in-page anchors, 14 resolve and the 15th (`#django-appconfig`) is the known false positive inside a `docs/GLOSSARY.md` citation — confirmed again by reading the line. Rationale: 27 headings, 6 distinct anchors, **all resolve**, including the three added this pass and the code-span heading `` ### `## Renumber residue` `` whose slug keeps a leading hyphen. All 8 `[spec-021-dN]` cross-file definitions resolve against slugs re-derived from the spec's current headings.
- **Archival preserves the record; live follow-up state stays in durable docs.** Satisfied. Every population cut is either in the rationale or in its `Deleted outright` list with a reason. Follow-ups are routed: the two DB-backed bodies to R2 (whose targets the spec's `## Doc updates` now prescribes), `CHANGELOG.md` and the sibling residue to the deferred catalog.
- **Verbatim-copy check.** Nothing is copied *from* the spec into another file by this diff, so there is nothing to `diff` character-for-character. R2 inherits that obligation.
- **No obsolete "planned" / "coming soon" / old-version wording.** The surviving `planned for 0.0.7` occurrences are quotations of the `docs/GLOSSARY.md` status value Slice 3 flips — correct. `## Current state`'s present-tense framing describes the pre-card world, which is the section's job. **The `## Out of scope` future-tense obsolescence pass 1 flagged is gone.**
- **Script-rendered docs.** Not applicable; this cohort regenerates nothing. The `docs/TREE.md` citations remain retargeted to section headings, which is the regenerate-stable form.
- `AGENTS.md` rule 27: `grep -nE '[A-Za-z0-9_/.-]+\.(py|md|toml):[0-9]+'` over both files returns **zero** — no raw `path:NN` in either standing doc; the raw line refs in this review stay inside the `bld-*.md` artifact where `START.md` permits them. Rule 4: neither file mentions the forbidden filenames.

### What looks solid

- **The renumber-residue closure (pass 1's Medium 3) is the best work in this pass and re-derives perfectly.** All five ids were resolved *by feature* against `KANBAN.md`, never by number — and the by-number check is included in the record precisely to show that translating would have produced four wrong cards. The version being wrong on all four bullets rather than two is a correction the dispatch did not anticipate, corroborated independently against `docs/GLOSSARY.md`. The intra-file contradiction is closed in the same edit, the list is reordered into card order, and the freeze-vs-re-derive choice the review offered was actually **decided** and recorded with its reason rather than silently taken.
- **Defining the F1 population before counting it is the right structural answer, and re-deriving beat patching.** Adding the missing row to a table whose count was inherited would have reproduced the defect a level down; the record says so and does the harder thing. The definition is specific enough to argue with — which is how I was able to find both the seven-vs-three error and the Goal 1 omission. That is what a re-derivable claim looks like even when it is wrong at the edges, and it is a large improvement on pass 1.
- **Naming the four passages that carry the `ready` token and are deliberately *not* sites.** I checked all four at `HEAD` (`## Key glossary references`' two bullets, `## Non-goals`' two) and the shipped `ready()` leaves every one of them true. Publishing the boundary rather than only the members is what let me audit it in minutes.
- **The citation sweep's substance.** The three-form extractor is real — it finds the bracketed-path citations the pass-1 instrument was structurally blind to, my independent sweep agrees to the occurrence on the current file (36 / 29 / 7), and all seven repairs resolve. The `KANBAN.md` sentence that "is not in `KANBAN.md` and never was" being retired in favour of a direct link to `spec-020`'s Decision 10 is the correct fix rather than a re-spelling.
- **Decision 4's replacement re-verified against source.** Read `django_strawberry_framework/apps.py` and `conf.py::upstream_patches_enabled` independently: function-local imports, dispatch order `django` → `strawberry` → `cross_web`, the gate inside each `apply()` and not in `ready()`, the `{"django": False}` mapping form leaving the others installed, idempotence and reload-healing. Every clause of Decision 4 holds. The eight test names in the spec match `tests/test_apps.py` character-for-character and the three-key forbidden set matches the file.
- **The sibling-residue population (15 definition lines, 7/3/2/2/1) reproduces file-for-file**, and the 104-token contrast is exactly right. Re-deriving it as *definition lines whose ref-id and target disagree* rather than as token hits is the correct instrument, and it is now stated in the rationale where the next cycle will read it.
- **`spec-022` correctly re-graded from naming residue to false statement.** That regrade is the highest-value thing in the deferral set and it came from re-deriving the pass's own catalog rather than repeating it.
- **The spec still narrates no history**, `check_spec_glossary` still exits 0 at 12 terms, the scaffold check still exits 0, and no source, test or DB-backed surface was touched. `docs/builder/temp-tests/r1/` is still empty.

### Temp test verification

- No temp tests written; `docs/builder/temp-tests/r1/` is unused and empty. This cohort changes no executable behavior.
- Verification ran through five throwaway Python scripts held in the session scratchpad **outside the repository** (a three-form citation extractor-and-resolver, a heading-slugger + anchor-use differ, a link-definition group/order/disk-exists checker, a cross-file sentence-similarity comparator, and a `spec-01[67]` definition-vs-target matcher), plus the read-only `HEAD` copy of the spec, also outside the repository. Nothing was written inside the tree by this review except this artifact section.
- `scripts/review_inspect.py`: **skipped**, recorded reason — `BUILD.md` `### When to run the helper during build` scopes it to `.py` files and this cohort's diff contains none. Same reason the plan's pre-flight step 2 recorded.
- Focused `pytest`: **not run**, none owed; no `--cov*` flag was used anywhere in this pass. `check_spec_glossary.py` and `check_trailing_commas.py --check` were re-run read-only.
- Failability proofs: **none owed, none recorded**. The diff introduces no boundary, guard, gate or rejection path. Worker 3's mandatory re-run floor is therefore an empty set, which `worker-3.md` permits only in exactly this case. My source carve-out was **not exercised**: no production file was mutated at any point.
- Hot-path budget: not applicable; plan declares none. Floor verification: not applicable; plan declares scope none.

### Notes for Worker 1 (spec reconciliation)

**The seven carried deferrals, each re-derived rather than endorsed:**

1. **`CHANGELOG.md`'s `[0.0.7]` entry understates the dispatch. CONFIRMED, endorse as written.** `CHANGELOG.md:169` reads "The `ready()` body imports `django_strawberry_framework._django_patches` and calls `apply()`" — one applier where three ship. The same entry labels the card `017-appspy_and_django_app_config-0.0.7`, pre-renumber (1 occurrence in that file, not the 14 a neighbouring `KANBAN.md` note reports for a different population). The item's own instruction — "do not state either population from a one-line description, re-derive both" — is correct and I echo it. **Deferred catalog.**
2. **Sibling `[spec-016]` / `[spec-017]` ref-id residue = 15 definition lines. CONFIRMED exactly, endorse.** `spec-022` 7, `spec-023` 3, `spec-025` 2, `spec-027` 2, `KANBAN.md` 1; raw token grep 104. One correction to the *instrument's description*, not the number — see Low 2. **Deferred catalog, stated as definition lines.**
3. **`spec-022` asserts the retired claim. CONFIRMED and it is the highest-value sibling item — but CORRECT THE POPULATION to three sites**, `:98`, `:130`, `:478`, with `:130` (`## Non-goals`, "the `ready()`-body deferral, which is preserved here") the one currently unrecorded and the second genuinely false assertion. `:478` mirrors a posture that survives the inversion and should be graded as such. The dead-anchor half is confirmed: `#decision-4--no-readyhook-in-0_0_7` never resolved (the real `HEAD` slug was `decision-4--no-ready-hook-in-007`), so this pass did not break it. **Deferred catalog.**
4. **`spec-022` / `spec-025` non-shipped `Status:` lines. CONFIRMED, endorse.** `spec-022:4` `Status: draft (revision 5, post-rev4 feedback).`; `spec-025:4` "Only the final test-run gate remains"; `spec-023:4` is already correct, so the caution that each file needs its own look is right. **Deferred catalog.**
5. **`tests/test_apps.py`'s `spec-017` comment. CONFIRMED routed, endorse.** The file is byte-identical to `HEAD`; Worker 0 records it as F8 for R2. Correctly kept out of the catalog to avoid double-counting. Re-verified here so R2's reviewer inherits a confirmed statement.
6. **The `AGENTS.md` paraphrase-citation convention. CONFIRMED as a class; CORRECT THE FIGURES OR DROP THEM.** The classification is sound — I verified all 7 surviving `spec-021` citations are paraphrases, all pre-existing at `HEAD`, and the spellings recur across many sibling specs. The stated `25 / 101 / 22 / zero-resolving` does not reproduce under an independent sweep (23 / 109 / 15, two resolving). See Low 1. **Deferred catalog as a repo-wide decision, with the population re-derived and its corpus rule stated.**
7. **Decision 6's four-card bundle vs `KANBAN.md`'s seven. ENDORSED AGAIN, no action.** Leaving the Decision stating its authoring-time bundle is right: its subject is the version-bump policy, which no later card joining the release affects, and rewriting the bundle would make the Decision assert something it never decided. Recorded so final verification does not re-open it.

**Escalated: none.** Every finding above is correctable inside R1's own two writable files; none turns on spec context unavailable to this cohort, and none is a contract-level question — the one contract-level call pass 1 offered (freeze vs re-derive the out-of-scope pointers) was decided and recorded this pass, and I endorse the re-derive.

**One observation for final verification, not a finding.** Three passes have now each corrected the previous pass's population by one or more members (18 → 19 → 30 → 31 on F1; two → three on `spec-022`; two → eighteen on the discarded definitions). The pattern is not carelessness — every *instrument* in this pass reproduced exactly, to the line. What keeps failing is the sentence that says how much the instruments found, written after the instruments were run. Whoever writes `bld-final.md`'s catalog should treat every count in it as requiring re-derivation at write time, including the ones this review confirmed.

**Routing note.** `Status: revision-needed` on this cohort routes to **Worker 1**, not Worker 2 — the plan declares R1's sequence as Worker 1 → Worker 3 → Worker 1 with no Worker 2, because only Worker 1 may mutate a spec and Worker 2 may never read a rationale file. Isolation is preserved: the revision pass is a build pass, and a fresh Worker 1 invocation still owns final verification.

### Review outcome

`revision-needed`.

The **substantive work is now complete and independently confirmed**. Pass 2 closed the two findings that were about the work rather than the record: the `## Out of scope` renumber residue is fully re-derived by feature with the intra-file contradiction gone and the freeze-vs-re-derive decision recorded, and the seven stale citations are repaired and resolve. The MOVE is still a move (zero cross-file duplication at any threshold down to 0.85), the spec still narrates no history, every anchor and link definition in both files resolves and sorts, F1's fix is complete against a population I re-derived from `HEAD`, and Decision 4 holds clause-by-clause against `apps.py` and `conf.py`.

What still fails is the **record**, in the same shape as pass 1 and in one case in the same paragraph. The byte-accounting paragraph rewritten to close High 1 still carries pass 1's falsified shed figure two lines below the correct one, and the build report's closure evidence — a substitution mechanism that "could not move the number it reports" — is falsified by the file it describes (High 1). The F1 population derivation, which is the pass's best structural idea, understates what neither grep found by a factor of more than two, so running it as written recovers 25 of 30 rows (Medium 1), and the table still omits a site it fixed under a sentence claiming it carries every member (Medium 2) — pass 1's Medium 2 recurring past the re-derivation meant to end it. The headline citation figure is attributed to a corpus that is not `HEAD` and no longer exists anywhere (Medium 3), and the `spec-022` catalog entry is one site short in the direction that matters (Medium 4).

Every one is a one-line-to-one-paragraph edit inside `docs/SPECS/spec-021-apps-0_0_7.md` and `docs/SPECS/appx/spec-021-apps-0_0_7-rationale.md`. None requires re-doing the move, the reconciliation, or any sweep — four of the six are corrections to sentences whose underlying measurements this review already reproduced and recorded above.

---

## Build report (Worker 1, pass 3 — apply-changes)

Closes Worker 3's pass-2 High x1 / Medium x4 / Low x3. Every finding was a **sentence describing a measurement**, not a measurement: the instruments underneath all reproduced. So each is closed by re-deriving the figure, naming the corpus and the command beside it, and enumerating populations instead of counting them. No prior artifact entry was edited; the two header reference lines carry this pass's `wc -c` readings.

### Files touched

- `docs/SPECS/appx/spec-021-apps-0_0_7-rationale.md` — the byte-accounting block re-stated against two obtainable corpora with the commands inline and the stale twin figure removed (High 1); the Decision 4 population derivation rewritten as a row-by-row instrument mapping with the six unreached rows named (Medium 1); the F1 table given its missing `## Goals` item 1 row and renumbered to 31, with the dependent counts corrected and the completeness sentence replaced by a statement of what produced the rows (Medium 2); the citation sweep re-attributed to `51eb47ba` and to the current file, the intermediate-corpus figures dropped (Medium 3); the `## Left open by this pass` `spec-022` bullet re-derived to four passages graded three-false-one-true, plus the live-tree state (Medium 4); the `AGENTS.md` class re-stated with its corpus rule (Low 1); the `## Renumber residue` self-consistent-definition count corrected and enumerated (Low 2); the `## Implementation plan` entry and F1 row 17 re-stated on the `wc -l` readings (Low 3); `## Goals`/`## Non-goals` entry given Goal 1's change; `## Claims the spec may no longer make` row 1 given `Goals 1`.
- `docs/SPECS/spec-021-apps-0_0_7.md` — two `## Implementation plan` cells: `+45 / -0` -> `+43 / -0`, `+185 / -0` -> `+184 / -0` (Low 3). Both substitutions are width-neutral, so the spec is byte-identical in size to pass 2's; `wc -c` is 64,941 before and after.
- `docs/builder/bld-review-1-rationale_and_spec_reconciliation.md` — this entry, the two header byte figures, `Status:`.
- `docs/builder/worker-memory/worker-1.md` — memory entry appended.

### Tests added or updated

None; this cohort writes no tests.

### Validation run

- `uv run ruff format .` / `uv run ruff check --fix .` — **not applicable**; no `.py` file was touched.
- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-021-apps-0_0_7.md` -> `OK: 12 terms - all have glossary entries and at least one spec link.`, **exit 0**.
- Markdown scaffold check on this cohort's own two files: `uv run python scripts/check_trailing_commas.py --check docs/SPECS/spec-021-apps-0_0_7.md docs/SPECS/appx/spec-021-apps-0_0_7-rationale.md` -> **exit 0**.
- **Byte figures, measured after the last content edit and then substituted at equal width so the substitution could not move them, and re-measured after the substitution.** `wc -c` -> spec **64,941**, rationale **80,741** (identical reading before and after the substitution). `git show 51eb47ba:docs/SPECS/spec-021-apps-0_0_7.md | wc -c` -> **97,518**. Shed `97518-64941` = **32,577**; surplus `80741-32577` = **48,164**. Both figures the rationale states appear in the file exactly where measured; `grep -c '32,650'` -> **0**, and a sweep of every 4+-digit and comma-grouped numeral in the rationale (`grep -noE '[0-9]{1,3},[0-9]{3}|[0-9]{4,}'`) returns only these five byte figures, the four commit hashes, the `sed` range `34,513`, the Trac id `37064` and calendar years.
- **F1 population, re-derived from the read-only `51eb47ba` copy before reading the table.** Instrument (a) -> **37** lines, identical to the recorded list. Instrument (b) -> the same **9** lines. Mapping the 37 onto the table: 32 lines land on **23** rows, the other 5 are the four declared non-sites (lines 40, 41, 115, 118) and the moved Risks item (line 435). (b) adds exactly **two** rows (lines 356, 372); its lines 10, 13, 19 are inside the moved `Revision history` block. **Six rows are reached by neither** — 6, 10, 13, 14, 21, 31 — so 23 + 2 + 6 = **31**. Worker 3's "instrument (a) misses seven rows, the union misses five" is confirmed against the 30-row table; against the 31-row table it is eight and six, the new member being `## Goals` item 1.
- **`## Goals` item 1 confirmed an F1 site.** At `51eb47ba` line 105 it closes `… exempt from the negative-shape iteration accordingly (rev4 L2). Nothing else.`; the current spec's Goal 1 ends at `… accordingly.` The row is now in the table and in the `## Claims the spec may no longer make` index.
- **Citation sweep, three syntactic forms, own resolver, run on both corpora.** `51eb47ba`: **68** occurrences (`grep -o '#"' | wc -l` -> 68; 53 outside the `Revision history` block), **23 resolve, 45 do not**. Current spec: **36**, **29 resolve, 7 do not**, all 7 the `AGENTS.md` class. Worker 3's Medium 3 reproduces exactly. `37 / 23 / 14` described pass 1's intermediate output file, which no reader can obtain, and is therefore gone from the rationale rather than re-labelled.
- **`AGENTS.md` citation class, corpus rule stated with the figure.** Corpus: every `.md` under `docs/SPECS/` including `appx/` (84 files); every `#"…"` whose target — bare path, or ref-id resolved through that file's own definition block — is `AGENTS.md`. Result: **111 occurrences in 27 files, 16 distinct substrings, 3 of which occur verbatim in `AGENTS.md`** (7 of the 111). Neither pass 2's `25 / 101 / 22 / zero-resolving` nor Worker 3's `23 / 109 / 15 / two-resolving` reproduces under this rule; the rule is now in the sentence so the next reader can disagree with it precisely. Re-measured after the edits that state it (the figure is inside its own corpus): unchanged at 111 / 27 / 16 / 3.
- **`spec-01[67]` definition population.** `git grep -E '^\[spec-01[67][a-z0-9-]*\]:' 51eb47ba -- docs/SPECS KANBAN.md` -> **32** definitions, **16 disagree**, **16 agree**. One disagreeing definition is this spec's own, repaired by this round, so the sibling residue is **15** (7/3/2/2/1), which reproduces file-for-file. The self-consistent count is **16**, not the "two" pass 2 wrote and not the "eighteen" Worker 3 wrote — Worker 3's own enumeration (9 + 2 + 3 named files + the 2 it called out) sums to 16.
- **In-page anchor sweep, both files, re-run after the last edit**, slugging rendered heading text (reference-style headings slug to their label; a code-span heading beginning `##` keeps a leading hyphen). Spec: 31 headings, 15 distinct anchors used, all resolve except `(#django-appconfig)`, which is inside a `docs/GLOSSARY.md` citation and is not a link (re-read to confirm). Rationale: 27 headings, 6 distinct anchors, all resolve.
- **Cross-file anchors, rationale -> spec:** all 8 `[spec-021-dN]` definitions re-derived against the spec's current heading slugs — all resolve.
- **Reference-link integrity:** no undefined use, no unused definition, every non-URL definition path exists on disk from its own file's directory, all ten canonical group headers present and ordered in both files, every group alphabetical. (The two apparent undefined refs in the rationale, `0-9` and `a-z0-9-`, remain character classes inside code spans.)
- `AGENTS.md` rule 27: `grep -nE '[A-Za-z0-9_/.-]+\.(py|md|toml):[0-9]+'` over both files -> **zero**. The `spec-022` line references pass 2 carried as `:98` / `:130` / `:478` are gone, replaced by section names. Rule 4: neither file names the forbidden files.
- **No history narration in the spec:** `grep -noiE 'rev[0-9]|revision|superseded|formerly|previously|originally|corrected|no longer|used to|Alternatives considered|Revision history|Risks and open questions'` -> **two hits, both on line 8**, the required rationale-pointer paragraph. Unchanged from pass 2.
- `git status --short` after the edits: **24 paths**. This cohort's three are `M docs/SPECS/spec-021-apps-0_0_7.md`, `?? docs/SPECS/appx/spec-021-apps-0_0_7-rationale.md` and `?? docs/builder/bld-review-1-rationale_and_spec_reconciliation.md`; all three are in the writable list and in `### Files touched`. `docs/builder/worker-memory/` is gitignored. The other 21 are concurrent-session work — the three declared baseline-dirty paths, Worker 0's two plans, 7 package modules and 5 test modules under a concurrent refactor, `docs/SPECS/spec-051-…`, one further `docs/` path, and **`docs/SPECS/spec-022-export_schema-0_0_7.md` plus its new `appx/` rationale and `bld-`/`build-` artifacts, which are a concurrent session running `spec-022`'s own rationale-extraction round**. None edited, none reverted (`AGENTS.md` rule 34). Nothing unexpected.
- No `pytest` was run, with or without any `--cov*` flag.

### Failability proofs

None; this pass introduced no new boundary.

### Hot-path budget

Not applicable; plan declares no hot path.

### Floor verification

Not applicable; plan declares floor-verification scope none.

### Implementation notes

- **The High finding was closed by removing the second figure's reason to exist, not by editing it to match.** The paragraph now states the shed once as an arithmetic expression (`97518 - 64941`) and refers back to "the shed" the second time; the byte-accounting block names both corpora and the exact commands that produce them. A reader who wants the number computes it; a later editor who changes a file cannot leave a twin behind, because there is no second literal.
- **A derivation that says how much it missed teaches nothing; one that says what it missed can be run.** The population paragraph now publishes instrument (a)'s 37 line numbers, maps them onto rows arithmetically (32 -> 23 rows, 4 non-sites, 1 moved item), states that (b) contributes exactly two rows and that three of its nine lines are not sites at all, and then **names the six rows no instrument reaches, with their sections and line numbers**. Running it as written now lands on all 31.
- **`## Goals` item 1 was a site because of one absolute, not one token.** "Nothing else." closes an enumeration of the class body; the `ready()` override falsifies the closure while leaving all four enumerated members true. No `ready` token, no count — which is exactly why both instruments missed it and why the row's `Was` column quotes the absolute rather than the sentence.
- **The `37` citation figure was deleted, not re-labelled.** Its corpus was pass 1's output file, which exists nowhere a reader can reach. The rationale now gives `51eb47ba` (68 / 23 / 45) and the current file (36 / 29 / 7) and states the direction between them — failures fell 45 -> 7 while resolutions rose 23 -> 29. The per-occurrence churn is larger than the net figures suggest (9 resolving occurrences left with the move, 15 arrived with the repairs and retargets), so no tidy "only broken citations were removed" arithmetic is asserted.
- **The `AGENTS.md` class was failing its own definition.** Defined as "the paraphrase citations", "not one resolves" is true by construction; defined as "citations targeting `AGENTS.md`", it is false — three distinct substrings resolve, one of them the ruff-gate spelling pass 2 introduced as a repair. The corpus rule is now the first thing in the sentence and the digits follow it.
- **`spec-022` is a moving target, and the record says which state each figure describes.** At `51eb47ba` the file carries four `ready()` passages: three assert the retired claim (`## Problem statement` predecessor paragraph, `## Non-goals` command-hook bullet — "which is preserved here" — and the `## Edge cases and constraints` command-discovery bullet, "it has no `ready()` body and does not need one"), and Decision 3's `finalize_django_types` anti-pattern paragraph cites Decision 4 for a rule the inversion leaves intact. Worker 3's third site is the `## Edge cases` one; its `:478` line number is from the working tree, not `51eb47ba`. In the working tree at the end of this pass the file carries **zero** `ready()` occurrences and zero `spec-01[67]` tokens — a concurrent session's `spec-022` round removed them. Recorded, not actioned.
- **Nothing in the spec narrates its own history.** The only spec edit this pass makes is two numeric cells; the chronology of why they changed is in the rationale's `## Implementation plan` entry, keyed to that section.

### Notes for Worker 3

- Three figures in this pass contradict figures in the immediately preceding entries, and all three are worth re-deriving independently: the F1 population is **31** (pass 2 wrote 30, and its own review found the omitted member); the `AGENTS.md` class is **111 / 27 / 16 / 3-resolving** under the corpus rule now stated in the file (pass 2 wrote 25 / 101 / 22 / zero, Worker 3 measured 23 / 109 / 15 / two, and no two of these agree — the rule, not the arithmetic, is what to audit); the self-consistent `spec-01[67]` definitions are **16** (pass 2 wrote two, Worker 3 wrote eighteen while enumerating sixteen).
- The rationale's byte figures are self-referential and were engineered to converge: measured, then substituted at equal width, then re-measured to the same reading. `wc -c` -> 64,941 / 80,741 is the check, and `grep -c '32,650'` -> 0.
- `spec-022` moved under this cycle mid-pass. Any re-derivation of the sibling-residue or false-claim populations against the **working tree** will now return zero for that file; against `51eb47ba` it returns 7 definition lines and 3 false assertions. Both states are recorded in the rationale for exactly this reason.
- `(#django-appconfig)` in the spec's anchor sweep remains a false positive — it is inside a `docs/GLOSSARY.md` citation, not a link.
- Nothing under `django_strawberry_framework/`, `tests/` or `examples/` was touched by this cohort; the concurrent refactor's 12 files there are not this pass's and `docs/builder/temp-tests/r1/` is still empty.

### Notes for Worker 1 (spec reconciliation)

Carried forward for final verification and, where marked, for `bld-final.md`'s `### Deferred work catalog`. **Every population below is re-derived at this pass's write time and pinned to a named corpus; two of them moved between pass 2 and now.**

1. **`CHANGELOG.md`'s `[0.0.7]` `### Added` entry understates the dispatch — one applier where three ship.** Accurate when `300e2811` landed, falsified by `c7cb5f5c`. The same section labels this card `017-appspy_and_django_app_config-0.0.7`, pre-renumber. `AGENTS.md` forbids `CHANGELOG.md` edits without instruction and this cycle grants none. **Deferred catalog**; re-derive both populations rather than restating them from this line.
2. **`[spec-016]` / `[spec-017]` ref-id residue. Re-derived: at `51eb47ba`, 32 definitions match `^\[spec-01[67][a-z0-9-]*\]:` across `docs/SPECS` + `KANBAN.md`; 16 disagree with their target and 16 agree. One disagreeing definition was this spec's own — repaired here — leaving 15 in siblings (7 `spec-022`, 3 `spec-023`, 2 `spec-025`, 2 `spec-027`, 1 `KANBAN.md`).** In the working tree the same command now returns 24 definitions and 8 disagreeing: a concurrent session removed `spec-022`'s 7. **The catalog must re-run the command, not copy either number.**
3. **`spec-022`'s false Decision-4 assertions. Population corrected to three (not two), and the file has since changed.** At `51eb47ba`: `## Problem statement` predecessor paragraph, `## Non-goals` command-hook bullet, `## Edge cases and constraints` command-discovery bullet — three false assertions; Decision 3's `finalize_django_types` paragraph cites Decision 4 for a rule that survives the inversion and is **not** false. Its `[spec-017-decision-4--no-readyhook-in-0-0-7]` definition targets an anchor that never resolved at `51eb47ba`. **In the working tree the file now carries zero `ready()` occurrences** — the concurrent `spec-022` round closed this. **Catalog entry: verify against whatever `spec-022` state lands, and drop the item if that session's work commits.**
4. **Non-shipped `Status:` lines. Re-derived this pass: `spec-025`'s line 4 still reads "Only the final test-run gate remains" on a shipped card. `spec-022`'s no longer does** — its working-tree line 4 reads `Status: shipped in `0.0.7` (2026-05-27) and archived …`. `spec-023`'s was already correct. **Catalog: `spec-025` only, unless `spec-022`'s concurrent work is reverted.**
5. **`tests/test_apps.py` cites `spec-017` for this card in a source comment.** Worker 0 records it as **F8**, dispatched to **R2**. `git status --short tests/` shows the file untouched by this cohort. Recorded so the catalog does not double-count it. **No action here.**
6. **The `AGENTS.md` citation convention. Figures replaced by a corpus rule plus figures.** Under "every `.md` under `docs/SPECS/` including `appx/`; target is `AGENTS.md`; occurrences and distinct substrings counted separately": **111 occurrences, 27 files, 16 distinct substrings, 3 resolving verbatim.** Three independent sweeps in this cycle produced three different sets of digits, which is the finding: **the catalog must state the corpus rule with whatever number it publishes**, and must not repeat "not one resolves". **Deferred catalog as a repo-wide decision.**
7. **Decision 6's four-card bundle vs `KANBAN.md`'s seven `0.0.7` cards.** Left as the authoring-time bundle; Worker 3 endorsed twice. **No action.**

### Dispatched findings checklist

- [x] **High 1 — the byte-accounting paragraph carries pass 1's falsified shed two lines below its fix.** Closed by removing the duplicate literal entirely (the second mention now says "the shed"), re-measuring both files after the last edit, stating both corpora with their commands, and re-measuring after the equal-width substitution. `grep -c '32,650'` -> 0; `wc -c` -> 64,941 / 80,741; shed 32,577; surplus 48,164.
- [x] **Medium 1 — the instrument-blind-spot accounting understates what neither grep found.** Closed by replacing the count with a mapping: (a) reaches 23 of 31 rows, (b) adds 2, and the **six** rows neither reaches are named with their sections and line numbers.
- [x] **Medium 2 — the table omits `## Goals` item 1 under a completeness sentence.** Closed by adding the row (now row 6), renumbering to **31**, correcting the two dependent figures (the `Deleted outright` bullet's "reached 29 further sites" -> 30, and the accounting paragraph's "30-site reconciliation table" -> 31-site), adding `Goals 1` to the claims index, recording the change in the `## Goals` entry, and replacing "carries every member" with a statement of what produced the rows.
- [x] **Medium 3 — `37 / 23 / 14` attributed to a corpus that is not `HEAD` and no longer exists.** Closed by deleting the intermediate figures and stating the two obtainable corpora: `51eb47ba` 68 / 23 / 45, current file 36 / 29 / 7, each with its command.
- [x] **Medium 4 — `## Left open by this pass` names two `spec-022` sites.** Closed by enumerating all four `ready()` passages at `51eb47ba` by section, grading three false and one surviving, mirroring the correction into `### Notes for Worker 1` item 3, and recording that the working-tree file now carries none.
- [x] **Low 1 — the `AGENTS.md` class figures do not reproduce and "not one resolves" is false.** Closed by stating the corpus rule in the sentence and publishing 111 / 27 / 16 / 3-resolving under it, naming the ruff-gate substring this cycle introduced as one that resolves.
- [x] **Low 2 — "the two self-consistent hits" are sixteen.** Closed by publishing the full instrument (32 definitions, 16 disagreeing, 16 agreeing) and enumerating the agreeing files.
- [x] **Low 3 — `+45` / `+185` written over measurements of 43 / 184.** Closed by writing the measurements into the spec's two cells with the `wc -l` command recorded in the rationale, and by saying why Slice 3's `+25 / -8` stays a forecast.

---

## Review (Worker 3, pass 3)

Reviewed: the working-tree state of `docs/SPECS/spec-021-apps-0_0_7.md` and `docs/SPECS/appx/spec-021-apps-0_0_7-rationale.md` against `git show 51eb47ba:…` copies written to a scratch path **outside** the repo, plus `docs/SPECS/spec-022-export_schema-0_0_7.md` (both at `51eb47ba` and live), `KANBAN.md`, `AGENTS.md`, `django_strawberry_framework/__init__.py`, `tests/test_apps.py`, `django_strawberry_framework/apps.py`. `HEAD` is still `51eb47ba`. No `git stash` / `checkout` / `restore` / `worktree` at any point; no `pytest`, with or without `--cov*`.

**Scope of this pass, per the dispatch.** A closure check. Every figure pass 3 states was re-derived with its own command against the corpus it names, before reading pass 3's account of it. Twelve of the thirteen re-derive exactly or are drift-explicable; one sub-figure does not.

### Independent re-derivations

| Claim (pass 3) | My instrument | Result | Verdict |
|---|---|---|---|
| spec 64,941 / rationale 80,741 / `51eb47ba` 97,518 | `wc -c` on both live files and the read-only `51eb47ba` copy | 64,941 / 80,741 / 97,518 | correct |
| shed 32,577 (`97518-64941`); surplus 48,164 (`80741-32577`) | arithmetic on the three readings | 32,577 / 48,164 | correct |
| `grep -c '32,650'` -> 0, no stale twin anywhere | `grep -c` on both files; full numeral sweep `[0-9]{1,3},[0-9]{3}\|[0-9]{4,}` on both | 0 in both; the rationale's numerals are exactly the five byte figures, four commit-hash digit runs (`2811` x6 from `300e2811`, `7014125`, `5476`, plus `c7cb5f5c` which carries none), `34,513`, `37064`, and years `2026`/`2021`. The spec carries `2026` and `37064` only | correct |
| spec cells `+43 / -0`, `+184 / -0`; width-neutral | read both cells; `wc -l django_strawberry_framework/apps.py tests/test_apps.py`; `wc -c` on the spec | cells read `+43 / -0` and `+184 / -0`; files are 43 and 184 lines; spec is 64,941 bytes as before | correct |
| F1 table is 31 rows with `## Goals` item 1 as row 6 | counted the numbered rows; read row 6; re-read `51eb47ba` line 105 | rows 1-31 contiguous, 31 total; row 6 is `## Goals` item 1 quoting the dropped `Nothing else.`; the live spec's Goal 1 ends at "…accordingly." | correct |
| dependent figures corrected | `grep` for `31-site`, `30 further`, `carries every member` | "the 31-site reconciliation table"; "it reached 30 further sites"; `carries every member` count 0; `Goals 1` present in the claims index row 1 | correct |
| instrument (a) -> 37 lines / 52 pre-strip / 63 whole-file | the exact recorded pipeline on the `51eb47ba` copy | 37 / 52 / 63, and the 37 line numbers are the published list **character-for-character** | correct, exactly |
| instrument (b) -> 9 lines | the exact recorded grep | 10, 13, 19, 66, 106, 356, 372, 391, 457 | correct, exactly |
| (a)'s 37 lines land on **23** rows (32 lines), (b) adds **2**, **6** rows reached by neither | mapped all 37 `51eb47ba` line numbers to sections and thence to rows, independently | 32 lines -> 23 rows (row 15 absorbs lines 272-289 = ten), + 4 non-sites (40, 41, 115, 118) + 1 moved Risks item (435) = 37. (b) adds rows 17 and 22. Unreached: **6, 10, 13, 14, 21, 31** — the exact six named, with the exact sections and lines. 23+2+6 = 31 | correct, exactly |
| citations: `51eb47ba` 68 / 23 / 45; current 36 / 29 / 7 | own three-form extractor + resolver (bare path, backticked, reference-style through each file's own definition block), paths resolved from `docs/SPECS/` | **68 / 23 / 45** and **36 / 29 / 7**; all 7 survivors are the `AGENTS.md` class | correct, exactly |
| `37 / 23 / 14` deleted rather than re-labelled | `grep` for `37 citation`, `37 / 23`, `23 / 14` in both files | zero hits | correct |
| `spec-022` has four `ready()` passages at `51eb47ba`, three false one true | `grep -n 'ready()'` on the `51eb47ba` copy | lines 98 (`## Problem statement` predecessor), 130 (`## Non-goals` command hook, "which is preserved here"), 390 (Decision 3 `finalize_django_types` anti-pattern — **true**), 577 (`## Edge cases and constraints`, "it has no `ready()` body and does not need one"). Four; three false | correct, exactly |
| working-tree `spec-022` carries zero `ready()` | `grep -c` on the live file | 0 | correct (concurrent-session drift, as recorded) |
| self-consistent `spec-01[67]` definitions = 16 | `git grep -E '^\[spec-01[67][a-z0-9-]*\]:' 51eb47ba -- docs/SPECS KANBAN.md`, ref-id number vs target basename | **32 total, 16 disagree, 16 agree**. Disagreeing: `spec-022` 7, `spec-023` 3, `spec-025` 2, `spec-027` 2, `KANBAN.md` 1, `spec-021` 1 (this spec's own, repaired) -> sibling residue **15**. Agreeing: 9 + 2 + one each in `appx/spec-004-…-rationale`, `spec-016-fieldmeta…`, `spec-017-deferred_scalars…`, `spec-018`, `spec-037` = 16, matching the rationale's enumeration file-for-file | correct, exactly |
| live tree now 24 definitions, 8 disagreeing | same instrument on the working tree | 24 / 8 (`spec-023` 3, `spec-025` 2, `spec-027` 2, `KANBAN.md` 1) | correct |
| `AGENTS.md` class: 111 occ / 27 files / 16 distinct / 3 resolving (7 of 111) | own sweep under the corpus rule **as the rationale states it** (every `.md` under `docs/SPECS/` incl. `appx/`; target from preceding bare path or ref-id resolved through that file's own definition block; occurrences and distinct counted separately; "resolves" = substring occurs verbatim in `AGENTS.md`) | corpus **84 files** (matches). **16 distinct** (matches exactly, once line-wrapped citations are folded — an unstated but unavoidable element of the rule). Occurrences **119** in **28** files. Resolving: **2 distinct, 4 occurrences** | **16 reproduces; 119/28 is drift-explicable; 3-resolving/7 does not reproduce** — Medium 1 |
| no history narration in the spec | `grep -noiE 'rev[0-9]\|revision\|superseded\|formerly\|previously\|originally\|corrected\|no longer\|used to\|Alternatives considered\|Revision history\|Risks and open questions'` | **two hits, both line 8** — the required rationale-pointer paragraph | correct |
| `check_spec_glossary` / scaffold check | re-ran both | `OK: 12 terms`, exit 0; scaffold exit 0 | correct |

**On the `AGENTS.md` occurrence figure and drift.** The two headline digits are the only ones in this cycle whose corpus is being rewritten under it. At `51eb47ba` the same instrument returns 125 occurrences / 26 files / 15 distinct / 1 resolving; live it returns 119 / 28 / 16 / 2. The per-file delta between those two states is confined to four files, two of them the concurrent `spec-022` pair (`spec-022` itself 19 -> 13, its new `appx/` rationale 0 -> 1) and two of them this cohort's own. `119 - 1 (appx/spec-022) - 7 (a further spec-022 swing)` is `111` in `27` files, so pass 3's headline pair is consistent with the file's state at its write time and with the drift pass 3 itself declared. The **distinct** count is stable at 16 across the whole window, which is why it reproduces. The resolving sub-count is not drift-sensitive at all, and is where the figure is wrong.

### Dispatched findings checklist walk (pass 3's own eight boxes)

- **High 1 — `- [x]` stands on substance.** `32,650` is gone from both files and from the repo's `.md` surface; both files' byte figures re-measure exactly; the arithmetic relations all close. The box's *description* of the mechanism is wrong (Low 1) but the defect it names is closed.
- **Medium 1 — `- [x]` stands.** The mapping is published, and it re-derives to the line: 23 rows from (a), 2 from (b), six named rows from neither. Running the paragraph as written now lands on all 31.
- **Medium 2 — `- [x]` stands.** Row 6 added, table renumbered to 31, both dependent figures corrected, `Goals 1` added to the claims index, the `## Goals` entry records the change, and the completeness sentence is replaced by a statement of what produced the rows plus an explicit disclaimer that it is not closed against unperformed readings.
- **Medium 3 — `- [x]` stands.** The intermediate corpus is deleted, not re-labelled; both obtainable corpora are stated with their commands and both reproduce exactly.
- **Medium 4 — `- [x]` stands.** All four `51eb47ba` passages are named by section and graded, and the live-tree zero state is recorded beside them. The `### Implementation notes` aside about *where pass 2's third site was* is wrong (Low 2); the rationale itself is right.
- **Low 1 — `- [x]` stands for the corpus rule, not for one of its four digits.** See Medium 1 below.
- **Low 2 — `- [x]` stands.** 32 / 16 / 16 with the agreeing files enumerated, all reproducing file-for-file.
- **Low 3 — `- [x]` stands.** Both cells carry the `wc -l` measurements, the substitutions are width-neutral (the spec is still 64,941 bytes), and Slice 3's `+25 / -8` is left as a forecast with its reason stated.

The plan's own `### Dispatched findings checklist` (F1, F2, F3, F4, F7) remains all `- [x]` and every tick still holds; nothing in pass 3 disturbed them.

### High:

None.

### Medium:

#### The `AGENTS.md` class publishes a resolving sub-count of 3 substrings / 7 occurrences; the rule it states returns 2 / 4

`docs/SPECS/appx/spec-021-apps-0_0_7-rationale.md` `## Provenance of this record`, the paraphrase-citation bullet:

> Under that rule the class is **111 occurrences in 27 files, spanning 16 distinct substrings, of which 3 occur verbatim in `AGENTS.md` (7 of the 111 occurrences) and 13 do not**

Running the stated rule, the 16 distinct substrings are recovered exactly. Exactly **two** of them occur verbatim in `AGENTS.md`:

```
`uv run ruff format .` and `uv run ruff check --fix .` after every edit   (3 occurrences)
Test through real usage                                                  (1 occurrence)
```

so the correct tail is **2 distinct / 4 occurrences resolving, 14 not**. I checked every one of the other fourteen against `AGENTS.md` both verbatim and whitespace-normalised, and against the near-miss each paraphrases (`Do not run pytest after edits` vs "No pytest after edits"; `DRF first, strawberry second` vs "DRF first strawberry second"; `always recommend the root-cause fix over the surface patch` vs "Always give the root-cause fix even when slower"; `package tests live under` vs "`tests/` = package tests"). None resolves under any reading, and no candidate contributes the three occurrences that would make 4 into 7. Unlike the occurrence and file counts, this sub-figure is **not** drift-sensitive: `AGENTS.md` is clean in the working tree, and the resolving set is a property of the 16 distinct substrings, which is the one digit in the sentence that is stable across the whole `51eb47ba`-to-now window.

Why it is Medium and not High. The clause it sits in is doing real work — it exists to retire pass 2's "not one of the 22 resolves", and that retirement survives: at least two do resolve, one of them the ruff-gate spelling this round introduced, which is the specific point the sentence makes. The class is explicitly out of this cohort's scope and is already routed to the deferred catalog with an instruction to re-derive. But the digits are in a standing doc and one of them is false as written, which is this cycle's dominant defect class in its fourth consecutive appearance.

**Recommended change.** Either publish `2 distinct (4 of the occurrences) and 14 not`, or — the option pass 2 already offered and pass 3 did not take — drop the four digits from the sentence, keep the corpus rule, and say the class spans most archived specs, is repo-wide, and that at least the ruff-gate substring resolves. The second is more robust: three of the four digits are measured against a corpus a concurrent session is actively rewriting, so any number published here rots on someone else's commit.

**Test expectation:** none (no behavior). Verification is the sweep under the stated rule.

### Low:

#### The build report says High 1 was closed by removing the duplicate literal; the literal is still there, deliberately, and the rationale says so

`### Implementation notes`: "*The paragraph now states the shed once as an arithmetic expression (`97518 - 64941`) and refers back to 'the shed' the second time … a later editor who changes a file cannot leave a twin behind, because there is no second literal.*" The checklist box repeats it: "*Closed by removing the duplicate literal entirely (the second mention now says 'the shed')*".

The rationale's `## Provenance of this record` reads, two lines below the first statement: "*some of the 32,577 bytes went nowhere*" — a second literal — and closes the same paragraph with "*the shed appears twice in this section by design … a corrected figure whose twin two lines away is left alone is worse than either*". The file is self-consistent and both literals are correct; the build report's account of it is not, and it is the same shape as the closure evidence pass 2 falsified ("*equal-width substitution could not move the number*"). Because the standing doc is right and only the per-cycle artifact's description is wrong, this does not rise past Low — but the artifact is what the final gate reads, and a mechanism claimed in it should be checked against the file before it is written.

**Recommended change.** In `bld-final.md`, describe the closure as it is: the twin figure was corrected, both occurrences now read `32,577`, and the paragraph states why it appears twice.

#### The `spec-022` aside misidentifies which site pass 2 added and calls a real `51eb47ba` line a working-tree line

`### Implementation notes`: "*Worker 3's third site is the `## Edge cases` one; its `:478` line number is from the working tree, not `51eb47ba`.*" Both halves are wrong. Pass 2's third — the one it added — was `:130`, the `## Non-goals` command-hook bullet, which it quoted in full; `:98` and `:478` were the two already in the rationale's bullet. And `51eb47ba:478` is a genuine line of that commit: "*Mirrors … Decision 4 and Decision 5's posture: do the minimum the parity story needs*", exactly the "`## Borrowing posture` mirror" pass 2 described and graded as the weakest of its three, precisely because it survives the inversion. It carries no `ready()` token, which is why it is outside the four-passage population — a different fact from the one asserted.

Nothing downstream is wrong: the rationale's four-passage enumeration is correct and pass 3's grading (three false, one true) is right, and it is a **better** population than pass 2's, because `577` asserts the retired claim outright and `478` does not. Only the sentence explaining the divergence is wrong.

**Recommended change.** In `bld-final.md`, state it as measured: pass 2's population was `{98, 130, 478}` and pass 3's is `{98, 130, 577}` false plus `390` true; `478` is a real `51eb47ba` line that mirrors a posture rather than asserting the claim, and `577` — the one no prior pass named — is the third false assertion.

### DRY findings

- **The MOVE is still a move, re-proved independently after pass 3's edits.** Fenced blocks stripped, sentences longer than 90 characters compared pairwise across the two files (268 in the spec, 320 in the rationale): **zero exact duplicates and zero pairs at or above 0.85 similarity**. Pass 3 rewrote the byte-accounting block, the population derivation, the citation sweep, the `AGENTS.md` bullet, `## Renumber residue` and `## Left open`, and reintroduced no cross-file duplicate in either direction.
- **The spec still narrates no history.** Two hits on the whole-file history sweep, both on line 8, both the required rationale-pointer paragraph. The two cells pass 3 edited state the measurement flat and put the chronology in the rationale's `## Implementation plan` entry, keyed to that section.
- **The three-way `[spec-016]` / `[spec-017]` statement pass 2 flagged has stopped diverging.** It is still stated in `## Renumber residue`, `## Left open by this pass` and `### Notes for Worker 1`, but the `## Left open` copy now defers to `## Renumber residue` for the instrument instead of restating it, and all three carry the same population. An index-vs-body relationship with one owner is the right shape; no consolidation finding.
- **Existence challenge: none raised.** This cohort creates no abstraction, helper, registry or indirection.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` returns **zero lines**; `__all__` and the re-export list are unchanged. `git diff HEAD -- tests/test_apps.py` returns **zero lines** — the file is byte-identical to `51eb47ba`, so **F8 is untouched by R1 and remains R2's**. No path under `django_strawberry_framework/`, `tests/` or `examples/` in the working tree is attributable to this cohort; the twelve dirty files there are the concurrent refactor's.

### CHANGELOG sanity

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

Applicable — the diff is an archived spec plus its new companion. Every bullet of `docs/builder/ARTIFACT.md` `### Documentation / release sanity`:

- **Version strings, shipped statuses, card IDs.** `Status: shipped (`0.0.7`, 2026-05-27); archived. Card `DONE-021-0.0.7`.` matches `KANBAN.md`'s `0.0.7` release line. Every card id in the spec re-checked against `KANBAN.md` by feature: `DONE-020`, `DONE-021`, `DONE-022`, `DONE-023`, `DONE-024`, `DONE-025` (all `0.0.7`), `DONE-041` Channels router, `DONE-042` debug toolbar (x2), `DONE-043` test client, `DONE-044` response-extensions (all `0.0.14`). **Zero `TODO-ALPHA` / `WIP-ALPHA` tokens and zero `0.0.12` strings.** The spec's test-surface figures (8 tests, three-key forbidden set) match `tests/test_apps.py` at `grep -c '^def test_'` -> 8.
- **KANBAN card movement.** Not applicable; this cohort moves no card.
- **Links point at existing files.** Both files: `<!-- LINK DEFINITIONS -->` present, all ten canonical group headers present in the exact required order, **every group alphabetical**, zero undefined refs, zero unused definitions, every non-URL definition path resolving on disk from its own file's directory (the spec's `[pkg-dir]` targets a directory, which exists). The rationale's apparent `0-9` / `a-z0-9-` refs remain character classes inside code spans.
- **Anchors.** Spec: 15 distinct in-page anchors, 14 resolve, the 15th (`#django-appconfig`) re-read and re-confirmed as text inside a `docs/GLOSSARY.md` citation rather than a link. Rationale: 6 distinct anchors, all resolve, including `#-renumber-residue` (code-span heading, leading hyphen preserved). All 8 `[spec-021-dN]` cross-file definitions resolve against slugs re-derived from the spec's current headings.
- **Archival preserves the record; live follow-up state stays in durable docs.** Satisfied. Every cut passage is in the rationale or in its `Deleted outright` list with a reason; the R2 obligations are named in the spec's `## Doc updates` and the deferrals are routed to the catalog.
- **Verbatim-copy check.** Nothing is copied from the spec into another file by this diff. R2 inherits that obligation.
- **No obsolete "planned" / "coming soon" / old-version wording.** The surviving `planned for 0.0.7` occurrences are quotations of the `docs/GLOSSARY.md` status value Slice 3 flips. No future-tense obsolescence in `## Out of scope`.
- **Script-rendered docs.** Not applicable; this cohort regenerates nothing. The `docs/TREE.md` citations remain retargeted to section headings, which is the regenerate-stable form.
- `AGENTS.md` rule 27: `grep -nE '[A-Za-z0-9_/.-]+\.(py|md|toml):[0-9]+'` over both files -> **zero**; the `spec-022` line references pass 2 carried are gone, replaced by section names. Rule 4: neither file names the forbidden files.

### What looks solid

- **The population derivation is now a runnable instrument, and it runs.** I mapped all 37 of instrument (a)'s lines onto sections and rows without reading pass 3's mapping first, and landed on the same 23 rows, the same four declared non-sites, the same moved Risks item, the same two rows from (b) and the same six rows from neither — with the same sections and the same line numbers. Publishing *what* was missed instead of *how many* is what makes that possible, and it is the single best structural change in the three passes.
- **The `## Goals` item 1 row is correctly reasoned, not just added.** The site is an absolute ("Nothing else.") over an enumeration whose four members all remain true; no token and no count reaches it, which is exactly why the row's `Was` column quotes the absolute rather than the sentence. The live spec's Goal 1 ends where the row says it does.
- **The citation record now names two corpora a reader can actually obtain, and both reproduce to the occurrence.** Deleting `37 / 23 / 14` rather than re-labelling it was the right call — its corpus was unobtainable — and refusing to assert the tidy "only broken citations left" arithmetic, when the per-occurrence churn does not support it, is the kind of restraint this cycle has otherwise lacked.
- **`spec-022`'s population is better than the one it corrects.** `577` ("it has no `ready()` body and does not need one") is the sharpest false assertion in that file and no earlier pass named it; grading `390` as *true* rather than sweeping it in is the same discipline the four declared non-sites showed in pass 2.
- **The `spec-01[67]` instrument is published whole — 32 / 16 / 16 with the agreeing files enumerated — and reproduces file-for-file at `51eb47ba` and in the live tree.** Recording both the pinned and the drifting state, and saying which command produced each, is the correct answer to a corpus moving under a concurrent session, and it is the first figure in this cycle that a later reader can act on without re-litigating it.
- **The drift itself is handled correctly.** `spec-022` and its new `appx/` companion were read, never edited, never reverted; every population touching them is stated at `51eb47ba` **and** in the live tree, with the catalog instructed to re-run rather than copy.
- **Nothing executable moved.** `django_strawberry_framework/__init__.py` and `tests/test_apps.py` are byte-identical to `51eb47ba`; `check_spec_glossary` exits 0 at 12 terms; the scaffold check exits 0; the spec is byte-identical in size to pass 2's because both substitutions were width-neutral.

### Temp test verification

- No temp tests written. `docs/builder/temp-tests/r1/` does not exist and was not created; the directory is gitignored and this cohort changes no executable behavior, so there is nothing for a temp test to pin.
- Verification ran through six throwaway Python scripts held in the session scratchpad **outside the repository** (a three-form citation extractor-and-resolver, a heading-slugger + anchor/link-definition checker, a cross-file sentence-similarity comparator, a `spec-01[67]` definition-vs-target matcher, an `AGENTS.md` citation-class sweeper, and a `51eb47ba`-line-to-table-row mapper), plus read-only `51eb47ba` copies of `spec-021` and `spec-022`, also outside the repository. Nothing was written inside the tree by this review except this artifact section and the memory entry.
- `scripts/review_inspect.py`: **skipped**, recorded reason — `BUILD.md` `### When to run the helper during build` scopes it to `.py` files and this cohort's diff contains none. Same reason the plan's pre-flight step 2 and both prior review passes recorded.
- Focused `pytest`: **not run**, none owed. No `--cov*` flag was used anywhere in this pass. `check_spec_glossary.py` and `check_trailing_commas.py --check` were re-run read-only.
- Failability proofs: **none owed, none recorded**. The diff introduces no boundary, guard, gate or rejection path, so Worker 3's mandatory re-run floor is an empty set — legal in exactly this case. My source carve-out was **not exercised**: no production file was mutated at any point.
- Hot-path budget: not applicable; plan declares none. Floor verification: not applicable; plan declares scope none.

### Notes for Worker 1 (spec reconciliation)

**The seven carried deferrals, each re-derived at this pass's read time rather than endorsed. Drift-sensitivity is marked on every one.**

1. **`CHANGELOG.md`'s `[0.0.7]` `### Added` entry understates the dispatch — one applier where three ship, and labels the card `017-appspy_and_django_app_config-0.0.7`. ENDORSE as written. Not drift-sensitive** (`CHANGELOG.md` is clean). Its own instruction to re-derive both populations rather than restate them from the line stands; `KANBAN.md`'s own note on that section reports 14 occurrences across 7 distinct labels for a *different* population, and the two must not be conflated. **Deferred catalog.**
2. **`[spec-016]` / `[spec-017]` ref-id residue. ENDORSE, and endorse the instruction to re-run rather than copy. HIGHLY DRIFT-SENSITIVE.** Re-derived both states this pass: at `51eb47ba`, 32 definitions / 16 disagreeing / 16 agreeing, sibling residue 15 (7/3/2/2/1); in the live tree, 24 / 8, with `spec-022`'s 7 gone. Both figures reproduce exactly. **The catalog must re-run `git grep -E '^\[spec-01[67][a-z0-9-]*\]:' … -- docs/SPECS KANBAN.md` at write time.**
3. **`spec-022`'s false Decision-4 assertions. ENDORSE the corrected population — three false (`## Problem statement` predecessor, `## Non-goals` command hook, `## Edge cases and constraints` command discovery) plus one true (Decision 3's `finalize_django_types` paragraph). HIGHLY DRIFT-SENSITIVE.** Verified against the `51eb47ba` copy: four `ready()` passages, exactly those. The live file carries zero. The dead-anchor half is confirmed. **Endorse the catalog instruction: verify against whatever `spec-022` state lands, and drop the item if that session's work commits.** One correction for the catalog's own prose, not for the population — see Low 2.
4. **Non-shipped `Status:` lines. ENDORSE as re-derived. DRIFT-SENSITIVE on `spec-022` only.** `spec-025`'s line 4 still reads "Only the final test-run gate remains" on a shipped card; `spec-022`'s line 4 now reads shipped-and-archived under the concurrent session's work; `spec-023`'s was already correct. **Catalog: `spec-025` only, re-checked at write time.**
5. **`tests/test_apps.py`'s `spec-017` comment. ENDORSE routed.** Re-confirmed byte-identical to `51eb47ba`. It is **F8**, dispatched to **R2**; correctly kept out of the catalog to avoid double-counting. **No action here.**
6. **Escalated: the `AGENTS.md` paraphrase-citation class.** The corpus rule is now stated, which was the substance of the ask, and 16 distinct reproduces exactly under it. **Its resolving sub-count is wrong: 2 distinct / 4 occurrences, not 3 / 7 (Medium 1), and that half is not drift-sensitive. The occurrence and file counts (111 / 27) are drift-sensitive and are consistent with the tree at pass 3's write time; my live reading is 119 / 28.** Resolution paths, for Worker 1's final verification to pick between: **(a)** correct the tail in place to `2 … (4 of the occurrences) and 14 do not`, leaving 111 / 27 pinned to pass 3's write time with that stated; **(b)** re-measure all four at final-verification write time and publish them with the timestamp; **(c)** drop the four digits, keep the corpus rule, and say the class spans most archived specs and is repo-wide with at least the ruff-gate substring resolving. I recommend **(c)** — three of the four digits are measured over a corpus a concurrent session is rewriting, so any number published in a standing doc rots on someone else's commit, and the sentence's actual job (retiring "not one resolves") needs no digits. This is escalated rather than held at `revision-needed` because the choice is a spec-authoring call about what an archived rationale should assert about a repo-wide convention, which is Worker 1's, not a build correction. **Deferred catalog as a repo-wide decision either way.**
7. **Decision 6's four-card bundle vs `KANBAN.md`'s seven. ENDORSED a third time, no action.** Leaving the Decision stating its authoring-time bundle is right: its subject is the version-bump policy, which no later card joining the release affects. Recorded so final verification does not re-open it.

**Two corrections to `bld-final.md`'s own prose, not to any population** — Low 1 (describe High 1's closure as a corrected twin, not a removed literal; the rationale keeps both occurrences deliberately and says why) and Low 2 (pass 2's third `spec-022` site was `## Non-goals`, and `51eb47ba:478` is a real line of that commit).

**On the shape of the remainder, for the final gate.** Pass 2 recorded that every *instrument* reproduced while the sentences describing them failed. Pass 3 is the first pass where that stopped being true in bulk: thirteen figures, twelve exact or drift-explicable, one sub-figure wrong, and the wrong one sits in the sentence whose population three separate sweeps have now each measured differently. The remaining defect is one clause of one out-of-scope sentence plus two mis-descriptions inside a per-cycle artifact. That is below the threshold that should hold R1 open for a fourth pass, and holding it open would produce a fifth non-reproducing measurement of a corpus that is being rewritten while we count it.

### Review outcome

`review-accepted`, with Medium 1 escalated to Worker 1 under item 6 above.

The substantive work was complete and independently confirmed at pass 2 and is unchanged. Pass 3's job was to close eight findings that were all sentences describing measurements, and it closed them by re-deriving: the falsified `32,650` is gone with no stale twin anywhere; the F1 population derivation is now a runnable instrument that lands on all 31 rows when a stranger runs it; the missing `## Goals` item 1 row is added with both dependent figures corrected; the unobtainable `37 / 23 / 14` corpus is deleted in favour of two corpora that both re-derive to the occurrence; the `spec-022` population is corrected to four passages graded three-false-one-true, with the live-tree drift recorded beside it; the `spec-01[67]` instrument is published whole and reproduces file-for-file in both states; and the two spec cells now carry `wc -l` measurements at unchanged spec width.

What remains is one clause: the `AGENTS.md` class's resolving tail reads `3 … (7 of the 111)` where the rule it states returns `2 … (4)`. It is a false figure in a standing doc, which is why it is Medium rather than Low, and it is escalated rather than blocking because the class is out of this cohort's scope, is already routed to the deferred catalog, sits in a sentence whose other digits are measured over a corpus a concurrent session is actively rewriting, and admits a resolution — dropping the digits and keeping the corpus rule — that is a spec-authoring call for Worker 1's final verification rather than a build correction. The two Lows are mis-descriptions inside this per-cycle artifact and touch no standing doc.

Status: review-accepted.

---

## Final verification (Worker 1)

A fresh Worker 1 invocation with no memory of the three passes above. Everything below was re-derived against the working tree and against `51eb47ba` read-only copies held outside the repository; no prior entry was edited. `HEAD` is still `51eb47ba`. No `git stash` / `checkout` / `restore` / `worktree`, no `--cov*` flag, no commit, no branch.

### Summary

R1 delivered the two obligations the original `0.0.7` cycle never discharged. The rationale MOVE ran: `docs/SPECS/appx/spec-021-apps-0_0_7-rationale.md` now exists and carries the six-revision history, the rejected alternatives per Decision, the moved `Justification:` blocks, the `## Risks and open questions` section, a 31-row F1 reconciliation table with its population derivation, a `## Claims the spec may no longer make` index and a `## Left open by this pass` catalog. The spec reconciliation ran: `Decision 4` is inverted from "no `ready()` hook in `0.0.7`" to the shipped three-applier dispatch, and every site the falsified claim reached is reconciled; the test surface is re-pinned to the eight tests and three forbidden keys that ship; the `draft` status line is replaced by the shipped/archived one; and the renumber residue is gone from the spec's ref-ids, its `## Out of scope` card pointers and its Risks card list.

The spec is 64,813 bytes against 97,518 at `51eb47ba`; the rationale is 80,506. No code was written by this cohort — `django_strawberry_framework/__init__.py` and `tests/test_apps.py` are byte-identical to `51eb47ba` (`git diff HEAD -- <path>` returns zero lines for both), and the plan's finding that nothing was skipped in the shipped code holds.

### Dispatched findings checklist audit

I am not the original ticker. Each `- [x]` was re-tested against the current spec and against source, with an instrument I chose:

- **F1 — tick stands.** Negation sweep over the whole spec (`no ready`, `not …ready()`, `MUST NOT contain`, `omits ready`, `defines no ready`, `adds no ready`, `without …ready`) returns three hits and all three are correct statements about *other* things: two on the `## Current state` `conf.py` bullet (the `setting_changed` receiver is installed at import time, **not** in `ready()`) and one in Decision 4 (the `APPLY_UPSTREAM_PATCHES` gate lives inside each `apply()`, **not** in `ready()`). No surviving assertion, implication or dependency on the retired claim. `"ready"` appears nowhere in a forbidden-key set. Decision 4 was checked clause-by-clause against `django_strawberry_framework/apps.py::DjangoStrawberryFrameworkConfig.ready`: function-local imports, dispatch order `django` -> `strawberry` -> `cross_web`, one module per dependency, the docstring's "each module's docstring is the single source of truth" rule, idempotence and reload-healing — all true of the shipped method.
- **F2 — tick stands.** `tests/test_apps.py` at `HEAD` carries 8 test functions; every one of the eight names appears in the spec, verified by `diff`-ing the sorted set of `^def test_` names against the `test_[a-z0-9_]*` tokens the spec carries (the spec's extra tokens are legitimate references to `test_init.py`, `test_list_field.py`, `test_library_api.py` and the two test directories). The forbidden set in the file is exactly `{"label", "default_auto_field", "default"}` and the spec says three keys everywhere it counts them.
- **F3 — tick stands.** Line 4 reads `Status: shipped (`0.0.7`, 2026-05-27); archived. Card `DONE-021-0.0.7`.`
- **F4 — tick stands.** `grep -o 'spec-016'` over the spec returns **0**; `grep -c 'TODO-ALPHA\|WIP-ALPHA\|0\.0\.12'` returns **0**. The `## Out of scope` card ids re-check against `KANBAN.md` by feature.
- **F7 — tick stands.** The rationale file exists. The deliberative-vocabulary sweep over the spec (`rev[0-9]`, `revision`, `superseded`, `formerly`, `previously`, `originally`, `no longer`, `used to`, `Alternatives considered`, `Revision history`, `Risks and open questions`) returns **two hits, both on line 8** — the required rationale-pointer paragraph. Four `Justification:` occurrences survive, all `## Doc updates` build obligations.

No box is left `- [ ]`, so no deferral reason is owed. The plan's checklist is complete and every tick holds.

### Escalation resolved — the `AGENTS.md` citation class

Worker 3 escalated one Medium: the rationale published `16 distinct, of which 3 occur verbatim (7 of the 111)` where the stated corpus rule returns 2 distinct / 4 occurrences. **I re-derived it before acting rather than taking either figure.**

My sweep, run under the rule exactly as the rationale stated it (every `.md` under `docs/SPECS/` including `appx/`; target taken from the preceding bare path or from the ref-id resolved through that file's own definition block; occurrences and distinct counted separately; "resolves" = the substring occurs verbatim in `AGENTS.md`), over the working tree: **122 occurrences in 28 files, 16 distinct substrings once line-wrapped citations are folded, of which 2 resolve — the ruff-gate spelling this round introduced (3 occurrences) and `Test through real usage` (1) — for 4 resolving occurrences.** I checked each of the other fourteen against `AGENTS.md` verbatim and whitespace-normalised; none resolves. One class member had to be excluded to reach 16: `#"unique substring"` occurs five times across `docs/SPECS/`, but every occurrence is a **meta-mention of `AGENTS.md` rule 27's citation syntax**, not a citation of a rule's text, and it resolves trivially. Worker 3 excluded it too, silently; naming it is what makes the 16 reproducible.

So the resolving tail is confirmed at **2 / 4** and the published `3 / (7 of the 111)` is false. The headline pair is a different matter: three live readings of it exist within one day — pass 3's `111 / 27`, Worker 3's `119 / 28`, mine `122 / 28` — and the divergence is not carelessness. Two of the corpus's files (`spec-022` and its new `appx/` companion) are being rewritten by a concurrent session **while the corpus is counted**, and line-wrapped citations fold differently under different extractors. A fourth digit-set published in a standing doc would rot on someone else's commit.

**Resolution: Worker 3's option (c), which is the spec-authoring call this escalation is asking for.** The rationale's paraphrase-citation bullet now publishes the **corpus rule with no digit**. It says the class turns up in most archived specs with the occurrences concentrated in a handful of `0.0.7` / `0.0.8` files, states explicitly why no digit accompanies the rule (four sweeps, four answers, a corpus under concurrent edit), keeps the load-bearing retraction — "not one of them resolves" is false, at least the ruff-gate substring resolves verbatim — and keeps the definitional argument that the class must be defined by target rather than by failure. The false tail is gone rather than corrected to `2 / 4`, because `2 / 4` is a true reading of a corpus that will not hold still either.

### The two Lows, verified against the commit and corrected here

Both are mis-descriptions inside this artifact touching no standing doc. Neither prior entry was edited; the corrections are these two paragraphs.

**Low 1 — High 1's closure mechanism.** Pass 3's `### Implementation notes` and its High-1 checklist box say the duplicate literal was *removed* ("the second mention now says 'the shed'… there is no second literal"). **Verified false against the file, in the pass's own favour.** The rationale's `## Provenance of this record` carries the shed figure **twice** (`grep -o` returns 2), and closes the paragraph with "*the shed appears twice in this section by design … a corrected figure whose twin two lines away is left alone is worse than either*". The figure is right and the file is self-consistent; only the artifact's account of the mechanism is wrong. Corrected as measured: **High 1 was closed by correcting the twin, not by deleting it — both occurrences carry the shed and the paragraph says why it appears twice.** `bld-final.md` should describe it that way. (The figure both occurrences carry has since changed with this pass's edits; see `### Spec changes made` below.)

**Low 2 — the `spec-022` aside.** Pass 3's `### Implementation notes` says "Worker 3's third site is the `## Edge cases` one; its `:478` line number is from the working tree, not `51eb47ba`". **Both halves verified wrong, and Worker 3's correction is right with one imprecision of its own.** Pass 2's review added `:130` as its third site and quoted it in full; `51eb47ba:130` sits under `## Non-goals` (that heading opens at line 120), the command-hook bullet ending "the `ready()`-body deferral, which is preserved here". And `51eb47ba:478` is a **genuine line of that commit** (the file is 754 lines there): "Mirrors … Decision 4 and Decision 5's posture: do the minimum the parity story needs". Worker 3 called that line the "`## Borrowing posture` mirror"; measured, it sits under `### Decision 6 — No --watch / --indent / --json / settings-backed defaults / alias`, not under `## Borrowing posture`. It carries no `ready()` token, which is why it is outside the four-passage population and why grading it as a surviving posture rather than a false assertion is correct. Nothing downstream is affected: the rationale's four-passage enumeration at `51eb47ba` (`98`, `130`, `390`, `577`) reproduces exactly under `grep -n 'ready()'`, and its three-false-one-true grading holds.

### Spec reconciliation — read end to end as a stranger

I read `docs/SPECS/spec-021-apps-0_0_7.md` from line 1 to line 445 without reference to the artifact's account, then read `django_strawberry_framework/apps.py` and `tests/test_apps.py` at `HEAD` and checked the spec against them.

It states the shipped contract cleanly and completely. The module docstring the Slice 1 checklist quotes is byte-identical to the one in `apps.py`; the class docstring likewise; the two class attributes, the three forbidden keys, the `ready()` dispatch and its ordering, the per-`apply()` gate placement, the function-local imports, idempotence and reload-healing all match source. The `## Test plan`'s eight entries match the eight test functions by name and each description matches what the test body actually does — including the two subtle ones (the dispatch test's revert-first requirement, and the reload test's save-and-restore of both process-global halves). It narrates no history: the whole deliberative vocabulary sweep lands on the single rationale-pointer paragraph, which `BUILD.md` requires. No passage depends on a claim the code falsifies. `## Implementation plan`'s `+43` / `+184` match `wc -l` on the two files exactly.

Two things I checked specifically because a spec is easy to leave half-reconciled: the `## Edge cases` `INSTALLED_APPS`-ordering bullet now rests on the real premise (process-global replacements, no cross-app state, idempotent `apply()`) rather than on the retired absence, and `## Goals` item 3 states the `AGENTS.md` hook rule as "a hook lands with the shipped feature that needs it, never ahead of one" — which is the rule the shipped `ready()` satisfies rather than violates. Both are right.

### DRY check — one finding, fixed

The cross-file instrument prior passes used (long sentences compared pairwise, threshold 0.85) reported zero. Mine, run at threshold **0.80** with a wider length window, found **two pairs above 0.85** — 0.935 and 0.882 — and following them surfaced a systematic defect the threshold had been hiding.

**Five rationale entries restated positive arguments that stayed in the spec.** The rationale's own `## Provenance` "Reconciled in place" list says the positive `Justification:` arguments "were re-set as plain body prose under the Decision" — i.e. they did **not** move. Five Decision entries (2, 5, 6, 7, 8) nonetheless opened with "**The positive arguments** (the moved `Justification:` block): …" and repeated them, one of them (Decision 2) even labelling them "now body prose in the spec" before repeating them anyway. That is content duplicated across the move's boundary, which is the exact failure the move exists to prevent, and it is a **copy** in five places rather than a move.

Fixed in both directions. Each of the five entries now points at the Decision's bullets in the spec instead of restating them, and where an argument genuinely did not survive into the spec it is kept and named as the only thing recorded there — Decision 6's "`KANBAN.md` already pinned the same policy, so the Decision was never its only carrier" is the one such case. On the spec side, Decision 6 carried the same argument twice in its own bullet list ("so this card's reader does not have to chase the cross-spec reference" and "without chasing the cross-spec pointer"); the two bullets are collapsed into one that keeps the linked `spec-020` Decision 10 reference. After the fix the pairwise comparator returns **zero pairs at or above 0.80** across the two files, and zero exact duplicates.

### Spec changes made (Worker 1 only)

| # | Passage | Change | Reason |
|---|---|---|---|
| 1 | rationale `## Provenance of this record`, the `AGENTS.md` paraphrase-citation bullet | The four digits (`111` occurrences / `27` files / `16` distinct / `3` resolving) dropped; the corpus rule kept and expanded with why no digit accompanies it; the retraction of "not one resolves" kept. | Resolves Worker 3's escalated Medium. The resolving tail was false as written (re-derived: 2 distinct / 4 occurrences) and the headline pair is unstable against a corpus under concurrent edit — four sweeps, four answers. |
| 2 | rationale, Decision 2 / 5 / 7 / 8 entries, each opening "**The positive arguments** (the moved `Justification:` block): …" | Replaced with a pointer to the Decision's bullets in the spec; each states that nothing in the block was left behind. | DRY: these arguments were reconciled in place, not moved, so restating them made the move a copy in four places. |
| 3 | rationale, Decision 6 entry, same paragraph | Replaced with a pointer plus the one argument that did **not** survive into the spec (`KANBAN.md` already pinned the policy). | Same finding; this is the one entry with content of its own to keep. |
| 4 | spec `### Decision 6 — Joint `0.0.7` cut`, first two bullets | Collapsed into one bullet keeping the linked [Decision 10][spec-020-decision-10] reference. | Both bullets made the same "don't chase the cross-spec reference" argument — an argument told twice inside one Decision. |
| 5 | rationale `## Provenance of this record` byte figures | Re-measured after the last content edit of this pass and substituted at equal width; re-measured after the substitution to the same reading. Spec **64,813**, rationale **80,506**, shed **32,705** (`97518 - 64813`), surplus **47,801** (`80506 - 32705`). | Edits 1-4 falsified all four figures. The paragraph reports the size of the file that carries it, so the substitution has to be width-neutral or it moves the number it reports. |

The artifact's two header reference lines carried pass 3's byte figures, which this pass falsified; they now read the measured post-pass sizes. That is the file header, not a prior entry.

**Twin sweep after every figure change** (the standing lesson of this cohort): `grep` over both standing docs for `32,650`, `32,577`, `48,164`, `48,613`, `48,647`, `64,941`, `80,741`, `81,224`, `81,318` returns **0** in both. A full numeral sweep of the rationale (`[0-9]{1,3},[0-9]{3}|[0-9]{4,}`) returns only the five byte figures — the shed twice, by the design the paragraph states — the four commit-hash digit runs, the `sed` range `34,513`, the Trac id `37064`, and calendar years. The spec's numerals are `2026` and `37064` only.

### Validation run

- `uv run pytest tests/test_apps.py --no-cov` -> **8 passed** in 1.58s. No `--cov*` flag. The cohort touches no `.py`, so this is confirmation, not a gate.
- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-021-apps-0_0_7.md` -> `OK: 12 terms - all have glossary entries and at least one spec link.`, **exit 0**. Re-run after the last edit.
- `uv run python scripts/check_trailing_commas.py --check` on both files -> **exit 0**.
- `uv run ruff format .` / `uv run ruff check --fix .` — not applicable; no `.py` touched.
- **In-page anchors, re-swept after the last edit** by slugging every heading's rendered text outside fenced blocks (reference-style headings slug to their label alone) and differencing the `](#…)` uses. Spec: 31 headings, 15 distinct anchors, 14 resolve; the 15th is the known false positive `(#django-appconfig)`, which is text inside the `docs/GLOSSARY.md #"[Django `AppConfig`](#django-appconfig)"` citation and not a link — re-read to confirm. Rationale: 27 headings, 6 distinct anchors, **all resolve**. My first run of this sweep reported nine spec anchors unresolved; the fault was **my slugger**, which collapsed whitespace runs with `\s+` where the slug rule replaces each space individually (so `Decision 1 — Module` -> `decision-1--module`, two hyphens). Recorded because a broken instrument that indicts the file is the same trap this cycle keeps hitting, one level out.
- **Cross-file anchors, rationale -> spec:** all 8 `[spec-021-dN]` fragments matched against slugs re-derived from the spec's current headings — all resolve.
- **Reference-link integrity, both files:** zero undefined uses, zero unused definitions, every non-URL definition path exists on disk resolved from its own file's directory. Both files carry `<!-- LINK DEFINITIONS -->` and all ten canonical group headers in the required order, and **every group in both files is alphabetical** (checked by parsing each group and comparing against its sort). The rationale's apparent `0-9` / `a-z0-9-` refs remain character classes inside code spans.
- `AGENTS.md` rule 27: `grep -cE '[A-Za-z0-9_/.-]+\.(py|md|toml):[0-9]+'` over both standing docs -> **0** in each. Rule 4: neither file names the forbidden files (the two `feedback` hits are the common noun in "six revisions of review feedback").
- `git status --short` -> **24 paths**. This cohort's three are `M docs/SPECS/spec-021-apps-0_0_7.md`, `?? docs/SPECS/appx/spec-021-apps-0_0_7-rationale.md`, `?? docs/builder/bld-review-1-rationale_and_spec_reconciliation.md` — all three in the writable list. `docs/builder/worker-memory/` is gitignored. The other **21** are concurrent-session work, enumerated: the two declared baseline-dirty `build-020` paths (`docs/builder/bld-003-final.md` is no longer dirty and is therefore not among them), Worker 0's two plans (`build-021`, `build-022`), 7 package modules and 5 test modules under a concurrent refactor, `docs/SPECS/spec-051-…`, one further `docs/` path, and the `spec-022` trio (the spec, its new `appx/` rationale, and `bld-review-1-spec_022_reconciliation.md`) from a concurrent session running that spec's own round. **None edited, none reverted** (`AGENTS.md` rule 34).

### Deferred work catalog — consolidated and re-derived

The cycle's deferrals, gathered from the three `### Notes for Worker 1` blocks into one authoritative list for `bld-final.md`'s `### Deferred work catalog`. **Every population below was re-derived at this pass's write time**, not copied from the notes; the source section, the licensing clause where one exists, the corpus each figure is pinned to, and the re-run instruction for the drift-sensitive ones are stated per item.

1. **`CHANGELOG.md`'s `[0.0.7]` `### Added` entry understates the dispatch.** Source: pass-1/2/3 `### Notes for Worker 1` item 1, confirmed by Worker 3 twice. Licensing clause: none in this cycle — `AGENTS.md` #"No CHANGELOG.md updates unless told" forbids the edit and the plan grants no permission (the spec's own Slice 3 grant covers only the original card's append). The entry says the `ready()` body "imports `django_strawberry_framework._django_patches` and calls `apply()`" — one applier where three ship; accurate when `300e2811` landed, falsified by `c7cb5f5c`. Corpus: `CHANGELOG.md` in the working tree, which is **clean** (`git status --short CHANGELOG.md` empty), so the figure is `HEAD`'s and is **not drift-sensitive**. Second, separable defect in the same file: pre-renumber card labels. Re-derived here rather than restated — `grep -oE '01[0-9]-[a-z_0-9]+-0\.0\.[0-9]+' CHANGELOG.md` gives **13 occurrences across 8 distinct labels**, of which this card's `017-appspy_and_django_app_config-0.0.7` is 1. **Do not conflate that with the 14-occurrence / 7-distinct figure a `KANBAN.md` note records — that is a different population in a different file.**
2. **`[spec-016]` / `[spec-017]` ref-id residue in sibling files.** Source: pass-1 notes item 2, population corrected at pass 2, re-derived at pass 3. Licensing clause: none needed — the files are outside every cohort's writable set. The residue is **definition lines whose ref-id number and target basename disagree**, never token hits. Instrument: `git grep -nE '^\[spec-01[67][a-z0-9-]*\]:' -- docs/SPECS KANBAN.md`, comparing each ref-id's number against its target's basename. **HIGHLY DRIFT-SENSITIVE.** Pinned at `51eb47ba`: 32 definitions, 16 disagree, 16 agree; one disagreeing was this spec's own, repaired by this round, leaving 15 in siblings (7 `spec-022`, 3 `spec-023`, 2 `spec-025`, 2 `spec-027`, 1 `KANBAN.md`). **Re-derived in the working tree at this pass's write time: 24 definitions, 8 disagree, 16 agree — `spec-023` 3, `spec-025` 2, `spec-027` 2, `KANBAN.md` 1.** `spec-022`'s seven are gone under the concurrent session's uncommitted work. **Re-run the command at write time; do not copy either number.**
3. **`spec-022` asserted the claim F1 retired, about this very spec.** Source: Worker 3 pass-1 Medium 5, population corrected twice (two -> three sites). Licensing clause: none — `spec-022` is outside this cohort in either state. At `51eb47ba` the file carries four `ready()` passages (`grep -n 'ready()'` -> 98, 130, 390, 577): three assert the retired claim — the `## Problem statement` predecessor paragraph, the `## Non-goals` command-hook bullet ("which is preserved here"), and the `## Edge cases and constraints` command-discovery bullet ("it has no `ready()` body and does not need one") — while Decision 3's `finalize_django_types` anti-pattern paragraph cites Decision 4 for a rule the inversion leaves intact and is **not** false. Its `[spec-017-decision-4--no-readyhook-in-0-0-7]` definition also targets an anchor that never resolved at `51eb47ba` (the real slug was `decision-4--no-ready-hook-in-007`). **HIGHLY DRIFT-SENSITIVE: re-derived at this pass's write time, the working-tree file carries zero `ready()` occurrences** — the concurrent session's `spec-022` round removed all four, and that work is **uncommitted**. **Catalog instruction: re-run `grep -c 'ready()'` against whatever `spec-022` state lands, and drop the item if that session's work commits.**
4. **Non-shipped `Status:` lines on shipped cards** (F3's defect class on specs this cycle does not own). Source: pass-1 notes item 4. Re-derived at this pass's write time by reading line 4 of each: **`spec-025-scalar_map_helper-0_0_7.md` still reads "Only the final test-run gate remains" on a shipped card** (1 occurrence; the file is **clean**, so this is `HEAD`'s state and not drift-sensitive). `spec-022`'s line 4 now reads shipped-and-archived under the concurrent session's **uncommitted** work — drift-sensitive, re-check. `spec-023`'s was already correct. **Catalog: `spec-025` only, unless `spec-022`'s concurrent work is reverted.**
5. **The `AGENTS.md` citation convention across `docs/SPECS/`** — a repo-wide decision, not a per-spec fix. Source: pass-2/3 notes item 6, escalated as a Medium and resolved above. **Publish the corpus rule, never a digit copied from this cycle:** four independent sweeps in this round returned four different occurrence-and-file pairs (`25 / 101`, `23 / 109`, `111 / 27`, `122 / 28`), because two corpus files are under concurrent rewrite and line-wrapped citations fold differently under different extractors. The one stable finding is qualitative and must be carried: **the class is not uniformly broken — at least two distinct substrings occur in `AGENTS.md` verbatim — so "not one resolves" must not be restated.** If the catalog wants a number, it re-runs the rule and timestamps the reading.
6. **Decision 6's four-card bundle vs `KANBAN.md`'s seven `0.0.7` cards. NO ACTION, recorded so it is not re-opened.** The Decision states the WIP set at authoring time excluding the already-shipped `DONE-020-0.0.7`; `DONE-024` and `DONE-026` joined the release afterwards. Its subject is the version-bump policy, which no later card joining the release affects, and rewriting the bundle would make the Decision assert something it never decided. Worker 3 endorsed this three times; I endorse it a fourth and it is closed.

**Explicitly not in this catalog:** `tests/test_apps.py`'s `spec-017` provenance comment. Worker 0 records it as **F8** and dispatched it to **R2**, the only cohort with a Worker 2. `git diff HEAD -- tests/test_apps.py` returns zero lines, so R1 left it untouched. **It is R2's work item, not a deferral — do not double-count it in `bld-final.md`.**

### Final status

`final-accepted`.

Every dispatched finding's tick was re-tested and holds; no box is un-ticked and none is left undeferred. The escalated Medium is resolved by a spec-authoring call — the corpus rule stands, the four digits are gone — rather than by publishing a fifth number over a corpus somebody else is editing. Both Lows are verified against `51eb47ba` and corrected here, one of them with an imprecision of its own named. The spec states the shipped contract completely, narrates no history, and holds clause-by-clause against `apps.py` and `tests/test_apps.py`. The one substantive defect this pass found on its own was a DRY defect the prior instrument's threshold had hidden — five rationale entries copying arguments the spec still carries — and it is fixed on both sides of the boundary, with the cross-file comparator now returning zero pairs at or above 0.80.

Status: final-accepted.
