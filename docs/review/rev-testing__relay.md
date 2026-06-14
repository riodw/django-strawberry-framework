# Review: `django_strawberry_framework/testing/relay.py`

Status: verified

## DRY analysis

- **Live-emission parity is single-sourced through `encode_typename`, not re-implemented — keep it that way.** `global_id_for` (`testing/relay.py:96`) computes the type-name slot by calling `types/relay.py::encode_typename` — the exact function the live `resolve_typename` closure runs (`types/relay.py::_install_typename_closure #"return encode_typename(definition, strategy, cls, root, info)"`). The `str(relay.GlobalID(...))` wrap (`testing/relay.py:97`) mirrors what Strawberry's `Node._id` does. No payload-shape logic is duplicated. The only candidate consolidation would be a shared "encode the slot then base64-wrap" helper spanning the live closure and this helper, but the live closure returns the bare slot (Strawberry wraps it downstream) while the helper must produce the finished string — different return contracts. Defer with trigger: if a third site ever needs the *finished* GlobalID string from a `(definition, strategy)` pair, extract `_finished_global_id(definition, strategy, type_cls, node_id)`; until then the current 2-line body is correctly inline.
- **The Relay-Node-gate message pair is already imported, not re-typed.** `_RELAY_NODE_GATE_LEAD` / `_RELAY_NODE_GATE_INHERIT_TAIL` are imported from `types/base.py:104,110` and reused at `testing/relay.py:82-83`, the same constants the `Meta.connection` / `relation_shapes` gates use (`types/base.py:216-217,268`). No drift risk. Correct factoring.

## High:

None.

## Medium:

None.

## Low:

None.

## What looks solid

### DRY recap

- **Existing patterns reused.** Slot computation delegates to `types/relay.py::encode_typename` (`testing/relay.py:96`); the uniform `ConfigurationError` contract is reused rather than a new exception type; the gate-message constants `_RELAY_NODE_GATE_LEAD` / `_RELAY_NODE_GATE_INHERIT_TAIL` and the `STRING_GLOBALID_STRATEGIES` frozenset are imported from `types/base.py` (`testing/relay.py:40-44`) — the same single sources of truth the production Relay path reads. The `getattr(type_cls, "__django_strawberry_definition__", None)` accessor (`testing/relay.py:59`) matches the canonical definition lookup used across the package.
- **New helpers considered.** A finished-GlobalID-string helper spanning the live closure and `global_id_for` was evaluated and rejected — the two have different return contracts (bare slot vs finished string); deferred with an explicit third-site trigger in DRY analysis.
- **Duplication risk in the current file.** The literal `global_id_for:` prefix repeats across the four raise messages (`testing/relay.py:62,73,87` + the `_RELAY_NODE_GATE_LEAD` arm at 82). This is intentional per-message provenance (the consumer sees which helper raised); folding into an f-string-prefix constant would hurt readability for no behavioral gain. Correctly inline.

### Other positives

- **Strategy-awareness is correct and consistent-by-construction across all four reachable strategies.** The helper reads `definition.effective_globalid_strategy` (`testing/relay.py:77`), the finalize-stamped classification (`types/relay.py::install_globalid_typename_resolver` step 3), *never* the raw setting — so it cannot disagree with what the type emits. Branch-by-branch parity verified against the live `encode_typename` (`types/relay.py:453-493`): `model` / `type+model` are both members of `MODEL_LABEL_STRATEGIES` so `encode_typename` returns `definition.model._meta.label_lower`; `type` falls through to `definition.graphql_type_name`. Because the live closure passes the *raw* strategy and the helper passes the *classification string*, but for all three string strategies those values are byte-identical strings, `encode_typename` takes the same branch in both call paths. The comment at `testing/relay.py:92-95` correctly notes the string branches never touch `root`/`info`, so passing `(None, None)` is sound — the `callable` branch (the only one that reads them) is gated out one statement earlier.
- **The four raise branches are correctly ordered and each guards a distinct real failure mode.** (1) non-DjangoType input → `__django_strawberry_definition__` absent (`testing/relay.py:59-64`); (2) **`finalized` is gated BEFORE the strategy stamp is read** (`testing/relay.py:65-76`) — the comment and spec-032-feedback-P2 rationale are accurate: the strategy is stamped in Phase 2.5 *before* `finalized` flips in Phase 3, so a partial-finalize failure can leave a non-`None` strategy on an unfinalized type; reading the stamp first would mint an id in violation of the contract. This ordering is independently pinned by `tests/testing/test_relay.py::test_global_id_for_strategy_stamped_but_unfinalized_raises` (monkeypatches a stamped-but-unfinalized state). (3) `strategy is None` → finalized non-Relay-Node type (`testing/relay.py:78-84`); (4) `strategy not in STRING_GLOBALID_STRATEGIES` → `callable`/`custom` (`testing/relay.py:85-91`), whose encoders need a live `(root, info)` the helper cannot supply. Each message names `global_id_for:` and the offending type/strategy.
- **`decode_global_id` re-export fidelity is exact.** Imported directly from `types/relay.py` (`testing/relay.py:45`) and listed in `__all__` (`testing/relay.py:47`) — a true re-export, no wrapper, so the uniform `ConfigurationError` contract, the `(target_type, node_id)` return, and every decode branch (`types/relay.py:634-747`) reach the consumer unchanged. The internal signature `(gid: relay.GlobalID | str) -> tuple[type, str]` is already consumer-shaped, so no adapter is warranted.
- **The documented round-trip asymmetry is honest, not a latent bug.** The module docstring (`testing/relay.py:24-30`) correctly states `decode_global_id(global_id_for(T, pk)) == (T, str(pk))` holds only for lone/primary model-label types and `type`-strategy payloads — a SECONDARY model-label emitter mints the payload it genuinely emits, while decode routes that label to the model's PRIMARY via `registry.get(model)`. This matches the live `node(id:)` routing (`types/relay.py:718`) and is verified by `tests/testing/test_relay.py:249-260` and `tests/types/test_relay_interfaces.py:1894`.
- **Module-placement and import-cost rationale are sound.** Living under `testing/` (consumer test audience) and being imported as the submodule (not via `testing/__init__`) keeps `import django_strawberry_framework.testing` light — the `types`-package imports are paid only by suites that use the helpers (`testing/relay.py:31-35` docstring). The `noqa: A002` on the `id` parameter (`testing/relay.py:50`) is the right ergonomic call: `id` mirrors Relay's `node(id:)` consumer vocabulary.
- **Test discipline is exemplary.** Live-parity (`assert live_id == global_id_for(...)`) for all three encodable strategies (`tests/testing/test_relay.py:85-126`), all four raise branches including the subtle Phase-2.5 stamped-but-unfinalized case, plus real end-to-end usage minting ids for `node`/`nodes` queries in `examples/fakeshop/test_query/test_library_api.py` (per the AGENTS.md "earn coverage through real GraphQL queries" rule).

### Summary

A clean, well-reasoned new 0.0.9 public test helper. `global_id_for` is strategy-aware by construction — it reads the finalize-stamped `effective_globalid_strategy` and delegates slot computation to the same `encode_typename` the live `resolve_typename` closure runs, so it provably emits the GlobalID a finalized type emits across the `model` / `type` / `type+model` strategies, and correctly raises `ConfigurationError` (not a silent wrong answer) for `callable`/`custom`, unfinalized types, and finalized non-Relay-Node types. The `finalized`-before-strategy gate ordering is the one genuinely subtle correctness point, and it is both correct and test-pinned. `decode_global_id` is a faithful zero-wrapper re-export. No High/Medium/Low findings; no GLOSSARY entry expected or present (per spec). Qualifies as a no-source-edit cycle (shape #5).

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
None — no-source-edit cycle.

### Tests added or updated
None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — 0 files reformatted (clean).
- `uv run ruff check --fix .` — All checks passed.

### Notes for Worker 3
- High / Medium / Low: all `None.` — no logic, comment, or DRY defect found.
- DRY analysis: both bullets are recap/defer-with-trigger (finished-GlobalID-string helper deferred until a 3rd site; gate-message constants already single-sourced). No act-now consolidation.
- No GLOSSARY-only fix in scope: `global_id_for` / `decode_global_id` have no own GLOSSARY entry, and per the cycle spec none is expected (`docs/GLOSSARY.md` documents the GlobalID strategy system under `#relay-node-integration` / `#metaglobalid_strategy`, not the test helpers). Grep confirmed no stale prose referencing either helper symbol.

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern. The module docstring, the `finalized`-gate comment (`testing/relay.py:66-71`), the non-Relay-Node comment (`testing/relay.py:79-80`), and the string-branch / `(None, None)` rationale (`testing/relay.py:92-95`) were all read and verified accurate against `types/relay.py` and the spec-032 references. No comment or docstring edit warranted.

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern. **Not warranted** — no source edit was made this cycle (AGENTS.md: "Do not update CHANGELOG.md unless explicitly instructed"; the active plan `review-0_0_9.md` carries no changelog directive for this item).

---

## Verification (Worker 3)

### Logic verification outcome
No-source-edit cycle (shape #5). Cycle diff for `testing/relay.py` vs baseline `0872a20` is EMPTY (byte-unchanged; absent from `git diff --stat`). High/Medium/Low all `None.` — verified each of the four dispatch claims independently:

- **(a) Live-emission strategy parity — byte-identical across all string strategies.** Drove parity directly, not via the artifact: `model` through the live installed `resolve_typename` closure (`cls.resolve_typename(...)` ignores root/info for model-label) and `type` / `type+model` through real `schema.execute_sync("{ row { id } }")` emission. All three byte-identical to `global_id_for(cls, pk)`: `model`→`cHJvZHVjdHMuY2F0ZWdvcnk6...`, `type`→`Q2F0ZWdvcnlOb2RlOjE=`, `type+model`→`cHJvZHVjdHMuY2F0ZWdvcnk6MjY=`. Root cause of parity confirmed at source: the live closure passes the raw resolved `strategy` (`types/relay.py::_install_typename_closure #"return encode_typename(definition, strategy, cls, root, info)"`) while `global_id_for` passes `definition.effective_globalid_strategy`; for the three string strategies `classification = strategy` (`install_globalid_typename_resolver` line 601), so both hit the SAME `encode_typename` branch (`MODEL_LABEL_STRATEGIES` → `model._meta.label_lower`; else → `graphql_type_name`). The helper's `(None, None)` for root/info is sound — those are read only in the `callable` branch, gated out one statement earlier.
- **(b) `finalized`-before-stamp gate ordering — correct and pinned.** Forged a Phase-2.5-stamped (`effective_globalid_strategy="model"`) but Phase-3-unfinalized (`finalized=False`) definition; `global_id_for` raised `ConfigurationError("... is not finalized ...")`, proving the `finalized` gate (`testing/relay.py:65`) fires BEFORE reading the stamp (`:77`). Confirmed at source the stamp is written as the last statement of `install_globalid_typename_resolver` (Phase 2.5, `types/finalizer.py #"install_globalid_typename_resolver(type_cls, definition)"` → `types/relay.py::install_globalid_typename_resolver` line 605) and `finalized = True` flips later in Phase 3 (`types/finalizer.py #"definition.finalized = True"`), so a partial-finalize raise genuinely leaves a stamped-but-unfinalized type — reading the stamp first would mint an id in violation of contract. Pinned by `tests/testing/test_relay.py::test_global_id_for_strategy_stamped_but_unfinalized_raises` (grep-confirmed, line 209; 10/10 suite passes).
- **(c) `decode_global_id` re-export fidelity.** True zero-wrapper re-export: `testing.relay.decode_global_id is types.relay.decode_global_id` (identity), pinned at `tests/testing/test_relay.py:252`. Listed in `__all__` (`testing/relay.py:47`).
- **(d) Error handling.** Drove all four raise branches live: non-DjangoType (`global_id_for(object,1)`), unfinalized (b above), finalized non-Relay-Node (`effective_globalid_strategy is None`), and `callable`/`custom` (encoder needs live root/info the helper lacks) — each raises `ConfigurationError` with `global_id_for:` provenance and names the offending type/strategy.

### DRY findings disposition
Both DRY bullets are recap / defer-with-trigger (finished-GlobalID-string helper deferred until a 3rd site needs the finished string; gate-message constants `_RELAY_NODE_GATE_LEAD`/`_RELAY_NODE_GATE_INHERIT_TAIL` + `STRING_GLOBALID_STRATEGIES` already single-sourced from `types/base.py`). No act-now consolidation. Carried forward as written.

### Sibling-cycle attribution
`testing/relay.py` itself is byte-unchanged (absent from the diff stat) → "Files touched: None" holds. All dirty paths in the owned-scope stat (conf.py, connection.py, exceptions.py, filters/factories.py, filters/sets.py, list_field.py, management/commands/inspect_django_type.py, optimizer/{extension,selections,walker}.py, orders/{factories,inputs}.py, docs/GLOSSARY.md, tests/management/test_inspect_django_type.py, tests/optimizer/test_selections.py) attribute to CLOSED sibling cycles (all `Status: verified`, `[x]` in `review-0_0_9.md`) — not a rejection trigger.

### Temp test verification
- Temp tests: `docs/review/temp-tests/testing_relay/repro_parity.py` (model parity via live closure + setup), `repro_parity2.py` (type/type+model parity via real schema), `repro_gate.py` (gate ordering + 4 error branches). All gitignored.
- Disposition: deleted at cycle closeout by Worker 0. Permanent coverage already exists and is exemplary — `tests/testing/test_relay.py` (10 tests: 3 live-parity, 4 raise branches incl. stamped-but-unfinalized, decode identity + asymmetry round-trip; all pass) plus real `node`/`nodes` GraphQL minting in `examples/fakeshop/test_query/test_library_api.py`. No promotion needed.

### Changelog disposition
`git diff -- CHANGELOG.md` EMPTY. **Not warranted** — no source edit this cycle; cites AGENTS.md ("Do not update CHANGELOG.md unless explicitly instructed") AND the active plan's silence. Honest internal-only framing (no shipped behavior changed; the public surface itself was unchanged this cycle). Correct.

### Verification outcome
`cycle accepted; verified` — sets top-level `Status: verified` AND marks the checklist box.

Note: the artifact's incoming `Status:` read `under-review` (dispatch expected bare `fix-implemented`). The Fix report / Comment / Changelog sections are all complete and filled per the no-source-edit (Worker-2-skipped) shape #5 pattern; the Status line was simply never advanced from `under-review`. Substance complete and independently verified — flipped to `verified` per terminal-pass duty.

---

## Iteration log

(none)
