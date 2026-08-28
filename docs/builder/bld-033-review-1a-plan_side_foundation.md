# Build: Review R1a — plan-side foundation conformance (`spec-033` Decisions 3 / 4 / 6 / 9 / 11)

Spec reference: `docs/SPECS/spec-033-connection_optimizer-0_0_9.md` (Slice checklist lines 53-61; Decisions 3/4/6/9/11 lines 235-333; `## Edge cases and constraints` lines 358-377; `## Test plan` Slice 1 lines 387-412; Definition-of-done items 2/3/4 lines 507-509)
Rationale companion: `docs/SPECS/appx/spec-033-connection_optimizer-0_0_9-rationale.md` (Decisions 3/4/6/9/11 read in full before this pass)
Status: review-accepted

**Shape.** Read-only conformance cohort of the `033` residual reconciliation cycle
([`build-033-connection_optimizer-0_0_9.md`][build-033] `## Cycle shape` item 2). There is no Worker 2
diff: the subject is shipped `HEAD`. This cohort writes no source, no spec, and no test. The
`## Plan (Worker 1)` and `## Build report (Worker 2)` sections of [`ARTIFACT.md`][artifact-md] are
deliberately absent, not omitted — no planner or builder pass ran. Everything they would carry that
applies to a read-only verification pass (the validation run, the failability position, the hot-path
and floor declarations, the ownership partition) is folded into `## Review (Worker 3)` below.

Raw `path:NN` references appear inline **alongside** the symbol identifier throughout, per
[`AGENTS.md`][agents] #"Source references in docs and code comments" (per-cycle scratchpad carve-out) and
[`BUILD.md`][build-md] `### Output files, and why their line numbers are NOT canonical`.

---

## Review (Worker 3)

### Verification method

Every contract below was proven present in source or proven absent. Nothing was accepted because the
spec asserts it. Where the spec names a test, the test's **body** was read against the spec sentence
it is supposed to pin, per [`worker-3.md`][worker-3] "A named test is not a passing contract".
Every count in this artifact was measured at the moment it was written.

Post-ship attribution is by **commit hash plus the "idea #N" label the commit or test itself uses**;
no card id is invented. Each module's creation commit was re-derived here rather than inherited:

```shell
git log --diff-filter=A --format='%h %ad %s' --date=short -- django_strawberry_framework/<path>
```

| Module | Created by | Date |
|---|---|---|
| `optimizer/selections.py` | `6912ca92` "DRY pass (docs/feedback.md round): query-source, selection, and set-family substrates" | 2026-06-13 |
| `utils/connections.py` | `0e864b7e` "Refactor connection optimizer: centralize window bounds and sidecar kwargs" | 2026-06-13 |
| `optimizer/nested_fetch.py` | `57cbd32a` "feat: Pluggable nested-connection fetch strategies + Postgres lateral backend" | 2026-07-07 |
| `optimizer/join_taxonomy.py` | `57cbd32a` (same commit) | 2026-07-07 |
| `optimizer/lateral_fetch.py` | `57cbd32a` (same commit — **re-derived; the dispatch did not attribute this one**) | 2026-07-07 |
| `keyset.py` | `51421e54` "feat(relay): keyset value-encoded cursors via Meta.cursor_field (idea #3 / BACKLOG-39)" | 2026-07-10 |
| `optimizer/nested_planner.py` | `991d5120` "fix(optimizer): isolate nested planning" | 2026-07-13 |
| `optimizer/single_parent_fetch.py` | `deeb53b4` "feat(optimizer): single-parent fast path, lateral visibility scope, recognizer hardening" | 2026-07-17 |

One further attribution this cohort measured and the dispatch did not supply: the
`Meta.relation_shapes` implicit default flipped from `"both"` to `"connection"` in
`567cc6d0` (2026-08-04, "feat(security): bound execution resources, fail closed on disclosure, and
pin the supply chain"), proven by `git log -S'DEFAULT_RELATION_SHAPE = "connection"'` /
`-S'DEFAULT_RELATION_SHAPE = "both"'` over `django_strawberry_framework/types/base.py`. Current value:
`django_strawberry_framework/types/base.py:112` #`DEFAULT_RELATION_SHAPE = "connection"`.

### Contracts proven PRESENT in shipped source

Symbol-qualified evidence. Each of these delivers what the spec says, at the stated site.

1. **`relation_connections` definition slot exists** (spec line 55; Decision 3 line 237; DoD item 3
   line 508). `django_strawberry_framework/types/definition.py::DjangoTypeDefinition
   #"relation_connections: dict[str, str] | None = None"` (`:194`), documented in the invariants
   docstring at `:91-103`.
2. **Written by the Phase-2.5 synthesis; suppressed shapes record nothing.**
   `types/finalizer.py::_record_relation_connection` (`:524`) is called from
   `types/finalizer.py::_synthesize_relation_connections` (`:612`) at `:728` (re-entrancy branch) and
   at `:795` (first-attach branch) — **both call sites sit after** the three suppression `continue`s:
   `name in definition.consumer_authored_fields` (`:681`), non-Relay-Node target (`:686-705`), and
   `shape == "list"` (`:708`). Suppressed shapes therefore cannot record. Proven structurally, not by
   test assertion.
3. **Recognition is definition-metadata-driven and fires before the unknown-name guard.**
   `optimizer/walker.py::_resolve_selection_target` (`:245`) reads
   `relation_connections.get(snake)` (`:255`) as the fast path, then forward-camelizes through the
   schema name converter on a miss (`:262-267`); `optimizer/walker.py::_walk_selections` (`:419`)
   reads the slot at `:463` and dispatches on `resolved[0] == "connection"` at `:486` — before the
   `django_field is None` handling at `:508`. No `_connection`-suffix guess and no `connection.py`
   import exists in `walker.py` (its local imports, `walker.py:14-37`, contain no `..connection`).
4. **Primary-type-only nested recognition** (Decision 3 closing paragraph; `## Edge cases` line 370).
   `optimizer/walker.py::_walk_selections` resolves the definition through
   `_resolve_field_map(model, source_type=source_type)` (`:453`), and the two nested recursions
   deliberately omit `source_type` (documented at `walker.py:462-478`), so a nested level reads
   `registry.get(model)` — the primary type. Pinned by
   `tests/optimizer/test_walker.py::test_secondary_type_relation_shapes_nested_recognition` (`:4546`).
5. **Argument-aware alias classification.** `optimizer/walker.py::_merge_aliased_selections`
   (`:1219`) now records `_optimizer_response_key_arguments` on the merged selection
   (`:1289-1292`; recorded on the merge branch at `:1277` through
   `::_record_response_key_arguments`, `:1298`), compares payloads
   pagination-normalized (`:1330 _normalized_alias_payload`), and exposes both
   `_response_key_arguments_conflict` (`:1352`) and `_aliased_arguments_diverge` (`:1363`). The
   spec's stated prerequisite ("preserves per-response-key argument payloads") is delivered
   verbatim; what happens *after* it is inverted (see Divergence D4).
6. **Union publish of all three correctness sentinels** (spec line 57; Decision 8 second paragraph).
   `optimizer/extension.py::DjangoOptimizerExtension._publish_plan_to_context` (`:1277`) calls
   `self._stash_union(...)` for `DST_OPTIMIZER_FK_ID_ELISIONS` (`:1300`), `DST_OPTIMIZER_PLANNED`
   (`:1313`) and `DST_OPTIMIZER_LOOKUP_PATHS` (`:1314`); `DST_OPTIMIZER_PLAN` stays last-wins
   (`:1296`). `_stash_union` (`:1318`) is set-typed with a subset early-out. Pinned by
   `tests/optimizer/test_extension.py::test_publish_plan_to_context_unions_parent_and_nested_sentinel_sets`.
7. **Windowed `Prefetch` under `_dst_<field>_connection`.** `optimizer/nested_fetch.py::attach_windowed_prefetch`
   (`:284`) builds `Prefetch(..., to_attr=request.to_attr)` (`:319`) with the `to_attr` grammar owned
   by `optimizer/nested_planner.py::relation_connection_to_attr` (`:723`). The default shape is
   exactly `_dst_<field>_connection`.
8. **Deterministic-order cursor-parity invariant and its hoisted helper** (Decision 4
   `**Deterministic order**` bullet line 248; Decision 11 line 328; DoD item 4).
   `optimizer/plans.py::ends_in_unique_column` (`:811`) and `::deterministic_order` (`:887`) are
   the one implementation; `connection.py:129` #`_ends_in_unique_column = ends_in_unique_column`
   imports it back, and `connection.py:84` imports `effective_connection_order`. Plan-time reads it
   at `optimizer/nested_planner.py::plan_connection_relation #"effective_connection_order("` (`:1284`);
   resolve-time at `connection.py::_finalize_queryset #"ordered = effective_connection_order("`
   (`:1605`). Both sides now share `optimizer/plans.py::effective_connection_order` (`:862`) — a
   *strengthening* of the invariant, since the precedence ladder is shared too, not just the
   pk-append rule. Pinned by `tests/optimizer/test_plans.py::TestDeterministicOrderHoistParity`
   (`:1140`, incl. `::test_deterministic_order_matches_connection_reexport` asserting object
   identity) and `::TestEffectiveConnectionOrder` (`:1211`).
9. **`window_partition_for_prefetch`'s per-relation-kind partition keys, including forward M2M
   without `related_name`.** `optimizer/plans.py::window_partition_for_prefetch` (`:903`) exists with
   the spec's raise contract; the derivation is
   `optimizer/join_taxonomy.py::_partition_expr` (`:182`) #`remote_field.attname or remote_field.name`.
   All three kinds plus the accessor-divergence case are pinned by
   `tests/optimizer/test_plans.py::TestWindowPartitionForPrefetch` (`:1059`) —
   `::test_reverse_fk_partitions_by_child_fk_attname`,
   `::test_forward_m2m_partitions_by_reverse_query_name`,
   `::test_reverse_m2m_partitions_through_forward_field_name`,
   `::test_forward_m2m_partition_diverges_from_accessor`. **Caveat: this helper has zero production
   callers** — see DRY finding DRY-1.
10. **The raw-Django-relation-field requirement** (the one Risks rule Slice 0 held back in the spec,
    Decision 4 line 249). `optimizer/nested_planner.py::_raw_relation_field` (`:1043`)
    #`model._meta.get_field(relation_field_name)` resolves the live field, and
    `plan_connection_relation` passes it to `classify_relation_join(raw_relation_field)` (`:1194`)
    and onto `NestedConnectionRequest(django_field=raw_relation_field, ...)`. The rule survives its
    hold-back; only the owning symbol path moved (see D5).
11. **`apply_window_pagination`'s annotations, range filters and reverse branch.**
    `optimizer/plans.py::apply_window_pagination` (`:946`) annotates `WINDOW_ROW_NUMBER`
    (`plans.py:744` #`"_dst_row_number"`) and `WINDOW_TOTAL_COUNT` (`:745`), filters the row-number
    range, and keeps the reverse branch via `WINDOW_ROW_NUMBER_REVERSED` (`:746`) with
    `_dst_row_number` staying **forward** (matching `## Edge cases` line 366 exactly). It also
    applies `.order_by(*order_by)` to the queryset itself. Pinned by
    `tests/optimizer/test_plans.py::TestApplyWindowPagination` (`:807`) and
    `::test_applies_order_by_to_queryset_not_just_the_window` (`:970`).
12. **The `relay_max_results` cap is read from the schema config and shared plan/resolve.**
    `optimizer/nested_planner.py::_relay_max_results_from_info` (`:769`) and
    `utils/connections.py::resolve_relay_max_results` (`:674`) both dig through the one
    `utils/typing.py::schema_config_from_info`. Pinned by
    `tests/optimizer/test_walker.py::test_window_respects_relay_max_results`.
13. **Malformed-slice error locality: no window, resolver keys still recorded** (Decision 4
    `**Slice arithmetic**` line 252; spec line 58 step (e)).
    `optimizer/nested_planner.py::_connection_window_slice_from_arguments` (`:803`) returns `None` on
    `ValueError` / `TypeError`; `_divergent_key_windows` (`:923`) routes it to `malformed` (`:995`); and
    `plan_connection_relation` records identities for the malformed keys
    (`:1162-1190`, #"Malformed pagination (Decision 4 step f") while emitting no window. The
    load-bearing distinction from the fully-unplanned fallbacks is preserved. Pinned by
    `tests/optimizer/test_walker.py::test_malformed_slice_arguments_emit_no_window_but_record_resolver_key`.
14. **Scalar-only `pageInfo` / `totalCount` selections are PLANNED with the minimal
    pk/connector/order projection** (Decision 4 `**Scalar-only connections**` line 251; Decision 6
    closing paragraph). `optimizer/nested_planner.py::plan_connection_relation` sets
    `scalar_only = not node_selections` (`:1213`) and calls
    `_project_scalar_only_window` (`:652`) at `:1296`. Pinned by
    `tests/optimizer/test_walker.py::test_scalar_only_pageinfo_and_total_count_are_window_planned`
    (`:3302`) and `::test_scalar_only_window_projects_pk_connector_and_order_columns` (`:3322`,
    which asserts `defer is False` and `{"id", "shelf_id"} <= set(only_fields)`).
15. **`_connection_node_child_selections` remained in `extension.py` as a thin composition** (spec
    line 54, the surviving half of Decision 9).
    `optimizer/extension.py::_connection_node_child_selections` (`:602`) supplies only the root
    response path and delegates the edges→node composition to
    `optimizer/selections.py::connection_node_children` (`:563`).
16. **No-leakage on refusal.** `plan_connection_relation` builds the child plan against a throwaway
    `sub_plan` (`:1236`) and absorbs it via `plan.merge_metadata_from(sub_plan)` (`:1421`) **only**
    after `planned_keys` is non-empty — so a refused window leaks no child resolver keys, FK-id
    elisions, or `cacheable` flip into the parent. This delivers Decision 6's "no
    `planned_resolver_keys` entry" more strictly than the spec text describes.

### Contracts proven ABSENT or DIVERGENT

Each carries its class (**build-time** = the build shipped something else; **post-ship** = a later
commit changed this card's surface) and its full per-site list.

#### D1 — Decision 9's consolidation target is `optimizer/selections.py`, the module Decision 9 rejects by name. `post-ship` (`6912ca92`), on top of a `build-time` divergence in the symbol list.

Shipped shape: the helpers are **public** in `optimizer/selections.py` — `named_children` (`:428`),
`with_runtime_prefix` (`:449`), `node_children_with_runtime_prefix` (`:477`), `response_key` (`:369`),
`response_keys` (`:374`), `should_include` (`:348`), `is_fragment` (`:334`),
`included_field_selections` (`:393`), `connection_node_children` (`:563`), `direct_child_selected`
(`:598`). Both consumers import from there under `_`-prefixed back-compat aliases:
`optimizer/walker.py:37-61` and `optimizer/extension.py:102-126`. `extension.py:119-121` states
outright that it "no longer imports the converted-selection helpers back from `walker`". That retires
Decision 9's *entire* argument: the forced import direction, the "one implementation or two drifting
ones" justification, and the explicit rejection of `optimizer/selections.py`.

Separately, **two of the six symbols Decision 9 names never existed** — `_converted_selection_included`
and `_is_converted_fragment` return zero matches tree-wide outside the spec itself
(`grep -rn` over `*.py` + `*.md`: 3 spec lines, 0 source lines). At the shipping commit they were
collapsed into `_should_include` / `_is_fragment`, recorded in the then-current
`git show 711b4a2f:django_strawberry_framework/optimizer/walker.py` #"`_converted_selection_included`
is just" comment. That half is **build-time**, not post-ship.

Sites to correct:
- spec `:54` — Slice-1 checklist sub-bullet (names the four symbols and `optimizer/walker.py` as target)
- spec `:102` — `## Current state` "The selection-unwrap helpers live on the extension side" bullet
- spec `:314-318` — Decision 9 body (names six symbols; `extension.py` imports "from the walker")
- spec `:328` — Decision 11 `**Source (build proper)**` "and the consolidated selection helpers"
- spec `:346` — `## Implementation plan` Slice-1 row, `optimizer/walker.py` "(helpers in ...)" and the
  new-test list's "helper-move no-regression"
- spec `:412` — `## Test plan` Slice 1 "Helper-move no-regression" bullet (the assertion it names is
  still green, but for the `selections.py` shape)
- spec `:507` — DoD item 2 "The `edges { node }` selection helpers live in `optimizer/walker.py`"
- rationale `## Decision 9` `### Alternatives considered (and rejected)` — "**A third module
  (`optimizer/selections.py`).** Rejected" is now false; and `### Changes this Decision underwent`
  currently reads "Nothing later reopened it", which is the sentence the shipped tree falsifies.

#### D2 — Decision 11's module map is six modules and one package-root module short. `post-ship`.

Shipped optimizer layout (`ls django_strawberry_framework/optimizer/`): `_context.py`,
`extension.py`, `field_meta.py`, `hints.py`, `join_taxonomy.py`, `lateral_fetch.py`,
`nested_fetch.py`, `nested_planner.py`, `plans.py`, `predicates.py`, `selections.py`,
`single_parent_fetch.py`, `walker.py`. Of these, six carry this card's vocabulary and did not exist
when it shipped (attribution table above), plus `keyset.py` at the package root. The single largest
move: `991d5120` relocated the nested-connection planner **out of `walker.py`** into
`nested_planner.py`; `optimizer/walker.py::_plan_connection_relation` (`:1406`) is now a
14-line delegator whose whole body is
`_plan_nested_connection_relation(...)` + `plan.merge_from(result.plan)`.

The Decision-11 test map is likewise short by six files. Present and unnamed:
`tests/optimizer/test_selections.py`, `test_join_taxonomy.py`, `test_nested_fetch.py`,
`test_lateral_fetch.py`, `test_single_parent_fetch.py`, `test_nested_index_advisory.py`. And
`optimizer/nested_planner.py` — 1,436 lines, the largest module the card's contract now lives in —
has **no** 1:1 test twin, so the "mirror-one-to-one rule still holds" claim at spec `:329` no longer
holds for the module that owns the planning contract.

Sites to correct:
- spec `:328` — Decision 11 `**Source (build proper):** no new module.` and the whole per-module map
  (`optimizer/walker.py` gains `_plan_connection_relation`; `optimizer/plans.py` gains
  `apply_window_pagination`)
- spec `:329` — Decision 11 `**Source (post-build DRY refactor):** one new module` (a count of one
  where eight landed; `utils/connections.py` is also no longer only the bounds/sidecar home — it now
  owns `FetchMode`, `WindowRangePlan`, `window_range_plan`, `is_ambiguous_empty_window`,
  `split_window_rows`, `assert_window_fetch_mode`, `resolve_relay_max_results`,
  `derive_keyset_window_bounds`)
- spec `:330` — Decision 11 `**Tests:**` map and its "The build proper added no new test file" claim
- spec `:346` — `## Implementation plan` Slice-1 row "Files touched" column
- spec `:56`, `:58`, `:59` — the three Slice-1 sub-bullets that site
  `_merge_aliased_selections` / `_walk_selections` / the window helpers by module
- spec `:475` — `## Doc updates` `docs/TREE.md` bullet names only four modules to refresh
  (doc surface — **recorded as deferred**, this cycle's fence forbids the `docs/TREE.md` edit)
- rationale `## Decision 11` `### Changes this Decision underwent` Revision-4 bullet — "added one
  neutral, cycle-safe module" needs a `**Post-ship:**` sibling naming the eight

#### D3 — `_dst_total_count` is no longer unconditionally annotated, and the spec's own named test now pins the inverse. `post-ship` (`57cbd32a`, "idea #2").

Shipped shape: `optimizer/nested_planner.py::plan_connection_relation` computes
`total_selected = connection_total_count_selected(sel, names=field_names)` and
`has_next_selected = connection_has_next_page_selected(sel, names=field_names)` (`:1333-1334`), then
derives one `utils/connections.py::FetchMode` (`:121`) value per window via
`WindowRangePlan.fetch_mode` (`:330`) and maps it to
`with_total_count = mode is FetchMode.COUNTED` / `next_page_probe = mode is FetchMode.PROBED`
(`:1378-1379`). `optimizer/plans.py::apply_window_pagination` therefore annotates
`_dst_total_count` only when `with_total_count`, and a plain `first: N` edges-only page carries an
n+1 sentinel overfetch instead of a partition `COUNT`.

**The named test now asserts the opposite of the spec sentence.**
`tests/optimizer/test_walker.py::test_nested_connection_planned_as_windowed_prefetch` (`:2700`)
docstring: "so the conditional-count contract (workstream B) plans the row-number window WITHOUT
`_dst_total_count`". The spec's `## Test plan` entry for that exact test name (spec `:390`) says the
queryset "carries `_dst_row_number` / `_dst_total_count` annotations". Same name, inverted assertion —
the exact class `worker-3.md` warns about. New coverage:
`::test_nested_connection_total_count_planned_only_when_observable` (`:2871`, parametrized).

Sites to correct:
- spec `:249` — Decision 4 `**Window**` bullet (states both annotations unconditionally)
- spec `:59` — Slice-1 checklist `optimizer/plans.py` window-helper sub-bullet (same)
- spec `:390` — `## Test plan` `test_nested_connection_planned_as_windowed_prefetch` entry
- spec `:509` — DoD item 4 "`_dst_row_number` / `_dst_total_count` annotations"
- spec `:365` — `## Edge cases` "Parents with no related rows … `totalCount` is `0`" (now depends on
  whether the count was annotated at all)
- spec `:113` — Goal 2 "`totalCount` (from `_dst_total_count`, when the target opted in)" —
  the gate is now *observability*, not just opt-in
- rationale `## Decision 4` `### Changes this Decision underwent` — needs a `**Post-ship:**` bullet
  for the conditional count and the count-free `hasNextPage` probe

#### D4 — Decision 6 fallback shape 2 is inverted: divergent aliases are now PLANNED, one window per response key. `post-ship` (`57cbd32a`, "idea #2").

Shipped shape: `optimizer/nested_planner.py::plan_connection_relation` selects the scheme with
`divergent = aliased_arguments_diverge(sel)` (`:1110`), feeds `sel._optimizer_response_key_arguments`
to `_divergent_key_windows` (`:1148-1157`), and issues one `NestedConnectionRequest` per response key
under `relation_connection_to_attr(relation_field_name, resp_key)` — the `_dst_<field>$<key>_connection`
grammar (`nested_planner.py:723-736`). Both keys' resolver identities are recorded
(`_identities_for_response_keys`, `:1427-1430`).

`tests/optimizer/test_walker.py::test_divergent_aliases_plan_one_window_per_response_key` (`:3580`)
names the change in its own docstring: "The idea-#2 inversion of the historical spec-033 Decision 6
fallback", and asserts `set(by_attr) == {"_dst_books$a_connection", "_dst_books$b_connection"}` plus
`len(plan.planned_resolver_keys) == 2`. Six sibling per-key tests exist (`:3627`, `:3675`, `:3723`,
`:3763`, `:3804`, `:3855`, `:4064`).

`test_fallback_not_planned_divergent_aliases` is **MISSING by design** — re-measured here: zero
matches for `def test_fallback_not_planned_divergent_aliases` across `tests/` and `examples/`. So is
`test_fallback_not_planned_distinct_target` (zero matches); its contract lives in
`test_distinct_child_queryset_left_unplanned_for_correct_total_count`, which is present.

Sites to correct:
- spec `:284` — Decision 6 item 2 (the whole item, incl. "One `to_attr` cannot serve two windows;
  per-alias windows are a follow-up" and "The current first-arguments-win merge is explicitly not
  enough for this card")
- spec `:279` — Decision 6 heading text ("sidecar input, divergent aliases, hints, and scalar-only
  connections") and the "**Four** nested-connection shapes are deliberately not window-planned" opener
- spec `:361` — `## Edge cases` "**Identical-argument aliases merge; divergent ones fall back.**"
- spec `:60` — Slice-1 checklist fallback sub-bullet ("aliased duplicates with divergent pagination
  or sidecar arguments … left **unplanned**")
- spec `:252` — Decision 4 `**Slice arithmetic**` closing clause "whereas the sidecar /
  divergent-alias / hint / distinct fallbacks stay fully unplanned"
- spec `:253` — Decision 4 `**`to_attr` isolation**` bullet ("the window lands on
  `_dst_<field>_connection`, **never** the relation accessor" is still true; the *one*-`to_attr`
  premise is not — the grammar now has a per-key form)
- spec `:404` — `## Test plan` `.../..._divergent_aliases / ..._distinct_target` names
- spec `:346` — `## Implementation plan` Slice-1 new-test list "fallback non-planning ×4" and
  "divergent-alias wrong-plan absence"
- spec `:509` — DoD item 4 "leaves the four Decision 6 fallback shapes (sidecar input, **divergent
  aliases**, `SKIP` hint, `.distinct()` target) unplanned"
- rationale `## Decision 4` `### Alternatives considered (and rejected)` — "**Per-alias windows for
  aliased nested connections with divergent pagination.** Rejected for `0.0.9`" is the rejected
  alternative the tree now implements
- rationale `## Decision 6` `### Justification (moved from the spec)` — "the matrix is monotonic: no
  query that works today changes results or stops working" is the claim the inversion needs a
  `**Post-ship:**` note against

#### D5 — the fallback matrix at `HEAD` has nine fully-unplanned shapes, not four, and the DISTINCT guard moved and generalised. `post-ship` (`57cbd32a` + `51421e54` + `deeb53b4`).

Measured by reading every `return NestedConnectionPlanResult(plan=plan)` / `fallbacks.append(...)`
exit in `optimizer/nested_planner.py::plan_connection_relation` and `::_divergent_key_windows`:

| # | Shape | Site | Spec bullet? |
|---|---|---|---|
| 1 | sidecar `filter:` / `orderBy:` (per key) | `_divergent_key_windows:976` #`fallbacks.append((resp_key, "sidecar arguments"))` | yes (item 1) |
| 2 | `OptimizerHint.SKIP` on the relation | `plan_connection_relation:1112` #`if hint_is_skip(hints_map.get(relation_field_name)):` | yes (item 3) |
| 3 | unwindowable child queryset — `sliced` / `select_for_update` / `combined` / `distinct` / `values` | `plan_connection_relation:1228` #`if unwindowable_child_queryset_reason(base_queryset) is not None:`; classifier at `optimizer/nested_fetch.py::unwindowable_child_queryset_reason` (`:76`) | **partly** (item 4 is the `distinct` reason only) |
| 4 | `UnwindowableConnection` — `after`+`last`, inverted `after`/`before` interval, every backward keyset shape | `_divergent_key_windows:991-992`; raised in `utils/connections.py::derive_connection_window_bounds` (`:566`) | **no** |
| 5 | reversed `last: 0` | `_divergent_key_windows:998-999` #`if reverse and limit == 0:` | **no** |
| 6 | one response key with two different argument payloads | `plan_connection_relation:1090` #`if response_key_arguments_conflict(sel):` | **no** |
| 7 | unwindowable relation kind (`join.windowable` false) | `plan_connection_relation:1195` | **no** — the spec says the helper *raises*; see below |
| 8 | `field_map` miss / `related_model is None` | `plan_connection_relation:1087`, `:1125` | **no** |
| 9 | active strategy refused every window | `plan_connection_relation:1412` #`if not planned_keys:` | **no** |

Two sub-divergences inside this:

- **The DISTINCT guard moved from post-build to pre-build, and became one reason of five.** Decision 6
  item 4 (spec `:290`) states the guard "sits at the end of child-queryset construction, before the
  window is applied — a single `query.distinct` check". Shipped: the classifier runs on
  `base_queryset` **before** child-plan application (`plan_connection_relation:1222-1229`), and the
  code states the inverse of the spec's placement outright: `nested_planner.py`
  #"No post-build re-check: the classified base queryset is the single strategy-independent gate".
- **Unsupported relation kinds no longer raise on the planning path.** Decision 4
  `**Partition key**` (spec `:247`) says "Unsupported relation kinds raise a package-internal
  planning error and fall back unplanned". Shipped: `plan_connection_relation` reads
  `join = classify_relation_join(raw_relation_field)` (`:1194`) and returns unplanned on
  `not join.windowable` — no exception. `optimizer/join_taxonomy.py::classify_relation_join` (`:290`)
  documents "Never raises". The raise survives only in the test-only shim (DRY-1).
  `GenericRelation` also joined `WINDOWABLE_RELATION_KINDS` (`join_taxonomy.py:73`), a fourth relation
  kind the spec's partition list does not mention.

Sites to correct:
- spec `:279-291` — the whole Decision 6 fallback matrix and its "Four … shapes" framing
- spec `:290` — item 4's guard-placement sentence and "a single `query.distinct` check, whatever the source"
- spec `:250` — Decision 4 `**DISTINCT-target guard**` bullet (same placement claim)
- spec `:247` — Decision 4 `**Partition key**` "Unsupported relation kinds raise" + the three-kind list
- spec `:369` — `## Edge cases` "**`.distinct()` child querysets are left unplanned**"
- spec `:366` — `## Edge cases` "`before` + `last` combinations that the offset arithmetic cannot push
  down fall back per-parent" (accurate in spirit; the shipped classifier is
  `UnwindowableConnection` and covers three shapes, not one)
- spec `:60` — Slice-1 checklist fallback list
- spec `:404` — `## Test plan` fallback-test names
- spec `:509` — DoD item 4 "the four Decision 6 fallback shapes"
- spec `:125` — `## Non-goals` "**Keyset / column-anchored cursors.** … stay in `BACKLOG.md` item 39" —
  `keyset.py` shipped (`51421e54`, "idea #3 / BACKLOG-39") and the nested planner now forks through
  `_keyset_window_slice_from_arguments` (`:861`), so this Non-goal is spent
- spec `:123` — `## Non-goals` "**Windowed planning for sidecar-filtered nested connections.**" is
  still accurate and needs no change (verified, not assumed)

#### D6 — `first: 0` and overshot `after:` no longer fall back per-parent; marker rows disambiguate them in one query. `post-ship` (`57cbd32a`, "idea #2").

Shipped shape: `utils/connections.py::is_ambiguous_empty_window` (`:179`) identifies the two shapes
and `::window_range_plan` (`:360`) sets `add_marker_rows` (`:428`) so the range filter ORs in each
partition's row 1 — the marker-only list then carries the real count. The predicate's docstring says
so directly: #"Workstream C disambiguates these shapes with marker rows". Pinned by
`tests/optimizer/test_plans.py::TestApplyWindowPagination::test_ambiguous_shapes_keep_partition_marker_row`
(`:828`).

The consuming half is Decision 5 / `connection.py::_resolve_from_window` and belongs to **cohort
R1b**; recorded here because the `## Edge cases` bullet is a Slice-1-adjacent shared site and must not
be corrected twice differently.

Sites to correct (Slice-1-side only; R1b owns Decision 5 `:270-272` and spec `:64`):
- spec `:364` — `## Edge cases` "**`first: 0` and overshot `after:`**" bullet (whole bullet)
- spec `:365` — `## Edge cases` "**Parents with no related rows**" bullet (its `offset == 0` /
  `limit > 0` precondition is no longer what distinguishes the case)

#### D7 — the plan-time `relay_max_results` cap now also passes through a request-policy `max_page_size` ceiling. `post-ship` (`567cc6d0`).

`utils/connections.py::resolve_relay_max_results` (`:674`) closes with
`return effective_bound(policy_from_info(info).max_page_size, cap)` (`:700`) and states why: "The request
policy is a CEILING over whichever cap won above". The spec's agreement bullet describes only the
schema config.

Sites to correct:
- spec `:367` — `## Edge cases` "**`relay_max_results` agreement**" bullet
- spec `:252` — Decision 4 `**Slice arithmetic**` "`max_results` read from the schema config's
  `relay_max_results` (default 100)"

#### D8 — the fetch mechanism is now a pluggable strategy seam with three backends; the spec describes only the windowed prefetch. `post-ship` (`57cbd32a`, `deeb53b4`).

`optimizer/nested_fetch.py` owns `NestedConnectionRequest` (`:200`), `WindowedPrefetchStrategy`
(`:328`), the single-parent strategy, and the `"auto"` resolution; `optimizer/lateral_fetch.py`
carries the Postgres `CROSS JOIN LATERAL` backend; selection is per-extension-instance via
`nested_connection_strategy=` / `DJANGO_STRAWBERRY_FRAMEWORK["NESTED_CONNECTION_STRATEGY"]`, with a
per-field `OptimizerHint.strategy(name)` override read at
`optimizer/nested_planner.py::_select_nested_strategy` (`:195`). Two further spec-silent additions
on the same path: `::_advise_composite_index` (`:560`, a `DEBUG`-only composite-index advisory) and
`::_log_connection_fallback` (`:1005`, per-response-key fallback logging).

This is not a defect — but Decision 4 and Decision 11 both read as though `apply_window_pagination`
is the only fetch shape, and Decision 11's "no new module" line is what the seam most obviously
contradicts. It needs stating in the spec because the strategy seam has **no owning spec of its own**:
`grep -rln 'nested_fetch\|strategy seam' docs/SPECS/` returns no file whose subject it is.

Sites to correct:
- spec `:241-256` — Decision 4 body (state that the window is *one* strategy's rendering)
- spec `:328-330` — Decision 11 module and test maps
- spec `:346` — `## Implementation plan` Slice-1 row
- spec `:375` — `## Edge cases` "**Backend floor**" bullet (a lateral backend now exists; the
  window-capability caveat is one strategy's)
- rationale `## Risks and open questions` — the "Window-function backend support" item's stated
  fallback ("a capability probe … deferred until a real consumer hits it") was effectively taken by
  the `"auto"` strategy; needs a `**Post-ship:**` note

#### D9 — the products relation-connection premise cites an implicit `"both"` default that is now `"connection"`. `post-ship` (`567cc6d0`).

Sites to correct:
- spec `:107` (`## Current state`, "so their many-side relations *already* synthesize live connection
  siblings under the implicit `"both"` default")
- spec `:61` — the Slice-6 products sub-bullet "already exist live via the [`DONE-032-0.0.9`][kanban]
  implicit `"both"` default" (Slice-6 text; **cohort R1c** owns Decision 10 — flagged here only so
  Worker 1 corrects the two sites consistently)
- spec `:253` — Decision 4 `**`to_attr` isolation**` "The `"both"` shape means the list sibling and
  the connection can be selected together" — still true when opted in, but no longer the default, so
  the sentence should say so

#### D10 — the Strawberry-floor Risks item is resolved at `HEAD`, and the source-verified internals still hold at the installed version.

`pyproject.toml:40` now reads `"strawberry-graphql>=0.316.0"` — exactly the version the spec
source-verified against, so the rationale's "Strawberry floor vs. locked-source assumptions" risk
("`pyproject.toml` allows `strawberry-graphql>=0.262.0` … either raise the Strawberry floor in the
joint `0.0.9` cut") was answered by raising the floor. `pyproject.toml:34` reads `"Django>=5.2.16"`,
matching [`BUILD.md`][build-md] `## Floor verification`.

**Shared `.venv`, read not remembered** (`uv pip list`): `django 6.1`, `strawberry-graphql 0.324.0`,
`channels 4.3.2`. The `.venv` is not the floor. Both Strawberry internals this cohort's contracts
depend on still hold at the installed 0.324.0:
- `SliceMetadata.from_arguments` (`.venv/.../strawberry/relay/utils.py:114`) keeps its
  `before` / `after` / `first` / `last` / `max_results` keyword signature, its
  `ValueError("Argument 'first' cannot be higher than {max_results}.")` (`:156`) and its
  `TypeError("Argument 'after' contains a non-existing value.")` (`:142`) — the exact two exception
  classes `derive_connection_window_bounds` catches. It has gained one optional `prefix` parameter,
  which the package does not pass.
- `strawberry/types/nodes.py:41` still carries `return info.variable_values.get(name)` — the spec's
  `#"info.variable_values.get(name)"` citation resolves.
- `ConnectionExtension` still exists, at `strawberry/relay/fields.py:219`.

No spec correction needed for the internals; the rationale's Risks item earns a **resolved** note.

### High:

None. No spec contract in Slice 1's scope is undelivered as a *capability*, no correctness bug was
found, and no fail-open shape sits on a decision path (see the fail-open hunt below). Every
divergence above is a spec-text divergence of one of the two classes the build plan defines.

### Medium:

#### Ten dead back-compat aliases in `optimizer/walker.py`, whose comment states a reason that is measurably false

`optimizer/walker.py:48-53` justifies the alias block as keeping "the tests that import these names
from `optimizer.walker` working unchanged", and `:62-63` likewise ("Compatibility aliases for private
imports that predate the connection planner extraction"). Measured against every `from … walker
import` / `walker.<name>` reference in `tests/`, `examples/` and `django_strawberry_framework/`, and
against each name's occurrence count inside `walker.py` itself:

- **Live** (4): `_should_include`, `_is_fragment`, `_concrete_order_columns`,
  `_relay_max_results_from_info` — all imported by `tests/optimizer/test_walker.py`.
- **Live via walker's own bodies** (3): `_response_key` (5 occurrences), `_response_keys` (4),
  `_included_field_selections` (3).
- **Dead — assignment-only in `walker.py`, zero importers anywhere** (10):
  `_named_children`, `_node_children_with_runtime_prefix`, `_with_runtime_prefix` (from the
  `.selections` block, `:59-61`); `_connection_window_slice_from_arguments`,
  `_extend_only_projection`, `_keyset_window_slice_from_arguments`, `_order_entry_field_name`,
  `_project_scalar_only_window`, `_relation_connection_to_attr`,
  `_relation_connection_to_attr_for_key` (from the `_nested_planner` block, `:64-72`).

The names that *look* like counter-examples are imported from their real owners, not from `walker`:
`tests/optimizer/test_extension.py:59-60` takes `_named_children` /
`_node_children_with_runtime_prefix` from `optimizer.extension`;
`tests/test_keyset_connection.py:43-46` takes `_extend_only_projection` /
`_keyset_window_slice_from_arguments` from `optimizer.nested_planner`.

Why it matters: a comment asserting a live reader for a name with none is worse than no comment — it
tells the next reader the line is load-bearing. Recommended change: delete the ten dead aliases and
narrow the two comments to the four names that have readers. Test expectation: none new;
`uv run pytest tests/optimizer/ tests/utils/test_connections.py tests/test_keyset_connection.py --no-cov`
must stay green, which is the whole proof the aliases are dead. Not `revision-needed`: this is dead
code, not a spec contract undelivered, a correctness bug, or a fail-open shape — and
[`worker-3.md`][worker-3] "The existence challenge" forbids holding a unit on an unresolved existence
challenge alone. Escalated below.

#### Ten source and test sites cite the cursor-parity invariant as "spec-033 Decision 11"; the spec sites it on Decision 4

Measured with `grep -rn 'spec-033 Decision 11' --include="*.py" .`: **10** occurrences —
`django_strawberry_framework/connection.py:127`, `:1575`;
`django_strawberry_framework/optimizer/plans.py:814`, `:869`, `:895`, `:999`;
`tests/optimizer/test_plans.py:970`, `:1218`; `tests/optimizer/test_walker.py:2426`, `:3386`.

The spec states the invariant in Decision 4 (`:248`) and gives Decision 11 only the hoist's module
location — and the rationale's `## Decision 11` `### Changes this Decision underwent` records
Revision 2 finding 7 as precisely the promotion *out of* Decision 11. So the code is citing the
Decision the invariant was deliberately moved off. This cohort writes no source, so it is routed, not
fixed. Note that only **two** of the ten are the sites Slice 0 flagged; the other eight (six of them
in production comments) were invisible to a `test_walker.py`-scoped look.

#### `optimizer/plans.py::window_partition_for_prefetch` has zero production callers and is pinned by six tests

`grep -rn 'window_partition_for_prefetch' --include="*.py" .` outside `plans.py`:
`tests/optimizer/test_join_taxonomy.py:122` (docstring), `tests/optimizer/test_walker.py:2553`
(docstring), `:3239-3244` (three assertions inside
`::test_m2m_shared_child_partitions_per_parent`), and two docstrings in
`django_strawberry_framework/exceptions.py:397` / `optimizer/join_taxonomy.py:297`. Production derives
the partition from the descriptor instead:
`optimizer/nested_fetch.py::attach_windowed_prefetch #"partition_by=request.join.partition_expr"`
(`:306`), built by `optimizer/nested_planner.py::plan_connection_relation #"join = classify_relation_join("`
(`:1194`).

Consequences worth naming: (a) `tests/optimizer/test_plans.py::TestWindowPartitionForPrefetch`
(`:1059`) — six rows, the most thorough per-relation-kind pins in the tree — exercises a surface no
request reaches, so an inconsistency between the shim and `classify_relation_join` would be invisible
to them; (b) `::test_forward_single_relation_raises` and
`::test_windowable_kind_without_remote_field_keys_raises` pin an `OptimizerError` that no production
path can now emit, and `django_strawberry_framework/exceptions.py:397` documents that raise as a live
error mode. This is the DRY existence challenge in its clearest form — see DRY-1.

### Low:

#### The spec's `test_relation_connections_slot_recorded` sentence over-claims what its named test covers

Spec `:389` says the test proves "suppressed shapes (`"list"`, non-Node target, consumer-authored)
record nothing". At `HEAD`, `tests/optimizer/test_walker.py::test_relation_connections_slot_recorded`
(`:2580`) asserts only the positive mapping for two types; the suppression half split into
`::test_relation_connections_slot_records_nothing_for_suppressed_shapes` (`:2594`), which covers the
`"list"` narrowing alone. The other two arms are structurally unreachable-to-record (finding 2 above)
and their *synthesis* suppression is spec-032-pinned, so no coverage is actually missing — the spec
sentence is what needs narrowing.

#### `test_scalar_only_pageinfo_and_total_count_are_window_planned` asserts only the `totalCount` arm

The body (`tests/optimizer/test_walker.py:3302`) builds `scalar_children=["totalCount"]`; a
`pageInfo`-only selection (which now takes the `FetchMode.PROBED` branch rather than `COUNTED`) is
not exercised by this test. A `grep -n 'scalar_children=\["pageInfo"' tests/optimizer/test_walker.py`
returns nothing. The `pageInfo`-observability path itself is covered by
`::test_nested_connection_total_count_planned_only_when_observable` (`:2871`) and the probe pins at
`:3826` / `:4244`, so this is a naming-versus-body mismatch, not a coverage gap.

#### `_optimizer_runtime_prefixes` is a bare literal in two modules

The shadow overviews list it as a repeated literal in `optimizer/walker.py` (2x) and it is also read
in `optimizer/selections.py::with_runtime_prefix` — the only attribute name shared across the
walker/selections seam that has no named constant. Cheap to name; not load-bearing.

#### A live `TODO(spec-033` anchor names this build's spec

`tests/test_connection.py:1588` #`# TODO(spec-033 Slice 1-2): root-connection no-regression fence.`
The anchor names no unshipped work — its own body says "No new tests required here; this marker
records the fence (DoD item 12)". It is the only `TODO(spec-033` anchor anywhere under `tests/`,
`examples/`, or `django_strawberry_framework/` (re-measured: `grep -rn 'TODO(spec-033' --include="*.py" .`
→ 1 occurrence). [`BUILD.md`][build-md] `## Cross-slice integration pass` step 6 requires it
discharged or explicitly re-classified: the work landed, so the `TODO(` prefix should be dropped and
the provenance sentence kept. Not this cohort's to edit; routed to the integration pass with a named
owner.

### DRY findings

#### DRY-1 (existence challenge) — `optimizer/plans.py::window_partition_for_prefetch` exists only for its own tests

One real caller: none. Its whole body is `classify_relation_join(field)` plus two `OptimizerError`
raises. Deleting it and inlining nothing would break: six rows in
`tests/optimizer/test_plans.py::TestWindowPartitionForPrefetch` (`:1059`), three assertions in
`tests/optimizer/test_walker.py::test_m2m_shared_child_partitions_per_parent` (`:3239`), and two
docstring references. Nothing in production. The readable reusable shape is to move those pins onto
`optimizer/join_taxonomy.py::classify_relation_join`'s `partition_expr` / `windowable` fields — where
`tests/optimizer/test_join_taxonomy.py` already lives — and drop the shim, or, if the raise contract
is wanted as a public API, give it a production caller so the two cannot drift. **Contract-level**
in [`BUILD.md`][build-md]'s sense (whether an abstraction should exist), so escalated to the
maintainer rather than decided here.

#### DRY-2 — the `to_attr` grammar is shared through two `_`-private `nested_planner` imports, not through the module Decision 11 created for exactly this

`django_strawberry_framework/connection.py:75-79` imports `_extend_only_projection`,
`_relation_connection_to_attr` and `_relation_connection_to_attr_for_key` from
`optimizer.nested_planner`, and uses the latter two at `connection.py:2001` and `:2011`. Decision 11
`:329` created `utils/connections.py` as "a neutral, cycle-safe home" precisely so the plan side and
the resolve side share one source; the `to_attr` grammar — as much a cursor-parity contract as the
bounds are — instead travels as two private compatibility delegates
(`nested_planner.py:738`, `:743`) that wrap the public
`::relation_connection_to_attr` (`:723`). Recommended shape: move
`relation_connection_to_attr` to `utils/connections.py` beside `CONNECTION_SIDECAR_KWARGS`, have both
sides import the public name, and delete the two delegates (whose only non-`connection.py` readers
are two of the ten dead walker aliases). No behavior change; no test expectation beyond the existing
`tests/utils/test_connections.py` twin.

#### DRY-3 — cross-file repeated literals: none of concern

Compared the `## Repeated string literals` section across all 12 emitted overviews (plus
`connection.py`'s and `types/resolvers.py`'s, which were already present in `docs/shadow/`). The
`_dst_*` window annotation names — the one family that would matter for cross-module drift — are
constants in exactly one place, `optimizer/plans.py:744-756` (`WINDOW_ROW_NUMBER`,
`WINDOW_TOTAL_COUNT`, `WINDOW_ROW_NUMBER_REVERSED`, `WINDOW_ROW_NUMBER_ABS`,
`WINDOW_KEYSET_SEEK_COUNT`), and every consumer imports the symbol
(`connection.py:81-83`, `optimizer/lateral_fetch.py:93-95`, `optimizer/single_parent_fetch.py:63`).
`grep -rn '"_dst_row_number\|"_dst_total_count' --include="*.py" django_strawberry_framework/` finds
the raw strings only in `plans.py`'s definitions and in `lateral_fetch.py`'s module docstring SQL
sketch. Verified rather than assumed; no finding. The sidecar-kwarg family is likewise single-sourced
at `utils/connections.py:57-60`.

### Static helper use

Run for every file in this cohort's source scope — mandatory here per [`BUILD.md`][build-md]
`### When to run the helper during build` (every file under `optimizer/` or `types/`). **No skips.**

```shell
uv run python scripts/review_inspect.py django_strawberry_framework/<path> --output-dir docs/shadow
```

Twelve invocations, all exit 0: `optimizer/walker.py`, `optimizer/plans.py`,
`optimizer/nested_planner.py`, `optimizer/nested_fetch.py`, `optimizer/lateral_fetch.py`,
`optimizer/single_parent_fetch.py`, `optimizer/join_taxonomy.py`, `optimizer/selections.py`,
`optimizer/extension.py`, `types/definition.py`, `types/finalizer.py`, `utils/connections.py`.
Shadow line numbers are not cited anywhere in this artifact; every reference above is
symbol-qualified with the ORIGINAL source line beside it.

- **Django / ORM markers — walked in full.** Every entry across the twelve overviews is ordinary ORM
  vocabulary for an optimizer package: `_meta` reads for pk/attname/ordering/index resolution,
  `QuerySet` type annotations, `Prefetch` construction, `select_related` / `prefetch_related` /
  `only` plan fields, `field_map` / `get_queryset` / `OptimizerHint` / `OptimizationPlan` /
  `DjangoType` seam names. Two clusters earned a closer read rather than a one-liner and are
  reported above as findings-or-justifications: `join_taxonomy.py`'s three `_meta` reads (`:223`,
  `:253`, `:285`) all sit inside `try: … except BaseException: return None` under the module's
  documented never-raises contract, and `nested_planner.py`'s `only` writers (`:689`, `:720`) are the
  scalar-only and keyset projection extensions verified under finding 14. No marker produced a
  finding.
- **Repeated string literals** — see DRY-3.
- **Control-flow hotspots — Medium-tier attention applied to every entry.** The four largest on this
  cohort's path: `optimizer/nested_planner.py::plan_connection_relation` (383 lines, 24 branches),
  `optimizer/plans.py::apply_window_pagination` (202 / 14), `optimizer/walker.py::_walk_selections`
  (212 / 20), `optimizer/lateral_fetch.py::build_lateral_sql` (201 / 18). Each was read end to end for
  this pass. `plan_connection_relation`'s size is the concrete cost of D5/D8: nine fallback exits,
  two window schemes, and an offset/keyset fork in one function. That is a structural observation for
  the maintainer, not a finding — splitting it is a contract-level call about the strategy seam that
  no spec currently owns (D8).
- **Imports — one-way and cycle-free on this cohort's path**, verified from the overviews' Imports
  sections: `walker.py → nested_planner.py → {nested_fetch, plans, selections, join_taxonomy,
  utils/connections, keyset}`; `extension.py → {walker, selections, plans, nested_fetch}`;
  `plans.py → join_taxonomy.py`; `selections.py → utils/typing` only. No module imports
  `connection.py` from `optimizer/`, so Decision 11's "the walker must not import from
  `connection.py`" still holds. The one cross-folder import worth flagging is
  `connection.py:75` reaching into `optimizer.nested_planner`'s private names — DRY-2.

### Failability position

`None; this pass introduces no boundary.` This cohort ships no executable byte, so there is no new
boundary, guard, gate, or rejection path to prove and no Worker 2 record to audit. Worker 3's
independent-re-run floor ([`worker-3.md`][worker-3] "Reading is necessary, not sufficient") computes
to an **empty re-run set**, which is legal here for the stated reason: the diff introduces no boundary
that meets the floor because there is no diff.

Worker 3's transient-source-mutation carve-out was **not** exercised and is not licensed this pass
(the dispatch says so, and no boundary is being introduced). No mutation was made; the tree carries
none from this cohort — `git status --short` after the pass shows only the four files the artifact
list accounts for plus the concurrent `0_0_14.md`.

### Fail-open shape hunt

Hunted the shapes [`BUILD.md`][build-md] `### Fail-open shapes` lists, wherever this cohort's source
computes an input to a limit, a size, or a rejection. **Result: no fail-open shape on a decision
path.** What was examined and why each answer is the refusing one:

- `optimizer/join_taxonomy.py::_safe_getattr` / `::_safe_truthy` / `::_safe_flag` (`:83`, `:91`,
  `:106`) are `except BaseException` around attribute reads and truth tests — textbook suspects. The
  computed *answer* is what matters, and it refuses: `classify_relation_join` (`:290`) closes with
  `windowable=windowable and partition is not None` (`:343`), and its `kind` read falls back to
  `"forward_single"` (`:303`), which is not in `WINDOWABLE_RELATION_KINDS`. Every incoherent input
  therefore lands on **unplanned**, i.e. the shipped per-parent pipeline — the conservative arm, and
  the one strictness can still see. Fail-closed.
- `utils/connections.py::window_range_plan` (`:360`) **raises** `OptimizerError` on a negative offset (`:406`)
  or a negative limit (`:408`) rather than clamping them, and says why: "silently treating a negative
  direct-call limit as unbounded would recreate the same wrong-row failure in both renderers". The
  clamp that would have been the fail-open shape is explicitly absent.
- `utils/connections.py::derive_connection_window_bounds` (`:566`) refuses the answer, not an input
  spelling: `slice_meta.start < 0` (`:631`) and `slice_meta.end < 0` (`:633`) raise `TypeError` (classified upstream as
  malformed pagination, so the field raises its own error), and `expected < 0` (`:639`) raises
  `UnwindowableConnection` (a valid query, fully unplanned) — the two incoherent outcomes are routed
  to *different* refusals, which is the distinction a guard written against input spellings would
  have lost.
- `optimizer/nested_planner.py::_coerce_pagination_int` (`:785`) passes a non-int-castable value
  through **untouched** rather than defaulting it, so `SliceMetadata.from_arguments` reaches its own
  `isinstance` gate. No silent default.
- `optimizer/extension.py::DjangoOptimizerExtension._stash_union` (`:1318`) falls back to `new` alone
  when the existing stash is not a set. Examined as a truthiness-on-absent suspect: the sentinel is a
  *planned* set, so the narrower value is the one that lets strictness flag more, not less — and the
  absent case is the first publish, where `new` is correct.
- `optimizer/walker.py:463` #`getattr(definition, "relation_connections", None) or {}` is an `or`
  fallback on a can-be-falsy value. Both falsy values (`None` and `{}`) mean the same thing here —
  "this type synthesized no connection siblings" — so the empty dict is not a coerced default but the
  accurate answer, and the consequence is the pre-`033` `continue`, i.e. unplanned.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` → **empty, exit 0**. `__all__` and the
re-export list are unchanged, as they must be: this cohort writes no source. Decision 11 `:329`
records that `utils/connections.py` is "package-internal (no public export)"; verified independently —
`grep -n 'connections' django_strawberry_framework/__init__.py` finds nothing, and none of
`selections`, `nested_fetch`, `nested_planner`, `lateral_fetch`, `single_parent_fetch`,
`join_taxonomy` is re-exported either. So the six post-ship modules (D2) added **no** public surface,
and DoD item 12's "no new public exports" posture holds through all of them.

### CHANGELOG sanity

Not applicable; this cohort did not modify `CHANGELOG.md` and is fenced from doing so.

### Documentation / release sanity

Not applicable; this cohort modified no docs, release metadata, KANBAN, or archived specs. Two
doc-surface divergences were *found* and are recorded as deferred rather than fixed, per the cycle's
scope fence: spec `:475`'s `docs/TREE.md` bullet names four optimizer modules where thirteen now
exist (D2), and `docs/TREE.md` itself therefore cannot carry entries for the six post-ship modules in
the shape Decision 11 describes. `docs/TREE.md` is script-rendered
(`scripts/build_tree_md.py`), so the fix is a docstring-plus-regenerate change owned by a later pass.

### Hot-path budget

`Not applicable; plan declares no hot path for this cohort.` The build plan's declaration is
`none` for R1a because it touches no runtime code, and it holds — nothing was written.

**Standing note for a repair cohort, per the plan's own carry-forward.** Every defect surfaced above
that a repair would touch sits on a declared-hot path: `optimizer/walker.py`'s plan walk and every
`nested_fetch.py` / `nested_planner.py` / `lateral_fetch.py` / `single_parent_fetch.py` fetch path run
per request, per resolver, per parent row. Concretely, the two code-side items here — deleting ten
dead module-level aliases in `walker.py`, and relocating `relation_connection_to_attr` to
`utils/connections.py` — are both **import-time-only**: neither adds or removes work inside a
per-request or per-row path. A repair cohort still owes the before/after number, because the
declaration is per-slice and not waivable by a worker's estimate; this paragraph records where the
number would come from (a plan-build iteration count over
`tests/optimizer/test_walker.py::test_nested_connection_planned_as_windowed_prefetch`'s shape), not a
claim that it is unnecessary.

### Floor verification

`Not applicable; plan declares floor-verification scope none.` No isolated floor venv was built and
no floor run was performed — correct for a pass that executes no integration seam. The floor
*numbers* were nevertheless needed, because two of this cohort's contracts depend on Strawberry
internals; they were read rather than remembered and are reported under D10 (`pyproject.toml:34`,
`:40`; `uv pip list` for the shared `.venv`; the three internals re-checked at the installed
0.324.0).

### Validation run

- `uv run pytest tests/optimizer/test_walker.py tests/optimizer/test_plans.py tests/optimizer/test_nested_fetch.py tests/optimizer/test_selections.py tests/optimizer/test_lateral_fetch.py tests/optimizer/test_single_parent_fetch.py tests/optimizer/test_join_taxonomy.py tests/utils/test_connections.py --no-cov -q`
  → **547 passed in 4.63s**, 8 workers. No `--cov*` flag was used anywhere in this pass;
  `--no-cov` is required because `pytest.ini`'s `addopts` auto-applies `--cov`.
- No `ruff` invocation: this pass touched no `.py` file, so neither
  `uv run ruff format` nor `ruff check --fix` applies.
- `git status --short` after the pass: `M docs/SPECS/spec-033-connection_optimizer-0_0_9.md`,
  `?? 0_0_14.md`, `?? docs/SPECS/appx/spec-033-connection_optimizer-0_0_9-rationale.md`,
  `?? docs/builder/bld-033-slice-0-rationale_extraction.md`,
  `?? docs/builder/build-033-connection_optimizer-0_0_9.md`, plus this artifact. Every entry is
  Slice 0's output, Worker 0's plan, this cohort's own artifact, or the baseline-dirty concurrent
  `0_0_14.md`. **Nothing outside the ownership partition was written**, and `0_0_14.md` /
  `docs/builder/bld-003-final.md` were neither read as this cycle's nor touched.
  One observation for Worker 0: the three files the session-start snapshot showed as modified
  (`examples/fakeshop/apps/products/services.py`,
  `examples/fakeshop/test_query/test_debug_extension_api.py`,
  `examples/fakeshop/test_query/test_products_api.py`) are **clean now** — a concurrent session
  committed or reverted them mid-cycle. Not reverted, not touched; recorded so a later pass does not
  read their absence as this cycle's doing.

### Ownership partition

The two files this cohort owns, per the build plan: this artifact and
`docs/builder/worker-memory/worker-3.md` (one appended block, under its own heading, in one write —
R1b and R1c append concurrently). `docs/shadow/` is generator-written and gitignored. No temp test
was needed (see below).

### What looks solid

- **The cursor-parity invariant is better served at `HEAD` than the spec describes.** The spec hoists
  the pk-append rule; `HEAD` hoists the whole precedence ladder into
  `optimizer/plans.py::effective_connection_order` (`:862`), so an explicit `orderBy:`, a declared
  `cursor_field`, and `Meta.ordering` resolve identically on both sides. The identity pin
  (`tests/optimizer/test_plans.py::TestDeterministicOrderHoistParity::test_deterministic_order_matches_connection_reexport`)
  asserts object identity, not equal behavior — the strongest available shape for a hoist.
- **The no-leakage discipline exceeds the spec.** Building the child plan against a throwaway
  `sub_plan` and absorbing it only on the success path (finding 16) makes Decision 6's "no
  `planned_resolver_keys` entry" true for *every* refusal arm, including the strategy refusal and the
  join-kind refusal that the spec never anticipated.
- **Malformed-slice error locality survived four rounds of change intact**, including the per-key
  refinement (`_identities_for_response_keys`) that keeps one alias's validation error local while
  its siblings still plan. This is the contract most at risk from the divergent-alias inversion, and
  it held.
- **Recognition never grew a second name-normalization path**, which is what Decision 3's
  justification most cared about: `_resolve_selection_target` (`:245`) is one function serving both
  the model-field and synthesized-connection namespaces, with the exact reversal as the fast path and
  one shared forward-camelization scan on a miss.
- **Every window refusal is fail-closed toward the shipped per-parent pipeline.** Across nine
  fallback arms and three `except BaseException` classifier guards, no incoherent input produces a
  window; the worst outcome is a strictness-visible per-parent access, which is the pre-`033`
  behavior.

### Temp test verification

None written. No suspicion in this pass turned on whether an existing assertion is
non-distinguishing: the two candidates —
`test_nested_connection_planned_as_windowed_prefetch` (D3) and
`test_divergent_aliases_plan_one_window_per_response_key` (D4) — both **state their inverted contract
in their own docstrings** and assert it positively, so reading them settled the question and a temp
test would have proved nothing the source did not. `docs/builder/temp-tests/r1a/` was not created.

### Notes for Worker 1 (spec reconciliation)

Divergences D1-D10 above are the actionable inventory; each carries its class, its shipped shape, its
attribution, and its complete per-site list. Worker 1's Slice 2 should be able to act from this
section plus those blocks without re-deriving anything. Three cross-cutting notes, then the two
escalations.

**N1 — the two Decision-9/11 corrections are one edit, not two.** D1 and D2 share a root: the card's
bounded-extension pin ("No new subpackage; touches `walker.py` / `plans.py` / `extension.py`") is what
both Decisions restate, and both were overtaken by the same post-`0.0.9` refactoring run. Correcting
one without the other leaves the spec self-contradictory: Decision 9 would name `selections.py` as
the helper home while Decision 11's map still says "no new module". Slice 0 predicted they were
"stale together"; verified — they are.

**N2 — the phrase "post-build DRY refactor" (spec `:52`, `:328`, `:329`) is now load-bearing and
wrong-sized.** Slice 0 deliberately left it because "the whole no-new-source-module claim it
qualifies is under review by Slice 2". That review is done: eight modules landed across seven
commits between 2026-06-13 and 2026-07-17, only one of which (`utils/connections.py`) is the
post-build DRY refactor the phrase names. The phrase should become a specific statement of the shipped
layout, with the rationale carrying the per-commit chronology.

**N3 — a fifth spelling of the Decision 6 count.** D4/D5 list nine spec sites for "four fallback
shapes". Worker 1 should treat the **number four** as the token to sweep, not the phrase: it appears
as "Four nested-connection shapes" (`:281`), "a fourth … fallback shape" (`:250`, `:290`),
"fallback non-planning ×4" (`:346`), and "the four Decision 6 fallback shapes" (`:509`) — four
different grammars for one count, which is exactly the population-versus-vocabulary trap
[`BUILD.md`][build-md] `## Claims are proven mechanically` names.

**N4 — cohort-boundary sites Worker 1 must reconcile once, not twice.** Three sites in my scope are
also in a sibling cohort's: spec `:364` / `:365` (`## Edge cases`, marker rows — Decision 5 body is
R1b's), spec `:61` and `:107` (the `"both"` default — Decision 10 is R1c's), and spec `:252`'s
strictness clause (Decision 8 is R1b's). Each is recorded above with the sibling named so the
corrections agree.

**Escalated: `optimizer/plans.py::window_partition_for_prefetch` — should this abstraction exist?**
Evidence in DRY-1 and the Medium finding above: zero production callers, six test rows plus three
more in `test_walker.py` pinning it, and a documented `OptimizerError` mode
(`django_strawberry_framework/exceptions.py:397`) that no request can reach. Resolution paths for the
maintainer to pick between: **(a)** delete the shim, move its per-relation-kind pins onto
`optimizer/join_taxonomy.py::classify_relation_join` in `tests/optimizer/test_join_taxonomy.py`, and
drop the `exceptions.py` docstring line — smallest surface, loses a public name no consumer is
documented to use; **(b)** keep it and give it the production caller it implies, so
`plan_connection_relation` derives the partition through the raising shim and the two cannot drift —
keeps the pins meaningful but reintroduces an exception on a hot path that currently returns a bool;
**(c)** keep it explicitly as a supported introspection/diagnostic helper and say so in Decision 4,
which makes the test-only status intentional rather than residual. This is contract-level
([`BUILD.md`][build-md] `### Contract-level findings are escalated as maintainer decisions before
dispatch`) — not a worker's call, and not grounds to hold this cohort.

**Escalated: the ten dead `optimizer/walker.py` back-compat aliases and DRY-2's private
`to_attr` imports.** These are the only two **code** items in this cohort, and neither meets
`revision-needed`'s bar (no undelivered spec contract, no correctness bug, no fail-open shape). They
do want a repair cohort if the maintainer opens one, and they pair naturally: deleting the ten
aliases removes the only non-`connection.py` readers of
`nested_planner._relation_connection_to_attr` / `_relation_connection_to_attr_for_key`, after which
moving the public `relation_connection_to_attr` into `utils/connections.py` and repointing
`connection.py:75-79` is a mechanical two-file change with no behavior delta. Such a cohort would own
`optimizer/walker.py`, `optimizer/nested_planner.py`, `utils/connections.py`, `connection.py` and
`tests/utils/test_connections.py`, and would inherit the standing hot-path declaration — see the
`### Hot-path budget` note above for where the number comes from.

**Routed, not escalated (no spec change; needs a `.py` owner in a later pass):**
- the ten `spec-033 Decision 11` cursor-parity citations in source and tests (Medium finding above,
  with the full ten-site list). The spec's siting on Decision 4 is the one Revision 2 chose
  deliberately, so the **code** is what should move.
- `tests/test_connection.py:1588`'s `TODO(spec-033 Slice 1-2)` anchor —
  [`BUILD.md`][build-md] `## Cross-slice integration pass` step 6. Recommended disposition:
  re-classify (drop `TODO(`, keep the `spec-033 Slice 1-2` provenance sentence), since the fence it
  records is discharged. Owner: the integration pass, or a repair cohort if one opens.

**Deferred-work catalog candidates** (for `bld-033-final.md`'s `### Deferred work catalog`):
`docs/TREE.md`'s optimizer module entries (six post-ship modules unlisted; script-rendered, so a
docstring-plus-regenerate change); the rationale's Strawberry-floor Risks item, now **resolved** by
`pyproject.toml:40`'s `>=0.316.0` and worth marking so rather than left open; and the absence of any
spec owning the `nested_fetch.py` strategy seam (D8) — a gap this cycle can record but not fill.

### Review outcome

`review-accepted`.

Verification is complete across Decisions 3 / 4 / 6 / 9 / 11: sixteen contracts proven present with
symbol-qualified evidence, ten divergences proven and fully site-listed, and every named Slice-1 test
accounted for — three of the five apparently-missing names (`test_apply_window_pagination_unit`,
`test_deterministic_order_helper_hoist_parity`,
`test_window_partition_for_reverse_fk_forward_m2m_reverse_m2m`) are **renames into test classes with
strictly broader coverage**, not lost coverage: `TestApplyWindowPagination` (`test_plans.py:807`),
`TestDeterministicOrderHoistParity` (`:1140`), `TestWindowPartitionForPrefetch` (`:1059`). The other
two (`test_fallback_not_planned_divergent_aliases`, `test_fallback_not_planned_distinct_target`) are
absent for the reasons D4 and D5 give — one by design, one by rename.

Every divergence is a **spec-text** divergence, which Worker 1's Slice 2 lands. `revision-needed` is
not warranted: no spec contract in this scope is undelivered as a capability, no correctness bug was
found, and the fail-open hunt found every incoherent-input path refusing toward the shipped
per-parent pipeline. The two code items (ten dead aliases; the private `to_attr` import path) are
escalated above with resolution paths rather than used to reject a pass whose subject is a shipped
card's spec text.

<!-- LINK DEFINITIONS -->

<!-- Root -->

[agents]: ../../AGENTS.md

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

[artifact-md]: ARTIFACT.md
[build-033]: build-033-connection_optimizer-0_0_9.md
[build-md]: BUILD.md
[worker-3]: worker-3.md

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
