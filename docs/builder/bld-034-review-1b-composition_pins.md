# Build: R1b — conformance audit, optimizer cooperation and composition pins

Spec reference: `docs/SPECS/spec-034-permissions-0_0_10.md` (Slices 2 and 3; Decisions 11 and 12; Goals 3 and 4; the plan-cache / FK-id-elision / strictness / sharded-caller / non-nullable-FK edge-case bullets; Test plan `### Slice 2` and `### Slice 3`; Definition of done items 6, 7, 8, 9)
Rationale companion: `docs/SPECS/appx/spec-034-permissions-0_0_10-rationale.md` (Decisions 7, 11, 12)
Build plan: `docs/builder/build-034-permissions-0_0_10.md` (`## Grading rule every R1 cohort applies`; `## Ownership partition` row R1b)
Status: final-accepted

**Cohort R1b of review round 1, `034` residual-reconciliation cycle.** This is a conformance audit at `HEAD`, not a review of a fresh diff. The cohort is read-only over source and tests and writes exactly one file, this artifact.

---

## Plan (Worker 1)

**Not applicable.** This cohort lands no source and no test. Its contract is the R1b row of the build plan's `## Ownership partition` plus the maintainer dispatch; there was no Worker 1 planning pass and no `### Spec slice checklist (verbatim)` to copy, because the unit under audit is a shipped spec territory rather than an unbuilt slice. The build plan's `## Grading rule every R1 cohort applies` is the checklist this pass walks, and it is applied per contract row in `### Contract census` below.

---

## Build report (Worker 2)

**Not applicable.** No builder pass ran for this cohort: R1 is read-only by the plan's declared partition ("Every R1 cohort is **read-only over source and tests** — it writes exactly one file, its own artifact"). There is therefore no Worker 2 diff, no `### Files touched`, and no builder-recorded failability proof to audit. The one failability proof in this pass is Worker 3's own, performed under the `worker-3.md` `## Scope` carve-out and recorded in `### Failability proof (Worker 3, own)`.

---

## Review (Worker 3)

### Method and evidence base

- Source read at `HEAD`: `django_strawberry_framework/optimizer/walker.py`, `optimizer/extension.py`, `connection.py`, `relay.py`, `list_field.py`, `filters/sets.py`, `orders/sets.py`, plus the seams those files delegate to (`utils/querysets.py`, `utils/permissions.py`, `types/relay.py`, `types/base.py`, `permissions.py` — the last three read only as far as a territory claim reaches into them).
- Tests read at `HEAD`: `tests/optimizer/test_extension.py`, `tests/optimizer/test_multi_db.py`, `tests/test_connection.py`, `tests/test_relay_node_field.py`, `tests/test_list_field.py`, and the Slice-2 / Slice-3 regions of `tests/test_permissions.py` (`# N+1 audit` banner at `tests/test_permissions.py:2342` through end of file).
- Mechanical runs (all `--no-cov`, no `--cov*` flag anywhere in this pass):
  - `uv run pytest tests/test_permissions.py tests/optimizer/test_extension.py tests/test_connection.py tests/test_relay_node_field.py tests/test_list_field.py tests/optimizer/test_multi_db.py --no-cov -q -k "cascad or gate_denial or strictness_raise_silent or fk_id_elision_falls_back"` → **25 passed**.
  - `uv run pytest tests/optimizer/ tests/test_permissions.py tests/test_connection.py tests/test_relay_node_field.py tests/test_list_field.py --no-cov -q` → **1071 passed, 1 skipped** (Definition-of-done item 7's "optimizer suites untouched and green").
  - One failability proof with a transient walker mutation, reverted and byte-compared — `### Failability proof (Worker 3, own)`.
- Static helper: `uv run python scripts/review_inspect.py django_strawberry_framework/optimizer/walker.py --output-dir docs/shadow` and the same for `connection.py` — `### Static inspection helper`.

The tree is legitimately dirty with a concurrent session's kanban-tooling work (the plan's baseline-dirty list). Nothing in that list was read as evidence, edited, or reverted.

### Contract census

Grades per the build plan's `## Grading rule every R1 cohort applies`. Evidence is symbol-qualified per `AGENTS.md` rule 27; raw `path:NN` appears only here, in this per-cycle artifact, alongside the symbol identifier.

#### Slice 2 checklist (`## Slice checklist`, Slice 2)

| # | Contract (spec) | Evidence at `HEAD` | Grade |
|---|---|---|---|
| S2-1 | "No optimizer source change." | `grep -l apply_cascade_permissions` over all seven territory source files returns **zero** files; `grep -n spec-034` over the same seven returns **zero** occurrences. No cascade-specific code exists in `optimizer/walker.py`, `optimizer/extension.py`, `connection.py`, `relay.py`, `list_field.py`, `filters/sets.py`, `orders/sets.py`. | CONFORMS |
| S2-2 | "a relation whose target type's hook cascades still downgrades `select_related` -> `Prefetch` (the type reports `has_custom_get_queryset() is True`, so `optimizer/walker.py::_target_has_custom_get_queryset` fires the shipped rule)" | `optimizer/walker.py::_target_has_custom_get_queryset` exists under that exact name (walker.py:200) and is `target_type is not None and target_type.has_custom_get_queryset()`; the downgrade is `optimizer/walker.py::plan_relation #"return (\"prefetch\", \"custom_get_queryset\")"` (walker.py:188-193). Pinned by `tests/optimizer/test_extension.py::test_cascading_target_downgrades_join_to_prefetch`. | CONFORMS |
| S2-3 | "plans embedding a cascading hook are `cacheable = False` (the shipped rule marks **any** plan baking a custom `get_queryset` uncacheable — `optimizer/walker.py::_target_has_custom_get_queryset` — regardless of whether the hook reads the request)" | The *behavior* holds: `optimizer/walker.py::_plan_prefetch_relation #"plan.cacheable = False"` (walker.py:793-795) flips on the mere presence of a custom hook. But `_target_has_custom_get_queryset` is a two-line boolean predicate that never touches `plan.cacheable`; the spec cites the gate as though it were the rule. | **STALE-DESCRIPTION** (behavior CONFORMS; the symbol citation is wrong) |
| S2-4 | "the cascade itself adds **zero** query round-trips (the `__in` subqueries compile into the caller's single `SELECT`)" | `django_strawberry_framework/permissions.py::_cascade_edges #"condition = Q(**{f\"{field.name}__in\": subquery})"` composes an unevaluated subquery. Pinned with an **absolute** count by `tests/test_permissions.py::test_cascaded_traversal_adds_zero_queries` (`django_assert_num_queries(1)` on both shapes, plus an `"IN (SELECT"` right-path guard). | CONFORMS |
| S2-5 | "a Strictness mode `\"raise\"` run across a cascaded 2-deep traversal stays silent" | Behavior holds: `tests/test_permissions.py::test_strictness_raise_silent_across_cascaded_shape` passes at `HEAD` and the cascade composes SQL rather than lazy-loading (`permissions.py::_cascade_edges` never evaluates a target queryset). The pin is failable — proven in `### Failability proof (Worker 3, own)`, attempt 4 — but what it detects is an optimizer-planning regression, not a cascade-side one. | CONFORMS (see finding L3) |
| S2-6 | "Package coverage: `tests/test_permissions.py` query-count and SQL-shape pins + `tests/optimizer/test_extension.py` downgrade/cacheability pins per the Test plan" | Both files carry the pins under the banners `tests/test_permissions.py #"# N+1 audit (permissions-owned pins; optimizer-plan pins live in"` and `tests/optimizer/test_extension.py #"# Cascade <-> optimizer cooperation pins (spec-034)"`. | CONFORMS |

#### Slice 3 checklist (`## Slice checklist`, Slice 3)

| # | Contract (spec) | Evidence at `HEAD` | Grade |
|---|---|---|---|
| S3-1 | "No new code in `filters/` / `orders/` / `connection.py` / `relay.py` / `list_field.py`." | Same zero-occurrence sweep as S2-1. `orders/sets.py` contains no `cascad` occurrence at all. | CONFORMS |
| S3-2 | "composition order is **cascade narrows first, gates judge input second** — a `get_queryset` that cascades runs at the visibility step of every pipeline, then the active-input-only `check_<field>_permission` gates fire from `FilterSet.apply_*` / `OrderSet.apply_*` exactly as shipped" | `connection.py::_pipeline_sync` orders `apply_type_visibility_sync` (connection.py:1711) -> `filterset_class.apply_sync` -> `orderset_class.apply_sync` -> `_finalize_queryset`; `connection.py::_pipeline_async` mirrors it (connection.py:1748). Gates fire from `filters/sets.py #"cls._run_permission_checks(input_value, request)"` and `orders/sets.py #"cls._run_permission_checks(input_value, request)"` inside the apply path. Pinned by `tests/test_permissions.py::test_cascade_then_filter_gate_composition` / `::test_cascade_then_order_gate_composition`. | CONFORMS |
| S3-3 | "a field denial does not leak existence (denied-filter errors and hidden-row-empty results are produced by independent layers)" | `tests/test_permissions.py::test_gate_denial_no_existence_leak` compares `str(exc)` **and** `exc.extensions` across two fixtures differing in whether a cascade-hidden row exists, over an `Item` queryset the cascade genuinely narrows (asserted: `sorted(with_hidden.values_list("name", flat=True)) == ["pub"]`). | CONFORMS |
| S3-4 | "a `DjangoConnectionField` over a cascading type narrows `edges` and `totalCount` together" | `tests/test_connection.py::test_connection_over_cascading_type_narrows_edges_and_total_count` — 3 rows seeded, 2 visible, `totalCount == 2` asserted against a raw count of 3, plus cursor distinctness and `pageInfo`. | CONFORMS |
| S3-5 | "`DjangoNodeField` / `DjangoNodesField` refetch of a cascade-hidden row returns `null` with no existence leak" | `tests/test_relay_node_field.py::test_node_refetch_of_cascade_hidden_row_returns_null` (`data == {"item": None}`, `errors is None`) and `::test_nodes_batch_holes_for_cascade_hidden_rows` (positional `[None, {...}]`). Backing seam: `types/relay.py::_resolve_node_default #"qs = apply_type_visibility_sync(cls, initial_queryset(cls), info)"` and `::_resolve_nodes_default` (+ the two async siblings). | CONFORMS |
| S3-6 | "`DjangoListField`'s default resolver narrows" | `list_field.py #"apply_type_visibility_sync(target_type, qs, info),"` inside the `_default` resolver (list_field.py:209) and `apply_type_visibility_async(...)` on the async branch (list_field.py:203). Pinned by `tests/test_list_field.py::test_list_field_default_resolver_applies_cascade`. | CONFORMS |
| S3-7 | "Package coverage: `tests/test_permissions.py` (composition fixtures) + `tests/test_connection.py` / `tests/test_relay_node_field.py` / `tests/test_list_field.py` additions per the Test plan" | All four files carry `spec-034` cascade banners and the named tests. | CONFORMS |

#### Decision 11

| # | Contract (spec) | Evidence at `HEAD` | Grade |
|---|---|---|---|
| D11-1 | Gates "keep their names" — `check_<field>_permission` | `utils/permissions.py::_check_method_name #"return f\"check_{flatten_lookup_path(field_path)}_permission\""`. Consumer-side spelling preserved in `examples/fakeshop/apps/products/filters.py::CategoryFilter.check_name_permission`. | CONFORMS |
| D11-2 | Gates keep their signature `(self, request)` | `utils/permissions.py::invoke_permission_method #"method(request)"` — the gate is invoked with the resolved request and nothing else. | CONFORMS |
| D11-3 | Gates keep "active-input-only scope" (plus active-branch double-dispatch for `RelatedOrder`) | `utils/permissions.py::run_active_input_permission_checks` walks only supplied input fields via `iter_active_fields` / `is_inactive_value` with `unset_sentinel=strawberry.UNSET`; both families declare it through `_permission: ClassVar[ActiveInputPermissionAttrs]` (`filters/sets.py:1197`, `orders/sets.py:168`). | CONFORMS |
| D11-4 | "No rename, no deprecation, no unified dispatcher." | Verified rather than assumed: `utils/permissions.py` was added by `e37aef5e` (2026-06-13) and `sets_mixins.py` by `3f177dbb` (2026-05-28), both **before** `034` landed (`1a5a7216`, 2026-06-15). The shared traversal mechanics are therefore the state the Decision was written against, not a later unification; the sentence is about the gate families themselves, and no rename or deprecation exists at `HEAD`. | CONFORMS |
| D11-5 | Three-layer table rows 1-2: row visibility on `DjangoType.get_queryset` with `(cls, queryset, info)`; input gates on `FilterSet` / `OrderSet` with `check_<field>_permission(self, request)`, shipped `0.0.8` | `types/base.py::DjangoType.get_queryset` is `(cls, queryset, info, **kwargs)` (types/base.py:763-768). The spec's cell writes the signature as `(cls, queryset, info)` with no `**kwargs`; the shipped default accepts and ignores extra keywords. Row 3 (`FieldSet`) is R1c territory and is not graded here. | **STALE-DESCRIPTION** (row 1 signature is one term short of the shipped one) |
| D11-6 | "Composition order, pinned by Slice 3 tests: cascade narrows first, gates judge input second ... a denial therefore cannot leak hidden-row existence" | Pinned; see S3-2 / S3-3. See the Low finding below on which half of "cascade narrows first" the two gate-composition tests actually exercise. | CONFORMS |

#### Decision 12

| # | Contract (spec) | Evidence at `HEAD` | Grade |
|---|---|---|---|
| D12-1 | "`DjangoConnectionField`'s pipelines call `utils/querysets.py::apply_type_visibility_sync` / `apply_type_visibility_async` on the wrapped type **before** `filter:` / `orderBy:` / slicing" | `connection.py::_pipeline_sync` (connection.py:1681-1719) and `connection.py::_pipeline_async` (connection.py:1721-1756) both apply visibility as the first post-normalization step; the pipeline's return is what `_build_connection_resolver` hands to `ConnectionExtension`, so `DjangoConnection.resolve_connection` — which owns every slice and window path — only ever sees the post-visibility source. | CONFORMS |
| D12-2 | "`totalCount` (counted post-visibility)" | `connection.py::DjangoConnection.resolve_connection` computes `want_count` and dispatches into `_consume_window` on the already-narrowed `nodes`; no count is taken upstream of `_pipeline_*`. Pinned end-to-end by `tests/test_connection.py::test_connection_over_cascading_type_narrows_edges_and_total_count` (`totalCount == 2`, raw table count 3). | CONFORMS |
| D12-3 | "...and its cursor space in one place" | Same seam: cursors are derived downstream of the pipeline; the test asserts one distinct cursor per surviving edge and `hasNextPage is False` over the narrowed set. | CONFORMS |
| D12-4 | "**Edges' nested relations** respect the *targets'* hooks via the optimizer's `Prefetch` downgrade ... and when those targets' hooks also cascade, the cascade applies transitively" | `tests/test_permissions.py::test_nested_relation_traversal_respects_target_cascade` asserts the narrowed nested rows through a real `schema.execute_sync`. | CONFORMS |
| D12-5 | "**Verified dependency to protect**: `optimizer/walker.py::_build_child_queryset` (walker.py:212-214) builds `field.related_model._default_manager.all()` and, when the target reports a custom hook, runs it through `apply_type_visibility_sync(target_type, queryset, info)` threading the *same* `info` from the root walk." | The symbol exists under that exact name and the mechanism holds: `optimizer/walker.py::_build_child_queryset #"queryset = field.related_model._default_manager.all()"` then `#"queryset = apply_type_visibility_sync(target_type, queryset, info, allow_sliced=True)"`. **Two description defects**: (a) the raw `(walker.py:212-214)` is an `AGENTS.md` rule-27 violation in a standing doc, and it is also factually wrong — the body sits at walker.py:385-389 at `HEAD`; (b) the call now carries `allow_sliced=True` (added by `spec-045-visibility_boundary-0_0_14` Decision 5, per the in-body comment), which the spec's quoted call shape omits. | **STALE-DESCRIPTION** (mechanism CONFORMS) |
| D12-6 | "so Slice 2's downgrade pin asserts the nested cascade narrows with the request user, not just that a `Prefetch` is planned" | `tests/optimizer/test_extension.py::test_cascading_target_downgrades_join_to_prefetch` asserts `seen_users[0] is request_user` **and** `"request_user" in str(plan.prefetch_related[0].queryset.query)` — the child SQL carries the live user's value. This is the distinguishing assertion the Decision demands, and it is present. | CONFORMS |
| D12-7 | "`DjangoNodeField` / `DjangoNodesField` resolve through `resolve_node` / `resolve_nodes` defaults that apply `get_queryset` — a cascade-hidden row refetches as `null`, indistinguishable from missing" | See S3-5. `relay.py` itself carries no visibility code; it dispatches to the `types/relay.py` defaults, which is what the spec's `## Current state` already says. | CONFORMS |
| D12-8 | "`DjangoListField` applies the type's hook in its default resolver and around `Manager`/`QuerySet`-returning consumer resolvers" | Default resolver: list_field.py:203/209. Consumer wrap: `list_field.py::_post_process_consumer_async` / its sync twin, reached from both `_wrap` branches. | CONFORMS |

#### `## Goals` items 3 and 4

| # | Contract (spec) | Evidence at `HEAD` | Grade |
|---|---|---|---|
| G3 | "Keep cascaded relations N+1-safe with zero optimizer changes. The shipped `get_queryset` -> `Prefetch` downgrade, the **`cacheable = False` request-scope rule**, and strictness silence across cascaded traversals are pinned, and the cascade itself is proven to add no query round-trips" | Every clause holds (S2-1..S2-5) **except** the phrase "the `cacheable = False` **request-scope** rule": the shipped rule is not request-scoped, it flips on the presence of any custom hook, which the spec's own plan-cache edge-case bullet states correctly ("it flips on the *presence* of a custom hook, not on whether the hook reads `info.context.user`"). Goal 3 and the edge case describe the same rule two ways, and only one is right. | **STALE-DESCRIPTION** |
| G4 | "Answer the composition questions with pins, not new machinery. The shipped `check_<field>_permission` filter/order gates survive unchanged and compose with the cascade in a fixed order; connections, node refetch, and root lists all honor a cascading hook through their existing seams" | S3-2..S3-6, D11-*, D12-*. | CONFORMS |

#### `## Edge cases and constraints` (the five bullets in this territory)

| # | Contract (spec) | Evidence at `HEAD` | Grade |
|---|---|---|---|
| E1 | **Plan-cache interaction** — "the shipped rule marks any plan baking a custom hook `cacheable = False` (`optimizer/walker.py`'s coarser custom-hook rule — it flips on the *presence* of a custom hook, not on whether the hook reads `info.context.user`). The cascade adds no new cache key dimension; pinned in Slice 2." | `optimizer/walker.py::_plan_prefetch_relation #"plan.cacheable = False"` is unconditional on the boolean. Pinned by `tests/optimizer/test_extension.py::test_plan_with_cascading_hook_uncacheable`, which asserts `misses == 2 / hits == 0 / size == 0` on the cascading half **and** the miss-then-hit `size == 1` on a non-cascading sibling extension — the second half is the control that makes the first non-vacuous. This bullet's module-level citation (`optimizer/walker.py`, no symbol) is the correct one; S2-3's symbol-level citation is the wrong one. | CONFORMS |
| E2 | **FK-id elision interaction** — "elision already falls back when a target hook must run; cascading targets therefore never elide. No change; pinned." | `optimizer/walker.py::_plan_select_relation #"and not _target_has_custom_get_queryset(target_type)"` (walker.py:731) gates the elision branch. Pinned by `tests/test_permissions.py::test_fk_id_elision_falls_back_for_cascading_target`, which asserts `plan.fk_id_elisions == ()`, `plan.select_related == ()`, and one `Prefetch` to `"category"`. | CONFORMS |
| E3 | **Strictness interaction** — "the cascade composes SQL; it cannot lazy-load, so strictness `\"raise\"` stays silent across cascaded shapes (pinned)." | The stated behavior is true at `HEAD` and the pin exists and can fail (proof attempt 4). But the sentence's causal clause — silence *because* the cascade cannot lazy-load — is not what the pin measures: `types/resolvers.py::_check_n1` reports unplanned **relation resolver** accesses only, so an eagerly-evaluating cascade would leave this row green. The property the clause names is pinned by `::test_cascaded_traversal_adds_zero_queries` instead. | CONFORMS (see finding L3) |
| E4 | **Sharded callers, the optimizer-built-prefetch-child half** — "when the cascade runs inside an **optimizer-built prefetch child**, the queryset it receives is `field.related_model._default_manager.all()` (`optimizer/walker.py::_build_child_queryset`, walker.py:212), whose `.db` is that model's *router-resolved* alias — **not** the root request's explicit `.using(\"shard_b\")`." | Mechanism holds: `_build_child_queryset` still builds from `field.related_model._default_manager.all()` with no `.using(...)`, and the cascade pins to what it is handed — `permissions.py::apply_cascade_permissions #"state = _TraversalState(alias=queryset.db, active=(cls,), path=())"`. The raw `walker.py:212` is the same rule-27 violation as D12-5 and is likewise stale (the line is walker.py:385 at `HEAD`). **Unpinned by any test**: `tests/optimizer/test_multi_db.py` contains zero `cascad` occurrences, and no `FAKESHOP_SHARDED`-gated file exercises the cascade inside a prefetch child. The spec claims no pin for this bullet ("Sharded-specific live coverage stays behind `FAKESHOP_SHARDED`"), so this is not a SKIPPED contract — see the Low finding. | **STALE-DESCRIPTION** (mechanism CONFORMS; the raw line cite is wrong and stale) |
| E5 | **Non-nullable forward-FK target hidden -> the parent row drops, not a nested `null`** — "Slice 3's nested-transitivity pin exercises the to-many shape (`test_nested_relation_traversal_respects_target_cascade`); the parent-drop shape is exercised by the connection / node / list pins." | Both halves check out. The to-many half: `test_nested_relation_traversal_respects_target_cascade` selects `allCategories { name items { name } }` and asserts the nested list narrows. The parent-drop half: every one of `test_connection_over_cascading_type_narrows_edges_and_total_count`, `test_node_refetch_of_cascade_hidden_row_returns_null`, `test_nodes_batch_holes_for_cascade_hidden_rows`, `test_list_field_default_resolver_applies_cascade` is built on `Item -> category` (`null=False`) and asserts the parent `Item` row is absent. | CONFORMS |

#### `## Definition of done` items 6-9

| # | Contract (spec) | Evidence at `HEAD` | Grade |
|---|---|---|---|
| DoD-6 | "All permission-related ORM paths are checked for N+1 behavior: the cascaded 2-deep shape adds zero query round-trips; a cascading relation target still downgrades to `Prefetch`; plans baking cascading hooks are `cacheable = False`; FK-id elision falls back; strictness `\"raise\"` stays silent across cascaded shapes." | Five clauses, five pins: S2-4, S2-2, S2-3/E1, E2, E3. | CONFORMS |
| DoD-7 | "No regression in the optimizer suites (B1-B8 plan-cache / queryset-diff coverage untouched and green)." | `uv run pytest tests/optimizer/ tests/test_permissions.py tests/test_connection.py tests/test_relay_node_field.py tests/test_list_field.py --no-cov -q` -> **1071 passed, 1 skipped**. The Slice-2 checklist's non-test bullet ("a consumer `select_related` on a cascading relation still reconciles per B8 (existing suites stay green)") names no test and is discharged by this run, which is what it asks for. | CONFORMS |
| DoD-8 | "the shipped `check_<field>_permission` filter/order gates survive unchanged; tests pin both shapes (denial on gated input regardless of cascade; gate-passing input operating on cascade-narrowed rows); a denial leaks no existence." | D11-1..D11-3, S3-2 (both shapes present in both the filter and order tests), S3-3. | CONFORMS |
| DoD-9 | "a connection over a cascading type narrows edges and `totalCount`, and every edge's nested relations respect the same cascade rule via the `Prefetch` downgrade; node refetch returns `null` for cascade-hidden rows; `DjangoListField` narrows." | S3-4, D12-4, S3-5, S3-6. | CONFORMS |

#### Census totals (derived, not asserted)

Rows enumerated above: 6 (Slice 2) + 7 (Slice 3) + 6 (Decision 11) + 8 (Decision 12) + 2 (Goals) + 5 (Edge cases) + 4 (DoD) = **38 contract rows**.

- **CONFORMS: 33** — S2-1, S2-2, S2-4, S2-5, S2-6, S3-1 … S3-7, D11-1, D11-2, D11-3, D11-4, D11-6, D12-1, D12-2, D12-3, D12-4, D12-6, D12-7, D12-8, G4, E1, E2, E3, E5, DoD-6, DoD-7, DoD-8, DoD-9.
- **STALE-DESCRIPTION: 5** — S2-3, D11-5, D12-5, G3, E4.
- **SKIPPED: 0.** No contract in this territory is stated by the spec, unsuperseded, and unimplemented by the code. Every Slice-2 and Slice-3 behavioral claim is implemented **and** pinned. Nothing routes to R3 from R1b.
- **SUPERSEDED: 0.** No later card changed a Slice-2 or Slice-3 contract; the five stale rows are description defects, not behavior flips. (The known-live behavior flips the build plan names — cycles raising, MTI `<parent>_ptr` inclusion, GFK preflight, conditional `__isnull` — are all Decision 5 / Slice 1 and belong to R1a.)
- **RENAMED: 0.** Both symbols the spec names by qualified path (`_target_has_custom_get_queryset`, `_build_child_queryset`) exist under those exact names, and all 13 named Slice-2/Slice-3 tests exist under their spec names.

### Test-name census, with assertion-quality grading

Every test named in the spec's `### Slice 2` and `### Slice 3` test-plan lists. Existence derived by `grep -rn "def <name>" tests/ examples/`; assertion quality graded against `BUILD.md` `### Query-shape tests must pin the load-bearing property, not observability`.

| Spec-named test | Exists at `HEAD` | Assertion quality |
|---|---|---|
| `test_cascaded_traversal_adds_zero_queries` | yes — `tests/test_permissions.py:2349` | **Distinguishing.** Absolute count (`django_assert_num_queries(1)`) on the cascaded shape *and* its identity-hook twin, derived from a real run — not a bare cascaded-vs-uncascaded equality. Carries the right-path guard `"IN (SELECT" in str(cascaded_qs.query)` so a silently-empty walk (which would also cost one query) cannot pass, plus `cascaded_rows == [keeps]` proving the narrowing is real. This is the shape the rule asks for. |
| `test_cascading_target_downgrades_join_to_prefetch` | yes — `tests/optimizer/test_extension.py:5181` | **Distinguishing, and it pins the Decision-12 property specifically.** Beyond `select_related == ()` / one `Prefetch` / `cacheable is False`, it asserts `seen_users[0] is request_user` and `"request_user" in str(plan.prefetch_related[0].queryset.query)` — the live request user's value is baked into the prefetch child SQL. A refactor dropping `info` from `_build_child_queryset` would still plan a `Prefetch` and would still fail this test. |
| `test_plan_with_cascading_hook_uncacheable` | yes — `tests/optimizer/test_extension.py:5266` | **Distinguishing.** `misses == 2 / hits == 0 / size == 0` on the cascading half is paired with a non-cascading sibling schema on its own extension asserting the ordinary miss-then-hit `size == 1`. The control is what stops "no hits" reading as "caching is broken generally". |
| `test_fk_id_elision_falls_back_for_cascading_target` | yes — `tests/test_permissions.py:2417` | **Distinguishing.** Asserts the full negative-and-positive plan shape (`fk_id_elisions == ()`, `select_related == ()`, exactly one `Prefetch` whose `prefetch_to == "category"`) over an `id`-only nested selection that *would* elide for a plain FK, plus `has_custom_get_queryset() is True`. |
| `test_strictness_raise_silent_across_cascaded_shape` | yes — `tests/test_permissions.py:2467` | **Failable but off-target — measured, not assumed.** Its single assertion is `result.errors is None`, the archetype of a control that might not be able to fail, so it was mutated rather than read. Four attempts: dropping the `Prefetch` registration alone leaves it green; dropping the planned-key bookkeeping alone leaves it green; removing both together fails it with `OptimizerError: Unplanned N+1: category`. So it is a real detector — of an **optimizer-planning** regression. It cannot detect the cascade-side regression the spec sentence attributes to it, because strictness reports unplanned relation-resolver accesses only. Finding L3. |
| `test_cascade_then_filter_gate_composition` | yes — `tests/test_permissions.py:2599` | **Distinguishing for the gate half; the "cascade" half is inert.** Both spec shapes are pinned (denial with `pytest.raises` on the gated input; `list(passed) == []` and `list(kept) == [public]` on passing input). But the narrowing under test comes from the hook's own `qs.filter(is_private=False)`, not from `apply_cascade_permissions`: the fixture roots on `Category`, the chain top with no cascadable forward FK, so the cascade call is a no-op. The test's own docstring says so explicitly. See the Low finding. |
| `test_cascade_then_order_gate_composition` | yes — `tests/test_permissions.py:2652` | Same as above: gate matrix distinguishing (`list(ordered) == [alpha, beta]`), cascade component inert for the same `Category`-rooted reason. |
| `test_gate_denial_no_existence_leak` | yes — `tests/test_permissions.py:2684` | **Distinguishing, and it is the row that carries the cascade half of Decision 11.** Rooted on `Item` (non-null `category` edge) so the cascade genuinely narrows; asserts the narrowing first (`== ["pub"]`) so the two fixtures differ in row content and not only in name, then compares `str(exc)` and `exc.extensions` across them. |
| `test_connection_over_cascading_type_narrows_edges_and_total_count` | yes — `tests/test_connection.py:1639` | **Distinguishing.** Seeded so `narrowed != raw` (3 rows, 2 visible); `totalCount == 2` would read 3 on any non-cascade path. Edges, cursor distinctness, and both `pageInfo` flags asserted. |
| `test_node_refetch_of_cascade_hidden_row_returns_null` | yes — `tests/test_relay_node_field.py:1309` | **Distinguishing.** A visible sibling item is seeded alongside the hidden one, so `data == {"item": None}` is not the trivially-empty-table result; `errors is None` pins "null, not an error". |
| `test_nodes_batch_holes_for_cascade_hidden_rows` | yes — `tests/test_relay_node_field.py:1466` | **Distinguishing.** The batch interleaves hidden and visible ids and asserts positional `[None, {"name": ...}]` — order-sensitive, so a hole-collapsing implementation fails. |
| `test_list_field_default_resolver_applies_cascade` | yes — `tests/test_list_field.py:1479` | **Distinguishing.** Two items seeded, one under a private category; `names == ["visible_item"]` (not merely non-empty). Deliberately scoped to the default resolver, with the scoping stated in the docstring. |
| `test_nested_relation_traversal_respects_target_cascade` | yes — `tests/test_permissions.py:2738` | **Distinguishing.** Two items under one public category, one of them hidden by the target hook; the whole `result.data` structure is asserted equal, so an un-narrowed nested list fails. Query kept minimal so it can only take the planned-`Prefetch` path. |

**13 named, 13 present, 0 renamed, 0 absent.** Assertion quality: **10 distinguishing outright**; **1** (`test_strictness_raise_silent_across_cascaded_shape`) failable but measuring an adjacent property to the one its spec sentence claims (L3); **2** (`test_cascade_then_filter_gate_composition` / `test_cascade_then_order_gate_composition`) distinguishing for the gate contract but inert for the cascade component of the composition sentence (L1). None is vacuous, and every one of the ten was graded by reading its assertions against a fixture seeded so `narrowed != raw` — not by name and not on a bare count.

### Failability proof (Worker 3, own)

Performed under the `worker-3.md` `## Scope` carve-out. **Each mutation was recorded in this artifact before it was made.** One boundary at a time, reverted before the next, every revert proved by `cmp` against a pristine copy held **outside the repository**. No `git checkout` / `git restore` / `git stash` was used at any point.

**Claim under proof:** `tests/test_permissions.py::test_strictness_raise_silent_across_cascaded_shape` asserts only `result.errors is None`. Per `BUILD.md` `### Query-shape tests must pin the load-bearing property, not observability` and `worker-3.md` `### Suspect the fixture before accepting "untestable"`, a lone "no error" assertion on a negative property is the archetype of a control that may be structurally incapable of failing. The question is whether the strictness sentinel is armed and reachable in this fixture at all.

**Scratch path (outside the repo):** `/private/tmp/claude-501/-Users-riordenweber-projects-django-strawberry-framework/e3a7bb93-0439-4447-b248-b5509e0f6d36/scratchpad/dsf-proof-strictness-cascade.orig`

**Scope as run, both attempts:** `uv run pytest tests/test_permissions.py -k strictness_raise_silent_across_cascaded_shape --no-cov`
**Pre-mutation state of that scope:** green — `1 passed in 2.65s`.

#### Attempt 1 — drop the `Prefetch` registration only (0 rows; the mutation did not remove the boundary)

- **Anchor check, first:** `grep -c 'append_prefetch_unique(plan.prefetch_related, Prefetch(lookup_path, queryset=child_queryset))' django_strawberry_framework/optimizer/walker.py` -> `1`. Exactly one match, so no prior live mutation was inherited.
- **Boundary targeted:** `optimizer/walker.py::_plan_prefetch_relation #"append_prefetch_unique(plan.prefetch_related, Prefetch(lookup_path, queryset=child_queryset))"` (walker.py:822).
- **Mutation applied:** the `append_prefetch_unique(...)` call replaced by `pass`, so the child queryset is still built and the plan never registers a `Prefetch` for the relation.
- **Failing node ids:** none. **Collection / setup errors:** 0. Result: `1 passed in 2.62s`.
- **why 0:** **not** weakly pinned and **not** harness-impossible — the mutation did not remove the boundary the test rests on, so this attempt is a discarded instrument rather than a measurement of the test. The line immediately above the mutated one, `_record_prefetch_path_keys(plan, lookup_path, (*resolver_identities, *nested_keys))` (walker.py:821), still recorded the relation's resolver keys as PLANNED. Strictness reads `planned_resolver_keys`, not the `Prefetch` list, so the plan claimed the relation was planned while carrying no `Prefetch` — the "planned -> silent" parity the `connection.py` resolver docstring names. Deleting the effect while leaving the bookkeeping that silences the sentinel is precisely the perturb-near-the-boundary failure `BUILD.md` `### What gets recorded` warns against.
- **Revert, proved by byte-comparison:** `cp <scratch>/dsf-proof-strictness-cascade.orig django_strawberry_framework/optimizer/walker.py` then `cmp django_strawberry_framework/optimizer/walker.py <scratch>/dsf-proof-strictness-cascade.orig` -> **exit 0**. Cross-checked with `git diff --stat HEAD -- django_strawberry_framework/optimizer/walker.py` -> empty. (The two residual `MUTATION` tokens a marker-grep reports at walker.py:121 and walker.py:570 are pre-existing GraphQL `OperationType.MUTATION` prose, present at `HEAD`.)

#### Attempt 2 — remove the whole prefetch planning boundary

- **Anchor check, first:** `grep -c '    lookup_path = f"{prefix}{instance_accessor(django_field)}"' django_strawberry_framework/optimizer/walker.py` -> `1`.
- **Boundary mutated:** `optimizer/walker.py::_plan_prefetch_relation` — the entire planning body after `_record_relation_access`, i.e. the `Prefetch` construction **and** the `_record_prefetch_path_keys` bookkeeping together. That pairing is what makes the relation "planned" for strictness, so it is one boundary and must be removed as one.
- **Mutation applied:** an unconditional `return` inserted immediately before `lookup_path = f"{prefix}{instance_accessor(django_field)}"` (walker.py:792), so no `Prefetch` is built and none is registered. The cascaded traversal then lazy-loads at resolve time, which is the condition strictness `"raise"` exists to catch.
- **Failing node ids:** none. **Collection / setup errors:** 0. Result: `1 passed in 2.94s`.
- **Mutation-is-live control (same mutation, wider scopes):** the mutation is emphatically effective — `uv run pytest tests/optimizer/test_extension.py --no-cov -q -k cascad` -> `2 failed` (`tests/optimizer/test_extension.py::test_cascading_target_downgrades_join_to_prefetch`, `::test_plan_with_cascading_hook_uncacheable`) and `uv run pytest tests/test_permissions.py --no-cov -q` -> `1 failed, 62 passed, 1 skipped` (`tests/test_permissions.py::test_fk_id_elision_falls_back_for_cascading_target`). Three sibling rows in this same territory detect the removed boundary; the strictness row does not. This control is what makes the zero a measurement of the test rather than of the mutation.
- **Revert, proved by byte-comparison:** `cp <scratch>/dsf-proof-strictness-cascade.orig django_strawberry_framework/optimizer/walker.py` then `cmp` -> **exit 0**; `git diff --stat HEAD -- django_strawberry_framework/optimizer/walker.py` -> empty; `grep -n "MUTATION-2"` -> no match. Post-revert sweep `uv run pytest tests/optimizer/ tests/test_permissions.py --no-cov -q` -> **889 passed, 1 skipped**.

#### Attempt 3 — remove the planned-key bookkeeping that silences the sentinel

- **Purpose:** attempt 2 established *that* the pin is non-distinguishing; this attempt establishes *why*, which is what decides weakly-pinned versus harness-impossible and therefore what the remediation is.
- **Anchor check, first:** `grep -c '    append_unique_many(plan.planned_resolver_keys, resolver_identities)' django_strawberry_framework/optimizer/walker.py` -> recorded with the result below.
- **Boundary mutated:** `optimizer/walker.py::_record_relation_access #"append_unique_many(plan.planned_resolver_keys, resolver_identities)"` (walker.py:851) — the unconditional append whose own docstring says it "stays unconditional so strictness still sees the planned relation regardless of operation".
- **Mutation applied:** the append replaced by `pass`, so no relation is recorded as planned and `types/resolvers.py::_check_n1 #"if not force_unplanned and _relation_is_planned(key, planned):"` can no longer short-circuit.
- **Anchor check result:** `1`.
- **Failing node ids:** none. **Collection / setup errors:** 0. Result: `1 passed in 2.85s`.
- **why 0, this attempt:** the mutation removed only the first of `_check_n1`'s two silencing conditions. The `Prefetch` was still planned and still fired, so the second condition held: `types/resolvers.py::_check_n1 #"lazy = _will_lazy_load_single(root, probe_name)"` returned `False` because Django's fields cache was already populated. Not a measurement of the test.
- **Revert, proved by byte-comparison:** `cmp` -> **exit 0**; `git diff --stat HEAD -- django_strawberry_framework/optimizer/walker.py` -> empty; `grep -n "MUTATION-3"` -> no match.

#### Attempt 4 — remove both silencing conditions together (the composite boundary)

- **Purpose:** attempts 2 and 3 each removed one of `_check_n1`'s two independent silencers, and each left the other holding. They are not separable: "the relation is planned" and "the relation is already loaded" are produced by the same planning act, so per `BUILD.md` `### Slice splitting` ("boundaries that cannot be separated ... are one unit") the pair is one boundary and must be removed as one.
- **Anchor checks, first:** both anchors re-verified at exactly `1` before the copy.
- **Boundary mutated:** the pairing of `optimizer/walker.py::_plan_prefetch_relation` (the `Prefetch` build + registration) and `optimizer/walker.py::_record_relation_access #"append_unique_many(plan.planned_resolver_keys, resolver_identities)"`.
- **Mutation applied:** attempt 2's unconditional `return` in `_plan_prefetch_relation` **and** attempt 3's removal of the `planned_resolver_keys` append, simultaneously. The cascaded relation is then neither planned nor prefetched, so the resolver's forward-FK access genuinely lazy-loads with no planned key to excuse it — the exact condition strictness `"raise"` exists to report.
- **Anchor check results:** `1` and `1`.
- **Failing node ids:** `tests/test_permissions.py::test_strictness_raise_silent_across_cascaded_shape`. **Collection / setup errors:** 0. Result: `1 failed in 2.63s`, raising

  ```text
  django_strawberry_framework/types/resolvers.py:324, in _check_n1
      raise OptimizerError(f"Unplanned N+1: {field_name}{suffix}")
  django_strawberry_framework.exceptions.OptimizerError: Unplanned N+1: category
  ```

  One row is the maximum obtainable at this scope (`-k <single test name>` collects exactly one item), so the weakly-pinned arithmetic in `BUILD.md` `### Acceptance rule` does not apply: this is a Worker 3 re-run of an existing pin at single-row scope, not a Worker 2 boundary count.
- **Revert, proved by byte-comparison:** `cmp django_strawberry_framework/optimizer/walker.py <scratch>/dsf-proof-strictness-cascade.orig` -> **exit 0**; `git diff --stat HEAD -- django_strawberry_framework/optimizer/walker.py` -> empty; `grep -n "MUTATION-4"` -> no match. Post-revert sweep `uv run pytest tests/optimizer/ tests/test_permissions.py tests/test_connection.py tests/test_relay_node_field.py tests/test_list_field.py --no-cov -q` -> **1071 passed, 1 skipped**, byte-identical to the pre-proof reading. `git status --short django_strawberry_framework tests examples` reports only the two baseline-dirty concurrent-session paths (`examples/fakeshop/db.sqlite3`, `tests/test_build_kanban_html.py`) and no walker change.

#### Verdict

**The pin is failable, and the four attempts locate exactly what it detects.** `types/resolvers.py::_check_n1` has two independent silencers on a forward-FK access — the planned-key short-circuit (`#"if not force_unplanned and _relation_is_planned(key, planned):"`) and the already-loaded probe (`#"lazy = _will_lazy_load_single(root, probe_name)"`) — and removing either alone leaves the row green. Only removing both makes it fail.

Two consequences worth carrying forward, neither a blocker:

1. **`result.errors is None` is a real assertion here, not a vacuous one.** It fails on a genuine optimizer-planning regression in the cascaded shape, which is what "strictness stays silent across cascaded shapes" is worth as a regression detector.
2. **It cannot detect a cascade-side regression.** Strictness reports *unplanned relation resolver* accesses only. If `permissions.py` ever started evaluating a target queryset eagerly — the failure Decision 7's "lazy subquery composition" exists to prevent — no relation would become unplanned, `_check_n1` would never fire, and this row would stay green. That property is pinned instead by `tests/test_permissions.py::test_cascaded_traversal_adds_zero_queries`'s absolute `django_assert_num_queries(1)`, which is the row that would actually catch it. The two tests are complementary and neither substitutes for the other; the spec sentence reads as though the strictness row carried the cascade property, which it does not.

**Boundaries re-run vs accepted on record:** this cohort had no Worker 2 build report and therefore no recorded proofs to audit. The one boundary re-run is the strictness pin above, chosen because it is the only assertion in this territory whose single-clause form could not be graded by reading. Every other pin in `### Test-name census` was graded distinguishing by reading its assertions against the seeded fixture (each asserts *which rows survive* against a fixture where narrowed != raw), which is the standard `BUILD.md` `### Query-shape tests must pin the load-bearing property` sets, and none was accepted on a bare count.

### Fail-open shape hunting

Hunted per `BUILD.md` `### Fail-open shapes` across every visibility-decision path in this territory. Findings: **none in this territory**.

- `optimizer/walker.py::_target_has_custom_get_queryset` — `target_type is not None and target_type.has_custom_get_queryset()`. The `is not None` short-circuit returns `False` for an unresolved target, which is the *conservative* direction on the downgrade path only in appearance: `False` means "keep `select_related`", i.e. no prefetch child and no target hook. But an unresolved target is also a target with no registered `DjangoType` and therefore no visibility contract to enforce — the same rule `permissions.py` applies at `registry.get(...) is None`. Not a permit-on-incoherence: there is no hook to run.
- `optimizer/walker.py::_build_child_queryset` — the `if has_custom_qs:` guard is a plain boolean on a precomputed value, not a `getattr` default or a truthiness test on a possibly-absent attribute. The `allow_sliced=True` argument widens what the shared seal accepts, but it delegates the decision to `utils/querysets.py` rather than absorbing a failure locally, and the in-body comment names the designed degradation it protects (`nested_fetch.py::unwindowable_child_queryset_reason`).
- `connection.py::_pipeline_sync` / `_pipeline_async` — the non-queryset arm returns `source` unchanged *after* `_guard_sidecar_input_against_non_queryset` rejects `filter:` / `orderBy:`. That is a guard on the answer (is this a queryset at all?), not on one spelling of a bad input, and the async twin's `reject_residual_async_source` explicitly exists to stop an inner awaitable slipping past the non-queryset arm and skipping visibility entirely — a fail-**closed** guard against exactly this class.
- `utils/permissions.py::invoke_permission_method` — routes the gate's return through `reject_async_in_sync_context`, whose own docstring names the fail-open it prevents: an `async def` gate returning a truthy un-awaited coroutine that a naive call would read as success. Closed.
- No bare `except`, no `max(...)`/`min(...)` clamp, and no `or`-fallback participates in any visibility decision in the seven territory files.

### High:

None.

### Medium:

None. Every contract this territory's spec text states is implemented at `HEAD` and pinned by an assertion that can fail. The five defects found are all descriptions, not behavior, and all route to R2 rather than R3.

### Low:

#### L1 — Two gate-composition pins exercise `get_queryset` narrowing, not cascade narrowing

`tests/test_permissions.py::test_cascade_then_filter_gate_composition` and `::test_cascade_then_order_gate_composition` root their fixture on `Category`, the top of the `Entry -> Item -> Category` chain, which has no cascadable forward FK. `apply_cascade_permissions` on that type is a no-op; the row narrowing the tests observe comes entirely from the hook's own `qs.filter(is_private=False)`. Both docstrings state this openly, and `::test_gate_denial_no_existence_leak` carries the genuinely-cascading half of Decision 11 (it roots on `Item` and asserts the cascade narrowed before comparing the two denials), so Decision 11's composition contract is not unpinned — it is pinned across two tests rather than one, with the two whose *names* say "cascade" exercising the weaker half.

```tests/test_permissions.py:2618:2622
    # (Calling
    # ``apply_cascade_permissions`` directly here would be a no-op - ``Category`` is
    # the chain top with no cascadable forward FK, and the cascade does not invoke
    # the type's own hook; the narrowing genuinely lives in ``get_queryset``.)
```

Recommended change: none to the code — the contract is covered. Recorded so a later reader does not mistake the test names for evidence that the cascade half is pinned there, and so R2 can decide whether the spec's Slice-3 bullet should say which pin carries which half.

#### L2 — The prefetch-child alias behavior is described but asserted nowhere

The `## Edge cases and constraints` sharded-callers bullet describes a real, security-adjacent behavior — inside an optimizer-built prefetch child the cascade pins to the child model's router-resolved alias rather than the root request's explicit `.using(...)`. It is verified by reading (`optimizer/walker.py::_build_child_queryset` builds a bare `_default_manager.all()`; `permissions.py::apply_cascade_permissions #"state = _TraversalState(alias=queryset.db, active=(cls,), path=())"` pins to what it is handed), but nothing asserts it: `tests/optimizer/test_multi_db.py` has zero `cascad` occurrences and no `FAKESHOP_SHARDED`-gated file exercises the cascade inside a prefetch child.

This is **not** a SKIPPED contract — the spec claims no pin for this bullet ("Sharded-specific live coverage stays behind `FAKESHOP_SHARDED` per `AGENTS.md`"). Recorded as a coverage observation for the maintainer: the behavior is described as correct-by-design in a standing doc with no executable evidence behind it, and `permissions.py`'s cross-alias rejection (`#"a cascade cannot compose cross-database subqueries."`) is the boundary that would fire if the description were wrong. Recommended change: none in this cycle; a future `FAKESHOP_SHARDED`-gated row asserting the prefetch child's `.db` would close it.

#### L3 — The strictness pin measures optimizer planning, not the cascade property its spec sentence names

The `## Edge cases and constraints` strictness bullet and Slice 2's fourth pin both read as though `tests/test_permissions.py::test_strictness_raise_silent_across_cascaded_shape` pinned the causal claim "the cascade composes SQL; it **cannot lazy-load**, so strictness `"raise"` stays silent". It does not. `types/resolvers.py::_check_n1` fires only on an unplanned **relation resolver** access; a cascade that began evaluating its target querysets eagerly — the regression Decision 7's lazy-composition contract exists to prevent — would add queries without making any relation unplanned, and this row would stay green.

The proof establishes both halves of that: removing the optimizer's prefetch planning **and** its planned-key bookkeeping together does fail the row (`OptimizerError: Unplanned N+1: category`), so it is a live detector of an optimizer-planning regression; removing either alone leaves it green, because `_check_n1` carries two independent silencers.

```django_strawberry_framework/types/resolvers.py:309:320
    if not force_unplanned and _relation_is_planned(key, planned):
        return
    ...
            lazy = _will_lazy_load_single(root, probe_name)
    if not lazy:
        return
```

Recommended change: **none to the test or the code.** The cascade's zero-round-trip property is already pinned, correctly and with an absolute count, by `::test_cascaded_traversal_adds_zero_queries`. The defect is in how the two spec sentences attribute the properties to the pins, and it routes to R2 as a wording fix — see `### Notes for Worker 1 (spec reconciliation)`.

### DRY findings

None in this territory. Slices 2 and 3 add no source, so there is no new abstraction to challenge and no duplicated logic introduced by this card in any of the seven files.

Two observations from reading the territory side by side, neither a finding:

- The `spec-034` cascade pins are cohesive rather than duplicated: each of the four surface files declares its own minimal local cascading fixture (`tests/test_connection.py::_make_cascading_item_node`, `tests/test_relay_node_field.py::_make_cascading_item_node`, and inline classes in `tests/test_list_field.py` / `tests/optimizer/test_extension.py`). These are four near-copies of one shape, but they live in four independently-runnable test modules with different registry/reload harnesses, and each docstring states why it is local. Consolidating them into a shared fixture would couple four schema-module harnesses that `BUILD.md` `### Example-project schema changes must sync every schema-module list` warns are order-dependent. Recommending against consolidation.
- `plan.cacheable = False` is set at three sites in `optimizer/walker.py` (`_plan_prefetch_relation` walker.py:795, `_apply_hint` walker.py:1015, and the child-plan propagation the walker.py:1102 docstring describes). They encode three different reasons (custom hook, consumer-supplied `Prefetch` closure, non-cacheable child propagation) and the `_apply_hint` comment explicitly names the discipline it mirrors. Three sites, one rule, deliberately cross-referenced — not a DRY defect.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` is **empty** — the file is unmodified in the working tree.

Read against the spec: `__all__` is a tuple in `django_strawberry_framework/__init__.py` and carries exactly two symbols this card added — `"aapply_cascade_permissions"` and `"apply_cascade_permissions"` — both authorized by Decision 4 ("Both are re-exported from `django_strawberry_framework/__init__.py` and join `__all__`") and Definition-of-done item 5. **No third symbol traceable to card `034` appears in `__all__` or in the re-export block.** Slices 2 and 3 were declared "no source change" and the public surface confirms it: nothing in the optimizer, connection, relay, list-field, filter, or order territory was promoted to the package root by this card.

(The `__all__` membership itself is R1a's territory per the partition — recorded here only to the extent this cohort's "no new public exports beyond the two cascade symbols" obligation requires.)

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity (only when the slice touches docs, release metadata, KANBAN, or archived specs)

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces. (This cohort is read-only and writes only this artifact; the plan's maintainer-set scope excludes every generated doc.)

### Static inspection helper

Run per `BUILD.md` `### When to run the helper during build` (a file under `optimizer/` is in scope), with `--output-dir docs/shadow` as this process requires:

```shell
uv run python scripts/review_inspect.py django_strawberry_framework/optimizer/walker.py --output-dir docs/shadow
uv run python scripts/review_inspect.py django_strawberry_framework/connection.py --output-dir docs/shadow
```

Both wrote `<stem>.overview.md` + `<stem>.stripped.py` under `docs/shadow/`. Walking the four sections `BUILD.md` `### Reading the overview` names, for `walker.py` (24 imports, 37 symbols, 8 control-flow hotspots, 65 executable marker lines, 7 repeated literals):

- **Django / ORM markers** — walked every entry. The markers relevant to this territory are the six `get_queryset` lines (walker.py:188, 200, 201, 731, 793, 794, 817, 863, 877), the two `Prefetch` lines (walker.py:9, 822), the `select_related` append (walker.py:738) and the two `prefetch_related` appends (walker.py:798, 822, 1024). Each is justified by a census row above: 188/200/201 are the downgrade rule and its predicate (S2-2); 731 is the FK-id-elision fallback gate (E2); 793-795 is the `cacheable = False` flip (S2-3 / E1); 817/863/877 thread `has_custom_get_queryset` into `_build_child_queryset` (D12-5); 822 is the `Prefetch` registration this pass mutated for its failability proof. The remaining markers (`field_map`, `OptimizationPlan`, `only_fields`, `_meta.pk.attname`) are outside this card's territory and belong to the optimizer's own specs. No entry is unaccounted for and none produced a finding.
- **Repeated string literals** — 7 entries, all low multiplicity: `3x prefetch`, `3x connection`, `3x arguments`, `2x operation`, `2x _optimizer_runtime_prefixes`, `2x prefetch_through`, `2x selections`. `"prefetch"` is the planner's kind token, returned from `plan_relation` and compared in `_dispatch_single_relation`; it is a protocol value shared with `optimizer/nested_planner.py`, not an accidental repetition. None is a `034` literal, and none crosses into this card's files. No DRY candidate.
- **Control-flow hotspots** — 8 entries. Two are in this territory: `_plan_select_relation` (58 lines, 3 branches) and `_plan_prefetch_relation` (67 lines, 2 branches). Both are short-branch dispatchers whose complexity is in their call graph rather than their own bodies, and the two branches this card's contracts depend on (the elision gate, the `cacheable` flip) are each one `if` with no nesting. `_walk_selections` (212 lines, 20 branches) and `_apply_hint` (141 lines, 8 branches) are the genuinely heavy bodies; neither carries a `034` contract, and both belong to the optimizer's own specs. Medium-tier attention applied, no finding.
- **Imports** — 24, direction one-way as documented: `walker.py` imports up into `..exceptions` / `..registry` / `..utils.*` and sideways into its own `optimizer/` siblings (`nested_planner`, `field_meta`, `hints`, `join_taxonomy`). The one that matters to this card is `from ..utils.querysets import apply_type_visibility_sync` (walker.py:16) — the shared visibility seam, imported rather than reimplemented, which is what makes Decision 12's "no optimizer change" true. No cross-folder import outside the documented boundary.

No helper skip was taken; `extension.py`, `relay.py`, `list_field.py`, `filters/sets.py`, and `orders/sets.py` were read directly, and none of them was touched by this cohort (which writes nothing) or by Slices 2/3 (which land no source), so the helper's trigger conditions do not apply to them.

### What looks solid

- **The "pins, not features" claim is true at `HEAD`, and it is checkable in one command.** Zero occurrences of `apply_cascade_permissions` and zero of `spec-034` across all seven territory source files. Slices 2 and 3 did what they said: they added assertions and no code, and four releases later the seams they bet on are all still where the spec put them.
- **The Decision-12 dependency-to-protect survived the very refactor it feared.** `_build_child_queryset` has since gained a `spec-045` sealed-queryset argument (`allow_sliced=True`) and moved ~170 lines down the file, and it still threads the root walk's `info` into `apply_type_visibility_sync`. The Slice-2 pin that asserts the child SQL carries the live user's value is the reason that would have been caught if it had not.
- **Two of the pins carry their own negative controls,** which is rarer than it should be: `test_plan_with_cascading_hook_uncacheable` runs a non-cascading sibling schema on a separate extension instance so "0 hits" cannot be read as "caching is broken", and `test_cascaded_traversal_adds_zero_queries` measures its uncascaded twin over the same seeded rows rather than asserting a bare equality.
- **The test docstrings state their own scope limits rather than overclaiming.** The two gate-composition tests say in-body that the cascade call is a no-op for their `Category`-rooted fixture; `test_list_field_default_resolver_applies_cascade` says it is deliberately scoped to the default resolver. Finding L1 is written from the test's own comment, not against it.
- **`_check_n1`'s two silencers are documented where they live.** The reason attempts 2 and 3 each returned a false zero is written into `optimizer/walker.py::_record_relation_access`'s own docstring ("The `planned_resolver_keys` append stays unconditional so strictness still sees the planned relation regardless of operation"). The code said what the mutation had to remove; reading it first would have saved an attempt.
- **`utils/permissions.py` predates this card**, so Decision 11's "no unified dispatcher" describes the same world as `HEAD`. This was checked (`git log --diff-filter=A`) rather than inferred; the opposite reading would have produced a false STALE-DESCRIPTION.

### Temp test verification

No temp test was written. `docs/builder/temp-tests/034-r1b/` was not created: the one suspicion that warranted mechanical proof (`test_strictness_raise_silent_across_cascaded_shape`'s single `errors is None` assertion) is answered by a production-code mutation, which is the stronger instrument — a temp test could only have demonstrated that some *other* shape raises, whereas the mutation demonstrates that *this* row fails when the property it claims to pin stops holding. Disposition: none to record.

### Notes for Worker 1 (spec reconciliation)

Six spec sentences R2 must rewrite, each with what is true at `HEAD` and the attribution R2 needs for the rationale's `**Post-ship:**` bullet. All six are description defects; none implies a code change, and none routes to R3.

- **Slice 2 checklist, second bullet** — "plans embedding a cascading hook are `cacheable = False` (the shipped rule marks **any** plan baking a custom `get_queryset` uncacheable — [`optimizer/walker.py::_target_has_custom_get_queryset`][walker] — regardless of whether the hook reads the request)". **True at `HEAD`:** the behavior is exactly as stated, but the cited symbol is the wrong one. `_target_has_custom_get_queryset` is a two-line boolean predicate that never touches `plan.cacheable`; the rule is `optimizer/walker.py::_plan_prefetch_relation #"plan.cacheable = False"`. The same bullet's *first* clause cites the same symbol correctly, for the downgrade. **Attribution:** no post-ship change — the citation was imprecise as written. The spec's own `## Edge cases and constraints` plan-cache bullet already cites this correctly at module level, so R2 has a same-file model to follow.
- **Decision 11's three-layer table, row 1** — "Row visibility (incl. cascade) | `DjangoType.get_queryset` | `(cls, queryset, info)`". **True at `HEAD`:** `types/base.py::DjangoType.get_queryset` is `(cls, queryset, info, **kwargs)`; every fixture in this territory's tests declares the `**kwargs` form. **Attribution:** the `**kwargs` tail is the shipped default's forward-compatibility slot and predates this card — this is a transcription omission in the table cell, not a post-ship flip. R2 should decide whether the table shows full signatures or intentional short forms, and apply the same choice to row 2 (`check_<field>_permission(self, request)`, which *is* the full signature).
- **Decision 12, third bullet** — "[`optimizer/walker.py::_build_child_queryset`][walker] (walker.py:212-214) builds `field.related_model._default_manager.all()` and, when the target reports a custom hook, runs it through `apply_type_visibility_sync(target_type, queryset, info)`". **True at `HEAD`:** the symbol and the mechanism both hold, but (a) `(walker.py:212-214)` is a raw `path:NN` in a standing doc, which `AGENTS.md` rule 27 permits only in per-cycle scratchpads, and it is now numerically wrong (walker.py:385-389); (b) the call carries a fourth argument, `allow_sliced=True`. **Attribution:** `spec-045-visibility_boundary-0_0_14` Decision 5 (degrade-to-unplanned) added `allow_sliced=True`, recorded in the in-body comment at `optimizer/walker.py::_build_child_queryset #"``allow_sliced=True``: a nested-connection child may legitimately return a"`. The line-number drift is ordinary file growth. **The `-terms.csv` / `check_citations.py` gates cannot see either defect** — `check_citations.py` is `path::Symbol`-only with `docs/` out of scope — so R2 is the only pass that will catch it.
- **`## Edge cases and constraints`, sharded-callers bullet** — "the queryset it receives is `field.related_model._default_manager.all()` ([`optimizer/walker.py::_build_child_queryset`][walker], walker.py:212)". **True at `HEAD`:** same as above — mechanism correct, raw line number both rule-27-illegal and stale. **Attribution:** none needed beyond file growth; this is the second of the two `walker.py:212` sites the Slice-0 pass flagged as suspicions and this cohort has now confirmed. Fixing one without the other leaves the class alive, and a grep for `walker.py:` finds both.
- **`## Goals` item 3** — "The shipped `get_queryset` -> `Prefetch` downgrade, the **`cacheable = False` request-scope rule**, and strictness silence ... are pinned". **True at `HEAD`:** the rule is *not* request-scoped. It flips on the presence of any custom `get_queryset`, whether or not the hook reads the request — which the spec's own plan-cache edge-case bullet states correctly and explicitly calls "coarser". Goal 3 and the edge case describe one rule two incompatible ways. **Attribution:** the rationale companion already records the correction — Decision 7's `### Changes this Decision underwent` says "**Revision 2 (L3)** reworded the plan-cache cacheability reason from 'reads `info.context.user`' to the coarser shipped rule: any custom `get_queryset` flips the plan uncacheable." The reword landed in Decision 7 and the edge case but **never reached `## Goals` item 3**, which still carries the pre-Revision-2 wording. This is the highest-value of the five: it is a live contradiction inside the spec, not merely an imprecise citation.

- **`## Edge cases and constraints`, strictness bullet, and the Slice-2 checklist's fourth pin** — "the cascade composes SQL; it cannot lazy-load, so strictness `\"raise\"` stays silent across cascaded shapes (pinned)" / "a Strictness mode `\"raise\"` run across a cascaded 2-deep traversal stays silent". **True at `HEAD`:** both statements of *behavior* are correct, and the pin exists and can fail. What is false is the implied attribution: the named pin does not measure the causal clause. `types/resolvers.py::_check_n1` reports unplanned relation-resolver accesses only, so an eagerly-evaluating cascade would leave the row green; the zero-round-trip property is pinned by `tests/test_permissions.py::test_cascaded_traversal_adds_zero_queries` instead. Measured, not inferred — see `### Failability proof (Worker 3, own)`, four attempts, and finding L3. **Attribution:** no post-ship change; the sentence has read this way since Revision 1 and no cohort had mutated the pin before. R2's fix is a wording change that says what the strictness row detects (an optimizer-planning regression in the composed shape) and stops implying it guards the lazy-load property; the rationale's `**Post-ship:**` bullet under Decision 7 is the right home for the measurement, since Decision 7 is where the zero-round-trip claim and its proof live.

Two items outside R1b's territory, recorded in one bullet each per the dispatch and not audited:

- **Slice 1 test-plan harness note** (R1a): the `test_multi_db_subquery_pinned_to_caller_alias` entry says to build the pin "on the established [`tests/optimizer/test_multi_db.py`][test-opt-multi-db] harness". The test exists at `tests/test_permissions.py:828`; `tests/optimizer/test_multi_db.py` contains zero `cascad` occurrences. Whether "build it on that harness" means "borrow its in-test alias/router pattern" (satisfied) or "put it there" (not) is R1a's call. The same sentence carries a third raw line cite, `examples/fakeshop/config/settings.py` line ~116.
- **Decision 6 / Slice 1 divergences** (R1a): `tests/test_permissions.py` at `HEAD` carries `test_mti_parent_link_edge_included`, `test_mutual_cycle_fails_closed_with_path`, and `test_gfk_default_walk_preflights_closed` — three test names that invert what the spec's Slice-1 test plan names (`test_mti_parent_link_edge_excluded`, cycles never raising, GFK silently skipped). These are the deliberate later flips the build plan's `## Cycle shape` already enumerates and they belong wholly to R1a's Decision 5 territory. Not audited here beyond noting that none of them touches a Slice-2 or Slice-3 contract.

### Review outcome

`review-accepted`.

The audit is complete and trustworthy: 38 contract rows enumerated and graded, 33 CONFORMS, 5 STALE-DESCRIPTION, **0 SKIPPED**, 0 SUPERSEDED, 0 RENAMED; 13 spec-named tests, 13 present, 0 renamed, 0 absent, assertion quality graded individually and the one pin that could not be graded by reading settled by four recorded mutations. Nothing in this territory routes to R3 — no contract the spec states in Slices 2/3, Decisions 11/12, Goals 3/4, the five edge-case bullets, or DoD 6-9 is unimplemented at `HEAD`. All three Low findings are recorded observations rather than blockers, and all six spec-text defects route to R2.

`revision-needed` was considered and rejected: nothing found undermines the audit's own trustworthiness. Both instruments that could have misfired were caught. The lone `errors is None` assertion was mutated rather than read, and the first two mutations each returned a clean, convincing, and **wrong** zero — a mutation that does not remove the boundary reads exactly like a boundary nothing pins, and only the mutation-is-live control (three sibling rows failing under the same mutation) told the two apart. The one finding that would have been wrong (Decision 11's "no unified dispatcher" read against `utils/permissions.py`) was killed by dating the module against the card with `git log --diff-filter=A` instead of inferring from the code.

---

## Final verification (Worker 1)

Performed by the R2 spec-reconciliation pass (`docs/builder/bld-034-review-2-spec_reconciliation.md`). Appended only; nothing this cohort wrote was altered.

**The census is sound.** The 38 rows re-tally to the section sizes stated (6 + 7 + 6 + 8 + 2 + 5 + 4) and to 33 / 5 / 0 / 0 / **0 SKIPPED**; the 13 spec-named Slice-2 and Slice-3 tests all exist under their spec names. Two of this cohort's methodological choices are what make the verdict trustworthy rather than merely tidy. The first is the four-attempt failability proof on `test_strictness_raise_silent_across_cascaded_shape`: a lone `result.errors is None` assertion is the archetype of a control that cannot fail, and reading it would have produced either a false CONFORMS or a false SKIPPED. The proof instead located exactly what the row detects — and the first two attempts each returned a clean, convincing and *wrong* zero, which is itself the finding worth carrying: a mutation that does not remove the boundary reads identically to a boundary nothing pins, and only the mutation-is-live control told them apart. The second is dating `utils/permissions.py` and `sets_mixins.py` against the card with `git log --diff-filter=A` before grading Decision 11's "no unified dispatcher": inferring from the code would have manufactured a STALE-DESCRIPTION where none exists.

**Discharged in the spec by R2 — all 6.** S2-3 (the `cacheable = False` rule cited to `_target_has_custom_get_queryset`, which never touches `plan.cacheable`; repointed to `_plan_prefetch_relation`). G3 (`## Goals` item 3's "request-scope rule" against the plan-cache edge case's correct coarser rule — R1b called this the highest-value of its five, and it was: sweeping the phrase rather than the finding's line found **two further homes**, in `## Key glossary references` and `## Current state`, that the finding did not name). D11-5 (`(cls, queryset, info)` → `(cls, queryset, info, **kwargs)`). D12-5 and E4 (both `walker.py:212` sites, plus a third the Slice-1 harness note carried — R1b's warning that fixing one leaves the class alive is why all three moved together, and `allow_sliced=True` was added to the quoted call with its `spec-045` attribution). E3/L3 (the strictness bullet and Slice 2's fourth pin now say which pin carries which property, and that the two are complementary).

**Recorded rather than acted on — 2.** Finding **L1** (the two gate-composition pins exercise `get_queryset` narrowing rather than cascade narrowing, because their fixture roots on the chain top) needs no spec edit: Decision 11's composition contract is genuinely pinned, across two tests rather than one, and `::test_gate_denial_no_existence_leak` carries the cascading half. R1b's own recommendation was "none to the code", and the observation is preserved here so a later reader does not mistake the test names for evidence. Finding **L2** (the prefetch-child alias behaviour is described in a standing doc and asserted by nothing) goes to the deferred-work catalog as a coverage observation; it is not a SKIPPED contract, because the spec claims no pin for that bullet.

**Nothing from this cohort routes to R3.**

Status set to `final-accepted`.

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
