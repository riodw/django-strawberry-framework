# Build: R2 — Reconcile the spec with what landed (spec-003)

Spec reference: `docs/SPECS/spec-003-optimizer_nested_prefetch_chains-0_0_2.md` (whole file)
Rationale file extended: `docs/SPECS/appx/spec-003-optimizer_nested_prefetch_chains-0_0_2-rationale.md`
Status: final-accepted

**Shape note.** Per `docs/builder/build-003-optimizer_nested_prefetch_chains-0_0_2.md` Deviation 2, R2 has no Worker 2 pass: `docs/builder/BUILD.md` `## Spec reconciliation` and `docs/builder/worker-1.md` `## Scope` make Worker 1 the only role that may mutate the spec, and R2's entire deliverable is spec edits. So the `## Build report (Worker 2)` section of `docs/builder/ARTIFACT.md` is not applicable and the performance record lives under `## Reconciliation report (Worker 1)` below, carrying the same fields Worker 3 would otherwise read from a build report. `Status:` is `planned` on return, which Worker 0 reads as "dispatch Worker 3" for this item.

---

## Plan (Worker 1)

### DRY analysis

- **Helper inventory checked.** Not applicable, and deliberately so. `worker-1.md` `### Package-wide helper inventory before helper planning` gates *helper-like logic*; R2 changes no package source and adds no helper, constant, validation branch, coercion utility, or test helper. The build plan's `## Build-wide context flags` declares package source, `tests/`, and `examples/` read-only for the whole cycle. No inventory was refreshed and none was needed.
- **Static inspection helper — RUN, not skipped.** `BUILD.md` `### When to run the helper during build` requires `scripts/review_inspect.py --output-dir docs/shadow` for planning that touches `optimizer/` or `types/`. This pass reads those modules rather than adding logic to them, but the trigger is worth honouring in the reading direction too: the **Symbols** sections are the fastest way to establish what a spec-named symbol is called today. Run over nine modules:

  ```shell
  uv run python scripts/review_inspect.py django_strawberry_framework/optimizer/{walker,plans,nested_planner,join_taxonomy,extension,hints,selections,field_meta}.py --output-dir docs/shadow
  uv run python scripts/review_inspect.py django_strawberry_framework/types/resolvers.py --output-dir docs/shadow
  ```

  (one invocation per file; the loop is elided for readability). Eighteen files landed under `docs/shadow/`. The **Symbols** section of the walker overview is what settled D1/D7/D10/D13 in one read — every spec-named private helper either appears there under a different name or does not appear at all. Shadow line numbers are not cited anywhere; every source reference in the spec, the rationale, and this artifact is symbol-qualified (`AGENTS.md` rule 27).
- **Existing patterns reused.** The precedent for the whole item is the spec-002 residual cycle (`docs/builder/build-002-optimizer-0_0_2.md`) and the two archived rationale files at the same depth. The section shape for the appended rationale block follows `## Entries keyed to the spec` in the same file — one entry per spec section, each carrying *Changed* / *Alternative rejected* / *Claims the spec no longer makes* — so a reader meets one vocabulary across both passes rather than two.
- **New helpers justified.** None; no code was written.
- **Duplication risk avoided.** Three live risks, all named and all handled:
  - **Spec versus rationale.** The build plan's DRY rule is explicit that a fact told twice across the two files goes stale in one of them. Every reconciliation entry in the rationale states *why* a claim changed; the spec states only *what* now holds. No entry's contract text is reproduced on both sides.
  - **Spec versus sibling specs.** The scope trap. Four later specs extended this subject matter, and the strongest pull rows (D8, D9, D12, D18, D22) were each resolved with a pointer rather than a transplant. Recorded per row in `### Verification of the 22-row drift floor` below and argued per section in the rationale.
  - **Spec versus itself.** Two statements of the same contract inside one spec rot the same way. One was found and removed: the `## Plan shape` sentence about nested relations landing in `select_related` restated the same-query recursion bullet that already carries it.

### Implementation steps

Line numbers are pin-at-write-time; all are against the **post-R1** spec unless stated.

1. Re-verify each of the 22 drift rows against HEAD source rather than trusting the table. Done — `### Verification of the 22-row drift floor`.
2. Sweep the whole spec for falsified claims the table does not carry (it is a verified floor, not an inventory). Done — nine further items, `### Drift found beyond the floor`.
3. `## Problem statement` (:6-8) — restate the slice's subject and its change as contract; delete the two sentences describing the pre-O4 walker and its TODO anchor. Done.
4. `## End-goal context` (:10-18) — retense the B-slice framing and the B8 bullet; replace the `_optimizer_field_map` symbol with the property it protects; fix the cross-reference to a heading that does not exist. Done.
5. `## Current state` -> `## Plan shape` (:20-34) — rename the section, restate the field inventory as the six bags O4 owns plus a pointer for the rest, drop the published planner signature for the two facts it carried, correct `only_fields` from root-relative to queryset-relative. Done.
6. `## Desired behavior` (:37) — qualify the three query counts on the O6 interaction the spec itself specifies. Done.
7. `## Implementation design` + `### Same-query recursion` (:63-74) — restate the dispatch guarantee, name the nested-connection third case and hand it to `spec-033`, drop three "(already done)" parentheticals and the obsolescence paragraph. Done.
8. `### Prefetch-boundary recursion` (:76-95) — route the visibility hook through the shared boundary, restate the `plan_relation` refactor instruction as its resulting contract, correct the `Prefetch` lookup segment to the instance accessor, add reverse-OneToOne to the connector arm. The rescued parent-side-append bullet is left byte-identical. Done.
9. `### Hints are leaf operations` + `### B4 optimizer hints` (:97-100, :140-146) — drop the two discharged doc/build instructions; add the two `force_select` facts and the `force_prefetch` second-route clause. Done.
10. `### Lookup-path flattening` (:112-113) — drop the position instruction and the direct private-attribute read. Done.
11. `### Resolver sentinel keys` (:115-131) — restate the leak argument as the standing reason for the key format; make the runtime-path plurality explicit; replace the two-mirrored-implementations conclusion with the one-shared-implementation contract; drop two falsified symbol names and one sequencing paragraph. Done.
12. `### B1 plan cache` / `### B3 strictness` / `### B8 queryset diffing` (:134-158) — correct the cacheable-propagation site, retense B3 and B8. Done.
13. `## Test plan` (:160-189) — move the query-count rows to the live tier with the reason, qualify the forward-FK count, name both elision-leak axes, drop two container-type assertions and one build instruction. Done.
14. `## Definition of done` (:198-208) — rewrite bullet 2's dead symbol; delete bullet 8's orphaned TODO clause. Done.
15. Delete `` ## Missing `.py` files `` in full. Done.
16. Append the reconciliation entries to the rationale, keyed to spec sections, with rejected alternatives and claims-no-longer-made per entry; repair the one in-page anchor the rename moved. Done.
17. Re-run `check_spec_glossary.py`, `check_trailing_commas.py --check`, and `import_spec_terms --check`; re-count all 8 anchors per anchor. Done — `### Validation run`.

### Test additions / updates

None. R2 adds no test and changes no code path. `AGENTS.md` rule 15 forbids a `pytest` run that was not asked for, and the build plan declares package source, `tests/`, and `examples/` read-only for the whole cycle. The verification for this item is the four commands under `### Validation run` plus the per-row source re-derivation in `### Verification of the 22-row drift floor`.

The spec's `## Test plan` was *edited*, which is not the same thing: no test file was touched. What the edits assert about the test surface was checked against the tree read-only, per row, and is recorded in `### Test-plan rows re-checked against the tree`.

### Boundary count

**Zero.** R2 introduces no guard, cap, rejection path, or validation branch — it changes no executable code. `BUILD.md` `### Slice splitting`'s second trigger therefore does not fire, and the split question is answered: this item is one unit because its whole deliverable is one document's internal consistency, and a half-reconciled spec is worse than an un-reconciled one (`worker-1.md` `## Review-round custody`). Splitting the sweep across two passes would guarantee exactly that state between them.

### Implementation discretion items

None reserved. R2 has no downstream builder, so nothing is delegable.

### Dispatched findings checklist

There is no `## Slice checklist` in spec-003 and this is not a review round, so — per `worker-1.md` planning step 8, which puts a `### Dispatched findings checklist` in this position when no spec slice checklist exists — the boxes below are the R2 obligations drawn from the maintainer's framing, `BUILD.md` `## Spec reconciliation` and `## Spec rationale extraction`, and the build plan's R2 constraints. Worker 1 both performs and ticks here because Deviation 2 removes the Worker 2 pass; the ticks are audited at Worker 1's own final verification after Worker 3.

- [x] Every one of the 22 drift rows re-verified against HEAD source rather than trusted from the table.
- [x] The table treated as a verified floor, not an inventory: the whole spec swept for further falsified claims.
- [x] Every falsified claim restated as the contract that actually holds, handed to the spec that now owns it, or deleted.
- [x] The spec never narrates its own history: no amendment block, no retraction paragraph, no "as of spec-NNN" hedge, no "originally this was X".
- [x] The explanation of every change lands in the rationale, keyed to the spec section it serves.
- [x] Every rationale entry that weighed an alternative records it with the one-line reason it lost. (Restated in the correcting pass from an unqualified universal, which was an over-tick: 10 of the 14 reconciliation entries carry an *Alternative rejected*; the other 4 record a correction that had no alternative in contention, and none is padded with a manufactured one. Measured in `## Reconciliation report (Worker 1, pass 2)` `### The two over-ticked boxes, measured and restated`.)
- [x] Every rationale entry records the claims the spec may no longer make. (14 of 14 as of the correcting pass; it was 10 of 14 when first ticked, which was an over-tick. The four missing lines were supplied rather than the box weakened — same measurement.)
- [x] The scope trap held: D8 / D9 / D12 / D18 / D22 resolved by pointer, not by transplanting another spec's surface.
- [x] The eight R1 hand-off items each dispositioned, and the disposition recorded.
- [x] All 8 glossary anchors still carry exactly one body link; the terms CSV was not opened.
- [x] `check_spec_glossary.py --spec …` exits 0 after every writing session, with the result quoted.
- [x] `check_trailing_commas.py --check` passes on the spec, the rationale, and this artifact.
- [x] `import_spec_terms --check` still exits 0 — the DONE-card glossary chain survives.
- [x] Every in-page anchor the rationale targets still resolves against a real spec heading.
- [x] Reference-style links only, `<!-- LINK DEFINITIONS -->` present with all 10 canonical group headers in order, every definition target disk-checked.
- [x] `AGENTS.md` rule 27 holds in the spec and the rationale: no raw `path:NN`, every source reference symbol-qualified.
- [x] No package source or test file touched; no sibling spec touched.
- [x] Every count the item's conclusions rest on is command-produced, with the command quoted beside it, and every figure found wrong is superseded by one. (Restated at final verification from an unqualified universal, which was an over-tick of the same shape as the *Alternative rejected* box above: **six** figures were stated in this cycle without the command that produces them — R1's "13 anchors" and "eight relabelled", R2 pass 1's "three backward-looking sentences", "19 entries", and "10 status-language hits", plus M3's two universals. All six are superseded in place by a commanded figure — three in `### The three superseded figures`, one in `### Validation run (pass 2)`, two in `### The two over-ticked boxes, measured and restated` — and Worker 3 re-derived every re-derivable figure in pass 2 exactly. The practice failed six times and the record now carries the correction beside each failure; the universal did not hold and is not asserted.)

---

## Reconciliation report (Worker 1)

### Files touched

- `docs/SPECS/spec-003-optimizer_nested_prefetch_chains-0_0_2.md` — the reconciliation. One section renamed, one section deleted, thirteen sections rewritten in place.
- `docs/SPECS/appx/spec-003-optimizer_nested_prefetch_chains-0_0_2-rationale.md` — one appended top-level section (`## Reconciliation pass — what the spec now says, and why`), one repaired in-page anchor, one added link definition.

Nothing else. `git status --short` after the pass shows this cycle's three paths plus the concurrent session's fourteen, all of which are in the build plan's `## Baseline-dirty out-of-scope files` and none of which was edited or reverted.

### Byte count

| | lines | bytes | source of the figure |
|---|---|---|---|
| spec at HEAD (pre-R1) | 447 | 34,030 | `wc -lc` over `git show HEAD:<spec>` into a scratch path outside the repo |
| spec after R1 | 241 | 25,786 | recorded in `docs/builder/bld-003-r1-rationale_move.md` `## Final verification (Worker 1)`; not re-derivable, R1 is uncommitted |
| spec after R2 | **240** | **27,864** | `wc -lc` on the working tree |
| R2's own delta | -1 | **+2,078** | arithmetic on the two rows above |
| rationale after R1 | 511 | 35,645 | same R1 artifact |
| rationale after R2 | **925** | **63,778** | `wc -lc` on the working tree |
| R2's own delta | +414 | **+28,133** | arithmetic |

`git diff --stat` on the spec reports `78 insertions(+), 285 deletions(-)` — that is **cumulative over R1 and R2**, R1 having contributed `18 / 224`.

The spec grew 2,078 bytes while losing a line. That is the expected shape: a falsified one-clause status claim ("this is already done") is replaced by the rule it was annotating, plus the reason the rule matters. Two sections got materially longer for that reason — the `Prefetch` lookup-segment bullet and the resolver-key protocol paragraph — and one section was deleted outright.

### Verification of the 22-row drift floor

Every row re-derived at HEAD with the symbol-qualified path given, not accepted from the build plan. All 22 confirmed; none was found overstated or wrong.

| # | Re-verified how | Disposition in the spec |
|---|---|---|
| D1 | `grep -rn '_collect_scalar_only_fields' django_strawberry_framework/ tests/ examples/` → **0 hits**. The recursion is `optimizer/walker.py::_plan_select_relation #"_walk_selections("` | Every mention deleted; the durable idea (a scalar-only step drops nested relations) folded into the recursion bullet and DoD bullet 2 |
| D2 | `optimizer/walker.py::plan_optimizations` read in full: keyword-only `runtime_prefixes` / `source_type`, `enable_only` derived once via `::_enable_only_for_operation`, returns `plan.finalize()` | Signature no longer published; the two contract facts it carried (empty Django prefix, empty runtime path at the root) stated instead |
| D3 | `grep -rn 'TODO(spec-003' django_strawberry_framework/ tests/ examples/` → **0 hits**. Dispatch is `optimizer/walker.py::_walk_selections #"_dispatch_single_relation("` | Claim deleted; the dispatch guarantee restated without the symbol |
| D4 | `optimizer/plans.py::OptimizationPlan.fk_id_elisions` docstring: "Resolver keys elided because the source row already carries the target id." | Restated as the delivered contract; the "O4 must migrate this bag" instruction deleted |
| D5 | `fields(OptimizationPlan)` enumerated from source: **11** — the 6 O4 owns plus `select_path_resolver_keys`, `prefetch_path_resolver_keys`, and three `finalized_*`. Three `ClassVar` merge partitions asserted at import by `::_assert_merge_field_inventory` | Six listed; five pointed at `spec-033` / `spec-035`. The rationale records why enumerating all eleven loses |
| D6 | `optimizer/plans.py::OptimizationPlan.finalize` swaps lists to tuples and computes three frozensets; `::_assert_under_construction` rejects a merge onto a finalized plan | One clause ("finalized at handoff") inside the pointer sentence; no paragraph. Scope trap held |
| D7 | `optimizer/walker.py::_plan_select_relation` reached via `::_dispatch_single_relation`; `optimizer/plans.py::append_unique` is public; the FK-column append is `walker.py::_record_relation_access` | Dispatch guarantee restated; no symbol published |
| D8 | `optimizer/walker.py::_build_child_queryset #"apply_type_visibility_sync(target_type, queryset, info, allow_sliced=True)"`, base is `field.related_model._default_manager.all()` | **Pointer to `spec-045`.** The spec states "route through the shared visibility boundary, never a direct hook call" and explicitly does not restate the boundary's rules |
| D9 | `optimizer/walker.py::_ensure_connector_only_fields` keeps the name and the `if not plan.only_fields: return` guard; rules live in `optimizer/join_taxonomy.py::_parent_join_column`, whose first arm reads `if getattr(field, "one_to_many", False) or kind == "reverse_one_to_one":` | **Rules kept as rules** (they are spec-003's contract), `reverse_one_to_one` folded into the existing arm as one clause. Where the rules now live is not published |
| D10 | `optimizer/walker.py::_plan_prefetch_relation`, `::_build_prefetch_child_queryset`, `::_build_prefetch_child_queryset_from_base`; `::plan_relation` returns `tuple[str, str]` and constructs nothing | The refactor instruction restated as its resulting contract |
| D11 | `optimizer/walker.py::_plan_prefetch_relation #"lookup_path = f\"{prefix}{instance_accessor(django_field)}\""`, with the helper's own docstring carrying the `AttributeError` history | **The one row where the code corrected the spec.** Stated as contract, with Django's reason and the boundary of the rule (only the string Django consumes uses the accessor) |
| D12 | `optimizer/walker.py::_walk_selections #"if resolved is not None and resolved[0] == \"connection\":"` routes to `optimizer/nested_planner.py::plan_connection_relation` | **Pointer to `spec-033`**, one clause naming it a third case. No description of the windowed / lateral strategies |
| D13 | `optimizer/plans.py::resolver_key` and `::runtime_path_from_info` are public and shared, imported by both `walker.py` and `types/resolvers.py`; `::runtime_path_from_path` is bounded by `_MAX_PATH_DEPTH = 1024`; `_is_fk_id_elided` / `_get_relation_field_name` → **0 hits**; the elision test is inlined at `types/resolvers.py::_make_relation_resolver.forward_resolver #"if elisions and key in elisions:"` | Key format kept verbatim (D13 confirms it shipped exactly); the two-mirrored-implementations conclusion replaced by the one-shared-implementation contract |
| D14 | (i) `spec-002` has no `## Current state`; (ii) the `spec-004` rider survives; (iii) 0 `TODO(spec-003` anchors in source or tests; (iv) `grep -rn "\bO4\b" django_strawberry_framework/` → **0 hits** | R1 already trimmed the section to the one open obligation. **R2 changed nothing here** — the rider is R3's, and the in-spec clause that licenses it must survive until then |
| D15 | Same 0-anchor sweep; the two TODO comments `review_inspect.py` reports in `walker.py` are `TODO(spec-035)`, read directly at `walker.py::_walk_selections` and `::_selected_scalar_names` | Section already deleted by R1; R2 removed its last orphaned referent (DoD bullet 8's clause) |
| D16 | `optimizer/plans.py::diff_plan_for_queryset`, `::prune_unsupportable_select_related`, wired at `optimizer/extension.py #"# B8 pre-publish prune"` | Both `## End-goal context` and `### B8 queryset diffing` retensed to the present |
| D17 | `optimizer/plans.py::lookup_paths` short-circuits on `plan.finalized_lookup_paths`, else `::_lookup_paths_from_parts`; `::_prefetch_lookup_paths(entries, prefix="")` recurses to arbitrary depth with a `prefetch_to is None` skip and routes through `::_consumer_prefetch_lookups`; the helper is the **last** symbol in a 1,384-line file | Module stated, position dropped; the private-attribute read dropped without importing `spec-035`'s single-reader rule |
| D18 | `optimizer/walker.py::_resolver_identities_for` returns the cartesian product of `_optimizer_runtime_prefixes` × `_response_keys(sel)`; alias preservation at `::_merge_aliased_selections` | **Split deliberately.** The response-key plurality is O4's (O4 is what made a merged node carry more than one key) and is stated; the runtime-prefix fan-out is `spec-033`'s and is one parenthesis |
| D19 | Same 0-anchor sweep | DoD bullet 8's clause deleted; the rest of the bullet kept |
| D20 | Package: `tests/optimizer/test_walker.py::test_plan_emits_nested_select_related_chain_depth_2` asserts `select_related == ("item", "item__category")` and the exact three `only_fields`. Live: `examples/fakeshop/test_query/test_products_api.py::test_products_optimizer_selects_nested_forward_fk_depth_2_over_http` docstring and body pin **3** queries, "one `allEntries` slice + one `item` prefetch + one `category` prefetch" | The counts are qualified on the O6 downgrade — which this spec itself specifies — rather than on the example project's configuration. `spec-034` is not mentioned |
| D21 | Section already deleted by R1 | Nothing owed; its two design-grade clauses survive in the spec's own prose |
| D22 | `optimizer/nested_planner.py`, `optimizer/selections.py`, `optimizer/join_taxonomy.py`, `optimizer/nested_fetch.py` all present under `django_strawberry_framework/optimizer/` | **Section deleted.** Build guidance in the imperative, discharged, and false as a present-tense map. The rationale records both rejected alternatives (re-point it; retense it) |

Four rows the build plan had spot-checked (D1, D2, D11, D14-ii) were re-derived here independently and all four match.

### Drift found beyond the floor

The build plan is explicit that its table is Worker 0's verified floor and that R2 owns the full sweep. Nine further items, each verified at HEAD:

1. **`_optimizer_field_map` does not exist.** `grep -rn '_optimizer_field_map\|optimizer_field_map' django_strawberry_framework/` → **0 hits**. The map is the registered definition's, resolved per entry by `optimizer/walker.py::_resolve_field_map`. The *property* the bullet protects is live: `::_walk_selections` opens with that call, so each recursion resolves the map for the model it is descending into. Property kept, symbol dropped.
2. **A cross-reference names a heading that does not exist.** `## End-goal context` said `see "Lookup paths vs resolver keys" below`; the heading is `## Lookup paths vs resolver sentinel keys`. Fixed.
3. **`only_fields` was described as "root-query scalar paths".** That contradicts `### Prefetch-boundary recursion`'s whole point — a child plan's `only_fields` are relative to the child queryset (`optimizer/walker.py::_build_prefetch_child_queryset_from_base` walks the child at `prefix=""`). Corrected to queryset-relative.
4. **The cacheable propagation was attributed to the wrong site.** `### B1 plan cache` said `_walk_selections`'s prefetch branch "copies `child_plan.cacheable` upward". At HEAD it travels with the rest of the child's resolver metadata through `optimizer/walker.py::_absorb_child_plan` → `optimizer/plans.py::OptimizationPlan.merge_metadata_from #"if not other.cacheable:"`, whose docstring states the reason ("so a future third site cannot forget it"). Restated with that reason, which is the implementation-relevant half.
5. **`force_select` on a many-side relation is rejected outright** — `optimizer/walker.py::_apply_hint #"Django requires prefetch_related for"` raises `ConfigurationError`. The spec never said so.
6. **`force_select` yields to O6.** `::_apply_hint` dispatches it with `prefer_prefetch=_target_has_custom_get_queryset(target_type)`, so a target overriding `get_queryset` crosses the prefetch boundary despite the hint. The spec's bullet implied the opposite. Both 5 and 6 are O4's own composition question (hints × cardinality × O6 at nested depth) and this section is the only place in the corpus that answers it.
7. **Two test-plan rows asserted list equality** (`select_related == ["item", "item__category"]`). The field is a tuple after `finalize()` (`optimizer/plans.py::OptimizationPlan.finalize`). Rewritten as coverage rather than container type, which is what the rows were pinning and does not re-break at the next storage change.
8. **`_attach_relation_resolvers(cls, fields)` is no longer that signature** — `types/resolvers.py::_attach_relation_resolvers` takes a keyword-only `skip_field_names`. The clause naming the signature was the carrier of a real contract (resolvers are attached per type, so each closure binds its own parent type); the contract stayed, the signature went.
9. **"Document this explicitly in `hints.py`" is discharged.** `optimizer/hints.py::OptimizerHint.prefetch` carries it: "This is a leaf operation. The consumer-provided queryset is the source of truth … not walked by the optimizer." Instruction deleted, rule kept.

Item 9's counterpart in the other direction was also checked and is **not** drift: `## Definition of done` bullet 8's ruff obligation is generic but true, so only its orphaned TODO clause went.

### The eight R1 hand-off items, dispositioned

| # | Item | Disposition |
|---|---|---|
| 1 | `## Definition of done` bullet 8 ends "…with TODO-anchored pseudo-code findings left untouched", an orphaned reference as well as a false one | **Closed.** Clause deleted; the ruff obligation kept. Recorded in the rationale's DoD entry with the rejected alternative (delete the whole bullet) |
| 2 | `### Hints are leaf operations`, `### Same-query recursion`'s trailing paragraph, and `## Problem statement` still name `_collect_scalar_only_fields` | **Closed.** All three rewritten; the trailing paragraph deleted outright under rule 2. Repo-wide grep confirms the spec now carries **0** occurrences of the symbol |
| 3 | `` ## Missing `.py` files `` is true of the change and false as a map | **Closed by deletion**, with both rejected alternatives recorded |
| 4 | The open `spec-004` rider is the only bullet left in `## Documentation updates when O4 ships`; R3 discharges it | **Untouched, deliberately.** R2 must not pre-empt R3, and the in-spec clause is what licenses the sibling edit. Flagged forward under `### Notes for Worker 1 … carried into R3` |
| 5 | The rescued parent-side FK-column append bullet is contract, not status prose — leave it alone | **Honoured.** `sed -n '79p'` on the spec is byte-identical to the pass-3 text; the pass touched neither the bullet nor its scope sentence |
| 6 | The fence-count correction belongs in the closeout, not a spec edit | **Honoured.** No spec edit; the build plan already carries the correction and is Worker 0's file |
| 7 | Whether the prefetch-boundary section should name the `force_prefetch` route alongside the O6 downgrade | **Answered: yes.** The rescued bullet at `:79` already named both routes; the section's lead-in and the B4 bullet did not agree with it. The B4 `force_prefetch` bullet now says outright that it is the second route into that branch, so the three sentences describe one population |
| 8 | Whether the spec should document that a forward `ManyToManyField` passes the `attname` guard | **Answered: no**, and the reason is recorded in the rationale. Django sets `ManyToManyField.attname` to the field's own name, so a field name rather than a column reaches `only_fields`; Django drops it from the compiled `SELECT` and nothing is broken. Writing it into the spec would document a harmless artifact as contract and would invite a future reader to narrow the guard below what HEAD needs. It stays a maintainer note and goes to the deferred-work catalog |

### Test-plan rows re-checked against the tree

The build plan's `### Test-plan coverage — nothing was skipped` table is pre-verified and was not re-derived. What R2 owed was narrower: for the four rows it *edited*, confirm the edit describes the tree.

- Both query-count rows: `grep -n 'def test_products_optimizer_prefetches_nested_reverse_fk_depth_2_over_http\|def test_products_optimizer_selects_nested_forward_fk_depth_2_over_http' examples/fakeshop/test_query/test_products_api.py` → present at the live tier. Read at the file's **current** content, which is dirty from the concurrent renumber sweep; the two test bodies carry no `TODO-BETA` token and are unaffected by it.
- The forward-FK row's count: the test's own docstring and assertion pin **3**, and state the reason (both `ItemType` and `CategoryType` define a custom `get_queryset`, so each forward FK O6-downgrades). The spec's rewritten row is consistent with both 1 and 3 and says to derive the number from a real run, which is `BUILD.md` `### Query-shape tests must pin the load-bearing property`'s own instruction.
- The sibling-leak row's two axes: `examples/fakeshop/test_query/test_scalars_api.py::test_scalars_optimizer_fk_id_elision_does_not_leak_to_sibling_root_in_http_query` (root axis) and `tests/types/test_resolvers.py::test_b2_forward_fk_id_elision_does_not_leak_across_parent_types` (parent-type axis), both confirmed present.
- The two container-type assertions: `tests/optimizer/test_walker.py::test_plan_emits_nested_select_related_chain_depth_2` asserts a **tuple**, confirming the list-equality wording was stale.

No test file was opened for writing.

### The read-only correctness audit

**No defect found, and none introduced.** The build plan's four pre-verified observations were carried, not re-derived, with one exception: observation 4 (the unguarded ordering invariant between the connector-column append and the elision short-circuit) was re-read at `optimizer/walker.py::_record_relation_access`, whose docstring states it and whose caller `::_plan_select_relation` calls it first. It has no automated guard, exactly as recorded.

The three "correct as designed; not drift" notes were **not** mistaken for things to fix:

- the elision path deliberately not recording `select_path_resolver_keys` — confirmed at `optimizer/walker.py::_plan_select_relation`, whose elision arm `return`s before `::_record_select_path_keys`, and at `::_plan_prefetch_relation #"Nested FK-id elisions are deliberately NOT recorded"`. Left alone;
- `cacheable` propagating in exactly one place — this one *did* produce a spec edit, but the edit corrects the spec's account of **where** the propagation lives, not the code. The design is unchanged and the spec now states its reason;
- the four B2 guards surviving in one predicate — confirmed at `::_plan_select_relation #"if ("`. The spec's four-guard list is accurate and was left as written except for one status word.

`AGENTS.md` rule 5 governs what a fix would look like if the maintainer authorized one; it does not authorize a documentation cycle to become a code cycle. `git diff -- django_strawberry_framework/ tests/ examples/` carries nothing from this pass.

### Validation run

- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-003-optimizer_nested_prefetch_chains-0_0_2.md` → `OK: 8 terms - all have glossary entries and at least one spec link.` **exit 0**. Run after each of the three writing sessions; identical every time.
- `uv run python scripts/check_trailing_commas.py --check docs/SPECS/spec-003-… docs/SPECS/appx/spec-003-…-rationale.md` → **exit 0** on both. Re-run on this artifact before returning.
- `uv run python examples/fakeshop/manage.py import_spec_terms --check` → `OK: 49 done cards have glossary links.` **exit 0** — the card-wrap chain the 8-anchor constraint protects is intact, re-checked **after** the concurrent session's DB write rather than trusted from the pre-flight baseline.
- Link scaffold, both files, measured by a script that strips the definition block before counting body uses: spec **10 definitions / 10 distinct uses**, rationale **19 / 19**; **0 undefined references, 0 unused definitions, 0 missing on-disk targets** across both.
- In-page anchors: an independent slugger over the post-R2 spec reports **21 headings, 0 duplicate slugs**; the rationale carries **9 anchor-bearing definitions** used **10 times** in its body; **0 unresolved**. The one anchor the rename moved (`#current-state` → `#plan-shape`) was repaired and re-verified.
- `grep -nE '[a-zA-Z_/]+\.(py|md):[0-9]+'` over both files → **no match**. `AGENTS.md` rule 27 preserved.
- No inline `](path)` link in either file (URL and in-page-anchor exclusions applied); `grep -c '```'` on the spec → **0** fenced blocks, unchanged from R1.
- Dead-symbol sweep over the spec for every private helper the pre-R2 text named — `_collect_scalar_only_fields`, `_is_fk_id_elided`, `_get_relation_field_name`, `_optimizer_field_map`, `_runtime_path_from_info`, `_walk_selections`, `_append_unique`, `_merge_aliased_selections`, `_build_child_queryset`, `_ensure_connector_only_fields`, `_attach_relation_resolvers`, `_make_relation_resolver`, `TODO(spec-003` → **no match on any of the twelve**.
- Status-language sweep (`currently|already|today|not yet|will |becomes obsolete|planned|future`) → 10 hits, each read individually; **9 are runtime or in-document references** (Django's matching behaviour, the plan under construction, the consumer's queryset, the literal rider text R3 owns) and the tenth was a real residue ("the same safety guards already in place") and was fixed.
- `git status --short` → this cycle's three paths plus the concurrent session's fourteen. `examples/fakeshop/db.sqlite3`, `KANBAN.md`, `KANBAN.html` are dirty **from that session**, exactly as the build plan records; `docs/GLOSSARY.md` is **clean**. Nothing was reverted and no `git checkout` was run.
- No `pytest` (`AGENTS.md` rule 15); no `--cov*` flag in any form; no `git stash` / `checkout` / `restore` / `worktree` at any point. The HEAD reference was obtained read-only via `git show HEAD:<spec>` into a scratch path outside the repository.
- No `ruff` run: no `.py` file was touched.

### The 8-anchor constraint — per-anchor result

All 8 survive at **exactly one body link each**, matching R1's post-move count with zero attrition. Measured as `grep -o "\[<ref-id>\]" | wc -l` per anchor, which returns 2 for each (one definition + one body use):

| Anchor | Carrier after R2 | Touched by R2? |
|---|---|---|
| `queryset-diffing` | `## End-goal context` B8 bullet | yes — the bullet was retensed; the link travelled with it |
| `schema-audit` | `## End-goal context` B-slice list | yes — the list's lead-in was retensed; the link is untouched |
| `plan-cache` | `## Plan shape` `cacheable` bullet | yes — the section was renamed and the bullet list rebuilt; the `cacheable` bullet and its link were carried verbatim |
| `metaoptimizer_hints` | `## End-goal context` B4 bullet | no |
| `fk-id-elision` | `## End-goal context` B2 list entry | yes — same retensed lead-in; link untouched |
| `only-projection` | `### Prefetch-boundary recursion …` lead-in prose | no — the lead-in sentence was not edited |
| `optimizerhint` | `### Hints are leaf operations` | yes — the paragraph was rewritten around the link, which was preserved character-for-character |
| `djangotype` | `## Lookup paths vs resolver sentinel keys` | no |

**Five of the eight sat inside prose R2 rewrote**, which is the exact failure mode the build plan warned about. Each was re-sited by carrying the link into the surviving contract sentence — never by re-adding narration and never by editing the terms CSV, which was not opened.

### The heading rename, and why it is the only anchor move

`## Current state` → `## Plan shape` is the one edit that moves an in-page anchor. It was made because a section named "Current state" announces by name that what follows describes the codebase *before* the change — the exact framing that goes stale, and one a spec that had been right from the start would never carry.

`BUILD.md` `## Spec rationale extraction` requires every rationale entry to name its spec decision **by heading and anchor**, so leaving the entry pointing at a dead anchor would have broken the rule the rename otherwise serves. Two mechanical repairs followed, both recorded under `### Spec changes made (Worker 1 only)`:

- the link definition `[spec-003-current]` re-pointed from `#current-state` to `#plan-shape`;
- the R1 entry's `Spec:` line amended to name the surviving heading and point at the reconciliation entry that explains the rename.

The R1 entry's own heading, and the two `## Provenance of this record` bullets that name `## Current state`, were **left alone**: they are R1's settled record of what R1 cut, `worker-1.md` `### Performing the rationale move` rule 4 makes the file append-only against a later pass, and the appended entry states the rename plainly so the two vocabularies reconcile.

No other document links that section: `grep -rn 'spec-003-optimizer_nested_prefetch_chains-0_0_2.md#'` across the repo returns hits only in the rationale.

### Failability proofs

None; this pass introduced no new boundary. R2 changes no package source — `git diff -- django_strawberry_framework/` is empty.

### Hot-path budget

Not applicable; plan declares no hot path.

### Floor verification

Not applicable; plan declares floor-verification scope none.

### Implementation notes

- **The governing principle was applied as a hard rule, not a preference.** Not one sentence in the reconciled spec says what a claim used to be. There is no amendment block, no retraction, no "as of spec-035", no "originally". The three surviving backward-looking sentences are the per-section pointers R1 added, which `worker-1.md` rule 1 *requires* ("every decision keeps a one-line pointer naming what was moved and where") and which point at the rationale rather than narrating a change. A reader of the spec alone cannot tell which sentences this pass rewrote — that was the target.
- **Where the scope trap bit hardest, and how each was decided.** D5 (enumerate all eleven plan fields) was the strongest pull, because the five extra fields are visibly there and a reader might call their absence an omission. It loses on two independent grounds recorded in the rationale: they are other specs' contracts, already stated once each, and a dataclass inventory is a symbol map — the same liability the rationale already argues against for the deleted insertion-point section. D18 was the subtlest: the response-key plurality genuinely **is** O4's (O4 is what made a merged node carry more than one response key) while the runtime-prefix fan-out is `spec-033`'s, so the row splits rather than resolving wholly one way. Splitting it is the only disposition that leaves both specs correct.
- **One row is a correction, not a relocation, and it reads differently in the spec because of that.** D11 is the only place where the shipped code contradicted the spec's design rather than renaming it. The `Prefetch` lookup-segment bullet is therefore the longest in the section: it states the rule, Django's reason for it, and — importantly — the rule's boundary, because a reader who takes "use the accessor" too far corrupts the resolver keys, which stay in field-name vocabulary. The bullet was written from `optimizer/walker.py::_plan_prefetch_relation`'s docstring and body, not from the drift table's summary.
- **Two additions were made that no drift row asked for**, both in `### B4 optimizer hints`, and both are things the spec was silently wrong about rather than merely stale: `force_select` is rejected outright for a many-side relation, and it yields to O6. A reader of the old bullet would expect the hint to force a join in both cases. These are O4's own composition question and no other spec answers them.
- **Deleting a section is a bigger act than rewriting one, so it was argued rather than performed.** `` ## Missing `.py` files `` went because all three of its possible dispositions were considered and two lose: re-pointing it creates a second module map maintained against `docs/TREE.md`, and retensing it to "O4 introduced no new module" preserves a historical fact about an implementation that constrains nobody. Both rejections are in the rationale, so the next reader cannot conclude the section was dropped for convenience.
- **The rationale was appended to, not edited**, with the single exception of the anchor repair described above. R1's entries stand as written.
- **`## Documentation updates when O4 ships` was not touched at all.** It is tempting to observe that its heading names a trigger that has passed, but its one surviving bullet is an open obligation and its clause is what licenses R3's `spec-004` edit. Pre-empting R3 here would have removed the license before the edit it authorizes. Flagged forward instead.

### Notes for Worker 3

- **The review question that matters here is the inverse of R1's.** R1's risk was over-cutting; R2's is **over-absorbing** — a reconciled sentence that is true of HEAD but is another spec's contract to state. The five rows to test are D8, D9, D12, D18, and D22: for each, read the spec's sentence and ask whether a reader would learn something that `spec-033` / `spec-035` / `spec-045` also says. The second risk is the opposite one: a claim rewritten into something *still* false, or false in a new way. `### Drift found beyond the floor` items 5 and 6 are the two newest assertions in the spec and the two most worth re-deriving from `optimizer/walker.py::_apply_hint` directly rather than from this report.
- **The rationale is the review instrument, and it now has two blocks.** `## Entries keyed to the spec` is R1's (what left the spec); `## Reconciliation pass — what the spec now says, and why` is R2's (what the survivors became). Every R2 entry names the spec section, the rejected alternative, and the claims the spec may no longer make, so each is checkable in one hop.
- **Five of the eight glossary anchors sat inside rewritten prose.** The per-anchor table above says which and how each was carried. Worth re-counting independently rather than trusting the green `check_spec_glossary`, which passes on one link as readily as on eight.
- **The heading rename is the one structural change**, and it touched a rationale link definition. Worth confirming that no in-page anchor anywhere resolves to `#current-state` and that the R1 entry is still lookup-able from its heading.
- **Every count in this report was produced by the command quoted beside it.** The byte table is the one place where two figures are *not* re-derivable — the post-R1 spec and rationale sizes, which exist only in R1's artifact because R1 is uncommitted. They are labelled as such in the table's own provenance column rather than presented as measurements.
- No temp tests and no `pytest` run. Nine shadow overviews were produced under `docs/shadow/` and read for their **Symbols** sections only; none is cited by line number anywhere.

### Notes for Worker 1 (spec reconciliation) — carried into R3

1. **`## Documentation updates when O4 ships` is R3's to close, and its end state is a decision R3 owes.** R2 left the section untouched. Once R3 discharges the `spec-004` rider, the section has zero open obligations and its heading names a trigger that passed twelve releases ago. Three dispositions exist — delete the section, keep it as a record of four discharged obligations, or fold a one-line "all documentation obligations discharged" statement into `## Definition of done` — and R3 should pick one deliberately rather than leaving an empty section behind. The rationale's `## Documentation updates when O4 ships` entry already records what discharged each of the other three, so deleting the section loses nothing that is not already written down.
2. **The `spec-004` rider edit is unchanged and still owed**, exactly as R1 recorded it. R2 verified only that the in-spec clause licensing it survives; it did not open `spec-004`.
3. **Two spec sections now point at sibling specs by filename**, which R3's cross-reference sweep will meet: `docs/SPECS/spec-033-connection_optimizer-0_0_9.md` (twice), `docs/SPECS/spec-035-optimizer_hardening-0_0_10.md` (once), `docs/SPECS/spec-045-visibility_boundary-0_0_14.md` (once). All four are code spans, not links, matching this spec's existing convention for `spec-002` / `spec-004`; all four files were disk-checked present. Three of them (`spec-033`, `spec-037`, `spec-041`…) sit in the concurrent renumber sweep's dirty set, so R3 must attribute any diff there by content before treating it as this cycle's.
4. **For the deferred-work catalog, two items, both unchanged in substance from R1's:**
   - the ordering invariant at the top of `### Same-query recursion` has **no automated guard** at HEAD — only `optimizer/walker.py::_record_relation_access`'s docstring and now the spec. Whether it earns a test is the maintainer's call and is out of scope for a documentation cycle;
   - a forward `ManyToManyField` appends a field name rather than a column to the parent's `only_fields` (hand-off item 8). Harmless — Django drops it from the compiled `SELECT` — deliberately undocumented in the spec, and recorded in the rationale's `## Standing notes`.
5. **One new catalog item.** `optimizer/plans.py::_prefetch_lookup_paths` recurses with no depth cap while its sibling `::runtime_path_from_path` is bounded at `_MAX_PATH_DEPTH = 1024`. The build plan already records this as a theoretical asymmetry only (the walker cannot construct a cyclic `Prefetch` graph). R2 re-read both and confirms the asymmetry is real and the reasoning holds; it is a maintainer note, not a finding, and it is deliberately **not** in the spec — a depth cap on a helper is `spec-035`'s vocabulary, not O4's.
6. **No sibling spec was made stale by an R2 edit**, as far as a read of the two inbound references shows: `spec-002` `## Purpose` delegates the O4 record to this spec, which is still true and now truer; `spec-004`'s B-slice riders are about O4's existence, not its wording. R3's sweep is the authority.

### Spec changes made (Worker 1 only)

Cited against the **post-R2** spec.

| Spec location | Change | Reason |
|---|---|---|
| `:3` | Extended the companion-pointer paragraph to name the reconciliation entries the rationale now also carries | The file gained a second entry block; a pointer that under-describes its target is a pointer a reader stops trusting |
| `:6-8` | `## Problem statement` rewritten: the slice's subject stated as contract; the two sentences describing the pre-O4 walker, its scalar-only helper, and its TODO anchor deleted | D1, D3 + hand-off item 2. Every clause of the second paragraph named deleted code; the prefix fact it carried is the only thing the `select_related` chain design rests on and was kept |
| `:11` | `## End-goal context` lead-in retensed from "have shipped or are designed around" to "are all built around" | The B-slices' relationship to `OptimizationPlan` is the contract; their ship status is not this spec's to track |
| `:14` | B7 bullet: `_optimizer_field_map` replaced by the property it protects (the field map is re-resolved per recursion level) | Beyond-floor drift 1 — the symbol has 0 occurrences package-wide; the property is live at `optimizer/walker.py::_walk_selections` → `::_resolve_field_map` |
| `:17` | B2/B3 bullet: "once nested paths exist" replaced by the reason nested paths make a bare name ambiguous; cross-reference corrected to the real heading | D-floor retense + beyond-floor drift 2 |
| `:18` | B8 bullet retensed from "Future … will normalize" to the present | D16 — B8 shipped (`optimizer/plans.py::diff_plan_for_queryset`, wired at `optimizer/extension.py #"# B8 pre-publish prune"`) |
| `:20` | `## Current state` renamed to `## Plan shape` | The heading itself was the falsified framing. See `### The heading rename` above; the rationale's entry records the rejected alternative |
| `:21-30` | Field inventory rebuilt: six bags O4 owns (adding `planned_resolver_keys`), plus one pointer sentence handing the other five to `spec-033` / `spec-035` | D5, D6. The rationale records why enumerating all eleven loses |
| `:25` | `only_fields` corrected from "root-query scalar paths" to queryset-relative | Beyond-floor drift 3 — the old wording contradicted `### Prefetch-boundary recursion`'s own rule |
| `:26` | `fk_id_elisions` restated as branch-sensitive resolver keys; the "O4 must migrate this bag" instruction deleted | D4 — the migration is delivered (`optimizer/plans.py::OptimizationPlan.fk_id_elisions`) |
| `:32` | The published planner signature replaced by the two contract facts it carried (empty Django prefix and empty runtime path at the root) | D2 — three later slices added keyword parameters, none of them this spec's |
| (deleted) | The `## Plan shape` sentence restating that nested single-valued relations land in `select_related` | Duplicated `### Same-query recursion`'s fourth bullet; a fact told twice inside one document goes stale in one of them |
| `:37` | `## Desired behavior` gained a lead-in qualifying all three query counts on the O6 downgrade | D20 — the counts are exact only where no type on the chain overrides `get_queryset`. The example project's own configuration is deliberately not named |
| `:64` | `## Implementation design` lead-in restated as the dispatch guarantee; the nested-connection third case named and handed to `spec-033` | D7/D10 + D12. A two-case sentence reads as a complete account of a dispatch that has three |
| `:67-72` | `### Same-query recursion` bullets: three "(already done)" parentheticals and the "replacing the current call" instruction removed; the scalar-only-step hazard folded into the recursion bullet | D1 + hand-off item 2 |
| (deleted) | The `_collect_scalar_only_fields` obsolescence paragraph | Rule 2 — every clause false; the symbol has 0 occurrences package-wide |
| `:80` | Child-queryset bullet: the direct `get_queryset` call replaced by the shared visibility boundary, with a pointer to `spec-045` and an explicit refusal to restate its rules | D8. Scope trap: pointer, not transplant |
| `:81` | `plan_relation` refactor instruction restated as its resulting contract (decides a kind, constructs nothing; one seam calls the hook exactly once) | D10 — `optimizer/walker.py::plan_relation` returns `tuple[str, str]` |
| `:85` | Connector reverse arm extended to reverse OneToOne | D9 — `optimizer/join_taxonomy.py::_parent_join_column`'s first arm is `one_to_many` **or** `reverse_one_to_one`. The rules are this spec's contract, so the arm is corrected in place rather than pointed elsewhere |
| `:89` | `Prefetch(full_path, …)` replaced by the instance-accessor rule, its Django reason, and its boundary | D11 — the one row where the shipped code corrected the spec (`optimizer/walker.py::_plan_prefetch_relation #"lookup_path = f\"{prefix}{instance_accessor(django_field)}\""`) |
| `:97-100` | `### Hints are leaf operations`: "the current walker already treats … preserve that" and the `_collect_scalar_only_fields` switch instruction removed; the leaf rule and a stronger parity statement kept | D1 + beyond-floor drift 9 |
| `:113` | `### Lookup-path flattening`: the "next to `OptimizationPlan`" position instruction and the direct private-attribute read both dropped | D17. The position contradicted the insertion-point section and is not contract; the single-reader discipline is `spec-035`'s to state |
| `:116-131` | `### Resolver sentinel keys` rewritten: the depth-1 leak restated as the standing argument for the key format; the runtime-path plurality made explicit with the prefix fan-out pointed at `spec-033`; the two-mirrored-implementations conclusion replaced by the one-shared-implementation contract; `_runtime_path_from_info` and the `_attach_relation_resolvers` signature dropped; the "small enough to land alongside O4" sequencing paragraph deleted | D13, D18 + beyond-floor drift 8. The key format itself is untouched — D13 confirms it shipped verbatim |
| `:135` | `### B1 plan cache`: the propagation re-attributed to the absorb step, with the reason it lives there | Beyond-floor drift 4 — `optimizer/walker.py::_absorb_child_plan` → `optimizer/plans.py::OptimizationPlan.merge_metadata_from` |
| `:138` | `### B3 strictness` retensed; "may separately stash" → "separately stashes" | Verified at `optimizer/extension.py #"DST_OPTIMIZER_LOOKUP_PATHS"` |
| `:143-146` | `### B4 optimizer hints`: `force_select`'s many-side rejection and O6 yield added; `force_prefetch` named as the second route into the prefetch branch; `prefetch(obj)`'s doc instruction dropped | Beyond-floor drift 5, 6, 9 + hand-off item 7 |
| `:149` | `### B2 FK-id elision`: "the same safety guards already in place" → "the same four safety guards the depth-1 elision holds" | Residual status language; the four guards themselves are confirmed at `optimizer/walker.py::_plan_select_relation #"if ("` |
| `:154` | `### B8 queryset diffing` retensed and narrowed to what B8 actually diffs against | D16 |
| `:160-189` | `## Test plan`: query-count rows moved to the live tier with the reason; the forward-FK count qualified and told to derive from a real run; both elision-leak axes named; two list-equality assertions restated as coverage; one build instruction restated as a property | D20 + beyond-floor drift 7. Every edited row re-checked against the tree (`### Test-plan rows re-checked against the tree`) |
| `:202` | `## Definition of done` bullet 2 rewritten without the deleted scalar-only helper | D1 |
| `:208` | `## Definition of done` bullet 8: the "with TODO-anchored pseudo-code findings left untouched" clause deleted | D15/D19 + hand-off item 1 — orphaned (its referent section is gone) as well as false (no such finding exists) |
| (deleted) | `` ## Missing `.py` files `` in full | D22 + hand-off item 3. Discharged build guidance, false as a present-tense map, and its one durable fact constrains nobody. Both rejected alternatives recorded in the rationale |

**No spec status/header line needed a `worker-1.md` `## Spec status-line re-verification` edit.** Spec-003 carries no `Status:` / owner / target-release header block; its lines 1-4 are the title and R1's companion-pointer paragraph, re-checked against the read-only HEAD copy at the start of this pass. The pointer paragraph *was* edited, but for coverage of the rationale's new content, not for a falsified status.

**Rationale changes (same custodian, same pass).** `worker-1.md` rule 4 makes the file append-only during the build, so R1's entries stand:

| Rationale location | Change | Reason |
|---|---|---|
| appended before the link block | `## Reconciliation pass — what the spec now says, and why` — 19 entries keyed to spec sections, each carrying *Changed* / *Alternative rejected* / *Claims the spec no longer makes*, plus a closing "what this pass deliberately did not change" | `BUILD.md` `## Spec rationale extraction`: the spec never narrates its own history, and the rationale is keyed to the spec so it works as a review instrument. This is the maintainer's instruction that the explanation of each change goes in the rationale, never in the spec |
| `[spec-003-current]` definition | Target re-pointed from `#current-state` to `#plan-shape` | Mechanical repair of the anchor the heading rename moved; leaving it would break the rule the rename otherwise serves |
| the R1 `## Current state` entry's `Spec:` line | Amended to name the surviving heading and point at the reconciliation entry that explains the rename | Same rule — an entry that cannot be looked up from its spec section is worthless however well argued. The entry's own heading and body are untouched |
| `<!-- Root -->` group | Added `[agents]: ../../../AGENTS.md` | Two reconciliation entries cite `AGENTS.md`'s live-first testing rule; the definition target was disk-checked |
| `<!-- docs/SPECS/ -->` group | Added `[spec-018]: ../spec-018-meta_primary-0_0_6.md` | The scope-line paragraph names all four later specs that extended this subject matter; alphabetical within the group; target disk-checked |

---

### Addendum: the concurrent session COMMITTED mid-pass, and the plan's baseline-dirty list is now stale in both directions

`git status --short` at the moment every measurement above was taken carried this cycle's three paths plus the fourteen files the build plan's `## Baseline-dirty out-of-scope files` lists. On the final check it carried this instead:

```text
 M docs/SPECS/NEXT.md
 M docs/SPECS/spec-003-optimizer_nested_prefetch_chains-0_0_2.md
 M docs/builder/BUILD.md
```

The concurrent session **committed** at `1f4b3265` ("docs: refresh the standing docs against the shipped 0.0.14 surface"), which is `HEAD` now and was not when this pass opened. Its 17 files are exactly the plan's baseline-dirty list — `CHANGELOG.md`, `GOAL.md`, `README.md`, `TODAY.md`, `docs/README.md`, the seven archived specs, both example files, `examples/fakeshop/db.sqlite3`, `KANBAN.md`, `KANBAN.html` — so all fourteen are now **clean**, and the same session has since opened two **new** dirty files this pass never touched: `docs/SPECS/NEXT.md` and `docs/builder/BUILD.md`.

**Not touched, not reverted, not `git checkout`-ed** (`AGENTS.md` rule 34, `START.md` "Concurrent sessions"). Per the plan's own instruction the list is Worker 0's to append, not a worker's to edit; recorded here so it reaches Worker 3 and R3 rather than being re-derived.

**This pass's work survived the commit, verified rather than assumed** (`docs/builder/worker-memory/worker-1.md` carries the precedent: a concurrent commit can adopt an uncommitted change):

- `git show --name-only --format= 1f4b3265 | grep -c spec-003` → **0**. Neither the spec nor the new rationale is in that commit.
- `git diff --stat` on the spec is still exactly `78 insertions(+), 285 deletions(-)`; `wc -lc` is still 240 / 27,864 and 925 / 63,778. Nothing above rests on a pre-commit reading.
- Both DB-backed checks re-run green **after** the commit landed: `check_spec_glossary.py --spec …` → `OK: 8 terms - all have glossary entries and at least one spec link.` exit 0, and `import_spec_terms --check` → `OK: 49 done cards have glossary links.` exit 0. Card 3's glossary chain is intact across the concurrent kanban write **and** its commit.

**Two consequences for the passes after this one.**

1. **`docs/builder/BUILD.md` is dirty with an uncommitted edit to a standing workflow doc.** Read at the point of writing this: it corrects the filename-pattern example (`build-013-` → `build-017-`) and moves the floor-verification policy version from Django `5.2.0` to `5.2.16`. Neither touches R2 or R3 — this cycle's floor-verification scope is `none` and spec-003's naming is unaffected — but a later pass reading `BUILD.md` will see a version this artifact does not, and the final gate should read the file rather than a number quoted anywhere.
2. **The renumber sweep's one touch on a file this pass read is confirmed inert.** `git show -U0 1f4b3265 -- examples/fakeshop/test_query/test_products_api.py` is a **single comment line** (`TODO-BETA-053-0.1.5` → `TODO-BETA-060-0.1.5`) at a point unrelated to the O4 rows. Both O4 live tests still pin `assert len(captured) == 3` — the reverse-FK chain and the forward-FK chain — so the `## Test plan` and `## Desired behavior` edits above are unaffected. R3 must still attribute any `docs/SPECS/` diff by content before treating it as this cycle's, but the seven archived specs are now clean, so the ambiguity the plan warned about has narrowed to `docs/SPECS/NEXT.md`.

---

## Review (Worker 3)

Read-only pass over the working-tree diff of `docs/SPECS/spec-003-optimizer_nested_prefetch_chains-0_0_2.md` against `HEAD` (`1f4b3265`) plus the appended `## Reconciliation pass` block of the untracked rationale. No `git stash` / `checkout` / `restore` / `worktree` at any point; the HEAD reference was obtained read-only with `git show HEAD:<path>` into a scratch path outside the repository. No `pytest`, no `--cov*` flag, no source or test edit.

### High:

None.

### Medium:

#### M1 — `## Plan shape` states an empty runtime response path at the root; HEAD's is the root field's response key

`docs/SPECS/spec-003-optimizer_nested_prefetch_chains-0_0_2.md:32`

> Planning starts from the root selection set with an empty Django lookup prefix and an empty runtime response path; every nested walk extends both.

This sentence is one of the **two contract facts** the pass says it kept when it dropped the published planner signature (`### Verification of the 22-row drift floor` row D2, `### Spec changes made` `:32`). The Django half is right; the runtime half is not.

`optimizer/walker.py::plan_optimizations` omits `prefix` (so `""`) but passes

```
runtime_prefixes=(runtime_prefixes if runtime_prefixes is not None else (runtime_path_from_info(info),))
```

and `optimizer/plans.py::runtime_path_from_info` → `::runtime_path_from_path` **includes the current node's key**, walking `path.prev` to the root. At the root resolver `info.path` is the root field's own path, so the root runtime prefix is `("allEntries",)`, not `()`. The empty tuple is only `_walk_selections`'s `runtime_prefixes=((),)` default, which its own docstring scopes to "direct or test-only callers without `info`" — and `plan_optimizations` is explicitly excluded there ("`plan_optimizations` always passes an explicit single-tuple").

Why it matters rather than being a nit: this section's own `### Resolver sentinel keys` makes the walker/resolver agreement load-bearing ("The walker side must use the same response-key convention", `:127`). The resolver side reconstructs `("allEntries", "item")` from `info.path`; a walker built from `:32` as written would emit `EntryType.item@item` against a resolver asking for `EntryType.item@allEntries.item`, and every elision and strictness key would silently miss. The spec is the only place that states this protocol.

**Recommended change.** State the fact that actually holds — planning starts at an empty Django lookup prefix and at the runtime response path of the root field being planned (empty only when no `info` is available) — or drop the runtime half of the clause and leave it to `### Resolver sentinel keys`, which already says the walker threads the runtime path "alongside the Django `prefix`".

#### M2 — `## Desired behavior`'s new lead-in says the plan shapes are unchanged under an O6 downgrade; they are not

`docs/SPECS/spec-003-optimizer_nested_prefetch_chains-0_0_2.md:37`

> A type that does is downgraded to a `Prefetch` by O6, which turns a same-query join into its own round trip; the plan shapes are unchanged, the counts are not.

Each of the three worked examples below it carries a line literally labelled **`Plan shape:`**, and the depth-3 one reads "root `select_related` includes the nested path". Under the O6 downgrade the lead-in is describing, that is exactly what stops being true — the same clause concedes it ("turns a same-query join into its own round trip"), so the sentence contradicts itself in eleven words.

The evidence the pass itself cites says so outright. `examples/fakeshop/test_query/test_products_api.py::test_products_optimizer_selects_nested_forward_fk_depth_2_over_http`:

```examples/fakeshop/test_query/test_products_api.py
Before spec-034 this query planned a single `select_related(
"item__category")` JOIN. With the cascade hooks active, `ItemType` and
`CategoryType` both define a custom `get_queryset`, so the optimizer
downgrades each forward FK in the `item -> category` chain to a windowed
`Prefetch` ...
```

So both the count **and** the plan shape change. The rationale entry (`### \`## Desired behavior\``) states the true intent — "Nothing about O4 changed — the optimizer plans what it always planned" — i.e. O4's *dispatch* is unchanged, not the plan shapes the section tabulates.

**Recommended change.** Qualify what is actually invariant: the dispatch rule is unchanged; a downgraded link moves from the `select_related` chain into its own `Prefetch`, so both the shape and the count shift for that link. Any wording is fine that does not tell a reader the `Plan shape:` bullets survive the downgrade.

#### M3 — two `### Dispatched findings checklist` boxes are ticked against a rationale that does not carry those fields

`docs/builder/bld-003-r2-spec_reconciliation.md:76-77`

> - [x] Every rationale entry records the rejected alternative and the one-line reason it lost.
> - [x] Every rationale entry records the claims the spec may no longer make.

Measured per entry across the 14 entries of `## Reconciliation pass` (closing subsection excluded):

```
ALT-YES CLAIMS-YES  `## Problem statement`
ALT-NO  CLAIMS-YES  `## End-goal context`
ALT-YES CLAIMS-YES  `## Plan shape` (was `## Current state`)
ALT-YES CLAIMS-NO   `## Desired behavior`
ALT-NO  CLAIMS-YES  `### Same-query recursion for single-valued paths`
ALT-YES CLAIMS-YES  `### Prefetch-boundary recursion ...`
ALT-NO  CLAIMS-YES  `### Hints are leaf operations` and `### B4 optimizer hints`
ALT-YES CLAIMS-YES  `### Lookup-path flattening`
ALT-YES CLAIMS-YES  `### Resolver sentinel keys`
ALT-NO  CLAIMS-NO   `### B1 plan cache`
ALT-NO  CLAIMS-NO   `### B8 queryset diffing`
ALT-NO  CLAIMS-NO   `## Test plan`
ALT-YES CLAIMS-YES  `## Definition of done`
ALT-YES CLAIMS-YES  The former `` ## Missing `.py` files ``
```

**6 of 14** carry no *Alternative rejected*; **4 of 14** carry no *Claims the spec no longer makes*. The same over-statement is repeated in `### Spec changes made (Worker 1 only)`'s rationale table ("19 entries … each carrying *Changed* / *Alternative rejected* / *Claims the spec no longer makes*") and in `### Notes for Worker 3` ("Every R2 entry names the spec section, the rejected alternative, and the claims the spec may no longer make, so each is checkable in one hop").

Two of the gaps are substantively owed rather than vacuous: `## Test plan` no longer claims the two query-count rows live in `tests/optimizer/test_extension.py`, nor that `select_related` compares equal to a list; `### B1 plan cache` no longer claims the propagation lives in `_walk_selections`'s prefetch branch. Those are exactly the "claims the decision once made and may no longer make" `BUILD.md` `## Spec rationale extraction` asks for, and they are the entries where the field is missing.

**Recommended change.** Either add the missing fields where a real alternative or retired claim exists (at minimum `## Test plan` and `### B1 plan cache`), or restate both boxes and both prose claims as what holds — "every entry that weighed an alternative records it" — so the artifact stops asserting a universal it does not meet. `BUILD.md` `## Claims are proven mechanically`: an unqualified universal reads as measured.

### Low:

#### L1 — `## End-goal context`'s retense converted a disjunction into a universal that is false for B6

`docs/SPECS/spec-003-optimizer_nested_prefetch_chains-0_0_2.md:11`

HEAD-before read "B1 … and B6 [schema audit] **have shipped or are designed around** the current `OptimizationPlan` shape"; the rewrite reads "… **are all built around** the `OptimizationPlan` shape". Dropping the disjunct makes the sentence assert of *every* B-slice that it is built around `OptimizationPlan`. `optimizer/extension.py::DjangoOptimizerExtension.check_schema` (B6) never touches a plan: it walks `registry.iter_types()`, the registered definition's `field_map`, and `optimizer_hints`, and returns warning strings. B7 field metadata (`optimizer/field_meta.py::FieldMeta`) is likewise upstream of the plan rather than built around it.

No rationale entry covers this change — `### \`## End-goal context\`` records the B7 symbol drop, the B8 retense, and the cross-reference repair, but not the lead-in's quantifier — so nothing else in the corpus would catch it. Recommended: restore a hedge that is true of all seven (e.g. "are all built on the optimizer's plan-based contract" / "must keep working across it") or name the subset.

#### L2 — stated count: "three surviving backward-looking sentences"; six survive

`docs/builder/bld-003-r2-spec_reconciliation.md:259`. `grep -n 'rationale file\]\[spec-003-rationale\]'` over the post-R2 spec returns **seven** lines: the companion paragraph at `:3` plus per-section pointers at `:32`, `:74`, `:95`, `:113`, `:125`, `:196` — all six of the per-section pointers are backward-looking in exactly the way the bullet describes ("was proposed in", "this section quoted", "already discharged"). `docs/builder/bld-003-r1-rationale_move.md:319` and `:691` independently count **six** per-section pointers plus the companion, and R2 deleted none. Third consecutive pass in which a count stated in narrative prose (rather than in `### Validation run`) is wrong.

#### L3 — stated count: "19 entries" in the appended rationale section; 15 `###` headings exist

`docs/builder/bld-003-r2-spec_reconciliation.md:332`. `awk 'NR>=476' <rationale> | grep -c '^### '` → **15**: 14 entries keyed to spec sections plus `### What this pass deliberately did not change`, which the same sentence describes separately ("plus a closing …"). 15 + the closing's 4 bullets = 19, which is probably where the number came from, but it is not what the sentence says.

#### L4 — the `## Plan shape` pointer narrates the section's own former content

`docs/SPECS/spec-003-optimizer_nested_prefetch_chains-0_0_2.md:32`, final clause:

> The pre-O4 dispatch block this section quoted is described in the [rationale file][spec-003-rationale].

Read cold, "this section quoted" has no referent: `## Plan shape` quotes nothing and is not named "Current state" any more. Of the six per-section pointers this is the only one whose subject is the spec's own past *content* rather than the design it once proposed, and it is in the section R2 both renamed and rewrote — so it is R2's to land cleanly even though R1 wrote it. The other five ("The shape this branch was proposed in …") read as ordinary companion pointers and need nothing.

Recommended: name the thing rather than the section's history — e.g. "The pre-O4 dispatch shape, and where the shipped walker departed from it, are in the rationale file" — which also matches the rationale entry's own heading.

#### L5 — pre-existing at HEAD: `glossary-optimizerhint`'s only body link sits inside a code span

`docs/SPECS/spec-003-optimizer_nested_prefetch_chains-0_0_2.md:98` opens `` `[OptimizerHint][glossary-optimizerhint].prefetch(obj)` `` — the reference is *inside* the backticks, so it renders as literal text and never becomes a link. Verified pre-existing read-only: `git show HEAD:<spec>` carries the identical shape at its line 188, so **R2 did not introduce it** and the paragraph rewrite preserved it character-for-character exactly as the artifact claims.

It is recorded because of the 8-anchor constraint, not for rendering: `optimizerhint` is a single-carrier anchor, and `scripts/check_spec_glossary.py` counts it because it does not strip code spans. A link-checker that ever does strip them drops the anchor and breaks card 3's `import_spec_terms` chain. Not this cycle's to fix (it is a content change outside reconciliation, in a paragraph whose link R2 was told not to move) — routed to the deferred-work catalog below.

### DRY findings

- **Spec-versus-rationale separation holds.** Spot-checked the five most-transplantable spots (`:80` visibility boundary, `:30` plan-field pointer, `:64` connection third case, `:123` prefix fan-out, `:113` single-reader rule): each states O4's own obligation and names the owning spec without restating its rules. No contract text appears on both sides of the split.
- **The one intra-spec duplication removed is real.** `## Plan shape` no longer restates that nested single-valued relations land in `select_related`; `### Same-query recursion`'s third bullet is the single carrier. Confirmed the fact survives exactly once.
- **New cross-file duplication introduced: none.** `grep` for the four sibling-spec filenames in the spec returns four code-span mentions, no transplanted paragraphs.
- **Existence challenge:** none raised. R2 adds no abstraction; the one deletion (`` ## Missing `.py` files ``) is itself the scope-narrowing move, and it is argued in the rationale with both rejected alternatives rather than performed silently.

### Verification I performed independently

Everything below was re-derived from source or by command, not accepted from the report.

**The three substantive beyond-floor claims (the ones the task named).** All three confirmed:

- `_optimizer_field_map` — `grep -rn 'optimizer_field_map' django_strawberry_framework/` → **0**. `optimizer/walker.py::_walk_selections` opens with `_resolve_field_map(model, source_type=source_type)`, resolving the map for the model being descended into, so the property `:14` now states is live and correctly stated. (The three `tests/optimizer/test_field_meta.py::test_optimizer_field_map_*` names are historical test naming, not package symbols; `KANBAN.md:240` already owns them for card 052.)
- `cacheable` propagation — `optimizer/walker.py::_absorb_child_plan` → `optimizer/plans.py::OptimizationPlan.merge_metadata_from #"if not other.cacheable:"`, whose docstring carries the reason `:135` now states ("so a future third site cannot forget it"). The old attribution to the prefetch branch was wrong; the new one is right.
- `force_select` — `optimizer/walker.py::_apply_hint` raises `ConfigurationError` for `is_many_side_relation_kind(kind)` ("Django requires prefetch_related for {kind} relations"), and dispatches the single-valued case with `prefer_prefetch=_target_has_custom_get_queryset(target_type)`. Both new `:144` clauses are exact.

**Sampled across the whole spec** (`BUILD.md` `## Claims are proven mechanically`; every rewritten present-tense sentence in `### Spec changes made` was read against the symbol it names):

| Spec line | Claim | Verified at |
|---|---|---|
| `:21-30` | six bags O4 owns; five further fields belong elsewhere | `fields(OptimizationPlan)` = **11** (6 + 2 path maps + 3 `finalized_*`); 3 `ClassVar` partitions excluded correctly |
| `:64` | one dispatcher, three deciders; connection is a third case recognized first | `walker.py::_dispatch_single_relation` docstring names the three; the connection route is `_walk_selections #"resolved[0] == \"connection\""` at walker.py:495, **before** the relation dispatch at :631 |
| `:70` | FK-column append must precede the elision short-circuit | `::_record_relation_access` is the first statement of `::_plan_select_relation`; its docstring states the invariant; no automated guard (as recorded) |
| `:80` | hook routed through the shared visibility boundary | `::_build_child_queryset` → `utils/querysets.py::apply_type_visibility_sync(..., allow_sliced=True)`; base is `related_model._default_manager.all()` |
| `:81` | `plan_relation` decides a kind, constructs nothing | `walker.py::plan_relation` → `tuple[str, str]`, three returns, no queryset |
| `:84-87` | empty-`only_fields` short-circuit + three connector arms | `walker.py::_ensure_connector_only_fields #"if not plan.only_fields:"`; `join_taxonomy.py::_parent_join_column` arms match all three |
| `:85` | reverse arm covers reverse OneToOne | `_parent_join_column #"or kind == \"reverse_one_to_one\""` |
| `:89` | lookup segment is the instance accessor | `::_plan_prefetch_relation #"lookup_path = f\"{prefix}{instance_accessor(django_field)}\""` + docstring, including the "only the lookup string Django consumes" boundary |
| `:91` | `cacheable` set before the child build | `if has_custom_get_queryset: plan.cacheable = False` precedes `_build_prefetch_child_queryset` |
| `:113` | flattening helper lives in `plans.py`, returns the union | `plans.py::lookup_paths` → `::_lookup_paths_from_parts` → `::_prefetch_lookup_paths` |
| `:118` | resolver closure knows its parent type | `types/resolvers.py:236` / `:393` call `resolver_key(parent_type, …)` |
| `:123` | one resolver identity per response key | `walker.py::_resolver_identities_for` — cartesian product over prefixes × `_response_keys(sel)` |
| `:131` | ONE shared implementation both sides import | `types/resolvers.py:48 from ..optimizer.plans import resolver_key, runtime_path_from_info`; `walker.py:31-36` imports the same |
| `:138` | extension stashes keys and lookup paths separately | `extension.py:1217-1218` — `DST_OPTIMIZER_PLANNED` and `DST_OPTIMIZER_LOOKUP_PATHS` |
| `:145` | `force_prefetch` is a second route into the branch | `_apply_hint` dispatches `prefer_prefetch=True` |
| `:149` | four B2 guards | `::_plan_select_relation #"if ("` — `_can_elide_fk_id`, no custom `get_queryset`, no custom id resolver, `_selected_scalar_names(...) == {target_pk_name}` |
| `:179-180` | live query counts | `test_products_api.py` — reverse-FK pins `assert len(captured) == 3`; forward-FK pins 3 with the O6 reason in its docstring |
| `:154` | B8 diffs against the consumer's queryset | `plans.py::diff_plan_for_queryset`, `::prune_unsupportable_select_related` |

Two of those readings produced M1 and M2. Everything else in the table matched.

**The rescued R1 rule survived byte-identically.** Reconstructed R1's pass-3 end state from `docs/builder/bld-003-r1-rationale_move.md:852` (the untouched instruction half) + `:846` (the blockquoted replacement scope sentences, `> ` stripped), wrote it to a scratch path outside the repo, and `diff`ed against `sed -n '79p'` of the working tree: **identical, 778 bytes both sides**. The bullet moved from `:78` to `:79` (one line added above it) and changed in no other way.

**The 8-anchor constraint, re-counted per anchor rather than from the green exit.** A script that strips the definition block and counts `][ref-id]` uses in the body returns exactly **one body use for each of the eight** (`djangotype`, `fk-id-elision`, `metaoptimizer_hints`, `only-projection`, `optimizerhint`, `plan-cache`, `queryset-diffing`, `schema-audit`); zero undefined references, zero definitions whose on-disk target is missing. `docs/SPECS/appx/spec-003-…-terms.csv` is **9 lines / not in `git status`** — never opened, as claimed.

**Stated counts re-derived.** `wc -lc` → spec **240 / 27,864**, rationale **925 / 63,778** (both exact). `git diff --stat` → **78 insertions(+), 285 deletions(-)** (exact). Spec headings **21**, duplicate slugs **0** (exact). Rationale anchor-bearing definitions **9**, used **10** times, **all 9 resolving** against real post-R2 spec headings including the repaired `#plan-shape` (exact). Rationale link scaffold **19 / 19** (exact). Fences in the spec: **0** (exact). `grep -nE '[a-zA-Z_/]+\.(py|md):[0-9]+'` on both files → no match (exact). All twelve dead private-helper names plus `TODO(spec-003` → **0 occurrences each** in the spec (exact, re-run individually). The four rows the build plan had spot-checked (D1, D2, D11, D14-ii) re-derived here a third time and match. Of the counts I could re-derive, the wrong ones are L2 and L3; the two post-R1 byte figures are correctly labelled non-re-derivable.

**Validation commands re-run by me, not read from the report:**

```
uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-003-…md
  → OK: 8 terms - all have glossary entries and at least one spec link.   exit 0
uv run python scripts/check_trailing_commas.py --check <spec> <rationale> <this artifact>
  → exit 0
uv run python examples/fakeshop/manage.py import_spec_terms --check
  → OK: 49 done cards have glossary links.                                exit 0
git diff --stat -- django_strawberry_framework/ tests/ examples/
  → empty (the no-source claim confirmed, not assumed)
```

**The section rename leaves nothing dangling.** `grep -rn 'spec-003-optimizer_nested_prefetch_chains-0_0_2.md#'` repo-wide returns hits only in the rationale's nine definitions, all repointed or unaffected. `grep -rn '#current-state' --include='*.md'` returns only `spec-035` and `spec-031` in-page anchors into their *own* documents. `docs/GLOSSARY.md`, `KANBAN.md`, `docs/README.md`, and the two sibling specs carry no anchor into spec-003 at all.

**The deletion lost nothing normative.** `` ## Missing `.py` files `` was "None. Every O4 change lands in an existing module … No new subpackage or Python module needs to be created for O4." — an answer to a build question, with no inbound reference anywhere (`grep -rn 'Missing .py files' --include='*.md'` → nothing outside this cycle's own artifacts). The four modules the rationale names as the surface's growth (`nested_planner.py`, `selections.py`, `join_taxonomy.py`, `nested_fetch.py`) all exist. Deletion is the right disposition and both rejected alternatives are recorded.

**The scope trap held on all five named rows.** D8 → one clause plus a `spec-045` pointer with an explicit refusal to restate; D12 → one clause naming the third case and handing it to `spec-033`; D18 → split correctly (the response-key plurality is genuinely O4's — `_resolver_identities_for`'s product is over prefixes × response keys, and the merge that creates multiple response keys is O4's `_merge_aliased_selections` concern; the prefix axis is one parenthesis); D22 → deleted. **D9, the one corrected in place, is the right call**: `_parent_join_column`'s three arms are the same three rules this spec authored, and only their file moved — publishing where they now live would have been the transplant, and the pass correctly does not.

**The eight R1 hand-off items are each dispositioned.** Items 1, 2, 3, 5, 6, 7 verified closed against the spec text (2 and 5 re-derived above). Item 4 (the `spec-004` rider) is correctly left standing — the in-spec clause at `:194` is what licenses R3's sibling edit, and pre-empting it would remove the licence before the edit. **Item 8 — silence in the spec is right.** The forward-M2M `attname` artifact is real, but it is a property of Django's field API surfacing in a guard, not a contract this spec sets; documenting it would freeze an implementation artifact as spec text and would invite exactly the narrowing of the guard that R1's pass-3 correction removed. Recorded in the rationale's `## Standing notes` and carried to the catalog, which is the right home.

**No boundaries, so no failability proofs are owed.** `git diff -- django_strawberry_framework/` is empty; the diff introduces no guard, gate, or rejection path. My mandatory re-run floor (`worker-3.md` "Reading is necessary, not sufficient") is therefore satisfied by an **empty re-run set, which is legal only in this case** — the diff introduces no boundary that meets the floor. Boundaries re-run: none. Boundaries accepted on the performer's record: none exist.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` → empty. `__all__` and the re-export list are unchanged. No new public export.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md. (`CHANGELOG.md` is clean at HEAD `1f4b3265` and closed to this cycle by `AGENTS.md` rule 21.)

### Documentation / release sanity

Applicable — the item's whole diff is documentation.

- No version string, shipped/planned status, or card ID was touched; the spec carries no `Status:` header block, correctly noted.
- No KANBAN card moved; `examples/fakeshop/db.sqlite3`, `KANBAN.md`, `KANBAN.html`, and `docs/GLOSSARY.md` are all clean at the end of this pass and carry nothing from R2.
- Every markdown link introduced or moved points at an existing file: 10/10 spec definitions and 19/19 rationale definitions disk-checked, including the four sibling-spec filenames added as code spans (`spec-033`, `spec-035`, `spec-045`, `spec-018` — all present under `docs/SPECS/`).
- The reference-style convention holds: no inline `](path)` link in either file, `<!-- LINK DEFINITIONS -->` present with all 10 canonical group headers in order, alphabetical within group (`check_trailing_commas --check` exit 0 confirms the scaffold mechanically).
- No script-rendered doc was regenerated by this pass, so the docstring-staging check does not apply.
- No obsolete "coming soon"/"planned" wording survives in the sections the pass deliberately updated; the status-language sweep the report describes was independently spot-checked at `:11`, `:37`, `:138`, `:149`, `:154` and the residues are gone. The one deliberate survivor is `## Documentation updates when O4 ships`'s open rider, correctly reserved to R3.

### What looks solid

- **The reconciliation is right far more often than not.** Roughly thirty rewritten present-tense claims were checked against the symbol each names; two are wrong (M1, M2) and one is over-quantified (L1). The three substantive beyond-floor discoveries are all genuine and all correctly stated in the spec — the `_optimizer_field_map` property/symbol separation in particular is the right instinct: it kept the load-bearing invariant and dropped the name that rots.
- **D11 is handled better than the drift table asked for.** The bullet states the rule, Django's reason, *and* the rule's boundary (only the string Django consumes uses the accessor). That last clause is not in the drift table and is the clause that stops a reader corrupting resolver keys — it was clearly written from `::_plan_prefetch_relation`'s docstring and body rather than from the summary.
- **The scope line held under real pressure.** D5 was the strongest pull and the argument recorded against it (two independent grounds, one of which is the symbol-map liability the rationale had already established for the deleted insertion-point section) is the kind of reasoning that survives being re-litigated.
- **Deleting a section was argued, not performed.** Both rejected alternatives for `` ## Missing `.py` files `` are on record, so the next reader cannot conclude it was dropped for convenience.
- **The rescued R1 rule is untouched to the byte**, and the pass says so with a check a reviewer can repeat rather than a prose assurance.
- **The concurrent-commit addendum is exemplary.** It proves the pass's work survived `1f4b3265` by `git show --name-only`, re-runs both DB-backed checks *after* the commit, and re-attributes the baseline-dirty list without editing the plan — precisely the standing hazard, discharged the standing way.

### Temp test verification

None created. This item introduces no boundary and changes no code path, so there was nothing a temp test could demonstrate that reading the source and running the four validation commands did not. `docs/builder/temp-tests/r2/` was not created.

### Static helper use

`scripts/review_inspect.py` was **not** re-run by this pass. `BUILD.md` `### When to run the helper during build` triggers Worker 3 on a slice that adds a `.py` file, touches `optimizer/` or `types/`, or adds 30+/50+ lines of logic — this diff does none of those (`git diff -- django_strawberry_framework/ tests/ examples/` is empty), so no trigger fires. The skip is recorded here with that reason. The nine shadow overviews the performing pass produced under `docs/shadow/` were not read or cited; every source reference above is symbol-qualified and was read from the original files.

### Notes for Worker 1 (spec reconciliation)

1. **M1 and M2 are spec-text corrections, both inside Worker 1's exclusive custody.** Neither needs a design decision; both need the sentence to say what the source says. M1 is the higher-value one because it is the only place the corpus states the walker/resolver key-path convention.
2. **M3 is an artifact correction, not a spec one.** The rationale content is good; the claim about it is over-quantified. Fixing the boxes and the two prose restatements is enough, though `## Test plan` and `### B1 plan cache` would both genuinely benefit from a *Claims the spec no longer makes* line.
3. **Carried into R3 — `KANBAN.md` card `TODO-ALPHA-052-0.1.0` is now partly discharged by R2, and its prescribed replacement disagrees with what R2 did.** `KANBAN.md:317` names four stale spec-003 sites; R2 closed three (`:4` remaining-O-slice, `:27` planner arity + `_collect_scalar_only_fields`, and `:333`'s `## Current state` referent, whose section R1 already cut). `KANBAN.md:240`'s second instance (`_collect_scalar_only_fields` at `spec-003:27`) is likewise closed. But `:317` also states the intended replacement as "the replacement states that O4 is shipped and that its record is this spec's" — and R2 deliberately rejected retensing to "O4 shipped at `0.0.2`" (rationale `### \`## Problem statement\``, first rejected alternative). R3 should surface the divergence to the maintainer rather than reconcile it silently, and the build plan's default ("a discharged scope item is card 052's") still governs who retires the prose.
4. **For the deferred-work catalog, one new item beyond the three the pass already lists:** the `glossary-optimizerhint` reference at `spec-003:98` sits inside a code span and therefore never renders as a link (L5, pre-existing at HEAD). It is that anchor's only carrier. `scripts/check_spec_glossary.py` passes because it does not strip code spans; a checker that ever does would drop the anchor and break card 3's `import_spec_terms` chain. Worth a maintainer decision on whether the checker should strip code spans, which is a package-wide question and not this cycle's.
5. **No sibling spec was made stale by an R2 edit**, independently confirmed: `spec-002` `## Purpose` still delegates the O4 record here, and `spec-004`'s B-slice riders are about O4's existence rather than its wording. R3's sweep remains the authority.
6. **Concurrent-session state at the close of this pass is unchanged from the addendum's**: `git status --short` shows ` M docs/SPECS/NEXT.md`, ` M docs/SPECS/spec-003-…md`, ` M docs/builder/BUILD.md`, plus this cycle's four untracked files. The spec's diff is still exactly 78/285 and its `wc -lc` still 240/27,864, so nothing above rests on a stale reading. Nothing was edited or reverted; `docs/builder/BUILD.md` was read at its current edited content, which is correct.

### Review outcome

`revision-needed` — three Medium findings (two rewritten sentences that are false about HEAD, one over-ticked checklist pair) and five Low findings, none of them yet addressed or rejected with a recorded reason.

The item is close. The reconciliation itself is sound: all 22 drift rows re-verified true, the nine beyond-floor discoveries genuine and correctly stated, the scope trap held on every row it was set for, the rescued R1 rule byte-identical, all eight glossary anchors carrying exactly one link with the CSV never opened, and no source or test touched. What sank the pass is the failure mode with no other detector — a reconciliation writes many new present-tense sentences, and two of them (`:32`'s empty root runtime path, `:37`'s "the plan shapes are unchanged") state the opposite of what `optimizer/walker.py` and the pass's own cited live test do.

Per the build plan's Deviation 2 corollary, the apply-changes pass is Worker 1's and returns the artifact to `planned`.


#### Addendum to note 6 — the concurrent session committed again while this review was being written

`HEAD` moved a second time, from `1f4b3265` to **`4d1c512a`** ("docs(workflow): correct the drifted identifiers in the build and spec flows"), between the start and the end of this pass. Its only file is `docs/builder/BUILD.md` (5 insertions / 5 deletions), so `docs/SPECS/NEXT.md` and `docs/builder/BUILD.md` are now **clean** and the baseline-dirty list is empty again. Verified rather than assumed:

- `git log --stat 1f4b3265..HEAD -- <spec> docs/SPECS/appx docs/builder` shows `4d1c512a` touching only `docs/builder/BUILD.md` — none of this cycle's four paths was swept into it.
- The spec's diff is still exactly `78 insertions(+), 285 deletions(-)` against the new `HEAD`, so every measurement in this review stands unchanged.
- `git status --short` now carries only this cycle's own files: ` M <spec>` plus the four untracked (`rationale`, the two `bld-003-*` artifacts, the plan).

Nothing was edited or reverted. Worker 0 owns appending this to the plan's `## Baseline-dirty out-of-scope files`, not a worker. **Consequence for the passes after this one:** `docs/builder/BUILD.md` is no longer dirty, so a later pass reads it at `4d1c512a` rather than at the uncommitted edit the reconciliation report described — the floor-verification numbers are now committed, and this cycle's floor scope is `none` either way.

---

## Reconciliation report (Worker 1, pass 2)

Apply-changes pass on Worker 3's `revision-needed`: three Mediums and five Lows. Per the build plan's Deviation 2 corollary this pass is Worker 1's — R2 has no Worker 2 — so it appends here rather than as a build report, and returns `Status: planned` for a Worker 3 re-review.

**Prior sections are not edited.** Where a figure in `## Reconciliation report (Worker 1)` is wrong it is superseded below (`docs/builder/ARTIFACT.md` `## Re-pass sections`), never corrected in place. The two exceptions are both mandated rather than chosen: the `### Dispatched findings checklist` boxes, whose tick-and-restate discipline `ARTIFACT.md` assigns to exactly this pass, and the rationale file, which is a durable companion edited where it stands (rule 4's append-only protects a *later round* from overwriting settled entries, not this item from fixing its own — the R1 precedent).

### Disposition of all eight findings

| # | Finding | Disposition |
|---|---|---|
| M1 | `spec:32`'s "an empty runtime response path" is false | **Fixed in the spec**, with the reason it matters stated. Rationale entry extended. |
| M2 | `spec:37` says the plan shapes are unchanged under an O6 downgrade | **Fixed in the spec.** The lead-in now qualifies count *and* shape and names what is actually invariant. Rationale entry extended. |
| M3 | Two over-ticked checklist boxes | **Both closed, by opposite moves.** The *Claims* box is now true at 14/14 because the four missing lines were supplied; the *Alternative rejected* box was restated, because 4 entries have no alternative in contention and padding them would be worse than the over-tick. |
| L1 | `spec:11`'s retense became a universal false for B6 | **Fixed in the spec**; a new *Changed* + *Alternative rejected* + retired-claim triple added to the `## End-goal context` entry, closing the "no rationale entry covers that clause" half of the finding. |
| L2 | "three surviving backward-looking sentences"; six survive | **Superseded below**, command-produced. |
| L3 | "19-entry rationale section"; 15 `###` | **Superseded below**, command-produced. |
| L4 | `spec:32`'s pointer orphaned by the `## Plan shape` rename | **Fixed in the spec** in the same edit as M1; recorded as its own *Changed* line in the rationale entry. |
| L5 | `glossary-optimizerhint`'s only carrier sits inside a code span | **Judged and fixed.** Reasoning below. |

### M1 — the root runtime response path, re-derived before it was rewritten

Worker 3's reading is exact, and it was re-derived here from source rather than accepted from the review or from Worker 0's confirmation.

- `optimizer/plans.py::runtime_path_from_path` appends the passed node's **own** key before walking `prev`: the loop reads `key = getattr(node, "key", None)`, appends it when it is neither `None` nor an `int`, and only then does `node = getattr(node, "prev", None)`. So the returned tuple always contains the node it was handed.
- `optimizer/plans.py::runtime_path_from_info` is a thin wrapper — `info is None` short-circuits to `()`, otherwise it delegates on `info.path`.
- `optimizer/walker.py::plan_optimizations` passes `runtime_prefixes=(runtime_prefixes if runtime_prefixes is not None else (runtime_path_from_info(info),))`. At a root resolver `info.path` is the root field's own `Path`, so the root prefix is `("allEntries",)`.
- The empty tuple is only `optimizer/walker.py::_walk_selections`'s `runtime_prefixes=((),)` parameter default, and that default's own docstring excludes the planner from it: it encodes "one empty-path prefix" for *direct or test-only callers without `info`*, and states that `plan_optimizations` always passes an explicit single-tuple.

So the falsified claim was describing an argument default, not the planner. The spec now states the condition that holds and — because this is the only document in the corpus that carries the walker/resolver key protocol — the consequence of getting it wrong: a walker built from the old sentence emits `EntryType.item@item` where the resolver asks for `EntryType.item@allEntries.item`, every key misses, and nothing raises.

`spec:127` ("The resolver side derives its half of the key by walking `info.path` back to the root … The walker side must use the same response-key convention") was re-read against the new `:32` and the two now agree; before this edit they contradicted each other.

### M2 — the shape changes too, per the row's own cited test

`examples/fakeshop/test_query/test_products_api.py::test_products_optimizer_selects_nested_forward_fk_depth_2_over_http` was read at its current content, not from the review:

> Before spec-034 this query planned a single `select_related("item__category")` JOIN. With the cascade hooks active, `ItemType` and `CategoryType` both define a custom `get_queryset`, so the optimizer downgrades each forward FK in the `item -> category` chain to a windowed `Prefetch` …

The three worked examples below the lead-in are each labelled `Plan shape:`, and the depth-3 one's is "root `select_related` includes the nested path" — exactly what stops being true. The rewritten lead-in qualifies both the count and the shape, and names the thing that genuinely survives the downgrade: O4's dispatch. That is what the rationale entry's "Nothing about O4 changed" was reaching for, stated one abstraction level too high.

### The two over-ticked boxes, measured and restated

Measured by a script that splits `## Reconciliation pass` on its `### ` headings, excludes the closing `### What this pass deliberately did not change`, and tests each entry body for the two italic field labels:

```shell
uv run python - <<'PY'
import pathlib
lines = pathlib.Path("docs/SPECS/appx/spec-003-optimizer_nested_prefetch_chains-0_0_2-rationale.md").read_text().splitlines()
start = next(i for i, l in enumerate(lines) if l.startswith("## Reconciliation pass"))
idxs = [i for i in range(start, len(lines)) if lines[i].startswith("### ")] + [len(lines)]
tot = alt = claims = 0
for a, b in zip(idxs, idxs[1:]):
    if lines[a][4:].startswith("What this pass deliberately"):
        continue
    body = "\n".join(lines[a:b])
    tot += 1
    alt += "*Alternative rejected" in body
    claims += "*Claims the spec no longer makes" in body
print(tot, alt, claims)
PY
```

- **Before this pass:** `14 8 10` — 6 of 14 entries carried no *Alternative rejected*, 4 of 14 no *Claims the spec no longer makes*. Worker 3's per-entry table is exact, row for row.
- **After this pass:** `14 10 14`.

The two gaps were closed by opposite moves, deliberately:

- ***Claims the spec no longer makes* — supply the missing lines.** All four are substantive retired claims, and two of them (`## Test plan`, `### B1 plan cache`) are the ones Worker 3 named as genuinely owed. `## Test plan` no longer claims the query-count rows live in `tests/optimizer/test_extension.py`, that the forward-FK row is one query regardless of configuration, that `select_related` compares equal to a list, that the leak row has one axis, or that the B2 stub/null tests are owed an update. `### B1 plan cache` no longer claims the propagation lives in the prefetch branch. `## Desired behavior` and `### B8 queryset diffing` likewise had real retired claims and now state them. The box stands ticked because it is now true.
- ***Alternative rejected* — restate the box.** Two more entries gained a genuine rejected alternative in this pass (`## End-goal context`'s "name the subset", `## Desired behavior`'s "qualify the counts only"), taking it to 10 of 14. The remaining four record a correction that had **no alternative in contention** — a symbol that does not exist, a tense, an attribution to the wrong call site. Writing four alternatives nobody weighed would satisfy the box by fabricating the evidence it exists to carry, which is a worse defect than the over-tick. The box now says what holds and carries the measurement.

The same universal is restated twice more in prose — `### Spec changes made (Worker 1 only)`'s rationale table and `### Notes for Worker 3`. Both are prior-pass sections, so both are **superseded here** rather than edited: the correct reading of each is the row above, and neither now-stale sentence should be relied on.

### The three superseded figures

| Prior claim | Where | What holds | Command |
|---|---|---|---|
| "The three surviving backward-looking sentences are the per-section pointers R1 added" | `### Implementation notes`, first bullet | **Seven** rationale pointers survive: the companion paragraph at `:3` plus **six** per-section pointers (`:32`, `:74`, `:95`, `:113`, `:125`, `:196`). R1's own artifact counts six; R2 deleted none and pass 2 deletes none | `grep -c 'rationale file\]\[spec-003-rationale\]' <spec>` → `7`; `grep -n` for the line numbers |
| "19 entries keyed to spec sections" | `### Spec changes made (Worker 1 only)`, rationale table row 1 | **15** `###` headings in `## Reconciliation pass`: 14 entries keyed to spec sections plus the closing `### What this pass deliberately did not change`, which the same sentence already describes separately | `awk '/^## Reconciliation pass/,0' <rationale> \| grep -c '^### '` → `15` |
| "each carrying *Changed* / *Alternative rejected* / *Claims the spec no longer makes*" (same row), and "Every R2 entry names the spec section, the rejected alternative, and the claims the spec may no longer make" (`### Notes for Worker 3`, bullet 2) | as cited | 14 of 14 carry the claims field; **10 of 14** carry a rejected alternative | the fenced script above → `14 10 14` |

L2 and L3 are the fourth and fifth miscounts across R1 and R2, and both share one shape with the three before them: a number written in narrative prose rather than in `### Validation run`, where the command sits beside the figure. Every count in this pass was produced by the command quoted next to it, and the population each command anchors is stated with it.

### L1 — the quantifier, and why the replacement is true of all seven

HEAD-before, read from the read-only copy (`git show HEAD:<spec>` into a scratch path outside the repo), line 9:

> B1 plan caching, B7 field metadata, B3 strictness, B4 optimizer hints, B5 context stashing, B2 FK-id elision, and B6 schema audit **have shipped or are designed around** the current `OptimizationPlan` shape.

R2 dropped the disjunct. The universal that replaced it is false for two of the seven, verified at source:

- **B6.** `optimizer/extension.py::DjangoOptimizerExtension.check_schema` collects the schema-reachable types, iterates `registry.iter_types()`, reads each registered definition's `field_map` and `optimizer_hints`, and appends warning strings. It constructs no plan and reads none.
- **B7.** `optimizer/field_meta.py::FieldMeta` is the metadata the walk plans *against* — upstream of any plan, not built around one.

The lead-in now names the planning **surface** — the plan the walk produces, the planning type's field metadata it plans against, or both — which is true of all seven and still delivers the sentence's actual job: O4 extends the planner without breaking any of them. Both glossary links (`fk-id-elision`, `schema-audit`) sit in the untouched tail of the sentence and were carried character-for-character.

### L5 — judged, and fixed

Pre-existence re-verified independently: `git show HEAD:<spec>` into a scratch path outside the repo carries the identical shape at its line 188, so this is not R2's doing and R2's rewrite of the paragraph preserved it exactly as the pass-1 report claimed.

**Fixed rather than deferred**, on margin rather than on severity. The eight-anchor constraint has zero margin; `optimizerhint` is a single-carrier anchor; and `scripts/check_spec_glossary.py` counts it today only because `REF_USE_PATTERN` does not strip code spans — so one of the eight links card 3's `import_spec_terms` chain rebuilds from is resting on a checker behaviour rather than on a link. The repair moves no link, changes no word of prose, and touches two characters: the backticks now sit inside the link label and around the trailing method call separately, leaving the reference outside both. That is the exact shape `check_spec_glossary.py --auto-link` writes for a term the spec already spells in inline code (its module docstring gives `` [`Meta.fields`][glossary-metafields] `` as the canonical form), so the anchor survives a checker that ever does strip code spans.

The package-wide question Worker 3 routed to the catalog — *should* `check_spec_glossary.py` strip code spans — is untouched and stays a maintainer decision. This fix makes spec-003 correct under either answer.

### Spec changes made (Worker 1 only), pass 2

Cited against the post-pass-2 spec. The line numbering is unchanged from pass 1: this pass edited four sentences in place and added no line.

| Spec location | Change | Reason |
|---|---|---|
| `:11` | `## End-goal context` lead-in: "are all built around the `OptimizationPlan` shape" → "all build on the optimizer's planning surface — the `OptimizationPlan` the walk produces, the planning type's field metadata the walk plans against, or both" | L1 — the retense dropped a disjunct and produced a universal false for B6 (`optimizer/extension.py::DjangoOptimizerExtension.check_schema` touches no plan) and for B7 (`optimizer/field_meta.py::FieldMeta` is upstream of one) |
| `:32` | The runtime half of the starting-condition sentence corrected: planning starts at the runtime response path of the **root field being planned**, empty only for a caller supplying no `info`; the consequence of the alternative stated | M1 — `optimizer/plans.py::runtime_path_from_path` appends the passed node's own key before walking `prev`, and `optimizer/walker.py::plan_optimizations` passes `runtime_path_from_info(info)`. `((),)` is `::_walk_selections`'s default, which its docstring scopes to callers without `info` |
| `:32` | Final clause: "The pre-O4 dispatch block this section quoted…" → "The pre-O4 dispatch shape, and where the shipped walker departed from it, are in the…" | L4 — the noun phrase's referent was the section's own former content, orphaned by the `## Current state` → `## Plan shape` rename. It now names the thing, matching its rationale entry's heading and the five sibling pointers' shape |
| `:37` | `## Desired behavior` lead-in: qualifies count **and** plan shape on the O6 downgrade, and names O4's dispatch as what the downgrade does not change | M2 — the three examples below are each labelled `Plan shape:`, and the cited live test's docstring records the depth-3 chain moving from `select_related("item__category")` to a `Prefetch` per downgraded link |
| `:98` | `` `[OptimizerHint][glossary-optimizerhint].prefetch(obj)` `` → the backticks moved inside the link label and around the trailing call, leaving the reference outside both | L5 — the anchor's only carrier sat inside a code span. Pre-existing at HEAD (its line 188); the repair changes no prose |

**Rationale changes (same custodian, same pass).** All are inside `## Reconciliation pass`, this item's own block; R1's `## Entries keyed to the spec` and `## Standing notes` were not touched.

| Rationale location | Change | Reason |
|---|---|---|
| `### \`## End-goal context\`` | Added a *Changed* paragraph for the quantifier, an *Alternative rejected* (name the subset), and a third retired claim | L1 — the finding's second half was that no entry covered the clause |
| `### \`## Plan shape\` (was \`## Current state\`)` | The planner-signature paragraph's "two facts" reworded to "two starting conditions"; a new *Changed* paragraph on the root runtime path with its consequence; a new *Alternative rejected* (drop the runtime half); a new *Changed* paragraph for the orphaned pointer; two retired claims added | M1, L4 — the entry itself asserted the falsified fact, so leaving it would have preserved the error in the document that explains the correction |
| `### \`## Desired behavior\`` | The qualifier paragraph rewritten to cover shape as well as count; a *Changed again, in the correcting pass* paragraph recording what the first wording got wrong and why; a new *Alternative rejected* (qualify counts only); a *Claims* line added | M2, M3 |
| `### \`### Hints are leaf operations\` and \`### B4 optimizer hints\`` | Added a *Fixed in passing* paragraph for the code-span link and an *Alternative rejected* (defer it) | L5 — a markup repair to a spec is still a custodian edit and owes its account here |
| `### \`### B1 plan cache\`` | *Claims* line added | M3 — named by Worker 3 as genuinely owed |
| `### \`### B8 queryset diffing\`` | *Claims* line added | M3 |
| `### \`## Test plan\`` | *Claims* line added, naming five retired claims | M3 — named by Worker 3 as genuinely owed |

**No spec status/header line needed a `worker-1.md` `## Spec status-line re-verification` edit.** Re-checked at the start of this pass against the read-only HEAD copy: spec-003 carries no `Status:` / owner / target-release block, and lines 1-4 are the title and the companion-pointer paragraph. The pointer paragraph was not edited this pass — its coverage of the rationale's second block, added in pass 1, is still accurate after the four entries this pass extended.

### Validation run (pass 2)

Every command run after the last edit of this pass.

- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-003-optimizer_nested_prefetch_chains-0_0_2.md` → `OK: 8 terms - all have glossary entries and at least one spec link.` **exit 0**. Re-run after each of the two writing sessions (spec, then rationale); identical both times.
- `uv run python examples/fakeshop/manage.py import_spec_terms --check` → `OK: 49 done cards have glossary links.` **exit 0**.
- `uv run python scripts/check_trailing_commas.py --check <spec> <rationale> <this artifact>` → **exit 0** on all three.
- **Per-anchor re-count, not the green exit.** A script that splits each file at `<!-- LINK DEFINITIONS -->`, parses the definitions, and counts `][ref-id]` uses in the body alone returns **exactly one body use for each of the eight** (`djangotype`, `fk-id-elision`, `metaoptimizer-hints`, `only-projection`, `optimizerhint`, `plan-cache`, `queryset-diffing`, `schema-audit`). The `optimizerhint` repair did not change its count — it changed where the backticks sit around it.
- **Link scaffold, both files:** spec **10 definitions / 10 distinct uses**, rationale **19 / 19**; **0 undefined references, 0 unused definitions, 0 definition targets missing on disk** (each target's path resolved from its own file's directory and `exists()`-checked). The rationale's count is unchanged from pass 1 — this pass added no definition and removed none.
- **In-page anchors:** an independent slugger over the post-pass-2 spec reports **21 headings, 0 duplicate slugs**; the rationale's **9 anchor-bearing definitions**, used **10 times**, all **9 resolve** against real spec headings, `#plan-shape` included.
- `grep -nE '[a-zA-Z_/]+\.(py|md):[0-9]+'` over the spec and the rationale → **no match**. `AGENTS.md` rule 27 preserved; every source reference added this pass is symbol-qualified.
- `grep -c '```'` on the spec → **0** fenced blocks, unchanged.
- **Status-language sweep** re-run — `grep -cE 'currently|already|today|not yet|will |becomes obsolete|planned|future' <spec>` → **14 matching lines**, each read individually. Thirteen are runtime, in-document, or vocabulary references (`planned_resolver_keys`, "planned by the same recursive walk", Django's matching behaviour, the plan under construction, the two rationale pointers); the fourteenth is the literal `not yet implemented` rider text at `:194`, which R3 owns and this pass must not pre-empt.
  - **No new status language was introduced, proved rather than asserted.** The pass-1 spec was reconstructed in a scratch path outside the repo by reverting this pass's five substitutions, and the reconstruction is exact: `wc -lc` returns **240 / 27,864**, the pass-1 figures recorded above. The same grep over it returns **12** matching lines, and `diff` of the two line-number sets shows the additions are **`:32` and `:37` only** — the two lead-ins this pass rewrote, matching on "the root field being **planned**" and "**planned** by the same recursion". Both are vocabulary, not a status claim.
  - **Pass 1's own figure for this sweep, "10 hits", does not reproduce** and is superseded: the same command over the reconstructed pass-1 spec returns **12**. Which two of the twelve pass 1 omitted is not recoverable — it recorded a total rather than the lines — so the disposition is re-derived here from scratch rather than differenced against it: every one of the twelve is among the fourteen read individually above, and the only one that reads as a status claim rather than as runtime, in-document, or vocabulary usage is `:194`'s literal rider text, which is R3's to discharge. Pass 1's *conclusion* therefore stands and its *count* does not. It is the fifth figure in this cycle written without the command that produces it.
- `wc -lc` → spec **240 lines / 28,624 bytes**; rationale **1,021 / 71,439**. Pass 2's own delta: spec **+0 lines / +760 bytes**, rationale **+96 / +7,661**, against the pass-1 figures of 240 / 27,864 and 925 / 63,778 recorded above.
- `git diff --stat -- docs/SPECS/spec-003-…md` → **78 insertions(+), 285 deletions(-)**, unchanged from pass 1: this pass rewrote four already-inserted lines and added none.
- `git diff --stat -- django_strawberry_framework/ tests/ examples/` → **empty**. No source or test file was opened for writing; no `pytest` (`AGENTS.md` rule 15); no `--cov*` flag in any form.
- No `git stash` / `checkout` / `restore` / `worktree` at any point. The HEAD reference was obtained read-only via `git show HEAD:<spec>` into a scratch path outside the repository.
- No `ruff` run: no `.py` file was touched.
- `git status --short` → ` M docs/SPECS/spec-003-…md` plus this cycle's four untracked paths, and **nothing else**. `HEAD` re-derived rather than trusted: `git rev-parse --short HEAD` → **`4d1c512a`**, matching the review's addendum; the baseline-dirty list is still empty.

### Failability proofs

None; this pass introduced no new boundary. `git diff -- django_strawberry_framework/` is empty.

### Hot-path budget

Not applicable; plan declares no hot path.

### Floor verification

Not applicable; plan declares floor-verification scope none.

### Implementation notes

- **The failure mode Worker 3 named is the one that produced both Mediums, and it has a cheap detector this pass adopted.** A reconciliation writes many new present-tense sentences, and nothing else in the process reads them against source — the drift table only covers what the spec *said*. Both M1 and M2 were sentences whose *first half* was verified and whose *second half* was carried over from the falsified text unexamined: `:32`'s Django prefix is right and its runtime path was inherited; `:37`'s "the counts are not" is right and "the plan shapes are unchanged" was asserted beside it. The detector is per-clause, not per-sentence: verify each conjunct against the symbol it names, including the one that looks like scaffolding.
- **M2 was self-refuting in eleven words and still shipped.** "…turns a same-query join into its own round trip; the plan shapes are unchanged" contradicts itself inside one semicolon. Reading a sentence for what it asserts about HEAD is not the same as reading it for internal consistency, and the second read costs nothing.
- **The two over-ticked boxes were closed by opposite moves on purpose.** A missing field is either a gap in the record or an honest absence, and the box has to be made true either by filling the gap or by saying what actually holds. Filling four alternatives nobody weighed would have satisfied the letter of the box while destroying the thing it measures — `BUILD.md` records rejected alternatives so a settled question is not re-fought, and a manufactured one re-opens nothing and misleads about what was considered.
- **The rationale entries were corrected where they stood, not appended to.** Three of them (`## Plan shape`, `## Desired behavior`, `## End-goal context`) *asserted* the facts M1, M2, and L1 falsified, so appending a correction beneath them would have left the document explaining a change while restating the error. Rule 4's append-only bar protects settled entries from a **later round**; this is the same item's own fix pass, the R1 precedent that Worker 3 accepted. The correcting paragraph in the `## Desired behavior` entry is explicitly labelled as the correcting pass's, so the record shows the deliberation moved rather than pretending the first wording never existed — which is the rationale's job and precisely what the spec must not do.
- **L5 was fixed on margin, not on severity.** It is genuinely out of reconciliation scope and genuinely pre-existing, and both are arguments for deferring. What decided it the other way is that the constraint it threatens has zero margin, the fix is two characters, it moves no link and changes no prose, and it is verified by the same command the constraint is already gated on. A deferred item that a later checker change turns into a broken card-wrap chain is a worse trade than a two-character repair inside a documentation cycle.
- **Nothing Worker 3 verified clean was disturbed.** The rescued R1 bullet, the 22 drift rows, the three beyond-floor finds, D11's treatment, the five scope-trap rows, the eight anchors' carriers, the `## Plan shape` rename, and the `` ## Missing `.py` files `` deletion were all left exactly as reviewed. This pass touched four sentences in the spec and seven entries in the rationale, all of them named in a finding.

### Notes for Worker 3 (re-review)

- **The two spec sentences to re-derive from source rather than from this report** are `:32` and `:37`. For `:32` the load-bearing chain is `optimizer/plans.py::runtime_path_from_path` (appends the passed node's own key first) → `::runtime_path_from_info` → `optimizer/walker.py::plan_optimizations` (`runtime_prefixes=(runtime_path_from_info(info),)`), with `::_walk_selections`'s `((),)` default and its docstring as the exclusion. For `:37`, `examples/fakeshop/test_query/test_products_api.py::test_products_optimizer_selects_nested_forward_fk_depth_2_over_http`'s docstring.
- **`:11` is the third new present-tense sentence** and is worth the same treatment: the claim is that all seven B-slices build on the plan, the field metadata, or both. `optimizer/extension.py::DjangoOptimizerExtension.check_schema` and `optimizer/field_meta.py::FieldMeta` are the two that make the previous wording false and the new wording true.
- **The counts.** Every figure in this report has its command beside it; the three superseded ones are tabled with the population each command anchors. The rationale-field measurement is a fenced, runnable script rather than a number, so it can be re-derived in one paste.
- **What this pass deliberately did not do:** it did not touch `## Documentation updates when O4 ships` (R3's), any sibling spec, the terms CSV, any package source or test, any prior artifact section, or R1's rationale entries. `KANBAN.md` note 3 from the prior review still stands unchanged for R3.

### Notes for Worker 1 (spec reconciliation) — carried into R3

The six items in the prior review's list carry forward unchanged, with two amendments:

1. **Item 4's deferred-work list gains nothing from this pass, and loses one.** The `glossary-optimizerhint` code-span item Worker 3 routed to the catalog is **partly discharged**: spec-003's own link now sits outside the code span, so no anchor of this spec's eight depends on the checker's code-span behaviour. What remains for the catalog is the package-wide question only — whether `scripts/check_spec_glossary.py` should strip code spans at all — which is a maintainer decision affecting every spec, not this one.
2. **The unguarded ordering invariant and the forward-M2M `attname` artifact are unchanged**, as is the `::_prefetch_lookup_paths` depth-cap asymmetry. All three stay maintainer notes.

### Review outcome of the prior pass, addressed

All three Mediums and all five Lows are closed: five by a spec edit, two by supersession with a command-produced figure, one (M3) by supplying four rationale fields and restating one box. No finding was rejected, so no rejection reason is owed.

`Status: planned` — Deviation 2 corollary; Worker 0 reads this as "dispatch Worker 3" for the re-review.

---

## Review (Worker 3, pass 2)

Read-only re-review of the working-tree diff of `docs/SPECS/spec-003-optimizer_nested_prefetch_chains-0_0_2.md` against `HEAD` (re-derived: `git rev-parse --short HEAD` -> `4d1c512a`) plus the `## Reconciliation pass` block of the untracked rationale. No `git stash` / `checkout` / `restore` / `worktree`; the HEAD reference was obtained read-only via `git show HEAD:<path>` into a scratch path outside the repository. No `pytest`, no `--cov*` flag, no source or test edit. Fresh invocation: nothing below is carried from pass 1's section, every figure and every claim was re-derived.

### High:

None.

### Medium:

None. All three pass-1 Mediums are closed on substance, each verified against source rather than against the report.

**M1 closed.** The rewritten `spec:32` is correct at HEAD. Re-derived along the whole chain: `optimizer/plans.py::runtime_path_from_path` appends the passed node's own `key` **before** advancing to `prev` (`key = getattr(node, "key", None)` ... `node = getattr(node, "prev", None)`), so the returned tuple always contains the node it was handed; `::runtime_path_from_info` short-circuits to `()` only for `info is None` and otherwise delegates on `info.path`; `optimizer/walker.py::plan_optimizations` passes `runtime_prefixes=(runtime_prefixes if runtime_prefixes is not None else (runtime_path_from_info(info),))`. The `((),)` empty prefix is `::_walk_selections`'s parameter default, and that default's own docstring scopes it to "direct or test-only callers without `info`" and states that `plan_optimizations` always passes an explicit single-tuple. The new sentence's three parts each hold: the Django prefix is empty, the runtime path is the root field's own response key, and the empty case is a caller supplying no `info`.

The `:127` agreement claim also holds: `:127` ("The resolver side derives its half of the key by walking `info.path` back to the root ... The walker side must use the same response-key convention") and the new `:32` now describe one convention; the pass-1 text asserted the opposite of `:127`. The added consequence clause (a walker started from an empty path keys every elision one segment short and nothing raises) is the load-bearing half and is correctly derived - `runtime_path_from_info` is what both sides call, so a mismatch is silent by construction.

**M2 closed.** `spec:37` now qualifies both count and shape and names O4's dispatch as what survives. Verified against the cited test at its current content: `examples/fakeshop/test_query/test_products_optimizer_selects_nested_forward_fk_depth_2_over_http`'s docstring (`examples/fakeshop/test_query/test_products_api.py:1364-1381`) records the chain moving from one `select_related("item__category")` JOIN to a windowed `Prefetch` per downgraded link and pins 3 queries. The "dispatch is unchanged" half is true at source: both branches are reached from `optimizer/walker.py::_dispatch_single_relation`, whose `prefer_prefetch` argument is the only thing O6 and the two hint routes vary.

**M3 closed, and the reasoning for closing it by two opposite moves is right.** Re-ran the measurement independently (own script, split on `### `, closing subsection excluded): **14 entries, 10 with *Alternative rejected*, 14 with *Claims the spec no longer makes*** - matching the report exactly, and matching pass 1's per-entry table on the four claims-gaps it named. The *Claims* box is now true at 14/14; I read all four supplied lines and each names a real retired claim (`## Test plan`'s five, `### B1 plan cache`'s propagation site, `## Desired behavior`'s unconditional counts, `### B8 queryset diffing`'s "future work").

On the restated box: **a restatement does discharge the over-tick here, and 10/14 is the real number.** `ARTIFACT.md:52` makes an over-tick a finding because a tick asserts a contract landed; it does not require the box's *wording* to be preserved when the box is the pass's own (this checklist is Worker-1-authored from the maintainer framing, not verbatim spec text, and `worker-1.md` planning step 8 is what put it there). `BUILD.md:98` requires each entry to carry "the alternatives rejected and why each lost" - a set that is empty for an entry where nothing was in contention, not a quota. Manufacturing four alternatives would have made the box's own evidence false, which is a worse defect than the over-tick and is unfalsifiable by any later reader. The four alternative-free entries (`### Same-query recursion`, `### B1 plan cache`, `### B8 queryset diffing`, `## Test plan`) were each read: they record a deleted "(already done)" parenthetical, a wrong attribution, a tense, and a set of tier/container corrections that `AGENTS.md` "Test through real usage" decides rather than weighs. The restated box now says what holds and carries its measurement.

The two prose repeats of the same universal were **superseded, not edited** (`ARTIFACT.md:187`), which is correct.

### Low:

#### L-a - `spec:37`'s second sentence generalizes past the many-side examples (recorded, not held)

`docs/SPECS/spec-003-optimizer_nested_prefetch_chains-0_0_2.md:37`

> A type that does is downgraded by O6, and that link leaves the `select_related` chain for a `Prefetch` of its own - so both the shape and the count change for it.

Two of the three worked examples below are many-side chains, whose links were never in the `select_related` chain; a custom `get_queryset` on `ItemType` there flips `plan.cacheable` and swaps the child queryset but changes neither shape nor count (the reverse-FK live test pins 3 either way). Read strictly over those examples the clause does not hold, and "a type ... is downgraded" is loose for "the relation to that type".

**Intentionally rejected as a finding, with the reason recorded rather than looped.** The governing first sentence scopes the whole block conservatively ("Each query count and plan shape below assumes no type on the chain overrides `get_queryset`"), so no reader derives a wrong plan shape or a wrong count from it - the imprecision is in the explanation of a hazard, not in a contract a builder codes from (`BUILD.md` `## Severity definitions`: Low is the non-load-bearing tier). This is the fifth review pass in the cycle and the sentence it would re-open is the one just corrected; a sixth loop buys a reader nothing they would notice. Carried to Worker 1 as note 1 below in case R3 is editing that section anyway.

All five pass-1 Lows are closed:

- **L1 closed and verified true of all seven B-slices.** `spec:11` now reads "all build on the optimizer's planning surface - the `OptimizationPlan` the walk produces, the planning type's field metadata the walk plans against, or both". B6 is the case that falsified the previous universal and the new disjunct covers it: `optimizer/extension.py::DjangoOptimizerExtension.check_schema` reads `definition.field_map` and `definition.optimizer_hints` and returns warning strings, constructing no plan - and `field_map`'s values *are* `optimizer/field_meta.py::FieldMeta` (`meta.is_relation`, `meta.related_model` at the loop body), so "the planning type's field metadata" is the surface it genuinely builds on. B7 is that metadata; B1/B2/B3/B5 read or write the plan. The missing-rationale-coverage half is closed too: the `## End-goal context` entry now carries a *Changed* paragraph for the quantifier, an *Alternative rejected* ("name the subset"), and a third retired claim.
- **L4 closed.** `spec:32`'s final clause now names the thing ("The pre-O4 dispatch shape, and where the shipped walker departed from it") instead of the section's own former content, and matches the five sibling pointers' shape.
- **L2 / L3 superseded with figures I re-derived exactly.** `grep -c 'rationale file\]\[spec-003-rationale\]'` -> **7**, at lines **3, 32, 74, 95, 113, 125, 196** = the companion paragraph plus **six** per-section pointers. `awk '/^## Reconciliation pass/,0' | grep -c '^### '` -> **15**. Both supersessions state the population the command anchors.
- **L5 closed, and the appeal to `--auto-link` is accurate.** `spec:98` now reads `` [`OptimizerHint`][glossary-optimizerhint]`.prefetch(obj)` `` - reference outside both code spans. `scripts/check_spec_glossary.py`'s module docstring (lines 44-47) states the canonical rewrite verbatim: "The backtick-wrapped form is preferred when the spec already says e.g. ``Meta.fields`` in inline code - the rewrite becomes ``[`Meta.fields`][glossary-metafields]`` with the inline-code backticks preserved inside the link label." That is exactly the shape landed. Independently re-counted after the repair: `optimizerhint` still carries **exactly one** body use, and the anchor now survives a checker that strips code spans (`REF_USE_PATTERN` at `scripts/check_spec_glossary.py:72` does not strip them today, which was the finding's whole point). Two characters, no prose moved, no link moved.

### The self-reported sixth miscount, re-derived and judged

**The 12 reproduces, by a route independent of the report's.** The status-language sweep over the post-pass-2 spec returns **14** matching lines (`:27 :32 :37 :64 :83 :86 :129 :138 :151 :154 :174 :194 :196 :202`), each read: thirteen are runtime, in-document, or vocabulary uses (`planned_resolver_keys`, "currently being built", "Django will match against", "does not warn", "already discharged"), and the fourteenth is `:194`'s literal `not yet implemented` rider text, which is R3's. The only two lines this pass added to that set are `:32` and `:37`, both on the word "planned" ("the root field being **planned**", "**planned** by the same recursion") - both vocabulary. 14 - 2 = **12** for the pass-1 spec, not the 10 pass 1 recorded. I confirmed the two pass-1 sentences the fix replaced (quoted in full in pass 1's M1/M2) carry none of the swept tokens, and the same for the pass-1 `:11` and `:98` texts, so no line left the set either.

**The reconstruction proof is sound for what it is asked to prove, with one caveat worth stating.** Reverting five known substitutions and confirming `wc -lc` returns the recorded 240 / 27,864 is a checksum, not an identity proof - two compensating byte errors would survive it. What makes the conclusion safe is that the byte check is not carrying the argument alone: the substitutions are enumerated in `### Spec changes made ... pass 2`, the diff stat is unchanged, and the derived figure reproduces from the other direction (above) without the reconstruction at all. Correctly labelled as the fifth miscount and correctly resolved by re-deriving the disposition from scratch rather than differencing against an unrecoverable line set.

### Nothing I cleared last pass was disturbed

Each re-derived, not assumed:

- `git diff --stat` on the spec -> **78 insertions(+), 285 deletions(-)**, unchanged. `wc -l` -> **240**, unchanged. Both confirm the pass appended no line - the cheapest available proof that the rewrite was in place.
- **The rescued R1 bullet at `spec:79` is byte-identical.** Reconstructed independently from `docs/builder/bld-003-r1-rationale_move.md:850` (the blockquoted scope sentences, `> ` stripped) plus the untouched instruction half at `:852`, written to a scratch path outside the repo: `diff` against `sed -n '79p'` of the working tree is **identical, 778 bytes both sides**.
- **All 8 glossary anchors at exactly one body link**, re-counted per anchor by a script that partitions each file at `<!-- LINK DEFINITIONS -->`: `djangotype`, `fk-id-elision`, `metaoptimizer-hints`, `only-projection`, `optimizerhint`, `plan-cache`, `queryset-diffing`, `schema-audit` -> 1 each; 0 undefined references, 0 unused definitions, 0 definition targets missing on disk, in both files (spec 10/10, rationale 19/19). `…-terms.csv` is absent from `git status` - never opened.
- **The 22 drift rows, the three beyond-floor finds, D11's treatment, and the scope trap on all five rows** are untouched: pass 2's edits are confined to `:11`, `:32`, `:37`, `:98`, and every line number pass 1 cited (`:64 :70 :80 :81 :84-87 :89 :91 :113 :118 :123 :131 :138 :144 :145 :149 :154 :179-180`) still carries the content pass 1 verified there, read end-to-end this pass. `D9`'s in-place correction and the `## Plan shape` rename are as reviewed; `grep -rn '#current-state'` still resolves nothing into this spec.
- **The `` ## Missing `.py` files `` deletion** is unchanged; the section is still absent and nothing points at it.
- **R1's rationale blocks are untouched.** `## Reconciliation pass` still begins at rationale line **476**, the same offset pass 1 measured, so lines 1-475 (`## Provenance`, `## Entries keyed to the spec`, `## Standing notes`) took no insertion or deletion.
- **No source or test file was touched** - confirmed rather than assumed: `git diff --stat -- django_strawberry_framework/ tests/ examples/` is **empty**, and `git status --porcelain` carries only ` M <spec>` plus this cycle's four untracked paths. No boundary is introduced, so no failability proof is owed and my mandatory re-run set is legitimately **empty** (`worker-3.md`: legal only when the diff introduces no boundary meeting the floor). Boundaries re-run: none. Boundaries accepted on the performer's record: none exist.

### The governing principle still holds

Read cold, the post-fix spec states a contract and never asks the reader to apply a chronology to reach the present. The four rewritten sentences are all present-tense contract (`:11` a property of the B-slices, `:32` a starting condition plus the reason it is that condition, `:37` a scoping assumption, `:98` markup only). No amendment block, no retraction, no "as of spec-NNN", no "originally". The seven rationale pointers are the `worker-1.md` rule-1 companion pointers and point outward rather than narrating; the one that previously narrated (`:32`'s "this section quoted") is the one L4 closed. The "+2 status-language lines, both vocabulary" claim is exactly what my own sweep finds.

### Every new claim checked against the symbol it names

Four spec sentences and seven rationale entries changed; each was read against source.

| Location | New claim | Verified at |
|---|---|---|
| `spec:11` | all seven B-slices build on the plan, the planning type's field metadata, or both | `extension.py::DjangoOptimizerExtension.check_schema` (reads `definition.field_map` / `optimizer_hints`, no plan); `field_meta.py::FieldMeta` is what `field_map` holds |
| `spec:32` | root Django prefix empty; root runtime path is the root field's response key; empty only without `info` | `plans.py::runtime_path_from_path` / `::runtime_path_from_info`; `walker.py::plan_optimizations`; `::_walk_selections` default + docstring |
| `spec:32` | consequence: keys would miss silently | both sides call `runtime_path_from_info`; nothing raises on a miss (`types/resolvers.py::_make_relation_resolver.forward_resolver #"if elisions and key in elisions:"`) |
| `spec:37` | shape and count both move for a downgraded link; O4's dispatch does not | live test docstring at `test_products_api.py:1364-1381`; `walker.py::_dispatch_single_relation` reached from both routes |
| `spec:98` | markup only | no semantic claim; `check_spec_glossary.py` docstring lines 44-47 |
| rationale `## End-goal context` | B6 walks the registry and returns warnings without constructing a plan; B7 is upstream | as `spec:11` |
| rationale `## Plan shape` | the empty tuple is the recursive walker's default, never the planner's | `walker.py::_walk_selections` signature + docstring |
| rationale `## Desired behavior` | what is invariant is O4's dispatch | as `spec:37` |
| rationale `### Hints are leaf operations` / `### B4` | `--auto-link`'s canonical form; `REF_USE_PATTERN` does not strip code spans | `scripts/check_spec_glossary.py:44-47`, `:72` |
| rationale `### B1 plan cache` | propagation is the single absorb step | `walker.py::_absorb_child_plan` -> `plans.py::OptimizationPlan.merge_metadata_from #"if not other.cacheable:"` |
| rationale `### B8` / `## Test plan` | retired claims as listed | `plans.py::diff_plan_for_queryset`; both live tests present; `test_walker.py::test_plan_emits_nested_select_related_chain_depth_2` asserts a tuple |

Nothing false found among them.

### Stated counts, re-derived

Every figure in `## Reconciliation report (Worker 1, pass 2)` that a command can produce was re-run: rationale field measurement **14 / 10 / 14** (exact, own script); `### ` headings in the block **15** (exact); rationale pointers **7**, six per-section at `:3 :32 :74 :95 :113 :125 :196` (exact); `wc -lc` spec **240 / 28,624** and rationale **1,021 / 71,439** (exact); pass-2 deltas **+0 / +760** and **+96 / +7,661** against the pass-1 figures (arithmetic, exact); `git diff --stat` **78 / 285** (exact); fenced blocks in the spec **0** (exact); status-language sweep **14** lines (exact) and the pass-1 figure **12** (re-derived independently, above); per-anchor body links **1 x 8** (exact); scaffold **10/10** and **19/19** with 0 undefined / 0 unused / 0 missing targets (exact); `grep -nE '[a-zA-Z_/]+\.(py|md):[0-9]+'` over both files -> no match (exact); `HEAD` -> `4d1c512a` (re-derived). **Of the figures re-derivable this pass, none is wrong** - the first pass in this cycle of which that is true.

### DRY findings

- **Spec-versus-rationale separation still holds.** The four corrected spec sentences state what holds; the seven rationale entries state why it changed and what was rejected. No contract text appears on both sides. The `:32` consequence clause is the one sentence that could have gone either way - it is a rule a builder codes against (use the resolver's response-key convention), not a deliberation, so the spec is its right home, and the rationale's longer version argues the choice rather than restating the rule.
- **No new duplication.** No definition, code span, or sibling-spec pointer was added this pass (rationale scaffold unchanged at 19/19).
- **Existence challenge:** none raised. The pass adds no abstraction.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` -> empty. `__all__` and the re-export list unchanged; no new public export.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

Applicable - the diff is entirely documentation.

- No version string, shipped/planned status, or card ID touched; the spec carries no `Status:` header block.
- `examples/fakeshop/db.sqlite3`, `KANBAN.md`, `KANBAN.html`, `docs/GLOSSARY.md` all clean; nothing from this pass reaches them.
- All 29 link definitions across the two files disk-checked present from each file's own directory; reference-style convention intact, `<!-- LINK DEFINITIONS -->` with all 10 canonical group headers in order.
- `## Documentation updates when O4 ships`'s open `spec-004` rider is correctly still standing for R3.

### Validation commands I re-ran

```
git rev-parse --short HEAD                              -> 4d1c512a
uv run python scripts/check_spec_glossary.py --spec <spec>
  -> OK: 8 terms - all have glossary entries and at least one spec link.   exit 0
uv run python scripts/check_trailing_commas.py --check <spec> <rationale> <this artifact>
  -> exit 0
git diff --stat -- django_strawberry_framework/ tests/ examples/          -> empty
git status --porcelain  -> " M <spec>" + this cycle's four untracked paths, nothing else
```

### Temp test verification

None created. The item introduces no boundary and changes no code path; `docs/builder/temp-tests/r2/` was not created.

### Static helper use

`scripts/review_inspect.py` **not run**, and the skip is recorded with its reason: `BUILD.md` `### When to run the helper during build` triggers Worker 3 on a slice adding a `.py` file, touching `optimizer/` or `types/`, or adding 30+/50+ lines of logic. This diff does none - `git diff -- django_strawberry_framework/ tests/ examples/` is empty. No shadow file was read or cited; every source reference above is symbol-qualified and read from the original file.

### What looks solid

- **The two Mediums were fixed by re-deriving from source, not by patching around the review's wording.** `spec:32` in particular now carries the consequence as well as the condition, which is the difference between a fact a reader can check and a rule a builder can code from - and it is the corpus's only statement of that protocol.
- **M3's asymmetric close is the right judgement and is the finding worth the cycle's memory.** The instinct that made a box true by supplying four real retired claims is the same instinct that refused to make the other box true by inventing four alternatives. A quota satisfied with manufactured evidence is undetectable by any later reader; an honestly restated box carries its own measurement.
- **L5 was decided on margin rather than on scope**, and the appeal to `--auto-link`'s canonical form is a real check against a real authority rather than a preference dressed as one.
- **The self-reported sixth miscount.** The pass found and published a wrong figure of its own that no reviewer had raised, then re-derived the disposition from scratch instead of differencing against an unrecoverable record. That is the behaviour that ends a run of miscounts.

### Notes for Worker 1 (spec reconciliation)

1. **L-a above is recorded and explicitly not held.** If R3 or a later pass edits `## Desired behavior` for another reason, tightening `:37`'s second sentence to the single-valued case ("a forward FK or OneToOne on the chain leaves the `select_related` chain for a `Prefetch` of its own") would close it at zero cost. Alone it does not justify reopening the section.
2. **The six items in the pass-1 review's list, as amended by pass 2, carry forward unchanged** - `## Documentation updates when O4 ships` is R3's to close and owes a disposition decision; the `spec-004` rider edit is still owed; the four sibling-spec code-span references meet R3's cross-reference sweep; the deferred-work catalog holds the unguarded ordering invariant, the forward-M2M `attname` artifact, and the `::_prefetch_lookup_paths` depth-cap asymmetry.
3. **The `glossary-optimizerhint` catalog item is correctly reduced, not dropped.** Spec-003 no longer depends on the checker's code-span behaviour; what remains for the maintainer is the package-wide question - should `scripts/check_spec_glossary.py` strip code spans in `REF_USE_PATTERN` - which affects every spec whose only carrier for an anchor sits in inline code. Worth a repo-wide count before anyone changes it.
4. **`KANBAN.md` note from the pass-1 review still stands for R3**: card `TODO-ALPHA-052-0.1.0` names four stale spec-003 sites, three now closed, and its prescribed replacement ("state that O4 is shipped") disagrees with what R2 deliberately rejected. Surface the divergence to the maintainer rather than reconciling it silently.
5. **Working-tree state at the close of this pass:** `HEAD` `4d1c512a`, baseline-dirty list empty, `git status --porcelain` carrying only this cycle's own five paths. Nothing was edited or reverted outside my writable set.

### Review outcome

`review-accepted`.

All three Mediums and all five Lows are closed on substance, each verified against the symbol or command it rests on rather than against the report: `spec:32` and `spec:37` now state what `optimizer/walker.py` and the cited live test actually do, the two checklist boxes are true as written (one by supplying four real fields, one by an honestly restated universal carrying its measurement), and the three superseded figures re-derive exactly. Nothing cleared in the prior pass was disturbed - the diff is still 78/285 with the line count unchanged, the rescued R1 bullet is byte-identical at 778 B by independent reconstruction, all eight anchors carry exactly one body link with the terms CSV never opened, R1's rationale blocks take no insertion, and no package source or test is touched.

One residue is recorded and intentionally rejected rather than looped (L-a, `:37`'s second sentence generalizing past the many-side examples): the governing sentence above it scopes the block conservatively, so it misleads no reader about a contract and no builder about a rule. `BUILD.md` `## Severity definitions` reserves Low for exactly that, and this is the fifth review pass in the cycle. The item is done.

---

## Final verification (Worker 1)

Fresh invocation with no memory of the prior passes; the artifact and the working-tree diff are the record. Every figure below was produced by the command quoted beside it, in the same edit that wrote it down. `HEAD` re-derived rather than trusted: `git rev-parse --short HEAD` -> **`4d1c512a`**; `git status --porcelain` carries ` M <spec>` plus this cycle's four untracked paths and **nothing else** — the baseline-dirty list is empty in both directions.

No `pytest` (`AGENTS.md` rule 15), no `--cov*` flag in any form, no `git stash` / `checkout` / `restore` / `worktree`. The read-only HEAD reference and both reconstructions were written to a scratch path **outside** the repository.

### Spec status-line re-verification

Spec-003 carries no `Status:` / owner / target-release header block. Lines 1-4 are the title, a blank, the companion-pointer paragraph, and a blank. The pointer paragraph was re-read against the rationale's current contents: it names both entry blocks' subject matter (proposed shapes, quoted pre-O4 code, insertion-point guidance, the staging convention, the documentation obligations, and "where the package later corrected or outgrew something it asserted") and is accurate after this pass's rationale addition. **No status/header line needed an edit.**

### The iteration history, confirmed closed in the files

Three Mediums, five Lows, and one self-reported miscount. Each re-checked against the file rather than against the report.

| Finding | Confirmed closed by |
|---|---|
| M1 — `spec:32`'s empty root runtime path | Re-derived the whole chain myself. `optimizer/plans.py::runtime_path_from_path` appends the passed node's own `key` (`key = getattr(node, "key", None)` … `node = getattr(node, "prev", None)`) **before** advancing, so the returned tuple always contains the node it was handed; `::runtime_path_from_info` returns `()` only for `info is None`; `optimizer/walker.py::plan_optimizations` passes `runtime_prefixes=(… else (runtime_path_from_info(info),))` and omits `prefix`. `::_walk_selections`'s `runtime_prefixes=((),)` is a parameter default whose own docstring scopes it to "direct or test-only callers without `info`" and states `plan_optimizations` always passes an explicit single-tuple. The rewritten `:32` states exactly this, and agrees with `:127` |
| M2 — `spec:37` said the plan shapes survive an O6 downgrade | The lead-in now qualifies shape **and** count. The invariant it names — O4's dispatch — is true at source: `optimizer/walker.py::_dispatch_single_relation`'s docstring names its three deciders and only `prefer_prefetch` varies per site |
| M3 — two over-ticked boxes | Re-measured with my own script: **14 entries, 10 with `*Alternative rejected`, 14 with `*Claims the spec no longer makes`**. The *Claims* box is true at 14/14; the *Alternative rejected* box is restated and carries its measurement. Judged below |
| L1 — `spec:11`'s quantifier false for B6 | `optimizer/extension.py::DjangoOptimizerExtension.check_schema` constructs no plan; `optimizer/field_meta.py::FieldMeta` is upstream of one. The replacement names the planning **surface** (the plan, the planning type's field metadata, or both), which covers both |
| L2 / L3 — two wrong narrative counts | Superseded with commanded figures. Re-derived here: `grep -c 'rationale file\]\[spec-003-rationale\]'` -> **7**; the link-scaffold pass reports `spec-003-rationale` at **7** body uses, the same population from the other direction. `awk '/^## Reconciliation pass/,0' \| grep -c '^### '` -> **15** |
| L4 — the orphaned `## Plan shape` pointer | `:32`'s final clause now names the thing ("The pre-O4 dispatch shape, and where the shipped walker departed from it"), matching the five sibling pointers |
| L5 — `glossary-optimizerhint` inside a code span | `:98` now reads `` [`OptimizerHint`][glossary-optimizerhint]`.prefetch(obj)` `` — reference outside both spans. Per-anchor re-count below still returns exactly one body use |
| The self-reported sixth miscount ("10 status-language hits") | Superseded. My own sweep over the post-pass-2 spec returns **14** matching lines, each read individually; thirteen are runtime, in-document, or vocabulary uses and the fourteenth is `:194`'s literal `not yet implemented` rider text, which is R3's |

### Checklist audit (`### Dispatched findings checklist`)

Nineteen boxes, all `- [x]`. Every one audited against the files; none un-ticked, none silently left open, no deferral owed. Two are **restated universals rather than satisfied ones**, and both restatements are judged sound:

- **The *Alternative rejected* box (`:76`).** Accepted. `BUILD.md` `## Spec rationale extraction` asks each entry to carry "the alternatives rejected and why each lost" — a set, empty where nothing was in contention, not a quota. I read all four alternative-free entries (`### Same-query recursion`, `### B1 plan cache`, `### B8 queryset diffing`, `## Test plan`): they record a deleted "(already done)" parenthetical, an attribution to the wrong call site, a tense, and a set of tier/container corrections that `AGENTS.md` "Test through real usage" and `spec-035`'s finalize-to-tuple **decide** rather than weigh. Padding four manufactured alternatives would make the box's own evidence false and unfalsifiable by any later reader, which is a worse defect than the over-tick it would paper over. `ARTIFACT.md:52` bars an over-tick because a tick asserts a contract landed; it does not require a Worker-1-authored box's wording to be preserved when the honest statement carries its own measurement.
- **The "every stated count" box (`:88`) — restated at this pass.** It was an unqualified universal of the same shape and the item's own record refutes it: **six** figures were stated in this cycle without the command that produces them. It is not un-ticked, because the contract behind it did land — all six are superseded in place by a commanded figure, the sixth was self-reported before any reviewer raised it, and Worker 3's pass-2 re-derivation found no re-derivable figure wrong. The box now says what holds and names the six. Recorded under `### Spec changes made (Worker 1 only)` below as an artifact edit, not a spec edit.

### Relocation / carried-over-unchanged claims, proven here

Run myself rather than read from Worker 3's acceptance (`worker-1.md` `### Verifying relocation / promotion claims`).

- **The rescued R1 bullet at `spec:79` is byte-identical to R1's end state.** Reconstructed independently in a scratch path outside the repo from `docs/builder/bld-003-r1-rationale_move.md:850` (the blockquoted scope sentences, `> ` stripped) prepended with the instruction half quoted verbatim at `:852` and a `- ` list marker. `diff` against `sed -n '79p'` of the working tree: **identical, 778 bytes both sides** (`wc -c` on each). The bullet R1 pass 3 measured at 778 B is the bullet on disk; an R2-era rewrite of that section did not happen.
- **The spec diff is unchanged and the file appended nothing.** `git diff --stat` -> **78 insertions(+), 285 deletions(-)**; `wc -l` -> **240**. Both identical to pass 1's and pass 2's figures, including after this pass's own one-clause substitution, which rewrote an already-inserted line and added none.
- **No source landed.** `git diff --name-only -- django_strawberry_framework/ tests/ examples/` -> **0 files**; `git diff --stat` over the same paths is empty. Confirmed rather than assumed, so the "no boundary, no failability proof owed" claim rests on a measurement.

### The governing principle, read cold

I read the finished spec end to end as a first-time reader with no knowledge of the old version. **No sentence forces the present to be reconstructed by applying a chronology.** `grep -niE 'amendment|retract|as of (spec|review|round)|originally|used to |formerly|previously|no longer|superseded'` over the spec -> **no match**. There is no amendment block, no retraction paragraph, no "as of spec-NNN", no "originally this was X".

The seven backward-looking references that do survive are all `worker-1.md` `### Performing the rationale move` rule-1 companion pointers — the paragraph at `:3` plus per-section pointers at `:32`, `:74`, `:95`, `:113`, `:125`, `:196`. Each points **outward** at the rationale for deliberation; none narrates a change to the contract, and a reader who never opens the rationale loses no rule. The one that previously narrated the section's own former content (`:32`'s "this section quoted") is what L4 closed. `## Interactions with shipped beyond slices` uses "shipped" as a present-tense property of the B-slices, not as a chronology. `## Documentation updates when O4 ships` carries the one open obligation and is reserved to R3 by name.

### The spec is true — sampled against the symbols it names

Every claim re-derived from source, not from the report or from Worker 3's table.

| Spec line | Claim | Read at |
|---|---|---|
| `:32` | root Django prefix empty; root runtime path is the root field's response key; empty only for a caller with no `info`; a walker started from an empty path keys every elision one segment short | `plans.py::runtime_path_from_path` / `::runtime_path_from_info`; `walker.py::plan_optimizations`; `::_walk_selections` signature + docstring. **The highest-consequence claim in the cycle, and it now holds** |
| `:37` | shape and count both move for a downgraded single-valued link; O4's dispatch does not | `walker.py::_dispatch_single_relation` docstring (three deciders, only `prefer_prefetch` varies). Tightened this pass — see below |
| `:64` | one entry point, three deciders; nested connection is a third case recognized first | same docstring; `_walk_selections #"resolved[0] == \"connection\""` precedes the relation dispatch |
| `:85` | connector reverse arm covers reverse FK **and** reverse OneToOne | `join_taxonomy.py::_parent_join_column #"if getattr(field, \"one_to_many\", False) or kind == \"reverse_one_to_one\":"` — and its second/third arms match the forward-single-valued and M2M rows |
| `:89` | the lookup segment is the instance accessor | `walker.py::_plan_prefetch_relation #"lookup_path = f\"{prefix}{instance_accessor(django_field)}\""` |
| `:91` | `cacheable=False` set before the child queryset is built | `_plan_prefetch_relation` — `if has_custom_get_queryset: plan.cacheable = False` precedes the child build and the `related_model is None` early return |
| `:11` | all seven B-slices build on the plan, the planning type's field metadata, or both | `extension.py::DjangoOptimizerExtension.check_schema`; `field_meta.py::FieldMeta` |
| `:79` | the `attname` guard and the two routes into the prefetch branch | byte-identical to R1's measured end state, above; `walker.py::_record_relation_access` reads `getattr(django_field, "attname", None)` |

Nothing false found.

### Failability / fail-open

**None owed, and that is measured rather than assumed.** `git diff -- django_strawberry_framework/ tests/ examples/` is empty, so the item introduced no boundary, guard, gate, or rejection path and touched no expression on a decision path. There is no diff in which a fail-open shape could hide.

### Staged-anchor sweep

`grep -rEn 'TODO\(spec-003|TODO-(ALPHA|BETA|STABLE)-003' .` excluding `docs/shadow/`, `.git/`, `.venv/` -> **21 hits, zero staged anchors.** Decomposition, because the count alone reads as failure: all 21 are prose quotations of the token inside four `.md` files — the rationale (6, recording what the anchors were), this artifact (3), `bld-003-r1-rationale_move.md` (7), and the build plan (5). Independently: `grep -rEn` over `django_strawberry_framework/ tests/ examples/ scripts/` -> **0**; `grep -cE` over the spec -> **0**. A staged anchor is a source-site `# TODO(...)`; none exists and none ever did in source or tests.

### Verification commands, re-run and quoted

```
git rev-parse --short HEAD                                              -> 4d1c512a
uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-003-optimizer_nested_prefetch_chains-0_0_2.md
  -> OK: 8 terms - all have glossary entries and at least one spec link.    exit 0
uv run python examples/fakeshop/manage.py import_spec_terms --check
  -> OK: 49 done cards have glossary links.                                 exit 0
uv run python scripts/check_trailing_commas.py --check <spec> <rationale> <this artifact>
  -> exit 0   (all three)
git diff --stat -- django_strawberry_framework/ tests/ examples/           -> empty
```

All four re-run **after** this pass's own edits, not before.

**Per-anchor re-verification, not the green exit.** A script that partitions each file at `<!-- LINK DEFINITIONS -->`, parses the definitions, and counts `][ref-id]` uses in the body alone returns **exactly one body use for each of the eight**: `djangotype`, `fk-id-elision`, `metaoptimizer-hints`, `only-projection`, `optimizerhint`, `plan-cache`, `queryset-diffing`, `schema-audit`. Zero undefined references, zero unused definitions, zero definition targets missing on disk, in both files (spec **10/10**, rationale **19/19**, each target resolved from its own file's directory and `exists()`-checked). `docs/SPECS/appx/spec-003-…-terms.csv` is absent from `git status` — never opened. The 8-anchor constraint has zero margin and it holds per anchor, so card 3's DONE-card wrap chain is intact.

**In-page anchors.** An independent slugger over the post-pass spec reports **21 headings, 0 duplicate slugs**; the rationale's **9 anchor-bearing definitions** all resolve against real spec headings, `#plan-shape` included.

**`AGENTS.md` rule 27.** `grep -nE '[a-zA-Z_/]+\.(py|md):[0-9]+'` over the spec and the rationale -> **no match**.

### The eight R1 hand-off items, and what R3 inherits

**All eight dispositioned**, confirmed against R1's own on-disk list at `docs/builder/bld-003-r1-rationale_move.md:1413` (items 1-4 at `:157`, 5-6 at `:525`, 7-8 at `:949`) and against R2's disposition table. Items 1, 2, 3, 5, 6, 7 closed in the spec text; item 4 (the `spec-004` rider) deliberately untouched; item 8 answered "no" with the reason in the rationale's `## Standing notes`.

**R3's inheritance is legible on disk**, per `BUILD.md` `### Cohorting, naming, and closure` — checked in the files rather than in a return report:

1. **The `spec-004` rider edit** is named in the build plan's R3 line (`docs/builder/build-003-…:29`, pointing at `### The one authorized sibling-spec edit`), licensed by the surviving in-spec clause at `spec:194`, and carried in this artifact's two `### Notes for Worker 1 … carried into R3` sections. R2 correctly did not perform it. Three independent on-disk carriers.
2. **The `KANBAN.md` divergence needs the maintainer, not a silent reconcile.** Card `TODO-ALPHA-052-0.1.0` is on disk at `KANBAN.md:240` and `:317`; I read both. `:317` names four stale spec-003 sites of which three are now closed, **and prescribes a replacement for the fourth ("the replacement states that O4 is shipped and that its record is this spec's") that R2 deliberately rejected** — the rationale's `### \`## Problem statement\`` entry records the rejection and its reason. That is a genuine divergence between a board card's prescription and the spec's decided disposition, and it is a maintainer call. It is recorded in this artifact twice (Worker 3 pass-1 note 3, pass-2 note 4) and here a third time; Worker 0 must also carry it into R3's spawn prompt, because R3's *planning* pass is not obliged by `worker-1.md` `## Required reading` to read every prior artifact the way an integration or final pass is. **Neither R3 nor any worker reconciles this silently.**

### Deferred work carried to the final gate's catalog

- The ordering invariant at `### Same-query recursion` (`spec:70`) has **no automated guard** at HEAD — only `optimizer/walker.py::_record_relation_access`'s docstring and now the spec. Whether it earns a test is the maintainer's call.
- A forward `ManyToManyField` appends a field name rather than a column to the parent's `only_fields`. Harmless (Django drops it from the compiled `SELECT`), deliberately undocumented, recorded in the rationale's `## Standing notes`.
- `optimizer/plans.py::_prefetch_lookup_paths` recurses with no depth cap while `::runtime_path_from_path` is bounded at `_MAX_PATH_DEPTH = 1024`. Theoretical only; a maintainer note.
- **Package-wide:** should `scripts/check_spec_glossary.py` strip code spans in `REF_USE_PATTERN`? Spec-003 no longer depends on the answer (L5 closed it here), but every spec whose only carrier for an anchor sits in inline code does. Worth a repo-wide count before anyone changes it.
- The `KANBAN.md` card-052 divergence above, as a maintainer decision rather than a worker's reconcile.

### Summary

R2 reconciled `docs/SPECS/spec-003-optimizer_nested_prefetch_chains-0_0_2.md` against HEAD: all 22 drift rows re-verified true, nine further falsified claims found beyond that floor and restated, one section renamed, one deleted with both rejected alternatives recorded, and 19 rationale entries keyed to the spec sections they explain. The spec ends at **240 lines / 28,634 bytes** across `78 insertions(+), 285 deletions(-)`; the rationale at **1,035 lines / 72,449 bytes**. No package source, test, sibling spec, terms CSV, or generated doc was touched.

The spec now states a contract and never narrates its own history — the maintainer's twice-stated instruction, verified by a cold end-to-end read and by a chronology-token sweep that returns nothing. Its highest-consequence sentence, the walker/resolver runtime-path protocol at `:32`, is the corpus's only statement of that protocol and is now correct at source.

`Status: final-accepted`.

### Spec changes made (Worker 1 only)

One spec edit and its rationale entry, plus one artifact-checklist restatement. Cited against the post-final-verification spec; the line numbering is unchanged (this pass rewrote one existing line and added none, `wc -l` -> 240 before and after).

| Location | Change | Reason |
|---|---|---|
| `spec:37` | "A type that does is downgraded by O6, and that link leaves the `select_related` chain for a `Prefetch` of its own — so both the shape and the count change for it." -> "A **single-valued link** to a type that does is downgraded by O6 and leaves the `select_related` chain for a `Prefetch` of its own, so both the shape and the count change for it." | Worker 3's L-a, recorded and intentionally rejected rather than looped. Acted on rather than accepted: only a single-valued link is ever *in* the `select_related` chain (`spec:22`; `walker.py::_plan_select_relation` is that branch), so read strictly over the two many-side worked examples the clause described a move that cannot happen there. Three words, no contract changed, mechanically checkable, and the spec outlives the cycle's catalog. Worker 3's judgement that no reader is misled — the governing first sentence scopes the whole block — is why this was **not** grounds for `revision-needed` |
| rationale `### \`## Desired behavior\`` | Appended a *Changed again, in the final-verification pass* paragraph, an *Alternative rejected* (leave it and defer), and a fourth retired claim | `worker-1.md` `### Performing the rationale move` rule 4 makes the file append-only against a **later round**, not against this item's own custodian passes — the R1 and pass-2 precedent, both accepted in review. The entry's prior text is narrowed, not falsified, so it is appended to rather than corrected in place |
| artifact `### Dispatched findings checklist` `:88` | The "every stated count" box restated to what holds, naming the six uncommanded figures and where each is superseded | An unqualified universal the item's own record refutes — the same over-tick shape as the *Alternative rejected* box, and `ARTIFACT.md` puts the box audit in exactly this pass. Not un-ticked: the contract behind it landed, since all six are superseded in place by a commanded figure and the sixth was self-reported |

**Post-edit re-verification, all four commands re-run after the last edit:** `check_spec_glossary` exit 0 (`8 terms`), `import_spec_terms --check` exit 0 (`49 done cards`), `check_trailing_commas --check` exit 0 on all three files, `git diff --stat -- django_strawberry_framework/ tests/ examples/` empty. `git diff --stat` on the spec still **78 / 285**; `wc -l` still **240**; `sed -n '79p' | wc -c` still **778**; all eight glossary anchors still at exactly one body use; rationale entry fields still **14 / 10 / 14**; zero undefined or unused link definitions and zero missing targets in either file.
