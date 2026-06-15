# Build: Slice 4 — products activation + live HTTP

Spec reference: `docs/spec-034-permissions-0_0_10.md` (Slice checklist lines 70-74; Test plan lines 459-468; Decision 5/6/8/11/12; Edge cases lines 395/405; Risks "Live-suite sensitivity" line 498)
Status: final-accepted

## Plan (Worker 1)

### DRY analysis

- **Existing patterns reused (cite file:line).**
  - **The source change is pure uncomment** — `examples/fakeshop/apps/products/schema.py` already carries the four `get_queryset` cascade hooks verbatim as comments (`CategoryType` schema.py:70-80, `ItemType` schema.py:104-114, `PropertyType` schema.py:138-148, `EntryType` schema.py:172-182) plus the commented import (`schema.py:33`). Each body is byte-for-byte the contract this slice ships (`staff → all`; `has_perm("products.view_<model>") → filter(is_private=False)`; else `apply_cascade_permissions(cls, queryset.filter(is_private=False), info)`). Nothing is authored; the four hooks + import are uncommented and the staged-seam TODO comment lines are removed.
  - **The live-test harness is fully in place** — `examples/fakeshop/test_query/test_products_api.py` carries the request helper `_post_graphql` (test_products_api.py:79-85), the assertion helper `_assert_graphql_data` (:88-94), the staff-login helper `_staff_client` (:97-102, which itself calls `create_users(1)` then `force_login(staff_1)`), the `_global_id` helper (:105-106), the autouse schema-reload fixture `_reload_project_schema_for_acceptance_tests` (:73-76), and `CaptureQueriesContext` query-count pinning (e.g. :206, :694). The new cascade tests reuse all of these — no new harness.
  - **The five Slice-4 live tests already exist as `@pytest.mark.skip` stubs** with assertion-spec docstrings, under the `# STAGED SEAM (spec-034 Slice 4)` banner (test_products_api.py:728-783): `test_cascade_anonymous_sees_no_entries_under_private_categories` (:742), `test_cascade_view_item_user_matrix` (:753), `test_cascade_staff_sees_everything` (:764), `test_cascade_query_count_fixed` (:770), `test_cascade_composes_with_filter_and_order_live` (:780). Worker 2 drops `@skip` and fills each body — does NOT add net-new test functions for these five (the Slice-4 Test-plan names map 1:1 to the existing stubs).
  - **User provisioning** — `apps.products.services.create_users(1)` (services.py:259-340) provisions `staff_1` (`is_staff=True`, NOT superuser — services.py:298-305), `regular_1` (no perms, not staff — :309-318), and one user per `VIEW_PERMISSIONS` codename (`view_category_1` / `view_item_1` / `view_property_1` / `view_entry_1` — :320-338), each holding ONLY its single `view_<model>` permission. The new tests `force_login(...)` the relevant seeded user, never hand-roll a `User`.
  - **Catalog seeding** — `apps.products.services.seed_data(N)` (services.py:147-240) is the only catalog seeder; the cascade fixtures seed through it, then flip specific rows' `is_private` via the ORM where a deterministic private/public split is needed (see Test additions).
- **New helpers justified.** None at slice scope. The five cascade tests are independent live scenarios; a shared private-fixture builder is tempting but the spec keeps each test self-seeding (first line `create_users(1)` / `seed_data(N)` per AGENTS.md). If two-or-more tests end up duplicating the *same* private-split ORM setup, a module-local `_seed_private_split()` helper is the right extraction — flagged to Worker 2 as a discretion item, not pre-built (premature before the bodies exist).
- **Duplication risk avoided.** The naive risk is **adding** new `test_cascade_*` functions alongside the existing skip-stubs, producing duplicate test names / dead stubs. Prevented: Worker 2 fills the EXISTING stub bodies and removes their `@skip` decorators, keeping the `# STAGED SEAM` banner comment until the last stub is filled (then the banner's "Fill in + drop the skips in Slice 4" line is stale — drop or rewrite it). Second risk: re-deriving expected row sets with a hand-rolled privacy filter instead of mirroring the ORM. Prevented: expected sets are computed from the equivalent `Model.objects.filter(...)` ORM query (the file's established data-driven pattern, e.g. :462-467, :596-598), so API == ORM and Faker-version drift stays robust.

### Implementation steps

Line numbers are pin-at-write-time navigational hints; re-verify against current source before editing (concurrent em-dash comment swaps and Slices 1-3 may have shifted nothing in these files, but confirm).

1. **Uncomment the import** in `examples/fakeshop/apps/products/schema.py::<module>` — turn `# from django_strawberry_framework import apply_cascade_permissions  # TODO-ALPHA-034-0.0.10` (schema.py:33) into live code: `from django_strawberry_framework import apply_cascade_permissions`. Decide placement: it currently sits in the "Future imports" comment block (schema.py:28-35). Move the now-live import into the real first-party import group with the existing `from django_strawberry_framework import (DjangoConnection, DjangoConnectionField, DjangoType)` block (schema.py:40-44) — add `apply_cascade_permissions` to that parenthesized group rather than leaving a lone import in the comment block (ruff/isort ordering; Worker 2 discretion on exact grouping per `ruff check --fix`). Remove the now-obsolete `# TODO(spec-034 Slice 4): activate the cascade …` instruction comment (schema.py:30-33) — it described the action this step performs.
2. **Uncomment `CategoryType.get_queryset`** (schema.py:70-80): remove the `# Future cascade-permission visibility hook - uncomment when TODO-ALPHA-034-0.0.10 ships:` lead comment + the `#`-prefix on the `@classmethod def get_queryset(cls, queryset, info): …` body. Result is the live four-line hook (staff → all; `view_category` → `filter(is_private=False)`; else `apply_cascade_permissions(cls, queryset.filter(is_private=False), info)`).
3. **Uncomment `ItemType.get_queryset`** (schema.py:104-114) — same shape, `view_item`.
4. **Uncomment `PropertyType.get_queryset`** (schema.py:138-148) — same shape, `view_property`.
5. **Uncomment `EntryType.get_queryset`** (schema.py:172-182) — same shape, `view_entry`. (Note the concurrent em-dash→hyphen comment sweep already normalized dashes inside these comment blocks; once the comment becomes code that churn dissolves — Worker 2 leaves the surrounding pre-existing comment swaps alone per the build plan's Concurrent-sweep instruction.)
6. **Drop `@skip` + fill the five cascade-test stub bodies** in `examples/fakeshop/test_query/test_products_api.py` (:738-783) — see Test additions for each body's shape. Keep `@pytest.mark.django_db`; remove `@pytest.mark.skip(...)`. The `# STAGED SEAM (spec-034 Slice 4)` banner (:728-735) loses its "Fill in + drop the skips in Slice 4" sentence (rewrite to a plain section header or drop the now-stale instruction line).
7. **Audit + re-pin the existing live assertions** (load-bearing — see "Audit method" below). Re-pin every anonymous-running assertion whose row count or specific-row presence changes once anonymous requests narrow via the activated hooks. This is in the SAME change (same diff) as steps 1-6, not a follow-up.

### Test additions / updates

**The five cascade tests fill the existing stubs (NOT net-new functions).** First line of each is `create_users(1)` per AGENTS.md / card DoD — real users, never mocked `info.context.user`. The staff branch keys on `is_staff` and `create_users` makes `staff_1` staff-not-superuser, so staff assertions must not assume `is_superuser` (spec Test-plan note, line 461).

- `test_cascade_anonymous_sees_no_entries_under_private_categories` (:742) — `create_users(1)`; `seed_data(N)`; flip a chosen `Category` to `is_private=True` via ORM and ensure it has a **public** `Item` carrying a **public** `Entry` (so only the cascade, not the entry's own privacy, hides it). Anonymous `allEntries { edges { node { id value item { name category { name } } } } }`; assert NO returned entry's `item.category.name` equals the private category's name (the cascade reaches `Entry → item → Category`). Assertion shape: collect returned `item.category.name` set, assert the private category name is absent AND a known public-chain entry IS present (proves narrowing, not blanket-empty).
- `test_cascade_view_item_user_matrix` (:753) — `create_users(1)`; `force_login(view_item_1)`; seed a private-category / public-item / public-entry chain AND a public-category / public-item / public-entry chain. The `view_item` user clears `ItemType`'s own `has_perm("products.view_item")` branch → sees non-private items regardless of category privacy; but `EntryType.get_queryset` for that same user has NO `view_entry` perm, so its cascade still drops entries whose `item.category` is hidden. Assert: `allItems` includes the item under the private category (item-level rule lets `view_item` see it), yet `allEntries` excludes that item's entry (entry-level cascade reaches the hidden category through `item`). This is the per-edge composition pin — the two root fields disagree by design.
- `test_cascade_staff_sees_everything` (:764) — `create_users(1)`; `force_login(staff_1)`; seed a private/public split (private categories, private items, private entries). Assert staff `allEntries` / `allItems` / `allCategories` counts equal the full ORM counts (`models.Entry.objects.count()` etc., capped at `_RELAY_MAX_RESULTS` where the connection caps). Pins the `is_staff` bypass without relying on `is_superuser`.
- `test_cascade_query_count_fixed` (:770) — `create_users(1)`; `seed_data(N)` with a private/public split; anonymous `allEntries { value item { name category { name } } }` under `CaptureQueriesContext`. Assert an ABSOLUTE fixed count (derive from a real run — the optimizer plans the forward-FK traversal as `select_related`/downgraded `Prefetch`; the cascade's `__in` subqueries compile inline per Decision 7 so they add ZERO round-trips). Load-bearing shape: assert the absolute integer (e.g. `== 1` for the single planned slice query if the traversal stays `select_related`, matching the un-cascaded twin at :354) AND assert the SQL carries the cascade's nested `IN (SELECT` subquery so the test cannot pass on a fall-through that skipped the cascade. Run-or-derive the count empirically; never guess. NOTE the cascade downgrade interaction: `EntryType` cascades into `ItemType`/`PropertyType` which cascade into `CategoryType`, all custom hooks — so the forward-FK `item__category` chain may downgrade `select_related → Prefetch` (Decision 12 / Slice-2 pin); the absolute count must come from a real run of THIS cascaded shape, which may differ from the un-cascaded :354 count of 1. Worker 2 derives it.
- `test_cascade_composes_with_filter_and_order_live` (:780) — `create_users(1)`; `seed_data(N)`; one request combining `filter:` + `orderBy:` + the active cascade. Two shapes per Decision 11 (cascade narrows first, gates judge input second): (a) a gated-field input (`allCategories(orderBy: [{ name: ASC }])` or `filter: { name: ... }`) anonymously still raises the `check_name_permission` "staff user" error (the gate fires on input shape independent of cascade — mirrors :535/:376); (b) a non-gated composing request as a staff or `view_item` client (e.g. `allItems(filter: { category: { id: { in: [...] } } }, orderBy: [{ name: ASC }])`) returns cascade-narrowed-then-ordered rows. Assert the gate error in shape (a) and the narrowed-ordered row set in shape (b). The `check_name_permission` gates keep firing exactly as their shipped live pins.

**Existing-assertion re-pins (load-bearing audit — spec checklist bullet 3, line 73).**

Audit method: (1) read `seed_data`'s `is_private` defaults (services.py:182-232) — Category/Property privacy is **deterministic** (`cat_index % 2 == 1` / `prop_index % 2 == 1`, sorted-index alternation → EXACT 50/50 split, services.py:183-204), but **Item and Entry privacy is `random.choice([True, False])`** (services.py:218/228) — NON-deterministic across runs. (2) For each existing test, classify by request identity: STAFF (`_staff_client()`) bypasses all four hooks → SAFE; DENIAL tests assert a gate error on input shape → SAFE (Decision 11: error independent of cascade); ANONYMOUS row/count assertions → AT RISK once anonymous requests narrow to `filter(is_private=False)` + cascade.

The spec Risks "Live-suite sensitivity" (line 498) names a *preferred* answer ("suite seeds public-only fixtures, churn minimal") — **the audit shows that preferred answer is FALSE for this suite**: `seed_data` makes ~50% of categories private deterministically and randomizes item/entry privacy, so the anonymous-running assertions below WILL break. The spec's documented *fallback* ("seed the private fixtures only inside the new cascade tests, keep legacy seed paths public-only — fixture-scoping, not contract change") is the realistic path. Worker 2 chooses per-test between two equally-valid re-pins (Implementation discretion item 1): **(A) flip the test to a staff client** (`_staff_client()`) where the test's intent (filter/order/optimizer SQL shape) is orthogonal to anonymous visibility — staff bypasses the cascade and the assertion holds unchanged; or **(B) keep it anonymous and re-derive the expected set through the post-cascade ORM filter** (`is_private=False` + parent-public predicates) so API == ORM under the new visibility. Prefer (A) for tests whose subject is SQL-shape/optimizer/filter-order mechanics (the cascade is incidental), prefer (B) for tests whose subject IS root-field row content.

At-risk anonymous assertions enumerated (each MUST be re-pinned in this same change):

- `test_emitted_globalid_is_model_anchored` (:110) — anon `allItems`; `next(node for node … name == item.name)` where `item` = first Item by id. First item may be private or under a private (odd-index) category → absent → `StopIteration`. Re-pin: staff client OR pick a known-public item under a known-public category.
- `test_globalid_filter_round_trip` (:132) — anon `allItems`, `target` = first Item. Same StopIteration risk on the emit step. Re-pin: same.
- `test_type_strategy_opt_out_reproduces_type_name` (:159) — anon `allItems`, first Item. Same. (Note: the `override_settings`+reload ordering is orthogonal; only the row presence is at risk.)
- `test_products_optimizer_merges_duplicate_root_field_nodes_over_http` (:188) — anon `allItems`; `payload["data"] == {"allItems": {"edges": expected}}` where `expected` = ALL items via `Item.objects.select_related("category").order_by("id")`. Anonymous now sees only non-private items under non-private categories → full-set equality breaks. Subject is optimizer SQL shape (1 query, JOIN) → prefer staff client (A); `expected` then stays the full set and `len(captured)==1` + JOIN assertions hold.
- `test_products_optimizer_prefetches_nested_reverse_fk_depth_2_over_http` (:228) — anon `allCategories { items { entries } }`; asserts `len(categories) == Category.objects.count()`, items == all, entries == all, AND `len(captured) == 3`. Anonymous sees only public (even-index) categories; nested `items`/`entries` LIST relations also narrow via `ItemType`/`EntryType` hooks. Counts break. Query-count 3 may also shift (the reverse-FK prefetch children now carry the target hooks' cascade subqueries inline — count likely stays 3 but re-verify). Subject is the depth-2 prefetch SQL shape → prefer staff client (A) to keep the full-set + `==3` assertions; if kept anonymous (B), re-derive all three counts through the post-cascade ORM and re-derive the query count from a real run.
- `test_products_optimizer_selects_nested_forward_fk_depth_2_over_http` (:289) — anon `allEntries`; `payload["data"] == expected` (first 100 entries by pk via `select_related("item__category")`). Anonymous now drops entries that are private, or whose `item`/`property` is private, or whose `item.category`/`property.category` is private (transitive cascade) — large churn; even the `> _RELAY_MAX_RESULTS` cap-boundary precondition may no longer hold for the narrowed set. Subject is the forward-FK `select_related` SQL shape → prefer staff client (A): `expected` stays the full first-100 set, JOIN + `len(captured)==1` hold. (Under staff the cascade hooks short-circuit to `return queryset`, so the optimizer plans plain `select_related("item__category")` exactly as today.)
- `test_products_categories_filter_by_relay_own_pk_global_id_in` (:425) — anon `allCategories(filter: { id: { in: [first 2 cats] } })`; expected = those 2 categories. The two are `cat_index` 0 (public) and 1 (PRIVATE, odd) → anonymous won't see category 1. `id` has no gate (runs anon by design). Re-pin: pick two known-PUBLIC categories (even indices, e.g. the 1st and 3rd by id) OR staff client. The test's subject is GlobalID `in`-decoding (not visibility) → either works; prefer picking two public categories to keep the anonymous path under test, else staff (A).
- `test_products_items_filter_by_related_category_global_id` (:477) — anon `allItems(filter: { category: { id: { exact } } })`; expected = ALL items in the first category. First category (index 0) is public, but its items have RANDOM privacy → anonymous sees only the non-private ones. Re-pin: re-derive `expected` through `Item.objects.filter(category=category, is_private=False)` (B) — the subject IS the RelatedFilter row content, so keep it anonymous and narrow the ORM expectation; OR staff (A).
- `test_products_items_order_by_name_asc` (:507) / `test_products_items_order_by_name_desc` (:521) — anon `allItems orderBy name` (Item has no order gate → runs anon); expected = ALL items by name. Anonymous narrows to non-private items under non-private categories. Re-pin: subject is ordering, not visibility → prefer staff (A) to keep the full-set ordering assertion; or (B) re-derive `expected` through the post-cascade ORM order.
- `test_products_items_filter_and_order_compose` (:613) — anon, filter category=first + order name; expected = all items in that (public) category by name. Items have random privacy → narrowed. Re-pin: (B) narrow ORM expectation to `is_private=False` under that category, or staff (A).
- `test_products_categories_items_connection_fixed_query_count` (:669) — anon `allCategories { itemsConnection(first:2) }`; iterates returned categories, asserts each item belongs to its category, AND asserts the query count is EQUAL across `seed_data(1)`/`seed_data(3)` AND `== 2` (the N+1 disproof). Anonymous now sees only public categories and their non-private items → the per-category membership checks still hold (they check subset membership, not full count) BUT the windowed `itemsConnection` prefetch child now also runs `ItemType.get_queryset`'s cascade. CRITICAL: confirm the cascade does NOT add a per-parent round-trip — the `__in` subqueries compile inline (Decision 7), so the count should stay a fixed 2; re-verify the `== 2` from a real run under the activated hooks. If the count changes, re-derive the absolute and update both the assertion and the docstring's "measured ~52 / ~102" fallback numbers. Subject is the windowed-prefetch N+1 disproof → may keep anonymous (the cascade-on-prefetch interaction is exactly what should be proven query-stable) but the `==2` MUST come from a real run, not the pre-cascade value.

SAFE (no re-pin needed), recorded so the audit is exhaustive:
- Staff-client tests: `test_products_categories_filter_by_name_exact_as_staff` (:363), `test_products_categories_filter_by_starts_with_via_all_lookups` (:451), `test_products_categories_order_by_name_as_staff` (:552), `test_products_items_order_by_related_category_name_as_staff` (:585) — staff bypasses all four hooks; assertions hold unchanged.
- Denial tests (gate fires on input shape, independent of cascade per Decision 11): `test_products_categories_filter_by_name_denied_for_anonymous` (:376), `test_products_categories_name_permission_fires_for_non_exact_lookup` (:390), `test_products_items_related_category_name_permission_fires_for_anonymous` (:411), `test_products_categories_order_by_name_denied_for_anonymous` (:535), `test_products_items_order_by_related_category_name_denied_for_anonymous` (:567) — assert a "staff user" GraphQLError, produced before/independent of visibility narrowing.

**Test-tree sweep (per worker-1.md "Wire-shape conversions touch all three test trees").** Slice 4 does NOT change a field's wire shape — the four `get_queryset` hooks change row *visibility*, not the GraphQL field envelope, so no `edges`/`node`/argument shape changes. The per-app non-live tree (`examples/fakeshop/apps/products/tests/`) executes `schema.execute_sync` against the SAME products schema, so the activated hooks could affect any anonymous-context in-process test there too. **Test step:** Worker 2 runs `grep -rn "allEntries\|allItems\|allCategories\|allProperties\|get_queryset\|is_private" examples/fakeshop/apps/products/tests/` to confirm no in-process products test asserts anonymous root-field row counts that the activation would flip. If any exist, re-pin them in this same change (same audit rule — staff client or post-cascade ORM expectation). The package `tests/` tree uses synthetic graphs / the package's own types and does not import the fakeshop products schema's anonymous root fields, so it is out of Slice-4 scope (Slices 1-3 own `tests/test_permissions.py` etc.). Worker 2 records the grep result in the build report.

### Implementation discretion items

1. **Re-pin strategy per at-risk test: staff-client (A) vs. post-cascade-ORM-expectation (B).** Both are valid; the plan recommends (A) for SQL-shape/optimizer/ordering-mechanics tests whose subject is orthogonal to anonymous visibility, (B) for tests whose subject IS root-field row content. Worker 2 picks per test using that heuristic. (This is a stylistic/equivalent-shape choice assessed and delegated — NOT an architectural escape hatch; either re-pin keeps the test green and meaningful.)
2. **Private-fixture construction in the cascade tests.** After `seed_data(N)`, whether to flip an existing seeded row's `is_private` via ORM `update()`/`.save()` or to `Model.objects.create(...)` a dedicated private/public chain is Worker 2's call — both keep the AGENTS.md first-line `create_users(1)`/`seed_data(N)` rule. If two-or-more cascade tests duplicate the same private-split setup, extract a module-local `_seed_private_split()` helper; do not pre-build it.
3. **Import grouping for the now-live `apply_cascade_permissions`** — add to the existing `from django_strawberry_framework import (...)` group vs. a separate line; let `ruff check --fix` / isort settle the exact order.
4. **Absolute query counts** in `test_cascade_query_count_fixed` and the re-verified `== 2` in `test_products_categories_items_connection_fixed_query_count` — derived from a real run under the activated hooks, Worker 2's measured values; never guessed.

### Spec slice checklist (verbatim)

- [x] [`examples/fakeshop/apps/products/schema.py`][products-schema]: the four commented cascade-permission `get_queryset` hooks (one per type, already correctly marked `TODO-ALPHA-034-0.0.10` — only the uncomment remains) activate: staff sees everything; a user with the matching `view_<model>` permission sees all non-private rows; everyone else gets `queryset.filter(is_private=False)` **plus** `apply_cascade_permissions(cls, ..., info)` so rows pointing at hidden targets drop out.
- [x] [`examples/fakeshop/test_query/test_products_api.py`][test-products]: live `/graphql/` coverage with **real permission users** — first line `services.create_users(1)` per [`AGENTS.md`][agents] (never hand-rolled users, card DoD) — across the products 2-deep FK chain (`Entry → Item → Category` / `Entry → Property → Category`): an anonymous request sees no entry whose item's category is private; the `view_item` user sees non-private items but still loses entries under private categories (the cascade composes per edge); staff sees everything; the per-request query count is pinned fixed (no per-row cascade queries).
- [x] **Audit the products seeders' `is_private` defaults and re-pin every existing live assertion that counted would-be-hidden rows.** Activating the four hooks flips anonymous-request visibility across the *entire* products live suite, not just the new tests — this is the single most likely source of churn when the card lands, so it is a load-bearing setup step, not a contingency. Confirm the default seed paths produce public (`is_private=False`) rows, enumerate every assertion whose count would change once anonymous requests stop seeing private-target rows, and re-pin them in this same change.
- [x] Existing products live assertions that counted public-only rows keep passing — the activation must be observable only where private fixtures exist; the suite seeds the private/public split it needs through the established service helpers.

### Notes for Worker 1 (spec reconciliation)

- **Spec Risks "Live-suite sensitivity" preferred answer is inaccurate for this suite (NOT a blocker; flag for final-verification spec edit).** Spec line 498 states the preferred answer is that "the existing suite runs against public-only seeded fixtures (the seeders default `is_private=False` paths), so churn should be minimal." The audit contradicts this: `seed_data` (services.py:183-204) makes Category/Property `is_private` a deterministic 50/50 split (`% 2 == 1`), and Item/Entry `is_private` is `random.choice([True, False])` (services.py:218/228). The seeders do NOT default to public-only. Anonymous-running assertions across the suite WILL churn (11 enumerated above). The spec's documented *fallback* (fixture-scoping; re-pin per test) is the actual path. RECOMMENDATION at final verification: edit the Risks "Live-suite sensitivity" bullet to record that the seeders are 50/50 (not public-only) so the re-pin was load-bearing-as-expected, not surprise churn — the checklist bullet 3 (line 73) already correctly frames it as load-bearing, so the contradiction is only in the Risks "preferred answer" wording, a one-line accuracy tightening. Do NOT change the slice contract.
- **Spec checklist bullet 4 (line 74) wording vs. reality.** "Existing products live assertions that counted public-only rows keep passing" — strictly, almost no anonymous assertion counted public-only rows (they counted FULL sets or first-by-id rows). Bullet 4 holds in spirit (staff/denial tests keep passing untouched; the activation is observable only where private fixtures matter), but the re-pin in bullet 3 is what makes the rest pass. No spec edit needed — bullet 3 already owns this; recorded so final-verification can confirm bullets 3 and 4 are not read as contradictory.
- **`test_cascade_query_count_fixed` absolute count interaction with the Slice-2 downgrade.** `EntryType` cascades through `item`/`property` to `CategoryType`, all custom hooks. The Slice-2 pin (spec line 443) established that a relation whose target hook cascades downgrades `select_related → Prefetch`. So the live `allEntries { item { category } }` shape under the activated Entry/Item/Category hooks may NOT stay the single `select_related` query of the un-cascaded :289 test (which currently asserts `len(captured)==1`). Worker 2 must derive the absolute from a real run; if it is no longer 1, that is the correct activated behavior (the downgrade firing), not a regression. Flagged so a reviewer does not read a count change as a bug.

---

## Build report (Worker 2)

### Files touched

- `examples/fakeshop/apps/products/schema.py` — (1) removed the staged-seam TODO instruction comment + uncommented the `apply_cascade_permissions` import into the real first-party `from django_strawberry_framework import (...)` group (ruff/isort settled the alpha order); (2) uncommented the four `get_queryset` cascade hooks on `CategoryType`/`ItemType`/`PropertyType`/`EntryType`; (3) **source-defect fix (see Notes for Worker 1):** each hook's user read changed from `getattr(info.context, "user", None)` to `getattr(getattr(info.context, "request", None), "user", None)`. The committed (commented) bodies read `info.context.user`, but the live Strawberry-Django context is `strawberry.django.context.StrawberryDjangoContext` (a dataclass with `request`/`response`, **no `user`**) — so as-written every staff/`view_<model>` branch was dead (`user` always `None`). The package's own canonical request resolution is `info.context.request` (`utils/permissions.py::request_from_info`, which the shipped `check_<field>_permission` gates use), so this aligns the hooks with the package convention.
- `examples/fakeshop/test_query/test_products_api.py` — dropped `@pytest.mark.skip` + filled the 5 cascade-test stubs (added module-local `_login(username)` and `_seed_cascade_split()` helpers); rewrote the staged-seam banner comment to a live section header; re-pinned 10 existing at-risk assertions (see below) + updated the stale `_RELAY_MAX_RESULTS` comment block.
- `examples/fakeshop/apps/products/tests/test_schema.py` — re-pinned the 2 in-process anonymous-context tests (`test_project_schema_executes_products_categories_list`, `test_project_schema_traverses_products_relations`) to the post-cascade ORM visibility; replaced the stale module-level `from config.schema import schema` binding with a `project_schema` fixture that re-imports the schema fresh per test (registry-consistent — root-cause fix for a test-isolation defect the activation exposed; see Notes for Worker 1).

### Tests added or updated

**5 new live cascade tests (filled stubs, anonymous-context hooks resolve no user → public-only branch; staff/`view_item` resolve via real `force_login`):**

- `::test_cascade_anonymous_sees_no_entries_under_private_categories` — `create_users(1)` + a hand-built private-cat/public-item/public-entry chain via `_seed_cascade_split()`; asserts anonymous `allEntries` excludes the entry under the private category (cascade reaches Entry→Item→Category) AND includes the fully-public control entry (narrowing, not blanket-empty).
- `::test_cascade_view_item_user_matrix` — `force_login(view_item_1)`; asserts `allItems` includes the public item under the private category (ItemType's `view_item` rule), yet `allEntries` excludes that item's entry (EntryType cascade still reaches the hidden category; that user holds no `view_entry`). The per-edge composition pin.
- `::test_cascade_staff_sees_everything` — `force_login(staff_1)`; asserts `allCategories`/`allItems` returned counts == full ORM counts (capped at `_RELAY_MAX_RESULTS`). Pins the `is_staff` bypass (NOT `is_superuser`).
- `::test_cascade_query_count_fixed` — anonymous `allEntries { value item { name category { name } } }` under `CaptureQueriesContext`; asserts `len(captured) == 3` (derived empirically; see Implementation notes), `"IN (SELECT"` present (cascade composed inline, zero added round-trips, Decision 7), and NO inter-products JOIN (forward-FK downgraded to Prefetch chain).
- `::test_cascade_composes_with_filter_and_order_live` — shape (a): anonymous `allCategories(orderBy:[{name:ASC}])` raises the `check_name_permission` "staff user" gate error (gate fires on input shape, Decision 11); shape (b): anonymous `allItems(filter:{category:{id:{exact:<public-cat>}}}, orderBy:[{name:ASC}])` returns the cascade-narrowed-then-ordered set, derived from the equivalent post-cascade ORM query.

**10 existing live assertions re-pinned** (old → new; derivation source = a throwaway probe run under the activated hooks, deleted after — see Validation run):

| Test | Old | New | Strategy |
|---|---|---|---|
| `test_emitted_globalid_is_model_anchored` | anon `allItems`, first Item | staff client (first item always visible) | A (subject = GlobalID emit/decode) |
| `test_globalid_filter_round_trip` | anon `allItems` emit + filter | staff client for both emit + filter | A |
| `test_type_strategy_opt_out_reproduces_type_name` | anon `allItems`, first Item | staff client (override/reload order preserved) | A |
| `test_products_optimizer_merges_duplicate_root_field_nodes_over_http` | anon, `len==1` + JOIN, full item set via `select_related` | anon, `len==2` (1 item slice + 1 category Prefetch, NO JOIN), 1 item-slice assert (the merge), expected via post-cascade ORM (`is_private=False, category__is_private=False`) | B + shape change |
| `test_products_optimizer_prefetches_nested_reverse_fk_depth_2_over_http` | anon, full 25/25/177 sets, `len==3` | anon, `len==3` (unchanged), each level's count via post-cascade ORM (visible cats / visible items / 5-predicate visible entries) | B |
| `test_products_optimizer_selects_nested_forward_fk_depth_2_over_http` | anon, capped-100 page, `len==1` + JOIN | anon, full visible set (< cap) via 5-predicate post-cascade ORM, `len==3` Prefetch chain (no JOIN), `"IN (SELECT"` present | B + shape change |
| `test_products_categories_filter_by_relay_own_pk_global_id_in` | first 2 cats (cat 1 is odd-index PRIVATE) | first 2 **public** cats (`filter(is_private=False)`) | pick-public (anon path kept) |
| `test_products_items_filter_by_related_category_global_id` | first cat, ALL its items | first **public** cat, items via `filter(category=..., is_private=False)` | B |
| `test_products_items_order_by_name_asc` / `_desc` | ALL items by name | post-cascade ORM `filter(is_private=False, category__is_private=False).order_by(±name)` | B |
| `test_products_items_filter_and_order_compose` | first cat, ALL items by name | first **public** cat, `filter(category=..., is_private=False).order_by(name)` | B |

`test_products_categories_items_connection_fixed_query_count` — assertions unchanged (`== 2` and the cross-cardinality equality hold under the activated hooks: the cascade's `__in` subqueries compile inline, so the windowed-prefetch count stays a fixed 2; verified empirically). Only the docstring's stale "25 parent categories" / "~52/~102" wording was corrected to reflect anonymous narrowing to public categories + the cascade-carrying windowed prefetch child.

**2 in-process tests re-pinned** (`examples/fakeshop/apps/products/tests/test_schema.py`):

- `test_project_schema_executes_products_categories_list` — category-name set → `Category.objects.filter(is_private=False)`.
- `test_project_schema_traverses_products_relations` — forward-FK map → `Item.objects.filter(is_private=False, category__is_private=False)`; reverse-FK nested-items map → public categories with each one's non-private items.

### Validation run

- `uv run ruff format .` — pass (reformatted `test_products_api.py` once — my own multi-line construct normalization, owned by the formatter; no `git checkout` used).
- `uv run ruff check --fix .` — pass ("All checks passed!"); zero residual lint.
- `uv run python scripts/check_trailing_commas.py` — reformatted 1 file once, then idempotent ("Fixed 0 file(s)."); re-ran `ruff format`/`ruff check` → clean.
- `git status --short` classification:
  - **Slice-intended (stay):** `examples/fakeshop/apps/products/schema.py`, `examples/fakeshop/test_query/test_products_api.py`, `examples/fakeshop/apps/products/tests/test_schema.py` (all three in `### Files touched`).
  - **Pre-existing / out of scope (NOT my edits this pass; left untouched per the STANDING GUARD):** `django_strawberry_framework/__init__.py`, `django_strawberry_framework/permissions.py` (Slice 1), `tests/test_permissions.py` / `tests/optimizer/test_extension.py` / `tests/test_connection.py` / `tests/test_list_field.py` / `tests/test_relay_node_field.py` (Slices 1-3), `docs/spec-034-permissions-0_0_10.md` (accepted in-flight doc). Confirmed via `git diff --stat` — my diff lands only in the three Slice-4 files. The concurrent em-dash comment swap dissolved as the four hook comments became code.
- Focused tests run (no `--cov*`): `uv run pytest examples/fakeshop/test_query/test_products_api.py examples/fakeshop/apps/products/tests/test_schema.py --no-cov` → **29 passed**, run 3× (different random Item/Entry splits each time) all green; full products tree + live suite `uv run pytest examples/fakeshop/apps/products/ examples/fakeshop/test_query/test_products_api.py --no-cov` → **86 passed**; package tests referencing `apps.products` (`tests/test_list_field.py`, `tests/optimizer/test_*.py`, `tests/types/test_resolvers.py`, `tests/test_permissions.py`, `tests/optimizer/test_extension.py`) → **436 passed, 1 skipped** (the `FAKESHOP_SHARDED`-gated Slice-1 test) — confirms the activation does not break the package tree.
- Throwaway probes used: 9 scripts under `docs/builder/temp-tests/slice-4/` (probe_cascade, probe_staff, probe_repins, probe_shapes, probe_counts, probe_anon_sets, probe_compose, probe_inprocess, probe_isolation), each a `@pytest.mark.django_db` test mirroring the live harness, run with `--no-cov`. All deleted after deriving values (dir is empty).

### Implementation notes

- **Derived query counts (structurally deterministic — independent of the random Item/Entry privacy split; verified stable across 3+ probe runs):** anonymous `allEntries { value item { name category { name } } }` = **3** products queries (entry slice + `item` Prefetch + `category` Prefetch). The forward-FK `select_related("item__category")` downgrades to a **Prefetch chain** because `ItemType`/`CategoryType` now define a custom `get_queryset` (`optimizer/walker.py::_plan_select_relation` plans `select_related` only `if ... and not _target_has_custom_get_queryset(target_type)`). This is **plan-time, user-independent** — staff does NOT restore the JOIN (it only short-circuits the hook's *runtime* return, not the *presence* check). The cascade's `__in` subqueries appear as nested `SELECT`s inside each prefetch query (`"IN (SELECT"`), so 3 round-trips, zero added by the cascade (Decision 7). Other shapes: merge-root `allItems` = 2 (item slice + category Prefetch); reverse-FK `allCategories { items { entries } }` = 3.
- **Observed `is_private` split (`seed_data(1)`):** 25 categories (13 public — deterministic `% 2`), 25 items (~6-8 public — `random.choice`), 176 properties (~95 public), 176 entries (~81 public). Item/Entry/Property privacy is **random per run**, so every re-pinned row-content assertion is derived from the equivalent post-cascade ORM query (API == ORM), never a hardcoded count — only the structurally-deterministic query counts (2/3/3) are pinned as absolutes.
- **Staff query counts carry +2 auth queries** (session + user lookup from `force_login`, inside `CaptureQueriesContext`), so query-count-sensitive pins stay anonymous (clean count, no auth pollution); only row-content pins that need full sets use staff.
- **`_seed_cascade_split()`** hand-creates the private/public chains (NOT `seed_data`, which randomizes Item/Entry privacy) so the cascade tests are deterministic; first line of each cascade test is still `create_users(1)` (the helper runs after) per AGENTS.md.
- **Compose shape (b) chosen anonymous-public-cat-exact** over the originally-planned `view_item` + `id:{in:[...]}`: the `in`-with-two-GlobalIDs shape produced confusing decode behavior entangling the RelatedFilter visibility derivation; the anonymous public-cat `exact` shape cleanly demonstrates Decision 11 (cascade narrows first, then filter+order operate on the visible set) and is deterministic.

### Notes for Worker 3

- The 9 throwaway probes under `docs/builder/temp-tests/slice-4/` were deleted; the dir is empty. No shadow files used (no `django_strawberry_framework/` source touched this pass — the only source change is the example-project `schema.py` hook bodies).
- **The forward-FK / merge optimizer tests now assert a Prefetch-chain shape, not a `select_related` JOIN.** This is correct, expected activated behavior (the hook-presence downgrade), not a regression — Worker 1 flagged the downgrade interaction at the plan's last `Notes for Worker 1` bullet. Re-derive any count by reading `optimizer/walker.py::_plan_select_relation`.
- **`schema.py` carries a source-defect fix beyond the pure uncomment** (`info.context.user` → `info.context.request.user`). Escalated to Worker 1 below; the fix is byte-uniform across all four hooks and is what makes the staff/`view_<model>` matrix work at all.
- Run the suite in BOTH orders if checking isolation: the in-process `test_schema.py` is now isolation-robust via the per-test fresh-schema fixture (it failed only when run AFTER the live suite before the fix).

### Notes for Worker 1 (spec reconciliation)

- **SOURCE DEFECT in the committed hook bodies (fixed in-slice; small mechanically-obvious drift per `worker-2.md`).** The plan stated "the commented bodies ARE the contract" and the bodies read `user = getattr(info.context, "user", None)`. Verified against the live stack: the fakeshop `GraphQLView` uses the stock `strawberry.django.context.StrawberryDjangoContext`, a dataclass exposing only `request`/`response` — **no `user`**. So as-written, `user` was always `None` and the `is_staff` / `has_perm` branches were permanently dead (a throwaway probe confirmed staff saw only the anonymous public subset). The package's own canonical request resolution is `info.context.request` (`utils/permissions.py::request_from_info`, used by the shipped `check_<field>_permission` gates — which is why the existing staff *filter* tests passed while the hook *visibility* did not). Fix applied uniformly to all four hooks: `getattr(getattr(info.context, "request", None), "user", None)`. **This is required for the slice to deliver DoD item 10** (the anonymous/`view_<model>`/staff matrix). RECOMMENDATION: confirm the fix and, if the spec/GLOSSARY body (Slice 5) describes the cascade reading `info.context.user`, correct it to `info.context.request.user` (the package convention). I considered the alternative of a project-level `get_context` shim adding `user` to the context, but rejected it as a non-canonical shim the spec never mentions; reading `info.context.request.user` is the upstream-faithful root-cause fix.
- **The plan's re-pin strategy (A) premise is FALSE: staff does NOT keep the `select_related` JOIN.** The plan said "Under staff the cascade hooks short-circuit to `return queryset`, so the optimizer plans plain `select_related("item__category")` exactly as today." Verified false: the optimizer's `select_related→Prefetch` downgrade is a **plan-time decision keyed on the target type's `has_custom_get_queryset()`** (`optimizer/walker.py::_plan_select_relation`), independent of the hook's runtime return. So the three forward-FK/merge optimizer SQL-shape tests (`..._merges_duplicate_root_field_nodes...`, `..._selects_nested_forward_fk_depth_2...`) could NOT be re-pinned via staff-keeps-the-JOIN; I re-pinned them to assert the new Prefetch-chain shape (the honest, observable consequence of activation) with post-cascade-ORM-derived row content. The reverse-FK depth-2 test keeps its `len==3`. No spec contract changed — the spec names no SQL shape (Decision 7); but the plan's strategy-(A) note for these three tests is inaccurate and should not be read as the actual implementation.
- **Test-isolation defect exposed (fixed in-slice).** `examples/fakeshop/apps/products/tests/test_schema.py` bound `config.schema.schema` at module import. The sibling live suite clears the registry + reloads `config.schema` between tests; a stale composed schema's nested-relation `Prefetch` children resolve the target type's `get_queryset` through the registry, so after a live-suite reload the **nested** list narrowing silently did not fire (the root narrowing still did). The pre-change assertion (full un-narrowed set) masked this; my narrowed re-pin exposed it. Root-cause fix: a `project_schema` pytest fixture that re-imports the schema fresh per test (registry-consistent, mirroring the live suite's reload discipline). This is a pre-existing latent fragility the activation surfaced, not new behavior.
- **Spec Risks "Live-suite sensitivity" preferred answer confirmed inaccurate (Worker 1's prior flag stands).** As Worker 1 noted at plan time: `seed_data` is NOT public-only — Category/Property are a deterministic 50/50 `% 2` split, Item/Entry are `random.choice`. The re-pin was load-bearing (12 assertions across 2 files, plus the 5 new tests), not minimal churn. The one-line Risks-wording tightening Worker 1 recommended still applies.

---

## Review (Worker 3)

Reviewed the Slice-4 contribution only (`### Files touched`: `examples/fakeshop/apps/products/schema.py`, `examples/fakeshop/test_query/test_products_api.py`, `examples/fakeshop/apps/products/tests/test_schema.py`). Confirmed Slice 4 changed **no** `django_strawberry_framework/` source: `git diff --name-only -- django_strawberry_framework/` shows only `__init__.py` (Slice-1 export pair) and `permissions.py` (Slice-1 module) — both out of Slice-4 scope. The other dirty files (`tests/*`, `docs/spec-034…`) are accepted Slices 1–3 + the concurrent sweep, not under this review.

### Source fix verdict (HIGH-attention) — CORRECT, canonical, root-cause

The four hooks now read `user = getattr(getattr(info.context, "request", None), "user", None)` instead of the committed `getattr(info.context, "user", None)`. Verified directly:

- `StrawberryDjangoContext` is a `@dataclass` with fields `['request', 'response']` and **no** `user` (confirmed via `uv run python` introspection: `hasattr(StrawberryDjangoContext, 'user') == False`). The fakeshop view is the stock `strawberry.django.views.GraphQLView` (`config/urls.py #"GraphQLView.as_view"`), so `info.context` is exactly that dataclass. As committed, `getattr(info.context, "user", None)` was permanently `None` → the `user.is_staff` and `user.has_perm(...)` branches in all four hooks were **dead**; staff/`view_<model>` users would have silently seen only the anonymous public subset (a data-visibility-correctness defect, not cosmetic).
- The fix is the package's own canonical request resolution: `utils/permissions.py::request_from_info` resolves `info.context.request`, and the shipped, passing filter gate `filters.py::CategoryFilter.check_name_permission` reads `getattr(request, "user", None)` — i.e. `info.context.request.user`. The hook now matches that convention exactly.
- Reachability confirmed by direct probe (temp test, deleted): anonymous → public-only branch; `view_item_1` → `ItemType` perm branch fires (sees item under a private category) while `EntryType` cascade still drops its entry; `staff_1` → `is_staff` short-circuit returns full set. All three branches reachable and correct.
- Byte-uniform across all four hooks (static-helper overview confirms 2 `getattr()` calls in each of the 4 `get_queryset` symbols, 0 control-flow hotspots).

This is a sound root-cause fix, not a divergence from the slice contract. The spec/GOAL reconciliation it raises is documentation-level (the *consumer-facing example* still shows the broken form) — escalated to Worker 1 below; it is **not** a slice blocker.

### High

None.

### Medium

None.

### Low

None.

### DRY findings

- The four cascade-hook bodies are byte-identical except the `view_<model>` codename string. As the contract states, this is the **consumer-facing per-type contract** (one explicit hook per `DjangoType`, the documented surface a consumer would hand-write) — expected, not a DRY violation. Extracting a shared helper would hide the very surface the example exists to demonstrate.
- Tests: the new live tests correctly factored shared setup into module-local `_login(username)` and `_seed_cascade_split()` helpers (the plan's discretion item 2 — extract when 2+ tests duplicate the same private-split setup; `_seed_cascade_split` is used by 4 of the 5 cascade tests). No genuine duplication remains. The repeated post-cascade ORM predicate `filter(is_private=False, category__is_private=False)` appears across several re-pins, but each is an independent ORM mirror of that test's own visible set (the file's established API==ORM pattern, AGENTS.md "data-driven assertions"); collapsing them into a shared constant would couple unrelated tests and reduce readability. Not flagged.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` shows only the Slice-1 cascade-export pair (`apply_cascade_permissions` / `aapply_cascade_permissions`), authorized by spec-034 Slice 1 Decision 4 (spec lines 56-62). **Slice 4 changes no package `__all__` or re-export** — the only source it touches is the example-project `schema.py`. Pass.

### CHANGELOG sanity

Not applicable; slice did not modify `CHANGELOG.md`.

### Documentation / release sanity

N/A; Slice 4 touched no `docs/`, `KANBAN.md`, or release files (the dirty `docs/spec-034…` is an accepted in-flight doc, not a Slice-4 edit). Doc reconciliation (GOAL/GLOSSARY `info.context.user`) is Slice 5 / Worker 1 work — see Notes for Worker 1.

### Static helper

Ran `uv run python scripts/review_inspect.py examples/fakeshop/apps/products/schema.py --output-dir docs/shadow` (the slice touches an existing `.py` and the hook bodies carry review-worthy logic). Overview confirmed: import `apply_cascade_permissions` now first-party; 4 `get_queryset` symbols each with 2 `getattr()` calls (the user-resolution fix); 0 control-flow hotspots; repeated literals are model-`Meta` declarations (`is_private`/`description`/`created_date`/`updated_date`), not extractable duplication. Shadow files are regenerable; no shadow line numbers cited.

### Test-tree sweep (cross-tree, per worker-3.md)

Slice 4 does not change any field's wire shape (the hooks change row *visibility*, not the `edges`/`node`/argument envelope), so a full wire-shape sweep is not triggered — but the activation flips anonymous-context products visibility, so I swept all three trees for anonymous products root-field assertions anyway:

- `examples/fakeshop/apps/products/tests/` — only `test_schema.py` asserts products visibility; re-pinned (2 in-process tests) in this slice. Confirmed.
- `examples/fakeshop/tests/` (project-level) — zero hits.
- `tests/` (package) — references `allItems`/`is_private` etc. but builds synthetic graphs / uses the package's own types; only `test_scalars.py`, `test_permissions.py`, `test_export_schema.py` import `config.schema`/products schema, and none assert anonymous products root-field row counts (`test_scalars.py` uses a separate `{ big }`/`echo` scalar schema; `test_export_schema.py` exports SDL structure; `test_permissions.py` uses the package permission surface). Ran them: 593 passed, 1 skipped (the `FAKESHOP_SHARDED`-gated Slice-1 test) — the activation does not break the package tree. No stale untouched tree.

### What looks solid

- **Source fix** — root-cause, canonical, byte-uniform, all branches reachable (verified by probe).
- **The 12 re-pins** — each reflects correct post-cascade visibility, derived from the equivalent post-cascade ORM query (API==ORM) rather than a hardcoded count, so they are robust across `seed_data`'s random Item/Entry privacy split. Spot-checked the highest-risk:
  - The forward-FK 5-predicate ORM mirror (`is_private=False, item__is_private=False, item__category__is_private=False, property__is_private=False, property__category__is_private=False`) is a faithful mirror of the actual cascade because all four FKs (`Entry.item`, `Entry.property`, `Item.category`, `Property.category`) are **non-nullable** (`models.py`) — so `apply_cascade_permissions`'s `Q(<edge>__in=…) | Q(<edge>__isnull=True)` disjunct is always empty and the `OR isnull` term adds no rows the mirror would miss. Confirmed against `permissions.py::_walk`.
  - The merge test (`len==2`: one item slice + one category Prefetch, no inter-products JOIN) and the forward-FK depth-2 test (`len==3` Prefetch chain, `IN (SELECT` present, no JOIN) correctly reflect the Slice-2 `select_related→Prefetch` plan-time downgrade keyed on `has_custom_get_queryset()` — Worker 2 correctly corrected Worker 1's plan premise that staff would keep the JOIN (the downgrade is plan-time, user-independent). The `IN (SELECT` assertion is non-vacuous (probe confirmed the cascade subqueries genuinely compile inline).
  - The "pick two PUBLIC categories" / "first PUBLIC category" re-pins keep the anonymous path under test (rather than flipping to staff) where the subject is GlobalID-decode / RelatedFilter content — the right call.
- **The 5 new live tests** — first line `create_users(1)` (real users, no mocked context); the visibility matrix is load-bearing and adversarially confirmed non-vacuous (anonymous returns ONLY the public-chain entry, not blanket-empty; `view_item` sees the item under a private category yet loses its entry — per-edge composition; staff sees the full count incl. private rows). `test_cascade_query_count_fixed` pins an absolute `== 3` derived from a real run plus the `IN (SELECT` and no-JOIN guards, so it cannot pass on a cascade-skipping fall-through. The compose test pins both Decision-11 shapes (gate fires on input shape independent of cascade; non-gated filter+order operates on the cascade-narrowed set).
- **The test-isolation fix** — verified a REAL defect, not scope-creep: a temp probe with the pre-fix module-level binding leaked 8 private items through the un-narrowed nested `items` Prefetch child after a registry-clearing reload (13 returned vs 5 visible), while the fresh-reimport fixture narrowed correctly (8==8, zero leak). The pre-change full-set assertion masked it. The `project_schema` fixture is the registry-consistent root-cause fix and masks nothing.
- Focused suites green and **non-flaky across the random Item/Entry split**: `uv run pytest examples/fakeshop/test_query/test_products_api.py examples/fakeshop/apps/products/tests/test_schema.py --no-cov -q` → **29 passed** on each of 3 consecutive runs. Both file orders (live-first and in-process-first, `-p no:randomly`) → 29 passed, confirming the isolation fix holds in the order that previously failed.

### Temp test verification

Two temp tests created under `docs/builder/temp-tests/slice-4/` (both deleted after use, dir + `__pycache__` removed):
- `test_isolation_defect_probe.py` — proved the isolation defect is real (stale binding leaks private nested items; fresh re-import narrows). Behavior is permanently pinned by the in-slice `test_schema.py` re-pins + `project_schema` fixture, so no promotion needed.
- `test_repins_load_bearing.py` — adversarially confirmed the new cascade tests pin real activated behavior (3 queries + `IN (SELECT` + no JOIN; anonymous drops private-cat entry; `view_item` per-edge disagreement). All behaviors already pinned by the permanent new tests; no promotion needed.
No temp test caught an unpinned bug. No temp test left as the only proof of shipped behavior.

### Notes for Worker 1 (spec reconciliation)

- **Escalated (Medium, documentation-only — accepted with escalation): the consumer-facing `info.context.user` example diverges from the now-correct fakeshop hook.** Worker 2's source fix changes the fakeshop hooks to `info.context.request.user` (correct — the live `StrawberryDjangoContext` has no `.user`). But the package's own canonical showcase still uses the **broken** form: `GOAL.md` astronomy showcase (`GOAL.md #"user = getattr(info.context, \"user\", None)"`, two `get_queryset` bodies + the `_user(info)` helper) reads `getattr(info.context, "user", None)`, and `docs/GLOSSARY.md`'s `apply_cascade_permissions` entry (spec line 24 names it the "canonical surface") shows the same shape. The spec's other `info.context.user` mentions (spec lines 351/443/461/538) are conceptual ("the request user") or anti-mock DoD phrasing, NOT a literal hook-body API contract — and Revision-2-L3 already moved the cache-rule wording *away* from `info.context.user`. So there is no spec *contract* conflict, but the showcase/GLOSSARY example, if a consumer copy-pastes it against the stock `StrawberryDjangoContext`, would silently grant nobody staff/perm visibility. **Resolution paths for Worker 1's final verification / Slice 5 doc work:** (a) correct the `GOAL.md` + `GLOSSARY.md` examples to `getattr(getattr(info.context, "request", None), "user", None)` (the upstream-faithful, package-convention form Worker 2 chose) — recommended, matches `request_from_info` / the shipped filter gates; or (b) document a `get_context` shim that adds `.user` to the context (Worker 2 considered and rejected this as a non-canonical shim the spec never mentions — I concur it is the weaker option). This is a one-pattern doc-accuracy fix, not a design change. Confirm the fakeshop fix (it is required for DoD item 10) and pick a path for the showcase in the same final-verification pass.
- **Confirming two of Worker 2's prior escalations (independently verified, not blockers):** (1) the plan's re-pin strategy-(A) premise "staff keeps the `select_related` JOIN" is false — the downgrade is plan-time on `has_custom_get_queryset()`, user-independent; Worker 2's Prefetch-chain re-pins are the honest shape. (2) The spec Risks "Live-suite sensitivity" preferred answer (public-only seeders) is inaccurate — `seed_data` is a deterministic Category/Property `% 2` split + random Item/Entry; the re-pin was load-bearing as the checklist (not the Risks preferred answer) framed it. Both warrant the one-line spec-wording tightenings Worker 1 already flagged; neither changes the contract.

### Review outcome

`review-accepted`. The source fix is a correct, canonical, root-cause repair (verified against the live `StrawberryDjangoContext` shape and the package's own `request_from_info` convention). All 12 re-pins reflect correct post-cascade visibility (API==ORM, non-vacuous, spot-checked adversarially). The 5 new live tests pin the load-bearing visibility matrix and the fixed query count with non-skippable guards. The test-isolation fix repairs a real defect (probe-confirmed) and masks nothing. Focused suites green and non-flaky across 3 random splits and both file orders. Zero High / zero Medium / zero Low findings. One Medium-level documentation reconciliation (the showcase `info.context.user` form) is transparently **escalated** to Worker 1's final verification per the worker-3.md escalation clause — it requires spec/GOAL/GLOSSARY context Worker 2 cannot own and is not a slice-implementation defect.

---

## Final verification (Worker 1)

Pass type: final-verification for Slice 4 (Worker 3 set `review-accepted`, 0 High/Medium/Low, one contract-accuracy reconciliation escalated). Read-only against source/tests; spec edits only; STANDING GUARD held (no `git checkout`/`restore`/`stash`/`reset`/`clean`).

### Checklist 1 — Spec slice checklist audit (every `- [x]` truly landed)

Audited all four ticked boxes against the live diff (`git diff --stat` on the three Slice-4 files: `schema.py` 85±, `test_schema.py` 70±, `test_products_api.py` 547± → 538 ins / 164 del) and direct source reads. All four landed; none over-ticked, none under-ticked:

- **Box 1 (four-hook activation).** Confirmed live in `examples/fakeshop/apps/products/schema.py`: the `apply_cascade_permissions` import is in the real first-party group (schema.py:36-41), and all four `get_queryset` hooks (`CategoryType` :67-75, `ItemType` :99-107, `PropertyType` :131-139, `EntryType`) are uncommented with the staff→all / `view_<model>`→`filter(is_private=False)` / else→`apply_cascade_permissions(cls, queryset.filter(is_private=False), info)` shape, each reading `user = getattr(getattr(info.context, "request", None), "user", None)` (the source fix — see Reconciliation below). **TRUE.**
- **Box 2 (live `create_users(1)` matrix anon/`view_item`/staff + fixed query count).** Confirmed: 5 `test_cascade_*` functions present, **0** `pytest.mark.skip` decorators remaining in the file, every cascade test's first line is `create_users(1)`; `test_cascade_anonymous_…`, `test_cascade_view_item_user_matrix`, `test_cascade_staff_sees_everything` (force_login(staff_1)), `test_cascade_query_count_fixed` (`CaptureQueriesContext` + `assert "IN (SELECT" in all_sql` guard at :1073), `test_cascade_composes_with_filter_and_order_live`. **TRUE.**
- **Box 3 (is_private audit + re-pins).** Confirmed: the 10 live re-pins (table in the build report) + the 2 in-process re-pins in `test_schema.py` landed (`project_schema` fixture :22; both `test_project_schema_*` tests now derive expectations from `Category.objects.filter(is_private=False)` / `Item.objects.filter(is_private=False, category__is_private=False)` at :68/:113-114/:132-133). **TRUE.**
- **Box 4 (existing public-only-counting assertions stay green).** Confirmed by the focused run (29 passed, twice) — the staff/denial SAFE tests and the re-pinned anonymous tests all pass. **TRUE.**

### Checklist 2 — DRY across Slices 1–4

The four repeated hook bodies in `products/schema.py` are the per-type consumer contract (one explicit hook per `DjangoType` — the documented surface a consumer hand-writes), expected, not a violation. No genuine new duplication: the two module-local test helpers (`_login`, `_seed_cascade_split` at test_products_api.py:868/875) are justified extractions (4 of 5 cascade tests share `_seed_cascade_split`); the repeated post-cascade ORM predicate is an independent per-test API==ORM mirror (the file's established data-driven pattern), correctly not collapsed. Cross-file test-fixture duplication remains deferred to the integration pass (carried in worker-1 memory since Slice 2). No DRY block.

### Checklist 3 — Focused existing tests (run twice, `--no-cov`)

`uv run pytest examples/fakeshop/test_query/test_products_api.py examples/fakeshop/apps/products/tests/test_schema.py --no-cov -q`:
- Run 1: **29 passed** in 14.92s.
- Run 2: **29 passed** in 15.11s.

Green both runs, no flake across the two random Item/Entry `is_private` seeds. `--no-cov` used; no `--cov*` flag.

### Checklist 4 — Spec reconciliation (adjudicated)

- **The `info.context.user` vs `info.context.request.user` contract (central reconciliation) — DECIDED: canonical consumer pattern is `info.context.request.user`.** The activated fakeshop hooks correctly read the user off the request, matching the package convention (`utils/permissions.py::request_from_info`, the shipped `FilterSet`/`OrderSet` `check_<field>_permission` gates) because the live `strawberry.django.context.StrawberryDjangoContext` is a dataclass with only `request`/`response` (no `.user`). I rejected introducing a `.user` convenience property: it would be a new, unscoped package source surface, and the upstream-faithful `request`-resolution is already the established convention — pulling a shim into this card is out of scope and the fakeshop source fix stands as the root-cause repair. Edited the spec's **User-facing API code example** (was `getattr(info.context, "user", None)` at line 163) to `getattr(getattr(info.context, "request", None), "user", None)`, plus a one-paragraph note explaining why (so a future reader does not "fix" it back). The other four spec `info.context.user` mentions (lines 351/402/443/461/538) are conceptual prose / anti-mock DoD phrasing referring abstractly to "the request user" — NOT literal hook-body API contracts — and were left unchanged (verified each in context). GLOSSARY (line 567 example) is in Slice 5's doc scope and is flagged for correction there; GOAL.md (lines 116/138 showcase bodies + 328 `_user(info)` helper) is NOT in Slice 5's doc list (spec line 479) — recorded as an authorized Slice-5 doc-accuracy follow-up below so the maintainer/Slice-5 author does not re-discover it.
- **Live-suite-sensitivity "preferred answer" inaccuracy — CORRECTED.** The Risks bullet (line 498) claimed the seeders are public-only with minimal churn. Rewrote it to reality: `Category`/`Property` `is_private` is a deterministic ~50/50 `% 2` split and `Item`/`Entry` is per-row `random.choice`, so the re-pin was load-bearing (12 assertions across two files), taking the documented fallback path as the actual one. Contract unchanged.
- **"Uncomment only" framing — RECONCILED minimally.** The Current-state bullet (line 96) said the commented body "is exactly the contract this spec ships." Reworded to "encodes the contract … save for one mechanical fix Slice 4 applied on activation" naming the `request.user` correction and cross-referencing the User-facing API note, so the activation reads as uncomment **plus** that uniform one-line correction.

`uv run python scripts/check_spec_glossary.py --spec docs/spec-034-permissions-0_0_10.md` → `OK: 43 terms` (after all edits).

### Summary

Slice 4 is `final-accepted`. All four verbatim checklist boxes truly landed (audited against the diff; none over-/under-ticked). The source fix (`info.context.user` → `info.context.request.user`, byte-uniform across all four hooks) is the correct, canonical root-cause repair and is required for DoD item 10; it is adopted as the spec's canonical consumer pattern. Focused suite green twice (29 passed each), no flake across random seeds. Four spec edits made (User-facing API example + note, Current-state framing, Risks "Live-suite sensitivity"); glossary checker `OK`. No DRY block. Two Slice-5 doc-accuracy follow-ups carried forward (GLOSSARY in-scope; GOAL.md flagged as an authorized addition / maintainer surface).

### Spec changes made (Worker 1 only)

1. `docs/spec-034-permissions-0_0_10.md` line 163 (User-facing API code example), Slice 4 — changed `user = getattr(info.context, "user", None)` to `user = getattr(getattr(info.context, "request", None), "user", None)`. Reason: the live `StrawberryDjangoContext` has no `.user`; the broken form silently collapses staff/`view_<model>` branches to anonymous, and the activated fakeshop hooks (correctly) use the `request` form. The example is the canonical copy-pasteable consumer surface and must match the shipped contract.
2. `docs/spec-034-permissions-0_0_10.md` after the User-facing API code block (~line 169), Slice 4 — added one paragraph explaining the `info.context.request.user` resolution (StrawberryDjangoContext shape, `request_from_info` / filter-gate convention, the silent-`None` failure mode) so the example is not "corrected" back to the broken form. Reason: make the canonical pattern self-documenting in the spec.
3. `docs/spec-034-permissions-0_0_10.md` line 96 (Current-state, fakeshop activation site), Slice 4 — reworded "the body text is exactly the contract this spec ships" to "encodes the contract … save for one mechanical fix Slice 4 applied on activation" naming the `request.user` correction. Reason: the activation was an uncomment **plus** a uniform one-line user-read fix, not a pure uncomment; the prior wording was inaccurate post-build.
4. `docs/spec-034-permissions-0_0_10.md` line 498 (Risks, "Live-suite sensitivity"), Slice 4 — replaced the "public-only seeders, minimal churn" preferred answer with the accurate seeder reality (deterministic ~50/50 Category/Property `% 2` split + random Item/Entry) and recorded the re-pin as load-bearing (12 assertions across two files, fallback path taken as actual). Reason: the preferred-answer wording was factually wrong about the seeders; contract unchanged.

### Slice-5 doc-accuracy follow-ups (carried forward)

- **GLOSSARY (in Slice 5's doc scope, spec line 475):** `docs/GLOSSARY.md` line 567's `apply_cascade_permissions` consumer example reads `user = getattr(info.context, "user", None)`. Correct it to `getattr(getattr(info.context, "request", None), "user", None)` in Slice 5's GLOSSARY body rewrite (same one-pattern fix; matches the package convention).
- **GOAL.md (NOT in Slice 5's doc list, spec line 479) — authorized addition / maintainer surface:** `GOAL.md`'s astronomy showcase has the same broken form in two `get_queryset` bodies (lines 116, 138) and the `_user(info)` helper (line 328). Recommend adding the GOAL.md correction to Slice 5's authorized doc edits (it is the same literal-code defect class, security-relevant if copy-pasted), or surface it to the maintainer as a standalone doc fix. Worker 1 did NOT edit GOAL.md this pass (Slice 4 owns no GOAL.md scope and Worker 1 does not edit source/docs outside the active spec); flagged for the Slice-5 planning pass to fold in with maintainer authorization.

---

## Build report (Worker 2, pass 2)

Gate-fix apply-changes pass. The final test-run gate (`bld-final.md`) found **1** deterministic
full-sweep failure:
`examples/fakeshop/apps/products/tests/test_schema.py::test_project_schema_traverses_products_relations`
— a test-isolation gap in the Slice-4 `project_schema` fixture. This pass is a **pure test-fixture
isolation fix**; `permissions.py` and the products `schema.py` activation are unchanged (accepted,
correct). STANDING GUARD held — no `git checkout`/`restore`/`stash`/`reset`.

### Files touched

- `examples/fakeshop/apps/products/tests/test_schema.py` — **only file changed this pass.** Rewrote
  the `project_schema` fixture (was a bare `importlib.import_module("config.schema").schema`) to
  mirror the proven reload discipline in
  `test_query/test_products_api.py::_reload_products_project_schema`: (1) `registry.clear()`, (2)
  reload (or first-import) `apps.products.schema` to **re-register the products `DjangoType` classes
  with their activated cascade hooks FIRST**, (3) reload (or first-import) `config.schema` so the
  composed project schema binds the activated products types, then return `config_schema.schema`.
  Added `import sys` and `from django_strawberry_framework.registry import registry`; `ruff
  check --fix` settled the latter into the first-party import group (its own placement, not drift).
  No assertion was weakened; the three tests using the fixture (`test_project_schema_executes_…`,
  `test_project_schema_traverses_…`, `test_project_schema_includes_products_types`) are unchanged
  except for inheriting the robust fixture.

### Validation run (focused, ordering-dependent — all `--no-cov`, never `--cov*`)

- **Reproduction (pre-fix), polluting suite first:**
  `uv run pytest examples/fakeshop/test_query/test_library_api.py examples/fakeshop/apps/products/tests/test_schema.py::test_project_schema_traverses_products_relations --no-cov -p no:randomly -q`
  → **`1 failed, 104 passed`**. The failing assert was
  `got_item_category == expected_item_category` with "Left contains 6 more items" (items under
  private categories leaking) — matches the gate diagnosis exactly.
- **Same command (post-fix):** → **`105 passed`**. Failure resolved.
- **In-isolation still green:** `uv run pytest examples/fakeshop/apps/products/tests/test_schema.py --no-cov -q`
  → **`3 passed`**.
- **Broader products+live combination (multiple polluting suites first), post-fix:**
  `uv run pytest examples/fakeshop/test_query/test_scalars_api.py examples/fakeshop/test_query/test_glossary_api.py examples/fakeshop/test_query/test_products_api.py examples/fakeshop/apps/products/tests/ --no-cov -p no:randomly -q`
  → **`115 passed`** — confirms no new isolation issue and that the live products suite (which
  self-reloads via its autouse fixture) is unaffected.
- **Post-ruff re-run:** `uv run pytest examples/fakeshop/test_query/test_library_api.py examples/fakeshop/apps/products/tests/test_schema.py --no-cov -p no:randomly -q`
  → **`107 passed`**.
- **ruff:** `uv run ruff format .` → `267 files left unchanged` (zero format drift from my edit);
  `uv run ruff check --fix .` → `Found 1 error (1 fixed, 0 remaining)` (the fix was isort settling
  the `registry` import into the first-party group — legitimate ordering of the import I added, not
  drift to hand-revert); re-check on the file → `All checks passed!`. Did NOT run the full sweep
  (Worker 1's gate re-run); never passed `--cov*`.
- **`git status --short` classification:** my only diff this pass is
  `examples/fakeshop/apps/products/tests/test_schema.py` (the gate fix — stays). All other dirty
  tracked files (`schema.py`, `test_products_api.py`, `permissions.py`, `__init__.py`, the
  `tests/*` package files, the docs + `db.sqlite3`) are pre-existing accepted Slices 1-5 + concurrent
  work, untouched this pass. `git diff -- examples/fakeshop/apps/products/tests/test_schema.py`
  confirms the only logic change vs HEAD-of-prior-pass is the fixture body.

### Implementation notes (the reload-order fix + why it's root-cause)

- **Root cause (confirmed via the reproduction):** the prior fixture called
  `importlib.import_module("config.schema").schema`. `import_module` returns an **already-cached**
  module without reloading. When a preceding non-products live suite (`test_library_api.py` et al.)
  has run, it did `registry.clear()` + reloaded only its own app schema + `config.schema` —
  **never** `apps.products.schema`. So the cached `config.schema` it leaves behind is composed with a
  products `Item` type whose activated cascade `get_queryset` hook is absent from the registry. The
  in-process fixture then re-served that stale module, the anonymous query saw items under private
  categories, and the forward-FK assertion (`got_item_category == expected_item_category`) failed.
- **Why the fix is root-cause, not a band-aid:** the fix restores the correct reload **order** —
  re-register `apps.products.schema` (so the products types carry their cascade hooks) **before**
  recomposing `config.schema` — exactly mirroring `_reload_products_project_schema`, the discipline
  that makes `test_products_api.py` non-polluting in the first place. The fixture is now correct
  regardless of which suite ran before it (it does not depend on collection order, and uses no
  `@pytest.mark.order` ordering hack). It clears the registry and reloads fresh per-test, so it does
  not leave new pollution for later tests (the same self-contained discipline the live products suite
  already relies on). No assertion changed; the products `schema.py`/`permissions.py` were not
  touched.

### Notes for Worker 3

- **Re-verify command (the exact ordering-dependent reproduction):**
  `uv run pytest examples/fakeshop/test_query/test_library_api.py examples/fakeshop/apps/products/tests/test_schema.py::test_project_schema_traverses_products_relations --no-cov -p no:randomly -q`
  — must be **`105 passed`** post-fix (was `1 failed, 104 passed` pre-fix). Any non-products live
  suite from the gate's polluter list (`test_glossary_api.py` / `test_kanban_api.py` /
  `test_library_api.py` / `test_scalars_api.py` / `test_scalars_filter_api.py`) reproduces it.
- **Fix mechanism:** the `project_schema` fixture now does `registry.clear()` → reload
  `apps.products.schema` → reload `config.schema` (same order as
  `test_products_api.py::_reload_products_project_schema`), so the composed schema always binds the
  **activated** products types with their cascade hooks, independent of prior cross-suite registry
  state. The only file changed this pass is `test_schema.py`; no source change.

### Notes for Worker 1

- **Consolidation idea (not actioned — minimal correct fix preferred for this failure):** both the
  live products suite (`test_products_api.py::_reload_products_project_schema`) and this in-process
  suite (`test_schema.py::project_schema`) now carry the same three-step reload discipline
  (clear registry → reload `apps.products.schema` → reload `config.schema`). A future cleanup could
  hoist a single shared reload helper (e.g. into a `conftest.py` under `examples/fakeshop/` or a small
  test-utility module) consumed by both, so the products-reload-first invariant lives in one place.
  Not done here to keep the gate fix minimal and root-caused to the failing fixture; flagged for a
  later DRY-consolidation pass.

---

## Review (Worker 3, pass 2)

Re-review of the Slice-4 gate-fix. Scope reviewed: only the `project_schema` fixture rewrite in
`examples/fakeshop/apps/products/tests/test_schema.py` (Worker 2 pass-2). The other dirty tracked
files (`schema.py`, `test_products_api.py`, `permissions.py`, `__init__.py`, `tests/*`, docs,
`db.sqlite3`) are prior accepted Slices 1-5 + concurrent work, NOT this pass — out of scope.
Inspected read-only via `git diff -- examples/fakeshop/apps/products/tests/test_schema.py`. STANDING
GUARD honored: no `git checkout`/`restore`/`stash`/`reset`; no source/test/spec edit; no commit.

### Fix confirmation — ROOT-CAUSE, CORRECT

The `project_schema` fixture was rewritten from `from config.schema import schema as project_schema`
(module-level bind of the already-cached, possibly-stale composed schema) to a per-test fixture that
mirrors the proven `test_query/test_products_api.py::_reload_products_project_schema` discipline.
Confirmed each acceptance criterion:

- **Reload ORDER is correct.** `registry.clear()` → reload (or first-import) `apps.products.schema`
  FIRST → reload (or first-import) `config.schema` → `return config_schema.schema`. Diffed
  side-by-side against `test_products_api.py:54-65`: byte-identical clear + `sys.modules.get`
  guard + reload/import pattern for both `apps.products.schema` and `config.schema`. Because the
  products `DjangoType` classes (carrying the activated cascade `get_queryset` hooks) are
  re-registered into the cleared registry BEFORE `config.schema` is recomposed, the composed schema
  always binds the activated `Item` type regardless of which suite polluted the registry earlier.
  This is the exact mechanism the gate diagnosis (`bld-final.md`) named as the root cause.
- **Sole legitimate divergence from the reference: no `config.urls` reload.** Correct — the
  in-process fixture executes `schema.execute_sync` (no HTTP request, no URL routing), so the
  reference's `config.urls` reload + `clear_url_caches()` (test_products_api.py:67-70) is irrelevant
  here. Reloading only schema modules (not `apps.products.models`) keeps Django model classes stable,
  matching the reference's documented intent.
- **No assertion weakened.** The fixture rewrite is the only behavioral change this pass; the three
  consuming tests' bodies/assertions are unchanged from the prior accepted Slice-4 re-pins (the
  `is_private=False` post-cascade ORM expectations were accepted in pass 1 / final-verification).
- **Does NOT touch `permissions.py` or the products `schema.py` activation.** `git diff --stat`
  shows `permissions.py` / `schema.py` / `__init__.py` / `test_products_api.py` carry their prior
  accepted deltas only; the only NEW logic this pass is the `test_schema.py` fixture.
- **Not a `@pytest.mark.order` band-aid.** No ordering marker anywhere; the fix is order-independent
  by construction (it reconstructs the registry+schema fresh per test).
- **Introduces no new pollution for later tests.** The fixture clears the registry and reloads fresh
  per test — the same self-contained discipline the live products autouse fixture relies on.
  Verified empirically (see reproductions): running `test_schema.py` FIRST then the live suites that
  depend on their own autouse reload stays green (133 passed).

### Reproduction (re-run, ≥2 orderings, all `--no-cov`, never `--cov*`, `-p no:randomly`)

| # | Command (preceding polluter → in-process target) | Result |
|---|---|---|
| 1 | `test_library_api.py` → `test_schema.py::test_project_schema_traverses_products_relations` (exact gate cmd) | **105 passed** |
| 2 | `test_glossary_api.py` → full `test_schema.py` | **8 passed** |
| 3 | `test_kanban_api.py` + `test_scalars_api.py` → `…::test_project_schema_traverses_products_relations` | **56 passed** |
| 4 | in-isolation: `test_schema.py` (all 3) | **3 passed** |
| 5 | downstream-pollution check: `test_schema.py` → `test_library_api.py` + `test_products_api.py` | **133 passed** |

Reproduction 1 matches Worker 2's reported `105 passed` (was `1 failed, 104 passed` pre-fix per the
gate diagnosis). Three distinct polluting-suite orderings (library / glossary / kanban+scalars — all
from the gate's bisected polluter list) now PASS, confirming the fix is general, not specific to one
preceding suite. Reproduction 5 confirms no new downstream pollution.

### Scope

Confirmed: only `examples/fakeshop/apps/products/tests/test_schema.py` changed for this fix; no
`django_strawberry_framework/` source change attributable to this pass. `uv run ruff check` on the
file → `All checks passed!`; `ruff format --check` → `1 file already formatted` (the emitted
`COM812` line is the repo's standing config notice, not a defect).

### High

None.

### Medium

None.

### Low

None.

### DRY findings

- **Reload-helper consolidation (DEFERRED — concur with Worker 2's Notes-for-Worker-1).** Both the
  live products suite (`test_products_api.py::_reload_products_project_schema`) and this in-process
  suite (`test_schema.py::project_schema`) now carry the same three-step discipline
  (clear registry → reload `apps.products.schema` → reload `config.schema`). This is a genuine live
  duplication of the products-reload-first invariant. However: (a) hoisting a shared helper (e.g.
  into an `examples/fakeshop/` `conftest.py` or a test-utility module) touches both suites + a new
  shared surface — exactly the kind of multi-file consolidation that should not ride a one-failure
  gate fix; (b) the two call sites differ (the live helper additionally reloads `config.urls` +
  `clear_url_caches()`, the in-process fixture does not), so the shared shape would need a parameter
  or the URL step factored out — non-trivial. **Verdict: deferred follow-up, not blocking.** The
  minimal in-fixture fix is the correct call for a gate fix. Recorded for a later DRY-consolidation
  pass (Worker 2 already flagged it to Worker 1).

### Public-surface check

N/A — test-only change. `git diff -- django_strawberry_framework/__init__.py` shows only the prior
accepted Slice-1 cascade-export pair; this pass adds no package export. Pass.

### CHANGELOG / Documentation sanity

N/A; this pass modified no `CHANGELOG.md`, `docs/`, `KANBAN.md`, or release files.

### What looks solid

- The fix is the smallest correct root-cause repair: it reuses the already-proven, already-in-tree
  reload discipline verbatim rather than inventing a new mechanism, and the one divergence (no
  `config.urls` reload) is correct for an in-process executor.
- The fix is order-independent and self-contained — confirmed across 3 polluter orderings + an
  in-isolation run + a downstream-pollution run (5 orderings total, all green), so it is general, not
  a tune to one collection order, and leaves no residue for later tests.
- The diagnosis in `bld-final.md` and Worker 2's pass-2 root-cause writeup match the observed
  behavior exactly (`importlib.import_module` returns the stale cached module; reloading
  `apps.products.schema` before `config.schema` re-registers the cascade hooks).

### Static helper

N/A — test-only change (no new `.py` file, no `django_strawberry_framework/optimizer|types/` touch,
no source logic). Skip recorded per worker-3.md "Static helper use".

### Temp test verification

No temp tests created this pass — the reproduction is itself the behavioral proof (a focused,
no-`--cov` ordering run that fails pre-fix and passes post-fix), and the behavior is permanently
pinned by `test_project_schema_traverses_products_relations` + the `project_schema` fixture in the
permanent suite. No temp test left as the only proof of shipped behavior.

### Notes for Worker 1

- **Re-run the final gate.** The Slice-4 gate fix is confirmed root-cause and order-independent
  across 5 orderings; the full `uv run pytest --no-cov` sweep (`bld-final.md` command 1) should now
  pass (the single deterministic isolation failure is resolved). Re-run all six gate commands.
- **Deferred DRY follow-up carried:** the shared products-reload-helper consolidation (live +
  in-process suites both own the clear→reload-products→reload-config invariant). Not actioned in this
  gate fix; weigh during a later cleanup pass — the two call sites differ by the `config.urls` reload
  step, so factoring needs care.

### Review outcome

`review-accepted`. The `project_schema` fixture fix is a correct, root-cause, order-independent
repair that mirrors the proven `_reload_products_project_schema` discipline (reload
`apps.products.schema` before `config.schema`), weakens no assertion, touches neither `permissions.py`
nor the products `schema.py` activation, is not a `@pytest.mark.order` band-aid, and introduces no new
pollution. Reproduced green across 3 distinct polluting-suite orderings + in-isolation + a
downstream-pollution run (105 / 8 / 56 / 3 / 133 passed). Scope confined to `test_schema.py`; no
package source change. Zero High / zero Medium / zero Low findings. One DRY consolidation idea
recorded as a deferred follow-up (concurring with Worker 2's flag to Worker 1).

---

## Final verification (Worker 1, gate-fix)

The Slice-4 gate-fix (the `project_schema` fixture reload-order repair, Worker-2 pass 2 / Worker-3
pass-2 review-accepted) is **verified by a green full sweep**. On the final test-run gate RE-RUN
(`docs/builder/bld-final.md`), `uv run pytest --no-cov` returned **`1948 passed, 4 skipped in
90.10s`** — the previously-failing
`examples/fakeshop/apps/products/tests/test_schema.py::test_project_schema_traverses_products_relations`
now PASSES both inside the full sweep (count moved from the prior `1 failed, 1947 passed` to
`1948 passed`, same total node count, zero new regressions) and in isolation (targeted node run →
`1 passed`), confirming the isolation fix holds within the real fixed collection order that exposed
the defect — not just in the focused reproductions. The other five gate commands also pass
(`manage.py check`, `makemigrations --check --dry-run`, `ruff format --check` `267 files already
formatted`, `ruff check` `All checks passed!`, `git diff --check` clean). With all six gate commands
green, this Slice-4 artifact's top-level `Status:` is restored to `final-accepted`. The deferred
shared products-reload-helper DRY consolidation (Worker-2/Worker-3 flag) is carried forward as a
maintainer follow-up; it is not a blocker.
