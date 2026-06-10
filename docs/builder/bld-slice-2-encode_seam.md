# Build: Slice 2 — the encode seam (strategy-parameterized `resolve_typename` + four encoders + default flip + strategy-aware filter)

Spec reference: `docs/spec-031-globalid_encoding-0_0_9.md` (lines 89-95)
Status: final-accepted

## Plan (Worker 1)

This slice ships the **encode** half of the GlobalID-encoding feature, on top of
Slice 1's foundation. Slice 1 already shipped (verified against
`bld-slice-1-globalid_strategy_key.md` final-verification): the raw
`DjangoTypeDefinition.globalid_strategy` slot (class-creation-set), the precedence
resolver `types/relay.py::_resolve_globalid_strategy(definition)`, and the
single-source constants in `types/base.py` — `STRING_GLOBALID_STRATEGIES`
(`frozenset({"model", "type", "type+model"})`), `DEFAULT_GLOBALID_STRATEGY = "model"`,
and `_GLOBALID_CALLABLE_PARAMS`. This slice REUSES those; it does not re-create them.

What Slice 2 adds (spec lines 89-95, Decisions 3/4/9/10/13):

1. An `encode_typename(definition, strategy)`-style internal helper in
   `types/relay.py` returning the type-name slot per resolved strategy.
2. `install_globalid_typename_resolver(type_cls, definition)` — re-entrant-safe,
   called from `finalize_django_types` Phase 2.5 alongside
   `install_relay_node_resolvers`; records `definition.effective_globalid_strategy`.
3. The new `DjangoTypeDefinition.effective_globalid_strategy: str | None = None`
   field (`definition.py`).
4. A Phase-2.5 model-label-routing audit in `finalizer.py` (parallel to
   `_audit_primary_ambiguity`).
5. The package-default flip to `model`.
6. Strategy-aware `GlobalID` filter validation in `filters/base.py` (Decision 13),
   co-landing with the flip.

**The single load-bearing contract Slice 3 (decode) depends on**: the recorded
field `DjangoTypeDefinition.effective_globalid_strategy` (one of
`"model" / "type" / "type+model" / "callable" / "custom"`, or `None` for a
non-framework-decodable type), AND the shared strategy→payload-shape mapping
(see DRY analysis) that Slice 3's decode Step-2 enforcement and this slice's
filter validation both consume.

### Pinned single source of truth for "strategy → payload shape"

`STRING_GLOBALID_STRATEGIES` / `DEFAULT_GLOBALID_STRATEGY` live in `types/base.py`
(Slice 1). The **strategy→payload-shape** mapping is net-new to this slice. It is
pinned to **`types/relay.py`** (the encode home, next to `encode_typename` and the
install step), exposed as two small named predicates + a constant:

- `MODEL_LABEL_STRATEGIES = frozenset({"model", "type+model"})` — strategies whose
  encoder emits the `app_label.modelname` model-label slot. Used by: the encoder
  (which slot to emit), the model-label-routing audit (`emits_model_label`), the
  decode Step-2 enforcement (Slice 3), the filter (which shape to accept).
- `_emits_model_label(effective_strategy) -> bool` — `effective_strategy in MODEL_LABEL_STRATEGIES`.
- `_accepts_model_label_decode(effective_strategy) -> bool` — same membership
  (`model` / `type+model` both decode model labels); the audit's
  `accepts_model_label(primary)` predicate and Slice 3's decode use this. (Encode
  and decode acceptance of the model-label shape coincide for the framework
  strategies, so one `frozenset` serves both; if Slice 3 reveals a divergence it
  splits then — flagged, not pre-split.)

`filters/base.py` imports these from `types/relay.py` (filters → types is the safe
direction — see DRY analysis import-cycle note). Worker 2 has discretion on the
exact constant/predicate names (see Implementation discretion items); the
requirement is ONE named source of truth, not three parallel literal sets across
the encoder, the audit, the filter, and (Slice 3) the decoder.

### DRY analysis

**Existing patterns reused (cite file:line — pin-at-write-time hints).**

- `types/relay.py::install_relay_node_resolvers` (relay.py:577-603) is the
  structural precedent for `install_globalid_typename_resolver`: the
  `existing.__func__ is relay.Node.<attr>.__func__` MRO-aware identity test
  (relay.py:598-603) is reused verbatim for `resolve_typename` against
  `relay.Node.resolve_typename.__func__`. `resolve_typename` is a `@classmethod`
  on `relay.Node` (strawberry `relay/types.py:493`), so it has `__func__` exactly
  like the four `resolve_*` defaults. The install path also reuses the
  `setattr(type_cls, attr, classmethod(default))` shape (relay.py:603).
- `types/relay.py::_resolve_globalid_strategy(definition)` (relay.py:323-371,
  Slice 1) is REUSED unchanged to resolve the raw strategy in the no-override
  branch — `install_globalid_typename_resolver` calls it, does not re-implement
  the precedence.
- `types/relay.py::_RELAY_RESOLVER_DEFAULTS` (relay.py:566-574): the slice
  deliberately does NOT add `resolve_typename` to this table (spec Decision 10 —
  the table maps a name→one static default; the typename default is
  strategy-parameterized per type). The "single source of truth for resolver
  names" comment (relay.py:566-568) stays accurate.
- `types/finalizer.py::_audit_primary_ambiguity` (finalizer.py:117-142) is the
  structural precedent for the model-label-routing audit: iterate
  `registry.models_with_multiple_types()` (finalizer.py:136), collect offenders,
  sort deterministically by `model.__name__` (finalizer.py:141), raise one
  `ConfigurationError` built by a `_format_*_error` helper (finalizer.py:142). The
  audit's home is the Phase-2.5 TODO at finalizer.py:145-155.
- `types/finalizer.py` Phase 2.5 Relay loop (finalizer.py:256-274): the install
  call slots in after `install_relay_node_resolvers` at the TODO
  (finalizer.py:269-274), inside the existing
  `if implements_relay_node(type_cls):` block (finalizer.py:266-268).
- `types/definition.py` defaulted-field block (definition.py:104-123): the new
  `effective_globalid_strategy` field is added at the pinned TODO
  (definition.py:118-122), immediately after the raw `globalid_strategy` slot
  (definition.py:117), mirroring how `connection` / `globalid_strategy` were added.
  Its docstring stub already exists (definition.py:78-83).
- `filters/base.py::_decode_and_validate_global_id` (filters-base.py:207-229) and
  `_expected_global_id_type_name` (filters-base.py:169-204): the existing
  owner/target resolution (own-PK branch → owner definition; relation branch →
  `owner.related_target_for(head)` target definition; finalizer-base.py:191-204)
  is reused — the refactor swaps the final `.graphql_type_name` read for a
  strategy-aware acceptance check keyed on the resolved definition's
  `effective_globalid_strategy`. The existing `expected is None` node-id-only
  fallback (filters-base.py:224) is the precedent for the `callable`/`custom`
  fallback.
- `definition.graphql_type_name` property (definition.py:136-147) is the single
  source for the `type`/`type+model` type-name slot, reused by the encoder and the
  filter's `type`-shape check.
- `definition.model._meta.label_lower` is the Django-canonical model label
  (`"products.item"`) — the `model`/`type+model` slot and the filter's
  `model`-shape check.

**New helpers/constants justified (single responsibility each).**

- `types/relay.py::encode_typename(definition, strategy, root, info)` — single
  responsibility: compute the type-name slot string for ONE resolved strategy.
  `model`/`type+model` → `definition.model._meta.label_lower`; `type` →
  `definition.graphql_type_name`; `callable` → the consumer callable's return
  (validated non-empty `str`). It serves the installed `resolve_typename` closure.
  (Note: for `type`, the framework installs NOTHING — Strawberry's default returns
  `info.path.typename`, byte-identical to `graphql_type_name` for the live
  schema — so `encode_typename` is only invoked from the framework closure for
  `model`/`type+model`/`callable`. Whether `encode_typename` is one dispatch
  function or the closures inline the per-strategy slot read is a Worker 2
  discretion item, provided the model-label / graphql-name reads are not
  duplicated across the install branches.)
- `types/relay.py::install_globalid_typename_resolver(type_cls, definition)` —
  single responsibility: classify the type's effective strategy, install the
  framework `resolve_typename` closure (or nothing), and record
  `definition.effective_globalid_strategy`. Re-entrant-safe.
- `types/relay.py::MODEL_LABEL_STRATEGIES` + `_emits_model_label` /
  `_accepts_model_label_decode` predicates — the ONE source of truth for the
  strategy→payload-shape mapping (see "Pinned single source of truth" above),
  reused by the encoder, the audit, the filter, and (Slice 3) the decoder.
- `types/finalizer.py::_audit_model_label_routing()` + a
  `_format_model_label_routing_error(...)` message builder — single
  responsibility: enforce the model-label-routing invariant for multi-type models.
  Modeled on `_audit_primary_ambiguity` + `_format_ambiguity_error`.

**Duplication risk avoided.**

- The strategy→payload-shape membership could be naively re-typed as three+
  parallel literal sets (`{"model", "type+model"}` in the encoder, the audit, the
  filter, and Slice 3's decoder). The plan forbids that: `MODEL_LABEL_STRATEGIES`
  in `types/relay.py` is the one frozenset all four sites reference.
- The model-label string (`definition.model._meta.label_lower`) and the
  graphql-name string (`definition.graphql_type_name`) recur in the encoder AND
  the filter's per-strategy acceptance check. The plan keeps each read sited on
  the definition (the encoder computes the emit slot; the filter computes the
  expected-accept slot[s]) — both read the SAME two definition accessors, not
  re-derived label logic. No hand-rolled `f"{app}.{model}"` formatting anywhere
  (use `_meta.label_lower`).
- The `__func__` identity test is NOT copied: `install_globalid_typename_resolver`
  uses the same idiom as `install_relay_node_resolvers` (relay.py:598-603). Worker 2
  should consider whether a tiny shared `_consumer_overrode(type_cls, attr)`
  helper is worth extracting vs. inlining the four-line idiom once more; Worker 1's
  assessment: a one-call-site inline is acceptable (the existing loop in
  `install_relay_node_resolvers` is structurally different — it iterates a table),
  but if Worker 2 sees a clean two-line predicate it may extract it. Discretion item.
- The `ConfigurationError` message-builder pattern (`_format_*_error` returning a
  string, raised by the caller) is reused for the routing audit — not a bespoke
  inline `raise ConfigurationError(f"...")` that would diverge in style from the
  finalizer's other audit messages.

### Implementation steps

Line numbers are pin-at-write-time navigational hints. Verify against current
source before editing — Slice 1 already shifted these files.

1. **`django_strawberry_framework/types/definition.py` — add the recorded field.**
   At the pinned TODO (definition.py:118-122), add
   `effective_globalid_strategy: str | None = None` immediately after the raw
   `globalid_strategy` slot (definition.py:117) and before `finalized: bool = False`
   (definition.py:123). Remove the now-satisfied TODO comment (definition.py:118-122)
   and the matching docstring TODO portion (definition.py:78-83), rewriting the
   docstring to describe the now-present `effective_globalid_strategy` field (set
   once at Phase-2.5 install, doubles as the re-entrancy sentinel; `None` ⇒ "not a
   framework-decodable Relay-Node type"). This field is `str | None` (NOT
   `Callable`): a callable raw strategy resolves to the recorded classification
   string `"callable"`, distinct from the raw callable object on `globalid_strategy`
   (spec Decision 10 / feedback P2).

2. **`django_strawberry_framework/types/relay.py` — add the strategy→payload-shape
   single source of truth.** Near the GlobalID-strategy TODO (relay.py:374-389) or
   beside `_resolve_globalid_strategy` (relay.py:323), add
   `MODEL_LABEL_STRATEGIES = frozenset({"model", "type+model"})` and the predicates
   `_emits_model_label(strategy) -> bool` / `_accepts_model_label_decode(strategy) -> bool`
   (both `strategy in MODEL_LABEL_STRATEGIES`). Name at Worker 2 discretion; the
   requirement is single-sourcing. `filters/base.py` and (Slice 3) the decoder
   import these.

3. **`django_strawberry_framework/types/relay.py` — add `encode_typename`.** Replace
   the encode-half of the Slices-2-3 TODO (relay.py:374-389, encode portion) with
   the helper computing the type-name slot for a resolved strategy
   (spec line 90, Decision 4):
   - strategy in `MODEL_LABEL_STRATEGIES` (`model`/`type+model`) →
     `definition.model._meta.label_lower`.
   - `type` → `definition.graphql_type_name` (the framework installs nothing for
     `type` — see step 4 — so this branch is for completeness / a single dispatch
     surface; Worker 2 discretion whether to include it).
   - callable → call `strategy(type_cls, model, root, info)` and validate the
     return is a non-empty `str`; on a non-`str` or empty return raise
     `ConfigurationError` (naming the type and the
     `(type_cls, model, root, info) -> str` contract), NOT letting Strawberry's
     `Node._id` `assert isinstance(type_name, str)` fire as an opaque
     `AssertionError` (spec Decision 4/10, feedback P2). The callable's
     arity/sync-ness was already validated at type creation (Slice 1) — this is
     ONLY the per-call return-value check.
   The installed closure must accept `(root, info)` (the `resolve_typename`
   classmethod seam, strawberry `relay/types.py:493`) and is installed via
   `setattr(type_cls, "resolve_typename", classmethod(closure))`. The closure
   captures `definition` and the resolved strategy (resolved once at install, not
   per request — spec Decision 5).

4. **`django_strawberry_framework/types/relay.py` — add
   `install_globalid_typename_resolver(type_cls, definition)`.** In the same
   region (replacing the install-half of the TODO at relay.py:374-389), implement
   the ordered steps of spec Decision 10:
   - **Step 0 — re-entrancy guard.** `if definition.effective_globalid_strategy is not None: return`
     (skip override-detection, recording, and install — the type was processed in a
     prior partial finalize; feedback P1). This is the FIRST statement.
   - **Step 1 — override detection.** Compute the override via the MRO-aware
     `__func__` test against `relay.Node.resolve_typename.__func__` (mirror
     relay.py:598-603). If the consumer overrode `resolve_typename`:
     - and the type ALSO declares an explicit `Meta.globalid_strategy` (i.e.
       `definition.globalid_strategy is not None`) → raise `ConfigurationError`
       (both-declared conflict: "declare a `resolve_typename` override OR
       `Meta.globalid_strategy`, not both"). The schema-wide
       `RELAY_GLOBALID_STRATEGY` setting is NOT a conflict (only the per-type
       `Meta` key collides — spec Decision 10 / feedback P1). So the conflict check
       keys on `definition.globalid_strategy is not None`, NOT on the resolved
       strategy.
     - otherwise → effective strategy is `"custom"`; install NOTHING (the override
       owns the slot). Fall through to step 3 to record `"custom"`.
   - **Step 2 — no override.** Resolve the raw strategy via
     `_resolve_globalid_strategy(definition)` (relay.py:323, Slice 1). Then:
     - `type` → install NOTHING (Strawberry's default `resolve_typename` returns
       `info.path.typename`, byte-identical to pre-`0.0.9`); effective strategy
       recorded is `"type"`.
     - `model` / `type+model` → install the framework closure emitting the
       model-label slot (via `encode_typename`); effective strategy `"model"` /
       `"type+model"`.
     - callable (raw strategy is callable) → install the framework closure that
       calls the consumer callable + validates the non-empty-`str` return; effective
       strategy recorded is the string `"callable"`.
   - **Step 3 — record.** Set `definition.effective_globalid_strategy` to the
     classification string (`"model"` / `"type"` / `"type+model"` / `"callable"` /
     `"custom"`). This is the single value decode (Slice 3) and the filter
     (Decision 13) read; it doubles as the step-0 sentinel.
   Note: the recorded classification keys on whether the raw strategy is a string
   (use it directly) or callable (record `"callable"`) — Worker 2 picks the
   cleanest spelling; the contract is the five exact strings.

5. **`django_strawberry_framework/types/finalizer.py` — call the install in Phase
   2.5.** At the TODO (finalizer.py:269-274), inside
   `if implements_relay_node(type_cls):` (finalizer.py:266), after
   `install_relay_node_resolvers(type_cls)` (finalizer.py:268), add
   `install_globalid_typename_resolver(type_cls, definition)`. Add it to the
   existing `from .relay import (...)` import (finalizer.py:59). The `definition`
   is already in scope (the loop binds `for type_cls, definition in registry.iter_definitions()`,
   finalizer.py:256). Remove the satisfied TODO (finalizer.py:269-274).

6. **`django_strawberry_framework/types/finalizer.py` — add the model-label-routing
   audit.** Replace the TODO (finalizer.py:145-155) with `_audit_model_label_routing()`
   modeled on `_audit_primary_ambiguity` (finalizer.py:117-142) plus a
   `_format_model_label_routing_error(...)` builder (modeled on
   `_format_ambiguity_error`, finalizer.py:95-114). Logic (spec Decision 8/10,
   feedback P1/P3):
   - For each `model in registry.models_with_multiple_types()` (multi-type only —
     single-type models trivially satisfy the invariant and have no
     `primary_for`):
     - read each registered type's recorded `effective_globalid_strategy` via
       `registry.get_definition(t).effective_globalid_strategy` for
       `t in registry.types_for(model)`.
     - if ANY emits model-label IDs (`_emits_model_label(...)`), read the model's
       primary `primary = registry.primary_for(model)` (guaranteed non-`None` for a
       multi-type model — Phase-1 `_audit_primary_ambiguity` ran first,
       finalizer.py:198) and its definition's `effective_globalid_strategy`; if the
       primary does NOT accept model-label decode (`_accepts_model_label_decode`),
       collect an offender.
   - if offenders, sort deterministically (by `model.__name__`, like
     finalizer.py:141) and raise ONE `ConfigurationError` naming the model, the
     model-label-emitting type, and the primary's strategy (spec error-shapes
     line 263).
   - **Placement (LOAD-BEARING, spec Decision 10 / feedback P1).** This audit MUST
     run AFTER the Relay loop (finalizer.py:256-274) has recorded EVERY type's
     `effective_globalid_strategy` (so it reads complete data), and it MUST run
     BEFORE Phase 3's `strawberry.type(...)` + `definition.finalized = True`
     (finalizer.py:279-283) AND before `registry.mark_finalized()`
     (finalizer.py:285). Recommended site: immediately after the Relay loop ends
     (after finalizer.py:274), before `_bind_filtersets()` (finalizer.py:276). This
     keeps the audit a Phase-2.5-raise (the per-entry `finalized` flag is still
     `False`, so a re-run re-enters the Relay loop from the top — where the step-0
     re-entrancy guard in `install_globalid_typename_resolver` prevents
     `model`→`custom` misclassification). Worker 2 verifies no later phase
     (`_bind_filtersets`/`_bind_ordersets`) depends on the audit having NOT run; it
     does not (they bind filter/order owners, orthogonal to GlobalID strategy).

7. **`django_strawberry_framework/types/relay.py` — flip the package default.** No
   new code: the default is already `DEFAULT_GLOBALID_STRATEGY = "model"`
   (`types/base.py`, Slice 1) and `_resolve_globalid_strategy` returns it when no
   `Meta` key and no setting are present (relay.py:371). The "flip" is realized by
   step 4 installing the model-label closure for the resolved `model` strategy —
   i.e. a Relay-Node type with no opt-in now emits `app_label.modelname` instead of
   Strawberry's `info.path.typename`. Confirm no separate default constant needs
   changing; the behavior change is purely that `install_globalid_typename_resolver`
   now runs and installs the model-label closure. (Spec line 93.)

8. **`django_strawberry_framework/filters/base.py` — make GlobalID validation
   strategy-aware (Decision 13).** Refactor so validation reads the resolved
   owner/target *definition*'s `effective_globalid_strategy` and accepts the
   matching payload shape:
   - Change `_expected_global_id_type_name` (filters-base.py:169-204) — which today
     returns the target's `graphql_type_name` string — to instead surface the
     resolved owner/target **definition** (own-PK branch → `owner`; relation branch
     → `target_definition` from `owner.related_target_for(head)`;
     filters-base.py:191-204). Worker 2 discretion on shape: either (a) rename it to
     `_target_definition_for(filter_instance) -> DjangoTypeDefinition | None` and
     move the strategy/shape logic into `_decode_and_validate_global_id`, or
     (b) keep a thin resolver returning the definition and add a small
     `_accepted_globalid_type_names(definition) -> set[str] | None` helper. Either
     way the resolution of WHICH definition (own-PK vs relation) stays single-sited.
   - In `_decode_and_validate_global_id` (filters-base.py:207-229), after decoding
     (`decoded = value if isinstance(value, relay.GlobalID) else relay.GlobalID.from_id(value)`,
     filters-base.py:222 — UNCHANGED), branch on the resolved definition's
     `effective_globalid_strategy`:
     - `model` → accept ONLY `definition.model._meta.label_lower`; reject a bare
       graphql type name.
     - `type` → accept ONLY `definition.graphql_type_name` (pre-`0.0.9` behavior).
     - `type+model` → accept EITHER the model label OR the graphql type name.
     - `callable` / `custom` (and the existing unbound-owner / unresolvable-target
       `None` case) → node-id-only fallback: skip the `type_name` guard entirely,
       return `decoded.node_id` (mirrors the existing `expected is None` fallback,
       filters-base.py:224). An absent (`None`) `effective_globalid_strategy` on a
       resolved definition (a non-finalized / non-Relay definition) ALSO falls back
       to node-id-only — the filter is defense-in-depth, not the uniform-error
       contract decode owns; do NOT raise from the filter for `None`.
     - A wrong-model/wrong-type ID (decoded `type_name` not in the accepted set for
       the three framework strategies) still raises the existing
       `GraphQLError("GlobalID type mismatch: filter expects <expected> but received <actual>")`
       (filters-base.py:226-227), with the `<expected>` text naming the accepted
       shape(s). Preserve the `index` suffix for the multi-value path
       (filters-base.py:225, 298).
   - The `node_id` extraction (`return decoded.node_id`, filters-base.py:229) is
     UNCHANGED across every strategy. `GlobalIDFilter` /
     `GlobalIDMultipleChoiceFilter` / `RelatedFilter`-expanded child filters all
     route through `_decode_and_validate_global_id` (filters-base.py:255, 298), so
     they inherit the strategy-aware behavior for free.
   - **Import the shared mapping** (`MODEL_LABEL_STRATEGIES` / the predicates) from
     `types/relay.py`. Direction check: `types/relay.py` module-top imports are
     stdlib/django/strawberry/`..exceptions` ONLY (relay.py:23-35) — no `filters`,
     no `registry`, no `.base` at module top — so a module-top
     `filters/base.py → types/relay.py` import is acyclic (`filters` → `types` is
     the documented safe direction; `types` imports `filters` only in-function, e.g.
     base.py:105, finalizer.py:799-801). Worker 2 confirms the import does not
     trip the load order; a module-top import in `filters/base.py` is preferred
     over an in-function one since no cycle exists. If a surprise cycle surfaces,
     fall back to an in-function import inside `_decode_and_validate_global_id`
     (the resolver is only called at filter-evaluation time).

### Test additions / updates

Per spec Test plan "Slice 2" (spec lines 575-596) and DoD item 4 (spec line 673).
All package-internal. Two test files (the spec names BOTH explicitly).

#### `tests/types/test_relay_interfaces.py` (extend) — spec lines 575-587

Reuse the file's existing Relay-Node `DjangoType` + `finalize_django_types()` +
registry-isolation fixtures (the file already exercises emitted-GlobalID payloads;
mirror its existing patterns). Use fakeshop models (e.g. `products.Item` /
`products.Category`) for the model-label expectations.

- `test_globalid_model_strategy_emits_model_label` — default Relay-Node type emits
  `app_label.modelname` (`products.item`) in the type-name slot.
- `test_globalid_type_strategy_emits_graphql_type_name` — `Meta.globalid_strategy = "type"`
  reproduces the pre-`0.0.9` GraphQL-type-name payload (byte-identical; framework
  installs nothing).
- `test_globalid_type_plus_model_emits_model_label` — `type+model` emits the
  model-label payload.
- `test_globalid_callable_strategy_emits_custom` — a callable returns the type-name
  slot and it appears in the emitted GlobalID.
- `test_globalid_callable_non_string_return_raises` — a callable returning a
  non-`str` (or empty) value raises `ConfigurationError` from the installed closure
  (NOT Strawberry's `Node._id` `AssertionError`).
- `test_consumer_resolve_typename_override_preserved_and_recorded_custom` — a
  consumer `resolve_typename` survives injection (the `__func__` test leaves it in
  place) AND `definition.effective_globalid_strategy == "custom"`.
- `test_resolve_typename_override_plus_meta_strategy_raises` — declaring both an
  override AND explicit `Meta.globalid_strategy` raises `ConfigurationError` at
  finalization; an override + only the schema-wide `RELAY_GLOBALID_STRATEGY` setting
  does NOT raise (the setting is a default an override supersedes).
- `test_model_label_routing_audit_rejects_type_primary_with_model_secondary` — a
  multi-type model whose primary is `type` and a secondary is default `model`
  raises `ConfigurationError` at finalization; assert the message names the model,
  the emitter, and the primary's strategy. Also assert the passing arrangements:
  all-`type+model`, primary-`model` (+ `type` secondary), and a single-type model
  all finalize cleanly (the invariant is scoped to multi-type models).
- `test_finalize_rerun_after_audit_raise_preserves_recorded_strategy` — the
  re-entrancy test: build a config that makes the Phase-2.5 routing audit raise,
  call `finalize_django_types()` (raises), then call it again (bare re-run, same
  definitions) and assert every type's recorded `effective_globalid_strategy` is
  unchanged (no `model`→`custom` misclassification from re-running the `__func__`
  test on an already-installed framework closure — the step-0 guard). The simplest
  durable assertion: capture each definition's `effective_globalid_strategy` after
  the first (raising) finalize, re-run, and confirm equality; the audit re-raises
  on the still-bad config (assert it does).
- `test_globalid_default_is_model` — no `Meta` key + no setting → recorded
  `effective_globalid_strategy == "model"` and emitted slot is the model label.
- (setting path) `test_callable_setting_well_formed_accepted` /
  `test_callable_setting_wrong_arity_raises` / `test_callable_setting_async_raises`
  — a `RELAY_GLOBALID_STRATEGY` callable runs through the SAME Slice-1
  `_validate_globalid_strategy` arity/sync validation (reached via
  `_resolve_globalid_strategy` at finalization); the failures raise a
  finalization-time `ConfigurationError` whose message names `RELAY_GLOBALID_STRATEGY`
  (vs. the type-creation error naming the type for the `Meta` path). Use the
  pytest-django `settings` fixture + a registry-clear + reload, mirroring the
  Slice-1 precedence test's settings-override pattern.

#### `tests/filters/test_base.py` (extend) — spec lines 589-596, Decision 13

The file already has lightweight fake owner/target definition scaffolding
(`_FakePk` / `_FakeMeta` / `_FakeModel` / `_FakeTargetDefinition` /
`_FakeOwnerDefinition` / `_FakeParent` / `_global_id_filter_with_owner`,
test_base.py:474-509). Extend those fakes to carry `effective_globalid_strategy`
and a `model._meta.label_lower` so the strategy-aware branches are exercised
without a full finalize (or, where a real round-trip reads cleaner, build a real
Relay-Node `DjangoType` + finalize and bind its definition as owner — Worker 2
discretion). The decoded inputs are built with `relay.to_base64(type_name, node_id)`
(model-label and graphql-name forms).

- `test_filter_model_strategy_accepts_model_label` /
  `test_filter_model_strategy_rejects_type_name` — under `model`, an own-PK
  `GlobalIDFilter` accepts the model-label payload and rejects the bare GraphQL
  type name (raises `GraphQLError`).
- `test_filter_type_strategy_accepts_graphql_name` — `type` preserves the
  pre-`0.0.9` `graphql_type_name` acceptance.
- `test_filter_type_plus_model_accepts_both` — `type+model` accepts model-label AND
  type-name inputs.
- `test_filter_callable_custom_node_id_only` — a `callable` / `custom` (override)
  type's filter falls back to node-id-only (decodes, skips the `type_name` guard);
  also covers the existing `None`-strategy / unbound-owner fallback staying intact.
- `test_filter_wrong_model_rejected` — a wrong-model GlobalID is still rejected for
  the three framework strategies.
- `test_related_filter_and_multi_value_strategy_aware` — `RelatedFilter`-expanded
  child filters (relation branch → target definition) AND
  `GlobalIDMultipleChoiceFilter` (the `index`-suffixed multi-value path) route
  through the same strategy-aware check.

Confirm the existing `_expected_global_id_type_name` tests (test_base.py:512-537)
are updated to the refactored shape (they currently assert the string return; the
refactor changes that contract — Worker 2 updates or replaces them, NOT silently
leaving stale assertions). This is a Slice-2 in-scope churn, not unrelated drift.

Temp/scratch tests: none required — every branch is package-internal and directly
covers a Slice-2 contract. Worker 3 should confirm (a) the re-entrancy test truly
exercises the step-0 guard (the recorded strategy survives a re-run), and (b) the
filter tests exercise BOTH rejection (wrong shape) and node-id-only fallback paths
per strategy.

### Implementation discretion items

Assessed and intentionally delegated to Worker 2 (equivalent-shape / naming
choices); none are architectural escape hatches:

- The exact names of the strategy→payload-shape source-of-truth symbols in
  `types/relay.py` (`MODEL_LABEL_STRATEGIES`, `_emits_model_label`,
  `_accepts_model_label_decode`) — any clear names; the requirement is ONE source
  reused by encoder/audit/filter/(Slice-3)decoder, not the literal spelling.
- Whether `encode_typename` is a single dispatch function the closure calls or the
  per-strategy closures inline the slot read — provided the model-label and
  graphql-name reads are not duplicated across install branches and the non-empty-
  `str` callable-return check is single-sited.
- Whether to extract a tiny `_consumer_overrode(type_cls, attr)` predicate for the
  `__func__` test or inline the idiom once in `install_globalid_typename_resolver`
  (the table-driven loop in `install_relay_node_resolvers` is structurally
  different) — Worker 2's call.
- The `filters/base.py` refactor shape: rename `_expected_global_id_type_name` to a
  definition-returning resolver vs. keep it + add an
  `_accepted_globalid_type_names(definition)` helper — either, provided the own-PK
  vs relation resolution stays single-sited and the node-id extraction is unchanged.
- Whether the shared mapping import in `filters/base.py` is module-top (preferred,
  no cycle) or in-function (fallback if a surprise cycle surfaces).
- The exact `ConfigurationError` / `GraphQLError` message wording, within the
  spec's required content (the routing audit names model + emitter + primary's
  strategy; the both-declared conflict names the two contradictory sources; the
  callable-return guard names the type + `(type_cls, model, root, info) -> str`
  contract; the filter mismatch names the accepted shape(s)).
- Whether the filter tests use extended fake-definition scaffolding or a real
  finalized `DjangoType` owner — Worker 2 picks whichever reads cleaner per case.

No unresolved architectural questions — nothing escalated to the maintainer.

### Spec slice checklist (verbatim)

- [x] [`django_strawberry_framework/types/relay.py`][relay] gains an `encode_typename(definition, strategy)`-style internal helper that returns the type-name slot for the resolved strategy: `model` → `definition.model._meta.label_lower` (`"products.item"`); `type` → the GraphQL type name ([`definition.graphql_type_name`][definition], matching Strawberry's `info.path.typename` default); `type+model` → the model label (emit model-anchored, accept both on decode, per [Decision 4](#decision-4--four-strategies-model-type-typemodel-callable-and-an-unchanged-node_id-portion)); callable → the consumer callable's return (signature `(type_cls, model, root, info) -> str`, sync, mirroring the `resolve_typename` seam — it never receives `node_id`, per [Decision 4](#decision-4--four-strategies-model-type-typemodel-callable-and-an-unchanged-node_id-portion)).
- [x] An `install_globalid_typename_resolver(type_cls, definition)` step (called from [`finalize_django_types`][glossary-finalize_django_types] Phase 2.5, alongside `install_relay_node_resolvers`) is **re-entrant-safe**: if `definition.effective_globalid_strategy is not None` it skips (the type was processed in a prior partial run — [Decision 10](#decision-10--resolve_typename-injection-via-the-__func__-identity-test-at-phase-25) step 0, [`docs/feedback.md`][feedback] P1). Otherwise it runs the `existing.__func__ is relay.Node.resolve_typename.__func__` override test (MRO-aware) **before** installing: a consumer override → effective strategy **`custom`**, install nothing (and if the type also declares an explicit `Meta.globalid_strategy`, raise [`ConfigurationError`][glossary-configurationerror] — the both-declared conflict); no override → resolve via `_resolve_globalid_strategy`, install the package closure for `model` / `type+model` / `callable` (the `callable` closure raises [`ConfigurationError`][glossary-configurationerror] on a non-`str` / empty return; the callable's arity / sync-ness were already validated at type creation), leave Strawberry's default for `type`. It records the resolved effective strategy (`model` / `type` / `type+model` / `callable` / `custom`) in the named field **`effective_globalid_strategy: str | None = None`** on the [`DjangoTypeDefinition`][definition] (distinct from the Slice-1 raw `globalid_strategy` slot), which decode reads and which also serves as the step-0 re-entrancy sentinel.
- [x] A Phase-2.5 **model-label-routing audit** (parallel to `_audit_primary_ambiguity`, after every type's effective strategy is recorded): for each model, if any registered type's effective strategy emits model-label IDs (`model` / `type+model`), the model's [`Meta.primary`][glossary-metaprimary] type's effective strategy must accept model-label decode (`model` / `type+model`), else [`ConfigurationError`][glossary-configurationerror] naming the model, the emitter, and the primary's strategy ([Decision 8](#decision-8--decode-routes-through-djangos-app-registry-then-the-framework-registry-to-the-primary-type), [`docs/feedback.md`][feedback] P1).
- [x] Flip the **package default** from the (DONE-015) type-anchored `GlobalID` to `model`: a Relay-Node-shaped type with no `Meta.globalid_strategy` and no `RELAY_GLOBALID_STRATEGY` setting now emits the model-label payload (per [Decision 9](#decision-9--changing-the-default-to-model-is-a-breaking-wire-format-change-acceptable-pre-100)).
- [x] **Make `GlobalID` filter validation strategy-aware (co-lands with the flip — [Decision 13](#decision-13--globalid-filter-validation-is-strategy-aware)).** [`filters/base.py::_decode_and_validate_global_id`][filters-base] reads the resolved owner/target definition's recorded `effective_globalid_strategy` and accepts the matching payload shape — `model` → model label, `type` → `graphql_type_name`, `type+model` → both, `callable` / `custom` (and the existing unbound/unresolvable case) → node-id-only fallback — so an emitted model-label ID round-trips through `GlobalIDFilter` / `GlobalIDMultipleChoiceFilter` / [`RelatedFilter`][glossary-relatedfilter]-expanded child filters instead of being rejected against the old GraphQL type name. Package coverage in [`tests/filters/test_base.py`][test-filters-base]: own-PK, relation, and multi-value round-trips under each framework strategy; wrong-model/type rejection; the `callable` / `custom` node-id-only path.
- [x] Package coverage: [`tests/types/test_relay_interfaces.py`][test-relay-interfaces] — each strategy's emitted type-name slot; the consumer-`resolve_typename`-override preservation **and** its `custom` effective-strategy recording; the both-declared (override + `Meta.globalid_strategy`) `ConfigurationError`; the non-`str` callable-return `ConfigurationError`; the model-label-routing audit `ConfigurationError` (a `type`-primary with a `model`-secondary, scoped to multi-type models); **a re-entrancy test — a finalize whose Phase-2.5 audit raises, then a re-run, leaves the recorded effective strategy intact (no `model`→`custom` misclassification, [`docs/feedback.md`][feedback] P1)**; the default-flip (no override → `model`); the `type`-strategy reproduces the pre-`0.0.9` GraphQL-type-name payload.

---

## Build report (Worker 2)

### Files touched

- `django_strawberry_framework/types/definition.py` — added the finalization-set `effective_globalid_strategy: str | None = None` field (distinct from the Slice-1 raw `globalid_strategy` slot), immediately after `globalid_strategy` and before `finalized`; rewrote the docstring TODO portion into a full description of the field (its five classification strings, the re-entrancy-sentinel role, the `None` ⇒ "not framework-decodable" meaning) and removed the satisfied inline TODO.
- `django_strawberry_framework/types/relay.py` — added `MODEL_LABEL_STRATEGIES = frozenset({"model", "type+model"})` + the `_emits_model_label` / `_accepts_model_label_decode` predicates (the single source of truth for the strategy→payload-shape mapping); `encode_typename(definition, strategy, type_cls, root, info)` (the per-strategy slot computation incl. the non-empty-`str` callable-return guard); `_consumer_overrode_resolve_typename(type_cls)` (the MRO-aware `__func__` identity test against `relay.Node.resolve_typename.__func__`); `install_globalid_typename_resolver(type_cls, definition)` (the ordered step-0 re-entrancy guard / override-detection / no-override resolve+install / record); and the private `_install_typename_closure(...)` that captures the resolved strategy in a `classmethod`. Replaced the Slices-2-3 encode/install TODO with these; narrowed the remaining TODO to the Slice-3 decode seam only.
- `django_strawberry_framework/types/finalizer.py` — extended the `from .relay import (...)` block with `_accepts_model_label_decode`, `_emits_model_label`, `install_globalid_typename_resolver`; added `_format_model_label_routing_error(...)` + `_audit_model_label_routing()` + the `_first_model_label_emitter(model)` helper (modeled on `_format_ambiguity_error` / `_audit_primary_ambiguity`); wired `install_globalid_typename_resolver(type_cls, definition)` into the Phase-2.5 Relay loop after `install_relay_node_resolvers`, and called `_audit_model_label_routing()` after the loop (every type's strategy recorded) and before `_bind_filtersets()`. Removed both satisfied TODOs.
- `django_strawberry_framework/filters/base.py` — added a module-top `from ..types.relay import MODEL_LABEL_STRATEGIES` (acyclic; `filters → types`) and a `TYPE_CHECKING` import of `DjangoTypeDefinition`; renamed `_expected_global_id_type_name` → `_target_definition_for(filter_instance) -> DjangoTypeDefinition | None` (now returns the resolved owner/target *definition*, keeping the own-PK-vs-relation resolution single-sited); added `_accepted_globalid_type_names(definition) -> set[str] | None` (the per-strategy accepted-`type_name` set, with `callable`/`custom`/absent/`None` → node-id-only fallback); rewired `_decode_and_validate_global_id` to branch on the accepted set (joining multiple accepted names with `" or "` in the mismatch message). Node-id extraction unchanged across every strategy.
- `django_strawberry_framework/filters/inputs.py` — one-line comment fix: the `_owner_type_name` docstring named the renamed `filters/base.py::_expected_global_id_type_name`; updated to `_accepted_globalid_type_names` (the helper that now reads `graphql_type_name`). Rename-driven, in-scope.
- `tests/types/test_relay_interfaces.py` — added `encode_typename` to the `types.relay` import; appended the spec-031 Slice 2 test section (see below).
- `tests/filters/test_base.py` — added `from graphql import GraphQLError`; swapped the `_expected_global_id_type_name` import for `_accepted_globalid_type_names` / `_decode_and_validate_global_id` / `_target_definition_for`; extended the fake-definition scaffolding to carry `effective_globalid_strategy` + `model._meta.label_lower`; updated the four existing `_expected_*` tests to the renamed `_target_definition_for` contract and added the strategy-aware tests (see below).

### Tests added or updated

`tests/types/test_relay_interfaces.py` (spec lines 575-587) — local `_emitted_typename(type_cls)` helper reads the emitted type-name slot via the installed `resolve_typename` closure (which ignores `info` for `model`/`type+model`/`callable`):

- `::test_globalid_model_strategy_emits_model_label` — default → `products.category`, recorded `"model"`.
- `::test_globalid_type_strategy_emits_graphql_type_name` — `type` records `"type"`, installs NOTHING (`resolve_typename.__func__` is still `relay.Node`'s default), `graphql_type_name == "CategoryNode"` (byte-identical pre-0.0.9 payload).
- `::test_globalid_type_plus_model_emits_model_label` — `type+model` → model label, recorded `"type+model"`.
- `::test_globalid_callable_strategy_emits_custom` — a callable's return reaches the emitted slot, recorded `"callable"`.
- `::test_globalid_callable_non_string_return_raises[None/42/""/bytes]` — non-`str`/empty callable return → `ConfigurationError("must return a non-empty string")` from the installed closure.
- `::test_encode_typename_helper_dispatch` — `encode_typename` computes `model`/`type+model`/`type`/callable slots directly.
- `::test_consumer_resolve_typename_override_preserved_and_recorded_custom` — override survives, recorded `"custom"`.
- `::test_resolve_typename_override_plus_meta_strategy_raises` — both-declared → `ConfigurationError`.
- `::test_resolve_typename_override_plus_setting_does_not_raise` — override + only the schema-wide setting is NOT a conflict (recorded `"custom"`).
- `::test_globalid_default_is_model` — no Meta + no setting → `"model"` + model label.
- `::test_model_label_routing_audit_rejects_type_primary_with_model_secondary` — `type`-primary + `model`-secondary → `ConfigurationError` naming model/`SecondaryType`/`'type'`.
- `::test_model_label_routing_audit_passes_all_type_plus_model` / `..._passes_model_primary_with_type_secondary` / `..._single_type_model_passes` — the passing arrangements.
- `::test_finalize_rerun_after_audit_raise_preserves_recorded_strategy` — the re-entrancy test (capture recordings after the raising finalize, bare re-run re-raises AND leaves recordings intact).
- `::test_callable_setting_well_formed_accepted` / `..._wrong_arity_raises` / `..._async_raises` — the `RELAY_GLOBALID_STRATEGY` callable runs through the same Slice-1 arity/sync validation; failures raise at finalization naming the setting.

`tests/filters/test_base.py` (spec lines 589-596, Decision 13):

- Renamed/updated: `::test_target_definition_for_returns_none_without_owner` / `..._own_pk_branch` / `..._relation_branch` / `..._relation_branch_unresolved_target`.
- `::test_accepted_globalid_type_names_none_definition` / `..._per_strategy` / `..._node_id_only_strategies[callable/custom/None]` — the per-strategy accepted-set mapping.
- `::test_filter_model_strategy_accepts_model_label` / `..._rejects_type_name`.
- `::test_filter_type_strategy_accepts_graphql_name` (also rejects the model-label under `type`).
- `::test_filter_type_plus_model_accepts_both`.
- `::test_filter_callable_custom_node_id_only[callable/custom/None]` / `::test_filter_unbound_owner_node_id_only`.
- `::test_filter_wrong_model_rejected`.
- `::test_related_filter_relation_branch_strategy_aware` (relation → target definition strategy) / `::test_multi_value_filter_strategy_aware_indexes_rejection` (`GlobalIDMultipleChoiceFilter` index-suffixed rejection, spying on the upstream filter).

### Validation run

- `uv run ruff format .` — pass (reformatted 1 file — `tests/types/test_relay_interfaces.py`, the appended test block).
- `uv run ruff check --fix .` — pass after one SIM108 fix (collapsed the `classification` if/else in `install_globalid_typename_resolver` to a ternary); final run "All checks passed!".
- `git status --short` after both ruff invocations — modified files:
  - `M django_strawberry_framework/types/definition.py` — slice-intended.
  - `M django_strawberry_framework/types/relay.py` — slice-intended (carries Slice-1's `_resolve_globalid_strategy` + my Slice-2 additions).
  - `M django_strawberry_framework/types/finalizer.py` — slice-intended.
  - `M django_strawberry_framework/filters/base.py` — slice-intended.
  - `M django_strawberry_framework/filters/inputs.py` — slice-intended (rename-driven comment fix).
  - `M tests/types/test_relay_interfaces.py` — slice-intended.
  - `M tests/filters/test_base.py` — slice-intended.
  - `M django_strawberry_framework/types/base.py`, `M tests/types/test_base.py` — **NOT this slice's work and NOT tool churn**: these carry Slice-1's `_validate_globalid_strategy` + the 10 Slice-1 tests, accumulated in the shared working tree (workers never commit; the maintainer commits the whole build cycle). I did not touch them this pass; reverting them would destroy Slice-1's `final-accepted` work, so they are correctly left in place.
  - `?? docs/builder/bld-slice-1-...md`, `?? bld-slice-2-...md`, `?? build-031-...md` — the build cycle's own artifacts.
  - No unrelated tool churn; nothing reverted. The expected spec-030 archive deletions are the maintainer's concurrent "archive 030" commit — not present in the tree, left untouched per the dispatch note.
- Focused tests (optional, no `--cov*`): `uv run pytest --no-cov tests/types/test_relay_interfaces.py tests/filters/test_base.py tests/types/test_base.py tests/filters/test_finalizer.py tests/types/test_definition_order_schema.py` → all green (233 + finalizer/schema suites pass).

### Implementation notes

- **`encode_typename` signature `(definition, strategy, type_cls, root, info)`.** The plan left "single dispatch fn vs inline" to discretion. I chose ONE dispatch function the installed closure calls, so the model-label / graphql-name reads and the non-empty-`str` callable-return guard are each single-sited. The closure passes the bound `cls` as `type_cls` so the callable receives the documented `(type_cls, model, root, info)` contract.
- **`_install_typename_closure` is a separate private fn** (not inlined in `install_globalid_typename_resolver`) so the `classmethod(closure)` capture site is named and the install step reads as the linear step-0/1/2/3 sequence the spec describes.
- **Extracted `_consumer_overrode_resolve_typename` predicate** (Worker-1 discretion item). The four-line `__func__` idiom is cleaner as a named predicate here than inlined; `install_relay_node_resolvers` keeps its table-driven loop unchanged (structurally different — it iterates `_RELAY_RESOLVER_DEFAULTS`). `resolve_typename` is deliberately NOT added to `_RELAY_RESOLVER_DEFAULTS` (spec Decision 10 — the table maps name→one static default; the typename default is strategy-parameterized).
- **Filter refactor shape: rename + add `_accepted_globalid_type_names`** (Worker-1 discretion: rename vs keep-thin-resolver). I took the rename path — `_target_definition_for` resolves the single definition; `_accepted_globalid_type_names` owns the strategy→accepted-set logic. The mismatch message joins multiple accepted names with `" or "` (sorted for determinism) so `type+model` reports "X or Y".
- **`_first_model_label_emitter` helper in finalizer.py** — extracted so `_audit_model_label_routing`'s body stays readable; single-sources the per-type `get_definition(t).effective_globalid_strategy` read used inside the emitter scan.
- **Module-top import in `filters/base.py`** (preferred shape). Verified acyclic at runtime by importing the package under Django setup (`filters.base`, `types.relay`, `types.finalizer` all import clean); `types/relay.py` reaches `filters`/`registry` only via in-function imports, so no cycle. No in-function fallback needed.

### Notes for Worker 3

- No shadow file used (additions modeled directly on the cited precedents: `install_relay_node_resolvers` for the install step, `_audit_primary_ambiguity`/`_format_ambiguity_error` for the audit, the existing `_expected_global_id_type_name` for the filter resolver).
- Decode is intentionally NOT implemented — it is Slice 3 (a narrowed decode-only TODO remains in `relay.py`). `MODEL_LABEL_STRATEGIES` / `_accepts_model_label_decode` are left available for Slice 3's Step-2 enforcement per the plan.
- The two filter-rejection directions AND the node-id-only fallback are both exercised per strategy in `tests/filters/test_base.py`; the re-entrancy test captures recordings after the raising finalize and asserts equality after the bare re-run (exercises the step-0 guard, not just that the re-run re-raises).
- `git status` shows `types/base.py` + `tests/types/test_base.py` modified — these are Slice-1's accepted diff in the shared working tree, NOT my changes (see Validation run). Worker 3's diff review should scope `git diff` to this slice's files (`definition.py`, `relay.py`, `finalizer.py`, `filters/base.py`, `filters/inputs.py`, `tests/types/test_relay_interfaces.py`, `tests/filters/test_base.py`).

### Notes for Worker 1 (spec reconciliation)

No spec gap, conflict, or unstated assumption surfaced; the plan resolved cleanly against the current source. No plan-vs-implementation drift (the two discretion choices — extract the `__func__` predicate, take the filter-rename path — are within the plan's explicitly-delegated discretion items). Two observations for downstream slices:

- **Slice-4 example-test breakage observed (expected blast radius, NOT fixed here per slice scope).** Running `examples/fakeshop/test_query/test_products_api.py` confirms the default flip + strategy-aware filter (Decision 13) break the existing live filter-input assertions: `test_products_categories_filter_by_relay_own_pk_global_id_in`, `test_products_items_filter_by_related_category_global_id`, and `test_products_items_filter_and_order_compose` now fail with `GlobalID type mismatch: filter expects products.category but received CategoryType` — exactly the spec's Slice-4 churn (`filter-input GlobalID`s must move from `CategoryType:<pk>` to `products.category:<pk>`). The same applies to the emitted-ID assertions in `test_library_api.py` (`assert type_name == "GenreType"`, the `node { id }` decode loops at lines 709-710, 2167-2168) and the filter-input / wrong-type-rejection inputs that build `CategoryType`/`GenreType`/`BookType`/`LoanType` (e.g. `test_library_api.py` lines 904, 934-935, 956, 1318-1319; `test_kanban_api.py` lines 265-266). These are deferred to Slice 4 per spec Risks "Default-flip blast radius" and the build-plan flag — out of scope for Slice 2 (package tests only).
- The filter mismatch message now reports the model label (e.g. `products.category`) under the `model` strategy and "X or Y" under `type+model`; Slice-4's `test_library_api.py` type-mismatch assertions that pin `"GenreType" in message` (e.g. line 1335) will need updating to the model-label expectation. Flagged for Worker 1's Slice-4 planning, not fixed here.

---

## Review (Worker 3)

Reviewed the working-tree diff against spec-031 Decisions 3/4/9/10/13, the Slice-2 checklist sub-bullets (spec lines 89-95), the two Slice 2 Test plan sections (spec lines 575-596), and DoD item 4 (spec line 673). Diff scoped to this slice via the artifact's `### Files touched` filter (`git diff -- django_strawberry_framework/ tests/`); Slice-1's `types/base.py` + `tests/types/test_base.py` (final-accepted, uncommitted in the shared tree) were NOT re-reviewed; the `types/relay.py` / `types/definition.py` Slice-1 parts (`_resolve_globalid_strategy`, the raw `globalid_strategy` slot) were treated as accepted context, not re-reviewed.

Static helper run (required — slice touches `types/relay.py`, `types/finalizer.py`, `types/definition.py`, `filters/base.py`), all to `docs/shadow`. Walked the Django/ORM markers, control-flow hotspots, and Repeated string literals sections. Focused tests run without `--cov*`: `tests/types/test_relay_interfaces.py` + `tests/filters/test_base.py` → 144 passed. Import-cycle and single-sourcing verified at runtime under Django setup.

### High:

None.

### Medium:

None.

### Low:

None.

### Spec slice checklist walk (verbatim boxes)

All six boxes ticked `- [x]` by Worker 2; each verified against the diff:

1. **`encode_typename`** — `types/relay.py::encode_typename(definition, strategy, type_cls, root, info)`. `model`/`type+model` → `definition.model._meta.label_lower`; `type` → `definition.graphql_type_name`; callable → `strategy(type_cls, definition.model, root, info)` with the non-empty-`str` guard raising `ConfigurationError` (not Strawberry's `AssertionError`). The callable receives `(type_cls, model, root, info)` and never `node_id` (Decision 4). Box correctly ticked. (Note: the `type` branch is reachable only from the direct dispatch test — the closure is never installed for `type` — which the plan authorized as a single dispatch surface; not a defect.)
2. **`install_globalid_typename_resolver` re-entrant-safe** — step-0 guard `if definition.effective_globalid_strategy is not None: return` is the first statement; the `__func__` override test (`_consumer_overrode_resolve_typename`, MRO-aware, against `relay.Node.resolve_typename.__func__`) runs BEFORE install; override → `custom`, install nothing; override + raw `Meta.globalid_strategy` (keyed on `definition.globalid_strategy is not None`, NOT the setting) → `ConfigurationError`; `type` leaves Strawberry's default; `model`/`type+model`/`callable` install the closure; `effective_globalid_strategy` recorded. Box correctly ticked.
3. **Model-label-routing audit** — `finalizer.py::_audit_model_label_routing()` scoped to `registry.models_with_multiple_types()`, placed AFTER the Phase-2.5 Relay loop records every strategy and BEFORE `_bind_filtersets()` / Phase-3 `finalized = True` / `mark_finalized()`; raises naming model + emitter + primary's strategy. `_audit_primary_ambiguity()` runs at Phase-1 top, so `primary_for(model)` is guaranteed non-`None` for the multi-type scope. Box correctly ticked.
4. **Default flip to `model`** — realized by the install step installing the model-label closure for the resolved `model` strategy (default via `DEFAULT_GLOBALID_STRATEGY`); confirmed live: `test_globalid_default_is_model` and the example-suite breakage both show emitted/expected `products.category` etc. Box correctly ticked.
5. **Strategy-aware filter validation** — `filters/base.py`: `_expected_global_id_type_name` → `_target_definition_for` (returns the resolved owner/target definition, single-sited own-PK-vs-relation resolution); `_accepted_globalid_type_names` maps `model`→label / `type`→graphql-name / `type+model`→both / `callable`/`custom`/`None`→node-id-only; `_decode_and_validate_global_id` branches on the accepted set; node-id extraction unchanged; `GlobalIDFilter` / `GlobalIDMultipleChoiceFilter` / `RelatedFilter` child filters all route through it. Box correctly ticked.
6. **Test coverage (`test_relay_interfaces.py` + `test_base.py`)** — every named Slice-2 test present and passing; both rejection directions, the node-id-only fallback per strategy, the wrong-model rejection, the relation branch, and the index-suffixed multi-value rejection are exercised; the re-entrancy test captures recordings after the raising finalize and asserts equality after the bare re-run (exercises the step-0 guard). Box correctly ticked.

No box was ticked without matching implementation; no sub-check is silently un-addressed.

### Correctness verification performed

- **Acyclic import + true single-sourcing.** Imported `filters.base`, `types.relay`, `types.finalizer` under Django setup — clean. `filters.base.MODEL_LABEL_STRATEGIES is relay.MODEL_LABEL_STRATEGIES` → `True` (the module-top `filters → types` import binds the same frozenset object, not a copy).
- **Re-entrancy guard.** `test_finalize_rerun_after_audit_raise_preserves_recorded_strategy` confirms recordings survive a bare re-run on a still-bad config; the audit re-raises and no `model`→`custom` misclassification occurs. The guard is the first statement of `install_globalid_typename_resolver`.
- **Audit placement.** Read finalizer.py lines 269/337-346: `_audit_primary_ambiguity()` (Phase-1 top) → Relay loop (records every strategy) → `install_globalid_typename_resolver` → `_audit_model_label_routing()` → `_bind_filtersets/_bind_ordersets` → Phase-3 `finalized = True` → `mark_finalized()`. Placement is load-bearing-correct.
- **Both-declared conflict keys on the raw Meta slot, not the setting.** Verified `if definition.globalid_strategy is not None:` and confirmed by `test_resolve_typename_override_plus_setting_does_not_raise` (override + setting → `custom`, no raise).
- **Filter focused suite** — 144 passed.
- **Deferred example breakage is real (verifies the deferral was correct, not a silent break).** Ran `examples/fakeshop/test_query/test_products_api.py::test_products_categories_filter_by_relay_own_pk_global_id_in` → fails with `GlobalID type mismatch: filter expects products.category but received CategoryType at index 0`, exactly the spec's Slice-4 churn. `git diff --stat -- examples/` is empty; `git status --short -- examples/` is empty — Worker 2 did NOT touch the example suite.

### DRY findings

- **`MODEL_LABEL_STRATEGIES` is correctly the one source of truth** for the model-label membership, reused by `encode_typename`, `_emits_model_label`/`_accepts_model_label_decode`, the finalizer audit, and the filter (and reserved for the Slice-3 decoder). Verified as the identical object across the `filters → types` import. This satisfies the plan's headline DRY watch point.
- **(Low, non-blocking, deferred to Worker 1 / Slice 3.)** The graphql-name-acceptance membership is spelled as a bare tuple literal `("type", "type+model")` at `filters/base.py::_accepted_globalid_type_names`. It is the *other* strategy-set (which strategies emit/accept the GraphQL-type-name slot) and currently appears exactly once, so it is NOT presently duplicated — no current DRY violation. But Slice 3's decode Step-2 enforcement will need the same "which strategies accept a type-name payload" notion; if Slice 3 re-types `{"type", "type+model"}`, that second site turns this into a parallel-literal-set defect. Recommend Worker 1/Slice 3 introduce a sibling named membership (e.g. `TYPE_NAME_STRATEGIES`) at the same `types/relay.py` source of truth when the decoder lands, rather than re-typing the tuple. Flagged, not blocking — single-site today.
- The `ConfigurationError` message-builder pattern (`_format_model_label_routing_error` returning a string, raised by the caller) mirrors `_format_ambiguity_error`; the audit body (`_audit_model_label_routing` + `_first_model_label_emitter`) mirrors `_audit_primary_ambiguity`. No bespoke divergent error style introduced.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` is empty — no change to `__all__` or the re-export list. Consistent with Decision 11 ("No new public export in `0.0.9`"; encode helpers are internal). Pass.

### CHANGELOG sanity

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces. (The only doc-shaped edits in the diff are source-level docstrings/comments on `definition.py` / `relay.py` / `finalizer.py` / `filters/base.py`, which are part of the source changes, not standing docs.)

### What looks solid

- The strategy→payload-shape single-sourcing is genuinely single-sourced (same frozenset object across the `filters → types` boundary), and the encoder / audit / filter all consume it — the build's central DRY contract.
- The install step reads as the clean linear step-0/1/2/3 sequence the spec describes, with the re-entrancy guard as the first statement and the both-declared conflict keyed precisely on the per-type Meta slot (not the setting).
- The audit placement is exactly the load-bearing site Decision 10 demands (after all recordings, before Phase 3), and the recoverability story (re-run re-enters the loop, guard prevents misclassification) is both implemented and test-pinned.
- Test coverage is comprehensive against the Test plan: every strategy's emitted slot, both filter-rejection directions, node-id-only fallback per strategy, wrong-model rejection, relation + multi-value paths, the override→`custom` recording, the both-declared raise, the non-`str` callable raise, the audit raise + passing arrangements, the re-entrancy preservation, and the callable-setting arity/sync reuse.
- The example-suite blast radius was correctly observed, confirmed real, and DEFERRED to Slice 4 (not silently fixed), with the affected assertions enumerated for Worker 1's Slice-4 planning.

### Temp test verification

No temp tests created. The existing package tests plus a runtime import-cycle/single-sourcing check and a focused run of one deferred example test were sufficient to verify every reviewed behavior. Disposition: none to promote.

### Notes for Worker 1 (spec reconciliation)

- No spec gap or conflict surfaced; the implementation matches Decisions 3/4/9/10/13 as written. No `Escalated:` items.
- Carry to Slice 3 (decode): the `TYPE_NAME_STRATEGIES`-membership DRY note above — introduce the sibling named constant at `types/relay.py` when the decode Step-2 enforcement lands, so `{"type", "type+model"}` does not become a parallel literal set across the filter and the decoder.
- Carry to Slice 4: Worker 2's enumerated example-suite breakage (the `products.category` / `library.genre` model-label moves for emitted-ID AND filter-input assertions, and the `"GenreType" in message` mismatch-text assertions now needing the model-label expectation) is the Slice-4 work list, licensed by spec Risks "Default-flip blast radius" + the build-plan "Breaking default flip" flag.

### Review outcome

`review-accepted` — every spec-required Slice-2 behavior is reflected in the diff, every verbatim checklist box correctly landed, the public surface is unchanged, the central DRY contract is single-sourced, all 144 focused tests pass, and the example-suite breakage was correctly deferred (not fixed). The one DRY observation is a single-site, non-duplicated, forward-looking note for Slice 3, recorded as a deferred follow-up for Worker 1 — not an unresolved finding.

---

## Final verification (Worker 1)

Fresh Worker-1 subagent, final-verification pass for Slice 2 (the encode seam). I am
no longer the original ticker — I AUDIT Worker 2's verbatim-checklist ticks against
the actual working-tree diff. Diff is cumulative Slice 1 + Slice 2 (workers never
commit); audited ONLY the Slice-2 contract. The "archive 030" commit (`502891e0`) is
the expected concurrent maintainer activity. Slice-1-only files (`types/base.py`,
`tests/types/test_base.py`) were NOT re-audited (final-accepted in
`bld-slice-1-globalid_strategy_key.md`).

### Spec slice checklist audit (verbatim boxes)

All six `- [x]` boxes were verified against the source diff; each truly landed:

1. **`encode_typename`** — `types/relay.py::encode_typename(definition, strategy, type_cls, root, info)` (relay.py:406). `model`/`type+model` → `definition.model._meta.label_lower`; `type` → `definition.graphql_type_name`; callable → `strategy(type_cls, definition.model, root, info)` with the non-empty-`str` guard raising `ConfigurationError` (not Strawberry's `AssertionError`); callable never receives `node_id` (Decision 4). Truly landed.
2. **`install_globalid_typename_resolver` re-entrant-safe** — `types/relay.py:463`. Step-0 guard `if definition.effective_globalid_strategy is not None: return` is the first statement; `_consumer_overrode_resolve_typename` (MRO-aware `__func__` test vs `relay.Node.resolve_typename.__func__`, relay.py:447) runs before install; override → `custom` install nothing; override + raw `definition.globalid_strategy` (NOT the setting) → `ConfigurationError`; `type` leaves Strawberry's default; `model`/`type+model`/`callable` install the closure; `effective_globalid_strategy` recorded. Truly landed.
3. **Model-label-routing audit** — `finalizer.py::_audit_model_label_routing()` (finalizer.py:177) scoped to `registry.models_with_multiple_types()`; called at finalizer.py:346 AFTER the Phase-2.5 Relay loop records every strategy and BEFORE `_bind_filtersets()` / Phase-3 `finalized = True` (finalizer.py:351-355) / `mark_finalized()` (finalizer.py:357); raises naming model + emitter + primary's strategy. Truly landed.
4. **Default flip to `model`** — realized by the install step installing the model-label closure for the resolved default `model` strategy (`DEFAULT_GLOBALID_STRATEGY`, Slice 1); no separate constant edit needed. `effective_globalid_strategy` records `"model"`, emitted slot is the model label. Truly landed.
5. **Strategy-aware filter validation** — `filters/base.py`: module-top `from ..types.relay import MODEL_LABEL_STRATEGIES` (line 44); `_target_definition_for` (line 179, returns the resolved owner/target definition, single-sited own-PK-vs-relation); `_accepted_globalid_type_names` (line 220, `model`→label / `type`→graphql-name / `type+model`→both / `callable`/`custom`/`None`→node-id-only); `_decode_and_validate_global_id` (line 250) branches on the accepted set; node-id extraction unchanged; `GlobalIDFilter` / `GlobalIDMultipleChoiceFilter` / `RelatedFilter` child filters all route through it. `filters/inputs.py:580` comment fix references the renamed helper. Truly landed.
6. **Test coverage** — `tests/types/test_relay_interfaces.py` + `tests/filters/test_base.py`: every named Slice-2 test present; both filter-rejection directions, node-id-only fallback per strategy, wrong-model rejection, relation + multi-value (`index`-suffixed) paths, override→`custom` recording, both-declared raise, non-`str` callable raise, audit raise + passing arrangements, the re-entrancy preservation, and the callable-setting arity/sync reuse all exercised. Truly landed.

No box was over-ticked (ticked without matching implementation); no box was silently left un-ticked; no remaining `- [ ]`, so no deferral reason is required.

### DRY check (this slice + Slice 1)

- **`MODEL_LABEL_STRATEGIES` is single-sourced.** Defined exactly once (`types/relay.py:380`), referenced by the encoder (relay.py:441), both predicates `_emits_model_label`/`_accepts_model_label_decode` (relay.py:390/403) which the finalizer audit consumes, and the filter (filters/base.py:243 via the module-top import). One frozenset object across the `filters → types` boundary (Worker 3 confirmed identity, not a copy). No parallel literal strategy set was introduced for the model-label membership.
- **Slice-1 reuse, not re-creation.** `_resolve_globalid_strategy` defined once (relay.py:323, Slice 1), called by the install step — not re-implemented. `STRING_GLOBALID_STRATEGIES` (the full valid-string set) + `DEFAULT_GLOBALID_STRATEGY` remain the Slice-1 base.py source of truth (a different set from `MODEL_LABEL_STRATEGIES` — the validation vocabulary vs the model-label-emitting subset; correctly distinct, not duplication). `_RELAY_RESOLVER_DEFAULTS` correctly does NOT gain `resolve_typename` (Decision 10).
- **`TYPE_NAME_STRATEGIES` note → Slice-3 planning input, NOT a Slice-2 defect.** Worker 3 flagged the bare tuple `("type", "type+model")` at `filters/base.py:245` (the graphql-name-acceptance membership). It appears exactly once today, so it is NOT presently duplicated and NOT a DRY violation. Slice 3's decode Step-2 enforcement will need the same "which strategies accept a type-name payload" notion; if Slice 3 re-types `{"type", "type+model"}`, the second site turns it into a parallel-literal defect. Dispositioned as a Slice-3 planning input (carried into worker-1 memory): introduce a sibling `TYPE_NAME_STRATEGIES` named membership at the `types/relay.py` source of truth when the decoder lands. Not blocking Slice-2 acceptance.

### Existing tests still pass (focused scope)

`uv run pytest tests/types/test_relay_interfaces.py tests/filters/test_base.py --no-cov` → **144 passed** (85 in `test_relay_interfaces.py`, 59 in `test_base.py`). No `--cov*` flag used (the explicit `--no-cov` opts out of `pytest.ini`'s auto-`--cov`). The `examples/fakeshop/test_query/` suite is the EXPECTED Slice-4 blast radius (spec Risks deferral) and was not run / not blocked on.

### Spec reconciliation

No spec edit made. The diff matches Decisions 3/4/9/10/13 as written (Worker 2 and Worker 3 both reported no spec gap). The spec's `Status:` / `## Slice checklist` boxes are the intentional contract record that stays unticked by design (spec line 5); per the dispatch contract I did NOT tick them. The spec header lines 1-5 still accurately describe the spec as an open build plan, so the per-spawn header re-verification is a no-op for this build (build progress lives in `build-031-...md`, not the spec). No status-line drift, no deleted-predecessor references.

### Summary

Slice 2 ships the **encode** half of the GlobalID-encoding feature: the strategy-parameterized `resolve_typename` injection at finalization Phase 2.5 (re-entrant-safe, `__func__`-gated to preserve consumer overrides as the fifth `custom` effective strategy), the four encoders (`model` / `type` / `type+model` / callable) sharing the single `MODEL_LABEL_STRATEGIES` source of truth, the `DjangoTypeDefinition.effective_globalid_strategy` recorded field (the load-bearing contract Slice 3 decode reads + the step-0 re-entrancy sentinel), the model-label-routing audit (multi-type models only), the package-default flip to `model`, and the co-landing strategy-aware `GlobalID` filter validation (Decision 13). 144 focused tests pass. The example-suite breakage is correctly deferred to Slice 4 (not silently fixed). DRY contract is genuinely single-sourced. **Status: `final-accepted`.**

### Spec changes made (Worker 1 only)

None. Slice 2 landed exactly as specced; no gap, conflict, or status-line drift required a spec edit. (No deferral reasons needed — every verbatim checklist box truly landed.)

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[feedback]: ../feedback.md
[glossary-configurationerror]: ../GLOSSARY.md#configurationerror
[glossary-finalize_django_types]: ../GLOSSARY.md#finalize_django_types
[glossary-metaprimary]: ../GLOSSARY.md#metaprimary
[glossary-relatedfilter]: ../GLOSSARY.md#relatedfilter

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[definition]: ../../django_strawberry_framework/types/definition.py
[filters-base]: ../../django_strawberry_framework/filters/base.py
[relay]: ../../django_strawberry_framework/types/relay.py

<!-- tests/ -->
[test-filters-base]: ../../tests/filters/test_base.py
[test-relay-interfaces]: ../../tests/types/test_relay_interfaces.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
