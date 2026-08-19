# Spec: Multi-database cooperation contract

Target release: `0.0.7` (per the [`KANBAN.md`][kanban] card `DONE-023-0.0.7`).
Status: shipped (`0.0.7`); implementation complete and committed. The spec is retained at this path as the durable record of the cooperation contract. Its deliberative layer — the revision history, every Decision's justification and rejected alternatives, and every claim it may no longer make — lives in [`spec-023-multi_db-0_0_7-rationale.md`][spec-023-rationale].
Owner: package maintainer.
Predecessors: [`docs/GLOSSARY.md`][glossary] (entries [`Multi-database cooperation`][glossary-multi-database-cooperation], [`DjangoOptimizerExtension`][glossary-djangooptimizerextension], [`get_queryset` visibility hook][glossary-get-queryset-visibility-hook], [`Strictness mode`][glossary-strictness-mode], [Queryset diffing][glossary-queryset-diffing], [FK-id elision][glossary-fk-id-elision]); [`KANBAN.md`][kanban] card `DONE-023-0.0.7`; joint-cut policy spec [`docs/SPECS/spec-020-list_field-0_0_7.md`][spec-020] ([Decision 10][spec-020-decision-10--joint-007-cut], reused verbatim in [Decision 9](#decision-9--joint-007-cut) here); shipped sibling [`docs/SPECS/spec-022-export_schema-0_0_7.md`][spec-022] (the bundle this card sits inside).

## Key glossary references

Skim these [`docs/GLOSSARY.md`][glossary] entries first — they anchor the vocabulary used throughout the spec:

- [`Multi-database cooperation`][glossary-multi-database-cooperation] — the entry this card flips from `planned for 0.0.7` to `shipped (0.0.7)` in [Slice 3](#implementation-plan). The entry body already describes the cooperation contract this spec pins down.
- [`DjangoOptimizerExtension`][glossary-djangooptimizerextension] — the optimizer that this card proves cooperates with Django's routing. The extension does not query the router itself; cooperation rides on the queryset's `_db` attribute being preserved through plan application, `Prefetch` chains, and FK-id elision stubs.
- [`get_queryset` visibility hook][glossary-get-queryset-visibility-hook] — the consumer-owned visibility filter that survives relation traversal via the optimizer's `Prefetch` downgrade. The downgrade uses whatever queryset the hook returned — if the hook explicitly returns a `.using(alias)` queryset, that alias survives the downgrade; the root queryset's alias is not threaded into a generated child queryset at plan-construction time — a generated child is routed alias-late, at fetch time.
- [Queryset diffing][glossary-queryset-diffing] — the optimizer's cooperation rule that respects work the consumer already applied to the queryset (including `.using(alias)`); cited so the [Decision 3](#decision-3--the-cooperation-contract-four-axes) cooperation contract is grounded in shipped behavior, not new code.
- [Strictness mode][glossary-strictness-mode] — `off` / `warn` / `raise` for unplanned N+1 detection; this card pins that strictness remains active for objects loaded from any database alias (the check is connection-agnostic; the error class and message are unchanged under `.using("shard_b")`), and that Django — not the package — owns which alias a lazy load (if permitted) would actually use. [`Decision 3`](#decision-3--the-cooperation-contract-four-axes) axis 4 (verified against [`types/resolvers.py::_check_n1`][resolvers]).
- [FK-id elision][glossary-fk-id-elision] — the optimizer's `{ relation { id } }` shortcut that reads the FK column off the parent row and synthesizes a stub. This card pins that the stub's `_state.db` is set via `router.db_for_read(...)` so subsequent attribute access (e.g. follow-up resolver hops) reads from the correct connection.
- [`DjangoType`][glossary-djangotype] — the consumer-facing type the optimizer plans for; not directly modified by this card but the framing for every test fixture.
- [`finalize_django_types`][glossary-finalize-django-types] — the consumer-owned synchronization point; tests that exercise multi-db cooperation finalize once per fixture exactly like the existing optimizer tests.
- [`ConfigurationError`][glossary-configurationerror] — not raised by anything in this card.

Project conventions to follow:

- [`AGENTS.md`][agents] — #"Test placement:" (test placement; package tests live under `tests/` with `__init__.py` shells in subdirectories like `tests/optimizer/`, example-project non-HTTP tests under `examples/fakeshop/tests/`, live HTTP tests under `examples/fakeshop/test_query/` and no `__init__.py` in either fakeshop test tree); #"Test through real usage, prefer the example project" ("any line reachable via a real GraphQL query against fakeshop MUST be covered in `examples/fakeshop/test_query/`"); #"No pytest after edits" ("No pytest after edits; run only when explicitly asked"); #"Add a settings key only when the feature that needs it lands" ("Add a settings key only when the feature that needs it lands; never preemptively"). **Note:** #"No CHANGELOG.md updates unless told" prohibits [`CHANGELOG.md`][changelog] edits without explicit permission; [Slice 3](#implementation-plan) grants that permission for this card's `[0.0.7]` `### Added` append.
- [`CONTRIBUTING.md`][contributing] — 100% coverage target.
- [`KANBAN.md`][kanban] — card-ID format; column movement at Slice 3; the card body's `docs/spec-multi_db.md` reference predates the structured `spec-<NNN>-<topic>-<0_0_X>.md` convention and gets rewritten in the same sweep per [Decision 1](#decision-1--spec-filename-and-canonical-naming).
- [`docs/TREE.md`][tree] — tests mirror source one-to-one; `tests/optimizer/` already carries `__init__.py` and shipped optimizer-test modules, so adding `tests/optimizer/test_multi_db.py` is a one-file extension, not a new subdirectory.

## Slice checklist

Each top-level item maps to one commit in the [Implementation plan](#implementation-plan). Three slices total.

- [ ] Slice 1: Package-internal tests (split across two files per [Decision 5](#decision-5--package-internal-tests-use-a-fixture-router-not-fakeshop_sharded) — `tests/types/test_resolvers.py` extends the existing file for resolver-level FK-id-elision + strictness unit tests; `tests/optimizer/test_multi_db.py` is new and holds the consumer-`OptimizerHint.prefetch(Prefetch(queryset=...using...))` round-trip test at the optimizer-plan layer. Decision 3 axis 2 — `OptimizationPlan.apply` `_db` preservation — is verified transitively by Slice 2's live HTTP test per `AGENTS.md` #"Test through real usage, prefer the example project" and is NOT covered by a separate package-internal assertion.)
  - [ ] Extend `tests/types/test_resolvers.py` with **five** new resolver-level tests (per [Test plan](#test-plan) — FK-id elision router call shape; router call passes `instance=parent_row`; router call passes `instance=None` when parent lacks `_state`; null FK takes the early-return branch and does NOT call the router; strictness check is connection-agnostic for non-default `_state.db`). Null-FK and parent-lacks-`_state` are separate tests; the strictness test lives here rather than in `tests/optimizer/test_multi_db.py` because `_check_n1` lives in `types/resolvers.py` and a direct unit test belongs in the source-mirror partner. Single pytest item per test, no `pytest.mark.parametrize` fan-out so the count matches pytest collection output unambiguously.
  - [ ] New `tests/optimizer/test_multi_db.py` containing **one** optimizer-plan-level test (per [Test plan](#test-plan) — consumer-provided `OptimizerHint.prefetch(Prefetch(queryset=…using…))` round-trips through plan construction with `_db` intact). Single pytest item; same no-`parametrize` rule. Decision 3 axis 2 (`OptimizationPlan.apply(qs)` preserves `qs._db` for an explicit `.using()` parent) is verified transitively by the Slice 2 live `/graphql/` HTTP test, NOT by a separate package-internal test — per [`AGENTS.md`][agents] #"Test through real usage, prefer the example project"'s "coverage achievable via a real GraphQL query against fakeshop MUST be earned that way" rule. Total Slice 1 pytest items: six (five resolver-level + one optimizer-plan-level).
  - [ ] Mock `router.db_for_read` only in the four FK-id-elision tests (the ones that actually call the router). The strictness test (test (e) in `tests/types/test_resolvers.py`) and the optimizer-plan test (test (f) in `tests/optimizer/test_multi_db.py`) do not exercise FK-id elision and do not need a router mock. When a mock is needed, the pattern is `monkeypatch.setattr(django_strawberry_framework.types.resolvers.router, "db_for_read", Mock(return_value="default"))` per [Decision 5](#decision-5--package-internal-tests-use-a-fixture-router-not-fakeshop_sharded). NO second SQLite file is created at package-test time; cooperation is verified by spying on the router call shape, not by exercising two real connections.
  - [ ] Add module and test docstrings to match existing style in `tests/optimizer/` and `tests/types/` (convention-matching only; verified at [`pyproject.toml #"[tool.ruff.lint.per-file-ignores]"`](../../pyproject.toml) that `per-file-ignores` includes `tests/**/*.py = ["D", "ANN", ...]`, so docstrings and annotations in tests are NOT gate-forced).
  - [ ] No `# noqa` suppressions for any docstring or annotation rule; they are unnecessary under the current per-file ignores.
- [ ] Slice 2: Fakeshop live coverage under `FAKESHOP_SHARDED=1`
  - [ ] New `examples/fakeshop/test_query/test_multi_db.py`; this contract contributes **two** live `/graphql/` HTTP tests to it against the sharded fakeshop layout (per [Test plan](#test-plan)). It is the tree's home for live multi-database coverage, so later cards add their own alias-pinning suites alongside these two; the module is positioned next to `test_library_api.py` so that file's reload pattern is reusable.
  - [ ] Tests gate on `FAKESHOP_SHARDED=1` by calling `pytest.skip("requires FAKESHOP_SHARDED=1", allow_module_level=True)` at module top **after** an `os.environ.get("FAKESHOP_SHARDED") != "1"` check (per [Decision 6](#decision-6--live-coverage-under-fakeshop_sharded1)). `pytest.mark.skipif(...)` would not work for the same load-time reason `config.settings`'s `DATABASES` is decided at module import time — the import below `if os.environ.get("FAKESHOP_SHARDED") == "1":` settles before `pytest.mark.skipif` would get to evaluate, so a `mark.skipif` test would still try to import models against a single-DB `DATABASES` dict.
  - [ ] Each test is decorated with `@pytest.mark.django_db(databases=["default", "shard_b"])` (per `pytest-django`'s multi-db access rule; without this marker any `Model.objects.using("shard_b").create(...)` call raises `DatabaseError` even when `FAKESHOP_SHARDED=1` has registered the alias).
  - [ ] Each test seeds a full `Branch → Shelf → Book` chain on `shard_b` (verified at [`examples/fakeshop/apps/library/models.py::Shelf`][models] and [`examples/fakeshop/apps/library/models.py::Book`][models] that `Book.shelf` and `Shelf.branch` are both non-null FKs, so `Book.objects.using(alias).create(...)` cannot complete without an upstream `Branch` and `Shelf` on the same alias). Seeding pattern per alias: `branch = Branch.objects.using(alias).create(...)`, `shelf = Shelf.objects.using(alias).create(branch=branch, ...)`, `book = Book.objects.using(alias).create(shelf=shelf, ...)`.
  - [ ] Live `/graphql/` HTTP exclusively per [Decision 6](#decision-6--live-coverage-under-fakeshop_sharded1) — no in-process `_test_schema.execute_sync(...)` alternative. Pattern: each test (a) constructs a per-test `strawberry.Schema(...)` whose root resolver returns `models.Book.objects.using("shard_b").select_related("shelf__branch")`, (b) wraps execution in `override_settings(ROOT_URLCONF=<module-level urlconf>)` with `clear_url_caches()` in test-module setup, (c) sends a `query { ... }` request via `django.test.Client.post("/graphql/", ...)`, (d) asserts on the JSON response. The schema is NOT modified to inject routing per [Decision 4](#decision-4--no-routing-decoration-on-fakeshop-schemas); routing is consumer-shaped, and the test exercises consumer-shaped routing via fixture data plus a per-test root resolver.
  - [ ] Tests take the `_reload_project_schema_for_acceptance_tests` reload contract from the shared `examples/fakeshop/test_query/conftest.py` autouse fixture (per [Decision 7](#decision-7--the-reload-fixture-comes-from-the-shared-test_query-conftest)); the module declares no reload fixture of its own.
  - [ ] Module + per-test docstrings to match existing fakeshop test-tree style (convention-matching only — `examples/**/*.py` is in `per-file-ignores` for `D` / `ANN` per [`pyproject.toml #"[tool.ruff.lint.per-file-ignores]"`](../../pyproject.toml), parallel to the Slice 1 wording above).
- [ ] Slice 3: Promotion + docs
  - [ ] Flip [`Multi-database cooperation`][glossary-multi-database-cooperation] from `planned for 0.0.7` to `shipped (0.0.7)` in [`docs/GLOSSARY.md`][glossary]: update the Index table row at `docs/GLOSSARY.md #"| [Multi-database cooperation](#multi-database-cooperation) |"` so its status cell reads `shipped (`0.0.7`)` and the entry body at `docs/GLOSSARY.md #"## Multi-database cooperation"` (the body already describes the cooperation in present tense — minor wording tightening to remove "Pins the existing … cooperation" framing and replace it with "Pins the cooperation contract: …" past-tense framing matching shipped entries).
  - [ ] Update [`docs/README.md`][readme]: rewrite the `### Sharded mode (multi-DB)` section to describe the additive `DATABASES` layout (`default → db.sqlite3` in both modes; `FAKESHOP_SHARDED=1` ADDS `shard_b → db_shard_b.sqlite3`) and note that the committed `examples/fakeshop/db_shard_b.sqlite3` fixture ships with `seed_shards(count=1)` already applied so the sharded mode works out of the box. The section already links to the GLOSSARY entry for the cooperation contract.
  - [ ] Update [`KANBAN.md`][kanban]: the card sits in the Done column as `DONE-023-0.0.7` with `Status: Done`, and its `Spec:` row resolves to [`docs/SPECS/spec-023-multi_db-0_0_7.md`][spec-023] (canonical name; supersedes the card's `docs/spec-multi_db.md` placeholder per [Decision 1](#decision-1--spec-filename-and-canonical-naming)). The board renders each card from the kanban DB into a fixed structure — metadata rows, a glossary-terms table, upstream-verification bullets, and a `#### Note` — so the card's summary of the shipped scope is that `Note` bullet rather than free-form prose (wording in [Doc updates](#doc-updates)).
  - [ ] Update [`CHANGELOG.md`][changelog]: **append** to the existing `[0.0.7]` `### Added` subsection (do NOT create a second `[0.0.7]` heading per [Decision 9](#decision-9--joint-007-cut) — every `0.0.7` card under the joint cut appends to the same shared section). [`AGENTS.md`][agents] #"No CHANGELOG.md updates unless told" ("No CHANGELOG.md updates unless told") — this Slice 3 bullet is the explicit instruction. Entry wording pinned in [Doc updates](#doc-updates).
  - [ ] No edits to [`README.md`][root-readme], [`GOAL.md`][goal], or [`TODAY.md`][today]. Justification: the cooperation contract is plumbing the package already honors; it is not a new consumer name-surface, the fakeshop schema is unchanged by this card, and `TODAY.md`'s query-shape snapshot is not affected (per [Decision 8](#decision-8--no-readme--goal--today-edits)). Same posture as [`docs/SPECS/spec-022-export_schema-0_0_7.md`][spec-022] Slice 3.
  - [ ] Version bump (deferred to **the last `0.0.7` card to ship**, NOT this card; per [Decision 9](#decision-9--joint-007-cut)): see [`docs/SPECS/spec-020-list_field-0_0_7.md`][spec-020] Decision 10. This card does NOT bump `pyproject.toml`, `django_strawberry_framework/__init__.py`'s `__version__`, or `tests/base/test_init.py`'s pinned version assertion.
  - [ ] Zero new public exports — the cooperation contract is plumbing already in the package, not a new symbol. `__all__` is unchanged.
  - [ ] Final gates (same posture as [`docs/SPECS/spec-022-export_schema-0_0_7.md`][spec-022] DoD item 13):
    - [ ] `uv run ruff format .` passes.
    - [ ] `uv run ruff check --fix .` passes.
    - [ ] `uv run pytest --no-cov` (or scoped subset) passes; the explicit `--no-cov` opts out of `pytest.ini`'s auto-applied `--cov` per the per-pass-gates contract; coverage enforcement is CI's job (`pyproject.toml [tool.coverage.report] fail_under = 100`), not this slice's.

## Problem statement

`django-strawberry-framework` already cooperates with Django's multi-database machinery in source: [`django_strawberry_framework/types/resolvers.py::_build_fk_id_stub`][resolvers] sets `state.db = router.db_for_read(field_meta.related_model, instance=instance)` on FK-id elision stubs, the optimizer's queryset diffing rule ([`Queryset diffing`][glossary-queryset-diffing]) preserves whatever explicit `.using(alias)` the consumer applied to the root queryset, and the optimizer's `Prefetch` downgrade for [`get_queryset`][glossary-get-queryset-visibility-hook] hooks uses whatever queryset the consumer's hook returned — so if the hook explicitly returns a `.using(alias)` queryset that alias survives the downgrade, while the root queryset's alias is not threaded into a generated child queryset at plan-construction time — a generated child is routed alias-late, at fetch time. The fakeshop example already ships a working additive two-alias layout: `examples/fakeshop/config/settings.py` keeps `default` → `db.sqlite3` in both single-DB and sharded modes, and `FAKESHOP_SHARDED=1` ADDS `shard_b` → `db_shard_b.sqlite3` on top of the single-DB layout, and [`examples/fakeshop/apps/products/management/commands/seed_shards.py`][seed-shards] materializes the secondary shard via `Model.objects.using("shard_b").create(...)` calls in [`examples/fakeshop/apps/products/services.py::seed_data`][services]. The committed `examples/fakeshop/db_shard_b.sqlite3` fixture ships with `seed_shards(count=1)` already applied so sharded mode works out of the box.

But none of this is specified, tested, or documented as a package contract. The consumer reading [`docs/README.md`][readme]'s `### Sharded mode (multi-DB)` section (`docs/README.md #"### Sharded mode (multi-DB)"`) sees the example project's shard wiring with no forward-pointer to a package commitment. The migrant from `graphene-django` or `strawberry-graphql-django` looking for "does this package work under `DATABASE_ROUTERS` / `.using()` / sharded reads?" has to read the source. The optimizer's behavior under `.using()` is implicit in [`Queryset diffing`][glossary-queryset-diffing] but never pinned with a test that would catch a regression (e.g., a future optimizer refactor that re-fetched the queryset via `Model.objects.all()` would silently lose the consumer's `.using("shard_b")` and the test suite would not notice).

Both reference packages take different stances:

- `strawberry-django` does not document multi-db behavior. Its `optimizer.py` (verified at `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/optimizer.py`) does not call `router.db_for_*` anywhere; cooperation rides entirely on the queryset's `_db` attribute. Adding a contract document moves us ahead of upstream on this axis.
- `graphene-django` does not document multi-db either; its filter / connection layer is database-agnostic by accident, not by design.

The shipping bar is deliberately low — this is a tests + docs card with **zero production code change**. The discipline the card needs to enforce is **what the contract covers and what it does NOT**: routing through Django's `router.db_for_*` API and queryset `_db` propagation are in scope; first-class sharding-aware planning (cross-shard joins, automatic shard selection based on FK, multi-shard aggregates, `Meta.preferred_database`) is explicitly deferred to [`BACKLOG.md`][backlog] item 41 (per the [`KANBAN.md`][kanban] card's Out of scope bullet).

## Current state

- [`django_strawberry_framework/types/resolvers.py::_build_fk_id_stub`][resolvers] sets `_state.db = router.db_for_read(field_meta.related_model, instance=instance)` inside `_build_fk_id_stub`. `instance=instance` is `root if hasattr(root, "_state") else None`, so consumer routers can consult the parent row as an `instance=` hint; the stub's `_state.db` is whatever the router returns from that call. This is the **read**-path router consultation the four axes cover, and the only one in the optimizer / type layer. The package's other router consultations belong to surfaces outside these axes: the permission layer collects candidate read aliases at [`utils/permissions.py #"aliases = {router.db_for_read(model)"`][permissions], and the write pipeline resolves the write alias at [`utils/write_transaction.py::resolve_write_alias`][write-transaction] and again with an instance hint at [`utils/write_transaction.py::check_instance_write_alias`][write-transaction].
- [`django_strawberry_framework/optimizer/extension.py`][extension] and [`walker.py`][walker] do NOT call `router.db_for_*` anywhere; cooperation rides entirely on the queryset's `_db` attribute being preserved through plan application. The [`Queryset diffing`][glossary-queryset-diffing] rule means: if the consumer's resolver returns `Item.objects.using("shard_b").select_related("category")`, the optimizer adds `prefetch_related("entries")` on top via `qs.prefetch_related(...)` (which preserves `_db`), and the consumer's `_db` survives.
- [`examples/fakeshop/config/settings.py`][settings] ships an additive `DATABASES` layout: a `default` entry is declared unconditionally, and `FAKESHOP_SHARDED=1` ADDS `shard_b → db_shard_b.sqlite3` on top of it. Both modes point `default` at the same SQLite file, so a single dev workflow (`manage.py seed_data`, etc.) populates the default alias regardless of mode; sharded mode only ADDS the secondary shard. Two env vars re-point `default` without disturbing that additivity: `DJANGO_STRAWBERRY_KANBAN_DB` swaps its SQLite file (used by the doc-render tooling against a migrated copy of the board DB), and `FAKESHOP_PG_DSN` swaps the whole `default` entry to Postgres for the vendor tier. The Postgres tier and `FAKESHOP_SHARDED` are mutually exclusive.
- [`examples/fakeshop/apps/products/services.py::seed_data`][services] uses `Model.objects.using(db_alias).create(...)` to seed shards; the `services.py` body proves the cooperation works at write time (rows land on the right shard when the alias is threaded through). The read-time cooperation through `/graphql/` is exercised by the live tests this card ships in `examples/fakeshop/test_query/test_multi_db.py`.
- [`examples/fakeshop/test_query/conftest.py::_reload_project_schema_for_acceptance_tests`][test-query-conftest] carries the tree-wide autouse reload fixture; every live `/graphql/` module depends on it (per [Decision 7](#decision-7--the-reload-fixture-comes-from-the-shared-test_query-conftest)) because package tests clear the registry and require schema re-finalize on each run.
- No `DATABASE_ROUTERS` are registered in `examples/fakeshop/config/settings.py` (verified by `grep -n "DATABASE_ROUTERS" config/settings.py` returning empty). All routing in fakeshop is explicit via `.using(alias)`; the cooperation contract this card pins works the same way against an implicit router and an explicit `.using()`, but the fakeshop live tests use `.using()` because that's what fakeshop's existing seed pipeline does.
- [`docs/GLOSSARY.md`][glossary] `docs/GLOSSARY.md #"## Multi-database cooperation"` carries the `## Multi-database cooperation` entry; Slice 3 sets its status to `shipped (`0.0.7`)` and replaces the present-tense paragraph with the four narrowed-axis bullets ([Doc updates](#doc-updates) pins the wording). That entry is the shipped statement of the contract; this spec's [Decision 3](#decision-3--the-cooperation-contract-four-axes) is its long form.
- [`tests/optimizer/`][tests-optimizer-dir] is an established test package (it carries `__init__.py` and a set of shipped optimizer-test modules), so adding `test_multi_db.py` extends it in place; no new subdirectory is needed.
- The version pins live in three places that move together: [`pyproject.toml`][pyproject] `pyproject.toml #"version ="`, [`django_strawberry_framework/__init__.py`][django-strawberry-framework-init] `django_strawberry_framework/__init__.py #"__version__ ="`, and [`tests/base/test_init.py::test_version`][test-init]. None of the three is this card's to touch: the `[0.0.7]` heading in [`CHANGELOG.md`][changelog] is shared by every card in the joint cut — [`DjangoListField`][glossary-djangolistfield] (`DONE-020-0.0.7`), [`Django AppConfig`][glossary-django-appconfig] (`DONE-021-0.0.7`), [`Schema export management command`][glossary-schema-export-management-command] (`DONE-022-0.0.7`) and the rest — and this card appends its bullet there, with the bump owned by the last card to ship per [Decision 9](#decision-9--joint-007-cut).

## Goals

1. Ship [`docs/SPECS/spec-023-multi_db-0_0_7.md`][spec-023] (this document) documenting the cooperation contract on four narrowed axes: (a) `router.db_for_read` on FK-id elision stubs, with the parent row forwarded as the `instance=` hint when present and `None` otherwise; (b) explicit `.using(alias)` `_db` preservation through [`OptimizationPlan.apply`][plans] for root querysets; (c) consumer-provided [`OptimizerHint.prefetch(Prefetch(queryset=...))`][glossary-optimizerhint] alias round-trip with the inner queryset's `_db` intact (a generated `Prefetch` child queryset does not carry the root alias in the plan; it is routed alias-late at fetch time — that boundary is explicit per [Decision 3](#decision-3--the-cooperation-contract-four-axes), and first-class shard-aware *planning* stays deferred to [`BACKLOG.md`][backlog] item 41); (d) strictness-mode N+1 detection remains active for rows loaded from non-default database aliases — the check is connection-agnostic and surfaces the same `OptimizerError` shape regardless of alias. None of the four axes claims that strictness routes connections or that a plan bakes an alias into a generated child queryset.
2. Ship the **six package-internal tests** pinned in [Test plan](#test-plan). Resolver-level tests in `tests/types/test_resolvers.py` (five): (a) FK-id elision stub `_state.db` is set via `router.db_for_read`, (b) the router-call's `instance=` argument is the parent row when the parent has a `_state` attribute, (c) the router-call's `instance=` argument is `None` when the parent row lacks `_state`, (d) a null FK takes the `return None` early-exit branch and does NOT call the router, (e) the strictness-mode N+1 check is connection-agnostic — it accepts rows with `_state.db != "default"` unchanged and surfaces the same `OptimizerError` shape regardless of alias. Optimizer-plan-level test in `tests/optimizer/test_multi_db.py` (one): (f) consumer-provided [`OptimizerHint.prefetch(Prefetch(queryset=Model.objects.using("shard_b").all()))`][glossary-optimizerhint] round-trips through plan construction with the consumer's `_db` intact on the inner queryset. Decision 3 axis 2 ([`OptimizationPlan.apply(qs)`][plans] preserves `qs._db` for an explicit `.using()` parent) is verified transitively by the Slice 2 live `/graphql/` HTTP test, NOT by a separate package-internal test — per [`AGENTS.md`][agents] #"Test through real usage, prefer the example project"'s "coverage achievable via a real GraphQL query against fakeshop MUST be earned that way" rule.
3. Ship `examples/fakeshop/test_query/test_multi_db.py` with **two** live `/graphql/` HTTP tests against the sharded fakeshop layout — both decorated with `@pytest.mark.django_db(databases=["default", "shard_b"])`, both seeding a full `Branch → Shelf → Book` chain on the queried alias, both reaching `/graphql/` through `django.test.Client.post(...)` against a temp URLConf under `override_settings(ROOT_URLCONF=...)`: (a) seeding rows on `shard_b` and reading them through `/graphql/` via a `.using("shard_b")` root resolver returns the seeded rows, (b) cross-shard reads return only rows from the queried alias (a chain seeded on `default` is not visible through a `using("shard_b")` resolver, demonstrating shard isolation under the existing cooperation contract).
4. Flip [`Multi-database cooperation`][glossary-multi-database-cooperation] in [`docs/GLOSSARY.md`][glossary] from `planned for 0.0.7` to `shipped (0.0.7)`; tighten the entry body to past-tense wording matching shipped entries.
5. Add a one-line forward-pointer to [`docs/README.md`][readme]'s `### Sharded mode (multi-DB)` section linking to the GLOSSARY entry, so a consumer reading the example onboarding sees the package's commitment.
6. Preserve [`AGENTS.md`][agents] #"Add a settings key only when the feature that needs it lands"'s "Add a settings key only when the feature that needs it lands" by omitting any new `DJANGO_STRAWBERRY_FRAMEWORK.*` settings keys.
7. Keep `__all__` unchanged — the cooperation contract is plumbing the package already honors, not a new symbol.

## Non-goals

- First-class sharding-aware planning — cross-shard joins, automatic shard selection based on FK, multi-shard aggregates, `Meta.preferred_database`. Tracked in [`BACKLOG.md`][backlog] item 41 (post-`1.0.0` differentiation) per the [`KANBAN.md`][kanban] card's Out of scope bullet.
- A package-level `DATABASE_ROUTERS` opinion. Routing policy is consumer-shaped; the package cooperates with whatever router the consumer registers and does not opine on which model lives on which shard.
- New consumer-facing API. No new symbol lands. No new `Meta.*` key. No new settings key. No new exception class. The contract is a behavior surface the package already exhibits.
- Production code changes in `0.0.7`. The cooperation already exists at [`types/resolvers.py::_build_fk_id_stub`][resolvers]. This card pins the behavior with tests + docs (per [Decision 2](#decision-2--no-production-code-change)); production code changes belong in follow-up cards if a test surfaces a regression.
- A `manage.py` helper for shard introspection or cross-shard queries. The example project's `seed_shards` command lives in `examples/fakeshop/`, not in the package; the package does not ship multi-db tooling.
- Settings-backed default shard alias. [`AGENTS.md`][agents] #"Add a settings key only when the feature that needs it lands" forbids preemptive settings; if a future card needs one (e.g., a planning hint that the package should prefer one shard), it adds the key alongside the consuming behavior.
- Auto-calling [`finalize_django_types()`][glossary-finalize-django-types] per database alias. Finalization is global to the process and identical regardless of routing; it does not need to be re-run when the queryset changes connections.

## Borrowing posture

Multi-database cooperation is a Django capability neither reference package documents as a contract. This card has no upstream surface to borrow.

### From `strawberry-django` — no precedent to borrow

Local source path: `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/optimizer.py`. Verified by inspection: the file does not call `router.db_for_*` anywhere; multi-db cooperation rides entirely on the queryset's `_db` attribute (the same shape our package ships today). There is no `docs/multi-db.md` in the upstream's repo; no `tests/test_multi_db.py`; no documented stance on what consumers can rely on under `.using()`.

The shape we ship is functionally equivalent to the upstream's — a queryset's `_db` survives `select_related` / `prefetch_related` / `Prefetch` chains because Django's queryset API preserves it — but we additionally call `router.db_for_read(...)` on FK-id elision stubs (the `_build_fk_id_stub` path at [`types/resolvers.py::_build_fk_id_stub`][resolvers]), which the upstream does not. The `router.db_for_read` call is necessary because an FK-id elision stub is a freshly-constructed model instance with no `_db` from a queryset to inherit; without the router lookup the stub would default to whatever `_state.db` Django picks for new instances (which is `None` until `save()`). The upstream's optimizer does not implement FK-id elision, so the cooperation gap doesn't arise there.

### From `graphene-django` — no precedent to borrow

Local source path: `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/`. Verified: no `router.db_for_*` calls anywhere in the package source. The package is database-agnostic by accident — `RelayConnectionField` and `DjangoListField` resolvers return whatever queryset the consumer hands them, and queryset `.using()` propagates through Django's machinery without the package noticing.

### Explicitly do not borrow

- A `DATABASE_ROUTERS` reference router class in the package. Routing policy is consumer-shaped; shipping a "default" router would impose an opinion the package has no business holding. Compare: Django ships no default router class either; the consumer registers one or doesn't.
- A `Meta.preferred_database` declarative shortcut. Tracked in [`BACKLOG.md`][backlog] item 41; out of scope here.
- Cross-shard join detection / rejection. The optimizer can't see across shards (each shard has its own connection); a consumer who writes `Item.objects.using("shard_a").filter(category__in=Category.objects.using("shard_b"))` gets whatever Django's queryset compiler does (typically an `OperationalError` from the cross-connection subquery). This card does not improve on or document that failure mode; [`BACKLOG.md`][backlog] item 41 covers it.

## User-facing API

The shipped consumer surface in `0.0.7` adds **no new symbols**. The contract is documented in [`docs/GLOSSARY.md#multi-database-cooperation`][glossary-multi-database-cooperation] and pinned with tests. No `__all__` change. No new `Meta.*` key. No new exception class.

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

- The optimizer's selection-tree walk respects the consumer's `select_related("shelf")` (per [`Queryset diffing`][glossary-queryset-diffing]) and adds any further optimizations on top via `qs.prefetch_related(...)` / `qs.only(...)` — both of which preserve the queryset's `_db` for explicit-`.using()` querysets ([`OptimizationPlan.apply(qs)`][plans] at [`plans.py::OptimizationPlan.apply`][plans] round-trips `_db` unchanged).
- FK-id elisions on forward relations route through `router.db_for_read(<related_model>, instance=<parent_row>)` (when the parent has a `_state` attribute) or `instance=None` (when it does not); the elision stub's `_state.db` is whatever the router returns for that call. The package forwards the parent row as the `instance=` hint so consumer-defined routers can consult the parent's routing context if they want to; what the router actually returns is consumer-shaped.
- Strictness-mode N+1 detection ([`_check_n1`][resolvers]) remains active for rows loaded from any database alias. The check inspects `_prefetched_objects_cache`, `_state.fields_cache`, the planned-resolver set, and the strictness mode — it does NOT inspect `root._state.db` or `queryset._db`, so the package does not re-route strictness; Django owns which alias any permitted lazy load would actually use. The error class (`OptimizerError`) and message (`"Unplanned N+1: <field>"`) are unchanged under `.using("shard_b")`.
- The [`get_queryset` visibility hook][glossary-get-queryset-visibility-hook] cooperates with routing on the **root** queryset: a consumer-provided `get_queryset` body that returns `queryset.filter(...)` preserves whatever `_db` the inbound queryset carried, and that `_db` survives plan application. On a single related object the same hook is re-applied on the related row's own connection: the resolver reads `related._state.db` and pins the visibility queryset to it ([`types/resolvers.py::_visible_related_object`][resolvers]), so the hook never evaluates a `shard_b` row's visibility against `default`. **Generated `Prefetch` child querysets do NOT inherit the root queryset's `_db` at plan-construction time** — [`_build_child_queryset`][walker] at [`walker.py::_build_child_queryset`][walker] starts from `related_model._default_manager.all()` and optionally applies `target_type.get_queryset(qs, info)`, neither of which threads the root alias through. Routing for a generated child is **alias-late**: it is decided at fetch time, against the parent rows actually in hand. Django's own prefetch machinery routes with the parent instances' alias, and where the package builds a child queryset itself it pins that alias explicitly — [`optimizer/single_parent_fetch.py #"child_qs = spec.pristine_child_queryset.using(queryset.db)"`][single-parent-fetch] on the degenerate single-parent path, and [`filters/sets.py #"child_manager.using(parent_db).all()"`][filters-sets] so a related filter's child visibility hook sees the same database as the parent request. Consumers who need a specific alias fixed in the plan pass a `Prefetch(queryset=Model.objects.using("shard_b"))` via [`OptimizerHint.prefetch(...)`][glossary-optimizerhint]; that consumer-provided `Prefetch` round-trips through plan construction with its own `_db` intact.

### Default usage — `DATABASE_ROUTERS` and implicit `db_for_read`

```python path=null start=null
# In settings.py
DATABASE_ROUTERS = ["myapp.routers.ShardRouter"]

# Consumer schema — no explicit .using() needed
@strawberry.type
class Query:
    @strawberry.field
    def all_books(self, info) -> list[BookType]:
        return models.Book.objects.all()  # router picks the connection at evaluation time
```

The package's contract under this shape:

- **Implicit-router root queryset:** `Model.objects.all()` carries `_db is None` until evaluation. The optimizer's `select_related` / `prefetch_related` / `only` additions are `_db`-neutral (they don't force a connection); Django routes at evaluation time via the registered `DATABASE_ROUTERS`. The package does not pre-route on the consumer's behalf.
- **FK-id elision stubs:** still route through `router.db_for_read(<related_model>, instance=<parent_row_or_None>)` because the stubs are freshly-constructed model instances that don't inherit a queryset alias — the router lookup is the only way to give them a stable `_state.db`. This is the same call path as the explicit-`.using()` case; the router decides the alias for both.
- **Strictness and `get_queryset` cooperation:** same as the explicit-`.using()` case. Strictness is connection-agnostic; `get_queryset` cooperation is whatever the consumer's hook returns.

The difference between explicit `.using(alias)` and implicit `DATABASE_ROUTERS`: explicit pins `_db` on the queryset before the optimizer ever sees it (and the package preserves that `_db` through plan application); implicit leaves `_db` unset and lets Django route at evaluation. The package's behavior in both shapes is consistent — preserve what's there, don't force what isn't, and consult the router only on FK-id elision stubs where there's no queryset alias to inherit.

### Error shapes

No new error shapes. The package does not raise on cross-shard queries (Django's `OperationalError` surfaces unchanged); the package does not raise on unrouted querysets (the `default` alias applies); the package does not raise on multi-shard `Prefetch` chains where each shard's queryset is independently consistent.

The one error shape the cooperation respects: strictness-mode N+1 detection ([`Strictness mode`][glossary-strictness-mode]) still fires under `using("shard_b")` if the relation is unplanned and would lazy-load. The error class (`OptimizerError`) and message (`"Unplanned N+1: <field>"`) are unchanged from the single-DB path.

## Architectural decisions

### Decision 1 — Spec filename and canonical naming

The spec carries the structured stem **`spec-023-multi_db-0_0_7`**, NOT `docs/spec-multi_db.md` as the [`KANBAN.md`][kanban] card body's `Definition of done` bullet 1 names it. The file is archived at **`docs/SPECS/spec-023-multi_db-0_0_7.md`** (this document); its terms CSV and rationale companion sit beside each other at `docs/SPECS/appx/spec-023-multi_db-0_0_7-terms.csv` and `docs/SPECS/appx/spec-023-multi_db-0_0_7-rationale.md`.

**Path lifecycle.** Simple rule: references point at whichever path the file actually has at the time the reference is written.

- An in-flight spec lives at `docs/spec-<NNN>-<topic>-<0_0_X>.md` and every reference to it uses that path; the [`KANBAN.md`][kanban] WIP card's `Active spec:` line points there.
- The [`docs/SPECS/NEXT.md`][next] Step 8 archive pass moves the spec under `docs/SPECS/` and its `-terms.csv` / `-rationale.md` companions under `docs/SPECS/appx/`, rewriting every cross-reference in one sweep. After it runs, every reference uses the archived path — which is what this spec and the [`KANBAN.md`][kanban] Done card use.

The implementation close-out and the next spec-author's Step 8 are independent workflows in this repo; neither assumes the other has run.

Rationale companion — this Decision's justification, its two rejected filename alternatives, and the revision history behind the lifecycle note: [Decision 1][rationale-d1].

### Decision 2 — No production code change

The card ships **zero production code change**. The cooperation surface this spec pins (`router.db_for_read` at [`types/resolvers.py::_build_fk_id_stub`][resolvers]; queryset `_db` propagation through the optimizer; `get_queryset` downgrade routing; strictness mode under `.using()`) already exists in source today.

Rationale companion — this Decision's justification (including the grep-population statement as it was written) and its three rejected alternatives: [Decision 2][rationale-d2].

### Decision 3 — The cooperation contract: four axes

The contract this card pins covers exactly four cooperation axes. Listed here with the source-of-truth location for each.

1. **`router.db_for_read` on FK-id elision stubs.** [`types/resolvers.py::_build_fk_id_stub`][resolvers]. When the optimizer elides a forward-relation `id`-only selection, the stub is built via `stub = field_meta.related_model(pk=related_id)` and then `state.db = router.db_for_read(field_meta.related_model, instance=instance)` runs, where `instance` is `root if hasattr(root, "_state") else None`. The package forwards the parent row as the `instance=` hint when it has one; consumer-defined routers decide what to return. Subsequent attribute reads on the stub hit whatever connection the router returned. Verified by the four FK-id-elision tests in `tests/types/test_resolvers.py` per [Test plan](#test-plan).
2. **Explicit `.using(alias)` `_db` preservation through `OptimizationPlan.apply`.** [`optimizer/walker.py`][walker], [`optimizer/plans.py::OptimizationPlan.apply`][plans]. When the consumer's resolver returns `Model.objects.using("shard_b").all()` (explicit `_db`), the optimizer's plan application calls `qs.select_related(...)`, `qs.prefetch_related(...)`, `qs.only(...)` (the [`only()` projection][glossary-only-projection] path) on that queryset — all of which preserve `_db` by Django queryset contract. `qs._db == "shard_b"` survives plan application unchanged. **Implicit-router querysets (no `.using(...)`) carry `_db is None` until evaluation**; the package does not force a connection on the consumer's behalf and lets Django route at evaluation time. Verified transitively by Slice 2's live HTTP test — `test_using_shard_b_resolver_returns_rows_seeded_on_shard_b` in `examples/fakeshop/test_query/test_multi_db.py` — which queries a resolver returning `Book.objects.using("shard_b").select_related("shelf__branch")` and asserts the seeded `shard_b` titles appear in the JSON response. The assertion cannot pass unless `OptimizationPlan.apply` preserves `_db` on the resolver's queryset: if `_db` were dropped, the queryset would route to `default` (empty of test seed) and the response would contain zero rows. Per [`AGENTS.md`][agents] #"Test through real usage, prefer the example project" (real-world live-HTTP coverage is preferred over package-internal mocking when both reach the line), axis 2 is verified through the live test rather than through a separate package-internal `OptimizationPlan.apply` assertion.
3. **Consumer-provided `Prefetch(queryset=...)` `_db` preservation.** [`OptimizerHint.prefetch(...)`][glossary-optimizerhint] accepts a consumer-built `Prefetch(lookup, queryset=Model.objects.using("shard_b").all())` and round-trips the inner queryset's `_db` through plan construction unchanged. **A generated `Prefetch` queryset does NOT carry the parent queryset's `_db` in the plan** (verified against [`optimizer/walker.py::_build_child_queryset`][walker] that `_build_child_queryset` starts from `field.related_model._default_manager.all()` and optionally applies `target_type.get_queryset(qs, info)` — neither of which threads the root queryset's alias into the child). That is deliberate rather than incidental: a plan is cached and selection-shaped, so an alias baked into it at plan-construction time would freeze one resolver's connection choice into a cache entry another resolver reads, and it would have been resolved without the parent-instance hint the router needs. **Routing for a generated child is instead alias-LATE — decided at fetch time, against the parent rows in hand.** Django's own prefetch machinery routes with the parent instances' alias, and where the package builds a child queryset itself it pins that alias explicitly: [`optimizer/single_parent_fetch.py #"child_qs = spec.pristine_child_queryset.using(queryset.db)"`][single-parent-fetch] on the degenerate single-parent path, and [`filters/sets.py #"child_manager.using(parent_db).all()"`][filters-sets] so a related filter's child `get_queryset` visibility hook runs against the same database as the parent request. Consumers who need a specific alias fixed in the plan use `OptimizerHint.prefetch(Prefetch(queryset=...))`; the package round-trips that intact. What stays outside the contract is shard-aware *planning* — an alias resolved at plan-construction time — tracked in [`BACKLOG.md`][backlog] item 41 and deferred per [Decision 2](#decision-2--no-production-code-change). Verified by Slice 1's optimizer-plan-level test (f) — `test_consumer_provided_prefetch_via_optimizer_hint_round_trips_using_alias` in `tests/optimizer/test_multi_db.py` — per [Test plan](#test-plan).
4. **Strictness mode is connection-agnostic.** [`types/resolvers.py::_check_n1`][resolvers]. The strictness check inspects `_prefetched_objects_cache`, `_state.fields_cache`, the planned-resolver set, and the strictness mode — it does NOT inspect `root._state.db`, `queryset._db`, or `router.db_for_read(...)`. Strictness remains active for rows loaded from any database alias; the error class (`OptimizerError`) and message (`"Unplanned N+1: <field>"`) are unchanged under `.using("shard_b")`. The package does not re-route the check; Django owns which alias a permitted lazy load (under `strictness="off"` / `"warn"`) would actually use via the descriptor protocol and the parent row's `_state.db`. Verified by Slice 1's resolver-level test (e) — `test_strictness_check_is_connection_agnostic_under_non_default_alias` in `tests/types/test_resolvers.py` — per [Test plan](#test-plan). The test sets `root._state.db = "shard_b"` to prove the connection-agnostic shape, not to prove routing — with `strictness="raise"` the lazy load is intentionally prevented, so the test cannot prove a connection ever gets used.

The four axes are stated at the plan and resolver seams where the package itself touches routing; the same alias-late principle governs every other place it builds a queryset from rows already in hand. The visibility re-check on a single related object is the clearest instance: when the relation's target type declares a custom `get_queryset`, [`types/resolvers.py::_visible_related_object`][resolvers] #"source = source.using(alias)" reads the related row's own `_state.db` and pins the visibility queryset to it, so a row loaded from `shard_b` has its visibility predicate evaluated on `shard_b` rather than on `default`. The alias comes from the row, never from a plan — which is why none of the four axes needs a clause about it.

Beyond the four axes and the alias-late principle they rest on, the following are **out of scope for the contract**:

- Cross-shard joins. The optimizer cannot plan them; the consumer's queryset compiler raises `OperationalError`; the package does not improve on this.
- Multi-shard aggregates. The optimizer aggregates against one queryset at a time, on its alias; cross-shard aggregation requires consumer-side logic.
- Routing policy. Consumer-shaped.
- `default_database` / preferred-shard selection. Consumer-shaped.

Rationale companion — this Decision's justification and the per-axis narrowing history: [Decision 3][rationale-d3].

### Decision 4 — No routing decoration on fakeshop schemas

The fakeshop schemas at [`examples/fakeshop/apps/library/schema.py`][schema] and [`examples/fakeshop/apps/products/schema.py`][products-schema] are NOT modified to inject `.using()` routing. Slice 2's live tests exercise routing through a per-test schema fixture (inline `@strawberry.type` Query class declared inside the test module) or a temporary monkeypatched root resolver, NOT by editing the example app schemas.

Rationale companion — this Decision's justification and its two rejected alternatives: [Decision 4][rationale-d4].

### Decision 5 — Package-internal tests use a fixture router, not `FAKESHOP_SHARDED`

Package-internal tests do NOT depend on `FAKESHOP_SHARDED=1` or on the existence of `db_shard_b.sqlite3`. The two files cover:

- **`tests/types/test_resolvers.py` (extended; resolver-level)** — the four FK-id-elision tests (stub `_state.db` shape, `instance=parent_row`, `instance=None`, null-FK early return) AND the strictness connection-agnostic-shape test. The four FK-id tests mock `django_strawberry_framework.types.resolvers.router.db_for_read` (via `monkeypatch.setattr(...)` or `unittest.mock.patch.object(...)`); the strictness test does NOT need the router mock — it asserts on `_check_n1`'s connection-agnostic behavior and never invokes the elision path.
- **`tests/optimizer/test_multi_db.py` (new; optimizer-plan-level)** — one consumer-`OptimizerHint.prefetch(Prefetch(queryset=...using...))` round-trip test. Does not exercise FK-id elision, so does not need a router mock; asserts directly on the queryset embedded in the consumer-provided `Prefetch` object after plan construction. Decision 3 axis 2 (`OptimizationPlan.apply` `_db` preservation) is verified transitively by Slice 2's live HTTP test per `AGENTS.md` #"Test through real usage, prefer the example project" and is NOT covered by a separate package-internal assertion in this file.

Mock target (pinned when a mock is needed):

- `monkeypatch.setattr(django_strawberry_framework.types.resolvers.router, "db_for_read", Mock(return_value="default"))` — patches the imported alias inside the resolvers module, so the patch survives the `from django.db import router` import at the top of `types/resolvers.py`.
- Equivalently: `unittest.mock.patch.object(django_strawberry_framework.types.resolvers, "router")` followed by setting the mocked router's `db_for_read.return_value`. Both shapes are acceptable; tests use whichever reads cleaner per test.

Rationale companion — this Decision's justification and its three rejected alternatives: [Decision 5][rationale-d5].

### Decision 6 — Live coverage under `FAKESHOP_SHARDED=1`

`examples/fakeshop/test_query/test_multi_db.py` skips the entire module at collection time when `os.environ.get("FAKESHOP_SHARDED") != "1"` via `pytest.skip(reason, allow_module_level=True)`, NOT `pytest.mark.skipif`.

Justification:

- `config.settings` decides `DATABASES` at module-import time, based on `os.environ.get("FAKESHOP_SHARDED")`. Importing the fakeshop project models under single-DB mode and then trying to query against `using("shard_b")` would raise `ConnectionDoesNotExist` because `shard_b` is not registered in `DATABASES`. The `pytest.skip(allow_module_level=True)` shape skips before any imports below it run, so the model imports happen only when the env var is set.
- `pytest.mark.skipif(os.environ.get("FAKESHOP_SHARDED") != "1", ...)` would not work for the same reason: the test module's imports run before pytest evaluates the mark, so the module would fail to import in single-DB mode (the per-test resolver fixtures would try to construct querysets against `shard_b`).
- The pattern is the tree's shared autouse reload fixture (per [Decision 7](#decision-7--the-reload-fixture-comes-from-the-shared-test_query-conftest)) with an additional early-module-skip guard on top.

Pinned shape (test-module header — a single `import pytest` placed before the skip block; the autouse fixture below uses the same name with no `# noqa`-suppressed second import):

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
import strawberry
from apps.library import models
from django.test import Client, override_settings
from django.urls import clear_url_caches, path
from strawberry.django.views import GraphQLView  # or strawberry.django.views.AsyncGraphQLView as preferred

from django_strawberry_framework import DjangoOptimizerExtension
from django_strawberry_framework.registry import registry
```

(Annotation on the top-block imports: `os` is read by the skip guard itself, so it is the only stdlib name the block needs. The module-reload work — `sys.modules.get(...)` plus `importlib.reload(...)` / `importlib.import_module(...)` recreating `apps.library.schema`, `config.schema`, and `config.urls` after the registry is cleared — belongs to the shared autouse fixture per [Decision 7](#decision-7--the-reload-fixture-comes-from-the-shared-test_query-conftest), so `importlib` and `sys` are not imported here.)

(The header pins what these two tests need, not a ceiling on the module: a later suite adding its own surface adds its own imports. `DjangoOptimizerExtension` is the only package import these two require, because `BookType` (the `DjangoType` subclass under test) is imported inside the `_build_test_schema` per-test fixture AFTER the autouse reload per [Decision 7](#decision-7--the-reload-fixture-comes-from-the-shared-test_query-conftest) — importing it at the test-module top would capture a stale class object before the reload fixture runs. `finalize_django_types()` is called by the reloaded `apps.library.schema` module body, so nothing here declares a `DjangoType` subclass or invokes the synchronization point. Do NOT add `DjangoType` / `finalize_django_types` to the top-level imports on these tests' account — ruff flags both as `F401` unused, and the Slice 2 checklist forbids `# noqa` suppressions.)

**Live `/graphql/` HTTP exclusively, with the schema built AFTER the autouse reload fixture runs.** A static module-level `_test_schema` is incompatible with [Decision 7](#decision-7--the-reload-fixture-comes-from-the-shared-test_query-conftest)'s reload fixture; the per-test holder pattern below builds the schema against the freshly-reloaded `DjangoType` classes.

**The holder-pattern URLConf:** the test module declares a module-level mutable holder (a `_current = {"schema": None}` dict OR a class attribute on a small `_Current` namespace class) that the temp URLConf's view reads from at request time. A per-test fixture (running after the autouse reload fixture) rebuilds the schema against the freshly-reloaded `apps.library.schema.BookType` and stores it on `_current["schema"]`. The URLConf's `path("graphql/", ...)` binds a view callable that reads `_current["schema"]` per request, so it always sees the freshly-built schema. Pseudocode:

```python path=null start=null
# Module-level (after the skip block):
_current: dict[str, object | None] = {"schema": None}
def _graphql_view(request):  # closure-bound view that reads the holder per request
    schema = _current["schema"]
    assert schema is not None, "_build_test_schema fixture must run before any /graphql/ request"
    return GraphQLView.as_view(schema=schema)(request)
urlpatterns = [path("graphql/", _graphql_view)]

# Per-test fixture (depends on the autouse reload fixture so it runs AFTER reload):
@pytest.fixture
def _build_test_schema(_reload_project_schema_for_acceptance_tests):
    from apps.library.schema import BookType  # freshly-reloaded class
    @strawberry.type
    class _MultiDbTestQuery:
        @strawberry.field
        def books_on_shard_b(self, info) -> list[BookType]:
            return models.Book.objects.using("shard_b").select_related("shelf__branch")
    _current["schema"] = strawberry.Schema(
        query=_MultiDbTestQuery,
        extensions=[DjangoOptimizerExtension()],
    )
    yield
    _current["schema"] = None
```

**Each test:**

1. Declares `@pytest.mark.django_db(databases=["default", "shard_b"])` so `pytest-django` permits read/write access to `shard_b`.
2. Declares the `_build_test_schema` fixture so the per-test schema is rebuilt after the autouse reload.
3. Seeds rows via `_seed_book_chain(alias, title=...)` (full `Branch → Shelf → Book` chain).
4. Wraps the body in `with override_settings(ROOT_URLCONF=__name__):`, calls `clear_url_caches()` immediately after entering the override context AND again in a `finally` block (or fixture teardown) — `__name__` resolves to the test module's dotted path at runtime, so Django re-resolves `/graphql/` against the temp URLConf.
5. Sends the GraphQL request via `django.test.Client.post("/graphql/", data={"query": query}, content_type="application/json")` and asserts on the JSON response.

The in-process `_test_schema.execute_sync(...)` path is NOT acceptable here — it skips URL routing, the view, and the Django request pipeline that the live HTTP rule in [`AGENTS.md`][agents] #"Test through real usage, prefer the example project" names as the right tier when the surface is reachable from a real query.

Rationale companion — this Decision's six rejected alternatives and the revision history behind the pinned harness shape: [Decision 6][rationale-d6]. The justification above stays in the spec because it changes how the module is written.

### Decision 7 — The reload fixture comes from the shared `test_query` conftest

`examples/fakeshop/test_query/test_multi_db.py` does not declare its own registry-reload fixture. It depends on the autouse `_reload_project_schema_for_acceptance_tests` at [`examples/fakeshop/test_query/conftest.py::_reload_project_schema_for_acceptance_tests`][test-query-conftest], which rebuilds the whole project schema once per module — the same fixture every other module in the tree uses. Package tests clear the registry, so any live `/graphql/` module needs that rebuild before its first request; one shared definition is what keeps every module in the tree rebuilding the same way.

Rationale companion — the "copy it verbatim, do not pre-emptively factor" posture this Decision started from, the condition it named for extracting the fixture, and its two rejected alternatives: [Decision 7][rationale-d7].

### Decision 8 — No README / GOAL / TODAY edits

This card does NOT edit [`README.md`][root-readme], [`GOAL.md`][goal], or [`TODAY.md`][today].

The one user-facing breadcrumb is the [`docs/README.md`][readme] `### Sharded mode (multi-DB)` one-liner per the card DoD bullet 5 — that's `docs/README.md`, the documentation index, not the root `README.md`.

Rationale companion — this Decision's justification: [Decision 8][rationale-d8].

### Decision 9 — Joint `0.0.7` cut

`0.0.7` ships under the joint-cut policy from [`docs/SPECS/spec-020-list_field-0_0_7.md`][spec-020] [Decision 10][spec-020-decision-10--joint-007-cut]: every card in the bundle — this one among them — accumulates its `### Added` entries under the same `[0.0.7]` heading in [`CHANGELOG.md`][changelog], and the bundle is cut once as a whole. The version bump in `pyproject.toml`, `django_strawberry_framework/__init__.py`'s `__version__` line, and `tests/base/test_init.py`'s pinned version assertion is owned by whichever card ships last in the bundle, NOT this card.

The Slice 3 doc-updates list explicitly excludes the version bump.

Rationale companion — this Decision's justification and its two rejected alternatives: [Decision 9][rationale-d9].

## Implementation plan

The slice ships as **three slices** aligned with the [Slice checklist](#slice-checklist). Each slice maps to one commit; squashing all three into a single PR is acceptable given the small surface.

| Slice | Files touched | New tests | Approx. line delta |
| --- | --- | --- | --- |
| 1 — Package-internal tests | `tests/types/test_resolvers.py` (extend), `tests/optimizer/test_multi_db.py` (new) | 6 — five in `tests/types/test_resolvers.py` (FK-id elision router call shape; `instance=<parent_row>`; `instance=None` when parent lacks `_state`; null FK takes early-return and does NOT call the router; strictness check is connection-agnostic) plus one in `tests/optimizer/test_multi_db.py` (consumer-`OptimizerHint.prefetch(Prefetch(queryset=…))` round-trips with `_db`). Decision 3 axis 2 (`OptimizationPlan.apply(qs)` preserves explicit `_db`) is verified transitively by the Slice 2 live HTTP test per `AGENTS.md` #"Test through real usage, prefer the example project". | `+180 / -0` |
| 2 — Fakeshop live coverage | `examples/fakeshop/test_query/test_multi_db.py` (new) | 2 (live `.using("shard_b")` round trip; shard isolation — chain on `default` not visible through `using("shard_b")` resolver). Live HTTP exclusively; `@pytest.mark.django_db(databases=["default", "shard_b"])` on each test; full `Branch → Shelf → Book` chain per alias. | `+160 / -0` |
| 3 — Promotion + docs | [`docs/GLOSSARY.md`][glossary], [`docs/README.md`][readme], [`KANBAN.md`][kanban], [`CHANGELOG.md`][changelog] | 0 | `+22 / -6` |

Total expected delta: ~380 lines across the three slices.

The three slices must be authored in order. Slice 2 depends on Slice 1 (the package-internal contract pins must exist before the live tests can target a documented behavior); Slice 3 depends on Slice 2 (the [`CHANGELOG.md`][changelog] `### Added` line and [`KANBAN.md`][kanban] Done body must describe shipped, tested coverage, not a half-landed one).

## Edge cases and constraints

- **`router.db_for_read` `instance=` argument can be `None`.** [`types/resolvers.py::_build_fk_id_stub`][resolvers]: `instance = root if hasattr(root, "_state") else None`. Django's `db_for_read(model, instance=None, **hints)` documented signature accepts `None`; the package-default behavior (when no `DATABASE_ROUTERS` are registered) returns `"default"`. Slice 1 test (c) pins this with a synthetic test double that has no `_state` attribute.
- **FK-id elision has pre-router exits, and a nullable FK is one of them.** [`types/resolvers.py::_build_fk_id_stub`][resolvers] returns before ever consulting the router in three cases: `field_meta.attname` or `field_meta.related_model` is absent; the FK column is deferred on `root`, which returns the `_FK_ELISION_UNSAFE` sentinel so the caller falls back loudly rather than issuing a silent per-row lazy load; and `related_id is None`, which returns `None`. The `router.db_for_read` call runs only on the path past all three, so a `None` FK never reaches the router. Slice 1 test (d) (`test_fk_id_elision_returns_none_for_null_fk_and_does_not_call_router`) pins the null-FK branch explicitly and separately from the parent-lacks-`_state` branch covered by test (c); the two are different code paths.
- **Mocking `router` at the resolver-module level.** `django.db.router` is a module-level singleton; `from django.db import router` in [`types/resolvers.py #"from django.db import router"`][resolvers] binds the local name `router` to that singleton. Patching `django.db.router.db_for_read` globally would affect every test; patching `django_strawberry_framework.types.resolvers.router.db_for_read` is module-local and the pytest `monkeypatch` fixture handles teardown automatically (per [Decision 5](#decision-5--package-internal-tests-use-a-fixture-router-not-fakeshop_sharded)).
- **`pytest.skip(allow_module_level=True)` runs before imports below it.** This is the load-bearing detail for [Decision 6](#decision-6--live-coverage-under-fakeshop_sharded1): the test file's `from apps.library import models` line below the skip block runs only when the skip didn't fire. Under single-DB mode, the import never runs; under `FAKESHOP_SHARDED=1`, the import runs against a `DATABASES` dict that has both `default` and `shard_b`.
- **Sharded-mode pytest collection.** Per `examples/fakeshop/config/settings.py`, `FAKESHOP_SHARDED=1` ADDS `shard_b → db_shard_b.sqlite3` to the existing `default → db.sqlite3` layout. Django creates `test_db.sqlite3` and `test_db_shard_b.sqlite3` during pytest (per Django's `TEST` config defaults); the committed `db.sqlite3` and `db_shard_b.sqlite3` fixture files are untouched by the test suite.
- **`pytest --no-cov` and the coverage gate.** Per [`docs/SPECS/spec-022-export_schema-0_0_7.md`][spec-022] DoD item 13, workers run `uv run pytest --no-cov` locally; the 100% coverage gate is CI's job (`pyproject.toml [tool.coverage.report] fail_under = 100`). This card's new tests contribute to the gate but do not enforce it locally.
- **Test-module docstring requirement.** [`pyproject.toml [tool.ruff.lint.per-file-ignores]`](../../pyproject.toml) covers `tests/**/*.py = ["D", "ANN", ...]` and `examples/**/*.py = ["D", "ANN", ...]` (verified at [`pyproject.toml #"[tool.ruff.lint.per-file-ignores]"`](../../pyproject.toml)); docstrings and annotations in tests are NOT gate-forced. They are added for convention-matching with the existing `tests/optimizer/test_*.py` and `tests/types/test_*.py` files, NOT for ruff compliance. `# noqa` suppressions for `D` or `ANN` rules in tests are unnecessary; the test files simply carry one-line docstrings to match the existing pattern.
- **`tests/optimizer/test_extension.py` and `tests/optimizer/test_walker.py` already cover non-routing optimizer behavior.** This card's new `tests/optimizer/test_multi_db.py` sits next to them with a focused scope (multi-db only); there is no overlap with the existing modules' assertions.
- **Order independence of Slice 1 tests.** Each test uses pytest's `monkeypatch` fixture for any `router` mock so the patch is automatically removed at end of test. Tests can run in any collection order without leaking state.
- **Consumer-provided `Prefetch(queryset=...)` `_db` round-trip is a Django contract.** Django's `Prefetch(lookup, queryset=qs)` carries `qs._db` for the inner query, regardless of the parent queryset's `_db`. Slice 1's optimizer-plan-level test (f) — `test_consumer_provided_prefetch_via_optimizer_hint_round_trips_using_alias` in `tests/optimizer/test_multi_db.py` — introspects the post-plan `_prefetch_related_lookups` to assert the package round-trips that intact — we don't accidentally rebuild the consumer's queryset and lose the `_db`. **A generated child queryset does NOT carry the parent's `_db` in the plan** ([`_build_child_queryset`][walker] at [`walker.py::_build_child_queryset`][walker] starts from `field.related_model._default_manager.all()`, so the parent alias is intentionally not threaded through at plan-construction time; the alias is applied late, at fetch time, per [Decision 3](#decision-3--the-cooperation-contract-four-axes) axis 3). Consumers who need a specific alias on a child relation pass `OptimizerHint.prefetch(Prefetch(queryset=Model.objects.using(...)))` and that consumer-provided alias round-trips per the test above.
- **`OptimizationPlan.apply(qs)` is the right unit of test for queryset alias preservation, NOT `plan_optimizations(...)`.** Verified against [`optimizer/walker.py::plan_optimizations`][walker] that the live signature is `plan_optimizations(selected_fields, model, info=None, *, runtime_prefixes=None, source_type=None)` — selections + model + optional GraphQL `info`, then keyword-only `runtime_prefixes` and `source_type`; there is no `parent_type` positional. The third positional binds to `info`, and the walker subsequently calls `info.path` (via `runtime_path_from_info`), so passing a class object there would crash at the first descent into the selection tree. The parent queryset is applied via [`OptimizationPlan.apply(queryset)`][plans] at [`plans.py::OptimizationPlan.apply`][plans]. Slice 1's optimizer-plan test (f) — the consumer-`Prefetch` round-trip — uses `plan_optimizations(selected_fields, Parent, source_type=ParentType)` so the walker actually picks up the parent type's `Meta.optimizer_hints`. Decision 3 axis 2's verification path (which would otherwise have called `plan.apply(Model.objects.using("shard_b").all())` and asserted `result._db == "shard_b"`) is folded into the Slice 2 live HTTP test per the `AGENTS.md` #"Test through real usage, prefer the example project" real-world-coverage rule — a regression where `OptimizationPlan.apply` drops `_db` would make the live HTTP test's seeded-titles assertion fail.
- **Optimizer plan cache key does NOT include the database alias.** Per the shipped [`Plan cache`][glossary-plan-cache] entry, cache keys include the operation AST, target model, and root runtime path — not the queryset's `_db`. Two resolvers on the same model targeting different shards share a cached plan; correct, because the plan is selection-shaped, not connection-shaped. This is a non-decision in this card (the plan cache is unchanged); pinned here as an edge-case clarification. **Type-scoped binding for consumer-provided `Prefetch(queryset=…)` aliases:** cache keys do not include `_db`, but consumer-provided [`OptimizerHint.prefetch(Prefetch(queryset=…using…))`][glossary-optimizerhint] hints are bound to the parent `DjangoType` via [`Meta.optimizer_hints`][glossary-metaoptimizer-hints], and [`resolver_key(parent_type, …)`][plans] at [`plans.py::resolver_key`][plans] includes the parent type in the cache key. Two resolvers using the same parent `DjangoType` necessarily share the same hint config (so the same consumer-provided alias choice) — there is no per-resolver-call leak; two resolvers using *different* parent types get different cache entries. The cache invariant holds: a single cached plan is selection-shaped + type-scoped, not connection-shaped, and the consumer's `_db` choice is a per-type decision rather than a per-call one.

## Test plan

Tests live across two trees, matching the rules in [`docs/TREE.md`][tree] and [`AGENTS.md`][agents]. Test-tree placement is mandatory per [Decision 5](#decision-5--package-internal-tests-use-a-fixture-router-not-fakeshop_sharded) and [Decision 6](#decision-6--live-coverage-under-fakeshop_sharded1). Slice 1 splits across two test files — resolver-level tests extend `tests/types/test_resolvers.py` (the source-mirror partner of [`django_strawberry_framework/types/resolvers.py`][resolvers] where `_build_fk_id_stub` and `_check_n1` live); optimizer-plan-level tests land in new `tests/optimizer/test_multi_db.py`.

### `tests/types/test_resolvers.py` (extend) — five new resolver-level tests

Package tests; system-under-test is `_build_fk_id_stub(...)` AND `_check_n1(...)` in [`django_strawberry_framework/types/resolvers.py`][resolvers]. **Five** new tests added to the existing file; the strictness test lives here rather than in `tests/optimizer/test_multi_db.py` because `_check_n1` also lives in `types/resolvers.py`, per the [`docs/TREE.md`][tree] mirror rule. Single pytest item per test, no `pytest.mark.parametrize` fan-out so the count matches pytest collection output unambiguously.

**Mock contract** (pinned for the four FK-id-elision tests; the strictness test does NOT need this): tests use `monkeypatch.setattr(django_strawberry_framework.types.resolvers.router, "db_for_read", Mock(return_value="default"))` (or `monkeypatch.setattr(django_strawberry_framework.types.resolvers, "router", Mock(...))` if the test inspects more than `db_for_read`). The mock's `db_for_read.return_value = "default"` so the call's outcome does not affect the assertion (the assertion is on the call shape, not the outcome).

**`FieldMeta` construction shape** (pinned so the implementer does not have to reverse-engineer the dataclass from [`optimizer/field_meta.py`][field-meta]): each FK-id-elision test constructs a `FieldMeta` directly (NOT via `FieldMeta.from_django_field`) because the test goal is to spy on `_build_fk_id_stub`'s router-call shape, not to exercise the Django-field-introspection pipeline. The required arguments for the FK-id-elision path are `name`, `is_relation=True`, `related_model`, and `attname`; every other `FieldMeta` field has a default sufficient for this test surface (the `_build_fk_id_stub` body at [`types/resolvers.py::_build_fk_id_stub`][resolvers] only reads `related_model` and `attname`).

- `test_fk_id_elision_stub_sets_state_db_via_router_db_for_read` — exercises `_build_fk_id_stub` against a fixture row with a non-null FK and a `_state` attribute; asserts the returned stub has `_state.db == <mock return value>` and that `router.db_for_read` was called once. Pins [Decision 3](#decision-3--the-cooperation-contract-four-axes) axis 1.
- `test_fk_id_elision_router_call_passes_parent_row_as_instance` — exercises `_build_fk_id_stub` against a fixture row with a `_state` attribute; asserts `router.db_for_read` was called with `instance=<parent_row>` (not `instance=None`). Pins the parent-`instance=` forwarding contract — a regression where the call switches to `instance=None` would silently break consumer routers that consult the parent row's `_state.db` to decide the child's connection.
- `test_fk_id_elision_router_call_passes_none_instance_when_parent_lacks_state` — exercises `_build_fk_id_stub` against a synthetic parent row built with `types.SimpleNamespace(pk=1)` (no `_state` attribute); asserts the stub is built and `router.db_for_read` was called with `instance=None`. Pins the `hasattr(root, "_state")` fallback at [`types/resolvers.py::_build_fk_id_stub`][resolvers].
- `test_fk_id_elision_returns_none_for_null_fk_and_does_not_call_router` — exercises `_build_fk_id_stub` against a fixture row whose FK is `None` (i.e., `getattr(root, field_meta.attname)` returns `None`); asserts `_build_fk_id_stub(...)` returns `None` AND `router.db_for_read` was NOT called. Pins the null-FK early-return branch at [`types/resolvers.py::_build_fk_id_stub`][resolvers] explicitly, separately from the parent-lacks-`_state` branch — the two are different code paths and a regression in either is a different bug.
- `test_strictness_check_is_connection_agnostic_under_non_default_alias`. Builds a fixture row with `_state.db = "shard_b"`, ensures `field_name not in root.__dict__` AND `field_name not in root._state.fields_cache` so [`_will_lazy_load_single`][resolvers] at [`types/resolvers.py::_will_lazy_load_single`][resolvers] reports the relation is unloaded; exercises `_check_n1(info, root, field_name, parent_type, kind="forward_single")` (`"forward_single"` is the canonical [`RelationKind`][relations] for forward FK per [`utils/relations.py #"RelationKind: TypeAlias"`][relations]; `"many_to_one"` is NOT a valid `RelationKind`) with `info.context` carrying `DST_OPTIMIZER_STRICTNESS = "raise"` and a non-empty planned set that does NOT include the resolver_key; asserts `OptimizerError("Unplanned N+1: <field>")` is raised. Does NOT set `root._prefetched_objects_cache` — the single-valued detector branch does not consult it. Does NOT mock the router (the strictness check never reaches that code path). Pins [Decision 3](#decision-3--the-cooperation-contract-four-axes) axis 4 — the check accepts non-default-aliased rows unchanged and surfaces the same error shape; the assertion is about the connection-agnostic shape, NOT about which alias a (prevented) lazy load would hit.

### `tests/optimizer/test_multi_db.py` (new) — one new optimizer-plan-level test

Package tests; system-under-test is [`OptimizerHint.prefetch(...)`][hints] round-trip behavior. **One** test; single pytest item, no `parametrize` fan-out. Does not exercise FK-id elision; does not need a `router.db_for_read` mock.

Decision 3 axis 2 ([`OptimizationPlan.apply(qs)`][plans] preserves `qs._db` for an explicit `.using()` parent) is verified transitively by the Slice 2 live HTTP test — `test_using_shard_b_resolver_returns_rows_seeded_on_shard_b` in `examples/fakeshop/test_query/test_multi_db.py`. The live test's resolver returns `Book.objects.using("shard_b").select_related("shelf__branch")`; the optimizer's `OptimizationPlan.apply(...)` runs against that queryset and the test asserts the seeded `shard_b` titles appear in the JSON response. A regression where `_db` is dropped on `apply` routes the resolver's queryset to `default` (empty of test seed) and the response contains zero rows, failing the live assertion. Per [`AGENTS.md`][agents] #"Test through real usage, prefer the example project" (coverage achievable via a real GraphQL query against fakeshop MUST be earned that way), axis 2 is verified through the live test rather than a separate package-internal `OptimizationPlan.apply` assertion.

**Synthetic `selected_fields` fixture shape** (pinned so the implementer does not invent a new fixture pattern that subtly mismatches the walker's assumptions): mirror the `SimpleNamespace`-based selection-builder pattern already used by [`tests/optimizer/test_walker.py`][test-walker] and [`tests/optimizer/test_plans.py`][test-plans]. The walker reads `.name`, `.alias`, `.directives`, and `.selections` on each selection node (via `_walk_selections` / `_included_field_selections` / `_merge_aliased_selections` at [`optimizer/walker.py::_walk_selections`][walker] and surrounding helpers); the existing fixture shape covers all four attributes. Inventing a new shape risks subtle mismatches with the merge logic and aliased-selection handling.

- `test_consumer_provided_prefetch_via_optimizer_hint_round_trips_using_alias` (the `plan_optimizations` call-shape uses the `source_type=` keyword so the walker performs the per-type hint lookup). Builds a fixture parent type that declares [`Meta.optimizer_hints`][glossary-metaoptimizer-hints] `= {"<rel>": OptimizerHint.prefetch(Prefetch("<rel>", queryset=Child.objects.using("shard_b").all()))}`; constructs a plan via `plan = plan_optimizations(selected_fields, Parent, source_type=ParentType)` so the walker looks up `ParentType`'s registered `optimizer_hints`; applies via `plan.apply(Parent.objects.all())`; introspects the resulting queryset's `_prefetch_related_lookups` and asserts the inner consumer-provided `Prefetch.queryset._db == "shard_b"`. Pins [Decision 3](#decision-3--the-cooperation-contract-four-axes) axis 3 — the consumer's explicit `Prefetch(queryset=...)` survives plan construction; generated child querysets are intentionally NOT in scope per [Decision 2](#decision-2--no-production-code-change).

### `examples/fakeshop/test_query/test_multi_db.py` (new) — two live `/graphql/` HTTP tests

Live tests; system-under-test is the fakeshop project running under `FAKESHOP_SHARDED=1`. **Two** tests from this contract; single pytest item per test. Module is skipped at collection time when `FAKESHOP_SHARDED != "1"` per [Decision 6](#decision-6--live-coverage-under-fakeshop_sharded1). Each test is decorated with `@pytest.mark.django_db(databases=["default", "shard_b"])`.

**Fixture-chain contract** (pinned for every seeding step): each alias used in the test gets a full `Branch → Shelf → Book` chain seeded via `.using(alias)` because both `Book.shelf` and `Shelf.branch` are non-null FKs:

```python path=null start=null
def _seed_book_chain(alias: str, *, title: str) -> models.Book:
    branch = models.Branch.objects.using(alias).create(name=f"Branch-{alias}", city="Boston")
    shelf = models.Shelf.objects.using(alias).create(code=f"S-{alias}", topic="Test", branch=branch)
    return models.Book.objects.using(alias).create(
        title=title,
        circulation_status=models.Book.CirculationStatus.AVAILABLE,
        shelf=shelf,
    )
```

**Live-HTTP harness** (per [Decision 6](#decision-6--live-coverage-under-fakeshop_sharded1) — holder-pattern schema built after the autouse reload, module-level `urlpatterns` whose view reads the holder per request, `override_settings(ROOT_URLCONF=__name__)` with `clear_url_caches()` on enter AND in teardown):

- The test module declares a module-level `_current: dict[str, object | None] = {"schema": None}` holder.
- The test module declares a module-level closure-bound view `_graphql_view(request)` that reads `_current["schema"]` at request time and delegates to `GraphQLView.as_view(schema=schema)(request)`.
- The test module declares a module-level `urlpatterns = [path("graphql/", _graphql_view)]` for the temp URLConf.
- A `_build_test_schema` per-test fixture (depending on `_reload_project_schema_for_acceptance_tests` so it runs AFTER the autouse reload) imports the freshly-reloaded `BookType` from `apps.library.schema`, builds a `@strawberry.type class _MultiDbTestQuery` whose `books_on_shard_b` resolver returns `models.Book.objects.using("shard_b").select_related("shelf__branch")`, constructs `strawberry.Schema(query=_MultiDbTestQuery, extensions=[DjangoOptimizerExtension()])`, and stores it on `_current["schema"]`. Teardown sets `_current["schema"] = None`.
- Each test body wraps the request in `with override_settings(ROOT_URLCONF=__name__):` and calls `clear_url_caches()` immediately inside the override AND inside the `try / finally` teardown (or via the fixture finalizer); `__name__` resolves to the test module's dotted path at runtime so Django re-resolves `/graphql/` against the temp URLConf.

Tests (each declares `@pytest.mark.django_db(databases=["default", "shard_b"])` and depends on the `_build_test_schema` fixture):

- `test_using_shard_b_resolver_returns_rows_seeded_on_shard_b` — seeds two `Book` chains on `shard_b` via `_seed_book_chain("shard_b", title="A")` / `_seed_book_chain("shard_b", title="B")`; sends `POST /graphql/` with `query { booksOnShardB { title shelf { code branch { name } } } }`; asserts the JSON response contains both seeded titles. Pins end-to-end cooperation under a real router scope.
- `test_cross_shard_isolation_default_rows_not_visible_via_shard_b_resolver` — seeds one `Book` chain on the default alias via `_seed_book_chain("default", title="default-only")` AND one on `shard_b` via `_seed_book_chain("shard_b", title="shard-b-only")`; sends `POST /graphql/` with `query { booksOnShardB { title shelf { code branch { name } } } }` (the query body matches test (a)'s shape because the spec-pinned `_MultiDbTestQuery.books_on_shard_b` resolver (see [Live-HTTP harness](#test-plan)) uses `.select_related("shelf__branch")`, and under the optimizer's `.only(...)` projection a `{ title }`-only selection produces `Book.objects.only("title", "shelf_id").select_related("shelf__branch")` which Django rejects with `FieldError: Field Book.shelf cannot be both deferred and traversed using select_related at the same time`; the wider query keeps the spec-pinned resolver shape — see [Decision 4](#decision-4--no-routing-decoration-on-fakeshop-schemas) — and pins the negative shape on the returned `title` set, not on the selection narrowness); asserts only `shard-b-only` appears in the response and `default-only` does not. Pins the negative shape — the cooperation respects the consumer's queryset routing rather than aggregating across shards.

### Existing tests — no edits beyond Slice 1 extension

The Slice 1 extension to `tests/types/test_resolvers.py` adds five new test functions; the file's existing tests are NOT modified. `tests/optimizer/test_extension.py`, `tests/optimizer/test_walker.py`, and the rest of the existing test suite are NOT modified by this card; the new `tests/optimizer/test_multi_db.py` sits alongside them with a focused scope.

`examples/fakeshop/test_query/test_library_api.py` is NOT modified; the new module reaches the reload contract through the shared conftest fixture per [Decision 7](#decision-7--the-reload-fixture-comes-from-the-shared-test_query-conftest).

## Doc updates

- [`docs/GLOSSARY.md`][glossary]
  - Update the Index table row for [`Multi-database cooperation`][glossary-multi-database-cooperation] at `docs/GLOSSARY.md #"| [Multi-database cooperation](#multi-database-cooperation) |"` from `planned for `0.0.7`` to `shipped (`0.0.7`)`.
  - Update the entry body at `docs/GLOSSARY.md #"## Multi-database cooperation"` (bullets pinned to the axes from [Decision 3](#decision-3--the-cooperation-contract-four-axes)): replace the opening "Pins the existing `router.db_for_read` cooperation in `types/resolvers.py` with a spec, tests, and a `GLOSSARY.md` status entry." with past-tense "Documented cooperation surface — what the package guarantees under Django's multi-database machinery. Four axes:" followed by the four narrowed-axis bullets: (1) `router.db_for_read` on FK-id elision stubs (parent row forwarded as the `instance=` hint when present, `None` otherwise); (2) explicit `.using(alias)` `_db` preservation through [`OptimizationPlan.apply`][glossary-djangooptimizerextension]; (3) consumer-provided [`Prefetch(queryset=...)`][glossary-optimizerhint] via `OptimizerHint.prefetch(...)` round-trips with its `_db` intact — generated `Prefetch` child querysets do NOT inherit the root alias; (4) strictness-mode N+1 detection is connection-agnostic and surfaces the same `OptimizerError` shape under non-default aliases. The body's `Companion BACKLOG.md item 41` and `See also:` lines stay unchanged.

- [`docs/README.md`][readme]
  - Rewrite the `### Sharded mode (multi-DB)` section to describe the additive layout: "In sharded mode `default` keeps pointing at `db.sqlite3` (same file as single-DB mode) and `shard_b` adds `db_shard_b.sqlite3`. The two modes share the same `default` file, so a single dev workflow (`manage.py seed_data`, etc.) populates the default alias either way; the sharded mode only ADDS the secondary shard. The committed `db_shard_b.sqlite3` ships with a minimal seed via `seed_shards` so the sharded mode works out of the box." Plus a forward-pointer line: "For the cooperation contract these shards run against — explicit `.using()` `_db` preservation, FK-id elision router hints, consumer-provided `Prefetch(queryset=…)` alias round-trips, and strictness-mode behavior under non-default aliases — see [`GLOSSARY.md#multi-database-cooperation`][glossary-multi-database-cooperation]."

- [`KANBAN.md`][kanban]
  - The card sits in the Done column as `DONE-023-0.0.7 - Multi-database cooperation contract`, `Status: Done`. [`KANBAN.md`][kanban] is rendered from the kanban DB, so each card's shape is fixed by the renderer rather than by free-form prose: metadata rows (priority, parity, status, relative size, labels, `Spec:`), a `#### Glossary terms` table, `#### Verified in upstream` bullets, and a `#### Note`. This card's obligations are therefore (a) the `Spec:` row resolving to [`docs/SPECS/spec-023-multi_db-0_0_7.md`][spec-023] — the canonical name, superseding the card's `docs/spec-multi_db.md` placeholder per [Decision 1](#decision-1--spec-filename-and-canonical-naming); (b) the glossary-terms table carrying [`Multi-database cooperation`][glossary-multi-database-cooperation] at `shipped (0.0.7)`; (c) the upstream-verification bullets recording that neither `strawberry-django`'s `optimizer.py` nor `graphene_django` specifies any multi-database contract (`.using(`, `_db`, `router`, `db_for_read` all absent), so this card is parity-adjacent rather than parity-matching; and (d) the `#### Note` stating the scope in one line: pin the multi-DB cooperation contract (router-aware FK-id stubs, `.using()` preservation, `Prefetch` `_db` round-trip) plus tests, with zero production-code change.
  - The card body's `Definition of done` bullet 1 names the canonical spec path rather than the `docs/spec-multi_db.md` placeholder, per [Decision 1](#decision-1--spec-filename-and-canonical-naming).
  - The `### In progress` summary paragraph does not list this card; the `0.0.7` shipped-bundle summary lists it among the cut's seven cards.

- [`CHANGELOG.md`][changelog]
  - **Append** to the single `[0.0.7]` `### Added` subsection (do NOT create a second `[0.0.7]` heading — verified at [`CHANGELOG.md`][changelog] #"## [0.0.7] - "). Every card in the joint cut appends to that one shared section per [Decision 9](#decision-9--joint-007-cut), so it carries `DONE-020-0.0.7`'s [`DjangoListField`][glossary-djangolistfield], `DONE-021-0.0.7`'s [`Django AppConfig`][glossary-django-appconfig], `DONE-022-0.0.7`'s [`Schema export management command`][glossary-schema-export-management-command], this card's bullet, and the remaining cut cards' entries alongside them:

    > "`Multi-database cooperation` — pinned the package's cooperation contract under Django's multi-database machinery: `router.db_for_read` on FK-id elision stubs (parent row forwarded as the `instance=` hint when present, `None` otherwise); explicit `.using(alias)` `_db` preservation through `OptimizationPlan.apply` for root querysets; consumer-provided `OptimizerHint.prefetch(Prefetch(queryset=…))` round-trips with the inner queryset's `_db` intact (generated `Prefetch` child querysets do NOT inherit the root alias at plan-construction time — deferred to BACKLOG item 41); strictness-mode N+1 detection is connection-agnostic and surfaces the same `OptimizerError` shape under non-default aliases. Tests across [`tests/types/test_resolvers.py`][test-resolvers] (resolver-level FK-id elision unit tests plus the strictness connection-agnostic-shape test against `_check_n1` — five tests total, FK-id tests hermetic via mocked router), [`tests/optimizer/test_multi_db.py`][test-multi-db] (optimizer-plan-level `OptimizerHint.prefetch` round-trip — one test; `OptimizationPlan.apply` `_db` preservation is verified transitively by the live HTTP test per the repository's real-query coverage rule), and [`examples/fakeshop/test_query/test_multi_db.py`][test-query-test-multi-db] (live `/graphql/` HTTP under `FAKESHOP_SHARDED=1`, gated by `@pytest.mark.django_db(databases=…)`). [`examples/fakeshop/config/settings.py`][settings] ships an additive `DATABASES` layout — `default → db.sqlite3` in both modes; `FAKESHOP_SHARDED=1` ADDS `shard_b → db_shard_b.sqlite3` — and the secondary shard's seed is committed at [`examples/fakeshop/db_shard_b.sqlite3`][db-shard-b.sqlite3] so sharded mode works out of the box. [`docs/GLOSSARY.md#multi-database-cooperation`][glossary-multi-database-cooperation] flipped from `planned for 0.0.7` to `shipped (0.0.7)`. No production code change — the cooperation already existed at [`django_strawberry_framework/types/resolvers.py::_build_fk_id_stub`][resolvers]. [`BACKLOG.md`][backlog] item 41 owns first-class sharding-aware planning post-`1.0.0`."

  - The version bump entry is owned by **the last `0.0.7` card to ship** per [Decision 9](#decision-9--joint-007-cut), NOT this slice.
  - [`AGENTS.md`][agents] #"No CHANGELOG.md updates unless told" ("No CHANGELOG.md updates unless told") — this Slice 3 bullet is the explicit instruction.

- No edits to [`README.md`][root-readme], [`GOAL.md`][goal], or [`TODAY.md`][today] per [Decision 8](#decision-8--no-readme--goal--today-edits).

- No edits to [`docs/TREE.md`][tree]. Justification: this card adds one test file under the existing `tests/optimizer/` subdirectory (already pinned in `TREE.md`'s current-on-disk-layout under `docs/TREE.md #"Package tests for optimizer plans"`) and one test file under `examples/fakeshop/test_query/` (already pinned under `docs/TREE.md #"examples/fakeshop/test_query/"`). No new subdirectory; no new source module. The current-on-disk-layout enumeration in `docs/TREE.md` describes the subdirectories and the per-file-mirror rule rather than listing every test file, so no edit is required.

## Risks and open questions

Each item names a preferred answer for `0.0.7` and a fallback if implementation reveals the preferred answer is wrong.

- **The `[0.0.7]` `CHANGELOG.md` heading is opened before the version bump lands.** Under the joint cut a card appends its `### Added` bullet to the shared `[0.0.7]` heading while [`pyproject.toml #"version ="`][pyproject], [`django_strawberry_framework/__init__.py #"__version__ ="`][django-strawberry-framework-init], and [`tests/base/test_init.py::test_version`][test-init] still pin the previous patch, so the section accumulates entries against an unbumped version. The heading's date is a placeholder set by the first card in the bundle and is reconciled by whichever card performs the bump per [Decision 9](#decision-9--joint-007-cut); this card appends its bullet and does not bump. Verified at [`CHANGELOG.md`][changelog] #"## [0.0.7] - ".
- **KANBAN card body names `docs/spec-multi_db.md`; the spec's canonical stem is `spec-023-multi_db-0_0_7`.** Per [Decision 1](#decision-1--spec-filename-and-canonical-naming), the canonical name is the structured one. Preferred answer: Slice 3 rewrites the card body's `Definition of done` bullet 1 to point at the structured name; the Step-8 archive pass at the end of the NEXT.md flow propagates the rename to any other cross-references. Fallback: if a future agent confused by the rename creates a second `docs/spec-multi_db.md`, the structured filename's content takes precedence; the stray file is deleted in a follow-up cleanup card.
- **`pytest.skip(allow_module_level=True)` precludes per-test marker control.** Slice 2's tests all share one collection-time skip; there is no way to opt one test in and another out. Preferred answer: this is fine — both Slice 2 tests target `FAKESHOP_SHARDED=1`, and if a future test needs to run under single-DB mode it lives in a different file. Fallback: if a future card needs mixed gating, it splits the module into two files (one for the gated tests, one for the un-gated).
- **Mocking `router` at the resolver-module level versus globally.** Preferred answer: patch `django_strawberry_framework.types.resolvers.router.db_for_read` (module-local) per [Decision 5](#decision-5--package-internal-tests-use-a-fixture-router-not-fakeshop_sharded). Fallback: if Django's router internals change such that the `from django.db import router` import at [`types/resolvers.py #"from django.db import router"`][resolvers] becomes stale, the patch target shifts to wherever `router` is bound at module-import time; the test breakage is informative and a one-line fix.
- **Consumer-provided `Prefetch(queryset=...)` `_db` round-trip under Django version changes.** Preferred answer: Django's queryset API preserves `_db` on a `Prefetch(queryset=qs)` because the inner `qs` is a Django queryset and its `_db` is sticky by the standard queryset contract. The Slice 1 optimizer-plan-level test (f) — `test_consumer_provided_prefetch_via_optimizer_hint_round_trips_using_alias` in `tests/optimizer/test_multi_db.py` — pins the package's cooperation by introspecting the post-plan `_prefetch_related_lookups` and asserting the inner consumer-provided queryset's `_db` is unchanged. Fallback: if Django changes the `_db` propagation rule (extremely unlikely; would break every Django app using `Prefetch(queryset=...)`), the test fails loudly and the package needs to adapt — but that's a Django regression, not a package one.
- **A generated `Prefetch` child queryset carries no alias in the plan.** Preferred answer: this is a deliberate boundary per [Decision 3](#decision-3--the-cooperation-contract-four-axes) axis 3 — [`_build_child_queryset`][walker] at [`walker.py::_build_child_queryset`][walker] starts from `field.related_model._default_manager.all()` and the optional `target_type.get_queryset(qs, info)` does not thread the root alias, so the alias is applied late, at fetch time, against the parent rows in hand. Consumers who need a specific alias fixed in the plan use [`OptimizerHint.prefetch(Prefetch(queryset=...))`][glossary-optimizerhint]. Fallback: if consumer demand surfaces for resolving a child's alias at *plan* time rather than fetch time, a follow-up card adds it under [`BACKLOG.md`][backlog] item 41's first-class sharding-aware-planning umbrella; the contract this card pins is unchanged because it never claimed otherwise.
- **`router.db_for_read` documented signature.** Preferred answer: `(model, **hints) -> str | None` per [Django's docs](https://docs.djangoproject.com/en/stable/topics/db/multi-db/#using-routers); `instance` is the documented hint name. The package's call uses `db_for_read(field_meta.related_model, instance=instance)`, which matches the documented call shape. Fallback: if a consumer's custom router does not accept `instance=` (e.g., a router defined as `def db_for_read(self, model, **hints):` that ignores `hints`), the package's call still works — the kwarg is silently dropped on the receiving side. The cooperation contract is "we forward `instance=` when we have it"; the router's reception is consumer-shaped.
- **Strictness mode is connection-agnostic**. Preferred answer: `_check_n1` inspects `_prefetched_objects_cache`, `_state.fields_cache`, the planned-resolver set, and the strictness mode — it does NOT inspect `root._state.db` or `queryset._db`, so the package does not re-route the check based on alias. Django's descriptor protocol propagates `_state.db` to related instances accessed through the descriptor (a permitted lazy-load via `book.shelf` from a `using("shard_b")` book row would read from `shard_b` automatically), but with `strictness="raise"` the lazy load never happens — the test in Slice 1 (e) sets `root._state.db = "shard_b"` only to prove the object shape is accepted, not to prove connection routing. Fallback: if Django changes the descriptor protocol to drop `_state.db` propagation (extremely unlikely), the package's strictness check is unaffected because it doesn't inspect that attribute; only consumer code that depends on the propagation would break.
- **Cross-shard joins and the optimizer's silence.** Preferred answer: a consumer who writes a cross-shard join gets Django's `OperationalError` at queryset evaluation; the package does not catch or document this failure mode because [`BACKLOG.md`][backlog] item 41 owns the first-class sharding-aware-planning future. Fallback: if real consumer demand surfaces for "the optimizer should detect cross-shard joins and raise a friendlier `ConfigurationError`," a follow-up card adds that detection and the BACKLOG item 41 framing is unchanged.

## Out of scope (explicitly tracked elsewhere)

- First-class sharding-aware planning: cross-shard joins, automatic shard selection based on FK, multi-shard aggregates, a hypothetical `Meta.preferred_database` declarative hint, AND resolving a generated child `Prefetch`'s alias at plan-construction time rather than alias-late at fetch time (the boundary called out in [Decision 3](#decision-3--the-cooperation-contract-four-axes) axis 3 and [Risks](#risks-and-open-questions)). All tracked in [`BACKLOG.md`][backlog] item 41 (post-`1.0.0` differentiation) per the [`KANBAN.md`][kanban] card's Out of scope bullet. The hypothetical `Meta.preferred_database` does not have a [`docs/GLOSSARY.md`][glossary] entry yet and is intentionally left as plain prose rather than a linked term (the terms CSV does NOT anchor it to an existing concept; if the project decides to reserve the future-API name, that's a new GLOSSARY entry under its own card).
- A package-level `DATABASE_ROUTERS` opinion or reference router class. Routing policy is consumer-shaped.
- A `Meta.preferred_database` declarative shortcut. Out of scope; [`BACKLOG.md`][backlog] item 41.
- Cross-shard join detection. Out of scope; [`BACKLOG.md`][backlog] item 41.
- Multi-shard aggregates. Out of scope; [`BACKLOG.md`][backlog] item 41 and the future [`AggregateSet`][glossary-aggregateset] (planned for `0.1.3`) — neither aggregates across connections in the contract this card pins.
- [Connection-aware optimizer planning][glossary-connection-aware-optimizer-planning]: planned for `0.0.9`. This is `edges { node { ... } }` selection planning, NOT database-connection planning — separate concern despite the overlapping word "connection."
- Warning-free scalar registration via `StrawberryConfig.scalar_map`: `DONE-025-0.0.7` in [`KANBAN.md`][kanban]. An independent card in the same `0.0.7` bundle; its surface does not overlap this one's.

## Definition of done

The card is complete when all of the following are true:

1. [`docs/SPECS/spec-023-multi_db-0_0_7.md`][spec-023] (this document) carries the canonical structured filename per [Decision 1](#decision-1--spec-filename-and-canonical-naming), with companion [`docs/SPECS/appx/spec-023-multi_db-0_0_7-terms.csv`][spec-023-terms] anchoring every project-specific term used in the spec body to the matching [`docs/GLOSSARY.md`][glossary] heading (per [`docs/SPECS/NEXT.md`][next] Step 7).
2. `tests/types/test_resolvers.py` is extended with the **5 resolver-level tests** listed in the [Test plan](#test-plan) (the strictness test lives here per the [`docs/TREE.md`][tree] mirror rule because `_check_n1` lives in `types/resolvers.py`; null-FK and parent-lacks-`_state` are two separate tests): (a) FK-id elision stub `_state.db` via `router.db_for_read`, (b) `instance=<parent_row>` on the router call, (c) `instance=None` when parent lacks `_state`, (d) null FK takes early-return and does NOT call the router, (e) strictness check is connection-agnostic and surfaces the same `OptimizerError` shape under non-default aliases. AND `tests/optimizer/test_multi_db.py` exists and contains the **1 optimizer-plan-level test** listed in the [Test plan](#test-plan): (f) consumer-provided `OptimizerHint.prefetch(Prefetch(queryset=…))` round-trips with `_db` intact (generated child `Prefetch` `_db` carryover is NOT in scope). Decision 3 axis 2 (`OptimizationPlan.apply(qs)` preserves explicit `_db`) is verified transitively by the Slice 2 live `/graphql/` HTTP test per `AGENTS.md` #"Test through real usage, prefer the example project"'s real-world-coverage rule, NOT by a separate package-internal assertion. The four FK-id-elision tests use pytest's `monkeypatch` for the router mock; the strictness test and the optimizer-plan test do NOT mock the router. No `pytest.mark.parametrize` fan-out (single pytest item per test); six pytest items total across the two files.
3. `examples/fakeshop/test_query/test_multi_db.py` exists with the module-level `pytest.skip(allow_module_level=True)` guard from [Decision 6](#decision-6--live-coverage-under-fakeshop_sharded1) and carries the **2 tests** listed in the [Test plan](#test-plan): (a) live `.using("shard_b")` round trip, (b) shard isolation under `.using()`. Each test carries `@pytest.mark.django_db(databases=["default", "shard_b"])`. Each test seeds a full `Branch → Shelf → Book` chain per alias. Each test reaches `/graphql/` exclusively through `django.test.Client.post("/graphql/", ...)` (no in-process `_test_schema.execute_sync(...)` alternative) under `override_settings(ROOT_URLCONF=__name__)` with `clear_url_caches()`. The test schema is built inside a `_build_test_schema` per-test fixture that runs AFTER the autouse reload fixture and stores the freshly-built schema on a module-level holder (the temp URLConf's view reads from the holder per request, so it sees the freshly-built schema even after `_reload_project_schema_for_acceptance_tests` clears the registry). The autouse reload fixture is the shared `examples/fakeshop/test_query/conftest.py::_reload_project_schema_for_acceptance_tests` per [Decision 7](#decision-7--the-reload-fixture-comes-from-the-shared-test_query-conftest).
4. `examples/fakeshop/apps/library/schema.py` and `examples/fakeshop/apps/products/schema.py` are NOT modified per [Decision 4](#decision-4--no-routing-decoration-on-fakeshop-schemas). The holder-pattern schema/URLConf machinery lives inline in `examples/fakeshop/test_query/test_multi_db.py`.
5. `examples/fakeshop/config/settings.py` ships an additive `DATABASES` layout: `default → db.sqlite3` is declared unconditionally in both modes, and `FAKESHOP_SHARDED=1` ADDS `shard_b → db_shard_b.sqlite3` on top. The committed `examples/fakeshop/db_shard_b.sqlite3` fixture (materialized via `seed_shards`) ships so sharded mode works out of the box. The `seed_shards` management command operates only on the secondary `shard_b` alias (the existing dev `db.sqlite3` is populated via the normal `manage.py seed_data` workflow regardless of mode).
6. `django_strawberry_framework/` is NOT modified per [Decision 2](#decision-2--no-production-code-change) (no production code change).
7. `django_strawberry_framework/__init__.py` is NOT modified. `__all__` is unchanged.
8. `tests/base/test_init.py`'s `__all__` assertion is unchanged. Version assertion is unchanged.
9. Package coverage stays at 100% (`pyproject.toml [tool.coverage.report] fail_under = 100`) — **verified by CI's `fail_under = 100` gate, not by the worker locally** (mirroring [`docs/SPECS/spec-022-export_schema-0_0_7.md`][spec-022]). The worker's local verification is item 13's `uv run pytest --no-cov` suite-passing check; coverage assertion is CI's job after the PR opens. If CI reports a coverage regression on the PR, the worker adds the missing test before merge.
10. [`docs/GLOSSARY.md`][glossary] [`Multi-database cooperation`][glossary-multi-database-cooperation] entry is flipped from `planned for 0.0.7` to `shipped (0.0.7)` (Index table row at `docs/GLOSSARY.md #"| [Multi-database cooperation](#multi-database-cooperation) |"`; entry body at `docs/GLOSSARY.md #"## Multi-database cooperation"`). Entry body lists the four cooperation axes from [Decision 3](#decision-3--the-cooperation-contract-four-axes).
11. [`docs/README.md`][readme] `### Sharded mode (multi-DB)` section carries a one-line forward-pointer to [`GLOSSARY.md#multi-database-cooperation`][glossary-multi-database-cooperation].
12. [`README.md`][root-readme], [`GOAL.md`][goal], [`TODAY.md`][today], and [`docs/TREE.md`][tree] are NOT edited per [Decision 8](#decision-8--no-readme--goal--today-edits) and the `docs/TREE.md` justification in the [Doc updates](#doc-updates) section.
13. [`KANBAN.md`][kanban] records the card as `DONE-023-0.0.7` in the Done column, with the rendered card's `Spec:` row, glossary-terms table, upstream-verification bullets, and `#### Note` carrying the shipped scope per [Doc updates](#doc-updates); the `Definition of done` bullet 1 in the card body names the structured spec filename per [Decision 1](#decision-1--spec-filename-and-canonical-naming).
14. [`CHANGELOG.md`][changelog] `[0.0.7]` `### Added` subsection carries the new bullet pinned in [Doc updates](#doc-updates); no second `[0.0.7]` heading is created.
15. The version bump is NOT in this card per [Decision 9](#decision-9--joint-007-cut); the last `0.0.7` card to ship owns `pyproject.toml`, `__version__`, and `tests/base/test_init.py`'s version assertion.
16. Zero new public exports — `__all__` is unchanged.
17. `uv run ruff format .` passes; `uv run ruff check --fix .` passes; `uv run pytest --no-cov` passes (explicit `--no-cov` opts out of `pytest.ini`'s auto-applied `--cov`; coverage enforcement is CI's job per `pyproject.toml [tool.coverage.report] fail_under = 100`, not this slice's; workers verify the suite passes, not that coverage stays at 100%).

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../AGENTS.md
[backlog]: ../../BACKLOG.md
[changelog]: ../../CHANGELOG.md
[contributing]: ../../CONTRIBUTING.md
[goal]: ../../GOAL.md
[kanban]: ../../KANBAN.md
[pyproject]: ../../pyproject.toml
[root-readme]: ../../README.md
[today]: ../../TODAY.md

<!-- docs/ -->
[glossary]: ../GLOSSARY.md
[glossary-aggregateset]: ../GLOSSARY.md#aggregateset
[glossary-configurationerror]: ../GLOSSARY.md#configurationerror
[glossary-connection-aware-optimizer-planning]: ../GLOSSARY.md#connection-aware-optimizer-planning
[glossary-django-appconfig]: ../GLOSSARY.md#django-appconfig
[glossary-djangolistfield]: ../GLOSSARY.md#djangolistfield
[glossary-djangooptimizerextension]: ../GLOSSARY.md#djangooptimizerextension
[glossary-djangotype]: ../GLOSSARY.md#djangotype
[glossary-finalize-django-types]: ../GLOSSARY.md#finalize_django_types
[glossary-fk-id-elision]: ../GLOSSARY.md#fk-id-elision
[glossary-get-queryset-visibility-hook]: ../GLOSSARY.md#get_queryset-visibility-hook
[glossary-metaoptimizer-hints]: ../GLOSSARY.md#metaoptimizer_hints
[glossary-multi-database-cooperation]: ../GLOSSARY.md#multi-database-cooperation
[glossary-only-projection]: ../GLOSSARY.md#only-projection
[glossary-optimizerhint]: ../GLOSSARY.md#optimizerhint
[glossary-plan-cache]: ../GLOSSARY.md#plan-cache
[glossary-queryset-diffing]: ../GLOSSARY.md#queryset-diffing
[glossary-schema-export-management-command]: ../GLOSSARY.md#schema-export-management-command
[glossary-strictness-mode]: ../GLOSSARY.md#strictness-mode
[readme]: ../README.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[next]: NEXT.md
[rationale-d1]: appx/spec-023-multi_db-0_0_7-rationale.md#decision-1--spec-filename-and-canonical-naming
[rationale-d2]: appx/spec-023-multi_db-0_0_7-rationale.md#decision-2--no-production-code-change
[rationale-d3]: appx/spec-023-multi_db-0_0_7-rationale.md#decision-3--the-cooperation-contract-four-axes
[rationale-d4]: appx/spec-023-multi_db-0_0_7-rationale.md#decision-4--no-routing-decoration-on-fakeshop-schemas
[rationale-d5]: appx/spec-023-multi_db-0_0_7-rationale.md#decision-5--package-internal-tests-use-a-fixture-router-not-fakeshop_sharded
[rationale-d6]: appx/spec-023-multi_db-0_0_7-rationale.md#decision-6--live-coverage-under-fakeshop_sharded1
[rationale-d7]: appx/spec-023-multi_db-0_0_7-rationale.md#decision-7--the-reload-fixture-comes-from-the-shared-test_query-conftest
[rationale-d8]: appx/spec-023-multi_db-0_0_7-rationale.md#decision-8--no-readme--goal--today-edits
[rationale-d9]: appx/spec-023-multi_db-0_0_7-rationale.md#decision-9--joint-007-cut
[spec-020]: spec-020-list_field-0_0_7.md
[spec-020-decision-10--joint-007-cut]: spec-020-list_field-0_0_7.md#decision-10--joint-007-cut
[spec-022]: spec-022-export_schema-0_0_7.md
[spec-023]: spec-023-multi_db-0_0_7.md
[spec-023-rationale]: appx/spec-023-multi_db-0_0_7-rationale.md
[spec-023-terms]: appx/spec-023-multi_db-0_0_7-terms.csv

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[django-strawberry-framework-init]: ../../django_strawberry_framework/__init__.py
[extension]: ../../django_strawberry_framework/optimizer/extension.py
[field-meta]: ../../django_strawberry_framework/optimizer/field_meta.py
[filters-sets]: ../../django_strawberry_framework/filters/sets.py
[hints]: ../../django_strawberry_framework/optimizer/hints.py
[permissions]: ../../django_strawberry_framework/utils/permissions.py
[plans]: ../../django_strawberry_framework/optimizer/plans.py
[relations]: ../../django_strawberry_framework/utils/relations.py
[resolvers]: ../../django_strawberry_framework/types/resolvers.py
[single-parent-fetch]: ../../django_strawberry_framework/optimizer/single_parent_fetch.py
[walker]: ../../django_strawberry_framework/optimizer/walker.py
[write-transaction]: ../../django_strawberry_framework/utils/write_transaction.py

<!-- tests/ -->
[test-init]: ../../tests/base/test_init.py
[test-multi-db]: ../../tests/optimizer/test_multi_db.py
[test-plans]: ../../tests/optimizer/test_plans.py
[test-resolvers]: ../../tests/types/test_resolvers.py
[test-walker]: ../../tests/optimizer/test_walker.py
[tests-optimizer-dir]: ../../tests/optimizer/

<!-- examples/ -->
[db-shard-b.sqlite3]: ../../examples/fakeshop/db_shard_b.sqlite3
[models]: ../../examples/fakeshop/apps/library/models.py
[products-schema]: ../../examples/fakeshop/apps/products/schema.py
[schema]: ../../examples/fakeshop/apps/library/schema.py
[seed-shards]: ../../examples/fakeshop/apps/products/management/commands/seed_shards.py
[services]: ../../examples/fakeshop/apps/products/services.py
[settings]: ../../examples/fakeshop/config/settings.py
[test-query-conftest]: ../../examples/fakeshop/test_query/conftest.py
[test-query-test-multi-db]: ../../examples/fakeshop/test_query/test_multi_db.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
