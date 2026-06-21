# Review: `django_strawberry_framework/relay.py`

Status: verified

## DRY analysis

- None — the file is already at its DRY floor. `decode_global_id` (shape-only decode), `_coerce_pk_or_none` (id-field coercion), and the model check are single-sourced through `relay.py::decode_model_global_id` (the spec-036 DRY-2 primitive), which the mutation root-id and relation-id decoders in `mutations/resolvers.py` (`#"result = decode_model_global_id(value, expected_model)"` line 374, `#"result = decode_model_global_id(id, target_model)"` line 1103) consume rather than re-implementing; the target-guard set is delegated to `list_field.py::_validate_relay_djangotype_target` via `relay.py::_validate_node_target`; `relay.py::_interleave` serves both the sync and async (`_gather`) re-assembly paths; and `relay.py::_stamp_node_type` / `relay.py::_await_and_stamp` are a deliberate sync/async sibling pair. No new helper consolidates further without losing the documented sync-vs-async-dispatch distinction.

## High:

None.

## Medium:

None.

## Low:

None.

## What looks solid

### DRY recap

- **Existing patterns reused.** `relay.py::_validate_node_target` is a thin wrapper over `list_field.py::_validate_relay_djangotype_target` (the 0.0.9 shared Relay-target guard, also used by `connection.py::DjangoConnectionField`); `relay.py::_coerce_pk_or_none` is reused by `relay.py::decode_model_global_id` so the node-field coercer and the mutation decode path share one ORM-safety boundary (`mutations/resolvers.py` lines 374, 1103); the `_node_fields_declared` ledger follows the `_helper_referenced_filtersets` precedent and is co-cleared by `registry.py::TypeRegistry.clear` (`registry.py` line 542) and consumed by `types/finalizer.py` (line 672) for the no-Node-types finalize check.
- **New helpers considered.** A unified sync/async stamp+resolve helper was rejected — `relay.py::DjangoNodeField._resolve` must branch on `inspect.isawaitable` and route through `relay.py::_await_and_stamp` only in the async case; collapsing the branches would reintroduce coroutine-color coupling for no readability gain. Merging the sync dict-comprehension and async `_gather` per-type loops in `DjangoNodesField._resolve` was rejected for the same reason (per-call async dispatch vs synchronous build is the load-bearing contrast with `connection.py`'s committed-at-construction split).
- **Duplication risk in the current file.** The two factory bodies (`DjangoNodeField` / `DjangoNodesField`) share decode → typed-match → coerce structure; they are intentional Relay-spec siblings (`node(id:)` single vs `nodes(ids:)` batch) and the batch path adds grouping, positional null reservation, and per-type `_check_nodes_result` validation that the single path cannot use. The two repeated `"DjangoNodeField"`/`"DjangoNodesField"` literals (factory name passed to `_validate_node_target` and appended to `_node_fields_declared`) are each self-naming a distinct factory; extracting a constant would obscure which factory the message names.

### Other positives

- The decode/dispatch try-except scope is deliberately narrow: `relay.py::_decode_or_graphql_error` wraps the decode call ONLY, so a dispatch-time `SyncMisuseError` (a `ConfigurationError` subclass) surfaces as itself rather than being mislabeled `GLOBALID_INVALID` (spec-032 Revision 7 P2). Verified the comment claim against the code path — `_check_typed_match` / `_coerce_pk_or_none` / `resolve_node(s)` all run outside the wrapper.
- ORM-safety is correct: `relay.py::_coerce_pk_or_none` runs `to_python` then `run_validators` against the resolution field (`resolve_id_attr()`, not `_meta.pk`), converting an out-of-range or non-coercible literal into a `null` hole before any query, so neither the node lookup nor the relation `pk__in` can raise a backend `OverflowError` (feedback fix). The `id_attr == "pk"` vs `get_field(id_attr)` split with a `FieldDoesNotExist`-passthrough correctly handles the non-pk `NodeID` and composite-pk escape hatches.
- `relay.py::_check_nodes_result` defends the positional 1:1 `resolve_nodes` override contract: materializes a generator before `len()`, converts the shrunk/duplicate-collapsed case into a named `ConfigurationError` instead of silently wrong rows or an `IndexError` in `_interleave`.
- `relay.py::_stamp_node_type` correctly carries the decode-routing decision through to `is_type_of` (the two-registered-types-per-model ambiguity, Round-4 review S2) and is best-effort under `contextlib.suppress(AttributeError)` for `__slots__` consumer objects.
- Cross-module imports all resolve: `_NODE_TYPE_HINT_ATTR`, `_model_for`, `decode_global_id` in `types/relay.py`; `install_is_type_of` honors the stamp before its isinstance fallback (`types/relay.py` line 113).

### Summary

`relay.py` is byte-identical between the cycle baseline `aa9302112c0aceda8fa3dd6c62bd7e2e6e551239` and HEAD (`git diff` empty against both) — unchanged this cycle. The static overview surfaced no new markers; the four control-flow hotspots (`_coerce_pk_or_none`, both factories, `DjangoNodesField._resolve`) are documented and each branch is justified by the Relay contract. All load-bearing cross-module contracts were re-verified live: the spec-036 DRY-2 `decode_model_global_id` primitive is consumed by `mutations/resolvers.py`, the `_node_fields_declared` ledger is co-cleared by `registry.py` and read by `types/finalizer.py`, and the shared target guard delegates to `list_field.py`. GLOSSARY prose for both public symbols (`DjangoNodeField` lines 400-406, `DjangoNodesField` lines 408-414, plus Relay Node integration line 1121) matches the implementation with no drift. Zero findings; genuine no-source-edit cycle (shape #5).

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — pass; 289 files left unchanged.
- `uv run ruff check --fix .` — pass; all checks passed.

### Notes for Worker 3
- No High/Medium/Low findings to address; all severities `None.`
- `relay.py` unchanged vs cycle baseline `aa9302112c0aceda8fa3dd6c62bd7e2e6e551239` AND HEAD (both `git diff` empty).
- No GLOSSARY-only fix in scope — GLOSSARY prose (`DjangoNodeField` 400-406, `DjangoNodesField` 408-414, Relay Node integration 1121) verified current against the implementation; no drift.
- Cross-module load-bearing symbols re-verified present: `decode_model_global_id` (consumed by `mutations/resolvers.py` lines 374, 1103), `_node_fields_declared` (co-cleared `registry.py:542`, read `types/finalizer.py:672`), `_validate_relay_djangotype_target` (`list_field.py:99`), and `_NODE_TYPE_HINT_ATTR`/`_model_for`/`decode_global_id`/`install_is_type_of` in `types/relay.py`.

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern. No comment or docstring edits — the module docstring and per-symbol docstrings accurately describe the contract (narrow decode try-except scope, nullable-by-contract dispatch, ORM-safe coercion, positional 1:1 `resolve_nodes` override contract); no stale TODOs (0 in overview), no obsolete spec references.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern. Not warranted — no source edits this cycle (AGENTS.md "Do not update CHANGELOG.md unless explicitly instructed"; the active plan `docs/review/review-0_0_11.md` is silent on changelog edits for this item).

---

## Verification (Worker 3)

### Logic verification outcome
All severities `None.` — independently confirmed genuine shape #5 (not a missed #4), no masked defect forcing a source edit:
- **null for hidden/missing vs `GLOBALID_INVALID` for malformed.** `_decode_or_graphql_error` wraps the `decode_global_id` call ONLY (`relay.py::_decode_or_graphql_error`); a malformed/undecodable id converts every `ConfigurationError` to `GraphQLError(..., extensions={"code": "GLOBALID_INVALID"})`. An uncoercible-pk literal returns `None` (single: line `#"return None"` in `DjangoNodeField._resolve` after the `pk is None` guard; batch: positional `None` hole in `DjangoNodesField._resolve`), no query issued. `_check_typed_match` / `_coerce_pk_or_none` / `resolve_node(s)` all run OUTSIDE the wrapper so a dispatch-time `SyncMisuseError` (a `ConfigurationError` subclass) surfaces as itself — verified against the source.
- **nodes per-type-batched + order-preserving.** `groups` is an insertion-ordered dict; `positions` records `(decoded_type, within-group index)` or `None`; `_interleave` reassembles by within-group index. `_check_nodes_result` materializes a generator before `len()` and converts a shrunk/duplicate-collapsed override return into a named `ConfigurationError`. One `_interleave` serves both the sync dict-comprehension and the async `_gather` path; sequential awaits (not `asyncio.gather`) per Django async-ORM safety. Confirmed against `DjangoNodesField._resolve`.
- **`decode_model_global_id` single-source.** Defined in `relay.py::decode_model_global_id` (non-raising, returns `DecodeResult`/`GlobalIDDecode`); imported in `mutations/resolvers.py` (`from ..relay import GlobalIDDecode, decode_model_global_id`, line 88) and consumed at `mutations/resolvers.py:374` (root id) and `:1103` (relation id). Grep-confirmed; no re-implementation downstream.
- **`_node_fields_declared` co-clear/read contract.** Appended by BOTH factories on every call; co-cleared by `registry.py::TypeRegistry.clear` (`registry.py:542`); read by `types/finalizer.py` (`from ..relay import _node_fields_declared`, line 670; emptiness check line 672). Grep-confirmed.
- **Shared target guard** delegates to `list_field.py::_validate_relay_djangotype_target` (def at `list_field.py:99`); cross-module imports `_NODE_TYPE_HINT_ATTR` / `_model_for` / `decode_global_id` resolve in `types/relay.py`, and `install_is_type_of` (`types/relay.py:77`) honors the `_NODE_TYPE_HINT_ATTR` stamp before its isinstance fallback (line 113). Grep-confirmed.

### GLOSSARY prose accuracy (genuine #5, not missed #4)
Read `DjangoNodeField` (GLOSSARY:404), `DjangoNodesField` (GLOSSARY:412), and Relay Node integration (GLOSSARY:1121) against the live implementation — all accurate, no drift:
- `DjangoNodeField` prose matches: nullable-by-contract (`required=False` unconditional), `id: strawberry.ID` raw-string rationale, `GLOBALID_INVALID` on malformed, typed-form wrong-type `GraphQLError`, hidden/missing/uncoercible-pk → `null`, and the no-Node-types finalization `ConfigurationError` (matches `types/finalizer.py:672`).
- `DjangoNodesField` prose matches: per-type batched (`resolve_nodes` once per distinct type), input-order preserved, duplicates supported, positional `null` holes, whole-field failure (`[Node]!` non-null) for any malformed/wrong-type id.
- Relay Node integration:1121 matches: the `0.0.9` refetch surface decodes payloads server-side and dispatches to `resolve_node` / `resolve_nodes` defaults. No owed GLOSSARY fix.

### DRY findings disposition
Single DRY bullet is the justified `None` — file is at its DRY floor. Verified the four cited single-source primitives live: `decode_model_global_id` (consumed by `mutations/resolvers.py`), `_coerce_pk_or_none` (shared by node field + `decode_model_global_id`), `_validate_node_target` → `list_field._validate_relay_djangotype_target`, and the `_interleave` / `_stamp_node_type`+`_await_and_stamp` sync/async sibling pairs. The sync/async-dispatch distinction is load-bearing; no further helper consolidates without reintroducing coroutine-color coupling. Concur.

### Temp test verification
- No temp tests created — zero-edit cycle, no behavior change to prove; logic confirmed by source read + grep of cross-module contracts.

### Sibling-cycle attribution
Zero-edit proof for relay.py holds: `git diff aa9302112c0aceda8fa3dd6c62bd7e2e6e551239 -- django_strawberry_framework/relay.py` empty AND `git diff HEAD -- ...relay.py` empty AND relay.py absent from `git diff --stat <baseline> -- django_strawberry_framework/ tests/ docs/GLOSSARY.md CHANGELOG.md`. The two dirty hunks in that stat are non-relay.py: `filters/sets.py` (owning `rev-filters__sets.md` is `Status: verified` but its plan box `review-0_0_11.md:97` is still `[ ]` — sibling cycle not yet box-closed) and `mutations/sets.py` (`rev-mutations__sets.md` not yet present; plan box `:111` `[ ]`). Both are AGENTS.md #33 concurrent/in-flight sibling work on non-target paths — not a relay.py rejection trigger. relay.py's own "Files touched: None" claim holds. CHANGELOG diff empty (consistent with Not-warranted).

### Validation
- `uv run ruff format --check django_strawberry_framework/relay.py` — 1 file already formatted (the COM812-formatter warning is the standing project config notice, not a failure).
- `uv run ruff check django_strawberry_framework/relay.py` — All checks passed.

### Verification outcome
- `cycle accepted; verified` — sets top-level `Status: verified` AND marks the `relay.py` checklist box in `docs/review/review-0_0_11.md`.
