# Build: Slice 4 — live HTTP coverage on a Relay-Node-shaped fakeshop type + public-export promotion

Spec reference: `docs/spec-030-connection_field-0_0_9.md` (Slice 4 checklist lines 91-94; Decision 7 lines 410-434; Decision 14 lines 513-527; Test plan Slice 4 lines 592-602; Edge cases lines 544, 546, 550-551; DoD `## Definition of done` Slice-4 items)
Status: final-accepted

## Plan (Worker 1)

### DRY analysis

**Existing patterns reused (cite file::Symbol):**

- **The `__init__.py` export + `__all__` pattern** — `django_strawberry_framework/__init__.py #"from .list_field import DjangoListField"` (the import line) and `django_strawberry_framework/__init__.py #"__all__ = ("` (the alphabetized tuple). `DjangoListField` is the exact mirror: one `# noqa: E402` import line from its flat module (`from .list_field import DjangoListField  # noqa: E402`) plus one entry in the `__all__` tuple. Slice 4 adds `from .connection import DjangoConnection, DjangoConnectionField  # noqa: E402` (a single import line — both symbols live in the one flat module `connection.py`, both already public-named there per `connection.py #"The public exports (``DjangoConnection`` / ``DjangoConnectionField``) land in"`) and the two new `__all__` entries (`"DjangoConnection",` and `"DjangoConnectionField",`) in alphabetical position. The `# noqa: E402` is required because every package import in this file sits after the `logger = logging.getLogger(...)` assignment (see the existing `# noqa: E402` on lines 18-24); mirror it exactly.
- **The library schema's Relay-Node `GenreType` + the sidecar-wired `Query` field shape** — `examples/fakeshop/apps/library/schema.py::GenreType` already declares `Meta.interfaces = (relay.Node,)`, `filterset_class = filters_genre.GenreFilter`, and `orderset_class = orders_genre.GenreOrder` — exactly the shape Decision 7 / Decision 14 require, so **no new model, migration, FilterSet, or OrderSet is needed**. The existing `all_library_genres` `@strawberry.field` resolver (`schema.py::Query.all_library_genres`) is the hand-written list analogue the connection field replaces with one declaration. The connection field is added as a **new class-attribute field** on `Query` next to it (NOT a replacement — `all_library_genres` stays for the existing filter/order list tests), shaped identically to the shipped `DjangoListField` class-attribute declaration `examples/fakeshop/apps/library/schema.py::Query #"all_library_branches_via_list_field: list[BranchType] = DjangoListField("`.
- **The fakeshop autouse reload harness** — `examples/fakeshop/test_query/test_library_api.py::_reload_library_project_schema` + the `_reload_project_schema_for_acceptance_tests` autouse fixture (lines 19-50). This is the canonical reload pattern `docs/TREE.md #"HTTP tests that import the project schema must preserve the reload pattern"` mandates: `registry.clear()` → reload `apps.library.schema` → reload `config.schema` → reload `config.urls` + `clear_url_caches()`. Slice 4's new tests live in this file and inherit the fixture automatically — **no new fixture is written, and the fixture must not be modified.** The new `DjangoConnectionField(GenreType)` field is recreated on every reload because it is declared at `apps.library.schema` module body level, the module the fixture reloads.
- **The live HTTP request + assert helpers** — `test_library_api.py::_post_graphql` (POSTs `{"query": ...}` to `/graphql/` via `django.test.Client`, returns the response) and `test_library_api.py::_assert_graphql_data` (asserts `status_code == 200` and `response.json() == {"data": expected}`). The new tests reuse `_post_graphql` for the cases that inspect `errors` / partial shapes and `_assert_graphql_data` for the clean round-trip; neither helper is re-implemented. The `payload = response.json(); assert "errors" not in payload, payload` shape (used throughout, e.g. lines 107-108, 650) is the standard error-absence assert.
- **Inline `Genre.objects.create(...)` seeding** — `test_library_api.py::_seed_library_graph #"genre = models.Genre.objects.create(name=\"Speculative\")"` and the genre-specific tests already seed genres inline (e.g. `test_library_genres_filter_by_relay_own_pk_global_id_in_list` at lines 874-876: `models.Genre.objects.create(name="SciFi")` etc.). Per `AGENTS.md #"Library acceptance tests use inline Model.objects.create; the library app has no services.py"`, Slice 4 seeds genres inline the same way — NO `seed_data` / services helper (that is the products-app rule, `AGENTS.md` line 7). Each test seeds its own deterministic genre set with `@pytest.mark.django_db`.
- **The GlobalID decode helper for `after:` cursors** — `test_library_api.py::_decode_global_id` exists for GlobalID round-trips, but connection **cursors** are opaque base64 `arrayconnection:N` offsets (Decision 9), distinct from node GlobalIDs. The `after:` round-trip test reads `endCursor` from page 1's `pageInfo` and feeds it back as `after:` on page 2 — the cursor stays opaque (never decoded), so no new decode helper is needed; the test treats `endCursor` as an opaque token per the Relay contract.

**New helpers / module justified (single responsibility each):**

- **None — no new test helper, no new fixture, no new production helper.** Slice 4 is (a) two `__init__.py` lines, (b) one `apps/library/schema.py` import + one `Meta.connection` line + one `Query` field declaration, and (c) five test functions that reuse the existing `_post_graphql` / `_assert_graphql_data` / autouse-reload machinery and inline `Genre.objects.create(...)`. If a test wants a small genre-seeding convenience (e.g. seed N genres with sortable names), Worker 2 may add a thin module-private `_seed_genres(...)` helper in `test_library_api.py` — that is an Implementation-discretion item, not a required new helper; the inline-create rule is satisfied either way because the helper would itself be inline `Model.objects.create` calls.

**Duplication risk avoided:**

- **Re-implementing the reload fixture.** The naive move would copy a fresh reload fixture into the new tests or build a per-test schema. The plan reuses the existing autouse `_reload_project_schema_for_acceptance_tests` fixture verbatim (the new tests are in the same file and inherit it). Re-deriving the reload would diverge from the `docs/TREE.md`-mandated pattern and risk stale-class bugs.
- **Replacing the existing `all_library_genres` list field.** The connection field is **additive** — a new `Query` attribute (e.g. `all_library_genres_connection`), NOT a replacement of `all_library_genres`. Removing the list field would orphan the existing genre filter/order/GlobalID list tests (lines 862-908). Adding alongside keeps both surfaces tested and matches how `DjangoListField` lives next to the hand-written resolvers in the same `Query`.
- **A second exported symbol path.** The example must import `DjangoConnectionField` (and, for the consumer annotation, `DjangoConnection`) **from the public surface** (`from django_strawberry_framework import DjangoConnectionField`), NOT from `django_strawberry_framework.connection` — Decision 14's whole point is that the export and the live proof land together so the example uses the public path. The plan pins the public import in `apps/library/schema.py`.
- **Generating a fresh per-field input type.** The connection field reuses `GenreType`'s `Meta.filterset_class` / `Meta.orderset_class`, so its `filter:` / `orderBy:` arguments resolve to the SAME `GenreFilterInputType` / `GenreOrderInputType` the existing `all_library_genres` resolver already uses (Decision 6 stable-name contract). No new input type, no SDL bloat — Worker 2 should confirm the connection's `filter:`/`orderBy:` argument input-type names match the list field's (a free correctness check via the existing `_input_field_names` helper if desired, not a required test).

### Does `config/schema.py` need a change? — NO.

Verified by reading `examples/fakeshop/config/schema.py`: the project `Query` is `class Query(LibraryQuery, ProductsQuery, ScalarsQuery, KanbanQuery, GlossaryQuery)` — it **inherits** each app's `Query` by subclassing. Adding the `DjangoConnectionField(GenreType)` field as a class attribute on `apps.library.schema.Query` (`LibraryQuery`) makes it a field on the project `Query` automatically through inheritance; `finalize_django_types()` and the `strawberry.Schema(...)` construction in `config/schema.py` pick it up with no edit. `config/schema.py` already imports `LibraryQuery` and constructs the schema with the singleton-factory `extensions=[lambda: _optimizer]` form + `strawberry_config()`. **Worker 2 must NOT edit `config/schema.py`** — it is out of scope for this slice (the spec's Slice-4 "Files touched" table lists only `__init__.py`, `apps/library/schema.py`, and `test_library_api.py`). The reload fixture already reloads `config.schema` after `apps.library.schema`, so the inherited field is present in the rebuilt project schema on every test.

### Async-path note (Decision 10 / Slice 2 finding) — live `/graphql/` sync view is the correct exercise; async needs no live test here.

The Slice 2 final-verification recorded (and Decision 10 codifies) that the connection field's **default resolver is build-time sync**: `ConnectionExtension.resolve` (the sync path, used when the field is not `async def`) hands the inner-resolver return straight to `resolve_connection` without awaiting, while only `ConnectionExtension.resolve_async` awaits. The fakeshop `/graphql/` endpoint is mounted on Strawberry's **sync** `GraphQLView` (the same view every existing `test_library_api.py` test posts to via `django.test.Client`), so the default `DjangoConnectionField(GenreType)` field exercises the build-time-sync path end-to-end — including the async-aware `totalCount` count, which `resolve_connection` materializes with `.count()` under the sync context. This is the right and complete live exercise for Slice 4. The async resolver path (`async def resolver=`) and the `SyncMisuseError`-on-async-`get_queryset` case are **genuinely unreachable from the sync `/graphql/` view** (Strawberry's sync execution rejects async resolvers with `RuntimeError: GraphQL execution failed to complete synchronously` — the same constraint documented for `DjangoListField`'s async `Manager` coercion at `apps/library/schema.py` lines 19-25), and their coverage already landed in `tests/test_connection.py` during Slice 2 (`test_connection_resolver_async_dispatch`, the async `.acount()` count test, the `SyncMisuseError` test). **No async live HTTP test is planned or needed for Slice 4** — adding one would be impossible against the sync view and redundant against Slice 2's package tests.

### Implementation steps

Line numbers are pin-at-write-time navigational hints. Verify against the current source before editing — Slices 1-3 have shifted `connection.py` but not `__init__.py` / `apps/library/schema.py` / `test_library_api.py` (those are at HEAD).

1. **`django_strawberry_framework/__init__.py` — promote the public exports (Decision 14).**
   - Add the import line `from .connection import DjangoConnection, DjangoConnectionField  # noqa: E402` alongside the other package imports (after `from .list_field import DjangoListField  # noqa: E402` at line 20 is the natural spot; the import block is at lines 20-24). The `# noqa: E402` is mandatory (the file's imports follow the module-level `logger` assignment; every sibling import carries it).
   - Add `"DjangoConnection",` and `"DjangoConnectionField",` to the `__all__` tuple (lines 28-39) in alphabetical position: `"DjangoConnection"` and `"DjangoConnectionField"` sit between `"BigInt"` and `"DjangoListField"` (alphabetical order: `BigInt` < `DjangoConnection` < `DjangoConnectionField` < `DjangoListField` < `DjangoOptimizerExtension` < `DjangoType`).
   - This is the FIRST and ONLY slice that touches `__init__.py` `__all__` for this card — authorized by Decision 14 / the build-plan public-export flag. Do NOT touch `__version__` (stays `"0.0.8"` per Decision 13).
   - The two symbols are already public-named in `connection.py` (verified: `connection.py::DjangoConnection` at the module's class def, `connection.py::DjangoConnectionField` factory at `connection.py #"def DjangoConnectionField("`) — no rename needed.

2. **`examples/fakeshop/apps/library/schema.py` — opt `GenreType` into `totalCount` (Decision 7 / spec User-facing-API).**
   - In `GenreType.Meta` (lines 144-149), add `connection = {"total_count": True}` (place it after the existing `filterset_class` / `orderset_class` lines; alphabetical-within-Meta is not enforced but `interfaces` / `filterset_class` / `orderset_class` / `connection` reads cleanly in the spec's example at spec lines 207-214). This is the net-new `Meta.connection` key Slice 1 shipped; `GenreType` already has `interfaces = (relay.Node,)`, so the `_validate_connection` Relay-Node requirement passes.

3. **`examples/fakeshop/apps/library/schema.py` — import + declare the connection field (Decision 14 / Decision 5).**
   - Extend the existing public import `from django_strawberry_framework import DjangoListField, DjangoType, OptimizerHint` (line 10) to add `DjangoConnection` and `DjangoConnectionField` → `from django_strawberry_framework import (DjangoConnection, DjangoConnectionField, DjangoListField, DjangoType, OptimizerHint)`. Import **from the public surface** (Decision 14), not from `django_strawberry_framework.connection`. `DjangoConnection` is imported for the consumer annotation; `DjangoConnectionField` for the field factory.
   - On `Query` (the `LibraryQuery`, lines 203-317), add a new class-attribute field — recommended name `all_library_genres_connection` (camelCased to `allLibraryGenresConnection` in the SDL; distinct from the existing `all_library_genres` list field so both surfaces stay testable). Shape per the spec User-facing-API and the `DjangoListField` class-attribute precedent:
     ```python
     all_library_genres_connection: DjangoConnection[GenreType] = DjangoConnectionField(GenreType)
     ```
     Meta-only derivation (Decision 5): no `filters=` / `order=` / `total_count=` kwargs — the `filter:` / `orderBy:` arguments and the `totalCount` field all come from `GenreType.Meta`. Place it near the existing `all_library_genres` resolver (after line 285) so the two genre surfaces sit together. Do NOT remove or alter `all_library_genres`.
   - Worker 2 confirms the consumer annotation (`DjangoConnection[GenreType]`) is accepted by Strawberry against the resolved concrete `GenreTypeConnection` (Decision 4 — the factory wires the concrete connection class through `relay.connection(...)`; the annotation documents the node type). If Strawberry rejects the annotation differing from the `relay.connection` type, the Risks fork (spec lines 624) applies — but Slice 2's tests already build a real schema with the same `relay.connection(_connection_type_for(target_type), ...)` shape, so this is expected to work; flag under Notes for Worker 1 only if it surfaces.

4. **`examples/fakeshop/test_query/test_library_api.py` — add the five live HTTP tests (Test additions section below).** Append the five `@pytest.mark.django_db` test functions; they inherit the autouse reload fixture. Each seeds genres inline with `models.Genre.objects.create(...)`. Group them under a section comment (mirroring the existing `# Slice 4 — live HTTP filter coverage` banner at line 659) e.g. `# spec-030 Slice 4 — live DjangoConnectionField HTTP coverage`.

5. **Undisturbed-suite check (spec lines 602).** A new reachable root field (`allLibraryGenresConnection`) changes the registered SDL. Confirm no existing `test_query/` test snapshots the whole SDL or asserts a registered-type / Query-field count — **already verified during planning** (grep found no `print_schema` / SDL-wide / type-count assertion in `examples/fakeshop/test_query/`; the only `__type` / `__schema` uses are scoped to named input types via `_input_field_names`, which are unaffected by an additional root field). Worker 2 re-runs this check at implementation time and records it in the build report.

### Test additions / updates

All five land in `examples/fakeshop/test_query/test_library_api.py`, each `@pytest.mark.django_db`, each seeding genres inline via `models.Genre.objects.create(...)` (the library inline-create rule, `AGENTS.md` line 8), each reusing `_post_graphql` / `_assert_graphql_data` and the autouse reload fixture. The connection field under test is `allLibraryGenresConnection` (root `DjangoConnectionField(GenreType)`, `Meta.connection = {"total_count": True}`, `GenreFilter` / `GenreOrder` sidecars). The GraphQL argument names are `filter:` and `orderBy:` (the camelCased `order_by` param). Pin the exact assertion shapes below (spec Test plan lines 596-600):

- **(a) `test_genre_connection_full_round_trip`** — seed several genres with sortable, filterable names (e.g. `Alpha`, `Beta`, `Gamma`, `Delta`, plus one that the filter excludes so `totalCount` ≠ total rows). Query `allLibraryGenresConnection(filter: {name: {icontains: "..."}}, orderBy: [{name: ASC}], first: 2) { edges { node { id name } } pageInfo { hasNextPage endCursor } totalCount }`. Assert: `edges` carries exactly the first 2 nodes in `name ASC` order from the post-filter set; `node.id` is a non-empty GlobalID string (it decodes to `("GenreType", pk)` via `_decode_global_id` — reuse it); `pageInfo.hasNextPage` is `True` (more than 2 in the filtered set); `pageInfo.endCursor` is a non-empty opaque string; `totalCount` equals the **full unpaginated post-filter** genre count (NOT 2, NOT the grand total — the count of rows matching the `filter:` before the `first: 2` slice). No `errors` in the payload. Then a **second page** assertion: re-query with `after: "<endCursor from page 1>"`, `first: 2`, same `filter:`/`orderBy:`; assert the next nodes in order and that pagination advanced correctly (no overlap with page 1). This single test proves pagination + ordering + filter + the pre-slice `totalCount` together, per the spec's "correct pagination, ordering, and totalCount on the unpaginated post-filter set."
- **(b) `test_genre_connection_first_and_last_rejected`** — query `allLibraryGenresConnection(first: 1, last: 1) { edges { node { id } } }`. Assert `response.status_code == 200` and the payload carries an `errors` array (the package's own `first` + `last` `GraphQLError` guard from `connection.py::_guard_first_and_last`, surfaced in the GraphQL `errors` array per Decision 3 / Edge cases line 546). Assert the error message names the mutual-exclusivity (substring match on the package guard's message, e.g. `"mutually exclusive"` — Worker 2 reads the exact wording from `connection.py::_guard_first_and_last` and matches a stable substring). This is a GraphQL `errors` entry, NOT a non-200 HTTP status.
- **(c) `test_genre_connection_first_zero_empty_edges`** — seed ≥1 genre. Query `allLibraryGenresConnection(first: 0) { edges { node { id } } pageInfo { hasNextPage endCursor } totalCount }`. Assert no `errors`; `edges == []` (empty); `pageInfo` is present and valid (`hasNextPage` is `True` when rows exist beyond the zero-window — delegated to Strawberry's `ListConnection`, Worker 2 reads the actual `ListConnection` `first: 0` semantics and asserts the real shape, not an assumed one); `totalCount` still equals the full genre count (the count is pre-slice, so `first: 0` does not zero it — selection-gated count runs because `totalCount` IS selected here). Per Edge cases line 544 (`first: 0` → empty `edges` + valid `pageInfo`, delegated to `ListConnection`).
- **(d) `test_genre_connection_total_count_omitted_no_count`** — seed several genres. Query `allLibraryGenresConnection(first: 2) { edges { node { id name } } pageInfo { hasNextPage } }` — **omitting `totalCount` entirely**. Assert no `errors`; `edges` carries the first 2 nodes correctly; the response is well-formed without any count field. This pins the selection-gating contract (Decision 4 / Edge cases line 550: when `totalCount` is not selected, no count query runs). Where observable, optionally wrap in `CaptureQueriesContext(connection)` (already imported at `test_library_api.py` line 12, used by the optimizer-SQL tests) and assert NO `COUNT(` query was issued (the count is skipped) — this is the strongest selection-gating proof; Worker 2 decides whether the SQL-capture assertion is robust against Strawberry's internal queries or whether the shape-only assertion suffices (record the choice). The minimum bar is: the query succeeds and returns correct edges with no `totalCount` in the response.
- **(e) `test_genre_connection_two_aliases_independent_total_counts`** — seed a genre set where two different `filter:` values match different counts (e.g. 3 genres whose names contain `"a"` and 1 whose name contains `"z"`). Query two **aliases** of the same field in one request:
  ```graphql
  query {
    matchA: allLibraryGenresConnection(filter: {name: {icontains: "a"}}) { totalCount edges { node { name } } }
    matchZ: allLibraryGenresConnection(filter: {name: {icontains: "z"}}) { totalCount edges { node { name } } }
  }
  ```
  Assert no `errors`; `matchA.totalCount` and `matchZ.totalCount` are the two distinct expected counts (proving the count rides the per-connection-instance attribute, NOT a shared `info.context` path-string stash — Decision 4 / Edge cases line 551). This is the per-instance-count contract.

Temp/scratch tests: none anticipated. All five are permanent live HTTP tests. Worker 3 may use `docs/builder/temp-tests/slice-4/` to probe the exact `ListConnection` `first: 0` / `endCursor` shapes against the locked Strawberry if needed, then promote/discard.

### Implementation discretion items

These are choices Worker 1 has assessed and deliberately leaves to Worker 2 — each is a stylistic/mechanical equivalent, not an architectural question:

- **The connection field's attribute name on `Query`.** `all_library_genres_connection` (→ `allLibraryGenresConnection`) is the recommended name (parallels `all_library_branches_via_list_field`). Worker 2 may pick another clear name as long as it (a) does not collide with the existing `all_library_genres` and (b) the five tests use the matching camelCase field name. Architectural constraint: it must be an additive field, not a replacement of `all_library_genres`.
- **Whether to add a thin module-private `_seed_genres(...)` helper** in `test_library_api.py` (a convenience wrapping inline `Genre.objects.create(...)` calls) vs. inline-creating in each test. Either satisfies the inline-create rule (the helper body is itself inline creates). Worker 2 picks whichever reads cleaner; if five tests duplicate the same genre-seed block, the helper is the DRY move (and Worker 3 will flag a 5× copy).
- **The `first: 0` `pageInfo` exact assertion shape** — Worker 2 reads the real `strawberry.relay.ListConnection` `first: 0` behavior (whether `hasNextPage` is `True`/`False`, whether `endCursor` is `null`/present) against the locked `0.316.0` and asserts the actual shape rather than an assumed one. The contract is "empty `edges` + valid `pageInfo`"; the precise `pageInfo` field values are whatever `ListConnection` produces (delegated, Edge cases line 544).
- **Whether test (d) adds a `CaptureQueriesContext` no-`COUNT` assertion** vs. a shape-only assertion. The SQL-capture is the stronger selection-gating proof but is sensitive to Strawberry's internal query shape; the shape-only assertion (correct edges, no `totalCount` in response) is the guaranteed-robust minimum. Worker 2 picks (record which in the build report); both honor the spec's "where observable, runs no count query" wording.
- **The exact `first` + `last` error-message substring** matched in test (b) — Worker 2 reads `connection.py::_guard_first_and_last`'s message and matches a stable substring (the message is the package's own, set in Slice 1).
- **`filter:` predicate wording** (which `GenreFilter` lookup to drive — `name: {icontains: ...}` vs `name: {exact: ...}` vs `id: {in: [...]}`). `GenreFilter.Meta.fields = {"id": ["exact", "in"], "name": ["exact", "icontains"]}` (verified in `apps/library/filters_genre.py`), so `name: {icontains: ...}` is the natural multi-match filter for the round-trip / two-alias tests. Worker 2 picks the lookup that makes the count arithmetic clearest.
- **`orderBy:` direction enum spelling** — the `Ordering` enum's ASC/DESC member names as they render in the SDL (`ASC` / `DESC` per the `0.0.8` ordering subsystem). Worker 2 reads the actual enum value names (e.g. via the existing order tests in the file) and uses them.

Worker 1 has NOT delegated any architectural question here. The two load-bearing design calls — (1) the export lands in this slice from the public surface, and (2) `config/schema.py` needs no change because the field rides `LibraryQuery` inheritance — are resolved in the plan (Implementation steps 1, 3 and the dedicated `config/schema.py` section), not left to discretion.

### Spec slice checklist (verbatim)

- [x] Promote `DjangoConnectionField` / `DjangoConnection` to the [`django_strawberry_framework/__init__.py`][package-init] public surface **in this slice**, alongside the live usage that proves the public shape (per [Decision 14](#decision-14--connectionpy-module-and-the-public-export-gate)).
- [x] Add a root `DjangoConnectionField` over the [`library`][fakeshop-library-schema] `GenreType` (already Relay-Node-shaped with both [`Meta.filterset_class`][glossary-metafilterset_class] and [`Meta.orderset_class`][glossary-metaorderset_class] declared) with `Meta.connection = {"total_count": True}`, exposed on the `library` `Query` via [`DjangoConnectionField(GenreType)`][connection], imported from the public surface.
- [x] Live HTTP tests in [`examples/fakeshop/test_query/test_library_api.py`][fakeshop-test-library]: (a) a full round-trip requesting `edges { node { id name } } pageInfo { hasNextPage endCursor } totalCount` with `filter:` + `orderBy:` + `first:` + `after:` asserting correct pagination, ordering, and `totalCount` on the unpaginated post-filter set; (b) the `first` + `last` `GraphQLError` path; (c) a `first: 0` empty-edges + `pageInfo` shape; (d) a query that omits `totalCount` and asserts the response is correct without a count (the selection-gating contract); (e) two aliases of the connection with different `filter:` values asserting independent `totalCount`s (the per-instance-count contract).

### Static inspection findings (Worker 1, planning)

Static-inspection helper (`scripts/review_inspect.py`) **SKIPPED for this slice** with recorded reason, per the BUILD.md "When to run the helper during build" thresholds:

- `django_strawberry_framework/__init__.py` — the only `django_strawberry_framework/` file Slice 4 touches, and the change is a **pure re-export**: one import line + two `__all__` tuple entries (~2-3 lines, zero logic). BUILD.md's Worker-1 trigger is "adds logic to any existing `.py` file with at least 150 source lines" OR any file under `optimizer/` / `types/`. `__init__.py` is 39 lines, adds no logic (a re-export), and is not under `optimizer/` / `types/`. The static-inspection-helper guidance explicitly permits skipping "for files where the artifact will be a 'no review-worthy logic' disposition (pure re-exports, single-line constants)." The export addition is a pure re-export → **skip, recorded here per the threshold.**
- `examples/fakeshop/apps/library/schema.py` and `examples/fakeshop/test_query/test_library_api.py` are **outside `django_strawberry_framework/`** (example project + tests). BUILD.md's Worker-1 helper triggers are scoped to package source; the example schema edit is one `Meta` line + one import + one field declaration (~3 lines, no new logic), and test files are never helper targets. **Skip.**

No file with ≥30 lines of new package logic (the Worker-3 threshold for re-running the helper on review) is touched; Worker 3's own helper rule will likewise find no package logic to inspect (`__init__.py` re-export only). Recorded so Worker 3 can confirm the skip is correct rather than an omission.

### Notes for Worker 3 (preview)

- The public-surface check this slice is the INVERSE of Slices 1-3: Slices 1-3 confirmed `__init__.py` `__all__` was UNCHANGED; Slice 4 must confirm `__all__` GREW by exactly `DjangoConnection` + `DjangoConnectionField` (and nothing else — `__version__` unchanged, no other symbol added), authorized by Decision 14 / the build-plan public-export flag. The CHANGELOG / GLOSSARY / version files stay untouched (those are Slice 5 / the joint cut).
- The five live tests are the spec's named (a)-(e); confirm each maps to its sub-check and that the `totalCount` assertions count the **pre-slice post-filter** set (test a) and are **per-instance** (test e, two aliases).

---

## Build report (Worker 2)

### Files touched

Grounded in `git status --short` after both ruff invocations.

- `django_strawberry_framework/__init__.py` — public-export promotion (Decision 14). Added `from .connection import DjangoConnection, DjangoConnectionField  # noqa: E402` directly above the `from .list_field import DjangoListField` line, and added `"DjangoConnection",` + `"DjangoConnectionField",` to `__all__` in alphabetical position between `"BigInt"` and `"DjangoListField"`. `__version__` left at `"0.0.8"` (Decision 13). This is the first and only slice that grows `__init__.py` `__all__` for this card.
- `examples/fakeshop/apps/library/schema.py` — (1) extended the public import `from django_strawberry_framework import (...)` to add `DjangoConnection` + `DjangoConnectionField` (imported from the public surface, not `django_strawberry_framework.connection`, per Decision 14). (2) Added `connection = {"total_count": True}` to `GenreType.Meta` (after `orderset_class`; `GenreType` already declares `interfaces = (relay.Node,)`, so `_validate_connection`'s Relay-Node requirement passes). (3) Added the additive class-attribute field `all_library_genres_connection: DjangoConnection[GenreType] = DjangoConnectionField(GenreType)` on `Query` (`LibraryQuery`), placed right after the existing `all_library_genres` resolver. The existing `all_library_genres` list resolver is untouched (both surfaces stay tested).
- `examples/fakeshop/test_query/test_library_api.py` — appended the five live HTTP tests `(a)`-`(e)` under a `spec-030 Slice 4` section banner, plus a thin module-private `_seed_genres(*names)` helper (inline `models.Genre.objects.create(...)` per the library inline-create rule — no services.py). All reuse `_post_graphql` / `_decode_global_id` / `CaptureQueriesContext` / the autouse `_reload_project_schema_for_acceptance_tests` fixture; no new fixture, no fixture modification.

**Not touched (confirmed by reading, per the plan):** `examples/fakeshop/config/schema.py` — the project `Query(LibraryQuery, …)` inherits the new field via subclassing, so no edit is needed; the reload fixture already reloads `config.schema` after `apps.library.schema`. `__version__`, `pyproject.toml`, `CHANGELOG.md`, `docs/GLOSSARY.md` all left as-is.

### Tests added or updated

All in `examples/fakeshop/test_query/test_library_api.py`, each `@pytest.mark.django_db`, each seeding genres inline via `_seed_genres(*names)`:

- `::test_genre_connection_full_round_trip` — (a) seeds 5 genres; `filter: {name: {iContains: "a"}}` matches 4 (`Alpha`/`Banana`/`Delta`/`Gamma`, excludes `Echo`) so `totalCount == 4` (≠ page size 2, ≠ grand total 5). Page 1 (`first: 2`, `orderBy: [{name: ASC}]`) returns `["Alpha", "Banana"]`, `hasNextPage == True`, non-empty opaque `endCursor`; each `node.id` decodes to `("GenreType", <digits>)`. Page 2 (`after: <endCursor>`, same filter/order) returns `["Delta", "Gamma"]`, disjoint from page 1, `hasNextPage == False`, `totalCount == 4` again.
- `::test_genre_connection_first_and_last_rejected` — (b) `first: 1, last: 1` → 200 with a GraphQL `errors` entry whose message contains `"mutually exclusive"` (the package's own `connection.py::_guard_first_and_last`, surfaced in `errors`, not a non-200).
- `::test_genre_connection_first_zero_empty_edges` — (c) `first: 0` → no errors, `edges == []`, `pageInfo.hasNextPage == True`, `pageInfo.endCursor is None`, `totalCount == 3` (pre-slice count unaffected by the zero window; count runs because `totalCount` is selected).
- `::test_genre_connection_total_count_omitted_no_count` — (d) `totalCount` omitted → correct edges (`["Alpha", "Beta"]`), `"totalCount" not in conn`, AND (under `CaptureQueriesContext`) no `COUNT(` SQL issued — the selection-gating proof.
- `::test_genre_connection_two_aliases_independent_total_counts` — (e) two aliases `matchA` (`iContains "a"` → 3) and `matchZ` (`iContains "z"` → 1) in one request report distinct `totalCount`s (per-instance count, not a shared context stash).

### Validation run

- `uv run ruff format .` — pass (`233 files left unchanged` on the final run).
- `uv run ruff check --fix .` — pass (`All checks passed!`; the COM812-vs-formatter warning is the repo's standing benign config note recorded in prior slices).
- `uv run python scripts/check_trailing_commas.py <touched files>` — initially exploded the `_seed_genres([...])` 4-/5-item list-literal args one-per-line, which then tripped COM812 on the wrapping call. Resolved at the source by changing `_seed_genres` to varargs (`*names`) so call sites stay inline (`_seed_genres("Alpha", "Beta", "Gamma")`); after that the comma-check is idempotent (`Fixed 0 file(s)`) and ruff lints clean.
- `git status --short` after both ruff invocations — classification:
  - **Slice-4-intended (stay; in Files touched):** `django_strawberry_framework/__init__.py`, `examples/fakeshop/apps/library/schema.py`, `examples/fakeshop/test_query/test_library_api.py`.
  - **Prior-slice working-tree carry (NOT my edits; the build does not commit between slices):** `django_strawberry_framework/connection.py` (untracked, Slice 1-2), `django_strawberry_framework/optimizer/extension.py` (Slice 2), `django_strawberry_framework/types/base.py` + `types/definition.py` (Slice 1), `tests/test_connection.py` (untracked, Slices 1-3), `tests/optimizer/test_extension.py` (Slice 2), `tests/types/test_base.py` (Slice 1), and the `bld-*.md` / `build-*.md` artifacts. Verified untouched by this pass.
  - **Baseline-dirty / Worker-1 carry (do not edit, do not revert):** `docs/GLOSSARY.md` (baseline-dirty Revision-3 anchoring), `docs/spec-030-connection_field-0_0_9.md` (Worker-1 spec edits from prior slices).
  - **No unrelated tool churn** was introduced this pass; nothing reverted.
- Focused tests (no `--cov*`):
  - `uv run pytest examples/fakeshop/test_query/test_library_api.py -k "genre_connection" --no-cov` → **5 passed**, 51 deselected.
  - `uv run pytest examples/fakeshop/test_query/test_library_api.py --no-cov` → **56 passed** (51 existing + 5 new) — the additive field did not break the existing library suite.

### Implementation notes

- **`first: 0` `pageInfo` shape (discretion item) — read from the locked source, not assumed.** Read `strawberry.relay.utils.SliceMetadata.from_arguments` + `strawberry.relay.types.ListConnection.resolve_connection` at the locked `0.316.0`. For `first: 0` with no `after`/`before`: `start=0`, `end=0`, `expected=0`, `overfetch=1`. The QuerySet path slices `[0:1]`, fetches one row, finds `len(edges)==1 == expected+1`, drops the overfetched edge → `edges == []`, `has_next_page == True`; `has_previous_page == (start>0) == False`; `start/end_cursor == None` (empty edges). Test (c) asserts exactly that real shape (`hasNextPage True`, `endCursor None`) — verified empirically by the passing test.
- **`_seed_genres` is varargs (`*names`), not a list param.** Chosen specifically so the comma-fixer/formatter keep call sites inline and COM812-clean; a single `list[str]` positional arg got exploded one-per-line and then required a trailing comma on the wrapping call, conflicting with the formatter. Varargs is the cleaner DRY shape and satisfies the library inline-create rule (the helper body is inline `Model.objects.create` calls). This is the plan's explicit Implementation-discretion item (thin `_seed_genres` helper vs inline-in-each-test) — chose the helper since five tests share the genre-seed block.
- **Test (d) uses the `CaptureQueriesContext` no-`COUNT` assertion (discretion item), not the shape-only minimum.** The genre connection's only queries are the row fetch and (when selected) the count, so the `COUNT(` substring check is robust here and is the strongest selection-gating proof. Combined with `"totalCount" not in conn`.
- **`filter:` lookup is `name: { iContains: "a" }`** (the camelCased `icontains` lookup; `GenreFilter.Meta.fields` declares `name: ["exact", "icontains"]`). Chosen so the count arithmetic is clear and the post-filter set differs from both the page size and the grand total. `orderBy:` uses the `ASC` enum member (matches the existing order tests in the file).
- **`first` + `last` error substring is `"mutually exclusive"`** — read verbatim from `connection.py::_guard_first_and_last`'s message ("`first` and `last` are mutually exclusive; supply only one.").
- **Consumer annotation `DjangoConnection[GenreType]` is accepted by Strawberry** against the resolved concrete `GenreTypeConnection` the factory wires through `relay.connection(...)` — the full library suite builds the real project schema on every reload and all 56 tests pass, so the annotation-vs-resolved-type fork (plan step 3 / Risks) did not surface. No action needed.

### Notes for Worker 3

- **Public-surface check is the INVERSE of Slices 1-3:** `git diff -- django_strawberry_framework/__init__.py` should show `__all__` GREW by exactly `"DjangoConnection"` + `"DjangoConnectionField"` (alphabetical, between `"BigInt"` and `"DjangoListField"`) plus the one `from .connection import …  # noqa: E402` line, and `__version__` UNCHANGED (`"0.0.8"`). Nothing else. Authorized by Decision 14 / the build-plan public-export flag.
- **Static-inspection helper:** correctly skipped per the plan's recorded thresholds — the only `django_strawberry_framework/` file touched is `__init__.py` (a ~3-line pure re-export, no logic, 41 lines, not under `optimizer/`/`types/`); the schema + test edits are outside the package. No package logic ≥30 new lines was added.
- **Undisturbed-suite check (spec line 602):** re-confirmed at implementation time — no `print_schema` / whole-SDL / Query-field-count / registered-type-count assertion exists in `examples/fakeshop/test_query/`. The two `fields {` introspection uses in `test_library_api.py` (lines ~358, ~1922) are scoped to named `__type(name: "BookType")` queries, unaffected by the additive root field. Full library suite passes (56), confirming the new `allLibraryGenresConnection` root field broke nothing.
- The five tests map 1:1 to the spec's named (a)-(e). `totalCount` in (a) is asserted pre-slice/post-filter (4, with page size 2 and grand total 5 both distinct); (e) asserts per-instance counts across two aliases.

### Notes for Worker 1 (spec reconciliation)

- No spec gap, conflict, or unstated assumption surfaced. The plan's two load-bearing calls held: (1) the export landed from the public surface in this slice; (2) `config/schema.py` needed no change (inheritance carries the field). The annotation-vs-resolved-type fork and the argument-injection fork did not surface (the live schema builds and serves correctly). Nothing to reconcile.

---

## Review (Worker 3)

Reviewed the three Slice-4 files via `git diff` (the cumulative working tree carries Slices 1-3 + the baseline-dirty `docs/GLOSSARY.md` + the Worker-1 spec edits; navigated by Worker 2's `### Files touched`). Ran the five focused tests, the full library suite, and three non-vacuity probes (deleted). All five tests pass; all three probes confirm the load-bearing assertions are data-driven, not constants.

### High:

None.

### Medium:

None.

### Low:

None.

### DRY findings

- **Clean.** No new test helper, no new fixture, no new production helper — exactly as the plan committed. `_seed_genres(*names)` is the single thin module-private convenience; its body is inline `models.Genre.objects.create(...)` calls, so it honors the library inline-create rule (`AGENTS.md` #"Library acceptance tests use inline Model.objects.create") rather than violating it, and it removes a 5x copy of the genre-seed block across the new tests (justified extraction, not premature abstraction). The varargs shape (`*names`) is the right call — it keeps call sites inline and avoids the comma-fixer/COM812 explosion Worker 2 documented.
- The five tests reuse the existing `_post_graphql` (line 76), `_decode_global_id` (line 616), `CaptureQueriesContext` + `connection` (lines 10, 12), and the autouse `_reload_project_schema_for_acceptance_tests` fixture (line 47) verbatim — no re-implementation, no fixture modification. The new `allLibraryGenresConnection` root field is recreated on every reload because it is declared at `apps.library.schema` module-body level (the module the fixture reloads).
- The connection field's `filter:` / `orderBy:` arguments reuse `GenreType.Meta.filterset_class` / `orderset_class` (the same `GenreFilter` / `GenreOrder` the existing `all_library_genres` resolver uses), so no new input type is generated (Decision 6 stable-name contract). Confirmed `GenreFilter.Meta.fields = {"id": ["exact","in"], "name": ["exact","icontains"]}` and `GenreOrder.Meta.fields = ["id","name"]` — the tests' `name: {iContains: ...}` and `orderBy: [{name: ASC}]` are both valid against the declared sidecars; `Ordering.ASC = "ASC"` is the real enum member spelling.

### Public-surface check

**INVERSE of Slices 1-3, PASSED.** `git diff -- django_strawberry_framework/__init__.py` shows `__all__` GREW by EXACTLY two entries — `"DjangoConnection"` and `"DjangoConnectionField"` — inserted in alphabetical position between `"BigInt"` and `"DjangoListField"`, plus the single import line `from .connection import DjangoConnection, DjangoConnectionField  # noqa: E402` (mirrors the sibling `# noqa: E402` imports; both symbols live in the one flat `connection.py` module). Nothing else changed in the tuple or the import block. This is authorized by **Decision 14** (spec line 517: *"`DjangoConnectionField` and `DjangoConnection` are promoted to the `django_strawberry_framework` public surface in Slice 4 — the same functional slice as the live fakeshop usage that proves the public shape"*) and the build-plan public-export flag (build-030 line 28). The tested-usage promotion gate is satisfied: the live tests prove the end-to-end public shape in the same slice. `__version__` is UNCHANGED (still `"0.0.8"`, line 27) per **Decision 13** (spec line 507) and the build-wide version-bump-owner flag (build-030 line 26). Both new symbols are correctly public-named in `connection.py` (`connection.py::DjangoConnection` at line 114, a subscriptable `relay.ListConnection[NodeType]` generic so the `DjangoConnection[GenreType]` consumer annotation resolves; `connection.py::DjangoConnectionField` factory at line 517) — no rename needed.

### CHANGELOG sanity

Not applicable; slice did not modify `CHANGELOG.md`. (The `CHANGELOG.md` `[Unreleased]` `### Added` bullet is Slice 5's explicit per-card permission grant per Decision 13 / the Doc-updates section; confirmed `CHANGELOG.md` is clean in `git status`.)

### Documentation / release sanity

Not applicable to a doc/release surface change in this slice — Slice 4 touches example-project code (`apps/library/schema.py`, `test_library_api.py`) + the public export (`__init__.py`), NOT docs/KANBAN/archive/release-metadata. Confirmed clean (`git status --short`): `pyproject.toml`, `tests/base/test_init.py`, `uv.lock`, `CHANGELOG.md` are all UNMODIFIED. `docs/GLOSSARY.md` IS dirty but is the **baseline-dirty Revision-3 `Meta.connection` anchoring** carried per build-030 line 21 (it was `M docs/GLOSSARY.md` at session start) — NOT a Slice-4 edit; inspected the diff and it is exclusively the `Meta.connection` Index row + "Type generation"/"Relay" browse-by-category rows + the `## Meta.connection` entry body, all still **`planned for 0.0.9`** (correctly NOT flipped to `shipped` — that is Slice 5's job). `docs/spec-030-…md` is dirty from prior-slice Worker-1 edits (out of scope). No doc/release/KANBAN/GLOSSARY-shipped-flip surface was changed by this slice.

### What looks solid

- **No scope creep.** Exactly three files changed by this slice: `django_strawberry_framework/__init__.py`, `examples/fakeshop/apps/library/schema.py`, `examples/fakeshop/test_query/test_library_api.py`. `examples/fakeshop/config/schema.py` is UNTOUCHED and correctly did not need a change — the project `Query(LibraryQuery, …)` inherits the additive `all_library_genres_connection` field through subclassing, and the reload fixture reloads `config.schema` after `apps.library.schema`, so the rebuilt project schema picks it up. The existing `all_library_genres` list resolver is UNTOUCHED (the new field is additive, placed after it), so both surfaces stay tested.
- **The five tests are non-vacuous and correct** — the plan's top risk, cleared:
  - **(a) full round-trip:** `totalCount == 4` counts the PRE-SLICE POST-FILTER set. The test data makes the three numbers genuinely distinct: grand total 5 (`Alpha/Gamma/Echo/Delta/Banana`), post-filter `icontains "a"` = 4 (Echo excluded — verified: E-c-h-o has no "a"), page size 2. The `after:` second page is real: a deleted probe confirmed that re-running the same `first: 2` query WITHOUT `after:` repeats page 1 (`[Alpha, Banana]`), and WITH `after: <endCursor>` advances to the disjoint `[Delta, Gamma]` — the cursor is load-bearing. Ordering (`name ASC`) and `hasNextPage` transitions (`True` → `False`) are both asserted. `node.id` is decoded to `("GenreType", <digits>)`, proving real GlobalIDs.
  - **(b) `first` + `last`:** asserts a 200 with a GraphQL `errors` entry whose joined messages contain `"mutually exclusive"` — verified verbatim against `connection.py::_guard_first_and_last` (line 87: *"Connection arguments `first` and `last` are mutually exclusive; supply only one."*). Correctly a wire `errors` entry, not a non-200.
  - **(c) `first: 0`:** asserts the ACTUAL locked-Strawberry-`0.316.0` `ListConnection` shape — `edges == []`, `hasNextPage is True`, `endCursor is None`. Verified this is real (not assumed) via a deleted probe: `first: 0` over an EMPTY set yields `hasNextPage is False`, so the `True` over a non-empty set is the genuine overfetch-and-drop behavior, data-driven. `totalCount == 3` correctly survives the zero window (pre-slice count, and selected here so it runs).
  - **(d) `totalCount` omitted:** asserts `"totalCount" not in conn` AND, under `CaptureQueriesContext`, no `COUNT(` SQL. The SQL-capture is genuinely non-vacuous: a deleted probe confirmed that when `totalCount` IS selected the same field emits a `COUNT(` query, so the no-`COUNT(` assertion truly proves selection-gating skipped the count (Decision 4). This is the strongest selection-gating proof and is robust here because the connection's only queries are the row fetch and the gated count.
  - **(e) two aliases:** `matchA` (`icontains "a"` → `Alpha/Banana/Cobra` = 3) and `matchZ` (`icontains "z"` → `Zephyr` = 1) in one request report DISTINCT `totalCount`s. Verified the filters yield genuinely different counts (Zephyr has no "a"; only Zephyr has "z"), proving the count rides the per-connection-instance attribute, not a shared `info.context` stash (Decision 4 / Edge cases line 551).
- **ORM correctness:** no wrong-data or N+1 risk introduced by the slice. The field rides the Slice-2 composition pipeline (visibility → filter → order → default-order → optimizer → slice); Slice 4 adds no ORM logic, only the live exercise. The `0.0.9` flat-walker connection-unaware empty-plan constraint is the documented Decision 11 / `033` gap, not a Slice-4 defect.
- **Spec slice checklist walk:** all three verbatim sub-checks are ticked `- [x]` and each genuinely landed in the diff — (1) the two exports in `__init__.py`; (2) the `Meta.connection = {"total_count": True}` + public-surface import + additive `DjangoConnectionField(GenreType)` field in `schema.py`; (3) the five live tests (a)-(e) in `test_library_api.py`. No over-ticks, no silently-unaddressed boxes.

### Temp test verification

- Temp probe `examples/fakeshop/test_query/test_slice4_probe.py` (placed in `test_query/` so it inherited the autouse reload fixture + conftest; NOT under `docs/builder/temp-tests/slice-4/`, which would miss the live-HTTP harness). Three probes: (1) `totalCount` selected DOES emit `COUNT(` (proves test (d) non-vacuous); (2) `first: 0` over empty set → `hasNextPage False` (proves test (c)'s `True` is data-driven); (3) `after:`-vs-no-`after:` (proves test (a) page-2 pagination is real). All three passed.
- **Disposition: deleted.** The three behaviors they verify are already pinned by the permanent tests (a), (c), (d) — the probes confirmed non-vacuity rather than catching a bug, so no promotion is needed. `docs/builder/temp-tests/slice-4/` was created but left empty (the probe needed the conftest-bearing `test_query/` location); harmless.

### Notes for Worker 1 (spec reconciliation)

- Nothing to reconcile. The plan's two load-bearing calls held in the diff: (1) the public export landed from the public surface in this slice (Decision 14); (2) `config/schema.py` needed no change (inheritance carries the field). The annotation-vs-resolved-type fork (Risks, spec line 624) and the argument-injection fork (spec line 623) did not surface — the live schema builds and serves correctly across all 56 library tests. No spec gap, conflict, or unstated assumption.

### Review outcome

`review-accepted`. Zero High / Medium / Low findings. The public-surface inverse check passed (exactly the two exports added, `__version__` unchanged); the five live tests are non-vacuous and correct, with the `totalCount` pre-slice-post-filter semantics, the per-instance two-alias contract, and the real `ListConnection` `first: 0` shape all independently verified; DRY is clean; no scope creep (only the three intended files; `config/schema.py` + version/CHANGELOG/GLOSSARY-shipped surfaces untouched). Artifact `Status:` set to `review-accepted`.

---

## Final verification (Worker 1)

Read the full artifact (Plan / Build report / Review), the current working-tree diff for the three Slice-4 files, and the spec Slice-4 checklist + Decision 14 + Decision 13. Ran the focused suite. Confirmed all guards.

### Summary

Slice 4 is **final-accepted**. The slice promoted `DjangoConnection` / `DjangoConnectionField` to the public surface and proved the public shape with live HTTP coverage, in one coherent diff across exactly three files:

- `django_strawberry_framework/__init__.py` — `__all__` grew by **exactly** `"DjangoConnection"` + `"DjangoConnectionField"` (alphabetical, between `"BigInt"` and `"DjangoListField"`) plus one import line `from .connection import DjangoConnection, DjangoConnectionField  # noqa: E402`. `__version__` UNCHANGED at `"0.0.8"`.
- `examples/fakeshop/apps/library/schema.py` — public-surface import of both symbols; `connection = {"total_count": True}` added to `GenreType.Meta` (already `interfaces = (relay.Node,)` + both sidecars); additive `all_library_genres_connection: DjangoConnection[GenreType] = DjangoConnectionField(GenreType)` on `Query` (the existing `all_library_genres` list resolver untouched; Meta-only derivation, no `filters=`/`order=`/`total_count=` kwargs). `config/schema.py` correctly NOT touched (the field rides `LibraryQuery` inheritance).
- `examples/fakeshop/test_query/test_library_api.py` — five `@pytest.mark.django_db` live HTTP tests `(a)`–`(e)` + the thin module-private `_seed_genres(*names)` inline-create helper; reuse the autouse reload fixture, `_post_graphql`, `_decode_global_id`, and `CaptureQueriesContext`.

**Final-verification checklist results:**

- **Spec slice checklist audit (3/3 `- [x]` truly landed, no over-tick):**
  1. Public export promotion — landed in `__init__.py` (verified the `git diff`: exactly the two `__all__` entries + the one import line).
  2. Root `DjangoConnectionField(GenreType)` over the library `GenreType` with `Meta.connection = {"total_count": True}`, imported from the public surface — landed in `schema.py` (verified all three edits in the diff).
  3. Five live HTTP tests `(a)`–`(e)` — landed in `test_library_api.py` (verified all five functions present, each mapping to its named spec sub-check; the `totalCount` in (a) counts the pre-slice post-filter set = 4 ≠ page 2 ≠ grand total 5; (e) asserts per-instance counts 3 vs 1 across two aliases). No remaining `- [ ]`; no deferral needed.
- **Public-surface (Decision 14) check — PASSED.** `git diff -- django_strawberry_framework/__init__.py` shows `__all__` grew by EXACTLY `DjangoConnection` + `DjangoConnectionField` and nothing else; authorized by **Decision 14** (spec line 517: *"`DjangoConnectionField` and `DjangoConnection` are promoted to the `django_strawberry_framework` public surface in Slice 4 — the same functional slice as the live fakeshop usage that proves the public shape"*) and the build-plan public-export flag (build-030 line 28). `__version__` UNCHANGED at `"0.0.8"` per **Decision 13** (spec line 507 / build-030 line 26).
- **DRY check across Slice 4 + prior slices — clean.** No new fixture, no new production helper. `_seed_genres(*names)` is a single justified extraction (consolidates a 5× genre-seed block; body is inline `Genre.objects.create(...)` per the library inline-create rule) — distinct from the existing `_seed_library_graph` / `_seed_branch_with_two_shelves` / `_seed_branches_with_varying_shelves` helpers (which build relationship graphs, not name-only genre rows). The connection's `filter:`/`orderBy:` arguments reuse `GenreType.Meta.filterset_class`/`orderset_class` (same `GenreFilter`/`GenreOrder` as the list resolver), so no new input type. The Slice-2 M-DRY1 integration carry-forward (`_validate_djangotype_target` shared 4-guard validator across `list_field.py` + `connection.py`) is untouched by Slice 4 and correctly remains an integration-pass item, not a Slice-4 defect.
- **Existing tests pass.** `uv run pytest examples/fakeshop/test_query/test_library_api.py --no-cov` → **56 passed** (51 existing + 5 new). The additive root field broke nothing.
- **Guards confirmed.** `git diff --stat` shows `pyproject.toml`, `tests/base/test_init.py`, `uv.lock`, `CHANGELOG.md`, and `examples/fakeshop/config/schema.py` all UNCHANGED. `docs/GLOSSARY.md` is dirty but is exactly the carried baseline-dirty Revision-3 `Meta.connection` anchoring (Index row + "Type generation"/"Relay" browse rows + the `## Meta.connection` entry body, all still `planned for 0.0.9`) — NOT flipped to `shipped` (that is Slice 5) and NOT reverted.

### Spec changes made (Worker 1 only)

- `docs/spec-030-connection_field-0_0_9.md` line 5 — advanced the top status line `in build — Slice 3 accepted` → `in build — Slice 4 accepted` (per-spawn status-line re-verification; Slice 4 now accepted). `uv run python scripts/check_spec_glossary.py --spec docs/spec-030-connection_field-0_0_9.md` reports `OK: 51 terms` after the edit. No other spec edit — the build report and review surfaced no spec gap, conflict, or unstated assumption to reconcile.

---
<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[glossary-metafilterset_class]: ../GLOSSARY.md#metafilterset_class
[glossary-metaorderset_class]: ../GLOSSARY.md#metaorderset_class

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[connection]: ../../django_strawberry_framework/connection.py
[package-init]: ../../django_strawberry_framework/__init__.py

<!-- tests/ -->

<!-- examples/ -->
[fakeshop-library-schema]: ../../examples/fakeshop/apps/library/schema.py
[fakeshop-test-library]: ../../examples/fakeshop/test_query/test_library_api.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
[strawberry-relay]: https://strawberry.rocks/docs/guides/relay
