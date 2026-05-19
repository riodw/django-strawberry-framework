# Spec: Consumer override semantics for scalar fields

Target release: `0.0.6`.
Status: draft (revision 7, post-rev6 review).
Owner: package maintainer.
Predecessors: [`docs/FEATURES.md`](FEATURES.md) (entries [`DjangoType`](FEATURES.md#djangotype), [`Scalar field conversion`](FEATURES.md#scalar-field-conversion), [`Scalar field override semantics`](FEATURES.md#scalar-field-override-semantics), [`Definition-order independence`](FEATURES.md#definition-order-independence), [`Relation handling`](FEATURES.md#relation-handling)), [`KANBAN.md`](../KANBAN.md) card `WIP-ALPHA-015-0.0.6`.
Card line: ["Consumer override semantics (scalar fields) — extends the `DONE-006-0.0.4` relation-field override contract to scalar fields and closes out the remaining `0.0.6` patch."](../KANBAN.md)

Revision history (kept inline so the spec is self-contained):

- **Revision 1** — initial draft. Surfaces the existing scalar/relation asymmetry in `_build_annotations`, pins the symmetric annotation-only contract for scalars (mirroring the shipped `consumer_annotated_relation_fields` path), confirms the assigned-`strawberry.field` scalar contract already shipped in `0.0.5` and stays unchanged, and lands the previously-skipped `test_consumer_annotation_overrides_synthesized` test as the proof of the new contract.
- **Revision 2** (post-feedback review) — two high-severity corrections plus one medium and one low:
  1. **H1**: rev1's Relay `id` edge case said a consumer `id: int` annotation on a `[Meta.interfaces](FEATURES.md#metainterfaces) = (relay.Node,)` type "would still raise `NodeIDAnnotationError` at finalization." That mis-orders the lifecycle. In `_build_annotations`, the consumer-authored short-circuit at `types/base.py:644` runs **before** the `relay.Node` pk-suppression branch at `types/base.py:651-657`, so a consumer `id: int` annotation skips synthesis cleanly and lands on `cls.__annotations__`. Finalization itself succeeds; `strawberry.Schema(...)` construction then fails with a Strawberry-side `ValueError` because `Node.id` is `ID!` while the concrete type's `id` is `Int!`. A schema-build `ValueError` is the wrong UX surface for a `DjangoType`-level configuration mistake. Fix: detect the collision in `__init_subclass__` (after `consumer_annotated_scalar_fields` / `consumer_assigned_scalar_fields` are collected) and raise a package-owned `ConfigurationError` with a message pointing at `relay.NodeID[...]` as the supported escape hatch. New Slice 1 implementation task; new Slice 1 test pinning the early raise.
  2. **H2**: rev1's "no change to `_build_annotations` body" reading was too narrow. Adding annotation-only scalar names to `consumer_authored_fields` skips the whole scalar branch before `convert_scalar(...)` runs. `convert_scalar` carries far more than annotation synthesis — it owns unsupported-field-type rejection (`types/converters.py:95-196`), grouped-choices rejection, `ArrayField` nested-array / outer-`choices` rejection, `HStoreField` sentinel routing, null widening, and choice-enum registration into the shared `(model, field_name)` cache. The new short-circuit silently bypasses every one of those validations for an annotation-overridden field. That is the correct consumer-authoritative contract for this card (matches the existing "consumer takes responsibility for runtime correctness" non-goal), but rev1 only called out the enum-cache side effect. Fix: add a new Decision 7 that pins the bypass contract explicitly, add three new Slice 1 tests covering unsupported-field-type override, invalid-choices override, and `ArrayField` rejected-shape override, and expand the Slice 5 `docs/FEATURES.md` update so the `Scalar field conversion` entry's "unsupported field types raise `ConfigurationError`" wording acquires the annotation-override recourse (parallel to the existing [`Meta.exclude`](FEATURES.md#metaexclude) recourse).
  3. **M1**: rev1's `test_annotation_only_scalar_override_survives_strawberry_finalization` end-to-end test described the introspection query as `__schema { types { name fields { name type { name } } } }` and asserted `type.name == "Int"`. That assertion misses non-null unwrapping: a non-nullable Django scalar surfaces in GraphQL as `Int!`, where `type.name` is `null` and the terminal name lives at `type.ofType.name`. Fix: rewrite the test description to query `type { kind name ofType { kind name } }` and unwrap through `kind == "NON_NULL"` (or reuse the existing `_introspect_field_type` helper pattern at `tests/types/test_converters.py:434`). Pins the actual scalar at the leaf, not the wrapper.
  4. **L1**: Slice 1's "add `consumer_annotated_scalar_fields` after `consumer_assigned_scalar_fields`" insertion-point instruction contradicted Decision 3's sample (which placed the new field between `consumer_annotated_relation_fields` and `consumer_assigned_relation_fields`). Fix: pick the grouped-by-style order (annotated-relation, annotated-scalar, assigned-relation, assigned-scalar). Update Slice 1's checklist text to match Decision 3's sample, and update Decision 3's sample to also re-order the existing two `consumer_assigned_*` lines so the dataclass field order is internally consistent. Worker 1 lands the cosmetic re-order in the same commit as the new field.
- **Revision 3** (post-rev2 review) — one high-severity correction plus two medium and one low cleanup pass:
  1. **H1**: rev2's Relay-collision guard predicate was too broad — `pk_name in consumer_annotated_scalar_fields or pk_name in consumer_assigned_scalar_fields` rejected (a) the advertised `id: relay.NodeID[int]` escape hatch (the annotation lands in `consumer_annotated_scalar_fields` because `id` is a model pk field, so the guard fires against the very pattern the error message tells consumers to use) and (b) non-`id` primary-key overrides (e.g., `code: str` on a `models.CharField(primary_key=True)` named `code` — the GraphQL fields are `id: ID!` and `code: String!`, no `Node.id` collision). Pinned by the existing `tests/types/test_relay_interfaces.py:240`'s `test_composite_pk_with_explicit_node_id_annotation_is_accepted` which uses `name: relay.NodeID[str]` to escape the composite-pk gate — the same shape this card's rev2 guard would have rejected on a `name`-pk model. Fix: narrow the guard. Only fire when (a) `cls.__annotations__.get("id")` is set OR `cls.__dict__.get("id")` is a `StrawberryField` (the consumer authored an `id` entry — checked by GraphQL field name, not by model pk name); AND (b) `interfaces` includes `relay.Node`; AND (c) the `id` annotation is NOT a `relay.NodeID[...]`-marked annotation (Worker 1 picks the detection mechanism — likely `typing.get_args` inspection for an `Annotated[T, NodeIDPrivate]` marker, or a probe-call of `cls.resolve_id_attr()` after Relay has injected the defaults; the spec contract is "valid `relay.NodeID[...]` passes the guard"). Updated Slice 1 implementation task. Two new Slice 1 tests: `test_consumer_id_relay_nodeid_annotation_on_relay_node_type_is_accepted` (escape-hatch acceptance) and `test_consumer_non_id_scalar_override_on_relay_node_type_is_accepted` (custom-pk override acceptance). Updated Decision 7.
  2. **M1**: rev2's `test_annotation_override_of_unsupported_scalar_field_type_is_allowed` test recipe suggested `myfield: bytes` "or similar". Strawberry's schema-construction pass rejects `bytes` as an unexpected Python type, so a `bytes`-annotated test would fail at `strawberry.Schema(...)` for a reason unrelated to the converter-bypass contract. Fix: rewrite the test recipe to use `str` (or `int`) as the consumer annotation. The Django field type stays unsupported (e.g., a `_FakeUnsupportedField(models.Field)` test fixture, or any concrete Django field not in `SCALAR_MAP`); the consumer annotation just needs to be Strawberry-supported so the schema build doesn't false-positive.
  3. **M2**: rev2's `test_annotation_override_of_arrayfield_with_nested_array_is_allowed` test placement was naive. Real-tree `ArrayField` testing requires the existing `_ARRAY_FIELD_CLS` monkeypatch + `_FakeArrayField` fixture pattern (anchored at `tests/types/test_converters.py:1021` and used at every `ArrayField`-related test in that file). Without the monkeypatch, the test becomes environment-dependent on whether `django.contrib.postgres.fields.ArrayField` imports cleanly (the production code soft-imports it; CI typically has it, but the test contract should not depend on that). Fix: either (a) add the `monkeypatch.setattr(converters, "_ARRAY_FIELD_CLS", _FakeArrayField)` and `_FakeArrayField` setup to the new test (importing the fixture or duplicating the dataclass shape), or (b) place the override-of-nested-`ArrayField` test in `tests/types/test_converters.py` beside the existing `_FakeArrayField` tests rather than in `tests/types/test_definition_order.py`. Worker 1 picks during planning; placement (b) keeps the fixture lookup local and is the smaller-touch option.
  4. **L1**: rev2's revision-history entry was correct, but four downstream cross-references stayed stale: the status badge still said "revision 1, initial"; the verbatim KANBAN body and CHANGELOG bullets at the end of Slice 5 referenced "Slice 6" in two places where the renamed Slice 5 had already taken over the docs/KANBAN/CHANGELOG role; the "no new error sites" claim in the [`ConfigurationError`](FEATURES.md#configurationerror) glossary reference no longer matched the H1 fix's new error site; and the implementation-plan summary table's Slice 1 row still said "4 new tests" and `+30/-1` after rev2 expanded the cluster to 7 tests. Rev3 picks up the strays in the same pass: badge → "revision 3, post-rev2 review"; "Slice 6" → "Slice 5"; "no new error sites" → "one new error site (Relay collision guard — Slice 1)"; Slice 1 row in implementation-plan table updated to "9 new tests" (4 core + 3 converter-bypass + 2 Relay accept/reject) and `+55/-1`; total line delta in the summary paragraph below the table from `~80` to `~140`.
- **Revision 4** (post-rev3 review) — one high-severity correction plus two medium and two low cleanup passes:
  1. **H1**: rev3's Decision 7 left Worker 1 with two choices for the `relay.NodeID[...]` detection mechanism — class-creation-time `typing.get_args` inspection OR finalize-time `cls.resolve_id_attr()` probe — without acknowledging that the option contradicts the rest of the spec. The Slice 1 reject test asserts class-creation failure (`test_consumer_id_annotation_on_relay_node_type_raises` checks that the error fires *before* `finalize_django_types()`); the CHANGELOG entry says the error is raised "at `DjangoType.__init_subclass__` time". A finalize-time probe (option ii) cannot satisfy either. Additionally, the recommended class-creation-time option only works for already-evaluated `relay.NodeID[int]` annotations — under `from __future__ import annotations` (or any stringified annotation), `cls.__annotations__["id"]` is the literal string `"relay.NodeID[int]"`, which `typing.get_args` cannot inspect for the `NodeIDPrivate` marker; a raw `get_args` check would falsely reject the supported escape hatch in that form. Fix: drop option (ii) entirely. Pin the contract as class-creation-time. Replace the detection prose to require `typing.get_type_hints(cls, include_extras=True)`-based evaluation (which resolves stringified annotations using `cls`'s module globals and preserves the `Annotated[T, NodeIDPrivate]` marker), with a fail-soft fallback for `NameError`/`AttributeError` (unresolved forward references that the consumer hasn't imported at type-creation time) — accept conservatively in the fail-soft case rather than raising spuriously. New Slice 1 test pins the string/future-annotation form: `test_consumer_id_string_relay_nodeid_annotation_on_relay_node_type_is_accepted`.
  2. **M1**: rev3's Decision 7 pseudocode rejected ANY `id = <StrawberryField>` assignment on a Relay-Node-shaped type. That bans a currently-working pattern: `@strawberry.field def id(self) -> relay.GlobalID: ...` (or any assigned `id` resolver returning `relay.GlobalID` / `strawberry.ID`) matches the `Node.id: ID!` interface contract and builds a valid schema today. Two viable contracts: (a) **ban all assigned `id` overrides on Relay-Node-shaped types** (the consumer's recourse is `@classmethod resolve_id` for custom id resolution, parallel to `@classmethod resolve_id_attr` for custom id source — both are Strawberry-provided hooks that survive interface compliance), or (b) **inspect the StrawberryField's return-type annotation** and accept `relay.GlobalID` / `strawberry.ID`-typed assignments. Rev4 picks contract (a) — simpler, consistent with the annotation-side guard's "consumer must use the supported escape hatch" framing, and the error message can point at `resolve_id` as the alternative. This is a small intentional behavior change for the niche population of consumers who currently write `id = @strawberry.field def ...: ... -> relay.GlobalID`; it lands as a `Changed` CHANGELOG entry rather than `Added`. New Slice 1 test pins the rejection: `test_consumer_id_assigned_strawberry_field_on_relay_node_type_raises`.
  3. **M2**: rev3's Decision 7 pseudocode used `has_id_annotation = id_annotation is not None` to detect "consumer authored an `id` annotation". That fails to detect `id: None` because `cls.__annotations__["id"]` is literally `None`. While rare, `id: None` is still a consumer-authored annotation and should follow the Relay collision guard (Strawberry's downstream `ValueError` would catch it eventually, but the spec's contract is to catch it at class-creation time with the package-owned `ConfigurationError`). Fix: use `"id" in cls.__annotations__` for the key-presence check. Same fix applied to the `consumer_annotations` mention in the prose where applicable.
  4. **L1**: rev3 said "Slice 1 test cluster has nine tests total" but the listed groups summed to 10 (4 core + 3 converter-bypass + 3 Relay). Rev4 expands further (H1 adds a string-annotation accept test, M1 adds an assigned-id reject test) bringing the total to 12. Fix: update every test-count assertion in the spec to 12 (test strategy intro, implementation-plan summary table's Slice 1 row, definition-of-done test count); also nudge the implementation-plan table's Slice 1 line-delta estimate from `+75/-1` to `+90/-1` to reflect the two extra tests.
  5. **L2**: rev3's `test_annotation_override_of_arrayfield_with_nested_array_is_allowed` recipe said to build a nested `_FakeArrayField(...)` instance and use a consumer `tags: list[list[int]]` annotation, but did not require the model-field name to match the annotation name. The existing converter tests at `tests/types/test_converters.py:1021` name the field `arr`; if Worker 1 mirrors that naming, the annotation `tags: list[list[int]]` does not collide with any selected field and the override-collection path never fires (the test would exercise the rejection path instead, false-passing for the wrong reason). Fix: make the recipe explicit — the model-field name must match the consumer-annotation name (recommend `tags` for both, or `arr` for both — Worker 1 picks during planning; the spec contract is "they match").
- **Revision 5** (post-rev4 review) — one medium correction plus two low cleanups:
  1. **M1**: rev4's `_id_annotation_is_relay_node_id` helper fail-soft path was too broad — on `NameError` / `AttributeError` from `typing.get_type_hints(cls, include_extras=True)`, the helper returned `True` (accept) for **any** unresolved forward reference. That defeats the H1 guard's purpose for the common case of a typo or missing import: `id: "SomeMissingType"` (where `SomeMissingType` is not a `NodeID`) would pass the guard at class-creation time and fall through to a Strawberry-side schema-construction `ValueError` — the exact failure surface the guard exists to replace. Fix: narrow the fail-soft path. On `NameError` / `AttributeError`, inspect the raw string at `cls.__annotations__["id"]` and only accept if it syntactically contains `"NodeID["` (the unqualified form) or `"relay.NodeID["` (the qualified form). Other unresolved strings (`"SomeMissingType"`, `"int"`, etc.) are rejected by the guard with the standard "use `relay.NodeID[...]`" error message. The fail-soft window is now scoped to "the consumer wrote a NodeID-shaped string that does not resolve in `cls`'s module globals at type-creation time" — the genuinely-ambiguous case the rev4 fail-soft was intended to cover. New Slice 1 reject test: `test_consumer_id_unresolved_non_nodeid_string_on_relay_node_type_raises` pins that a typo-style `id: "MissingType"` raises at class-creation time. Test count bumps to 13 (4 core + 3 converter-bypass + 6 Relay = 3 reject + 3 accept).
  2. **L1**: the Decision 7 heading at `spec:347` and every internal anchor reference (`#decision-7--relay-id-override-collision`) still carries the rev3 anchor suffix, even though rev4 substantially expanded the contract (class-creation-only detection, stringified `NodeID` support, assigned-`id` rejection). The suffix is misleading at this point. Fix: rename the heading to a rev-neutral form — `### Decision 7 — Relay \`id\` override collision` — and update every internal anchor reference (six sites including the heading) to the new anchor `#decision-7--relay-id-override-collision`. The detection-mechanism subsection's "Decision-7-7 finalize-time alternative was dropped" reference also flips to rev-neutral wording.
  3. **L2**: the verbatim KANBAN body's "100% coverage across `tests/types/test_definition_order.py`" line and the Definition of done's "three converter-bypass in `tests/types/test_definition_order.py`" wording both ignore the rev4 M2 placement allowance for the `ArrayField` bypass test (Worker 1 may park it in `tests/types/test_converters.py`). Fix: broaden the coverage / placement language to "the override-contract host (`tests/types/test_definition_order.py`) and the converter test host (`tests/types/test_converters.py`) as applicable per the M2 placement decision".
- **Revision 6** (post-rev5 review) — one high-severity correction plus three medium and three low cleanups:
  1. **H1**: rev5's `_id_annotation_is_relay_node_id` fail-soft path falsely rejects directly-resolved `id: relay.NodeID[int]` whenever an unrelated annotation on the same class fails to resolve. `typing.get_type_hints(cls, include_extras=True)` evaluates **every** annotation on `cls` (and walks the MRO); a single unresolved string annotation anywhere on the class trips `NameError`, the fail-soft fires, and the helper inspects `cls.__annotations__["id"]` — which is the already-resolved `Annotated[int, NodeIDPrivate]` object, not a string. `isinstance(raw, str)` is False, the substring check returns False, and the guard rejects the valid escape hatch with the "use `relay.NodeID[...]`" error message — i.e., tells the consumer to do exactly what they already did. The realistic trigger is a `DjangoType` with `id: relay.NodeID[int]` plus any forward-referenced relation annotation like `items: list["AdminItemType"]` (a common pattern). The bug was reproduced locally against the on-disk `strawberry.relay`. Fix: in the fail-soft branch, when `raw` is not a string, fall back to inspecting the resolved object directly (`_has_node_id_marker(raw)`) rather than rejecting unconditionally. New Slice 1 accept test: `test_consumer_id_resolved_relay_nodeid_with_unresolved_sibling_annotation_is_accepted` pins the mixed-annotation class shape.
  2. **M1**: rev4's blanket assigned-`id` ban (every `id = <StrawberryField>` on a Relay-Node-shaped type raises `ConfigurationError`) removes the only path consumers have to attach GraphQL field-level metadata (`description=`, `deprecation_reason=`, `directives=`) to the Relay-supplied `id` field. The two named alternatives — `@classmethod resolve_id` (custom resolver) and `id: relay.NodeID[<pk_type>]` (custom pk shape) — neither attach field metadata. Pre-spec, `id = strawberry.field(description="…")` worked because the assigned-field type matched `Node.id: ID!`. Two options were considered: (a) acknowledge the loss explicitly and document a sibling-field workaround (a separate `display_id: ID` field carries the description; the Relay-supplied `id` stays undecorated), or (b) loosen the ban to allow metadata-only `id = strawberry.field(...)` assignments by inspecting the StrawberryField's `base_resolver` and `type_annotation`. Rev6 picks option (a) — smaller-touch, keeps the guard simple, and field-level metadata on the Relay-supplied `id` field is a rare consumer use case. Update the assigned-side error message to mention the sibling-field workaround; update the Slice 5 `Scalar field override semantics` FEATURES.md body to name the metadata limitation; update the `Changed` CHANGELOG entry to acknowledge the route loss.
  3. **M2**: rev5's Decision 7 pseudocode has a dead `if has_id_annotation and _id_annotation_is_relay_node_id(cls):` conjunction. By the time control reaches this branch, the assigned-id branch has already raised (so `has_id_assignment` is False), and the outer guard required at least one of `has_id_annotation or has_id_assignment` to be True — therefore `has_id_annotation` must be True. The `has_id_annotation and` is dead code. Fix: drop the conjunction, leaving just `if _id_annotation_is_relay_node_id(cls):`. Cosmetic but Worker 1 copies pseudocode mechanically; carrying dead predicates into production code adds drift surface.
  4. **M3**: rev4's M2 entry claims `cls.__annotations__["id"]` is "literally `None`" for `id: None`. Python evaluates the `None` annotation to the `NoneType` class (`<class 'NoneType'>`), not the literal `None` value; `cls.__annotations__["id"] is None` is False for an `id: None` annotation. The key-presence fix (`"id" in cls.__annotations__`) that rev4 landed is still correct, but the rationale was mechanically wrong. Fix: rewrite the inline comment at Decision 7's pseudocode to use accurate reasoning ("key-presence rather than value-truthiness so unusual annotations like `id: None`, `id: Literal[None]`, or string forms that evaluate to false-y types are detected").
  5. **L1**: rev5's "Inheritance" edge case correctly notes inherited annotations don't land in `cls.__annotations__` (so the collection misses them), matching the existing relation-annotation behavior. For the H1 Relay guard specifically, this means an inherited `id: int` on a Relay-Node-shaped DjangoType subclass slips past `"id" in cls.__annotations__`, the guard doesn't fire, and Strawberry's downstream `ValueError` at `strawberry.Schema(...)` is the (acknowledged) failure mode. The corner case is named in the edge-cases section but not pinned by a test, so future changes to the guard could accidentally start walking the MRO without surfacing the regression. New Slice 1 test: `test_inherited_id_annotation_on_relay_node_subclass_is_not_caught_by_guard` declares a base DjangoType with `id: int` and a Relay-Node subclass on a separate model, asserts no `ConfigurationError` at class creation, and asserts Strawberry's `ValueError` fires at schema construction with a message naming `Node.id`.
  6. **L2**: rev5's Decision 7a flags a real cross-type behavior change ("two `DjangoType`s on the same model where one overrides and one does not get the fresh enum from the non-overriding type alone; pre-spec they would have shared whichever loaded first") but the test cluster only pins the single-type case (`test_annotation_override_of_grouped_choices_field_is_allowed` asserts `registry.get_enum` is None after one overriding type). Two-type scenarios are common (the shipped `Meta.primary` card exists to support them). New Slice 1 test: `test_annotation_override_does_not_populate_shared_enum_cache_for_co_resident_types` declares two DjangoTypes on the same model with the same `choices=` column, one overriding and one not, asserts the non-overriding type's introspected GraphQL field uses the generated enum, asserts the overriding type's introspected GraphQL field uses the consumer's annotation, and asserts `registry.get_enum(model, field_name)` is non-`None` (populated by the non-overriding type alone).
  7. **L3**: rev5's `+95/-1` Slice 1 line-delta estimate was a stale carryover from a smaller-scoped earlier revision. With rev6's H1 fail-soft fix branch logic, three new tests (H1 sibling-annotation accept, L1 inheritance non-trigger, L2 cross-type cache), and the M1 sibling-field workaround prose in error messages and the FEATURES.md update, the realistic delta is closer to `+185/-1` (the helper expands to ~45 lines including the resolved-object fallback path; the three tests add ~45 lines combined; the prose adds ~5 lines across the CHANGELOG / FEATURES update). Bump the implementation-plan table row and the "Total expected delta" summary paragraph accordingly. Bump Slice 1 test count from 13 to 16: 4 core + 4 converter-bypass (added cross-type cache) + 8 Relay (3 reject + 5 accept; added sibling-annotation accept and inherited-id non-trigger). Plus three derivative cleanups: (a) promote the "Worker 1 picks during planning" recommendations to defaults across Slices 1 and 2 — placement (a) for the ArrayField bypass test, `description: int` for the non-`id` scalar accept test, explicit string annotation `id: "relay.NodeID[int]"` for the stringified-NodeID accept test, and option (a) (delete) for the Slice 2 skipped test; (b) sweep the verbatim KANBAN body's present-tense action verbs to past tense for consistency with the rest of `KANBAN.md`'s `DONE-*` entries; (c) clarify pre-Slice-1 vs. post-Slice-1 line-number references throughout so post-implementation readers can match against the right snapshot.
- **Revision 7** (post-rev6 review) — one high-severity correction plus two medium and one low cleanup:
  1. **H1**: rev6's `_id_annotation_is_relay_node_id` fail-soft accept path for unresolved NodeID-shaped strings is two-pronged broken. First, the `"NodeID[" in raw` substring check accepts typo shapes that contain "NodeID[" as a non-token substring — e.g., `id: "NotNodeID[int]"` (a typo of a custom class) or `id: "MyNodeID[int]"` (a non-Strawberry NodeID alias) syntactically match and the guard accepts, but the consumer's intent was none of "use the Relay escape hatch". Second, the contract framing implies end-to-end acceptance (the test asserts `finalize_django_types()` and `strawberry.Schema(...)` succeed), but the fail-soft path only suppresses the package's own `ConfigurationError`; Strawberry's downstream schema construction still resolves Relay annotations against `cls`'s module globals using its own machinery, and an unresolved string annotation (whether NodeID-shaped or not) will fail there too — the existing test happens to pass because `relay` IS imported at module scope and the string resolves cleanly via Strawberry's path. The end-to-end success is therefore conflated between the resolved-string and fail-soft sub-cases. Fix: (a) tighten the substring predicate to a token-shaped regex like `(?:^|\.)NodeID\[` so prefixed-substring false positives are rejected; (b) split `test_consumer_id_string_relay_nodeid_annotation_on_relay_node_type_is_accepted` into two tests with distinct end-to-end contracts — one for the resolved string form (`relay` imported at module scope; assert finalize+schema build) renamed to `test_consumer_id_resolved_string_relay_nodeid_annotation_on_relay_node_type_is_accepted_end_to_end`, and one for the unresolved NodeID-shaped string form (`relay` NOT imported in the test class's resolution scope; assert ONLY that class creation succeeds, since Strawberry's downstream resolution remains the consumer's responsibility) named `test_consumer_id_unresolved_nodeid_shaped_string_on_relay_node_type_passes_guard_only`; (c) add a new reject test `test_consumer_id_typo_lookalike_nodeid_string_on_relay_node_type_raises` pinning that `id: "NotNodeID[int]"` (and similar prefixed-substring shapes) are rejected by the tightened predicate. Net test delta: +2 (one rename, one split, one new reject).
  2. **M1**: rev6's `test_inherited_id_annotation_on_relay_node_subclass_is_not_caught_by_guard` test asserts Strawberry's `ValueError` fires at `strawberry.Schema(...)` construction when an inherited `id: int` annotation on a no-`Meta` base `DjangoType` flows through to a Relay-Node-shaped child. That does not match the current pipeline: `_build_annotations`'s `suppress_pk_annotation and field.name == pk_name` branch at `types/base.py:651-657` (pre-Slice-1) suppresses the synthesized scalar annotation for the pk field on any Relay-Node-shaped type. The post-merge line `cls.__annotations__ = {**synthesized, **consumer_annotations}` at `types/base.py:138` replaces the child's `__annotations__` with the merge result — which contains neither the inherited `id: int` (because the child's own `consumer_annotations` doesn't have it) nor a synthesized `id` annotation (because pk-suppression skipped it). Strawberry's `@strawberry.type` reads the child's `__annotations__` (Strawberry walks the assigned dict, not `typing.get_type_hints`-style MRO collection for this purpose), sees no `id`, applies Relay's interface-supplied `id: GlobalID!`, and `resolve_id_attr()` falls back to `"pk"` because the inherited `id: int` is not a `relay.NodeID[...]`-marked annotation. Schema construction succeeds. Fix: invert the test contract. Rename to `test_inherited_id_annotation_on_relay_node_subclass_is_handled_by_pk_suppression` and assert: (a) no `ConfigurationError` at class creation; (b) `strawberry.Schema(query=Query, types=[ChildRelayType])` succeeds; (c) introspecting `ChildRelayType.id` returns `ID!` (the Relay-supplied interface field); (d) optionally, `ChildRelayType.resolve_id_attr() == "pk"`. Update every spec sentence around the inheritance corner case in the rev6 entry, Decision 7 prose, Slice 1 checklist, KANBAN body, CHANGELOG entry, edge-cases section, and test strategy.
  3. **M2**: rev6's sibling-field workaround examples (in the assigned-side error message, the Decision 7 Contract paragraph, the KANBAN body, the CHANGELOG `Changed` entry, the Slice 5 FEATURES.md update text, and the Definition of done) all use the shape `display_id: ID = strawberry.field(description="…")`. That attaches GraphQL field-level metadata but does not define a value source: `display_id` is not a Django model field, so Strawberry's default resolver looks up `display_id` as an attribute on the returned model instance and fails at query time. The error-message example should not point at a field shape that is likely to build but fail when queried. Fix: rewrite every sibling-field example to be resolver-backed — preferred form is the decorator `@strawberry.field(description="…") def display_id(self) -> strawberry.ID: return str(self.pk)` (or equivalent), with `strawberry.field(resolver=..., description="…")` as the equivalent function-call form. Update the assigned-side error message wording, the KANBAN body, the CHANGELOG `Changed` entry, the Slice 5 FEATURES.md update, and the Definition of done.
  4. **L1**: rev6's "Choice-enum fields" edge-case bullet at the bottom of the Edge cases section says the cross-type cache behavior change is pinned by `test_annotation_override_of_grouped_choices_field_is_allowed` — that test asserts the **single-type** case (`registry.get_enum` is None after one overriding type). The rev6 L2 entry added a dedicated cross-type test, `test_annotation_override_does_not_populate_shared_enum_cache_for_co_resident_types`, which is the actual pin for the two-type cache behavior. Fix: update the edge-case bullet's closing sentence to name the cross-type cache test as the behavior pin (the grouped-choices test still pins the single-type bypass; the cross-type test pins the two-type cache interaction).

## Key glossary references

Skim these [`docs/FEATURES.md`](FEATURES.md) entries first — they anchor the vocabulary used throughout the spec:

- [`DjangoType`](FEATURES.md#djangotype) — the base class whose scalar-override gap this card closes.
- [`Scalar field conversion`](FEATURES.md#scalar-field-conversion) — the auto-synthesized scalar annotation path this card lets consumers override.
- [`Scalar field override semantics`](FEATURES.md#scalar-field-override-semantics) — currently `planned for 0.0.6`; flipped to `shipped (0.0.6)` in [Slice 5](#slice-5--docs-kanban-changelog-archive).
- [`Specialized scalar conversions`](FEATURES.md#specialized-scalar-conversions) — home of the `ArrayField`, `HStoreField`, and `BigInt` mappings whose rejection paths the H2 converter-bypass contract explicitly skips for overridden fields.
- [`Relation handling`](FEATURES.md#relation-handling) — the relation-override path whose annotation-only contract this card mirrors for scalars.
- [`Relay Node integration`](FEATURES.md#relay-node-integration) — the broader Relay contract the H1 collision guard protects; documents `relay.NodeID[...]` as the supported consumer escape hatch.
- [`Definition-order independence`](FEATURES.md#definition-order-independence) — the foundation slice (`DONE-006-0.0.4`) that pinned the relation-field override contract; this card extends the same shape to scalars.
- [`ConfigurationError`](FEATURES.md#configurationerror) — raised at type-creation time for unsupported shadow shapes; this card adds one new error site (the Relay collision guard in Slice 1 per [Decision 7](#decision-7--relay-id-override-collision)).

Project conventions to follow:

- [`AGENTS.md`](../AGENTS.md) — schema testing via `schema.execute_sync`. **Note:** `AGENTS.md` prohibits `CHANGELOG.md` edits without explicit permission; [Slice 5](#slice-5--docs-kanban-changelog-archive) grants that permission.
- [`CONTRIBUTING.md`](../CONTRIBUTING.md) — 100% coverage target; release-bump checklist.
- [`KANBAN.md`](../KANBAN.md) — card-ID format; column movement at Slice 5.
- [`docs/TREE.md`](TREE.md) — package layout; tests mirror source one-to-one.

## Slice checklist

Each top-level item maps to one commit in the [Implementation plan](#implementation-plan).

- [ ] Slice 1: Track annotation-only scalar overrides on `DjangoTypeDefinition`
  - [ ] In `django_strawberry_framework/types/base.py:95-108`, collect a new `consumer_annotated_scalar_fields` frozenset in `DjangoType.__init_subclass__` parallel to `consumer_annotated_relation_fields`. Walks the same `consumer_annotations = dict(getattr(cls, "__annotations__", {}))` mapping but filters on `not field.is_relation` instead of `field.is_relation`. (See [Decision 1](#decision-1--annotation-only-scalar-override-collection).)
  - [ ] Add `consumer_annotated_scalar_fields: frozenset[str] = frozenset()` field to `django_strawberry_framework/types/definition.py:DjangoTypeDefinition` in the **grouped-by-style** order (L1 fix; matches Decision 3's sample): annotated-relation, annotated-scalar, assigned-relation, assigned-scalar. Worker 1 lands the cosmetic re-order of the existing two `consumer_assigned_*` lines in the same commit as the new field so the dataclass field order is internally consistent.
  - [ ] Union the new set into the existing `consumer_authored_fields` frozenset at `types/base.py:102-108`. The scalar branch of `_build_annotations` already short-circuits on `consumer_authored_fields` membership (`types/base.py:644`) — once annotation-only scalars are members, synthesis is skipped for them, and the existing post-merge line `cls.__annotations__ = {**synthesized, **consumer_annotations}` at `types/base.py:138` leaves the consumer's annotation untouched. **No change to `_build_annotations` body.**
  - [ ] Plumb the new set through to `DjangoTypeDefinition` at the registration call site (`types/base.py:117-134`).
  - [ ] **Relay `id` collision guard (H1 fix, rev4 pinned class-creation-time + assigned-id rejection; rev6 sibling-field workaround in error message + rev6 H1 fail-soft fix).** After the `consumer_annotated_scalar_fields` / `consumer_assigned_scalar_fields` collections are built but before `_build_annotations` is invoked, detect: (a) `interfaces` (from `_validate_meta`) includes `relay.Node` — checked the same way `_build_annotations` does it at `types/base.py:609` (pre-Slice-1), via `any(issubclass(i, relay.Node) for i in interfaces) or issubclass(cls, relay.Node)`; AND (b) the consumer authored an entry for the GraphQL field name `"id"` — either an annotation (`"id" in cls.__annotations__` — rev4 M2: key-presence rather than value-truthiness so unusual annotations like `id: None`, `id: Literal[None]`, or string forms that evaluate to false-y types are also detected; rev6 M3 corrected the rev4 M2 rationale, which described the value as "literally None" — Python actually evaluates `None` to `<class 'NoneType'>`) or an assignment (`isinstance(cls.__dict__.get("id"), StrawberryField)`). Two reject paths:
    - **Assigned `id = <StrawberryField>`**: always rejected on a Relay-Node-shaped type. The error message names three supported alternatives (rev6 M1 + rev7 M2): `@classmethod resolve_id` for a custom id resolver, `id: relay.NodeID[<pk_type>]` for a custom id annotation, and a **resolver-backed sibling field** — e.g., `@strawberry.field(description="…") def display_id(self) -> strawberry.ID: return str(self.pk)` — for the field-level GraphQL metadata use case (rev4 M1 banned `id = strawberry.field(description="…")`, rev6 M1 acknowledged this removed the only field-metadata path for the Relay-supplied `id`, and rev7 M2 corrected the workaround example from the metadata-only `display_id: ID = strawberry.field(description="…")` form — which would build but fail at query time because `display_id` is not a Django attribute on the model instance — to the resolver-backed form that carries the metadata AND defines a value source). Rev4 M1: this is a small intentional behavior change — previously consumers could write `@strawberry.field def id(self) -> relay.GlobalID: ...` and Strawberry would accept it. This card bans that pattern uniformly.
    - **Annotation `id: <type>` where `<type>` is not `relay.NodeID[...]`**: rejected. Detection of "is `relay.NodeID[...]`" uses `typing.get_type_hints(cls, include_extras=True)` (NOT raw `typing.get_args(cls.__annotations__["id"])`) so stringified annotations and PEP 563 (`from __future__ import annotations`) forms are evaluated against `cls`'s module globals. Fail-soft on `NameError`/`AttributeError`: the fail-soft scoping covers two sub-cases — (i) the `id` annotation itself is an unresolved string, accept only when the string matches the rev7 H1 token-shaped regex `(?:^|\.)NodeID\[` (not the rev6 plain-substring `"NodeID["` check, which accepted prefixed-substring lookalikes like `"NotNodeID[int]"` as false positives); (ii) some OTHER annotation on the class failed to resolve while `id` is directly resolved (rev6 H1 fix: fall back to `_has_node_id_marker(raw)` rather than rejecting on the not-a-string branch — the rev5 logic falsely rejected valid escape hatches in this case). The fail-soft accept window in sub-case (i) is package-level guard suppression only — Strawberry's downstream schema construction still resolves the same string against `cls`'s module globals and may fail there if the consumer hasn't made the symbol importable. The error message points at `relay.NodeID[<pk_type>]` as the supported escape hatch. (See [Decision 7](#decision-7--relay-id-override-collision) for the detection-helper pseudocode and the dropped finalize-time alternative.) **Important: the predicate is keyed off the GraphQL field name `"id"`, not the model's pk name.** A model with `code = models.CharField(primary_key=True)` and a consumer `code: str` override does NOT trigger the guard — the GraphQL fields are `id: ID!` (from Relay) and `code: String!` (from the consumer), no collision.
  - [ ] Tests in `tests/types/test_definition_order.py` (the existing override-contract host, where the three relation-override tests at `:179`, `:206`, `:235` live, plus the `:278` `test_assigned_scalar_field_override_keeps_consumer_resolver` test). The annotation-only scalar contract is the natural fourth sibling; placement matches the existing relation/scalar/annotation/assigned 2×2 matrix:
    - [ ] `test_annotation_only_scalar_field_override_wins_over_synthesized` (the headline test for this card): declare a `DjangoType` with a Django `CharField` selected and a consumer annotation `description: int` shadowing it. Pre-finalize, assert `cls.__annotations__["description"] is int`. Post-finalize, assert the same — and assert the Strawberry definition's field type matches the consumer's annotation, not the auto-synthesized `str`. This is the test currently skipped at `tests/types/test_base.py:444-465` (rename / move and unskip — see Slice 2).
    - [ ] `test_annotation_only_scalar_override_populates_definition_metadata`: assert `definition.consumer_annotated_scalar_fields == frozenset({"description"})`, `definition.consumer_authored_fields >= frozenset({"description"})`, and `definition.consumer_assigned_scalar_fields == frozenset()` (annotation-only, no assignment).
    - [ ] `test_annotation_only_scalar_override_does_not_emit_synthesized_annotation`: assert the synthesized annotations dict returned by `_build_annotations` does NOT contain `"description"` for the override case. (Pins that the short-circuit fires; without this we could still merge consumer-over-synthesized but the side-effect of double-walking the field path could regress later.)
    - [ ] `test_annotation_only_scalar_override_survives_strawberry_finalization` (M1 fix — unwrap through `NON_NULL`): the historical skip-reason at `tests/types/test_base.py:444-453` claimed Strawberry's `@strawberry.type` decorator regenerates `cls.__annotations__` after our merge. The current `__init_subclass__` already merges `{**synthesized, **consumer_annotations}` at `types/base.py:138` (consumer last so consumer wins), but the pre-Slice-1 single-source `synthesized` dict still contained the auto-mapped scalar annotation for the field name. Under this card, the synthesized dict no longer contains the consumer-overridden field, so the merge degenerates to "consumer annotation only" — no Strawberry-side regeneration can override it because there's nothing for it to fall back to. This test calls `[finalize_django_types](FEATURES.md#finalize_django_types)()`, builds a `strawberry.Schema(query=Query)` with a query field returning the type, and runs `schema.execute_sync(...)` against an introspection query of the shape `__type(name: "<TypeName>") { fields { name type { kind name ofType { kind name } } } }`. A non-nullable Django scalar surfaces in GraphQL as `Int!` — `type.kind == "NON_NULL"` and `type.name is None`; the terminal scalar name (`"Int"`) lives at `type.ofType.name`. The test unwraps through `NON_NULL` and asserts the terminal `ofType.name` matches the consumer's annotation. Worker 1 may instead reuse the existing `_introspect_field_type` helper pattern at `tests/types/test_converters.py:434` if the surface is a closer fit — the contract is "unwrap to the terminal type and assert that". Pins the end-to-end contract.
    - [ ] **Converter-bypass regressions (H2 fix; four new tests, rev6 L2 — added cross-type cache test).** The new short-circuit skips `convert_scalar(...)` for the overridden field, which means every converter-side validation and side effect is bypassed for that field. The bypass is the intended consumer-authoritative contract (see [Decision 7a](#decision-7a--converter-validation-bypass-h2-fix)), but the spec needs explicit tests that pin it so future readers understand the surface and so converter changes do not silently re-introduce validation against an overridden field:
      - [ ] `test_annotation_override_of_unsupported_scalar_field_type_is_allowed` (rev2 M1 fix — use Strawberry-supported consumer annotation): declare a `DjangoType` selecting a synthetic `_FakeUnsupportedField(models.Field)` fixture (or any Django field type whose MRO has no `SCALAR_MAP` match). Without the override, `convert_scalar` raises `ConfigurationError`. With a consumer `myfield: str` annotation (or `int` — any Strawberry-supported scalar annotation; **NOT** `bytes`, which Strawberry's schema-construction pass rejects as an unexpected Python type and would create a false test failure unrelated to the bypass contract), assert: (a) no error is raised at class-creation time, (b) `definition.consumer_annotated_scalar_fields` contains the field name, and (c) `finalize_django_types()` succeeds. The consumer's override is the recourse for unsupported scalars; `Meta.exclude` is still the recourse for "drop the field entirely".
      - [ ] `test_annotation_override_of_grouped_choices_field_is_allowed`: declare a `DjangoType` selecting a Django `CharField` with grouped `choices=[("group1", [("a", "A"), ("b", "B")])]`. Without the override, `convert_choices_to_enum` raises `ConfigurationError` containing `"grouped-choices"` (existing test `tests/types/test_converters.py:test_grouped_choices_form_rejected` pins this). With a consumer `status: str` annotation, assert no error is raised, the type is finalizable, and `registry.get_enum(model, "status")` is `None` (enum registration is bypassed along with annotation synthesis).
      - [ ] `test_annotation_override_of_arrayfield_with_nested_array_is_allowed` (rev3 M2 placement; rev4 L2 name-match; rev6 L3 — placement (a) is the default): real `django.contrib.postgres.fields.ArrayField` testing requires the `_ARRAY_FIELD_CLS` monkeypatch + `_FakeArrayField` fixture pattern that lives in `tests/types/test_converters.py:449-1100` (every existing `ArrayField` test uses it; the production code at `types/converters.py:91` soft-imports the real class and CI environment-dependence is the failure mode without the monkeypatch). **Default: place this single test in `tests/types/test_converters.py` beside the existing `_FakeArrayField` tests** so the fixture lookup stays local (smaller-touch). The alternative (b) — placement in `tests/types/test_definition_order.py` with a re-import or duplicate of `_FakeArrayField` — is no longer recommended; Worker 1 may pick (b) only if a planning-time concern surfaces. **The model-field name and the consumer-annotation name MUST match** (rev4 L2) — mirror the existing converter tests' `arr`-named field, so the consumer annotation is `arr: list[list[int]]`. A name mismatch means the override-collection path never fires (the consumer annotation does not name a selected model field) and the test exercises the rejection path instead — false-passing for the wrong reason. Test body: `monkeypatch.setattr(converters, "_ARRAY_FIELD_CLS", _FakeArrayField)`; build a `_FakeArrayField(_FakeArrayField(models.IntegerField()))` instance registered as a model field named `arr`; declare a `DjangoType` selecting that field with a consumer `arr: list[list[int]]` annotation; assert no error is raised at class-creation time and `finalize_django_types()` succeeds. Verify that the existing `tests/types/test_converters.py:1021` nested-array rejection test still passes (un-overridden nested arrays still raise).
      - [ ] `test_annotation_override_does_not_populate_shared_enum_cache_for_co_resident_types` (rev6 L2 — cross-type cache behavior change): pins the rev5 Decision 7a flag that two `DjangoType`s on the same model with the same `choices=` column — one overriding and one not — get the fresh enum from the non-overriding type alone. Declare a single Django model with a non-grouped `status` `CharField(choices=[...])`. Declare two `DjangoType`s on that model: `OverrideType` with `class Meta: model = M; primary = True; fields = ("status",)` and a consumer `status: str` annotation (override); `NonOverrideType` with `class Meta: model = M; fields = ("status",)` (no override). `finalize_django_types()`. Assert: (a) `registry.get_enum(model, "status")` returns a non-`None` enum class (populated by `NonOverrideType`'s `convert_scalar` call); (b) building a `strawberry.Schema` and introspecting `NonOverrideType.status` returns the generated enum's GraphQL name; (c) introspecting `OverrideType.status` returns `String!` (the consumer's annotation). Pins both halves of the contract — the bypass on the overriding type does not poison the cache for the non-overriding type, and the cache entry from the non-overriding type does not leak into the overriding type's GraphQL surface. Test placement: `tests/types/test_definition_order.py` (the override-contract host) or `tests/types/test_converters.py` (beside the existing cache tests) — Worker 1 picks during planning; default is the override-contract host because the test exercises the cross-type override surface.
  - [ ] **Relay collision tests (H1 fix; ten new tests, rev6 + rev7 expanded — rev6 added H1 sibling-annotation accept and L1 inheritance non-trigger; rev7 split the stringified-NodeID accept test into resolved-end-to-end and unresolved-guard-only variants, added a typo-lookalike reject test, and inverted the inheritance test to assert schema succeeds via pk-suppression).** New tests in `tests/types/test_definition_order.py` alongside the four-corner cluster:
    - [ ] `test_consumer_id_annotation_on_relay_node_type_raises`: declare a `DjangoType` with `Meta.interfaces = (relay.Node,)` and an `id: int` (or `id: str`) consumer annotation. Assert `ConfigurationError` raised at class-creation time (before `finalize_django_types()`), with message containing both `"relay.NodeID"` and `"GlobalID"`. Pins the early-raise contract; without H1's guard, the consumer would see a Strawberry-side `ValueError` only at `strawberry.Schema(...)` construction, which is the wrong UX surface.
    - [ ] `test_consumer_id_assigned_strawberry_field_on_relay_node_type_raises` (rev4 M1 assigned-id rejection; rev6 M1 + rev7 M2 sibling-field workaround in error message): declare a `DjangoType` with `Meta.interfaces = (relay.Node,)` and an assigned `id = strawberry.field(resolver=...)` (or `@strawberry.field def id(self) -> relay.GlobalID: ...` decorator-style). Assert `ConfigurationError` raised at class-creation time with message containing **all three** of `"resolve_id"`, `"relay.NodeID"`, and one of `"display_id"` / `"sibling field"` (rev7 M2 — the resolver-backed sibling field is the documented workaround for the metadata-only assigned-`id` use case). Pins the intentional ban on assigned `id` overrides on Relay-Node-shaped types and the rev6 M1 + rev7 M2 resolver-backed sibling-field workaround in the error message.
    - [ ] `test_consumer_id_unresolved_non_nodeid_string_on_relay_node_type_raises` (rev5 M1 unresolved-non-NodeID-string rejection): declare a `DjangoType` with `Meta.interfaces = (relay.Node,)` and a stringified `id: "MissingType"` annotation (where `MissingType` is not imported and not a NodeID — e.g., a typo or a forward reference to a non-existent class). Assert `ConfigurationError` raised at class-creation time with message containing both `"relay.NodeID"` and `"GlobalID"`. Pins the narrow rev5 fail-soft contract under the rev7 H1 tightened predicate: `typing.get_type_hints` raises `NameError` for this annotation, the helper inspects the raw string at `cls.__annotations__["id"]`, fails to match the `(?:^|\.)NodeID\[` regex, and rejects. Without this test, a typo like `id: "Stirng"` would slip past the guard at class-creation time and surface only as a Strawberry schema-construction error later — exactly the failure mode H1 exists to prevent. (The companion rev7 `test_consumer_id_typo_lookalike_nodeid_string_on_relay_node_type_raises` covers the rev7 H1 regex-specific rejection of prefixed-substring lookalikes like `"NotNodeID[int]"`; this rev5 test covers the broader "non-NodeID-shaped unresolved string" case.)
    - [ ] `test_consumer_id_typo_lookalike_nodeid_string_on_relay_node_type_raises` (rev7 H1 — tightened predicate rejects prefixed-substring lookalikes): declare a `DjangoType` with `Meta.interfaces = (relay.Node,)` and a stringified `id: "NotNodeID[int]"` annotation (where `NotNodeID` is not imported and not Strawberry's `NodeID`; the prefix means the string DOES contain `"NodeID["` as a substring but is NOT a token-shaped NodeID reference). Assert `ConfigurationError` raised at class-creation time with message containing both `"relay.NodeID"` and `"GlobalID"`. Worker 1 should also verify a `"MyNodeID[int]"` variant in the same test (parametrize or add a second assertion). Pins the rev7 H1 tightening: `_NODEID_STRING_RE = re.compile(r"(?:^|\.)NodeID\[")` requires a start-of-string or dot-boundary before `NodeID[`; the substring `NodeID[` inside `NotNodeID[` does not match. Without the regex tightening, the rev6 `"NodeID[" in raw` substring check would have accepted this false-positive and the consumer's typo would have slipped past the package guard.
    - [ ] `test_consumer_id_relay_nodeid_annotation_on_relay_node_type_is_accepted` (rev3 H1 escape-hatch acceptance): declare a `DjangoType` with `Meta.interfaces = (relay.Node,)` and an `id: relay.NodeID[int]` consumer annotation. Assert no `ConfigurationError` at class-creation time; assert `finalize_django_types()` succeeds; assert `strawberry.Schema(...)` builds. Pins that the guard does NOT reject the advertised escape hatch. Mirrors the existing `tests/types/test_relay_interfaces.py:240`'s `test_composite_pk_with_explicit_node_id_annotation_is_accepted` pattern, but applies to a plain (non-composite-pk) Relay-Node-shaped type to specifically exercise this card's guard.
    - [ ] `test_consumer_id_resolved_string_relay_nodeid_annotation_on_relay_node_type_is_accepted_end_to_end` (rev4 H1 string-annotation acceptance; rev6 L3 — explicit string annotation is the default; rev7 H1 — renamed/split for resolved end-to-end contract): declare a `DjangoType` with `Meta.interfaces = (relay.Node,)` and an explicit stringified `id: "relay.NodeID[int]"` consumer annotation, **with `relay` imported at module scope** so the string resolves cleanly under both `typing.get_type_hints(cls, include_extras=True)` (the package's guard) AND Strawberry's downstream schema-construction resolution. Assert no `ConfigurationError` at class-creation time; assert `finalize_django_types()` succeeds; assert `strawberry.Schema(...)` builds; assert the introspected `id` field is `ID!` (the Relay-supplied interface field). Pins that the `typing.get_type_hints(cls, include_extras=True)` detection helper resolves stringified annotations correctly **and** Strawberry's downstream pipeline accepts the same string. This is the resolved-string end-to-end contract.
    - [ ] `test_consumer_id_unresolved_nodeid_shaped_string_on_relay_node_type_passes_guard_only` (rev7 H1 — fail-soft sub-case-1 split): declare a `DjangoType` with `Meta.interfaces = (relay.Node,)` and an explicit stringified `id: "relay.NodeID[int]"` consumer annotation, **with `relay` NOT importable** from the class's resolution scope (e.g., the test creates the class via `types.new_class(...)` with a custom module spec, or constructs the class in a `__module__` whose globals do not include `relay`). Assert ONLY that class creation succeeds — no `ConfigurationError` at `__init_subclass__` time — because the fail-soft branch matches the `(?:^|\.)NodeID\[` regex on the raw string and suppresses the guard. **Do NOT assert** `finalize_django_types()` or `strawberry.Schema(...)` succeed; Strawberry's downstream resolution operates against the same module globals and will fail with its own error if the consumer has not made `relay` resolvable. The spec contract for this case is "package guard suppressed at class-creation time"; full end-to-end resolution is the consumer's responsibility. Worker 1 picks the precise test recipe for "make `relay` unresolvable in cls's scope" during planning — recommended options are (a) a synthetic stub module created via `types.ModuleType("stub_mod")` with selective globals, or (b) a `typing.TYPE_CHECKING`-style import where the test asserts the string-form guard suppression without actually attempting schema construction. The contract is "class creation succeeds; schema build is not promised".
    - [ ] `test_consumer_id_resolved_relay_nodeid_with_unresolved_sibling_annotation_is_accepted` (rev6 H1 — fail-soft H1-sub-case-2 acceptance): declare a `DjangoType` with `Meta.interfaces = (relay.Node,)`, a directly-resolved `id: relay.NodeID[int]` consumer annotation, AND a forward-referenced sibling annotation like `items: list["AdminItemType"]` (or any annotation that doesn't resolve at class-creation time). Assert no `ConfigurationError` at class-creation time. Pins the rev6 H1 fix: when `typing.get_type_hints(cls, include_extras=True)` raises `NameError` because of the sibling annotation, the helper's fail-soft branch sees `cls.__annotations__["id"]` is an already-resolved `Annotated[int, NodeIDPrivate]` object (not a string), falls back to `_has_node_id_marker(raw)`, recognizes the marker, and accepts. Without this test, the rev5 fail-soft logic would silently false-positive-reject `id: relay.NodeID[int]` whenever any other annotation on the class fails to resolve — a realistic pattern for `DjangoType`s with forward-referenced relation annotations.
    - [ ] `test_consumer_non_id_scalar_override_on_relay_node_type_is_accepted` (rev3 H1 custom-pk acceptance; rev6 L3 — `description: int` recipe is the default): declare a `DjangoType` on a Relay-Node-shaped type with a non-`id` consumer scalar override (use **`description: int` as the recipe**; the monkeypatched `code = models.CharField(primary_key=True)` alternative is no longer recommended because it requires a fixture monkeypatch for marginal value). Assert no `ConfigurationError` is raised. Pins that the guard is keyed off the GraphQL field name `"id"`, not the model's pk name — a consumer who overrides a non-`id` field on a Relay-Node-shaped type does not collide with `Node.id` and must not be rejected.
    - [ ] `test_inherited_id_annotation_on_relay_node_subclass_is_handled_by_pk_suppression` (rev6 L1 + rev7 M1 — inverted contract: schema construction succeeds, not raises): declare a base `DjangoType` subclass `BaseWithId` with `id: int` annotation but no `Meta` (so `__init_subclass__` short-circuits the collection pipeline for the base). Then declare a child `ChildRelayType(BaseWithId)` with `class Meta: model = M; interfaces = (relay.Node,)`. Assert: (a) no `ConfigurationError` at class-creation time — the rev6 L1 guard predicate `"id" in cls.__annotations__` is False for the child (inherited annotations don't land in the subclass's own `__annotations__` dict); (b) **`strawberry.Schema(query=Query, types=[ChildRelayType])` SUCCEEDS** (rev7 M1 — this inverts the rev6 contract). `_build_annotations`'s `suppress_pk_annotation and field.name == pk_name` branch at `types/base.py:651-657` (pre-Slice-1) suppresses the synthesized scalar `id` annotation for the child, and the post-merge line at `types/base.py:138` (pre-Slice-1) replaces the child's `__annotations__` with `{**synthesized, **consumer_annotations}` — which contains neither the inherited `id: int` nor a synthesized one. Strawberry's `@strawberry.type` reads the child's assigned `__annotations__` and sees no `id`, applies Relay's `id: GlobalID!`, and `resolve_id_attr()` falls back to `"pk"`; (c) the introspected `id` field type is `ID!` (the Relay-supplied interface field), not `Int!`; (d) optionally, `ChildRelayType.resolve_id_attr() == "pk"`. Pins the corrected inheritance behavior — the H1 guard does NOT walk the MRO (rev6 L1 framing was correct on this point) but **pk-suppression in `_build_annotations` silently handles the inherited `id: int` case**, so Strawberry's `ValueError` does NOT fire (rev6 L1's downstream-failure claim was wrong; rev7 M1 corrects it). Without this test, future changes to the pk-suppression branch could regress the inherited-`id` corner without surfacing.
- [ ] Slice 2: Unskip / replace `test_consumer_annotation_overrides_synthesized`
  - [ ] Remove the `@pytest.mark.skip` decorator and its reason text at `tests/types/test_base.py:444-453`.
  - [ ] **Default (rev6 L3): delete the test body** at `tests/types/test_base.py:454-465` because Slice 1's new tests cover the contract more thoroughly. The alternative — keep as a smoke-test sibling alongside the Slice 1 tests — is no longer recommended. `tests/types/test_definition_order.py` is the canonical override-contract host and a one-line smoke test sitting alone in `test_base.py` would invite future drift between the two locations. Worker 1 may override during planning if a strong reason surfaces, but the default is delete.
  - [ ] If the body was deleted above, also remove the `CATEGORY_SCALAR_FIELDS` reference if it becomes unused (check via `grep` before deleting).
- [ ] Slice 3: Document the four-corner override contract in `_consumer_assigned_fields`'s docstring
  - [ ] After Slice 1 lands, the four-corner override matrix (`relation × annotation`, `relation × assigned`, `scalar × annotation`, `scalar × assigned`) is symmetric and complete. Update the `_consumer_assigned_fields` docstring at `types/base.py:211-220` so it names the parallel `consumer_annotated_relation_fields` / `consumer_annotated_scalar_fields` collection sites in `__init_subclass__`, the four `consumer_*_fields` sets on `DjangoTypeDefinition`, and the single `consumer_authored_fields` short-circuit in `_build_annotations`. This is documentation only — no behavior change. Worker 1 verifies no other docstrings need parallel updates (likely `_build_annotations` already documents the relation+scalar consumer-authored branches; if it does, no change there either).
- [ ] Slice 4: Atomic version-bump quintet (single commit). Same shape as `spec-013-deferred_scalars-0_0_6.md` Slice 5 and `spec-014-meta_primary-0_0_6.md` Slice 5: covers programmatically-checked sites only (`pyproject.toml`, `__init__.py`, `tests/base/test_init.py`'s pinned `__version__`, `docs/FEATURES.md`'s "Current package version" line, `uv.lock`). The two consumer-facing version strings (`README.md`, `docs/README.md`) move in Slice 5. **At spec-authoring time the tree is already at `0.0.6` from `spec-013-deferred_scalars-0_0_6.md` and `spec-014-meta_primary-0_0_6.md`'s Slice 5**, so every checkbox below is expected to be a no-op. The slice still exists in the plan so the build cycle's Worker 1 final-verification pass explicitly `grep`s for stale `0.0.5` strings before marking complete.
  - [ ] `pyproject.toml` — `version = "0.0.6"` (no-op if already at `0.0.6` from any prior `0.0.6` card).
  - [ ] `django_strawberry_framework/__init__.py` — `__version__ = "0.0.6"` (no-op if already bumped).
  - [ ] `tests/base/test_init.py` — pinned `__version__` assertion to `"0.0.6"` (no-op if already bumped).
  - [ ] `docs/FEATURES.md` — "Current package version: `0.0.6`" line (no-op if already bumped).
  - [ ] `uv.lock` — re-lock with `uv lock` (no-op if already at `0.0.6`).
  - [ ] **Prior-`0.0.6`-card note.** `0.0.6` carries three cards (`spec-013-deferred_scalars`, `spec-014-meta_primary`, this card). The first card to land does the real bump; every subsequent card's Slice 4 is a no-op. The Worker 1 final-verification pass MUST `grep` for stale `0.0.5` strings rather than blindly editing — if the bump has already happened, mark every checkbox above complete without re-editing.
- [ ] Slice 5: Docs, KANBAN, CHANGELOG, archive (separate commit; may follow Slice 4 by any interval).
  - [ ] Root `README.md` — confirm the package-version line reads `0.0.6` (no-op if any prior `0.0.6` card already bumped it).
  - [ ] `docs/README.md` — confirm the "shipped today is `0.0.6`" line (no-op if any prior `0.0.6` card already bumped it). Add a one-line mention of scalar override symmetry to the shipped-capability summary.
  - [ ] `docs/FEATURES.md` entries updated:
    - [`Scalar field override semantics`](FEATURES.md#scalar-field-override-semantics) → `shipped (0.0.6)`. Rewrite the body to describe the actual delivered contract: annotation-only and assigned-`strawberry.field` scalar overrides both supported, with the same `consumer_authored_fields` short-circuit; opt-out via `Meta.exclude`; field metadata via the assigned-`strawberry.field(...)` path; **converter validations bypassed for overridden fields** (consumer-authoritative contract — name unsupported-scalar override, grouped-choices override, and nested-`ArrayField` override as the three behavior changes worth highlighting); **`relay.Node` `id` collision rejected at type-creation time**, with two sub-restrictions: (1) assigned `id = <StrawberryField>` overrides are uniformly rejected on Relay-Node-shaped types (the supported alternatives are `relay.NodeID[<pk_type>]` for a custom id annotation, `@classmethod resolve_id` for a custom id resolver, and a **resolver-backed sibling field** — `@strawberry.field(description="…") def display_id(self) -> strawberry.ID: return str(self.pk)` — for the field-level GraphQL metadata use case, since the rev6 M1 + rev7 M2 ban removes the only path for attaching `description`/`deprecation_reason`/`directives` to the Relay-supplied `id`; a metadata-only sibling like `display_id: ID = strawberry.field(description="…")` without a resolver would build but fail at query time because Strawberry's default resolver looks up `display_id` as an attribute on the returned model instance); (2) inherited `id` annotations on a Relay-Node-shaped subclass slip past the guard at class-creation time, and `_build_annotations`'s pk-suppression branch silently handles them — Strawberry sees no `id` annotation on the child, applies the Relay-supplied `id: GlobalID!`, and `resolve_id_attr()` falls back to `"pk"` (rev7 M1 correction; the rev6 framing of "Strawberry's downstream `ValueError` is the acknowledged failure mode" was wrong — schema construction actually succeeds). Annotation `id: relay.NodeID[...]` is accepted in direct, PEP 563 / stringified, and mixed (resolved-id-with-unresolved-sibling) forms; non-`id` overrides are accepted unchanged. Drop the "planned for `0.0.6`" framing.
    - [`Scalar field conversion`](FEATURES.md#scalar-field-conversion) (H2 fix) — the "Subclass MRO walk" paragraph and surrounding text frame unsupported scalar fields as `ConfigurationError` cases with `Meta.exclude` as the consumer recourse. Update to add annotation-only override as a parallel recourse: "or supply a consumer annotation override (see [Scalar field override semantics](#scalar-field-override-semantics))". Parallel update to any sibling sentences that mention grouped-choices rejection or `ArrayField` shape rejection — those continue to raise for the non-override path, but the override path is now also a recourse. Worker 1 reads the whole entry during planning to find all affected sentences.
    - [`Definition-order independence`](FEATURES.md#definition-order-independence) → remove the "Manual scalar-field override semantics remain an implementation detail until [Scalar field override semantics](#scalar-field-override-semantics) ships." closing sentence; the contract is now part of the foundation.
    - [`DjangoType`](FEATURES.md#djangotype) — review the "Current alpha constraints" bullet list (`docs/FEATURES.md:386-388`) and remove any scalar-override-related entry. Today the list only has the relation-cardinality-validation deferral; the spec author should verify nothing scalar-shaped is in there to drop.
    - [Index](FEATURES.md#index) → flip the status badge on `Scalar field override semantics` to `shipped (0.0.6)`.
  - [ ] `docs/TREE.md` — no source-tree changes (no new files); confirm the `types/base.py` and `types/definition.py` per-file annotations in the current-on-disk-layout block don't need updating. The `DjangoTypeDefinition` line in `definition.py` currently reads "canonical per-type metadata with [Meta.primary](FEATURES.md#metaprimary) flag and forward-reserved Layer-3 slots" (post-DONE-014); no update needed for this card — the new `consumer_annotated_scalar_fields` field is part of the same internal-metadata shape, not a new public capability.
  - [ ] `TODAY.md` — add scalar override semantics to the "shipped today" section. The fakeshop example does not currently exercise scalar annotation overrides; mention under "available but not currently demonstrated in fakeshop" if that subsection exists.
  - [ ] `KANBAN.md` — move `WIP-ALPHA-015-0.0.6` → `DONE-015-0.0.6`. **Drop in the verbatim body below:**

    ```markdown
    ### DONE-015-0.0.6 — Consumer override semantics (scalar fields)

    Slice-by-slice scope (per `docs/spec-015-consumer_overrides_scalar-0_0_6.md`):

    - `DjangoType.__init_subclass__` collected `consumer_annotated_scalar_fields`
      parallel to `consumer_annotated_relation_fields`. Annotation-only scalar
      overrides (e.g., `description: int` shadowing an auto-synthesized `str`)
      are added to the unified `consumer_authored_fields` frozenset and skip
      auto-synthesis in `_build_annotations`'s scalar branch via the existing
      `if field.name in consumer_authored_fields: continue` short-circuit.
    - `DjangoTypeDefinition` gained `consumer_annotated_scalar_fields: frozenset[str]`.
    - The previously-skipped `test_consumer_annotation_overrides_synthesized`
      landed as `test_annotation_only_scalar_field_override_wins_over_synthesized`
      in `tests/types/test_definition_order.py` alongside the three relation
      overrides and the assigned-scalar override. The four-corner matrix
      (relation × annotation, relation × assigned, scalar × annotation,
      scalar × assigned) is symmetric and complete.
    - End-to-end test pinned the override surviving `strawberry.type(...)`
      decoration and showing up in the GraphQL schema with the consumer's type
      (unwrapped through `NON_NULL` for non-nullable Django columns).
    - **Consumer annotation overrides are authoritative.** `_build_annotations`'s
      scalar short-circuit bypasses every `convert_scalar` validation and side
      effect for an overridden field: unsupported-field-type rejection,
      grouped-choices rejection, `ArrayField` nested-array / outer-`choices`
      rejection, `null=True` widening, and choice-enum registration into the
      shared `(model, field_name)` cache. The contract matches the existing
      relation-annotation override path (which also bypasses `convert_relation`
      entirely) and treats annotation override as the consumer's escape from
      auto-conversion. `Meta.exclude` and annotation override are now parallel
      recourses for unsupported scalar fields. Cross-type cache behavior was
      pinned by an explicit test: two `DjangoType`s on the same `choices=`
      column where one overrides and one does not get the fresh enum from
      the non-overriding type alone (the overriding type's GraphQL surface
      uses the consumer's annotation; the cache is populated only by the
      non-overriding type's `convert_scalar` call).
    - **`relay.Node` `id` collision rejected at type-creation time.** A consumer
      who writes `id: <T>` (where `<T>` is not `relay.NodeID[...]`) or assigns
      any `id = <StrawberryField>` on a `DjangoType` with
      `Meta.interfaces = (relay.Node,)` now raises `ConfigurationError` from
      `__init_subclass__`. The annotation-side error points at
      `relay.NodeID[<pk_type>]` and `GlobalID`; the assigned-side error
      points at `relay.NodeID[<pk_type>]`, `@classmethod resolve_id`, and a
      **resolver-backed sibling-field workaround** (e.g.,
      `@strawberry.field(description="…") def display_id(self) -> strawberry.ID: return str(self.pk)`
      for the field-level GraphQL metadata use case — the rev4 M1 ban on
      `id = <StrawberryField>` on Relay-Node-shaped types eliminated the
      only path for attaching `description`/`deprecation_reason`/
      `directives` to the Relay-supplied `id` field; rev6 M1 documented
      the sibling-field workaround and rev7 M2 corrected the example
      from the metadata-only `display_id: ID = strawberry.field(description="…")`
      shape — which would build but fail at query time because Strawberry's
      default resolver looks up `display_id` as an attribute on the
      returned Django model instance — to the resolver-backed form that
      carries the metadata AND defines a value source). Without the guard
      the consumer would have seen a Strawberry-side `ValueError` only at
      `strawberry.Schema(...)` construction, which obscured the source.
      The guard is narrow: it fires only when the consumer authored an
      `id` entry on a Relay-Node-shaped type AND the annotation is not a
      `relay.NodeID[...]`-marked annotation. Detection uses
      `typing.get_type_hints(cls, include_extras=True)` so direct, PEP
      563 / `from __future__ import annotations`, and explicit-string
      forms are all resolved against the consumer's module globals; the
      fail-soft branch covers two sub-cases — id-itself-failed-to-
      resolve (rev7 H1: accept only when the raw string matches the
      token-shaped regex `(?:^|\.)NodeID\[`, so prefixed-substring
      lookalikes like `"NotNodeID[int]"` are rejected) and id-resolved-
      but-sibling-failed (rev6 H1: fall back to `_has_node_id_marker(raw)`
      on the already-resolved object so directly-resolved `id:
      relay.NodeID[int]` alongside a forward-referenced relation
      annotation is accepted). The fail-soft accept window for unresolved
      NodeID-shaped strings is package-level suppression only; Strawberry's
      downstream schema construction also resolves the string and may
      still error if the consumer's module globals don't expose `relay`
      (rev7 H1). `id: relay.NodeID[int]` and `id: "relay.NodeID[int]"`
      (the documented escape hatch in direct and stringified forms, with
      `relay` importable at module scope) are accepted end-to-end; non-
      `id` consumer scalar overrides (e.g., `description: int`, or `code:
      str` on a model with `code` as pk) pass through unchanged;
      **inherited `id` annotations on a subclass slip past the guard at
      class-creation time and are silently handled by `_build_annotations`'s
      pk-suppression branch** (rev6 L1 + rev7 M1: the guard does not
      walk the MRO, but pk-suppression strips the synthesized `id`
      annotation for any Relay-Node-shaped type and the post-merge
      reassignment leaves the child without an `id` key; Strawberry
      applies the Relay-supplied `id: GlobalID!` and `resolve_id_attr()`
      falls back to `"pk"` — schema construction succeeds).
    - No new public API. No `Meta.field_overrides = {...}`-style key. Opt-out
      / removal continues to go through `Meta.exclude`. Field description /
      deprecation / default continues to go through the assigned
      `strawberry.field(...)` path that shipped in `0.0.5`.
    - 100% coverage was reached across `tests/types/test_definition_order.py`
      (the override-contract host, where the core + Relay-collision +
      cross-type-cache tests live) and `tests/types/test_converters.py`
      (the converter test host, where the nested-`ArrayField` bypass test
      lives by default per the rev6 L3 placement decision).

    Design notes carried into `0.0.6`:

    - The four `consumer_*_fields` sets on `DjangoTypeDefinition`
      (`consumer_annotated_relation_fields`, `consumer_assigned_relation_fields`,
      `consumer_annotated_scalar_fields`, `consumer_assigned_scalar_fields`) are
      the introspection surface. The unified `consumer_authored_fields` is the
      single short-circuit input for `_build_annotations`.
    - Resolver / metadata overrides for scalars stay on the assigned
      `strawberry.field(...)` path — the consumer writes
      `description = strawberry.field(resolver=..., description="...", deprecation_reason=...)`
      and `_consumer_assigned_fields` already routes it through the
      `consumer_assigned_scalar_fields` short-circuit. Field-level GraphQL
      metadata on the Relay-supplied `id` field is **not** configurable in
      `0.0.6` (the rev4 M1 / rev6 M1 / rev7 M2 assigned-`id` ban applies
      uniformly); the documented workaround is a **resolver-backed sibling
      field** (`@strawberry.field(description="…") def display_id(self) ->
      strawberry.ID: return str(self.pk)`) carrying both the metadata and
      a value source.
    - Type-annotation overrides are the consumer's responsibility for runtime
      correctness. `description: int` against a `CharField` will surface a
      Strawberry-side serialization error at query time if the database returns
      a non-integer value; the package does not pre-check annotation/field-type
      compatibility (out of scope for this card).
    ```
  - [ ] `CHANGELOG.md` — `[Unreleased]` entries (**permission granted by this spec**, overriding [`AGENTS.md`](../AGENTS.md)'s default prohibition):
    - `Added`: Annotation-only scalar field overrides on `DjangoType`. Writing `description: int` (or any other class-level scalar annotation that shadows a Django scalar column selected via [`Meta.fields`](FEATURES.md#metafields)) is now a stable public contract — the consumer's annotation wins over the auto-synthesized one and survives `finalize_django_types()` / `strawberry.type(...)` decoration. Mirrors the annotation-only relation-override path that has shipped since `0.0.4` (`DONE-006-0.0.4`).
    - `Added`: `DjangoTypeDefinition.consumer_annotated_scalar_fields: frozenset[str]` — introspection surface for the new override path; symmetric with the existing `consumer_annotated_relation_fields`, `consumer_assigned_relation_fields`, and `consumer_assigned_scalar_fields` sets.
    - `Changed`: Annotation-only and assigned scalar field overrides bypass `convert_scalar` validations and side effects for the overridden field — unsupported-field-type rejection, grouped-choices rejection, `ArrayField` shape rejection, `null=True` widening, and choice-enum registration are skipped. The consumer's annotation is authoritative. `Meta.exclude` and annotation override are now parallel consumer recourses for unsupported scalar fields.
    - `Added`: `ConfigurationError` raised at `DjangoType.__init_subclass__` time when a consumer authors an `id` annotation on a `Meta.interfaces = (relay.Node,)`-shaped type that is not a `relay.NodeID[...]`-marked annotation. Points at `strawberry.relay.NodeID[<pk_type>]` as the supported escape hatch. Replaces the downstream Strawberry-side `ValueError` ("Interface field Node.id expects type ID! but ...") that surfaced only at `strawberry.Schema(...)` construction. Narrow guard: `id: relay.NodeID[int]` is accepted in direct, stringified / PEP 563 / `from __future__ import annotations`, and mixed (directly-resolved `id` alongside other unresolved annotations on the same class) forms; non-`id` consumer scalar overrides on Relay-Node-shaped types (including custom-named primary keys like `code: str` on `models.CharField(primary_key=True)`) are accepted; inherited `id` annotations on a Relay-Node-shaped subclass also pass through at class-creation time (the guard does not walk the MRO) and are silently handled by `_build_annotations`'s pk-suppression branch — Strawberry applies the Relay-supplied `id: GlobalID!` and `resolve_id_attr()` falls back to `"pk"`, so schema construction succeeds. Detection uses `typing.get_type_hints(cls, include_extras=True)` with a fail-soft fallback for unresolved forward references that distinguishes "id itself failed to resolve" (accept only when the raw string matches the token-shaped regex `(?:^|\.)NodeID\[`, so prefixed-substring lookalikes like `"NotNodeID[int]"` are rejected) from "id is directly resolved but another annotation failed" (inspect the resolved object via `_has_node_id_marker`). The fail-soft accept window for unresolved NodeID-shaped strings is package-level guard suppression only — Strawberry's downstream resolution against `cls`'s module globals still applies.
    - `Changed`: `id = <StrawberryField>` assignment on a `Meta.interfaces = (relay.Node,)`-shaped `DjangoType` now raises `ConfigurationError` at `__init_subclass__` time. Previously consumers could write `@strawberry.field def id(self) -> relay.GlobalID: ...` (or `id = strawberry.field(description="…")`) and the resulting schema would build because the assigned-field type matched `Node.id: ID!`; this card uniformly rejects assigned `id` overrides on Relay-Node-shaped types for consistency with the annotation-side guard. The supported alternatives are `@classmethod resolve_id` (custom id resolver), `id: relay.NodeID[<pk_type>]` (custom id annotation), and a **resolver-backed sibling field** for the field-level GraphQL metadata use case (declare a separate field with a resolver — e.g., `@strawberry.field(description="…") def display_id(self) -> strawberry.ID: return str(self.pk)` — carrying the metadata AND a value source; the Relay-supplied `id` stays undecorated). Field-level metadata on the Relay-supplied `id` field is not configurable in `0.0.6`; the resolver-backed sibling-field is the documented alternative. **Note**: a metadata-only sibling like `display_id: ID = strawberry.field(description="…")` without a resolver would build but fail at query time because Strawberry's default resolver looks up `display_id` as an attribute on the returned Django model instance and does not find it.
  - [ ] **Before archiving**, the spec stays at its working location per [`docs/builder/BUILD.md`](builder/BUILD.md) "Specs stay at their working location after closeout". Opt-in archival to `docs/SPECS/` is the maintainer's call; the [Definition of done](#definition-of-done) does not gate on it.

## Problem statement

[`docs/FEATURES.md`](FEATURES.md)'s [`Definition-order independence`](FEATURES.md#definition-order-independence) entry currently closes with the sentence: *"Manual scalar-field override semantics remain an implementation detail until [Scalar field override semantics](#scalar-field-override-semantics) ships."* The `DONE-006-0.0.4` foundation slice pinned the override contract for **relation fields only** — both the annotation-only path (`items: list["AdminItemType"]`) and the assigned-`strawberry.field` path are part of the stable surface and are exercised by the three tests at `tests/types/test_definition_order.py:179`, `:206`, and `:235`.

For scalar fields, the picture is asymmetric. The assigned-`strawberry.field` path landed during the `0.0.5` foundation extension (`tests/types/test_definition_order.py:278`'s `test_assigned_scalar_field_override_keeps_consumer_resolver` — its docstring credits the "Medium fix from `rev-types__base.md`" that widened `_consumer_assigned_fields` to walk every selected Django field rather than only relations). The **annotation-only path** for scalars never got the same treatment: today, writing `description: int` on a `DjangoType` whose `CharField` `description` column is selected via `Meta.fields` lands the consumer's annotation in `cls.__annotations__` at `__init_subclass__` time (the merge at `types/base.py:138` puts `consumer_annotations` last so consumer wins), but the `consumer_authored_fields` set does NOT contain the name, so the synthesized scalar annotation is also computed and written into the same dict (the consumer's `int` lands over the synthesized `str` only because dict-merge order favors the consumer — the path is brittle and not a stable contract).

The previously-skipped `tests/types/test_base.py:444-465`'s `test_consumer_annotation_overrides_synthesized` was the original placeholder for this contract. Its skip reason states *"Strawberry's @strawberry.type decorator regenerates cls.__annotations__ from its own field metadata after our merge in DjangoType.__init_subclass__, so the consumer's class-level scalar annotation loses to the synthesized one."* Under the current code, the merge order at `types/base.py:138` already puts the consumer's annotation last — the skip reason describes a pre-foundation-slice state. The test would likely pass today for the simple pre-finalize case, but the contract is not part of the documented public surface, and the symmetric four-corner override matrix is incomplete.

This card closes the asymmetry by extending the existing `consumer_annotated_relation_fields` collection to a parallel `consumer_annotated_scalar_fields` set, unioning it into `consumer_authored_fields`, and landing the test as the stable proof.

## Current state

`DjangoType.__init_subclass__` (`django_strawberry_framework/types/base.py:75-140`) builds the override-routing state as follows:

```python
# types/base.py:94-108 (current)
consumer_annotations = dict(getattr(cls, "__annotations__", {}))
consumer_annotated_relation_fields = frozenset(
    field.name for field in fields if field.is_relation and field.name in consumer_annotations
)
consumer_assigned_relation_fields, consumer_assigned_scalar_fields = _consumer_assigned_fields(
    cls.__dict__,
    fields,
)
consumer_authored_fields = frozenset(
    {
        *consumer_annotated_relation_fields,
        *consumer_assigned_relation_fields,
        *consumer_assigned_scalar_fields,
    },
)
```

Note the asymmetry: `consumer_annotated_relation_fields` filters on `field.is_relation`, but there is no parallel `consumer_annotated_scalar_fields`. The unified `consumer_authored_fields` therefore covers three of the four override corners but not the fourth (scalar annotation only).

`_build_annotations` (`types/base.py:535-659`) already has the right short-circuit shape — both branches check `if field.name in consumer_authored_fields: continue` (`:621` for relations, `:644` for scalars). Once the fourth corner lands in `consumer_authored_fields`, the scalar branch will skip synthesis for annotation-only-overridden scalars without further code change.

`DjangoTypeDefinition` (`django_strawberry_framework/types/definition.py:14-34`) carries the three existing introspection sets:

```python
# types/definition.py:28-31 (current)
consumer_authored_fields: frozenset[str] = frozenset()
consumer_annotated_relation_fields: frozenset[str] = frozenset()
consumer_assigned_relation_fields: frozenset[str] = frozenset()
consumer_assigned_scalar_fields: frozenset[str] = frozenset()
```

The `consumer_annotated_scalar_fields: frozenset[str] = frozenset()` field is the symmetric fourth corner.

`tests/types/test_definition_order.py:179-303` carries the four-corner test cluster as of `0.0.5`:

| Field shape | Override style | Test |
|---|---|---|
| Relation | Annotation-only | `test_annotation_only_relation_override_keeps_generated_resolver` (`:179`) |
| Relation | Assigned `strawberry.field` | `test_assigned_relation_field_override_keeps_consumer_resolver` (`:206`) + decorator variant at `:235` |
| Scalar | Assigned `strawberry.field` | `test_assigned_scalar_field_override_keeps_consumer_resolver` (`:278`) |
| Scalar | Annotation-only | **missing** — currently the skipped test at `tests/types/test_base.py:454-465` |

This card lands the bottom-right cell.

## Goals

- Add `consumer_annotated_scalar_fields` collection in `DjangoType.__init_subclass__`, parallel to the existing `consumer_annotated_relation_fields` collection.
- Add `consumer_annotated_scalar_fields: frozenset[str] = frozenset()` field to `DjangoTypeDefinition`.
- Union the new set into `consumer_authored_fields` so the existing scalar-branch short-circuit in `_build_annotations` fires for the new override path.
- Pin the **converter-validation-bypass contract** for overridden scalar fields (H2 / Decision 7a): consumer annotation overrides are authoritative, so `convert_scalar`'s unsupported-field-type rejection, grouped-choices rejection, `ArrayField` shape rejection, `null=True` widening, and choice-enum registration are all bypassed for an overridden field. Annotation override becomes a parallel recourse to `Meta.exclude` for unsupported scalar fields.
- Add the **Relay `id` collision guard** (H1 / Decision 7): raise `ConfigurationError` from `__init_subclass__` when the consumer authors an `id` entry (annotation or assigned `StrawberryField`) on a `Meta.interfaces = (relay.Node,)`-shaped type, unless the annotation is a `relay.NodeID[...]` marker. The guard uses `typing.get_type_hints(cls, include_extras=True)` with a token-shaped regex fail-soft (`(?:^|\.)NodeID\[`) for unresolved string annotations and a resolved-object fallback for the sibling-annotation-unresolved case. Replaces the downstream Strawberry-side `ValueError` at `strawberry.Schema(...)` construction.
- Unskip and relocate the existing `test_consumer_annotation_overrides_synthesized` (rev6 L3 default: delete; the Slice 1 test cluster on `tests/types/test_definition_order.py` covers the contract more thoroughly).
- Document the four-corner override contract, the H2 bypass contract, and the H1 Relay collision guard in `docs/FEATURES.md`'s `Scalar field override semantics` entry, flipping its status to `shipped (0.0.6)`.
- 100% coverage on the new collection path, the new definition field, the H1 Relay guard (including the `_id_annotation_is_relay_node_id` helper's two fail-soft sub-cases), the H2 converter bypass, and the cross-type enum-cache behavior change. The 18-test Slice 1 cluster (4 core + 4 converter-bypass + 10 Relay) is the contract surface.

## Non-goals

- **No new `Meta.field_overrides = {...}` API.** The card's KANBAN entry explicitly lists `Meta.field_overrides` as a *design choice* but the symmetric annotation-only + assigned-`strawberry.field` path is sufficient to close the contract gap. A future card may add a declarative override key if the assigned / annotation routes prove insufficient for some real consumer use case; that lives outside `0.0.6`.
- **No annotation/field-type compatibility pre-check.** Writing `description: int` against a `CharField` is the consumer's responsibility; the package does not assert that the consumer's annotation is type-compatible with the Django column. Runtime serialization errors at query time are the consumer-visible failure mode and are intentional — the package treats consumer overrides as authoritative.
- **No new opt-out / removal API.** The `Meta.exclude` path that shipped in `0.0.1` already covers "drop the field entirely". This card does not add a sentinel-value or `Skip`-typed annotation shape (e.g., `description: None` or `description: strawberry.SKIP`) — the design space is not justified by any pending consumer use case.
- **No new field metadata API.** Description / deprecation / default routing already work via the assigned `strawberry.field(...)` path (`description = strawberry.field(description="...", deprecation_reason="...")` is preserved by `_consumer_assigned_fields`'s scalar branch). This card adds no parallel route through annotation-only syntax.
- **No change to relation overrides.** All four cells of the relation × {annotation, assigned} matrix shipped in `0.0.4` / `0.0.5` and stay unchanged.
- **No change to the post-merge annotation order at `types/base.py:138`.** The line `cls.__annotations__ = {**synthesized, **consumer_annotations}` continues to put consumer last; the only difference is that under this card the synthesized dict no longer contains entries for annotation-only-overridden scalars, so the merge degenerates to "consumer annotation only" for those keys.

## Architectural decisions

### Decision 1 — Annotation-only scalar override collection

Symmetric to the existing relation collection. Replace the single-list comprehension at `types/base.py:95-97` with two comprehensions:

```python
# types/base.py (post-Slice-1)
consumer_annotations = dict(getattr(cls, "__annotations__", {}))
consumer_annotated_relation_fields = frozenset(
    field.name for field in fields if field.is_relation and field.name in consumer_annotations
)
consumer_annotated_scalar_fields = frozenset(
    field.name for field in fields if not field.is_relation and field.name in consumer_annotations
)
```

Both filters walk the same `fields` tuple and read the same `consumer_annotations` dict; the only difference is the `field.is_relation` polarity. The two sets are disjoint by construction.

**Why two filters rather than one walk-and-bucket loop.** The two-comprehension form keeps the code shape symmetric with the existing relation collection one line above. A bucket-loop variant would compress the two lines into a single multi-line for-loop with an if/else inside, which loses the visual symmetry and makes the two override paths look like they are doing different things. They are not — they are the same logic with a polarity flip.

**Why filter on `not field.is_relation` rather than `field.is_relation is False`.** Django's `Field.is_relation` attribute is documented as a bool but is sometimes accessed at type-check time before model loading completes; the `not` form is bool-coercion-safe in a way that the explicit-comparison form is not. The existing `_build_annotations` code at `types/base.py:620` uses `if field.is_relation:` (bool-coercion), so the new filter matches the established convention.

### Decision 2 — `consumer_authored_fields` union shape

The single `consumer_authored_fields` frozenset stays as the only short-circuit input to `_build_annotations`. Extend its construction at `types/base.py:102-108` to include the new set:

```python
# types/base.py (post-Slice-1)
consumer_authored_fields = frozenset(
    {
        *consumer_annotated_relation_fields,
        *consumer_annotated_scalar_fields,   # new
        *consumer_assigned_relation_fields,
        *consumer_assigned_scalar_fields,
    },
)
```

Order inside the set literal does not matter (frozenset is unordered). The line ordering is chosen to keep relations and scalars adjacent — relations first, then scalars, within each (annotated, assigned) pair.

**Why not pass the four sets individually to `_build_annotations`.** The function already only needs the union — it does not distinguish between the four corners. Passing four sets would force `_build_annotations` to recompute the union or to switch on which set the name came from, neither of which it needs to do. The single `consumer_authored_fields` argument stays.

### Decision 3 — `DjangoTypeDefinition.consumer_annotated_scalar_fields` field

Symmetric to the three existing sibling fields. Replace `types/definition.py:28-31` with the **grouped-by-style** order (L1 fix: annotated-relation, annotated-scalar, assigned-relation, assigned-scalar — annotations group first, assignments group second):

```python
# types/definition.py (post-Slice-1)
consumer_authored_fields: frozenset[str] = frozenset()
consumer_annotated_relation_fields: frozenset[str] = frozenset()
consumer_annotated_scalar_fields: frozenset[str] = frozenset()      # new
consumer_assigned_relation_fields: frozenset[str] = frozenset()
consumer_assigned_scalar_fields: frozenset[str] = frozenset()
```

Order chosen to group annotated fields first, then assigned fields, with relation and scalar pairs adjacent within each. Worker 1 lands the cosmetic re-order of the existing two `consumer_assigned_*` lines (currently at `:30-31` in the rev1 dataclass) in the same commit as the new field so the dataclass field order is internally consistent. Slice 1's checklist text and this Decision 3 sample now match (L1 fix; rev1 had them disagreeing).

The field is read by tests for introspection (per the Slice 1 test cluster). No production code path consumes it directly — production routes through the unified `consumer_authored_fields`. The four-corner sets exist as the introspection surface and as a tested contract that the package will not silently change the bucketing.

### Decision 4 — `_build_annotations` body stays unchanged

The scalar branch at `types/base.py:643-650` already does the right thing:

```python
# types/base.py:643-650 (unchanged)
else:
    if field.name in consumer_authored_fields:
        # A consumer-assigned ``StrawberryField`` (or annotation) on a
        # scalar column wins over the auto-synthesized annotation so
        # ``strawberry.field(resolver=...)`` overrides survive
        # collection. Relation override symmetry: see the
        # ``field.is_relation`` branch above.
        continue
    if suppress_pk_annotation and field.name == pk_name:
        continue
    annotations[field.name] = convert_scalar(field, cls.__name__)
```

The existing inline comment already mentions "annotation" in parallel with "assigned `StrawberryField`" — the docstring's *intent* covers the annotation-only path. What's been missing is the upstream collection that adds annotation-only scalars to `consumer_authored_fields`. Slice 1 closes that gap with no body edit in `_build_annotations`. Worker 1 may choose to slightly retighten the inline comment for clarity after Slice 1 lands; the spec is neutral on the wording polish.

### Decision 5 — Test placement and the skipped test's fate

The four-corner override matrix lives in `tests/types/test_definition_order.py` (the foundation-slice override-contract host) — three of the four cells are already there at `:179`, `:206`, `:235`, and `:278`. The fourth cell (annotation-only scalar) is the natural sibling and lands as a new test in the same file. The placement keeps the override matrix discoverable in one spot.

The previously-skipped `tests/types/test_base.py:454-465` is then redundant. Two reasonable resolutions:

1. **Delete** the skipped test entirely. The new tests in `test_definition_order.py` cover the contract more thoroughly (pre-finalize + post-finalize + introspection + end-to-end Strawberry schema query). Smaller-touch.
2. **Unskip and keep** as a tiny smoke-test sibling of the larger test cluster. Doesn't add coverage value, but preserves test history.

The spec recommends option (1) — `test_definition_order.py` is the canonical host for the override-contract matrix, and a one-line smoke test sitting alone in `test_base.py` would invite future drift between the two locations. Worker 1 may override during planning if there's a strong reason to keep the test_base.py site.

### Decision 6 — Why `_consumer_assigned_fields` stays the way it is

`_consumer_assigned_fields` at `types/base.py:207-240` walks `cls.__dict__` and buckets assigned `StrawberryField` instances into (relation, scalar) tuples. The function does NOT walk `consumer_annotations` — that's the parallel job of the annotation-collection lines at `:95-97`. Symmetric responsibility split:

- `_consumer_assigned_fields` reads `cls.__dict__` → produces `(consumer_assigned_relation_fields, consumer_assigned_scalar_fields)`.
- The annotation-collection lines read `cls.__annotations__` → produce `(consumer_annotated_relation_fields, consumer_annotated_scalar_fields)`.

The two sources are independent (a consumer can write `description: int` annotation-only, OR `description = strawberry.field(...)` assigned, OR both — the four-corner matrix treats them as separate input channels). `_consumer_assigned_fields` stays unchanged by this card; the new collection is the annotation-side parallel.

### Decision 7 — Relay `id` override collision

`_build_annotations` (`types/base.py:619-657`) processes each selected field in two ordered checks: first the consumer-authored short-circuit (`if field.name in consumer_authored_fields: continue` at `:621` for relations and `:644` for scalars), then the `relay.Node` pk-suppression branch (`if suppress_pk_annotation and field.name == pk_name: continue` at `:651-657`). The ordering matters: a consumer who writes an `id: int` annotation on a Relay-Node-shaped type lands `"id"` in `cls.__annotations__`, the consumer-authored short-circuit fires at `:644` (assuming `id` is also a model field), and the loop continues. The pk-suppression branch never executes for that field name. The merge at `types/base.py:138` then writes the consumer's `id: int` annotation onto `cls.__annotations__`.

The downstream behavior is broken in a way that surfaces far from the source: `finalize_django_types()` runs to completion (the `_build_annotations` skip is cooperative with the consumer override); `strawberry.Schema(query=Query, types=[ThatType])` then fails inside Strawberry's schema-validation pass with a `ValueError` because `Node.id` is `ID!` (the interface contract) while the concrete type's `id` is `Int!`. The error originates from Strawberry's interface-compliance check, not from any `DjangoType` code path — the user's traceback points at `strawberry/schema/schema.py` rather than at `types/base.py`, and the message ("Interface field Node.id expects type ID! but ImplementingType.id is of type Int!") leaves the consumer to reverse-engineer the connection back to their `DjangoType` declaration.

**Contract.** This card adds a package-owned `ConfigurationError` raised at `DjangoType.__init_subclass__` time when **and only when** the consumer authored an `"id"` entry on a Relay-Node-shaped type, AND the entry is not a `relay.NodeID[...]`-marked annotation. Assigned `id` overrides (any `StrawberryField`) are always rejected — the supported alternatives are the `@classmethod resolve_id` hook from Strawberry's Relay Node interface (custom id resolver) and `id: relay.NodeID[<pk_type>]` (custom id annotation). Consumers who previously wrote `id = strawberry.field(description="…")` purely to attach GraphQL field-level metadata to the Relay-supplied `id` lose that route — the rev6 M1 + rev7 M2 workaround is a **resolver-backed sibling field** (e.g., `@strawberry.field(description="…") def display_id(self) -> strawberry.ID: return str(self.pk)`) that carries the metadata AND defines a value source. A metadata-only sibling (`display_id: ID = strawberry.field(description="…")`) without a resolver would build but fail at query time because Strawberry's default resolver would look up `display_id` as an attribute on the returned Django model instance and not find it (rev7 M2). The Relay-supplied `id` stays undecorated; field-level metadata on it is not configurable in `0.0.6` (rev4 M1 + rev6 M1 + rev7 M2):

```python
# In DjangoType.__init_subclass__, after consumer_*_scalar_fields collection
# and BEFORE _build_annotations runs (so the error fires at type-creation time).
relay_shaped = (
    any(issubclass(i, relay.Node) for i in interfaces)
    or issubclass(cls, relay.Node)
)
if relay_shaped:
    # Rev6 M3 (corrected from rev4 M2): use key-presence rather than
    # value-truthiness so unusual annotations are still detected. The rev4
    # M2 entry described `id: None` as having `cls.__annotations__["id"] is
    # None`, but Python evaluates `None` to `<class 'NoneType'>` — not the
    # literal None value. The key-presence check is still the right
    # predicate; it also covers `id: Literal[None]`, string forms that
    # evaluate to false-y types, and any other annotation the consumer
    # may write whose value is not a clean truthy object.
    has_id_annotation = "id" in cls.__annotations__
    id_assignment = cls.__dict__.get("id")
    has_id_assignment = isinstance(id_assignment, StrawberryField)
    if has_id_annotation or has_id_assignment:
        # Assigned `id = <StrawberryField>` is always rejected on a Relay-
        # Node-shaped type (rev4 M1). Custom id resolution belongs on the
        # Strawberry-provided `@classmethod resolve_id` hook; custom id
        # shape belongs on `id: relay.NodeID[<pk_type>]`. Both are
        # interface-compliant; assigned `id` resolvers are not, because
        # this card's contract treats `id` as Relay-owned. Rev6 M1 + rev7
        # M2: the error message names a **resolver-backed** sibling-field
        # workaround for consumers who only wanted to attach GraphQL
        # field-level metadata (description / deprecation_reason /
        # directives) to the Relay-supplied id. The metadata-only form
        # (`display_id: ID = strawberry.field(description="…")`) without a
        # resolver would build but fail at query time because Strawberry's
        # default resolver looks up `display_id` as an attribute on the
        # returned Django model instance; the resolver-backed form
        # (`@strawberry.field def display_id(self) -> strawberry.ID:
        # return str(self.pk)`) carries the metadata AND defines a value
        # source.
        if has_id_assignment:
            raise ConfigurationError(
                f"{cls.__name__}: cannot override the id field on a "
                "relay.Node-shaped type with an assigned strawberry.field. "
                "Use @classmethod resolve_id for a custom id resolver, "
                "id: relay.NodeID[<pk_type>] for a custom id annotation, "
                "or declare a resolver-backed sibling field — e.g., "
                "`@strawberry.field(description=...)` `def display_id(self) -> "
                "strawberry.ID: return str(self.pk)` — if you only need "
                "GraphQL field-level metadata on a custom identifier "
                "(a metadata-only sibling without a resolver builds but "
                "fails at query time); "
                "or remove relay.Node from Meta.interfaces."
            )
        # Annotation-only path: pass through valid relay.NodeID[...]-marked
        # annotations (the documented escape hatch). Detection mechanism
        # (rev4 H1): typing.get_type_hints(cls, include_extras=True) so
        # stringified / future-annotations forms are resolved against the
        # consumer's module globals. The Annotated[T, NodeIDPrivate] marker
        # survives include_extras=True. Fail-soft on NameError /
        # AttributeError (unresolved forward references) — see helper for
        # the rev5 M1 / rev6 H1 fail-soft scoping. Rev6 M2: the conjunction
        # `has_id_annotation and _id_annotation_is_relay_node_id(cls)` was
        # dead — by this point `has_id_assignment` has already raised so
        # `has_id_annotation` must be True; drop the conjunction.
        if _id_annotation_is_relay_node_id(cls):
            pass  # Accept.
        else:
            raise ConfigurationError(
                f"{cls.__name__}: cannot override the id field on a "
                "relay.Node-shaped type without using strawberry.relay.NodeID[...]. "
                "The Relay interface supplies id: GlobalID! — declare the id "
                "field via relay.NodeID[<pk_type>] if you need a different id "
                "shape, or remove relay.Node from Meta.interfaces."
            )


def _id_annotation_is_relay_node_id(cls: type) -> bool:
    """Return True when ``cls.__annotations__['id']`` resolves to ``relay.NodeID[...]``.

    Uses ``typing.get_type_hints(cls, include_extras=True)`` so stringified
    annotations (``from __future__ import annotations`` or explicit string
    annotations like ``id: "relay.NodeID[int]"``) evaluate against the
    consumer's module globals. ``include_extras=True`` is required so the
    ``Annotated[T, NodeIDPrivate]`` marker survives the resolution.

    Fail-soft: ``typing.get_type_hints`` evaluates **every** annotation on
    ``cls`` (and walks the MRO). A single unresolved string annotation
    anywhere on the class trips ``NameError`` / ``AttributeError`` —
    even when the ``id`` annotation itself resolves cleanly. The fail-
    soft therefore covers two distinct sub-cases (rev6 H1 + rev5 M1):

    1. **``id`` annotation itself failed to resolve.** ``cls.__annotations__["id"]``
       is the raw string the consumer wrote. Accept only when the string
       matches the token-shaped regex ``(?:^|\.)NodeID\[`` — covers the
       qualified (``"relay.NodeID[int]"``, ``"strawberry.relay.NodeID[int]"``)
       and unqualified (``"NodeID[int]"``) forms of a deferred NodeID
       reference. Other unresolved strings — typos like ``id:
       "MissingType"``, non-NodeID forward references, and
       prefixed-substring lookalikes like ``id: "NotNodeID[int]"`` or
       ``id: "MyNodeID[int]"`` (rev7 H1: a plain ``"NodeID[" in raw``
       substring check accepted these false positives) — return False
       so the H1 guard fires at class-creation time with the supported-
       escape-hatch message. The fail-soft window is open ONLY for
       package-level guard suppression; the consumer is still
       responsible for making the string resolvable by Strawberry's
       downstream schema-construction pass (which uses its own
       evaluation path against ``cls``'s module globals). A consumer
       who writes a NodeID-shaped string that does not resolve in their
       module's globals will see the package's ``ConfigurationError``
       suppressed but Strawberry's later resolution error remain — see
       the split tests under "Relay collision tests" for the
       end-to-end-vs-guard-only contract distinction (rev7 H1).
    2. **Some OTHER annotation on the class failed to resolve, but the
       ``id`` annotation is directly resolved (rev6 H1).**
       ``cls.__annotations__["id"]`` is the already-resolved
       ``Annotated[int, NodeIDPrivate]`` object, not a string. The
       rev5 fail-soft logic would have returned False (because
       ``isinstance(raw, str)`` is False), falsely rejecting the valid
       escape hatch. Rev6 fix: fall back to inspecting the resolved
       object via ``_has_node_id_marker`` rather than rejecting
       unconditionally.

    The realistic trigger for sub-case (2) is a ``DjangoType`` with
    ``id: relay.NodeID[int]`` plus any forward-referenced relation
    annotation like ``items: list["AdminItemType"]`` — a common
    pattern in real consumer code.
    """
    try:
        hints = typing.get_type_hints(cls, include_extras=True)
    except (NameError, AttributeError):
        # Fail-soft (rev5 M1 + rev6 H1 + rev7 H1): handle both "id
        # failed to resolve" (raw is a string) and "another annotation
        # failed but id is already resolved" (raw is an Annotated
        # object). The string check uses a token-shaped regex rather
        # than a substring ``in`` test so prefixed-substring lookalikes
        # like ``"NotNodeID[int]"`` are rejected (rev7 H1).
        raw = cls.__annotations__.get("id")
        if isinstance(raw, str):
            # Sub-case 1: id is the unresolved string. Accept only
            # token-shaped NodeID strings (start-of-string or dot-
            # boundary before ``NodeID[``). Typos and prefixed-
            # substring lookalikes fall through to the guard.
            return bool(_NODEID_STRING_RE.search(raw))
        # Sub-case 2 (rev6 H1): id is the already-resolved annotation
        # object (some other annotation tripped the exception). Inspect
        # the resolved object directly rather than rejecting on the
        # "not a string" branch — rev5's logic falsely rejected valid
        # escape hatches in this case.
        return _has_node_id_marker(raw)


# Rev7 H1: token-shaped regex prevents prefixed-substring false
# positives like "NotNodeID[int]" or "MyNodeID[int]" from passing
# the fail-soft accept path. The dot-boundary form covers
# "relay.NodeID[int]" and "strawberry.relay.NodeID[int]"; the
# start-of-string form covers the unqualified "NodeID[int]".
_NODEID_STRING_RE = re.compile(r"(?:^|\.)NodeID\[")
    id_hint = hints.get("id")
    if id_hint is None:
        return False
    # Check both the direct relay.NodeID[T] form (typing.get_origin returns
    # NodeID-related marker) and the Annotated[T, NodeIDPrivate] form
    # (typing.get_args returns metadata including the marker). Worker 1
    # picks the precise marker shape during planning by inspecting
    # strawberry.relay internals; the spec contract is "valid
    # relay.NodeID[...] in any form is accepted".
    return _has_node_id_marker(id_hint)
```

**Rev3 narrowing — what the predicate excludes.** Two false-positive cases that rev2's broader predicate would have rejected:

1. **`id: relay.NodeID[int]`** — the advertised escape hatch. Under rev2's `pk_name in consumer_annotated_scalar_fields` predicate, a consumer following the error message's instructions would land `"id"` in `consumer_annotated_scalar_fields` (because `id` is the model pk and the `NodeID[int]` annotation goes through the same collection path) and the guard would fire against the very pattern it told the consumer to use. Rev3 detects the `relay.NodeID` marker and passes through.
2. **Non-`id` primary-key overrides.** A model with `code = models.CharField(primary_key=True)` and a consumer `code: str` override has GraphQL fields `id: ID!` (from Relay) and `code: String!` (from the consumer) — no `Node.id` collision because no `id` field is being overridden. Rev2's `pk_name in consumer_*_scalar_fields` predicate fired against the pk name regardless of whether it was `"id"`; rev3 keys off the GraphQL field name `"id"` exclusively.

Existing `tests/types/test_relay_interfaces.py:240`'s `test_composite_pk_with_explicit_node_id_annotation_is_accepted` pattern (uses `name: relay.NodeID[str]`) confirms the framework's broader contract — `relay.NodeID` annotations land on any attribute, not just `"id"`, and the package must not reject them. The H1 guard never fires for non-`id` field names regardless of model pk shape; the `id`-only narrowing keeps the guard scope tight.

**Why `__init_subclass__` and not `_build_annotations` or `_validate_meta`.** Three options were considered:

1. **In `_validate_meta`** — too early. `_validate_meta` does not have access to `consumer_annotations` or `cls.__dict__`; it runs over the `Meta` class only. Threading the pk-shadow check through would require widening `_validate_meta`'s signature for a single-purpose check.
2. **In `_build_annotations`** — too late and wrong-layered. `_build_annotations`'s job is annotation synthesis, not configuration validation. Reordering the existing short-circuit / pk-suppression checks inside it to detect the collision would entangle three different concerns (consumer override, Relay suppression, conflict detection) into the per-field loop.
3. **In `__init_subclass__` after collection** — chosen. The collection lines at `types/base.py:95-108` already produce `consumer_annotated_scalar_fields` and `consumer_assigned_scalar_fields` (post-Slice-1), and `cls.__annotations__` / `cls.__dict__` are already populated. The `interfaces` tuple is already validated by `_validate_meta` at `:87`. The check is a single guard between collection and `_build_annotations` invocation, with all inputs already in hand.

**`relay.NodeID` detection — pinned class-creation-time (rev4 H1).** The detection runs inside `__init_subclass__` so the `ConfigurationError` fires at class-definition time, matching the reject test and the CHANGELOG wording. The mechanism is `typing.get_type_hints(cls, include_extras=True)` (NOT raw `typing.get_args(cls.__annotations__["id"])`). The difference matters:

- `cls.__annotations__["id"]` returns the literal value the consumer wrote — under `from __future__ import annotations` (PEP 563) or an explicit string annotation like `id: "relay.NodeID[int]"`, that value is the string `"relay.NodeID[int]"`, not the resolved type. Raw `typing.get_args` against a string returns `()`, and the `NodeIDPrivate` marker check fails — the guard would reject the documented escape hatch in stringified form.
- `typing.get_type_hints(cls, include_extras=True)` evaluates the string against `cls`'s module globals using the standard PEP 563 resolution path. `include_extras=True` preserves `Annotated[T, ...]` metadata so the `NodeIDPrivate` marker (or whatever shape strawberry's `relay.NodeID` reduces to internally) is discoverable.

**Narrow fail-soft on unresolved forward references (rev5 M1 + rev6 H1 + rev7 H1).** `typing.get_type_hints(cls, include_extras=True)` evaluates **every** annotation on `cls` (and walks the MRO). A single unresolved string annotation anywhere on the class trips `NameError` (or `AttributeError`, for nested attribute references) — even when the `id` annotation itself resolves cleanly. The detection helper's fail-soft branch therefore covers two distinct sub-cases:

1. **The `id` annotation itself failed to resolve.** `cls.__annotations__["id"]` is the raw string the consumer wrote. Accept **only** when that string matches the token-shaped regex `(?:^|\.)NodeID\[` — covering the qualified (`"relay.NodeID[int]"`, `"strawberry.relay.NodeID[int]"`) and unqualified (`"NodeID[int]"`) forms of an unresolved-at-class-creation NodeID reference. Other unresolved strings — typos like `id: "MissingType"`, non-NodeID forward references like `id: "MyEnumType"`, and prefixed-substring lookalikes like `id: "NotNodeID[int]"` or `id: "MyNodeID[int]"` (rev7 H1: a plain `"NodeID[" in raw` substring check accepted these as false positives) — are rejected by the H1 guard with the standard "use `relay.NodeID[...]`" error message. **Important (rev7 H1): the fail-soft window is open ONLY for package-level guard suppression.** Strawberry's downstream schema-construction pass resolves the same string annotation against `cls`'s module globals using its own evaluation path; if the consumer's string is not resolvable in that scope, Strawberry's `ValueError` will still fire later — the package's `ConfigurationError` is just suppressed at class-creation time, not the entire end-to-end failure. A test that wants to pin **end-to-end** schema success must ensure `relay` (or whichever module supplies `NodeID`) is importable at the test class's module scope; a test that wants to pin **guard-only** suppression for the unresolved-but-syntactically-NodeID case must assert class-creation acceptance only, not finalize / schema build. See the split tests under "Relay collision tests" for the contract distinction.
2. **Some other annotation on the class failed to resolve, but the `id` annotation is directly resolved (rev6 H1).** `cls.__annotations__["id"]` is the already-resolved `Annotated[int, NodeIDPrivate]` object, not a string. The rev5 fail-soft path returned False on this branch (because `isinstance(raw, str)` was False), which falsely rejected the valid escape hatch. The realistic trigger is a `DjangoType` with `id: relay.NodeID[int]` plus any forward-referenced relation annotation like `items: list["AdminItemType"]` — a common pattern. The rev6 fix is to fall back to `_has_node_id_marker(raw)` (the same check used on the success path) when `raw` is not a string, accepting the annotation when the resolved object carries the marker and rejecting otherwise. Reproduced locally against the on-disk `strawberry.relay`.

**Worker 1's planning task.** The detection helper needs the precise `NodeIDPrivate` marker shape that strawberry's `relay.NodeID[T]` reduces to. Worker 1 reads `strawberry.relay`'s source during planning to confirm the marker class name and check whether `typing.get_origin(hint) is relay.NodeID` is the canonical detection, or whether the marker lives only in `typing.get_args(hint)`'s metadata slot. The spec contract is "any valid `relay.NodeID[T]` annotation, in direct or stringified form, is accepted"; the exact helper body is an implementation detail.

**Decision-7-7 finalize-time alternative was dropped (rev4).** A previous draft offered a finalize-time `cls.resolve_id_attr()` probe as an alternative detection mechanism. That option cannot satisfy this card's class-creation-time raise contract (the reject test asserts pre-`finalize_django_types()` failure, and the CHANGELOG says `__init_subclass__`); the alternative is no longer in scope.

**Why this is in scope for this card.** The card's headline contract is "consumer annotation override for scalars". Without H1's guard, the new annotation-only override path silently breaks `relay.Node`-shaped types in a way that points the consumer at the wrong code surface. The guard is the smallest correct UX surface for the new override behavior and fits inside the same `__init_subclass__` pass that the collection itself lives in.

### Decision 7a — Converter validation bypass (H2 fix)

Adding annotation-only scalar names to `consumer_authored_fields` skips the entire scalar branch at `types/base.py:643-650` before `convert_scalar(...)` is called. `convert_scalar` (`types/converters.py:95-196`) carries several validation and side-effect responsibilities beyond annotation synthesis:

1. **Unsupported field-type rejection.** Walks `type(field).__mro__` looking for a `SCALAR_MAP` match; raises `ConfigurationError` if nothing matches. The error message names `Meta.exclude` as the consumer recourse.
2. **Grouped-choices rejection.** `convert_choices_to_enum` raises `ConfigurationError("Meta.fields contains grouped-choices field ...")` when the Django field's `choices=` is the grouped `[(label, [(value, label), ...])]` shape.
3. **`ArrayField` shape validation.** Rejects nested `ArrayField` (recursive `base_field` walk hits a second `ArrayField`) and outer `choices=` declarations with `ConfigurationError`.
4. **`HStoreField` routing.** Sentinel-guarded branch that returns `strawberry.scalars.JSON` only when `django.contrib.postgres.fields` imports successfully; rejects outer `choices=` with `ConfigurationError`.
5. **`null=True` widening.** `T | None` wrapping for nullable scalar columns.
6. **Choice-enum registration.** Successful `convert_choices_to_enum` calls register the generated enum into `registry._enums[(model, field_name)]` so two `DjangoType`s reading the same choice column share one cached enum (the existing [`Choice enum generation`](FEATURES.md#choice-enum-generation) contract from `0.0.1`).

Under the new short-circuit, **every one of these validations and side effects is bypassed for an annotation-overridden field.** The contract for this card:

- Consumer annotation overrides are **authoritative**. The consumer takes responsibility for the runtime shape of the annotation; the package does not pre-validate that the override is compatible with the underlying Django column.
- Unsupported scalar fields can be annotation-overridden as a recourse parallel to `Meta.exclude`. Before this card, the only recourse for an unsupported scalar was to drop the field via `Meta.exclude`; after this card, a consumer can also write a custom annotation. (Aligns with the existing relation path: annotation-only relation overrides bypass `convert_relation` and its pending-relation routing.)
- Grouped-choices, nested-`ArrayField`, and outer-`choices`-on-postgres-fields rejections **do not fire** when the consumer overrides those columns. The consumer's annotation replaces the package's auto-conversion entirely.
- Choice-enum registration **does not fire** when the consumer overrides a `choices=`-bearing column. The shared `(model, field_name)` enum cache is not populated for that field. A second `DjangoType` on the same model that selects the same column without an override will trigger fresh enum generation. This is a behavior change worth flagging — pre-spec, two `DjangoType`s with one overriding and one not would have shared the auto-generated enum from whichever loaded first; post-spec, the overriding type contributes nothing to the cache.
- `null=True` widening is the consumer's responsibility — a consumer who writes `description: int` against a nullable `IntegerField(null=True)` gets the literal `int` annotation, not `int | None`. The consumer is expected to write `description: int | None` themselves.

**Why the bypass is the correct contract.** Two reasons:

1. **Consistency with the relation override path.** Annotation-only relation overrides already bypass `convert_relation` entirely (the `if field.name in consumer_authored_fields: continue` short-circuit at `types/base.py:621` fires before any relation-side validation). The scalar contract should match.
2. **Override is escape, not augmentation.** The point of an override is to escape the package's auto-conversion. If the package still enforced `convert_scalar`'s validations on overridden fields, an unsupported scalar would still raise even when the consumer was providing a perfectly valid manual annotation — defeating the purpose of the override.

**What this means for `docs/FEATURES.md`.** The `Scalar field conversion` entry currently frames unsupported scalars as `ConfigurationError` cases with `Meta.exclude` as the recourse. Under this card, annotation-only override is a parallel recourse. Slice 5 updates the entry to list both paths.

**Mandatory tests pinning the bypass.** See the three Slice 1 tests added under the "Converter-bypass regressions" sub-checklist: unsupported field type, grouped choices, nested `ArrayField`. Worker 1 may add additional regressions for `HStoreField` choices, outer `ArrayField` choices, and the null-widening path if planning surfaces a use case; the three listed cover the contract surface.

## Implementation plan

The slice ordering is **strict** — each slice depends on the previous. The plan deliberately keeps Slice 1 a one-commit change (collection + definition field + tests in `test_definition_order.py`) so the historical staleness in `test_base.py` is cleared in a discrete Slice 2 commit and the doc / KANBAN / CHANGELOG churn lives entirely in Slice 5.

| Slice | Files | Approx. line delta | Tests landed | Notes |
|---|---|---|---|---|
| 1 | `types/base.py`, `types/definition.py`, `tests/types/test_definition_order.py`, `tests/types/test_converters.py` (the default placement for the nested-`ArrayField` bypass test per rev6 L3) | +210/-1 | 18 new tests: 4 core overrides + 4 converter-bypass (added cross-type cache, rev6 L2) + 10 Relay collision (4 reject + 6 accept; rev6 added H1 sibling-annotation accept and L1 inheritance non-trigger; rev7 split the stringified-NodeID test, added a typo-lookalike reject, and inverted the inheritance test) | Headline change. Includes the H1 Relay guard implementation and the `_id_annotation_is_relay_node_id` detection helper (with the rev6 H1 fail-soft fix for the resolved-id + unresolved-sibling sub-case, and the rev7 H1 token-shaped regex fix for prefixed-substring false positives). |
| 2 | `tests/types/test_base.py` | -22/+0 (rev6 L3: default is the full delete of the skipped test block) | None new; existing skipped test resolved | Default is the full delete. |
| 3 | `types/base.py` | +5/-3 (docstring polish in `_consumer_assigned_fields`) | None | Documentation only. |
| 4 | Version-bump quintet | 0 lines if any prior `0.0.6` card already bumped | None | No-op gate. |
| 5 | Docs / KANBAN / CHANGELOG | +70/-10 | None | Largest cosmetic churn; closeout (adds the `Scalar field conversion` annotation-override-as-recourse update per H2, and the rev6 M1 metadata-route-loss acknowledgment in the `Scalar field override semantics` body and the `Changed` CHANGELOG entry). |

Total expected delta: ~290 lines added across the package and tests; one delete in `tests/types/test_base.py`; one substantial KANBAN body insert in `KANBAN.md`. No new source files. No new test files (rev6 L3: the nested-`ArrayField` bypass test defaults to placement in the existing `tests/types/test_converters.py`).

## Edge cases and constraints

- **`Meta.fields = "__all__"` interaction.** When `Meta.fields` is unspecified or `"__all__"`, every concrete Django field is selected. A consumer annotation that shadows any one of them — relation or scalar — lands in `consumer_authored_fields` under this card. The interaction with `Meta.exclude` is unchanged: a name listed in `Meta.exclude` is filtered out of `fields` upstream of the collection, so the `field.name in consumer_annotations` check never sees it. (Worker 1 should verify by reading `_select_fields` at `types/base.py:472` (pre-Slice-1).)
- **`relay.Node` `id` collision.** Pinned as a behavior contract, not a flagged edge case — see [Decision 7](#decision-7--relay-id-override-collision). A consumer who writes `id: <non-NodeID-type>` annotation, an unresolved-non-NodeID stringified annotation (e.g., `id: "MissingType"`), an unresolved NodeID-lookalike string (e.g., `id: "NotNodeID[int]"` — rev7 H1 rejected by the tightened token-shaped regex), or assigns any `id = <StrawberryField>` on a Relay-Node-shaped type raises `ConfigurationError` at `__init_subclass__` time. The annotation-side errors point at `relay.NodeID[...]` as the supported escape hatch; the assigned-side error points at three alternatives — `relay.NodeID[<pk_type>]`, `@classmethod resolve_id`, and the rev6 M1 + rev7 M2 **resolver-backed sibling-field workaround** (`@strawberry.field(description="…") def display_id(self) -> strawberry.ID: return str(self.pk)` for the field-level metadata use case; the metadata-only `display_id: ID = strawberry.field(description="…")` form is NOT recommended because it would build but fail at query time). The guard is narrow: `id: relay.NodeID[int]` passes in direct, resolved-string-end-to-end, unresolved-NodeID-shaped-string-guard-only, and mixed (directly-resolved `id` alongside other unresolved annotations) forms (rev4 H1 + rev5 M1 + rev6 H1 + rev7 H1: detection uses `typing.get_type_hints(cls, include_extras=True)` with two fail-soft sub-cases — id-itself-failed-to-resolve scoped by the `(?:^|\.)NodeID\[` token-shaped regex check, and id-resolved-but-sibling-failed scoped by direct `_has_node_id_marker(raw)` inspection of the resolved object); non-`id` consumer scalar overrides on Relay-Node-shaped types pass (no `Node.id` collision); inherited `id` annotations on a subclass slip past the guard at class-creation time AND are silently handled by `_build_annotations`'s pk-suppression branch — Strawberry applies the Relay-supplied `id: GlobalID!` and `resolve_id_attr()` falls back to `"pk"`, so schema construction succeeds (rev6 L1 + rev7 M1 correction: the guard does not walk the MRO and the rev6 "Strawberry's downstream `ValueError` is the failure mode" framing was wrong; pk-suppression handles the case silently). The ten Slice 1 Relay-collision tests pin the reject + accept + inheritance-handled paths: `test_consumer_id_annotation_on_relay_node_type_raises`, `test_consumer_id_assigned_strawberry_field_on_relay_node_type_raises`, `test_consumer_id_unresolved_non_nodeid_string_on_relay_node_type_raises`, `test_consumer_id_typo_lookalike_nodeid_string_on_relay_node_type_raises`, `test_consumer_id_relay_nodeid_annotation_on_relay_node_type_is_accepted`, `test_consumer_id_resolved_string_relay_nodeid_annotation_on_relay_node_type_is_accepted_end_to_end`, `test_consumer_id_unresolved_nodeid_shaped_string_on_relay_node_type_passes_guard_only`, `test_consumer_id_resolved_relay_nodeid_with_unresolved_sibling_annotation_is_accepted`, `test_consumer_non_id_scalar_override_on_relay_node_type_is_accepted`, and `test_inherited_id_annotation_on_relay_node_subclass_is_handled_by_pk_suppression`.
- **Choice-enum fields.** Pinned as a behavior contract, not a flagged edge case — see [Decision 7a](#decision-7a--converter-validation-bypass-h2-fix). A consumer annotation `status: MyEnum` on a `choices=`-bearing column bypasses `convert_choices_to_enum` entirely; `registry.get_enum(model, field_name)` returns `None` for the overridden field. Two `DjangoType`s on the same model where one overrides and one does not will get the fresh enum from the non-overriding type alone; pre-spec they would have shared whichever loaded first. `test_annotation_override_of_grouped_choices_field_is_allowed` pins the **single-type** bypass (`registry.get_enum` is None after one overriding type); `test_annotation_override_does_not_populate_shared_enum_cache_for_co_resident_types` (rev6 L2 + rev7 L1) pins the **cross-type** cache behavior — the non-overriding co-resident type populates the cache, the overriding type's GraphQL surface uses the consumer's annotation.
- **Inheritance.** Inherited consumer annotations on a base `DjangoType` subclass are NOT in the subclass's own `cls.__annotations__` (Python returns only the class's own annotations dict). A subclass that inherits from a base with `description: int` and adds `class Meta: model = Category` will see `cls.__annotations__ = {}` at `__init_subclass__` time and the collection will miss the inherited override. This matches the existing relation-annotation behavior at `:95-97` (also walks `cls.__annotations__`, also misses inherited annotations) — no asymmetry to fix here. Worker 1 should document this in the docstring or `FEATURES.md`'s `Scalar field override semantics` entry for clarity; it is not a bug, it is the same "per-subclass declaration" contract as relations.
- **Mutable-default-argument hazard.** `consumer_authored_fields: frozenset[str] = frozenset()` is the default argument shape in `_build_annotations`'s signature at `types/base.py:541`. `frozenset()` is immutable, so the default is safe. The new `consumer_annotated_scalar_fields: frozenset[str] = frozenset()` field on `DjangoTypeDefinition` uses the same pattern (and `DjangoTypeDefinition` is a `@dataclass`, where mutable defaults of mutable types must use `field(default_factory=...)` — but `frozenset()` is immutable, so the bare default is allowed). The spec uses `frozenset()` literals throughout to match the existing siblings.
- **`finalize_django_types()` interaction.** Annotation-only overrides land in `cls.__annotations__` at `__init_subclass__` time (before finalize). `finalize_django_types()` does not re-read `cls.__annotations__` for the override-routing decision — it only resolves pending relations and decorates with `strawberry.type(...)`. The Strawberry decorator reads `cls.__annotations__` to build `__strawberry_definition__.fields`; under this card the consumer's annotation is what's in the dict, so the resulting Strawberry field type matches the consumer's override. This is the end-to-end contract that the Slice 1 `test_annotation_only_scalar_override_survives_strawberry_finalization` test pins.

## Test strategy

All new tests land in `tests/types/test_definition_order.py` — the existing host for the override-contract matrix (per [Decision 5](#decision-5--test-placement-and-the-skipped-tests-fate)). The single exception is the rev3 M2 / rev6 L3 default placement for `test_annotation_override_of_arrayfield_with_nested_array_is_allowed`, which lives in `tests/types/test_converters.py` beside the existing `_FakeArrayField` fixture. The rev6 L2 `test_annotation_override_does_not_populate_shared_enum_cache_for_co_resident_types` lives in `tests/types/test_definition_order.py` by default (the override-contract host) but Worker 1 may park it in `tests/types/test_converters.py` if a planning-time concern surfaces.

The Slice 1 test cluster has 18 tests total (rev7 expanded from rev6's 16):

**Four core override tests** — cover the new annotation-only scalar override path:

- `test_annotation_only_scalar_field_override_wins_over_synthesized` — **pre-finalize annotation contents.** Assert `cls.__annotations__[field_name]` is the consumer's type immediately after `__init_subclass__`.
- `test_annotation_only_scalar_override_populates_definition_metadata` — **`consumer_*_fields` introspection.** Assert the new `consumer_annotated_scalar_fields` set on `DjangoTypeDefinition` contains exactly the overridden name, that `consumer_authored_fields` contains it (transitively, via the union), and that `consumer_assigned_scalar_fields` does NOT (because the override is annotation-only).
- `test_annotation_only_scalar_override_does_not_emit_synthesized_annotation` — **`_build_annotations` skip.** Assert the synthesized annotations dict — the first element of `_build_annotations`'s return tuple — does NOT contain the override-field key. Whitebox-but-stable: the synthesized dict is what feeds the post-merge line at `types/base.py:138` (pre-Slice-1), so its shape is the contract under test.
- `test_annotation_only_scalar_override_survives_strawberry_finalization` — **End-to-end Strawberry schema.** Build a `strawberry.Schema(query=Query)` with a query field returning the type, execute an introspection query of shape `__type(name: "...") { fields { name type { kind name ofType { kind name } } } }`, unwrap through `kind == "NON_NULL"`, and assert the terminal `ofType.name` matches the consumer's annotation.

**Four converter-bypass tests** (H2 fix; rev6 L2 — added cross-type cache test) — pin the bypass contract from [Decision 7a](#decision-7a--converter-validation-bypass-h2-fix):

- `test_annotation_override_of_unsupported_scalar_field_type_is_allowed` — annotation override is a recourse parallel to `Meta.exclude` for unsupported scalar field types.
- `test_annotation_override_of_grouped_choices_field_is_allowed` — annotation override bypasses `convert_choices_to_enum`'s grouped-choices rejection; `registry.get_enum(model, field_name)` is `None` for the overridden field.
- `test_annotation_override_of_arrayfield_with_nested_array_is_allowed` — annotation override bypasses `convert_scalar`'s nested-`ArrayField` rejection. Default placement: `tests/types/test_converters.py`.
- `test_annotation_override_does_not_populate_shared_enum_cache_for_co_resident_types` (rev6 L2) — pins the cross-type behavior change Decision 7a flagged. Two `DjangoType`s on the same `choices=` column, one overriding and one not: the non-overriding type populates the shared enum cache, the overriding type does not (its GraphQL surface uses the consumer's annotation; the cache is populated by the non-overriding type alone).

**Ten Relay-collision tests** (H1 fix; rev6 expanded — added H1 sibling-annotation accept and L1 inheritance non-trigger; rev7 expanded — split stringified-NodeID into resolved + unresolved variants, added typo-lookalike reject, inverted inheritance test) — pin [Decision 7](#decision-7--relay-id-override-collision):

- `test_consumer_id_annotation_on_relay_node_type_raises` — `ConfigurationError` at class-creation time with message pointing at `relay.NodeID[...]` (annotation reject path).
- `test_consumer_id_assigned_strawberry_field_on_relay_node_type_raises` — `ConfigurationError` at class-creation time with message pointing at `resolve_id`, `relay.NodeID[...]`, and the rev6 M1 + rev7 M2 resolver-backed sibling-field workaround (assigned reject path; rev4 M1 — small intentional behavior change; rev7 M2 — the workaround example is resolver-backed, not metadata-only).
- `test_consumer_id_unresolved_non_nodeid_string_on_relay_node_type_raises` — `id: "MissingType"` (unresolved non-NodeID string) raises (rev5 M1 — pins the narrow fail-soft contract; without this test, typos would slip past the guard at class-creation time).
- `test_consumer_id_typo_lookalike_nodeid_string_on_relay_node_type_raises` (rev7 H1) — `id: "NotNodeID[int]"` (and similar prefixed-substring lookalikes like `"MyNodeID[int]"`) raise via the tightened token-shaped regex. Pins that the rev7 H1 `(?:^|\.)NodeID\[` predicate rejects what the rev6 `"NodeID[" in raw` substring check accepted as false positives.
- `test_consumer_id_relay_nodeid_annotation_on_relay_node_type_is_accepted` — `id: relay.NodeID[int]` direct-form passes the guard (escape-hatch accept path; end-to-end success).
- `test_consumer_id_resolved_string_relay_nodeid_annotation_on_relay_node_type_is_accepted_end_to_end` (rev4 H1 + rev7 H1 rename) — `id: "relay.NodeID[int]"` stringified form with `relay` importable at module scope; assert class creation + finalize + schema build all succeed. Pins the resolved-string end-to-end path.
- `test_consumer_id_unresolved_nodeid_shaped_string_on_relay_node_type_passes_guard_only` (rev7 H1) — `id: "relay.NodeID[int]"` stringified form with `relay` NOT importable from the class's resolution scope; assert ONLY that class creation succeeds (the fail-soft regex match suppresses the package guard). Pins the guard-only-suppression contract; finalize / schema build are explicitly NOT asserted because Strawberry's downstream resolution operates against the same module globals and may still fail there.
- `test_consumer_id_resolved_relay_nodeid_with_unresolved_sibling_annotation_is_accepted` (rev6 H1) — directly-resolved `id: relay.NodeID[int]` alongside a forward-referenced sibling annotation passes the guard (pins the rev6 H1 fail-soft fix for sub-case 2 — without this test, the rev5 fail-soft falsely rejected the valid escape hatch).
- `test_consumer_non_id_scalar_override_on_relay_node_type_is_accepted` — non-`id` consumer override on a Relay-Node-shaped type passes the guard (custom-pk / non-collision accept path; rev6 L3 — `description: int` recipe is the default).
- `test_inherited_id_annotation_on_relay_node_subclass_is_handled_by_pk_suppression` (rev6 L1 + rev7 M1 — inverted contract) — inherited `id: int` annotation on a Relay-Node-shaped subclass does NOT trigger the guard at class-creation time, AND `strawberry.Schema(...)` succeeds because `_build_annotations`'s pk-suppression branch strips the synthesized `id` and the post-merge reassignment leaves the child without an `id` annotation; Strawberry applies the Relay-supplied `id: GlobalID!` and `resolve_id_attr()` falls back to `"pk"`. Pins the corrected rev7 M1 contract (rev6's "Strawberry's `ValueError` is the failure mode" framing was wrong).

Slice 2 has no new tests — it deletes the previously-skipped `test_consumer_annotation_overrides_synthesized`. The full-suite pass on Slice 2 is the only test-side contract.

Slices 3 / 4 / 5 are documentation-only and have no test deltas. Coverage stays at 100% because the new definition field is exercised by Slice 1 tests, the new collection branch in `__init_subclass__` is exercised by every override test in `tests/types/test_definition_order.py`, the new Relay-collision guard is exercised by all ten H1 tests (four reject + six accept including the rev6 H1 sibling-annotation accept and the rev7 M1 inheritance pk-suppression accept), the `_id_annotation_is_relay_node_id` detection helper's resolved-success path is hit by `test_consumer_id_relay_nodeid_annotation_on_relay_node_type_is_accepted` and `test_consumer_id_resolved_string_relay_nodeid_annotation_on_relay_node_type_is_accepted_end_to_end`, the resolved-reject path is hit by `test_consumer_id_annotation_on_relay_node_type_raises`, the fail-soft-sub-case-1-accept path (rev7 H1 regex match) is hit by `test_consumer_id_unresolved_nodeid_shaped_string_on_relay_node_type_passes_guard_only`, the fail-soft-sub-case-1-reject paths are hit by `test_consumer_id_unresolved_non_nodeid_string_on_relay_node_type_raises` and `test_consumer_id_typo_lookalike_nodeid_string_on_relay_node_type_raises` (the latter pins the rev7 H1 regex rejection of prefixed-substring lookalikes), the fail-soft-sub-case-2-accept path (rev6 H1) is hit by `test_consumer_id_resolved_relay_nodeid_with_unresolved_sibling_annotation_is_accepted`, and the converter-bypass paths are exercised by the four H2 / rev6 L2 tests (unsupported / grouped-choices / nested-array / cross-type-cache).

## Definition of done

- [ ] Every Slice 1 / Slice 2 / Slice 3 checkbox in [Slice checklist](#slice-checklist) is checked.
- [ ] `tests/types/test_base.py:454-465` (`test_consumer_annotation_overrides_synthesized`) is deleted per [Decision 5](#decision-5--test-placement-and-the-skipped-tests-fate) and rev6 L3 (delete is the default); no `@pytest.mark.skip` block referencing "Deferred scalar-field override behavior" remains.
- [ ] All 18 Slice 1 tests pass (four core overrides + four converter-bypass + ten Relay-collision tests — four reject + six accept). Test placement: the override-contract host (`tests/types/test_definition_order.py`) for the core overrides, the Relay-collision tests, and the cross-type cache test (rev6 L2); the converter test host (`tests/types/test_converters.py`) for the nested-`ArrayField` bypass test (rev6 L3 — default placement).
- [ ] `uv run pytest` passes locally with 100% package coverage.
- [ ] `uv run ruff check .` passes.
- [ ] `uv run ruff format --check .` passes.
- [ ] `git diff --check` passes.
- [ ] `docs/FEATURES.md`'s `Scalar field override semantics` entry reads `shipped (0.0.6)` (Slice 5).
- [ ] `docs/FEATURES.md`'s `Scalar field conversion` entry names annotation override as a parallel recourse to `Meta.exclude` for unsupported scalar fields (Slice 5; H2 fix).
- [ ] `docs/FEATURES.md`'s `Scalar field override semantics` body names the rev6 M1 + rev7 M2 metadata-route limitation: field-level GraphQL metadata on the Relay-supplied `id` is not configurable in `0.0.6`; the documented workaround is a **resolver-backed sibling field** (`@strawberry.field(description="…") def display_id(self) -> strawberry.ID: return str(self.pk)`) carrying the metadata AND a value source, with the Relay-supplied `id` left undecorated. A metadata-only sibling without a resolver would build but fail at query time (Strawberry's default resolver looks up `display_id` as a Django model attribute) and is NOT recommended (Slice 5).
- [ ] `KANBAN.md` shows `DONE-015-0.0.6` with the verbatim body from Slice 5 above; `WIP-ALPHA-015-0.0.6` is no longer present.
- [ ] `CHANGELOG.md` `[Unreleased]` carries the five entries from Slice 5 (`Added` annotation-only, `Added` introspection field, `Changed` converter-bypass, `Added` Relay annotation-collision guard, `Changed` assigned-id rejection on Relay-Node-shaped types — the last with the rev6 M1 sibling-field workaround acknowledgment).
- [ ] Slice 4 version-bump quintet is verified by `grep` rather than blind edits — every checkbox is a no-op if `spec-013-deferred_scalars-0_0_6.md` or `spec-014-meta_primary-0_0_6.md` already landed the bump.
- [ ] No new public top-level symbol; no new `Meta.*` key; `django_strawberry_framework/__init__.py.__all__` is unchanged.
