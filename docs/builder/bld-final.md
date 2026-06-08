# Build: Final test-run gate

Spec reference: `docs/spec-030-connection_field-0_0_9.md`
Build plan: `docs/builder/build-030-connection_field-0_0_9.md`
Status: final-accepted

The narrow final test-run gate (BUILD.md "Final test-run gate") was run by Worker 1
after the integration pass set `bld-integration.md` to `final-accepted`. One of the
six gate commands failed (`uv run pytest --no-cov`), so the build is **NOT**
`final-accepted`. The pytest failures decompose into three defect classes owned by
Slice 1, Slice 2, and Slice 4 (detailed below). The other five gate commands pass.

No baseline-dirty exception covers these failures: the build plan's only recorded
baseline-dirty file is `docs/GLOSSARY.md`, which Slice 5 legitimately regenerated
from the DB (it is coherent now, not an exception), and `git diff --check` does not
flag it. The failures are genuine, in-scope regressions introduced by the build.

## Gate command results

| # | Command | Result |
|---|---------|--------|
| 1 | `uv run pytest --no-cov` | **FAIL** — 9 failed, 1402 passed, 3 skipped (63s) |
| 2 | `uv run python examples/fakeshop/manage.py check` | PASS — `System check identified no issues (0 silenced).` |
| 3 | `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run` | PASS — `No changes detected` |
| 4 | `uv run ruff format --check .` | PASS — `234 files already formatted` (exit 0; the `COM812`-vs-formatter warning is the repo's standing benign config note) |
| 5 | `uv run ruff check .` | PASS — `All checks passed!` (exit 0) |
| 6 | `git diff --check` | PASS — no output (exit 0; no whitespace errors / conflict markers) |

The explicit `--no-cov` was used for the pytest sweep (required — `pytest.ini`
`addopts` auto-applies `--cov`; plain `uv run pytest` would be a forbidden coverage
run). No other coverage-shaped flag was passed; line coverage was not inspected.

## Failure analysis (pytest)

The 9 failures are deterministic (confirmed across two full sweeps) and fall into
three classes. Worker 1 traced each to its owning slice; Worker 1 did NOT fix any
code (per the gate's "do not fix code yourself; report so Worker 0 can re-loop the
owning slice" rule).

### Class A — async connection tests leak DB rows (6 failures) — owning slices: Slice 1 + Slice 2

```text
FAILED examples/fakeshop/test_query/test_products_api.py::test_products_items_order_by_related_category_name_as_staff
FAILED examples/fakeshop/apps/products/tests/test_admin.py::test_item_admin_seed_data_zero_does_not_create
FAILED examples/fakeshop/apps/products/tests/test_commands.py::test_delete_data_command_nothing_to_delete_warns
FAILED examples/fakeshop/apps/products/tests/test_services.py::test_seed_data_creates_expected_counts
FAILED examples/fakeshop/apps/products/tests/test_services.py::test_seed_data_creates_only_shortfall_when_x_grows
FAILED examples/fakeshop/apps/products/tests/test_services.py::test_delete_data_int_mode_no_data_returns_zeros
```

- **Symptom.** Each failing assertion sees rows that should not exist — e.g.
  `test_seed_data_creates_expected_counts` asserts `result["categories"] == Category.objects.count()`
  and fails `assert 0 == 25`: `seed_data(1)` reports creating 0 categories (its
  shortfall logic sees the target already met) because **25 `Category` rows leaked
  into the test DB** from an earlier test.
- **Root cause (proven by bisection).** `tests/test_connection.py` contains
  `async def` tests decorated with a *plain* `@pytest.mark.django_db` (no
  `transaction=True`). Under `pytest-django`, a plain-`django_db` **async** test is
  not wrapped in the per-test rollback transaction (the transaction wrapper cannot
  span the event loop), so the rows it seeds via `services.seed_data(...)` persist
  into the shared test DB and pollute every later `@pytest.mark.django_db` test.
  - Isolated repro: `pytest tests/test_connection.py::test_total_count_async_path_counts_via_acount examples/fakeshop/apps/products/tests/test_services.py::test_seed_data_creates_expected_counts`
    → the products test fails `assert 0 == 25`. The products app suite passes 53/53
    when run alone; the failures appear only after a seeding async connection test runs.
  - Confirmed against clean HEAD (`235c3e4`): these 6 do NOT fail without the
    build's `tests/test_connection.py` — i.e. they are build-introduced, not a
    pre-existing flake.
- **Leaking tests** (both seed rows that are never rolled back):
  - `tests/test_connection.py::test_total_count_async_path_counts_via_acount`
    (`connection.py` line 286 region; `seed_data(2)`) — **Slice 1** (the async
    `.acount()` totalCount test).
  - `tests/test_connection.py::test_connection_resolver_async_dispatch`
    (line 810 region; `seed_data(2)`) — **Slice 2** (the async-dispatch test).
  - (`test_async_consumer_resolver_iterable_with_total_count_selected_raises`,
    line 628, also `async`+`django_db`, seeds via `sync_to_async(seed_data)(1)` —
    same Slice 2 leak class; smaller blast radius.)
- **Why it slipped through.** Every per-slice and integration pass ran *focused*
  test scopes (e.g. `tests/test_connection.py` + `tests/optimizer/test_extension.py`),
  where the async tests pass and the leak is invisible because no cross-tree
  `django_db` test runs afterward. The leak surfaces only in the full sweep — which
  is exactly what this final gate is for.
- **Fix direction (for the owning slice's Worker 2, Worker 1's call to plan):** the
  async tests must isolate their DB writes so they roll back — the standard shapes
  are `@pytest.mark.django_db(transaction=True)` on the async test (with explicit
  teardown) or seeding/asserting via `sync_to_async`-wrapped helpers inside a
  transactional fixture so no rows persist. The async tests' *behavioral* assertions
  (the `.acount()` count, async dispatch) are correct; only their DB-isolation is wrong.

### Class B — `__all__` pinning test not updated for the Slice-4 public exports (1 failure) — owning slice: Slice 4

```text
FAILED tests/base/test_init.py::test_public_api_surface_is_pinned
  At index 1 diff: 'DjangoConnection' != 'DjangoListField'
  Left contains 2 more items, first extra item: 'finalize_django_types'
```

- **Symptom.** `tests/base/test_init.py::test_public_api_surface_is_pinned` pins
  `django_strawberry_framework.__all__` to a 10-name tuple that does NOT include the
  two new connection exports. Slice 4 (authorized by Decision 14) correctly grew
  `__all__` with `"DjangoConnection"` + `"DjangoConnectionField"` (alphabetical,
  between `BigInt` and `DjangoListField`) but did **not** update this pinning test to
  match, so the test now fails against the (correctly) widened surface.
- **Owning slice: Slice 4** (the public-export promotion). The export itself is
  correct and spec-authorized; the omission is that the same slice's diff did not
  carry the `tests/base/test_init.py` update that pins the new surface. (Per
  AGENTS.md the public-surface pin test is supposed to grow in lockstep when a spec
  adds a public name; Slice 4 added the names but not the test edit.)
- **Note on the build plan's Decision-13 guard:** the plan flags
  `tests/base/test_init.py::test_version` as version-bump-owned-by-the-joint-cut and
  off-limits. That guard is about the **version** assertion. The
  **`test_public_api_surface_is_pinned`** assertion in the same file is a separate,
  public-surface pin that Slice 4's Decision-14 export *does* license editing
  (the surface widened in-card; the version did not). Worker 1 should confirm this
  distinction when planning the re-loop so Worker 2 edits only the `__all__` pin,
  not `test_version`.
- **Fix direction:** add `"DjangoConnection"` and `"DjangoConnectionField"` to the
  expected tuple in `test_public_api_surface_is_pinned` (alphabetical), in the
  Slice-4 loop.

### Class C — package import eagerly pulls in `filters` / `orders` (2 failures) — owning slice: Slice 4 (root cause Slices 1/2)

```text
FAILED tests/filters/test_finalizer.py::test_registry_clear_works_without_filters_imported
FAILED tests/orders/test_inputs.py::test_registry_clear_works_without_orders_imported
```

- **Symptom.** Both tests spawn a subprocess that does `django.setup()`, imports
  `django_strawberry_framework.registry`, and asserts the `filters` (resp. `orders`)
  package is NOT yet in `sys.modules` before calling `registry.clear()`. The
  `assert 'django_strawberry_framework.filters' not in sys.modules` now trips.
- **Root cause (proven).** Slice 4 added `from .connection import DjangoConnection,
  DjangoConnectionField` to `django_strawberry_framework/__init__.py`. `connection.py`
  (Slices 1/2) imports `filter_input_type` from `filters/__init__.py` and
  `order_input_type` from `orders/__init__.py` at **module scope**, so importing the
  package top-level now eagerly imports both `filters` and `orders`. Direct repro:
  ```text
  import django_strawberry_framework
  -> 'django_strawberry_framework.filters' in sys.modules  == True
  -> 'django_strawberry_framework.orders'  in sys.modules  == True
  ```
  This breaks the lazy-import contract those two tests pin (the package must be
  importable, and `registry.clear()` must work, without the `filters`/`orders`
  subpackages having been imported).
- **Owning slice: Slice 4** is where the regression becomes observable (the
  `__init__.py` → `connection` import is the trigger), but the **root cause** is the
  module-level `filter_input_type` / `order_input_type` imports in `connection.py`
  (landed in Slices 1/2). Worker 1's re-loop plan should fix the abstraction, not
  the test: defer the `filters`/`orders` imports in `connection.py` to call-time
  (inside `_synthesized_signature`, where `filter_input_type` / `order_input_type`
  are actually invoked) so top-level package import stays lazy — mirroring the
  existing lazy-import discipline the two tests guard. (A test-only relaxation would
  violate the AGENTS.md root-cause-over-surface standard.)
- **Why it slipped through.** Same reason as Class A: the per-slice focused scopes
  never imported the package fresh in a subprocess and asserted the lazy-import
  contract; only the full sweep exercises `tests/filters/test_finalizer.py` and
  `tests/orders/test_inputs.py` alongside the new `__init__.py` export.

## Re-loop recommendation (for Worker 0)

The gate is blocked. The three defect classes touch three slices; Worker 0 should
re-loop them (Worker 1 plans the fix → Worker 0 dispatches Worker 2 → Worker 0
dispatches Worker 3 → Worker 1 re-runs this gate):

1. **Slice 1 + Slice 2** — fix the DB-isolation of the `async def` tests in
   `tests/test_connection.py` so seeded rows roll back (Class A). The largest blast
   radius; fixing it clears all 6 Class-A failures.
2. **Slice 4** — update `tests/base/test_init.py::test_public_api_surface_is_pinned`
   to include the two Decision-14 exports (Class B); and defer the
   `filters`/`orders` imports in `connection.py` to call-time so the package import
   stays lazy (Class C, root cause in Slices 1/2 but surfaced by Slice 4's
   `__init__.py` export). Worker 1 plans whether Class C is best re-looped through
   Slice 4 or Slice 2 given the import lives in `connection.py`.

After the fixes land and are reviewed, re-run this exact six-command gate. The other
five commands already pass and are unaffected by the recommended changes.

## Deferred work catalog

Walked every per-slice and integration artifact's spec-reconciliation notes and
`What looks solid` / `Notes for Worker 1` sections. The following work was
explicitly deferred to a future slice, future spec, or maintainer follow-up. These
are the next spec author's reading list; they are NOT gate failures (they are
out-of-scope-by-design).

- **Connection-aware optimizer planning (the empty-plan-for-every-connection-field
  constraint) → sibling card `WIP-ALPHA-033-0.0.9`.** Source: `bld-slice-3-optimizer_cooperation.md`
  `### Spec reconciliation (Worker 1)` (the confirmed-empty-plan finding) + Slice 3
  `### Final verification` + `bld-integration.md` `### Final verification`. Spec
  license: Non-goals (spec line 140), Out of scope (spec line 633), Decision 11
  "Scope honesty" (spec line 483), Edge cases (spec line 556). The `0.0.9` flat
  walker stops at a connection field's `edges`/`pageInfo`/`totalCount` root children,
  so the derived `OptimizationPlan` is empty for *every* connection field (no
  `select_related` / `prefetch_related` / `only()`, even a direct root FK). `030`
  ships only the cooperation seam (extracted `apply_to` tail + `_active_optimizer`
  ContextVar + the `apply_connection_optimization` call site); the indivisible
  `edges { node }`-recognition walker primitive is `033`'s, and it lights up root
  connection optimization with zero `connection.py` change.

- **`_validate_djangotype_target` third consumer → card `WIP-ALPHA-032-0.0.9`'s
  `DjangoNodeField`.** Source: `bld-slice-2-connection_field.md` `### Notes for
  Worker 1` (M-DRY1) + `bld-integration.md` `### Notes for Worker 1 (spec
  reconciliation)` + `### What looks solid`. No spec line licenses it (it is an
  implementation-DRY follow-up). The integration pass resolved M-DRY1 by extracting
  the shared four-guard validator into `list_field.py::_validate_djangotype_target`
  (delegated to by both `DjangoListField` and `DjangoConnectionField`); card 032's
  `DjangoNodeField` becomes the third consumer. The integration note flags that *if*
  a cluster of shared field-factory helpers accretes at 032, a dedicated `_fields.py`
  home becomes the moment-to-consider (do not pre-create now).

- **`import_spec_terms` vs `check_spec_glossary` anchor-universe mismatch → future-spec
  tooling cleanup candidate.** Source: `bld-slice-5-doc_card_wrap.md` `### Notes for
  Worker 1 (spec reconciliation)` + `### Spec changes made (Worker 1 only)`. No spec
  line licenses it; logged here as the catalog item Slice 5 promised. `import_spec_terms`
  requires every `*-terms.csv` anchor to resolve to a `GlossaryTerm`
  (`GlossaryTerm.objects.get(anchor=...)`), while `check_spec_glossary` only requires
  a matching `## H2` GitHub auto-anchor. The spec-030 terms CSV's `public-exports`
  row pointed at the `## Public exports` board-document *section* heading (not a
  `GlossaryTerm`), which hard-failed `import_spec_terms` once card 030 flipped to
  done. Worker 1 ratified the minimal fix (remove the anomalous row — it was the only
  non-`GlossaryTerm` anchor across all `docs/**/*-terms.csv`). The deeper tooling
  tension (two tools, two anchor-universe definitions) is the cleanup candidate.

- **No production cache-clear hook for `connection.py`'s `_connection_type_cache` →
  maintainer / future-slice follow-up if finalization re-runs need it.** Source:
  `bld-slice-1-connection_base.md` `### Notes for Worker 1 (spec reconciliation)`
  ("No production cache-clear hook") + Worker 2's build-report note. No spec line
  licenses it. The module-level connection-type cache is cleared only in the test
  fixture; production never calls `registry.clear()` outside tests, so no hook was
  added. Flagged so it is not assumed delivered: if a future slice's live usage
  interacts with a finalization re-run that recreates types, revisit whether
  `registry.clear()` should also invalidate the connection-type cache.

- **`Meta.cursor_field` stable column-based cursors → deferred to a future release
  (`BACKLOG.md` item 39 sub-feature 3).** Source: spec Decision 9 (spec line 459),
  Non-goals (spec line 146), Edge cases `after:`-under-concurrent-mutation
  (spec line 547). Not raised as a new deferral in any build artifact (the build
  shipped opaque offset cursors as designed), but it is the spec-pinned deferral the
  catalog should carry forward for the next author: `0.0.9` uses Strawberry's opaque
  base64 offset cursors; stable column cursors (`Meta.cursor_field`) are out of scope
  and live in BACKLOG.

- **`search:` connection argument → `Meta.search_fields` (`0.1.2`).** Source: spec
  Non-goals (spec line 142), Out of scope (spec line 635); reflected in the Slice 2
  checklist ("`search:` is NOT generated") and Slice 5's `DjangoConnectionField`
  GLOSSARY-body honesty edit (search reserved, not generated in `0.0.9`). The
  connection field reserves the seam but generates no `search:` argument until search
  ships. (Likewise `FieldSet`/`Meta.fields_class` at `0.1.1` and
  `AggregateSet`/`Meta.aggregate_class`/the `aggregates` argument at `0.1.3` are spec
  Non-goals / Out-of-scope pointers — spec lines 57-58, 143 — layering onto the
  connection field after it ships.)

- **No per-field `Meta.connection` / `total_count` override → out of scope by
  Decision 5 (Meta-only derivation).** Source: spec Decision 5 (spec lines 362-389),
  Decision 6 (no per-connection-field input types, spec line 406). Not a future-slice
  deferral with a card, but recorded because the artifacts reference it as a
  deliberate non-goal: the factory takes no `filters=` / `order=` / `total_count=`
  kwargs and generates no per-field input type; one connection shape per node type.

## Fix pass (Worker 2)

All three defect classes from the gate diagnosis were fixed in a single coupled
pass. No version / public-surface / `CHANGELOG.md` / `docs/GLOSSARY.md` change.

### Files touched

- `django_strawberry_framework/connection.py` — **Class C** (owning slice: Slice 4
  surfaced it; root cause Slices 1/2). Removed the two module-scope imports
  `from .filters import filter_input_type` / `from .orders import order_input_type`
  and re-introduced them as function-local imports at the top of
  `_synthesized_signature` (the only call site — they were used only at lines
  ~422/~433 inside the `filterset_class` / `orderset_class` branches). A comment
  documents why (lazy-subpackage contract).
- `tests/test_connection.py` — **Class A** (owning slices: Slice 1 + Slice 2).
  Changed the three DB-touching `async def` tests from plain `@pytest.mark.django_db`
  to `@pytest.mark.django_db(transaction=True)` so their seeded rows roll back
  (truncate on teardown) instead of leaking into later sync `django_db` tests.
- `tests/base/test_init.py` — **Class B** (owning slice: Slice 4). Added
  `"DjangoConnection"` and `"DjangoConnectionField"` to the expected `__all__`
  tuple in `test_public_api_surface_is_pinned`, in alphabetical position between
  `"BigInt"` and `"DjangoListField"` (matching `__init__.py`). `test_version` was
  NOT touched — `__version__` stays `0.0.8` (Decision 13).

### Tests touched

- Class A: three async-isolation marker changes in `tests/test_connection.py`
  (`test_total_count_async_path_counts_via_acount`,
  `test_async_consumer_resolver_iterable_with_total_count_selected_raises`,
  `test_connection_resolver_async_dispatch`). Behavioral assertions unchanged —
  only the `transaction=True` DB-isolation kwarg added.
- Class B: the surface-pin expected tuple in
  `tests/base/test_init.py::test_public_api_surface_is_pinned` (2 names added).

### Validation run (focused; no `--cov*`)

- `uv run pytest tests/test_connection.py tests/base/test_init.py tests/filters/test_finalizer.py tests/orders/test_inputs.py --no-cov` → **105 passed**
  (clears Class B's `test_public_api_surface_is_pinned` and Class C's two
  `registry_clear`-without-import tests).
- All 9 previously-failing cases together (3 leaking async tests + the 6 polluted
  products/admin/commands/services/api cases) → **9 passed** (clears Class A).
- Exact gate bisection repro
  (`tests/test_connection.py::test_total_count_async_path_counts_via_acount` +
  `examples/fakeshop/apps/products/tests/test_services.py::test_seed_data_creates_expected_counts`)
  → **2 passed** (was `assert 0 == 25`).
- Broad no-leak subset
  (`tests/test_connection.py tests/base/ tests/filters/ tests/orders/ tests/optimizer/test_extension.py`)
  → **525 passed**.
- Class C direct proof: `DJANGO_SETTINGS_MODULE=config.settings python -c "import django; django.setup(); import django_strawberry_framework; ..."` →
  `filters imported: False`, `orders imported: False` (bare package import no
  longer eagerly pulls the subpackages).
- `uv run ruff format .` → `234 files left unchanged` (only the standing benign
  `COM812`-vs-formatter config warning). `uv run ruff check --fix .` →
  `All checks passed!`. No tooling churn introduced.
- `git status --short` classification: the three files I touched are
  `django_strawberry_framework/connection.py` (untracked `??` — the build's new
  module), `tests/test_connection.py` (untracked `??` — the build's new test
  file), `tests/base/test_init.py` (` M` — surface-pin edit). All other entries
  in `git status --short` are pre-existing build/baseline-dirty state from prior
  slices (e.g. `CHANGELOG.md`, `docs/GLOSSARY.md`, `list_field.py`,
  `examples/fakeshop/db.sqlite3`, the `bld-*.md` artifacts) — untouched this pass.

### Implementation notes

- **Class C — import deferral.** `filter_input_type` and `order_input_type` are
  invoked only inside `_synthesized_signature`, and that function only runs at
  field-construction time (schema build), so a single function-local import at the
  top of `_synthesized_signature` is the minimal correct fix. Both branches
  (`filterset_class` / `orderset_class`) reference the helpers, so one import each
  at function top — not inside the `if` blocks — keeps it readable without
  re-importing per branch. Confirmed the synthesized signature still derives the
  `filter:` / `orderBy:` arguments: `test_connection_field_derives_filter_arg_from_filterset`,
  `test_connection_field_derives_orderby_arg_from_orderset`, and
  `test_connection_field_omits_args_without_sidecars` all pass. The module-scope
  import removal left no other reference to the two helpers, so no unused-import
  churn (ruff clean).
- **Class A — `transaction=True` over band-aid seeding.** Chose proper
  transactional isolation (the standard pytest-django pattern for async DB tests)
  rather than reworking each test to seed-only-what-it-paginates, because all three
  tests legitimately need `seed_data(...)` rows to exercise the `.acount()` /
  async-dispatch paths, and `transaction=True` is the root-cause-correct fix (the
  rows now truncate on teardown). The behavioral assertions are untouched.
- **Class B — tuple-only edit.** Only the expected tuple changed; the test's
  docstring/comment and `test_version` are untouched.

### Notes for Worker 3

- The three Class-A async tests now carry `@pytest.mark.django_db(transaction=True)`.
  Under pytest-django this runs them as transactional (truncate-on-teardown) tests;
  the trade-off is they are slightly slower and run against a non-rolled-back DB
  per-test, but that is exactly what makes their seeded rows not leak. No behavioral
  assertion changed.
- Class C moved two imports to function scope inside `_synthesized_signature`
  (connection.py ~lines 415-416). Verify the deferral does not regress the
  arg-derivation tests (it does not — they pass) and that no other module-scope
  consumer of `filter_input_type` / `order_input_type` exists in `connection.py`
  (grep confirms the only references are the two function-local imports).

### Notes for Worker 1

- Re-run the exact six-command FINAL gate. Classes A/B/C are the only changes;
  the other five gate commands were already passing and are unaffected (Class C is
  behavior-preserving on SDL/args; Class A only changes DB isolation; Class B only
  the expected tuple). The focused runs above prove all 9 prior failures now pass.
- No version bump, no `__init__.py` `__all__` change (the surface was already
  correct as Slice 4 set it; only the TEST that pins it was updated, per
  Decision 14). `CHANGELOG.md` and `docs/GLOSSARY.md` were not edited
  (baseline-dirty, left as-is).
- Class C's owning-slice attribution: the regression surfaced via Slice 4's
  `__init__.py` export but the module-scope imports landed in Slices 1/2; the fix
  lives in `connection.py`. Confirm this matches your re-loop plan's slice routing.

## Review (Worker 3)

Reviewed the FINAL-gate fix pass (Worker 2): 3 files, 3 defect classes (A/B/C).
Fresh subagent; read the gate report + `## Fix pass (Worker 2)` from disk. The two
new files (`django_strawberry_framework/connection.py`, `tests/test_connection.py`)
are untracked (`??`), so their content was inspected directly rather than via
`git diff`; `tests/base/test_init.py` is tracked (` M`) and reviewed via `git diff`.

### High:

None.

### Medium:

None.

### Low:

None.

### DRY findings

None introduced by the fix. `scripts/review_inspect.py` on `connection.py`
(`docs/shadow/django_strawberry_framework__connection.overview.md`) reports the two
function-local imports at lines 415-416 inside `_synthesized_signature`, which still
spans 63 lines / **2 branch nodes** (the two `if definition.filterset_class` /
`if definition.orderset_class` checks) — unchanged from the pre-fix shape; the import
move adds no branching, so no new hotspot. Repeated string literals reported
(`order_by` 5x, `total_count` 3x) are structural parameter/attribute names predating
this pass, not fix-introduced. The single function-local import each (at the function
top, not duplicated inside the two `if` branches) is the readable shape — both
branches reference both helpers but a single top-of-function import covers both.

### Fix-by-fix correctness verdict

- **Class A (async DB leak) — CORRECT, root-cause.** The three `async def` tests that
  seed via `services.seed_data(...)` and touch the DB now carry
  `@pytest.mark.django_db(transaction=True)` at lines 285, 628, 809
  (`test_total_count_async_path_counts_via_acount`,
  `test_async_consumer_resolver_iterable_with_total_count_selected_raises`,
  `test_connection_resolver_async_dispatch`). (a) Markers changed on exactly the
  DB-leaking async tests: the fourth `async def` test
  (`test_attach_count_async_awaits_before_guard_raises`, line 593) is correctly left
  UNMARKED — it touches no DB (uses `SimpleNamespace` / plain lists), so it neither
  leaked nor needs transactional isolation. (b) Behavioral assertions unchanged: each
  still seeds, then asserts `.acount()`/edge-count/`totalCount` exactly as before —
  only the isolation kwarg was added. (c) `transaction=True` is the root-cause fix,
  not a teardown hack: a plain-`django_db` async test cannot be wrapped in the per-test
  atomic rollback (the transaction wrapper can't span the event loop), so seeded rows
  persisted; `transaction=True` switches pytest-django to truncate-on-teardown, which
  genuinely rolls the rows back. Not a band-aid.

- **Class B (surface pin) — CORRECT, tracks Decision 14.** `git diff` on
  `tests/base/test_init.py` shows ONLY `"DjangoConnection"` + `"DjangoConnectionField"`
  added to the `test_public_api_surface_is_pinned` expected `__all__` tuple, in
  alphabetical position between `"BigInt"` and `"DjangoListField"` — matching
  `__init__.py.__all__` exactly. `test_version` is UNTOUCHED: it still asserts
  `__version__ == "0.0.8"` (line 11), honoring Decision 13 (no version bump). The pin
  now tracks the authorized Decision-14 export surface; nothing else in the file changed.

- **Class C (lazy-subpackage contract) — CORRECT, root-cause.** (a) No module-scope
  `filters` / `orders` import remains in `connection.py`: `grep` shows the only
  references to `filter_input_type` / `order_input_type` are the two function-local
  imports (lines 415-416) plus their two genuine call sites (lines 431, 442). (b) The
  imports sit at the top of `_synthesized_signature`, the only call site (it runs at
  field-construction / schema-build time), with a clear comment citing the contract and
  the two pinning tests. (c) Arg derivation preserved: the SDL `filter:` / `orderBy:`
  argument synthesis (lines 430-449) is byte-unchanged; the focused arg-derivation and
  live tests pass. This fixes the abstraction (deferred import), not the test — a
  test-only relaxation would have violated the AGENTS.md root-cause standard.

### Lazy-contract proof (Class C)

```text
$ DJANGO_SETTINGS_MODULE=config.settings uv run python -c \
  "import django; django.setup(); import django_strawberry_framework, sys; \
   print('filters in sys.modules:', 'django_strawberry_framework.filters' in sys.modules); \
   print('orders  in sys.modules:', 'django_strawberry_framework.orders'  in sys.modules)"
filters in sys.modules: False
orders  in sys.modules: False
```

Bare `import django_strawberry_framework` no longer pulls `filters` / `orders` into
`sys.modules` — the lazy-subpackage contract holds.

### Focused-test verification (no `--cov*`)

- `uv run pytest tests/test_connection.py tests/base/test_init.py
  tests/filters/test_finalizer.py::test_registry_clear_works_without_filters_imported
  tests/orders/test_inputs.py::test_registry_clear_works_without_orders_imported
  examples/fakeshop/apps/products/tests/test_services.py --no-cov` → **65 passed**
  (clears Class B's surface pin, Class C's two `registry_clear` lazy-import tests, and
  the polluted services suite).
- Exact gate bisection repro
  (`tests/test_connection.py::test_total_count_async_path_counts_via_acount` +
  `examples/fakeshop/apps/products/tests/test_services.py::test_seed_data_creates_expected_counts`)
  → **2 passed** (was `assert 0 == 25` at the gate).
- Leaking async tests + all previously-polluted product trees
  (`tests/test_connection.py` + products `test_admin.py` + `test_commands.py` +
  `test_query/test_products_api.py`) → **89 passed** (clears Class A end-to-end).
- `uv run ruff check` on the three fix files → `All checks passed!` (the module-scope
  import removal left no unused-import churn).

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` shows only the prior Slice-4
baseline (the `from .connection import DjangoConnection, DjangoConnectionField  # noqa:
E402` line + the two `__all__` names). The FIX pass made **zero** change to
`__init__.py` — the public surface was already correct as Slice 4 set it (authorized
by Decision 14, spec line 517); only the pinning TEST in `tests/base/test_init.py` was
updated to match. `__version__` is `0.0.8` (`__init__.py` line 27); `pyproject.toml`
`version = "0.0.8"` — both unchanged, per Decision 13. No new public name.

### CHANGELOG sanity

Not applicable; the fix pass did not modify `CHANGELOG.md`. (`CHANGELOG.md` shows ` M`
in `git status` but that is pre-existing Slice-5 baseline-dirty state — untouched by
this fix.)

### Documentation / release sanity

Not applicable. The fix touched no docs, no release surface: `docs/GLOSSARY.md`,
`docs/spec-030-connection_field-0_0_9.md`, the terms CSV, KANBAN.* and all `docs/*`
entries shown in `git status` are pre-existing baseline-dirty state from prior slices,
not modified by the fix pass. No version-file edit. Scope is exactly the 3 intended
files (`connection.py`, `tests/test_connection.py`, `tests/base/test_init.py`); no
scope creep.

### What looks solid

- All three fixes are root-cause, not band-aids: real transactional isolation for the
  async leak, the surface pin tracking the authorized export, and a genuine
  import-deferral that keeps the package import lazy while preserving arg derivation.
- The async-test marker change is surgically scoped — the one async test that does NOT
  touch the DB was correctly left alone, so no test was made needlessly transactional.
- The function-local import carries a precise comment naming both the contract and the
  two tests that pin it, so the non-obvious "why is this import inside the function"
  is self-documenting against future re-hoisting.
- `test_version` and `__init__.py` were both left untouched, holding the Decision-13
  version freeze and confirming the export surface was already correct.

### Temp test verification

None created. The fix is small and fully verifiable by the existing permanent suite;
the previously-failing tests now pass, the bisection repro passes, and the
lazy-contract subprocess proof is direct. No `docs/builder/temp-tests/final-fix/`
artifacts. Disposition: not needed.

### Notes for Worker 1 (spec reconciliation)

None. No spec reconciliation is required: the fix is behavior-preserving on SDL/args
(Class C), DB-isolation-only (Class A), and an authorized surface-pin update (Class B,
Decision 14). The Decision-13 version freeze and Decision-14 export surface both hold.
The deferred-work catalog above is unchanged by this pass.

### Review outcome

**review-accepted.** 0 High / 0 Medium / 0 Low. All three defect classes are fixed at
root cause, scope is exactly the 3 intended files, no public-surface / version /
CHANGELOG / GLOSSARY / spec drift, and every previously-failing case now passes under
focused runs. The build is ready for Worker 1 to re-run the full six-command FINAL gate.

## Final verification (Worker 1) — gate re-run

Re-ran the EXACT six-command FINAL test-run gate from a fresh subagent (read all
sections from disk) after the fix loop (Worker 2 fixed all three defect classes;
Worker 3 re-reviewed: `review-accepted`, 0 findings). All six commands pass.

| # | Command | Result |
|---|---------|--------|
| 1 | `uv run pytest --no-cov` | **PASS** — 1411 passed, 3 skipped, 2 warnings (68.34s); 0 failed |
| 2 | `uv run python examples/fakeshop/manage.py check` | PASS — `System check identified no issues (0 silenced).` |
| 3 | `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run` | PASS — `No changes detected` |
| 4 | `uv run ruff format --check .` | PASS — `234 files already formatted` (exit 0; the standing benign `COM812`-vs-formatter config warning only) |
| 5 | `uv run ruff check .` | PASS — `All checks passed!` (exit 0) |
| 6 | `git diff --check` | PASS — no output (exit 0; no whitespace errors / conflict markers) |

The explicit `--no-cov` was used for the pytest sweep (required — `pytest.ini`
`addopts` auto-applies `--cov`). No other coverage-shaped flag was passed; line
coverage was not inspected.

**All 9 prior failures are resolved.** Ran the 9 previously-failing node IDs together
(6 Class-A polluted products/admin/commands/services/api cases + the Class-B surface
pin + the 2 Class-C lazy-import `registry_clear` tests) → **9 passed**. The full sweep
count moved from `9 failed, 1402 passed` (first gate run) to `1411 passed, 3 skipped`
(this run): the 9 failures flipped to passes and the previously-passing 1402 are
intact (1402 + 9 = 1411).

**Version / surface freeze (Decision 13/14) confirmed.** `__version__` stays `"0.0.8"`
in `django_strawberry_framework/__init__.py` and `CHANGELOG.md` carries no release
heading — correct, not a failure. The only baseline-dirty file (`docs/GLOSSARY.md`,
regenerated from the DB by Slice 5) is coherent and `git diff --check` does not flag
it.

**Deferred work catalog.** The `## Deferred work catalog` recorded in the first gate
run (the 7 deferral bullets: connection-aware optimizer planning → card 033;
`_validate_djangotype_target` third consumer → card 032; `import_spec_terms` vs
`check_spec_glossary` anchor mismatch; no production cache-clear hook for
`_connection_type_cache`; `Meta.cursor_field` stable cursors → BACKLOG; `search:` /
`FieldSet` / `AggregateSet` future-spec pointers; no per-field `Meta.connection`
override) is still present and accurate above — unchanged by the fix loop (the fixes
were behavior-preserving on SDL/args, DB-isolation-only, and an authorized surface-pin
update). Not duplicated here; see the `## Deferred work catalog` section above.

**Status set to `final-accepted`.** All six gate commands pass. The build is complete
and ready for Worker 0 to mark the final checklist box and hand off to the maintainer.
