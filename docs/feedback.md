# spec-033 build review — round 3 (live-coverage lens, 2026-06-13)

Re-review after commit `41164269` ("Refactor spec-033 documentation: update revision history
and reconcile strictness-message vocabulary"). This pass (1) verifies the two round-2
residuals are closed and (2) audits spec-033 **test placement against the coverage rule in
[`examples/fakeshop/test_query/README.md`](../examples/fakeshop/test_query/README.md)** —
*"Any coverage line in `django_strawberry_framework/` that can be earned by a real `/graphql/`
query against the fakeshop schema MUST be earned here … only fall back to the package-internal
`tests/` tree when the path is genuinely unreachable from a live request."* Working tree clean;
`41164269` is docs-only, so the mechanism (rounds 1–2) is unchanged.

## Verdict

**Round-2 residuals N1 and N2 are resolved.** Measured against the README's live-HTTP-first
rule, spec-033 coverage is mostly compliant: the headline nested-connection behaviors are
earned live, and the package-only placements that the spec calls out (plan/cache internals,
strictness, the `.distinct()` fallback) are *genuinely* unreachable from the current fakeshop
schema — a correct use of the fallback clause. There is **one real gap (G1, MED): the "both"
shape — a list relation and its connection sibling selected together — is consumer-visible and
expressible live, but only package-tested.** Two lower items follow. None is a correctness bug;
the cut is not blocked, but G1 is the one worth closing to hold `test_query/` to its mandate.

## Round-2 residuals — verified closed

- **N1 (resolved).** The Slice-4 checklist (spec line 77) now reads "parameterized with an
  explicit connection probe kind, a `to_attr` probe, **the relation field name**, and a
  fallback-reason message." `rg "generated field name"` over the spec returns nothing — the F2
  reconciliation is now complete and internally consistent.
- **N2 (resolved).** Revision history is ordered **1, 2, 3, 4** (spec lines 13–16).

## Test placement vs the live-HTTP-first coverage rule

The spec's own Test plan already encodes the README rule (its "Live-first (Slices 5–6)" vs
"Package-only where live is genuinely unreachable" split, spec ~lines 460-467). Audited
against the shipped suites:

### Correctly earned LIVE (honor the rule)

| Behavior | Live test (file:line) |
| --- | --- |
| Nested windowed fast path, fixed query count (parent-count-independent, `== 2`) | `test_nested_books_connection_fixed_query_count` — test_library_api.py:2928 |
| Nested `totalCount` from the window, no per-parent COUNT | `test_nested_total_count_no_per_parent_count` — test_library_api.py:2988 |
| Visibility-filtered nested window (`BookType.get_queryset`) | `test_nested_window_respects_book_visibility` — test_library_api.py:3063 |
| Reverse-FK nested connection fixed count (products) | `test_products_categories_items_connection_fixed_query_count` — test_products_api.py:669 |
| Nested sidecar `filter:`/`orderBy:` (per-parent fallback path) | `test_book_genres_connection_sidecars_and_total_count` — test_library_api.py:2773 |

### Correctly PACKAGE-ONLY (genuinely unreachable — consistent with the fallback clause)

- **`.distinct()` fallback `totalCount`** (`tests/test_relay_connection.py::test_distinct_target_fallback_reports_correct_total_count`, in-process synthetic schema). No fakeshop *connection target* distincts — the only `.distinct()` in fakeshop is `apps/kanban/schema.py` `all_kanban_board_doc_kinds`, a **root list** resolver over a non-Relay-Node type (no synthesized connection). Earning this live would require *adding a `.distinct()`-ing relation target to fakeshop* — a schema change, not a test move — so package placement is the correct fallback. (The spec scoped exactly this: "a live pin to Slice 5 **if** any library/products target distincts.")
- **Strictness `"raise"`/`"warn"`** (Slice 4 package tests). `examples/fakeshop/config/schema.py:38` builds `DjangoOptimizerExtension()` with no strictness arg (default `off`), so the raise/warn paths cannot fire over `/graphql/`. Package-only is correct; the spec says so.
- **Plan-object / `diff_plan_for_queryset` / cache-key-identity assertions** (Slices 1/3). You cannot inspect an `OptimizationPlan` or a cache key over HTTP; these are inherently package-internal.

### Gaps under the rule

#### G1 [MED] The "both" shape is consumer-visible and live-expressible, but only package-tested

`GenreType.books` is simultaneously a list relation field **and** the parent of a synthesized
`booksConnection`. The spec's Edge-cases section (spec line ~433) and User-facing API treat
selecting both together as a supported, load-bearing shape — the list field returns the full
related set, the connection returns the windowed page, and the package's `to_attr` isolation
(Decision 4) exists precisely so the two `Prefetch`es don't collide into Django's
"lookup already seen" error. Yet:

- The only test of this coexistence is `tests/optimizer/test_walker.py::test_both_shape_connection_to_attr_coexists_with_list_and_consumer_prefetch` (line 2842), which asserts on the **plan object** + `diff_plan_for_queryset`. The plan-object assertion is correctly package-only — but the **consumer-visible behavior** (both siblings resolve, no duplicate-prefetch error, list = full set / connection = windowed page) has **no live `/graphql/` test**.
- It is fully expressible against the current schema — e.g. `allLibraryGenres { books { title } booksConnection(first: 2) { edges { node { title } } } }` — with no schema change. Per the README ("MUST be earned here … the *first* place to add a test"), this behavior should be earned live.
- The spec under-specifies it too: Slice 5's DoD (spec items 8) and live deliverables list the fixed-count / totalCount / visibility pins but **not** a live "both"-shape pin, so the gap traces back to the test plan, not just the implementation.

**Recommend:** add one live test to `test_library_api.py` selecting a list relation and its
connection sibling on the same parent, asserting both resolve with correct, distinct results
(and, ideally, a query-count pin showing the window + the list prefetch coexist). Cheap, and it
closes the clearest README-rule violation in the card.

#### G2 [LOW] The live harness cannot send GraphQL variables, so variable-driven nested pagination is never live

`_post_graphql(query, *, client=None)` (test_library_api.py:77, test_products_api.py:79) takes
no `variables=` argument, so every live query uses literal pagination (`first: 2`). The
"variable drives the nested window" behavior is therefore exercised only in-process
(`test_window_slice_from_variables`, the Slice-3 cache-key tests). The cache-keying assertions
are legitimately package-internal, and the literal-paginated live tests cover the same
`derive_connection_window_bounds` line — so this is a harness limitation broader than spec-033,
not a spec-033 hole. **Optional:** add a `variables=` parameter to `_post_graphql` and one live
variable-paginated nested-connection test, which would also serve future cards.

#### G3 [LOW — note] Nested ambiguous-empty fallback (`first: 0` / overshot `after:`) is not live

`first: 0` is pinned live only at the **root** connection (`test_genre_connection_first_zero_empty_edges`, test_library_api.py:2250); the **nested** ambiguous-empty fast-path→fallback (a consumer-visible parity behavior) is package-only (`test_fast_path_first_zero_falls_back_*`). The spec did not scope a nested ambiguous-empty live pin, so this is arguably intentional, but it is expressible live and would round out the nested-connection live matrix. Lowest priority.

## Re-checks (clean)

- `41164269` is docs-only (`git show --stat`): spec revision-history reorder + the one
  strictness-vocabulary phrase. No package source, no test logic changed. Rounds 1–2 mechanism
  and test verifications stand.
- The round-2 fixes (F3 SQL-bound assertion, F4 `delta` assertion, F5 distinct fan-out test)
  remain correctly placed under the README rule: F3/F4 assert plan internals (package-correct),
  and F5's distinct path is genuinely unreachable live (package-correct, per above).

## Net assessment

Build-ready; N1/N2 closed. The card is consistent with the `test_query/` coverage rule
**except G1** — the "both"-shape coexistence is a consumer-visible, live-expressible behavior
currently earned only at the plan-object level. Closing it is a one-test addition to
`test_library_api.py` and would make the live suite honor its own "MUST be earned here"
mandate for the last unexercised nested-connection shape. G2/G3 are optional polish (a harness
enhancement and an out-of-scope-but-expressible nested case). Nothing here blocks the joint
`0.0.9` cut.
