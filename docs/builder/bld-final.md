# Build: Final test-run gate — auth_mutations / 0.0.13 (040)

Spec reference: `docs/spec-040-auth_mutations-0_0_13.md`
Build plan: `docs/builder/build-040-auth_mutations-0_0_13.md`
Status: **final-accepted** (Slice-1 re-loop landed the one-line fix — `"apps.accounts.schema"`
added to `examples/fakeshop/tests/test_inspect_django_type.py #"_SCHEMA_MODULES"` — and the
Final test-run gate re-run below now passes all six commands with 0 failed / 0 errors. The
`DuplicatedTypeName: Type UserType` regression is resolved. See `## Final test-run gate
(re-run)` at the bottom of this artifact for the confirming counts. The original
`revision-needed` gate below is preserved as the historical record.)

All three in-spec slices and the cross-slice integration pass are `final-accepted`
(`build-040-…` checklist boxes 1-4 are `- [x]`). This is the build's closing step:
the six-command Final test-run gate (BUILD.md "Final test-run gate") plus the required
`### Deferred work catalog`. The gate is intentionally narrow — no `--cov*` flag is
ever passed; the explicit `--no-cov` opts OUT of `pytest.ini`'s auto-applied `--cov`
(coverage is the maintainer's / CI's gate, not this pass's).

---

## Gate command results

| # | Command | Result |
|---|---------|--------|
| 1 | `uv run pytest --no-cov` | **FAIL** — 1 failed, 2813 passed, 4 skipped, 4 xfailed, 2 errors |
| 2 | `uv run python examples/fakeshop/manage.py check` | **PASS** — "System check identified no issues (0 silenced)." |
| 3 | `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run` | **PASS** — "No changes detected" (exit 0) |
| 4 | `uv run ruff format --check .` | **PASS** — "308 files already formatted" (exit 0) |
| 5 | `uv run ruff check .` | **PASS** — "All checks passed!" (exit 0) |
| 6 | `git diff --check` | **PASS** — clean (exit 0) |

### Command 1 — `uv run pytest --no-cov` (full sweep, all three test trees) — FAIL

The full parallel sweep (`pytest-xdist`, 8 workers) fails on worker `gw1` with a
`DuplicatedTypeName` at the aggregate `config.schema` build. Reproduced deterministically
across two independent full-sweep runs (277.00s run and a `-p no:randomly` 369.42s
re-run — same three nodes, same worker `gw1`, same error each time):

```
FAILED examples/fakeshop/tests/test_inspect_django_type.py::test_inspect_with_schema_option[config.schema]
ERROR  examples/fakeshop/tests/test_inspect_django_type.py::test_inspect_by_registered_name    (at setup)
ERROR  examples/fakeshop/tests/test_inspect_django_type.py::test_inspect_by_dotted_path         (at setup)
E   strawberry.exceptions.duplicated_type_name.DuplicatedTypeName: Type UserType is defined multiple times in the schema
.venv/.../strawberry/schema/schema_converter.py:1040
```

Counts: **1 failed, 2813 passed, 4 skipped, 4 xfailed, 2 errors**. Every other test
across `tests/`, `examples/fakeshop/apps/*/tests/`, and `examples/fakeshop/test_query/`
passes (the FAKESHOP_SHARDED-gated tests do not run under the default invocation — that
is expected and not a failure). The `4 xfailed` are the pre-existing
`test_mutation_atomicity.py` xfails.

**This is a genuine in-build regression, NOT flaky infra to paper over.** Per worker-1.md
"Example-model field changes ripple …" / "A regression introduced this way is the
build's to fix in-loop — never defer an in-build regression to a spawned background
task," it blocks `final-accepted` and re-loops the owning slice.

#### Root-cause diagnosis (mechanically confirmed)

- **The failing type is the new `accounts` app's `UserType`.** Slice 1 added the
  schema-only fakeshop app `examples/fakeshop/apps/accounts/` declaring
  `class UserType(DjangoType)` over `get_user_model()`
  (`examples/fakeshop/apps/accounts/schema.py::UserType`), composed into
  `examples/fakeshop/config/schema.py`.
- **`test_inspect_django_type.py` carries a private, hardcoded, now-STALE schema-module
  list.** `examples/fakeshop/tests/test_inspect_django_type.py #"_SCHEMA_MODULES"`
  (lines 38-45) is a private tuple of the six project schema modules used ONLY by
  `test_inspect_with_schema_option`'s cold-path `sys.modules.pop(...)` eviction. It lists
  `config.schema` + `apps.{library,products,scalars,kanban,glossary}.schema` but **omits
  `apps.accounts.schema`** — the app Slice 1 added.
- **The collision mechanism.** On a worker that has already built the aggregate
  `config.schema` (so `apps.accounts.schema` is cached in `sys.modules` with `UserType`
  registered), `test_inspect_with_schema_option[config.schema]` evicts only its private
  six-module list (leaving `apps.accounts.schema` stranded, cached, still holding its
  `UserType` class), calls `registry.clear()`, then `call_command("inspect_django_type",
  "BookType", "--schema", "config.schema")` re-imports `config.schema`, which re-imports
  `apps.accounts.schema` and re-registers `UserType` — while the stranded cached module's
  `UserType` also participates in the aggregate build → `UserType` defined twice →
  `DuplicatedTypeName`. The two follow-on `test_inspect_by_*` ERRORs are the same worker's
  next tests failing at fixture setup because the worker's registry/`sys.modules` is left
  dirty by the failed cold-path test. This is exactly the eviction-strands-a-module hazard
  the test's OWN docstring names (lines 122-128) — but for `apps.accounts.schema`, which the
  private list never learned about.
- **The shared complete-reload helper WAS updated; the private copy was NOT.** Slice 1
  correctly added `"apps.accounts.schema"` to the single-sited
  `examples/fakeshop/schema_reload.py #"_PROJECT_APP_SCHEMA_MODULES"` (so the
  `test_query/` + `apps/products/` conftests that delegate to
  `reload_all_project_schemas()` are safe), but missed this ONE test file's private
  parallel `_SCHEMA_MODULES` eviction tuple. Verified no other test carries a stale
  hardcoded list: `test_query/conftest.py` and `apps/products/tests/conftest.py` both
  delegate to `schema_reload.reload_all_project_schemas`; `test_inspect_django_type.py` is
  the sole holder of a private eviction list.
- **Order-dependency confirmed (matches the known cross-test-pollution class).** The file
  passes in isolation (10 passed), single-worker in file order (10 passed), and even
  single-worker after the whole `test_query/` suite (333 passed) or after
  `tests/auth/` — it only fails under the 8-worker parallel distribution, where a foreign
  aggregate-building test lands on `gw1` ahead of the cold-path test. Green-on-one-ordering
  ≠ isolated; the parallel sweep is the first run to hit the polluting sequence.

#### Owning slice + the fix (for Worker 0's re-loop)

**Owning slice: Slice 1** (`bld-slice-1-auth_substrate_login_logout.md`) — it introduced
`apps.accounts.schema` / `UserType` and owns keeping the project's schema-module lists in
sync with that addition. Slice 1 updated the shared `_PROJECT_APP_SCHEMA_MODULES` but not
this test's private `_SCHEMA_MODULES`.

The fix is a one-line test change (Worker 1 does NOT edit tests — this is Slice-1
re-loop work for Worker 2): add `"apps.accounts.schema"` to
`examples/fakeshop/tests/test_inspect_django_type.py #"_SCHEMA_MODULES"` (lines 38-45) so
the cold-path eviction strands+restores `apps.accounts.schema` alongside the other five
apps, matching the shared helper's module set. The teardown (`reload_all_project_schemas`)
already handles accounts; only the eviction list is stale. The re-loop verification MUST
be the FULL parallel sweep (`uv run pytest --no-cov`), not a focused run — the regression
is invisible to any single-file or single-worker scope.

### Commands 2-6 — all PASS

- **`manage.py check`** → "System check identified no issues (0 silenced)." No model /
  admin / URL-config drift.
- **`makemigrations --check --dry-run`** → "No changes detected" (exit 0). Model state is
  migration-consistent; no migration files produced. (The auth surface adds no fakeshop
  model — `accounts` is schema-only over `auth.User`.)
- **`ruff format --check .`** → "308 files already formatted" (exit 0). The standing
  `COM812`-conflicts-with-formatter warning is pre-existing config noise (noted in
  `bld-integration.md`), not a failure.
- **`ruff check .`** → "All checks passed!" (exit 0).
- **`git diff --check`** → clean (exit 0). No whitespace errors or conflict markers
  anywhere in the working tree.

No pre-flight baseline exception was recorded in the build plan preamble beyond the
expected prior-cycle (039) artifact deletions, so the command-1 failure is not waived and
blocks `final-accepted`.

---

## Deferred work catalog

Walked every per-slice and integration artifact's spec-reconciliation notes +
`What looks solid` / `Notes for Worker 1` sections, and the spec's
`## Risks and open questions` (spec lines 2559-2617) + `## Out of scope` (spec lines
2619-2649). The catalog below is the next spec author's reading list. Format per bullet:
**source artifact section** — spec line licensing the deferral (if any) — one-line
description.

### Discharged this build (recorded for completeness — NOT open deferrals)

- **Integration artifact `### Build report (Worker 2)` / carry-forward 2** — spec
  Decision 10 P3 ("may", not "must"; edited during Slice-1 final verification, spec
  ~line 2035): the generic `run_in_one_sync_boundary` factoring was NOT taken (the auth
  async boundary stays auth-local via `_run_in_one_boundary`), and the
  `mutations/resolvers.py::run_pipeline_async` `TODO(spec-040 Slice 1)` anchor was
  **discharged** in the integration consolidation (re-tagged to a non-TODO provenance
  comment). No `TODO(spec-040` survives in shipped `.py`. Open only as a *possible future*
  factoring on a dedicated async card — not an obligation this build left behind.
- **Integration artifact / carry-forward 3** (Slice-1 `### Deferred-work note`): the dead
  `_build_auth_field(permission_holder=...)` parameter was **removed** in the integration
  consolidation pass. Closed.
- **Slice 3 / CHANGELOG note (maintainer-gated, LANDED — not deferred).** Per the build
  plan "CHANGELOG permission gate" and spec Decision 12 / lines 66-70 + 687-689, the
  `CHANGELOG.md` `[0.0.13]` release bullets for BOTH `0.0.13` cards (039 serializer + 040
  auth) were AUTHORIZED by the Slice-3 maintainer prompt and **landed this build** (see
  `bld-slice-3-…::Reconciliation / Final verification`). Flagged here per the task's
  explicit instruction: it was maintainer-gated (AGENTS.md "Do not update CHANGELOG.md
  unless explicitly instructed"), NOT auto-taken. It is shipped, not deferred.

### Accepted non-blocker carried forward

- **Integration artifact `### Final verification (Worker 1)` "Minor coherence note"** — no
  spec line (docstring-provenance polish): `auth/queries.py::current_user` function
  docstring still reads `"sharing the Slice-1 auth machinery"`
  (`queries.py #"sharing the Slice-1 auth machinery"`), while the module docstring three
  lines above dropped the qualifier to `"sharing the auth substrate"`. Factual inline
  provenance (no `TODO(` prefix, no `NotImplementedError`, does NOT render into
  `docs/TREE.md`), acceptable per AGENTS.md L26; recorded so the next docstring-touching
  change drops the lone `Slice-1` qualifier for full within-module coherence. Non-blocking.

### Spec-level follow-ons (spec `## Risks and open questions` + `## Out of scope`)

The card ships the parity surface as specced; these are the explicitly-tracked follow-ons
the spec / artifacts named as future work:

- **Spec `## Risks` — `credential_fields=` for non-`username` backends** (spec lines
  2583-2591): a backend wanting different credential *names* (a `token=`-shaped backend)
  cannot ride `login_mutation()`; out of scope for `0.0.13`. Fallback follow-on: a
  `credential_fields=` factory kwarg mapping GraphQL args onto `authenticate` kwargs —
  contained/additive if demanded.
- **Spec `## Risks` + `## Out of scope` — register customization / subclassable
  `DjangoRegisterMutation` base** (spec lines 2592-2599, 2636-2637): a consumer wanting
  extra profile fields at registration has no seam short of hand-writing a mutation.
  Recorded follow-on: expose `DjangoRegisterMutation` as a documented subclassable base
  (its password write step inherited, the upstream shape) — a small additive card,
  sequenced on real consumer need.
- **Spec `## Risks` — native-async auth APIs** (spec lines 2600-2605): `aauthenticate` /
  `alogin` / `alogout` (Django ≥ 5.0, in-support on the `Django>=5.2` floor). `0.0.13`
  keeps the family's single `sync_to_async(thread_sensitive=True)` boundary; adopting
  native-async session APIs is a family-wide decision for a dedicated card (spec Decision
  10). No correctness gap — the boundary is correct, just not maximally concurrent.
- **Spec `## Risks` + `## Out of scope` — Channels / websocket / consumer-scope auth →
  `0.0.14`** (spec lines 2606-2612, 2621-2625): deferred to the `0.0.14` router card
  (`TODO-ALPHA-041-0.0.14`, `DjangoGraphQLProtocolRouter`); upstream's `channels_auth`
  fallback ports there if at all (spec Decision 11, deliberately not borrowed here).
- **Spec `## Out of scope` — ergonomic `TestClient` / `GraphQLTestCase` helpers →
  `0.0.14`** (spec lines 2626-2629): `TODO-ALPHA-043-0.0.14`; the live auth tests use the
  raw Django test client's session support today.
- **Spec `## Out of scope` — token / JWT auth + password-change / password-reset
  mutations** (spec lines 2630-2632): no upstream analog in either reference package;
  `BACKLOG.md` material if ever (spec Decision 2).
- **Spec `## Out of scope` — a package-provided `UserType` default** (spec lines
  2633-2635): the consumer declares their own; a documented helper is a possible follow-on
  (spec Decision 8). (The fakeshop `accounts.UserType` is an *example*, not a package
  export.)
- **Spec `## Out of scope` — field-level read gates → `0.1.1`** (spec lines 2638-2647):
  `FieldSet` / per-field permission hooks; they will compose on top of the auth surface's
  returned user objects — on `register`'s G2-planned re-fetched node as for any type. But
  `login.node` / `me` (the raw, non-optimizer-planned actor instances, spec Decisions 5/7)
  are **flagged for re-examination** when field gates land — whether a per-field
  `check_<field>_permission` fires identically on a raw unplanned instance versus a planned
  node is not yet proven (the Revision-4 GOAL cross-reference).

---

## Routing

**A re-loop IS required.** Worker 0 must:

1. Re-loop **Slice 1** (`bld-slice-1-auth_substrate_login_logout.md`): dispatch Worker 2 to
   add `"apps.accounts.schema"` to
   `examples/fakeshop/tests/test_inspect_django_type.py #"_SCHEMA_MODULES"` (lines 38-45) —
   the stale private eviction list that omits the accounts app Slice 1 introduced — so the
   cold-path eviction strands+restores it alongside the other five apps (matching the
   already-correct shared `schema_reload._PROJECT_APP_SCHEMA_MODULES`). Then Worker 3
   review, then Worker 1 Slice-1 final verification.
2. **Return to Worker 1** to re-run this Final test-run gate. The re-run MUST execute the
   FULL parallel sweep `uv run pytest --no-cov` (the regression is invisible to any
   single-file or single-worker scope); confirm 0 failed / 0 errored, then set this
   artifact `Status: final-accepted`. Gate commands 2-6 already pass and need only a
   confirming re-run after the Slice-1 fix lands.

Do NOT mark the final checklist box `- [x]` while command 1 fails.

---

## Final test-run gate (re-run)

**Status: final-accepted.** The Slice-1 re-loop landed the one-line fix Worker 0 routed:
`"apps.accounts.schema"` was added to
`examples/fakeshop/tests/test_inspect_django_type.py #"_SCHEMA_MODULES"` (now a seven-module
tuple matching the shared `examples/fakeshop/schema_reload.py #"_PROJECT_APP_SCHEMA_MODULES"`).
Worker 2 built it, Worker 3 re-reviewed → `review-accepted`. All six gate commands re-run
below pass with **0 failed / 0 errors**. The `DuplicatedTypeName: Type UserType`
cross-test-pollution regression is **resolved**. This is a verification-only pass — no
source/test/doc/DB/spec was edited, and no commit was made.

### Gate command re-run results

| # | Command | Result |
|---|---------|--------|
| 1 | `uv run pytest --no-cov` | **PASS** — 2816 passed, 4 skipped, 4 xfailed (0 failed, 0 errors) |
| 2 | `uv run python examples/fakeshop/manage.py check` | **PASS** — "System check identified no issues (0 silenced)." |
| 3 | `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run` | **PASS** — "No changes detected" (exit 0) |
| 4 | `uv run ruff format --check .` | **PASS** — "308 files already formatted" (exit 0) |
| 5 | `uv run ruff check .` | **PASS** — "All checks passed!" (exit 0) |
| 6 | `git diff --check` | **PASS** — clean (exit 0) |

### Command 1 — regression resolved

The full parallel sweep (`pytest-xdist`, 8 workers) that previously failed on worker `gw1`
with `DuplicatedTypeName: Type UserType` at
`test_inspect_django_type.py::test_inspect_with_schema_option[config.schema]` (plus the two
follow-on `test_inspect_by_*` setup ERRORs) now passes cleanly. The three previously-broken
nodes (1 failed + 2 errors) all pass; the passed count rose from 2813 to **2816** with the
`+3` accounted for exactly by those three nodes. Counts this run:
**2816 passed, 4 skipped, 4 xfailed, 0 failed, 0 errors** in 144.99s. Confirmed the fix:
`_SCHEMA_MODULES` now lists all seven schema modules (the six prior + `apps.accounts.schema`),
so the cold-path `sys.modules.pop(...)` eviction strands+restores `apps.accounts.schema`
alongside the other apps instead of leaving it cached with a stranded `UserType`. The
`4 xfailed` remain the pre-existing `test_mutation_atomicity.py` xfails; the `4 skipped` are
the `FAKESHOP_SHARDED`-gated tests (not run under the default invocation, expected).

### Commands 2-6 — all PASS (unchanged from the prior gate)

`manage.py check`, `makemigrations --check --dry-run`, `ruff format --check .`,
`ruff check .`, and `git diff --check` all re-confirmed green (the `COM812`-conflicts-with-
formatter line on command 4 is the pre-existing standing config-noise warning, not a failure).

### Deferred work catalog — still current

The `### Deferred work catalog` above stands unchanged. The Slice-1 re-loop was a single
test-file eviction-list sync (test-only; no source/spec/behavior change), so nothing in the
catalog was added, removed, or altered. It remains the next spec author's reading list as
written.

### Outcome

All six gate commands pass. This artifact's top-level `Status:` is set to `final-accepted`.
The build is closed; Worker 0 marks the final checklist box `- [x]` and hands off to the
maintainer.
