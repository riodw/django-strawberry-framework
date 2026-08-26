# Build: Slice 2 — `DjangoConnectionField` factory + synthesized-signature argument injection + composition pipeline + consumer-resolver contract + optimizer cooperation point + sync/async

Spec reference: `docs/SPECS/spec-030-connection_field-0_0_9.md` (as-audited lines 66-71 for the slice checklist; Decisions 5, 6, 7, 10, 11 and the helper-extraction half of Decision 11; Test plan lines 482-490; DoD items 4-5)
Rationale companion: `docs/SPECS/appx/spec-030-connection_field-0_0_9-rationale.md`
Build plan: `docs/builder/build-030-connection_field-0_0_9.md`, checklist Slice 2
Status: final-accepted

**Closure path taken: procedural closure (`BUILD.md` `### Procedural-closure slices`), one combined Plan + Final-verification block, `Status: final-accepted` in this single pass.** The reason, stated explicitly: **all seven of Slice 2's sub-checks are satisfied at `HEAD`** — verified by reading each function body and each named test's assertions against the spec sentence, not by grepping for symbol names — so there is **no CODE GAP**, and the only work the slice owes is spec reconciliation, which is Worker 1's alone. No Worker 2 build and no Worker 3 review were dispatched, and none is owed: this pass ships no `.py` change (proved below by an inverse diff, not asserted).

- **Hot-path declaration: none.** This pass writes two `.md` files and no `.py` file, so no code runs differently and no number can move. The build plan's conditional hot-path clause (a change inside `connection.py::_pipeline_sync` / `::_pipeline_async` / `::_resolve_from_window` / `::_finalize_queryset` or `optimizer/extension.py::apply_connection_optimization`) is not triggered — and this slice's audit read all five of those symbols, so the absence of a change to them is a finding rather than an oversight. Stated rather than left to be read out of a silence.
- **Floor-verification scope: none.** The plan's conditional clause fires only on a `.py` change under `connection.py`, `types/base.py`, `types/definition.py`, or `optimizer/extension.py`. No floor venv was built and none is owed. The shared `.venv` was not mutated.
- **Static inspection helper: skipped, with the reason.** `BUILD.md` `### When to run the helper during build` requires it when the plan **adds logic** to a `.py` file of 150+ source lines or anything under `optimizer/` or `types/`. This plan adds no logic anywhere — the audit found no CODE GAP, so there is nothing for a builder to implement in `connection.py` (2077 lines) or `optimizer/extension.py` and no `docs/shadow` output to cite. Had the audit found a gap in either file, the helper would have been mandatory and both files are squarely inside the trigger.
- **Boundary count: 0.** No guard, cap, rejection path, or validation branch is added, so no failability proof is owed and the `### Slice splitting` question does not arise. The boundaries this slice's contract covers are all shipped and all pinned — five constructor guards, the sidecar-input-over-non-queryset rejection, the `totalCount`-over-non-queryset rejection, the `SyncMisuseError` sync/async boundary, and one guard the contract never named (see the CODE GAP section).
- **Environment.** `uv run` works on this tree; both `uv run` and `.venv/bin/python` were used and are noted per command.
- **No `ruff`.** Both `ruff format` and `ruff check` are no-ops against `.md`, and running them repo-wide would touch a concurrent session's dirty `.py` files. Not run, deliberately.

## Working-tree baseline re-read (`git status --short`, start and end of pass)

The build plan's baseline list is a snapshot and has moved again. Dirty-and-out-of-scope, never edited and never reverted (`AGENTS.md` rule 34):

`AGENTS.md`, `pyproject.toml`, `uv.lock`, `django_strawberry_framework/__init__.py`, `django_strawberry_framework/exceptions.py`, `django_strawberry_framework/scalars.py`, `scripts/bug_hunt.py`, `tests/base/test_init.py`, `tests/test_bug_hunt.py`, `tests/filters/test_base.py`, `tests/filters/test_factories.py`, `tests/filters/test_inputs.py`, `tests/forms/test_converter.py`, `tests/test_exceptions.py`, `tests/test_resource_policy.py`, `tests/test_scalars.py`, `tests/test_schema.py`, `tests/test_sets_mixins.py`, `tests/mutations/test_operations.py` (untracked), `docs/review/**`, `docs/dry/**`, `docs/bug_hunt/**`.

**New since Slice 1's list, and appearing MID-PASS:** `tests/forms/test_inputs.py` (M) and `tests/test_views.py` (M). Both out of scope. `docs/SPECS/spec-030-connection_field-0_0_9.md` and the untracked companion show dirty from this cycle's own prior passes.

---

## Plan (Worker 1)

### Spec status-line re-verification

Read on entry: spec lines 1-11 (title, shipped-in line, `Status:`, owner, predecessors, the rationale-companion pointer). All still describe the build's current state — the card is `DONE-030-0.0.9`, the spec is the final implementation record, the five-slice decomposition holds, the joint-`0.0.9`-cut version boundary holds, and no predecessor doc it names has been deleted. The one false clause in the Predecessors paragraph (the `Connection-aware optimizer planning` glossary entry is `shipped (0.0.9)` at `HEAD`, not left `planned`) is Slice 3 / Slice 5's, already inventoried, and is not a status-line falsification. **No status-line edit was needed or made.**

### DRY analysis

- **Helper inventory checked — not applicable, and why.** The package-wide AST inventory exists to stop a builder writing a duplicate *code* shape. This pass writes no code and adds no helper, constant, validation branch, coercion utility, or test helper, so there is no candidate to inventory against. Recorded rather than skipped so a later pass does not read the absence as an omission. The `.py` surface is byte-unchanged (proof below). The audit did read the package surface it needed directly — `connection.py`, `list_field.py`, `optimizer/extension.py`, `optimizer/plans.py`, `utils/querysets.py`, `utils/connections.py`, `filters/__init__.py`, `orders/__init__.py` — which is what the inventory would have indexed. The audit's own DRY finding is recorded as sub-check 6 below: the middleware and the connection field share ONE plan-application core, so the extraction the spec contracted did not decay into two copies.
- **Existing patterns reused.** The reconciliation reuses the companion's documented append convention (a `**Post-ship:**` bullet under the owning Decision's `### Changes this Decision underwent`), and for findings belonging to no single Decision, the `## Non-Decision deliberation` subsection Slice 1 created — **extended rather than duplicated**, because the population it names is the same population this slice finishes. Writing a second post-ship-citations subsection would have split one finding across two homes.
- **New helpers justified: none.**
- **Duplication risk avoided.** The one real duplication risk in a spec/rationale split is stating the same correction in both files, which then drift. Prevented by rule: the spec carries only the corrected contract, present tense, with no trace of what it used to say; the companion carries only the change record. Verified mechanically after the edits — `Relay-foundation`, `apply_connection_plan`, and `_apply_get_queryset` outside `## Current state` are each **0** occurrences in the spec and non-zero only in the companion (counts below).

### Slice 2's contract, audited against `HEAD`

Method note, because it decides what this audit is worth: **a grep proves the symbol, not the claim.** Every sub-check below was checked by reading the function body against the spec sentence, and every named test by reading its assertions. The audit's two most productive reads are called out where they land: `_finalize_queryset` (which turned out to be wider than Decision 7 step 5 describes) and `apply_connection_optimization` (whose call shape the spec describes in two mutually inconsistent ways).

**Sub-check 1 — the factory.** `connection.py::DjangoConnectionField` has exactly the contracted signature: `(target_type, *, resolver=None, description=None, deprecation_reason=None, directives=())`, PascalCase with the `noqa: N802`, and **no** `filters=` / `order=` / `total_count=` kwarg. It runs the guards through `list_field.py::_validate_relay_djangotype_target`, which delegates the four base checks to `_validate_djangotype_target` and then applies the Relay-Node fifth, and returns `relay.connection(_connection_type_for(target_type), resolver=_build_connection_resolver(target_type, resolver), description=…, deprecation_reason=…, directives=…)`. SATISFIED.

**Are the four guards still in the contracted order, and does the Relay guard still share the canonical predicate?** Yes to both, read rather than grepped. `_validate_djangotype_target` runs `inspect.isclass` → `issubclass(DjangoType)` → `definition is None or definition.origin is not target_type` → `resolver is not None and not callable(resolver)`, in that order, each raising `ConfigurationError` with the caller's `field` name interpolated; its docstring states the order is load-bearing and that the third check is `definition.origin is target_type` rather than `hasattr`, which is the strict own-class invariant the spec names. The Relay fifth calls `_is_relay_shaped(target_type, definition.interfaces)` — the same `types/base.py` predicate the `Meta.connection` gate uses, not a local re-derivation — and the connection field supplies its own `relay_error_message`. So the sharing the spec contracted survived the guard's promotion into a helper that `DjangoNodeField` / `DjangoNodesField` also call. **No finding.**

**Sub-check 2 — the synthesized signature.** `connection.py::_synthesized_signature` builds `[root, info]` plus `filter` when `definition.filterset_class is not None` and `order_by` when `definition.orderset_class is not None`, with the annotations `filter_input_type(FS) | None` and `list[order_input_type(OS)] | None`, a `return_annotation` of `Iterable[target_type]`, and a matching `__annotations__` dict; `_build_connection_resolver` assigns both onto `_resolve`. `root` / `info` are Strawberry reserved names, so only the sidecar params become GraphQL arguments. **The `search:` argument is absent** — verified rather than assumed: the only occurrence of `search` in `connection.py` is the docstring line stating it is not generated, and `types/base.py::DEFERRED_META_KEYS` still contains `"search_fields"`, so the seam is reserved and unbuilt exactly as the spec says. The orphan-ledger registration is real and is a side effect of building the annotations: `filter_input_type` / `order_input_type` write `_helper_referenced_filtersets` / `_helper_referenced_ordersets` (both sets exist in `filters/__init__.py` / `orders/__init__.py` with `register_subsystem_clear` teardown), and `tests/test_connection.py::test_connection_field_registers_sidecars_against_orphan_ledgers` discards both entries and then asserts constructing the field re-adds them. SATISFIED.

**Sub-check 3 — the composition pipeline.** `_pipeline_sync` runs: `reject_awaitable_sync_source` → `_prepare_pipeline_source` (Manager coercion via `normalize_query_source`, then either the non-queryset sidecar guard and an early return, or the pre-sliced guard) → `apply_type_visibility_sync` → `filterset_class.apply_sync` when `filter` is supplied → `orderset_class.apply_sync` when `order_by` is supplied → `_finalize_queryset`. `_pipeline_async` is the same sequence with `reject_residual_async_source` and the awaited variants. `_finalize_queryset` does the deterministic total order and then `apply_connection_optimization`, in that order. So the contracted order — visibility → filter → order → total-order → plan → (return for `ConnectionExtension` to slice) — holds end to end on both paths. SATISFIED; **DRIFT in three places on what step 5 does and one on step 1's symbol** — see S3, S5, S6.

**Is the ordering step still the terminal-pk-tiebreaker rule the spec describes?** Substantively yes, and wider in two ways plus relocated. `_finalize_queryset` reads `explicit = tuple(qs.query.order_by)`, falls back to `tuple(target_model._meta.ordering)` when that is empty — the exact `Meta.ordering`-would-be-dropped resolution the spec calls for — and calls `optimizer/plans.py::deterministic_order(effective, target_model)`, which returns `effective` unchanged when `ends_in_unique_column(effective, model)` and otherwise appends `model._meta.pk.attname`. Reordering happens only when the tuple actually changed. Two widenings the spec does not state: `ends_in_unique_column` treats a **nullable** unique column as non-unique (SQL `UNIQUE` permits multiple NULLs, so terminal ties among NULLs are nondeterministic) and likewise a relation path, an annotation alias, and any non-`F` expression; and a keyset-mode type with an empty `query.order_by` orders by its declared `Meta.cursor_field` instead, which beats `Meta.ordering` because the cursors do not encode `Meta.ordering`'s columns. The decision also no longer lives in `connection.py` — it is hoisted to `optimizer/plans.py` so the plan-time window order and this resolve-time order cannot disagree, with `connection.py` keeping `_ends_in_unique_column` as a deliberate re-export.

**Sub-check 4 — the consumer `resolver=` contract.** All four contracted cases plus the escalated fifth are shipped and pinned. `Manager` → `normalize_query_source` coerces (`test_consumer_resolver_manager_coerced`); `QuerySet` → the full pipeline (`test_consumer_resolver_queryset_full_pipeline`, which asserts the order actually applied); non-queryset iterable with no sidecar input → paginates (`test_consumer_resolver_iterable_without_sidecar_input_paginates`); non-queryset iterable with sidecar input → `_guard_sidecar_input_against_non_queryset` raises `GraphQLError` (`test_consumer_resolver_iterable_with_sidecar_input_raises`); and `totalCount` selected over a non-queryset → `_guard_total_count_countable` raises, with `test_consumer_resolver_iterable_with_total_count_selected_raises` asserting BOTH that the package message appears and that the engine's `Cannot return null for non-nullable field` does not — which is the whole point of the M1 escalation, and an assertion that would be vacuous without the negative half. The async mirror (`test_async_consumer_resolver_iterable_with_total_count_selected_raises`) and the await-before-raise discipline (`test_attach_count_async_awaits_before_guard_raises`) are both pinned too. SATISFIED; **the shipped contract has a FOURTH rejection the spec never contracted** — see S4.

**Sub-check 5 — sync + async, and Decision 10's dispatch freeze.** `_build_connection_resolver` branches ONCE, on `is_async_callable(resolver)`: the async-consumer branch is an `async def` awaiting the resolver then `_pipeline_async`; everything else — the default field, a plain `def` resolver, and a declared async-generator resolver (`is_async_callable` is deliberately False for those) — shares one sync `def` running `_pipeline_sync`. That IS the build-time freeze the spec describes, and it is not a per-call `in_async_context()` dispatch. **Decision 10's stated consequence is exactly what the code does, and it is pinned in both directions**, which was worth confirming rather than assuming: `test_sync_context_async_get_queryset_raises_sync_misuse` covers the `execute_sync` case, and `test_async_execution_default_connection_async_get_queryset_raises_sync_misuse` covers the one a reader would expect to differ — under `await schema.execute` a default connection field STILL refuses an async `get_queryset`, because the branch was chosen at construction; that test also asserts `result.data is None`, so an async pipeline serving the seeded row would fail it. The sync branch additionally carries two runtime guards the freeze makes necessary (an awaitable return rejected before normalization; an async-only iterable in a sync context raising `SyncMisuseError` rather than reaching Strawberry's sync slicer as a blank `AssertionError`), each with its own test. SATISFIED; the guards and the async-execution consequence are absent from the spec — see S7.

**Sub-check 6 — the optimizer cooperation point.** The extraction is real, and the middleware genuinely shares it rather than carrying a copy: `DjangoOptimizerExtension._optimize` normalizes the source, short-circuits an already-evaluated queryset, resolves `(origin, model)` from the return type, and then `return self.apply_to(resolved.origin, resolved.model, result, info)`; `apply_connection_optimization(target_type, queryset, info, *, selection_extractor=…)` resolves the model from `registry.model_for_type(target_type)` and calls `optimizer.apply_to(target_type, target_model, queryset, raw_info, selection_extractor=…)`. So `apply_to` is the one plan-build-and-apply implementation, `_optimize` adds only the return-type resolution the connection field does not need, and **nothing is inferred from `info.return_type` on the connection path** — the substantive half of the contract. SATISFIED as to the contract; **DRIFT as to the call shape the spec describes** — the spec says the helper "accepts `target_type` / `target_model` directly" in three places, which is true of `apply_to` and not of `apply_connection_optimization`, whose own signature the spec's Decision-11 parenthetical already gets right. Two shipped behaviors are unstated: the `_active_optimizer` `ContextVar` short-circuit (no installed extension → return unoptimized, never fabricate one) and the `selection_extractor` parameter. See S8.

**Sub-check 7 — package coverage.** Every contract the sub-check names has a test, and the `tests/optimizer/` no-regression check exists as `tests/optimizer/test_extension.py::test_optimizer_helper_extraction_no_regression`. SATISFIED; **the Test plan names a test that does not exist and omits several that do** — see S9.

### CODE GAP list

**Empty.** No sub-check of Slice 2 is unimplemented, silently narrowed, or dropped. Nothing is dispatched to Worker 2, and nothing owes a failability proof.

The divergences run in one direction, the same one Slice 1 recorded: the code is wider or more precise than the `0.0.9` text — a fourth resolver-contract rejection the spec never contracted, two narrowings of the unique-terminal rule, a keyset ordering branch, two sync-branch runtime guards, and two unstated properties of the optimizer helper. One divergence is a plain error in the spec rather than a widening: `apply_connection_plan`, a symbol that never existed.

### Spec slice checklist (verbatim, as audited)

Quoted **as the spec stated them at the start of this pass**, before the reconciliation below — deliberately, so the boxes audit the shipped code against the contract as written when the card shipped, rather than against text this same pass rewrote to match the code. Boxes are ticked because the **shipped code satisfies the contract at `HEAD`** (this cycle's inversion of the usual tick discipline). Each box's reconciliation, where there was one, is named in `### Spec changes made (Worker 1 only)`.

- [x] `DjangoConnectionField(target_type, *, resolver=None, description=None, deprecation_reason=None, directives=())` PascalCase factory (Meta-only derivation — no `filters=` / `order=` / `total_count=` kwargs, per [Decision 5](#decision-5--factory-function-mechanism-meta-only-derivation)) running the four [`DjangoListField`][glossary-djangolistfield]-style guards (`isclass` → `issubclass(DjangoType)` → own-class `definition.origin is target_type` → callable resolver) plus a Relay-Node-shaped guard that reuses the canonical `_is_relay_shaped(target_type, definition.interfaces)` predicate — accepting both the declared `Meta.interfaces` tuple and direct `relay.Node` inheritance (`class Foo(DjangoType, relay.Node)`), the same single definition the `Meta.connection` gate uses (per [Decision 5](#decision-5--factory-function-mechanism-meta-only-derivation)). A non-Relay target raises [`ConfigurationError`][glossary-configurationerror]. Returns `relay.connection(_connection_type_for(target_type), resolver=<synthesized>, description=…, …)`.
- [x] Build the field's resolver with a **synthesized `__signature__`** (and matching `__annotations__`) carrying `filter: filter_input_type(FS) | None = None` when the type declares [`Meta.filterset_class`][glossary-metafilterset_class] and `order_by: list[order_input_type(OS)] | None = None` when it declares [`Meta.orderset_class`][glossary-metaorderset_class], so Strawberry's native resolver-argument derivation emits the `filter:` / `orderBy:` arguments (the same shape the hand-written filter/order resolvers use); `ConnectionExtension` forwards these non-pagination kwargs to the resolver. Register the referenced FilterSet/OrderSet against the existing `_helper_referenced_filtersets` / `_helper_referenced_ordersets` ledgers so [`finalize_django_types`][glossary-finalize_django_types] orphan validation stays honest. The `search:` argument is NOT generated (search is `0.1.2`). (Fallback mechanism if signature-derivation proves insufficient with `relay.connection`: a custom `FieldExtension.apply(...)` appending `StrawberryArgument`s — see [Decision 6](#decision-6--sidecar-derived-arguments-via-a-synthesized-resolver-signature) and [Risks and open questions](#risks-and-open-questions).)
- [x] The resolver runs the composition pipeline: build the base queryset (default `initial_queryset(target_type)` or the consumer `resolver=` return with the [Decision 7](#decision-7--composition-pipeline-visibilityfilterorderdefault-orderoptimizer) `Manager` / `QuerySet` / iterable contract) → `target_type.get_queryset(qs, info)` (visibility) → `FilterSet.apply_*` (if `filter` given) → `OrderSet.apply_*` (if `order_by` given) → **deterministic total ordering** (append the pk as a terminal tiebreaker — resolving the effective ordering from `qs.query.order_by` or `model._meta.ordering` — so the cursors index a unique total order in ALL cases, unless the ordering already ends in a unique column; a supplied `orderBy` / model `Meta.ordering` is preserved with the pk appended) → **apply the extracted optimizer plan helper** (target_type / target_model passed explicitly) → return the queryset. `ConnectionExtension` then slices it. Sync and async paths mirror [`DjangoListField`][glossary-djangolistfield], reusing `apply_type_visibility_sync` / `apply_type_visibility_async` and `apply_sync` / `apply_async`; a sync context meeting an async `get_queryset` raises [`SyncMisuseError`][glossary-syncmisuseerror].
- [x] Extract the plan-application logic from [`DjangoOptimizerExtension._optimize`][optimizer-extension] into a reusable internal helper that accepts `target_type` / `target_model` directly (not inferred from `info.return_type`); call it from the connection resolver before slicing (per [Decision 11](#decision-11--the-connection-field-owns-its-optimizer-cooperation-point)). The existing middleware path stays behavior-identical for non-connection fields.
- [x] Package coverage: [`tests/test_connection.py`][test-connection] extends — constructor guards; argument presence/absence by sidecar declaration; the four consumer-resolver cases (`Manager` coercion, `QuerySet` pipeline, iterable-without-sidecar-input, iterable-with-sidecar-input error); deterministic total ordering (unordered → pk order; supplied non-unique `orderBy` → `orderBy, pk`; `Meta.ordering` over a non-unique column preserved + pk appended, NOT clobbered to pk-only; an already-unique terminal left alone — [`optimizer/plans.py::ends_in_unique_column`][optimizer-plans], re-exported into [`connection.py`][connection] as `_ends_in_unique_column`); composition order (visibility before filter before order before total-order before plan before slice); sync + async dispatch; `SyncMisuseError` on async-`get_queryset`-in-sync.

Tick 2 carries a caveat recorded rather than hidden: the contract landed, and the parenthetical fallback it names was never needed — a tick means the obligation was discharged and is still discharged, not that every clause of the sentence describing it was still current. Tick 3's ordering clause and tick 4's helper clause carry the same caveat, both reconciled below.

### Implementation steps

None. No `.py` step exists to plan: the audit closed with an empty CODE GAP list, so this artifact's work is the reconciliation recorded under `### Spec changes made (Worker 1 only)`.

### Test additions / updates

None. No executable surface changed, and every assertion Slice 2's contract needs already exists (sub-check 7 above). No temp test was written; none would have anything to demonstrate. The one shortfall the audit found is in the spec's *description* of the tests, not in the tests — fixed as S9.

### Implementation discretion items

None. Every judgement call is decided and recorded below, including the three that could have gone either way: whether to rename Decision 10's heading, whether the already-sliced guard belongs to `030`'s contract at all, and whether to extend Slice 1's post-ship subsection or open a second one.

---

## Final verification (Worker 1)

### Populations swept, instruments used, and counts

`BUILD.md` `## Claims are proven mechanically`: every number below is re-derivable by running the named token against the named file, and each population was confirmed with a **second instrument of disjoint vocabulary**, because a sweep keyed on one known instance's wording finds a fraction of its population. Counts are **occurrences** (`grep -o … | wc -l`), not matching lines, so a claim wrapped across two lines cannot hide.

| Population | Instrument A (pre-edit) | Instrument B, disjoint (pre-edit) | Union of sites | Post-edit |
|---|---|---|---|---|
| The relocated visibility / initial-queryset helpers | the old private names: `_apply_get_queryset_sync` **7** occ + `_apply_get_queryset_async` **6** occ (13 over 6 lines: 103, 104, 366, 393, 395, 563) + `_initial_queryset` **3** occ (104, 358, 453) | the CONCEPT vocabulary, which carries no symbol: `Relay-foundation` **3** occ (33, 391, 460) + the new names `apply_type_visibility` **2** occ (69, Slice 1's fix) + the module path `utils/querysets` **0** occ — the spec had NO reference to the helpers' current home at all | **9 distinct lines**; 2 (103, 104) are licensed `## Current state` observations, 7 are contract statements | old names **2** occ, both in `## Current state` (103, 104); `Relay-foundation` **0**; `apply_type_visibility` **11**; `utils/querysets` **8** |
| The `_ends_in_unique_column` citation | `_ends_in_unique_column` **2** occ (71 — Slice 1's fix, 362) | the canonical name `ends_in_unique_column` **3** occ; the sibling decision symbol `deterministic_order` **0** occ — the tuple half of the rule was uncited anywhere | **2 sites**, 1 already fixed | **4** occ over 3 lines (71, 364, and 2 inside test names at 495), every one a deliberate alias or test-name mention |
| The optimizer-helper call shape | `target_model` in the spec: 4 occ (69, 70, 405, 563) | reading the two bodies: `apply_connection_optimization` takes `(target_type, queryset, info, *, selection_extractor)`; `apply_to` takes `(target_type, target_model, queryset, info, *, selection_extractor)` | **3 sites in my scope** (69, 70, 563) + `:405`, which is Slice 3's | all 3 name both symbols; `:405` untouched |
| A symbol spelling that never existed | invisible to instrument A (not an old name) | invisible to a backticked-identifier sweep too (it sits inside a ```` ```text ```` fence, so it carries no backticks) — found by READING the section against the source: `apply_connection_plan` **1** occ (258), **0** occ anywhere in `django_strawberry_framework/`, `tests/`, `examples/` | **1 site** | `apply_connection_plan` **0** occ in the spec |
| A shipped guard absent from the contract | invisible to every spec-side instrument: the spec never names it | reading the shipped guard list in `connection.py` against Decision 7's contracted list — `_guard_source_not_pre_sliced` has **2** call sites (`_prepare_pipeline_source`, and the keyset slicer) and **0** occurrences in any spec or standing doc | **4 spec sites owed a sentence** (the API contract list, Error shapes, Decision 7, Edge cases) | stated in all 4 |

**The instruments mattered most in rows 1, 4 and 5, and each failed differently.** Row 1: the Decision-10 *heading* made the stale claim with no symbol in it, so the symbol sweep could not see it — and neither could a line count, since `_apply_get_queryset_sync` alone is 7 occurrences over 6 lines. Row 4: two independent instruments were both structurally blind, one because the token is not an old name and one because a fenced block has no backticks; only reading found it. Row 5: no spec-side instrument can find a guard the spec never mentions — the only instrument is the shipped code's own guard list, read against the contracted one. That is the "nothing was skipped" question inverted, and it is the one direction a checklist audit cannot cover.

### The `## Current state` licence, applied explicitly

Slice 1 established that `## Current state` is licensed as a dated observation of the pre-build repo, so a bullet naming an old symbol is not drift — while the licence covers **observations only**, never predictions the build falsified, and never a spelling that never existed. Applied here to three candidates, and **re-derived rather than inherited**:

- **Line 104 (`types/relay.py` ships `_apply_get_queryset_sync` / `_apply_get_queryset_async` / `_initial_queryset`) — observation, TRUE, left as written.** Slice 1 verified this at the spec's authoring commit `eaaf1385`.
- **Line 103 (`list_field.py` branches on `in_async_context()` to dispatch `_apply_get_queryset_sync` vs `_apply_get_queryset_async`, with `_post_process_consumer_sync` / `_async`) — observation, TRUE, left as written, and verified independently this pass rather than by analogy.** `git show eaaf1385:django_strawberry_framework/list_field.py` shows the import of all three symbols from `.types.relay`, the `in_async_context()` branch, and both `_post_process_consumer_*` definitions. Slice 1 graded this bullet by the same reasoning as 104 without reading it; the grade was right, but the evidence was for a different file. **A licence claim about a section is not a licence claim about each sentence in it.**
- **Line 258 (`apply_connection_plan`) — NOT covered, in either direction, and fixed.** It is not in `## Current state`; it is in `## User-facing API`, which is contract. And a spelling that never existed in the package describes no repo at any date, so even a `Current state` home would not have licensed it.
- No bullet in this slice's scope asserts what the build *will* do.

### Spec changes made (Worker 1 only)

Line numbers are **post-edit**. Cause for every entry: the Slice 2 audit above, `docs/builder/build-030-connection_field-0_0_9.md` Slice 2. Every "what changed and why" record went to the rationale companion; the spec carries only the corrected contract, in the present tense, with no chronology, no amendment block, and no "as of `045`" hedge.

**S1 — the never-taken `FieldExtension` fallback left the spec.** 1 site: the Slice-2 checklist sub-bullet 2 (`:68`). Signature derivation worked, so a shipped contract may not read as a live contingency; the parenthetical naming the fallback mechanism and pointing at `## Risks and open questions` was deleted rather than reworded (the fallback survives in the companion's rejected-alternatives list, where a reader looking for it belongs). Two mechanism facts went in its place, both load-bearing under `worker-1.md`'s implementation-relevant-rationale carve-out: calling `filter_input_type` / `order_input_type` to build the annotations IS the ledger registration, so a separate `.add(...)` would double-register.

**S2 — the pipeline sub-bullet's base-queryset symbol, ordering clause, and helper clause.** 1 site (`:69`). `initial_queryset(target_type)` now carries the `[querysets]` link, the `QuerySet` half of the resolver contract reads `Manager` / `QuerySet` / **unsliced** / iterable, "unique column" became "unique **non-nullable** column", and the optimizer parenthetical "(target_type / target_model passed explicitly)" was dropped in favor of naming the symbol in the following sub-bullet.

**S3 — the helper-extraction sub-bullet names the core and the entry point.** 1 site (`:70`). It now states that the shared core is `DjangoOptimizerExtension.apply_to`, taking `target_type` / `target_model` directly; that `_optimize` resolves the return type and delegates to it, which is what makes the middleware path behavior-identical; and that the connection field reaches it through `optimizer/extension.py::apply_connection_optimization`. The old sentence attributed the core's signature to the connection field's entry point, which is true of neither symbol on its own.

**S4 — the fourth consumer-resolver rejection is now contracted.** 4 sites: the User-facing-API contract list (`:268`), `### Error shapes` (`:278`), Decision 7's consumer-resolver paragraph (`:368`), and `## Edge cases and constraints` (`:466`). `connection.py::_guard_source_not_pre_sliced` rejects an already-sliced `QuerySet` return with a `GraphQLError`, regardless of sidecar input, because the field reorders and re-slices on every request and Django permits neither on a sliced query. **This is the reconciliation item I most nearly missed**, and the one whose provenance needed establishing rather than assuming: it is not a later card's surface. `git log -S` puts it in a standalone bug-fix commit with no card and no spec (`11da7de8`, 2026-06-19, "Convert pre-sliced connection … to clear GraphQL errors"), fixing a defect in exactly the seam Decision 7 owns — the pipeline's `order_by` was leaking Django's raw `TypeError: Cannot reorder a query once a slice has been taken` at the GraphQL boundary. No other spec mentions it (`grep` over every `.md`: 0 hits outside this cycle's own scratch). So `030`'s Decision 7 owns it, and a shipped guard absent from its owning contract is a spec gap.

**S5 — Decision 7 steps 1, 5 and 6.** 3 sites (`:360`, `:364`, `:365`). Step 1 cites `utils/querysets.py::initial_queryset` and folds in why it matters (an unordered default is the reason step 5 exists). Step 5 now names both halves of the rule in `optimizer/plans.py` — `deterministic_order` for the tuple, `ends_in_unique_column` for the skip — with the reason they are hoisted (the plan-time window order and this resolve-time order can never disagree), states that unique means unique **and non-nullable** and that a relation path / annotation alias / non-`F` expression counts as non-unique, and adds the keyset-mode branch. Step 6 names `apply_connection_optimization` and drops the loose "using `target_type` / `target_model`".

**S6 — Decision 7's consumer-resolver paragraph, split in two.** 2 sites (`:368`, `:370`). The contract paragraph gained the already-sliced rejection (S4) and now says what the three rejections have in common — the Meta-driven behavior cannot apply to that source, so the field says so rather than leaking a Django internal, ignoring an argument, or returning `null` into `Int!`. The sync/async sentence became its own paragraph and states the guarantee rather than only the call: `apply_type_visibility_sync` / `apply_type_visibility_async` are a **sealed-execution boundary**, rebuilding the source and the hook's return into a fresh framework-owned `QuerySet` from validated query state and rejecting every non-sealable shape, so step 2's scope is an upper bound the later steps can only narrow — for the `totalCount` count as well as the edges. That is the item the task flagged as possibly understated, and it was: the Decision described a call and the code delivers an invariant. Pinned on this surface by the four `test_connection_hostile_hook_*` / `test_connection_*_sealed` / `test_connection_resolver_manager_degrading_to_list_fails_closed` families.

**S7 — Decision 10, heading and body.** The heading changed — `Sync + async resolver paths reuse the Relay-foundation helpers` → `Sync + async resolver paths reuse the shared visibility helpers` (`:395`) — because the helpers left `types/relay.py` for `utils/querysets.py`, where they are the shared boundary four recomposing read surfaces use, so "Relay-foundation" had become provenance rather than description. All 7 sites naming the old slug or heading text were repointed in the same change: the spec's 2 in-page anchors (`:467`, `:539`) and the `[rationale-d10]` def (`:659`), and the companion's heading, back-pointer, and `[spec-030-d10]` def. A tree-wide sweep confirmed the old slug is cited from nowhere outside these two files. The body (`:397`) cites the new names and the sealed boundary; the Consequence paragraph (`:399`) adds that the refusal holds under `await schema.execute` too (because the branch cannot be re-decided per call) and records the two runtime guards the freeze makes necessary plus why a declared async-generator resolver deliberately takes the sync branch. The same stale vocabulary was fixed in the two other places it appeared — the `SyncMisuseError` key-glossary bullet (`:33`) and the async-`get_queryset` edge case (`:467`); fixing 2 of 3 would have been exactly the partial-claim-fix defect this cycle keeps finding.

**S8 — Decision 11's `Fix:` paragraph.** 2 sites (`:407`, plus a new paragraph at `:409`). The Fix now names both symbols and which sentence is true of each, keeps the substantive contract explicit (the model is never inferred from `info.return_type`), and says what `_optimize` adds that the connection field does not need. The new paragraph records two shipped properties the Decision never stated, both of which make "the field self-optimizes" conditional rather than absolute: the helper is opt-in on the extension — it reads `_active_optimizer` and returns the queryset unoptimized when no extension is installed, rather than fabricating a throwaway one — and the node-selection navigator is a parameter, not a hardcoded `edges { node }` walk. **Decision 11's `Scope honesty` paragraph and the empty-plan bound were deliberately NOT touched** — Slice 3's, per the handed-forward partition.

**S9 — the Slice-2 Test plan named a test that does not exist and omitted several that do.** 6 rows rewritten (`:489`, `:494`-`:498`). `test_connection_resolver_sync_dispatch` has no such test at `HEAD` (0 occurrences in `tests/`); the sync path is driven by every `execute_sync` row and its misuse boundaries are pinned by four named rows, which the plan now says instead of naming a test that was never written. The four constructor-guard rows were abbreviated to names that do not match reality (`..._subclass` / `..._own_class_definition` / `..._relay_node`) and omitted the callable-resolver guard entirely; all five now appear in full, plus the direct-`relay.Node`-inheritance acceptance row. Added: the pre-sliced row, the three `test_finalize_queryset_*` rows and two `test_ends_in_unique_column_*` rows (which is where the already-unique-terminal case is actually pinned), and four async-pipeline rows. And the composition-order row's claim was corrected to what its test asserts: `test_connection_resolver_composition_order` pins visibility → filter → order and the pre-slice count, not "before default-order before plan before slice" — those two steps are pinned where they are decided, which the row now names. Every test name in the Slice-2 Test plan was confirmed present by reading its body.

**S10 — DoD item 5.** 1 site (`:572`). New helper names with the `[querysets]` link, the already-sliced rejection added to the consumer-resolver summary, and the optimizer clause restated as the `apply_to` core reached through `apply_connection_optimization`, with `_optimize` delegating to the same core.

**S11 — `apply_connection_plan` → `apply_connection_optimization`.** 1 site (`:258`), in the `### Composing with get_queryset, filter, and order` fenced sketch. A symbol spelling that never existed anywhere in the package.

**S12 — one new link definition.** `[querysets]: ../../django_strawberry_framework/utils/querysets.py` (`:694`), under the existing `<!-- django_strawberry_framework/ -->` group in alphabetical order between `[package-init]` and `[relay]`. Disk-exists-checked. It is net-new because the spec previously had **zero** references to the helpers' current home — a gap only the disjoint instrument could see. `[relay]` stays used (by `## Current state` line 104), so nothing was orphaned.

**Not changed, deliberately.** No status line (nothing the build falsified). No `## Current state` bullet (the licence applies — see above, with line 103 re-derived). Nothing in Decision 11's `Scope honesty` paragraph, the Slice-3 checklist, the Slice-3 Test plan, or DoD items 6 and 8 — Slice 3's. Nothing in Decisions 1-4, 8, 9, 12-14 or the Slice-1/4/5 checklist, Test plan, and DoD text.

### Rationale companion appends (Worker 1 only)

The companion is append-only during the build, and every append used its own documented convention — a `**Post-ship:**` bullet under the owning Decision's `### Changes this Decision underwent`. No moved text was rewritten.

- **Decision 6** — 1 bullet: the fallback was never taken, why a shipped contract may not carry it as a contingency, and the two mechanism facts that replaced it.
- **Decision 7** — 4 bullets: the three relocated symbols and, at length, what the sealed boundary changed about what "reusing" GUARANTEES (the Decision understated its own contract); the fourth rejection with its no-card provenance and why a guard absent from its owning contract is the skipped-work question inverted; the ordering rule's NULL clause and keyset branch as narrowings rather than reversals; and step 6 naming its symbol.
- **Decision 10** — 2 bullets: the dispatch freeze verified in both directions, with the async-execution consequence named as the half worth testing rather than assuming; and the heading rename with the relocation that forced it, plus why the two sync-branch guards belong to this Decision's contract rather than being incidental hardening.
- **Decision 11** — 2 bullets: the core-plus-entry-point split, including that the Decision's own parenthetical example signature was already right so the imprecision was in the prose — a shape a symbol grep cannot detect; and the two unstated behaviors of the cooperation point.
- **`## Non-Decision deliberation`** — Slice 1's `### Post-ship: symbol citations the Relay-foundation relocations invalidated` subsection was **extended, not duplicated**: its opener now covers the two symbol-free sites, and two new paragraphs record the line-103 re-derivation at `eaaf1385` (with the general rule it produced) and the two sites that were invisible to the symbol sweep — the Decision-10 heading and `apply_connection_plan`, with why each instrument was structurally blind to it.

### Postcondition proofs

**1. `check_spec_glossary` holds.**

```
$ uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-030-connection_field-0_0_9.md
OK: 50 terms - all have glossary entries and at least one spec link.
EXIT=0
```

**2. Link scaffold and paths, both files.**

```
$ .venv/bin/python scripts/check_trailing_commas.py --check docs/SPECS/spec-030-connection_field-0_0_9.md docs/SPECS/appx/spec-030-connection_field-0_0_9-rationale.md
EXIT=0

$ .venv/bin/python   # undefined refs / unused defs / def paths not on disk / def anchors that do not resolve / dangling in-page anchors / inline cross-file links
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

Two notes on this check, because it caught real defects rather than confirming a hope. First, the Decision-10 rename is why it is load-bearing: the companion's `## Decision 10 — …` and the spec's `### Decision 10 — …` slug IDENTICALLY, so `[rationale-d10]` and `[spec-030-d10]` had to move together. Second, **the checker's own first run was wrong and had to be fixed before it could be trusted** — its slug function collapsed runs of whitespace to one hyphen, so every em-dash heading looked dangling. A checker that reports 26 false positives is indistinguishable from one reporting 26 real ones until you read its code; the corrected run above is the one that counts. Its second real catch: two in-page anchors I wrote in the *companion* pointing at *spec* headings, which cannot resolve from that file. Both became reference-style cross-file links with new defs (`[spec-030-edge-cases]`, `[spec-030-error-shapes]`).

**3. `.py` surface unchanged — the inverse proof.** The claim is that no executable byte moved, so the proof is a diff empty by construction, not a green suite.

```
$ git status --short -- '*.py'
 M django_strawberry_framework/__init__.py       # all 17 pre-existing; see the baseline re-read
 M django_strawberry_framework/exceptions.py
 M django_strawberry_framework/scalars.py
 M scripts/bug_hunt.py
 M tests/base/test_init.py
 M tests/filters/test_base.py
 M tests/filters/test_factories.py
 M tests/filters/test_inputs.py
 M tests/forms/test_converter.py
 M tests/forms/test_inputs.py                    # appeared MID-PASS (concurrent)
 M tests/test_bug_hunt.py
 M tests/test_exceptions.py
 M tests/test_resource_policy.py
 M tests/test_scalars.py
 M tests/test_schema.py
 M tests/test_sets_mixins.py
 M tests/test_views.py                           # appeared MID-PASS (concurrent)
?? tests/mutations/test_operations.py
$ git status --short docs/SPECS/
 M docs/SPECS/spec-030-connection_field-0_0_9.md
?? docs/SPECS/appx/spec-030-connection_field-0_0_9-rationale.md
```

Every dirty `.py` belongs to the concurrent session; none is `connection.py`, `optimizer/extension.py`, `optimizer/plans.py`, `list_field.py`, `utils/querysets.py`, or `tests/test_connection.py`, which are the files this slice's contract covers. The only version-controlled paths this pass wrote are the spec, the companion, and this artifact; `docs/builder/worker-memory/worker-1.md` is the fourth write and is gitignored.

**4. Focused tests run (no `--cov*` flag in any form).**

```
$ uv run pytest tests/test_connection.py tests/optimizer/test_extension.py --no-cov -q
237 passed in 57.92s
```

Recorded as run-and-passing, per `worker-1.md` step 5. This is a sanity confirmation, not evidence for any claim above: nothing executable changed, so a green run here could not have failed differently. `tests/optimizer/test_extension.py` is in scope because sub-check 6's no-regression check lives there.

**5. Byte counts (measured, `wc -c` / `wc -l`).**

| File | Before this pass | After | Delta |
|---|---|---|---|
| `docs/SPECS/spec-030-connection_field-0_0_9.md` | 124,482 B / 706 lines | 132,612 B / 716 lines | **+8,130** B / +10 lines |
| `docs/SPECS/appx/spec-030-connection_field-0_0_9-rationale.md` | 61,742 B / 425 lines | 74,603 B / 443 lines | **+12,861** B / +18 lines |

The spec grew because several corrections are genuinely longer than the claims they replace: a fourth resolver-contract rejection did not exist in the text at all, the sealed boundary's guarantee has to be stated for it to be a contract, and the optimizer helper needed two symbols where the text named one. The corpus ratchet in `BUILD.md` governs the six workflow documents, none of which this pass touched.

### Handed forward to Slices 3-5

Verified at `HEAD` by this pass and **deliberately not fixed** — each belongs to a later slice of this same cycle. Line numbers are post-edit.

**The symbol-rename population is now CLOSED.** Slice 1 handed forward 7 lines (`:358`, `:362`, `:366`, `:393`, `:395`, `:453`, `:563` in its numbering) plus 2 companion sites. All 7 are fixed, and the population turned out to be larger than the handoff described: the Decision-10 heading, the `SyncMisuseError` key-glossary bullet, and the `apply_connection_plan` fence line were not in the inventory. Post-edit, the only occurrences of the old private names in the spec are the two licensed `## Current state` observations (103, 104). The two companion sites Slice 1 named (`:186` `_initial_queryset`, and Decision 7's justification calling the keyset work "deferred") were handled as that handoff prescribed — by appending `**Post-ship:**` bullets under Decision 7 rather than editing moved justification text, which is append-only. **No later slice inherits any part of this population**, so the mid-cycle inconsistency Slice 1 flagged is resolved rather than passed on.

**To Slice 3 (`bld-slice-3-030-optimizer_cooperation.md`):**

- The `Connection-aware optimizer planning` `planned` claim at `:9` (Predecessors), `:27`, `:111` (`Current state` — the licence question applies there too, so grade it before fixing it), `:523` (Doc updates), and DoD item 8.
- The "derived plan is **empty** for every connection field" bound at `:411` (Decision 11 `Scope honesty`), `:73` (Slice-3 checklist), `:503` (Test plan `test_root_connection_field_queryset_is_planned`), and DoD item 6 (`:576`). Two pieces of evidence from this pass that the bound is gone: `tests/test_connection.py::test_root_connection_field_queryset_prefetches_node_many_relation` exists at `HEAD`, and `optimizer/extension.py::apply_connection_optimization` defaults its `selection_extractor` to `_connection_node_child_selections`, i.e. a navigator that descends `edges { node }` — the exact capability the `0.0.9` text says the walker lacks. **Note for that pass:** I edited Decision 11's `Fix:` paragraph and added one after it, and left `Scope honesty` untouched; read both before rewriting, because the new paragraph already states the two conditions under which the plan is a no-op, and those are NOT the same thing as the flat walker's connection-unawareness.
- `:503`'s Test-plan row still asserts the plan is empty. Slice 3's, but flagged here because S9 rewrote the rows around it and left that one deliberately alone.

**To Slice 5 (audit-only under the cycle's scope fence):**

- Carried forward unchanged from Slice 1: `docs/GLOSSARY.md` has no `Meta.cursor_field` heading while two entry bodies reference it; `CHANGELOG.md` has no entry for the keyset-cursor feature. Record only.
- New from this pass: **the already-sliced-`QuerySet` `GraphQLError` is shipped public behavior with no `CHANGELOG.md` entry and no glossary mention** (`grep -c` over `pre-sliced` / `already-sliced` in both files returns 0). It is a consumer-visible error contract on a shipped field. Record for the maintainer; `CHANGELOG.md` and `docs/GLOSSARY.md` are fenced out of this cycle.

**To the integration pass:**

- `:553` "**Auto-trigger of `finalize_django_types()`** — deferred to `032`" (Decision 12's Out-of-scope twin), carried from Slice 1 and still unaudited.
- The unused `[goal]` link definition — pre-existing, harmless, named so a later sweep does not attribute it to this pass.
- **A method note worth carrying rather than a defect:** `_guard_source_not_pre_sliced` reached the shipped package through a commit with no card and no spec. If the integration pass wants one cross-cutting check, it is worth sweeping `connection.py`'s other guards for the same shape — a boundary whose owning contract never learned about it. This slice found one by reading; there may be siblings in the module's `032` / `033` / `0.0.14` regions, which no `030` slice audits.

### Summary

Slice 2's whole contract is satisfied at `HEAD`: the Meta-only `DjangoConnectionField` factory with the four `DjangoListField` guards in their load-bearing order plus a Relay-Node fifth sharing the canonical `_is_relay_shaped` predicate; the synthesized `__signature__` carrying exactly the sidecars the type declares, with no `search:` and with orphan-ledger registration as a side effect of building the annotations; the composition pipeline in the contracted order on both the sync and async paths, ending in the deterministic total order and then the optimizer plan; all four consumer-`resolver=` cases plus the escalated `totalCount`-over-non-queryset rejection, whose test asserts the engine's non-null violation does NOT appear; Decision 10's build-time dispatch freeze, with its `SyncMisuseError` consequence pinned under sync AND async execution; and one plan-application core, `DjangoOptimizerExtension.apply_to`, genuinely shared by the middleware and the connection field's entry point rather than copied.

**CODE GAP list: empty.** Twelve reconciliation items landed in the spec — the never-taken `FieldExtension` fallback removed, three sub-bullet corrections, the fourth consumer-resolver rejection contracted across 4 sites, Decision 7's steps 1/5/6 and its consumer-resolver paragraph split and hardened with the sealed-boundary guarantee, Decision 10 renamed and its stale vocabulary fixed in all 3 places it appeared, Decision 11's helper shape and two unstated behaviors, 6 Test-plan rows rewritten, DoD item 5, a symbol that never existed, and one new link definition — each with its "what changed and why" in the rationale companion and none of it in the spec. `check_spec_glossary` holds at `OK: 50 terms`, both link scaffolds validate, every in-page anchor and cross-file def anchor resolves across the renamed Decision 10, the `.py` surface is byte-unchanged, and the focused 237-row scope passes.

### Spec changes made (Worker 1 only) — deferral reasons for unticked boxes

None. Every box in `### Spec slice checklist (verbatim, as audited)` is ticked because the shipped code satisfies it at `HEAD`. No box is deferred and none is un-ticked, so there is nothing to record here beyond that statement.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[glossary-configurationerror]: ../GLOSSARY.md#configurationerror
[glossary-djangolistfield]: ../GLOSSARY.md#djangolistfield
[glossary-finalize_django_types]: ../GLOSSARY.md#finalize_django_types
[glossary-metafilterset_class]: ../GLOSSARY.md#metafilterset_class
[glossary-metaorderset_class]: ../GLOSSARY.md#metaorderset_class
[glossary-syncmisuseerror]: ../GLOSSARY.md#syncmisuseerror

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[connection]: ../../django_strawberry_framework/connection.py
[optimizer-extension]: ../../django_strawberry_framework/optimizer/extension.py
[optimizer-plans]: ../../django_strawberry_framework/optimizer/plans.py

<!-- tests/ -->
[test-connection]: ../../tests/test_connection.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
