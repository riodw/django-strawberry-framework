# Build: Slice 4 — Live HTTP coverage

Spec reference: `docs/spec-016-list_field-0_0_7.md` (lines 142-145 — Slice 4 checklist; Decision 4 spec lines 520-540 + rev3 M6 two-fold framing at line 534; Decision 9 spec lines 632-652 + rev4 H3 "Card-text departure" at line 644; rev2 M1 history at spec line 16; rev2 M2 history at spec line 17; rev4 H3 history at spec line 39; rev6 L2 scaffold-TODO sweep at spec line 65; rev6 M6 `assertNumQueries(N)` exact-count discipline at spec line 63; Test plan extend block at spec lines 754-766; Definition of done items 5 + 6 at spec lines 833-834)
Status: final-accepted

## Plan (Worker 1)

### DRY analysis

Slice 4 is a two-file slice: one production-shape edit to `examples/fakeshop/apps/library/schema.py` (add a new sibling root field; remove the scaffold TODO) and one test edit to `examples/fakeshop/test_query/test_library_api.py` (add a new HTTP test; remove the file-level scaffold TODO). The production source surface lives in `django_strawberry_framework/` and is unchanged by this slice — the symbol under test is `DjangoListField`, shipped under Slice 1 and validated/test-pinned by Slices 2 and 3. Slice 4's job is to prove the end-to-end contract (URL routing + view + schema execution + JSON serialization + optimizer cooperation) through a real `/graphql/` HTTP request, per `AGENTS.md` line 9 ("Test through real usage").

- **Existing patterns reused.**
  - The eight `@strawberry.field` resolvers in `examples/fakeshop/apps/library/schema.py:106-136` all share a one-line `return models.X.objects.order_by("id")` shape. The new `all_library_branches_via_list_field` field replaces that three-line pattern with a single-line attribute declaration: `all_library_branches_via_list_field: list[BranchType] = DjangoListField(BranchType)`. The contrast is the readable point of the example — pinning a position adjacent to the existing `all_library_branches` at `schema.py:106-108` makes the contrast visible at glance (and is what the scaffold TODO at `schema.py:86-104` already pre-positions). Worker 2 places the new field directly above the existing `all_library_branches` resolver, at the site where the scaffold TODO sits today (the TODO block is removed in the same edit per rev6 L2).
  - The HTTP test pattern in `examples/fakeshop/test_query/test_library_api.py` uses `django.test.Client` via the `_post_graphql(query)` helper at lines 95-101 (POSTs to `/graphql/` with `content_type="application/json"`), `_assert_graphql_data(query, expected)` at lines 104-108 for response-shape pinning, and `CaptureQueriesContext(connection)` at lines 244-271 (`test_library_optimizer_selects_book_shelf_in_http_query`), 278-314 (`test_library_reverse_fk_and_m2m_prefetch_sql_shape_over_http`), 378-409 (`test_library_consumer_prefetched_queryset_cooperates_with_optimizer_over_http`), 419-477 (`test_library_optimizer_hints_are_observable_over_http`), and 485-522 (`test_library_relation_override_shapes_http_response_data`) for query-count + SQL-shape assertions. The new test reuses these helpers exactly — no new helper extraction.
  - The `_seed_branch_with_two_shelves(name)` seed helper at lines 89-92 creates one `Branch` with two `Shelf` rows (`code="A-1"`, `code="B-2"`). The new test seeds two branches via two calls to this helper (mirroring `test_library_relation_override_shapes_http_response_data` at lines 482-483, which seeds `"Override"` and `"Override East"`). Worker 2 reuses the helper verbatim — no new seed inline.
  - The autouse `_reload_project_schema_for_acceptance_tests` fixture at lines 43-69 re-imports `apps.library.schema` and `config.schema` between tests. Because Worker 2 adds the new root field to `apps.library.schema.Query` (not a new module), the reload fixture picks up the new field automatically with no fixture changes. The reload pattern doc-anchor is `docs/TREE.md:457-459` (per the spec Test plan at line 766); Slice 4 follows the existing pattern unchanged.
  - `CaptureQueriesContext(connection)` + `assert len(captured) == N` is the file-local query-count discipline at lines 244, 267 (1 query), 278, 309 (3 queries), 378, 403 (2 queries), 419, 443 (2 queries), 448, 474 (3 queries), 485, 522 (4 queries). The pytest-django `django_assert_num_queries` fixture is NOT used in this file; Worker 2 MUST match the file-local `CaptureQueriesContext` + `len(captured)` shape rather than introducing the pytest-django fixture (the spec at line 762 cites "`assertNumQueries` / SQL-sniffer pattern" generically, but the file's actual pattern is `CaptureQueriesContext`; following the file's pattern keeps the test grep-stable with its siblings).
  - The `assertNumQueries(N)` exact-count discipline pinned in Slice 3 (rev6 M6 — `tests/test_list_field.py::test_djangolistfield_at_root_position_is_optimized` asserts exact `assertNumQueries(2)`) carries forward to Slice 4 as the same falsifiability bar: the test asserts `len(captured) == N` for an exact integer N, NOT `len(captured) <= N` or a tolerant range. The derivation for N lives in the test docstring so a future maintainer who reshapes the selection can recompute N deterministically.
  - The closest sibling for the new test's assertion shape is `test_library_relation_override_shapes_http_response_data` at lines 480-522 — that test issues `{ allLibraryBranches { name shelves { code } } }` against the existing `all_library_branches` resolver (whose `order_by("id")` provides deterministic ordering) and asserts `len(captured) == 4` for two seeded branches (1 root SELECT + 1 planned prefetch + 1 consumer-override-manager query per branch × 2 branches = 4). The new test's selection shape is structurally identical except (a) the field name is the new `allLibraryBranchesViaListField`, (b) the selection adds `id` columns inline (`{ id name shelves { id code } }` per the scaffold TODO at `schema.py:102` and the spec Test plan at line 760), and (c) the new field has no `order_by("id")` so the assertion is order-agnostic (sort by `id` before comparison).

- **New helpers justified.** None. The two existing helpers (`_post_graphql`, `_assert_graphql_data`, `_seed_branch_with_two_shelves`) plus `CaptureQueriesContext` cover every assertion shape Slice 4 needs. Worker 2 MUST NOT introduce a `_assert_graphql_data_unordered(query, expected_rows_by_id)` helper for this slice — the order-agnostic comparison is a one-line sort on the response payload at the single new test site; extracting it would be premature for a one-call-site abstraction.

- **Duplication risk avoided.** Four near-copies a naive Slice 4 implementation could introduce:
  1. **Inlining a seed call instead of reusing `_seed_branch_with_two_shelves`.** Avoided: the plan pins reuse of the existing seed helper at lines 89-92, matching `test_library_relation_override_shapes_http_response_data`'s precedent at lines 482-483.
  2. **Re-deriving the `assertNumQueries(N)` derivation in the test body instead of documenting it in the docstring.** rev6 M6 (spec line 63) requires the derivation in the docstring so a future maintainer who changes the selection shape can recompute N deterministically; Slice 4 inherits the same discipline. The plan pins the docstring shape below.
  3. **Adding the new field to `__all__` in `apps.library.schema`.** Avoided: `apps.library.schema` re-exports only `("Query",)` at `schema.py:139` (the `Query` class composes the root fields). The new field is a class attribute on `Query`; no `__all__` update is needed, and Worker 2 MUST NOT widen the example app's public surface.
  4. **Re-implementing the optimizer-cooperation contract in the HTTP test (asserting `ctx.dst_optimizer_plan.prefetch_related == ("shelves",)`-style assertions against an in-process schema).** Decision 4's two-fold framing (rev3 M6, spec line 534) explicitly separates the **return-shape** contract (package-internal `tests/test_list_field.py::test_djangolistfield_at_root_position_is_optimized` — already shipped in Slice 3 with `assertNumQueries(2)`) from the **end-to-end** contract (this Slice 4 HTTP test). The Slice 4 test asserts the *observable* SQL shape via `CaptureQueriesContext` + `len(captured) == 4` + per-query SQL substring checks (e.g. `"library_branch" in captured[0]["sql"]`, `"library_shelf" in captured[1]["sql"]`); it does NOT reach into `ctx.dst_optimizer_plan` (that is Slice 3's job). The duplication is intentional and the regression risks are distinct (Slice 3 catches "did we accidentally return a list?"; Slice 4 catches "does the live HTTP path still wire through the optimizer?").

- **Static inspection helper.** Ran during this planning pass against both Slice 4 files:
  - `uv run python scripts/review_inspect.py examples/fakeshop/apps/library/schema.py --output-dir docs/shadow --stdout` — overview at `docs/shadow/examples__fakeshop__apps__library__schema.{overview.md,stripped.py}`. Confirms HEAD line anchors: 24 symbols total; 8 `@strawberry.field` resolvers on `Query` at lines 107-108 / 111-112 / 115-116 / 119-120 / 123-124 / 127-128 / 131-132 / 135-136 (each carries `order_by("id")` on its line + 1); one TODO at line 86 (the spec-016 Slice 4 scaffold block spanning lines 86-104 with the proposed `all_library_branches_via_list_field` field and rev6 L2 cleanup target); 0 control-flow hotspots; 4 imports; `BranchType` at lines 61-71 with a consumer-override `shelves` resolver at lines 64-67 (`return list(self.shelves.order_by("-code"))`) — this is the resolver that drives the per-Branch override query in the assertNumQueries derivation below.
  - `uv run python scripts/review_inspect.py examples/fakeshop/test_query/test_library_api.py --output-dir docs/shadow --stdout` — overview at `docs/shadow/examples__fakeshop__test_query__test_library_api.{overview.md,stripped.py}`. Confirms HEAD shape: 16 symbols (10 tests + 6 helpers); 6 control-flow hotspots all in test bodies (none requiring refactor for this slice — the new test will be a 7th hotspot of similar shape and is acceptable); 0 TODO comments in the executable body (the file-level docstring at lines 3-26 carries the Slice 4 scaffold TODO and is the rev6 L2 cleanup target); the existing repeated-string-literals scan shows 8 `"Speculative"`, 3 `"Override"`, 3 `"Override East"` — Worker 2 may pick new seed names that do not collide with these (the scaffold proposes the existing `_seed_branch_with_two_shelves` helper's defaults). Confirms NO `django_assert_num_queries` / `assertNumQueries` usage anywhere in the file — the canonical query-count discipline is `CaptureQueriesContext(connection)` + `assert len(captured) == N`. Walks every "calls of interest" entry — 7 `len()` calls at lines 267, 309, 403, 443, 474, 522, 561, all in `assert len(captured) == N` or `assert len(genres) == N` shape; the new test adds one more `len(captured) == 4` assertion and matches this convention. Helper run for `apps/library/models.py` SKIPPED with reason "read-only reference; `grep -n` already confirmed `Branch.shelves` reverse-FK relation at `models.py:56-60` is the relation under the nested-selection test (related_name='shelves' on `Shelf.branch` FK to `Branch`)."

### Implementation steps

Slice 4 ships two file edits in one slice. Line numbers below are pin-at-write-time navigational hints; Worker 2 must re-verify against HEAD before editing — Slice 3 shipped `tests/test_list_field.py` changes but did not touch either Slice 4 file, so HEAD anchors for both files should be stable since the scaffold TODOs were written.

#### Step 1 — Add the new root field to `examples/fakeshop/apps/library/schema.py`

1. Add the import `from django_strawberry_framework import DjangoListField, DjangoType, OptimizerHint` at `schema.py:7` (extend the existing import; alphabetical insert of `DjangoListField` BEFORE `DjangoType` — `D`-prefix tie-broken on `L < T`). Spec citation: spec line 117 — Slice 1 already added the public export; Slice 4 only imports it at the consumer site.
2. Add the new root field as the FIRST entry on the `Query` class, positioned at the scaffold-TODO site (`schema.py:86-104`). The field declaration is `all_library_branches_via_list_field: list[BranchType] = DjangoListField(BranchType)` per spec line 143 (verbatim) and the scaffold TODO at `schema.py:95-97`. Place the line directly above the existing `@strawberry.field def all_library_branches(self) -> list[BranchType]` resolver at `schema.py:106-108` so the contrast (one-line declaration vs three-line resolver) is visible at glance per Decision 9 (spec lines 632-642). Multi-line shape (matching the scaffold TODO's pre-formatted block):
   ```python
   all_library_branches_via_list_field: list[BranchType] = DjangoListField(
       BranchType,
   )
   ```
   The trailing comma is mandatory per `AGENTS.md` line 17 (COM812: trailing comma on multi-arg calls expands the layout and locks it in). Spec citation: spec lines 142-143 (Slice 4 checklist bullet 1); Decision 9 at spec lines 632-642 (justification for the add-only, adjacent placement); rev4 H3 "Card-text departure" at spec line 644 (the new field is ADDED, not replacing any existing resolver).
3. Remove the entire scaffold TODO block at `schema.py:86-104` (the comment lines starting `# TODO(spec-016, Slice 4 — Decision 9 add-only posture, rev2 M1 + rev4 H3):` through the closing comment at line 104). Spec citation: spec line 145 (Slice 4 checklist bullet 3); rev6 L2 history at spec line 65 (Ruff's `ERA001` catches commented-out code but not `# TODO:` markers; explicit cleanup is mandatory).
4. Do NOT modify any of the eight existing `@strawberry.field def all_library_*` resolvers at `schema.py:106-136` — strict ADD-only posture per rev2 M1 (spec line 16) and Decision 9 (spec lines 632-642). Their `order_by("id")` calls are depended on by `test_library_relation_override_shapes_http_response_data` (`test_library_api.py:481-522`) and other HTTP tests in the file.
5. Do NOT add `BranchType.get_queryset` to `examples/fakeshop/apps/library/schema.py`. Spec line 144 + rev2 M2 (spec line 17): adding a real `BranchType.get_queryset` would mutate every `BranchType` path in the schema (including nested `book → shelf → branch` selections and `test_library_branch_shelf_book_loan_graph_over_http` at `test_library_api.py:116-177` and `test_library_relation_override_shapes_http_response_data` at `test_library_api.py:481-522`). The `get_queryset`-cooperation coverage for `DjangoListField` lives entirely in package-internal `tests/test_list_field.py` (shipped in Slice 3).
6. Do NOT modify the prose docstring at `schema.py:1` or the comment block at `schema.py:9-13`. Spec line 642's "prose comment near the top of `schema.py` should be updated" wording is a Slice-5 doc-update concern (it lands in `docs/GLOSSARY.md` / `TODAY.md` / `KANBAN.md` per spec lines 768-802), not Slice 4. Slice 4 is strictly a schema change + scaffold-TODO removal; the prose-doc updates are Slice 5's contract.

#### Step 2 — Add the new HTTP test to `examples/fakeshop/test_query/test_library_api.py`

1. Remove the file-level scaffold TODO block at `test_library_api.py:3-26` (the multi-paragraph block inside the module docstring describing the planned `test_library_branches_via_djangolistfield_optimized_nested_selection` test). The module docstring's leading line (`"""Live GraphQL HTTP tests for the library acceptance app."""` at line 1) and the closing `"""` at line 27 remain; only the TODO body between them is removed. Spec citation: spec line 145 (Slice 4 checklist bullet 3); rev6 L2 history at spec line 65.
2. Add a new test method `test_library_branches_via_djangolistfield_optimized_nested_selection` at the position immediately after `test_library_relation_override_shapes_http_response_data` (currently lines 480-522), BEFORE the `_decode_global_id` helper at line 525. Worker 2 inserts the new test as a sibling to the existing `*_relation_override_*` test because both touch `Branch.shelves` traversal — co-location aids future maintainers grepping `Branch` HTTP tests. The new test name is taken verbatim from the spec Test plan at line 758 (`test_library_branches_via_djangolistfield_optimized_nested_selection`) — Worker 2 MUST NOT shorten or rename it (the spec name is the contract).
3. The test body follows this shape (Worker 2 lands the exact code; the structure below is the plan-time pin):
   ```python
   @pytest.mark.django_db
   def test_library_branches_via_djangolistfield_optimized_nested_selection():
       """End-to-end pipeline coverage for ``DjangoListField`` via ``/graphql/``.

       Pins the Slice 4 end-to-end contract (spec Decision 4 + rev3 M6, spec line
       534): URL routing + view + schema execution + JSON serialization + optimizer
       cooperation through the real Django + Strawberry HTTP stack. The package-
       internal return-shape contract is pinned separately by
       ``tests/test_list_field.py::test_djangolistfield_at_root_position_is_optimized``
       (rev2 M3, spec line 532).

       Query count derivation (rev6 M6, spec line 63 — exact ``assertNumQueries(N)``):
       - 1 SELECT for the ``Branch`` root queryset (the ``DjangoListField`` default
         resolver returns ``Branch._default_manager.all()``; the root-gated
         ``DjangoOptimizerExtension`` plans ``prefetch_related("shelves")`` for
         the nested ``shelves`` selection).
       - 1 SELECT for the planned ``prefetch_related("shelves")`` prefetch
         (loads all ``Shelf`` rows for the two seeded branches).
       - 2 SELECTs (one per seeded ``Branch``) for the consumer-override
         ``BranchType.shelves`` resolver at ``apps/library/schema.py:64-67``
         (``return list(self.shelves.order_by("-code"))``), which re-evaluates
         the relation manager and bypasses the prefetch cache. This mirrors the
         baseline established by ``test_library_relation_override_shapes_http_response_data``
         at ``test_library_api.py:481-522`` for the same selection shape.

       Total: 1 + 1 + 2 = 4 queries. If a future maintainer adds ``order_by`` to
       the new field, removes the consumer override on ``BranchType.shelves``, or
       changes the seeded branch count, recompute N accordingly.
       """
       _seed_branch_with_two_shelves("ListField West")
       _seed_branch_with_two_shelves("ListField East")

       with CaptureQueriesContext(connection) as captured:
           response = _post_graphql(
               """
               query {
                 allLibraryBranchesViaListField {
                   id
                   name
                   shelves { id code }
                 }
               }
               """,
           )

       assert response.status_code == 200
       payload = response.json()
       assert "errors" not in payload, payload
       branches = payload["data"]["allLibraryBranchesViaListField"]
       # Order-agnostic comparison: the new field has no ``order_by`` (rev2 M1 —
       # the add-only posture deliberately does NOT inherit ``order_by("id")``
       # from the sibling ``all_library_branches`` resolver because the new field
       # exercises the default-resolver code path, not a consumer resolver).
       branches_by_name = {b["name"]: b for b in branches}
       assert set(branches_by_name) == {"ListField West", "ListField East"}
       for branch in branches_by_name.values():
           assert {shelf["code"] for shelf in branch["shelves"]} == {"A-1", "B-2"}
       assert len(captured) == 4
   ```
4. Use new seed names `"ListField West"` and `"ListField East"` (NOT `"Override"` / `"Override East"`) so the new test cannot collide with `test_library_relation_override_shapes_http_response_data`'s seed names if the two tests are ever co-run inside the same transaction. The `_seed_branch_with_two_shelves` helper at lines 89-92 takes a single `name: str` argument; Worker 2 calls it twice with the two new names.
5. The query string MUST select `id` on both `Branch` and `Shelf` per the spec Test plan at line 760 (`{ allLibraryBranchesViaListField { id name shelves { id code } } }`). Selecting `id` exercises the FK-id elision path on the nested `shelves` selection (the optimizer plans the relation without a join on the `id`-only sub-selection), which is a sibling regression net to `tests/test_list_field.py::test_djangolistfield_fk_id_elision_survives` (spec line 750) — Slice 3's coverage is in-process; this Slice 4 coverage is end-to-end.
6. The assertion `assert len(captured) == 4` is the exact-count discipline pinned by rev6 M6 (spec line 63). NO `<= 4` or range form. The derivation in the docstring (4 = 1 + 1 + 2) makes the count falsifiable: a future refactor that drops the consumer-override on `BranchType.shelves` would change the count to 2, a refactor that loses the optimizer plan would change the count to 3 (the 2 override queries plus 1 root SELECT, with the prefetch dropped), and either shift would be caught by the exact assertion.
7. Do NOT add SQL substring assertions (e.g. `assert "library_branch" in captured[0]["sql"]`) beyond the existing precedent. Looking at sibling tests in the file: `test_library_optimizer_selects_book_shelf_in_http_query` adds 3 substring checks; `test_library_reverse_fk_and_m2m_prefetch_sql_shape_over_http` adds 4; `test_library_consumer_prefetched_queryset_cooperates_with_optimizer_over_http` adds 4. Worker 2 SHOULD include 2-4 SQL substring checks for grep stability — recommended set: `assert "library_branch" in captured[0]["sql"]`, `assert "library_shelf" in captured[1]["sql"]`, and on the per-Branch override queries `assert "library_shelf" in captured[2]["sql"]` + `assert "library_shelf" in captured[3]["sql"]`. The exact set is at Worker 2's discretion within the SQL-shape-sniffer convention this file already establishes (see Implementation discretion items below).

### Test additions / updates

- **New live HTTP test**: `examples/fakeshop/test_query/test_library_api.py::test_library_branches_via_djangolistfield_optimized_nested_selection`. Spec name pinned at spec line 758; assertion shape pinned above; query string pinned at spec line 760. The test asserts (a) the response data contains both seeded branches (order-agnostic comparison by name → set), (b) each branch has the expected two shelves (order-agnostic comparison by code → set), (c) `len(captured) == 4` exact (rev6 M6 discipline), with the N derivation documented in the docstring per the rev6 M6 contract.
- **No package-internal tests added.** Slice 3 owns the `tests/test_list_field.py` coverage; Slice 4 does NOT add package-internal tests. The `cls.get_queryset` cooperation coverage is in `tests/test_list_field.py` (Slice 3); the root-position optimizer-cooperation contract is pinned by `test_djangolistfield_at_root_position_is_optimized` (Slice 3). Worker 2 MUST NOT pull Slice 3 coverage forward into Slice 4 or duplicate it here — the two-fold framing (Decision 4 + rev3 M6, spec line 534) is load-bearing.
- **rev6 L2 scaffold-TODO sweep at both touched sites.** Slice 4 removes (a) the multi-line scaffold TODO block at `examples/fakeshop/apps/library/schema.py:86-104` and (b) the file-level scaffold TODO block at `examples/fakeshop/test_query/test_library_api.py:3-26`. The Slice 5 docs sweep handles `KANBAN.md` / `TODAY.md` / `GLOSSARY.md` / etc. separately; Slice 4's L2 sweep is scoped to the two touched source/test files only.

### Implementation discretion items

The following choices are at Worker 2's discretion within the constraints already pinned by the plan and the spec:

- **The exact set of SQL-substring assertions appended to the `len(captured) == 4` check.** The plan recommends 2-4 substring assertions in the `assert "<table>" in captured[N]["sql"]` shape, but the exact set (which captured indices to check, which table names to assert against) is at Worker 2's discretion within the precedent set by `test_library_optimizer_selects_book_shelf_in_http_query` (3 substrings), `test_library_reverse_fk_and_m2m_prefetch_sql_shape_over_http` (4 substrings), and `test_library_consumer_prefetched_queryset_cooperates_with_optimizer_over_http` (4 substrings). Worker 2 picks the shape that best documents the per-query SQL story.
- **The exact docstring wording** beyond the rev6 M6-mandated query-count derivation. The docstring MUST include the derivation (1 + 1 + 2 = 4 with the per-line justification) so a future maintainer can recompute N; Worker 2 may rephrase the surrounding context for clarity but MUST keep the derivation intact.
- **Whether to include a `payload = response.json(); assert "errors" not in payload, payload` guard** in addition to the `assert response.status_code == 200` check. The file's existing tests use both shapes (`_assert_graphql_data` checks via `response.json() == {"data": ...}` exact match; `test_library_relay_node_global_id_round_trips` at line 559 uses the `"errors" not in payload, payload` shape with a helpful failure message). The plan recommends the `errors not in payload` shape because the order-agnostic comparison makes the response-equality form unsuitable, but Worker 2 may pick either as long as Strawberry execution errors are surfaced before the data assertions run.
- **The blank-line spacing around the new test method.** Match the file's existing convention (two blank lines between top-level test functions per `ruff format`'s output).

**NOT discretionary (called out for emphasis):**
- The new field name `all_library_branches_via_list_field` — spec-pinned at line 143.
- The test method name `test_library_branches_via_djangolistfield_optimized_nested_selection` — spec-pinned at line 758.
- The query string shape `{ allLibraryBranchesViaListField { id name shelves { id code } } }` — spec-pinned at line 760.
- The file paths `examples/fakeshop/apps/library/schema.py` and `examples/fakeshop/test_query/test_library_api.py` — spec-pinned at line 144.
- The ADD-only posture (Worker 2 MUST NOT replace any existing `all_library_*` resolver) — rev2 M1 + Decision 9 + rev4 H3 (spec lines 16, 39, 142-143, 644).
- The exact `assert len(captured) == 4` count — rev6 M6 (spec line 63) requires exact assertion, not a tolerant bound; the derivation in the docstring is the falsifiability anchor.
- The omission of any `BranchType.get_queryset` modification — rev2 M2 (spec line 17) explicitly forbids it for this slice.
- The use of `django.test.Client` POSTing to `/graphql/` (the file's existing pattern via `_post_graphql`) — `AGENTS.md` line 9's "test through real usage" rule + the file's reload pattern at `docs/TREE.md:457-459` are both load-bearing.
- The use of `CaptureQueriesContext(connection)` + `len(captured)` (the file's existing pattern) rather than `django_assert_num_queries` (pytest-django fixture). The file does NOT use `django_assert_num_queries` anywhere; following the file's actual convention keeps the new test grep-stable with siblings.
- The non-modification of the prose docstring at `schema.py:1` or the example-app `TODAY.md` line (Slice 5 owns those edits per spec lines 768-802).

### Spec slice checklist (verbatim)

- [x] **Add a new** root field — `all_library_branches_via_list_field: list[BranchType] = DjangoListField(BranchType)` — to `examples/fakeshop/apps/library/schema.py` (rev2 M1; do NOT replace the existing `all_library_branches` because its `order_by("id")` is depended on by `test_library_relation_override_shapes_http_response_data`). The other seven `@strawberry.field` resolvers stay unchanged.
- [x] Add a new HTTP test in `examples/fakeshop/test_query/test_library_api.py` (or extend an existing test in the same file) asserting: (a) the new field returns the expected branches via `/graphql/`, (b) the optimizer planned `prefetch_related` / `select_related` correctly for a nested selection (via `assertNumQueries` / the existing SQL-sniffer pattern). The `cls.get_queryset` cooperation coverage lives in the package-internal `tests/test_list_field.py` tests (rev2 M2 — adding a real `BranchType.get_queryset` filter would mutate every `BranchType` path in the library schema and is out of scope here).
- [x] Remove the spec-016 scaffold TODOs at this site (rev6 L2) — covers `examples/fakeshop/apps/library/schema.py` and `examples/fakeshop/test_query/test_library_api.py`.

---

## Build report (Worker 2)

### Files touched

- `examples/fakeshop/apps/library/schema.py` — added `DjangoListField` to the existing top-level package import (alphabetical: `DjangoListField, DjangoType, OptimizerHint`); added the new root field `all_library_branches_via_list_field: list[BranchType] = DjangoListField(BranchType,)` as the FIRST entry on the `Query` class (immediately above the existing `all_library_branches` resolver) so the one-line declaration sits adjacent to the three-line resolver per Decision 9 (spec lines 632-642); removed the scaffold TODO block at the same site per rev6 L2. No existing `all_library_*` resolver was touched (rev2 M1 + rev4 H3 — strict ADD-only); `BranchType.get_queryset` was deliberately NOT added (rev2 M2).
- `examples/fakeshop/test_query/test_library_api.py` — removed the file-level scaffold TODO block from the module docstring (rev6 L2; only the multi-paragraph TODO body between the opening and closing triple quotes was removed; the surviving docstring is the single-line `"""Live GraphQL HTTP tests for the library acceptance app."""`); added the new test `test_library_branches_via_djangolistfield_optimized_nested_selection` immediately after `test_library_relation_override_shapes_http_response_data` and before `_decode_global_id`. The new test reuses the existing `_post_graphql`, `_seed_branch_with_two_shelves`, and `CaptureQueriesContext(connection)` helpers verbatim — no new helper extracted.

### Tests added or updated

- `examples/fakeshop/test_query/test_library_api.py::test_library_branches_via_djangolistfield_optimized_nested_selection` — pins the Slice 4 end-to-end contract (Decision 4 + rev3 M6): seeds two `Branch` rows with two `Shelf` rows each via `_seed_branch_with_two_shelves("ListField West")` + `_seed_branch_with_two_shelves("ListField East")`, POSTs `{ allLibraryBranchesViaListField { id name shelves { id code } } }` against `/graphql/`, asserts (a) `response.status_code == 200`, (b) `"errors" not in payload`, (c) order-agnostic name-set comparison `{"ListField West", "ListField East"}`, (d) per-branch shelf-code set `{"A-1", "B-2"}`, (e) exact `assert len(captured) == 4` per rev6 M6 (derivation in the docstring: 1 root Branch SELECT + 1 `prefetch_related("shelves")` SELECT + 2 consumer-override-manager SELECTs from `BranchType.shelves` resolver = 4), and (f) four SQL-substring sniffer checks (`"library_branch"` in `captured[0]`; `"library_shelf"` in `captured[1]`, `captured[2]`, `captured[3]`) to pin the per-query table story.

### Validation run

- `uv run ruff format .` — passed (`103 files left unchanged`; the COM812 conflict-with-formatter warning is pre-existing repo config noise, not caused by this slice's edits).
- `uv run ruff check --fix .` — passed (`All checks passed!`).
- `git status --short` — listed every modified file with classification:
  - `M examples/fakeshop/apps/library/schema.py` — **slice-intended** (Step 1).
  - `M examples/fakeshop/test_query/test_library_api.py` — **slice-intended** (Step 2).
  - `?? docs/builder/bld-slice-4-live_http_coverage.md` — **slice-intended** (Worker 1's planning artifact; this build report appended to it; will become tracked at maintainer commit time).
  - `M AGENTS.md` — **inherited maintainer state; out of Slice 4 scope** (concurrent maintainer edit, not reverted).
  - `M docs/builder/bld-slice-3-optimizer_get_queryset_tests.md` — **inherited maintainer state; out of Slice 4 scope** (prior-slice artifact carried over, not touched in this pass).
  - `M docs/builder/build-016-list_field-0_0_7.md` — **inherited maintainer state; out of Slice 4 scope** (build-plan checklist owned by Worker 0; not touched by Worker 2).
  - `M docs/spec-016-list_field-0_0_7.md` — **inherited maintainer state; out of Slice 4 scope** (active spec; only Worker 1 may edit, and Worker 2 must not).
  - `M tests/test_list_field.py` — **inherited maintainer state; out of Slice 4 scope** (Slice 3 deliverable; Slice 4 does not add package-internal tests per the spec).
  No unrelated tool churn. The worker-memory file `docs/builder/worker-memory/worker-2.md` will be appended to after this report and is gitignored.
- `uv run pytest --no-cov examples/fakeshop/test_query/test_library_api.py` — **10 passed in 0.28s** (all 9 pre-existing tests plus the new `test_library_branches_via_djangolistfield_optimized_nested_selection`).
- `uv run pytest --no-cov tests/test_list_field.py tests/base/test_init.py` — **25 passed in 2.12s** (Slices 1/2/3 still green: 21 `test_list_field.py` tests + 4 `tests/base/test_init.py` tests).

### Implementation notes

- **Field position in `schema.py`.** Placed `all_library_branches_via_list_field` as the FIRST entry on `Query` (immediately above the existing `all_library_branches` resolver) per Worker 1's plan step 2 — the scaffold TODO already pre-positioned the new field at this site, so removing the TODO and dropping the new declaration in its place keeps the one-line-vs-three-line contrast visible at glance with `all_library_branches`. The declaration uses the multi-line `DjangoListField(BranchType,)` shape with the trailing comma (COM812 mandatory per `AGENTS.md` line 17).
- **Import shape.** Extended the existing single-line `from django_strawberry_framework import DjangoType, OptimizerHint` to `from django_strawberry_framework import DjangoListField, DjangoType, OptimizerHint` (alphabetical: `D` < `D` < `O`, with `L` < `T` breaking the `D` tie). No second import line; ruff did not flag.
- **Test method position.** Inserted the new test immediately after `test_library_relation_override_shapes_http_response_data` and before `_decode_global_id` — both tests touch `Branch.shelves` traversal, so the co-location helps future maintainers grepping the `Branch` HTTP coverage. The blank-line spacing follows ruff format's two-blank-line convention between top-level functions.
- **Seed-helper reuse.** Used the existing `_seed_branch_with_two_shelves(name)` helper at lines 89-92 (the same helper used by `test_library_relation_override_shapes_http_response_data` at lines 482-483). Chose seed names `"ListField West"` and `"ListField East"` rather than `"Override"` / `"Override East"` to avoid any future collision if the two tests are ever co-run inside the same transaction. The `"A-1"` / `"B-2"` shelf codes the helper creates are reused verbatim in the assertion's set comparison.
- **Docstring N derivation wording.** Followed Worker 1's plan-pinned docstring wording verbatim for the rev6 M6 derivation (`1 + 1 + 2 = 4`), reformatted to a bullet list (using `*` markers) so the per-query justification reads cleanly under the rST-friendly docstring conventions the rest of the file uses. The derivation explicitly names what would change N if a future maintainer modifies the field, the override, or the seed count — the falsifiability anchor that rev6 M6 demands.
- **Order-agnostic comparison.** Compared via `branches_by_name = {b["name"]: b for b in branches}` + `set(branches_by_name) == {...}` and per-branch `{shelf["code"] for shelf in branch["shelves"]} == {"A-1", "B-2"}` — set semantics make the assertion order-agnostic per rev2 M1 (the new field has no `order_by`, so the result row ordering is non-deterministic at the SQL level). Chose this shape over a sort-by-id list-equality because the new field's response includes the (non-stable) `id` column inline; a set-based comparison stays robust to future seed-id shifts.
- **SQL-substring sniffer set.** Included four substring checks (`"library_branch"` in `captured[0]`, then `"library_shelf"` in `captured[1]`, `captured[2]`, `captured[3]`) — within the 2-4 range Worker 1's plan recommended and matching the per-query SQL story (the root Branch query plus the three downstream shelf queries: 1 planned prefetch + 2 consumer-override re-evaluations).
- **`assert "errors" not in payload, payload` over `_assert_graphql_data`.** Picked the `errors not in payload` shape from `test_library_relay_node_global_id_round_trips` precedent (line 559) over the `_assert_graphql_data` shape from the rest of the file. The order-agnostic comparison rules out the exact-equality form `_assert_graphql_data` uses; using `_assert_graphql_data` would force a fixed JSON shape that the non-deterministic ordering would break.

### Notes for Worker 3

- The new field is **strict ADD-only** adjacent to `all_library_branches`; the eight existing `@strawberry.field` resolvers (`all_library_branches`, `all_library_shelves`, `all_library_books`, `all_library_prefetched_books`, `all_library_genres`, `all_library_patrons`, `all_library_membership_cards`, `all_library_loans`) are untouched. Verify by `git diff -- examples/fakeshop/apps/library/schema.py`: the diff should show one new import token (`DjangoListField`), one new field declaration block, and the scaffold-TODO removal; nothing else.
- `BranchType.get_queryset` was deliberately NOT added per rev2 M2 (spec line 17). Adding a real `BranchType.get_queryset` would have mutated every `BranchType` path in the schema and broken sibling tests including `test_library_branch_shelf_book_loan_graph_over_http` and `test_library_relation_override_shapes_http_response_data`. The `get_queryset` cooperation coverage for `DjangoListField` lives entirely in Slice 3's package-internal `tests/test_list_field.py` tests.
- The new test's docstring derives N per rev6 M6: 1 root Branch SELECT + 1 `prefetch_related("shelves")` SELECT + 2 consumer-override SELECTs from `BranchType.shelves` (which calls `self.shelves.order_by("-code")` and bypasses the prefetch cache) = 4. This mirrors the baseline established by `test_library_relation_override_shapes_http_response_data` for the same nested-selection shape.
- The order-agnostic assertion uses set semantics on both the branch-name level and the shelf-code level per rev2 M1 (the new field has no `order_by`; the response row ordering is non-deterministic).
- No new helpers were extracted; the four SQL-substring assertions are within the 2-4 range Worker 1's plan recommended and follow the per-query SQL story.
- No package-internal tests added (Slice 3 owns those); no `tests/` files touched by this slice's diff (the `M tests/test_list_field.py` in `git status --short` is inherited maintainer state from Slice 3).
- No shadow files used during the build pass (Worker 1's planning shadow output is referenced for line anchors but not re-generated by Worker 2).

### Notes for Worker 1 (spec reconciliation)

No spec reconciliation needed. Implementation landed verbatim against the plan's pins: field name, test name, query string shape, file paths, ADD-only posture, exact `len(captured) == 4` assertion, and rev6 M6 docstring derivation all matched the spec verbatim.

---

## Review (Worker 3)

### High:

None.

### Medium:

None.

### Low:

None.

### DRY findings

- None new. The slice reuses `_post_graphql`, `_seed_branch_with_two_shelves`, and `CaptureQueriesContext(connection)` verbatim per the plan; no helper was extracted, no seed call was hand-rolled, no parallel SQL-sniffer plumbing was introduced. The new test's `len(captured) == 4` derivation explicitly cites and mirrors `test_library_relation_override_shapes_http_response_data`'s baseline (`test_library_api.py:455-496`), so the two tests carry the same per-query story without duplicating the rationale text. The chosen seed names `"ListField West"` / `"ListField East"` deliberately avoid the existing `"Override"` / `"Override East"` strings so the per-test fixture stays grep-distinguishable from its sibling.

### Public-surface check

`git diff HEAD -- django_strawberry_framework/__init__.py` is empty. No change to `__all__` or the re-export list. Slice 4 ships zero public-surface change; `DjangoListField` was already exposed in Slice 1, and the example app's `apps.library.schema.__all__ = ("Query",)` at `examples/fakeshop/apps/library/schema.py:123` is unchanged (no widening of the example app's public surface).

### CHANGELOG sanity

Not applicable; slice did not modify `CHANGELOG.md`.

### Documentation / release sanity

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces. The `examples/fakeshop/apps/library/schema.py` prose-comment update mentioned at spec line 642 is a Slice 5 doc-update concern per the plan's Step 1 sub-item 6 and the spec's Slice 5 checklist at spec lines 146-156; Slice 4 correctly defers it.

### Static inspection helper

Skipped for both touched files. Recorded reason:

- `examples/fakeshop/apps/library/schema.py` — net diff is `+3 / -19` per `git diff --stat HEAD`; new logic is one import-line extension + one three-line attribute declaration. Well under the 30-line threshold for files inside `django_strawberry_framework/` and the 50-line threshold for files outside it (the threshold this file falls under).
- `examples/fakeshop/test_query/test_library_api.py` — net diff is `+70 / -22` per `git diff --stat HEAD`; the new test method is 62 lines including a 27-line docstring, a 9-line GraphQL query literal, 5 comment lines, and only about 21 lines of executable logic (seed calls, `CaptureQueriesContext` block, GraphQL POST, set-comparison assertions, exact-count assertion, four SQL-substring checks). Under the 50-line threshold for files outside `django_strawberry_framework/`. Worker 1's planning pass already ran the helper against both files (artifact lines 29-31 cite the shadow output at `docs/shadow/examples__fakeshop__apps__library__schema.{overview.md,stripped.py}` and `docs/shadow/examples__fakeshop__test_query__test_library_api.{overview.md,stripped.py}`); review pass relies on the planning-pass output rather than re-running.

### What looks solid

- **Strict ADD-only adjacency.** `git diff HEAD -- examples/fakeshop/apps/library/schema.py` shows exactly three change tokens: the import extension at line 7 (`DjangoListField` inserted alphabetically before `DjangoType`), the scaffold-TODO block removal at the prior lines 86-104, and the new three-line `all_library_branches_via_list_field: list[BranchType] = DjangoListField(BranchType,)` declaration in the freed-up position. The eight existing `@strawberry.field` resolvers (`all_library_branches`, `all_library_shelves`, `all_library_books`, `all_library_prefetched_books`, `all_library_genres`, `all_library_patrons`, `all_library_membership_cards`, `all_library_loans`) at `schema.py:90-120` are untouched. Decision 9's add-only posture and rev4 H3's "Card-text departure" land cleanly; rev2 M1's resolver-determinism dependency on `order_by("id")` is preserved across the whole file.
- **`BranchType.get_queryset` correctly absent.** `grep -n "get_queryset" examples/fakeshop/apps/library/schema.py` returns no matches. Rev2 M2's "adding a `BranchType.get_queryset` would mutate every `BranchType` path" constraint is honored at the source level.
- **rev6 L2 scaffold-TODO sweep is clean at both sites.** `grep -n "TODO: spec-016\|TODO(spec-016" examples/fakeshop/apps/library/schema.py examples/fakeshop/test_query/test_library_api.py` returns no matches; the schema scaffold (former lines 86-104) and the test-file scaffold (former lines 3-26 of the module docstring) are both gone, replaced by their landed implementations and the single-line module docstring respectively.
- **Falsifiable exact-count assertion with derivation in the docstring (rev6 M6).** `assert len(captured) == 4` at `test_library_api.py:556` is the exact-integer form rev6 M6 requires; the docstring at lines 510-526 derives the count as `1 root Branch SELECT + 1 planned prefetch_related("shelves") SELECT + 2 consumer-override BranchType.shelves SELECTs = 4` and explicitly names what would shift N (adding `order_by` to the new field, removing the consumer override on `BranchType.shelves`, or changing the seeded branch count). A future maintainer who reshapes the selection can recompute N without rediscovering the rationale.
- **Order-agnostic comparison via set semantics.** The new field carries no `order_by` (rev2 M1 — deliberately not inheriting `order_by("id")` because the new field exercises the default-resolver code path, not a consumer resolver). The assertion uses `branches_by_name = {b["name"]: b for b in branches}` + `set(branches_by_name) == {"ListField West", "ListField East"}` + per-branch `{shelf["code"] for shelf in branch["shelves"]} == {"A-1", "B-2"}` — robust to any SQL-level row-ordering shift on `Branch._default_manager.all()`. An explicit comment at lines 548-551 names the rev2 M1 anchor so the set-comparison shape isn't drift-magnet.
- **File-local `CaptureQueriesContext` discipline preserved.** The test does not introduce `pytest-django`'s `django_assert_num_queries` fixture (which is not used anywhere in this file); it follows the same `with CaptureQueriesContext(connection) as captured: ... assert len(captured) == N` shape used by every sibling test in the file (`test_library_optimizer_selects_book_shelf_in_http_query`, `test_library_reverse_fk_and_m2m_prefetch_sql_shape_over_http`, `test_library_consumer_prefetched_queryset_cooperates_with_optimizer_over_http`, `test_library_optimizer_hints_are_observable_over_http`, `test_library_relation_override_shapes_http_response_data`). Grep-stable with siblings.
- **SQL-substring sniffer set is right-sized.** Four substring assertions (`"library_branch" in captured[0]["sql"]`, then `"library_shelf" in captured[1..3]["sql"]`) pin the per-query table story: root Branch SELECT first, then the planned `prefetch_related("shelves")` SELECT, then the two consumer-override re-evaluations. Within the 2-4 range Worker 1's plan recommended and matches the precedent set by `test_library_reverse_fk_and_m2m_prefetch_sql_shape_over_http` and `test_library_consumer_prefetched_queryset_cooperates_with_optimizer_over_http`.
- **Test placement co-locates `Branch.shelves` HTTP coverage.** The new test sits at `test_library_api.py:499-560`, immediately after `test_library_relation_override_shapes_http_response_data` (which also touches `Branch.shelves` traversal) and before the `_decode_global_id` helper at line 563. Future maintainers grepping `Branch` HTTP coverage land on the two tests adjacent.
- **Seed-helper reuse honors `AGENTS.md` line 8.** The library acceptance tests use inline `Model.objects.create` per `AGENTS.md` line 7's library-test exception, but this file already encapsulates the two-shelf-per-branch pattern as `_seed_branch_with_two_shelves(name)` at `test_library_api.py:63-66`; reusing it (rather than hand-rolling four `Branch.objects.create` + `Shelf.objects.create` calls) keeps the test in line with the file's existing convention and mirrors `test_library_relation_override_shapes_http_response_data`'s precedent at lines 456-457.

### Temp test verification

- No temp tests created under `docs/builder/temp-tests/slice-4/`. The diff and the existing test suite proved every behavior the review needed:
  - `uv run pytest --no-cov examples/fakeshop/test_query/test_library_api.py` → 10 passed in 0.26s (the 9 pre-existing live HTTP tests + the new `test_library_branches_via_djangolistfield_optimized_nested_selection`).
  - The exact-count derivation is reproduced by inspection of the captured-queries semantics already pinned by the sibling `test_library_relation_override_shapes_http_response_data` test, which uses the same `BranchType.shelves` consumer override.
- Disposition: not applicable; no temp tests created or left under `docs/builder/temp-tests/slice-4/`.

### Notes for Worker 1 (spec reconciliation)

No spec reconciliation needed; the diff lands the slice's contract verbatim and the spec wording matches the shipped behavior. One consideration for the final-verification pass (informational, not a finding):

- The exact `len(captured) == 4` count surfaces the consumer-override-manager pattern on `BranchType.shelves` (`return list(self.shelves.order_by("-code"))`) as the source of two extra SELECTs that bypass the planned `prefetch_related("shelves")` cache. Under the `AGENTS.md` root-cause-fix directive, the production-code-right shape would be to make `BranchType.shelves` cooperate with the optimizer's prefetch cache (e.g., consult `self._prefetched_objects_cache` before re-evaluating the manager). That is NOT a Slice 4 finding — the override pre-dates this card, its behavior is the documented baseline for `test_library_relation_override_shapes_http_response_data` (which has been live since the library app shipped), and refactoring it would mutate every `BranchType` path in the schema (the same blast-radius rev2 M2 cited against adding `BranchType.get_queryset`). The N=4 baseline is the right shape for Slice 4 to pin; the optimizer-cooperation refactor of the override resolver belongs to a separate spec/card that owns the cross-test blast radius. Surfacing it here so Worker 1 has the option to record it as deferred work in `bld-final.md`'s `### Deferred work catalog` if appropriate.

### Review outcome

`review-accepted`. Every spec sub-check at spec lines 142-145 is reflected in the diff: (1) the new root field `all_library_branches_via_list_field: list[BranchType] = DjangoListField(BranchType)` is added to `examples/fakeshop/apps/library/schema.py` with the existing seven `@strawberry.field` resolvers unchanged; (2) the new HTTP test `test_library_branches_via_djangolistfield_optimized_nested_selection` in `examples/fakeshop/test_query/test_library_api.py` asserts response data plus exact `assertNumQueries`-equivalent `len(captured) == 4` with the rev6 M6 derivation in the docstring; (3) the rev6 L2 scaffold-TODO sweep is clean at both touched sites. Public-surface check passes (no change to `__all__` or the package re-exports). Focused HTTP test sweep passes 10/10. Setting `Status: review-accepted` at the top of the artifact.

---

## Final verification (Worker 1)

- **Spec slice checklist**: every `- [ ]` in the Plan's `### Spec slice checklist (verbatim)` is now `- [x]`. All three sub-checks landed verbatim in the diff: (1) the new root field `all_library_branches_via_list_field: list[BranchType] = DjangoListField(BranchType,)` lands at the scaffold-TODO site in `examples/fakeshop/apps/library/schema.py` immediately above the existing `all_library_branches` resolver, with the eight `@strawberry.field def all_library_*` resolvers unchanged (rev2 M1 + Decision 9 + rev4 H3 ADD-only posture honored); (2) the new HTTP test `test_library_branches_via_djangolistfield_optimized_nested_selection` in `examples/fakeshop/test_query/test_library_api.py` asserts both response payload (set-based, order-agnostic) and the exact `len(captured) == 4` with the rev6 M6 derivation in the docstring, plus four SQL-substring sniffer checks pinning the per-query table story; (3) both scaffold-TODO blocks (the multi-line block at the prior `schema.py:86-104` and the file-level docstring block at the prior `test_library_api.py:3-26`) are removed cleanly — `grep -n "TODO(spec-016\|TODO: spec-016" examples/fakeshop/apps/library/schema.py examples/fakeshop/test_query/test_library_api.py` returns no matches. No silently un-ticked boxes; no deferrals required.
- **DRY check across this slice and prior accepted slices**: clean. The new field uses `DjangoListField(BranchType,)` verbatim — no re-implementation of the Slice 1 factory. The new HTTP test reuses `_post_graphql`, `_seed_branch_with_two_shelves`, and `CaptureQueriesContext(connection)` verbatim from the file's existing pattern (lines 244, 278, 378, 419, 448, 485). No `_assert_graphql_data_unordered`-style helper extracted (single call site; premature). No fresh `DjangoType` fixture rebuilt — `BranchType` is reused from the live library schema. The Worker 3 informational note about the `BranchType.shelves` consumer-override (`return list(self.shelves.order_by("-code"))`) bypassing the prefetch cache and contributing two extra SELECTs to the N=4 baseline is acknowledged but explicitly NOT escalated to a Slice 4 fix: under the `AGENTS.md` line 4 root-cause-fix directive, the highest-quality remedy is to make the override resolver consult `_prefetched_objects_cache` — but that override pre-dates this card, refactoring it would mutate every `BranchType` path in the schema (the same cross-test blast-radius rev2 M2 cited against adding `BranchType.get_queryset`), and Slice 4's contract is ADD-only. The N=4 baseline is the right shape for this card to pin; the override refactor belongs to a separate spec that owns the cross-test blast radius. Recorded in `### Spec changes made (Worker 1 only)` below as deferred-work input for `bld-final.md`'s `### Deferred work catalog`.
- **Existing tests still pass**:
  - `uv run pytest --no-cov examples/fakeshop/test_query/test_library_api.py` → **10 passed in 0.26s** (all 9 pre-existing tests plus the new `test_library_branches_via_djangolistfield_optimized_nested_selection`).
  - `uv run pytest --no-cov tests/test_list_field.py tests/base/test_init.py` → **25 passed in 2.12s** (Slice 3's 21 `test_list_field.py` tests still green; Slice 1's `__all__` pin in `tests/base/test_init.py::test_public_api_surface_is_pinned` still green).
  - No `--cov*` flags used; `--no-cov` only (opts out of `pytest.ini`'s auto-applied `--cov`).
- **Spec reconciliation**: no spec edits required for Slice 4. The implementation landed verbatim against the plan's pins — field name (spec line 143), test name (spec line 758), query string shape (spec line 760), file paths (spec line 144), ADD-only posture (rev2 M1 + Decision 9 + rev4 H3), exact `assertNumQueries(N)` discipline (rev6 M6 at spec line 63), and rev6 L2 scaffold-TODO sweep all matched the spec verbatim. The spec status line at line 4 (`draft (revision 6, post-rev5 scaffolding review)`) was re-verified at the start of this spawn and remains accurate.
- **Final status**: `final-accepted`. Setting `Status: final-accepted` at the top of the artifact.

### Summary

Slice 4 shipped the live HTTP coverage that proves the `DjangoListField` end-to-end contract through the real Django + Strawberry stack. The example library app now declares `all_library_branches_via_list_field: list[BranchType] = DjangoListField(BranchType,)` as a new root field on `Query` adjacent to the eight existing `@strawberry.field def all_library_*` resolvers (strict ADD-only per rev2 M1 + Decision 9 + rev4 H3 — none of the existing resolvers were modified), and `examples/fakeshop/test_query/test_library_api.py` gains one new HTTP test that POSTs `{ allLibraryBranchesViaListField { id name shelves { id code } } }` against `/graphql/` and pins (a) response-payload correctness via order-agnostic set semantics on both the branch-name and shelf-code levels, (b) exact `len(captured) == 4` with the rev6 M6 derivation (1 root Branch SELECT + 1 planned `prefetch_related("shelves")` SELECT + 2 consumer-override `BranchType.shelves` SELECTs) documented in the docstring, and (c) per-query SQL-substring sniffer checks for grep stability with the file's existing sibling tests. The rev6 L2 scaffold-TODO sweep at both touched sites lands cleanly. Decision 4's two-fold framing (rev3 M6) holds: Slice 3's package-internal `test_djangolistfield_at_root_position_is_optimized` pins the return-shape contract under `assertNumQueries(2)` against an isolated fixture; this Slice 4 HTTP test pins the end-to-end contract through URL routing + view + schema execution + JSON serialization + optimizer cooperation. Both regression nets are load-bearing and neither subsumes the other.

### Spec changes made (Worker 1 only)

No spec edits required for Slice 4.

Deferred-work catalog input for `bld-final.md` (Worker 1's responsibility at the final test-run gate):
- The `BranchType.shelves` consumer-override resolver at `examples/fakeshop/apps/library/schema.py` (the `return list(self.shelves.order_by("-code"))` body) bypasses the optimizer's planned `prefetch_related("shelves")` cache and contributes two extra SELECTs to every `Branch.shelves` HTTP-query baseline (visible as the `+2` in Slice 4's `len(captured) == 4` derivation and as the matching baseline in `test_library_relation_override_shapes_http_response_data` at the same selection shape). Under the `AGENTS.md` line 4 root-cause-fix directive, the highest-quality remedy is to make the override resolver consult `self._prefetched_objects_cache` before re-evaluating the relation manager. Out of scope for Slice 4 (ADD-only contract) and out of scope for Slice 5 (docs/promotion only). Belongs to a separate spec/card that owns the cross-test blast radius (the same blast radius rev2 M2 cited against modifying `BranchType` paths). Source artifact section: `## Review (Worker 3) → ### Notes for Worker 1 (spec reconciliation)` of this artifact.
