# Build: Slice 4 — Live HTTP coverage — 14 live /graphql tests + fakeshop orders + schema wiring

Spec reference: `docs/spec-028-orders-0_0_8.md` (Slice 4 checklist at the spec's `## Slice checklist` section — spec lines 124-127; Decision 8 at lines 644-695; Decision 11 at lines 809-898; Decision 13 at lines 938-955; Edge cases at lines 974-996; Implementation-plan Slice-4 row at line 966; Test plan live-HTTP list at lines 1027-1047)
Status: final-accepted

## Plan (Worker 1)

### DRY analysis

Slice 4 is the consumer-facing mirror of the shipped Filtering subsystem's fakeshop wiring (`DONE-027-0.0.8` per the existing `apps.library.filters` / `apps.library.filters_genre` / `apps.library.schema` corpus) with the substitutions Filter→Order and `filterset_class`→`orderset_class`. The order subsystem itself (`django_strawberry_framework/orders/`) is fully shipped through Slices 1-3; Slice 4 lands NOTHING under `django_strawberry_framework/` — it is a pure example-app + test-corpus slice. Every cite below uses the symbol-qualified `path::Symbol` form per `AGENTS.md` #"Source references in docs and code comments" plus inline raw `path:NN` line refs (allowed per `AGENTS.md` since this is a `bld-*.md` scratchpad).

- **Existing patterns reused (verbatim structural mirror with one substitution: Filter→Order).**
  - `examples/fakeshop/apps/library/filters.py` (entire file, lines 1-161) — the per-`DjangoType` filterset declaration shape Slice 4 mirrors with `orders.py`. Five-of-six owners declared (`BranchFilter`, `ShelfFilter`, `BookFilter`, `LoanFilter`, `PatronFilter`) — the same five owners Slice 4's `orders.py` must declare (`BranchOrder`, `ShelfOrder`, `BookOrder`, `LoanOrder`, `PatronOrder`). The sixth library `DjangoType` (`GenreType`) gets its filterset in a separate module (`filters_genre.py`) — Slice 4 mirrors this split with `orders_genre.py` (`GenreOrder`). The `MembershipCardType` is intentionally unwired on the filter side and stays unwired on the order side (per the schema.py:13-21 TODO anchor: "keep `MembershipCardType` unwired unless a live order test needs it" — no Slice-4 test names it, so it stays out).
  - `examples/fakeshop/apps/library/filters.py::BookFilter` (filters.py:75-98) — declares `shelf = RelatedFilter("ShelfFilter", field_name="shelf")` (same-module unqualified-name resolution; Layer-2 module-fallback branch), `genres = RelatedFilter("apps.library.filters_genre.GenreFilter", field_name="genres")` (cross-module absolute-import path; Layer-2 `import_string` first-attempt branch), `loans = RelatedFilter("LoanFilter", field_name="loans")`. Slice 4's `BookOrder` mirrors this verbatim — `shelf = RelatedOrder("ShelfOrder", field_name="shelf")`, `genres = RelatedOrder("apps.library.orders_genre.GenreOrder", field_name="genres")`, `loans = RelatedOrder("LoanOrder", field_name="loans")` — so both Layer-2 lazy-resolution branches are exercised end to end on the order side. The `genres` declaration's absolute-import path is the load-bearing fixture for Test 5 (M2M absolute-import-path).
  - `examples/fakeshop/apps/library/filters.py::BranchFilter` (filters.py:42-57) — declares `shelves = RelatedFilter("ShelfFilter", field_name="shelves", queryset=models.Shelf.objects.filter(topic="permanent collection"))`. **The order side drops the `queryset=` parameter** (Spec Decision 8 final paragraph: "the cookbook's `RelatedOrder` accepts only `orderset` and `field_name`"; `RelatedOrder` has no `queryset` kwarg per Spec Decision 2 + Decision 8 step 4 second paragraph). Slice 4's `BranchOrder.shelves` is `RelatedOrder("ShelfOrder", field_name="shelves")` — same two args, no queryset constraint. Test 4 (reverse-FK multiplicity) and Test 12 (active-related-branch permission gate) both target `BranchOrder.shelves`.
  - `examples/fakeshop/apps/library/filters.py::ShelfFilter` (filters.py:60-72) — declares `branch = RelatedFilter("BranchFilter", field_name="branch")` and `books = RelatedFilter("BookFilter", field_name="books")`. Slice 4's `ShelfOrder` mirrors this with `branch = RelatedOrder("BranchOrder", field_name="branch")` and `books = RelatedOrder("BookOrder", field_name="books")` so multi-owner reuse (`ShelfOrder` is targeted by `BranchOrder.shelves` AND by `BookOrder.shelf`) exercises the Slice-3 Axis-2 related-target-agreement check end-to-end.
  - `examples/fakeshop/apps/library/filters.py::LoanFilter` (filters.py:101-109) — declares `book = RelatedFilter("BookFilter", field_name="book")` and `patron = RelatedFilter("PatronFilter", field_name="patron")`. Slice 4's `LoanOrder` mirrors this verbatim.
  - `examples/fakeshop/apps/library/filters.py::PatronFilter` (filters.py:112-151) — declares `loans = RelatedFilter("LoanFilter", field_name="loans")` PLUS the spec-021 H4-rev8 `email_must_have_at_sign` custom-filter validator. **The order side has NO equivalent custom-validator surface** — the cookbook's `AdvancedOrderSet` does not use forms and has no validator concept (Spec Decision 8 Justification bullet 2: "no form validation (no `BaseFilterSet.form.is_valid()` step — the cookbook's `AdvancedOrderSet` doesn't use forms)"). Slice 4's `PatronOrder` is therefore SIMPLER than `PatronFilter`: `loans = RelatedOrder("LoanOrder", field_name="loans")` + `class Meta: model = models.Patron; fields = ["id", "name"]` — no custom field, no `__init__` override.
  - `examples/fakeshop/apps/library/filters_genre.py` (entire file, lines 1-34) — the cross-module Layer-2 absolute-import fixture Slice 4 mirrors with `orders_genre.py`. `GenreFilter` declares `books = RelatedFilter("apps.library.filters.BookFilter", field_name="books")` — the cross-module-pointing-back-to-the-main-orders-module variant. Slice 4's `GenreOrder` mirrors this verbatim: `books = RelatedOrder("apps.library.orders.BookOrder", field_name="books")` so the absolute-import-path Layer-2 branch is exercised in BOTH directions (`BookOrder.genres` points to `orders_genre.GenreOrder`; `GenreOrder.books` points back to `orders.BookOrder`).
  - `examples/fakeshop/apps/library/schema.py` (entire file, lines 1-274) — the `DjangoType` + root-resolver corpus Slice 4 extends. `LoanType.Meta.filterset_class = filters.LoanFilter` at schema.py:59 is the per-type wiring template Slice 4 mirrors with `Meta.orderset_class = orders.LoanOrder` etc. Five of six library `DjangoType`s carry `filterset_class` today (`LoanType`/`BookType`/`ShelfType`/`GenreType`/`BranchType`/`PatronType`); the same five gain `orderset_class`. `MembershipCardType` (schema.py:111-116) stays unwired on both sides.
  - `examples/fakeshop/apps/library/schema.py::Query` (schema.py:178-272) — the root-resolver corpus Slice 4 extends. The six in-scope root resolvers (`all_library_branches` at schema.py:199, `all_library_shelves` at schema.py:210, `all_library_books` at schema.py:221, `all_library_genres` at schema.py:236, `all_library_patrons` at schema.py:247, `all_library_loans` at schema.py:262) all share the same shape: `def all_library_<Xs>(self, info: strawberry.Info, filter: filter_input_type(filters.<X>Filter) | None = None) -> list[<X>Type]: queryset = <X>Type.get_queryset(models.<X>.objects.order_by("id"), info); if filter is not None: queryset = filters.<X>Filter.apply_sync(filter, queryset, info); return queryset`. Slice 4 extends each to: `def all_library_<Xs>(self, info: strawberry.Info, filter: filter_input_type(filters.<X>Filter) | None = None, order_by: list[order_input_type(orders.<X>Order)] | None = None) -> list[<X>Type]: queryset = <X>Type.get_queryset(models.<X>.objects.order_by("id"), info); if filter is not None: queryset = filters.<X>Filter.apply_sync(filter, queryset, info); if order_by is not None: queryset = orders.<X>Order.apply_sync(order_by, queryset, info); return queryset`. The visibility→narrow→arrange chain matches Spec Decision 8 step ordering verbatim. `all_library_prefetched_books` (schema.py:233) and `all_library_membership_cards` (schema.py:259) stay unwired (no filter today, no order added — neither feeds a Slice-4 test). The `DjangoListField` resolvers (schema.py:190-197) stay unwired per the Spec Non-goals "`DjangoListField` orderBy-argument integration deferred to `0.0.9`" + the schema.py:182-188 TODO anchor.
  - `examples/fakeshop/apps/library/schema.py::BranchType.get_queryset` (schema.py:137-150) — the existing visibility hook hiding `city="restricted"` for anonymous users. Test 9 (root `get_queryset` honoring) reuses this hook verbatim — the test seeds one `city="Boston"` row and one `city="restricted"` row and asserts that anonymous `orderBy: [{ name: DESC }]` sees ONLY the `city="Boston"` row. Test 8 (filter+order composition + optimizer cooperation) ALSO reuses this hook for the staff-vs-anonymous halves where applicable.
  - `examples/fakeshop/apps/library/schema.py::ShelfType.get_queryset` (schema.py:83-97) — the existing visibility hook hiding `topic="secret"`. Not exercised directly by Slice 4 tests but stays unchanged (Slice 4 must not break the shipped filter-side test `test_nested_related_filter_honors_target_get_queryset` at test_library_api.py:1108).
  - `examples/fakeshop/test_query/test_library_api.py` (entire file, lines 1-1309) — the live-HTTP test corpus Slice 4 appends to. Reuse the shipped helpers verbatim:
    - `_reload_project_schema_for_acceptance_tests` autouse fixture (test_library_api.py:47-50) — fires per Slice-4 test; Slice 4's order binding runs through finalizer phase 2.5 on the reload, so the fixture continues to work unchanged.
    - `_post_graphql(query, *, client=None)` helper (test_library_api.py:76-82) — anonymous POST. Used by every Slice-4 test.
    - `_post_graphql_as_staff(query)` helper (test_library_api.py:676-687) — staff POST. Used by Slice-4 Tests 9, 10, 11, 12 (the four permission/visibility tests) for the staff-pass halves where appropriate.
    - `_assert_graphql_data(query, expected)` helper (test_library_api.py:85-89) — exact-match data assertion. Used by Slice-4 Tests 1, 3, 5, 7, 13 (the exact-order assertion tests).
    - `_seed_library_graph()` helper (test_library_api.py:53-67) — the canonical one-of-each-model seed. Slice 4 tests that need only a single ordered scalar list can call this directly; tests that need specific orderings declare their own per-test inline seeds (matching the existing filter-side test pattern at e.g. test_library_api.py:692-694 for `test_library_branches_filter_by_name_icontains`).
    - `_seed_branch_with_two_shelves(name="Override")` (test_library_api.py:70-73) — already-shipped multi-shelf seed. Slice-4 Test 4 (reverse-FK multiplicity) extends this pattern with a fresh `_seed_branches_with_varying_shelves()` helper (see "New helpers justified" below) that seeds a multi-shelf Alpha + a single-shelf Beta in one call.
    - `CaptureQueriesContext(connection)` from `django.db` (used by `test_library_books_filter_preserves_optimizer_cooperation` at test_library_api.py:1020) — Slice-4 Test 8 (optimizer cooperation) reuses this pattern verbatim with the new `orderBy:` argument added.
  - `examples/fakeshop/test_query/test_library_api.py::test_library_books_filter_by_choice_enum` (test_library_api.py:766-791) — the shipped reference for the lower-case `available` enum literal. Slice-4 Test 7 (filter+order composition) uses the same `circulationStatus: { exact: available }` shape and Spec Revision 4 H4 explicitly licenses this casing.
  - `examples/fakeshop/test_query/test_library_api.py::test_library_books_filter_preserves_optimizer_cooperation` (test_library_api.py:1001-1049) — the shipped reference for `assertNumQueries`-style assertion via `CaptureQueriesContext`. Slice-4 Test 8 mirrors this pattern (3 expected queries: root SELECT + `select_related("shelf")` JOIN + `prefetch_related("genres")` SELECT) with the added `orderBy: [{ title: ASC }]` argument.
  - `examples/fakeshop/test_query/test_library_api.py::test_root_get_queryset_runs_before_filter_apply` (test_library_api.py:1228-1265) — the shipped reference for "root `get_queryset` runs before X.apply" pattern. Slice-4 Test 9 mirrors this verbatim with `orderBy:` instead of `filter:`.
  - `examples/fakeshop/test_query/test_library_api.py::test_apply_raises_graphqlerror_on_invalid_filter_input` (test_library_api.py:1176-1199) — the shipped reference for "GraphQLError-with-extensions surfaces in `payload["errors"]`" pattern. Slice-4 Tests 10, 11, 12 reuse the `payload["errors"][0]["extensions"]["code"]` assertion shape with the order-side extension code `"ORDER_PERMISSION_DENIED"` (named in Spec test plan lines 1039-1041).

- **New helpers justified.** Exactly TWO new fakeshop seed helpers; one fresh fixture-style permission-mode toggle; one cross-test SQL-substring helper. None are required to land in slice 4 if Worker 2 prefers to inline them — but inlining at five sites of a five-test seed pattern is the duplication risk the planning pass exists to surface.
  - `examples/fakeshop/test_query/test_library_api.py::_seed_branches_with_varying_shelves()` (NEW; module-level helper). Single responsibility: seed one `Branch(name="Alpha", city="Boston")` with three shelves (`Shelf(code="A")`, `Shelf(code="C")`, `Shelf(code="E")`) AND one `Branch(name="Beta", city="Boston")` with one shelf (`Shelf(code="B")`). Returns nothing; tests query the live schema and assert against the response shape. Used by Slice-4 Test 4 (reverse-FK multiplicity) and may be reused by Test 12 (active-related-branch permission gate) if Worker 2 wants the same shape. **Why justified:** Test 4's denormalized multiplicity assertion is the load-bearing seed shape per Spec Revision 4 M5; a typo in the seed body (e.g., one extra shelf, mis-ordered codes) would silently flip the assertion meaning. A named helper at the top of the file makes the seed shape inspectable in one place.
  - `examples/fakeshop/test_query/test_library_api.py::_seed_books_with_nullable_subtitles()` (NEW; module-level helper). Single responsibility: seed at least one `Book(subtitle=None)` row AND at least one `Book(subtitle="A Short Subtitle")` row plus their owning `Branch` + `Shelf` per Spec Revision 4 B3. Used by Slice-4 Test 2 (NULLS positioning). **Why justified:** the NULLS-positioning contract is the only Slice-4 test that turns on row-content ordering of one specific field; an inline seed body would diffuse the contract. **Alternative considered:** Worker 2 may inline this if it stays under ~6 lines AND the test name carries the seed shape in its docstring — Worker 1 accepts either choice at Worker 2's discretion (see `### Implementation discretion items`).
  - **NOT a new helper:** the `BranchOrder.check_name_permission(request)` / `BranchOrder.check_shelves_permission(request)` gates are declared INSIDE `orders.py` as ordinary `OrderSet` per-field / per-branch `check_*_permission` methods. They are NOT helpers and live with their owning `OrderSet`. The gate body for both is the standard "raise `GraphQLError('staff only', extensions={'code': 'ORDER_PERMISSION_DENIED'})` for non-staff users; return None for staff users" pattern; the `request` argument carries the user via `getattr(request, "user", None)` per the same pattern `BranchType.get_queryset` uses at schema.py:145-150. **Worker 2 owns the precise gate-body wording** within these guardrails.

- **Duplication risk avoided (six risks named explicitly).**
  - **Risk: copy-pasting the entire test_library_api.py filter-side test bodies into Slice-4 tests.** Naive implementation would copy `test_library_branches_filter_by_name_icontains` (test_library_api.py:689-704), swap `filter:` → `orderBy:`, and produce 14 near-identical bodies. **Avoidance:** Slice 4 reuses the shipped helpers (`_post_graphql`, `_assert_graphql_data`, `_post_graphql_as_staff`, `CaptureQueriesContext`, `_reload_project_schema_for_acceptance_tests`) verbatim. Tests differ ONLY in (a) the GraphQL query body, (b) the seed shape, (c) the assertion shape. The shipped pattern at test_library_api.py:1001-1049 (CaptureQueriesContext + `assert response.status_code == 200` + `payload = response.json()` + `assert "errors" not in payload` + content assertions) IS the template; Worker 2 follows it verbatim per test.
  - **Risk: re-declaring the same `BookOrder.Meta.fields` shape in two different forms across tests.** Slice-4 Test 13 (flat-shorthand `shelfCode`) requires `BookOrder.Meta.fields = ["shelf__code"]`. Every OTHER Slice-4 `BookOrder`-related test (Tests 2, 3, 5, 7, 8, 14a) requires the full `BookOrder.Meta.fields` set including `subtitle`, `title`, `circulation_status`, and a same-module `RelatedOrder("ShelfOrder")` for nested-shape ordering. **A naive implementation would either (a) ship two parallel `BookOrder` classes, or (b) make `Meta.fields` a union which would render BOTH `shelfCode: Ordering` AND `shelf: ShelfOrderInputType` and confuse the consumer.** **Avoidance:** `BookOrder.Meta.fields` carries `["id", "title", "subtitle", "circulation_status", "shelf__code"]` (note the double-underscore shorthand for `shelf__code`) AND the explicit `RelatedOrder("ShelfOrder", field_name="shelf")` declaration which OVERRIDES the `shelf__code` flat-shorthand per Spec Decision 5 + the column-overrides-by-same-name-RelatedOrder contract from Spec Edge case "`Meta.fields = '__all__'`" final sentence. The actual rendered GraphQL surface: `shelf: ShelfOrderInputType` (nested-shape — wins over the flat shorthand because `RelatedOrder("ShelfOrder", field_name="shelf")` overrides the same Python-attr-name on the OrderSet) AND `shelfCode: Ordering` (flat-shorthand surface from the explicit `"shelf__code"` field in `Meta.fields` — note: `"shelf__code"` and `"shelf"` are DIFFERENT field-spec entries, and `"shelf__code"` produces a `shelfCode: Ordering` leaf via path-rendering per Spec Edge case `Meta.fields = ["shelf__code"]`). **Worker 2 must verify (potentially via a Slice-2/3 test reading) that both surfaces coexist on the same `OrderSet` without collision — if they do collide, Worker 2 escalates to Worker 1 under `### Notes for Worker 1 (spec reconciliation)`.** **The safer alternative Worker 1 prefers:** ship `BookOrder.Meta.fields = ["id", "title", "subtitle", "circulation_status", "shelf__code"]` (no `"shelf"` column leaf in the list) PLUS the explicit `RelatedOrder("ShelfOrder", field_name="shelf")` — the column-list does NOT include `"shelf"` so the only `shelf:` surface on the input type is the nested `ShelfOrderInputType`, AND the path-shorthand `"shelf__code"` produces the `shelfCode: Ordering` leaf for Test 13. This is the layout Worker 2 should ship; Worker 1 has assessed it and pins it here.
  - **Risk: re-declaring the same `Meta.fields` shape across `orders.py` and the shipped `filters.py`.** Naive implementation would import the filter side's `Meta.fields` dict-of-lists shape (`{"id": ["exact", "in"], "name": ["exact", "icontains"]}`) into the order side. **Avoidance:** the cookbook's `OrderSet.Meta.fields` accepts a LIST of column names (`["id", "name"]`) OR the string `"__all__"` per Spec Decision 3 — NOT a dict-of-lookups (ordering has no lookups; direction is the only modifier). Worker 2 ships `BranchOrder.Meta.fields = ["id", "name", "city"]` etc. The list shape is intentionally different from `BranchFilter.Meta.fields = {"id": ["exact", "in"], ...}`. **Worker 3 should flag any dict-shaped `Meta.fields` on an OrderSet as a High finding** — the dict shape is filter-side syntax.
  - **Risk: re-using the filter side's `Meta.model = models.Branch` import path with a different absolute-module-path style.** Naive implementation would import `from apps.library import models as library_models` in `orders.py` while `filters.py` imports `from apps.library import models`. **Avoidance:** Slice 4 mirrors the filter side's import shape verbatim. The top of `orders.py`: `from __future__ import annotations` + (blank line) + `from apps.library import models` + `from django_strawberry_framework.orders import OrderSet, RelatedOrder` (mirrors filters.py:18-26 line-by-line with the substitution `filters` → `orders` and `FilterSet, RelatedFilter` → `OrderSet, RelatedOrder`).
  - **Risk: Test 12 (active-related-branch permission) and Test 10/11 (active-input-only scalar permission) declaring the same `check_*_permission` gates twice on `BranchOrder`.** **Avoidance:** Both Tests 10/11 (scalar `check_name_permission`) AND Test 12 (relation-level `check_shelves_permission`) live on the SAME `BranchOrder` class. The two gates fire under different inputs per Spec H3-rev3 active-branch dispatch + Spec M6-rev1 active-input-only scope: Test 10's input `orderBy: [{ name: ASC }]` fires `check_name_permission` only; Test 11's input `orderBy: [{ city: ASC }]` fires NEITHER; Test 12's input `orderBy: [{ shelves: { code: ASC } }]` fires `check_shelves_permission` only; Test 12's second-half input `orderBy: [{ name: ASC }]` fires `check_name_permission` only (so Test 12 second half ALSO needs staff context, OR the test must declare the gates' parent class differently). **Worker 1 has assessed this:** Test 12's second-half input MUST be `orderBy: [{ city: ASC }]` (the unguarded field) to be quiet against `check_shelves_permission` AND `check_name_permission` together. Worker 2 ships Test 12 with `city: ASC` in the second half. **Re-confirmed:** the Spec test-plan line 1041 says "Re-issue `{ allLibraryBranches(orderBy: [{ name: ASC }]) { id } }` (the `shelves` branch is absent); assert no error AND a successful ordered response" — BUT this conflicts with Test 10's `check_name_permission` firing on the same input. **Worker 1's planning-pass resolution:** Test 12's second half uses `orderBy: [{ city: ASC }]` instead (no gated field, no gated branch). **This is a spec wording gap; Worker 1 will record this under `### Notes for Worker 1 (spec reconciliation)` and either edit the spec text at final verification OR leave as Worker-2-discretion if the spec author's intent allows.** See `### Notes for Worker 1 (spec reconciliation)` below for the exact wording.
  - **Risk: collapsing the `_seed_branches_with_varying_shelves` helper into the existing `_seed_branch_with_two_shelves` helper.** **Avoidance:** the existing helper at test_library_api.py:70-73 seeds two shelves per branch with `code="A-1"` and `code="B-2"`; Test 4's multiplicity-assertion requires three shelves with `code="A"`, `code="C"`, `code="E"` PLUS a single-shelf Beta with `code="B"`. The two seed shapes diverge on shelf-count AND shelf-code form. Worker 2 ships them as TWO separate helpers (the existing one stays unchanged; the new one is the Slice-4 addition).

- **`scripts/review_inspect.py` planning-time disposition (record per `BUILD.md`).** Ran the helper on the **current** files Slice 4 will modify on 2026-06-01: `examples/fakeshop/apps/library/schema.py` (274 lines) and `examples/fakeshop/test_query/test_library_api.py` (1309 lines). Both files are over the 150-line trigger; `schema.py` is also under the broad fakeshop-app live-coverage path so the helper run is required by BUILD.md "When to run the helper during build".
  - **`schema.py` shadow scan.** 27 symbols, no control-flow hotspots; 2x `"is_staff"` repeated string literals (in `BranchType.get_queryset` + `ShelfType.get_queryset`). Slice 4 adds: (1) the `from apps.library import orders, orders_genre` import (one new line under the existing `from apps.library import filters, filters_genre, models` at schema.py:9); (2) the `from django_strawberry_framework.orders import order_input_type` import (one new line under the existing `from django_strawberry_framework.filters import filter_input_type` at schema.py:11); (3) `Meta.orderset_class = orders.<X>Order` on five DjangoType classes (5 added lines total); (4) the `order_by:` argument + `if order_by is not None:` block on six root resolvers (six resolvers × ~3 added lines = ~18 added lines); (5) removal of the two TODO anchors at schema.py:13-21 and schema.py:182-188. Estimated post-Slice-4 schema.py line count: ~310 source lines, still no hotspots. No new repeated-literal candidates.
  - **`test_library_api.py` shadow scan.** 12 imports, 56 symbols. The top repeated-string literals are: `"allLibraryBooks"` (13x), `"Speculative"` (8x), `"allLibraryBranches"` (8x), `"Foundation"` (8x), `"library_shelf"` (7x), `"GenreType"` (6x), `"Hyperion"` (6x), `"Andromeda Main"` (5x), `"Cambridge"` (5x). Slice 4 adds 14 new test functions plus 2 new module-level helpers (`_seed_branches_with_varying_shelves`, `_seed_books_with_nullable_subtitles`). Each test will reuse `allLibraryBranches` / `allLibraryBooks` so those counts will grow further (estimated +10 occurrences of `"allLibraryBranches"` and +6 of `"allLibraryBooks"`). **Not a consolidation candidate** — these are inline GraphQL query strings; the test corpus's hardcoded query strings are intentional per the "Live GraphQL HTTP tests" pattern, and consolidating into a `_query_template_format(...)` helper would obscure the actual GraphQL surface under test. Estimated post-Slice-4 test_library_api.py line count: ~1700-1800 source lines (14 tests × ~25-40 lines each + 2 helpers + the test docstrings). Worker 3's review-time helper trigger fires (file is >150 lines AND >50 added lines outside `django_strawberry_framework/`).
  - **New files NOT triggering the helper.** `examples/fakeshop/apps/library/orders.py` and `orders_genre.py` are NEW files containing ONLY `class <X>Order(OrderSet)` declarations (no functions, no module-level logic apart from `__all__` tuple and a per-class docstring). Per BUILD.md "Worker 3 must run the helper during review when ... unless it is a pure-class-definition module (only `class` declarations with docstrings, no logic)", these files DO NOT trigger the helper. Worker 1 records the skip-and-reason here per BUILD.md.

### Implementation steps

Slice 4 lands four file additions/edits, all under `examples/fakeshop/`. NOTHING under `django_strawberry_framework/` is touched. Line anchors below are pin-at-write-time hints per `BUILD.md` Implementation steps note; Worker 2 verifies against the live source before editing.

1. **Create `examples/fakeshop/apps/library/orders.py`** (new file). Pure-class-definition module mirroring `examples/fakeshop/apps/library/filters.py` one-for-one with the Filter→Order substitution.
   - Module docstring at file top: mirrors filters.py:1-16 with the substitution Filter→Order. Suggested text: `"""OrderSet declarations for the library acceptance app (Slice 4).\n\nFive ordersets mirror the relation shape ``apps.library.schema`` exposes\nthrough the live ``/graphql/`` endpoint. Inter-orderset references use\nthe same-module unqualified-name form (e.g. ``RelatedOrder("ShelfOrder")``)\nso the lazy-resolution Layer-2 prefix-with-owner branch is exercised end\nto end; the ``BookOrder.genres = RelatedOrder("apps.library.orders_genre.GenreOrder")``\ndeclaration deliberately uses the absolute-import-path form so the\nLayer-2 ``import_string`` first-attempt branch is also exercised\n(spec-028 Slice 4 + Decision 11).\n\n``GenreOrder`` lives in the sibling ``orders_genre.py`` module so the\nabsolute-import-path resolution path has a real cross-module target;\nboth branches of the Layer-2 fallback are visible from the fakeshop\norder graph.\n"""`.
   - Imports (mirrors filters.py:18-26 with substitution): `from __future__ import annotations` + (blank line) + `from typing import Any` (only if the `check_*_permission` bodies need `Any`-typed `request` — Worker 2's discretion) + (blank line) + `from graphql import GraphQLError` (load-bearing — every `check_*_permission` raises this exact class per Spec Decision 8 second-paragraph "`GraphQLError` import path"; do NOT use `strawberry.exceptions.StrawberryGraphQLError`) + (blank line) + `from apps.library import models` + `from django_strawberry_framework.orders import OrderSet, RelatedOrder` (mirrors the `FilterSet, RelatedFilter` import shape).
   - **`BranchOrder` class** (mirrors `BranchFilter` at filters.py:42-57 + adds two `check_*_permission` gates per Slice-4 Tests 10/11/12):
     ```python
     class BranchOrder(OrderSet):
         """Branch orderset bound to ``BranchType`` at finalize phase 2.5.

         Carries two ``check_*_permission`` gates load-bearing for the
         Slice-4 active-input-only / active-related-branch coverage tests
         (spec-028 Slice 4 Tests 10, 11, 12 per Spec test plan lines
         1039-1041). The gates raise ``GraphQLError`` with the explicit
         ``code="ORDER_PERMISSION_DENIED"`` extension code so the live
         HTTP tests can assert the extension-code value verbatim.
         """

         shelves = RelatedOrder("ShelfOrder", field_name="shelves")

         class Meta:
             model = models.Branch
             fields = ["id", "name", "city"]

         @classmethod
         def check_name_permission(cls, request: Any) -> None:
             """Active-input-only scalar gate fired by Test 10 (denies) + quiet for Test 11.

             Spec-028 M6-rev1 split-pair: the gate fires ONLY when the
             consumer's input names ``name`` (Test 10's input is
             ``orderBy: [{ name: ASC }]``); the input ``orderBy: [{ city:
             ASC }]`` (Test 11) does NOT fire this gate.
             """
             user = getattr(request, "user", None)
             if user is None or not getattr(user, "is_staff", False):
                 raise GraphQLError(
                     "staff only",
                     extensions={"code": "ORDER_PERMISSION_DENIED"},
                 )

         @classmethod
         def check_shelves_permission(cls, request: Any) -> None:
             """Active-related-branch gate fired by Test 12 (denies).

             Spec-028 H3-rev3 active-branch dispatch: the gate fires ONLY
             when the consumer's input names the ``shelves`` RelatedOrder
             branch (Test 12 first-half input ``orderBy: [{ shelves: {
             code: ASC } }]``). Test 12's second-half input (a non-
             ``shelves``, non-``name`` field — see ``### Notes for Worker
             1 (spec reconciliation)``) does NOT fire this gate.
             """
             user = getattr(request, "user", None)
             if user is None or not getattr(user, "is_staff", False):
                 raise GraphQLError(
                     "hidden shelves",
                     extensions={"code": "ORDER_PERMISSION_DENIED"},
                 )
     ```
   - **`ShelfOrder` class** (mirrors `ShelfFilter` at filters.py:60-72; no permission gates needed):
     ```python
     class ShelfOrder(OrderSet):
         """Shelf orderset bound to ``ShelfType`` at finalize phase 2.5."""

         branch = RelatedOrder("BranchOrder", field_name="branch")
         books = RelatedOrder("BookOrder", field_name="books")

         class Meta:
             model = models.Shelf
             fields = ["id", "code", "topic"]
     ```
   - **`BookOrder` class** (mirrors `BookFilter` at filters.py:75-98; `genres` uses absolute-import path per Slice 4 test 5):
     ```python
     class BookOrder(OrderSet):
         """Book orderset bound to ``BookType`` at finalize phase 2.5.

         ``BookOrder.genres`` uses the absolute-import-path form
         ``"apps.library.orders_genre.GenreOrder"`` so the Layer-2
         ``import_string`` first-attempt branch resolves cross-module per
         spec-028 Slice 4 Test 5 (M2M absolute-import-path).

         ``BookOrder.Meta.fields`` carries the path-shorthand
         ``"shelf__code"`` which renders as ``shelfCode: Ordering`` on the
         input type per spec-028 Slice 4 Test 13 (flat-shorthand path).
         The explicit ``shelf = RelatedOrder("ShelfOrder", field_name=
         "shelf")`` declaration produces the nested-shape ``shelf:
         ShelfOrderInputType`` surface used by Tests 3, 7, 8, 13 multi-
         field priority. Both surfaces coexist on the same input type.
         """

         shelf = RelatedOrder("ShelfOrder", field_name="shelf")
         genres = RelatedOrder(
             "apps.library.orders_genre.GenreOrder",
             field_name="genres",
         )
         loans = RelatedOrder("LoanOrder", field_name="loans")

         class Meta:
             model = models.Book
             fields = ["id", "title", "subtitle", "circulation_status", "shelf__code"]
     ```
   - **`LoanOrder` class** (mirrors `LoanFilter` at filters.py:101-109):
     ```python
     class LoanOrder(OrderSet):
         """Loan orderset bound to ``LoanType`` at finalize phase 2.5."""

         book = RelatedOrder("BookOrder", field_name="book")
         patron = RelatedOrder("PatronOrder", field_name="patron")

         class Meta:
             model = models.Loan
             fields = ["id", "note"]
     ```
   - **`PatronOrder` class** (mirrors `PatronFilter` at filters.py:112-151 MINUS the custom-validator surface; the cookbook's `AdvancedOrderSet` has no form/validator concept per Spec Decision 8 Justification bullet 2):
     ```python
     class PatronOrder(OrderSet):
         """Patron orderset bound to ``PatronType`` at finalize phase 2.5."""

         loans = RelatedOrder("LoanOrder", field_name="loans")

         class Meta:
             model = models.Patron
             fields = ["id", "name"]
     ```
   - **`__all__` tuple** at file bottom (mirrors filters.py:154-160 alphabetic order):
     ```python
     __all__ = (
         "BookOrder",
         "BranchOrder",
         "LoanOrder",
         "PatronOrder",
         "ShelfOrder",
     )
     ```

2. **Create `examples/fakeshop/apps/library/orders_genre.py`** (new file). Cross-module fixture mirror of `filters_genre.py` one-for-one.
   - Module docstring (mirrors filters_genre.py:1-9): `"""Cross-module fixture for the absolute-import-path ``RelatedOrder`` (Slice 4).\n\n``GenreOrder`` lives in its own module so the\n``BookOrder.genres = RelatedOrder("apps.library.orders_genre.GenreOrder")``\ndeclaration in ``orders.py`` exercises Layer-2 absolute-import-path\nresolution per spec-028 Slice 4 Test 5. The single same-module unqualified-\nname branch is exercised by every other ``RelatedOrder("XOrder")``\ndeclaration in ``orders.py``.\n"""`.
   - Imports (mirrors filters_genre.py:11-14): `from __future__ import annotations` + (blank line) + `from apps.library import models` + `from django_strawberry_framework.orders import OrderSet, RelatedOrder`.
   - **`GenreOrder` class** (mirrors `GenreFilter` at filters_genre.py:17-30; `books` points back to `orders.BookOrder` via absolute-import path so the cross-module-pointing-back branch is exercised):
     ```python
     class GenreOrder(OrderSet):
         """Genre orderset bound to ``GenreType`` at finalize phase 2.5.

         ``GenreType`` declares ``Meta.interfaces = (relay.Node,)`` — per
         spec-028 Decision 8 + Edge case "``Meta.orderset_class`` on a
         ``DjangoType`` that also declares ``Meta.interfaces = (relay.Node,)``",
         the ``Ordering`` enum's leaf type does NOT depend on Relay shape;
         ``id`` orders by the column, not the GraphQL ID. The own-PK
         column-ordering path is exercised by ordering on ``GenreOrder``
         via the absolute-import-path resolution from ``BookOrder.genres``.
         """

         books = RelatedOrder("apps.library.orders.BookOrder", field_name="books")

         class Meta:
             model = models.Genre
             fields = ["id", "name"]
     ```
   - **`__all__` tuple** (mirrors filters_genre.py:33): `__all__ = ("GenreOrder",)`.

3. **Edit `examples/fakeshop/apps/library/schema.py`** (existing file, 274 lines). Six surgical edits per the existing TODO anchors.
   - **Add `orders` + `orders_genre` to the `apps.library` import line** at schema.py:9. Final shape: `from apps.library import filters, filters_genre, models, orders, orders_genre`.
   - **Add `order_input_type` import** at schema.py:11. New line immediately AFTER `from django_strawberry_framework.filters import filter_input_type`: `from django_strawberry_framework.orders import order_input_type`.
   - **Remove the TODO anchor at schema.py:13-21** (the multi-line block naming "spec-028-orders-0_0_8 Slice 4: Import `orders` / `orders_genre`"). The anchor is fully consumed by the two imports above + the wirings below.
   - **Wire `Meta.orderset_class` on five `DjangoType` classes** (one new line per class, immediately after the existing `filterset_class = filters.<X>Filter` line):
     - `LoanType.Meta`: after `filterset_class = filters.LoanFilter` at schema.py:59, add `orderset_class = orders.LoanOrder`.
     - `BookType.Meta`: after `filterset_class = filters.BookFilter` at schema.py:77, add `orderset_class = orders.BookOrder`.
     - `ShelfType.Meta`: after `filterset_class = filters.ShelfFilter` at schema.py:108, add `orderset_class = orders.ShelfOrder`.
     - `GenreType.Meta`: after `filterset_class = filters_genre.GenreFilter` at schema.py:126, add `orderset_class = orders_genre.GenreOrder`.
     - `BranchType.Meta`: after `filterset_class = filters.BranchFilter` at schema.py:160, add `orderset_class = orders.BranchOrder`.
     - `PatronType.Meta`: after `filterset_class = filters.PatronFilter` at schema.py:175, add `orderset_class = orders.PatronOrder`.
     - `MembershipCardType` (schema.py:111-116) stays UNWIRED on the order side (matches the filter side — no `filterset_class` either).
   - **Add `order_by:` argument to six root resolvers** (one new signature line + one new resolver-body line per resolver):
     - `all_library_branches` at schema.py:199-208: signature grows `order_by: list[order_input_type(orders.BranchOrder)] | None = None,`; body grows `if order_by is not None: queryset = orders.BranchOrder.apply_sync(order_by, queryset, info)` immediately after the `if filter is not None: queryset = filters.BranchFilter.apply_sync(...)` block. The chain becomes `BranchType.get_queryset(...) → filters.BranchFilter.apply_sync(...) → orders.BranchOrder.apply_sync(...)` per Spec Decision 8 step ordering.
     - `all_library_shelves` at schema.py:210-219: same pattern with `ShelfOrder`.
     - `all_library_books` at schema.py:221-230: same pattern with `BookOrder`.
     - `all_library_genres` at schema.py:236-245: same pattern with `GenreOrder` (imported via `orders_genre.GenreOrder`).
     - `all_library_patrons` at schema.py:247-256: same pattern with `PatronOrder`.
     - `all_library_loans` at schema.py:262-271: same pattern with `LoanOrder`.
     - `all_library_prefetched_books` (schema.py:232-234) stays UNWIRED (no filter today, no order added).
     - `all_library_membership_cards` (schema.py:258-260) stays UNWIRED.
     - `DjangoListField` resolvers at schema.py:190-197 stay UNWIRED per Spec Non-goals "`DjangoListField` orderBy-argument integration deferred to `0.0.9`".
   - **Remove the TODO anchor at schema.py:182-188** (the multi-line block naming "spec-028-orders-0_0_8 Slice 4: Add `order_by` arguments"). Fully consumed by the six resolver edits above.

4. **Edit `examples/fakeshop/test_query/test_library_api.py`** (existing file, 1309 lines). Two new helpers + 14 new test functions appended after the existing tests. Worker 2 places them in spec-list order (Tests 1-14) so a future reader walks the live-HTTP coverage in the same order as the Spec test plan at lines 1031-1045.
   - **Remove the TODO anchor at test_library_api.py:114-127** (the multi-line block naming "spec-028-orders-0_0_8 Slice 4: Add exactly 14 live `/graphql/` order acceptance tests"). Fully consumed by the 14 test additions below.
   - **Add two module-level seed helpers** (after the existing helper block at test_library_api.py:53-111; before the first `@pytest.mark.django_db` decorator at test_library_api.py:130):
     - `_seed_branches_with_varying_shelves()` — seeds Alpha branch (3 shelves: codes A, C, E) + Beta branch (1 shelf: code B), both `city="Boston"`. Returns nothing.
     - `_seed_books_with_nullable_subtitles()` — seeds one Branch + one Shelf + two Books (one with `subtitle=None`, one with `subtitle="A Short Subtitle"`). Returns nothing. The shelf carries `topic="general"` (avoids the `ShelfType.get_queryset` `topic="secret"` filter so anonymous queries see the seeded books).
   - **Add the 14 new test functions** appended after the final existing test at test_library_api.py:1268-1309. Each test follows the pattern: `@pytest.mark.django_db` decorator + `def test_<name>():` + inline seed (calling the helper or hand-rolling) + GraphQL query string + `response = _post_graphql(query)` (or `_post_graphql_as_staff(query)` for staff halves) + assertion block. The 14 test names + GraphQL query shapes + assertion shapes are pinned in `### Test additions / updates` below.

### Test additions / updates

The 14 new live HTTP tests append to `examples/fakeshop/test_query/test_library_api.py`. Names + query shapes + assertion shapes are pinned per the Spec test plan at lines 1027-1047 + Spec Slice 4 sub-bullet at lines 124-127. **Count verification (Worker 1 explicit recount per the dispatch prompt's "Verify the spec body's exact count" instruction):** the Spec test plan at lines 1031-1045 lists exactly 15 distinct bullets, BUT Decision 13 at line 942 + the Implementation-plan Slice-4 row at line 966 both pin the count at "14 tests total". The reconciling bullets: Spec line 1042 (multi-field priority) is bullet #13; Spec line 1043 (`shelfCode` flat-shorthand) is bullet #14 — **wait, recounting more carefully — the spec test plan bullets at lines 1031-1045 are: (1) name_asc, (2) subtitle_desc_nulls_last, (3) forward_fk, (4) reverse_fk_multiplicity, (5) m2m_absolute_path, (6) filter_and_order_compose, (7) optimizer_cooperation, (8) get_queryset_runs_before_order, (9) denies_for_active_field, (10) quiet_for_inactive_field, (11) denies_active_related_branch, (12) multi_field_priority, (13) flat_shorthand_path, (14) empty_list_passes_through, (15) null_direction_skips_field.** That is 15 bullets, NOT 14. Decision 13 + the Implementation-plan row pin "14". The mismatch is real.

**Worker 1 planning-pass resolution:** the Spec test plan at line 1029 says "Exactly 14 new live HTTP tests" verbatim — the 15-bullet enumeration that follows is an OVER-COUNT. The dispatch prompt's analysis confirms: "Decision 13's count is **14** per Spec rev4". The reconciliation: the M6 split-pair (Tests 9 + 10 in my recount) IS two distinct tests per Spec test plan lines 1039-1040 — Spec explicitly calls them out as "split from a single combined test". The two M7 no-op tests (Tests 14 + 15 in my recount) per Spec test plan lines 1044-1045 are likewise BOTH called out as `_empty_list_passes_through` AND `_null_direction_skips_field` — explicitly two tests. **The over-count is in the Slice 4 sub-bullet wording at spec line 127**, which folds the M7 pair under "empty-list / null-direction no-op edge cases" — language that reads as ONE bundle but enumerates as TWO. Worker 1's pin: ship 14 tests by **combining the two M7 no-op tests into ONE test that exercises both** `orderBy: []` AND `orderBy: [{ name: null }]` via separate query bodies in one test function — the SQL contract is the same ("no `ORDER BY` clause is emitted") and the combined test pins both halves with named subassertions. This matches the spec Slice 4 sub-bullet wording ("empty-list / null-direction no-op edge cases" — a single combined contract) and brings the count to 14. **Worker 1 will record this resolution under `### Notes for Worker 1 (spec reconciliation)` and edit the spec test-plan bullets 14 + 15 to reflect the combined test at final verification** (the spec's slice sub-bullet at line 127 already pins the combined shape; only the test-plan enumeration at lines 1044-1045 needs harmonizing).

**The canonical 14-test list (named verbatim per Spec test plan line numbers cited):**

1. **`test_library_branches_order_by_name_asc`** — scalar ASC on `BranchType.name` (Spec line 1031).
   - Query: `{ allLibraryBranches(orderBy: [{ name: ASC }]) { id name } }`.
   - Seed: three branches with distinct names (e.g., `"Bravo"`, `"Alpha"`, `"Charlie"`) all `city="Boston"`.
   - Assert: response's `allLibraryBranches[*].name` equals `["Alpha", "Bravo", "Charlie"]` (alphabetic ascending).

2. **`test_library_books_order_by_subtitle_desc_nulls_last`** — scalar DESC with NULLS positioning on `Book.subtitle` (Spec line 1032; Spec Revision 4 B3).
   - Query: `{ allLibraryBooks(orderBy: [{ subtitle: DESC_NULLS_LAST }]) { id title subtitle } }`.
   - Seed: call `_seed_books_with_nullable_subtitles()` — seeds one `Book(subtitle=None, title="Null Title")` and one `Book(subtitle="A Short Subtitle", title="Non-null Title")` plus their owning Branch + Shelf.
   - Assert: response's `allLibraryBooks[0].subtitle == "A Short Subtitle"` AND `allLibraryBooks[-1].subtitle is None` (the non-null subtitle row appears BEFORE the `subtitle=None` row per NULLS-LAST).

3. **`test_library_books_order_by_forward_fk_relation`** — forward-FK nested-shape ordering on `BookType.shelf.code` via same-module `RelatedOrder` (Spec line 1033).
   - Query: `{ allLibraryBooks(orderBy: [{ shelf: { code: ASC } }]) { id shelf { code } } }`.
   - Seed: one Branch + three Shelves with codes `["C", "A", "B"]` + one Book per shelf.
   - Assert: response's `allLibraryBooks[*].shelf.code` equals `["A", "B", "C"]` (alphabetic ascending by shelf code).

4. **`test_library_branches_order_by_reverse_fk_relation`** — reverse-FK relation order with denormalized JOIN+ORDER multiplicity (Spec line 1034; Spec Revision 4 M5).
   - Query: `{ allLibraryBranches(orderBy: [{ shelves: { code: ASC } }]) { id name } }`.
   - Seed: `_seed_branches_with_varying_shelves()` — Alpha (shelves A, C, E) + Beta (shelf B), both `city="Boston"`.
   - Assert: response's `allLibraryBranches[*].name` equals `["Alpha", "Beta", "Alpha", "Alpha"]` (Alpha appears THREE times — once per shelf — interleaved with Beta at the position of shelf code "B" alphabetically between "A" and "C"). The denormalized multiplicity is the load-bearing contract; the test name documents it.

5. **`test_library_books_order_by_m2m_absolute_import_path`** — M2M relation order through the Layer-2 absolute-import-path resolution (Spec line 1035).
   - Query: `{ allLibraryBooks(orderBy: [{ genres: { name: ASC } }]) { id title } }`.
   - Seed: one Branch + one Shelf + three Genres (`"Mystery"`, `"Fantasy"`, `"SciFi"`) + three Books each tagged with one distinct genre.
   - Assert: response's `allLibraryBooks[*].title` order corresponds to alphabetic Genre-name order (`"Fantasy"`, `"Mystery"`, `"SciFi"`). The test exercises `BookOrder.genres = RelatedOrder("apps.library.orders_genre.GenreOrder")` — the absolute-import-path Layer-2 first-attempt branch.

6. **`test_library_books_filter_and_order_compose`** — composition with the shipped Filtering subsystem (Spec line 1036; Spec Revision 4 H4 for the lower-case `available` enum).
   - Query: `{ allLibraryBooks(filter: { circulationStatus: { exact: available } }, orderBy: [{ title: ASC }]) { id title circulationStatus } }`.
   - Seed: one Branch + one Shelf + three Books — two `CirculationStatus.AVAILABLE` (titles `"Beta Title"`, `"Alpha Title"`) + one `CirculationStatus.CHECKED_OUT` (title `"Gamma Title"`).
   - Assert: response's `allLibraryBooks[*].title` equals `["Alpha Title", "Beta Title"]` (only `available` books, sorted ascending by title) AND `circulationStatus` is `"available"` for every row.

7. **`test_library_books_order_preserves_optimizer_cooperation`** — composition with the optimizer; assert query count under `assertNumQueries(N)` (Spec line 1037; Spec Revision 4 H2).
   - Query: `{ allLibraryBooks(filter: { circulationStatus: { exact: available } }, orderBy: [{ title: ASC }]) { id title shelf { code } genres { name } } }`.
   - Seed: same shape as the shipped filter-side test_library_books_filter_preserves_optimizer_cooperation at test_library_api.py:1001-1049 — one Branch + one Shelf + one Genre + two Books (one `available` tagged with the genre + one `checked_out` tagged with the genre).
   - Assert (using `CaptureQueriesContext(connection)` per the shipped pattern at test_library_api.py:1020): `response.status_code == 200`, no errors, response's `allLibraryBooks[*].title == ["Foundation"]` (only the `available` book), `len(captured) == 3` (root SELECT + `select_related("shelf")` JOIN + `prefetch_related("genres")` SELECT — Spec H2 explicitly does NOT promise order-aware projection augmentation; the count is identical to the shipped filter-only test).

8. **`test_root_get_queryset_runs_before_order_apply`** — root `get_queryset` visibility scopes the queryset BEFORE the order clause (Spec line 1038).
   - Query (anonymous): `{ allLibraryBranches(orderBy: [{ name: DESC }]) { id name } }`.
   - Seed: one `Branch(name="Alpha", city="Boston")` + one `Branch(name="Zeta", city="restricted")` — anonymous query sees ONLY the Boston row per `BranchType.get_queryset` at schema.py:137-150.
   - Assert: response's `allLibraryBranches[*].name` equals `["Alpha"]` — `"Zeta"` is hidden BEFORE the DESC order clause runs (without the hide, `"Zeta"` would appear at position 0).
   - Staff half: re-issue via `_post_graphql_as_staff(query)`; assert response's `allLibraryBranches[*].name` equals `["Zeta", "Alpha"]` (both rows visible, DESC-ordered).

9. **`test_order_check_permission_denies_for_active_field`** — split-pair active-input-only scalar permission denial (Spec line 1039; Spec Revision 4 M6).
   - Query (anonymous): `{ allLibraryBranches(orderBy: [{ name: ASC }]) { id } }`.
   - Seed: minimal — one Branch row to confirm the gate fires before any rows return.
   - Assert: response's `payload["errors"][0]["extensions"]["code"] == "ORDER_PERMISSION_DENIED"` (the gate `BranchOrder.check_name_permission(request)` fires because `name` is active in the input).

10. **`test_order_check_permission_quiet_for_inactive_field`** — split-pair quiet half (Spec line 1040; Spec Revision 4 M6).
    - Query (anonymous): `{ allLibraryBranches(orderBy: [{ city: ASC }]) { id city } }`.
    - Seed: one or two Branches with distinct `city` values (e.g., `"Boston"`, `"Cambridge"`), both visible to anonymous users (city != `"restricted"`).
    - Assert: `payload` carries NO `"errors"` key AND `allLibraryBranches[*].city` is alphabetically ascending — `check_name_permission` does NOT fire because `name` is absent from the input (active-input-only scope).

11. **`test_order_check_permission_denies_active_related_branch`** — H3-rev3 active-branch relation-level permission gate (Spec line 1041; Spec Revision 4 H3).
    - Query (anonymous, denial half): `{ allLibraryBranches(orderBy: [{ shelves: { code: ASC } }]) { id } }`.
    - Seed: one Branch + one Shelf so the gate has a row substrate (the gate fires before rows return; the seed just ensures the visibility scope is non-empty).
    - Assert (denial half): response's `payload["errors"][0]["extensions"]["code"] == "ORDER_PERMISSION_DENIED"` (the gate `BranchOrder.check_shelves_permission(request)` fires because the `shelves` RelatedOrder branch is active).
    - Query (anonymous, quiet half): `{ allLibraryBranches(orderBy: [{ city: ASC }]) { id city } }`. **Note:** Worker 1's planning-pass resolution — the Spec test plan line 1041 says "Re-issue `orderBy: [{ name: ASC }]`" for the quiet half, but `name` is ALSO gated by `check_name_permission` from Test 9, which would denial-trigger on the same input. The quiet half MUST use an unguarded field. `city` is the right choice (no `check_city_permission` on `BranchOrder`; the gate from `BranchType.get_queryset` hides `city="restricted"` rows but does not raise). Worker 1 will edit Spec line 1041 to substitute `city` for `name` in the quiet half at final verification — recorded under `### Notes for Worker 1 (spec reconciliation)`.
    - Assert (quiet half): `payload` carries NO `"errors"` key AND `allLibraryBranches[*].city` is ascending — `check_shelves_permission` does NOT fire because the `shelves` branch is absent.

12. **`test_library_books_order_by_multi_field_priority`** — multi-field priority via list-element ordering (Spec line 1042).
    - Query: `{ allLibraryBooks(orderBy: [{ shelf: { code: ASC } }, { title: DESC }]) { id title shelf { code } } }`.
    - Seed: two Shelves (codes `"A"` and `"B"`) + four Books: two on shelf A (titles `"Foo"`, `"Bar"`) and two on shelf B (titles `"Foo"`, `"Bar"`).
    - Assert: response's `allLibraryBooks` ordered as `[(shelf="A", title="Foo"), (shelf="A", title="Bar"), (shelf="B", title="Foo"), (shelf="B", title="Bar")]` — shelf code dominates (ASC); title is the secondary tie-breaker (DESC, so `"Foo"` before `"Bar"`).

13. **`test_library_books_order_by_flat_shorthand_path`** — flat-shorthand path order via `Meta.fields = ["shelf__code"]` rendering as `shelfCode: Ordering` (Spec line 1043; Spec Revision 4 M2).
    - Query: `{ allLibraryBooks(orderBy: [{ shelfCode: ASC }]) { id title } }`.
    - Seed: one Branch + three Shelves with codes `["C", "A", "B"]` + one Book per shelf with distinct titles.
    - Assert: response's `allLibraryBooks[*]` ordered such that the book on shelf `"A"` is first, on shelf `"B"` second, on shelf `"C"` third (shelf code ascending via the flat `shelfCode:` GraphQL field name). The test confirms the GraphQL surface accepts `shelfCode:` (NOT `shelf: { code: ASC }`) AND the runtime normalizer reconstructs the Django ORM path as `shelf__code` (verified by row-order assertion; an SQL-substring assertion via `CaptureQueriesContext` is optional and at Worker 2's discretion).

14. **`test_library_branches_order_empty_list_and_null_direction_no_op`** — combined M7-rev1 no-op edge cases (Spec lines 1044-1045 combined into one test per Worker 1's planning-pass resolution to fit the 14-count). Tests BOTH halves in one function via separate query bodies + named subassertions.
    - Query A (empty-list): `{ allLibraryBranches(orderBy: []) { id name } }`.
    - Query B (null-direction): `{ allLibraryBranches(orderBy: [{ name: null }]) { id name } }`.
    - Seed: three Branches with distinct names (e.g., `"Bravo"`, `"Alpha"`, `"Charlie"`) all `city="Boston"` (avoid `"restricted"` to keep the anonymous query non-empty).
    - Assert A (empty-list half): `payload` carries NO `"errors"` key AND `allLibraryBranches[*].name` is in the queryset's default order (`models.Branch.objects.order_by("id")` per the resolver chain at schema.py:205 — so the order is insertion order: `["Bravo", "Alpha", "Charlie"]`). **Worker 2 may optionally verify via `CaptureQueriesContext` that the executed SQL carries NO additional `ORDER BY` clause beyond the pre-existing `ORDER BY id` from the resolver-level `models.Branch.objects.order_by("id")`.**
    - Assert B (null-direction half): same as Assert A — `payload` carries NO `"errors"` key AND `allLibraryBranches[*].name` is in default order (the null direction decodes to `None` in the Strawberry input and `get_flat_orders` skips `None` directions per Spec Edge case "`orderBy: [{ name: null }]`").

### Implementation discretion items

Worker 1 has assessed every architectural choice above. The items below are at Worker 2's discretion (style, naming, equivalent-shape preference); Worker 2 ships whichever shape reads best per the surrounding code:

- **Seed-helper inlining.** `_seed_books_with_nullable_subtitles()` is named here, but if Worker 2 prefers to inline the seed body directly inside Test 2 because the seed shape stays under ~6 lines and reads as part of the test's contract, inlining is acceptable. The `_seed_branches_with_varying_shelves()` helper for Test 4 is RECOMMENDED as a named module-level helper because the seed shape (3-shelf Alpha + 1-shelf Beta) is the load-bearing multiplicity contract and a typo in shelf-count or shelf-code form would silently flip the assertion meaning.
- **`check_*_permission` gate body wording.** The `GraphQLError("staff only", extensions={"code": "ORDER_PERMISSION_DENIED"})` body shape is pinned by Spec test plan lines 1039-1041; the precise message string (`"staff only"`, `"hidden shelves"`, or another consumer-facing string) is at Worker 2's discretion as long as the extension code is exactly `"ORDER_PERMISSION_DENIED"` and the assertion path `payload["errors"][0]["extensions"]["code"]` matches.
- **Test docstring shape.** Worker 2 may use a one-line docstring (matching the shipped filter-side pattern at test_library_api.py:691, 723, 747, 767) OR a multi-line block (matching the shipped pattern at test_library_api.py:794-803, 1002-1003, 1108-1117) per the test's complexity. Tests 4 (reverse-FK multiplicity) and 11 (active-branch H3) merit multi-line docstrings citing the spec sub-bullet rationale; the remaining 12 may use one-line docstrings.
- **`CaptureQueriesContext` usage in Test 13.** Spec test plan line 1043 says "verified by assertion against `queryset.query.order_by` or by SQL substring match" — the SQL-substring path is at Worker 2's discretion. A row-order assertion alone is sufficient to pin the contract; adding `CaptureQueriesContext` for SQL inspection is BELT-AND-SUSPENDERS and Worker 2 may skip it.
- **Order of the 14 test function definitions in `test_library_api.py`.** Worker 1 recommends spec-list order (Tests 1-14 matching Spec lines 1031-1045) so a future reader walks the coverage in the same order as the Spec test plan. Worker 2 may group differently (e.g., scalar tests first, relation tests second, permission tests third) at Worker 2's discretion as long as all 14 are present.
- **Whether to use `_assert_graphql_data(query, expected)` exact-match shape OR a `response = _post_graphql(query)` + per-row assertion shape per test.** Worker 1 recommends `_assert_graphql_data` for Tests 1, 3, 5, 6, 12, 13 (exact ordered-list comparisons) and the lower-level `_post_graphql` shape for Tests 2 (NULLS positioning needs row-content + position checks), 4 (multiplicity counts), 7 (CaptureQueriesContext + error-key check), 8 (visibility halves), 9, 10, 11 (error-extension checks), 14 (no-error halves) — but Worker 2 may use either pattern as long as the assertion is unambiguous.

### Notes for Worker 1 (spec reconciliation)

Worker 1 records three planning-pass spec-vs-codebase findings here. Each will be re-assessed at Slice-4 final verification; final-verification authorizes the spec edits if still warranted.

- **Spec line 127 + Spec lines 1044-1045 over-count vs Decision 13 at line 942 / Implementation-plan row at line 966.** The Spec test plan at lines 1031-1045 enumerates 15 distinct test names; Decision 13 + the Implementation-plan row both pin "14 tests total". The over-count is in the M7 no-op bundle (lines 1044-1045 list two tests; Slice 4 sub-bullet at line 127 folds them as "empty-list / null-direction no-op edge cases" — one bundle). Worker 1's planning-pass resolution: ship 14 tests by combining the two M7 no-op tests into ONE test (Test 14 above) that exercises both halves via separate query bodies. **Final-verification action:** edit Spec test-plan lines 1044-1045 to read as one combined bullet (`test_library_branches_order_empty_list_and_null_direction_no_op`) so the spec body matches the shipped test count. The Slice 4 sub-bullet at line 127 already pins the combined shape; only the test-plan enumeration needs harmonizing.
- **Spec line 1041 quiet-half input collides with Test 9 + 10's `check_name_permission` gate.** The Spec says "Re-issue `{ allLibraryBranches(orderBy: [{ name: ASC }]) { id } }`" for Test 11's quiet half — but `name` is ALSO gated by `check_name_permission` from Test 9, which would denial-trigger on the same input. The quiet half MUST use an unguarded field. Worker 1's planning-pass resolution: Test 11's quiet half uses `orderBy: [{ city: ASC }]` instead. **Final-verification action:** edit Spec line 1041 to substitute `city` for `name` in the quiet half. The H3 contract (quiet when the `shelves` branch is absent) is preserved either way; only the example query needs updating.
- **`BookOrder.Meta.fields` coexistence of `"shelf__code"` (flat shorthand) AND explicit `RelatedOrder("ShelfOrder", field_name="shelf")` (nested shape).** Test 13 (flat-shorthand) and Tests 3, 7, 8, 12 (nested-shape) both target `BookOrder` and need both surfaces (`shelfCode: Ordering` AND `shelf: ShelfOrderInputType`) to coexist on the input type. Worker 1's planning-pass pin: `BookOrder.Meta.fields = ["id", "title", "subtitle", "circulation_status", "shelf__code"]` (no `"shelf"` column leaf) PLUS the explicit `shelf = RelatedOrder("ShelfOrder", field_name="shelf")` — the column-list does NOT include `"shelf"` so the only `shelf:` surface on the input type is the nested `ShelfOrderInputType` (per the override-by-same-name contract from Spec Edge case "`Meta.fields = '__all__'`" final sentence), AND the path-shorthand `"shelf__code"` produces the `shelfCode: Ordering` leaf. **If Worker 2 (or Worker 3) discovers at build/review time that the path-shorthand entry collides with the explicit `RelatedOrder` (e.g., both emit a `shelf:` field on the input type), escalate via `### Notes for Worker 1 (spec reconciliation)` in the build report. Worker 1's final-verification will then decide whether to (a) split `BookOrder` into two ordersets (e.g., a `BookFlatOrder` for Test 13 only), (b) drop the `"shelf__code"` entry and rewrite Test 13 to use a different model (e.g., a `Loan.book__title` path on `LoanOrder`), or (c) accept the collision and edit Test 13 accordingly.** Worker 1 has no Slice-2 test that pins the coexistence-on-the-same-OrderSet contract directly, so this is a real planning-time uncertainty; the pin above is Worker 1's best guess based on Spec Edge case wording.

---

## Build report (Worker 2)

### Files touched

- `examples/fakeshop/apps/library/orders.py` — replaced TODO-anchored placeholder with five `OrderSet` declarations (`BranchOrder`, `ShelfOrder`, `BookOrder`, `LoanOrder`, `PatronOrder`) mirroring `filters.py` one-for-one with the Filter→Order substitution. `BranchOrder` carries the two `check_*_permission` gates (`check_name_permission`, `check_shelves_permission`) raising `GraphQLError` with `code="ORDER_PERMISSION_DENIED"` per Spec test plan lines 1039-1041. `BookOrder.Meta.fields = ["id", "title", "subtitle", "circulation_status", "shelf__code"]` (flat-shorthand `shelf__code` path included, NO `"shelf"` column leaf) PLUS explicit `shelf = RelatedOrder("ShelfOrder", field_name="shelf")` so both surfaces coexist per Worker 1's planning-pass pin. `BookOrder.genres` uses absolute-import path `"apps.library.orders_genre.GenreOrder"` so Layer-2 `import_string` first-attempt branch is exercised end-to-end.
- `examples/fakeshop/apps/library/orders_genre.py` — replaced TODO-anchored placeholder with `GenreOrder` cross-module fixture; `books = RelatedOrder("apps.library.orders.BookOrder", field_name="books")` exercises the cross-module-pointing-back branch.
- `examples/fakeshop/apps/library/schema.py` — added `from apps.library import orders, orders_genre` to the existing import; added `from django_strawberry_framework.orders import order_input_type` import; wired `Meta.orderset_class` on the five `DjangoType` classes that already carry `filterset_class` (`LoanType`, `BookType`, `ShelfType`, `GenreType`, `BranchType`, `PatronType`); added `order_by: list[order_input_type(orders.<X>Order)] | None = None` argument to the six in-scope root resolvers (`all_library_branches`, `all_library_shelves`, `all_library_books`, `all_library_genres`, `all_library_patrons`, `all_library_loans`); resolver chain is now `<Type>.get_queryset → <Type>Filter.apply_sync → <Type>Order.apply_sync` per Spec Decision 8 step ordering. Removed both TODO anchors (the import-block anchor at schema.py:13-21 and the resolver-block anchor at schema.py:182-188).
- `examples/fakeshop/test_query/test_library_api.py` — removed the TODO anchor at test_library_api.py:114-127; added two module-level seed helpers (`_seed_branches_with_varying_shelves`, `_seed_books_with_nullable_subtitles`); appended exactly 14 new live HTTP tests per Worker 1's pinned canonical list (in spec-list order, Tests 1-14).

### Tests added or updated

The 14 new tests appended to `examples/fakeshop/test_query/test_library_api.py`:

- `test_library_branches_order_by_name_asc` — scalar ASC on `Branch.name` (staff context, see Implementation notes).
- `test_library_books_order_by_subtitle_desc_nulls_last` — `DESC_NULLS_LAST` on nullable `Book.subtitle` (B3-rev3).
- `test_library_books_order_by_forward_fk_relation` — forward-FK nested `shelf: { code: ASC }`.
- `test_library_branches_order_by_reverse_fk_relation` — reverse-FK denormalized multiplicity (M5-rev1; staff context).
- `test_library_books_order_by_m2m_absolute_import_path` — M2M order via Layer-2 absolute-import-path resolution.
- `test_library_books_filter_and_order_compose` — composition with the shipped filter subsystem (H4 enum literal `available`).
- `test_library_books_order_preserves_optimizer_cooperation` — `assertNumQueries == 3` (H2-rev1).
- `test_root_get_queryset_runs_before_order_apply` — visibility scope before order (orders by `city` not `name`; see Implementation notes).
- `test_order_check_permission_denies_for_active_field` — `check_name_permission` denies anonymous (M6-rev1 split-pair).
- `test_order_check_permission_quiet_for_inactive_field` — `check_name_permission` quiet for unguarded `city` field (M6-rev1 split-pair).
- `test_order_check_permission_denies_active_related_branch` — `check_shelves_permission` denies for active `shelves` branch + quiet for `city` (H3-rev3; the quiet half uses `city` per Worker 1's plan reconciliation).
- `test_library_books_order_by_multi_field_priority` — list-element ordering tie-breaker.
- `test_library_books_order_by_flat_shorthand_path` — `shelfCode: ASC` flat-shorthand path (M2-rev1).
- `test_library_branches_order_empty_list_and_null_direction_no_op` — combined M7-rev1 no-op edge cases (empty-list + null-direction halves in one test).

### Validation run

- `uv run ruff format .` — pass (1 file reformatted on first run; clean on re-run).
- `uv run ruff check --fix .` — pass.
- `git status --short` after both ruff invocations — all slice-intended files (`orders.py`, `orders_genre.py`, `schema.py`, `test_library_api.py`) are in scope; every other modified/untracked file in the working tree is on the build plan's baseline-dirty out-of-scope list and was not touched by this pass.
- Focused tests: `uv run pytest --no-cov examples/fakeshop/test_query/test_library_api.py` — **46 passed** (32 pre-existing filter-side tests + 14 new Slice 4 order tests). No `--cov*` flags.

### Implementation notes

- **Staff context applied to Tests 1, 4, 8.** Worker 1's plan put `check_name_permission` and `check_shelves_permission` permanently on `BranchOrder`, but Tests 1 (`name: ASC`), 4 (`shelves: { code: ASC }`), and 8 (initially `name: DESC`) target the same gated fields/branches that Tests 9 and 11 use to denial-trigger. With anonymous context, all three would denial-fire on the gate before exercising their actual contracts. I applied `_post_graphql_as_staff` to Tests 1 and 4 (the gate fires but staff bypasses it; the contract — ascending order, reverse-FK multiplicity — is still pinned cleanly). Test 8's contract is "root `get_queryset` runs BEFORE order apply" — using staff bypasses the visibility hook (the test's load-bearing assertion), so instead the test orders by `city: DESC` (an unguarded scalar) with the same `Branch(name="Alpha", city="Boston")` + `Branch(name="Zeta", city="restricted")` fixture; anonymous still sees only Alpha (visibility hook ran first); staff sees both rows ordered. This is the same spec-reconciliation pattern Worker 1 applied to Test 11's quiet half (substitute `city` for `name` when the `name` gate would collide). Flagged under `### Notes for Worker 1 (spec reconciliation)` below.
- **Test 14 (combined M7 no-op).** Both halves (empty-list AND null-direction) fit cleanly in one test function via separate query bodies + named subassertions, matching Worker 1's planning-pass count-reconciliation pin (Spec body says "14 tests" but enumerates 15 bullets; M7 was the over-count). The empty-list half passes through the queryset's resolver-level `order_by("id")` insertion order; the null-direction half does the same because `_active_permission_field_paths` filters `raw_value is None` (so `check_name_permission` does NOT fire for `name: null`) and the apply pipeline filters `direction is None` before `queryset.order_by(...)`.
- **`_assert_graphql_data` vs `_post_graphql` split.** Used `_assert_graphql_data` for the exact-match-ordered-list tests (Tests 1, 3, 5, 6, 13). Used `_post_graphql` + per-row assertion for the tests with multi-shape assertions: Test 2 (NULLS positioning needs row-content + position), Test 4 (multiplicity counts), Test 7 (CaptureQueriesContext + error-key + len-rows), Test 8 (visibility halves with city/name shapes), Tests 9, 10, 11 (errors/extensions), Test 12 (tuple-style ordering), Test 14 (two halves in one function). Matches Worker 1's discretion-item recommendation.
- **Seed helpers kept as module-level.** `_seed_branches_with_varying_shelves` (Test 4) is mandatory per Worker 1's plan; `_seed_books_with_nullable_subtitles` (Test 2) was named-helper rather than inlined because its seed shape is the load-bearing contract for the NULLS-LAST positioning assertion.

### Notes for Worker 3

- The shipped filter-side test corpus at `test_library_api.py:670-1293` was the reference template; the 14 new Slice 4 tests live after it (separator comment at line 1297 "Slice 4 — live HTTP order coverage"). Reuse of `_post_graphql`, `_post_graphql_as_staff`, `_assert_graphql_data`, `CaptureQueriesContext`, `_reload_project_schema_for_acceptance_tests` is verbatim — no new helpers were introduced beyond the two seed helpers.
- Both `apps/library/orders.py` and `apps/library/orders_genre.py` are pure-class-definition modules (no functions outside class bodies, no module-level logic apart from `__all__`). Per `BUILD.md` "Worker 3 must run the helper during review when ... unless it is a pure-class-definition module", the helper is NOT required for these two new files.
- No shadow-file usage during build.

### Notes for Worker 1 (spec reconciliation)

Worker 2 surfaced one new spec-vs-implementation conflict beyond the three Worker 1 already recorded at plan time:

- **Spec Tests 1, 4, and 8 collide with the Test 9/11 permission gates declared on `BranchOrder`.** Tests 9 and 11 require `BranchOrder.check_name_permission` and `BranchOrder.check_shelves_permission` to be DECLARED permanently on the orderset (Spec lines 1039, 1041). Tests 1 (`name: ASC`), 4 (`shelves: { code: ASC }`), and 8 (originally `name: DESC`) use the same gated fields/branches with anonymous context — so the gate denial-fires before each test's actual contract can be exercised. Worker 1's plan acknowledged this conflict for Test 11's quiet half (substituting `city` for `name`) but did not address the same conflict for Tests 1, 4, 8. Build-pass resolution applied:
  - Test 1 (`name: ASC`): use `_post_graphql_as_staff` (gate fires but staff bypasses; ASC contract pinned cleanly).
  - Test 4 (`shelves: { code: ASC }`): use `_post_graphql_as_staff` (gate fires but staff bypasses; multiplicity contract pinned cleanly).
  - Test 8 (originally `name: DESC` per spec line 1038): order by `city: DESC` instead (an unguarded scalar) — same Branch+city fixture, same anonymous-visibility-scope contract; the `restricted` row is still hidden by `BranchType.get_queryset` BEFORE the order clause runs. Using staff bypasses the visibility hook (the test's load-bearing observation), which is why this test cannot just become staff-context like Tests 1 and 4. Same reconciliation pattern Worker 1 applied to Test 11.
  - **Final-verification action recommendation:** edit Spec lines 1031, 1034, 1038 to either (a) explicitly mark Tests 1, 4 as staff-context AND change Test 8's order field from `name` to `city`, OR (b) move the `check_*_permission` declarations off the shipped `BranchOrder` into test-local orderset declarations specific to Tests 9 / 10 / 11 (requires a different test setup pattern — fixture-scoped orderset wiring through the reload mechanism). Option (a) is the smaller surface change and matches the build-pass resolution.

The three spec-reconciliation notes Worker 1 already raised in the Plan section stand unchanged:
- Spec line 127 + Spec lines 1044-1045 14-vs-15 count over-count (build-pass resolved via combined Test 14).
- Spec line 1041 quiet-half input collision (build-pass resolved via `city` substitution).
- `BookOrder.Meta.fields` flat-shorthand `shelf__code` coexistence with explicit `RelatedOrder("ShelfOrder", field_name="shelf")` — build-pass confirms they coexist on the same input type without collision (Tests 3, 7, 8, 12 use the nested `shelf: { code: ... }` surface; Test 13 uses the flat `shelfCode: ...` surface; both pass).

### Spec slice checklist (verbatim)

The spec's nested sub-bullets for Slice 4 from `## Slice checklist` at spec lines 124-127, copied verbatim as `- [ ]` boxes. Worker 1 ticks each `- [x]` during final verification as the contract lands.

- [x] [`examples/fakeshop/apps/library/`][fakeshop-library] grows `orders.py` containing `BranchOrder`, `ShelfOrder`, `BookOrder`, `LoanOrder`, `PatronOrder` (mirrors the filter side's [`examples/fakeshop/apps/library/filters.py`][fakeshop-library] split — same set of `DjangoType` owners so the live HTTP test plan exercises filter / order composition end-to-end). The M2M side targets `GenreType`; `GenreOrder` lives in a **separate fixture module** [`examples/fakeshop/apps/library/orders_genre.py`][fakeshop-library] so this card's `BookOrder.genres = RelatedOrder("apps.library.orders_genre.GenreOrder")` declaration exercises the Layer-2 absolute-import-path lazy-resolution path (mirrors the filter side's [`examples/fakeshop/apps/library/filters_genre.py`][fakeshop-library] fixture). Same-module unqualified-name resolution is exercised by every other `RelatedOrder("...")` declaration in `orders.py`.
- [x] [`examples/fakeshop/apps/library/schema.py`][fakeshop-library-schema] grows `Meta.orderset_class = orders.BranchOrder` (etc.) on the corresponding `DjangoType` classes. Sibling library root-list resolvers (`all_library_branches`, `all_library_books`, etc.) annotate `orderBy:` via `order_input_type(orders.BranchOrder)` per [Decision 11](#decision-11--order_input_typeorderset-consumer-helper). Each resolver **calls the owning type's `get_queryset(queryset, info)` BEFORE `OrderSet.apply_sync(...)` / `apply_async(...)`** (same security-correct ordering the filter side pins: visibility before order — although ordering does not see through visibility the way filtering can, the rule is one-directional discipline that keeps every resolver call site uniform). Resolvers that previously took only `filter:` grow a sibling `orderBy:` argument; chaining is `queryset = <Type>.get_queryset(...)` → `queryset = <Type>Filter.apply_sync(filter, queryset, info)` → `queryset = <Type>Order.apply_sync(order_by, queryset, info)` (filter narrows the rows, order arranges them).
- [x] [`examples/fakeshop/test_query/test_library_api.py`][fakeshop-test-library] grows **exactly 14 new live `/graphql/` HTTP tests** covering: scalar-field ascending order (`name: ASC`); scalar-field descending order with NULLS positioning (`subtitle: DESC_NULLS_LAST` — per B3 of [`docs/feedback.md`][feedback] rev3, the test must target a nullable text field that actually exists on the model; `Book.subtitle` is the only `TextField(blank=True, null=True)` on the library `Book` model, and the fixture seeds at least one `subtitle=None` row alongside non-null rows to verify NULLS-last positioning); forward-FK relation order (`shelf: { code: ASC }`); reverse-FK relation order with **denormalized JOIN+ORDER multiplicity pinned explicitly** per M5 of [`docs/feedback.md`][feedback] rev1 (a `Branch` with N shelves appears N times in the response, each instance ordered by its individual shelf's code — that is the SQL contract, and the test seeds a multi-shelf Branch to verify the multiplication rather than dodging it); M2M relation order through the absolute-import-path `RelatedOrder` resolution (`genres: { name: ASC }`); flat-shorthand path order via `Meta.fields = ["shelf__code"]` rendering as `shelfCode: ASC` per M2 of [`docs/feedback.md`][feedback] rev1 (pins the path-based GraphQL field name that the runtime normalizer must reconstruct); composition with the shipped filter subsystem (`{ allLibraryBooks(filter: { ... }, orderBy: [...]) { ... } }` — pins filter and order compose cleanly without one clobbering the other); composition with the optimizer (`assertNumQueries(N)` against an ordered + filtered queryset with nested selection — pins that `.order_by(...)` does not break the optimizer's `select_related` / `prefetch_related` plan); root `get_queryset` honoring (ordering operates on the visibility-scoped queryset, not on the unscoped manager); split-pair active-input-only `check_<field>_permission` discipline per M6 of [`docs/feedback.md`][feedback] rev1 — `test_order_check_permission_denies_for_active_field` AND `test_order_check_permission_quiet_for_inactive_field`; **active-branch relation-level permission gate** per H3 of [`docs/feedback.md`][feedback] rev3 — `test_order_check_permission_denies_active_related_branch` exercises `BranchOrder.check_shelves_permission(request)` (the parent's per-RelatedOrder-branch gate) firing for `orderBy: [{ shelves: { code: ASC } }]` and being quiet for `orderBy: [{ name: ASC }]`; multi-field priority ordering (`orderBy: [{ shelf: { code: ASC } }, { title: DESC }]` — pins that the list-shaped `orderBy:` argument processes elements in order so earlier list entries dominate later ones); empty-list / null-direction no-op edge cases per M7 of [`docs/feedback.md`][feedback] rev1 — `test_order_empty_list_passes_through` (`orderBy: []` returns the unordered queryset) AND `test_order_null_direction_skips_field` (`orderBy: [{ name: null }]` is treated as if the field were omitted).

---

## Review (Worker 3)

### High:

None.

### Medium:

None — but see `### Notes for Worker 1 (spec reconciliation)` for two Medium-severity escalations Worker 2 already raised; the build-pass resolutions are well-pinned and Worker 1's final verification owns the spec-edit decision.

### Low:

#### Stale trailing `Status: planned` line at artifact bottom

The artifact carries TWO `Status:` lines: the canonical top-level line 4 (`Status: review-accepted` after this pass) and a stale `Status: planned` trailing the verbatim spec-checklist block at line 422. The trailing line is a template-shape leftover that should have been pruned when Worker 2 set `Status: built`. Not a correctness defect (Worker 0 reads only the top-level Status per `BUILD.md` "Status field ownership"); flagged Low so Worker 1's final-verification pass can decide whether to remove it for cleanliness. Out of scope for Worker 3's edit permissions per `docs/builder/worker-3.md` "Scope" — only the review section is appended.

`docs/builder/bld-slice-4-live_http.md:422`

### DRY findings

- `orders.py` mirrors `filters.py` one-for-one with the Filter→Order substitution per Worker 1's plan. Verified verbatim: same five owner classes (`BranchOrder` / `ShelfOrder` / `BookOrder` / `LoanOrder` / `PatronOrder`), same `RelatedOrder` shape with same `field_name=` arguments, same `Meta.model` references, same `__all__` tuple alphabetic order. The two intentional Worker-1-pinned divergences hold: (a) `BranchOrder.shelves` drops `filters.py::BranchFilter.shelves`'s `queryset=` kwarg because `RelatedOrder` has no `queryset` parameter per Spec Decision 8 (verified at `orders.py::BranchOrder::shelves`); (b) `PatronOrder` is SIMPLER than `PatronFilter` — no `email_must_have_at_sign` custom-validator surface because the cookbook's `AdvancedOrderSet` has no form/validator concept per Spec Decision 8 Justification (verified at `orders.py::PatronOrder`).
- `orders_genre.py::GenreOrder.books` correctly uses the absolute-import-path form `"apps.library.orders.BookOrder"` mirroring `filters_genre.py::GenreFilter.books`, exercising the cross-module-pointing-back Layer-2 branch.
- `BookOrder.Meta.fields = ["id", "title", "subtitle", "circulation_status", "shelf__code"]` uses the LIST shape per Spec Decision 3 (ordering has no lookups; direction is the only modifier). This is intentionally different from `BookFilter.Meta.fields = {"id": ["exact", "in"], ...}` dict-of-lookups. No dict-shaped `Meta.fields` on any OrderSet — clean.
- Test corpus reuses `_post_graphql`, `_post_graphql_as_staff`, `_assert_graphql_data`, `CaptureQueriesContext`, `_reload_project_schema_for_acceptance_tests` verbatim — no test-helper duplication. The two new module-level seed helpers (`_seed_branches_with_varying_shelves`, `_seed_books_with_nullable_subtitles`) are justified per Worker 1's plan (load-bearing multiplicity / NULLS-LAST contract).
- The 14 test bodies follow the shipped filter-side template (per-test seed + GraphQL query + `_post_graphql` or `_assert_graphql_data` + assertion); no near-copy of the filter-side test bodies beyond the structural pattern. Each test differs in (a) the GraphQL query, (b) the seed shape, (c) the assertion shape — the irreducible content per test.
- Resolver chain `BranchType.get_queryset → BranchFilter.apply_sync → BranchOrder.apply_sync` repeats six times in `schema.py` (one per root resolver) — this is the canonical visibility→narrow→arrange pattern per Spec Decision 8 step ordering, not a DRY candidate. Hoisting to a shared helper would obscure the per-type Filter/Order class names.

No DRY findings — Slice 4 is the textbook mirror of the shipped filter side with the spec-justified divergences pinned explicitly in Worker 1's plan.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` empty. Slice 4 is fakeshop-only — NO edits to package source under `django_strawberry_framework/`. Confirmed via diff.

### CHANGELOG sanity

Not applicable; slice did not modify `CHANGELOG.md`. (Slice 5 carries the explicit CHANGELOG-edit permission per the build plan's "CHANGELOG-edit permission" preamble; Slice 4 does not.) The working-tree `M CHANGELOG.md` is out-of-scope maintainer concurrent work — not Slice 4's contribution.

### Documentation / release sanity

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces. (The working-tree `M docs/TREE.md` / `M KANBAN.md` / `M KANBAN.html` / `M docs/GLOSSARY.md` are out-of-scope maintainer concurrent work and on the build plan's baseline-dirty list.)

### What looks solid

- **One-for-one filter-side mirror.** `orders.py` and `orders_genre.py` mirror `filters.py` and `filters_genre.py` shape-for-shape with the Filter→Order substitution and the two spec-justified divergences (no `queryset=` kwarg on `RelatedOrder`; no custom-validator surface on `PatronOrder`). Both Layer-2 lazy-resolution branches are exercised end-to-end: same-module unqualified-name (`RelatedOrder("ShelfOrder")` etc.) AND absolute-import-path (`RelatedOrder("apps.library.orders_genre.GenreOrder")`).
- **Resolver chain ordering.** All six root resolvers in `schema.py` follow the canonical `<Type>.get_queryset → <Type>Filter.apply_sync → <Type>Order.apply_sync` chain per Spec Decision 8 step ordering. The chain is uniform across the six resolvers and matches the filter side's pre-existing shape additively.
- **`order_input_type(...)` wrapping.** Every resolver's `order_by:` argument is correctly typed as `list[order_input_type(orders.<X>Order)] | None = None` per Spec Revision 4 B1. Confirmed at lines 193, 207, 221, 239, 253, 271 of `schema.py`.
- **`BookOrder.Meta.fields` coexistence.** `["id", "title", "subtitle", "circulation_status", "shelf__code"]` (flat-shorthand `shelf__code` rendering as `shelfCode: Ordering`) AND explicit `shelf = RelatedOrder("ShelfOrder", field_name="shelf")` (nested `shelf: ShelfOrderInputType`) coexist on the same input type without collision. Tests 3, 7, 8, 12 use the nested shape; Test 13 uses the flat shorthand. All pass — confirms the Spec Edge case "`Meta.fields = '__all__'`" override-by-same-name contract.
- **Reverse-FK multiplicity asserted explicitly.** Test 4 (`test_library_branches_order_by_reverse_fk_relation`) asserts `names == ["Alpha", "Beta", "Alpha", "Alpha"]` — Alpha appears 3 times (3 shelves: A, C, E), Beta appears once (shelf B), interleaved by shelf code alphabetically. The denormalized JOIN+ORDER SQL contract is pinned rather than dodged via DISTINCT (per Spec Revision 4 M5).
- **`Book.subtitle` nullable seed.** `_seed_books_with_nullable_subtitles()` seeds one `Book(subtitle=None, title="Null Title")` AND one `Book(subtitle="A Short Subtitle", title="Non-null Title")`. Test 2 asserts `rows[0]["subtitle"] == "A Short Subtitle"` AND `rows[-1]["subtitle"] is None` — the non-null subtitle row appears FIRST under `DESC_NULLS_LAST` (per Spec Revision 4 B3).
- **Combined Test 14 (M7 no-op).** Empty-list AND null-direction halves fit cleanly in one test via separate query bodies + named subassertions, reconciling the spec's `14 tests` count with the 15-bullet test plan enumeration. Both halves return the queryset in default (`order_by("id")`) order without raising.
- **14 tests, all green.** Focused run `uv run pytest examples/fakeshop/test_query/test_library_api.py --no-cov` produced 46 passed (32 pre-existing filter-side tests + 14 new Slice 4 order tests). No regressions; new tests pin every Spec test plan contract.
- **Test count exact.** Counted `^def test_` lines under the Slice-4 section banner: exactly 14. Names match the canonical list pinned in Worker 1's plan and the prompt's checklist verbatim.
- **No edits to `tests/orders/*` package tests.** Slice 4 is fakeshop-only per the spec contract; confirmed via `git diff --stat -- tests/orders/` (empty).
- **No edits to version files.** Confirmed via the build plan's "No version bump in this card" rule — `pyproject.toml`, `__version__`, and `CHANGELOG.md` are not touched by Slice 4.
- **`scripts/review_inspect.py` runs.** Re-ran during this review on the two existing files Slice 4 modified: `examples/fakeshop/apps/library/schema.py` (lands at 27 symbols, 0 control-flow hotspots, 1 repeated literal — well within the trigger thresholds post-slice) and `examples/fakeshop/test_query/test_library_api.py` (58 symbols, 13 control-flow hotspots from pre-existing tests, 68 repeated literals from the inline GraphQL query strings — within range for a 1882-line live-HTTP corpus). Both shadow files refreshed under `docs/shadow/`. The two new files `orders.py` and `orders_genre.py` are pure-class-definition modules (only `class` declarations with docstrings, no module-level logic apart from `__all__`) — per `BUILD.md` "Worker 3 must run the helper during review when ... unless it is a pure-class-definition module", the helper is NOT required for them. Skip recorded explicitly per `BUILD.md` instructions.

### Temp test verification

- No temp tests created during this review. The 14 permanent Slice-4 tests pin every Spec test plan contract directly; no behavior needed a separate proof harness.

### Notes for Worker 1 (spec reconciliation)

Worker 2 escalated four spec-vs-implementation reconciliation items in the build report. Worker 3 has read each and confirms the build-pass resolutions are correct under the spec's letter; the spec-text edits remain Worker 1's call at final verification. Re-stated here for completeness:

- **Escalated (Worker 1 ownership): Spec line 1041 quiet-half input collision (Worker 1's planning-pass note).** Spec text says "Re-issue `orderBy: [{ name: ASC }]`" for Test 11's quiet half, but `name` is gated by `check_name_permission` from Test 9 and would denial-trigger on the same input. Build-pass resolution: Test 11 quiet half uses `orderBy: [{ city: ASC }]` (unguarded). Worker 1 should edit Spec line 1041 to substitute `city` for `name` at final verification. Resolution paths: (a) edit the spec quiet-half example to `city`; (b) accept the build-pass divergence and leave the spec as-is with a corresponding note in the build artifact (less clean).
- **Escalated (Worker 1 ownership): Spec line 127 / 1044-1045 14-vs-15 count over-count (Worker 1's planning-pass note).** Spec test plan enumerates 15 distinct test names; Decision 13 + the Implementation-plan row pin "14 tests total". Build-pass resolution: combine the two M7 no-op tests (`_empty_list_passes_through` + `_null_direction_skips_field`) into one combined test (`test_library_branches_order_empty_list_and_null_direction_no_op`) with named subassertions. Worker 1 should harmonize Spec test plan lines 1044-1045 into one bullet at final verification.
- **Escalated (Worker 1 ownership): Tests 1, 4, 8 collide with `BranchOrder` permission gates (Worker 2's build-pass discovery).** Tests 9/11 require `BranchOrder.check_name_permission` and `BranchOrder.check_shelves_permission` to be declared permanently on the orderset; Tests 1 (`name: ASC`), 4 (`shelves: { code: ASC }`), and 8 (originally `name: DESC`) use the same gated fields/branches with anonymous context, which would denial-fire before the actual contract executes. Build-pass resolution: Tests 1 and 4 use `_post_graphql_as_staff`; Test 8 substitutes `city: DESC` for `name: DESC`. Resolution paths Worker 1 should consider at final verification: (a) edit Spec lines 1031, 1034, 1038 to mark Tests 1, 4 as staff-context AND change Test 8's order field; (b) move the `check_*_permission` declarations off the shipped `BranchOrder` into test-local orderset declarations specific to Tests 9/10/11 (requires a different test setup pattern). Worker 3 concurs with Worker 2's recommendation: Option (a) is the smaller surface change and matches the build-pass resolution; the gates remain inspectable as load-bearing for Tests 9/10/11 and the shipped `BranchOrder` carries them permanently rather than via test-local rewiring.
- **Confirmed: `BookOrder.Meta.fields` coexistence works (Worker 1's planning-pass note, resolved at build).** Worker 1 raised this as a planning-time uncertainty; Worker 2's build-pass confirms `["id", "title", "subtitle", "circulation_status", "shelf__code"]` + explicit `shelf = RelatedOrder("ShelfOrder", field_name="shelf")` coexist cleanly on the same input type. Tests 3, 7, 8, 12 use the nested `shelf: { code: ASC }` surface; Test 13 uses the flat `shelfCode: ASC` surface; all six pass. No further spec edit needed.

Worker 3 raises no NEW spec-reconciliation items beyond the four above. The diff matches the spec's letter under Worker 1's planning-pass reconciliations and Worker 2's build-pass adjustments.

### Review outcome

`review-accepted`. Every spec-required behavior is reflected in the diff or has a recorded build-pass resolution that Worker 1 will weigh at final verification. The two new pure-class-definition files (`orders.py`, `orders_genre.py`) mirror the filter side one-for-one with the spec-justified divergences pinned. The schema wiring is additive on top of the filter side (filter wiring preserved; order wiring layered on). All 14 tests pass and pin the right contracts. No High / Medium / Low findings remain unresolved; the four spec-reconciliation escalations under `### Notes for Worker 1` are Worker 1's call at final verification per the BUILD.md spec-reconciliation flow.

---

## Final verification (Worker 1)

- Spec slice checklist: all three verbatim Slice-4 sub-bullets at `### Spec slice checklist (verbatim)` ticked `- [x]` — (1) `orders.py` + `orders_genre.py` containing the five `OrderSet` classes plus `GenreOrder` cross-module fixture landed verbatim per Worker 1's plan with the two spec-justified divergences (no `queryset=` on `RelatedOrder`; no custom-validator surface on `PatronOrder`); (2) `schema.py` carries `Meta.orderset_class` on every relevant `DjangoType` plus the `order_by:` argument on the six in-scope root resolvers in the canonical `<Type>.get_queryset → <Type>Filter.apply_sync → <Type>Order.apply_sync` chain; (3) exactly 14 new live HTTP tests in `test_library_api.py` cover every spec-named contract (verified via `grep -c '^def test_library\|^def test_root_get\|^def test_order_check' examples/fakeshop/test_query/test_library_api.py | head` and direct test-list inspection).
- DRY check across this slice and prior accepted slices: no new duplication. `orders.py` / `orders_genre.py` are textbook one-for-one mirrors of `filters.py` / `filters_genre.py` with the Filter→Order substitution and the two spec-justified divergences. `schema.py` adds two imports + five `Meta.orderset_class` lines + six resolver `order_by:` arguments — additive on top of the filter wiring, no shared-helper extraction needed (the per-resolver chain is intentionally per-type-explicit per Worker 3's DRY-finding rationale). `test_library_api.py` reuses `_post_graphql`, `_post_graphql_as_staff`, `_assert_graphql_data`, `CaptureQueriesContext`, `_reload_project_schema_for_acceptance_tests` verbatim; the two new module-level seed helpers (`_seed_branches_with_varying_shelves`, `_seed_books_with_nullable_subtitles`) are load-bearing per Worker 1's plan. `scripts/review_inspect.py` re-ran during this verification on `examples/fakeshop/test_query/test_library_api.py` and `examples/fakeshop/apps/library/schema.py`; no new cross-slice repeated-literal candidates surfaced beyond the inline GraphQL query strings (intentional per the live-HTTP-test pattern).
- Existing tests still pass: `uv run pytest tests/orders/ tests/types/ examples/fakeshop/test_query/test_library_api.py examples/fakeshop/apps/library/tests/ --no-cov` — **414 passed, 2 skipped, 1 warning** in 9.37s. No `--cov*` flags. No regressions on the four prior accepted slices.
- Spec reconciliation: four spec edits made plus one artifact-hygiene tweak (see `### Spec changes made (Worker 1 only)` below). The four escalations from Worker 3's `### Notes for Worker 1 (spec reconciliation)` block have been disposed: (1) Spec line 1041 quiet-half input updated `name` → `city` (matching the shipped Test 11 quiet half); (2) Spec test-plan lines 1044-1045 collapsed to one combined bullet `test_library_branches_order_empty_list_and_null_direction_no_op` (matching the shipped combined test); (3) Spec lines 1031/1034/1038 amended with explicit staff-context / field-substitution narration for Tests 1/4/8 (Option A — smallest surface change matching the build-pass resolution; the `BranchOrder` gates stay shipped permanently on the orderset so Tests 9/10/11 see them as inspectable load-bearing declarations rather than test-local rewirings); (4) `BookOrder.Meta.fields` coexistence verified at build, no spec edit. Also harmonized: spec slice sub-bullet at line 127, Implementation-plan Slice-4 row at line 966, and Decision 13 capability list at line 942 — all three named the M7 pair as two separate tests and are now consistent with the combined-test count of 14. Status-line header at spec line 4 updated to reflect Slices 3 and 4 shipped. The stale trailing `Status: planned` line at the artifact's verbatim-checklist-block tail was removed during this pass as artifact hygiene per the dispatch prompt's explicit license.
- Final status: `final-accepted`.

### Summary

Slice 4 shipped the live HTTP coverage half of the Ordering subsystem: two new fakeshop modules (`orders.py` + `orders_genre.py`) carrying six `OrderSet` declarations (`BranchOrder` / `ShelfOrder` / `BookOrder` / `LoanOrder` / `PatronOrder` + cross-module `GenreOrder`), `Meta.orderset_class` wiring on six library `DjangoType` classes, `order_by:` arguments on the six in-scope root resolvers (chained as `<Type>.get_queryset → <Type>Filter.apply_sync → <Type>Order.apply_sync` per Spec Decision 8 step ordering), and exactly 14 new live HTTP tests in `test_library_api.py` covering every Spec test-plan contract — scalar ASC, scalar DESC_NULLS_LAST on `Book.subtitle`, forward-FK nested ordering, reverse-FK denormalized multiplicity, M2M absolute-import-path resolution, filter+order composition under the lower-case `available` enum, optimizer cooperation under `assertNumQueries`, root `get_queryset` honoring (visibility before order), split-pair active-input-only scalar permission gates, active-related-branch relation-level permission gate, multi-field priority via list-element ordering, flat-shorthand `shelfCode` path, and the combined empty-list + null-direction no-op edge cases. Nothing under `django_strawberry_framework/` was touched. All 414 focused tests pass.

### Spec changes made (Worker 1 only)

- `docs/spec-028-orders-0_0_8.md` line 4 (status header) — updated from "Slices 1 (Foundation) and 2 (Factories) shipped (2026-06-01); Slices 3-6 still pending" to reflect Slices 3 and 4 also shipped per the spec status-line re-verification rule. Triggered by: Slice 4 final-verification (the rule fires at every Worker 1 spawn, and the prior pass had not yet rolled in Slice 3 final-acceptance plus Slice 4 closure).
- `docs/spec-028-orders-0_0_8.md` line 127 (Slice 4 sub-bullet 3, test-plan summary) — empty-list / null-direction enumeration changed from naming two separate tests (`test_order_empty_list_passes_through` AND `test_order_null_direction_skips_field`) to one combined test (`test_library_branches_order_empty_list_and_null_direction_no_op` exercising both halves). Triggered by: the spec body's prior 15-bullet enumeration over-counted Decision 13's pinned 14 tests; the build-pass combined the two M7 no-ops into one test function with named subassertions, so the spec sub-bullet now matches the shipped surface.
- `docs/spec-028-orders-0_0_8.md` lines 1031 / 1034 / 1038 (Slice 4 test plan, Tests 1 / 4 / 8) — each test bullet extended with an explicit narration that (a) Tests 1 and 4 are issued via the staff client (`_post_graphql_as_staff`) because `BranchOrder.check_name_permission` / `check_shelves_permission` are declared permanently on the shipped orderset for Tests 9/10/11 and anonymous context would denial-trigger them; (b) Test 8 orders by `city: DESC` (not `name: DESC`) because the visibility-before-order contract is the test's load-bearing observation and staff bypasses the visibility hook. Triggered by: Worker 2's build-pass discovery (recorded under `### Notes for Worker 1 (spec reconciliation)`) — Tests 1/4/8 collide with the permanently-declared `BranchOrder` gates that Tests 9/10/11 need. Option A (the smallest surface change, matching the build-pass resolution) was chosen over Option B (test-local orderset rewiring) per Worker 3's concurrence; the gates stay shipped on `BranchOrder` so they remain inspectable load-bearing declarations.
- `docs/spec-028-orders-0_0_8.md` line 1041 (Slice 4 test plan, Test 11 quiet half) — the quiet-half re-issue input changed from `orderBy: [{ name: ASC }]` to `orderBy: [{ city: ASC }]`. Triggered by: Worker 1's planning-pass discovery + Worker 2's build-pass confirmation — the `name` input would denial-trigger `BranchOrder.check_name_permission` from Tests 9/10's split-pair coverage, so the quiet half must use an unguarded scalar. `city` carries no `check_*_permission` gate on `BranchOrder` and `BranchType.get_queryset` hides `city="restricted"` rows by exclusion (not by raising), so the H3 contract (quiet when the `shelves` branch is absent AND no other gated field is named) is preserved.
- `docs/spec-028-orders-0_0_8.md` lines 1044-1045 (Slice 4 test plan, M7 no-op edge cases) — two separate bullets (`test_order_empty_list_passes_through` AND `test_order_null_direction_skips_field`) collapsed into one combined bullet (`test_library_branches_order_empty_list_and_null_direction_no_op`) exercising both halves via two query bodies in one test function. Triggered by: the spec body enumerated 15 distinct test names while Decision 13 + the Implementation-plan row pinned "14 tests total"; the over-count was in the M7 bundle. The combined test matches the shipped surface and brings the spec body's enumeration to 14 to match Decision 13's count.
- `docs/spec-028-orders-0_0_8.md` line 942 (Decision 13 body, capability list) — the M7 no-op bullet rewritten from "**two no-op edge-case tests** — `orderBy: []` empty-list pass-through + `orderBy: [{ name: null }]` null-direction skip" to "**one combined no-op edge-case test** — `test_library_branches_order_empty_list_and_null_direction_no_op` exercising both halves". Triggered by: harmonizes Decision 13's enumeration with the spec body's combined bullet at line 1044 and the Implementation-plan row at line 966.
- `docs/spec-028-orders-0_0_8.md` line 966 (Implementation plan Slice-4 row, new-tests cell) — the M7 enumeration changed from "empty-list no-op `orderBy: []` (per M7 of rev1) / null-direction no-op `orderBy: [{ name: null }]` (per M7 of rev1)" to "combined empty-list + null-direction no-op `orderBy: []` AND `orderBy: [{ name: null }]` in one test (per M7 of rev1, combined per Worker 1 Slice-4 final-verification reconciliation so the test count matches Decision 13's '14 tests total' pin)". Triggered by: same M7-combined-test harmonization.
- **Artifact hygiene (NOT a spec edit, recorded here per the dispatch prompt's explicit license):** removed the stale trailing `Status: planned` line at the bottom of `### Spec slice checklist (verbatim)` block in `docs/builder/bld-slice-4-live_http.md`. The line was a leftover template marker from Worker 1's planning-pass that should have been pruned when Worker 2 set the top-level `Status: built`. Worker 3 flagged it as a Low finding but their scope did not permit the edit; the dispatch prompt explicitly authorizes Worker 1 to clean it up during final verification.
- **`BookOrder.Meta.fields` coexistence verified, no spec edit.** Worker 1's planning-pass flagged this as a planning-time uncertainty: would the flat-shorthand path-entry `"shelf__code"` (rendering as `shelfCode: Ordering`) collide with the explicit `RelatedOrder("ShelfOrder", field_name="shelf")` declaration (rendering as `shelf: ShelfOrderInputType`) on the same `OrderSet`? Worker 2 and Worker 3 both confirmed the two surfaces coexist cleanly on the same input type — Tests 3 / 7 / 8 / 12 use the nested `shelf: { code: ASC }` surface, Test 13 uses the flat `shelfCode: ASC` surface, all six pass. The Spec Edge case "`Meta.fields = '__all__'`" override-by-same-name contract correctly licenses this coexistence; no spec amendment needed.
