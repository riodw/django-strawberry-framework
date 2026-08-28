# Build: R3 — retired-vocabulary sweep

Spec reference: `docs/SPECS/spec-033-connection_optimizer-0_0_9.md` (`### Decision 6 — Refusal arms, divergent aliases, hints, and scalar-only connections`, read in full before any wording was written; `### Decision 5`'s `last: 0` degrade sentence; `### Decision 11` for the module map), plus `docs/SPECS/spec-030-connection_field-0_0_9.md` `### Decision 11 — The connection field owns its optimizer cooperation point` for the two re-qualified citations
Status: review-accepted

## Plan (Worker 1)

This round was dispatched by Worker 0 against the population `bld-033-review-2-py_comment_repair.md` `### Low 7` and `### Notes for Worker 3` item 4 measured but could not write: the retired `### Decision 6` heading noun stranded across the tree by this cycle's own Slice 2 rewrite, plus four findings routed forward from the pass-3 review.

### Dispatched findings checklist

One box per file in the measured population, plus one per routed finding.

- [x] **P1.** `django_strawberry_framework/optimizer/nested_planner.py` — 4 occurrences of the retired `fallback shape(s)` noun, including the round's known-hardest site `::plan_connection_relation #"for each Decision-6 fallback shape"`, "a live citation carrying both retired spellings at once - the hyphenated `Decision-6` and the retired noun"
- [x] **P2.** `tests/optimizer/test_walker.py` — 3 occurrences, one of them the deliberately-left simile `#"behaves exactly like the other fallback shapes"`, which the pass-3 reviewer amended to "1 of 13, not a singleton, and should be retired with them or not at all"
- [x] **P3.** `tests/test_relay_connection.py` — 3 occurrences
- [x] **P4.** `django_strawberry_framework/optimizer/lateral_fetch.py` — 1 occurrence, `#"The walker-owned fallback shapes (sidecar, SKIP, DISTINCT, malformed slice, unwindowable join)"`, "the same five-item list R2 repaired in `nested_fetch.py`'s module docstring, one word different"
- [x] **P5.** `django_strawberry_framework/optimizer/nested_fetch.py` — 1 occurrence, `::NestedConnectionRequest #"every strategy-independent fallback shape has been ruled out"`, the **singular** a plural-only sweep cleared the file against
- [x] **P6.** `tests/optimizer/test_nested_fetch.py` — 1 occurrence, wrapped across two docstring lines
- [x] **R-a.** Routed: `optimizer/lateral_fetch.py` and `optimizer/nested_planner.py` "carry the retired vocabulary and were outside the previous cohort's partition. They are inside yours."
- [x] **R-b.** Routed: "A correct bare `Decision 11` became ambiguous because R2 re-sited a `spec-033 Decision 11` two list items above it: `tests/optimizer/test_extension.py`, where the surviving bare reference is **spec-030's** Decision 11, not spec-033's. Qualify it so the spec it belongs to is unambiguous." — **closed in pass 2.** Pass 1 qualified the two `tests/optimizer/test_extension.py` references the dispatch named, and deferred by name the site the finding actually describes, `django_strawberry_framework/connection.py::_finalize_queryset #"the connection field's own cooperation point, Decision 11"`, which was outside the writable list. Worker 0 added that one file mid-flight; pass 2 qualified it to `spec-030 Decision 11` and surveyed every other bare `Decision N` in `connection.py` (14 references, 2 qualified, 12 graded house convention with a named reason each).
- [x] **R-c.** Routed: "`optimizer/nested_fetch.py:214` still carries the **singular** retired noun; a plural-only sweep cleared the file's other sites and missed it." (same site as P5)
- [x] **R-d.** Routed: "Whatever you cannot close cleanly, record as an explicit deferral naming the site rather than ticking a box." — one deferral recorded (R-b's real site), one measured-and-deliberately-left population recorded (`### Implementation notes`).

---

## Build report (Worker 2)

### Files touched

Grounded in `git status --short` after both ruff invocations. Changed-line counts are `diff -u <baseline copy outside the repo> <working tree>` counting `^[+-][^+-]` rows, i.e. against **this pass's own baseline**, not `HEAD` — five of the seven files were already dirty with R2's accepted work when this pass opened them.

| file | +/- lines | what changed |
|---|---|---|
| `django_strawberry_framework/optimizer/nested_planner.py` | 9 | 4 retired-noun sites: the `_divergent_key_windows` per-key sentence, the `plan_connection_relation` docstring citation (both retired spellings), the `# (b)` section marker, the no-leakage comment. One reflow to keep `refusal` off a line break |
| `django_strawberry_framework/optimizer/nested_fetch.py` | 4 | `::NestedConnectionRequest` docstring, singular noun + one reflow |
| `django_strawberry_framework/optimizer/lateral_fetch.py` | 8 | module docstring: retired noun **and** the false `walker-owned` ownership claim, replaced with what the sentence actually claims |
| `tests/optimizer/test_walker.py` | 8 | 3 sites: the per-key sentence, the `test_divergent_all_keys_fallback_stays_unplanned` docstring, the simile |
| `tests/optimizer/test_nested_fetch.py` | 4 | module docstring, the wrapped site |
| `tests/optimizer/test_extension.py` | 10 | the two bare `Decision 11` references qualified to `spec-030 Decision 11`, plus the reflow that qualification forced |
| `tests/test_relay_connection.py` | 12 | 3 sites: the divergent-sidecar docstring, the `last: 0` degrade sentence, the strictness section comment |

**No executable byte changed in any of the seven.** `### Inverse proof` is the record.

### Tests added or updated

None. This pass adds no assertion and renames no test function — `tests/optimizer/test_walker.py::test_divergent_all_keys_fallback_stays_unplanned` keeps its name deliberately (a rename is an executable change and would break the identity this pass owes).

### Validation run

- `uv run ruff format <the 7 files>` — pass, `7 files left unchanged`
- `uv run ruff check --fix <the same 7>` — pass, `All checks passed!`
- `uv run python scripts/check_trailing_commas.py --check <the same 7>` — pass, exit 0 (this is also the ASCII-only gate for `.py`; every replacement uses plain `-` and `->`)
- `uv run python scripts/check_citations.py --check` — **before `OK: 828 citations resolve (738 in 431 .py files, 90 in KANBAN.md)`; after, identical.** The count is unchanged by construction: this pass creates no `path::Symbol` citation and wraps none. (`828`, not the `819` recorded during R2 pass 1 — R2's own repairs added nine `path::Symbol` refs between then and this pass's baseline.)
- `git status --short` after both ruff invocations — 23 modified tracked files. **Seven are this cohort's** (the table above). The other sixteen were dirty at this pass's start and are not this cohort's: R2's accepted work (`connection.py`, `optimizer/plans.py`, `optimizer/walker.py`, `tests/optimizer/test_plans.py`, `tests/test_connection.py`, `examples/fakeshop/test_query/test_library_api.py`) and Slice 2's spec (`docs/SPECS/spec-033-…md`); the concurrent session's `README.md`, `docs/builder/ARTIFACT.md`, `BUILD.md`, `worker-1.md`, `worker-2.md`, `worker-3.md`, `KANBAN.md`, `KANBAN.html`, `examples/fakeshop/db.sqlite3`. Nothing was reverted or tidied. **One change against the session-start snapshot, recorded because it is evidence and not a breach:** `examples/fakeshop/test_query/test_products_api.py`, `test_debug_extension_api.py` and `examples/fakeshop/apps/products/services.py` were dirty at start and are clean now — a concurrent session committed them mid-pass, exactly as the dispatch anticipated for `test_products_api.py`. This cohort never opened any of the three.
- Focused runs, all without any `--cov*` flag (`pytest.ini`'s `addopts` auto-applies `--cov`, so `--no-cov` is required), each re-run against the **final** state of the tree:
  - `uv run pytest tests/optimizer/ tests/test_connection.py tests/test_relay_connection.py --no-cov -q` -> **1005 passed** (matches the recorded figure)
  - `uv run pytest examples/fakeshop/test_query/test_library_api.py tests/test_keyset_connection.py --no-cov -q` -> **224 passed** (matches)
  - `uv run pytest tests/ --no-cov -q` -> **5967 passed, 40 skipped** (matches)

### Failability proofs

None; this pass introduced no boundary, guard, gate, or rejection path. Every edit is a comment or a docstring, which `### Inverse proof` demonstrates rather than asserts.

### Inverse proof

**Instrument.** `ast.parse` -> strip every module / class / function docstring (substituting `Pass()` where a body would empty) -> `ast.dump(tree)` (default `include_attributes=False`, so line numbers are out and a reflow is invisible) -> `sha256`, first 12 hex. Written fresh for this pass; it then had to reproduce the four digests the dispatch pinned before it was trusted for anything, and it did on the first run: `optimizer/nested_fetch.py` `302fbecdcc8d`, `optimizer/walker.py` `615fe2fe2be2`, `tests/test_relay_connection.py` `e357f45d6f2a`, `examples/fakeshop/test_query/test_library_api.py` `b5918390baa8`. Python `3.14.2`.

**Baseline.** `HEAD` is **not** the baseline: five of the seven files carry R2's accepted work at `HEAD`+dirty. Each file was copied to a scratch path **outside the repository** before any edit (`…/scratchpad/r3/before/`, one flattened name per path). No `git stash` / `checkout` / `restore` / `worktree` was run at any point in this pass.

**Evidence the instrument can fail.** Two asserted controls per file, both run over the **live** file rather than a synthetic fixture, before and again after the edits:

- **must-see** — insert `_dsf_r3_control_probe = 1` at column 0 immediately above the file's first module-level `def` / `class` (located through `ast`, taking the minimum of the node's `lineno` and its decorators'), in memory. The digest **must** move.
- **must-not-see** — prepend a sentence to the module docstring **and** append a trailing `#` comment, in memory. The digest **must not** move.
- **Both anchors fail loudly when absent.** Demonstrated against a one-line scratch module with neither anchor: `control_must_see: RAISED (did not skip quietly) -> CONTROL ANCHOR ABSENT: no module-level def/class in …`, `control_must_not_see: RAISED … no module docstring in …`. Neither returns a passing-looking result.
- The must-see anchor also failed loudly **for real, once**: a first version located the anchor by a textual `line.startswith("def ")`, which in `optimizer/lateral_fetch.py` matched a line inside a docstring and produced a `SyntaxError` at parse rather than a silent skip. Recorded because a control that cannot fail reads exactly like a passing proof, and this one demonstrably can.

| file | before | after | identical | mutant digest (must-see control) |
|---|---|---|---|---|
| `django_strawberry_framework/optimizer/nested_planner.py` | `3e8f913d90ae` | `3e8f913d90ae` | **yes** | `9e064e8ada97` |
| `django_strawberry_framework/optimizer/nested_fetch.py` | `302fbecdcc8d` | `302fbecdcc8d` | **yes** | `69c0287962c6` |
| `django_strawberry_framework/optimizer/lateral_fetch.py` | `9abf1bbf2dc2` | `9abf1bbf2dc2` | **yes** | `ee0988f2f6a3` |
| `tests/optimizer/test_walker.py` | `1311b82c4ceb` | `1311b82c4ceb` | **yes** | `f4f06ced6d0b` |
| `tests/optimizer/test_nested_fetch.py` | `b459bd8740f2` | `b459bd8740f2` | **yes** | `0eb533de533e` |
| `tests/optimizer/test_extension.py` | `bd92ca53429b` | `bd92ca53429b` | **yes** | `a9a5a2d06ce2` |
| `tests/test_relay_connection.py` | `e357f45d6f2a` | `e357f45d6f2a` | **yes** | `d071cc963c86` |

**The two files this cohort did not write but the dispatch pinned**, re-measured in the same invocation: `django_strawberry_framework/optimizer/walker.py` `615fe2fe2be2` -> `615fe2fe2be2`, `examples/fakeshop/test_query/test_library_api.py` `b5918390baa8` -> `b5918390baa8`. Both hold.

### Hot-path budget

The plan declares `optimizer/nested_planner.py`, `optimizer/nested_fetch.py` and `optimizer/lateral_fetch.py` **hot** — per request, per resolver, per parent row. Every edit in all three is a comment or a docstring, so the honest number is a **demonstrated zero delta**, and the AST identity above **is** that record rather than a substitute for one:

- metric: `ast.dump` of the docstring-stripped module, before vs after. Command: the instrument recorded verbatim in `### Inverse proof`. Iterations: one exact comparison per file; an identity needs no statistic.
- before / after / delta: `3e8f913d90ae` / `3e8f913d90ae` / **0** (`optimizer/nested_planner.py`); `302fbecdcc8d` / `302fbecdcc8d` / **0** (`optimizer/nested_fetch.py`); `9abf1bbf2dc2` / `9abf1bbf2dc2` / **0** (`optimizer/lateral_fetch.py`).
- No instruction, branch, import, attribute read or allocation was added to any of the three paths. The mutant digests in the same table are what make the zero a measurement rather than a null the instrument would have reported either way.

### Floor verification

Not applicable; plan declares floor-verification scope `none`. No comment-only edit touches a Django / Strawberry / channels integration seam, and the shared `.venv` was not mutated by this pass (no `uv pip install` was run at all).

### Implementation notes

#### The population, re-derived before any edit

**13 occurrences of `fallback shape(s)` across 6 tracked `.py` files** — agreeing digit for digit with the figure the dispatch supplied and with `bld-033-review-2-py_comment_repair.md` `### Low 7`.

| n | file |
|---|---|
| 4 | `django_strawberry_framework/optimizer/nested_planner.py` |
| 3 | `tests/optimizer/test_walker.py` |
| 3 | `tests/test_relay_connection.py` |
| 1 | `django_strawberry_framework/optimizer/lateral_fetch.py` |
| 1 | `django_strawberry_framework/optimizer/nested_fetch.py` |
| 1 | `tests/optimizer/test_nested_fetch.py` |

**The instrument**, over every tracked `.py` (`git ls-files "*.py"`), in this order, because each step defeats a spelling that beat a sweep earlier in this cycle:

1. `re.sub(r"\n\s*#\s?", " ", src)` — join wrapped **comments** first. Whitespace normalization alone is not enough, because a comment's continuation line carries its own `#`.
2. `re.sub(r"\s+", " ", src)` — normalize whitespace, which is what catches a docstring sentence wrapped mid-phrase. `tests/optimizer/test_nested_fetch.py`'s occurrence is exactly that shape and is **invisible to a single-line `grep`**: `grep -n -i "fallback shape"` on that file returns nothing while the true count is 1.
3. `src.replace("-", " ")` — fold hyphenation, then re-normalize whitespace.
4. Count **occurrences** (`len(re.findall(...))`), never matching lines.

Case-insensitive, so `# (b) Fallback shapes …` at sentence start is inside the count. Post-edit the same instrument returns **0 in 0 files**.

#### The decision on the simile, and on the vocabulary as a whole: **retire it everywhere**

`tests/optimizer/test_walker.py::test_refusing_nested_fetch_strategy_leaves_selection_unplanned #"behaves exactly like the other fallback shapes"` is retired along with the other twelve. Three reasons, in order of weight:

1. **The noun names a spec structure that no longer exists.** `### Decision 6`'s heading was `Fallback shapes: sidecar input, divergent aliases, hints, and scalar-only connections`; it is now `Refusal arms, divergent aliases, hints, and scalar-only connections`, and the body says "refusal arms" throughout. A reader who greps the spec for `fallback shape` finds nothing. That is true of a simile as much as of a citation — the simile's referent is "the other things Decision 6 lists", which the spec now calls arms.
2. **A half-retired vocabulary is worse than either end state.** The pass-3 reviewer's own amendment is the governing one: the simile is 1 of 13, not a singleton, "and should be retired with them or not at all". Leaving one site standing means the next sweep finds a survivor and re-opens the question with no record of why it survived.
3. **This cycle created the rot**, so this cycle owns it end to end rather than handing a residue forward.

The cost the earlier pass weighed against the edit — "cosmetic churn into the one partition file carrying an executable repair this cohort must not disturb" — does not apply here: `tests/optimizer/test_walker.py` carries no executable repair in **this** pass, and its AST identity (`1311b82c4ceb` -> `1311b82c4ceb`) proves R2's repair was not disturbed.

**What "retire the vocabulary" does and does not mean.** The retired token is the two-word phrase `fallback shape(s)`, the pre-rewrite heading noun. The bare word `fallback` is **not** retired and was not swept: the current spec still uses it freely (`### Decision 5 — … and a per-parent fallback`, "routed to a fallback rather than approximated"), 600 occurrences stand across 112 `.py` files, and mass-editing them would be exactly the unrelated cleanup `worker-2.md` `## Scope` forbids. Likewise the bare word `shape`, which `### Decision 6` itself uses in its first sentence ("Nine nested-connection **shapes** are not window-planned").

#### The thirteen sites, before and after, with the citation call for each

Every replacement was written from `### Decision 6` as it stands in `docs/SPECS/spec-033-connection_optimizer-0_0_9.md`, read in full first — not from the dispatch, not from another file's wording, and not from `nested_fetch.py`'s repaired sentence except where noted as a reference point rather than a template.

**1. `optimizer/nested_planner.py::_divergent_key_windows`** — *dropped, reads correctly without one.*
- before: "``None``), so one alias's fallback shape must not drag its siblings per-parent:"
- after: "``None``), so one alias's refusal must not drag its siblings per-parent:"
- The sentence describes this helper's own per-payload behavior, and the spec's word for a one-alias non-planning is exactly "a **per-response-key** refusal leaves one alias unplanned while its siblings still plan". Nothing here needs a Decision reference; the four bullets it introduces name the arms concretely.

**2. `optimizer/nested_planner.py::plan_connection_relation`** — *kept, and both retired spellings corrected.* The round's known-hardest site: a live citation carrying the hyphenated `Decision-6` and the retired noun at once, in the module that owns the planning contract today (`### Decision 11`: "1,436 lines … it owns the planning contract today").
- before: "leaves the selection UNPLANNED (no ``Prefetch``, no ``planned_resolver_keys`` entry) for each Decision-6 fallback shape so the strictness contract still sees the per-parent access."
- after: "… for each **spec-033 Decision 6 refusal arm** so the strictness contract still sees the per-parent access."
- The Decision reference **stays** because the sentence asserts Decision 6's own contract verbatim: "each resolves per-parent through the shipped pipeline (and a whole-relation refusal is therefore visible to strictness as unplanned)". It gains the `spec-033` qualifier because the preceding sentence in the same docstring already says `spec-033 Decision 4`, and a bare neighbour is the exact ambiguity routed finding R-b is about.

**3. `optimizer/nested_planner.py #"# (b) Fallback shapes detectable before any queryset is built"`** — *no citation, none added.* An inline section marker.
- after: `# (b) Refusal arms detectable before any queryset is built -> UNPLANNED.`
- This is the replacement `bld-033-review-2` `### Notes for Worker 1` item 4 recommended verbatim; it is correct against the current Decision, so it was taken rather than re-derived.

**4. `optimizer/nested_planner.py::plan_connection_relation #"like each earlier fallback shape"`** — *kept, already correct.*
- after: "a strategy that refused every window (like each earlier **refusal arm**) must leak no child resolver keys / fk-id elisions / cacheable flip into the parent plan (the spec-033 Decision 6 no-leakage contract)."
- The trailing citation is untouched and still resolves: arm 9 states "The child plan is built against a throwaway `sub_plan` and absorbed into the parent only once at least one key planned, so a refusal leaks no resolver key, FK-id elision, or `cacheable` flip into the parent plan."

**5. `optimizer/lateral_fetch.py`** module docstring — *no citation, none added; and a second, separate defect fixed.* Routed finding R-a. R2's repaired `nested_fetch.py` sentence was the **reference for what a correct version looks like**, adapted to what this sentence actually claims rather than copied: `nested_fetch.py`'s sentence is about what the planner **owns**, this one is about what **never reaches a strategy**, and those are different sets.
- before: "The walker-owned fallback shapes (sidecar, SKIP, DISTINCT, malformed slice, unwindowable join) never reach any strategy; divergent aliases arrive as one request per response key, each self-contained."
- after: "The refusal arms decided before any strategy runs - among them sidecar input, ``OptimizerHint.SKIP``, an unwindowable child queryset, a window the slice arithmetic cannot express, and an unwindowable relation kind - never reach any strategy; divergent aliases arrive as one request per response key, each self-contained."
- Two things changed, not one. The retired noun, and the **false ownership claim** `walker-owned`: `### Decision 6` sites the DISTINCT reason on `optimizer/nested_fetch.py::unwindowable_child_queryset_reason`, the unexpressible window on `utils/connections.py::derive_connection_window_bounds`, and the relation kind on `optimizer/join_taxonomy.py::classify_relation_join` — three of the five are not the walker's. "Decided before any strategy runs" is the property the sentence actually needs and the one Decision 6 states ("classified before the child plan is applied … one strategy-independent gate answers for every fetch backend"). `DISTINCT` and `malformed slice` were also generalized to the arms the spec names, because DISTINCT is one of five reasons under the unwindowable-child-queryset arm rather than an arm of its own. No Decision reference added: the paragraph two lines above already cites `spec-033 Decision 6` for the strictness-visibility claim, and a second citation in the same breath would say nothing new.

**6. `optimizer/nested_fetch.py::NestedConnectionRequest`** — *no citation, none added.* Routed finding R-c; the singular a plural-only sweep cleared this file against.
- before: "Built only AFTER every strategy-independent fallback shape has been ruled out:"
- after: "Built only AFTER every strategy-independent **refusal arm** has been ruled out:"
- A true statement about the request's construction order, needing no spec reference to resolve. `nested_fetch.py` reads `302fbecdcc8d` afterwards, as required.

**7. `tests/optimizer/test_walker.py::test_divergent_mixed_sidecar_plans_only_the_plain_key`** — *no citation, none added.* The test mirror of site 1, and worded to match it.
- after: "The per-key scheme must not let one alias's **refusal** drag its siblings per-parent."

**8. `tests/optimizer/test_walker.py::test_divergent_all_keys_fallback_stays_unplanned`** — *no citation, none added.*
- before: `"""When EVERY divergent alias is a fallback shape, the relation stays unplanned."""`
- after: `"""When EVERY divergent alias is a refusal arm, the relation stays unplanned."""`
- This now reads as `### Decision 6`'s own sentence does: "The residual fallback is the case where *every* alias is itself one of the refusal arms above." **The function name keeps `fallback`** — renaming it is an executable change and outside this pass's contract.

**9. `tests/optimizer/test_walker.py::test_refusing_nested_fetch_strategy_leaves_selection_unplanned`** — the simile. *No citation added; the docstring's own correct one, two lines above, is untouched.*
- after: "so even a callback that mutates every plan field behaves exactly like the other **refusal arms**."

**10. `tests/test_relay_connection.py::test_divergent_mixed_sidecar_serves_each_alias_correctly`** — *no citation, none added.* The live-behavior mirror of sites 1 and 7.
- after: "``b`` (plain page) is served from its per-key window - one alias's **refusal** must not corrupt the other's rows."

**11. `tests/test_relay_connection.py::test_async_fast_path_last_zero_falls_back_for_total_count_and_pageinfo`** — *behavior sentence; vocabulary fixed, claim kept, no citation added.*
- before: "``last: 0`` is the one remaining always-fallback shape after the marker-row disambiguation (workstream C)"
- after: "``last: 0`` is the one shape that always **degrades** after the marker-row disambiguation (workstream C)"
- This site names a **behavior**, not the spec structure, so the behavior sentence is what matters and only the vocabulary moved. The replacement is `### Decision 5`'s own words: "**`last: 0` is the one shape that always degrades, and does so on purpose.**" "shape" survives because the spec uses it; "always-fallback shape" does not, because it reads as a member of the retired list.

**12. `tests/test_relay_connection.py #"the clearest live-reachable fallback shape"`** — *kept and qualified.* A module-section comment above the strictness pins.
- before: "is the clearest live-reachable fallback shape: the walker leaves it unplanned (Decision 6), so the resolver runs per-parent and is visible to strictness."
- after: "is the clearest live-reachable **refusal arm (spec-033 Decision 6)**: the walker leaves it unplanned, so the resolver runs per-parent and is visible to strictness."
- The citation stays (arm 1, sidecar input, is exactly this) and gains `spec-033` for a concrete reason: this file's **module docstring cites spec-032**, and two further bare `Decision 6` references at `::test_…` docstrings in this same file are spec-032's, so a bare one here resolves against the wrong spec on a first read. The reference was also lifted out of the trailing clause and onto the noun so the phrase and its citation sit on one line.

**13. `tests/optimizer/test_nested_fetch.py`** module docstring — *no citation, none added.* The wrapped site.
- before: "the walker rules out every strategy-independent fallback / shape, then hands one ``NestedConnectionRequest`` to the active strategy"
- after: "the walker rules out every strategy-independent **refusal arm**, then hands one ``NestedConnectionRequest`` to the active strategy"
- Worded to match site 6, which is the production sentence this docstring is the test-side statement of. Reflowed so `refusal arm` sits on one line — a phrase split across lines is the shape that has defeated three counts in this cycle, and re-creating one here would be building the next blind spot.

**Reflows.** Five sentences were re-wrapped so a replaced phrase does not straddle a line break (sites 1, 6, 7, 11, 13) and one docstring paragraph was re-wrapped because `spec-030 ` lengthened its first line (`tests/optimizer/test_extension.py::test_apply_connection_optimization_uses_active_optimizer_cache`). A reflow is invisible to the AST identity by construction (`include_attributes=False`), which is why it is safe here and why the identity is not weakened by it.

#### Routed finding R-b: what landed, and the site that could not

The finding as dispatched names `tests/optimizer/test_extension.py`. **Verified against source, that file is not the site the finding describes.** Both of its `Decision 11` references are bare and both are spec-030's:

- `::test_optimizer_helper_extraction_no_regression #"Per Decision 11 the plan-build-and-apply tail was extracted into"` — `spec-030` `### Decision 11` states exactly this: "the plan-application logic is a reusable core on the extension, `DjangoOptimizerExtension.apply_to` … Two callers share that one core".
- `::test_apply_connection_optimization_uses_active_optimizer_cache #"Decision 11 plan-cache-reuse route"` — same Decision: "it reads the active extension from the `_active_optimizer` `ContextVar` that `on_execute` publishes, so it shares the instance-bound plan cache".

`spec-033` `### Decision 11` is a module map ("Module and test-file locations") and says nothing about cooperation points or cache reuse, so neither reference resolves against it. Both are **qualified to `spec-030 Decision 11`** in this pass — the improvement the finding asks for, at the file it names.

**But the ambiguity the finding actually describes is elsewhere, and its site is outside this cohort's writable list.** `bld-033-review-2` `### Low 9` and its `### Notes for Worker 1` item 5 name it explicitly: `django_strawberry_framework/connection.py::_finalize_queryset #"the connection field's own cooperation point, Decision 11"`. That is the one where "box 2 changed step 5 of the *same docstring*, two list items above, from `spec-033 Decision 11` to `spec-033 Decision 4`" — verified in source: step 5 reads "(the cursor-parity invariant, spec-033 Decision 4)" and step 6, three lines below, reads "(the connection field's own cooperation point, Decision 11)". `tests/optimizer/test_extension.py` has no such adjacent `spec-033` reference, and R2's pass explicitly recorded its two as "correctly left alone".

**Deferral, naming the site:** `django_strawberry_framework/connection.py::_finalize_queryset #"the connection field's own cooperation point, Decision 11"` should gain a `spec-030` prefix. It is a one-word comment edit with no executable byte, and `connection.py` must stay at `ecc47449f5ec`. `connection.py` is **not** on this cohort's writable list, so per the dispatch's own scope rule this is reported rather than written. Box **R-b** is left `- [ ]`.

#### Measured and deliberately left, so it is not re-raised as a miss

**Seven hyphenated `Decision-6` occurrences survive** (`optimizer/nested_planner.py` 1, `utils/connections.py` 1, `tests/optimizer/test_extension.py` 1, `tests/optimizer/test_walker.py` 1, `tests/test_relay_connection.py` 3). Every one was opened and read. All are the informal arm vocabulary "a Decision-6 fallback" / "the other Decision-6 fallbacks" — no ordinal, no heading string, and each is true against the current Decision. Not written, for three reasons: `Decision-<N>` hyphenation is a live tree-wide convention rather than retired vocabulary (38 occurrences across 25 `.py` files **at this pass's baseline**, 37 across 25 after site 2's removal — the figure is dated here by the integration pass per `### Low: 2` below, because it was a pre-edit measurement stated beside post-edit counts; both figures re-derived and both reconcile); `bld-033-review-2`'s Worker 3 pass read all nine of them and graded them not-defects, so re-litigating them is not this cohort's call; and sweeping them would be the unrelated cleanup `worker-2.md` `## Scope` forbids. The **one** hyphenated site that was a genuine defect — the known-hardest site, which carried the retired heading noun alongside the hyphen — is site 2 above and is fixed.

The retired-**ordinal** vocabulary (`shape <N>`, `arm <N>`) measures **0** tree-wide after this pass, as it did before it. A `four (numbered )?(fallback )?shapes` sweep returns one hit, `tests/test_strawberry_patches.py #"The rejection of these same four shapes is the package view's job"` — read, unrelated to `spec-033`, no edit.

`refusal arm(s)` now occurs **11** times across the six population files (`nested_fetch.py` 3, `nested_planner.py` 3, `test_walker.py` 2, `lateral_fetch.py` 1, `test_nested_fetch.py` 1, `test_relay_connection.py` 1). **Two** of those eleven are R2's, both in `nested_fetch.py`; the other **nine** are this pass's. Measured against the baseline copies, not asserted.

#### Small choices

- **No process provenance.** Every replacement states the invariant. Nothing says "renamed", "formerly", "now centralized", or names a pass, round, finding id, or artifact.
- **No test function renamed**, in either direction. `test_divergent_all_keys_fallback_stays_unplanned` and `test_async_fast_path_last_zero_falls_back_…` keep their names; a rename is an executable change and is what `### Inverse proof` exists to forbid.
- **The three escalations in the build plan's `## Escalations` were not acted on** and are untouched by this diff: the `connection_to_attr` strictness probe, `window_partition_for_prefetch`'s zero production callers, and the ten dead `optimizer/walker.py` aliases. `walker.py` was not opened for writing and reads `615fe2fe2be2`.
- **Both spec files were read and neither was written.** `git status --short` shows `docs/SPECS/spec-033-…md` modified — that is Slice 2's accepted work, present at this pass's baseline. `docs/SPECS/appx/spec-033-…-rationale.md` was **not read**, per `BUILD.md` `### Who reads it, and when`.

### Notes for Worker 3

- **Read the diff against this pass's baseline, not `HEAD`.** `git diff -- tests/` and `git diff -- django_strawberry_framework/optimizer/` both show R2's accepted work interleaved with this pass's. The seven-row table in `### Files touched` gives the per-file changed-line count against the baseline copies taken outside the repository, which is the honest measure of this cohort's diff; the copies are at `…/scratchpad/r3/before/` (one flattened filename per path).
- **The population instrument is reproducible and the wrapped site is the one to check it with.** `grep -n -i "fallback shape" tests/optimizer/test_nested_fetch.py` returned **nothing** at baseline while the true count was 1. Any re-measurement that uses a single-line grep will read 12, not 13, and will conclude a site is missing that was never there to see.
- **The four dispatch-pinned digests all reproduce under this pass's independently written instrument** (`302fbecdcc8d`, `615fe2fe2be2`, `e357f45d6f2a`, `b5918390baa8`). If a re-review's own instrument disagrees on any of the four, the instrument is what to check first — those four are now agreed by four separately written implementations across three passes.
- **The must-see control's mutant digests are in the table** precisely so a re-review can distinguish "the instrument reported identity" from "the instrument reported nothing". A re-implementation should reproduce the mutant column too, not only the identity column.
- One box, **R-b**, is deliberately un-ticked with its site named. It is not an oversight and it is not a deferral of the work the dispatch asked for at the file the dispatch named — that half landed.

### Notes for Worker 1 (spec reconciliation)

1. **The `connection.py` bare `Decision 11` is still open and is not this cohort's to write.**
   - Where it lives: `django_strawberry_framework/connection.py::_finalize_queryset`, step 6 of the pipeline docstring, `#"the connection field's own cooperation point, Decision 11"`.
   - Current wording: "Optimizer plan - ``apply_connection_optimization`` applies ``select_related`` / ``prefetch_related`` / ``only()`` using the node type / model explicitly (the connection field's own cooperation point, Decision 11), because the schema middleware never sees the pre-slice queryset behind ``ConnectionExtension``."
   - Recommended replacement: identical, with "Decision 11" -> "**spec-030** Decision 11". One word, no executable byte; `connection.py` must still read `ecc47449f5ec`. It correctly cites `docs/SPECS/spec-030-connection_field-0_0_9.md` `### Decision 11 - The connection field owns its optimizer cooperation point`, but sits three lines below an explicit `spec-033 Decision 4` in the same docstring, so a reader resolves it against spec-033's module map.

2. **`### Decision 6` should say how source prose is expected to cite its arms.** This is `bld-033-review-2`'s recommended amendment 2, widened by its own `### Low 4` and now by this pass's whole population — recorded again because the case is now measured across 13 sites rather than 4, and because no gate can see this class of rot: `scripts/check_citations.py` validates the `path::Symbol` form and is blind to spec-heading nouns and prose ordinals alike.
   - Where it lives: `docs/SPECS/spec-033-connection_optimizer-0_0_9.md` `### Decision 6 — Refusal arms, divergent aliases, hints, and scalar-only connections`, in the introduction, after "The refusal arms, with the site that decides each:".
   - Current wording: the introduction states the nine arms and their granularity but says nothing about how they are referred to elsewhere.
   - Recommended replacement — one sentence appended to that introduction: "Source comments and test docstrings cite an arm **by its content** (\"the unwindowable-child-queryset refusal arm\"), never by ordinal and never by this Decision's heading text, so neither a renumbering nor a rename can silently falsify a citation." Both retired spellings produced live rot in this cycle — the ordinal at three sites, the heading noun at thirteen — and a retired-*ordinal* sweep is structurally blind to a retired-*heading-noun* one.

3. **`optimizer/lateral_fetch.py`'s module docstring asserted a false ownership claim, and the spec is where the correct one is stated.** The sentence read "The **walker-owned** fallback shapes (sidecar, SKIP, DISTINCT, malformed slice, unwindowable join)", attributing all five to the walker where `### Decision 6` sites three of them elsewhere (`utils/connections.py::derive_connection_window_bounds`, `optimizer/join_taxonomy.py::classify_relation_join`, `optimizer/nested_fetch.py::unwindowable_child_queryset_reason`). Fixed in this pass. No spec edit is owed — the spec was already right and the comment was wrong — but it is recorded because it is the **second** file to carry that same five-item stale enumeration (the first was `nested_fetch.py`, repaired by R2), and a claim that appears twice in two modules is the shape that appears a third time.

4. **A vocabulary retirement has no gate, and this cycle now has two data points that it rots within one pass.** `### Decision 6`'s heading changed during Slice 2 and stranded 13 source sites; nothing in pre-commit or CI could see any of them. If a future Decision heading is renamed, the rename's own slice owes a tree-wide sweep of the retired heading's **nouns**, run with the wrapped-comment-join-then-normalize instrument recorded in `### Implementation notes`. That is a process observation for `BUILD.md` rather than a spec edit, and is offered as such.

---

## Build report (Worker 2, pass 2)

### Worker-0 mid-flight instruction, mirrored here

Per `worker-0.md` `### Mid-flight instructions are mirrored into the artifact`, recorded verbatim in substance so the artifact remains the contract the next worker reads:

**What was sent:** `django_strawberry_framework/connection.py` was added to this cohort's writable list, **for one site only** — `::_finalize_queryset`, step 6 of the pipeline docstring, `#"the connection field's own cooperation point, Decision 11"`.

**Why:** pass 1 identified that the routed finding R-b named `tests/optimizer/test_extension.py` while the ambiguity it describes lives in `connection.py`, did the improvement at the file it was told to edit, deferred the real site **by name**, and left box R-b un-ticked. Worker 0 verified the deferral against both specs before dispatch and adjudicated it: `docs/SPECS/spec-030-connection_field-0_0_9.md #"### Decision 11 — The connection field owns its optimizer cooperation point"` is what the sentence means — that Decision's own title is the phrase the comment uses — and `spec-033`'s Decision 11 (`Module and test-file locations`) is not. **The fix is qualification, not re-siting**; the reference was correct in substance and ambiguous only in spelling, because five lines above it in the same docstring sits `#"the cursor-parity invariant, spec-033 Decision 4"` and a reader carries that spec forward.

**Also instructed:** survey the rest of `connection.py` for bare `Decision N` references and establish per reference whether an adjacent qualified reference to a *different* spec makes it ambiguous the same way — qualifying only where the ambiguity is real, since a bare reference in a passage naming no other spec is house convention and not a defect. And: keep the seven hyphenated `Decision-6` deferrals from pass 1 exactly as recorded; they are graded not-defects and are not reopened.

Pass 1's qualification of the two `tests/optimizer/test_extension.py` references stands and was not revisited.

### Files touched

| file | +/- lines | what changed |
|---|---|---|
| `django_strawberry_framework/connection.py` | 12 | two bare `Decision N` references qualified, plus the two reflows that qualification forced. Comment/docstring only |

`+/-` is `diff -u <baseline copy outside the repo> <working tree>` counting `^[+-][^+-]` rows. **`HEAD` is not the baseline** — R2 edited `connection.py`, and its two hunks (the `optimizer/plans.py` hoist comment and the `spec-033 Decision 11` -> `Decision 4` re-siting at `::_finalize_queryset` step 5) are present in `git diff` and are **not** this pass's. The baseline copy was taken before any edit, to `…/scratchpad/r3/before/django_strawberry_framework@connection.py`; no `git stash` / `checkout` / `restore` / `worktree` was run.

The seven files from pass 1 are untouched by this pass and re-verified below.

### Tests added or updated

None. No assertion, no test name, no executable byte.

### The full bare-reference survey of `connection.py`

Every `Decision N` reference in the file was enumerated (`grep -n "Decision[ -][0-9]"`, 35 lines / 42 references) and each **bare** one — 14 individual references across 10 passages — was read against its passage and against the two candidate specs' Decision lists. **2 qualified, 12 left.**

*(Corrected by the integration pass, count only, per `### Low: 1` below: this sentence first read `27 lines`. Re-derived at the integration pass with the wrapped-comment-join instrument — `HEAD` 34 lines / 41 references, this pass's worktree 35 / 42, matching the reviewer's figure exactly. The substantive figures — 14 bare across 10 passages, then 12 bare / 2 qualified — reproduce unchanged, so the enumeration was complete and only its stated size was wrong. The file has since moved again to 39 lines / 46 references through a concurrent session's edit that is not this cycle's; see `docs/builder/bld-033-integration.md`.)*

The file's governing declaration is its module docstring line 3, `Spec: docs/SPECS/spec-030-connection_field-0_0_9.md`, so an unqualified reference defaults to spec-030 unless a nearer qualified reference overrides it. That gives the test two directions, and both had to be checked: **carry-forward** (a bare reference after a qualified one naming a different spec) and **module-default** (a bare reference whose home spec is not the file's declared one).

#### Qualified — 2

**1. `::_finalize_queryset` step 6, `Decision 11` -> `spec-030 Decision 11`** (the dispatched site).
- before: "using the node type / model explicitly (the connection field's own cooperation point, **Decision 11**), because the schema middleware never sees the pre-slice queryset behind ``ConnectionExtension``."
- after: "… (the connection field's own cooperation point, **spec-030 Decision 11**), because …"
- Carry-forward ambiguity, real: step 5 of the same docstring, five lines above, ends "(the cursor-parity invariant, **spec-033 Decision 4**)". A reader who has just resolved a qualified `spec-033` reference carries it onto the next bare one and lands on `spec-033` `### Decision 11 — Module and test-file locations`, a module map that says nothing about cooperation points. What it points at is unchanged.

**2. `_build_relation_connection_resolver`'s strictness comment, `Decision 6` -> `spec-033 Decision 6`.**
- before: "a sidecar (``filter:`` / ``orderBy:``) selection is the explicitly-unwindowed shape (**Decision 6**), so it carries the spec's filter/orderBy wording"
- after: "… is the explicitly-unwindowed shape (**spec-033 Decision 6**), so it carries …"
- **Module-default ambiguity, and the sharper of the two.** The nearest qualified reference is `spec-033 Decision 8` four lines above, so carry-forward resolves it correctly — but the file's declared spec is **spec-030**, which *has* a Decision 6, and it is `### Decision 6 — Sidecar-derived arguments via a synthesized resolver signature`. The sentence is literally about a `filter:` / `orderBy:` sidecar, so a reader falling back to the module default lands on a Decision that is topically adjacent and reads as plausible. A wrong resolution that looks right is worse than one that looks wrong. The intended target is `spec-033` `### Decision 6`'s first refusal arm ("**Sidecar input** (`filter:` / `orderBy:` arguments on the nested selection) — *per key*"), which is what "explicitly-unwindowed" means here. What it points at is unchanged.

#### Left, with the reason — 12 references across 8 passages

- **Module docstring `#"The connection-class surface (Decision 3 / Decision 4):"`** (2 refs) and **`#"The window-pagination surface (Decision 5 / Decision 6 / Decision 7 / Decision 10):"`** (4 refs). Both are section headers sitting under the docstring's own `Spec:` declaration, and all six resolve correctly against spec-030 (`D3` the `first`+`last` guard, `D4` the base-plus-concrete-classes design, `D5` factory-function / Meta-only derivation, `D6` sidecar-derived arguments, `D7` the composition pipeline, `D10` sync+async resolver paths). The `spec-032` parenthetical at line 17 sits between the `Spec:` line and the second header, which is the only reason this passage was weighed at all — but a file-level `Spec:` declaration exists precisely so the module's own section headers need no per-reference qualification, and re-qualifying six of them would be rewriting the file's convention rather than fixing a defect. **House convention.**
- **`#"spec-033 Decision 11 sites the hoist; Decision 4 states the cursor-parity invariant it serves"`** (1 bare ref). A continuation of the qualified reference in the same sentence, same spec; carry-forward gives the right answer.
- **`::_resolve_from_window #"spec-033 Decision 4 / Decision 5"`** (1). Continuation, same spec.
- **`DjangoConnection` class docstring `#"that is the opt-in ``<TypeName>Connection`` variant's job (Decision 4)"`** (1) — the reference the instruction named as a for-instance. **Not a defect.** The only qualified reference in the passage is `spec-030 Decision 3` two sentences earlier, the *same* spec, and spec-030 `### Decision 4 — DjangoConnection[T] base plus per-target concrete connection classes` is exactly what the sentence claims. Both carry-forward and the module default land on the correct Decision. Verified against the spec's Decision list rather than assumed from the adjacency.
- **`::_finalize_queryset #"Steps 5-6 of the Decision 7 pipeline"`** (1). This is the **first** reference in that docstring, so nothing precedes it to carry forward, and the module default (spec-030 `### Decision 7 — Composition pipeline: visibility→filter→order→default-order→optimizer`) is correct. The `spec-033 Decision 4` that appears later in the same docstring is downstream of it and cannot mis-steer a top-down reader.
- **`::_resolve_connection_sync #"spec-030 Decision 7 / Decision 10"`** (1) and **`::_synthesized_connection_resolver #"spec-030 Decision 6 / Decision 7"`** (1). Continuations, same spec.

### Validation run

- `uv run ruff format django_strawberry_framework/connection.py` — pass, `1 file left unchanged`
- `uv run ruff check --fix django_strawberry_framework/connection.py` — pass, `All checks passed!`
- `uv run python scripts/check_trailing_commas.py --check django_strawberry_framework/connection.py` — pass, exit 0 (also the ASCII gate; both replacements are plain ASCII, and neither comment states how the change came to be, names a finding id, a review round, or a per-cycle artifact)
- `uv run python scripts/check_citations.py --check` — **`OK: 828 citations resolve (738 in 431 .py files, 90 in KANBAN.md)`, held exactly.** Neither edit adds a `path::Symbol` citation and neither wraps one; both were reflowed so the qualified reference sits on one line.
- `git status --short` — `django_strawberry_framework/connection.py` is the one file this pass modified. Everything else is unchanged from pass 1's classification; nothing was reverted or tidied.
- Focused runs, all `--no-cov`, no `--cov*` flag anywhere:
  - `uv run pytest tests/optimizer/ tests/test_connection.py tests/test_relay_connection.py --no-cov -q` -> **1005 passed**
  - `uv run pytest examples/fakeshop/test_query/test_library_api.py tests/test_keyset_connection.py --no-cov -q` -> **224 passed**
  - `uv run pytest tests/ --no-cov -q` -> **5967 passed, 40 skipped**

### Failability proofs

None; this pass introduced no boundary, guard, gate, or rejection path.

### Inverse proof

Same instrument as pass 1 (`ast.parse` -> strip every module / class / function docstring, substituting `Pass()` where a body would empty -> `ast.dump` with `include_attributes=False` -> `sha256[:12]`), unchanged, with `connection.py` added to its file list. Baseline copy taken outside the repository before the edit.

**Evidence the instrument can fail, on `connection.py` specifically.** Both controls were re-run over the live file: **must-see** (an AST-located `_dsf_r3_control_probe = 1` inserted at column 0 above the first module-level `def`/`class`, in memory) moves the digest `ecc47449f5ec` -> **`a1edbeee834d`**; **must-not-see** (a sentence prepended to the module docstring plus a trailing `#` comment) leaves it at `ecc47449f5ec`. Both raise loudly rather than skipping when their anchor is absent, demonstrated in pass 1 against a two-line scratch module — and the must-see anchor has failed loudly for real once in this round, raising a `SyntaxError` on `optimizer/lateral_fetch.py`'s SQL docstring when it was still located textually, which is the behavior that makes a passing result mean something.

| file | before | after | identical | mutant digest (must-see control) |
|---|---|---|---|---|
| `django_strawberry_framework/connection.py` | `ecc47449f5ec` | `ecc47449f5ec` | **yes** | `a1edbeee834d` |

`ecc47449f5ec` is the digest `bld-033-review-2-py_comment_repair.md` recorded for this file, reproduced here on the first run by an independently written instrument — a fourth implementation agreeing on it.

**The eight other files re-measured in the same invocation and all unchanged from pass 1**: `optimizer/nested_planner.py` `3e8f913d90ae`, `optimizer/nested_fetch.py` `302fbecdcc8d`, `optimizer/lateral_fetch.py` `9abf1bbf2dc2`, `tests/optimizer/test_walker.py` `1311b82c4ceb`, `tests/optimizer/test_nested_fetch.py` `b459bd8740f2`, `tests/optimizer/test_extension.py` `bd92ca53429b`, `tests/test_relay_connection.py` `e357f45d6f2a`, plus the two written by neither pass, `optimizer/walker.py` `615fe2fe2be2` and `examples/fakeshop/test_query/test_library_api.py` `b5918390baa8`.

### Hot-path budget

`django_strawberry_framework/connection.py` is **hot** — per request, per resolver, per parent row; `::_resolve_from_window` and `::_finalize_queryset` are on the connection resolve path. Both edits are comment/docstring text, so the honest number is a **demonstrated zero delta**, and the AST identity **is** that record:

- metric: `ast.dump` of the docstring-stripped module, before vs after. Command: the instrument recorded in `### Inverse proof`. Iterations: one exact comparison; an identity needs no statistic.
- before / after / delta: `ecc47449f5ec` / `ecc47449f5ec` / **0**.
- No instruction, branch, import, attribute read or allocation was added. The mutant digest `a1edbeee834d` in the same table is what makes the zero a measurement rather than a null the instrument would have reported either way.
- Pass 1's three hot-path figures are unchanged and re-measured above: `3e8f913d90ae` / `302fbecdcc8d` / `9abf1bbf2dc2`, delta **0** each.

### Floor verification

Not applicable; plan declares floor-verification scope `none`. A comment-only edit touches no Django / Strawberry / channels integration seam, and the shared `.venv` was not mutated (no `uv pip install` was run in either pass).

### Implementation notes

- **Qualification only, in both edits.** Neither reference was re-sited, reworded, or re-scoped; the only change is the addition of a `spec-0NN` prefix, plus the reflow it forces. What each points at is what it pointed at before.
- **The second site was not in the instruction and is reported as a judgement call.** The instruction asked which bare references are genuinely ambiguous and which are house convention; twelve were graded convention and one was graded a defect on a mechanism the instruction did not name — **module-default** rather than carry-forward. It is offered with its reasoning above precisely so it can be reversed in one word if Worker 3 or Worker 1 disagrees; the case for it is that spec-030's Decision 6 is topically about the same `filter:` / `orderBy:` sidecars the sentence names, which makes the wrong resolution read as correct.
- **Every "left" verdict was checked against the target spec's Decision list, not inferred from adjacency.** The `DjangoConnection #"(Decision 4)"` reference the instruction singled out as a for-instance is the clearest case: it looks ambiguous (a bare reference following a qualified one) and is not, because the qualified neighbour is the *same* spec and spec-030's Decision 4 is exactly the base-plus-concrete-classes contract the sentence describes.
- **Pass 1's seven hyphenated `Decision-6` deferrals are untouched**, as instructed, and their reasoning in pass 1's `### Implementation notes` stands unamended.

### Notes for Worker 3

- This pass's diff is **two hunks in one file**. `git diff -- django_strawberry_framework/connection.py` shows **four**; the first two (the `optimizer/plans.py` hoist comment, and the `spec-033 Decision 11` -> `spec-033 Decision 4` re-siting in `::_finalize_queryset` step 5) are R2's accepted work, present at this pass's baseline. The baseline copy at `…/scratchpad/r3/before/django_strawberry_framework@connection.py` is the honest comparison point.
- **The bare-reference survey is the part most worth re-deriving**, because a "left" verdict looks identical to a site that was never examined. The enumeration is `grep -n "Decision[ -][0-9]" django_strawberry_framework/connection.py` (35 lines / 42 references, 14 bare references across 10 passages); every one is accounted for above with a named reason and a named target Decision. *(Size corrected by the integration pass, count only — it first read `27 lines`; the bare-reference figures are unchanged.)*
- The second qualification is flagged as a judgement call rather than presented as settled. Reversing it is one word and leaves the AST identity untouched either way.

### Notes for Worker 1 (spec reconciliation)

1. **Pass 1's item 1 is now closed** — `connection.py::_finalize_queryset #"the connection field's own cooperation point, Decision 11"` carries the `spec-030` qualifier and needs nothing from the custodian. No spec edit is owed: the spec was already right and the comment was ambiguous only in spelling.
2. **Pass 1's items 2, 3 and 4 stand unchanged** and are not restated here — the Decision 6 citation-convention sentence, the `lateral_fetch.py` false-ownership record, and the observation that a Decision-heading rename owes a tree-wide sweep of the retired heading's nouns because no gate can see that class of rot.
3. **A new, small observation from the survey, offered as a process note rather than a spec edit.** `connection.py` declares `Spec: docs/SPECS/spec-030-connection_field-0_0_9.md` in its module docstring, but the file legitimately carries references to **four** specs (030, 032, 033, and the module's own). A file-level `Spec:` line is a good default only while the file is single-spec; once it is not, a bare `Decision N` has two plausible resolutions — the declared spec and the nearest qualified neighbour — and this pass found one site where those two disagree and the wrong one reads as correct. If the convention is worth stating anywhere, the natural home is `AGENTS.md`'s source-reference rule alongside `path::QualifiedName`: **a bare `Decision N` is house convention only in a file whose passages name exactly one spec.** Not proposed as a spec Decision; recorded so the custodian can decide whether it belongs in the standing docs.

---

## Review (Worker 3)

Reviewed both passes together: the pass-1 seven-file vocabulary sweep and the pass-2
`connection.py` qualification. Every number below was re-derived with an instrument written
for this review, never read off the build report.

### High:

None.

### Medium:

None.

### Low:

#### 1. The `connection.py` survey mis-states the size of its own enumeration

`docs/builder/bld-033-review-3-retired_vocabulary_sweep.md` `### The full bare-reference survey of connection.py`
says "enumerated (`grep -n "Decision[ -][0-9]"`, 27 lines)". That grep returns **35** lines, in
every state of the file — worktree 35, this pass's baseline copy 35, `HEAD` 34. The true
*reference* count (occurrences, wrapped-comment-joined) is **42**, of which 30 are now qualified.

The substantive figures are all correct: I independently measured **14 bare references across 10
passages** at the baseline and **12 bare / 2 qualified** now, matching the artifact digit for digit.
So the enumeration was real and complete; only its stated raw size is wrong. Artifact-only, no
source byte implicated, no box affected. Recorded rather than held, because this cycle's standing
lesson is that a count can be right in every digit and wrong in its subject, and `27` is neither the
line count, the reference count, the qualified count, nor the passage count.

Instrument: `re.sub(r"\n\s*#\s?", " ", src)` then `\s+`->" ", then
`(spec-0\d\d\s+)?Decision[ -]\d+`, counting occurrences.

#### 2. The hyphenation-convention figure is a pre-edit measurement stated in a post-edit sentence

`#### Measured and deliberately left` says `Decision-<N>` hyphenation is "a live tree-wide convention
rather than retired vocabulary (38 occurrences across 25 `.py` files)". The tree now carries **37
across 25**. The arithmetic reconciles exactly — this pass removed one at
`optimizer/nested_planner.py::plan_connection_relation` (site 2), so 38 was true at the baseline —
but the sentence sits beside post-pass counts and reads as one. No action; noted so the integration
pass does not re-derive 37 and read it as a discrepancy.

### DRY findings

None from this cohort. It added no code, no literal, and no branch: the AST identity below is the
proof, and `scripts/review_inspect.py`'s repeated-string-literal section is unchanged by
construction (a docstring/comment edit cannot add a literal the helper sees). Recorded for the
integration pass's cross-cohort comparison:

- `optimizer/nested_planner.py` — 2x `opclasses`, 2x `_connection`
- `optimizer/nested_fetch.py` — 2x `select_for_update`, 2x `distinct`, 2x `windowed`
- `optimizer/lateral_fetch.py` — 5x `children`, 4x `resolve_expression`, 3x `lookup_name`, 2x `ROW_NUMBER() OVER (ORDER BY`, 2x `ORDER BY`
- `connection.py` — 3x `total_count`, 2x `_dst_node_type`, 2x `is_relation`

Control-flow hotspots, likewise unchanged and pre-existing: `nested_planner.py::plan_connection_relation`
383 lines / 24 branch nodes, `connection.py::_resolve_from_window` 323 / 26 (already carried forward
by R1b), `lateral_fetch.py::build_lateral_sql` 201 / 18. Django/ORM markers and imports: no delta.
No section skipped.

### The population, re-derived independently

**13 -> 0, per file, digit for digit with the artifact.** Instrument, over all 434 tracked `.py`
files: join wrapped comments (`re.sub(r"\n\s*#\s?", " ", src)`) **first**, then `\s+`->" ", then
`-`->" " and re-normalize, then count occurrences of `fallback\s+shapes?` case-insensitively —
never matching lines.

| state | total | nested_planner | test_walker | test_relay_connection | lateral_fetch | nested_fetch | test_nested_fetch |
|---|---|---|---|---|---|---|---|
| `HEAD` | 14 | 4 | 3 | 3 | 1 | **2** | 1 |
| this pass's baseline | **13** | 4 | 3 | 3 | 1 | 1 | 1 |
| worktree now | **0** | 0 | 0 | 0 | 0 | 0 | 0 |

`HEAD` reads 14 because R2's accepted `nested_fetch.py` module-docstring repair removed one before
this pass opened. That is the separation the artifact claims, measured rather than assumed.

The wrapped-site trap reproduces: a single-line `grep -oi "fallback shape"` over `HEAD` returns 13
occurrences and **zero** on `tests/optimizer/test_nested_fetch.py`, where the true count is 1. Any
re-measurement by grep reads 12 at the baseline and concludes a site is missing that was never
visible.

**No live vocabulary was collaterally swept.** Bare `fallback` went 602 in 112 files -> 587 in 111,
delta -15, and every unit of it is accounted for: 13 are this pass's retired-phrase removals, 3 are
R2's in `nested_fetch.py`, and `+1` is R2's in `test_library_api.py` (a file this pass shows a
zero-line diff against its baseline). The bare word remains live spec vocabulary — `### Decision 5`'s
heading ends "and a per-parent fallback", `### Decision 6` says "The residual fallback is the case
where *every* alias is itself one of the refusal arms" — so `test_divergent_all_keys_fallback_stays_unplanned`
keeping `fallback` in its name is correct on the merits, not merely a rename this pass could not make.

Residual sweeps all reproduce: `refusal arm(s)` **11 in 6 files** (2 of them R2's, both in
`nested_fetch.py`, verified against the baseline copies; 9 this pass's); retired ordinals
`shape <N>` and `arm <N>` **0** tree-wide; `four (numbered )?(fallback )?shapes` returns exactly one
hit, `tests/test_strawberry_patches.py #"The rejection of these same four shapes is the package view's job"`,
which is about the package `GraphQLView`'s decode rejection and unrelated to `spec-033`.

### Verdict on the sweep's judgement calls

**The simile: retiring it was right.** `tests/optimizer/test_walker.py::test_refusing_nested_fetch_strategy_leaves_selection_unplanned #"behaves exactly like the other refusal arms"`.
The simile's referent is "the other things `### Decision 6` lists", and the spec now calls those
arms; a reader who greps the spec for the old noun finds nothing, which is as true of a simile as of
a citation. The earlier cohort's stated cost — churn into a partition file carrying an executable
repair — does not survive: that file's AST identity is `1311b82c4ceb` at baseline and now, so R2's
repair is provably undisturbed. The half-retirement was the worse end state.

**`lateral_fetch.py`: `walker-owned` was false, and the replacement is verified in source, not
taken from spec prose.** The old sentence attributed all five items to the walker.
`django_strawberry_framework/optimizer/walker.py` decides **none** of the five nested-connection
refusal arms: it imports `hint_is_skip` and `classify_relation_join` only for its own list-path work
(`::_plan_relation` region, lines 956 and 1219), and its single mention of
`unwindowable_child_queryset_reason` is a comment pointing at `nested_fetch.py`.

The replacement claim, "decided before any strategy runs", checks out against `spec-033`
`### Decision 6`'s own siting **and** against control flow. In `nested_planner.py::plan_connection_relation`
the strategy is invoked exactly once, at `#"if strategy.plan(request, strategy_plan):"` (line 1396),
and all five named arms are decided strictly before it:

| arm named in the new sentence | decided at | line |
|---|---|---|
| sidecar input | `::_divergent_key_windows #"if has_connection_sidecar_kwargs(key_arguments):"` | 974 |
| `OptimizerHint.SKIP` | `::plan_connection_relation #"if hint_is_skip(hints_map.get(relation_field_name)):"` | 1111 |
| unwindowable child queryset | `::plan_connection_relation #"if unwindowable_child_queryset_reason(base_queryset) is not None:"` | 1227 |
| a window the slice arithmetic cannot express | `derive_connection_window_bounds` -> `except UnwindowableConnection` | 848 / 990 |
| an unwindowable relation kind | `::plan_connection_relation #"join = classify_relation_join(raw_relation_field)"` | 1193 |

Generalizing `DISTINCT` to "an unwindowable child queryset" is also right: `### Decision 6` arm 6
names `distinct` as one of five reasons under that arm, not an arm of its own.

**The keep/drop calls on Decision references are each correct.** Three kept (sites 2, 4, 12), ten
dropped or never present. Every kept one resolves: site 2's sentence asserts arm-level contract
verbatim ("each resolves per-parent through the shipped pipeline (and a whole-relation refusal is
therefore visible to strictness as unplanned)"); site 4's trailing citation is arm 9's no-leakage
sentence, untouched; site 12 is arm 1. Of the ten without one, none is a sentence that *should*
cite: sites 1/7/10 restate `### Decision 6`'s own per-response-key granularity sentence, sites 6/13
state a construction-order fact, site 3 is an inline section marker, site 8 mirrors "The residual
fallback is the case where *every* alias is itself one of the refusal arms", site 11 states a
behavior in `### Decision 5`'s literal words ("**`last: 0` is the one shape that always degrades**"),
and site 5 already carries a `spec-033 Decision 6` citation two lines above. No site trades a needed
citation for prose.

### Verdict on both qualification calls

**Qualification 1 (`::_finalize_queryset` step 6, `Decision 11` -> `spec-030 Decision 11`) — correct,
uncontroversial.** `spec-030` `### Decision 11 — The connection field owns its optimizer cooperation
point` is the sentence's own phrase; `spec-033` `### Decision 11 — Module and test-file locations` is
a module map that says nothing about cooperation points. `#"the cursor-parity invariant, spec-033 Decision 4"`
sits five lines above in the same docstring, so carry-forward actively pointed the reader wrong.

**Qualification 2 (`::_build_relation_connection_resolver` strictness comment, `Decision 6` ->
`spec-033 Decision 6`) — a defect correctly closed, not over-reach.** I checked both resolutions
against source. The module docstring's line 3 declares `Spec: docs/SPECS/spec-030-connection_field-0_0_9.md`,
and `spec-030` **does** have a `### Decision 6 — Sidecar-derived arguments via a synthesized resolver
signature`, whose whole subject is how `filter:` / `orderBy:` reach the field. The sentence is
literally about a `filter:` / `orderBy:` sidecar, so the module-default resolution lands on a
Decision that skims as correct and asserts something entirely different from what the comment
claims. The intended target — `spec-033` `### Decision 6` arm 1, "**Sidecar input** (`filter:` /
`orderBy:` arguments on the nested selection) — *per key*" — is what "explicitly-unwindowed" means.

Carry-forward would have resolved it right (`spec-033 Decision 8` four lines up), so this rests
entirely on the module default, which is the weaker of the two signals — that is the honest reading
and it is why the builder flagged it. It still lands as a defect rather than a convention, for the
reason the builder gave and I verified: a wrong target that reads as correct is the failure mode
this cycle has hit repeatedly, and it is the same mechanism the same pass fixed at
`tests/test_relay_connection.py`, where the module docstring cites `spec-032` Decisions 6/7/11 and
the file carries live bare `Decision 6` references belonging to **both** specs. Consistent treatment
across the two files is the right call. Keep it.

**The rejected for-instance — the rejection is correct.** `connection.py::DjangoConnection #"that is the opt-in ``<TypeName>Connection`` variant's job (Decision 4)"`.
Its only qualified neighbour is `spec-030 Decision 3` two sentences earlier — the *same* spec — and
`spec-030` `### Decision 4` says in its own words that `DjangoConnection[NodeType]` is "a generic
`ListConnection[NodeType]` subclass with **no** `total_count` field" while "an opted-in type's class
declares `total_count: int`". That is exactly the claim. Carry-forward and module default agree and
both are right; `spec-033` `### Decision 4` (windowed-prefetch planning under a reserved `to_attr`)
is not remotely plausible here, so there is not even a competing reading. Declining the suggestion
was correct.

### Spot-check of the twelve left references: I checked all twelve

Not a sample — the survey's realness was the open question, and twelve is cheap. I enumerated them
myself with the wrapped-comment-joined instrument and got the same twelve, across the same eight
passages, and read each against the target spec's Decision list rather than against adjacency:

1-2. Module docstring `#"The connection-class surface (Decision 3 / Decision 4):"` — both resolve
against `spec-030` (D3 the `first`+`last` guard the first bullet names; D4 the concrete
`<TypeName>Connection` factory the second bullet names). Directly under the `Spec:` line. Convention.

3-6. Module docstring `#"The window-pagination surface (Decision 5 / Decision 6 / Decision 7 / Decision 10):"` —
all four resolve against `spec-030`: D5 factory-function / Meta-only derivation ("the PascalCase
factory"), D6 sidecar-derived arguments ("synthesizes a resolver whose `__signature__` carries the
`filter` / `order_by` parameters"), D7 the composition pipeline (spelled out verbatim in the second
bullet), D10 the sync+async resolver paths. The `spec-032` parenthetical at line 17 does sit between
the `Spec:` line and this header, which is why it needed weighing at all; a module's own top-level
section headers under its `Spec:` declaration are the strongest case for the default. Convention,
agreed.

7. `#"spec-033 Decision 11 sites the hoist; Decision 4 states the cursor-parity invariant it serves"` —
same-spec continuation in one sentence. This is R2's accepted re-siting and it holds.

8. `::_resolve_from_window #"spec-033 Decision 4 / Decision 5"` — same-spec continuation.

9. `DjangoConnection #"(Decision 4)"` — adjudicated above.

10. `::_finalize_queryset #"Steps 5-6 of the Decision 7 pipeline"` — I verified the builder's claim
that this is the **first** reference in that docstring: it is (line 1562, ahead of the `spec-033
Decision 4` at 1576 and the `spec-030 Decision 11` at 1581), so nothing precedes it to carry
forward, and `spec-030` `### Decision 7 — Composition pipeline: visibility->filter->order->default-order->optimizer`
makes steps 5-6 the default-order and optimizer steps. Correct.

11. `::_resolve_connection_sync #"spec-030 Decision 7 / Decision 10"` — same-spec continuation.

12. `::_synthesized_connection_resolver #"spec-030 Decision 6 / Decision 7"` — same-spec continuation.

Twelve of twelve stand. The survey was real.

### Inverse proof, rebuilt independently

Instrument written for this review, not read from the build report: `ast.parse` -> strip every
module / class / function / async-function docstring (substituting `Pass()` where a body would
empty) -> `ast.dump(include_attributes=False)` -> `sha256[:12]`. Python 3.14.2.

**Evidence it can fail, three asserted controls per file, all in memory:**

- **must-see (insert)** — an AST-located `_w3_control_probe = 1` at column 0 above the first
  module-level `def`/`class`. Digest **moved on all ten files**.
- **must-see (delete)** — remove the last statement of the first multi-statement module-level
  function, via `ast.unparse`. Digest **moved on all ten files**. A second must-see in a different
  direction, because an insert-only control cannot distinguish "identity" from "the instrument only
  notices additions".
- **must-not-see** — prepend a sentence into the module docstring **and** append a trailing `#`
  comment. Digest **held on all ten files**.
- **Anchors fail loudly, not quietly.** Against a one-line scratch module carrying neither anchor,
  all three raise `CONTROL ANCHOR ABSENT: ...` rather than returning a passing-looking result.

**All five established digests reproduce, and so do the other five:**

| file | `HEAD` | this pass's baseline | now | identical |
|---|---|---|---|---|
| `django_strawberry_framework/connection.py` | `ecc47449f5ec` | `ecc47449f5ec` | **`ecc47449f5ec`** | yes |
| `django_strawberry_framework/optimizer/nested_fetch.py` | `302fbecdcc8d` | `302fbecdcc8d` | **`302fbecdcc8d`** | yes |
| `django_strawberry_framework/optimizer/walker.py` | `615fe2fe2be2` | `615fe2fe2be2` | **`615fe2fe2be2`** | yes |
| `tests/test_relay_connection.py` | `e357f45d6f2a` | `e357f45d6f2a` | **`e357f45d6f2a`** | yes |
| `examples/fakeshop/test_query/test_library_api.py` | `b5918390baa8` | `b5918390baa8` | **`b5918390baa8`** | yes |
| `django_strawberry_framework/optimizer/nested_planner.py` | `3e8f913d90ae` | `3e8f913d90ae` | `3e8f913d90ae` | yes |
| `django_strawberry_framework/optimizer/lateral_fetch.py` | `9abf1bbf2dc2` | `9abf1bbf2dc2` | `9abf1bbf2dc2` | yes |
| `tests/optimizer/test_walker.py` | `5e9799a71eee` | `1311b82c4ceb` | `1311b82c4ceb` | yes |
| `tests/optimizer/test_nested_fetch.py` | `b459bd8740f2` | `b459bd8740f2` | `b459bd8740f2` | yes |
| `tests/optimizer/test_extension.py` | `349aa5422d06` | `bd92ca53429b` | `bd92ca53429b` | yes |

**No executable byte moved in any of the ten.** The two `HEAD`-vs-baseline disagreements —
`test_walker.py` and `test_extension.py` — are R2's two failability-proved behavior repairs, which
is exactly where a difference should be and nowhere else.

**Re-running the mutant column, which is the stronger check.** Re-implementing R3's probe name
(`_dsf_r3_control_probe`) rather than my own, my instrument reproduces **all eight** recorded mutant
digests exactly: `9e064e8ada97`, `69c0287962c6`, `ee0988f2f6a3`, `f4f06ced6d0b`, `0eb533de533e`,
`a9a5a2d06ce2`, `d071cc963c86`, `a1edbeee834d`. Two instruments agreeing on a mutant are running the
same algorithm; two agreeing only on an identity might both be reporting a null.

### The baseline separation, verified rather than assumed

`HEAD` is not the baseline for five of the seven pass-1 files nor for `connection.py`. The build
report's scratch copies exist at `.../scratchpad/r3/before/`, timestamped 20:20 (pass 1) and 20:33
(pass 2), both ahead of the corresponding edits. I validated them rather than trusting them: each
copy's `HEAD`-difference is R2-shaped and each copy's worktree-difference reproduces the artifact's
own changed-line count.

| file | `HEAD` -> baseline (R2 et al.) | baseline -> worktree (this cohort) | artifact claims |
|---|---|---|---|
| `optimizer/nested_planner.py` | 0 | 9 | 9 |
| `optimizer/nested_fetch.py` | 37 | 4 | 4 |
| `optimizer/lateral_fetch.py` | 0 | 8 | 8 |
| `tests/optimizer/test_walker.py` | 80 | 8 | 8 |
| `tests/optimizer/test_nested_fetch.py` | 0 | 4 | 4 |
| `tests/optimizer/test_extension.py` | 19 | 10 | 10 |
| `tests/test_relay_connection.py` | 43 | 12 | 12 |
| `django_strawberry_framework/connection.py` | **7** | **12** | 12 |
| `optimizer/walker.py` | 24 | **0** | untouched |
| `examples/fakeshop/test_query/test_library_api.py` | 61 | **0** | untouched |

Eight for eight. `connection.py`'s `git diff` carries R2's two hunks (7 lines: the `optimizer/plans.py`
hoist comment and the step-5 `Decision 11` -> `Decision 4` re-siting) plus this pass's two (12 lines).
The separation is real. No `git stash` / `checkout` / `restore` / `worktree` was run in this review.

### Hot-path budget

Declared hot: `optimizer/nested_planner.py`, `optimizer/nested_fetch.py`, `optimizer/lateral_fetch.py`,
`connection.py`. My obligation is that the number **exists and reproduces as recorded**, not whether
it is good.

All four carry a recorded before/after with a metric, a command, an iteration count, and a delta;
all four reproduce under my instrument: `3e8f913d90ae` / `302fbecdcc8d` / `9abf1bbf2dc2` /
`ecc47449f5ec`, **delta 0 each**. For a comment-only edit the demonstrated zero delta is the honest
number, and the AST identity is that record — and the mutant column I reproduced above is what makes
it a measurement rather than a null. No missing number; nothing to escalate on cost.

### Failability proofs

Empty re-run set, and legal here: this cohort introduces no boundary, guard, gate, or rejection path
that could meet the floor. I established that from the diff content, not from the build report's
assertion — all fifteen hunks across the eight files are inside a comment or a docstring, and the
ten-file AST identity is the mechanical proof that nothing executable moved.

### Gates re-run

- `uv run python scripts/check_citations.py --check` -> `OK: 828 citations resolve (738 in 431 .py files, 90 in KANBAN.md)`, rc 0. Exactly the recorded figure.
- **No wrapped citation was introduced by the five reflows.** The gate is structurally blind to one,
  so I checked separately: applying the gate's own `([\w][\w./]*\.py)::([A-Za-z_][\w.]*)` pattern to
  the raw source and to the wrapped-comment-joined source gives **identical counts in all eight
  files**, baseline and now (`nested_planner` 11, `nested_fetch` 9, `lateral_fetch` 6, `test_walker` 4,
  `test_nested_fetch` 0, `test_extension` 8, `test_relay_connection` 11, `connection` 12). Swept
  tree-wide over all 434 tracked `.py` files: **zero** files carry a citation visible only when
  joined. No reflow broke a citation into or out of the reflowed text.
- `uv run ruff format --check <8 files>` -> `8 files already formatted`, rc 0 (argc printed as 8 and each path existence-checked first, per this file's own `$FILES`-collapse trap).
- `uv run ruff check <8 files>` -> `All checks passed!`, rc 0.
- `uv run python scripts/check_trailing_commas.py --check <8 files>` -> rc 0; an independent `LC_ALL=C grep -n '[^\x00-\x7F]'` over the eight returns nothing.
- `uv run pytest tests/optimizer/ tests/test_connection.py tests/test_relay_connection.py --no-cov -q` -> **1005 passed**.
- `uv run pytest examples/fakeshop/test_query/test_library_api.py tests/test_keyset_connection.py --no-cov -q` -> **224 passed**.
- `uv run pytest tests/ --no-cov -q` -> **5967 passed, 40 skipped**.

All three suite figures match the build report exactly. No `--cov*` flag was used anywhere.

### Dispatched findings checklist: ten boxes, ten landed fixes

| box | landed | evidence |
|---|---|---|
| P1 `nested_planner.py` x4 | yes | 4 sites in the baseline diff, incl. the known-hardest `#"for each Decision-6 fallback shape"` -> `#"for each spec-033 Decision 6 refusal arm"` (both retired spellings) |
| P2 `test_walker.py` x3 | yes | 3 sites incl. the simile; AST identity `1311b82c4ceb` unchanged |
| P3 `test_relay_connection.py` x3 | yes | 3 sites; `e357f45d6f2a` unchanged |
| P4 `lateral_fetch.py` x1 + ownership | yes | noun **and** the false `walker-owned` claim; replacement verified against source above |
| P5 `nested_fetch.py` singular | yes | `::NestedConnectionRequest`; `302fbecdcc8d` unchanged |
| P6 `test_nested_fetch.py` wrapped | yes | the site invisible to a single-line grep |
| R-a routed partition | yes | both files edited |
| R-b routed bare `Decision 11` | yes | pass 1 the two `test_extension.py` refs, pass 2 `connection.py::_finalize_queryset` step 6 |
| R-c routed singular | yes | same site as P5 |
| R-d routed deferrals | yes | the pass-1 R-b deferral named its site; the 7-site hyphenation deferral is recorded with its measurement and reasoning |

No tick without a fix; no unaddressed box. The population measurement (13 -> 0, per file) is the
independent cross-check that P1-P6 are complete rather than merely ticked.

### No-regression and scope

- **The three `## Escalations` are untouched.** `optimizer/walker.py` shows a **zero-line** diff
  against its baseline and holds `615fe2fe2be2`, so the ten dead aliases stand. `optimizer/plans.py`
  and `types/resolvers.py` are not in this cohort's changed-file set at all, so
  `window_partition_for_prefetch` and the `connection_to_attr` probe are untouched.
- **The seven hyphenated `Decision-6` deferrals are intact and recorded.** I measured them
  independently: 7 survive, sited exactly as the artifact states (`nested_planner.py` 1,
  `utils/connections.py` 1, `test_extension.py` 1, `test_walker.py` 1, `test_relay_connection.py` 3).
  The baseline carried 8 — `nested_planner.py` had 2 — and the one removed is site 2, the genuine
  defect that carried the retired heading noun alongside the hyphen. The deferral is recorded with
  its reasoning in `#### Measured and deliberately left`, not silently dropped.
- **Both spec files were read-only to this cohort.** `docs/SPECS/spec-033-connection_optimizer-0_0_9.md`
  and the rationale carry mtimes of 19:08 and 19:06, ahead of both of this pass's editing windows
  (20:20-20:27 and 20:33-20:35). Neither appears in the cohort's changed-file set.
- **`examples/fakeshop/test_query/test_products_api.py` is byte-identical to `HEAD`** and clean in
  `git status`.
- **No partition breach.** The cohort's changed-file set, established from diff content, is exactly
  the eight `.py` files on its writable list plus the mid-flight `connection.py` addition. The six
  concurrent-session files carry mtimes of 19:48-20:16, all ahead of both editing windows; none was
  written by this cohort and none was reverted or tidied.
- **No live mutation.** No `ACTIVE-MUTATION.json` anywhere in the tree, and a tree-wide grep for
  either pass's control-probe identifiers (`_dsf_r3_control_probe`, and my own `_w3_control_probe`)
  returns nothing on disk. Both instruments mutate in memory only.
- **My own carve-out was not used.** I made no source mutation at all, so there is nothing to
  revert; the ten digests re-read at the end of this review are identical to the ones I read at the
  start.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` is empty and the file is clean in
`git status`. `__all__` and the re-export list are unchanged. No new public exports.

### CHANGELOG sanity

Not applicable; slice did not modify `CHANGELOG.md`.

### Documentation / release sanity

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces. The `.md` files dirty in
the tree belong to Slice 0, Slice 2, and the concurrent session.

### Floor verification

Plan declares scope `none`, and that ground holds against the actual diff: every one of the fifteen
hunks is inside a comment or a docstring, so no Django / Strawberry / channels integration seam is
touched — the ten-file AST identity is the mechanical form of that claim. The shared `.venv` was not
mutated by this review (no `uv pip install` was run). Read, not recalled: `uv pip list` reports
`django 6.1`, `strawberry-graphql 0.324.0`, `channels 4.3.2`, and `uv run python` reports `3.14.2` —
none of which is the supported floor (Django 5.2.16 / Python 3.10 / strawberry-graphql 0.316.0), and
none of which this cohort's diff can reach.

### Static helper use

`uv run python scripts/review_inspect.py <file> --output-dir docs/shadow` run on all four production
files this cohort touched: `optimizer/nested_planner.py`, `optimizer/nested_fetch.py`,
`optimizer/lateral_fetch.py`, `connection.py`. All four sections walked — Django / ORM markers,
repeated string literals (recorded under `### DRY findings`), control-flow hotspots, imports. **No
section skipped.** Nothing in any of the four is attributable to this cohort, which the AST identity
makes structural rather than a judgement.

### What looks solid

- The population instrument is the right one and is reproducible: joining wrapped comments **before**
  normalizing whitespace is what makes the 13th site visible, and the build report says so with the
  falsifiable claim (grep returns nothing on that file) rather than asserting completeness.
- Every replacement is written from `### Decision 6` / `### Decision 5` as they now stand. Sites 8
  and 11 are near-verbatim spec sentences; site 5's replacement claim is the one Decision 6 actually
  states.
- The `lateral_fetch.py` repair found a **second, unrelated defect** — a false ownership claim — in a
  sentence dispatched only for its noun, and fixed it against source rather than against the
  neighbouring file's wording. That is the correct instinct: the adjacent repaired sentence is about
  what the planner *owns*, this one about what never *reaches* a strategy, and those are different
  sets.
- No process provenance anywhere in the fifteen hunks; no test renamed in either direction; no
  citation dropped that should have stayed.
- The pass-1 deferral of the real R-b site was made **by name**, with the box left unticked, rather
  than ticked against the file the dispatch happened to name. That is the behavior that made the
  mid-flight correction possible.

### Temp test verification

None written. Nothing in this cohort has behavior to pin, and the ten-file AST identity plus the
three reproduced suite figures cover what a temp test could have shown. No `docs/builder/temp-tests/r3-review/`
directory was created. All review instruments live outside the repository, under this session's
scratchpad.

### Notes for Worker 1 (spec reconciliation)

1. **Carried forward unchanged from the build report, all four still standing:** the
   `### Decision 6` citation-convention sentence (its case is now measured across 13 sites, not 4);
   the `lateral_fetch.py` false-ownership record, which I independently confirmed against
   `walker.py`'s body and not only against spec prose; the observation that a Decision-heading
   rename owes a tree-wide sweep of the retired heading's **nouns**; and the pass-2 note that a
   file-level `Spec:` line is a good default only while the file is single-spec. I endorse all four.
   The fourth is the sharpest and belongs in `AGENTS.md`'s source-reference rule if anywhere: this
   cohort found a live site where the module default and the nearest qualified neighbour disagree
   and **the wrong one reads as correct**.

2. **The same bare-`Decision N` ambiguity class is larger in `tests/test_relay_connection.py` than
   the one site this cohort qualified, and no gate can see it.** Measured with the same
   wrapped-comment-joined instrument: that file carries **20** `Decision N` references, **15 of them
   bare**, while its module docstring cites `spec-032` Decisions 6/7/11 and its body carries live
   references belonging to `spec-032`, `spec-033`, and `spec-030` at once. At least two bare
   `Decision 6` references there are `spec-032`'s (the Node-shaped-schema and `filterset_class`
   contract sentences) and several bare `Decision 5`/`Decision 4` references are `spec-033`'s. Every
   one I read is *correct*; the exposure is that the file has no single default a reader can fall
   back on. Out of scope for this cohort — sweeping it would be the unrelated cleanup Worker 2's
   `## Scope` forbids — and recorded here rather than as a finding so the integration pass can decide
   whether it wants a cohort or a convention.

3. **Low 1 above is worth a line in the integration pass's own counting record**, not a fix. The
   `27` is the only number in either build report that does not reproduce, out of roughly thirty I
   checked. It is a mis-stated size of a correct enumeration, which is a milder version of this
   cycle's standing lesson rather than a new one.

### Review outcome

`review-accepted`.

No High and no Medium. Both Lows are artifact-only mis-statements of a count's subject with no
source, no box, and no gate implicated, and neither warrants a round-trip on the cycle's last
source-touching cohort; both are recorded for the integration pass instead. Everything that could
have forced `revision-needed` was checked and is clean: no executable byte moved in any of ten files
under an independently written instrument that reproduces all five pinned digests **and** all eight
mutant digests; no comment left false — the one ownership claim that was false is fixed and verified
against source; no citation pointing at the wrong Decision, and no wrapped citation introduced
anywhere in the tree; all ten boxes ticked with a matching landed fix; no live mutation; no partition
breach; hot-path numbers present and reproducing for all four hot files.

The two qualification calls both stand. The first is unambiguous. The second rests on the
module-default mechanism rather than carry-forward, which the builder said plainly rather than
overstating, and it lands as a defect because `spec-030`'s own `### Decision 6` is about the same
`filter:` / `orderBy:` sidecars the sentence names — the wrong target reads as correct, which is the
exact shape this cycle keeps paying for.
