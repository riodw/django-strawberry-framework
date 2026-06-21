# Review: `django_strawberry_framework/registry.py`

Status: verified

## DRY analysis

- Defer with trigger: the connection-class cache eviction in `registry.py::TypeRegistry.unregister` (`_clear_if_importable("django_strawberry_framework.connection", "_connection_type_cache", lambda cache: cache.pop(type_cls, None))`) and the whole-cache purge in `registry.py::TypeRegistry.clear` (`_clear_if_importable("django_strawberry_framework.connection", "clear_connection_type_cache", lambda clear: clear())`) both reach into the same sidecar module via the same helper but with different attribute/action shapes (pop-one vs clear-all). This is the only repeated literal in the file (`"django_strawberry_framework.connection"`, 2x). Do NOT consolidate now — the two call sites have genuinely different semantics (per-type eviction vs full purge) and a shared wrapper would either take an action callback (no readability gain over the `_clear_if_importable` already-shared shape) or hard-couple `registry.py` to connection-cache internals. Defer until a third connection-cache reach-in appears in this module; fold all three through a connection-cache-specific helper exported from `connection.py` at that point.

- Defer with trigger: `register_with_definition`'s rollback block (`registry.py::TypeRegistry.register_with_definition`, the `except Exception` body) hand-inlines the inverse of `register`'s mutations (`_types[model]` removal + empty-list pop, `_models.pop`, `_primaries` restore). It is a near-mirror of the trace-removal logic in `registry.py::TypeRegistry.unregister`. Do NOT consolidate now — `unregister` removes ALL traces unconditionally (including `_definitions` and `_pending`), whereas the rollback removes only state THIS `register` call appended and restores the pre-call `_primaries` snapshot rather than clearing it. Extracting a shared `_drop_type_traces` would need a "restore-to-snapshot vs delete" mode parameter that obscures both call sites. Defer until a third partial-rollback site appears; the source comment at `registry.py::TypeRegistry.register_with_definition #"Inverse of register's mutations above"` already flags the mirror obligation as the cheaper guard.

## High:

None.

## Medium:

None.

## Low:

None.

## What looks solid

### DRY recap

- **Existing patterns reused.** `_clear_if_importable` (`registry.py::_clear_if_importable`) is the single-sited cycle-safe co-clear helper backing every subsystem teardown — ten call sites across `clear` (filter/order/mutation input namespaces + helper ledgers, connection cache, root node-field ledger) plus one in `unregister` (connection-cache eviction), per the 0.0.9 DRY pass. `_already_registered` (`registry.py::TypeRegistry._already_registered`) centralizes the "already registered" `ConfigurationError` phrasing for the two cross-key collision sites (`register` reverse-collision + `register_enum` `(model, field_name)` collision) so consumer substring-matching stays grep-stable; the distinct primary-flip / duplicate-primary / definition-collision phrasings are intentionally inline because they are test-pinned by different substrings. `_check_mutable` (`registry.py::TypeRegistry._check_mutable`) is the single finalize guard reused by every mutator except the deliberately-bypassing `clear`.
- **New helpers considered.** A connection-cache reach-in wrapper and a shared partial-rollback `_drop_type_traces` were both evaluated and deferred-with-trigger (see `## DRY analysis`) — each would need a mode/action parameter that obscures the call sites today.
- **Duplication risk in the current file.** The only repeated literal is `"django_strawberry_framework.connection"` (2x, `unregister` eviction + `clear` purge); intentional sibling design covered by the deferred DRY bullet. The co-clear blocks in `clear` are deliberately separate independent rows (not a loop/table) so an unreachable subsystem never blocks a later co-clear and each carries its own spec-anchored comment — the source comment at `registry.py::TypeRegistry.clear #"a future sidecar family"` documents the append-one-row growth path.

### Other positives

- **Mutation-safety contract is coherent and documented.** Every production mutator runs `_check_mutable` first; the class docstring (`registry.py::TypeRegistry`) explains the no-lock decision (import-time single-threaded mutation only) and `clear`'s docstring documents the deliberate guard bypass for test teardown. The contract is defense-in-depth: `DjangoType.__init_subclass__` already rejects post-finalize subclasses and the registry pins the same contract at its boundary.
- **`register_with_definition` atomicity is correct.** It snapshots `_primaries[model]` before `register`, captures whether `register` actually appended state, and on `register_definition` failure rolls back ONLY this call's mutations — a pre-existing idempotent re-register survives a re-register-with-different-definition failure. `_types`/`_models` lock-step is asserted by comment and relied on in `unregister`.
- **`get` vs `primary_for` vs `model_for_type` return semantics are precisely specified.** `get` returns the primary, falls back to a lone single type, and returns `None` for the multi-type-no-primary ambiguous state (documented as indistinguishable from "unregistered" without `types_for`); `primary_for` is strict `_primaries`-only; `model_for_type` tolerates `None` input so the optimizer pipelines through unwrapped wrappers without a guard. No accidental overlap.
- **`iter_pending_relations` / `discard_pending` mutation-during-iteration hazard is documented, not silently broken.** The docstring spells out that `discard_pending` rebinds `self._pending` to a fresh list so an in-flight `yield from` sees a stale view, and notes the finalizer drains to a list first. `discard_pending` uses `id()` identity-matching deliberately (stronger than `__eq__`, avoids coupling to `PendingRelation` hashability).
- **`definition_for_graphql_name` correctness.** Scans `iter_definitions()` for a unique `graphql_type_name` match over Relay-Node definitions only, keyed on `definition.graphql_type_name` (honoring `Meta.name`) not `type_cls.__name__`; raises distinct `ConfigurationError` phrasings for the no-match and ambiguity cases (ambiguity lists colliding origins sorted). The in-function `from .types.relay import implements_relay_node` import is justified by comment (early-import module must not couple its top to `types.relay`; decode-time call resolves cheaply).

### Summary

`registry.py` is byte-identical to both the per-cycle baseline (`7b6c615f9dcf65daf3dfda8edbd0ea4929000ef5`) and HEAD — `git diff` is empty in both directions. No source, test, GLOSSARY, or CHANGELOG edits are in scope, so this is a genuine no-source-edit cycle (shape #5). I re-verified the load-bearing `clear()` claim: all ten subsystem co-clear targets resolve to real symbols (`filters.inputs.clear_filter_input_namespace`, `filters._helper_referenced_filtersets`, `orders.inputs.clear_order_input_namespace`, `orders._helper_referenced_ordersets`, `mutations.inputs.clear_mutation_input_namespace`, `mutations.sets.clear_mutation_registry`, `connection.clear_connection_type_cache` + `_connection_type_cache`, `relay._node_fields_declared`), plus the `unregister` connection-cache eviction target. GLOSSARY prose is current — the registry-surface paragraph (`primary_for` / `types_for` / `models_with_multiple_types`), the `Meta.primary` entry (`registry.get(model)` / `registry.model_for_type`), and the `_helper_referenced_ordersets` co-clear note all match the implementation, no drift. Two DRY opportunities exist, both defer-with-trigger (connection-cache reach-in wrapper; shared partial-rollback helper) — neither is act-now. Zero High/Medium/Low findings.

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
- `registry.py` is byte-identical to baseline `7b6c615f9dcf65daf3dfda8edbd0ea4929000ef5` and HEAD (`git diff` empty both ways). Genuine shape #5.
- Both DRY bullets are defer-with-trigger, not act-now; no source change required.
- Low: none.
- No GLOSSARY-only fix in scope — registry-surface, `Meta.primary`, and `_helper_referenced_ordersets` prose all current vs implementation.
- Load-bearing `clear()` co-clear claim re-verified: all ten teardown targets + the `unregister` eviction target resolve to real symbols.

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern.

No comment or docstring edits in scope — the file is unchanged and the in-source comments (mutation-safety contract, `_types`/`_models` lock-step, rollback-mirror obligation, in-function-import rationale, co-clear growth path) all remain accurate.

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern.

Not warranted. No source behavior changed (zero-diff cycle). AGENTS.md: do not update `CHANGELOG.md` unless explicitly instructed; the active plan `docs/review/review-0_0_11.md` is silent on any registry changelog entry.

---

## Verification (Worker 3)

### Logic verification outcome
All High / Medium / Low are `None.` — confirmed genuine, not lazy. Independent reads:
- **Zero-edit proof (shape #5).** `git diff 7b6c615f9dcf65daf3dfda8edbd0ea4929000ef5 -- django_strawberry_framework/registry.py` empty; `git diff HEAD -- …registry.py` empty; `git diff --stat <baseline> -- django_strawberry_framework/ tests/ docs/GLOSSARY.md CHANGELOG.md` empty (no dirt in owned paths this run). registry.py byte-identical to baseline AND HEAD.
- **Each Worker 2 section** opens `Filled by Worker 1 per no-source-edit cycle pattern.` (Fix report, Comment/docstring pass, Changelog disposition).
- **clear() co-clear target list — all 11 resolve to real symbols** (grep-confirmed): `filters.inputs.clear_filter_input_namespace` (def @830), `filters._helper_referenced_filtersets` (set @44), `orders.inputs.clear_order_input_namespace` (def @342), `orders._helper_referenced_ordersets` (set @40), the **new mutations-namespace co-clears** `mutations.inputs.clear_mutation_input_namespace` (def @127) and `mutations.sets.clear_mutation_registry` (def @140), `connection.clear_connection_type_cache` (def @523), `relay._node_fields_declared` (list @74), plus the `unregister` connection-cache eviction target `connection._connection_type_cache` (@520). `implements_relay_node` (types/relay.py @52) backs `definition_for_graphql_name`.
- **`_clear_if_importable` ImportError-only swallow** (line 48): `except ImportError:` — narrow, not bare `Exception`; preserves per-block independence so an unreachable subsystem skips without masking a real error in `action`. Pinned by `tests/test_registry.py::test_unregister_tolerates_unimportable_connection_submodule` (@1293).
- **Registry reset/rollback semantics.** `register_with_definition` snapshots `pre_primary` before `register`, captures `appended`, and on `register_definition` failure rolls back ONLY this call's mutations (`_types`/`_models` removal + empty-list pop; restore-to-snapshot vs delete on `_primaries`). Matches the deferred DRY rationale. Pinned by `test_register_with_definition_rollback_clears_primary` (@903), `…rollback_restores_pre_existing_primary` (@924), `…idempotent_re_register_preserves_primary` (@980). `clear()` deliberately bypasses `_check_mutable` (test-teardown reset) — pinned by `test_clear_drops_all_state` (@244), `test_clear_resets_primaries` (@1112).
- `get`/`primary_for`/`model_for_type` return semantics pinned by `test_get_returns_single_type_when_one_registered_no_primary` (@1017), `…primary_when_multiple_and_primary_declared` (@1027), `…none_when_multiple_and_no_primary` (@1041), `test_primary_for_returns_none_when_only_implicit_single_type` (@1057). No unpinned defensive seam → `None.` severities genuine; no masked defect forcing a source edit.

### DRY findings disposition
Both DRY items confirmed correctly **defer-with-trigger** (not act-now):
1. Connection-cache reach-in (`"django_strawberry_framework.connection"` 2x — `unregister` pop-one eviction vs `clear` full purge): a shared wrapper would need an action callback (no gain over the already-shared `_clear_if_importable` shape) or hard-couple registry.py to connection internals. Trigger: a third connection-cache reach-in.
2. `register_with_definition` partial-rollback near-mirror of `unregister` trace-removal: `unregister` removes ALL traces unconditionally; rollback removes only this-call state and restores the `_primaries` snapshot. A shared `_drop_type_traces` would need a "restore-to-snapshot vs delete" mode that obscures both call sites. Trigger: a third partial-rollback site. The source comment at `register_with_definition #"Inverse of register's mutations above"` already flags the mirror obligation. Confirmed verbatim in source (line 333).

### Temp test verification
- None — no temp tests needed; zero-edit cycle verified by diff + grep + existing named tests.
- Disposition: n/a.

### GLOSSARY accuracy (genuine #5, not missed #4)
Spot-checked the registry prose against live source — all current, no drift, no owed GLOSSARY fix:
- Registry surface (GLOSSARY:874): `primary_for(model)` / `types_for(model)` / `models_with_multiple_types()` match `registry.py` defs verbatim.
- `Meta.primary` (GLOSSARY:865): `registry.get(model)` returns primary; `registry.model_for_type(SecondaryType)` reverse-discovers — matches `get()` (lines 234-240) and `model_for_type()` (lines 252-254).
- `_helper_referenced_ordersets` co-clear note (GLOSSARY:981): ledger co-cleared by `registry.clear()` — matches the `orders._helper_referenced_ordersets` co-clear block. Genuine shape #5.

### Changelog disposition
`Not warranted` accepted. `git diff -- CHANGELOG.md` empty (confirmed). Disposition cites BOTH AGENTS.md ("do not update CHANGELOG.md unless explicitly instructed") AND the active plan `review-0_0_11.md` silence on a registry entry. Zero-diff cycle, internal-only — "Not warranted" is the correct state. Ruff format-check + check both pass on registry.py.

### Verification outcome
`cycle accepted; verified` — sets top-level `Status: verified` AND marks the `registry.py` checklist box `- [x]` in `docs/review/review-0_0_11.md`.
