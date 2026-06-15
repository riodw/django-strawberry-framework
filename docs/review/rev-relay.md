# Review: `django_strawberry_framework/relay.py`

Status: verified

## DRY analysis

- None — the module is already single-sited against its canonical helpers. The two factories (`DjangoNodeField` / `DjangoNodesField`) share every reusable seam: decode-to-wire-error via `_decode_or_graphql_error`, target validation via the cross-module `_validate_node_target` → `list_field.py::_validate_relay_djangotype_target`, pk coercion via `_coerce_pk_or_none`, typed-match via `_check_typed_match`, node stamping via `_stamp_node_type`, and order reassembly via the single `_interleave` that serves both the sync branch and the gathering coroutine. The remaining per-factory text (the two `_resolve` bodies, the sync vs async-gather split in `DjangoNodesField`) is genuinely divergent control flow (single id vs batch grouping), not a near-copy. The 3x `"DjangoNodeField"` / 3x `"DjangoNodesField"` literals flagged by the static helper are the decorator `noqa` text, the consumer-facing example, and the `field=`/ledger argument — distinct concerns, not a hoistable constant (folding them would couple the ledger key to the noqa comment text).

## High:

None.

## Medium:

None.

## Low:

### `_node_fields_declared` ledger entries are append-only with no per-factory dedup (intentional; pre-empt re-flag)

`_node_fields_declared` (relay.py #"_node_fields_declared: list[str]") is appended once per factory call by both `DjangoNodeField` and `DjangoNodesField`, and never deduplicated. The docstring is explicit that "only emptiness is load-bearing, the factory-name entries aid debugging" — so an unbounded grow under repeated declarations is by design (it mirrors the `_helper_referenced_filtersets` precedent and is co-cleared by `registry.clear()`, confirmed at `registry.py` wiring in cycle 8). No action: this is a deliberate marker list, not a set, and the finalize check reads only `bool(...)`. Recorded only to stop a future cycle re-flagging the missing dedup as a leak.

## What looks solid

### DRY recap

- **Existing patterns reused.** `_validate_node_target` (relay.py:157-174) is a thin wrapper over the cross-module `list_field.py::_validate_relay_djangotype_target` (verified at `list_field.py:99-122`), passing `None` for the resolver seam because a refetch field has no `resolver=` — correct, since the four base guards plus the Relay-shaped fifth do not need it. `_decode_or_graphql_error` is the single decode→`GLOBALID_INVALID` chokepoint consumed by both factories' `_resolve` bodies. `_interleave` is the one order-reassembly implementation shared by the sync dict-comprehension path and the `_gather` coroutine. Async dispatch reuses the package's `inspect.isawaitable` + `in_async_context` idiom (same shape as `connection.py:345/645` and `list_field.py:165`).
- **New helpers considered.** A shared `_resolve` body for the two factories was considered and rejected: the single-id path returns one value (with a direct `_await_and_stamp` async sibling) while the batch path groups by decoded type, builds `positions`, and dispatches one `resolve_nodes` per group inside a gathering coroutine — the divergence is the whole point, so a merged body would need a mode flag that re-splits internally. A named constant for the duplicated factory-name literals was rejected (the three occurrences are distinct concerns, see DRY analysis).
- **Duplication risk in the current file.** The two `_check_typed_match` call sites (single at relay.py #"_check_typed_match(target_type, resolved)" inside `DjangoNodeField._resolve`; batch loop inside `DjangoNodesField._resolve`) and the two `_coerce_pk_or_none` call sites are intentional sibling design — the batch path must iterate, the single path must not. Not a near-copy to consolidate.

### Other positives

- **No-existence-oracle property is airtight.** Decode runs on payload data only, before any query (`_decode_or_graphql_error` wraps the decode call ONLY; the dispatch runs outside the try/except so `SyncMisuseError` — a `ConfigurationError` subclass — surfaces as itself rather than being mislabeled `GLOBALID_INVALID`). Uncoercible pks return `None` with **no query issued** (single: early `return None`; batch: reserved `positions` hole that never enters the `pk__in` group). Hidden/missing rows resolve to `null` through `required=False` dispatch. Malformed ids raise `GraphQLError(extensions={"code": "GLOBALID_INVALID"})`. The four families (hidden / missing / uncoercible / malformed) are correctly separated and none leaks row existence — matches the module docstring and Decision 5.
- **Order preservation is structurally enforced.** `_interleave` indexes per-type results by within-group position, and `_check_nodes_result` validates a `resolve_nodes` override returns a list positionally 1:1 with `pks` (materializing a generator first so the length check fires instead of a bare `len()` `TypeError`), converting the shrunk/duplicate-collapsed override mistake into a named `ConfigurationError` rather than silently-wrong rows or an `IndexError`. Duplicate input ids resolve per position via the `groups.setdefault` + `len(pks)` index scheme.
- **pk coercion targets the right column.** `_coerce_pk_or_none` coerces against `resolved_type.resolve_id_attr()` (the same field the resolution filters on), not `model._meta.pk` — correctly handling the `NodeID[...]` non-pk-column escape hatch and the `CompositePrimaryKey` case where `_meta.pk` has no single-column `to_python`. A non-concrete-field NodeID attr skips coercion and passes the raw string (pre-032 behavior). `ValueError`/`ValidationError` from `to_python` map to `None`.
- **`is_type_of` stamping closes the two-types-one-model ambiguity.** `_stamp_node_type` carries the decode-routing decision (`_NODE_TYPE_HINT_ATTR`, verified `= "_dsf_node_type_hint"` at `types/relay.py:74`, read by `install_is_type_of`'s closure) through to concrete-type selection, so a model with two registered Relay types resolves to the GlobalID-named type rather than iteration order. `None` passes through; the `contextlib.suppress(AttributeError)` makes the stamp best-effort for `__slots__` override returns — documented and correct.
- **Async/sync dispatch is per-call and correct.** Both factories use runtime `in_async_context()` (batch) / `inspect.isawaitable()` (single + batch per-group) rather than a construction-time commit, because there is no consumer resolver to inspect at construction — the deliberate, documented contrast with `connection.py`'s committed-at-construction split. `resolve_nodes` results are awaited only when actually awaitable (so a synchronous consumer override is honored, never double-wrapped). Sequential awaits (not `asyncio.gather`) for Django async-ORM connection safety. `_await_and_stamp` is the minimal async sibling that awaits then stamps without an extra coroutine layer.
- **Cross-module call shapes verified.** `decode_global_id` (`types/relay.py:634`) returns `(target_type, node_id)` and accepts `relay.GlobalID | str` — relay.py feeds it `id: strawberry.ID` (a raw string, deliberately not `relay.GlobalID`, so malformed ids reach the package instead of being rejected by Strawberry's `convert_argument`). The `resolved.resolve_node(pk, info=info, required=False)` call matches the bound default `_resolve_node_default(cls, node_id, *, info, required=False)` (`types/relay.py:787`); `resolve_nodes(info=info, node_ids=pks, required=False)` matches `_resolve_nodes_default(cls, *, info, node_ids=None, required=False)` (`types/relay.py:844`). Both call the classmethods (not the underscore defaults), preserving consumer overrides.
- **GLOSSARY accurate, no drift.** `DjangoNodeField` (GLOSSARY.md:375-381) and `DjangoNodesField` (GLOSSARY.md:383-389) describe the bare/typed forms, nullable-by-contract dispatch, the `GLOBALID_INVALID` boundary, the whole-field-fails batch semantics, the `strawberry.Schema(types=[...])` engine note, and order/duplicate handling — all matching source verbatim. Unlike the `DjangoListField` entry (cycle 6 forward), neither relay GLOSSARY entry describes the async-detection mechanism, so the package-wide `is_async_callable`-vs-`inspect.iscoroutinefunction` prose forward does NOT apply to relay.py — nothing to forward to the project pass from this file.

### Summary

`relay.py` is a thin, well-factored consumer surface over the `types/relay.py` decode/resolve internals: two factories sharing a complete set of single-sited helpers, with the only divergence being genuine single-vs-batch control flow. Every focus-area contract holds — node/nodes refetch dispatch the classmethods (preserving overrides), GlobalID decode is wrapped narrowly so `SyncMisuseError` surfaces as itself, the no-existence-oracle property is airtight across all four failure families (null for hidden/missing/uncoercible, `GraphQLError`/`GLOBALID_INVALID` for malformed), order is structurally preserved and override-validated, and async/sync dispatch is per-call by design. The cycle diff against the baseline is empty (file unchanged this cycle); all cross-module call shapes were re-verified against `types/relay.py` and `list_field.py`. No High, no Medium, one no-action Low. This is a no-source-edit cycle (shapes #1 → #5).

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — pass, no changes (267 files unchanged).
- `uv run ruff check --fix .` — pass, no changes (all checks passed).

### Notes for Worker 3
- Single Low (`_node_fields_declared` append-only ledger) is no-action: append-only is by design (only emptiness is load-bearing; co-cleared by `registry.clear()`), recorded only to pre-empt re-flagging. No edit required.
- No GLOSSARY-only fix in scope. The cycle-6 `is_async_callable`-vs-`inspect.iscoroutinefunction` GLOSSARY forward does NOT apply here: relay.py's GLOSSARY entries (GLOSSARY.md:375-389) do not describe an async-detection mechanism, and the source uses `inspect.isawaitable` / `in_async_context`, not `is_async_callable`.
- Cycle diff `git diff 97b67c45e4578a6f6f458ba10865f1c4806d1702 -- django_strawberry_framework/relay.py` is empty (file unchanged this cycle).
- Static shadow overview used: `docs/shadow/django_strawberry_framework__relay.overview.md`.

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern.

No comment/docstring changes warranted. The module docstring and per-symbol docstrings accurately describe behavior (verified against source: decode-scope narrowing, nullable-by-contract dispatch, the four failure families, the stamp best-effort caveat, the per-call async dispatch rationale). No stale comments, no obsolete TODOs (0 TODO anchors), no docstrings promising unimplemented behavior.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern.

Not warranted — no source edits made this cycle (review-only). Per `AGENTS.md` ("Do not update CHANGELOG.md unless explicitly instructed") and the active plan (`docs/review/review-0_0_10.md`), which is silent on changelog edits for review cycles.

---

## Verification (Worker 3)

Shape #5 (no-source-edit) terminal verification. Bare `Status: fix-implemented` incoming → terminal-verify.

### Logic verification outcome

Independently re-derived every security-relevant invariant against source (`relay.py`) and its callees — not the artifact's prose.

- **No-existence-oracle (all four failure families):** `_decode_or_graphql_error` (relay.py #"return decode_global_id(gid)") wraps the decode call ONLY; both `_resolve` bodies run `_check_typed_match` / `_coerce_pk_or_none` / dispatch OUTSIDE the try/except, so `SyncMisuseError` (a `ConfigurationError` subclass) surfaces as itself, never mislabeled `GLOBALID_INVALID`. Uncoercible pk → `None` with NO query: single path early `return None` (relay.py #"Uncoercible literal"); batch path appends a `None` to `positions` and `continue`s before `groups.setdefault`, so the hole never enters a `pk__in` group. Hidden/missing rows → `null` via `required=False` dispatch. Malformed/undecodable ids → `GraphQLError(extensions={"code": "GLOBALID_INVALID"})`. Confirmed `decode_global_id` is `-> tuple[type, str]` at `types/relay.py:634`. Property is airtight.
- **Order preservation for nodes(ids:):** `_interleave` indexes per-type results by `position[1]` (within-group index); `positions` is built in input order with `None` holes. `_check_nodes_result` materializes a generator (`list(result)` when no `__len__`) THEN length-checks 1:1 against `pks`, raising a named `ConfigurationError` rather than `IndexError`/silently-wrong rows. Duplicate ids resolve per position via `groups.setdefault(resolved, [])` + `positions.append((resolved, len(pks)))`. Structurally enforced.
- **Async/sync dispatch correctness:** per-call (`in_async_context()` for the batch branch split, `inspect.isawaitable()` for single + per-group), not committed-at-construction — correct, since there is no consumer resolver to inspect at factory time. `resolve_nodes`/`resolve_node` results awaited ONLY when actually awaitable (so a synchronous consumer override is honored, never double-wrapped). Sequential awaits in `_gather`, not `asyncio.gather` (Django async-ORM connection safety). `_await_and_stamp` is the minimal async sibling.
- **Cross-module call shapes (re-verified to disk):** `resolved.resolve_node(pk, info=info, required=False)` matches `_resolve_node_default(cls, node_id, *, info, required=False)` (`types/relay.py:787`). `resolve_nodes(info=info, node_ids=pks, required=False)` matches `_resolve_nodes_default(cls, *, info, node_ids=None, required=False)` (`types/relay.py:844`). `_validate_node_target` passes `None` for the resolver seam into `_validate_relay_djangotype_target(target_type, resolver, *, field, relay_error_message)` (`list_field.py:99`) — correct, a refetch field has no `resolver=`. `_NODE_TYPE_HINT_ATTR = "_dsf_node_type_hint"` (`types/relay.py:74`); `_model_for` at `types/relay.py:335`. All resolve.
- **The single Low is genuinely no-action.** `_node_fields_declared` (relay.py #"_node_fields_declared: list[str]") is appended once per factory call by both factories with no dedup. Confirmed it IS co-cleared by `registry.clear()` — `_clear_if_importable("django_strawberry_framework.relay", "_node_fields_declared", lambda ledger: ledger.clear())` at `registry.py:523-527`, the exact `_helper_referenced_filtersets` precedent (registry.py:503-507) the Low cites. The finalize check reads only `bool(...)` (emptiness load-bearing); the factory-name entries are debug aids. Append-only-with-no-dedup is by design, not a leak. No edit warranted. Low has verbatim trigger phrasing, is NOT a GLOSSARY-only fix (shape #5 disqualifier absent).

High 0 / Medium 0 verified None — no defects missed.

### DRY findings disposition

DRY=None upheld. The two factories share a complete single-sited helper set (`_decode_or_graphql_error`, `_validate_node_target` → cross-module `_validate_relay_djangotype_target`, `_coerce_pk_or_none`, `_check_typed_match`, `_stamp_node_type`, `_interleave`, `_check_nodes_result`). Confirmed `_interleave` is the one order-reassembly impl serving both the sync dict-comprehension path and `_gather`. The two `_resolve` bodies are genuine single-vs-batch control-flow divergence (single value + `_await_and_stamp` sibling vs group-by-type + `positions` + per-group dispatch), not a hoistable near-copy. The 3×/3× factory-name literals are distinct concerns (noqa text, example, ledger arg) — folding would couple the ledger key to comment text. Nothing to carry forward.

### Temp test verification

- No temp tests required. No-source-edit cycle; every invariant verifiable by reading source + grepping callees to disk. Did not run pytest (no test introduced; nothing to focus).

### Shape #5 checks

1. `git diff <baseline> -- django_strawberry_framework/relay.py` empty; `git diff --stat <baseline> -- django_strawberry_framework/ tests/ docs/GLOSSARY.md CHANGELOG.md` empty. Dirty tracked files (`__init__.py`/`pyproject.toml`/`uv.lock`/`dicta.md`) are diff-empty vs baseline (pre-baseline, AGENTS.md #33 concurrent work); untracked `rev-*.md` / `review-0_0_10.md` are this cycle's review artifacts. "Files touched: None" holds.
2. Each Worker 2 section (Fix report, Comment/docstring pass, Changelog disposition) opens with `Filled by Worker 1 per no-source-edit cycle pattern.` ✓
3. Single Low has verbatim trigger phrasing; no GLOSSARY-only fix present. ✓
4. Changelog `Not warranted` cites BOTH `AGENTS.md` ("Do not update CHANGELOG.md unless explicitly instructed") AND the active plan's silence; `git diff -- CHANGELOG.md` empty; internal-only framing honest (zero source edits, no public-API change). ✓
5. `uv run ruff format --check django_strawberry_framework/relay.py` → already formatted; `uv run ruff check django_strawberry_framework/relay.py` → all checks passed. ✓

### Verification outcome

`cycle accepted; verified` — sets top-level `Status: verified` and marks the `relay.py` checklist box in `docs/review/review-0_0_10.md`.

