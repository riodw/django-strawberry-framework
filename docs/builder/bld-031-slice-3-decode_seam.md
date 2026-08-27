# Build: Slice 3 — the decode seam (`decode_global_id` resolve-then-enforce dispatch + `registry.definition_for_graphql_name` + encoder/decoder symmetry + transitional `type+model`)

Spec reference: `docs/SPECS/spec-031-globalid_encoding-0_0_9.md` (Slice checklist lines 68-72; Decision 8 lines 315-341; Decision 11 lines 381-387; Decode-dispatch sketch lines 215-225; Error shapes lines 227-244; Implementation plan Slice-3 row line 418; Test plan lines 494-516; Definition of done item 5 line 580)
Status: final-accepted

**Procedural closure** (`docs/builder/BUILD.md` `### Procedural-closure slices`, and the build plan's `## Dispatch rule for this cycle`): the CODE GAP list is empty and no source edit is judged worth a build cycle, so this is one combined Plan + Final-verification block. No Worker 2, no Worker 3.

This is a **residual reconciliation cycle** over already-shipped work (`DONE-031-0.0.9`, package now at `0.0.14`). The obligations are (1) the CODE GAP audit and (2) spec reconciliation where later cards changed what `031` landed. Code is the truth.

---

## Plan (Worker 1) + Final verification (Worker 1)

### DRY analysis

**Helper inventory checked.** Refreshed over the **whole package** (`django_strawberry_framework/`, not just `utils/`) by grepping the shapes this slice contracts — `decode`, `graphql_name`, `graphql_type_name`, `get_model`, `label`, `accepts`, `strategy`, `_safe_`, `from_id` — and opening every hit. Relevant existing shapes, all of them already the shipped single-siting rather than candidates for new extraction:

- `django_strawberry_framework/types/relay.py::MODEL_LABEL_STRATEGIES` / `::TYPE_NAME_STRATEGIES` — the two payload-shape frozensets. Step-2 enforcement reads them through `::_accepts_model_label_decode` / `::_accepts_type_name_decode`; the finalization audit reads the same `MODEL_LABEL_STRATEGIES` through `::_emits_model_label`; `django_strawberry_framework/filters/base.py` imports both across the acyclic `filters -> types` direction. Four consumers, two literals, typed once.
- `django_strawberry_framework/exceptions.py::_safe_type_name` / `::_safe_arg_repr` — the shared hostile-value renderers. `decode_global_id` uses both for its input-gate, malformed-input, and empty-slot diagnostics rather than re-implementing containment locally, the same reuse Decision 6's typo guard makes.
- `django_strawberry_framework/registry.py::TypeRegistry.get` / `::get_definition` / `::iter_definitions` — the pre-existing routing surface Decision 8 Step 1 composes; `::definition_for_graphql_name` is the one net-new member and reuses `iter_definitions()` plus `types/relay.py::implements_relay_node` instead of adding a parallel name index.
- `django_strawberry_framework/relay.py::_decode_or_graphql_error` / `::decode_model_global_id` — the two `DONE-032` wrappers around this slice's helper (wire-error conversion; the write-side typed-id primitive). Both call `decode_global_id`; neither re-implements the parse or the dispatch.

**New helpers justified:** none. This pass writes no source.

**Duplication risk avoided:** none introduced; the pass touches two Markdown files.

### Implementation steps

This pass performs the audit and the reconciliation only. No source, no tests.

1. Re-derive every contracted Slice-3 surface at HEAD against the spec's stated shape and behavior — not merely its symbol name — and read `decode_global_id` path by path rather than trusting its docstring, which is itself a claim (`### CODE GAP audit`).
2. Test the Decision 8 uniform-`ConfigurationError` guarantee against **every** failure mode the spec enumerates, plus the ones shipped code adds.
3. Re-derive every test named in the Slice-3 `## Test plan` block, confirm it exists *and* asserts what the spec says, and confirm the file the spec files it under can reach that scope.
4. Apply the three-case test to Decision 11's "no public export in `0.0.9`" posture (true dated observation / falsified prediction / true prediction whose enduring implication later work falsified).
5. Enumerate shipped Slice-3 behavior with **no** owning spec sentence, and decide per case.
6. Rewrite the spec to state the current contract directly; append the reasoning to the rationale companion under the owning Decision.
7. Run the closing verification checks.

### Test additions / updates

None. `### Final verification checks run` records the focused run confirming the contracted rows are green at HEAD.

### Implementation discretion items

None; no Worker 2 pass.

### Spec slice checklist (verbatim)

Copied verbatim from `docs/SPECS/spec-031-globalid_encoding-0_0_9.md` `## Slice checklist`, Slice 3, **as it read at the start of this pass** (pre-edit, so the audit is legible against what the slice was dispatched with). Boxes are ticked because the slice **shipped** — each tick is the CODE GAP audit's verdict, evidenced below.

- [x] Slice 3: the decode seam — `decode_global_id` dispatch + encoder/decoder symmetry + transitional `type+model` (per [Decision 8](#decision-8--decode-routes-through-djangos-app-registry-then-the-framework-registry-to-the-primary-type))
  - [x] [`registry.py`][registry] gains `definition_for_graphql_name(name)` — a unique-`graphql_type_name` lookup over [`iter_definitions()`][registry] returning the matching [`DjangoTypeDefinition`][definition], raising [`ConfigurationError`][glossary-configurationerror] on ambiguity or miss (the type-name decode entry point; keyed on `graphql_type_name`, NOT `type_cls.__name__`, so a [`Meta.name`][glossary-metaname]-renamed type still decodes).
  - [x] [`django_strawberry_framework/types/relay.py`][relay] gains an internal `decode_global_id(gid: relay.GlobalID | str)` (accepts a [`relay.GlobalID`][glossary-relay-node-integration] or its base64 string, NOT a raw payload) implementing the **resolve-then-enforce** dispatch of [Decision 8](#decision-8--decode-routes-through-djangos-app-registry-then-the-framework-registry-to-the-primary-type): Step 1 resolves a candidate — a model-label slot via `django.apps.apps.get_model(...)` → [`registry.get(model)`][registry] (primary / lone type), a GraphQL-type-name slot via `registry.definition_for_graphql_name(...)`; Step 2 reads the candidate's **recorded effective strategy** ([Decision 10](#decision-10--resolve_typename-injection-via-the-__func__-identity-test-at-phase-25)) and enforces it permits the payload shape (`model` → model-label only; `type` → type-name only; `type+model` → both; `callable` / `custom` → no decode, encode-only). Malformed base64 / non-`type:id` input (Strawberry's `GlobalIDValueError` / `ValueError`), an unresolvable label, or a strategy-forbidden shape all raise [`ConfigurationError`][glossary-configurationerror] (one uniform decode-failure type, the [`RelatedFilter`][glossary-relation-handling]-style fail-loud message).
  - [x] Encoder/decoder round-trip symmetry tests for the **three decodable strategies** (`model` / `type` / `type+model`; `callable` is encode-only — no decode symmetry); the transitional-mode test proving an old type-anchored ID still decodes while new emitted IDs use the model-label payload (the card DoD's explicit requirement); a [`Meta.name`][glossary-metaname]-renamed `type`-strategy round-trip (`ItemType` with `Meta.name = "Item"` emits `Item:<pk>` and decodes back through the `graphql_type_name` helper); and the **negative** Step-2 cases (a type-name ID rejected by a `model`-strategy type, a model-label ID rejected by a `type`-strategy type, any ID for a `custom`-override type rejected as encode-only); and a malformed-base64 / non-`type:id` input raising [`ConfigurationError`][glossary-configurationerror] (not a leaked `GlobalIDValueError`). The decode helper honors [`Meta.primary`][glossary-metaprimary] (a model-label ID for a multi-type model routes to the primary) — pinned with a multi-`DjangoType` fixture.
  - [x] Package coverage: [`tests/types/test_relay_interfaces.py`][test-relay-interfaces] (the one-to-one mirror of [`types/relay.py`][relay] per [`docs/TREE.md`][tree], where the encode / decode lands) covers the `model` / `type` / `type+model` decode paths, the `graphql_type_name` (not `__name__`) lookup, the Step-2 strategy-shape enforcement (both rejection directions plus the `custom` encode-only rejection), the **absent-strategy rejection** (a non-Relay-Node `graphql_type_name` / model-label candidate whose `effective_globalid_strategy` is `None`), the malformed-input `ConfigurationError`, the primary-routing rule, and the unresolvable-label `ConfigurationError`. [`registry.definition_for_graphql_name`][registry] coverage (Relay-only scan + ambiguity) lands in [`tests/test_registry.py`][test-registry].

All four boxes landed. Three were then **extended** in the spec by this pass (S7/S8/S9) to contract shipped behavior the sub-bullets were silent on; the verbatim copy above is deliberately the pre-edit text.

### CODE GAP audit

**Verdict: the CODE GAP list is EMPTY.** Every surface Slice 3 contracts exists at HEAD, in the shape the spec states, pinned by the named tests. Nothing was skipped, dropped, or forgotten. Worker 0's three-item index was used as a starting point and each item independently re-derived; all three confirmed, and six further divergences (none of them a gap) surfaced.

Evidence is symbol-qualified per `AGENTS.md` rule 27.

| # | Contracted surface | Verdict | Evidence |
| --- | --- | --- | --- |
| 1 | `registry.py::TypeRegistry.definition_for_graphql_name` exists, returns the `DjangoTypeDefinition` | **exists** | `django_strawberry_framework/registry.py::TypeRegistry.definition_for_graphql_name` — signature `(self, name: str) -> DjangoTypeDefinition`; returns `matches[0]`. |
| 2 | …scans `iter_definitions()`, **Relay-Node definitions only** | **exists** | `…::TypeRegistry.definition_for_graphql_name` #"if implements_relay_node(type_cls) and definition.graphql_type_name == name" — the comprehension is over `self.iter_definitions()` and gates on `types/relay.py::implements_relay_node`. Pinned by `tests/test_registry.py::test_definition_for_graphql_name_ignores_non_relay_definitions`. |
| 3 | …keyed on `graphql_type_name`, **not** `type_cls.__name__` | **exists** | Same comprehension compares `definition.graphql_type_name`. `tests/test_registry.py::test_definition_for_graphql_name_honors_meta_name` asserts the `Meta.name` value resolves **and** that the class name raises. |
| 4 | …raises `ConfigurationError` on miss and on ambiguity | **exists** | `…::TypeRegistry.definition_for_graphql_name` #"No registered Relay-Node DjangoType has GraphQL type name" and #"is ambiguous across multiple Relay-Node". `tests/test_registry.py::test_definition_for_graphql_name_unknown_raises`, `::test_definition_for_graphql_name_ambiguous_raises` (the latter asserts both colliding class names appear in the message). |
| 5 | `types/relay.py::decode_global_id(gid: relay.GlobalID \| str) -> tuple[type, str]` | **exists** | `django_strawberry_framework/types/relay.py::decode_global_id` — exact annotation, returns `target_type, node_id`. |
| 6 | Runtime input-type gate before any parse | **exists** | `…::decode_global_id` #"if not isinstance(gid, (relay.GlobalID, str))" — first statement after the in-function `registry` import. `tests/types/test_relay_interfaces.py::test_decode_non_str_input_raises` parametrizes `None` / `42` / `object()` / `b"bytes"`. |
| 7 | `str` branch parses via `relay.GlobalID.from_id`, catching the `ValueError` superset | **exists** | `…::decode_global_id` #"decoded = relay.GlobalID.from_id(raw_gid)" inside `except ValueError as exc:` → `ConfigurationError`. `::test_decode_malformed_base64_raises_configuration_error`. |
| 8 | `relay.GlobalID` branch read directly (`.type_name` / `.node_id`) | **exists** | `…::decode_global_id` #"decoded = gid" then the slot reads. |
| 9 | Empty `type_name` / empty `node_id` rejected (package-added) | **exists** | `…::decode_global_id` #"GlobalID has an empty slot". `::test_decode_empty_type_name_raises`, `::test_decode_empty_node_id_raises`. |
| 10 | Step 1, model-label branch: `apps.get_model` → `registry.get(model)` | **exists** | `…::decode_global_id` #"app_label, model_name = type_name.split" and #"target_type = registry.get(model)"; the `LookupError` arm raises `ConfigurationError`. `::test_decode_model_label_routes_to_primary`. |
| 11 | Step 1, type-name branch: `registry.definition_for_graphql_name` | **exists** | `…::decode_global_id` #"definition = registry.definition_for_graphql_name(type_name)". `::test_decode_type_name_routes_via_graphql_name`. |
| 12 | Step 1 honors `Meta.primary` (multi-type model → primary) | **exists** | `registry.py::TypeRegistry.get` returns `_primaries[model]` first. `::test_decode_model_label_routes_to_primary` builds a two-type model and asserts the primary; `::test_model_label_secondary_collapse_warns_and_routes_to_primary` re-pins it from the emit side. |
| 13 | Step 2 reads the **recorded** `effective_globalid_strategy` | **exists** | `…::decode_global_id` #"strategy = definition.effective_globalid_strategy" — reads the stamped field, never re-resolves. |
| 14 | Step 2: absent (`None`) strategy → `ConfigurationError` | **exists** | `…::decode_global_id` #"no recorded GlobalID strategy". Pinned twice, once per arrival: `::test_decode_non_node_graphql_name_raises` (type-name) and `::test_decode_model_label_to_non_node_primary_raises` (model-label). |
| 15 | Step 2: `model` → model-label only; `type` → type-name only; `type+model` → both | **exists** | `…::_accepts_model_label_decode` / `::_accepts_type_name_decode` over `MODEL_LABEL_STRATEGIES` / `TYPE_NAME_STRATEGIES`, selected by `is_model_label`. `::test_decode_model_strategy_rejects_type_name_id`, `::test_decode_type_strategy_rejects_model_label_id`, `::test_type_plus_model_decodes_both`. |
| 16 | Step 2: `callable` / `custom` are encode-only (no decode) | **exists** | Neither name is in either frozenset, so both fall to the `not permitted` arm. `::test_decode_callable_strategy_has_no_decode_path`, `::test_decode_custom_override_type_has_no_decode_path` (each first asserts the recorded strategy, then the raise). |
| 17 | Unresolvable label (no installed app/model; no registered type) → `ConfigurationError` | **exists** | `…::decode_global_id` #"resolves to no installed" and #"has no registered (primary)". `::test_decode_unresolvable_label_raises`, `::test_decode_model_label_unregistered_model_raises`. |
| 18 | Encoder/decoder round-trip symmetry for the three decodable strategies | **exists** | `::test_encode_decode_round_trip_decodable_strategies`, parametrized `["model", "type", "type+model"]`, encoding through the same `_emitted_type_name_slot` helper the emit tests use. |
| 19 | Transitional `type+model` accepts old type-anchored **and** new model-anchored IDs | **exists** | `::test_type_plus_model_decodes_both` asserts both directions against one type. |
| 20 | `Meta.name`-renamed `type`-strategy round-trip | **exists** | `::test_decode_type_strategy_honors_meta_name_round_trip` asserts the emitted slot is `"Item"` (not `"ItemType"`) **and** that it decodes back. |
| 21 | Coverage placement: decode in `tests/types/test_relay_interfaces.py`, helper in `tests/test_registry.py` | **exists** | 21 decode tests under the `# spec-031 - the decode seam` banner in the former; 5 `definition_for_graphql_name` tests under the `# spec-031` banner in the latter. Count re-derivable: `awk 'NR>=2608' tests/types/test_relay_interfaces.py \| grep -c '^def test_'` → 21; `grep -c '^def test_definition_for_graphql_name' tests/test_registry.py` → 5. |

**Decision 8's uniform-`ConfigurationError` guarantee, tested per failure mode rather than assumed.** Every enumerated mode was traced through the shipped body, and the two paths the docstring does *not* mention were traced too:

| Failure mode | Surfaces as | Where contained |
| --- | --- | --- |
| non-`str` / non-`GlobalID` input | `ConfigurationError` | the `isinstance` gate; the message renders the type through `exceptions.py::_safe_type_name`, so a metaclass whose `__name__` raises cannot escape (`::test_decode_hostile_input_type_name_stays_typed`) |
| malformed base64 / non-`type:id` | `ConfigurationError` | `except ValueError` — `GlobalIDValueError ⊂ ValueError`, and `binascii.Error` / `UnicodeDecodeError` are also `ValueError` subclasses, so the superset spelling is correct rather than merely convenient |
| hostile `str` subclass | `ConfigurationError` | `str.__str__(gid)` before `from_id`, plus `_safe_arg_repr` in the diagnostic (`::test_decode_hostile_string_subclass_stays_typed`) |
| `GlobalID` slot access raises | `ConfigurationError` | `except BaseException` around the two slot reads (`::test_decode_hostile_globalid_slots_stay_typed`) |
| non-`str` `GlobalID` slot | `ConfigurationError` | the `isinstance(type_name, str)` pair, **before** the truthiness check (`::test_decode_globalid_rejects_non_string_slots`) |
| empty `type_name` / `node_id` | `ConfigurationError` | the post-normalization truthiness check |
| unresolvable app / model label | `ConfigurationError` | `except LookupError` around `apps.get_model` |
| model with no registered type | `ConfigurationError` | the `target_type is None` arm — `registry.get` returns `None` for *both* "unregistered" and "multiple types, no primary", so the ambiguous-model case lands here too rather than leaking |
| ambiguous `graphql_type_name` | `ConfigurationError` | raised inside `registry.py::TypeRegistry.definition_for_graphql_name`, not re-wrapped |
| absent (`None`) recorded strategy | `ConfigurationError` | the Step-2 `strategy is None` arm |
| strategy-forbidden shape | `ConfigurationError` | the Step-2 `not permitted` arm |

No path can reach `GlobalIDValueError`, `KeyError`, `AttributeError`, or `TypeError`. The only unguarded expressions after the gate are `type_name.split(".", 1)` and the two frozenset membership tests, both of which run on values already proved to be base `str`. `registry.get_definition` returns `None` rather than raising, and the `definition is not None` guard folds that into the `strategy is None` arm.

**Divergences found (all reconciled in the spec; none is a CODE GAP).**

1. **The hostile-input hardening had no owning spec sentence** (Worker 0's handed item, **confirmed**). `types/relay.py::decode_global_id` normalizes `str` subclasses through `str.__str__` on the raw input **and** on both parsed slots, wraps the slot reads in `BaseException`, and rejects non-`str` slots before the truthiness check. Decision 8 stated the gate and the empty-slot contract and stopped. Four shipped tests pin it (`::test_decode_hostile_input_type_name_stays_typed`, `::test_decode_hostile_globalid_slots_stay_typed`, `::test_decode_globalid_rejects_non_string_slots`, `::test_decode_hostile_string_subclass_stays_typed`). Contracted by S1/S6/S7/S8/S12 — same treatment Slices 1 and 2 gave the un-inspectable-callable and normalized-return rules.
2. **"the only caller" / "the only callers" — a caller census `DONE-032` falsified, in three spellings.** Decision 8 said it at line 317 ("because its caller is root `node(id:)`"), line 326 ("its only caller is root `node(id:)`"), and line 340 ("root `node(id:)` / `nodes(ids:)` (the only callers)"). At HEAD there are three distinct consumption paths: `django_strawberry_framework/relay.py::_decode_or_graphql_error` (root node fields; converts to a `GLOBALID_INVALID` `GraphQLError`), `django_strawberry_framework/relay.py::decode_model_global_id` (the **write-side** typed-id primitive shared by `mutations/resolvers.py::coerce_lookup_id`, `utils/write_values.py`, and the form / DRF resolvers), and the public `django_strawberry_framework/testing/relay.py` re-export. S1/S3/S4.
3. **Step 2's memberships are shared named frozensets, not four independent rules.** `types/relay.py::MODEL_LABEL_STRATEGIES` / `::TYPE_NAME_STRATEGIES`, read through `::_accepts_model_label_decode` / `::_accepts_type_name_decode`, and shared with `::_emits_model_label` (the routing audit) and `filters/base.py::_accepted_globalid_type_names`. The spec spelled the shapes inline. Same class as Slice 1's `STRING_GLOBALID_STRATEGIES` finding. S2/S7/S12.
4. **Decision 11's public-export posture — case (c), a true prediction whose enduring implication later work falsified.** The three-case test was applied, not assumed. (a) is ruled out: the sentence sits in a Decision, not in the licensed-dated-observation `## Current state`. (b) is ruled out: the prediction *held* — `031` shipped no public export, and the rejected alternative's tested-usage promotion discipline named `032` as the promoting card, which is exactly what happened. What rots is the present-tense reading of "the `decode_global_id` / encode helpers are internal": `testing/relay.py` re-exports `decode_global_id` as **the same function object** (`tests/testing/test_relay.py::test_public_decode_round_trip_primary_and_type_name` #"re-export, not a wrapper"), so Decision 8's uniform-error contract is now the public one. Reconciled to the scope boundary it was really drawing — this **card**, not the `0.0.9` **release** — neither deleted nor left verbatim. S5. The heading and the `## Non-goals` entry were already card-scoped and stand; renaming the heading would break the `[spec-031-d11]` / `[rationale-d11]` anchor pair for no gain in accuracy.
5. **A Test-plan bullet naming three cases hid two shipped tests and a whole test file.** `test_decode_unresolvable_label_raises` was filed as covering "an unknown app/model, an unregistered model, or an ambiguous `graphql_type_name`" — three different rejection sites, shipped as three tests in two files, one of which (`tests/test_registry.py`) the Test plan never listed even though the Slice-3 checklist said the helper's coverage lands there. Sibling of Slice 1's wrong-file finding. S11.
6. **Two shipped tests had no owning Test-plan bullet, both contracted.** `::test_decode_model_label_to_non_node_primary_raises` (the model-label arrival of the absent-strategy rejection — it reaches the Step-2 `None` guard because `registry.get` does not filter on Relay shape, where the type-name arrival raises earlier inside the Relay-only scan) and `::test_decode_model_label_unregistered_model_raises`. Both pin consequences a Decision already states; neither is scope creep. S11.

**Deliberately NOT written into the spec.** `registry.py::TypeRegistry.definition_for_graphql_name`'s in-function `from .types.relay import implements_relay_node` and `decode_global_id`'s in-function `from ..registry import registry` are import-cycle mechanics documented at the call sites; the spec contracts behavior, not import placement (the same call Slice 2 made for the finalizer's internal-consistency raises).

**`## Current state` — checked, not touched.** Its Slice-3-relevant sentence ("Strawberry's native decode … is reached only through a root `node(id:)` field, which is **not shipped until** `DONE-032-0.0.9`. So in `0.0.9` no shipped path hits native `resolve_type` with a model-label payload") is a licensed dated observation and was **true at the authoring commit**: `git ls-tree b1f82f0e django_strawberry_framework/relay.py django_strawberry_framework/testing/` returns no `relay.py` at either path. Same instrument Slice 2 used for the `_expected_global_id_type_name` sentence, same verdict — leave it.

### Spec changes made (Worker 1 only)

All in `docs/SPECS/spec-031-globalid_encoding-0_0_9.md`; line numbers are post-edit. Every change is triggered by Slice 3.

| # | Line(s) | Change | Reason |
| --- | --- | --- | --- |
| S1 | 317 | Decision 8 opening: added the **input-containment** contract (subclass admission, `str.__str__` normalization of the raw input and both slots, the `BaseException` slot guard, non-`str` slot rejection before the truthiness check, `_safe_type_name` / `_safe_arg_repr` diagnostics) and extended the uniform-error enumeration; replaced "because its caller is root `node(id:)`" with "because every caller feeds it arbitrary client input" | divergence 1 + divergence 2 (spelling 1) |
| S2 | 324 | Decision 8 Step-2 lead-in: named `MODEL_LABEL_STRATEGIES` / `TYPE_NAME_STRATEGIES` and the `_accepts_model_label_decode` / `_accepts_type_name_decode` predicates, and their sharing with `_emits_model_label` and `filters/base.py::_accepted_globalid_type_names` | divergence 3 |
| S3 | 326 | Decision 8 absent-`None` bullet: replaced "its only caller is root `node(id:)`" with the three shipped consumption paths | divergence 2 (spelling 2) |
| S4 | 340 | Decision 8 closing paragraph: rewritten from the falsified census to the current contract — the single decode entry point, no native `GlobalID.resolve_type` for model labels, and the three named `DONE-032` callers; adds that `GlobalID` filtering never calls it | divergence 2 (spelling 3) |
| S5 | 385 | Decision 11: "No new public export in `0.0.9`" → "No public export from this card", with the same-release `testing/relay.py` re-export named as the identity re-export and the tested-usage promotion discipline stated | divergence 4 |
| S6 | 241 | `## Error shapes`: new row for the subclass-containment rejections (hostile `str` subclass; `GlobalID` subclass whose slots raise or are non-`str`) | divergence 1 |
| S7 | 70 | Slice-3 checklist, decode bullet: appended the input-containment clause and the Step-2 shared-frozenset clause | divergences 1, 3 |
| S8 | 71 | Slice-3 checklist, test bullet: appended the four input-containment cases | divergence 1 |
| S9 | 72 | Slice-3 checklist, coverage bullet: split the unresolvable-label case in two, added input-containment, and enumerated the registry helper's five covered behaviors | divergences 5, 6 |
| S10 | 418 | Implementation plan Slice-3 row: the `~14` new-tests estimate replaced by the **measured** 26 (21 + 5), enumerated by case and by file | divergences 1, 5, 6 |
| S11 | 504, 507-508, 510-516 | `## Test plan`: added `test_decode_model_label_to_non_node_primary_raises`; added the four input-containment tests; split `test_decode_unresolvable_label_raises` from `test_decode_model_label_unregistered_model_raises` and pointed the ambiguity case at the registry block; added a new `### Slice 3 — tests/test_registry.py` block with all five helper tests | divergences 1, 5, 6 |
| S12 | 580 | DoD item 5: added the containment half and the named Step-2 frozensets; extended the "Tests pin" list with both absent-strategy arrivals, the containment errors, the unregistered-model error, and the registry helper's coverage | divergences 1, 3, 5, 6 |
| S13 | 672, 676 | Link definitions: added `[package-relay]` → `django_strawberry_framework/relay.py` and `[testing-relay]` → `django_strawberry_framework/testing/relay.py`, in alphabetical position under `<!-- django_strawberry_framework/ -->` | required by S4 / S5 |

No spec sub-check is left `- [ ]`; no deferral reason is owed.

### Rationale companion entries appended

All in `docs/SPECS/appx/spec-031-globalid_encoding-0_0_9-rationale.md`, append-only, in the `**Post-ship:**` convention Slices 1 and 2 established, keyed to the Decision they belong to.

- **Decision 8 → `### Changes this Decision underwent`**, three bullets: (a) the type gate admits subclasses, so the uniform-error contract needed a containment half — the third instance in this spec of *a type check is a claim about the moment it runs, so a boundary that admits subclasses owes a normalization step as well as a check*; (b) "the only caller" falsified twice over by the card it named, with the load-bearing half restated and the generalization firmed up — *a spec may state how a path is reached, never how many things reach it*; (c) Step 2's memberships are shared frozensets, not four independent rules.
- **Decision 11 → `### Changes this Decision underwent`**, one bullet: the prediction held, its enduring implication did not — *a dated prediction that came true still needs reconciling when its subject is a scope a later reader will mis-read as current*.
- **`## Non-Decision deliberation`**, two bullets: (a) one Test-plan bullet naming three cases hid two shipped tests and a whole test file — *a Test-plan bullet that lists several cases in one sentence is a claim about one test, and a rejection path per case is the normal shipped shape*; (b) the fourth stale `.py` comment clause, batched not dispatched.

Four link definitions were added to the companion (`[package-relay]`, `[testing-relay]`, `[test-registry]`, `[spec-031-non-goals]`), each in alphabetical position within its group header.

### Static inspection helper

**Not run, recorded skip.** `docs/builder/BUILD.md` `### When to run the helper during build` triggers it when *the plan adds logic* to a file under `types/`. This plan adds no logic anywhere: it writes two Markdown files and no `.py`. Had a CODE GAP forced a Worker 2 pass against `types/` or `registry.py`, it would have run with `--output-dir docs/shadow`. (Worker 0's pre-flight step 2 already exercised it against `types/relay.py`, exit 0.)

### Plan declarations

- **Hot-path declaration:** `none`. No production code is written by this pass. Recorded for the next pass that does: `decode_global_id` **is** now hot — `relay.py::_decode_or_graphql_error` runs per root `node(id:)` / per element of `nodes(ids:)`, and `relay.py::decode_model_global_id` runs per typed id and per relation `<field>_id` value on the write path — so a Worker 2 pass landing there owes a before/after wall-clock median over a stated iteration count for `decode_global_id` on a model-label payload, plus the `nodes(ids:)` per-element multiple. Deliberate, not silence.
- **Floor-verification scope:** `none`. `types/relay.py` and `registry.py` are Strawberry type-construction seams and would have required a focused `tests/types/` + `tests/test_registry.py` floor run in an isolated venv had this pass landed in them; it does not. Deliberate, not silence.
- **Ownership partition:** `none; sequential slices`.
- **Boundary count (split trigger):** zero new boundaries. No split question to answer beyond recording the count.

### Final verification checks run

- `uv run pytest tests/types/test_relay_interfaces.py tests/test_registry.py --no-cov -q` → **222 passed**, 8 workers, 4.95s. No `--cov*` flag.
- `uv run pytest tests/testing/test_relay.py --no-cov -q` → **14 passed**, 3.73s (the public re-export contract cited in divergence 4).
- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-031-globalid_encoding-0_0_9.md` → **`OK: 31 terms`**, unchanged from pre-flight.
- `uv run python scripts/check_trailing_commas.py --check <spec> <rationale>` → clean (the `.md` link-def scaffold and group ordering, including the four new definitions).
- In-page anchors and reference-style link definitions, both files, after the edits: spec `83` defs / `83` uses / `20` in-page anchors, rationale `49` / `49` / `14` — no missing definition, no unused definition, no dangling anchor. Every cross-file definition's target file exists and every cross-file `#anchor` resolves to a real heading in the target.
- Byte counts: spec `169,444` (from `161,327`); rationale companion `104,080` (from `95,578`).
- Caller-census re-sweep of the whole spec after the edits: no `the only caller` / `the only callers` / `its caller is root` remains.
- `git status --short` re-read at the start of this pass: only this cycle's own files (`docs/SPECS/spec-031-globalid_encoding-0_0_9.md` modified; the rationale companion, build plan, and slice artifacts untracked). The concurrent session's four baseline-dirty paths were absorbed by its mid-cycle commit (HEAD `5ebcfe9c`); none was edited or reverted.
- No `git stash` / `git checkout` / `git restore` / `git worktree` was used. The one HEAD-history read (`git ls-tree b1f82f0e …`) is read-only and wrote nothing into the repo.

### Worker 2 dispatch

**Not owed.** The CODE GAP list is empty and no source edit is judged worth a build cycle. One source-side item is deferred rather than dispatched — see below.

### Deferred to `### Deferred work catalog` (for `bld-031-final.md`)

- **A fourth stale `.py` docstring clause, joining the batch Slice 2 opened.** `django_strawberry_framework/types/relay.py::decode_global_id` docstring #"WIP-ALPHA-032-0.0.9" — the surrounding sentence reads "It is the forward-looking piece root ``node(id:)`` / ``nodes(ids:)`` (``WIP-ALPHA-032-0.0.9``) will consume - no shipped ``0.0.9`` path calls it yet". Both clauses are false at HEAD: the card is `DONE-032-0.0.9`, and the helper has three live callers (divergence 2). Comment-only, nothing behavioral rests on it, and the spec now states the correct contract in every home; `### Isolation is non-waivable` makes even this a two-spawn cycle, so it batches with Slice 2's three rather than opening a fifth. **Running total for the batch: four clauses.**
- **Handed forward, unclaimed by any slice so far** (raised by Slice 0, not taken by Slices 1, 2, or 3, and outside Slice 3's contract): the pre-archival `docs/spec-031-globalid_encoding-0_0_9.md` path is still asserted at spec lines 250 (Decision 1), 567 (DoD item 1), and 84 / 542 / 589 (the Slice-5 doc-wrap text). Decision 1 and DoD item 1 belong to no functional slice; Slice 5 of this cycle is audit-only. The integration pass should either take them or record them as a maintainer follow-up. DoD item 1's companion claim that the two net-new terms are absent from the terms CSV is likewise still standing and still false.

### Summary

Slice 3 shipped complete. `registry.py::TypeRegistry.definition_for_graphql_name` and `types/relay.py::decode_global_id` both exist at HEAD in the shape Decision 8 specifies, the resolve-then-enforce dispatch behaves as contracted in both Step-1 branches and all five Step-2 strategy states, and the uniform-`ConfigurationError` guarantee holds against every one of the eleven failure modes traced — including the three the spec never named. All 26 contracted tests exist across the two files the checklist names and assert what the spec says they assert. **CODE GAP list empty.** Thirteen spec changes reconcile the spec to the shipped code: one unowned hardening contracted, one caller census falsified in three separate spellings, one shared-constant vocabulary named, one scope-boundary sentence sharpened after the three-case test, one Test-plan bullet split into the three sites it actually described, and one whole test file added to the Test plan. Six rationale bullets appended. All three of Worker 0's handed items survived re-derivation this time; six further divergences were found beyond them, confirming again that the handed list is a floor and not a population.

### Final status

`final-accepted`. Procedural closure: no Worker 2, no Worker 3.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

[glossary-configurationerror]: ../GLOSSARY.md#configurationerror
[glossary-metaname]: ../GLOSSARY.md#metaname
[glossary-metaprimary]: ../GLOSSARY.md#metaprimary
[glossary-relation-handling]: ../GLOSSARY.md#relation-handling
[glossary-relay-node-integration]: ../GLOSSARY.md#relay-node-integration
[tree]: ../TREE.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

[definition]: ../../django_strawberry_framework/types/definition.py
[registry]: ../../django_strawberry_framework/registry.py
[relay]: ../../django_strawberry_framework/types/relay.py

<!-- tests/ -->

[test-registry]: ../../tests/test_registry.py
[test-relay-interfaces]: ../../tests/types/test_relay_interfaces.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
