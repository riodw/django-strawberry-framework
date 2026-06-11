# Build: Slice 4 — cursor-contract conformance + permission integration

Spec reference: `docs/spec-032-full_relay-0_0_9.md` (Slice-4 checklist lines 99-103; Decision 9 at 426-441; Decision 5 at 335-357; Edge cases 516-518, 531; Test plan intro 533-543 + Slice 4 at 578-582; Implementation-plan table row 4 at 505; DoD item 7 at 670-672; Revision 2 P1 at line 39; Revision 6 P3 at line 24; pre-`033` posture: Decision 12 / build-plan context flag)
Status: final-accepted

## Plan (Worker 1)

Spec status-line re-verification (worker-1.md per-spawn rule): spec line 5 reads "in build — Slices 1–3 implemented (final-accepted in the build cycle, uncommitted); Slices 4–7 not started" — accurate at the start of this planning pass; no edit needed.

**Tests-only slice (verified). [SUPERSEDED — Worker 2's build falsified this premise for one matrix entry; the slice now ships a production fix in `connection.py`. See `### Plan amendment (Worker 1, first+last guard fix)` below.]** The spec's Implementation-plan table row 4 (line 505) lists only test files (`examples/fakeshop/test_query/test_library_api.py`, `tests/test_relay_connection.py`, `tests/test_relay_node_field.py`, `tests/test_connection.py`, `+290 / -0`); reading the Slice-4 checklist, Decisions 5/9, and the shipped Slices 1–3 diffs surfaces **no required source change** — every behavior the conformance matrix pins is already shipped (`connection.py` pipeline + Strawberry `ListConnection` delegation from spec-030; `relay.py` null/no-oracle contract from Slice 2; the synthesized relation connections from Slice 3). Worker 2 edits only the four test files. Public-surface check is trivially clean (no `__init__.py` diff); no CHANGELOG edit (Slice 7 owns the grant).

Spec-vs-codebase verification: every symbol/fixture the spec names for this slice exists on disk — `allLibraryGenresConnection` (`examples/fakeshop/apps/library/schema.py`, shipped spec-030), the autouse `_reload_project_schema_for_acceptance_tests` fixture (test_library_api.py:47-50, wrapping `_reload_library_project_schema` at 19-44), `strawberry_config(**config_kwargs)` forwarding `relay_max_results` to `StrawberryConfig` (`django_strawberry_framework/scalars.py:100-135`), the Slice-3 synthesis machinery and its cardinality fixtures (`tests/test_relay_connection.py::_make_type` / `_schema_with_root` / `_seed_library_books`), and the Slice-2 root-field permission tests (see the pre-satisfied-contract note below). Strawberry's cap error text source-verified against the locked engine: `.venv/lib/python3.14/site-packages/strawberry/relay/utils.py:157` — `"Argument 'first' cannot be higher than {max_results}."` (and `:170` for `last`). No spec-vs-codebase gap requiring escalation; two pre-satisfied/already-pinned overlaps are resolved in-plan (see "Notes for Worker 1 (spec reconciliation)" below).

Staged `TODO(spec-032 … Slice 4)` anchors this slice removes (grep-verified; the slice removes its own anchors per the AGENTS.md design-doc discipline, in the same change that ships the tests):

- `examples/fakeshop/test_query/test_library_api.py:2124-2148` — the live PRIMARY conformance-matrix list.
- `tests/test_relay_connection.py:37-46` — the synthesized-relation package-mirror list (the file's module docstring sentence "The Slice-4 staged list below is removed by the change that ships Slice 4." at test_relay_connection.py:16-17 is removed/reworded in the same change so the docstring stays accurate).
- `tests/test_relay_node_field.py:680-686` — the permission-integration list (contract pre-satisfied by Slice 2; see below).
- `tests/test_connection.py:1342-1352` — the `relay_max_results` cap entry.

No other slice's anchors are touched (Slice 5 anchors in `testing/` + `tests/testing/test_relay.py`, Slice 6 anchors in `apps/library/schema.py` + test_library_api.py:2416, Slice 7 anchors in docs stay as-is).

`scripts/review_inspect.py` disposition: refreshed shadow overviews for all four touched files (`--output-dir docs/shadow`): `tests__test_relay_connection`, `tests__test_connection`, `tests__test_relay_node_field`, `examples__fakeshop__test_query__test_library_api`. All four are ≥150-line existing files, but the slice adds **pure test functions only** (no production logic, no new helpers with branching beyond a parametrized fixture) — recorded here as the skip-with-reason convention for deep hotspot walking; the overviews were used for the repeated-string-literal DRY signal only (e.g. 20x `allLibraryBooks` / 17x `allLibraryBranches` in the live file are inline GraphQL documents, the suite's established idiom — the new tests follow it; the standing "unhoisted GraphQL doc literals" integration watch item from Slice 2 covers the family).

### DRY analysis

- **Existing patterns reused** (cite file:line):
  - **Live suite plumbing:** `_post_graphql` (test_library_api.py:77-83), `_seed_genres` (test_library_api.py:2153-2156 — the library inline-`Model.objects.create` rule; no services.py), and the **autouse** `_reload_project_schema_for_acceptance_tests` fixture (test_library_api.py:47-50) — every new live test rides it automatically (autouse), satisfying the spec's by-name fixture pinning; new tests carry `@pytest.mark.django_db` like the existing genre-connection block.
  - **Two matrix entries are already pinned live** by the spec-030-era suite and are NOT re-implemented: `first: 0` → `test_genre_connection_first_zero_empty_edges` (test_library_api.py:2264-2297; asserts empty edges + well-formed `pageInfo` incl. the overfetch-by-1 `hasNextPage: True` + null `endCursor`) and `first`+`last` → `test_genre_connection_first_and_last_rejected` (test_library_api.py:2238-2262; asserts the package guard's `GraphQLError` on a 200 — the spec's own "re-affirmed" wording for this entry, Decision 9 line 433). The plan maps the matrix onto them instead of duplicating (see reconciliation note).
  - **Package conformance fixtures:** `tests/test_relay_connection.py::_make_type` (64-83), `_schema_with_root` (85-108), `_seed_library_books` (122-133 — inline library creates, one shelf with N books: the deterministic reverse-FK cardinality fixture), and the `_isolate_global_registry` autouse (48-62, clears `registry` + `_connection_type_cache`). `test_synthesized_connection_paginates` (409-430) is the in-file precedent for behavior-only nested-connection execution assertions (pre-`033` posture).
  - **`relay_max_results` test fixtures:** `tests/test_connection.py::_make_node_type` (73-88) and `_field_schema` (487-503, currently hardcoding `strawberry_config()`); `strawberry_config`'s documented `**config_kwargs` passthrough (`scalars.py:100-135` — `relay_max_results` is its named example). Error text from the locked engine, source-verified (`strawberry/relay/utils.py:151-171`).
  - **Permission-integration tests already exist** (shipped by Slice 2, per the spec's own Slice-2 test list at spec lines 556/559): `test_node_hidden_row_returns_null` (test_relay_node_field.py:246-258), `test_node_missing_row_returns_null` (261-273), `test_node_null_paths_issue_equal_queries` (276-297 — the same-query-count no-existence-oracle pin), and `test_nodes_preserves_input_order_with_null_holes` (393-416 — visible/hidden/missing ids interleaved into the right `null` positions), all over the `_make_hidden_category_node` `get_queryset`-filtered fixture (229-242). Slice 4 adds no near-copies.
  - **Cursor opacity discipline:** every cursor a new test feeds back (`after:` / `before:`) is taken from a prior response's `pageInfo` / `edges[].cursor` — never hand-minted via `to_base64` — matching the shipped round-trip idiom (`test_genre_connection_full_round_trip`, test_library_api.py:2160-2236) and keeping the tests honest against Decision 9's "clients must not parse it" contract.
- **New helpers justified:**
  - `tests/test_relay_connection.py::_shelf_books_connection_schema(shape)` (name at Worker 2's discretion) — single responsibility: build the reverse-FK cardinality fixture the live graph lacks (`BookType` + `ShelfType` over `Shelf.books`, `relation_shapes={"books": shape}` for the parametrized variant, default-`"both"` otherwise) and return the finalized schema via `_schema_with_root(shelf_type)`. Call sites: all seven parametrized matrix tests. This is the one helper that prevents the matrix from being copy-pasted per shape variant.
  - Optionally, a thin live-file helper `_genres_connection(args: str, selection: str) -> dict` posting one `allLibraryGenresConnection` query and returning the connection dict — at Worker 2's discretion (five call sites would use it; the existing block inlines full documents, so inlining is equally acceptable — see discretion items).
  - No new production helpers: the slice ships zero source lines.
- **Duplication risk avoided:**
  - The naive plan would re-add live `test_first_zero` / `test_first_and_last_rejected` beside the byte-equivalent spec-030 tests — avoided by mapping the matrix onto the existing pins (recorded in the live file's block comment and the reconciliation note).
  - The naive package mirror would copy the seven-test matrix once per relation-shape variant — avoided by `pytest.mark.parametrize("shape", ["both", "connection"])` over the single fixture helper, which also delivers the staged anchor's "reverse-FK relation connection AND the narrowed `connection` shape" in one shape-agnostic test body.
  - Strawberry's cap error text appears in exactly one test (one literal); the package never re-implements or re-asserts pagination math beyond observable behavior (Decision 9's delegation posture).
  - The live and package copies of the matrix are deliberate twins by spec mandate (root vs synthesized-relation surface — Decision 9 line 428 "against both"); this is pre-cleared for Worker 3 as not-a-DRY-finding, like the Slice-1 re-affirmation pins.

### Implementation steps

Line numbers are pin-at-write-time navigational hints. Verify against the current source before editing — another worker's pass may have shifted the file since this plan was written.

1. **`examples/fakeshop/test_query/test_library_api.py` — live PRIMARY matrix.**
   - Remove the staged anchor block (test_library_api.py:2124-2148).
   - Extend the spec-030 section header comment (test_library_api.py:2113-2123) with a short spec-032 Slice-4 paragraph: the conformance matrix's live primary home; `test_genre_connection_first_zero_empty_edges` and `test_genre_connection_first_and_last_rejected` are the matrix's `first: 0` and `first`+`last` pins (re-affirmed, not duplicated); the five new tests below complete the matrix; stale-`after` pins ONLY the no-error property (Revision 2 P1); behavior-only, no SQL shape (pre-`033`).
   - Append, after the existing genre-connection block (after test_library_api.py:2368-…`test_genre_connection_order_by_to_many_no_node_multiplication`), five `@pytest.mark.django_db` tests, each first line seeding via `_seed_genres(...)` (library inline-create rule; the autouse reload fixture applies):
     - `test_first_overrun` — seed 3; `first: 10` → exactly the 3 remaining edges, `hasNextPage: false` (Decision 9 line 431).
     - `test_stale_after_cursor_no_error` — seed 4; page 1 `first: 2`, capture `endCursor`; delete the row the cursor position points at (e.g. `models.Genre.objects.order_by("pk")[1].delete()` — the second row in the default deterministic pk order); re-query `first: 2, after: <endCursor>`; assert `status_code == 200` and `"errors" not in payload` **only** — no row/skip/duplicate/next-row assertion (Revision 2 P1; offset cursors encode a position, not row identity).
     - `test_page_info_four_fields` — seed 3; `first: 2` selecting `edges { cursor }` + all four `pageInfo` fields → `hasNextPage: true`, `hasPreviousPage: false`, `startCursor == edges[0].cursor`, `endCursor == edges[1].cursor`; then `first: 2, after: <endCursor>` → `hasNextPage: false`, `hasPreviousPage: true` (Strawberry computes it from slice start > 0).
     - `test_has_next_page_correct_when_edges_unrequested` — seed 3; a `pageInfo`-only query (NO `edges` selection) with `first: 2` → `hasNextPage: true`; and with `first: 3` → `hasNextPage: false` (the `should_resolve_list_connection_edges` distinct path, Revision 6 P3 — the observable inverse of "unrequested").
     - `test_backward_pagination_last_before` — seed 5; `last: 2` → the final two rows in order with `hasPreviousPage: true`; then fetch cursors and query `last: 2, before: <cursor of the last row>` → the two rows immediately preceding it. Row identity is the load-bearing assertion; pin the `pageInfo` flags at the values the locked Strawberry actually produces (Worker 2 verifies by running the focused test, never by guessing — see discretion items).
2. **`tests/test_relay_connection.py` — synthesized-relation package mirror.**
   - Remove the staged anchor block (37-46) and fix the module docstring's now-stale "Slice-4 staged list below" sentence (16-17); extend the docstring's package-internal-by-mandate rationale with one line: the conformance mirror runs here because the synthesized-relation variants need cardinality fixtures the fakeshop graph lacks until Slice 6 (spec line 101).
   - Add `_shelf_books_connection_schema(shape: str)` (helper or fixture, Worker 2's discretion): `_seed_library_books([...])`-style inline data is per-test, so the helper only declares types + builds the schema — `_make_type("BookType", Book, ("id", "title"))`; `_make_type("ShelfType", Shelf, ("id", "code", "books"), meta_extra={"relation_shapes": {"books": shape}} if shape == "connection" else None)` (the `"both"` run exercises the implicit default — pass no key for it so the default path is the thing tested); return `_schema_with_root(shelf_type)`. The nested field under either shape is `booksConnection`.
   - Add a new section ("spec-032 Slice 4 — cursor-contract conformance on the synthesized relation connection") with seven tests, each `@pytest.mark.django_db` + `@pytest.mark.parametrize("shape", ["both", "connection"])`, seeding 3-5 books via `_seed_library_books([...])` (inline library creates; one shelf, deterministic pk order):
     - `test_relation_connection_first_zero` — `booksConnection(first: 0)` → `edges == []`, well-formed `pageInfo` (`hasNextPage` true over a non-empty set — the Strawberry overfetch shape the live first:0 pin documents).
     - `test_relation_connection_first_overrun` — `first:` past the remainder → actual remainder, `hasNextPage: false`.
     - `test_relation_connection_stale_after_no_error` — capture `endCursor` from page 1, delete a book before the position, re-query with `after:` → `result.errors is None` ONLY (Revision 2 P1).
     - `test_relation_connection_first_and_last_rejected` — `(first: 1, last: 1)` → the shipped package guard `GraphQLError` ("mutually exclusive") in `result.errors`.
     - `test_relation_connection_page_info_four_fields` — same four-field shape as the live test, against the nested connection.
     - `test_relation_connection_has_next_page_when_edges_unrequested` — nested `pageInfo`-only selection → correct `hasNextPage` for both a true and a false window.
     - `test_relation_connection_backward_pagination_last_before` — `last:` / `before:` row identity through the relation-manager-seeded pipeline.
   - All assertions are behavior-only (rows, cursors, `pageInfo`) — never SQL shape (pre-`033` posture; build-plan context flag).
3. **`tests/test_connection.py` — the `relay_max_results` cap.**
   - Remove the staged anchor block (1342-1352).
   - Add `test_relay_max_results_cap` near the other through-schema pagination tests: build a `DjangoConnectionField` schema over `_make_node_type("MaxResultsNode", total_count=None)` with `strawberry_config(relay_max_results=2)` (either extend `_field_schema` with an optional `config=None` keyword defaulting to `strawberry_config()`, or build the schema inline — discretion item), then assert `{ items(first: 3) … }` surfaces an `errors` entry whose message contains `"Argument 'first' cannot be higher than 2."` (source-verified text, `strawberry/relay/utils.py:157`) and that `{ items(first: 2) … }` succeeds. First line `services.seed_data(N)` (catalog fixture rule) for the success half; the error half raises before any row math.
4. **`tests/test_relay_node_field.py` — permission integration (pre-satisfied).**
   - Remove the staged anchor block (680-686). No new tests: the three checklist properties are already pinned by the shipped Slice-2 tests cited in the DRY analysis (hidden→null at 246-258; same-query-count no-oracle at 276-297; mixed visible/hidden/missing positional nulls at 393-416; missing→null at 261-273). The anchor removal plus this citation is the slice's delivery for checklist box 3; live copies land with Slice 6 per the spec's own parenthetical (spec line 102).
5. **Validation (Worker 2):** `uv run ruff format .`; `uv run ruff check --fix .`; `git status --short` classification per BUILD.md. Focused runs, if any, use `--no-cov` explicitly (`pytest.ini` auto-applies `--cov`; coverage flags are forbidden — `--no-cov` is the only permitted coverage-shaped flag). Suggested focused scope: `uv run pytest tests/test_relay_connection.py tests/test_connection.py tests/test_relay_node_field.py examples/fakeshop/test_query/test_library_api.py --no-cov`.
6. **Checklist ticking (Worker 2):** tick each `### Spec slice checklist (verbatim)` box as its contract lands in the diff; box 3's tick cites the pre-existing Slice-2 tests + the anchor removal in the build report.

### Test additions / updates

Every spec-named matrix entry, with placement and pinning (live tests all ride the **autouse** `_reload_project_schema_for_acceptance_tests` fixture, test_library_api.py:47-50; package tests ride their files' `_isolate_global_registry` autouse fixtures):

| Matrix entry (spec lines 100, 430-435) | Live primary (root `allLibraryGenresConnection`) | Package mirror (synthesized relation, parametrized `both`/`connection`) |
| --- | --- | --- |
| `first: 0` → empty edges + pageInfo | **existing** `test_genre_connection_first_zero_empty_edges` (2264) — the pin; no new test | `test_relation_connection_first_zero` (new) |
| overrun `first: N` → actual remainder | `test_first_overrun` (new) | `test_relation_connection_first_overrun` (new) |
| stale `after` → no error ONLY (Rev 2 P1) | `test_stale_after_cursor_no_error` (new) | `test_relation_connection_stale_after_no_error` (new) |
| `first`+`last` → shipped `GraphQLError` (re-affirmed) | **existing** `test_genre_connection_first_and_last_rejected` (2238) — the pin; no new test | `test_relation_connection_first_and_last_rejected` (new) |
| `pageInfo` four-field correctness | `test_page_info_four_fields` (new) | `test_relation_connection_page_info_four_fields` (new) |
| `hasNextPage` on a `pageInfo`-only query (edges unrequested, Rev 6 P3) | `test_has_next_page_correct_when_edges_unrequested` (new) | `test_relation_connection_has_next_page_when_edges_unrequested` (new) |
| backward pagination (`last`/`before`) | `test_backward_pagination_last_before` (new) | `test_relation_connection_backward_pagination_last_before` (new) |
| `relay_max_results` cap (Edge cases line 518) | — genuinely unreachable live (fakeshop uses the default `StrawberryConfig`) | `tests/test_connection.py::test_relay_max_results_cap` (new) |

Permission integration (checklist box 3) — pre-satisfied, package-internal, all in `tests/test_relay_node_field.py` (shipped by Slice 2): hidden→null `test_node_hidden_row_returns_null`; missing→null `test_node_missing_row_returns_null`; same-queryset-path / no-existence-oracle `test_node_null_paths_issue_equal_queries` (equal query counts); mixed visible/hidden/missing positional nulls `test_nodes_preserves_input_order_with_null_holes`. Slice 4 removes the staged anchor and records the citation; live copies are Slice 6's (spec line 102 parenthetical).

Fixture/seeding rules restated for Worker 2: live + library-model package tests seed via inline `Model.objects.create` (`_seed_genres` / `_seed_library_books`; the library app has no services.py — AGENTS.md); the `tests/test_connection.py` cap test over `Category` starts with `services.seed_data(N)` (catalog rule). No temp/scratch tests are needed for development; Worker 3 may create temp probes under `docs/builder/temp-tests/slice-4/` if it wants to falsify the pageInfo-flag values against the locked Strawberry.

Coverage note: this slice adds no package source lines, so the `fail_under = 100` gate is unaffected by construction; the new tests harden already-covered shipped paths. No worker runs coverage (BUILD.md "Coverage is the maintainer's gate"); focused runs use `--no-cov`.

### Implementation discretion items

Assessed and decided as Worker 2's choice (equally valid shapes; nothing architectural):

- **The live `_genres_connection(args, selection)` mini-helper vs inlined GraphQL documents** — the existing block inlines; five new call sites would justify the helper. Either shape passes review.
- **`_field_schema(config=...)` keyword vs an inline schema build** for `test_relay_max_results_cap` — extending the helper is slightly DRYer; an inline build keeps the helper's signature stable. Either.
- **Helper function vs `@pytest.fixture` for `_shelf_books_connection_schema(shape)`**, and its exact name/seed counts/book titles.
- **Exact `pageInfo` flag values pinned by `test_backward_pagination_last_before` (and the nested twin)** — row identity is the contract; the boolean flags must be pinned at the values the locked Strawberry `0.316.0` actually produces, verified by running the focused test (`--no-cov`) during the build pass, never guessed. If the observed values contradict the Relay spec outright, stop and surface it under Notes for Worker 1 instead of pinning.
- **Placement/order of the new tests within each file's existing section structure**, and the precise wording of the updated section-header comments/docstrings (content pinned by the steps above; phrasing free).

### Notes for Worker 1 (spec reconciliation)

Two in-plan resolutions for final verification to confirm (no spec edit during planning; both are name-mapping clarifications, not contract changes):

1. **Matrix entries `first: 0` and `first`+`last` map onto shipped spec-030-era live tests.** The spec's Slice-4 test plan (line 580) names `test_first_zero` / `test_first_and_last_rejected`; the live suite already pins both contracts as `test_genre_connection_first_zero_empty_edges` / `test_genre_connection_first_and_last_rejected` (Decision 9 itself marks `first`+`last` "re-affirmed"). The plan maps rather than duplicates (DRY-first). At final verification, consider a one-line spec Test-plan edit recording the existing test names as the satisfying pins.
2. **The permission-integration triple was delivered early by Slice 2** (the spec's own Slice-2 list, lines 556/559, names the same tests the Slice-4 checklist box 3 describes). Slice 4's delivery is presence-verification + anchor removal; no new package tests. At final verification, confirm box 3's tick against this citation rather than expecting new diff lines beyond the anchor removal.

### Spec slice checklist (verbatim)

The spec's nested sub-bullets for Slice 4 from `## Slice checklist` (spec lines 100-103), copied verbatim. Worker 2 ticks each `- [x]` as it implements that sub-check during the build pass; Worker 1 audits at final verification.

- [x] A Relay-spec conformance suite pinning, against both a root [`DjangoConnectionField`][glossary-djangoconnectionfield] and a synthesized relation connection: `first: 0` → empty edges + `pageInfo`; `first: N` past the remainder → the actual remainder; an `after` cursor whose row no longer exists → the query does **not** error (the only guaranteed offset-cursor property — positional stability under inserts/deletes is NOT asserted, per the [`spec-030`][spec-030] contract and Revision 2 P1); `first` + `last` together → the shipped `GraphQLError`; `pageInfo` four-field correctness including `hasNextPage` correct on a `pageInfo`-only query (edges unrequested — the observable form of the invariant, since unrequested fields are omitted from the response); backward pagination (`last` / `before`).
- [x] **The matrix's primary copies run live** in [`examples/fakeshop/test_query/test_library_api.py`][fakeshop-test-library] against the already-shipped `allLibraryGenresConnection` (the [`test_query/README.md`][fakeshop-test-query-readme] coverage rule; no dependency on the Slice-6 activation), via the `_reload_project_schema_for_acceptance_tests` fixture. Package-internal copies remain only for the genuinely unreachable / fixture-dependent shapes: `relay_max_results` (non-default `StrawberryConfig`) and the synthesized-relation variants on cardinality fixtures.
- [x] Permission-integration tests for the root fields: `node(id:)` for a row hidden by [`get_queryset`][glossary-get_queryset-visibility-hook] returns `null` (not an error); the hidden-row and missing-row paths traverse the same queryset code path (no existence oracle); `nodes(ids:)` mixes visible / hidden / missing ids into the right `null` positions. (Live copies land with Slice 6, which activates the root fields in the example schema.)
- [x] Package coverage: extends `tests/test_relay_connection.py`, `tests/test_relay_node_field.py`, and [`tests/test_connection.py`][test-connection] per the [Test plan](#test-plan).

(The reference-style link ids above resolve in the spec document; they are preserved verbatim per the checklist-copy rule and are not live links in this scratchpad artifact.)

### Plan amendment (Worker 1, first+last guard fix)

Amendment pass, 2026-06-11, in response to Worker 2's structural-drift escalation. `Status:` reset to `planned`; Worker 2 resumes with the steps below ON TOP of its existing green diff (the implemented matrix tests stay; `test_relation_connection_first_and_last_rejected` stays in the tree unchanged as the contract pin — it goes green when the fix lands).

**Diagnosis verified independently (Worker 1).** Ran `docs/builder/temp-tests/slice-4/probe_dispatch.py` and a second SDL/guard probe: for a bare (no `total_count` opt-in) node type, `_connection_type_for` returns the generic alias `DjangoConnection[T]`; at schema build, Strawberry's generic specialization hands `ConnectionExtension` a COPIED specialized class (`strawberry.types.base` machinery) whose `resolve_connection` qualname is `ListConnection.resolve_connection` — the package override is dropped, so `first: 1, last: 1` resolves silently. A concrete subclass (`types.new_class("BareNodeConnection", (DjangoConnection[BareNode],))` + `strawberry.type`) is used as-is by the schema build: the guard fires through-schema, and the SDL is **byte-identical to today's bare-alias SDL except one line** — the inherited type description `"A connection to a list of items."`, which the fix must preserve (see step 1). Worker 2's diagnosis and suggested root-cause fix are both confirmed.

**Ruling: always-concrete `_connection_type_for`.** The bare branch generates a concrete `<TypeName>Connection` subclass of `DjangoConnection[target_type]` (no `total_count` members), via the same generation tail `_build_total_count_connection` already uses. This is the root-cause fix: the override-loss is a property of using a generic ALIAS as a schema connection type, so the cure is to never hand the schema an alias. It is also architecturally consistent with spec-030 Decision 4's "per-target concrete connection classes" and removes the dual-shape branch (one naming source, one cache shape, one dispatch story).

Alternatives weighed and rejected:

- **Guard in the synthesized resolver** — impossible cleanly: `ConnectionExtension.resolve` consumes `before/after/first/last` itself and does NOT forward them to the inner resolver; declaring them in `_synthesized_signature` would collide with the extension-added SDL arguments. Wrong layer.
- **A package `ConnectionExtension` subclass re-running the guard** — adds a second guard site, leaves `_connection_type_for`'s bare alias still silently override-dropping for any FUTURE `DjangoConnection` override (the same trap re-armed). Symptom patch; AGENTS.md forbids it over the root-cause fix.
- **Document the bare path as guard-less** — contradicts spec Decision 9's pinned contract and the shipped guard's single-sited intent. Not considered viable.

**SDL no-regress verification (done during this pass, Worker 2 re-verifies in-build):** bare-path SDL today names the specialized type `<TypeName>Connection` / `<TypeName>Edge` — exactly what the generated concrete class yields (same `graphql_type_name` source) — so connection/edge TYPE NAMES do not change for any consumer, opted or bare (spec-030 contract holds). The ONLY drift a naive `strawberry.type(generated)` introduces is dropping the bare alias's inherited description `"A connection to a list of items."`; step 1 preserves it. The shipped `totalCount`-opted `<TypeName>Connection` classes carry NO description today — the fix must NOT add one there (that would churn shipped opted SDL); the asymmetry is shipped surface, recorded as an integration-pass watch item, not changed here.

#### Implementation steps (production fix)

1. **`django_strawberry_framework/connection.py` — always-concrete `_connection_type_for`.**
   - Extract the shared generation tail as a module helper (single-sited naming + class creation), e.g.:
     `_generate_connection_class(target_type, populate=None, *, description=None)` → reads `definition = target_type.__django_strawberry_definition__`, builds `types.new_class(f"{definition.graphql_type_name}Connection", (DjangoConnection[target_type],), exec_body=populate)`, returns `strawberry.type(generated, description=description)`. (Exact name at Worker 2's discretion; keep the P1 naming comment — `graphql_type_name`, never `__name__` — on the helper, not duplicated at both call sites.)
   - `_build_total_count_connection` delegates to the helper with its existing `_populate` body and `description=None` (today's shipped opted SDL shape — no description).
   - In `_connection_type_for`, replace `connection_type = DjangoConnection[target_type]` with `connection_type = _generate_connection_class(target_type, description=DjangoConnection.__strawberry_definition__.description)` — the description is READ from the parent strawberry definition (single source, Strawberry's literal is never copied into the package), preserving the bare path's shipped SDL byte-for-byte. Caching is unchanged (same identity-keyed dict; the bare branch now caches a concrete class).
   - Update the now-false docstrings/comments: module docstring `connection.py:12-17` ("the bare ``DjangoConnection[target_type]`` when the type does not opt in" → always a generated concrete subclass; the opt-in only controls whether `total_count` members are added), `_connection_type_for` docstring (`connection.py:298-307`), and add a short WHY comment at the fix site recording the specialization-copy mechanism (generic aliases lose classmethod overrides at schema build — the Slice-4 discovered bug).
2. **`tests/test_connection.py` — re-pin the bare-branch contract.**
   - `test_connection_type_for_returns_bare_connection_without_opt_in` (≈245) and `test_connection_type_for_returns_bare_connection_when_total_count_false` (≈256): replace the `__origin__ is DjangoConnection` alias pins with the concrete-subclass contract — `issubclass(connection_type, DjangoConnection)`, `connection_type is not DjangoConnection`, `connection_type.__name__ == "<Name>Connection"`, and (unchanged) `"total_count" not in getattr(connection_type, "__annotations__", {})`. Rename/redocstring as needed ("yields a generated concrete subclass without ``total_count``").
   - `test_django_connection_is_listconnection_subclass` (≈118-125) is about the class/alias itself, NOT `_connection_type_for` — leave its `__origin__` assertion as-is.
   - Update the `_schema_for` docstring's "(bare or generated)" wording (≈94) and the stale "bare path is the generic alias" comment (≈249-251).
3. **New through-schema pins for the previously-unreachable branch (no `total_count`):**
   - `tests/test_connection.py::test_first_and_last_graphql_error_through_schema_without_opt_in` — sibling of the existing `test_first_and_last_graphql_error_through_schema` (≈410), built over `_make_node_type("BareBothArgsNode", total_count=None)`; `{ items(first: 1, last: 1) ... }` → "mutually exclusive" in `result.errors`. First line `services.seed_data(2)` (catalog rule). This is the ROOT-level pin of the fixed dispatch (the synthesized-relation pin already exists: `test_relation_connection_first_and_last_rejected`).
   - `tests/test_connection.py` — one SDL-parity assertion pinning the preserved description on the bare path, e.g. extend `test_total_count_present_only_when_opted_in` (≈265) with `assert "A connection to a list of items." in str(bare_schema)` (the load-bearing no-regress detail; an inline comment cites the Slice-4 amendment). Asserting the literal in the TEST is correct pinning — the production code still sources it from the parent definition.
   - No new live test: `GenreType` is `totalCount`-opted, so the live surface was never affected; the live matrix mapping stands unchanged.
4. **DRY notes.** The generation tail (new_class + strawberry.type + the `graphql_type_name` naming rule) becomes single-sited in the new helper — without it the fix would copy the naming line and the P1 comment into a second site. No other helper is justified. The guard literal stays single-sited in `_guard_first_and_last` (untouched). Deliberate near-twin pre-cleared for Worker 3: the new `..._through_schema_without_opt_in` test mirrors the opted sibling by design (the two dispatch shapes are exactly the contract under test).
5. **Validation (Worker 2):** `uv run ruff format .`; `uv run ruff check --fix .`; focused re-run with `--no-cov`: `uv run pytest tests/test_connection.py tests/test_relay_connection.py tests/test_relay_node_field.py examples/fakeshop/test_query/test_library_api.py --no-cov` → expect 0 failures (the two formerly-failing params go green). Tick checklist box 1 when green. Coverage note: the slice now ships source lines; every new line is reachable through the updated/added tests above by construction (the helper runs on both branches; the description read runs on the bare branch) — no pragma is needed or permitted.
6. **Discretion items (assessed, Worker 2's choice):** helper name; whether the description default is `None` or keyword-required; reading `DjangoConnection.__strawberry_definition__.description` inline at the call site vs a module-level constant (inline avoids import-order coupling and is suggested); exact renamed test names/docstrings.

### Spec changes made (Worker 1 only)

All triggered by Slice 4 (this amendment pass); glossary check re-run OK (38 terms) after the edits:

- `docs/spec-032-full_relay-0_0_9.md:5` — status line: Slice 4 marked in build with the plan-amendment note (per-spawn status re-verification; "Slices 4–7 not started" was stale).
- `docs/spec-032-full_relay-0_0_9.md:136` — Current state: the "ships the … `first`+`last` guard" claim was false as stated for bare connection types; recorded the schema-bypass discovery and the Slice-4 fix, and corrected the `_connection_type_for` description (bare alias until the fix).
- `docs/spec-032-full_relay-0_0_9.md:433` — Decision 9 `first`+`last` bullet: "(re-affirmed)" was inaccurate for bare types (the guard was never reachable there); recorded the discovered bypass mechanism and pinned the root-cause fix (always-concrete `_connection_type_for`, SDL-parity constraints).
- `docs/spec-032-full_relay-0_0_9.md:505` — Implementation-plan table row 4: added `connection.py` to the slice's files (the slice is no longer tests-only) and adjusted the test-count/diff estimates.

Spec-030 is a shipped record and is not edited; the bug is recorded where it is being fixed (the active spec).

---

## Build report (Worker 2)

**Pause note (structural drift):** `Status: revision-needed` is set by Worker 2 under the worker-2.md "Plan-vs-implementation drift / Structural drift" rule, NOT by a Worker 3 review. The plan's "tests-only slice (verified) — every behavior the conformance matrix pins is already shipped" premise is falsified for ONE matrix entry: the `first` + `last` package guard does not fire through a schema for any **bare** `DjangoConnection[T]` connection type (no `totalCount` opt-in) — root `DjangoConnectionField` and synthesized relation connections alike. The spec-mandated `test_relation_connection_first_and_last_rejected` is implemented per the plan and **fails** (both `both`/`connection` params), correctly surfacing a shipped spec-030-surface bug. The fix is a production change in `connection.py` (an architectural call); Worker 1 must revise the plan before this slice can complete. Full details under `### Notes for Worker 1 (spec reconciliation)`.

### Files touched

- `examples/fakeshop/test_query/test_library_api.py` — removed the Slice-4 `TODO(spec-032 …)` anchor block; extended the spec-030 section-header comment with the Slice-4 live-primary-matrix paragraph (maps `first: 0` / `first`+`last` onto the existing spec-030 pins); added `_genres_connection(args, selection)` helper + the five new live conformance tests (all `@pytest.mark.django_db`, riding the autouse `_reload_project_schema_for_acceptance_tests` fixture, inline `_seed_genres` seeding).
- `tests/test_relay_connection.py` — removed the Slice-4 anchor block; reworded the module docstring's stale "staged list below" sentence into the conformance-mirror rationale (cardinality fixtures the fakeshop graph lacks until Slice 6); added `_shelf_books_connection_schema(shape)` + `_books_connection(schema, args, selection)` helpers and the seven `@pytest.mark.parametrize("shape", ["both", "connection"])` matrix tests over the `Shelf.books` reverse-FK fixture.
- `tests/test_connection.py` — removed the Slice-4 anchor block; extended `_field_schema` with an optional `config=None` keyword (defaults preserved); added `test_relay_max_results_cap` after `test_connection_resolver_sync_dispatch` (first line `services.seed_data(2)` per the catalog rule; over-cap error text source-verified, at-cap success).
- `tests/test_relay_node_field.py` — removed the Slice-4 anchor block only (permission-integration contract pre-satisfied by Slice 2; see the pre-satisfied mapping below).
- `docs/builder/bld-slice-4-cursor_conformance.md` — this report + checklist ticks + status.
- `docs/builder/worker-memory/worker-2.md` — memory entry (untracked scratch).

### Tests added or updated

Live primary matrix (`examples/fakeshop/test_query/test_library_api.py`), all passing:

- `test_first_overrun` — `first: 10` over 3 rows → exactly 3 edges, `hasNextPage: false`.
- `test_stale_after_cursor_no_error` — deletes the cursor-position row; pins ONLY 200 + no `errors` (Revision 2 P1; the `_genres_connection` envelope assertions are the test).
- `test_page_info_four_fields` — page 1: `hasNextPage` true / `hasPreviousPage` false / `startCursor`/`endCursor` == first/last edge cursors; page 2 via fed-back `endCursor`: flags inverted.
- `test_has_next_page_correct_when_edges_unrequested` — `pageInfo`-only selections: `first: 2` → true, `first: 3` → false (Revision 6 P3).
- `test_backward_pagination_last_before` — `last: 2` → final two rows, `hasPreviousPage` true / `hasNextPage` false; `last: 2, before: <last row's fed-back cursor>` → the two preceding rows, both flags true (locked-Strawberry values, verified by the focused run AND source-read of `strawberry/relay/types.py::ListConnection.resolve_connection`).

Pre-satisfied live pins (mapped, NOT duplicated — the DRY-first rule): `first: 0` → existing `test_genre_connection_first_zero_empty_edges`; `first`+`last` → existing `test_genre_connection_first_and_last_rejected` (passes live because `GenreType` opts into `total_count` — see the escalation).

Package mirror (`tests/test_relay_connection.py`), parametrized `["both", "connection"]`, 12 of 14 param-cases passing:

- `test_relation_connection_first_zero` / `_first_overrun` / `_stale_after_no_error` (pins ONLY `result.errors is None`) / `_page_info_four_fields` / `_has_next_page_when_edges_unrequested` / `_backward_pagination_last_before` — all passing, both shapes.
- `test_relation_connection_first_and_last_rejected` — **FAILING (both params)**: the guard never runs (the escalation). Implemented exactly per the plan; left in the tree as the spec-contract pin awaiting the production fix.

Package remainder (`tests/test_connection.py`): `test_relay_max_results_cap` — `strawberry_config(relay_max_results=2)`; `first: 3` → `"Argument 'first' cannot be higher than 2."` in `errors`; `first: 2` → 2 edges. Passing.

Permission integration (`tests/test_relay_node_field.py`) — pre-satisfied by Slice 2, recorded per the plan's mapping: hidden→null `test_node_hidden_row_returns_null`; missing→null `test_node_missing_row_returns_null`; same-query-count no-existence-oracle `test_node_null_paths_issue_equal_queries`; mixed visible/hidden/missing positional nulls `test_nodes_preserves_input_order_with_null_holes`. Slice 4's delivery = anchor removal + this citation (checklist box 3 ticked on that basis, per the plan's "tick it if the contract IS satisfied per the plan" rule).

### Validation run

- `uv run ruff format .` — pass (reformatted only the two files carrying my new code; re-run after comma fixes: clean).
- `uv run ruff check --fix .` — pass ("All checks passed!").
- `git status --short` after both — exactly the pre-existing baseline (Slices 1–3 diffs + this build's artifacts) plus the four slice-intended test files above. No unrelated tool churn to revert. `scripts/check_trailing_commas.py --check` reports 4 remaining violations, ALL in prior slices' uncommitted diffs (`tests/test_relay_connection.py:357` from Slice 3, `tests/types/test_base.py:371/385/454` from Slice 3) — verified by line content; my own two flagged seed-list literals were fixed to the exploded trailing-comma layout. Prior slices' diffs left intact.
- Focused run (`--no-cov`): `uv run pytest tests/test_relay_connection.py tests/test_connection.py tests/test_relay_node_field.py examples/fakeshop/test_query/test_library_api.py --no-cov` → **2 failed, 172 passed** — the 2 failures are the two params of `test_relation_connection_first_and_last_rejected` (the escalation); every other new and pre-existing test passes.

### Implementation notes

- `_genres_connection(args, selection)` live helper (the plan's optional discretion item): taken — five call sites; it asserts the 200 + no-`errors` envelope so the stale-`after` test's body is just the helper call (the envelope IS the pinned property).
- `_books_connection(schema, args, selection)` package twin: same envelope-assert shape over `execute_sync`; the `first`+`last` test bypasses it (needs `result.errors`).
- `_shelf_books_connection_schema(shape)` as a plain helper (not a fixture): the `"both"` run passes NO `relation_shapes` key (conditional `meta_extra`) so the implicit-default path is the thing tested, per the plan.
- `_field_schema(config=None)` keyword (the plan's discretion item): taken over an inline build — one extra kwarg, defaults preserved for all existing callers.
- Backward-pagination `pageInfo` flags pinned at observed locked-Strawberry values: plain `last: 2` → `hasNextPage` false / `hasPreviousPage` true (the `end == sys.maxsize` branch); `last: 2, before:` → both true (overfetch sees the row after the window; slice start > 0). Verified by the focused run; consistent with the Relay spec (no contradiction to surface).
- Test naming: the live five use the spec's bare names (`test_first_overrun`, …) rather than the file's `test_genre_connection_*` prefix — the spec Test plan (line 580) and the plan's step 1 pin those exact names.
- Stale-row deletion shapes: live deletes via `models.Genre.objects.order_by("pk")[1].delete()`; package mirror deletes `books[1]` from the seeding helper's return — same second-row-in-pk-order position, no extra query.

### Notes for Worker 3

- No shadow files used beyond the plan's pre-refreshed overviews; all new code is pure test functions + three tiny test helpers.
- `docs/builder/temp-tests/slice-4/probe_dispatch.py` (untracked scratch) is the mechanism probe for the escalation — run with `uv run python docs/builder/temp-tests/slice-4/probe_dispatch.py`; it prints that Strawberry's `ConnectionExtension.connection_type` for a bare `DjangoConnection[BareNode]` field resolves to a class whose `resolve_connection` is `ListConnection.resolve_connection` (qualname-verified), so the package guard never runs through-schema.
- The deliberate live/package matrix twinning is pre-cleared by the plan as not-a-DRY-finding (Decision 9 "against both").

### Notes for Worker 1 (spec reconciliation)

- **STRUCTURAL DRIFT / shipped-bug escalation — the `first`+`last` guard is schema-bypassed for bare connection types.** `connection.py::DjangoConnection.resolve_connection` owns `_guard_first_and_last`, but when `_connection_type_for(target)` returns the **bare generic alias** `DjangoConnection[T]` (no `Meta.connection` `total_count` opt-in), Strawberry's schema generic-specialization hands `ConnectionExtension` a copied connection type whose `resolve_connection` is `ListConnection`'s — the override is lost, `first: 1, last: 1` resolves silently with ListConnection semantics. Probe-verified (`docs/builder/temp-tests/slice-4/probe_dispatch.py`) at the ROOT `DjangoConnectionField` level, so this is a spec-030-surface bug, not a Slice-3 synthesis bug. The generated `<TypeName>Connection` subclass is a concrete class and keeps the guard — which is why every pre-existing guard test passes: `tests/test_connection.py::test_first_and_last_graphql_error_through_schema` uses `total_count=True`, the direct-call tests (`test_first_and_last_raises_graphql_error`) never go through a schema, and the live `GenreType` opts into `total_count`. The bare through-schema path had zero coverage until this slice's conformance matrix — which is the suite doing exactly its job (DoD item 7). `test_relation_connection_first_and_last_rejected` is implemented per the plan and fails on both params; everything else in the slice is green (172/174). The root-cause fix is a production change (e.g. `_connection_type_for` always returning a concrete subclass so the override survives specialization — Worker 1's design call, not taken unilaterally in a tests-only slice). Checklist box 1 left unticked pending the fix; boxes 2–4 ticked (their contracts landed).
- Pre-satisfied mappings delivered as planned (the plan's two reconciliation notes): `first: 0` / `first`+`last` live pins map onto the spec-030-era `test_genre_connection_first_zero_empty_edges` / `test_genre_connection_first_and_last_rejected`; the permission-integration triple maps onto the Slice-2 tests (citations in the build report). No new near-copies added.
- Small note: `scripts/check_trailing_commas.py --check` flags 4 pre-existing layout violations in Slice-3 diff lines (`tests/test_relay_connection.py:357`, `tests/types/test_base.py:371/385/454`) — left untouched per the prior-slices-stay-intact rule; worth a sweep at integration.

---

## Build report (Worker 2, pass 2)

Pass 2 implements the `### Plan amendment (Worker 1, first+last guard fix)` on top of the intact pass-1 diff. The escalated bug is fixed at the root cause: `_connection_type_for` is now always-concrete; the two formerly-failing params of `test_relation_connection_first_and_last_rejected` pass **unchanged** (the contract pin did its job).

### Files touched

- `django_strawberry_framework/connection.py` — extracted `_generate_connection_class(target_type, populate=None, *, description=None)` as the single-sited generation tail (new_class + `strawberry.type` + the P1 `graphql_type_name` naming rationale, now living on the helper docstring only); `_build_total_count_connection` delegates with its existing `_populate` and `description=None` (opted SDL stays description-less); `_connection_type_for`'s non-opted branch now calls the helper with `description=DjangoConnection.__strawberry_definition__.description` (read inline from the parent definition — Strawberry's literal is never copied into the package), with a WHY comment recording the specialization-copy mechanism; module docstring and `_connection_type_for` docstring rewritten for the always-concrete contract (no remaining "bare alias" wording — swept, only `_synthesized_signature`'s unrelated "bare ``import``" and `_ends_in_unique_column`'s "annotation alias" remain, both about different things).
- `tests/test_connection.py` — re-pinned the two direct-call bare-branch tests to the concrete-subclass contract (renamed `test_connection_type_for_returns_concrete_subclass_without_opt_in` / `..._when_total_count_false`: `issubclass(..., DjangoConnection)`, `is not DjangoConnection`, `__name__ == "<Name>Connection"`, no `total_count` annotation); `test_django_connection_is_listconnection_subclass`'s `__origin__` assertion left as-is per the amendment (it pins the alias itself, not `_connection_type_for`); updated the `_schema_for` docstring's "(bare or generated)" wording; extended `test_total_count_present_only_when_opted_in` with the SDL description-parity assertion (`"A connection to a list of items."` in the non-opted schema, comment citing the amendment); added `test_first_and_last_graphql_error_through_schema_without_opt_in` (root-level through-schema pin, `_make_node_type("BareBothArgsNode", total_count=None)`, first line `services.seed_data(2)`).
- `docs/builder/bld-slice-4-cursor_conformance.md` — this report + checklist box 1 tick + status.
- `docs/builder/worker-memory/worker-2.md` — memory entry (untracked scratch).
- Deleted: `docs/builder/temp-tests/slice-4/` (probe disposition, below).

### Tests added or updated

- `test_first_and_last_graphql_error_through_schema_without_opt_in` (new) — the root-level fixed-dispatch pin; deliberate near-twin of the opted sibling, pre-cleared by the amendment's DRY note.
- `test_total_count_present_only_when_opted_in` (extended) — SDL description parity on the non-opted path.
- `test_connection_type_for_returns_concrete_subclass_without_opt_in` / `test_connection_type_for_returns_concrete_subclass_when_total_count_false` (re-pinned + renamed from the `..._returns_bare_connection_...` names).
- `tests/test_relay_connection.py::test_relation_connection_first_and_last_rejected` — NOT edited; now passes (both params) against the fix, exactly as the amendment required.

### Validation run

- `uv run ruff format .` — pass (241 files left unchanged after my edits settled).
- `uv run ruff check --fix .` — pass ("All checks passed!").
- `git status --short` after both — exactly the pass-1 baseline plus `connection.py`, `tests/test_connection.py`, and this artifact; no unrelated tool churn; prior slices' diffs intact. `scripts/check_trailing_commas.py --check` still reports the same 4 pre-existing Slice-3-line violations (`tests/test_relay_connection.py:357`, `tests/types/test_base.py:371/385/454`) — untouched, left for the integration pass per the pass-1 note; the fixer did not auto-touch them (only `--check` was run).
- Focused run (`--no-cov`): `uv run pytest tests/test_relay_connection.py tests/test_connection.py tests/test_relay_node_field.py tests/types/test_base.py examples/fakeshop/test_query/test_library_api.py --no-cov` → **285 passed, 0 failed**.

### Implementation notes

- Helper name `_generate_connection_class` with `populate` positional-with-default and `description` keyword-only defaulting to `None` (the amendment's discretion items): `None` default keeps the opted call site honest about "no description" while letting the bare site pass the parent's; positional `populate` mirrors `types.new_class`'s `exec_body` shape.
- Description read inline at the `_connection_type_for` call site (the amendment's suggested shape) — avoids a module-level constant's import-order coupling and keeps the single read on the only branch that needs it.
- `_build_total_count_connection` keeps a local `generated = _generate_connection_class(...)` binding (not a direct `return`): its `resolve_connection` closure dispatches via `super(generated, cls)` and needs the name bound in the enclosing scope.
- The P1 naming comment moved verbatim into the helper docstring (single-sited per the amendment); a two-line pointer comment at the opted call site records only the `description=None` asymmetry rationale.

### Probe disposition

`docs/builder/temp-tests/slice-4/probe_dispatch.py` (untracked scratch) deleted this pass: its diagnosis is now permanently pinned by `test_first_and_last_graphql_error_through_schema_without_opt_in` + `test_relation_connection_first_and_last_rejected` (the through-schema dispatch the probe demonstrated), and Worker 1's amendment records the independent verification. Nothing in it warranted promotion beyond those pins.

### Notes for Worker 3

- No shadow files used this pass; the production diff is one helper extraction + one branch rewrite, reviewable from the diff alone.
- The opted/bare description asymmetry (opted `<TypeName>Connection` ships description-less; non-opted preserves the inherited Strawberry description) is shipped surface deliberately NOT changed — the amendment records it as an integration-pass watch item, not a Slice-4 finding.
- The `..._through_schema_without_opt_in` near-twin of the opted sibling is pre-cleared by the amendment's DRY note (the two dispatch shapes are the contract under test).

### Notes for Worker 1 (spec reconciliation)

- No drift: the amendment was implemented as written (helper extraction, description sourcing from `DjangoConnection.__strawberry_definition__.description`, re-pinned direct-call tests, root-level through-schema pin, SDL description-parity assertion, docstring sweep). All discretion items recorded under Implementation notes.
- SDL no-regress re-verified in-build via the description-parity assertion plus the full focused run: connection/edge type names unchanged (`test_generated_connection_name_uses_graphql_type_name_not_python_name` and the live suite pass untouched).
- Checklist box 1 ticked this pass (the conformance matrix is fully green against both surfaces); boxes 2–4 were ticked in pass 1.

---

## Review (Worker 3)

Review pass over the combined pass-1 + pass-2 diff (the artifact's two build reports), 2026-06-11. Slice-4 files reviewed per `### Files touched`: `django_strawberry_framework/connection.py` (Slice-4 delta only; the Slice-3 `_build_relation_connection_resolver` hunk in the same cumulative diff was reviewed and accepted in `bld-slice-3-relation_shapes.md`), `examples/fakeshop/test_query/test_library_api.py`, `tests/test_relay_connection.py`, `tests/test_connection.py`, `tests/test_relay_node_field.py`.

### High:

None.

### Medium:

None.

### Low:

#### Stale "staged" sentence in `tests/test_relay_node_field.py` module docstring

`tests/test_relay_node_field.py:8-9` — the module docstring still ends "The Slice-4 permission-integration additions below are staged." That sentence described the `TODO(spec-032 ... Slice 4)` anchor block this slice removed; with the anchor gone and the contract delivered via the Slice-2 citations, the sentence is now false (nothing below is staged). The analogous docstring repair WAS done in `tests/test_relay_connection.py` (the plan's step 2 directed it there; step 4 for this file said "remove the anchor block" only, so the plan itself missed the sentence). One-line deletion/reword. Not load-bearing (severity table: stale docstring = Low).

Disposition: recorded for Worker 1's final verification (a one-line docstring edit Worker 1 can fold into final verification or route through a trivial Worker 2 touch-up alongside the integration pass's pre-existing trailing-comma sweep in the same file family). Accepting with this recorded disposition per the Slice-3 precedent (Lows with recorded dispositions).

### DRY findings

- **`_generate_connection_class` is genuinely single-sited.** `grep` confirms exactly one `types.new_class` site in `connection.py` (`_generate_connection_class`, connection.py:203); `_build_total_count_connection` delegates with `_populate` + `description=None` (connection.py:275) and `_connection_type_for`'s non-opted branch delegates with the parent-definition description read (connection.py:353-356). The P1 `graphql_type_name`-not-`__name__` naming rationale lives once, on the helper docstring. The guard literal stays single-sited in `_guard_first_and_last`. This is the DRY-improving shape the amendment pinned — verified landed.
- **Description literal never copied into production.** `grep -rn "A connection to a list of items"` over `django_strawberry_framework/` hits zero production sites; the only repo occurrence is the deliberate test pin (`tests/test_connection.py:288`), exactly the amendment's "the literal is pinned in the TEST, sourced from the parent definition in production" contract.
- **Deliberate twins, all pre-cleared, all confirmed in-bounds:** the live/package conformance-matrix twinning (Decision 9 "against both" — spec mandate, pre-cleared by the plan); `_genres_connection` (live, HTTP envelope) vs `_books_connection` (package, `execute_sync` envelope) — same shape, different harness, not consolidatable across the live/package boundary; `test_first_and_last_graphql_error_through_schema_without_opt_in` as near-twin of the opted sibling (the two dispatch shapes ARE the contract, pre-cleared by the amendment's DRY note).
- **No new named-constant candidates.** The refreshed `tests__test_relay_connection` overview's repeated literals (13x `pageInfo`, 9x `hasNextPage`, GraphQL document fragments) are the suite's established inline-document idiom — covered by the standing Slice-2 integration watch item (unhoisted GraphQL doc literals); the new tests follow the idiom rather than worsening it. `connection.py`'s repeated literals (6x `order_by`, 3x `total_count`) all predate this slice.
- **Cross-slice (Slice 3 ↔ 4):** the `_build_relation_connection_resolver` vs `_build_connection_resolver` near-copy is the already-recorded Slice-3 Low deferred to the integration pass; Slice 4's `connection.py` delta does not touch either body and adds no third near-copy. Standing item stands; nothing new.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` shows exactly the Slice-2 spec-authorized change (the `DjangoNodeField` / `DjangoNodesField` import + `__all__` entries, spec Slice-2 checklist / DoD items 3-4; accepted in `bld-slice-2-root_node_fields.md`). The Slice-4 delta to `__init__.py` is zero — no new public exports. Pass.

### CHANGELOG sanity

Not applicable; slice did not modify CHANGELOG.md. (Slice 7 owns the grant; confirmed `CHANGELOG.md` absent from `git status`.)

### Documentation / release sanity

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces. (The four `docs/spec-032-full_relay-0_0_9.md` edits in the working tree are Worker 1's own amendment-pass spec reconciliation, recorded under `### Spec changes made (Worker 1 only)` with cited lines — Worker-1-owned, not part of Worker 2's diff. Spot-checked Decision 9 line 433 and Implementation-plan row 4 against the shipped fix: accurate.)

### What looks solid

- **The production fix is the root-cause fix and is independently re-verified.** Pre-existing-claim verification per worker-3.md: with `git stash push -- django_strawberry_framework/` (package source at pristine HEAD, Slice-4 tests in place), all three guard pins FAIL — `test_first_and_last_graphql_error_through_schema_without_opt_in` plus both params of `test_relation_connection_first_and_last_rejected` — confirming the guard was schema-bypassed for bare types on BOTH the root and synthesized-relation surfaces at HEAD. Stash popped (baseline's 28 dirty entries restored); against the working tree the same tests pass. The guard is now genuinely reachable through any schema for non-opted connections.
- **The SDL no-regress claim is real, verified byte-for-byte.** Temp probe (bare node type over `Category` + `DjangoConnectionField` schema, SDL printed at HEAD-package-source vs working tree): `diff` reports byte-identical SDL — `<TypeName>Connection` / `<TypeName>Edge` names unchanged, the inherited `"A connection to a list of items."` description preserved on the bare path. Engine cross-checks: `strawberry.type` mutates and returns the SAME class (`object_type.py::_process_type` returns `cls`; `dataclasses.dataclass` mutates in place), so `_build_total_count_connection`'s `super(generated, cls)` closure remains sound through the helper extraction; the description literal source-verified at `strawberry/relay/types.py:670/744`; opted classes stay description-less (`description=None` at the opted call site — shipped SDL shape, asymmetry recorded as the integration watch item).
- **Conformance-suite spec fidelity walked entry-by-entry against Decision 9 / the Test plan:** stale-`after` pins ONLY the no-error envelope on both surfaces (live: the `_genres_connection` 200+no-`errors` envelope IS the test; package: `result.errors is None` — zero row/skip/duplicate assertions, Revision 2 P1 honored); `hasNextPage` exercised via genuinely `pageInfo`-only selections with both a true (windowed) and false (exact) page (Revision 6 P3) — and the live docstring's "neither edges nor pageInfo" wording is actually MORE engine-accurate than the spec's (see Notes for Worker 1); overrun `first` clamps with `hasNextPage: false`; backward pagination pins row identity with fed-back opaque cursors (never hand-minted, Decision 9 opacity), flags at observed locked-engine values; `relay_max_results` error text matches `strawberry/relay/utils.py::SliceMetadata.from_arguments` verbatim (source-re-verified) with the at-cap success half seeded per the catalog `services.seed_data` rule.
- **Placement rules honored:** live primaries on the autouse `_reload_project_schema_for_acceptance_tests` fixture with inline `_seed_genres` creates (library inline-create rule); package copies confined to the spec's two sanctioned families (`relay_max_results` on a non-default `StrawberryConfig`; the synthesized-relation matrix parametrized `["both", "connection"]` over the `Shelf.books` reverse-FK cardinality fixture, with the `"both"` run passing NO `relation_shapes` key so the implicit default is the thing tested) — plus the bare root through-schema guard pin, which is likewise genuinely live-unreachable (`GenreType` is `totalCount`-opted; spec row 4 as amended names it).
- **Permission-integration triple correctly mapped, not duplicated:** all four cited Slice-2 tests exist and pin exactly the checklist's three properties — hidden→null (`test_node_hidden_row_returns_null`, test_relay_node_field.py:246), missing→null (`:261`), same-path no-existence-oracle via equal `django_assert_num_queries(1)` counts (`:276`), mixed visible/hidden/missing positional nulls (`:393`) — anchor removed, no near-copies added.
- **Verbatim checklist walk: all 4 boxes ticked, no over-tick, no silent omission.** Box 1: the full matrix is green against both surfaces including the fixed guard. Box 2: live-primary + the two sanctioned package families, confirmed above. Box 3: tick rests on the pre-recorded Slice-2 mapping + anchor removal — the plan and both reconciliation notes record this delivery shape explicitly, so it is a recorded mapping, not a silent omission (Worker 1 confirms at final verification per plan note 2). Box 4: all three named package files extended (`test_relay_node_field.py`'s "extension" is the anchor removal per the same recorded mapping).
- **Anchor hygiene:** zero `TODO(spec-032 ... Slice 4)` anchors remain in any of the four files; Slice 5/6/7 anchors untouched; no stale "bare alias" / "generic alias" wording survives in `connection.py` (grep-swept).
- **Focused run re-verified:** `uv run pytest tests/test_connection.py tests/test_relay_connection.py tests/test_relay_node_field.py examples/fakeshop/test_query/test_library_api.py --no-cov` → 175 passed, 0 failed. Read-only gates re-run clean: `ruff format --check .` (241 files formatted), `ruff check .` (all checks passed). `scripts/check_trailing_commas.py --check`: the same 4 pre-existing violations Worker 2 reported, ownership re-verified by line content (test_relay_connection.py:357 sits in the Slice-3 sidecar/totalCount section above the Slice-4 block at :465; the three test_base.py lines are Slice-3 diff) — integration-pass sweep item, correctly left untouched.

### Temp test verification

- `docs/builder/temp-tests/slice-4/sdl_probe.py` (created this review pass) — printed the bare-path `DjangoConnectionField` SDL for the HEAD-vs-worktree byte comparison above. Disposition: **deleted** after the diff (its load-bearing properties are permanently pinned by `test_total_count_present_only_when_opted_in`'s description-parity assertion, `test_generated_connection_name_uses_graphql_type_name_not_python_name`, and the two concrete-subclass direct-call pins; the byte-level diff was review-time verification, not shipped behavior's only proof).
- Worker 2's `probe_dispatch.py` was already deleted in pass 2 with its disposition recorded there — confirmed gone from `docs/builder/temp-tests/`.

### review_inspect.py disposition

- `django_strawberry_framework/connection.py` — **run** (`--output-dir docs/shadow`; mandated: existing package file gaining ≥30 logic lines). Hotspot walk: `_build_total_count_connection` (66 lines / 0 branches — closure-heavy by design, unchanged semantics through the delegation); no new hotspot introduced by the Slice-4 delta. Django/ORM marker walk over the touched region (lines 178-208, 267-276, 323-358): zero markers on new lines (the delta is class generation + description plumbing, no ORM access); the file's 13 marker lines all predate the slice and were justified in prior reviews. Calls of interest on the touched region: only the pre-existing `getattr` at :231. Repeated literals (6x `order_by`, 3x `total_count`): pre-existing, not slice-introduced.
- `tests/test_relay_connection.py` — **run** (refreshed overview) for the repeated-literal DRY signal only; deep hotspot walk skipped: the slice adds pure test functions + two assertion-helper functions with no branching beyond an f-string conditional.
- `tests/test_connection.py`, `tests/test_relay_node_field.py`, `examples/fakeshop/test_query/test_library_api.py` — **skipped** with reason: pure test additions / anchor-removal-only (test_relay_node_field.py) / pure test additions following the established inline-document idiom (test_library_api.py); the plan's pass-1 refreshed overviews already carried the literal-signal walk for all four files.

### Notes for Worker 1 (spec reconciliation)

- Confirm the plan's two pre-recorded reconciliation notes at final verification (live `first: 0` / `first`+`last` name-mapping onto the spec-030-era tests — consider the one-line Test-plan edit recording the satisfying names; the permission-integration box-3 tick against the Slice-2 citations). Both delivered exactly as the plan recorded; nothing drifted.
- The Low above (stale "staged" sentence, `tests/test_relay_node_field.py:8-9`) is a one-line docstring fix to fold into final verification or the integration pass.
- Spec-text nuance, zero behavior impact: Decision 9's `pageInfo`-only bullet (spec line 434) says Strawberry "takes a distinct path when edges are absent"; the locked engine's `should_resolve_list_connection_edges` checks `{"edges", "pageInfo"}` — the distinct (skip-resolution) path is taken only when BOTH are absent, so a `pageInfo`-only selection still walks the window (which is exactly why the shipped test's true/false flags work). The live test's docstring already states the engine-accurate condition. Optional one-phrase spec polish; the pinned contract (`hasNextPage` correct on a `pageInfo`-only query) is unaffected.
- Standing integration-pass ledger after this slice (no new entries beyond the amendment's): Slice-1 2x `".Meta.interfaces entry "` prefix; the two-site fifth-guard Relay-Node wording; unhoisted GraphQL doc literals in tests; the Slice-3 relation-resolver delegation question; 2x gate-tail literal in base.py; the 4 pre-existing trailing-comma violations in Slice-3 diff lines; NEW from the amendment: the opted/bare connection description asymmetry (opted `<TypeName>Connection` ships description-less, bare preserves the inherited description — shipped surface, watch only).

### Review outcome

`review-accepted` — zero High, zero Medium; one Low with a recorded disposition (deferred to Worker 1's final verification, Slice-3 precedent); every DRY observation either landed (the helper extraction), pre-cleared (the mandated twins), or carried on the standing integration ledger. Top-level `Status:` set to `review-accepted`.

---

## Final verification (Worker 1)

Final-verification pass, 2026-06-11. Spec status-line re-verification done at spawn (line 5 was stale — "Slice 4 in build (paused …)"; updated, see below).

- **Verbatim checklist audit (4 boxes, all ticked by Worker 2 — all confirmed, no over-tick, no silent omission):**
  - Box 1 (conformance matrix against both surfaces): five new live tests confirmed in-diff (`test_first_overrun` test_library_api.py:2416, `test_stale_after_cursor_no_error` :2433, `test_page_info_four_fields` :2457, `test_has_next_page_correct_when_edges_unrequested` :2483, `test_backward_pagination_last_before` :2502) plus the two mapped spec-030-era pins (`test_genre_connection_first_and_last_rejected` :2223, `test_genre_connection_first_zero_empty_edges` :2249); seven parametrized package-mirror tests confirmed (`test_relation_connection_*`, test_relay_connection.py:509-650, both `both`/`connection` params); the amended `first`+`last` production fix confirmed (`_generate_connection_class` connection.py:178, single `types.new_class` site at :203, parent-definition description read at :355, `_build_total_count_connection` delegation, root-level pin `test_first_and_last_graphql_error_through_schema_without_opt_in` tests/test_connection.py:437, SDL description-parity assertion :288, re-pinned concrete-subclass tests :244/:262).
  - Box 2 (live primary home + sanctioned package families): live primaries ride the autouse `_reload_project_schema_for_acceptance_tests` fixture with inline `_seed_genres` creates; package copies confined to `test_relay_max_results_cap` (tests/test_connection.py:1049, non-default `StrawberryConfig`) and the synthesized-relation matrix on the `Shelf.books` cardinality fixture. Confirmed.
  - Box 3 (permission integration — pre-satisfied mapping): the four Slice-2 tests exist and pin the three checklist properties (test_relay_node_field.py:246, :261, :276, :393); the Slice-4 anchor block is removed; the tick rests on the recorded mapping per the plan's reconciliation note 2 — confirmed, not a silent omission.
  - Box 4 (package coverage extends the three named files): test_relay_connection.py + test_connection.py extended with tests; test_relay_node_field.py's extension is the anchor removal under the recorded box-3 mapping. Confirmed.
- **Anchor hygiene re-verified:** zero `TODO(spec-032 … Slice 4)` anchors remain anywhere; the surviving anchors are Slice 5 (testing/, tests/testing/) and Slice 6 (library schema + test_library_api.py:2533) — correct.
- **DRY check across Slices 1–4:** the `_generate_connection_class` consolidation is a net DRY improvement (generation tail + P1 naming rationale now single-sited; grep-confirmed one `types.new_class` site in connection.py). Standing integration-pass ledger unchanged and re-verified by occurrence count: 2x `".Meta.interfaces entry "` prefix (Slice 1), 2 executable gate-tail sites in base.py (:202/:322; the :91 mention is a comment, not a third copy), 2-site fifth-guard "Relay-Node-shaped DjangoType" wording (connection.py + relay.py), unhoisted GraphQL doc literals in tests, the Slice-3 relation-resolver delegation question, the 4 pre-existing trailing-comma violations in Slice-3 diff lines, plus the amendment's new watch item (opted/bare connection description asymmetry — shipped surface, watch only). No new duplication introduced by this slice; the deliberate live/package matrix twins and the opted/bare through-schema guard near-twins are spec-mandated and pre-cleared.
- **Focused tests:** `uv run pytest tests/test_relay_connection.py tests/test_connection.py tests/test_relay_node_field.py tests/types/test_base.py examples/fakeshop/test_query/test_library_api.py --no-cov` → **285 passed, 0 failed** (collection re-verified at 285; the live file contributes 64). No coverage flags run (maintainer's gate).
- **Worker 3's deferred Low (stale module-docstring sentence, tests/test_relay_node_field.py:8-9 "The Slice-4 permission-integration additions below are staged."):** confirmed still present and now false (the staged anchor is gone; the contract was delivered via the Slice-2 mapping). worker-1.md's Scope forbids Worker 1 editing source code or tests, so no direct fix at final verification. **Disposition: accepted deferral to the cross-slice integration pass** — a one-line reword for Worker 2, folded into the consolidation pass that already owns the same file family's trailing-comma sweep; severity Low (stale docstring, not load-bearing, BUILD.md severity table), so it does not block `final-accepted` under the Slice-3 recorded-disposition precedent. Carried on the integration ledger above.
- **Spec reconciliation:** three edits made (below), including the Worker-3-flagged Decision 9 engine-accuracy polish — the "distinct path when edges are absent" claim was materially wrong (the locked engine's `should_resolve_list_connection_edges` returns True if EITHER `edges` or `pageInfo` is selected; the skip path needs both absent), and the wrong version would mislead a future reader about why the `pageInfo`-only test works. `scripts/check_spec_glossary.py` re-run after the edits: OK (38 terms).
- **Final status: `final-accepted`.**

### Summary

Slice 4 shipped the Relay cursor-contract conformance suite (live primary matrix over `allLibraryGenresConnection` + the parametrized synthesized-relation package mirror + the `relay_max_results` cap pin), mapped the permission-integration contract onto the shipped Slice-2 tests, and — via a mid-slice plan amendment — fixed a discovered shipped spec-030-surface bug: the `first`+`last` guard was schema-bypassed for bare connection types because Strawberry's generic specialization drops classmethod overrides from `DjangoConnection[T]` aliases; `_connection_type_for` is now always-concrete via the new single-sited `_generate_connection_class` helper, with byte-identical SDL (names + inherited bare-path description) verified. All four checklist boxes confirmed; 285 focused tests pass; one Low (stale docstring) deferred to the integration pass with recorded reason.

### Spec changes made (Worker 1 only)

All triggered by Slice 4 (final-verification pass); glossary check re-run OK (38 terms):

- `docs/spec-032-full_relay-0_0_9.md:5` — status line updated to "Slices 1–4 implemented … Slices 5–7 not started" (per-spawn status re-verification; "Slice 4 in build (paused …)" was stale after the slice completed).
- `docs/spec-032-full_relay-0_0_9.md:434` — Decision 9 `pageInfo`-only bullet: corrected the materially wrong "takes a distinct path when edges are absent" to the engine-accurate condition (skip-resolution only when both `edges` and `pageInfo` are absent; a `pageInfo`-only query still walks the window) — Worker 3's flagged nuance, confirmed against the locked `strawberry/relay/utils.py::should_resolve_list_connection_edges` source.
- `docs/spec-032-full_relay-0_0_9.md:580` — Test plan Slice-4 live list: recorded the satisfying spec-030-era test names for `test_first_zero` / `test_first_and_last_rejected` (`test_genre_connection_first_zero_empty_edges` / `test_genre_connection_first_and_last_rejected` — mapped, not duplicated), closing the plan's reconciliation note 1.

Deferral record (checklist-audit rule): no checklist box remains un-ticked; the only deferred item is the non-checklist Low above (stale docstring sentence, tests/test_relay_node_field.py:8-9) → integration pass, Worker 2 one-line reword alongside the trailing-comma sweep.
