# Spec: Multi-database cooperation contract

Target release: `0.0.7` (per the [`KANBAN.md`](../KANBAN.md) card `WIP-ALPHA-019-0.0.7`).
Status: draft (revision 1).
Owner: package maintainer.
Predecessors: [`docs/GLOSSARY.md`](GLOSSARY.md) (entries [`Multi-database cooperation`](GLOSSARY.md#multi-database-cooperation), [`DjangoOptimizerExtension`](GLOSSARY.md#djangooptimizerextension), [`get_queryset` visibility hook](GLOSSARY.md#get_queryset-visibility-hook), [`Strictness mode`](GLOSSARY.md#strictness-mode), [Queryset diffing](GLOSSARY.md#queryset-diffing), [FK-id elision](GLOSSARY.md#fk-id-elision)); [`KANBAN.md`](../KANBAN.md) card `WIP-ALPHA-019-0.0.7`; joint-cut policy spec [`docs/SPECS/spec-016-list_field-0_0_7.md`](SPECS/spec-016-list_field-0_0_7.md) ([Decision 10](SPECS/spec-016-list_field-0_0_7.md#decision-10--joint-007-cut), reused verbatim in [Decision 9](#decision-9--joint-0_0_7-cut) here); shipped sibling [`docs/SPECS/spec-018-export_schema-0_0_7.md`](SPECS/spec-018-export_schema-0_0_7.md) (the bundle this card sits inside).

Revision history (kept inline so the spec is self-contained):

- **Revision 1** — initial draft. Pins the canonical spec filename (`docs/spec-019-multi_db-0_0_7.md`, NOT the [`KANBAN.md`](../KANBAN.md) card body's ad-hoc `docs/spec-multi_db.md` — pinned in [Decision 1](#decision-1--spec-filename-and-canonical-naming)), the no-production-code-change scope (the cooperation already exists in [`django_strawberry_framework/types/resolvers.py`](../django_strawberry_framework/types/resolvers.py) at line 82 — `state.db = router.db_for_read(field_meta.related_model, instance=instance)`; this card's job is to spec + test + document that cooperation, pinned in [Decision 2](#decision-2--no-production-code-change)), the four-axis cooperation contract (database routers via `router.db_for_read`, explicit `.using(alias)` querysets, `_state.db` propagation through FK-id elision stubs, optimizer plan / strictness / `get_queryset` downgrade routing — pinned in [Decision 3](#decision-3--the-cooperation-contract-four-axes)), the test layout (`tests/optimizer/test_multi_db.py` with mocked router for hermetic package-internal coverage per [Decision 5](#decision-5--package-internal-tests-use-a-fixture-router-not-fakeshop_sharded); fakeshop live-HTTP coverage under `examples/fakeshop/test_query/` per [Decision 6](#decision-6--live-coverage-under-fakeshop_sharded1) gated on `FAKESHOP_SHARDED=1` via `pytest.skip(...)` rather than `pytest.mark.skipif` because the env var changes `config.settings.DATABASES` at module-import time), the GLOSSARY entry flip from `planned for 0.0.7` to `shipped (0.0.7)` in Slice 3, the `docs/README.md` `### Sharded mode (multi-DB)` one-line forward-pointer per the card DoD, the joint-`0.0.7` cut policy ([Decision 9](#decision-9--joint-0_0_7-cut)), and zero new public exports. Out of scope: first-class sharding-aware planning (cross-shard joins, automatic shard selection based on FK, multi-shard aggregates, `Meta.preferred_database`) — [`BACKLOG.md`](../BACKLOG.md) item 41 owns that.

## Key glossary references

Skim these [`docs/GLOSSARY.md`](GLOSSARY.md) entries first — they anchor the vocabulary used throughout the spec:

- [`Multi-database cooperation`](GLOSSARY.md#multi-database-cooperation) — the entry this card flips from `planned for 0.0.7` to `shipped (0.0.7)` in [Slice 3](#implementation-plan). The entry body already describes the cooperation contract this spec pins down.
- [`DjangoOptimizerExtension`](GLOSSARY.md#djangooptimizerextension) — the optimizer that this card proves cooperates with Django's routing. The extension does not query the router itself; cooperation rides on the queryset's `_db` attribute being preserved through plan application, `Prefetch` chains, and FK-id elision stubs.
- [`get_queryset` visibility hook](GLOSSARY.md#get_queryset-visibility-hook) — the consumer-owned visibility filter that survives relation traversal via the optimizer's `Prefetch` downgrade; this card adds a routing axis to that contract.
- [Queryset diffing](GLOSSARY.md#queryset-diffing) — the optimizer's cooperation rule that respects work the consumer already applied to the queryset (including `.using(alias)`); cited so the [Decision 3](#decision-3--the-cooperation-contract-four-axes) cooperation contract is grounded in shipped behavior, not new code.
- [Strictness mode](GLOSSARY.md#strictness-mode) — `off` / `warn` / `raise` for unplanned N+1 detection; this card pins that the strictness check fires against the relation access on whatever connection the queryset was scoped to, not against a globally-routed re-read.
- [FK-id elision](GLOSSARY.md#fk-id-elision) — the optimizer's `{ relation { id } }` shortcut that reads the FK column off the parent row and synthesizes a stub. This card pins that the stub's `_state.db` is set via `router.db_for_read(...)` so subsequent attribute access (e.g. follow-up resolver hops) reads from the correct connection.
- [`DjangoType`](GLOSSARY.md#djangotype) — the consumer-facing type the optimizer plans for; not directly modified by this card but the framing for every test fixture.
- [`finalize_django_types`](GLOSSARY.md#finalize_django_types) — the consumer-owned synchronization point; tests that exercise multi-db cooperation finalize once per fixture exactly like the existing optimizer tests.
- [`ConfigurationError`](GLOSSARY.md#configurationerror) — not raised by anything in this card.

Project conventions to follow:

- [`AGENTS.md`](../AGENTS.md) — line 6 (test placement; package tests live under `tests/` with `__init__.py` shells in subdirectories like `tests/optimizer/`, example-project non-HTTP tests under `examples/fakeshop/tests/`, live HTTP tests under `examples/fakeshop/test_query/` and no `__init__.py` in either fakeshop test tree); line 9 ("any coverage line achievable via a real GraphQL query against fakeshop in `examples/fakeshop/test_query/` MUST be earned that way"); line 14 ("Do not run pytest after edits"); line 20 ("Add settings keys only when the feature that needs them lands"). **Note:** line 21 prohibits [`CHANGELOG.md`](../CHANGELOG.md) edits without explicit permission; [Slice 3](#implementation-plan) grants that permission for this card's `[0.0.7]` `### Added` append.
- [`CONTRIBUTING.md`](../CONTRIBUTING.md) — 100% coverage target.
- [`KANBAN.md`](../KANBAN.md) — card-ID format; column movement at Slice 3; the card body's `docs/spec-multi_db.md` reference predates the structured `spec-<NNN>-<topic>-<0_0_X>.md` convention and gets rewritten in the same sweep per [Decision 1](#decision-1--spec-filename-and-canonical-naming).
- [`docs/TREE.md`](TREE.md) — tests mirror source one-to-one; `tests/optimizer/` already carries `__init__.py` and shipped optimizer-test modules, so adding `tests/optimizer/test_multi_db.py` is a one-file extension, not a new subdirectory.

## Slice checklist

Each top-level item maps to one commit in the [Implementation plan](#implementation-plan). Three slices total.

- [ ] Slice 1: Package-internal tests
  - [ ] New `tests/optimizer/test_multi_db.py` containing **six** tests (per [Test plan](#test-plan); single pytest item per test, no `pytest.mark.parametrize` fan-out so the count matches pytest collection output unambiguously, mirroring [`docs/SPECS/spec-017-apps-0_0_7.md`](SPECS/spec-017-apps-0_0_7.md) rev4 informational item 2 and [`docs/SPECS/spec-018-export_schema-0_0_7.md`](SPECS/spec-018-export_schema-0_0_7.md) rev2 M1).
  - [ ] Tests use Django's `unittest.mock.patch("django.db.router.db_for_read", ...)` (or `monkeypatch` against `django_strawberry_framework.types.resolvers.router.db_for_read`) to assert the cooperation contract hermetically — NO second SQLite file is created at package-test time; the cooperation is verified by spying on the router call, not by exercising two real connections (per [Decision 5](#decision-5--package-internal-tests-use-a-fixture-router-not-fakeshop_sharded)).
  - [ ] One-line module docstring on the test file (required by `D100`); each test carries a one-line docstring (required by `D102` because `tests/**` is NOT in the per-file ignore set when authoring test docstrings would be the root-cause fix — verified at `pyproject.toml:100-107` the per-file ignore for `tests/**/*.py` covers only `D` rules that the test pattern doesn't actually need; in practice all existing test files in `tests/optimizer/` carry per-function docstrings, so this is convention-matching, not gate-forcing).
  - [ ] No `# noqa` suppressions on any pydocstyle or annotation rule.
- [ ] Slice 2: Fakeshop live coverage under `FAKESHOP_SHARDED=1`
  - [ ] New `examples/fakeshop/test_query/test_multi_db.py` containing **two** live `/graphql/` HTTP tests against the sharded fakeshop layout (per [Test plan](#test-plan)); positioned next to the existing `test_library_api.py` so the reload-pattern from that file is reusable.
  - [ ] Tests gate on `FAKESHOP_SHARDED=1` by calling `pytest.skip("requires FAKESHOP_SHARDED=1", allow_module_level=True)` at module top **after** an `os.environ.get("FAKESHOP_SHARDED") != "1"` check (per [Decision 6](#decision-6--live-coverage-under-fakeshop_sharded1)). `pytest.mark.skipif(...)` would not work for the same load-time reason `config.settings`'s `DATABASES` is decided at module import time — the import below `if os.environ.get("FAKESHOP_SHARDED") == "1":` settles before `pytest.mark.skipif` would get to evaluate, so a `mark.skipif` test would still try to import models against a single-DB `DATABASES` dict.
  - [ ] Each test seeds rows on `shard_b` via `.using("shard_b")` and queries through `/graphql/` (the schema's root resolvers return `Item.objects.using("shard_b")` querysets for the routed flow per [Decision 4](#decision-4--no-routing-decoration-on-fakeshop-schemas)). The schema is NOT modified to inject routing; routing is consumer-shaped, and the test exercises consumer-shaped routing via fixture data + a custom queryset returned through a per-test resolver override (or, more simply, via an inline schema fixture next to the test).
  - [ ] Tests share the `_reload_project_schema_for_acceptance_tests` reload contract from `examples/fakeshop/test_query/test_library_api.py:17-43` — copy the autouse fixture into the new module verbatim (per [Decision 7](#decision-7--reuse-the-test_library_api-reload-fixture-verbatim)).
  - [ ] One-line module docstring (`D100`); per-test docstrings matching the existing fakeshop test-tree style.
- [ ] Slice 3: Promotion + docs
  - [ ] Flip [`Multi-database cooperation`](GLOSSARY.md#multi-database-cooperation) from `planned for 0.0.7` to `shipped (0.0.7)` in [`docs/GLOSSARY.md`](GLOSSARY.md): update the Index table row (currently `| [Multi-database cooperation](#multi-database-cooperation) | planned for `0.0.7` |` at line 88) and the entry body at line 679 (the body already describes the cooperation in present tense — minor wording tightening to remove "Pins the existing … cooperation" framing and replace it with "Pins the cooperation contract: …" past-tense framing matching shipped entries).
  - [ ] Update [`docs/README.md`](README.md): add a one-line forward-pointer at the end of the `### Sharded mode (multi-DB)` section (line 216) reading: "For the cooperation contract these shards run against — what the package guarantees under `.using()`, `Prefetch` chains, and `get_queryset` downgrades — see [`GLOSSARY.md#multi-database-cooperation`](GLOSSARY.md#multi-database-cooperation)." (per the [`KANBAN.md`](../KANBAN.md) card DoD bullet 5).
  - [ ] Update [`KANBAN.md`](../KANBAN.md): move `WIP-ALPHA-019-0.0.7` to the Done column with the next available `DONE-NNN-0.0.7` id (renumbering owned by the column-move pass, not pinned here). The past-tense Done body summarizes the shipped scope: cooperation contract spec'd at [`docs/SPECS/spec-019-multi_db-0_0_7.md`](SPECS/spec-019-multi_db-0_0_7.md) (canonical name; supersedes the card's `docs/spec-multi_db.md` placeholder per [Decision 1](#decision-1--spec-filename-and-canonical-naming)); tests in `tests/optimizer/test_multi_db.py` and `examples/fakeshop/test_query/test_multi_db.py`; GLOSSARY entry flipped to `shipped (0.0.7)`; one-line forward-pointer added to `docs/README.md`.
  - [ ] Update [`CHANGELOG.md`](../CHANGELOG.md): **append** to the existing `[0.0.7]` `### Added` subsection (do NOT create a second `[0.0.7]` heading per [Decision 9](#decision-9--joint-0_0_7-cut) — every `0.0.7` card under the joint cut appends to the same shared section). [`AGENTS.md`](../AGENTS.md) line 21 ("Do not update CHANGELOG.md unless explicitly instructed") — this Slice 3 bullet is the explicit instruction. Entry wording pinned in [Doc updates](#doc-updates).
  - [ ] No edits to [`README.md`](../README.md), [`GOAL.md`](../GOAL.md), or [`TODAY.md`](../TODAY.md). Justification: the cooperation contract is plumbing the package already honors; it is not a new consumer name-surface, the fakeshop schema is unchanged by this card, and `TODAY.md`'s query-shape snapshot is not affected (per [Decision 8](#decision-8--no-readme--goal--today-edits)). Same posture as [`docs/SPECS/spec-018-export_schema-0_0_7.md`](SPECS/spec-018-export_schema-0_0_7.md) Slice 3.
  - [ ] Version bump (deferred to **the last `0.0.7` card to ship**, NOT this card; per [Decision 9](#decision-9--joint-0_0_7-cut)): see [`docs/SPECS/spec-016-list_field-0_0_7.md`](SPECS/spec-016-list_field-0_0_7.md) Decision 10. This card does NOT bump `pyproject.toml`, `django_strawberry_framework/__init__.py`'s `__version__`, or `tests/base/test_init.py`'s pinned version assertion.
  - [ ] Zero new public exports — the cooperation contract is plumbing already in the package, not a new symbol. `__all__` is unchanged.
  - [ ] Final gates (same posture as [`docs/SPECS/spec-018-export_schema-0_0_7.md`](SPECS/spec-018-export_schema-0_0_7.md) DoD item 13):
    - [ ] `uv run ruff format .` passes.
    - [ ] `uv run ruff check --fix .` passes.
    - [ ] `uv run pytest --no-cov` (or scoped subset) passes; the explicit `--no-cov` opts out of `pytest.ini`'s auto-applied `--cov` per the per-pass-gates contract; coverage enforcement is CI's job (`pyproject.toml [tool.coverage.report] fail_under = 100`), not this slice's.

## Problem statement

`django-strawberry-framework` already cooperates with Django's multi-database machinery in source: [`django_strawberry_framework/types/resolvers.py:82`](../django_strawberry_framework/types/resolvers.py) sets `state.db = router.db_for_read(field_meta.related_model, instance=instance)` on FK-id elision stubs, the optimizer's queryset diffing rule ([`Queryset diffing`](GLOSSARY.md#queryset-diffing)) preserves whatever `.using(alias)` the consumer applied, and the optimizer's `Prefetch` downgrade for [`get_queryset`](GLOSSARY.md#get_queryset-visibility-hook) hooks runs against whatever queryset the consumer's hook returned (which carries its own `_db`). The fakeshop example already ships a working two-shard layout: `examples/fakeshop/config/settings.py:115-125` registers `default` → `db_shard_a.sqlite3` and `shard_b` → `db_shard_b.sqlite3` when `FAKESHOP_SHARDED=1`, and [`examples/fakeshop/apps/products/management/commands/seed_shards.py`](../examples/fakeshop/apps/products/management/commands/seed_shards.py) materializes both shards via `Model.objects.using(alias).create(...)` calls in [`examples/fakeshop/apps/products/services.py:174-222`](../examples/fakeshop/apps/products/services.py).

But none of this is specified, tested, or documented as a package contract. The consumer reading [`docs/README.md`](README.md)'s `### Sharded mode (multi-DB)` section (line 204) sees the example project's shard wiring with no forward-pointer to a package commitment. The migrant from `graphene-django` or `strawberry-graphql-django` looking for "does this package work under `DATABASE_ROUTERS` / `.using()` / sharded reads?" has to read the source. The optimizer's behavior under `.using()` is implicit in [`Queryset diffing`](GLOSSARY.md#queryset-diffing) but never pinned with a test that would catch a regression (e.g., a future optimizer refactor that re-fetched the queryset via `Model.objects.all()` would silently lose the consumer's `.using("shard_b")` and the test suite would not notice).

Both reference packages take different stances:

- `strawberry-django` does not document multi-db behavior. Its `optimizer.py` (verified at `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/optimizer.py`) does not call `router.db_for_*` anywhere; cooperation rides entirely on the queryset's `_db` attribute. Adding a contract document moves us ahead of upstream on this axis.
- `graphene-django` does not document multi-db either; its filter / connection layer is database-agnostic by accident, not by design.

The shipping bar is deliberately low — this is a tests + docs card with **zero production code change**. The discipline the card needs to enforce is **what the contract covers and what it does NOT**: routing through Django's `router.db_for_*` API and queryset `_db` propagation are in scope; first-class sharding-aware planning (cross-shard joins, automatic shard selection based on FK, multi-shard aggregates, `Meta.preferred_database`) is explicitly deferred to [`BACKLOG.md`](../BACKLOG.md) item 41 (per the [`KANBAN.md`](../KANBAN.md) card's Out of scope bullet).

## Current state

- [`django_strawberry_framework/types/resolvers.py`](../django_strawberry_framework/types/resolvers.py) lines 70-83 set `_state.db = router.db_for_read(field_meta.related_model, instance=instance)` inside `_build_fk_id_stub`. `instance=instance` is `root if hasattr(root, "_state") else None`, so the stub inherits the routing context of the parent row when one exists. This is the package's only explicit `router.db_for_read` call; verified by `grep -rn "router\|using\|_db\|db_for" django_strawberry_framework/` returning that single hit.
- [`django_strawberry_framework/optimizer/extension.py`](../django_strawberry_framework/optimizer/extension.py) and [`walker.py`](../django_strawberry_framework/optimizer/walker.py) do NOT call `router.db_for_*` anywhere; cooperation rides entirely on the queryset's `_db` attribute being preserved through plan application. The [`Queryset diffing`](GLOSSARY.md#queryset-diffing) rule means: if the consumer's resolver returns `Item.objects.using("shard_b").select_related("category")`, the optimizer adds `prefetch_related("entries")` on top via `qs.prefetch_related(...)` (which preserves `_db`), and the consumer's `_db` survives.
- [`examples/fakeshop/config/settings.py:115-125`](../examples/fakeshop/config/settings.py) registers the sharded `DATABASES` layout when `FAKESHOP_SHARDED=1` (mutually exclusive with the single-DB `db.sqlite3` mode). Without the env var the single-DB mode is active; the test suite runs in single-DB mode by default.
- [`examples/fakeshop/apps/products/services.py`](../examples/fakeshop/apps/products/services.py) lines 157-222 use `Model.objects.using(db_alias).create(...)` to seed shards; the `services.py` body proves the cooperation works at write time (rows land on the right shard when the alias is threaded through). The read-time cooperation through `/graphql/` is not exercised by any existing test — Slice 2 closes that gap.
- [`examples/fakeshop/test_query/test_library_api.py:17-43`](../examples/fakeshop/test_query/test_library_api.py) carries the autouse `_reload_project_schema_for_acceptance_tests` fixture; the same fixture must be copied into Slice 2's new file because package tests clear the registry and require schema re-finalize on each run.
- No `DATABASE_ROUTERS` are registered in `examples/fakeshop/config/settings.py` (verified by `grep -n "DATABASE_ROUTERS" config/settings.py` returning empty). All routing in fakeshop is explicit via `.using(alias)`; the cooperation contract this card pins works the same way against an implicit router and an explicit `.using()`, but the fakeshop live tests use `.using()` because that's what fakeshop's existing seed pipeline does.
- [`docs/GLOSSARY.md`](GLOSSARY.md) line 679 already carries the `## Multi-database cooperation` entry with status `planned for 0.0.7` and a paragraph describing the cooperation in present tense. Slice 3 flips the status and tightens the body to past-tense "shipped" wording.
- [`tests/optimizer/`](../tests/optimizer/) ships seven test modules today (verified by `ls tests/optimizer/`): `test_definition_order.py`, `test_extension.py`, `test_field_meta.py`, `test_hints.py`, `test_plans.py`, `test_relay_id_projection.py`, `test_walker.py`. Adding `test_multi_db.py` extends this set in place; no new subdirectory needed.
- [`pyproject.toml`](../pyproject.toml) line 4 pins `version = "0.0.6"`; [`django_strawberry_framework/__init__.py`](../django_strawberry_framework/__init__.py) line 26 pins `__version__ = "0.0.6"`; [`tests/base/test_init.py`](../tests/base/test_init.py) line 11 pins `assert __version__ == "0.0.6"`. The `[0.0.7]` heading in [`CHANGELOG.md`](../CHANGELOG.md) already carries `### Added` entries for `DONE-016-0.0.7` ([`DjangoListField`](GLOSSARY.md#djangolistfield)), `DONE-017-0.0.7` ([`Django AppConfig`](GLOSSARY.md#django-appconfig)), and `DONE-018-0.0.7` ([`Schema export management command`](GLOSSARY.md#schema-export-management-command)) per the joint-cut policy — this card appends a fourth bullet without bumping the version.

## Goals

1. Ship [`docs/spec-019-multi_db-0_0_7.md`](spec-019-multi_db-0_0_7.md) (this document) documenting the cooperation contract: which Django multi-db facilities the package respects (database routers, explicit `.using()`, `_state.db` propagation through FK-id elision), and what behavior the consumer can rely on (optimizer plans correctly under `.using()`; `Prefetch` chains respect routing; `get_queryset` downgrade respects routing; strictness mode tracks the originating connection).
2. Ship `tests/optimizer/test_multi_db.py` covering the **six tests** pinned in [Test plan](#test-plan): (a) FK-id elision stub `_state.db` is set via `router.db_for_read`, (b) the router-call's `instance=` argument is the parent row (proving the cooperation respects the parent's routing context), (c) the FK-id elision stub returns `None` for a `None` FK (the `instance` arg is forwarded as `None` when the parent row has no `_state` attribute), (d) the optimizer's `Prefetch` plan does not re-resolve the queryset's connection (a fixture queryset with `using="shard_b"` round-trips through `walker.plan_optimizations` unchanged), (e) the strictness-mode N+1 check fires on the queryset's connection (a `using="shard_b"` queryset's lazy-load lights up `OptimizerError` against the same alias), (f) the `get_queryset` downgrade preserves the consumer's `.using(...)` on the downgraded `Prefetch`.
3. Ship `examples/fakeshop/test_query/test_multi_db.py` containing **two** live `/graphql/` HTTP tests against the sharded fakeshop layout: (a) seeding rows on `shard_b` and reading them through `/graphql/` via a `.using("shard_b")` root resolver returns the seeded rows, (b) cross-shard reads return only rows from the queried alias (a row seeded on `default` is not visible through a `using("shard_b")` resolver, demonstrating shard isolation under the existing cooperation contract).
4. Flip [`Multi-database cooperation`](GLOSSARY.md#multi-database-cooperation) in [`docs/GLOSSARY.md`](GLOSSARY.md) from `planned for 0.0.7` to `shipped (0.0.7)`; tighten the entry body to past-tense wording matching shipped entries.
5. Add a one-line forward-pointer to [`docs/README.md`](README.md)'s `### Sharded mode (multi-DB)` section linking to the GLOSSARY entry, so a consumer reading the example onboarding sees the package's commitment.
6. Preserve [`AGENTS.md`](../AGENTS.md) line 20's "Add settings keys only when the feature that needs them lands" by omitting any new `DJANGO_STRAWBERRY_FRAMEWORK.*` settings keys.
7. Keep `__all__` unchanged — the cooperation contract is plumbing the package already honors, not a new symbol.

## Non-goals

- First-class sharding-aware planning — cross-shard joins, automatic shard selection based on FK, multi-shard aggregates, `Meta.preferred_database`. Tracked in [`BACKLOG.md`](../BACKLOG.md) item 41 (post-`1.0.0` differentiation) per the [`KANBAN.md`](../KANBAN.md) card's Out of scope bullet.
- A package-level `DATABASE_ROUTERS` opinion. Routing policy is consumer-shaped; the package cooperates with whatever router the consumer registers and does not opine on which model lives on which shard.
- New consumer-facing API. No new symbol lands. No new `Meta.*` key. No new settings key. No new exception class. The contract is a behavior surface the package already exhibits.
- Production code changes in `0.0.7`. The cooperation already exists at [`types/resolvers.py:82`](../django_strawberry_framework/types/resolvers.py). This card pins the behavior with tests + docs (per [Decision 2](#decision-2--no-production-code-change)); production code changes belong in follow-up cards if a test surfaces a regression.
- A `manage.py` helper for shard introspection or cross-shard queries. The example project's `seed_shards` command lives in `examples/fakeshop/`, not in the package; the package does not ship multi-db tooling.
- Settings-backed default shard alias. [`AGENTS.md`](../AGENTS.md) line 20 forbids preemptive settings; if a future card needs one (e.g., a planning hint that the package should prefer one shard), it adds the key alongside the consuming behavior.
- Auto-calling [`finalize_django_types()`](GLOSSARY.md#finalize_django_types) per database alias. Finalization is global to the process and identical regardless of routing; it does not need to be re-run when the queryset changes connections.

## Borrowing posture

Multi-database cooperation is a Django capability neither reference package documents as a contract. This card has no upstream surface to borrow.

### From `strawberry-django` — no precedent to borrow

Local source path: `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/optimizer.py`. Verified by inspection: the file does not call `router.db_for_*` anywhere; multi-db cooperation rides entirely on the queryset's `_db` attribute (the same shape our package ships today). There is no `docs/multi-db.md` in the upstream's repo; no `tests/test_multi_db.py`; no documented stance on what consumers can rely on under `.using()`.

The shape we ship is functionally equivalent to the upstream's — a queryset's `_db` survives `select_related` / `prefetch_related` / `Prefetch` chains because Django's queryset API preserves it — but we additionally call `router.db_for_read(...)` on FK-id elision stubs (the `_build_fk_id_stub` path at [`types/resolvers.py:70-83`](../django_strawberry_framework/types/resolvers.py)), which the upstream does not. The `router.db_for_read` call is necessary because an FK-id elision stub is a freshly-constructed model instance with no `_db` from a queryset to inherit; without the router lookup the stub would default to whatever `_state.db` Django picks for new instances (which is `None` until `save()`). The upstream's optimizer does not implement FK-id elision, so the cooperation gap doesn't arise there.

### From `graphene-django` — no precedent to borrow

Local source path: `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/`. Verified: no `router.db_for_*` calls anywhere in the package source. The package is database-agnostic by accident — `RelayConnectionField` and `DjangoListField` resolvers return whatever queryset the consumer hands them, and queryset `.using()` propagates through Django's machinery without the package noticing.

### Explicitly do not borrow

- A `DATABASE_ROUTERS` reference router class in the package. Routing policy is consumer-shaped; shipping a "default" router would impose an opinion the package has no business holding. Compare: Django ships no default router class either; the consumer registers one or doesn't.
- A `Meta.preferred_database` declarative shortcut. Tracked in [`BACKLOG.md`](../BACKLOG.md) item 41; out of scope here.
- Cross-shard join detection / rejection. The optimizer can't see across shards (each shard has its own connection); a consumer who writes `Item.objects.using("shard_a").filter(category__in=Category.objects.using("shard_b"))` gets whatever Django's queryset compiler does (typically an `OperationalError` from the cross-connection subquery). This card does not improve on or document that failure mode; [`BACKLOG.md`](../BACKLOG.md) item 41 covers it.

## User-facing API

The shipped consumer surface in `0.0.7` adds **no new symbols**. The contract is documented in [`docs/GLOSSARY.md#multi-database-cooperation`](GLOSSARY.md#multi-database-cooperation) and pinned with tests. No `__all__` change. No new `Meta.*` key. No new exception class.

### Default usage — explicit `.using(alias)` on the consumer queryset

```python path=null start=null
from apps.library import models
from django_strawberry_framework import DjangoType


class BookType(DjangoType):
    class Meta:
        model = models.Book
        fields = ("id", "title", "shelf")


@strawberry.type
class Query:
    @strawberry.field
    def books_on_shard_b(self, info) -> list[BookType]:
        return models.Book.objects.using("shard_b").select_related("shelf")
```

The package's contract:

- The optimizer's selection-tree walk respects the consumer's `select_related("shelf")` (per [`Queryset diffing`](GLOSSARY.md#queryset-diffing)) and adds any further optimizations on top via `qs.prefetch_related(...)` / `qs.only(...)` — both of which preserve the queryset's `_db`.
- FK-id elisions on forward relations route through `router.db_for_read(<related_model>, instance=<parent_row>)`, so the elision stub's `_state.db` matches the parent row's routing context.
- Strictness-mode N+1 detection fires against the queryset's connection — an unplanned `book.genres.all()` access on a `using("shard_b")` book lights up the `Potential N+1` warning / `OptimizerError` against the relation on that alias, not against a globally-routed re-read.
- The [`get_queryset` visibility hook](GLOSSARY.md#get_queryset-visibility-hook) cooperates with routing: a `get_queryset` body that returns `queryset.filter(...)` preserves the inbound `_db`, and the optimizer's `Prefetch` downgrade applies that filter on the same connection. A `get_queryset` body that explicitly `.using()`-switches the queryset is the consumer's call and the package honors it.

### Default usage — `DATABASE_ROUTERS` and implicit `db_for_read`

```python path=null start=null
# In settings.py
DATABASE_ROUTERS = ["myapp.routers.ShardRouter"]

# Consumer schema — no explicit .using() needed
@strawberry.type
class Query:
    @strawberry.field
    def all_books(self, info) -> list[BookType]:
        return models.Book.objects.all()  # router picks the connection
```

The package's contract under this shape: same as the explicit-`.using()` case. The router decides the connection at queryset evaluation time; the `_db` attribute is set on the queryset before the optimizer's plan application; FK-id elisions then call `router.db_for_read(<related_model>, instance=<parent_row>)` and the router's policy applies again for the related model.

### Error shapes

No new error shapes. The package does not raise on cross-shard queries (Django's `OperationalError` surfaces unchanged); the package does not raise on unrouted querysets (the `default` alias applies); the package does not raise on multi-shard `Prefetch` chains where each shard's queryset is independently consistent.

The one error shape the cooperation respects: strictness-mode N+1 detection ([`Strictness mode`](GLOSSARY.md#strictness-mode)) still fires under `using("shard_b")` if the relation is unplanned and would lazy-load. The error class (`OptimizerError`) and message (`"Unplanned N+1: <field>"`) are unchanged from the single-DB path.

## Architectural decisions

### Decision 1 — Spec filename and canonical naming

The spec file lives at **`docs/spec-019-multi_db-0_0_7.md`** (this document), NOT `docs/spec-multi_db.md` as the [`KANBAN.md`](../KANBAN.md) card body's `Definition of done` bullet 1 names it.

Justification:

- The structured `spec-<NNN>-<topic>-<0_0_X>.md` convention pinned in [`docs/SPECS/NEXT.md`](SPECS/NEXT.md) Step 6 and proven by every recent spec ([`docs/SPECS/spec-014-meta_primary-0_0_6.md`](SPECS/spec-014-meta_primary-0_0_6.md), [`docs/SPECS/spec-015-consumer_overrides_scalar-0_0_6.md`](SPECS/spec-015-consumer_overrides_scalar-0_0_6.md), [`docs/SPECS/spec-016-list_field-0_0_7.md`](SPECS/spec-016-list_field-0_0_7.md), [`docs/SPECS/spec-017-apps-0_0_7.md`](SPECS/spec-017-apps-0_0_7.md), [`docs/SPECS/spec-018-export_schema-0_0_7.md`](SPECS/spec-018-export_schema-0_0_7.md)) bakes the card's NNN and target patch into the filename. The card body's `docs/spec-multi_db.md` predates that convention and would land an unnumbered spec next to a numbered cohort, breaking the alphabetical archive ordering at `docs/SPECS/`.
- The Slice 3 [`KANBAN.md`](../KANBAN.md) update overwrites the stale `docs/spec-multi_db.md` reference in the card body to point at the canonical name, so the cross-reference resolves after archival (per [Step 8 of NEXT.md](SPECS/NEXT.md#step-8--archive-prior-specs-and-update-cross-references)).
- This Decision is enforcement, not innovation: the convention is already pinned in [`docs/SPECS/NEXT.md`](SPECS/NEXT.md) Step 6 and observed by every spec from 014 forward.

Alternatives considered (and rejected):

- **Honor the card body verbatim with `docs/spec-multi_db.md`.** Rejected: would diverge from the structured naming convention; would force a Step-8 archive rename anyway; would not match the [`KANBAN.md`](../KANBAN.md) sibling cards' filenames in the WIP / Done columns.
- **Ship as `docs/spec-019-multi-db-0_0_7.md` (hyphen separator in the topic slug).** Rejected: every prior spec uses snake_case for the topic slug (`list_field`, `meta_primary`, `consumer_overrides_scalar`, `export_schema`, `apps`, `deferred_scalars`). `multi_db` matches the convention; `multi-db` would be a one-spec outlier.

### Decision 2 — No production code change

The card ships **zero production code change**. The cooperation surface this spec pins (`router.db_for_read` at [`types/resolvers.py:82`](../django_strawberry_framework/types/resolvers.py); queryset `_db` propagation through the optimizer; `get_queryset` downgrade routing; strictness mode under `.using()`) already exists in source today.

Justification:

- [`KANBAN.md`](../KANBAN.md) card body: "Status: planned. **The cooperation already exists in source; this card pins the contract with a spec, tests, and docs.**" The card explicitly frames this as a documentation + tests card.
- The cooperation is grep-verifiable: `grep -rn "router\.\|\.using\b\|_state\.db\b" django_strawberry_framework/` returns one production line ([`types/resolvers.py:82`](../django_strawberry_framework/types/resolvers.py)) and zero other touchpoints; the optimizer's cooperation rides on queryset `_db` propagation, which is a Django queryset contract, not a package one.
- Pinning a contract with tests is the cheapest way to prevent regression. Adding production code (e.g., a `router.allow_relation` consultation, a `Meta.preferred_database` hint) would expand the surface beyond what the contract actually documents and would re-litigate the [`BACKLOG.md`](../BACKLOG.md) item 41 boundary.

Alternatives considered (and rejected):

- **Add a `router.allow_relation(obj1, obj2)` consultation in the FK-id elision path.** Rejected: `allow_relation` is for cross-DB foreign-key validity; FK-id elision happens within a single connection, so calling it would be a no-op (Django's queryset cross-shard validation already runs at queryset evaluation, before the optimizer sees the row).
- **Add a `Meta.preferred_database` hint for routing.** Rejected: covered by [`BACKLOG.md`](../BACKLOG.md) item 41; pre-shipping it would impose API surface this card does not have evidence to design correctly.
- **Refactor `_build_fk_id_stub` to read `instance=parent_row` through a helper.** Rejected: the current code is six lines and reads cleanly; introducing a helper for one call site would be over-abstraction.

### Decision 3 — The cooperation contract: four axes

The contract this card pins covers exactly four cooperation axes. Listed here with the source-of-truth location for each:

1. **`router.db_for_read` on FK-id elision stubs.** [`types/resolvers.py:70-83`](../django_strawberry_framework/types/resolvers.py). When the optimizer elides a forward-relation `id`-only selection, the stub is built via `stub = field_meta.related_model(pk=related_id)` and then `state.db = router.db_for_read(field_meta.related_model, instance=instance)` runs, where `instance` is `root if hasattr(root, "_state") else None`. The router's policy decides the stub's `_state.db`; subsequent attribute reads on the stub hit that connection.
2. **Queryset `_db` propagation through the optimizer.** [`optimizer/walker.py`](../django_strawberry_framework/optimizer/walker.py), [`optimizer/extension.py`](../django_strawberry_framework/optimizer/extension.py). The optimizer's plan application calls `qs.select_related(...)`, `qs.prefetch_related(...)`, `qs.only(...)` (the [`only()` projection](GLOSSARY.md#only-projection) path) — all of which preserve the queryset's `_db` attribute by Django queryset contract. A consumer's `.using("shard_b")` queryset survives plan application unchanged. This is verified by Slice 1's test (d).
3. **`Prefetch(queryset=...)` routing inheritance.** [`Queryset diffing`](GLOSSARY.md#queryset-diffing) rule. When the optimizer generates a `Prefetch` for a downgraded join (because the target type has a custom [`get_queryset`](GLOSSARY.md#get_queryset-visibility-hook)), the inner queryset is whatever the consumer's `get_queryset` returned. If `get_queryset` was passed a `using("shard_b")` queryset, its return value carries the same `_db` (Django's queryset filter methods preserve `_db`), and the `Prefetch` uses that connection. Verified by Slice 1's test (f).
4. **Strictness mode under `.using()`.** [`types/resolvers.py:119-154`](../django_strawberry_framework/types/resolvers.py) (`_check_n1`). The strictness check fires when a relation access would actually lazy-load; the lazy-load itself hits whatever connection the parent row was loaded from (via Django's `_state.db` propagation through the descriptor protocol). The strictness machinery does not consult the router; it consults `_prefetched_objects_cache` and `_state.fields_cache` on the row. A `using("shard_b")` lazy-load lights up on the same alias the parent row was loaded from. Verified by Slice 1's test (e).

Anything outside these four axes is **out of scope for the contract**:

- Cross-shard joins. The optimizer cannot plan them; the consumer's queryset compiler raises `OperationalError`; the package does not improve on this.
- Multi-shard aggregates. The optimizer aggregates against one queryset at a time, on its alias; cross-shard aggregation requires consumer-side logic.
- Routing policy. Consumer-shaped.
- `default_database` / preferred-shard selection. Consumer-shaped.

Justification:

- The four-axis list maps 1-to-1 to the [`KANBAN.md`](../KANBAN.md) card's "Confirm …" bullets (router cooperation; optimizer plan correctness under `.using()`; strictness mode tracking originating connection; `get_queryset` downgrade respecting routing). Pinning the axes here lets the test plan target one test per axis with no gaps.
- Anything not on the list is either an in-scope behavior the package already exhibits via Django's queryset contract (and therefore needs no package-level pinning) or an out-of-scope future-card concern.

### Decision 4 — No routing decoration on fakeshop schemas

The fakeshop schemas at [`examples/fakeshop/apps/library/schema.py`](../examples/fakeshop/apps/library/schema.py) and [`examples/fakeshop/apps/products/schema.py`](../examples/fakeshop/apps/products/schema.py) are NOT modified to inject `.using()` routing. Slice 2's live tests exercise routing through a per-test schema fixture (inline `@strawberry.type` Query class declared inside the test module) or a temporary monkeypatched root resolver, NOT by editing the example app schemas.

Justification:

- Routing policy is consumer-shaped (per [Decision 3](#decision-3--the-cooperation-contract-four-axes)); a fakeshop schema with hard-coded `.using("shard_b")` would be misleading example code suggesting routing is the package's call. The default fakeshop schemas should continue to demonstrate the simplest possible Strawberry surface, which is single-DB.
- The live test's purpose is to prove cooperation under the existing `FAKESHOP_SHARDED=1` infrastructure, not to redesign the example schemas.
- Mirrors the [`docs/SPECS/spec-016-list_field-0_0_7.md`](SPECS/spec-016-list_field-0_0_7.md) Decision 9 posture for `DjangoListField` (added a fakeshop demonstration as a *sibling* root field rather than rewriting existing list-resolver schema entries).

Alternatives considered (and rejected):

- **Add a `books_on_shard_b: list[BookType]` sibling resolver to `apps/library/schema.py`.** Rejected: would clutter the example app schema with a multi-db demonstration that only triggers under `FAKESHOP_SHARDED=1`; the routing would always read from `shard_b` regardless of env var, which is wrong under single-DB mode (where `shard_b` doesn't exist in `DATABASES`).
- **Add `DATABASE_ROUTERS` to `examples/fakeshop/config/settings.py`.** Rejected: would impose a routing opinion on the example project; consumers exercising the existing single-DB and sharded modes don't need a router class.

### Decision 5 — Package-internal tests use a fixture router, not `FAKESHOP_SHARDED`

`tests/optimizer/test_multi_db.py` does NOT depend on `FAKESHOP_SHARDED=1` or on the existence of `db_shard_b.sqlite3`. Tests mock `django.db.router.db_for_read` (via `unittest.mock.patch` or pytest's `monkeypatch` against the imported alias `django_strawberry_framework.types.resolvers.router.db_for_read`) and assert the cooperation contract hermetically.

Justification:

- Package-internal tests must be runnable without any fakeshop-side env var. The test suite already runs against a single SQLite by default; introducing a real second SQLite would (a) require materializing it before the test runs, (b) require teardown logic to avoid polluting the dev `db.sqlite3`, (c) double the per-test cost without testing anything the mock doesn't catch.
- The cooperation contract is "we call `router.db_for_read` with this signature and this `instance` argument" — that's a router-call assertion, not a routing-outcome assertion. The router's outcome (which alias gets returned) is consumer-shaped; the package's contribution is the call itself.
- The fakeshop live test in Slice 2 is what exercises a real second connection end-to-end. The two test layers compose: Slice 1 pins the package's router call shape; Slice 2 pins the end-to-end cooperation under a real router policy.

Mock target (pinned):

- `monkeypatch.setattr(django_strawberry_framework.types.resolvers.router, "db_for_read", Mock(return_value="default"))` — patches the imported alias inside the resolvers module, so the patch survives the `from django.db import router` import at the top of `types/resolvers.py`.
- Equivalently: `unittest.mock.patch.object(django_strawberry_framework.types.resolvers, "router")` followed by setting the mocked router's `db_for_read.return_value`. Both shapes are acceptable; tests use whichever reads cleaner per test.

Alternatives considered (and rejected):

- **Run package-internal tests under a real two-DB SQLite layout.** Rejected: cost / setup / teardown burden, and the assertion granularity is worse (a router-call assertion catches a regression where the call is dropped, even when the alias outcome happens to match the default).
- **Mock `router.db_for_read` globally via `django.db.router.db_for_read`.** Rejected: monkey-patching the global would leak to other tests in the suite. The module-level alias inside `types.resolvers` is the right scope.

### Decision 6 — Live coverage under `FAKESHOP_SHARDED=1`

`examples/fakeshop/test_query/test_multi_db.py` skips the entire module at collection time when `os.environ.get("FAKESHOP_SHARDED") != "1"` via `pytest.skip(reason, allow_module_level=True)`, NOT `pytest.mark.skipif`.

Justification:

- `config.settings` decides `DATABASES` at module-import time, based on `os.environ.get("FAKESHOP_SHARDED")`. Importing the fakeshop project models under single-DB mode and then trying to query against `using("shard_b")` would raise `ConnectionDoesNotExist` because `shard_b` is not registered in `DATABASES`. The `pytest.skip(allow_module_level=True)` shape skips before any imports below it run, so the model imports happen only when the env var is set.
- `pytest.mark.skipif(os.environ.get("FAKESHOP_SHARDED") != "1", ...)` would not work for the same reason: the test module's imports run before pytest evaluates the mark, so the module would fail to import in single-DB mode (the per-test resolver fixtures would try to construct querysets against `shard_b`).
- The pattern mirrors [`examples/fakeshop/test_query/test_library_api.py`](../examples/fakeshop/test_query/test_library_api.py)'s autouse fixture shape (Slice 2 copies that fixture) but with an additional early-module-skip guard.

Pinned shape (test-module header):

```python path=null start=null
"""Live /graphql/ multi-database cooperation tests against the sharded fakeshop layout."""

import os

import pytest

if os.environ.get("FAKESHOP_SHARDED") != "1":
    pytest.skip(
        "requires FAKESHOP_SHARDED=1 (the sharded DATABASES layout)",
        allow_module_level=True,
    )

# Below this line, FAKESHOP_SHARDED=1 is set and `shard_b` is in DATABASES.
import importlib
import sys

import pytest as _pytest_for_fixtures  # noqa: F401 — autouse fixture below uses pytest
from apps.library import models
from django.db import connection
from django.test import Client
from django.urls import clear_url_caches

from django_strawberry_framework.registry import registry
```

Alternatives considered (and rejected):

- **`pytest.mark.skipif(...)` on each test.** Rejected per the module-import-time `DATABASES` decision above.
- **`pytest.mark.skipif(...)` on the test class.** Rejected for the same reason; mark evaluation happens after import.
- **Move the entire test into `examples/fakeshop/tests/` (non-HTTP).** Rejected: the cooperation surface this test pins is end-to-end through `/graphql/`, including the URL routing, view, schema execution, and JSON serialization; the `test_query/` tree is the right home. The package-internal `tests/optimizer/test_multi_db.py` is the non-HTTP layer.

### Decision 7 — Reuse the `test_library_api` reload fixture verbatim

`examples/fakeshop/test_query/test_multi_db.py` copies the `_reload_project_schema_for_acceptance_tests` autouse fixture from [`examples/fakeshop/test_query/test_library_api.py:17-43`](../examples/fakeshop/test_query/test_library_api.py) verbatim — same body, same docstring, same module-reload sequence (`apps.library.schema` → `config.schema` → `config.urls`).

Justification:

- The fixture is required for any test that runs after a package test that clears the registry; the multi-db tests are no exception.
- Copying the fixture verbatim (rather than moving it to a conftest.py) keeps the fixture local to the file that needs it; the test file's first ~30 lines remain self-contained and a reader does not have to chase a sibling file.
- The trade-off is duplicated code, but the fixture is small (~25 lines) and copying it follows the existing fakeshop test-tree pattern (the README at `examples/fakeshop/test_query/README.md` does not specify a shared `conftest.py`, and `test_library_api.py` is the only existing `test_query/` test file).
- If a future card moves the fixture to a `conftest.py` shared across `test_query/` files (justified once 2+ files need it), the move is a Definition-7 follow-up under its own spec. The boundary is "do not pre-emptively factor."

Alternatives considered (and rejected):

- **Move the fixture to `examples/fakeshop/test_query/conftest.py` and let both files autouse it.** Rejected per the "do not pre-emptively factor" boundary; the conftest-extraction is justified by a second test file needing it, and this spec's job is to add that second file, not to settle the factoring question.
- **Skip the reload fixture and hope tests run in a friendly order.** Rejected: registry-clearing package tests run before `examples/fakeshop/test_query/` tests in pytest's discovery order, so the fixture is load-bearing for the test suite to pass.

### Decision 8 — No README / GOAL / TODAY edits

This card does NOT edit [`README.md`](../README.md), [`GOAL.md`](../GOAL.md), or [`TODAY.md`](../TODAY.md).

Justification:

- The README's status section names consumer-facing primitives ([`DjangoType`](GLOSSARY.md#djangotype), the optimizer, [`DjangoListField`](GLOSSARY.md#djangolistfield)); the multi-database cooperation contract is plumbing the package already honors, not a new consumer-name surface.
- `GOAL.md`'s astronomy showcase walks through model definitions and the sidecar files (`filters.py`, `orders.py`, `aggregates.py`, `fields.py`); none of which is multi-db-specific. The migration shape section names `graphene-django` / `strawberry-graphql-django` / DRF + django-filter migrants, none of which leans on multi-db cooperation as a primary feature.
- `TODAY.md` is a query-shape-and-capability snapshot ("what GraphQL queries work in fakeshop today?"). The cooperation contract is not a query-shape change; the fakeshop schema is unchanged by this card.
- Same posture as [`docs/SPECS/spec-018-export_schema-0_0_7.md`](SPECS/spec-018-export_schema-0_0_7.md) Slice 3 and [`docs/SPECS/spec-017-apps-0_0_7.md`](SPECS/spec-017-apps-0_0_7.md) Slice 3.

The one user-facing breadcrumb is the [`docs/README.md`](README.md) `### Sharded mode (multi-DB)` one-liner per the card DoD bullet 5 — that's `docs/README.md`, the documentation index, not the root `README.md`.

### Decision 9 — Joint `0.0.7` cut

`0.0.7` ships under the joint-cut policy from [`docs/SPECS/spec-016-list_field-0_0_7.md`](SPECS/spec-016-list_field-0_0_7.md) [Decision 10](SPECS/spec-016-list_field-0_0_7.md#decision-10--joint-007-cut): the two remaining WIP cards in the bundle — `WIP-ALPHA-019-0.0.7` (this card) and `WIP-ALPHA-020-0.0.7` (warning-free scalar registration) — accumulate `### Added` entries under the same `[0.0.7]` heading in [`CHANGELOG.md`](../CHANGELOG.md). The version bump in `pyproject.toml`, `django_strawberry_framework/__init__.py`'s `__version__` line, and `tests/base/test_init.py`'s pinned version assertion is owned by whichever card ships last in the bundle, NOT this card.

Justification:

- Restates [`docs/SPECS/spec-016-list_field-0_0_7.md`](SPECS/spec-016-list_field-0_0_7.md) [Decision 10](SPECS/spec-016-list_field-0_0_7.md#decision-10--joint-007-cut) verbatim so this card's reader does not have to chase the cross-spec reference.
- Per [`KANBAN.md`](../KANBAN.md) line 50: "The last `0.0.7` card to ship owns the version bump from `0.0.6` per Decision 10 of `docs/SPECS/spec-016-list_field-0_0_7.md`." The cross-card policy is already pinned in the [`KANBAN.md`](../KANBAN.md); this Decision pulls it into the spec so Slice 3's checklist can reference it.
- The [`CHANGELOG.md`](../CHANGELOG.md) `[0.0.7]` `### Added` section already carries `DONE-016-0.0.7`'s [`DjangoListField`](GLOSSARY.md#djangolistfield), `DONE-017-0.0.7`'s [`Django AppConfig`](GLOSSARY.md#django-appconfig), and `DONE-018-0.0.7`'s [`Schema export management command`](GLOSSARY.md#schema-export-management-command) entries (verified at [`CHANGELOG.md`](../CHANGELOG.md) lines 24-30); this card appends a fourth bullet for [`Multi-database cooperation`](GLOSSARY.md#multi-database-cooperation).

The Slice 3 doc-updates list explicitly excludes the version bump.

Alternatives considered (and rejected):

- **This card bumps `0.0.7` because the cooperation contract is the natural release-cut sentinel.** Rejected: ship order is determined by which card a maintainer picks up next, not by topical fit; pinning the bump to a specific card creates a sequencing constraint that has no engineering justification.
- **Add a separate `TODO-ALPHA-XXX-0.0.7 — 0.0.7 release cut` card to [`KANBAN.md`](../KANBAN.md) that owns the bump.** Rejected: out of scope for this spec (the spec's boundary forbids editing [`KANBAN.md`](../KANBAN.md) outside the column move in Slice 3); the "last card to ship" policy is workable as-is.

## Implementation plan

The slice ships as **three slices** aligned with the [Slice checklist](#slice-checklist). Each slice maps to one commit; squashing all three into a single PR is acceptable given the small surface.

| Slice | Files touched | New tests | Approx. line delta |
| --- | --- | --- | --- |
| 1 — Package-internal tests | `tests/optimizer/test_multi_db.py` (new) | 6 (FK-id elision router call; elision router `instance=parent_row`; elision returns `None` for null FK; optimizer plan preserves queryset `_db`; strictness mode under `.using()`; `get_queryset` downgrade preserves `.using()`) | `+180 / -0` |
| 2 — Fakeshop live coverage | `examples/fakeshop/test_query/test_multi_db.py` (new) | 2 (live `.using("shard_b")` round trip; shard isolation — rows on `default` not visible through `using("shard_b")` resolver) | `+130 / -0` |
| 3 — Promotion + docs | [`docs/GLOSSARY.md`](GLOSSARY.md), [`docs/README.md`](README.md), [`KANBAN.md`](../KANBAN.md), [`CHANGELOG.md`](../CHANGELOG.md) | 0 | `+20 / -6` |

Total expected delta: ~330 lines across the three slices.

The three slices must be authored in order. Slice 2 depends on Slice 1 (the package-internal contract pins must exist before the live tests can target a documented behavior); Slice 3 depends on Slice 2 (the [`CHANGELOG.md`](../CHANGELOG.md) `### Added` line and [`KANBAN.md`](../KANBAN.md) Done body must describe shipped, tested coverage, not a half-landed one).

## Edge cases and constraints

- **`router.db_for_read` `instance=` argument can be `None`.** [`types/resolvers.py:80-82`](../django_strawberry_framework/types/resolvers.py): `instance = root if hasattr(root, "_state") else None`. Django's `db_for_read(model, instance=None, **hints)` documented signature accepts `None`; the package-default behavior (when no `DATABASE_ROUTERS` are registered) returns `"default"`. Slice 1 test (c) pins this with a synthetic test double that has no `_state` attribute.
- **FK-id elision returns `None` for nullable FK.** [`types/resolvers.py:74-76`](../django_strawberry_framework/types/resolvers.py): `if related_id is None: return None`. The `router.db_for_read` call only runs when `related_id is not None`; a `None` FK never reaches the router. Slice 1 does not need a separate test for this branch beyond test (c) — the early-return covers both the no-FK and no-instance cases.
- **Mocking `router` at the resolver-module level.** `django.db.router` is a module-level singleton; `from django.db import router` in [`types/resolvers.py:27`](../django_strawberry_framework/types/resolvers.py) binds the local name `router` to that singleton. Patching `django.db.router.db_for_read` globally would affect every test; patching `django_strawberry_framework.types.resolvers.router.db_for_read` is module-local and the pytest `monkeypatch` fixture handles teardown automatically (per [Decision 5](#decision-5--package-internal-tests-use-a-fixture-router-not-fakeshop_sharded)).
- **`pytest.skip(allow_module_level=True)` runs before imports below it.** This is the load-bearing detail for [Decision 6](#decision-6--live-coverage-under-fakeshop_sharded1): the test file's `from apps.library import models` line below the skip block runs only when the skip didn't fire. Under single-DB mode, the import never runs; under `FAKESHOP_SHARDED=1`, the import runs against a `DATABASES` dict that has both `default` and `shard_b`.
- **Sharded-mode pytest collection.** Per `examples/fakeshop/config/settings.py:115-125`, `FAKESHOP_SHARDED=1` registers both shards in `DATABASES`. Django creates `test_db_shard_a.sqlite3` and `test_db_shard_b.sqlite3` during pytest (per Django's `TEST` config defaults); the seed_shards command's shard files (`db_shard_a.sqlite3` / `db_shard_b.sqlite3`) are untouched by the test suite.
- **`pytest --no-cov` and the coverage gate.** Per [`docs/SPECS/spec-018-export_schema-0_0_7.md`](SPECS/spec-018-export_schema-0_0_7.md) DoD item 13, workers run `uv run pytest --no-cov` locally; the 100% coverage gate is CI's job (`pyproject.toml [tool.coverage.report] fail_under = 100`). This card's new tests contribute to the gate but do not enforce it locally.
- **Test-module docstring requirement.** `pyproject.toml [tool.ruff.lint.per-file-ignores]` covers `tests/**/*.py` (verified at lines 100-107 of `pyproject.toml`); the ignore list for the tests glob includes the relevant `D` rules so test-module docstrings are not gate-forced. They are added for convention-matching with the existing `tests/optimizer/test_*.py` files, NOT for ruff compliance. `# noqa` suppressions for `D` rules in tests are unnecessary; the test files simply carry one-line docstrings to match the existing pattern.
- **`tests/optimizer/test_extension.py` and `tests/optimizer/test_walker.py` already cover non-routing optimizer behavior.** This card's new module sits next to them with a focused scope (multi-db only); there is no overlap with the existing modules' assertions.
- **Order independence of Slice 1 tests.** Each test uses pytest's `monkeypatch` fixture for any `router` mock so the patch is automatically removed at end of test. Tests can run in any collection order without leaking state.
- **`Prefetch` chains under `.using()`.** Django's `Prefetch(lookup, queryset=qs)` carries `qs._db` for the inner query, regardless of the parent queryset's `_db`. The optimizer's downgrade path constructs `Prefetch` from the consumer's `get_queryset` return value, which carries its own `_db`. This is a Django contract, not a package contract — Slice 1's test (f) pins the package's *cooperation* with that contract (we don't accidentally rebuild the queryset and lose the `_db`).
- **Optimizer plan cache key does NOT include the database alias.** Per the shipped [`Plan cache`](GLOSSARY.md#plan-cache) entry, cache keys include the operation AST, target model, and root runtime path — not the queryset's `_db`. Two resolvers on the same model targeting different shards share a cached plan; correct, because the plan is selection-shaped, not connection-shaped. This is a non-decision in this card (the plan cache is unchanged); pinned here as an edge-case clarification.

## Test plan

Tests live across two trees, matching the rules in [`docs/TREE.md`](TREE.md) and [`AGENTS.md`](../AGENTS.md). Test-tree placement is mandatory per [Decision 5](#decision-5--package-internal-tests-use-a-fixture-router-not-fakeshop_sharded) and [Decision 6](#decision-6--live-coverage-under-fakeshop_sharded1).

### `tests/optimizer/test_multi_db.py` (new)

Package tests; system-under-test is the cooperation surface at [`django_strawberry_framework/types/resolvers.py`](../django_strawberry_framework/types/resolvers.py) and the optimizer's queryset-`_db` preservation behavior. **Six** tests; single pytest item per test, no `pytest.mark.parametrize` fan-out so the count matches pytest collection output unambiguously. Selectors and mock targets pinned in [Decision 5](#decision-5--package-internal-tests-use-a-fixture-router-not-fakeshop_sharded).

**Mock contract** (pinned for every router-using test): tests `monkeypatch.setattr(django_strawberry_framework.types.resolvers.router, "db_for_read", Mock(return_value="default"))` (or `monkeypatch.setattr(django_strawberry_framework.types.resolvers, "router", Mock(...))` if the test inspects more than `db_for_read`). The mock's `db_for_read.return_value = "default"` so the call's outcome doesn't affect the assertion (the assertion is on the call shape, not the outcome).

- `test_fk_id_elision_stub_sets_state_db_via_router_db_for_read` — exercises `_build_fk_id_stub` against a fixture row with a non-null FK; asserts the returned stub has `_state.db == <mock return value>` and that `router.db_for_read` was called once. Pins cooperation axis 1 from [Decision 3](#decision-3--the-cooperation-contract-four-axes).
- `test_fk_id_elision_router_call_passes_parent_row_as_instance` — exercises `_build_fk_id_stub` against a fixture row that has a `_state` attribute; asserts `router.db_for_read` was called with `instance=<parent_row>` (not `instance=None`). Pins the instance-propagation contract — a regression where the call switches to `instance=None` would silently break consumer routers that consult the parent row's `_state.db` to decide the child's connection.
- `test_fk_id_elision_passes_none_instance_when_parent_lacks_state` — exercises `_build_fk_id_stub` against a synthetic parent row built with `types.SimpleNamespace(pk=1)` (no `_state` attribute); asserts the stub is built and `router.db_for_read` was called with `instance=None`. Pins the `hasattr(root, "_state")` fallback at [`types/resolvers.py:81`](../django_strawberry_framework/types/resolvers.py).
- `test_optimizer_plan_preserves_queryset_using_alias` — constructs a fixture `DjangoType` with one FK relation, runs a GraphQL selection through `walker.plan_optimizations` against a queryset constructed via `Model.objects.using("shard_b").all()`, asserts the post-plan queryset's `_db == "shard_b"`. Pins cooperation axis 2 (queryset `_db` propagation through the optimizer). Mocks `router.db_for_read` is NOT necessary for this test (no FK-id elision exercised); the queryset's `_db` is the assertion target.
- `test_strictness_mode_lazy_load_fires_under_using` — constructs a fixture row with `_state.db = "shard_b"`, exercises `_check_n1` against an unplanned relation, with `info.context` carrying `DST_OPTIMIZER_STRICTNESS = "raise"`; asserts `OptimizerError("Unplanned N+1: <field>")` is raised. Pins cooperation axis 4 — the strictness check fires regardless of the queryset's connection (the strictness check is connection-agnostic; the assertion is that the N+1 detection works under `.using()` exactly as it does under default routing, with the same error class and message).
- `test_get_queryset_downgrade_preserves_using_alias_on_prefetch` — constructs a fixture parent type with a relation to a child type that defines a custom `get_queryset` body returning `queryset.filter(is_private=False)`; runs the optimizer's plan application against a `Model.objects.using("shard_b").all()` parent queryset; asserts the generated `Prefetch` for the downgraded relation has `queryset._db == "shard_b"`. Pins cooperation axis 3 — `Prefetch` chains respect the consumer's queryset routing.

### `examples/fakeshop/test_query/test_multi_db.py` (new)

Live tests; system-under-test is the fakeshop project running under `FAKESHOP_SHARDED=1`. **Two** tests; single pytest item per test. Module is skipped at collection time when `FAKESHOP_SHARDED != "1"` per [Decision 6](#decision-6--live-coverage-under-fakeshop_sharded1).

- `test_using_shard_b_resolver_returns_rows_seeded_on_shard_b` — seeds two `Book` rows on `shard_b` via `models.Book.objects.using("shard_b").create(...)` (using minimal fixtures, no relations needed for this test); uses a per-test schema fixture that adds a `books_on_shard_b: list[BookType]` root resolver returning `models.Book.objects.using("shard_b").all()`; sends a `query { booksOnShardB { title } }` GraphQL request through `django.test.Client.post("/graphql/", ...)`; asserts the response contains both seeded titles. Pins the end-to-end cooperation under a real router scope.
- `test_cross_shard_isolation_default_rows_not_visible_via_shard_b_resolver` — seeds one `Book` row on the default alias (no `.using(...)`) and one on `shard_b` via `.using("shard_b")`; queries the same `booksOnShardB` resolver from the previous test; asserts only the `shard_b` row appears in the response. Pins the negative shape — the cooperation respects the consumer's queryset routing rather than aggregating across shards.

The per-test schema fixture lives inline in the test module (a `@strawberry.type` Query class declared at module level after the skip guard, used to construct a per-test `Schema(...)` and routed through a per-test URL configuration). The fixture intentionally does NOT modify `apps/library/schema.py` per [Decision 4](#decision-4--no-routing-decoration-on-fakeshop-schemas). Specifically, the test module:

1. Declares a `class _MultiDbTestQuery: ...` with the routing-specific root resolvers.
2. Constructs a `_test_schema = strawberry.Schema(query=_MultiDbTestQuery, extensions=[DjangoOptimizerExtension()])` once at module level (after the skip guard).
3. Uses Django's `RequestFactory` or `Client` with a temporary URL pattern routing `/graphql/` to a Strawberry view bound to `_test_schema`, OR (preferred) constructs the GraphQL response in-process via `_test_schema.execute_sync(...)` and asserts on the result — both shapes are acceptable; the spec author / implementer picks whichever reads cleaner against the existing fakeshop fixture conventions.

### Existing tests — no edits

`tests/optimizer/test_extension.py`, `tests/optimizer/test_walker.py`, `tests/types/test_resolvers.py`, and the rest of the existing test suite are NOT modified by this card. The new module sits alongside them with a focused scope; no regression-test surface is shifted.

`examples/fakeshop/test_query/test_library_api.py` is NOT modified; the autouse fixture is copied into the new file per [Decision 7](#decision-7--reuse-the-test_library_api-reload-fixture-verbatim) rather than refactored out.

## Doc updates

- [`docs/GLOSSARY.md`](GLOSSARY.md)
  - Update the Index table row for [`Multi-database cooperation`](GLOSSARY.md#multi-database-cooperation) at line 88 from `planned for `0.0.7`` to `shipped (`0.0.7`)`.
  - Update the entry body at line 679-687: replace the opening "Pins the existing `router.db_for_read` cooperation in `types/resolvers.py` with a spec, tests, and a `GLOSSARY.md` status entry." with past-tense "Documented cooperation surface — what the package guarantees under Django's multi-database machinery. Four axes:". List the four axes from [Decision 3](#decision-3--the-cooperation-contract-four-axes) as a bulleted enumeration. The body's `Companion BACKLOG.md item 41` and `See also:` lines stay unchanged.

- [`docs/README.md`](README.md)
  - Add a one-line forward-pointer at the end of the `### Sharded mode (multi-DB)` section (after line 216, before `## Using the package in your own project`) reading: "For the cooperation contract these shards run against — what the package guarantees under `.using()`, `Prefetch` chains, and `get_queryset` downgrades — see [`GLOSSARY.md#multi-database-cooperation`](GLOSSARY.md#multi-database-cooperation)."

- [`KANBAN.md`](../KANBAN.md)
  - Move `WIP-ALPHA-019-0.0.7` to the Done column with the next available `DONE-NNN-0.0.7` id (the column-move pass renumbers as usual; the next available id is determined at merge time, not pinned in this spec). The past-tense Done body summarizes the shipped scope: "Pinned the package's multi-database cooperation contract — `router.db_for_read` on FK-id elision stubs, queryset `_db` propagation through the optimizer, `Prefetch` chains under `.using()`, `get_queryset` downgrade routing, and strictness mode under `.using()`. Tests in [`tests/optimizer/test_multi_db.py`](tests/optimizer/test_multi_db.py) (package-internal, hermetic via mocked router) and [`examples/fakeshop/test_query/test_multi_db.py`](examples/fakeshop/test_query/test_multi_db.py) (live `/graphql/` HTTP, gated on `FAKESHOP_SHARDED=1`). [`docs/GLOSSARY.md#multi-database-cooperation`](docs/GLOSSARY.md#multi-database-cooperation) flipped from `planned for 0.0.7` to `shipped (0.0.7)` with a four-axis entry body; [`docs/README.md`](docs/README.md) `### Sharded mode (multi-DB)` carries a one-line forward-pointer. Spec: [`docs/SPECS/spec-019-multi_db-0_0_7.md`](docs/SPECS/spec-019-multi_db-0_0_7.md). Zero production code change; the cooperation already existed in [`django_strawberry_framework/types/resolvers.py:82`](django_strawberry_framework/types/resolvers.py). [`BACKLOG.md`](BACKLOG.md) item 41 owns first-class sharding-aware planning post-`1.0.0`."
  - Update the card body's `Definition of done` bullet 1 (`docs/spec-multi_db.md` → `docs/SPECS/spec-019-multi_db-0_0_7.md` after the Step 8 archive pass per [Decision 1](#decision-1--spec-filename-and-canonical-naming)) at column-move time.
  - Update the `### In progress` summary paragraph (if one is present) to remove `WIP-ALPHA-019-0.0.7` from the remaining-cards list once this card moves to Done.

- [`CHANGELOG.md`](../CHANGELOG.md)
  - **Append** to the existing `[0.0.7]` `### Added` subsection (do NOT create a second `[0.0.7]` heading — verified at [`CHANGELOG.md`](../CHANGELOG.md) lines 24-30, the `[0.0.7]` heading already carries `DONE-016`'s [`DjangoListField`](GLOSSARY.md#djangolistfield), `DONE-017`'s [`Django AppConfig`](GLOSSARY.md#django-appconfig), and `DONE-018`'s [`Schema export management command`](GLOSSARY.md#schema-export-management-command) entries; every `0.0.7` card under the joint cut appends to the same shared section per [Decision 9](#decision-9--joint-0_0_7-cut)):

    > "`Multi-database cooperation` — pinned the package's cooperation contract under Django's multi-database machinery: `router.db_for_read` on FK-id elision stubs (with the parent row passed as the `instance=` hint when present), queryset `_db` propagation through the optimizer's `select_related` / `prefetch_related` / `only` plan, `Prefetch(queryset=...)` routing inheritance from `get_queryset` downgrades, and strictness-mode N+1 detection on the queryset's connection. Tests in [`tests/optimizer/test_multi_db.py`](tests/optimizer/test_multi_db.py) (hermetic, router mocked) and [`examples/fakeshop/test_query/test_multi_db.py`](examples/fakeshop/test_query/test_multi_db.py) (live `/graphql/` HTTP under `FAKESHOP_SHARDED=1`). [`docs/GLOSSARY.md#multi-database-cooperation`](docs/GLOSSARY.md#multi-database-cooperation) flipped from `planned for 0.0.7` to `shipped (0.0.7)`. No production code change — the cooperation already existed at [`django_strawberry_framework/types/resolvers.py:82`](django_strawberry_framework/types/resolvers.py). [`BACKLOG.md`](BACKLOG.md) item 41 owns first-class sharding-aware planning post-`1.0.0`."

  - The version bump entry is owned by **the last `0.0.7` card to ship** per [Decision 9](#decision-9--joint-0_0_7-cut), NOT this slice.
  - [`AGENTS.md`](../AGENTS.md) line 21 ("Do not update CHANGELOG.md unless explicitly instructed") — this Slice 3 bullet is the explicit instruction.

- No edits to [`README.md`](../README.md), [`GOAL.md`](../GOAL.md), or [`TODAY.md`](../TODAY.md) per [Decision 8](#decision-8--no-readme--goal--today-edits).

- No edits to [`docs/TREE.md`](TREE.md). Justification: this card adds one test file under the existing `tests/optimizer/` subdirectory (already pinned in `TREE.md`'s current-on-disk-layout at line 357-365 of `docs/TREE.md`) and one test file under `examples/fakeshop/test_query/` (already pinned at line 380-382 of `docs/TREE.md`). No new subdirectory; no new source module. The current-on-disk-layout enumeration in `docs/TREE.md` describes the subdirectories and the per-file-mirror rule rather than listing every test file, so no edit is required.

## Risks and open questions

Each item names a preferred answer for `0.0.7` and a fallback if implementation reveals the preferred answer is wrong.

- **`[0.0.7]` already cut in `CHANGELOG.md` versus `WIP-ALPHA-019-0.0.7`'s target patch.** Verified at [`CHANGELOG.md`](../CHANGELOG.md) line 24: `## [0.0.7] - 2026-05-20`. The CHANGELOG advertises `0.0.7` as released on 2026-05-20, but [`pyproject.toml:4`](../pyproject.toml) and [`django_strawberry_framework/__init__.py:26`](../django_strawberry_framework/__init__.py) and [`tests/base/test_init.py:11`](../tests/base/test_init.py) all still pin `0.0.6` — meaning the joint cut has accumulated CHANGELOG entries against an unbumped version. Preferred answer: the `[0.0.7] - 2026-05-20` heading and date are placeholders set by the first-shipped card under the joint cut (`DONE-016-0.0.7`), to be confirmed / updated by whichever card actually performs the version bump per [Decision 9](#decision-9--joint-0_0_7-cut). This card honors the joint-cut policy verbatim, appends the fourth `### Added` bullet, and does NOT bump the version. The maintainer reconciles the date at release time. Fallback: if the maintainer decides `0.0.7` is in fact released and this card should target `0.0.8`, the slice-3 doc updates re-point at a new `[0.0.8]` `### Added` heading (single-line edit) and the spec filename moves to `docs/spec-019-multi_db-0_0_8.md`; production-code surface is unaffected because this card has none.
- **KANBAN card body names `docs/spec-multi_db.md`; spec ships as `docs/spec-019-multi_db-0_0_7.md`.** Per [Decision 1](#decision-1--spec-filename-and-canonical-naming), the canonical name is the structured one. Preferred answer: Slice 3 rewrites the card body's `Definition of done` bullet 1 to point at the structured name; the Step-8 archive pass at the end of the NEXT.md flow propagates the rename to any other cross-references. Fallback: if a future agent confused by the rename creates a second `docs/spec-multi_db.md`, the structured filename's content takes precedence; the stray file is deleted in a follow-up cleanup card.
- **`pytest.skip(allow_module_level=True)` precludes per-test marker control.** Slice 2's tests all share one collection-time skip; there is no way to opt one test in and another out. Preferred answer: this is fine — both Slice 2 tests target `FAKESHOP_SHARDED=1`, and if a future test needs to run under single-DB mode it lives in a different file. Fallback: if a future card needs mixed gating, it splits the module into two files (one for the gated tests, one for the un-gated).
- **Mocking `router` at the resolver-module level versus globally.** Preferred answer: patch `django_strawberry_framework.types.resolvers.router.db_for_read` (module-local) per [Decision 5](#decision-5--package-internal-tests-use-a-fixture-router-not-fakeshop_sharded). Fallback: if Django's router internals change such that the `from django.db import router` import at [`types/resolvers.py:27`](../django_strawberry_framework/types/resolvers.py) becomes stale, the patch target shifts to wherever `router` is bound at module-import time; the test breakage is informative and a one-line fix.
- **`Prefetch(queryset=...)` `_db` carryover under Django version changes.** Preferred answer: Django's queryset API preserves `_db` through `Prefetch` chains as a documented contract since Django 1.7 (when prefetch was added). The test in Slice 1 (f) pins our cooperation with that contract. Fallback: if Django changes the `_db` propagation rule (extremely unlikely; would break every Django app using `Prefetch(queryset=...)`), the test fails loudly and the package needs to adapt — but that's a Django regression, not a package one.
- **`router.db_for_read` documented signature.** Preferred answer: `(model, **hints) -> str | None` per [Django's docs](https://docs.djangoproject.com/en/stable/topics/db/multi-db/#using-routers); `instance` is the documented hint name. The package's call uses `db_for_read(field_meta.related_model, instance=instance)`, which matches the documented call shape. Fallback: if a consumer's custom router does not accept `instance=` (e.g., a router defined as `def db_for_read(self, model, **hints):` that ignores `hints`), the package's call still works — the kwarg is silently dropped on the receiving side. The cooperation contract is "we forward `instance=` when we have it"; the router's reception is consumer-shaped.
- **Strictness mode and `_state.db` propagation.** Preferred answer: Django's descriptor protocol propagates `_state.db` to related instances accessed through the descriptor; a lazy-load via `book.shelf` from a `using("shard_b")` book row reads from `shard_b` automatically. The strictness check fires regardless of connection; the connection is a Django concern, not a strictness one. Fallback: if Django changes the descriptor protocol to drop `_state.db` propagation (extremely unlikely), the test in Slice 1 (e) catches it and we adapt.
- **Cross-shard joins and the optimizer's silence.** Preferred answer: a consumer who writes a cross-shard join gets Django's `OperationalError` at queryset evaluation; the package does not catch or document this failure mode because [`BACKLOG.md`](../BACKLOG.md) item 41 owns the first-class sharding-aware-planning future. Fallback: if real consumer demand surfaces for "the optimizer should detect cross-shard joins and raise a friendlier `ConfigurationError`," a follow-up card adds that detection and the BACKLOG item 41 framing is unchanged.

## Out of scope (explicitly tracked elsewhere)

- First-class sharding-aware planning: cross-shard joins, automatic shard selection based on FK, multi-shard aggregates, [`Meta.preferred_database`](GLOSSARY.md). Tracked in [`BACKLOG.md`](../BACKLOG.md) item 41 (post-`1.0.0` differentiation) per the [`KANBAN.md`](../KANBAN.md) card's Out of scope bullet.
- A package-level `DATABASE_ROUTERS` opinion or reference router class. Routing policy is consumer-shaped.
- A `Meta.preferred_database` declarative shortcut. Out of scope; [`BACKLOG.md`](../BACKLOG.md) item 41.
- Cross-shard join detection. Out of scope; [`BACKLOG.md`](../BACKLOG.md) item 41.
- Multi-shard aggregates. Out of scope; [`BACKLOG.md`](../BACKLOG.md) item 41 and the future [`AggregateSet`](GLOSSARY.md#aggregateset) (planned for `0.1.3`) — neither aggregates across connections in the contract this card pins.
- [Connection-aware optimizer planning](GLOSSARY.md#connection-aware-optimizer-planning): planned for `0.0.9`. This is `edges { node { ... } }` selection planning, NOT database-connection planning — separate concern despite the overlapping word "connection."
- Warning-free scalar registration via `StrawberryConfig.scalar_map`: `WIP-ALPHA-020-0.0.7` in [`KANBAN.md`](../KANBAN.md). Independent card; the two `0.0.7` WIP cards do not overlap.

## Definition of done

The card is complete when all of the following are true:

1. [`docs/spec-019-multi_db-0_0_7.md`](spec-019-multi_db-0_0_7.md) (this document) is at the canonical structured filename per [Decision 1](#decision-1--spec-filename-and-canonical-naming), with companion [`docs/spec-019-multi_db-0_0_7-terms.csv`](spec-019-multi_db-0_0_7-terms.csv) anchoring every project-specific term used in the spec body to the matching [`docs/GLOSSARY.md`](GLOSSARY.md) heading (per [`docs/SPECS/NEXT.md`](SPECS/NEXT.md) Step 7).
2. `tests/optimizer/test_multi_db.py` exists and contains the **6 tests** listed in the [Test plan](#test-plan): (a) FK-id elision stub `_state.db` via `router.db_for_read`, (b) `instance=<parent_row>` on the router call, (c) `instance=None` when parent lacks `_state`, (d) optimizer plan preserves queryset `_db`, (e) strictness mode under `.using()`, (f) `get_queryset` downgrade preserves `.using()`. Every test uses pytest's `monkeypatch` for any router mock so teardown is automatic; no `pytest.mark.parametrize` fan-out (single pytest item per test).
3. `examples/fakeshop/test_query/test_multi_db.py` exists with the module-level `pytest.skip(allow_module_level=True)` guard from [Decision 6](#decision-6--live-coverage-under-fakeshop_sharded1) and contains the **2 tests** listed in the [Test plan](#test-plan): (a) live `.using("shard_b")` round trip, (b) shard isolation under `.using()`. The autouse reload fixture is copied verbatim from `examples/fakeshop/test_query/test_library_api.py:17-43` per [Decision 7](#decision-7--reuse-the-test_library_api-reload-fixture-verbatim).
4. `examples/fakeshop/apps/library/schema.py` and `examples/fakeshop/apps/products/schema.py` are NOT modified per [Decision 4](#decision-4--no-routing-decoration-on-fakeshop-schemas). The per-test schema fixture lives inline in `examples/fakeshop/test_query/test_multi_db.py`.
5. `examples/fakeshop/config/settings.py` is NOT modified (the existing `FAKESHOP_SHARDED=1` branch suffices).
6. `django_strawberry_framework/` is NOT modified per [Decision 2](#decision-2--no-production-code-change) (no production code change).
7. `django_strawberry_framework/__init__.py` is NOT modified. `__all__` is unchanged.
8. `tests/base/test_init.py`'s `__all__` assertion is unchanged. Version assertion is unchanged.
9. Package coverage stays at 100% (`pyproject.toml [tool.coverage.report] fail_under = 100`) — **verified by CI's `fail_under = 100` gate, not by the worker locally** (mirroring [`docs/SPECS/spec-018-export_schema-0_0_7.md`](SPECS/spec-018-export_schema-0_0_7.md) rev4 L4 clarifying clause). The worker's local verification is item 13's `uv run pytest --no-cov` suite-passing check; coverage assertion is CI's job after the PR opens. If CI reports a coverage regression on the PR, the worker adds the missing test before merge.
10. [`docs/GLOSSARY.md`](GLOSSARY.md) [`Multi-database cooperation`](GLOSSARY.md#multi-database-cooperation) entry is flipped from `planned for 0.0.7` to `shipped (0.0.7)` (Index table row at line 88; entry body at line 679). Entry body lists the four cooperation axes from [Decision 3](#decision-3--the-cooperation-contract-four-axes).
11. [`docs/README.md`](README.md) `### Sharded mode (multi-DB)` section carries a one-line forward-pointer to [`GLOSSARY.md#multi-database-cooperation`](GLOSSARY.md#multi-database-cooperation).
12. [`README.md`](../README.md), [`GOAL.md`](../GOAL.md), [`TODAY.md`](../TODAY.md), and [`docs/TREE.md`](TREE.md) are NOT edited per [Decision 8](#decision-8--no-readme--goal--today-edits) and the `docs/TREE.md` justification in the [Doc updates](#doc-updates) section.
13. [`KANBAN.md`](../KANBAN.md) moves `WIP-ALPHA-019-0.0.7` to Done with the next `DONE-NNN-0.0.7` id and a past-tense body summarizing the shipped scope; the `Definition of done` bullet 1 in the card body is rewritten to point at the structured spec filename per [Decision 1](#decision-1--spec-filename-and-canonical-naming).
14. [`CHANGELOG.md`](../CHANGELOG.md) `[0.0.7]` `### Added` subsection carries the new bullet pinned in [Doc updates](#doc-updates); no second `[0.0.7]` heading is created.
15. The version bump is NOT in this card per [Decision 9](#decision-9--joint-0_0_7-cut); the last `0.0.7` card to ship owns `pyproject.toml`, `__version__`, and `tests/base/test_init.py`'s version assertion.
16. Zero new public exports — `__all__` is unchanged.
17. `uv run ruff format .` passes; `uv run ruff check --fix .` passes; `uv run pytest --no-cov` passes (explicit `--no-cov` opts out of `pytest.ini`'s auto-applied `--cov`; coverage enforcement is CI's job per `pyproject.toml [tool.coverage.report] fail_under = 100`, not this slice's; workers verify the suite passes, not that coverage stays at 100%).
