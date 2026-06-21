# Review: `django_strawberry_framework/types/finalizer.py`

Status: verified

## DRY analysis

- None — the module is already its own DRY resolution. The two phase-2.5 owner-binding flows are single-sourced through `types/finalizer.py::_bind_set_owner_common` and the four-subpass driver through `types/finalizer.py::_bind_sidecar_sets` + the frozen `types/finalizer.py::_SidecarBindingSpec` config object (the 0.0.9 DRY pass, `docs/feedback.md` Major 2); `_bind_filterset_owner` / `_bind_orderset_owner` and `_bind_filtersets` / `_bind_ordersets` are thin per-family parameterizations. The remaining `_format_*` helpers are a deliberate one-formatter-per-error-string family clustered at the top of the module so finalize-time error strings stay grep-stable for tests and consumer error matching (stated in every formatter's docstring) — folding them behind a generic builder would obscure the literal error text the tests pin against, a net readability loss. No act-now or defer-with-trigger consolidation exists.

## High:

None.

## Medium:

None.

## Low:

None.

## What looks solid

### DRY recap

- **Existing patterns reused.** Owner-binding logic single-sourced via `_bind_set_owner_common` (finalizer.py:723-807), consumed by both `_bind_filterset_owner` (finalizer.py:847) and `_bind_orderset_owner` (finalizer.py:1027) through hook callables. The four-subpass binding skeleton single-sourced via `_bind_sidecar_sets` (finalizer.py:1192-1268), driven by the frozen `_SidecarBindingSpec` (finalizer.py:1116-1136) and consumed by `_bind_filtersets` (finalizer.py:1377) + `_bind_ordersets` (finalizer.py:1317). Relation-connection slot writes single-sourced via `_record_relation_connection` (finalizer.py:334-349), called from both the first-attach and re-entrancy branches of `_synthesize_relation_connections`. List-form suppression single-sourced via `_suppress_relation_list_form` (finalizer.py:320-331). The multi-type-model walk is materialized once (finalizer.py:571) and shared by `_audit_primary_ambiguity` + `_audit_model_label_routing` + `_warn_model_label_secondary_collapse` so `registry.models_with_multiple_types()` is invoked exactly once per build.
- **New helpers considered.** A generic error-string builder folding the `_format_*` family was evaluated and rejected — the per-string formatters keep the literal error text grep-stable for the spec-pinned tests (`spec-018 #"test_finalize_ambiguity_error_message_contains_actionable_fix"`, etc.); a builder would indirect the text away from the test-matched site. Folding `_first_model_label_emitter`'s strategy read into the collapse warning was rejected — the emitter helper already single-sources the per-type `effective_globalid_strategy` read (finalizer.py:248-260) and the warning needs the full secondary list, not the first emitter.
- **Duplication risk in the current file.** The `<unresolved>` literal (5x) and the `relay_node=` / `type_name=` fragments (2x each) are surface text inside sibling `_format_*` messages, not dispatch keys — intentional per-message wording. The `_meta.model.__name__` direct read in `_format_owner_model_mismatch_error` (finalizer.py:952) vs the defensive `getattr(...,"Meta",None)`-then-`None`-fallback in `_format_owner_orderset_model_mismatch_error` (finalizer.py:1079-1080) is the documented set-family divergence: FilterSet carries a metaclass-built `_meta` options object (always present, and the filter mismatch only fires after `_bind_set_owner_common` confirmed `set_model is not None`), while OrderSet exposes only a raw `Meta` namespace, so the order formatter must degrade to `<unset>`. Not a unify candidate.

### Other positives

- **Phase-1 failure-atomicity is real and load-bearing.** `_audit_primary_ambiguity` and the unresolved-target detection (finalizer.py:573, 602-603) both complete *before* any `__annotations__` mutation (the resolved-relation rewrite at finalizer.py:606-611), so a config error leaves every collected class intact for a re-call. The multi-type walk materialized at finalizer.py:571 is a pure read that does not disturb this contract, per its inline comment.
- **Once-only / partial-recovery contract is consistent across every phase.** Entry-guard `registry.is_finalized()` (finalizer.py:561), per-loop `if definition.finalized: continue` heads (Phase 2 finalizer.py:623, Phase 2.5 :646, synthesis :408, Phase 3 :715), and `registry.mark_finalized()` as the strict last statement (finalizer.py:720) — a raise in Phase 2/2.5/3 leaves the flag False and the re-entrancy markers (`_SYNTHESIZED_RELATION_CONNECTION_MARKER`, the `_suppress_relation_list_form` tolerant pops, idempotent `_record_relation_connection`) make a rerun safe. The synthesis re-entrancy branch correctly re-suppresses the list form for `"connection"` shapes on rerun (finalizer.py:457-458, spec-032 feedback P1) and re-records the walker slot (finalizer.py:464) so a fresh post-`clear()` definition is not skipped.
- **Phase ordering is documented and justified at each seam.** Phase 2 (resolvers) before Phase 2.5 (interface injection) with the latent-ordering note (finalizer.py:615-621) flagging the swap-and-pin recourse if a future Strawberry interface ships a same-named `resolve_<field>` default; relation-connection synthesis before `_bind_filtersets`/`_bind_ordersets` so `_synthesized_signature` sidecar registrations are orphan-validated in the same finalize (finalizer.py:677-682); `bind_mutations` after primary-type state settles and before Phase 3 (finalizer.py:695-710).
- **Error rewrap into `ConfigurationError` is uniform and preserves `__cause__`.** `_bind_sidecar_sets` subpass 2 (finalizer.py:1228-1242) catches `ImportError` (lazy-target rewrap), re-raises bare `ConfigurationError`, and rewraps any other `Exception` with `repr(exc)` + `from exc`. The PERF203 per-iteration try is intentional and commented (attributes failure to the specific `set_cls`). Orphan validation runs *before* materialization (finalizer.py:1248-1257) so a failure leaves no half-materialized input classes in the module namespace.
- **Function-local plain imports are the deliberate cycle-dodge.** `_synthesize_relation_connections`'s `..connection` import (finalizer.py:404), the `..relay._node_fields_declared` read (finalizer.py:670), `..mutations.sets.bind_mutations` (finalizer.py:708), and the filter/order subsystem imports (finalizer.py:1313-1315, :1373-1375) are all plain (no try/except) because a contract step must never be silently skipped — the comments state this and contrast it with `registry.clear()`'s best-effort teardown. Import direction is one-way (`types/` is imported *by* connection/relay/mutations/filters/orders), so the locals break the cycle without masking failures.
- **Reflective access is guarded.** Every `getattr` carries a default (`_owner_definition` finalizer.py:767, `related_orders`/`related_filters` :782/:1155/:1176, `Meta`/`model` chains :998-999/:1030/:1079, `spec.definition_attr` :1218, the marker probe :449), and the lone `isinstance(v, StrawberryField)` collision-surface scan (finalizer.py:469) plus `issubclass` model-derivation check (finalizer.py:773) are both load-bearing.
- **GLOSSARY accuracy verified.** `finalize_django_types` (GLOSSARY:552-573) contract prose matches the source: no-op on second call (finalizer.py:561-562), post-finalize declaration raises `ConfigurationError`, `registry.clear()` as fresh-lifecycle escape hatch. `Meta.relation_shapes` (GLOSSARY:880-884) and connection-aware planning (GLOSSARY:260-262) match `_synthesize_relation_connections` byte-for-byte: the `"list"`/`"connection"`/`"both"` shapes, the fail-loud-on-explicit-`"connection"`/`"both"` vs silent-degrade-on-implicit split for non-Node targets (finalizer.py:426-443), per-target connection-class reuse, and the `relation_connections` walker metadata (written finalizer.py:347-349, read walker.py:331/344/348). No drift on any documented public-contract symbol.

### Summary

`finalize_django_types()` is the package's once-only build gate and the only place `strawberry.type` decoration touches a consumer class. The four-phase pipeline (failure-atomic Phase 1 relation resolution, Phase 2 resolver attach, Phase 2.5 interface/relay/connection/sidecar binding, Phase 3 decoration) is correct, with the once-only guard, per-phase `finalized` skips, and `mark_finalized()`-as-last-statement giving a coherent partial-recovery-on-rerun contract that the re-entrancy markers and tolerant removals all respect. Phase ordering, error rewrap into `ConfigurationError` with `__cause__` preserved, orphan-before-materialization sequencing, and cycle-safe function-local imports are each documented at their seam and verified at source. DRY is already maximal — owner binding and the four-subpass driver are single-sourced, and the `_format_*` family's per-string layout is a deliberate grep-stable test-contract choice, not duplication. No-source-edit cycle: `git diff` against the per-cycle baseline `5f4c87a4` and against `HEAD` are both empty, `git log baseline..HEAD -- <target>` is empty, no High / no behavior-changing Medium, every severity `None.`, and the GLOSSARY needs no edit. Qualifies as shape #5.

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — pass, "289 files left unchanged".
- `uv run ruff check --fix .` — pass, "All checks passed!".

### Notes for Worker 3
- All severities `None.`; DRY analysis is a single `None —` (module is its own DRY resolution).
- No GLOSSARY-only fix in scope: `finalize_django_types` (GLOSSARY:552-573), `Meta.relation_shapes` (GLOSSARY:880-884), and connection-aware-planning (GLOSSARY:260-262) prose all verified accurate against source; no edit needed.
- Both `git diff 5f4c87a4 -- django_strawberry_framework/types/finalizer.py` and `git diff HEAD -- ...` are empty; `git log 5f4c87a4..HEAD -- <target>` returns nothing — the file is fully settled in HEAD, no pending edit.

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern.

No comment/docstring changes warranted. Docstrings and inline comments are accurate and load-bearing (phase-ordering rationale, partial-recovery contract, cycle-safe-import justification, re-entrancy markers). TODO scan: none in this file.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern.

Not warranted — no source change in this cycle. `AGENTS.md` ("Do not update CHANGELOG.md unless explicitly instructed") and the active plan `docs/review/review-0_0_11.md` (silent on changelog edits for this item) both apply.

---

## Verification (Worker 3)

### Logic verification outcome
No-source-edit (shape #5) cycle. Every severity is `None.` and the DRY analysis is a single `None —`; there are no findings to address or reject, so the false-premise rule does not engage. The substantive verification is the genuine-#5 / not-missed-#4 confirmation below.

Independently confirmed against live source:
- **Once-only / partial-recovery contract** — entry guard `registry.is_finalized()` (finalizer.py:561-562, no-op second call); per-phase `if definition.finalized: continue` heads; `registry.mark_finalized()` as the strict last statement (finalizer.py:720) so a Phase 2/2.5/3 raise leaves the flag False. Re-entrancy markers (`_SYNTHESIZED_RELATION_CONNECTION_MARKER`, tolerant `_suppress_relation_list_form` pops, idempotent `_record_relation_connection`) make a rerun safe.
- **Phase ordering** — relation resolution (Phase 1 failure-atomic, audits + unresolved check before any `__annotations__` mutation) → Phase 2 resolver attach → Phase 2.5 sidecar/connection/relation-shape binding: `_synthesize_relation_connections()` (682) runs BEFORE `_bind_filtersets`/`_bind_ordersets` (711-712) so `_synthesized_signature` sidecar registrations are orphan-validated in the same finalize; `bind_mutations()` (710) after primary-type state settles, before Phase 3.
- **ConfigurationError rewrap** — `_bind_sidecar_sets` subpass 2 (finalizer.py:1228-1242) catches `ImportError` (lazy-target rewrap), re-raises bare `ConfigurationError`, rewraps any other `Exception` with `repr(exc)` + `from exc`. Orphan validation (subpass 3, 1248-1257) runs before materialization (subpass 4) so a failure leaves no half-materialized input classes.
- **Single-sourced helpers (DRY-None)** — `_bind_set_owner_common` is 1 def / 2 callers (`_bind_filterset_owner`:847, `_bind_orderset_owner`:1027); `_bind_sidecar_sets` is 1 def / 2 callers (the two `mutations/sets.py` hits are a *documented deliberate divergence* per spec-036 Decision 5, NOT a `_bind_sidecar_sets` consumer — no straggler call site). `_record_relation_connection` / `_suppress_relation_list_form` each single-sourced with first-attach + re-entrancy call sites. `models_with_multiple_types()` invoked exactly once (finalizer.py:571) and shared by both audits.

### DRY findings disposition
DRY-None confirmed genuine. The `_format_*` family is a deliberate one-formatter-per-error-string cluster kept grep-stable for spec-pinned tests — `tests/test_registry.py::test_finalize_ambiguity_error_message_contains_actionable_fix` exists and pins the actionable-fix sentence. No act-now or defer-with-trigger consolidation exists.

### Temp test verification
- None used. All severities `None.`; no behavior under suspicion.
- Disposition: n/a.

### Verification outcome
`cycle accepted; verified` — sets top-level `Status: verified` AND marks the checklist box.

Zero-edit proof (shape #5): `git diff 5f4c87a4 -- django_strawberry_framework/types/finalizer.py` empty; `git diff HEAD -- <target>` empty; `git log 5f4c87a4..HEAD -- <target>` empty; owned-paths `git diff --stat 5f4c87a4 -- django_strawberry_framework/ tests/ docs/GLOSSARY.md CHANGELOG.md` empty; `git diff -- CHANGELOG.md` empty. Working tree dirt is all `docs/` (review artifacts / dry / feedback / spec) — no source, test, GLOSSARY, or CHANGELOG hunk; no sibling-cycle attribution needed.

Shape #5 gates: all three Worker 2 sections open with `Filled by Worker 1 per no-source-edit cycle pattern.`; every High/Medium/Low is `None.`; no GLOSSARY-only fix in scope.

Genuine #5, not a missed #4: `finalize_django_types` (GLOSSARY:552) and `Meta.relation_shapes` (GLOSSARY:880) prose verified accurate against live source (no-op second call, post-finalize ConfigurationError, `registry.clear()` escape hatch; the `"list"`/`"connection"`/`"both"` shapes, implicit-`"both"` default, fail-loud-on-explicit vs silent-degrade-on-implicit split for non-Node targets, type-creation-vs-finalization validation split). Both are the only public finalizer symbols in `types/__init__.__all__` (`DjangoType`, `SyncMisuseError`, `finalize_django_types`); all `_`-prefixed helpers correctly carry no GLOSSARY entry — absence is not drift.

Changelog `Not warranted` cites both required sources (AGENTS.md + active-plan silence) and matches the empty diff; internal-only framing matches the no-source-change scope.

`uv run ruff format --check` — "1 file already formatted". `uv run ruff check` — "All checks passed!".
