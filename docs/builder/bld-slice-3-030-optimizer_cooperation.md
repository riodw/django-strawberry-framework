# Build: Slice 3 — verify optimizer cooperation; bound the connection-aware-planning gap

Spec reference: `docs/SPECS/spec-030-connection_field-0_0_9.md` (as-audited lines 72-75 for the slice checklist; Decision 11 `Scope honesty` + `Forward design input for 033`; Test plan lines 501-504; DoD item 6)
Rationale companion: `docs/SPECS/appx/spec-030-connection_field-0_0_9-rationale.md`
Build plan: `docs/builder/build-030-connection_field-0_0_9.md`, checklist Slice 3
Status: final-accepted

**Closure path taken: procedural closure (`BUILD.md` `### Procedural-closure slices`), one combined Plan + Final-verification block, `Status: final-accepted` in this single pass.** The reason, stated explicitly: **the load-bearing half of Slice 3's contract is satisfied at `HEAD` and the other half was deliberately replaced by later work** — so there is **no CODE GAP**, and the only work the slice owes is spec reconciliation, which is Worker 1's alone. No Worker 2 build and no Worker 3 review were dispatched, and none is owed: this pass ships no `.py` change (proved below by an inverse diff, not asserted).

The replacement is the cycle's largest reconciliation item and is treated as its own case rather than a silent tick: sub-check 2 contracted an assertion that the derived plan is **empty**, and the shipped test at that exact name now asserts the opposite. That is not a code gap — the code is right and the spec's claim is what must change (see `### Sub-check 2`).

- **Hot-path declaration: none.** This pass writes two `.md` files and no `.py` file, so no code runs differently and no number can move. The build plan's conditional clause (a change inside `connection.py::_pipeline_sync` / `::_pipeline_async` / `::_resolve_from_window` / `::_finalize_queryset` or `optimizer/extension.py::apply_connection_optimization`) is not triggered — and this slice's audit read `_finalize_queryset` and `apply_connection_optimization` end to end, so the absence of a change to either is a finding rather than an oversight.
- **Floor-verification scope: none.** The plan's conditional clause fires only on a `.py` change under `connection.py`, `types/base.py`, `types/definition.py`, or `optimizer/extension.py`. No floor venv was built and none is owed. The shared `.venv` was not mutated.
- **Static inspection helper: skipped, with the reason, and the trigger named because this slice sits squarely inside it.** `BUILD.md` `### When to run the helper during build` makes it **mandatory** when the plan adds logic to anything under `optimizer/` — which is this slice's entire subject. The plan adds no logic anywhere: the audit closed with an empty CODE GAP list, so there is nothing for a builder to implement in `optimizer/extension.py` (1549 lines) or `connection.py` (2077 lines), and no `docs/shadow` output exists to cite. Had the audit found a gap in either, the helper would have been run as `uv run python scripts/review_inspect.py <file> --output-dir docs/shadow` and its output cited here.
- **Boundary count: 0.** No guard, cap, rejection path, or validation branch is added, so no failability proof is owed and the `### Slice splitting` question does not arise. The two boundaries this slice's contract covers are shipped and pinned: `apply_connection_optimization`'s no-optimizer short-circuit and its no-registered-model short-circuit, each with its own test (`tests/test_connection.py:1485`, `:1499`).
- **Environment.** `uv run` works on this tree; both `uv run` and `.venv/bin/python` were used and are noted per command.
- **No `ruff`.** Both `ruff format` and `ruff check` are no-ops against `.md`, and running them repo-wide would touch a concurrent session's dirty `.py` files. Not run, deliberately.

## Working-tree baseline re-read (`git status --short`, start and end of pass)

The build plan's baseline list is a snapshot and has moved again. Dirty-and-out-of-scope, never edited and never reverted (`AGENTS.md` rule 34):

`AGENTS.md`, `pyproject.toml`, `uv.lock`, `django_strawberry_framework/__init__.py`, `django_strawberry_framework/exceptions.py`, `django_strawberry_framework/scalars.py`, `scripts/bug_hunt.py`, `tests/base/test_init.py`, `tests/test_bug_hunt.py`, `tests/filters/test_base.py`, `tests/filters/test_factories.py`, `tests/filters/test_inputs.py`, `tests/forms/test_converter.py`, `tests/forms/test_inputs.py`, `tests/test_exceptions.py`, `tests/test_resource_policy.py`, `tests/test_scalars.py`, `tests/test_schema.py`, `tests/test_sets_mixins.py`, `tests/test_views.py`, `tests/mutations/test_operations.py` (untracked), `docs/review/**`, `docs/dry/**`, `docs/bug_hunt/**`.

**New since Slice 2's list, and appearing MID-PASS:** `tests/forms/test_sets.py` (M). Out of scope. `docs/SPECS/spec-030-connection_field-0_0_9.md` and the untracked companion show dirty from this cycle's own prior passes.

---

## Plan (Worker 1)

### Spec status-line re-verification

Read on entry: spec lines 1-11 (title, shipped-in line, `Status:`, owner, Predecessors, the rationale-companion pointer). The card is still `DONE-030-0.0.9`, the spec is still the final implementation record, the five-slice decomposition and the joint-`0.0.9`-cut version boundary hold, and no predecessor doc it names has been deleted. **Two status-line clauses were falsified and both were edited this pass** — they are this slice's own subject rather than a general header sweep, so they are recorded here and again under `### Spec changes made`:

- Line 5's Slice-3 summary read "bound the connection-aware-planning gap to the sibling `DONE-033-0.0.9` card". The gap it names is closed, so the summary now reads "name the nested-connection planning boundary the sibling `DONE-033-0.0.9` card owns" — which is what Slice 3 actually delivers as a durable statement.
- Line 9's Predecessors tail asserted the glossary carries all four entries at `planned for 0.0.9` and that this card "leaves the fourth planned". Slices 1 and 2 both flagged it and both correctly declined to fix it. Reconciled to a status-free scope statement.

### DRY analysis

- **Helper inventory checked — not applicable, and why.** The package-wide AST inventory exists to stop a builder writing a duplicate *code* shape. This pass writes no code and adds no helper, constant, validation branch, coercion utility, or test helper, so there is no candidate to inventory against. Recorded rather than skipped so a later pass does not read the absence as an omission. The `.py` surface is byte-unchanged (proof below). The audit read the surface it needed directly — `optimizer/extension.py`, `optimizer/plans.py`, `connection.py`, `orders/sets.py`, `tests/test_connection.py`, `tests/optimizer/test_extension.py`, `examples/fakeshop/test_query/test_library_api.py`, `examples/fakeshop/config/schema.py` — which is what the inventory would have indexed.
- **Existing patterns reused.** The reconciliation reuses the companion's documented append convention (a `**Post-ship:**` bullet under the owning Decision's `### Changes this Decision underwent`) and, for the finding that belongs to no single Decision, the `## Non-Decision deliberation` subsection shape Slices 1 and 2 established — a **new** `###` subsection this time rather than an extension, because the population it names (the empty-plan claim's out-of-Decision sites) is disjoint from the symbol-citation population that subsection already closes. Extending it would have merged two closed populations into one open-looking one.
- **New helpers justified: none.**
- **Duplication risk avoided.** The one real duplication risk in a spec/rationale split is stating the same correction in both files, which then drift. Prevented by rule: the spec carries only the corrected contract, present tense, with no trace of what it used to say; the companion carries only the change record. Verified mechanically after the edits — `flat walker` / `flat-walker`, `connection-unaware`, `empty in 0.0.9`, `empty for every connection`, `deferred sibling`, `currently empty`, `plans ()` and `A/B control` are each **0** occurrences in the spec and non-zero only in the companion (counts below).

### Slice 3's contract, audited against `HEAD`

Method note, because it decides what this audit is worth: **a grep proves the symbol, not the claim.** Every sub-check below was checked by reading the function body or the test body against the spec sentence. For this slice that discipline is not optional — both named tests **exist under the exact names the spec gives**, so a name-only audit would have reported the whole slice satisfied and missed that one of them now asserts the negation of its contract.

**Sub-check 1 — the cooperation point the FIELD owns, called before the slice, publishing a plan.** SATISFIED, and this is the load-bearing half no later work superseded.

- The call site is `connection.py::_finalize_queryset`, step 6 of the Decision-7 pipeline, and **both** of its exits go through the helper: the keyset-mode branch returns `apply_connection_optimization(target_type, qs.order_by(*cursor_field), info)` (`connection.py:1572`) and the ordinary offset tail returns `apply_connection_optimization(target_type, qs, info)` (`:1581`). So the keyset path added by later work did not route around the cooperation point.
- `optimizer/extension.py::apply_connection_optimization` resolves the model from `registry.model_for_type(target_type)` — never from `info.return_type` — and delegates to `DjangoOptimizerExtension.apply_to`, whose step 2 is `_publish_plan_to_context(plan, info)`. The publish happens unconditionally once there are field nodes, before the `plan.is_empty` early return, so a plan reaches `info.context` whether or not it has content.
- The "which the schema middleware never does for a connection field" half holds by code, not by assertion: `DjangoOptimizerExtension.resolve` gates on `info.path.prev is None` and hands the result to `_optimize`, whose first act is `normalize_query_source(result)` followed by `if not is_queryset: return result`. `ConnectionExtension.resolve` returns a connection object, so `_optimize` returns it untouched and never reaches `apply_to`. The middleware cannot publish for a connection field.
- Pinned by `tests/test_connection.py::test_root_connection_field_queryset_is_planned`, which asserts `getattr(ctx, "dst_optimizer_plan", None) is not None` after a real `execute_sync` over a root `DjangoConnectionField`.

**Sub-check 2 — "the derived plan is asserted empty in `0.0.9`". DELIBERATELY REPLACED by later work; the spec's claim is what changed.** This is the case the task flagged and it is worth stating precisely rather than ticking.

- At `HEAD`, `apply_connection_optimization`'s signature is `(target_type, queryset, info, *, selection_extractor: SelectionExtractor = _connection_node_child_selections)`. The **default** is the `edges { node { ... } }` navigator. Its own docstring states the intent: the walker "must see the same child selection list it would receive for a list field over the node type".
- `test_root_connection_field_queryset_is_planned` now asserts `plan.select_related == ("category",)`, `plan.prefetch_related == ()`, and `plan.only_fields == ("id", "name", "category_id", "category__id", "category__name")` — the full projection, not an empty tuple — plus the planned resolver key `"PlanItemNode.category@items.edges.node.category"` in `ctx.dst_optimizer_planned`.
- Its many-side twin `test_root_connection_field_queryset_prefetches_node_many_relation` asserts `prefetch_to == ["items"]` with `select_related == ()`. Two tests, opposite relation kinds, both non-empty.
- **Provenance, established rather than assumed.** `git log -S'selection_extractor' -- optimizer/extension.py` puts the seam in commit `a3f84ea9` (2026-06-11), a post-`032` hardening pass with no card and no spec of its own, touching `optimizer/extension.py`, `optimizer/walker.py`, `tests/test_connection.py` and one example test. `git show a3f84ea9 -- tests/test_connection.py` shows that same commit deleting the "SCOPE-HONEST ASSERTION" docstring block and flipping `assert plan.select_related == ()` to `== ("category",)`. So the root half was closed **before** `DONE-033-0.0.9`, which then shipped the nested half; `docs/SPECS/spec-033-connection_optimizer-0_0_9.md` records the identical finding from its own side as the card-premise staleness its Revision 1 opens with. **The handed-forward inventory's "closed by `DONE-033-0.0.9`" is therefore right about the outcome and wrong about the agent for the root half** — a distinction that matters because the spec must not restate `033`'s contract as `030`'s.
- **The claim was true when written.** Reading the deleted docstring confirms the reasoning was explicit and correct for the walker as it then stood. This is recorded in the rationale as a deliberate intra-cohort sequencing boundary, not as a mistake.

**Sub-check 3 — the alpha constraint documented honestly, no silent cap, named in `docs/GLOSSARY.md` and `## Edge cases and constraints`.** The obligation was discharged and the constraint it described no longer exists in that form, so the sub-check needed re-aiming rather than ticking or failing.

- `docs/GLOSSARY.md` at `HEAD` carries `## Connection-aware optimizer planning` at `**Status:** shipped (0.0.9)` (index row `:103`, body `:387`), and the `DjangoConnectionField` body (`:557`) no longer carries an empty-plan caveat — it states the field owns its cooperation point and that the same seam feeds nested window planning. So the "no silent cap" obligation is still discharged; what is documented is now an ownership split rather than a gap.
- The spec's `## Edge cases and constraints` nested-connection bullet still described the flat walker's connection-unawareness. Reconciled, and split into a root bullet and a nested bullet, because those two cases now have different owners and one sentence could not carry both truthfully.

**Sub-check 4 — the Strictness-mode `"raise"` assertion, and the B1-B8 no-regression check.** Both tests exist. The strictness one exists **with a changed subject**, which the spec must not keep mis-describing.

- `tests/test_connection.py::test_nested_connection_unplanned_raises_under_strictness` exists and passes, and asserts `"Unplanned N+1: items"` in `result.errors`. But it now calls `_field_schema(category_node)` with **no optimizer extension** and seeds `SimpleNamespace(dst_optimizer_planned=set(), dst_optimizer_strictness="raise")`. Its own docstring says so: "This test intentionally installs no optimizer extension ... so the gap is genuine". Commit `a3f84ea9` is where that changed, in the same diff that flipped sub-check 2. So the test no longer guards "the seam the connection-aware card closes" — with the optimizer installed, that relation IS planned (sub-check 2's twin proves it on the same relation). What it guards now is that the connection's `edges { node }` response path does not blind `types/resolvers.py::_check_n1`. A retired guard would have been acceptable given the seam closed; this one was not retired, it was re-aimed, and the spec described the old aim.
- `tests/optimizer/test_extension.py::test_optimizer_helper_extraction_no_regression` exists, and its assertions are the right ones: a non-connection root field still gets `select_related == ("category",)`, and a spy on `apply_to` records `delegations == [(ItemType, Item)]`, proving `_optimize` delegates with the resolved `(origin, model)` rather than the helper inferring them. No regression, and the delegation direction is pinned, not just the outcome.

**Sub-check 5 — the `## Test plan` names two tests.** Both names resolve at `HEAD` (`tests/test_connection.py:1293` and `:1370`) — the first slice of this cycle where the Test plan's named rows all existed. But **the plan's description of the first is now the negation of what it asserts**, and it omits the many-side twin `test_root_connection_field_queryset_prefetches_node_many_relation` (`:1343`) entirely. Every test name in the Slice-3 Test plan was confirmed present by reading its body, and every claim the plan makes about what those bodies assert was checked line by line.

**The `Forward design input for 033` sub-block — a deliberate decision, per the task.** Verdict: **both**, and it graduated from advice to a live constraint. Reasoning and evidence:

- Its premise ("when `033` makes the derived plan non-empty") is now satisfied for root connections, so steps 3 and 6 of the Decision-7 pipeline compose on every request that supplies a to-many `orderBy` — this is `030`'s own pipeline, not a forward-looking concern about another card.
- The interaction is **answered in shipped code**, and the answer is stated at the symbol that owns it: `django_strawberry_framework/orders/sets.py::OrderSet._resolve_order_expressions` orders a to-many path through `Min`/`Max` so exactly one row per parent survives the `GROUP BY`, and its docstring already spells out the connection consequence ("A root `DjangoConnectionField` applies this grouped queryset before its normal cursor slice ... a to-many aggregate order never sits below the optimizer's `_dst_row_number` window annotation"), citing `spec-030 P1-B`.
- It is pinned **live with the optimizer installed**: `examples/fakeshop/config/schema.py` builds the fakeshop schema with `extensions=[lambda: _optimizer]`, and `examples/fakeshop/test_query/test_library_api.py::test_genre_connection_order_by_to_many_no_node_multiplication` drives `allLibraryGenresConnection(orderBy: [{ books: { title: ASC } }])` over `/graphql/`, asserting no duplicated node and `totalCount == 2`. So the plan step really does run on the grouped queryset in that row.
- Therefore: the **constraint** is contract and stays in the spec (restated as a property of the shipped pipeline under `Aggregate-ordering coexistence`, cited to the symbol and the live test); the **fact that it was once design advice to an unshipped card** is history and goes to the rationale. Leaving it as forward advice would have addressed a closed audience; deleting it outright would have dropped a live invariant.

### CODE GAP list

**Empty.** No sub-check of Slice 3 is unimplemented, silently narrowed, or dropped. Nothing is dispatched to Worker 2, and nothing owes a failability proof.

The direction of divergence is the same one Slices 1 and 2 recorded, and here it is at its strongest: the code does **more** than the `0.0.9` text claims — a root connection now derives the full plan the text says is empty — while the one contract the text asserts that later work did NOT touch (the field-owned, pre-slice, plan-publishing cooperation point) is intact on both the offset and keyset paths. The single divergence that is not a widening is the strictness test's re-aimed subject, and that is a description defect in the spec rather than in the test.

### Spec slice checklist (verbatim, as audited)

Quoted **as the spec stated them at the start of this pass**, before the reconciliation below — deliberately, so the boxes audit the shipped code against the contract as written when the card shipped, rather than against text this same pass rewrote to match the code. A box is ticked because the **shipped state satisfies it** (this cycle's inversion of the usual tick discipline). One box carries an explicit note instead of a silent tick, because its contract was deliberately replaced rather than merely satisfied.

- [x] Tests that a root `DjangoConnectionField`'s pre-slice queryset is run through the extracted helper — the cooperation point the field now owns, NOT the middleware: the field publishes an [`OptimizationPlan`][glossary-djangooptimizerextension] to `info.context` before the slice (which the schema middleware never does for a connection field, since it cannot reach the queryset behind `ConnectionExtension`). ~~The derived plan is **empty in `0.0.9`** (no `select_related` / `prefetch_related` / [`only()`][glossary-only-projection]) because the flat walker is connection-unaware; a non-empty plan — root scalar/FK projection included — lands with the connection-aware walker ([`DONE-033-0.0.9`][kanban]), which plugs into this exact cooperation point with no [`connection.py`][connection] change (per [Decision 11] "Scope honesty").~~
  - **Ticked for its first clause; struck clause DELIBERATELY REPLACED, not satisfied and not deferred.** The cooperation-point half is satisfied at `HEAD` (sub-check 1). The empty-plan half was a real, correctly-reasoned `0.0.9`-cohort-internal boundary that later work removed on purpose: `apply_connection_optimization` defaults its `selection_extractor` to the `edges { node }` navigator, and the test at the very name this box cites asserts the opposite of the struck clause. A box whose contract was replaced is not the same as one that failed, so it is called out here rather than ticked silently — and the replacement is the spec change recorded as S4/S12/S13/S15/S17 below, not a code finding.
- [x] Document the alpha constraint honestly: nested `edges { node { ... } }` connection selections are functional but the helper's plan is bounded by the flat walker's connection-unawareness — descending `edges { node }` into nested relations is the sibling [`DONE-033-0.0.9`][kanban] card, which plugs into this card's cooperation point (a walker change, not a field retrofit). No silent cap — named in [`docs/GLOSSARY.md`][glossary] and Edge cases and constraints.
  - Ticked on the obligation, which is what a tick means: the constraint was documented in both named places and remains documented in both, with no silent cap at any point. Its **content** changed with the seam (an ownership split where there was a gap), which is the reconciliation, not a shortfall.
- [x] Package coverage: a [Strictness mode][glossary-strictness-mode] `"raise"` assertion that an unplanned nested-connection access still surfaces as an N+1, guarding the seam the connection-aware card will close; a no-regression check that the existing B1–B8 optimizer suite is unaffected by the `_optimize` helper extraction.
  - Both assertions exist and pass. The strictness row's **subject** was re-aimed when the seam closed (it now installs no optimizer, so the unplanned access is genuine rather than a consequence of walker blindness); the guard was not retired, so the spec may keep claiming it exists — it may not keep claiming what it guards. Reconciled as S15/S17.

### Implementation steps

None. No `.py` step exists to plan: the audit closed with an empty CODE GAP list, so this artifact's work is the reconciliation recorded under `### Spec changes made (Worker 1 only)`.

### Test additions / updates

None. No executable surface changed, and every assertion Slice 3's contract needs already exists — including one the spec never named (the many-side prefetch twin). No temp test was written; none would have anything to demonstrate. The shortfall the audit found is in the spec's *description* of the tests, fixed as S15.

### Implementation discretion items

None. Every judgement call is decided and recorded, including the four that could have gone either way: whether the replaced sub-check gets a tick, whether `## Out of scope` / `## Non-goals` drift, what to do with the `Forward design input for 033` block, and whether to fix the parity table's `DONE-032-0.0.9` row while fixing its `033` twin (decided: no, and handed forward with the reason).

---

## Final verification (Worker 1)

### Populations swept, instruments used, and counts

`BUILD.md` `## Claims are proven mechanically`: every number below is re-derivable by running the named token against the named file, and each population was confirmed with a **second instrument of disjoint vocabulary** — a site that omits the term you keyed on is invisible to that instrument. Counts are **occurrences** (`grep -o … | wc -l`), not matching lines. Both sweeps deliberately include headings and fenced blocks (`grep` over the raw file, so neither is excluded).

| Population | Instrument A (pre-edit) | Instrument B, disjoint (pre-edit) | Union of sites | Post-edit |
|---|---|---|---|---|
| The `Connection-aware optimizer planning` **status** claim | the status vocabulary: lines carrying `planned` AND (`connection-aware` OR `033`) — 11 lines: 9, 75, 81, 111, 151, 447, 468, 503, 504, 523, 576 | the **ref-id**, which carries no status word at all: `glossary-connection-aware-optimizer-planning` **10** occ (9, 26, 27, 81, 96, 118, 151, 523, 544, 607-the-def) + the concept phrases `deferred sibling` **1** occ (27) and `Leave [Connection-aware` **2** occ (81, 523) | **9 claim sites**: 9, 27, 81, 111, 118, 151, 293, 447, 523 (+ 26 for precision). `:96` and `:544` graded not-drift; `:607` is the def | `deferred sibling` **0**; the status phrase `` `planned for 0.0.9` `` survives at **6** occ (17, 18, 81, 111, 527, 566), every one about `030`'s OWN three entries or the licensed `Current state` observation; the parity-table Status cell no longer says `planned` |
| The **empty-plan** bound | the claim's own word: `empty` **16** occ over 10 lines, of which 7 lines sit next to `plan` (73, 364, 411, 413, 503, 576, 580) | two disjoint phrasings that never use `empty`: `flat walker` / `flat-walker` **7** occ (73, 74, 293, 411, 468, 503, 523, 576) and `connection-unaware` **6** occ (73, 74, 411, 468, 503, 576); third instrument `silent cap` **5** occ (74, 411, 468, 504, 576) | **8 sites**: 73, 74, 411, 468, 503, 504, 523, 576 (+ 293 and 447 for the same vocabulary) | `flat walker`/`flat-walker` **0**; `connection-unaware` **0**; `empty in 0.0.9` **0**; `empty for every connection` **0**; `currently empty` **0**; `plans ()` **0**; `A/B control` **0**. Remaining `empty` occ (79, 364, 457, 508, 516, 584) are all `first: 0` empty-edges or "an empty strictness context" |
| The **handed-forward inventory itself**, treated as a claim | the inventory's own line list from `bld-slice-2` (`:249`-`:251`): 5 sites for the status claim (`:9`, `:27`, `:111`, `:523`, DoD item 8) + 4 for the bound (`:411`, `:73`, `:503`, DoD item 6) = 9 | re-derived from the file with instruments A and B above, then each candidate read | **the inventory was wrong in both directions**: it named DoD item 8, which carries NO status claim (`sed -n '584p'` — it names only the three `030` entries); and it missed 7 real sites (`:74`, `:75`, `:81`, `:118`, `:151`, `:293`, `:468`, `:504`, `:447`) | every real site reconciled or graded; DoD item 8 left untouched |

**Where the instruments mattered, and how each failed.** Row 1: the ref-id sweep is the only instrument that finds `:26`, `:96`, `:118` and `:544`, because those sentences carry the term as a *link* and no status word — a `planned`-keyed sweep is blind to all four. Row 2: the `empty`-keyed sweep misses `:74`, `:468` and `:523`, which make the same bound with `flat walker` / `flat-walker` and no `empty` anywhere; conversely the `flat walker` sweep misses `:413`'s `Forward design input` block, which is *about* the bound and names neither phrase. Only the union is the population. Row 3 is the finding worth carrying: **a handed-forward inventory is a claim, not a measurement** — it under-counted this slice's populations by 7 sites and over-counted by 1, and the over-count is the more dangerous shape because chasing a claim that is not there invites inventing one.

**One post-edit count needed correcting while it was being written, in the direction the standing lesson does not usually run.** A loose `grep -o 'planned for'` returns **7** occurrences post-edit, but one of them (`:415`) is the substring inside `unplanned for that same reason` in the new `Aggregate-ordering coexistence` paragraph — a sentence with no status claim in it. The exact status phrase is `` `planned for 0.0.9` `` (the backtick opens *before* `planned`), which occurs **6** times. So a grep vocabulary can over-count as well as under-count, and a phrase whose delimiter sits outside the words you keyed on is why: keying on `planned for \`0.0.9\`` returns **0** because the backtick is in the wrong place, and keying on `planned for` returns one site too many. The number in the table is the 6.

### The `## Current state` licence, applied explicitly

Slices 1 and 2 established that `## Current state` is licensed as a dated observation of the pre-build repo, that the licence covers **observations only** and never predictions the build falsified, and that a licence claim about a section is not one about each sentence in it. Applied here to the one candidate in this slice's scope, **re-derived rather than inherited**:

- **Line 111, sentence 1** (`docs/GLOSSARY.md` already has the four headings, all `planned for 0.0.9`) — **observation, TRUE, left as written.** Verified read-only: `git show eaaf1385:docs/GLOSSARY.md` into a scratch path outside the repo shows `## Connection-aware optimizer planning` at line 219 with `**Status:** planned for 0.0.9` at line 221. The later flip by `033` does not falsify a sentence about the repo at that date.
- **Line 111, sentence 2** ("Slice 5 flips the first three ... and leaves the connection-aware entry planned for the sibling card") — **not an observation, and reconciled.** It states what the build's own Slice 5 will do. That prediction came true, so this is not the "prediction the build falsified" case Slice 1 named; it is a third case worth naming: **a true prediction whose enduring implication a LATER card falsified.** The sentence's scope content (this card does not own that entry) is kept; the status implication is removed. Deleting it would have lost a real scope boundary; leaving it would have had a current reader check the glossary and conclude the spec is wrong.
- No other `## Current state` bullet is in this slice's scope. `:102` and `:103`/`:104` belong to Slices 4 and 1-2 respectively and were graded there.

### The `## Out of scope` / `## Non-goals` test, applied explicitly

The task asked which test I applied. **The test: does the sentence assert what some artifact's STATE is, or what THIS CARD does not build?** State claims drift when falsified; scope claims do not, because `030`'s scope is fixed history that no later card can change.

- **`## Out of scope` (`:544`, now `:548`) — scope statement, UNCHANGED.** "Connection-aware optimizer planning — the sibling `DONE-033-0.0.9` card; plugs into this card's cooperation point." It asserts no status. Both clauses are true today: the capability is the sibling card's, and it does plug into this cooperation point. Editing it would have been churn.
- **`## Non-goals` (`:125`) — scope statement, kept, with one precision word.** "Teaching the walker to descend `edges { node { ... } }` and plan nested `Prefetch` chains ... is the sibling card" stays a scope claim, but its first clause had become ambiguous in a way that would now mis-assign work: the **root** `edges { node }` unwrap lands at *this card's own seam* (`apply_connection_optimization`'s default extractor), while the walker-side recognition of a **nested** connection is the sibling card's. Added `nested` and named the windowed shape, so the non-goal draws the line where the code draws it.
- The same test kept `:96` ("Connection-aware optimizer planning ships in parallel") unchanged — a statement about cohort sequencing, true then and now — and kept the `### Explicitly do not borrow` bullet (`:172`) unchanged, which is a borrowing-posture scope claim.

### Spec changes made (Worker 1 only)

Line numbers are **post-edit**. Cause for every entry: the Slice 3 audit above, `docs/builder/build-030-connection_field-0_0_9.md` Slice 3. Every "what changed and why" record went to the rationale companion; the spec carries only the corrected contract, in the present tense, with no chronology, no amendment block, and no "as of `033`" hedge.

**S1 — the `Status:` line's Slice-3 summary.** 1 site (`:5`). "bound the connection-aware-planning gap to the sibling card" → "name the nested-connection planning boundary the sibling card owns". Per `worker-1.md` `## Spec status-line re-verification`.

**S2 — the Predecessors tail.** 1 site (`:9`). The glossary-status enumeration and the "leaves the fourth planned" prediction are replaced by a status-free scope statement: this card ships and documents the first three entries, and the fourth's status belongs to `DONE-033-0.0.9`.

**S3 — the optimizer Key-glossary bullet.** 1 site (`:26`). It said the `edges { node }` descent is the sibling card. Now: the cooperation point derives the node type's plan from the `edges { node { ... } }` selections, and **nested** `<field>Connection` window planning is the sibling card. This is the precision half of the whole reconciliation — an unqualified "`edges { node }` descent is `033`" hands away a capability that lives at `030`'s own seam.

**S4 — the `Connection-aware optimizer planning` Key-glossary bullet.** 1 site (`:27`). "the deferred sibling slice that teaches the walker to descend `edges { node { ... } }`" → the sibling `DONE-033-0.0.9` card that teaches the walker to recognize and window-plan **nested** connection selections. The glossary link survives, so `check_spec_glossary` still resolves the term.

**S5 — Slice-3 checklist sub-bullet 1.** 1 site (`:73`). The empty-plan clause is replaced by what the cooperation point derives: the default `selection_extractor` is the `edges { node { ... } }` navigator, so the walker gets the same child-selection list a `DjangoListField` over the node type would, and a root connection plans `select_related` for a to-one, a `Prefetch` for a many-side, and the `only()` projection for the selected scalars — with the two short-circuit conditions named so the sentence is not read as unconditional.

**S6 — Slice-3 checklist sub-bullet 2.** 1 site (`:74`). "Document the alpha constraint honestly ... bounded by the flat walker's connection-unawareness" → "Name the planning boundary this card does NOT cross", with the nested case, its owner, and the statement that the sibling card owns its own fallback shapes. The "no silent cap" obligation and both named documentation homes survive verbatim in substance.

**S7 — Slice-3 checklist sub-bullet 3.** 1 site (`:75`). "guarding the seam the connection-aware card **will close**" — a future-tense prediction the build outlived — becomes what the shipped test actually guards: that a genuinely unplanned relation reached through a connection's `edges { node }` response path still surfaces as an N+1, i.e. the connection response shape does not blind the detector.

**S8 — the Slice-5 checklist glossary bullet.** 1 site (`:81`). "Leave [Connection-aware optimizer planning] `planned for 0.0.9` (ships under `DONE-033`)" → "Do not touch the entry — its status is `DONE-033-0.0.9`'s to set." Same scope boundary, no status claim. Its `## Doc updates` twin is S16; **fixing one and not the other is exactly the partial-claim-fix defect this cycle keeps finding**, so both moved in this change.

**S9 — `## Current state`, sentence 2 only.** 1 site (`:111`). See the licence section above for why sentence 1 stayed and sentence 2 did not.

**S10 — Goal 4's tail.** 1 site (`:118`). "Document the nested-`edges { node }`-planning gap as the sibling card's job" → "Name nested-`<field>Connection` window planning as the sibling card's job." The goal is unchanged; it no longer asserts a live gap, and it uses the vocabulary that distinguishes the nested case from the root one.

**S11 — the reference-package parity checkpoint's Status cell.** 1 site (`:151`). `planned (0.0.9 — DONE-033-0.0.9)` → `sibling card (0.0.9 — DONE-033-0.0.9)`. The cell was self-contradictory: a `DONE-` card id inside a `planned` status. **The `DONE-032-0.0.9` row one line above has the identical defect and was deliberately NOT touched** — see the handoff below for the ownership reasoning.

**S12 — Decision 2's card-boundary bullets.** 2 sites (`:293`, `:296`). The `030` bullet dropped "against the existing flat walker" (a dated description of the walker this card was built against, now false and load-bearing for nothing). The `033` bullet gained what that card actually owns — walker recognition and windowed planning of **nested** `<field>Connection` selections — so the boundary is drawn at the same place the code draws it.

**S13 — Decision 11: `Scope honesty` replaced by `Planning scope`, in two paragraphs.** 1 site replaced, 1 added (`:411`, `:413`). The new text states what the cooperation point derives (node type, not connection type; the default navigator; list-field parity in the child-selection list) and the one deliberate difference from the list-field shape — the node children keep the connection's response path as a runtime prefix, so planned resolver keys read `<Type>.<rel>@<field>.edges.node.<rel>` and strictness accounting matches the path a resolver actually runs at. That clause stays in the spec under `worker-1.md`'s implementation-relevant-rationale carve-out: a reader who does not know it will read a resolver key as a bug. The second paragraph states the nested boundary and, deliberately kept from the old text because the build vindicated it, **why the seam belongs in the field**: richer planning arrives as an optimizer change rather than a connection-field retrofit. The bold lead-in was renamed because its subject changed from an emptiness to a boundary; `grep -rn "Scope honesty"` over every `.md` and `.py` confirms the old label is cited from nowhere outside this cycle's own scratchpads.

**S14 — Decision 11: `Forward design input for 033` becomes `Aggregate-ordering coexistence`.** 1 site (`:415`). The block's verdict is argued in the audit above. It now states the interaction as a live property of the shipped pipeline — the aggregate keeps one row per parent so cursors index distinct nodes and `totalCount` counts distinct parents; a to-one `select_related` adds no multiplication and stays functionally dependent on the grouped parent pk on strict backends; the projection narrows the select list the `GROUP BY` follows rather than widening it — cited to `orders/sets.py::OrderSet._resolve_order_expressions` and pinned to the live test. The `P1-B` finding label was dropped from the spec (it survives in the companion, where a reader looking for the finding belongs) and the pointer to the companion's Decision 11 stays via the existing `[rationale-d11]` reference at the Decision's tail.

**S15 — the Slice-3 Test plan: 2 rows rewritten, 1 added.** 3 rows (`:506`-`:508`). Row 1 asserted the plan is empty; it now states what the test asserts, including the exact `only_fields` tuple and the planned resolver key, because "a plan was published" and "the right plan was built" are different claims and only the second is what the test now makes. Row 2 is new — `test_root_connection_field_queryset_prefetches_node_many_relation` existed at `HEAD` and the plan named neither it nor the contract it pins. Row 3 (the strictness row) now says what its test does: no optimizer installed, an empty strictness context, `types/resolvers.py::_check_n1`, and the explicit note that a *planned* nested connection's fallback shapes belong to `DONE-033-0.0.9` — so the row cannot be read as `030` owning that surface.

**S16 — `## Doc updates`, Slice 5's glossary bullet.** 1 site (`:527`). The "flat-walker cooperation-point alpha-constraint note" instruction becomes the note the glossary actually carries (the field owns its own optimizer seam; nested-connection window planning is the sibling card's), and the "Leave ... `planned for 0.0.9`" tail becomes the same scope statement as S8.

**S17 — DoD item 6.** 1 site (`:580`). The empty-plan clause becomes the derived-plan contract with the resolver-key prefix named; nested window planning is attributed to `DONE-033-0.0.9`; and the strictness clause states what the shipped test pins rather than the seam it used to pin. The B1-B8 no-regression clause and the "no silent cap" clause are unchanged in substance.

**S18 — the implementation-plan estimate row for Slice 3.** 1 site (`:449`). The row's title and its test-summary parenthetical tracked the old claim. The table is explicitly labeled as estimates, so the line delta and `~4` are left alone; the *descriptions* were corrected so the table does not contradict the checklist two hundred lines above it.

**S19 — two new link definitions.** `[orders-sets]: ../../django_strawberry_framework/orders/sets.py` and `[resolvers]: ../../django_strawberry_framework/types/resolvers.py`, both under the existing `<!-- django_strawberry_framework/ -->` group in alphabetical order (`orders-sets` between `optimizer-plans` and `package-init`; `resolvers` after `relay`). Both disk-exists-checked. Both are net-new because the spec previously cited neither module — the aggregate-ordering constraint was stated without naming the symbol that implements it, and the strictness contract without naming the function that raises.

**Not changed, deliberately.** No `## Current state` bullet other than `:111`'s second sentence (the licence applies; sentence 1 re-derived at `eaaf1385`). `## Out of scope` (`:548`) and `:96` and `:172` — scope statements, per the test above. The `DONE-032-0.0.9` parity-table row (`:150`) — handed forward. DoD item 8 (`:584`) — the handed-forward inventory named it and it carries no such claim. The implementation-plan table's line deltas and test counts — labeled estimates. Nothing in Decisions 1, 3-10, 12-14 or the Slice-1/2/4/5 checklist, Test plan, and DoD text.

### Rationale companion appends (Worker 1 only)

The companion is append-only during the build, and every append used its own documented convention. No moved text was rewritten.

- **Decision 11 — 2 new `**Post-ship:**` bullets, placed before the two Slice 2 added** (so the section reads scope-then-shape rather than shape-then-scope):
  - The empty-plan bound: that it was **true when written and correctly reasoned**, describing a real boundary inside the `0.0.9` patch line between two cards that shipped together and existing precisely so the card would not claim an optimization it had not built; the mechanism that closed the root half (commit `a3f84ea9`, the default `selection_extractor`, the same commit inverting the test's assertions) and the sibling card that closed the nested half, with `spec-033`'s own record of the same finding cited; and the **three claims this Decision may no longer make** (`BUILD.md`'s "any claim the decision once made and may no longer make") — that the plan is empty for every connection field, that root scalar/FK planning arrives only with the sibling card, and that `edges { node }` recognition is a single indivisible change owned wholesale elsewhere, since the root unwrap and the nested walker recognition turned out to be separable and were separated. The **prediction the Decision got right** is recorded too, because it is why the design survived the change: putting the seam in the field bought richer planning as an optimizer change, not a retrofit.
  - `P1-B`'s forward design input: why it stopped being forward (the addressee shipped), why it stopped being hypothetical (the plan is non-empty, so Decision 7 steps 3 and 6 compose on every such request), and why it is **answered** rather than open, with the owning symbol and the live pin. The maintainer's split applied literally: the constraint is contract and stays in the spec; that it was once advice to an unshipped card is history and stays in the companion.
- **`## Non-Decision deliberation` — a new `### Post-ship: the empty-plan claim's population was mostly outside the Decision that made it` subsection.** A new subsection rather than an extension of the symbol-citation one, because the two populations are disjoint and that one is closed. It records that the claim lived in eight non-Decision sections plus the Predecessors paragraph and two Key-glossary bullets; that only two sites name a `select_related`-shaped symbol and one carries the whole claim as a single word in a table cell; and the two judgements with their tests stated — the `## Out of scope` / `## Non-goals` scope-vs-state test, and the `## Current state` sentence-level split with the authoring-commit evidence.

### Postcondition proofs

**1. `check_spec_glossary` holds.**

```
$ uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-030-connection_field-0_0_9.md
OK: 50 terms - all have glossary entries and at least one spec link.
EXIT=0
```

The `Connection-aware optimizer planning` term keeps its glossary link at every site that carried one (10 ref-id uses pre-edit, 10 post-edit), which is why the count is unchanged despite four of those sentences being rewritten.

**2. Link scaffold and paths, both files.**

```
$ .venv/bin/python scripts/check_trailing_commas.py --check docs/SPECS/spec-030-connection_field-0_0_9.md docs/SPECS/appx/spec-030-connection_field-0_0_9-rationale.md
EXIT=0

$ .venv/bin/python <scratch>/linkcheck.py START.md          # instrument sanity FIRST, on a known-good file
== START.md
 undefined refs: ['ref-id']        # the convention doc's own literal example -- explainable, so the tool is trustworthy
 ... all other fields empty

$ .venv/bin/python <scratch>/linkcheck.py docs/SPECS/spec-030-connection_field-0_0_9.md docs/SPECS/appx/spec-030-connection_field-0_0_9-rationale.md
== docs/SPECS/spec-030-connection_field-0_0_9.md
 undefined refs: []
 unused defs: ['goal']        # pre-existing before this cycle
 missing paths: []
 def anchors not resolving: []
 dangling in-page anchors: []
 inline cross-file links: []
== docs/SPECS/appx/spec-030-connection_field-0_0_9-rationale.md
 undefined refs: []
 unused defs: []
 missing paths: []
 def anchors not resolving: []
 dangling in-page anchors: []
 inline cross-file links: []
```

Slice 2 recorded that this checker's first run was wrong and had to be fixed before it could be trusted. **So it was validated on a known-good file before being believed here** — `START.md` returns exactly one hit and that hit is the markdown-link-convention section's own literal `[text][ref-id]` example, i.e. a true positive of the pattern and a documentation artifact. A tool with one explainable hit on a file known to be correct is one whose clean result elsewhere means something. Four new cross-file def anchors were added to the companion (`[spec-030-dod]`, `[spec-030-parity]`, `[spec-030-slice-checklist]`, `[spec-033]`) and all four resolve against real headings in the target files.

**3. `.py` surface unchanged — the inverse proof.** The claim is that no executable byte moved, so the proof is a diff empty by construction, not a green suite.

```
$ git status --short -- '*.py'
 M django_strawberry_framework/__init__.py       # all 18 pre-existing or concurrent; see the baseline re-read
 M django_strawberry_framework/exceptions.py
 M django_strawberry_framework/scalars.py
 M scripts/bug_hunt.py
 M tests/base/test_init.py
 M tests/filters/test_base.py
 M tests/filters/test_factories.py
 M tests/filters/test_inputs.py
 M tests/forms/test_converter.py
 M tests/forms/test_inputs.py
 M tests/forms/test_sets.py                      # appeared MID-PASS (concurrent)
 M tests/test_bug_hunt.py
 M tests/test_exceptions.py
 M tests/test_resource_policy.py
 M tests/test_scalars.py
 M tests/test_schema.py
 M tests/test_sets_mixins.py
 M tests/test_views.py
?? tests/mutations/test_operations.py
$ git status --short docs/SPECS/
 M docs/SPECS/spec-030-connection_field-0_0_9.md
?? docs/SPECS/appx/spec-030-connection_field-0_0_9-rationale.md
```

Every dirty `.py` belongs to the concurrent session; none is `connection.py`, `optimizer/extension.py`, `optimizer/plans.py`, `orders/sets.py`, `tests/test_connection.py`, `tests/optimizer/test_extension.py`, or `examples/fakeshop/test_query/test_library_api.py`, which are the files this slice's contract and its citations cover. The only version-controlled paths this pass wrote are the spec, the companion, and this artifact; `docs/builder/worker-memory/worker-1.md` is the fourth write and is gitignored.

**4. Focused tests run (no `--cov*` flag in any form).**

```
$ uv run pytest tests/test_connection.py tests/optimizer/test_extension.py --no-cov -q
8 workers [237 items]
237 passed in 21.18s

$ uv run pytest examples/fakeshop/test_query/test_library_api.py -k "to_many" --no-cov -q
8 workers [4 items]
4 passed in 6.44s
```

Recorded as run-and-passing, per `worker-1.md` step 5. The first scope is a sanity confirmation — nothing executable changed, so a green run could not have failed differently. The **second is evidence**, not sanity: the `Aggregate-ordering coexistence` claim S14 states rests on the live P1-B rows executing the whole pipeline with the optimizer installed (`examples/fakeshop/config/schema.py` builds the schema with `extensions=[lambda: _optimizer]`), so their passing is what licenses the spec sentence. Per `BUILD.md` `### Query-shape tests must pin the load-bearing property`, the non-empty-plan claim itself is pinned on the **assertions** in `test_root_connection_field_queryset_is_planned` (`plan.select_related == ("category",)`, the exact `only_fields` tuple) and on `apply_connection_optimization`'s default `selection_extractor` in the source — never on a wire result, which would look identical either way.

**5. Byte counts (measured, `wc -c` / `wc -l`).**

| File | Before this pass | After | Delta |
|---|---|---|---|
| `docs/SPECS/spec-030-connection_field-0_0_9.md` | 132,612 B / 716 lines | 135,375 B / 722 lines | **+2,763** B / +6 lines |
| `docs/SPECS/appx/spec-030-connection_field-0_0_9-rationale.md` | 74,603 B / 443 lines | 81,517 B / 465 lines | **+6,914** B / +22 lines |

The spec grew modestly because the replacement text is roughly the length of what it replaces — the old `Scope honesty` paragraph was long, and the new `Planning scope` pair is not longer — while the Test plan gained a row for a test that existed and was never named. Most of the growth is in the companion, which is where a replaced claim's whole history belongs. The corpus ratchet in `BUILD.md` governs the six workflow documents, none of which this pass touched.

### Handed forward to Slices 4-5 and the integration pass

Verified at `HEAD` by this pass and **deliberately not fixed**. Line numbers are post-edit.

**The `Connection-aware optimizer planning` status population and the empty-plan population are both CLOSED in the spec.** No later slice inherits any part of either. Slice 2's handoff described 9 sites across the two; the real union was 17, and every one is reconciled or graded with its test recorded. The one site either handoff named that turned out not to carry a claim (DoD item 8) is left untouched.

**To Slice 5 (audit-only under the cycle's scope fence):**

- Carried forward unchanged from Slices 1-2: `docs/GLOSSARY.md` has no `Meta.cursor_field` heading while two entry bodies reference it; `CHANGELOG.md` has no entry for the keyset-cursor feature; the already-sliced-`QuerySet` `GraphQLError` is shipped public behavior with no `CHANGELOG.md` entry and no glossary mention. Record only.
- **New from this pass, and the one Slice-5 item this slice actually clears rather than adds:** the spec's Slice-5 and `## Doc updates` glossary obligations for `030`'s own three entries are satisfied at `HEAD` — `DjangoConnectionField`, `DjangoConnection`, and `Meta.connection` all read `**Status:** shipped (0.0.9)` — and the `DjangoConnectionField` body carries the cooperation-point note in its current (post-`033`) form rather than the flat-walker alpha-constraint form the spec used to ask for. Slice 5 should audit that against S16's rewritten instruction, not against the old one.

**To the integration pass:**

- **The `DONE-032-0.0.9` parity-table row (`:150`) has the identical defect S11 fixed one line below it**: `planned (0.0.9 — DONE-032-0.0.9)` — a `DONE-` card id inside a `planned` status cell. I fixed only the `033` row, deliberately: `032`'s shipped surface is not in any `030` slice's audit scope, and I have not read it, so changing its status word would be asserting a claim I did not verify. But leaving two structurally identical cells disagreeing is not an acceptable end state for the cycle, only an acceptable mid-state (Slice 1's rule). The integration pass should either verify `032`'s status and fix the row, or record why it stands.
- `:557` "**Auto-trigger of `finalize_django_types()`** — deferred to `032`" (Decision 12's Out-of-scope twin), carried from Slices 1 and 2 and still unaudited.
- The unused `[goal]` link definition — pre-existing, harmless, named so a later sweep does not attribute it to this pass.
- **A method note, carried from Slice 2 and now with a second instance.** Slice 2 found `connection.py::_guard_source_not_pre_sliced` reaching the shipped package through a commit with no card and no spec, and suggested sweeping the module's other guards for the same shape. This slice found the *same provenance shape* on a different surface: commit `a3f84ea9` closed a spec-stated `0.0.9` bound with no card and no spec of its own, and no document recorded it until `spec-033`'s Revision 1 mentioned it in passing. Two instances make it a pattern rather than an anecdote, and both sat in seams `030` owns. If the integration pass wants one cross-cutting check, `git log -S` over each Decision-11 / Decision-7 symbol for card-less commits is the shape that finds it.

### Summary

Slice 3's load-bearing contract is satisfied at `HEAD`: the connection field owns its optimizer cooperation point, calls it as step 6 of the pipeline on **both** the offset and the keyset exit of `_finalize_queryset`, resolves the model from the registry rather than `info.return_type`, and publishes an `OptimizationPlan` to `info.context` before `ConnectionExtension` slices — which the schema middleware cannot do for a connection field, because `_optimize` returns a non-queryset result untouched. Both tests the Test plan names exist, the B1-B8 no-regression check exists and pins the delegation direction as well as the outcome, and the strictness guard exists and passes.

**What a connection field's optimizer cooperation delivers today, stated precisely.** A **root** connection derives a full plan, not an empty one: `apply_connection_optimization` defaults its `selection_extractor` to `_connection_node_child_selections`, the `edges { node { ... } }` navigator, so the O2 walker receives the same child-selection list a `DjangoListField` over the node type would — `select_related` for a selected to-one relation, a `Prefetch` for a selected many-side relation, and the `only()` projection for the selected scalars. Evidence pinned on the load-bearing property, not on a wire result: the default argument in `optimizer/extension.py::apply_connection_optimization`, and the assertions in `tests/test_connection.py::test_root_connection_field_queryset_is_planned` (`select_related == ("category",)` plus the exact five-element `only_fields` tuple and the planned resolver key `PlanItemNode.category@items.edges.node.category`) and `::test_root_connection_field_queryset_prefetches_node_many_relation` (`prefetch_to == ["items"]`). **The bounds that genuinely remain** are three and they are all `030`'s own: nothing is planned when no `DjangoOptimizerExtension` is installed for the execution (the helper reads `_active_optimizer` and returns the queryset unoptimized rather than fabricating one), nothing is planned when `target_type` has no registered model, and an empty plan returns the queryset unchanged. The one boundary this card does not cross is the **nested** one — windowed planning of a `<field>Connection` reached under `edges { node { relConnection { ... } } }` is `DONE-033-0.0.9`, with its own fallback shapes named in that spec, and it plugs into this cooperation point rather than retrofitting the field. "The plan is no longer always empty" and "the plan is now always non-empty" are different claims; the spec now makes neither, and states the conditions instead.

**CODE GAP list: empty.** Nineteen reconciliation items landed in the spec — the status line, the Predecessors tail, two Key-glossary bullets, all three Slice-3 checklist sub-bullets, the Slice-5 checklist bullet and its `## Doc updates` twin, one `## Current state` sentence, Goal 4, the parity-table status cell, two Decision-2 boundary bullets, Decision 11's `Scope honesty` replaced by a two-paragraph `Planning scope` and its `Forward design input` block promoted to a live `Aggregate-ordering coexistence` constraint, two `## Edge cases` bullets where there was one, three Test-plan rows, DoD item 6, an estimate-table row, and two new link definitions — each with its "what changed and why" in the rationale companion and none of it in the spec. `check_spec_glossary` holds at `OK: 50 terms`, both link scaffolds validate against an instrument verified on a known-good file first, every in-page anchor and cross-file def anchor resolves, the `.py` surface is byte-unchanged, and both focused scopes pass.

### Spec changes made (Worker 1 only) — deferral reasons for unticked boxes

None deferred. All three boxes in `### Spec slice checklist (verbatim, as audited)` are ticked because the shipped state satisfies them. Box 1 carries an explicit **deliberately-replaced** note on one struck clause rather than a tick for it: the clause's contract was removed on purpose by later work, so it is neither satisfied nor deferred, and recording it as a case is the honest third option. The replacement is discharged as spec reconciliation (S5, S13, S15, S17), not as work owed to a future slice.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[kanban]: ../../KANBAN.md

<!-- docs/ -->
[glossary]: ../GLOSSARY.md
[glossary-djangooptimizerextension]: ../GLOSSARY.md#djangooptimizerextension
[glossary-only-projection]: ../GLOSSARY.md#only-projection
[glossary-strictness-mode]: ../GLOSSARY.md#strictness-mode

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[connection]: ../../django_strawberry_framework/connection.py

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
