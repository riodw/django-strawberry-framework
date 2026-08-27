# Build: Slice 2 — the encode seam (strategy-parameterized `resolve_typename` injection + the four encoders + the default flip to `model` + strategy-aware `GlobalID` filter validation)

Spec reference: `docs/SPECS/spec-031-globalid_encoding-0_0_9.md` (Slice checklist lines 61-67; Decisions 3/4/9/10/13 lines 263-288, 343-408; Implementation plan Slice-2 row line 416; Test plan lines 454-495; Definition of done item 4 line 565)
Status: final-accepted

**Procedural closure** (`docs/builder/BUILD.md` `### Procedural-closure slices`, and the build plan's `## Dispatch rule for this cycle`): the CODE GAP list is empty and no source edit is judged worth a build cycle, so this is one combined Plan + Final-verification block. No Worker 2, no Worker 3.

This is a **residual reconciliation cycle** over already-shipped work (`DONE-031-0.0.9`, package now at `0.0.14`). The obligations are (1) the CODE GAP audit and (2) spec reconciliation where later cards changed what `031` landed. Code is the truth.

---

## Plan (Worker 1) + Final verification (Worker 1)

### DRY analysis

**Helper inventory checked.** Refreshed over the **whole package** via `scripts/review_inspect.py`'s symbol surface plus direct grep of `django_strawberry_framework/` for the shapes this slice contracts — `encode`, `typename`, `strategy`, `globalid`, `audit`, `accept`, `resolve_target`, `label_lower`, `graphql_type_name`. Relevant existing shapes found, all of them **already** the shipped single-siting rather than candidates for new extraction:

- `types/relay.py::MODEL_LABEL_STRATEGIES` / `::TYPE_NAME_STRATEGIES` — the two payload-shape frozensets. Read by the encoder, the model-label-routing audit, the decoder's Step-2 enforcement, and (imported across the `filters -> types` acyclic direction) `filters/base.py`. The `{"model","type+model"}` / `{"type","type+model"}` literals are typed once.
- `types/relay.py::_emits_model_label` / `::_accepts_model_label_decode` / `::_accepts_type_name_decode` — named predicates over those two frozensets; the emit/accept split is deliberate naming, not duplication (both memberships coincide today, documented as splittable if they ever diverge).
- `filters/base.py::FRAMEWORK_GLOBALID_STRATEGIES` — **derived** (`MODEL_LABEL_STRATEGIES | TYPE_NAME_STRATEGIES`) rather than re-typed, so "validatable on a filter" cannot drift from "emitted by the encoder".
- `filters/base.py::resolve_globalid_target_definition` — the own-PK-vs-relation (and multi-hop) target resolution, factored out of the runtime `_target_definition_for` accessor so the build-time audit and the request-time backstop resolve the *same* definition.
- `types/finalizer.py::_format_model_label_routing_error` / `::_format_globalid_encode_only_filter_error` — the two Slice-2 error strings hoisted to module top beside `_format_ambiguity_error`, keeping the finalize-time strings grep-stable.

**New helpers justified:** none. This pass writes no source.

**Duplication risk avoided:** none introduced; the pass touches two Markdown files.

### Implementation steps

This pass performs the audit and the reconciliation only. No source, no tests.

1. Re-derive every contracted Slice-2 surface at HEAD against the spec's stated shape and behavior (not merely its symbol name) — `### CODE GAP audit` below.
2. Re-derive every test named in both Slice-2 `## Test plan` blocks, and read each body against the sentence the spec files it under.
3. Enumerate shipped Slice-2 behavior with **no** owning spec sentence, and decide per case.
4. Rewrite the spec to state the current contract directly; append the reasoning to the rationale companion under the owning Decision.
5. Run the closing verification checks.

### Test additions / updates

None. `### Final verification checks run` below records the focused run confirming the contracted rows are green at HEAD.

### Implementation discretion items

None; no Worker 2 pass.

### Spec slice checklist (verbatim)

Copied verbatim from `docs/SPECS/spec-031-globalid_encoding-0_0_9.md` `## Slice checklist`, Slice 2. Boxes are ticked by this pass because the slice **shipped** — each tick is the CODE GAP audit's verdict, evidenced below.

- [x] Slice 2: the encode seam — strategy-parameterized `resolve_typename` injection + the four encoders + the default flip to `model` (per [Decision 3](#decision-3--the-encode-seam-a-strategy-parameterized-resolve_typename-default) / [Decision 4](#decision-4--four-strategies-model-type-typemodel-callable-and-an-unchanged-node_id-portion) / [Decision 9](#decision-9--changing-the-default-to-model-is-a-breaking-wire-format-change-acceptable-pre-100) / [Decision 10](#decision-10--resolve_typename-injection-via-the-__func__-identity-test-at-phase-25))
  - [x] [`django_strawberry_framework/types/relay.py`][relay] gains an `encode_typename(definition, strategy, type_cls, root)` internal helper that returns the type-name slot for the resolved strategy: `model` → `definition.model._meta.label_lower` (`"products.item"`); `type` → the GraphQL type name ([`definition.graphql_type_name`][definition], matching Strawberry's `info.path.typename` default); `type+model` → the model label (emit model-anchored, accept both on decode, per [Decision 4](#decision-4--four-strategies-model-type-typemodel-callable-and-an-unchanged-node_id-portion)); callable → the consumer callable's return (signature `(type_cls, model, root) -> str`, sync — it never receives `node_id` and never receives `info`; purity is a documented consumer obligation, per [Decision 4](#decision-4--four-strategies-model-type-typemodel-callable-and-an-unchanged-node_id-portion)).
  - [x] An `install_globalid_typename_resolver(type_cls, definition)` step (called from [`finalize_django_types`][glossary-finalize_django_types] Phase 2.5, alongside `install_relay_node_resolvers`) is **re-entrant-safe**: if `definition.effective_globalid_strategy is not None` it skips (the type was processed in a prior partial run — [Decision 10](#decision-10--resolve_typename-injection-via-the-__func__-identity-test-at-phase-25) step 0). Otherwise it runs the `existing.__func__ is relay.Node.resolve_typename.__func__` override test (MRO-aware) **before** installing: a consumer override → effective strategy **`custom`**, install nothing (and if the type also declares an explicit `Meta.globalid_strategy`, raise [`ConfigurationError`][glossary-configurationerror] — the both-declared conflict); no override → resolve via `_resolve_globalid_strategy`, install the package closure for `model` / `type+model` / `callable` (the `callable` closure raises [`ConfigurationError`][glossary-configurationerror] on a non-`str` / empty return; the callable's arity / sync-ness were already validated at type creation), leave Strawberry's default for `type`. It records the resolved effective strategy (`model` / `type` / `type+model` / `callable` / `custom`) in the named field **`effective_globalid_strategy: str | None = None`** on the [`DjangoTypeDefinition`][definition] (distinct from the Slice-1 raw `globalid_strategy` slot), which decode reads and which also serves as the step-0 re-entrancy sentinel.
  - [x] A Phase-2.5 **model-label-routing audit** (parallel to `_audit_primary_ambiguity`, after every type's effective strategy is recorded): for each model, if any registered type's effective strategy emits model-label IDs (`model` / `type+model`), the model's [`Meta.primary`][glossary-metaprimary] type's effective strategy must accept model-label decode (`model` / `type+model`), else [`ConfigurationError`][glossary-configurationerror] naming the model, the emitter, and the primary's strategy ([Decision 8](#decision-8--decode-routes-through-djangos-app-registry-then-the-framework-registry-to-the-primary-type)).
  - [x] Flip the **package default** from the (DONE-015) type-anchored `GlobalID` to `model`: a Relay-Node-shaped type with no `Meta.globalid_strategy` and no `RELAY_GLOBALID_STRATEGY` setting now emits the model-label payload (per [Decision 9](#decision-9--changing-the-default-to-model-is-a-breaking-wire-format-change-acceptable-pre-100)).
  - [x] **Make `GlobalID` filter validation strategy-aware (co-lands with the flip — [Decision 13](#decision-13--globalid-filter-validation-is-strategy-aware)).** [`filters/base.py::_decode_and_validate_global_id`][filters-base] reads the resolved owner/target definition's recorded `effective_globalid_strategy` and accepts the matching payload shape — `model` → model label, `type` → `graphql_type_name`, `type+model` → both — so an emitted model-label ID round-trips through `GlobalIDFilter` / `GlobalIDMultipleChoiceFilter` / [`RelatedFilter`][glossary-relatedfilter]-expanded child filters instead of being rejected against the old GraphQL type name. A `callable` / `custom` (or known-`None`-effective-strategy) target **fails closed**: a Phase-2.5 filterset-binding audit [`types/finalizer.py::_audit_globalid_filter_strategies`][finalizer] (run inside `_bind_filtersets`) raises [`ConfigurationError`][glossary-configurationerror] at schema build, and [`filters/base.py::_decode_and_validate_global_id`][filters-base] raises a runtime `GraphQLError` (`extensions.code = "GLOBALID_UNVALIDATABLE"`) as the hand-built-filterset backstop; only the pre-existing unbound-owner / unresolvable-target `None`-expected case keeps the node-id-only path. Package coverage in [`tests/filters/test_base.py`][test-filters-base] (own-PK, relation, and multi-value round-trips under each framework strategy; wrong-model/type rejection; the encode-only fail-closed reject; the retained unbound-owner node-id-only path) and [`tests/filters/test_finalizer.py`][test-filters-finalizer] (the Phase-2.5 audit rejections).
  - [x] Package coverage: [`tests/types/test_relay_interfaces.py`][test-relay-interfaces] — each strategy's emitted type-name slot; the consumer-`resolve_typename`-override preservation **and** its `custom` effective-strategy recording; the both-declared (override + `Meta.globalid_strategy`) `ConfigurationError`; the non-`str` callable-return `ConfigurationError`; the model-label-routing audit `ConfigurationError` (a `type`-primary with a `model`-secondary, scoped to multi-type models); **a re-entrancy test — a finalize whose Phase-2.5 audit raises, then a re-run, leaves the recorded effective strategy intact (no `model`→`custom` misclassification)**; the default-flip (no override → `model`); the `type`-strategy reproduces the pre-`0.0.9` GraphQL-type-name payload.

Two boxes above are ticked against text this pass then **corrected in the spec** (the verbatim copy is deliberately the pre-edit text, so the audit is legible against what the slice was dispatched with):

- box 2's `install_globalid_typename_resolver(type_cls, definition)` — the contract landed at the three-arg form Decision 10 already specified; see CG-2 and spec change S1.
- box 5's "known-`None`-effective-strategy target … rejected at schema build" — the contract landed with the known-`None` rejection at **request time only**; see CG-8 and spec change S3.

### CODE GAP audit

Every surface Slice 2 contracts, re-derived at HEAD (`5ebcfe9c`). Worker 0's pre-verified name list was **confirmed, not accepted**: each entry was read for shape and behavior against the spec sentence, not matched on symbol name.

**CODE GAP list: EMPTY.** Nothing the spec's Slice 2 planned was skipped, dropped, or forgotten. Every contracted surface exists, and every contracted behavior is the shipped behavior. Stated explicitly because an empty list is a valid outcome of this cycle, not a pass that found nothing to look at.

| # | Contracted surface (spec site) | Verdict | Evidence |
|---|---|---|---|
| CG-1 | `encode_typename(definition, strategy, type_cls, root)`, four branches (checklist box 1, Decision 4) | **present, shape matches** | `django_strawberry_framework/types/relay.py::encode_typename` — callable branch first, then `strategy in MODEL_LABEL_STRATEGIES` → `definition.model._meta.label_lower`, else `definition.graphql_type_name`. Positional order is exactly `(definition, strategy, type_cls, root)`. |
| CG-2 | `install_globalid_typename_resolver`, Phase-2.5 install step (checklist box 2, Decision 10, DoD 4) | **present; spec contradicted itself on the signature — shipped is 3-arg** | `django_strawberry_framework/types/relay.py::install_globalid_typename_resolver(type_cls, definition, globalid_setting)`. The Slice-2 checklist spelled two args; Decision 10 spelled three. Shipped and Decision 10 agree. Spec change S1. |
| CG-3 | Step 0 re-entrancy guard (Decision 10 step 0) | **present, behavior matches** | `types/relay.py::install_globalid_typename_resolver` #"if definition.effective_globalid_strategy is not None" — a bare early `return` before override detection, recording, and install. Pinned by `tests/types/test_relay_interfaces.py::test_finalize_rerun_after_audit_raise_preserves_recorded_strategy`, which raises the routing audit, captures both recordings, re-runs bare, and asserts both survive. |
| CG-4 | Step 1 override test **with** the `_FRAMEWORK_CLOSURE_MARKER` exclusion (Decision 10 step 1) | **present, behavior matches** | `types/relay.py::_FRAMEWORK_CLOSURE_MARKER` (stamped on the plain function in `::_install_typename_closure` **before** the `classmethod(...)` wrap, so it survives `__func__` retrieval); `::_consumer_overrode_resolve_typename` returns `False` for a marked function and for an absent `__func__`, else compares against `relay.Node.resolve_typename.__func__`. Both-declared conflict raises before the `custom` recording. |
| CG-5 | Step 2 `type` **shadow-install** (Decision 10 step 2) | **present; the spec's exclusivity claim about it is falsified** | `types/relay.py::install_globalid_typename_resolver` #"if classification != \"type\" or _inherits_framework_closure(type_cls)" and `::_inherits_framework_closure`. The install logic is exactly as specified. The spec's claim that the shadow-install is "the one live production path through `encode_typename`'s `type` branch" is **not** true at HEAD: `django_strawberry_framework/testing/relay.py::global_id_for` (shipped by `DONE-032-0.0.9`) calls `encode_typename(definition, strategy, type_cls, None)` directly with the recorded strategy, reaching the `type` branch with no installed closure. Not a code gap — a spec census claim a later card falsified. Spec change S2. |
| CG-6 | `effective_globalid_strategy: str \| None = None` on the definition (checklist box 2, Decision 10 step 3, DoD 4) | **present, exact field name and default** | `django_strawberry_framework/types/definition.py::DjangoTypeDefinition` #"effective_globalid_strategy: str \| None = None", declared among the defaulted fields directly after the raw `globalid_strategy` slot. |
| CG-7 | Model-label-routing audit, scoped to `registry.models_with_multiple_types()`, running **after** every type's strategy is recorded (checklist box 3, Decisions 8/10, DoD 4) | **present; both scope and ordering confirmed, not assumed** | `django_strawberry_framework/types/finalizer.py::_audit_model_label_routing` + `::_first_model_label_emitter` + `::_format_model_label_routing_error`. Scope: `finalize_django_types` materializes `multi_type_models = tuple(registry.models_with_multiple_types())` once and passes the **same** tuple to Phase-1 `_audit_primary_ambiguity` and this audit. Ordering: the call site sits after the whole `for type_cls, definition in registry.iter_definitions()` Relay loop (which is where `install_globalid_typename_resolver` runs) and before Phase 3 — so it reads complete data and a raise leaves every type `finalized = False`. |
| CG-8 | `_audit_globalid_filter_strategies` + `_format_globalid_encode_only_filter_error`, run inside `_bind_filtersets` (checklist box 5, Decision 13, DoD 4) | **present; its rejection set is narrower than the spec claimed** | `types/finalizer.py::_audit_globalid_filter_strategies`, reached via `::_audit_filterset_subpass_2_5` (second of two, after `_audit_unregistered_related_filter_targets`), which `_bind_filtersets` runs. It rejects `strategy in ENCODE_ONLY_GLOBALID_STRATEGIES` — the two names `callable` / `custom` — so a **known-`None`** strategy target is *not* a build-time error. Five spec sites said it was. Not a code gap: the shipped split is correct (a build-time raise on `None` would reject a `GlobalID` filter against any not-yet-Relay-shaped target, `None` also being the ordinary pre-install state). Spec change S3. |
| CG-9 | `FRAMEWORK_GLOBALID_STRATEGIES` / `ENCODE_ONLY_GLOBALID_STRATEGIES` (Decision 13) | **present, and the derivation is the DRY win** | `django_strawberry_framework/filters/base.py` #"FRAMEWORK_GLOBALID_STRATEGIES = MODEL_LABEL_STRATEGIES \| TYPE_NAME_STRATEGIES" — derived from the encoder's own memberships, not re-typed; `#"ENCODE_ONLY_GLOBALID_STRATEGIES = frozenset({\"callable\", \"custom\"})"` is a literal because the names appear in the reject message. |
| CG-10 | `resolve_globalid_target_definition` (Decision 13's audit, implicitly) | **present; the spec did not name it** | `django_strawberry_framework/filters/base.py::resolve_globalid_target_definition` — own-PK-vs-relation and multi-hop resolution, called by both `::_target_definition_for` (runtime) and `types/finalizer.py::_audit_globalid_filter_strategies` (build time), so the two guards cannot resolve different targets. Spec change S4 names it. |
| CG-11 | `_accepted_globalid_type_names` per-strategy accept sets (Decision 13) | **present, behavior matches** | `django_strawberry_framework/filters/base.py::_accepted_globalid_type_names` — `None` definition → `None`; `MODEL_LABEL_STRATEGIES` adds `model._meta.label_lower`; `TYPE_NAME_STRATEGIES` adds `graphql_type_name`; `accepted or None` is a documented defensive belt reached only if the fail-closed guard above it were bypassed. |
| CG-12 | `_decode_and_validate_global_id` strategy-aware validation + `GLOBALID_UNVALIDATABLE` backstop + retained unbound-owner path (checklist box 5, Decision 13, DoD 4) | **present, behavior matches** | `django_strawberry_framework/filters/base.py::_decode_and_validate_global_id` — the fail-closed guard is spelled `if strategy not in FRAMEWORK_GLOBALID_STRATEGIES` (the complement of the audit's predicate, hence its wider set), branching the message on encode-only vs known-`None` and raising with `extensions={"code": "GLOBALID_UNVALIDATABLE"}`; the accepted-set mismatch below it raises the spec's exact `GlobalID type mismatch: filter expects <expected> but received <actual>` string; `definition is None` skips the guard entirely. |
| CG-13 | Default flip to `model` (checklist box 4, Decision 9, DoD 4) | **present** | `types/relay.py::_resolve_globalid_strategy` falls through to `types/base.py::DEFAULT_GLOBALID_STRATEGY`; pinned end-to-end by `tests/types/test_relay_interfaces.py::test_globalid_default_is_model` (recording **and** emitted slot) and `::test_globalid_model_strategy_emits_model_label`. |
| CG-14 | Every test named in both Slice-2 `## Test plan` blocks | **all present and asserting what the spec says, with one name divergence** | See `#### Test-plan re-derivation` below. |

#### Two Worker-0 hand-offs that did not survive re-derivation

Recorded because a pre-verified claim is a claim (`docs/builder/BUILD.md` `## Claims are proven mechanically, never accepted on prose`), and both would have produced a wrong spec edit if accepted:

- **"`filters/base.py` mismatch and empty-slot rejections now carry `extensions={"code": "GLOBALID_INVALID"}`; the spec still quotes the bare `GraphQLError(...)` string."** Half wrong, and the half that matters is wrong. The **mismatch** rejection is deliberately **code-less** — `filters/base.py::_decode_and_validate_global_id` raises the mismatch `GraphQLError` with no `extensions` at all, and the module comment above it says so explicitly (#"keeps its own (code-less) mismatch error"). What *does* carry `GLOBALID_INVALID` is the malformed-payload, empty-`node_id`, and pk-coercion rejections — none of which any spec-031 sentence describes or claims to describe (they are `spec-027` / later contracts; Decision 13 scopes itself to the `type_name` slot and says the `node_id` extraction is unchanged). **No spec edit made.** Had the hand-off been accepted, the spec would now assert a code the shipped mismatch error does not carry.
- **"`## Current state` describes `_expected_global_id_type_name` as the live helper."** True sentence, **licensed dated observation, not drift** — and the prompt's own instruction was to determine which. Verified read-only: `git show b1f82f0e:django_strawberry_framework/filters/base.py > <scratch outside the repo>` (b1f82f0e is the commit that created the spec) contains `def _expected_global_id_type_name(filter_instance: Filter) -> str | None:` at that revision, and the same file at that revision already raised the identical `GlobalID type mismatch: filter expects {expected} but received {decoded.type_name}` string. The spec's opener licenses `## Current state` as "the repo as of this spec's authoring, before the build". **No spec edit made**; recorded in the rationale companion under Decision 13 so the next reader does not re-flag it.

#### Test-plan re-derivation

Every name in the Slice-2 `tests/types/test_relay_interfaces.py` block, the Slice-2 `tests/filters/test_base.py` block, and the `tests/filters/test_finalizer.py` sub-block, read against the sentence the spec files it under:

- `tests/types/test_relay_interfaces.py` — all thirteen named rows present (`test_globalid_model_strategy_emits_model_label`, `..._type_strategy_emits_graphql_type_name`, `..._type_plus_model_emits_model_label`, `..._callable_strategy_emits_custom`, `..._callable_non_string_return_raises`, `test_consumer_resolve_typename_override_preserved_and_recorded_custom`, `test_resolve_typename_override_plus_meta_strategy_raises`, `test_model_label_routing_audit_rejects_type_primary_with_model_secondary`, `test_finalize_rerun_after_audit_raise_preserves_recorded_strategy`, `test_globalid_default_is_model`, `test_callable_setting_well_formed_accepted` / `..._wrong_arity_raises` / `..._async_raises`). Bodies checked, not just names: the `type` row asserts `CategoryNode.resolve_typename.__func__ is relay.Node.resolve_typename.__func__` (i.e. *nothing installed*, which is what "byte-identical to pre-`0.0.9`" actually means, rather than merely comparing an emitted string); the both-declared row's negative twin exists as a separate test; the audit row asserts the model, the emitter, **and** the primary's strategy appear in the message; the re-entrancy row differences the recordings across a raise and a bare re-run; the two callable-setting rejection rows both `match="RELAY_GLOBALID_STRATEGY"`, i.e. the spec's "naming the setting".
- `tests/filters/test_base.py` — eight of nine named rows present under the spec's names. **`test_related_filter_and_multi_value_strategy_aware` does not exist**; its contract landed split across `tests/filters/test_base.py::test_related_filter_relation_branch_strategy_aware` (relation branch validates against the *target*'s strategy — target model label accepted, target type name rejected) and `::test_multi_value_filter_strategy_aware_indexes_rejection` (multi-value routes every element through the same check, decoding a good batch through to the upstream filter and naming the bad element's index). A test-plan naming divergence, not a code gap. Spec change S5.
- `tests/filters/test_finalizer.py` — all three named rows present, asserting the filterset name, `encode-only`, and the strategy name in the message; the skip row proves an unresolvable target is a no-op skip and finalization *succeeds*.

#### Shipped behavior with no owning spec sentence

Treated as findings of the same class as a missing surface. Decided per case; four contracted, one deliberately not.

1. **`types/relay.py::encode_typename`'s `str.__str__` normalization of a callable return.** Decision 4 and Decision 10 contracted one per-call check, a non-empty-`str` guard. Shipped code adds a second step: the validated return is re-read through the base `str.__str__` descriptor, and the emptiness check runs on the *normalized* value. Closes a `str` subclass that passes `isinstance` and then overrides `__str__` / `__format__` once Strawberry's base64 encoder reads it. Pinned by `tests/types/test_relay_interfaces.py::test_globalid_callable_string_subclass_is_normalized`. **Contracted** (spec change S6) — it is a boundary, not an implementation detail.
2. **`types/finalizer.py::_warn_model_label_secondary_collapse`.** A shipped finalization warning nothing in the spec contracted (handed forward by Slice 1; confirmed by `grep -i 'collapse\|warn'` over the spec returning zero hits before this pass). It warns when a non-primary registered type also emits model-label IDs, whose `GlobalID`s decode through `registry.get(model)` to the primary and so refetch AS the primary. Pinned by `::test_model_label_secondary_collapse_warns_and_routes_to_primary` and `::test_model_label_no_collapse_warning_when_secondary_is_type`. **Contracted** (spec change S7) — it is user-visible behavior on the card's own headline default flip.
3. **`_format_model_label_routing_error`'s two-branch remediation.** The fix sentence branches on whether the offending primary's recorded strategy is a string or `None`, because `Meta.globalid_strategy` is rejected on a non-Relay type and the default fix would otherwise prescribe an impossible one. Pinned by `::test_routing_audit_non_relay_primary_remediation_names_relay_shape`. **Contracted** (folded into spec change S7).
4. **The `_FRAMEWORK_CLOSURE_MARKER` / shadow-install test cohort** (`test_concrete_relay_child_of_concrete_parent_records_own_strategy`, `test_concrete_relay_child_with_meta_strategy_finalizes_cleanly`, `test_type_strategy_child_shadows_inherited_framework_closure`, `test_routing_audit_sees_child_true_recorded_strategy`, `test_plain_function_resolve_typename_is_not_classified_override`) plus `test_resolve_typename_override_plus_setting_does_not_raise`. The *behavior* is fully contracted by Decision 10 steps 1-2; only the `## Test plan` was short of the rows. **Named in the test plan** (spec change S8). `test_plain_function_resolve_typename_is_not_classified_override` also pins a semantic Decision 10 left implicit — a plain function assigned as `resolve_typename` carries no `__func__` and is therefore not an override — so its line states that.
5. **`_first_model_label_emitter` / `_audit_model_label_routing`'s "registered type has no `DjangoTypeDefinition`" raises.** Internal-consistency guards against a registry state the finalizer's own invariants exclude. **Not contracted**: they assert an invariant rather than offer a consumer contract, and giving them spec sentences would invite a reader to treat an impossible state as a supported one. Recorded here for `### Deferred work catalog` visibility only.
6. **`test_encode_typename_helper_dispatch`.** A unit-level mirror of the four encoder rows the checklist already contracts. **Not a finding**; no edit.

### Spec changes made (Worker 1 only)

All in `docs/SPECS/spec-031-globalid_encoding-0_0_9.md`; line numbers are post-edit. The spec never narrates its own history — every change states the current contract directly, and the reasoning is appended to `docs/SPECS/appx/spec-031-globalid_encoding-0_0_9-rationale.md` under the owning Decision (`### Rationale companion entries appended`).

| # | Spec site (post-edit lines) | Change | Reason |
|---|---|---|---|
| S1 | 63 (Slice-2 checklist box 2) | `install_globalid_typename_resolver(type_cls, definition)` → `(type_cls, definition, globalid_setting)` | The spec contradicted itself; shipped `types/relay.py::install_globalid_typename_resolver` and Decision 10 (line 365) both carry the three-arg form. Slice 2. |
| S2 | 374 (Decision 10 step 2) | "This shadow-install is the one live production path through `encode_typename`'s `type` branch" → the shadow-install is the only way a `type`-strategy type carries a framework closure, hence the only route into that branch during `id` resolution; names `testing/relay.py::global_id_for` as the other direct caller | The exclusivity claim was falsified by `DONE-032-0.0.9` shipping a second caller. CG-5. Slice 2. |
| S3 | 66, 234, 403, 433, 565 (checklist box 5, `## Error shapes`, Decision 13, `## Edge cases`, DoD 4) | Five sites: a known-`None`-effective-strategy target is rejected by the **runtime** backstop only, never at schema build; the build-time audit keys on the two encode-only names | CG-8: shipped `_audit_globalid_filter_strategies` rejects `ENCODE_ONLY_GLOBALID_STRATEGIES` only. Five homes, because the spec states each contract in five and a partial fix is the recurring defect. Slice 2. |
| S4 | 66, 403 (checklist box 5, Decision 13) | Name `filters/base.py::resolve_globalid_target_definition` as the shared target resolver the build-time audit and the request-time backstop both use | CG-10; the single-siting is what makes the two guards agree, and an unnamed shared shape drifts. Slice 2. |
| S5 | 485-486 (`## Test plan`, Slice-2 filters block) | `test_related_filter_and_multi_value_strategy_aware` → `test_related_filter_relation_branch_strategy_aware` + `test_multi_value_filter_strategy_aware_indexes_rejection`, each with what it actually asserts | The named test does not exist; the contract shipped split across two. Slice 2. |
| S6 | 281 (Decision 4, callable bullet) | State the `str.__str__` normalization of the callable return and that the emptiness check runs on the normalized value | Unowned shipped boundary, finding 1 above. Slice 2. |
| S7 | 64, 376, 416, 565 (checklist box 3, Decision 10's audit paragraph, Implementation-plan Slice-2 row, DoD 4) | State `_warn_model_label_secondary_collapse` — what it warns on, that it never raises, what the warning names — and `_format_model_label_routing_error`'s two-branch remediation. Checklist box 3's "for each model" also tightened to "for each multi-type model" to match the shipped scope | Unowned shipped behavior, findings 2 and 3 above. Slice 2. |
| S8 | 466-473 (`## Test plan`, Slice-2 relay block) | Add eight rows: the str-subclass test, the two collapse tests, the non-Relay-primary remediation test, the three marker/inheritance tests, the shadow-install test, the plain-function test, and the override-plus-setting negative | Finding 4: the behavior was contracted, the test plan was not. Slice 2. |

No deferral reason is owed for any `### Spec slice checklist (verbatim)` box: all six are `- [x]`.

**Out-of-fence surfaces left alone, deliberately.** `docs/GLOSSARY.md`, `docs/TREE.md`, `docs/README.md`, `TODAY.md`, `README.md`, `CHANGELOG.md`, `KANBAN.md`/`.html`, `examples/fakeshop/db.sqlite3`, and the spec's `-terms.csv` are out of fence for the whole cycle; Slice 5 audits them. No source or test file was edited by this pass — Worker 1 never edits source.

### Rationale companion entries appended

Appended to `docs/SPECS/appx/spec-031-globalid_encoding-0_0_9-rationale.md`, append-only, each under its Decision's `### Changes this Decision underwent` in Slice 1's established `**Post-ship:**` bullet convention:

- **Decision 4** — "`isinstance(result, str)` is not a `str`." Why the normalization exists, the `str`-subclass class it closes, and the principle it shares with Slice 1's un-inspectable-callable rule: *a validated value must be inert by the time it leaves the validator, not merely well-typed at the moment it is inspected.* Names the pinning tests and the spec sites now stating it.
- **Decision 10** — two bullets. (a) "'the one live production path' was an exclusivity claim, and `032` falsified it", with the general shape: *an exclusivity claim about who reaches a code path is a claim about the whole package at one moment; a later card adding a caller falsifies it without touching the file the claim is about. A membership claim survives, a census claim does not.* (b) "the collapse warning had no owning sentence" — what it warns on, why the hard audit permits the arrangement, why it is nonetheless a regression against the pre-`0.0.9` default, and the `_format_model_label_routing_error` remediation branch recorded alongside it.
- **Decision 13** — two bullets. (a) "'rejected the same way' collapsed two different sites into one" — the audit keys on `ENCODE_ONLY_GLOBALID_STRATEGIES`, the backstop on the complement `not in FRAMEWORK_GLOBALID_STRATEGIES`, why the shipped split is right, the five sites corrected, and the general shape: *"the same way" is a claim about two guards' predicates, and predicates written from opposite directions are exactly where it is wrong.* (b) "the audit and the runtime path share one target resolver", which also records that `## Current state`'s `_expected_global_id_type_name` sentence is a verified true dated observation and is deliberately untouched.

### Static inspection helper

**Not run, recorded skip.** `docs/builder/BUILD.md` `### When to run the helper during build` triggers it when *the plan adds logic* to a file under `types/`. This plan adds no logic anywhere: it writes two Markdown files and no `.py`. Had a CODE GAP forced a Worker 2 pass against `types/` or `optimizer/`, it would have run with `--output-dir docs/shadow`. (Worker 0's pre-flight step 2 already exercised it against `types/relay.py`, exit 0.)

### Plan declarations

- **Hot-path declaration:** `none`. No production code is written by this pass, so neither the `resolve_typename` install closure (per-node `id` resolution) nor `_decode_and_validate_global_id` (per filter value) is touched. Deliberate, not silence.
- **Floor-verification scope:** `none`. `types/relay.py`, `types/finalizer.py`, `types/definition.py`, and `filters/base.py` are Strawberry type-construction seams and would have required a focused `tests/types/` + `tests/filters/` floor run had this pass landed in them; it does not. Deliberate, not silence.
- **Ownership partition:** `none; sequential slices`.
- **Boundary count (split trigger):** zero new boundaries. No split question to answer beyond recording the count.

### Final verification checks run

- `uv run pytest tests/types/test_relay_interfaces.py tests/filters/test_base.py tests/filters/test_finalizer.py tests/types/test_finalizer.py tests/testing/test_relay.py --no-cov -q` → **308 passed**, 8 workers, 5.36s. No `--cov*` flag.
- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-031-globalid_encoding-0_0_9.md` → **`OK: 31 terms`**, unchanged from pre-flight.
- In-page anchors and reference-style link definitions, both files, after the edits: every `](#anchor)` resolves to a heading slug; no dangling reference-style link; no unused link definition. Spec `161,327` bytes (from `155,021`); rationale companion `95,578` bytes (from `89,002`).
- `git status --short` re-read at the start of this pass: the concurrent session had already committed once mid-cycle (HEAD moved `bc4ed00a` → `5ebcfe9c`) and its four baseline-dirty paths were absorbed by that commit. The tree now carries only this cycle's own files: `docs/SPECS/spec-031-globalid_encoding-0_0_9.md` (M) plus the untracked rationale companion, the build plan, and the slice artifacts. No baseline-dirty file was edited or reverted.
- No `git stash` / `git checkout` / `git restore` / `git worktree` was used. The one HEAD-history read (`git show b1f82f0e:…`) wrote to a scratch path outside the repo.

### Worker 2 dispatch

**Not owed.** The CODE GAP list is empty and no source edit is judged worth a build cycle. One source-side item is deferred rather than dispatched — see below.

### Deferred to `### Deferred work catalog` (for `bld-031-final.md`)

- **Three stale `.py` docstring/comment clauses, all comment-only, all in the maintainer's fence but outside Worker 1's.** Batched deliberately so a future pass fixes them in one change: (a) `django_strawberry_framework/types/definition.py::DjangoTypeDefinition` invariants docstring #"the filter falls back to node-id-only validation" — false since the `0.0.14` fail-closed hardening; shipped `filters/base.py::_decode_and_validate_global_id` fails closed on a known `None`, and the spec's Decision 13 was already right (handed forward by Slice 1); (b) `django_strawberry_framework/types/relay.py::encode_typename` docstring #"so this branch is the live implementation for exactly that shape" and (c) `::_install_typename_closure` docstring — both carry the same exclusivity claim about the `type` branch that CG-5 falsified in the spec. **Judged not worth a full Worker 2 → Worker 3 cycle** (`### Isolation is non-waivable` makes even a one-line comment fix a two-spawn cycle, and the spec now states the correct contract in every home). Nothing behavioral rests on them, and (a) is contradicted in the same file by the adjacent `filters/base.py::_accepted_globalid_type_names` docstring, which is correct.
- **`_first_model_label_emitter` / `_audit_model_label_routing` no-definition raises** are shipped internal-consistency guards with no spec sentence, deliberately left uncontracted (finding 5 above).

### Summary

Slice 2 shipped complete. Every surface the spec's largest slice contracts — the four encoders, the three-arg Phase-2.5 install with its re-entrancy guard, framework-closure exclusion and `type` shadow-install, the recorded `effective_globalid_strategy` field, the model-label-routing audit, the default flip, and the whole strategy-aware `GlobalID` filter stack across `filters/base.py` and `types/finalizer.py` — exists at HEAD, behaves as specified, and is pinned by the named tests. **CODE GAP list empty.** Eight spec changes reconcile the spec to the shipped code: one self-contradicted signature, one exclusivity claim `DONE-032` falsified, one wrong rejection site corrected across five homes, one test-plan name divergence, and four unowned shipped behaviors now contracted. Two of Worker 0's three handed divergences did not survive re-derivation and were deliberately **not** written into the spec.

### Final status

`final-accepted`.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

[glossary-configurationerror]: ../GLOSSARY.md#configurationerror
[glossary-finalize_django_types]: ../GLOSSARY.md#finalize_django_types
[glossary-metaprimary]: ../GLOSSARY.md#metaprimary
[glossary-relatedfilter]: ../GLOSSARY.md#relatedfilter

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

[definition]: ../../django_strawberry_framework/types/definition.py
[filters-base]: ../../django_strawberry_framework/filters/base.py
[finalizer]: ../../django_strawberry_framework/types/finalizer.py
[relay]: ../../django_strawberry_framework/types/relay.py

<!-- tests/ -->

[test-filters-base]: ../../tests/filters/test_base.py
[test-filters-finalizer]: ../../tests/filters/test_finalizer.py
[test-relay-interfaces]: ../../tests/types/test_relay_interfaces.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
