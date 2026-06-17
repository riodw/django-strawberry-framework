# Review: `django_strawberry_framework/testing/relay.py`

Status: verified

## DRY analysis

- None — the module is a thin public test-helper veneer over already-single-sourced machinery. `global_id_for` delegates payload computation to `types/relay.py::encode_typename` (the canonical per-strategy slot encoder), reads the strategy set `STRING_GLOBALID_STRATEGIES` and the gate-message constants `_RELAY_NODE_GATE_LEAD` / `_RELAY_NODE_GATE_INHERIT_TAIL` from `types/base.py`, and re-exports `decode_global_id` verbatim from `types/relay.py`. Nothing is duplicated locally; the five `ConfigurationError` raises carry distinct subjects/contracts and the four `f"global_id_for: "` literal prefixes are per-message human-readable strings, not a dispatch key (folding them into a constant would obscure each message and save nothing material).

## High:

None.

## Medium:

None.

## Low:

None.

## What looks solid

### DRY recap

- **Existing patterns reused.** `global_id_for` reuses `types/relay.py::encode_typename` (`testing/relay.py::global_id_for` #"encode_typename(definition, strategy") for payload computation, imports `STRING_GLOBALID_STRATEGIES` + the two gate-message constants from `types/base.py` (`testing/relay.py:40-44`), and re-exports `types/relay.py::decode_global_id` unchanged (`testing/relay.py:45`, `__all__` at `:47`). The helper reads the finalize-stamped `definition.effective_globalid_strategy` rather than the setting, so it is consistent-by-construction with live emission — pinned by the `live_id == global_id_for(...)` assertions in `tests/testing/test_relay.py:94,110,125`.
- **Duplication risk in the current file.** The four `"global_id_for:"` message prefixes (`testing/relay.py:62,72,81,86`) are the only repeated literal (static overview flags `4x global_id_for:`). Intentional — each is a distinct error message with a different subject and remediation contract; a shared prefix constant would not be reused as a dispatch key and would harm message readability. Correct to leave inline.

### Other positives

- **Strategy-aware encoding is correct across all four strategy classes.** The gate `strategy in STRING_GLOBALID_STRATEGIES` (`testing/relay.py:85`) admits exactly `{model, type, type+model}`; `encode_typename` resolves `model`/`type+model` via `MODEL_LABEL_STRATEGIES` → `model._meta.label_lower` and the remaining `type` → `graphql_type_name` (`types/relay.py:490-493`). `STRING_GLOBALID_STRATEGIES \ MODEL_LABEL_STRATEGIES == {type}`, so there is no uncovered string strategy and no over-broad admission. `callable`/`custom` are correctly rejected before `encode_typename` is reached, so the `callable(strategy)` branch (the only one that touches `root`/`info`) is unreachable from this helper — which is why passing `None, None` for `(root, info)` at `:96` is safe, not a latent crash.
- **Gate ordering is deliberate and documented.** `definition is None` → not-a-DjangoType (`:60`), then `not definition.finalized` BEFORE reading the strategy stamp (`:65`), then `strategy is None` → finalized-but-non-Relay-Node (`:78`), then the non-string-strategy gate (`:85`). The `finalized`-first ordering is justified inline against the spec-032 P2 partial-finalize hazard (strategy stamped in Phase 2.5 before Phase 3 flips `finalized`) and pinned by `tests/testing/test_relay.py::test_global_id_for_strategy_stamped_but_unfinalized_raises` (monkeypatch sets a strategy on an unfinalized type and asserts the not-finalized message wins).
- **Public-API shape / back-compat intact.** `__all__ = ["decode_global_id", "global_id_for"]` (`:47`), the submodule path is the public surface (not re-exported from `testing/__init__`, by design), and the signatures match the GLOSSARY contract. The `# noqa: A002` on the `id` shadow is justified — `id` is the consumer-facing parameter name the helper documents.
- **Test discipline.** Every branch is pinned in `tests/testing/test_relay.py`: the three string strategies (`:85,101,116`, each also asserting equality with the live-emitted id), `callable`/`custom` raise (`:169`), unfinalized raise (`:183`), non-Node raise (`:193`), the stamped-but-unfinalized edge (`:209`), the non-DjangoType branch (`:205`, asserts "not a registered DjangoType subclass"), the decode round-trip for primary + type-name payloads (`:244`), and the documented secondary-model-label-emitter → primary asymmetry (`:255`).
- **Asymmetry contract is documented, not a bug.** The module docstring (`:24-30`) states the round-trip holds only for lone/primary model-label types and `type`-strategy payloads, because a secondary model-label emitter mints the payload it genuinely emits while `decode_global_id` routes it to the model's PRIMARY via `registry.get(model)` — exactly what a live `node(id:)` does. This is correct behavior pinned by `test_secondary_model_label_emitter_decodes_to_primary`.

### Summary

`testing/relay.py` is a clean public test-helper module: one function `global_id_for` plus a re-export of `decode_global_id`. It has no changes since the baseline (`git log 14910230..HEAD` empty, `git diff HEAD` empty; only `testing/__init__.py` changed +2 this set, a future-version doc bump). The strategy-aware encoding is correct for all four strategy classes — string strategies delegate to the canonical `encode_typename` and the `(root, info)=None` arguments are provably unreachable in the touching branch; `callable`/`custom` are gated out with a clear contract. The four ordered `ConfigurationError` gates are well-justified (the `finalized`-first ordering defends the spec-032 P2 partial-finalize hazard) and exhaustively tested, including the deliberately-documented decode asymmetry. No High/Medium/Low findings; DRY is correctly None (the file is a veneer over already-single-sourced machinery). GLOSSARY entry (`docs/GLOSSARY.md:46`) accurately describes the public contract. No-source-edit cycle.

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — pass, 270 files left unchanged.
- `uv run ruff check .` — pass, all checks passed (only the pre-existing COM812/formatter advisory notice).

### Notes for Worker 3
- No-source-edit cycle (shape #5): empty `git log 14910230..HEAD` and empty `git diff HEAD` for `testing/relay.py`. The only this-set change to `testing/` was `testing/__init__.py` (+2, a `0.0.12`→`0.0.14` future-export doc-version bump), out of scope for this artifact.
- No High / no behaviour-changing Medium / zero Lows.
- No GLOSSARY-only fix in scope — `docs/GLOSSARY.md:46` (and the `0.0.9` model-label payload prose at `:97`) accurately describe the public contract; no drift.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern.

Not warranted — no source edits this cycle (AGENTS.md #21 "Do not update CHANGELOG.md unless explicitly instructed"; the active plan `docs/review/review-0_0_10.md` is silent on a changelog entry for this item).

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern.

No comment/docstring edits warranted. The module docstring and the four inline comment blocks are accurate and load-bearing: the Phase-2.5-before-Phase-3 finalize-ordering rationale (`:66-71`), the finalized-but-unstamped non-Relay-Node note (`:79-80`), and the `(root, info)`-untouched justification for the `None, None` arguments (`:92-95`) each document a non-obvious correctness invariant verified above. No stale spec references (spec-032 anchors match the shipped behavior); no TODOs.

---

## Verification (Worker 3)

Shadow dictum (first pass): the shadow strips `#` comments and string tokens, so its line numbers are not canonical. Treated original `testing/relay.py` line numbers and the artifact's references as authoritative; the shadow (`docs/shadow/django_strawberry_framework__testing__relay.overview.md`) was used only for control-flow confirmation (4 imports, 1 symbol, 1 branch hotspot, 4x `global_id_for:` repeated literal — matches source).

Baseline note: dispatch SHA `14910230` predates current HEAD `58ca2def`; `git diff HEAD` and `git diff 14910230` for `testing/relay.py` are both empty and `git log 14910230..HEAD -- testing/relay.py` is empty, so the SHA drift is cosmetic (content-not-identifier — same pattern as prior cycles). `testing/relay.py` is absent from the cycle-wide diff stat.

### Logic verification outcome
No-source-edit cycle (shape #5); no High/Medium/Low findings to disposition. Independently re-derived every load-bearing claim against canonical source:
- **Strategy partition is exact.** `STRING_GLOBALID_STRATEGIES = {model, type, type+model}` (`types/base.py:122`); `MODEL_LABEL_STRATEGIES = {model, type+model}` (`types/relay.py:413`). Residual = exactly `{type}`. In `encode_typename` (`types/relay.py:481-493`): `callable` first (the ONLY branch reading `root`/`info`, :482), then `MODEL_LABEL_STRATEGIES → model._meta.label_lower` (:490-491), else `type → graphql_type_name` (:493). So the helper's `:85` gate admits exactly the three string strategies and each routes to a `(root,info)`-free branch.
- **`(root, info)=None` delegation is provably safe.** `callable`/`custom` are rejected at `relay.py:85` BEFORE `encode_typename` is reached at `:96`, so the `callable(strategy)` branch is unreachable from this helper — passing `None, None` cannot crash. Verified the gate precedes the call in source, not just the artifact's prose.
- **Gate ordering defends spec-032 P2.** `None` definition → not-a-DjangoType (`:60`); `not finalized` BEFORE reading the stamp (`:65`); `strategy is None` → non-Relay-Node (`:78`); non-string-strategy (`:85`). The finalized-first ordering is the partial-finalize defense (stamp written Phase 2.5, `finalized` flipped Phase 3) and is pinned by `test_global_id_for_strategy_stamped_but_unfinalized_raises` (`tests/testing/test_relay.py:209-233`, monkeypatches a strategy onto an unfinalized type and asserts the not-finalized message wins).
- **Decode round-trip + re-export identity.** `decode_global_id` is a single def (`types/relay.py:634`) re-exported verbatim; `test_public_decode_round_trip_primary_and_type_name` pins both the round-trip (`:249-250`) AND `testing_relay.decode_global_id is types_relay.decode_global_id` (`:252`). The documented secondary→primary asymmetry is pinned by `test_secondary_model_label_emitter_decodes_to_primary` (`:255-266`) — correct routing, not a bug.
- **Public-API back-compat intact.** `__all__ = ["decode_global_id", "global_id_for"]` (`:47`); submodule-path-only export (not re-exported from `testing/__init__`); GLOSSARY (`docs/GLOSSARY.md:46`) accurately describes the strategy-aware contract and the submodule-path discipline.

All ten branches are pinned by named tests in `tests/testing/test_relay.py` (three string strategies each with a `live_id ==` equality assertion at :94/:110/:125, callable/custom :169, unfinalized :183, non-Node :193, non-DjangoType :205, stamped-but-unfinalized :209, decode round-trip :249, asymmetry :255). Focused run `uv run pytest tests/testing/test_relay.py --no-cov` = 10 passed.

### DRY findings disposition
DRY None is sound and verified by grep/read: `global_id_for` delegates payload to the single-sourced `encode_typename`, imports the strategy set + the two gate constants from `types/base.py` (`STRING_GLOBALID_STRATEGIES` :122; `_RELAY_NODE_GATE_LEAD` :107 / `_RELAY_NODE_GATE_INHERIT_TAIL` :113 — the latter's hoist comment at `types/base.py:108-109` explicitly names `global_id_for` as the byte-identical 3rd compose site), and re-exports `decode_global_id` verbatim. Nothing duplicated locally. The 4x `"global_id_for:"` prefixes are distinct per-message human strings with separate subjects/remediation, not a dispatch key — correct inline.

### Temp test verification
- None — claims were verifiable by direct source/test read + the existing permanent suite; no temp test needed.
- Disposition: n/a.

### Verification outcome
`cycle accepted; verified` — sets top-level `Status: verified` AND marks the `testing/relay.py` checklist box in `docs/review/review-0_0_10.md`.

Shape #5 gates all met: every Worker 2 section carries `Filled by Worker 1 per no-source-edit cycle pattern.`; no High/behaviour-Medium/Lows; no GLOSSARY-only fix; changelog `Not warranted` with both citations (AGENTS.md #21 + active-plan silence) and empty `git diff -- CHANGELOG.md`; ruff format-check + check pass on the target.

---

## Iteration log

(none)
