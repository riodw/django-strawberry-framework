# DRY review: `django_strawberry_framework/optimizer/nested_fetch.py`

Status: verified

## System trace

The target owns the **pluggable nested-connection fetch-strategy seam**: the
strategy-independent request contract (`NestedConnectionRequest`), the
`NestedConnectionStrategy` protocol, the shared windowed correctness floor
(`attach_windowed_prefetch` → `plans.apply_window_pagination` + `to_attr`
`Prefetch`), built-in strategy identity (`WINDOWED_STRATEGY` /
`AUTO_STRATEGY` + lazy `_builtin_strategies` registry), construction-time
selection (`resolve_strategy`), and the per-execution ContextVar
(`_active_strategy` / `active_strategy`) that the walker reaches without
importing `extension.py`.

Owned responsibility:

- **Request boundary** — everything a strategy may consume after Decision-6
  fallbacks are ruled out; `__post_init__` enforces probe/count mutual
  exclusion via shared `utils.connections.assert_window_fetch_mode_for`.
- **Windowability gate** — `unwindowable_child_queryset_reason` classifies
  consumer-hook queryset shapes no backend can window (sliced, locking,
  combined, distinct, non-model iterable); planner-only caller, seam-owned
  precondition of `NestedConnectionRequest`.
- **Floor every backend shares** — `attach_windowed_prefetch` (optional
  `wrap=` for lateral's `LateralQuerySet` rebind); `WindowedPrefetchStrategy`
  is the bare call.
- **Auto identity** — `AutoNestedConnectionStrategy` keeps `name="auto"` and
  delegates planning to `LATERAL_STRATEGY` so cached plans stay backend-neutral
  while fetch-time alias selects lateral vs windowed ORM body.
- **Registry / ContextVar** — lazy import of lateral breaks the intentional
  cycle; extension publishes the instance strategy in `on_execute`.

Connected behavior examined (evidence only where noted):

- `optimizer/lateral_fetch.py` — second backend; consumes
  `NestedConnectionRequest`, `attach_windowed_prefetch`, `WINDOWED_STRATEGY`
  downgrade (just verified sibling; left untouched).
- `optimizer/nested_planner.py` — sole production caller of
  `unwindowable_child_queryset_reason`, `NestedConnectionRequest`,
  `active_strategy`; isolates candidate plans and merges only on `True`
  (evidence; open plan item).
- `optimizer/plans.py` — `apply_window_pagination` / `append_prefetch_unique`
  (window renderer + Prefetch dedupe owners).
- `optimizer/extension.py` — `resolve_strategy` at construction;
  `_active_strategy` publish/reset in `on_execute`.
- `optimizer/join_taxonomy.py` — `RelationJoinDescriptor` on the request
  (read-only).
- `utils/connections.py` — `assert_window_fetch_mode_for` /
  `window_range_plan` (already singular).
- `conf.py::nested_connection_strategy_setting` — name string only;
  validation stays in `resolve_strategy`.
- `connection.py::_resolve_from_window` — consumer of the `to_attr` row
  contract (unchanged by strategy choice).
- Pins: `tests/optimizer/test_nested_fetch.py`, walker strategy
  accept/refuse/raise + unwindowable matrix in `tests/optimizer/test_walker.py`,
  builders in `tests/optimizer/_builders.py`, lateral/keyset consumers,
  `examples/fakeshop/strategy_schemas.py`.
- Baseline
  `git diff 7ac2fa0a209cf5d5cc05a269ef63e3c18b55895f -- …/nested_fetch.py`
  was empty. Concurrent dirty optimizer / docs / test paths left untouched.

## Verification

Searches:

- `unwindowable_child_queryset_reason` / `NestedConnectionRequest` /
  `attach_windowed_prefetch` / `resolve_strategy` / `active_strategy` /
  `WINDOWED_STRATEGY` / `AUTO_STRATEGY` / `_active_strategy` /
  `apply_window_pagination` / `assert_window_fetch_mode_for` /
  `query.is_sliced` / `select_for_update` / `combinator` / `_iterable_class`
  package-wide.
- Optional
  `export_dry_review.py audit --target …/nested_fetch.py --stdout`: 13
  definitions; reverse imports match extension / nested_planner / lateral /
  tests. No exact-duplicate bodies against other modules. Static similarity
  only oriented.

Disproved / rejected candidates:

1. **Share queryset-flag checks with `lateral_fetch._recognize_lateral_fetch` /
   `_fetch_lateral_rows`.** Overlap on sliced / distinct / locking /
   combinator / non-`ModelIterable` is real syntax, not one responsibility.
   `unwindowable_*` is **plan-time Decision-6** (leave selection fully
   unplanned, reason strings for telemetry); lateral checks are **fetch-time
   recognition** (return `None` → execute windowed body) plus many extra
   predicates (`select_related`, `extra_tables`, `group_by`, order/select/
   WHERE residue). A shared helper would need mode flags or dual return
   shapes and would couple refuse-to-plan with degrade-to-windowed.
   Rejected.

2. **Move `unwindowable_child_queryset_reason` into `nested_planner`.** Only
   one caller, but the gate is the seam precondition of
   `NestedConnectionRequest` ("built only AFTER … fallback shapes ruled
   out"). Relocating would split the strategy contract from its safety
   vocabulary. Rejected (wrong-direction ownership move, not consolidation).

3. **Collapse `AUTO_STRATEGY` into `resolve_strategy("auto") → LATERAL_STRATEGY`.**
   Loses stable `name="auto"` identity and cache/telemetry distinction while
   planning already delegates to lateral. Rejected.

4. **Deduplicate `assert_window_fetch_mode_for` between
   `NestedConnectionRequest` and `LateralWindowSpec`.** Rule already lives
   once in `utils.connections`; each dataclass validates at its own boundary
   (strategy request vs frozen SQL spec). Twin call sites are intentional.
   Rejected.

5. **Abstract `NestedConnectionRequest` window fields into
   `LateralWindowSpec` (or a shared window carrier).** Spec must freeze a
   self-contained SQL projection that survives queryset clones without
   holding the full request; different lifecycle. Rejected.

6. **Touch `lateral_fetch` / `nested_planner` / `plans` / `extension` in this
   item.** Prior consolidations (`attach_windowed_prefetch`, shared fetch-mode
   assert, lateral seek owner under `keyset.py`) already put shared rules at
   their owners. No second seam owner to establish here. Deferred to those
   open plan items / already-verified siblings.

Focused experiments: none required — contracts are pinned by
`test_nested_fetch.py` (registry, resolve, ContextVar, windowed floor,
probe/count reject, unwindowable matrix) and walker integration under both
strategy names. Item-scoped production diff remains empty.

## Opportunities

None — the seam already is the single owner of strategy selection, the
request contract, the windowed floor, and the plan-time unwindowable
vocabulary; remaining syntactic overlaps with lateral fetch-time guards and
`LateralWindowSpec` construction checks are intentionally distinct failure
postures that must not share one helper.

## Judgment

Zero-edit. `nested_fetch.py` is the Prisma-style strategy interface the rest
of the optimizer was shaped around; cross-backend duplication that used to
live here (window argument threading, fetch-mode exclusion) already moved to
`attach_windowed_prefetch` and `assert_window_fetch_mode_for`. Further
helpers would obscure Decision-6 vs lateral-degrade ownership. Ready for
Worker 2.

## Independent verification (Worker 2)

Scoped diff vs `ITEM_BASELINE`
`7ac2fa0a209cf5d5cc05a269ef63e3c18b55895f` for
`django_strawberry_framework/optimizer/nested_fetch.py` is empty (confirmed).

Re-traced ownership: request contract + `__post_init__` fetch-mode assert,
`unwindowable_child_queryset_reason` Decision-6 gate, `attach_windowed_prefetch`
floor, strategy protocol / windowed + auto identities, lazy registry +
`resolve_strategy`, ContextVar publish seam. Sole production planner caller is
`nested_planner.plan_connection_relation`; sole floor consumers are
`WindowedPrefetchStrategy` and `LateralPrefetchStrategy` (via `wrap=`);
extension owns construction-time resolve and `on_execute` publish. No parallel
registry, bypass, or second selection path found under package search.

Challenged rejected candidates (all hold):

1. **Queryset-flag overlap with
   `lateral_fetch._recognize_lateral_fetch` / `_fetch_lateral_rows`.** Overlap on
   sliced / distinct / locking / combinator / non-`ModelIterable` is real
   syntax. Contracts still diverge: plan-time returns a reason string and
   leaves the selection fully unplanned; fetch-time returns `None` and
   executes the already-attached windowed body. Lateral's set is strictly
   larger (`select_related`, `extra_tables`, `group_by`, order/select/WHERE
   residue). Shared helper would need mode flags or dual return shapes and
   would couple refuse-to-plan with degrade-to-windowed. Stand.

2. **Move `unwindowable_*` into `nested_planner`.** One caller, but the
   docstring + `NestedConnectionRequest` construction contract treat the gate
   as the seam precondition ("built only AFTER … fallback shapes ruled out").
   Relocating splits vocabulary from the strategy boundary. Stand.

3. **Collapse `AUTO_STRATEGY` into `LATERAL_STRATEGY`.** Tests pin
   `resolve_strategy("auto") is AUTO_STRATEGY` with stable `name="auto"`;
   planning already delegates. Identity is load-bearing for cache/telemetry.
   Stand.

4. **Twin `assert_window_fetch_mode_for` call sites.** Rule lives once in
   `utils.connections`; request vs frozen SQL-spec are distinct boundaries that
   must each fail loudly. Stand.

5. **Shared window carrier for request ↔ `LateralWindowSpec`.** Spec freezes a
   clone-surviving SQL projection; window fields are data flow into that
   freeze, not a second policy owner. Stand.

Missed consolidations searched and not found: package-wide flag-check sites
beyond the intentional Decision-6 / lateral-recognition / top-level
`connection.py` sliced-source GraphQLError guard (different lifecycle);
`apply_window_pagination` / `append_prefetch_unique` already owned under
`plans.py`; conf only supplies the name string; `__init__.py` correctly does
not re-export the internal seam; test builders already share
`tests/optimizer/_builders.py`.

Verdict: zero-edit stands. No revision-needed findings.
