# DRY review: `django_strawberry_framework/connection.py`

Status: fix-implemented → verified

## System trace

`connection.py` owns the Relay cursor-pagination surface: `DjangoConnection[T]`
(the `ListConnection` subclass carrying the `first` + `last` guard, windowed-prefetch
consumption via `_consume_window` / `_resolve_from_window`, and keyset dispatch),
the framework keyset slicer `_resolve_keyset_connection`, the generated concrete
`<TypeName>Connection` classes (`_generate_connection_class` / `_build_total_count_connection`
/ `_connection_type_for`), and the `DjangoConnectionField` factory with its synthesized
signature resolver running the composition pipeline (`_pipeline_sync` / `_pipeline_async`
→ `_finalize_queryset` → optimizer plan).

Consumers: package root export (`django_strawberry_framework/__init__.py`),
finalizer Phase-2.5 relation-connection synthesis (`types/finalizer.py` imports
`_build_relation_connection_resolver` / `_connection_type_for`), dogfooding in
`examples/fakeshop/apps/{products,library}/schema.py` (offset, `totalCount`, and
keyset `cursor_field` surfaces), and three test trees (`tests/test_connection.py`,
`tests/test_relay_connection.py`, `tests/test_keyset_connection.py`,
`examples/fakeshop/test_query/*`). Lockstep partners: `utils/connections.py`
(shared window/sidecar/fetch-mode contracts), `keyset.py` (canonical cursor codec),
`optimizer/plans.py` + `nested_planner.py` (plan-time window/order twins),
`list_field.py` (non-Relay sibling flavor sharing target validation), `resource_policy.py`.

## Verification

Axis 1 — cross-flavor policy mirroring (searched). Grep for `AsyncIterable`,
`SyncMisuseError`, `_validate_relay_djangotype_target`, `bounded_rows` across the
package. Target validation is already single-sited (`list_field.py::_validate_relay_djangotype_target`);
row bounds are genuinely distinct policies (Relay cap via `SliceMetadata` /
`resolve_relay_max_results` vs `bounded_rows` max_list_rows). Found: the
async-only-iterable-in-sync-context guard spelled twice (connection + list_field,
shapes differing, wording drifted: "async-generator resolvers" vs "async iterable
resolvers") plus the raw predicate a third time in `resource_policy.py::bounded_rows_async`.
Became Opportunity 2. The `consumers.py` "connection" hits are the WebSocket
transport domain — unrelated.

Axis 2 — sync/async twins (searched, mostly rejected). `_pipeline_sync` / `_pipeline_async`
share head (`_prepare_pipeline_source`) and tail (`_finalize_queryset`); the colored
middle steps are kept explicit by documented package convention
(`utils/querysets.py::normalize_query_source` docstring) — merging would need a
maybe-await abstraction the convention forbids. REJECTED. `_attach_count_sync` /
`_attach_count_async` differ mechanically (lazy bound `.count` vs awaited `.acount()`,
await-before-raise discipline) and already share the single writer `_set_total_count`;
merging adds color flags. REJECTED. `_resolve_keyset_connection` already dispatches
internally over one `_build` body — correct as-is.

Axis 3 — derived rather than repeated knowledge (searched). Grep `_meta.ordering |
query.order_by`: the effective-order SELECTION (keyset `cursor_field` > explicit >
`Meta.ordering`, made total) was spelled twice — `nested_planner.py::plan_connection_relation`
step (d) and `connection.py::_finalize_queryset` — around the already-hoisted
`deterministic_order`. Became Opportunity 1. Grep `cursor_columns_for | order_fingerprint`:
the columns+fingerprint derivation lives once in `keyset.py`; `_keyset_connection_context`
(class-cached on the generated connection) and `nested_planner._keyset_cursor_context`
(`@cache`) are thin adapters whose difference is caching lifetime, not policy. REJECTED.

Axis 4 — inverse/round-trip pairs (searched, ruled clean). Keyset encode/decode
(`encode_keyset_cursor` / `decode_keyset_cursor`) and value serialize/deserialize are
both halves in `keyset.py`, one grammar; decode re-serializes to prove canonical shape.
Offset cursors are minted through Strawberry's edge class (`resolve_edge`, prefix +
base64 owned upstream) and decoded upstream (`SliceMetadata`) — not locally duplicated.
The walker→resolver window attr vocabulary routes through the shared
`_relation_connection_to_attr` / `_relation_connection_to_attr_for_key`. No split pair found.

Axis 5 — contracts restated in another medium (searched). GLOSSARY entries
(DjangoConnection / DjangoConnectionField / Connection-aware optimizer planning) restate
behavior — the standing-doc medium, updated under AGENTS.md Slice-5 rules, not code
duplication. Tests pin the shared error substring ("AsyncIterable in a sync execution
context", four sites) and enforce plan/resolve order parity end-to-end
(`test_fast_path_wire_parity_with_pipeline`, keyset cross-strategy parity tests).

Single-edit-site counts:
- "Keyset default order honors Meta.ordering when it extends cursor_field" (or "drop
  the Meta.ordering fallback") → forces nested_planner step (d) AND `_finalize_queryset`:
  **2** → Opportunity 1.
- "Change the sync-misuse recourse wording" / "classify declared async generators
  differently from plain AsyncIterable returns" → forces BOTH flavor guards: **2**
  (wording drift already observed) → Opportunity 2.
- "Change the terminal pk-tiebreak rule" → `plans.py::deterministic_order` only: **1**
  (Decision 11 hoist already proved).
- "Change the keyset cursor payload/codec" → `keyset.py` only: **1**.

Rejected candidate (strongest): the two token-identical keyset edge-minting
comprehensions (`_resolve_from_window` keyset branch vs `_resolve_keyset_connection._build`).
Realistic changes to them resolve elsewhere: codec changes land in `keyset.py` (count 1);
node resolution is Strawberry's stable `cls.resolve_node` API shared with every other
connection path; offset-prefix avoidance is one documented decision at each site. The
byte-parity between the two arms is enforced live by the wire-parity suites, so a helper
would add indirection between two dispatch arms without owning a drifting rule. Kept separate.

Scratch experiment: `docs/dry/temp-tests/connection/check_finalize_order_equivalence.py`
(untracked) ran all seven `_finalize_queryset` order arms (unordered, Meta.ordering,
explicit unique/non-unique, keyset default, explicit-beats-keyset, declared==implicit)
through the refactored code — all equivalent to the pre-refactor branch semantics.

## Opportunities

### 1. Connection default-order precedence selected at two sites

- **Repeated responsibility:** which ORDER BY a connection paginates under by default —
  keyset declared `cursor_field` when no explicit orderBy won, else explicit orderBy /
  model `Meta.ordering` made total — the cursor-parity invariant's order leg.
- **Sites:** `optimizer/nested_planner.py::plan_connection_relation` step (d);
  `connection.py::_finalize_queryset` step 5.
- **Evidence:** posited changes above force both sites (count 2); the planner comment
  itself calls the order "shared with the resolve-time pipeline", yet the precedence
  ladder around the hoisted `deterministic_order` was re-spelled per site. The resolve
  site additionally skipped `deterministic_order` on its keyset early return while the
  planner ran it — identical today only because validated-unique input returns unchanged.
- **Owner:** `optimizer/plans.py` (the Decision-11 home of `deterministic_order` /
  `ends_in_unique_column`, importable by both sites cycle-free).
- **Consolidation:** new `effective_connection_order(cursor_field, explicit, model)`
  stating the ladder once; both call sites reduced to one call. Behavior preserved
  including the implicit-Meta.ordering subtlety (empty `query.order_by` ≠ unordered).
- **Proof:** `tests/optimizer/test_plans.py::TestEffectiveConnectionOrder` (four arms);
  existing finalize tests (`tests/test_connection.py`) and fast-path wire-parity +
  keyset suites keep pinning plan/resolve parity end-to-end. Equivalence probe above.
- **Risks / non-goals:** the planner must keep never seeing sidecar-bearing windows
  (Decision 6) — the helper's explicit-beats-keyset arm is then inert there by
  construction, matching prior behavior; `first`-page SQL shapes and window bounds are
  untouched.

### 2. Async-only-iterable sync-misuse guard spelled per field flavor

- **Repeated responsibility:** "an AsyncIterable-only resolver source under synchronous
  GraphQL execution is a `SyncMisuseError` naming the recourse."
- **Sites:** `connection.py::_build_connection_resolver` (inner
  `_require_async_iterable_context(source)`), `list_field.py::_require_async_iterable_context()`
  + isinstance branch at its call site, raw predicate again in
  `resource_policy.py::bounded_rows_async`. Wording had already drifted between the twins.
- **Evidence:** wording/recourse or detection-shape changes force both guards (count 2).
  The structural split (isinstance inside vs outside the guard) was an accident of call
  shape, not two rules.
- **Owner:** `utils/querysets.py` — the established neutral home beside
  `SyncMisuseError`, `reject_async_in_sync_context`, and `sync_pipeline_recourse`.
- **Consolidation:** `is_async_only_iterable(value)` (one spelling of the predicate;
  QuerySet is both protocols so never async-only) + `reject_async_iterable_in_sync_context(value, *, flavor_noun)`
  (one rule + one recourse sentence, flavor subject parameterized); `bounded_rows_async`
  now reads the shared predicate. Both flavors' messages keep their subject noun;
  connection's recourse tail unified to the list-field wording ("async iterable
  resolvers"), which is also the accurate umbrella term. Nothing pins the old tail.
- **Proof:** new unit tests in `tests/utils/test_querysets.py` (predicate arms,
  flavor-named raises, sync pass-through, async-context no-op); the existing through-schema
  pins stay green-by-construction (`tests/test_connection.py` sync-misuse trio,
  `tests/test_list_field.py` async-iterable guard, async-executor consumption tests on
  both flavors).
- **Risks / non-goals:** `reject_async_in_sync_context` (awaitables from sync HOOKS)
  remains a deliberately distinct contract; the list field's branching to its async
  completion path stays local (control flow, not the rejected rule).

## Implementation (Worker 1)

- `optimizer/plans.py`: added `effective_connection_order`; docstring states the ladder
  and the implicit-Meta.ordering trap.
- `connection.py`: `_finalize_queryset` now selects the order via the shared helper
  (keyset early-return folded into one tail); deleted the local
  `_require_async_iterable_context`; imports swapped (`effective_connection_order` in,
  `deterministic_order`/`SyncMisuseError` out — both unused after the change).
- `optimizer/nested_planner.py`: step (d) calls the shared helper; import swapped.
- `utils/querysets.py`: added `is_async_only_iterable` + `reject_async_iterable_in_sync_context`
  (strawberry context probe added to the module's cycle-safety dependency list).
- `list_field.py`: both wrapper branches use the shared predicate/guard; local helper
  and dead imports removed.
- `resource_policy.py`: `bounded_rows_async` reads the shared predicate.
- Permanent tests: `tests/optimizer/test_plans.py` (`TestEffectiveConnectionOrder`),
  `tests/utils/test_querysets.py` (four unit tests). Orphan-import sweep done (ruff F401
  clean; grep confirms no remaining references to the removed locals).
- `uv run ruff format .` + `uv run ruff check --fix .` + trailing-comma `--check`: clean.
- pytest DEFERRED per AGENTS.md (no run without maintainer authorization); coverage of
  every touched branch is carried by the permanent tests listed above.

## Judgment

The file is heavily pre-consolidated — its window/keyset/count policies already route
through single owners in `utils/connections.py`, `keyset.py`, and `optimizer/plans.py`,
and most apparent twins (pipelines, count attachers, keyset contexts) are intentional
color or cache boundaries. Two genuine system-level duplications remained and were
consolidated at their true owners: the connection default-order precedence (completing
the spec-033 Decision-11 hoist across the plan/resolve boundary) and the async-only
sync-misuse guard (unifying two read-flavor twins whose wording had already drifted).
Everything else was disproved with counts of one or rejected as intentional repetition.

## Independent verification (Worker 2)

Re-traced both consolidations from the cycle baseline `7d2292c` (scoped diff: the six production
files + two new test files, +200/−91). Verdict: **verified**.

Consolidation 1 — `effective_connection_order` equivalence, every input class:

- Non-keyset target (`cursor_field is None`): old and new both compute
  `deterministic_order(explicit or Meta.ordering, model)` — same branch.
- Keyset target WITH explicit `orderBy:`: the old early-return required `not explicit`, so it fell
  through to the identical ladder; new behavior identical.
- Keyset target, default page: both sides return the raw `cursor_field` tuple. The one residual
  divergence — when `cursor_field` equals `Meta.ordering` exactly, the new tail skips the now-redundant
  `.order_by()` and leaves implicit ordering — compiles to the same ORDER BY rows, and the PRE-EXISTING
  defensive no-order branch in `_keyset_order_state` (connection.py #"if not effective or effective ==
  state.cursor_field", present verbatim in baseline `7d2292c`) re-applies `state.cursor_field`, so the
  final slicing queryset state converges byte-identically. Offset connections cannot reach that arm.
- Determinism: pk tiebreak unchanged for the ladder arms; the keyset arm skipping
  `deterministic_order` is safe because finalization validates a unique terminal
  (`finalizer.py` → `keyset.validate_cursor_field_columns`) and planning only runs against finalized
  targets (sibling `_keyset_cursor_context` already assumes this), so `deterministic_order(cursor_field)`
  was identity at the old plan site.
- Shape safety: `definition.cursor_field` is `tuple[str, ...] | None`, validated non-empty at class
  creation (`types/base.py::_validate_cursor_field`) — `tuple(cursor_field)` can never explode a string
  or yield `()`.
- Planner-side explicit-beats-keyset arm inert by construction, as claimed: per-payload sidecar gate
  `has_connection_sidecar_kwargs` (nested_planner.py #"if has_connection_sidecar_kwargs(key_arguments)")
  fallbacks any `orderBy:` payload before step (d), and child-queryset construction adds no `.order_by`.

Boundaries: `plans.py` imports only django / `..exceptions` / `..utils.connections` /
`.join_taxonomy` — no import of `nested_planner` or `connection`, so no cycle; `nested_planner`
already imported from `plans`; `plans.py` is the Decision-11 home of `deterministic_order`, which the
new helper wraps — correct owner. Tests live in `tests/optimizer/` + `tests/utils/` (package tier,
example models as fixtures, matching each file's existing conventions); the new production lines stay
end-to-end covered by `test_fast_path_wire_parity_with_pipeline` (tests/test_relay_connection.py:1406),
the keyset parity suite, and the four sync-misuse pins.

Consolidation 2 — guard/predicate equivalence:

- connection flavor: predicate, `in_async_context` probe (same `strawberry.utils.inspect` symbol),
  exception type, call position (after `resolver()` return, before the pipeline) all preserved;
  recourse tail unified "async-generator" → "async iterable" resolvers with ZERO remaining references
  to the old tail anywhere (grep: package, tests, examples).
- list_field declared-async-generator branch: calling an async-generator function always yields an
  object with `__aiter__` and no `__iter__`, so `is_async_only_iterable(source)` is statically True and
  the new guard reduces exactly to the old context-only check. Plain-def branch: isinstance-pair-outside
  + context-check-inside folds into one logically identical call. `DjangoListField` message text
  byte-identical.
- `resource_policy.bounded_rows_async`: needed ONLY the predicate — its job is bound dispatch, not
  rejection — and that is what it got; the old condition is exactly De Morgan of
  `not is_async_only_iterable(result)`.
- New import edge `resource_policy → utils.querysets` is cycle-free (`querysets` imports django,
  `..exceptions`, `..utils.context`, `strawberry.utils.inspect` only).

Orphan sweep: `_require_async_iterable_context` and the removed imports leave no references anywhere
(package, tests, `examples/`); ruff check + format clean on all eight scoped files. Scratch probe
re-read: seven arms including declared==implicit (arm 7 tolerates both qs-states but asserts row-order
equivalence, consistent with the slicer-convergence analysis above).

Single-edit-site recounts (my own posited changes): (a) "point the recourse at `execute_async` instead
of `await schema.execute`" — pre-change forced BOTH flavor guards (their drifted tails prove it),
post-change forces one helper + its test: 2 → 1. (b) "also treat AsyncIterator-only shapes as
async-only" — pre-change forced two guards plus the `bounded_rows_async` dispatch predicate: 3 sites,
post-change one predicate: 3 → 1. Recorded counts hold. Matrix discharge re-checked against the real
surface: axes searched with named terms; the axis-2 color-boundary rejection and axis-4 upstream-codec
rejection stand on behavior I independently confirmed. pytest deferred per AGENTS.md.
