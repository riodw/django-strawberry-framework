# Build: Cross-slice integration pass (`spec-033` residual reconciliation cycle)

Spec reference: `docs/SPECS/spec-033-connection_optimizer-0_0_9.md` (whole file) + `docs/SPECS/appx/spec-033-connection_optimizer-0_0_9-rationale.md` (whole file)
Status: final-accepted

**Shape.** Worker-1-owned pass ([`docs/builder/BUILD.md`][build-md] `## Cross-slice integration pass`, [`docs/builder/worker-1.md`][worker-1] `## Integration pass`), with no Worker 2 build pass and no Worker 3 review pass, so it carries one combined Plan + Final-verification block. The `## Build report (Worker 2)` and `## Review (Worker 3)` sections of [`ARTIFACT.md`][artifact-md] are deliberately absent, not omitted; the validation run, the failability position, and the hot-path / floor declarations are folded into `## Final verification (Worker 1)`.

Input: all seven prior `bld-033-*` artifacts, read in full and in order, plus both spec files and the build plan. Raw `path:NN` references appear only in this file, per [`AGENTS.md`][agents] #"Source refs in docs and code comments" (per-cycle scratchpad carve-out). Every citation this pass wrote **into the spec** is symbol-qualified or a heading reference.

**Every number in this artifact was measured at the moment it was written**, with the instrument this cycle converged on: join wrapped comments (`re.sub(r"\n\s*#\s?", " ", src)`) **first**, then normalize whitespace, then fold hyphenation where the target admits it, then count **occurrences** rather than matching lines.

---

## Plan (Worker 1)

### Spec status-line re-verification

Read `docs/SPECS/spec-033-connection_optimizer-0_0_9.md` lines 1-9 (title, shipped-in line, `Status:`, Owner, Predecessors) at the start of this spawn, per [`worker-1.md`][worker-1] `## Spec status-line re-verification`. All still describe the build's current state after Slice 0 and Slice 2: the card is `DONE-033-0.0.9`, the `Status:` line reads `SHIPPED (0.0.9)` and describes the seven **original** slices (true as history, and the sentence is explicitly a completion record rather than a prediction), the unticked-checklist convention it invokes still holds, the rationale-companion pointer Slice 0 added resolves, and no predecessor doc it names has been deleted. **No status-line edit was required by this pass, and none was made.**

The one status-shaped sentence worth naming as *deliberately left*: the `Status:` line's closing "cross-slice integration pass + final test-run gate green" describes the `0.0.9` build's own gates, not this residual cycle's. It is true of the build it records. Rewriting it to mean this cycle's gates would turn a completion record into a claim about a pass that had not finished when the sentence was read.

### DRY analysis

- **Helper inventory checked.** Not applicable in the package sense: this pass edits markdown only and proposes no helper, so the package-wide AST inventory ([`worker-1.md`][worker-1] `### Package-wide helper inventory before helper planning`) has nothing to prevent. What the pass owes instead is the **cross-cohort** inventory `BUILD.md` steps 3 and 4 define, and that is performed in full below against all 14 emitted shadow overviews — not against a subset, and not against the cohorts' recorded readings of them.
- **Existing patterns reused.** The artifact shape is the one Slice 0 and Slice 2 established for a Worker-1-only pass in this cycle; the counting instrument is R3's; the attribution discipline (class every dirty file from **diff content**, never from `git status` membership) is R1a's and R2's.
- **New helpers justified.** None.
- **Duplication risk avoided.** The hazard for an integration pass is restating a cohort's finding as though it were new. Every item below either (a) reproduces a cohort's measurement and says so, (b) corrects one and says which, or (c) is new and says that. Nothing is re-derived silently.

### Dispatched findings checklist

The six `BUILD.md` `## Cross-slice integration pass` preconditions, then the findings Worker 0 routed to this pass to close or explicitly defer.

- [x] **1.** Read every prior `bld-033-*.md` artifact, in order, in full
- [x] **2.** Confirm `scripts/review_inspect.py` ran, or was explicitly skipped with a recorded reason, for every `.py` file with review-worthy logic this cycle touched
- [x] **3.** Compare the **Repeated string literals** section across every shadow overview; record cross-file literals
- [x] **4.** Compare the **Imports** sections; confirm one-way direction and spot any sibling importing outside the documented boundary
- [x] **5.** Walk every accepted artifact's `What looks solid` and `DRY findings` sections for deferred follow-up
- [x] **6.** Re-run the staged-anchor sweep myself and record the result
- [x] **R1.** R3's `connection.py` survey states "27 lines" where the grep returns 35 — corrected in the artifact that carries it
- [x] **R2.** R3's `Decision-<N>` "38 across 25" is a pre-edit figure stated beside post-edit counts — dated in place
- [x] **R3.** `bld-033-review-2`'s `Decision-6` "8 times in 6 files", self-falsified by its own five-file enumeration — corrected
- [x] **R4.** The larger bare-`Decision N` exposure in `tests/test_relay_connection.py` — graded, and routed as deferred work rather than a non-issue
- [x] **R5.** The `nested_fetch.py` "Decision 6 shape 4" class, generalised — routed to the catalog with a recommendation
- [x] **R6.** R2 pass 3's recommended Decision 6 intro sentence — **accepted and landed** (`### Spec changes made (Worker 1 only)`)
- [x] **R7.** The three `## Escalations` plus the fourth (the strategy seam has no owning spec) — recorded, not resolved

### Implementation steps

1. Read the standing docs, both spec files, the build plan, and all seven cohort artifacts.
2. Run the six preconditions as measurements, not as re-readings of the cohorts' recorded measurements.
3. Run the cross-slice scan proper over the whole cycle diff, classifying every dirty file by **diff content**.
4. Correct the three artifact-only counts, count-only, each with the re-derivation beside it.
5. Decide the Decision 6 intro sentence and land it if accepted; re-run both gate scripts and the citation gate.
6. Write the deferred-work contribution under `### Notes for Worker 1 (spec reconciliation)` so `bld-033-final.md` inherits it from disk.

### Test additions / updates

None, and none possible: this pass edits markdown only. `pytest` was **not** run — the final gate owns the suites and follows immediately ([`docs/builder/BUILD.md`][build-md] `## Final test-run gate`), and no `--cov*` flag was used anywhere in this cycle.

### Implementation discretion items

None delegated — single-worker pass, no builder. Four choices were **assessed and decided here**:

- **The Decision 6 intro sentence lands.** Three cohorts converged on it independently (R2 pass 2 proposed it, R2's pass-3 reviewer widened it by "nor by heading text", R3 re-recommended it with a 13-site measurement), and this pass adds a fourth, independent data point measured below. It is one normative sentence in a Decision's introduction; it costs 247 bytes and closes the only instrument available for a rot class no gate can see.
- **No spec edit is made in reaction to the mis-sited marker-row citations.** The cheap-looking repair is a cross-pointer in Decision 4. It is the wrong direction: the spec is the contract and source comments cite it, not the reverse, and the four citations in question are a concurrent session's uncommitted prose. A contract document must not be edited to make observed content true.
- **The pass closes `final-accepted` rather than `revision-needed`, despite a live incoherence in this cycle's subsystem.** The incoherence is provably not this cycle's (attribution below). `revision-needed` would route it into a cohort loop of *this* cycle, which would have to write files another session is actively writing — the collision `AGENTS.md` rule 34 exists to prevent. It is recorded, attributed, and escalated instead.
- **The `tests/test_relay_connection.py` bare-`Decision N` exposure is deferred work, not a non-issue.** Reasoning under `### R4` below.

---

## Final verification (Worker 1)

### Precondition 1 — every prior `bld-033-*` artifact read, in order

| # | Artifact | Bytes | Read |
|---|---|---|---|
| 1 | `bld-033-slice-0-rationale_extraction.md` | 29,002 | full |
| 2 | `bld-033-review-1a-plan_side_foundation.md` | 68,507 | full |
| 3 | `bld-033-review-1b-fast_path_strictness.md` | 61,394 | full |
| 4 | `bld-033-review-1c-cache_examples_census.md` | 64,290 | full |
| 5 | `bld-033-slice-2-spec_reconciliation.md` | 46,083 | full |
| 6 | `bld-033-review-2-py_comment_repair.md` | 207,563 | full; the four verbatim digest-table dumps were read as tables rather than line by line |
| 7 | `bld-033-review-3-retired_vocabulary_sweep.md` | 87,701 | full |

589,368 bytes total. No "as needed" reading. `docs/builder/bld-003-final.md` and `0_0_14.md` were neither read as this cycle's nor touched.

### Precondition 2 — `scripts/review_inspect.py` coverage

**Every production `.py` file this cycle touched has an emitted overview, and every one was walked by a cohort with all four sections read.** 14 overviews exist under `docs/shadow/`; the six production files in this cycle's partition are all among them.

| File | Ran by | Sections walked |
|---|---|---|
| `django_strawberry_framework/connection.py` | R1b, R2 pass 1, R3 | all four |
| `django_strawberry_framework/optimizer/plans.py` | R1a, R2 pass 1 | all four |
| `django_strawberry_framework/optimizer/walker.py` | R1a, R2 passes 1-2 | all four |
| `django_strawberry_framework/optimizer/nested_fetch.py` | R1a, R2 passes 2-3, R3 | all four |
| `django_strawberry_framework/optimizer/nested_planner.py` | R1a, R3 | all four |
| `django_strawberry_framework/optimizer/lateral_fetch.py` | R1a, R3 | all four |

**Recorded skips, all with reasons on disk:** R2 pass 2's review states why `connection.py` and `optimizer/plans.py` were not re-run in that pass (neither was written by it; both hold their pass-1 digests; pass 1 already walked and recorded all four sections). That is the explicit-skip form the precondition asks for.

**One gap, recorded here on the cohorts' behalf rather than routed as a finding.** No artifact records a run-or-skip disposition for any of the seven **test** files this cycle wrote, and `tests/optimizer/test_walker.py` crosses the helper's own Worker-3 trigger — `+87 / -14` lines against `HEAD`, past the "50+ lines to any file outside `django_strawberry_framework/`" threshold in [`BUILD.md`][build-md] `### When to run the helper during build`. The disposition, measured rather than assumed:

- Exactly **two** of this cycle's test files differ from `HEAD` at the executable level: `tests/optimizer/test_walker.py` and `tests/optimizer/test_extension.py` — precisely R2's two failability-proved behavior repairs (digest evidence under `### Verification commands`). Every other test file's change is comment-only.
- Both executable repairs were reviewed by **transient mutation with listed failing node ids at a recorded scope**, re-run independently by Worker 3, plus a deselect counterfactual. That is a strictly stronger instrument than the helper's static overview for the property in question.
- Disposition for the remaining five: **no review-worthy logic** — comment and docstring text only, proven by AST identity rather than asserted.

So the substance is discharged and only the record was missing; it is recorded now. Not `revision-needed`: re-running a static overview on files whose executable structure is proven byte-identical would reproduce a reading of an unchanged file.

### Precondition 3 — Repeated string literals across all 14 shadow overviews

Compared mechanically across every overview, not by reading the cohorts' quotations of their own sections.

**Cross-file literals (a literal listed as repeated in two or more overviews): two, both rejected as consolidation candidates.**

| Literal | Files | Verdict |
|---|---|---|
| `connection` | `optimizer/walker.py` x3, `types/finalizer.py` x5 | Not a shared constant. In `walker.py` it is the `resolved[0] == "connection"` selection-target discriminator; in `finalizer.py` it is the `Meta.relation_shapes` value and the synthesized-field suffix. Same word, three unrelated namespaces. Naming them one constant would assert a coupling that does not exist. |
| `selections` | `optimizer/selections.py` x8, `optimizer/walker.py` x2 | The graphql-core AST attribute name, read through `getattr` / node access. Not a package-owned key. |

**The literal family that would have mattered is single-sourced, verified rather than assumed.** The `_dst_*` window annotation names — the one family whose cross-module drift would be a correctness bug — are defined once in `optimizer/plans.py` (`WINDOW_ROW_NUMBER`, `WINDOW_TOTAL_COUNT`, `WINDOW_ROW_NUMBER_REVERSED`, `WINDOW_ROW_NUMBER_ABS`, `WINDOW_KEYSET_SEEK_COUNT`) and every consumer imports the symbol: `connection.py`, `optimizer/lateral_fetch.py`, `optimizer/single_parent_fetch.py`. The sidecar-kwarg family is likewise single-sourced in `utils/connections.py`. This reproduces R1a's DRY-3 independently.

**One correction to a cohort's literal finding.** R1a's Low `#"_optimizer_runtime_prefixes` is a bare literal in two modules"` overstates its own heading. Measured: the **string literal** `"_optimizer_runtime_prefixes"` occurs in exactly **one** module, `optimizer/walker.py`, twice, both inside `getattr` calls (`walker.py:417`, `:1399`). `optimizer/selections.py` carries the name as a **keyword argument** (`selections.py:473`) and in a docstring — an identifier, not a literal. The body of R1a's finding says "read in", which is accurate; only its heading claims a shared literal. The shape is still a real cross-seam attribute-name grammar with no named constant, and it is still cheap to name — recorded as deferred work under its accurate description.

**Nothing else crosses a file.** `optimizer/extension.py` and `optimizer/single_parent_fetch.py` report `None`, as R1c recorded for the first of them.

### Precondition 4 — Imports and dependency direction

Compared across all 14 overviews' `Imports` sections. **The two invariants this cycle established both hold, and both were checked in both directions.**

- **`optimizer/selections.py` exists to remove a reverse `extension` -> `walker` import for the selection helpers, and it does.** `selections.py`'s only intra-package import is `from ..utils.typing import schema_config_from_info` — it is a leaf. Both consumers import *from* it: `extension.py:102` (10 names) and `walker.py:37` (8 names). `extension.py` still imports `walker.py` (`:114`, `plan_optimizations` / `plan_relation`) — that is the plan entry point, not a selection helper, and it is the direction Decision 11 prescribes. **No module under `optimizer/` imports `extension.py`.**
- **`walker.py` and `connection.py` do not import each other.** `connection.py` reaches the optimizer through `optimizer.extension`, `optimizer.nested_planner`, `optimizer.plans` and `optimizer.selections` and **never** through `optimizer.walker`; `walker.py` contains no `..connection` import at any level, module or function-local. Verified from the overviews and re-verified by AST over the two files.
- **One-way and cycle-free on the plan path:** `walker -> nested_planner -> {nested_fetch, plans, selections, join_taxonomy, keyset, utils/connections}`; `plans -> join_taxonomy`; `join_taxonomy -> utils/relations`; `selections -> utils/typing`. No back edge.
- **The fetch-strategy triangle is cyclic by construction and broken deliberately.** `nested_fetch <-> lateral_fetch` and `nested_fetch -> single_parent_fetch -> {lateral_fetch, nested_fetch}` close a cycle; five of `nested_fetch.py`'s eighteen imports are **function-local** (`:184`, `:364`, `:398`, `:411`, `:426`), each with an adjacent comment naming the cycle it breaks. Recorded as documented-and-intentional, matching R2 pass 2's reading.
- **`types/finalizer.py:669` imports `..connection` function-locally**, closing the `connection -> types.resolvers` / `finalizer -> connection` cycle the same way. Also intentional.

**The private-import population, measured tree-wide — and this is the finding, because two cohorts each reported one instance as a boundary anomaly.** R1a's DRY-2 flagged `connection.py:75` (three `_`-private names from `optimizer.nested_planner`); R1c's L6 flagged `optimizer/extension.py:95` (`_active_strategy` from `.nested_fetch`). An AST sweep of every relative `ImportFrom` in `django_strawberry_framework/` carrying at least one underscore-private name returns **76 statements across 45 modules**. Two more sit inside this cycle's own subsystem and no cohort named either: `optimizer/single_parent_fetch.py:51` (**four** private names from `.lateral_fetch`) and `optimizer/walker.py:25` (`_coerce_pagination_int` from `.nested_planner`).

The verdict is an **anchor** measurement, not a distance one: a cross-module private import is an established house convention in this package, not a boundary violation, and neither flagged instance is anomalous against its population. **R1c's L6 is therefore closed here as not-a-defect**, and re-flagging it in a later cycle would be a repeat. R1a's DRY-2 survives on entirely different grounds — not that the names are private, but that Decision 11 created `utils/connections.py` as the neutral, cycle-safe home for exactly the plan-side/resolve-side shared grammar the `to_attr` builders are, and they are not in it. That half is carried forward.

### Precondition 5 — deferred follow-up from `What looks solid` and `DRY findings`

Every accepted artifact's two sections were walked. Items that could land in this pass: **one** — R2 pass 3's Decision 6 intro sentence, which is a spec edit and is landed below. Everything else is either already closed inside the cycle, or is a `.py` / doc-surface item this cycle's fence or another session's ownership puts outside it. The full inventory, with disposition, is in `### Notes for Worker 1 (spec reconciliation)` so the final gate inherits it from disk.

Two `What looks solid` observations are worth promoting into the cycle's own record rather than leaving them per-cohort, because both are cross-cohort facts rather than one artifact's opinion:

- **The cursor-parity invariant is better served at `HEAD` than the spec describes**, and independently so on both legs: plan-time and resolve-time share `optimizer/plans.py::effective_connection_order` (the whole precedence ladder, not only the pk-append rule), pinned by an object-identity assertion; and plan-time and resolve-time share `utils/connections.py::derive_connection_window_bounds` for the bounds. R1a found the first, R1b the second, and neither saw the other's. Together they are the structural reason the fast path cannot drift from the plan.
- **Every window refusal is fail-closed toward the shipped per-parent pipeline.** Nine refusal arms, three `except BaseException` classifier guards, and two clamp-shaped candidates were examined across R1a and R1b, and every incoherent input lands on *unplanned* — the pre-`033` behavior, which strictness can still see. The one fail-open shape found anywhere in the cycle (R1b's M1) is on the *diagnostic*, not on a data path.

### Precondition 6 — staged-anchor sweep, re-run

Re-run here rather than inherited. Instrument: every tracked file (`git ls-files`, all types, binaries decoded with replacement), wrapped comments joined **first**, whitespace normalized, then `TODO\(spec-033|TODO-(ALPHA|BETA|STABLE)-033`, counting occurrences.

**Result: 9 occurrences in 5 files. Zero in shipped source or tests.**

| File | n | Classification |
|---|---|---|
| `examples/fakeshop/db.sqlite3` | 3 | The kanban boards' generated source. Excluded by the rule covering `KANBAN.md` / `KANBAN.html` / `BACKLOG.md`, which it renders. |
| `docs/SPECS/spec-034-permissions-0_0_10.md` | 3 | `TODO-ALPHA-033-0.0.10` — a **pre-renumbering** id for the permissions card, quoted by spec-034 as rot it found in `TODAY.md`. Belongs to a different card under a numbering that no longer exists. |
| `docs/SPECS/spec-033-connection_optimizer-0_0_9.md` | 1 | The spec's **own description of the convention** ("a source-site `TODO(spec-033 Slice N)` comment naming this spec and the owning slice"). Prose about the discipline, not an anchor. |
| `docs/SPECS/appx/spec-022-export_schema-0_0_7-rationale.md` | 1 | A historical table row: `TODO-ALPHA-033` for `0.0.12`, superseded by `DONE-043-0.0.14`. A past plan under a past numbering. |
| `docs/builder/DONE/build-032-full_relay-0_0_9.md` | 1 | `TODO(spec-033/035/036` inside a closed cycle's *description of its own grep*. Prose about anchors. |

**Independent confirmation for source specifically:** `grep -rn 'TODO(spec-033' --include='*.py' .` returns nothing, and an AST-free sweep of all 434 tracked `.py` files for every `TODO(...)` anchor of any spec returns ten, naming `spec-035` (x4), `spec-036` (x2), `spec-056`, `BACKLOG`, `unscheduled`, and one polymorphic-interface backlog item. **None names `spec-033`.** `tests/test_connection.py:1588`'s anchor, live at Slice 0, was discharged by R2 repair 1 and the re-classified provenance sentence is present.

**Recorded discrepancy against Worker 0's sweep, because a sweep whose instrument you did not verify is not a sweep.** Worker 0 reported one hit (`db.sqlite3`); I find nine across five files. The difference is entirely instrument width — my pattern also matches the bare card form `TODO-ALPHA-033` without a version suffix, which is what surfaces the four `.md` hits belonging to other cards under older numbering. **The substance is identical and both readings agree on it:** no staged anchor naming this build survives anywhere in shipped source, tests, or comments.

### The cross-slice scan

#### Do the comments now tell one coherent story? — **No, and the incoherence is not this cycle's**

This is the load-bearing question for a cycle whose every edit was a comment, and it is the pass's one substantive finding.

**One contract is now named three different ways across `.py`.** The marker-row disambiguation — the shipped answer to `first: 0` and an overshot `after:` — is cited in eleven passages:

| Naming | Sites | Resolves? |
|---|---|---|
| `spec-033 Decision 5` | 7 — `connection.py` x2, `test_library_api.py` x1, `tests/test_relay_connection.py` x2, plus two in `connection.py`'s dispatch prose | **Yes.** The spec states the marker-row contract in Decision 5 (`#"first: 0` and an overshot `after:` are served from the window, not fallen back."`), plan side and resolve side both. |
| `spec-033 Decision 4` | 4 — `connection.py` #"With marker rows planned for the ambiguous shapes", `optimizer/lateral_fetch.py` #"the ambiguous-shape marker rows", `optimizer/plans.py` #"Marker rows (spec-033 Decision 4", `tests/optimizer/test_plans.py` #"The marker-row disambiguation" | **No.** Decision 4 states no marker-row contract. Its only occurrence of the word "marker" is the unrelated `_dst_synthesized_relation_connection` marker in the `to_attr`-isolation bullet. A reader following the citation finds nothing. |
| `Workstream C` | 3 — `optimizer/lateral_fetch.py`, `utils/connections.py`, `tests/test_relay_connection.py` | **No.** Retired build-time vocabulary that names no spec structure at all. |

Four of those citations are mis-sited and three are un-sited, in the same subsystem, for the same contract. That is the definition of the comments not telling one story.

**Attribution, established from diff content rather than `git status` membership.** These citations are the product of a **`workstream` vocabulary sweep that is not this cycle's**:

- **Population:** `workstream` went from **38 occurrences in 12 files** at `HEAD` to **3 in 3 files** in the worktree. 35 replacements.
- **Files:** `connection.py`, `optimizer/lateral_fetch.py`, `optimizer/nested_planner.py`, `optimizer/plans.py`, `optimizer/selections.py`, `optimizer/walker.py`, `examples/fakeshop/test_query/test_library_api.py`, `tests/optimizer/test_plans.py`, `tests/optimizer/test_selections.py`, `tests/optimizer/test_walker.py`, `tests/test_relay_connection.py`.
- **Two of those eleven — `optimizer/selections.py` and `tests/optimizer/test_selections.py` — are the files Worker 0's dispatch independently attributes to the concurrent session**, and they are outside every ownership partition this cycle declared. A sweep spanning them is one authorship, and it is not ours.
- **Timing:** the eleven files' mtimes cluster at 20:52-20:55. R3's two editing windows were 20:20-20:27 and 20:33-20:35, and its artifact closed at 20:52. Every cohort of this cycle had closed.
- **Silence:** no `bld-033-*` artifact records any of it. R3's own build report says its `connection.py` pass was "two hunks in one file"; that file now carries ten.
- **Net effect on citations:** the sweep introduced **17 net-new `spec-033 Decision 4` citations, 3 `Decision 5`, and 1 `Decision 6`** (separating out the 8 `Decision 11 -> Decision 4` re-sitings that are R2's dispatched repair 2). None was verified by any cohort against the Decision text Slice 2 rewrote hours earlier.

**What it does not break.** Checked rather than assumed, because the cycle's hot-path and inverse-proof records all rest on it: **all eleven AST digests this cycle recorded reproduce exactly in the current worktree**, under an instrument written for this pass and carrying a must-see control. The concurrent sweep is comment-only, as this cycle's own work was. Exactly two files differ from `HEAD` at the executable level, and they are R2's two failability-proved test repairs. So every zero-delta hot-path number in this cycle survives, and so does R3's `fallback shape(s)` result (re-derived: `HEAD` 14, R3's baseline 13, worktree **0**).

**Disposition: recorded, attributed, escalated — not repaired here.** `.py` files are outside this pass's writable list; the four mis-sited citations are another session's uncommitted work, which `AGENTS.md` rule 34 forbids editing or reverting; and routing it into a cohort loop of this cycle would put a builder into files a live writer holds. It is the first item in the deferred-work contribution below.

#### Duplicated helpers across cohorts

**None.** The cycle added no helper, no module, no constant, and no executable byte outside two test-file repairs — the AST identity across eleven files is the mechanical form of that statement. The three convergent *prose* shapes the cohorts produced are consolidations rather than near-copies, and they are consistent with each other: the six parent-count deferral sites all use one shape (absolute count + seeded cardinality + a pointer at the two-cardinality pin); the thirteen retired-noun replacements all name the arm by content; the ten cursor-parity citations all resolve on Decision 4 with Decision 11 kept only where the sentence genuinely asserts a module location.

#### Inconsistent naming or error handling between cohorts

**None from the cohorts.** One item that reads like inconsistency and is not: `optimizer/nested_fetch.py`'s five reason strings (`sliced`, `select_for_update`, `combined`, `distinct`, `values`) are a wire contract the function's own docstring declares "stable, test/telemetry-friendly", and hoisting them into constants would hide that. Left alone deliberately by R2, R3 and this pass, and recorded here so a later sweep does not extract them.

Error-handling shape across the subsystem is uniform and uniformly fail-closed: `window_range_plan` **raises** rather than clamping a negative offset or limit; `derive_connection_window_bounds` routes its two incoherent outcomes to *different* refusals (`TypeError` for malformed pagination, `UnwindowableConnection` for a valid-but-unwindowable query); `classify_relation_join` never raises and returns `windowable=False`; `_window_rows_are_annotated` converts any exception during the probe to *reject*. No cohort found a fail-open shape on a data path.

#### Repeated ORM / queryset patterns that should be centralized

**None.** The two patterns that would matter are already single-sourced across the plan/resolve seam and were verified in both directions: window **bounds** through `utils/connections.py::derive_connection_window_bounds` (and its keyset twin), and window **order** through `optimizer/plans.py::effective_connection_order`. Both are imported by `optimizer/nested_planner.py` and `connection.py` alike. That sharing is the cursor-parity invariant's structural guarantee, not a duplication.

#### Misplaced responsibilities between modules

One, carried forward from R1a's DRY-2 and re-verified here: the `to_attr` grammar (`relation_connection_to_attr`, and the per-key `_dst_<field>$<key>_connection` form) lives in `optimizer/nested_planner.py` and reaches `connection.py` through two `_`-private compatibility delegates, while Decision 11 created `utils/connections.py` as the neutral, cycle-safe home for exactly this plan-side/resolve-side shared grammar. It is a real misplacement and it is a source change, so it is recorded, not implemented.

The related observation this pass adds: the two delegates' only non-`connection.py` readers are two of the ten dead `optimizer/walker.py` aliases, so the escalated alias deletion and this relocation are one change, not two — deleting the aliases first makes the move mechanical.

#### Missing or too-broad exports

**None.** `git diff HEAD -- django_strawberry_framework/__init__.py` is empty and the file is absent from `git status --porcelain`. Independently: none of the seven post-ship modules this cycle documented (`selections`, `nested_fetch`, `nested_planner`, `lateral_fetch`, `single_parent_fetch`, `join_taxonomy`, `keyset`) nor `utils/connections.py` is re-exported from the package root, which is what Decision 11's rewritten "**Public surface: none.**" line now states. Four cohorts checked this and all four agree.

#### Repeated literals, keys, and tuple shapes across cohorts

The shadow comparison is above. **One repeated tuple shape crosses files and is a genuine consolidation candidate, and this pass corrects its population.**

R1b escalated the five-exception coercion tuple `except (ValueError, TypeError, AttributeError, KeyError, IndexError)` as "15 occurrences across 2 files (`connection.py` 11, `auth/mutations.py` 4), zero elsewhere", and recommended one shared constant under `utils/` "at the integration pass, where cross-file literals are the declared instrument".

**Re-derived: 16 occurrences across 3 files.** `connection.py` 11, `auth/mutations.py` 4, and `django_strawberry_framework/utils/sessions.py:131` — one occurrence R1b's sweep did not see. The set is identical, member order differs (`AttributeError, KeyError, TypeError, ValueError, IndexError`), and the site is written in the **exploded multi-line** trailing-comma layout this repo's `check_trailing_commas.py` enforces. R1b's sweep declared it counted "both member orders"; what defeated it is the same class this cycle has now hit six times — **an exact-shape regex over a form the source does not use.** A sixth grammar for the list: an **exploded tuple**, where the members are on separate lines and no single line carries the shape.

The consolidation still warrants a source change and is still the right one: `except` accepts a tuple *name*, and one shared constant under `utils/` serves all three files. It is out of this cycle's fence — `auth/mutations.py` and `utils/sessions.py` are in no declared partition and no cohort owns `utils/` — so it goes to the catalog with the corrected population, not to a builder. `utils/sessions.py:152` carries a six-member superset (adds `ImportError`) and is **not** part of the population; a consolidation must not fold it in.

### Concurrent work found mid-pass, attributed by diff content

Recorded per `AGENTS.md` rule 34 and [`BUILD.md`][build-md] `### Tracked binary / generated files`. **Nothing below was edited, reverted, or tidied by this pass.**

- **The `workstream` sweep**, 11 `.py` files — the finding above. Not this cycle's.
- `optimizer/selections.py` and `tests/optimizer/test_selections.py` — dirty, in no partition of this cycle, and the two files whose membership in the `workstream` sweep is what identifies its authorship.
- `KANBAN.md`, `KANBAN.html`, `README.md`, `docs/builder/ARTIFACT.md`, `docs/builder/BUILD.md`, `docs/builder/worker-1.md`, `worker-2.md`, `worker-3.md`, `examples/fakeshop/db.sqlite3` — the concurrent session's, as the dispatch stated. The current `worker-1.md` and `BUILD.md` were read for this pass, per the instruction.
- `0_0_14.md` (untracked) and `docs/builder/bld-003-final.md` (a committed prior cycle's record) — baseline-dirty, neither read as this cycle's nor touched.
- Three files dirty at this cycle's session start — `examples/fakeshop/apps/products/services.py`, `examples/fakeshop/test_query/test_debug_extension_api.py`, `examples/fakeshop/test_query/test_products_api.py` — are **clean now**; a concurrent session committed them mid-cycle. R1a, R2 and R3 each recorded this independently. `test_products_api.py` is byte-identical to `HEAD`, so this cycle's do-not-touch fence on it held end to end.

**Partition arithmetic.** 15 `.py` files are dirty; this cycle declared 13; the two extras are exactly the two the dispatch names as concurrent. But the concurrent sweep also wrote **inside 11 of this cycle's 13**, which is the precise reason `git status` membership is not evidence in either direction and every attribution above is by diff content, mtime clustering, and absence from the artifact record.

### Counts corrected

Three, all artifact-only, all count-only, each re-derived at the moment it was written.

1. **`bld-033-review-3` `### The full bare-reference survey of connection.py`: "27 lines" -> "35 lines / 42 references".** Re-derived with the wrapped-comment-join instrument: `HEAD` **34** lines / **41** references, R3's worktree **35** / **42** — matching its reviewer's independent figure exactly. `27` is neither the line count, the reference count, the qualified count, nor the passage count. The substantive figures all reproduce (**14 bare across 10 passages** at the baseline; **12 bare / 2 qualified** after), so the enumeration was real and complete and only its stated size was wrong. Corrected at both sites that carry it. The file has since moved to **39 lines / 46 references** through the concurrent sweep; that vintage is stated in the correction so a later reader does not read the drift as a discrepancy.
2. **`bld-033-review-3` `#### Measured and deliberately left`: the `Decision-<N>` hyphenation figure is dated in place.** "38 occurrences across 25 `.py` files" was true at R3's baseline; the tree now carries **37 across 25** (`HEAD` **39 across 26**). The arithmetic reconciles with no residue: R2's Low 4 repair removed one, R3's site 2 removed one. Both figures re-derived; the sentence now carries its vintage rather than sitting undated beside post-edit counts.
3. **`bld-033-review-2` `### Low 5` item 3: `Decision-6` "8 times in 6 files" -> "8 times in 5 files".** Self-falsified by the five-file enumeration printed in the same sentence, which sums to 8. Its own pass-3 reviewer measured 8-in-5 independently and graded it `Low 6`; the occurrence count — the load-bearing half — was always right.

**A fourth stated count, re-derived and left where it is.** R3's `### Notes for Worker 1` item 2 says `tests/test_relay_connection.py` carries "20 `Decision N` references, 15 of them bare". Measured: `HEAD` **20 references / 16 bare**; worktree **24 / 15**. The two halves of R3's figure are from different vintages of a file that moved under it. No correction is owed — the note is addressed to me, I am the consumer, and the substance (the file has no safe default and the exposure is growing) is unchanged and now larger by four references.

### Verification commands and their real results

- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-033-connection_optimizer-0_0_9.md` -> `OK: 38 terms - all have glossary entries and at least one spec link.`, exit 0. Same 38 as after Slice 0 and Slice 2; **no term added or lost**, and `docs/SPECS/appx/spec-033-connection_optimizer-0_0_9-terms.csv` was not touched.
- `uv run python scripts/check_trailing_commas.py --check docs/SPECS/spec-033-connection_optimizer-0_0_9.md` -> exit 0.
- `uv run python scripts/check_citations.py --check` -> `OK: 828 citations resolve (738 in 431 .py files, 90 in KANBAN.md).` Identical to R3's reading; this pass creates no `path::Symbol` citation and wraps none.
- `git diff --check` -> exit 0.
- **AST identity across every file this cycle recorded a digest for.** Instrument written for this pass: `ast.parse` -> strip every module / class / function docstring (`Pass()` where a body would empty) -> `ast.dump` (`include_attributes=False`) -> `sha256[:12]`, Python 3.14.2. **Must-see control:** inserting `_integration_control_probe = 1` above `connection.py`'s first module-level binding moves the digest `ecc47449f5ec` -> `6c158d9b8174`, so a reported identity is a measurement and not a null the instrument would report either way.

| File | worktree | `HEAD` | recorded by the cycle | match |
|---|---|---|---|---|
| `connection.py` | `ecc47449f5ec` | `ecc47449f5ec` | `ecc47449f5ec` | yes |
| `optimizer/plans.py` | `8fb1b399480f` | `8fb1b399480f` | `8fb1b399480f` | yes |
| `optimizer/walker.py` | `615fe2fe2be2` | `615fe2fe2be2` | `615fe2fe2be2` | yes |
| `optimizer/nested_fetch.py` | `302fbecdcc8d` | `302fbecdcc8d` | `302fbecdcc8d` | yes |
| `optimizer/nested_planner.py` | `3e8f913d90ae` | `3e8f913d90ae` | `3e8f913d90ae` | yes |
| `optimizer/lateral_fetch.py` | `9abf1bbf2dc2` | `9abf1bbf2dc2` | `9abf1bbf2dc2` | yes |
| `tests/optimizer/test_walker.py` | `1311b82c4ceb` | `5e9799a71eee` | `1311b82c4ceb` | yes |
| `tests/optimizer/test_nested_fetch.py` | `b459bd8740f2` | `b459bd8740f2` | `b459bd8740f2` | yes |
| `tests/optimizer/test_extension.py` | `bd92ca53429b` | `349aa5422d06` | `bd92ca53429b` | yes |
| `tests/test_relay_connection.py` | `e357f45d6f2a` | `e357f45d6f2a` | `e357f45d6f2a` | yes |
| `examples/fakeshop/test_query/test_library_api.py` | `b5918390baa8` | `b5918390baa8` | `b5918390baa8` | yes |

Eleven for eleven, under a fifth independently-written implementation. **Exactly two files differ from `HEAD` at the executable level** — R2's two failability-proved repairs — which is the whole cycle's executable footprint, and it is unchanged by the concurrent sweep landing on top of it.

- No `ruff` invocation: this pass touched no `.py` file.
- **No `pytest`.** The final gate owns the suites and follows immediately. No `--cov*` flag was used anywhere in this pass or this cycle.

### Declarations

- **Hot-path declaration:** `none`, as the build plan declares for this pass. It touches no runtime code. The cycle-wide zero-delta records are re-verified above and all hold.
- **Floor-verification scope:** `none`, as the build plan declares. This pass touches no Django / Strawberry / channels integration seam, so no floor venv was built and no floor run was performed. Where a floor fact was needed it was taken from [`BUILD.md`][build-md] `## Floor verification` (the single canonical statement: Django **5.2.16** on Python **3.10** with strawberry-graphql **0.316.0**) and never from memory; the shared `.venv` was **not** mutated and no `uv pip install` was run. The cohorts' cited `uv pip list` readings (Django 6.1, strawberry-graphql 0.324.0, channels 4.3.2, Python 3.14.2) are the shared `.venv`'s and are **not** the floor.
- **Ownership partition:** the four files this pass owns per the build plan and the dispatch — `docs/builder/bld-033-integration.md`, `docs/SPECS/spec-033-connection_optimizer-0_0_9.md`, the two cohort artifacts carrying the mis-stated counts, and `docs/builder/worker-memory/worker-1.md`. **Nothing outside it was written**; the rationale companion needed no edit and got none; no `.py` file was touched; nothing was reverted.
- **Failability position:** `None; this pass introduces no boundary.` It ships no executable byte. The analogous proof for a text pass is the citation, anchor and AST verification above, each of which fails loudly.

### Checklist audit

Every box in `### Dispatched findings checklist` is `- [x]` and each contract landed on disk: the six preconditions are each performed and recorded as a measurement above; R1, R2 and R3 are corrected in their artifacts; R4 and R5 are graded and routed with named owners; R6 is landed in the spec; R7 is recorded, unresolved, and carried forward. No box is ticked without a landed contract and none is left silently un-ticked.

### Summary

The cross-slice scan is **clean on this cycle's own work**: no duplicated helper, no inconsistent error handling, no repeated ORM pattern that should be centralized, no missing or too-broad export, two cross-file string literals both correctly rejected as consolidation candidates, and both import invariants the cycle established verified in both directions. The staged-anchor sweep is zero in shipped source under an instrument wider than the one Worker 0 used, and all eleven AST digests the cycle recorded reproduce.

The scan is **not clean on the subsystem**, and the reason is external: a concurrent session's `workstream` vocabulary sweep — 35 replacements across 11 files, landed after every cohort closed and recorded in no artifact — introduced 21 new prose citations into the Decisions this cycle had just rewritten, four of which site the marker-row contract on a Decision that does not state it, while three sites of the retired vocabulary survive un-swept. One contract, three names. It changes no executable byte and breaks none of the cycle's records, and it is not this cycle's to repair.

Two source-change opportunities are recorded and not implemented: the `to_attr` grammar's relocation into `utils/connections.py` (paired with the escalated alias deletion), and the five-exception coercion tuple, whose population this pass corrects from 15-across-2 to **16 across 3**.

### Spec changes made (Worker 1 only)

One edit. `docs/SPECS/spec-033-connection_optimizer-0_0_9.md` **160,376 -> 160,623 bytes** (+247).

1. **`### Decision 6 — Refusal arms, divergent aliases, hints, and scalar-only connections`, introduction** — one sentence appended after the granularity sentence and before the arm list: *"Source comments and test docstrings cite an arm **by its content** ("the unwindowable-child-queryset refusal arm"), never by ordinal and never by this Decision's heading text, so neither a renumbering nor a rename can silently falsify a citation."*

   **Why it lands.** Recommended by `bld-033-review-2` pass 2 (`### Notes for Worker 1` item 2), widened by its pass-3 reviewer to cover the retired **heading text** as well as the ordinal, and re-recommended by `bld-033-review-3` with the population measured at **13 sites** rather than four. Both retired spellings produced live rot inside this cycle — the ordinal (`shape 4`) at three sites, the heading noun at thirteen — and neither was visible to any gate: `scripts/check_citations.py` validates `path::Symbol` references and puts `docs/` out of scope by design, so a prose reference to a spec heading is structurally invisible to it. The spec-side convention is the only instrument available.

   **Verbatim from R3's recommendation**, deliberately. Two cohorts converged on this wording across three reviews; re-phrasing it would have been the custodian substituting taste for a measured recommendation.

   **Gates after the edit:** `check_spec_glossary.py` -> `OK: 38 terms`, exit 0 (unchanged); `check_trailing_commas.py --check` -> exit 0; `check_citations.py --check` -> `OK: 828 citations resolve`, unchanged; `git diff --check` -> exit 0. The sentence introduces no glossary term, no link, and no anchor.

**Deliberately NOT edited, and why** — recorded so a later reader does not read the absence as an oversight:

- **No cross-pointer added to Decision 4 for the marker-row contract**, though it would make all eleven marker citations resolve. The four citations that need it are a concurrent session's uncommitted comments; editing a contract document so that observed content becomes true is the wrong direction, and the spec is internally consistent as it stands.
- **The `Status:` line and the whole header** — verified current, no falsified claim. Detail under `### Spec status-line re-verification`.
- **`docs/SPECS/appx/spec-033-connection_optimizer-0_0_9-rationale.md`** — read in full; the pass found no cross-cohort contradiction in it and no record it is missing. Slice 2's 29 records cover every divergence this scan re-encountered.
- **The four cohort artifacts not carrying a mis-stated count**, and `docs/SPECS/appx/…-terms.csv`.

### Notes for Worker 1 (spec reconciliation)

**This section is the integration pass's contribution to `### Deferred work catalog`**, which [`BUILD.md`][build-md] `## Final test-run gate` places in `bld-033-final.md`. The final gate inherits it from disk, not from a report. Items are grouped by owner. Nothing below was fixed by this pass.

#### A. Escalations — recorded, unresolved, maintainer-owned

In all four the shipped code implements the spec's own words, so none is a deviation this cycle repairs.

1. **The `connection_to_attr` strictness probe answers "attribute present", not "the window was consumed"** (`bld-033-review-1b` M1). `types/resolvers.py::_check_n1` re-derives from the attribute an answer `connection.py::_build_relation_connection_resolver._resolve` computed one branch earlier and discarded, so three refusal shapes read as "served" and `"raise"` stays silent on a real per-parent query. Demonstrated with a 3-row temp test, not argued. Decision 8 states the condition as "the fast-path `to_attr` is absent on `root`", so changing it is a contract change. No data-correctness impact — only the diagnostic is silent. R1b's three resolution paths stand, and it recommends threading the resolver's already-computed boolean.
2. **`optimizer/plans.py::window_partition_for_prefetch` has zero production callers** (`bld-033-review-1a` DRY-1, the existence challenge). Six test rows plus three assertions pin it; production derives the partition from the join descriptor instead, and two of the six pin an `OptimizerError` no production path can emit while `exceptions.py` documents that raise as a live error mode. **R2's failability work is the decisive evidence and should be read with this item:** mutating `join_taxonomy.py::_partition_expr` (read by the shim *and* by production) and mutating `nested_fetch.py::attach_windowed_prefetch`'s `partition_by=` (read only by production) fail the **same two rows** — the restored shared-child test's, both times — and **neither fails any row of the shim's own six-row family**. Three resolution paths in R1a; the maintainer picks.
3. **Ten of `optimizer/walker.py`'s seventeen back-compat aliases are dead.** Independently re-derived by Worker 3 from an AST pass over all 17. The false half of the comment was repaired by R2 (a comment correction is not an existence question); the deletion is executable and remains escalated. **Pair it with item C1** — deleting the aliases removes the only non-`connection.py` readers of the two `to_attr` delegates, after which the relocation is mechanical.
4. **The nested-connection strategy seam has no owning spec, and it is the root cause of the other three rather than a fourth item.** No file under `docs/SPECS/` takes it as its subject. This is why three of this card's contracts silently inverted post-ship and why every attribution in this cycle had to be by commit rather than by card: `57cbd32a`, `9580e84e`, `51421e54`, `6912ca92`, `991d5120`, `deeb53b4`, `de2601e9`, `841e56d6`, `567cc6d0`. R1c's three resolution paths are the framing to start from, and it argues (b) — open a card for the seam and move the inverted contracts onto its spec — is what the package's "every shipped surface has an owning spec" posture implies.

#### B. The one finding this pass found and could not route inside the cycle

5. **A concurrent session's `workstream` sweep left one contract named three ways, four citations mis-sited, and three sites un-swept.** Full measurement, attribution and evidence under `### The cross-slice scan` above. Concretely, the four sites that cite the marker-row contract to a Decision that does not state it: `django_strawberry_framework/connection.py` #"With marker rows planned for the ambiguous shapes", `django_strawberry_framework/optimizer/lateral_fetch.py` #"the ambiguous-shape marker rows", `django_strawberry_framework/optimizer/plans.py` #"Marker rows (spec-033 Decision 4", `tests/optimizer/test_plans.py` #"The marker-row disambiguation". The three surviving `Workstream C` sites: `django_strawberry_framework/optimizer/lateral_fetch.py`, `django_strawberry_framework/utils/connections.py`, `tests/test_relay_connection.py`.

   **Two repairs are possible and they are not equivalent.** (a) Re-site the four citations on Decision 5 and retire the three `Workstream C` survivors — smallest surface, and it makes all eleven passages agree. (b) Add a marker-row cross-pointer to Decision 4 — one edit instead of seven, but it changes the contract document to accommodate prose, and Decision 5 already states the plan side as well as the resolve side. **Recommend (a)**, in a follow-on `.py` cohort with its own declared partition, dispatched only once the concurrent session's work has landed — a cohort cannot own files a live writer holds.

   **The transferable half:** a vocabulary retirement has no gate, and this cycle now has *two* independent data points that it rots within one pass — Slice 2's Decision 6 heading rename stranded 13 source sites, and this sweep stranded 3 while creating 4 mis-sited citations. R3's process observation is the right one and belongs in `BUILD.md`: a slice that renames a Decision heading owes a tree-wide sweep of the retired heading's **nouns**, run with the wrapped-comment-join instrument.

#### C. Source changes recorded, not implemented (outside this cycle's fence)

6. **Relocate the `to_attr` grammar to `utils/connections.py`** (`bld-033-review-1a` DRY-2, re-verified here). `connection.py:75` imports `_extend_only_projection`, `_relation_connection_to_attr` and `_relation_connection_to_attr_for_key` from `optimizer.nested_planner` and uses the latter two at the resolver's per-key probe. Decision 11 created `utils/connections.py` as "a neutral, cycle-safe home" precisely so the plan side and the resolve side share one source, and the `to_attr` grammar is as much a cursor-parity contract as the bounds are. **Note the corrected grounds:** the privacy of the imported names is *not* the argument — a cross-module private import is an established house convention here (**76 statements across 45 modules**, measured tree-wide), and on that basis `bld-033-review-1c`'s **L6** (`optimizer/extension.py:95` importing `_active_strategy`) is **closed as not-a-defect and should not be re-flagged**. The argument is placement: the shared grammar is not in the module Decision 11 created for it. No behavior change; pairs with escalation A3.
7. **One shared `_COERCION_ERRORS` constant under `utils/`.** `except (ValueError, TypeError, AttributeError, KeyError, IndexError)` — **16 occurrences across 3 files**, re-derived by this pass: `django_strawberry_framework/connection.py` 11, `django_strawberry_framework/auth/mutations.py` 4, `django_strawberry_framework/utils/sessions.py` 1. `bld-033-review-1b` reported 15 across 2 and recommended this consolidation at the integration pass; its exact-shape regex could not see the third site, which is written in the **exploded multi-line** trailing-comma layout this repo enforces. `except` accepts a tuple name, so the consolidation is mechanical. **`utils/sessions.py:152` carries a six-member superset (adds `ImportError`) and must not be folded in.** No cohort owns `utils/` or `auth/`; needs its own partition.
8. **Name `_optimizer_runtime_prefixes`**, accurately described. The **string literal** occurs twice, in one module (`optimizer/walker.py`, both inside `getattr`); `optimizer/selections.py` carries the name as a keyword argument. `bld-033-review-1a`'s Low heading says "a bare literal in two modules", which its own body does not claim. Still a real cross-seam attribute-name grammar with no named constant, and still cheap; the finding is Low on its merits, not on its heading.
9. **`connection.py::_resolve_from_window`'s keyset legs are separable** (`bld-033-review-1b` L3). 323 lines / 26 branch nodes, more than twice the file's next entry; the branch fan-out is the cross-product of four `FetchMode` shapes, the marker/probe split, and the keyset fork, and separating the keyset legs would roughly halve each half. A repair-cohort suggestion, explicitly not a defect — the shape predicates already delegate to `utils/connections.py` rather than being re-spelled.

#### D. Prose-citation exposure with no gate

10. **`tests/test_relay_connection.py` has no safe default for a bare `Decision N`, and the exposure is growing.** Measured here: `HEAD` **20 references / 16 bare**; worktree **24 / 15** after the concurrent sweep added five qualified ones. Its module docstring cites `spec-032` while its body carries live references belonging to `spec-030`, `spec-032`, `spec-033` and `spec-047`. **Every reference R3's reviewer read is correct**, so there is no live defect — this is a **deferred-work item, not a non-issue**, on three grounds: the file has no single default a reader can fall back on, the concurrent sweep has just increased the density of mixed qualified/bare references in it, and the failure mode is silent (a wrong resolution that *reads* as correct, which R3 found and closed once already in `connection.py`, where the module's declared `Spec:` line pointed at `spec-030`'s topically-adjacent Decision 6). Remedy: qualify every bare reference in that file with its `spec-0NN` prefix, in a cohort with its own partition. Not a spec edit.
11. **The "Decision 6 shape 4" class, generalised — the cycle's most transferable finding.** The instance is closed (R2 repaired it, R3 swept its vocabulary siblings 13 -> 0). The class is: **a prose reference from source into a spec Decision is invisible to every gate this repo has.** `scripts/check_citations.py` resolves `path::Symbol` references and deliberately excludes `docs/`, so it can see neither an ordinal into a Decision's item list, nor a citation by a Decision's heading text, nor a citation to a Decision that exists but does not state the claim.

    **Recommendation, in two parts, because a gate can only reach the first.** (a) A mechanical extension of `check_citations.py` — resolve every `spec-<NNN> Decision <N>` occurring in first-party `.py` against the `### Decision <N>` headings of `docs/SPECS/spec-<NNN>-*.md` — would catch a citation to a **non-existent** Decision. It is worth having, and it is cheap. (b) **It would not have caught any of this cycle's four instances**: "shape 4" was an ordinal *inside* an existing Decision, and all four marker-row mis-sitings name a Decision that exists and simply does not state the claim. Only reading catches those, which is why the durable instrument is the spec-side convention landed above — a citation that names the arm by content carries its own claim, so target and claim are checkable in one read. **Record both, and do not let (a) create the impression the class is gated.**

#### E. Doc surfaces this cycle's fence excludes — evidence recorded, none fixed

12. **`docs/TREE.md`** — script-rendered by `scripts/build_tree_md.py` from module docstrings this cycle edited, and its optimizer entries cannot describe the seven post-ship modules Decision 11 now names. The fix is a docstring-plus-regenerate change, not a doc edit, and it must land in the same change as the docstrings. *(`bld-033-review-1a` D2, `bld-033-slice-2`.)*
13. **`docs/GLOSSARY.md` `## Strictness mode`** — its `0.0.9` paragraph still lists "divergent aliases" among the shapes that fall back per parent, which the idea-#2 inversion (`57cbd32a` / `9580e84e`) retired. DB-generated: edit the glossary app's DB and re-render, never hand-edit. **The dispatch's premise is corrected and this is the only stale entry:** `docs/GLOSSARY.md`'s `## Connection-aware optimizer planning` entry is **not** stale — it already describes marker rows, the conditional count, `last: 0`, the strategy seam and keyset cursors, and Slice 2 used it as its voice reference. *(`bld-033-slice-2` `### Deferred work`.)*
14. **`KANBAN.md`** — `DONE-033-0.0.9`'s card body was never read against the corrected spec. Read-only this cycle, used only to adjudicate card ids.
15. **`docs/README.md` — no change needed, recorded so a later reader does not "fix" it.** `bld-033-review-1b` established it is *right* where the spec was wrong about keyset ordering; the spec is now corrected toward it.

---

<!-- LINK DEFINITIONS -->

<!-- Root -->

[agents]: ../../AGENTS.md

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

[artifact-md]: ARTIFACT.md
[build-md]: BUILD.md
[worker-1]: worker-1.md

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
