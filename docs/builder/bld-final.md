# Build: Final test-run gate — serializer_mutations / 0.0.13 (039)

Spec reference: `docs/spec-039-serializer_mutations-0_0_13.md`
Build plan: `docs/builder/build-039-serializer_mutations-0_0_13.md`
Status: final-accepted

The gate is the last pass before maintainer handoff. It is intentionally narrow:
the full `pytest --no-cov` sweep, Django's two consistency checks, and the
read-only lint/format/diff gate. **One gate command failed** — the full test
sweep — on a **build-introduced cross-test-pollution regression owned by Slice 3**
(an async DB-committing test missing `transaction=True`). Every other gate command
passed cleanly. The build cannot be `final-accepted` until Slice 3 re-loops the
one-line test-marker fix and the sweep re-runs green.

---

## Gate results

### 1. Full test sweep — `uv run pytest --no-cov` — **FAIL**

```
======= 1 failed, 2591 passed, 4 skipped, 4 xfailed in 128.21s (0:02:08) =======
FAILED tests/test_list_field.py::test_list_field_default_resolver_applies_cascade
```

(Run with the explicit `--no-cov` required by `pytest.ini`'s auto-applied `--cov`;
no `--cov*` flag used; line coverage neither inspected nor asserted.)

**The single failure is build-introduced cross-test pollution, root-caused to Slice 3.**

- **Symptom.** `tests/test_list_field.py::test_list_field_default_resolver_applies_cascade`
  creates only `visible_item` (public category) + `hidden_item` (private category) and asserts
  the cascade-permission resolver returns `["visible_item"]`. It instead saw
  `['AsyncItem', 'visible_item']` — an `AsyncItem` row leaked in from another test.
- **Passes in isolation.** `uv run pytest tests/test_list_field.py::test_list_field_default_resolver_applies_cascade --no-cov`
  → **1 passed**. The victim test's own logic is correct; the failure is ordering-dependent
  pollution, not a logic regression in the victim.
- **Deterministically reproduced.** Forcing the suspected polluter then the victim onto one
  worker —
  `uv run pytest -n0 --dist no "tests/rest_framework/test_resolvers.py::test_async_serializer_resolver_runs_sync_body_under_sync_to_async" "tests/test_list_field.py::test_list_field_default_resolver_applies_cascade" --no-cov`
  → **1 failed, 1 passed** with the identical `['AsyncItem', 'visible_item']` diff. The polluter
  is confirmed.
- **Root cause.** `tests/rest_framework/test_resolvers.py::test_async_serializer_resolver_runs_sync_body_under_sync_to_async`
  (the Slice-3 async-pipeline test, `tests/rest_framework/test_resolvers.py:752-753`) is decorated
  with bare `@pytest.mark.django_db`, but it is an **async** test that **commits** rows
  (`AsyncCat` via `await sync_to_async(Category.objects.create)(...)` at `:804`, and `AsyncItem`
  via `await resolve_serializer_async(...)` → `serializer.save()` at `:817`). Writes made through
  `sync_to_async` run on a separate thread with their own DB connection and commit **outside** the
  test's `django_db` rollback transaction, so the rows persist after the test and pollute every
  later test that shares that xdist worker's database — here, `tests/test_list_field.py`.
- **The established pattern is unambiguous.** Every DB-committing async/transactional test in the
  victim file and in the live `examples/fakeshop/test_query/test_products_api.py` surface uses
  `@pytest.mark.django_db(transaction=True)` (the truncate-flush teardown that DOES clean up
  cross-connection commits). The Slice-3 async test is the lone DB-committing test using the bare
  marker. The synchronous tests in the same file (`:159`, `:175`, … all `.objects.create()` inside
  the test's own sync transaction) are correctly rolled back by `@pytest.mark.django_db` and are
  NOT pollution sources — the fix scope is precisely the one async test at `:752`.

**Owning slice: Slice 3** (`bld-slice-3-resolver_pipeline_live_surface.md` —
`tests/rest_framework/test_resolvers.py` is a Slice-3 deliverable, `M` in the working tree).
This is an **in-build regression** and must be fixed **in-loop**, never deferred to a background
task (`worker-1.md` "Example-model field changes ripple into package-test fixtures" / the
acceptance-suite cross-test-pollution precedent in Worker-1 memory). It is a **test-only** fix
(no production code or spec change), so it is NOT escalation-eligible — Worker 0 re-spawns
Worker 2 for the marker fix and Worker 3 to review, then Worker 1 re-runs this gate.

**Recommended fix (route to Slice 3 Worker 2):** change `tests/rest_framework/test_resolvers.py:752`
from `@pytest.mark.django_db` to `@pytest.mark.django_db(transaction=True)`. Worker 2 should also
re-confirm no other async DB-committing test in the file carries the bare marker (grep showed line
753 is the only `async def test` in the file; the rest are synchronous and correctly rolled back).
Acceptance: the full `uv run pytest --no-cov` sweep returns green, AND the polluter→victim
single-worker reproduction above passes.

### 2a. Django system check — `uv run python examples/fakeshop/manage.py check` — **PASS**

```
System check identified no issues (0 silenced).
```

### 2b. Migration consistency — `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run` — **PASS**

```
No changes detected
```

No model/admin/url drift; model state is migration-consistent.

### 3a. Format check — `uv run ruff format --check .` — **PASS**

```
295 files already formatted
```

(The `COM812`-vs-formatter warning is a pre-existing config note, not a formatting change; it
prints on every ruff invocation in this repo. Read-only; `--fix` not passed.)

### 3b. Lint check — `uv run ruff check .` — **PASS**

```
All checks passed!
```

(Read-only; `--fix` not passed.)

### 3c. Whitespace / conflict-marker check — `git diff --check` — **PASS**

Exit 0, no output — no whitespace errors or conflict markers anywhere in the working tree, in
ANY build file. Notably `git diff --check docs/feedback.md` is itself clean (exit 0): the
documented baseline-dirty `docs/feedback.md` exception was **not even triggered** (it carries no
whitespace/conflict-marker damage). The lint/format/diff gate is fully clean.

---

## `docs/feedback.md` baseline exception status

`docs/feedback.md` was recorded in the build plan preamble as baseline-dirty out-of-scope
(concurrent maintainer work, `AGENTS.md` #34 — workers do not edit, do not revert). At this gate
it produced **no** `git diff --check` finding, so the exception did not need to be invoked. No
BUILD file was flagged by `git diff --check`. The only blocking gate failure is the Slice-3 test
pollution above — unrelated to `docs/feedback.md`.

---

## Deferred work catalog

The next spec author's reading list. Walked every `bld-slice-0..4-*.md` and `bld-integration.md`
spec-reconciliation / `What looks solid` / `Notes for Worker 1` section, plus the spec's
`## Risks and open questions` (lines 3372-3471) and `## Out of scope` (lines 1240-1262)
preferred-answer follow-ups. The two integration-finalized seeds plus the Risks/Out-of-scope
future affordances are below. **Items resolved in-build are listed separately as NOT deferred**, so
the catalog is not mistaken for an open-work list.

### Deferred to the joint `0.0.13` cut / future specs

1. **Licensed joint-cut docs deferral (F8 / Decision 14).** Source: build-plan "Build-wide context
   flags" + `bld-slice-4-docs_card_wrap.md` final verification + `bld-integration.md` "Finalized
   deferred-work catalog". Spec license: Decision 14 (version-bump ownership) + F8 (release-status
   docs split) + spec lines 388 / 436-457 / 1067-1069. The following all defer to the joint `0.0.13`
   cut shared with the sibling Auth-mutations card `WIP-ALPHA-040-0.0.13`:
   - the package version bump `0.0.12 → 0.0.13` (`pyproject.toml [project].version`, `__version__`,
     `tests/base/test_init.py::test_version`, the `django-strawberry-framework` entry in `uv.lock` —
     all still `0.0.12`);
   - the GLOSSARY `shipped (0.0.13)` status flip (Slice 4 set `status_text="implemented on main,
     releasing in \`0.0.13\`"` with the status FK kept `planned` — the renderer prints `status_text`,
     not the FK);
   - the `README.md` / `docs/README.md` "Coming next" → "Shipped today" move (README Status →
     `0.0.13`);
   - the `CHANGELOG.md` release bullets — **additionally** gated on an explicit maintainer prompt
     (`AGENTS.md` "Do not update CHANGELOG.md unless explicitly instructed"; the spec describes but
     cannot authorize the edit).

2. **Out-of-scope board-hygiene: `planning_state` residue on done cards.** Source:
   `bld-slice-4-docs_card_wrap.md` final verification + `bld-integration.md` "Finalized deferred-work
   catalog" entry 2. Spec license: none (out-of-scope observation, DONE-038 precedent). A
   `planning_state="In progress"` residue lingers on done cards in the kanban DB; observed
   out-of-scope by Slice 4, not this build's to fix. Catalog only.

3. **Model-less plain `Serializer` flavor — deferred (preferred), not resolved.** Source: spec
   `## Out of scope` line 1240-1244 + `## Risks and open questions` lines 3386-3394 + Decision 6 +
   `bld-slice-3-resolver_pipeline_live_surface.md` (the `forms/resolvers.py::_run_plain_form_pipeline_sync`
   path is correctly NOT folded into the serializer pipeline, F6). Spec license: explicit "deferred"
   in the Risks item. `0.0.13` ships the `ModelSerializer`-driven contract only (resolvable model +
   uniform `node`/`result` slot). A plain model-less `serializers.Serializer` is deferred; the
   preferred future shape is a model-less sibling in the `DjangoFormMutation` mold (own metaclass +
   `{ ok, errors }` payload + `bind_serializer_mutations()`), never a weakening of the
   `ModelSerializer` contract.

4. **`Meta.model_operations` alias affordance — near-term, sequence right after `0.0.13`.** Source:
   spec `## Risks and open questions` lines 3395-3414 + `bld-slice-4-docs_card_wrap.md` (the
   reconciled GLOSSARY/TREE surface keys document `Meta.operation` over graphene's `model_operations`).
   Spec license: the Risks item names this as the preferred **near-term affordance** ("sequence it
   right after `0.0.13` if the migration friction proves real"). The package uses per-operation
   `Meta.operation`; the affordance is to accept graphene's `Meta.model_operations` as an alias that
   desugars at metaclass time into the per-operation mutations, letting the graphene migrant key
   carry over verbatim. Not built in this card.

5. **`Meta.lookup_field` non-pk locate — future fallback.** Source: spec `## Risks and open
   questions` lines 3415-3422 + `## Out of scope` lines 1256-1260. Spec license: the Risks item
   records this as the **fallback** ("a future `Meta.lookup_field` for a non-pk locate — a contained
   resolver change"). `0.0.13` keeps the `id:`-`GlobalID`-decode locate (the no-existence-leak
   contract uniform with `036`/`038`); a `Meta.lookup_field` non-pk locate is deferred.

6. **Serializer-derived / serializer-shaped output type — separate post-`1.0.0` surface.** Source:
   spec `## Risks and open questions` lines 3423-3434 + `## Out of scope` lines 1245-1251 + Decision 7.
   Spec license: the Risks "dual-purpose" item records the fallback as "a separate (post-`1.0.0`)
   surface, not this card." The converter is input-directed; the mutation output is the frozen primary
   `DjangoType` `node`/`result` slot, not a serializer-derived output type. The `is_input` parameter
   is carried for graphene parity / forward use but accepted-and-ignored (no `if not is_input:` branch).
   Nested writable serializers (`ParsedObject`-style nested create/connect) stay the `036` nested-write
   non-goal.

### Explicitly NOT deferred — resolved in-build (recorded so the catalog is not misread)

- **D8 resolver overrides (`resolve_sync` / `resolve_async`).** Slice 2 deferred these two overrides
  to Slice 3 (D8 option b — the `rest_framework/resolvers.py` module did not yet exist at Slice 2).
  **Closed in Slice 3** (`bld-slice-3-resolver_pipeline_live_surface.md` "D8 close confirmed
  explicitly" — both the `rest_framework/sets.py` overrides and the `rest_framework/resolvers.py`
  bodies landed). Not a standing deferral.
- **F-INT-1 — `relation_field_error` 3-site near-copy / `"Invalid id for relation …"` repeated
  literal.** **Closed in the integration consolidation loop** (shared `relation_field_error(graphql_name)`
  leaf ctor at `mutations/resolvers.py:864`; three byte-equivalent thin delegates; model raw-pk path
  routed transitively via the verified `_relation_error` correction; 545 focused tests green with zero
  production-test edits). Not deferred.
- **F-INT-2 — L1 vacuous-tautology test assertion** at `tests/rest_framework/test_inputs.py`. **Closed
  in the same integration loop** (vacuous line deleted; the M2 contract stays pinned by the two
  adjacent survivors). Not deferred.

(No other deferral surfaced in the slice or integration artifacts beyond the six above. The DRF floor
record — `djangorestframework>=3.17.0` — was an in-contract Slice-0 spec fill-in discharged at Slice-0
final verification, not a standing deferral.)

---

## Summary

`Status: revision-needed` (historical — gate FAIL #1, the `test_list_field` cross-test pollution
that triggered the first fix loop; RESOLVED by Worker 2's marker fix below. The authoritative
top-level `Status:` near the top of the file governs; this gate FAILED AGAIN on the re-run over a
*second, distinct* pollution defect — see `## Final verification (Worker 1) — gate re-run`). Five of
six gate commands pass cleanly:

| Gate command | Result |
| --- | --- |
| `uv run pytest --no-cov` | **FAIL** — 1 failed, 2591 passed, 4 skipped, 4 xfailed |
| `uv run python examples/fakeshop/manage.py check` | PASS — 0 issues |
| `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run` | PASS — No changes detected |
| `uv run ruff format --check .` | PASS — 295 files already formatted |
| `uv run ruff check .` | PASS — All checks passed |
| `git diff --check` | PASS — clean (exit 0); `docs/feedback.md` exception not even triggered |

The lone failure is a **build-introduced cross-test-pollution regression owned by Slice 3**:
`tests/rest_framework/test_resolvers.py::test_async_serializer_resolver_runs_sync_body_under_sync_to_async`
(`:752`) carries a bare `@pytest.mark.django_db` on an **async** test that commits rows via
`sync_to_async` / `serializer.save()`; those cross-connection commits are not rolled back and leak
an `AsyncItem` row into `tests/test_list_field.py::test_list_field_default_resolver_applies_cascade`
(passes in isolation; deterministically reproduced polluter→victim on one worker). The fix is a
one-line marker change to `@pytest.mark.django_db(transaction=True)` — a **test-only, in-loop**
Slice-3 fix (not escalation-eligible, not background-deferrable). The deferred-work catalog carries
**six** entries (two integration-finalized joint-cut/board-hygiene seeds + four Risks/Out-of-scope
future affordances), with the in-build resolutions (D8 overrides, F-INT-1, F-INT-2) recorded as
explicitly NOT deferred.

Route to Slice 3: Worker 0 re-spawns Worker 2 (marker fix) → Worker 3 (review) → Worker 1 re-runs
this gate. `final-accepted` only after the full sweep is green.

### Spec changes made (Worker 1 only)

None. The spec status header (`docs/spec-039-…md:3` — "Implemented on main; release deferred to the
joint `0.0.13` cut (card `DONE-039-0.0.13`)") is accurate to the current state and needs no edit; it
was reconciled by Slice 4's final verification. The gate failure is a test-marker defect, not a
spec gap — no spec mutation, so `scripts/check_spec_glossary.py` was not re-run.

---

## Build report (Worker 2) — gate-fix pass

`Status: built`. Applied the one-line Slice-3 test-marker fix Worker 1 root-caused. The cross-test
pollution is fixed and the full sweep is green.

### Files touched

- `tests/rest_framework/test_resolvers.py` — the single marker change below. (This file was already
  `M` in the working tree as a Slice-3 build deliverable; the gate-fix pass adds only the one line.)

### The marker change

Line 752, `test_async_serializer_resolver_runs_sync_body_under_sync_to_async`:

```diff
-@pytest.mark.django_db
+@pytest.mark.django_db(transaction=True)
 async def test_async_serializer_resolver_runs_sync_body_under_sync_to_async():
```

**Diagnosis re-confirmed before applying** (the fix matched what I saw — no STOP needed):

- Line 753 is the **only** `async def test` in `tests/rest_framework/test_resolvers.py`, and line 752
  was the **only** `@pytest.mark.django_db` in the file lacking `(transaction=True)`
  (`grep -n "pytest.mark.django_db"` → 19 markers, all the others are synchronous tests correctly
  rolled back by bare `django_db`).
- It commits rows: `AsyncCat` via `await sync_to_async(product_models.Category.objects.create)(...)`
  (`:804`) and `AsyncItem` via `await ...resolve_serializer_async(...)` → `serializer.save()`
  (`:817`). Those `sync_to_async` commits run on a separate connection and escape the test's bare
  `django_db` rollback, leaking the `AsyncItem` row into later same-worker tests.
- The established sibling form is `@pytest.mark.django_db(transaction=True)` with no extra args — every
  DB-committing async/transactional test in `examples/fakeshop/test_query/test_products_api.py`
  (`:158`, `:193`, `:235`, …) uses exactly that form. Matched it verbatim.

Only the marker was changed — no assertion edits, no resolver-source edits, no scope broadening.

### Validation run

- `uv run ruff format .` → **PASS** (295 files left unchanged; the `COM812`-vs-formatter warning is the
  pre-existing config note, not a change).
- `uv run ruff check --fix .` → **PASS** (All checks passed; no autofix churn).
- **Polluter→victim, single worker (proves the pollution is fixed):**
  - `uv run pytest -n0 --dist no -p no:randomly tests/rest_framework/test_resolvers.py tests/test_list_field.py --no-cov`
    (polluter file physically before victim file on one worker) → **50 passed**.
  - `uv run pytest -n0 --dist no "…::test_async_serializer_resolver_runs_sync_body_under_sync_to_async" "…::test_list_field_default_resolver_applies_cascade" --no-cov`
    (the gate's exact node-id pair) → **2 passed**. The victim no longer sees the leaked `AsyncItem`
    row; `transaction=True`'s truncate-flush teardown cleans the cross-connection commits regardless
    of collection order.
- **Full sweep:** `uv run pytest --no-cov` → **2592 passed, 4 skipped, 4 xfailed in 127.59s** — fully
  green (the previously-failing `test_list_field_default_resolver_applies_cascade` is now in the
  2592 passed; net +1 over the gate's `1 failed, 2591 passed`). Explicit `--no-cov`; no `--cov*` flag.
- `git status --short` after ruff: the working tree carries the full pre-existing uncommitted spec-039
  build (all the `M` source/docs/test files were already modified before this pass; `db.sqlite3` and
  `docs/feedback.md` untouched by me — the sweep uses a separate test database). My net contribution
  this pass is the single marker line in `tests/rest_framework/test_resolvers.py`. No tool churn to
  revert.

### Implementation notes

- Forced single-worker ordering with `-n0 --dist no` (the gate's form), not `-p no:xdist` — `pytest.ini`
  passes `-n auto --dist loadscope`, and `-p no:xdist` unregisters the plugin while leaving those args
  unrecognized (errors out). `-n0 --dist no` keeps the plugin loaded but pins one worker.
- pytest collects in file-sort order, so `tests/test_list_field.py` sorts before `tests/rest_framework/`;
  the airtight polluter-before-victim proof is therefore the whole-resolvers-file-first run (50 passed),
  with the node-id pair as the corroborating second check. With `transaction=True` the cleanup is
  order-independent, so both pass.

### Notes for Worker 3

- Single-line, test-only marker change. Diff to review: `tests/rest_framework/test_resolvers.py:752`
  `@pytest.mark.django_db` → `@pytest.mark.django_db(transaction=True)`. No production code, no spec,
  no assertion changes.
- No shadow files used.
- The full sweep is green at 2592 passed; no checkbox ticks were owed (this is a gate-fix pass on a
  test-marker defect, not a slice sub-check landing).

---

## Review (Worker 3) — gate-fix

`Status: review-accepted`. The one-line gate-fix is correct, matches the established codebase
pattern, root-causes (not papers over) the pollution, and my independent full `--no-cov` sweep is
fully green. No new findings.

### The diff under review (narrow — one line)

The gate-fix's net contribution is the single marker change at `tests/rest_framework/test_resolvers.py:752`:
`@pytest.mark.django_db` → `@pytest.mark.django_db(transaction=True)` on
`test_async_serializer_resolver_runs_sync_body_under_sync_to_async` (line 753).

**Cumulative-diff note (not a finding).** `git diff -- tests/rest_framework/test_resolvers.py`
prints the entire 24→820-line Slice-3 rewrite, and `git diff -- django_strawberry_framework/__init__.py`
prints the Slice-2 lazy-`__getattr__` addition — both are *uncommitted prior-slice work* still in the
working tree (HEAD `test_resolvers.py` is the 24-line stub; HEAD `__init__.py` has no `__getattr__`).
Filtered against the artifact's `### Files touched`, the gate-fix pass's own contribution is exactly
the one marker line. Verified mechanically:
- `grep -n "pytest.mark.django_db" tests/rest_framework/test_resolvers.py` → 19 markers; line 752 is
  the **only** one carrying `(transaction=True)`; the other 18 are bare on synchronous tests.
- `grep -n "async def test" tests/rest_framework/test_resolvers.py` → line 753 is the **only** async
  test in the file. The marker scope is precisely correct: the lone async committer carries the lone
  `transaction=True`.

No assertion change, no resolver-source change, no scope broadening. Confirmed.

### Root-cause vs band-aid

The change is the correct root-cause fix, not a mask:
- The test genuinely commits rows outside the `django_db` rollback transaction: `AsyncCat` via
  `await sync_to_async(product_models.Category.objects.create)(...)` (`:804`) and `AsyncItem` via
  `await serializer_resolvers.resolve_serializer_async(...)` → `serializer.save()` (`:817`). Those
  `sync_to_async` writes run on a separate thread/connection and commit outside the bare-`django_db`
  rollback, so the rows survive teardown and pollute later same-worker tests (the observed
  `['AsyncItem', 'visible_item']` leak into `tests/test_list_field.py`). `transaction=True`'s
  truncate-flush teardown is exactly the mechanism that reclaims cross-connection commits — so the
  marker is the correct fix for the actual failure mode, not a reorder/skip band-aid.
- It is NOT papering over a resolver bug. The async pipeline running `serializer.save()` under
  `sync_to_async` and committing a real row is the intended behavior the test exists to pin; the bug
  was purely the test's isolation marker. The assertions (`:818-820`: `payload.errors == []`,
  `payload.node is not None`, `payload.node.name == "AsyncItem"`) are unchanged — the marker change
  does not weaken what the test pins.

### Established-pattern match

`@pytest.mark.django_db(transaction=True)` (no extra args) is the codebase's unambiguous form for
DB-committing async/transactional tests: `examples/fakeshop/test_query/test_products_api.py` uses it
on every committing test (`:158`, `:193`, `:235`, … through `:949`), and the synchronous resolver
tests in the same `test_resolvers.py` correctly keep bare `@pytest.mark.django_db` (their writes roll
back inside the test's own sync transaction). The fix matches the sibling form verbatim.

### High

None.

### Medium

None.

### Low

None.

### DRY

None. A single-token marker change introduces no duplication; it brings the lone outlier into line
with the established `(transaction=True)` pattern (a DRY improvement, if anything).

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` is unchanged **by this gate-fix**. The diff it
shows is the uncommitted Slice-2 lazy-`__getattr__` addition (HEAD has no `__getattr__`); `__all__`
and the re-export tuple below it are untouched by that addition, and the gate-fix touched only the
test file. No public-surface drift from the gate-fix.

### CHANGELOG sanity

Not applicable; gate-fix did not modify `CHANGELOG.md`.

### Documentation / release sanity

Not applicable.

### Static helper

Not applicable — skipped. The change is a one-token test-marker edit with no new `.py` file, no
`optimizer/`/`types/` touch, and zero lines of new logic (well under every `review_inspect.py`
trigger threshold). Recorded skip + reason.

### Pre-existing claim verification

Worker 2 made no "pre-existing at HEAD" claim requiring the stash/checkout protocol; the regression
is build-introduced and the fix is in-loop. The relocation/promotion-claim and behavioral-claim
checks are inapplicable to a marker change (no body moved, no runtime fallback property claimed).

### Re-confirmed gate-relevant results (independent re-run)

- **Full sweep (gate's blocking command):** `uv run pytest --no-cov` →
  **2592 passed, 4 skipped, 4 xfailed in 126.93s**. Fully green; matches Worker 2's report and is
  +1 over the gate's prior `1 failed, 2591 passed`. Explicit `--no-cov`; no `--cov*` flag used.
- **Polluter→victim node-id pair (independent):**
  `uv run pytest -n0 --dist no "tests/rest_framework/test_resolvers.py::test_async_serializer_resolver_runs_sync_body_under_sync_to_async" "tests/test_list_field.py::test_list_field_default_resolver_applies_cascade" --no-cov`
  → **2 passed**. The victim no longer sees the leaked `AsyncItem` row; cleanup is order-independent.

### Temp test verification

None created — the marker semantics and the pollution fix are fully proven by the polluter→victim
pair and the green full sweep; a temp test would add nothing.

### What looks solid

The fix is minimal, correctly scoped to the lone async DB-committing test, root-causes the
cross-connection-commit leak (not a reorder/skip mask), preserves the async-pipeline assertions, and
brings the file into line with the established `(transaction=True)` sibling pattern. Both the gate's
blocking sweep and the targeted pollution reproduction are green on my independent re-run.

### Notes for Worker 1 (spec reconciliation)

None. Test-only marker fix; no spec context required.

### Review outcome

`review-accepted`. Diff is exactly the one marker line, matches the established codebase pattern,
root-causes the pollution without weakening the test, and the independent full `--no-cov` sweep is
green at 2592 passed / 4 skipped / 4 xfailed. Route to Worker 1 to re-run the final gate.

---

## Final verification (Worker 1) — gate re-run

`Status: revision-needed` (top-level). The Worker-2 marker fix for the *first* pollution defect
(`test_list_field`) is confirmed correct and holds. But the gate re-run surfaced a **second, distinct
build-introduced cross-test-pollution defect** — an intermittent `DuplicatedTypeName` in the live
products in-process schema test — so the build cannot be `final-accepted` yet. Five of six gate
commands pass cleanly; the full sweep is **flaky-FAIL** (failed 1 of 3 canonical runs).

### 1. Full test sweep — `uv run pytest --no-cov` — **FAIL (flaky / xdist-order-dependent)**

```
======= 2589 passed, 4 skipped, 4 xfailed, 3 errors in 130.07s (0:02:10) =======
ERROR examples/fakeshop/apps/products/tests/test_schema.py::test_project_schema_executes_products_categories_list
ERROR examples/fakeshop/apps/products/tests/test_schema.py::test_project_schema_traverses_products_relations
ERROR examples/fakeshop/apps/products/tests/test_schema.py::test_project_schema_includes_products_types
```

The error (identical on all three errored tests):

```
strawberry.exceptions.duplicated_type_name.DuplicatedTypeName:
    Type BookInputCirculationStatusEnum is defined multiple times in the schema
.venv/.../strawberry/schema/schema_converter.py:1040: DuplicatedTypeName
```

(Run with the explicit `--no-cov` required by `pytest.ini`'s auto-applied `--cov`; no `--cov*` flag;
coverage neither inspected nor asserted.)

**Flake-rate evidence — this is the authoritative gate result.** The canonical `uv run pytest --no-cov`
invocation was run three times this gate:

| Canonical sweep | Result |
| --- | --- |
| Run 1 (gate run) | **FAIL** — 2589 passed, 3 errors (`DuplicatedTypeName`) |
| Run 2 | PASS — 2592 passed, 4 skipped, 4 xfailed |
| Run 3 | PASS — 2592 passed, 4 skipped, 4 xfailed |

**1 of 3 canonical sweeps failed.** `pytest-randomly` is NOT installed (confirmed:
`import pytest_randomly` → `ModuleNotFoundError`; `pytest.ini` explicitly assumes "no pytest-randomly")
— so all three runs used the IDENTICAL `-n auto --dist loadscope` config. The pass/fail divergence
across identical-config runs is therefore driven purely by xdist's run-to-run **worker scheduling**
(which test modules land on which of the 8 workers, and their within-worker order), not by a config or
seed difference. A canonical-invocation gate command that fails 1-in-3 is a gate FAIL — Worker 2's and
Worker 3's lucky-green single sweeps did not exonerate the suite (this is exactly the
"green-on-one-machine ≠ isolated; verify with a polluter-matrix" precedent in Worker-1 memory).

**Passes in isolation.** `uv run pytest examples/fakeshop/apps/products/tests/test_schema.py --no-cov`
→ **3 passed**. The victim file's own logic is correct; the failure is ordering/scheduling-dependent
pollution, not a logic regression.

**Root cause — partial-reload isolation gap, newly exposed by the Slice-3 live products surface.**

- The victim is the `project_schema` fixture in `examples/fakeshop/apps/products/tests/test_schema.py`
  (`examples/fakeshop/apps/products/tests/test_schema.py::project_schema`). It does a **PARTIAL**
  schema rebuild: `registry.clear()`, then `importlib.reload(apps.products.schema)`, then
  `importlib.reload(config.schema)` — re-registering ONLY the products app + the `config.schema`
  aggregate, NOT all five apps.
- `config.schema` (`examples/fakeshop/config/schema.py`) imports every app's `Query`/`Mutation`
  (including `apps.library.schema`), calls `finalize_django_types()` (materializes the
  `<Model>Input`/`<Model>PartialInput` classes from the registry), then `strawberry.Schema(...)` —
  where the duplicate-type-name check fires. `importlib.reload(config.schema)` re-executes
  `config/schema.py` but pulls `apps.library.schema` from `sys.modules` **without re-executing it**,
  so the partial reload does not deterministically reset the library app's registration footprint.
- The polluter family is the set of sibling in-process schema-building tests that share an xdist
  worker but lack the full-reload discipline — chiefly
  `examples/fakeshop/tests/test_inspect_django_type.py::test_inspect_with_schema_option`
  (`examples/fakeshop/tests/test_inspect_django_type.py #"sys.modules.pop(name, None)"`), which
  **evicts all six schema modules from `sys.modules` and clears the registry but never restores them**,
  leaving a re-imported `apps.library.schema` (a fresh `BookInput` class object) cached for whatever
  test next builds `config.schema` on that worker. When the products `project_schema` partial reload
  then runs against that accumulated state, two `BookInput` class objects can both claim
  `BookInputCirculationStatusEnum` at `Schema(...)` build → `DuplicatedTypeName`.
- **Why this is build-introduced (Slice 3).** The products `test_schema.py` partial-reload fixture is a
  pre-existing (spec-034) artifact that was order-robust before this card. Slice 3 added the live
  products `SerializerMutation` surface to `examples/fakeshop/apps/products/schema.py`
  (`CreateItemViaSerializer` / `UpdateItemViaSerializer` over `ItemSerializer`, plus the
  `from . import … serializers` import and the two `DjangoMutationField` rows). That **enlarged the
  input-type materialization footprint** that `finalize_django_types()` walks during the products
  partial reload — enough to expose the latent duplicate-registration race that the prior, smaller
  products schema never tripped. The defect rides in on a Slice-3 deliverable file
  (`examples/fakeshop/apps/products/schema.py`, `M` in the working tree); the fix belongs in the same
  live-surface slice that introduced it.

**Reproduction notes (for the fix-loop worker).** The defect is multi-process: it requires a specific
accumulation of schema-module/registry state across modules sharing one xdist worker. It did NOT
reproduce in a single-process simulation of the obvious polluter→victim pair, nor in a 5-cycle
`reload_all → polluter → victim` in-process loop, nor in targeted two-file `-n0` pairings (the file
sort places `apps/...` before `tests/...`, so naive node-id pairing runs the victim first). Do not
treat "passes in a single targeted pairing" as proof of a fix — validate with a **repeated full
`uv run pytest --no-cov` sweep (run it 4-6×; it must be green EVERY time)**, the discipline the
flake demands.

**Recommended root-cause fix (route to Slice 3 — test-only, in-loop, NOT escalation-eligible, NOT
background-deferrable).** Bring the products in-process schema test onto the same **full**-reload
discipline every `examples/fakeshop/test_query/` acceptance file already uses
(`reload_all_project_schemas` in `examples/fakeshop/test_query/conftest.py`, which clears the registry
and re-imports/reloads ALL five app schemas in dependency-safe order before reloading `config.schema`,
making the rebuild complete and order-independent). The preferred shape:
  1. Convert the partial `project_schema` fixture in
     `examples/fakeshop/apps/products/tests/test_schema.py` to a **complete** project rebuild (all five
     apps, then `config.schema`), not a products-only reload — the same fix shape that closed the
     acceptance-suite cross-test-pollution precedent (Worker-1 memory: "shared complete-reload conftest
     helper"). Factor the reload into a shared helper an `examples/fakeshop/apps/` (or a per-app)
     conftest can expose, rather than re-forking the `test_query/conftest.py` logic, to keep the reload
     discipline single-sited.
  2. Fix the polluter to not leave the worker dirty: have
     `examples/fakeshop/tests/test_inspect_django_type.py::test_inspect_with_schema_option` **restore**
     the schema modules / re-finalize a complete project schema on teardown (the same complete-reload
     helper), so the cold-`--schema` simulation does not strand a half-registered
     `apps.library.schema` in `sys.modules` for the next test on the worker.
  Whichever side is fixed, the acceptance bar is the same: a **repeated** full `uv run pytest --no-cov`
  sweep green every time. (Recommendation only — Worker 1 does not implement; this routes back to
  Worker 0 for a Slice-3 fix loop.)

### 2a. Django system check — `uv run python examples/fakeshop/manage.py check` — **PASS**

```
System check identified no issues (0 silenced).
```

### 2b. Migration consistency — `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run` — **PASS**

```
No changes detected
```

### 3a. Format check — `uv run ruff format --check .` — **PASS**

```
295 files already formatted
```

(The `COM812`-vs-formatter warning is the pre-existing config note that prints on every ruff
invocation in this repo, not a formatting change. Read-only; `--fix` not passed.)

### 3b. Lint check — `uv run ruff check .` — **PASS**

```
All checks passed!
```

(Read-only; `--fix` not passed.)

### 3c. Whitespace / conflict-marker check — `git diff --check` — **PASS**

Exit 0, no output — no whitespace errors or conflict markers in ANY working-tree file, in ANY build
file. `git diff --check docs/feedback.md` is itself clean (exit 0): the documented baseline-dirty
`docs/feedback.md` exception (AGENTS.md #34) was **not even triggered** — it carries no
whitespace/conflict-marker damage. The lint/format/diff gate is fully clean.

### Summary

`Status: revision-needed`. Five of six gate commands pass cleanly; the full sweep is a flaky FAIL:

| Gate command | Result |
| --- | --- |
| `uv run pytest --no-cov` | **FAIL (flaky)** — 1 of 3 canonical runs errored: 2589 passed + 3 `DuplicatedTypeName` errors (runs 2 & 3: 2592 passed) |
| `uv run python examples/fakeshop/manage.py check` | PASS — 0 issues |
| `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run` | PASS — No changes detected |
| `uv run ruff format --check .` | PASS — 295 files already formatted |
| `uv run ruff check .` | PASS — All checks passed |
| `git diff --check` | PASS — clean (exit 0); `docs/feedback.md` exception not even triggered |

The blocking failure is a **second, distinct build-introduced cross-test-pollution defect owned by
Slice 3** (separate from the now-resolved `test_list_field` marker defect): the products in-process
schema test `examples/fakeshop/apps/products/tests/test_schema.py` errors with an intermittent
`DuplicatedTypeName: Type BookInputCirculationStatusEnum is defined multiple times` because its
`project_schema` fixture does a **partial** registry reload (products + `config.schema` only, not all
five apps) — a latent spec-034 isolation gap **newly exposed** by Slice 3's live products
`SerializerMutation` surface enlarging the `finalize_django_types()` input-materialization footprint,
and tripped by sibling worker-dirtying tests (chiefly
`test_inspect_with_schema_option`'s un-restored `sys.modules.pop`). It is **test-only**, so **in-loop**
(re-loop Slice 3, never background-deferred) and **not escalation-eligible**. The fix is the
established complete-reload discipline (`reload_all_project_schemas`), validated by a **repeated** full
`--no-cov` sweep that is green every time.

**Deferred-work catalog: intact and unchanged.** Re-walked the six-entry `### Deferred work catalog`
above — no gate result changed any of it. All six entries (licensed joint-cut docs deferral incl.
version bump / GLOSSARY shipped flip / README+docs-README move / CHANGELOG; out-of-scope board-hygiene
`planning_state` residue; model-less plain `Serializer` flavor; `Meta.model_operations` alias;
`Meta.lookup_field` future locate; serializer-shaped output post-`1.0.0`) stand. F-INT-1, F-INT-2, and
the D8 overrides remain RESOLVED (NOT deferred). No version bump. No spec edit (the gate failure is a
test-isolation defect, not a spec gap; `scripts/check_spec_glossary.py` not re-run).

Route to Slice 3: Worker 0 re-spawns Worker 2 (complete-reload fix) → Worker 3 (review) → Worker 1
re-runs this gate. `final-accepted` only after a **repeated** full `uv run pytest --no-cov` sweep is
green on every run.

---

## Build report (Worker 2) — second gate-fix pass

`Status: built`. Applied the root-cause fix Worker 1 root-caused for the *second* pollution defect
(the intermittent `DuplicatedTypeName: BookInputCirculationStatusEnum` in
`examples/fakeshop/apps/products/tests/test_schema.py`). The defect is gone: **5 of 5** repeated full
`uv run pytest --no-cov` sweeps are green (the documented bar — one green is insufficient on this
~1-in-3 xdist-scheduling flake). The fix is test-only and brings the products in-process schema test
onto the same complete-reload discipline every `test_query/` acceptance file already uses, with the
reload logic DRY-promoted into a single shared module (not forked).

### Files touched

My pass's net contribution is exactly five files (3 modified, 2 new). Grounded in `git status --short`:

- **`examples/fakeshop/schema_reload.py`** (NEW) — the single source of truth for the complete-reload
  helper. Holds `reload_all_project_schemas()`, the dependency-safe `_PROJECT_APP_SCHEMA_MODULES`
  tuple, and `_reload_or_import()`, moved **verbatim** out of `test_query/conftest.py` (a `conftest.py`
  is not importable by sibling test trees, so the logic could not stay there and be reused — DRY
  required a plain importable module). Importable as `schema_reload` via `pytest.ini`'s
  `pythonpath = examples/fakeshop`. Its docstring documents BOTH partial-reload failure modes (the
  pre-existing `LazyType` `KeyError` and this card's `DuplicatedTypeName`).
- **`examples/fakeshop/test_query/conftest.py`** (M) — now imports `reload_all_project_schemas` from
  the shared `schema_reload` module and keeps its `reload_all_project_app_schemas` fixture wrapper
  unchanged in name/shape, so every acceptance file that consumes that fixture is untouched. The
  duplicated reload body is deleted (now single-sited in `schema_reload`).
- **`examples/fakeshop/apps/products/tests/conftest.py`** (NEW) — exposes the SAME
  `reload_all_project_app_schemas` fixture (backed by the same shared `reload_all_project_schemas`),
  so the products in-process schema tests rebuild on the identical complete-reload discipline. This is
  the conftest the task authorized over forking the reload logic.
- **`examples/fakeshop/apps/products/tests/test_schema.py`** (M) — the **primary fix**. The
  `project_schema` fixture no longer does a products-only **partial** reload (`registry.clear()` +
  reload `apps.products.schema` + reload `config.schema`); it now requests
  `reload_all_project_app_schemas` and calls it to rebuild ALL five apps in dependency-safe order
  before `config.schema`, then returns `sys.modules["config.schema"].schema`. The three test
  assertions are untouched.
- **`examples/fakeshop/tests/test_inspect_django_type.py`** (M) — **secondary hardening** (applied;
  see "Implementation notes" for why it was warranted). `test_inspect_with_schema_option` evicts the
  six schema modules from `sys.modules` and clears the registry to simulate a cold `--schema` CLI
  process, but never restored them — stranding a half-registered `apps.library.schema` for the next
  same-worker test. Wrapped the command-run + asserts in `try` / `finally`; the `finally` calls the
  shared `reload_all_project_schemas()` to restore a complete, finalized project schema on teardown.
  The six assertions are byte-identical (only wrapped, not changed).

`docs/feedback.md` and `examples/fakeshop/db.sqlite3` show `M` in the working tree but are NOT my
edits — they are the build plan's recorded baseline-dirty / concurrent-writable files (`AGENTS.md`
#34); I did not touch either (the sweeps use a separate test database). No tool churn to revert.

### The diagnosis matched — no STOP needed

Worker 1's diagnosis matched exactly what I found, so I applied the root-cause fix without a STOP:

- The canonical complete-reload helper is `reload_all_project_schemas` in
  `examples/fakeshop/test_query/conftest.py`, exposed via the `reload_all_project_app_schemas` fixture,
  and consumed by every `test_query/` acceptance file (`test_products_api.py`, `test_library_api.py`,
  … — confirmed via `grep`). The products `test_schema.py::project_schema` fixture was the lone
  in-process schema test still on a **partial** reload.
- There was **no** pre-existing `conftest.py` under `examples/fakeshop/apps/` or
  `examples/fakeshop/apps/products/tests/`, and **no** plain shared test-support module — so the reload
  logic genuinely lived only inside `test_query/conftest.py`. Promoting it to `schema_reload.py` (a
  plain module) is the DRY-correct move the task preferred over a near-copy fork.
- The polluter `test_inspect_with_schema_option` does `sys.modules.pop(name, None)` for all six schema
  modules + `registry.clear()` and never restores them — confirmed by reading the test.

### Reproduce step (per the mandatory reproduce-then-fix bar)

- **Pre-fix, attempted reproduction.** Worker 1's gate re-run already deterministically established the
  flake at **1 of 3** canonical full sweeps (`bld-final.md` "Final verification (Worker 1) — gate
  re-run", run-matrix table), with the identical `DuplicatedTypeName: BookInputCirculationStatusEnum`.
  I relied on that authoritative gate evidence plus a fresh targeted polluter+victim file-set run; the
  defect is multi-process (it needs an accumulation of schema-module/registry state across modules
  sharing one xdist worker), so — exactly as Worker 1's reproduction notes warned — it does NOT
  reliably reproduce in a single targeted pairing. The authoritative bar is therefore the **repeated
  full sweep**, which is what I validated against below.
- **Post-fix, focused wiring proof:** `uv run pytest --no-cov` over
  `examples/fakeshop/apps/products/tests/test_schema.py` + `examples/fakeshop/tests/test_inspect_django_type.py`
  + `examples/fakeshop/test_query/test_products_api.py` + `examples/fakeshop/test_query/test_library_api.py`
  → **223 passed**. Confirms the shared `schema_reload` import resolves from BOTH conftest locations and
  the new products `reload_all_project_app_schemas` fixture wires correctly.

### Validation run

- `uv run ruff format .` → **PASS** (297 files left unchanged; the `COM812`-vs-formatter warning is the
  pre-existing config note that prints on every ruff invocation, not a change).
- `uv run ruff check --fix .` → **PASS** (All checks passed; no autofix churn).
- **Repeated full sweep (the acceptance bar) — `uv run pytest --no-cov` run 5×, green EVERY run:**

  | Full sweep | Result |
  | --- | --- |
  | Run 1 | **PASS** — 2592 passed, 4 skipped, 4 xfailed in 128.05s |
  | Run 2 | **PASS** — 2592 passed, 4 skipped, 4 xfailed in 130.14s |
  | Run 3 | **PASS** — 2592 passed, 4 skipped, 4 xfailed in 129.81s |
  | Run 4 | **PASS** — 2592 passed, 4 skipped, 4 xfailed in 130.65s |
  | Run 5 | **PASS** — 2592 passed, 4 skipped, 4 xfailed in 130.15s |

  Explicit `--no-cov` on every run (required by `pytest.ini`'s auto-applied `--cov`); no `--cov*` flag;
  line coverage neither inspected nor asserted. `pytest-randomly` is NOT installed, so all five runs
  used the identical `-n auto --dist loadscope` config — five-for-five green across the
  worker-scheduling space that produced the 1-in-3 flake is the robustness the documented lesson
  demands ("a single green sweep does NOT prove the fix").
- `git status --short` after ruff: my pass's net contribution is the five files in `### Files touched`
  (3 `M`, 2 `??`). The rest of the working tree carries the pre-existing uncommitted spec-039 build
  (all `M` source/docs/test files were modified before this pass). `docs/feedback.md` and `db.sqlite3`
  are baseline-dirty/concurrent-writable and untouched by me. No tool churn to revert.

### Implementation notes

- **Promoted the helper rather than forking it (DRY).** The reload logic could not stay in
  `test_query/conftest.py` and also be reused by `apps/products/tests/` — pytest conftests are not
  importable across sibling test trees. Moving it to a plain `examples/fakeshop/schema_reload.py`
  module (importable as `schema_reload` via the existing `pythonpath`) keeps the reload discipline
  single-sited; both conftests now import the one function. This is the "promote to a shared location
  both can import" path the task preferred over a near-copy.
- **Kept the fixture name `reload_all_project_app_schemas` identical** in both conftests so the existing
  `test_query/` acceptance files (which request that fixture name) need zero changes, and the products
  `project_schema` fixture requests the same name — uniform surface, no `import conftest` boundary in
  any test body.
- **`sys.modules["config.schema"].schema` (not `importlib.import_module`)** to fetch the rebuilt schema
  in the products fixture: `reload_all_project_app_schemas()` has just reloaded `config.schema` into
  `sys.modules`, so a direct dict lookup returns the freshly-rebuilt module without a redundant import
  round-trip.
- **Secondary polluter hardening WAS applied (not just the primary fix).** I applied it proactively
  because the diagnosis names `test_inspect_with_schema_option` as the chief worker-dirtying sibling,
  and a robust suite should not depend on the victim fixture being the only line of defense — a
  polluter that strands `sys.modules` state is a latent foot-gun for any future worker-sharing test.
  With both the primary complete-reload fixture AND the polluter teardown in place, the 5/5 green
  sweep is the evidence the combination is stable. (The primary fix alone makes the *named* victim
  order-independent; the teardown fix removes the dirty-state *source*, so neither side can strand the
  worker.)
- **`finally`-block deferred import of `reload_all_project_schemas`.** Imported inside the `finally`
  rather than at module top so the polluter test's cold-start eviction of `sys.modules` is not
  perturbed by an extra top-level import binding, and the restore helper is referenced only at the
  teardown point where it runs.

### Notes for Worker 3

- Test-only fix. No production code, no spec, no assertion changes (the three products `test_schema.py`
  asserts and the six `test_inspect_with_schema_option` asserts are byte-identical — the latter only
  wrapped in `try`/`finally`).
- DRY shape to confirm: the reload logic now lives ONCE in `examples/fakeshop/schema_reload.py`; both
  `test_query/conftest.py` and `apps/products/tests/conftest.py` import it; no near-copy fork.
  `git diff -- examples/fakeshop/test_query/conftest.py` shows the body moved out verbatim (deletion),
  not rewritten.
- The acceptance bar is the **repeated** full sweep, not a single green — I ran 5×, all green at 2592
  passed. Re-run the full `uv run pytest --no-cov` sweep multiple times to independently confirm (the
  defect is ~1-in-3 on a single run, so one green run is non-distinguishing).
- No shadow files used (test-only change, no `.py` under `django_strawberry_framework/`).
- No `### Spec slice checklist (verbatim)` ticks owed — this is a gate-fix pass on a test-isolation
  defect, not a slice sub-check landing.

### Notes for Worker 1 (spec reconciliation)

None. Test-only fix; no spec context required, no spec gap surfaced. The diagnosis matched what I
found, so no STOP / plan-revision was needed.

---

## Review (Worker 3) — second gate-fix

`Status: review-accepted`. The second gate-fix is correct, the complete-reload helper is genuinely
PROMOTED to one site (not forked), the primary + secondary fixes both rebuild a COMPLETE project
schema, no assertion was weakened, and my independent repeated full `--no-cov` sweep is green on
**4 of 4** runs. No new findings.

### Files under review (matches the artifact's `### Files touched` exactly)

`git status --short` confirms the pass's net contribution is exactly the five test-infra files (3 `M`,
2 `??`): `examples/fakeshop/schema_reload.py` (NEW), `examples/fakeshop/test_query/conftest.py` (M),
`examples/fakeshop/apps/products/tests/conftest.py` (NEW),
`examples/fakeshop/apps/products/tests/test_schema.py` (M),
`examples/fakeshop/tests/test_inspect_django_type.py` (M). `CHANGELOG.md` is NOT in the working tree.
`docs/feedback.md` / `db.sqlite3` are the recorded baseline-dirty/concurrent-writable files — out of
scope, untouched by the fix.

**Cumulative-diff note (not a finding).** The rest of the working tree carries the full uncommitted
spec-039 build (all the `M` source/docs/test files modified by prior slices). Filtered against the
artifact's `### Files touched`, the second gate-fix's own contribution is exactly these five files.

### DRY — the headline: helper PROMOTED, not forked (VERIFIED)

The complete-reload helper is genuinely single-sited and both conftests IMPORT it — confirmed
mechanically, not on prose:

- `grep -rn "schema_reload\|reload_all_project_schemas"` across `examples/`, `django_strawberry_framework/`,
  `tests/` shows `reload_all_project_schemas` is **defined exactly once** —
  `examples/fakeshop/schema_reload.py:59`. Both conftests do `from schema_reload import
  reload_all_project_schemas` (`test_query/conftest.py:23`, `apps/products/tests/conftest.py:20`), and
  the inspect polluter's `finally` imports the same function (`test_inspect_django_type.py:145`). No
  near-copy fork anywhere.
- **Relocation is behavior-preserving (proven via AST token-diff against HEAD).** I parsed HEAD
  `test_query/conftest.py` and the new `schema_reload.py` and compared the moved logic:
  `_PROJECT_APP_SCHEMA_MODULES` and `_reload_or_import` are **byte/AST-identical**. For
  `reload_all_project_schemas`, the **five non-import executable statements are AST-identical**
  (`registry.clear()`, the dependency-safe reload loop, `_reload_or_import("config.schema")`, the
  `config.urls` lookup, and the `if urls is not None: importlib.reload(urls); clear_url_caches()`
  block). The **only** delta is that `from django.urls import clear_url_caches` moved from a
  module-level import (where it had to leave, or `schema_reload.py` would carry an unused top-level
  import) into a function-local import inside the helper — a placement move that preserves the runtime
  call. This is a verbatim promotion, not a rewrite.
- `git diff -- examples/fakeshop/test_query/conftest.py` shows the helper body **deleted** (moved out)
  and replaced by the one-line `from schema_reload import reload_all_project_schemas`; the
  `reload_all_project_app_schemas` fixture is kept identical in name/shape (only its docstring `:func:`
  ref is requalified to `schema_reload.reload_all_project_schemas`), so every `test_query/` acceptance
  file that requests that fixture is untouched — the relocation is behavior-preserving for the existing
  acceptance suites.
- **Importability is real.** `pytest.ini` has `pythonpath = examples/fakeshop`, so `schema_reload` is
  importable as a top-level module from any conftest — the path the task authorized over keeping the
  logic in a non-importable `conftest.py`. A conftest genuinely cannot be imported by a sibling test
  tree, so promoting to a plain module is the DRY-correct move (not over-abstraction).

**Robustness property confirmed.** `reload_all_project_schemas` reloads ALL FIVE app schemas
(`_PROJECT_APP_SCHEMA_MODULES` = glossary, kanban, library, products, scalars — dependency-safe order,
glossary before kanban for the `CardGlossaryTermType.term` FK) AND fully resets the registry
(`registry.clear()` first), then reloads `config.schema` + `config.urls`. So a products fixture
rebuild materializes the aggregate from a clean registry over every app exactly once — exactly one
`BookInput` regardless of incoming dirty `sys.modules` / registry state.

### Primary fix correct (products `project_schema` complete reload)

`examples/fakeshop/apps/products/tests/test_schema.py::project_schema` no longer does the products-only
**partial** reload (the prior `registry.clear()` + reload `apps.products.schema` + reload
`config.schema`); it now requests the new `reload_all_project_app_schemas` fixture and calls it
(`reload_all_project_app_schemas()` → `sys.modules["config.schema"].schema`). The fixture is backed by
the new `apps/products/tests/conftest.py`, which exposes the same fixture name as `test_query/`,
backed by the same single-sited helper. The diff is exactly two hunks — the import block (drops the now-
dead `import importlib` and `from ...registry import registry`; `sys` correctly retained for the
`sys.modules` lookup at `:45`) and the fixture body. No dead imports remain (ruff `check` would have
flagged them; it passed). **The 3 assertions are untouched** — confirmed: `git diff` shows the two
hunks end at the fixture; the three `test_project_schema_*` functions and their assertions
(`result.errors is None`; the `names == set(Category.objects.filter(is_private=False)...)` cascade pin;
the forward/reverse-relation maps) are byte-identical. The marker/fixture change does not weaken what
the test pins.

### Secondary hardening correct (inspect polluter teardown)

`examples/fakeshop/tests/test_inspect_django_type.py::test_inspect_with_schema_option` now wraps the
command-run + asserts in `try`, with a `finally` that does `from schema_reload import
reload_all_project_schemas; reload_all_project_schemas()`. The `finally` restore is correct and rebuilds
a **complete** project schema, not a partial one: `reload_all_project_schemas()` clears the registry and
re-registers all five apps + `config.schema`. The eviction set it counters — `_SCHEMA_MODULES`
(`test_inspect_django_type.py:38-44`) — is `config.schema` + all five app schemas, so the restore
re-finalizes everything the test popped. The worker is no longer left dirty (no half-registered
`apps.library.schema` stranded in `sys.modules`). **The 6 assertions are byte-identical** — confirmed
the diff only wraps the existing `out = StringIO()` / `call_command(...)` / six `assert ... in text`
lines in `try`; not one assertion string changed.

### No source / assertion / spec change

- `django_strawberry_framework/` source is untouched by this fix: `grep -rn "schema_reload"
  django_strawberry_framework/` → **zero** hits. The fix is entirely test-infrastructure.
- No test assertion weakened (3 products asserts + 6 inspect asserts byte-identical, verified above).
- No spec change; the gate failure was a test-isolation defect, not a spec gap.

### High

None.

### Medium

None.

### Low

None.

### DRY

None — the headline of this fix IS a DRY improvement. The complete-reload logic that previously lived
only in `test_query/conftest.py` is now single-sited in `examples/fakeshop/schema_reload.py` and
imported by both conftests; the products in-process schema test joins the same discipline every
`test_query/` acceptance file already uses. No duplication introduced; one removed (the products
fixture's bespoke partial-reload body is gone).

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` is unchanged **by this gate-fix**. The diff it
shows is the uncommitted Slice-2 lazy-`__getattr__` addition (HEAD carried a TODO comment block; the
working tree has the PEP-562 `__getattr__`). `__all__` is byte-unchanged by that addition, and
`SerializerMutation` remains deliberately ABSENT from `__all__` (F1). This gate-fix touched only the
five test-infra files. No public-surface drift.

### CHANGELOG sanity

Not applicable; gate-fix did not modify `CHANGELOG.md` (confirmed absent from `git status`).

### Documentation / release sanity

The new `examples/fakeshop/schema_reload.py` is example-project test infrastructure — not docs, not a
release artifact, not KANBAN/archive. No version or card claim to check. The `test_query/README.md`
already documents the complete-reload discipline (`reload_all_project_app_schemas`); the fix is
consistent with it.

### Static helper

Skipped — recorded reason. `examples/fakeshop/schema_reload.py` is moved-VERBATIM reload logic (proven
AST-token-identical to the HEAD `test_query/conftest.py` functions above), i.e. **zero net-new logic**;
it lives outside `django_strawberry_framework/`, where the helper trigger is 50+ lines of NEW logic.
With zero new logic and the relocation proven mechanically, the AST scan would add nothing over the
token-identity proof already performed. Skip recorded.

### Pre-existing claim verification

Worker 2 made no "pre-existing at HEAD" claim requiring the stash/checkout protocol — the regression is
build-introduced (the Slice-3 live products surface exposed a latent spec-034 partial-reload gap) and
the fix is in-loop, test-only. The relocation/promotion claim ("helper moved verbatim out of
`test_query/conftest.py`") was the load-bearing claim here, and I verified it mechanically via the AST
token-diff against HEAD (see DRY section): byte/AST-identical except the `clear_url_caches` import
placement.

### Re-confirmed gate-relevant result — REPEATED full sweep (independent)

The defect is flaky (~1-in-3, pure xdist worker scheduling; `pytest-randomly` confirmed NOT installed —
`import pytest_randomly` → `ModuleNotFoundError`, so every run used the identical `-n auto
--dist loadscope` config). A single green sweep does not exonerate, so I ran the canonical
`uv run pytest --no-cov` **four times** independently:

| Independent full sweep | Result |
| --- | --- |
| Run 1 | **PASS** — 2592 passed, 4 skipped, 4 xfailed in 126.68s |
| Run 2 | **PASS** — 2592 passed, 4 skipped, 4 xfailed in 128.89s |
| Run 3 | **PASS** — 2592 passed, 4 skipped, 4 xfailed in 129.66s |
| Run 4 | **PASS** — 2592 passed, 4 skipped, 4 xfailed in 129.94s |

**4 of 4 green.** Explicit `--no-cov` on every run (required by `pytest.ini`'s auto-applied `--cov`); no
`--cov*` flag; coverage neither inspected nor asserted. Combined with Worker 2's reported 5/5, the
combined evidence across the worker-scheduling space that produced the original 1-in-3 flake is the
robustness the documented bar demands. Plus a focused wiring proof — `uv run pytest --no-cov` over
`apps/products/tests/test_schema.py` + `tests/test_inspect_django_type.py` +
`test_query/test_products_api.py` → **102 passed** — confirms the shared `schema_reload` import resolves
from BOTH new conftest locations and the products `reload_all_project_app_schemas` fixture wires.

### Other gate sub-checks (touched files)

- `uv run ruff format --check` on the five files → **PASS** (5 files already formatted; the
  `COM812`-vs-formatter warning is the pre-existing config note).
- `uv run ruff check` on the five files → **PASS** (All checks passed — would have flagged the removed
  `importlib`/`registry` imports in `test_schema.py` had any gone stale; none did).
- `git diff --check` on the modified files → clean (exit 0); no whitespace/conflict-marker damage.

### Temp test verification

None created. The fix's correctness is fully established by (a) the AST token-identity proof of the
verbatim helper promotion, (b) the byte-identical assertion confirmation on both test files, and (c) the
4/4 green repeated full sweep over the flake's scheduling space. A temp test would add nothing.

### What looks solid

The complete-reload helper is genuinely single-sited (`schema_reload.py`), proven moved-verbatim from
HEAD, and imported by both conftests — a clean DRY promotion that brings the lone partial-reload
products fixture onto the same order-independent discipline every acceptance file already uses. The
primary fix rebuilds the full project schema; the secondary fix removes the dirty-state source by
restoring a complete schema in `finally`. Both sides — victim made order-independent AND polluter
de-fanged — so neither can strand the worker. Assertions byte-identical on both files; source/spec
untouched. The repeated full sweep is green every run on my independent re-run.

### Review outcome

`review-accepted`. The fix correctly root-causes the second cross-test-pollution defect
(`DuplicatedTypeName: BookInputCirculationStatusEnum`), the complete-reload helper is PROMOTED to one
site (not forked) and proven verbatim, the primary + secondary fixes both rebuild a COMPLETE project
schema, no assertion is weakened, the public surface and CHANGELOG are clean, and my independent
repeated full `--no-cov` sweep is green at 2592 passed on 4 of 4 runs. Route to Worker 1 to re-run the
final gate.

### Notes for Worker 1 (spec reconciliation)

None. Test-only fix; no spec context required, no spec gap surfaced.

---

## Final verification (Worker 1) — gate re-run (round 2)

`Status: final-accepted` (top-level, authoritative). Both prior cross-test-pollution defects are
fixed and hold: the *first* (`test_list_field` async-marker, Worker-2 fix #1) and the *second*
(`DuplicatedTypeName: BookInputCirculationStatusEnum` partial-reload, Worker-2 fix #2, Worker-3
`review-accepted` on 4/4 independent sweeps). This re-run confirms the full gate is green: **all six
gate commands pass**, and the previously-flaky full sweep is green on **4 of 4** repeated runs. The
two `Status: revision-needed` lines inside the prose above are **historical records** of gate FAIL #1
and gate FAIL #2 (the two fix loops) — left intact per the artifact-hygiene instruction; this
top-level `final-accepted` governs.

### 1. Full test sweep — `uv run pytest --no-cov` — **PASS (4 of 4 repeated runs green)**

The defect that triggered the last loop was flaky (~1-in-3, pure xdist worker scheduling;
`pytest-randomly` confirmed NOT installed this run — `import pytest_randomly` → `ModuleNotFoundError`,
so every run used the identical `-n auto --dist loadscope` config). A single green is insufficient for
a previously-flaky failure, so the canonical `uv run pytest --no-cov` invocation was run **four** times
this gate, green EVERY run:

| Canonical sweep | Result |
| --- | --- |
| Run 1 | **PASS** — 2592 passed, 4 skipped, 4 xfailed in 126.27s |
| Run 2 | **PASS** — 2592 passed, 4 skipped, 4 xfailed in 129.18s |
| Run 3 | **PASS** — 2592 passed, 4 skipped, 4 xfailed in 130.42s |
| Run 4 | **PASS** — 2592 passed, 4 skipped, 4 xfailed in 129.78s |

**4 of 4 green** at the expected `2592 passed, 4 skipped, 4 xfailed`. Explicit `--no-cov` on every run
(required by `pytest.ini`'s auto-applied `--cov`); no `--cov*` flag; line coverage neither inspected nor
asserted. Combined with Worker 2's reported 5/5 and Worker 3's independent 4/4, the cumulative evidence
across the worker-scheduling space that produced the original 1-in-3 flake (13/13 green across three
independent operators) is the robustness the documented bar demands ("a single green sweep does NOT
prove the fix" — Worker-1 memory). The `DuplicatedTypeName` defect is resolved.

### 2a. Django system check — `uv run python examples/fakeshop/manage.py check` — **PASS**

```
System check identified no issues (0 silenced).
```

### 2b. Migration consistency — `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run` — **PASS**

```
No changes detected
```

### 3a. Format check — `uv run ruff format --check .` — **PASS**

```
297 files already formatted
```

(297, up from the 295 in the round-1 records — the two new gate-fix files,
`examples/fakeshop/schema_reload.py` and `examples/fakeshop/apps/products/tests/conftest.py`, are now
in the formatted set. The `COM812`-vs-formatter warning is the pre-existing config note that prints on
every ruff invocation in this repo, not a formatting change. Read-only; `--fix` not passed.)

### 3b. Lint check — `uv run ruff check .` — **PASS**

```
All checks passed!
```

(Read-only; `--fix` not passed.)

### 3c. Whitespace / conflict-marker check — `git diff --check` — **PASS**

Exit 0, no output — no whitespace errors or conflict markers in ANY working-tree file, in ANY build
file. `git diff --check docs/feedback.md` is itself clean (exit 0): the documented baseline-dirty
`docs/feedback.md` exception (AGENTS.md #34) was **not even triggered** — it carries no
whitespace/conflict-marker damage. The lint/format/diff gate is fully clean.

### Summary

`Status: final-accepted`. **All six gate commands pass; the full sweep is green on 4 of 4 repeated runs.**

| Gate command | Result |
| --- | --- |
| `uv run pytest --no-cov` (×4) | **PASS** — 4 of 4 green at 2592 passed, 4 skipped, 4 xfailed |
| `uv run python examples/fakeshop/manage.py check` | PASS — 0 issues |
| `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run` | PASS — No changes detected |
| `uv run ruff format --check .` | PASS — 297 files already formatted |
| `uv run ruff check .` | PASS — All checks passed |
| `git diff --check` | PASS — clean (exit 0); `docs/feedback.md` exception not even triggered |

Both build-introduced cross-test-pollution defects are resolved (FAIL #1 — the Slice-3 async-test
`@pytest.mark.django_db(transaction=True)` marker; FAIL #2 — the Slice-3-exposed partial-reload
`DuplicatedTypeName`, fixed by promoting the complete-reload helper to `examples/fakeshop/schema_reload.py`
and bringing the products in-process schema test + the inspect polluter onto it). The flake that drove
the round-1 re-run no longer reproduces across 4 of 4 sweeps. This **closes the spec-039 build cycle**.

**`docs/feedback.md` baseline exception: not triggered.** `git diff --check` flagged no file at all
(exit 0), including `docs/feedback.md`. The documented AGENTS.md #34 baseline-dirty exception did not
need to be invoked. No BUILD file was flagged.

**Deferred-work catalog: intact and unchanged.** Re-walked the six-entry `### Deferred work catalog`
above — no gate result changed any of it. All six entries stand: (1) the licensed joint-cut docs
deferral (version bump `0.0.12 → 0.0.13` / GLOSSARY `shipped` flip / README+docs-README "Shipped today"
move / CHANGELOG — also maintainer-gated); (2) the out-of-scope board-hygiene `planning_state` residue;
(3) the model-less plain `Serializer` flavor; (4) the `Meta.model_operations` alias affordance; (5) the
`Meta.lookup_field` non-pk future locate; (6) the serializer-shaped output type post-`1.0.0`. The
in-build resolutions remain recorded as **explicitly NOT deferred**: D8 resolver overrides
(`resolve_sync`/`resolve_async`, closed in Slice 3), F-INT-1 (`relation_field_error` consolidation), and
F-INT-2 (vacuous-tautology test deletion). **Additionally, both cross-test-pollution gate-fixes are
RESOLVED this build, NOT deferred:** the `test_list_field` async-marker fix and the `DuplicatedTypeName`
complete-reload promotion (`examples/fakeshop/schema_reload.py` single-sited, both conftests import it).

No version bump (package stays `0.0.12`). No `--cov*` flag used. No commit. No spec edit — the gate was
fully green, so no gate-revealed spec gap surfaced; the spec status header was already reconciled by
Slice 4 and remains accurate (`scripts/check_spec_glossary.py` not re-run, as there was no spec edit).

### Spec changes made (Worker 1 only)

None. The gate re-run passed every command; no spec gap was revealed, so no spec mutation was made. The
spec status header (`docs/spec-039-…md` — "Implemented on main; release deferred to the joint `0.0.13`
cut") remains accurate to the current state.
