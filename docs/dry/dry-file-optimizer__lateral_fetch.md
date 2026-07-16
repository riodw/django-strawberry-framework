# DRY review: `django_strawberry_framework/optimizer/lateral_fetch.py`

Status: verified

## System trace

The target owns the **Postgres `CROSS JOIN LATERAL` nested-connection fetch
backend**: plan-time capability detection (`LateralPrefetchStrategy` /
`_build_lateral_spec` / `LateralWindowSpec`), fetch-time recognition and
fallback to the windowed ORM body (`LateralQuerySet` / `_fetch_lateral_rows` /
`_extract_parent_ids`), and raw-SQL rendering (`build_lateral_sql`) that is a
byte-mirror of `plans.py::apply_window_pagination` for the `to_attr` contract
consumed by `connection.py::_resolve_from_window`.

Owned responsibility:

- lateral-capable shapes only (plain `QuerySet`, local concrete order columns,
  no child filters/annotations/`select_related`, scalar or typed-VALUES parent
  binds); everything else downgrades inside `plan` to `WINDOWED_STRATEGY`;
- counted keyset seeks downgrade (qualify-wrapped whole-partition scan already
  owns that cost; no second marker/count dialect);
- count-free keyset seeks render inside the lateral branch via the shared
  seek owner (`keyset.keyset_seek_sql`);
- fetch-time safety: unrecognized WHERE residue / vendor / iterable falls
  through to superclass `_fetch_all` (performance downgrade, never wrong rows);
- `_keyset_seek_quals_match` structurally verifies the windowed-floor seek
  residue so lateral SQL never drops or double-applies a non-seek filter.

Connected behavior examined:

- `keyset.py` — codec, `KeysetSeek` carrier, direction rule, seek plan, ORM
  `Q` and raw-SQL seek renderers (this pass completed the seek-structure owner);
- `utils/connections.py::window_range_plan` / `assert_window_fetch_mode_for` —
  shared range/marker/probe decisions (already shared before this pass);
- `optimizer/nested_fetch.py` — strategy seam, `attach_windowed_prefetch`
  floor, `NestedConnectionRequest` (still open as its own plan item; left
  untouched);
- `optimizer/plans.py::apply_window_pagination` — ORM window renderer twin;
- `optimizer/join_taxonomy.py` — `LateralJoinShape` / link fields (read-only);
- `connection.py::_resolve_from_window` — consumer of window attrs;
- Pins: `tests/optimizer/test_lateral_fetch.py`, `tests/test_keyset.py`
  (lateral seek SQL + quals match), `tests/test_lateral_pg_parity.py`,
  live keyset HTTP in `examples/fakeshop/test_query/test_keyset_api.py`.
- Baseline
  `git diff 381a2274d22a5138a9177558be5132a88a9f27b0 -- …/lateral_fetch.py`
  was empty before this pass. Concurrent dirty optimizer / docs / test paths
  left untouched.

## Verification

Searches:

- `keyset_seek_q` / `_keyset_seek_sql` / `keyset_seek_greater` /
  `_keyset_seek_quals_match` / `window_range_plan` / `apply_window_pagination` /
  `_order_columns` / `_select_columns` / `_concrete_order_columns` /
  `order_entry_name_and_direction` / `deferred_loading_of` — package-wide.
- Optional `export_dry_review.py audit --target …/lateral_fetch.py`: 21
  definitions; reverse imports from nested_fetch / tests / pg-parity. Static
  similarity only oriented; behavior checked against tests and live keyset API.

Disproved / rejected candidates:

1. **Merge ORM `Q` seek and raw-SQL seek into one backend.** Re-evaluated
   fresh. Rejected: the windowed floor needs portable ORM `Q` (SQLite tests,
   non-Postgres `.using()`, counted-keyset qualify path); the lateral branch
   needs parameterized SQL with a uniform-direction **row-value** shortcut
   Django `Q` cannot emit. Backends stay separate. What *was* duplicated was
   the predicate STRUCTURE (directions + leading-bound OR-expansion), not the
   rendering target — consolidated below without merging backends.

2. **Unify `_order_columns` with `keyset.split_order_ref` /
   `nested_planner._concrete_order_columns`.** Disproved: different failure
   postures (lateral returns `None` to downgrade; keyset raises
   `ConfigurationError`; nested planner skips unresolvable names for
   `.only()` projection). Parser already shared via
   `plans.order_entry_name_and_direction`.

3. **Share `_select_columns` further / merge with scalar-only projection.**
   Rejected: already reads `plans.deferred_loading_of`; scalar-only projection
   is a different contract (minimal pk/connector/order mask at plan time).

4. **Abstract window-range SQL vs `apply_window_pagination` `Q` rendering.**
   Rejected: decisions already live once in `window_range_plan`; remaining
   rendering is thin and dialect-shaped (including lateral's in-branch
   `LIMIT` for `plain_first_page`). Same pattern as seek backends: shared
   plan, separate renderers.

5. **Touch `nested_fetch.py` in this item.** Deferred: still an open plan
   item; lateral already consumes `attach_windowed_prefetch` /
   `NestedConnectionRequest` correctly. No second seam owner to establish here.

6. **Reverse `keyset_seek_greater` consolidation.** Explicitly out of scope
   (and still correct): direction rule stays in `keyset.py`.

Focused verification (not the full suite):

```text
uv run pytest tests/test_keyset.py::test_build_keyset_seek_plan_mixed_and_uniform \
  tests/test_keyset.py::test_keyset_seek_sql_uniform_row_value_and_mixed_or_expansion \
  tests/test_keyset.py::test_keyset_seek_greater_direction_table \
  tests/test_keyset.py::test_keyset_seek_q_mixed_directions_both_ways \
  tests/test_keyset.py::test_keyset_seek_carrier_q_matches_builder \
  tests/test_keyset.py::test_lateral_count_free_keyset_renders_in_branch_seek \
  tests/test_keyset.py::test_lateral_keyset_prepares_values_through_model_fields \
  tests/test_keyset.py::test_lateral_uniform_keyset_renders_row_value_seek \
  tests/test_keyset.py::test_lateral_single_column_keyset_renders_scalar_seek \
  tests/test_keyset.py::test_lateral_counted_keyset_downgrades_to_windowed -q
```

10 passed (coverage gate failed only because the invocation was partial).

## Opportunities

### 1. Shared keyset seek plan + SQL renderer under `keyset.py`

- **Repeated responsibility:** the count-free keyset seek predicate
  (per-column direction via `keyset_seek_greater`, redundant leading inclusive
  bound, OR-expansion arms; SQL row-value shortcut when directions are
  uniform) was encoded twice — once as ORM `Q` in `keyset_seek_q`, once as
  raw SQL in `lateral_fetch._keyset_seek_sql` — after the direction bit alone
  had already been unified.
- **Sites:** `keyset.py::keyset_seek_q` (and `KeysetSeek.q`);
  `optimizer/lateral_fetch.py::_keyset_seek_sql` (caller of the new SQL
  renderer); `_keyset_seek_quals_match` (consumes the shared plan for
  direction/value facts while still verifying Django's WHERE tree shape).
- **Evidence:** both dialects must select the identical post-cursor row set
  (cross-strategy byte-parity / index-seek contract). Mixed-direction SQL
  text in `test_lateral_count_free_keyset_renders_in_branch_seek` matches the
  ORM OR-expansion shape; uniform SQL uses row-value as a rendering
  optimization of the same plan. Changing the leading-bound or arm structure
  without both sites would silently diverge.
- **Owner:** `keyset.py` — `KeysetSeekPlan` / `build_keyset_seek_plan` own
  structure; `keyset_seek_q` and `keyset_seek_sql` are the two renderers;
  `KeysetSeek.plan` exposes the carrier. Lateral keeps only the
  field-adapter + quoted child-column bind step (`_keyset_seek_sql` as a thin
  adapter) and the fetch-time WHERE verifier.
- **Consolidation:** implemented this pass (see Implementation).
- **Proof:** new unit pins
  `test_build_keyset_seek_plan_mixed_and_uniform`,
  `test_keyset_seek_sql_uniform_row_value_and_mixed_or_expansion`, plus
  existing lateral SQL-shape / quals-match / ORM mixed-direction tests.
  End-to-end behavior already earned live in
  `examples/fakeshop/test_query/test_keyset_api.py` (no new live pin — internal
  ownership move, observable seek semantics unchanged).
- **Risks / non-goals:** do not force ORM onto row-value SQL; do not force
  lateral off the row-value shortcut; do not merge counted-keyset lateral
  (still intentionally windowed-only); do not move `_keyset_seek_quals_match`
  into keyset (it recognizes Django prefetch WHERE residue, a lateral
  fetch-time concern).

## Judgment

The lateral backend is already well-factored against shared owners for window
range decisions, fetch-mode assertion, deferred loading, order-entry parsing,
and the windowed prefetch floor. The one remaining dual encoding of a single
rule was the keyset seek **structure** across ORM and raw-SQL dialects —
direction had been unified earlier; this pass finishes that ownership under
`keyset.py` without collapsing the intentionally separate backends. Ready for
Worker 2.

## Implementation (Worker 1)

Owner chosen: `django_strawberry_framework/keyset.py` for seek plan + both
renderers; `lateral_fetch.py` retains lateral bind/verify only.

Migrated:

- Added `KeysetSeekPlan`, `build_keyset_seek_plan`, `keyset_seek_sql`;
  `keyset_seek_q` now renders from the shared plan; `KeysetSeek.plan` added.
- `lateral_fetch._keyset_seek_sql` reduced to prepare-values + quote refs +
  `keyset_seek_sql`; `_keyset_seek_quals_match` reads `seek.plan()`.
- Module docstring in `keyset.py` records "one seek plan, two renderers".
- Permanent tests in `tests/test_keyset.py` for plan facts and SQL shapes;
  existing lateral seek pins still assert end-to-end SQL text/params.

Behavior kept separate: ORM always OR-expansion; SQL row-value when uniform;
lateral fetch-time quals matcher; counted keyset → windowed downgrade;
`nested_fetch.py` untouched.

Validation: ruff format + ruff check --fix + trailing-comma fixer on edited
paths; focused seek tests 10/10 passed.

Changelog: no — internal ownership consolidation, no public API change worth
a release note without maintainer authorization.

Ready for W2: yes.

## Independent verification (Worker 2)

Re-traced from `lateral_fetch.py` through `keyset.py`, `plans.py::apply_window_pagination`
(ORM `keyset_seek.q()`), `window_range_plan`, and the lateral plan/fetch path. Item-scoped
diff vs `381a2274d22a5138a9177558be5132a88a9f27b0` is exactly the claimed migration
(`keyset.py` + thin `lateral_fetch` adapter + `tests/test_keyset.py` pins).

**Seek structure belongs in `keyset.py`.** Challenged putting structure under the optimizer
or leaving SQL text in `lateral_fetch`: the cursor/seek domain already owns direction
(`keyset_seek_greater`), the ORM renderer (`keyset_seek_q`), and the carrier
(`KeysetSeek`); the duplicated knowledge was the leading-bound + OR-expansion plan both
dialects must share for cross-strategy row-set parity. `KeysetSeekPlan` /
`build_keyset_seek_plan` / `keyset_seek_sql` complete that ownership without inverting
lateral → keyset dependence.

**ORM Q vs SQL backends stay separate.** `keyset_seek_q` always renders portable
OR-expansion `Q` (windowed floor / SQLite / non-Postgres `.using()` /
counted-keyset qualify path). `keyset_seek_sql` may emit row-value when
`plan.uniform`, else the same OR-expansion shape. No mode-flagged mega-renderer;
backends remain distinct renderers of one plan.

**Migration / thin adapter.** `lateral_fetch._keyset_seek_sql` is prepare-values +
quote child refs + `seek.plan(values)` + `keyset_seek_sql`. Plan-time
`seek_signature == order_columns` still guarantees column/value alignment.
`_keyset_seek_quals_match` correctly stays here: it recognizes Django prefetch WHERE
residue of the ORM seek tree, not abstract seek structure. Lateral no longer imports
`keyset_seek_greater` directly.

**Rejected candidates (disposed).**

1. Merge Q + SQL backends — disproved: Django `Q` cannot emit row-value; portable `Q`
   remains required for the windowed floor.
2. Unify `_order_columns` with `split_order_ref` / `_concrete_order_columns` — different
   failure postures (downgrade `None` vs `ConfigurationError` vs skip-for-`.only()`);
   string parse already shared via `order_entry_name_and_direction`.
3. Further share `_select_columns` / scalar-only projection — already uses
   `deferred_loading_of`; scalar-only is a different contract.
4. Abstract window-range SQL vs `apply_window_pagination` — decisions already once in
   `window_range_plan`; dialect renderers remain thin.
5. Touch `nested_fetch.py` — correctly deferred; still its own open plan item.
6. Reverse `keyset_seek_greater` — out of scope and still correct: one definition in
   `keyset.py`, only called from `build_keyset_seek_plan` (and pinned by the direction
   table test).

**`keyset_seek_greater` owned once.** Package-wide: sole definition in `keyset.py`; no
`_keyset_seek_greater` remnant; consumers go through the plan.

**Tests.** Re-ran the artifact's 10 focused pins (`--no-cov`): 10 passed, including plan
facts, SQL row-value/mixed shapes, ORM mixed directions, carrier `.plan()`, and lateral
in-branch seek / prepare / downgrade pins.

**Missed opportunities.** None material. Private `_keyset_seek_sql` naming shadows the
public renderer but is a local adapter, not a second structure owner. Arm-construction
loops in each renderer are dialect rendering from shared plan facts, not a remaining
dual encoding of the rule.

**Blockers.** None.

Verdict: verified; plan item checked.
