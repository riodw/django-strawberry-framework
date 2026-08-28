# Build: Review round 1, cohort R1b — connection-class fast path + strictness wiring conformance

Spec reference: `docs/SPECS/spec-033-connection_optimizer-0_0_9.md` (Decisions 5 and 8; Slice-checklist Slice 2 lines 62-66 and Slice 4 lines 71-74; `### Error shapes` lines 209-212; `## Edge cases and constraints` lines 358-378; `## Test plan` Slice 2 lines 414-428 and Slice 4 lines 441-449; Definition-of-done items 5 and 7, lines 513 and 517)
Status: review-accepted

This cohort reviews shipped `HEAD`, not a Worker 2 diff. It writes no source and no spec. Every contract below is either proven present in source with symbol-qualified evidence, or reported absent / divergent with the shipped shape named. Raw `path:NN` refs appear inline beside the symbol identifiers, which `AGENTS.md` permits in a per-cycle `docs/builder/bld-*.md` scratchpad; shadow-file line numbers are never cited.

---

## Plan (Worker 1)

Not applicable: this artifact is a read-only conformance cohort dispatched by Worker 0 under the `build-033-connection_optimizer-0_0_9.md` `## Checklist` entry `R1b`. There is no `### Spec slice checklist (verbatim)` and no `### Dispatched findings checklist`; the unit's contract is the Decision-5 / Decision-8 verification list in the dispatch, reproduced as `## Contract verification` below.

---

## Build report (Worker 2)

Not applicable: no Worker 2 pass. `### Failability proofs` is likewise not applicable — this cohort introduces no boundary. Existing boundaries were audited by reading and by a temp test (see `### Temp test verification`); no production code was mutated, and Worker 3's transient-mutation carve-out was deliberately not exercised (`docs/builder/worker-3.md` `## Scope` — nothing new is being introduced, so there is nothing to re-prove, and a mutation left in a shipped tree is a live defect).

---

## Review (Worker 3)

### Environment reading (cited, not remembered)

`uv pip list` in the shared `.venv` on 2026-08-27: `django 6.1`, `strawberry-graphql 0.324.0`, `graphql-core 3.2.8`, `channels 4.3.2`; `uv run python -c "import sys; print(sys.version)"` -> `3.14.2`. The shared `.venv` is **not** the floor (`BUILD.md` `## Floor verification`: Django 5.2.16 / Python 3.10 / strawberry-graphql 0.316.0). Floor-verification scope for this cohort is `none` per the plan, so no floor venv was built.

The spec's three source-verified Strawberry claims were re-checked against the **installed** 0.324.0 and all three still hold:

- `strawberry/types/nodes.py #"info.variable_values.get(name)"` — present at line 41 of the installed package; converted selections still resolve variable references. (Spec lines 58, 103.)
- `strawberry/relay/utils.py::SliceMetadata.from_arguments` — present, same `(info, *, before, after, first, last, max_results, prefix)` signature; `start = int(after_parsed) + 1`, `end = sys.maxsize` for the unbounded tail. (Spec Decision 4 slice-arithmetic bullet, Decision 5.)
- `strawberry/relay/fields.py::ConnectionExtension.resolve` still calls `self.connection_type.resolve_connection(next_(source, info, **kwargs), info=..., before=..., after=..., first=..., last=..., max_results=...)` — the resolver's return value is fed back as the node iterable, which is the whole reason Decision 5 forbids returning a prebuilt connection. `strawberry/relay/types.py::Edge.resolve_edge` still `to_base64(cls.CURSOR_PREFIX, cursor)`, so the fast path passing only the integer offset keeps the prefix owned by Strawberry.

### Contract verification

Present and proven (symbol-qualified evidence; every one read body-against-sentence, not name-matched):

| Spec contract | Shipped evidence | Verdict |
|---|---|---|
| Resolver returns an internal wrapper, never a prebuilt connection | `connection.py::_build_relation_connection_resolver._resolve #"return _WindowedConnectionRows("` (2033-2036); `connection.py::_WindowedConnectionRows` (212-237) is a plain `@dataclass`, not a `Connection` | **present** |
| `ConnectionExtension.resolve` still calls the generated class's `resolve_connection` | `tests/test_relay_connection.py::test_fast_path_through_schema_connection_extension` executes the real `relay.connection(...)` field; installed-Strawberry `ConnectionExtension.resolve` re-verified above | **present** |
| Probe uses the precomputed `_dst_<field>_connection` from the **relation field name**, not the accessor | `connection.py::_build_relation_connection_resolver #"to_attr = _relation_connection_to_attr(relation_field_name)"` (2001); `types/finalizer.py::_synthesize_relation_connections` passes `name`, and `name = field.name` at `types/finalizer.py #"name = field.name"` (678). Pinned by `test_fast_path_fires_for_reverse_fk_without_related_name` | **present** |
| Sidecar-kwargs guard: `filter` / `order_by` present -> ignore the window, run the pipeline | `connection.py::_build_relation_connection_resolver._resolve #"no_sidecar = not has_connection_sidecar_input("` (2018-2026); the `and no_sidecar` conjunct gates the wrapper return. Pinned by `test_fast_path_ignores_window_when_sidecar_kwargs_present` | **present** |
| Annotation-presence detection; fallback when the attribute is absent or unannotated | `connection.py::_window_rows_are_annotated` (1904-1930) — but it probes `_dst_row_number` **only**, see D5-2 below | **present, narrowed** |
| Positional cursor `_dst_row_number - 1` forward for **every** window incl. the `last`-only reversed one | `connection.py::_resolve_from_window #"cursor=getattr(node, WINDOW_ROW_NUMBER) - 1"` (557); `optimizer/plans.py` line 746 defines `WINDOW_ROW_NUMBER_REVERSED = "_dst_row_number_reversed"` and it is used only at `plans.py:1107` (the annotation) and `plans.py:1116` (the plan-time `__lte` filter). The Decision-5 retraction of the reversed-cursor scheme holds against `HEAD`; the spec's stated formula is **correct** | **present** |
| `pageInfo` derivation and the forward page-flag comparisons | `connection.py::_resolve_from_window #"has_previous_page=keyset_seek_supplied or first_rn > 1"` (595) and the `has_next_page` ladder (577-589) — the forward comparison survives as one of four branches, see D5-4 | **present, forked** |
| `totalCount` read from `_dst_total_count`, branching **before** `_guard_total_count_countable` / `.count()` | `DjangoConnection.resolve_connection` (1216-1299) calls `_consume_window` at 1285; `_guard_total_count_countable` (1405-1422) is reachable only through `_consume_fallback` -> `_attach_count_sync` / `_attach_count_async`. Pinned by `test_fast_path_total_count_marker_bypasses_non_queryset_guard` | **present** |
| Outer `totalCount` predicate stays direct-children-scoped | `connection.py::_total_count_requested` (1146-1173) delegates to `optimizer/selections.py::connection_total_count_selected`, whose docstring and behavior recurse only through fragment wrappers. Pinned by `test_outer_total_count_predicate_ignores_nested_total_count` | **present** |
| `SDL identity / first+last guard / totalCount member shape unchanged` | `_resolve_from_window` and `_empty_page_connection` both construct `cls(...)` where `cls` is the generated class; `_guard_first_and_last` (1117-1132) runs at 1268 before any window work | **present** |
| Decision 8 three-condition guard, `OptimizerError` under `"raise"` / logged warning under `"warn"` | `types/resolvers.py::_check_n1` (218-327): strictness gate at 293-296, planned-key short-circuit at 308-309, `kind == "connection_to_attr"` `to_attr` probe at 310-313, raise/warn at 322-326. Condition 1 diverges — see D8-1 | **present, conditions restated** |
| Message names the **relation** field (`books`), not `books_connection` | `types/resolvers.py::_check_n1 #"raise OptimizerError(f\"Unplanned N+1: {field_name}{suffix}\")"` (324) with `field_name` threaded as `relation_field_name` from `connection.py:2052`. Pinned by `test_strictness_raise_unplanned_nested_connection` asserting `"Unplanned N+1: books"` | **present** |
| Parameterization of `_check_n1` rather than a duplicate implementation in `connection.py` | `connection.py` line 97 imports `_check_n1`; a tree-wide grep for `_check_n1` finds one definition (`types/resolvers.py:218`) and four production call sites (`resolvers.py:528`, `:587`, `:692`, `connection.py:2049`). No second checker | **present** |
| Fallback-reason text | `connection.py::_build_relation_connection_resolver._resolve #"not window-planned: selection carries filter/orderBy; resolving per-parent"` (2044-2048), appended by `_check_n1` at 322. Pinned by `test_sidecar_fallback_is_flagged_with_reason` | **present** |
| Union publish so a nested pipeline cannot clobber the parent's planned set / FK-id elisions | `optimizer/extension.py::DjangoOptimizerExtension._publish_plan_to_context` (1277-1315) + `._stash_union` (1317-1341); `DST_OPTIMIZER_PLAN` deliberately not unioned (1296). Pinned by `tests/optimizer/test_extension.py::test_publish_plan_to_context_unions_parent_and_nested_sentinel_sets` and `tests/test_relay_connection.py::test_nested_fallback_does_not_clobber_fk_id_elisions` | **present** |

**Nothing in Decision 5 or Decision 8 was planned and never implemented.** The two Slice-2 contracts the spec still states that shipped code does *not* deliver (per-parent fallback for ambiguous empty windows; the wrapper carrying `offset`/`limit`/`reverse`) are cases where the **spec** is wrong about what shipped, not cases where the build skipped work — see D5-1 and D5-3.

### What actually happens today for the four named shapes

Measured by reading the shipped control flow end-to-end and confirmed by the named tests, which all pass at `HEAD`.

| Shape | Today's behavior | Path |
|---|---|---|
| `first: 0` on a parent **with** children | Fast-pathed from a **marker row**. `edges: []`, `hasNextPage: true`, `hasPreviousPage: false`, `totalCount` = the true count. No per-parent query. | `window_range_plan` -> `add_marker_rows=True`, `fetch_mode` -> `COUNTED` (`utils/connections.py::WindowRangePlan.fetch_mode #"if total_selected or self.limit == 0"`, 351); `split_window_rows` returns `([], False)` for `limit == 0`; `_resolve_from_window` marker-only branch (447-489) serves `has_next_page = total > offset`. Pinned by `test_fast_path_ambiguous_empty_served_from_marker_row[first: 0]` and live by `test_nested_connection_first_zero_empty_page_live` |
| Overshot `after:` on a parent **with** children | Fast-pathed from a marker row. `edges: []`, `hasPreviousPage: true` (`offset > 0`), `hasNextPage: false`, `totalCount` = the true count when counted; when the window is count-free (`PROBED` / edges-only) the marker proves `total <= offset` and the empty page is served with `hasNextPage: false` and no count. No per-parent query. | `_resolve_from_window` 447-489; the count-free arm at 459-477. Pinned by `test_fast_path_ambiguous_empty_served_from_marker_row[after: …]` |
| Childless parent (any forward shape) | Fast-pathed. `edges: []`, `totalCount: 0`, `hasNextPage: false`, `hasPreviousPage = offset > 0`. An empty `to_attr` list now **proves** no children, because a parent with children would have kept its marker row or its probe sentinel. | `_resolve_from_window #"if not rows:"` (412-432) -> `_empty_page_connection` (179-208). Pinned by `test_fast_path_genuinely_empty_parent_serves_zero` and `test_fast_path_zero_children_parent_serves_under_ambiguous_shapes` |
| `last: 0` | **Fully unplanned.** No window prefetch is emitted at all, no resolver key is recorded, so the per-parent pipeline runs and reproduces upstream's `edges[-0:]` serve-all quirk (all edges), and strictness **sees** the access. | `optimizer/nested_planner.py #"fallbacks.append((resp_key, \"last: 0\"))"` (998-999); `connection.py::_resolve_from_window #"if reverse and limit == 0:"` (413-417) survives as the defensive tail for direct callers. Pinned by `test_fast_path_last_zero_quirk_parity_via_fallback` (asserts 3 queries and `not any("_dst_row_number" in sql)`), `test_fast_path_last_zero_visible_under_strictness`, and the async mirror `test_async_fast_path_last_zero_falls_back_for_total_count_and_pageinfo` |

### High:

None. No spec contract in Decision 5 or Decision 8 is undelivered, no correctness bug was found, and every divergence below is a **spec-text** defect.

### Medium:

#### M1 (Escalated) — the `connection_to_attr` strictness probe answers "attribute present", not "the window was consumed"

`django_strawberry_framework/types/resolvers.py::_check_n1 #"lazy = getattr(root, to_attr, None) is None if isinstance(to_attr, str) else True"` (310-313)

```python
    if kind == "connection_to_attr":
        # The windowed page already landed under ``to_attr`` when present;
        # only an absent ``to_attr`` means the per-parent pipeline will query.
        lazy = getattr(root, to_attr, None) is None if isinstance(to_attr, str) else True
```

The resolver reaches `_check_n1` only on the branch where it has **already decided not to consume** whatever sits under `to_attr` (`connection.py::_build_relation_connection_resolver._resolve` 2022-2057). Three independent conditions can produce that decision — the value is not a `list`, its rows carry no `_dst_row_number`, or the resolver's own `filter` / `order_by` kwargs are present — and in all three the per-parent pipeline then runs and genuinely queries. The probe re-derives a *different* answer from the same attribute, and reads "present" as "served", so the B3 contract stays silent on a real per-parent access. This is `BUILD.md` `### Fail-open shapes`'s shape in its "guard the ANSWER, not one spelling of the input" form: the answer to guard is *did this resolver consume the window*, which the resolver already computed one branch earlier and then threw away.

Demonstrated mechanically, not argued — `docs/builder/temp-tests/r1b/test_probe_answers_presence_not_consumption.py`, 3 rows, all passing: the control (`to_attr` absent) raises `OptimizerError`, while both refused-window shapes are silent under `strictness="raise"` with the key absent from the planned set.

Reachability is narrow, which is why this is Medium and not High: the unannotated-rows shape requires a consumer to write the package-reserved `_dst_` namespace (which the spec's `## Edge cases and constraints` consumer-cooperation bullet, line 371, declares explicitly unsupported and unguarded), and the sidecar shape requires the planner/resolver desync the sidecar guard exists as a belt against. No visibility or data-isolation boundary is involved — the served rows are correct in every case; only the diagnostic is silent.

**Why this is escalated rather than dispatched to a builder.** The shipped code implements the spec's own words: Decision 8 (line 308) and the Slice-4 checklist (line 72) both state the third condition as "the fast-path `to_attr` is absent on `root`". Changing the code to thread the resolver's already-computed answer is therefore a **contract** change to Decision 8's stated three-condition guard, which `docs/builder/worker-3.md` `### The existence challenge` and `BUILD.md` `### Contract-level findings are escalated as maintainer decisions before dispatch` put outside a worker's call. Resolution paths for Worker 1 / the maintainer:

1. **Thread the answer.** `_resolve` already knows whether it returned a wrapper; pass that boolean (or `to_attr=None` when it refused) into `_check_n1`, and restate Decision 8's third condition as "the resolver did not consume a window for this response key". Smallest change, closes all three shapes, and the existing `to_attr` probe stays for the ordinary absent case. New rows required: the two in the temp test, promoted to `tests/test_relay_connection.py` next to `test_strictness_silent_when_window_served` (the row that currently pins the *intended* silence).
2. **Accept as designed and say so in the spec.** Record in Decision 8 that the probe is deliberately attribute-shaped and that a consumer writing the reserved namespace can silence strictness — consistent with the existing "explicitly unsupported, documented, not guarded" posture for that namespace. Costs nothing in code; costs the guarantee that `"raise"` cannot be silenced by a `_dst_`-namespace write.
3. **Narrow to the sidecar half only.** Pass `to_attr=None` when `no_sidecar` is false, leaving the unannotated-rows shape as documented-unsupported. Half a fix; not recommended, since it leaves two of the three shapes open while looking closed.

Recommend path 1. This finding is Medium and escalated; it does **not** hold the cohort at `revision-needed` (`docs/builder/worker-3.md` `### Acceptance gate`, the escalation clause).

### Low:

#### L1 — a test docstring still describes the retired two-annotation probe

`tests/test_relay_connection.py::test_fallback_when_annotations_missing #"without ``_dst_row_number`` / ``_dst_total_count``"` (2205-2210). The shipped probe is row-number-only by design (`connection.py::_window_rows_are_annotated`, whose own docstring states "``_dst_total_count`` is NOT probed"). The test **body** is correct (its planted list carries neither), so this is prose only. Not fixable in this cohort (no `.py` edits); routed under `### Notes for Worker 1`.

#### L2 — two strictness test docstrings attribute the silence to the wrong mechanism

`tests/test_relay_connection.py::test_strictness_silent_when_off #"no sentinel is stashed (the publish gates on ``strictness != \"off\"``)"` (2570-2572) and `::test_strictness_silent_no_optimizer #"``DST_OPTIMIZER_PLANNED`` is never stashed, so the prelude returns before any probe"` (2590-2592). Since `841e56d6` the prelude returns because `_strictness_for(context)` answers `"off"` (`types/resolvers.py::_strictness_for`, 187-202), reading the `_active_strictness` `ContextVar` first; an absent `DST_OPTIMIZER_PLANNED` stash is no longer what disarms the check — that was the exact fail-open `841e56d6` closed. Both behavioral pins are still right; only the stated mechanism is stale.

#### L3 — `_resolve_from_window` is the file's dominant control-flow hotspot

`connection.py::_resolve_from_window` (277-599): 323 lines, 26 branch nodes per the static helper — more than twice the next entry (`_resolve_keyset_connection`, 168 lines / 20 nodes). It is not accidental complexity: the branch fan-out is the cross-product of four `FetchMode` shapes, the marker/probe split, and the keyset fork, and the shape predicates already delegate to `utils/connections.py` (`probe_shape`, `constant_false_shape`, `split_window_rows`, `window_range_plan`) rather than being re-spelled. Recorded rather than filed as a defect, per `BUILD.md` `### Reading the overview` ("apply Medium-tier complexity attention to every entry"). Worth naming for a future pass: the keyset legs (`keyset_seek_supplied` computation at 400-404, the keyset edge branch at 537-552, the two keyset flag forks at 579-587 and 595) are separable from the offset legs and would halve the branch count of each half; this is a repair-cohort suggestion, not a finding.

### DRY findings

- **The 5-exception coercion tuple is repeated 15 times across 2 files.** Measured, not estimated: an exact-shape regex over every `.py` under `django_strawberry_framework/` counts `except (ValueError, TypeError, AttributeError, KeyError, IndexError,)` (either member order) **11x in `connection.py`** and **4x in `auth/mutations.py`**, 15 occurrences total, zero elsewhere. `except` accepts a tuple *name*, so the readable consolidation exists: one module-level `_COERCION_ERRORS` constant (or a shared one in `utils/`, given the cross-file spread). `auth/mutations.py` is outside every R1 cohort's scope, so this is an integration-pass / repair-cohort item, escalated below rather than actioned.
- **Repeated string literals, `connection.py`** (static helper, `## Repeated string literals`): `total_count` x3, `_dst_node_type` x2, `is_relation` x2. `_dst_node_type` is a set/get pair across two symbols (`_generate_connection_class._populate #"namespace[\"_dst_node_type\"] = target_type"` 1352, read at `_keyset_connection_context #"getattr(cls, \"_dst_node_type\", None)"` 156) — a named constant would make the pairing greppable, matching how `_TOTAL_COUNT_ATTR` (137) already handles the same pattern for the count attribute. Low value, recorded for the integration pass's cross-file literal comparison.
- **Repeated string literals, `types/resolvers.py`**: `__dict__` x2 only. Nothing cross-file.
- **No duplicated logic found on either Decision's surface.** The two contracts most at risk of a near-copy are both single-sited and were checked directly: there is exactly one `_check_n1` implementation (Decision 8's explicit non-duplication requirement), and the plan-time / resolve-time window derivation shares one source (`utils/connections.py::derive_connection_window_bounds` and `::window_range_plan`, imported by both `optimizer/nested_planner.py` and `connection.py`), which is the cursor-parity invariant's structural guarantee. `connection.py::_finalize_queryset` (1558-1642) reads its order through the shared `optimizer/plans.py::effective_connection_order`, so the resolve-time order cannot drift from the planned window's.
- **Existence challenge — not raised.** No new registry, token, fingerprint, or single-caller indirection appears on this surface. The one candidate, `_WindowedConnectionRows`, earns its existence: it is the type-discriminated handoff `ConnectionExtension`'s node-iterable contract requires, and the spec's Decision-5 rationale records the alternative (a context-stash handshake) as rejected for exactly the reason the dataclass avoids.

### Static helper invocations

Both required by `BUILD.md` `### When to run the helper during build` (a `types/` file, and `connection.py` far past the 150-line threshold), both run from the repo root with the mandatory `--output-dir docs/shadow`; no file in this cohort's scope was skipped:

```shell
uv run python scripts/review_inspect.py django_strawberry_framework/connection.py --output-dir docs/shadow
uv run python scripts/review_inspect.py django_strawberry_framework/types/resolvers.py --output-dir docs/shadow
```

Shadow output was read for control flow, repeated literals, markers, and imports only; every citation in this artifact is to the original source line, never to a shadow line. The four overview sections are walked in `### Django / ORM markers walked`, `### Imports (cross-folder direction)`, the `### DRY findings` literal bullets, and L3 (control-flow hotspots).

### Django / ORM markers walked

Ten entries in the `connection.py` overview; each justified, none produced a finding:

- `connection.py:801` / `:803` (`current._meta.pk.name`, `current._meta.get_field(...)`) — `_resolve_order_path_field`, read-only meta traversal resolving a keyset cursor column's terminal field. Post-ship keyset surface (`51421e54`); no query, no mutation.
- `:821` / `:822` — `models.QuerySet` type annotations on `_keyset_order_state`. Annotation only.
- `:992` (`isinstance(nodes, models.QuerySet)`) — the keyset slicer's source guard; rejects a non-queryset before slicing. Fail-closed.
- `:1416` — `_guard_total_count_countable`, the spec-030 Decision 7 `totalCount`-over-non-queryset guard. **Load-bearing for Decision 5**: verified above that `_consume_window` branches before it can be reached.
- `:1506` — `_guard_sidecar_input_against_non_queryset`, the sidecar-over-non-queryset guard the spec's `### Error shapes` inherits.
- `:1515` — `_guard_source_not_pre_sliced` signature; rejects an already-sliced queryset (`11da7de8`).
- `:1558` — `_finalize_queryset` signature.
- `:1618` (`tuple(target_model._meta.ordering)`) — reads the model's declared ordering to decide whether an explicit `order_by` call is needed; the *effective* order itself comes from the shared `effective_connection_order` two statements earlier, so the cursor-parity invariant is not re-derived here.

### Imports (cross-folder direction)

`connection.py` imports from `optimizer/` (`extension`, `nested_planner`, `plans`, `selections`), `types/` (`resolvers`), `utils/` (`connections`, `querysets`, `relations`, `typing`), plus `keyset`, `list_field`, `registry`, `resource_policy`, `exceptions`. Nothing under `optimizer/` imports `connection.py` back — verified: `optimizer/walker.py` reaches the `to_attr` builders through `optimizer/nested_planner.py` (`walker.py:70-71`), never through `connection.py`, which is the no-cycle rule Decision 11 states. The `_ends_in_unique_column` re-export at `connection.py:129` points the other way (`connection.py` imports the canonical `optimizer/plans.py::ends_in_unique_column` and aliases it under the old private name for the spec-030 test pins) — the direction Decision 11 prescribes, held.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` produces **no output**: `__all__` and the re-export list are unchanged by this cohort, which writes no source. Consistent with the spec's `## User-facing API` line 159 ("This card adds no public symbol, no `Meta` key, and no constructor argument") and DoD item 5's implicit no-new-exports posture.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces. (`docs/README.md` disagreements with the spec are **recorded** under `### Notes for Worker 1` per the plan's scope fence, never fixed here.)

### Test verification

Focused runs, no `--cov*` flags:

- `uv run pytest tests/test_relay_connection.py tests/test_connection.py tests/utils/test_connections.py --no-cov -q` -> **229 passed**.
- `uv run pytest tests/optimizer/test_extension.py tests/types/test_resolvers.py --no-cov -q` -> **214 passed**.

**Named-test census for Slices 2 and 4** (mechanical: `grep -rl "def <name>(" tests/ examples/` per name). 22 of the 24 names the Test plan gives are present; the 2 absent are exactly the two whose contract was retired:

- **Absent:** `test_fast_path_first_zero_falls_back_for_total_count_and_pageinfo`, `test_fast_path_after_end_falls_back_for_total_count_and_pageinfo` (spec line 424). Their contract — per-parent fallback for the ambiguous-empty shapes — no longer exists (D5-1). The behavior that replaced it **is** pinned, by `test_fast_path_ambiguous_empty_served_from_marker_row` (parametrized over `first: 0` and an overshot `after:`, `tests/test_relay_connection.py:1997`) and `test_fast_path_zero_children_parent_serves_under_ambiguous_shapes` (`:2123`). So this is a stale Test-plan entry, not a coverage gap.
- **Present, bodies read against their spec sentences:** all 13 remaining Slice-2 names and all 9 Slice-4 names. Nothing was accepted on its name.

**Query-shape assertions pin the load-bearing property** (`BUILD.md` `### Query-shape tests must pin the load-bearing property`):

- `test_fast_path_single_query` uses an **absolute** `django_assert_num_queries(2)` over a **4-parent** fixture, so a per-parent pipeline (1 + 4 = 5) is distinguishable, and the query carries no sidecar argument that could silently route it to the fallback. Single cardinality, but the two-cardinality pin exists live: `examples/fakeshop/test_query/test_library_api.py::test_nested_books_connection_fixed_query_count` runs the identical query at **3 and 10** genres and asserts both `three_count == ten_count` **and** `three_count == 2`. Together these satisfy the rule.
- `test_fast_path_last_zero_quirk_parity_via_fallback` goes further than a count: it asserts `not any("_dst_row_number" in entry["sql"] for entry in captured)` — the path itself, not its observability.
- `test_fast_path_ambiguous_empty_served_from_marker_row` and `test_fast_path_zero_children_parent_serves_under_ambiguous_shapes` each assert an absolute `2` **and** wire-equality against an optimizer-off execution of the same document, which is the parity half the spec's `## Edge cases` last bullet demands ("the fallback tests assert wire parity, not just non-error").

### What looks solid

- **The annotation probe is fail-closed by construction.** `_window_rows_are_annotated` (1904-1930) wraps its `all(hasattr(...))` in `except (TypeError, ValueError, AttributeError, KeyError, IndexError): return False`, and `False` means "not a window, run the pipeline". An exception during the check converts to *reject*, never to *consume* — the correct direction for a probe that gates a visibility-bypassing path. Contrast with the fail-open direction M1 documents on the strictness side.
- **The workstream-B drift guard falls back rather than serving a wrong flag.** `_resolve_from_window` 503-535 returns `None` (-> per-parent recovery) when a count-less page's selection needs a count-derived answer, and the check runs **before any edge is built** so the fallback discards no work. The `want_count` clause is exempt from no exemption; the `hasNextPage` exemptions delegate to the shared `range_plan.probe_shape` / `constant_false_shape` predicates rather than re-spelling the shapes, so plan-time and resolve-time cannot drift into disagreement silently.
- **The `has_previous_page` arithmetic is computed before the data is consulted** (`_empty_page_connection #"has_previous_page=offset > 0 if has_previous_page is None else has_previous_page"`, 204), which is what makes a childless parent with an overshot `after:` report `hasPreviousPage: true` exactly like `ListConnection`'s `start > 0`. That is the kind of parity detail a marker-row rewrite would normally lose, and it is pinned by wire-equality rather than by a hand-written expectation.
- **`_check_n1`'s connection probe uses `is None`, not truthiness.** `getattr(root, to_attr, None) is None` distinguishes "absent" from "an empty served window", so a genuinely childless parent whose window landed `[]` is correctly silent. A truthiness test there would have false-flagged every empty page under `"raise"`.
- **The Decision-8 non-duplication requirement is structurally held.** One `_check_n1` definition, four production call sites, and the connection kind is a parameter rather than a branch in `connection.py`.
- **The cursor-parity invariant has one source on both legs.** Plan-time and resolve-time both derive bounds through `utils/connections.py::derive_connection_window_bounds` (or its keyset twin) and order through `optimizer/plans.py::effective_connection_order`. The spec argues this invariant as a *correctness prerequisite*; the shipped shape is stronger than the spec's own description of it (which still says the resolver reads slice metadata off the wrapper — D5-3).

### Temp test verification

- `docs/builder/temp-tests/r1b/test_probe_answers_presence_not_consumption.py` — 3 rows, all passing, demonstrating M1: the control row proves the boundary exists (absent `to_attr` -> `OptimizerError`), and two rows prove it is silent for windows the resolver already refused. Run: `uv run pytest docs/builder/temp-tests/r1b/test_probe_answers_presence_not_consumption.py --no-cov -q` -> 3 passed.
- **Disposition:** kept in the gitignored temp-test directory, not promoted, because promotion depends on which M1 resolution path the maintainer picks. Under path 1 the two demonstration rows become the pins for the corrected probe (inverted: they must then raise) and belong in `tests/test_relay_connection.py` beside `test_strictness_silent_when_window_served`. Under path 2 they document accepted behavior and should be dropped rather than promoted, since a row asserting silence would manufacture confidence in the shape the spec would then be admitting. The finding does not rest on the temp test alone: M1 is fully readable from `types/resolvers.py:310-313` against `connection.py:2022-2057`.
- No production code was mutated at any point in this pass.

### Notes for Worker 1 (spec reconciliation)

Every item below is a **spec-text** divergence unless marked otherwise. Class per the plan's `## Two divergence classes`: **build-time** = the build shipped something else; **post-ship** = a later commit changed this card's surface. Post-ship items name the commit; the strategy seam has no owning spec, so commits are identified by hash + the "idea #N" label the commit itself uses, never by an invented card id.

---

#### D5-1 — Ambiguous empty windows are served from MARKER ROWS, not fallen back per parent. **Post-ship**, commit `57cbd32a` (2026-07-07, "Pluggable nested-connection fetch strategies + Postgres lateral backend"), whose message states the change: *"Marker-row windows: keep each partition's row 1 for the ambiguous-empty shapes (first:0, overshot after:) so a childless parent and an empty page stay distinguishable in one query; 2+2N queries collapse to 2."*

The shipped contract: `first: 0` and an overshot `after:` are **planned and fast-pathed**; the window keeps each partition's row 1 as a marker; an empty rows list now *proves* the parent has no children. `last: 0` became **fully unplanned** in the same commit and is the one remaining always-fallback shape. Exact per-shape behavior is tabulated in `### What actually happens today for the four named shapes` above; the shared predicate is `utils/connections.py::is_ambiguous_empty_window` (179-199) and the consuming branch is `connection.py::_resolve_from_window` (412-489).

**Every spec home (9 prose sites + 1 Test-plan entry + 1 table cell), all stating the retired contract:**

| Spec line | Site | What it says that is now false |
|---|---|---|
| 5 | `Status:` line, Slice-2 clause | "with a per-parent fallback for ambiguous empty windows" |
| 26 | `## Key glossary references`, `Meta.connection` bullet | "serves zero only for unambiguous empty windows (`offset == 0`, `limit > 0`), and falls back per parent for ambiguous empty windows (`first: 0`, overshot `after:`)" |
| 64 | `## Slice checklist`, Slice 2 sub-bullet 2 | "or an **ambiguous empty wrapper** (`limit == 0` or `offset > 0`) -> the shipped per-parent pipeline runs for that parent" |
| 113 | `## Goals` item 2 | "with per-parent fallback for ambiguous empty windows (`first: 0`, overshot `after:`)" |
| 272 | Decision 5, empty-wrapper bullet | the whole bullet: "Empty wrappers with `limit == 0` … or `offset > 0` … are ambiguous and fall back to the per-parent pipeline for that parent" |
| 347 | `## Implementation plan` table, Slice-2 "New tests" cell | "`first: 0` / overshot `after:` ambiguous-empty fallback parity" |
| 364 | `## Edge cases and constraints`, "`first: 0` and overshot `after:`" bullet | "Empty wrappers with `limit == 0` or `offset > 0` fall back per parent" |
| 424 | `## Test plan` Slice 2 | names the two tests that do not exist (see the census above) |
| 458 | `## Test plan` Slice 5 | `test_nested_connection_first_zero_empty_page_live`'s parenthetical "(`first: 0`, fast-path -> per-parent fallback, Decision 5)". **The test exists and passes**; only the parenthetical is wrong — it is served from the marker |
| 513 | DoD item 5 | "and per-parent fallback for ambiguous empty windows" |
| 365 | `## Edge cases`, "Parents with no related rows" bullet | **still true** — do not change it; `totalCount 0`, both flags `False`, no fallback |

`last: 0` needs a **new** statement somewhere in Decision 5 / `## Edge cases`: it has no home in the current spec at all (the `last`-only bullet at line 366 covers backward pagination generally, not the zero case), yet it is now the only shape that always falls back, it is deliberately left unplanned so strictness can see it, and three tests pin it.

---

#### D5-2 — The annotation probe reads `_dst_row_number` ONLY; `_dst_total_count` is annotated conditionally. **Post-ship**, three converging commits.

`connection.py::_window_rows_are_annotated` (1904-1930) probes `hasattr(row, WINDOW_ROW_NUMBER)` and explicitly does **not** probe `_dst_total_count`. Three separate later changes make the count's absence normal rather than exceptional:

1. `57cbd32a` (2026-07-07) — conditional `_dst_total_count`: *"annotate the per-partition Count(1) OVER only when the selection can observe it (totalCount / pageInfo.hasNextPage) or the window shape needs it"*.
2. `744aea93` (2026-07-09, "count-free hasNextPage via an n+1 overfetch probe") — the common `first: N` page carries **no** count at all, by design.
3. `deeb53b4` (2026-07-17, "single-parent fast path") — `optimizer/single_parent_fetch.py` synthesizes `_dst_row_number` **in Python** (`#"setattr(row, WINDOW_ROW_NUMBER, index + 1)"`, 286) and never sets `_dst_total_count` (verified: the module imports only `WINDOW_ROW_NUMBER` from `plans.py`, line 63, and gates itself on `not request.with_total_count`, line 132). A row-number-only probe is what makes that strategy consumable at all.

**Spec homes:** line 63 (Slice-2 checklist sub-bullet 1, "a list whose members carry `_dst_row_number` / `_dst_total_count`") and line 263 (Decision 5, second bullet, same phrasing). Line 390 (`## Test plan` Slice 1, `test_nested_connection_planned_as_windowed_prefetch`) and line 509 (DoD item 4) state the same pair on the **plan** side — those two are R1a's (Decision 4) to confirm, flagged here only so the pair is corrected consistently in one pass rather than half-corrected.

---

#### D5-3 — The wrapper carries no slice metadata; `resolve_connection` re-derives it. **Build-time.**

Spec line 263 says the resolver wraps the rows "in an internal `_WindowedConnectionRows` marker that stores the rows plus the resolved `offset`, `limit`, and `reverse` slice metadata used by the planner", and line 270 says "`pageInfo` is derived from the edge rows and **the wrapper's slice metadata**". Shipped `connection.py::_WindowedConnectionRows` (212-237) has exactly two fields: `rows: list[Any]` and `fallback: Callable[[], Any]`.

This was never implementable as the spec states it, and the shipped docstring says why (`_WindowedConnectionRows`, 226-229): *"The resolver lacks the pagination arguments needed to classify the rows itself (Strawberry's `ConnectionExtension.resolve` consumes `first` / `last` / `before` / `after` and forwards them only to `resolve_connection`), so all window classification happens there."* Re-verified against installed Strawberry 0.324.0 above. The bounds are derived in `connection.py::_consume_window` (633-689) through the shared `utils/connections.py::derive_connection_window_bounds`, which is the *stronger* cursor-parity guarantee — the resolve-time window is computed by the same helper the walker planned with, rather than trusted from a value the resolver stashed. The `fallback` field, which the spec never mentions, is the second half of the divergence: it exists because `resolve_connection` cannot rebuild the per-parent relation manager the resolver holds.

**Spec homes:** lines 263 and 270. Decision 5's rejected alternative "A context-stash handshake" in the rationale (`### Alternatives considered (and rejected)`) is adjacent but distinct and stays correct as written.

---

#### D5-4 — `pageInfo` page flags are now a four-way fork, not one forward comparison. **Post-ship**, `744aea93` + `41008e4c` + `51421e54`.

Spec line 270: "the page flags are the forward comparisons against `_dst_total_count` for **all** windows (`has_previous_page` when the first row is past row 1; `has_next_page` when the last row is short of the total)". Shipped `connection.py::_resolve_from_window` (577-596):

- `has_next_page = probe_row_seen` on the count-free n+1 probe shape (`744aea93`, 2026-07-09);
- `has_next_page = row_number < seek_total` in the value domain for a counted keyset-seek page (`51421e54`, 2026-07-10, "idea #3 / BACKLOG-39");
- `has_next_page = False` as a constant for the `CONSTANT_FALSE` shapes — an unbounded forward page and the reversed `last`-only page (`41008e4c`, 2026-07-17, "FetchMode axis");
- `has_next_page = row_number < total` — the spec's comparison, now one branch of four;
- `has_previous_page = keyset_seek_supplied or first_rn > 1` — the spec's comparison plus the keyset "a cursor was supplied" rule.

The spec's *claim about the reversed `last`-only window* ("these land on the pipeline's values … since its row numbers are forward") is still true and still pinned by `test_fast_path_wire_parity_last_only`; it just arrives via the `CONSTANT_FALSE` branch now. **Spec homes:** line 270 (Decision 5) and line 366 (`## Edge cases`, the `last`-only bullet, which says "the page flags are the same forward comparisons as every other window").

---

#### D5-5 — There is one `resolve_connection`, not two. **Post-ship**, commit `de2601e9` (2026-08-17, "single-site the connection dispatch and the recognized-fetch rebind").

The spec describes two entry points at lines 64, 267, and 271 ("`DjangoConnection.resolve_connection` **and** the generated `<TypeName>Connection.resolve_connection` path"; "the generated total-count connection path must branch before `_guard_total_count_countable`"). Shipped: `DjangoConnection.resolve_connection` (1216-1299) is the only override, and the count opt-in is the `ClassVar` `_resolves_total_count` (1213) that `_build_total_count_connection._populate` sets (1396). The commit message states the retirement of both the duplicated override and the intermediate `_resolve_connection_fast_path` helper that `6912ca92` (2026-06-13) had introduced to share the guard-plus-head between them: *"That leaves `_resolve_connection_fast_path` with a single caller, so inline it into `resolve_connection`."*

So the interim shape Worker 0's dispatch describes (one shared head, `want_count` evaluated after the guard) is itself now historical: `want_count` is a short-circuiting `and` in the `_consume_window` argument list (1297). The contract the spec cares about — the marker is treated as an annotated optimized source and never reaches `_guard_total_count_countable` — **holds**, and is pinned. Only the two-paths phrasing is stale. **Spec homes:** lines 64, 267, 271, and line 105 (`## Current state`, "the generated `<TypeName>Connection`'s `resolve_connection` counts the post-filter pre-slice queryset").

---

#### D5-6 — Divergent aliases are window-planned per response key; the resolver probes a per-key `to_attr` first. **Post-ship**, commit `9580e84e` (2026-07-10, "perf(optimizer): batch divergent-alias connections per response key (**idea #2**)").

Resolver-side shape (mine): `connection.py::_build_relation_connection_resolver._resolve` (2005-2016) probes `_relation_connection_to_attr_for_key(relation_field_name, info.path.key)` — the `_dst_<field>$<key>_connection` attr — **first**, then falls back to the shared `_dst_<field>_connection`, and threads whichever attr held rows into the `_check_n1` probe as `probe_attr`. The naming scheme (`$` escaping, no `__`) is the commit's, for the reason it gives: Django splits `prefetch_to` on `LOOKUP_SEP`.

The **plan-side** half of this — Decision 6 item 2's "Aliased duplicates with divergent pagination arguments … One `to_attr` cannot serve two windows; per-alias windows are a follow-up" (spec line 284), the Slice-1 checklist fallback bullet (line 60), the `## Edge cases` bullet (line 361), the DoD item 4 fallback list (line 509), the `## Test plan` package-only rationale (line 384), the `## Out of scope` per-alias-windows entry (line 491), and the Doc-updates glossary instruction (line 472) — **belongs to R1a (Decision 6)**. Stated here explicitly so Worker 1 does not receive two half-findings: R1b owns only the resolver-side probe order, R1a owns the fallback matrix. Both must land in one pass, because the spec currently lists divergent aliases as an unplanned fallback in **seven** places while the resolver has a dedicated per-key branch for them, and `tests/test_relay_connection.py::test_divergent_aliases_one_window_query_per_alias` pins one window query per alias at a fixed count.

---

#### D5-7 — Keyset (`Meta.cursor_field`) cursors ship and intersect the fast path directly. The spec lists them as a **Non-goal**. **Post-ship**, commit `51421e54` (2026-07-10, "feat(relay): keyset value-encoded cursors via `Meta.cursor_field` (**idea #3** / BACKLOG-39)").

Spec line 125 (`## Non-goals`): "**Keyset / column-anchored cursors.** `Meta.cursor_field` and positional-stability-under-mutation guarantees stay in `BACKLOG.md` item 39; the window math below inherits Strawberry's offset-cursor semantics verbatim." Spec line 492 (`## Out of scope`) repeats it. Both are false at `HEAD`, and the intersection is not incidental — it forks Decision 5's own mechanism at five sites in the file this cohort owns:

- `connection.py::_keyset_connection_context` (140-161) resolves keyset mode off the generated class per connection;
- `connection.py::_consume_window #"derive_bounds = ("` (645-649) **forks the bounds derivation at the cursor vocabulary** — `derive_keyset_window_bounds` instead of `derive_connection_window_bounds`, because a value cursor cannot pass through `SliceMetadata`;
- `connection.py::_resolve_from_window` takes `keyset_state` / `keyset_after` parameters and builds edges **directly** with `encode_keyset_cursor` rather than through `resolve_edge` (537-552), which is a direct exception to Decision 5's "the cursor prefix stays owned by Strawberry's edge type" (line 269);
- the counted-keyset marker shape and its own drift guard (400-411, 478-489, 525-535, 579-587), keyed on `WINDOW_KEYSET_SEEK_COUNT` (`_dst_keyset_seek_count`, `optimizer/plans.py:756`) — an annotation family the spec does not know exists;
- `connection.py::_consume_fallback` (731-740) routes a non-window keyset source to `_resolve_keyset_connection` rather than to `ListConnection`.

`connection.py::_finalize_queryset` (1583-1605) also now selects the deterministic order through `effective_connection_order(cursor_field, explicit, target_model)`, so a keyset target's declared cursor field wins over the pk-append rule the spec's `## Current state` line 105 describes. Related fix: `04cc9214` (2026-07-15, "preserve `last: 0` serve-all parity with offset") extended the `last: 0` quirk to the keyset slicer.

`docs/README.md` line 106 states the consumer-facing version of this and **disagrees with the spec directly**: "A keyset-mode nested connection always orders by its target type's declared `Meta.cursor_field`; supplying that field's `orderBy:` sidecar deliberately falls back to the per-parent pipeline rather than overriding the cursor order." Between the two, `docs/README.md` is right and the spec is wrong. The spec is fenced to spec + `.py` this cycle, so `docs/README.md` needs no edit; recording the agreement direction so a later reader does not "fix" the README toward the stale Non-goal.

---

#### D5-8 — A third fetch strategy and a runtime single-parent fast path feed the same `to_attr`. **Post-ship**, `57cbd32a` (strategy seam + Postgres lateral) and `deeb53b4` (single-parent fast path).

Decision 5's wrapper-absent paragraph (line 275) enumerates the causes of degradation — "no optimizer installed, strictness off, a fallback shape from Decision 6, a Decision 4 DISTINCT-target relation left unplanned, a consumer's own prefetch" — and the list is now incomplete in both directions:

- **New always-fallback shapes** the list omits: `last: 0` (`optimizer/nested_planner.py:998`), `after` + `last` and an inverted `after`/`before` interval (`utils/connections.py::derive_connection_window_bounds` raising `UnwindowableConnection`, 635-642), every backward keyset shape (`::derive_keyset_window_bounds`, 738-740), and the same-response-key argument conflict `9580e84e` added.
- **New window producers** the spec's annotation contract never contemplated: `optimizer/lateral_fetch.py` (Postgres `CROSS JOIN LATERAL`) and `optimizer/single_parent_fetch.py` (a plain `WHERE fk = x ORDER BY … LIMIT n` whose row numbers are synthesized in Python). Both land rows under the same `to_attr` and are consumed by the same `_window_rows_are_annotated` probe. `docs/README.md` `### Single-parent fast path` (lines 203-210) is the current consumer-facing description; the spec has none.

The strategy seam has **no owning spec** (confirmed: no file under `docs/SPECS/` takes it as its subject), so Worker 1 should attribute by hash + the commit's own label, as above, and not invent a card id. Whether Decision 5 should *describe* the strategy seam at all, or merely stop asserting a closed list, is a maintainer call — recommend the latter: restate line 275 as "whenever the window is absent or unsafe to consume", keep the named examples, and drop the implication that the list is exhaustive.

---

#### D8-1 — The strictness guard's first condition is `strictness != "off"` read from a `ContextVar`, not "`DST_OPTIMIZER_PLANNED` is stashed"; and the second condition reads two publish channels. **Post-ship**, commit `841e56d6` (2026-08-18, "fix(types,optimizer): scope relation visibility per relation and reach strictness in every execution").

Spec line 308 (Decision 8) and line 72 (Slice-4 checklist) both state condition 1 as "a strictness sentinel is stashed (`DST_OPTIMIZER_PLANNED` present — an optimizer ran with `strictness != "off"`)". Shipped `types/resolvers.py::_check_n1` (289-309):

1. **Condition 1** is `_strictness_for(context) != "off"` (293-296), which prefers the per-execution `_active_strictness` `ContextVar` (`optimizer/_context.py:98-101`, armed at `on_execute` entry) and falls back to the `DST_OPTIMIZER_STRICTNESS` stash. The `_context.py` comment states exactly why the spec's version was insufficient: the stash "is unavailable to an execution that runs without a `context_value`, and it is written at plan-publish time, so an operation whose root resolver returns something the walker cannot plan … never publishes it at all. Both shapes leave a configured N+1 guard silently disarmed."
2. **Condition 2** is `_relation_is_planned(key, planned)` (205-215), which is satisfied by the `DST_OPTIMIZER_PLANNED` stash **or** the per-execution `_scoped_relations` set (`_context.py::publish_scoped_relations`, published on *every* execution at `optimizer/extension.py:1308`, not only under strictness).
3. `_check_n1` also gained a `force_unplanned` parameter (spec-035 Decision 5, `resolvers.py:280-287`) that bypasses the planned-key short-circuit for an unsafe FK-id elision. Not reachable from the connection call site — `connection.py:2049-2057` does not pass it — recorded so the Decision-8 restatement does not over-claim that the planned key always short-circuits.

The **observable** contract Decision 8 promises is unchanged: planned -> silent, window-served -> silent, unplanned-and-will-query -> flag, `"off"` / no-optimizer -> no-op, all four pinned (`test_strictness_silent_when_planned` / `_when_window_served` / `_when_off` / `_no_optimizer`). Only the mechanism sentence is stale — but it is stale in the direction of *understating* the guarantee, and a reader implementing against it would reintroduce the fail-open `841e56d6` closed, so it is worth correcting precisely rather than loosely. **Spec homes:** lines 72 and 308; line 104 (`## Current state`, "it probes the plan's `DST_OPTIMIZER_PLANNED` sentinel and the instance caches") describes the pre-build shape of the same mechanism and is now doubly stale.

---

#### D8-2 — `_build_relation_connection_resolver` gained **two** parameters, not one. **Build-time.**

Spec line 63 (Slice-2 checklist) and line 146 (Decision 11's module map) both say the function "gains a relation-field-name parameter". Shipped signature (`connection.py:1933-1938`): `_build_relation_connection_resolver(target_type, accessor_name, relation_field_name, declaring_type)`. The fourth parameter is Decision **8**'s, not Decision 5's: `declaring_type` is the `parent_type` component of the resolver key, without which the resolve-time `resolver_key(declaring_type, relation_field_name, runtime_path)` cannot match the walker's emission — the "load-bearing parity for planned -> silent" the shipped docstring names (1986-1991). The call site passes the iterated `type_cls` deliberately rather than `registry.get(model)`, so a divergent secondary type's connection stays correctly flagged (`types/finalizer.py:770-773`).

Decision 8's body (line 308) states the key's three components but never says the resolver *takes* the declaring type as a constructor parameter, so the inventory sentence at line 146 is the site that needs the second parameter added. Small, but line 146 is the spec's module map — the one place a reader looks to know what each module gained.

---

#### D8-3 — `### Error shapes`'s "No new error surface" is false on the fast path. **Post-ship**, several commits; one is arguably **build-time**.

Spec lines 209-212 assert "No new error surface. The `first` + `last` guard, the sidecar-input-over-non-queryset guard, the `totalCount`-over-non-queryset guard, and the `SyncMisuseError` contract are all inherited unchanged on both the fast path and the fallback." At `HEAD` the fast path and its plan-time twin raise through at least four surfaces the sentence does not cover:

- `connection.py::_consume_window` (667-674) converts a malformed-pagination `ValueError` / `TypeError` (and `AttributeError` / `KeyError` / `IndexError`) into a `GraphQLError` rather than letting it surface as the field's own raw error — `11da7de8` ("Convert pre-sliced connection and out-of-range raw-pk M2M crashes to clear GraphQL errors"). Fail-closed, and arguably **build-time** since Decision 4 step (e) and Decision 5 both describe the raw error surfacing.
- `utils/connections.py::window_range_plan` (405-408) raises `OptimizerError` for a negative window offset or limit.
- `utils/connections.py::assert_window_fetch_mode` (434-465) raises `OptimizerError` when a probe window would also annotate the count — deliberately not a `ValueError` / `TypeError` "so the walker's leave-unplanned pagination handler cannot swallow it" (`744aea93` / `41008e4c`).
- `optimizer/walker.py` (947-963) raises `ConfigurationError` at plan time for `OptimizerHint.prefetch(Prefetch(..., to_attr=...))` on a generated relation (`57cbd32a`).
- `connection.py::DjangoConnection.resolve_connection` also now runs `resolve_relay_max_results` (a `ResourcePolicy.max_page_size` ceiling) and `check_deadline(info)` before any window work (1267-1275), both from the security program (`567cc6d0`, 2026-08-04; hardened by `3c105cf9`, 2026-08-26). Neither is spec-033's, but both sit inside the method Decision 5 describes and both can raise before the fast path is reached.

The last of these is also the **resolver-side consequence of the `to_attr`-hint rejection** Worker 0 flagged. To answer the routing question the dispatch asked: the *sentence that is now false* is **Decision 6 item 3**'s "a consumer `Prefetch(obj)` hint targets the accessor, the window targets the `to_attr`, no collision" (spec line 285) — a `to_attr`-bearing hint on a generated relation no longer coexists, it raises `ConfigurationError` unless the relation is consumer-assigned. That sentence lands under **R1a's Decision 6**. The `### Error shapes` section (lines 209-212) is the second home and belongs to **neither** cohort's Decision, so Worker 1 should treat it as a Slice-2 item in its own right. The resolver-side fact I own is the benign half: because a `to_attr`-bearing hint is refused outright for generated relations, the fast-path probe can never collide with a consumer hint's `to_attr` — the collision Decision 6 reasons about cannot arise, but for the opposite reason to the one it gives.

---

#### Also for Slice 2, lower priority

- **`## Current state` line 105** describes `_finalize_queryset` as appending "the pk as a terminal tiebreaker unless the effective ordering already ends in a unique column (`_ends_in_unique_column`)". Shipped, the whole rule is `optimizer/plans.py::effective_connection_order` (hoisted per Decision 11, re-exported at `connection.py:129` under the old private name for the spec-030 test pins), it now takes a keyset `cursor_field` first (`51421e54`), and per `41008e4c` "a nullable unique column no longer ends an order deterministically (SQL UNIQUE permits multiple NULLs), so the pk tiebreaker is appended". Whether a shipped card's `## Current state` section should track `HEAD` at all is a Worker 1 call — it is explicitly framed as "the repo as of this spec's authoring, before the build" (line 3), which argues for leaving it. Flagged because lines 104 and 105 are cited *as inputs* by Decisions 5 and 8, so a reader follows them expecting current fact.
- **Two test docstrings need a `.py` edit, not a spec edit** — L1 and L2 above. Neither is load-bearing; both are `tests/test_relay_connection.py`. Route to a repair cohort or fold into whichever cohort next writes that file.

---

#### The `TODO(spec-033 Slice 1-2)` anchor — a `.py` edit this cohort may not make

`tests/test_connection.py:1588` (`#"TODO(spec-033 Slice 1-2)"`) is the only `TODO(spec-033` anchor anywhere in `django_strawberry_framework/`, `tests/`, or `examples/` — measured with `grep -rn 'TODO(spec-033' --include='*.py' --include='*.md' .` excluding `docs/SPECS/`, which returns exactly one `.py` hit plus three `docs/builder/` mentions of the anchor itself. It is a **fence marker**, not staged work: its own body says "No new tests required here; this marker records the fence". `AGENTS.md` (the design-doc anchor rule) and `BUILD.md` `## Cross-slice integration pass` step 6 require the anchor removed in the change that ships the slice, replaced by non-`TODO` provenance where the context helps. Both slices shipped in `0.0.9`, so the anchor is discharged-but-unremoved.

Recommended replacement text — same six lines, `TODO(` removed, provenance kept, tense corrected:

```python
# spec-033 Slices 1-2 (DONE-033-0.0.9): root-connection no-regression fence. The
# shipped root-connection planning pins here (edges { node } extraction ->
# select_related / Prefetch on the pre-slice queryset) stayed GREEN UNMODIFIED
# through the helper consolidation (Decision 9) and the fast-path addition
# (Decision 5), which touch only the NESTED half. No new tests are required
# here; this marker records the fence (DoD item 12, "no root-connection
# regression").
```

Verified against the fence's own claim before recommending the tense change: `uv run pytest tests/test_connection.py --no-cov -q` passes, and the root-connection planning pins it names (`test_root_connection_field_queryset_prefetches_node_many_relation` and siblings) are present and unmodified. This is the one item in this artifact that is a `.py` edit rather than a spec edit; Worker 0 routes the owner. Its presence is **not** grounds for `revision-needed`.

---

#### Escalated (DRY, cross-cohort) — the 5-exception coercion tuple

`Escalated:` 15 occurrences of the identical `except (ValueError, TypeError, AttributeError, KeyError, IndexError,)` tuple across two files (11 in `connection.py`, 4 in `auth/mutations.py`; measured by exact-shape regex over every `.py` under `django_strawberry_framework/`, both member orders counted, zero elsewhere). `except` accepts a tuple name, so a single `_COERCION_ERRORS` constant is the readable consolidation. `auth/mutations.py` is outside every R1 cohort's ownership, so this cannot be actioned here. Resolution paths: (a) a module-level constant in `connection.py` only, leaving the cross-file half — cheap, and the cross-file signal survives for a later pass; (b) one shared constant under `utils/`, which touches a file no cohort owns and needs its own partition; (c) leave it, on the grounds that an explicit tuple at each site is more readable than an indirection. Recommend (b) at the integration pass, where cross-file literals are the declared instrument (`BUILD.md` `## Cross-slice integration pass` step 3).

### Review outcome

`review-accepted`.

Verification is complete for Decisions 5 and 8. **No spec contract in either Decision is undelivered by the code**, no correctness bug was found, and every divergence in the inventory above is a spec-text defect for Worker 1's Slice 2 — nine of them (D5-1, D5-2, D5-4, D5-5, D5-6, D5-7, D5-8, D8-1, D8-3) post-ship with the changing commit named, two (D5-3, D8-2) build-time.

The one Medium finding, **M1**, is transparently escalated rather than dispatched, per `docs/builder/worker-3.md` `### Acceptance gate`: the shipped code implements the spec's own stated third condition, so changing it is a contract decision Worker 2 cannot make, and the three resolution paths are laid out for Worker 1 and the maintainer. Both Low findings are test-docstring prose with correct bodies underneath.

`revision-needed` was considered and rejected: it is reserved for a spec contract the code does not deliver, and this cohort found none. M1's fail-open shape sits on a diagnostic path whose only triggers are a documented-unsupported consumer write into the package-reserved `_dst_` namespace and a hypothetical planner/resolver desync — and the spec, not the code, is what currently prescribes it.

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
