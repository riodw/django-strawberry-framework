# Plan: Single-parent degenerate fast path for the windowed nested-connection prefetch

## Context

The windowed nested-connection scheme (`ROW_NUMBER() OVER (PARTITION BY fk)` in
`plans.py::apply_window_pagination`) has no LIMIT pushdown: with N parents that is the right
trade (one query, not N), but when the prefetch executes with exactly **one** parent id the
database numbers *every* child row before filtering `rn <= limit`. A parent with 50k children
and `first: 10` scans all 50k rows where `WHERE fk = x ORDER BY ... LIMIT 10` is an index walk.
This plan adds a **runtime-only** fast path: at fetch time, when the Django-prefetch-injected
`IN` list has length 1 and the shape is a count-free plain first page, execute the plain
filtered LIMIT query instead and synthesize `_dst_row_number` in Python. Any unrecognized
shape returns `None` and the superclass `_fetch_all` runs the already-planned windowed body —
the same strict-degradation contract `LateralQuerySet` already uses. Cache note (precise
wording): the wrapped `SingleParentWindowQuerySet` IS cached inside the `Prefetch` in the
plan cache (same as lateral) — only the len==1 decision is fetch-time, so cache hits and
misses behave identically. Verified.

**Two verified corrections to the original idea** (state both in the new module docstring):

1. `node(id:)` roots do NOT reach the windowed prefetch today — `types/relay.py::
   _resolve_node_default` returns `qs.first()` (an instance) and the extension middleware only
   optimizes `QuerySet` results. The fast path targets the general case: any windowed prefetch
   whose injected parent-IN list has length 1 (e.g. a root connection/filtered list returning
   one parent row). Do NOT claim node-root benefit.
2. M2M/THROUGH_TABLE joins are excluded in v1: Django's M2M prefetch attaches rows via
   `extra(select={"_prefetch_related_val_*": ...})`, which a degenerate re-query from the
   pristine clone cannot reproduce. v1 requires the DIRECT_FK join shape.

## Standing constraints (AGENTS.md — do not violate)

- READ AGENTS.md before starting. ASCII-only in `.py` files (no arrows/ellipsis chars).
- `uv run ruff format .` + `uv run ruff check --fix .` after every edit.
- Do NOT commit, branch, or stash. Leave everything dirty for the maintainer.
- Do not touch KANBAN tables / db.sqlite3, CHANGELOG.md, or GLOSSARY.md — this is a
  direct implementation from this plan; card/spec ceremony is deferred.
- Concurrent sessions may dirty other files — never revert files you didn't edit.
- Match surrounding comment density and idiom; the optimizer modules are heavily documented.

## Architecture (all line refs verified against current tree)

Seams reused, not invented:
- `nested_fetch.py::attach_windowed_prefetch(request, plan, *, wrap=None)` (179-220) — the
  existing `wrap` hook (lateral already uses it) means **zero changes** to the shared floor.
- `lateral_fetch.py::LateralQuerySet` (396-424) — the fetch-time interception pattern to
  mirror: `_fetch_all` populates `_result_cache` then STILL calls `super()._fetch_all()`
  (load-bearing: runs `_prefetch_related_objects` for deeper nesting levels).
- `lateral_fetch.py::_is_window_qual` (566-576) — already spec-free; import directly. It
  skips window quals including the `(range) OR rn = 1` marker OR-node.
- `utils/connections.py::window_range_plan` (240-304) — `plain_first_page` /
  `fetch_limit` (= limit+1 iff `next_page_probe`) are the derivations to ride.
- Consumer contract (`connection.py`): `_window_rows_are_annotated` (~1885) requires
  `_dst_row_number` on EVERY row (empty list passes); `_resolve_from_window` (296-575)
  re-infers the probe as `plain_first_page and rows and getattr(rows[-1],
  "_dst_total_count", None) is None`, splits the probe row by `rn > limit` via
  `split_window_rows`, computes offset cursors as `rn - 1`.

Adversarial-verifier confirmations the executor can rely on (do not re-derive):
- For the eligible shape, `apply_window_pagination` annotates exactly `{_dst_row_number}`
  and DOES filter `rn <= fetch_upper_bound` (plans.py:1044-1064) — a window qual
  `_is_window_qual` recognizes. Fetch-time WHERE = that qual + the injected parent IN.
- conf.py has NO known-keys allowlist (`Settings.__getattr__` conf.py:238-266 is a plain
  dict lookup); the reload path covers new keys automatically. Step 2 needs nothing extra.
- The double-nested-prefetch worry is moot: synthesizing rows from the pristine clone runs
  deeper prefetches once; `super()._fetch_all()`'s pass is a no-op on already-populated
  instances (same net behavior as lateral).
- `_parent_in_values` has ONE production caller (lateral_fetch.py:548) and FIVE test call
  sites (tests/optimizer/test_lateral_fetch.py:630, 641, 652, 662, 668) — all six must
  move to the keyword signature. The tests' `spec = _build_lateral_spec(...)` assignment
  at ~line 628 becomes dead once the calls stop taking `spec` — remove it.
- REUSE, don't copy: import `_deduplicate_parent_ids` from `lateral_fetch` (its TypeError
  arm is already covered there — one owner of the unhashable/NULL semantics). Extract the
  WHERE walk into a `_single_parent_where_ids(where, spec)` helper so the recognizer stays
  readable and within line budgets.
- `override_settings(DJANGO_STRAWBERRY_FRAMEWORK={...})` IS seen at fetch time: conf.py
  installs a `setting_changed` receiver (`conf.py:436` -> `reload_settings`), same
  mechanism the `HIDE_FLAT_FILTERS` live test (test_library_api.py:789-803) relies on.
  The fakeshop base dict is empty (`config/settings.py:228-231`), so the disable test
  passes a fresh `{"SINGLE_PARENT_FAST_PATH": False}`.
- COVERAGE TRAP: in `single_parent_spec`, fold the join checks into ONE expression —
  `join.lateral_shape is not LateralJoinShape.DIRECT_FK or join.parent_link_field is None`
  — because DIRECT_FK always has a non-None `parent_link_field` (join_taxonomy.py:204), so
  a separate `parent_link_field is None` branch is unreachable and would break
  fail_under=100. One combined branch is earned by the THROUGH_TABLE test.
- Probe nuance for the live SQL assertions: `next_page_probe` is True only when
  `pageInfo { hasNextPage }` is selected WITHOUT `totalCount` — that test asserts
  `LIMIT 3` (first:2 + probe); the no-pageInfo test produces `LIMIT 2` and asserts only
  the absence of `OVER (`. The live `OVER (` string-scan is a new (but sound) idiom —
  the only existing `OVER (` assertion is package-tier.

## Step 1 — refactor `_parent_in_values` (lateral_fetch.py:644)

Decouple from `LateralWindowSpec` so both fetchers share the recognizer:

```python
def _parent_in_values(node: Any, *, column: str, table: str) -> list | None:
```

Body: `spec.parent_link_column` -> `column`, `spec.parent_link_table` -> `table`. Update the
single caller in `_extract_parent_ids` (~548) to keyword form. Grep
`tests/optimizer/test_lateral_fetch.py` for direct call sites and update them.

## Step 2 — setting (conf.py)

Follow the `NESTED_CONNECTION_STRATEGY` pattern exactly:
- `SINGLE_PARENT_FAST_PATH_KEY = "SINGLE_PARENT_FAST_PATH"` near the other `*_KEY` consts
  (~line 74), matching neighbor comment style.
- Reader after `nested_connection_strategy_setting` (~364):

```python
def single_parent_fast_path_setting() -> bool:
    """Whether the runtime single-parent degenerate window fast path is enabled.

    Reads DJANGO_STRAWBERRY_FRAMEWORK["SINGLE_PARENT_FAST_PATH"], default True.
    Consumed at FETCH time by optimizer/single_parent_fetch.py so the flag is
    plan-cache invisible and override_settings-testable.
    """
```

- If conf.py keeps a known-keys allowlist / `reload_settings` wiring, register the new key
  there too (verify while implementing — mirror whatever `NESTED_CONNECTION_STRATEGY` does).

## Step 3 — new module `django_strawberry_framework/optimizer/single_parent_fetch.py`

ASCII-only. Imports: `QuerySet`, `ModelIterable` (from `django.db.models.query`),
`dataclass`, `Any`, `from . import logger`, `from .plans import WINDOW_ROW_NUMBER`,
`from .lateral_fetch import _is_window_qual, _parent_in_values`,
`from ..utils.connections import window_range_plan`. Import cycle is safe because
`nested_fetch` imports THIS module only lazily inside `WindowedPrefetchStrategy.plan`
(precedent: `AutoNestedConnectionStrategy.plan`, nested_fetch.py:251-257).

### 3a. Spec (frozen dataclass) `SingleParentWindowSpec`

Fields: `pristine_child_queryset` (the pre-window `request.child_queryset` — carries
select_related/only/nested prefetches), `order_by: tuple`, `parent_link_attname: str`
(filter kwarg), `parent_link_column: str` + `parent_link_table: str` (WHERE-tree matching;
DIRECT_FK means the link lives on the child table), `limit: int`, `fetch_limit: int`.
No with_total_count/offset/reverse fields — eligibility pins them False/0/False.

### 3b. Plan-time eligibility `single_parent_spec(request) -> SingleParentWindowSpec | None`

Return `None` unless ALL hold (document each exclusion in the docstring):
- `request.keyset_seek is None` (keyset out of scope v1)
- `not request.with_total_count` (a bare LIMIT cannot produce the partition count;
  totalCount/counted shapes keep the window)
- `not request.reverse` (last-only needs the reversed row number)
- `type(request.child_queryset) is QuerySet` (class-rebind safety — same rule as
  `_build_lateral_spec`, lateral_fetch.py:776)
- join shape is DIRECT_FK and `request.join.parent_link_field is not None` (M2M excluded —
  correction 2; use the exact enum/attr names found on `RelationJoinDescriptor` in
  `join_taxonomy.py`, verify before writing)
- `window_range_plan(offset=request.offset, limit=request.limit, reverse=request.reverse,
  next_page_probe=request.next_page_probe).plain_first_page` is True (implies offset==0,
  bounded limit>0)

Build spec with `fetch_limit=range_plan.fetch_limit`.

### 3c. `SingleParentWindowQuerySet(QuerySet)` + rebind helper

Mirror `LateralQuerySet` exactly: `_dst_single_parent_spec` class attr defaulting None,
`_clone` carries it, `_fetch_all` populates `_result_cache` from
`_fetch_single_parent_rows(self)` when non-None, then ALWAYS `super()._fetch_all()`.
`as_single_parent_queryset(queryset, spec)` mirrors `_as_lateral_queryset` (722-732):
`clone = queryset._chain(); clone.__class__ = ...; clone._dst_single_parent_spec = spec`.

### 3d. Fetch-time recognizer `_fetch_single_parent_rows(queryset) -> list | None`

Refuse (`return None`, windowed body runs) unless:
1. spec present; 2. `single_parent_fast_path_setting()` is True (lazy import from `..conf`);
3. `queryset._iterable_class is ModelIterable`;
4. query not mutated: refuse `query.is_sliced / distinct / select_for_update / combinator /
   extra / extra_tables / group_by is not None` (subset of lateral's gates 521-529; do NOT
   refuse select_related — the pristine clone carries the same one);
5. `tuple(query.order_by) == tuple(spec.order_by)` and `query.standard_ordering`;
6. `set(query.annotations) == {WINDOW_ROW_NUMBER}` (eligible shape annotates ONLY rn);
7. WHERE walk (structural twin of `_extract_parent_ids` minus keyset): root not negated,
   connector AND; per child `_is_window_qual` -> skip, else `_parent_in_values(child,
   column=spec.parent_link_column, table=spec.parent_link_table)` — accept at most one;
   anything else -> None;
8. dedup parent ids copying `_deduplicate_parent_ids` semantics (469-478, incl. the
   TypeError arm for unhashables); **`len(unique) != 1` -> None** (zero parents included —
   let the windowed body return its trivially-empty result).

Execute:
```python
(pid,) = unique
child_qs = spec.pristine_child_queryset.using(queryset.db)  # honor prefetch/router alias
rows = list(child_qs.filter(**{spec.parent_link_attname: pid})
            .order_by(*spec.order_by)[: spec.fetch_limit])
for index, row in enumerate(rows):
    setattr(row, WINDOW_ROW_NUMBER, index + 1)
logger.debug(...)  # one line, %s-style args, mirroring optimizer logger idiom
return rows
```
Never set `_dst_total_count` (its ABSENCE is what makes the consumer's probe re-inference
work). Row contract satisfied: rn 1-based page-relative == absolute (offset 0), forward
order, probe row is the limit+1th (rn = limit+1 > upper bound, split off by
`split_window_rows`), cursors `rn - 1` byte-identical to the windowed body.

## Step 4 — hook into `WindowedPrefetchStrategy.plan` (nested_fetch.py:228-230)

```python
def plan(self, request, plan):
    # Lazy import: single_parent_fetch imports lateral_fetch which imports this module.
    from .single_parent_fetch import as_single_parent_queryset, single_parent_spec

    spec = single_parent_spec(request)
    if spec is None:
        return attach_windowed_prefetch(request, plan)
    return attach_windowed_prefetch(
        request, plan, wrap=lambda queryset: as_single_parent_queryset(queryset, spec)
    )
```

Do NOT touch `LateralPrefetchStrategy`. Auto-strategy nuance (verified — word the
docstring accurately): `LateralPrefetchStrategy.plan` falls back to `WINDOWED_STRATEGY.plan`
only when `_build_lateral_spec` returns None (lateral_fetch.py:708), and for a CLEAN
eligible shape the lateral spec succeeds — so under `auto`/`lateral` the fast path engages
only in the narrow residue where lateral refuses at plan time but the single-parent spec
accepts (e.g. a child queryset carrying `select_related`, which lateral refuses at 763-771
but this path allows). The fast path is effectively a `"windowed"`-strategy feature. A
lateral single-parent variant is explicitly OUT of scope v1. Update the
`WindowedPrefetchStrategy` docstring to mention the runtime-only wrap.

## Step 5 — tests (live tier FIRST, per examples/fakeshop/test_query/README.md coverage rule)

**Any line earnable by a real /graphql/ query MUST be earned in the live tier.** Package-tier
tests cover only the refusal branches genuinely unreachable over HTTP.

### 5a. Live tier: new `examples/fakeshop/test_query/test_single_parent_fastpath_api.py`

Model on `test_library_api.py`: module seed helpers, `@pytest.mark.django_db`,
`post_graphql` from `../graphql_client.py`, `django.test.utils.CaptureQueriesContext
(connection)`. SQL-shape assertion idiom: scan `ctx.captured_queries` for the child-table
query; assert `"OVER ("` presence/absence.

**Test substrate (dry-run VERIFIED — do it exactly this way).** There is NO
`get_queryset`-free, cursor-free, DIRECT_FK, Relay-Node child anywhere in fakeshop:
nested connections require a Relay-Node child (`list_field.py:121`, live-pinned by
`test_book_loans_relation_stays_list_only`, test_library_api.py:4034-4050), and every
Relay-Node DIRECT_FK child type carries a visibility `get_queryset` by design
(`BookType` excludes `circulation_status="repair"` for non-staff, library schema
~113-121; products' `ItemType` filters `is_private`; `IssueType` is additionally
keyset-cursored via `cursor_field=("-number","id")` ~337 + embargo filter ~320-325).
Do NOT try to add a field — it cannot produce a clean substrate. Instead:

1. **Run the offset happy-path tests as STAFF against `ShelfType.booksConnection`**
   (offset cursors, DIRECT_FK, Relay-Node child; currently untested so no perturbation).
   As staff, `BookType.get_queryset` returns the queryset unchanged — clean single-parent
   window — fast path engages. Staff bracket idiom: `_post_graphql_as_staff`
   (test_library_api.py:752-768; `create_user(..., is_staff=True)` +
   `with client.login(staff):`). Do NOT add a new model/migration — out of scope; the
   staff bracket earns the same lines.
2. **Keyset-first-page engagement on `periodical.issuesConnection`**: first page (no
   `after:`) has `keyset_seek is None`, so the fast path engages — as staff only.
3. **The anonymous run of either connection is the visibility-degradation test**: the
   non-staff `get_queryset` filter lands as an extra WHERE qual on the child queryset at
   fetch time -> recognizer refusal -> `OVER (` kept, data still correct.

Tests (all offset-connection tests drive `shelf.booksConnection` AS STAFF unless noted):
- `test_single_parent_first_page_skips_window_over_http` — root filtered to ONE parent,
  `booksConnection(first: 2) { edges { node {...} cursor } }` (no pageInfo): data +
  cursors correct, NO `OVER (` in any child query.
- `test_single_parent_probe_shape_overfetches_without_window_over_http` — adds
  `pageInfo { hasNextPage }`, seed limit+1 children: hasNextPage true, page length ==
  limit, no `OVER (`, child SQL contains `LIMIT 3` (the probe overfetch on the fast path).
- `test_single_parent_total_count_keeps_window_over_http` — selects `totalCount`: correct
  count AND `OVER (` present.
- `test_multi_parent_keeps_window_over_http` — two parents, same nested `first:`:
  `OVER (` present, per-parent pages correct.
- `test_single_parent_offset_page_keeps_window_over_http` — `after:` offset cursor:
  `OVER (` present.
- `test_single_parent_keyset_first_page_skips_window_as_staff_over_http` —
  `issuesConnection(first: N)` as staff, no `after:`: fast path engages (no `OVER (`),
  keyset cursors correct (the consumer derives them from row column values, not rn —
  verified).
- `test_visibility_filtered_child_keeps_window_over_http` — same query ANONYMOUS: the
  non-staff `get_queryset` filter is an unrecognized WHERE qual -> recognizer refusal,
  `OVER (` present, data still correct (degradation, never breakage).
- `test_single_parent_empty_children_over_http` — one parent, zero children: empty edges,
  hasNextPage false, no `OVER (`.
- `test_fast_path_disabled_by_setting_over_http` — override
  `DJANGO_STRAWBERRY_FRAMEWORK={..., "SINGLE_PARENT_FAST_PATH": False}` (copy the existing
  dict and update — check how sibling tests override this settings dict; the flag is
  fetch-time so no schema rebuild is needed): single-parent shape uses `OVER (`.
- M2M shape (a library M2M relation, single parent): `OVER (` present (through-table
  exclusion observable live).

### 5b. Package tier: new `tests/optimizer/test_single_parent_fetch.py`

Mirror `test_nested_fetch.py` / `test_lateral_fetch.py` style (check `_builders.py` for
request builders to reuse):
- Eligibility matrix over `single_parent_spec`: accepts plain first page; None for each of
  with_total_count / reverse / offset>0 / limit None or 0 / keyset_seek / custom QuerySet
  subclass / THROUGH_TABLE join; `fetch_limit == limit+1` iff probe.
- Recognizer refusal matrix over `_fetch_single_parent_rows` (build via the strategy,
  mutate the queryset, assert None + that the windowed body still returns correct rows):
  missing spec; setting off; `.values()` iterable; sliced/distinct/extra mutation; wrong
  order_by; extra annotation; negated/OR where root; second unrecognized qual; two IN
  quals; expression rhs; zero parents; two parents; duplicate single id (ACCEPTED — dedup);
  unhashable ids (TypeError arm).
- Row synthesis on SQLite: rn 1..N, no `_dst_total_count`, forward order; nested
  `prefetch_related` on the child body still populates (two-level prefetch assertion);
  `_clone` carries the spec.
- `_parent_in_values` keyword-signature units (update any existing direct-call tests).

### 5c. PG parity: `tests/test_lateral_pg_parity.py`

ONE test: with the windowed strategy forced on the PG alias, the single-parent shape
returns rows/cursors/pageInfo identical to the lateral strategy's output for the same
query (reuse `_assert_parity` / `build_strategy_schema` helpers). Comment: under
strategy=lateral the fast path never engages (wrap is windowed-branch-only).

## Verification (final gate)

1. `uv run ruff format .` + `uv run ruff check --fix .` (and run pre-commit checks per the
   build-final-gate memory — ASCII-only + stricter-ruff slip through ruff alone).
2. Run the new package-tier file, then the new live-tier file, then the FULL suite with
   coverage — `fail_under = 100` must hold; audit every new line in
   `single_parent_fetch.py` / `conf.py` / `nested_fetch.py` / `lateral_fetch.py` against
   the tier map above (live tier earns: spec construction, wrap, recognizer happy path,
   probe, empty page, setting gate both ways, logger line; package tier earns each refusal
   `return None` and the TypeError dedup arm).
3. Sanity: `test_lateral_fetch.py` and `test_nested_fetch.py` still green after the
   `_parent_in_values` signature change; `test_lateral_pg_parity.py` runs only under the PG
   env (mirror its existing skip conditions).
4. NO commit — leave the working tree dirty for the maintainer.
