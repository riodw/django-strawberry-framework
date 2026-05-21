# Build: Slice 3 — Optimizer + `get_queryset` cooperation tests

Spec reference: `docs/spec-016-list_field-0_0_7.md` (lines 139-141 — Slice 3 checklist; Decision 2 spec lines 381-498; Decision 3 spec lines 499-519; Decision 4 spec lines 520-540; Decision 6 spec lines 568-590; rev2 H1 history at spec line 13; rev2 H2 history at spec line 14; rev2 M3 history at spec line 18; rev4 H2 history at spec line 38; rev5 H1 history at spec line 44; rev5 H2 history at spec line 45; rev5 M3 history at spec line 49; rev6 H1/H2/H3 history at spec lines 55-57; rev6 L3 history at spec line 66; rev6 M6 `assertNumQueries` pinning at spec line 63; Test plan behavior cluster at spec lines 737-752)
Status: final-accepted

## Plan (Worker 1)

### DRY analysis

Slice 3 is a tests-only slice. No production code under `django_strawberry_framework/` is touched (per the spec's slice partition at lines 139-141 and the Slice 2 final-verification carry-forward — the four `_post_process_consumer_*` helpers, the `_default` / `_wrap` dispatch, and the four validation guards all shipped under Slices 1 and 2). Slice 3's DRY scope is therefore test-infrastructure DRY across the 14 new behavior tests and against the existing Slice 2 cluster + `tests/test_registry.py` patterns.

- **Existing patterns reused.**
  - `_isolate_global_registry` autouse fixture — already in `tests/test_list_field.py:40-50` (Slice 2 imported the pattern verbatim from `tests/test_registry.py:35-39`). All 14 new behavior tests inherit this fixture automatically because they live in the same module; no new fixture wiring is needed for registry isolation. This is the Slice-2 review's Low finding ("two-site duplication of `_isolate_global_registry`") deferred to this planning pass.
  - Per-test concrete `DjangoType` declaration shape — `tests/test_list_field.py:116-118` (Slice 2's test #4 used `class _T(DjangoType): class Meta: model = Category` at function scope). The 14 behavior tests follow the same pattern: declare the `DjangoType`(s) inside each test body, with the autouse fixture cleaning the registry between tests.
  - `apps.products.models.Category` + `Item` — already imported into `tests/test_list_field.py:33` (Slice 2) for the resolver-callable test. The behavior tests reuse `Category` for the simplest single-model cases (no relations needed). When a test needs a parent + child FK (root-position optimizer test, FK-id elision test), reuse `apps.products.models.Item` and `Category` (one FK from `Item.category` to `Category`, same pattern the existing optimizer integration tests use at `tests/optimizer/test_extension.py:288-325`).
  - `apps.products.services.seed_data(N)` — `tests/optimizer/test_extension.py:290` uses it; the optimizer/FK-id-elision tests in this slice reuse it for the same reason (per `AGENTS.md` line 6: "First line of every catalog/auth test: `seed_data(N)` or `create_users(N)` from `apps.products.services`").
  - `django_assert_num_queries(N)` pytest-django fixture — `tests/optimizer/test_extension.py:288, 312-316` is the canonical shape for asserting exact query counts inside a `schema.execute_sync(...)` call. The root-position-optimization test and the FK-id-elision test reuse this fixture exactly.
  - `ctx = SimpleNamespace()` then `context_value=ctx` then assert `ctx.dst_optimizer_plan.fk_id_elisions == ("...",)` — `tests/optimizer/test_extension.py:310-325` is the prevailing assertion shape for "did FK-id elision fire?". The FK-id-elision test reuses this verbatim.
  - `_apply_get_queryset_sync` / `_apply_get_queryset_async` — `django_strawberry_framework/types/relay.py:199` / `:225` (verified at HEAD via `grep -n` during this planning pass; Slice 1 confirmed these anchors). The coroutine-rejection guard at `types/relay.py:213-221` is what the sync-coroutine-rejection test pins; Slice 3 reuses the production code, not a re-implemented contract. The test asserts the `ConfigurationError` message matches the leading prefix `<TypeName>.get_queryset returned a coroutine in a sync resolver context.` from `types/relay.py:215-216`.
  - `pytest-asyncio` + `asyncio_mode = auto` — `pytest.ini:7` enables auto-mode; `async def test_*` callables run as async tests without explicit `@pytest.mark.asyncio` markers. Async tests in Slice 3 use this convention (no `asyncio.run(...)` wrappers, no `asgiref.sync.async_to_sync` rewrapping).
  - `Item.objects` / `Category.objects` ORM access inside async tests — must be wrapped with `asgiref.sync.sync_to_async(...)` because Django's sync ORM cannot be awaited directly under `await schema.execute(...)`. The spec's user-facing example at spec lines 305-313 already uses this pattern for an async consumer resolver.
  - `finalize_django_types()` — must be called between `DjangoType` subclass declaration(s) and `strawberry.Schema(query=Query, extensions=[...])` (Slice 0's Worker 2 carry-forward, recorded in `worker-1.md` memory at the Slice 0 final-verification entry). Every test that builds a Strawberry schema follows this order.
  - Introspection-query schema-shape assertion — Slice 0's spike pinned the shape (`{ __type(name: "Query") { fields { name type { kind ofType { kind ofType { kind name } } } } } }`; spec line 109). The two outer-nullability tests (`test_djangolistfield_nullable_outer_via_consumer_annotation`, `test_djangolistfield_non_nullable_outer_default_via_consumer_annotation`) reuse this shape — the test docstrings cite spec line 109 as the assertion-shape anchor.
  - Decision 4's two-fold test-framing (rev3 M6, spec line 534): the package-internal test pins the **return-shape** contract (the default resolver returns a `QuerySet`, not a Python `list`), while the Slice 4 HTTP test pins the **end-to-end** contract. Slice 3 must NOT reach into URL routing / view-layer / SQL-sniffer territory; the live HTTP coverage is Slice 4's job. Slice 3's optimizer-cooperation test calls `schema.execute_sync(...)` against an in-process schema, asserts `ctx.dst_optimizer_plan` was set, and asserts the exact `assertNumQueries` count — that is the "did the root-gated planning hook fire?" probe.

- **New helpers justified.** None at the test-fixture level for this slice. Decision: keep test-local `DjangoType` declarations inline inside each test body (matches the Slice 2 precedent at test #4) rather than extracting a `make_django_type(model, name, get_queryset=None)` factory module. Three reasons:
  1. Each test's `DjangoType` carries distinct semantics — `get_queryset` returning a filtered queryset (default-resolver test), `async def get_queryset(...)` (async-await test), `get_queryset` returning a coroutine (sync-rejection test), no `get_queryset` (root-optimization test), `Meta.primary = True` (Decision 6 tests). Folding these into one parametrized helper would either explode the helper's keyword surface or force callers to monkey-patch attributes onto the returned class — neither is cleaner than `class _T(DjangoType): class Meta: model = Category; @classmethod def get_queryset(cls, qs, info): ...` at the test site.
  2. The Slice 2 review's Low finding flagged duplication of the autouse fixture only; no helper-factory pressure surfaced. Worker 2's note for the same review explicitly defers the `conftest.py` consolidation until a third file appears.
  3. The spec's "test through real usage" rule (`AGENTS.md` line 8) prefers tests that route through `schema.execute_sync(...)` against real Django models over tests that build mock fixtures. Inline `DjangoType` declarations using real `apps.products` models keep the production path live in every test.

  **Fixture-consolidation outcome (Slice 2 carry-forward, resolved here).** `tests/conftest.py` does not exist at HEAD (`ls tests/conftest.py` returns no such file; `find tests/ -name conftest.py` returns nothing). The autouse `_isolate_global_registry` fixture stays inline in `tests/test_list_field.py:40-50` (where Slice 2 placed it). Slice 3 does NOT introduce a third call site (all 14 new tests live in the same `tests/test_list_field.py` file and inherit the autouse from module scope), so the duplication stays bounded at two sites — exactly the threshold the Slice 2 review accepted as "fix-now is not warranted." Worker 2 MUST NOT introduce `tests/conftest.py` in this slice; if a future slice (Slice 4 / Slice 5 / a follow-up spec) adds a third test file needing the same isolation, that slice owns the `conftest.py` consolidation.

- **Duplication risk avoided.** Three near-copies a naive Slice 3 implementation could introduce:
  1. **Re-implementing `_apply_get_queryset_sync`'s coroutine-rejection semantics in a test fixture.** Decision 3 (spec lines 499-519) pins Option A — `list_field.py` imports the production helpers and reuses them verbatim. The `test_djangolistfield_sync_path_rejects_coroutine_from_get_queryset` test asserts the production behavior (raise + message prefix from `types/relay.py:215-216`) rather than asserting a test-mock substitute. Worker 2 MUST NOT replace `_apply_get_queryset_*` with mocks; the test exercises the real `DjangoListField(...)` factory output executed under a real schema.
  2. **Building 14 separate Strawberry schemas with subtly different boilerplate.** Each test that builds a schema follows the same five-step pattern: (a) declare `DjangoType` subclass(es); (b) call `finalize_django_types()`; (c) build `@strawberry.type class Query`; (d) `strawberry.Schema(query=Query, extensions=[...])`; (e) execute. The 14 tests differ in steps (a) and (c) but share (b), (d), (e). The plan keeps the steps inline at each test site (mirrors Slice 2 / the existing optimizer integration tests at `tests/optimizer/test_extension.py:287-325`) rather than extracting a `make_schema_with_type(...)` helper — the latter would need conditional support for `extensions=[DjangoOptimizerExtension()]` vs no extensions, sync vs async `get_queryset`, single-type vs two-type setups, and at that point the helper is more complex than the inline pattern.
  3. **Repeating the introspection-query string in the two outer-nullability tests.** The two tests (`test_djangolistfield_nullable_outer_via_consumer_annotation`, `test_djangolistfield_non_nullable_outer_default_via_consumer_annotation`) both issue the same introspection-query string from spec line 109. Worker 2 may, at their discretion, hoist the query string to a module-level constant (`_INTROSPECTION_QUERY = "{ __type(name: \"Query\") { ... } }"`) at the top of `tests/test_list_field.py` if the duplication reads as noise. Recommended: keep inline at both sites — the string is short enough that the duplication is not load-bearing, and inline keeps the test's read-flow self-contained. NOT discretionary: both tests MUST use an introspection query (not `print(schema)` or `str(schema)` substring checks), per rev6 M2 (spec line 59).

  **Static inspection helper.** Run completed against `django_strawberry_framework/list_field.py` (the system-under-test for the 14 cases) at planning time: `uv run python scripts/review_inspect.py django_strawberry_framework/list_field.py --output-dir docs/shadow --stdout`. The refreshed shadow at `docs/shadow/django_strawberry_framework__list_field.{overview.md,stripped.py}` confirms the post-Slice-2 surface (134 source lines; 6 symbols — factory `DjangoListField` at lines 47-134, two module-scope `_post_process_consumer_*` helpers at lines 31-44, plus the three nested resolver shapes `_default` / `async def _wrap` / `def _wrap` at lines 93-101, 108-117, 120-125; one control-flow hotspot — the factory at 88 lines, 7 branch nodes; 0 TODOs; 9 ORM markers; 11 imports). Walks every ORM marker and call-of-interest; each maps to a Slice 3 test:
  - `models.QuerySet` isinstance checks (lines 34, 42) → `test_djangolistfield_consumer_resolver_python_list_return_passes_through` (sync) + `test_djangolistfield_async_consumer_resolver_python_list_return_passes_through` (async) — both exercise the False branch where a non-QuerySet pass-through happens.
  - `_apply_get_queryset_sync` calls (lines 35, 101) → `test_djangolistfield_default_resolver_returns_queryset_filtered_by_get_queryset` (default path, line 101) + `test_djangolistfield_consumer_resolver_queryset_return_gets_get_queryset_applied` (consumer path, line 35).
  - `_apply_get_queryset_async` calls (lines 43, 100) → `test_djangolistfield_async_get_queryset_is_awaited` (default async path, line 100) + `test_djangolistfield_async_consumer_resolver_queryset_return_gets_get_queryset_applied` (consumer async path, line 43).
  - `in_async_context()` branch (line 95) → `test_djangolistfield_default_resolver_works_under_sync_and_async_schema_execution` (rev5 M3 — the dual-execution test pins both True and False arms of this branch).
  - `inspect.iscoroutinefunction(user_resolver)` decision (line 106) → `test_djangolistfield_async_consumer_resolver_*` (True arm) + `test_djangolistfield_consumer_resolver_*` (False arm).
  - Coroutine-rejection in `_apply_get_queryset_sync` (via `types/relay.py:213-221`) → `test_djangolistfield_sync_path_rejects_coroutine_from_get_queryset`.
  - Strawberry-field metadata pass-through (line 129) → covered by the two outer-nullability tests' schema-build assertions.
  - Root-gated `DjangoOptimizerExtension.resolve` hook (`optimizer/extension.py:553`) → `test_djangolistfield_at_root_position_is_optimized`.
  - FK-id elision plan emission → `test_djangolistfield_fk_id_elision_survives`.
  - `Meta.primary` discrimination → `test_djangolistfield_with_meta_primary_true_returns_primary_queryset` + `test_djangolistfield_with_secondary_target_uses_secondary_get_queryset`.

  Helper run for `tests/test_list_field.py`: SKIPPED with reason "test file; not part of the package's review-worthy logic surface per Worker 3's role-file note." (The file is currently 241 lines but most of those are TODO comments; the file remains below the threshold once the TODOs are replaced because Worker 2 deletes the TODO blocks as it lands each test.) For `types/base.py` and `optimizer/extension.py`, helper runs SKIPPED with reason "read-only reference for Slice 3; `grep -n` lookups suffice for pinning HEAD line numbers."

### Implementation steps

Slice 3 ships 14 behavior tests inside `tests/test_list_field.py`, each replacing one of the 14 TODO blocks at `tests/test_list_field.py:141-241` (verified by re-reading the file at HEAD during this planning pass; the TODO count is 14, one per Slice-3 test method). All test method names below are VERBATIM from the spec Test plan (spec lines 737-752); Worker 2 MUST NOT invent or shorten names. The 14 tests group into eight clusters by the production-code branch each one pins (see DRY analysis above). The plan presents them in the order they appear in the spec Test plan + scaffold-TODO order — Worker 2 may replace each TODO block in place to preserve scaffold navigation.

Line numbers below are pin-at-write-time navigational hints; Worker 2 must re-verify against HEAD before editing — Slice 2 shipped Slice 2's diff, so line anchors in `tests/test_list_field.py` reference the post-Slice-2 file.

The autouse `_isolate_global_registry` fixture at `tests/test_list_field.py:40-50` already protects every test in the file; Worker 2 does NOT re-add it. Imports already present at the top of the file (`pytest`, `Category` from `apps.products.models`, `DjangoListField` + `DjangoType` from `django_strawberry_framework`, `ConfigurationError` from `.exceptions`, `registry`) cover the common needs; Slice 3 adds the following imports at the top of `tests/test_list_field.py` only as the corresponding tests need them:

- `from types import SimpleNamespace` — for `ctx = SimpleNamespace()` in the optimizer-cooperation and FK-id-elision tests (mirrors `tests/optimizer/test_extension.py:5,310`).
- `from asgiref.sync import sync_to_async` — for the async tests that wrap ORM calls (`Item.objects.filter(...)`) before returning a `QuerySet` from an `async def` resolver (mirrors the spec's user-facing example at spec lines 305-313).
- `import strawberry` — to build `@strawberry.type class Query: ...` inside test bodies.
- `from django_strawberry_framework import DjangoOptimizerExtension, finalize_django_types` — `DjangoOptimizerExtension` for tests asserting optimizer behavior; `finalize_django_types` for every test that builds a schema (Slice 0 carry-forward — finalize MUST run between subclass declarations and `strawberry.Schema(...)`).
- `from apps.products import services` — for `services.seed_data(N)` (`AGENTS.md` line 6).
- `from apps.products.models import Item` — for parent + child FK fixtures (root-optimization test, FK-id-elision test).

Worker 2 lands these imports alphabetically grouped per the existing import convention in the file.

#### Group A — Default-resolver shape and `cls.get_queryset` invocation (2 tests)

1. **`test_djangolistfield_default_resolver_returns_queryset_filtered_by_get_queryset`** (spec line 739; scaffold TODO at `tests/test_list_field.py:141-144`).
   - Pins: the default resolver path at `list_field.py:91-103` — specifically the sync branch at `list_field.py:101` (`return _apply_get_queryset_sync(target_type, qs, info)`).
   - Setup: `services.seed_data(1)` to populate `Category` rows; declare a function-scope `class _CategoryType(DjangoType): class Meta: model = Category; @classmethod def get_queryset(cls, qs, info): return qs.exclude(name__startswith=<known-prefix>)`. Choose a prefix that excludes at least one but not all rows so the test is falsifiable.
   - Schema: `@strawberry.type class Query: all_categories: list[_CategoryType] = DjangoListField(_CategoryType)`; call `finalize_django_types()`; build `strawberry.Schema(query=Query)` (NO `extensions=[]` — this test pins the queryset return shape, not the optimizer hook).
   - Execution: `result = schema.execute_sync("{ allCategories { id name } }")`; assert `result.errors is None`; assert every returned row's `name` does NOT start with the known prefix (i.e., `get_queryset`'s filter fired).
   - Docstring: one sentence — "Default resolver applies `cls.get_queryset(qs, info)` in a sync context (spec Decision 2, line 482)."

2. **`test_djangolistfield_async_get_queryset_is_awaited`** (spec line 740; scaffold TODO at `tests/test_list_field.py:147-151`).
   - Pins: the default resolver's async branch at `list_field.py:94-100` — specifically the `_apply_get_queryset_async(target_type, qs, info)` call when `in_async_context()` returns True and `get_queryset` is `async def`.
   - Setup: `services.seed_data(1)`; declare `class _CategoryType(DjangoType): class Meta: model = Category; @classmethod async def get_queryset(cls, qs, info): return await sync_to_async(lambda: qs.exclude(name__startswith=<known-prefix>))()`.
   - Test function is `async def test_...` (pytest-asyncio auto-mode runs it under an event loop).
   - Schema: same as test 1; execute via `await schema.execute("{ allCategories { id name } }")`.
   - Assertion: `result.errors is None`; every row's `name` does NOT start with the known prefix.
   - Docstring: "Default resolver awaits an `async def get_queryset(...)` under `await schema.execute(...)` (spec Decision 2 async path; Decision 3 `_apply_get_queryset_async`)."

#### Group B — Dual-execution (rev5 M3; 1 test)

3. **`test_djangolistfield_default_resolver_works_under_sync_and_async_schema_execution`** (spec line 741; scaffold TODO at `tests/test_list_field.py:154-161`).
   - Pins: the runtime `in_async_context()` branch at `list_field.py:95` — both arms when `get_queryset` is SYNC. The `True` arm exercises the case where the default resolver is invoked under `await schema.execute(...)` (the wrapper returns the coroutine from `_apply_get_queryset_async`); the `False` arm exercises `schema.execute_sync(...)`. This is the rev5 M3 dual-execution test added explicitly to cover the runtime-branch shape promised in the Edge cases section (spec line 697).
   - Setup: `services.seed_data(1)`; declare `class _CategoryType(DjangoType): class Meta: model = Category; @classmethod def get_queryset(cls, qs, info): return qs.exclude(name__startswith=<known-prefix>)` — note this `get_queryset` is SYNC, not `async def`.
   - Test function: `async def test_...` because `await schema.execute(...)` requires an event loop. Inside the body, run both `schema.execute_sync("{ allCategories { id name } }")` and `await schema.execute("{ allCategories { id name } }")`; assert both results' `data` are identical and both filter out the known-prefix rows.
   - Docstring: "Sync `get_queryset` works under both `schema.execute_sync(...)` and `await schema.execute(...)`; pins the runtime `in_async_context()` branch at `list_field.py:95` (rev5 M3, spec line 49)."

#### Group C — Sync coroutine rejection (1 test)

4. **`test_djangolistfield_sync_path_rejects_coroutine_from_get_queryset`** (spec line 742; scaffold TODO at `tests/test_list_field.py:164-168`).
   - Pins: the coroutine-rejection guard at `types/relay.py:213-221` — the field reuses this guard verbatim per Decision 3 Option A (spec lines 510-513). The test pins the guard fires when the default resolver runs synchronously but `get_queryset` is `async def`.
   - Setup: `services.seed_data(1)`; declare `class _CategoryType(DjangoType): class Meta: model = Category; @classmethod async def get_queryset(cls, qs, info): return qs`.
   - Schema: same as test 1; execute via `result = schema.execute_sync("{ allCategories { id name } }")`.
   - Assertion: `result.errors is not None`; `len(result.errors) == 1`; the first error's message contains `_CategoryType.get_queryset returned a coroutine in a sync resolver context.` (verbatim leading sentence from `types/relay.py:215-216`). Use `assert "returned a coroutine in a sync resolver context" in str(result.errors[0])` to pin the load-bearing substring.
   - Docstring: "Sync resolver path raises `ConfigurationError` when `get_queryset` is `async def` and the request is sync (Decision 3; reuses `types/relay.py:_apply_get_queryset_sync`'s rejection at lines 215-220)."

#### Group D — Sync consumer-resolver paths (rev2 H1; 2 tests)

5. **`test_djangolistfield_consumer_resolver_queryset_return_gets_get_queryset_applied`** (spec line 743; scaffold TODO at `tests/test_list_field.py:171-175`).
   - Pins: the sync consumer-resolver wrapper at `list_field.py:120-125` — specifically that `_post_process_consumer_sync` (line 121) applies `target_type.get_queryset(...)` to a `Manager`/`QuerySet` return (rev2 H1, graphene-django parity).
   - Setup: `services.seed_data(1)`; declare `class _CategoryType(DjangoType)` with a `get_queryset` that excludes rows matching a known prefix; supply `resolver=lambda root, info: Category.objects.all()`.
   - Schema build: `all_categories: list[_CategoryType] = DjangoListField(_CategoryType, resolver=_resolver)`.
   - Execution: `result = schema.execute_sync("{ allCategories { id name } }")`; assert the known-prefix rows are absent (`get_queryset` fired on the consumer's queryset return).
   - Docstring: "Sync consumer resolver returning a `QuerySet` receives `target_type.get_queryset(...)` (rev2 H1 graphene-django parity, spec line 13)."

6. **`test_djangolistfield_consumer_resolver_python_list_return_passes_through`** (spec line 744; scaffold TODO at `tests/test_list_field.py:178-182`).
   - Pins: the sync consumer-resolver wrapper at `list_field.py:120-125` — specifically that `_post_process_consumer_sync` returns the non-`QuerySet` result unchanged (line 36 — the `return result` pass-through arm).
   - Setup: `services.seed_data(1)`; declare `_CategoryType` with a `get_queryset` that excludes a known-prefix row; supply `resolver=lambda root, info: list(Category.objects.all())` so the resolver returns a Python `list`, not a queryset. Choose a known-prefix value present in the seed so the list contains one of the would-have-been-filtered rows.
   - Execution: `result = schema.execute_sync("{ allCategories { id name } }")`; assert the known-prefix row IS present in `result.data["allCategories"]` (proving `get_queryset` was NOT applied to the list return).
   - Docstring: "Sync consumer resolver returning a Python `list` bypasses `target_type.get_queryset(...)` (rev2 H1 graphene-django parity)."

#### Group E — Async consumer-resolver paths (rev4 H2; 2 tests)

7. **`test_djangolistfield_async_consumer_resolver_queryset_return_gets_get_queryset_applied`** (spec line 745; scaffold TODO at `tests/test_list_field.py:185-191`).
   - Pins: the async consumer-resolver wrapper at `list_field.py:108-117` — specifically that the awaited consumer return is fed to `_post_process_consumer_async` (lines 113-117), and the `_apply_get_queryset_async` call (line 43) fires on a `QuerySet` result.
   - Setup: `services.seed_data(1)`; declare `_CategoryType` with sync `get_queryset` that excludes a known prefix; build `async def _resolver(root, info): return await sync_to_async(lambda: Category.objects.all())()`.
   - Test function: `async def test_...`; execute via `await schema.execute("{ allCategories { id name } }")`.
   - Assertion: `result.errors is None`; the known-prefix rows are absent.
   - Docstring: "Async consumer resolver returning a `QuerySet` receives `target_type.get_queryset(...)` after the consumer coroutine is awaited (rev4 H2, spec line 38)."

8. **`test_djangolistfield_async_consumer_resolver_python_list_return_passes_through`** (spec line 746; scaffold TODO at `tests/test_list_field.py:194-198`).
   - Pins: the async consumer-resolver wrapper at `list_field.py:108-117` — specifically that `_post_process_consumer_async` returns a non-`QuerySet` result unchanged (line 44 — the pass-through arm).
   - Setup: as test 7 but `async def _resolver(root, info): return await sync_to_async(lambda: list(Category.objects.all()))()`. Choose a known-prefix value present in the seed.
   - Assertion: the known-prefix row is PRESENT in `result.data["allCategories"]` (proving `get_queryset` was NOT applied to the list).
   - Docstring: "Async consumer resolver returning a Python `list` bypasses `target_type.get_queryset(...)` (rev4 H2 — pins await-then-isinstance ordering)."

#### Group F — Outer-nullability via consumer annotation (rev2 H2; 2 tests)

9. **`test_djangolistfield_nullable_outer_via_consumer_annotation`** (spec line 748; scaffold TODO at `tests/test_list_field.py:209-213`).
   - Pins: the consumer's class-attribute annotation (`list[T] | None`) drives the rendered GraphQL type (`[T!]`), NOT a constructor argument (rev2 H2, spec line 14).
   - Setup: declare `class _CategoryType(DjangoType): class Meta: model = Category`; `@strawberry.type class Query: all_categories: list[_CategoryType] | None = DjangoListField(_CategoryType)`; `finalize_django_types()`; build `strawberry.Schema(query=Query)`.
   - Execution: issue the introspection query from spec line 109 (`{ __type(name: "Query") { fields { name type { kind ofType { kind ofType { kind name } } } } } }`) via `schema.execute_sync(...)`.
   - Assertion: locate the `allCategories` field in `result.data["__type"]["fields"]`; assert `type.kind == "LIST"`, `type.ofType.kind == "NON_NULL"`, `type.ofType.ofType.kind == "OBJECT"`, `type.ofType.ofType.name == "_CategoryType"`. (Note: the outer `NON_NULL` wrapper from the non-nullable test case is ABSENT here — that's the load-bearing difference.)
   - Docstring: "`list[_CategoryType] | None` renders as `[_CategoryType!]` (rev2 H2, spec line 14; introspection-shape mechanism per rev6 M2, spec line 59)."

10. **`test_djangolistfield_non_nullable_outer_default_via_consumer_annotation`** (spec line 749; scaffold TODO at `tests/test_list_field.py:216-220`).
    - Pins: the default annotation (`list[T]` without `| None`) renders as `[T!]!`.
    - Setup: as test 9 but annotation is `list[_CategoryType]` (no `| None`).
    - Assertion: `type.kind == "NON_NULL"`, `type.ofType.kind == "LIST"`, `type.ofType.ofType.kind == "NON_NULL"`, `type.ofType.ofType.ofType.kind == "OBJECT"`, `type.ofType.ofType.ofType.name == "_CategoryType"`. (Four levels of unwrap, matching Slice 0's pinned shape at spec line 109.)
    - Docstring: "`list[_CategoryType]` renders as `[_CategoryType!]!` (rev2 H2; introspection-shape mechanism per rev6 M2)."

#### Group G — Optimizer cooperation (rev2 M3 + FK-id elision; 2 tests)

11. **`test_djangolistfield_at_root_position_is_optimized`** (spec line 747; scaffold TODO at `tests/test_list_field.py:201-206`).
    - Pins: the root-gated `DjangoOptimizerExtension.resolve` hook (`optimizer/extension.py:553` — the `info.path.prev is not None` early-return) fires on a `DjangoListField`-served root query; the planning hook produces `prefetch_related` for the nested relation selection. This is the SINGLE regression net for the rev2 M3 "root only" scope narrowing (Decision 4, spec line 532).
    - Setup: `services.seed_data(1)`; declare two `DjangoType`s — `class _CategoryType(DjangoType): class Meta: model = Category; fields = ("id", "name", "items")` (with `items` as the reverse-FK relation), `class _ItemType(DjangoType): class Meta: model = Item; fields = ("id", "name", "category")`. `finalize_django_types()`. `@strawberry.type class Query: all_categories: list[_CategoryType] = DjangoListField(_CategoryType)`. `strawberry.Schema(query=Query, extensions=[DjangoOptimizerExtension()])`.
    - Execution: inside `with django_assert_num_queries(2)` issue `{ allCategories { id name items { id name } } }`. `ctx = SimpleNamespace(); ...execute_sync(..., context_value=ctx)`.
    - **`assertNumQueries(N)` derivation** (rev6 M6, spec line 63): `N = 2` — one base SELECT against `Category` plus one `prefetch_related("items")` SELECT against `Item`. Pin the value (not a `<= N` bound). The test docstring documents the derivation so a future maintainer who changes the selection shape can recompute deterministically: `N = 1 base SELECT + 1 SELECT per prefetch_related relation in the nested selection. For { allCategories { items { id } } } against Category with items as reverse-FK, N = 2.`
    - Additional assertions: `result.errors is None`; `ctx.dst_optimizer_plan is not None` (the plan was published by the optimizer extension); `ctx.dst_optimizer_plan.prefetch_related == ("items",)` or whatever the canonical shape is at HEAD (Worker 2 pins this against the actual plan output during implementation — pattern match against `tests/optimizer/test_extension.py:320-325`).
    - Docstring: "Root-position `DjangoListField` triggers `DjangoOptimizerExtension.resolve` (`optimizer/extension.py:553`); pins the rev2 M3 root-only contract via exact `assertNumQueries(2)` (rev6 M6 — 1 base SELECT + 1 prefetch_related SELECT for the `items` relation, spec lines 18, 63)."

12. **`test_djangolistfield_fk_id_elision_survives`** (spec line 750; scaffold TODO at `tests/test_list_field.py:223-227`).
    - Pins: the FK-id elision plan fires when a `DjangoListField`-served query selects only `id` on a forward FK relation. Mirrors the existing integration pattern at `tests/optimizer/test_extension.py:287-325`.
    - Setup: `services.seed_data(1)`; declare `_CategoryType(DjangoType)` with `Meta.fields = ("id", "name")` and `_ItemType(DjangoType)` with `Meta.fields = ("id", "name", "category")`. `finalize_django_types()`. `@strawberry.type class Query: all_items: list[_ItemType] = DjangoListField(_ItemType)`. `strawberry.Schema(query=Query, extensions=[DjangoOptimizerExtension()])`.
    - Execution: `ctx = SimpleNamespace()`; `with django_assert_num_queries(1):` issue `{ allItems { name category { id } } }`.
    - Assertions (mirroring `tests/optimizer/test_extension.py:317-325`): `result.errors is None`; every item has a non-None `category.id`; `ctx.dst_optimizer_plan.select_related == ()`; `ctx.dst_optimizer_plan.prefetch_related == ()`; `ctx.dst_optimizer_plan.only_fields == ("name", "category_id")`; `ctx.dst_optimizer_plan.fk_id_elisions == ("_ItemType.category@allItems.category",)`; `ctx.dst_optimizer_fk_id_elisions == {"_ItemType.category@allItems.category"}`.
    - Docstring: "FK-id elision fires under a root `DjangoListField` for `category { id }`-only selections; pins one query and the FK-id-elision plan shape (mirrors `tests/optimizer/test_extension.py:287-325`)."

#### Group H — `Meta.primary` interaction (Decision 6; 2 tests)

13. **`test_djangolistfield_with_meta_primary_true_returns_primary_queryset`** (spec line 751; scaffold TODO at `tests/test_list_field.py:230-234`).
    - Pins: when two `DjangoType`s exist on the same model and one carries `Meta.primary = True`, `DjangoListField(PrimaryType)` returns rows queried via the primary's `get_queryset`. The test discriminates by giving the two types' `get_queryset`s different filtering behavior; pointing the field at the primary picks the primary's behavior.
    - Setup: `services.seed_data(1)`; declare `class _PrimaryCategoryType(DjangoType): class Meta: model = Category; primary = True` with a `get_queryset` excluding a known-prefix row; declare `class _SecondaryCategoryType(DjangoType): class Meta: model = Category` (no `primary`) with a different `get_queryset` (e.g., excludes a different-prefix row, or excludes nothing). `finalize_django_types()`.
    - Schema build: `@strawberry.type class Query: all_primary: list[_PrimaryCategoryType] = DjangoListField(_PrimaryCategoryType)`. `strawberry.Schema(query=Query)`.
    - Execution: `schema.execute_sync("{ allPrimary { id name } }")`.
    - Assertion: the rows match the primary's `get_queryset` filter (the known-prefix row from the primary's exclusion is absent; rows the secondary would have filtered out are present).
    - Docstring: "`DjangoListField(PrimaryType)` invokes the primary's `get_queryset` (Decision 6 multi-type-per-model; spec line 583)."

14. **`test_djangolistfield_with_secondary_target_uses_secondary_get_queryset`** (spec line 752; scaffold TODO at `tests/test_list_field.py:237-240`).
    - Pins: pointing the field at the secondary returns the secondary's `get_queryset` filter, NOT the primary's.
    - Setup: same as test 13 (two types on `Category`, one primary, distinct `get_queryset` behaviors).
    - Schema build: `@strawberry.type class Query: all_secondary: list[_SecondaryCategoryType] = DjangoListField(_SecondaryCategoryType)`. `strawberry.Schema(query=Query)`.
    - Execution: `schema.execute_sync("{ allSecondary { id name } }")`.
    - Assertion: the rows match the SECONDARY's `get_queryset` filter (rows the primary's exclusion would have removed are present; the secondary's-prefix row is absent).
    - Docstring: "`DjangoListField(SecondaryType)` invokes the secondary's `get_queryset`; the registry's `Meta.primary` discriminator does NOT override the explicit-target argument (Decision 6; spec line 584)."

### Test additions / updates

- **14 new test functions / methods land in `tests/test_list_field.py`.** Each replaces one of the 14 TODO blocks at `tests/test_list_field.py:141-241` (one-to-one mapping; the scaffold's TODO order matches the spec Test plan order; Worker 2 replaces each TODO in place to preserve the scaffold's navigation structure).
- The 14 test names verbatim, in the order they replace the scaffold TODOs:
  1. `test_djangolistfield_default_resolver_returns_queryset_filtered_by_get_queryset`
  2. `test_djangolistfield_async_get_queryset_is_awaited`
  3. `test_djangolistfield_default_resolver_works_under_sync_and_async_schema_execution`
  4. `test_djangolistfield_sync_path_rejects_coroutine_from_get_queryset`
  5. `test_djangolistfield_consumer_resolver_queryset_return_gets_get_queryset_applied`
  6. `test_djangolistfield_consumer_resolver_python_list_return_passes_through`
  7. `test_djangolistfield_async_consumer_resolver_queryset_return_gets_get_queryset_applied`
  8. `test_djangolistfield_async_consumer_resolver_python_list_return_passes_through`
  9. `test_djangolistfield_at_root_position_is_optimized`
  10. `test_djangolistfield_nullable_outer_via_consumer_annotation`
  11. `test_djangolistfield_non_nullable_outer_default_via_consumer_annotation`
  12. `test_djangolistfield_fk_id_elision_survives`
  13. `test_djangolistfield_with_meta_primary_true_returns_primary_queryset`
  14. `test_djangolistfield_with_secondary_target_uses_secondary_get_queryset`
- **rev6 L2 scaffold-TODO sweep at this site** (spec line 141): Worker 2 must grep `tests/test_list_field.py` for `# TODO(spec-016` markers as each TODO block is replaced. Confirm zero residue after the slice lands (`grep -c "TODO(spec-016, Slice 3" tests/test_list_field.py` must return 0). The four Slice 2 TODOs were already removed in Slice 2's diff (`tests/test_list_field.py:53-130` no longer carries any `# TODO(spec-016, Slice 2` markers); Worker 2 only needs to confirm the 14 Slice 3 markers go away.
- **No production source under `django_strawberry_framework/` changes.** Slice 3 ships tests only. If a test reveals a missing branch in `list_field.py`, that is spec drift — surface it via `### Notes for Worker 1 (spec reconciliation)` in the Build report. Worker 1 will consider splitting into Slice 3a (tests) and Slice 3b (production fix) if needed; do NOT pull a production fix into the same Worker 2 pass without Worker 1 authorization.
- **Temp tests under `docs/builder/temp-tests/slice-3/`** — none expected. The 14 pinned tests are direct exercises of the production contract through `schema.execute_sync(...)` / `await schema.execute(...)`; no scaffolding scratchpad is justified.
- **Slice 3 must not touch the Slice 4 surfaces** (`examples/fakeshop/apps/library/schema.py`, `examples/fakeshop/test_query/test_library_api.py`); those are explicitly Slice 4's contract per spec lines 142-145.

### Implementation discretion items

These items are Worker-2-discretionary because Worker 1 has assessed them and decided either equally-valid options exist OR the spec does not pin them:

- **Fixture naming inside test bodies.** The Slice 2 precedent uses `class _T(DjangoType): ...` for the resolver-callable test (test #4). Slice 3's behavior tests need more semantically-distinct names because many tests declare TWO `DjangoType`s (the `Meta.primary` tests, the optimizer-cooperation tests, the FK-id-elision test). Worker 2's discretion: pick names like `_CategoryType` / `_ItemType` (semantic, mirrors `tests/optimizer/test_extension.py:292-300`) OR `_T1` / `_T2` (terse). Recommended: semantic names matching the model — they read better in the assertion failure traces.
- **Whether to parametrize the four sync/async × `QuerySet`/`list` consumer-resolver tests (Group D + Group E)** into a single `pytest.mark.parametrize` table or keep them as four named functions. Either is acceptable. Recommended: keep four named functions — the spec names each test explicitly at lines 743-746, and `pytest.raises` doesn't compose into the body the same way an explicit `async def` test function does (async tests need `async def`; sync tests need `def`; parametrizing across the sync/async axis would force a parametrize-id-driven branch in the body). Two named functions per axis (sync queryset, sync list, async queryset, async list) reads cleanly.
- **Known-prefix value choice for the `get_queryset` filter.** The spec doesn't pin a specific prefix. Recommended: use a deterministic prefix that `services.seed_data(N)` reliably produces — e.g., `Category` names start with `"Category "` followed by an index (verify against `apps/products/services.py` during implementation if unsure). The discriminator can be `name__startswith="Category 1"` or similar; the test only needs ONE row excluded for falsifiability.
- **Introspection-query string placement.** Discretion to inline at both sites (Group F) vs hoist to a module-level constant. Recommended inline (the duplication is two lines per site; hoisting saves four lines but adds module-level noise).
- **The exact `prefetch_related` shape pinned by test 11.** Recommended pattern: assert `ctx.dst_optimizer_plan.prefetch_related == ("items",)` if the items relation prefetches as `"items"`; Worker 2 may need to inspect the actual plan shape during implementation. If the plan shape is more complex (e.g., includes a tuple-of-Prefetch objects), pin via substring match on `repr(plan.prefetch_related)`. Pattern-match against `tests/optimizer/test_extension.py:320-325`.

NOT discretionary (Worker 2 MUST follow these):

- **The 14 test names** are spec-pinned at lines 739-752 and the scaffold TODOs at `tests/test_list_field.py:141-241` use those exact names verbatim. Worker 2 MUST NOT shorten, expand, or reorder them.
- **The assertion mechanism** for the two outer-nullability tests MUST be an introspection query against `__type(name: "Query")` (rev6 M2, spec line 59 / spec line 109). Worker 2 MUST NOT use `print(schema)`, `str(schema)` substring matching, or SDL serialization.
- **`assertNumQueries(N)` for the optimizer-cooperation test (test 11)** MUST be the exact-value form (`django_assert_num_queries(2)`), NOT `<= N` (rev6 M6, spec line 63). The docstring MUST derive `N` so future maintainers can recompute it.
- **The coroutine-rejection test (test 4)** MUST assert the error message contains the leading substring `returned a coroutine in a sync resolver context` (verbatim from `types/relay.py:215-216`). This pins that `DjangoListField` reuses the production helper and does NOT re-implement the rejection.
- **Async tests** MUST use `async def test_...` (pytest-asyncio auto-mode) — NOT `asyncio.run(...)` wrappers or `asgiref.sync.async_to_sync` around the test body. The convention is set by `pytest.ini:7` (`asyncio_mode = auto`).
- **ORM access inside async tests** MUST be wrapped with `sync_to_async(...)` (matches the spec's user-facing example at spec lines 305-313 and the Edge cases note at spec line 695).
- **Decision 4's two-fold framing** — Slice 3 owns the package-internal return-shape contract; the Slice 4 HTTP test owns the end-to-end contract. Do NOT add `django.test.Client`-style live `/graphql/` HTTP coverage to `tests/test_list_field.py`.

### Spec slice checklist (verbatim)

The spec's nested sub-bullets for Slice 3 from `## Slice checklist` (spec lines 139-141), copied verbatim. Every box stays `- [ ]` during this planning pass; the final-verification pass ticks each `- [x]` as the contract lands.

- [x] Package-internal tests under `tests/test_list_field.py` covering: default-resolver shape, `cls.get_queryset` invocation, sync coroutine rejection, async path awaits sync + async `get_queryset`, **sync consumer `resolver=` return value receives `get_queryset` when it is a `Manager`/`QuerySet`** (rev2 H1), Python-`list` sync consumer returns pass through unchanged (rev2 H1), **async consumer `resolver=` returning a `Manager`/`QuerySet` receives `get_queryset`** (rev4 H2), Python-`list` async consumer returns pass through unchanged (rev4 H2), nullable-outer-via-consumer-annotation produces `[T!]` (rev2 H2), non-nullable-outer default produces `[T!]!` (rev2 H2), `DjangoListField` at root position is optimized (rev2 M3), FK-id elision survives, `Meta.primary` interaction (explicit primary, explicit secondary).
- [x] Remove the spec-016 scaffold TODOs at this site (rev6 L2) — covers the 18 TODO stubs in `tests/test_list_field.py` as they get replaced with real test bodies.

---

## Build report (Worker 2)

### Files touched

- `tests/test_list_field.py` — appended the 14 Slice-3 behavior tests below the existing Slice-2 validation cluster (one-to-one with the spec Test plan at lines 739-752; one-to-one with the scaffold's 14 TODO blocks). Replaced every `# TODO(spec-016, Slice 3 ...)` marker; zero spec-016 TODOs remain in the file (`grep -c "TODO(spec-016" tests/test_list_field.py` → `0`). Added the imports the Slice-3 tests need (`from types import SimpleNamespace`, `from typing import Any`, `import strawberry`, `from apps.products import services`, `from apps.products.models import Item`, `from asgiref.sync import sync_to_async`, `from strawberry.types import Info`, plus `DjangoOptimizerExtension` + `finalize_django_types` from the package root); the existing Slice-2 imports (`Category`, `DjangoListField`, `DjangoType`, `ConfigurationError`, `registry`) and the autouse `_isolate_global_registry` fixture stayed in place.

### Tests added or updated

- `tests/test_list_field.py::test_djangolistfield_default_resolver_returns_queryset_filtered_by_get_queryset` — pins the sync default-resolver path (`list_field.py:101`); the type's sync `get_queryset` excludes Categories whose names start with `"a"` and the assertion confirms none of those rows survive.
- `tests/test_list_field.py::test_djangolistfield_async_get_queryset_is_awaited` — pins the async default-resolver path (`list_field.py:94-100`); declares an `async def get_queryset` and executes via `await schema.execute(...)`; the rows whose names start with `"a"` are filtered out, proving the coroutine was awaited.
- `tests/test_list_field.py::test_djangolistfield_default_resolver_works_under_sync_and_async_schema_execution` — pins both arms of the runtime `in_async_context()` branch at `list_field.py:95` against a SYNC `get_queryset`; runs the same query through `schema.execute_sync` and `await schema.execute` and asserts both return identical filtered data (rev5 M3 dual-execution test).
- `tests/test_list_field.py::test_djangolistfield_sync_path_rejects_coroutine_from_get_queryset` — pins the coroutine-rejection guard at `types/relay.py:213-221`; asserts the GraphQL error message contains the verbatim leading substring `returned a coroutine in a sync resolver context`.
- `tests/test_list_field.py::test_djangolistfield_consumer_resolver_queryset_return_gets_get_queryset_applied` — pins the sync consumer-resolver wrapper at `list_field.py:120-125`; a sync consumer returning `Category.objects.all()` has `get_queryset` applied (the `"a"`-prefixed rows are filtered out).
- `tests/test_list_field.py::test_djangolistfield_consumer_resolver_python_list_return_passes_through` — pins the Python-`list` pass-through arm at `list_field.py:36`; a sync consumer returning `list(Category.objects.all())` keeps the `"a"`-prefixed rows.
- `tests/test_list_field.py::test_djangolistfield_async_consumer_resolver_queryset_return_gets_get_queryset_applied` — pins the async consumer-resolver wrapper at `list_field.py:108-117`; an `async def` consumer's awaited QuerySet return receives `target_type.get_queryset(...)` (rev4 H2 await-then-isinstance ordering).
- `tests/test_list_field.py::test_djangolistfield_async_consumer_resolver_python_list_return_passes_through` — pins the async pass-through arm at `list_field.py:44`; an `async def` consumer returning a Python `list` keeps the `"a"`-prefixed rows.
- `tests/test_list_field.py::test_djangolistfield_at_root_position_is_optimized` — pins the rev2 M3 root-only contract; exact `assertNumQueries(2)` (1 base SELECT + 1 prefetch SELECT, derivation pinned in the docstring per rev6 M6); asserts `ctx.dst_optimizer_plan.prefetch_related` is a single `Prefetch` object with `prefetch_to == "items"`.
- `tests/test_list_field.py::test_djangolistfield_nullable_outer_via_consumer_annotation` — pins `list[CategoryType] | None` rendering to `[CategoryType!]` via an introspection query against `__type(name: "Query")` (rev6 M2 — no `str(schema)` substring matching).
- `tests/test_list_field.py::test_djangolistfield_non_nullable_outer_default_via_consumer_annotation` — pins `list[CategoryType]` rendering to `[CategoryType!]!` via the same introspection-query mechanism with the four-level wrap shape from spec line 109.
- `tests/test_list_field.py::test_djangolistfield_fk_id_elision_survives` — pins FK-id elision under `DjangoListField`; the assertion shape mirrors `tests/optimizer/test_extension.py:317-325` exactly (`select_related == ()`, `prefetch_related == ()`, `only_fields == ("name", "category_id")`, `fk_id_elisions == ("ItemType.category@allItems.category",)`).
- `tests/test_list_field.py::test_djangolistfield_with_meta_primary_true_returns_primary_queryset` — pins Decision 6; two `DjangoType`s on `Category` with distinct `get_queryset` filters (primary excludes `"a"`-prefixed; secondary excludes `"b"`-prefixed); pointing `DjangoListField` at the primary picks the primary's filter (only `"b"`-prefixed survive the secondary's would-have-filtered group; `"a"`-prefixed are absent).
- `tests/test_list_field.py::test_djangolistfield_with_secondary_target_uses_secondary_get_queryset` — same fixture shape as the previous test but the field targets the secondary; the secondary's filter fires (no `"b"`-prefixed rows; `"a"`-prefixed rows survive, proving the registry's `Meta.primary` discriminator did NOT override the explicit-target argument).

### Validation run

- `uv run ruff format .` — pass (`103 files left unchanged`).
- `uv run ruff check --fix .` — pass (`All checks passed!`).
- `git status --short` — `M tests/test_list_field.py` (one file). Classified slice-intended (lands in `### Files touched`). The Slice 1 / Slice 2 files (`django_strawberry_framework/__init__.py`, `django_strawberry_framework/list_field.py`, `tests/base/test_init.py`) are already in HEAD and were not modified in this pass. No unrelated tool churn.
- `uv run pytest --no-cov tests/test_list_field.py` — **21 passed in 2.15s**. The 21 includes the 4 parametrized non-class-rejection cases (one `test_djangolistfield_rejects_non_class_argument[...]` per parameter id) + the 3 other Slice-2 validation tests + the 14 Slice-3 behavior tests. The pytest output line above is the verbatim summary.
- `uv run pytest --no-cov tests/base/test_init.py` — **4 passed in 0.04s**. Slice 1's `__all__` pin survives unchanged.

### Implementation notes

- **Class names dropped the leading underscore** (`CategoryType`, `ItemType`, `PrimaryCategoryType`, `SecondaryCategoryType`) rather than the plan's discretionary `_CategoryType` shape. Justification: Strawberry uses `cls.__name__` as the GraphQL type name when `Meta.name` is unset, and a leading underscore propagates into the schema (`_CategoryType` as a GraphQL type name). The leading underscore is allowed by the GraphQL spec but reads as an introspection-leaked Python implementation detail; matching `tests/optimizer/test_extension.py`'s `CategoryType` / `ItemType` convention keeps the schema clean. The plan listed this as Worker-2-discretionary (artifact line 210); the existing optimizer-test convention dominated the call.
- **`Prefetch`-object assertion shape for the root-position optimizer test.** The plan's recommended assertion was `ctx.dst_optimizer_plan.prefetch_related == ("items",)`, but the optimizer emits a `Prefetch` instance (not a string) when reverse-FK chains land in the plan — verified at execution time. The assertion was adjusted to mirror `tests/optimizer/test_extension.py:2286-2288`'s shape: `len(plan.prefetch_related) == 1`, `isinstance(plan.prefetch_related[0], Prefetch)`, `plan.prefetch_related[0].prefetch_to == "items"`. The plan flagged this as a discretionary call (artifact line 214) and explicitly authorized the pattern-match against `tests/optimizer/test_extension.py:320-325`.
- **`DJANGO_ALLOW_ASYNC_UNSAFE=true` via `monkeypatch.setenv` in three async tests** (`test_djangolistfield_async_get_queryset_is_awaited`, `test_djangolistfield_default_resolver_works_under_sync_and_async_schema_execution`, `test_djangolistfield_async_consumer_resolver_queryset_return_gets_get_queryset_applied`). Strawberry's `complete_list_value` iterates the returned QuerySet synchronously inside the async event loop; Django's `SynchronousOnlyOperation` guard raises without this override. The contract under test is the `DjangoListField` async dispatch (whether `_apply_get_queryset_async` was awaited and `get_queryset` applied to the resulting queryset), NOT Django's async-ORM rules — the env-var override unblocks the downstream iteration so the field's contract is exercisable end-to-end through `await schema.execute(...)`. The fourth async test (`test_djangolistfield_async_consumer_resolver_python_list_return_passes_through`) returns a pre-evaluated Python `list` and doesn't need the override. Each affected test docstring documents the override and its rationale.
- **`monkeypatch.setenv` parameter** is left unannotated to match the existing pytest-monkeypatch convention in the project (e.g., `tests/test_registry.py:` uses bare `monkeypatch`).
- **Filter discriminator: `name__startswith="a"` / `"b"`** — `services.seed_data(1)` populates `Category.name` from Faker provider names (`address`, `automotive`, `bank`, `barcode`, ...), so excluding `"a"`-prefix removes `address` + `automotive` (deterministic across runs; verified via the provider walk in `examples/fakeshop/apps/products/services.py:165`). The `Meta.primary` tests use distinct prefixes (`"a"` for primary, `"b"` for secondary) so each test can prove the other type's filter did NOT fire by checking that one prefix survived.
- **`finalize_django_types()` placement** — every behavior test calls it BETWEEN the inline `class CategoryType(DjangoType)` declarations and `strawberry.Schema(query=Query, ...)`. The Slice-0 carry-forward (Worker 2 memory) flagged that without the finalize step, schema construction fails with `TypeError: Unexpected type ...` because `DjangoType` subclasses are not auto-`@strawberry.type`-decorated at class-creation time. Inline `finalize_django_types()` calls satisfy this without an extra fixture.
- **Introspection-query string inlined at both nullability test sites** rather than hoisted to a module-level constant. The two query strings differ by one nesting level (three vs four `ofType` chains) and the duplication reads cleanly inline; hoisting to a constant would force a parametrize-id, which obscures the load-bearing shape difference.

### Notes for Worker 3

- **No production code under `django_strawberry_framework/` changed.** Slice 3 is tests-only. The system-under-test (`list_field.py:1-135` post-Slice-2) is the same surface Slice 2's review accepted. The 14 new tests exercise the surface through `schema.execute_sync(...)` / `await schema.execute(...)` against real Django models (the `apps.products` fixture from `AGENTS.md` line 6).
- **`assertNumQueries(2)` derivation pinned in the test docstring per rev6 M6** — the docstring spells out "1 base SELECT + 1 SELECT per `prefetch_related` relation". A future selection-shape change (e.g., adding a second nested prefetch relation) requires the maintainer to recompute `N` and update the test; the docstring keeps that derivation visible at the test site.
- **FK-id elision assertion mirrors `tests/optimizer/test_extension.py:317-325`** byte-for-byte except for the swap from `@strawberry.field`-served `all_items` to `DjangoListField(ItemType)`-served `all_items`. The resolver key (`ItemType.category@allItems.category`) is identical between the two tests because the underlying selection shape and field name match. If the optimizer's resolver-key shape changes in a future patch, the existing `tests/optimizer/test_extension.py:324-325` lines update at the same time as this test.
- **No temp tests under `docs/builder/temp-tests/slice-3/`** — the 14 pinned tests are direct exercises of the production contract; no scratchpad helpers were needed.
- **Static helper run** — not re-run for `list_field.py` in this Slice 3 build pass (the Slice 2 helper run captured the post-Slice-2 surface; Slice 3 didn't touch production code). The Worker 1 plan referenced the Slice-2 shadow output for ORM-marker coverage planning; Worker 3 should treat the Slice-2 shadow at `docs/shadow/django_strawberry_framework__list_field.overview.md` as the authoritative reference.

### Notes for Worker 1 (spec reconciliation)

No spec reconciliation needed. The 14 behavior tests landed against the spec contract exactly as Worker 1's plan called for, with two small discretionary deviations recorded in `### Implementation notes` (the class-name underscore drop and the `Prefetch`-object assertion shape) — both of which the plan explicitly flagged as Worker-2-discretionary at artifact lines 210 and 214. The `DJANGO_ALLOW_ASYNC_UNSAFE` test override is a test-infrastructure detail (not a contract change); the spec's Edge cases section (spec line 697) promises the dual-execution dispatch works, and the override is the documented Django-side bypass for the unrelated sync-ORM-in-async-context guard. No spec edit is required.

---

## Review (Worker 3)

### High:

None.

### Medium:

None.

### Low:

#### Local `Prefetch` import inside test body

`tests/test_list_field.py:554` imports `from django.db.models import Prefetch` inside the test function rather than at module top. The rest of the file consistently imports at the top (`models.QuerySet`, `Category`/`Item` from `apps.products.models`, etc.). The local import is functional and the assertion that follows is correct, but the convention drift reads as a Slice 2-style top-of-file import would be cleaner. Severity is Low because the import is one line and pytest collection is not affected; the test still passes (verified) and the production contract is exercised correctly. Recommended change (non-blocking): hoist to the top of the file alongside the other Django imports. Worker 1 may pick this up at the integration pass or leave it as is.

### DRY findings

- **`_isolate_global_registry` two-site duplication** — `tests/test_list_field.py:35-45` and `tests/test_registry.py:34-39` both declare a bytewise-identical autouse fixture. Per the new AGENTS.md directive, I assessed whether consolidation into `tests/conftest.py` is the right fix in this slice. Result: **the duplication is part of a repo-wide pre-existing pattern, not a Slice 3 introduction**. Thirteen test files under `tests/` carry their own autouse registry-clear fixture (verified via `grep -rln "autouse=True"` then filtering for `registry.clear`); consolidating only the `test_list_field.py` + `test_registry.py` pair would leave eleven sibling sites still duplicating the same shape, producing inconsistency rather than reducing it. The right fix is a repo-wide consolidation that touches all 13 files in a single change — outside Slice 3's tests-only scope and outside spec-016's contract. Slice 3 inherits the pattern from Slice 2 (which inherited it from the broader codebase); no in-slice action is correct. Flagged here so Worker 1 can record it as a candidate for a separate refactor spec when the maintainer prioritizes the cleanup.
- **No new duplication introduced.** Inline `class _CategoryType(DjangoType): ...` declarations across the 14 tests (per Worker 1's plan, artifact line 27) keep each test's semantics self-contained; the four ORM-filter discriminators (`name__startswith="a"`/`"b"`) and the inline `finalize_django_types()` + `strawberry.Schema(...)` pattern are intentional repetition that keeps each test self-readable. Worker 1's plan justified this at artifact lines 26-29 and the result reads cleanly. Hoisting a `make_django_type(...)` helper would over-abstract; keep the inline shape.
- **Introspection-query strings duplicated across the two nullability tests** — Worker 2 chose inline (per the plan's recommendation at artifact line 36 and discretion item at line 213) rather than hoisting to a module-level constant. The two query strings differ by one `ofType` nesting level (three vs four), which is load-bearing — hoisting would force a parametrize-id that obscures the shape difference. Inline is the correct call.

### Public-surface check

`git diff HEAD -- django_strawberry_framework/__init__.py` is empty. The Slice 1 addition (`"DjangoListField"` in `__all__`) is unchanged. No new public exports added by Slice 3 (tests-only slice). Spec-authorized: Slice 3 checklist at spec lines 139-141 does not authorize any public-surface change.

### CHANGELOG sanity

Not applicable; slice did not modify `CHANGELOG.md`.

### Documentation / release sanity

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces.

### What looks solid

- **All 14 spec-pinned test names matched verbatim** — grep against the 14 method names in spec lines 739-752 produces 14 matches in the file, in spec Test plan order. No name was shortened, expanded, or reordered.
- **`assertNumQueries` derivation in docstring** — `test_djangolistfield_at_root_position_is_optimized:513-519` spells out "N = 1 base SELECT + 1 SELECT per `prefetch_related` relation in the nested selection. For `{ allCategories { id name items { id name } } }` against `Category` with `items` as a reverse-FK, N = 2". The derivation is rigorous, falsifiable, and lets a future maintainer recompute N when the selection shape changes. Pinned via exact `django_assert_num_queries(2)`, not a `<= N` bound (rev6 M6 contract honored).
- **Introspection-query mechanism for nullability** — both `test_djangolistfield_nullable_outer_via_consumer_annotation` and `test_djangolistfield_non_nullable_outer_default_via_consumer_annotation` use `{ __type(name: "Query") { fields { name type { kind ofType { ... } } } } }` with `kind`/`ofType` traversal asserting `NON_NULL` / `LIST` / `OBJECT` at the correct depths. No `print(schema)` or `str(schema)` substring matching (rev6 M2 contract honored). The load-bearing difference (outer `NON_NULL` present vs absent) is explicitly called out in the test bodies.
- **Coroutine-rejection test pins production message verbatim** — `test_djangolistfield_sync_path_rejects_coroutine_from_get_queryset:317` asserts `"returned a coroutine in a sync resolver context" in str(result.errors[0])`, which is the exact leading substring from `types/relay.py:215-217` (`_apply_get_queryset_sync`). This proves `DjangoListField` reuses the production helper unchanged rather than re-rolling the rejection. The same `ConfigurationError` shape Relay code uses fires.
- **`Meta.primary` pair uses two DjangoTypes on the same model** — both `test_djangolistfield_with_meta_primary_true_returns_primary_queryset` and `test_djangolistfield_with_secondary_target_uses_secondary_get_queryset` declare `PrimaryCategoryType(DjangoType)` with `primary = True` and `SecondaryCategoryType(DjangoType)` (no primary) on the same `Category` model. Decision 6 contract honored — the explicit-target shape is the discriminator, not the registry's primary lookup.
- **FK-id elision assertion observes the elision, not return values** — `test_djangolistfield_fk_id_elision_survives:681-685` asserts `plan.select_related == ()`, `plan.prefetch_related == ()`, `plan.only_fields == ("name", "category_id")`, and `plan.fk_id_elisions == ("ItemType.category@allItems.category",)`. This mirrors `tests/optimizer/test_extension.py:317-325` byte-for-byte (modulo `@strawberry.field` → `DjangoListField(ItemType)`) — the assertion captures the optimizer plan internals, not just whether rows came back.
- **rev5 M3 14th test exercises BOTH execution paths** — `test_djangolistfield_default_resolver_works_under_sync_and_async_schema_execution:269-272` runs the same query through `await sync_to_async(schema.execute_sync)(...)` AND `await schema.execute(...)`, then asserts `sync_result.data == async_result.data`. Both arms of the `in_async_context()` branch at `list_field.py:95` fire under the same factory output, which is the rev5 H2 async-detection-asymmetry contract.
- **Async tests use `pytest-asyncio` auto-mode convention** — every `async def test_...` (lines 180, 231, 410, 454) relies on `pytest.ini`'s `asyncio_mode = auto`; no `asyncio.run(...)` inline, no `async_to_sync` rewrapping. ORM access inside async tests is properly wrapped with `sync_to_async(...)` (matches the spec's user-facing example at lines 305-313).
- **rev6 L2 scaffold-TODO sweep complete** — `grep -c "TODO" tests/test_list_field.py` returns 0; `grep -n "TODO(spec-016" tests/test_list_field.py` returns nothing. Only docstring references to `spec-016-list_field-0_0_7.md` remain (line 3, expected). Worker 2's build report (`grep -c "TODO(spec-016" tests/test_list_field.py → 0`) confirmed.
- **No production code changes** — `git diff HEAD -- django_strawberry_framework/` is empty. Slice 3 is tests-only as the spec requires.
- **Focused test sweep confirms all pass** — `uv run pytest --no-cov tests/test_list_field.py` returns 21 passed (14 Slice 3 + 4 validation incl. the 4 parametrize variants of `rejects_non_class_argument`). No skips, no errors.

### Temp test verification

- No temp test files created under `docs/builder/temp-tests/slice-3/`. The 14 pinned tests are direct exercises of the production contract through `schema.execute_sync(...)` / `await schema.execute(...)`; no scratchpad helpers were justified during review. Confirmed `docs/builder/temp-tests/` contains only the pre-existing empty `slice-0/` subdirectory.

### Static helper invocations

- Ran `uv run python scripts/review_inspect.py django_strawberry_framework/list_field.py --output-dir docs/shadow` to refresh the post-Slice-2 surface. Output at `docs/shadow/django_strawberry_framework__list_field.{overview.md,stripped.py}`. The diff against the Slice 2 shadow shows zero structural change (production source unchanged; Slice 3 ships tests only). Used only for confirmation that no production drift slipped in.
- Helper SKIPPED for `optimizer/extension.py` with reason: slice does not touch `optimizer/extension.py`; helper not required (BUILD.md's "touches an existing `.py` file under `optimizer/`" trigger does not fire).
- Helper SKIPPED for `tests/test_list_field.py` with reason: test file; not part of the package's review-worthy logic surface per Worker 3's role-file note. The file's logic is non-trivial (autouse fixture, parametrize tables, async tests, Django ORM access, `assertNumQueries` plumbing) but the role file's test-tree exemption applies and the per-test walk above covers the assertion shapes directly.

### Notes for Worker 1 (spec reconciliation)

- **No spec edits required.** The 14 tests landed against the spec contract verbatim; all calibration points in the prompt (assertNumQueries derivation, introspection mechanism, async convention, Meta.primary fixture shape, coroutine-rejection message, FK-id elision observation, dual-execution coverage) check out.
- **`_isolate_global_registry` consolidation** is a candidate refactor spec — 13 sites duplicate the autouse pattern repo-wide, not a Slice 3 churn. The right fix is a separate slice (or its own spec) that consolidates all 13 sites at once. Slice 3 is correct to leave the pattern in place rather than partial-consolidate.
- **`Prefetch` import location** (Low finding above) is the only inline polish opportunity. Worker 1 may fold it into the integration pass or defer; it does not affect the contract.

### Review outcome

`review-accepted` — every spec slice sub-bullet (spec lines 139-141) is addressed in the diff: the 14 named behavior tests land verbatim with correct assertion shapes; the rev6 L2 scaffold-TODO sweep is complete (`grep -c "TODO" tests/test_list_field.py` returns 0). Zero High findings, zero Medium findings, one Low (non-blocking import-location polish). DRY findings recorded as repo-wide pattern observations, not Slice 3 defects. Public-surface check clean. No CHANGELOG / docs / KANBAN changes in scope. The 21 focused tests pass (`uv run pytest --no-cov tests/test_list_field.py` → 21 passed in 2.20s). Production source is byte-for-byte unchanged (`git diff HEAD -- django_strawberry_framework/` empty).

---

## Final verification (Worker 1)

- Spec slice checklist: both `- [ ]` boxes in the Plan's `### Spec slice checklist (verbatim)` ticked `- [x]` — the 14 verbatim test names land at the file (verified by `grep -n "^def test_djangolistfield_\|^async def test_djangolistfield_" tests/test_list_field.py` returning 18 hits: 4 Slice-2 validation + 14 Slice-3 behavior cases pinned at spec lines 739-752), and the rev6 L2 scaffold-TODO sweep is complete at this site (`grep -c "TODO" tests/test_list_field.py` → 0). No silently un-ticked sub-checks.
- DRY check across this slice and prior accepted slices: no new duplication introduced. The `_isolate_global_registry` two-site duplication is part of a pre-existing 13-site repo-wide pattern (Worker 3 confirmed via `grep -rln "autouse=True"` + `registry.clear` walk); consolidating only the Slice-3 pair would leave 11 sibling sites duplicating the same shape and produce inconsistency rather than reduce it. The right fix is a repo-wide consolidation slice that touches all 13 sites in one change — outside Slice 3's tests-only scope and outside spec-016's contract. Worker 3's rejection of the consolidation as out-of-slice work stands under the new AGENTS.md directive; the directive's "always recommend the root-cause fix" clause is honored by surfacing the consolidation candidate for a separate refactor spec rather than partial-fixing here. The inline `class _CategoryType(DjangoType): ...` per-test declarations, the inline `finalize_django_types()` + `strawberry.Schema(...)` schema-build pattern, and the duplicated introspection-query strings across the two outer-nullability tests are all intentional repetition (justified at artifact lines 26-36 and confirmed by Worker 3 at artifact lines 308-310); none introduce a new pattern that consolidates to a helper without obscuring the per-test semantics.
- Existing tests still pass:
  - `uv run pytest --no-cov tests/test_list_field.py` → **21 passed in 2.06s** (4 Slice-2 validation parametrized cases + 3 other Slice-2 validation tests + 14 Slice-3 behavior tests).
  - `uv run pytest --no-cov tests/base/test_init.py` → **4 passed in 0.04s** (Slice-1's `__all__` pin survives unchanged).
- Spec reconciliation: no spec edits required for Slice 3. Worker 2's and Worker 3's `### Notes for Worker 1 (spec reconciliation)` sections both reported nothing actionable; the 14 tests landed against the spec contract verbatim. Worker 2's two discretionary deviations (dropping the underscore prefix from inline `DjangoType` class names; `Prefetch`-object assertion shape pattern-matched against `tests/optimizer/test_extension.py:320-325`) were both authorized by Worker 1's plan at artifact lines 210, 214. The `DJANGO_ALLOW_ASYNC_UNSAFE` env-var override in three async tests is a Django-side sync-ORM-in-async-context bypass (not a contract surface) and matches the spec's documented dual-execution shape at spec line 697. Spec status line at line 4 (`draft (revision 6, post-rev5 scaffolding review)`) re-verified accurate at the start of this pass; no edit needed.
- Final status: `revision-needed`. See "Low finding decision" below for the calibration under the new AGENTS.md directive.

### Low finding decision (under the AGENTS.md root-cause-fix directive)

Worker 3's single Low finding (`tests/test_list_field.py:554` imports `from django.db.models import Prefetch` inline inside `test_djangolistfield_at_root_position_is_optimized` rather than at the top of the file alongside the existing Django imports) is **not accepted as the correct shape**. The inline placement has no justifying constraint:

- No circular-import concern (`Prefetch` is a pure Django ORM symbol; the test module already imports `apps.products.models` at line 21, which transitively requires Django to be configured).
- No conditional or parametrization-driven import; `Prefetch` is used at exactly one site, on exactly one assertion path, in exactly one test (verified by `grep -n "Prefetch" tests/test_list_field.py` returning three hits — one comment, one inline import, one isinstance check).
- No lazy-import cost-deferral motive; the file already imports `strawberry`, `asgiref.sync.sync_to_async`, and the `django_strawberry_framework` package at module load.
- The file's existing convention is to import at the module top (lines 15-32 group standard-library, third-party, and first-party imports per the prevailing alphabetical-within-group shape; the Slice-2 cluster and the other 13 Slice-3 tests all follow it).

Under the new AGENTS.md directive (line 4: "Code is held to the highest standard always; always recommend the root-cause fix over the surface patch; ... if a lower-quality option is mentioned at all it is named as the wrong choice, not offered as a tradeoff"), the inline import is the lower-quality shape. The root-cause-correct fix is to hoist `from django.db.models import Prefetch` to the module's top-of-file imports (alongside `from strawberry.types import Info` at line 23, in the same third-party-grouping band). This is a one-line edit; Worker 2's adjustment pass moves the import and removes the inline statement at the original site. The directive explicitly forbids accepting a Low when the right fix is a slice-local one-line edit, and it forbids deferring as "follow-up" — either the Low lands here, or it's explicitly rejected as the correct shape. There is no reason to reject; therefore Worker 2 fixes it.

Worker 0 dispatches Worker 2 for the adjustment pass; Worker 3 re-reviews; Worker 1 returns for a second final-verification.

### Summary

Slice 3 ships the 14 pinned behavior tests for `DjangoListField`'s `get_queryset` cooperation and root-position optimizer planning — one-to-one with the spec Test plan at lines 739-752 across eight clusters (default sync + async, rev5 M3 dual-execution, rev2 H1 sync consumer x2, rev4 H2 async consumer x2, rev6 M2 introspection-shape outer-nullability x2, rev2 M3 root-position optimization with exact `assertNumQueries(2)` per rev6 M6, FK-id elision mirroring `tests/optimizer/test_extension.py:317-325`, Decision 6 `Meta.primary` primary + secondary). The rev6 L2 scaffold-TODO sweep is complete (0 TODOs remain). No production code under `django_strawberry_framework/` changes — `list_field.py`, `__init__.py`, `relay.py`, and `extension.py` are byte-for-byte unchanged at HEAD. All 21 focused tests pass; the Slice-1 `__all__` pin survives. The slice is one inline-import-location polish away from `final-accepted`; under the new AGENTS.md directive the polish lands in this slice rather than being deferred.

### Spec changes made (Worker 1 only)

No spec edits required for Slice 3.

---

## Build report (Worker 2, pass 2)

### Files touched

- `tests/test_list_field.py` — one-line hoist of `Prefetch` to the module-top third-party import band (new line `from django.db.models import Prefetch` inserted between the existing `from asgiref.sync import sync_to_async` and `from strawberry.types import Info` to preserve the file's prevailing alphabetical-within-group import ordering); deleted the inline `from django.db.models import Prefetch` statement inside `test_djangolistfield_at_root_position_is_optimized` at the original line 554. Net change: `+1 -1`.

### Tests added or updated

No tests added or updated; the one-line hoist preserves existing tests.

### Validation run

- `uv run ruff format .` — pass (`103 files left unchanged`).
- `uv run ruff check --fix .` — pass (`All checks passed!`).
- `git status --short` — three files modified:
  - `tests/test_list_field.py` — **slice-intended** (the one-line hoist + inline-import delete; lands in `### Files touched`).
  - `docs/builder/bld-slice-3-optimizer_get_queryset_tests.md` — **slice-intended** (this pass-2 build report append + `Status: built` flip).
  - `AGENTS.md` — **inherited maintainer state; out of Slice 3 scope** (concurrent maintainer edit per Worker 1's final-verification note; not touched by this pass).
  - (Worker 1's note also called out `django_strawberry_framework/types/base.py` as inherited maintainer state; at the time this pass-2 ran, that file is no longer in `git status --short` — the maintainer-state change appears to have been resolved between pass-1 and pass-2. Either way, Slice 3 did not touch it.)
  - No unrelated tool churn; no files to revert.
- `uv run pytest --no-cov tests/test_list_field.py` — **21 passed in 2.05s** (4 Slice-2 validation parametrized cases + 3 other Slice-2 validation tests + 14 Slice-3 behavior tests). No skips, no errors. The previously-failing-shape `Prefetch` assertion still resolves correctly with the module-top import.

### Implementation notes

- **Hoist landed on its own dedicated line** (`from django.db.models import Prefetch`) rather than consolidating into an existing `from django.db.models import ...` line. Rationale: no such line exists at HEAD — `Prefetch` is the first `django.db.models` symbol the test module imports. The file's prevailing import convention is one alphabetical entry per third-party / first-party module (lines 18-23 follow `apps.products`, `apps.products.models`, `asgiref.sync`, `strawberry.types` — one `from X import Y` line per module path). Inserting between `asgiref.sync` and `strawberry.types` preserves the alphabetical ordering (`asgiref` < `django.db.models` < `strawberry.types`). If a future test needs additional `django.db.models` symbols (e.g., `F`, `Q`), that change consolidates onto this line.

### Notes for Worker 3

- This is **pass-2**; the pass-1 review's single Low finding (inline `from django.db.models import Prefetch` at the original line 554) is addressed. The diff is one-line insert at the import band + one-line delete at the original inline-import site (plus the surrounding comment block stays — it explains why `Prefetch` is being checked at all, which is orthogonal to where the import lives). Net diff against the pass-1-built `tests/test_list_field.py`: `+1 -1`. The 21-test focused sweep still passes.
- No new shadow-file run; the production surface is byte-for-byte unchanged across pass-1 and pass-2 (`git diff HEAD -- django_strawberry_framework/` continues to be empty modulo the inherited `types/base.py` maintainer state, which this pass did not touch).

### Notes for Worker 1 (spec reconciliation)

No spec reconciliation needed; pass-2 is a stylistic import-placement fix.

---

## Review (Worker 3, pass 2)

### High:

None.

### Medium:

None.

### Low:

None.

### Diff scope confirmation

Pass-2's delta against the pass-1-built file is **`+1 -1`** — the one-line hoist plus the one-line inline-import deletion — exactly the shape promised in Worker 2's pass-2 build report.

- The new module-top import lands at `tests/test_list_field.py:23` as `from django.db.models import Prefetch`, inserted between `from asgiref.sync import sync_to_async` (line 22) and `from strawberry.types import Info` (line 24). Alphabetical ordering by module path is preserved (`asgiref` < `django.db.models` < `strawberry.types`); the third-party-grouping band stays intact.
- The inline `from django.db.models import Prefetch` statement inside `test_djangolistfield_at_root_position_is_optimized` is gone. `grep -n "Prefetch" tests/test_list_field.py` returns exactly three hits: line 23 (the new module-top import), line 551 (an unchanged comment block explaining the `Prefetch` object shape — the comment text refers to "``Prefetch``" as a type, not as an import), and line 556 (the `isinstance(plan.prefetch_related[0], Prefetch)` assertion). No fourth hit means no inline import survived; no second `from django.db.models import Prefetch` line exists.
- The test that previously hosted the inline import (`test_djangolistfield_at_root_position_is_optimized`) still uses the `Prefetch` symbol at line 556 — Worker 2 did not delete the usage along with the inline import. The surrounding comment block (lines 550-554) explaining why `Prefetch` is checked stays in place, which reads correctly.
- `git status --short` shows three files modified: `tests/test_list_field.py` (pass-2 hoist), `docs/builder/bld-slice-3-optimizer_get_queryset_tests.md` (pass-2 build report + Status flip + this Review section), and `AGENTS.md` (inherited maintainer state from a concurrent edit, explicitly called out by the prompt as out of scope for Slice 3 review). `django_strawberry_framework/types/base.py` was called out by the prompt as possibly present in inherited state but is not in `git status --short` at this pass-2 review time — either way, Slice 3 did not touch it. No scope violation; pass-2 is correctly bounded to the test file's import band + the inline-import deletion.

### DRY findings

No new DRY findings. Pass-2 is a single-symbol hoist — it does not add any new patterns, helpers, fixtures, or duplicated literals. The pass-1 DRY assessment stands: the `_isolate_global_registry` autouse fixture remains the only candidate for repo-wide consolidation (13 sites), still out of Slice 3's scope.

### Public-surface check

`git diff HEAD -- django_strawberry_framework/__init__.py` is empty. The Slice 1 addition (`"DjangoListField"` in `__all__`) is unchanged. Pass-2 adds no public-surface change; spec-authorized as a tests-only adjustment.

### CHANGELOG sanity

Not applicable; pass-2 did not modify `CHANGELOG.md`.

### Documentation / release sanity

Not applicable; pass-2 did not modify docs/release/KANBAN/archive surfaces.

### What looks solid

- **Surgical `+1 -1` shape** — pass-2 is exactly one line inserted at the import band and one line deleted at the original inline-import site. No surrounding refactor, no comment churn, no whitespace adjustments. The pass-2 delta is the minimum viable fix for the pass-1 Low finding.
- **Alphabetical ordering preserved** — the new `from django.db.models import Prefetch` lands between `asgiref.sync` and `strawberry.types` (`a*` < `d*` < `s*`), matching the file's prevailing one-module-per-line third-party convention.
- **Symbol usage preserved** — the test body that previously held the inline import (`test_djangolistfield_at_root_position_is_optimized`) still references `Prefetch` at the `isinstance` check on line 556. Worker 2 did not collateral-delete the usage; the comment block at lines 550-554 explaining the `Prefetch`-object emission stays untouched and accurate.
- **All 21 focused tests still pass** — `uv run pytest --no-cov tests/test_list_field.py` returns `21 passed in 2.09s` (4 Slice-2 validation parametrized cases + 3 other Slice-2 validation tests + 14 Slice-3 behavior tests). The previously-passing `Prefetch`-assertion shape continues to resolve correctly with the module-top import; pytest collection is unaffected.
- **Convention drift fixed at root cause** — the inline import was the only convention-drift site in the file; the rest of the third-party imports (`pytest`, `strawberry`, `apps.products.services`, `apps.products.models.Category`/`Item`, `asgiref.sync.sync_to_async`, `strawberry.types.Info`) already lived in the module-top band. The hoist restores file-wide consistency rather than introducing a new pattern.

### Temp test verification

No temp test files created under `docs/builder/temp-tests/slice-3/`; the `slice-3/` subdirectory does not exist (`ls docs/builder/temp-tests/` shows only the pre-existing `slice-0/`). Pass-2 is a one-line hoist; no scratchpad helpers were needed, consistent with the prompt's guidance.

### Static helper invocations

- Static inspection helper SKIPPED for pass-2 with reason: "pass-2 is a one-line import hoist; no logic change, helper not applicable." The pass-1 review already refreshed the post-Slice-2 shadow at `docs/shadow/django_strawberry_framework__list_field.{overview.md,stripped.py}`; production source is byte-for-byte unchanged across pass-1 and pass-2, so the shadow remains current.

### Notes for Worker 1 (spec reconciliation)

No spec reconciliation needed. Pass-2 is a mechanical import-placement adjustment; the spec contract is unchanged from pass-1's `review-accepted-modulo-Low` state to pass-2's `review-accepted`. No spec edits required.

### Review outcome

`review-accepted` — the pass-1 Low finding is addressed at the right shape (root-cause hoist to the module-top third-party band, not a workaround or deferral); the pass-2 delta is exactly `+1 -1` against the pass-1-built file; the `Prefetch` symbol's single in-test usage and surrounding documentation comment are preserved; the 21 focused tests pass; production code stays byte-for-byte unchanged; no new findings at any severity (0 High, 0 Medium, 0 Low). Pass-2 closes Slice 3 cleanly under the new AGENTS.md directive's root-cause-fix calibration.

---

## Final verification (Worker 1, pass 2)

- Spec slice checklist: both `- [ ]` boxes at spec lines 140-141 were left un-ticked at the pass-1 final-verification because `revision-needed` fired before the contract had landed end-to-end (the inline-`Prefetch` Low was the open item). Pass-2's `+1 -1` import hoist closed that gap; this pass-2 final-verification ticks both boxes `- [x]` in the spec to record that the Slice-3 contract has landed (verified by `grep -n "^def test_djangolistfield_\|^async def test_djangolistfield_" tests/test_list_field.py` returning 18 hits — 4 Slice-2 validation + 14 Slice-3 behavior tests pinned at spec lines 739-752; `grep -c "TODO" tests/test_list_field.py` returns 0 — rev6 L2 sweep complete). The Plan's `### Spec slice checklist (verbatim)` ticks at artifact lines 230-231 (set at pass-1 final-verification) match the now-ticked spec boxes; no silently un-ticked sub-checks remain.
- DRY check across this slice and prior accepted slices: pass-2 is a `+1 -1` mechanical hoist — no new patterns, helpers, fixtures, or literals introduced. The pass-1 DRY assessment stands verbatim: the `_isolate_global_registry` autouse fixture is a 13-site repo-wide pattern requiring a separate consolidation spec; inline `class _CategoryType(DjangoType): ...` per-test declarations, inline `finalize_django_types()` + `strawberry.Schema(...)` schema-build pattern, and the two duplicated introspection-query strings across the outer-nullability tests are all intentional repetition justified at artifact lines 26-36 and 308-310. Pass-2 introduced zero new duplication.
- Existing tests still pass:
  - `uv run pytest --no-cov tests/test_list_field.py` → **21 passed in 2.10s** (4 Slice-2 validation parametrized cases + 3 other Slice-2 validation tests + 14 Slice-3 behavior tests). The `Prefetch`-assertion in `test_djangolistfield_at_root_position_is_optimized` resolves correctly using the module-top import.
  - `uv run pytest --no-cov tests/base/test_init.py` → **4 passed in 0.04s**. Slice-1's `__all__` pin survives unchanged.
- Spec reconciliation: pass-2 was a mechanical `+1 -1` import hoist; no spec contract change. Spec status line at line 4 (`draft (revision 6, post-rev5 scaffolding review)`) re-verified accurate at the start of this pass — the header describes the drafting revision, while the per-slice ship state is tracked separately by Worker 0 in the build plan. The two Slice-3 sub-bullets at spec lines 140-141 were ticked `- [x]` in this pass to record the contract landing; recorded under `### Spec changes made (Worker 1 only, pass 2)` below.
- Final status: `final-accepted`. The pass-1 Low (inline `Prefetch` import) was rejected as the wrong shape under the new AGENTS.md root-cause-fix directive; Worker 2's pass-2 hoist landed at the correct shape (module-top third-party band, alphabetical between `asgiref.sync` and `strawberry.types`); Worker 3's pass-2 re-review accepted with 0 H / 0 M / 0 L; this pass-2 final-verification confirms the slice contract is end-to-end clean.

### Summary

Pass-2 shipped a surgical `+1 -1` import hoist: `from django.db.models import Prefetch` moved from inline inside `test_djangolistfield_at_root_position_is_optimized` (test_list_field.py:554 at pass-1) to the module's third-party-import band at `tests/test_list_field.py:23`. The 14 Slice-3 behavior tests pinned at spec lines 739-752 (eight clusters across default sync + async, rev5 M3 dual-execution, rev2 H1 sync consumer x2, rev4 H2 async consumer x2, rev6 M2 introspection-shape outer-nullability x2, rev2 M3 root-position optimization with exact `assertNumQueries(2)` per rev6 M6, FK-id elision mirroring `tests/optimizer/test_extension.py:317-325`, Decision 6 `Meta.primary` primary + secondary) all land cleanly. Production source under `django_strawberry_framework/` is byte-for-byte unchanged across the build; the `__all__` Slice-1 pin survives; rev6 L2 scaffold-TODO sweep is complete. The Slice-3 contract has now landed end-to-end and the slice closes at `final-accepted` under the new AGENTS.md root-cause-fix directive.

### Spec changes made (Worker 1 only, pass 2)

- `docs/spec-016-list_field-0_0_7.md:140-141` — ticked both Slice-3 sub-checklist boxes from `- [ ]` to `- [x]` to record that the Slice-3 contract has landed end-to-end. Pass-1 left these un-ticked because `revision-needed` fired before the contract closed; pass-2's `+1 -1` import hoist closed the remaining gap and pass-2 final-verification ticks them.
- No spec edits required for Slice 3 pass-2 (the box-ticking is checklist hygiene per the BUILD.md "Spec slice checklist (verbatim)" rule, not a contract change).
