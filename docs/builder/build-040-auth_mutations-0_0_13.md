# Package build plan: auth_mutations / 0.0.13 (040)

> **Maintainer note (post-build reconciliation, 2026-07-03):** the worker artifacts
> below record the BUILD.md cycle as executed on the reference implementation. The
> implementation that ships merged the strongest variant from three parallel builds
> of this spec, so a few internals the artifacts cite by name landed in a different
> (better) shape: the auth async boundary is the promoted generic
> `mutations/resolvers.py::run_in_one_sync_boundary` (the spec's optional P3
> factoring WAS taken; there is no auth-local `_run_in_one_boundary`), the injected
> signature idiom is the promoted
> `mutations/fields.py::build_lazy_field_signature` (not
> `attach_synthesized_signature`), the auth ledger stores the permission holders /
> rider directly with an `_auth_surface` key (there is no `_AuthDeclaration`
> wrapper record), the `current_user` holder `__name__` is `CurrentUser`, and the
> finalizer's auth bind is guarded on `sys.modules` so an auth-free consumer never
> imports the subsystem. Where an artifact's prose and the committed diff disagree,
> the diff is authoritative. Additionally, the spec and its terms CSV were archived
> post-ship to `docs/SPECS/`; the `docs/spec-040-…` paths recorded below and in the
> `bld-*.md` artifacts (including the pre-flight `check_spec_glossary` invocation)
> are the pre-archive paths, preserved intentionally as the historical record.

Spec source: `docs/spec-040-auth_mutations-0_0_13.md` (archived post-ship to `docs/SPECS/spec-040-auth_mutations-0_0_13.md`)
Target release: `0.0.13`
Date created: 2026-07-02
Build rule: one slice at a time. Plan first, build second, review third, reconcile fourth. Do not start the next slice until the current slice's plan/build/review/verification/spec-reconciliation cycle is complete.
DRY rule: every plan, every implementation, every review pass answers first — is this the maximally DRY shape that stays readable? Duplicated logic, parallel data flows, near-copies between modules, and repeated string/key/tuple literals are build-time defects. This card is explicitly a *rider* build (spec Decision 6): the register flavor is NOT a fourth write-flavor plumbing kit — it reuses the `036` write-pipeline skeleton via a custom step pair, adds no new field converter, no new input generator, no new pipeline orchestration. Every auth resolver must route through the named write-stack / `utils/` helpers (spec `## Helper-reuse obligations (DRY)`) and not re-spell them; the three deliberate non-reuse points must each carry a source comment.

Pre-flight: passed on 2026-07-02.
- Working-tree baseline: clean apart from the 8 expected pre-flight deletions of prior-cycle (039) build artifacts (`build-039-serializer_mutations-0_0_13.md` + 7 `bld-*.md`). No unrelated uncommitted changes. (Maintainer authorized the cleanup.)
- `scripts/review_inspect.py` runs (smoke: `django_strawberry_framework/registry.py` → overview OK, imports: 10, symbols: 28).
- `.gitignore` lists `docs/builder/worker-memory/`, `docs/shadow/`, `docs/builder/temp-tests/` — confirmed.
- Scratch cleared: `docs/builder/worker-memory/{0,1,2,3}.md` reseeded empty; `docs/builder/temp-tests/` empty; `docs/shadow/` top-level `*.overview.md`/`*.stripped.py` build-cycle output removed. **AGENTS.md-L23 reconciliation:** `docs/shadow/` also holds `current/ diff/ new/ old/` sibling folders owned by *other* generators (`review_historical_package_snapshot_at_commit.py`, `review_changed_python_diffs_against_head.py`); AGENTS.md L23 ("each generator clears ONLY its own folder(s), never the whole tree") overrides BUILD.md pre-flight step 5's literal "delete every file under docs/shadow/", so those sibling folders were left intact. The build's own `review_inspect` output lives as flat top-level files and was cleared.
- `uv run python scripts/check_spec_glossary.py --spec docs/spec-040-auth_mutations-0_0_13.md` → `OK: 127 terms`.

## Baseline-dirty / out-of-scope files (workers do not edit, do not revert)

- None as a starting baseline. The only working-tree changes at plan-creation are this build's own pre-flight deletions (above), which are build-cycle artifact churn, not out-of-scope maintainer work.

### Concurrent-writable tracked binary / generated files (BUILD.md L77-84)

Per BUILD.md "Tracked binary / generated files", the following are rewritable by a concurrent maintainer process or the build's own test/regenerate runs; a dirty status on one of these is not by itself proof this build caused it, and a same-size binary diff is not proof of a no-op:

- `examples/fakeshop/db.sqlite3` — DB-backed; Slice 3's card-wrap legitimately diverges it from HEAD (kanban card move + any glossary term seed). Verify Slice 3's DB writes by two-consecutive-regenerate byte-stability + spot-checks, NOT by "git diff is clean" (the DB has legitimately diverged).
- `KANBAN.md` / `KANBAN.html` — rendered from the kanban tables in `db.sqlite3`. Slice 3 edits the DB via the ORM then regenerates; never hand-edit.
- `docs/GLOSSARY.md` — rendered from the glossary tables in `db.sqlite3`. Slice 3 flips the Auth-mutations and SerializerMutation statuses + the package-version line via the DB then regenerates; never hand-edit.

## Build-wide context flags

- **Version-bump owner:** this card (040) owns the `0.0.13` version bump (spec Decision 12, the lone-card posture of spec-038 Decision 14) — Slice 3 moves the version quintet `0.0.12` → `0.0.13` (`pyproject.toml`, `__init__.py` `__version__`, `tests/base/test_init.py::test_version`, the `docs/GLOSSARY.md` package-version line, and the `django-strawberry-framework` `version` entry in `uv.lock`).
- **Joint-cut completion:** `DONE-039-0.0.13` (serializer flavor) is implemented on main with its release wording deferred to *this* card's cut (spec-039 Decision 14 / F8). Slice 3 lands the `039`-deferred flips: GLOSSARY `SerializerMutation` → `shipped (0.0.13)`, README/docs-README "Coming next" → "Shipped today" + README Status → `0.0.13`, and the `CHANGELOG.md` release bullets for BOTH `0.0.13` cards.
- **CHANGELOG permission gate:** `CHANGELOG.md` is edited ONLY when the Slice 3 maintainer prompt explicitly requests it (AGENTS.md #"Do not update CHANGELOG.md unless explicitly instructed"). This spec describes the edit but cannot grant the permission. Absent an explicit maintainer instruction at Slice 3, the CHANGELOG bullet is deferred and recorded in the deferred-work catalog.
- **Live-first mandate:** Slices 1 and 2 each land their resolvers TOGETHER WITH their fakeshop `accounts` live surface in one commit (`examples/fakeshop/test_query/README.md` #"Coverage rule." / `docs/TREE.md` #"Coverage priority."). Package tests under `tests/auth/` hold ONLY the residue a live `/graphql/` request cannot drive.
- **Permission-gate coverage placement (Revision-7 fix, NOT a live-first weakening):** the one-declaration-per-process rule (spec Decision 6) makes a second, permission-gated variant of the same fixed-payload auth field impossible in the single aggregated `config/schema.py`, so ALL permission-gate coverage (exact denial strings, gate-payload contract, `IsAuthenticated`-style `me` gate, mutation-introspection raise) is genuinely unreachable live and lives in `tests/auth/` on isolated throwaway schemas. This is the documented AGENTS.md unreachable-live placement exception.
- **Scaffolded fail-loud stubs already on disk at HEAD (`b2e1dd63`):** `django_strawberry_framework/auth/{__init__,mutations,queries}.py`, `tests/auth/{test_mutations,test_queries}.py`, `examples/fakeshop/apps/accounts/{apps,schema}.py`, `examples/fakeshop/test_query/test_auth_api.py`, and `docs/spec-040-auth_mutations-0_0_13-terms.csv` exist as TODO-anchored fail-loud scaffolds. `examples/fakeshop/config/schema.py` carries a `TODO(spec-040 Slice 1)` anchor for composing the accounts surface; `examples/fakeshop/schema_reload.py` `_PROJECT_APP_SCHEMA_MODULES` does NOT yet list `"apps.accounts.schema"`. Workers implement over these stubs. **Every `TODO(spec-040 …)` anchor must be discharged (work landed + anchor removed) by build end** (BUILD.md integration-pass step 6); the integration pass greps `TODO\(spec-040|TODO-(ALPHA|BETA|STABLE)-040` across the tree and routes any survivor to its owning slice.
- **Register is a rider, not a flavor:** `register_mutation()` synthesizes a cached `DjangoMutation` subclass whose `__name__` is pinned to `Register` (so the unchanged machinery emits `RegisterPayload` — no payload-name seam), overrides `resolve_sync` AND `resolve_async` to ride `run_write_pipeline_sync` with a password-aware `decode_step`/`write_step` pair because the `036` create pipeline exposes no per-instance write hook and its default steps would persist the raw password. The plaintext-never-persisted assertion is required on BOTH sync and async paths.

## One-slice-at-a-time rule (copy)

Build only one slice at a time. Do not start the next slice until the current slice's plan → build → review → verification → spec-reconciliation cycle is complete. After all in-spec slices are built, run a cross-slice integration pass (Worker 1; may trigger a second-loop refactor through Worker 2 / Worker 3). The build closes with one final test-run gate handled by Worker 1.

## DRY-first rule (copy)

Every slice must justify shared/duplicated patterns before merging. Worker 1 plans for DRY before code is written; Worker 3 enforces DRY before code is accepted; Worker 1 re-checks DRY across slices at the integration pass. This card's DRY spine is the `## Helper-reuse obligations (DRY)` section of the spec — the auth code reuses `run_write_pipeline_sync`, `build_payload_type`, `DjangoMutationField`'s signature-injection idiom, `authorize_or_raise` / `check_permission`, `validation_error_to_field_errors` (except the password key-direct path), `editable_input_fields`, and the AR-H2 exclusion seam by call.

## Artifact list

- `docs/builder/bld-slice-1-auth_substrate_login_logout.md`
- `docs/builder/bld-slice-2-register_current_user.md`
- `docs/builder/bld-slice-3-docs_version_cut_wrap.md`
- `docs/builder/bld-integration.md`
- `docs/builder/bld-final.md`

## Checklist

- [x] Slice 1 — auth substrate + `login_mutation` / `logout_mutation`, earned live -> `docs/builder/bld-slice-1-auth_substrate_login_logout.md`
- [x] Slice 2 — `register_mutation` + `current_user`, earned live -> `docs/builder/bld-slice-2-register_current_user.md`
- [x] Slice 3 — docs + the `0.0.13` version cut + card wrap -> `docs/builder/bld-slice-3-docs_version_cut_wrap.md`
- [x] Cross-slice integration pass -> `docs/builder/bld-integration.md`
- [x] Final test-run gate -> `docs/builder/bld-final.md`
