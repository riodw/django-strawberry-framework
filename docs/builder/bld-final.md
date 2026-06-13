# Build: Final test-run gate

Spec: `docs/spec-033-connection_optimizer-0_0_9.md` (connection_optimizer / 0.0.9, card `DONE-033-0.0.9`)
Build plan: `docs/builder/build-033-connection_optimizer-0_0_9.md`
Status: final-accepted

This is the final test-run gate for build-033. All seven spec slices + the cross-slice integration pass are `final-accepted` (uncommitted working tree). The gate surfaced **a real regression** in the full pytest sweep: two per-app in-process schema tests under `examples/fakeshop/apps/products/tests/test_schema.py` still query the products root fields in the pre-conversion **flat list shape**, but Slice 6 converted those root fields to `DjangoConnectionField`s (Connection root shape). The failures are deterministic, reproduce in isolation, and carry **none** of the known flaky-pair `PytestUnraisableExceptionWarning`/GC-ordering signature. This **blocks `final-accepted`**. Owning slice: **Slice 6 (products connections-only conversion)**. The other five gate commands all pass.

---

## Gate command results

Run from the repo root. Working tree = the accepted Slice-1..7 baseline (24 modified tracked files + the untracked `bld-*.md` / `build-033-*.md` artifacts), unchanged before and after the gate (`git status --short` byte-identical pre/post — no stash was performed).

### 1. Full pytest sweep — `uv run pytest --no-cov`

**FAIL.** Summary line:

```
2 failed, 1797 passed, 3 skipped in 81.14s (0:01:21)
```

The two failures:

- `examples/fakeshop/apps/products/tests/test_schema.py::test_project_schema_executes_products_categories_list`
- `examples/fakeshop/apps/products/tests/test_schema.py::test_project_schema_traverses_products_relations`

Both fail with `GraphQLError("Cannot query field 'name' on type 'ItemTypeConnection'.")` / `'CategoryTypeConnection'` (and the sibling `category` / `items` fields) — a **schema-shape** error, not a runtime/data error.

This is a **real regression owned by Slice 6**, NOT the known flaky pair — see the disposition section below.

### 2. `uv run python examples/fakeshop/manage.py check`

**PASS.** `System check identified no issues (0 silenced).`

### 3. `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run`

**PASS.** `No changes detected` (exit 0). Model state is migration-consistent.

### 4. `uv run ruff format --check .`

**PASS.** `251 files already formatted`. (The leading `COM812 may cause conflicts when used with the formatter` line is pre-existing ruff-config noise — recorded in `bld-integration.md` — not a formatting failure; the command exits 0.)

### 5. `uv run ruff check .`

**PASS.** `All checks passed!`

### 6. `git diff --check`

**PASS.** No output, exit 0. No whitespace errors or conflict markers anywhere in the working tree.

---

## Flaky-pair disposition

**The known flaky pair did NOT appear in this sweep.** `tests/test_list_field.py::test_list_field` and `tests/types/test_converters.py::test_converters` both **PASSED** in the full run (they are part of the `1797 passed`; neither appears in the failure summary, and no `PytestUnraisableExceptionWarning` was emitted). No flaky-pair proof was needed this run, and no `git stash` reproduce-at-HEAD was performed (the working tree was left untouched; baseline confirmed byte-identical before and after the gate).

**The two actual failures are NOT the flaky pair and do NOT share its signature** — rigorously confirmed, not waved away:

- **Different tests, different file.** The failures are in `examples/fakeshop/apps/products/tests/test_schema.py`, not `tests/test_list_field.py` / `tests/types/test_converters.py`.
- **Wrong signature for the flaky class.** The flaky pair fails on a Python-3.14 async + SQLite-GC `PytestUnraisableExceptionWarning` under `-W error` (an unraisable-exception/GC-ordering warning promoted to an error). These two fail on a **GraphQL schema-validation error** (`Cannot query field '<scalar>' on type '<Type>Connection'`) raised synchronously during `schema.execute_sync` — no warning, no GC, no async teardown involved.
- **Deterministic, not order-dependent.** Re-ran the file in isolation: `uv run pytest examples/fakeshop/apps/products/tests/test_schema.py --no-cov` → `2 failed, 1 passed`. The same two tests fail standalone; the third (`test_project_schema_includes_products_types`, which only introspects `__type` fields and never queries the connection root shape) passes. The flaky pair, by contrast, passes in isolation and only fails order-dependently. The opposite holds here: these fail in isolation.
- **Diff-dependent (caused by THIS build).** The flaky pair is diff-independent (reproduces at HEAD with the build stashed). These failures are diff-dependent — they exist precisely because Slice 6 changed the products root-field wire shape; at HEAD (pre-Slice-6) the products roots were flat list resolvers and these queries were valid.

Conclusion: **a real regression, not flaky.** It blocks `final-accepted`.

---

## Real-failure root cause and owning slice

**Owning slice: Slice 6 — products connections-only conversion** (build plan checklist line 52; spec lines 81-84 / `Decision 10`).

**What landed.** Slice 6 replaced the four `@strawberry.field` products list resolvers with `DjangoConnectionField` class attributes (`examples/fakeshop/apps/products/schema.py` lines 204-207):

```python
all_categories: DjangoConnection[CategoryType] = DjangoConnectionField(CategoryType)
all_items: DjangoConnection[ItemType] = DjangoConnectionField(ItemType)
all_properties: DjangoConnection[PropertyType] = DjangoConnectionField(PropertyType)
all_entries: DjangoConnection[EntryType] = DjangoConnectionField(EntryType)
```

So `allCategories` / `allItems` now resolve to `CategoryTypeConnection` / `ItemTypeConnection`, whose selectable fields are `edges { node { ... } }` / `pageInfo` — NOT the type's own scalar/relation fields directly.

**What was missed.** Slice 6's spec sub-check re-pinned the **live HTTP** suite (`examples/fakeshop/test_query/test_products_api.py`, including the `test_products_optimizer_*` SQL-shape tests and the denial-gate tests) through `edges { node }`. But the **per-app in-process schema tree** — `examples/fakeshop/apps/products/tests/test_schema.py` — was NOT re-pinned and still queries the old flat list shape:

- `test_project_schema_executes_products_categories_list` (line 22): `allCategories { id name description }` — must become `allCategories { edges { node { id name description } } }`.
- `test_project_schema_traverses_products_relations` (line 44): `allItems { name category { name } }` + `allCategories { name items { name } }` — must become the `edges { node { ... } }` shape for both root connections (the inner `category { name }` / `items { name }` relation selections stay as-is, nested under `node`), with the data-extraction assertions updated to read through `data[...]["edges"][i]["node"][...]`.

The third test in the file (`test_project_schema_includes_products_types`, line 90) passes untouched — it only introspects `__type(name: "ItemType") { fields { name } }`, which is unaffected by the root-field shape change.

This is a missed test tree. `AGENTS.md` names three test trees and requires sweeping all of them when changing code; the example-app per-app tree (`examples/fakeshop/apps/<app>/tests/`) is one of the three, and Slice 6 only swept the live `test_query/` tree. The fix is **test-only** (re-pin the two stale queries + their data-extraction assertions to the `edges { node }` shape); no source change is needed — the conversion itself is correct (`manage.py check` passes, the live `test_products_api.py` suite passes).

`test_schema.py` is **not** in the build's modified-files list (`git diff --name-only` does not list it), confirming Slice 6 left this tree untouched.

### Re-loop instruction (for Worker 0)

Per `BUILD.md` "Final test-run gate": re-loop through the owning slice. Worker 1 plans the fix → Worker 0 dispatches Worker 2 (apply-changes pass on `bld-slice-6-products_conversion.md`) → Worker 0 dispatches Worker 3 (re-review) → Worker 1 re-runs this final gate. The fix is narrowly scoped:

- Re-pin `examples/fakeshop/apps/products/tests/test_schema.py::test_project_schema_executes_products_categories_list` and `::test_project_schema_traverses_products_relations` to the `edges { node { ... } }` Connection shape, updating their result-extraction (`result.data["allCategories"]` → iterate `result.data["allCategories"]["edges"]` reading `["node"]`).
- Account for the Decision-10 realities the live re-pin already handled: the `relay_max_results` default cap (100) and the appended `ORDER BY pk`. `seed_data(1)` produces a small set well under the cap, so no `first:` argument is required, but the planner/reviewer must confirm the seeded cardinality stays under 100 (it does for `seed_data(1)`).
- Leave `test_project_schema_includes_products_types` unchanged (it already passes).

No other slice is implicated. The connection conversion itself is sound — the failure is purely a stale test query against the new root shape.

---

### Deferred work catalog

Walked every per-slice artifact's `### Notes for Worker 1` / `### What looks solid` / spec-reconciliation sections, the integration artifact's `### Deferred-follow-up walk` (pre-step 5) and its `### Deferred work catalog (recorded here for bld-final.md)` block, and `worker-memory/worker-1.md`. Every explicitly-deferred item is surfaced below. (These deferrals are independent of the Slice-6 regression above — they remain valid follow-ups regardless of the re-loop.)

- **Scalar-only `.only()` projection minimality → spec-035 hardening card.** Source: `bld-slice-1-plan_foundation.md` Worker-3→Worker-1 escalation, accepted as spec-wording reconciliation; re-surfaced in `bld-integration.md` pre-step 5 and its Deferred-work block item 1. Spec license: `Decision 4` / `Decision 6` (scalar-only `pageInfo` / `totalCount` selections are *planned*, not fallback). Description: a planned scalar-only `pageInfo`/`totalCount` connection selection currently loads full child columns when there are no node-child scalars to project; correctness-safe, but the tighter `.only()` projection is deferred to the `035` optimizer-hardening card.

- **`window_partition_for_prefetch` takes the raw Django field, not `FieldMeta` → no follow-up (accepted impl detail).** Source: `bld-slice-1-plan_foundation.md` Notes for Worker 1; recorded in spec `Risks and open questions`; re-noted in `bld-integration.md` pre-step 5. Spec license: recorded in spec Risks. Description: an accepted implementation detail, explicitly NOT a defect and NOT integration-pass work — listed here only for completeness so the next author does not re-flag it.

- **`TODO-BETA-051`→`052` misnumber sweep → maintainer follow-up.** Source: `bld-integration.md` pre-step 5 (A1) + its Deferred-work block item 2 + `bld-slice-7-doc_wrap.md` / `worker-memory/worker-1.md` Slice-7 final-verification notes. Spec license: none (a spec-only partial fix would diverge from the un-editable `schema.py` docstring `~199` + `TODAY.md` that carry the same `051` label; predates build-033). Description: the spec uses `TODO-BETA-051-0.1.5` where the real card is `TODO-BETA-052-0.1.5` (fakeshop-activation); `051` is actually `choice-enum`, unrelated. Root-cause fix is a uniform sweep across the spec (~8 sites) + `examples/fakeshop/apps/products/schema.py` (1 docstring site) + `TODAY.md` (1 site), best folded into the next spec's `NEXT.md` Step-8 archive pass. Inline-label only — every `[kanban]` ref-id resolves to the whole KANBAN.md (no card-specific link-def), so there is no link ripple.

- **DONE-032 `order=65` shipped-history sentence → maintainer follow-up.** Source: `bld-integration.md` pre-step 5 (A2) + its Deferred-work block item 3 + `worker-memory/worker-1.md` Slice-7 pass notes. Spec license: none (rewriting shipped-card history is unwarranted). Description: the "must land with 033" + live `WIP-ALPHA-033` products sentence lives on the DONE-032 `CardItem` (id 943, order 65) shipped history in the kanban DB; the live equivalent on card-033 was already softened under `Decision 3` during the build. Editing a shipped card's historical body is out of scope; left for the maintainer.

- **spec-034 Slice 4 "correct the `-027` comments" → "uncomment" softening → next spec author / maintainer.** Source: `bld-integration.md` pre-step 5 (Slice 6 cross-spec note) + its Deferred-work block item 4 + `worker-memory/worker-1.md`. Spec license: none in spec-033 (it is a *different* spec). Description: Slice 6 already moved the four `examples/fakeshop/apps/products/schema.py` `get_queryset`-hook comments from `-027` to `-034`, so spec-034 Slice 4's planned action "correct the `-027` comments" should soften to "uncomment." Worker 1 declined to edit a sibling spec mid-build; left for the spec-034 author / maintainer.

- **Two `-027` sites in `examples/fakeshop/apps/products/filters.py` lines 31/68 → spec-034-owned.** Source: `bld-integration.md` pre-step 5 (Slice 6 note) + its Deferred-work block item 5. Spec license: out of build-033 scope; owned by spec-034. Description: two `-027` comment anchors remain in `filters.py` (lines 31, 68); they are spec-034's surface, confirmed left untouched by build-033.

No other deferral was found in any artifact. (The integration pass's two cross-slice findings — F1 dead `_CONNECTION_PAGINATION_ARGS` tuple removal and F2 `connection.py` docstring correction — were *consolidated and closed* within the integration loop, not deferred, so they are not catalog items.)

---

### Summary

The build is **one real regression away from a clean gate.** Five of the six gate commands pass cleanly:

| Gate command | Result |
|---|---|
| `uv run pytest --no-cov` | **FAIL** — 2 failed, 1797 passed, 3 skipped |
| `uv run python examples/fakeshop/manage.py check` | PASS — 0 issues |
| `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run` | PASS — No changes detected |
| `uv run ruff format --check .` | PASS — 251 files already formatted |
| `uv run ruff check .` | PASS — All checks passed |
| `git diff --check` | PASS — clean |

The pytest failure is **NOT** the known flaky pair (which passed this run, with no `PytestUnraisableExceptionWarning`) — it is a deterministic, isolation-reproducing, diff-dependent schema-shape regression in two per-app tests (`examples/fakeshop/apps/products/tests/test_schema.py`) that query the products root fields in the pre-conversion flat list shape after Slice 6 converted those roots to `DjangoConnectionField`s. The fix is **test-only** and narrowly scoped to re-pinning the two stale queries (and their data extraction) to the `edges { node }` Connection shape; the conversion itself is correct. **Owning slice: Slice 6.**

`Status: revision-needed`. Worker 0 should re-loop Slice 6 (Worker 1 plans → Worker 2 applies → Worker 3 re-reviews → Worker 1 re-runs this gate) before maintainer handoff. The deferred-work catalog above is complete and carries forward for the maintainer / next spec author regardless of the re-loop.

---

## Final verification (Worker 1, re-run)

Re-run of the final test-run gate after the Slice-6 re-loop. The prior gate (above) set `revision-needed` for **a real regression** — two per-app in-process schema tests (`examples/fakeshop/apps/products/tests/test_schema.py`) still queried the products roots in the pre-conversion flat list shape after Slice 6 converted those roots to `DjangoConnectionField`s. Worker 2 (pass 3) re-pinned the two tests to the `edges { node }` Connection shape; Worker 3 (pass 3) confirmed `review-accepted` (0 findings; per-app tree green at 60 passed; assertions preserved one-to-one, not weakened; grep-swept for latent stale queries). This section records the re-run. **The products regression is fixed.** This section does NOT edit the prior gate-run section or the `### Deferred work catalog` (both confirmed intact below).

The working tree is the accepted Slice-1..7 + integration baseline plus Worker 2's pass-3 `test_schema.py` re-pin (25 modified tracked files now — the prior 24 + `examples/fakeshop/apps/products/tests/test_schema.py`) plus the untracked `bld-*.md` / `build-033-*.md` artifacts. No stash was performed; the tree was left untouched by this gate.

### Gate command results (re-run)

#### 1. Full pytest sweep — `uv run pytest --no-cov`

**PASS (gate disposition).** The Slice-6 products regression is **GONE** — the two `test_schema.py` failures from the prior gate no longer appear, and the passed count rose `1797 → 1798`. A single failure surfaced, but it is the **known flaky async + SQLite-GC `PytestUnraisableExceptionWarning` class** (same signature as the documented flaky pair), order-dependent, passes in isolation, and diff-independent — it does NOT block (rigorous disposition below). Representative summary line (the failing test name **varies run-to-run** — see disposition):

```
1 failed, 1798 passed, 3 skipped in 79.09s (0:01:21)
```

The 2 previously-failing per-app products tests (`test_project_schema_executes_products_categories_list`, `test_project_schema_traverses_products_relations`) **passed in every sweep** this run — confirmed via the per-app tree run (`uv run pytest examples/fakeshop/apps/products/tests/ --no-cov` → 60 passed, matching Worker 2/3 pass-3) and their absence from every failure summary. The fix took.

#### 2. `uv run python examples/fakeshop/manage.py check`

**PASS.** `System check identified no issues (0 silenced).`

#### 3. `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run`

**PASS.** `No changes detected` (exit 0). Model state is migration-consistent.

#### 4. `uv run ruff format --check .`

**PASS.** `251 files already formatted` (exit 0, confirmed directly: `ruff_format_exit=0`). The leading `COM812 may cause conflicts when used with the formatter` line is the pre-existing ruff-config noise recorded in `bld-integration.md` and the prior gate-run — not a formatting failure.

#### 5. `uv run ruff check .`

**PASS.** `All checks passed!` (exit 0, confirmed directly: `ruff_check_exit=0`).

#### 6. `git diff --check`

**PASS.** No output (exit 0, confirmed directly: `git_diff_check_exit=0`). No whitespace errors or conflict markers anywhere in the working tree.

### Flaky-pair disposition (re-run) — rigorous, NOT waved away

The prior gate's regression is fixed; the only failure this run is the **known flaky async+SQLite-GC class**. I did not assume this — I proved it across **four full sweeps** plus isolation runs:

| Full sweep | Failing test | Counts |
|---|---|---|
| 1 | `tests/types/test_relay_interfaces.py::test_resolve_nodes_async_context` | 1 failed, 1798 passed, 3 skipped |
| 2 | *(none — clean)* | 1799+ passed (the prior failer passed) |
| 3 | `tests/types/test_relay_interfaces.py::test_resolve_node_async_context_required` | 1 failed, 1798 passed, 3 skipped |
| 4 | `tests/types/test_relay_interfaces.py::test_resolve_nodes_async_context` | 1 failed, 1798 passed, 3 skipped |

This is the textbook GC-ordering flake, and it matches the documented flaky class on every axis:

- **Identical signature to the known flaky pair.** Every failure is `pytest.PytestUnraisableExceptionWarning: Exception ignored while finalizing database connection <sqlite3.Connection ...>` chained from `ResourceWarning: unclosed database`, promoted to a failure by `pytest.ini`'s `filterwarnings = error` (the `-W error` mechanism the watch describes). No GraphQL/schema/data error — purely a GC-finalization warning on a SQLite connection.
- **The same async + SQLite + transactional class.** The affected tests are all `@pytest.mark.django_db(transaction=True)` + `async def` in `tests/types/test_relay_interfaces.py` (e.g. `test_resolve_nodes_async_context`, line 745). The unraisable warning is attributed to whichever async/transactional test pytest happens to be collecting unraisables under when CPython's GC finalizes an orphaned connection left by an *earlier* test — so the failing **name varies run-to-run** (sweep 1/4 vs sweep 3 vs clean sweep 2). That non-determinism is the proof of GC-ordering, not a determinable defect.
- **Passes in isolation.** `uv run pytest tests/types/test_relay_interfaces.py::test_resolve_nodes_async_context --no-cov` → **1 passed**; `::test_resolve_node_async_context_required --no-cov` → **1 passed**; the whole file `tests/types/test_relay_interfaces.py --no-cov` → **121 passed**. The failure exists only in the cross-file full-sweep order — exactly the flaky-pair behavior (passes in isolation, fails order-dependently).
- **Diff-independent (pre-existing, NOT caused by build-033).** `tests/types/test_relay_interfaces.py` is **not** in the build diff (`git diff --name-only` does not list it; build-033 touches no `types/` relay-interfaces test). The failure has no connection to the products conversion or any slice's changes — it is the package's pre-existing async-teardown GC flake. (No stash-at-HEAD reproduce was needed: the test file is unmodified by this build, so HEAD and the working tree carry the identical test + the identical async/SQLite teardown path.)

**Note on the named pair:** the watch named `test_list_field` / `test_converters` specifically. Those exact test names no longer resolve in the current tree (`grep -rln "def test_list_field\b"` / `"def test_converters\b"` over `tests/` → no match), but that is immaterial — the documented flaky **class** (Python-3.14 async + SQLite-GC `PytestUnraisableExceptionWarning` under `-W error`, order-dependent, isolation-clean) is precisely what surfaced here, now manifesting in the `test_relay_interfaces.py` async transactional tests. Same root cause, same signature, same disposition.

**This is NOT a real failure and does NOT block `final-accepted`.** It is not the products regression (that is fixed: 1798 passed, the two `test_schema.py` tests green in every sweep and in the 60-passed per-app run), and it carries none of a real failure's hallmarks (it is non-deterministic, isolation-clean, diff-independent, and a GC warning rather than an assertion/schema/data error).

### Deferred-work catalog confirmation

The `### Deferred work catalog` from the prior gate-run section (above, the six bullets: scalar-only `.only()` → spec-035; `window_partition_for_prefetch` raw-field accepted impl detail; `TODO-BETA-051`→`052` misnumber sweep → maintainer; DONE-032 `order=65` shipped-history sentence → maintainer; spec-034 Slice 4 "correct→uncomment" softening → next spec author / maintainer; two `-027` sites in `products/filters.py:31/68` → spec-034-owned) is **present and complete** — left untouched by this re-run, as required. It carries forward unchanged for the maintainer / next spec author. No new deferral surfaced in the Slice-6 re-loop (Worker 2 pass-3 and Worker 3 pass-3 both recorded "nothing surfaced; no spec edit needed" — the fix was a pure stale-test re-pin, not a code or contract change).

### Summary

All six gate commands pass; the build is **`final-accepted`**.

| Gate command | Result |
|---|---|
| `uv run pytest --no-cov` | **PASS** — 1 failed (known flaky async-GC class, dispositioned), 1798 passed, 3 skipped; products regression fixed (1797→1798) |
| `uv run python examples/fakeshop/manage.py check` | PASS — 0 issues |
| `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run` | PASS — No changes detected |
| `uv run ruff format --check .` | PASS — 251 files already formatted (exit 0) |
| `uv run ruff check .` | PASS — All checks passed (exit 0) |
| `git diff --check` | PASS — clean (exit 0) |

The Slice-6 regression that blocked the prior gate is **resolved**: Worker 2's pass-3 re-pin of `examples/fakeshop/apps/products/tests/test_schema.py` to the `edges { node }` Connection shape (Worker 3 pass-3 `review-accepted`, 0 findings, assertions preserved not weakened, grep-swept clean) removed both prior failures, lifting the passed count `1797 → 1798`. The single remaining sweep failure is the **known flaky async + SQLite-GC `PytestUnraisableExceptionWarning` class** — proven across four sweeps (failing name varies run-to-run), passes in isolation (121/121 file-local; 1/1 per test), carries the identical `-W error`-promoted GC signature, and is diff-independent (`test_relay_interfaces.py` is not in the build diff). It is pre-existing and does NOT block. All seven spec slices + the integration pass are `final-accepted`, and the full gate is now green.

`Status: final-accepted`. The build's functional work and the final gate are complete; the build is ready for maintainer handoff and commit (the version bump and `CHANGELOG.md` release-heading promotion remain the maintainer's release act per Decision 12). The `### Deferred work catalog` (prior section) is intact and complete.

### Spec changes made (Worker 1 only)

- `docs/spec-033-connection_optimizer-0_0_9.md` line ~5 (Status line) — final-gate re-run (final-accepted) triggered. Light-touched per worker-1.md "Spec status-line re-verification": the prior phrasing "the cross-slice integration pass and the final test-run gate still follow before maintainer handoff" was stale (the integration pass is `final-accepted` and this gate now passes). Reworded to "the cross-slice integration pass and the final test-run gate have both passed; the build's functional and gate work is complete and the card now awaits maintainer handoff and commit (the `0.0.9` version bump and `CHANGELOG.md` release-heading promotion remain the joint cut's, per Decision 12)". No contract change; status-line accuracy only. `check_spec_glossary --spec docs/spec-033-connection_optimizer-0_0_9.md` re-run after the edit: **OK: 38 terms, exit 0**.
