# Review: `django_strawberry_framework/utils/connections.py`

Status: verified

NEW 0.0.9 file (no prior artifact). Shared cycle-safe contract home: the slice-window
derivation (`ConnectionWindowBounds` / `derive_connection_window_bounds`, the cursor-parity
invariant's plan/resolve agreement) and the `CONNECTION_SIDECAR_KWARGS` family. Reviewed
against BOTH consumers — the plan-time path (`optimizer/walker.py::_connection_window_slice`
-> `_plan_connection_relation` -> `optimizer/plans.py::apply_window_pagination`) and the
resolve-time path (`connection.py::_consume_window` -> `_resolve_from_window`) — and against
`strawberry/relay/utils.py::SliceMetadata.from_arguments` (the engine both branches share)
and spec-033 Decision 4 / Decision 5.

## DRY analysis

- Defer-with-trigger: `connection.py` re-spells `kwargs.get("filter")` / `kwargs.get("order_by")`
  nowhere now (it routes through `connection_sidecar_inputs_from_kwargs` at five sites and
  `has_connection_sidecar_input` at `connection.py:834,1119`; the walker uses
  `has_connection_sidecar_kwargs` at `optimizer/walker.py:1192`). The three-helper sidecar
  ladder (`connection_sidecar_inputs_from_kwargs` -> `has_connection_sidecar_input` ->
  `has_connection_sidecar_kwargs`) is correctly single-sourced. No act-now consolidation. The
  one standing item is the `CONNECTION_SIDECAR_KWARGS` tuple itself (see Low "Built-but-unconsumed
  tuple constant"): it is the documented future-extension anchor but has no production reader.
  **Defer until a third sidecar (e.g. the reserved `search:`, GLOSSARY:298 `0.1.2`) lands** —
  at that point either route a presence-check loop through the tuple, or delete the tuple if the
  per-name constants still suffice. Quote-trigger: "a future sidecar (e.g. `search`) is then a
  one-line edit here" (connections.py module docstring, line 19-20).

## High:

### `after` + `last` slips into the reverse branch with a non-zero offset and breaks `pageInfo` parity

`derive_connection_window_bounds` line 124:

```django_strawberry_framework/utils/connections.py:124:125
reverse = isinstance(last, int) and not isinstance(first, int) and before is None
limit = last if reverse else slice_meta.expected
```

The `reverse` predicate guards against `first` and `before`, but **not `after`**. For an
`after: c, last: N` query (a valid, unguarded Relay combination — only `first`+`last` is
mutually exclusive, enforced at resolve time by `connection.py::_guard_first_and_last`), this
returns `reverse=True` with a **non-zero** `offset` (`slice_meta.start = int(c)+1`) and
`limit = last`. The walker then plans it through the reverse branch of
`apply_window_pagination` (`optimizer/plans.py:640-652`): `_dst_row_number__gt offset` ANDed
with `_dst_row_number_reversed__lte limit`. The reversed row number partitions over the
**whole** parent partition, not the `after`-filtered subset, so when the after-set is smaller
than (or equal to) `last`, the window returns the right ROWS but `_resolve_from_window`'s page
flags (`connection.py:249`, `has_previous_page = first_rn > 1`) read the absolute forward row
number and report a previous page that the per-parent fallback does not.

Verified divergence (forward rn = reversed rn complement over the partition; fast-path vs the
inherited `ListConnection.resolve_connection` `edges[-last:]` + `has_previous_page =
len(edges) != original_len` tail):

| partition | args | window rows | fallback rows | fast-path prev/next | fallback prev/next |
|---|---|---|---|---|---|
| 5 rows | `after:3, last:3` | rn 5 | rn 5 | **True**, False | **False**, False |
| 5 rows | `after:1, last:3` | rn 3,4,5 | rn 3,4,5 | **True**, False | **False**, False |
| 6 rows | `after:4, last:3` | rn 6 | rn 6 | **True**, False | **False**, False |
| 10 rows | `after:6, last:3` | rn 8,9,10 | rn 8,9,10 | **True**, False | **False**, False |
| 10 rows | `after:2, last:3` | rn 8,9,10 | rn 8,9,10 | True, False | True, False (matches) |

The rows match in every case, but `has_previous_page` diverges whenever the `after`-filtered
remainder is `<= last` rows. This is an optimizer-on vs optimizer-off `pageInfo` correctness
split — precisely the cursor-parity invariant this module is the contract for (spec-033
Decision 4 / Decision 5). It is data-correctness, hence High.

Spec scope confirms `after + last` was never meant to take the reverse window: Decision 5
(spec-033 line 450) scopes the reversed-row-number branch to **`last`-only** backward
pagination, and line 582 states `before`/`last` combinations "the offset arithmetic cannot
push down fall back per-parent rather than approximating." The docstring here reasons only about
`before` (lines 109-114: "`last` set with no `first` and no `before` bound") and never mentions
`after` — the `after is None` clause was simply omitted from the predicate.

**Recommended change (root cause):** add `and after is None` to the `reverse` predicate so
`after + last` no longer maps onto the reversed window. With `after + last` and `reverse=False`,
`limit` becomes `slice_meta.expected` (`end - start`, which `SliceMetadata` computes as
`maxsize - start` -> `None` because `end == sys.maxsize`). A `None` limit with a non-zero offset
is NOT a clean forward window either — the forward branch applies only the `__gt offset` filter
and would return the entire after-tail uncapped, still not the `last N`. So the predicate fix
alone yields the wrong (uncapped) rows. The correct root-cause fix is to treat `after + last`
(and any `last`-with-offset shape the reversed window's whole-partition row numbering cannot
honor) as an **unwindowable fallback**: have `derive_connection_window_bounds` signal "do not
window" for this shape (e.g. raise the same `ValueError` family the walker already catches at
`optimizer/walker.py:1159` to leave the selection unplanned, or return a sentinel the walker
maps to UNPLANNED) so it falls back per-parent like the `before + last` shapes the spec already
defers. The resolver half (`connection.py`) then never sees a windowed wrapper for this shape
and runs the shipped pipeline, restoring byte-parity. Prefer the unplanned-fallback route over
trying to make the reversed window offset-aware — Decision 5 explicitly chose "window what
`SliceMetadata` expresses; fall back per-parent for the rest" as the monotonic-safe answer.

**Tests to add** (none exist today — every reverse-branch test in
`tests/utils/test_connections.py` uses pure `last`-only): a unit pin in
`tests/utils/test_connections.py` that `after + last` does NOT return `reverse=True` with a
non-zero offset (asserts the fallback signal), plus a wire-parity pin in
`tests/test_relay_connection.py` mirroring `test_fast_path_wire_parity_last_only` for
`after: c, last: N` on a partition whose after-remainder is `<= last`, asserting `pageInfo`
(`hasPreviousPage` in particular) matches the per-parent pipeline. A live products-graph
assertion (reverse-FK `itemsConnection(after: $c, last: $n)`) would earn the same line per the
AGENTS.md "prefer the example project" rule.

## Medium:

### Missing-branch test coverage for the offset-bearing `last` shapes

Tied to the High but recorded separately as a coverage gap: `tests/utils/test_connections.py`
covers `last`-only (reverse=True, offset=0), `first`-only, and `before + last` (reverse=False),
but never `after + last`, `after + first` cap interaction, or `first: 0` / `last: 0` boundary
windows. The `first: 0` / `last: 0` cases route to the resolver's ambiguous-empty fallback
(`limit == 0`, `connection.py:211`), so they are exercised indirectly, but the `after + last`
hole let the High ship unpinned. Recommend the unit + wire-parity pins named in the High;
they double as the regression fence for the predicate fix.

## Low:

### Built-but-unconsumed tuple constant `CONNECTION_SIDECAR_KWARGS`

`CONNECTION_SIDECAR_KWARGS` (line 43) is exported and named in the module docstring as the
sidecar-family anchor, but has **zero production readers** — the live code uses the individual
`CONNECTION_FILTER_KWARG` / `CONNECTION_ORDER_KWARG` (`connection.py:942,948,953,959`) and the
three predicate helpers; the tuple is referenced only by `tests/utils/test_connections.py:87`,
which asserts its value. Per the worker-1 calibration, a built-but-unconsumed surface is normally
Low, and here the module docstring frames the tuple explicitly as recorded forward-intent ("a
future sidecar ... is then a one-line edit here", lines 19-20) rather than a same-version
consumer promise, so it stays Low rather than promoting to Medium. No source change needed now;
see the DRY analysis defer-with-trigger for the retire-or-route decision when `search:` lands.
This is the kind of value-only-asserted-in-test constant that is fine to keep as the documented
extension point.

### Docstring reverse-branch rationale omits the `after` case

`derive_connection_window_bounds`'s docstring (lines 108-114) explains the reverse predicate by
reasoning about `first` and `before` only — "`before` + `last` resolves to a forward offset
window the forward branch already handles" — and never states what happens for `after + last`.
This is the same omission that produced the High in the code. Once the High's predicate/fallback
fix lands, the docstring should state explicitly that `after`-bearing `last` windows are NOT
reversed (they fall back per-parent), so a future reader does not re-introduce the bug by
"simplifying" the predicate. Comment-tier; defer to the comment pass after the High's logic fix.

## What looks solid

### DRY recap

- **Existing patterns reused.** The module is the single home for the cursor-parity window rule
  and the sidecar family — both consumers import back rather than re-spelling:
  `optimizer/walker.py:16-17` and `connection.py:71-75` both import
  `derive_connection_window_bounds` / the sidecar helpers, and the `max_results` is passed
  EXPLICITLY from each side (`optimizer/walker.py:1157` via `_relay_max_results_from_info`;
  `connection.py:300` from the resolver argument) so plan-time and resolve-time caps are one
  number. The window math defers entirely to `strawberry/relay/utils.py::SliceMetadata.from_arguments`
  (line 116-123) — no re-implementation of the start/end/expected arithmetic.
- **New helpers considered.** The sidecar ladder is already three thin helpers over one set of
  constants; no further extraction warranted until a third sidecar lands (DRY analysis).
- **Duplication risk in the current file.** The `reverse` / `limit` rule appears once here and
  is consumed by both branches; `apply_window_pagination` (plans.py) and `_resolve_from_window`
  (connection.py) read the SAME `(offset, limit, reverse)` triple — intentional single-source,
  not duplication. The plan-time-only int coercion is deliberately NOT folded in here (module
  docstring lines 22-27; `optimizer/walker.py::_coerce_pagination_int`) — correct, the resolver
  caller already receives `int` arguments from Strawberry.

### Other positives

- The `last`-only reverse rule is correct and well-pinned: `SliceMetadata` sets `end =
  sys.maxsize` -> `expected is None` for a `last`-only window, and the helper correctly returns
  `limit = last` (not `expected`) so the reversed `__lte` filter actually applies
  (`apply_window_pagination` plans.py:650-651). `test_last_only_window_limit_is_literal_last_not_expected`
  pins exactly this trap. Forward `first`, `after + first`, `before + last`, and the unbounded
  no-args window all derive correct bounds (verified against the engine).
- Cycle-safety is real and load-bearing: the module imports neither `connection.py` nor
  `optimizer/walker.py` (only `dataclasses`, `typing`, and `strawberry.relay.utils`), so both
  consumers import it freely — the stated reason for the file's existence holds.
- `ConnectionWindowBounds` is `frozen=True` — the triple cannot be mutated between plan and
  resolve, reinforcing the parity contract.
- Error-propagation contract is clean and asymmetric-by-design: `SliceMetadata` raises
  `ValueError` / `TypeError`, which this helper lets propagate; the walker catches them to leave
  the selection unplanned (`optimizer/walker.py:1159`), the resolver lets them surface as the
  field's own pagination error (`connection.py:294` un-caught). Documented at lines 102-106.
- The sidecar helpers are precise: `has_connection_sidecar_input` is keyword-only and tests
  `is not None` (not truthiness), so a falsy-but-present filter input (e.g. an empty filter
  object) still counts as present — correct for the "refuse the window if any sidecar is
  supplied" gate. `has_connection_sidecar_kwargs` composes extraction + presence in one call.
- GLOSSARY: no drift. The new symbols are internal contracts (correctly undocumented, matching
  the established internal-scaffolding pattern); the Connection-aware optimizer planning entry
  (GLOSSARY:236) and the `Meta.relation_shapes` / Strictness-mode entries (836, 1264) describe
  the fallback shapes and `last`-only reverse accurately and do not mention `after + last` as a
  windowed shape — consistent with the (intended) per-parent fallback. `#multi-database-cooperation`
  is unrelated to this file's contracts.

### Summary

A small, well-factored, correctly cycle-safe contract module that is the right shape for its job
— with one real data-correctness bug. The `reverse` predicate at line 124 omits an `after is
None` clause, so `after: c, last: N` queries slip into the reversed-row-number window with a
non-zero offset; the rows come back correct but `has_previous_page` diverges from the per-parent
pipeline whenever the after-remainder is `<= last` rows, breaking the very cursor-parity
invariant the file exists to protect. Spec-033 Decision 5 already scopes the reversed window to
`last`-only and chose per-parent fallback for the offset-bearing shapes, so the root-cause fix is
to make this shape an unwindowable fallback (not merely flip the predicate, which would leave the
forward branch uncapped). One Medium (the matching missing-branch test gap) and two Lows (the
unconsumed tuple constant as a documented extension point; the docstring omission that seeded the
bug) round it out. No GLOSSARY drift.

---

## Fix report (Worker 2)

### Files touched

- `django_strawberry_framework/utils/connections.py` — added `UnwindowableConnection`
  (an internal control-flow signal exception, NOT a `DjangoStrawberryFrameworkError` and
  NOT a `ValueError`/`TypeError`) and raised it from `derive_connection_window_bounds` for
  the offset-bearing backward shape (`reverse and after is not None`). The pre-existing
  `reverse` predicate is unchanged; the guard fires AFTER it, before the
  `limit`/`ConnectionWindowBounds` return. Docstring gained the `after`-bearing-backward
  rationale paragraph. The `# noqa: N818` on the class is justified inline (control-flow
  sentinel, not a surfaced error — the only other `Exception` subclass in the package is the
  `...Error` root, which this deliberately is not).
- `django_strawberry_framework/optimizer/walker.py` — imported `UnwindowableConnection`;
  `_connection_window_slice` deliberately does NOT catch it (only `(ValueError, TypeError)`),
  so it propagates; `_plan_connection_relation` wraps the `_connection_window_slice` call in
  `try/except UnwindowableConnection` and does a FULLY-UNPLANNED early `return` (records NO
  `planned_resolver_keys` identities) — distinct from the malformed-pagination `window is None`
  path which DOES record identities. Both docstrings document the distinction.

### The seam (which file signals, which honors)

- **Signals unwindowable:** `utils/connections.py::derive_connection_window_bounds` raises the
  new `UnwindowableConnection` for `after`+`last` (no `first`, no `before`).
- **Honors it:** `optimizer/walker.py::_plan_connection_relation` catches it and leaves the
  nested connection unplanned (no `to_attr` Prefetch, no resolver-key entry). With no
  `to_attr` written, the resolver's `_build_relation_connection_resolver` probe misses, no
  `_WindowedConnectionRows` wrapper is built, and `connection.py`'s shipped per-parent pipeline
  serves the page — restoring byte-parity. The resolver side needs NO change: `_consume_window`
  only calls `derive_connection_window_bounds` when a wrapper exists, which it never will for
  this shape (verified: `connection.py:285-286` returns `_NOT_A_WINDOW` before the helper call
  when `nodes` is not a wrapper).

### Why fully-unplanned (not the `window is None` path)

`after`+`last` is a VALID query that resolves correctly per-parent and raises NO error, so it
must be visible to the Slice-4 strictness contract as a real per-parent access — exactly like
the other Decision-6 fallback shapes (sidecar, divergent alias, hint SKIP, distinct), which all
early-`return` without recording identities. The `window is None` path records identities on
purpose (the malformed-pagination case will raise its OWN error, so strictness must not preempt
it — `walker.py` comment at the `window is None` branch). Routing `after`+`last` through
`window is None` would HIDE a genuine per-parent N+1 from strictness under `"raise"` — wrong per
Decision 8. Hence the distinct exception type and the separate early return.

### Confirmation against spec-033 Decision 5

Read Decision 5 (spec-033 line 293-322) and the Edge-cases `last`-only bullet (line 450):
"`before` + `last` combinations that the offset arithmetic cannot push down fall back per-parent
rather than approximating. The exact supported set follows `SliceMetadata`'s arithmetic and is
pinned by tests, not prose." `after`+`last` is precisely such an offset-bearing-`last` shape the
reversed whole-partition row numbering cannot honor; the fix makes it a per-parent fallback, as
Decision 5 mandates. Verified empirically that `SliceMetadata.from_arguments(after=c(3), last=3)`
→ `start=4` (non-zero offset), `expected=None` (no clean forward cap either), so neither the
reverse nor the forward window can serve it correctly.

### Currently-correct shapes confirmed still windowed (preserved)

In-process probe + the passing wire-parity suite confirm these still windowed (NOT rejected):
`last`-only (`reverse=True, offset=0`), `first`-only (`reverse=False, limit=expected`),
`after`+`first` (forward offset window, `offset=3, limit=2, reverse=False`), `before`+`last`
(forward window, `reverse=False`), unbounded no-args. Only `after`+`last` raises.

### Tests added or updated

- `tests/utils/test_connections.py::test_after_with_last_is_unwindowable_not_reverse_with_offset`
  — pins that `after`+`last` raises `UnwindowableConnection` and that `SliceMetadata.start == 4`
  (the non-zero offset that was the trap). FAILS pre-fix (pre-fix returns
  `ConnectionWindowBounds(offset=4, limit=3, reverse=True)`, no raise — confirmed by emulating
  the pre-fix body); PASSES post-fix.
- `tests/utils/test_connections.py::test_after_with_first_stays_a_windowed_forward_offset` —
  companion pin that `after`+`first` is NOT rejected (forward offset window preserved).
- `examples/fakeshop/test_query/test_library_api.py::test_genre_books_connection_after_last_page_info_matches_per_parent`
  — LIVE `/graphql/` nested reverse-M2M `booksConnection(after: c, last: 3)` over five books,
  after-remainder = 2 (`<= last`), NO sidecar (the shape itself routes to fallback, pk order via
  the deterministic-order rule). Asserts `hasPreviousPage is False` (the per-parent truth), right
  rows `["Dune","Elantris"]`, and positional cursors byte-matching the forward window. FAILS
  pre-fix on exactly `assert page["pageInfo"]["hasPreviousPage"] is False` → `assert True is False`
  (the windowed fast-path reported `True`; rows were already correct — the exact divergence the
  High's table predicts); PASSES post-fix. This is the AGENTS.md "prefer the example project"
  live home; it also closes the Medium coverage gap.

### Validation run

- `uv run ruff format .` — pass (1 file reformatted on first run, then no-changes; 265 unchanged)
- `uv run ruff check --fix .` — pass (`All checks passed!`; the `N818` is silenced by the
  justified inline `# noqa`)
- Focused tests (NOT the full suite): `tests/utils/test_connections.py` 9 passed;
  `tests/test_relay_connection.py` + `tests/utils/test_connections.py` 74 passed;
  `tests/optimizer/` 397 passed; live `examples/fakeshop/test_query/test_library_api.py` 100
  passed. The new live test confirmed fail-pre/pass-post by temporarily reverting the raise guard.

### Notes for Worker 3

- No shadow file used.
- No false-premise rejections — the High's premise (the `after is None` omission) was verified in
  source and the divergence reproduced live.
- The artifact's recommended change said "merely flip the predicate would leave the forward branch
  uncapped"; I followed the artifact's PREFERRED unplanned-fallback route, but used a DEDICATED
  exception (`UnwindowableConnection`) rather than reusing the `ValueError` family the artifact
  mentioned, BECAUSE the `ValueError`-caught `window is None` path records resolver identities
  (wrong for this valid-resolves-per-parent shape per the strictness contract). The dedicated
  type routes to the fully-unplanned early return instead. This is a refinement of the artifact's
  suggestion within its stated intent (per-parent fallback, Decision 5), not a departure.
- This re-touches the verified `walker.py` (box 97) — expected for a cross-file High per the
  dispatch. The walker change is small (import + a docstring note + the `try/except` early
  return). `plans.py` (box 95) was NOT touched — the fix is upstream of the windowing math.
- `uv.lock` clean (not modified). `examples/fakeshop/db.sqlite3` shows as modified (binary, 0 net
  bytes) — a live-test-run side effect on a regenerable artifact; left untouched per AGENTS #33 /
  regenerable-db rule. The working tree carries extensive prior-cycle / concurrent-dev dirt
  (AGENTS #33), left untouched; my contribution is the four files above (diffstat below).
- Diff IS logic-bearing (a real behaviour change at a public API surface: nested `after`+`last`
  connections now resolve per-parent with correct `pageInfo` instead of a windowed fast path with
  divergent `hasPreviousPage`).

### `git diff --stat` vs baseline (my four files)

```
 django_strawberry_framework/optimizer/walker.py  | (import + docstring note + try/except early return; rest of walker hunk is prior-cycle dirt)
 django_strawberry_framework/utils/connections.py | 40 ++++  (UnwindowableConnection + raise guard + docstring)
 examples/fakeshop/test_query/test_library_api.py | live after+last page-info parity test
 tests/utils/test_connections.py                  | 58 +++++ (two unit pins)
```

(Whole-tree `git diff <baseline> --stat` is dominated by concurrent other-worker dirt; the four
files above are my contribution.)

---

## Verification (Worker 3)

### Logic verification outcome

**High (`after`+`last` slips into reverse branch, breaks `pageInfo` parity) — ADDRESSED, root-cause.**
The fix adds `UnwindowableConnection` (a control-flow `Exception`, not `...Error`/`ValueError`/
`TypeError`) raised by `derive_connection_window_bounds` for `reverse and after is not None`
(connections.py:160-164), and a `try/except UnwindowableConnection: return` in
`_plan_connection_relation` (walker.py:1225-1236) that early-returns WITHOUT recording resolver
identities. Verified the bug mechanism in source: `_resolve_from_window`
(connection.py:241,249) reads `has_previous_page = first_rn > 1` off the FORWARD `_dst_row_number`
which spans the whole partition, so for `after:c, last:N` (reverse=True, offset=int(c)+1) the tail
rows carry high forward row numbers → `True`, while the per-parent pipeline reports `False` when
the after-remainder ≤ `last`. The fix prevents that shape from ever being windowed.

(a) **Bug-fixed repro (fail-pre / pass-post).** Unit probe
(`docs/review/temp-tests/connections_high/probe_logic.py`): emulating the PRE-FIX body returns
`reverse=True, offset=4` for `after:3,last:3` and the fast-path `first_rn>1`→`True` diverges from
per-parent `False`; the REAL helper raises `UnwindowableConnection` for every after-remainder.
LIVE probe (`test_pre_fix_live.py`, monkeypatching the pre-fix body across all three import sites —
`utils.connections`, `optimizer.walker`, `connection` — without editing tracked source): the same
`booksConnection(after:c, last:3)` query returns the correct rows `["Dune","Elantris"]` with
`hasPreviousPage: True` PRE-FIX and `hasPreviousPage: False` POST-FIX. This is exactly the
divergence the High table predicts (rows right, `hasPreviousPage` wrong). The permanent live test
`test_genre_books_connection_after_last_page_info_matches_per_parent` pins precisely this; it
passes post-fix and asserts `hasPreviousPage is False`.

(b) **No regression to windowed shapes.** Independently probed every other shape against the REAL
helper: `last`-only → `(offset=0, limit=3, reverse=True)`; `first`-only → `(0,3,False)`;
`after+first` → `(offset=3, limit=2, reverse=False)`; `before+last` → `(offset=5, limit=3,
reverse=False)` (forward window, NOT reversed); unbounded → `(0,None,False)`. None raise — the
`UnwindowableConnection` raise fires ONLY for `after+last` (no `first`, no `before`). Plan-level
probe (`test_plan_parity.py`) confirms `last`-only still emits a window prefetch.

(c) **Dedicated-exception / strictness-visibility soundness — SOUND.** (i) The catch is narrow:
`_connection_window_slice` catches only `(ValueError, TypeError)` (walker.py:1168);
`UnwindowableConnection` is `Exception` (not a `ValueError`/`TypeError`, asserted in probe), so it
propagates uncaught through `_connection_window_slice` and is caught by the dedicated
`except UnwindowableConnection` in `_plan_connection_relation` — it does NOT swallow malformed
pagination (a bad cursor still raises `ValueError`/`TypeError` → routes to the `window is None`
path, verified) nor `OptimizerError` (the `window_partition_for_prefetch` catch is a separate
later try). (ii) It routes to a FULLY-UNPLANNED early return recording NO `planned_resolver_keys`,
distinct from the `window is None` path which DOES `append_unique_many` (walker.py:1247).
Plan-level parity probe proves `after+last` yields `prefetch_related=()` AND
`planned_resolver_keys=()` — byte-identical to the **sidecar** fallback (`()`,`()`), and distinct
from **malformed** (records ≥1 key). This is correct: `after+last` is a VALID query that resolves
per-parent and raises no error of its own, so it is a real per-parent access that strictness SHOULD
see (like sidecar/divergent/distinct, pinned by `test_fallback_not_planned_sidecar_input` which
asserts `planned_resolver_keys == ()`), NOT the malformed case (which records its key so strictness
does not preempt the pipeline's own cursor error — `test_malformed_slice_arguments_emit_no_window_but_record_resolver_key`).
Strictness (`raise`) behavior is correct: at resolve time `_check_n1(kind="connection_to_attr")`
finds the key absent and `to_attr` absent → `lazy=True` → flagged under `"raise"` like any genuine
per-parent access (no SPURIOUS raise — the access genuinely IS per-parent); no missed-plan crash
(the resolver's `to_attr` probe at connection.py:1117 simply misses → shipped per-parent pipeline
serves the page, `derive_connection_window_bounds` never re-invoked at resolve time for this shape).

**Spec-033 Decision 5 confirmation.** Line 450 scopes the reversed window to `last`-only and states
"combinations that the offset arithmetic cannot push down fall back per-parent rather than
approximating ... The exact supported set follows `SliceMetadata`'s arithmetic and is pinned by
tests, not prose." Line 582 (Edge-cases) reaffirms "window what `SliceMetadata`'s arithmetic
expresses; fall back per-parent for the rest." `after+last` resolves a non-zero offset with
`expected is None` (no clean forward cap either), so it is precisely such an offset-bearing shape
— the per-parent fallback is spec-aligned, not a departure.

**Medium (missing-branch coverage) — ADDRESSED** by the same three tests (unit `after+last`
rejection, unit `after+first` preserved, live wire-parity), which double as the regression fence.

**Lows — deferred to comment pass / standing.** L (built-but-unconsumed `CONNECTION_SIDECAR_KWARGS`)
remains a documented extension point, no source change — correct. L (docstring omits `after` case)
is now ADDRESSED in the code-comment scope (the new docstring paragraph at connections.py:141-150
states `after`-bearing `last` windows are NOT reversed); comment-pass will re-verify final wording.

### DRY findings disposition

The DRY defer-with-trigger bullet (route a presence-check loop through `CONNECTION_SIDECAR_KWARGS`
or delete it when a third sidecar `search:` lands) is PRESERVED — the fix touched neither the
three-helper sidecar ladder nor the tuple; quote-trigger "a future sidecar (e.g. `search`) is then
a one-line edit here" still stands. No new act-now consolidation introduced. (Note: walker.py's
cycle diff also carries the prior-cycle `_resolver_identities_for` DRY refactor — box 97, verified —
which is concurrent dirt, not this cycle's edit.)

### Temp test verification

- `docs/review/temp-tests/connections_high/probe_logic.py` — unit logic: pre-fix emulation
  divergence, post-fix raise, no-regression grid, narrow-catch. ALL PASSED.
- `docs/review/temp-tests/connections_high/test_pre_fix_live.py` — LIVE fail-pre/pass-post via
  monkeypatched pre-fix body (no tracked-source edit). PASSED (PRE `hasPreviousPage:True`, POST
  `hasPreviousPage:False`).
- `docs/review/temp-tests/connections_high/test_plan_parity.py` — plan-level: `after+last`
  fully-unplanned parity with sidecar, distinct from malformed, last-only still windows. PASSED.
- Disposition: deleted at cycle closeout (Worker 0). Shipped behavior is already pinned by the two
  permanent unit pins + the live wire-parity test — temp tests are not the only proof. No new
  Medium/High promotion needed.
- Focused suite: `tests/utils/test_connections.py` (9) + the live `after+last` test (1) = 10 passed.
  Coverage-gate FAIL under the focused subset is the expected artifact (connections.py itself 100%).

### Verification outcome

`logic accepted; awaiting comment pass` — sets top-level `Status: logic-accepted`. Checkbox NOT
marked (interim sub-pass; terminal verify pending comment + changelog passes).

---

## Comment/docstring pass

### Files touched

- None. The logic pass already documented the non-obvious rationale adequately at
  every site the comment pass requires; no edit was made.

### Per-finding dispositions

- **High (`UnwindowableConnection` sentinel rationale)** — already documented; no edit.
  `UnwindowableConnection`'s class docstring (`connections.py::UnwindowableConnection`)
  states it is a control-flow SENTINEL — the inline `# noqa: N818 - control-flow signal,
  not a surfaced error` justifies the naming, and the body says "A control-flow sentinel,
  deliberately NOT a ``DjangoStrawberryFrameworkError`` and NOT a ``ValueError`` /
  ``TypeError``". It documents the raise is ONLY for the offset-bearing-reverse shape
  ("``after`` + ``last``, no ``first``, no ``before``"), the walker-fallback signal intent
  ("must treat THIS shape as a fully-unplanned Decision-6 fallback (no
  ``planned_resolver_keys`` entry) so the per-parent access stays visible to the Slice-4
  strictness contract"), the cursor-parity divergence (the forward ``_dst_row_number``
  spans the WHOLE partition so ``hasPreviousPage`` / the offset cursor "diverge from the
  per-parent pipeline whenever the after-remainder is ``<= last`` rows"), and the spec-033
  Decision 5 deferral verbatim. The raise site in `derive_connection_window_bounds` carries
  the matching docstring paragraph (the `after`-bearing-backward window is NOT reversed +
  the Decision-5 per-parent fallback) and an inline comment at the `raise`.
- **Low (docstring reverse-branch rationale omits the `after` case)** — already addressed
  in the logic pass (the new `derive_connection_window_bounds` docstring paragraph states
  `after`-bearing `last` windows are NOT reversed and fall back per-parent); no further
  edit. This was the comment-tier item Worker 1 deferred to this pass; it is satisfied.
- **Walker catch-site rationale** — already documented; no edit. The
  `except UnwindowableConnection` block in `_plan_connection_relation` documents WHY it
  routes to a FULLY-UNPLANNED early `return` recording NO resolver identities, and contrasts
  it explicitly against the malformed-pagination `window is None` path ("unlike the
  malformed-pagination `window is None` path below, this query resolves correctly per-parent
  and never raises its own error, so it is a real per-parent access"). The `window is None`
  branch's own comment reciprocally names the unwindowable shape in its list of fully-unplanned
  fallback shapes and explains why malformed DOES record identities (Decision 8 error
  locality). `_connection_window_slice`'s docstring also documents that
  `UnwindowableConnection` is deliberately NOT caught there. Decision-6/Decision-5 fallback
  parity is cited at each site.
- **DRY defer-with-trigger bullet** — PRESERVED untouched (no source edit, so the
  `CONNECTION_SIDECAR_KWARGS` retire-or-route trigger when `search:` lands still stands).

### Validation run

- `uv run ruff format .` — pass (265 files unchanged)
- `uv run ruff check --fix .` — pass (`All checks passed!`)

### Notes for Worker 3

- ZERO source edit this pass: the logic-pass commit already carried the full comment/docstring
  rationale at the class docstring, the `derive_connection_window_bounds` docstring + inline
  raise comment, the `_plan_connection_relation` catch block, the `window is None` contrast
  comment, and the `_connection_window_slice` docstring. Per the comment-dicta "don't over-comment
  the now-consistent line" and the brief's "if the logic-pass code already documents these
  adequately, make NO edit and say so", I added nothing.
- No logic changed. `git diff --stat` for the two source files is unchanged from the logic pass
  (walker.py 95 lines, connections.py 40 lines — the same hunks Worker 3 logic-accepted).
- `uv.lock` clean (not modified).

---

## Verification (Worker 3, comment pass)

### Comment/docstring verification outcome

**No logic changed since logic-accept — CONFIRMED.** `git diff --stat <baseline> --
connections.py walker.py` is unchanged (connections.py +40; walker.py 95, of which the
`_resolver_identities_for` hunk is prior-cycle box-97 DRY dirt and the
`UnwindowableConnection` import + catch block is this cycle). No commit touched either file
since baseline (`git log <baseline>..HEAD -- <both>` empty); both are working-tree
modifications byte-identical to the logic-accepted state. The comment pass added zero source
edit, as Worker 2 reported — the full docstring/comment rationale was already present at
logic-accept and is visible in the same diff hunks I logic-verified.

**(a) `UnwindowableConnection` sentinel + `# noqa: N818` — ADEQUATE.** The class docstring
carries the inline `# noqa: N818 - control-flow signal, not a surfaced error` justification and
states it is "A control-flow sentinel, deliberately NOT a ``DjangoStrawberryFrameworkError`` and
NOT a ``ValueError`` / ``TypeError``"; documents the raise fires ONLY for `after`+`last` (no
`first`, no `before`); the fully-unplanned-fallback intent (no `planned_resolver_keys`,
strictness-visible); the partition-spanning divergence mechanism (forward `_dst_row_number`
spans the WHOLE partition → `hasPreviousPage`/offset cursor diverge when after-remainder
`<= last`); and the spec-033 Decision 5 deferral verbatim. The `derive_connection_window_bounds`
docstring repeats the matching paragraph and the `raise` site carries an inline comment. The
non-obvious *why* is documented without restating obvious code.

**(b) Walker catch — fully-unplanned vs malformed-`window is None` — ADEQUATE.** The
`except UnwindowableConnection` block comment states it stays FULLY unplanned (records NO
resolver identities, like sidecar / divergent-alias / distinct), and contrasts it explicitly
against the malformed-pagination `window is None` path ("unlike the malformed-pagination
`window is None` path below, this query resolves correctly per-parent and never raises its own
error, so it is a real per-parent access"), citing Decision 5. `_connection_window_slice`'s
docstring documents that `UnwindowableConnection` is deliberately NOT caught there. Both sides of
the distinction are documented at the right altitude.

Worker 2's decision to add nothing is defensible — no genuine comment gap remains.

### Verification outcome

`comments accepted; awaiting changelog disposition` — sets top-level `Status: comments-accepted`.
Checkbox NOT marked (interim sub-pass; terminal verify pending changelog pass).

---

## Changelog disposition

### State

`Not warranted`.

### Reason

The fixed surface is **new-in-0.0.9 and unreleased** — no released consumer could ever have
hit the divergent `hasPreviousPage`, so the fix folds into the existing 0.0.9 `### Added`
entries rather than earning a `### Fixed` note. Cites BOTH required authorities:

- `AGENTS.md` ("Do not update CHANGELOG.md unless explicitly instructed") — no edit authority.
- The active review plan is silent on changelog authorization for this cycle, and a per-file
  cycle is NEVER the authorising scope (changelog drift forwards to the project pass).

### Released-vs-unreleased investigation (git + CHANGELOG)

CHANGELOG release dates: `0.0.7` = 2026-05-27, `0.0.8` = 2026-06-03, `0.0.9` = 2026-06-13
(current / unreleased). Version-bump commits: `171a9bc1` bumps to `0.0.8`; `8f35f6d2` bumps
to `0.0.9` (the current cycle).

Every element of the affected surface — the synthesized `<field>Connection` relation fields,
`DjangoConnectionField`, the windowed-`Prefetch` planning path, and the
`derive_connection_window_bounds` window-bounds contract — is strictly newer than the `0.0.8`
release commit:

- **`derive_connection_window_bounds` / `utils/connections.py`:** introduced at `c8df425c`
  ("Refactor connection optimizer: centralize window bounds and sidecar kwargs"), which is a
  descendant of the `0.0.8` bump (`git merge-base --is-ancestor 171a9bc1 c8df425c` → true).
  `git show 171a9bc1:django_strawberry_framework/utils/connections.py` → file ABSENT at `0.0.8`.
- **`DjangoConnectionField` / `connection.py`:** `git show 171a9bc1:.../connection.py` →
  file ABSENT at `0.0.8` (zero `DjangoConnectionField` hits). The connection field landed via
  spec-030 (`89798607` "Finish spec-030-connection_field-0_0_9.md"), which is AFTER the `0.0.8`
  bump (`merge-base --is-ancestor 171a9bc1 89798607` → true; `--is-ancestor 89798607 171a9bc1`
  → false, i.e. NOT in `0.0.8`).
- **Relation-as-Connection synthesis / `Meta.relation_shapes`:** `relation_shapes` has zero hits
  in `git show 171a9bc1:.../inspect_django_type.py`; the synthesis shipped via spec-032
  (`8a860e9a`) and the optimizer planning via spec-033 (`4e536697` "Finish
  spec-033-connection_optimizer-0_0_9"), both AFTER `0.0.8` (`--is-ancestor 171a9bc1 4e536697`
  → true).

All four pieces are new-in-0.0.9. The `[0.0.9]` CHANGELOG section already documents them under
`### Added`: "**`DjangoConnectionField` (Relay connection field).**", "**Relation-as-Connection
upgrade + `Meta.relation_shapes`.**", and "**Connection-aware optimizer planning.**" (which
explicitly states the windowed-`Prefetch` planning "falls back to the per-parent pipeline for
ambiguous empty windows (`first: 0`, overshot `after:`) and unplanned shapes"). The
`after`+`last` fix is precisely such a per-parent fallback shape — it extends the already-listed
fallback set within an unreleased feature, never a regression against shipped behaviour.

This is the expected `Not warranted` outcome, in deliberate contrast to the separately-fixed
optimizer anonymous-fragment High, which DID ship on the released `0.0.7` `DjangoListField`
list path and was therefore `Warranted but deferred to maintainer`.

### What was done

No `CHANGELOG.md` edit. (Read for evidence this pass only; not modified.)

### Validation run

- `uv run ruff format .` — pass / no-changes (265 files unchanged)
- `uv run ruff check --fix .` — pass / no-changes (`All checks passed!`)

---

## Verification (Worker 3, terminal)

### Terminal verification outcome

Incoming `Status: fix-implemented` (bare) — terminal verify. Logic-accepted + comments-accepted
already recorded; changelog `Not warranted` git-grounded. All gates re-affirmed; nothing changed
since the interim passes (`git log <baseline>..HEAD -- connections.py walker.py` empty; both are
working-tree mods byte-identical to the logic-accepted hunks).

**(1) High fixed at root cause — RE-AFFIRMED.** `derive_connection_window_bounds` raises
`UnwindowableConnection` for `reverse and after is not None` (connections.py:160-164); the catch
in `_plan_connection_relation` (walker.py:1225-1236) early-`return`s FULLY unplanned (no
`append_unique_many`). Focused logic probe (`docs/review/temp-tests/connections_terminal/probe.py`,
`uv run python`, config.settings): `after+last` raises for every after-remainder (1,2,3,4,6);
`SliceMetadata.start == 4` is the pre-fix non-zero-offset trap. Windowed shapes UNAFFECTED — no
raise, correct triples: `last`-only `(0,3,reverse=True)`, `first`-only `(0,3,False)`, `after+first`
`(3,2,False)`, `before+last` forward (`reverse=False, limit=3` — NOT reversed), unbounded
`(0,None,False)`. The live wire-parity pin
`test_genre_books_connection_after_last_page_info_matches_per_parent` passes post-fix asserting
`hasPreviousPage is False` (the per-parent truth) with correct rows `["Dune","Elantris"]`.

**(2) Faithful no-regression / strictness-visible — RE-AFFIRMED.** `UnwindowableConnection` is a
plain `Exception`, NOT a `ValueError`/`TypeError` and NOT a `DjangoStrawberryFrameworkError`
(probe-asserted). `_connection_window_slice` catches only `(ValueError, TypeError)` (walker.py:1133
diff / source confirmed), so UC propagates uncaught to the dedicated catch — the fully-unplanned
path records NO identities (distinct from `window is None` which `append_unique_many`s at
walker.py:1247). A malformed cursor still raises the narrow `ValueError` family (probe-confirmed),
routing to the identity-recording `window is None` branch — so no spurious N+1 raise for the valid
`after+last` shape, and no missed-plan crash (resolve-time `to_attr` probe at connection.py:1117
simply misses → shipped per-parent pipeline; `_consume_window` returns `_NOT_A_WINDOW` at
connection.py:286 before `derive_connection_window_bounds` is ever re-called for this shape).

**(3) Changelog `Not warranted` git-justified — CONFIRMED.** `git diff -- CHANGELOG.md` empty;
the connection / windowed-Prefetch surface is new-in-0.0.9 unreleased (per the prior changelog-pass
git investigation: `connections.py` absent at the `0.0.8` bump `171a9bc1`). Both required citations
present (AGENTS.md + active-plan silence). Internal-only/unreleased framing matches the diff scope.

**(4) Tests fail-pre/pass-post, placement, not over-fit — CONFIRMED.** `tests/utils/test_connections.py`
9 passed (connections.py 100% own-coverage); the live pin 1 passed (focused-subset coverage-gate FAIL
is the expected artifact). The two unit pins (`test_after_with_last_is_unwindowable_not_reverse_with_offset`
asserts the raise AND `SliceMetadata.start == 4`; `test_after_with_first_stays_a_windowed_forward_offset`
preserves the forward shape) + the live `tests`-tree pin are at correct AGENTS.md placements
(`tests/utils/`, `examples/fakeshop/test_query/`). The walker.py cycle diff also carries the prior
box-97 `_resolver_identities_for` DRY hunk — already-verified concurrent content, scoped OUT of this
cycle's judgment (this cycle = the `UnwindowableConnection` import + catch block only). The
test_library_api.py diff likewise carries prior box-97/98 skip-include + anonymous-fragment tests as
concurrent content; this cycle owns only `test_genre_books_connection_after_last_page_info_matches_per_parent`.
Not over-fit — the unit pins assert the contract (raise + offset trap + forward preserved), the live
pin asserts the wire-parity invariant.

**(5) DRY defer bullet preserved — CONFIRMED.** The `CONNECTION_SIDECAR_KWARGS` retire-or-route
defer-with-trigger (quote-trigger "a future sidecar (e.g. `search`) is then a one-line edit here")
is untouched; the fix touched neither the three-helper sidecar ladder nor the tuple.

**Ruff — CLEAN.** `ruff format --check` (4 files already formatted) + `ruff check` (`All checks
passed!`) on the four files; the `N818` silenced by the justified inline `# noqa`. COM812 conflict
notice is standing/expected.

### Temp test verification

- `docs/review/temp-tests/connections_terminal/probe.py` — terminal logic probe (UC-not-narrow-family,
  after+last raises for every remainder, all windowed shapes unaffected, malformed→narrow ValueError).
  PASSED. Disposition: deleted at cycle closeout (Worker 0); shipped behavior pinned by the two
  permanent unit pins + the live wire-parity test — temp test is not the only proof.

### Verification outcome

`cycle accepted; verified` — sets top-level `Status: verified` AND marks the `utils/connections.py`
box in `docs/review/review-0_0_9.md`.

---

## Iteration log

_None yet._
