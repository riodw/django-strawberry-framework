# Review: `django_strawberry_framework/relay.py`

Status: verified

## DRY analysis

- **`resolve_nodes` per-type dispatch + check + stamp loop is duplicated between the sync and async branches of `DjangoNodesField._resolve`.** The sync comprehension (`relay.py:401-411`) and the async `_gather` loop body (`relay.py:384-397`) compute the identical `per_type[t] = [_stamp_node_type(t, n) for n in _check_nodes_result(t, resolve_nodes(...), pks)]` shape; the only difference is the `if inspect.isawaitable(result): result = await result` step the async branch adds. This is the same sync/async-twin pattern `types/relay.py` keeps as deliberate siblings (`_resolve_nodes_default` / `_resolve_nodes_async`), and the awaitable-unwrap cannot be lifted into the sync branch without making it a coroutine. **Defer until a third per-type dispatch site lands (e.g. a connection-backed nodes resolver); then extract `_build_per_type(resolved_type, result_or_awaitable, pks)` and have only the await-vs-not wrapper differ.** Acting now would either force the sync branch through an `async`-shaped helper or introduce an `isawaitable` no-op on the sync path — net negative for two call sites.
- **`_node_fields_declared.append("DjangoNodeField" | "DjangoNodesField")` repeats the factory-name string literal at the append site (`relay.py:277`, `relay.py:345`) and again at the `field="..."` validator call (`relay.py:276`, `relay.py:344`).** Per the shadow repeated-literal scan (`3x DjangoNodeField`, `3x DjangoNodesField`). The third occurrence each is the `noqa` comment. Only emptiness of the ledger is load-bearing (module docstring `relay.py:69-73`), so the string content is debugging-only and the two-site-per-factory repeat is inside a single small factory body each. **None to act on — defer with trigger: if a third factory in this module ever appends to the ledger, hoist a `_FIELD_NAME` local per factory so the validator-call and the append share one binding.** Not worth a module constant for two factories today.

## High:

None.

## Medium:

None.

## Low:

### `_coerce_pk_or_none` swallows a coercible-but-out-of-range value silently into `null`

`_coerce_pk_or_none` (`relay.py:133-136`) maps any `ValueError`/`ValidationError` from `field.to_python` to `None` ("identifies no row"). For an `AutoField`/`BigAutoField` pk a client id like `"99999999999999999999"` (larger than the column can hold) coerces cleanly through `to_python` (it is a valid integer string) and is treated as a normal missing row — correct. The genuinely-uncoercible case (`"abc"` on an int column) is also correctly `null`. This is the documented Decision-5 / Revision-7-P2 contract and the no-existence-oracle property holds. **No defect** — flagged only to record that the catch is intentionally broad and the `null`-on-`ValidationError` path (distinct from `ValueError`) is exercised by NodeID-attr columns whose `to_python` raises `ValidationError` rather than `ValueError`. Forward-looking note: **if a future field type raises a coercion error that is neither `ValueError` nor `ValidationError` (e.g. `TypeError` from a custom field), it would escape this catch and surface raw**; revisit the except tuple when the first custom-`NodeID`-column field with a non-standard `to_python` lands.

### `_check_nodes_result` materializes a generator override but does not re-guard a second non-`__len__` return

`_check_nodes_result` (`relay.py:216-217`) handles a generator/iterator `resolve_nodes` override by `list()`-materializing when `__len__` is absent, then length-checks. This is correct and the `IndexError`-avoidance rationale is sound. The materialized `result` is then iterated again by the caller's comprehension (`relay.py:394-396` / `relay.py:402-408`) — safe because `_check_nodes_result` returns the materialized `list`, not the exhausted generator. **No defect** — recording that the return-the-materialized-list contract (`relay.py:225`) is load-bearing and a future refactor that drops the `return result` (relying on in-place mutation) would silently re-exhaust a generator. Defer; correct as written.

## What looks solid

### DRY recap

- **Existing patterns reused.** `_validate_node_target` (`relay.py:157-174`) is a thin wrapper delegating to the shared `list_field.py::_validate_relay_djangotype_target` (`list_field.py:99-122`), realizing the 0.0.9 DRY win with `DjangoConnectionField` (`connection.py:1198`); no re-implementation of the five target guards. `_model_for` / `decode_global_id` / `_NODE_TYPE_HINT_ATTR` are imported from `types/relay.py` (`relay.py:64`), not duplicated. The `_node_fields_declared` ledger mirrors the `_helper_referenced_filtersets` precedent and is co-cleared by `registry.clear()` (`registry.py:523-527`) and consumed by the finalizer's no-Node-types gate (`finalizer.py:656-661`) — the wiring is coherent across all three sites.
- **New helpers considered.** A unified per-type dispatch helper across the sync/async `DjangoNodesField` branches was evaluated and deferred (see DRY analysis) — the awaitable-unwrap asymmetry makes a two-site extraction net-negative, matching the `_resolve_node_default` / `_resolve_node_async` sibling precedent.
- **Duplication risk in the current file.** The `DjangoNodeField` / `DjangoNodesField` factory-name literals (3x each per the shadow scan) are debugging-only ledger entries, not dispatch keys; the repeat is intentional and bounded to one small factory body each.

### Other positives

- **No-existence-oracle invariant is airtight.** Decode (`_decode_or_graphql_error`, `relay.py:289`/`359`) and pk-coercion (`_coerce_pk_or_none`, `relay.py:293`/`368`) both run on payload data ONLY, before any queryset is touched. Hidden, missing, and uncoercible-pk ids all resolve to `null` via the SAME `resolve_node(s)` path under `required=False` (`relay.py:302`, `relay.py:391`/`406`) — a hidden row and a missing row are indistinguishable to the client, and an uncoercible literal short-circuits to `null` with zero DB access (`relay.py:294-296`, `relay.py:369-371`). The GLOSSARY's "hidden and missing paths share one queryset code path — no existence leak" claim is satisfied.
- **`GLOBALID_INVALID` boundary is correctly scoped.** `_decode_or_graphql_error` (`relay.py:76-97`) wraps ONLY the `decode_global_id` call; the resolver's `_check_typed_match` and `resolve_node(s)` dispatch run outside it (`relay.py:290-291` comment), so a `SyncMisuseError` (a `ConfigurationError` subclass) from a sync/async-`get_queryset` misconfiguration surfaces as itself and is never mislabeled `GLOBALID_INVALID`. The extensions code is applied exactly at the one boundary the spec assigns it; `_check_typed_match` deliberately carries no code (`relay.py:146`).
- **Per-type batching, order preservation, duplicates, and null holes are all correct.** `decoded` is built for every id before any query (`relay.py:359`); the typed-form match runs across the full decoded list so a wrong-type id anywhere fails the whole field (`relay.py:360-361`). Grouping is insertion-ordered with `setdefault`, duplicates preserved, uncoercible positions reserved as `None` holes that never enter `pk__in` (`relay.py:365-374`). `_interleave` (`relay.py:177-196`) reassembles by `(type, within-group index)`, and `_check_nodes_result` (`relay.py:199-225`) converts a shrunk/duplicate-collapsed override return into a named `ConfigurationError` rather than `IndexError` or silently-wrong rows — the positional 1:1 contract is enforced, not assumed.
- **`get_queryset` honoring and sync/async.** Both factories dispatch via the `resolve_node` / `resolve_nodes` *classmethods* (`relay.py:302`, `relay.py:391`/`406`), preserving consumer overrides and routing through the visibility-aware defaults in `types/relay.py` that await async `get_queryset` hooks. The async branch uses `inspect.isawaitable` to await only when the result is actually awaitable (`relay.py:303`, `relay.py:392`) — never unconditionally — so a synchronous consumer override under async context is handled. Sequential awaits (not `asyncio.gather`) respect Django async-ORM connection safety (`relay.py:379-381`). The empty-`ids` fast path returns `[]` with zero DB access (`relay.py:354-356`).
- **Multi-type-model `__typename` disambiguation.** `_stamp_node_type` (`relay.py:228-252`) carries the decode-routing decision through to graphql-core's concrete-type selection via `_NODE_TYPE_HINT_ATTR`, honored by `install_is_type_of`'s closure (`types/relay.py:112-116`). The `contextlib.suppress(AttributeError)` for `__slots__`-rejecting consumer objects is a sound best-effort fallback to pre-032 isinstance behavior, and the async-result stamp rides inside `_await_and_stamp` (`relay.py:255-257`) so the stamp applies after the await.
- **Coercion targets the resolution field, not `_meta.pk`.** `_coerce_pk_or_none` (`relay.py:124-132`) coerces against `resolve_id_attr()`'s field — the same column the resolver filters on — falling back to the raw string for a non-concrete-model NodeID attr. This correctly handles the `id: relay.NodeID[...]` non-pk-column escape hatch and the composite-pk case where `_meta.pk` has no single-column `to_python`. The `"007" -> 7` mis-typing trap is explicitly avoided.

### Summary

`relay.py` is a clean, carefully-reasoned implementation of the root Relay refetch surface. The two load-bearing invariants — no-existence-oracle (decode/coerce before any query, hidden/missing/uncoercible all collapse to `null`) and the `GLOBALID_INVALID` boundary scoped to the decode call only — are both correct and well-documented at the source. Per-type batching, order preservation, duplicate handling, null holes, the positional 1:1 override contract, `get_queryset` honoring, and sync/async dispatch are all sound. No High or Medium findings; two Lows are forward-looking notes on intentionally-broad error catches, neither a defect today. The single deferred DRY opportunity (sync/async per-type dispatch twin) is correctly left as a sibling pair matching the established `types/relay.py` precedent. GLOSSARY entries `#djangonodefield` / `#djangonodesfield` are accurate — no drift.

## GLOSSARY drift quick-check

Grepped `docs/GLOSSARY.md` for `DjangoNodeField`, `DjangoNodesField`, `GLOBALID_INVALID`, `decode_global_id`, `resolve_node`. The `#djangonodefield` entry (GLOSSARY line 361) and `#djangonodesfield` entry (line 369) accurately describe both forms, the `required=False` nullable-by-contract dispatch, server-side strategy decode, `get_queryset` honoring, the hidden/missing shared-code-path no-leak claim, `GLOBALID_INVALID` extensions code, the typed-form wrong-type `GraphQLError`, the finalize-time no-Node-types `ConfigurationError`, the `strawberry.Schema(types=[...])` engine note, per-type batching, positional `null` holes, duplicate support, whole-field failure on malformed/wrong-type, and the deliberately-uncapped batch. All match the source. **No stale prose; no replacement text required.**

---

## Fix report (Worker 2)

Consolidated single-spawn (no-findings file, REVIEW shape #1 in substance). High 0 / Med 0 / Low 2, both Lows forward-looking (defer-with-trigger), both DRY bullets forward-looking. No in-cycle edit required.

Before recording the no-op I independently re-checked the load-bearing invariants Worker 1 verified against source (relay.py is unchanged-since-baseline — `git diff 0872a20f -- django_strawberry_framework/relay.py` is empty):

- **No-existence-oracle (deepest re-check).** Traced `required=False` end to end: `_decode_or_graphql_error` (`relay.py:289`/`359`) and `_coerce_pk_or_none` (`relay.py:293`/`368`) run on payload data only, before any queryset. Uncoercible pk short-circuits to `null`/positional-hole with zero DB access (`relay.py:294-296`, `relay.py:369-371`). For the rows that ARE queried, dispatch flows through `resolve_node` → `_resolve_node_default` → `qs.first()` (`types/relay.py:820`) and `resolve_nodes` → `_order_nodes` → `index.get(key)` returning `None` for missing keys (`types/relay.py:783`). A hidden row (filtered out by `apply_type_visibility`) and a genuinely-missing row are therefore indistinguishable at the resolver layer — all three families (hidden/missing/uncoercible) collapse to the same `null`. Invariant holds.
- **`GLOBALID_INVALID` boundary.** Confirmed `decode_global_id` (`types/relay.py:634-747`) raises ONLY `ConfigurationError` for every failure mode (input gate, malformed-base64 parse, empty slot, unresolvable label/name, strategy-forbidden). `_decode_or_graphql_error` (`relay.py:91-97`) catches exactly `ConfigurationError` → `GLOBALID_INVALID`, wrapping only the decode call; `_check_typed_match` + `resolve_node(s)` dispatch run outside the try (`relay.py:290-292`), so a `SyncMisuseError` (`ConfigurationError` subclass) surfaces as itself, never mislabeled. Invariant holds.
- **Per-type batching / order / holes / duplicates.** `decoded` built for all ids before any query (`relay.py:359`); typed-match across the full decoded list (`relay.py:360-361`); `setdefault` insertion-ordered grouping with duplicates preserved and uncoercible positions reserved as `None` holes that never enter `pk__in` (`relay.py:365-374`); `_interleave` reassembles by `(type, within-group index)` (`relay.py:177-196`); `_check_nodes_result` (`relay.py:199-225`) enforces the positional 1:1 override contract with a named `ConfigurationError`. Invariant holds.
- **`get_queryset` honoring + sync/async.** Both factories dispatch via the `resolve_node`/`resolve_nodes` *classmethods* (`relay.py:302`, `relay.py:391`/`406`), preserving consumer overrides and routing through the visibility-aware async-`get_queryset`-awaiting defaults; `inspect.isawaitable` awaits only when the result is actually awaitable (`relay.py:303`, `relay.py:392`). Invariant holds.
- **Ledger wiring (whole-system).** `_node_fields_declared` (`relay.py:73`) appended by both factories (`relay.py:277`, `relay.py:345`), co-cleared by `registry.clear()` (`registry.py:523-527`), consumed by the finalizer no-Node-types gate via a PLAIN (no try/except) function-local import (`finalizer.py:656-661`). Coherent across all three sites.

### Files touched
- None. relay.py is correct as written; no source/test/comment defect found.

### Tests added or updated
- None (no logic change).

### Validation run
- `uv run ruff format .` — pass / no-changes (265 files left unchanged).
- `uv run ruff check --fix .` — pass (All checks passed; standing COM812 formatter-conflict warning only).
- No pytest (per AGENTS.md / role file). Verified upstream contracts by reading `types/relay.py`, `registry.py`, `types/finalizer.py` rather than executing.

### Notes for Worker 3
- Shadow overview used: `docs/shadow/django_strawberry_framework__relay.overview.md` (read-only aid; line numbers cited above are original-source line numbers, not shadow).
- No intentionally-rejected findings — every artifact premise re-verified true against source.
- Deferred findings (forward-looking, no action): Low 1 (`_coerce_pk_or_none` except-tuple — trigger: first custom-`NodeID` column whose `to_python` raises neither `ValueError` nor `ValidationError`); Low 2 (`_check_nodes_result` materialized-list return contract — correct as written, trigger: a future refactor dropping `return result`); DRY 1 (sync/async per-type dispatch twin — trigger: a third per-type dispatch site); DRY 2 (`_FIELD_NAME` local hoist — trigger: a third factory appending to the ledger).
- relay.py existed at baseline `0872a20f` and is unchanged since; the cycle diff for relay.py is empty (no tracked file edited this cycle).

---

## Verification (Worker 3)

### Logic verification outcome
Bare `fix-implemented` → terminal verify of a shape #1 no-findings consolidated cycle on the substantial NEW 0.0.9 file. Independent re-inspection (not a rubber stamp) confirmed every load-bearing invariant against source:

- **No-existence-oracle (independently re-derived).** Decode + coerce run on payload data only, before any query. Uncoercible-pk short-circuits to `None`/positional-hole with zero DB access (`relay.py:294-296`, `relay.py:369-371`). For queried rows: `_resolve_node_default` filters via `apply_type_visibility_sync` (`types/relay.py:818`) so a hidden row is removed before `qs.first()` (`types/relay.py:820`) and returns `None`; a genuinely-missing row equally returns `None` from `.first()`. Batch path: `_order_nodes` `required=False` emits `index.get(key)` = `None` for missing keys (`types/relay.py:783`). All three families (hidden / missing / uncoercible) collapse to the SAME `null` and are indistinguishable at the resolver layer. **Holds.**
- **GLOBALID_INVALID boundary (independently re-derived).** Read every raise in `decode_global_id` (`types/relay.py:684/693/703/714/720/731/741`) — all `ConfigurationError`; the only non-`ConfigurationError` raise in the module is `_order_nodes`'s `model.DoesNotExist` (`:779`), outside the decode call. `_decode_or_graphql_error` (`relay.py:91-97`) wraps the decode call ONLY and catches exactly `ConfigurationError` → `GLOBALID_INVALID`. Confirmed `SyncMisuseError(ConfigurationError, RuntimeError)` (`utils/querysets.py:35`) IS a `ConfigurationError` subclass — so the boundary scope is genuinely load-bearing: keeping `_check_typed_match` + `resolve_node(s)` dispatch OUTSIDE the try (`relay.py:290-292`) is what stops a dispatch-time `SyncMisuseError` from being mislabeled `GLOBALID_INVALID`. **Holds.**
- **nodes batching / order / holes / duplicates.** `decoded` built for all ids before any query (`relay.py:359`); typed-match across the full decoded list fails the whole field on a wrong-type id anywhere (`relay.py:360-361`); `setdefault` insertion-ordered grouping with duplicates preserved, uncoercible positions reserved as `None` holes never entering `pk__in` (`relay.py:365-374`); `_interleave` reassembles by `(type, within-group index)` (`relay.py:177-196`); `_check_nodes_result` enforces the positional 1:1 override contract (`relay.py:199-225`). **Holds** — see Temp test below for the live probe.
- **get_queryset honoring + sync/async dispatch.** Both factories dispatch via the `resolve_node`/`resolve_nodes` *classmethods* (`relay.py:302`, `relay.py:391`/`406`), preserving consumer overrides; `inspect.isawaitable` awaits only when actually awaitable (`relay.py:303`, `relay.py:392`); async branch uses sequential awaits (`relay.py:379-381`) for Django async-ORM safety; empty-`ids` fast path returns `[]` with zero DB (`relay.py:354-356`). **Holds.**
- **Ledger wiring.** `_node_fields_declared` (`relay.py:73`) appended by both factories (`relay.py:277/345`), co-cleared by `registry.clear` (`registry.py:523-527`), consumed by the finalizer no-Node-types gate via a plain (no try/except) function-local import (`finalizer.py:656-661`). Coherent across all three sites.

### DRY findings disposition
Both DRY bullets genuinely forward-looking. DRY 1 (sync/async per-type dispatch twin) correctly deferred — the `isawaitable` await asymmetry makes a two-site extraction net-negative and matches the established `types/relay.py` `_resolve_node_default`/`_resolve_node_async` sibling precedent; trigger = a third per-type dispatch site. DRY 2 (`_FIELD_NAME` local hoist) correctly deferred — two-site-per-factory string literals are debugging-only ledger entries (only emptiness is load-bearing); trigger = a third factory appending to the ledger. Both Lows are forward-looking notes on intentionally-broad error catches, neither a defect today.

### Temp test verification
- `docs/review/temp-tests/relay/probe_interleave.py` (gitignored; deleted after the run). Drove the pure positional reassembly math — the deepest batch invariant — under the worst-case mix: input `[A:1, B:9, A:1(dup), A:bad(uncoercible), B:2, A:3]` with `A:3` simulated hidden/missing. Result reassembled exactly to input order `["A1","B9","A1",None,"B2",None]` — duplicate `1` resolved per-position, the uncoercible hole and the missing-pk hole both `null`, multi-type interleave order preserved. Separately confirmed `_check_nodes_result`'s 1:1 enforcement: a shrunk/dup-collapsed override return (the `filter(pk__in=...)` trap) raises, and a generator (no `__len__`) override is materialized then length-checked. All assertions passed.
- Disposition: deleted. No new behavior bug surfaced; the existing source contract is correct, so no promotion to the permanent suite warranted (no logic change this cycle).

### Sibling-cycle attribution
Cycle diff `git diff 0872a20f -- django_strawberry_framework/relay.py` is **empty** — confirms the shape #1 no-op. Owned-path `--stat` dirty files all attribute to CLOSED sibling cycles, not relay.py:
- `conf.py` → `rev-conf.md` (Status: verified, `[x]` at review-0_0_9.md:70).
- `exceptions.py` → `rev-exceptions.md` (Status: verified, `[x]` at review-0_0_9.md:72).
- `list_field.py` → `rev-list_field.md` (Status: verified, `[x]` at review-0_0_9.md:73).
- `docs/GLOSSARY.md` (single line: the `DjangoConnection` entry rewrite) → owned by the `rev-connection.md` connection.py cycle, not relay.py.

`relay.py`'s own "Files touched: None" claim holds. Deleted root `feedback2.md`/`feedback3.md` are AGENTS.md #33 concurrent-maintainer work — left untouched.

### Validation run
- `git diff 0872a20f -- django_strawberry_framework/relay.py` — empty (no-op confirmed).
- `uv run ruff check django_strawberry_framework/relay.py` — All checks passed.
- `uv run ruff format --check django_strawberry_framework/relay.py` — 1 file already formatted (standing COM812 formatter-conflict warning only).
- `git diff 0872a20f -- CHANGELOG.md` — empty; `Not warranted` disposition cites BOTH AGENTS.md #21 and the active plan's silence; no-op cycle has nothing consumer-visible to record. Correct state.
- No pytest (per AGENTS.md / role file).

### Verification outcome
`cycle accepted; verified` — sets top-level `Status: verified` AND marks the checklist box.

---

## Comment/docstring pass

No comment/docstring edit. The module docstring (`relay.py:1-47`) and every helper docstring accurately describe the final (and only) behavior — re-read during the invariant re-check above, no stale or contradicting prose found. The two forward-looking Lows are notes about intentionally-broad error catches, not docstring drift.

### Files touched
- None.

### Per-finding dispositions
- Low 1 (`_coerce_pk_or_none` swallows out-of-range value): forward-looking note, no defect today; docstring (`relay.py:101-123`) correctly documents the broad `(ValueError, ValidationError)` catch and the no-existence-oracle rationale. No change.
- Low 2 (`_check_nodes_result` materialized-list return): forward-looking note, correct as written; docstring (`relay.py:200-215`) and the load-bearing `return result` (`relay.py:225`) match. No change.

### Validation run
- `uv run ruff format .` — pass / no-changes.
- `uv run ruff check --fix .` — pass.

### Notes for Worker 3
Comment pass folded into the consolidated spawn; no logic change preceded it, so no docstring contract could have shifted.

---

## Changelog disposition

### State
`Not warranted`.

### Reason
Cites BOTH required grounds: (1) AGENTS.md #21 — "Do not update CHANGELOG.md unless explicitly instructed"; and (2) the active review plan is silent on changelog authorization for this per-file cycle. Per the role file, per-file and folder-pass cycles are NEVER the authorising scope — any CHANGELOG drift is forwarded to the project pass. This cycle made no behaviour change (no-op, no source/test/comment edit), so there is nothing consumer-visible to record regardless.

### What was done
No `CHANGELOG.md` edit.

### Validation run
- `uv run ruff format .` — pass / no-changes.
- `uv run ruff check --fix .` — pass.

---

## Iteration log

_None yet._
