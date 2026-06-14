# Review: `django_strawberry_framework/types/relay.py`

Status: verified

> Supersedes a STALE 0.0.7 on-disk artifact (`Status: verified`, refs `spec-011`/`spec-015`, `_apply_get_queryset_sync`/`_initial_queryset`, 528-line pre-GlobalID-strategy shape). That artifact described a file that no longer exists: the 0.0.9 heavy change rewrote this module around the model-anchored GlobalID default and the four-strategy system. Replaced wholesale per the recurring stale-artifact pattern; the active plan checkbox for `types/relay.py` is unchecked.

## DRY analysis

- **Defer until a third in-async-context Relay resolver lands.** `_resolve_node_default` (`types/relay.py:787-820`) and `_resolve_nodes_default` (`:844-885`) share the identical dispatch prelude (`id_attr = cls.resolve_id_attr(); if in_async_context(): return _resolve_<X>_async(...); qs = apply_type_visibility_sync(cls, initial_queryset(cls), info); qs = _apply_node_filter(...)`), differing only in the terminal materialization (`qs.get()`/`qs.first()` vs the `_order_nodes` map). A shared `_dispatch_node_resolver(cls, *, info, sync_finalize, async_helper, ...)` would have to thread two terminal callbacks plus the singular/plural `_apply_node_filter` keyword choice through one signature, losing more readability than it saves. Defer until a third sync-vs-async-context resolver lands (most plausibly `resolve_connection` if a root connection refetch ships); collapse all three then. Same calibration as the intentional sync/async twins recorded across the package.
- **Defer the `_emits_model_label` / `_accepts_model_label_decode` frozenset-predicate pair collapse until encode/decode acceptance diverges.** `_emits_model_label` (`:417-424`) and `_accepts_model_label_decode` (`:427-437`) are byte-identical bodies (`return effective_strategy in MODEL_LABEL_STRATEGIES`), distinguished only by name so the encode-audit half and the decode-Step-2 half read against semantically-named predicates. The docstring at `:427-437` already states the deferral trigger verbatim: "Slice 3 splits this if a divergence ever surfaces." Do NOT merge now — the two names are the addressability-by-design pattern (audit reads `emits`, decode reads `accepts`); a single predicate would force every call site to re-encode which side of the encode/decode boundary it sits on. Quote the existing trigger.

## High:

None.

## Medium:

None.

## Low:

### L1: `_NODE_TYPE_HINT_ATTR` comment names `_stamp_node_type` as living in `relay.py` without the qualifier

The module-level comment at `types/relay.py:65-66` reads "the root ``node``/``nodes`` resolvers (``relay.py``'s ``_stamp_node_type``)". From inside `types/relay.py`, an unqualified ``relay.py`` reads as a self-reference, but `_stamp_node_type` actually lives in the ROOT module `django_strawberry_framework/relay.py:228` (`_stamp_node_type`), a different file. The same ambiguity recurs in `install_is_type_of`'s docstring at `:88-89` ("set by the root refetch fields on the instances they fetch") — that one disambiguates with "root", so it is clear. Per AGENTS.md the symbol-qualified form would be `django_strawberry_framework/relay.py::_stamp_node_type`; in a docstring the shorter "the root ``relay.py``'s ``_stamp_node_type``" suffices. Stale-but-harmless naming clarity; the cross-file wire is correct and tested. Recommended: at `:65-66` change "``relay.py``'s ``_stamp_node_type``" to "the root ``relay.py``'s ``_stamp_node_type``" to match the disambiguation `install_is_type_of` already uses.

### L2: `_resolve_id_default` `# noqa: ARG001` covers a now-used `info`? — confirm vacuous-arg suppression still warranted

`_resolve_id_default` (`:272`) carries `# noqa: ARG001` on the signature, suppressing the unused-argument lint for the keyword-only `info`. `info` is genuinely unused in the body (the dict-cache / getattr path never touches it) — the parameter exists only to match Strawberry's `cls.resolve_id(root, info=info)` call shape. The suppression is correct. Recorded as a confirm-only Low: the noqa is load-bearing for signature-parity, not dead. No change; documented so a future reviewer does not "clean up" the unused `info` and break the keyword-binding contract the docstring at `:277-280` describes.

### L3: `decode_global_id` model-label branch's `get_definition` can return `None` only theoretically; the guard is defensive-correct

In the model-label branch (`:718-724`), `target_type = registry.get(model)` is None-checked and raises; then `definition = registry.get_definition(target_type)` (`:724`). `get_definition` returns `Optional` (`registry.py:346-348`), but `target_type` just came from `registry.get(model)` which only returns a registered type, so a registered type missing its definition is an unreachable internal-invariant break. The uniform `strategy = definition.effective_globalid_strategy if definition is not None else None` guard at `:729` absorbs the theoretical None into the same fail-loud `ConfigurationError`. Defensive-correct, not a defect. Recorded so the `if definition is not None` arm is not mistaken for dead code worth deleting — it is the shared guard for BOTH branches (the type-name branch's `definition_for_graphql_name` raises rather than returns None, so its `target_type = definition.origin` at `:727` is safe; the None-guard exists for branch symmetry). No change.

## What looks solid

### DRY recap

- **Existing patterns reused.** `_model_for` (`:335-344`) is the single source of truth for `cls.__django_strawberry_definition__.model`, consumed at `install_is_type_of` (`:110`), `_check_composite_pk_for_relay_node` (`:172`), and `_order_nodes` (`:773`); its contract is explicitly aligned with `utils/querysets.py::initial_queryset`. `MODEL_LABEL_STRATEGIES` / `TYPE_NAME_STRATEGIES` (`:413-414`) are the single home for the `{"model","type+model"}` / `{"type","type+model"}` memberships — the encoder (`:490`), the three `_*_model_label` / `_*_type_name` predicates, the finalizer audit, and the decoder all reference them rather than re-typing the sets. The string constants `STRING_GLOBALID_STRATEGIES` / `DEFAULT_GLOBALID_STRATEGY` correctly live ONCE in `types/base.py:119-120` and are imported in-function (`:384-387`). `_apply_node_filter` (`:314-332`) is color-agnostic — both sync and async resolvers consume it. `_RELAY_RESOLVER_DEFAULTS` (`:917-922`) is the single source of truth for the four `resolve_*` names + defaults, iterated once by `install_relay_node_resolvers`. `_validate_globalid_strategy` is reused (not re-implemented) for the setting path (`:394-399`) — one validator, two sources.
- **New helpers considered.** A unified `_dispatch_node_resolver` folding the node/nodes resolvers, and a merge of the `_emits_model_label`/`_accepts_model_label_decode` predicate pair, were both considered and deferred-with-trigger (see DRY analysis). The `callable`/`custom` strategies are deliberately absent from BOTH frozensets — their non-membership IS the "encode-only, no decode" contract, so there is intentionally no `{"callable","custom"}` literal to extract.
- **Duplication risk in the current file.** The three near-identical one-line `in MODEL_LABEL_STRATEGIES` / `in TYPE_NAME_STRATEGIES` predicates (`_emits_model_label`, `_accepts_model_label_decode`, `_accepts_type_name_decode`) are intentional sibling design (addressability-by-design for the encode-audit vs decode-Step-2 readers); the two `__func__`-identity override discriminators (`_consumer_overrode_resolve_typename` at `:523-547` and the loop in `install_relay_node_resolvers` at `:951-957`) are structurally parallel but answer different questions (typename's framework-closure-marker exemption vs the four resolver defaults' plain identity test). Not collapse candidates.

### Other positives

- **GlobalID strategy precedence is correct and frozen-once.** `_resolve_globalid_strategy` (`:352-400`) implements `Meta.globalid_strategy` (`:389-391`, already validated at type creation) → `RELAY_GLOBALID_STRATEGY` setting (`:392-399`, re-validated through the SAME `_validate_globalid_strategy` with `source="setting"`, so an unknown string / wrong-arity / `async def` callable in the setting raises naming the setting) → `DEFAULT_GLOBALID_STRATEGY` (`"model"`, `:400`). Never returns `None`. Setting read is defensive (`getattr(..., None)`) so an absent setting falls through cleanly. The setting branch passes `relay_shaped=True` because the per-type Relay-shape gate already ran at type creation — verified against `base.py:339-342` (the gate is `is_meta`-only and skipped for `source="setting"`).
- **`encode_typename` covers all four strategies with a fail-loud callable contract.** `model`/`type+model` → `definition.model._meta.label_lower` (`:491`, Django's canonical `app_label.modelname`); `type` → `definition.graphql_type_name` (`:493`); callable → invoked `(type_cls, model, root, info)` with a non-empty-`str` return check (`:481-489`) that converts a bad return into a named `ConfigurationError` rather than letting Strawberry's downstream `assert isinstance(type_name, str)` fire opaquely. The comment correctly notes `type` is "the only remaining string strategy" after the MODEL_LABEL membership check. The string-strategy branches never touch `root`/`info`, which is exactly what makes the `testing/relay.py::global_id_for` mint helper byte-identical to live emission.
- **`decode_global_id` is hardened for client-controlled input with a uniform error contract.** Input gate (`:683-687`) rejects non-`(GlobalID, str)` before any parse; `from_id` `ValueError` superset caught (`:692`, covers `GlobalIDValueError`); empty-slot rejection (`:702-706`, since `from_id` does not enforce non-empty). Step 1 routes on the dot: model-label → `apps.get_model` (LookupError → ConfigurationError, `:713`) → `registry.get(model)` (primary/lone, None → ConfigurationError), type-name → `definition_for_graphql_name` (raises on miss/ambiguity). Step 2 enforces the recorded `effective_globalid_strategy` permits the payload shape via `_accepts_model_label_decode` / `_accepts_type_name_decode`; an absent (`None`) strategy (non-Relay-Node or mid-state type) is rejected (`:730-734`), so a crafted ID cannot resolve to a non-Node type. Every failure surfaces ONE `ConfigurationError` — no `KeyError`/`AttributeError`/`GlobalIDValueError` leak. The model-label-routes-to-primary asymmetry is documented honestly (`:660-662`) and matches `testing/relay.py`'s round-trip-asymmetry contract and `finalizer.py::_warn_model_label_secondary_collapse` — security-adjacent no-existence-leak property holds (decode is payload-shape-only, runs before any query).
- **The override-detection three-discriminator design is sound and documented.** `_consumer_overrode_resolve_typename` (`:523-547`) layers the `_FRAMEWORK_CLOSURE_MARKER` exemption (`:544-545`) ON TOP OF the `__func__`-identity test so a framework closure inherited from a CONCRETE Relay parent through the MRO is not misclassified `custom` — the marker lives on the plain function so it survives `classmethod.__func__` retrieval (`:630`). The step-0 re-entrancy guard in `install_globalid_typename_resolver` (`:586-587`) is load-bearing: a Phase-2.5 raise (including the model-label-routing audit in finalizer.py) leaves every type `finalized=False`, so a re-run must not re-run the `__func__` test against the now-installed framework closure. The both-declared conflict (override + explicit `Meta.globalid_strategy`, `:590-596`) correctly excludes the schema-wide setting from the conflict. The `type`-must-install-its-own-closure-when-inheriting-a-parent-framework-closure branch (`:603`) is the subtle correctness fix for emitting the parent's payload.
- **Composite-pk gate and id-attr stamping defend against inherited-cache bypass.** `_check_composite_pk_for_relay_node` (`:154-191`) asks `relay.Node.resolve_id_attr.__func__(type_cls)` DIRECTLY (`:181`) rather than `type_cls.resolve_id_attr()` — the rationale (`:175-179`) is correct: a relay-shaped child of a relay-shaped parent inherits the parent's installed framework default which swallows `NodeIDAnnotationError` into the `"pk"` fallback and would let a composite-pk child slip the gate. `_stamp_relay_id_attr` (`:204-233`) seeds `_id_attr = None` into the class's OWN `__dict__` to blind upstream's inherited-cache read before the scan, and stamps `_RELAY_ID_ATTR_SLOT` (deliberately NOT Strawberry's `_id_attr`, `:194-200`) so a subclass never inherits its parent's stamp. `_resolve_id_attr_default` reads the own-`__dict__` stamp first (`:263`) with a live-scan fallback via `__func__` (`:267`, avoids the `super()` infinite-recursion documented at `:252-261`).
- **`_resolve_id_default` proxy-model keying and `__dict__` cache are correct.** Keys the `__dict__` lookup on `root.__class__._meta.pk.attname` (`:297`) not the declared-model pk — correct for proxy-model rows whose actual class differs (`:290-293`). Reads `root.__dict__[id_attr]` first to avoid an ORM hit when the optimizer already loaded the row, falling back to `getattr` on KeyError (`:298-301`).
- **Async/sync resolver twins honor the `get_queryset` contract.** `_resolve_node_async` / `_resolve_nodes_async` (`:823-841`, `:888-911`) await `apply_type_visibility_async` (honoring async `get_queryset` hooks) before the id filter and the terminal `aget`/`afirst` / `async for`. The sync paths use `apply_type_visibility_sync`; a coroutine from a sync-context `get_queryset` surfaces as `SyncMisuseError` (the `ConfigurationError`+`RuntimeError` subclass) per the docstrings (`:810-813`, `:871-874`), routed through `utils/querysets.py`. `_order_nodes` (`:750-784`) preserves input order and raises the model's `DoesNotExist` under `required=True` (homogeneous with `_resolve_node_default`'s `qs.get()`), `None` otherwise. `node_ids=None` returns the queryset directly for the bulk-fetch path.
- **In-function imports correctly dodge the load cycle.** `_resolve_globalid_strategy` (`:383-387`, `conf`+`base`), `decode_global_id` (`:681`, `registry`) all import in-function with documented cycle-dodge rationale (`base.py` imports `install_is_type_of` from this module at module top). The `SyncMisuseError as SyncMisuseError` re-export alias (`:41`) keeps the moved-to-`utils/querysets.py` symbol importable from here, documented at `:37-40`.
- **Consumption is complete — no built-but-unconsumed surface.** Verified every public helper has a live consumer: `install_is_type_of` (base.py:647), `apply_interfaces`/`_check_composite_pk_for_relay_node`/`install_relay_node_resolvers`/`install_globalid_typename_resolver`/`_emits_model_label`/`_accepts_model_label_decode` (finalizer.py Phase 2.5 + audits), `implements_relay_node` (registry/filters/finalizer), `encode_typename` (testing/relay.py + the installed closure), `decode_global_id` (testing/relay.py re-export + root relay.py refetch fields), `_NODE_TYPE_HINT_ATTR`/`_model_for` (root relay.py). `_accepts_type_name_decode` is read by decode_global_id and `filters/base.py` per its docstring.

### Summary

`types/relay.py` is the 0.0.9-rewritten internal Relay foundation: interface `__bases__` injection, the composite-pk gate, the four `resolve_*` node-resolver defaults (sync/async twins), `is_type_of`, and the net-new model-anchored GlobalID strategy system (`encode_typename`, the `Meta`→`RELAY_GLOBALID_STRATEGY`→`"model"` precedence in `_resolve_globalid_strategy`, the strategy-classification `effective_globalid_strategy` stamping in `install_globalid_typename_resolver`, and the hardened `decode_global_id`). Logic is correct across all four strategies: the model-label encode is Django's `_meta.label_lower`, precedence and frozen-once finalization match base.py/definition.py, the framework-closure marker correctly exempts inherited closures from override misclassification, and `decode_global_id` is genuinely security-hardened (uniform `ConfigurationError`, payload-shape-only, strategy-gated, no existence oracle). The secondary-type-collapse is correctly OWNED by finalizer.py (`_audit_model_label_routing` hard-error + `_warn_model_label_secondary_collapse` warn); this file only supplies the membership predicates and the honest decode-routes-to-primary documentation. No High, no Medium. Three Lows, all confirm-only / naming-clarity (a self-referential `relay.py` comment, a load-bearing `noqa: ARG001`, a defensive-but-correct None guard in decode). GLOSSARY entries for the strategy system (`Meta.globalid_strategy`, `RELAY_GLOBALID_STRATEGY`, `Relay Node integration`) verified accurate against current source — no drift.

---

## Fix report (Worker 2)

Consolidated single-spawn (comment-only cycle: L1 act-now comment fix; L2/L3 confirm-only, no edit).

### Files touched

- `django_strawberry_framework/types/relay.py:65` — L1 comment-clarity fix. Disambiguated the `_NODE_TYPE_HINT_ATTR` module comment so the unqualified ``relay.py`` no longer reads as a self-reference from inside `types/relay.py`. Changed "Attribute the root ``node``/``nodes`` resolvers (``relay.py``'s ``_stamp_node_type``)" → "...(the root ``relay.py``'s ``_stamp_node_type``)". Matches the disambiguation `install_is_type_of`'s docstring (`:88-89`) already uses ("set by the root refetch fields"). Verified `_stamp_node_type` lives in the ROOT module `django_strawberry_framework/relay.py::_stamp_node_type` (def at line 228, consumed at 257/305/395/403), NOT in `types/relay.py` — confirmed by `grep -rn "_stamp_node_type"` (only this comment in `types/relay.py`, the def + 5 call sites in root `relay.py`).

### Tests added or updated

None — comment-only change, no behavior touched.

### Validation run

- `uv run ruff format .` — pass / no-changes (265 files unchanged).
- `uv run ruff check --fix .` — pass (all checks passed).
- No pytest (per AGENTS.md / role rules).

### Notes for Worker 3

- Shadow file used: `docs/shadow/django_strawberry_framework__types__relay.overview.md` (read-only overview; comment inventory line 65-73 matches source). Shadow line numbers are non-canonical; source-file line numbers cited above.
- **L2 (confirm-only):** `_resolve_id_default`'s `# noqa: ARG001` (`:272`) confirmed load-bearing — `info` is genuinely unused in the body (dict-cache/getattr path) but the keyword-only param exists to match Strawberry's `cls.resolve_id(root, info=info)` call shape. No change.
- **L3 (confirm-only):** the `if definition is not None` guard at `:729` (decode model-label branch) confirmed defensive-correct, shared by both decode branches for symmetry. Not dead code. No change.
- `git diff --stat` vs baseline `0872a20` shows `types/relay.py | 2 +-` (1 insertion, 1 deletion) — the single comment line. The remainder of the working-tree diff is concurrent other-worker activity (AGENTS.md #33), untouched by this cycle.
- `uv.lock` clean (no touch).

---

## Verification (Worker 3)

### Logic verification outcome

NO logic changed. Cycle diff vs baseline `0872a20` = `types/relay.py | 2 +-` (1 insertion, 1 deletion) — a single `#` comment line inside the `_NODE_TYPE_HINT_ATTR` block (`:65`): "(``relay.py``'s ``_stamp_node_type``)" → "(the root ``relay.py``'s ``_stamp_node_type``)". Adjacent executable lines (`implements_relay_node` return at `:62`, `_NODE_TYPE_HINT_ATTR = "_dsf_node_type_hint"` at `:74`) byte-unchanged.

- **Low 1 (fixed):** comment-clarity disambiguation confirmed accurate. `grep -rn "_stamp_node_type"` shows the def at ROOT `django_strawberry_framework/relay.py:228` plus 5 call sites (257/305/395/403); the only occurrence in `types/relay.py` is this comment. The reworded "the root ``relay.py``'s ``_stamp_node_type``" correctly disambiguates the cross-file reference and matches the "root refetch fields" wording `install_is_type_of`'s docstring already uses (`:88`).
- **Low 2 (confirm-only, unchanged):** `_resolve_id_default`'s `# noqa: ARG001` for the unused keyword-only `info` — not in the diff, confirmed load-bearing for Strawberry `cls.resolve_id(root, info=info)` signature-parity.
- **Low 3 (confirm-only, unchanged):** the `if definition is not None` defensive guard in the decode model-label branch — not in the diff, confirmed defensive-correct (shared by both decode branches for symmetry).
- **Security-adjacent decode (untouched):** the GlobalID `decode_global_id` contract (uniform `ConfigurationError`, payload-shape-only, strategy-gated, no existence oracle) Worker 1 verified is unaffected by a comment edit; executable bodies byte-unchanged.

### DRY findings disposition

Both DRY items (`_dispatch_node_resolver` fold; `_emits_model_label`/`_accepts_model_label_decode` predicate collapse) confirmed deferred-with-trigger; existing docstring at `:427-437` already states the split trigger verbatim. No change.

### Temp test verification

None — comment-only cycle, no behavior to probe. Verification was read-only (diff inspection + cross-file grep for `_stamp_node_type`).

### Verification outcome

`cycle accepted; verified` — sets top-level `Status: verified` AND marks the checklist box. Diff is comment-only (+1/-1, single `#` line); executable lines byte-unchanged; ruff format-check + check pass (COM812 standing notice); `git diff -- CHANGELOG.md` empty, Not-warranted with both citations (AGENTS.md + active-plan silence), internal-only framing honest (comment-clarity, zero consumer-visible change).

---

## Comment/docstring pass

Folded into the consolidated single-spawn (the sole in-cycle edit is the L1 comment-clarity fix; see Fix report above).

### Files touched

- `django_strawberry_framework/types/relay.py:65` — L1, as recorded in the Fix report.

### Per-finding dispositions

- DRY (defer `_dispatch_node_resolver`): confirmed deferred-with-trigger (third in-async-context resolver). No change.
- DRY (defer `_emits_model_label` / `_accepts_model_label_decode` collapse): confirmed deferred-with-trigger; the existing docstring at `:427-437` already states "Slice 3 splits this if a divergence ever surfaces". No change.
- Low 1: fixed — comment disambiguated to "the root ``relay.py``'s ``_stamp_node_type``".
- Low 2: confirm-only — `# noqa: ARG001` load-bearing for signature-parity. No change.
- Low 3: confirm-only — `if definition is not None` guard defensive-correct, shared by both decode branches. No change.

### Validation run

- `uv run ruff format .` — pass / no-changes.
- `uv run ruff check --fix .` — pass.

### Notes for Worker 3

Comment-only cycle; no logic touched, no docstring contract changed.

---

## Changelog disposition

### State

`Not warranted`.

### Reason

The sole edit is an internal comment-clarity fix (disambiguating a cross-file reference) with zero consumer-visible behavior change. No `CHANGELOG.md` authorization for this cycle: AGENTS.md "Do not update CHANGELOG.md unless explicitly instructed", AND the active review plan is silent on changelog authorization for `types/relay.py` (per-file cycles are never the authorising scope; any drift forwards to the project pass).

### What was done

No `CHANGELOG.md` edit.

### Validation run

- `uv run ruff format .` — pass / no-changes.
- `uv run ruff check --fix .` — pass.

---

## Iteration log
