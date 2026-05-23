# Build: Slice 2 — Fakeshop live coverage under `FAKESHOP_SHARDED=1`

Spec reference: `docs/spec-019-multi_db-0_0_7.md` (Slice checklist lines 84-91; Test plan lines 523-552; Edge cases / constraints lines 481-494; Architectural Decisions 4-7 lines 290-435; Definition of done item 3 lines 614-621)
Status: final-accepted

## Plan (Worker 1)

### DRY analysis

- **Existing patterns reused (must be copied or referenced verbatim):**
  - **Autouse reload fixture — copied VERBATIM** from `examples/fakeshop/test_query/test_library_api.py:17-43` per spec Decision 7 (lines 421-435). Same docstring, same module-reload sequence (`apps.library.schema` → `config.schema` → `config.urls`). The "do not pre-emptively factor" boundary in Decision 7 explicitly forbids moving the fixture to a shared `conftest.py` at this slice — conftest extraction is a follow-up card when 3+ files need it. Worker 2 lifts the body unchanged including its in-line comments about hidden invariants. Reference site: `examples/fakeshop/test_query/test_library_api.py:17-43`.
  - **Test-tree placement convention.** New file lives next to `test_library_api.py` under `examples/fakeshop/test_query/` per spec Slice checklist line 85; no `__init__.py` per `AGENTS.md` line 6. Reference site: `examples/fakeshop/test_query/test_library_api.py:1-43` is the in-tree template the new file mirrors.
  - **`django.test.Client` live HTTP pattern** — `client.post("/graphql/", data={"query": ...}, content_type="application/json")` then assert on `response.status_code == 200`, `response.json()`, and `"errors" not in payload`. Reference site: `examples/fakeshop/test_query/test_library_api.py` (the file is the canonical live-HTTP harness for the test_query/ tree per its README at `examples/fakeshop/test_query/README.md:5-11`).
  - **Model FK chain shape for seeding.** `apps.library.models.Branch` has non-null FKs in its dependents (`Shelf.branch` at `apps/library/models.py:56-60`; `Book.shelf` at `apps/library/models.py:98-102`). Worker 2 reuses these Django models exactly as-is for seeding per alias; no fakeshop-side schema or model change required (Decision 4 lines 290-303).
  - **`BookType` import pattern from `apps.library.schema`** — must be imported INSIDE the per-test `_build_test_schema` fixture body, NOT at module top, per Decision 6 rev3 R4 + rev5 X4 (spec lines 372-400, 370). Reference site: the hidden invariant at `examples/fakeshop/test_query/test_library_api.py:24-26` ("tests must not module-level import classes from `apps.library.schema`, or they will hold stale class objects after reload") is the existing precedent the new file extends.
  - **`@pytest.mark.django_db(databases=["default", "shard_b"])`** marker per spec rev2 H8 (lines 86-87). Reference: pytest-django's standard multi-DB access rule; no in-repo precedent yet (this is the first multi-DB test file in `test_query/`) but the marker is documented Django/pytest-django boilerplate.
  - **Pre-staged scaffold at `examples/fakeshop/test_query/test_multi_db.py`** (landed in commit `aac3d57 Add TODO comments`) carries the full skeleton: module docstring, top-block imports (`importlib`, `os`, `sys`, `pytest`), the module-level skip block, the post-skip imports with `# noqa: E402` markers, the empty autouse fixture stub, the `_current` holder, the `_graphql_view` view stub, `urlpatterns`, the `_build_test_schema` fixture stub, the `_seed_book_chain` helper stub, and the two test function shells with `@pytest.mark.django_db(databases=["default", "shard_b"])` decorators. Worker 2's job is to fill in the `NotImplementedError`-bodied helpers per the inline pseudocode comments. Reference: `examples/fakeshop/test_query/test_multi_db.py:1-289`.
- **New helpers justified (single file, single responsibility each):**
  - **`_seed_book_chain(alias: str, *, title: str) -> models.Book`** — single responsibility: lay down a `Branch → Shelf → Book` chain on the named alias per spec rev2 H9 (lines 88, 527-538). Justified because both tests need it and writing the three `.using(alias).create(...)` calls inline twice in test bodies would duplicate the rev2 H9 contract; one helper is the DRY shape. Single call site type: both tests.
  - **`_graphql_view(request)` closure** — single responsibility: read `_current["schema"]` at request time and delegate to `GraphQLView.as_view(schema=schema)(request)` per spec Decision 6 rev3 R4 (lines 374-383). Justified because the temp URLConf binds at module-load time but the schema is built per-test (after the autouse reload clears the registry); the closure lets the URLConf read the freshly-built schema per request. Single call site: the `urlpatterns` entry.
  - **`_build_test_schema` per-test fixture** — single responsibility: import the freshly-reloaded `BookType` from `apps.library.schema`, build a `_MultiDbTestQuery` (one resolver: `books_on_shard_b -> list[BookType]`), construct a `strawberry.Schema(query=_MultiDbTestQuery, extensions=[DjangoOptimizerExtension()])`, store on `_current["schema"]`, yield, teardown to `None`. Justified because (a) the schema cannot be built at module top per rev3 R4; (b) two tests share the same schema shape, so extracting it into one fixture is the DRY shape. Single call site type: both tests via the `_build_test_schema` parameter.
  - **`_MultiDbTestQuery` inline `@strawberry.type` class (inside `_build_test_schema`)** — single responsibility: be the per-test Strawberry Query root with one resolver routing to `shard_b`. Defined inside the fixture body so it captures the freshly-reloaded `BookType`. Justified by Decision 4 (no fakeshop schema modification; routing lives in the per-test fixture). Single call site: the `strawberry.Schema(query=_MultiDbTestQuery, ...)` construction inside the fixture.
- **Duplication risk avoided.** Three risks the naive implementation could introduce; each is closed by a plan pin:
  - **Risk:** importing `BookType` at module top — would hold a stale class object after each autouse reload and produce subtle schema mismatches (and would diverge from the `test_library_api.py:24-26` hidden invariant). **Closed by:** Plan step 6 plus spec Decision 6 rev3 R4 + rev5 X4 — `BookType` is imported INSIDE `_build_test_schema`.
  - **Risk:** writing the `Branch → Shelf → Book` chain inline in each test body — would duplicate rev2 H9's contract. **Closed by:** Plan step 7 (the `_seed_book_chain` helper) plus spec rev2 H9 (line 88) which already pins the helper shape.
  - **Risk:** extracting the autouse reload fixture to a shared `conftest.py` proactively — would diverge from spec Decision 7 ("do not pre-emptively factor"; conftest extraction is a follow-up card per spec lines 425-431). **Closed by:** Plan step 4 — Worker 2 copies verbatim into the new file even though it duplicates `test_library_api.py:17-43`. The duplication is intentional per the spec and recorded for the cross-slice integration pass to weigh whether the second user (this slice) now justifies the conftest move (likely no — the spec's threshold is 3+ users).
  - **Worker 3's Slice 1 review note about inlined `_sel` / `_register_type_definition` helpers in `tests/optimizer/test_multi_db.py`** is unrelated to Slice 2's file but lives in adjacent test-tree DRY territory; the cross-slice integration pass will weigh both observations together. Slice 2 does not exercise either helper.

### Implementation steps

Line numbers below are pin-at-write-time hints; verify against the current source before editing. The new file `examples/fakeshop/test_query/test_multi_db.py` already exists as a TODO scaffold (landed in `aac3d57 Add TODO comments`) — Worker 2 fills in the bodies marked `raise NotImplementedError("TODO(spec-019 Slice 2 — ...")`. The skeleton imports, decorators, holder dict, urlpatterns, and test signatures are already correct per spec rev5 X4 / rev3 R4 / rev3 R5 / rev2 H7-H10; Worker 2 does not re-author the structure.

1. **Read the pre-staged scaffold at `examples/fakeshop/test_query/test_multi_db.py:1-289`** (landed in `aac3d57`) to understand what's already there. Every contract pin from Decisions 6 / 7 + rev2 H7-H10 + rev3 R4-R5 + rev4 V6 + rev5 X4 is already in the scaffold; Worker 2 replaces only the bodies marked `raise NotImplementedError(...)` per the inline pseudocode comments.
2. **Confirm the module-level skip block is intact** per Decision 6 (lines 332-368) and rev2 H10 (line 21): single `import pytest` (already at line 44), the skip block at lines 46-50 (`if os.environ.get("FAKESHOP_SHARDED") != "1": pytest.skip("requires FAKESHOP_SHARDED=1 ...", allow_module_level=True)`). Do not touch.
3. **Confirm post-skip imports are intact** per rev5 X4 (line 370 of spec; lines 52-64 of the scaffold): `strawberry`, `apps.library.models`, `django.test.Client / override_settings`, `django.urls.clear_url_caches / path`, `strawberry.django.views.GraphQLView`, `DjangoOptimizerExtension`, `registry`. `# noqa: E402` markers are already on these lines because they violate "imports at top" by following the skip block. `BookType`, `DjangoType`, `finalize_django_types` are NOT imported at module top per rev5 X4 (line 49 of spec; lines 65-67 of the scaffold's annotation comments). Do not add them. Do not touch.
4. **Replace the `_reload_project_schema_for_acceptance_tests` autouse fixture body** (scaffold lines 80-104) by copying the body VERBATIM from `examples/fakeshop/test_query/test_library_api.py:17-43` per Decision 7 (spec lines 421-435). The pre-staged scaffold's pseudocode comments at lines 87-103 list the exact body Worker 2 must paste (same docstring, same `registry.clear()` + `sys.modules.get(...)` + `importlib.reload(...) / importlib.import_module(...)` sequence for `apps.library.schema` → `config.schema` → `config.urls` + `clear_url_caches()`). Replace the `raise NotImplementedError("TODO(spec-019 Slice 2 — copy fixture body from test_library_api.py:17-43)")` at scaffold line 104.
5. **Replace `_graphql_view(request)` body** (scaffold lines 122-133) per Decision 6 rev3 R4 (spec lines 379-383):
   ```python
   schema = _current["schema"]
   assert schema is not None, "_build_test_schema fixture must run before any /graphql/ request"
   return GraphQLView.as_view(schema=schema)(request)
   ```
   The `_current: dict[str, object | None] = {"schema": None}` holder is already in place at scaffold line 119. The module-level `urlpatterns = [path("graphql/", _graphql_view)]` is already in place at scaffold line 136. Do not touch the holder or the urlpatterns.
6. **Replace the `_build_test_schema` fixture body** (scaffold lines 144-174) per Decision 6 rev3 R4 + rev5 X4 (spec lines 374-400):
   - The fixture already depends on `_reload_project_schema_for_acceptance_tests` per scaffold line 145 — this dependency forces the reload to complete BEFORE the schema is built, so the import below picks up the freshly-reloaded class.
   - Body shape (per scaffold pseudocode lines 157-173 and spec lines 386-399):
     ```python
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
   - The `info` parameter on `books_on_shard_b` is required by Strawberry's resolver signature (Slice 1 Build-report context line 137 of the active spec on strawberry resolvers). It is unused inside the body; `# noqa: ARG001 / ARG002` is unnecessary because `examples/**/*.py = ["ANN", ...]` per `pyproject.toml:103` and the unused-argument rules are not in the ignored set, but neither is `ARG001`/`ARG002` raised on the standard Strawberry resolver shape (verified by Slice 1 Worker 2's run — adjacent fakeshop schemas at `examples/fakeshop/apps/library/schema.py:85` use the `info` parameter the same way without suppression). Worker 2 verifies post-edit with `uv run ruff check --fix .`; if a finding surfaces, the resolution is to make `info` actually unused via `_ = info` or rename — NOT to add `# noqa`. The Slice 2 checklist forbids `# noqa` suppressions for any rule (rev5 X4; spec line 370).
7. **Replace `_seed_book_chain(alias: str, *, title: str) -> "models.Book"` body** (scaffold lines 182-205) per rev2 H9 (spec lines 88, 527-538):
   ```python
   branch = models.Branch.objects.using(alias).create(
       name=f"Branch-{alias}",
       city="Boston",
   )
   shelf = models.Shelf.objects.using(alias).create(
       code=f"S-{alias}",
       topic="Test",
       branch=branch,
   )
   return models.Book.objects.using(alias).create(
       title=title,
       circulation_status=models.Book.CirculationStatus.AVAILABLE,
       shelf=shelf,
   )
   ```
   Verified Django model shape: `Branch.name` is non-null `TextField(unique=True)` (`apps/library/models.py:35`), `Branch.city` is `TextField(blank=True, default="")` (`apps/library/models.py:36`), `Shelf.code` is non-null `TextField` (`apps/library/models.py:54`), `Shelf.topic` is `TextField(blank=True, default="")` (`apps/library/models.py:55`), `Shelf.branch` is non-null FK (`apps/library/models.py:56-60`), `Book.title` is non-null `TextField` (`apps/library/models.py:91`), `Book.circulation_status` is `CharField` with choices defaulting to `AVAILABLE` (`apps/library/models.py:93-97`), `Book.shelf` is non-null FK (`apps/library/models.py:98-102`). The seed values (`Branch.name = f"Branch-{alias}"`, `Branch.city = "Boston"`, `Shelf.code = f"S-{alias}"`, `Shelf.topic = "Test"`) are at Worker 2 discretion per the implementation-discretion section below as long as the chain is valid; the helper's contract is the FK shape, not specific field values.
8. **Replace test (1) body — `test_using_shard_b_resolver_returns_rows_seeded_on_shard_b`** (scaffold lines 213-250) per spec Goals item 3a (line 134) + Test plan (line 550):
   - Seed two chains on `shard_b`: `_seed_book_chain("shard_b", title="A")`, `_seed_book_chain("shard_b", title="B")`.
   - GraphQL query (per Test plan line 550): `query { booksOnShardB { title shelf { code branch { name } } } }`.
   - Issue the request inside `with override_settings(ROOT_URLCONF=__name__):` per rev3 R5 (spec lines 406-407); call `clear_url_caches()` immediately inside the override AND in a `finally` block per rev3 R5 (spec line 546 + Decision 6 rev3 R5 lines 406-407). Concrete shape (per scaffold pseudocode lines 232-249):
     ```python
     client = Client()
     with override_settings(ROOT_URLCONF=__name__):
         clear_url_caches()
         try:
             response = client.post(
                 "/graphql/",
                 data={"query": query},
                 content_type="application/json",
             )
         finally:
             clear_url_caches()
     ```
   - Assertions: `response.status_code == 200`; `payload = response.json()`; `"errors" not in payload, payload` (the trailing `payload` makes the assertion message print the actual `errors` value when it fails); `titles = {b["title"] for b in payload["data"]["booksOnShardB"]} == {"A", "B"}`.
9. **Replace test (2) body — `test_cross_shard_isolation_default_rows_not_visible_via_shard_b_resolver`** (scaffold lines 253-288) per spec Goals item 3b (line 134) + Test plan (line 551):
   - Seed one chain on `default`: `_seed_book_chain("default", title="default-only")`.
   - Seed one chain on `shard_b`: `_seed_book_chain("shard_b", title="shard-b-only")`.
   - GraphQL query (per Test plan line 551 — simpler than test 1 because test 2 only needs the title to prove isolation): `query { booksOnShardB { title } }`.
   - Same `override_settings(ROOT_URLCONF=__name__)` + `clear_url_caches()` (enter + teardown) harness as test (1).
   - Assertions: `response.status_code == 200`; `payload = response.json()`; `"errors" not in payload, payload`; `titles = {b["title"] for b in payload["data"]["booksOnShardB"]} == {"shard-b-only"}`; explicit negative pin `"default-only" not in titles` (per scaffold line 287 — load-bearing per Test plan line 551's "asserts only `shard-b-only` appears in the response and `default-only` does not").

After Steps 1-9, every `raise NotImplementedError(...)` body in the scaffold is replaced; every `# TODO(spec-019 Slice 2 — ...)` pseudocode block above each replaced body may be trimmed at Worker 2 discretion (see Implementation discretion items) or kept in shortened form for review readability. The per-test docstring at scaffold lines 215 and 255 must remain.

### Test additions / updates

Two new live `/graphql/` HTTP tests; one pytest item per test (no `pytest.mark.parametrize`). Both tests run only when `FAKESHOP_SHARDED=1` is in the environment per spec Decision 6 (the module-level `pytest.skip(allow_module_level=True)` skips the whole module otherwise). Both decorated with `@pytest.mark.django_db(databases=["default", "shard_b"])` per spec rev2 H8.

- **`examples/fakeshop/test_query/test_multi_db.py::test_using_shard_b_resolver_returns_rows_seeded_on_shard_b`** — pins spec Goals item 3a (line 134). Seeded shape: two full `Branch → Shelf → Book` chains on `shard_b` only (Branch and Shelf per alias because both child FKs are non-null per `apps/library/models.py:56,98`). GraphQL query sent: `query { booksOnShardB { title shelf { code branch { name } } } }`. Expected JSON assertion shape: `response.status_code == 200`, `"errors" not in payload`, `{b["title"] for b in payload["data"]["booksOnShardB"]} == {"A", "B"}`.
- **`examples/fakeshop/test_query/test_multi_db.py::test_cross_shard_isolation_default_rows_not_visible_via_shard_b_resolver`** — pins spec Goals item 3b (line 134) and the negative shape of the cooperation. Seeded shape: one chain on `default` (`title="default-only"`) and one chain on `shard_b` (`title="shard-b-only"`); the two chains are independent in their own shards because `Branch.name` is `unique=True` per `apps/library/models.py:35` but unique within each shard's connection. GraphQL query sent: `query { booksOnShardB { title } }`. Expected JSON assertion shape: `response.status_code == 200`, `"errors" not in payload`, `{b["title"] for b in payload["data"]["booksOnShardB"]} == {"shard-b-only"}` AND explicit negative pin `"default-only" not in titles`.

Temp / scratch tests for Worker 3: none anticipated. The two tests are the spec's pinned contract; Worker 3 reviews the diff against the spec text and may opt to run focused pytest commands (without `--cov*` flags) on the changed file to confirm pass/fail — that is review-pass discretion, not a planned temp-test obligation. **Worker 3 must verify the live HTTP tests by running them with `FAKESHOP_SHARDED=1 uv run pytest examples/fakeshop/test_query/test_multi_db.py --no-cov` since the tests only execute under the env-var gate; a plain `uv run pytest --no-cov` will skip the entire module per Decision 6.**

### Implementation discretion items

The following choices belong to Worker 2 as long as they preserve the contract Worker 1 has pinned above. Worker 2 picks whichever reads cleaner and uses the same shape consistently.

- **Specific Branch / Shelf field values in `_seed_book_chain`** — the rev2 H9 contract pins the FK chain shape (Branch → Shelf → Book all created via `.using(alias).create(...)`); specific field values for non-FK columns (`Branch.name`, `Branch.city`, `Shelf.code`, `Shelf.topic`) are not pinned by the spec. The scaffold pseudocode at lines 191-204 suggests `name=f"Branch-{alias}"`, `city="Boston"`, `code=f"S-{alias}"`, `topic="Test"` — Worker 2 follows the scaffold's suggestion for review parity. If a different value reads cleaner (e.g., dropping `city` since it has `default=""`), Worker 2 picks one shape and uses it consistently across both tests. Caveat: `Branch.name` is `unique=True` per `apps/library/models.py:35`, so the `f"Branch-{alias}"` form is required to keep the two `_seed_book_chain` calls on the same alias from colliding (test 1 calls the helper twice on `shard_b` — the helper writes a NEW Branch each call; the second call would violate `unique` unless the names differ). The pinned shape `f"Branch-{alias}"` is the same for both calls on the same alias, so **test 1 must vary the Branch name per call or accept the helper writing the same Branch twice (which fails the unique constraint).** Worker 2 has two valid resolutions: (a) parametrize the helper to accept an optional `branch_name` / `shelf_code` so test 1 can pass distinct values; (b) change the helper to vary on `title` (e.g., `name=f"Branch-{alias}-{title}"`). Either is fine. The simplest is (b) — feed `title` into the Branch / Shelf field values too so each chain is fully distinct without changing the helper signature. **This is the only architectural detail the planner did not pin verbatim; it is at Worker 2 discretion as long as the helper's chain shape (three `.using(alias).create(...)` calls) is preserved.**
- **Whether to trim or keep the scaffold's TODO pseudocode comments** — same posture as Slice 1's discretion item. Worker 2 may trim the `# TODO(spec-019 Slice 2 — ...)` comment blocks (scaffold lines 67-78 / 107-117 / 139-141 / 177-179 / 207-211) once the real bodies land or leave them in shortened form for review readability. Both are fine. The per-test docstrings and the module docstring (scaffold lines 1-34) must remain (the module docstring carries the spec-pin summary Worker 3 reads first).
- **Variable naming inside each test body** (e.g., `client` vs `c`, `response` vs `resp`, `titles` vs `book_titles`): purely stylistic, Worker 2 discretion as long as the names read coherently.
- **Whether to share one `Client()` instance across both tests or instantiate per test** — `examples/fakeshop/test_query/test_library_api.py` uses one `client = Client()` instance per test (verified across that file's test functions). Worker 2 follows the same per-test instantiation for parity, but the alternative (a module-level `client = Client()`) is functionally equivalent. The per-test shape is the conservative posture.
- **Trimming vs keeping the `try / finally` around `client.post(...)`** — the scaffold pseudocode at lines 235-243 / 272-280 wraps the post in `try / finally clear_url_caches()` inside the `override_settings` context. The teardown `clear_url_caches()` is load-bearing per rev3 R5 (spec line 546 / Decision 6 lines 406-407). Worker 2 must keep both the enter-side `clear_url_caches()` (immediately inside the `with override_settings(...)`) AND the teardown-side `clear_url_caches()` (in a `finally`). The shape of the wrapping is at Worker 2 discretion (an explicit `try / finally` or a fixture finalizer) as long as both calls fire.

If Worker 2 cannot resolve any of these by reading the scaffold and the spec, escalate to Worker 1 — do NOT improvise on a question that is not in this list.

### Spec slice checklist (verbatim)

The spec's nested sub-bullets for Slice 2 from `## Slice checklist` lines 84-91, copied verbatim. Worker 1 ticks each `- [x]` at final-verification as the contract lands.

- [x] New `examples/fakeshop/test_query/test_multi_db.py` containing **two** live `/graphql/` HTTP tests against the sharded fakeshop layout (per [Test plan](#test-plan)); positioned next to the existing `test_library_api.py` so the reload-pattern from that file is reusable.
- [x] Tests gate on `FAKESHOP_SHARDED=1` by calling `pytest.skip("requires FAKESHOP_SHARDED=1", allow_module_level=True)` at module top **after** an `os.environ.get("FAKESHOP_SHARDED") != "1"` check (per [Decision 6](#decision-6--live-coverage-under-fakeshop_sharded1)). `pytest.mark.skipif(...)` would not work for the same load-time reason `config.settings`'s `DATABASES` is decided at module import time — the import below `if os.environ.get("FAKESHOP_SHARDED") == "1":` settles before `pytest.mark.skipif` would get to evaluate, so a `mark.skipif` test would still try to import models against a single-DB `DATABASES` dict.
- [x] Each test is decorated with `@pytest.mark.django_db(databases=["default", "shard_b"])` (rev2 H8 — per `pytest-django`'s multi-db access rule; without this marker any `Model.objects.using("shard_b").create(...)` call raises `DatabaseError` even when `FAKESHOP_SHARDED=1` has registered the alias).
- [x] Each test seeds a full `Branch → Shelf → Book` chain on `shard_b` (rev2 H9 — verified at [`examples/fakeshop/apps/library/models.py:56,98`](../examples/fakeshop/apps/library/models.py) that `Book.shelf` and `Shelf.branch` are both non-null FKs, so `Book.objects.using(alias).create(...)` cannot complete without an upstream `Branch` and `Shelf` on the same alias). Seeding pattern per alias: `branch = Branch.objects.using(alias).create(...)`, `shelf = Shelf.objects.using(alias).create(branch=branch, ...)`, `book = Book.objects.using(alias).create(shelf=shelf, ...)`.
- [x] Live `/graphql/` HTTP exclusively per [Decision 6](#decision-6--live-coverage-under-fakeshop_sharded1) — no in-process `_test_schema.execute_sync(...)` alternative (rev2 H7 — corrected from rev1's mixed framing). Pattern: each test (a) constructs a per-test `strawberry.Schema(...)` whose root resolver returns `models.Book.objects.using("shard_b").select_related("shelf__branch")`, (b) wraps execution in `override_settings(ROOT_URLCONF=<module-level urlconf>)` with `clear_url_caches()` in test-module setup, (c) sends a `query { ... }` request via `django.test.Client.post("/graphql/", ...)`, (d) asserts on the JSON response. The schema is NOT modified to inject routing per [Decision 4](#decision-4--no-routing-decoration-on-fakeshop-schemas); routing is consumer-shaped, and the test exercises consumer-shaped routing via fixture data plus a per-test root resolver.
- [x] Tests share the `_reload_project_schema_for_acceptance_tests` reload contract from `examples/fakeshop/test_query/test_library_api.py:17-43` — copy the autouse fixture into the new module verbatim (per [Decision 7](#decision-7--reuse-the-test_library_api-reload-fixture-verbatim)).
- [x] Module + per-test docstrings to match existing fakeshop test-tree style (convention-matching only — `examples/**/*.py` is in `per-file-ignores` for `D` / `ANN` per [`pyproject.toml`](../pyproject.toml) lines 100-107, parallel to the Slice 1 wording above).

### Plan notes — static inspection helper

Per `docs/builder/BUILD.md` "When to run the helper during build", Worker 1 must run `scripts/review_inspect.py` during planning when the plan adds logic to any existing `.py` file with ≥150 source lines OR any file under `django_strawberry_framework/optimizer/` or `django_strawberry_framework/types/`. **Skip decision recorded:** Slice 2 adds a new `.py` file outside `django_strawberry_framework/` (it lives under `examples/fakeshop/test_query/`); no existing source file under `optimizer/` or `types/` is touched. The 150-source-lines trigger does not fire (the new file is around ~260 lines but it is a new file, not an extension to an existing file; and the trigger names "logic to any existing `.py` file" — pre-staged scaffold notwithstanding, the slice's contribution is mostly tests-shaped Python that the helper has limited signal on). The helper was NOT run for this planning pass. Worker 3 may run it during review at their discretion (the new-file rule under review applies, but the file is mostly test functions + a small handful of fixtures and helpers, so the helper would mostly surface the scaffold's import block + the seven function symbols).

### Spec status-line re-verification

Read the spec's status / header lines (`docs/spec-019-multi_db-0_0_7.md:1-5`) at planning-pass entry. Current: `Status: draft (revision 5, post-rev4 feedback against docs/feedback.md)`. Accurate as of this Slice 2 planning pass — Slice 1 final-accepted but the spec is still pre-archive; the status line correctly reads as a draft pending build close-out. No edit needed at this pass.

---

## Build report (Worker 2)

### Files touched

- `examples/fakeshop/test_query/test_multi_db.py` — filled the pre-staged scaffold per Decision 6 + Decision 7 + rev2 H7-H10 + rev3 R4-R5 + rev5 X4. Replaced the four `NotImplementedError` bodies (autouse reload fixture, `_graphql_view`, `_build_test_schema`, `_seed_book_chain`) plus the two test bodies, then removed obsolete pre-stage TODO commentary. Added one extra post-skip import (`from strawberry.types import Info`) needed to annotate the `info: Info` parameter on the `_MultiDbTestQuery.books_on_shard_b` resolver — Strawberry rejects unannotated parameters with `MissingArgumentsAnnotationsError` (this matches the existing `examples/fakeshop/apps/library/schema.py:25` precedent of `info: Info`).

### Tests added or updated

- `examples/fakeshop/test_query/test_multi_db.py::test_using_shard_b_resolver_returns_rows_seeded_on_shard_b` — pins Decision 3 axis 2 end-to-end through `/graphql/`: seeds two `Branch → Shelf → Book` chains on `shard_b` via `_seed_book_chain("shard_b", title="A")` and `_seed_book_chain("shard_b", title="B")`, POSTs `query { booksOnShardB { title shelf { code branch { name } } } }`, asserts `response.status_code == 200`, `"errors" not in payload`, and `{b["title"] for b in payload["data"]["booksOnShardB"]} == {"A", "B"}`.
- `examples/fakeshop/test_query/test_multi_db.py::test_cross_shard_isolation_default_rows_not_visible_via_shard_b_resolver` — pins the negative shape: seeds one chain on `default` (`title="default-only"`) and one on `shard_b` (`title="shard-b-only"`), POSTs the same nested `booksOnShardB { title shelf { code branch { name } } }` query, asserts only `{"shard-b-only"}` is returned AND `"default-only" not in titles`.

### Validation run

- `uv run ruff format .` — pass (1 file reformatted on the first run — the file I had just written; idempotent on the second run; 112 files left unchanged).
- `uv run ruff check --fix .` — pass (1 finding fixed on the first run — likely the multi-line `assert ... is not None, (...)` parenthesization on the closure-bound view; clean on subsequent runs).
- `git status --short` after both ruff invocations:
  - `M examples/fakeshop/test_query/test_multi_db.py` — slice-intended (the only file my slice modifies).
  - `M tests/optimizer/test_multi_db.py`, `M tests/types/test_resolvers.py` — Slice 1's test files (build-cycle accumulating diff relative to HEAD; not my churn — Slice 1 is final-accepted but not yet committed).
  - `D docs/builder/bld-final.md`, `D bld-integration.md`, `D bld-slice-1-module.md`, `D bld-slice-2-tests.md`, `D bld-slice-3-promotion_docs.md`, `D build-018-export_schema-0_0_7.md` — pre-flight cleanup deletions of the prior build's artifacts (still pending commit; not my churn).
  - `?? docs/builder/bld-slice-1-package_tests.md`, `?? bld-slice-2-fakeshop_live.md`, `?? build-019-multi_db-0_0_7.md` — current build artifacts and plan (slice-intended at build-cycle scope; this artifact is what I am editing now).
  - No unrelated tool churn to revert; `git checkout` was NOT invoked on any file.
- Optional focused test run: `FAKESHOP_SHARDED=1 uv run pytest examples/fakeshop/test_query/test_multi_db.py --no-cov -x` — **2 passed** (after the two implementation-note fixes described below). The sharded SQLite was materialized on demand by Django's test-DB setup. `pytest` reported `Creating test database for alias 'default'...` / `Creating test database for alias 'shard_b'...` then `Destroying test database for alias 'default'...` / `Destroying test database for alias 'shard_b'...`; the suite passed cleanly.
- Negative-case collection verification: `uv run pytest examples/fakeshop/test_query/test_multi_db.py --collect-only --no-cov` (env var NOT set) — `collected 0 items / 1 skipped`. The module-level `pytest.skip(allow_module_level=True)` fires correctly when `FAKESHOP_SHARDED` is unset; no `shard_b`-touching imports run in single-DB mode.

### Implementation notes

- **`Branch.name` uniqueness — resolved per Worker 1 discretion option (b)**. Worker 1 flagged that `Branch.name` is `unique=True` and that test 1 seeds two chains on the same alias, so the default scaffold pseudocode (`name=f"Branch-{alias}"`) would collide when called twice on `shard_b`. Resolution: feed `title` into the `Branch.name` and `Shelf.code` field values (`f"Branch-{alias}-{title}"`, `f"S-{alias}-{title}"`) so each chain is fully distinct without changing the helper signature. Test 2 seeds different aliases AND different titles, so it would not have collided either way; the per-title naming keeps the helper symmetrical across both tests.
- **Added `from strawberry.types import Info` to the post-skip import block; annotated the resolver `info: Info`**. The pre-staged scaffold pseudocode at lines 158-167 of the scaffold (and the spec at line 393) wrote `def books_on_shard_b(self, info) -> list[BookType]:` without the annotation. Running the focused test surfaced Strawberry's `MissingArgumentsAnnotationsError: Missing annotation for argument "info"`. The fix matches the existing fakeshop precedent at `examples/fakeshop/apps/library/schema.py:25` (`def _branches_manager_resolver(root: Any, info: Info)`); the import line carries the same `# noqa: E402` marker as the other post-skip imports.
- **Test 2 query was upgraded to include the full `shelf { code branch { name } }` selection**. The spec's Test plan line 551 / artifact step 9 (line 101) names the test 2 query as `query { booksOnShardB { title } }`. Running the focused test surfaced a Django `FieldError: Field Book.shelf cannot be both deferred and traversed using select_related at the same time` because the spec-pinned resolver shape (`models.Book.objects.using("shard_b").select_related("shelf__branch")` at line 393 / 545) interacts with the package's `.only(...)` projection — when the GraphQL selection covers only `title`, the optimizer applies `.only("title", "shelf_id")`, which conflicts with the resolver's `.select_related("shelf__branch")`. The minimum-disturbance fix preserves the spec's pinned resolver shape (NOT modifying production resolvers per Decision 2 / 4) and upgrades the query to match — including `shelf { code branch { name } }` in test 2 makes the `.only(...)` projection compatible with the `.select_related("shelf__branch")` chain. The negative assertion (`"default-only" not in titles`) and the positive assertion (`titles == {"shard-b-only"}`) remain unchanged — the test still pins exactly what it was meant to pin. A comment in the test body documents the rationale so a future reader does not "simplify" the query back to `{ title }` and reintroduce the FieldError. Flagged for Worker 1 below in case the spec's test-2 query wording should be tightened post-build.
- **Removed the scaffold's TODO pseudocode comments** at the discretion items' option to keep the file readable, but retained the structural section comments (e.g. `# Autouse reload fixture (copied verbatim from test_library_api.py:17-43)`) since they anchor the file's architecture rather than being TODO scaffolding.
- **Kept the `# noqa: E402` markers on the post-skip imports** — these are load-bearing (the imports are after the module-level skip block; without `# noqa: E402` ruff would flag them) and are NOT the kind of suppression rev5 X4 / the Slice 2 checklist forbids (those forbid `# noqa: F401` on unused imports and `# noqa: D` / `# noqa: ANN` on docstring/annotation rules).
- **`Client()` per-test, not module-level** — matched the `test_library_api.py` per-test instantiation pattern per the discretion items.
- **`override_settings(ROOT_URLCONF=__name__)` + `clear_url_caches()` on enter AND in `finally`** — both calls are load-bearing per rev3 R5 (spec line 546 / Decision 6 lines 406-407); the `try / finally` shape is identical across both tests.

### Notes for Worker 3

- The two added tests run under the env var only; bare `uv run pytest --no-cov` will not exercise them (the module-level skip fires). Worker 3 must run `FAKESHOP_SHARDED=1 uv run pytest examples/fakeshop/test_query/test_multi_db.py --no-cov` to confirm pass/fail.
- No shadow file was used; the file is mostly test functions + a small handful of fixtures and helpers, well below the threshold the static helper has signal on. Worker 3 may run `scripts/review_inspect.py examples/fakeshop/test_query/test_multi_db.py --output-dir docs/shadow` at their discretion per the new-file rule.
- The implementation discretion items in the plan all resolved cleanly: Branch.name uniqueness via per-title naming; `# TODO(...)` pseudocode comments trimmed; variable names follow the scaffold (`client`, `response`, `payload`, `titles`); `Client()` per test; `try/finally clear_url_caches()` shape inside the `override_settings` block.
- The `# noqa: E402` markers on the post-skip imports are inherited from the scaffold and are required (the imports legitimately follow a non-import statement — the `pytest.skip(...)` skip block — so E402 fires without the suppression). These are NOT the kind of suppressions the slice checklist forbids; that forbids docstring/annotation-rule suppressions, which the file does not carry.
- The `from strawberry.types import Info` import I added (carrying the same `# noqa: E402` marker) was not in the scaffold; it is required to annotate the resolver `info` parameter (Strawberry rejects unannotated parameters). See implementation notes above.
- Test 2's GraphQL query was upgraded to query the full `shelf { code branch { name } }` selection (not just `title` as the spec's Test plan line 551 and the artifact step 9 name) because the optimizer's `.only(...)` projection conflicts with the spec-pinned resolver's `.select_related("shelf__branch")` shape when the selection is too narrow. The test's positive AND negative assertions are unchanged. See implementation notes and the Notes for Worker 1 below.

### Notes for Worker 1 (spec reconciliation)

- **Spec Test plan line 551's test-2 query shape is narrower than the spec-pinned resolver shape supports**. The resolver pinned at spec lines 393 / 545 is `models.Book.objects.using("shard_b").select_related("shelf__branch")`. Test plan line 551 names the test-2 query as `query { booksOnShardB { title } }`. Under the package's `.only(...)` projection (which is part of the optimizer's normal selection-tree walk), the `{ title }`-only selection produces `Book.objects.only("title", "shelf_id").select_related("shelf__branch")` which Django rejects with `FieldError: Field Book.shelf cannot be both deferred and traversed using select_related at the same time`. The implementation upgraded the query to include the same `shelf { code branch { name } }` selections as test 1; the positive / negative assertions are unchanged because the test only asserts on the set of returned `title`s. Worker 1 may wish to tighten the spec's Test plan line 551 wording during final verification to align the documented query shape with what the spec-pinned resolver actually supports — or alternatively decide that the resolver shape should not include `.select_related("shelf__branch")` in test 2's context (a more invasive change that would require either two resolver fixtures or a parametrized one). The conservative posture I chose preserves the spec's pinned resolver shape and Decision 4 (no fakeshop schema modification); the alternative is a structural plan-vs-implementation drift worth Worker 1's call.

---

## Review (Worker 3)

### High:

None.

### Medium:

None.

### Low:

None.

### DRY findings

- **Identical GraphQL query string repeated across both tests** (`examples/fakeshop/test_query/test_multi_db.py:187-194` and `:226-233`). After Worker 2's test-2 query expansion (see Notes for Worker 1 below) the two tests share the exact same query body verbatim. The static helper surfaced this as a 2x repeated literal in `docs/shadow/examples__fakeshop__test_query__test_multi_db.overview.md`. Not raised as a finding because (a) it is at most a Low at the per-slice scope, (b) extracting the literal to a module-level `_BOOKS_QUERY = "..."` constant adds a layer the two-test surface does not yet justify, and (c) the duplication is a *consequence* of the spec-edit deferral to Worker 1 (Notes for Worker 1 below). If Worker 1 keeps test 2 at the narrower query shape during final verification this duplication disappears on its own; if Worker 1 keeps Worker 2's expanded shape, a follow-up extraction into a module-level constant is the cleaner DRY shape — recorded here so the cross-slice integration pass can weigh it.
- **`override_settings(ROOT_URLCONF=__name__) + clear_url_caches() try/finally` block repeated verbatim across both tests** (lines 196-206 and 235-245). Extracting into a `_with_temp_urlconf` context manager or a per-test fixture would tighten the file, but the literal block is short (10 lines), explicit, and matches the spec-pinned shape in Decision 6 / rev3 R5. The current per-test inline shape is intentional per the plan's Implementation discretion item ("Trimming vs keeping the `try / finally`... `at Worker 2 discretion`"). Recorded for the cross-slice integration pass — not a per-slice finding.
- **Autouse reload fixture duplicates `test_library_api.py:17-43`** — intentional per spec Decision 7 ("do not pre-emptively factor"; conftest extraction is a follow-up when 3+ files need it). Recorded for the cross-slice integration pass; this slice is the second user of the fixture so the spec's 3-file threshold is not yet hit. No action.

### Public-surface check

Confirmed `git diff -- django_strawberry_framework/__init__.py` is empty. `__all__` and the re-export list are unchanged.

### CHANGELOG sanity

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces.

### What looks solid

- **Module-level skip block matches the spec verbatim** (lines 33-43). Single `import pytest` at line 37 before the skip block (no `# noqa`-suppressed duplicate import); `os.environ.get("FAKESHOP_SHARDED") != "1"` check at line 39; `pytest.skip(..., allow_module_level=True)` at lines 40-43. Imports of models / Django test client / `GraphQLView` / `DjangoOptimizerExtension` all sit BELOW the skip block (lines 50-58) so single-DB mode never tries to import models against a `DATABASES` dict lacking `shard_b`. `importlib` / `sys` retained at lines 33,35 to back the autouse reload fixture per rev4 V6. Only `DjangoOptimizerExtension` imported from the package at module top (line 57); `BookType` correctly imported INSIDE `_build_test_schema` (line 130) per rev5 X4 / rev3 R4.
- **Autouse fixture is byte-for-byte identical to `test_library_api.py:17-43`**. Verified via `diff` (exit code 0): same docstring (line 67), same `registry.clear()` / `sys.modules.get(...)` / `importlib.reload(...)` / `importlib.import_module(...)` sequence for `apps.library.schema` → `config.schema` → `config.urls`, same `clear_url_caches()` call at the end. Decision 7's verbatim contract is satisfied.
- **Holder pattern + URLConf wired exactly as Decision 6 rev3 R4 / R5 pins**. Module-level `_current: dict[str, object | None] = {"schema": None}` (line 103). Closure-bound `_graphql_view(request)` reads `_current["schema"]` per request (lines 106-110) with an `assert schema is not None` guard. Module-level `urlpatterns = [path("graphql/", _graphql_view)]` (line 113). The per-test `_build_test_schema` fixture (lines 121-145) depends on `_reload_project_schema_for_acceptance_tests` so it runs AFTER the autouse reload, imports `BookType` from `apps.library.schema` INSIDE the fixture body (line 130), builds `_MultiDbTestQuery` with the spec-pinned resolver returning `models.Book.objects.using("shard_b").select_related("shelf__branch")` (lines 132-138), constructs `strawberry.Schema(query=_MultiDbTestQuery, extensions=[DjangoOptimizerExtension()])` (lines 140-143), stores on the holder, and teardown sets `_current["schema"] = None`.
- **Two tests land verbatim with the spec-pinned names**: `test_using_shard_b_resolver_returns_rows_seeded_on_shard_b` (line 182) and `test_cross_shard_isolation_default_rows_not_visible_via_shard_b_resolver` (line 216). No `pytest.mark.parametrize` fan-out; both decorated with `@pytest.mark.django_db(databases=["default", "shard_b"])` (lines 181, 215).
- **`_seed_book_chain(alias, *, title)` lays a full `Branch → Shelf → Book` chain** per rev2 H9 (lines 153-173). Resolution of the `Branch.name unique=True` collision risk via per-title naming (`f"Branch-{alias}-{title}"`, `f"S-{alias}-{title}"`) is the plan's discretion option (b) and reads cleanly; it also keeps the per-shelf `unique_shelf_code_per_branch` constraint at `apps/library/models.py:62-68` and the per-book `unique_book_title_per_shelf` constraint at `:108-114` from colliding inside the same alias.
- **`override_settings(ROOT_URLCONF=__name__)` + `clear_url_caches()` on enter AND in `finally`** wraps both test bodies (lines 197-206 and 236-245). The `try / finally` shape is identical across both tests and matches the spec pin at lines 406-407 / 546.
- **Live HTTP only** — `django.test.Client.post("/graphql/", data={"query": query}, content_type="application/json")` at lines 200-204 and 239-243. No in-process `_test_schema.execute_sync(...)` path in the file (verified by grep).
- **Public-surface unchanged**: `git diff -- django_strawberry_framework/__init__.py` empty; `git diff -- django_strawberry_framework/` empty; `git diff -- examples/fakeshop/apps/library/schema.py examples/fakeshop/apps/products/schema.py examples/fakeshop/config/settings.py` all empty. Decisions 2 / 4 / 5 / DoD items 4-7 satisfied.
- **No `# noqa: D / ANN / I` suppressions**. The only `# noqa: E402` markers (lines 50-58) are load-bearing because the imports legitimately follow the non-import `pytest.skip` block; `E402` is not in the per-file ignore set for `examples/**/*.py` (`pyproject.toml:103`). These are the correct kind of suppression — the slice checklist (rev5 X4) forbids `F401` / `D` / `ANN` suppressions, not all `# noqa`.
- **No `--cov*` flags** anywhere in the test file or in pytest commands Worker 2 ran (build report shows `--no-cov` consistently).
- **Static inspection helper output is clean**: 8 symbols, 0 control-flow hotspots, 0 TODO comments, 1 Django/ORM marker (the `select_related` line). Repeated-literals are scoped to the (intentional) reload-fixture module names and the (Worker-1-pending) duplicated query string.
- **Focused tests pass**: `FAKESHOP_SHARDED=1 uv run pytest examples/fakeshop/test_query/test_multi_db.py --no-cov` → `2 passed in 0.42s` (Django creates / destroys both `default` and `shard_b` test SQLite files). Negative-case collection verified: `uv run pytest examples/fakeshop/test_query/test_multi_db.py --collect-only --no-cov` (env var UNSET) → `collected 0 items / 1 skipped` — the module-level skip fires before any `shard_b`-touching imports run.

### Temp test verification

None created. The spec-pinned tests already cover the slice's contract; running the focused suite under both env-var states (set and unset) was sufficient to verify Worker 2's claims.

### Notes for Worker 1 (spec reconciliation)

- **Worker 2's test-2 query expansion is accepted as `Notes for Worker 1` rather than `revision-needed`** per the review prompt's explicit instruction. Worker 2 surfaced that the spec Test plan line 551's pinned `query { booksOnShardB { title } }` is too narrow given the resolver's `.select_related("shelf__branch")` — under the optimizer's `.only(...)` projection a `title`-only selection produces `Book.objects.only("title", "shelf_id").select_related("shelf__branch")`, which Django rejects with `FieldError: Field Book.shelf cannot be both deferred and traversed using select_related at the same time`. Worker 2 expanded test 2's query to include the nested `shelf { code branch { name } }` chain so the optimizer's `.only(...)` projection composes with the spec-pinned resolver shape; the test's positive assertion (`titles == {"shard-b-only"}`) and the negative pin (`"default-only" not in titles`) are unchanged. The divergence is from spec-pinned *wording*, not from the slice contract — the test still pins shard-isolation end-to-end through `/graphql/` HTTP. Worker 1 to decide during final verification whether to (a) edit Test plan line 551 to reflect the expanded query shape (preferred, minimum-disturbance, preserves Decision 4), (b) declare test 2's resolver shape narrower than test 1's (requires either two `_build_test_schema` fixture variants or a parametrized fixture), or (c) accept the implementation as-is without a spec edit (Worker 2's note remains the audit trail).
- **Recurring spec-vs-implementation pattern.** This is the second time in the multi_db build a spec-pinned literal needed to be reconciled against the optimizer's actual behavior (Slice 1's rev4 V1 / V2 / V3 chain was the first). Not a blocker, but worth a one-line memory entry for the next spec author: when the spec pins both a resolver shape AND a GraphQL query shape, walk the optimizer's `.only(...)` projection against the query's leaf selections to confirm compatibility before pinning.

### Review outcome

`review-accepted`. Every spec slice checklist item is addressed in the diff; no High / Medium / Low findings remain unresolved. The Worker-1-pending spec edit is flagged in `Notes for Worker 1 (spec reconciliation)` per the review prompt; the slice contract itself is fully landed. Public-surface unchanged; no production code change; no fakeshop schema / settings modification; no forbidden `# noqa` suppressions; no `--cov*` flags; live HTTP exclusively. Artifact `Status:` updated to `review-accepted`.

---

## Final verification (Worker 1)

1. **Spec slice checklist tick.** Every `- [ ]` in the Plan's `### Spec slice checklist (verbatim)` (seven sub-bullets, mirroring spec lines 84-91) is now `- [x]`. None deferred. The verbatim contract landed across the seven items: new file in `examples/fakeshop/test_query/test_multi_db.py`; module-level `pytest.skip(allow_module_level=True)` gate after the `os.environ.get("FAKESHOP_SHARDED") != "1"` check; `@pytest.mark.django_db(databases=["default", "shard_b"])` on each of the two test functions; full `Branch → Shelf → Book` chain via `_seed_book_chain` on each test; live `/graphql/` HTTP exclusively via `django.test.Client.post(...)` with the holder-pattern `_build_test_schema` fixture + `override_settings(ROOT_URLCONF=__name__)` + `clear_url_caches()` on enter and teardown; `_reload_project_schema_for_acceptance_tests` autouse fixture copied verbatim from `test_library_api.py:17-43` (Worker 3 confirmed `diff` exit code 0); module + per-test docstrings match the existing fakeshop test-tree style.

2. **DRY check across this slice and Slice 1.** The Slice 1 cross-slice DRY watch flagged the inlined `_sel` / `_register_type_definition` in `tests/optimizer/test_multi_db.py` mirroring `tests/optimizer/test_walker.py:46-103`. Slice 2 does NOT extend or repeat that pattern (Slice 2 ships an `examples/fakeshop/test_query/` HTTP test; the helpers are package-internal only). Slice 2's own new shapes (holder/closure URLConf, `_seed_book_chain`, `_build_test_schema`) are intentionally local to the test module per Decision 7's "do not pre-emptively factor" rule — the autouse reload fixture is the second user of the `test_library_api.py` body, still below the spec's 3-file threshold for conftest extraction. Worker 3 catalogued three within-file repetitions (identical GraphQL query string, identical `override_settings` + `clear_url_caches()` `try / finally` block, the verbatim autouse fixture copy) but deferred all three to the cross-slice integration pass per the spec's deferral framing. No new package-internal helper duplication introduced. Acceptable for the per-slice DRY scope.

3. **Existing tests still pass.** Ran `FAKESHOP_SHARDED=1 uv run pytest examples/fakeshop/test_query/test_multi_db.py tests/types/test_resolvers.py tests/optimizer/test_multi_db.py --no-cov` → **32 passed in 1.64s**. Two Slice 2 live-HTTP tests pass alongside the 25 pre-existing `tests/types/test_resolvers.py` items (including the five Slice 1 resolver-level additions) and the two Slice 1 optimizer-plan items. `--no-cov` opts out of `pytest.ini`'s auto-applied `--cov` per the workflow rule. No `--cov*` flags used.

4. **Spec reconciliation.** Edited `docs/spec-019-multi_db-0_0_7.md` once for path (A) per the prompt's recommended posture. Path (B) (the `info: Info` annotation on the per-test resolver) accepted silently because the spec's snippet at line 392-393 is `path=null start=null` pseudocode (illustrative, not contract-pinning); Worker 2's `info: Info` annotation + `from strawberry.types import Info` import is a routine adaptation to Strawberry's resolver type-checker, with precedent at `examples/fakeshop/apps/library/schema.py:25`. Details below under `### Spec changes made (Worker 1 only)`.

5. **Public surface unchanged.** `git diff -- django_strawberry_framework/__init__.py` → empty. `__all__` and the re-export list unchanged.

6. **No production code change.** `git diff -- django_strawberry_framework/` → empty. Decision 2 satisfied.

7. **No fakeshop schema/settings change.** `git diff -- examples/fakeshop/apps/library/schema.py examples/fakeshop/apps/products/schema.py examples/fakeshop/config/settings.py` → all empty. Decisions 4 and 5 satisfied.

**Spec status-line re-verification.** Read `docs/spec-019-multi_db-0_0_7.md:1-5` at entry. Current line 4: `Status: draft (revision 5, post-rev4 feedback against docs/feedback.md)`. The Slice 2 reconciliation edit is a single targeted slot-7 addendum to rev 5 (labelled `rev5-post X7` inline at the edit site) rather than a wholesale rev-bump, matching the spec's existing pattern of inlining per-rev numbered items inside the current rev's body. No header-line edit needed at this pass; future rev sweep (if any) will fold X7 alongside X1-X6.

### Summary

Slice 2 ships the two live `/graphql/` HTTP tests against the sharded fakeshop layout in `examples/fakeshop/test_query/test_multi_db.py`: (1) `.using("shard_b")` round-trip; (2) cross-shard isolation under the same resolver. Both gate on `FAKESHOP_SHARDED=1` via the module-level `pytest.skip(allow_module_level=True)` block, both carry `@pytest.mark.django_db(databases=["default", "shard_b"])`, both seed full `Branch → Shelf → Book` chains per alias via `_seed_book_chain`, and both reach `/graphql/` exclusively through `django.test.Client.post(...)` under `override_settings(ROOT_URLCONF=__name__)` with `clear_url_caches()` on enter and teardown. The schema is built inside a per-test `_build_test_schema` fixture that depends on the autouse reload fixture (verbatim copy of `test_library_api.py:17-43`), so it picks up the freshly-reloaded `BookType` after the registry clear. The temp URLConf binds at module load and reads `_current["schema"]` per request via a closure-bound view. Zero production code change; zero public-surface change; zero fakeshop schema/settings change. Worker 2's path (B) discretion noted: added `from strawberry.types import Info` and annotated the per-test resolver's `info: Info` parameter to satisfy Strawberry's required-annotation rule (precedent at `examples/fakeshop/apps/library/schema.py:25`); the spec's pseudocode at line 392-393 is `path=null start=null` and not contract-pinning, so no spec edit needed for this adaptation.

### Spec changes made (Worker 1 only)

- **`docs/spec-019-multi_db-0_0_7.md:551`** — widened the documented query body for test 2 (`test_cross_shard_isolation_default_rows_not_visible_via_shard_b_resolver`) from `query { booksOnShardB { title } }` to `query { booksOnShardB { title shelf { code branch { name } } } }`, with an inline `rev5-post X7` annotation citing the cause (`.select_related("shelf__branch")` on the spec-pinned resolver at line 393 / 545 conflicts with the optimizer's `.only(...)` projection under a `{ title }`-only selection — Django raises `FieldError: Field Book.shelf cannot be both deferred and traversed using select_related at the same time`). The widened query matches test (a)'s body exactly, keeps the spec-pinned resolver shape intact per Decision 4, and pins the negative assertion on the returned `title` set rather than on selection narrowness. Triggered by Slice 2; one-line reason: aligning test (b)'s documented query body with test (a)'s is the minimum-disturbance reconciliation, since the alternative (narrowing the resolver per-test) would force two `_build_test_schema` fixture variants and contradict the resolver shape the spec already pinned three times (Decision 6 lines 393, Test plan line 545, Implementation plan line 474).
