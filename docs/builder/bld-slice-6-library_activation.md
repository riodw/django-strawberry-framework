# Build: Slice 6 — fakeshop library activation (Decision 12)

Spec reference: `docs/spec-032-full_relay-0_0_9.md` (lines 107-110 — Slice 6 checklist; lines 473-487 — Decision 12; lines 591-606 — Test plan Slice 6; lines 335-356 — Decision 5 error contracts; lines 314-333 — Decision 4 typed/mismatch contracts)
Status: final-accepted

## Plan (Worker 1)

Spec status-line re-verification: spec line 5 reads "Slices 1–5 implemented … Slices 6–7 not started" — accurate at planning time; no edit needed.

Static inspection: `uv run python scripts/review_inspect.py examples/fakeshop/apps/library/schema.py --output-dir docs/shadow` ran (377 source lines ≥ 150 — mandatory). Overview is clean: no control-flow hotspots, repeated literals only `3x "subtitle"` / `2x "is_staff"` (the `is_staff` pair is the duplication this plan's DRY hoist removes — see below). **Skip recorded:** `examples/fakeshop/test_query/test_library_api.py` (2,581 lines) — per-cycle live-test file, not package source; a shadow overview for it already exists from the Slice-4 cycle (`docs/shadow/examples__fakeshop__test_query__test_library_api.overview.md`) and the additions are flat test functions with no review-worthy control flow; Worker 3's own thresholds govern at review.

Staged TODO anchors owned by this slice (grep-verified; the slice removes ALL of its own, and ONLY its own):

- `examples/fakeshop/apps/library/schema.py:61-85` — the `BookType` promotion pseudocode block.
- `examples/fakeshop/apps/library/schema.py:336-342` — the root-field pseudocode block inside `Query`.
- `examples/fakeshop/test_query/test_library_api.py:2533-2581` — the live-test enumeration block.

NOT this slice's: the Slice-7 anchors in `CHANGELOG.md`, `docs/GLOSSARY.md`, `docs/TREE.md`, `docs/README.md`, `README.md`, `TODAY.md`, `GOAL.md`, `KANBAN.md`, and the spec itself — leave untouched.

Revision 6 claim **verified**: `grep -rn "repair"` across `examples/` and `tests/` finds no inline-created `Book` row with `circulation_status="repair"` anywhere (all creates use `AVAILABLE` / `CHECKED_OUT` or the model default `AVAILABLE`); the only hits are the model's `TextChoices` member, the migration, and the staged TODO comments. The hidden-row predicate therefore changes zero existing rows' visibility.

Revision 7 Q4 claim **verified**: `examples/fakeshop/apps/library/tests/test_schema.py` carries no book-id literals and pins field presence by **subset** (`{"title", "shelf", "genres"} <= {...}`) plus declaration order via `vars(library_schema)` — the promotion (new `id: GlobalID!`, new synthesized `genres_connection`) breaks neither assertion. **No edit needed**, exactly as spec line 110 records. The staff half reuses the existing `_post_graphql_as_staff` helper (`test_library_api.py:710-720`, `force_login` of an `is_staff=True` user) — already in place.

### Blast-radius audit of the `BookType` promotion (read before implementing)

Enumerated by reading the full live suite and grepping every consumer of `BookType` / book ids:

1. **No existing live assertion selects a book `id`.** Every `allLibraryBooks` / nested `books { … }` / `book { … }` selection in `test_library_api.py` selects `title` / `subtitle` / `circulationStatus` / relation fields only (grep-verified across all 30 book-query sites). The wrong-type-GlobalID tests at lines 945-967 / 1308-1344 mint `library.book`-label payloads as deliberately-wrong inputs to **genre** filters — still wrong after the promotion, unaffected. So the "existing book-id assertions" churn inside `test_library_api.py` is **zero existing tests**; the file's churn is the TODO-block removal plus the new tests.
2. **Real out-of-file churn the spec missed:** `examples/fakeshop/tests/test_inspect_django_type.py::test_inspect_by_registered_name` asserts `"Int!" in text` AND `"GlobalID!" not in text` for `BookType` (lines 78-81: "Non-Relay pk renders as a plain Int!"), and `::test_inspect_by_dotted_path` asserts `"Int!" in text` (line 105; `id` is BookType's only Int-rendered field, so this fails post-promotion too). Both must flip to the `GenreType`-style expectation already pinned by `::test_inspect_relay_node_pk_row` (`GlobalID!` + `relay.Node id`). This contradicts spec line 110's "Churn is confined to `test_query/test_library_api.py`" — recorded under `### Notes for Worker 1 (spec reconciliation)` below; the implementation updates the two tests regardless (the spec's *intent* — bounded churn, no `test_schema.py` edit — holds).
3. **`BookFilter.id` flips to GlobalID lookups** (`Meta.fields = {"id": ["exact", "in"], …}` at `apps/library/filters.py:94`; the filter layer renders GlobalID lookups when the bound type is Relay-shaped — the `GenreFilter` precedent pinned at `test_library_api.py:884`). Audited: **no test anywhere filters books by own `id`** (the `shelf: { id: … }` filters bind `ShelfFilter`/non-Relay `ShelfType`; the `genres: { id: … }` filters were already GlobalID). Input-shape churn with zero assertion impact.
4. **Query-count / SQL-shape tests survive.** Relations INTO `Book` are `Shelf.books` (reverse FK), `Genre.books` (reverse M2M), `Loan.book` (forward FK with an explicit `OptimizerHint.prefetch_related()`) — all already on the prefetch path, so the optimizer's downgrade-to-`Prefetch`-on-custom-`get_queryset` rule (`optimizer/walker.py:68-74`) changes no plan shape; the new `get_queryset` only threads an `exclude(...)` into the existing prefetch querysets (`walker.py:146-151`). The FK-id-elision gate (`walker.py:314`) is moot — no test selects `book { id }` alone. Counts pinned at `test_library_api.py:285` (2), `:324` (3), `:411` (2), `:1084` (3), `:1734` (3) all hold; Worker 2 verifies by running the focused suite.
5. **`test_multi_db.py`** (FAKESHOP_SHARDED-only, outside the default run per `AGENTS.md`) imports the freshly-reloaded `BookType` in-fixture and asserts `title` sets only — promotion-safe by reading; do NOT add it to the default validation run.
6. **`NullabilityOverrideBookType`** (secondary, non-Relay) is unaffected per Decision 12 — its `id` stays `Int!`; `test_inspect_reads_resolved_annotation_not_field_null` and the live nullability tests need no edit.
7. **Synthesis eligibility after promotion** (Decision 6): `GenreType.books` (reverse M2M, both ends Relay) → `booksConnection`; `BookType.genres` (forward M2M, target Relay, target declares `total_count`) → `genresConnection`; `BookType.loans` (reverse FK, target `LoanType` NOT Relay) → silently list-only under the implicit default; `BookType.shelf` (single-valued forward FK) → ineligible by cardinality; `ShelfType.books` → no synthesis (declaring type not Relay-shaped). No `relation_shapes` key is declared anywhere in fakeshop — the implicit `"both"` default is the live proof surface, exactly as specced.
8. **Root-field name collisions:** `node` / `nodes` / `genre` collide with nothing across the five composed app `Query` classes (grep-verified); the no-Node-types finalize ledger check passes trivially (GenreType + products/kanban Relay types exist).

### DRY analysis

- **Existing patterns reused** (cite `path:NN`, pin-at-write-time):
  - `apps/library/schema.py:135-149` (`ShelfType.get_queryset`) and `:192-205` (`BranchType.get_queryset`) — the staff-bypass visibility pattern `BookType.get_queryset` mirrors; the request/user unwrap dance (`info.context` → `request` → `user` → `is_staff`) is currently duplicated 2x and the new hook would be the **3rd byte-near copy** — hoisted, see below.
  - `apps/library/schema.py:172-181` (`GenreType.Meta`) — the `interfaces = (relay.Node,)` declaration shape the `BookType.Meta` copies.
  - `django_strawberry_framework/relay.py::DjangoNodeField` / `::DjangoNodesField` (shipped Slice 2) and `django_strawberry_framework/testing/relay.py::global_id_for` (shipped Slice 5) — consumed, not modified. The mismatch wire text to assert live is `"Wrong node type: expected a GenreType id, received a BookType id."` (`relay.py::_check_typed_match`, `graphql_type_name`-based; carries NO extensions code by design); the malformed-id code is `extensions={"code": "GLOBALID_INVALID"}` (`relay.py::_decode_or_graphql_error`).
  - `test_library_api.py` file-local helpers, reused as-is: `_post_graphql` (:76), `_assert_graphql_data` (:85), `_decode_global_id` (:660), `_post_graphql_as_staff` (:710), `_seed_genres` (:2138), `_genres_connection` (:2400), `_field_type` (:92), and the autouse `_reload_project_schema_for_acceptance_tests` fixture (:47-50 — autouse, so every new test rides it by construction; new docstrings still name it per the spec's by-name pinning).
  - The in-test-body class-import discipline from `test_multi_db.py:125-132` / the file-header invariant at `test_library_api.py:26-27`: tests must NOT module-level import classes from `apps.library.schema`; the hidden-row / mixed-batch tests import `BookType` (for `global_id_for`) inside the test body after the autouse reload.
  - Inline `Model.objects.create` seeding per `AGENTS.md` (library has no `services.py`); `_seed_library_graph` (:53) for graph-shaped fixtures where the full graph helps.
- **New helpers justified:**
  - `apps/library/schema.py::_user_is_staff(info)` — single responsibility: the context→request→user→`is_staff` unwrap. Call sites: `ShelfType.get_queryset`, `BranchType.get_queryset`, the new `BookType.get_queryset` (3 sites — the hoist lands exactly where the third copy would appear, the established build-cycle rule). The two existing hooks are refactored to delegate; behavior is byte-identical and already pinned by the shipped visibility tests (lines 1159-1210, 1738-1800 et al.), so this is a zero-risk consolidation inside the slice's own file. The staged TODO pseudocode itself anticipates this shape (`if user_is_staff(info):`).
  - No new test-file helper is *required*; a small file-local `_node_query(gid, selection)` formatter is at Worker 2's discretion if the `node(id:)` query literal repeats ≥3 times (see discretion items).
- **Duplication risk avoided:**
  - The cursor-round-trip + `totalCount` contracts named by the spec (`test_genres_connection_cursor_round_trip` / `test_genres_connection_total_count`) are **already live-proven** by the shipped `test_genre_connection_full_round_trip` (:2144 — `endCursor` → `after` continuation with no-overlap assertion AND post-filter `totalCount == 4`) plus `test_genre_connection_first_zero_empty_edges` (:2257 — `totalCount` pre-slice). Duplicating them would be a DRY defect; this plan **maps them by citation** (the Slice-4 "mapped, not duplicated" precedent the spec itself uses at line 580) and records the mapping for the final-verification spec-reconciliation pass. No new test is written for these two names.
  - Do NOT hand-roll base64 GlobalID minting in the new tests: book ids come from `testing.relay.global_id_for` (spec line 606); genre ids in refetch tests come from the **emitted** `id` of a prior query (round-trip realism) or `global_id_for` where no prior query exists.
  - The hidden-row test must not duplicate `_post_graphql_as_staff`'s user-creation block — call the helper.

### Implementation steps

Line numbers are pin-at-write-time navigational hints; verify against current source before editing.

1. `examples/fakeshop/apps/library/schema.py:10-16` — extend the existing `django_strawberry_framework` import block with `DjangoNodeField, DjangoNodesField` (alphabetical within the block).
2. `examples/fakeshop/apps/library/schema.py` (module level, near `_branches_manager_resolver`) — add `_user_is_staff(info) -> bool` implementing the context→request→user→`is_staff` unwrap; refactor `ShelfType.get_queryset` (:144-148) and `BranchType.get_queryset` (:200-204) to `if _user_is_staff(info): return queryset` (docstrings unchanged; behavior identical).
3. `examples/fakeshop/apps/library/schema.py:61-85` — delete the Slice-6 TODO block; promote `BookType`:
   - add `interfaces = (relay.Node,)` to `BookType.Meta` (placed with the other Meta keys, mirroring `GenreType.Meta`),
   - add the `get_queryset` classmethod (before `Meta`, the `ShelfType` ordering): staff bypass via `_user_is_staff(info)`, else `queryset.exclude(circulation_status=...)` hiding `"repair"`,
   - docstring notes the Decision-12 purpose (the live hidden-row eligible type) in one or two lines — keep it lean; the spec is the record.
4. `examples/fakeshop/apps/library/schema.py:336-342` — replace the TODO block with the three root fields on `Query`, exactly the spec's supported nullable-by-contract spellings:
   - `node: relay.Node | None = DjangoNodeField()`
   - `nodes: list[relay.Node | None] = DjangoNodesField()`
   - `genre: GenreType | None = DjangoNodeField(GenreType)`
   Keep them where the TODO sits (after `all_library_genres_connection`, before `all_library_patrons`) with a short comment citing Decision 12 + the import-from-public-surface fact. `__all__` stays `("Query",)`.
5. `examples/fakeshop/test_query/test_library_api.py:2533-2581` — delete the TODO block; append the new live test block (a section comment naming spec-032 Slice 6 / Decision 12, the README rule, and the autouse fixture) with the tests under `### Test additions / updates`. Module-level import of `global_id_for` from `django_strawberry_framework.testing.relay` is safe (package module, not reloaded); `BookType` / `GenreType` class references are imported **inside test bodies** only.
6. `examples/fakeshop/tests/test_inspect_django_type.py:73-81` (`test_inspect_by_registered_name`) and `:100-105` (`test_inspect_by_dotted_path`) — update the pk-row expectations for the promotion: `GlobalID!` + `relay.Node id` (the `test_inspect_relay_node_pk_row` shape at :226-238), drop the `"Int!" in text` / `"GlobalID!" not in text` asserts, and update the line-78 comment (it currently states BookType declares no interfaces). Do not touch the other inspect tests (`_field_row`-scoped; promotion-safe — but see the watch item in Notes for Worker 3).
7. Run `uv run ruff format .` and `uv run ruff check --fix .`; classify any churn per the build-report contract. Run the focused suite (no coverage flags): `uv run pytest examples/fakeshop/test_query/test_library_api.py examples/fakeshop/apps/library/tests/ examples/fakeshop/tests/test_inspect_django_type.py --no-cov`.
8. Grep-confirm zero `TODO(spec-032` anchors remain in `apps/library/schema.py` and `test_query/test_library_api.py`; confirm the Slice-7 anchors elsewhere are untouched.

### Test additions / updates

All in `examples/fakeshop/test_query/test_library_api.py`; every test rides the autouse `_reload_project_schema_for_acceptance_tests` fixture (name it in the block comment / docstrings per the spec's by-name pinning); all seeding is inline `Model.objects.create` (library rule); all assertions are **behavior, not SQL shape** (pre-`033` posture, Decision 12) — no `CaptureQueriesContext` in the new nested-connection tests.

- `test_node_refetch_genre` — create a genre; query `allLibraryGenres { id name }`; refetch the emitted id via `node(id:) { ... on GenreType { id name } }`; assert id + field equality (round-trip through the live wire format).
- `test_typed_node_field_live` — `genre(id: <genre gid>) { id name }` resolves the row; assert `errors` absent.
- `test_typed_node_field_mismatch_live` — `genre(id: <book gid via global_id_for(BookType, pk)>)` → 200, `errors` present, message contains `"Wrong node type: expected a GenreType id, received a BookType id."` (the wire-text watch from the build memory — flag any drift, do not loosen the assertion below the expected/received names).
- `test_node_malformed_id_live` — post `node(id: "not-base64!!!")` → 200 (never a 500), `errors[0].extensions.code == "GLOBALID_INVALID"`; assert the message starts with `"Invalid GlobalID:"` (proves the package converted, not Strawberry's upstream argument error — reachable because the argument is `strawberry.ID`, Revision 7 P1).
- `test_node_uncoercible_pk_live` — post the base64 of `library.genre:abc` → 200, `data.node is None`, `errors` absent (Revision 7 P2; the existence-family `null`, not an error).
- `test_nodes_batch_mixed_types_order_and_null` — seed a genre and a non-`repair` book; ids `[genre_gid, missing_or_bogus_pk_gid, book_gid]` (the hole id is WELL-FORMED per the staged anchor — a missing pk; malformed-mid-batch is pinned package-side in `tests/test_relay_node_field.py::test_nodes_malformed_id_mid_batch`); assert input order preserved, the `null` hole in position, both real rows resolved to their concrete types (inline fragments).
- `test_nodes_duplicates_and_empty_live` — `[gid, gid]` resolves the same row per position; `ids: []` returns `[]` (one test, two posts — or two asserts on aliases, Worker 2's call).
- `test_genres_connection_cursor_round_trip` / `test_genres_connection_total_count` — **mapped, not duplicated**: satisfied by the shipped `test_genre_connection_full_round_trip` (:2144 — `endCursor`→`after` + `totalCount`) and `test_genre_connection_first_zero_empty_edges` (:2257); record the citation in the build report; Worker 1 promotes the mapping into the spec's Test plan at final verification (the Slice-4 precedent).
- `test_genre_books_connection_behavior` — seed one genre linked to ≥3 books (one of them `repair` to also observe the target `get_queryset` inside the nested connection, the Decision-12 bonus proof); query `allLibraryGenres { booksConnection(first: 2) { edges { node { title } } pageInfo { hasNextPage endCursor } } }`, then continue with `after:`; assert right rows, right order, no overlap, and the `repair` row absent for the anonymous client. Behavior only.
- `test_book_genres_connection_sidecars_and_total_count` — seed a book with ≥2 genres; query the book (via `allLibraryBooks` or the typed refetch) selecting `genresConnection(filter: { name: { iContains: ... } }, orderBy: [{ name: ASC }], first: ...) { totalCount edges { node { name } } }`; assert the filter narrows, the order arranges, and `totalCount` equals the post-filter count — the target-driven contract (`GenreType.Meta.connection = {"total_count": True}`), live.
- `test_book_loans_relation_stays_list_only` — introspect `__type(name: "BookType")` field names: `loans` present, `loansConnection` absent, `genresConnection` present (the positive control in the same assertion set); plus a behavior query `loans { note }` still list-shaped. The live graceful-degradation proof.
- `test_node_hidden_row_null_live` — create a `circulation_status="repair"` book; mint its gid via `global_id_for(BookType, book.pk)` (in-body import of the freshly-reloaded `BookType`); anonymous `node(id:)` → `data.node is None`, no errors; `_post_graphql_as_staff` with the same id → the row (visibility, not existence).
- **Updates to existing tests** — `test_library_api.py`: none required by the audit (no existing live assertion selects a book id — record this audited finding in the build report). `examples/fakeshop/tests/test_inspect_django_type.py`: the two pk-row updates per Implementation step 6.
- **No-edit verifications to record in the build report**: `apps/library/tests/test_schema.py` (subset assertions — re-confirm green in the focused run), `test_multi_db.py` (sharded-only, title-set assertions; reading-level verification only).
- Temp/scratch tests: none needed; Worker 3 may stage a `docs/builder/temp-tests/slice-6/` probe for the synthesized-connection SDL if it wants an in-process look, but the live suite is the contract.

### Implementation discretion items

Assessed and deliberately left to Worker 2 (style-level, both shapes valid):

- `exclude(circulation_status="repair")` literal vs `models.Book.CirculationStatus.REPAIR` enum member — the model enum exists; either reads fine (ShelfType uses the literal `"secret"` precedent; the enum is more greppable).
- Whether to add a file-local `_node_query(gid, selection)` / `_post_node(gid)` formatter in `test_library_api.py` if the `node(id:)` query literal repeats ≥3 times; one helper max, no parametrization gymnastics.
- The mixed-batch hole id: any WELL-FORMED missing-pk genre or book gid (e.g. `global_id_for(GenreType, 999999)`); exact value free.
- `test_nodes_duplicates_and_empty_live` as one test with two posts vs two aliases in one query.
- Exact placement/wording of the new section comment in the test file and the one-line docstring on `BookType.get_queryset`.

NOT discretionary: the three root-field annotation spellings (nullable-by-contract, verbatim from the spec), the `_user_is_staff` hoist, the mapped-not-duplicated cursor/totalCount tests, the in-body class-import discipline, behavior-only assertions for nested connections, and `global_id_for` (never hand-minted base64) for book ids.

### Notes for Worker 1 (spec reconciliation)

- **Spec line 110 churn-confinement claim is incomplete**: "Churn is confined to `test_query/test_library_api.py`" misses `examples/fakeshop/tests/test_inspect_django_type.py::test_inspect_by_registered_name` / `::test_inspect_by_dotted_path`, which pin BookType's pk as `Int!` / not-`GlobalID!` and break on the promotion. Resolved in-plan (Implementation step 6 updates them); at final verification Worker 1 amends the Slice-6 checklist sentence (and the Decision-12 blast-radius wording if needed) to record the two-test inspect-suite churn. The companion claims (test_schema.py needs no edit; staff infra exists; no `repair` row exists) all verified true.
- **Cursor round-trip / totalCount mapping**: `test_genres_connection_cursor_round_trip` / `test_genres_connection_total_count` are satisfied by citation to the shipped `test_genre_connection_full_round_trip` / `test_genre_connection_first_zero_empty_edges`; promote the satisfying names into the spec's Test plan Slice-6 list at final verification (Slice-4 precedent, build-memory pattern).
- Inside-`test_library_api.py` book-id churn turned out to be zero existing tests (audited); the spec's "+300/-60" delta estimate still roughly holds via the TODO-block removals (~75 lines).

### Notes for Worker 3

- Watch item: the synthesized `genres_connection` annotation now appears on `BookType` when `inspect_django_type` renders it — the command reads finalized Strawberry field metadata, so it should render a `GenreTypeConnection!`-ish row, but no test pins that row; if the focused inspect run errors, that is a product finding to surface, not a test to delete.
- The mismatch-error and `GLOBALID_INVALID` wire texts go live in this slice — assert them tightly (build-memory watch).

### Spec slice checklist (verbatim)

- [x] [`examples/fakeshop/apps/library/schema.py`][fakeshop-library-schema]: add `node: relay.Node | None = DjangoNodeField()`, `nodes: list[relay.Node | None] = DjangoNodesField()`, and the typed `genre: GenreType | None = DjangoNodeField(GenreType)` to the library `Query`; promote [`BookType`][fakeshop-library-schema] to Relay-Node shape (`interfaces = (relay.Node,)`) so `GenreType.books` (reverse M2M) synthesizes a live `booksConnection` counterpart and `BookType.genres` (forward M2M) synthesizes a live `genresConnection` whose target declares `total_count` — while `BookType.loans` (reverse FK to the non-Relay `LoanType`) stays list-only under the implicit default (the live graceful-degradation proof); and add a `BookType.get_queryset` hiding `circulation_status="repair"` from non-staff requests (the shipped [`ShelfType.get_queryset`][fakeshop-library-schema] `topic="secret"` pattern) so a Relay-Node-shaped **and** visibility-filtered type exists for the live hidden-row `null` test (no fakeshop type is both today).
- [x] [`examples/fakeshop/test_query/test_library_api.py`][fakeshop-test-library]: live HTTP Relay-shaped queries — **the mandated coverage home for every live-reachable path per [`test_query/README.md`][fakeshop-test-query-readme]**, all riding the `_reload_project_schema_for_acceptance_tests` fixture: bare `node(id:)` refetch of an emitted Genre `GlobalID`; the typed-field happy path and expected/received-types mismatch error; the malformed-id `GLOBALID_INVALID` error; `nodes(ids:)` batch with order preservation, a `null` hole, duplicate ids, and the empty list; the paginated `allLibraryGenresConnection` cursor round-trip (`endCursor` → `after`) and `totalCount`; `genre → booksConnection` and `book → genresConnection` nested relation-as-Connection queries (the latter proving sidecar `filter:` / `orderBy:` arguments and target-driven `totalCount` live) asserting **behavior** (right rows, right pagination), not SQL shape (pre-`033` posture); the hidden-row `null` semantics through a `get_queryset`-filtered type.
- [x] Update the existing library assertions the `BookType` Relay promotion changes (its `id` becomes `GlobalID!`; emitted book ids move to the encoded model-label payload). Churn is confined to [`test_query/test_library_api.py`][fakeshop-test-library]: the per-app introspection suite [`examples/fakeshop/apps/library/tests/test_schema.py`][fakeshop-library-tests] asserts type presence / declaration order with **no** book-id literals (checked — needs no edit, Revision 7 Q4), and the hidden-row test's staff half reuses the existing `client.force_login` of an `is_staff=True` user already set up for the `ShelfType` visibility tests.

---

## Build report (Worker 2)

### Files touched

- `examples/fakeshop/apps/library/schema.py` — imported `DjangoNodeField` / `DjangoNodesField` from the package public surface (alphabetical within the existing block); added the module-level `_user_is_staff(info)` hoist (single responsibility: the context→request→user→`is_staff` unwrap) and refactored `ShelfType.get_queryset` / `BranchType.get_queryset` to delegate (docstrings unchanged, behavior byte-identical); deleted the Slice-6 `BookType`-promotion TODO block and promoted `BookType` (`interfaces = (relay.Node,)` placed after `fields` mirroring `GenreType.Meta`; `get_queryset` classmethod before `Meta` in the `ShelfType` ordering, hiding `circulation_status=models.Book.CirculationStatus.REPAIR` from non-staff via `_user_is_staff`; class docstring notes the Decision-12 purpose in two lines); deleted the root-field TODO block and added the three root fields verbatim per the spec spellings (`node: relay.Node | None = DjangoNodeField()`, `nodes: list[relay.Node | None] = DjangoNodesField()`, `genre: GenreType | None = DjangoNodeField(GenreType)`) at the TODO's position (after `all_library_genres_connection`, before `all_library_patrons`) with a short Decision-12 comment. `__all__` unchanged (`("Query",)`).
- `examples/fakeshop/test_query/test_library_api.py` — deleted the Slice-6 live-test TODO enumeration block; added the module-level `global_id_for` import (package module — safe; class references stay in-test-body per the file-header reload invariant); appended the Slice-6 section (comment names spec-032 Slice 6 / Decision 12, the README rule, the autouse `_reload_project_schema_for_acceptance_tests` fixture, the behavior-only posture, and the cursor/totalCount mapped-not-duplicated citation) with two file-local helpers (`_seed_shelf`, `_post_node`) and ten new live tests (list under Tests added).
- `examples/fakeshop/tests/test_inspect_django_type.py` — the two pk-pin updates the promotion forces (plan finding 1 / Implementation step 6): `test_inspect_by_registered_name` now asserts `GlobalID!` + `relay.Node id` (the `test_inspect_relay_node_pk_row` shape) and the line-78 comment is rewritten for the Slice-6 promotion; `test_inspect_by_dotted_path` flips its `"Int!" in text` assert to `"GlobalID!" in text`. No other inspect test touched.

### Tests added or updated

All new tests in `examples/fakeshop/test_query/test_library_api.py`, every one on the autouse reload fixture, inline `Model.objects.create` seeding, behavior-only assertions:

- `test_node_refetch_genre` — bare `node(id:)` round-trip of an EMITTED genre id; id + field equality.
- `test_typed_node_field_live` — typed `genre(id:)` happy path (`errors` absent, row fields equal).
- `test_typed_node_field_mismatch_live` — book gid at `genre(id:)` → 200 + errors containing the exact wire text `"Wrong node type: expected a GenreType id, received a BookType id."` (tight assert per the Worker 3 watch item).
- `test_node_malformed_id_live` — `"not-base64!!!"` → 200, `errors[0].extensions.code == "GLOBALID_INVALID"`, message starts `"Invalid GlobalID:"`.
- `test_node_uncoercible_pk_live` — base64 of `library.genre:abc` → 200, `data.node is None`, no errors.
- `test_nodes_batch_mixed_types_order_and_null` — `[genre_gid, global_id_for(GenreType, 999999), book_gid]` → input order preserved, positional `null` hole, both rows resolved to concrete types via inline fragments + `__typename`.
- `test_nodes_duplicates_and_empty_live` — `[gid, gid]` resolves per position; `ids: []` → `[]` (one test, two posts — discretion item).
- `test_genre_books_connection_behavior` — nested reverse-M2M `booksConnection(orderBy:, first:, after:)` over 3 visible + 1 `repair` book: right rows, right order, no overlap, hidden row absent for the anonymous client (the nested `get_queryset` bonus proof).
- `test_book_genres_connection_sidecars_and_total_count` — synthesized forward-M2M `genresConnection(filter:, orderBy:, first:)`: `iContains` narrows (3 of 4), `name ASC` arranges, `totalCount == 3` (post-filter, ≠ page size 2 ≠ grand total 4 — the target-driven `GenreType.Meta.connection = {"total_count": True}` contract live).
- `test_book_loans_relation_stays_list_only` — `__type(name: "BookType")` field names: `loans` present, `loansConnection` absent, `genresConnection` present (positive control); plus the live `loans { note }` list-shape behavior query.
- `test_node_hidden_row_null_live` — `repair` book gid via in-body `BookType` import + `global_id_for`; anonymous `node(id:)` → `null` with no errors; `_post_graphql_as_staff` with the same id resolves the row.
- `test_genres_connection_cursor_round_trip` / `test_genres_connection_total_count` — **mapped, not duplicated** per the plan: satisfied by the shipped `test_genre_connection_full_round_trip` (`endCursor` → `after` continuation with no-overlap + post-filter `totalCount == 4`) and `test_genre_connection_first_zero_empty_edges` (pre-slice `totalCount`); the mapping is recorded in the new section comment for Worker 1's final-verification spec promotion (Slice-4 precedent).
- Updated: `examples/fakeshop/tests/test_inspect_django_type.py::test_inspect_by_registered_name` / `::test_inspect_by_dotted_path` (pk pins flipped to the Relay shape, see Files touched).
- Updates to existing `test_library_api.py` tests: **none** — re-confirms the plan's audited finding that no existing live assertion selects a book `id`; the focused run passed with zero edits to pre-existing tests.
- No-edit verifications: `apps/library/tests/test_schema.py` re-confirmed green in the focused run (subset + declaration-order assertions hold through the promotion); `test_multi_db.py` re-read — in-fixture reloaded `BookType` import + title-set assertions only, promotion-safe (reading-level verification; sharded-only, not in the default run per the plan).

### Validation run

- `uv run ruff format .` — pass (1 file reformatted: my own new test code in `test_library_api.py`; the pre-existing COM812 formatter warning is baseline).
- `uv run ruff check --fix .` — pass ("All checks passed!").
- `git status --short` after both — modified: `examples/fakeshop/apps/library/schema.py`, `examples/fakeshop/test_query/test_library_api.py`, `examples/fakeshop/tests/test_inspect_django_type.py` (all three slice-intended, listed in Files touched). Every other entry is the build's accumulated prior-slice diff (package + tests files from Slices 1–5, the spec edit, the `bld-*`/`build-*` artifacts, and the pre-flight `D docs/builder/*.md` deletions recorded in the plan preamble) — untouched by this pass, no tool churn to revert.
- Focused tests (`--no-cov` only, per the artifact's step 7): `uv run pytest examples/fakeshop/test_query/test_library_api.py examples/fakeshop/tests/test_inspect_django_type.py examples/fakeshop/apps/library/tests/ --no-cov` → **89 passed** in 12.64s (includes all pinned query-count tests from blast-radius item 4 — all green unmodified).
- Anchor sweep: `grep -rn "TODO(spec-032"` over `apps/library/schema.py` + `test_query/test_library_api.py` → zero hits; the Slice-7 anchors in `CHANGELOG.md`, `GOAL.md`, `KANBAN.md`, `README.md`, `TODAY.md`, `docs/GLOSSARY.md`, `docs/README.md`, `docs/TREE.md`, and the spec remain untouched.

### Implementation notes

- `exclude(circulation_status=models.Book.CirculationStatus.REPAIR)` — took the enum member over the `"repair"` literal (discretion item; more greppable, and the model enum already exists — the `ShelfType` `"secret"` literal precedent has no enum to reach for).
- `_post_node(global_id, selection="__typename")` — the discretion-item node-query formatter landed (4 call sites: refetch, malformed, uncoercible, hidden-row anonymous half); returns the FULL payload, not `data.node`, so callers assert errors presence/absence per Decision 5's two failure families; pins only the never-a-500 transport contract itself.
- `_seed_shelf()` — small file-local fixture helper (branch + shelf one-liner) because five new tests need a `Book` and every `Book` needs a shelf chain; keeps the per-test book creates to single inline `Model.objects.create` lines per the library rule.
- `test_nodes_duplicates_and_empty_live` as one test with two posts (discretion item) — two aliases in one query would interleave the empty-list and duplicate contracts in one response dict for no readability gain.
- The mixed-batch hole id is `global_id_for(GenreType, 999999)` (discretion item: any well-formed missing pk).
- `test_genre_books_connection_behavior` seeds 3 visible + 1 `repair` book and pages `first: 2` so the continuation page (`["Circe"]`, `hasNextPage: False`) proves no-overlap AND the window math over the *filtered* set in one walk; `orderBy: [{ title: ASC }]` (from `BookOrder.Meta.fields`) makes row order deterministic rather than relying on implicit pk order.
- The nested-page helper `_books_page` is local to its one test (not module-level) — only that test queries the nested `booksConnection` envelope twice.

### Notes for Worker 3

- No shadow files used or refreshed this pass; the plan's overview of `schema.py` was sufficient.
- The plan's watch item on `inspect_django_type` rendering the synthesized `genres_connection` row: the focused inspect run passed all 10 tests with no error, so the command tolerates the synthesized field; no test pins its row (unchanged from the plan's posture — nothing to surface).
- Both wire texts are asserted tightly as instructed: the full mismatch sentence and the `GLOBALID_INVALID` code + `"Invalid GlobalID:"` prefix.
- The three root-field annotations are byte-verbatim from the spec/plan; `ruff format` kept them one-per-line as written.

### Notes for Worker 1 (spec reconciliation)

- Carried from the plan, now implemented: the two `test_inspect_django_type.py` pk-pin updates (spec line 110's churn-confinement sentence needs the amendment the plan already records).
- Cursor/totalCount mapping landed as citation (section comment in `test_library_api.py`), per the plan — the spec's Test plan Slice-6 list awaits the promotion of the satisfying names at final verification.
- No plan-vs-implementation drift: every implementation step landed as written; all deviations were inside the plan's explicit discretion items (recorded under Implementation notes).

---

## Review (Worker 3)

### High:

None.

### Medium:

None.

### Low:

None.

### DRY findings

- **The `_user_is_staff` hoist landed correctly and removed the targeted duplication.** Verified two ways: (1) behavior identity by diff reading — the helper body (`getattr(info, "context", None)` → `getattr(context, "request", None) or context` → `getattr(request, "user", None)` → `user is not None and getattr(user, "is_staff", False)`) is the exact four-line chain previously inlined at `ShelfType.get_queryset` and `BranchType.get_queryset`, now delegated with docstrings untouched; (2) the re-run `review_inspect.py` overview's repeated-literals section now reads only `3x "subtitle"` — the plan-time `2x "is_staff"` pair is gone. The shipped Shelf/Branch visibility tests (e.g. `test_library_api.py:1199`, `:1783`) all pass unmodified in the focused run, pinning the behavior-identical claim.
- **Cursor round-trip / totalCount mapped-not-duplicated citation verified.** `test_genre_connection_full_round_trip` (`test_library_api.py:2145`) asserts the `endCursor` → `after` continuation with explicit no-overlap rows AND `totalCount == 4` post-filter (≠ page size 2 ≠ grand total 5); `test_genre_connection_first_zero_empty_edges` (`:2250`) asserts the pre-slice `totalCount` under `first: 0`. The two spec-named contracts are fully covered by the citations; writing them again would have been the DRY defect the plan predicted. The mapping is recorded in the new section comment for Worker 1's spec promotion.
- **`_post_node` helper** (4 call sites: refetch, malformed, uncoercible, hidden-row anonymous half) is the plan's discretion-item formatter at exactly the ≥3-repeat threshold; returning the full payload (not `data.node`) keeps both Decision-5 failure families assertable. The staff half of `test_node_hidden_row_null_live` builds its `node(id:)` literal inline because it must route through `_post_graphql_as_staff`'s logged-in client — not a consolidation candidate.
- **`_seed_shelf`** (branch+shelf one-liner, 5 call sites) keeps per-test book creates to single inline `Model.objects.create` lines per the library rule — justified, not premature.
- The new tests repeat the `status_code == 200` / `json()` / `"errors" not in payload` envelope triple where `_post_graphql` is called directly — this is the file's established idiom across the pre-existing ~2,400 lines (and `_assert_graphql_data` only fits exact-match cases); no new helper warranted. No action.
- Integration-pass ledger unchanged by this slice: no new repeated package-source literals introduced (the slice's only package-adjacent file is the example schema, inspected clean).

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` shows exactly the accepted Slice-2 change (the `from .relay import DjangoNodeField, DjangoNodesField` import, the two `__all__` entries alphabetically placed, and the removal of the Slice-2 TODO anchor) — spec-authorized by the Slice-2 checklist ("exported from the package public surface", spec line 5 / Slice-2 sub-checks). **Slice 6 adds no new change to the package root**; the per-memory rule ("verify no NEW change, not empty diff") holds. The consuming side imports `DjangoNodeField` / `DjangoNodesField` from the public surface in `apps/library/schema.py` as the spec requires; `apps/library/schema.py::__all__` stays `("Query",)`.

### CHANGELOG sanity

Not applicable; slice did not modify CHANGELOG.md. (Confirmed: the Slice-7 `TODO(spec-032` anchor in `CHANGELOG.md` is untouched by this diff.)

### Documentation / release sanity

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces. The Slice-7 anchors in `CHANGELOG.md`, `GOAL.md`, `KANBAN.md`, `README.md`, `TODAY.md`, `docs/GLOSSARY.md`, `docs/README.md`, `docs/TREE.md`, and the spec were grep-confirmed untouched; the slice's own three `TODO(spec-032 ... Slice 6)` anchors (schema.py x2, test_library_api.py x1) are all removed — `grep -rn "TODO(spec-032"` over the two slice files returns zero hits.

### What looks solid

- **The three root-field spellings are byte-verbatim from the spec** (`node: relay.Node | None = DjangoNodeField()`, `nodes: list[relay.Node | None] = DjangoNodesField()`, `genre: GenreType | None = DjangoNodeField(GenreType)`) at the TODO's position, with the nullable-by-contract comment citing Decision 5's `required=False` dispatch.
- **The `BookType` promotion is exactly the Decision-12 shape**: `interfaces = (relay.Node,)` placed after `fields` mirroring `GenreType.Meta`; `get_queryset` classmethod before `Meta` in the `ShelfType` ordering; the enum-member `exclude(circulation_status=models.Book.CirculationStatus.REPAIR)` (recorded discretion item); staff bypass via the hoisted `_user_is_staff`.
- **Both live wire texts assert tightly against the package source**: the mismatch test pins the full sentence `"Wrong node type: expected a GenreType id, received a BookType id."` — byte-matching `relay.py::_check_typed_match`'s f-string with `graphql_type_name` substitution (and correctly asserts no extensions code is required, since the spec assigns a code only to `GLOBALID_INVALID`); the malformed test pins `extensions.code == "GLOBALID_INVALID"` AND the `"Invalid GlobalID:"` prefix, proving the package conversion (not Strawberry's upstream argument error — the Revision 7 P1 reachability) at `relay.py::_decode_or_graphql_error`.
- **The Decision-5 failure families are discriminated live**: malformed → error with code; uncoercible (`library.genre:abc` via module-level `base64`, line 3 import pre-existing) → `data.node is None` with NO errors entry (existence family, Revision 7 P2); hidden → `null` with NO errors for anonymous AND the row for staff via the reused `_post_graphql_as_staff` (both halves present, no existence-oracle leak — the anonymous response is indistinguishable from a missing row).
- **`nodes` semantics fully pinned live**: input order across two concrete types with inline fragments + `__typename`, the well-formed missing-pk hole (`global_id_for(GenreType, 999999)`) as a positional `null` (the malformed-mid-batch whole-field contract correctly left package-side per the staged anchor), duplicates resolved per position, `ids: []` → `[]`.
- **The synthesis triple is proven exactly per Decision 6/12**: `booksConnection` (reverse M2M) paginates behavior-only with `orderBy: [{ title: ASC }]` determinism, no-overlap continuation, AND the nested `get_queryset` bonus proof (the `repair` row absent through the nested connection); `genresConnection` proves sidecar `filter:`/`orderBy:` + target-driven `totalCount == 3` (post-filter, ≠ page size 2 ≠ grand total 4 — the three-way discrimination); `loans` stays list-only with `genresConnection` as the positive control in the same introspection set plus the live list-shape behavior query.
- **Behavior-not-SQL posture held**: zero `CaptureQueriesContext` / `connection.queries` uses in the new Slice-6 block (grep-verified over the appended lines); every new test rides the autouse `_reload_project_schema_for_acceptance_tests` fixture by construction (autouse at `test_library_api.py:48`) and the section comment names it per the spec's by-name pinning.
- **In-body class-import discipline observed**: `BookType` / `GenreType` imported inside test bodies only; the sole new module-level import is `global_id_for` (package module, not reloaded — safe). All seeding is inline `Model.objects.create`; no `services.py` usage.
- **The `test_inspect_django_type.py` updates are the promotion-forced minimum**: exactly the two tests the plan's blast-radius item 2 named (`test_inspect_by_registered_name` flips `Int!`/not-`GlobalID!` to `GlobalID!` + `relay.Node id` — the `test_inspect_relay_node_pk_row` shape — with the stale comment rewritten; `test_inspect_by_dotted_path` flips its single `Int!` assert); no other inspect test touched, and all 10 pass.
- **Checklist walk (3 boxes, all ticked `- [x]`)**: box 1 (schema.py: three fields + promotion + `get_queryset`) — landed in full, verified against the diff. Box 2 (live test enumeration) — every named contract landed or is citation-mapped with the mapping recorded (the two mapped names verified above). Box 3 (update existing assertions) — the substance landed: the audit's zero-existing-live-assertion finding is recorded in the build report, and the real churn (the two inspect tests) is implemented; the box's "churn is confined to test_library_api.py" sentence is the spec inaccuracy already escalated to Worker 1 (see below). No over-tick, no silent omission.
- Focused run independently reproduced: `uv run pytest examples/fakeshop/test_query/test_library_api.py examples/fakeshop/tests/test_inspect_django_type.py examples/fakeshop/apps/library/tests/ --no-cov` → **89 passed** (matches the build report), including the unmodified pinned query-count tests and `apps/library/tests/test_schema.py` (the Revision 7 Q4 no-edit claim holds).

### Temp test verification

- Static helper re-run (mandated: the slice adds >50 lines outside `django_strawberry_framework/`): `uv run python scripts/review_inspect.py examples/fakeshop/apps/library/schema.py --output-dir docs/shadow` — clean (0 control-flow hotspots; repeated literals down to `3x "subtitle"`, confirming the DRY hoist). Shadow files used for control-flow orientation only; all line numbers cited above are original-source.
- **Skips recorded**: `examples/fakeshop/test_query/test_library_api.py` (~2,870 lines post-slice) — per-cycle live-test file of flat test functions with no review-worthy control flow; the Slice-4 overview already exists and the Slice-6 additions were read in full from the diff. `examples/fakeshop/tests/test_inspect_django_type.py` — 6-line assertion-flip delta, no logic.
- No temp tests created under `docs/builder/temp-tests/slice-6/`: the optional synthesized-connection SDL probe the plan mentioned is superseded by the live `__type(name: "BookType")` introspection test, which pins the same fact (`genresConnection` present / `loansConnection` absent) on the contract surface; the live suite plus the independently reproduced focused run sufficed. Disposition: none needed.

### Notes for Worker 1 (spec reconciliation)

- Carried from the plan and build report, confirmed by review: **spec line 110's "Churn is confined to `test_query/test_library_api.py`" is incomplete** — the promotion forced the two `test_inspect_django_type.py` pk-pin flips (verified as the exact minimum). Amend the Slice-6 checklist sentence (and Decision-12 blast-radius wording if needed) at final verification, per the plan's note.
- **Promote the cursor/totalCount mapping into the spec's Test plan Slice-6 list**: `test_genres_connection_cursor_round_trip` / `test_genres_connection_total_count` are satisfied by `test_genre_connection_full_round_trip` + `test_genre_connection_first_zero_empty_edges` (citation verified during this review; the Slice-4 precedent).
- Watch item disposition (plan's Notes for Worker 3): `inspect_django_type` tolerates the synthesized `genres_connection` field — all 10 inspect tests pass with no error; no test pins the synthesized row's rendering. Acceptable for this card; a future inspect-coverage slice could pin it.

### Review outcome

`review-accepted` — no High/Medium/Low findings; all three checklist boxes verified landed (no over-tick); the two spec-reconciliation items are recorded above for Worker 1's final verification. Status line updated.

---

## Final verification (Worker 1)

### Summary

Slice 6 shipped the fakeshop library activation in full (Decision 12): `BookType` promoted to Relay-Node shape (`interfaces = (relay.Node,)`) with a `get_queryset` hiding `circulation_status="repair"` from non-staff; the three root refetch fields (`node` / `nodes` / typed `genre`) added to the library `Query` byte-verbatim per the spec spellings, imported from the package public surface; ten new live tests in `test_query/test_library_api.py` covering refetch, typed happy/mismatch, malformed `GLOBALID_INVALID`, uncoercible-pk `null`, mixed/duplicate/empty `nodes` batches, the synthesized `booksConnection` / `genresConnection` (sidecars + target-driven `totalCount`), the `loans` list-only graceful degradation, and the hidden-row `null` vs staff visibility; plus the two promotion-forced pk-pin flips in `tests/test_inspect_django_type.py`.

- **Checklist audit (3 boxes, all `- [x]`, verified against the diff)**: box 1 — the three root-field annotations, the `BookType.Meta.interfaces` promotion, and the `get_queryset` hook (enum-member `exclude`, `_user_is_staff` staff bypass) all present in `apps/library/schema.py`; box 2 — every named live contract landed as a test or is citation-mapped (the cursor-round-trip/totalCount pair — see Spec changes); box 3 — the substance landed: zero existing live tests selected a book id (audited finding held), the real churn is the two `test_inspect_django_type.py` updates, and the staff half reuses `_post_graphql_as_staff`. No over-tick, no silent deferral.
- **DRY ruling**: the `_user_is_staff` hoist landed exactly at the third-copy site and removed the 2x inline context-unwrap from `ShelfType` / `BranchType` (diff-verified byte-identical behavior; shipped visibility tests pass unmodified) — the slice's targeted duplication is GONE. The mapped-not-duplicated cursor/totalCount citation prevented two redundant tests. New file-local helpers (`_post_node` 4 sites, `_seed_shelf` 5 sites, per-test `_books_page`) all meet the ≥3-repeat threshold or are single-test-local — accepted. No new package-source duplication; the standing integration-pass ledger items (gate-tail 3x consolidation candidate, ".Meta.interfaces entry " prefix, fifth-guard wording, test-file GraphQL doc literals, Worker 3's stale-docstring Low for Worker 2) carry unchanged into the integration pass.
- **Focused run**: `uv run pytest examples/fakeshop/test_query/test_library_api.py examples/fakeshop/tests/test_inspect_django_type.py examples/fakeshop/apps/library/tests/ tests/test_relay_node_field.py --no-cov` → **115 passed** in 15.91s (the Worker 2/3 89-test scope plus the 26 package-side node-field tests — all green, pinned query-count tests included).
- **Anchor sweep**: zero `TODO(spec-032` hits in the two slice files; the remaining anchors are all Slice-7-owned doc surfaces (CHANGELOG, GOAL, KANBAN, README, TODAY, docs/GLOSSARY, docs/README, docs/TREE, the spec) — untouched, as required.
- **Wire-text watches discharged**: the mismatch sentence `"Wrong node type: expected a GenreType id, received a BookType id."` and `GLOBALID_INVALID` + `"Invalid GlobalID:"` are now live-pinned tightly; no drift observed.

Final status: **final-accepted**.

### Spec changes made (Worker 1 only)

- Spec line 5 (status line): "Slices 1–5 implemented … Slices 6–7 not started" → "Slices 1–6 implemented … Slice 7 not started", with a Slice-6/Decision-12 parenthetical noting the live library activation. Reason: status currency per the build-cycle rule.
- Spec line 110 (Slice-6 checklist box 3): "Churn is confined to `test_query/test_library_api.py`" → "Churn lands in `test_query/test_library_api.py` plus two pk-row pin updates in `examples/fakeshop/tests/test_inspect_django_type.py` (…flipped to the `GlobalID!` + `relay.Node id` shape — found at build time)". Reason: the original confinement claim was factually incomplete — the `BookType` promotion forced `test_inspect_by_registered_name` / `test_inspect_by_dotted_path` updates (plan blast-radius finding 2, confirmed by Workers 2 and 3).
- Spec line 601 (Test plan, Slice 6): recorded the satisfying test names for the citation-mapped pair — `test_genres_connection_cursor_round_trip` / `test_genres_connection_total_count` are satisfied by the shipped `test_genre_connection_full_round_trip` + `test_genre_connection_first_zero_empty_edges` (mapped, not duplicated; the Slice-4 precedent at the Slice-4 Test-plan section). Reason: promote the build-verified mapping into the spec's contract record so the names are findable.
- `check_spec_glossary.py --spec docs/spec-032-full_relay-0_0_9.md` re-run after the edits: OK, 38 terms.
