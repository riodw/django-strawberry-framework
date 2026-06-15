# Build: Final test-run gate — permissions / 0.0.10 (034)

Spec reference: `docs/spec-034-permissions-0_0_10.md`
Build plan: `docs/builder/build-034-permissions-0_0_10.md`
Status: final-accepted

Worker 1 final test-run gate. The cross-slice integration pass (`bld-integration.md`) is
`final-accepted`; this is the build's last gate before maintainer handoff. The gate is a
**read-only** verification: every command below was run from the repo root with no `--fix`, no
`--cov*` flag, and no working-tree mutation. STANDING GUARD honored — no `git checkout` /
`restore` / `stash` / `reset`; no source / test / spec edit in this pass (the one gate failure is
recorded and routed back through its owning slice, not fixed here).

Date: 2026-06-15. Environment: Python 3.14.2, Django 6.0.5, pytest 9.0.3.

---

## Gate command results (run in order, recorded verbatim)

### 1. `uv run pytest --no-cov` — **FAIL**

Summary line: **`1 failed, 1947 passed, 4 skipped in 90.26s`**.

The explicit `--no-cov` opts out of `pytest.ini`'s auto-applied `--cov` (plain `uv run pytest` is a
forbidden coverage run). Line coverage was NOT inspected.

Failing node:

```
FAILED examples/fakeshop/apps/products/tests/test_schema.py::test_project_schema_traverses_products_relations
```

Failure excerpt (`examples/fakeshop/apps/products/tests/test_schema.py:121`):

```
assert got_item_category == expected_item_category
AssertionError: Left contains 6 more items:
{'automotive_24ff574d': 'automotive', 'doi_d4345d1f': 'doi', 'file_c723c6e4': 'file',
 'job_18285c1c': 'job', ...}
```

The anonymous-user in-process query returned `Item`s that sit under **private** categories — i.e.
the activated products-schema cascade `get_queryset` hook (spec-034 Slice 4) was NOT applied to the
`Item` type when this test ran inside the full sweep. (The sibling
`test_project_schema_executes_products_categories_list`, which only exercises the top-level
`allCategories` narrowing, PASSES — only the `allItems` / nested-`items` relations test fails.)

The 4 skips are expected: the `FAKESHOP_SHARDED`-gated multi-DB tests do not run under a bare
invocation (build plan "Multi-DB test harness gate"; spec [Decision 8]). The single collection-time
skip (`collected 1951 items / 1 skipped`) is likewise expected and not a failure.

#### Root cause (diagnosed, not fixed)

A **deterministic cross-tree test-isolation defect** (no random-ordering plugin is installed —
`pytest-randomly` absent — so the full-sweep order is the fixed collection order). The failure is
not flaky; it reproduces every run.

- The test passes in isolation (`... -vv` → `1 passed`) and passes when the **products** test trees
  run alone.
- It FAILS when a **non-products** live HTTP suite from `examples/fakeshop/test_query/` runs before
  it. Bisected polluters (each reproduces the failure as a 2-file run):
  `test_glossary_api.py`, `test_kanban_api.py`, `test_library_api.py`, `test_scalars_api.py`,
  `test_scalars_filter_api.py`. `test_products_api.py` does **NOT** pollute (it reloads the products
  schema before composing `config.schema`).
- Mechanism: each polluting live suite's autouse reload fixture (e.g.
  `test_glossary_api.py::_reload_project_schema_for_acceptance_tests`) does `registry.clear()`, then
  reloads **only its own** app schema module + `importlib.reload(config.schema)`. It does NOT reload
  `apps.products.schema`, so the global registry has no products `DjangoType`s (with their activated
  cascade hooks) at the moment `config.schema` is composed. The resulting **cached** `config.schema`
  module holds a project schema whose products `Item` type lacks the cascade `get_queryset`.
- The in-process products suite's `project_schema` fixture
  (`examples/fakeshop/apps/products/tests/test_schema.py::project_schema`) then calls
  `importlib.import_module("config.schema")`, which returns that **already-cached, stale** module —
  `import_module` does NOT reload, and the fixture does NOT re-register `apps.products.schema` first.
  The fixture docstring claims it "binds the registry-current schema, mirroring the live suite's
  reload discipline," but the live products suite's `_reload_products_project_schema` reloads
  `apps.products.schema` **then** `config.schema`; the in-process fixture skips that first reload, so
  the mirror is incomplete.

#### Owning slice + routing

**Owner: Slice 4 (`docs/builder/bld-slice-4-products_activation.md`).** Slice 4 introduced both the
products-schema activation and the `project_schema` in-process fixture whose reload discipline is
incomplete. Per the gate protocol, the fix re-loops through Slice 4: Worker 1 plans the fix
(candidate direction: have the `project_schema` fixture reload `apps.products.schema` before
re-importing/reloading `config.schema`, mirroring `test_products_api.py::_reload_products_project_schema`,
so the products cascade hooks are registered before the composed schema is bound — final shape is
the planning pass's call), Worker 0 dispatches Worker 2 (apply) → Worker 3 (review) → Worker 1
re-runs this gate. This gate pass does **not** fix it.

### 2. `uv run python examples/fakeshop/manage.py check` — **PASS**

Output: `System check identified no issues (0 silenced).` (exit 0). No model/admin/url config drift.

### 3. `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run` — **PASS**

Output: `No changes detected` (exit 0). Model state is migration-consistent; no model/admin drift.

### 4. `uv run ruff format --check .` — **PASS**

Output: `267 files already formatted` (exit 0). The single emitted line — the standing
`COM812 may cause conflicts when used with the formatter` warning — is the repo's pre-existing config
notice (every run emits it; it does not fail the check and is not a build defect). Read-only; no
`--fix` passed.

### 5. `uv run ruff check .` — **PASS**

Output: `All checks passed!` (exit 0). Read-only; no `--fix` passed.

### 6. `git diff --check` — **PASS**

No output, exit 0. No whitespace errors and no conflict markers anywhere in the working tree
(includes the out-of-scope concurrent-sweep baseline files — none flag).

---

## Gate verdict

| # | Command | Result |
|---|---|---|
| 1 | `uv run pytest --no-cov` | **FAIL** — `1 failed, 1947 passed, 4 skipped` |
| 2 | `uv run python examples/fakeshop/manage.py check` | PASS |
| 3 | `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run` | PASS |
| 4 | `uv run ruff format --check .` | PASS (`267 files already formatted`) |
| 5 | `uv run ruff check .` | PASS (`All checks passed!`) |
| 6 | `git diff --check` | PASS (clean) |

Five of six gate commands pass. Command 1 (the full pytest sweep) fails on a single
deterministic cross-tree test-isolation defect owned by **Slice 4**. Because the gate requires all
six to pass for `final-accepted`, this artifact is `revision-needed`.

> **Superseded by the gate RE-RUN below.** This first run's record is preserved verbatim for the
> audit trail; the Slice-4 gate-fix loop subsequently repaired the `project_schema` test-isolation
> defect (pass 2, Worker-3 re-accepted), and the re-run below is now GREEN. The current
> artifact-level `Status:` reflects the re-run, not this superseded first run.

---

## Gate RE-RUN (Worker 1, after Slice-4 gate-fix) — all six PASS

Date: 2026-06-15. Environment: Python 3.14.2, Django 6.0.5, pytest 9.0.3. Same read-only protocol as
the first run (every command from repo root; no `--fix`, no `--cov*`, no working-tree mutation;
STANDING GUARD honored — no `git checkout` / `restore` / `stash` / `reset`; no source / test / spec
edit in this pass). This re-run was triggered by the Slice-4 gate-fix
(`docs/builder/bld-slice-4-products_activation.md`, build report pass 2, Worker-3 pass-2
review-accepted) which repaired the `project_schema` in-process fixture's incomplete reload
discipline.

### 1. `uv run pytest --no-cov` — **PASS**

Summary line: **`1948 passed, 4 skipped in 90.10s`**.

The prior run's single failure —
`examples/fakeshop/apps/products/tests/test_schema.py::test_project_schema_traverses_products_relations`
— now **PASSES** (also confirmed in isolation: targeted node run → `1 passed in 1.78s`). The
full-sweep count moved from the prior `1 failed, 1947 passed` to `1948 passed` (the previously-failing
test joins the passing set; total node count is unchanged), confirming the gate-fix landed cleanly
with **no new regressions** anywhere in the suite. The `--no-cov` opts out of `pytest.ini`'s
auto-applied `--cov`; line coverage was NOT inspected.

The 4 skips are the expected `FAKESHOP_SHARDED`-gated multi-DB tests (build plan "Multi-DB test
harness gate"; spec [Decision 8]) — expected, not failures.

The gate-fix mechanism (per the Slice-4 pass-2 report): the in-process `project_schema` fixture now
reloads `apps.products.schema` before re-importing/reloading `config.schema`, mirroring
`test_products_api.py::_reload_products_project_schema`, so the products cascade `get_queryset` hooks
are registered in the global registry before the composed project schema is bound — closing the
deterministic cross-tree isolation hole the first run diagnosed.

### 2. `uv run python examples/fakeshop/manage.py check` — **PASS**

Output: `System check identified no issues (0 silenced).` (exit 0).

### 3. `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run` — **PASS**

Output: `No changes detected` (exit 0).

### 4. `uv run ruff format --check .` — **PASS**

Output: `267 files already formatted` (exit 0). The standing `COM812 may cause conflicts when used
with the formatter` warning is the repo's pre-existing config notice (every run emits it; it does not
fail the check and is not a build defect). Read-only; no `--fix` passed.

### 5. `uv run ruff check .` — **PASS**

Output: `All checks passed!` (exit 0). Read-only; no `--fix` passed.

### 6. `git diff --check` — **PASS**

No output, exit 0. No whitespace errors and no conflict markers anywhere in the working tree.

### Re-run gate verdict

| # | Command | Result |
|---|---|---|
| 1 | `uv run pytest --no-cov` | **PASS** — `1948 passed, 4 skipped` |
| 2 | `uv run python examples/fakeshop/manage.py check` | PASS |
| 3 | `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run` | PASS |
| 4 | `uv run ruff format --check .` | PASS (`267 files already formatted`) |
| 5 | `uv run ruff check .` | PASS (`All checks passed!`) |
| 6 | `git diff --check` | PASS (clean) |

**All six gate commands pass.** The single deterministic Slice-4 test-isolation defect from the first
run is repaired and verified by the green full sweep. This artifact is `final-accepted`.

No ruff / `git diff --check` issue surfaced in any file — neither in build-touched files (in scope)
nor in out-of-scope concurrent-sweep baseline files. The deferred-work catalog below is carried
forward unchanged (no new item surfaced in this re-run).

---

## Deferred work catalog

Union of every per-slice + integration artifact's spec-reconciliation / `What looks solid` /
`Notes for Worker 1` / `Carry-forward` sections, plus the items the integration pass seeded in its
§7. These are the next spec author's / maintainer's reading list. None of these is the cause of the
gate failure above (that is a Slice-4 test-isolation bug to be fixed in the re-loop, not a deferral).

1. **M2M / reverse-relation cascade follow-up** — *source:* Slice-1 final-verification + spec scope
   (cascade scope is single-column **forward FK / OneToOne** only; M2M and reverse relations are
   explicitly out). *Spec licence:* spec Non-goals / Risks (the Slice-1 scope-predicate edit
   `getattr(field, "column", None) is not None` deliberately excludes Django-6 M2M / GenericRelation
   whose `column` is `None`). No KANBAN card exists yet. *Description:* extending the cascade to walk
   M2M and reverse relations is a future-spec subsystem, not in this card.

2. **Async-native cascade walking** — *source:* Slice-1 plan / final-verification ([Decision 10]).
   *Spec licence:* [Decision 10] (the async twin is `sync_to_async(thread_sensitive=True)` around the
   single sync walk, deliberately no sync/async fork). *Description:* a future spec could rewrite the
   walk as a native async traversal if a real async-ORM need emerges; today the `sync_to_async` wrap
   is the correct DRY shape and no fork should be introduced.

3. **Per-`(model, fields)` walk-result memo (perf fallback)** — *source:* integration §7-adjacent /
   Slice-2 N+1 audit ([Decision 7]). *Spec licence:* [Decision 7] (lazy-subquery composition + zero
   added round-trips is the shipped guarantee; a memo is an optional optimization, not a contract).
   *Description:* if profiling later shows the repeated forward-FK walk per request is hot, a
   per-`(model, fields)` walk-result memo is the fallback optimization — deliberately not shipped now
   (no measured need; would add cache-invalidation surface).

4. **`Exists()` constraint-shape fallback** — *source:* Slice-2 optimizer cooperation ([Decision 7]).
   *Spec licence:* [Decision 7] (the cascade composes as a lazy `__in` subquery intersection). 
   *Description:* should a future backend / query shape make the `__in (SELECT …)` subquery
   intersection underperform, an `Exists()`-shaped constraint is the documented alternative — not
   needed for the shipped SQLite/Postgres path.

5. **FieldSet `044` → `046` cross-surface mis-number cluster** — *source:* integration §7 item 3 +
   Slice-5 item E / final-verification. *Spec licence:* none (left per the no-partial-multi-surface-fix
   rule). *Description:* the card-34 body's open-question prose quotes the older FieldSet card `044`
   while the live card is `TODO-BETA-046-0.1.1`; a holistic cross-surface renumber is a maintainer
   follow-up, not actioned mid-build to avoid a partial multi-surface edit.

6. **Pre-build committed-DB-vs-committed-GLOSSARY divergence** — *source:* integration §7 item 1 +
   Slice-5 Notes-for-Worker-1 item A. *Spec licence:* none (concurrent-sweep artifact predating this
   build). *Description:* 8 shipped glossary entry bodies + the `testing.relay` public-exports line
   were out of sync between the committed `db.sqlite3` and `docs/GLOSSARY.md` before this build;
   Slice 5 reconciled them INTO the DB byte-clean. Surface to the maintainer so the source of the
   pre-build divergence is understood.

7. **`docs/TREE.md` generator staleness (maintainer regenerate `build_tree_md.py`)** — *source:*
   integration §7 item 2 + Slice-5 item F. *Spec licence:* none. *Description:* `build_tree_md.py
   --check` reports `docs/TREE.md` not-up-to-date due to earlier-spec docstring/file drift a full
   regenerate would sweep in; Slice 5 did a targeted hand-edit (the right call to avoid pulling in
   unrelated drift). Recommend a separate maintainer doc-regeneration follow-up that runs the full
   `build_tree_md.py` regenerate and reviews the resulting diff.

8. **Optional `SyncMisuseError` cascade-message polish** — *source:* Slice-1 carry-forward +
   integration §6 / §7 item 6. *Spec licence:* [Decision 10] (the cascade reuses
   `utils/querysets.py::apply_type_visibility_sync`, which raises `SyncMisuseError`). *Description:*
   the reused message text names "the Relay node defaults" and a sync-`get_queryset`-rewrite recourse
   — accurate-but-generic on the cascade surface; it does not name `aapply_cascade_permissions`.
   Accepted reuse for now (the Slice-1 test pins type-name + error + closed-coroutine, not the recourse
   wording, so nothing is mis-pinned). Generalizing the message touches shared source serving three
   surfaces (Relay defaults, list-field defaults, cascade) for a specificity gain — optional future
   polish only.

9. **Residual `docs/spec-permissions.md` card-body refs** — *source:* integration §7 item 4 +
   Slice-5 item E / final-verification. *Spec licence:* none (left per the no-partial-multi-surface-fix
   rule). *Description:* the DoD order=8 inner clause + two scope/other card bullets still cite the
   pre-convention spec filename `docs/spec-permissions.md`; a maintainer follow-up should rename these
   cross-references in one sweep.

10. **Two genuinely-generic `info.context.user` teaching examples** — *source:* integration §7 item 5
    + Slice-5 final-verification. *Spec licence:* none (judged out-of-named-scope generic teaching
    demos). *Description:* the GLOSSARY `get_queryset` visibility-hook entry (shipped `0.0.1`, a
    generic single-type demo) and `TODAY.md`'s `ItemType` demo still show the bare
    `info.context.user` form. These are non-cascade generic teaching examples outside this card's
    named scope; Slice 5 left them as-is (the cascade-path `request.user` reconciliation IS consistent
    across the fakeshop hooks, GOAL.md, and the GLOSSARY cascade example). A holistic
    `info.context.user` → `request.user` cleanup across the generic teaching surfaces is a maintainer
    follow-up.

---

## Status

**Status: final-accepted.**

This reflects the **gate RE-RUN** (above), run after the Slice-4 gate-fix
(`docs/builder/bld-slice-4-products_activation.md`, build report pass 2, Worker-3 pass-2
review-accepted) repaired the `project_schema` test-isolation defect. **All six** gate commands now
pass:

| # | Command | Result |
|---|---|---|
| 1 | `uv run pytest --no-cov` | PASS — `1948 passed, 4 skipped` |
| 2 | `uv run python examples/fakeshop/manage.py check` | PASS |
| 3 | `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run` | PASS |
| 4 | `uv run ruff format --check .` | PASS (`267 files already formatted`) |
| 5 | `uv run ruff check .` | PASS (`All checks passed!`) |
| 6 | `git diff --check` | PASS (clean) |

The first run's single failure
(`examples/fakeshop/apps/products/tests/test_schema.py::test_project_schema_traverses_products_relations`)
now passes — both in the full sweep (`1948 passed`, up from the prior `1 failed, 1947 passed`, same
total node count, zero new regressions) and in isolation. The four skips remain the expected
`FAKESHOP_SHARDED`-gated multi-DB tests. The deferred-work catalog (10 items) is carried forward
unchanged; no new item surfaced. The build's last gate before maintainer handoff is GREEN.

(The first run's `revision-needed` record and the Slice-4 routing are preserved above for the audit
trail and are superseded by this re-run.)

### Memory

Appended to `docs/builder/worker-memory/worker-1.md`.
