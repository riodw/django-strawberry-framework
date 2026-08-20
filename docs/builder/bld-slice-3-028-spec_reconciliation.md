# Build: Slice 3 — Spec reconciliation

Spec reference: `docs/SPECS/spec-028-orders-0_0_8.md` (whole file; 1,153 lines / 224,759 bytes at entry) plus its rationale companion `docs/SPECS/appx/spec-028-orders-0_0_8-rationale.md` (594 lines / 98,821 bytes at entry).
Status: final-accepted

## Plan (Worker 1)

### Worker-1-only artifact shape

This slice has no Worker 2 / Worker 3 cycle — the build plan's `Ownership partition: none; sequential slices` line assigns Slices 1 and 3 to Worker 1 alone. So the planning, the work, and the final verification all happen in one spawn, and this artifact carries `## Plan (Worker 1)` and `## Final verification (Worker 1)` with no `## Build report` / `## Review` between them (the shape Slice 1 used). Every `[ ]` box in `### Spec slice checklist (verbatim)` below is therefore ticked by the same worker that audits it, so each tick names the measurement it was derived from rather than resting on a builder's report.

### What this slice is, in one paragraph

`docs/SPECS/spec-028-orders-0_0_8.md` describes a subsystem that shipped in full and then **grew**. Slice 1 moved the deliberative layer out (D1, D2). This slice rewrites the surviving contract prose so the spec states what HEAD actually does — build-plan findings **D3 through D16** plus five further findings routed here after the plan was written. Two rules govern every edit: (1) the spec states the corrected contract **directly**, with no amendment block, no "superseded" annotation, no chronology a reader must apply; (2) what changed and why goes in the rationale companion, keyed to the Decision by heading and anchor. Where HEAD and the spec disagree, HEAD wins.

### Precondition census — the protect-list, measured at entry, three instruments

Timestamped `2026-08-20T15:40:34Z`, run from the repository root over every non-`.venv` `*.py` in the tree. **No figure was read out of a prior artifact**; the Slice-2 handoff instruction was explicit that its own numbers are a timestamped observation, not a contract.

| Population | A: line-scoped `[ \t]` | B: whitespace-flattened `\s` | C: join-aware (`\n` inside the match) |
| --- | --- | --- | --- |
| `spec-028` | 91 | 91 | 0 |
| `spec-028 Decision N` | 62 | 62 | 0 |
| `spec-028 DoD N` | 2 | 2 | 0 |
| `spec-028 test plan` | 6 | 6 | 0 |
| `spec-028 Edge cases` | 1 | 1 | 0 |
| `spec-028 Slice checklist` | 0 | 0 | 0 |

All three instruments agree at every class, and instrument C reads 0 everywhere, so **no `spec-028` citation is wrapped across two source lines at entry** — Slice 2 closed the two joins it found. Instrument A is the control the cycle's R4 lesson demands: `[ \t]` cannot cross a newline, where `\s` can, so A and B are provably different instruments rather than one written twice.

**Which anchors the 71 heading-bearing citations depend on**, enumerated rather than counted:

- `### Decision 2` (3), `### Decision 3` (5), `### Decision 5` (10), `### Decision 6` (7), `### Decision 8` (16), `### Decision 9` (11), `### Decision 11` (4), `### Decision 12` (4), `### Decision 13` (2) — 62 total. Decisions 1, 4, 7 and 10 carry no `.py` citation but their headings are still in-page anchor targets.
- `## Test plan` (6).
- `## Definition of done` (2 — both `spec-028 DoD 4(c)`, in `django_strawberry_framework/orders/sets.py`). **There is no `### DoD` heading**; the anchor is the `## Definition of done` heading, and both citations resolve against DoD **item 4(c)** ("NO `apply(...)` dispatcher"), so item 4's `(a)`-`(e)` sub-lettering is load-bearing and must survive.
- `## Edge cases and constraints` (1, `django_strawberry_framework/orders/inputs.py`).

**Nineteen files** carry a `spec-028` citation: `orders/sets.py` (18), `orders/inputs.py` (16), `utils/inputs.py` (7), `types/finalizer.py` (6), `orders/__init__.py` (6), `orders/factories.py` (5), `orders/base.py` (5), `tests/orders/test_base.py` (4), `examples/fakeshop/apps/library/orders.py` (4), `tests/orders/test_finalizer.py` (3), `tests/orders/test_composition.py` (3), `examples/fakeshop/test_query/test_glossary_api.py` (3), `tests/orders/test_inputs.py` (2), `examples/fakeshop/test_query/test_library_api.py` (2), `examples/fakeshop/apps/library/orders_genre.py` (2), `sets_mixins.py` (2), `tests/types/test_base.py` (1), `tests/test_sets_mixins.py` (1), `tests/test_registry.py` (1).

**The constraint this puts on the slice: rename no heading.** Every `### Decision N` heading, `## Test plan`, `## Definition of done`, `## Edge cases and constraints`, and `## Slice checklist` keeps its exact current text, and DoD item 4 keeps its sub-lettering. `scripts/check_citations.py` resolves `path::Symbol` only and `docs/` is outside its scope, so nothing in the repo would report a break. Rewording the prose **inside** a section is safe; touching the heading is not. Everything below is a body edit.

### Gate preconditions, measured

- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-028-orders-0_0_8.md` -> `OK: 44 terms - all have glossary entries and at least one spec link.` exit 0.
- `uv run python scripts/check_citations.py` -> exit 0, `OK: 782 citations resolve (705 in 422 .py files, 77 in KANBAN.md)`. The absolute number is unstable under the concurrent `spec-027` cohort; exit 0 is the criterion.

### DRY analysis

- **Helper inventory checked.** Not applicable as a code-planning step: this slice changes no `.py` file and proposes no helper. What replaces it is a **source-of-truth inventory** for every claim the rewrite makes — each edit below cites the HEAD symbol it was read from, and the claim was read out of the source rather than out of the build plan's summary of it. That inventory found two build-plan findings partly wrong (see `### Findings re-derived, and where the input contract was wrong`), which is exactly what the step is for.
- **Existing patterns reused.** The rationale companion's existing per-Decision `### Claims this Decision may no longer make` sections are the landing sites for the "what changed and why" half; no new section shape is invented. The spec's existing `Rationale companion` pointer lines, one per Decision, already resolve through the `rationale-dN` reference ids Slice 1 added, so no new pointer scaffolding is needed.
- **New helpers justified.** None. Two new rationale sub-sections (`### Corrections this Decision received after ship`) are added only under Decisions that received one, reusing the file's existing `###`-under-`##` grain.
- **Duplication risk avoided.** The single real risk is stating the same correction in both files — which is the one thing the maintainer's rule forbids. The discipline: the **spec** gets the corrected contract sentence and nothing about the change; the **rationale** gets what the claim used to be, when it moved, and why, and never restates the new contract beyond the clause needed to identify it.

### Boundary count, and the split question answered in writing

**Zero.** This slice edits two Markdown files and changes no executable statement, so it adds no guard, cap, rejection path, or validation branch. No failability proof is owed — and that is by **entitlement**, not omission: `BUILD.md` `## Failability proofs` scopes the obligation to new boundaries, and there are none. A reader finding no proof section should read it as "none was owed", which is why this paragraph exists.

Split question, answered: **one unit.** The findings are not independent — D4 (`check_permissions` deleted) and D5 (mechanics moved to the shared substrate) touch the same four sentences; D8 (pre-validation) and D9 (queryset model) both rewrite `_resolve_order_expressions`'s description; D10's four sites and D12's `14` census both live in the Test plan, Decision 13, the Implementation-plan table and the quoted KANBAN body. Splitting would put two halves of one sentence in two slices.

### Hot-path declaration

None. This slice edits Markdown only; nothing runs per request, per resolver, per row, or per outbound message.

### Floor verification

None. No slice in this build touches a Django / Strawberry / channels integration seam, and this one changes no executable statement. (Reference only, from `docs/builder/BUILD.md` `## Floor verification`: Django 5.2.16 on Python 3.10 with strawberry-graphql 0.316.0.)

### Findings re-derived, and where the input contract was wrong

Every finding was re-measured against HEAD before being written into the spec. Three came back different from the build plan.

1. **D11's first sub-claim is half wrong.** The build plan says Decision 8 step 4 asserts the position-side-channel leak is called out by both the `OrderSet` and the `RelatedOrder` GLOSSARY entries and that "neither entry mentions a side channel, a leak, or a position inference." At HEAD the **`RelatedOrder` entry does** — `docs/GLOSSARY.md` carries a paragraph opening `Position-side-channel note:` under `## `RelatedOrder``, naming the parent-side `check_<branch>_permission` gate as the consumer defense. Only the `OrderSet` half is false. So the spec's sentence is false because of one of its two subjects, and the corrected sentence must name `RelatedOrder` alone rather than dropping the claim entirely. (D11's second and third sub-claims re-derive as stated: the `RelatedOrder` entry says nothing about multiplicity, and the `OrderSet` entry documents three contracts `## Doc updates` never names.)
2. **Decision 10's stale claim is larger than "a dated CHANGELOG claim".** The build plan flags the closing sentence "Release-heading promotion ... had not happened as of this spec's writing". At HEAD `CHANGELOG.md` carries `## [0.0.8] - 2026-06-03` — the promotion **has** happened — and there is no `[Unreleased]` heading at all, while `pyproject.toml` and `django_strawberry_framework/__init__.py::__version__` both read `0.0.14`. So three sentences are stale, not one: the closing sentence, the same Decision's "the package's version files already read `0.0.8`", and the spec opener's / `Status:` line's assertions that the Ordering bullets sit under `[Unreleased]`. All are dated snapshots of a moving file, and all three are in scope.
3. **The `14` census is 11 sites over 10 lines, not 14 or 13.** Measured on `\b14\b` in the spec at entry: lines 70, 814, 827, 829, 873, 892, 909, 943, 950, 1007, 1008 — 11 occurrences over 10 lines (1007 and 1008 are DoD items 15 and 16 adjacent, and 1007's `14` is `DoD item 14`, a cross-reference, not a test count). Slice 1 removed the `Status:`-line site; the build plan's 14 and Slice 1's revised 13 were both counting a population that has since moved. **This is the third time this cycle a handed-down count was right in its digits and wrong in its subject**, so the rewrite states the count with its subject attached every time it appears.

Two further findings were routed here after the plan was written and both re-derive as stated: Decision 3's quoted `"__all__"` expression (HEAD's `orders/inputs.py::_get_concrete_field_names_for_order` uses `getattr(f, "column", None) is not None`, a **stronger** guard than the spec's `hasattr(f, "column")`, because Django's virtual `GenericRelation` / `GenericForeignKey` descriptors expose `column = None` and `hasattr` alone admits them — the code's own docstring gives that reason), and Decision 5's `Ordering.resolve` example (HEAD routes the ASC/DESC discrimination through a new `Ordering.is_ascending` property using `self.name.startswith("ASC")`, a prefix test rather than the spec's `"ASC" in self.name` substring test, and that property has a **second consumer** the spec names nowhere — `OrderSet._resolve_order_expressions` uses it to pick `Min` vs `Max` for a to-many term).

And one finding of the same class as D5 that no prior pass named: **Decision 11's fenced `order_input_type` body is a stale spelling too.** At HEAD `orders/__init__.py::order_input_type` delegates to `utils/inputs.py::build_lazy_input_annotation`, shared with `filters/__init__.py::filter_input_type`; the eager validation, the ledger write, and the `Annotated[<runtime str>, strawberry.lazy(...)]` construction all live in the shared helper. Decision 6 is the same story at a different grain: `_bind_ordersets()` and `_bind_filtersets()` both delegate to `types/finalizer.py::_bind_sidecar_sets` driven by a `_SidecarBindingSpec`, and the shared driver carries a **subpass 2.5** (unregistered-related-target audit) that is filter-only for orders (`post_expand_audit=None`). Both are recorded and both are corrected.

### Implementation steps

Line numbers are pin-at-write-time navigational hints; every edit is applied as a **count-asserted exact-string replacement** so a shifted line cannot mis-target it, and the whole run aborts on any count mismatch. That is the Slice-1 method, adopted here for the same reason: the file renumbers under its own edits, so line anchors are worthless mid-run.

**Header and state lines (per-spawn status-line re-verification).**

1. Spec opener (line 3) — the version-boundary sentence. Replace the dated reconciliation ("The package's `0.0.8` version-file values ... and the `CHANGELOG.md` `__version__` note were set under the maintainer's separate explicit release command") with the durable contract: this card shipped inside the `0.0.8` line and never touched a version file; the `0.0.8` version values and release heading landed under separate maintainer release commands; the package has moved on past `0.0.8` since.
2. `Status:` line (line 4) — `CHANGELOG.md` carries the Added and Changed bullets "under `[Unreleased]`" is false at HEAD (they sit under `## [0.0.8] - 2026-06-03`; no `[Unreleased]` heading exists). State the shipped location.

**Key glossary references (D16).**

3. Lines 14, 17, 18 — three bullets read `(planned for 0.0.8)` as present fact for `OrderSet`, `RelatedOrder`, `Meta.orderset_class`. Flip to `shipped (0.0.8)`. **The other 11 `planned for 0.0.8` occurrences stay**: the Predecessors line, the Pre-implementation baseline, and the Slice-5 / Doc-updates flip-this instructions all use the phrasing correctly. Keep every glossary link intact — `check_spec_glossary.py` needs one spec link per CSV term.
4. Line 47 — the `docs/TREE.md` convention bullet says the target-layout section "already names the directory; this card flips it from `[alpha]` to on-disk." State the shipped fact: `orders/` sits in the current-on-disk block.

**Slice checklist (D3, D10, D12, D16).**

5. Sub-bullet under Slice 3 (line 66) — `registry.clear()` "invokes `clear_order_input_namespace()` AND clears `_helper_referenced_ordersets` so ... share one entry point". At HEAD both clear through their own `register_subsystem_clear` row, replayed by `TypeRegistry.clear` via `iter_subsystem_clears()`. Restate on the registration seam.
6. Sub-bullet under Slice 4 (line 70) — "**exactly 14 new live `/graphql/` HTTP tests**" and the reverse-FK clause carrying a `(**superseded**: ...)` chronology block. Replace with the shipped count **stated with its subject** (16 test functions / 19 test rows) and the row-preserving aggregate contract stated directly; name the two post-ship additions; delete the chronology.
7. Sub-bullet under Slice 5 (line 74) — "List the five new files" against `docs/TREE.md`'s four described files (`build_tree_md.py` omits `__init__.py`).
8. Sub-bullet under Slice 5 (line 78) — the pre-archive path `docs/spec-028-orders-0_0_8.md`.
9. Sub-bullet under Slice 5 (line 79) — the CHANGELOG instruction's `[Unreleased]` target.
10. Sub-bullet under Slice 6 (line 82) — "One package-internal test" against HEAD's two (`test_filter_and_order_compose_through_finalizer_and_apply_pipelines`, `test_filter_and_order_share_lazy_related_class_mixin_via_neutral_module`).

**Pre-implementation baseline.**

11. Line 100 — drop the "and the five planned files" clause. The section is an explicit pre-Slice-1 snapshot, so it must not acquire HEAD facts; the file-count claim is dropped rather than restated, and the shipped-state statement lands in `## Doc updates` and the DoD where it belongs.

**Borrowing posture (D4, D14).**

12. The `AdvancedOrderSet.check_permissions -> port verbatim` bullet — `OrderSet` ships no `check_permissions`. Restate on the shipped classmethod pipeline inherited from `sets_mixins.py::ActiveInputPermissionMixin`.
13. The strawberry-django `ORDER_ARG` / `ORDERING_ARG` bullet's closing sentence "Constant name in the package: `ORDER_BY_ARG = "orderBy"`". **Worker 0 recommended correcting the spec rather than shipping a dead constant; I concur and rule that way** — `git log --oneline -S'ORDER_BY_ARG' --all` hits only the two spec-draft commits, nothing needs it, and Strawberry derives `orderBy` from the resolver's `order_by` parameter by auto-camel-case. Same YAGNI judgement Decision 2 already records for the dropped `apply()` dispatcher and Decision 12 for Layer 6. State that the package ships no argument-name constant and why it needs none.

**User-facing API (D7, D8).**

14. `### Per-field permission gates` — add the shipped constraint that the hook must be a plain `def`. An `async def check_<field>_permission` is **rejected**, not awaited.
15. `### Error shapes` bullet 1 — "at type-creation time" is the wrong time. The `Meta.fields` raise lands at finalize phase-2.5 subpass 2 (Decision 3 Layer 3 is explicit the metaclass does not expand), and the path is pre-validated by `utils/relations.py::classify_path`.
16. `### Error shapes` — add the async-gate rejection (`SyncMisuseError`), which the list does not name.
17. `### Error shapes` bullet 3 (`Meta.orderset_class = NotAnOrderSet`) — this one **is** type-creation time (`_validate_meta`); left alone deliberately so the two timings read as the different things they are.

**Decision 2 (D3, D4, D5).**

18. The `sets.py` bullet — drop `check_permissions` from the member list; name the inherited classmethod pipeline.
19. The `base.py` bullet — `RelatedOrder`'s direct base is `sets_mixins.py::RelatedSetTargetMixin` (itself a `LazyRelatedClassMixin` subclass), which owns `_bind_owner` / `_resolved_target` / `_set_target`.
20. The `inputs.py` bullet — name where the mechanics live: `FieldSpec` / `build_input_class` / `_input_type_name_for` / `_iter_orderset_subclasses` are one-line aliases of `utils/inputs.py::GeneratedInputFieldSpec` / `::build_strawberry_input_class` / `::set_input_type_name` / `::iter_set_subclasses`, and `materialize_input_class` / `clear_order_input_namespace` are thin wrappers over `utils/inputs.py::make_set_input_namespace`. Every spec-named name still resolves from `orders.*`, deliberately — this is a where-the-mechanics-live statement, not a surface break.
21. The `__init__.py` ledger bullet — "as **two separate blocks** (one block per module)" describes the retired shape. Two `register_subsystem_clear` rows (`orders.input_namespace`, `before_bind=True`; `orders.helper_references`).

**Decision 3 (D5, plus the `"__all__"` finding).**

22. Layer 2 — `RelatedSetTargetMixin`.
23. Layer 3 — metaclass collection is `sets_mixins.py::collect_related_declarations`.
24. Layer 4 — the cache/guard is `sets_mixins.py::expanded_once` / `::should_cache_expansion` plus a class-level `SetLifecycleAttrs`; the slot names `_expanded_fields` / `_is_expanding_fields` survive at HEAD and stay named.
25. Layer 5 — `_ensure_built` and `_build_class_type` have **zero** occurrences under `orders/`. The BFS lives on `utils/inputs.py::GeneratedInputArgumentsFactory` and the subclass declares `_build_input_triples` plus class-level config.
26. The `Meta.fields = "__all__"` scope paragraph — state HEAD's expression and the stronger guarantee it buys. The cookbook's `hasattr(f, "column")` stays quoted as the **cookbook's** code; the package's line becomes `getattr(f, "column", None) is not None and not getattr(f, "many_to_many", False)`, with the virtual-descriptor reason. **This paragraph is `spec-028 Decision 3`'s citation target for `orders/inputs.py` and one of Slice 2's C2 replacement targets, so the `### Decision 3` heading is untouched and the paragraph keeps its `"__all__"` scope subject.**

**Decision 5 (the `Ordering.resolve` finding).**

27. The fenced `inputs.py` code block — replace with HEAD's shape: module-level `F` / `OrderBy` imports, the `is_ascending` property with the prefix test and its reason, and `resolve` routed through it. Name the second consumer (`OrderSet._resolve_order_expressions`'s `Min` / `Max` pick). Delete the two stale copy-paste comments about local-vs-top-of-file imports, which describe a shape the file does not have.

**Decision 6 (D3, D5).**

28. The opening sentence — `_bind_ordersets()` and `_bind_filtersets()` both delegate to `types/finalizer.py::_bind_sidecar_sets` driven by a `_SidecarBindingSpec`; the shared driver carries a filter-only subpass 2.5 that orders opt out of (`post_expand_audit=None`).
29. Subpass 4's closing `registry.clear()` sentence — the registration seam (same correction as step 5).

**Decision 8 (D4, D5, D6, D7, D9, D11, D13).**

30. Step 4's closing GLOSSARY sentence — name `RelatedOrder` alone (re-derivation 1 above).
31. Step 6 — delete the instance-method-delegate parenthetical and its cited test `test_orderset_check_permissions_instance_method_delegates` (**0** occurrences anywhere but the spec). Name the mixin home for `_run_permission_checks`.
32. Step 6 — add the async-gate rejection with its reason (an un-awaited coroutine is truthy, so an intended denial would become an authorization **bypass**), via `utils/permissions.py::invoke_permission_method` -> `reject_async_in_sync_context` -> `SyncMisuseError`.
33. Step 6's dedup-contract paragraph — the `_fired` map and the double-dispatch walk live on `sets_mixins.py::ActiveInputPermissionMixin`, delegating to `utils/permissions.py::invoke_permission_method`; `OrderSet` inherits them and configures via a class-level `ActiveInputPermissionAttrs`.
34. Step 6's "Tests pin the contract" list — all four named package tests have **0** occurrences repo-wide. Replace with the tests that exist: `tests/utils/test_permissions.py::test_run_active_input_permission_checks_double_dispatch_and_dedup` (the family-neutral double-dispatch-plus-dedup contract), `tests/test_sets_mixins.py` (the family wiring, including `::test_permission_facade_methods_are_single_sourced_on_the_mixin`), and the order-side residue in `tests/orders/test_sets.py` (`::test_orderset_check_permission_dedups_repeated_list_entries`, `::test_orderset_inactive_input_does_not_resolve_lazy_related_target`). The live gate test named at the end of the bullet exists and stays.
35. Step 7 — the path resolves against **`queryset.model`**, not `Meta.model`, so a model-less `OrderSet` is legal; every resolved path is pre-validated by `classify_path`; a to-many term is ordered by a `Min` / `Max` aggregate over an annotation alias rather than the raw fan-out path. Also: "**The instance** applies `queryset.order_by(...)`" is wrong about the receiver — it is a classmethod chain.
36. The `apply_async` paragraph — the boundary is `utils/querysets.py::run_in_one_sync_boundary`, not a literal `sync_to_async(..., thread_sensitive=True)` call site. The behavioral claim (one worker, `thread_sensitive=True`, parsing deliberately unwrapped) survives; the named mechanism does not. The cited test `::test_orderset_apply_async_runs_check_permission_in_sync_to_async` **does** exist and stays.

**Decision 9 (D3).**

37. The `Import-cycle-safe integration` bullet and its fenced ~59-line `registry.py` block — the whole shape is retired. `TypeRegistry.clear` carries **no** `except ImportError` guard for either subsystem; it replays `for clear in iter_subsystem_clears(): clear()`. Replace the fence with the registration seam: `registry.py::register_subsystem_clear` / `::iter_subsystem_clears`, the two order-side rows and their owners, and why a callable registration cannot silently drift the way an attribute reference can. The subprobe test claim (`registry` imported alone) survives and its real home is named.
38. The `clear_order_input_namespace()` bullet's closing sentence — "symmetric `pass` + `else:` blocks (no `return`) so a future-added fifth clear phase is not silently skipped" describes the retired shape's footgun fix. The registration seam makes it structurally impossible instead.
39. The `_helper_referenced_ordersets` separate-block bullet — same correction as step 21; the two-ledger separation survives as a contract, its mechanism changes.

**Decision 10 (re-derivation 2).**

40. The reconciliation paragraph and its closing sentence — three stale sentences, all dated snapshots. State the durable contract and the boundary without asserting today's `CHANGELOG.md` / `pyproject.toml` state as though it were frozen.

**Decision 11 (the shared-substrate finding).**

41. The fenced `order_input_type` body — replace with HEAD's delegation to `utils/inputs.py::build_lazy_input_annotation`, keeping every normative clause the block carried (element type not list type, eager `TypeError`, the ledger write, and the `ForwardRef`-wrapped `Annotated[<runtime str>, strawberry.lazy(...)]` form `LazyType.resolve_type` requires — that last one is implementation-relevant rationale and **stays in the spec** under `BUILD.md`'s carve-out).

**Decision 13 (D10, D12).**

42. "(14 tests total)" and "reverse-FK relation order with denormalized-multiplicity asserted" — the count with its subject, and the row-preserving aggregate. This is one of D10's four surviving sites.
43. The `tests/orders/` sentence — "**7 files total**" is correct at HEAD and stays; it is the Test-plan preamble that disagrees with it.

**Implementation plan table (D10, D12, D16).**

44. Slice 1 row — `check_permissions` in the new-tests cell.
45. Slice 4 row — `14 (... reverse-FK relation with denormalized-multiplicity asserted ...)`. D10's third site.
46. Slice 6 row — `New tests = 1` against HEAD's two.

**Edge cases and constraints (D8).**

47. The `Meta.fields = "__all__"` bullet — state the shipped guard, and delete the closing chronology "the prior revisions' 'relations are NOT included' framing was incorrect against the cookbook helper's actual behavior."
48. The "Order that raises a Django ORM error at queryset-translation time" bullet — "the framework does not pre-validate the backend's supported expressions" is false for a bad path. It **is** pre-validated, as a `ConfigurationError` rather than a Django `FieldError`. The genuinely-unvalidated residue (a backend that cannot execute an expression it accepted) survives and is stated as the narrower claim it is.
49. The "`Meta.fields` referencing a model property" bullet — "Rejected at type creation" is the wrong time, same as step 15.
50. The circular-cycles bullet — keeps `_is_expanding_fields` (the slot name survives at HEAD) and gains the shared-substrate home.

**Test plan (D10, D11, D12, D13, D16).**

51. The preamble "Tests live in two trees" — name the trees instead of counting them, and include the two the shared-substrate move added (`tests/utils/`, `tests/test_sets_mixins.py`).
52. The `tests/orders/` subsection's "Five files mirror the source layout" against the seven Decision 2, Decision 13 and DoD item 11 all state (seven is correct).
53. The `test_sets.py` bullet — `check_permissions` -> `_run_permission_checks`; the two named split-pair package tests do not exist (their live counterparts do, under different names).
54. The `test_finalizer.py` bullet — `test_registry_clear_works_without_orders_imported` lives in `tests/orders/test_inputs.py`, not here.
55. The `test_library_api.py` subsection header "**Exactly 14 new live HTTP tests**" -> 16 functions / 19 rows, subject attached.
56. The `test_library_books_order_by_subtitle_desc_nulls_last` bullet — **0** occurrences at HEAD. The contract ships parametrized as `test_library_books_order_by_subtitle_null_positioning` over four NULLS directions, and those four rows are the whole 19-vs-16 delta.
57. The `test_library_branches_order_by_reverse_fk_relation` bullet — D10's dominant site, carrying **three** retired claims in one bullet ("assert the response carries Alpha three times"; "Pinning the multiplicity ... catches a future regression where the runtime accidentally `.distinct()`s the queryset"; "The `RelatedOrder` GLOSSARY entry calls out this multiplicity"). The shipped test asserts `names == ["Alpha", "Beta"]`. The third claim is also D11's second sub-claim and **must not** be repointed at another entry — the multiplicity no longer occurs, so no entry should document it.
58. Add the two post-ship live tests the spec names nowhere: `test_library_branches_order_by_scalar_then_to_many_aggregate_no_multiplication` and `test_library_genres_connection_pages_by_to_many_aggregate`, attributed to the contract they pin rather than to this card's plan.
59. The closing "All 14 new live HTTP tests reuse the existing `_reload_project_schema_for_acceptance_tests` fixture at `test_library_api.py::_reload_project_schema_for_acceptance_tests`" — wrong count and wrong home. The fixture is defined at `examples/fakeshop/test_query/conftest.py`.
60. The `[fakeshop-test-library-reload]` link definition, which resolves to the same path as `[fakeshop-test-library]` — repoint at `conftest.py` so the two defs name two files.

**Doc updates (D11, D16).**

61. The GLOSSARY `OrderSet` bullet — add the three contracts the shipped entry documents and this block does not name: the `Min` / `Max` row-preserving aggregate, the root connection's deterministic pk tiebreaker over the grouped queryset, and the deliberate nested-relation-connection `orderBy:` bypass of window/lateral planning.
62. The GLOSSARY `RelatedOrder` bullet — add the position-side-channel note the shipped entry carries (the half of D11 that is true).
63. The `docs/TREE.md` bullets — "Test layout going forward" does not exist; the headings are `## Test layout`, `### Current test trees`, `### Target test shape`. And the five-file list is four described files.
64. The quoted KANBAN past-tense body — four retired claims: `check_permissions`, "exactly 14 live HTTP tests", "reverse-FK with denormalized-multiplicity-pinned" (D10's fourth site), and the pre-archive spec path. Corrected in the spec; **`KANBAN.md` itself is out of this cycle's scope and still carries all four**, which goes to the deferred catalog.
65. The quoted CHANGELOG bullets — the `14` count, the pre-archive path, and the `[Unreleased]` heading.

**Risks and open questions.**

66. The terms-CSV bullet — the pre-archive `docs/spec-028-orders-0_0_8-terms.csv` path is now `docs/SPECS/appx/`, and the "headings exist with `planned for 0.0.8` status so the gate stays green before implementation" clause is a plan-time statement reading as current.

**Definition of done.**

67. Item 1 and item 17 — the pre-archive spec and terms-CSV paths; **item 17's quoted `check_spec_glossary` command would fail as written**, so the quoted command gets the real path.
68. Item 4(b) — `queryset.model`, `classify_path`, the aggregate. **Item 4's `(a)`-`(e)` sub-lettering is preserved exactly**; two `.py` citations resolve against `4(c)`.
69. Item 4(e) — drop `check_permissions` from the member list.
70. Item 10 — the `registry.clear()` seam, and `_bind_sidecar_sets` as the shared driver.
71. Item 11 — "five mirror files ... plus `test_finalizer.py` and `test_composition.py`" reads as five where every sibling site says seven. State seven.
72. Item 13 — seven ordersets in `orders.py` (the five named plus `PeriodicalOrder` / `IssueOrder`, the keyset-cursor `orderBy:` substrate), and `orders_genre.py::GenreOrder` additionally declaring `books = RelatedOrder("apps.library.orders.BookOrder")` — a second absolute-import-path form. `BookOrder.loans` and `ShelfOrder.books` are named too.
73. Item 14 — **eight** `Meta.orderset_class` wirings, not six (`Loan`, `Book`, `Shelf`, `Genre`, `Branch`, `Patron`, `Issue`, `Periodical`). Six root resolvers carry `order_input_type(...)`, which matches and stays six.
74. Item 15 — "**exactly 14**" -> 16 functions / 19 rows.
75. Item 18 — the `docs/TREE.md` section name.
76. Item 22 — the spec path form.

**Rationale companion (append-only during the build).**

77. Add a `### Corrections this Decision received after ship` sub-section under each Decision the rewrite corrected (2, 3, 5, 6, 8, 9, 10, 11, 13), each entry naming **what the Decision claimed, what HEAD does, and why the shipped shape is the one that is right** — keyed to the spec Decision by heading and by the existing `[spec-028-dN]` anchor, so an entry can be looked up.
78. Extend `## Claims the spec may no longer make` with the spec-wide corrections that belong to no single Decision (the Test plan's, the DoD's, the Doc-updates block's, the tail sections').
79. Replace `## Handed to Slice 3` with a `## Discharged by Slice 3` record: what was corrected, what was deliberately left, and the two things a later reader must not re-derive as new rot.
80. Every rewritten link definition is disk-exists-checked, both files keep exactly one link-definitions delimiter and all 10 canonical group headers in order and alphabetical within group, and the rationale file's paths stay one level deeper (`../../` vs `../`).

### Test additions / updates

None. This slice adds and changes no test. The tests named in the spec are re-derived against HEAD (`### Findings re-derived` above and the checklist audit below) but no test file is touched — every `.py` in the tree is on the do-not-touch list, and Slice 2 owned all code correction.

### Implementation discretion items

None to delegate — this is a Worker-1-only slice, so there is no builder to delegate to. Two choices I assessed and decided rather than leaving open:

- **D14's call.** Correct the spec; do not ship the constant. Ruled in step 13 with the reason.
- **The quoted-KANBAN-body question.** A block whose text asserts a retired contract is the spec asserting it, whichever quotation marks surround it, so the quoted body is corrected in the spec and the `KANBAN.md`-side drift is routed to the deferred catalog rather than left as a silent divergence. Ruled in step 64.

### Spec slice checklist (verbatim)

This is a residual-reconciliation cycle, not a fresh build: the spec's `## Slice checklist` describes the six slices of the **original** card, all six shipped and ticked, and copying it here would audit the wrong thing. `docs/builder/BUILD.md` `### Dispatched findings checklist` gives the substitute shape for a pass with no spec slice checklist of its own, so the boxes below are **one per finding this slice was dispatched with** — D3 through D16, plus the five later findings — in the same position and under the same tick-and-audit discipline.

- [x] **D3** — Decision 9's `registry.clear()` integration and its ~59-line fenced `registry.py` block replaced with the `register_subsystem_clear` / `iter_subsystem_clears` seam; the four other sites asserting the retired shape corrected too.
- [x] **D4** — `OrderSet.check_permissions` removed from all four spec sites, and the cited nonexistent test removed rather than repointed.
- [x] **D5** — the six relocated mechanisms stated at their shared-substrate homes; `_ensure_built` / `_build_class_type` (gone, not relocated) removed as named mechanisms.
- [x] **D6** — `apply_async`'s thread boundary stated as `utils/querysets.py::run_in_one_sync_boundary`.
- [x] **D7** — the async-gate rejection stated, with the authorization-bypass reason, in Decision 8 step 6, `### Error shapes`, and `### Per-field permission gates`.
- [x] **D8** — the Edge-case "does not pre-validate" claim and the two `at type-creation time` timings corrected to finalize phase-2.5 subpass 2 via `classify_path`.
- [x] **D9** — order paths resolve against `queryset.model`; a model-less `OrderSet` is legal.
- [x] **D10** — all four surviving JOIN-multiplicity sites corrected (Test-plan reverse-FK bullet with its three claims, Decision 13's capability list, the Implementation-plan Slice-4 row, the quoted KANBAN body).
- [x] **D11** — the GLOSSARY claims corrected in both directions, with the `RelatedOrder` half of the side-channel claim kept because it is true at HEAD.
- [x] **D12** — the live-test count stated with its subject at every site, and the stale live-test name replaced with the parametrized one that ships.
- [x] **D13** — the four nonexistent package tests replaced with the tests that exist, and `test_registry_clear_works_without_orders_imported` relocated to its real home.
- [x] **D14** — `ORDER_BY_ARG` removed; the spec corrected rather than a dead constant shipped.
- [x] **D15** — seven ordersets and eight wirings stated, with the two extra ordersets' role named and the unnamed `RelatedOrder` declarations added.
- [x] **D16** — every tail-section item: the Slice-6 count, the three `planned for 0.0.8` bullets, the 12 pre-archive path occurrences including DoD item 17's quoted command, the `docs/TREE.md` section name, the `docs/TREE.md` file count, Decision 10's dated claims, and the Test-plan preamble's tree and file counts.
- [x] **Later finding 1** — Decision 3's `"__all__"` helper expression stated as HEAD's stronger guard, with the virtual-descriptor reason.
- [x] **Later finding 2** — Decision 5's `Ordering.resolve` example replaced with HEAD's `is_ascending` prefix test, and the property's second consumer named.
- [x] **Later finding 3** — DoD item 4's `(a)`-`(e)` sub-lettering preserved, so both `spec-028 DoD 4(c)` citations still resolve.
- [x] **Later finding 4** (found by this pass) — Decision 11's fenced `order_input_type` body stated as HEAD's delegation to `utils/inputs.py::build_lazy_input_annotation`.
- [x] **Later finding 5** (found by this pass) — Decision 6's `_bind_ordersets()` stated as a `_bind_sidecar_sets` / `_SidecarBindingSpec` delegation, with the filter-only subpass 2.5 named.
- [x] **Protect-list held** — no heading renamed, no `### Decision N` / `## Test plan` / `## Definition of done` / `## Edge cases and constraints` / `## Slice checklist` anchor touched; postcondition census re-measured on all three instruments.
- [x] **Both gates green** — `check_spec_glossary.py` exit 0 with the same term count, `check_citations.py` exit 0.
- [x] **Link scaffold and anchors intact** — one link-definitions delimiter and all 10 group headers in both files, alphabetical within group, every path disk-exists-checked, zero dangling `](#...)` in-page anchors.

---

## Final verification (Worker 1)

### Summary

`docs/SPECS/spec-028-orders-0_0_8.md` now reads as the current contract. **101 count-asserted exact-string replacements** landed — 96 prose edits plus 5 operations on the link-definition block — across the header, the Slice checklist, the Pre-implementation baseline, the Borrowing posture, the User-facing API, Decisions 1, 2, 3, 5, 6, 8, 9, 10, 11 and 13, the Implementation-plan table, the Edge cases, the Test plan, the Doc updates, the Risks, and the Definition of done. Three of those replacements swapped a whole fenced code block (Decision 5's `Ordering`, Decision 9's retired `registry.py` integration, Decision 11's `order_input_type`). The rationale companion took 13 operations: nine per-Decision `### Corrections this Decision received after ship` sub-sections, a retargeted `## Claims the spec may no longer make` preamble plus eight new spec-wide entries, `## Handed to Slice 3` replaced by `## Discharged by Slice 3`, and one link-definition group extended. No `.py` file was touched, no heading was renamed, both gates are green, and all three census instruments agree before and after.

### Byte and line counts

| File | Before | After | Delta |
| --- | --- | --- | --- |
| `docs/SPECS/spec-028-orders-0_0_8.md` | 224,759 bytes / 1,153 lines | 247,470 bytes / 1,162 lines | +22,711 bytes / +9 lines |
| `docs/SPECS/appx/spec-028-orders-0_0_8-rationale.md` | 98,821 bytes / 594 lines | 131,529 bytes / 697 lines | +32,708 bytes / +103 lines |

**The spec got bigger, and that is the honest outcome rather than the expected one.** Slice 1 was a move and shrank it by 64KB; this slice is a correction, and a corrected claim is almost always longer than the false one it replaces — "at type-creation time" becomes a sentence naming the real phase and why the metaclass defers, and "the framework does not pre-validate" becomes two clauses separating what *is* pre-validated from what is not. The one place the rewrite deleted more than it added is Decision 9, where a 61-line fenced block of retired Python became a 34-line fence plus the three properties the registration seam provides. Anyone expecting a reconciliation pass to shrink a spec should read the +22KB as the cost of stating a contract instead of gesturing at one.

### Postcondition census — the protect-list, re-measured

Timestamped `2026-08-20T16:08:18Z`, same three instruments, same corpus as the precondition table.

| Population | A: line-scoped `[ \t]` | B: flattened `\s` | C: join-aware | vs. precondition |
| --- | --- | --- | --- | --- |
| `spec-028` | 91 | 91 | 0 | unchanged |
| `spec-028 Decision N` | 62 | 62 | 0 | unchanged |
| `spec-028 DoD N` | 2 | 2 | 0 | unchanged |
| `spec-028 test plan` | 6 | 6 | 0 | unchanged |
| `spec-028 Edge cases` | 1 | 1 | 0 | unchanged |

Every class is unchanged in all three readings. The stronger check is the one that actually protects the citations: the spec's **45 markdown headings outside fenced blocks are byte-identical to their pre-edit text, in the same order** — verified by diffing the two heading lists, which come back with zero differences. So all 62 `Decision N` citations still resolve (they name Decisions 2, 3, 5, 6, 8, 9, 11, 12, 13), the 6 `test plan` and 1 `Edge cases` citations resolve against `## Test plan` and `## Edge cases and constraints`, and both `spec-028 DoD 4(c)` citations in `orders/sets.py` resolve because DoD item 4 keeps `(a)` through `(e)` with `(c)` still reading "**NO `apply(...)` dispatcher**".

This census is a **stability** reading, not a differencer, and saying so matters: the population could not move, because no citation-bearing `.py` file was edited by this slice. What it proves is the negative — that rewriting every Decision's prose broke nothing pointing into it. The heading diff is the instrument that could have failed, and it is the one worth trusting here.

One instrument note worth recording, because it cost a false alarm. My first anchor-resolution sweep reported **13 dangling in-page anchors**, every `#decision-N--...` target. The bug was in the checker, not the file: a slugger written as `re.sub(r'\s+', '-', …)` collapses the double space left where an em-dash was stripped into ONE hyphen, where GitHub emits two. Replacing each whitespace character individually reproduces the real slugs and the count drops to zero. **A slug function is an instrument like any other, and a plausible one can condemn a healthy file** — the same lesson this cycle paid for seven times over on grep patterns, arriving through a completely different door.

### One process near-miss, recorded because it nearly destroyed this artifact

A cleanup script of mine split this file by searching its text for the link-definitions delimiter, in order to rewrite the block that delimiter opens. The plan's step 80 **mentions that marker inline, in prose**, so `find` matched the mention rather than the block, and the write truncated the artifact from 452 lines to 248 — losing the dispatched-findings checklist and the entire final-verification section. It was caught immediately (the next `grep` for `^## ` returned one heading instead of three) and rebuilt byte-for-byte from the scratchpad copies the same script had written a minute earlier, with every inline mention of the marker de-literalised so the same split cannot recur.

Two things worth carrying, both generalisations of this cycle's standing lesson rather than new ones. **A structural marker used as a split point must be anchored to its structural position, not found by substring** — `find` on a marker that also appears in prose is the same class of error as a grep pattern that also matches its own documentation, which is what defeated four instruments earlier in this cycle. And **keeping the intermediate pieces on disk is what made the loss a two-minute repair instead of a rewrite**: the reconstruction was possible only because the split had persisted `art_head.md` and `art_mid.md` before writing. The spec and the rationale companion were never at risk — every edit to those two went through the count-asserted replacement harness, which aborts the whole run on any mismatch and never splits a file.

### Gates

- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-028-orders-0_0_8.md` -> `OK: 44 terms - all have glossary entries and at least one spec link.` **exit 0**, the same 44 as at entry. This is the one gate a spec rewrite can break silently, and the risk was live: three edits stripped a `planned for 0.0.8` parenthetical out of a Key-glossary bullet and several deleted whole sentences containing glossary links. Every affected term kept a link in the surviving contract prose. `docs/SPECS/appx/spec-028-orders-0_0_8-terms.csv` was not opened.
- `uv run python scripts/check_citations.py` -> **exit 0**, `OK: 782 citations resolve (705 in 422 .py files, 77 in KANBAN.md)` — the same total as at entry, which is expected rather than reassuring: this slice added no `.py` citation, and the number moves only when the concurrent cohort commits. Exit 0 is the criterion.
- `uv run python scripts/check_trailing_commas.py --check` on both files -> **exit 0**. This is the `source-layout` hook's own script, invoked directly because `pre-commit` is not on PATH in this environment (`uv run pre-commit` fails to spawn); the script is what the hook runs, so the check is the same one, and it auto-appended nothing.

### In-page anchors and link definitions

- **Zero dangling in-page anchors** in either file: 21 distinct `](#...)` targets in the spec and 13 in the rationale, all resolving to headings that still exist. No heading was reworded, so no slug moved.
- **Zero used-but-undefined reference ids** in either file. The spec's only defined-but-unused id is `[relay]`, which Slice 1 verified was already unused at `HEAD` before the move — not an orphan either slice created. Left in place: removing it is a judgement about whether Decision 9's `orders.sets -> types.relay -> types.base` cycle discussion should link `types/relay.py`, and I neither removed it nor invented a use for it.
- **Every path disk-exists-checked**, fragments stripped: 119 definitions in the spec and 58 in the rationale, zero missing on disk. Against `HEAD` the spec's set is +24 / −8; of those, 17 are Slice 1's (`[spec-028-rationale]` plus the 13 `[rationale-dN]` pointers, and the seven removals whose only uses the move took). **This slice added ten and removed one**: `[utils-inputs]`, `[utils-permissions]`, `[utils-querysets]`, `[utils-relations]`, `[orders-sets]`, `[test-orders-inputs]`, `[test-sets-mixins]`, `[test-utils-permissions]`, `[build-tree]`, `[fakeshop-test-conftest]`, and dropped `[fakeshop-test-library-reload]` — which pointed at the same file as `[fakeshop-test-library]`, so two ids named one path and the fixture's real home was unreachable.
- **All 10 canonical group headers present, in order, in both files**, one link-definitions delimiter each. Alphabetical within group: my one insertion that broke local order (`[orders-sets]` landing after `[package-init]`) was caught and repositioned before the checker ran.

### Dispatched findings checklist — every tick re-derived, not read

All 22 boxes walked. **22 ticked, 0 open.** Each row names the measurement, not the edit.

| Box | Verdict | Basis re-derived after the edits |
| --- | --- | --- |
| **D3** | holds | `grep -c 'except ImportError' django_strawberry_framework/registry.py` -> **0**, and the same pattern in the spec -> **0**. `iter_subsystem_clears()` is the replay in `TypeRegistry.clear`; the two order-side rows exist with owners `orders.input_namespace` (`before_bind=True`) and `orders.helper_references`. All five spec sites asserting the retired shape corrected. |
| **D4** | holds | `grep -rn 'def check_permissions' django_strawberry_framework/` -> exactly **1**, `filters/sets.py`. Six `check_permissions` strings survive in the spec and all six are correct: one names the *filter* side's discipline in the Predecessors line, four are explicit negations ("no instance-method `check_permissions` is shipped"), one is a hypothetical future `check_permissions_mode` opt-in in a Risks fallback. `test_orderset_check_permissions_instance_method_delegates` -> **0** occurrences repo-wide, where the spec previously held its only one. |
| **D5** | holds | `_ensure_built` / `_build_class_type` -> **0** files under `django_strawberry_framework/orders/`; in the spec, `_ensure_built` -> 0 and `_build_class_type` -> 1, that one correctly attributed to the *cookbook's* factory in the do-not-borrow list. `RelatedSetTargetMixin`, `ActiveInputPermissionMixin`, `collect_related_declarations`, `expanded_once`, `should_cache_expansion`, `GeneratedInputArgumentsFactory`, `make_set_input_namespace` each resolve at the module now named. The four aliases re-read at `orders/inputs.py:58-62`, so every spec-named `orders.*` name still resolves from `orders.*`. |
| **D6** | holds | `OrderSet.apply_async`'s body is `await run_in_one_sync_boundary(cls._run_permission_checks, input_value, request)`; `grep -r sync_to_async django_strawberry_framework/orders/` -> **0 files**. The four `sync_to_async` strings left in the spec are all prose about the boundary's semantics, not a pinned call site. |
| **D7** | holds | `utils/permissions.py::invoke_permission_method` routes `method(request)` through `reject_async_in_sync_context(..., context="permission-check")`; `utils/querysets.py::reject_async_in_sync_context` raises `SyncMisuseError`. The spec now names the rejection at three sites (`### Per-field permission gates`, `### Error shapes`, Decision 8 step 6) and the bypass reason at two. |
| **D8** | holds | `classify_path` called in both `OrderSet._expand_meta_fields` and `::_resolve_order_expressions`, each raising `ConfigurationError` naming path and model; `test_orderset_meta_fields_rejects_unknown_order_path` and `::test_orderset_resolve_order_expressions_rejects_unknown_order_path` both exist in `tests/orders/test_sets.py`. "does not pre-validate" -> **0** in the spec. One `at type-creation time` survives, deliberately: `Meta.orderset_class = NotAnOrderSet` genuinely raises at `_validate_meta`, and leaving the two timings differently worded is the point. |
| **D9** | holds | `_apply_orderings` calls `_resolve_order_expressions(flat_orders, model=queryset.model)`; the method's own docstring states `Meta.model` may be absent for a related-only set. `test_modelless_orderset_uses_queryset_model_for_to_many_order` and `::test_queryset_model_overrides_conflicting_orderset_meta_model` both exist. |
| **D10** | holds | `denormalized` -> **0** in the spec. `multiplicity` -> **1**, and that one is Decision 3's excluded-M2M-leaf parenthetical, which was already correct. `multiplied` -> 3, all three new statements of what the aggregate prevents. `Alpha three times` -> 1, and it now reads as what a *regression* would return, which is the reason the uneven-shelf fixture is load-bearing. All four retired sites corrected, the quoted KANBAN body included. A fifth site surfaced during the sweep and was fixed: the reverse-FK bullet's staff-client sentence still called it "the multiplicity contract". |
| **D11** | holds | `docs/GLOSSARY.md` `## RelatedOrder` carries `Position-side-channel note:`; `## OrderSet` carries none — so naming `RelatedOrder` alone is true and the dropped half was the false one. Neither entry mentions multiplicity, so the Test plan's claim was deleted rather than repointed. The `OrderSet` entry's three undocumented contracts are now named in `## Doc updates`. |
| **D12** | holds | Section bounds `test_library_api.py:1738` (order banner) to `:2484` (`spec-029` banner); `^def test_` -> **16**; exactly one `parametrize`, over **four** NULLS directions; 16 − 1 + 4 = **19** rows. Re-derived from the section's own structure, not read from Slice 2's banner, and the two agree. `exactly 14` -> 0 in the spec; every surviving `14` names its subject. `test_library_books_order_by_subtitle_desc_nulls_last` -> **0** repo-wide. |
| **D13** | holds | All four spec-named package permission tests -> **0** occurrences repo-wide, and all four replacements exist: `tests/utils/test_permissions.py::test_run_active_input_permission_checks_double_dispatch_and_dedup`, `tests/test_sets_mixins.py::test_permission_facade_methods_are_single_sourced_on_the_mixin`, `tests/orders/test_sets.py::test_orderset_check_permission_dedups_repeated_list_entries`, `::test_orderset_inactive_input_does_not_resolve_lazy_related_target`. `test_registry_clear_works_without_orders_imported` is in `tests/orders/test_inputs.py`, and the spec now cites it there in both Decision 9 and the Test plan. |
| **D14** | holds | `ORDER_BY_ARG` -> **0** in the spec and **0** in the tree outside this cycle's own `docs/builder/` artifacts. |
| **D15** | holds | `grep -c '^class .*Order(OrderSet)' examples/fakeshop/apps/library/orders.py` -> **7**; `grep -c 'orderset_class = ' …/schema.py` -> **8**; `grep -c 'order_input_type(' …/schema.py` -> **6**. `orders_genre.py:29` declares `books = RelatedOrder("apps.library.orders.BookOrder", field_name="books")`; `BookOrder.loans` at `orders.py:123`, `ShelfOrder.books` at `:90`. DoD items 13 and 14 state seven, eight and six. |
| **D16** | holds | `docs/spec-028-orders` -> **0** in the spec, down from 12 over 9 lines, DoD item 17's quoted command included. `planned for 0.0.8` -> **10**, all in the four correct contexts (Predecessors, Pre-implementation baseline, Slice-5 and Doc-updates flip-this instructions), with the three present-fact bullets flipped. `Test layout going forward` -> 0. `Tests live in two trees` -> 0. `Five files mirror` -> 1, and that one is Decision 2 describing the five-module **source** package, which is correct. Slice-6 count is 2 at both sites. Decision 10 asserts no `CHANGELOG.md` state. |
| **Later 1** | holds | `orders/inputs.py::_get_concrete_field_names_for_order` re-read: `getattr(f, "column", None) is not None and not getattr(f, "many_to_many", False)`. Decision 3 quotes it exactly, keeps the cookbook's `hasattr` form attributed to the cookbook, and states the virtual-descriptor reason its own docstring gives. |
| **Later 2** | holds | `Ordering.is_ascending` returns `self.name.startswith("ASC")`; `Ordering.resolve` branches on it; `OrderSet._resolve_order_expressions` reads `direction.is_ascending` to pick `models.Min` / `models.Max`. Decision 5's fence shows the property and both consumers are named. |
| **Later 3** | holds | DoD item 4's sub-letters `(a)` `(b)` `(c)` `(d)` `(e)` all present in order; `(c)` unchanged. Both `spec-028 DoD 4(c)` citations (`orders/sets.py` lines 13 and 121) resolve. |
| **Later 4** | holds | `orders/__init__.py::order_input_type` returns `build_lazy_input_annotation(...)` with seven keyword arguments; `utils/inputs.py::build_lazy_input_annotation` exists. Decision 11's fence shows the delegation and keeps the ForwardRef and idempotent-ledger clauses in the spec per `BUILD.md`'s implementation-relevant-rationale carve-out. |
| **Later 5** | holds | `types/finalizer.py::_bind_ordersets` builds a `_SidecarBindingSpec` and calls `_bind_sidecar_sets` with `post_expand_audit=None`; `_bind_sidecar_sets` carries the `Subpass 2.5 (filter-only today)` branch. Decision 6 states both, and DoD item 10 names the shared driver. |
| **Protect-list** | holds | Postcondition table plus the byte-identical 45-heading diff. Zero wrapped citations on the join-aware instrument, before and after. |
| **Gates** | holds | glossary exit 0 / 44 terms; citations exit 0 / 782; `check_trailing_commas.py --check` exit 0 on both files. |
| **Scaffold + anchors** | holds | One delimiter and 10 ordered group headers per file; 119 + 58 definitions, zero missing on disk, zero undefined; zero dangling `](#...)`. |

### DRY check across this slice and prior accepted slices

No new duplication. One seam is worth stating: Slice 2 wrote the code-side banner (`16 test functions / 19 test rows`, naming the two post-ship additions) and this slice writes the spec-side count. **They agree, and the agreement is derived rather than copied** — I re-derived 16/19 from the section's own structure without reading Slice 2's figure, and the two derivations match. The wordings deliberately differ: the banner names the section it heads, the spec names the 14 functions this card shipped and points at the file's total. Neither is the other's source, which is the right shape for a number two files must both state.

One thing this slice deliberately did **not** consolidate: the row-preserving aggregate contract is now stated in five spec locations (the Slice-4 checklist bullet, Decision 12, Decision 13, the Implementation-plan Slice-4 row, the Test-plan reverse-FK bullet) and once in `docs/GLOSSARY.md`. That reads like duplication and is not — each states it at a different grain (a deliverable, a contract, a coverage summary, a plan cell, a test assertion). **D10's defect was never that five sites state it; it was that four of the five stated the OPPOSITE.** Collapsing them into one cross-reference would trade a divergence that a grep can detect for a spec a reader cannot follow.

### Slice-local checks, run by this pass

- **No `pytest`**, per `AGENTS.md` #"No pytest after edits" and the build plan's declaration. This slice touched no Python, so no focused scope was owed and none was run. **No `--cov*` flag anywhere.**
- **No `ruff`.** `git diff HEAD --name-only -- '*.py'` lists 57 paths and none of them is mine — every one belongs to the concurrent `spec-027` cohort or to Slice 2, whose set closed `final-accepted`.
- **Writable-file discipline.** Exactly four files are mine: the spec (modified), the rationale companion (untracked, created by Slice 1), this artifact (created), and my memory file (appended). Nothing else was opened for writing.
- **Do-not-touch audit.** `docs/SPECS/appx/spec-028-orders-0_0_8-terms.csv`, `docs/GLOSSARY.md`, `KANBAN.md`, `KANBAN.html`, `CHANGELOG.md`, `docs/TREE.md`, `README.md`, `TODAY.md`, `examples/fakeshop/db.sqlite3`, `docs/builder/BUILD.md`, `docs/builder/ARTIFACT.md`, every `worker-*.md` role file, every `*-027*.md`, and `docs/SPECS/spec-027-filters-0_0_8.md` — none edited by me. The spec was moved and renamed by nobody: it is still at `docs/SPECS/spec-028-orders-0_0_8.md` with its companion at `docs/SPECS/appx/`.
- **Concurrent-work note, and HEAD moved under this pass.** The tree's dirty set peaked at **79 paths, 57 of them `.py`**, against the ~21 Slice 1 recorded — the concurrent `spec-027` cohort grew materially during this cycle. Then, between this slice's edits closing and its verification finishing, that cohort **committed**: HEAD advanced to `8a9840dc` ("docs(specs): complete the spec-027 record and reconcile its Decision 9 claims"), and left `docs/SPECS/spec-027-filters-0_0_8.md` clean where it had been dirty all pass. The dirty set did NOT shrink — it reads **79 paths, 57 of them `.py`** after the commit as well as before, because that cohort's uncommitted work simply moved forward on top of it. I asserted a drop before measuring one and it was wrong; the measured figures are identical on both sides of the commit.

  **Attribution checked in both directions, because a mid-pass commit is exactly where work gets swallowed.** `git log --stat -1` confirms that commit touched no `spec-028` path — its only `docs/builder/` entry is `bld-slice-3-027-spec_reconciliation.md`, its own artifact. My spec still shows as modified against the new HEAD and every landed edit is verifiably present (`register_subsystem_clear` 5, `is_ascending` 4, `build_lazy_input_annotation` 3, `run_in_one_sync_boundary` 2, `reject_async_in_sync_context` 3 — all zero before this slice). Both gates re-run green against the new HEAD. Nothing of mine was swept in and nothing of theirs was reverted: I read `git diff HEAD -- <path>` throughout, never `git diff -- <path>`, which is the reading that stays correct across exactly this event.

### Spec changes made (Worker 1 only)

101 replacements in `docs/SPECS/spec-028-orders-0_0_8.md`, grouped by the finding that triggered each and cited by section rather than by line — the file renumbered under its own edits, so a line cite would have been stale before this artifact was saved. Every replacement was applied as a **count-asserted exact-string substitution with the whole run aborting on any mismatch**, which is the method Slice 1 established and the only safe one when the target file is being renumbered by the same run.

| Section | Finding | Reason, one line |
| --- | --- | --- |
| Opener, `Status:` line | re-derivation 2 | Two dated snapshots of `CHANGELOG.md` and version-file state read as current fact. |
| `## Key glossary references` (4 bullets) | D16 | Three `planned for 0.0.8` parentheticals asserted as present fact; the `docs/TREE.md` flip described as pending. |
| `## Slice checklist` (6 sub-bullets) | D3, D10, D12, D16 | The retired clear seam; the reverse-FK chronology block; the `14` / five-file / one-test counts; the pre-archive path. |
| `## Pre-implementation baseline` (1 bullet) | D16 | A five-file claim the snapshot never supported; dropped rather than restated, so no HEAD fact enters a snapshot section. |
| `## Borrowing posture` (2 bullets) | D4, D14 | The `check_permissions` port-verbatim claim; the `ORDER_BY_ARG` constant that never shipped. |
| `### Per-field permission gates`, `### Error shapes` (4 edits) | D7, D8 | The async-gate rejection was unnamed; two raise timings said type-creation where the raise lands at finalize. |
| `### Decision 1` (1 edit) | D16 | The pre-archive path, restated as the archive layout the `NEXT.md` Step-8 sweep produced. |
| `### Decision 2` (4 bullets) | D3, D4, D5 | Member list, base class, mechanics homes, two-block clear shape. |
| `### Decision 3` (7 edits) | D5, later 1 | Four layers naming retired local mechanisms; the materialization attribution; the `"__all__"` scope sentence and its quoted expression. |
| `### Decision 5` (1 fence + surrounding prose) | later 2 | A substring direction test, stale import commentary, and an unnamed second consumer. |
| `### Decision 6` (2 edits) | D3, later 5 | The shared `_bind_sidecar_sets` driver and its filter-only subpass 2.5; the clear seam. |
| `### Decision 8` (7 edits) | D4, D5, D6, D7, D9, D11, D13 | The deleted delegate and its phantom test; the mixin homes; the thread boundary; the async rejection; `queryset.model`; the GLOSSARY half-claim; four phantom tests. |
| `### Decision 9` (4 edits incl. the 61-line fence) | D3 | The whole `except ImportError` integration shape is retired; the registration seam and its three properties replace it. |
| `### Decision 10` (1 edit) | re-derivation 2 | Three stale sentences about files that keep moving. |
| `### Decision 11` (1 fence + 1 bullet) | later 4 | The helper body is a shared-substrate delegation at HEAD. |
| `### Decision 13` (1 edit) | D10, D12 | The capability list's multiplicity claim and the bare `14`. |
| `## Implementation plan` (3 rows) | D4, D10, D12, D16 | `check_permissions`; the multiplicity cell; the Slice-6 `1`. |
| `## Edge cases and constraints` (5 bullets) | D8, D5, D16 | The "does not pre-validate" claim; a raise timing; a chronology clause; the guard's home; the `"__all__"` scope. |
| `## Test plan` (10 edits) | D10, D11, D12, D13, D16 | Tree and file counts; the phantom split-pair tests; the misplaced subprocess test; the `14` header; the deleted NULLS test name; the reverse-FK bullet's three retired claims plus its staff-client sentence; two unnamed post-ship tests; the fixture's real home. |
| `## Doc updates` (9 edits) | D10, D11, D16 | Three undocumented GLOSSARY contracts; the side-channel note; the `docs/TREE.md` section name and file count; the quoted KANBAN body's four retired claims; the quoted CHANGELOG bullets. |
| `## Risks and open questions` (2 bullets) | D16 | The terms-CSV path; a plan-time gate statement reading as current. |
| `## Definition of done` (items 1, 4(b), 4(e), 10, 11, 13, 14, 15, 17, 18, 22, 23) | D3, D4, D9, D13, D15, D16 | Paths, the deleted delegate, `queryset.model`, the seam, five counts, and the `[Unreleased]` state claim. Item 4's sub-lettering preserved. |
| the link-definitions delimiter (5 operations) | D16 + the new citations | Ten added, one removed (`[fakeshop-test-library-reload]`, a duplicate target), one repositioned for alphabetical order; every path disk-exists-checked. |

And in `docs/SPECS/appx/spec-028-orders-0_0_8-rationale.md`, appended per the append-only rule: nine `### Corrections this Decision received after ship` sub-sections under Decisions 2, 3, 5, 6, 8, 9, 10, 11 and 13 — each keyed to its spec Decision by heading and by the existing `[spec-028-dN]` anchor, and each naming what the Decision claimed, what HEAD does, and **why the shipped shape is the one that is right**; eight new spec-wide entries under `## Claims the spec may no longer make`; and `## Discharged by Slice 3` replacing `## Handed to Slice 3`.

**Two rationale entries record a re-derivation with no matching spec edit**, because the spec was right and the finding was wrong: D11's `RelatedOrder` half (the entry does carry the note, so naming it alone is the correct sentence and deleting the claim outright would have removed a true one) and the build plan's `14`-site census (11 sites over 10 lines at entry, one of them a cross-reference to DoD item 14, with the subject having moved twice). A negative result that goes unrecorded is a finding the next pass re-opens.

### Notes for Worker 1 (spec reconciliation) — routed to `bld-final-028.md`

Nine items for the `### Deferred work catalog`. None blocks this slice; each is outside the cycle's scope fence or a maintainer decision.

1. **`KANBAN.md`'s `DONE-028-0.0.8` body still carries four retired claims** — `check_permissions` in the apply-pipeline sentence, "exactly 14 live HTTP tests", "reverse-FK with denormalized-multiplicity-pinned", and the pre-archive `docs/spec-028-orders-0_0_8.md` path — plus two `per <ID> of rev3` provenance breadcrumbs the spec no longer carries. The spec's quoted copy is corrected, so the two now differ deliberately. `KANBAN.md` is DB-generated and out of scope; the fix is a kanban DB edit plus `scripts/build_kanban_md.py` regenerate. **`KANBAN.md:357` already tracks one clause of this** (the card body's "Layer 6 deferred to `0.0.9`"), so fold it into that carded sweep rather than opening a new item.
2. **`docs/GLOSSARY.md`'s `## OrderSet` entry carries no position-side-channel note** where its `## RelatedOrder` sibling does. The spec now claims only what is true, but the asymmetry is arguably a real documentation gap: `OrderSet` is where `check_<field>_permission` is documented, and the side channel is the reason a consumer would declare a branch gate. DB edit plus re-render; a maintainer call, not a defect.
3. **`docs/TREE.md` omits `__init__.py` by renderer design**, so every spec listing "five files" for a five-module subpackage will disagree with the rendered tree by one. This is a convention mismatch that recurs on every subpackage card, not a `spec-028` defect. Worth one line in `BUILD.md`'s doc-wrap guidance so the next spec author states the count the tree will actually show.
4. **`spec-028`'s two orphaned `0.0.9` deferrals**, already carded at `KANBAN.md:357` and re-verified live by this pass. The `DjangoListField` orderBy-argument deferral **re-derives as still true at HEAD**: `list_field.py`'s `_default` and all three `_wrap` variants take `(root, info)` only, so no arbitrary resolver argument survives, and the deferral is real and still uncarded. The position-side-channel leak-closing design is the second. Both need the card-or-drop adjudication the board item names.
5. **`[relay]` is a defined-but-unused link definition in the spec**, as it was at `HEAD` before Slice 1. One-line decision for whoever next opens the file: either Decision 9's import-cycle discussion should link `types/relay.py`, or the definition goes.
6. **The cycle's instrument lesson deserves a gate clause, not a memory.** `scripts/check_citations.py` resolves `path::Symbol` only, with `docs/` out of scope, so **no gate in this repo can see a broken `spec-NNN <Heading>` citation** — exactly the 71-citation population this slice protected by hand. Slice 2 routed two clauses to the gate-extension card (the `path::Symbol` + `#"substring"` join, and the split-path wrap); this adds a third: resolve a `spec-NNN Decision N` / `DoD N` / `test plan` / `Edge cases` citation against the named spec's heading list. Without it the next reconciliation cycle spends its whole precondition budget the same way.
7. **Two `spec-028` statements about `0.0.9` are defensible in either voice and I changed neither.** Decision 12 describes `connection.py::_synthesized_signature` / `::_pipeline_sync` / `::_pipeline_async` in the present tense (correct — the connection field shipped as `DONE-030-0.0.9`), while the Non-goals block still frames the connection field as future work scoped out of this card (also correct, as a statement about *this card*). A maintainer may prefer Non-goals to say "shipped later in `0.0.9`". Flagged rather than absorbed because it is a voice choice, not a false claim.
8. **The cross-cohort seam widened again during this pass.** The tree's dirty set is 79 paths with 57 `.py` files, against the ~21 Slice 1 recorded — the concurrent `spec-027` cohort is materially larger now. Nothing is lost in either direction and every hunk on both sides is prose-only, but only the maintainer can see both cycles, so the size is recorded rather than acted on.
9. **No code finding surfaced, and I looked for one specifically.** The dispatch reserved one exception to "HEAD wins": a place where HEAD looks like a genuine *regression* against a contract the spec intended, which routes to the maintainer rather than into a spec edit that quietly blesses it. **There is none.** Every divergence resolves the other way — HEAD is stricter (`getattr(f, "column", None) is not None` over `hasattr`, closing the virtual-descriptor door; `startswith("ASC")` over substring membership; `classify_path` pre-validation where the spec promised none; the async-gate rejection closing an authorization bypass the spec never noticed), or single-sited (the six relocated mechanisms, `build_lazy_input_annotation`, `_bind_sidecar_sets`, `run_in_one_sync_boundary`, the registration seam), or a correction a later card landed deliberately (the row-preserving aggregate, `queryset.model`, the deleted cookbook-compat delegate). The subsystem shipped in full and then grew; its description was the only thing wrong.

### Final status

`final-accepted`.

D3 through D16 and all five later findings are discharged in the spec, with each change recorded in the rationale companion keyed to its Decision — and in the two cases where the finding itself was wrong, the re-derivation is recorded in place of an edit. The protect-list held: 71 heading-bearing citations across 19 files, five populations, three instruments, identical before and after, with all 45 headings byte-identical and in the same order. Both gates green, the glossary term count unchanged at 44, the layout checker clean on both files, zero dangling anchors, zero undefined references, every link path on disk. Zero `.py` files touched and zero boundaries added, so no failability proof, no hot-path number, and no floor run is owed — each **by entitlement**, stated explicitly so a reader does not read the absence as omission. Nine items routed to `bld-final-028.md`'s deferred catalog.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
