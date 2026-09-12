# Adversarial implementation review: spec 050, second pass

Date: 2026-09-11. Graded against the maintainer's re-review of the same date (base `7de31cd7`;
HEAD `8179819a` differs from it only by `docs/builder/DONE/build-041-*`), against the working-tree
diff and the working-tree [specification][spec-050], and against [AGENTS.md][agents] /
[START.md][start]. Per-cycle artifact: raw `path:NN`
references are used deliberately so every claim can be opened at the line. No pytest was run; every
behavioral claim below is argued from the code as it stands. Concurrent sessions were editing this
checkout throughout; every hunk was attributed by content, and nothing was reverted or staged.

## Verdict

**Not accepted yet.** Four of the six findings are closed at the root (P1-2 ledger, P2-1 exact
boolean, P2-2 raw bytes, P3-1 scope predicate) and the list-field half of P1-1 is closed with
consequential proofs. P1-1 still has a live residual on the connection side: the optimizer's
plan-time nested window derives the keyset vocabulary by re-reading `__django_strawberry_definition__`
off the target class on every request, the new `keyset.py` docstring waves this off, and the
synthesized-relation read-once proof is built on a schema with no optimizer installed, so it is
structurally unable to see the read it certifies as absent. The build record's status prose and the
spec's five homes also still disagree with each other about what shipped.

## Findings

### P1-1 (residual, blocking) - the plan-time nested window still reads the target class for its cursor vocabulary, and the proof cannot see it

The connection class now fixes its keyset state at generation
(`django_strawberry_framework/connection.py:1350-1355`), `_keyset_connection_context` reads only that
slot (`connection.py:145-157`), and `_finalize_queryset` takes `definition.model` /
`definition.cursor_field` (`connection.py:1640-1641`). That closes the resolve-time half. The
plan-time half is untouched:

```text
django_strawberry_framework/optimizer/nested_planner.py:1128
    keyset_context = resolve_declared_cursor_state(target_type)
django_strawberry_framework/keyset.py:317-318
    return declared_cursor_state_for_definition(
        getattr(target_type, "__django_strawberry_definition__", None),
```

`plan_connection_relation` (`nested_planner.py:1048`) is reached from `optimizer/walker.py:1452` for
every connection-shaped relation selection the optimizer plans, unconditionally (the read happens
before any `cursor_field` test). The class was generated from the finalizer's registry read
(`types/finalizer.py:721`); the window is planned from whatever the class answers at request time.
A stateful target answering the second question differently plans the nested page under one set of
cursor columns and fingerprint while `DjangoConnection.resolve_connection` mints and decodes under
another. That is exactly the "cross-strategy byte-parity invariant" the retained wrapper's own
docstring says it preserves (`keyset.py:311-313`), now preserved only for a target that never
changes its answer - the threat model Decision 1 exists to remove.

The new docstring is a wave-off, not an argument (`keyset.py:308-311`): "for the callers that hold
only the type: the plan-time nested window ... reaches its target through the walker, not through a
field factory." The walker holds the registry: `walker.py:1201` already does
`registry.get_definition(target_type)`, and `resolve_relation_target` is a callback the walker
supplies (`nested_planner.py:1061`). Nothing prevents the planner from being handed the same
definition object the finalizer captured. The spec repeats the wave-off in Decision 1 ("stays for
the plan-time nested window, which reaches its target through the walker and holds no definition").

**Why the proof passes anyway.** Every connection read-once test builds a plain
`strawberry.Schema(query=query_cls, config=strawberry_config())`
(`tests/test_connection.py:2519`, `:2624`). `apply_connection_optimization` returns the queryset
unplanned when no extension is active (`optimizer/extension.py:1571-1573`), so the walker never
runs and `plan_connection_relation` is never entered. The shipped schema shape installs the
extension (`examples/fakeshop/config/schema.py:77-82`). Under that shape, the metaclass counter in
`test_a_synthesized_relation_connection_is_built_from_the_registrys_definition`
(`tests/test_connection.py:2562-2638`) would record a read at request time and its
`assert reads["names"] == []` would fail. The instrument excludes the one path where the residual
lives, which is the "control that cannot fail" shape [START.md][start] names. The test's docstring
("a stateful target has nothing to answer when the generated `<field>Connection` is built or
resolved") is false for the schema class consumers are told to use.

This is the same failure mode the previous round was rejected for: the wording moved to the seams
that were threaded while one seam kept re-reading.

**Root-cause correction**

- Derive the plan-time keyset context from the definition object, never the class attribute: have
  the walker pass the target's registry definition (the object `finalizer.py:721` captured, reached
  through the same `registry.get_definition` the walker already calls at `walker.py:1201`) into
  `plan_connection_relation`, and call `declared_cursor_state_for_definition` on it at
  `nested_planner.py:1128`.
- Retire `resolve_declared_cursor_state` from every execution path. Either delete it (its remaining
  callers are `tests/test_keyset_connection.py:107,117-118,533`, which can call the definition-keyed
  function directly) or keep it strictly for construction-time callers and say so; a type-keyed
  request-time wrapper that exists "for the walker" is the abstraction the review rejected.
- Correct the Decision 1 sentence and the `keyset.py` docstring that currently license the read.

**Required proofs**

- Run the synthesized-relation and root-connection read-once tests under `DjangoSchema` with
  `DjangoOptimizerExtension` installed (the `config/schema.py` shape), selecting the nested
  connection with `first:` so a window is planned. The counter must stay empty through the request.
- Give the decoy a DIFFERENT `cursor_field` (keyset mode) and prove the page's cursors decode under
  the captured vocabulary: assert the minted `endCursor` decodes with the captured
  `DeclaredCursorState.fingerprint` and columns, not the decoy's. No current decoy carries a
  `cursor_field` or a sidecar for a connection, so "neither the decoy model nor its sidecars/cursor"
  is proven for the model only.
- A live keyset row in `examples/fakeshop/test_query/test_keyset_api.py` if the planned-window and
  per-parent-fallback cursor bytes are consumer-observable there; otherwise state why package tier
  suffices.

### P2 (non-blocking) - the read-once proofs stop short of what was demanded

Code is symmetric by reading; these are proof gaps against the review's literal list, each of which
was requested and each of which is currently claimed as discharged in
[bld-final][bld-final] `## Fifth implementation review`:

- **Warm cache.** `test_a_root_connection_on_a_warm_cache_reads_the_definition_once_too`
  (`tests/test_connection.py:2534-2559`) constructs two fields and stops: no schema build, no
  request. The review asked for the counter armed through all three phases "with cold and warm
  connection caches". For the synthesized relation there is no warm-cache proof at all (the
  registry-isolation fixture clears `_connection_type_cache` between tests, so every synthesized
  run is cold).
- **Async coloring.** No counter is armed through `_execute_queryset_pipeline_async`
  (`list_field.py:950`) or `_pipeline_async` (`connection.py:1808`). Both pass `model=` /
  `definition=` by inspection, but the review's complaint was precisely that inspection had been
  trusted before.
- **No-argument list shape.** The three list-field proofs use `orderBy` (`:2706`, `:2814`) and
  `limit: 5` (`:2894`); none exercises the `not args_record.any_argument_supplied` branch
  (`list_field.py:908-911`), which is the most common request shape.
- **Connection sidecar decoy.** The connection decoys (`_item_node_type`, `RelationChildDecoyNode`)
  declare no `filterset_class` / `orderset_class`, so a re-read that swapped the sidecar would not
  be visible as a dispatch through the wrong class the way the list-field `DecoyOrder` makes it.
- **Live rows.** The review asked for consumer-observable rows through live HTTP with count
  mechanics staying package-tier. Zero live rows mention the invariant (`rg` over the four list /
  connection / keyset live suites: 0 hits). If the position is that a sane target has no observable
  difference, the build record should say that rather than list the item as done.

**Correction**: add the missing rows (package tier for counters, live tier for any observable
cursor/row consequence) or amend the build record to state what was not proven.

### P3 - `_dst_node_type` lost its only reader and gained a false comment

Before this round `_keyset_connection_context` read `cls._dst_node_type` to derive the keyset state
at first resolve (`git show HEAD:django_strawberry_framework/connection.py`, the body that
`connection.py:145-157` replaced). The change removed that read and left the slot, then rewrote the
comment at `connection.py:1347-1349` to claim "the optimizer's window handoff reads it back to
identify which type a page's rows belong to." Population: `rg -n '_dst_node_type' .` over the whole
repository returns exactly two hits, the write at `connection.py:1350` and a passing mention in a
comment at `connection.py:1397`. Zero readers in the package, the optimizer, or any test tree.

A bare dead slot would be a P3 tidy-up. A comment asserting a reader that does not exist is a false
description of the code, which this repository treats as its own defect class ([START.md][start]
"Derived descriptions outlive sources").

**Correction**: delete the slot and the comment (sweep `connection.py:1397`), or keep the slot only
if a real reader is named and cited.

### P3-2 (still open) - spec homes and build record disagree with each other and with the code

Checked by a full read of the working-tree spec, [bld-final][bld-final], [build-050][build-050] and
the `docs/GLOSSARY.md` hunk (population: 4 files; counts below are `grep -c`, after a first `rg -c`
sweep returned 0 for terms the file demonstrably contains - state the instrument before trusting it).

- **Read-once capture lives in ONE home.** Decision 1 states it fully and correctly (it names
  `base_queryset`, the three seals, `_generate_connection_class` / `_connection_type_for` /
  `_build_total_count_connection` / `_finalize_queryset`, `declared_cursor_state_for_definition`,
  and the registry read for synthesized relations). The slice checklist, `## Edge cases and
  constraints`, `## Test plan` and `## Definition of done` carry no read-once row at all. "Two
  disagreeing is a defect"; here four homes are silent on a contract the fifth calls foundational,
  and the cold/warm/decoy matrix exists only in the build record. Decision 1 also says the
  connection "shares the validator" and later names its guard as
  `list_field.py::_validate_relay_djangotype_target` - two functions, one sentence.
- **Exact-boolean rule is not where the build record says.** It lives under `## Caps and error
  table`, correctly worded (`effective_bound` widens on `trusted is True`; `validate_trusted_flag`
  at the constructing line). `### Decision 4` has no such sentence, yet bld-final P3-2 claims
  "Decision 4's bound table gains the exact-boolean opt-in rule". No Edge-cases, Test-plan or DoD
  row names a non-`bool` value, while bld-final P2-1 lists six such pins.
- **The ledger is a DRY-section contract.** The normalization transport is specified only under
  `## Helper-reuse obligations (DRY)` (correctly: append-only, claim-once per class-and-input,
  disagreement fails closed, binding reset and ledger emptied in `finally`). Slice 2 of the
  checklist describes the pipeline order only; `## Test plan` still says "pin the documented double
  normalization" and names no child-task, worker-thread, nested-`OrderSet` or disagree-fail-closed
  row, while bld-final P1-2 lists nine package pins and two live rows. DoD is silent.
- **Combined-source byte oracle.** Test-plan item 22 states it correctly ("every legacy row - the
  combined-source one included - asserts equality of the RAW `HttpResponse.content` bytes ..."). DoD
  names the byte claim against "a pre-argument reference resolver mounted under the SAME GraphQL
  field name" without naming the combined source. Minor home-vs-home gap; the code matches item 22.
- **Scope predicate.** Correct under `## Helper-reuse obligations (DRY)`; absent from the other four
  homes. bld-final's `## Fourth implementation review` P2-5 row still describes the one-argument
  predicate, unstamped.
- **bld-final still presents the superseded transport as the fix.** `## Fourth implementation
  review` P1-2 reads "`orders/sets.py::_CaptureState` is a frozen dataclass ... `_record_applied_normalization`
  REBINDS the variable, and `_input_has_active_terms` consumes by rebinding too." The section intro
  stamps only P2-2 and P2-3 as partial; this row carries no stamp. `## Gate re-run - 2026-09-10` uses
  singular-record semantics, unstamped. `_CaptureState` no longer exists in the package.
- **`## Fifth implementation review` overstates.** Its read table shows the synthesized relation
  row as `0 | 0 | 0` and then says "The one read counted during finalization in the relation row is
  the finalizer's OWN Relay composite-pk gate" - a read counted in a row that shows zero, in a table
  with no finalization column. It records `uv run pytest` and the sharded tier each with ONE failure
  and no exit status, while [build-050][build-050]'s new `Status:` calls both "re-run green". Its
  synthesized-relation "real request" is `schema.execute_sync` under a plain `strawberry.Schema`
  (see P1-1 above), stated as if it covered the shipped schema shape. Floor is honestly marked not
  run and the gate honestly marked not green; the section does not itself state that any later
  production change invalidates its figures (that stamp exists only at file level and on the fourth
  section).
- **build-050 internal staleness.** Its unchecked final item still reads "rerun full coverage and
  sharded verification after remediation" while its own new `Status:` claims those two done and
  floor pending. Slice 2 says "the seal gains the new `unevaluated` option" where the spec checklist
  says `require_unevaluated`. The spec's checklist is entirely `[ ]` while build-050's is `[x]`
  through Slice 5 (checkboxes stay unticked by convention in the spec; the point is that the two
  plans' `Status:` prose, not the boxes, must agree).
- **GLOSSARY hunk.** The `DjangoListField` row states read-once for the seed, both visibility seals,
  the published `orderBy` and dispatch, omitting the post-`OrderSet` seal Decision 1 names. No hunk
  touches the `DjangoConnectionField` row, so the connection thread-through and the registry-sourced
  relation connection have no glossary statement. The row-bound row's exact-`True` wording is
  consistent with the spec.

**Correction**: home the read-once, ledger, exact-boolean and predicate contracts in all five homes
(one row each is enough); stamp or rewrite the fourth-review P1-2 / P2-5 rows and the gate-re-run
paragraph as superseded; fix the fifth-review table/prose contradiction and replace "re-run green"
with the recorded figures and exit status; re-render the glossary after the connection row is
updated in the DB.

### P3 - convention defects in the added lines

Population: 4302 added lines over 17 files (13 `.py` = 3833; spec 208; bld-final 257; build-050 1;
GLOSSARY 3). Each item below was attributed to this diff by checking the phrase is absent at
`git show HEAD:<path>`.

- **Unresolvable citation added to the spec.** Decision 1 cites
  `registry.py::DjangoTypeRegistry.get_definition`; the class is `TypeRegistry`
  (`django_strawberry_framework/registry.py:107`, method at `:458`) and `DjangoTypeRegistry` occurs
  nowhere in the repository. `check_citations.py` does not read `docs/` prose, so no gate catches
  it. 16 of the 17 `path::Symbol` citations added to the spec resolve; this one does not.
- **Provenance wording added to a standing doc.** Spec, ledger token-identity paragraph: "but it is
  no longer what ..." - "no longer" is on the banned list for standing prose. One added test
  docstring uses "used to" in the sense of "employed to"
  (`tests/test_list_field.py:4419`); pattern hit only, not temporal, no change needed. Zero hits in
  the 49 added test names and zero in error strings.
- **bld-final cites tests that do not exist in any tree.** Added lines name
  `tests/test_list_field.py::test_list_arguments_immutability_and_slots` (actual:
  `test_list_arguments_immutability`) and three `tests/orders/test_sets.py::test_a_descendant_*` /
  `::test_a_worker_thread_running_a_copied_context_cannot_publish_into_the_parents` rows whose
  nearest existing tests are `test_an_unrelated_descendant_application_is_never_claimed` and
  `test_a_worker_threads_application_reaches_the_ledger_its_parent_claims_from`. Added lines at
  bld-final `:330` and `:431` still cite `orders/sets.py::_CaptureState`, a class that no longer
  exists. Scratchpad provenance is allowed; a description of a test that does not exist is not.
- **Pre-existing, not this diff's, recorded so nobody re-derives them:** build-050's two `<!-- docs/ -->`
  definitions are repo-root-relative (`docs/spec-050-...`) and resolve to a missing
  `docs/builder/docs/...` path; bld-final's `<!-- docs/builder/ -->` group is out of alphabetical
  order; the spec has two unused definitions (`resource-policy-extension`, `types-resolvers`);
  `_staff_client` (`examples/fakeshop/test_query/test_list_field_api.py:62`) hand-rolls a `User`
  through `create_user` rather than `create_users(N)`, and three new live rows take it as their first
  statement (`:1323`, `:1592`, `:1620`).

### Design note (no correction demanded) - identity-keyed claims and input-transforming overrides

`_NormalizationLedger.claim` matches by `orderset_class is` and `input_value is`
(`orders/sets.py:146`). A public override that rewrites the input before delegating
(`super().apply_async(cleaned, ...)`) attests under `cleaned`; the guard asks about the original
object, claims nothing, and falls back to the three-call path over the ORIGINAL input. Purity is
still checked, but `has_active_order` is then derived from a normalization of an input the base
never applied. The review's alternative design (a result-carried attestation travelling with the
returned queryset) would not have this edge. Identity is the right key for the delegation shapes the
review named, and equality would reopen consumer `__eq__` dispatch, so this is recorded as a known
boundary for the spec to state, not as a defect.

## Corrections verified in this pass

Preserve these; each was checked against the code, and each proof was checked for whether it would
still pass with the fix reverted.

- **List field reads its definition once, and the proofs are consequential.**
  `DjangoListField` takes the validator's returned definition (`list_field.py:1074`), reads model
  and sidecar from it (`:1075-1076`), seeds with `base_queryset(target_model)` (`:1107`) and threads
  `model=` through both colorings into `apply_type_visibility_*` and `_validate_post_orderset_result`
  (`:909`, `:913-919`, `:926-933`, `:962`, `:966-972`, `:979-986`). `_captured_model`
  (`utils/querysets.py:3426-3437`) is the seam; both seals of one call take the same value
  (`:3480`, `:3600`). With the fix reverted, `test_list_field_reads_the_target_definition_once_and_dispatches_through_it`
  (`tests/test_list_field.py:2706`) would seed the decoy's `Category` table and fail
  `"genuine-row" in returned` as well as the `reads` assertion; the consumer-resolver proof
  (`:2814`) would have the seals reject the `Item` queryset against the decoy model; the seals proof
  (`:2894`) would record `seen_models == [Category]`. None can pass vacuously.
- **Connection threads the definition end to end.** `_connection_type_for`,
  `_generate_connection_class`, `_build_total_count_connection`, `_synthesized_signature`,
  `_build_connection_resolver`, `_build_relation_connection_resolver`, `_build_windowed_fallback`,
  both pipelines and `_finalize_queryset` take `definition`; the default seed is
  `base_queryset(definition.model)` (`connection.py:1979`); the finalizer resolves the target's
  definition once from the registry and fails loudly on a miss (`types/finalizer.py:721-729`). The
  cold-cache root proof (`tests/test_connection.py:2483`) is armed through a real
  `execute_sync` request with a decoy over another model and would fail on both the counter and the
  returned rows if any of `initial_queryset` / `model_for` / the `_finalize_queryset` getattr came
  back. Out-of-package callers of every changed signature were swept: all are in `tests/` and all
  pass the new arity.
- **The ledger satisfies every property the review listed.** (a) `apply_sync` / `apply_async`
  remain the only dispatch (`orders/sets.py:744`, `:777`); (b) nothing touches `info.context`
  (proven at `tests/orders/test_sets.py` `test_public_apply_never_writes_the_consumer_context` and
  live at `test_list_field_api.py` / `test_list_field_async_api.py` context rows); (c) `publish`
  appends, nothing overwrites (`:127-130`); (d) child task, copied context, worker thread and nested
  `OrderSet` are each proven (`tests/orders/test_sets.py:1874`, `:2205`, `:2053`, plus the
  24-thread barrier test); (e) two applicable attestations that disagree raise (`:151-158`, proven
  at `:1973`); (f) `finally` resets the binding and empties the ledger (`:201-205`, proven for the
  exception exit). The lock covers only identity comparisons and list appends; the disagreement
  `raise` happens after the `with` block releases it, so no exception can wedge it; `close()` racing
  a fire-and-forget child appends to an emptied ledger that no later resolution can see (each scope
  allocates a new object). Strong references to `input_value` last one resolution, no longer than
  `args_record` itself. Growth is bounded by the consumer's own number of applications.
- **The live A/B/B row genuinely depends on the ledger.**
  `test_async_child_delegated_impure_ordering_is_rejected`
  (`examples/fakeshop/test_query/test_list_field_async_api.py:897`) asserts
  `calls["n"] == 2` (`:927`). A rebinding-only transport leaves the parent with no attestation,
  runs two more normalizations (B/B), accepts, and returns data: three calls, `data` populated, both
  assertions fail. The usability row (`:874`) proves the override still orders and pages through a
  real `AsyncClient` request. The package nested-`OrderSet` row (`tests/orders/test_sets.py:2053`)
  raises only because the nested record is filtered by class identity; a single slot would compare
  B against the nested DESC record and accept.
- **Exact boolean, both layers.** `validate_trusted_flag` (`resource_policy.py:685-697`) at the
  factory (`list_field.py:1069`), `trusted is True` in the primitive (`:723`); truthy and falsy
  non-`bool` rows in `tests/test_resource_policy.py:302-352` and factory rows in
  `tests/test_list_field.py:2985`. No other package factory exposes a `trusted` flag (`rg` over the
  package: only `resource_policy.py` / `list_field.py`).
- **Combined oracle is raw bytes.**
  `test_holder_branches_combined_legacy_branch_matches_the_legacy_reference`
  (`examples/fakeshop/test_query/test_list_field_api.py:1323`) asserts
  `response.content == legacy_response.content` for both the omitted and the all-null request
  (`:1373`) while keeping SQL, marks and visibility-count assertions.
- **Scope predicate takes the captured sidecar.** `_order_normalization_scope(args_record,
  orderset_class)` (`list_field.py:861-893`) opens the capture only when `order_by_supplied and
  orderset_class is not None and offset > 0`; the no-`OrderSet` direct-call row is in
  `test_the_capture_scope_opens_only_where_the_offset_guard_can_use_it`
  (`tests/test_list_field.py:2655`).
- **Routing intent carried forward from the previous round.** `_routing_hints_equal` is now
  identity-only (`utils/querysets.py:2763-2790`), pinned by
  `tests/utils/test_querysets.py::test_routing_hints_equal_rejects_equal_primitives_that_are_not_identical`.
  Fail-closed and correct for a private seal; noted because `tests/utils/test_querysets.py` carries
  spec-050 hunks the task's file list omitted.

## Convention compliance

Swept over the 4302 added lines of the 17 in-scope files, with HEAD attribution for every hit.

| Rule | Verdict | Evidence |
| --- | --- | --- |
| Root-cause fix, no narrowing | **Blocked** | P1-1 residual above; the wave-off is in a docstring and in Decision 1. |
| Live-first placement | Pass for reviewed additions | 9 of 49 added package tests execute GraphQL; all are definition-read counters, converter-call counters or `ContextVar`-reset assertions, the package-tier exception the review allowed. Child-delegation rejection and usability, context isolation and the byte oracle are live HTTP. |
| Fakeshop seed discipline | Pass with a pre-existing caveat | 12 added live rows touch only library `Branch` / `Genre` via inline `create`, which the library exception permits; 0 hand-rolled Category/Item/Property/Entry. Three rows start with `_staff_client()`, a pre-existing helper that hand-rolls a `User`. |
| Tests accompany production behavior | Partial | Every threaded seam has a test; the nested-planner read has none, and the warm-cache / async-coloring / no-argument rows are missing (P2). |
| `pragma: no cover` as remediation | Pass | None added in the reviewed hunks. |
| No process provenance in code / test names / errors | Pass in `.py`; one spec hit | 0 hits in 49 added test names and 0 in error strings; the spec gained one "no longer" (P3 above). Pre-existing hits at HEAD ("P1-B" spec-030 label cites, "used to spell this out") are not this diff's. |
| `path:NN` outside scratchpads | Pass | 0 hits in added lines of the 16 non-scratchpad files. |
| `path::Symbol` citations resolve | One failure | `registry.py::DjangoTypeRegistry.get_definition` (P3 above); 16/17 added spec citations resolve; GLOSSARY 16/16. |
| Markdown link scaffold | Pass on this diff's lines | All three docs carry one block with 10 headers in order; 0 undefined refs, 0 inline cross-file links. Pre-existing ordering / root-relative-path defects listed under P3. |
| ASCII-only `.py` | Pass | 0 non-ASCII bytes over 3833 added `.py` lines. |
| `docs/feedback*.md` never named in code / DB | Pass | 0 hits over the package, three test trees, spec, KANBAN.md, TREE.md, GLOSSARY.md; `strings db.sqlite3` count 0. |
| Concurrent work preserved | Pass for this review | Nothing reverted, stashed or staged; `docs/feedback2.md` untouched. |

## Required correction order and gate

1. Derive the plan-time keyset context from the registry definition and retire the type-keyed
   request-time wrapper from execution paths; correct the Decision 1 sentence and the `keyset.py`
   docstring that license it.
2. Re-arm the connection read-once proofs under `DjangoSchema` with the optimizer installed, with a
   `cursor_field`-bearing decoy, through warm caches and the async coloring; add the no-argument
   list-shape row.
3. Remove the dead `_dst_node_type` slot and its false comment.
4. Home the four contracts in all five spec homes, stamp the superseded fourth-review rows, fix the
   fifth-review table/prose contradiction and the "re-run green" wording in build-050, repair the
   `TypeRegistry` citation and the "no longer" sentence in the spec, and retarget bld-final's
   nonexistent test names.
5. Then formatting, lint, structural/link checks, the default and sharded full suites at 100%
   package coverage, and the supported-floor verification. Any production change after a recorded
   run invalidates it.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../AGENTS.md
[start]: ../../START.md

<!-- docs/ -->
[spec-050]: ../spec-050-list_field_arguments-0_0_15.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->
[bld-final]: ../builder/bld-final.md
[build-050]: ../builder/build-050-list_field_arguments-0_0_15.md

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
