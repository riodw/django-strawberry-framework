# Spec: Multi-database cooperation contract

Target release: `0.0.7` (per the [`KANBAN.md`][kanban] card `DONE-023-0.0.7`).
Status: shipped (`0.0.7`). Each Decision's justification and rejected alternatives live in [`spec-023-multi_db-0_0_7-rationale.md`][spec-023-rationale].
Owner: package maintainer.
Predecessors: [`docs/GLOSSARY.md`][glossary] (entries [`Multi-database cooperation`][glossary-multi-database-cooperation], [`DjangoOptimizerExtension`][glossary-djangooptimizerextension], [`get_queryset` visibility hook][glossary-get-queryset-visibility-hook], [`Strictness mode`][glossary-strictness-mode], [Queryset diffing][glossary-queryset-diffing], [FK-id elision][glossary-fk-id-elision]); [`KANBAN.md`][kanban] card `DONE-023-0.0.7`; joint-cut policy spec [`docs/SPECS/spec-020-list_field-0_0_7.md`][spec-020] ([Decision 10][spec-020-decision-10--joint-007-cut], reused in [Decision 9](#decision-9--joint-007-cut) here); shipped sibling [`docs/SPECS/spec-022-export_schema-0_0_7.md`][spec-022] (the bundle this card sits inside).

## Key glossary references

Skim these [`docs/GLOSSARY.md`][glossary] entries first — they anchor the vocabulary used throughout the spec:

- [`Multi-database cooperation`][glossary-multi-database-cooperation] — the shipped four-axis statement of this contract; [Decision 3](#decision-3--the-cooperation-contract-four-axes) is its long form.
- [`DjangoOptimizerExtension`][glossary-djangooptimizerextension] — the optimizer this contract proves cooperates with Django's routing. The extension does not query the router itself; cooperation rides on the queryset's `_db` attribute being preserved through plan application, `Prefetch` chains, and FK-id elision stubs.
- [`get_queryset` visibility hook][glossary-get-queryset-visibility-hook] — the consumer-owned visibility filter. On a generated `Prefetch` child the optimizer builds the child unrouted and runs the target type's hook on it; a hook that pins an alias there fails closed with `ConfigurationError`, and the unrouted child follows the parent rows' connection at fetch time. On a root queryset the hook may narrow but cannot re-route an already-pinned resolution.
- [Queryset diffing][glossary-queryset-diffing] — the optimizer's cooperation rule that respects work the consumer already applied to the queryset (including `.using(alias)`); cited so the [Decision 3](#decision-3--the-cooperation-contract-four-axes) cooperation contract is grounded in shipped behavior, not new code.
- [Strictness mode][glossary-strictness-mode] — `off` / `warn` / `raise` for unplanned N+1 detection; strictness remains active for objects loaded from any database alias (the check is connection-agnostic; the error class and message are unchanged under `.using("shard_b")`), and Django — not the package — owns which alias a lazy load (if permitted) would actually use. [`Decision 3`](#decision-3--the-cooperation-contract-four-axes) axis 4 (verified against [`types/resolvers.py::_check_n1`][resolvers]).
- [FK-id elision][glossary-fk-id-elision] — the optimizer's `{ relation { id } }` shortcut that reads the FK column off the parent row and synthesizes a stub. The stub's `_state.db` is set via `router.db_for_read(...)` so subsequent attribute access (e.g. follow-up resolver hops) reads from the correct connection.
- [`DjangoType`][glossary-djangotype] — the consumer-facing type the optimizer plans for; the framing for every test fixture.
- [`finalize_django_types`][glossary-finalize-django-types] — the consumer-owned synchronization point; the multi-db tests finalize exactly like the other optimizer tests.
- [`ConfigurationError`][glossary-configurationerror] — this contract adds no raise of its own; routing conflicts the visibility boundary refuses surface as `ConfigurationError` ([Error shapes](#error-shapes)).

Project conventions to follow:

- [`AGENTS.md`][agents] — #"Test placement:" (package tests live under `tests/` with `__init__.py` shells in subdirectories like `tests/optimizer/`, example-project non-HTTP tests under `examples/fakeshop/tests/`, live HTTP tests under `examples/fakeshop/test_query/`, and no `__init__.py` in either fakeshop test tree); #"Test through real usage, prefer the example project" (a line reachable via a real GraphQL query against fakeshop is covered in `examples/fakeshop/test_query/`); #"Add a settings key only when the feature that needs it lands".
- [`CONTRIBUTING.md`][contributing] — 100% coverage target.
- [`docs/TREE.md`][tree] — tests mirror source one-to-one; `tests/optimizer/` is an established test package, so `tests/optimizer/test_multi_db.py` extends it in place.

## Slice checklist

Three slices, aligned with the [Implementation plan](#implementation-plan).

- [ ] Slice 1: Package-internal tests, split across two files per [Decision 5](#decision-5--package-internal-tests-use-a-fixture-router-not-fakeshop_sharded) — `tests/types/test_resolvers.py` holds the resolver-level FK-id-elision + strictness tests; `tests/optimizer/test_multi_db.py` holds the consumer-`OptimizerHint.prefetch(Prefetch(queryset=...using...))` round-trip at the optimizer-plan layer. Decision 3 axis 2 — `OptimizationPlan.apply` `_db` preservation — is verified by Slice 2's live HTTP test per `AGENTS.md` #"Test through real usage, prefer the example project", not by a separate package-internal assertion.
  - [ ] `tests/types/test_resolvers.py` carries **five** resolver-level tests (per [Test plan](#test-plan) — FK-id elision router call shape; router call passes `instance=parent_row`; router call passes `instance=None` when the parent lacks `_state`; null FK takes the early-return branch and does NOT call the router; strictness check is connection-agnostic for non-default `_state.db`). The strictness test lives here because `_check_n1` lives in `types/resolvers.py`. Single pytest item per test, no `pytest.mark.parametrize` fan-out.
  - [ ] `tests/optimizer/test_multi_db.py` carries **one** optimizer-plan-level test (per [Test plan](#test-plan) — consumer-provided `OptimizerHint.prefetch(Prefetch(queryset=…using…))` round-trips through plan construction with `_db` intact). Single pytest item. Total Slice 1 pytest items: six.
  - [ ] Only the four FK-id-elision tests mock the router: `monkeypatch.setattr(resolvers_module, "router", mock_router)` with `mock_router.db_for_read.return_value = "default"`, per [Decision 5](#decision-5--package-internal-tests-use-a-fixture-router-not-fakeshop_sharded). The strictness test and the optimizer-plan test never reach FK-id elision and carry no router mock. No second SQLite file exists at package-test time; cooperation is verified by spying on the router call shape.
  - [ ] Module and test docstrings match the existing style in `tests/optimizer/` and `tests/types/` (convention only: [`pyproject.toml`][pyproject] #"[tool.ruff.lint.per-file-ignores]" ignores `D` and `ANN` for `tests/**/*.py`).
  - [ ] No `# noqa` suppressions for any docstring or annotation rule.
- [ ] Slice 2: Fakeshop live coverage under `FAKESHOP_SHARDED=1`
  - [ ] `examples/fakeshop/test_query/test_multi_db.py` carries **two** live `/graphql/` HTTP tests from this contract against the sharded fakeshop layout (per [Test plan](#test-plan)). It is the tree's home for live multi-database coverage, so later contracts' alias pins sit beside these two.
  - [ ] The module gates on `FAKESHOP_SHARDED=1` by calling `pytest.skip("requires FAKESHOP_SHARDED=1 (the sharded DATABASES layout)", allow_module_level=True)` at module top after an `os.environ.get("FAKESHOP_SHARDED") != "1"` check (per [Decision 6](#decision-6--live-coverage-under-fakeshop_sharded1)), not `pytest.mark.skipif`.
  - [ ] Each test is decorated with `@pytest.mark.django_db(databases=["default", "shard_b"])` (pytest-django blocks access to a database a test does not declare).
  - [ ] Each test seeds a full `Branch → Shelf → Book` chain on the alias it reads (`Book.shelf` and `Shelf.branch` are both non-null FKs per [`examples/fakeshop/apps/library/models.py::Shelf`][models] and [`examples/fakeshop/apps/library/models.py::Book`][models]) through the module's `_seed_book_chain(alias, *, title)` helper.
  - [ ] Live `/graphql/` HTTP exclusively per [Decision 6](#decision-6--live-coverage-under-fakeshop_sharded1) — no in-process `execute_sync(...)`. Each test depends on the `_build_test_schema` fixture, whose per-test `strawberry.Schema(...)` root resolver returns `models.Book.objects.using("shard_b").select_related("shelf__branch")`; the request runs under `override_settings(ROOT_URLCONF=__name__)` with `clear_url_caches()` on entry and in teardown, through `examples/fakeshop/graphql_client.py`'s `assert_graphql_success` (a `django.test.Client` POST to `/graphql/`). The fakeshop app schemas are not decorated with routing per [Decision 4](#decision-4--no-routing-decoration-on-fakeshop-schemas).
  - [ ] The reload contract comes from the shared `examples/fakeshop/test_query/conftest.py` autouse fixture (per [Decision 7](#decision-7--the-reload-fixture-comes-from-the-shared-test_query-conftest)); the module declares no reload fixture of its own.
  - [ ] Module + per-test docstrings match the fakeshop test-tree style (convention only — `examples/**/*.py` ignores `D` / `ANN` in the same [`pyproject.toml`][pyproject] table).
- [ ] Slice 3: Promotion + docs
  - [ ] [`Multi-database cooperation`][glossary-multi-database-cooperation] in [`docs/GLOSSARY.md`][glossary] reads `shipped (`0.0.7`)` in its Index row (`docs/GLOSSARY.md #"| [Multi-database cooperation](#multi-database-cooperation) |"`) and its entry body (`docs/GLOSSARY.md #"## Multi-database cooperation"`) states the four axes.
  - [ ] [`docs/README.md`][readme]'s `### Sharded mode (multi-DB)` section describes the additive `DATABASES` layout (`default → db.sqlite3` in both modes; `FAKESHOP_SHARDED=1` ADDS `shard_b → db_shard_b.sqlite3`) and links the GLOSSARY entry.
  - [ ] [`KANBAN.md`][kanban] carries the card as `DONE-023-0.0.7` with `Status: Done` and a `Spec:` row resolving to [`docs/SPECS/spec-023-multi_db-0_0_7.md`][spec-023].
  - [ ] [`CHANGELOG.md`][changelog]'s single `[0.0.7]` `### Added` subsection carries the `Multi-database cooperation` bullet ([Decision 9](#decision-9--joint-007-cut)).
  - [ ] [`README.md`][root-readme] and [`GOAL.md`][goal] carry no multi-database text; [`TODAY.md`][today]'s capability list links the GLOSSARY entry rather than restating the contract (per [Decision 8](#decision-8--no-readme--goal--today-edits)).
  - [ ] No version bump in this card ([Decision 9](#decision-9--joint-007-cut)).
  - [ ] Zero new public exports — `__all__` carries no multi-database symbol.
  - [ ] Final gates:
    - [ ] `uv run ruff check --fix .` passes.
    - [ ] `uv run ruff format .` passes.
    - [ ] `uv run pytest` passes; coverage enforcement is CI's `pyproject.toml [tool.coverage.report] fail_under = 100`.

## Problem statement

`django-strawberry-framework` cooperates with Django's multi-database machinery in source: [`django_strawberry_framework/types/resolvers.py::_build_fk_id_stub`][resolvers] sets `state.db = router.db_for_read(field_meta.related_model, instance=instance)` on FK-id elision stubs, the optimizer's queryset diffing rule ([`Queryset diffing`][glossary-queryset-diffing]) preserves whatever explicit `.using(alias)` the consumer applied to the root queryset, and a generated `Prefetch` child is built unrouted at plan-construction time and routed alias-late, at fetch time, against the parent rows in hand. The fakeshop example ships a working additive two-alias layout: `examples/fakeshop/config/settings.py` keeps `default` → `db.sqlite3` in both single-DB and sharded modes, and `FAKESHOP_SHARDED=1` ADDS `shard_b` → `db_shard_b.sqlite3`; [`examples/fakeshop/apps/products/management/commands/seed_shards.py`][seed-shards] materializes the secondary shard through [`examples/fakeshop/apps/products/services.py::seed_data`][services]'s `Model.objects.using(db_alias)` calls. The committed `examples/fakeshop/db_shard_b.sqlite3` fixture ships with `seed_shards(count=1)` applied so sharded mode works out of the box.

Without a pinned contract that behavior is implicit. A migrant from `graphene-django` or `strawberry-graphql-django` asking "does this package work under `DATABASE_ROUTERS` / `.using()` / sharded reads?" would have to read the source, and a future optimizer refactor that re-fetched the queryset via `Model.objects.all()` would silently lose the consumer's `.using("shard_b")` with no test noticing. This spec states the contract, the tests pin it, and the GLOSSARY entry publishes it.

Both reference packages take different stances:

- `strawberry-django` does not document multi-db behavior. Its `optimizer.py` (verified at `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/optimizer.py`) does not call `router.db_for_*` anywhere; cooperation rides entirely on the queryset's `_db` attribute.
- `graphene-django` does not document multi-db either; its filter / connection layer is database-agnostic by accident, not by design.

This is a tests + docs contract with **zero production code change**. Its discipline is **what the contract covers and what it does NOT**: routing through Django's `router.db_for_*` API and queryset `_db` propagation are in scope; first-class sharding-aware planning (cross-shard joins, automatic shard selection based on FK, multi-shard aggregates, `Meta.preferred_database`) is deferred to the [`BACKLOG.md`][backlog] `sharding_aware_optimizer` entry.

## Current state

- [`django_strawberry_framework/types/resolvers.py::_build_fk_id_stub`][resolvers] sets `_state.db = router.db_for_read(field_meta.related_model, instance=instance)`, where `instance` is `root if getattr(root, "_state", None) is not None else None`, so consumer routers can consult the parent row as an `instance=` hint; the stub's `_state.db` is whatever the router returns from that call. This is the **read**-path router consultation the four axes cover, and the only one in the optimizer / type layer. The package's other router consultations belong to surfaces outside these axes: the permission layer collects candidate read aliases in [`utils/permissions.py::resolve_auth_aliases`][permissions], a read surface's seal resolves an unrouted source's effective alias in [`utils/querysets.py::_snapshot_routing_intent`][querysets], and the write pipeline resolves the write alias in [`utils/write_transaction.py::resolve_write_alias`][write-transaction] and again with an instance hint in [`utils/write_transaction.py::check_instance_write_alias`][write-transaction].
- [`django_strawberry_framework/optimizer/extension.py`][extension] and [`walker.py`][walker] do NOT call `router.db_for_*` anywhere; cooperation rides entirely on the queryset's `_db` attribute being preserved through plan application. The [`Queryset diffing`][glossary-queryset-diffing] rule means: if the consumer's resolver returns `Item.objects.using("shard_b").select_related("category")`, the optimizer adds `prefetch_related("entries")` on top via `qs.prefetch_related(...)` (which preserves `_db`), and the consumer's `_db` survives.
- [`examples/fakeshop/config/settings.py`][settings] ships an additive `DATABASES` layout: a `default` entry is declared unconditionally, and `FAKESHOP_SHARDED=1` ADDS `shard_b → db_shard_b.sqlite3` on top of it. Both modes point `default` at the same SQLite file, so a single dev workflow (`manage.py seed_data`, etc.) populates the default alias regardless of mode. Two env vars re-point `default` without disturbing that additivity: `DJANGO_STRAWBERRY_KANBAN_DB` swaps its SQLite file (used by the doc-render tooling against a migrated copy of the board DB), and `FAKESHOP_PG_DSN` swaps the whole `default` entry to Postgres for the vendor tier. The Postgres tier and `FAKESHOP_SHARDED` are mutually exclusive.
- [`examples/fakeshop/apps/products/services.py::seed_data`][services] seeds through `Model.objects.using(db_alias)`, so rows land on the shard the alias names. The read-time cooperation through `/graphql/` is exercised by the live tests in `examples/fakeshop/test_query/test_multi_db.py`.
- [`examples/fakeshop/test_query/conftest.py::_reload_project_schema_for_acceptance_tests`][test-query-conftest] is the tree-wide module-scoped autouse reload fixture; every live `/graphql/` module depends on it (per [Decision 7](#decision-7--the-reload-fixture-comes-from-the-shared-test_query-conftest)) because package tests clear the registry.
- No `DATABASE_ROUTERS` are registered in `examples/fakeshop/config/settings.py`. All routing in fakeshop is explicit via `.using(alias)`; the cooperation contract works the same way against an implicit router and an explicit `.using()`, and the fakeshop live tests use `.using()` because that is what fakeshop's seed pipeline does.
- [`docs/GLOSSARY.md`][glossary] `docs/GLOSSARY.md #"## Multi-database cooperation"` is the shipped four-axis statement of the contract; this spec's [Decision 3](#decision-3--the-cooperation-contract-four-axes) is its long form.
- [`tests/optimizer/`][tests-optimizer-dir] is an established test package (it carries `__init__.py` and the shipped optimizer-test modules), so `test_multi_db.py` extends it in place.
- The release is single-sourced in [`django_strawberry_framework/__init__.py`][django-strawberry-framework-init] `django_strawberry_framework/__init__.py #"__version__ ="` (hatchling derives the packaging metadata from it) and pinned by [`tests/base/test_init.py::test_version`][test-init]. This contract touches neither: the `[0.0.7]` heading in [`CHANGELOG.md`][changelog] is shared by every card in the joint cut — [`DjangoListField`][glossary-djangolistfield] (`DONE-020-0.0.7`), [`Django AppConfig`][glossary-django-appconfig] (`DONE-021-0.0.7`), [`Schema export management command`][glossary-schema-export-management-command] (`DONE-022-0.0.7`) and the rest — per [Decision 9](#decision-9--joint-007-cut).

## Goals

1. [`docs/SPECS/spec-023-multi_db-0_0_7.md`][spec-023] (this document) states the cooperation contract on four narrowed axes: (a) `router.db_for_read` on FK-id elision stubs, with the parent row forwarded as the `instance=` hint when present and `None` otherwise; (b) explicit `.using(alias)` `_db` preservation through [`OptimizationPlan.apply`][plans] for root querysets; (c) consumer-provided [`OptimizerHint.prefetch(Prefetch(queryset=...))`][glossary-optimizerhint] alias round-trip with the inner queryset's `_db` intact (a generated `Prefetch` child queryset does not carry the root alias in the plan; it is routed alias-late at fetch time — that boundary is explicit per [Decision 3](#decision-3--the-cooperation-contract-four-axes), and first-class shard-aware *planning* stays deferred to the [`BACKLOG.md`][backlog] `sharding_aware_optimizer` entry); (d) strictness-mode N+1 detection remains active for rows loaded from non-default database aliases — the check is connection-agnostic and surfaces the same `OptimizerError` shape regardless of alias. None of the four axes claims that strictness routes connections or that a plan bakes an alias into a generated child queryset.
2. **Six package-internal tests** pinned in [Test plan](#test-plan). Resolver-level tests in `tests/types/test_resolvers.py` (five): (a) FK-id elision stub `_state.db` is set via `router.db_for_read`, (b) the router call's `instance=` argument is the parent row when the parent has a `_state` attribute, (c) the router call's `instance=` argument is `None` when the parent row lacks `_state`, (d) a null FK takes the `return None` early-exit branch and does NOT call the router, (e) the strictness-mode N+1 check is connection-agnostic — it accepts rows with `_state.db != "default"` unchanged and surfaces the same `OptimizerError` shape regardless of alias. Optimizer-plan-level test in `tests/optimizer/test_multi_db.py` (one): (f) consumer-provided [`OptimizerHint.prefetch(Prefetch(queryset=Model.objects.using("shard_b").all()))`][glossary-optimizerhint] round-trips through plan construction with the consumer's `_db` intact on the inner queryset. Decision 3 axis 2 ([`OptimizationPlan.apply(qs)`][plans] preserves `qs._db` for an explicit `.using()` parent) is verified by the Slice 2 live `/graphql/` HTTP test, per [`AGENTS.md`][agents] #"Test through real usage, prefer the example project".
3. **Two** live `/graphql/` HTTP tests in `examples/fakeshop/test_query/test_multi_db.py` against the sharded fakeshop layout — both decorated with `@pytest.mark.django_db(databases=["default", "shard_b"])`, both seeding a full `Branch → Shelf → Book` chain on the queried alias, both reaching `/graphql/` through a `django.test.Client` POST against a temp URLConf under `override_settings(ROOT_URLCONF=...)`: (a) seeding rows on `shard_b` and reading them through `/graphql/` via a `.using("shard_b")` root resolver returns the seeded rows, (b) cross-shard reads return only rows from the queried alias (a chain seeded on `default` is not visible through a `using("shard_b")` resolver).
4. [`Multi-database cooperation`][glossary-multi-database-cooperation] in [`docs/GLOSSARY.md`][glossary] is `shipped (0.0.7)` and states the four axes.
5. [`docs/README.md`][readme]'s `### Sharded mode (multi-DB)` section links the GLOSSARY entry, so a consumer reading the example onboarding sees the package's commitment.
6. No `DJANGO_STRAWBERRY_FRAMEWORK.*` settings key, per [`AGENTS.md`][agents] #"Add a settings key only when the feature that needs it lands".
7. `__all__` carries no multi-database symbol — the cooperation contract is plumbing the package already honors.

## Non-goals

- First-class sharding-aware planning — cross-shard joins, automatic shard selection based on FK, multi-shard aggregates, `Meta.preferred_database`. Tracked in the [`BACKLOG.md`][backlog] `sharding_aware_optimizer` entry (post-`1.0.0` differentiation).
- A package-level `DATABASE_ROUTERS` opinion. Routing policy is consumer-shaped; the package cooperates with whatever router the consumer registers and does not opine on which model lives on which shard.
- New consumer-facing API. No new symbol, `Meta.*` key, settings key, or exception class. The contract is a behavior surface the package already exhibits.
- Production code changes. The cooperation exists at [`types/resolvers.py::_build_fk_id_stub`][resolvers] and in the optimizer's queryset handling; this contract pins it with tests + docs (per [Decision 2](#decision-2--no-production-code-change)).
- A `manage.py` helper for shard introspection or cross-shard queries. The example project's `seed_shards` command lives in `examples/fakeshop/`, not in the package.
- Settings-backed default shard alias. [`AGENTS.md`][agents] #"Add a settings key only when the feature that needs it lands" forbids preemptive settings.
- Auto-calling [`finalize_django_types()`][glossary-finalize-django-types] per database alias. Finalization is global to the process and identical regardless of routing.

## Borrowing posture

Multi-database cooperation is a Django capability neither reference package documents as a contract. This card has no upstream surface to borrow.

### From `strawberry-django` — no precedent to borrow

Local source path: `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/optimizer.py`. Verified by inspection: the file does not call `router.db_for_*` anywhere; multi-db cooperation rides entirely on the queryset's `_db` attribute (the same shape this package ships). There is no `docs/multi-db.md` in the upstream's repo; no `tests/test_multi_db.py`; no documented stance on what consumers can rely on under `.using()`.

The shape we ship is functionally equivalent to the upstream's — a queryset's `_db` survives `select_related` / `prefetch_related` / `Prefetch` chains because Django's queryset API preserves it — but we additionally call `router.db_for_read(...)` on FK-id elision stubs (the [`types/resolvers.py::_build_fk_id_stub`][resolvers] path), which the upstream does not. The call is necessary because an FK-id elision stub is a freshly-constructed model instance with no `_db` from a queryset to inherit; without the router lookup the stub's `_state.db` stays `None`. The upstream's optimizer does not implement FK-id elision, so the cooperation gap doesn't arise there.

### From `graphene-django` — no precedent to borrow

Local source path: `/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/`. Verified: no `router.db_for_*` calls anywhere in the package source. The package is database-agnostic by accident — `RelayConnectionField` and `DjangoListField` resolvers return whatever queryset the consumer hands them, and queryset `.using()` propagates through Django's machinery without the package noticing.

### Explicitly do not borrow

- A `DATABASE_ROUTERS` reference router class in the package. Routing policy is consumer-shaped; Django ships no default router class either.
- A `Meta.preferred_database` declarative shortcut. Tracked in the [`BACKLOG.md`][backlog] `sharding_aware_optimizer` entry; out of scope here.
- Cross-shard join detection / rejection. The optimizer can't see across shards (each shard has its own connection); a consumer who writes `Item.objects.using("shard_a").filter(category__in=Category.objects.using("shard_b"))` gets whatever Django's queryset compiler does. The [`BACKLOG.md`][backlog] `sharding_aware_optimizer` entry covers it.

## User-facing API

The contract adds **no new symbols**. It is documented in [`docs/GLOSSARY.md#multi-database-cooperation`][glossary-multi-database-cooperation] and pinned with tests. No `__all__` change. No new `Meta.*` key. No new exception class.

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
    @strawberry.field(graphql_type=list[BookType])
    def books_on_shard_b(self, info) -> QuerySet[models.Book]:
        return models.Book.objects.using("shard_b").select_related("shelf")
```

The package's contract:

- The optimizer keeps a consumer `select_related` JOIN only on paths its plan does not prefetch (per [`Queryset diffing`][glossary-queryset-diffing]): when the selection reads `shelf` and the shelf target type declares a custom `get_queryset`, the plan's `Prefetch` replaces the consumer's `select_related("shelf")`, since a JOIN left on that path would cache the row the hook excludes. The optimizer adds its own optimizations on top via `qs.only(...)` / `qs.select_related(...)` / `qs.prefetch_related(...)` — each of which preserves the queryset's `_db` for explicit-`.using()` querysets ([`plans.py::OptimizationPlan.apply`][plans] round-trips `_db` unchanged).
- FK-id elisions on forward relations route through `router.db_for_read(<related_model>, instance=<parent_row>)` (when the parent has a `_state` attribute) or `instance=None` (when it does not); the elision stub's `_state.db` is whatever the router returns for that call. The package forwards the parent row as the `instance=` hint so consumer-defined routers can consult the parent's routing context; what the router returns is consumer-shaped.
- Strictness-mode N+1 detection ([`_check_n1`][resolvers]) remains active for rows loaded from any database alias. The check inspects the relation caches (`__dict__`, `_state.fields_cache`, `_prefetched_objects_cache`), the planned-resolver set, and the strictness mode — it does NOT inspect `root._state.db` or `queryset._db`, so the package does not re-route strictness; Django owns which alias any permitted lazy load would actually use. The error class (`OptimizerError`) and message (`"Unplanned N+1: <field>"`) are unchanged under `.using("shard_b")`.
- The [`get_queryset` visibility hook][glossary-get-queryset-visibility-hook] cooperates with routing on the **root** queryset: a hook that returns `queryset.filter(...)` preserves whatever `_db` the inbound queryset carried, and that `_db` survives plan application; a hook that re-routes an already-pinned resolution fails closed. On a single related object the hook is re-applied on the related row's own connection: [`types/resolvers.py::_visible_related_object`][resolvers] reads `related._state.db` and pins the visibility queryset to it, so the hook never evaluates a `shard_b` row's visibility against `default`. **Generated `Prefetch` child querysets do NOT inherit the root queryset's `_db` at plan-construction time** — [`walker.py::_build_child_queryset`][walker] seeds from the related model's `_default_manager.all()` and, when the target type declares a custom `get_queryset`, runs it under a seal that requires the child to stay unrouted, so a hook that pins an alias on a generated child fails closed. Routing for a generated child is **alias-late**: it is decided at fetch time, against the parent rows actually in hand. Django's own prefetch machinery routes with the parent instances' alias, and where the package builds a child queryset itself it pins that alias explicitly — [`optimizer/single_parent_fetch.py #"child_qs = spec.pristine_child_queryset.using(queryset.db)"`][single-parent-fetch] on the degenerate single-parent path, and [`filters/sets.py::FilterSet._branch_visibility_seed`][filters-sets] so a related filter's child visibility hook, for a nested branch or a branch a flat leaf walks, sees the same database as the parent request. Consumers who need a specific alias fixed in the plan pass a `Prefetch(queryset=Model.objects.using("shard_b"))` via [`OptimizerHint.prefetch(...)`][glossary-optimizerhint]; that consumer-provided `Prefetch` round-trips through plan construction with its own `_db` intact.

### Default usage — `DATABASE_ROUTERS` and implicit `db_for_read`

```python path=null start=null
# In settings.py
DATABASE_ROUTERS = ["myapp.routers.ShardRouter"]

# Consumer schema — no explicit .using() needed
@strawberry.type
class Query:
    @strawberry.field(graphql_type=list[BookType])
    def all_books(self, info) -> QuerySet[models.Book]:
        return models.Book.objects.all()  # router picks the connection at evaluation time
```

The package's contract under this shape:

- **Implicit-router root queryset:** `Model.objects.all()` carries `_db is None` until evaluation. The optimizer's `select_related` / `prefetch_related` / `only` additions are `_db`-neutral (they don't force a connection); Django routes at evaluation time via the registered `DATABASE_ROUTERS`. The optimizer does not pre-route on the consumer's behalf. (A read surface that hands its source to a consumer override resolves the source's effective alias through the router first — [`utils/querysets.py::_snapshot_routing_intent`][querysets] — and pins the sealed result to it, so the override cannot move the read to another connection.)
- **FK-id elision stubs:** still route through `router.db_for_read(<related_model>, instance=<parent_row_or_None>)` because the stubs are freshly-constructed model instances that don't inherit a queryset alias — the router lookup is the only way to give them a stable `_state.db`.
- **Strictness and `get_queryset` cooperation:** same as the explicit-`.using()` case.

The difference between explicit `.using(alias)` and implicit `DATABASE_ROUTERS`: explicit pins `_db` on the queryset before the optimizer ever sees it (and the package preserves that `_db` through plan application); implicit leaves `_db` unset and lets Django route at evaluation. The optimizer's behavior in both shapes is consistent — preserve what's there, don't force what isn't, and consult the router only on FK-id elision stubs where there's no queryset alias to inherit.

### Error shapes

This contract adds no error shape. The package does not raise on cross-shard queries (Django's own error surfaces unchanged) or on unrouted querysets (the router, else `default`, applies).

Routing conflicts the visibility boundary refuses fail closed with `ConfigurationError` before any row is read: a `get_queryset` hook that re-routes an already-pinned resolution, or a hook on a generated `Prefetch` child that pins any alias (`examples/fakeshop/test_query/test_multi_db.py::test_planned_prefetch_child_cannot_route_itself_to_the_other_shard`).

Strictness-mode N+1 detection ([`Strictness mode`][glossary-strictness-mode]) still fires under `using("shard_b")` if the relation is unplanned and would lazy-load. The error class (`OptimizerError`) and message (`"Unplanned N+1: <field>"`) are unchanged from the single-DB path.

## Architectural decisions

### Decision 1 — Spec filename and canonical naming

The spec carries the structured stem **`spec-023-multi_db-0_0_7`** and lives at **`docs/SPECS/spec-023-multi_db-0_0_7.md`** (this document); its terms CSV and rationale companion are `docs/SPECS/appx/spec-023-multi_db-0_0_7-terms.csv` and `docs/SPECS/appx/spec-023-multi_db-0_0_7-rationale.md`.

**Path lifecycle.** References point at whichever path the file actually has at the time the reference is written.

- An in-flight spec lives at `docs/spec-<NNN>-<topic>-<0_0_X>.md` and every reference to it uses that path; the [`KANBAN.md`][kanban] WIP card's `Spec:` row points there.
- The [`docs/SPECS/NEXT.md`][next] Step 8 archive pass moves the spec under `docs/SPECS/` and its `-terms.csv` / `-rationale.md` companions under `docs/SPECS/appx/`, rewriting every cross-reference in one sweep. After it runs, every reference uses the archived path — which is what this spec and the [`KANBAN.md`][kanban] Done card use.

Rationale companion: [Decision 1][rationale-d1].

### Decision 2 — No production code change

The contract ships **zero production code change**. The cooperation surface it pins (`router.db_for_read` at [`types/resolvers.py::_build_fk_id_stub`][resolvers]; queryset `_db` propagation through the optimizer; `get_queryset` downgrade routing; strictness mode under `.using()`) exists in source.

Rationale companion: [Decision 2][rationale-d2].

### Decision 3 — The cooperation contract: four axes

The contract covers exactly four cooperation axes, each with its source-of-truth location.

1. **`router.db_for_read` on FK-id elision stubs.** [`types/resolvers.py::_build_fk_id_stub`][resolvers]. When the optimizer elides a forward-relation `id`-only selection, the stub is built via `stub = field_meta.related_model(pk=related_id)` and then `state.db = router.db_for_read(field_meta.related_model, instance=instance)` runs, where `instance` is `root if getattr(root, "_state", None) is not None else None`. The package forwards the parent row as the `instance=` hint when it has one; consumer-defined routers decide what to return. Subsequent attribute reads on the stub hit whatever connection the router returned. Verified by the four FK-id-elision tests in `tests/types/test_resolvers.py` per [Test plan](#test-plan).
2. **Explicit `.using(alias)` `_db` preservation through `OptimizationPlan.apply`.** [`optimizer/walker.py`][walker], [`optimizer/plans.py::OptimizationPlan.apply`][plans]. When the consumer's resolver returns `Model.objects.using("shard_b").all()` (explicit `_db`), plan application calls `qs.only(...)` (the [`only()` projection][glossary-only-projection] path), `qs.select_related(...)`, and `qs.prefetch_related(...)` on that queryset — all of which preserve `_db` by Django queryset contract. `qs._db == "shard_b"` survives plan application unchanged. **Implicit-router querysets (no `.using(...)`) carry `_db is None` until evaluation**; the optimizer does not force a connection and lets Django route at evaluation time. Verified by Slice 2's live HTTP test — `test_using_shard_b_resolver_returns_rows_seeded_on_shard_b` in `examples/fakeshop/test_query/test_multi_db.py` — which queries a resolver returning `Book.objects.using("shard_b").select_related("shelf__branch")` and asserts the seeded `shard_b` titles appear in the JSON response. The assertion cannot pass unless `OptimizationPlan.apply` preserves `_db`: dropped, the queryset would route to `default` (empty of test seed) and the response would contain zero rows.
3. **Consumer-provided `Prefetch(queryset=...)` `_db` preservation.** [`OptimizerHint.prefetch(...)`][glossary-optimizerhint] accepts a consumer-built `Prefetch(lookup, queryset=Model.objects.using("shard_b").all())` and round-trips the inner queryset's `_db` through plan construction unchanged. **A generated `Prefetch` queryset does NOT carry the parent queryset's `_db` in the plan**: [`optimizer/walker.py::_build_child_queryset`][walker] seeds from the related model's `_default_manager.all()` and runs a custom target `get_queryset` under a seal that requires the child to leave unrouted. That is deliberate: a plan is cached and selection-shaped, so an alias baked into it at plan-construction time would freeze one resolver's connection choice into a cache entry another resolver reads, and it would have been resolved without the parent-instance hint the router needs. **Routing for a generated child is instead alias-LATE — decided at fetch time, against the parent rows in hand.** Django's own prefetch machinery routes with the parent instances' alias, and where the package builds a child queryset itself it pins that alias explicitly: [`optimizer/single_parent_fetch.py #"child_qs = spec.pristine_child_queryset.using(queryset.db)"`][single-parent-fetch] on the degenerate single-parent path, and [`filters/sets.py::FilterSet._branch_visibility_seed`][filters-sets] so a related filter's child `get_queryset` visibility hook, for a nested branch or a branch a flat leaf walks, runs against the same database as the parent request. The live module pins both halves: `test_planned_prefetch_child_follows_a_routed_parent_onto_its_shard` (an unrouted child follows a `shard_b` parent) and `test_planned_prefetch_child_cannot_route_itself_to_the_other_shard` (a child hook pinning `shard_b` under a `default` parent fails closed). Consumers who need a specific alias fixed in the plan use `OptimizerHint.prefetch(Prefetch(queryset=...))`; the package round-trips that intact. What stays outside the contract is shard-aware *planning* — an alias resolved at plan-construction time — tracked in the [`BACKLOG.md`][backlog] `sharding_aware_optimizer` entry and deferred per [Decision 2](#decision-2--no-production-code-change). Verified by Slice 1's optimizer-plan-level test (f) — `test_consumer_provided_prefetch_via_optimizer_hint_round_trips_using_alias` in `tests/optimizer/test_multi_db.py` — per [Test plan](#test-plan).
4. **Strictness mode is connection-agnostic.** [`types/resolvers.py::_check_n1`][resolvers]. The strictness check inspects the relation caches (`__dict__`, `_state.fields_cache`, `_prefetched_objects_cache`), the planned-resolver set, and the strictness mode — it does NOT inspect `root._state.db`, `queryset._db`, or `router.db_for_read(...)`. Strictness remains active for rows loaded from any database alias; the error class (`OptimizerError`) and message (`"Unplanned N+1: <field>"`) are unchanged under `.using("shard_b")`. The package does not re-route the check; Django owns which alias a permitted lazy load (under `strictness="off"` / `"warn"`) would actually use via the descriptor protocol and the parent row's `_state.db`. Verified by Slice 1's resolver-level test (e) — `test_strictness_check_is_connection_agnostic_under_non_default_alias` in `tests/types/test_resolvers.py` — per [Test plan](#test-plan). The test sets `root._state.db = "shard_b"` to prove the connection-agnostic shape, not to prove routing — with `strictness="raise"` the lazy load is intentionally prevented.

The four axes are stated at the plan and resolver seams where the package itself touches routing; the same alias-late principle governs every other place it builds a queryset from rows already in hand. The visibility re-check on a single related object is the clearest instance: when the relation's target type declares a custom `get_queryset`, [`types/resolvers.py::_visible_related_object`][resolvers] #"source = source.using(alias)" reads the related row's own `_state.db` and pins the visibility queryset to it, so a row loaded from `shard_b` has its visibility predicate evaluated on `shard_b` rather than on `default`. The alias comes from the row, never from a plan — which is why none of the four axes needs a clause about it.

Beyond the four axes and the alias-late principle they rest on, the following are **out of scope for the contract**:

- Cross-shard joins. The optimizer cannot plan them; the package does not improve on Django's behavior.
- Multi-shard aggregates. The optimizer aggregates against one queryset at a time, on its alias; cross-shard aggregation requires consumer-side logic.
- Routing policy. Consumer-shaped.
- `default_database` / preferred-shard selection. Consumer-shaped.

Rationale companion: [Decision 3][rationale-d3].

### Decision 4 — No routing decoration on fakeshop schemas

The fakeshop schemas at [`examples/fakeshop/apps/library/schema.py`][schema] and [`examples/fakeshop/apps/products/schema.py`][products-schema] carry no shard-pinned read resolvers. The live tests exercise routing through per-test schema fixtures (an inline `@strawberry.type` Query class declared inside the test module), not through the example app schemas.

Rationale companion: [Decision 4][rationale-d4].

### Decision 5 — Package-internal tests use a fixture router, not `FAKESHOP_SHARDED`

Package-internal tests do NOT depend on `FAKESHOP_SHARDED=1` or on the existence of `db_shard_b.sqlite3`. The two files cover:

- **`tests/types/test_resolvers.py` (resolver-level)** — the four FK-id-elision tests (stub `_state.db` shape, `instance=parent_row`, `instance=None`, null-FK early return) AND the strictness connection-agnostic-shape test. The four FK-id tests mock the resolvers module's `router`; the strictness test does NOT need the router mock — it asserts on `_check_n1`'s connection-agnostic behavior and never invokes the elision path.
- **`tests/optimizer/test_multi_db.py` (optimizer-plan-level)** — one consumer-`OptimizerHint.prefetch(Prefetch(queryset=...using...))` round-trip test. Does not exercise FK-id elision, so does not need a router mock; asserts directly on the queryset embedded in the consumer-provided `Prefetch` object after plan application. Decision 3 axis 2 (`OptimizationPlan.apply` `_db` preservation) is verified by Slice 2's live HTTP test.

Mock target: `monkeypatch.setattr(django_strawberry_framework.types.resolvers, "router", mock_router)` with `mock_router.db_for_read.return_value = "default"`. It rebinds the module-local name bound by `from django.db import models, router` at the top of `types/resolvers.py`, so the shared `django.db.router` singleton is untouched and `monkeypatch` restores the name at teardown.

Rationale companion: [Decision 5][rationale-d5].

### Decision 6 — Live coverage under `FAKESHOP_SHARDED=1`

`examples/fakeshop/test_query/test_multi_db.py` skips the entire module at collection time when `os.environ.get("FAKESHOP_SHARDED") != "1"` via `pytest.skip(reason, allow_module_level=True)`, NOT `pytest.mark.skipif`.

Justification:

- `config.settings` (layered under pytest by `config.test_settings`) decides `DATABASES` at module-import time, based on `os.environ.get("FAKESHOP_SHARDED")`. Querying `using("shard_b")` in single-DB mode would raise `ConnectionDoesNotExist` because `shard_b` is not registered in `DATABASES`. The `pytest.skip(allow_module_level=True)` shape skips before any import below it runs, so the model imports happen only when the env var is set.
- `pytest.mark.skipif(os.environ.get("FAKESHOP_SHARDED") != "1", ...)` would not work for the same reason: the test module's imports run before pytest evaluates the mark.
- The pattern is the tree's shared autouse reload fixture (per [Decision 7](#decision-7--the-reload-fixture-comes-from-the-shared-test_query-conftest)) with an additional early-module-skip guard on top.

Pinned shape (test-module header — a single `import pytest` placed before the skip block; every other import sits below it):

```python path=null start=null
import os

import pytest

if os.environ.get("FAKESHOP_SHARDED") != "1":
    pytest.skip(
        "requires FAKESHOP_SHARDED=1 (the sharded DATABASES layout)",
        allow_module_level=True,
    )

# Below this line, FAKESHOP_SHARDED=1 is set and ``shard_b`` is in DATABASES.
import strawberry
from apps.library import models
...
```

**Live `/graphql/` HTTP exclusively, with the schema built AFTER the autouse reload fixture runs.** A static module-level schema is incompatible with [Decision 7](#decision-7--the-reload-fixture-comes-from-the-shared-test_query-conftest)'s reload fixture; the per-test holder pattern below builds the schema against the freshly-reloaded `DjangoType` classes. `BookType` is imported inside the fixture body, never at module top, which would capture a stale class object from before the reload.

**The holder-pattern URLConf:** the test module declares a module-level `_current = {"schema": None}` holder that the temp URLConf's view reads at request time. A per-test fixture (running after the autouse reload fixture) builds the schema against the freshly-reloaded `apps.library.schema.BookType` and stores it on `_current["schema"]`:

```python path=null start=null
# Module-level (after the skip block):
_current: dict[str, object | None] = {"schema": None}


def _graphql_view(request):
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
        @strawberry.field(graphql_type=list[BookType])
        def books_on_shard_b(self, info: Info) -> QuerySet[models.Book]:
            return models.Book.objects.using("shard_b").select_related("shelf__branch")

    optimizer = DjangoOptimizerExtension()
    _current["schema"] = strawberry.Schema(
        query=_MultiDbTestQuery,
        config=strawberry_config(),
        extensions=[lambda: optimizer],
    )
    yield
    _current["schema"] = None
```

**Each test:**

1. Declares `@pytest.mark.django_db(databases=["default", "shard_b"])` so `pytest-django` permits access to `shard_b`.
2. Declares the `_build_test_schema` fixture so the per-test schema is rebuilt after the autouse reload.
3. Seeds rows via `_seed_book_chain(alias, title=...)` (full `Branch → Shelf → Book` chain).
4. Wraps the request in `with override_settings(ROOT_URLCONF=__name__):`, calling `clear_url_caches()` immediately after entering the override context AND again in a `finally` block — `__name__` resolves to the test module's dotted path at runtime, so Django re-resolves `/graphql/` against the temp URLConf.
5. Sends the GraphQL request through `examples/fakeshop/graphql_client.py`'s `assert_graphql_success(query, client=Client())` (a `django.test.Client` POST to `/graphql/` that asserts HTTP 200 and no GraphQL errors) and asserts on the returned `data`.

The in-process `execute_sync(...)` path is NOT acceptable here — it skips URL routing, the view, and the Django request pipeline that the live HTTP rule in [`AGENTS.md`][agents] #"Test through real usage, prefer the example project" names as the right tier when the surface is reachable from a real query.

Rationale companion — this Decision's rejected alternatives: [Decision 6][rationale-d6].

### Decision 7 — The reload fixture comes from the shared `test_query` conftest

`examples/fakeshop/test_query/test_multi_db.py` does not declare its own registry-reload fixture. It depends on the autouse `_reload_project_schema_for_acceptance_tests` at [`examples/fakeshop/test_query/conftest.py::_reload_project_schema_for_acceptance_tests`][test-query-conftest], which rebuilds the whole project schema once per module — the same fixture every other module in the tree uses. Package tests clear the registry, so any live `/graphql/` module needs that rebuild before its first request; one shared definition keeps every module in the tree rebuilding the same way.

Rationale companion: [Decision 7][rationale-d7].

### Decision 8 — No README / GOAL / TODAY edits

The contract adds no root-doc surface. [`README.md`][root-readme] and [`GOAL.md`][goal] carry no multi-database text, and [`TODAY.md`][today]'s capability list links the GLOSSARY entry rather than restating the axes.

The one onboarding breadcrumb is the [`docs/README.md`][readme] `### Sharded mode (multi-DB)` forward-pointer — `docs/README.md`, the documentation index, not the root `README.md`.

Rationale companion: [Decision 8][rationale-d8].

### Decision 9 — Joint `0.0.7` cut

`0.0.7` shipped under the joint-cut policy from [`docs/SPECS/spec-020-list_field-0_0_7.md`][spec-020] [Decision 10][spec-020-decision-10--joint-007-cut]: every card in the bundle — this one among them — carries its `### Added` entry under the same `[0.0.7]` heading in [`CHANGELOG.md`][changelog], and the bundle was cut once as a whole. The version bump (the `__version__` literal in `django_strawberry_framework/__init__.py` and `tests/base/test_init.py`'s pinned assertion) belonged to whichever card shipped last in the bundle, NOT this card.

Rationale companion: [Decision 9][rationale-d9].

## Implementation plan

Three slices, aligned with the [Slice checklist](#slice-checklist).

| Slice | Files | Tests |
| --- | --- | --- |
| 1 — Package-internal tests | `tests/types/test_resolvers.py`, `tests/optimizer/test_multi_db.py` | 6 — five in `tests/types/test_resolvers.py` (FK-id elision router call shape; `instance=<parent_row>`; `instance=None` when parent lacks `_state`; null FK takes early-return and does NOT call the router; strictness check is connection-agnostic) plus one in `tests/optimizer/test_multi_db.py` (consumer-`OptimizerHint.prefetch(Prefetch(queryset=…))` round-trips with `_db`). Decision 3 axis 2 is verified by the Slice 2 live HTTP test. |
| 2 — Fakeshop live coverage | `examples/fakeshop/test_query/test_multi_db.py` | 2 (live `.using("shard_b")` round trip; shard isolation — chain on `default` not visible through `using("shard_b")` resolver). Live HTTP exclusively; `@pytest.mark.django_db(databases=["default", "shard_b"])` on each test; full `Branch → Shelf → Book` chain per alias. |
| 3 — Promotion + docs | [`docs/GLOSSARY.md`][glossary], [`docs/README.md`][readme], [`KANBAN.md`][kanban], [`CHANGELOG.md`][changelog] | 0 |

## Edge cases and constraints

- **`router.db_for_read` `instance=` argument can be `None`.** [`types/resolvers.py::_build_fk_id_stub`][resolvers]: `instance = root if getattr(root, "_state", None) is not None else None`. Django's `db_for_read(model, **hints)` accepts `instance=None`. With no router answering, Django's `ConnectionRouter` falls back to the `instance` hint's `_state.db` and then to `"default"`, so forwarding the parent row is what lands a stub on its parent's alias in a router-less project. Slice 1 test (c) pins the `None` branch with a synthetic `SimpleNamespace` parent that has no `_state` attribute.
- **FK-id elision has pre-router exits, and a nullable FK is one of them.** [`types/resolvers.py::_build_fk_id_stub`][resolvers] returns before ever consulting the router when `field_meta.attname` or `field_meta.related_model` is absent (`None`); when the FK column is deferred on `root` (the `_FK_ELISION_UNSAFE` sentinel, so the caller falls back loudly rather than issuing a silent per-row lazy load); when reading `attname` raises `AttributeError` (`None`); when `related_id is None` (`None`); and when constructing the stub raises (`_FK_ELISION_UNSAFE`). The `router.db_for_read` call runs only on the path past all of them, so a `None` FK never reaches the router. Slice 1 test (d) (`test_fk_id_elision_returns_none_for_null_fk_and_does_not_call_router`) pins the null-FK branch separately from the parent-lacks-`_state` branch covered by test (c); the two are different code paths.
- **Mocking `router` at the resolver-module level.** `django.db.router` is a module-level singleton; [`types/resolvers.py #"from django.db import models, router"`][resolvers] binds the local name `router` to it. Patching `db_for_read` on that singleton would reroute every caller in the process for the test's duration; rebinding the resolvers module's `router` is module-local and the pytest `monkeypatch` fixture handles teardown (per [Decision 5](#decision-5--package-internal-tests-use-a-fixture-router-not-fakeshop_sharded)).
- **`pytest.skip(allow_module_level=True)` runs before imports below it.** This is the load-bearing detail for [Decision 6](#decision-6--live-coverage-under-fakeshop_sharded1): the test file's `from apps.library import models` line below the skip block runs only when the skip didn't fire. Under single-DB mode, the import never runs; under `FAKESHOP_SHARDED=1`, the import runs against a `DATABASES` dict that has both `default` and `shard_b`.
- **Sharded-mode pytest collection.** Per `examples/fakeshop/config/settings.py`, `FAKESHOP_SHARDED=1` ADDS `shard_b → db_shard_b.sqlite3` to the existing `default → db.sqlite3` layout. Neither alias sets a `TEST` name, so Django runs each test database as in-memory SQLite; the committed `db.sqlite3` and `db_shard_b.sqlite3` fixture files are untouched by the test suite.
- **Coverage gate.** The 100% coverage gate is `pyproject.toml [tool.coverage.report] fail_under = 100`, enforced in CI. The sharded live tests skip under the default invocation and run under `FAKESHOP_SHARDED=1 uv run pytest`; the six package-internal tests run in every invocation.
- **Test-module docstring requirement.** [`pyproject.toml`][pyproject] #"[tool.ruff.lint.per-file-ignores]" covers `tests/**/*.py` and `examples/**/*.py` with `D` and `ANN` among the ignored rules; docstrings and annotations in tests are NOT gate-forced. They are added for convention-matching with the existing `tests/optimizer/test_*.py` and `tests/types/test_*.py` files, and no `# noqa` suppression for `D` or `ANN` is needed.
- **`tests/optimizer/test_extension.py` and `tests/optimizer/test_walker.py` cover non-routing optimizer behavior.** `tests/optimizer/test_multi_db.py` sits next to them with a focused scope (multi-db only).
- **Order independence of Slice 1 tests.** Each test uses pytest's `monkeypatch` fixture for any `router` mock so the patch is automatically removed at end of test. Tests can run in any collection order without leaking state.
- **Consumer-provided `Prefetch(queryset=...)` `_db` round-trip is a Django contract.** Django's `Prefetch(lookup, queryset=qs)` carries `qs._db` for the inner query, regardless of the parent queryset's `_db`. Slice 1's optimizer-plan-level test (f) — `test_consumer_provided_prefetch_via_optimizer_hint_round_trips_using_alias` in `tests/optimizer/test_multi_db.py` — introspects the post-plan `_prefetch_related_lookups` to assert the package round-trips that intact. **A generated child queryset does NOT carry the parent's `_db` in the plan** ([`walker.py::_build_child_queryset`][walker] seeds from the related model's `_default_manager.all()`, so the parent alias is intentionally not threaded through at plan-construction time; the alias is applied late, at fetch time, per [Decision 3](#decision-3--the-cooperation-contract-four-axes) axis 3). Consumers who need a specific alias on a child relation pass `OptimizerHint.prefetch(Prefetch(queryset=Model.objects.using(...)))` and that consumer-provided alias round-trips per the test above.
- **`OptimizationPlan.apply(qs)` is the unit of test for queryset alias preservation, NOT `plan_optimizations(...)`.** The live signature is [`optimizer/walker.py::plan_optimizations`][walker]`(selected_fields, model, info=None, *, runtime_prefixes=None, source_type=None)` — selections + model + optional GraphQL `info`, then keyword-only `runtime_prefixes` and `source_type`; there is no `parent_type` positional. The third positional binds to `info`, and the walker reads `info.path` (via `runtime_path_from_info`), so passing a class object there would crash at the first descent into the selection tree. The parent queryset is applied via [`plans.py::OptimizationPlan.apply`][plans]. Slice 1's optimizer-plan test (f) uses `plan_optimizations(selected_fields, Category, source_type=ParentType)` so the walker picks up the parent type's `Meta.optimizer_hints`. A regression where `OptimizationPlan.apply` drops `_db` makes the Slice 2 live test's seeded-titles assertion fail.
- **Optimizer plan cache key does NOT include the database alias.** Per the shipped [`Plan cache`][glossary-plan-cache] entry, cache keys include the operation AST, relevant variables, target model, root runtime path, and the resolver's origin Strawberry type ([`optimizer/extension.py::DjangoOptimizerExtension._build_cache_key`][extension]) — not the queryset's `_db`. Two resolvers on the same model targeting different shards share a cached plan; correct, because the plan is selection-shaped, not connection-shaped. **Type-scoped binding for consumer-provided `Prefetch(queryset=…)` aliases:** consumer-provided [`OptimizerHint.prefetch(Prefetch(queryset=…using…))`][glossary-optimizerhint] hints are bound to their `DjangoType` via [`Meta.optimizer_hints`][glossary-metaoptimizer-hints], and the cache key carries the resolver's origin type, so two resolvers that share a cached plan share the same types and therefore the same hint config — there is no per-resolver-call leak. The consumer's `_db` choice is a per-type decision rather than a per-call one.

## Test plan

Tests live across two trees, matching the rules in [`docs/TREE.md`][tree] and [`AGENTS.md`][agents]. Test-tree placement follows [Decision 5](#decision-5--package-internal-tests-use-a-fixture-router-not-fakeshop_sharded) and [Decision 6](#decision-6--live-coverage-under-fakeshop_sharded1). Slice 1 splits across two test files — resolver-level tests in `tests/types/test_resolvers.py` (the source-mirror partner of [`django_strawberry_framework/types/resolvers.py`][resolvers], where `_build_fk_id_stub` and `_check_n1` live); the optimizer-plan-level test in `tests/optimizer/test_multi_db.py`.

### `tests/types/test_resolvers.py` — five resolver-level tests

Package tests; system-under-test is `_build_fk_id_stub(...)` AND `_check_n1(...)` in [`django_strawberry_framework/types/resolvers.py`][resolvers]. **Five** tests; the strictness test lives here because `_check_n1` also lives in `types/resolvers.py`, per the [`docs/TREE.md`][tree] mirror rule. Single pytest item per test, no `pytest.mark.parametrize` fan-out.

**Mock contract** (the four FK-id-elision tests; the strictness test does NOT need it): `mock_router = Mock()`, `mock_router.db_for_read.return_value = "default"`, `monkeypatch.setattr(resolvers_module, "router", mock_router)`. The return value does not affect the assertion; the assertion is on the call shape.

**`FieldMeta` construction shape**: each FK-id-elision test constructs a `FieldMeta` directly (NOT via `FieldMeta.from_django_field`) — `FieldMeta(name="category", is_relation=True, related_model=Category, attname="category_id")` — because the test spies on `_build_fk_id_stub`'s router-call shape, not on the Django-field-introspection pipeline. Every other [`optimizer/field_meta.py`][field-meta] `FieldMeta` field has a default sufficient for this surface.

- `test_fk_id_elision_stub_sets_state_db_via_router_db_for_read` — exercises `_build_fk_id_stub` against an `Item(category_id=42)` parent; asserts the returned stub is a `Category` with `pk == 42` and `_state.db == <mock return value>`, and that `router.db_for_read` was called once. Pins [Decision 3](#decision-3--the-cooperation-contract-four-axes) axis 1.
- `test_fk_id_elision_router_call_passes_parent_row_as_instance` — exercises `_build_fk_id_stub` against a model-instance parent (which always has `_state`); asserts `router.db_for_read` was called with `(Category, instance=<parent_row>)`. Pins the parent-`instance=` forwarding contract — a regression switching the call to `instance=None` would silently break consumer routers that consult the parent row's `_state.db`.
- `test_fk_id_elision_router_call_passes_none_instance_when_parent_lacks_state` — exercises `_build_fk_id_stub` against a `types.SimpleNamespace(pk=1, category_id=42)` parent (no `_state` attribute); asserts the stub is built and `router.db_for_read` was called with `instance=None`. Pins the `getattr(root, "_state", None) is not None` fallback.
- `test_fk_id_elision_returns_none_for_null_fk_and_does_not_call_router` — exercises `_build_fk_id_stub` against a parent whose FK `attname` reads `None`; asserts `_build_fk_id_stub(...)` returns `None` AND `router.db_for_read` was NOT called. Pins the null-FK early-return branch separately from the parent-lacks-`_state` branch — the two are different code paths and a regression in either is a different bug.
- `test_strictness_check_is_connection_agnostic_under_non_default_alias` — builds a `SimpleNamespace` root whose `_state` carries `db="shard_b"` and an empty `fields_cache`, so `shelf` is in neither `root.__dict__` nor `root._state.fields_cache` and [`types/resolvers.py::_will_lazy_load_single`][resolvers] reports the relation unloaded; calls `_check_n1(info, root, "shelf", _ParentType, kind="forward_single")` (`"forward_single"` is the [`RelationKind`][relations] for a forward FK per [`utils/relations.py #"RelationKind: TypeAlias"`][relations]; `"many_to_one"` is NOT a valid `RelationKind`) with `info.context` carrying `DST_OPTIMIZER_STRICTNESS: "raise"` and a non-empty `DST_OPTIMIZER_PLANNED` set that does NOT include this resolver's key; asserts `OptimizerError` matching `"Unplanned N+1: shelf"` is raised. Does NOT set `root._prefetched_objects_cache` — the single-valued detector branch does not consult it. Does NOT mock the router. Pins [Decision 3](#decision-3--the-cooperation-contract-four-axes) axis 4 — the check accepts non-default-aliased rows unchanged and surfaces the same error shape; the assertion is about the connection-agnostic shape, NOT about which alias a (prevented) lazy load would hit.

### `tests/optimizer/test_multi_db.py` — one optimizer-plan-level test

Package tests; system-under-test is [`OptimizerHint.prefetch(...)`][hints] round-trip behavior. **One** test; single pytest item, no `parametrize` fan-out. Does not exercise FK-id elision; does not need a router mock.

Decision 3 axis 2 ([`OptimizationPlan.apply(qs)`][plans] preserves `qs._db` for an explicit `.using()` parent) is verified by the Slice 2 live HTTP test `test_using_shard_b_resolver_returns_rows_seeded_on_shard_b` (see [Decision 3](#decision-3--the-cooperation-contract-four-axes) axis 2).

**Synthetic `selected_fields` fixture shape**: the module's `_sel(name, selections=None)` builder mirrors the `SimpleNamespace`-based selection pattern in [`tests/optimizer/test_walker.py`][test-walker] and [`tests/optimizer/test_plans.py`][test-plans], carrying `.name`, `.alias`, `.directives`, `.arguments`, and `.selections` — the attributes the walker reads through [`optimizer/walker.py::_walk_selections`][walker] and its merge helpers.

- `test_consumer_provided_prefetch_via_optimizer_hint_round_trips_using_alias` — registers a synthetic `ParentType` definition for `Category` whose [`Meta.optimizer_hints`][glossary-metaoptimizer-hints] are `{"items": OptimizerHint.prefetch(Prefetch("items", queryset=Item.objects.using("shard_b").all()))}`; builds `plan = plan_optimizations([_sel("items", selections=[_sel("id")])], Category, source_type=ParentType)` so the walker looks up `ParentType`'s hints; applies via `plan.apply(Category.objects.all())` (an unrouted parent); finds the `items` entry in the result's `_prefetch_related_lookups` and asserts its `queryset._db == "shard_b"`. Pins [Decision 3](#decision-3--the-cooperation-contract-four-axes) axis 3 — the consumer's explicit `Prefetch(queryset=...)` survives plan construction; generated child querysets are out of this test's scope.

### `examples/fakeshop/test_query/test_multi_db.py` — two live `/graphql/` HTTP tests

Live tests; system-under-test is the fakeshop project running under `FAKESHOP_SHARDED=1`. **Two** tests from this contract; single pytest item per test. The module is skipped at collection time when `FAKESHOP_SHARDED != "1"` per [Decision 6](#decision-6--live-coverage-under-fakeshop_sharded1). Each test is decorated with `@pytest.mark.django_db(databases=["default", "shard_b"])`. The module also carries the alias pins of later contracts (debug-capture alias, the row-preserving predicate on `shard_b`, write-alias mutations, post-`OrderSet` routing seals, and the planned-prefetch-child alias rows cited under [Decision 3](#decision-3--the-cooperation-contract-four-axes) axis 3).

**Fixture-chain contract**: each alias used in the test gets a full `Branch → Shelf → Book` chain seeded via `.using(alias)` because both `Book.shelf` and `Shelf.branch` are non-null FKs. `Branch.name` is unique, so the helper varies the branch and shelf values by `title`:

```python path=null start=null
def _seed_book_chain(alias: str, *, title: str) -> "models.Book":
    branch = models.Branch.objects.using(alias).create(name=f"Branch-{alias}-{title}", city="Boston")
    shelf = models.Shelf.objects.using(alias).create(code=f"S-{alias}-{title}", topic="Test", branch=branch)
    return models.Book.objects.using(alias).create(
        title=title,
        circulation_status=models.Book.CirculationStatus.AVAILABLE,
        shelf=shelf,
    )
```

**Live-HTTP harness** (per [Decision 6](#decision-6--live-coverage-under-fakeshop_sharded1)): the module-level `_current` holder, the `_graphql_view(request)` view reading it per request, the module-level `urlpatterns = [path("graphql/", _graphql_view)]`, and the `_build_test_schema` per-test fixture (depending on `_reload_project_schema_for_acceptance_tests`) that builds `_MultiDbTestQuery.books_on_shard_b` returning `models.Book.objects.using("shard_b").select_related("shelf__branch")` and stores the schema on `_current["schema"]`, resetting it to `None` at teardown. Each test body wraps the request in `override_settings(ROOT_URLCONF=__name__)` with `clear_url_caches()` on entry and in `finally`.

Tests (each declares `@pytest.mark.django_db(databases=["default", "shard_b"])` and depends on the `_build_test_schema` fixture):

- `test_using_shard_b_resolver_returns_rows_seeded_on_shard_b` — seeds two `Book` chains on `shard_b` via `_seed_book_chain("shard_b", title="A")` / `_seed_book_chain("shard_b", title="B")`; sends `query { booksOnShardB { title shelf { code branch { name } } } }`; asserts the returned title set is exactly `{"A", "B"}`. Pins end-to-end cooperation under a real second connection.
- `test_cross_shard_isolation_default_rows_not_visible_via_shard_b_resolver` — seeds one `Book` chain on `default` via `_seed_book_chain("default", title="default-only")` AND one on `shard_b` via `_seed_book_chain("shard_b", title="shard-b-only")`; sends the same query; asserts the returned title set is exactly `{"shard-b-only"}` and `default-only` is absent. The query selects the full `shelf { code branch { name } }` chain because under the optimizer's `.only(...)` projection a `{ title }`-only selection against the `.select_related("shelf__branch")` resolver produces `Book.objects.only("title", "shelf_id").select_related("shelf__branch")`, which Django rejects with `FieldError: Field Book.shelf cannot be both deferred and traversed using select_related at the same time`; the negative pin rests on the returned `title` set, not on the selection narrowness. Pins the negative shape — the cooperation respects the consumer's queryset routing rather than aggregating across shards.

### Existing tests

`tests/optimizer/test_extension.py`, `tests/optimizer/test_walker.py`, and the rest of the package suite carry no assertion of this contract; `tests/optimizer/test_multi_db.py` sits alongside them with a focused scope. `examples/fakeshop/test_query/test_library_api.py` reaches the reload contract through the same shared conftest fixture per [Decision 7](#decision-7--the-reload-fixture-comes-from-the-shared-test_query-conftest).

## Doc updates

- [`docs/GLOSSARY.md`][glossary] — the [`Multi-database cooperation`][glossary-multi-database-cooperation] Index row (`docs/GLOSSARY.md #"| [Multi-database cooperation](#multi-database-cooperation) |"`) reads `shipped (`0.0.7`)`, and the entry body (`docs/GLOSSARY.md #"## Multi-database cooperation"`) opens "Documented cooperation surface — what the package guarantees under Django's multi-database machinery. Four axes:" and lists the four axes of [Decision 3](#decision-3--the-cooperation-contract-four-axes): (1) `router.db_for_read` on FK-id elision stubs; (2) explicit `.using(alias)` `_db` preservation through [`OptimizationPlan.apply`][glossary-djangooptimizerextension]; (3) consumer-provided [`Prefetch(queryset=...)`][glossary-optimizerhint] via `OptimizerHint.prefetch(...)` round-trips with its `_db` intact, generated `Prefetch` child querysets not inheriting the root alias; (4) strictness-mode N+1 detection is connection-agnostic.
- [`docs/README.md`][readme] — the `### Sharded mode (multi-DB)` section shows the `seed_shards` command, states that `default` keeps pointing at `db.sqlite3` while `shard_b` adds `db_shard_b.sqlite3`, and closes with the forward-pointer to [`GLOSSARY.md#multi-database-cooperation`][glossary-multi-database-cooperation] naming explicit `.using()` `_db` preservation, FK-id elision router hints, consumer `Prefetch(queryset=…)` alias round-trips, and strictness under non-default aliases.
- [`KANBAN.md`][kanban] — the card renders in the Done column as `DONE-023-0.0.7 - Multi-database cooperation contract`, `Status: Done`, with its `Spec:` row resolving to [`docs/SPECS/spec-023-multi_db-0_0_7.md`][spec-023].
- [`CHANGELOG.md`][changelog] — the single `[0.0.7]` `### Added` subsection (`CHANGELOG.md #"## [0.0.7] - "`) carries the `Multi-database cooperation` bullet beside the joint cut's other entries, per [Decision 9](#decision-9--joint-007-cut).
- [`TODAY.md`][today] — the capability list's multiple-databases bullet links the GLOSSARY entry; [`README.md`][root-readme] and [`GOAL.md`][goal] carry no multi-database text, per [Decision 8](#decision-8--no-readme--goal--today-edits).
- [`docs/TREE.md`][tree] — rendered from module docstrings; it lists both `test_multi_db.py` modules under their directories with their docstring first lines.

## Risks and open questions

Each item names a preferred answer and a fallback if the preferred answer proves wrong.

- **`pytest.skip(allow_module_level=True)` precludes per-test marker control.** Every test in the module shares one collection-time skip. Preferred answer: this is fine — every test in the module targets `FAKESHOP_SHARDED=1`, and a test that needs single-DB mode lives in a different file. Fallback: a future need for mixed gating splits the module into two files.
- **Mocking `router` at the resolver-module level versus globally.** Preferred answer: patch the resolvers module's `router` (module-local) per [Decision 5](#decision-5--package-internal-tests-use-a-fixture-router-not-fakeshop_sharded). Fallback: if the `from django.db import models, router` import at [`types/resolvers.py #"from django.db import models, router"`][resolvers] changes shape, the patch target shifts to wherever `router` is bound at module-import time; the test breakage is informative and a one-line fix.
- **Consumer-provided `Prefetch(queryset=...)` `_db` round-trip under Django version changes.** Preferred answer: Django preserves `_db` on a `Prefetch(queryset=qs)` because the inner `qs` is a Django queryset and its `_db` is sticky by the standard queryset contract. Slice 1's optimizer-plan-level test (f) — `test_consumer_provided_prefetch_via_optimizer_hint_round_trips_using_alias` in `tests/optimizer/test_multi_db.py` — pins the package's cooperation by introspecting the post-plan `_prefetch_related_lookups`. Fallback: if Django changes the `_db` propagation rule, the test fails loudly and the package adapts.
- **A generated `Prefetch` child queryset carries no alias in the plan.** Preferred answer: this is a deliberate boundary per [Decision 3](#decision-3--the-cooperation-contract-four-axes) axis 3 — [`walker.py::_build_child_queryset`][walker] seeds from the related model's `_default_manager.all()` and seals a custom `get_queryset` result to stay unrouted, so the alias is applied late, at fetch time, against the parent rows in hand. Consumers who need a specific alias fixed in the plan use [`OptimizerHint.prefetch(Prefetch(queryset=...))`][glossary-optimizerhint]. Fallback: if consumer demand surfaces for resolving a child's alias at *plan* time, a follow-up card adds it under the [`BACKLOG.md`][backlog] `sharding_aware_optimizer` entry; this contract never claimed otherwise.
- **`router.db_for_read` documented signature.** Preferred answer: `(model, **hints) -> str | None` per [Django's docs](https://docs.djangoproject.com/en/stable/topics/db/multi-db/#using-routers); `instance` is the documented hint name. The package's call uses `db_for_read(field_meta.related_model, instance=instance)`, which matches the documented call shape. Fallback: a consumer router that ignores `hints` still works — the kwarg is dropped on the receiving side. The contract is "we forward `instance=` when we have it"; the router's reception is consumer-shaped.
- **Strictness mode is connection-agnostic.** Preferred answer: `_check_n1` inspects the relation caches, the planned-resolver set, and the strictness mode — never `root._state.db` or `queryset._db`. Django's descriptor protocol propagates `_state.db` to related instances accessed through the descriptor (a permitted lazy-load via `book.shelf` from a `using("shard_b")` book row reads from `shard_b`), but with `strictness="raise"` the lazy load never happens — Slice 1 test (e) sets `root._state.db = "shard_b"` only to prove the object shape is accepted. Fallback: if Django drops that propagation, the strictness check is unaffected because it doesn't inspect that attribute.
- **Cross-shard joins and the optimizer's silence.** Preferred answer: a consumer who writes a cross-shard join gets Django's own error at queryset evaluation; the package does not catch or document this failure mode because the [`BACKLOG.md`][backlog] `sharding_aware_optimizer` entry owns first-class sharding-aware planning. Fallback: if demand surfaces for a friendlier `ConfigurationError` on a detected cross-shard join, a follow-up card adds that detection.

## Out of scope (explicitly tracked elsewhere)

- First-class sharding-aware planning: cross-shard joins, automatic shard selection based on FK, multi-shard aggregates, a hypothetical `Meta.preferred_database` declarative hint, AND resolving a generated child `Prefetch`'s alias at plan-construction time rather than alias-late at fetch time (the boundary called out in [Decision 3](#decision-3--the-cooperation-contract-four-axes) axis 3 and [Risks](#risks-and-open-questions)). All tracked in the [`BACKLOG.md`][backlog] `sharding_aware_optimizer` entry (post-`1.0.0` differentiation). `Meta.preferred_database` has no [`docs/GLOSSARY.md`][glossary] entry and stays plain prose rather than a linked term (the terms CSV does not anchor it).
- A package-level `DATABASE_ROUTERS` opinion or reference router class. Routing policy is consumer-shaped.
- Cross-shard join detection. Out of scope; the [`BACKLOG.md`][backlog] `sharding_aware_optimizer` entry.
- Multi-shard aggregates. Out of scope; the [`BACKLOG.md`][backlog] `sharding_aware_optimizer` entry and the future [`AggregateSet`][glossary-aggregateset] (planned for `0.1.3`) — neither aggregates across connections in this contract.
- [Connection-aware optimizer planning][glossary-connection-aware-optimizer-planning] (shipped `0.0.9`) is `edges { node { ... } }` selection planning, NOT database-connection planning — separate concern despite the overlapping word "connection."
- Warning-free scalar registration via `StrawberryConfig.scalar_map`: `DONE-025-0.0.7` in [`KANBAN.md`][kanban]. An independent card in the same `0.0.7` bundle; its surface does not overlap this one's.

## Definition of done

The card is complete when all of the following are true:

1. [`docs/SPECS/spec-023-multi_db-0_0_7.md`][spec-023] (this document) carries the canonical structured filename per [Decision 1](#decision-1--spec-filename-and-canonical-naming), with companion [`docs/SPECS/appx/spec-023-multi_db-0_0_7-terms.csv`][spec-023-terms] anchoring every project-specific term used in the spec body to the matching [`docs/GLOSSARY.md`][glossary] heading (per [`docs/SPECS/NEXT.md`][next] Step 7).
2. `tests/types/test_resolvers.py` carries the **5 resolver-level tests** listed in the [Test plan](#test-plan): (a) FK-id elision stub `_state.db` via `router.db_for_read`, (b) `instance=<parent_row>` on the router call, (c) `instance=None` when parent lacks `_state`, (d) null FK takes early-return and does NOT call the router, (e) strictness check is connection-agnostic and surfaces the same `OptimizerError` shape under non-default aliases. `tests/optimizer/test_multi_db.py` carries the **1 optimizer-plan-level test**: (f) consumer-provided `OptimizerHint.prefetch(Prefetch(queryset=…))` round-trips with `_db` intact. Decision 3 axis 2 is verified by the Slice 2 live `/graphql/` HTTP test. The four FK-id-elision tests use pytest's `monkeypatch` for the router mock; the strictness test and the optimizer-plan test do NOT mock the router. No `pytest.mark.parametrize` fan-out; six pytest items across the two files.
3. `examples/fakeshop/test_query/test_multi_db.py` carries the module-level `pytest.skip(allow_module_level=True)` guard from [Decision 6](#decision-6--live-coverage-under-fakeshop_sharded1) and the **2 tests** listed in the [Test plan](#test-plan): (a) live `.using("shard_b")` round trip, (b) shard isolation under `.using()`. Each test carries `@pytest.mark.django_db(databases=["default", "shard_b"])`, seeds a full `Branch → Shelf → Book` chain per alias, and reaches `/graphql/` exclusively through a `django.test.Client` POST under `override_settings(ROOT_URLCONF=__name__)` with `clear_url_caches()`. The test schema is built inside the `_build_test_schema` per-test fixture, which runs AFTER the autouse reload fixture and stores the schema on the module-level holder the temp URLConf's view reads per request. The autouse reload fixture is the shared `examples/fakeshop/test_query/conftest.py::_reload_project_schema_for_acceptance_tests` per [Decision 7](#decision-7--the-reload-fixture-comes-from-the-shared-test_query-conftest).
4. `examples/fakeshop/apps/library/schema.py` and `examples/fakeshop/apps/products/schema.py` carry no shard-pinned read resolvers per [Decision 4](#decision-4--no-routing-decoration-on-fakeshop-schemas); the holder-pattern schema/URLConf machinery lives inline in `examples/fakeshop/test_query/test_multi_db.py`.
5. `examples/fakeshop/config/settings.py` ships an additive `DATABASES` layout: `default → db.sqlite3` is declared unconditionally in both modes, and `FAKESHOP_SHARDED=1` ADDS `shard_b → db_shard_b.sqlite3` on top. The committed `examples/fakeshop/db_shard_b.sqlite3` fixture (materialized via `seed_shards`) ships so sharded mode works out of the box. The `seed_shards` management command operates only on the secondary `shard_b` alias (the dev `db.sqlite3` is populated via `manage.py seed_data` regardless of mode).
6. The contract adds no production code in `django_strawberry_framework/` per [Decision 2](#decision-2--no-production-code-change).
7. `__all__` in `django_strawberry_framework/__init__.py` carries no multi-database symbol.
8. `tests/base/test_init.py`'s `__all__` assertion carries no multi-database symbol; its version assertion belongs to the release bump ([Decision 9](#decision-9--joint-007-cut)).
9. Package coverage stays at 100% (`pyproject.toml [tool.coverage.report] fail_under = 100`) — **enforced by CI's gate**. The local check is item 17's suite pass.
10. [`docs/GLOSSARY.md`][glossary]'s [`Multi-database cooperation`][glossary-multi-database-cooperation] entry is `shipped (0.0.7)` (Index row at `docs/GLOSSARY.md #"| [Multi-database cooperation](#multi-database-cooperation) |"`; entry body at `docs/GLOSSARY.md #"## Multi-database cooperation"`) and lists the four cooperation axes from [Decision 3](#decision-3--the-cooperation-contract-four-axes).
11. [`docs/README.md`][readme]'s `### Sharded mode (multi-DB)` section carries the forward-pointer to [`GLOSSARY.md#multi-database-cooperation`][glossary-multi-database-cooperation].
12. [`README.md`][root-readme] and [`GOAL.md`][goal] carry no multi-database text, and [`TODAY.md`][today] links the GLOSSARY entry rather than restating the contract, per [Decision 8](#decision-8--no-readme--goal--today-edits); [`docs/TREE.md`][tree] lists both `test_multi_db.py` modules from their docstrings per [Doc updates](#doc-updates).
13. [`KANBAN.md`][kanban] records the card as `DONE-023-0.0.7` in the Done column, with its `Spec:` row naming the structured spec filename per [Decision 1](#decision-1--spec-filename-and-canonical-naming).
14. [`CHANGELOG.md`][changelog]'s `[0.0.7]` `### Added` subsection carries the `Multi-database cooperation` bullet; there is one `[0.0.7]` heading.
15. The version bump is NOT in this card per [Decision 9](#decision-9--joint-007-cut); the release is single-sourced in `__version__` and pinned by `tests/base/test_init.py::test_version`.
16. Zero new public exports.
17. `uv run ruff check --fix .` passes; `uv run ruff format .` passes; `uv run pytest` passes (coverage enforcement is CI's per `pyproject.toml [tool.coverage.report] fail_under = 100`).

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
[querysets]: ../../django_strawberry_framework/utils/querysets.py
[relations]: ../../django_strawberry_framework/utils/relations.py
[resolvers]: ../../django_strawberry_framework/types/resolvers.py
[single-parent-fetch]: ../../django_strawberry_framework/optimizer/single_parent_fetch.py
[walker]: ../../django_strawberry_framework/optimizer/walker.py
[write-transaction]: ../../django_strawberry_framework/utils/write_transaction.py

<!-- tests/ -->
[test-init]: ../../tests/base/test_init.py
[test-plans]: ../../tests/optimizer/test_plans.py
[test-walker]: ../../tests/optimizer/test_walker.py
[tests-optimizer-dir]: ../../tests/optimizer/

<!-- examples/ -->
[models]: ../../examples/fakeshop/apps/library/models.py
[products-schema]: ../../examples/fakeshop/apps/products/schema.py
[schema]: ../../examples/fakeshop/apps/library/schema.py
[seed-shards]: ../../examples/fakeshop/apps/products/management/commands/seed_shards.py
[services]: ../../examples/fakeshop/apps/products/services.py
[settings]: ../../examples/fakeshop/config/settings.py
[test-query-conftest]: ../../examples/fakeshop/test_query/conftest.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
