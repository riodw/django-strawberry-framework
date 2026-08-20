# Build: Integration consolidation — broken `#"substring"` spec citations (027)

Spec reference: `docs/SPECS/spec-027-filters-0_0_8.md` (`### Decision 4 — Upstream-primitives parity floor`, `### Decision 9 — Input-class namespace vs \`TypeRegistry\` and lifecycle`, and `### Decision 3 — Six-layer lazy-resolution pipeline` Layer 5). Cited by heading rather than by `#"substring"`: two of the three targets have a non-unique substring, which is the defect class this pass exists to repair.
Status: final-accepted

## Plan (Worker 1)

### Planning lives in `bld-integration-027.md`

This cohort has no Worker 1 planning pass of its own. The plan is the integration pass's analysis, and it is the contract this build was executed against:

- [`bld-integration-027.md`][integration] `### Citation audit: .py -> spec, every occurrence` — the population, the two broken targets, the cause (Slice 1's rationale move), and the decided replacement text. Worker 2 chose no wording here; it re-derived and applied.
- [`bld-integration-027.md`][integration] `### Staged-anchor sweep` and `### Deferred work catalog (re-derived)` item 8 — the `filters/sets.py` staged anchor routed to this cohort as a **disposition decision**, not a repair order.
- [`build-027-filters-0_0_8.md`][plan] `### Integration-pass consolidation cohort` — the verified finding table and the declared ownership partition.

**Ownership partition (single cohort, declared):** `django_strawberry_framework/filters/base.py` and `django_strawberry_framework/types/finalizer.py`, plus `django_strawberry_framework/filters/sets.py` because this pass took the retarget option on the staged anchor (see `### Implementation notes`). No other cohort ran concurrently.

Section placement follows [`ARTIFACT.md`][artifact]: `### Spec slice checklist (verbatim)` sits in `## Plan (Worker 1)`, which is where Worker 1 audits the ticks at final verification.

### DRY analysis

Not applicable and deliberately skipped, on the ground Slices 1 and 3 and the integration pass recorded: [`BUILD.md`][build] `### Package-wide helper inventory before helper planning` gates *helper planning*, and this pass proposes no helper, shared constant, validation branch, or test helper. The diff contains no executable statement.

### Spec slice checklist (verbatim)

Built from the finding table in [`build-027-filters-0_0_8.md`][plan] `### Integration-pass consolidation cohort`, one box per site plus the routed disposition decision.

Boxes 4-6 were added by Worker 1 at the first final verification and box 7 at the second; the reason for each is under the corresponding `### Spec changes made (Worker 1 only)`. Boxes 1-3 are the original plan text, unaltered.

- [x] `filters/base.py` #"spec-027 #\"accept both raw\"" (two sites) | target substring `accept both raw` -> 0 hits | the target was a rev-8 revision-history bullet Slice 1 moved to the rationale | the contract survives in Decision 4 as `Accepts both raw` (1 hit)
- [x] `types/finalizer.py::_bind_filterset_owner` #"Decision 6 #\"Partial-finalize lifecycle\"" | target substring `Partial-finalize lifecycle` -> 0 hits | the target was Decision 6's `Justification:` bullet Slice 1 moved | the contract survives as Decision 9's `Partial-finalize recovery` (2 hits, so cite `Decision 9` without a substring)
- [x] Also routed to this cohort for a disposition decision (not a repair order): `filters/sets.py` #"TODO(spec-027-filters-0_0_8 Meta.search_fields)" — a staged anchor naming **this** spec for work owned by a future card (`Meta.search_fields`, `0.1.2`).
- [x] (added by Worker 1 — partition correction 2) `filters/inputs.py` #"spec-027 Decision 3 Layer 5" above `LOOKUP_PREFIXES` | Decision 3 (spec 404-481) carries **0** occurrences of `construct_search` / `LOOKUP_PREFIXES` | Decision 2 (spec 379-403) carries **2**, both on spec line 387 | same defect, same repair as the `sets.py` twin
- [x] (added by Worker 1 — dispatched at final verification) `filters/inputs.py::_scalar_from_form_field` #"lists CharField as a recognized" -> name the class the spec's table row actually names: `CharFilter`. Exact replacement text in `### Spec changes made (Worker 1 only)`
- [x] (added by Worker 1 — dispatched at final verification) `filters/inputs.py::normalize_input_value` #"Implementation-discretion item" -> `spec-027 Decision 4`'s `normalize_input_value` contract, which Worker 1 made carry the multi-key return shape in this same pass. Exact replacement text in `### Spec changes made (Worker 1 only)`
- [x] (added by Worker 1 — partition correction 3) `filters/factories.py::FilterArgumentsFactory` #"per Implementation discretion item 5" -> `spec-027 Decision 6 subpass 4`; the cited surface is an [`ARTIFACT.md`][artifact] template section, and `grep -rn -i 'discretion' docs/SPECS/` returns **0** across the whole 145-file archive, so no spec has ever carried it. Closes the never-existent-**name** class in `django_strawberry_framework/`; it does **not** close the wrong-**card** class (see the `spec-011` item in the second `### Deferred work catalog`)

---

## Build report (Worker 2)

### Files touched

Grounded in `git status --short` and in a `diff` of each file against a pre-pass copy held outside the repo. Four hunks total, all comment / docstring text.

- `django_strawberry_framework/filters/base.py` — two sites, `_decode_and_validate_global_id` (the decode helper's docstring) and `GlobalIDFilter` (the class docstring): `spec-027 #"accept both raw"` -> `spec-027 #"Accepts both raw"`. One character changed per site; the wrap boundary is unchanged, so nothing reflowed.
- `django_strawberry_framework/types/finalizer.py` — one site, `_bind_filterset_owner`'s docstring: `spec-027 Decision 6 #"Partial-finalize lifecycle"` -> `spec-027 Decision 9`, dropping the substring. Single-line edit; the following two lines are untouched, so no citation could be wrapped by this pass.
- `django_strawberry_framework/filters/sets.py` — one site, inside `FilterSet.get_filters`: the staged anchor retargeted from `TODO(spec-027-filters-0_0_8 Meta.search_fields)` to `TODO(spec-055 Slice 1)`, with the originating contract kept as non-TODO provenance. Reasoning in `### Implementation notes`.

Every other modified path in `git status --short` is either this cycle's Slices 1-3 (**17** further `.py` files, plus the spec and the rationale — counted off `git status`, not off any artifact's stated figure, so re-derive before relying on it) or a concurrent session's baseline-dirty work listed in [`build-027-filters-0_0_8.md`][plan] `### Baseline-dirty out-of-scope files` (here: `examples/fakeshop/apps/scalars/models.py` and `examples/fakeshop/test_query/test_scalars_api.py`). None was touched by this pass, and none was reverted.

### Tests added or updated

None. This pass adds no executable statement and no contract; there is nothing new for a test to pin. The existing suite is the regression check and was run (see `### Validation run`).

### Validation run

Every command run from the repository root.

| Check | Command | Result |
|---|---|---|
| Format (scoped, never `.`) | `uv run ruff format django_strawberry_framework/filters/base.py django_strawberry_framework/types/finalizer.py django_strawberry_framework/filters/sets.py` | `3 files left unchanged`, exit 0 |
| Lint (scoped) | `uv run ruff check --fix <the same three files>` | `All checks passed!`, exit 0 |
| Source layout / ASCII-only | `uv run python scripts/check_trailing_commas.py --check <the same three files>` | exit 0 |
| Citation gate | `uv run python scripts/check_citations.py` | `OK: 740 citations resolve (665 in 422 .py files, 75 in KANBAN.md).` exit 0 — the same 740 the integration pass recorded, so this pass added and removed no `path::Symbol` citation |
| Churn classification | `git status --short` after both ruff invocations | see `### Files touched`; no unexpected churn, nothing reverted |
| Focused tests | `uv run pytest tests/filters tests/types tests/orders tests/test_registry.py tests/test_sets_mixins.py examples/fakeshop/test_query/test_library_api.py --no-cov -q` | **1465 passed in 60.57s** |

Scope choice for the focused run: `grep -rln 'from django_strawberry_framework.filters\|types.finalizer\|finalize_django_types'` over `tests/` and `examples/` names the importing surface; the six paths above cover the package mirrors of both touched modules (`tests/filters/`, `tests/types/`), the sibling family that shares their lifecycle (`tests/orders/`, `tests/test_sets_mixins.py`), the registry lifecycle that drives finalization (`tests/test_registry.py`), and the live `/graphql/` filter surface (`test_library_api.py`). No `--cov*` flag was used anywhere.

#### Comment-and-docstring-only proof (executable-token identity)

Claimed mechanically, per [`BUILD.md`][build] `## Claims are proven mechanically, never accepted on prose`. No `git checkout` / `git stash` / `git restore` / `git worktree` was used; three concurrent sessions are writing this tree.

The instrument tokenizes with `tokenize`, drops `COMMENT` / `NL` / `ENCODING` tokens and every statement-position `STRING` (i.e. docstrings), and compares the remaining `(type, string)` sequence. Script and copies live outside the repo, under this session's scratchpad.

**Two baselines, because `HEAD` is not "before this pass".** `filters/base.py`, `types/finalizer.py`, and `filters/sets.py` already carry this cycle's Slice 2 edits, so the working tree diverged from `HEAD` before this pass began. Slice 2 was also comment-only, so tokens are the one surface identical across all three states, and both comparisons were run:

| File | vs `git show HEAD:<path>` | vs the pre-pass working-tree copy | Token count |
|---|---|---|---|
| `django_strawberry_framework/filters/base.py` | IDENTICAL | IDENTICAL | 2620 |
| `django_strawberry_framework/types/finalizer.py` | IDENTICAL | IDENTICAL | 6436 |
| `django_strawberry_framework/filters/sets.py` | IDENTICAL | IDENTICAL | 8511 |

#### Re-derivation: every repaired citation resolves, and nothing else went to zero

Run **before** editing (to reproduce the dispatch brief's baselines rather than self-confirm) and again after. Both targets were re-derived against `docs/SPECS/spec-027-filters-0_0_8.md` at its current state, not taken on trust:

| Substring | Occurrences before | Occurrences after | Where |
|---|---|---|---|
| `accept both raw` | **0** | 0 (no longer cited) | — |
| `Accepts both raw` | 1 | **1** | line 530, inside Decision 4 (`### Decision 4 — Upstream-primitives parity floor`, lines 482-541) |
| `Partial-finalize lifecycle` | **0** | 0 (no longer cited) | — |
| `Partial-finalize recovery` | 2 | 2 (**not cited as a substring** — the citation names `Decision 9` only) | line 695 inside Decision 9; line 835 inside `## Edge cases and constraints` |

**Contract check, not just resolution.** Spec line 530 reads "Accepts both raw `str` and `strawberry.relay.GlobalID` objects: `isinstance(value, relay.GlobalID)` short-circuits the decode; otherwise the filter calls `relay.GlobalID.from_id(value)`" — exactly the contract both `base.py` sentences claim. Spec line 695 (Decision 9) reads "**Partial-finalize recovery.** ... A subsequent `finalize_django_types()` call re-runs the binding pass; the idempotent `(name, filterset_class)` check above lets already-materialized classes pass through cleanly" — exactly the idempotent-rebinding contract `_bind_filterset_owner`'s sentence claims.

Full-file sweep of both owned files, resolving every `#"substring"` citation whose context names `spec-027`:

| File | spec-027 substring citations | Resolving to exactly 1 before | After |
|---|---|---|---|
| `filters/base.py` | 9 | 7 | **9** |
| `types/finalizer.py` | 6 | 5 | **6** |

The three non-`spec-027` `#"substring"` citations in these files were resolved against their own targets and all hold: `filters/base.py` #"no ``{"callable", "custom"}`` literal" against `types/relay.py` (1 hit), and `types/finalizer.py`'s two `spec-018` citations against `docs/SPECS/spec-018-meta_primary-0_0_6.md` (1 hit each).

#### Re-run of the staged-anchor sweep ([`BUILD.md`][build] integration-pass precondition 6)

```shell
grep -rEn 'TODO\(spec-027|TODO-(ALPHA|BETA|STABLE)-027' . \
  --exclude-dir=.venv --exclude-dir=.git \
  --exclude=KANBAN.md --exclude=KANBAN.html --exclude=BACKLOG.md
```

**Zero hits in shipped source or tests** after this pass (it returned one, in `filters/sets.py`, before). The remaining hits are prose: `docs/SPECS/spec-031-…md` and `docs/SPECS/spec-034-…md` recording historical discharges, `docs/SPECS/spec-055-…md` quoting the anchor, and this cycle's own artifacts. Precondition 6 is now discharged on the tree rather than argued around.

### Failability proofs

None; this pass introduced no new boundary.

Discharged mechanically rather than on prose: the executable-token identity table above shows the diff contains no statement, branch, guard, comparison, or raise for the mandatory floor to select.

### Hot-path budget

Not applicable; plan declares no hot path.

### Floor verification

Not applicable; plan declares floor-verification scope none.

### Implementation notes

- **`#"Accepts both raw"` is unique case-sensitively (1) and ambiguous case-insensitively (2).** The second case-insensitive match is spec line 851, the `## Test plan` sentence "`GlobalIDFilter.clean()` accepts both raw `str` and `strawberry.relay.GlobalID` objects". Rule 27's citation form is a literal substring, so the citation is well-formed; and the ambiguity is harmless either way, because **both matches state the same contract** — a case-insensitive resolver lands on the test-plan restatement of Decision 4, not on unrelated text. The alternative that is unique both ways is the full clause through its terminating colon (`Accepts both raw \`str\` and \`strawberry.relay.GlobalID\` objects:`), which is 63 characters and would restate the citing sentence verbatim inside its own citation. Rejected as unreadable, with the collision recorded here instead.
- **The finalizer citation drops the substring rather than picking a longer one.** `Partial-finalize recovery` occurs twice, so it fails rule 27's uniqueness requirement. A longer unique variant exists (`Partial-finalize recovery.**` with the bold terminator distinguishes line 695 from line 835's `Partial-finalize recovery for the input-class namespace`), but citing punctuation is a citation pinned to formatting, which is the same fragility class the substring form already has. `Decision 9` resolves for a reader, is stable under any reword inside the decision, and is the form the dispatch verified.
- **Minimal-edit discipline over tidiness at the finalizer site.** Only the one line carrying the citation changed; the two following lines were left byte-identical. That leaves the repaired line short and leaves a pre-existing duplicated word intact (see `### Notes for Worker 3`). Re-wrapping the paragraph to fix both would have reflowed three lines of a comment this pass is otherwise not editing, which is exactly the mechanism that splits a citation across a line break — the defect class this cycle has already hit twice.
- **Staged anchor: RETARGETED, not left as-is.** `filters/sets.py` #"TODO(spec-027-filters-0_0_8 Meta.search_fields)" now reads `TODO(spec-055 Slice 1)`, with the originating contract preserved as non-TODO provenance ("The prefix map and `construct_search` landed with spec-027 Decision 3 Layer 5; spec-055 owns the consumer surface"). Four reasons, each verified rather than assumed:
  1. **`AGENTS.md` rule 26** requires a staged anchor to name "the doc and slice" that will ship the work. The old anchor named a **shipped** spec and no slice, so it satisfied neither half. `spec-027` will never ship `Meta.search_fields`.
  2. **The owner is verified, not inferred.** `docs/SPECS/spec-055-search_fields-0_1_2.md` names this exact comment and states "Slice 1 removes the TODO"; its Slice 1 checklist box is unticked; `search_fields` is still in `types/base.py` #"DEFERRED_META_KEYS"; and `docs/TREE.md` independently records `tests/filters/test_search_fields.py` as "planned by TODO-BETA-055-0.1.2".
  3. **[`BUILD.md`][build] integration-pass precondition 6 is discharged rather than argued around.** The rule requires every anchor naming this build's spec to be discharged by the build's end, and it names replacement with non-TODO `spec-<NNN>` provenance as the sanctioned form where historical context helps — which is precisely what landed. Deleting the anchor was never an option (the work has not shipped); leaving it would have closed the build with the precondition unmet and with a live marker that a `grep 'TODO(spec-055'` by its owning card cannot find.
  4. **The retargeted form matches the tree's dominant convention.** Re-derived over the full census (`grep -rn 'TODO(' --include='*.py' .` minus `.venv`, 11 anchors): **5** spell it `TODO(spec-NNN Slice N)` — `tests/test_connection.py`, `tests/test_permissions.py`, `tests/optimizer/test_extension.py`, `tests/optimizer/test_walker.py`, `tests/mutations/__init__.py`; **3** spell a bare `TODO(spec-035)` — `optimizer/walker.py` x2 and `test_library_api.py`; **2** name a non-spec owner (`TODO(unscheduled …)`, `TODO(BACKLOG …)`). Nothing else used the full-stem-with-version spelling, and nothing else omitted the slice while naming a spec: the `027` anchor was the only anchor doing both.

  **The cost, stated rather than buried:** `spec-055` line 200 quotes the anchor's old text and that quote is now wrong in two ways rather than one. It was already wrong at `HEAD` — it quotes a `card 0.1.2` suffix the real comment has never carried — and `spec-055` is another card's spec, fenced from this cycle. Routed to `### Notes for Worker 1 (spec reconciliation)` rather than fixed.

### Notes for Worker 3

- **The instrument the integration pass used undercounts this citation class, and the corrected count is larger.** Its recipe strips a leading `#` from every line so a citation wrapped inside a comment block reads as one string. That strip also eats the `#` of a citation which *begins* a line — the shape `#"consult ...` takes when a docstring wraps just before it. Stripping only a `#` followed by whitespace or end-of-line fixes it. Consequence: the integration pass measured **13** substring citations across three files; the corrected sweep finds **15 naming `spec-027` in the two owned files alone** (9 in `base.py`, 6 in `finalizer.py`). The three it could not see (`base.py` #"consult `cls._owner_definition.related_target_for(field_name)`" and two further `#"validates every element of the list independently"` sites) all resolve to exactly 1, so the corrected population contains no additional breakage — but the count in `bld-integration-027.md` is wrong, and a reviewer re-running its recipe verbatim will reproduce the blind spot. The corrected script is under this session's scratchpad; re-derive rather than trusting either number.
- **Pre-existing duplicated word at the finalizer site, deliberately not fixed.** `types/finalizer.py::_bind_filterset_owner`'s docstring reads "A second, distinct owner triggers the / the strict-equality check" across the line this pass edited and the one after it. It is present at `HEAD` and is not this pass's. Fixing it means re-wrapping a comment this pass is not otherwise editing; left for a pass whose scope covers it, and recorded here so a reviewer reading the diff hunk does not read it as newly introduced.
- No shadow file was used. `scripts/review_inspect.py` was **skipped**: this pass adds no logic to any `.py` file, and the helper's `<stem>.stripped.py` replaces every comment and string-literal token with `...`, so its output is byte-identical before and after — the same recorded skip and reason Slice 2 carried, and the executable-token identity table above is the mechanical evidence for it.

### Notes for Worker 1 (spec reconciliation)

Three items. None is a spec-027 edit; all three concern surfaces fenced from this cohort.

- **`docs/SPECS/spec-055-search_fields-0_1_2.md`, the `## …` bullet beginning "`filters/sets.py::FilterSet.get_filters` carries a".**
  - Current wording: "`filters/sets.py::FilterSet.get_filters` carries a `TODO(spec-027-filters-0_0_8 Meta.search_fields card 0.1.2)` comment at the point where prefix translation was originally imagined to wire in."
  - Recommended replacement: "`filters/sets.py::FilterSet.get_filters` carries a `TODO(spec-055 Slice 1)` comment at the point where prefix translation was originally imagined to wire in."
  - Reason: the quoted `card 0.1.2` suffix has never been in the real comment (wrong at `HEAD`), and this pass retargeted the anchor's id. `spec-055` is another card's spec; recorded, not edited.
- **`docs/TREE.md`, the `examples/fakeshop/apps/library/` block, the `filters.py` row.**
  - Current wording: "`filters.py            # FilterSet declarations for the library acceptance app (spec-021).`"
  - Recommended replacement: re-render with `scripts/build_tree_md.py`, which now emits `(spec-027)`.
  - Reason: this is the **one** live consequence of Slice 2 that no pass in this cycle recorded. Slice 2 fixed the module docstring (`examples/fakeshop/apps/library/filters.py` line 1 now reads `spec-027`, and `grep -rn 'spec-021' --include='*.py'` returns zero tree-wide), but `docs/TREE.md` is script-rendered and was not regenerated, so it is the last surviving `spec-021` reference to this card anywhere outside archived-spec prose. The integration pass's `### Deferred work catalog` item 11 read `docs/TREE.md` and reported it green; it checked the `filters/` and `tests/filters/` entries the spec's `## Doc updates` bullet names, and this row is outside that bullet's population — the population-selection trap in its cross-file form. `docs/TREE.md` is fenced this cycle and is a render, not a source, so the fix is a regenerate and belongs to whoever owns doc-wrap.
- **`docs/builder/bld-integration-027.md` `### Citation audit: .py -> spec, every occurrence`.**
  - Current wording: "`Partial-finalize recovery` occurs twice in the spec (Decision 9 and Decision 11), so it is not the unique substring rule 27 requires".
  - Recommended replacement: "… twice in the spec (Decision 9 and `## Edge cases and constraints`) …".
  - Reason: the count of 2 is right and its second **subject** is wrong. The second occurrence is spec line 835, which sits under `## Edge cases and constraints` (line 811), past `### Decision 12` (line 784); Decision 11 spans lines 710-783 and contains no occurrence. The disposition the sentence supports — drop the substring — is unaffected. A worker may not edit a prior artifact, so this is recorded rather than corrected in place.

---

## Review (Worker 3)

Every claim below was re-derived against the tree by this pass. Where a figure differs from
the build report's, the corrected figure and the command that produced it are stated. No
`git checkout` / `git stash` / `git restore` / `git worktree` was used; the read-only `HEAD`
reference is `git show HEAD:<path>` into this session's scratchpad, outside the repo.

**Baseline separation.** `git diff HEAD` on all three files carries this cycle's Slice 2 hunks
as well as this pass's. Attribution was made against
[`bld-slice-2-027-citation_and_provenance_rot.md`][slice-2] and against the `HEAD` copies:
this pass owns exactly four hunks — `base.py` two (`#"accept both raw"` -> `#"Accepts both
raw"`), `finalizer.py` one (`Decision 6 #"Partial-finalize lifecycle"` -> `Decision 9`),
`sets.py` one (the staged anchor). The `Decision 4 M6`, `round-6 Finding 1`, `finding 1` /
`finding 3`, `L566-567` / `L518-605` / `L668-678` and `round-3 loop` hunks visible in the same
`git diff HEAD` are Slice 2's and were not re-reviewed here.

### High:

None.

### Medium:

#### M1 — The retargeted anchor introduces a NEW citation that names a decision carrying none of the cited contract

`django_strawberry_framework/filters/sets.py::FilterSet.get_filters` #"The prefix map and"

The retarget's non-TODO provenance clause reads "The prefix map and `construct_search` landed
with spec-027 Decision 3 Layer 5; spec-055 owns the consumer surface." **`### Decision 3 —
Six-layer lazy-resolution pipeline` (spec lines 404-481) contains zero occurrences of
`LOOKUP_PREFIXES`, zero of `construct_search`, and zero of the substring `search` in any
case** — re-derived with `awk 'NR>=404 && NR<=481' docs/SPECS/spec-027-filters-0_0_8.md |
grep -in search` (empty) and with a whole-file `grep -n 'LOOKUP_PREFIXES\|construct_search'`,
whose hits are lines 26, 64, 102, 162, 387, 790, 801, 824, 851, 945, 946, 954, 972 — **none
inside Decision 3**. Layer 5 is the BFS-plus-module-global-materialization layer; the prefix
map is not part of it.

Why it matters: this pass exists to repair citations that do not resolve to the contract they
claim, and it lands a new one of exactly that class in shipped package source. It is also
un-catchable by the gates — `scripts/check_citations.py` resolves `path::Symbol` only and puts
`docs/` out of scope, which is the ungated seam the integration pass named.

Where the contract actually lives, both verified:

- **`### Decision 2 — Subpackage layout and public export surface`** (spec line 387, the
  `inputs.py` bullet) pins `construct_search` and `LOOKUP_PREFIXES` (the `^` / `=` / `@` / `$`
  search prefixes) as `inputs.py` contents — the "where it landed" half the clause asserts.
- **`## Edge cases and constraints`** #"`construct_search` lookup-prefix handling" (spec line
  824) pins the prefix behaviour itself.

Recommended change: repoint to `spec-027 Decision 2` (or to both Decision 2 and the Edge-cases
bullet). Do not simply drop the decision number — the clause's job is to preserve the
originating provenance the old anchor carried.

Root cause worth recording, because it is the pass's own stated method failing at one step:
`### Implementation notes` reason 2 verified the *ownership* four ways and then took this
provenance clause verbatim from `docs/SPECS/spec-055-search_fields-0_1_2.md` #"landed with
spec-027 Decision 3 Layer 5", which is itself wrong. Another document's claim is a claim, not
a measurement.

```django_strawberry_framework/filters/sets.py:1369:1373
            # TODO(spec-055 Slice 1): Meta.search_fields - wire
            # `construct_search(all_filters)` from
            # `django_strawberry_framework.filters.inputs.LOOKUP_PREFIXES` here.
            # The prefix map and `construct_search` landed with spec-027
            # Decision 3 Layer 5; spec-055 owns the consumer surface.
```

#### M2 — The substring-citation population figures mix a pre-pass and a post-pass baseline

`### Notes for Worker 3`, bullet 1, and `### Re-derivation …`'s second table.

The build report states "the corrected sweep finds **15 naming `spec-027` in the two owned
files alone** (9 in `base.py`, 6 in `finalizer.py`)", and its table's **After** column reads
`base.py` 9 / `finalizer.py` 6. The finalizer's `6` cannot be a post-pass figure: this pass
**removed** a substring from that file (`Decision 6 #"Partial-finalize lifecycle"` ->
`Decision 9`, no substring), so the population there shrank by one.

Re-derived with an independent instrument that flattens each `COMMENT` block and each `STRING`
token to one whitespace-normalized string before extracting `#"…"` (so a wrapped citation is
captured rather than lost) and normalizes backticks out of both sides before resolving:

| File | `#"…"` total | naming `spec-027` | naming something else | each resolving to exactly 1 |
|---|---|---|---|---|
| `filters/base.py` | 10 | **9** | 1 (`types/relay.py`) | yes, all 10 |
| `types/finalizer.py` | 7 | **5** | 2 (`spec-018`) | yes, all 7 |
| `filters/factories.py` | 2 | 2 | 0 | yes, both |

Cross-checked against a raw `grep -o '#"' | wc -l`: worktree `base.py` 10 / `finalizer.py` 7 /
`factories.py` 2 / `sets.py` 0, and the `HEAD` copies `base.py` 10 / `finalizer.py` **8**. The
`8 -> 7` step is this pass's removal, and it is what makes the three figures reconcile.

So: **post-pass the two owned files carry 14, not 15** (9 + 5); 15 is their **pre-pass** count
(9 + 6). And the corrected count of the population `bld-integration-027.md` actually measured
— three files, pre-pass — is **17** (9 + 2 + 6), not 15 and not 13: the build report's
correction drops `factories.py`, which the integration pass counted, so it understates the
very undercount it is correcting. The substantive finding is real and confirmed (the
integration instrument's leading-`#` strip eats the `#` of a line-initial citation, and it also
missed the second `finalizer.py` #"Bind the owner."); only its arithmetic is wrong.

Recommended change: restate as pre-pass 17 across the three files the integration pass
measured (9 `base.py` + 2 `factories.py` + 6 `finalizer.py`), post-pass 16, and correct the
`After` column for `finalizer.py` to 5-of-5. `bld-final-027.md`'s deferred-work catalog reads
these artifacts, which is exactly how a wrong number propagates.

### Low:

#### L1 — The recorded deferral of the duplicated word rests on a false premise

`django_strawberry_framework/types/finalizer.py::_bind_filterset_owner` #"Decision 9). A second"

`### Implementation notes` bullet 3 and `### Notes for Worker 3` bullet 2 defer the pre-existing
"triggers the / the strict-equality check" duplication on the ground that "fixing it means
re-wrapping a comment this pass is not otherwise editing, which is exactly the mechanism that
splits a citation across a line break."

That is not the case here. The first `the` sits at the **end of the very line this pass
edited**; deleting it is a single-line deletion on a line already in the diff and touches no
other line, so no reflow and no wrap hazard is involved. The pass also shortened that line from
~78 characters to ~30 by removing the substring, so it has already disturbed the paragraph's
fill and left a four-word line.

The duplication itself is genuinely pre-existing (confirmed byte-identical at `HEAD`,
`git show HEAD:django_strawberry_framework/types/finalizer.py` line 1226), so the *decision* to
leave it is defensible on minimal-diff grounds. **Only the stated reason is wrong**, and a
recorded rejection reason is what licenses acceptance, so it should say what is actually true:
"pre-existing at `HEAD`, out of this cohort's dispatched population" rather than "fixing it
requires a reflow."

#### L2 — A third pre-existing wrapped citation, in a file this cohort owns

`django_strawberry_framework/types/finalizer.py::_format_multi_owner_mismatch_error`

The wrap sweep this pass owes found one hit, and it is **not** this pass's:

```django_strawberry_framework/types/finalizer.py:1383:1384
    and both resolved target type names per spec-027 #"owning `FilterSet`'s
    target `DjangoType`". ``family`` is the family noun …
```

The citation is split across a line break, so every line-bounded instrument in this repo is
blind to it; my line-scoped pass reported it as a dangling `#"` with no closing quote, and only
the token-flattening pass resolved it (1 occurrence in the spec — it holds). It is byte-identical
at `HEAD` (same line numbers, verified against the `HEAD` copy), so it predates both Slice 2 and
this pass, and the sibling citation at line 1252 of the `HEAD` file spells the same substring
un-wrapped. **Disposition: no re-build action** — it is outside this cohort's dispatched
population and fixing it means the reflow L1 correctly declines. Routed to
`### Notes for Worker 1 (spec reconciliation)` for the final gate's catalog, because this is the
**third** instance of a class the cycle has now hit three times and the catalog currently
records two.

### DRY findings

None against this diff. The pass adds no executable statement (proved below), so it can
introduce no duplicated logic, no repeated literal, and no near-copy. `review_inspect.py`'s
`## Repeated string literals` section for `types/finalizer.py` (`8x Cannot finalize`, `5x
connection`, `5x FilterSet`, `3x <unresolved>`, `3x filterset_class`, `3x OrderSet`, `3x
orderset_class`) is entirely pre-existing at `HEAD` by the token-identity proof, so none of it
is chargeable to this pass. No existence challenge: the pass creates no abstraction.

### Verification I performed independently

| Claim under test | Instrument | Result |
|---|---|---|
| Executable-token identity, **all three files** (not a subset) | own `tokenize` differ: drops `COMMENT` / `NL` / `NEWLINE` / `INDENT` / `DEDENT` / `ENCODING` / `ENDMARKER` and every statement-position `STRING`, compares the `(type, string)` sequence against `git show HEAD:<path>` | **IDENTICAL** for `filters/base.py` (2158 tokens), `types/finalizer.py` (5567), `filters/sets.py` (7348). Counts differ from the build report's because my filter also drops layout tokens; the identity verdict agrees |
| `Accepts both raw` is unique in the spec | `grep -o … | wc -l` | **1**, at spec line 530, inside `### Decision 4 — Upstream-primitives parity floor` (lines 482-541). Case-insensitively 2 (line 851, the `## Test plan` restatement) — the build report's own note, and both state the same contract |
| Decision 4 carries the cited contract | read spec line 530 against both `base.py` sentences | **Holds.** "Accepts both raw `str` and `strawberry.relay.GlobalID` objects: `isinstance(value, relay.GlobalID)` short-circuits the decode; otherwise the filter calls `relay.GlobalID.from_id(value)`" is what both docstrings claim |
| `Partial-finalize recovery` occurs twice | `grep -n` | **2**: line 695 (inside Decision 9, 655-699) and line 835 (inside `## Edge cases and constraints`, 811-838). Dropping the substring is therefore required, not preferred |
| Decision 9 carries the partial-finalize lifecycle contract `_bind_filterset_owner` depends on | read Decision 9 end to end | **Holds.** Its `**Partial-finalize recovery.**` bullet states "A subsequent `finalize_django_types()` call re-runs the binding pass … while the failed type's binding completes on the retry" — the retry property the docstring's parenthetical claims |
| `TODO(spec-055 Slice 1)` names the right owner | four independent re-derivations, none taken from the build report | **All four hold**, see below |
| Staged-anchor sweep is clean in shipped source | the build report's own fenced command, re-run | **Zero hits in any `.py` file.** All 16 remaining hits are `.md` prose: `spec-031` and `spec-034` recording historical discharges, `spec-055` quoting the anchor, and this cycle's four artifacts. The `021` twin returns nothing |
| No citation wrapped by this pass | token-flattening sweep over all three files, both forms | **One wrapped `#"…"` found, pre-existing at `HEAD`** (L2 above). Zero wrapped `path::Symbol` refs; 12 / 3 / 11 such refs across the three files, all single-line |
| Public surface | `git diff HEAD -- django_strawberry_framework/__init__.py` | **Empty.** The file is not in `git status --short` at all |
| Gates | `ruff format --check`, `ruff check`, `check_trailing_commas.py --check` on the three files; `check_citations.py` repo-wide | `3 files already formatted`; `All checks passed!`; exit 0; `OK: 740 citations resolve (665 in 422 .py files, 75 in KANBAN.md)` — the same 740, so no `path::Symbol` citation was added or removed |
| Focused tests | `uv run pytest tests/filters tests/types tests/test_registry.py --no-cov -q` (my own scope, narrower than the build report's, chosen to hit both touched modules' mirrors plus the registry lifecycle that drives finalization) | **1114 passed in 11.87s.** No `--cov*` flag was used anywhere in this review |

**The `TODO(` retarget's ownership, re-derived from source rather than accepted:**

1. `docs/SPECS/spec-055-search_fields-0_1_2.md` line 204 states "Slice 1 removes the TODO",
   and line 202 states "This spec supersedes that placement ([Decision 1])".
2. That spec's `## Slice checklist` line 108 carries `- [ ] **Slice 1 — filters/search.py
   core.**` — unticked, and its scope includes `tests/filters/test_search_fields.py`.
3. `django_strawberry_framework/types/base.py` #"DEFERRED_META_KEYS" is
   `frozenset({"aggregate_class", "fields_class", "search_fields"})` — `search_fields` is
   still deferred, so the work has not shipped and the anchor legitimately stays.
4. `docs/TREE.md` line 720 records `test_search_fields.py # planned by TODO-BETA-055-0.1.2`,
   and `KANBAN.md` line 584 carries `TODO-BETA-055-0.1.2` as an **open** card with
   `docs/SPECS/spec-055-search_fields-0_1_2.md` as its spec of record.

**Verdict on the retarget: the disposition is right and the target is right; the clause
attached to it is wrong (M1).** `AGENTS.md` rule 26 requires a staged anchor to name the doc
**and slice** that will ship the work; the old anchor named a shipped spec and no slice, so it
satisfied neither half, and `spec-027` will never ship `Meta.search_fields`. Retargeting — not
deleting, not leaving — is the only option that satisfies rule 26 while keeping a live pointer
`spec-055`'s Slice 1 depends on, and the retargeted spelling matches the tree's dominant
convention. One precision note for the record: `BUILD.md` integration-pass precondition 6
discharges an anchor whose work **has landed**, which is not the case here, so what licenses
this edit is rule 26, not precondition 6 — the build report's reason 3 states it the other way
round. The sweep is nonetheless clean afterwards, so the outcome is the same.

### Failability proofs — audit and re-run

Recorded: `None; this pass introduced no new boundary.`

**Audited against the actual diff, not accepted from the plan.** The executable-token identity
above is the mechanical ground: the `(type, string)` token sequence of all three files is
byte-for-byte the `HEAD` sequence, so the diff contains no statement, branch, guard,
comparison, gate, rejection path, or `raise` for the mandatory floor to select. The record is
therefore correct as written.

**Boundaries re-run: none. Boundaries accepted on Worker 2's record: none.** The mandatory
re-run floor (`worker-3.md`, every boundary at 3-or-fewer recorded failing rows, plus every
security / data-isolation boundary) selects the empty set legally, because the diff introduces
no boundary at all — the one condition under which an empty re-run set is permitted. **The
source carve-out was not exercised**: no transient mutation was made, so there is nothing to
revert and no byte-comparison to record.

No fail-open shape landed either, by the same proof — the diff contains no expression.

### `scripts/review_inspect.py`

**Run, not skipped.** `BUILD.md` `### When to run the helper during build` fires for Worker 3
on a slice that "touches an existing `.py` file under `optimizer/` or `types/`", and
`types/finalizer.py` is such a file, so the skip carve-out was not relied on:

```shell
uv run python scripts/review_inspect.py django_strawberry_framework/types/finalizer.py --output-dir docs/shadow
```

Wrote `docs/shadow/django_strawberry_framework__types__finalizer.overview.md` and
`…stripped.py`. Django / ORM markers, control-flow hotspots and imports are all pre-existing at
`HEAD` by the token-identity proof, so each needs no per-entry justification against **this**
diff. The helper's `.stripped.py` replaces every comment and string-literal token with `...`,
so it is structurally incapable of showing a comment-text change — which is why Worker 2's
recorded skip for the other two files is **valid**, and the token-identity proof rather than
the helper is what discharges it. No shadow-file line number is cited anywhere in this review.

### Spec slice checklist walk

All three boxes are `- [x]` in the Plan, and all three contracts are in the diff:

- Box 1 (`filters/base.py`, two sites) — **landed and correct.** Both sites now read `spec-027
  #"Accepts both raw"`; the substring is unique and sits in the decision that carries the
  contract. Neither edit changed a wrap boundary.
- Box 2 (`types/finalizer.py::_bind_filterset_owner`) — **landed and correct.** The substring
  is dropped (required: 2 occurrences) and `Decision 9` carries the retry contract the
  sentence claims.
- Box 3 (`filters/sets.py` staged anchor, a disposition decision) — **landed**; the disposition
  is the right one, but the text that landed with it carries M1.

No box is silently unaddressed and none is ticked without a matching change.

### Hot-path budget

`Not applicable; plan declares no hot path.` **Audited:** the build plan's preamble declares
`Hot-path declaration: none`, and the token-identity proof means nothing executes differently
per request, per resolver, per row, per connection, or per outbound message. No number is owed
and none should be manufactured for a comment edit.

### Floor verification

`Not applicable; plan declares floor-verification scope none.` **Audited:** no executable
statement changed, so no Django / Strawberry / channels integration seam is touched. Correct as
recorded.

### Public-surface check

`git diff HEAD -- django_strawberry_framework/__init__.py` is **empty** — the file does not
appear in `git status --short` at all. `__all__` and the re-export list are unchanged. No spec
authorization is needed.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity (only when the slice touches docs, release metadata, KANBAN, or archived specs)

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces. The diff is three
`.py` files; `git status --short` shows no `.md` file this pass wrote other than this artifact.

### What looks solid

- **The two-baseline discipline.** Recognizing that `git show HEAD:` is not "before this pass"
  because Slice 2's edits are also uncommitted, and running both comparisons, is the correct
  and non-obvious move on this tree. I re-derived it independently and it holds.
- **Dropping the substring rather than lengthening it** at the finalizer site. A citation
  pinned to `Partial-finalize recovery.**` — bold terminator and all — would be pinned to
  markdown formatting, the same fragility class the pass is repairing. The reasoning is
  recorded rather than left implicit, and it is right.
- **The case-sensitivity collision is recorded instead of hidden.** `Accepts both raw` is
  unique case-sensitively and ambiguous case-insensitively; the note names the second match,
  names why the unambiguous alternative was rejected (63 characters, restating the citing
  sentence inside its own citation), and leaves the reader able to re-derive the call.
- **Indicting the integration pass's instrument.** The leading-`#` strip eating the `#` of a
  line-initial citation is a real blind spot, correctly diagnosed, with the fix named (strip
  only a `#` followed by whitespace or end-of-line). My own line-scoped pass reproduced the
  same class of blindness from the other direction — it saw the wrapped citation as an
  unterminated quote — which is the confirmation that the flatten-first design is the right one.
- **Refusing to manufacture a proof.** `### Failability proofs`, `### Hot-path budget` and
  `### Floor verification` are all discharged mechanically against the diff rather than
  asserted, and the executable-token table is what does the discharging in all three.

### Temp test verification

No temp test was written and `docs/builder/temp-tests/slice-4-027/` was not created. The diff
contains no executable statement, so there is no behaviour for a temp test to demonstrate; the
review's instruments are text and token analyses over the source and the spec, which prove more
about this diff than any test could. Nothing to promote.

### Notes for Worker 1 (spec reconciliation)

Five items. None is a `spec-027` edit; the first three concern surfaces fenced from this cohort.

1. **`docs/SPECS/spec-055-search_fields-0_1_2.md` carries the same wrong Decision attribution
   as M1**, at the bullet beginning "`filters/inputs.py::LOOKUP_PREFIXES`": it reads "landed
   with spec-027 Decision 3 Layer 5". Decision 3 contains no occurrence of `LOOKUP_PREFIXES`,
   `construct_search`, or `search`; Decision 2's `inputs.py` bullet (spec line 387) and the
   `## Edge cases and constraints` #"`construct_search` lookup-prefix handling" bullet (line
   824) are the real homes. This is the **source** of M1 — fixing M1 without recording this
   leaves the wrong attribution live in the document the next author will copy from again.
   `spec-055` is another card's spec and fenced; recorded, not edited. It compounds the
   already-routed `card 0.1.2` mis-quote on the same page.
2. **`Escalated:` `docs/TREE.md` line 859 still renders `(spec-021)` for
   `examples/fakeshop/apps/library/filters.py`.** Confirmed independently: `grep -rn 'spec-021'
   --include='*.py' .` returns **zero** tree-wide (Slice 2 fixed the module docstring), and
   `grep -n 'spec-021' docs/TREE.md` returns exactly **one** line — 859. It is the last live
   `spec-021` reference to this card anywhere outside archived-spec prose, and `spec-021` today
   names a different card (`docs/SPECS/spec-021-apps-0_0_7.md`, the `AppConfig` card), so the
   row is actively wrong rather than merely stale. `docs/TREE.md` is script-rendered and fenced
   by the maintainer's scope fence (spec files and `.py` files only), so the fix is a
   `scripts/build_tree_md.py` re-render owned by whoever owns doc-wrap. **Report to the
   maintainer; never a fix inside this cycle.** Resolution paths: (a) maintainer lifts the
   fence for a one-file regenerate, or (b) it lands in the final gate's deferred-work catalog
   as a doc-wrap obligation with the exact row named.
3. **`docs/builder/bld-integration-027.md` `### Citation audit: .py -> spec, every
   occurrence`** attributes the second `Partial-finalize recovery` to Decision 11.
   **Confirmed wrong, exactly as the build report states**: the occurrence is spec line 835,
   under `## Edge cases and constraints` (line 811); `### Decision 11` spans 710-783 and
   `### Decision 12` starts at 784, so line 835 is past both. Decision 11 carries zero
   occurrences. The disposition that sentence supports — drop the substring — is unaffected, so
   this is a record correction only. A worker may not edit a prior artifact.
4. **`Escalated:` M2's corrected figures should reach `bld-final-027.md`'s
   `### Deferred work catalog` rather than the build report's.** The catalog explicitly says
   "This list is a claim; the final gate's `### Deferred work catalog` should re-derive anything
   it acts on" — the pre-pass population across the three files the integration pass measured is
   **17**, post-pass **16**; the two owned files are **15** pre-pass and **14** post-pass.
   Resolution paths: (a) Worker 2 restates them in its re-pass build report (my preference — it
   is arithmetic, not spec context), or (b) Worker 1 records the corrected figures at final
   verification.
5. **A third wrapped citation exists (L2), so the cycle's count of two is now three.** The
   catalog should carry the class with the exemplar
   (`types/finalizer.py::_format_multi_owner_mismatch_error`, worktree lines 1383-1384) and an
   audit step, **never a count** — the class is instrument-dependent by construction, since a
   wrapped citation is invisible to every line-bounded instrument in this repo including
   `scripts/check_citations.py`. A useful follow-up card would be a flatten-first citation
   checker, which is the only instrument shape that sees this class at all.

One non-defect worth a sentence, recorded so a later pass does not re-raise it: the
`Decision 6` -> `Decision 9` retarget at `_bind_filterset_owner` is **correct** for the
sentence's own claim (partial-finalize recovery), but the idempotent-owner-binding *mechanism*
itself is pinned in `### Decision 6` subpass 1 #"Bind the owner." — which `finalizer.py`
already cites twice elsewhere. A reader chasing the mechanism from this sentence lands on the
recovery contract rather than the binding rule. Not a defect and not a re-build item; a
candidate refinement if a later pass edits that docstring for another reason.

### Process note for Worker 0 (not a finding against Worker 2)

`build-027-filters-0_0_8.md` `### Integration-pass consolidation cohort` declares the ownership
partition as two files (`filters/base.py`, `types/finalizer.py`). This pass wrote a third,
`filters/sets.py`. It did **not** do so silently — the artifact's Plan section declares the
extension and gives the reason, and the dispatch brief that spawned this review named all three
files, so Worker 0 has evidently accepted it. `BUILD.md` `### Parallel cohorts under a declared
ownership partition` nonetheless says the correction is "recorded in the plan", and the plan
still lists two. No cohort ran concurrently, so there was no collision risk and no work was
endangered. The build plan is Worker 0's file and fenced from me; recorded here so the
re-partition is not left implicit.

### Review outcome

`revision-needed`.

M1 is a wrong spec citation newly introduced into shipped package source by the pass whose
entire contract is repairing wrong spec citations, in a file this cohort owns, invisible to
every gate in the repo. It is Worker 2's to close — repointing a comment in
`filters/sets.py` needs no spec context Worker 2 lacks, so the escalation route to Worker 1 does
not apply. M2 and L1 are text corrections to the build report that ride the same re-pass at no
extra cost, and L2 carries a recorded disposition of no re-build action.

Everything else the pass was dispatched to do is verified correct and independently
re-derived: both repaired citations resolve to exactly one occurrence in the decision that
carries their contract, the anchor's new owner is right on four independent grounds, the
staged-anchor sweep is clean in shipped source, no citation was wrapped by this pass, the public
surface is untouched, and the no-executable-change claim holds by token identity for **all
three** files rather than a subset.

---

## Build report (Worker 2, pass 2)

Apply-changes pass against [`Review (Worker 3)`](#review-worker-3): M1 and M2 closed in the
tree and in this artifact, L1 fixed, L2 agreed. Two source lines changed, both comment /
docstring text. No `git checkout` / `git stash` / `git restore` / `git worktree` was used.

### Files touched

Grounded in `git status --short` (below) and in a `diff` against a reconstructed pre-pass-2
copy held outside the repo. **Two hunks, one line each.**

- `django_strawberry_framework/filters/sets.py` — `FilterSet.get_filters`, the staged anchor's
  non-TODO provenance clause: `spec-027 / Decision 3 Layer 5` -> `spec-027 / Decision 2`
  (M1). Line 1373 only; the four surrounding comment lines are byte-identical to pass 1, so
  nothing reflowed and no citation moved across a line break.
- `django_strawberry_framework/types/finalizer.py` — `_bind_filterset_owner`'s docstring, the
  duplicated word: `triggers the` / `the strict-equality check` -> `triggers` /
  `the strict-equality check` (L1). Line 1226 only — the line pass 1 already edited — so the
  deletion touches nothing new and needs no reflow.

`django_strawberry_framework/filters/base.py` was **not** touched by this pass; Worker 3
re-derived its two repairs as correct and they stand.

Every other modified path in `git status --short` is this cycle's Slices 1-3, this pass's own
artifact, or a concurrent session's baseline-dirty work. The list is byte-identical to the
status taken before this pass began: **no unexpected churn, nothing reverted**.

### Tests added or updated

None. The diff is two words of comment text; there is no contract for a test to pin.

### Validation run

Every command run from the repository root.

| Check | Command | Result |
|---|---|---|
| Format (scoped, never `.`) | `uv run ruff format django_strawberry_framework/filters/sets.py django_strawberry_framework/types/finalizer.py` | `2 files left unchanged`, exit 0 |
| Lint (scoped) | `uv run ruff check --fix <the same two files>` | `All checks passed!`, exit 0 |
| Source layout / ASCII-only | `uv run python scripts/check_trailing_commas.py --check <the same two files>` | exit 0 |
| Citation gate | `uv run python scripts/check_citations.py` | `OK: 740 citations resolve (665 in 422 .py files, 75 in KANBAN.md).` exit 0 — the same 740 as pass 1 and as the integration pass, so no `path::Symbol` citation was added or removed |
| Churn classification | `git status --short` after both ruff invocations | 24 ` M` + 14 `??` paths, **identical to the pre-pass list**; both touched files appear, nothing else changed |
| Focused tests | `uv run pytest tests/filters tests/types tests/orders tests/test_registry.py tests/test_sets_mixins.py examples/fakeshop/test_query/test_library_api.py --no-cov -q` | **1465 passed in 63.29s** (same scope and same count as pass 1) |

No `--cov*` flag was used anywhere in this pass.

#### Comment-and-docstring-only proof (executable-token identity), two baselines

The instrument tokenizes with `tokenize`, drops `COMMENT` / `NL` / `NEWLINE` / `INDENT` /
`DEDENT` / `ENCODING` / `ENDMARKER` and every statement-position `STRING` (docstrings), and
compares the remaining `(type, string)` sequence. Script and copies live outside the repo,
under this session's scratchpad.

**Baseline 1 — `git show HEAD:<path>`.** Not "before this pass": these files also carry Slice
2's and pass 1's uncommitted hunks, so this baseline proves the *cumulative* claim.

**Baseline 2 — a reconstructed pre-pass-2 copy.** Built outside the repo by reversing this
pass's two known single-line edits with `sed` on a copy of the worktree file (never a
`checkout`), then `diff`ed against the worktree: **exactly one changed line per file**, both
inside a comment / docstring, no other hunk. This is the baseline that separates pass 2's work
from pass 1's and from Slice 2's.

| File | vs `HEAD` | vs reconstructed pre-pass-2 | Tokens |
|---|---|---|---|
| `django_strawberry_framework/filters/sets.py` | IDENTICAL | IDENTICAL | 7315 |
| `django_strawberry_framework/types/finalizer.py` | IDENTICAL | IDENTICAL | 5530 |
| `django_strawberry_framework/filters/base.py` (untouched this pass) | IDENTICAL | n/a | 2154 |

Token counts differ from pass 1's table because this instrument also drops layout tokens; the
identity verdict is what carries, and it agrees with pass 1 and with Worker 3.

#### M1 — the repaired provenance clause, re-derived rather than transplanted

The clause now reads:

```django_strawberry_framework/filters/sets.py:1369:1373
            # TODO(spec-055 Slice 1): Meta.search_fields - wire
            # `construct_search(all_filters)` from
            # `django_strawberry_framework.filters.inputs.LOOKUP_PREFIXES` here.
            # The prefix map and `construct_search` landed with spec-027
            # Decision 2; spec-055 owns the consumer surface.
```

Re-derived against `docs/SPECS/spec-027-filters-0_0_8.md` at its current state, not taken from
Worker 3's finding and not from `spec-055`:

| Question | Command | Answer |
|---|---|---|
| Section bounds | `grep -n '^### Decision [23] ' docs/SPECS/spec-027-filters-0_0_8.md` | Decision 2 = 379, Decision 3 = 404, so Decision 2 spans **379-403** and Decision 3 spans **404-481** |
| Does Decision 2 carry the two symbols? | `awk 'NR>=379 && NR<=403' <spec> \| grep -c 'LOOKUP_PREFIXES'` and the same for `construct_search` | **1 and 1**, both on spec line 387, the `inputs.py` bullet |
| Does Decision 3 carry them? | `awk 'NR>=404 && NR<=481' <spec> \| grep -ci 'search'` | **0** — zero occurrences of the substring `search` in any case, which is Worker 3's finding reproduced independently |
| Is `Decision 2` an unambiguous pointer? | `grep -c '^### Decision 2 ' <spec>` | **1** |

**The cited surface carries the contract the sentence claims.** Spec line 387 (Decision 2,
`### Decision 2 — Subpackage layout and public export surface`) reads "`inputs.py` — per-module
input-class namespace, `build_input_class`, `_build_logic_fields`, `_build_input_fields`,
`construct_search`, `LOOKUP_PREFIXES` (the `^` / `=` / `@` / `$` search prefixes), …". The
sentence's claim is a **placement** claim — where the prefix map and `construct_search` landed
— and Decision 2 is the decision that places them. Verified in the tree as well:
`django_strawberry_framework/filters/inputs.py` defines `LOOKUP_PREFIXES` at line 82 and
`construct_search` at line 949, exactly where Decision 2 puts them.

**No `#"substring"` was added, deliberately.** Three reasons, in the order the rule ranks them:

1. Rule 27's substring form is valid only when the substring occurs **exactly once**. The
   natural candidates are not unique: `grep -o 'LOOKUP_PREFIXES' <spec> | wc -l` returns **16**
   and `grep -o 'construct_search' <spec> | wc -l` returns **11** (occurrences, not matching
   lines — the line-based figure is 13 for the two patterns combined and is a different
   quantity). A unique variant exists (the full `inputs.py`-bullet clause through
   its parenthesis) but is ~90 characters and would restate the citing sentence inside its own
   citation — the same trade pass 1 rejected at the `Accepts both raw` site, for the same
   reason.
2. The prompt's rule and this cycle's own precedent both prefer **no substring over a
   non-unique one**. Dropping it is what pass 1 did at `_bind_filterset_owner`, and Worker 3
   confirmed that disposition as required rather than merely preferred.
3. The comment's two preceding lines already name the module and the symbol
   (`django_strawberry_framework.filters.inputs.LOOKUP_PREFIXES`,
   `construct_search(all_filters)`), so a substring citation would pin a second copy of a fact
   the sentence already states in executable-resolvable form.

**`Decision 3 Layer 5` was not simply deleted**, per Worker 3's instruction not to drop the
decision number: the clause's job is to keep the originating `spec-027` provenance the old
`TODO(spec-027-filters-0_0_8 …)` anchor carried, and it now points at the decision that
actually carries it.

**The `## Edge cases and constraints` bullet is intentionally not cited.** Spec line 824
— the bullet #"`construct_search` lookup-prefix handling" — pins the prefix *behaviour* (`^foo` ->
`__istartswith`, etc.). The sentence makes no behavioural claim, only a placement claim, so
citing it would attach a pointer to an assertion the sentence does not make. Recorded as a
judgement rather than an omission.

**The `spec-027` / `Decision 2` wrap was left as pass 1 wrapped it.** The reference spans lines
1372-1373. It is neither a `path::Symbol` nor a `#"…"` citation, so no instrument in the repo
goes blind to it: `scripts/check_citations.py` resolves `path::Symbol` only. Pulling
`Decision 2` up onto line 1372 would edit a line this pass otherwise does not touch, for no
gate benefit, so the minimal edit was taken — the same discipline that governs L1 below.

#### M2 — the citation populations, re-derived at three named baselines

**Instrument** (new, written for this pass; it is not the pass-1 instrument and not Worker 3's):
`tokenize` the file, concatenate each *run* of consecutive `COMMENT` tokens into one string and
take each `STRING` token whole, whitespace-normalize, and only then extract `#"…"`. Flattening
before extraction is what makes a citation wrapped across a line break visible. Command:

```shell
uv run python <scratchpad>/cite_census2.py \
  django_strawberry_framework/filters/base.py \
  django_strawberry_framework/filters/factories.py \
  django_strawberry_framework/types/finalizer.py \
  django_strawberry_framework/filters/sets.py
```

**Three baselines, named rather than implied.** `HEAD` is *not* "before this pass" on this tree
— these files carry Slice 2's uncommitted edits as well.

- **`HEAD`** — `git show HEAD:<path>` into the scratchpad, four files.
- **pre-pass** (post-Slice-2, pre-Slice-4) — proved **equal to `HEAD` for this population**,
  not assumed: `git diff HEAD -- <file> | grep '#"'` over all four files returns exactly three
  changed lines, and all three are Slice 4 pass 1's own hunks (two `base.py`
  `accept both raw` -> `Accepts both raw`, one `finalizer.py` `Partial-finalize lifecycle`
  removal). **Slice 2's hunks changed no `#"…"` line in any of these files**, so the pre-pass
  population is `HEAD`'s.
- **post-pass** — the worktree now. Pass 2 changed no `#"…"` citation at all (census re-run
  after the edits: identical), so post-pass-1 and post-pass-2 are the same figure.

**Population enumerated, not asserted** — spec-027-naming `#"…"` citations, the population the
integration pass measured:

| File | pre-pass (= `HEAD`) | post-pass | The citations |
|---|---|---|---|
| `filters/base.py` | **9** | **9** | `#"Bind the owner."`, `#"rebuild ORM paths"`, `` #"consult `cls._owner_definition.related_target_for(field_name)`" ``, `#"accept both raw"` -> `#"Accepts both raw"` x2, `#"filter expects <expected> but received <actual>"`, `#"validates every element of the list independently"` x3 |
| `filters/factories.py` | **2** | **2** | `` #"Auto-generation of ``FilterSet`` from ``Meta.fields``" `` x2 |
| `types/finalizer.py` | **6** | **5** | `` #"owning `FilterSet`'s target `DjangoType`" `` x2, `#"Relation traversal under"`, `#"Bind the owner."` x2, plus `#"Partial-finalize lifecycle"` **removed by pass 1** |
| `filters/sets.py` | 0 | 0 | none — the file carries `path::Symbol` and `Decision N` refs only |

**The corrected figures, each at its stated baseline:**

- The population the integration pass actually measured — three files (`base.py`,
  `factories.py`, `finalizer.py`), pre-pass — is **17** (9 + 2 + 6). It recorded **13**. Its
  four misses: three in `base.py` (the line-initial `` #"consult `cls…` `` its leading-`#`
  strip ate, and two of the three `#"validates every element…"` sites) and one in
  `finalizer.py` (a second `#"Bind the owner."`).
- The same three files **post-pass** carry **16**.
- The two files this cohort owns (`base.py` + `finalizer.py`) carry **15 pre-pass** (9 + 6) and
  **14 post-pass** (9 + 5).
- Counting *every* `#"…"` citation rather than only the spec-027-naming ones: `base.py` 10
  (one cites `types/relay.py`), `factories.py` 2, `finalizer.py` 8 pre-pass / 7 post-pass —
  three-file totals **20 pre-pass**, **19 post-pass**.

**Explicit correction of pass 1's own sentence.** `### Notes for Worker 3` bullet 1 and the
`### Re-derivation …` second table stated "15 in the two owned files (9 `base.py` + 6
`finalizer.py`)" with `finalizer.py` `After: 6`. **Both are wrong as written**: 15 is the
**pre-pass** figure for those two files, the post-pass figure is 14, and the `After` column for
`finalizer.py` should read **5**. The 15 was also offered as the correction to the integration
pass's 13, which is a baseline substitution as well as a population substitution — 13 covered
three files and 15 covers two, so the sentence understated the very undercount it was
correcting. The substantive finding underneath it is unaffected and stands: the integration
pass's leading-`#` strip is blind to a line-initial citation, and the fix is to strip only a
`#` followed by whitespace or end-of-line.

Cross-check with a second, dumber instrument (`grep -o '#"' | wc -l`, which counts openers and
so cannot see a wrapped citation but also cannot over-flatten): worktree `base.py` 10 /
`finalizer.py` 7 / `factories.py` 2 / `sets.py` 0; `HEAD` copies `base.py` 10 /
`finalizer.py` 8. The `8 -> 7` step is pass 1's removal. Both instruments agree.

#### L1 and L2 dispositions

- **L1 — fixed, and the false reason withdrawn.** Worker 3 is right: the first `the` sat at the
  end of line 1226, the very line pass 1 edited, so removing it is a single-line deletion that
  touches nothing else. Pass 1's stated reason ("fixing it means re-wrapping a comment this
  pass is not otherwise editing") was **false for this site** — it describes L2, not L1 — and
  is withdrawn here rather than restated. The correct disposition was the cheap fix, and it
  landed.
- **L2 — agreed: no re-build action.** `types/finalizer.py::_format_multi_owner_mismatch_error`
  carries `` #"owning `FilterSet`'s / target `DjangoType`" `` split across worktree lines
  1383-1384. Confirmed pre-existing (byte-identical at `HEAD`) and confirmed to resolve (1
  occurrence in the spec), so nothing is broken. Fixing it means re-filling a five-line
  paragraph (1383-1387) that neither pass has otherwise touched — the reflow hazard L1 does
  **not** have and this site genuinely does. It is outside this cohort's dispatched population.
  Routed to Worker 1's catalog as Worker 3 filed it; nothing further from this pass.

#### Licensing correction to pass 1's own prose

`### Implementation notes` reason 3 of pass 1 stated that the `TODO(` retarget is licensed by
[`BUILD.md`][build] integration-pass precondition 6. **That is backwards.** Precondition 6
discharges an anchor whose work **has landed**; `Meta.search_fields` has not shipped
(`django_strawberry_framework/types/base.py::DEFERRED_META_KEYS` still carries it — cited by
symbol rather than by `#"DEFERRED_META_KEYS"`, which occurs 7 times in that file and so is not
the unique substring rule 27 requires), so precondition 6 does not reach this
anchor at all. What licenses the edit is **`AGENTS.md` rule 26**, which requires a staged anchor
to name the doc **and** the slice that will ship the work: the old anchor named a shipped spec
and no slice, satisfying neither half, and `spec-027` will never ship `Meta.search_fields`. The
outcome is unchanged — retarget to `TODO(spec-055 Slice 1)` — and the sweep being clean
afterwards is a *consequence*, not the licence.

### Failability proofs

None; this pass introduced no new boundary.

Discharged mechanically, not asserted: the executable-token identity table above shows the two
changed lines contain no statement, branch, guard, comparison, gate, rejection path, or
`raise` for the mandatory floor to select.

### Hot-path budget

Not applicable; plan declares no hot path.

### Floor verification

Not applicable; plan declares floor-verification scope none.

### Implementation notes

- **`Decision 2` over `Decision 2` + the Edge-cases bullet.** Worker 3 offered both. The
  sentence makes a placement claim only, so one pointer at the decision that places the symbols
  is the whole contract; a second pointer at the behaviour bullet would pin an assertion the
  sentence does not make.
- **Minimal edit over tidiness, twice.** Both hunks are one line. The `spec-027` / `Decision 2`
  line break and the ragged fill left at `_bind_filterset_owner` after the L1 deletion are both
  left alone: neither is a rule-27 citation form, no gate reads them, and re-filling either
  paragraph would touch lines outside both passes' hunks. This is the same call pass 1 made,
  now stated with the reason that actually holds (no gate benefit) rather than the one that
  does not (reflow hazard — true at L2, false at L1).
- **Every count in this report was re-derived by an instrument written for this pass**, not
  carried from pass 1, from Worker 3, or from `bld-integration-027.md`. Where a figure agrees
  with Worker 3's it is an independent agreement; where it disagrees the command is named.

### Notes for Worker 3

- **The wrong `Decision 3 Layer 5` attribution has a second live site, outside this cohort's
  writable set.** `django_strawberry_framework/filters/inputs.py` lines 80-81 read "Search-prefix
  vocabulary for the future `Meta.search_fields` card per spec-027 Decision 3 Layer 5" directly
  above `filters/inputs.py::LOOKUP_PREFIXES` (line 82). Same defect, same decision, same symbol,
  byte-identical at `HEAD`
  (`git show HEAD:django_strawberry_framework/filters/inputs.py`), so it predates this cycle.
  `inputs.py` is not in this pass's writable set, so it is **not** fixed here; routed to
  `### Notes for Worker 1 (spec reconciliation)` below.
- **Two neighbouring `Decision 3 Layer 5` citations were checked and are CORRECT — do not
  "fix" them by pattern.** `filters/inputs.py` line 91 attributes `LOOKUP_NAME_MAP` to Decision
  3 Layer 5, and Layer 5 (spec lines 416-470, bounded by `grep -n '^\*\*Layer [0-9]'`) does
  carry `LOOKUP_NAME_MAP` — spec lines 423 and 443, with the lookup table between them.
  `filters/sets.py` line 2219 attributes the per-field operator bag to Decision 3 Layer 5, and
  Layer 5 does carry the flat-field / `FieldSpec` rendering (spec lines 445-465). Only the
  `LOOKUP_PREFIXES` / `construct_search` attribution is wrong, in exactly two places.
- **Minor, artifact-only, not a tree defect:** pass 1 and this review both wrote
  `types/base.py #"DEFERRED_META_KEYS"` in artifact prose, and that substring occurs **7** times
  in the file, so the citation is not unique. Prior sections are not mine to edit; this pass
  spells it `django_strawberry_framework/types/base.py::DEFERRED_META_KEYS` instead. No `.py`
  file carries the non-unique form.
- No shadow file was used; `scripts/review_inspect.py` was skipped for the same recorded reason
  as pass 1 (its `.stripped.py` replaces every comment and string token with `...`, so it is
  structurally incapable of showing a comment-text change), and the token-identity table is the
  mechanical evidence for the skip.

### Notes for Worker 1 (spec reconciliation)

Pass 1's three items and Worker 3's five stand as filed; this pass adds one, and closes one of
its own.

- **`django_strawberry_framework/filters/inputs.py`, the comment above `LOOKUP_PREFIXES`
  (`filters/inputs.py::LOOKUP_PREFIXES`, the two lines directly above the assignment).**
  - Current wording: "`# Search-prefix vocabulary for the future \`Meta.search_fields\` card per`
    / `# spec-027 Decision 3 Layer 5; consumed by \`construct_search\` below.`"
  - Recommended replacement: "`# Search-prefix vocabulary for the future \`Meta.search_fields\` card per`
    / `# spec-027 Decision 2; consumed by \`construct_search\` below.`"
  - Reason: identical to M1. Decision 3 (spec lines 404-481) contains zero occurrences of the
    substring `search` in any case; Decision 2's `inputs.py` bullet (spec line 387) is where
    `LOOKUP_PREFIXES` and `construct_search` are placed. Pre-existing at `HEAD`, so it is not
    this cycle's rot — but it is the **third** live copy of the same false attribution
    (`sets.py` fixed here, `spec-055` already routed by pass 1 and Worker 3, this one), which
    makes it the propagation source's sibling rather than an isolated typo. `inputs.py` is
    outside this pass's writable set; recorded, not edited. A one-line fix for whoever owns the
    file next.
- **Closed by this pass, recorded so it is not re-raised:** pass 1's `### Implementation notes`
  reason 3 mis-attributed the `TODO(` retarget's licence to `BUILD.md` precondition 6 instead of
  `AGENTS.md` rule 26. Corrected in prose above under "Licensing correction to pass 1's own
  prose". No spec or tree consequence.
- **Worker 3's item 4 (`Escalated:` M2's corrected figures) is discharged here**, along
  resolution path (a): the corrected populations, their baselines, the instrument and the
  command are all in `#### M2` above, with the population enumerated rather than asserted so
  `bld-final-027.md`'s catalog can re-derive rather than copy.

---

## Build report (Worker 2, pass 3)

One repair, in the file Worker 0's partition correction 2 added to this cohort:
`django_strawberry_framework/filters/inputs.py`, the comment above `LOOKUP_PREFIXES`. It is the
sibling of M1 that pass 2 surfaced and could not fix, because `inputs.py` was outside the
writable set at the time. **One line changed, comment text.** No `git checkout` / `git stash` /
`git restore` / `git worktree` was used; three concurrent sessions are writing this tree.

### Files touched

Grounded in `git status --short` (below) and in a `diff` against a pre-pass copy held outside
the repo. **One hunk, one line.**

- `django_strawberry_framework/filters/inputs.py` — the two-line comment immediately above
  `LOOKUP_PREFIXES`: `spec-027 Decision 3 Layer 5` -> `spec-027 Decision 2`. Line 81 only. Line
  80 is byte-identical, so nothing reflowed. The reference now sits **wholly on line 81**
  (60 characters), so unlike the `sets.py` twin it is not even wrapped.

Before / after:

```django_strawberry_framework/filters/inputs.py:80:81
# Search-prefix vocabulary for the future `Meta.search_fields` card per
# spec-027 Decision 2; consumed by `construct_search` below.
```

No other file was touched by this pass. `filters/base.py`, `filters/sets.py` and
`types/finalizer.py` carry their landed pass-1 and pass-2 repairs unchanged.

### Tests added or updated

None. The diff is one clause of comment text; there is no contract for a test to pin.

### Validation run

Every command run from the repository root.

| Check | Command | Result |
|---|---|---|
| Format (scoped, never `.`) | `uv run ruff format django_strawberry_framework/filters/inputs.py` | `1 file left unchanged`, exit 0 |
| Lint (scoped) | `uv run ruff check --fix django_strawberry_framework/filters/inputs.py` | `All checks passed!`, exit 0 |
| Source layout / ASCII-only | `uv run python scripts/check_trailing_commas.py --check django_strawberry_framework/filters/inputs.py` | exit 0 |
| Citation gate | `uv run python scripts/check_citations.py` | `OK: 742 citations resolve (665 in 422 .py files, 77 in KANBAN.md).` exit 0 |
| Churn classification | `git status --short` after both ruff invocations | 27 ` M` + 14 `??`; see below |
| Focused tests | `uv run pytest tests/filters tests/types tests/orders tests/test_registry.py tests/test_sets_mixins.py examples/fakeshop/test_query/test_library_api.py --no-cov -q` | **1465 passed in 60.69s** (same scope and same count as passes 1 and 2) |

No `--cov*` flag was used anywhere in this pass.

**The citation gate's total moved and the `.py` half did not.** Passes 1 and 2 recorded
`740 (665 in 422 .py files, 75 in KANBAN.md)`; this pass reads `742 (665 in 422 .py files, 77 in
KANBAN.md)`. The `.py` figure is byte-for-byte the same triple, which is the half this pass
could affect: it added and removed no `path::Symbol` citation. The `+2` is entirely in
`KANBAN.md`, a **declared concurrent-writable generated file**
([`build-027-filters-0_0_8.md`][plan] `### Baseline-dirty out-of-scope files`), and it is
another session's. Stated rather than glossed, because "the same 740" was the phrasing passes 1
and 2 used as evidence and a later reader comparing totals would otherwise read a real
regression.

#### Churn classification: the working-tree roster changed under this pass, and not by it

`git status --short` now shows **27 ` M` + 14 `??`**, against pass 2's recorded **24 ` M` + 14
`??`**. **This is a stop-and-report item, not a revert** — nothing was reverted, and every
delta is accounted for:

- **`HEAD` moved mid-pass.** `git log --oneline -3` reads `00a1cc4a Move spec files around;` /
  `2d1f117c Move spec files around;` / `5842d23d docs(specs): complete the spec-025 record …`.
  The first two are new since this cycle's plan was written; they are a concurrent session's.
  Files pass 2 saw dirty (`docs/SPECS/spec-024-*`, `docs/builder/bld-final-025.md`,
  `build-02{4,5,6}-*.md`, the `D`-marked deletions) have left the status because that session
  committed them.
- **Three of the newly-dirty paths are exactly the plan's declared concurrent-writable set**:
  `KANBAN.md`, `KANBAN.html`, `examples/fakeshop/db.sqlite3`. The plan states this cycle plans
  no edit to any of them, so churn there is another session's by construction. Left alone.
- **`django_strawberry_framework/filters/inputs.py` is the only path this pass wrote**, proved
  below by a single-line `diff` against a pre-pass copy, not by reading the status.

**The `HEAD` move does not weaken the proof below.** Verified rather than assumed:
`git show HEAD:django_strawberry_framework/filters/inputs.py` into the scratchpad after the two
new commits landed is `cmp`-identical to the copy taken before this pass began, so the `HEAD`
baseline is the same bytes either side of the move.

#### Comment-only proof (executable-token identity), two baselines

Claimed mechanically per [`BUILD.md`][build] `## Claims are proven mechanically, never accepted
on prose`. The instrument tokenizes with `tokenize`, drops `COMMENT` / `NL` / `NEWLINE` /
`INDENT` / `DEDENT` / `ENCODING` / `ENDMARKER` and every statement-position `STRING`
(docstrings), and compares the remaining `(type, string)` sequence. Script and copies live
outside the repo, under this session's scratchpad.

**`HEAD` is not "before this pass".** `filters/inputs.py` already carries this cycle's **Slice
2** edits — `git diff` against the `HEAD` copy shows **7** hunks predating this pass (`Decision
4 M1` -> `Decision 4`, `Decision 4 M5 (line 591)` -> `Decision 4`, `Decision-4 M1` ->
`spec-027 Decision 4`, `spec-027 line 595` -> `spec-027 Decision 4`, `spec-027 L603` ->
`spec-027 Decision 4`, `Decision 4 line 594` -> `Decision 4`, and the `Finding 2` provenance
removal). So both baselines were taken and both were run.

| Baseline | Command | Result |
|---|---|---|
| 1 — `HEAD` (cumulative: Slice 2 + this pass) | `git show HEAD:django_strawberry_framework/filters/inputs.py` into the scratchpad | **IDENTICAL**, 2759 exec tokens each side |
| 2 — pre-pass working-tree copy (this pass alone) | `cp` of the worktree file taken before the edit | **IDENTICAL**, 2759 exec tokens each side |

`diff <pre-pass copy> <worktree>` prints **exactly one changed line** (line 81), inside a
comment. The target site is byte-identical at `HEAD`, so the defect is **pre-existing rot, not
this cycle's** — Slice 2 rewrote six other citations in this file and left this one.

#### Re-derivation: the repaired citation resolves to the surface that carries the contract

Re-derived from the spec directly, **not** taken from Worker 0's dispatch brief, from Worker 3's
M1, or from the `sets.py` twin. Every figure below was re-run **after** the concurrent `HEAD`
move, so it reflects the spec as it stands now.

| Question | Command | Answer |
|---|---|---|
| Section bounds | `grep -n '^### Decision [234] ' <spec>` | Decision 2 = 379, Decision 3 = 404, Decision 4 = 482 -> **D2 spans 379-403, D3 spans 404-481** |
| Does Decision 3 carry the cited symbols? | `awk 'NR>=404 && NR<=481' <spec> \| grep -o '<sym>' \| wc -l` | `construct_search` **0**, `LOOKUP_PREFIXES` **0**, and `grep -oi 'search'` **0** — the substring does not occur in Decision 3 in any case |
| Does Decision 2 carry them? | same `awk` over 379-403 | `construct_search` **1**, `LOOKUP_PREFIXES` **1** — both on spec line 387, the `inputs.py` bullet |
| Is `Decision 2` an unambiguous pointer? | `grep -c '^### Decision 2 ' <spec>` | **1** |

**The cited surface carries the contract the comment claims.** Spec line 387 (Decision 2,
`### Decision 2 — Subpackage layout and public export surface`) reads "`inputs.py` — per-module
input-class namespace, `build_input_class`, `_build_logic_fields`, `_build_input_fields`,
`construct_search`, `LOOKUP_PREFIXES` (the `^` / `=` / `@` / `$` search prefixes), …". The
comment's claim is a **placement** claim — this vocabulary lives here, for a future card — and
Decision 2 is the decision that places it. Confirmed in the tree too: `LOOKUP_PREFIXES` is
defined at `filters/inputs.py` line 82 and `construct_search` at line 949, exactly where
Decision 2 puts them.

**No `#"substring"` was added**, for the reason pass 2 recorded at the twin site and re-derived
here: `grep -o 'LOOKUP_PREFIXES' <spec> | wc -l` returns **16** and
`grep -o 'construct_search' <spec> | wc -l` returns **11** (occurrences, not matching lines), so
neither natural candidate is the unique substring rule 27 requires. A unique variant exists (the
full `inputs.py`-bullet clause) but is ~90 characters and would restate the citing comment
inside its own citation.

**Wording matched to the `sets.py` twin, deliberately.** `filters/sets.py::FilterSet.get_filters`
now reads "The prefix map and `construct_search` landed with spec-027 / Decision 2; spec-055
owns the consumer surface"; this site reads "… card per / spec-027 Decision 2; consumed by
`construct_search` below". Both cite `spec-027 Decision 2`, both without a substring, so the two
live copies of the same attribution now agree. Only the surrounding clause differs, because the
two sentences make different claims (the anchor's is provenance-for-a-future-card, this one's is
vocabulary-placement).

#### The two correct neighbours: re-confirmed, and left alone

Pass 2's `### Notes for Worker 3` recorded both as correct. Re-derived independently here, and
**both still hold**; neither was touched.

| Site | Attribution | Layer-5 bounds re-derived | Verdict |
|---|---|---|---|
| `filters/inputs.py` line 90-91, above `LOOKUP_NAME_MAP` | `spec-027 Decision 3 Layer 5` | Layer 5 = spec **416-470** (`grep -n '^\*\*Layer [0-9]'`: L5 at 416, L6 at 471) | **CORRECT** — `LOOKUP_NAME_MAP` occurs **3** times inside Layer 5 (the constant's introduction, the lookup table, and the factory/normalizer agreement clause) |
| `filters/sets.py` line 2219, the per-field operator bag | `spec-027 Decision 3 Layer 5 (per-field operator bag)` | same bounds | **CORRECT** — Layer 5 carries the flat-field / `FieldSpec` rendering (`Meta.fields = {"galaxy__name": …}` renders as the flat `galaxyName: { exact: … }`), which is the operator-bag shape the comment describes. `sets.py` is not in this pass's writable set and was not opened for edit |

After the repair, `grep -n 'Decision 3 Layer 5' django_strawberry_framework/filters/inputs.py`
returns **exactly one** hit — line 91, the correct one.

#### Full scan of `filters/inputs.py` for further unresolving attributions

The pass's second obligation. Population enumerated rather than asserted: every `Decision` and
every `spec-NNN` reference in the file, each read against the spec section it names.

**16 spec references, 14 `Decision N` attributions.** Resolving:

| Ref (line) | Attribution | Verdict |
|---|---|---|
| 5, 61, 148, 652, 966, 976 (6) | Decision 9 (`### Decision 9 — Input-class namespace vs \`TypeRegistry\` and lifecycle`, spec 655-699) | **RESOLVE.** D9 carries module-global materialization via `setattr(sys.modules[…])`, the `_materialized_names` ledger, `(name, filterset_class)` idempotency, the distinct-class `ConfigurationError` raise, and the `clear_filter_input_namespace()` lifecycle — every claim the six sites make |
| 294, 411, 461, 592, 688 (5) | Decision 4 (spec 482-541) | **RESOLVE.** The conversion table's rows carry each cited contract: `ChoiceFilter` -> `ConfigurationError` for a non-`Choices` source (294); the table itself (411); "if the form field is unknown, raises `ConfigurationError` naming the filter and method" (461); `GlobalIDFilter` validating the decoded `type_name` against `owner_definition.related_target_for(field_name).graphql_type_name` before any queryset clause (592); `RangeWidget.value_from_datadict` reading positional `name_0` / `name_1` "NOT named `_from` / `_to` keys" (688) |
| 81 (1) | Decision 3 Layer 5 -> **Decision 2** | **REPAIRED THIS PASS** |
| 91 (1) | Decision 3 Layer 5 | **RESOLVES** — the correct neighbour above |
| 424, 657 (2) | bare `spec-027` ("forward path", "spec-027 assumed a duplicate-type error would surface") | **No decision named**, so nothing to mis-resolve. Both are prose about a spec-level assumption rather than a citation; out of this pass's population |
| 362 (1) | `spec-051 C3` | Different card's spec; out of this cohort's population and not re-derived here |

**Two attributions do not fully resolve. Neither was repaired, and here is why each.**

1. **Line 260 — "the conversion table in spec-027 Decision 4 lists CharField as a recognized
   shape".** `grep -c 'CharField'` over Decision 4 (482-541) returns **0**; the whole spec
   carries `CharField` exactly once, at line 853, in an unrelated `test_definition_relations.py`
   aside about `Book.circulation_status`. What the table's first row actually names is
   **`CharFilter`** — "`CharFilter` / scalar `*Filter` with `lookup_expr` other than `in` /
   `range` | the scalar Python type … derived from the model field's `to_python`". The
   **attribution resolves** (Decision 4 is the decision that carries the conversion table, and
   that table does cover this branch's `-> str` mapping); what is wrong is one letter inside the
   sentence, and the sentence is genuinely about a `forms.CharField` — a form field, a different
   object from the spec's `CharFilter`. Repairing it means deciding whether the comment should
   say `CharFilter` (matching the spec) or keep `CharField` and stop claiming the table names it
   (matching the code). That is a wording judgement, not the mechanical retarget this pass was
   dispatched for, so it is **reported, not repaired**, and routed below. Note it is *not*
   pre-existing untouched text: Slice 2 edited this very line (`Decision 4 M1` -> `Decision 4`)
   and left the `CharField` word standing.
2. **Line 522 — "Per the spec-027 Implementation-discretion item, the multi-key return shape
   …".** `grep -in 'discretion'` over the whole spec returns **0 hits**; so do `multi-key` and
   `sentinel`. `### Implementation discretion items` is a section of
   [`ARTIFACT.md`][artifact]'s **build-artifact** template — a Worker 1 plan section — not a
   spec section, and this cycle's per-slice artifacts are deleted at the next build's pre-flight.
   The citation therefore names a surface that does not exist in the spec and, if it ever named
   an artifact, names one that will not survive. Byte-identical at `HEAD` (Slice 2 did not touch
   this line). **Reported, not repaired**: the replacement is not derivable from the spec — there
   is no passage to repoint it at — so the honest fixes are either to drop the citation and keep
   the design note, or for Worker 1 to add the clause to the spec. Both are decisions above this
   pass's dispatch.

### Failability proofs

None; this pass introduced no new boundary.

Discharged mechanically rather than on prose: the executable-token identity table above shows
the one changed line contains no statement, branch, guard, comparison, gate, rejection path, or
`raise` for the mandatory floor to select.

### Hot-path budget

Not applicable; plan declares no hot path.

### Floor verification

Not applicable; plan declares floor-verification scope none.

### Implementation notes

- **Re-derived, not accepted.** Worker 0's partition correction 2 states D3 = 404-481 with 0
  hits and D2 = 379-403 with 2. Both were re-run from the spec here, after the concurrent `HEAD`
  move, and both reproduce exactly. Stated as an independent agreement rather than a citation of
  the brief — a dispatch brief is a claim the subagent re-derives.
- **The repair is a retarget, not a deletion.** `Decision 3 Layer 5` was replaced by
  `Decision 2`, not dropped: the comment's job is to tell a future `Meta.search_fields` reader
  where this vocabulary was placed and by which decision, and stripping the pointer would lose
  that while leaving the sentence's "per" dangling.
- **Minimal edit.** One line. Line 80 was left byte-identical even though the repaired line is
  now 11 characters shorter and the two lines would re-fill onto one — re-filling would edit a
  line this pass does not otherwise touch, which is the mechanism that splits a citation across
  a line break.
- **`Layer 5` was NOT swept out of the file by pattern.** The instruction and pass 2's own
  finding both say the two neighbouring `Layer 5` attributions are correct; both were
  re-verified against the re-derived Layer-5 bounds (416-470) before being left alone. A
  pattern fix here would have broken two correct citations to repair one wrong one.

### Notes for Worker 3

- **What to re-review in this pass: one line.** Everything else in the artifact above it is
  passes 1 and 2, already reviewed. The re-review covers all three passes together, so the
  landed state of `base.py` (2 hunks), `finalizer.py` (2 hunks), `sets.py` (2 hunks) and now
  `inputs.py` (1 hunk) is the whole cohort's diff.
- **The citation-gate total is 742, not the 740 passes 1 and 2 recorded, and the `.py` triple is
  unchanged.** Do not read the delta as this pass's; it is `KANBAN.md` 75 -> 77, a declared
  concurrent-writable generated file. The command and both readings are in `### Validation run`.
- **The working-tree roster grew from 24 ` M` to 27 ` M` and `HEAD` moved by two commits during
  this pass.** Classified in `### Validation run`, nothing reverted. If you re-run
  `git status --short` you will get a third roster; classify against the concurrent-writable
  list in the plan rather than against any number written down in this artifact.
- **Two reported-not-repaired attributions** are in the full-scan section above (line 260's
  `CharField`, line 522's `Implementation-discretion item`). Both are stated with the command
  that establishes them; neither is a repair this pass was dispatched to make, and both are
  routed to Worker 1 below. If you disagree that they are out of dispatch, they are one-line
  fixes and this pass can take them on a re-pass.
- No shadow file was used. `scripts/review_inspect.py` was **skipped**, same recorded reason as
  passes 1 and 2: its `<stem>.stripped.py` replaces every comment and string-literal token with
  `...`, so it is structurally incapable of showing a comment-text change, and the
  executable-token identity table is the mechanical evidence for the skip.

### Notes for Worker 1 (spec reconciliation)

Passes 1 and 2's items and Worker 3's stand as filed. This pass closes one of them and adds two.

- **Closed by this pass:** pass 2's `### Notes for Worker 1` item routing
  `filters/inputs.py`'s `LOOKUP_PREFIXES` comment to "whoever owns the file next" is
  **discharged** — Worker 0 extended the partition to `inputs.py` and the repair landed here
  (`spec-027 Decision 3 Layer 5` -> `spec-027 Decision 2`). Recorded so `bld-final-027.md`'s
  deferred-work catalog does not carry it forward as open. With `sets.py` (pass 2) and this
  site, **both live copies of the false `Decision 3 Layer 5` attribution are now fixed**; the
  third copy, in `docs/SPECS/spec-055-search_fields-0_1_2.md`, remains routed and unfixed
  (another card's spec, fenced from this cycle).
- **`django_strawberry_framework/filters/inputs.py`, `_form_field_to_scalar`, the comment above
  the `forms.CharField` branch (line 260).**
  - Current wording: "`# Both ``CharField`` and the catch-all map to ``str``. The explicit`
    / `# ``CharField`` branch is kept for documentation: the conversion` /
    `# table in spec-027 Decision 4 lists CharField as a recognized` /
    `# shape, …`"
  - Recommended replacement: "`# table in spec-027 Decision 4 lists ``CharFilter`` as a
    recognized` / `# shape, …`" — i.e. name the class the spec's table row actually names.
  - Reason: `CharField` occurs **0** times in Decision 4 (spec 482-541); the table's first row
    reads "`CharFilter` / scalar `*Filter` with `lookup_expr` other than `in` / `range`". The
    Decision attribution is right and the class name in the sentence is not. If Worker 1 would
    rather the comment keep saying `CharField` (it is describing a `forms.CharField` branch),
    then the fix is to stop claiming the spec table names it — either wording is a one-line
    edit, but which one is a judgement this pass did not make unilaterally.
- **`django_strawberry_framework/filters/inputs.py`, `normalize_input_value`'s docstring (line
  522).**
  - Current wording: "`Per the spec-027 Implementation-discretion item, the` / `multi-key
    return shape lets the ``_normalize_input`` caller merge` / `the patch without inventing a
    sentinel-pair object.`"
  - Recommended replacement: either (a) drop the citation and keep the design note — "`The
    multi-key return shape lets the ``_normalize_input`` caller merge the patch without
    inventing a sentinel-pair object.`" — or (b) Worker 1 adds the clause to the spec (Decision
    4's converter/normalizer surface is where it would sit) and the comment cites that.
  - Reason: `grep -in 'discretion'` over `docs/SPECS/spec-027-filters-0_0_8.md` returns **0**;
    so do `multi-key` and `sentinel`. `### Implementation discretion items` is a section of
    [`ARTIFACT.md`][artifact]'s build-artifact template — Worker 1's *plan* section — not a spec
    section, and per-cycle `bld-*.md` artifacts are deleted at the next build's pre-flight, so
    even reading it as an artifact citation it points at something that will not exist. Which of
    (a) and (b) is right depends on whether the multi-key return shape is a contract the spec
    should carry, which is the custodian's call. Pre-existing at `HEAD`; Slice 2 did not touch
    this line.

## Review (Worker 3, pass 2)

Re-review of passes 1, 2 and 3 as one accumulated diff. Every figure below was re-derived by
this pass with its own instrument; where it agrees with a build report it is an independent
agreement, and the command is named either way. No `git checkout` / `git stash` / `git restore`
/ `git worktree` was used.

**Baseline used, and why it is sound despite the mid-pass `HEAD` move.**
`git show HEAD:<path>` at `00a1cc4a` into this session's scratchpad, for all four files. The
move is verified harmless rather than assumed so: `git log --stat 5842d23d..HEAD` shows
`2d1f117c` and `00a1cc4a` touch **only** `docs/SPECS/spec-024-*`, `docs/builder/build-024/025-*`,
`bld-final-024/025`, `bld-slice-*-025-*` and `docs/builder/DONE/` — no `.py` file and not
`spec-027`. Directly `cmp`-proved as well: the `HEAD` copies I took **before** the move (during
pass 1) are byte-identical to the copies taken after it for `base.py`, `sets.py` and
`finalizer.py`. So `HEAD` is the same bytes either side, spec line numbers are stable, and
Worker 2's claim reproduces.

`HEAD` is still not "before this pass" — all four files carry this cycle's uncommitted Slice 2
hunks. Attribution: `git diff HEAD --` per file, hunks matched against
[`bld-slice-2-027-citation_and_provenance_rot.md`][slice-2]. **This cohort owns exactly seven
hunks** across the three passes: `base.py` two (`#"accept both raw"` -> `#"Accepts both raw"`,
both riding inside larger Slice-2 hunks), `finalizer.py` two (`Decision 6 #"Partial-finalize
lifecycle"` -> `Decision 9`; the duplicated `the` deletion — both on line 1226, so one hunk in
the diff), `sets.py` two (the staged anchor, then `Decision 3 Layer 5` -> `Decision 2`),
`inputs.py` one (line 81, `Decision 3 Layer 5` -> `Decision 2`).

### High:

None.

### Medium:

None. Both pass-1 Mediums are closed; see `#### M1 — closed` and `#### M2 — closed` below.

#### M1 — closed

Re-derived from the spec directly, not from Worker 2's report and not from my own pass-1 finding:

| Question | Command | Answer |
|---|---|---|
| Decision bounds | `grep -n '^### Decision [0-9]' <spec>` | D1 373, **D2 379**, **D3 404**, D4 482 -> D2 spans **379-403**, D3 spans **404-481** |
| Does D2 carry the symbols? | `awk 'NR>=379 && NR<=403' <spec> \| grep -c '<sym>'` | `LOOKUP_PREFIXES` **1**, `construct_search` **1**, both on spec line 387 |
| Does D3 carry them? | `awk 'NR>=404 && NR<=481' <spec> \| grep -ci 'search'` | **0** — the substring does not occur in D3 in any case |
| Is `Decision 2` unambiguous? | `grep -c '^### Decision 2 ' <spec>` | **1** |

**The repaired citation resolves, and Decision 2 genuinely carries the placement claim.** Spec
line 387 (`### Decision 2 — Subpackage layout and public export surface`) enumerates `inputs.py`
contents and names `construct_search` and `` `LOOKUP_PREFIXES` (the `^` / `=` / `@` / `$` search
prefixes) `` inside that enumeration. It carries more than the placement: it also spells the
four-symbol vocabulary, which is byte-for-byte the four keys of `filters/inputs.py`'s
`LOOKUP_PREFIXES` dict. So both repaired sentences are supported.

**The sentence does make only a placement claim, so declining the Edge-cases bullet is right.**
`filters/sets.py::FilterSet.get_filters` now reads "The prefix map and `construct_search` landed
with spec-027 / Decision 2; spec-055 owns the consumer surface." Its two assertions are *where
the symbols landed* and *who owns the consumer surface*; neither is a claim about what a prefix
does. Spec line 824's `` #"`construct_search` lookup-prefix handling" `` bullet pins prefix
behaviour (`^foo` -> `__istartswith`), which the sentence never asserts, so citing it would
attach a pointer to an assertion that is not being made. Worker 2's judgement is correct and I
withdraw the "(or to both)" half of my pass-1 recommendation.

**Adding no `#"substring"` is correct.** Re-derived: `grep -o 'LOOKUP_PREFIXES' <spec> | wc -l`
= **16**, `grep -o 'construct_search' <spec> | wc -l` = **11**. Neither is the unique substring
rule 27 requires, and rule 27 admits the decision-only form.

**The sibling landed and is the same repair.** `filters/inputs.py` lines 80-81 now read
"Search-prefix vocabulary for the future `Meta.search_fields` card per / spec-027 Decision 2;
consumed by `construct_search` below." `grep -n 'Decision 3 Layer 5'
django_strawberry_framework/filters/inputs.py` returns **exactly one** hit — line 91, the
correct `LOOKUP_NAME_MAP` neighbour.

**The two neighbours Worker 2 refused to sweep by pattern are correct; I re-derived both.**
Layer bounds from `grep -n '^\*\*Layer [0-9]' <spec>`: Layer 5 = **416-470** (Layer 6 opens at
471). `LOOKUP_NAME_MAP` occurs **3** times inside 416-470, so `inputs.py` line 91 holds; Layer 5
line 445 carries the `Meta.fields = {"galaxy__name": …}` -> flat `galaxyName: { exact: … }`
rendering plus the `FieldSpec` substrate, which is the operator-bag shape `sets.py` line 2219
describes, so that one holds too. Refusing the pattern fix was the right call: it would have
broken two correct citations to repair one wrong one.

#### M2 — closed

Re-derived with my own instrument (not pass 1's, not Worker 2's): `tokenize` the file, join each
**run** of consecutive `COMMENT` tokens into one string and take each `STRING` token whole,
whitespace-normalize, then extract `#"…"` — flattening before extraction is what makes a wrapped
citation visible. Citations classified `spec-027` by a 120-character preceding context window.
Run against the worktree and against `git show HEAD:<path>` copies.

| File | pre-pass (= `HEAD`) spec-027 | post-pass spec-027 | total `#"…"` HEAD -> worktree |
|---|---|---|---|
| `filters/base.py` | **9** | **9** | 10 -> 10 |
| `filters/factories.py` | **2** | **2** | 2 -> 2 |
| `types/finalizer.py` | **6** | **5** | 8 -> 7 |
| `filters/sets.py` | 0 | 0 | 0 -> 0 |
| `filters/inputs.py` | 0 | 0 | 0 -> 0 |

**My figures, at my stated baseline:** the three files the integration pass measured carry
**17 pre-pass** (9 + 2 + 6) and **16 post-pass** (9 + 2 + 5); the two files the cohort originally
owned carry **15 pre-pass** and **14 post-pass**; `finalizer.py`'s `After` is **5**. Every one of
Worker 2's restated figures reproduces exactly. The integration pass's 13 remains the undercount,
and the four misses Worker 2 enumerated are visible in my own listing (the line-initial
`` #"consult `cls._owner_definition…` ``, two of the three `#"validates every element…"` sites,
and the second `#"Bind the owner."`).

**`HEAD == pre-pass` is proved here, not accepted.** `git diff HEAD -- <file> | grep '#"'` across
all four files returns exactly **three** changed source lines (two `base.py` `accept both raw` ->
`Accepts both raw`, one `finalizer.py` `Partial-finalize lifecycle` removal), and all three are
pass 1's own hunks. `sets.py` and `inputs.py` carry no `#"…"` citation at all. So no Slice-2 hunk
touched this population and the `HEAD` census *is* the pre-pass census.

### Low:

#### N1 — `filters/inputs.py::_scalar_from_form_field`, "Decision 4 lists CharField": confirmed, deferral accepted, but the escalation route as written cannot execute

`django_strawberry_framework/filters/inputs.py::_scalar_from_form_field` #"lists CharField as a recognized"

Confirmed exactly as pass 3 reports. `awk 'NR>=482 && NR<=541' <spec> | grep -c 'CharField'` =
**0**; the whole spec carries `CharField` once, at line 853, inside a
`test_definition_relations.py` aside about `Book.circulation_status`. The conversion table's
first row (spec line 518) names **`CharFilter`**. The Decision attribution resolves — Decision 4
is the decision that carries the conversion table, and that row's "the scalar Python type …
derived from the model field's `to_python`" does cover this branch's `-> str` mapping — so what
is false is one word inside the sentence, not the pointer.

**The recorded deferral reason holds.** Two shapes are genuinely available: name `CharFilter`
(true to the table, but drops a `CharFilter` into the middle of a sentence otherwise discussing
the `forms.CharField` branch it documents), or keep `CharField` and stop claiming the table names
it. Both are defensible prose; picking between them is a wording call, and pass 3 wrote out both
rather than choosing unilaterally. I accept the deferral.

**What I do not accept is where it was routed.** Worker 1 reads source **read-only**
([`BUILD.md`][build] `## Required reading per worker`), so a "recommended replacement" for a
`.py` comment filed under `### Notes for Worker 1` has no executor: Worker 1 cannot apply it, and
the only route to the tree is a Worker 2 pass. Escalated below with the two resolution paths that
actually terminate.

Severity Low, not Medium: it is inherited rot, outside the dispatched population of three sites,
and the pointer resolves. It is **not** the M1 class — M1 was a false attribution this pass
itself introduced.

```django_strawberry_framework/filters/inputs.py:258:262
    # Both ``CharField`` and the catch-all map to ``str``. The explicit
    # ``CharField`` branch is kept for documentation: the conversion
    # table in spec-027 Decision 4 lists CharField as a recognized
    # shape, and a future reader who inspects this function should see
    # that the mapping is intentional, not an accidental fallthrough.
```

#### N2 — `filters/inputs.py::normalize_input_value`, "the spec-027 Implementation-discretion item": confirmed, and the deferral reason is sound

`django_strawberry_framework/filters/inputs.py::normalize_input_value` #"Implementation-discretion item"

Confirmed and slightly stronger than pass 3 states it. `grep -in 'discretion'` over
`docs/SPECS/spec-027-filters-0_0_8.md` returns **0**; so do `multi-key` and `sentinel`.
`### Implementation discretion items` is a section of [`ARTIFACT.md`][artifact]'s **build-artifact
template** — a Worker 1 *plan* section inside a `bld-*.md` file — so the citation names a surface
the spec has never carried, and the only surface with that name is per-cycle and deleted at the
next build's pre-flight. Byte-identical at `HEAD`; Slice 2 did not touch this line.

The dispatch is right that this is the stronger defect of the two: N1 mis-words a claim about a
real cited surface, this one cites a surface that does not exist. But **strength of defect and
availability of the repair are different axes**, and on the second axis this one is worse for
Worker 2, not better. The two honest fixes are (a) drop the citation and keep the design note, or
(b) Worker 1 adds the clause to the spec and the comment cites it. (b) is a spec edit, which only
Worker 1 may make; taking (a) unilaterally destroys a pointer whose target Worker 1 may
legitimately want to create. So the recorded reason — that the choice is above this pass's
dispatch — is **sound**, and I accept it on stronger grounds than the report claims for it.

One argument for (a) that neither pass raised, recorded so Worker 1 can weigh it: `AGENTS.md`
bans build-process provenance from code comments and keeps spec **Decision** pointers. A pointer
at a build-artifact template section is the banned class and is not the kept class, which puts
(a) ahead on the standing rule unless Worker 1 wants the contract in the spec.

Same routing correction as N1: filed under `### Notes for Worker 1` with no executor. Escalated
below.

```django_strawberry_framework/filters/inputs.py:522:524
    Per the spec-027 Implementation-discretion item, the
    multi-key return shape lets the ``_normalize_input`` caller merge
    the patch without inventing a sentinel-pair object.
```

#### L1 — closed

`types/finalizer.py::_bind_filterset_owner` now reads "… per spec-027 / Decision 9). A second,
distinct owner triggers / the strict-equality check (``_check_filterset_owner_axes``) …". The
duplicated `the` is gone, the sentence is grammatical, and the fix is confined to line 1226 —
the line pass 1 had already edited. The following line is a **context** line in `git diff HEAD`,
so it is byte-identical to `HEAD`: nothing reflowed, and no citation moved across a line break.
The false deferral reason was withdrawn in pass 2's prose rather than restated, which is the
disposition I asked for.

#### L2 — still routed, not dropped

`types/finalizer.py::_format_multi_owner_mismatch_error` still carries `` #"owning `FilterSet`'s
/ target `DjangoType`" `` split across worktree lines 1383-1384. Re-confirmed byte-identical at
`HEAD` (same lines in the `HEAD` copy) and re-confirmed to resolve (1 occurrence in the spec), so
nothing is broken. My own line-scoped detector still reports it as an unterminated `#"`, which is
the class signature.

Routing audited rather than assumed: pass 2's `#### L1 and L2 dispositions` records agreement and
states "Routed to Worker 1's catalog as Worker 3 filed it"; pass 3's `### Notes for Worker 1`
opens "Passes 1 and 2's items and Worker 3's stand as filed." My pass-1 item 5 is the catalog
entry and is intact. **Not silently dropped.** Re-stated below so the final gate has it in the
most recent section too.

### DRY findings

None against this accumulated diff. All seven hunks are comment / docstring text and the
executable-token sequence of all four files is identical to `HEAD` (proved below), so the cohort
can introduce no duplicated logic, no repeated literal and no near-copy. The repeated-string
literals `scripts/review_inspect.py` reports for `types/finalizer.py` are pre-existing at `HEAD`
by that same proof and are not chargeable here. No existence challenge: the cohort creates no
abstraction.

**Cross-cohort duplication review: not applicable.** The plan declares a single cohort with no
other cohort running concurrently, so there is no second cohort's additions to compare against.

One near-duplication worth naming as a positive: the two live copies of the provenance clause
(`sets.py` and `inputs.py`) were deliberately worded to agree on the citation while differing on
the surrounding claim, because the two sentences assert different things. That is the right
shape — a shared pointer, not a copy-pasted sentence.

### Verification I performed independently

| Claim under test | Instrument | Result |
|---|---|---|
| `HEAD` is stable across the mid-pass move | `git log --stat 5842d23d..HEAD`, plus `cmp` of pre-move vs post-move `HEAD` copies | **Stable.** The two commits touch only `docs/`; `base.py`, `sets.py`, `finalizer.py` `HEAD` copies are byte-identical either side |
| Executable-token identity, **all four files** | own `tokenize` differ (drops `COMMENT` / `NL` / `NEWLINE` / `INDENT` / `DEDENT` / `ENCODING` / `ENDMARKER` and every statement-position `STRING`), vs `git show HEAD:<path>` | **IDENTICAL** for `filters/base.py` (2154), `filters/sets.py` (7315), `filters/inputs.py` (**2721**), `types/finalizer.py` (5530). My `inputs.py` count differs from Worker 2's 2759 because my filter also drops layout tokens; the identity verdict is what carries and it agrees |
| Substring-citation populations | own flatten-then-extract census, worktree and `HEAD` | three files **17 pre / 16 post**; two owned files **15 pre / 14 post**; `finalizer.py` `After` = **5**. All of Worker 2's restated figures reproduce |
| `HEAD` == pre-pass for that population | `git diff HEAD -- <file> \| grep '#"'` over all four files | **3** changed lines, all pass 1's own. Claim proved, not assumed |
| Decision 2 carries the placement claim | `grep -n '^### Decision [0-9]'`, `awk` + `grep -c` over 379-403 and 404-481, read spec line 387 | **Holds.** D2 = 379-403 carries both symbols on line 387; D3 = 404-481 carries `search` 0 times in any case |
| The sentence makes only a placement claim | read both repaired sentences against spec lines 387 and 824 | **Holds.** No behavioural assertion; declining the Edge-cases bullet is correct |
| Layer-5 neighbours are correct | `grep -n '^\*\*Layer [0-9]'` -> L5 = 416-470; `grep -c 'LOOKUP_NAME_MAP'` inside | **Both correct.** 3 occurrences inside Layer 5; the flat-field / `FieldSpec` rendering is there too. `grep -n 'Decision 3 Layer 5' inputs.py` -> exactly 1 hit, line 91 |
| `Accepts both raw` still unique | `grep -o … \| wc -l` | **1**, spec line 530, inside Decision 4 (482-541). Case-insensitively 2 (line 851's test-plan restatement), the recorded and harmless collision |
| `Partial-finalize recovery` still ambiguous | `grep -n` | **2**: line 695 (Decision 9, 655-699) and line 835 (`## Edge cases and constraints`). Dropping the substring remains required |
| `CharField` / `discretion` claims | `awk` + `grep -c` over 482-541; `grep -in` whole spec | `CharField` in D4 **0** (whole spec 1, line 853, unrelated); the table row names `CharFilter`. `discretion` **0**, `multi-key` **0**, `sentinel` **0** |
| No citation wrapped by any pass | own line-scoped detector for unbalanced `#"` and line-terminal `path::`/`.py` over all four files | **One wrapped `#"…"`, pre-existing at `HEAD`** (L2). **Zero** new wraps. `sets.py:1868` is a false positive of my detector (a reST literal-block `::`, not a reference). Single-line `path::Symbol` refs: 12 / 11 / 10 / 3 |
| Staged-anchor sweep | `grep -rn 'TODO(spec-027' --include='*.py' .` and the report's fenced form | **Zero hits in any `.py` file.** Precondition 6 stays discharged on the tree |
| Citation gate | `uv run python scripts/check_citations.py` | `OK: 742 citations resolve (665 in 422 .py files, 77 in KANBAN.md).` — my own reading reproduces pass 3's triple exactly |
| Public surface | `git diff HEAD -- django_strawberry_framework/__init__.py` | **Empty**, exit 0; the file is absent from `git status --short` |
| Focused tests | `uv run pytest tests/filters tests/types tests/test_registry.py tests/test_sets_mixins.py --no-cov -q` | **1119 passed in 13.97s.** My own scope, narrower than the build report's. No `--cov*` flag anywhere in this review |

### Churn reports — both classifications audited, both correct

**Citation gate 740 -> 742.** Reproduced independently: `742 (665 in 422 .py files, 77 in
KANBAN.md)`. The `.py` triple is byte-for-byte the `665 / 422` of passes 1 and 2, which is the
only half any pass here could move, and `KANBAN.md` is in the plan's declared
**concurrent-writable** set (`### Baseline-dirty out-of-scope files`). The `+2` is another
session's. **Not reverting is correct** — and reporting the moved total rather than reusing "the
same 740" is the right call, because a later reader differencing totals would otherwise read a
regression that is not there.

**The `HEAD` advance newly dirtied `KANBAN.md` / `KANBAN.html` / `examples/fakeshop/db.sqlite3`.**
Reproduced: `git status --short` reads **27 ` M` + 14 `??` = 41 paths**, exactly pass 3's roster,
and those three paths are exactly the plan's declared concurrent-writable set. `AGENTS.md` rule
34 and [`BUILD.md`][build] `### Tracked binary / generated files` both forbid the revert; a
`git checkout` of `db.sqlite3` here would clobber a live concurrent kanban write. **Not
reverting is correct**, and stop-and-report was the required response. Also verified that the
files pass 2 saw dirty and pass 3 saw leave (`spec-024-*`, `bld-final-025.md`,
`build-02{4,5}-*.md`) left because `2d1f117c` / `00a1cc4a` committed or deleted them, not because
anyone reverted anything.

### Failability proofs — audit and re-run

Recorded by all three passes: `None; this pass introduced no new boundary.`

**Audited against the accumulated diff, not accepted from the reports.** The executable-token
identity above is the mechanical ground: the `(type, string)` sequence of all four files is
`HEAD`'s, so the seven hunks contain no statement, branch, guard, comparison, gate, rejection
path or `raise` for the mandatory floor to select. The record is correct as written for all
three passes, and no proof should be manufactured for a comment edit.

**Boundaries re-run: none. Boundaries accepted on Worker 2's record: none.** The mandatory floor
(every boundary at 3-or-fewer recorded failing rows, plus every security / data-isolation
boundary) selects the empty set **legally**, under the one permitted condition — the diff
introduces no boundary at all. **The source carve-out was not exercised:** no transient mutation
was made, so there is nothing to revert and no byte-comparison to record.

No fail-open shape landed either, by the same proof: the diff contains no expression that
computes an input to a limit, a size, a permission decision or a rejection.

### `scripts/review_inspect.py`

**Re-run, not carried from pass 1.** [`BUILD.md`][build] `### When to run the helper during
build` fires for Worker 3 on a slice that "touches an existing `.py` file under `optimizer/` or
`types/`", and the accumulated diff touches `types/finalizer.py` in passes 1 **and** 2, so the
trigger fires again:

```shell
uv run python scripts/review_inspect.py django_strawberry_framework/types/finalizer.py --output-dir docs/shadow
```

Wrote `docs/shadow/django_strawberry_framework__types__finalizer.overview.md` and
`…stripped.py`. Django / ORM markers, control-flow hotspots and imports are all pre-existing at
`HEAD` by the token-identity proof, so none needs a per-entry justification against **this**
diff. Worker 2's recorded skip for the other three files is **valid** and is now discharged
mechanically rather than argued: the helper's `.stripped.py` replaces every comment and
string-literal token with `...`, so its output is provably invariant under a comment-text change,
and the token-identity table is that proof. No shadow-file line number is cited anywhere in this
review.

### Spec slice checklist walk

All three boxes are `- [x]`; all three contracts are in the accumulated diff and all three are
now correct.

- Box 1 (`filters/base.py`, two sites) — **landed and correct.** Both read `spec-027
  #"Accepts both raw"`; unique (1 hit, spec line 530) and inside Decision 4, which carries the
  contract both docstrings claim. No wrap boundary moved.
- Box 2 (`types/finalizer.py::_bind_filterset_owner`) — **landed and correct.** Substring dropped
  (required: 2 occurrences), `Decision 9` carries the retry contract, and pass 2's L1 fix left
  the sentence grammatical without reflowing.
- Box 3 (`filters/sets.py` staged anchor, a disposition decision) — **landed and now correct.**
  The disposition was already right at pass 1; pass 2 repaired the provenance clause that rode
  with it, and the repair re-derives.

No box is silently unaddressed and none is ticked without a matching change.

**One gap, and it is Worker 1's not Worker 2's:** partition correction 2 added
`filters/inputs.py` to the cohort and its repair landed in pass 3, but the checklist still
carries **three** boxes for **four** landed sites. Worker 2 may not add boxes — Worker 1 writes
the checklist at plan time — so this is not a build defect. It does mean Worker 1's final audit
has no box to audit for the `inputs.py` site. Routed below.

### Hot-path budget

`Not applicable; plan declares no hot path.` **Audited:** the build plan's preamble declares
`Hot-path declaration: none`, and the token-identity proof means nothing executes differently per
request, per resolver, per row, per connection or per outbound message. No number is owed and
none should be manufactured for a comment edit.

### Floor verification

`Not applicable; plan declares floor-verification scope none.` **Audited:** no executable
statement changed in any of the four files, so no Django / Strawberry / channels integration seam
is touched. Correct as recorded across all three passes.

### Public-surface check

`git diff HEAD -- django_strawberry_framework/__init__.py` is **empty** (exit 0); the file does
not appear in `git status --short`. `__all__` and the re-export list are unchanged across all
three passes. No spec authorization is needed.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity (only when the slice touches docs, release metadata, KANBAN, or archived specs)

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces. The cohort's diff is
four `.py` files. `KANBAN.md` / `KANBAN.html` are dirty in the tree but are another session's, in
the plan's declared concurrent-writable set, and untouched by any pass here.

### What looks solid

- **The `HEAD`-move handling.** Re-taking the `HEAD` copy after the move and `cmp`-proving it
  identical, instead of assuming a docs-only commit could not matter, is the right instinct on
  this tree. I reproduced it two ways and it holds.
- **Reporting the moved citation-gate total instead of reusing the earlier phrasing.** Passes 1
  and 2 used "the same 740" as evidence; pass 3 could have quietly kept saying it. Splitting the
  total into the `.py` half it could affect and the `KANBAN.md` half it could not is what makes
  the number evidence again rather than a coincidence.
- **Refusing the pattern fix on `Layer 5`.** Three sites spell `Decision 3 Layer 5`; one was
  wrong and two were right. A sweep would have broken two correct citations to repair one. Both
  neighbours were re-verified against re-derived Layer bounds before being left alone, and I
  re-derived them again independently.
- **Deriving the placement/behaviour distinction rather than citing both surfaces.** My pass-1
  recommendation offered "Decision 2 (or both Decision 2 and the Edge-cases bullet)". Taking only
  Decision 2, with the reason stated, is the better answer, and it is a case of the builder
  correcting the reviewer.
- **Withdrawing pass 1's own false statements in prose rather than restating them** — the L1
  deferral reason and the precondition-6-vs-rule-26 licensing. A recorded rejection reason is
  what licenses acceptance, so a wrong one being retracted out loud is worth as much as the fix.
- **Enumerating the citation population instead of asserting a total.** Both M2 tables list the
  actual citations, which is what let me difference against my own instrument's listing rather
  than compare two bare numbers.

### Temp test verification

No temp test was written and `docs/builder/temp-tests/slice-4-027/` was not created. The
accumulated diff contains no executable statement, so there is no behaviour for a temp test to
demonstrate; this review's instruments are token and text analyses over the source and the spec,
which prove more about this diff than any test could. Nothing to promote.

### Notes for Worker 1 (spec reconciliation)

Pass 1's five items stand. Items 4 (M2's corrected figures) and the `inputs.py` `LOOKUP_PREFIXES`
routing are **discharged** — the figures are re-derived and enumerated in pass 2's `#### M2` and
independently confirmed above, and the `inputs.py` repair landed in pass 3 under partition
correction 2. Four items remain or are new.

1. **`Escalated:` `filters/inputs.py::_scalar_from_form_field` #"lists CharField as a recognized"
   (N1) has no executor as currently routed.** Worker 1 reads source read-only, so the
   "recommended replacement" for a `.py` comment cannot be applied by the worker it was filed
   with. Resolution paths, both terminating: (a) Worker 1 picks the wording — `CharFilter`, or
   drop the claim about the table — and sets `revision-needed` for a one-line Worker 2 pass
   (pass 3 explicitly offered to take it); or (b) Worker 1 records it in `bld-final-027.md`'s
   deferred-work catalog as an explicit next-card obligation with the site and both wordings
   named. What is **not** available is leaving it as a recommendation in a build report: nothing
   downstream of that reads it as work.
2. **`Escalated:` `filters/inputs.py::normalize_input_value` #"Implementation-discretion item"
   (N2), same routing problem, plus a genuine custodian question.** The citation names a surface
   the spec has never had (`discretion` / `multi-key` / `sentinel` all 0 hits) and whose only
   real-world namesake is [`ARTIFACT.md`][artifact]'s build-artifact template section, which is
   deleted at the next build's pre-flight. Resolution paths: (a) drop the citation and keep the
   design note — favoured by `AGENTS.md`'s ban on build-process provenance in code comments,
   whose KEEP list covers spec Decision pointers and not this; or (b) add the multi-key
   return-shape clause to `spec-027` Decision 4's converter / normalizer surface and cite that.
   Either way the tree edit needs a Worker 2 pass, so the same (a)/(b) execution note as item 1
   applies. **Whether the multi-key return shape is a contract the spec should carry is the
   custodian's call and nobody else's** — that part of pass 3's reason is right.
3. **The third wrapped citation (L2) is still open and still uncounted.**
   `types/finalizer.py::_format_multi_owner_mismatch_error`, worktree lines 1383-1384,
   byte-identical at `HEAD`, resolves correctly. Confirmed routed by both later passes, not
   dropped. The catalog should carry the **class with the exemplar and an audit step, never a
   count** — a wrapped citation is invisible to every line-bounded instrument in this repo,
   `scripts/check_citations.py` included (its `CITATION_RE` is line-scoped and `docs/` is
   deliberately out of scope), so any count is instrument-dependent by construction. A
   flatten-first citation checker is the only instrument shape that sees the class at all and is
   the useful follow-up card.
4. **The Plan's `### Spec slice checklist (verbatim)` carries three boxes for four landed
   sites.** Partition correction 2 added `filters/inputs.py` and its repair landed in pass 3, but
   no box was added, so the final audit has nothing to tick for it. Worker 2 may not write the
   checklist. Resolution: Worker 1 adds a fourth box quoting partition correction 2's finding row
   and ticks it against pass 3's diff, or records the site explicitly under `### Spec changes
   made (Worker 1 only)`.

Pass 1's items 1 (`spec-055`'s identical false `Decision 3 Layer 5` attribution, still live and
still fenced), 2 (`Escalated:` `docs/TREE.md` line 859 rendering `(spec-021)` for
`examples/fakeshop/apps/library/filters.py`) and 3 (`bld-integration-027.md` attributing the
second `Partial-finalize recovery` to Decision 11 when it is under `## Edge cases and
constraints`) are unchanged and unaddressed by design — all three are outside this cohort's
writable set.

One non-defect re-recorded so it is not re-raised: the `Decision 6` -> `Decision 9` retarget at
`_bind_filterset_owner` is correct for the sentence's own claim (partial-finalize recovery), even
though the idempotent-binding *mechanism* is pinned in Decision 6 subpass 1 #"Bind the owner.". A
candidate refinement only if a later pass edits that docstring for another reason.

### Review outcome

`review-accepted`.

All four pass-1 findings are closed or correctly disposed: **M1** — both live copies of the false
`Decision 3 Layer 5` attribution now cite Decision 2, which I re-derived as carrying the
placement claim the sentences make, and declining the Edge-cases bullet is right because neither
sentence makes a behavioural claim; **M2** — every restated figure reproduces under my own
instrument at my own stated baseline, and `HEAD == pre-pass` is proved rather than assumed;
**L1** — fixed on one line with nothing reflowed and the false reason withdrawn; **L2** —
confirmed pre-existing, confirmed to resolve, confirmed still routed to Worker 1's catalog and
not silently dropped.

The two reported-not-repaired `inputs.py` sites are **real defects, correctly reported, and
correctly not repaired by this pass**. N2 is the stronger defect and the weaker repair candidate:
its only two fixes are a spec edit (Worker 1's alone) or the destruction of a pointer Worker 1
may want to make valid, so deferring it is right on stronger grounds than the report claims. N1's
reason is thinner — the replacement pass 3 itself wrote is very nearly mechanical — but two
defensible wordings do exist and the choice is Worker 1's, so the deferral holds. Neither is
`revision-needed` material: both are inherited rot outside the dispatched population, the pointer
resolves in N1's case, and both carry a recorded reason that survives audit. What they do carry
is a routing defect I have corrected above — a `.py` fix filed as a recommendation to a
read-only worker has no executor, so both are escalated with resolution paths that terminate.

Both churn reports are classified correctly and neither was reverted, which is the required
behaviour: the citation gate's `+2` is `KANBAN.md`'s and the `.py` triple is unchanged; the newly
dirty `KANBAN.md` / `KANBAN.html` / `db.sqlite3` are exactly the plan's declared
concurrent-writable set, and a revert there would clobber a live concurrent session's work.

Mechanically: executable-token identity holds against `HEAD` for **all four** files rather than a
subset, so the `### Failability proofs` record of `None` is a measurement; no citation was wrapped
by any of the three passes and the one wrapped citation in the cohort is pre-existing; the
staged-anchor sweep is clean in shipped source; the public surface is untouched; 1119 focused
tests pass with no coverage flag; and `scripts/review_inspect.py` was re-run on
`types/finalizer.py` with `--output-dir docs/shadow`.

---

## Final verification (Worker 1)

Fourth Worker 1 spawn of this cycle. Every figure below was re-derived with this pass's own
instruments; where it agrees with a build report or a review it is an independent agreement, and
the command is named either way. No `git checkout` / `git stash` / `git restore` /
`git worktree` was used. `HEAD` advanced a **third** time during this pass — `7722c4b3
docs(specs): reconstruct the spec-026 record and home its residual findings`, after
`00a1cc4a` / `2d1f117c` — and `git log --oneline 5842d23d..HEAD -- docs/SPECS/spec-027-filters-0_0_8.md docs/SPECS/appx/spec-027-filters-0_0_8-rationale.md django_strawberry_framework/`
returns **nothing**, so no commit in the range touched this cycle's spec, its rationale, or any
package source. The `HEAD` copies taken by this pass are `cmp`-identical to the ones passes 1
and 2 left in the scratchpad for `base.py`, `sets.py` and `finalizer.py`.

- **Spec slice checklist:** audited below. Boxes 1-4 are `- [x]` and every contract landed;
  boxes 5-6 are newly written by this pass and are the dispatch, not a deferral.
- **DRY check across this cohort and prior accepted slices:** no new duplication. Executable-token
  identity against `HEAD` holds for all four files (this pass's own instrument, below), so the
  cohort's diff can introduce no logic, literal, or near-copy at all.
- **Existing tests still pass:** `uv run pytest tests/filters tests/types tests/test_registry.py tests/test_sets_mixins.py examples/fakeshop/test_query/test_library_api.py --no-cov -q`
  -> **1316 passed in 60.83s**. No `--cov*` flag anywhere in this pass.
- **Spec reconciliation:** yes, and it is load-bearing for one of the two dispatched repairs. See
  `### Spec changes made (Worker 1 only)` items 1-2.
- **Floor verification:** `No floor-verification scope declared.` The build plan's preamble
  declares `Floor-verification scope: none`, no pass in this cycle owed a floor run, and none was
  run. Recorded as the literal rather than left blank, so the final gate inherits a statement
  instead of a silence.
- **Final status: `revision-needed`.** Two one-line comment repairs in `filters/inputs.py`, a file
  this cohort already owns under partition correction 2, are dispatched to a Worker 2 pass 4 with
  the wording decided here. Reasoning under `### The two `inputs.py` Lows: decided, with a path that terminates`.

### Gates re-run by this pass

| Gate | Command | Result |
|---|---|---|
| Spec glossary | `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-027-filters-0_0_8.md` | `OK: 48 terms - all have glossary entries and at least one spec link.` exit **0**, re-run **after** this pass's spec edit |
| Citation gate | `uv run python scripts/check_citations.py` | `OK: 742 citations resolve (665 in 422 .py files, 77 in KANBAN.md).` exit **0** |
| Source layout / ASCII-only | `uv run python scripts/check_trailing_commas.py --check docs/SPECS/spec-027-filters-0_0_8.md docs/SPECS/appx/spec-027-filters-0_0_8-rationale.md` | exit **0** |
| Focused tests | as above | **1316 passed** |

**The `.py` half of the citation gate is `665 in 422 .py files`, exactly the triple passes 1-3
recorded.** This pass wrote no `.py` file, so that is the half it could have moved and did not.
The `KANBAN.md` half reads 77 against passes 1-2's 75; `7722c4b3` committed a `KANBAN.md` change
during this cycle and `KANBAN.md` is in the plan's declared concurrent-writable set. **Not this
cycle's, and not explained away** — the delta is named, attributed to a commit, and left alone.

### Executable-token identity, all four files, this pass's own instrument

`tokenize` each file, drop `COMMENT` / `NL` / `NEWLINE` / `INDENT` / `DEDENT` / `ENCODING` /
`ENDMARKER` and every statement-position `STRING`, compare the remaining `(type, string)`
sequence against `git show HEAD:<path>`.

| File | Verdict | Tokens |
|---|---|---|
| `django_strawberry_framework/filters/base.py` | **IDENTICAL** | 2153 |
| `django_strawberry_framework/filters/sets.py` | **IDENTICAL** | 7347 |
| `django_strawberry_framework/filters/inputs.py` | **IDENTICAL** | 2755 |
| `django_strawberry_framework/types/finalizer.py` | **IDENTICAL** | 5567 |

Three instruments in this cohort now report three different token counts for the same file
(`inputs.py`: Worker 2 2759, Worker 3 2721, this pass 2755) because each drops a different set of
layout tokens. **The count is not the measurement; the verdict is**, and all three agree on it.
The accumulated diff — this cohort's seven hunks plus Slice 2's, since `HEAD` is not "before this
cohort" — therefore contains no statement, branch, guard, comparison, rejection path, or `raise`.
That is the mechanical ground for the three passes' `### Failability proofs` record of `None`, for
`### Hot-path budget` `Not applicable`, and for the floor-scope literal above.

### Spec slice checklist audit

Every `- [x]` was checked against the tree, not against the report that ticked it.

| Box | Contract | Verdict |
|---|---|---|
| 1 | `filters/base.py` x2 -> `spec-027 #"Accepts both raw"` | **LANDED.** Lines 553 and 692 carry it; `grep -o 'Accepts both raw' <spec> \| wc -l` = **1**, spec line 530, inside Decision 4 (482-541), whose sentence states the contract both docstrings claim |
| 2 | `types/finalizer.py::_bind_filterset_owner` -> `Decision 9`, substring dropped | **LANDED.** Line 1226; `Partial-finalize recovery` still occurs **2**x (spec 695, 835), so dropping it was required, and `grep -c '^### Decision 9 ' <spec>` = **1** |
| 3 | `filters/sets.py` staged anchor, disposition decision | **LANDED.** Line 1369 reads `TODO(spec-055 Slice 1)` with the originating contract kept as non-TODO provenance; `grep -rEn 'TODO\(spec-027\|TODO-(ALPHA\|BETA\|STABLE)-027' --include='*.py' .` returns **zero** |
| 4 | `filters/inputs.py` `LOOKUP_PREFIXES` comment -> `Decision 2` | **LANDED.** Line 81; `grep -c '^### Decision 2 ' <spec>` = **1**, and Decision 2's spec line 387 enumerates `construct_search` and `LOOKUP_PREFIXES` |

**No box was over-ticked and none needed un-ticking.** Boxes 5 and 6 are this pass's dispatch and
are correctly `- [ ]`; they are not deferrals and carry no deferral reason, because the work is
routed rather than parked.

**On the missing box.** Worker 3 is right that partition correction 2 grew the cohort to four
sites while the checklist carried three, and right that neither builder nor reviewer may add one.
Box 4 is the repair: it quotes partition correction 2's own verified finding and is ticked against
pass 3's diff, which I re-derived above rather than accepting. Recording the site only in prose
was the weaker option — the checklist is what the audit walks, so a landed site invisible to it is
a site nothing audits next cycle either.

### The two `inputs.py` Lows: decided, with a path that terminates

Worker 3's routing charge is correct and is the reason this pass does not close the cohort: a
`.py` comment fix filed as a "recommended replacement" under `### Notes for Worker 1` addresses a
worker who reads source read-only, so it has no executor. Both are decided below, both take the
**same** terminating path, and both are boxes on the checklist so the next pass has something to
tick.

**Why `revision-needed` rather than the deferred-work catalog, for both.** Three reasons, and none
of them is severity:

1. **The file is this cohort's.** Partition correction 2 put `filters/inputs.py` in the ownership
   partition and pass 3 wrote it. A cohort whose entire contract is "repair false spec citations"
   cannot close leaving two false spec citations in a file it owns — one asserting the spec says
   something it does not, one naming a spec surface that has never existed.
2. **Neither is a judgement any more.** Worker 3 accepted both deferrals on the ground that the
   wording was a custodian call. That call is made below, in exact replacement text, so the pass
   is mechanical: two lines, no reflow, both target lines byte-verified against the tree.
3. **A catalog item needs an owner that exists.** The genuinely deferred items below are fenced
   files and other cards' trees — surfaces no pass in this cycle may write. These two are neither
   fenced nor another card's, so parking them would hand a live defect to a card that does not
   exist yet. This cycle's own evidence is that a routed-but-unowned item survives every pass:
   the `spec-055` attribution has now been routed four times and is still wrong.

**Dispatch: Worker 2 pass 4. Writable set: `django_strawberry_framework/filters/inputs.py` only**
(already in the declared partition, so no partition correction is owed). Both edits are single
lines; leave the neighbouring lines byte-identical, exactly as passes 2 and 3 did, so no citation
can be wrapped by a reflow.

**N1 — line 260, `_scalar_from_form_field`.** Decided: **name the class the spec's table row
actually names.** Re-derived here, not accepted: `awk 'NR>=482 && NR<=541' <spec> | grep -c 'CharField'`
= **0**; the whole spec carries `CharField` exactly **once**, at line 853, in a
`test_definition_relations.py` aside about `Book.circulation_status`; the conversion table's first
row (spec line 518) names **`CharFilter`**. The attribution to Decision 4 resolves — Decision 4 is
the decision carrying the conversion table, and that row's "the scalar Python type … derived from
the model field's `to_python`" is exactly this branch's `-> str` mapping — so only the class name
inside the sentence is false. The rejected alternative is the other wording Worker 2 and Worker 3
both named: keep `CharField` and delete the claim about the table. **Rejected because it pays for
a true sentence with a lost pointer.** `AGENTS.md` keeps spec Decision pointers in comments; the
pointer here is correct and load-bearing (it is why the explicit branch exists at all), and one
word is what is wrong with the sentence. The two surviving `` ``CharField`` `` mentions stay: they
name the `forms.CharField` branch this function actually tests, which is a different object from
the spec's `CharFilter`, and that distinction is the sentence's whole point.

Exact replacement, **line 260 only** (verified byte-exact against the tree with `od -c`):

```text
-    # table in spec-027 Decision 4 lists CharField as a recognized
+    # table in spec-027 Decision 4 lists ``CharFilter`` as a recognized
```

**N2 — line 522, `normalize_input_value`.** Decided: **make the spec side valid, then repoint the
citation at it.** Worker 3 is right that this is the stronger defect and the weaker repair
candidate — `grep -in 'discretion'` over the spec returns **0**, so do `multi-key` and `sentinel`,
and `### Implementation discretion items` is a section of [`ARTIFACT.md`][artifact]'s
**build-artifact template**, a Worker 1 plan section inside a per-cycle `bld-*.md` file that
pre-flight deletes. So the citation names a surface the spec has never had and whose only namesake
is not durable.

What decided it is a defect neither builder nor reviewer looked for, because neither was pointed
at the spec paragraph the citation *should* have named. **Spec line 526, the `normalize_input_value`
contract paragraph inside Decision 4, was false in two independent ways** (both re-derived against
the code, details in `### Spec changes made (Worker 1 only)` item 1):

- it claimed a `relay.GlobalID` object normalizes to a **decoded `node_id`**, which is the exact
  shape `filters/inputs.py::_encode_global_id_input` exists to *prevent* — its docstring records
  that eager decoding stripped the `type_name` before the validation that depends on it, and let a
  wrong-type GlobalID object pass the gate silently;
- it claimed the range dataclass normalizes to named `{lookup}_from` / `{lookup}_to` keys — **four
  lines below the table row that says, in bold, `NOT` named `_from` / `_to` keys**, and after the
  rationale's `rev5 H3` entry records that this very claim was retracted and the table corrected.
  The retraction fixed the table row and missed the prose. A partial claim fix reads as a whole one
  to every later sweep, which is why it survived eight revisions, three slices, and an integration
  pass.

So the honest sequence was not (a)-or-(b) but both halves of (b): the paragraph the comment wants
to cite was wrong and is now right, and it now states the multi-key return shape explicitly. The
citation becomes a true pointer at a durable contract instead of a pointer at nothing. **Option
(a) — drop the citation, keep the design note — is rejected**, and Worker 3's argument for it is
answered rather than ignored: `AGENTS.md`'s ban is on build-*process* provenance, and its KEEP list
is spec Decision pointers. Under (a) this sentence would have kept a design claim with no
authority anywhere; under (b) it cites the decision that now carries that claim, which is the KEEP
class exactly. The pointer was not the defect — its target's absence was, and a custodian can
close that.

Exact replacement, **line 522 only** (verified byte-exact against the tree with `od -c`), citing
`Decision 4` without a `#"substring"` for the reason this cohort established twice already: a
substring pinned to prose is the fragility class the whole cohort exists to repair.

```text
-    Per the spec-027 Implementation-discretion item, the
+    Per spec-027 Decision 4's ``normalize_input_value`` contract, the
```

Lines 523-524 (`multi-key return shape lets the ``_normalize_input`` caller merge` /
`the patch without inventing a sentinel-pair object.`) stay byte-identical, and are now supported
word for word by the spec's third bullet.

### Summary

The cohort's dispatched work is **complete and correct**: four `.py` sites across three passes,
every repaired citation re-derived against the spec by this pass and resolving to the decision that
carries the contract its sentence claims, executable-token identity against `HEAD` holding for all
four files, the staged-anchor sweep clean in shipped source, the `.py` citation gate unmoved at
`665 in 422`, and 1316 focused tests green. The cohort does **not** close, for a reason the
dispatch anticipated and one it did not: the two `inputs.py` Lows needed a decision only the
custodian could make, and making the second one exposed that the spec paragraph the citation should
have named was itself false twice over — a claim the rationale records as retracted in `rev5 H3`,
retracted only in the table row, live in the prose four lines below it ever since.

### Spec changes made (Worker 1 only)

1. **`docs/SPECS/spec-027-filters-0_0_8.md`, `### Decision 4 — Upstream-primitives parity floor`,
   the `normalize_input_value(filter_instance, raw_value)` paragraph (was one line, spec line 526;
   now a lead-in plus three bullets).** Triggered by this cohort's N2. The sentence carried two
   false claims about shipped behaviour and one of them contradicted the table row four lines above
   it. Replaced by the three return shapes the function actually has, each checked against
   `django_strawberry_framework/filters/inputs.py`: a scalar (with the `relay.GlobalID` case stated
   as the re-encoded **base64 wire string**, and why — `_encode_global_id_input`'s docstring records
   the decoded shape as the bug it fixed); a `list`; and a `dict[str, Any]` patch the caller merges,
   for a filter consuming more than one positional form-data key, with the `RangeFilter` case
   spelled as the positional `{<field>_0, <field>_1}` per the table row. Applied by a
   count-asserted replacement that writes nothing on a mismatch (1 occurrence expected, 1 found).
   Spec **254,798 -> 255,828 bytes** (`wc -c`; a `len(text)` reading of the same edit reports
   253,898 -> 254,928, because this prose carries em dashes and arrows and Python counts
   characters where `wc -c` counts bytes -- state which instrument produced a size claim). **This is a correction, not new contract**: every shape stated was
   already on disk and two of the three were already stated correctly elsewhere in the same
   Decision.
2. **`docs/SPECS/appx/spec-027-filters-0_0_8-rationale.md`, `## Decision 4`, new
   `### Claims this Decision may no longer make`.** The rationale is the keyed home for a claim a
   Decision may no longer make, and Decision 4 had no such section while carrying two. Both
   retractions recorded with the evidence: the decoded-`node_id` claim against
   `django_strawberry_framework/filters/inputs.py::_encode_global_id_input`, and the
   `{lookup}_from` / `{lookup}_to` claim against `rev5 H3`, which is recorded three bullets above in
   the same Decision's `### Changes this Decision underwent` as *already retracted* — the partial
   fix is the finding, not the claim. Same count-asserted method. Rationale **143,887 -> 145,000 bytes** (`wc -c`). Nothing references any `#claims-this-decision-may-no-longer-make` anchor (verified
   repo-wide); the heading text now occurs 8 times in the file, as it did 7 before.
3. **This artifact's `### Spec slice checklist (verbatim)`, box 4 added and ticked.** Partition
   correction 2 grew the cohort to a fourth site (`filters/inputs.py` `LOOKUP_PREFIXES`) after the
   checklist was written, and neither Worker 2 nor Worker 3 may add a box. Box 4 quotes partition
   correction 2's verified finding row; the tick is against this pass's own re-derivation of the
   landed line, not against pass 3's report.
4. **This artifact's `### Spec slice checklist (verbatim)`, boxes 5 and 6 added, left `- [ ]`.**
   The two dispatched `inputs.py` repairs, so Worker 2 pass 4 has a box to tick and the next final
   verification has one to audit. They are a dispatch, not a deferral, so they carry no deferral
   reason.

No status/header edit was owed. Spec lines 1-9 were re-read at the start of this pass:
`Status: shipped (`0.0.8`)`, the card id, the `0.0.8` target, the owner line, the predecessors, and
the rationale-companion pointer all still describe the build's current state.

### Deferred work catalog (consolidated for the final gate)

**This is the single list `bld-final-027.md` inherits.** It supersedes the five scattered
`### Notes for Worker 1` lists across this cohort's three build reports and two reviews, plus
`bld-integration-027.md` `### Deferred work catalog (re-derived)`. Every item was re-derived here
with the command shown. **Three inherited items were wrong and are corrected in place** — a catalog
is a claim, and this cycle's catalogs have now been wrong three times.

Nothing below is `revision-needed` material: every item is either a fenced file, another card's
tree, or a class whose population no instrument in this repo can close.

1. **A wrapped `#"substring"` citation, invisible to every line-bounded instrument.** Exemplar:
   `django_strawberry_framework/types/finalizer.py::_format_owner_target_mismatch_error`, worktree
   lines 1383-1384, `#"owning `FilterSet`'s / target `DjangoType`"`. Byte-identical at `HEAD`, and
   it **resolves** (1 occurrence in the spec) — fixing it means reflowing five lines of a docstring
   nothing else in this cycle edits. **Correction to the inherited item:** every prior artifact and
   the dispatch brief name the symbol `_format_multi_owner_mismatch_error`. **That symbol does not
   exist** — `grep -n 'def _format_.*mismatch_error' <file>` returns six formatters and none is it.
   The unwrapped twin of the same citation is at line 1252, inside `_bind_filterset_owner`.
   *Source: this artifact, Worker 3 pass 1 `### Notes for Worker 1` item 5 and pass 2 item 3.*
   *Licensing spec line: none; it is a comment-legibility item, not a contract.* The useful
   follow-up card is a **flatten-first citation checker** — `scripts/check_citations.py`'s
   `CITATION_RE` is line-scoped and puts `docs/` out of scope by design, so no count of this class
   is available from any existing instrument. **Card the class with the exemplar and an audit step,
   never a count.**
2. **`docs/TREE.md` line 859 renders `(spec-021)` for `examples/fakeshop/apps/library/filters.py`.**
   Slice 2 fixed the module docstring (`grep -rn 'spec-021' --include='*.py' .` returns **zero**
   tree-wide) but `docs/TREE.md` is script-rendered and was never regenerated, so the render still
   carries the pre-renumber id — and `spec-021` today names a **different** card
   (`docs/SPECS/spec-021-apps-0_0_7.md`, the `AppConfig` card), which makes the row actively wrong
   rather than merely stale. `docs/TREE.md` is fenced this cycle and is a render, not a source:
   **the fix is `uv run python scripts/build_tree_md.py`, owned by whoever owns doc-wrap, and never
   a hand-edit** (the next render reverts one). **Correction to the inherited item:** it is *not*
   "the last live `spec-021` reference to this card". `KANBAN.md` line 5256 carries a second, under
   `## Decision: FilterSet subclassing unsupported` — "Ref: spec-021 pre-merge review M-filters-3 /
   H-filters-3" — which is this card's pre-renumber id, not the `AppConfig` card's. `KANBAN.md` is
   DB-generated too, so that one is an ORM edit plus a regenerate, not a text fix.
   *Source: this artifact, Worker 2 pass 1 and Worker 3 pass 1 item 2.*
3. **`README.md` carries zero occurrences of `filter_input_type`.** Re-derived:
   `grep -c 'filter_input_type' README.md` = **0**, against a `## Doc updates` bullet that names it
   alongside `FilterSet` / `RelatedFilter` / `Meta.filterset_class` (all three present at the
   `0.0.8` line) and argues explicitly why the helper belongs there. **The one genuinely
   undischarged `## Doc updates` obligation in the cycle**, found only by reading a surface a prior
   slice had declared unexamined. `README.md` is fenced.
   *Source: `bld-integration-027.md` item 10. Licensing spec line: the `## Doc updates` `README.md`
   bullet — which licenses the work, not the deferral.*
4. **Four `test_clear_tolerates_unimportable_*` docstrings describe a retired mechanism.**
   Re-derived: `tests/test_registry.py` lines 1617 / 1651 / 1687 / 1721, and
   `grep -c 'except ImportError' django_strawberry_framework/registry.py` = **0**. All four
   describe the cycle-safe local-import guards that `register_subsystem_clear(...)` replaced; each
   test still proves something real (poisoning `sys.modules` leaves the registry's own clear
   undisturbed), so this is docstring rot, not a dead test. **Only the `filter` one belongs to this
   card**; the others name spec-028 / spec-030 / spec-032.
   *Source: `bld-integration-027.md` item 2.*
5. **The PEP-563 deferred-annotation path for `filter_input_type` has no dedicated test.**
   Re-derived: `test_filter_input_type_under_future_annotations` returns **zero** hits tree-wide.
   The spec's `## Test plan` now says so in as many words, and the repeat-safety property PEP 563
   depends on is pinned by `test_filter_input_type_is_idempotent_under_repeated_calls`. A coverage
   boundary, not an untested contract.
   *Source: `bld-integration-027.md` item 3. Licensed by the `## Test plan`'s own sentence.*
6. **History-narrating prose in `.py` comments — a real class whose population is
   instrument-dependent.** Three instruments over the same file set disagree: ~65 across 15 files,
   54 across 11, 46 across 11. All three include legitimate contrast prose (a docstring saying what
   a fixture is *not* is not build provenance), so no number is a population. Confirmed exemplar all
   three agree on and this pass re-confirmed at line 593:
   `django_strawberry_framework/filters/inputs.py::_encode_global_id_input`
   #"The previous implementation eagerly decoded the object". **Card the class with the exemplar and
   an audit step, never a count.**
   *Source: `bld-integration-027.md` item 4.*
7. **Bare `Decision N` references naming no card.** The defect is **card attribution, not count**:
   most belong to other cards, so the population cannot be swept by number — only resolved site by
   site against the card whose file it sits in. Two readings over the cycle's dirty `.py` set: 83
   across 13 of 19 files (integration pass), and **72 across 13 of 20 files** (this pass, counting
   occurrences and treating a `spec-NNN`-prefixed reference as attributed). Confirmed ambiguous
   exemplar: `django_strawberry_framework/utils/inputs.py` carries two `no operator bag, Spec
   Decision 8` refs in the shared substrate, both meaning **spec-028**'s Decision 8, not this
   card's.
   *Source: `bld-integration-027.md` item 5.*
8. **Raw source-line references, which `AGENTS.md` rule 27 allows only in per-cycle scratchpads.**
   Two populations, both in other cards' surfaces:
   - **Five** in `examples/fakeshop/test_query/test_products_api.py`, lines 2948 / 2984 / 3015 /
     3051 / 3098, all re-derived present. **Correction to the inherited item:** they are *not*
     spelled `spec-036 line NNN`; they are bare `(line 388)` / `(mirror line 493)` refs inside that
     file's `036` mirror block, so a sweep by the token `spec-036` finds none of them. They were
     correctly untouched under the card-not-directory scope boundary.
   - **Eleven**, not thirteen, across other cards' package modules: `orders/inputs.py` 2,
     `orders/sets.py` 4, `mutations/resolvers.py` 1, `mutations/sets.py` 4. **Correction to the
     inherited item:** the two attributed to `_strawberry_patches.py` are the `#L45-L52` fragment of
     a **GitHub permalink pinned to a commit sha** — a legitimate upstream reference, not a raw
     source-line ref into this repo. The instrument's `L[0-9]` alternative is what manufactured
     them.
   *Source: `bld-integration-027.md` items 6 and 7.*
9. **The same broken/ungated citation class in other cards' trees.** Confirmed live by reading, in
   ten files: `orders/factories.py`, `mutations/resolvers.py`, `mutations/inputs.py`,
   `mutations/sets.py`, `rest_framework/{resolvers,serializer_converter,sets,inputs}.py`,
   `forms/inputs.py`, `types/base.py`. Exemplars:
   `rest_framework/serializer_converter.py` #"``annotate_queryset_relation`` after" (a bare `M3:`
   review-finding id) and `rest_framework/inputs.py` #"even when DRF ``required=True``" (a bare
   `H3`). Every one belongs to another card; the count is instrument-dependent for the same reason
   as items 6 and 7.
   *Source: `bld-integration-027.md` item 7, `bld-slice-2-027` out-of-scope table.*
10. **`docs/SPECS/spec-055-search_fields-0_1_2.md` carries three wrong references to this card, not
    one.** Re-derived: **line 29** and **line 195** both attribute `construct_search` /
    `LOOKUP_PREFIXES` to "spec-027 Decision 3 Layer 5" — the identical false attribution this cohort
    repaired at both live `.py` sites, and `spec-055` is the document the next author copies from,
    so it is the propagation source; **line 200** quotes the staged anchor as
    `TODO(spec-027-filters-0_0_8 Meta.search_fields card 0.1.2)`, which is now wrong in the id (pass
    1 retargeted it to `TODO(spec-055 Slice 1)`) *and* was already wrong at `HEAD` in the
    `card 0.1.2` suffix the real comment has never carried. **Correction to the inherited item:** it
    was recorded as one site plus a suffix; it is three sites. `spec-055` is another card's spec and
    fenced.
    *Source: this artifact, Worker 3 pass 1 item 1 and Worker 2 pass 1 `### Notes for Worker 1`.*
11. **`docs/builder/bld-integration-027.md` `### Citation audit` mis-attributes the second
    `Partial-finalize recovery` occurrence to Decision 11.** Re-derived: the occurrence is spec line
    835, under `## Edge cases and constraints` (line 811); `### Decision 11` spans 710-783 and
    `### Decision 12` opens at 784, so line 835 is past both, and Decision 11 carries zero
    occurrences. The disposition that sentence supports — drop the substring — is unaffected. A
    record correction only; a worker may not edit a prior artifact.
    *Source: this artifact, Worker 2 pass 1 and Worker 3 pass 1 item 3.*
12. **The `## Non-goals` auto-generation sentence is already carded — do not re-derive it as new
    rot.** `KANBAN.md` `TODO-ALPHA-051-0.0.15` carries the WP-D contract question that gates it.
    Acting on it would pre-empt a decision this cycle does not own.
    *Source: `bld-integration-027.md` item 9.*
13. **`[fakeshop-test-library-reload]` resolves to two different files across the spec/rationale
    pair, deliberately.** The spec's def points at `conftest.py` (Slice 3's fix); the rationale's
    still points at `test_library_api.py`, because its only use is the verbatim `rev7` entry whose
    subject is the claim naming that file. Recorded so a future sweep reads it as a decision rather
    than an unfinished fix.
    *Source: `bld-integration-027.md` item 12.*

**Closed, so the gate does not carry them forward as open:** the three broken `#"substring"`
citations (integration item 1) landed in passes 1-2; the `filters/inputs.py` `LOOKUP_PREFIXES`
attribution (Worker 2 pass 2) landed in pass 3; M2's corrected citation populations (Worker 3 pass
1 item 4) were enumerated in pass 2 and independently reproduced in Worker 3 pass 2; the staged
anchor (integration item 8) was retargeted in pass 1 and the `spec-055` half of it is item 10 above.
The two `inputs.py` Lows are **dispatched, not deferred**, and are checklist boxes 5 and 6.


---

## Build report (Worker 2, pass 4)

Apply-changes pass against Worker 1's `## Final verification (Worker 1)` dispatch. Two one-line
comment repairs in `django_strawberry_framework/filters/inputs.py`, the file partition correction 2
already put in this cohort's ownership set. Worker 1 pinned the exact replacement wording; this pass
re-derived both against the **current** spec before applying, because Worker 1's own Decision-4 edit
landed after every prior measurement in this cohort.

### Files touched

Grounded in `git status --short`, run after both ruff invocations.

- `django_strawberry_framework/filters/inputs.py` — two comment lines, no executable statement.
  - **line 260, `_scalar_from_form_field`** (N1). `# table in spec-027 Decision 4 lists CharField as a recognized`
    -> ``# table in spec-027 Decision 4 lists ``CharFilter`` as a recognized``. The sentence claimed
    Decision 4's conversion table names `CharField`; it names `CharFilter`. Worker 1's pinned wording
    applied verbatim.
  - **line 522, `normalize_input_value`** (N2). `Per the spec-027 Implementation-discretion item, the`
    -> ``Per spec-027 Decision 4's ``normalize_input_value`` contract, the``. The old citation named a
    spec surface that has never existed. Worker 1's pinned wording applied verbatim.
- `docs/builder/bld-slice-4-027-broken_substring_citations.md` — this build report, checklist boxes 5
  and 6 ticked (markers only, box text untouched), `Status:` set to `built`.

Nothing else was written. `filters/base.py`, `filters/sets.py` and `types/finalizer.py` — landed and
reviewed in passes 1-3 — were not opened for edit.

### Tests added or updated

None. The diff changes comment text only; there is no behaviour to pin, and an assertion over a
comment's wording would pin a spelling rather than a contract.

### Validation run

**Baseline, stated explicitly.** `HEAD` was `7722c4b3` when this pass took its reference copy and is
`5c6fdd71` at its close — **it advanced a fourth time mid-pass**, after the three Worker 1 named.
`5c6fdd71 Move spec files around;` is the `spec-026` session archiving its own artifacts: its whole
diff is six `docs/builder/*-026*` paths (five `bld-*-026` deletions plus `build-026-*`), no `.py`, no
`-027` file, nothing this cycle owns. The reference copy is therefore still valid at the new `HEAD`,
proven rather than assumed — a fresh `git show HEAD:django_strawberry_framework/filters/inputs.py`
`cmp`s **identical** (exit 0) against the copy taken at `7722c4b3`, and the token proof below was
re-run against it after the move.

`filters/inputs.py` at `HEAD` carries **neither** this cycle's Slice 2 edits **nor** this cohort's
pass-3 `LOOKUP_PREFIXES` edit — both are uncommitted in the worktree. So `HEAD` is **not** "before
this pass", and the executable-token proof below covers the **accumulated** diff (Slice 2 + passes
1-4), which is the stronger statement. No `git stash` / `git checkout` / `git restore` /
`git worktree` was used; the `HEAD` reference was obtained read-only via `git show HEAD:<path>` into
a scratch path outside the repository.

| Gate | Command | Result |
|---|---|---|
| Format | `uv run ruff format django_strawberry_framework/filters/inputs.py` | `1 file left unchanged` |
| Lint | `uv run ruff check --fix django_strawberry_framework/filters/inputs.py` | `All checks passed!` |
| Source layout / ASCII-only | `uv run python scripts/check_trailing_commas.py --check django_strawberry_framework/filters/inputs.py` | exit **0** |
| Citation gate | `uv run python scripts/check_citations.py` | `OK: 742 citations resolve (665 in 422 .py files, 77 in KANBAN.md).` exit **0** |
| Focused tests | `uv run pytest tests/filters tests/types tests/test_registry.py tests/test_sets_mixins.py examples/fakeshop/test_query/test_library_api.py --no-cov -q` | **1316 passed in 59.43s** |

Never `ruff format .` or `ruff check .`; both write-mode runs were scoped to the one file this pass
touched. No `--cov*` flag appears anywhere in this pass.

**The `.py` half of the citation gate reads `665 in 422 .py files`** — the identical triple passes
1-3 and Worker 1's final verification recorded. That is the half this pass could have moved, and it
did not move: neither edited line is a `path::Symbol` or `#"..."` citation form, so
`check_citations.py`'s `CITATION_RE` matched neither of them before or after. The `KANBAN.md` half
reads 77, matching Worker 1's reading; `7722c4b3` is now in `HEAD`'s history, so its `KANBAN.md`
change is committed rather than dirty.

**Line budget and encoding.** Line 260 is **71** columns, line 522 is **69** — both well inside the
99 limit, so neither needed a re-wrap and E501's 110 grace was never in play. The file carries **0**
non-ASCII bytes (`LC_ALL=C grep -nP '[^\x00-\x7F]'` -> 0 lines), which the source-layout gate above
confirms independently.

**`git status --short` after both ruff invocations: 21 ` M` + 7 `??`, and every entry is this cycle's
own work.** Six package modules and thirteen test / fakeshop modules are Slice 2's
citation-and-provenance sweep plus this cohort's passes 1-4; `docs/SPECS/spec-027-filters-0_0_8.md`
is Slices 1/3 plus Worker 1's Decision-4 edit; the seven untracked files are the `-027` rationale and
the six `-027` build artifacts.

**Reported, not reverted, and not explained away: the fenced out-of-scope set now reads CLEAN.** The
dispatch fenced the `spec-024` / `spec-025` / `spec-026` spec, rationale, `build-*` and `bld-*`
files, `examples/fakeshop/apps/scalars/models.py`, and
`examples/fakeshop/test_query/test_scalars_api.py` as baseline-dirty, and named `KANBAN.md` /
`KANBAN.html` / `examples/fakeshop/db.sqlite3` as the plan's concurrent-writable set. None of them is
dirty any more. Cause, derived rather than assumed: the three commits Worker 1 named — `2d1f117c`,
`00a1cc4a`, `7722c4b3` — **committed** exactly that work (`git show --stat` on each names those
paths, `db.sqlite3` and both KANBAN renders included), and all three are ancestors of `HEAD`
(`git merge-base --is-ancestor 7722c4b3 HEAD` -> yes). **The `git status` snapshot carried in the
dispatch brief was stale**: its newest commit is `5842d23d`, three behind the `HEAD` this pass
started against and four behind the one it closed against. This is churn *disappearing*, not
appearing; it is attributable to commits; and none of those commits — nor the mid-pass `5c6fdd71` —
touched a file this cycle owns. `git diff --stat 7722c4b3..HEAD` names six paths, every one a
`docs/builder/*-026*` artifact; `git log --oneline 7722c4b3..HEAD -- django_strawberry_framework/ docs/SPECS/spec-027-filters-0_0_8.md docs/SPECS/appx/spec-027-filters-0_0_8-rationale.md`
returns nothing. (The same command with `docs/builder/` appended **does** return `5c6fdd71`, because
that directory holds both cycles' artifacts — a path filter at directory grain cannot separate them,
which is why the `--stat` file list above is the load-bearing evidence and the path filter is not.)
Nothing was reverted and nothing was tidied.

#### Executable-token identity against `HEAD`

`tokenize` both files, drop `COMMENT` / `NL` / `NEWLINE` / `INDENT` / `DEDENT` / `ENCODING` /
`ENDMARKER` and every statement-position `STRING` (a docstring), compare the surviving
`(type, string)` sequence.

| File pair | Tokens | Verdict |
|---|---|---|
| `git show HEAD:django_strawberry_framework/filters/inputs.py` vs worktree | **2759 vs 2759** | **IDENTICAL** |

2759 is the same figure this cohort's pass-3 instrument reported for this file; Worker 1's
independent instrument reported 2755 because it drops a different layout set. **The count is not the
measurement, the verdict is**, and every instrument in this cohort agrees on the verdict. So the
accumulated Slice-2-plus-passes-1-4 diff to this file contains no statement, branch, guard,
comparison, rejection path, or `raise` — the mechanical ground for the three `None` / `Not
applicable` subsections below.

#### This pass's own diff, isolated

`HEAD` cannot separate pass 4 from Slice 2 and pass 3, so the pre-pass-4 state was reconstructed
**outside the repo** by `sed`-reversing exactly the two edits this pass made, then diffed:

```text
260c260
<     # table in spec-027 Decision 4 lists CharField as a recognized
---
>     # table in spec-027 Decision 4 lists ``CharFilter`` as a recognized
522c522
<     Per the spec-027 Implementation-discretion item, the
---
>     Per spec-027 Decision 4's ``normalize_input_value`` contract, the
```

Two single-line substitutions, `260c260` and `522c522`. **No neighbouring line was touched and the
file's line count is unchanged at 1000**, so no comment was reflowed and no `path::Symbol` or
`#"..."` citation could have been wrapped across a line break by this pass. Lines 258-259 (two
``CharField`` mentions naming the `forms.CharField` branch the function actually tests) and lines
523-524 (the surviving half of the N2 sentence) are byte-identical.

#### Re-derivation against the post-Worker-1-edit spec

Both repaired citations were resolved against the spec **as it now stands**, not against the
dispatch's description of it. Decision bounds taken from `grep -n '^### Decision '` rather than from
any number written down in this artifact.

**N1 — Decision 4 names `CharFilter`, not `CharField`.**

- `### Decision 4` opens at spec line **482**; `### Decision 5` opens at **546**, so Decision 4 spans
  **482-545**.
- `awk 'NR>=482 && NR<=545' <spec> | grep -o 'CharField' | wc -l` -> **0**. Decision 4 does not carry
  the word at all.
- `grep -o 'CharField' <spec> | wc -l` -> **1** whole-spec, at spec line **857**, inside the
  `test_definition_relations.py` aside about `Book.circulation_status`. Unrelated to this branch.
- `grep -n 'CharFilter' <spec>` -> the Decision-4 hit is spec line **518**, the conversion table's
  first row, whose "the scalar Python type ... derived from the model field's `to_python`" is exactly
  this branch's `-> str` mapping. The `Decision 4` attribution therefore resolves, and only the class
  name inside the sentence was false.
- `grep -c '^### Decision 4 ' <spec>` -> **1**, so the heading the comment cites is unambiguous.

**N2 — the cited surface never existed; Decision 4 now carries the contract.**

- `grep -oi 'discretion' <spec> | wc -l` -> **0**. The spec has no discretion surface in any casing.
- `### Implementation discretion items` is a section of `docs/builder/ARTIFACT.md`'s **build-artifact
  template** (`ARTIFACT.md:44`) and of the per-cycle `bld-*.md` artifacts copied from it — a Worker 1
  plan section inside files pre-flight deletes. The old citation pointed at nothing durable.
- Decision 4's `normalize_input_value` contract paragraph now runs spec **526-530**: a lead-in naming
  **three** return shapes, then a scalar bullet, a `list` bullet, and — spec line **530** — a
  `dict[str, Any]` patch the caller merges into the form-data dict, closing with "what lets
  `_normalize_input` merge a multi-key filter's contribution **without inventing a sentinel-pair
  object** to carry the two halves."
- That supports the comment's surviving lines 523-524 word for word: `grep -n 'multi-key' <spec>` ->
  lines 526 and 530; `grep -o 'sentinel' <spec> | wc -l` -> **1**, on line 530. The repaired sentence
  now points at a durable contract that says what the sentence claims.

**Citation form.** Neither replacement uses a `#"unique substring"`, so the exactly-once rule does
not bite; each cites a heading (`spec-027 Decision 4`) whose text occurs once. That is deliberate and
matches the disposition this cohort took twice already: a substring pinned to prose is the fragility
class the cohort exists to repair.

### Failability proofs

None; this pass introduced no new boundary.

### Hot-path budget

Not applicable; plan declares no hot path.

### Floor verification

Not applicable; no floor-verification scope declared.

### Implementation notes

- **Worker 1's wording applied verbatim, its arithmetic re-derived.** The dispatch decided the
  wording and recorded the rejected alternative (keep `CharField`, drop the claim about the table);
  nothing about that judgement was reopened. What was re-derived is every number behind it, because
  the same spec edit that made N2's target true also moved N1's evidence — see the two corrections
  under `### Notes for Worker 1 (spec reconciliation)`.
- **The double-backtick form is the file's own convention, not an addition.** ``CharFilter`` matches
  the two ``CharField`` mentions two lines above it, so the repaired sentence reads as one comment
  rather than one sentence in two styles. It also makes the distinction the sentence exists to draw —
  the spec's `CharFilter` versus this branch's `forms.CharField` — visible at a glance.
- **Both edits are single-line by construction.** The replacement strings were length-checked before
  application (71 and 69 columns) precisely so no cascade re-wrap could be triggered; a cascading
  reflow is the mechanism that splits a citation across a line break, which is the defect class this
  cohort was opened to repair.

### Notes for Worker 3

- **Boxes 5 and 6 quote substrings this pass deliberately retired.** Box 5 cites
  `#"lists CharField as a recognized"` and box 6 cites `#"Implementation-discretion item"`. Both now
  return **0** hits in `filters/inputs.py` — that is the repair landing, not a miss. A builder may
  edit only the `- [ ]` / `- [x]` marker and never the box text, so both boxes are ticked with Worker
  1's original wording intact. Re-derive them against the *replacement* text
  (``lists ``CharFilter`` as a recognized``, ``Per spec-027 Decision 4's ``normalize_input_value`` contract``),
  which is what the diff shows.
- **`HEAD` is not "before this pass" for this file**, so an empty-`git diff` check would be
  meaningless here and a `git checkout` to obtain one would destroy Slice 2's and pass 3's
  uncommitted work. The two proofs offered instead are the executable-token identity against `HEAD`
  (covering the accumulated diff) and the reversed-edit reconstruction outside the repo (isolating
  this pass's own two lines). The tokenizer used lives in this session's scratchpad, outside the
  repository, and drops `COMMENT` / `NL` / `NEWLINE` / `INDENT` / `DEDENT` / `ENCODING` /
  `ENDMARKER` plus statement-position `STRING`.
- **Expect a smaller `git status` than the dispatch describes, and expect `HEAD` to have moved
  again.** The fenced baseline-dirty set is now committed, not reverted, and `HEAD` advanced a
  **fourth** time mid-pass (`5c6fdd71`, the `spec-026` session archiving its own artifacts) after the
  three Worker 1 named. Full attribution under `### Validation run`. Two things to carry into your
  own re-derivation: re-take the `HEAD` copy and `cmp` it (this pass did — byte-identical), and note
  that a `git log -- docs/builder/` path filter **cannot** separate this cycle's artifacts from the
  `-026` session's, because both live in that directory. Read the commit's `--stat` file list.

### Notes for Worker 1 (spec reconciliation)

No spec amendment is owed by this pass — Worker 1's own Decision-4 edit made N2's target true before
this pass repointed the comment at it, and N1 needed no spec change at all. Two record corrections
follow, both to numbers in the dispatch that its own spec edit invalidated. Neither changes a
disposition; both would mislead a later pass that copied them instead of re-deriving.

- **Where it lives:** `## Final verification (Worker 1)`, subsection
  ``### The two `inputs.py` Lows: decided, with a path that terminates``, paragraph **N1**.
  **Current wording:** "the whole spec carries `CharField` exactly **once**, at line 853, in a
  `test_definition_relations.py` aside about `Book.circulation_status`".
  **Recommended replacement:** "the whole spec carries `CharField` exactly **once**, at line **857**,
  in a `test_definition_relations.py` aside about `Book.circulation_status`". The claim's substance —
  one occurrence, in an unrelated aside — is re-derived here and holds; only the line number is
  stale, by exactly the four lines the same pass's Decision-4 edit added above it.
- **Where it lives:** same subsection, same **N1** paragraph, the bracketed command.
  **Current wording:** ``awk 'NR>=482 && NR<=541' <spec> | grep -c 'CharField'`` = **0**.
  **Recommended replacement:** ``awk 'NR>=482 && NR<=545' <spec> | grep -o 'CharField' | wc -l``
  = **0**. Two corrections in one line: Decision 4 now spans **482-545** (`### Decision 5` opens at
  546), and `grep -c` counts matching *lines* where the claim is about *occurrences*. The result is 0
  either way, so the disposition is unaffected — but a later pass copying the bound rather than
  re-deriving it would measure a Decision 4 four lines short of its real end.

The general form, for whichever pass writes the final gate: **a Decision's line bounds are a
measurement with a shelf life of one spec edit.** Take them from `grep -n '^### Decision '` at the
moment of use, never from a bound written down in an artifact — this one included.

---

## Review (Worker 3, pass 3)

Third Worker 3 spawn of this cohort, re-reviewing Worker 2 pass 4 against the accumulated
cohort diff. Every figure below was re-derived with this pass's own instruments; where it
agrees with a build report or an earlier review it is an independent agreement, and the
command is named either way. No `git stash` / `git checkout` / `git restore` / `git worktree`
was used, and no `--cov*` flag appears anywhere in this pass.

**`HEAD` was `5c6fdd71` at the start of this pass and `5c6fdd71` at its close** — the first
pass in this cohort during which it did not move. `git status --short` reads **21 ` M` + 7
`??`**, exactly Worker 2's roster, and every entry is this cycle's own work: the fenced
baseline-dirty set is committed, not reverted. Verified rather than accepted:
`git show --stat 5c6fdd71` names **six** `docs/builder/*-026*` paths and nothing else;
`git log --oneline -2 -- examples/fakeshop/apps/scalars/models.py examples/fakeshop/test_query/test_scalars_api.py`
names `7722c4b3` as the commit that took them; and `git merge-base --is-ancestor <c> HEAD`
returns yes for all four of `2d1f117c` / `00a1cc4a` / `7722c4b3` / `5c6fdd71`. Worker 2's
warning that a `git log -- docs/builder/` path filter cannot separate the two cycles' artifacts
is correct and is why the `--stat` file list above is the evidence used here.

**`git diff HEAD` is a clean instrument for this cycle for the first time**, so every
verification below runs against the whole 21-file diff rather than a per-file selection.

### High:

None.

### Medium:

None.

### Low:

#### L1 — the same never-existent citation surface N2 repaired is live at a parallel site in `filters/factories.py`

`django_strawberry_framework/filters/factories.py::FilterArgumentsFactory` (class docstring,
worktree line 95) reads:

```django_strawberry_framework/filters/factories.py:95
    class for the root filterset (per Implementation discretion item 5).
```

`### Implementation discretion items` is a section of [`ARTIFACT.md`][artifact]'s build-artifact
template and of the per-cycle `bld-*.md` files pre-flight deletes — the exact finding N2 was
opened on. Re-derived repo-wide, not inherited: `grep -rn 'discretion' --include='*.py' .`
returns **4** hits, of which `tests/test_connection.py:1600`, `mutations/resolvers.py:758` and
`mutations/resolvers.py:1093` belong to other cards, leaving `filters/factories.py:95` as the
**one** site in this card's tree. A sweep for the other build-artifact template section names
(`Implementation notes`, `Files touched`, `Notes for Worker`, `Spec slice checklist`,
`Hot-path budget`, `Build report`) returns **0** in any `.py`, so the class is bounded at this
one site rather than open-ended.

Why it matters, and why it is worse than N2 in one respect: N2's citation at least carried
`spec-027`, so an id-vocabulary sweep could reach it. This one names **no card at all**, so it
is invisible to a `spec-027` sweep and to a `Decision N` sweep alike — it sits in the
intersection of this cycle's deferred-catalog item 7 (bare references naming no card) and the
N2 class, and no prior artifact in this cycle mentions it (`grep -rn 'discretion item 5' docs/builder/*.md`
-> zero). `factories.py` has been in `git diff HEAD` since Slice 2, so it was in the diff every
pass of this cohort read.

**Why this is not `revision-needed`, and why it is not filed as a fix for Worker 2.**
`filters/factories.py` is **not** in this cohort's declared ownership partition (`base.py`,
`finalizer.py`, `sets.py`, plus `inputs.py` via partition correction 2) — it is Slice 2's file.
Worker 1's own N2 reasoning was "a cohort cannot close leaving false spec citations in a file
**it owns**"; that ground does not extend to a file it does not own, and a worker never writes
outside its cohort's ownership. Escalated to Worker 1 with the two resolution paths under
`### Notes for Worker 1 (spec reconciliation)` item 1. No test expectation: comment text.

#### L2 — Decision 4's rewritten `normalize_input_value` paragraph is true, and two of its three bullets under-enumerate the live cases

The paragraph is **correct** where it was previously false — see `### Decision 4's rewritten paragraph, read against the runtime`
below, which traces both retracted claims to the code. Two residues, both spec-side and both
custodian-only, so neither is a build defect and neither has a Worker 2 executor:

- the lead-in spells the contract `normalize_input_value(filter_instance, raw_value)` while the
  shipped signature is `normalize_input_value(filter_instance, raw_value, field_name=None)`, and
  `field_name` is what supplies the `<field>` prefix in the very `{<field>_0, <field>_1}` bullet
  the repaired line-522 comment now cites (`filters/sets.py::FilterSet._normalize_input` passes
  `field_name=form_key` at **both** call sites, so the two-argument spelling is the form no
  production caller uses). The two-argument spelling is inherited text, not new — but it sits on
  a line this pass rewrote and is now the pointer a reader follows;
- the **`list`** bullet enumerates `GlobalIDMultipleChoiceFilter` / `ListFilter` / `ArrayFilter`
  and omits the `BaseCSVFilter` family, which is a live fourth producer of that shape:
  `_FILTER_INPUT_KIND_TYPES` puts `BaseCSVFilter` at index 2, **ahead** of
  `(RangeFilter, _DjangoRangeFilter)` at index 3, and `issubclass(BaseRangeFilter, BaseCSVFilter)`
  is `True` (verified by import). So a `range` lookup declared through `Meta.fields` normalizes to
  a **list** via `_csv`, while a declared `RangeFilter` normalizes to the positional **dict** via
  `_range` — two shapes for one lookup name, and the paragraph names only the second. The
  **`dict`** bullet likewise states the two-key shape where `_normalize_range_value` drops
  `None`-valued axes (one key for a partial range, `{}` for neither); the spec does carry that
  case, but in the `## Test plan` rather than in the contract paragraph.

Routed to Worker 1 as item 2 below. Flagged rather than waved through because the paragraph was
rewritten precisely to close a **partial** claim fix, and an enumeration that omits one live
producer is the same shape one bullet down.

#### L3 — Worker 1's own final-verification numbers carry the same +4 spec shift Worker 2 corrected, at two further sites

Worker 2's two corrections are **both confirmed** (see below). The class is systematic rather
than two isolated slips: Worker 1's Decision-4 edit added four lines above spec line 526, so
**every** spec line number above it that Worker 1 wrote before its own edit is stale by exactly
four. Two sites beyond the two Worker 2 named, both re-derived here:

| Where | As written | Re-derived now |
|---|---|---|
| `### Spec slice checklist audit`, box 1 | `Accepts both raw` at spec line **530**, Decision 4 = **482-541** | line **534**; Decision 4 = **482-545** |
| `### Spec slice checklist audit`, box 2 | `Partial-finalize recovery` at spec **695, 835** | **699, 839** |
| `### Deferred work catalog` item 11 | occurrence at **835**; `## Edge cases and constraints` at **811**; Decision 11 spans **710-783**; Decision 12 opens at **784** | **839**; **815**; **714-787**; **788** |

No disposition moves: `Accepts both raw` is still **1** occurrence and still inside Decision 4;
`Partial-finalize recovery` is still **2**, so dropping the substring is still required; and
item 11's conclusion (the second occurrence is past Decision 11, under `## Edge cases and
constraints`, and Decision 11 carries zero occurrences) holds at the corrected numbers. The
catalog is what `bld-final-027.md` inherits, which is why it is worth correcting rather than
leaving. Routed as item 3 below.

### DRY findings

None. `scripts/review_inspect.py`'s `## Repeated string literals` section for
`filters/inputs.py` is **byte-identical** between `HEAD` and the worktree (3x `contains`, 2x
`istartswith`, 2x `week_day`, 2x `FilterSet`, 2x `field_name` — all pre-existing), and the
executable-token identity below means the accumulated diff can introduce no logic, literal,
helper, or near-copy at all. No abstraction was added, so the existence challenge has no
subject this pass.

### Verification I performed independently

| Claim under test | Instrument | Result |
|---|---|---|
| `HEAD` stable across this pass; the fenced set was committed not reverted | `git rev-parse`, `git show --stat 5c6fdd71`, `git log -- <scalars paths>`, `git merge-base --is-ancestor` x4 | **Holds.** `5c6fdd71` start and close; `5c6fdd71` = six `docs/builder/*-026*` paths only; `7722c4b3` took the scalars pair; all four commits are ancestors |
| Executable-token identity, **all 20 modified `.py` files** (not the four the cohort names) | own `tokenize` differ vs `git show HEAD:<path>`, dropping `COMMENT` / `NL` / `NEWLINE` / `INDENT` / `DEDENT` / `ENCODING` / `ENDMARKER` and every statement-position `STRING` | **IDENTICAL for all 20; divergent files: 0.** `filters/inputs.py` **2759 vs 2759** — my count reproduces Worker 2's figure exactly this pass, having differed in pass 2 |
| Pass 4's own two edits landed as pinned, and nothing else | `git diff HEAD -- inputs.py` read hunk by hunk against Worker 1's fenced replacement text; `wc -l`; `awk` column widths | **Holds.** Line **260** = `` # table in spec-027 Decision 4 lists ``CharFilter`` as a recognized ``, line **522** = `` Per spec-027 Decision 4's ``normalize_input_value`` contract, the ``; file still **1000** lines; widths **71** / **69**; lines 258-259 and 523-524 byte-identical |
| Neither replacement carries a `#"substring"`, so the exactly-once rule does not apply | own flatten-then-extract census, `HEAD` vs worktree | **Confirmed.** `inputs.py`'s `#"..."` multiset and its `path::Symbol` multiset are **both unchanged** by the whole accumulated diff, so no citation of either form was added, removed, or reworded there |
| No edit wrapped a citation across a line break | own flatten-first census plus a line-scoped unbalanced-`#"` detector, over all 20 modified `.py` files | **Zero new wraps.** `inputs.py` carries **zero** wrapped citations at `HEAD` and in the worktree. Three pre-existing wraps found, all byte-identical at `HEAD` — `finalizer.py:1383` (the catalogued exemplar) plus **two the catalog does not name**, `factories.py:15` and `factories.py:148` |
| Worker 2 correction 1: `CharField` is at spec **857**, not 853 | `grep -no 'CharField' <spec>`, `grep -o ... \| wc -l` | **HOLDS.** Exactly **1** occurrence, at line **857**, in the `test_definition_relations.py` aside about `Book.circulation_status` |
| Worker 2 correction 2: Decision 4 spans **482-545**, not 482-541 | `grep -n '^### Decision '` | **HOLDS.** `### Decision 4` at **482**, `### Decision 5` at **546**. `awk 'NR>=482 && NR<=545' \| grep -o 'CharField' \| wc -l` = **0** either way, so no disposition moves |
| The line-260 attribution resolves | read spec line **518** (Decision 4's conversion-table first row) | **Holds.** The row names `` `CharFilter` `` and maps it to "the scalar Python type ... derived from the model field's `to_python`", which is this branch's `-> str` mapping. `grep -c '^### Decision 4 ' <spec>` = **1** |
| The line-522 target exists and says what the sentence claims | read spec **526-530** against `filters/inputs.py::normalize_input_value` and `filters/sets.py::FilterSet._normalize_input` | **Holds**, in detail below. `grep -in 'discretion' <spec>` = **0**, so the retired citation named nothing |
| Boxes 5 / 6 quote substrings that are now absent | `grep -c` for both, plus `grep -n` for both replacements | Retired substrings **0** hits each; replacements **1** hit each, at 260 and 522 |
| Boxes 1-4 still landed, re-derived against the **post-edit** spec | `grep -no` / `grep -c` / `grep -rEn` | `Accepts both raw` **1** (line 534, inside 482-545), sites at `base.py` 553 and 692; `Partial-finalize recovery` **2** (699, 839) so the substring drop is still required, `Decision 9` heading unique, site at `finalizer.py:1226`; `TODO(spec-027` in `.py` = **0**, `TODO(spec-055 Slice 1)` at `sets.py:1369`; Decision 2 (379-403) carries **2** `construct_search`/`LOOKUP_PREFIXES`, Decision 3 (404-481) carries **0**, site at `inputs.py:81` |
| Worker 1's spec-edit byte and occurrence claims | `wc -c`, `grep -c` / `grep -o \| wc -l`, `grep -rn` for the anchor | **All four reproduce exactly.** Spec **255,828**; rationale **145,000**; `Claims this Decision may no longer make` occurs **8** times by both line and occurrence count; the only repo-wide hit for the anchor slug is Worker 1's own sentence in this artifact, so nothing links to it |
| Citation gate | `uv run python scripts/check_citations.py` | `OK: 742 citations resolve (665 in 422 .py files, 77 in KANBAN.md).` exit **0** — the `.py` triple is the identical `665 / 422` of every pass in this cohort |
| Source layout / ASCII-only / format / lint | `check_trailing_commas.py --check`, `ruff format --check`, `ruff check` (read-only forms) | exit **0**; `1 file already formatted`; `All checks passed!`. `LC_ALL=C grep -cnP '[^\x00-\x7F]'` -> **0** |
| Public surface | `git diff HEAD -- django_strawberry_framework/__init__.py` | **Empty**, exit 0 |
| Focused tests | `uv run pytest tests/filters tests/types tests/test_registry.py tests/test_sets_mixins.py examples/fakeshop/test_query/test_library_api.py --no-cov -q` | **1316 passed in 62.96s** — reproduces Worker 2's and Worker 1's figure at the same scope |

### Decision 4's rewritten paragraph, read against the runtime

This is the one place in the cohort where spec and code could still disagree, because both
replacements point into text Worker 1 wrote during this same cycle. I read spec **526-530**
against `filters/inputs.py` rather than against the comment citing it, and against the `HEAD`
version of the same paragraph to see exactly what changed.

The `HEAD` sentence (scratch copy of `git show HEAD:<spec>`, line 618) read:

```text
... (e.g., Enum member -> `enum.value`, `relay.GlobalID` object -> decoded `node_id`,
Strawberry range dataclass -> `{lookup}_from` / `{lookup}_to` keys).
```

Both false claims are gone and both replacements check out against the code:

- **scalar.** `normalize_input_value`'s `_gid` / `_gid_multi` riders call
  `filters/inputs.py::_encode_global_id_input`, which returns
  `relay.to_base64(value.type_name, value.node_id)` for a `relay.GlobalID` object — the base64
  **wire string**, exactly as the new bullet states, and the shape that helper's own docstring
  records as the fix for a wrong-type GlobalID passing the gate silently. `_choice` / `_catchall`
  ride `_unwrap_enum_member`, which returns `value.value` for an `enum.Enum` member, matching
  "an Enum member normalizes to `enum.value`";
- **dict patch.** `_range` calls `_normalize_range_value`, which returns
  `{f"{base}_0": start, f"{base}_1": end}` — positional, never `_from` / `_to`. The claim now
  agrees with the conversion-table row four lines above it instead of contradicting it, and with
  `sets.py::FilterSet._normalize_input`, whose **two** call sites both do
  `if isinstance(normalized, dict): data.update(normalized)`. That `data.update` is the literal
  referent of "a `dict[str, Any]` patch **the caller merges**" and of the surviving comment lines
  523-524, which spec line 530 now supports word for word (`grep -o 'sentinel' <spec> | wc -l` =
  **1**, on line 530; `grep -n 'multi-key' <spec>` -> 526 and 530).

The rationale companion carries the keyed retraction: `## Decision 4` grew
`### Claims this Decision may no longer make` naming both claims, with the decoded-`node_id` one
evidenced against `_encode_global_id_input` and the `_from` / `_to` one against `rev5 H3`, which
is recorded three bullets above in the same Decision's `### Changes this Decision underwent` as
already retracted. That is the keyed shape [`BUILD.md`][build] `## Spec rationale extraction`
requires, and it is looked up by Decision rather than by date.

**Verdict: the freshly-written paragraph is true against the runtime.** Its two
under-enumerations are L2 above, and neither touches the two sentences the repaired comments
actually cite.

### Checklist boxes 5 and 6 — the inverted tick-audit reading, judged

Both boxes quote a substring pass 4 deliberately retired, so a tick-audit that greps the box's
own quoted text reads **0 hits** and concludes "unaddressed" — the inverse of the truth. My
reading: **the ticks are correct, and Worker 2 was right to flag the inversion rather than
silently rely on it.**

- A box's contract is the **right-hand side of its arrow**, not the substring on the left. The
  left-hand substring is the *target identifier* — the thing the pass was dispatched to remove.
  Both right-hand sides landed: `` `CharFilter` `` at line 260, and `spec-027 Decision 4`'s
  `normalize_input_value` contract at line 522, both re-derived above against the replacement
  text.
- Worker 2 may edit only the `- [x]` / `- [ ]` marker, so leaving Worker 1's box text intact was
  the only lawful option; rewriting the box to quote the new text would have destroyed the
  record of what was repaired.
- The residual hazard is real and belongs to whoever audits next: a box whose quoted text is
  *supposed* to vanish is the one box where a grep-the-box-text audit is guaranteed wrong. Worker
  2's `### Notes for Worker 3` supplies the replacement vocabulary to re-derive against, which is
  the correct remedy and is why this is not a finding.

Boxes 1-4 are `- [x]` and all four contracts are still in the tree, re-derived above against the
**post-edit** spec rather than against the numbers in Worker 1's audit table (which is L3). No
box is silently unaddressed and none is ticked without a matching change. Six boxes, six ticks,
six landed contracts.

### Failability proofs — audit and re-run

Recorded by pass 4: `None; this pass introduced no new boundary.`

**Audited against the diff, not accepted from the report.** The executable-token identity above
is the mechanical ground, and this pass widened it from the cohort's four files to **all 20
modified `.py` files**: the `(type, string)` sequence of every one is `HEAD`'s, so this cycle's
entire `.py` diff — Slice 2's sweep plus this cohort's passes 1-4 — contains no statement,
branch, guard, comparison, gate, rejection path or `raise` for the mandatory floor to select.
The record is correct as written, and no proof should be manufactured for a comment edit.

**Boundaries re-run: none. Boundaries accepted on Worker 2's record: none.** The mandatory floor
(every boundary at 3-or-fewer recorded failing rows, plus every security / data-isolation
boundary) selects the empty set **legally**, under the one permitted condition — the diff
introduces no boundary at all. **The source carve-out was not exercised:** no transient mutation
was made, so there is nothing to revert and no byte-comparison to record.

No fail-open shape landed either, by the same proof: the diff contains no expression computing
an input to a limit, a size, a permission decision, or a rejection.

### Test staleness a focused run cannot see

Both shapes [`BUILD.md`][build] `### Test staleness a focused run cannot see` names are
**vacuous on this diff**, and the ground is a measurement rather than an argument: no example
model field was added, removed, or renamed and no wire-shape conversion occurred, because the
executable-token sequence of all 20 modified `.py` files is `HEAD`'s. There is no converted
field name to `grep -rn` across the three test trees, and no model field set for a `fields=` /
`exclude=` list to have gone stale against. Run independently of the cohort's file list, over
the whole `git diff HEAD` roster, per `worker-3.md`.

### `scripts/review_inspect.py`

**Decision: skipped for pass 4's own diff, and the skip is discharged by measurement rather than
by argument.** [`BUILD.md`][build] `### When to run the helper during build` fires for Worker 3
on a new `.py` file (none), a file under `optimizer/` or `types/` (pass 4 touched
`filters/inputs.py` only), or 30+ lines of new logic (zero). The accumulated-diff trigger via
`types/finalizer.py` was discharged in pass 2, and `finalizer.py` has not changed since — its
`git diff HEAD` is still the single `Decision 9` hunk pass 2 reviewed.

Rather than rest there, I ran the helper on `filters/inputs.py` and on a `HEAD` copy of the same
file held **outside** the repository, both with `--output-dir docs/shadow`:

```shell
uv run python scripts/review_inspect.py django_strawberry_framework/filters/inputs.py --output-dir docs/shadow
uv run python scripts/review_inspect.py <scratch>/headtree/django_strawberry_framework/filters/inputs.py --output-dir docs/shadow
```

`cmp` of the two `.stripped.py` outputs: **byte-identical**, and the two overviews'
`## Repeated string literals` sections are identical. The helper replaces every comment and
string-literal token with `...`, so its output is **provably invariant** under a comment-only
change to this file — which converts "the helper would tell me nothing new" from a claim into a
measurement. The extra `docs/shadow/inputs.*` pair written by the second run was removed;
`docs/shadow/` is regenerable and gitignored. No shadow-file line number is cited anywhere in
this review.

### Spec slice checklist walk

Walked in full; six boxes, all `- [x]`.

- Box 1 (`filters/base.py`, two sites) — **landed and correct.** `base.py` 553 and 692 both read
  `spec-027 #"Accepts both raw"`; the substring is **1** occurrence in the spec, at line **534**,
  inside Decision 4 (482-545), whose sentence states the contract both docstrings claim.
- Box 2 (`types/finalizer.py::_bind_filterset_owner`) — **landed and correct.** Line 1226 reads
  `Decision 9` with the substring dropped, which is still required: `Partial-finalize recovery`
  occurs **2** times (699, 839). `### Decision 9` is a unique heading.
- Box 3 (`filters/sets.py` staged anchor, a disposition decision) — **landed and correct.**
  `sets.py:1369` reads `TODO(spec-055 Slice 1)`; `grep -rEn 'TODO\(spec-027|TODO-(ALPHA|BETA|STABLE)-027' --include='*.py' .`
  returns **zero** tree-wide.
- Box 4 (`filters/inputs.py` `LOOKUP_PREFIXES`) — **landed and correct.** `inputs.py:81` cites
  `spec-027 Decision 2`; Decision 2 (379-403) carries **2** occurrences of
  `construct_search` / `LOOKUP_PREFIXES` and Decision 3 (404-481) carries **0**.
- Box 5 (`_scalar_from_form_field`) — **landed and correct**, per the inverted-reading section
  above. Line 260 names `` `CharFilter` ``, which spec line 518 confirms is what the conversion
  table's first row lists.
- Box 6 (`normalize_input_value`) — **landed and correct.** Line 522 cites Decision 4's
  `normalize_input_value` contract; the contract exists at spec 526-530 and supports the
  sentence's surviving half word for word, per the runtime read above.

### Hot-path budget

`Not applicable; plan declares no hot path.` **Audited:** the build plan's preamble declares
`Hot-path declaration: none`, and the 20-file token-identity proof means nothing executes
differently per request, per resolver, per row, per connection, or per outbound message. No
number is owed and none should be manufactured for a comment edit.

### Floor verification

`Not applicable; no floor-verification scope declared.` **Audited:** the build plan's preamble
declares `Floor-verification scope: none`; no pass in this cycle owed a floor run and none was
run. No scratch venv was created by this review, and nothing was installed into the shared
`.venv`.

### Public-surface check

`git diff HEAD -- django_strawberry_framework/__init__.py` is **empty**, exit 0, and the path
does not appear in `git status --short`. `__all__` and the re-export list are unchanged. The
cohort's Definition of Done item "no new public exports" holds.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md. `CHANGELOG.md` is fenced out of this cycle by
the maintainer and is absent from `git status --short`.

### Documentation / release sanity (only when the slice touches docs, release metadata, KANBAN, or archived specs)

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces. Pass 4's diff is two
`.py` comment lines plus this artifact. The one docs surface in the cycle's diff,
`docs/SPECS/spec-027-filters-0_0_8.md`, is Worker 1's custodian-only edit rather than this
cohort's build output; I read it end to end against the runtime anyway (see the Decision 4
section above) and re-derived its four stated byte and occurrence figures, all of which
reproduce exactly. `KANBAN.md`, `KANBAN.html`, `docs/GLOSSARY.md`, `docs/TREE.md`, `README.md`
and `examples/fakeshop/db.sqlite3` are all **clean** in `git status --short` this pass.

### What looks solid

- **The re-derivation discipline in pass 4 is the reason this pass was cheap.** Worker 2 applied
  Worker 1's wording verbatim while re-measuring every number behind it, and found two errors in
  its own dispatch. Both hold. That is the correct division: the judgement was the custodian's,
  the arithmetic was the builder's, and the builder did not defer to the custodian on a
  measurement.
- **The `HEAD`-move handling.** Worker 2 proved the mid-pass move harmless by `cmp`-ing a fresh
  `git show HEAD:` copy against the one taken before it, and named the reason a
  `git log -- docs/builder/` path filter cannot settle the question. Both reproduce.
- **The isolation proof for a pass whose file has no clean "before".** Reconstructing the
  pre-pass state outside the repo by reversing exactly the two edits, then diffing, is the right
  instrument where `HEAD` is not "before this pass" and `git checkout` would destroy Slice 2's
  and pass 3's uncommitted work. The `260c260` / `522c522` result plus an unchanged 1000-line
  count is a stronger statement than an empty `git diff` would have been.
- **Both replacements avoid a `#"substring"` deliberately**, and the reason given is the one the
  cohort established twice: a substring pinned to prose is the fragility class this cohort exists
  to repair. My census confirms neither replacement moved the `#"..."` population at all.
- **Worker 2 named the limit of its own green gate**: `check_citations.py`'s `CITATION_RE`
  matches neither edited line, so the unmoved `665 in 422` is not evidence these two citations
  resolve. It is not, and the resolution above is manual for exactly that reason.

### Temp test verification

- No temp test was written. `docs/builder/temp-tests/slice-4-027/` was not created.
- Nothing in this pass's diff is executable, so there is no behavior a temp test could pin and no
  assertion whose distinguishing power is in question. The instruments this pass used instead —
  a tokenizer, a flatten-first citation census, and two `review_inspect.py` runs — live in the
  session scratchpad **outside** the repository.
- Disposition: none to promote.

### Notes for Worker 1 (spec reconciliation)

1. **`Escalated:` L1 — `django_strawberry_framework/filters/factories.py::FilterArgumentsFactory`
   #"per Implementation discretion item 5" is the parallel site of the defect N2 repaired.**
   Evidence and boundedness under L1 above. It is **outside this cohort's ownership partition**,
   so the decision is yours, not a builder's. Two resolution paths:
   (a) **partition correction 3 + a Worker 2 pass 5** on `filters/factories.py` alone, mirroring
   exactly the reasoning that dispatched N1/N2 — the cohort's contract is "repair false spec
   citations", the file is this cycle's (Slice 2 wrote it), and the repair is one line whose
   wording is a custodian call: the docstring sentence states a real design contract
   (`arguments` returns the root filterset's built input class; the factory does not materialize
   module globals, which is the finalizer's phase-2.5 contract) that Decision 6 or Decision 9 may
   already carry, so the fix is likely a repoint rather than a deletion; or
   (b) **deferred-work catalog entry**, on the ground that `factories.py` is Slice 2's file and
   this cohort's dispatch is complete. If you take (b), note that catalog item 7 (bare
   `Decision N` references) does **not** cover it — this citation names no decision either, so a
   sweep by that item's vocabulary will not find it.
   My own reading favours (a): the class was declared closed by N2's repair, and a class declared
   closed with a live site left in the same cycle's diff is the shape that survives every later
   sweep.
2. **`Escalated:` L2 — two under-enumerations in Decision 4's rewritten `normalize_input_value`
   paragraph.** Both are yours alone (spec text, custodian-only) and neither has a Worker 2
   executor, so this is routed to you rather than filed as a fix. Evidence under L2. Suggested
   resolutions, both one clause:
   (a) spell the contract `normalize_input_value(filter_instance, raw_value, field_name=None)` in
   the lead-in, since `field_name` is what supplies the `<field>` prefix the dict bullet names
   and both production call sites pass it;
   (b) add the `BaseCSVFilter` family to the `list` bullet — "and the generated `BaseInFilter` /
   `BaseRangeFilter` (`BaseCSVFilter`) shapes `Meta.fields` `in` / `range` lookups expand into" —
   which also resolves the genuinely confusing case: a `range` lookup declared through
   `Meta.fields` takes the **list** shape (`BaseCSVFilter` precedes `(RangeFilter, ...)` in
   `_FILTER_INPUT_KIND_TYPES`), while a declared `RangeFilter` takes the **dict** shape.
   Optionally note in the dict bullet that `None` axes are dropped, so a partial range yields one
   key and an all-`None` range yields `{}`; the `## Test plan` already names the test that pins
   it.
   Neither is `revision-needed` material: the paragraph is **true** as written, and these make it
   complete.
3. **Record correction — the +4 spec shift reached your own final-verification numbers at two
   further sites.** Table and re-derivations under L3. Worker 2's two corrections
   (`CharField` at 857 not 853; Decision 4 = 482-545 not 482-541, measured by occurrences not
   `grep -c` lines) are **both confirmed independently here**; this is the same class at two more
   sites, one of them in the `### Deferred work catalog` that `bld-final-027.md` inherits.
   A worker may not edit a prior artifact, so recording it here is the whole disposition. Worker
   2's general rule is the right one and worth carrying into the final gate verbatim: **a
   Decision's line bounds are a measurement with a shelf life of one spec edit** — take them from
   `grep -n '^### Decision '` at the moment of use.
4. **Catalog enrichment, item 1 — two more exemplars of the wrapped-citation class, in a second
   file.** Item 1 names one exemplar (`finalizer.py` 1383-1384) and correctly prescribes
   "exemplar and an audit step, never a count". My flatten-first census over all 20 modified
   `.py` files found **two more**, both byte-identical at `HEAD`:
   `django_strawberry_framework/filters/factories.py` lines **15** and **148**, both wrapping
   `#"Auto-generation of ``FilterSet`` from ..."` across a line break. They surfaced only because
   this pass swept the whole cycle diff rather than the cohort's four files — which is itself the
   item's argument for an audit step. `check_citations.py` reports `OK: 742` with all three live,
   confirming the gate is blind to the class. Worth adding to the item so the card it becomes
   carries a second file, not just a second line.

### Process note for Worker 0 (not a finding against Worker 2)

The dispatch brief for this pass was **accurate in every particular I checked** — the two edited
lines, the two Worker 2 corrections, the four `HEAD` moves, the 21+7 tree state, and the
`git log -- docs/builder/` warning all reproduced. That is the first brief in this cohort where
nothing needed correcting, and it is worth recording as such, since the two prior briefs each
carried an error a re-derivation caught.

### Review outcome

`review-accepted`.

The dispatched contract landed exactly as pinned: two single-line comment repairs, no
neighbouring line touched, file still 1000 lines, executable-token identity holding against
`HEAD` for all 20 of this cycle's modified `.py` files, both repaired citations resolving to
spec text that is now true against the runtime, all six checklist boxes ticked with matching
implementations, and 1316 focused tests green.

Three Low findings, none of which a Worker 2 pass may close: L1 is in a file outside this
cohort's ownership partition and needs a partition decision only Worker 1 or Worker 0 can make;
L2 is spec text, custodian-only; L3 is a record correction inside a prior artifact, which no
worker may edit. All three are escalated above with resolution paths, per
[`ARTIFACT.md`][artifact]'s `review-accepted`-with-escalation route — the same routing test this
cohort's pass 2 established: an escalation must name a path that terminates in an actor who may
write the surface, and Worker 1 is that actor for all three.

`Status:` set to `review-accepted`.

---

## Build report (Worker 2, pass 5)

Apply-changes pass against Worker 3's pass-3 `L1`, dispatched by [`build-027-filters-0_0_8.md`][plan]
*Partition correction 3*. **One** comment line in `django_strawberry_framework/filters/factories.py`
— the third and last site of the never-existent-spec-surface class this cohort's `N2` opened.

### Files touched

Grounded in `git status --short`, run after both ruff invocations.

- `django_strawberry_framework/filters/factories.py` — one docstring line, no executable statement.
  - **line 95, `FilterArgumentsFactory` class docstring.**
    `class for the root filterset (per Implementation discretion item 5).`
    -> `class for the root filterset (per spec-027 Decision 6 subpass 4).`
- `docs/builder/bld-slice-4-027-broken_substring_citations.md` — this build report; `Status:` set to
  `built`. **No checklist box was ticked**: all six boxes in the Plan's
  `### Spec slice checklist (verbatim)` were already `- [x]` at pass 4, and this pass's contract
  (Worker 3's `L1`, dispatched through partition correction 3) has no box. A builder may edit only a
  box's marker, never add one, so the gap is recorded here and surfaced to Worker 1 below.

Nothing else was written. `filters/base.py`, `filters/sets.py`, `filters/inputs.py` and
`types/finalizer.py` — landed and reviewed in passes 1-4 — were not opened for edit.

### Tests added or updated

None. The diff changes docstring text only; there is no behaviour to pin, and an assertion over a
docstring's wording would pin a spelling rather than a contract.

### Validation run

**Baseline, stated explicitly.** `HEAD` was `5c6fdd71` at the start of this pass and `5c6fdd71` at
its close — the second consecutive pass during which it did not move (`git rev-parse HEAD` twice,
plus `cmp` of two independently taken `git show HEAD:<path>` copies, exit **0**).

`factories.py` at `HEAD` already carries **one** of this cycle's edits and not the other: Slice 2's
module-docstring repair (`(Decision 4 H1 / spec-027 lines 579-584)` -> `(spec-027 Decision 4)`, with
the following two lines re-wrapped) is **uncommitted in the worktree**, so `HEAD` is **not** "before
this pass". Two references were therefore taken, answering two different questions:

- a **pre-pass copy** of the worktree file, taken before any edit. `diff` against it isolates *this
  pass's* change: **one line**, lines 93-94 and 96 byte-identical, file still **172** lines. That is
  the proof that nothing reflowed, hence that no `path::Symbol` or `#"..."` citation was wrapped;
- a **read-only `HEAD` copy** via `git show HEAD:django_strawberry_framework/filters/factories.py`
  into a scratch path **outside** the repository. The token proof below runs against it and covers
  the **accumulated** diff (Slice 2 + this pass), which is the stronger statement.

No `git stash` / `git checkout` / `git restore` / `git worktree` was used anywhere in this pass.

**Executable-token identity, `filters/factories.py`, `HEAD` vs worktree.** Own `tokenize` differ,
dropping `COMMENT` / `NL` / `NEWLINE` / `INDENT` / `DEDENT` / `ENCODING` / `ENDMARKER` and every
statement-position `STRING` (a docstring), then comparing the `(type, string)` sequence:
**232 vs 232 tokens, IDENTICAL.** The accumulated diff on this file is comment/docstring text only.

| Gate | Command | Result |
|---|---|---|
| Format | `uv run ruff format django_strawberry_framework/filters/factories.py` | `1 file left unchanged` |
| Lint | `uv run ruff check --fix django_strawberry_framework/filters/factories.py` | `All checks passed!` |
| Source layout / ASCII-only | `uv run python scripts/check_trailing_commas.py --check django_strawberry_framework/filters/factories.py` | exit **0** |
| ASCII sanity, whole file | `LC_ALL=C grep -n '[^ -~]' django_strawberry_framework/filters/factories.py` | no match |
| Citation gate | `uv run python scripts/check_citations.py` | `OK: 742 citations resolve (665 in 422 .py files, 77 in KANBAN.md).` exit **0** |
| Column width | `awk` over lines 93-95 | **77 / 77 / 69** — the edited line is 3 columns *shorter* than the one it replaced |
| Focused tests | `uv run pytest tests/filters tests/types tests/test_registry.py tests/test_sets_mixins.py examples/fakeshop/test_query/test_library_api.py --no-cov -q` | **1316 passed in 61.20s** |

Never `ruff format .` or `ruff check .`; both write-mode runs were scoped to the one file this pass
touched. No `--cov*` flag appears anywhere in this pass.

**The `.py` half of the citation gate reads `665 in 422 .py files`** — the identical triple passes
1-4 and Worker 1's final verification recorded, and the half this pass could have moved. It did not:
the replacement is prose (`per spec-027 Decision 6 subpass 4`), not a `path::Symbol` or `#"..."`
form, so `CITATION_RE` matched neither the old text nor the new. `docs/` is out of the gate's scope
by design (its module docstring says so), so no spec-target citation is gate-checked either way.

**Churn classification.** `git status --short` after both ruff invocations reads **21 ` M` + 7 `??`**
— byte-for-byte the roster Worker 3 recorded at pass 3, with `filters/factories.py` already among
the 21 since Slice 2. No file entered or left the roster. Nothing was reverted.

### The re-derivation behind the repair

Every number below was measured during this pass, not inherited from the dispatch brief.

**1. The retired citation named a surface that has never existed.**

- `grep -rn --include='*.py' -i "implementation discretion" .` -> **1** hit, `filters/factories.py:95`.
  Repo-wide, the only site.
- `grep -rn --include='*.py' -i "discretion" .` -> **4** hits. The other three
  (`tests/test_connection.py:1600` "plan discretion item (a)", `mutations/resolvers.py:758`
  "the discretion-item", `mutations/resolvers.py:1093` "spec-038 plain-form auth-message discretion")
  belong to other cards and name no spec section.
- `grep -ci discretion docs/SPECS/spec-027-filters-0_0_8.md` -> **0**.
- Stronger than the brief required: `grep -rn -i "discretion" docs/SPECS/` -> **0**. That sweep is
  recursive, so it covers the whole archive — `ls docs/SPECS/spec-*.md | wc -l` = **56** specs, plus
  `NEXT.md`, plus the **86** files under `docs/SPECS/appx/` (`find docs/SPECS -type f | wc -l` =
  **145** in total). The surface has never existed in *any* spec, only in
  [`ARTIFACT.md`][artifact]'s build-artifact template (`### Implementation discretion items`) and in
  the per-cycle `bld-*.md` files pre-flight deletes.

**2. The sentence's surviving claim is true against the runtime.** Both halves:

- *"The factory does NOT materialize built classes as module globals; that is the finalizer's
  phase-2.5 contract."* — `grep -rn "materialize_input_class" --include='*.py'
  django_strawberry_framework/` puts every call site in `types/finalizer.py`
  (`_bind_sidecar_sets(_SidecarBindingSpec(..., materialize=materialize_input_class, ...))` at
  `finalizer.py:2002`) and **none** in `filters/factories.py` or in
  `utils/inputs.py::GeneratedInputArgumentsFactory._ensure_built`.
- *"``arguments`` returns the built input class for the root filterset."* —
  `utils/inputs.py::GeneratedInputArgumentsFactory.arguments` is
  `self._ensure_built(); return self.input_object_types[self.input_type_name]`, docstring
  "BFS-build the root set and return its input class."

**3. The spec surface that genuinely carries it is Decision 6, subpass 4.** Read, not assumed:

- `### Decision 6 — Finalizer phase-2.5 binding seam + materialize-before-`Schema` ordering` spans
  spec **568-601** (`grep -n '^### Decision '` at the moment of use: Decision 6 at 568, Decision 7 at
  602), and its **Subpass 4** paragraph (spec line **592**) states both halves in one sentence pair:
  "call `FilterArgumentsFactory(filterset_cls).arguments` to trigger Layer-5 BFS ... For each built
  class, **materialize as a real module global** of `django_strawberry_framework.filters.inputs` via
  the helper `materialize_input_class(name, cls)`." The subpass is a numbered step of the
  **finalizer's** phase 2.5, which is exactly the division the docstring asserts.
- Decision 9 (**659-703**) was read and **rejected** as the home: it owns the *namespace* and the
  *lifecycle contract* (idempotency, collision, `registry.clear()`, partial-finalize recovery), not
  the who-materializes division of labour.

**4. Citation form: no substring, deliberately.** `Subpass 4` occurs exactly **1** time in the spec
(line 592, inside Decision 6), so a `#"Subpass 4"` citation would satisfy the exactly-once rule.
It was still not used, for three reasons: the prose pointer `Decision 6 subpass 4` already resolves
to the same paragraph, so the substring adds no locating power; the spec's own heading text for it
(`Subpass 4 — Materialize input classes`) carries an em dash and could not be quoted in an
ASCII-only `.py`; and the twin repair this pass mirrors (pass 4's line-522 fix,
`Per spec-027 Decision 4's ``normalize_input_value`` contract`) landed as prose, so the two sites now
read the same way. `grep -c '^### Decision 6 '` -> **1**, so the pointer is unambiguous.
The module docstring of this same file already uses the identical form, `(spec-027 Decision 4)`.

### The class-closing sweep

Five axes, all run this pass over the whole package. The brief's axis was `per <Title Case Phrase>` /
`the spec's <section>`; axes 3-5 were added because the first two cannot see a pointer spelled any
other way, which is the mechanism that grew this cohort three times.

| # | Axis | Command | Result |
|---|---|---|---|
| 1 | `per <Title Case Phrase>` | `grep -rnoE "per [A-Z][A-Za-z_'\`-]+([ -][A-Z][A-Za-z_'\`-]+)*" --include='*.py' django_strawberry_framework/` then `uniq -c` | **10** distinct phrases. `per Decision`/`per Layer` excluded as the intended form. All 10 inspected individually (below) |
| 2 | `the spec's <section>` | `grep -rn --include='*.py' "spec's" django_strawberry_framework/` | **12** sites, all inspected |
| 3 | build-artifact template section names | 19 `grep -rn --include='*.py' -F "<name>"` runs repo-wide | **0** in the package. The only hits anywhere are `scripts/prove_failability.py` + `tests/test_prove_failability.py` (whose job IS to emit that subsection) and one `tests/test_export_dry_review.py` fixture string |
| 4 | `<Word> item <n>` pointers | `grep -rnoE "[A-Za-z-]+ item [0-9(]" --include='*.py' django_strawberry_framework/` | **1** site besides the repaired one: `filters/sets.py:2906` `Definition-of-done item 4(d)` — **resolves**; spec-027 DoD item 4(d) is `filter_queryset(self, queryset)`, exactly what that override is |
| 5 | `the spec <Cap>` / `(Spec <Cap>)` / `spec's <Cap>` | `grep -rnE "the spec [A-Z]\|\(Spec [A-Z]\|spec's [A-Z]" --include='*.py' django_strawberry_framework/` | **10** sites — 6 in `orders/`, 3 in `rest_framework/`, 1 at `routers.py:71` — all inspected |

**Axis 1, all ten phrases.** Three are spec pointers besides the repaired `per Implementation`:
`per Spec Decision` (**3** occurrences at `orders/__init__.py:60`, `orders/inputs.py:281`,
`orders/inputs.py:293`) and `per Spec DoD` (**1**, `orders/sets.py:13`). Both name spec-028 surfaces
that **exist**: `grep -n '^### Decision '` on `spec-028-orders-0_0_8.md` returns Decisions **1-13**,
so Decision 5 / Decision 8 all resolve, and spec-028 DoD item **4(c)** is "**NO `apply(...)`
dispatcher**", exactly what `orders/sets.py:13` cites it for. The remaining **seven** are not spec
pointers at all — `per RFC` (RFC 8259), `per EVENT`, `per PROCESS`, `per WRITABLE` (field),
`per Manager`, `per OrderSet`, `per FilterSet BUILD` are English quantifiers or symbol names.

**Axis 2, all twelve `spec's` sites**, enumerated so the split is auditable. **Ten** are
*descriptive* references to a spec's content rather than section-name citations, so there is no
surface for them to miss: `connection.py:971` ("the spec's cursor-supplied rules"),
`connection.py:1983` ("the spec's filter/orderBy wording"), `optimizer/lateral_fetch.py` 243 / 578 /
832 and `optimizer/single_parent_fetch.py:188` (a `DIRECT_FK` *fetch spec* — an unrelated sense of
the word), `schema.py:37` (the **GraphQL** spec), `utils/write_values.py:286`,
`management/commands/inspect_django_type.py:72`, `rest_framework/inputs.py:473`. The remaining
**two** do name a section, and both resolve: `filters/base.py:21` "the spec's single-symbol promise
(spec-027 Decision 2)" — Decision 2 (spec **379-403**) lists `RelatedFilter` as a single `base.py`
symbol and re-exports it from `filters/__init__.py`; and `routers.py:71` "the spec's Risks note" —
`## Risks and open questions` is at `spec-041-*.md:1947`.

**Verdict: the class is closed.** `filters/factories.py:95` was the **only** site in
`django_strawberry_framework/` citing a spec surface that does not exist. Everything else either
resolves or is not a spec pointer.

**What the sweep found that is NOT this class**, and is therefore reported rather than repaired: the
pointers spelled `per Spec Decision N` / `(Spec Decision N)` / `per Spec DoD 4(c)` / `the spec D8
step 4` / `the spec's Risks` are **card-less** — each names a real section of *its own* spec but no
`spec-NNN`, so a reader has to infer the document. That is this cycle's deferred-catalog **item 7**
class (bare references naming no card); it reaches `orders/`, `rest_framework/`, and `routers.py` at
the package root, none of which the catalog records, and none of it is a false citation. Enumerated
site by site under `### Notes for Worker 1 (spec reconciliation)` item 3.

### Failability proofs

None; this pass introduced no new boundary.

### Hot-path budget

Not applicable; plan declares no hot path.

### Floor verification

Not applicable; no floor-verification scope declared.

### Implementation notes

- **`subpass 4` is spelled lower-case in the pointer** while the spec's paragraph label is
  `**Subpass 4 — ...**`. Deliberate: the lower-case form is the spelling the spec itself uses in
  running prose ("Subpass 3 runs BEFORE subpass 4"), and it keeps the parenthetical from reading as a
  quoted heading, which is what a `#"..."` citation is for.
- **The sentence keeps its parenthetical rather than dropping the pointer.** The brief's fallback —
  state the invariant with no pointer — was available and was not needed: a genuine home exists, and
  the docstring's next-door claim (`the finalizer's phase-2.5 contract`) is exactly the vocabulary of
  Decision 6's heading, so the pointer earns its parentheses.
- **The two pre-existing wrapped citations in this file were left untouched** (`factories.py` lines
  15 and 148, both wrapping `#"Auto-generation of ``FilterSet`` from ``Meta.fields``" ` across a line
  break). They are catalogued, and lines **14-16** and **147-149** are byte-identical to the pre-pass
  copy (checked line by line, not inferred from the one-line diff). The edit at line 95 sits **80**
  lines below the first wrap and **53** lines above the second, so neither could be reached by a
  reflow even had one happened.

### Notes for Worker 3

- The whole diff for this pass is **one line**. The pre-pass copy diff in `### Validation run` is the
  cheapest way to see it in isolation; `git diff HEAD -- django_strawberry_framework/filters/factories.py`
  shows **two** hunks, because the module-docstring hunk is Slice 2's and predates this pass.
- The `tokenize` differ used for the identity proof lives outside the repository, at the session
  scratchpad, and is the same instrument passes 2-4 used. It drops statement-position `STRING`
  tokens, which is what makes a docstring edit invisible to it — the property being asserted.
- `Subpass 4` being a **unique** substring is the one place a reviewer might reasonably prefer a
  `#"..."` citation to the prose form landed here. The three reasons it was not used are in the
  re-derivation section, point 4; the em-dash one is dispositive for the heading text, the other two
  are judgement.

### Notes for Worker 1 (spec reconciliation)

1. **Decision 3's Layer 5 bullet contradicts Decision 6's subpass 4 and is false against the
   runtime.** This is the surface a reader following the *other* obvious pointer would land on, so
   the repaired docstring now disagrees with it.
   - **Where it lives:** `### Decision 3 — Six-layer lazy-resolution pipeline`, the **Layer 5**
     block, its fourth bullet (spec line **422** at the time of writing — secondary to the quote).
   - **Current wording:** "`FilterArgumentsFactory._ensure_built` produces both halves: it
     materializes each input class as a module global (via the helper `materialize_input_class(name,
     cls)` in `inputs.py` — two-argument signature; the destination module is always
     `django_strawberry_framework.filters.inputs` so it is not a parameter) AND it emits the
     `Annotated[...]` shape in field annotations so cycle-safe references between filtersets keep
     working."
   - **Why it is false:** `grep -rn "materialize_input_class" --include='*.py'
     django_strawberry_framework/` shows the only call site is `types/finalizer.py:2002`, passed as
     `materialize=materialize_input_class` into `_bind_sidecar_sets`. Neither
     `filters/factories.py` nor `utils/inputs.py::GeneratedInputArgumentsFactory._ensure_built`
     calls it. Decision 6's subpass 4 has it right; Layer 5's bullet does not.
   - **Recommended replacement:** "`FilterArgumentsFactory._ensure_built` emits the `Annotated[...]`
     shape in field annotations so cycle-safe references between filtersets keep working; it does
     **not** write module globals. Materialization is the finalizer's, via the helper
     `materialize_input_class(name, cls)` in `inputs.py` — two-argument signature; the destination
     module is always `django_strawberry_framework.filters.inputs` so it is not a parameter — called
     once per built class in phase-2.5 subpass 4 (see
     [Decision 6](#decision-6--finalizer-phase-25-binding-seam--materialize-before-schema-ordering))."
2. **This pass's contract has no checklist box.** All six boxes in the Plan's `### Spec slice
   checklist (verbatim)` were `- [x]` before this pass began, and `L1` was dispatched through
   *partition correction 3* in the plan rather than as a new box. A builder may edit only a box's
   marker, so if the audit wants the pass visible in the checklist, box 7 is yours to add — wording
   suggestion: "(added by Worker 1 — partition correction 3) `filters/factories.py::FilterArgumentsFactory`
   #\"per Implementation discretion item 5\" -> `spec-027 Decision 6 subpass 4`; the cited surface is
   an `ARTIFACT.md` template section; `grep -rn -i discretion docs/SPECS/` returns **0**."
3. **Catalog item 7's population is larger than the catalog records, and spans three more
   subpackages.** Item 7 (bare references naming no card) is scoped to `Decision N` refs. The
   class-closing sweep found the same shape spelled `per Spec Decision N` / `(Spec Decision N)` /
   `per Spec DoD 4(c)` / `the spec D8 step 4` / `the spec's Risks`. Enumerated rather than counted,
   because a count over a two-grep union rots the moment either grep's vocabulary changes — the
   reproducible form is
   `{ grep -rnE "per Spec (Decision|DoD)" --include='*.py' django_strawberry_framework/; grep -rnE "the spec [A-Z]|\(Spec [A-Z]|spec's [A-Z]|the spec D[0-9]" --include='*.py' django_strawberry_framework/; } | sort -u -t: -k1,1 -k2,2n`,
   whose output is **14** distinct sites: `orders/__init__.py:60`, `orders/factories.py:103`,
   `orders/inputs.py:222`, `orders/inputs.py:281`, `orders/inputs.py:293`, `orders/sets.py:13`,
   `orders/sets.py:120`, `orders/sets.py:318`, `orders/sets.py:451`, `orders/sets.py:461`,
   `rest_framework/__init__.py:13`, `rest_framework/resolvers.py:834`, `rest_framework/sets.py:48`,
   `routers.py:71`. Every one **resolves** to a real section of its own spec (spec-028 has Decisions
   1-13 and DoD 4(c); `## Risks and open questions` is at `spec-041-*.md:1947`), so none is a false
   citation — the defect is only that the reader must infer *which* spec. Worth carrying into the
   catalog so the card it becomes is scoped to the real population rather than to `filters/`.
4. **The one-line disposition of the repair, for the catalog:** the never-existent-surface class
   opened by `N2` had exactly **two** sites and both are now repaired — `inputs.py:522` in pass 4,
   `factories.py:95` here — with the boundedness proven by axes 1-5 of the sweep above rather than
   asserted. No further site in `django_strawberry_framework/` cites a spec surface that does not
   exist.

`Status:` set to `built`.

## Review (Worker 3, pass 4)

Third re-review of this cohort, over Worker 2's **pass 5**: one docstring line in
`django_strawberry_framework/filters/factories.py` (line 95), closing my pass-3 `L1`. Dispatched
through [`build-027-filters-0_0_8.md`][plan] *partition correction 3*. `HEAD` is `5c6fdd71` and
the tree carries **21 ` M` + 7 `??`** — this cycle's diff and nothing else — so `git diff HEAD` is
a clean instrument this pass. No `git stash` / `checkout` / `restore` / `worktree` anywhere.

### High:

None.

### Medium:

None.

### Low:

#### L1 — the closure claim's SCOPE SENTENCE is false: four live sites cite `Decision`s the spec they name does not have

The class as `N2` defined it — a pointer naming a spec-structural surface whose name has never
existed in **any** spec — **is** closed, and I verified that with my own instrument (below). What is
not true is the sentence the build report closes on, twice:

> "`filters/factories.py:95` was the **only** site in `django_strawberry_framework/` citing a spec
> surface that does not exist." (`### The class-closing sweep`)
> "No further site in `django_strawberry_framework/` cites a spec surface that does not exist."
> (`### Notes for Worker 1` item 4)

`grep -rn "spec-011" --include='*.py' .` returns **8** sites, **6** of them in shipped package
source. Four of the eight name a Decision:

```django_strawberry_framework/types/base.py:1174
       ``_validate_interfaces`` (spec-011 Decision 4).
```

- `types/base.py:1174` — `spec-011 Decision 4`
- `types/base.py:1778` — `spec-011 Decision 7 #"keeps every selected Django field including the primary key"`
- `types/base.py:1899` — the same citation again, inline
- `types/resolvers.py:558` — `spec-011 Decision 7`

`docs/SPECS/spec-011-stale_placeholder_cleanup-0_0_4.md` is **53 lines** and has **zero** `### Decision`
headings (`grep -cE '^### Decision ' -> 0`; its only sections are `## Card snapshot` and `## Scope`).
So `spec-011 Decision 4` and `spec-011 Decision 7` name a surface that does not exist in the document
they name. The remaining two source sites (`types/base.py:1041`, `:1043`) carry
`spec-011 #"An empty tuple is the same as not declaring"` and
`spec-011 #"may be a tuple/list of interface classes"`; each substring resolves **0** times in
spec-011 and **1** time in `spec-015-relay_interfaces-0_0_5.md`. Two more sites sit in tests
(`tests/filters/test_sets.py:451`, `tests/types/test_base.py:495`).

The real home is spec-015, whose Decision 4 is `validation` and Decision 7 is
`optimizer and projection invariants` — exactly what the two citations are about. **This is a
documented, never-fixed finding from a prior cycle:** `docs/builder/DONE/build-015-relay_interfaces-0_0_5.md`
finding `F14` records it as the `spec-011` renumber artifact (`81e4704d` renamed
`spec-011-relay_interfaces-0_0_5.md` -> `spec-015-…` without sweeping citations) at eight sites, and
the population is still eight.

Why it survived every gate: `scripts/check_citations.py` resolves only `path::Symbol` forms and its
module docstring puts `docs/` deliberately out of scope, so a `spec-NNN`-targeted citation is
invisible to it in both halves. And it survived this cohort's five-axis sweep because none of the
five axes has vocabulary for it: the pointer is spelled `spec-011 Decision N`, which is the
*intended* form, and axis 1 explicitly excludes `per Decision` / `per Layer` as intended.

**Severity and route.** Low, and **not** a defect in this pass's diff: all six sites are pre-existing
at `HEAD`, in `types/base.py` and `types/resolvers.py`, which are in **no** cohort's partition and are
not in this cycle's `git diff HEAD` at all. Nothing for Worker 2 to do. What must change is the
recorded claim, because the deferred catalog will inherit it: item 4's disposition sentence should be
scoped to the never-existent-surface class it actually proved, and the `spec-011` population should
enter the catalog as its own item. Routed under `### Notes for Worker 1` item 1.

#### L2 — the report's "states both halves in one sentence pair" overstates what subpass 4 says

`### The re-derivation behind the repair` point 3 says Decision 6's Subpass 4 "states both halves in
one sentence pair". Subpass 4 (spec line 592) states the first half outright — materialization is a
step of the **finalizer's** phase 2.5, performed via `materialize_input_class(name, cls)` after
`.arguments` is called — which is the docstring's load-bearing claim and the reason the pointer earns
its parentheses. It does **not** state the second half, `arguments` *returns* the built input class
for the root filterset: it names `.arguments` only as the Layer-5 BFS **trigger** and then speaks of
"each built class". The return semantics are stated in the code
(`utils/inputs.py::GeneratedInputArgumentsFactory.arguments`, docstring "BFS-build the root set and
return its input class"), not in that paragraph.

This does not make the citation wrong, and I am **not** asking for a re-word: Decision 6 subpass 4 is
the only *Decision* surface in the spec that names `.arguments` at all (the other three occurrences
are the slice checklist at line 69, the goals list at 127, and DoD item 10 at 980), so it is the
correct home by elimination as well as by vocabulary. Recorded because the artifact's own sentence is
what a later reader will treat as proven, and because this cohort has already been bitten once by a
citation that resolved, named the right mechanism, and described a slightly different contract.
**Disposition: rejected as a repair, recorded as a precision correction to the build report.**

### DRY findings

None. The diff contains no executable statement (proved below), so there is no logic, literal,
helper, or branch to consolidate, and no existence challenge to raise. The one shape worth naming as
a positive: the pass reused the citation form the file's own module docstring already uses
(`(spec-027 Decision 4)`) and that pass 4's twin repair landed at `inputs.py:522`, so the three
spec pointers in this pair of files now read identically rather than in three dialects.

### Verification I performed independently

Every figure below is my own measurement, taken this pass, not read off the build report.

| Claim | My instrument | Result |
|---|---|---|
| No executable change, `factories.py` | own `tokenize` differ vs `git show HEAD:…` into a scratch path outside the repo | **232 vs 232, IDENTICAL** |
| No executable change, the cohort's other five files | same differ vs `HEAD` | `filters/base.py` 2154, `filters/sets.py` 7315, `filters/inputs.py` 2721, `types/finalizer.py` 5530, `utils/inputs.py` 5370 — **all IDENTICAL** |
| File length unchanged | `wc -l` on both copies | **172 / 172** |
| Nothing reflowed at the two pre-existing wraps | `sed`-extract lines 13-17 and 145-151 from both copies, `cmp` | both **exit 0** |
| No citation wrapped by this pass | flatten-first census of `COMMENT`/`STRING` tokens, HEAD copy vs worktree | identical wrap sets (lines **15** and **148**); the edited line 95 carries no `#"` or `path::Symbol` form at all |
| Column width / ASCII / layout | `awk` widths 93-95, `LC_ALL=C grep '[^ -~]'`, `check_trailing_commas.py --check` | **77 / 77 / 69**, no match, exit **0** |
| Citation gate | `uv run python scripts/check_citations.py` | `OK: 742 citations resolve (665 in 422 .py files, 77 in KANBAN.md)` — the identical triple |
| Lint / format, read-only | `ruff format --check` + `ruff check` on the one file | `1 file already formatted`, `All checks passed!` |
| Focused suite | `uv run pytest tests/filters tests/types tests/test_registry.py tests/test_sets_mixins.py examples/fakeshop/test_query/test_library_api.py --no-cov -q` | **1316 passed in 61.22s** — Worker 2's figure reproduced exactly |
| Tree state | `git rev-parse HEAD`, `git status --porcelain` | `5c6fdd71`; **21 ` M` + 7 `??`** |

My `filters/inputs.py` count is **2721** where pass 4 recorded 2759 and Worker 1 recorded 2755: three
instruments, three drop sets, one verdict. The verdict is the measurement; the count is not.

**The seven earlier repaired sites are unchanged**, each re-read in the worktree rather than inferred
from the diff: `filters/base.py:553` and `:692` (`spec-027 #"Accepts both raw"`),
`types/finalizer.py:1226` (`spec-027 Decision 9`, substring dropped, `triggers the` dedup),
`filters/sets.py:1369-1373` (`TODO(spec-055 Slice 1)` + `spec-027 / Decision 2` provenance),
`filters/inputs.py:81` (`spec-027 Decision 2`), `:260` (` ``CharFilter`` `), `:522`
(`Per spec-027 Decision 4's ``normalize_input_value`` contract`). All five files are token-identical
to `HEAD`, so nothing executable moved under them either. I did not re-litigate any of the seven.

### The new pointer, judged

**Resolves, to the right contract, and the rejection of Decision 9 is correct.** Re-derived from
`grep -n '^### Decision '` at the moment of use, not from any written-down bound:

- Decision 6 spans spec **568-601** (Decision 7 opens at 602). **Subpass 4** is spec line **592** and
  sits inside it.
- Subpass 4 puts materialization in the finalizer: "call `FilterArgumentsFactory(filterset_cls).arguments`
  to trigger Layer-5 BFS … For each built class, **materialize as a real module global** … via the
  helper `materialize_input_class(name, cls)`." The docstring's claim — the factory does **not**
  materialize; that is the finalizer's phase-2.5 contract — is exactly this, and the pointer's
  vocabulary (`phase-2.5`) is Decision 6's own heading vocabulary. See L2 for the one half subpass 4
  states only implicitly.
- **Decision 9 (659-703) is correctly rejected.** I read it end to end: it answers "shares the
  `TypeRegistry` or has its own namespace", then carries the lifecycle contract (idempotency,
  collision `ConfigurationError`, `registry.clear()` co-clear, subsystem registration,
  partial-finalize recovery, the public `clear_filter_input_namespace()`). Nowhere does it divide
  labour between factory and finalizer. Citing it would have reproduced the pass-1 defect this
  cohort exists to repair.
- **The prose-over-substring choice is right, and one of its three stated reasons is dispositive.**
  `Subpass 4` occurs exactly **1** time in the spec (line 592; line 594's is lower-case), so
  `#"Subpass 4"` would satisfy the exactly-once rule and is pure ASCII — the em-dash argument rules
  out quoting the **full heading** (`Subpass 4 — Materialize input classes`), not a two-word
  substring, and the report says as much. The two judgement reasons carry it instead: the prose
  pointer already resolves to the same paragraph, and it matches both the file's own module docstring
  (`(spec-027 Decision 4)`) and the twin repair at `inputs.py:522`. `grep -c '^### Decision 6 '` -> 1,
  so the pointer is unambiguous.
- **The surviving claim is true against the runtime**, checked in the code rather than against the
  report: `utils/inputs.py::GeneratedInputArgumentsFactory.arguments` is
  `self._ensure_built(); return self.input_object_types[self.input_type_name]`, and `_ensure_built`'s
  body is a BFS over `pending` with a collision raise and `_build_class_type` calls — **no**
  materialization anywhere in it.

### The closure claim, re-derived with my own instrument

I did not re-run Worker 2's five axes. A closure claim is the one claim here that costs a whole loop
if wrong, and re-running the claimant's vocabulary inherits the claimant's blind spot, so I built
three instruments that enumerate a different population.

**Axis A — resolve every structural pointer's qualifier word in the target corpus.** The decisive
signature of this defect is that the pointer's distinctive qualifier appears **nowhere** in any spec
(`discretion` -> 0). Generalised: `tokenize` all **108** package `.py` files, keep every `COMMENT` and
`STRING` token (**11831** tokens), flatten whitespace, find every structural noun followed by an
ordinal (`decision|layer|subpass|phase|slice|non-goal|risk|dod|item|section|step|bullet|note|amendment|invariant|rule|checklist|table|appendix` + `[0-9]`/`(a)`/roman), take the four-word window before it,
and test each non-stopword against a flattened corpus of **every** file under `docs/SPECS/`
(specs + `appx/` + terms CSVs). **317 qualifier-word instances, 213 distinct words, 8 with zero
corpus hits** — and all 8 are ordinary English or symbol names adjacent to a pointer, none a claimed
spec surface: `dynamic-orderset`, `modelmultiplechoicefilter`, `over-consolidation`, `build-only`,
`leaf-shape`, `rerun's`, `type-cls`, `intervals`.

**The instrument is failable, and I proved it rather than asserting it.** Run unchanged against the
`HEAD` copy of `factories.py` (which still carries the pre-repair text), it reports exactly one
zero-hit qualifier:

```text
### 'discretion'  (1 site(s))
    headcopy/factories.py:76   ...ilt input class for the root filterset (per Implementation discretion item 5)...
```

So the empty result over the worktree is a measurement, not a silence.

**Axis B — the complete template-heading population, not a chosen 19.** Worker 2's axis 3 grepped 19
hand-picked build-artifact section names. I harvested **every** `^#+` heading from `BUILD.md`,
`ARTIFACT.md` and the four `worker-*.md` files — **158** multi-word names — and substring-matched each
against the same flattened comment/docstring corpus. **8 hits, all incidental English**: seven are
"validation run(s)" as a verb phrase (`filters/base.py:802`, `forms/sets.py:163`,
`rest_framework/resolvers.py:1353`, `rest_framework/sets.py:300`, `types/base.py:167`, `:196`,
`utils/write_transaction.py`), one is `types/base.py:122` "(… hoist, spec-032 integration pass)".
Zero template-section citations remain in the package.

**Axis C — numeric resolution, which is the axis that found L1.** For every package
comment/docstring, associate each `Decision N` with the nearest preceding `spec-NNN` in the same token
and test membership against that spec's actual `### Decision` set. **603** spec-anchored Decision
references checked (plus 129 bare ones, which are catalog item 7's class), **6** unresolved; two are
my associator's fault (`consumers.py:1` really says "Spec-046 Decision 16", which exists;
`extension.py:1053` is a bare `(Decision 11)` that borrowed spec-035 from earlier in the same
docstring) and the remaining **4** are `L1`.

**Verdict: the class Worker 2 was dispatched to close IS closed** — no site in
`django_strawberry_framework/` still cites a spec surface whose name has never existed, and the two
sites `N2` opened (`inputs.py:522`, `factories.py:95`) are both repaired. The **scope sentence** the
report closes on is what fails, per `L1`.

### The Decision-3-Layer-5 escalation, verified — and it is stronger than the report claims

**Confirmed on both sides.** Worker 1 owes a spec edit.

- **Spec side.** Decision 3 spans **404-481**; the Layer 5 block's bullet at spec line **422** reads
  "`FilterArgumentsFactory._ensure_built` produces both halves: it materializes each input class as a
  module global (via the helper `materialize_input_class(name, cls)` in `inputs.py` …) AND it emits
  the `Annotated[...]` shape …". Line 422 is where the report says it is.
- **Runtime side.** `grep -rn "materialize_input_class" --include='*.py' django_strawberry_framework/`
  puts the filter-side call site at exactly one place, `types/finalizer.py:2002`, passed as
  `materialize=materialize_input_class` into `_bind_sidecar_sets`. Neither `filters/factories.py` nor
  `utils/inputs.py::GeneratedInputArgumentsFactory._ensure_built` calls it — I read `_ensure_built`'s
  whole body. The bullet is false.
- **It contradicts Decision 6 subpass 4** (materialization is a finalizer subpass) and now the
  repaired docstring, exactly as the report says.
- **One thing the report missed, which strengthens it: the spec already contradicts itself inside
  Decision 4.** Spec line **507**: "The conditional runs on the `FilterSet`, NOT inside
  `FilterArgumentsFactory._ensure_built`: `_ensure_built` **only controls the Strawberry input
  shape**". Line **512** repeats it. So the recommended replacement does not introduce a new claim;
  it brings Layer 5 into line with what Decision 4 and Decision 6 both already say. That makes the
  edit strictly a correction, not a contract change — worth knowing before you weigh it.
- The recommended replacement text reads correctly against the runtime and preserves the
  two-argument-signature and destination-module notes. I have not edited the spec and will not: it is
  yours alone.

### Failability proofs — audit and re-run

`### Failability proofs` records `None; this pass introduced no new boundary.` **Audited against the
diff and confirmed mechanically, not read off the prose:** executable-token identity vs `HEAD`
(232 vs 232, IDENTICAL) means the accumulated diff to this file contains no statement, branch,
comparison, guard, rejection path or `raise` — so there is no boundary that could owe a proof. The
mandatory re-run floor (`worker-3.md` "Reading is necessary, not sufficient") is **legally empty**:
the diff introduces no boundary meeting it. Boundaries re-run: **none**. Boundaries accepted on
Worker 2's record: **none exist**. The same token proof independently discharges
`### Hot-path budget` and `### Floor verification` — no executable token changed, so no cost was
added and no framework seam was touched.

### `scripts/review_inspect.py`

**Run, not skipped — and the run is what proves the skip would have been correct.** None of the three
Worker-3 triggers fires (no new `.py` file; `filters/factories.py` is under neither `optimizer/` nor
`types/`; **0** lines of new logic by the token proof), so a recorded skip was licensed. I ran it
anyway, twice, because the comparison converts the judgement into a measurement:

```shell
uv run python scripts/review_inspect.py django_strawberry_framework/filters/factories.py --output-dir docs/shadow
uv run python scripts/review_inspect.py <scratch>/headcopy/factories.py --output-dir docs/shadow
cmp <worktree>.stripped.py <headcopy>.stripped.py   # exit 0
```

The two `.stripped.py` outputs are **byte-identical**, and the two `.overview.md` files differ only
in their two path header lines — so the helper is provably blind to a docstring-only diff and carries
no review signal for it. Django/ORM markers, repeated string literals, control-flow hotspots and
imports are all unchanged from `HEAD` by construction. I then **deleted** the two stray
`docs/shadow/factories.*` outputs the second run produced from an out-of-tree basename: leaving a
duplicate overview for the same source file would double-count that file's literals at the
integration pass's cross-file comparison. Only the canonical
`django_strawberry_framework__filters__factories.*` pair remains. No shadow line numbers are cited
anywhere in this review.

### Spec slice checklist walk

All **six** boxes in the Plan's `### Spec slice checklist (verbatim)` were already `- [x]` before this
pass began, and this pass ticked none. Walked each against the worktree anyway (see "the seven
earlier repaired sites are unchanged"): every tick still has a matching landed repair, so no box is
over-ticked and none is silently un-addressed.

**This pass's contract has no box, and Worker 2's handling is right.** Boxes 4-6 of this very
checklist were added by **Worker 1** at final verification, so the precedent inside this artifact is
unambiguous: adding a box is the custodian's act, and a builder that added a seventh would be writing
in Worker 1's section. Recording the gap in the build report plus supplying suggested wording is the
correct routing, and it terminates somewhere — Worker 1's final verification runs next regardless.
I read the suggested box-7 text and it is accurate as written: the target substring, the replacement,
the `ARTIFACT.md`-template provenance, and `grep -rn -i discretion docs/SPECS/` -> **0** all
reproduce. One amendment I would make if you take it: scope its closing clause to the class it
proved (see `L1`).

### Hot-path budget

`Not applicable; plan declares no hot path.` — correct, and independently grounded: the token proof
shows no executable token changed, so no per-request, per-resolver, per-row or per-connection cost
could have been added.

### Floor verification

`Not applicable; no floor-verification scope declared.` — correct on the same ground. A
docstring-only diff touches no Django / Strawberry / channels integration seam.

### Public-surface check

`git diff HEAD -- django_strawberry_framework/__init__.py` -> **empty**. `__all__` and the re-export
list are unchanged; this pass adds no public export. (Checked against `HEAD`, not a bare
`git diff`, since another session's commit can make a path-scoped `git diff` read clean.)

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity (only when the slice touches docs, release metadata, KANBAN, or archived specs)

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces. The only non-`.py` file
this pass wrote is its own `bld-*.md` artifact, which is the per-cycle scratchpad, not a doc surface.

### What looks solid

- **The pointer is the best available, and the report says why rather than asserting it.** Decision 6
  subpass 4 is the only Decision surface in the spec that names `.arguments`, its heading vocabulary
  is the docstring's vocabulary, and Decision 9 was read and rejected on the correct ground.
- **Every number in the build report reproduced.** 232 tokens, 172 lines, 77/77/69 columns,
  `742 = 665 in 422 + 77`, 1316 tests, 21 ` M` + 7 `??`, `Subpass 4` occurring once, Decision 6 at
  568-601, Decision 9 at 659-703, spec line 422, `finalizer.py:2002`. Fourth consecutive pass in
  this cohort where the figures held — and again the reason is that the report **enumerated** its
  populations (all 10 axis-1 phrases, all 12 `spec's` sites, all 14 catalog-item-7 sites) instead of
  asserting totals, so I could difference listings.
- **The two pre-existing wrapped citations were correctly left alone.** They are catalogued, not this
  pass's contract, and the report proved untouched-ness by line-by-line comparison rather than
  inferring it from a one-line diff.
- **The escalation is routed, not fixed.** `factories.py` was repaired; the spec was not touched by a
  builder. That is the boundary holding.
- **The five-axis sweep, while not closing what its verdict claims, is a real widening** — axes 3-5
  were added precisely because the dispatch brief's two axes cannot see a pointer spelled another
  way, which is the mechanism that grew this cohort three times. Axis 4 also resolved
  `filters/sets.py:2906` `Definition-of-done item 4(d)` against the DoD, which I re-checked.

### Temp test verification

No temp tests were written and none were needed: the diff contains no executable token, so there is
no behaviour a test could distinguish. `docs/builder/temp-tests/slice-4-027/` holds nothing from this
pass. My instruments (a `tokenize` corpus builder, the qualifier-resolution sweep, the complete
heading harvest, the numeric Decision resolver, an executable-token differ, and a flatten-first wrap
census) all live in the session scratchpad **outside** the repository, and the `HEAD` copies they read
were taken read-only via `git show HEAD:<path>`. Nothing was left in the tree.

### Notes for Worker 1 (spec reconciliation)

1. **`Escalated:` L1 — correct the closure claim's scope, and carry the `spec-011` population into
   the catalog as its own item.** Evidence under `L1`. Two things are needed and neither is a
   builder's:
   (a) **the recorded claim.** `### Notes for Worker 1` item 4 of pass 5 and the verdict paragraph of
   `### The class-closing sweep` both say no further package site cites a non-existent spec surface.
   Scope them to what was proven — "no site cites a spec surface whose **name** has never existed in
   any spec" — or the `final-accepted` record ships a false universal that every later sweep will
   trust.
   (b) **a new catalog item**, because item 7 (bare `Decision N` refs naming no card) does not cover
   it: these name a card, and the card is the wrong one. Population, enumerated rather than counted:
   `types/base.py` **1041, 1043, 1174, 1778, 1899**, `types/resolvers.py` **558**,
   `tests/filters/test_sets.py` **451**, `tests/types/test_base.py` **495**. Reproducible with
   `grep -rn "spec-011" --include='*.py' .`. The fix is a `spec-011` -> `spec-015` sweep across
   those eight sites (spec-015 Decision 4 is `validation`, Decision 7 is
   `optimizer and projection invariants`, and all three cited substrings resolve **1** time each in
   spec-015 and **0** in spec-011). It is **already documented**, in
   `docs/builder/DONE/build-015-relay_interfaces-0_0_5.md` finding `F14`, at the same eight sites —
   so the catalog entry should say "F14, re-confirmed unfixed at `5c6fdd71`", which is a stronger
   card than a fresh finding. All six source sites are pre-existing at `HEAD` and in **no** cohort's
   partition, so nothing re-loops for it.
2. **`Escalated:` the Decision-3-Layer-5 spec edit is yours and it is owed.** Verified above from both
   sides. Take the recommended replacement, or an equivalent that stops attributing materialization
   to `_ensure_built`. One addition to weigh: Decision 4 at spec lines **507** and **512** already
   says `_ensure_built` "only controls the Strawberry input shape", so this is a correction that
   removes an internal contradiction rather than a contract change — and after the edit, three
   surfaces (Decision 3 Layer 5, Decision 4, Decision 6 subpass 4) plus the repaired docstring all
   say the same thing.
3. **`L2` — the report's characterisation of subpass 4, corrected but not to be repaired.** Detail
   under `L2`. No `.py` change is wanted; the note exists so a later reader does not inherit
   "subpass 4 states both halves" as proven.
4. **My pass-3 `L2` and `L3` are still live and still yours.** Confirmed intact and unedited in
   `## Review (Worker 3, pass 3)` and its `### Notes for Worker 1`: `L2` (two under-enumerations in
   Decision 4's rewritten `normalize_input_value` paragraph) and `L3` (the systematic +4 spec-line
   shift above Worker 1's own Decision-4 insertion, at the checklist-audit boxes 1-2 and at deferred
   catalog item 11's four numbers). Pass 5 correctly said nothing about either — they have no Worker 2
   executor. Neither has been dropped; neither has been discharged.
5. **The wrapped-citation population is 6 package-wide, not the 3 my pass-3 review recorded.** My
   pass-3 census swept the cohort's **modified** `.py` files; run over all 108 package files it finds
   **38** `#"…"` openings of which **6** wrap across a line break: `factories.py` **15** and **148**
   (catalogued), `types/finalizer.py` **1383**, plus three the diff-scoped sweep structurally could
   not see — `consumers.py` **887**, `routers.py` **148**, `types/relay.py` **143**. All pre-existing
   at `HEAD`, all invisible to every line-bounded instrument in this repo including
   `check_citations.py`. My own earlier count was the understatement; correct the catalog to 6 and to
   the package-wide scope.
6. **Two smaller catalog observations, both pre-existing and out of partition.** `types/base.py:122`
   carries `(… hoist, spec-032 integration pass)` — a build-**process** phase named in shipped source,
   which is the provenance class the package bans rather than the spec-Decision pointer class it
   keeps. And `optimizer/extension.py:1053`'s bare `(Decision 11)` sits in a docstring whose only
   `spec-NNN` mention is spec-035, which has Decisions **1-9** — so a reader following the nearest
   card lands on a Decision that does not exist there. That belongs with catalog item 7, whose
   population pass 5 already widened to 14 sites.

### Review outcome

`review-accepted`.

Both `L1` and `L2` are Low, both are escalated to you rather than fixed, and **neither is a defect in
the `.py` diff** — `L1`'s sites are pre-existing at `HEAD` in files no cohort owns, and `L2` is a
precision correction to the build report's prose with an explicit recorded rejection of any repair.
The diff itself is one docstring line: it resolves, it resolves to the right contract, it is
executable-token-identical to `HEAD` on all six of the cohort's files, it wraps no citation, it leaves
the two catalogued wraps byte-identical, and the focused suite passes at 1316. `revision-needed` is
reserved for a defect in the `.py` diff, and there is none. The spec finding routes to your final
verification, which runs next regardless.

`Status:` set to `review-accepted`.

---

## Final verification (Worker 1, pass 2)

Fifth Worker 1 spawn of this cycle and the second `## Final verification (Worker 1)` section, per
the dispatch. Every figure below was measured by this pass's own instruments; where it agrees with a
build report or a review it is an independent agreement, and the command is named either way. No
`git stash` / `git checkout` / `git restore` / `git worktree` was used anywhere — the tree holds this
cycle's entire uncommitted diff.

**Baseline.** `HEAD` is `5c6fdd71` at the start of this pass and `5c6fdd71` at its close — the third
consecutive pass during which it did not move. `git status --porcelain` reads **21 ` M` + 7 `??`**,
byte-for-byte the roster Worker 2 pass 5 and Worker 3 pass 4 recorded.

- **Spec slice checklist:** audited below. Boxes 1-6 were `- [x]` on arrival and every contract is
  still in the tree; **box 7 is added and ticked by this pass** against its own re-derivation.
- **DRY check across this cohort and prior accepted slices:** no new duplication. Executable-token
  identity against `HEAD` holds for **all 20** modified `.py` files under this pass's own instrument,
  so the whole cycle's diff can introduce no logic, literal, helper, or near-copy at all.
- **Existing tests still pass:** `uv run pytest tests/filters tests/types tests/test_registry.py tests/test_sets_mixins.py examples/fakeshop/test_query/test_library_api.py --no-cov -q`
  -> **1316 passed in 61.05s**. No `--cov*` flag anywhere in this pass.
- **Spec reconciliation:** yes — four spec edits and three rationale edits, all under
  `### Spec changes made (Worker 1 only)`. None changes a contract Worker 2 implemented against, so
  none re-opens a build pass.
- **Floor verification:** `No floor-verification scope declared.` The build plan's preamble declares
  `Floor-verification scope: none`, no pass in this cycle owed a floor run, and none was run.
- **Final status: `final-accepted`.**

### Gates re-run by this pass

| Gate | Command | Result |
|---|---|---|
| Spec glossary | `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-027-filters-0_0_8.md` | `OK: 48 terms - all have glossary entries and at least one spec link.` exit **0**, re-run **after** every spec edit |
| Citation gate | `uv run python scripts/check_citations.py` | `OK: 742 citations resolve (665 in 422 .py files, 77 in KANBAN.md).` exit **0** |
| Source layout / ASCII-only | `uv run python scripts/check_trailing_commas.py --check docs/SPECS/spec-027-filters-0_0_8.md docs/SPECS/appx/spec-027-filters-0_0_8-rationale.md` | exit **0** |
| Focused tests | as above | **1316 passed** |

**The `.py` half of the citation gate reads `665 in 422 .py files`** — the identical figure every pass
in this cohort recorded. This pass wrote no `.py` file, so that is the half it could have moved and
did not. The `KANBAN.md` half reads 77, matching passes 4-5.

### Executable-token identity, all 20 modified `.py` files, and the instrument proved failable first

`tokenize` each file, drop `COMMENT` / `NL` / `NEWLINE` / `INDENT` / `DEDENT` / `ENCODING` /
`ENDMARKER` and every statement-position `STRING`, compare the remaining `(type, string)` sequence
against a read-only `git show HEAD:<path>` copy held outside the repository.

**IDENTICAL for all 20; divergent files: 0.** The six files this cohort owns report
`filters/base.py` 2158, `filters/factories.py` 232, `filters/inputs.py` 2759, `filters/sets.py` 7348,
`types/finalizer.py` 5567, `utils/inputs.py` 5397 tokens.

**Four instruments in this cohort now report three distinct token counts for the same file** — for
`filters/inputs.py`: Worker 2 2759, Worker 3 2721 (pass 4; its pass-3 run reported 2759), this pass's
predecessor 2755, and this pass 2759 — because each drops a different layout set. Counting the
instruments and counting the values are two different arithmetics and it is worth saying which:
**four instruments, three values, one verdict, and the verdict is the measurement.**

**The differ was proved failable rather than asserted.** Run unchanged against a mutated `HEAD` copy
of `filters/factories.py` (`_factory_label = "FilterArgumentsFactory"` -> `"MUTANT"`, one executable
token) it reports **DIVERGENT**; the mutation was then reverted and the restored copy `cmp`s
byte-identical against `git show HEAD:<path>` (exit 0), after which the differ reports **IDENTICAL**
again. So the 20 identical verdicts are a measurement, not a silence.

### Spec slice checklist audit

Every box was checked against the tree, not against the report that ticked it, and every spec-side
target was re-derived **after** this pass's own spec edits.

| Box | Contract | Verdict |
|---|---|---|
| 1 | `filters/base.py` x2 -> `spec-027 #"Accepts both raw"` | **LANDED.** Lines 553 and 692; `grep -o 'Accepts both raw' <spec> \| wc -l` = **1**, spec line **534**, inside Decision 4 (482-545) |
| 2 | `types/finalizer.py::_bind_filterset_owner` -> `Decision 9`, substring dropped | **LANDED**, and the pin needs a correction — see below. `Partial-finalize recovery` still occurs **2**x (spec 699, 839) so dropping it was required; `grep -c '^### Decision 9 ' <spec>` = **1** |
| 3 | `filters/sets.py` staged anchor, disposition decision | **LANDED.** Line 1369 reads `TODO(spec-055 Slice 1)` with the originating contract kept as non-TODO provenance; `grep -rEn 'TODO\(spec-027\|TODO-(ALPHA\|BETA\|STABLE)-027' --include='*.py' .` returns **zero** |
| 4 | `filters/inputs.py` `LOOKUP_PREFIXES` comment -> `Decision 2` | **LANDED.** Line 81; Decision 2 (379-403) carries **2** `construct_search` / `LOOKUP_PREFIXES` occurrences, Decision 3 (404-481) carries **0** |
| 5 | `filters/inputs.py::_scalar_from_form_field` -> `` ``CharFilter`` `` | **LANDED.** Line 260; Decision 4 (482-545) carries `CharFilter` **1**x and `CharField` **0**x; the whole spec carries `CharField` **1**x, at line **857**, in the unrelated `test_definition_relations.py` aside |
| 6 | `filters/inputs.py::normalize_input_value` -> `spec-027 Decision 4`'s `normalize_input_value` contract | **LANDED.** Line 522; `grep -oi 'discretion' <spec> \| wc -l` = **0**, and the surviving lines 523-524 (`multi-key` / `sentinel-pair`) are supported word for word by spec lines 526 and 530 |
| 7 | `filters/factories.py::FilterArgumentsFactory` -> `spec-027 Decision 6 subpass 4` | **LANDED, added and ticked by this pass.** Line 95; `Subpass 4` occurs **1**x, spec line **592**, inside Decision 6 (568-601); `grep -c '^### Decision 6 ' <spec>` = **1**; `grep -rn -i 'discretion' docs/SPECS/` returns **0** across the whole archive |

**No box was over-ticked and none needed un-ticking. Seven boxes, seven ticks, seven landed
contracts, and no box is left `- [ ]`, so no deferral reason is owed for any of them.**

**Box 2's pin was wrong in a way that matters more than the pin.** Both my prior final verification
and Worker 3's pass-2 walk recorded the citation as "line 1226" carrying `spec-027 Decision 9`. It
does not: a `grep -n 'spec-027 Decision 9' django_strawberry_framework/types/finalizer.py` returns
**nothing**, because the citation is **wrapped** — line 1225 ends `...per spec-027` and line 1226
begins `Decision 9).`. The contract landed and resolves for a reader; what is false is that any
line-scoped grep can find it. The wrap is **pre-existing at `HEAD`** (`git show HEAD:<path>` lines
1225-1226 read `per spec-027` / `Decision 6 #"Partial-finalize lifecycle")`), so pass 1 inherited it
and preserved it deliberately under its minimal-edit discipline rather than manufacturing it. This
widens the deferred catalog's wrapped-citation item to a second form; see item 1 below.

### The four routed items, decided

**1. Worker 2 pass 5 item 1 / Worker 3 pass 4 item 2 — Decision 3's Layer 5 bullet. CONFIRMED FALSE;
spec edited.** Re-derived from the runtime rather than from either report:
`grep -rn 'materialize_input_class' --include='*.py' django_strawberry_framework/` puts the
filter-side call site at `types/finalizer.py:2002`, where `materialize=materialize_input_class` is
handed to `_bind_sidecar_sets`; I read `_bind_filtersets` (the family wrapper) **and**
`_bind_sidecar_sets` (the shared implementation), and the actual invocation is a single
`spec.materialize(name, input_cls)` inside `_bind_sidecar_sets`'s subpass-4 loop. I then read
`utils/inputs.py::GeneratedInputArgumentsFactory._ensure_built`'s whole body: a BFS over `pending`, a
collision raise, and `_build_class_type` calls — no materialization anywhere. The replacement text was
re-derived rather than pasted; details and the divergence from Worker 2's suggestion are under
`### Spec changes made (Worker 1 only)` item 1.

**Worker 3's strengthening holds, and one half of it does not survive re-derivation.** Worker 3 cited
spec lines **507** and **512** as both saying `_ensure_built` "only controls the Strawberry input
shape". **Line 507 says exactly that; line 512 does not** — it says `_ensure_built` derives the input
field type from the resolved filter instances rather than from a parallel `FILTER_DEFAULTS` lookup,
which is an adjacent claim about where input *types* come from and is silent on materialization. So
the corrected inventory, re-derived rather than inherited, is:

- **Four sites affirmatively put materialization in the finalizer or deny it to `_ensure_built`:** the
  `## Slice checklist` phase-2.5 subpass-4 sub-bullet at spec **69**, Decision 4 at **507**,
  Decision 6's subpass 4 at **592**, and DoD item 10 at **980**.
- **Three more are consistent but name no actor:** the `## Slice checklist` bullet at **59** and DoD
  item 6 at **976** both state materialization in the passive voice, and **512** constrains
  `_ensure_built` without mentioning module globals at all.

Either way the conclusion Worker 3 drew stands and is what makes this a correction rather than a
contract change: after the edit, Decision 3 Layer 5, Decision 4, Decision 6 subpass 4 and the repaired
docstring all say the same thing, and nothing that was true before is false now. **The reason the false
claim survived is in the bullet's shape, not in anyone's attention:** it asserted two contracts joined
by `AND`, one of them true, and a bullet like that is audited as one claim. That is the transferable
finding, and it is recorded in the rationale.

**2. Worker 3 pass 3 L2 — Decision 4's `normalize_input_value` under-enumerations. CONFIRMED on both
halves; spec edited, and the fix was widened because the narrow one was a partial fix.**

- **`field_name`.** The shipped signature is
  `normalize_input_value(filter_instance, raw_value, field_name=None)`
  (`filters/inputs.py:496-500`), and `filters/sets.py::FilterSet._normalize_input` passes
  `field_name=form_key` at **both** call sites (lines 2267 and 2286), so the two-argument spelling is
  the form no production caller uses. **Worker 3 asked for the Decision 4 lead-in; the spec spells the
  two-argument form at seven sites** (lines 64, 387, 465, 526, 622, 635, 976). Fixing only the one a
  finding pointed at is the partial claim fix this cohort already recorded twice, so all seven were
  corrected in one count-asserted replacement.
- **`BaseCSVFilter`.** Verified by import rather than by reading:
  `issubclass(BaseRangeFilter, BaseCSVFilter)` and `issubclass(BaseInFilter, BaseCSVFilter)` are both
  `True`, `_FILTER_INPUT_KIND_TYPES` puts `BaseCSVFilter` at index **2** ahead of
  `(RangeFilter, _DjangoRangeFilter)` at index **3**, and the `_csv` rider returns a list while
  `_range` returns `_normalize_range_value`'s dict. So a `range` lookup declared through `Meta.fields`
  normalizes to a **list** and a filter declared as `RangeFilter` normalizes to the positional
  **dict** — one lookup name, two shapes.
- **The dict bullet's `None` axes.** `_normalize_range_value` (`filters/inputs.py:681-701+`) omits a
  `None`-valued axis, so a partial range yields one key and an all-`None` range `{}`. Worker 3 marked
  this optional; it is in, because "the two-key shape" reads as unconditional otherwise.

**3. Worker 3 pass 3 L3 — the `+4` spec-line shift. CONFIRMED, and it is a record-only item with one
live consequence.** Worker 3's four re-derivations all reproduce here (`Accepts both raw` at **534**;
`Partial-finalize recovery` at **699** / **839**; `## Edge cases and constraints` at **815**;
Decision 11 spanning **714-787** and Decision 12 opening at **788**), and no disposition moves at the
corrected numbers. A worker may not edit a prior artifact, so the two sites inside my own prior
`### Spec slice checklist audit` stand as written and are corrected in this pass's table above. **The
one that mattered is the fourth — inside the deferred-work catalog `bld-final-027.md` inherits — and
it is discharged by supersession rather than by correction:** the consolidated catalog below is a
fresh derivation at the current spec, so the stale numbers leave the gate's inheritance entirely.
Worker 2's rule is adopted verbatim: **a Decision's line bounds are a measurement with a shelf life of
one spec edit** — take them from `grep -n '^### Decision '` at the moment of use, this artifact
included.

**4. Worker 3 pass 4 L2 — "subpass 4 states both halves". CONFIRMED as an overstatement, and I am
taking the spec side rather than letting the precision correction stand alone.** Worker 3 is right on
the reading (subpass 4 names `.arguments` only as the BFS trigger and then speaks of "each built
class") and right to reject a docstring re-word (Decision 6 subpass 4 is the only Decision surface in
the spec that names `.arguments` at all, so there is no better target). But the code makes the
distinction load-bearing rather than pedantic: `_bind_sidecar_sets`'s subpass-4 loop reads the property
for its side effect — the statement is literally `_ = factory.arguments` — and then iterates
`factory.input_object_types`, which is *why* a class the BFS built for a reachable `RelatedFilter`
target gets materialized too and why a sibling root's factory sees those builds. That contract lived
only in a code comment. **A precision note in a build report closes with the cycle; the spec does
not** — so Decision 6 subpass 4 now states it, which makes the shipped docstring's citation true
rather than merely well-aimed. The alternative (leave it, keep the note) is recorded as rejected in the
rationale.

### Anchors and reference-style links, both files, both directions

`](#anchor)` uses resolved against the GitHub slug of every heading plus every explicit
`<a id="...">`; `[text][ref-id]` uses resolved against the definition block, and every definition
resolved back to a use. Fenced blocks stripped; inline code spans stripped for the ref-use scan only.

| File | headings | anchors | in-page uses | dangling | ref uses | defs | undefined | unused defs |
|---|---|---|---|---|---|---|---|---|
| `docs/SPECS/spec-027-filters-0_0_8.md` | 44 | 46 | 164 | **0** | 105 | 105 | **0** | **0** |
| `docs/SPECS/appx/spec-027-filters-0_0_8-rationale.md` | 82 | 43 | 68 | **0** | 62 | 62 | **0** | **0** |

Cross-file `#fragment` resolution as well, which my memory records as a blind spot four earlier
instruments shared: **97** definitions carry a fragment (63 in the spec, 34 in the rationale) and
every one resolves against the target file's own heading set. Duplicate-heading `-1` / `-2` variants
were generated before testing, and no use needed one.

**Indicted the instrument first, and it needed it twice.** A first run reported **3 dangling anchors
in both files** and **1 undefined ref-id** — all four false. The dangling three
(`decision-7--metafilterset_class-promotion-gate`,
`decision-8--relation-permission-cascade--get_queryset-cooperation`,
`decision-11--filter_input_typefilterset-consumer-helper`) came from my slug function stripping `_`
as a markdown emphasis marker, which GitHub does not do; the undefined `[0]` was
`extensions.errors["email_must_have_at_sign"][0]["message"]` inside an inline code span matching
`\]\[...\]`. Both were instrument bugs. This is the fifth cycle running in which a home-grown
slugger or citation parser indicted the file before itself.

### Summary

The cohort closes. Seven `.py` sites across five build passes, every one re-derived here against the
post-edit spec and resolving to the surface that carries the contract its sentence claims;
executable-token identity against `HEAD` holding for all 20 of this cycle's modified `.py` files under
a differ proved failable and reverted with a byte comparison; the staged-anchor sweep clean in shipped
source; the `.py` citation gate unmoved at `665 in 422`; the spec-glossary, source-layout and
anchor/ref gates green in both files and both directions; and 1316 focused tests passing. Four routed
findings are decided, three of them by spec edit and none by a further build pass. **The load-bearing
result is that the false claim this pass removed was contradicted outright by four other sites in its
own spec and still survived eight revisions, three slices, an integration pass and five build passes,
because it was the false half of a two-contract `AND` bullet and a bullet like that is audited as one
claim.**

### Spec changes made (Worker 1 only)

Every edit was applied by a count-asserted replacement script that writes **nothing** if any expected
occurrence count misses. Byte figures from `wc -c`, never `len(text)`.

1. **`docs/SPECS/spec-027-filters-0_0_8.md`, `### Decision 3 — Six-layer lazy-resolution pipeline`,
   the Layer 5 block's `_ensure_built` bullet (spec line 422, 1 occurrence expected, 1 found).**
   Triggered by Worker 2 pass 5 item 1 / Worker 3 pass 4 item 2. The bullet attributed module-global
   materialization to `FilterArgumentsFactory._ensure_built`, which never does it. It now states the
   half that is true (`_ensure_built` emits the `Annotated[...]` shape), states in bold that it does
   **not** write module globals, and hands materialization to the finalizer's phase-2.5 subpass 4 with
   the two-argument-signature and destination-module notes preserved verbatim.
   **Two departures from Worker 2's recommended replacement, both from re-deriving it:** (a) it names
   the call path at symbol grain — `types/finalizer.py::_bind_filtersets` as the filter-side entry
   point and the shared `_bind_sidecar_sets` as the loop that invokes the helper — because a finding
   derived from the family wrapper alone is a partial reading of the contract; and (b) it closes by
   naming Decision 4 as saying the same thing from the other side, which is what makes the edit
   legible as a correction rather than a new claim.
2. **Same file, `### Decision 4 — Upstream-primitives parity floor`, the `normalize_input_value`
   contract paragraph — lead-in plus the `list` and `dict` bullets (3 occurrences expected, 3 found).**
   Triggered by Worker 3 pass 3 L2. The lead-in now says what `field_name` is for; the `list` bullet
   names the `BaseCSVFilter` family as a fourth producer and spells the `Meta.fields`-`range`-versus-
   declared-`RangeFilter` split; the `dict` bullet says `<field>` is the `field_name` argument and that
   `None` axes are dropped.
3. **Same file, the two-argument spelling `normalize_input_value(filter_instance, raw_value)` at
   **seven** sites — lines 64, 387, 465, 526, 622, 635, 976 (7 occurrences expected, 7 found) —
   corrected to the shipped three-parameter signature.** Not requested by any finding: the finding
   named one site, and correcting only that one is the partial claim fix this cohort has now recorded
   three times. One of the seven is a `## Slice checklist` sub-bullet, whose text a per-cycle
   artifact may have copied as verbatim; the cost is recorded here and taken, because a spec that
   spells a shipped signature wrongly in six places is worse than a stale verbatim quote in a
   scratchpad that closes with the cycle.
4. **Same file, `### Decision 6 — ...`, `**Subpass 4 — Materialize input classes.**` (spec line 592,
   1 occurrence expected, 1 found).** Triggered by Worker 3 pass 4 L2. Adds what `.arguments` returns
   (the root set's own input class) and what the subpass-4 loop actually consumes (the factory's
   `input_object_types` ledger, which is why related-target builds and sibling roots are covered).
   Makes the shipped `filters/factories.py::FilterArgumentsFactory` docstring's citation true rather
   than merely well-aimed.

   Spec **255,828 -> 258,176 bytes** (`wc -c`) across edits 1-4. Line count unchanged — every edit is
   within-line — so no Decision's line bounds moved and no in-page anchor shifted.

5. **`docs/SPECS/appx/spec-027-filters-0_0_8-rationale.md`, `## Decision 3`,
   `### Claims this Decision may no longer make`.** The Layer-5 materialization claim recorded as
   retracted, with the runtime evidence and with the transferable form of the finding: **a bullet that
   states two contracts joined by `AND` is audited as one claim**, and the true half licensed the false
   one through eight revisions, three slices, an integration pass and five build passes.
6. **Same file, `## Decision 4`, `### Claims this Decision may no longer make`.** Two more
   retractions: that the `list` shape has exactly the three producers the bullet named, and that the
   runtime symmetric's signature is the two-argument form.
7. **Same file, new `## Integration consolidation cohort — the two additions that were not
   retractions`.** Records the Decision 6 subpass-4 addition and the two Decision 4 completeness
   clauses as *additions*, with the rejected alternatives (re-word the docstring to claim less; leave
   the precision note in the build report), so a later reader does not read them as rot this cycle
   introduced. Rationale **145,000 -> 149,253 bytes** (`wc -c`).

8. **This artifact's `### Spec slice checklist (verbatim)`, box 7 added and ticked.** Partition
   correction 3 grew the cohort to a seventh site after the checklist was written, all six existing
   boxes were already `- [x]`, and neither Worker 2 nor Worker 3 may add a box — the precedent is
   boxes 4-6, which I added at the prior final verification. Worker 3's amendment was taken: the
   closing clause is scoped to the never-existent-**name** class the sweep actually proved, and says
   explicitly that it does not close the wrong-**card** class. The tick is against this pass's own
   re-derivation of `filters/factories.py:95` and of `grep -rn -i 'discretion' docs/SPECS/` -> **0**,
   not against pass 5's report.

No status/header edit was owed. Spec lines 1-9 were re-read at the start of this pass: the
`Status: shipped (`0.0.8`)` line, the card id, the `0.0.8` target, the owner line, the predecessors,
and the rationale-companion pointer all still describe the build's current state.

### Deferred work catalog (consolidated for the final gate)

**This is the single list `bld-final-027.md` inherits.** It supersedes every earlier list in this
cycle: the five `### Notes for Worker 1` sections across this cohort's build reports and reviews, the
`### Deferred work catalog (consolidated for the final gate)` in my prior final verification, and
`bld-integration-027.md` `### Deferred work catalog (re-derived)`. Every item was re-derived here with
the command shown, at `HEAD` `5c6fdd71` and against the post-edit spec.

**Six inherited items were wrong and are corrected in place**, five of them in their **subject** rather
than their count. A catalog is a claim; this cycle's catalogs have now been wrong nine times across
three passes.

Nothing below is `revision-needed` material: every item is a fenced file, another card's tree, an
already-carded cluster, or a class whose population no instrument in this repo can close.

1. **A citation split across a line break, invisible to every line-bounded instrument — and the class
   has TWO forms, not one.**
   - **Form A, a wrapped `#"substring"`: six sites package-wide.** `filters/factories.py` **15** and
     **148**, `types/finalizer.py` **1383**, `consumers.py` **887**, `routers.py` **148**,
     `types/relay.py` **143**. Independently reproduced here by a flatten-first census over all
     **108** package `.py` files, confirming Worker 3's pass-4 correction. **Correction to the
     inherited item:** my prior catalog named one exemplar and a diff-scoped population of three; the
     scope was the cohort's modified files, which structurally cannot see the other three. The three
     inside this cycle's diff are byte-identical to `HEAD` (line-range `diff` against a `HEAD` copy,
     exit 0 for all three), so none is this cycle's.
   - **Form B, a `spec-NNN` token whose qualifier sits on the next line: 44 sites package-wide.** This
     form is **not a defect** — it is what ordinary comment wrapping at 99 columns produces, and every
     one reads correctly. It is an **audit hazard**: `types/finalizer.py:1225-1226` is why box 2's pin
     in two prior artifacts said "line 1226 carries `spec-027 Decision 9`" when
     `grep -n 'spec-027 Decision 9'` over that file returns nothing. **Any sweep or audit of a
     `spec-NNN <qualifier>` pointer must flatten before matching**, or it reports a live pointer as
     absent. One of the 44 (`filters/sets.py:1372-1373`) was created by this cohort's own pass-1
     retarget; that is normal wrapping, not a regression.
   - **Card the class with the exemplars and an audit step, never a count.**
     `scripts/check_citations.py`'s `CITATION_RE` is line-scoped and puts `docs/` out of scope by
     design, so it reports `OK: 742` with every Form-A wrap live; no existing instrument in this repo
     can measure either form. *Source: this artifact, Worker 3 pass 1 items 5 / pass 2 item 3 / pass 3
     `### Verification I performed independently` / pass 4 item 5.*
2. **`spec-011 Decision 4` / `Decision 7` cited at eight `.py` sites when `spec-011` has no
   Decisions — ALREADY CARDED, do not re-card.** Population re-derived by
   `grep -rn 'spec-011' --include='*.py' .`: **8** sites, **6** in shipped package source
   (`types/base.py` **1041, 1043, 1174, 1778, 1899**; `types/resolvers.py` **558**) and 2 in tests
   (`tests/filters/test_sets.py:451`, `tests/types/test_base.py:495`).
   `docs/SPECS/spec-011-stale_placeholder_cleanup-0_0_4.md` is **53** lines with
   `grep -cE '^### Decision ' -> 0` and only `## Card snapshot` / `## Scope`. The real home is
   `spec-015-relay_interfaces-0_0_5.md` (Decision 4 `validation`, Decision 7
   `optimizer and projection invariants`), and each of the three cited substrings resolves **1** time
   there and **0** times in spec-011 — verified here, not inherited.
   **Correction to the routed item, and it is the most load-bearing one in this catalog:** Worker 3
   proposed entering this as a new catalog item and noted it is `build-015`'s finding `F14`, "still
   unfixed". Both halves are true and the conclusion is wrong — **it is already homed on two live
   KANBAN cards**, with a *more precise* population than the finding: `TODO-ALPHA-051-0.0.15`
   (`KANBAN.md` line **249**) owns the eight live-code / test occurrences with the per-file counts, the
   retarget target, an explicit "do not widen into a documentation sweep" boundary, **and a recorded
   re-derivation trap** (`git grep -oh '\[spec-011\]' | wc -l` reports **9**; the ninth row is git's
   `Binary file examples/fakeshop/db.sqlite3 matches` line); `TODO-ALPHA-052-0.1.0` (`KANBAN.md` line
   **353**) owns the documentation half, 43 occurrences across 13 files. So this entry exists to stop
   the next author filing a duplicate: **re-confirmed unfixed at `5c6fdd71`, population still 8, owner
   still 051/052.** Pre-existing at `HEAD`, in no cohort's partition, and `check_citations.py` is blind
   to it by design. *Source: this artifact, Worker 3 pass 4 L1 and item 1.*
3. **`types/base.py:122` names a build **process** phase in shipped source.** Re-derived present: the
   comment reads "byte-identical at three compose sites (3rd-copy hoist, spec-032 integration pass)".
   A spec Decision pointer is the KEEP class; a build-cycle phase name is the banned class. Another
   card's file, in no cohort's partition. *Source: this artifact, Worker 3 pass 4 item 6.*
4. **Card-less prose pointers naming a real section of an unnamed spec: 14 sites, reaching
   `orders/`, `rest_framework/` and the package root.** Re-derived with Worker 2's own reproducible
   union command: `orders/__init__.py:60`, `orders/factories.py:103`, `orders/inputs.py:222`,
   `orders/inputs.py:281`, `orders/inputs.py:293`, `orders/sets.py:13`, `orders/sets.py:120`,
   `orders/sets.py:318`, `orders/sets.py:451`, `orders/sets.py:461`,
   `rest_framework/__init__.py:13`, `rest_framework/resolvers.py:834`, `rest_framework/sets.py:48`,
   `routers.py:71`. **Every one resolves** to a real section of its own spec, so **none is a false
   citation** — the defect is only that the reader must infer which document. Enumerated rather than
   counted, because a count over a two-grep union rots the moment either grep's vocabulary changes.
   *Source: this artifact, Worker 2 pass 5 item 3.*
5. **Bare `Decision N` references whose card attribution is ambiguous — and the exemplar the reviews
   named is resolvable, at four sites rather than one.** The class is card **attribution**, not count:
   most of these belong to other cards, so the population cannot be swept by number, only resolved
   site by site. **Correction to the routed item:** Worker 3 pass 4 named
   `optimizer/extension.py:1053`'s bare `(Decision 11)`. Line 1053 carries no such reference;
   `grep -n 'Decision 11' django_strawberry_framework/optimizer/extension.py` returns **four** sites —
   **671**, **991**, **1081**, **1499** — and 1081 is the one inside the docstring whose only
   `spec-NNN` mention is `spec-035` (which has Decisions **1-9**, so a reader following the nearest
   card lands on a Decision that does not exist). The referent is resolvable and worth writing into
   the card: `spec-030-connection_field-0_0_9.md` `### Decision 11 — The connection field owns its
   optimizer cooperation point`, which is exactly what line 1499's sentence is about. The fix is to
   spell `spec-030 Decision 11` at all four; it belongs to the connection / optimizer card.
   Second confirmed exemplar, unchanged: `utils/inputs.py` carries two `no operator bag, Spec
   Decision 8` refs meaning **spec-028**'s Decision 8, not this card's.
   *Source: `bld-integration-027.md` item 5; this artifact, Worker 3 pass 4 item 6.*
6. **Raw source-line and spec-line references, which `AGENTS.md` rule 27 allows only in per-cycle
   scratchpads. Three sub-kinds, enumerated — the total has now moved three times for three different
   reasons, which is why this item carries no total.**
   - **Spec / doc line refs in package comments (7):** `optimizer/walker.py:836`
     ("edge case line 315"), `mutations/sets.py` **503, 508, 671, 1339**, `orders/inputs.py` **167,
     227**.
   - **Raw line refs into this repo's own source (2):** `mutations/fields.py:32` and
     `mutations/resolvers.py:1150`, both "(``relay.py`` line 287)".
   - **Refs into the external upstream cookbook (4):** `orders/sets.py` **94, 179, 256, 312**
     ("cookbook lines 30-38", "265-285", "279-280", "115-170"). Expressible as
     `path::Symbol` against the vendored upstream tree, so the same rule reaches them, but they are
     not refs into this repo.
   - **Five in `examples/fakeshop/test_query/test_products_api.py`**, lines **2948, 2984, 3015, 3051,
     3098**, all re-derived present and all spelled as bare `(line 388)` / `(mirror line 493)` inside
     that file's `036` mirror block — so a sweep by the token `spec-036` finds none of them.
   - **Corrections to the inherited item, three of them:** the two once attributed to
     `_strawberry_patches.py` are the `#L45-L52` fragment of a **single** GitHub permalink pinned to a
     commit sha (`_strawberry_patches.py:218`) — an upstream reference, not a raw line ref, and the
     instrument's `L[0-9]` alternative is what manufactured them; my own prior correction of "13 to
     11" was measured with the narrower vocabulary and reads **13** under a wider one, but **not the
     same 13** — the two additions are `optimizer/walker.py:836` and `mutations/fields.py:32`, neither
     of which any prior list carried. *Source: `bld-integration-027.md` items 6 and 7; my prior final
     verification item 8.*
7. **The same broken / ungated citation class in other cards' trees.** Confirmed live by reading, in
   ten files: `orders/factories.py`, `mutations/resolvers.py`, `mutations/inputs.py`,
   `mutations/sets.py`, `rest_framework/{resolvers,serializer_converter,sets,inputs}.py`,
   `forms/inputs.py`, `types/base.py`. Exemplars: `rest_framework/serializer_converter.py`
   #"``annotate_queryset_relation`` after" (a bare `M3:` review-finding id) and
   `rest_framework/inputs.py` #"even when DRF ``required=True``" (a bare `H3`). Every one belongs to
   another card; the count is instrument-dependent for the same reason as items 4-6.
   *Source: `bld-integration-027.md` item 7, `bld-slice-2-027` out-of-scope table.*
8. **History-narrating prose in `.py` comments — a real class whose population is
   instrument-dependent.** Three instruments over the same file set disagree: ~65 across 15 files, 54
   across 11, 46 across 11. All three include legitimate contrast prose (a docstring saying what a
   fixture is *not* is not build provenance), so no number is a population. Confirmed exemplar all
   instruments agree on, re-confirmed here at `filters/inputs.py:593`:
   `django_strawberry_framework/filters/inputs.py::_encode_global_id_input`
   #"The previous implementation eagerly decoded the object". **Card the class with the exemplar and an
   audit step, never a count.** *Source: `bld-integration-027.md` item 4.*
9. **`docs/TREE.md` line 859 renders `(spec-021)` for `examples/fakeshop/apps/library/filters.py`, and
   `KANBAN.md` line 5256 carries a second live `spec-021` reference to this card. Both FENCED —
   maintainer items, never fixes here.** Slice 2 fixed the module docstring
   (`grep -rn 'spec-021' --include='*.py' .` returns **zero** tree-wide) but `docs/TREE.md` is
   script-rendered and was never regenerated, and `spec-021` today names a **different** card
   (`docs/SPECS/spec-021-apps-0_0_7.md`, the `AppConfig` card), which makes the row actively wrong
   rather than merely stale. **The fix is `uv run python scripts/build_tree_md.py`, owned by whoever
   owns doc-wrap, and never a hand-edit** — the next render reverts one. `KANBAN.md` line 5256 reads
   "Ref: spec-021 pre-merge review M-filters-3 / H-filters-3" under a board Decision note; `KANBAN.md`
   is DB-generated, so that one is an ORM edit plus a regenerate, not a text fix.
   *Source: this artifact, Worker 2 pass 1 and Worker 3 pass 1 item 2; my prior final verification
   item 2.*
10. **`README.md` carries zero occurrences of `filter_input_type`. FENCED.** Re-derived:
    `grep -c 'filter_input_type' README.md` = **0**, against a `## Doc updates` bullet that names it
    alongside `FilterSet` / `RelatedFilter` / `Meta.filterset_class` (all three present at the `0.0.8`
    line) and argues explicitly why the helper belongs there. **The one genuinely undischarged
    `## Doc updates` obligation in the cycle**, found only by reading a surface a prior slice had
    declared unexamined. *Source: `bld-integration-027.md` item 10. Licensing spec line: the
    `## Doc updates` `README.md` bullet — which licenses the work, not the deferral.*
11. **`docs/SPECS/spec-055-search_fields-0_1_2.md` carries three wrong references to this card.
    FENCED (another card's spec).** Re-derived: lines **29** and **195** both attribute
    `construct_search` / `LOOKUP_PREFIXES` to "spec-027 Decision 3 Layer 5" — the identical false
    attribution this cohort repaired at both live `.py` sites, and `spec-055` is the document the next
    author copies from, so it is the propagation source; line **200** quotes the staged anchor as
    `TODO(spec-027-filters-0_0_8 Meta.search_fields card 0.1.2)`, wrong in the id (pass 1 retargeted
    it to `TODO(spec-055 Slice 1)`) **and** already wrong at `HEAD` in the `card 0.1.2` suffix the real
    comment has never carried. *Source: this artifact, Worker 3 pass 1 item 1 and Worker 2 pass 1
    `### Notes for Worker 1`.*
12. **Four `test_clear_tolerates_unimportable_*` docstrings describe a retired mechanism.**
    Re-derived: `tests/test_registry.py` lines **1617 / 1651 / 1687 / 1721**, and
    `grep -c 'except ImportError' django_strawberry_framework/registry.py` = **0**. All four describe
    the cycle-safe local-import guards `register_subsystem_clear(...)` replaced; each test still proves
    something real (poisoning `sys.modules` leaves the registry's own clear undisturbed), so this is
    docstring rot, not a dead test. **Only the `filter` one belongs to this card**; the others name
    spec-028 / spec-030 / spec-032. *Source: `bld-integration-027.md` item 2.*
13. **The PEP-563 deferred-annotation path for `filter_input_type` has no dedicated test.**
    Re-derived: `grep -rn 'test_filter_input_type_under_future_annotations' --include='*.py' .`
    returns **0**, and `test_filter_input_type_is_idempotent_under_repeated_calls` — the repeat-safety
    property PEP 563 depends on — exists (**1** definition). A coverage boundary, not an untested
    contract; the spec's `## Test plan` says so in as many words. **Correction to the inherited item:**
    it recorded "zero hits tree-wide", which is no longer true and was self-falsifying by
    construction — writing the finding down populates the grep. There are now **3** tree-wide hits, all
    prose in this cycle's own artifacts and rationale discussing the absence. Scope the claim to `.py`.
    *Source: `bld-integration-027.md` item 3. Licensed by the `## Test plan`'s own sentence.*
14. **`docs/builder/bld-integration-027.md` `### Citation audit` mis-attributes the second
    `Partial-finalize recovery` occurrence to Decision 11.** Re-derived at the current spec: the
    occurrence is line **839**, under `## Edge cases and constraints` (line **815**); Decision 11 spans
    **714-787** and Decision 12 opens at **788**, so line 839 is past both and Decision 11 carries zero
    occurrences. The disposition that sentence supports — drop the substring — is unaffected. A record
    correction only; a worker may not edit a prior artifact. *Source: this artifact, Worker 2 pass 1
    and Worker 3 pass 1 item 3.*
15. **The `## Non-goals` auto-generation sentence is already carded — do not re-derive it as new
    rot.** `KANBAN.md` `TODO-ALPHA-051-0.0.15` carries the WP-D contract question that gates it. Acting
    on it would pre-empt a decision this cycle does not own. *Source: `bld-integration-027.md` item 9.*
16. **`[fakeshop-test-library-reload]` resolves to two different files across the spec / rationale
    pair, deliberately.** The spec's def points at `conftest.py` (Slice 3's fix); the rationale's still
    points at `test_library_api.py`, because its only use is the verbatim `rev7` entry whose subject is
    the claim naming that file. Recorded so a future sweep reads it as a decision rather than an
    unfinished fix. *Source: `bld-integration-027.md` item 12.*
17. **Worker 3 pass 4 deleted a stray out-of-tree-basename shadow pair, and the deletion holds.**
    Verified here: `ls docs/shadow/` carries the canonical
    `django_strawberry_framework__filters__factories.{overview.md,stripped.py}` pair and **no**
    `factories.*` duplicate, so the integration pass's cross-file `## Repeated string literals`
    comparison cannot double-count that file's literals. Recorded as discharged rather than deferred.
    *Source: this artifact, Worker 3 pass 4 ``### `scripts/review_inspect.py` ``.*

**Closed, so the gate does not carry them forward as open:** the three broken `#"substring"` citations
(integration item 1) landed in passes 1-2; the `filters/inputs.py` `LOOKUP_PREFIXES` attribution landed
in pass 3; the two `inputs.py` Lows (N1 / N2) landed in pass 4 as checklist boxes 5-6; the
never-existent-**name** class closed in pass 5 with `filters/factories.py:95` as box 7, its
boundedness proved by Worker 2's five axes and Worker 3's three independent ones; M2's corrected
citation populations were enumerated in pass 2 and reproduced twice since; the staged anchor was
retargeted in pass 1 and the `spec-055` half of it is item 11 above; and Decision 3's Layer 5 bullet,
Decision 4's two under-enumerations, the seven-site signature spelling and Decision 6 subpass 4's
return contract are all discharged by this pass's spec edits.

`Status:` set to `final-accepted`.

---

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

[artifact]: ARTIFACT.md
[build]: BUILD.md
[integration]: bld-integration-027.md
[plan]: build-027-filters-0_0_8.md
[slice-2]: bld-slice-2-027-citation_and_provenance_rot.md

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->

