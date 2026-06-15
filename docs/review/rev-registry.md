# Review: `django_strawberry_framework/registry.py`

Status: verified

## DRY analysis

- None — the two cross-key collision phrasings already funnel through `registry.py::TypeRegistry._already_registered` (the `register` reverse-collision at line 141 and `register_enum`'s `(model, field_name)` collision at lines 457-461), the connection-cache eviction and the six subsystem co-clears both route through the single `registry.py::_clear_if_importable` helper (lines 215-219 and 498-527), and the `register_with_definition` rollback (lines 334-343) is the deliberate hand-written inverse of `register`'s mutations rather than a near-copy to hoist — collapsing the inverse into a shared helper would couple the two methods' internal state-mutation order and defeat the localized "mirror any new register side-effect here" comment that keeps them auditable side-by-side. The 0.0.9 DRY pass (`docs/feedback.md` "Registry Clear Optional-Callback Pattern") already single-sited the only real duplication in this module.

## High:

None.

## Medium:

None.

## Low:

### Linear scan in `definition_for_graphql_name` on the per-request GlobalID-decode path

`definition_for_graphql_name` (lines 350-390) materializes a list comprehension over the full `iter_definitions()` stream on every call, filtering by `implements_relay_node(type_cls)` and `definition.graphql_type_name == name`. It is invoked from the GlobalID type-name decode path (`types/relay.py` #"registry.definition_for_graphql_name(type_name)", line 726), which runs per request when a consumer resolves a `node(id:)` field by encoded type name. The scan is O(number of registered DjangoTypes) per decode. This is correct and harmless at current registry sizes (a handful of types in the example project), and building a `graphql_type_name -> definition` index would have to (a) live behind `mark_finalized` to stay consistent with the ambiguity contract this method enforces by raising on duplicate `graphql_type_name`, and (b) be torn down in `clear()` alongside the existing maps. Defer until a consumer registers a large DjangoType catalog (rough trigger: tens-to-hundreds of Relay-Node types) AND profiling shows node-decode latency dominated by this scan; then add a finalize-built name index with the duplicate-detection moved to index-build time so the raise-on-ambiguity contract is preserved. Not worth the added mutable-state surface before that.

## What looks solid

### DRY recap

- **Existing patterns reused.** `_already_registered` (lines 88-99) centralizes the two cross-key "already registered" `ConfigurationError` phrasings (consumed at lines 141 and 457-461); `_clear_if_importable` (lines 34-50) is the single cycle-safe optional-callback co-clear shape reused by `unregister`'s connection-cache eviction (lines 215-219) and all six `clear()` subsystem co-clears (lines 498-527). Every one of those six co-clear targets resolves on disk: `filters/inputs.py::clear_filter_input_namespace`, `filters/__init__.py` `_helper_referenced_filtersets`, `orders/inputs.py::clear_order_input_namespace`, `orders/__init__.py` `_helper_referenced_ordersets`, `connection.py::clear_connection_type_cache`, `relay.py` `_node_fields_declared`.
- **New helpers considered.** Folding the `register_with_definition` rollback (lines 334-343) into a shared "undo register" helper was evaluated and rejected: it is the deliberate inverse of `register`'s three mutations, the inline comment explicitly tasks future editors to mirror new side-effects here, and a helper would couple the two methods' mutation ordering without removing a real near-copy.
- **Duplication risk in the current file.** The 2x `"django_strawberry_framework.connection"` module-path literal (line 216 in `unregister`, line 519 in `clear`) is intentional sibling design — one evicts a single identity-keyed cache entry, the other calls the whole-cache `clear_connection_type_cache`; they target different attributes (`_connection_type_cache` vs `clear_connection_type_cache`) so the shared string is incidental, not a hoistable constant.

### Other positives

- **Process-state safety is documented and structurally enforced.** The class docstring (lines 54-61) states the no-lock contract and why it holds (all production mutation runs at import time from `DjangoType.__init_subclass__`, single-threaded module load; `clear` is test-only). `_check_mutable` (lines 72-85) is a defense-in-depth boundary guard that fails loud on any out-of-band post-finalize mutation, and every mutator (`register`, `unregister`, `register_definition`, `add_pending_relation`, `discard_pending`, `register_enum`) calls it — with `clear()` the single intentional bypass, documented as such (lines 468-476).
- **`register_with_definition` atomicity is correct.** It snapshots `_primaries[model]` and captures `register`'s `appended` return before the `register_definition` call, and the `except` branch rolls back only state THIS call added (lines 328-344), so an idempotent same-type re-register survives a later definition-mismatch failure intact. A collision raised inside `register` propagates before the `try`, leaving no partial state; `appended=False` correctly skips rollback.
- **Reflective access is minimal and justified.** Only one `getattr` (line 47, inside `_clear_if_importable`, immediately after a guarded `importlib.import_module` whose `ImportError` is caught) — the partial-load skip contract. No `hasattr`/`setattr`/`isinstance` reflective branching elsewhere; lookups are plain dict reads.
- **Import-time side effects are limited to the module-global singleton** `registry = TypeRegistry()` (line 530), whose `__init__` only allocates empty containers. The single first-party runtime import (`from .types.relay import implements_relay_node`, line 373) is in-function and decode-time, keeping `registry.py`'s module top decoupled from `types.relay` to avoid the early-import cycle — documented at lines 368-372, matching the `TYPE_CHECKING`-only `types.definition`/`types.relations` imports.
- **Iterator/identity contracts are precise.** `discard_pending` matches by `id()` not `__eq__` (documented decoupling from `PendingRelation` hashability, lines 414-425); `iter_pending_relations`'s stale-view-under-concurrent-discard caveat is documented (lines 401-412) and the only consumer (`types/finalizer.py` #"for pending in registry.iter_pending_relations()", line 578) drains into a list before discarding (lines 578-613), honoring the contract. `types_for` returns an immutable tuple snapshot.
- **No GLOSSARY drift.** GLOSSARY.md:834 and :843 describe `registry.get(model)`, `registry.model_for_type(...)`, `primary_for`, `types_for`, and `models_with_multiple_types` exactly as implemented (primary semantics, declaration-order tuple, two-or-more-types audit driver). All eight surveyed external consumers (permissions, filters/sets, types/{resolvers,converters,definition,base,finalizer,relay}, optimizer/{extension,walker}, management/inspect_django_type, testing/relay) call only the public surface in line with each method's documented return states.

### Summary

`registry.py` is a mature, heavily-reviewed process-global singleton whose mutability, finalization, and rollback contracts are explicitly documented and structurally enforced via `_check_mutable`. The cycle diff against the baseline is empty (the file was not touched this cycle); every cross-module symbol the module references resolves on disk, every documented return state matches its consumers, and GLOSSARY prose is accurate. No High or Medium findings. The only Low is a forward-looking, explicitly-triggered note on the O(n) per-decode scan in `definition_for_graphql_name`, which is correct and appropriately simple at current registry sizes. This qualifies as a no-findings (shape #1) cycle collapsing to no-source-edit (shape #5).

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — pass (267 files left unchanged).
- `uv run ruff check .` — pass (All checks passed!).

### Notes for Worker 3
- Cycle diff `git diff cd84886a39aa06d47e4d6beca2df529f6ba1dcf2 -- django_strawberry_framework/registry.py` is empty; the file was not modified this cycle.
- Low (linear scan in `definition_for_graphql_name`) is forward-looking with an explicit trigger (large Relay-Node catalog + profiling showing node-decode latency dominated by the scan); no edit made.
- No GLOSSARY-only fix in scope — GLOSSARY.md:834 and :843 verified accurate against the implementation.
- All six `clear()` co-clear targets and the `unregister` connection-cache eviction target verified to resolve on disk (see DRY recap).

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern. No comment or docstring edits warranted: the module's docstrings and inline comments are accurate, current, and load-bearing (mutability/finalization contract, rollback-mirror instruction, in-function-import rationale, co-clear partial-load contract). TODO comments: none. No stale spec references found.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern. Not warranted — no source change this cycle (review-only; cycle diff empty). Per `AGENTS.md` ("Do not update CHANGELOG.md unless explicitly instructed") and the active plan (`docs/review/review-0_0_10.md`) which carries no changelog directive for this item.

---

## Verification (Worker 3)

### Logic verification outcome
No High / Medium findings to verify. Single Low (O(n) per-decode scan in `definition_for_graphql_name`) independently confirmed as a genuine forward-looking note that masks no present defect:

- **Premise accurate.** `definition_for_graphql_name` (registry.py:375-379) materializes a list comprehension over the full `iter_definitions()` stream filtered by `implements_relay_node(type_cls)` AND `definition.graphql_type_name == name`, so the scan is O(number of registered definitions) per call.
- **Call path is genuinely per-request.** Confirmed the sole caller at `types/relay.py::decode_global_id` line 726 — the `else` (no-".") type-name branch of GlobalID decode, which runs per request when a consumer resolves `node(id:)` by encoded type name. `implements_relay_node` def resolves at `types/relay.py:52`.
- **Masks no defect.** The raise-on-miss / raise-on-ambiguity contract (registry.py:380-390) is already correct at any registry size; the scan is purely a perf consideration. The deferral rationale (an index must live behind `mark_finalized` and be torn down in `clear()`, with duplicate-detection moved to index-build time to preserve the ambiguity raise) is sound, and the trigger (tens-to-hundreds of Relay-Node types AND profiling showing node-decode latency dominated by the scan) is explicit and falsifiable. No present edit warranted. Verbatim trigger phrasing present; not a GLOSSARY-only fix.

**Registry-mutation correctness (independent sanity-check of Worker 1's clearance):**

- **`clear()` co-clears every registry.** Lines 477-483 clear all seven internal containers/flags; lines 498-527 co-clear all six subsystems. All six targets resolve on disk: `filters/inputs.py:829 clear_filter_input_namespace`, `filters/__init__.py:44 _helper_referenced_filtersets`, `orders/inputs.py:342 clear_order_input_namespace`, `orders/__init__.py:40 _helper_referenced_ordersets`, `connection.py:523 clear_connection_type_cache`, `relay.py:73 _node_fields_declared`.
- **`unregister` evicts the connection cache.** Lines 215-219 `pop` the identity-keyed entry from `connection._connection_type_cache` (resolves at `connection.py:520`).
- **Registration idempotency / process-state safety.** `register` returns `False` on same-`type_cls`/same-model re-register with matching primary flag (line 150) and raises on a flipped flag (lines 146-149) — primary status is a declaration, not mutable. `_check_mutable` guards all six mutators; `clear()` is the single documented bypass (lines 472-476).
- **`register_with_definition` rollback is a faithful inverse.** Lines 334-343 undo exactly `register`'s three mutations (append to `_types[model]`, set `_models[type_cls]`, set `_primaries[model]`), gated on the `appended` return and restoring the `pre_primary` snapshot; an idempotent pre-existing registration survives a later definition-mismatch failure intact.

### DRY findings disposition
DRY=None confirmed sound. `_already_registered` (lines 88-99) centralizes the two cross-key collision phrasings (consumed at lines 141, 457-461); `_clear_if_importable` (lines 34-50) single-sites the co-clear shape across `unregister` (215-219) and the six `clear()` blocks. The rejected hoist of the `register_with_definition` rollback into a shared helper is correctly left inline — it is the deliberate inverse and a helper would couple mutation ordering. The 2x `"django_strawberry_framework.connection"` literal is incidental (targets distinct attrs `_connection_type_cache` vs `clear_connection_type_cache`), not a hoistable constant.

### Temp test verification
- None used — no-source-edit cycle, no behavioral change to pin. All claims verified by source re-read and grep of call sites / co-clear targets.
- Disposition: n/a.

### Shape #5 checks
1. `git diff cd84886a39aa06d47e4d6beca2df529f6ba1dcf2 -- django_strawberry_framework/registry.py` empty; `git diff --stat <baseline> -- django_strawberry_framework/ tests/ docs/GLOSSARY.md CHANGELOG.md` empty over all owned paths.
2. Every Worker 2 section opens with `Filled by Worker 1 per no-source-edit cycle pattern.`
3. The single Low carries verbatim trigger phrasing; no GLOSSARY-only fix in scope.
4. Changelog `Not warranted` cites both `AGENTS.md` and the active plan's silence; `git diff -- CHANGELOG.md` empty.
5. Source byte-matches the shadow overview symbol/line map; diff empty ⇒ ruff format-check + check trivially clean (Worker 1 recorded both passing).

### Verification outcome
`cycle accepted; verified` — sets top-level `Status: verified` AND marks the `registry.py` checklist box in `docs/review/review-0_0_10.md`.
