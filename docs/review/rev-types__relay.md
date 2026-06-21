# Review: `django_strawberry_framework/types/relay.py`

Status: verified

## DRY analysis

- None — this module IS its own resolution layer for the GlobalID strategy memberships and the model lookup. The two payload-shape sets are single-sourced as `MODEL_LABEL_STRATEGIES` / `TYPE_NAME_STRATEGIES` (`types/relay.py:402-403`) and consumed by the encode/decode predicates (`_emits_model_label`/`_accepts_model_label_decode`/`_accepts_type_name_decode`, `:406-439`), the encoder (`encode_typename`, `:479`), and `filters/base.py::_accepted_globalid_type_names` — no site re-types `{"model", "type+model"}` / `{"type", "type+model"}`. The four resolver names + defaults are single-sourced in `_RELAY_RESOLVER_DEFAULTS` (`:906-911`, "appears nowhere else"). The model handle read is now single-sourced in `utils/querysets.py::model_for` (the `model_for` promotion, commit `7a17ba75`); the prior in-module `_model_for` twin was removed and its three call sites delegate to the import. No remaining duplication candidate.

## High:

None.

## Medium:

None.

## Low:

None.

## What looks solid

### DRY recap

- **Existing patterns reused.** `model_for` (`utils/querysets.py:94`) at the three model-only read sites (`install_is_type_of` `:111`, `_check_composite_pk_for_relay_node` `:173`, `_order_nodes` `:762`) — the verbatim `__django_strawberry_definition__.model` read centralized in the `7a17ba75` promotion. Visibility seam reuses the canonical `apply_type_visibility_sync`/`apply_type_visibility_async` + `initial_queryset` (`:807-808`, `:828`, `:868`, `:893`); the sync path rejects an async `get_queryset` coroutine through the shared `SyncMisuseError` contract. `_apply_node_filter` (`:315`) is the one color-agnostic filter builder shared by both sync and async node/nodes paths; `_order_nodes` (`:739`) is the one order-preserving map_results port shared by `_resolve_nodes_default` + `_resolve_nodes_async`. `_validate_globalid_strategy` (`base.py`) validates BOTH the `Meta` path and the setting path via `_resolve_globalid_strategy` (`:383`) — one validator, two sources.
- **New helpers considered.** No new helper at this granularity. The two-member membership frozensets are already hoisted; the resolver-defaults tuple is already single-sited; the `__func__`-identity override discriminator is structurally shared across `install_relay_node_resolvers` and `_consumer_overrode_resolve_typename` but the questions differ (four-name loop vs single `resolve_typename` + framework-closure-marker exemption), so folding would obscure the marker special-case — rejected.
- **Duplication risk in the current file.** Repeated literals are non-hoistable: `__func__` (5x) is the MRO-identity protocol token read off heterogeneous objects; `decode_global_id:` (3x) is the per-error-message namespacing prefix in `ConfigurationError` strings (deliberate caller-naming); `type+model` (2x) and `resolve_typename` (2x) are distinct-role string reads, not dispatch keys. `_emits_model_label` and `_accepts_model_label_decode` share `MODEL_LABEL_STRATEGIES` membership but are named distinctly on purpose (encode-emit vs decode-accept), with the divergence-split documented inline (`:419-425`) — intentional sibling design.

### Other positives

- **`model_for` promotion is semantics-identical.** The removed private `_model_for` was `return cls.__django_strawberry_definition__.model`; `utils/querysets.py::model_for` returns the same attribute verbatim (`querysets.py:94`). The handle is used only for the `is_type_of` isinstance target, the composite-pk `_meta.pk` gate, and the `_order_nodes` `DoesNotExist` raise — never as a visibility queryset seed (that stays `apply_type_visibility_* → initial_queryset` at `:807`/`:828`/`:868`/`:893`), so no existence-leak or refetch regression. `grep -rn _model_for` returns zero — the twin is fully removed, no orphan.
- **Strategy precedence is correct and single-validated.** `_resolve_globalid_strategy` (`:341`) honors `Meta.globalid_strategy` → `RELAY_GLOBALID_STRATEGY` setting (read defensively, absent → default) → `DEFAULT_GLOBALID_STRATEGY` ("model"), with the setting branch validated through the same `_validate_globalid_strategy` rule the Meta path uses (`relay_shaped=True`). Matches GLOSSARY `Meta.globalid_strategy` / `RELAY_GLOBALID_STRATEGY` precedence prose byte-for-byte.
- **Encode/decode model-label vs type-name routing is airtight.** `encode_typename` (`:442`) emits `definition.model._meta.label_lower` for `model`/`type+model`, `graphql_type_name` for `type`, and validates a non-empty `str` callable return before Strawberry's `assert isinstance` could fire opaquely. `decode_global_id` (`:623`) gates input type → parses → resolves a candidate (dotted label → `apps.get_model` → `registry.get`; bare name → `definition_for_graphql_name`) → enforces the recorded `effective_globalid_strategy` permits the payload shape, collapsing every failure mode to one uniform `ConfigurationError` so client-controlled input never leaks `GlobalIDValueError`/`KeyError`/`AttributeError`. `callable`/`custom` are absent from both membership sets (encode-only in 0.0.9) — the "no decode" contract IS their absence, with no `{"callable","custom"}` literal anywhere.
- **`is_type_of` injection contract preserved.** The `_NODE_TYPE_HINT_ATTR` stamp (set by root refetch fields) takes precedence over the isinstance fallback (`:114-117`), resolving the multiple-types-per-model collapse: without the hint, every candidate's `is_type_of` answers True for the same bare instance and graphql-core's iteration order picks `__typename`. Consumer-declared `is_type_of` preserved via the `cls.__dict__` membership discriminator (`:109`).
- **Cross-module wiring re-verified at source.** `install_is_type_of` consumed by `base.py:650`; `install_relay_node_resolvers` + `install_globalid_typename_resolver` by `finalizer.py:657-658`; `decode_global_id` + `_NODE_TYPE_HINT_ATTR` by root `relay.py:65`/`:94`/`:217`/`:310`. The three in-function imports (`conf`/`base` at `:372-373`, `registry` at `:670`) are documented cycle-dodges resolved only at finalization/decode (well after module load), mirroring `base.py`'s FilterSet/OrderSet pattern — no module-top back-edge.
- **Re-entrancy / partial-finalize safety.** `install_globalid_typename_resolver` step-0 guard skips a type whose `effective_globalid_strategy` is already recorded; the `_FRAMEWORK_CLOSURE_MARKER` (`:494`) distinguishes a framework closure inherited through the MRO from a consumer override, so a Phase-2.5 raise + finalizer re-entry never misclassifies the type `custom`. `_stamp_relay_id_attr` seeds `_id_attr = None` into the class's own `__dict__` to blind upstream's inherited-cache read (order-dependent-shadowing fix) and turns the per-row `"pk"`-fallback rescan into one `__dict__` read.

### Summary

`types/relay.py` is unchanged since the per-cycle baseline (`fec882b7`): both `git diff <baseline> -- types/relay.py` and `git diff HEAD -- types/relay.py` are empty, and `git log <baseline>..HEAD -- types/relay.py` returns nothing — the maintainer's DRY-cycle `model_for` promotion (commit `7a17ba75`) is fully cumulative-in-HEAD, not a pending edit. That change drops the private `_model_for` twin and routes its three call sites through `utils/querysets.py::model_for`, which returns the same `__django_strawberry_definition__.model` attribute verbatim — semantics fully preserved, no leak/refetch/ordering regression. Strategy precedence (Meta → setting → default), model-label vs type-name encode/decode routing, the multi-type-per-model `is_type_of` hint resolution, and all cross-module install/decode wiring re-verify clean at source. Every symbol in the file is private (no `__all__`; `SyncMisuseError` is a re-export defined in `utils/querysets.py`), so the contract-level GLOSSARY prose (`#djangonodefield`, `#djangonodesfield`, `Meta.globalid_strategy`, `RELAY_GLOBALID_STRATEGY`, Relay Node integration) abstracts over these internal helpers and shows no drift. No High/Medium/Low findings; DRY is the single `None —`. Genuine no-source-edit cycle (shape #5).

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — pass; "289 files left unchanged".
- `uv run ruff check --fix .` — pass; "All checks passed!".

### Notes for Worker 3
- No-source-edit cycle (shape #5). Both `git diff fec882b7 -- types/relay.py` and `git diff HEAD -- types/relay.py` empty; `git log fec882b7..HEAD -- types/relay.py` empty; the spawn-named `model_for` promotion (commit `7a17ba75`) is cumulative-in-HEAD, semantics-identical (verbatim `__django_strawberry_definition__.model` return).
- All findings `None.` No GLOSSARY-only fix in scope: every symbol in the file is private (no `__all__`); `SyncMisuseError` is a re-export defined in `utils/querysets.py`; the relevant GLOSSARY prose is contract-level and shows no drift.

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern. No comment or docstring edits: the module's docstrings and inline comments accurately describe current behavior (the import comment at `:37-40` documents the `SyncMisuseError` re-export; the cycle-dodge comments at `:366-371`/`:665-669` match the in-function imports; no stale `_model_for` reference survives).

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern. Not warranted — no source edit this cycle. Per AGENTS.md "Do not update CHANGELOG.md unless explicitly instructed" and the active plan (`docs/review/review-0_0_11.md`) records no changelog requirement for review-cycle artifacts.

---

## Verification (Worker 3)

### Logic verification outcome
Shape-#5 no-source-edit cycle confirmed on all four zero-edit axes: `git diff fec882b7 -- types/relay.py`, `git diff HEAD -- types/relay.py`, `git log fec882b7..HEAD -- types/relay.py`, and the owned-paths `--stat` (`django_strawberry_framework/ tests/ docs/GLOSSARY.md CHANGELOG.md`) are all empty. CHANGELOG diff empty. Dirty tree is `docs/` only (review artifacts, dry/feedback, spec-038) — no sibling attribution into the target needed. All severities `None.`; each Worker 2 section opens with the `Filled by Worker 1 per no-source-edit cycle pattern.` gate line. No Low findings to forward; no GLOSSARY-only fix.

`model_for` promotion independently confirmed semantics-identical and regression-free:
- `git show HEAD:utils/querysets.py` → `model_for` returns `type_cls.__django_strawberry_definition__.model` verbatim (querysets.py:105) — byte-identical to the removed private `_model_for`.
- `grep -rn _model_for django_strawberry_framework/` → ZERO; the private twin is fully removed, no orphan.
- `grep -n model_for types/relay.py` → import (46) + exactly 3 call sites: `install_is_type_of:111` (handle → isinstance fallback target only), `_check_composite_pk_for_relay_node:173` (handle → `_meta.pk` CompositePrimaryKey gate + `DoesNotExist`/error-name only), `_order_nodes:762` (handle → `model.DoesNotExist` raise + `__name__` only). None feed a visibility queryset seed.
- Visibility seed stays `get_queryset`-routed and handle-independent: the four resolver paths seed via `apply_type_visibility_{sync,async}(cls, initial_queryset(cls), info)` at :807/:828/:868/:893 — `initial_queryset` derives its own model lookup, never the `model_for` handle returned to the resolver body → no existence-leak / refetch / ordering regression.

Spot-checks re-confirmed at source: strategy precedence Meta → `RELAY_GLOBALID_STRATEGY` setting (defensive `getattr`, absent → default) → `DEFAULT_GLOBALID_STRATEGY = "model"` (base.py:123), setting branch validated through the same `_validate_globalid_strategy` (`relay_shaped=True`) the Meta path uses (`_resolve_globalid_strategy:341`). Encode model-label vs type-name routing (`encode_typename:442`, `MODEL_LABEL_STRATEGIES`/`TYPE_NAME_STRATEGIES` frozensets), decode resolve-then-enforce collapsing all failure modes to one `ConfigurationError` (`decode_global_id:623`), the multi-type-per-model `is_type_of` hint precedence (`_NODE_TYPE_HINT_ATTR`, :114-117), and the `_FRAMEWORK_CLOSURE_MARKER` override-vs-inherited-closure discriminator all read clean. `callable`/`custom` absent from both membership sets — the no-decode contract IS their absence, no `{"callable","custom"}` literal.

Tests pin the load-bearing behaviors at `tests/types/test_relay_interfaces.py`: `test_model_for_returns_registered_model` (the promoted helper), `test_is_type_of_injected_for_all_djangotypes` / `test_consumer_declared_is_type_of_is_preserved` (injection + override discriminator), `test_relay_node_with_composite_pk_raises` / `test_relay_chain_composite_pk_child_still_gated` (composite-pk gate via the `_meta.pk` handle), `test_resolve_nodes_required_raises_for_missing` / `test_resolve_nodes_preserves_order_and_missing` (`_order_nodes` `DoesNotExist` + ordering), `test_resolve_node_applies_get_queryset` and the `*_awaits_async_get_queryset` async siblings (visibility seam stays `get_queryset`-routed). No new test introduced this cycle — none required.

### DRY findings disposition
DRY-None genuine. `model_for` is single-sited in `utils/querysets.py` and consumed by import at the three model-only read sites; the membership frozensets and `_RELAY_RESOLVER_DEFAULTS` are each single-sourced. No remaining duplication candidate.

### Temp test verification
None — no temp tests created; the existing permanent suite already pins every load-bearing claim.

### Verification outcome
`cycle accepted; verified` — sets top-level `Status: verified` AND marks the `types/relay.py` checklist box in `docs/review/review-0_0_11.md`.

Validation: `uv run ruff format --check types/relay.py` (already formatted), `uv run ruff check types/relay.py` (All checks passed). All symbols private (no `__all__`; `SyncMisuseError` re-export defined in `utils/querysets.py`) → contract-level GLOSSARY prose abstracts over these helpers, absence of entries correct, genuine #5 not a missed #4.

---

## Verification (Worker 3) — END
