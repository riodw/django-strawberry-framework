# Test hardening plan: restore every claim the live-tier sweep thinned

Status: plan, not started
Owner: maintainer (Rio)
Executor: Gemini coordinator + parallel Gemini workers, one worker per work package

## Why this plan exists

Nineteen commits (`f54cf12d` .. `8d00f9f8`, all titled `test(<area>): move ... to the live tier`)
moved package tests under `tests/` to the live tier under `examples/fakeshop/test_query/`. An
independent eight-reader audit graded every deleted test against its live twin. Most twins are
equivalent or stronger. The items below are the exceptions: a claim that the deleted test pinned
and no surviving test pins, or a promoted live test whose control fixture cannot fail for the
reason its docstring gives.

Working assumption for this plan: every item CAN be made as strong as the original. A worker
that concludes otherwise stops on that item, writes why in its report, and continues with the rest
of its package. Nobody deletes, weakens, or skips a test to make an item "pass".

---

## 0. Mandatory reading, in this order, before touching anything

Every worker and the coordinator read these in full first. No exceptions, even if the prompt
that dispatched you seems complete.

1. `AGENTS.md` (35 numbered rules; rules 4, 15, 27, 32, 33, 34 govern this plan directly)
2. `START.md` (sections "Working with Rio", "Concurrent work", "Pre-commit and CI gates",
   "Markdown link convention", "Per-cycle scratch")
3. `GOAL.md`
4. `README.md` (package overview) and `docs/README.md` (docs map)
5. `examples/fakeshop/test_query/README.md` (the live-tier rulebook: rungs, what a live test must
   assert, the "failability" requirement, the suite map at the bottom)
6. `docs/TREE.md` (module map: find any file named below before opening it)
7. The section of this plan for your work package, then the git history of the test you are
   fixing: `git show <sha>^:<path>` gives the ORIGINAL deleted test verbatim. Read it in full.
   The original is the bar; you are restoring its claims.

Test-placement rules you must apply (from `AGENTS.md`):

- `tests/` = package tests (target is `django_strawberry_framework` itself).
- `examples/fakeshop/test_query/` = live tests, HTTP to `/graphql/` via `django.test.Client`
  (helpers `graphql_client.post_graphql`, `_post_graphql`, `AsyncTestClient`).
- `examples/fakeshop/tests/` = project/config-level tests (management commands via
  `call_command`).
- First line of every catalog/auth test: `seed_data(N)` or `create_users(N)` from
  `apps.products.services`. Library tests use inline `Model.objects.create(...)`.
- Source references in docstrings/comments: `path::QualifiedName`, never `path:NN`.
- No process provenance in code: no "audit", "grader", "restored", "sweep", "round 2",
  no mention of this plan or its filename, in any docstring, comment, test name, or commit text.
  State the invariant the test pins, nothing about how it came to exist.

---

## 1. Rules for every worker

Git and tree hygiene (violations are not recoverable by the coordinator, so read twice):

- NEVER commit. NEVER `git add`. NEVER create or switch branches. NEVER `git stash`,
  `git checkout -- <path>`, `git restore`, `git reset`. The maintainer commits.
- Other sessions work in this checkout concurrently. `git status` will show dirty files you did
  not touch. Leave them alone. Never revert or "tidy" them. If a file you own is already dirty
  when you start, diff it against `git show HEAD:<path>` into your scratch dir, report the fact,
  and continue: edit around the foreign hunks, never over them.
- Edit ONLY the files listed under your work package's "Files owned". If an item needs a file
  outside that list, stop that item and report; do not edit.
- After every edit: `uv run ruff format <file>` then `uv run ruff check --fix <file>` on the files
  you touched.
- Temp files, scratch copies, mutation scripts: ONLY under
  `/private/tmp/claude-501/-Users-riordenweber-projects-django-strawberry-framework/gemini-hardening/<WP-id>/`
  (create it). Never under the repo, never bare `/tmp`.
- Running tests: this plan authorizes focused runs ONLY, of the node ids you touched plus the
  module they live in:
  `uv run pytest <path>::<test> ... --no-cov -p no:cacheprovider -n0`
  Never run the whole suite. Never run with coverage. The coordinator does the integration run.
- Markdown files in `docs/` and the test_query README use reference-style links with the
  `<!-- LINK DEFINITIONS -->` block; if you add a row to the README suite map, follow the existing
  rows exactly.

Quality bar for every restored or hardened test:

- It must FAIL under a specific, named mutation of production code and PASS on the unmodified
  tree. You prove this with the recipe in section 2 and paste the result into your report.
- Package-side tests (under `tests/`) may call package internals directly. Live tests may not:
  they post a document and read the response, the captured SQL, or the database.
- Prefer restoring the original deleted test verbatim (from `git show <sha>^:<path>`) when the
  plan says "restore". Re-add any helper the original used that was deleted alongside it. Adjust
  imports. Do not "modernize" it.
- When the plan says "add one assertion", add exactly that; do not restructure the test.
- Each test name states the invariant. Do not encode history in the name.

Report format (one report per worker, written to your scratch dir as `report.md` and pasted back
to the coordinator): for each item, `DONE` / `BLOCKED (reason)`, the node ids added or changed,
the mutation used and the exact pytest summary line under mutation and after restore, and
`git diff --stat` of the files you touched.

---

## 2. Failability recipe (mandatory per item)

A mutation proof shows the test discriminates. It runs in a SCRATCH COPY of the working tree,
never in the shared checkout. Two traps, both fatal to the proof:

1. The scratch copy imports the REAL package unless `PYTHONPATH` puts the scratch tree first
   (the venv has an editable install of the repo). Always prefix `PYTHONPATH=<scratch>`.
2. `cd` inside a shell command can persist into your later commands. Use absolute paths.

Recipe:

```bash
REPO=/Users/riordenweber/projects/django-strawberry-framework
S=/private/tmp/claude-501/-Users-riordenweber-projects-django-strawberry-framework/gemini-hardening/<WP-id>
mkdir -p "$S" && rm -rf "$S/wt" && mkdir "$S/wt"
rsync -a --exclude .venv --exclude .git --exclude db.sqlite3 "$REPO/" "$S/wt/"
ln -s "$REPO/.venv" "$S/wt/.venv"
cat > "$S/wt/tests/test_zz_probe.py" <<'EOF'
def test_probe_scratch():
    import django_strawberry_framework as pkg
    assert pkg.__file__.startswith("/private/tmp/"), pkg.__file__
EOF
```

Then, per mutation: edit the named production file INSIDE `$S/wt/` (never in `$REPO`), run

```bash
cd "$S/wt" && PYTHONPATH="$S/wt" uv run --no-sync pytest -q -p no:cacheprovider -n0 --no-cov \
  tests/test_zz_probe.py <node ids the item names>
```

Run it as one command from `$S/wt` (the `cd` is inside the same command; do not rely on it
persisting). Expect: the probe passes, and EXACTLY the node ids the item names fail. Then
restore the production file in the scratch copy byte-for-byte (`rsync` it again from `$REPO`)
and re-run: everything passes. Paste both summary lines into your report. If the mutation does
NOT fail the target test, the item is not done: your assertion is not pinning the claim.

`--no-sync` stops `uv` from rebuilding the symlinked venv. The probe test is what proves the
scratch tree, not the real package, is under test; if it fails, stop and fix the environment
before trusting any mutation result.

---

## 3. Work packages

Packages are disjoint by file so they run in parallel. A worker touches only its "Files owned".
Two packages never own the same file. `WP-A` is the largest; dispatch it first.

Legend for each item: **Lost** = the claim the original pinned and nothing pins now. **Do** = the
exact change. **Mutation** = production edit that must fail the named test. **Verify** = commands.

### WP-A: `examples/fakeshop/test_query/test_library_api.py`

Files owned: `examples/fakeshop/test_query/test_library_api.py`,
`examples/fakeshop/apps/library/schema.py` (only if an item below says so),
`examples/fakeshop/test_query/README.md` (suite-map row for `test_library_api.py` only).

Helpers already in the module you will reuse: `_post_graphql` (imported as
`from graphql_client import post_graphql as _post_graphql`), `_seed_library_graph`,
`_sql_from_table`, `_post_async_shipped`, `global_id_for`, `project_schema_override` fixture,
`CaptureQueriesContext`.

#### A1. `test_library_genres_order_by_to_many_desc_applies_over_graphql_async` (from b8e7314e)

Lost: the control. Genres are named `Aardvark` and `Zebra` and the expected output is
`["Aardvark", "Zebra"]`, which is also plain name-ascending. An implementation that ordered
genres by their own `name` instead of `MAX(books.title) DESC` passes.

Do: rename the genres so name order and the expected `MAX(title) DESC` order DISAGREE. Keep the
books as they are (`Beta` on one genre, `Alpha` + `Zulu` on the other). Concretely: the genre
holding `Zulu` must sort LAST by name but FIRST in the result. Example: genre with books
`Alpha`+`Zulu` named `Zeta`; genre with book `Beta` named `Alpha`. Expected result is then
`["Zeta", "Alpha"]` (MAX titles `Zulu` > `Beta`), while name-ASC would give `["Alpha", "Zeta"]`
and pk order gives insertion order; create the `Zeta` genre SECOND so pk order also disagrees.
Update the docstring's control sentence to state all three orders that are ruled out (name ASC,
name DESC, pk).

Mutation: in `django_strawberry_framework/orders/sets.py::OrderSet._resolve_order_expressions`,
change the `aggregate = models.Min if direction.is_ascending else models.Max` line to
`aggregate = models.Min`. Expect this test AND
`test_library_books_order_by_to_many_desc_uses_max_aggregate` to fail. Second mutation: in the
same file, make `apply_async` return `queryset` unchanged instead of
`cls._apply_orderings(input_value, queryset)`. Expect only this test to fail.

#### A2. `test_library_force_select_book_hint_still_prefetches_when_book_is_hooked` (from 9031cb3d)

Lost: `_seed_library_graph` seeds no book with `circulation_status="repair"`, so the test cannot
tell whether `BookType.get_queryset` (which hides repair books from non-staff, see
`examples/fakeshop/apps/library/schema.py::BookType.get_queryset`) was applied to the downgraded
`Prefetch`. Only the select-vs-prefetch decision is pinned; the visibility half is vacuous.

Do: inside the `override_settings` block, after `_seed_library_graph()`, create a second book on
the same shelf with `circulation_status=models.Book.CirculationStatus.REPAIR` and a loan on it
for the seeded patron. Query `allLibraryLoans { book { title } }` as anonymous. Assert the
response lists the repair loan with `"book": None` (the loan row is visible, its book is hidden by
the prefetch queryset) AND that the captured `library_book` SQL (exactly one statement) contains
the repair exclusion, i.e. the string `repair` does NOT appear as a returned title and the book
SQL contains `circulation_status`. Keep every existing assertion.

If `Loan.book` is non-nullable on the wire and the framework returns an error instead of `null`
for a hidden non-null relation, assert THAT documented shape instead (check what
`test_library_api.py::test_library_optimizer_hints_are_observable_over_http` or the
visibility rows in `test_products_visibility_api.py` assert for a hidden FK target) and say so
in the docstring.

Mutation: in `django_strawberry_framework/optimizer/walker.py::_apply_hint`, in the
`if hint.force_select:` branch, change `prefer_prefetch=_target_has_custom_get_queryset(...)`
to `prefer_prefetch=False`. Expect this test to fail (it already does for the JOIN assertion; the
new assertion must also fail if you additionally leave the JOIN assertion out in the scratch copy
to confirm the visibility half discriminates on its own).

#### A3. `test_library_loans_deep_leaf_sql_shape_is_row_preserving` (from c527e75c, 9031cb3d)

Lost (original `tests/test_predicate_pg_explain.py::test_emitted_leaf_is_a_single_distinct_free_correlated_exists`
at `git show c527e75c^:tests/test_predicate_pg_explain.py`, and
`tests/optimizer/test_predicates.py::test_same_table_inner_aliasing_from_loan_root` at
`git show 9031cb3d^:tests/optimizer/test_predicates.py`): the outer query owns EXACTLY one
`EXISTS`, and the outer alias set is `{"library_loan"}` only. The live row checks
`FROM "library_loan"` once and `library_patron` absent before `WHERE`, so an added outer
`JOIN "library_book"` passes.

Do: add to the existing test: `assert sql.upper().count("EXISTS(") == 1`;
`assert "library_book" not in pre_where.lower()`; and `assert "JOIN" not in pre_where.upper()`.
Also assert the payload: the two seeded loans come back, each once
(`len(ids) == 2 and len(set(ids)) == 2`), because the row currently asserts no payload of its own.

Mutation: in `django_strawberry_framework/optimizer/predicates.py`, find where the correlated
`EXISTS` branch is composed and make it ALSO join the relation on the outer query (e.g. append
`.filter(book__isnull=False)` style traversal that forces an outer JOIN to `library_book`, or
`select_related("book")` on the outer queryset in the composing site in
`django_strawberry_framework/filters/sets.py` if predicates.py has no outer-queryset handle).
Expect this test to fail on the new `pre_where` assertion. Record which site you mutated.

#### A4. `test_unauthorized_book_genres_update_never_queries_m2m_membership_over_http` (from 8d00f9f8)

Lost (original `tests/rest_framework/test_resolvers.py::test_no_m2m_membership_query_runs_before_authorization`
at `git show 8d00f9f8^:tests/rest_framework/test_resolvers.py`): on the GRANTED path, the
membership snapshot IS taken (a through-table query happens) and it happens AFTER the permission
class ran. The live row proves only the denied path issues no through-table query.

Do: in the granted half (after `client.force_login(user)`), wrap the `allowed` POST in
`CaptureQueriesContext(connection)` and assert that at least one captured statement contains
`through_table` (the snapshot ran), AND that the FIRST captured statement containing
`through_table` comes AFTER the first captured statement containing `auth_permission` or
`auth_user_user_permissions` (the permission read). Use statement indexes in
`captured.captured_queries`. Update the docstring to name both halves.

Mutation: in `django_strawberry_framework/mutations/resolvers.py::run_write_pipeline_sync`,
immediately after `check_instance_write_alias(model, using, instance)` and BEFORE
`authorize_or_raise`, insert `for _m2m in model._meta.many_to_many: list(getattr(instance, _m2m.name).all())`.
Expect this test to fail on BOTH halves (denied path now queries; granted path order flips).

#### A5. Single-node missing row is `null`, and hidden-vs-missing cost parity (from ceef2344)

Lost (originals `tests/test_relay_node_field.py::test_node_missing_row_returns_null` and
`::test_node_null_paths_issue_equal_queries` at `git show ceef2344^:tests/test_relay_node_field.py`):
the SINGLE `node(id:)` field returns `null` for a well-formed id of a nonexistent row, and the
hidden-row and missing-row lookups issue the same number of `library_genre` queries. Only the
batch (`nodes`) form is live (`test_nodes_batch_mixed_types_order_and_null`,
`test_nodes_hidden_and_missing_issue_equal_per_table_queries`).

Do: add two live tests next to `test_node_hidden_row_null_live`:
`test_node_missing_row_null_live` (create one genre, delete it or use `pk + 1000`, build the id
with `global_id_for(GenreType, missing_pk)`, post `{ node(id: $id) { ... on GenreType { name } } }`
mirroring the query shape of `test_node_refetch_genre`, assert `data["node"] is None` and no
`errors`) and `test_node_hidden_and_missing_issue_equal_queries_live` (hidden = a genre the
shipped `GenreType.get_queryset` hides if one exists; otherwise use `BookType` with a repair book,
which `BookType.get_queryset` hides; capture both single-node posts and assert equal counts of
statements containing the target table). Read `test_nodes_hidden_and_missing_issue_equal_per_table_queries`
first and mirror its counting helper.

Mutation: in `django_strawberry_framework/types/relay.py::_resolve_node_default` (sync) make the
missing-row branch raise instead of returning `None`. Expect `test_node_missing_row_null_live`
to fail. Second mutation: make the hidden-row branch issue an extra existence query (e.g.
`model._base_manager.filter(pk=pk).exists()` before the visibility lookup). Expect the parity
test to fail.

#### A6. Nested-connection argument guards (from ceef2344)

Lost (originals `tests/test_relay_connection.py::test_relation_connection_first_overrun`,
`::test_relation_connection_stale_after_no_error`, `::test_relation_connection_first_and_last_rejected`
at `git show ceef2344^:tests/test_relay_connection.py`): the three guards on a NESTED connection.
Live rows `test_first_overrun`, `test_stale_after_cursor_no_error`,
`test_genre_connection_first_and_last_rejected` cover the ROOT spelling only.

Do: add three live tests over the shipped nested `booksConnection` under `allLibraryGenres`
(the shape `test_genre_books_connection_behavior` and
`test_nested_books_connection_has_next_page_without_edges` already use):
`test_nested_books_connection_first_overrun_clamps` (`first: 1000` on a genre with 3 books
returns all 3, `hasNextPage` false, no errors), `test_nested_books_connection_stale_after_is_not_an_error`
(take `endCursor` from a first page, delete every book, re-post with `after:` that cursor: empty
edges, no errors), `test_nested_books_connection_first_and_last_rejected` (`first: 1, last: 1`
yields a GraphQL error whose message matches the root row's expected message; copy the exact
assertion from `test_genre_connection_first_and_last_rejected`).

Mutation: in `django_strawberry_framework/connection.py`, find the `first`+`last` rejection and
disable it. Expect only the new first+last test (and its root sibling) to fail. Second mutation:
find the overrun clamp (the `max_results`/cap application in the nested slicing path) and remove
the clamp. Expect the overrun test to fail. Record the symbols you mutated.

#### A7. `test_library_prefetch_child_over_unrelated_table_is_refused_over_http` (from 02e266df)

Lost: the row asserts the masked generic envelope (`"An unexpected error occurred."`, `data is
None`), which any exception in the resolver satisfies. Nothing ties the live refusal to the seal.

Do: the shipped `/graphql/` mount masks the message by design, so sharpen it on a debug mount.
Mount a holder in this test module with the error policy's debug mode on, the way
`test_error_policy_api.py` mounts its holders (read that module's `urlpatterns` block and its
debug-mode row first), and post the same `branchNotes` query to it. Assert the unmasked error
message contains the seal's wording for an unrelated-table child: copy the exact substring that
`tests/utils/test_querysets.py::test_prefetch_child_over_unrelated_table_still_fails_for_proxy_target`
asserts at HEAD (read it; do not paraphrase; do not edit that file, it is not owned by WP-A).
Keep the existing masked assertion on `/graphql/`. If mounting a debug holder in this module
proves too invasive, report BLOCKED with the reason; do not weaken anything.

Mutation: in `django_strawberry_framework/utils/querysets.py`, make the unrelated-table check in
the prefetch-child seal a no-op (return the queryset instead of the defect). Expect the new
debug-holder test to fail (and the existing masked row may also change).

#### A8. README suite-map row

After A1..A7, extend the `test_library_api.py` row in the README suite map (bottom table) with a
short phrase per new claim (single-node missing `null` + parity, nested connection guards,
granted-path snapshot ordering). Keep the row one line; follow the existing style.

### WP-B: products live modules

Files owned: `examples/fakeshop/test_query/test_products_api.py`,
`examples/fakeshop/test_query/test_products_visibility_api.py`,
`examples/fakeshop/test_query/README.md` (suite-map rows for those two modules only).

#### B1. `test_update_item_via_form_malformed_id_is_field_error_no_coercion_crash` (from 5c62515a)

Lost: two ids (`"not-a-global-id"`, `str(item.pk)`) run in one `for` loop, so one node id; a
regression on one shape is masked by the other passing first only if it fails; and failability
per shape is not observable. `AGENTS.md`/`START.md` want `pytest.mark.parametrize`.

Do: convert the loop into `@pytest.mark.parametrize("bad_id", [...], ids=["not-a-global-id", "raw-pk"])`,
one shape per node id, identical assertions. Note the `str(item.pk)` case needs the item created
inside the test body (the fixture must run per parameter).

Mutation: in `django_strawberry_framework/mutations/resolvers.py::coerce_lookup_id` (or wherever
the malformed id becomes a field error; grep `coerce_lookup_id`), make it raise `ValueError`
instead of returning the field error. Expect both parametrized ids to fail.

#### B2. `test_relay_id_and_name_selection_is_clean_under_strictness_raise_over_http` (from 9031cb3d)

Lost: `assert all(row["id"] for row in ...)` is truthiness only.

Do: decode each id with `relay.GlobalID.from_id(row["id"])` and assert
`[int(g.node_id) for g in decoded] == list(Category.objects.order_by("pk").values_list("pk", flat=True))`
and every `g.type_name == Category._meta.label_lower` (derive from the ORM, do not hard-code).
Mirror `test_relay_id_only_connection_page_costs_one_query_and_emits_decodable_ids`, which
already decodes.

Mutation: in `django_strawberry_framework/types/relay.py::_resolve_id_default` (grep the name),
return `str(getattr(root, "pk")) + "x"`. Expect this test to fail on decode/equality.

#### B3. `test_cascade_query_count_fixed` (from ceef2344)

Lost: the total `len(captured) == 3` was dropped for per-table counts, so an added unrelated
query no longer fails it.

Do: keep the per-table counts and RE-ADD a total: count statements whose SQL contains
`FROM "products_` (all product tables) and assert that total equals the sum of the per-table
expectations already asserted. This ignores session/auth statements while pinning that no extra
product-table statement appears.

Mutation: in `django_strawberry_framework/permissions.py`, in the cascade helper
(`apply_cascade_permissions` or the function it calls that builds the `pk__in` subquery), force
the subquery to evaluate (`list(...)`) so it becomes a separate statement. Expect this test to fail
on the total.

#### B4. README rows

Extend the `test_products_api.py` / `test_products_visibility_api.py` suite-map rows with the
sharpened claims (decoded Relay ids under `raise`; product-table statement total on the cascade
row). One line each.

### WP-C: relay and keyset package restores

Files owned: `tests/test_keyset_connection.py`, `tests/test_keyset.py`,
`tests/test_relay_connection.py`, `examples/fakeshop/test_query/test_keyset_api.py`,
`examples/fakeshop/test_query/test_connection_pagination_api.py`.

#### C1. Bare keyset type routes through the keyset slicer (from ceef2344)

Lost, NO TWIN anywhere: `tests/test_keyset_connection.py::test_bare_keyset_connection_routes_through_keyset_slicer`
at `git show ceef2344^:tests/test_keyset_connection.py`. A `cursor_field` type with NO
`Meta.connection` opt-in still routes through the keyset slicer. Shipped `IssueType` opts in
(`examples/fakeshop/apps/library/schema.py::IssueType`), so no live row can show it.

Do: restore the original test verbatim into `tests/test_keyset_connection.py`, with every helper
or fixture it used (compare imports against the deleted version). Add one sentence to its
docstring stating why it is package-only: every shipped keyset type declares `Meta.connection`,
so the bare shape has no live fixture.

Mutation: in `django_strawberry_framework/connection.py` (the routing predicate that sends a
`cursor_field` type to the keyset slicer; the original test's assertions name the symbol it
exercised), make the bare shape fall through to the offset slicer. Expect the restored test to fail.

#### C2. Cursor projection keeps unrelated defers (from ceef2344)

Lost: original `tests/test_keyset_connection.py::test_extend_only_projection_arms` asserted
`names == frozenset({"title"})` / `defer_flag is True` after the cursor column is restored,
i.e. restoring the cursor column does NOT clear unrelated deferrals. Both live twins pass under a
projection that clears every deferral.

Do: read the original at `git show ceef2344^:tests/test_keyset_connection.py`. Add back the
deleted arm(s) into the surviving `test_extend_only_projection_passthrough_arms` (or as a new
sibling test named for the invariant, e.g. `test_extend_only_projection_keeps_unrelated_defers`)
with the exact original assertions.

Mutation: in `django_strawberry_framework/optimizer/nested_planner.py::_extend_only_projection`,
clear every existing deferral (`queryset.defer(None)` style) before adding the cursor column. Expect
the restored assertion to fail.

#### C3. Tampered cursor rejected at the auth tag, not at envelope decode (from ceef2344)

Lost (minor): original `tests/test_keyset.py::test_decode_rejects_tampered_ciphertext` tampered
the INNER ciphertext under a valid prefix; the live `test_root_keyset_rejects_tampered_and_offset_cursors[tampered]`
rewrites the outer base64, so an envelope-decode failure is indistinguishable from an AES-SIV
authentication failure.

Do: restore the original package test verbatim into `tests/test_keyset.py` (package-only: the
inner ciphertext is not addressable over the wire). One docstring sentence saying so.

Mutation: in `django_strawberry_framework/keyset.py::_decrypt_cursor_payload`, catch the AES-SIV
authentication failure and return the parsed payload anyway. Expect the
restored test to fail.

#### C4. Nested connection SDL argument block (from ceef2344)

Lost: original `tests/test_relay_connection.py::test_synthesized_connection_carries_sidecar_args_and_total_count`
and its helper `_field_args_block` (both at `git show ceef2344^:tests/test_relay_connection.py`)
pinned, for a NESTED synthesized connection: sidecar args present when the target declares them,
ABSENT for a sidecar-less target, and `sdl.count("totalCount") == 1`. The live replacement
`test_connection_pagination_api.py::test_root_connection_arguments_follow_declared_sidecars`
introspects ROOT `Query` fields only.

Do: add a live test in `test_connection_pagination_api.py` that introspects a NESTED connection
field on a shipped type: `__type(name: "GenreType") { fields { name args { name } } }` and asserts
the `booksConnection` field's arg names include `filter` and `orderBy` (if `BookType` declares
sidecars; verify in `apps/library/schema.py`) and a sidecar-less nested connection on another
shipped type (find one whose target declares neither `filterset_class` nor `orderset_class`;
`PeriodicalType.issues` per the relay commit) has NEITHER. Also assert `totalCount` appears in
exactly the connection types that opted in (`__type(name: "<X>Connection") { fields { name } }`).
Mirror the helper style already in that module. If no shipped sidecar-less nested connection
exists, additionally restore the original package test and helper verbatim into
`tests/test_relay_connection.py` and say why in its docstring.

Mutation: in `django_strawberry_framework/connection.py` (the synthesized-connection argument
derivation; grep `filterset_class` there), always attach `filter`/`orderBy` regardless of the
target's declaration. Expect the sidecar-less assertion to fail.

#### C5. `test_root_keyset_cursors_are_deterministic` (from ceef2344)

Lost (cosmetic): asserts equality of cursors across two requests, never that a cursor is non-empty.

Do: add `assert all(cursor for cursor in first_cursors)` (or the equivalent for the variables in
the test) before the equality assertion.

Mutation: none required beyond a passing run; note in the report that this is a guard against a
vacuous equality, not a discriminating claim.

### WP-D: transport, patches, schema, error policy

Files owned: `tests/test_views.py`, `tests/test_strawberry_patches.py`, `tests/test_schema.py`,
`tests/test_error_policy.py`, `examples/fakeshop/test_query/test_error_policy_api.py`,
`examples/fakeshop/test_query/test_transport_api.py`.

#### D1. No boundary middleware, over-limit multipart still parses nothing (from 9444cbb7)

Lost, NO TWIN: `tests/test_views.py::test_the_same_two_mounts_parse_nothing_without_the_middleware_either`
and helpers `_counting_multipart_parses`, `_STOCK_CSRF_MIDDLEWARE_PATH`, `_csrf_enforcing_client`
(all at `git show 9444cbb7^:tests/test_views.py`). fakeshop always installs the boundary entry, so
no live row can express the middleware-less chain. The surviving
`test_without_the_middleware_the_view_keeps_its_own_ordering_and_exemption` uses
`_RejectingCsrfMiddleware`, which refuses before reading `request.POST`, so its empty log cannot
witness a parse.

Do: restore the test and all three helpers verbatim. Keep the original module comment on
`_STOCK_CSRF_MIDDLEWARE_PATH` explaining why the stock CSRF class is needed.

Mutation: in `django_strawberry_framework/views.py::_RequestBodyBoundaryMixin._enforce_request_boundary`
(grep the mixin), read `request.POST` before the cap check. Expect the restored test to fail with
a nonzero parse count.

#### D2. Declined mount, SYNC colour (from 9444cbb7)

Lost: `tests/test_views.py::test_a_declined_callbacks_over_limit_body_never_reaches_the_csrf_class`
(sync). Live `test_transport_api.py::test_the_async_view_also_refuses_before_djangos_parser_runs`
covers the declined mount in the ASYNC colour only; the sync live row drives fakeshop's marked
mount.

Do: restore the original sync package test verbatim into `tests/test_views.py` (it needs the
helpers D1 restores). Docstring: one sentence that the live sync mount is marked, so the declined
sync colour is package-only.

Mutation: same as D1 but on the sync view path. Expect the restored test to fail.

#### D3. Translated recursion errors chain their cause (from 9444cbb7)

Lost: `type(err.__cause__) is RecursionError` on `_patched_parse_json` and
`_patched_parse_query_params` (originals `tests/test_strawberry_patches.py::test_patched_parse_json_translates_a_pathologically_nested_body`
and `::test_patched_parse_query_params_translates_a_deep_param` at
`git show 9444cbb7^:tests/test_strawberry_patches.py`). Live rows prove 400-not-500 only.

Do: restore both original package tests verbatim into `tests/test_strawberry_patches.py`
(package-only: `__cause__` is not on the wire). Keep the live 400 rows.

Mutation: in `django_strawberry_framework/_strawberry_patches.py`, raise the translated error
with `from None`. Expect both restored tests to fail.

#### D4. Error-policy extension survives a resolver emptying the extension list (from 7e5302d0)

Lost: original `tests/test_schema.py::test_a_resolver_cannot_disarm_enforcement_by_emptying_the_extension_list`
(at `git show 7e5302d0^:tests/test_schema.py`) asserted that after the write,
`schema.get_extensions(sync=True)` still contains a `DjangoErrorPolicyExtension`. The live twin
`test_resource_policy_api.py::test_a_resolver_cannot_widen_the_next_request_through_the_schema`
proves the RESOURCE half only.

Do: restore the original package test verbatim (it is package-only: it inspects
`get_extensions`). Also restore `test_get_extensions_sync_and_async` from
`git show 7e5302d0^:tests/test_schema.py`, but STRENGTHEN it: instead of `len(...) >= 2`, assert
that both `get_extensions(sync=True)` and `get_extensions(sync=False)` contain exactly one
`DjangoErrorPolicyExtension` and one `DjangoResourcePolicyExtension` instance (by `isinstance`
count), so the row states a real claim.

Mutation: in `django_strawberry_framework/schema.py::DjangoSchema.get_extensions`, return
`super().get_extensions(sync=sync)` without re-injecting the policy extensions (or drop the
error-policy one). Expect both restored tests to fail.

#### D5. Async pre-execution error: `data is None`, single error, over HTTP (from 7e5302d0)

Lost: `tests/test_error_policy.py::test_an_async_pre_execution_error_carries_no_original_error`
now defers `data is None` / one-error to a SYNC live row
(`test_error_policy_api.py::test_a_validation_error_keeps_its_own_message_and_carries_no_correlation_id`).
No async live sibling.

Do: add an ASYNC twin of that live row in `test_error_policy_api.py`, posting the same invalid
document to the module's `/graphql-async/` mount (read the module's `urlpatterns` and existing
async rows first; reuse their client helper). Assert `data is None`, exactly one error, the
error's own message, and no correlation id in `extensions`.

Mutation: in `django_strawberry_framework/extensions/error_policy.py`, in the async
pre-execution branch, mask the validation message the way execution errors are masked. Expect
only the new async row to fail (the sync row must stay green under this mutation; if it also
fails, your mutation is not async-specific: find the async branch).

#### D6. `test_an_unnamed_multi_operation_document_is_charged_in_full` (from 7e5302d0)

Weak-live: depends on the budget stage running before GraphQL's "must provide operation name"
error. The docstring says so; the test would silently change meaning if stage order moved.

Do: add an explicit assertion that the returned error is the BUDGET error (match the exact
resource-policy message/extension code the module's other over-bound rows assert) and NOT the
operation-name error (assert the string `Must provide operation name` is absent from every
error message). Now a stage-order change fails loudly.

Mutation: none needed beyond the passing run; explain in the report.

### WP-E: forms and filters package rows

Files owned: `tests/forms/test_resolvers.py`, `tests/filters/test_inputs.py`.

#### E1. Upload lands in `files`, never in `data` (from 5c62515a)

Lost: original `tests/forms/test_resolvers.py::test_decode_split_upload_lands_in_files_never_data`
(at `git show 5c62515a^:tests/forms/test_resolvers.py`) asserted `"attachment" not in provided_data`
and `provided_data == {"label": "L"}`. Django's `FileField` widget reads only `files`, so a
`_decode_form_data` that wrote the upload into BOTH dicts passes every live row.

Do: restore the original test verbatim (package-only: `provided_data` is an internal split).
If its fixture form no longer exists at HEAD, rebuild it minimally from the original.

Mutation: in `django_strawberry_framework/forms/resolvers.py::_decode_form_data`, also write each
file value into `provided_data`. Expect the restored test to fail.

#### E2. Range input scoping matters because the axes differ (from e9e4d45c)

Lost: original `tests/filters/test_inputs.py::test_range_input_type_name_is_scoped_per_filterset`
(at `git show e9e4d45c^:tests/filters/test_inputs.py`) built two filtersets whose range axes are
DIFFERENT scalars and asserted `r1.__annotations__["start"] != r2.__annotations__["start"]`. Both
shipped `price_span` filtersets range over Decimal, so the live row proves name distinctness only.

Do: restore the original test verbatim. Docstring sentence: shipped filtersets share one axis
scalar, so the differing-axis claim is package-only.

Mutation: in `django_strawberry_framework/filters/inputs.py`, make the range input type name a
constant (drop the per-filterset scoping). Expect the restored test to fail (and the live
`test_scalars_filter_api.py::test_range_input_types_are_scoped_per_filterset` also).

### WP-F: middleware, management, extensions

Files owned: `tests/middleware/test_debug_toolbar.py`,
`examples/fakeshop/test_query/test_debug_toolbar_api.py`,
`examples/fakeshop/tests/test_inspect_django_type.py`, `tests/management/test_export_schema.py`.

#### F1. Callable panel `title` / `nav_subtitle` arms (from 20646db2)

Lost: original `tests/middleware/test_debug_toolbar.py::test_get_payload_panel_title_only_when_has_content`
(at `git show 20646db2^:tests/middleware/test_debug_toolbar.py`) drove `_get_payload` with a
fake panel whose `title`/`nav_subtitle` are callables, asserted the exact `{"title", "subtitle"}`
key set, and that the subtitle survives on a `has_content`-false panel. No stock toolbar panel has
a callable title, so `django_strawberry_framework/middleware/debug_toolbar.py::_get_payload #"title() if callable(title) else title"`
has both callable arms pinned by nothing; statement coverage marks an unused ternary arm covered.

Do: restore the original test verbatim. Docstring sentence: stock panels expose properties, so the
callable arm is package-only.

Mutation: in `_get_payload`, replace `title() if callable(title) else title` with `title`
(and likewise for the subtitle). Expect the restored test to fail.

#### F2. Encoded response row needs an in-test positive control (from 20646db2)

Weak-live: `test_debug_toolbar_api.py::TestToolbarPresent.test_encoded_response_gets_no_package_mutation`
has no control; if the toolbar stops firing, all four cells pass vacuously.

Do: inside the same test, before the encoded cells, issue one request WITHOUT the stamping
middleware entry (or with an unencoded body) and assert the toolbar payload marker IS present
(reuse the marker assertion the module's other rows use, e.g. whatever
`test_named_json_operation_gets_panel_payload` asserts). Keep the four cells.

Mutation: in `django_strawberry_framework/middleware/debug_toolbar.py`, make `_postprocess`
return early for every response. Expect this test to fail on the control (it would otherwise
pass vacuously; that is the point).

#### F3. Inspect command: graphql-type column pinned on its own (from 81c63703)

Lost: `examples/fakeshop/tests/test_inspect_django_type.py::test_inspect_file_and_image_rows_name_output_converters`
asserts `"DjangoFileType" in attachment_row`, which the converter column on the same line already
satisfies. Original `tests/management/test_inspect_django_type.py::test_scalar_row_names_file_output_converter_not_scalar_map`
(at `git show 81c63703^:tests/management/test_inspect_django_type.py`) asserted
`graphql_type == output_type.__name__` and `nullable == "yes"` as separate columns.

Do: split the row into columns (read how `_field_row` returns the line; split on the table
separator the command emits, e.g. `|`, and strip) and assert the graphql-type column equals
`DjangoFileType` / `DjangoImageType` and the nullable column equals `yes`, positionally.

Mutation: in `django_strawberry_framework/management/commands/inspect_django_type.py`, emit the
scalar-map name (e.g. `String`) in the graphql-type column for file fields while leaving the
converter column unchanged. Expect this test to fail.

#### F4. `test_export_schema_raises_command_error_when_path_flag_has_no_value` (from 81c63703)

Weak: the selector became `"x"` (unimportable) and the assertion is a bare `pytest.raises(CommandError)`,
so the row no longer isolates the argparse no-value branch.

Do: use an importable selector (`config.schema:schema`, matching the module's other rows) and add
`match=` with the argparse no-value message (`expected one argument` or whatever `--path` with no
value raises; run it once to read the text).

Mutation: in `django_strawberry_framework/management/commands/export_schema.py`, give `--path`
`nargs="?"` with a default. Expect this test to fail (no error raised).

### WP-G: auth and exceptions

Files owned: `tests/auth/test_mutations.py`, `tests/auth/test_sessions.py`,
`examples/fakeshop/test_query/test_auth_api.py`, `tests/test_exceptions.py`.

#### G1. Logout signal failure leaves the in-process actor anonymous (Django HTTP colour) (from fad17c20)

Lost: original `tests/auth/test_mutations.py::test_django_logout_signal_failure_no_ok_and_actor_anonymized`
(at `git show fad17c20^:tests/auth/test_mutations.py`) asserted `not request.user.is_authenticated`
after a raising `user_logged_out` receiver on the Django HTTP transport. Live
`test_logout_signal_failure_is_an_error_and_keeps_the_durable_session` cannot see the in-process
request object.

Do: restore the original test verbatim (package-only: in-process request state).

Mutation: in `django_strawberry_framework/auth/mutations.py`, in the logout compensation path,
skip re-pointing `request.user` to `AnonymousUser` when the signal raises. Expect the restored
test to fail.

#### G2. `require_session` raises `ConfigurationError` on the Django HTTP branch (from fad17c20)

Lost: original `tests/auth/test_sessions.py::test_require_session_missing_django_middleware_raises_with_the_session_substring`
pinned the EXCEPTION CLASS; live sessionless rows assert message text only.

Do: restore the original test verbatim.

Mutation: in `django_strawberry_framework/auth/sessions.py::require_session`, raise
`RuntimeError` with the same message on the `Transport.DJANGO_HTTP` branch. Expect the restored
test to fail and the live rows to stay green (confirms the class was the lost claim).

#### G3. Backend crash leaves no durable session row (from fad17c20)

Lost: live `test_auth_api.py::test_login_backend_crash_propagates_and_leaves_session_untouched`
dropped the durable half of `tests/auth/test_mutations.py::_assert_login_fully_compensated`
(`Session.objects.count() == 0`, `SESSION_KEY not in session`).

Do: add both assertions to the live row: after the crashing login, assert
`django.contrib.sessions.models.Session.objects.count() == 0` and that the response set no
session cookie (or the cookie's session has no `SESSION_KEY`). Read `_assert_login_fully_compensated`
and mirror exactly what it checks.

Mutation: in `django_strawberry_framework/auth/mutations.py`, in the login path, call
`request.session.save()` (or `cycle_key()`) BEFORE `authenticate` runs. Expect the live row to
fail on the durable count.

#### G4. Shallow copy shares the terminal object (from bd89ef5f)

Lost: `tests/test_exceptions.py::test_lookup_validation_error_roundtrip_preserves_attributes`
dropped `copy.copy(err).terminal is term` (original
`test_lookup_validation_error_pickle_and_copy_fidelity` at `git show bd89ef5f^:tests/test_exceptions.py`).

Do: in the `copy` arm of the parametrized test (or as an explicit extra assertion guarded on the
copy mode), assert `restored.terminal is term` for shallow copy and `is not` for deepcopy/pickle.

Mutation: in `django_strawberry_framework/exceptions.py`, give `LookupValidationError` a
`__copy__` that deep-copies `terminal`. Expect the shallow-copy id to fail.

### WP-H: list field

Files owned: `examples/fakeshop/test_query/test_list_field_async_api.py`,
`examples/fakeshop/test_query/test_list_field_api.py`, `tests/test_list_field.py`.

Before editing, `git status --short` these three files. If any is dirty, diff it against
`git show HEAD:<path>` into your scratch dir and report; edit around foreign hunks.

#### H1. Async source consumed only up to the bound (from 509d8cc0)

Lost: original `tests/test_list_field.py::test_djangolistfield_async_consumer_resolver_async_iterable_is_bounded`
(at `git show 509d8cc0^:tests/test_list_field.py`) asserted `source.consumed == 1`. No live row
asserts the advance count for a POSITIVE bound (only `== 0` for `limit: 0`). A drain-then-slice
implementation stays green everywhere.

Do: in `test_list_field_async_api.py::test_async_http_partial_async_generator_resolver_is_bounded`,
the holder resolver's async generator must count `__anext__` calls (look at how
`test_async_iterator_aclose_witness_on_limit_zero_and_rejection` witnesses `aclose`; add a
`next_count` witness the same way) and the test asserts `next_count == limit` (or `limit + 1` if
the implementation probes one extra row; read `django_strawberry_framework/list_field.py` to know
which, and assert the exact number, not `<=`).

Mutation: in `django_strawberry_framework/resource_policy.py::bounded_rows_async` (the async
bounding helper `list_field.py` routes through), collect the whole iterator into a list and slice
it. Expect this test to fail.

#### H2. `patron_id` is in the projection, not just somewhere in the SQL (from 509d8cc0)

Weak-live: `test_list_field_api.py::test_holder_membership_card_list_elides_patron_id_to_one_query`
asserts `"patron_id" in card_sql[0]`, a substring over the whole statement.

Do: split the statement at the first ` FROM ` and assert `"patron_id"` is in the SELECT list
(the part before `FROM`) and that `"library_patron"` appears nowhere in the statement.

Mutation: in `django_strawberry_framework/optimizer/walker.py`, in the FK-id elision branch, plan
`select_related` for the relation instead of projecting the `_id` column. Expect this test to fail.

#### H3. Offset coercion rows pin the refusal reason (from 509d8cc0)

Weak-live: `test_shipped_branches_an_offset_variable_outside_int_is_refused_before_sql` and
`test_shipped_branches_a_float_offset_literal_is_refused_before_sql` assert only `"errors" in payload`,
`data is None`, zero queries.

Do: add an assertion on the error message: the GraphQL `Int` coercion text (run once and copy the
exact phrase, e.g. `Int cannot represent non-integer value`). Apply the same to their pre-existing
`limit` twins in the same module for consistency.

Mutation: none discriminating beyond the passing run; report.

### WP-I: permissions and optimizer-auto fixtures

Files owned: `examples/fakeshop/test_query/test_optimizer_auto_api.py`,
`tests/test_predicate_pg_explain.py`, `tests/test_lateral_pg_parity.py`.

#### I1. `_seed_hint_shelf` seeds one parent (from c527e75c)

Weak-live: with one shelf, the windowed row can be satisfied by the single-parent fast path
(`django_strawberry_framework/optimizer/single_parent_fetch.py`), which also emits no
`CROSS JOIN LATERAL`, so neither hint row proves the windowed body ran or exercises per-parent
partitioning. The deleted pair ran against three shelves.

Do: make `_seed_hint_shelf` seed THREE shelves with differing book counts (mirror the deleted
tests' `_seed_library` at `git show c527e75c^:tests/test_lateral_pg_parity.py`), and in
`test_per_field_strategy_hint_windowed_under_lateral_default_skips_lateral_over_http` assert the
captured book SQL contains `OVER (` (the window) and `PARTITION BY` and no `LATERAL`; in the
lateral twin assert `LATERAL` present. Update `response.data ==` expectations for three parents.

Mutation: in `django_strawberry_framework/optimizer/nested_fetch.py` (strategy selection), ignore
the per-field hint and always use the extension default. Expect both hint rows to fail.

#### I2. Single distinct-free correlated EXISTS under Postgres (from c527e75c)

Lost: `tests/test_predicate_pg_explain.py::test_emitted_leaf_is_a_single_distinct_free_correlated_exists`
(at `git show c527e75c^:tests/test_predicate_pg_explain.py`): `EXISTS` count == 1 and
`outer_tables == {"library_loan"}` from the alias map, under the `pg` mark.

Do: restore the original verbatim (it is `@pytest.mark.pg`, skipped without Postgres; that is
fine, the live SQLite row in WP-A A3 carries the SQLite half). Note the mark in your report.

Mutation: same as A3; run only if you have Postgres available, otherwise report the restored row
as unproven-by-mutation and collected-but-skipped.

### WP-J: guards, isolation, fixtures

Files owned: `tests/test_build_tree_md.py`, `tests/test_ci_governance.py`,
`examples/fakeshop/test_query/test_resource_policy_api.py`,
`examples/fakeshop/apps/products/tests/test_services.py`,
`examples/fakeshop/test_query/test_mutation_atomicity.py`.

#### J1. Parametrized populations read at import need a non-empty guard

Weak: `tests/test_build_tree_md.py::test_curated_planned_description_is_one_sentence` parametrizes
over `PLANNED_PATH_DESCRIPTIONS` at import; an emptied dict collects zero cases and reads as a pass.
`tests/test_ci_governance.py::test_container_images_are_pinned_by_digest` passes per-file with
zero assertions when a workflow has no image reference.

Do: add a plain (non-parametrized) sibling in each module: `test_curated_planned_descriptions_are_present`
asserting `len(PLANNED_PATH_DESCRIPTIONS) > 0` (mirror
`test_discovered_fakeshop_apps_equal_the_installed_local_apps`'s `assert installed` shape), and in
`test_ci_governance.py` assert that at least one workflow file in `WORKFLOW_PATHS` contains an
image reference (so the per-file loop is known to have a non-empty population), or make the
per-file test assert the count of image references it checked is `> 0` for the files that are
expected to have them (read the workflows to decide which).

Mutation: empty the dict / remove the image line in the scratch copy. Expect the guard to fail.

#### J2. `test_an_overlapping_request_does_not_admit_an_oversized_one` isolation (from 7e5302d0)

Weak-live: 8 parametrized rows share class-level mutable state (`_OverlapCoordinator.armed/parked/released`,
`_ExecutionWitness.entered`) plus a background thread and two 10s waits. Correct only under
`--dist loadscope`; order-coupled.

Do: give each parametrized case fresh state: reset the coordinator/witness class attributes in a
function-scoped fixture (`autouse` for this test only, or called at the top of the test body) and
join the background thread in a `finally`. Do not change what the test asserts. Run the 8 ids in
reverse order (`-p no:randomly` is not installed; pass the node ids reversed on the command line)
and forward order; both must pass.

Mutation: none; this is isolation. Report both run orders.

#### J3. Fixture-helper gate: per-helper deltas (from f54cf12d)

Weak: `examples/fakeshop/apps/products/tests/test_services.py::test_every_named_fixture_helper_seeds_into_one_database`
ends with `Category.objects.filter(name__startswith="zzz_").count() >= len(helpers)`, looser than
its docstring (one helper silently ceasing to write a category still passes).

Do: inside the loop, record `Category.objects.count()` before and after each helper and assert
the delta is `>= 1` per helper, naming the helper in the assertion message. Keep the existing
collision detection.

Mutation: in the scratch copy, make one `seed_*` helper in `apps/products/services.py` return
without creating a category. Expect the gate to fail naming that helper.

#### J4. `test_mutation_atomicity.py::test_update_does_not_commit_when_response_completion_fails_over_graphql_async`

Weak-live: `status_code < 500` is loose.

Do: assert `status_code == 200` and that the payload has `errors` with a located error path
matching the failing completion field (read the sync sibling in the same module for the exact
shape and copy it).

Mutation: none needed; report.

### WP-K: mutations override composite

Files owned: `tests/mutations/test_resolvers.py`.

#### K1. Consumer-declared relation override still reaches relation visibility (from e3257e25)

Lost, NO TWIN: `tests/mutations/test_resolvers.py::test_globalid_relation_override_flows_through_visibility_contract`
(at `git show e3257e25^:tests/mutations/test_resolvers.py`). Shipped `BookCreateFieldOverrides`
declares only `subtitle`, so no live row declares a relation in an override.

Do: restore the original test verbatim AND the `_build_item_schema` keyword parameters it needs
(`category_get_queryset`, `input_cls`, `partial_input_cls`; see the original signature at the same
`git show`). Re-add only the kwargs this test uses; keep the current callers working (all kwargs
default to `None`). Docstring sentence: no shipped override declares a relation field, so the
composite is package-only.

Mutation: in `django_strawberry_framework/mutations/resolvers.py`, in the relation decode step,
skip the visibility check for any input field whose spec did not come from the generated input
(if no such distinction exists in code, mutate the visibility check to a no-op and confirm the
restored test AND the live hidden-category row both fail; report that the override-specific
branch does not exist, which is itself the finding).

---

## 4. Coordinator protocol

1. Read section 0 in full yourself. Then dispatch WP-A .. WP-K as eleven parallel workers, each
   with: this file's section 0, section 1, section 2, and ONLY its own work-package section.
   Tell each worker its `<WP-id>` for the scratch path.
2. Do not let two workers touch one file. The ownership lists above are disjoint; if a worker
   reports it needs a file outside its list, hold that item and assign it after the owning worker
   finishes.
3. When all workers report, run ONE integration pass yourself, in this order:
   - `uv run ruff format <all touched files>` and `uv run ruff check --fix <all touched files>`
   - `uvx pre-commit run --files <all touched files>` (six hooks; if `source-layout` reports
     "files were modified", re-run until all six say Passed, then re-run the touched tests)
   - `uv run pytest <every touched module> --no-cov -p no:cacheprovider` (modules, not the suite)
   - `uv run python scripts/build_tree_md.py --check` (no test FILE was added or removed, so this
     must say up to date; if a first docstring sentence changed, regenerate and include
     `docs/TREE.md`)
   - `uv run python scripts/check_citations.py --check`
4. Collect every worker's mutation table into one report for the maintainer: item id, node ids,
   mutation site, failing count under mutation, passing count restored, and every `BLOCKED`.
5. Do NOT commit. Do NOT stage. Hand the maintainer the list of touched paths and the report.
   The maintainer decides what lands.

## 5. Out of scope, deliberately

- Removing, renaming, or weakening any test.
- Editing production code under `django_strawberry_framework/` in the shared checkout. Mutations
  happen only in scratch copies.
- `docs/TREE.md`, `KANBAN.md`, `CHANGELOG.md` edits (unless step 3 of the coordinator protocol
  requires regenerating TREE).
- Touching any file the other in-flight sessions have dirty (spec-050 list-field docs,
  `db.sqlite3`, DRY and bug-hunt records).
