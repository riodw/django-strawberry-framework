# Build: Cross-slice integration pass

Spec: `docs/spec-033-connection_optimizer-0_0_9.md` (connection_optimizer / 0.0.9, card `DONE-033-0.0.9`)
Build plan: `docs/builder/build-033-connection_optimizer-0_0_9.md`
Status: final-accepted

This is the cross-slice integration pass for build-033. All seven spec slices are `final-accepted` (uncommitted working tree). Two cross-slice quality findings need a single Worker 2 consolidation pass (both source-comment / dead-code, no behavior change); the exact edit list is in [`### Worker 2 consolidation edit list`](#worker-2-consolidation-edit-list). Everything else in the integration checklist is clean.

---

## Pre-step results (per BUILD.md "Cross-slice integration pass")

### 1. Prior slice artifacts read in slice order (required)

Read in full, in order: `bld-slice-1-plan_foundation.md`, `bld-slice-2-fast_path.md`, `bld-slice-3-cache_key_hygiene.md`, `bld-slice-4-strictness_wiring.md`, `bld-slice-5-library_sql_shape.md`, `bld-slice-6-products_conversion.md`, `bld-slice-7-doc_wrap.md`. Plus the active spec (whole), the build plan, and `worker-memory/worker-1.md` (which carried the two known candidates into this pass). All seven artifacts are `final-accepted`.

### 2. Static inspection helper — run confirmation

Re-ran `scripts/review_inspect.py --output-dir docs/shadow` this pass on every package file the build touched with review-worthy logic:

- `optimizer/walker.py`, `optimizer/plans.py`, `optimizer/extension.py`, `connection.py`, `types/resolvers.py`, `types/finalizer.py`, `types/definition.py` — all seven re-inspected; fresh `.overview.md` + `.stripped.py` written under `docs/shadow/`.

Per-slice helper history confirms full coverage: Slice 1 (walker/plans/extension/connection, Worker 1 plan + Worker 3 review), Slice 2 (connection, Worker 3), Slice 3 (extension, Worker 3), Slice 4 (connection/resolvers, Worker 3). Slices 5–6 are test/example-only (`test_library_api.py`, `test_products_api.py`, `apps/products/schema.py`) and Slice 7 is doc/DB-only — helper correctly skipped each with a recorded reason (no package-source review-worthy logic). No skip was unexplained.

### 3. Repeated string literals — cross-file comparison

Compared the "Repeated string literals" section of all seven fresh shadow overviews. Per-file lists:

| File | Repeated literals (executable, ≥ default min-length) |
|---|---|
| `optimizer/walker.py` | `selections` 8x, `arguments` 6x, `directives` 4x, `prefetch` 3x, `related_model` 3x, `_optimizer_runtime_prefixes` 3x, `target_field` 2x |
| `optimizer/plans.py` | `prefetch_to` 2x, `queryset` 2x |
| `optimizer/extension.py` | `_strawberry_schema` 2x |
| `connection.py` | `order_by` 7x, `total_count` 3x |
| `types/resolvers.py` | None |
| `types/finalizer.py` | `<unresolved>`, `connection` 3x, `FilterSet` 3x, plus filterset/orderset error-message fragments (all pre-existing finalizer error prose) |
| `types/definition.py` | `resolve_id` 2x, `__func__` 2x |

**Cross-file finding:** no executable string literal recurs across two or more of the touched files as a duplicated value that should be a shared constant. Every recurrence in the table above is **intra-file** (the same token repeated within one file — e.g. `order_by` 7x in `connection.py`, all argument-name / kwarg uses), and the cross-slice shared vocabulary is already single-sourced (next paragraph). `connection`/`FilterSet`/`OrderSet` in `finalizer.py` are pre-existing finalizer content, not build-033 surface.

**Cross-slice shared vocabulary is single-sourced — verified by grep, not just the shadow table:**
- The window-annotation literals `_dst_row_number` / `_dst_total_count` / `_dst_row_number_reversed` are defined ONCE in `optimizer/plans.py` (`WINDOW_ROW_NUMBER` / `WINDOW_TOTAL_COUNT` / `WINDOW_ROW_NUMBER_REVERSED`, lines 476-478). `connection.py` imports `WINDOW_ROW_NUMBER` / `WINDOW_TOTAL_COUNT` (line 64-66) and reads them via `getattr(node, WINDOW_*)` — no re-spelled `"_dst_row_number"` executable literal anywhere in `connection.py` (the only `_dst_*` mentions there are docstrings/comments). This is the Slice-1/Slice-2 DRY pin, confirmed holding.
- The `_dst_<field>_connection` `to_attr` literal is single-sourced via `optimizer/walker.py::_relation_connection_to_attr` (line 1005-1014, the only `f"_dst_{...}_connection"` site); `connection.py` imports and reuses it (line 70). No fourth f-string.
- The `edges { node }` unwrap helpers (`_named_children` / `_node_children_with_runtime_prefix` / `_with_runtime_prefix` / `_response_key`) live ONLY in `walker.py`; `extension.py` imports them back (Decision 9). One implementation, not two.

**One exception — the flagged pagination-arg-name candidate — is NOT a clean repeated-literal case but a dead-constant case; see [Decision on the known DRY candidates](#decision-on-the-known-dry-candidates) below.** The four names `first`/`last`/`before`/`after` do not surface in the shadow "Repeated string literals" tables because each appears below the per-file recurrence threshold, but they DO exist as two named constants in two modules — which is the candidate the prompt and `worker-1.md` flagged. Investigated in full below.

### 4. Imports — one-way dependency direction confirmation

Compared the "Imports" section of all seven shadow overviews and grep-verified the absence of every reverse edge. The documented one-way directions all hold; no cycle, no sibling reaching outside its boundary:

- **`extension` → `walker`** (extension imports `_named_children`, `_node_children_with_runtime_prefix`, `_response_key`, `plan_optimizations`, `plan_relation` from `.walker`, line 67). Reverse (`walker` → `extension`) is ABSENT — `walker.py` imports nothing from `extension` (grep: none). ✓
- **`connection` → `plans`** (connection imports `WINDOW_ROW_NUMBER`, `WINDOW_TOTAL_COUNT`, `deterministic_order`, `ends_in_unique_column` from `.optimizer.plans`, line 64). Reverse (`plans` → `connection`) ABSENT — the one `connection.py` mention in `plans.py` (line 487) is a docstring comment, not an import. ✓
- **`connection` → `walker`** (connection imports `_relation_connection_to_attr` from `.optimizer.walker`, line 70). Reverse (`walker` → `connection`) ABSENT (grep: none). ✓
- **`connection` → `types.resolvers`** (connection imports `_check_n1` from `.types.resolvers`, line 77, Slice 4). Reverse (`resolvers` → `connection`) ABSENT — `resolvers.py` imports `..optimizer.*` / `..registry` / `..exceptions` / `..utils.relations`, never `connection` (grep: none). ✓
- **`plans`** depends only on django + `..exceptions` + `..utils.relations` — it imports neither `walker`, `extension`, nor `connection` (the lowest module; both `walker` and `connection` import from it). ✓
- **`types/definition`** gained the `relation_connections` slot (Slice 1) and imports neither `connection` nor `walker` directly (grep: none) — it stays a data-definition module read by the walker via `registry`. ✓
- **`types/finalizer`** writes the slot and, at its existing Phase-2.5 call site (line 352), imports `_build_relation_connection_resolver` / `_connection_type_for` from `..connection` (a finalizer→connection edge that predates this build — Slice 2 only threaded `field.name` / the declaring `type_cls` into the existing call). No new cross-boundary import. ✓

`git diff -- django_strawberry_framework/__init__.py` is **empty** — no public-surface export added (DoD item 12; spec "adds no public symbol"). All new names (`apply_window_pagination`, `window_partition_for_prefetch`, `deterministic_order`, `ends_in_unique_column`, the `WINDOW_*` constants, `_WindowedConnectionRows`, `_check_n1`'s widened signature, `relation_connections`) are package-internal.

### 5. Deferred-follow-up walk (every accepted artifact's "What looks solid" / "DRY findings" / "Notes for Worker 1")

Walked all seven artifacts' solid/DRY/W1-notes sections plus the spec Risks for items that should land in this pass:

- **Slice 1 — scalar-only `.only()` projection minimality** (W3→W1 escalation, accepted as spec-wording reconciliation): scalar-only `pageInfo`/`totalCount` selections are *planned* (not fallback) but load full child columns when there are no node-child scalars. Correctness-safe; tighter-projection refinement deferred to the `035` hardening card. **Not an integration-pass item** (a deferred optimization, not a cross-slice DRY/consistency defect) → carried to `bld-final.md` Deferred-work catalog.
- **Slice 1 — `window_partition_for_prefetch` takes the raw Django field, not `FieldMeta`** (accepted impl detail, recorded in spec Risks). **Not an integration-pass item** → not a defect.
- **Slice 2 — `connection.py` docstring L1 clause mischaracterizes upstream as "overwriting" row numbers** (W3 Low L1; W1 explicitly LEFT it in the Slice-2 cut and spawned a follow-up). **THIS IS an integration-pass item** — "whether comments now tell one coherent story across the new code." Confirmed still present and still wrong; swept here. See finding [F2](#f2--connectionpy-docstring-l1-clause-mischaracterizes-upstream-comment-only).
- **Slice 3 — `walker._CONNECTION_PAGINATION_ARGS` (tuple) vs `extension._PAGINATION_ARG_NAMES` (frozenset)** (W1 explicitly carried this to the integration pass; in `worker-1.md`). **THIS IS the integration-pass DRY item.** Investigated in full; the investigation changed its character (see [F1](#f1--walker_connection_pagination_args-is-dead-code-not-a-shape-justified-constant-pair)).
- **Slice 6 / Slice 7 — `TODO-BETA-051`→`052` misnumber (A1) and DONE-032 `order=65` shipped-history sentence (A2)** — W1 dispositioned both as **maintainer follow-ups** (a spec-only partial fix of A1 would create a worse spec-vs-source divergence; rewriting shipped-card history is unwarranted). **Not an integration-pass item** (they are doc/spec maintenance outside the build's source/test surface, already escalated to the maintainer) → carried to `bld-final.md` Deferred-work catalog.
- **Slice 6 → spec-034 cross-spec note** — soften spec-034 Slice 4 "correct the `-027` comments" → "uncomment" now that Slice 6 already moved the four `schema.py` `get_queryset` hook comments to `-034`. W1 declined to edit a different spec mid-build. **Not an integration-pass item** (different spec, not in build) → carried to `bld-final.md` Deferred-work catalog. (Also: two `-027` sites remain in `examples/fakeshop/apps/products/filters.py` lines 31/68 — owned by spec-034, out of build-033 scope; confirmed left untouched.)

No deferred item from the artifacts was a missed cross-slice consolidation that this pass must force, EXCEPT the two findings below (F1, F2), both already flagged for this pass.

---

## Integration checklist findings

### Duplicated helpers across slices

**None.** The DRY spine held end-to-end: `_check_n1` is the single strictness checker (parameterized for the connection kind in Slice 4, not forked into `connection.py`); the `edges { node }` helpers are one implementation in `walker.py` (Decision 9 consolidation, `extension` imports back); `ends_in_unique_column` + `deterministic_order` are a true MOVE+import-back to `plans.py` (the cursor-parity invariant, `connection._ends_in_unique_column is plans.ends_in_unique_column` proven by test); the windowed child queryset reuses `_build_prefetch_child_queryset` rather than re-deriving. No near-copy helper was introduced.

### Inconsistent naming or error handling between slices

**None of consequence.** The strictness message is one f-string family (`Unplanned N+1: {field_name}` stem + optional ` ({reason})` suffix; list callers pass `reason=None` → byte-identical pre-card message). The `OptimizerError` raise is single-sited in `_check_n1`; `connection.py` never raises it directly. The `_dst_` reserved namespace is consistent across the window annotations, the `to_attr`, and the synthesis marker. `GraphQLError`/`SliceMetadata`-ValueError handling on the fallback path preserves the shipped error locality (Slice 1 step f). Naming is uniform: `WINDOW_*` constants, `_connection_*` helpers, `relation_connections` slot.

### Repeated ORM/queryset patterns that should be centralized

**None.** The window-application (`apply_window_pagination`), partition-derivation (`window_partition_for_prefetch`), and deterministic-order (`deterministic_order`) are each single helpers in `plans.py`, called from one site. Child-queryset construction reuses the existing `_build_prefetch_child_queryset` / `_build_child_queryset` / `_ensure_connector_only_fields`. No parallel queryset-building path was introduced.

### Misplaced responsibilities between modules

**None.** Plan vocabulary lives in `plans.py` (window helpers, order, partition, resolver keys); selection-walk + recognition + planning in `walker.py`; the consume-side fast path + fallback + strictness consultation in `connection.py`; the strictness checker in `types/resolvers.py`; the synthesis-metadata slot in `types/definition.py` written by `types/finalizer.py`. The one-way import graph (pre-step 4) confirms the layering: optimizer subpackage never reaches into `connection.py`; `connection.py` sits above and reads down into `plans`/`walker`/`types.resolvers`. The walker reads connection recognition through the `relation_connections` definition slot, never `DjangoConnectionField` internals (the DoD's no-internals rule).

### Missing or too-broad exports introduced by the build

**None.** `git diff -- django_strawberry_framework/__init__.py` is empty (verified). No `__all__` change in any touched module's own export list. Spec "adds no public symbol, no `Meta` key, no constructor argument" holds.

### Repeated string literals / dictionary keys / tuple shapes across slices

**One finding (F1), and it is a dead-constant, not a live duplication** — see below. All genuinely-shared literals (window annotations, `to_attr`, the `edges`/`node` keys) are single-sourced.

### Whether comments now tell one coherent story across the new code

**One finding (F2)** — the `connection.py` docstring L1 clause still tells the wrong story about upstream's row-number scheme, contradicting the (now-reconciled) spec Decision 5 and the verified upstream source. See below.

---

## Decision on the known DRY candidates

### F1 — `walker._CONNECTION_PAGINATION_ARGS` is dead code, not a shape-justified constant pair

**Flagged as:** `walker._CONNECTION_PAGINATION_ARGS` (tuple, "plan-time ordered reads") vs `extension._PAGINATION_ARG_NAMES` (frozenset, "cache-key membership") — "two single-source pagination-arg-name constants in different modules/shapes," with the question of whether to consolidate into one shared source or justify the two shapes as different access patterns.

**Investigation (this pass, grep + source read):**

- `optimizer/extension.py::_PAGINATION_ARG_NAMES` (frozenset, lines 83-90) is **live**: read at `extension.py` line 223 (`if arg.name.value in _PAGINATION_ARG_NAMES and isinstance(arg.value, VariableNode)`) — a membership test in the Slice-3 nested-pagination-variable cache-key collector. A frozenset is the correct shape for a membership test.
- `optimizer/walker.py::_CONNECTION_PAGINATION_ARGS` (tuple, lines 996-1001) is **DEAD**: grep over the entire package, `tests/`, `examples/`, and standing docs finds exactly ONE occurrence — its own definition. **It is never read.** Its leading comment claims it is "the pagination family the window math consumes," but the window math (`walker._connection_window_slice`, line 1117-1120) reads the four names via inline `arguments.get("first")` / `arguments.get("last")` / `arguments.get("before")` / `arguments.get("after")` and passes them as the explicit `first=`/`last=`/`before=`/`after=` keyword arguments to `SliceMetadata.from_arguments` — it does NOT iterate the tuple. The sibling constant directly beneath it, `_CONNECTION_SIDECAR_ARGS` (line 1002), IS consumed (line 1172, the fallback `any(arguments.get(name) ...)` check); the pagination tuple has no analogous consumer.
- Ruff does not flag it (module-level constants are not unused-import/unused-variable targets).

**Why the "two justified shapes" framing does not hold:** there is no *live* duplication to justify. Only one of the two constants is consumed. The walker tuple is not "the plan-time ordered-reads form" — the plan-time reads do not use it; they use positional kwargs to `SliceMetadata`. So the candidate resolves not to "consolidate into one shared source" and not to "justified two shapes," but to a third outcome: **the walker tuple is dead weight, and its comment actively misleads** a reader into believing the window math iterates it.

**Decision: REMOVE the dead tuple (Worker 2 consolidation pass).** Deleting `_CONNECTION_PAGINATION_ARGS` leaves `extension._PAGINATION_ARG_NAMES` as the single live pagination-arg-name constant, correctly shaped (frozenset) for its single live use. No shared-source extraction is warranted, because the walker has no use for a collection of these names (its reads are positional `SliceMetadata` kwargs, not an iteration or membership test). Extracting a shared constant the walker would not consume would be over-engineering; deletion is the higher-quality, root-cause fix (AGENTS.md "recommend the root-cause fix over the surface patch"). The walker's `_CONNECTION_SIDECAR_ARGS` (live) stays; its shared comment block must be trimmed so it describes only the surviving sidecar constant.

**Risk: nil.** Zero readers anywhere (package, tests, examples, standing docs). No test or contract references it.

### F2 — `connection.py` docstring L1 clause mischaracterizes upstream (comment-only)

**Flagged as:** the `connection.py` docstring L1 clause from Slice 2 that mischaracterizes upstream as "overwriting" row numbers — sweep-or-justify.

**Investigation (this pass):**

- `connection.py::_resolve_from_window` docstring, lines 190-192 (current text): *"...matches the pipeline's `ListConnection` cursors directly - no `_dst_total_count - row_number` re-derivation (that is upstream's scheme, which overwrites its row-number annotation; Slice 1 did not port that, recorded for Worker 1)."*
- This is **factually wrong**, confirmed against the upstream source this pass (`/Users/riordenweber/projects/strawberry-django-main`): `pagination.py::apply_window_pagination` keeps `_strawberry_row_number` FORWARD (lines 244-245) and adds a *separate* `_strawberry_row_number_reversed` (lines 269-270) used ONLY for the `__lte` filter (line 275) — it does **not** overwrite `_strawberry_row_number`. `relay/list_connection.py` uses `cursor=node._strawberry_row_number - 1` (line 193) with forward page-flag comparisons (lines 197-199) for every window. Slice 1's port is verbatim-faithful to upstream. The `_dst_total_count - row_number` scheme the clause attributes to upstream is used by **neither** upstream **nor** this package.
- The spec Decision 5 (line 301) and Edge cases (line 446) were already reconciled in Slice 2's final verification to the forward `_dst_row_number - 1` scheme, and now explicitly state "An earlier revision of this Decision described a `_dst_total_count - _dst_row_number` reversed-cursor scheme; neither upstream nor Slice 1's port implements that." So the docstring's "recorded for Worker 1" note is **stale** — the reconciliation it points at already happened (Slice 2). The docstring is the only remaining site still telling the wrong story.

**Decision: SWEEP (Worker 2 consolidation pass).** Correct the clause so the comment tells the same (correct) story the spec and the verified upstream source now tell. The behavior is byte-correct and test-pinned (`test_fast_path_wire_parity_last_only`); this is a Low, comment-only defect, but "comments tell one coherent story across the new code" is an explicit integration-pass check and the clause directly contradicts the reconciled spec. Worker 1 explicitly left it in the Slice-2 cut for an integration-pass sweep; this is that sweep.

---

## Worker 2 consolidation edit list

Both edits are source-comment / dead-code, no behavior change, no test change. Both land in files this pass already scanned. After the edits, Worker 2 runs `uv run ruff format .` + `uv run ruff check --fix .` and confirms no tool churn. **No new tests** are needed (F1 deletes an unconsumed constant; F2 corrects prose) — but Worker 2 should run a focused `uv run pytest tests/optimizer/ tests/test_relay_connection.py tests/test_connection.py --no-cov` to confirm the optimizer/connection suites stay green after the deletion (defense-in-depth; the constant has no readers so the suite must be unaffected).

### Edit 1 (F1) — remove the dead pagination-args tuple in `django_strawberry_framework/optimizer/walker.py`

Current (lines ~992-1002):

```python
# Pagination argument names a synthesized connection sibling may carry. ``filter``
# / ``order_by`` are the SIDECAR argument names (their presence forces a per-parent
# fallback, Decision 6); the four below are the pagination family the window math
# consumes.
_CONNECTION_PAGINATION_ARGS = (
    "first",
    "last",
    "before",
    "after",
)
_CONNECTION_SIDECAR_ARGS = ("filter", "order_by")
```

Replace with (delete the dead `_CONNECTION_PAGINATION_ARGS` tuple AND trim the comment to describe only the surviving constant):

```python
# Sidecar argument names a synthesized connection sibling may carry; their presence
# forces a per-parent fallback (Decision 6). The pagination family
# (``first`` / ``last`` / ``before`` / ``after``) is read positionally by
# ``_connection_window_slice`` as explicit ``SliceMetadata.from_arguments`` kwargs,
# so it needs no name collection here.
_CONNECTION_SIDECAR_ARGS = ("filter", "order_by")
```

- The tuple `_CONNECTION_PAGINATION_ARGS` has zero readers package-wide (grep-confirmed: tests, examples, standing docs all clean) — deletion is safe.
- Keep `_CONNECTION_SIDECAR_ARGS` exactly as is (it is consumed at line ~1172).
- Do NOT change `_connection_window_slice`'s inline `arguments.get("first")` reads — they are correct (positional `SliceMetadata` kwargs).

### Edit 2 (F2) — correct the upstream-mischaracterizing docstring clause in `django_strawberry_framework/connection.py`

Current (`_resolve_from_window` docstring, lines ~189-192):

```
    rows). The forward absolute-offset cursor therefore matches the pipeline's
    ``ListConnection`` cursors directly - no ``_dst_total_count - row_number``
    re-derivation (that is upstream's scheme, which overwrites its row-number
    annotation; Slice 1 did not port that, recorded for Worker 1). The cursor
```

Replace the parenthetical so it states the verified truth (upstream keeps row numbers forward; the `_dst_total_count - row_number` scheme is a now-corrected earlier spec-revision description, implemented by neither upstream nor this package) and drops the stale "recorded for Worker 1" note. Suggested wording (Worker 2 may adjust prose, but it must no longer claim upstream "overwrites" its row-number annotation):

```
    rows). The forward absolute-offset cursor therefore matches the pipeline's
    ``ListConnection`` cursors directly - no ``_dst_total_count - row_number``
    re-derivation (that scheme was an earlier spec-revision description that
    neither upstream ``strawberry-django`` nor Slice 1's port implements - both
    keep the row number forward and use a separate reversed annotation only for
    the plan-time ``__lte`` filter). The cursor
```

- Behavior is unchanged (the forward `_dst_row_number - 1` math is already correct and test-pinned by `test_fast_path_wire_parity_last_only`).
- Keep the surrounding sentences (lines 183-189, 192-194) intact.

---

## Build report (Worker 2)

Consolidation pass applying the two findings from the `Worker 2 consolidation edit list` (F1 + F2). Both are source-comment / dead-code, no behavior change, no test change.

### Files touched

- `django_strawberry_framework/optimizer/walker.py` (F1) — deleted the dead `_CONNECTION_PAGINATION_ARGS = ("first", "last", "before", "after")` tuple and trimmed the preceding comment block so it now describes ONLY the surviving `_CONNECTION_SIDECAR_ARGS` constant (and notes that the pagination family is read positionally by `_connection_window_slice` as explicit `SliceMetadata.from_arguments` kwargs, so no name collection is needed). `_CONNECTION_SIDECAR_ARGS` is unchanged (def at line 997; consumed at line 1167, the per-parent-fallback `any(arguments.get(name) ...)` check). The inline `arguments.get("first")` / `"last"` / `"before"` / `"after"` reads inside `_connection_window_slice` are untouched.
- `django_strawberry_framework/connection.py` (F2) — rewrote the parenthetical clause in the `_resolve_from_window` docstring (was lines ~189-192). The old clause claimed the `_dst_total_count - row_number` re-derivation was "upstream's scheme, which overwrites its row-number annotation; Slice 1 did not port that, recorded for Worker 1." Replaced with Worker 1's suggested verbatim wording: that scheme was an earlier spec-revision description that neither upstream `strawberry-django` nor Slice 1's port implements — both keep the row number forward and use a separate reversed annotation only for the plan-time `__lte` filter. The surrounding sentences are intact.

### Tests added or updated

- none — comment/dead-code only. F1 deletes an unconsumed constant; F2 corrects prose. No behavior changed, so no test needed changing or adding.

### Validation run

- **F1 zero-readers re-confirmation (grep, this pass):** `grep -rn "_CONNECTION_PAGINATION_ARGS" django_strawberry_framework/ tests/ examples/ docs/` before the edit found exactly ONE code occurrence in package source — its own definition site at `walker.py:996`. `tests/` and `examples/` are completely clean. The remaining hits are all in non-code scratch surfaces: the `docs/builder/bld-*.md` cycle artifacts (this integration artifact + slice-3 / slice-7 carry-forward notes), `docs/builder/worker-memory/` (W0/W1 carry-forward notes), and the regenerable `docs/shadow/...walker.stripped.py` snapshot — none of which are runtime readers. Confirmed deletion is safe; no reader exists anywhere. After the edit, `grep` confirms `_CONNECTION_PAGINATION_ARGS` is gone from `walker.py` and `_CONNECTION_SIDECAR_ARGS` remains (def 997, consumer 1167).
- `uv run ruff format .` — pass; `251 files left unchanged` (no reformatting; the COM812-vs-formatter warning is pre-existing config noise, not a change my edits caused).
- `uv run ruff check --fix .` — pass; `All checks passed!` (no fixes applied).
- `git status --short` after both ruff invocations — the 24 modified tracked files (`CHANGELOG.md`, `KANBAN.html`, `KANBAN.md`, `README.md`, `TODAY.md`, `django_strawberry_framework/{connection,optimizer/extension,optimizer/plans,optimizer/walker,types/definition,types/finalizer,types/resolvers}.py`, `docs/{GLOSSARY,README,TREE}.md`, `docs/spec-033-connection_optimizer-0_0_9.md`, `examples/fakeshop/apps/products/schema.py`, `examples/fakeshop/db.sqlite3`, `examples/fakeshop/test_query/{test_library_api,test_products_api}.py`, `tests/optimizer/{test_extension,test_plans,test_walker}.py`, `tests/test_relay_connection.py`) plus the untracked `bld-*.md` / `build-033-*.md` artifacts are the **accepted Slice-1..7 baseline** (the whole build's uncommitted final-accepted working tree per this artifact's preamble) — NOT reverted, per the consolidation-pass constraint. **My pass's only source deltas are the two intended edits to `walker.py` and `connection.py`** (both of which were already in the baseline diff from Slices 1-4 / Slice 2, so they appear as cumulative diffs). Ruff applied zero changes, so there was **no tool churn to revert**.
- Focused test run (no `--cov*`): `uv run pytest tests/optimizer/ tests/test_relay_connection.py tests/test_connection.py --no-cov` → **485 passed in 11.75s**. The F2 behavior pin `tests/test_relay_connection.py::test_fast_path_wire_parity_last_only` ran and passed (confirmed via a targeted `-k` re-run: 1 passed). The deleted constant has no readers, so the optimizer/connection suites are unaffected — confirmed green.

### Implementation notes

- F2 used Worker 1's suggested verbatim wording from the edit list unchanged (it is accurate against the verified upstream source). No prose adjustment was needed.
- F1 comment trim preserved the Decision-6 cross-reference for the sidecar args and added a one-line explanation of why no pagination-name collection lives in the walker (the reads are positional `SliceMetadata` kwargs), so a future reader does not re-introduce a dead collection.

### Notes for Worker 3

- Both changes are isolated and self-contained: one dead module-level constant deleted + its comment trimmed (`walker.py`), one docstring parenthetical rewritten (`connection.py`). No control-flow, signature, or behavior change. The shadow file `docs/shadow/django_strawberry_framework__optimizer__walker.stripped.py` still shows the old `_CONNECTION_PAGINATION_ARGS` at line 996 because it is a stale snapshot from the integration-pass `review_inspect.py` run; it is regenerable and was not (and must not be) edited. Re-run `review_inspect.py --output-dir docs/shadow` if a fresh overview of `walker.py` is wanted for the re-review.
- Worker 1's investigation (F1) of zero-readers was independently re-confirmed by grep this pass before deletion; no reader was found that Worker 1 missed.

### Notes for Worker 1 (spec reconciliation)

- Nothing surfaced. F2 brings the last remaining wrong-story comment site into line with the already-reconciled spec Decision 5 / Edge cases (Slice 2). The spec needs no further edit; F1 is a pure dead-code removal with no spec surface.

---

## Re-spawn plan (for Worker 0)

Per BUILD.md "Cross-slice integration pass" and this artifact's `revision-needed` status: Worker 0 dispatches **Worker 2 (consolidation pass)** with the two edits above, then **Worker 3 (review pass)** to confirm the deletion broke nothing and the docstring now reads coherently, then **re-spawns Worker 1** to re-run this integration pass. The consolidation loop is small (two comment/dead-code edits in two files, no test change); a single Worker 2 + Worker 3 cycle should close it. On re-spawn, Worker 1 re-verifies F1/F2 resolved in the diff, re-confirms the import-direction + repeated-literal + public-surface checks still hold, and flips this artifact to `final-accepted`.

---

## Summary

The build is cross-slice **clean on every structural axis** — no duplicated helpers, no inconsistent naming/error handling, no misplaced module responsibilities, no public-surface drift (`__init__.py` diff empty), one-way import direction confirmed (extension→walker, connection→{plans,walker,types.resolvers}, plans depends on neither; no cycles), and all genuinely cross-slice-shared vocabulary single-sourced (the `_dst_*` window annotations in `plans.py`, the `to_attr` helper in `walker.py`, the `edges { node }` helpers consolidated into `walker.py`, `_check_n1` the single strictness checker).

Two cross-slice **quality** findings need a single small Worker 2 consolidation pass, both no-behavior-change:

- **F1 (DRY / dead code):** the `walker._CONNECTION_PAGINATION_ARGS` tuple — the flagged "pagination-arg constant pair" — turns out to be **dead code** (zero readers; the window math reads the four names as inline positional `SliceMetadata` kwargs, not via the tuple), while `extension._PAGINATION_ARG_NAMES` (frozenset) is the single live constant correctly shaped for its membership test. The decision is **deletion of the dead tuple + comment trim**, NOT a shared-source extraction (the walker has no use for a collection of these names) and NOT a "two justified shapes" acceptance (only one shape is live).
- **F2 (comments / coherent story):** the `connection.py::_resolve_from_window` docstring L1 clause still claims the `_dst_total_count - row_number` cursor scheme is "upstream's scheme, which overwrites its row-number annotation" — factually wrong (verified against the upstream source: upstream keeps the row number forward and adds a separate reversed annotation only for the `__lte` filter, exactly as Slice 1's port does), and it carries a stale "recorded for Worker 1" note pointing at a reconciliation that already happened in Slice 2. The decision is to **sweep the clause** to match the reconciled spec Decision 5 and the verified upstream behavior.

Status: **final-accepted** (this `## Summary` was written at the `revision-needed` stage; the consolidation loop closed and the pass was re-run — see [`## Final verification (Worker 1)`](#final-verification-worker-1) for the closing confirmation). The exact Worker 2 edit list is in [`### Worker 2 consolidation edit list`](#worker-2-consolidation-edit-list); both edits landed and were confirmed in the diff. Items dispositioned as future-work (scalar-only projection minimality, `051`→`052` misnumber, DONE-032 shipped-history sentence, the spec-034 "correct→uncomment" softening, the two `filters.py` `-027` sites) are NOT consolidation work — they are carried to the `bld-final.md` Deferred-work catalog for the maintainer / next spec author.

---

## Review (Worker 3)

Review of the Worker 2 consolidation pass (F1 dead-code removal in `walker.py`, F2 docstring rewrite in `connection.py`). Reviewed against the `### Worker 2 consolidation edit list` contract and Worker 2's `## Build report (Worker 2)`. The diff is the uncommitted Slice-1..7 baseline plus the two consolidation edits; per the artifact's preamble and `worker-3.md` "Cumulative-diff trap" I scoped to `walker.py` + `connection.py` only and treated the 22 other baseline files as accepted, out-of-scope context.

### High:

None.

### Medium:

None.

### Low:

None.

#### Observation (not a finding): F2 mid-phrase line wrap

In `connection.py::_resolve_from_window`, the reflowed docstring breaks "The cursor / PREFIX / base64 stay owned by the edge class" across the parenthetical's close and the next line (current lines 194-195). This is a pre-existing ruff-format reflow artifact of the surrounding paragraph, not introduced by F2's parenthetical rewrite, and reads correctly when rendered. Not load-bearing; recorded as an observation only, no change requested.

### DRY findings

- **F1 resolved the only standing cross-slice DRY/dead-constant candidate.** Confirmed-correct. `walker._CONNECTION_PAGINATION_ARGS` (the flagged "pagination-arg constant pair") is gone from the source tree. Independent grep over `django_strawberry_framework/`, `tests/`, and `examples/` for `_CONNECTION_PAGINATION_ARGS` returns **zero** matches (exit 1). The only remaining hits are non-runtime scratch/regenerable surfaces — `docs/shadow/...walker.stripped.py` (stale snapshot, regenerable, Worker 2 flagged it), the `docs/builder/bld-*.md` cycle artifacts, and `docs/builder/worker-memory/` — none of which are code readers. The decision to **delete** rather than extract a shared constant is the correct, root-cause call: the walker has no collection-use for these names (its reads are positional `SliceMetadata.from_arguments` kwargs), so a shared constant would be over-abstraction.
- Re-ran `scripts/review_inspect.py --output-dir docs/shadow` on both files this pass. The fresh **Repeated string literals** tables match the integration artifact's recorded values exactly — `walker.py`: `selections` 8x / `arguments` 6x / `directives` 4x / `prefetch` 3x / `related_model` 3x / `_optimizer_runtime_prefixes` 3x / `target_field` 2x; `connection.py`: `order_by` 7x / `total_count` 3x. Crucially, `first`/`last`/`before`/`after` do **not** surface as repeated literals in `walker.py` (each appears once, in the inline `_connection_window_slice` reads), confirming F1's deletion did not leave a same-file recurrence that would warrant re-introducing a name collection. No new cross-file or intra-file DRY candidate appeared.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` is **empty** (exit 0, no output). `__all__` and the re-export list are unchanged. F1/F2 are both package-internal (a private constant deletion + a private-function docstring), consistent with the spec's "adds no public symbol" Definition-of-Done.

### CHANGELOG sanity

Not applicable; the consolidation pass did not modify `CHANGELOG.md` (the `walker.py`/`connection.py` diff is the only consolidation surface). `CHANGELOG.md` appears in the working tree only as part of the accepted Slice-7 baseline, out of scope for this consolidation review.

### Documentation / release sanity

Not applicable; the consolidation pass did not modify docs/release/KANBAN/archive surfaces. The two edits are an in-source dead-code removal and an in-source docstring rewrite. (The doc/KANBAN files in the working tree are the accepted Slice-7 baseline, already `final-accepted`, out of scope here.)

### What looks solid

- **F1 — confirmed-correct.** The dead `_CONNECTION_PAGINATION_ARGS` tuple is removed. The preceding comment is trimmed to describe only the surviving `_CONNECTION_SIDECAR_ARGS`, and it now explains *why* no pagination-name collection lives in the walker (the four names are read positionally by `_connection_window_slice` as explicit `SliceMetadata.from_arguments` kwargs) — which forestalls a future reader re-introducing a dead collection. `_CONNECTION_SIDECAR_ARGS` is byte-unchanged (def at `walker.py:997`) and still live: consumed at `walker.py:1167` in the Decision-6 sidecar-fallback classification (`any(arguments.get(name) is not None for name in _CONNECTION_SIDECAR_ARGS)`). The inline `arguments.get("first")` / `"last"` / `"before"` / `"after"` reads in `_connection_window_slice` (lines 1112-1115) are untouched and correctly feed `SliceMetadata.from_arguments` as `first=`/`last=`/`before=`/`after=` kwargs (lines 1117-1124).
- **F2 — confirmed-correct.** The `connection.py::_resolve_from_window` docstring (lines 183-196) no longer claims upstream "overwrites" its row-number annotation and no longer carries the "recorded for Worker 1" note (grep for both `overwrites` and `recorded for Worker 1` in `connection.py` returns zero). The new wording accurately states the forward `_dst_row_number` is kept and a separate `_dst_row_number_reversed` annotation is added only for the plan-time `__lte` filter. **Independently verified against both sources:** upstream `strawberry-django/pagination.py` keeps `_strawberry_row_number` forward (line 244; `__gt`/`__lte` offset filters at 256/280) and adds a separate `_strawberry_row_number_reversed` used only at the `__lte` filter (lines 269/275); this package's port in `optimizer/plans.py` mirrors it exactly (`_dst_row_number` forward, separate `_dst_row_number_reversed` `__lte=limit` only — lines 616/625/629/637). The old "overwrites" claim was indeed factually wrong; the rewrite tells the same (correct) story the reconciled spec Decision 5 now tells. Behavior is byte-unchanged and pinned by `test_fast_path_wire_parity_last_only` (`tests/test_relay_connection.py:997`), whose own docstring already describes the forward-row-number scheme.
- **No behavior change, no logic change, no test change — confirmed.** The two edits are a module-level dead-constant deletion + comment trim (`walker.py`) and a docstring parenthetical rewrite (`connection.py`). No executable line changed. No test file was touched by the consolidation: grep of `tests/` for `_CONNECTION_PAGINATION_ARGS` / `_CONNECTION_SIDECAR_ARGS` returns zero, so no test could have depended on the removed constant.
- **No scope creep — confirmed.** Only `walker.py` + `connection.py` carry the consolidation deltas (beyond the accepted Slice-1..7 baseline). `git diff -- django_strawberry_framework/__init__.py` is empty.

### Temp test verification

No temp tests needed. The two edits are comment/dead-code only with no behavior surface to probe. Verification was: independent grep (zero readers of the removed constant; stale phrases gone from the docstring), source reads of both edit sites, an upstream-source cross-check of the F2 claim, a fresh `review_inspect.py` repeated-literal confirmation, and the focused suite run below. `docs/builder/temp-tests/integration/` was not used.

### Notes for Worker 1 (spec reconciliation)

Nothing to reconcile. F2 brings the last wrong-story comment site into line with the already-reconciled spec Decision 5 / Edge cases (done in Slice 2). F1 is a pure dead-code removal with no spec surface. The spec needs no further edit.

### Focused test result

`uv run pytest tests/optimizer/ tests/test_relay_connection.py tests/test_connection.py --no-cov` → **485 passed in 11.81s** (matches Worker 2's reported 485). The F2 behavior pin `test_fast_path_wire_parity_last_only` ran and passed. The removed constant has no readers, so the optimizer/connection suites are unaffected — confirmed green.

### Review outcome

`review-accepted`. F1 and F2 are both confirmed-correct. No behavior/test/logic change, zero remaining code readers of the deleted constant, public surface unchanged, no new findings at any severity. Worker 0 should re-spawn Worker 1 to re-run the integration pass and flip this artifact to `final-accepted`.

---

## Final verification (Worker 1)

Re-ran the integration pass after the Worker 2 consolidation + Worker 3 `review-accepted`. The two findings (F1, F2) are resolved in the diff, the build stays clean on every integration axis, and the focused suite is green. Closing the integration pass: **`final-accepted`**.

### F1 — resolved (confirmed in diff + grep)

- `git diff -- django_strawberry_framework/optimizer/walker.py` shows the dead `_CONNECTION_PAGINATION_ARGS = ("first", "last", "before", "after")` tuple **deleted** and the preceding comment trimmed to describe only the surviving constant (it now notes the pagination family is read positionally by `_connection_window_slice` as explicit `SliceMetadata.from_arguments` kwargs, so no name collection is needed — forestalls a future reader re-introducing a dead collection).
- **Independent zero-readers re-confirmation (this pass):** `grep -rn "_CONNECTION_PAGINATION_ARGS" django_strawberry_framework/ tests/ examples/` → **exit 1, zero matches**. The dead tuple is gone with no code reader anywhere. (The only non-runtime residual mentions are this artifact, the worker-memory carry notes, and the regenerable `docs/shadow/...walker.stripped.py` snapshot — none are runtime readers.)
- `_CONNECTION_SIDECAR_ARGS` is **still live and byte-unchanged**: def at `walker.py:997`, consumed at `walker.py:1167` (the Decision-6 sidecar-fallback `any(arguments.get(name) is not None for name in _CONNECTION_SIDECAR_ARGS)` classification). The inline `arguments.get("first")` / `"last"` / `"before"` / `"after"` reads in `_connection_window_slice` are untouched.

### F2 — resolved (confirmed in diff + grep)

- `git diff -- django_strawberry_framework/connection.py` shows the `_resolve_from_window` docstring parenthetical rewritten. The clause no longer claims the `_dst_total_count - row_number` re-derivation is "upstream's scheme, which overwrites its row-number annotation," and no longer carries the stale "recorded for Worker 1" note. It now states accurately that the scheme "was an earlier spec-revision description that neither upstream `strawberry-django` nor Slice 1's port implements - both keep the row number forward and use a separate reversed annotation only for the plan-time `__lte` filter."
- **Stale-phrase re-confirmation (this pass):** `grep -n "overwrites\|recorded for Worker 1" django_strawberry_framework/connection.py` → **exit 1, zero matches**. The last wrong-story comment site now tells the same (correct) story as the reconciled spec Decision 5 / Edge cases (Slice 2) and the verified upstream source. Behavior is byte-unchanged and pinned by `test_fast_path_wire_parity_last_only`.

### Integration axes still clean

- **Public surface unchanged:** `git diff -- django_strawberry_framework/__init__.py` is **empty** (re-verified this pass). No public symbol added; both F1/F2 are package-internal (a private constant deletion + a private-function docstring). Spec "adds no public symbol" DoD holds.
- **No new duplication from the consolidation:** F1 was a deletion (it removed a dead constant, it did not add a near-copy), and Worker 3's fresh `review_inspect.py` repeated-literal tables match this artifact's recorded values exactly — `first`/`last`/`before`/`after` do **not** surface as repeated literals in `walker.py` after the deletion, so no same-file recurrence warrants re-introducing a name collection. The decision to delete (not extract a shared constant) was the correct root-cause call: the walker has no collection-use for these names.
- All other integration-checklist axes (duplicated helpers, inconsistent naming/error handling, repeated ORM/queryset patterns, misplaced responsibilities, one-way import direction) were confirmed clean in the pre-step pass above and are untouched by a two-edit comment/dead-code consolidation.

### Focused suite — green

`uv run pytest tests/optimizer/ tests/test_relay_connection.py tests/test_connection.py --no-cov` (no `--cov*`) → **485 passed in 11.98s**. Matches Worker 2's and Worker 3's reported 485. The F2 behavior pin `test_fast_path_wire_parity_last_only` is in the suite and passed. The deleted constant has no readers, so the optimizer/connection suites are unaffected — confirmed green.

### Spec status line

Re-verified spec lines 1-5. Line 5 already accurately reads "all seven slices ... accepted; the cross-slice integration pass and the final test-run gate still follow before maintainer handoff" (card moved to `DONE-033-0.0.9`, on-disk version still `0.0.8`). No spec edit warranted — the line correctly describes the state with the final test-run gate still ahead. No `### Spec changes made (Worker 1 only)` entry needed this pass.

### Deferred work catalog (recorded here for `bld-final.md`)

The following items were dispositioned during the slice/integration passes as future-work (NOT consolidation work). They are captured here so the final test-run gate's `### Deferred work catalog` can cite each one:

1. **Scalar-only `.only()` projection minimality → spec-035 hardening card.** Source: pre-step 5 (Slice 1, W3→W1 escalation). Scalar-only `pageInfo`/`totalCount` selections are *planned* (not fallback) but load full child columns when there are no node-child scalars; correctness-safe, tighter-projection refinement deferred. Not an integration-pass defect.
2. **`TODO-BETA-051`→`052` misnumber sweep → maintainer follow-up.** Source: pre-step 5 (Slice 6/7) + Slice-7 final-verification memory. A spec-only partial fix would diverge from the un-editable `schema.py` docstring (~199) + `TODAY.md` that carry the same `051` label; full root-cause is a uniform sweep across spec (8 sites) + `schema.py` (1) + `TODAY.md` (1). Predates build-033.
3. **DONE-032 `order=65` shipped-history sentence → maintainer follow-up.** Source: pre-step 5 (Slice 6/7). The "must land with 033" + live WIP-ALPHA-033 products sentence lives on the DONE-032 `CardItem` (id 943, order 65) shipped history; the live equivalent on card-033 was already softened (Decision 3). Rewriting shipped-card history is unwarranted.
4. **spec-034 Slice 4 "correct the `-027` comments" → "uncomment" softening → next spec author / maintainer.** Source: pre-step 5 (Slice 6 cross-spec note). Slice 6 already moved the four `schema.py` `get_queryset` hook comments to `-034`; W1 declined to edit a different spec mid-build.
5. **Two `-027` sites in `examples/fakeshop/apps/products/filters.py` lines 31/68 → spec-034-owned.** Source: pre-step 5 (Slice 6 note). Owned by spec-034, out of build-033 scope; confirmed left untouched.

### Outcome

Integration pass **CLOSED — `final-accepted`**. F1 + F2 confirmed resolved in the diff (dead tuple deleted with grep-zero code readers; docstring corrected with stale phrases gone), public surface unchanged (`__init__.py` diff empty), no new duplication introduced, focused suite 485 passed. The deferred-work catalog above is recorded for the final test-run gate (`bld-final.md`). Worker 0 should advance to the final test-run gate.
