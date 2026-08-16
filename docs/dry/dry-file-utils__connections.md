# DRY review: `django_strawberry_framework/utils/connections.py`

Status: verified

## System trace

Cycle-safe owner of the contracts that plan-time (`optimizer/nested_planner.py`,
re-exported through `optimizer/walker.py`) and resolve-time (`connection.py`)
must spell identically, or optimizer-on vs optimizer-off pages diverge:

1. **Sidecar kwarg family** — `CONNECTION_FILTER_KWARG` / `CONNECTION_ORDER_KWARG`
   (+ GraphQL twin `CONNECTION_ORDER_KWARG_GRAPHQL`),
   `connection_sidecar_inputs_from_kwargs`, `has_connection_sidecar_input`,
   `has_connection_sidecar_kwargs`. Walker refuses to window-plan a
   sidecar-bearing nested connection; resolver refuses to consume a window when
   sidecars are present.
2. **Fetch-mode / window-range policy** — `FetchMode`, `_is_probe_shape`,
   `is_ambiguous_empty_window`, `WindowRangePlan` (+ probe increment /
   `fetch_upper_bound` / `fetch_limit` / shape predicates / `fetch_mode`),
   `window_range_plan`, `assert_window_fetch_mode` /
   `assert_window_fetch_mode_for`, `split_window_rows`. ORM
   (`plans.py::apply_window_pagination`) and lateral
   (`lateral_fetch.py`) renderers, plus nested/single-parent fetch request
   objects, consume the plan; the resolver reads shape predicates off the
   physical window rather than re-deriving `fetch_mode` per alias.
3. **Offset / keyset window bounds** — `ConnectionWindowBounds`,
   `UnwindowableConnection`, `derive_connection_window_bounds` (via
   `SliceMetadata.from_arguments`), `derive_keyset_window_bounds`,
   `resolve_relay_max_results`, and (this pass)
   `assert_relay_pagination_bound`.

Plan-time Int-literal coercion stays in
`optimizer/nested_planner.py::_coerce_pagination_int` (walker re-exports it) —
deliberately not owned here. Cursor decoding stays in `keyset.py`. `list_field.py`
has no overlap with these contracts.

Connected importers: `connection.py`, `optimizer/nested_planner.py`,
`optimizer/plans.py`, `optimizer/lateral_fetch.py`, `optimizer/nested_fetch.py`,
`optimizer/single_parent_fetch.py`. Tests: `tests/utils/test_connections.py`,
`tests/test_keyset.py`, connection/keyset HTTP pins.

Item baseline `49b401e1fc68aa0cab0486941b0e81c68d0e35c0`: pre-edit target matched
baseline; concurrent docstring-only wording vs HEAD (nested_planner ownership of
`_coerce_pagination_int`) left untouched.

## Verification

Searches covered window-bound derivation, sidecar presence, `FetchMode` /
probe/count XOR, `relay_max_results` digs, pagination `ValueError` text,
`lower_bound` / `upper_bound` / `+1` overfetch math, and reverse predicates.
Renderers already bind `range_plan.fetch_*` / marker rules rather than
re-deriving them. Sidecar presence goes only through the shared helpers (no
re-spelled `kwargs.get("filter")` / `order_by` outside this module).

Strongest rejected candidates:

- **`_relay_max_results_from_info` vs `resolve_relay_max_results` config dig.**
  Both read `getattr(schema_config_from_info(info), "relay_max_results", None)`,
  but missing-config policy forks on purpose: planner passes `None` into
  `SliceMetadata` (engine default); resolve applies terminal `_RELAY_MAX_RESULTS_DEFAULT`
  (100) then `effective_bound`. The dig *path* is already owned by
  `schema_config_from_info`; extracting a one-line getattr would churn a
  verified sibling for no contract gain.
- **Backward / reverse predicates** across
  `derive_connection_window_bounds` (`last` + no `first` + no `before`),
  `derive_keyset_window_bounds` (any `before` / `last`-only → unwindowable), and
  `_resolve_keyset_connection` (`last`-only with `last: 0` quirk). Same words,
  different rules — a shared helper would need mode flags.
- **Keyset root `page_size + 1` vs `WindowRangePlan._probe_increment`.** Classic
  Relay list overfetch for page flags vs the windowed n+1 probe sentinel —
  different fetch surfaces and consumers.
- **`CONNECTION_SIDECAR_KWARGS` omitting `orderBy`.** Tuple is the Python-kwarg
  vocabulary; presence helpers already read both order spellings. Spec-055
  notes the tuple as a future extension hook — not a second presence check.
- **`assert_window_fetch_mode` vs `_for`.** Dual entry for resolved plan vs raw
  request args; `_for` delegates through `window_range_plan` once.
- **Folding `_coerce_pagination_int` into this module.** Docstring and nested
  planner already own plan-time token coercion; resolver arguments are already
  `int`. Moving it here would pull planner concerns into the shared substrate
  for no second consumer.

## Opportunities

### 1. SliceMetadata-parity keyset page-size validation

- **Repeated responsibility:** Relay `first` / `last` must be non-negative and
  `<= cap`, raising `SliceMetadata`'s exact `ValueError` text, on every keyset
  path that cannot run through `SliceMetadata.from_arguments`.
- **Sites:** `derive_keyset_window_bounds` (windowed plan/resolve); 
  `connection.py::_resolve_keyset_connection` (root / per-parent slicer,
  validates both `first` and `last` because it serves backward pages).
- **Evidence:** Identical message strings and `< 0` / `> cap` rule; comments at
  both sites stated the lockstep intent; a message or rule change had to be
  hand-mirrored.
- **Owner:** `utils/connections.py` (keyset fork of bounds / cap policy).
- **Consolidation:** New `assert_relay_pagination_bound(argument, value, *, cap)`;
  both sites call it. Window path still validates only `first` (backward raises
  `UnwindowableConnection` first); slicer still validates `first` and `last`.
- **Proof:** `tests/utils/test_connections.py::test_assert_relay_pagination_bound_matches_slice_metadata_text`;
  existing `tests/test_keyset.py::test_derive_keyset_window_bounds_first_validation`
  and keyset connection over-cap pins remain the integration surface (deferred
  pytest this cycle).
- **Risks / non-goals:** Does not replace `SliceMetadata` validation on the
  offset path; does not unify reverse/unwindowable predicates; slicer retains
  `last: 0` quirk after the shared bound check.

## Judgment

This module already is the system owner for sidecar presence, fetch-mode /
window-range math, and offset/keyset bounds. One real drift surface remained:
keyset page-size `ValueError` text spelled twice. That rule now lives once here;
verified siblings were touched only to consume the owner. Remaining lookalikes
are intentional forks (None vs 100, reverse vs unwindowable, list overfetch vs
probe).

## Implementation (Worker 1)

- Added `assert_relay_pagination_bound` in `utils/connections.py`.
- Migrated `derive_keyset_window_bounds` and
  `connection.py::_resolve_keyset_connection` to it.
- Permanent unit test in `tests/utils/test_connections.py`.
- `uv run ruff format` + `uv run ruff check --fix` on edited paths — clean.
- Deferred pytest (cycle policy). No CHANGELOG.
- Concurrent docstring-only edit on this file vs HEAD left untouched.

Item-scoped diff vs `49b401e1fc68aa0cab0486941b0e81c68d0e35c0`:
`utils/connections.py`, `connection.py`, `tests/utils/test_connections.py`
(+51 / −19). Artifact is new.

Ready for Worker 2.

## Independent verification (Worker 2)

Re-traced the keyset bound-check contract independently against present-day
source, `SliceMetadata.from_arguments`, both migrated call sites, and a
package-wide search for leftover spellings / missed consolidations.

**Consolidation holds.** `assert_relay_pagination_bound` is the single
package-owned spelling of the Relay `< 0` / `> cap` `ValueError` text that
`SliceMetadata` applies on the offset path. Upstream `SliceMetadata` still
owns the offset vocabulary (cannot be the package owner); the keyset fork
cannot run through it, so this helper is the correct package owner for the
two sites that previously mirrored the messages by hand.

**Both sites migrated; no leftovers.**
- `derive_keyset_window_bounds` validates only `"first"` after the
  unwindowable guard (backward never reaches the bound check) — confirmed.
- `connection.py::_resolve_keyset_connection` still validates both
  `"first"` and `"last"`, then applies `last_zero_quirk` after the shared
  check — confirmed; quirk is not a bypass of the cap.
- Package-wide search for `must be a non-negative integer` /
  `cannot be higher than` / inline `value < 0` bound checks finds only
  `assert_relay_pagination_bound`. No third consumer, no stale inline copy.

**Message parity with SliceMetadata.** Upstream raises exactly
`Argument '{argument}' must be a non-negative integer.` and
`Argument '{argument}' cannot be higher than {max_results}.`; the helper
matches. Non-`int` no-op matches `isinstance(..., int)` gating.

**Rejected candidates challenged and upheld.**
- `_relay_max_results_from_info` returns `None` (engine default);
  `resolve_relay_max_results` applies terminal `100` then `effective_bound`.
  Shared dig path already lives in `schema_config_from_info`; missing-config
  policy fork is intentional — consolidating would need a mode flag.
- Reverse predicates differ by design: offset
  (`last` + no `first` + no `before`, with `after`+`last` → unwindowable);
  keyset window (any `before` OR `last`-only → unwindowable); keyset slicer
  (`last`-only minus `last: 0` quirk). Same words, different contracts.
- `page_size + 1` (keyset list overfetch for page flags) vs
  `WindowRangePlan._probe_increment` (windowed SQL sentinel) — different
  fetch surfaces and consumers.
- `CONNECTION_SIDECAR_KWARGS` is Python-kwarg vocabulary; presence helpers
  already read `orderBy`. No second presence check.
- `assert_window_fetch_mode_for` delegates through `window_range_plan` once.
- `_coerce_pagination_int` remains nested-planner-owned (plan-time token
  coercion); resolver args are already `int`.

**Owner clarity.** One named helper with SliceMetadata-parity docstring beats
two comment-locked inline copies that had to change in lockstep. Callers keep
their distinct first-only vs first+last validation scope.

**Scoped diff.** Item-scoped diff vs `49b401e1…` is only
`utils/connections.py`, `connection.py`, `tests/utils/test_connections.py`
(+51 / −19): helper add, two call-site migrations, permanent unit test.
Concurrent nested-planner docstring wording vs HEAD was already present at
item baseline and was not absorbed into this item's delta. No unrelated
cleanup.

**Missed consolidations.** Independent search for sidecar `.get("filter")` /
`order_by` re-spells, duplicate bound messages, and probe/+1 lookalikes found
no additional same-contract duplicates warranting a change on this target.

**Proof.** Permanent
`tests/utils/test_connections.py::test_assert_relay_pagination_bound_matches_slice_metadata_text`
pins the shared text; existing
`tests/test_keyset.py::test_derive_keyset_window_bounds_first_validation`
and keyset over-cap pins remain the integration surface (pytest deferred per
cycle policy). No blockers.

Verdict: verified. Plan checkbox marked.
