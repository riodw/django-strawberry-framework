# DRY Review: Optimizer Upgrade (commit 6daba908)

Scope: the full optimizer arc (window rigor, join taxonomy, strategy seam, PG
tier, lateral backend, review fixes) plus the tests and scripts it added.
Method: utils inventory first, then cross-module duplication sweep of
`plans.py`, `walker.py`, `connection.py`, `selections.py`, `extension.py`,
`nested_fetch.py`, `lateral_fetch.py`, `join_taxonomy.py`, `filters/base.py`,
`conf.py`, and the new test/bench files. Findings only - nothing implemented.
Line numbers are as of HEAD (6daba908).

The findings are grouped: Majors 1-3 are one FAMILY (the window-shape
vocabulary is spelled per-module instead of owned once) and would ideally land
as one consolidation slice; the rest are independent.

(The previous content of this file - the fourth-round spec-042 debug-toolbar
review - is preserved in git history at 6daba908.)

---

## Implementation status (2026-07-07, working tree on top of 27d08327)

- **IMPLEMENTED**: Majors 1-7; moderates M8-M12; test-tier T1-T6, T8.
  Key artifacts: `plans.py::WindowRangePlan`/`window_range_plan` +
  `order_entry_name_and_direction` + `deferred_loading_of`;
  `utils/connections.py::is_ambiguous_empty_window`;
  `selections.py::connection_total_count_selected`/
  `connection_has_next_page_selected`;
  `nested_fetch.py::attach_windowed_prefetch`; descriptor slots
  `parent_link_field`/`through_child_field` on `RelationJoinDescriptor`
  (single `LateralWindowSpec` construction); walker
  `_dispatch_single_relation` + `_absorb_child_plan` (cacheable folded in);
  `connection.py::_set_total_count`/`_empty_page_connection`;
  `filters/base.py::_apply_lookup_predicate`;
  `tests/optimizer/conftest.py::nested_connection_request`;
  `tests/conftest.py::isolate_global_registry`;
  `examples/fakeshop/strategy_schemas.py` (make_django_type +
  build_strategy_schema, shared by the parity suite and the bench);
  `examples/fakeshop/graphql_client.py` (post_graphql/assert_graphql_data,
  8 modules migrated); `scripts/_bench_common.py`
  (bootstrap_fakeshop_django); `_assert_parity` now returns
  `(data, captured)`.
- **SKIPPED (deliberate)**: M13 (the three queryset fingerprints keep
  genuinely different semantics; a predicate layer would add indirection
  without owning a contract), M14 (Major 5's shared attach removed the
  duplicated field threading between strategies; restructuring the request/
  spec into a window value object would churn the public
  `NestedConnectionRequest` contract for one remaining site per layer),
  T7 (per its own caveat - no seeder unification).
- Gates: SQLite sweep 2973 passed / coverage 100.00%; PG sweep 2985 passed /
  coverage 100.00%; ruff format+check, trailing commas, pre-commit all clean;
  both bench scripts smoke-run (lateral verified executing on PG).

---

## MAJOR 1 - The window range/marker arithmetic exists twice, in two dialects

**Sites**
- `optimizer/plans.py:807-848` - `apply_window_pagination`: the reverse
  branch (`rn > offset` then `rn_reversed <= limit`), the forward branch
  (`rn > offset` AND `rn <= offset + limit`), and the marker OR (`| Q(rn=1)`),
  built as Django `Q` objects.
- `optimizer/lateral_fetch.py:194-230` - `build_lateral_sql`: the SAME
  three-way branch structure rendered as raw SQL strings, self-described as
  "mirroring ``apply_window_pagination`` exactly" (plus the lateral-only
  `plain_first_page` ORDER BY/LIMIT shape).

**Why it matters** This is the byte-parity invariant of the whole lateral
backend: if one copy's bound arithmetic (offset threshold, `offset + limit`
upper bound, marker condition) drifts, lateral pages silently diverge from
windowed pages. Today the only thing keeping them aligned is the pg parity
suite.

**Suggested consolidation** The renderers cannot merge (Q vs SQL), but the
DECISIONS can: a pure `window_range_plan(offset, limit, reverse) ->
WindowRangePlan` in `plans.py` (fields like `lower_bound: int | None`,
`upper_bound: int | None`, `use_reversed_row_number: bool`,
`add_marker_row: bool`, `plain_first_page: bool`), computed once and consumed
by both `apply_window_pagination` and `build_lateral_sql`. Each backend keeps
only its rendering of the shared plan. `lateral_fetch` already imports from
`plans`, so no new dependency edge. (The `plain_first_page` flag stays a
lateral-only rendering choice, but its ELIGIBILITY predicate - forward,
zero offset, bounded positive limit - belongs in the shared plan.)

## MAJOR 2 - The unbounded-limit sentinel (`None` / `sys.maxsize`) is spelled at 6+ sites

**Sites**
- `optimizer/plans.py:819` and `:827` (`limit is not None and limit !=
  sys.maxsize`, the forward copy adding `limit >= 0`)
- `optimizer/walker.py:1552-1558` (`limit is None or limit == 0 or limit ==
  sys.maxsize` inside the `with_total_count` decision)
- `optimizer/lateral_fetch.py:197-203`, `:215`, `:223` (three more copies,
  again with/without the `>= 0` guard)

**Why it matters** The forward and reverse copies already disagree subtly
(`limit >= 0` present in some, absent in others). Copy-paste drift here
changes which shapes get an upper bound.

**Suggested consolidation** Two options, strongest first:
1. Normalize the sentinel AT THE SOURCE: `utils/connections.py::
   derive_connection_window_bounds` already documents "``limit is None``
   means no upper bound" - have it map `sys.maxsize -> None` once, so no
   downstream module ever sees `sys.maxsize`. `apply_window_pagination` /
   `build_lateral_sql` / the walker then only test `limit is None`. (Check
   the direct `apply_window_pagination` callers in tests; the default-arg
   contract is unchanged.)
2. If the sentinel must survive: `window_limit_is_unbounded(limit)` +
   `window_has_upper_bound(limit)` predicates next to the `WINDOW_*`
   constants in `plans.py`, called by all six sites, with the `>= 0`
   question answered once deliberately.

## MAJOR 3 - The ambiguous-empty-shape predicate (`offset > 0 or limit == 0`) is spelled in four layers

**Sites**
- `optimizer/plans.py:831` (decide to add the marker rows)
- `optimizer/lateral_fetch.py:227` (same decision in the SQL dialect)
- `optimizer/walker.py:1553-1555` (force `with_total_count` for marker shapes)
- `connection.py:255` (`ambiguous = not reverse and (offset > 0 or limit ==
  0)` - decide to CONSUME rows as marker-classified)

**Why it matters** This is a plan-time/resolve-time contract exactly like the
sidecar-kwargs family that `utils/connections.py` already single-sites (its
module docstring is the argument: "a future sidecar is a one-line edit here
rather than synchronized edits across the planner and resolver"). If the
plan side and the consume side ever disagree on what counts as ambiguous,
the fast path misclassifies empty pages.

**Suggested consolidation** One predicate - for example
`is_ambiguous_empty_window(offset, limit)` - in `utils/connections.py`
beside `ConnectionWindowBounds` (it is a property of the bounds; it could
even be a method/property on the dataclass). All four sites call it. If
MAJOR 1's `WindowRangePlan` lands, its `add_marker_row` field IS this
predicate for the two builder sites, leaving only walker + connection as
callers.

## MAJOR 4 - The totalCount / hasNextPage selection predicates are hand-aligned in three places

**Sites**
- `optimizer/selections.py:509-535` - `connection_count_required(selection)`
  (plan time): `direct_child_selected(children, "totalCount")` OR the
  `hasNextPage`-under-`pageInfo` walk via `named_children`.
- `connection.py:440-465` - `_total_count_requested(info)` (resolve time):
  the same `totalCount` walk mapped over `info.selected_fields`.
- `connection.py:468-487` - `_has_next_page_requested(info)` (resolve time):
  the `hasNextPage` half, byte-identical inner expression to
  `connection_count_required`'s.

**Why it matters** The conditional `_dst_total_count` feature (workstream B)
is precisely "plan time annotates iff resolve time will read": both
docstrings acknowledge the invariant, but it is currently maintained by
keeping three copies visually aligned. Divergence means a wrong
`hasNextPage`/`totalCount` or a spurious per-parent fallback.

**Suggested consolidation** Two per-selection primitives in
`optimizer/selections.py` - `connection_total_count_selected(selection)` and
`connection_has_next_page_selected(selection)`. `connection_count_required`
becomes their OR; the two `connection.py` helpers become
`any(<primitive>(f) for f in info.selected_fields)`. One implementation of
each walk, observably shared across the plan/resolve halves. While there,
fold in the one spelling inconsistency: `_total_count_requested` reads
`.selections` directly where the plan-time twin uses the safer
`getattr(..., "selections", None) or []`.

## MAJOR 5 - The two strategies' `plan()` bodies are near-verbatim twins

**Sites**
- `optimizer/nested_fetch.py:147-166` - `WindowedPrefetchStrategy.plan`:
  `apply_window_pagination(request.child_queryset, partition_by=..., order_by
  =..., offset/limit/reverse/with_total_count=request...)` then
  `append_prefetch_unique(plan.prefetch_related, Prefetch(request.lookup,
  queryset, to_attr=request.to_attr))`.
- `optimizer/lateral_fetch.py:423-445` - `LateralPrefetchStrategy.plan`: the
  IDENTICAL two steps, differing only in wrapping the windowed queryset via
  `_as_lateral_queryset(windowed_queryset, spec)` before the Prefetch.

**Why it matters** The windowed body IS the lateral correctness floor - the
lateral strategy must build exactly what the windowed strategy would. Today
that is enforced by a copied 8-argument call; add a parameter to
`apply_window_pagination` (or a field to the request) and both copies must
move in lockstep.

**Suggested consolidation** One shared helper in `nested_fetch.py`, e.g.
`attach_windowed_prefetch(request, plan, *, wrap=None)` (or a
`windowed_queryset_for(request)` builder plus a shared attach): the windowed
strategy calls it bare; the lateral strategy passes
`wrap=lambda qs: _as_lateral_queryset(qs, spec)`. A third future strategy
(the portable correlated-subquery backend the Prisma notes anticipate) gets
the floor for free.

## MAJOR 6 - `_build_lateral_spec` constructs `LateralWindowSpec` twice with 10 shared kwargs; the through-link derivation belongs to the taxonomy

**Sites**
- `optimizer/lateral_fetch.py:499-518` (THROUGH_TABLE construction) and
  `:519-538` (DIRECT_FK construction): of the 15 spec fields, 10 are
  identical between the branches; only the five link-shaped fields differ
  (`parent_link_field` / `parent_link_table` / `through_table` /
  `through_child_column` / `prefetch_value_aliases`).
- `optimizer/lateral_fetch.py:541-556` - `_through_link` derives the
  through table's (parent-side FK, child-side FK) from the raw field.

**Suggested consolidation** Two moves:
1. Mechanical: branch only on the five link fields (compute them in the
   if/else), then ONE `LateralWindowSpec(...)` construction.
2. Structural (the creative half): `join_taxonomy.py` declares itself the
   home of "everything join-shaped one relation field implies", and
   `RelationJoinDescriptor` already carries `through_model` +
   `lateral_shape`. Promote the `_through_link` FK-pair derivation (and the
   DIRECT_FK `field.field` parent-link resolution at `:521`) into
   `classify_relation_join` as descriptor slots (e.g. `parent_link_field`,
   `through_child_field`). `_build_lateral_spec` then just READS the
   descriptor it is already handed via `request.join`, and any future
   strategy (or the polymorphic work, TODO-ALPHA-035) inherits the same
   resolved join facts instead of re-walking `remote_field` /
   `m2m_field_name`.

## MAJOR 7 - Three parsers of the `deterministic_order` entry shape, two with a latent disagreement

**Sites**
- `optimizer/walker.py:994-1005` - `_order_entry_field_name`: strips ONE
  leading `-` from a str entry, else reads `entry.expression.name`.
- `optimizer/plans.py:658-661` (inside `ends_in_unique_column`): same
  intent, but `terminal.lstrip("-")` (strips ALL leading dashes), else the
  same `expression.name` read.
- `optimizer/lateral_fetch.py:559-585` - `_order_columns`: a third parse of
  the same entry vocabulary (`startswith("-")`, name extraction, `pk`
  normalization, concrete-field resolution).

**Why it matters** Two of the three disagree on dash-stripping (`"--name"`
parts ways); all three must track any change to what `deterministic_order`
emits. The entry vocabulary is a de facto contract with no single owner.

**Suggested consolidation** One exported parser co-located with
`deterministic_order` / `_reverse_order_by` in `plans.py` - e.g.
`order_entry_name_and_direction(entry) -> (name, descending) | None` -
with ONE deliberately chosen dash rule. Walker and `ends_in_unique_column`
call it for the name; `lateral_fetch._order_columns` keeps only its
column-resolution tail (`pk` mapping + concrete-field lookup).

---

## MODERATE findings (package)

### M8 - `connection.py` empty-page construction + the `want_count` setattr idiom
`connection.py:237-248` and `:262-283` build the identical
`cls(edges=[], page_info=relay.PageInfo(start_cursor=None, end_cursor=None,
has_previous_page=offset > 0, has_next_page=<X>))` shape; the
`if want_count: setattr(conn, _TOTAL_COUNT_ATTR, <x>)` guard recurs at
`:246`, `:281`, `:326`, `:780-781`, `:796-797` (five sites). Extract
`_empty_page_connection(cls, *, offset, has_next_page, want_count, total)`
and `_set_total_count(conn, *, want_count, value)`. The
`has_previous_page = offset > 0` flag arithmetic is pipeline-parity-bearing
and deserves one home.

### M9 - The `query.deferred_loading` private-contract unpack is read in three places
`plans.py:451-463` (`_consumer_only_fields`) and `plans.py:529-539`
(`_consumer_projection`) share seven identical opening lines (getattr chain,
None guard, try/except unpack); `lateral_fetch.py:588-605`
(`_select_columns`) is a third direct reader of the same Django-private
tuple. One `deferred_loading_of(queryset) -> (frozenset, bool) | None`
primitive in `plans.py`; the two consumer helpers and the lateral projection
build on it. Both plans.py docstrings claim to "centralize the brittle
private contract" - currently each centralizes its own copy.

### M10 - The select-vs-prefetch relation dispatch is written three times in the walker
`walker.py:480-504` (cardinality dispatch), `:802-826` (`force_select` hint
branch), `:828-840` (`force_prefetch` hint branch): the same
`_plan_prefetch_relation(...)` / `_plan_select_relation(...)` pair with the
same 8-9 argument list. One `_dispatch_single_relation(*, prefer_prefetch,
...)` helper removes three copies of the argument threading.

### M11 - "Absorb an accepted child plan" bookkeeping is duplicated
`walker.py:685-687` and `:1583-1585`: `_merge_child_plan_metadata(parent,
child)` followed by `if not child.cacheable: parent.cacheable = False`.
Forgetting the second line at a future third site is a cache-poisoning bug
(the exact hazard the plan docstring warns about). Fold the cacheable
propagation INTO `_merge_child_plan_metadata` (or rename to
`_absorb_child_plan`).

### M12 - `filters/base.py`: the distinct + single-predicate idiom exists twice
`filters/base.py:130-133` (`ArrayFilter.filter`) and `:444-446`
(`GlobalIDMultipleChoiceFilter.filter`) both spell `if self.distinct:
qs = qs.distinct()` + `self.get_method(qs)(**{f"{self.field_name}__
{self.lookup_expr}": value})`. Correctness-relevant: the GlobalID `in`-fix
from this commit depends on the whole-list-in-one-predicate form; a second
independent copy of that form can drift. One module-level
`_apply_lookup_predicate(filter_instance, qs, value)` shared by both. (The
GlobalID decode loop itself is already single-sited in
`_decode_and_validate_global_id` - no action there.)

### M13 - Three "is this queryset pristine" fingerprints with overlapping probes
`nested_fetch.py:79-90` (`unwindowable_child_queryset_reason`: is_sliced /
select_for_update / combinator / distinct / iterable class),
`lateral_fetch.py:329-335` (`_extract_parent_ids`: is_sliced / distinct /
select_related) plus `:295` (iterable class), and `lateral_fetch.py:485`
(`_build_lateral_spec`: where.children / select_related / annotations /
extra). The semantics genuinely differ (walker safety gate vs fetch-time
purity vs plan-time expressibility), so a full merge is wrong - but the
shared ATTRIBUTE PROBES (`is_sliced`, `distinct`, iterable-class,
`select_related`) could become tiny named predicates in `nested_fetch.py`
so each fingerprint composes the same probes instead of re-spelling the
getattr chains. Low urgency; flagged so a future probe fix (a Django
rename, say) lands once.

### M14 - The window slice quadruple is threaded field-by-field through three layers
`(offset, limit, reverse, with_total_count)` is copied name-by-name from the
walker into `NestedConnectionRequest` (`walker.py:1563-1576`), from the
request into `apply_window_pagination` calls (both strategies), and from the
request into `LateralWindowSpec` (`lateral_fetch.py:514-517`, `:534-537`).
`ConnectionWindowBounds` already models the first three. Creative option: a
frozen window value object (bounds + `with_total_count`) carried as ONE
field on the request and the spec, and accepted by
`apply_window_pagination` - a new window parameter then touches one
dataclass instead of four call sites. Pairs naturally with MAJOR 5.

---

## Test-tier and scripts findings

### T1 - The `NestedConnectionRequest` builder is duplicated across the two strategy test modules
`tests/optimizer/test_nested_fetch.py:36-56` (`_books_request`) and
`tests/optimizer/test_lateral_fetch.py:43-72` (`_request` +
`_shelf_books_request`) build the same 13-key request dict with
`values.update(overrides)`. Add one parameterized
`nested_connection_request(field_owner, field_name, **overrides)` helper in
a `tests/optimizer/conftest.py`; a new request field then touches one
builder.

### T2 - `_isolate_global_registry` autouse fixture duplicated verbatim
`tests/test_relay_connection.py:59-72` and
`tests/test_lateral_pg_parity.py:36-43`: identical registry +
`_connection_type_cache` clear-around-yield. Promote to `tests/conftest.py`
(opt-in fixture) - it is a test-isolation invariant that should not have two
copies.

### T3 - The two-strategy schema-pair builder exists in both the parity test and the bench script
`tests/test_lateral_pg_parity.py:46-104` and
`scripts/bench_nested_fetch.py:110-183` both declare the Book/Shelf
DjangoType pair, finalize, and close over `_schema(strategy) ->
strawberry.Schema(extensions=[lambda: DjangoOptimizerExtension(
nested_connection_strategy=strategy)])`. One shared
`build_strategy_schema(strategy, *, extra_types=...)` helper (test-support
module) serves both; the bench keeps its extra per-parent schema, the test
its Genre/Loan additions.

### T4 - `_make_type` DjangoType-declaration helper re-spelled three times
`tests/test_relay_connection.py:75-93`, `tests/test_lateral_pg_parity.py:
46-57`, `tests/test_permissions.py:122-141` - same
`type(name, (DjangoType,), {"Meta": type("Meta", (), ...)})` core with
different Meta shorthands. One `make_django_type(name, model, fields, *,
node=True, meta_extra=None, namespace_extra=None)` in `tests/conftest.py`
expresses all three (the parity copy's `total_count` is
`meta_extra={"connection": {"total_count": True}}`).

### T5 - `_post_graphql` / `_assert_graphql_data` duplicated across ~7 fakeshop modules
`examples/fakeshop/test_query/test_library_api.py:61-77`,
`test_products_api.py:64-83`, and five siblings each define the same
`Client().post("/graphql/", ...)` wrapper (and several the same
status-200 + data-equality assert). Mostly PRE-EXISTING, but this commit's
new tests reinforce it. One superset-signature helper pair in
`examples/fakeshop/test_query/conftest.py` (`post_graphql(query, *,
client=None, variables=None)`).

### T6 - Benchmark scaffolding shared between the two bench scripts
`scripts/bench_nested_fetch.py:44-70,206-286` vs
`scripts/bench_plan_cache.py:50-77,130-240`: byte-identical `_FAKESHOP`
path constant, near-identical `_bootstrap_django` core (sys.path + settings
+ `django.setup()` + migrate) diverging only in the DB tail (PG DSN assert
vs sqlite `:memory:`), and the same argparse + median-timing +
fixed-width-table `main()` shape. A `scripts/_bench_common.py` with
`bootstrap_fakeshop_django(mode)`, a timing-samples helper, and the table
printer leaves each script holding only its candidates and columns.

### T7 - Library seeding: extract only the smallest primitive
`tests/test_lateral_pg_parity.py:107-131`, `scripts/bench_nested_fetch.py:
73-107`, `tests/test_relay_connection.py:133-143`, and the fakeshop
`_seed_library_graph` / `_seed_genre_with_books` all build the
Branch/Shelf/Book(/Genre) graph - but with MATERIALLY different fan-out
shapes (parity edge cases vs dense benchmark bulk_create vs single-row
fixtures). Do NOT unify the top-level seeders; at most extract the smallest
composable builder (`make_shelf_with_books(branch, code, titles, *,
genre=None)`) and let each seeder keep its own fan-out. Flagged with this
caveat because a blind merge would erase the shapes the tests depend on.

### T8 - `_assert_parity` re-inlined by the reverse-M2M parity test
`tests/test_lateral_pg_parity.py:140-167` (`_assert_parity`) vs `:217-234`:
the through-once test re-spells the capture/compare preamble because it also
asserts join counts. Let `_assert_parity` return the captured queries (or
accept an extra-assert callback) and the test reuses it.

---

## Checked and already DRY (verified - no action, listed so nobody re-chases)

- **Window attr names / to_attr / annotated probe**: `WINDOW_ROW_NUMBER` /
  `WINDOW_TOTAL_COUNT` / `WINDOW_ROW_NUMBER_REVERSED` are single-sited
  constants in `plans.py` used everywhere (including as the lateral SQL AS
  aliases); the `_dst_<field>_connection` string is built ONLY by
  `walker._relation_connection_to_attr`; the "rows are annotated" probe
  exists once (`connection._window_rows_are_annotated`).
- **utils reuse in the hot modules**: `connection.py` / `extension.py`
  already route through `normalize_query_source`,
  `apply_type_visibility_sync/async`, `derive_connection_window_bounds`,
  the sidecar-kwarg family, `model_for`, `initial_queryset` - no inline
  re-derivations found.
- **Sync/async twins in `connection.py`**: `_pipeline_sync/_pipeline_async`
  and `_attach_count_sync/_attach_count_async` already share extracted
  head/tail (`_prepare_pipeline_source`, `_finalize_queryset`,
  `_consume_window`, `_consume_fallback`); the residue is exactly the
  colored steps the package deliberately keeps explicit (no maybe-await
  abstraction). M8's `_set_total_count` is the only shared line left.
- **`window_partition_for_prefetch` / `_connector_only_field`**: already
  thin shims over `join_taxonomy.classify_relation_join` - this is the DRY
  win the commit itself landed.
- **`_select_path_traversable` defer-vs-only branches (plans.py:584-590)**:
  look like twins, are genuinely different set semantics (exact-entry block
  vs restricted-level head-match). Correctly unshared.
- **`conf.py` setting accessors**: two one-line accessors with different
  coercion; below the consolidation bar until a third lands.
- **`on_execute` ContextVar set/reset (extension.py:843-864)**: six paired
  set/reset lines in one function, single-sited - an ExitStack would trade
  auditability for brevity; not recommended.
