# Review: `django_strawberry_framework/types/relay.py`

Status: verified

## DRY analysis

- None — this module IS the single source of the Relay GlobalID machinery. The "strategy → payload shape" memberships are already centralized: `MODEL_LABEL_STRATEGIES` / `TYPE_NAME_STRATEGIES` frozensets (`types/relay.py:413-414`) back all four predicate helpers (`_emits_model_label`, `_accepts_model_label_decode`, `_accepts_type_name_decode`) and are consumed cross-file by `filters/base.py::_accepted_globalid_type_names` rather than re-typing `{"type","type+model"}` at each site. The four `resolve_*` method names live once in `_RELAY_RESOLVER_DEFAULTS` (`types/relay.py:917-922`). The model-lookup is delegated to `_model_for` (`types/relay.py:335-344`), which the docstring explicitly pairs with `utils/querysets.py::initial_queryset` as a deliberate two-source mirror (model-only vs queryset-variant), not duplication. `_accepts_model_label_decode` and `_emits_model_label` share one frozenset but carry distinct names by design — the docstring states Slice 3 will split them only if encode/decode acceptance ever diverges. Folding any of these heterogeneous-body siblings would re-couple deliberately-distinct strategy semantics.

## High:

None.

## Medium:

None.

## Low:

### `decode_global_id` model-label branch relies on a second-tier `definition is not None` guard that the type-name branch can never trip

In `decode_global_id` (`types/relay.py:708-734`) the model-label branch sets `definition = registry.get_definition(target_type)` (`registry.get_definition` returns `DjangoTypeDefinition | None`), while the type-name branch sets `definition = registry.definition_for_graphql_name(type_name)` which **raises** `ConfigurationError` on miss/ambiguity (never returns `None`). The downstream `strategy = definition.effective_globalid_strategy if definition is not None else None` (`types/relay.py:729`) therefore only ever exercises its `else None` arm via the model-label path — when `registry.get(model)` returns a non-`None` `target_type` whose `get_definition` is nevertheless `None`. That window is real (a registered type whose definition was discarded mid-state) and the guard correctly funnels it into the "no recorded GlobalID strategy" raise (`types/relay.py:730-734`), preserving the no-existence-leak contract. This is correct as written; the only Low is that the asymmetry (one branch raises, one returns `None`) is implicit. Defer with trigger: "When a fourth resolution branch lands, or `definition_for_graphql_name` is changed to return `None` instead of raising, add a one-line comment at `types/relay.py:729` stating which branch supplies the `None` so the guard's purpose stays legible." No current defect — both upstream contracts are honored and exercised by package tests.

## What looks solid

### DRY recap

- **Existing patterns reused.** `_model_for` (`types/relay.py:335-344`) is the single model-only lookup, documented as the deliberate mirror of `utils/querysets.py::initial_queryset`. The strategy-membership frozensets `MODEL_LABEL_STRATEGIES` / `TYPE_NAME_STRATEGIES` (`types/relay.py:413-414`) are the cross-file single source consumed by `filters/base.py`. The string constants `DEFAULT_GLOBALID_STRATEGY` / `STRING_GLOBALID_STRATEGIES` are imported from `types/base.py` (in-function, `types/relay.py:384`) rather than re-typed. `_validate_globalid_strategy` is the one validator serving both the `Meta` path and the setting path (`types/relay.py:394-399`) — one rule, two sources. `_RELAY_RESOLVER_DEFAULTS` (`types/relay.py:917-922`) is the single name→default table.
- **New helpers considered.** Collapsing `_accepts_model_label_decode` / `_emits_model_label` into one (they share `MODEL_LABEL_STRATEGIES`) was rejected — the docstrings document encode-acceptance vs decode-acceptance as semantically distinct axes that Slice 3 splits on divergence; merging now would erase the intended seam. Folding `_resolve_node_default` / `_resolve_nodes_default` and their async siblings was rejected — single-vs-batch fetch shapes differ in materialization and ordering (`_order_nodes`), heterogeneous bodies.
- **Duplication risk in the current file.** Repeated literals are intentional sibling design: `"type+model"` (×2) appears once in each frozenset membership (the whole point of the two sets); `"decode_global_id:"` (×3) is the human-readable error-message prefix on three distinct failure messages, not a dispatch key; `__func__` (×5) is the override-discriminator idiom shared by `install_relay_node_resolvers` and `_consumer_overrode_resolve_typename`, each reading a different attribute. None warrant a constant.

### Other positives

- **Three-tier precedence is exactly the documented contract.** `_resolve_globalid_strategy` (`types/relay.py:389-400`) returns `definition.globalid_strategy` (Meta) → validated `RELAY_GLOBALID_STRATEGY` setting → `DEFAULT_GLOBALID_STRATEGY`, matching GLOSSARY:720/1104 `Meta.globalid_strategy → RELAY_GLOBALID_STRATEGY → "model"` precisely. The setting path is run through the SAME `_validate_globalid_strategy` rule as the Meta path with `source="setting"`, so a malformed setting names the setting rather than failing opaquely from the installed closure — `conf.py` stays a thin reader, validation lives at the domain layer.
- **No-existence-leak is structurally enforced.** `decode_global_id` rejects out-of-band inputs at the input gate (`types/relay.py:683-687`), empty slots (`:702-706`), unresolvable model labels (`:713-717`), unregistered models (`:719-723`), and — critically — a resolved candidate whose recorded strategy does not permit the payload shape (`:735-745`). `callable`/`custom` (encode-only) and a `None` strategy are both in neither acceptance membership, so a crafted id cannot resolve to a non-Node or mid-state type. Every failure surfaces ONE uniform `ConfigurationError`, never leaking `GlobalIDValueError` / `KeyError` / `AttributeError`. The `GraphQLError` + `GLOBALID_INVALID` translation correctly lives one layer up at the field boundary (root `relay.py::_decode_or_raise`, `relay.py:92-96`), not here — `decode_global_id` is a pure resolve-then-enforce primitive, validated directly by package tests since no shipped `0.0.9` path calls it.
- **Model-label vs type-name routing is symmetric with encode.** `encode_typename` (`types/relay.py:481-493`) emits `model._meta.label_lower` for `model`/`type+model` and `graphql_type_name` for `type`; `decode_global_id` inverts via the dot-presence test (`"." in type_name`, `:708`) → `apps.get_model` + `registry.get` for labels vs `registry.definition_for_graphql_name` for bare names. `definition_for_graphql_name` is keyed on `graphql_type_name` (honoring `Meta.name`), inverting the exact field `encode_typename`'s `type` branch emits.
- **Callable-return guard prevents an opaque upstream AssertionError.** `encode_typename` (`:483-489`) validates a non-empty `str` callable return and raises `ConfigurationError` naming the type + contract, rather than letting Strawberry's `Node._id` `assert isinstance(type_name, str)` fire — arity/sync-ness already validated at type creation, so this is correctly only the per-call return check.
- **Async/sync split is principled.** `_apply_node_filter` (`:314-332`) is the color-agnostic lazy `.filter`; only the terminal materialization differs (`.get`/`.first` vs `.aget`/`.afirst`). The sync path rejects a coroutine `get_queryset` with `SyncMisuseError` rather than producing `AttributeError: 'coroutine' object has no attribute 'filter'`. `in_async_context()` is the single routing predicate.
- **Inheritance-chain hardening is well-reasoned.** `_stamp_relay_id_attr` seeds `_id_attr = None` into the class's own `__dict__` to blind Strawberry's inherited-cache read (kills order-dependent shadowing and per-row rescan); `_RELAY_ID_ATTR_SLOT` / `_FRAMEWORK_CLOSURE_MARKER` / `_NODE_TYPE_HINT_ATTR` are distinct framework slots each documented against a specific multi-type / chain-child failure mode (Round-4 S1/S2). The composite-pk gate asks `relay.Node.resolve_id_attr.__func__(type_cls)` directly to avoid a chain child slipping past via an inherited `"pk"` fallback.
- **Import-cycle discipline is consistent.** The three in-function imports (`conf`/`base` at `:383-387`, `registry` at `:681`) are each documented as the same cycle-dodge `base.py` uses, all on finalize-time/decode-time call paths well after module load. No import-time side effects: module top is functions + two frozensets + string-constant slots only.

### Summary

`types/relay.py` is unchanged since baseline `14910230` (empty `git log 14910230..HEAD` and empty `git diff HEAD`) and is not in any recent changed-file set. It is the single-source GlobalID encode/decode + Relay-resolver-injection machinery: the three-tier `Meta → setting → default` precedence, the model-label/type-name strategy routing, and the malformed-id / no-existence-leak handling all match the documented contract and the GLOSSARY (720/1104/379/387 all consistent — no drift). DRY is genuinely `None` — every shared membership/name/validator is already centralized here or imported from `types/base.py`. One forward-looking Low only (the implicit raise-vs-return-None asymmetry between the two `decode_global_id` resolution branches, correct today, comment-deferred with trigger). No High, no Medium, no source edit. Qualifies as a Shape #5 no-source-edit cycle.

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — pass / no changes to `types/relay.py` (see run note below).
- `uv run ruff check --fix .` — pass / no changes to `types/relay.py` (see run note below).

### Notes for Worker 3
- No shadow regeneration: the plan-time `--all` sweep overview at `docs/shadow/django_strawberry_framework__types__relay.overview.md` is current (source unchanged since baseline).
- Single Low is forward-looking with an explicit trigger; no source edit, no comment edit warranted now.
- No GLOSSARY-only fix in scope — GLOSSARY entries (720/1104/379/387/46) for `decode_global_id` / `Meta.globalid_strategy` / `RELAY_GLOBALID_STRATEGY` / `global_id_for` are all consistent with source; no replacement text staged.
- False-premise note for change-context: the dispatch's claim that `relay.py` does NOT appear in the changed-file set is CONFIRMED (empty `git log 14910230..HEAD` + empty `git diff HEAD`). The registry-cycle O(n)-scan-caller observation (`decode_global_id` → `definition_for_graphql_name` iterates `iter_definitions()`) is a registry-side deferred concern, not a `types/relay.py` defect; not re-litigated here.

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern.

No comment/docstring edits. Docstrings were audited against source during the logic pass: every `resolve_*` signature comment, the cycle-dodge import justifications, the framework-slot rationales, and the `decode_global_id` step-by-step all match the implementation. The single Low is a deferred (trigger-gated) comment addition, not a current defect.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern.

Not warranted. No source/behavior change this cycle (empty diff). Per AGENTS.md #21 ("Do not update CHANGELOG.md unless explicitly instructed") and the active plan `docs/review/review-0_0_10.md` is silent on changelog edits for review cycles.

---

## Verification (Worker 3)

Shape #5 no-source-edit terminal-verify. `types/relay.py` is unchanged this cycle: `git diff HEAD -- django_strawberry_framework/types/relay.py` is empty AND `types/relay.py` is ABSENT from the cycle-wide diff stat (`git diff --stat 14910230 -- django_strawberry_framework/ tests/ docs/GLOSSARY.md CHANGELOG.md` = 28 files, none of them this target). Last-touch `e30d77ab` (2026-06-14) predates HEAD `58ca2def`; prompt baseline `14910230` is stale but cosmetic — verified content by reading source, not by the SHA string.

### Logic verification outcome

All four data-isolation checks independently confirmed against live source:

- **(a) strategy encode/decode correct across model/type/type+model/callable.** `encode_typename` (relay.py:481-493): callable → validated non-empty `str` (else `ConfigurationError` naming the type + contract, pre-empting Strawberry's opaque `assert isinstance`); `model`/`type+model` → `definition.model._meta.label_lower`; `type` → `definition.graphql_type_name`. `decode_global_id` inverts via the dot-presence test (relay.py:708): label path → `apps.get_model` + `registry.get`; bare-name path → `registry.definition_for_graphql_name`. Encode/decode symmetric per shape.
- **(b) precedence Meta→setting→default holds.** `_resolve_globalid_strategy` (relay.py:389-400): returns `definition.globalid_strategy` if non-None (Meta) → `getattr(conf_settings, "RELAY_GLOBALID_STRATEGY", None)` run through the SAME `_validate_globalid_strategy(source="setting")` → `DEFAULT_GLOBALID_STRATEGY`. One validator, two sources; matches GLOSSARY `Meta.globalid_strategy → RELAY_GLOBALID_STRATEGY → "model"`.
- **(c) malformed/missing ids do NOT leak existence.** Every failure path in `decode_global_id` raises ONE uniform `ConfigurationError`: out-of-band type (683), malformed base64 (692), empty slot (702), unknown model label (713), unregistered model (719), no recorded strategy (730), payload-shape not permitted under candidate strategy (740). `callable`/`custom` are in NEITHER acceptance frozenset (413-414), so an encode-only strategy cannot decode a crafted id to a non-Node/mid-state type. Hidden vs missing surface identically. No `GlobalIDValueError`/`KeyError`/`AttributeError`/`LookupError` leak (each caught and re-raised). The `GraphQLError`/`GLOBALID_INVALID` translation correctly lives one layer up at the field boundary (root `relay.py::_decode_or_raise`), not here.
- **(d) Low's asymmetric-branch guard is genuinely correct today; defer sound.** Verified by reading BOTH registry contracts, not the artifact prose: `get_definition` (registry.py:346-348) = `return self._definitions.get(type_cls)` → **can return None** (the model-label branch, relay.py:724); `definition_for_graphql_name` (registry.py:350-385) **raises `ConfigurationError`** on miss/ambiguity and **never returns None** (docstring `Raises:` + body `if not matches: raise` / ambiguity raise), so the type-name branch reads `definition.origin` (727) on a guaranteed-non-None object. Therefore the `definition.effective_globalid_strategy if definition is not None else None` guard at relay.py:729 (and `effective_globalid_strategy: str | None`, definition.py:179) is load-bearing only for the model-label path — a registered model whose definition was discarded mid-state — and funnels that window into the no-strategy raise (730-734), preserving no-leak. Correct as written; the implicit raise-vs-return-None asymmetry is the sole Low. Defer with verbatim in-source trigger ("When a fourth resolution branch lands, or `definition_for_graphql_name` is changed to return `None`...") is sound — no current defect, both upstream contracts honored and exercised by package tests.

No High/Medium present; all artifact High/Medium claims are `None` and consistent with source. The single Low is forward-looking with verbatim trigger phrasing, not a current defect — not a rejection trigger.

### DRY findings disposition

DRY=None confirmed grep-decidable. The two payload-shape frozensets exist exactly once (`MODEL_LABEL_STRATEGIES`/`TYPE_NAME_STRATEGIES`, relay.py:413-414) and are consumed cross-file by `filters/base.py:47,254,256` (imported, not re-typed); `STRING_GLOBALID_STRATEGIES` is single-sourced in `types/base.py:122` and imported in-function. `_model_for` is a single def (relay.py:335). The `_accepts_model_label_decode`/`_emits_model_label` shared-frozenset twins are distinct-by-design (encode vs decode acceptance axes, Slice-3 split-on-divergence seam). Folding any heterogeneous-body sibling would re-couple deliberately-distinct semantics. Carried forward as `None`.

### Temp test verification

None used — the four checks are statically decidable from source + the two registry contracts; no behavior suspicion required a temp test.

### Shape #5 gate confirmation

- (1) Zero this-cycle edit: HEAD diff empty + target absent from cycle-wide diff stat (per-item proof). The 28 dirty files attribute to other planned cycle items; this target is not among them.
- (2) All four Worker 2 sections open `Filled by Worker 1 per no-source-edit cycle pattern.`
- (3) Single Low forward-looking with verbatim trigger; no GLOSSARY-only fix in scope (GLOSSARY entries 720/1104/379/387/46 consistent with source, no replacement staged).
- (4) Changelog `Not warranted` cites BOTH AGENTS.md #21 AND active-plan (`review-0_0_10.md`) silence; `git diff HEAD -- CHANGELOG.md` empty (the cycle-wide stat's CHANGELOG +9 belongs to other items, not this cycle). Internal-only framing honest — empty behavior diff, no public-API surface changed.
- (5) `uv run ruff format --check django_strawberry_framework/types/relay.py` = "1 file already formatted"; `uv run ruff check` = "All checks passed!".

### Verification outcome

`cycle accepted; verified` — sets top-level `Status: verified` AND marks the `types/relay.py` checklist box in `docs/review/review-0_0_10.md`.

---

## Iteration log

(none)
