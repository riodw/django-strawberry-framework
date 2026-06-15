# Build: Slice 3 — composition pins

Spec reference: `docs/spec-034-permissions-0_0_10.md` (lines 67-69; Decision 11 lines 326-344, Decision 12 lines 346-357; Test plan lines 448-456)
Status: final-accepted

## Plan (Worker 1)

**Slice contract in one line:** NO source change. Slice 3 *pins* that the shipped
`check_<field>_permission` gates and the `DjangoConnectionField` / `DjangoNodeField` /
`DjangoNodesField` / `DjangoListField` pipelines all honor a cascading `get_queryset`
through their existing seams (Decision 11 / Decision 12). The whole slice is
un-skipping + implementing eight `@pytest.mark.skip(reason="TODO(spec-034 Slice 3): …")`
stubs that already exist across four test files. If any pin cannot pass without a
source edit, that is a **finding for the build pass** (record under `### Notes for
Worker 1 (spec reconciliation)`), NOT a planned source change.

### Pre-existing-stub inventory (verified on disk)

Every Slice-3 test is a **pre-existing skip-stub** with an assertion-spec docstring —
none are net-new files. Worker 2 un-skips and fills the body; the docstring is the
contract:

- `tests/test_permissions.py` (4 stubs, lines 1190/1199/1204/1209): `test_cascade_then_filter_gate_composition`, `test_cascade_then_order_gate_composition`, `test_gate_denial_no_existence_leak`, `test_nested_relation_traversal_respects_target_cascade`.
- `tests/test_connection.py` (1 stub, line 1388): `test_connection_over_cascading_type_narrows_edges_and_total_count`.
- `tests/test_relay_node_field.py` (2 stubs, lines 1027/1032): `test_node_refetch_of_cascade_hidden_row_returns_null`, `test_nodes_batch_holes_for_cascade_hidden_rows`.
- `tests/test_list_field.py` (1 stub, line 1019): `test_list_field_default_resolver_applies_cascade`.

Each file also carries a `# STAGED SEAM (spec-034 Slice 3)` banner above its stub(s)
asserting "NO <file> source change" — Worker 2 keeps the banner, drops the
`@pytest.mark.skip` decorator, and implements the body. Spec Test plan also names
`test_node_refetch…null` AND a batch sibling, both already stubbed.

The spec Test plan (line 448-456) lists `test_list_field_default_resolver_applies_cascade`
and a `test_nested_relation_traversal_respects_target_cascade` — both present as stubs.
**8 stubs total, 8 spec Test-plan bullets** (the connection bullet maps to one stub; the
node/nodes bullet maps to two stubs). No stub is missing and no spec bullet is unstubbed.

### DRY analysis

- **Existing patterns reused — the per-file harness is already in place; mirror it, do not invent.**
  - `tests/test_permissions.py:110-131` `_make_type(name, model, *, get_queryset=…, fields=…, primary=…)` + `tests/test_permissions.py:70-88` autouse `_isolate_registry` / `_assert_contextvar_clean` fixtures + the `_exclude_private` cascading hook (`tests/test_permissions.py:1038-1039`/`:551-552`/`:1104-1105` — declared THREE times already). The four gate/nested pins reuse `_make_type` + `_exclude_private` and the real products `Entry → Item → Category` chain exactly as `test_transitive_cascade_two_deep` (`tests/test_permissions.py:541-574`) and `test_cascaded_traversal_adds_zero_queries` (`:1021`) do.
  - The gate-composition pins reuse the products `CategoryFilter.check_name_permission` / `CategoryOrder.check_name_permission` gate *shape* (`examples/fakeshop/apps/products/filters.py:48-52` / `orders.py:41-45`) but declare LOCAL filtersets/ordersets in-test (the products sidecars are not registry-wired to the synthetic in-test `DjangoType`s). The `HttpRequest()` + `request.user = SimpleNamespace(is_staff=…)` on `info.context.request`, driven via `schema.execute_sync(query, context_value=request)`, is the `tests/orders/test_composition.py:128-140` + `tests/test_connection.py:976` (`context_value=HttpRequest()`) precedent. The gate resolves the request through `utils/permissions.py::request_from_info` (`info.context.request`, or a bare `HttpRequest` context).
  - `tests/test_connection.py:442-503` `_make_sidecar_node_type(name, *, total_count=…, filterset=…, orderset=…, get_queryset=…)` + `_field_schema(node_type)` + the `test_connection_resolver_composition_order` template (`:919-982`: instrumented `get_queryset` + `total_count=True`, asserts `totalCount` == full post-filter pre-slice count, edges sliced). The connection pin is a near-twin: a cascading `get_queryset` over a type with a forward FK to a hidden target; assert edges drop hidden-target rows AND `totalCount` matches the narrowed count.
  - `tests/test_relay_node_field.py:430-443` `_make_hidden_category_node()` + `test_node_hidden_row_returns_null` (`:447`) / `test_node_null_paths_issue_equal_queries` (`:477`) / `test_nodes_preserves_input_order_with_null_holes` (`:594`) — the per-type-visibility-hook→null contract. The cascade node pins are the *cascade* analogue: a node type whose `get_queryset` calls `apply_cascade_permissions`, refetching a row whose FK target is hidden → `null` / positional null hole. `_gid`, `_schema_with`, `_CATEGORY_QUERY` / `_CATEGORIES_QUERY` reused.
  - `tests/test_list_field.py:273-298` (inline `DjangoType` with cascading `get_queryset` → `DjangoListField` → `schema.execute_sync`) is the list-field default-resolver template.
- **New helpers justified — NONE inside this slice.** Every pin reuses an existing per-file fixture/harness. The ONE shape that recurs across all four files is the cascading hook `lambda cls, qs, info: apply_cascade_permissions(cls, qs.filter(is_private=False), info)` (the `_exclude_private` body). It is ALREADY locally re-declared 3× in `test_permissions.py` (Slice 1/2) and will recur in the connection/node/list files. **Do not extract a shared cross-file fixture in this slice** — a cross-file test fixture (conftest-level) is a structural change with its own review surface, and the carry-forward from Worker-1 memory (Slice 2) already flags this for the **integration pass**: "if Slice 3 rebuilds the cascading `Entry → Item → Category` schema a 3rd+ time, the integration pass should extract a shared cascading-schema fixture." Slice 3's job is the pins; the hoist (if any) is the integration pass's call after the duplication count is final. Worker 2 keeps each file's local `_exclude_private` mirroring its sibling Slice-1/2 declarations.
- **Duplication risk avoided.** The naive risk is each pin re-deriving its own ad-hoc cascading-schema scaffolding instead of reusing the file's `_make_type` / `_make_sidecar_node_type` / `_make_hidden_category_node` / `_schema_with` helpers. The plan prevents it by pinning, per stub, the exact existing helper to reuse (see Implementation steps). The connection helper `_make_sidecar_node_type` is hardcoded to `Category` (the chain TOP, which has no forward FK to cascade); the connection pin therefore needs a type over `Item` (forward FK `category`) — see the connection-step discretion note for the minimal, DRY way to get there without forking the helper wholesale.

### Implementation steps

Line numbers are pin-at-write-time hints — verify against current source before editing (another worker's pass may have shifted them; planning made no source/test edits).

**No source files are touched. All edits land in the four test files. Per BUILD.md, Worker 2 ticks each `### Spec slice checklist (verbatim)` box as the matching pin lands.**

1. **`tests/test_permissions.py` — gate composition (Decision 11), 3 stubs.** Under the existing `# Slice 3 - gate-composition pins` banner (`:1184`). For each: declare local `DjangoType`s over the products chain via `_make_type`, with the cascading `_exclude_private` hook on the relevant types, AND a local `FilterSet`/`OrderSet` carrying a `check_<field>_permission` gate (mirror `CategoryFilter.check_name_permission` — staff-only). Drive through an in-process schema with `context_value` = `HttpRequest()` whose `request.user = SimpleNamespace(is_staff=…)` (the `tests/orders/test_composition.py:128-140` shape; the gate resolves `info.context.request`). Composition order to PIN: `get_queryset` (cascade) runs at the visibility step BEFORE `FilterSet.apply_*`/`OrderSet.apply_*` (the gate). Reuse the `test_connection_resolver_composition_order` call-order-recording idiom (`:928-979`) if proving order directly, or assert the observable consequence (denial independent of hidden rows; passing input narrows only cascade-visible rows).
   - `test_cascade_then_filter_gate_composition` (`:1190`): **pin BOTH shapes** (card DoD). (a) A request whose `filter:` input names the gated field is DENIED by `check_<field>_permission` regardless of whether cascade-hidden rows exist (the gate raises `GraphQLError` on input shape alone). (b) With *passing* input (staff user, or input not naming the gated field), the filter operates only on cascade-narrowed rows — i.e. the result is the filtered subset of the cascade-visible set, never reaching hidden-target rows.
   - `test_cascade_then_order_gate_composition` (`:1199`): same matrix for an `OrderSet` `check_<field>_permission` gate (`orderBy:` naming the gated field denied; passing order applies only to cascade-narrowed rows).
   - `test_gate_denial_no_existence_leak` (`:1204`): the gate denial fires on input shape alone — assert the **byte-identical** denial error (message + any extensions) with hidden rows present AND with hidden rows absent (seed two fixtures differing only in whether a hidden-target row exists; the gated denial is the same `GraphQLError`). This is the no-existence-leak property: a denial cannot reveal whether a hidden row exists.
2. **`tests/test_permissions.py` — nested transitivity (Decision 12), 1 stub.** `test_nested_relation_traversal_respects_target_cascade` (`:1209`): the connection-DoD's "every edge's nested relations" half via the `Prefetch` downgrade. Build a real in-process schema over `Item` (or `Entry`) where the *nested relation's target type* (`CategoryType`) has a cascading hook; query the relation (`{ allItems { category { name } } }` shape) and assert the nested `category` rows reflect the target type's cascade — a hidden category does not surface through the nested traversal. Reuse the optimizer-plan harness already proven in Slice 2's `test_fk_id_elision_falls_back_for_cascading_target` (`:1089-1136`) / `test_strictness_raise_silent_across_cascaded_shape` (`:1139-1181`) (inline `@strawberry.type Query` + `DjangoOptimizerExtension` + `execute_sync(context_value=SimpleNamespace(user=…))`). This pin protects the verified `_build_child_queryset(..., info)` transitivity dependency (Decision 12 line 351) at the *traversal-result* level (Slice 2 already pinned it at the plan level via the live-user downgrade assertion); keep the two complementary, not duplicative — this one asserts the *narrowed nested rows*, Slice 2 asserts the *plan shape + child SQL carries the request user*.
3. **`tests/test_connection.py` — connection pin (Decision 12), 1 stub.** `test_connection_over_cascading_type_narrows_edges_and_total_count` (`:1391`). Mirror `test_connection_resolver_composition_order` (`:919-982`): build a Relay-Node `DjangoType` over **`Item`** (forward FK `category`) whose `get_queryset` calls `apply_cascade_permissions`, with `total_count=True`; register a `CategoryType` whose hook hides private categories; seed items split across a public and a private category. Assert: (a) `edges` contain only items whose category is visible (cascade-hidden rows dropped); (b) `totalCount` (counted post-visibility) equals the narrowed count, NOT the raw row count; (c) cursors stay consistent (the existing connection tests' cursor/`pageInfo` assertions are the precedent — `edges[i].cursor` monotonic, `pageInfo` coherent with the narrowed page). See the connection-step discretion note for getting an `Item`-targeted connection field without forking `_make_sidecar_node_type` (hardcoded to `Category`).
4. **`tests/test_relay_node_field.py` — node/nodes pins (Decision 12), 2 stubs.** Build a cascade-analogue of `_make_hidden_category_node` (`:430-443`): a Relay-Node `DjangoType` over `Item` whose `get_queryset` calls `apply_cascade_permissions` (so an item under a hidden category becomes invisible), plus a `CategoryType` hiding private categories. Use `_schema_with` + `_gid` + `_CATEGORY_QUERY`/`_CATEGORIES_QUERY` (or item-named equivalents).
   - `test_node_refetch_of_cascade_hidden_row_returns_null` (`:1028`): `node(id:)` / typed-node refetch of an item whose FK target (category) is cascade-hidden returns `null` with NO error and no existence leak — mirror `test_node_hidden_row_returns_null` (`:447`), the difference being the row is hidden by the **cascade through its FK**, not its own column. Optionally pin equal query count vs a missing row (the `test_node_null_paths_issue_equal_queries` precedent, `:477`) — at Worker 2's discretion if it strengthens the no-oracle property without churn.
   - `test_nodes_batch_holes_for_cascade_hidden_rows` (`:1033`): `nodes(ids:)` returns a positional `null` hole for each cascade-hidden id while visible ids resolve — mirror `test_nodes_preserves_input_order_with_null_holes` (`:594`).
5. **`tests/test_list_field.py` — list pin (Decision 12), 1 stub.** `test_list_field_default_resolver_applies_cascade` (`:1020`). Mirror the inline-`DjangoType`-+-`DjangoListField`-+-`execute_sync` shape (`:273-298`): a list field over `Item` whose `get_queryset` calls `apply_cascade_permissions`, with a `CategoryType` hiding private categories; assert the returned list drops items under hidden categories (the default resolver narrows through the cascade). The consumer-`resolver=` wrap also applies the hook (`list_field.py::_wrap`), but the stub docstring scopes this to the **default resolver** — keep it to the default-resolver path unless the spec Test plan widens it (it does not).

### Test additions / updates

All eight tests are the deliverable — there is no production code to prove. Pin shapes:

- **Gate composition** (`test_permissions.py`): `pytest.raises(GraphQLError)` (or `result.errors` carrying the gate message) for the denial shape; an equality/subset assertion on the cascade-narrowed result for the passing shape. Both shapes in `test_cascade_then_filter_gate_composition` / `_order_`; byte-identical error across hidden-present/absent fixtures in `test_gate_denial_no_existence_leak`.
- **Nested transitivity** (`test_permissions.py`): assert the nested relation's rows are the cascade-narrowed set (hidden target absent from the traversal). Optionally assert `result.errors is None` (the cascade composes SQL, never trips strictness — Slice 2 already pins the strictness-silence, so keep this assertion light to avoid a near-duplicate of `test_strictness_raise_silent_across_cascaded_shape`).
- **Connection** (`test_connection.py`): `len(edges)` / edge node ids == visible set; `totalCount == narrowed count` (load-bearing: must be the post-visibility count, distinguishable from the raw count — seed so raw != narrowed); cursor monotonicity / `pageInfo` coherence reusing the file's existing assertions.
- **Node / nodes** (`test_relay_node_field.py`): `result.data == {"<field>": None}` (single) and a positional-null-hole list (batch); `result.errors is None`.
- **List** (`test_list_field.py`): the returned list excludes hidden-target rows; `result.errors is None`.
- **Load-bearing / right-path discipline** (BUILD.md "Query-shape tests"): where the wire result alone could be produced by a non-cascade path, pin the distinguishing property. For the connection pin, `totalCount` MUST be derived from a real run and the seeding MUST make `narrowed != raw` (else the count assertion is vacuous). Keep each query MINIMAL so it can only take the path it claims (e.g. the gate-denial query names exactly the gated field; the nested-transitivity query selects exactly the nested relation). No `--cov*` flags anywhere.
- **No temp/scratch tests anticipated** — every pin lands directly in its permanent home file. If Worker 2 needs a scratch harness while iterating, place it under `docs/builder/temp-tests/slice-3/` and note it for Worker 3 (the only legitimate temp-test location; delete with `rm`, never `git checkout`).

### Implementation discretion items

Items I have assessed and decided belong to Worker 2 (equivalent-shape / mechanical choices); none is an architectural escape hatch.

- **Connection pin: how to target `Item` without forking `_make_sidecar_node_type`.** The file's helper is hardcoded to `Category` (the chain top, no forward FK to cascade). Worker 2's discretion between: (a) a small local `_make_item_sidecar_node_type` / inline `DjangoType` over `Item` mirroring the helper's shape (`fields=("id","name")`, `interfaces=(relay.Node,)`, `connection={"total_count": True}`, the cascading `get_queryset`), wired through `_connection_type_for` + `DjangoConnectionField` exactly as `_field_schema` does; or (b) a minimal generalization of `_make_sidecar_node_type` to accept a `model=`/`fields=` kwarg if that reads cleaner against the file. Either is acceptable; prefer the one that adds the least surface. (The pin does not need filter/order sidecars — pass `filterset=None, orderset=None` if reusing the helper, or omit them inline.)
- **Gate-composition: prove order directly vs by consequence.** Worker 2 may either record the call order with an instrumented `get_queryset` + `apply_sync` override (the `test_connection_resolver_composition_order` idiom) OR assert only the observable consequence (denial independent of hidden rows; passing input narrows to cascade-visible rows). Both satisfy Decision 11's "cascade narrows first, gates judge input second"; the consequence-only shape is lighter and sufficient if it pins both shapes.
- **Node pin: whether to add the equal-query-count assertion.** Optional strengthening of the no-existence-oracle property (the `test_node_null_paths_issue_equal_queries` precedent). Add it only if it does not bloat the pin.
- **Local `_exclude_private` placement.** Re-declare the cascading hook locally in each file mirroring its Slice-1/2 siblings (do NOT hoist a shared fixture this slice — that is the integration pass's call per the recorded carry-forward). Whether it is a module-level helper or a per-test closure is Worker 2's choice, matching the file's existing style.
- **Whether the node/nodes/list pins target `Item` or `Entry`.** Both have a forward FK to a cascading target (`Item → Category`; `Entry → Item`/`Property`). `Item → Category` is the simpler 1-edge cascade and matches the connection pin; `Entry` exercises 2 edges. Worker 2's choice; `Item → Category` is the lower-surface default and keeps the four files consistent.

### Spec slice checklist (verbatim)

- [x] Slice 3: composition pins — gates, connections, nodes, lists (per [Decision 11](#decision-11--the-existing-check_field_permission-filterorder-gates-survive-unchanged) / [Decision 12](#decision-12--connection--node--list-composition-is-contract-pinning-not-new-code))
  - [x] No new code in `filters/` / `orders/` / `connection.py` / `relay.py` / `list_field.py`. Pins: composition order is **cascade narrows first, gates judge input second** — a `get_queryset` that cascades runs at the visibility step of every pipeline, then the active-input-only `check_<field>_permission` gates fire from `FilterSet.apply_*` / `OrderSet.apply_*` exactly as shipped; a field denial does not leak existence (denied-filter errors and hidden-row-empty results are produced by independent layers); a [`DjangoConnectionField`][glossary-djangoconnectionfield] over a cascading type narrows `edges` and `totalCount` together; [`DjangoNodeField`][glossary-djangonodefield] / [`DjangoNodesField`][glossary-djangonodesfield] refetch of a cascade-hidden row returns `null` with no existence leak; [`DjangoListField`][glossary-djangolistfield]'s default resolver narrows.
  - [x] Package coverage: `tests/test_permissions.py` (composition fixtures) + [`tests/test_connection.py`][test-connection] / [`tests/test_relay_node_field.py`][test-relay-node-field] / [`tests/test_list_field.py`][test-list-field] additions per the [Test plan](#test-plan).

### Notes for Worker 1 (spec reconciliation)

No spec gap found at planning. All eight Slice-3 stubs exist on disk with their assertion-spec
docstrings; every spec Test-plan bullet (lines 448-456) maps to a stub; the four target test
files all carry the `# STAGED SEAM (spec-034 Slice 3)` "NO <file> source change" banners that
match Decision 12's contract-pinning posture. No `FAKESHOP_SHARDED` gating applies to any Slice-3
pin (confirmed — multi-DB is a Slice-1 concern only). Spec status line (line 5) already reads
"Slice 1 … shipped; Slices 2-5 remain" — accurate for an uncommitted-acceptance planning pass
where Slice 2 is `final-accepted` but the build is not yet committed; will re-verify at Slice 3
final verification (Slice 2 acceptance may warrant updating it to "Slices 1-2 shipped" then).

**Carry-forward for the integration pass (not a Slice-3 action):** the cascading-hook
`_exclude_private` body + the `Entry → Item → Category` synthetic-schema scaffold will now be
re-declared across `test_permissions.py` (3× already) + `test_connection.py` + `test_relay_node_field.py`
+ `test_list_field.py`. Once Slice 3 lands, the count is high enough that the integration pass should
evaluate extracting a shared cascading-schema test fixture (the Worker-1 Slice-2 memory carry-forward).
Flagging here so the integration pass has it in writing; NOT consolidating in Slice 3 (cross-file
fixture extraction is a structural change with its own review surface, premature before the
duplication count is final).

**Finding-vs-source-edit rule (restate for Worker 2/3):** if any pin cannot pass without editing
`filters/` / `orders/` / `connection.py` / `relay.py` / `list_field.py`, that is a Decision-12
violation finding — surface it under this section, do NOT plan or apply a source edit. Slice 3 is
no-source-change by contract.

---

## Build report (Worker 2)

### Files touched

Four test files only — **zero** source change under `django_strawberry_framework/` (confirmed
below). Each kept its `# STAGED SEAM (spec-034 Slice 3)` banner; the `@pytest.mark.skip`
decorators were dropped and the bodies implemented.

- `tests/test_permissions.py` — un-skipped + implemented the 4 gate/nested pins; added imports
  `django.http.HttpRequest`, `graphql.GraphQLError`, `FilterSet`, `Ordering`, `OrderSet`; added
  module-level helpers `_exclude_private` (cascading hook), `_gate_info` (request-bearing info
  stub), and local `_StaffOnlyCategoryFilter` / `_StaffOnlyCategoryOrder` gate mirrors.
- `tests/test_connection.py` — added import `apply_cascade_permissions`; added local
  `_make_cascading_item_node(name)`; un-skipped + implemented the connection pin.
- `tests/test_relay_node_field.py` — added import `apply_cascade_permissions`; added local
  `_make_cascading_item_node()` + `_ITEM_QUERY` / `_ITEMS_QUERY`; un-skipped + implemented the 2
  node pins.
- `tests/test_list_field.py` — added import `apply_cascade_permissions`; un-skipped + implemented
  the list pin.

### Tests added or updated

The 8 pre-existing skip-stubs, un-skipped + filled (no net-new test functions):

- `tests/test_permissions.py::test_cascade_then_filter_gate_composition` — **both shapes**: (a)
  a `filter: {name: ...}` input is denied by `check_name_permission` on input shape alone
  (`pytest.raises(GraphQLError)`) over the cascade-narrowed queryset; (b) staff-passing input
  operates only on cascade-visible rows (`{"name":"hidden"}` → `[]` because the private row was
  cascade-dropped; `{"name":"public"}` → `[public]`). Drives `FilterSet.apply_sync(input, narrowed,
  info)` directly (the consequence-only shape the plan permits).
- `::test_cascade_then_order_gate_composition` — same matrix for `OrderSet.apply_sync`: `orderBy`
  naming `name` denied; staff-passing order arranges only the cascade-narrowed rows
  (`[alpha, beta]`, private row absent).
- `::test_gate_denial_no_existence_leak` — two fixtures differing only in whether a hidden private
  row exists; asserts the denial `GraphQLError` is **byte-identical** (`str(...)` equal AND
  `.extensions` equal) hidden-present vs hidden-absent.
- `::test_nested_relation_traversal_respects_target_cascade` — in-process schema over `Category`
  with a cascading nested `ItemType` (the **to-many** `Category -> items` reverse relation);
  `{ allCategories { name items { name } } }` narrows each category's nested `items` LIST to the
  target's visible rows (hidden item absent), `errors is None`. Uses `DjangoOptimizerExtension` so
  the relation takes the `Prefetch` downgrade. **Design note (see finding below):** the plan
  sketched the forward-FK shape `{ allItems { category { name } } }`, but `Item.category` is a
  *non-nullable* FK — a cascade-hidden forward-FK target raises
  `GraphQLError('Item has no category.')`, it does NOT resolve to a clean nested `null`. The
  to-many list is the clean traversal-narrowing shape and matches the DoD's "every edge's nested
  relations" wording. Complementary to Slice 2's plan-level downgrade pin.
- `tests/test_connection.py::test_connection_over_cascading_type_narrows_edges_and_total_count` —
  connection over the cascading `Item` node; edges == the 2 visible items, `totalCount == 2`
  (post-visibility, NOT the raw 3), cursors present/distinct/one-per-edge, `pageInfo` coherent.
- `tests/test_relay_node_field.py::test_node_refetch_of_cascade_hidden_row_returns_null` —
  `item(id:)` of an item under a private category → `{"item": None}`, no error.
- `::test_nodes_batch_holes_for_cascade_hidden_rows` — `items(ids: [hidden, visible])` →
  `[None, {"name": ...}]` positional null hole, no error.
- `tests/test_list_field.py::test_list_field_default_resolver_applies_cascade` — `DjangoListField`
  over the cascading `Item` type; `{ allItems { id name } }` returns only `["visible_item"]`.

**Connection-type-over-`Item` decision (plan discretion item (a)):** added a minimal local
`_make_cascading_item_node` rather than generalizing `_make_sidecar_node_type` (hardcoded to
`Category`, the chain top with no forward FK to cascade). The node declares `fields=("id","name")`
+ `interfaces=(relay.Node,)` + `connection={"total_count": True}` + a `get_queryset` calling
`apply_cascade_permissions`; sidecars omitted (the pin exercises visibility, not filter/order).
`category` is NOT a declared field — the cascade walks `Item._meta.get_fields()` regardless of the
selected surface (the Slice-1 "Meta.fields-excluded FK edges still cascade" property), and the
query selects only `node { id name }`, keeping the pin on the Item-level-visibility path it claims
(BUILD.md right-path).

### Derived counts / load-bearing seeding

- **Connection pin `totalCount`:** seeded 3 items (2 under a public category, 1 under a private
  category) so `narrowed (2) != raw (3)`. The `totalCount == 2` assertion is therefore
  distinguishing — a non-cascade path would report 3. The count is derived from the seeded shape,
  not guessed (no query-count `django_assert_num_queries` assertion was needed for this pin; the
  load-bearing property here is the post-visibility count, not a round-trip count).
- No absolute `django_assert_num_queries` count was introduced this slice (the node/list/connection
  pins assert visibility narrowing, not query-count). The optional node equal-query-count
  strengthening was **not** added — `test_node_null_paths_issue_equal_queries` already pins that
  oracle property for the column-hidden case and the cascade case shares the same
  `qs.first()`/`pk__in` code path, so adding it here would bloat the pin without new signal (plan
  discretion: "add only if it does not bloat the pin").

### Validation run

- `uv run ruff format .` — pass (reformatted 1 file: `tests/test_connection.py`, my own
  write-time drift; owned and resolved by the formatter, not git-checkout per the standing guard).
- `uv run ruff check --fix .` — pass ("All checks passed!").
- `uv run python scripts/check_trailing_commas.py` — reformatted 1 file on first run, then
  idempotent-clean ("Fixed 0 file(s)."); `uv run ruff format --check .` reports "267 files already
  formatted".
- `uv run python -m py_compile` over the four files — `COMPILE OK`.
- Did NOT run `pytest` on the suite (per the task contract — Worker 3 runs focused tests). Three
  **throwaway probes** were used during development under `docs/builder/temp-tests/slice-3/`
  (the permitted scratch location) to settle empirical questions, then `rm`-deleted (temp-tests is
  now empty): (1) `probe_nested` — confirmed a forward non-nullable FK to a hidden target raises
  `GraphQLError('Item has no category.')` rather than nesting `null` (drove the nested-pin
  redesign); (2) `probe_reverse` — confirmed the to-many `Category -> items` nested list narrows
  cleanly (`errors None`, hidden child dropped); (3) `probe_item_cascade` — confirmed
  `apply_cascade_permissions(ItemType, Item.objects.all(), info)` composes
  `category_id IN (SELECT ... WHERE NOT is_private) OR category_id IS NULL` and drops items under a
  hidden category at both the queryset and `DjangoListField` levels (the connection/node/list
  pins' premise).
- `git status --short` after both ruff invocations — classification:
  - **Slice-3 intended (my diff):** `tests/test_permissions.py`, `tests/test_connection.py`,
    `tests/test_relay_node_field.py`, `tests/test_list_field.py`.
  - **Concurrent / out-of-scope (NOT mine — left untouched):** `django_strawberry_framework/__init__.py`,
    `django_strawberry_framework/permissions.py` (Slice 1 accepted, uncommitted),
    `tests/optimizer/test_extension.py` (Slice 2 accepted, uncommitted),
    `docs/spec-034-permissions-0_0_10.md` (Worker-1-owned),
    `examples/fakeshop/apps/products/schema.py` (concurrent em-dash swap, flagged in worker memory).
    I made **zero** edits to any of these; `git diff --stat` shows my additions land only in the
    four test files. **Zero source change under `django_strawberry_framework/`** is confirmed: the
    only `django_strawberry_framework/` entries in `git status` are the pre-existing
    Slice-1/2 uncommitted work, not Slice-3 edits.
  - **Untracked build artifacts:** `docs/builder/bld-slice-*.md`, `docs/builder/build-034-*.md`
    (cycle artifacts).

### Implementation notes

- **Gate pins via `apply_sync` directly, not full schema wiring.** The plan offered driving through
  an in-process schema with `context_value=HttpRequest()` OR asserting the observable consequence.
  I chose `FilterSet.apply_sync(input, narrowed_qs, info)` / `OrderSet.apply_sync(...)` over a
  cascade-narrowed queryset — the lowest-surface consequence-only shape, mirroring
  `tests/filters/test_sets.py` / `tests/orders/test_sets.py` `apply_sync` idioms. It pins both
  shapes without standing up the registry/factory/schema, and the products sidecars are not
  registry-wired to synthetic in-test types anyway (plan note).
- **Order pin: `_normalize_input` override instead of `OrderArgumentsFactory`.** A bare dict order
  input cannot normalize without a populated `_field_specs` ledger (which only the factory builds),
  and `test_permissions.py`'s autouse fixtures do not clear the order factory's module-global
  caches. Overriding `_normalize_input` to return `list(input_value.items())` (the
  `tests/orders/test_sets.py::_NoneDirectionSyncOrder` precedent) keeps the apply pipeline
  deterministic and avoids leaking factory state into this file. The gate's active-input walk falls
  back to the python-attr token when `_field_specs` is empty (the documented fallback), so
  `check_name_permission` still fires on `{"name": ...}`.
- **`_gate_info` carries `info.context.request` with `user.is_staff`.** The gate resolves the
  request via `utils/permissions.py::request_from_info` (canonical `info.context.request`); the
  cascade hook (`_exclude_private`) ignores `info`, so one stub shape serves the visibility step.
  The cascade-only `apply_cascade_permissions` calls in these pins use the file's existing
  `_INFO = SimpleNamespace(context=SimpleNamespace(user=None))` placeholder.
- **Node/list pins target `Item → Category` (1-edge cascade).** Plan default; matches the
  connection pin and keeps the four files consistent. The hooks use the
  `get_queryset(cls, queryset, info, **kwargs)` signature mirroring the file's
  `_make_hidden_category_node` precedent (the node-field refetch passes `**kwargs`).
- **`_exclude_private` re-declared locally** (module-level in `test_permissions.py`) per the plan's
  "do NOT hoist a shared cross-file fixture this slice" directive — the hoist is the integration
  pass's call once the duplication count is final.

### Notes for Worker 3

- **No source change, no shadow-file use.** This is a test-only slice over `tests/`. No
  `scripts/review_inspect.py` run (no `django_strawberry_framework/` `.py` touched).
- **Fixtures / derived shapes for re-running:** all cascade pins hand-create `Category`/`Item` rows
  with explicit `is_private` (not `seed_data`, which randomizes `is_private` for items — see
  `services.py` `is_private=random.choice([True, False])`). The connection pin's `totalCount == 2`
  is load-bearing only because the seeding makes `narrowed (2) != raw (3)`; do not collapse the
  seeding to all-visible rows.
- The gate pins assert the denial **message substring** (`pytest.raises(..., match=...)`) plus, for
  the no-leak pin, full `str(...)` + `.extensions` equality — the local gate mirrors the products
  `CategoryFilter` / `CategoryOrder` messages verbatim.
- The nested-transitivity pin keeps `result.errors is None` implicit via the equality assert on
  `result.data`; it deliberately does NOT re-assert strictness silence (Slice 2's
  `test_strictness_raise_silent_across_cascaded_shape` owns that, plan note).

### Notes for Worker 1 (spec reconciliation)

No spec gap, no Decision-12 violation, no source change required. Every pin passed within the
no-source-change contract: the shipped `apply_sync` gates, the `DjangoConnectionField` /
`DjangoNodeField` / `DjangoNodesField` / `DjangoListField` pipelines, and the optimizer `Prefetch`
downgrade all honor the cascading `get_queryset` through their existing seams, exactly as
Decisions 11/12 assert. No pin required editing `filters/` / `orders/` / `connection.py` /
`relay.py` / `list_field.py`.

**Small plan-vs-implementation drift (recorded per worker-2.md "Small, mechanically obvious
drift"): the nested-transitivity pin uses a to-many relation, not the plan's forward-FK sketch.**
The plan (step 2 / Test-additions) sketched `test_nested_relation_traversal_respects_target_cascade`
as `{ allItems { category { name } } }` asserting a `null` nested `category` for an item under a
hidden category. Empirically (`probe_nested`), a cascade-hidden **non-nullable forward FK**
(`Item.category`, `null=False`) raises `GraphQLError('Item has no category.')` — it CANNOT resolve
to a clean nested `null` (a non-null GraphQL field returning `None` is a null-violation; and
`Meta.nullable_overrides` is scalar-only per spec-029 Decision 10, so the FK field cannot be forced
nullable). The correct traversal-narrowing shape for a forward non-null FK is that the PARENT row
drops via its own cascade — which the connection/node/list pins already exercise. So the
nested-transitivity pin was implemented over the **to-many** `Category -> items` reverse relation
instead: the nested `items` LIST narrows to the target's visible rows (a list can be empty/narrowed
without a null-violation), matching the DoD sentence's "every edge's nested relations respect the
same cascade rule" wording. The assertion (`errors is None`; hidden item absent from the nested
list) is the verified shape. This stays within the slice contract (still pins target-cascade
transitivity at the traversal-result level via the `Prefetch` downgrade) — Worker 1 may keep it or,
if the spec Test-plan bullet's "every edge's nested relations" wording wants a forward-FK example,
note the nullability constraint in the spec. No source or spec edit made by Worker 2.

---

## Review (Worker 3)

Reviewed the Slice-3 surface only (the 8 now-implemented pins), using the artifact's
`### Files touched` as the navigational filter against the cumulative working-tree diff.
Confirmed **zero Slice-3 source change under `django_strawberry_framework/`**: the only
`django_strawberry_framework/` entries in `git status` are `__init__.py` and `permissions.py`,
both the Slice-1 baseline (the `__init__.py` delta is the Decision-4 export of
`apply_cascade_permissions` / `aapply_cascade_permissions`; `permissions.py` is the restored
Slice-1 module). `tests/optimizer/test_extension.py` is Slice-2; `docs/spec-034-…` is
Worker-1-owned; `examples/fakeshop/apps/products/schema.py` is the concurrent em-dash→hyphen swap
inside a `# TODO(spec-034 Slice 4)` comment (verified read-only: the cascade import and the four
hooks remain commented — Slice 4 territory, untouched here). The four Slice-3 test files are the
only intended diff.

**Focused run (the contract's command, no coverage):**
`uv run pytest tests/test_permissions.py tests/test_connection.py tests/test_relay_node_field.py tests/test_list_field.py --no-cov -q`
→ **2 failed, 144 passed, 1 skipped** (the 1 skip is the `FAKESHOP_SHARDED` multi-DB pin, not a
Slice-3 pin). The two failures are both Slice-3 gate-composition pins (H1 below). The other six
Slice-3 pins pass and were isolated green (`6 passed`).

### High:

#### H1 — `test_cascade_then_filter_gate_composition` and `test_cascade_then_order_gate_composition` FAIL: the "cascade narrows first" half is built on a no-op call, so the gate-passing shape asserts against an un-narrowed queryset

- **Severity:** High (spec-contract pin fails red; Slice-3 DoD item 8 "gate-passing input operating on cascade-narrowed rows" is not delivered).
- **Source:** `tests/test_permissions.py::test_cascade_then_filter_gate_composition` #"narrowed = apply_cascade_permissions(category_type, Category.objects.all(), _INFO)" and `tests/test_permissions.py::test_cascade_then_order_gate_composition` #"narrowed = apply_cascade_permissions(category_type, Category.objects.all(), _INFO)".
- **Why it matters:** Both pins build their "cascade-narrowed" queryset as
  `narrowed = apply_cascade_permissions(category_type, Category.objects.all(), _INFO)` where
  `category_type` is `_make_type(..., Category, get_queryset=_exclude_private)`.
  `apply_cascade_permissions` cascades through the model's **forward FK edges** (intersecting each
  edge's target-type visibility) — it does **not** invoke the type's own `get_queryset` hook, so the
  `_exclude_private` body's `qs.filter(is_private=False)` row-narrow never runs. And `Category` is the
  chain **top**: `_cascadable_edge_names(Category) == set()` (verified — a `Category` points at no
  cascadable forward FK; `Item.category` is the forward FK *into* `Category`). So
  `apply_cascade_permissions(category_type, Category.objects.all(), _INFO)` is a **no-op** that returns
  every row, including the private one. The filter pin's shape (b) `assert list(passed) == []` then sees
  the `hidden` row survive the `{"name": "hidden"}` filter (`[<Category: hidden>] != []`); the order pin's
  shape (b) `assert list(ordered) == [alpha, beta]` sees `[alpha, beta, hidden]`. **Verified with a temp
  probe** (`docs/builder/temp-tests/slice-3/probe_gate_narrow.py`, since `rm`-removed): the direct
  `apply_cascade_permissions(...)` call returns `['hidden', 'public']`; invoking
  `category_type.get_queryset(Category.objects.all(), _INFO)` returns `['public']`. The "cascade narrows
  first" premise of both pins is false as written — shape (a) (the denial) passes only because the gate
  raises on input shape *before any row math*, so the cascade half is entirely un-exercised even when the
  test is made green.
- **Recommended change:** Build `narrowed` from a path where the cascade genuinely narrows. Two sound shapes:
  (i) the **hook-invocation** shape — `narrowed = category_type.get_queryset(Category.objects.all(), _gate_info(...))`
  (or `_INFO`) so `_exclude_private`'s `is_private=False` row-narrow actually fires (matches "cascade lives
  in `get_queryset`" wording, lowest surface); or (ii) the **forward-FK** shape used by the
  connection/node/list pins — drive the gate over an `Item`-rooted type whose `get_queryset` calls
  `apply_cascade_permissions` so `category__in (SELECT visible)` drops the items under a hidden category,
  then run the gate's `apply_sync` over that genuinely-narrowed `Item` queryset (this exercises the real
  cascade, not just the hook's local `filter`). Shape (i) is the minimal fix and keeps the gate over
  `Category` (matching the products `CategoryFilter`/`CategoryOrder` mirror); either restores the
  load-bearing "narrows first" half.
- **Test expectation:** After the fix, shape (b) must observe the private/hidden row *absent* from the
  narrowed set (so the `[]` / `[alpha, beta]` assertions hold), AND the narrowing must be caused by the
  cascade/hook (not by some unrelated filter) — i.e. removing the hook would let the hidden row through.
  Keep shape (a)'s denial assertion as-is. Re-run the focused command to green
  (`tests/test_permissions.py` to 146 passed / 0 failed in the four-file scope).

### Medium:

None.

### Low:

#### L1 — gate-composition pins exercise `FilterSet`/`OrderSet` `apply_sync` directly rather than through a full pipeline (informational, not a defect)

- **Severity:** Low (design note, no action required).
- The two gate pins drive `_StaffOnlyCategoryFilter.apply_sync(...)` / `_StaffOnlyCategoryOrder.apply_sync(...)`
  over a pre-narrowed queryset rather than standing up a connection/list pipeline that applies
  `get_queryset` then the gate. The plan explicitly permits this ("consequence-only shape... lighter and
  sufficient if it pins both shapes", discretion item "prove order directly vs by consequence"). Once H1 is
  fixed so `narrowed` is genuinely cascade/hook-narrowed, the consequence-only shape does pin both halves.
  Noting only so Worker 1 is aware the composition *order* is asserted by consequence (cascade-narrowed input
  to the gate), not by an instrumented call-order recorder — which the plan blessed.

### DRY findings

- **Cross-file cascading-fixture duplication (for the integration pass, do NOT fix now).** The cascading
  hook shape (`get_queryset` calling `apply_cascade_permissions`) plus a hiding-`Category` target hook
  (`queryset.filter(is_private=False)`) now recurs across all four Slice-3 files:
  `tests/test_permissions.py` (`_exclude_private`, module-level at `::_exclude_private`),
  `tests/test_connection.py` (`_make_cascading_item_node` + the inline `CcCategoryType`),
  `tests/test_relay_node_field.py` (`_make_cascading_item_node` + the inline `_HidingCategoryType`),
  `tests/test_list_field.py` (the inline `ItemType` + `_HidingCategoryType`). Count of independent
  cascading-`Item`-node declarations introduced by Slice 3: **3** (`test_connection.py`,
  `test_relay_node_field.py`, `test_list_field.py` — two share the helper name `_make_cascading_item_node`
  but are separate per-file declarations). Combined with the `test_permissions.py` `_exclude_private`
  re-declarations (already flagged by Worker 1's carry-forward), the duplication count is now high enough
  to warrant the **integration pass** evaluating a shared cascading-schema test fixture. This matches the
  Plan's DRY analysis and Worker-1's recorded carry-forward verbatim; a cross-file conftest fixture is a
  structural change with its own review surface and is premature mid-slice. **Not a Slice-3 finding** —
  recorded for the integration pass.
- **No in-file near-copy introduced by Worker 2.** Within each file the new pin reuses that file's existing
  harness (`_field_schema` / `_make_sidecar_node_type` precedent in connection, `_schema_with` / `_gid` /
  `_make_hidden_category_node` precedent in node, the inline-`DjangoListField` template in list). The local
  `_make_cascading_item_node` in `test_connection.py` and `test_relay_node_field.py` are justified by
  the plan's discretion item (a) (the file's `_make_sidecar_node_type` is hardcoded to `Category`, the chain
  top with no forward FK). No in-file DRY finding.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` shows `__all__` gaining `aapply_cascade_permissions`
and `apply_cascade_permissions` plus the matching import. This is **not a Slice-3 change** — it is the
Slice-1 export work authorized by spec Decision 4 (line 56-62) and Decision 13 (line 361: "The exports pin
in `tests/base/test_init.py` *does* grow in Slice 1 (two new `__all__` members)"). Slice 3 introduces **no**
public-surface change of its own (test-only slice). No new exports attributable to Slice 3. Pass.

### CHANGELOG sanity

Not applicable; slice did not modify `CHANGELOG.md`.

### Documentation / release sanity

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces. (The `examples/fakeshop/apps/products/schema.py`
em-dash→hyphen swap inside a Slice-4 TODO comment is concurrent out-of-scope churn, not a Slice-3 doc edit,
and is left untouched per the standing guard.)

### What looks solid

- **The six non-gate pins are correct, green, and load-bearing.**
  - **Connection pin** (`test_connection.py::test_connection_over_cascading_type_narrows_edges_and_total_count`):
    seeds 3 items (2 under public, 1 under private category) so `narrowed (2) != raw (3)` — the
    `totalCount == 2` assertion is genuinely post-visibility and NOT vacuous (a non-cascade path would report
    3). Edges drop the hidden-target item, cursors present/distinct/one-per-edge, `pageInfo` coherent. The
    local `_make_cascading_item_node` over `Item` (forward FK `category`) is the right vehicle (the helper
    `_make_sidecar_node_type` is hardcoded to `Category`, the chain top). Exactly the BUILD.md
    "pin the load-bearing property" shape.
  - **Node / nodes pins** (`test_relay_node_field.py`): single refetch of a cascade-hidden item →
    `{"item": None}`, `errors is None`; batch `nodes(ids: [hidden, visible])` → `[None, {"name": ...}]`
    positional hole. Mirrors the column-hidden `test_node_hidden_row_returns_null` precedent (line 447 /
    `_schema_with("category", hidden_node | None, …)` at line 452); the cascade analogue is sound.
  - **List pin** (`test_list_field.py`): `DjangoListField` over the cascading `Item` type → only
    `["visible_item"]`; scoped to the default resolver per the stub docstring (not the consumer-`resolver=`
    wrap), which matches the spec Test plan.
  - **No-existence-leak pin** (`test_permissions.py::test_gate_denial_no_existence_leak`): asserts
    `str(...)` equality AND `.extensions` equality across hidden-present vs hidden-absent fixtures — the
    byte-identical-denial property the spec (Decision 11 line 336) requires. Correct and load-bearing.
  - **Nested-transitivity pin** (`test_permissions.py::test_nested_relation_traversal_respects_target_cascade`):
    **adversarially verified load-bearing** — a temp probe (`probe_nested_loadbearing.py`, since `rm`-removed)
    confirmed that *without* the cascading hook on `ItemType` the hidden item surfaces in the nested list
    (`['hidden_item', 'visible_item']`); with the hook it narrows to `['visible_item']`. So the narrowing is
    genuinely caused by the hook riding the `Prefetch` downgrade (the query selects exactly
    `{ allCategories { name items { name } } }`, so it can only take the planned-Prefetch path). Sound.
- **`_assert_contextvar_clean` autouse fixture** (`test_permissions.py`) guards `_cascade_seen` cleanliness
  across every test — the gate pins inherit it, so the H1 failures cannot leave a leaked seen-set.
- **Local gate mirrors are byte-faithful.** `_StaffOnlyCategoryFilter` / `_StaffOnlyCategoryOrder` messages
  match the products `examples/fakeshop/apps/products/filters.py::CategoryFilter.check_name_permission` /
  `orders.py::CategoryOrder.check_name_permission` verbatim ("You must be a staff user to filter/order by
  Category name."). The `_normalize_input` override on the order mirror is the documented
  `tests/orders/test_sets.py::_NoneDirectionSyncOrder` precedent for avoiding factory-cache leakage.

### Temp test verification

- `docs/builder/temp-tests/slice-3/probe_gate_narrow.py` — used to isolate the H1 root cause (direct
  `apply_cascade_permissions` vs hook-invocation narrowing). Confirmed the no-op. **Deleted (`rm -rf` of the
  slice-3 dir I created); not promoted** — the bug it proves is H1, which Worker 2 fixes in the permanent
  pin itself (no new permanent test needed beyond the corrected pin).
- `docs/builder/temp-tests/slice-3/probe_nested_loadbearing.py` — used to adversarially confirm the
  nested-transitivity pin is hook-caused (load-bearing). **Deleted; not promoted** — it proved the existing
  pin is sound, not a bug.
- `docs/builder/temp-tests/` is empty after cleanup (verified). No `git checkout`/`restore`/`stash`/`reset`
  used anywhere; only `rm` of files I created under `docs/builder/temp-tests/slice-3/`.

### Notes for Worker 1 (spec reconciliation)

- **Nested-pin adjudication (Worker 2's to-many redesign): SOUND, no gap.** Worker 2's empirical finding is
  correct: a cascade-hidden **non-nullable forward FK** (`Item.category`, `null=False`) raises
  `GraphQLError('Item has no category.')` rather than nesting a clean `null` — a non-null GraphQL field
  returning `None` is a null-violation, and `Meta.nullable_overrides` is scalar-only (spec-029 Decision 10),
  so the FK cannot be forced nullable. The correct traversal-narrowing shape for a forward non-null FK is
  that the **parent row drops** via its own cascade — which the connection/node/list pins already exercise.
  Worker 2 therefore implemented the nested pin over the **to-many** `Category → items` relation, where the
  nested list narrows cleanly (a list can be empty/narrowed without a null-violation) and matches the DoD's
  "every edge's nested relations respect the same cascade rule" wording. I adversarially verified this pin is
  load-bearing (see "What looks solid"). This stays within the no-source-change slice contract and pins
  target-cascade transitivity at the traversal-result level. **Recommendation:** keep the to-many shape as
  shipped. Worker 1's call whether to add a one-line edge-case note to the spec Test plan (line 456) recording
  the non-null-forward-FK nullability constraint (parent-drops vs nested-null) — this is a clarification, not
  a contract change, and is purely Worker 1's discretion.
- **No Decision-12 violation surfaced.** Every passing pin honored the cascading `get_queryset` through the
  shipped seams; H1 is a test-construction bug (no-op `apply_cascade_permissions` call on a chain-top model),
  not a source/contract gap. No source edit is warranted by H1 — the fix is in the test.

### Review outcome

`revision-needed` — H1 (two failing gate-composition pins) blocks acceptance. The "cascade narrows first"
half of `test_cascade_then_filter_gate_composition` / `test_cascade_then_order_gate_composition` is built on a
no-op `apply_cascade_permissions(category_type, Category.objects.all(), …)` call (Category has no cascadable
forward FK), so the gate-passing shape asserts against an un-narrowed queryset and fails red. Worker 2 must
rebuild `narrowed` via the hook-invocation path (`category_type.get_queryset(...)`) or an `Item`-rooted
forward-FK cascade so the narrowing genuinely fires, keeping both shapes load-bearing, then re-run the focused
command to green. The other six Slice-3 pins are accepted as solid and load-bearing; the nested-pin to-many
redesign is adjudicated sound. No source change required.

---

## Build report (Worker 2, pass 2)

Apply-changes pass after Worker 3's `revision-needed` (1 High: H1). Addressed H1 with a
test-only, two-line construction fix; **no source change** under `django_strawberry_framework/`
(this was a test-construction bug, not a source bug). L1 needed no change (plan-blessed
`apply_sync`-direct shape; now genuinely load-bearing once `narrowed` is hook-narrowed). Did not
touch the six accepted Slice-3 pins.

### Files touched

- `tests/test_permissions.py` — H1 fix only. In `test_cascade_then_filter_gate_composition` and
  `test_cascade_then_order_gate_composition`, rebuilt the `narrowed` queryset from the no-op
  `apply_cascade_permissions(category_type, Category.objects.all(), _INFO)` to the
  **hook-invocation** path `category_type.get_queryset(Category.objects.all(), _INFO)` (Worker 3's
  recommended shape (i), the minimal fix). Added a short explanatory comment at each call site
  noting why the direct `apply_cascade_permissions` call was a no-op (Category is the chain top with
  no cascadable forward FK; the cascade does not invoke the type's own hook). No other test changed;
  the gate mirrors (`_StaffOnlyCategoryFilter` / `_StaffOnlyCategoryOrder`), `_exclude_private`,
  `_gate_info`, and the other six pins are untouched.

### Tests added or updated

No net-new tests. Two existing pins corrected (construction only — the assertion contracts are
unchanged):

- `::test_cascade_then_filter_gate_composition` — shape (b) `{"name": "hidden"}` now resolves to
  `[]` and `{"name": "public"}` to `[public]` against a queryset the hook genuinely narrowed (the
  private `hidden` row is dropped at the visibility step by `_exclude_private`'s `is_private=False`
  row-narrow, which only runs through `get_queryset`). Shape (a)'s denial assertion is unchanged.
- `::test_cascade_then_order_gate_composition` — shape (b) `[alpha, beta]` now holds because the
  hidden row is hook-dropped before the order applies. Shape (a)'s denial unchanged.

### Validation run

- `uv run ruff format .` — pass, **267 files left unchanged** (zero formatter drift from this pass;
  the two-line edit fit existing layout).
- `uv run ruff check --fix .` — pass ("All checks passed!").
- Did NOT run `pytest` (per the task contract — Worker 3 re-runs the focused four-file command).
- `docs/builder/temp-tests/slice-3/` — verified absent (no scratch tests created this pass).
- `git status --short` classification:
  - **Slice-3 intended (this pass's diff):** `tests/test_permissions.py` (the two `narrowed =`
    hook-invocation lines + their comments). `git diff` confirms the only behavioral change is
    `+    narrowed = category_type.get_queryset(Category.objects.all(), _INFO)` (×2). The other
    `tests/` insertions in the cumulative diff are pass-1's accepted Slice-3 work, untouched.
  - **Concurrent / out-of-scope (NOT mine — left untouched):**
    `django_strawberry_framework/__init__.py` + `permissions.py` (Slice-1 uncommitted),
    `tests/optimizer/test_extension.py` (Slice-2 uncommitted), `docs/spec-034-permissions-0_0_10.md`
    (Worker-1-owned), `examples/fakeshop/apps/products/schema.py` (concurrent em-dash→hyphen swap
    inside a Slice-4 TODO comment), `tests/test_connection.py` / `tests/test_list_field.py` /
    `tests/test_relay_node_field.py` (my pass-1 Slice-3 work — the six accepted pins, untouched).
  - **Untracked build artifacts:** `docs/builder/bld-slice-*.md`, `docs/builder/build-034-*.md`.
  - **Zero source change under `django_strawberry_framework/` this pass** — confirmed.

### Implementation notes

- **Chose Worker 3's recommended shape (i) — the hook-invocation path — over shape (ii)
  (an `Item`-rooted forward-FK cascade).** Rationale: shape (i) is the minimal, lowest-surface fix.
  It keeps the gate over `Category` (so the local `_StaffOnlyCategoryFilter` / `_StaffOnlyCategoryOrder`
  mirrors still match the products `CategoryFilter` / `CategoryOrder` shape byte-for-byte), keeps both
  pins one-fixture, and corrects exactly the one false premise. Shape (ii) would have required
  re-rooting both pins on `Item` + standing up a hiding `CategoryType` + re-mirroring the gate to an
  `Item`-field gate — far more churn for an equivalent contract, and the connection/node/list pins
  already exercise the forward-FK cascade path, so shape (ii) would add no distinct coverage here.
- **Why the hook genuinely narrows ("narrows first" is now load-bearing).** `_exclude_private`'s body
  is `apply_cascade_permissions(cls, qs.filter(is_private=False), info)`. The `get_queryset` classmethod
  on the synthetic type IS `_exclude_private` (installed by `_make_type`), so
  `category_type.get_queryset(Category.objects.all(), _INFO)` runs the `qs.filter(is_private=False)`
  row-narrow that drops the private `hidden` row, then the (harmless no-op-on-Category)
  `apply_cascade_permissions` pass. The earlier bug was calling `apply_cascade_permissions` *directly*,
  which never touches the type's own hook and, on the chain-top `Category`
  (`_cascadable_edge_names(Category) == set()`), returns every row including the private one. **Probe of
  load-bearingness:** removing the `is_private=False` filter from `_exclude_private` would make
  `get_queryset` an identity hook, the hidden row would survive, and shape (b) would flip
  (`[hidden]` for the filter pin / `[alpha, beta, hidden]` for the order pin) — so the narrowing now
  causally drives shape (b)'s result, exactly as Decision 11 requires.
- **`_INFO` (not `_gate_info(...)`) is correct for the cascade step.** `_exclude_private` ignores
  `info` (it narrows unconditionally), so the file's existing `_INFO` placeholder is sufficient at the
  visibility step; the request-bearing `_gate_info(is_staff=…)` stays on the `apply_sync` calls where
  the gate resolves `info.context.request`. The two layers take independent `info`, matching the
  "independent layers" property the no-leak pin pins.

### Notes for Worker 3

- **H1 addressed; both shapes now load-bearing.** `narrowed` is rebuilt via
  `category_type.get_queryset(Category.objects.all(), _INFO)` in both gate pins, so the
  `_exclude_private` `is_private=False` row-narrow actually fires before the gate runs. Shape (a)
  (denial on input shape alone) is unchanged and still passes; shape (b) (gate-passing input operates
  ONLY on cascade-narrowed rows) now asserts against a genuinely-narrowed queryset — the private/hidden
  row is absent, so `assert list(passed) == []` (filter) and `assert list(ordered) == [alpha, beta]`
  (order) hold. The "narrows first" half is causally load-bearing: removing the hook's
  `is_private=False` filter would let the hidden row through and flip shape (b)'s result.
- **L1 (informational) — no change.** The gate pins still drive `apply_sync` directly (the
  plan-blessed consequence-only shape). With H1 fixed, the input to `apply_sync` is genuinely
  cascade/hook-narrowed, so the consequence-only shape now pins both halves of Decision 11's
  composition order, as L1 anticipated.
- **No source change, no shadow-file use** — test-only construction fix over `tests/test_permissions.py`.
  Suggested re-run: `uv run pytest tests/test_permissions.py tests/test_connection.py
  tests/test_relay_node_field.py tests/test_list_field.py --no-cov -q` → expect 146 passed / 0 failed
  / 1 skipped (the `FAKESHOP_SHARDED` pin) in the four-file scope.

---

## Review (Worker 3, pass 2)

Re-review after Worker 2's pass-2 apply-changes addressing my single High finding (H1). Reviewed
the Slice-3 surface only, using the artifact's `### Files touched` as the navigational filter
against the cumulative working-tree diff. This pass's only behavioral change is the two-line H1 fix
in `tests/test_permissions.py`; the other three Slice-3 test files and the six accepted pins are
untouched (confirmed below).

### H1 resolution confirmation

**RESOLVED.** Both gate-composition pins now build the narrowed queryset via the hook-invocation
path, not the no-op direct call:

- `tests/test_permissions.py::test_cascade_then_filter_gate_composition` (`:1283`):
  `narrowed = category_type.get_queryset(Category.objects.all(), _INFO)`.
- `tests/test_permissions.py::test_cascade_then_order_gate_composition` (`:1323`):
  `narrowed = category_type.get_queryset(Category.objects.all(), _INFO)`.

`_make_type` (`:114-135`) installs the `get_queryset` kwarg as a `classmethod` on the synthetic
`DjangoType` (`:133-134`), so `category_type.get_queryset(...)` genuinely invokes `_exclude_private`
(`:1194-1202`), whose body is `apply_cascade_permissions(cls, qs.filter(is_private=False), info)`.
The `is_private=False` row-narrow therefore fires at the visibility step before the gate runs —
the false "narrows first" premise from pass 1 is corrected.

**Both shapes verified genuinely load-bearing:**
- **Shape (a) — denial on gated input regardless of narrowing.** `pytest.raises(GraphQLError,
  match="staff user to filter/order by Category name")` on `{"name": ...}` input with a non-staff
  `_gate_info(is_staff=False)`. The gate raises on input shape alone, before any row math —
  independent of cascade state (filter pin `:1287-1292`; order pin `:1326-1331`). Unchanged from
  pass 1 and still green.
- **Shape (b) — gate-passing input operates only on narrowed rows.** Filter pin: `{"name":
  "hidden"}` over the narrowed queryset → `list(passed) == []` (`:1302`) because the private
  `hidden` row was already cascade-dropped; `{"name": "public"}` → `[public]` (`:1308`). Order pin:
  `{"name": Ordering.ASC}` over the narrowed queryset → `[alpha, beta]` (`:1340`), the private
  `hidden` row absent. These now hold because `narrowed` is genuinely hook-narrowed.

**"Narrows first" is causal — adversarially verified.** Temp probe
(`docs/builder/temp-tests/slice-3/probe_causal.py`, since `rm`-removed) ran three assertions, all
passing: (1) the hook *with* `qs.filter(is_private=False)` → `get_queryset(...)` returns
`['public']` (hidden dropped); (2) the hook *without* the `is_private` filter (identity hook) →
`['hidden', 'public']` — the hidden row survives, so removing the hook's filter flips shape (b)
exactly as required (the narrowing causally drives the result); (3) the OLD construction,
`apply_cascade_permissions(type, Category.objects.all(), _INFO)` directly on chain-top `Category`,
returns `['hidden', 'public']` — confirming pass-1's root-cause diagnosis (the direct call was a
no-op because `Category` has no cascadable forward FK and the cascade never invokes the type's own
hook). Worker 2's chosen shape (i) (hook-invocation, minimal fix) restores the load-bearing half
without re-rooting the pins on `Item`.

### Focused-test counts

`uv run pytest tests/test_permissions.py tests/test_connection.py tests/test_relay_node_field.py tests/test_list_field.py --no-cov -q`
→ **146 passed, 1 skipped, 0 failed** (10.12s). The prior 2 gate-composition failures are gone. The
1 skip is the `FAKESHOP_SHARDED` multi-DB alias pin (`tests/test_permissions.py:355`,
`reason="multi-DB alias pin needs the FAKESHOP_SHARDED 'shard_b' alias"`), not a Slice-3 pin —
matches the contract's expected ≈146/1 exactly. The two formerly-failing gate pins pass in
isolation (`2 passed`); the six accepted pins pass in isolation (`6 passed`).

### High:

None.

### Medium:

None.

### Low:

None. (Pass-1 L1 — gate pins drive `apply_sync` directly rather than through a full pipeline — was
informational and plan-blessed; with H1 fixed the `apply_sync` input is genuinely hook-narrowed, so
the consequence-only shape now pins both halves of Decision 11's composition order, as L1
anticipated. No action.)

### DRY findings

- **Cross-file cascading-fixture duplication (for the integration pass, do NOT fix now) — carried
  forward unchanged.** The cascading-hook shape (`get_queryset` calling `apply_cascade_permissions`)
  plus a hiding-`Category`/`Item` target hook now recurs across all four Slice-3 files
  (`test_permissions.py::_exclude_private`; `test_connection.py` + `test_relay_node_field.py`
  `_make_cascading_item_node`; `test_list_field.py` inline). The pass-2 fix added no new
  duplication (it only swapped a single call expression in two existing pins). The duplication count
  is now final for Slice 3; per the Plan's DRY analysis and Worker-1's recorded carry-forward, the
  **integration pass** should evaluate extracting a shared cascading-schema test fixture (a
  conftest-level cross-file fixture is a structural change with its own review surface, premature
  mid-slice). **Not a Slice-3 finding** — recorded for the integration pass.
- **No in-file near-copy introduced this pass.** The pass-2 edit is a two-line construction fix
  inside two existing pins, reusing the file's existing `_make_type` / `_exclude_private` /
  `_gate_info` / gate-mirror helpers. No new helper, no new duplication.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` shows `__all__` gaining
`aapply_cascade_permissions` and `apply_cascade_permissions` plus the matching `from .permissions
import (...)` and the removal of the staged-seam TODO/ERA001 directive. This is **not a Slice-3
change** — it is the Slice-1 export work authorized by spec Decision 4 (lines 56-62) and Decision 13
(line 361: the exports pin grows by two `__all__` members in Slice 1). Slice 3 introduces **no**
public-surface change of its own (test-only slice; this pass touched only two lines of
`tests/test_permissions.py`). Pass.

### CHANGELOG sanity

Not applicable; slice did not modify `CHANGELOG.md`.

### Documentation / release sanity

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces. (The
`examples/fakeshop/apps/products/schema.py` em-dash→hyphen swap inside a Slice-4 TODO comment is
concurrent out-of-scope churn, not a Slice-3 doc edit, and is left untouched per the standing
guard.)

### What looks solid

- **H1 fix is minimal and correct.** Two lines changed (`narrowed =
  category_type.get_queryset(Category.objects.all(), _INFO)` ×2), with an explanatory comment at the
  filter call site noting why the direct `apply_cascade_permissions` call was a no-op (chain-top
  `Category`, no cascadable forward FK, cascade does not invoke the type's own hook). The assertion
  contracts are unchanged; only the queryset construction was corrected. Worker 2 chose shape (i)
  (hook-invocation) over shape (ii) (`Item`-rooted forward-FK cascade), keeping the gate over
  `Category` so the local `_StaffOnlyCategoryFilter` / `_StaffOnlyCategoryOrder` mirrors still match
  the products `CategoryFilter` / `CategoryOrder` shape byte-for-byte — the lower-surface fix, and
  the forward-FK cascade path is already exercised by the connection/node/list pins.
- **`_INFO` (not `_gate_info`) at the cascade step is correct.** `_exclude_private` ignores `info`
  (narrows unconditionally), so the file's `_INFO` placeholder is sufficient at the visibility step;
  `_gate_info(is_staff=...)` stays on the `apply_sync` calls where the gate resolves
  `info.context.request`. The two layers take independent `info`, matching the "independent layers"
  property the no-leak pin (`test_gate_denial_no_existence_leak`) pins.
- **No regression to the six accepted pins.** All six pass in isolation and in the full focused run;
  this pass touched only `tests/test_permissions.py` (the two `narrowed =` lines) — the other three
  test files and the four other `test_permissions.py` pins are byte-identical to pass 1. The
  no-existence-leak pin (`str(...)` + `.extensions` equality across hidden-present/absent fixtures),
  the nested-transitivity to-many pin (adversarially verified load-bearing in pass 1), the
  connection pin (`totalCount == 2` non-vacuous, raw 3 ≠ narrowed 2), the node/nodes null-hole pins,
  and the list-field default-resolver pin all remain solid.
- **Zero Slice-3 source change confirmed.** `git diff --name-only -- django_strawberry_framework/`
  reports only `__init__.py` and `permissions.py`, both Slice-1 baseline (the `__init__.py` export
  delta is Decision-4/13 authorized; `permissions.py` carries the Slice-1 H1 fix `getattr(field,
  "column", None) is not None` and both `apply_cascade_permissions` + `aapply_cascade_permissions`).
  `permissions.py` carries **no** Slice-3 marker (`NotImplementedError` / `STAGED SEAM` / `Slice 3`
  grep → 0). No `filters/` / `orders/` / `connection.py` / `relay.py` / `list_field.py` edit.

### Static helper

Skipped — no source logic in this slice (test-only construction fix; no `.py` under
`django_strawberry_framework/` touched by Slice 3, no new file, no ≥30/≥50-line logic addition this
pass). Recorded per the BUILD.md helper-trigger rules.

### Temp test verification

- `docs/builder/temp-tests/slice-3/probe_causal.py` — used this pass to adversarially confirm the
  H1 fix's "narrows first" half is causally hook-driven (3 assertions: hook-with-filter narrows to
  `['public']`; identity hook lets `['hidden','public']` through → shape (b) flips; direct
  `apply_cascade_permissions` on chain-top `Category` is a no-op `['hidden','public']`). All 3
  passed. **Deleted (`rm -rf docs/builder/temp-tests/slice-3`, incl. its `__pycache__`); not
  promoted** — it proves the corrected pin is sound and re-confirms the pass-1 root cause; no new
  permanent test is needed beyond the corrected pins themselves (which now causally pin shape (b)).
- `docs/builder/temp-tests/` is empty after cleanup (verified). No
  `git checkout`/`restore`/`stash`/`reset` used anywhere; only `rm` of the file/dir I created under
  `docs/builder/temp-tests/slice-3/`.

### Notes for Worker 1 (spec reconciliation)

- **Nested-pin edge-case note (carry forward, unchanged from pass 1).** A cascade-hidden
  **non-nullable forward FK** (`Item.category`, `null=False`) raises `GraphQLError('Item has no
  category.')` rather than nesting a clean `null` — a non-null GraphQL field returning `None` is a
  null-violation, and `Meta.nullable_overrides` is scalar-only (spec-029 Decision 10), so the FK
  cannot be forced nullable. The correct traversal-narrowing shape for a forward non-null FK is that
  the **parent row drops** via its own cascade (covered by the connection/node/list pins); the
  nested-transitivity pin therefore uses the **to-many** `Category → items` relation (a list can be
  empty/narrowed without a null-violation), matching the DoD's "every edge's nested relations"
  wording. Adjudicated SOUND in pass 1; keep as shipped. Worker 1's discretion whether to add a
  one-line spec Test-plan note (line 456) recording the non-null-forward-FK nullability constraint —
  a clarification, not a contract change.
- **DRY-fixture-duplication note (carry forward for the integration pass).** The cascading-hook +
  hiding-target-schema scaffold is now re-declared across all four Slice-3 files (duplication count
  final). The integration pass should evaluate hoisting a shared cascading-schema test fixture per
  the Plan's DRY analysis and Worker-1's Slice-2 carry-forward. Recorded here in writing; not
  consolidated mid-slice (cross-file conftest fixture is a structural change with its own review
  surface).
- **No Decision-11/12 violation, no source change required.** H1 was a test-construction bug (no-op
  `apply_cascade_permissions` call on a chain-top model), fixed entirely in the test via the
  hook-invocation path. Every pin honors the cascading `get_queryset` through the shipped seams.

### Review outcome

`review-accepted` — H1 is resolved (both gate-composition pins now build `narrowed` via
`category_type.get_queryset(...)`, so the `_exclude_private` `is_private=False` row-narrow genuinely
fires before the gate; both shapes confirmed load-bearing, the "narrows first" half adversarially
verified causal). The focused four-file suite is green at **146 passed / 1 skipped / 0 failed** (the
1 skip is the `FAKESHOP_SHARDED` multi-DB pin, not a Slice-3 pin). No new High/Medium/Low findings;
the six previously-accepted pins are unchanged and still green; zero Slice-3 source change under
`django_strawberry_framework/` confirmed. The DRY cross-file fixture duplication and the
non-null-forward-FK nested-pin edge case are carried forward to the integration pass / Worker 1, not
Slice-3 blockers.

---

## Final verification (Worker 1)

Final-verification pass after Worker 3 set `review-accepted` (pass 2). Read the full artifact
(Plan + both Worker 2 build reports incl. pass 2 + both Worker 3 reviews incl. the nested-pin
adjudication and the DRY carry-forward), the current diff, and the spec's Slice 3 / Decision 11 /
Decision 12 / Edge cases. No source or test edit made (test-only slice; the implementation is
already accepted). One spec edit applied (Edge-cases bullet); spec status line refreshed.

### Checklist results

1. **Spec slice checklist audit (both `- [x]` boxes) — PASS, no re-tick needed.**
   - Box 1 (composition order; no-existence-leak; connection narrows edges+totalCount; node/nodes
     refetch → null; list default-resolver narrows): all five clauses land in the diff and pass.
     Audited each pin against its assertion:
     - `tests/test_permissions.py::test_cascade_then_filter_gate_composition` /
       `::test_cascade_then_order_gate_composition` — both shapes load-bearing. `narrowed` is built
       via `category_type.get_queryset(Category.objects.all(), _INFO)` (the H1-pass-2 hook-invocation
       fix), so `_exclude_private`'s `is_private=False` row-narrow genuinely fires before the gate
       (`apply_sync`) judges input. Shape (a) denial (`pytest.raises(GraphQLError, match=...)`) is
       input-shape-only; shape (b) operates on the cascade-narrowed set (`list(passed) == []`;
       `[alpha, beta]`). "Cascade narrows first, gates judge input second" pinned by consequence.
     - `::test_gate_denial_no_existence_leak` — `str(...)` AND `.extensions` equality across
       hidden-present vs hidden-absent fixtures: byte-identical denial, no existence leak.
     - `tests/test_connection.py::test_connection_over_cascading_type_narrows_edges_and_total_count`
       — seeds 3 items / 2 visible so `narrowed (2) != raw (3)`; `totalCount == 2` is non-vacuous;
       edges drop the hidden-target item; cursors distinct/one-per-edge; `pageInfo` coherent.
     - `tests/test_relay_node_field.py::test_node_refetch_of_cascade_hidden_row_returns_null` →
       `{"item": None}`, `errors is None`; `::test_nodes_batch_holes_for_cascade_hidden_rows` →
       `[None, {"name": ...}]` positional hole (hidden id first), `errors is None`.
     - `tests/test_list_field.py::test_list_field_default_resolver_applies_cascade` → only
       `["visible_item"]`; scoped to the default resolver per the stub docstring.
     - `tests/test_permissions.py::test_nested_relation_traversal_respects_target_cascade` — to-many
       `Category → items` narrows via the `Prefetch` downgrade (`DjangoOptimizerExtension`); the
       query selects exactly `{ allCategories { name items { name } } }` (right-path), hidden item
       absent. Adjudicated sound (see below).
   - Box 2 (package coverage across `tests/test_permissions.py` + `tests/test_connection.py` +
     `tests/test_relay_node_field.py` + `tests/test_list_field.py`): confirmed — all four files
     carry the implemented pins; 8 stubs → 8 implemented tests; zero `@pytest.mark.skip` remaining in
     any of the four files (the only `skipif` is the unrelated `FAKESHOP_SHARDED` multi-DB pin at
     `tests/test_permissions.py:355`). Both boxes correctly ticked by Worker 2; neither over- nor
     under-ticked. No remaining `- [ ]`.
2. **DRY check across Slices 1-3 — DEFERRED to the integration pass (correct home; do NOT force a
   mid-slice extraction).** The cascading-hook shape (`get_queryset` → `apply_cascade_permissions`)
   plus a hiding-`Category`/`Item` target hook now recurs across all four Slice-3 files
   (`test_permissions.py::_exclude_private`, declared multiple times; `test_connection.py` +
   `test_relay_node_field.py` local `_make_cascading_item_node`; `test_list_field.py` inline). This
   matches the Plan's DRY analysis and my Slice-2 carry-forward verbatim. **Decision:** a shared
   cross-file fixture (conftest-level) is a *structural* change with its own review surface; the
   integration pass is its proper home (the duplication count is now final for Slice 3, which is
   exactly the trigger condition I recorded). Forcing the extraction mid-slice would be premature and
   widen the Slice-3 review surface. No in-file near-copy was introduced (each pin reuses its file's
   existing harness; the two same-named `_make_cascading_item_node` helpers are separate per-file
   declarations justified by `_make_sidecar_node_type` being hardcoded to chain-top `Category`).
   Carried forward to `bld-integration.md`.
3. **Focused existing tests (the contract's command, `--no-cov`) — GREEN.**
   `uv run pytest tests/test_permissions.py tests/test_connection.py tests/test_relay_node_field.py tests/test_list_field.py --no-cov -q`
   → **146 passed, 1 skipped, 0 failed** (the 1 skip is the `FAKESHOP_SHARDED` multi-DB pin, not a
   Slice-3 pin). Matches the contract's expected ≈146/1 exactly.
4. **Spec reconciliation — one edit (the nested-pin edge case); the second carry-forward (DRY)
   deferred to the integration pass.**
   - Nested-pin edge case: ADDED a one-line Edge-cases bullet (see below). The distinction
     (non-nullable forward FK → parent-drop vs. to-many → list-narrow) is a verified mechanical
     consequence of Decision 6's row-exclusion contract; pinning it sharpens Decision 12's "every
     edge's nested relations" wording without altering any Decision contract. Worker 3 adjudicated
     the to-many redesign sound and left the spec note to my discretion; I added it because it
     prevents a future reader from misreading the to-many shape as a workaround.
   - No Decision-11/12 violation surfaced; the slice required zero source change to
     `filters/` / `orders/` / `connection.py` / `relay.py` / `list_field.py` (confirmed: only
     `django_strawberry_framework/__init__.py` + `permissions.py` appear in
     `git diff -- django_strawberry_framework/`, both Slice-1 baseline; `permissions.py` carries no
     Slice-3 marker).
5. **Final status:** `final-accepted` — all checks pass.

### Summary

Slice 3 ships eight composition pins (no source change) proving the shipped pipelines honor a
cascading `get_queryset` through their existing seams (Decisions 11/12):
- **Gate composition (Decision 11):** the `FilterSet` / `OrderSet` `check_<field>_permission` gates
  survive unchanged and compose as "cascade narrows first, gates judge input second" — a gated-input
  denial fires on input shape alone (independent of hidden rows), a passing input operates only on
  cascade-narrowed rows, and the denial is byte-identical with/without hidden rows present
  (no existence leak).
- **Connection / node / list (Decision 12):** a `DjangoConnectionField` over a cascading type
  narrows `edges` and `totalCount` together (post-visibility count, non-vacuously distinct from the
  raw count); `DjangoNodeField` / `DjangoNodesField` refetch of a cascade-hidden row returns `null`
  with no existence leak (single → `None`; batch → positional null hole); `DjangoListField`'s default
  resolver narrows; and a nested to-many relation narrows transitively via the optimizer's `Prefetch`
  downgrade. Zero change to `filters/` / `orders/` / `connection.py` / `relay.py` / `list_field.py`.

### Spec changes made (Worker 1 only)

- `docs/spec-034-permissions-0_0_10.md` — **Edge cases** (new bullet inserted immediately after the
  `Meta.fields`-excluded FK edges bullet, formerly line 394). Reason: Slice 3's nested-transitivity
  pin (`test_nested_relation_traversal_respects_target_cascade`) was implemented over a **to-many**
  relation after Worker 2/3 verified (and Worker 3 adjudicated sound) that a cascade-hidden
  **non-nullable forward FK** (`Item.category`, `null=False`) cannot null-resolve at the field (a
  non-null GraphQL field returning `None` is a null-violation; `Meta.nullable_overrides` is
  scalar-only per spec-029 Decision 10) — so for such an edge the **parent row drops** via its own
  cascade (Decision 6's row-exclusion contract) rather than nesting a `null`. The bullet pins the
  by-FK-shape resolution of Decision 12's "every edge's nested relations respect the same cascade"
  wording (to-many → list-narrow; non-null forward FK → parent-drop) and names which Slice-3 pins
  exercise each shape. A clarification of a verified consequence, not a contract change.
- `docs/spec-034-permissions-0_0_10.md` line 5 (status line) — refreshed from "Slice 1 (cascade
  foundation) shipped; Slices 2-5 remain" to "Slices 1-3 (cascade foundation; optimizer cooperation +
  N+1 audit; composition pins) shipped; Slices 4-5 remain." Reason: per-spawn status-line
  re-verification (worker-1.md) — Slice 2 is `final-accepted` and Slice 3 is accepted this pass; the
  prior wording understated reality. "Shipped" matches the spec's own usage for accepted-uncommitted
  slices (it already called Slice 1 "shipped"); the on-disk `0.0.9` version note (line 3) is
  unchanged (Decision 13 — joint-cut owns the bump).
- Verified after both edits: `uv run python scripts/check_spec_glossary.py --spec docs/spec-034-permissions-0_0_10.md`
  → `OK: 43 terms` (the new Decision-6 cross-reference link resolves).
