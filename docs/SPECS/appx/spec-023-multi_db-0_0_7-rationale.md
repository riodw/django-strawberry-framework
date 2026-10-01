# Rationale: spec-023 — Multi-database cooperation contract

Deliberative companion to [`spec-023-multi_db-0_0_7.md`][spec-023]. The spec is the contract; this file holds the reasons behind each of its nine Decisions and the alternatives each one rejects. Every Decision heading below reproduces the spec's heading text, so the spec's `[rationale-d1]` … `[rationale-d9]` links land on the matching section.

## Decision 1 — Spec filename and canonical naming

Spec text: [Decision 1][spec-023-d1].

### Justification

- The structured `spec-<NNN>-<topic>-<0_0_X>.md` convention pinned in [`docs/SPECS/NEXT.md`][next] bakes the card's NNN and target patch into the filename, which keeps the `docs/SPECS/` archive ordered by card number.
- References pointing at whichever path the file has when the reference is written is the simplest rule that survives the archive move: the in-flight path and the archived path are each correct at their own point in the lifecycle, and the Step 8 sweep rewrites every reference when the file moves.

### Alternatives considered (and rejected)

- **An unnumbered `docs/spec-multi_db.md`.** Rejected: it diverges from the structured naming convention and would sit unnumbered beside a numbered cohort.
- **A hyphenated topic slug (`multi-db`).** Rejected: topic slugs are snake_case across the spec corpus (`list_field`, `export_schema`, `scalar_map_helper`); `multi_db` matches, `multi-db` would be an outlier.

## Decision 2 — No production code change

Spec text: [Decision 2][spec-023-d2].

### Justification

- The cooperation already exists in source: `router.db_for_read` on FK-id elision stubs, and the optimizer's reliance on queryset `_db` propagation, which is a Django queryset contract rather than a package one.
- Pinning a contract with tests is the cheapest way to prevent regression. Adding production code (a `router.allow_relation` consultation, a `Meta.preferred_database` hint) would expand the surface beyond what the contract documents and re-open the boundary owned by the [`BACKLOG.md`][backlog] `sharding_aware_optimizer` entry.

### Alternatives considered (and rejected)

- **Add a `router.allow_relation(obj1, obj2)` consultation in the FK-id elision path.** Rejected: `allow_relation` is for cross-DB foreign-key validity; FK-id elision builds a stub from a column already read on one connection, so the call would decide nothing.
- **Add a `Meta.preferred_database` hint for routing.** Rejected: owned by the `sharding_aware_optimizer` backlog entry; shipping it here would impose API surface without the evidence to design it.
- **Route the stub's `instance=` hint through a helper.** Rejected: the router call has one site in [`types/resolvers.py::_build_fk_id_stub`][resolvers]; a helper for it would be over-abstraction.

## Decision 3 — The cooperation contract: four axes

Spec text: [Decision 3][spec-023-d3].

### Justification

- The four axes are the seams where the package itself touches routing: the one router call (FK-id elision), the one place it transforms a consumer queryset (plan application), the one place it carries a consumer-built child queryset (`OptimizerHint.prefetch`), and the one check that inspects loaded rows (strictness). Pinning them lets the test plan target each axis with a named test.
- Anything not on the list is either behavior the package exhibits through Django's queryset contract (and needs no package-level pin) or a future concern of the sharding backlog entry.
- Axis 3 promises nothing about a *generated* child's alias at plan time because a plan is cached and selection-shaped: an alias resolved at plan-construction time would freeze one resolver's connection choice into a cache entry another resolver reads, and would be resolved without the parent-instance hint the router needs. Routing the child alias-late, against the parent rows at fetch time, is how the axis is kept.

### Alternatives considered (and rejected)

- **"`Prefetch` chains respect routing" as a general axis.** Rejected: false of the code. [`optimizer/walker.py::_build_child_queryset`][walker] seeds a generated child from the related model's `_default_manager.all()` and seals a custom `get_queryset` result to stay unrouted; it never threads the root alias. Only a consumer-provided `Prefetch(queryset=…)` keeps an alias of its own.
- **"Strictness tracks the originating connection."** Rejected: false of the code. [`types/resolvers.py::_check_n1`][resolvers] reads the relation caches, the planned-resolver set and the strictness mode, never `root._state.db`, `queryset._db`, or the router. Strictness is connection-agnostic by design.
- **"The optimizer sets `_db` on the queryset before plan application."** Rejected: an implicit-router queryset keeps `_db is None` until evaluation, and the optimizer leaves it so; only an explicit `.using()` alias is preserved.
- **A fifth axis for alias-late routing and the single-related-object visibility re-pin.** Rejected: both are how the existing axes are kept, not separate promises, and the shipped [`docs/GLOSSARY.md`][glossary] entry and [`CHANGELOG.md`][changelog] bullet both state four axes.

## Decision 4 — No routing decoration on fakeshop schemas

Spec text: [Decision 4][spec-023-d4].

### Justification

- Routing policy is consumer-shaped (per [Decision 3][spec-023-d3]); a fakeshop schema with a hard-coded `.using("shard_b")` would be misleading example code suggesting routing is the package's call. The default fakeshop schemas demonstrate the single-DB surface.
- The live tests prove cooperation under the existing `FAKESHOP_SHARDED=1` infrastructure; they bring their own schema rather than redesigning the example ones.

### Alternatives considered (and rejected)

- **Add a `books_on_shard_b: list[BookType]` sibling resolver to `apps/library/schema.py`.** Rejected: it would always read from `shard_b` regardless of the env var, which breaks single-DB mode, where `shard_b` is not in `DATABASES`.
- **Add `DATABASE_ROUTERS` to `examples/fakeshop/config/settings.py`.** Rejected: it would impose a routing opinion on the example project; the single-DB and sharded modes need no router class.

## Decision 5 — Package-internal tests use a fixture router, not `FAKESHOP_SHARDED`

Spec text: [Decision 5][spec-023-d5].

### Justification

- Package-internal tests must run without any fakeshop-side env var. A real second SQLite would need materializing before the test and teardown to avoid polluting the dev `db.sqlite3`, and would test nothing the targeted assertion misses.
- The router-call contract is "we call `router.db_for_read` with this signature and this `instance` argument" — a call-shape assertion, not a routing-outcome assertion. The router's answer is consumer-shaped; the package's contribution is the call. Mock the router and assert on the call.
- The queryset-`_db` and `Prefetch`-`_db` contracts are direct queryset-attribute assertions; they don't go through the router and need no mock.
- The tests split across two files by the [`docs/TREE.md`][tree] mirror rule: `_build_fk_id_stub` and `_check_n1` live in `types/resolvers.py`, so their unit tests live in `tests/types/test_resolvers.py`; the optimizer-plan round-trip lives in `tests/optimizer/`.
- Axis 2 is verified through the live `/graphql/` test rather than a package-internal `OptimizationPlan.apply` assertion because [`AGENTS.md`][agents] #"Test through real usage, prefer the example project" makes a real query the home for any line one can reach.

### Alternatives considered (and rejected)

- **Run package-internal tests under a real two-DB SQLite layout.** Rejected: cost and setup/teardown burden, and a worse assertion — a router-call assertion catches a dropped call even when the alias outcome happens to match the default.
- **Patch `db_for_read` on the shared `django.db.router` singleton.** Rejected: it reroutes every caller in the process for the test's duration. Rebinding the resolvers module's `router` name is the right scope.
- **Mock the router in every Slice 1 test, including the strictness and optimizer-plan tests.** Rejected: those tests never reach FK-id elision, so a mock there would be dead weight that hides nothing and proves nothing.
- **Drive the strictness test through `DjangoOptimizerExtension(strictness="raise")` and real GraphQL execution.** Rejected: it couples a connection-agnostic-shape pin to the extension surface and demands a GraphQL fixture for a one-function unit test.

## Decision 6 — Live coverage under `FAKESHOP_SHARDED=1`

Spec text: [Decision 6][spec-023-d6]. The mechanism that makes `pytest.skip(..., allow_module_level=True)` correct and `pytest.mark.skipif` wrong stays in the spec, because it decides how the module is written.

### Alternatives considered (and rejected)

- **`pytest.mark.skipif(...)` on each test.** Rejected: the env var changes `DATABASES` at settings-import time, and the mark is evaluated after the module's imports run.
- **`pytest.mark.skipif(...)` on a test class.** Rejected for the same reason; mark evaluation happens after import.
- **Move the tests into `examples/fakeshop/tests/` (non-HTTP).** Rejected: the cooperation surface is end-to-end through `/graphql/`, including URL routing, view, schema execution, and JSON serialization; `test_query/` is its home. The package-internal Slice 1 tests are the non-HTTP layer.
- **In-process `execute_sync(...)`.** Rejected: it skips URL routing, the view, and the Django request pipeline that the live-HTTP rule names as the right tier.
- **A module-level static schema built at import time.** Rejected: the autouse reload fixture clears the registry and reloads `apps.library.schema` before the tests run, so a static schema would reference `DjangoType` classes whose registry entries were cleared. The holder pattern defers schema construction until after the reload.
- **Rebuild the schema inside each test body.** Rejected in favor of the per-test fixture, which is the same construction factored into one place; test bodies stay on the assertion.
- **A `{ title }`-only isolation query.** Rejected: under the optimizer's `.only(...)` projection it produces `Book.objects.only("title", "shelf_id").select_related("shelf__branch")`, which Django rejects with `FieldError`. The full `shelf { code branch { name } }` selection keeps the resolver's `select_related` shape and moves the negative pin onto the returned title set.

## Decision 7 — The reload fixture comes from the shared `test_query` conftest

Spec text: [Decision 7][spec-023-d7].

### Justification

- The reload is load-bearing: registry-clearing package tests run in the same session, so any live `/graphql/` module needs the project schema rebuilt before its first request.
- One shared definition in [`examples/fakeshop/test_query/conftest.py`][test-query-conftest] keeps every module rebuilding the same way; a per-module copy would drift.

### Alternatives considered (and rejected)

- **A private copy of the reload fixture in `test_multi_db.py`.** Rejected: duplicated code that drifts from the tree's single definition.
- **No reload fixture, relying on a friendly test order.** Rejected: order independence is a contract of the suite, and the registry-clearing package tests would leave the live schema stale.

## Decision 8 — No README / GOAL / TODAY edits

Spec text: [Decision 8][spec-023-d8].

### Justification

- The root `README.md` presents consumer-facing primitives ([`DjangoType`][glossary-djangotype], the optimizer, [`DjangoListField`][glossary-djangolistfield]); the multi-database cooperation contract is plumbing the package already honors, not a new consumer-name surface.
- `GOAL.md`'s showcase and migration sections are not multi-db-specific.
- `TODAY.md` lists capabilities; its multiple-databases line points at the [`Multi-database cooperation`][glossary-multi-database-cooperation] entry instead of restating the axes, so the contract has one consumer-facing statement.

## Decision 9 — Joint `0.0.7` cut

Spec text: [Decision 9][spec-023-d9].

### Justification

- Restates [`docs/SPECS/spec-020-list_field-0_0_7.md`][spec-020] [Decision 10][spec-020-decision-10--joint-007-cut] so this card's reader does not have to chase the cross-spec reference.
- One shared `[0.0.7]` heading in [`CHANGELOG.md`][changelog] carries every bundle card's `### Added` entry — [`DjangoListField`][glossary-djangolistfield], [`Django AppConfig`][glossary-django-appconfig], [`Schema export management command`][glossary-schema-export-management-command], and this card's [`Multi-database cooperation`][glossary-multi-database-cooperation] among them — and the bundle is cut once.

### Alternatives considered (and rejected)

- **This card bumps `0.0.7` because the cooperation contract is the natural release-cut sentinel.** Rejected: ship order is decided by which card a maintainer picks up next, not by topical fit; pinning the bump to one card creates a sequencing constraint with no engineering justification.
- **A separate release-cut card on [`KANBAN.md`][kanban] that owns the bump.** Rejected: the "last card to ship" policy is workable as-is.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../../AGENTS.md
[backlog]: ../../../BACKLOG.md
[changelog]: ../../../CHANGELOG.md
[kanban]: ../../../KANBAN.md

<!-- docs/ -->
[glossary-django-appconfig]: ../../GLOSSARY.md#django-appconfig
[glossary-djangolistfield]: ../../GLOSSARY.md#djangolistfield
[glossary-djangotype]: ../../GLOSSARY.md#djangotype
[glossary-multi-database-cooperation]: ../../GLOSSARY.md#multi-database-cooperation
[glossary-schema-export-management-command]: ../../GLOSSARY.md#schema-export-management-command
[glossary]: ../../GLOSSARY.md
[tree]: ../../TREE.md

<!-- docs/SPECS/ -->
[next]: ../NEXT.md
[spec-020-decision-10--joint-007-cut]: ../spec-020-list_field-0_0_7.md#decision-10--joint-007-cut
[spec-020]: ../spec-020-list_field-0_0_7.md
[spec-023-d1]: ../spec-023-multi_db-0_0_7.md#decision-1--spec-filename-and-canonical-naming
[spec-023-d2]: ../spec-023-multi_db-0_0_7.md#decision-2--no-production-code-change
[spec-023-d3]: ../spec-023-multi_db-0_0_7.md#decision-3--the-cooperation-contract-four-axes
[spec-023-d4]: ../spec-023-multi_db-0_0_7.md#decision-4--no-routing-decoration-on-fakeshop-schemas
[spec-023-d5]: ../spec-023-multi_db-0_0_7.md#decision-5--package-internal-tests-use-a-fixture-router-not-fakeshop_sharded
[spec-023-d6]: ../spec-023-multi_db-0_0_7.md#decision-6--live-coverage-under-fakeshop_sharded1
[spec-023-d7]: ../spec-023-multi_db-0_0_7.md#decision-7--the-reload-fixture-comes-from-the-shared-test_query-conftest
[spec-023-d8]: ../spec-023-multi_db-0_0_7.md#decision-8--no-readme--goal--today-edits
[spec-023-d9]: ../spec-023-multi_db-0_0_7.md#decision-9--joint-007-cut
[spec-023]: ../spec-023-multi_db-0_0_7.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[resolvers]: ../../../django_strawberry_framework/types/resolvers.py
[walker]: ../../../django_strawberry_framework/optimizer/walker.py

<!-- tests/ -->

<!-- examples/ -->
[test-query-conftest]: ../../../examples/fakeshop/test_query/conftest.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
