# Build: Slice 5 — live library SQL-shape coverage

Spec reference: `docs/spec-033-connection_optimizer-0_0_9.md` (Slice checklist lines 78-80; Test plan Slice 5 lines 528-533; Test plan preamble + live-first rule lines 459-464; Edge cases — visibility-filtered targets line 448, outer-`totalCount` direct-children scope line 456; Goal 5 line 119; DoD item 8 line 615; the cacheable-vs-visibility-disjoint note line 350)
Status: final-accepted

## Plan (Worker 1)

Slice 5 is **live-HTTP test coverage only — no source change** (build plan line 21; spec line 79 as reconciled below). It adds the SQL-shape assertions that `spec-032`'s Slice-6 nested-connection tests deferred to this card: the two existing behavior pins (`test_genre_books_connection_behavior`, `test_book_genres_connection_sidecars_and_total_count`) asserted *behavior only* (right rows, right order, no overlap) and explicitly named this card as the owner of the deferred fixed-query-count / no-per-parent-COUNT / visibility-window assertions. The live nested surface already exists on the fakeshop library graph (Slice-2 consumes the Slice-1 window; both `final-accepted`), so Slice 5 only *observes* it through `/graphql/`.

**Carry-forward from Slice 2's artifact (`bld-slice-2-fast_path.md`, load-bearing):** the windowed fast path fires only when the **parent queryset flows through the optimizer's root gate** (`info.path.prev is None`). The optimizer is root-gated uniformly for any root resolver returning a Django `QuerySet` — a plain `@strawberry.field` returning a queryset (`all_library_genres`, `all_library_books`) OR a `DjangoConnectionField` root (`all_library_genres_connection`); the walker then recurses and recognizes the nested synthesized connection via the `relation_connections` definition slot (verified at `optimizer/walker.py::_walk_selections` #"if django_name in relation_connections"). So the nested `booksConnection` / `genresConnection` windows plan under both the list roots and the connection root. The fakeshop project schema runs **strictness-off** (`config/schema.py` `DjangoOptimizerExtension()` with no `strictness=`), so **no strictness assertions belong in Slice 5** (those are Slice 4's package-only pins; the fakeshop suite cannot exercise `"raise"`/`"warn"`).

### Spec gap found and reconciled (Worker 1, recorded under `### Spec changes made` below)

The spec's line-79 sub-bullet named a single query `allLibraryGenresConnection { edges { node { booksConnection(first: N) { edges { node } totalCount } } } }` — selecting `totalCount` on `booksConnection`. But the live library schema (`examples/fakeshop/apps/library/schema.py`) declares `Meta.connection = {"total_count": True}` **only on `GenreType`** (line 184); `BookType.Meta` (lines 94-112) declares `interfaces=(relay.Node,)`, `filterset_class`, `orderset_class` — and **no `connection`**. So `BookType`'s connections (the nested `booksConnection`) expose **no `totalCount` field**, and that exact query is a GraphQL validation error. Confirmed via git history: `BookType` never declared `total_count`; `GenreType` is the lone library type with it; `GenreType` has no `get_queryset` filter.

The DoD (item 8, line 615), the Test plan (lines 530-532), and the size-budget row (line 430) all name **three distinct properties** — fixed query count, nested-`totalCount` zero-extra-queries, visibility-filtered window — not one combined query; only the line-79 prose merged them into an impossible single shape. The reconciliation keeps Slice 5 **test-only** and uses the live graph as-is:

- **`booksConnection`** (target `BookType`, `get_queryset`-filtered `circulation_status="repair"`, NO `total_count`) carries the **fixed-query-count** pin and the **visibility-window** pin — both on `edges { node }` + `pageInfo` (no `totalCount` selected).
- **`genresConnection`** (target `GenreType`, `total_count` ON, no visibility filter) carries the **nested-`totalCount`-no-per-parent-COUNT** pin — nested under the optimizer-rooted `allLibraryBooks` list resolver, the exact forward-M2M shape the shipped `test_book_genres_connection_sidecars_and_total_count` already established.

Spec line 79 was edited to state the `totalCount` siting explicitly and reaffirm "test-only, no `Meta.connection` added to `BookType`". **No library-schema source change** — adding `total_count` to `BookType` would be (a) out of Slice 5's test-only contract, (b) a Worker-1-forbidden source edit at planning, and (c) an SDL change risking the "behavior pins stay green unmodified" requirement (every `BookType` connection would gain a `totalCount` field).

### DRY analysis

- **Existing patterns reused.**
  - **Query-count idiom — `CaptureQueriesContext(connection)`.** The established query-count assertion mechanism in this file (`test_library_api.py:262`, `:298`, `:1060`, `:1709` — every optimizer SQL-shape test uses `with CaptureQueriesContext(connection) as captured:` then asserts `len(captured.captured_queries)` / `== N` or `<= N`). Slice 5's three new tests reuse this verbatim — do NOT introduce `django_assert_num_queries` (the file's convention is `CaptureQueriesContext`; mixing idioms is a DRY/consistency smell). The import is already present (`from django.test.utils import CaptureQueriesContext`, line 12; `from django.db import connection`, line 10).
  - **`_reload_project_schema_for_acceptance_tests` autouse fixture (`test_library_api.py:48-51`).** Every test in the file already rides this autouse fixture (clears the global registry, reloads `apps.library.schema` → `config.schema` → `config.urls`, clears URL caches). The new tests inherit it automatically by living in the file — **add no per-test fixture setup**; do not re-import `apps.library.schema` classes at module level (the file-header reload invariant at lines 27-28 — module-level imports hold stale class objects after reload). `BookType` is imported **in-test-body** only where a `global_id_for` mint is needed (the pattern at `test_node_hidden_row_null_live:2852`); Slice 5's tests do not need `global_id_for`, so no in-body type import is required.
  - **`_post_graphql(query)` / `_post_graphql_as_staff(query)` helpers (`test_library_api.py:77-83`, `:711-721`).** `_post_graphql` POSTs to `/graphql/` as an anonymous client; `_post_graphql_as_staff` creates a staff user, `force_login`s, and POSTs. The visibility test reuses BOTH (anonymous → repair books hidden; staff → repair books visible) — exactly the pair `test_node_hidden_row_null_live` uses. No new posting helper.
  - **Inline `Model.objects.create` seeding (AGENTS.md "Library acceptance tests use inline Model.objects.create; the library app has no services.py").** Reuse `_seed_shelf()` (`test_library_api.py:2552-2555`) for the branch+shelf so `Book` fixtures stay one-liners, exactly as the two behavior pins do. Genre/Book/`genres.add(...)` follow the existing `test_genre_books_connection_behavior:2727-2737` seeding shape.
  - **Connection-payload extraction shape.** The behavior pins already navigate `payload["data"]["allLibraryGenres"][0]["booksConnection"]` (list root) and `payload["data"]["allLibraryBooks"][0]["genresConnection"]`. For the connection root, navigate `payload["data"]["allLibraryGenresConnection"]["edges"][i]["node"]["booksConnection"]` (mirrors the root-connection extraction at `test_genre_connection_full_round_trip:2177`).
- **New helpers justified.** **None required.** Optionally a tiny local helper inside the fixed-query-count test to build the two-level query string for a given `first` and run it under `CaptureQueriesContext` (parameterized over 3-genre vs 10-genre seedings) — but this is a per-test closure, not a module-level helper; Worker 2's discretion (see Implementation discretion items). No shared helper crosses tests, so none is extracted. (Condition that would justify extraction later: a fourth test needing the same two-level builder — not the case in this slice.)
- **Duplication risk avoided.** The naive risk is **re-seeding the same genre/book graph three times with copy-pasted `Model.objects.create` blocks**. Each test has a *different* cardinality requirement (3 vs 10 parent genres for the independence pin; a single book with N visible + M repair books for the visibility pin; a single book with N genres for the `totalCount` pin), so a single shared fixture would not fit all three — the seedings are legitimately distinct, not duplicated. The shared surface (`_seed_shelf`, `_post_graphql*`, `CaptureQueriesContext`) is already factored. The risk of **re-spelling the GraphQL query string** across the 3-genre and 10-genre runs of the fixed-query-count test IS real and IS avoided by parameterizing one query-builder closure over the seed count (Implementation step 1).

### Implementation steps

Line numbers are pin-at-write-time navigational hints; Worker 2 re-locates by symbol/anchor before editing. All edits land in `examples/fakeshop/test_query/test_library_api.py` at the `TODO(spec-033 Slice 5)` anchor block (lines 2874-2887) — the anchor already names the three test functions. Worker 2 **removes the anchor comment block** in the same change that lands the tests.

1. **`test_nested_books_connection_fixed_query_count`** — the per-parent-independence pin (spec line 530; Goal 5; DoD item 8).
   - GraphQL shape (the cookbook two-level connection-root shape, `totalCount` dropped from `booksConnection` per the reconciliation): `query { allLibraryGenresConnection { edges { node { booksConnection(first: 2) { edges { node { title } } pageInfo { hasNextPage } } } } } }`. Anonymous client (`_post_graphql`).
   - Fixture cardinalities: seed **3 genres**, each with the same set of books (e.g. 3 books per genre via `genres.add`), in one run; seed **10 genres** with the same per-genre book set in a second run (separate `@pytest.mark.django_db` test invocations, or a parametrized fixture-count — Worker 2 discretion). Reuse `_seed_shelf()` for the shelf; inline `Book.objects.create(...)` + `book.genres.add(genre)`.
   - Query-count mechanism: wrap each run in `with CaptureQueriesContext(connection) as captured:`; capture `len(captured.captured_queries)` for the 3-genre run and the 10-genre run; **assert the two counts are EQUAL** (parent-count independence — the literal N+1 disproof). Optionally also assert the absolute count equals a small fixed N (Worker 2 pins the exact integer empirically — expect: 1 root genres query + 1 windowed `booksConnection` prefetch query, plus the root-connection's own machinery; do NOT hard-guess the integer in the plan, pin it from the actual run). The load-bearing assertion is **equality across the two parent counts**; an exact-N assertion is a stronger secondary pin if Worker 2 derives it.
   - Wire assertion: each genre node's `booksConnection.edges` returns the windowed page (2 books per genre, correct titles) — proves the window is per-parent-correct, not a single shared slice.

2. **`test_nested_total_count_no_per_parent_count`** — selecting nested `totalCount` adds zero queries over the same selection without it (spec line 531; Edge case line 456; DoD item 8).
   - GraphQL shape (rides `genresConnection`, the `total_count`-opted target, nested under the optimizer-rooted `allLibraryBooks` list resolver — the forward-M2M shape `test_book_genres_connection_sidecars_and_total_count` established): build TWO queries differing only in the nested `totalCount` selection:
     - WITHOUT: `query { allLibraryBooks { genresConnection(first: 2) { edges { node { name } } } } }`
     - WITH: `query { allLibraryBooks { genresConnection(first: 2) { totalCount edges { node { name } } } } }`
   - Fixture: seed a single (or a few) `Book` with N>2 genres via `genres.add` (reuse the `test_book_genres_connection_sidecars_and_total_count:2782-2789` shape — one book, four genres). Multiple books strengthen the "no per-parent COUNT" claim (the count must come from the `_dst_total_count` window annotation, not a per-book `COUNT`). Anonymous client (`GenreType` has no visibility filter, so anonymous sees all genres).
   - Query-count mechanism: run each query under its own `CaptureQueriesContext(connection)`; **assert `len(with_total_count) == len(without_total_count)`** — selecting nested `totalCount` adds ZERO queries (the window already carries `_dst_total_count`). Additionally assert the `totalCount` value is correct (== the genre count for the book, not the page size).

3. **`test_nested_window_respects_book_visibility`** — `circulation_status="repair"` books excluded from non-staff nested pages AND nested `totalCount`; staff sees them (spec line 532; Edge case line 448; DoD item 8).
   - GraphQL shape: `query { allLibraryGenresConnection { edges { node { booksConnection { edges { node { title } } } } } } }` (the visibility surface is `booksConnection`, whose target `BookType.get_queryset` filters `circulation_status="repair"`). `booksConnection` has no `totalCount` field — so the "AND nested `totalCount`" half of the spec line is asserted via the **visible-edge count / page contents**, not a `totalCount` field that does not exist (this is the line-79 reconciliation: the post-visibility window's row count IS the count, computed post-`get_queryset` per Edge case line 448 — "row numbers and `_dst_total_count` are computed post-visibility"). If Worker 2 wants a `totalCount` assertion specifically, route a SECOND query through `genresConnection` (which has `totalCount`) under a visibility-bearing root — but `GenreType` has no visibility filter, so the genuine visibility-filtered-`totalCount` proof is unavailable live; the `booksConnection` edge-count proof is the correct live surface for `BookType`'s visibility. State this explicitly in the test docstring.
   - Fixture: one genre with several visible books (e.g. `circulation_status` AVAILABLE/CHECKED_OUT) + one or more `circulation_status=models.Book.CirculationStatus.REPAIR` books, all `genres.add(genre)`. Reuse `_seed_shelf()`; mirror `test_genre_books_connection_behavior:2727-2737` (which already seeds a `REPAIR` "Withdrawn" book).
   - Assertions: (a) **anonymous** (`_post_graphql`): the repair book title is absent from `booksConnection.edges`, and the visible-page contents match the post-visibility set; (b) **staff** (`_post_graphql_as_staff`): the repair book IS present in `booksConnection.edges`. This pins that `BookType.get_queryset` runs INSIDE the windowed nested connection (post-visibility row numbering), not bypassed — the live proof of Edge case line 448. (No `CaptureQueriesContext` needed here unless Worker 2 wants to also re-pin the fixed-query-count under the visibility filter — optional, not required.)

### Test additions / updates

- **Two shipped behavior pins stay green UNMODIFIED — wire parity (spec line 533; DoD item 8):**
  - `test_genre_books_connection_behavior` (`test_library_api.py:2718-2769`) — the reverse-M2M `booksConnection` behavior pin (right rows, right order, no overlap; the anonymous repair-book-hidden bonus). Slice 5 must NOT touch it; its wire results are unchanged by the now-planned window (Slice 2 proved fast-path == pipeline wire parity in the package suite). Worker 1 confirms at final verification that the diff does not modify it.
  - `test_book_genres_connection_sidecars_and_total_count` (`test_library_api.py:2772-2814`) — the forward-M2M `genresConnection` sidecars + `totalCount` behavior pin. Unchanged. The new `test_nested_total_count_no_per_parent_count` is its SQL-shape sibling (re-asserts the same `totalCount` value, adds the zero-extra-query pin) — **re-assert wire parity, do not rewrite** the behavior pin.
- **New tests (names verbatim from the Slice-5 Test plan, lines 530-532):**
  - `test_nested_books_connection_fixed_query_count` — `CaptureQueriesContext`; equal query count for 3-genre vs 10-genre seedings over `allLibraryGenresConnection { edges { node { booksConnection(first: 2) { edges { node { title } } } } } }`.
  - `test_nested_total_count_no_per_parent_count` — `CaptureQueriesContext`; equal query count with vs without nested `totalCount` on `allLibraryBooks { genresConnection(first: 2) { [totalCount] edges { node { name } } } }`; correct `totalCount` value.
  - `test_nested_window_respects_book_visibility` — anonymous excludes / staff includes `circulation_status="repair"` books in `booksConnection.edges` under `allLibraryGenresConnection`.
- **No new test file** (build plan line 21; Decision 11): all three extend `test_library_api.py`. **No `--cov*` flags** in any focused run Worker 2 makes.
- **Temp/scratch tests for Worker 3:** Worker 3 may want to pin the *exact* absolute query count (not just equality) by running the two-level query once under `CaptureQueriesContext` and printing `captured.captured_queries` — useful to confirm the count is the small fixed N (root + one window) and not silently `1 + N`. This is an empirical confirmation, optionally promoted into the test as a secondary exact-N assertion. Note under `docs/builder/temp-tests/slice-5/` if used.

### Implementation discretion items

Assessed and decided to be Worker 2's choice (Worker-1 has resolved the design; these are equivalent-shape / mechanical choices only):

- **3-genre vs 10-genre as two separate `@pytest.mark.django_db` test functions, one parametrized test, or two `CaptureQueriesContext` blocks inside one test body.** The contract is fixed: *the captured query count is equal for 3 parents and 10 parents*. Worker 2 picks the cleanest shape (a single test body with two seed-and-capture passes asserting equality reads cleanest and keeps the query string single-sited; a `@pytest.mark.parametrize` over the genre count with an equality assertion against a captured baseline is also fine).
- **Whether to add a secondary exact-N query-count assertion** (alongside the load-bearing equality assertion). Encouraged if Worker 2 derives N empirically, but the equality-across-parent-counts assertion is the required pin; the exact-N is a strengthening, not a requirement. Pin N from the actual run, never a guess.
- **Books-per-genre count and visible/repair split in the fixtures.** Any cardinality that makes the assertions unambiguous (e.g. ≥3 books per genre with `first: 2` so `hasNextPage` is meaningful; ≥1 repair + ≥1 visible for the visibility test) is fine.
- **Local query-builder closure vs inline f-string** inside the fixed-query-count test (the DRY pin is only that the 3-genre and 10-genre runs share ONE query string — a closure or a module-local constant both satisfy it).
- **Number of parent books in `test_nested_total_count_no_per_parent_count`** (one book is sufficient for the value assertion; multiple books strengthen the "no per-parent COUNT" claim — Worker 2's call, multiple preferred).

### Spec slice checklist (verbatim)

- [x] Slice 5: live library nested-connection SQL-shape coverage
  - [x] [`examples/fakeshop/test_query/test_library_api.py`][test-library]: the [`spec-032`][spec-032] Slice-6 nested-connection tests (`test_genre_books_connection_behavior`, `test_book_genres_connection_sidecars_and_total_count`) asserted **behavior only** with the explicit note that SQL-shape assertions are this card's deliverable. Slice 5 adds the deferred pins: a two-level `allLibraryGenresConnection { edges { node { booksConnection(first: N) { edges { node } } } } }` query (the cookbook-equivalent nested-connection shape the card's DoD names) executes in a **fixed query count** independent of the number of parent genres, and the nested `totalCount` adds no per-parent `COUNT`. **`totalCount` siting**: `booksConnection`'s target `BookType` does **not** declare `Meta.connection = {"total_count": True}` (only `GenreType` does), so a `totalCount` field exists only on the `total_count`-opted connections — the nested-`totalCount`-no-extra-COUNT pin therefore rides `allLibraryBooks { genresConnection(first: N) { totalCount edges { node } } }` (target `GenreType`, `total_count` on), the forward-M2M shape the shipped `test_book_genres_connection_sidecars_and_total_count` already established; the `booksConnection` shape carries the fixed-query-count and visibility pins (its `BookType.get_queryset` `circulation_status="repair"` filter is the visibility surface). Slice 5 stays **test-only — no library-schema source change** (no `Meta.connection` added to `BookType`).
  - [x] Per the [`test_query/README.md`][test-query-readme] coverage rule, the live suite is the primary home; the package mirrors in [`tests/test_relay_connection.py`][test-relay-connection] cover the shapes the fakeshop graph lacks (reverse-FK relation connections, the narrowed `"connection"` shape, divergent-alias fallback).

### Static inspection helper

**Skipped — recorded reason (per BUILD.md "may skip the helper ... The skip must be recorded explicitly with a short reason").** Slice 5 is **test-only**: it touches no `.py` source under `django_strawberry_framework/` and adds no `.py` source logic anywhere — it extends one existing live-HTTP test file (`examples/fakeshop/test_query/test_library_api.py`) with three `@pytest.mark.django_db` functions built from established helpers (`CaptureQueriesContext`, `_post_graphql`, `_post_graphql_as_staff`, `_seed_shelf`). The helper's value (import-direction / Django-ORM-marker / control-flow-hotspot mapping) targets package source and review-worthy logic; the test file carries no such logic for this slice (linear seed → POST → assert bodies). BUILD.md's "must run" triggers are all package-source-scoped and none apply to a test-only example-tree extension. If the build later surfaces non-trivial test-helper logic, Worker 3's review-pass helper-run policy still applies.

---

## Build report (Worker 2)

### Files touched

- `examples/fakeshop/test_query/test_library_api.py` — removed the `TODO(spec-033 Slice 5)` anchor block (14 lines) and replaced it with a Slice-5 section comment, one local seed helper (`_seed_genre_with_books`), one shared module-level query constant (`_NESTED_BOOKS_CONNECTION_QUERY`), and the three named live tests. No other region of the file changed; the two shipped behavior pins (`test_genre_books_connection_behavior`, `test_book_genres_connection_sidecars_and_total_count`) are untouched (`git diff` shows zero `-`/`+` lines in their bodies; the only deletions are the TODO anchor). No source under `django_strawberry_framework/` touched; no library schema/models touched.

### Tests added or updated

- `examples/fakeshop/test_query/test_library_api.py::test_nested_books_connection_fixed_query_count` — the per-parent-independence pin. Seeds 3 genres (each with 3 own books via M2M) in one run and 10 genres in a second run over the SAME shared query string (`_NESTED_BOOKS_CONNECTION_QUERY`, `allLibraryGenresConnection { edges { node { booksConnection(first: 2) { edges { node { title } } pageInfo { hasNextPage } } } } }`, anonymous client), wraps each in `CaptureQueriesContext(connection)`. **Load-bearing assertion: `three_count == ten_count` (the N+1 disproof).** **Measured query counts: 3-genre run = 2 queries, 10-genre run = 2 queries** — equal, and the absolute fixed N = **2** (one root genres-connection query + one windowed `booksConnection` prefetch query), pinned as a secondary `assert three_count == 2` derived empirically (my initial guess of 3 was wrong; corrected to the measured 2). Wire pin: each genre's `booksConnection.edges` returns its OWN 2-book page (`Book-{i}-a`, `Book-{i}-b`) with `hasNextPage True`.
- `examples/fakeshop/test_query/test_library_api.py::test_nested_total_count_no_per_parent_count` — the nested-`totalCount`-no-extra-query pin. Seeds 3 books, each with the same 4 genres, then runs two queries (`allLibraryBooks { genresConnection(first: 2) { [totalCount] edges { node { name } } } }`) differing only in the `totalCount` selection, each under its own `CaptureQueriesContext`. **Assertion: `len(with_captured) == len(without_captured)`. Measured: both = 2 queries** (one root `allLibraryBooks` query + one windowed `genresConnection` prefetch query); selecting nested `totalCount` adds ZERO. Value pin: `totalCount == 4` for every one of the 3 parent books (distinct from page size 2), proving the count rides the `_dst_total_count` window annotation, not a per-book `COUNT`.
- `examples/fakeshop/test_query/test_library_api.py::test_nested_window_respects_book_visibility` — the post-visibility window pin. Seeds one genre with 3 visible books + 1 `circulation_status=REPAIR` book, all on the M2M. Anonymous (`_post_graphql`) nested `booksConnection.edges` = `[Aurora, Binti, Circe]` (repair excluded); staff (`_post_graphql_as_staff`) = `[Aurora, Binti, Circe, Withdrawn]` (repair included). Pins that `BookType.get_queryset` runs INSIDE the windowed nested connection (post-visibility row numbering, spec Edge case line 448). The "nested `totalCount`" half is proven through the visible-edge set (the post-visibility window row count IS the visible count) because `BookType` exposes no `totalCount` field; the test docstring states this explicitly and notes the genuine visibility-filtered-`totalCount` field is unavailable live (`GenreType` has `total_count` but no visibility filter).
- **Two shipped behavior pins re-confirmed green UNMODIFIED:** `test_genre_books_connection_behavior` and `test_book_genres_connection_sidecars_and_total_count` both pass in the focused run; the diff does not modify either.

### Validation run

- `uv run ruff format .` — pass (reformatted `test_library_api.py` once on the first invocation; idempotent on the second).
- `uv run ruff check --fix .` — pass (`All checks passed!`). The pre-existing `COM812`-vs-formatter warning is the standing repo config warning, not a Slice-5 issue.
- `git status --short` after both ruff invocations — `examples/fakeshop/test_query/test_library_api.py` is my only slice-intended source/test change (appears in Files touched). The other 7 `M` package files (`connection.py`, `optimizer/extension.py`, `optimizer/plans.py`, `optimizer/walker.py`, `types/definition.py`, `types/finalizer.py`, `types/resolvers.py`), the 4 `M` package-test files (`tests/optimizer/test_extension.py`, `test_plans.py`, `test_walker.py`, `tests/test_relay_connection.py`), and `M docs/spec-033-connection_optimizer-0_0_9.md` are the accepted (uncommitted) Slice-1/2/3/4 changes — **NOT reverted** (per the dispatch contract: revert tool churn, never revert accepted prior slices). No unrelated tool churn was introduced by my pass; ruff touched only my test file.
- Focused live-test run (no `--cov*`): `uv run pytest examples/fakeshop/test_query/test_library_api.py --no-cov -k "<5 tests>"` → **5 passed, 73 deselected**. The three new tests pass; the two behavior pins pass unmodified.

### Implementation notes

- **3-genre vs 10-genre as two seed-and-capture passes inside ONE test body** (an `_run(genre_count)` closure), not two `@pytest.mark.django_db` functions or a parametrize. This keeps the query string single-sited (`_NESTED_BOOKS_CONNECTION_QUERY` module constant) and the equality assertion (`three_count == ten_count`) co-located with both captures — the cleanest expression of the contract per the discretion item. Between the two passes the graph is reset via `Book/Genre/Shelf/Branch.objects.all().delete()` so the 10-genre count is not contaminated by the 3-genre rows.
- **`_NESTED_BOOKS_CONNECTION_QUERY` is a module-level constant, not a per-test closure.** The DRY pin is only that the two parent-count runs share ONE query string; a module constant reads cleaner than a closure and is the single source for the shape. (Per-test seed helper `_seed_genre_with_books` stays a module function for the same reason — used only by the fixed-count test but expresses the per-genre-own-books invariant once.)
- **Per-genre UNIQUE book titles** (`Book-{index}-a/b/c`) — `Book` has a `UniqueConstraint(shelf, title)` and the fixtures share one `_seed_shelf()` shelf, so reusing titles across genres would violate the constraint. Unique-per-genre titles also make the per-parent window wire assertion unambiguous (genre `i` returns exactly `Book-{i}-a`, `Book-{i}-b`).
- **`_seed_genre_with_books` attaches books to the genre via the M2M, not the FK.** The `booksConnection` window is the reverse-M2M relation `Genre.books`; the books also need a `shelf` (non-null FK) which the shared `_seed_shelf()` supplies. Books carry the default `AVAILABLE` status (no visibility filter interference in the fixed-count test).
- **`test_nested_total_count` uses 3 parent books, each with the same 4 genres** (discretion item: multiple books preferred). A per-book `COUNT` would scale with book count; the equal-query-count assertion plus the per-book `totalCount == 4` value assertion together prove the count is window-annotation-derived, not per-parent.
- **Anonymous client for the fixed-count and total-count tests; both anonymous + staff for the visibility test.** `GenreType` has no `get_queryset` filter so anonymous sees all genres; `BookType.get_queryset` is the only visibility surface, exercised by the dedicated visibility test reusing the exact `_post_graphql` / `_post_graphql_as_staff` pair `test_node_hidden_row_null_live` uses.
- **No `global_id_for` / in-body type import needed** — none of the three tests mint a GlobalID, so the file-header reload invariant (no module-level `apps.library.schema` class imports) is honored without any in-test-body import.

### Notes for Worker 3

- **Static helper skipped** — recorded reason above (test-only example-tree extension, no package source touched, no review-worthy logic). No shadow file used.
- **Empirical query counts** to verify if you want the exact-N pin re-derived: I confirmed the absolute counts by temporarily injecting a `print(len(without_captured), len(with_captured))` into the total-count test and running with `-s` (output: `without=2 with=2`), then **fully reverted the injection** (`grep` for `SLICE5_TC_COUNTS` returns clean). The fixed-count test's `assert three_count == 2` is likewise the measured value, not a guess. No temp test files were left under `docs/builder/temp-tests/`.
- **Behavior-pin parity** — `git diff examples/fakeshop/test_query/test_library_api.py | grep '^-'` shows the only deletions are the 14-line TODO anchor; the two behavior-pin bodies are byte-unchanged. The new `test_nested_total_count_no_per_parent_count` re-asserts the same `totalCount` value contract as `test_book_genres_connection_sidecars_and_total_count` without rewriting it (SQL-shape sibling, not a replacement).
- **`len(captured)` on a `CaptureQueriesContext`** is the file's established idiom (`:262`, `:298`, etc.); I use `len(captured)` directly, consistent with the surrounding tests, not `len(captured.captured_queries)`.

### Notes for Worker 1 (spec reconciliation)

- **None.** No source defect surfaced; all three pins passed against the live optimizer-rooted schema with the spec-reconciled `totalCount` siting (the `booksConnection`/`genresConnection` split from the Plan). The spec-line-79 reconciliation Worker 1 already recorded held up end-to-end: `booksConnection` carries the fixed-count + visibility pins (no `totalCount` selected), `genresConnection` carries the no-extra-COUNT pin. No `Meta.connection` was added to `BookType`; no library-schema source change.
- **Empirical fixed N = 2** (not 3, my plan-time-irrelevant initial guess): one root genres-connection query + one windowed `booksConnection` prefetch query. The equality-across-parent-counts pin (the required contract) and the secondary exact-N pin both hold at N=2.

---

## Review (Worker 3)

Scope: `examples/fakeshop/test_query/test_library_api.py` only (`git diff -- examples/fakeshop/test_query/test_library_api.py`). The other 7 `M` package files, 4 `M` package-test files, and `M docs/spec-033-…md` are accepted Slice-1/2/3/4 baseline — not re-reviewed (cumulative-diff filter via `### Files touched`). Slice 5 is test-only; static helper correctly skipped (recorded reason in Plan; no package source, no review-worthy logic).

### High:

None.

### Medium:

#### `test_nested_window_respects_book_visibility` proves visibility on the FALLBACK path, not the window — the spec's "post-visibility window" deliverable stays unpinned

Severity: Medium. Source: `examples/fakeshop/test_query/test_library_api.py::test_nested_window_respects_book_visibility` (the `query` string #"booksConnection(orderBy: [{ title: ASC }])").

The test passes an `orderBy:` sidecar argument to `booksConnection`. Per Decision 6 / Non-goals / the Slice-1 plan, **a nested connection carrying `filter:` / `orderBy:` input is left UNPLANNED and falls back per-parent** — no window prefetch is emitted. So this test exercises the per-parent fallback pipeline, NOT the windowed nested connection. I verified this empirically (temp probe, both shapes, two cardinalities):

```text
PLAIN   booksConnection (no sidecar):  3-genre = 2 queries, 10-genre = 2 queries   (flat -> windowed)
ORDERBY booksConnection(orderBy: ...): 3-genre = 5 queries, 10-genre = 12 queries  (~2 + parent_count -> per-parent fallback)
```

Why it matters: DoD item 8 (line 615) names the **visibility-filtered window** as a distinct property, and Edge case line 448 is explicit — "row numbers and `_dst_total_count` are computed **post-visibility**" — i.e. the deliverable is that `BookType.get_queryset` runs *inside the window*. The test's own docstring claims exactly that ("the target `BookType.get_queryset` runs INSIDE the nested windowed `booksConnection` (post-visibility row numbering)"), but with `orderBy:` present that path never executes. The visibility behavior the test asserts is real, but it is the same fallback-path visibility the UNMODIFIED `test_genre_books_connection_behavior` already covers (that pin also uses `orderBy: [{ title: ASC }]` and already asserts the anonymous repair-book exclusion). The new test therefore adds no coverage of the windowed-visibility branch — the one thing Slice 5 was meant to pin.

This is a spec-contract test pointed at the wrong code path, not a shipped bug (the visibility filtering itself is correct on both paths). No source change is wrong; the test is.

Recommended change: drop the `orderBy: [{ title: ASC }]` argument so the window plans. The window appends the deterministic pk-terminal order (Decision 4 / `_finalize_queryset`), so the books come back in seeded insertion order with no `orderBy` needed — I confirmed the no-sidecar query returns identical wire results: anonymous `["Aurora", "Binti", "Circe"]`, staff `["Aurora", "Binti", "Circe", "Withdrawn"]`. Optionally wrap the anonymous run (with ≥2 genres each carrying a repair book) in `CaptureQueriesContext` and assert a parent-independent flat count, so the test actively pins that visibility rides the window (post-visibility row numbering) rather than the fallback. Update the docstring's "INSIDE the nested windowed `booksConnection`" claim to be true. (The "no `totalCount` field on `BookType`" half of the docstring is correct and stays.)

Test expectation after fix: the no-`orderBy` `allLibraryGenresConnection { edges { node { booksConnection { edges { node { title } } } } } }` query (a) returns anonymous-excluded / staff-included repair rows in deterministic pk order, and (b) executes in a flat, parent-count-independent query count (window planned).

### Low:

None.

### DRY findings

- No duplication worth flagging. `_NESTED_BOOKS_CONNECTION_QUERY` is a single module-level constant shared across both parent-count runs of the fixed-count test (the only real re-spell risk, correctly factored). `_seed_genre_with_books` expresses the per-genre-own-books invariant once. The query-count idiom (`CaptureQueriesContext(connection)` + `len(captured)`), the `_post_graphql` / `_post_graphql_as_staff` pair, and `_seed_shelf()` are all the file's established helpers, reused verbatim — no new posting/seeding helper introduced, consistent with the file's convention. The three tests' seedings are legitimately distinct cardinalities (3-vs-10 parents / multi-book-N-genre / visible+repair), not copy-paste; a single shared fixture would not fit all three. The visibility test's seeding mirrors `test_genre_books_connection_behavior` but is a legitimate per-test fixture for a different surface, not extractable duplication.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` is empty — the file is not in the diff. No `__all__` or re-export change. Slice 5 is test-only and touches no package source, consistent with DoD "no new public exports" and the spec's "adds no public symbol".

### CHANGELOG sanity

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

Not applicable; slice did not modify docs/KANBAN/archive/release-metadata surfaces (the only changed file is the live test `test_library_api.py`).

### What looks solid

- **Per-parent independence IS genuinely asserted** in `test_nested_books_connection_fixed_query_count`: both 3-genre and 10-genre cardinalities are really seeded (each genre with its own 3 books via M2M, unique titles to satisfy the `(shelf, title)` constraint), the SAME shared query string runs under two captures, and the load-bearing assertion is `three_count == ten_count` (not merely an absolute-N pin). The secondary `three_count == 2` exact-N pin is empirically correct (I re-derived it: 1 root genres-connection query + 1 windowed `booksConnection` prefetch). The per-genre wire assertion (`Book-{i}-a`/`Book-{i}-b` with `hasNextPage True`) proves the window is per-parent-correct, not a shared slice. I confirmed the harness genuinely detects per-parent scaling via the ORDERBY probe above (5 vs 12), so the equality pin is not vacuous.
- **The totalCount-no-extra-query pin is real and correctly sited.** `test_nested_total_count_no_per_parent_count` rides `genresConnection` (target `GenreType`, which DOES declare `Meta.connection = {"total_count": True}`), NOT `booksConnection` — correct per the line-79 reconciliation. It compares the same selection with vs without nested `totalCount` and asserts equal query count, AND asserts `totalCount == 4` (≠ page size `first: 2`) for every one of 3 parent books. I verified the count is window-annotation-derived (`_dst_total_count`), not a per-book COUNT: with/without both stay flat at 2 queries across 3-book and 7-book seedings, and the value stays `4` regardless — a per-parent COUNT would have scaled.
- **The two spec-032 behavior pins are byte-unmodified.** `git diff | grep '^-'` shows the only deletions are the 14-line TODO anchor block; the `test_genre_books_connection_behavior` and `test_book_genres_connection_sidecars_and_total_count` bodies have zero `-`/`+` lines (the only lines mentioning their names are the new comment block + one docstring reference). Both pass green in the full-file run.
- **Full file green, format clean.** `uv run pytest examples/fakeshop/test_query/test_library_api.py --no-cov` → 78 passed. `uv run ruff format --check` → already formatted (the `COM812` warning is the standing repo config warning, not a Slice-5 issue). No `--cov*` flags used.
- **No source touched, schema unchanged.** No `Meta.connection` added to `BookType`; the test-only contract held.

### Temp test verification

- `docs/builder/temp-tests/slice-5/test_visibility_query_shape_probe.py` — proved the `orderBy:` visibility query scales per-parent (5 vs 12) while the plain query stays flat (2 vs 2). Diagnostic; basis for the Medium finding.
- `docs/builder/temp-tests/slice-5/test_visibility_window_path_probe.py` — proved the no-`orderBy` visibility query is window-planned (flat across 3 vs 10 parents) AND still hides repair rows for anonymous; basis for the recommended fix. (First version of this file mis-measured 0 queries due to a connection-alias artifact when capturing across the imported `connection` object outside the file's own harness; the rewritten multi-genre version measured correctly.)
- `docs/builder/temp-tests/slice-5/test_total_count_probe.py` — proved the `genresConnection` `totalCount` is window-derived (with==without==2 queries, flat across 3 vs 7 parent books, value stays 4).
- Disposition: all three are diagnostic probes, kept under `docs/builder/temp-tests/slice-5/` (gitignored), not promoted. The Medium finding records the behavior the visibility-test fix should pin; the window-path probe's assertions can guide Worker 2's rewrite. No probe caught a SHIPPED bug requiring promotion (the visibility filtering is correct on both paths) — the finding is a test-targets-wrong-path coverage gap, fixed in the test itself.

### Notes for Worker 1 (spec reconciliation)

- No spec edit needed. The Medium finding is a test-fidelity gap against the already-reconciled spec (Edge case line 448 + DoD item 8), not a spec ambiguity. If Worker 2 fixes the test as recommended, the spec stands as written. If for some reason the `orderBy:` must stay (it should not — determinism is free from the window's pk-terminal order), that would be a spec-contract miss Worker 1 must weigh, because the windowed-visibility property would then be unpinned anywhere in the live suite.

### Review outcome

`revision-needed`. One Medium finding: `test_nested_window_respects_book_visibility` exercises the per-parent fallback (via `orderBy:`) instead of the windowed nested connection, leaving the spec's post-visibility-window deliverable (DoD item 8 / Edge case line 448) unpinned. Clean one-line fix (drop `orderBy:`; optionally add a flat-query-count capture). The per-parent-independence pin and the totalCount pin are both genuine and solid; the two behavior pins are unmodified and green.

---

## Build report (Worker 2, pass 2)

Re-pass resolving Worker 3's single Medium finding: `test_nested_window_respects_book_visibility` carried an `orderBy:` sidecar, which (per Decision 6) leaves the nested connection UNPLANNED and falls back per-parent — so the test exercised the fallback pipeline, not the windowed nested connection, leaving the windowed-visibility property (DoD item 8 / Edge case line 448) unpinned. Worker 3's recommendation verified empirically and applied: drop `orderBy:` so the selection is window-planned, and add a flat query-count capture that actively pins window-vs-fallback.

### Files touched

- `examples/fakeshop/test_query/test_library_api.py` — rewrote ONLY `test_nested_window_respects_book_visibility`. Three changes: (1) dropped the `orderBy: [{ title: ASC }]` argument from the nested `booksConnection` selection so the connection is window-planned; (2) seeded **2 genres**, each carrying 3 visible books + 1 repair book on the M2M (was 1 genre), and wrapped the anonymous run in `CaptureQueriesContext(connection)` with a load-bearing `assert len(captured) == 2` flat-count pin — the active window-vs-fallback guard; (3) rewrote the docstring to accurately describe the windowed-visibility pin and the deterministic pk-terminal order the window appends. The two shipped behavior pins (`test_genre_books_connection_behavior`, `test_book_genres_connection_sidecars_and_total_count`) and the other two new tests (`test_nested_books_connection_fixed_query_count`, `test_nested_total_count_no_per_parent_count`) are untouched by this pass. No source under `django_strawberry_framework/` touched; no library schema/models touched.

### Tests added or updated

- `examples/fakeshop/test_query/test_library_api.py::test_nested_window_respects_book_visibility` — **strengthened, not added.** Now pins the WINDOWED-visibility branch (the fix to the Medium):
  - **GraphQL shape**: `allLibraryGenresConnection { edges { node { booksConnection { edges { node { title } } } } } }` — no `orderBy:` sidecar, so the selection is window-planned (verified below).
  - **Fixture**: 2 genres, each with visible books (`Aurora-{i}`, `Binti-{i}`, `Circe-{i}`) + 1 repair book (`Withdrawn-{i}`, `circulation_status=REPAIR`) via the M2M; per-genre unique titles satisfy the `Book(shelf, title)` constraint under the shared `_seed_shelf()`.
  - **Window-vs-fallback pin (the Medium resolution)**: anonymous run wrapped in `CaptureQueriesContext(connection)`; `assert len(captured) == 2` — flat, parent-count-independent (1 root genres-connection query + 1 windowed `booksConnection` prefetch). **Measured: 2 genres = 2 queries; re-derived independently as 2 vs 6 genres both = 2 via a temp probe** (deleted, see Notes for Worker 3). This assertion FAILS if the selection ever silently falls back per-parent.
  - **Post-visibility wire pin**: anonymous nested pages = `[["Aurora-0","Binti-0","Circe-0"], ["Aurora-1","Binti-1","Circe-1"]]` (repair excluded per genre); staff = the same plus `"Withdrawn-{i}"` appended (visibility bypass). **Measured ordering confirmed from a real run**: the window's deterministic pk-terminal order yields seeded insertion order for free — anonymous `["Aurora","Binti","Circe"]`, staff adds `"Withdrawn"` (Worker 3's predicted lists, confirmed per-genre).
- **Revert-and-fail proof** (per worker-2.md "Pre-existing claim verification" discipline applied to the new pin): temporarily re-injected `orderBy: [{ title: ASC }]` into the visibility test's query (forces the Decision-6 fallback), ran the test → `assert len(captured) == 2` failed with `assert 4 == 2` (2 parents → ~1 query/parent + root). Fully restored from a `/tmp` backup; confirmed green again afterward. This proves the flat-count assertion is non-vacuous and the "runs inside the window" claim is now genuinely enforced.
- **Two shipped behavior pins re-confirmed green UNMODIFIED**, and the other two new tests re-confirmed green unmodified, in the focused run below.

### Validation run

- `uv run ruff format .` — pass (`251 files left unchanged`; my edit was already well-formatted, idempotent). The `COM812`-vs-formatter line is the standing repo config warning, not a Slice-5 issue.
- `uv run ruff check --fix .` — pass (`All checks passed!`).
- `git status --short` after both ruff invocations — `examples/fakeshop/test_query/test_library_api.py` is my only slice-intended source/test change (appears in Files touched). The 7 other `M` package source files (`connection.py`, `optimizer/extension.py`, `optimizer/plans.py`, `optimizer/walker.py`, `types/definition.py`, `types/finalizer.py`, `types/resolvers.py`), the 4 `M` package-test files (`tests/optimizer/test_extension.py`, `test_plans.py`, `test_walker.py`, `tests/test_relay_connection.py`), and `M docs/spec-033-connection_optimizer-0_0_9.md` are the accepted (uncommitted) Slice-1/2/3/4 baseline — **NOT reverted** (dispatch contract: revert tool churn, never revert accepted prior slices). The `??` `docs/builder/build-033-*.md` + `bld-slice-*.md` files are build-cycle artifacts. No unrelated tool churn was introduced by this pass (ruff left every file unchanged).
- Focused live-test run (no `--cov*`): `uv run pytest examples/fakeshop/test_query/test_library_api.py --no-cov -k "<3 new + 2 behavior pins>"` → **5 passed, 73 deselected**. After restoring the revert-and-fail injection: `test_nested_window_respects_book_visibility` → **1 passed, 77 deselected**.

### Implementation notes

- **2 genres (was 1) for the visibility test.** A single parent cannot distinguish window from fallback by query count (both cost ~2). With ≥2 parents each carrying a repair book, the fallback would emit ~1 query per parent while the window stays flat at 2 — this is what makes the `assert len(captured) == 2` an active window-vs-fallback guard rather than decoration. I kept it at 2 (the minimum that discriminates) plus an independent 2-vs-6 probe to confirm the flatness scales.
- **Flat-count pin uses `assert len(captured) == 2`, not an equality-across-two-cardinalities shape.** The fixed-count sibling test (`test_nested_books_connection_fixed_query_count`) already uses the 3-vs-10 equality shape; here a single absolute `== 2` reads cleaner inside the visibility test (one anonymous capture, no second seed-reset pass needed) and is just as discriminating because the fixture has 2 parents — a per-parent fallback gives 4, caught by `== 2`. The revert-and-fail proof confirms it.
- **Per-genre unique titles (`Aurora-{i}` / `Withdrawn-{i}`)** for the same `Book(shelf, title)` UniqueConstraint reason as the other Slice-5 tests; the shared `_seed_shelf()` shelf is reused, so titles must differ across genres.
- **No `orderBy:` needed for determinism.** The window appends the pk-terminal deterministic order (Decision 4 / `_finalize_queryset`), so books arrive in seeded insertion order without any client `orderBy:` — verified from the real run (anonymous `Aurora,Binti,Circe`; staff appends `Withdrawn`). Dropping `orderBy:` is therefore free: it both fixes the path and keeps the wire assertion deterministic.
- **`_nested_titles_by_genre` local helper** replaces the prior single-genre `_nested_titles` closure — it maps over all parent edges (now 2) returning a list-of-lists, keeping the anonymous/staff assertions symmetric. Local to the test (used twice within it), not a module helper.

### Notes for Worker 3

- **Medium resolved at the root, not patched.** The finding was a spec-contract test pointed at the wrong code path (per-parent fallback via `orderBy:`), leaving the windowed-visibility deliverable unpinned. The fix removes the `orderBy:` so the selection is genuinely window-planned, and adds the `assert len(captured) == 2` flat-count pin so the windowed path is actively enforced — a silent fallback now fails the test. The visibility filtering behavior asserted is unchanged; what changed is that it is now asserted ON THE WINDOW (DoD item 8 / Edge case line 448), which is the property Slice 5 was meant to pin.
- **Empirical re-derivation, temp probe deleted.** I re-derived the ordering and flat counts with a temporary `examples/fakeshop/test_query/test_slice5_probe.py` (single-genre ordering: anonymous `["Aurora","Binti","Circe"]`, staff adds `"Withdrawn"`; multi-genre flat count: 2 genres = 2 queries, 6 genres = 2 queries, repair hidden for anonymous in every genre). The probe is **fully deleted** (`git status` shows no `test_slice5_probe.py`); it left nothing under `docs/builder/temp-tests/`. The revert-and-fail proof (re-inject `orderBy:` → `assert 4 == 2`) is also fully reverted.
- **Behavior-pin + sibling-test parity** — `git diff -- examples/fakeshop/test_query/test_library_api.py` against HEAD shows the cumulative Slice-5 change (this is an uncommitted build); the only `-`/`+` lines touching `test_genre_books_connection_behavior`, `test_book_genres_connection_sidecars_and_total_count`, `test_nested_books_connection_fixed_query_count`, or `test_nested_total_count_no_per_parent_count` are the unchanged section-comment/docstring references — zero changes inside those four function bodies. My pass-2 delta is confined to `test_nested_window_respects_book_visibility`.

### Notes for Worker 1 (spec reconciliation)

- **None.** No source defect surfaced; the fix is test-only and confined to one test function. The spec-line-79 reconciliation Worker 1 already recorded holds: `booksConnection` (target `BookType`, `get_queryset` `circulation_status="repair"` filter, no `total_count`) carries the visibility pin, now genuinely on the windowed path. Edge case line 448 ("row numbers and `_dst_total_count` are computed post-visibility ... pins this through `BookType`'s `circulation_status="repair"` filter") is now actively pinned in the live suite. No `Meta.connection` added to `BookType`; no library-schema source change.

---

## Review (Worker 3, pass 2)

Re-review of Worker 2's pass-2 fix for the single pass-1 Medium. Scope: `git diff -- examples/fakeshop/test_query/test_library_api.py`. The 7 `M` package source files, 4 `M` package-test files, and `M docs/spec-033-…md` are the accepted Slice-1/2/3/4 baseline — not re-reviewed (cumulative-diff filter via `### Files touched`). The pass-2 delta is confined to `test_nested_window_respects_book_visibility` (verified below). Slice 5 remains test-only; static helper correctly skipped (recorded reason in Plan).

### Pass-1 Medium — CONFIRMED FIXED

Pass-1 Medium: `test_nested_window_respects_book_visibility` carried an `orderBy:` sidecar, which (Decision 6) leaves the nested connection UNPLANNED → per-parent fallback, so it pinned the fallback path's visibility, not the windowed-visibility deliverable (DoD item 8 / Edge case line 448). 

The fix is applied at the root, exactly as recommended:

1. **`orderBy:` dropped** — the visibility query is now plain `allLibraryGenresConnection { edges { node { booksConnection { edges { node { title } } } } } }` (the test-body `query` string carries no sidecar; the only `orderBy` text in the function is docstring/comment prose at the source explaining why it is omitted). The plain selection is window-planned.
2. **Active window-vs-fallback guard added** — fixture seeds 2 genres, each with 3 visible books + 1 repair book on the M2M; the anonymous run is wrapped in `CaptureQueriesContext(connection)` with `assert len(captured) == 2` (flat = 1 root genres-connection query + 1 windowed `booksConnection` prefetch). A per-parent fallback would emit ~1 query/parent, failing this pin.

I verified the discrimination **independently**, not by trusting Worker 2's revert claim. Temp probe `docs/builder/temp-tests/slice-5/test_pass2_window_vs_fallback.py` + a measured count print over two cardinalities:

```text
PLAIN   booksConnection (window):   2-genre = 2 queries, 6-genre = 2 queries   (flat → windowed)
ORDERBY booksConnection (fallback): 2-genre = 4 queries, 6-genre = 8 queries   (~2/parent → per-parent fallback)
```

This reproduces Worker 2's revert-and-fail claim exactly: re-injecting `orderBy:` yields 4 queries at 2 parents, so `assert len(captured) == 2` fails with `assert 4 == 2`. The pin is **non-vacuous** and genuinely enforces the windowed path. Both shapes still hide the repair book from anonymous (the probe asserts this), confirming the wire assertion alone cannot distinguish window from fallback — only the query count can, which is precisely why the flat-count pin is load-bearing.

**Visibility property pinned on the WINDOWED path** (verified — the isolated test passes, full file passes):
- anonymous `booksConnection.edges` per genre = `[["Aurora-0","Binti-0","Circe-0"],["Aurora-1","Binti-1","Circe-1"]]` — repair `Withdrawn-{i}` excluded;
- staff = the same plus `"Withdrawn-{i}"` appended per genre — repair included;
- titles arrive in seeded insertion order with no `orderBy:` (the window's pk-terminal deterministic order, Decision 4). The repair book appears LAST for staff because it was seeded last — confirming the pk-terminal order holds. This is `BookType.get_queryset` running INSIDE the window, post-visibility row numbering (Edge case line 448, DoD item 8).

### High:

None.

### Medium:

None. The single pass-1 Medium is confirmed-fixed (above). No new Medium surfaced.

### Low:

None.

### No-regression to the rest

- **The two spec-032 behavior pins are byte-unmodified.** `git diff … | grep '^[-+].*def test_genre_books_connection_behavior|…sidecars_and_total_count'` → NONE; both exist at HEAD (lines 2719, 2773) and appear in zero diff hunks. Both pass green in the full-file run.
- **The two other new tests are byte-unmodified from pass 1.** `test_nested_books_connection_fixed_query_count` still asserts `three_count == ten_count` + `three_count == 2` over the per-genre `Book-{index}-a/b` wire; `test_nested_total_count_no_per_parent_count` still seeds 3 books × 4 genres (Alpha/Beta/Gamma/Echo; Kindred/Dawn/Wild Seed), asserts `len(with_captured) == len(without_captured)` and `totalCount == 4`. These match the pass-1-accepted descriptions exactly — pass 2 did not touch them. All three new tests are pure additions (none exist at HEAD).
- **No source/spec/schema edit.** Diff touches only the one test file; no `django_strawberry_framework/` source, no library schema/models, no `Meta.connection` on `BookType`.

### DRY findings

None new. The pass-2 delta reuses the file's established helpers verbatim (`CaptureQueriesContext(connection)` + `len(captured)`, `_post_graphql` / `_post_graphql_as_staff`, `_seed_shelf()`). The new `_seed_genres` and `_nested_titles_by_genre` are local to the visibility test (each used twice within it), not extractable module helpers — correct scoping. Per-genre unique titles (`Aurora-{i}` / `Withdrawn-{i}`) are the same `(shelf, title)` UniqueConstraint accommodation the sibling tests use.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` is empty — not in the diff. No `__all__` / re-export change. Consistent with DoD "no new public exports"; Slice 5 is test-only.

### CHANGELOG sanity

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

Not applicable; the only changed file is the live test `test_library_api.py`.

### What looks solid

- The Medium fix is a **root fix, not a patch**: the path the test exercises actually changed (fallback → window), and a new active guard (`assert len(captured) == 2`) enforces it — independently confirmed discriminating (2 vs 4 at 2 parents; 2 vs 8 at 6 parents).
- Determinism is genuinely free from the window's pk-terminal order; dropping `orderBy:` both fixes the path and keeps the wire assertion deterministic.
- The whole Slice-5 contribution (DoD item 8: fixed query count + nested-`totalCount` zero-extra-queries + visibility-filtered window) is now pinned on the windowed path; the shipped behavior pins stay unmodified and green.

### Temp test verification

- `docs/builder/temp-tests/slice-5/test_pass2_window_vs_fallback.py` (NEW, pass 2) — independently proves the `assert len(captured) == 2` pin discriminates window (plain, flat 2/2) from fallback (orderBy, 4/8), and that both paths hide the repair row for anonymous (so only the count distinguishes them). Diagnostic; basis for confirming the Medium fix is non-vacuous.
- The three pass-1 probes (`test_visibility_query_shape_probe.py`, `test_visibility_window_path_probe.py`, `test_total_count_probe.py`) remain under `docs/builder/temp-tests/slice-5/` (gitignored), superseded by the shipped tests.
- Disposition: all diagnostic, none promoted — the shipped tests now carry the behavior the probes verified. No probe caught a shipped bug.

### Notes for Worker 1 (spec reconciliation)

- **None.** The spec-line-79 reconciliation (recorded in the Plan) holds end-to-end; Edge case line 448 is now actively pinned in the live suite. No spec edit needed.

### Review outcome

`review-accepted`. The single pass-1 Medium is confirmed-fixed: `test_nested_window_respects_book_visibility` now drops `orderBy:` (window-planned) and adds an independently-verified non-vacuous window-vs-fallback guard (`assert len(captured) == 2`; fallback would be 4). The visibility property is pinned on the windowed path (repair excluded anon / included staff, pk-terminal order). No regression — the two spec-032 behavior pins and the two other new tests are byte-unmodified; no source/spec/schema edit. Full file: `uv run pytest examples/fakeshop/test_query/test_library_api.py --no-cov` → 78 passed. Artifact `Status:` set to `review-accepted`.

## Final verification (Worker 1)

Status: final-accepted

Diff inspected: `git diff -- examples/fakeshop/test_query/test_library_api.py` (291 insertions, 14 deletions — the deletions are exactly the 14-line `TODO(spec-033 Slice 5)` anchor block; no other region of the file changed). No `django_strawberry_framework/` source touched; no library schema/models touched; no `Meta.connection` added to `BookType`. The other 7 `M` package source files, 4 `M` package-test files, and `M docs/spec-033-…md` are the accepted Slice-1/2/3/4 baseline (not re-reviewed here; cumulative-diff filter via Worker 2's `### Files touched`).

### 1. Spec slice checklist audit (Plan's `### Spec slice checklist (verbatim)`)

- **Box 1** (`test_library_api.py` SQL-shape pins) — `- [x]` **CONFIRMED**. All three DoD-item-8 properties landed in the diff, sited per the reconciled line-79 text:
  - fixed query count, parent-count-independent → `test_nested_books_connection_fixed_query_count` (`three_count == ten_count` load-bearing; `three_count == 2` secondary exact-N).
  - nested-`totalCount` zero-extra-queries → `test_nested_total_count_no_per_parent_count` (rides `genresConnection`, target `GenreType` `total_count` ON; `len(with) == len(without)`; `totalCount == 4` ≠ page size, across 3 parent books).
  - visibility-filtered **window** → `test_nested_window_respects_book_visibility` (no `orderBy:` so the selection is window-planned; `assert len(captured) == 2` flat-count active window-vs-fallback guard; anon excludes / staff includes the repair book in pk-terminal order). The pass-1 Medium (the test was on the per-parent fallback path via an `orderBy:` sidecar) was resolved at the root in Worker 2's pass 2 and independently re-confirmed by Worker 3's pass-2 probe (window flat 2/2; fallback 4/8). The box's contract genuinely landed on the windowed path.
- **Box 2** (`test_query/README.md` coverage rule — live suite primary home; package mirrors in `tests/test_relay_connection.py` cover the shapes the fakeshop graph lacks: reverse-FK relation connections, narrowed `"connection"` shape, divergent-alias fallback) — `- [x]` **CONFIRMED**, with one recorded scoping note (see `### Spec changes made` below): the live-suite half is delivered by this slice's diff; the package-mirror half (`tests/test_relay_connection.py`) is satisfied by the accepted Slice-1/2 baseline, not by Slice-5's own diff. Box 2 is a statement of *where* coverage lives, not a net-new Slice-5 source deliverable, so the tick is correct — the coverage it names exists and is green.
- No box was over-ticked (every `- [x]` has matching landed coverage); no box was left silently un-ticked; no `- [ ]` remains.

### 2. DRY check across Slices 1–5

- The three live tests reuse the suite's established helpers verbatim — `_seed_shelf()`, `_post_graphql` / `_post_graphql_as_staff`, the `CaptureQueriesContext(connection)` + `len(captured)` query-count idiom (the file convention, NOT `django_assert_num_queries`), and the `_reload_project_schema_for_acceptance_tests` autouse fixture inherited free. No new posting/seeding helper introduced.
- The single real re-spell risk (the two-level query string across the 3-genre and 10-genre runs) is correctly factored into one shared module constant `_NESTED_BOOKS_CONNECTION_QUERY`. `_seed_genre_with_books`, `_seed_genres`, and `_nested_titles_by_genre` are test-local (each used ≥twice within its owning test), correctly scoped — not extractable module helpers.
- The three seedings are legitimately distinct cardinalities (3-vs-10 parents / multi-book-N-genre / 2-genres-with-repair), not copy-paste; a single shared fixture would not fit all three.
- The two spec-032 behavior pins (`test_genre_books_connection_behavior`, `test_book_genres_connection_sidecars_and_total_count`) are **byte-unmodified** — `git diff | grep '^[-+]'` touches neither `def` signature nor body; both pass green. No new cross-slice duplication or inconsistent helper shape introduced.

### 3. Existing tests pass

- `uv run pytest examples/fakeshop/test_query/test_library_api.py --no-cov` → **78 passed** (10.16s). The three new tests pass; the two spec-032 behavior pins pass unmodified. No `--cov*` flag used.

### 4. Spec reconciliation

- **Line-79 reconciliation confirmed present and consistent with the implemented tests.** Spec line 79 (the `booksConnection` totalCount → `genresConnection` re-siting) — made during the Slice-5 PLANNING pass — is in place and reads as reconciled: it states the `totalCount` siting explicitly (`booksConnection`/`BookType` carries the fixed-query-count + visibility pins with no `totalCount`; the nested-`totalCount`-no-extra-COUNT pin rides `allLibraryBooks { genresConnection(first: N) { totalCount edges { node } } }`, target `GenreType`, `total_count` on) and reaffirms "test-only — no library-schema source change (no `Meta.connection` added to `BookType`)". The implemented test sites match this text exactly: `test_nested_total_count_no_per_parent_count` rides `genresConnection`; `test_nested_window_respects_book_visibility` + `test_nested_books_connection_fixed_query_count` ride `booksConnection` with no `totalCount` selected.
- **Status line (line 5) refreshed** to "Slices 1–5 … accepted; Slices 6–7 not yet started" (was "Slices 1–4 … accepted; Slices 5–7 not yet started") per `worker-1.md` "Spec status-line re-verification".
- `### Spec slice checklist` stays UNTICKED by design (contract record per spec lines 3 / 5) — not touched.

### 5. check_spec_glossary

- `uv run python scripts/check_spec_glossary.py --spec docs/spec-033-connection_optimizer-0_0_9.md` → `OK: 38 terms`, exit 0 (re-run after the status-line edit).

### Summary

Slice 5 ships **test-only** live `/graphql/` SQL-shape coverage in `examples/fakeshop/test_query/test_library_api.py` — three new tests pinning the three DoD-item-8 properties (parent-count-independent fixed query count, nested-`totalCount` zero-extra-queries, visibility-filtered windowed nested connection), proving the Slice-1/2 windowed nested-connection mechanism live over the fakeshop library graph. The two spec-032 behavior pins are byte-unmodified and green. No source, schema, or `Meta.connection` change. One review loop: Worker 3's pass-1 Medium (visibility test was on the per-parent fallback path via an `orderBy:` sidecar) was fixed at the root in pass 2 (drop `orderBy:` → window-planned; add `assert len(captured) == 2` flat-count guard) and independently re-confirmed. Full file 78 passed; glossary clean.

### Spec changes made (Worker 1 only)

- **`docs/spec-033-connection_optimizer-0_0_9.md` line 79 (Slice-5 sub-bullet)** — *recorded here, made during the Slice-5 PLANNING pass*: re-sited the nested-`totalCount` pin from `booksConnection` onto `genresConnection`. Reason: the original line-79 prose named `booksConnection { edges { node } totalCount }`, but `BookType` declares no `Meta.connection = {"total_count": True}` (only `GenreType` does, `examples/fakeshop/apps/library/schema.py` `GenreType.Meta`), so a `totalCount` field does not exist on `BookType` connections and that query would be a GraphQL validation error; DoD item 8 / the Test plan name three distinct properties, which only the line-79 prose had merged into one impossible shape. The edit states the `totalCount` siting explicitly and reaffirms "test-only — no `Meta.connection` added to `BookType`". The reconciliation triggered no Worker-2 re-spawn (it clarified the test contract, not the implementation contract) and is consistent with the landed tests (verified, item 4 above).
- **`docs/spec-033-connection_optimizer-0_0_9.md` line 5 (status line)** — refreshed "Slices 1–4 … accepted; Slices 5–7 not yet started" → "Slices 1–5 … accepted; Slices 6–7 not yet started". Reason: per `worker-1.md` "Spec status-line re-verification", the header must describe current build state; Slice 5 is now final-accepted. The `## Slice checklist` boxes stay unticked (contract record per spec lines 3 / 5).
- **Deferral note (no `- [ ]` remains; recorded for audit):** Box 2's package-mirror half (`tests/test_relay_connection.py` covering reverse-FK relation connections / narrowed `"connection"` shape / divergent-alias fallback) was delivered by the accepted Slice-1/2 baseline, not by Slice-5's diff. Box 2 is correctly `- [x]` because it asserts *where* the coverage lives (live suite primary; package mirrors for fakeshop-absent shapes) and that coverage exists and is green — no Slice-5 source deliverable was deferred.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->
[spec-032]: ../SPECS/spec-032-full_relay-0_0_9.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->
[test-relay-connection]: ../../tests/test_relay_connection.py

<!-- examples/ -->
[test-library]: ../../examples/fakeshop/test_query/test_library_api.py
[test-query-readme]: ../../examples/fakeshop/test_query/README.md

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
