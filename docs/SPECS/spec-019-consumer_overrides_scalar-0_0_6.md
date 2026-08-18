# Spec: Consumer override semantics for scalar fields

Target release: `0.0.6`.
Status: shipped (`0.0.6`, 2026-05-19); archived. Card `DONE-019-0.0.6`.
Owner: package maintainer.
Predecessors: [`docs/GLOSSARY.md`][glossary] (entries [`DjangoType`][glossary-djangotype], [`Scalar field conversion`][glossary-scalar-field-conversion], [`Scalar field override semantics`][glossary-scalar-field-override-semantics], [`Definition-order independence`][glossary-definition-order-independence], [`Relation handling`][glossary-relation-handling]), [`KANBAN.md`][kanban] card `DONE-019-0.0.6`.
Card line: ["Consumer override semantics (scalar fields) — extends the `DONE-010-0.0.4` relation-field override contract to scalar fields and closes out the remaining `0.0.6` patch."][kanban]
Deliberation: the review history, the alternatives each Decision rejected, and every claim this spec once made and may no longer make live in [`docs/SPECS/appx/spec-019-consumer_overrides_scalar-0_0_6-rationale.md`][spec-019-rationale]. This file states only what holds at `HEAD`.

**The card shipped as `015`.** The build commit is `a357c68c`; the 2026-07-30 board renumber moved it to `019`. The landed tests, and `CHANGELOG.md`'s tracking label, still carry the pre-renumber number — see the rationale companion's provenance section before chasing `git log` for "spec-019".

## Key glossary references

Skim these [`docs/GLOSSARY.md`][glossary] entries first — they anchor the vocabulary used throughout the spec:

- [`DjangoType`][glossary-djangotype] — the base class whose scalar-override gap this card closes.
- [`Scalar field conversion`][glossary-scalar-field-conversion] — the auto-synthesized scalar annotation path this card lets consumers override.
- [`Scalar field override semantics`][glossary-scalar-field-override-semantics] — `shipped (0.0.6)`; this card is what flipped it.
- [`Specialized scalar conversions`][glossary-specialized-scalar-conversions] — home of the `ArrayField`, `HStoreField`, and [`BigInt`][glossary-bigint-scalar] mappings whose rejection paths the converter-bypass contract explicitly skips for overridden fields.
- [`Relation handling`][glossary-relation-handling] — the relation-override path whose annotation-only contract this card mirrors for scalars.
- [`Relay Node integration`][glossary-relay-node-integration] — the broader Relay contract the `id` collision guard protects; documents `relay.NodeID[...]` as the supported consumer escape hatch.
- [`Definition-order independence`][glossary-definition-order-independence] — the foundation slice (`DONE-010-0.0.4`) that pinned the relation-field override contract; this card extends the same shape to scalars.
- [`ConfigurationError`][glossary-configurationerror] — raised at type-creation time for unsupported shadow shapes; this card adds one new error site (the Relay collision guard in Slice 1 per [Decision 7](#decision-7--relay-id-override-collision)).

Project conventions to follow:

- [`AGENTS.md`][agents] — schema testing via `schema.execute_sync`. **Note:** `AGENTS.md` prohibits `CHANGELOG.md` edits without explicit permission; [Slice 5](#slice-checklist) grants that permission for this card's own entries.
- [`CONTRIBUTING.md`][contributing] — 100% coverage target; release-bump checklist.
- [`KANBAN.md`][kanban] — card-ID format; column movement at Slice 5.
- [`docs/TREE.md`][tree] — package layout; tests mirror source one-to-one.

## Slice checklist

Each top-level item maps to one commit in the [Implementation plan](#implementation-plan).

- [ ] Slice 1: Track annotation-only scalar overrides on `DjangoTypeDefinition`
  - [ ] In `django_strawberry_framework/types/base.py::DjangoType.__init_subclass__` (consumer-field collection block beginning with `consumer_annotations = dict(cls.__annotations__)`), collect a new `consumer_annotated_scalar_fields` frozenset parallel to `consumer_annotated_relation_fields`. Walks the same `consumer_annotations = dict(getattr(cls, "__annotations__", {}))` mapping but filters on `not field.is_relation` instead of `field.is_relation`. (See [Decision 1](#decision-1--annotation-only-scalar-override-collection).)
  - [ ] Add `consumer_annotated_scalar_fields: frozenset[str] = frozenset()` field to `django_strawberry_framework/types/definition.py::DjangoTypeDefinition` in the **grouped-by-style** order (matching Decision 3's sample): annotated-relation, annotated-scalar, assigned-relation, assigned-scalar. Land the cosmetic re-order of the existing two `consumer_assigned_*` lines in the same commit as the new field so the dataclass field order is internally consistent.
  - [ ] Union the new set into the existing `consumer_authored_fields` frozenset at `django_strawberry_framework/types/base.py::DjangoType.__init_subclass__ #"consumer_authored_fields = frozenset"`. The scalar branch of `_build_annotations` already short-circuits on `consumer_authored_fields` membership (`django_strawberry_framework/types/base.py::_build_annotations #"if field.name in consumer_authored_fields:"`, scalar branch) — once annotation-only scalars are members, synthesis is skipped for them, and the existing post-merge line `cls.__annotations__ = {**synthesized, **consumer_annotations}` at `django_strawberry_framework/types/base.py::DjangoType.__init_subclass__ #"cls.__annotations__ = {**synthesized, **consumer_annotations}"` leaves the consumer's annotation untouched. **No change to `_build_annotations` body.**
  - [ ] Plumb the new set through to `DjangoTypeDefinition` at the registration call site (`django_strawberry_framework/types/base.py::DjangoType.__init_subclass__ #"definition = DjangoTypeDefinition("`).
  - [ ] **Module-scope helpers for the Relay guard.** Land these in `django_strawberry_framework/types/base.py` **above** `DjangoType`'s class definition, before the guard bullet below. The guard body calls `_id_annotation_is_relay_node_id(cls)`, which calls `_has_node_id_marker(...)`, which uses `_NODEID_STRING_RE` — all three must exist at module scope when the guard executes. Imports to add at the top of `types/base.py`: `re`, `typing`, `Annotated` from `typing`, and `NodeIDPrivate` from `strawberry.relay.types`. Full bodies in [Decision 7](#decision-7--relay-id-override-collision)'s code block.
    - [ ] `_NODEID_STRING_RE = re.compile(r"(?:^|\.)NodeID\[")` — module-scope (compiled once per process).
    - [ ] `def _has_node_id_marker(hint: object) -> bool:` returning `typing.get_origin(hint) is Annotated and any(isinstance(arg, NodeIDPrivate) for arg in typing.get_args(hint))`.
    - [ ] `def _id_annotation_is_relay_node_id(cls: type) -> bool:` reading `cls.__annotations__["id"]` directly and dispatching on `isinstance(raw, str)` — string form to the regex, resolved form to `_has_node_id_marker`.
    - [ ] `def _is_relay_shaped(cls: type, interfaces: tuple[type, ...]) -> bool:` returning `any(issubclass(i, relay.Node) for i in interfaces) or issubclass(cls, relay.Node)` — the single source of truth for the Relay-shape predicate, read by both this card's collision guard and `_build_annotations`'s `suppress_pk_annotation`.
  - [ ] **Relay `id` collision guard.** After the `consumer_annotated_scalar_fields` / `consumer_assigned_scalar_fields` collections are built but before `_build_annotations` is invoked, detect: (a) `_is_relay_shaped(cls, interfaces)` is True for the `interfaces` tuple returned by `_validate_meta`; AND (b) the consumer authored an entry for the GraphQL field name `"id"` — either an annotation (`"id" in cls.__annotations__`; key-presence rather than value-truthiness, so unusual annotations like `id: None`, `id: Literal[None]`, or string forms that evaluate to false-y types are also detected) or an assignment (`isinstance(cls.__dict__.get("id"), StrawberryField)`). Two reject paths:
    - **Assigned `id = <StrawberryField>`**: always rejected on a Relay-Node-shaped type. The error message names three supported alternatives: `@classmethod resolve_id` for a custom id resolver, `id: relay.NodeID[<pk_type>]` for a custom id annotation, and a **resolver-backed sibling field** — e.g. `@strawberry.field(description="…") def display_id(self) -> strawberry.ID: return str(self.pk)` — for the field-level GraphQL metadata use case. This is a small intentional behavior change: previously consumers could write `@strawberry.field def id(self) -> relay.GlobalID: ...` and Strawberry would accept it. This card bans that pattern uniformly.
    - **Annotation `id: <type>` where `<type>` is not `relay.NodeID[...]`**: rejected. Detection reads `cls.__annotations__["id"]` and dispatches on the value's shape — a string is matched against the token-shaped regex `(?:^|\.)NodeID\[` (so `"relay.NodeID[int]"`, `"strawberry.relay.NodeID[int]"`, and `"NodeID[int]"` pass while prefixed-substring lookalikes such as `"NotNodeID[int]"` and `"MyNodeID[int]"` are rejected); a resolved object is checked for the `Annotated[T, NodeIDPrivate]` marker. Accepting a NodeID-shaped string is package-level guard suppression only — Strawberry's downstream schema construction resolves the same string against `cls`'s module globals and may still fail there if the consumer has not made the symbol importable. The error message points at `relay.NodeID[<pk_type>]` as the supported escape hatch. (See [Decision 7](#decision-7--relay-id-override-collision) for the helper bodies.) **Important: the predicate is keyed off the GraphQL field name `"id"`, not the model's pk name.** A model with `code = models.CharField(primary_key=True)` and a consumer `code: str` override does NOT trigger the guard — the GraphQL fields are `id: ID!` (from Relay) and `code: String!` (from the consumer), no collision.
  - [ ] Tests in `tests/types/test_definition_order.py` (the existing override-contract host, home of the three relation-override tests and the `test_assigned_scalar_field_override_keeps_consumer_resolver` test). The annotation-only scalar contract is the natural fourth sibling; placement matches the existing relation/scalar × annotation/assigned 2×2 matrix:
    - [ ] `test_annotation_only_scalar_field_override_wins_over_synthesized` (the headline test for this card): declare a `DjangoType` with a Django `CharField` selected and a consumer annotation `description: int` shadowing it. Pre-finalize, assert `cls.__annotations__["description"] is int`. Post-finalize, assert the same — and assert the Strawberry definition's field type matches the consumer's annotation, not the auto-synthesized `str`. This is the contract the test skipped at `tests/types/test_base.py` (the `test_consumer_annotation_overrides_synthesized` block, deleted in Slice 2) was the placeholder for.
    - [ ] `test_annotation_only_scalar_override_populates_definition_metadata`: assert `definition.consumer_annotated_scalar_fields == frozenset({"description"})`, `definition.consumer_authored_fields >= frozenset({"description"})`, and `definition.consumer_assigned_scalar_fields == frozenset()` (annotation-only, no assignment).
    - [ ] `test_annotation_only_scalar_override_does_not_emit_synthesized_annotation`: assert the synthesized annotations dict returned by `_build_annotations` does NOT contain `"description"` for the override case. (Pins that the short-circuit fires; without this we could still merge consumer-over-synthesized but the side-effect of double-walking the field path could regress later.)
    - [ ] `test_annotation_only_scalar_override_survives_strawberry_finalization`: calls [`finalize_django_types`][glossary-finalize-django-types]`()`, builds a `strawberry.Schema(query=Query)` with a query field returning the type, and runs `schema.execute_sync(...)` against an introspection query of the shape `__type(name: "<TypeName>") { fields { name type { kind name ofType { kind name } } } }`. A non-nullable Django scalar surfaces in GraphQL as `Int!` — `type.kind == "NON_NULL"` and `type.name is None`; the terminal scalar name (`"Int"`) lives at `type.ofType.name`. The test unwraps through `NON_NULL` and asserts the terminal `ofType.name` matches the consumer's annotation. The existing `_introspect_field_type` helper pattern at `tests/types/test_converters.py::_introspect_field_type` is an acceptable substitute — the contract is "unwrap to the terminal type and assert that". Pins the end-to-end contract.
    - [ ] **Converter-bypass regressions (four tests).** The short-circuit skips `convert_scalar(...)` for the overridden field, which means every converter-side validation and side effect is bypassed for that field. The bypass is the intended consumer-authoritative contract (see [Decision 7a](#decision-7a--converter-validation-bypass)), but it needs explicit tests so future readers understand the surface and so converter changes do not silently re-introduce validation against an overridden field:
      - [ ] `test_annotation_override_of_unsupported_scalar_field_type_is_allowed`: **first add** a minimal `_FakeUnsupportedField(models.Field)` fixture at the top of `tests/types/test_definition_order.py` — placement is mandatory there (the "18 of 19 Slice 1 tests land in `test_definition_order.py`" rule must stay true; only the nested-`ArrayField` bypass test gets the converter-host exception, and that exception has a concrete fixture-locality reason — `_FakeArrayField` already lives there). The fixture is a one-line `Field` subclass whose MRO has no `SCALAR_MAP` match; it does not exist in the test tree pre-Slice-1, so this is a real fixture-creation step. Then declare a `DjangoType` selecting that field. Without the override, `convert_scalar` raises [`ConfigurationError`][glossary-configurationerror]. With a consumer `myfield: str` annotation (or `int` — any Strawberry-supported scalar annotation; **NOT** `bytes`, which Strawberry's schema-construction pass rejects as an unexpected Python type and would create a false failure unrelated to the bypass contract), assert: (a) no error is raised at class-creation time, (b) `definition.consumer_annotated_scalar_fields` contains the field name, and (c) `finalize_django_types()` succeeds. The consumer's override is the recourse for unsupported scalars; [`Meta.exclude`][glossary-metaexclude] is still the recourse for "drop the field entirely".
      - [ ] `test_annotation_override_of_grouped_choices_field_is_allowed`: declare a `DjangoType` selecting a Django `CharField` with grouped `choices=[("group1", [("a", "A"), ("b", "B")])]`. Without the override, `convert_choices_to_enum` raises `ConfigurationError` containing `"grouped-choices"` (existing test `tests/types/test_converters.py::test_grouped_choices_form_rejected` pins this). With a consumer `status: str` annotation, assert no error is raised, the type is finalizable, and `registry.get_enum(model, "status")` is `None` (enum registration is bypassed along with annotation synthesis).
      - [ ] `test_annotation_override_of_arrayfield_with_nested_array_is_allowed`: real `django.contrib.postgres.fields.ArrayField` testing requires the `_ARRAY_FIELD_CLS` monkeypatch + `_FakeArrayField` fixture pattern that lives in `tests/types/test_converters.py::_FakeArrayField` (every existing `ArrayField` test uses it; the production code at `django_strawberry_framework/types/converters.py::_resolve_array_field` soft-imports the real class and CI environment-dependence is the failure mode without the monkeypatch). **Place this single test in `tests/types/test_converters.py`** beside the existing `_FakeArrayField` tests so the fixture lookup stays local. **The model-field name and the consumer-annotation name MUST match** — mirror the existing converter tests' `arr`-named field, so the consumer annotation is `arr: list[list[int]]`. A name mismatch means the override-collection path never fires (the consumer annotation does not name a selected model field) and the test exercises the rejection path instead — false-passing for the wrong reason. Test body: `monkeypatch.setattr(converters, "_ARRAY_FIELD_CLS", _FakeArrayField)`; build a `_FakeArrayField(_FakeArrayField(models.IntegerField()))` instance registered as a model field named `arr`; declare a `DjangoType` selecting that field with a consumer `arr: list[list[int]]` annotation; assert no error is raised at class-creation time and `finalize_django_types()` succeeds. Verify that the existing `tests/types/test_converters.py::test_array_field_multidim_rejected_via_fake_sentinel` nested-array rejection test still passes (un-overridden nested arrays still raise).
      - [ ] `test_annotation_override_does_not_populate_shared_enum_cache_for_co_resident_types`: pins the Decision 7a cross-type flag that two `DjangoType`s on the same model with the same `choices=` column — one overriding and one not — get the fresh enum from the non-overriding type alone. Declare a single Django model with a non-grouped `status` `CharField(choices=[...])`. Declare two `DjangoType`s on that model: `OverrideType` with `class Meta: model = M; primary = True; fields = ("status",)` and a consumer `status: str` annotation (override); `NonOverrideType` with `class Meta: model = M; fields = ("status",)` (no override). `finalize_django_types()`. Assert: (a) `registry.get_enum(model, "status")` returns a non-`None` enum class (populated by `NonOverrideType`'s `convert_scalar` call); (b) building a `strawberry.Schema` and introspecting `NonOverrideType.status` returns the generated enum's GraphQL name; (c) introspecting `OverrideType.status` returns `String!` (the consumer's annotation). Pins both halves of the contract — the bypass on the overriding type does not poison the cache for the non-overriding type, and the cache entry from the non-overriding type does not leak into the overriding type's GraphQL surface. **Test placement: `tests/types/test_definition_order.py`, mandatory** — the test exercises override-vs-non-override cross-talk, not converter-internal behavior, so it belongs with the rest of the override-contract matrix.
  - [ ] **Relay collision tests (eleven).** New tests in `tests/types/test_definition_order.py` alongside the four-corner cluster:
    - [ ] `test_consumer_id_annotation_on_relay_node_type_raises`: declare a `DjangoType` with [`Meta.interfaces`][glossary-metainterfaces]` = (relay.Node,)` and an `id: int` (or `id: str`) consumer annotation. Assert `ConfigurationError` raised at class-creation time (before `finalize_django_types()`), with message containing both `"relay.NodeID"` and `"GlobalID"`. Pins the early-raise contract for the `Meta.interfaces` declaration shape; without the guard, the consumer would see a Strawberry-side `ValueError` only at `strawberry.Schema(...)` construction, which is the wrong UX surface.
    - [ ] `test_consumer_id_annotation_on_direct_relay_node_subclass_raises`: declare a `DjangoType` that directly subclasses `relay.Node` — i.e. `class DirectRelayChild(DjangoType, relay.Node): id: int; class Meta: model = Category; fields = ("id", "name")` (NO `Meta.interfaces` line). Assert `ConfigurationError` raised at class-creation time with the same message contract as the `Meta.interfaces` variant. Pins the second half of `_is_relay_shaped`'s disjunction — without this test, an implementation wiring only the `interfaces` half would pass every other Relay-collision test while leaving `class CategoryNode(DjangoType, relay.Node): id: int` to fall through to the downstream Strawberry `ValueError`. Parametrizing `test_consumer_id_annotation_on_relay_node_type_raises` over both declaration styles is an equivalent discharge; the contract is "the annotation reject path fires for both shapes". Note: the assigned-`id` reject path is deliberately NOT parametrized over the direct-inheritance shape — the high-value pin is annotation-side.
    - [ ] `test_consumer_id_assigned_strawberry_field_on_relay_node_type_raises`: declare a `DjangoType` with `Meta.interfaces = (relay.Node,)` and an assigned `id = strawberry.field(resolver=...)` (or `@strawberry.field def id(self) -> relay.GlobalID: ...` decorator-style). Assert `ConfigurationError` raised at class-creation time with message containing **all three** of `"resolve_id"`, `"relay.NodeID"`, and one of `"display_id"` / `"sibling field"`. Pins the intentional ban on assigned `id` overrides on Relay-Node-shaped types and the resolver-backed sibling-field workaround in the error message.
    - [ ] `test_consumer_id_unresolved_non_nodeid_string_on_relay_node_type_raises`: declare a `DjangoType` with `Meta.interfaces = (relay.Node,)` and a stringified `id: "MissingType"` annotation (a typo, or a forward reference to a non-existent class). Assert `ConfigurationError` raised at class-creation time with message containing both `"relay.NodeID"` and `"GlobalID"`. The helper sees a string that does not match `(?:^|\.)NodeID\[` and rejects. Without this test, a typo like `id: "Stirng"` would slip past the guard at class-creation time and surface only as a Strawberry schema-construction error later — exactly the failure mode the guard exists to prevent.
    - [ ] `test_consumer_id_typo_lookalike_nodeid_string_on_relay_node_type_raises`: declare a `DjangoType` with `Meta.interfaces = (relay.Node,)` and a stringified `id: "NotNodeID[int]"` annotation — the prefix means the string DOES contain `"NodeID["` as a substring but is NOT a token-shaped NodeID reference. Assert `ConfigurationError` raised at class-creation time with message containing both `"relay.NodeID"` and `"GlobalID"`. Verify a `"MyNodeID[int]"` variant in the same test (parametrize or add a second assertion). Pins that `_NODEID_STRING_RE` requires a start-of-string or dot boundary before `NodeID[`; a plain substring test would accept these false positives.
    - [ ] `test_consumer_id_relay_nodeid_annotation_on_relay_node_type_is_accepted`: declare a `DjangoType` with `Meta.interfaces = (relay.Node,)` and an `id: relay.NodeID[int]` consumer annotation. Assert no `ConfigurationError` at class-creation time; assert `finalize_django_types()` succeeds; assert `strawberry.Schema(...)` builds. Pins that the guard does NOT reject the advertised escape hatch. Mirrors the existing `tests/types/test_relay_interfaces.py::test_composite_pk_with_explicit_node_id_annotation_is_accepted` pattern, applied to a plain (non-composite-pk) Relay-Node-shaped type to exercise this card's guard specifically.
    - [ ] `test_consumer_id_resolved_string_relay_nodeid_annotation_on_relay_node_type_is_accepted_end_to_end`: declare a `DjangoType` with `Meta.interfaces = (relay.Node,)` and an explicit stringified `id: "relay.NodeID[int]"` consumer annotation, **with `relay` imported at module scope** so the string resolves cleanly under Strawberry's downstream schema-construction resolution. Assert no `ConfigurationError` at class-creation time; assert `finalize_django_types()` succeeds; assert `strawberry.Schema(...)` builds; assert the introspected `id` field is `ID!` (the Relay-supplied interface field). Pins that the string form passes the package guard **and** that Strawberry's downstream pipeline accepts the same string.
    - [ ] `test_consumer_id_unresolved_nodeid_shaped_string_on_relay_node_type_passes_guard_only`: declare a `DjangoType` with `Meta.interfaces = (relay.Node,)` and an explicit stringified `id: "relay.NodeID[int]"` consumer annotation, **with `relay` NOT importable** from the class's resolution scope. Assert ONLY that class creation succeeds — no `ConfigurationError` at `__init_subclass__` time — because the regex match on the raw string accepts by shape alone. **Do NOT assert** `finalize_django_types()` or `strawberry.Schema(...)` succeed; Strawberry's downstream resolution operates against the same module globals and will fail with its own error if the consumer has not made `relay` resolvable. The spec contract for this case is "package guard suppressed at class-creation time"; full end-to-end resolution is the consumer's responsibility. **Landed recipe** (recorded as the shipped spelling, not as a choice to re-make): (1) generate a unique synthetic module name via `stub_name = f"spec015_unresolved_relay_stub_{uuid.uuid4().hex}"` — the `spec015_` prefix is the pre-renumber card number and is the landed identifier, deliberately not renamed; (2) register `sys.modules[stub_name] = types.ModuleType(stub_name)` and **assert** the stub module's `__dict__` has no `"relay"` key; (3) build the `DjangoType` via `types.new_class("UnresolvedRelayChild", (DjangoType,), {}, _body)` where `_body` mutates the class namespace to set `__module__ = stub_name`, `__annotations__ = {"id": "relay.NodeID[int]"}`, and a `Meta` class with `model = Category` and `interfaces = (relay.Node,)`; (4) assert ONLY that `types.new_class(...)` returns without raising; (5) wrap the body in `try/finally` so **both** `sys.modules.pop(stub_name, None)` **and** `registry.clear()` run even if the assertion fails — the synthetic type registers against `Category` the moment class creation passes the guard, and a stale co-resident type poisons the cross-type cache test if it runs later in the same session.
    - [ ] `test_consumer_id_resolved_relay_nodeid_with_unresolved_sibling_annotation_is_accepted`: declare a `DjangoType` with `Meta.interfaces = (relay.Node,)`, a directly-resolved `id: relay.NodeID[int]` consumer annotation, AND a forward-referenced sibling annotation like `items: list["AdminItemType"]` that does not resolve at class-creation time. Assert no `ConfigurationError` at class-creation time. Pins that the guard's verdict on `id` is **independent of every other annotation on the class**: the helper reads `cls.__annotations__["id"]` and nothing else, so an unresolvable sibling cannot influence the outcome. This is a realistic pattern for `DjangoType`s with forward-referenced relation annotations, and a detection mechanism that evaluated the whole class would have to recover from it explicitly.
    - [ ] `test_consumer_non_id_scalar_override_on_relay_node_type_is_accepted`: declare a `DjangoType` on a Relay-Node-shaped type with a non-`id` consumer scalar override (recipe: `description: int`). Assert no `ConfigurationError` is raised. Pins that the guard is keyed off the GraphQL field name `"id"`, not the model's pk name — a consumer who overrides a non-`id` field on a Relay-Node-shaped type does not collide with `Node.id` and must not be rejected.
    - [ ] `test_inherited_id_annotation_on_relay_node_subclass_is_handled_by_pk_suppression`: declare a base `DjangoType` subclass `BaseWithId` with an `id: int` annotation but no `Meta` (so `__init_subclass__` short-circuits the collection pipeline for the base). Then declare a child `ChildRelayType(BaseWithId)` with `class Meta: model = M; interfaces = (relay.Node,)`. Assert: (a) no `ConfigurationError` at class-creation time — the guard's `"id" in cls.__annotations__` predicate is False for the child, because inherited annotations do not land in the subclass's own `__annotations__` dict; (b) **`strawberry.Schema(query=Query, types=[ChildRelayType])` SUCCEEDS**. `_build_annotations`'s `suppress_pk_annotation and field.name == pk_name` branch suppresses the synthesized scalar `id` annotation for the child, and the post-merge line `cls.__annotations__ = {**synthesized, **consumer_annotations}` replaces the child's `__annotations__` with a dict containing neither the inherited `id: int` nor a synthesized one. Strawberry's `@strawberry.type` reads the child's assigned `__annotations__`, sees no `id`, applies Relay's `id: GlobalID!`, and `resolve_id_attr()` falls back to `"pk"`; (c) the introspected `id` field type is `ID!` (the Relay-supplied interface field), not `Int!`; (d) optionally, `ChildRelayType.resolve_id_attr() == "pk"`. Pins the inheritance behavior: the guard does NOT walk the MRO, and pk-suppression in `_build_annotations` silently handles the inherited `id: int` case, so no Strawberry `ValueError` fires. Without this test, future changes to the pk-suppression branch could regress the inherited-`id` corner without surfacing.
- [ ] Slice 2: Retire the skipped `test_consumer_annotation_overrides_synthesized`
  - [ ] Delete the `test_consumer_annotation_overrides_synthesized` function at `tests/types/test_base.py`, its `@pytest.mark.skip` decorator, and its reason text. Slice 1's new tests cover the contract more thoroughly (pre-finalize + post-finalize + introspection + end-to-end Strawberry schema query), and `tests/types/test_definition_order.py` is the canonical override-contract host — a one-line smoke test sitting alone in `test_base.py` would invite drift between two locations for one contract. (See [Decision 5](#decision-5--test-placement-and-the-skipped-tests-fate).)
  - [ ] Remove the `CATEGORY_SCALAR_FIELDS` module constant only if it becomes unused; check via `grep` before deleting.
- [ ] Slice 3: Document the four-corner override contract in `_consumer_assigned_fields`'s docstring
  - [ ] After Slice 1 lands, the four-corner override matrix (`relation × annotation`, `relation × assigned`, `scalar × annotation`, `scalar × assigned`) is symmetric and complete. Update the `_consumer_assigned_fields` docstring at `django_strawberry_framework/types/base.py::_consumer_assigned_fields` so it names the parallel `consumer_annotated_relation_fields` / `consumer_annotated_scalar_fields` collection sites in `__init_subclass__`, the four `consumer_*_fields` sets on `DjangoTypeDefinition`, and the single `consumer_authored_fields` short-circuit in `_build_annotations`. Documentation only — no behavior change. Verify no other docstrings need parallel updates (`_build_annotations` already documents the relation+scalar consumer-authored branches; if it does, no change there either).
- [ ] Slice 4: Atomic version-bump quintet (single commit). Same shape as `spec-017-deferred_scalars-0_0_6.md` Slice 5 and `spec-018-meta_primary-0_0_6.md` Slice 5: covers programmatically-checked sites only (`pyproject.toml`, `__init__.py`, `tests/base/test_init.py`'s pinned `__version__`, `docs/GLOSSARY.md`'s "Current package version" line, `uv.lock`). The two consumer-facing version strings (`README.md`, `docs/README.md`) move in Slice 5. **At spec-authoring time the tree is already at `0.0.6` from the two prior `0.0.6` cards' closeout slices**, so every checkbox below is expected to be a no-op. The slice still exists in the plan so final verification explicitly `grep`s for stale `0.0.5` strings before marking complete.
  - [ ] `pyproject.toml` — `version = "0.0.6"` (no-op if already at `0.0.6` from any prior `0.0.6` card).
  - [ ] `django_strawberry_framework/__init__.py` — `__version__ = "0.0.6"` (no-op if already bumped).
  - [ ] `tests/base/test_init.py` — pinned `__version__` assertion to `"0.0.6"` (no-op if already bumped).
  - [ ] `docs/GLOSSARY.md` — "Current package version: `0.0.6`" line (no-op if already bumped).
  - [ ] `uv.lock` — re-lock with `uv lock` (no-op if already at `0.0.6`).
  - [ ] **Prior-`0.0.6`-card note.** The `0.0.6` line carries four cards: `DONE-016-0.0.6`, `DONE-017-0.0.6`, `DONE-018-0.0.6`, and this card (`DONE-019-0.0.6`). The first card to land does the real bump; every subsequent card's Slice 4 is a no-op. Final verification MUST `grep` for stale `0.0.5` strings rather than blindly editing — if the bump has already happened, mark every checkbox above complete without re-editing.
- [ ] Slice 5: Docs, KANBAN, CHANGELOG, archive (separate commit; may follow Slice 4 by any interval).
  - [ ] Root `README.md` — confirm the package-version line reads `0.0.6` (no-op if any prior `0.0.6` card already bumped it).
  - [ ] `docs/README.md` — confirm the "shipped today is `0.0.6`" line (no-op if any prior `0.0.6` card already bumped it). Add a one-line mention of scalar override symmetry to the shipped-capability summary.
  - [ ] `docs/GLOSSARY.md` entries updated:
    - [`Scalar field override semantics`][glossary-scalar-field-override-semantics] → `shipped (0.0.6)`. Rewrite the body to describe the delivered contract: annotation-only and assigned-`strawberry.field` scalar overrides both supported, with the same `consumer_authored_fields` short-circuit; opt-out via [`Meta.exclude`][glossary-metaexclude]; field metadata via the assigned-`strawberry.field(...)` path; **converter validations bypassed for overridden fields** (consumer-authoritative contract — name unsupported-scalar override, grouped-choices override, and nested-`ArrayField` override as the three behavior changes worth highlighting); **`relay.Node` `id` collision rejected at type-creation time**, with two sub-restrictions: (1) assigned `id = <StrawberryField>` overrides are uniformly rejected on Relay-Node-shaped types (the supported alternatives are `relay.NodeID[<pk_type>]` for a custom id annotation, `@classmethod resolve_id` for a custom id resolver, and a **resolver-backed sibling field** — `@strawberry.field(description="…") def display_id(self) -> strawberry.ID: return str(self.pk)` — for the field-level GraphQL metadata use case, since the ban removes the only path for attaching `description`/`deprecation_reason`/`directives` to the Relay-supplied `id`; a metadata-only sibling like `display_id: ID = strawberry.field(description="…")` without a resolver would build but fail at query time because Strawberry's default resolver looks up `display_id` as an attribute on the returned model instance); (2) inherited `id` annotations on a Relay-Node-shaped subclass slip past the guard at class-creation time, and `_build_annotations`'s pk-suppression branch silently handles them — Strawberry sees no `id` annotation on the child, applies the Relay-supplied `id: GlobalID!`, and `resolve_id_attr()` falls back to `"pk"`, so schema construction succeeds. Annotation `id: relay.NodeID[...]` is accepted in direct, PEP 563 / stringified, and mixed (resolved-`id`-alongside-unresolved-sibling) forms; non-`id` overrides are accepted unchanged. Drop the "planned for `0.0.6`" framing.
    - [`Scalar field conversion`][glossary-scalar-field-conversion] — the "Subclass MRO walk" paragraph and surrounding text frame unsupported scalar fields as `ConfigurationError` cases with `Meta.exclude` as the consumer recourse. Update to add annotation-only override as a parallel recourse: "or supply a consumer annotation override (see [Scalar field override semantics](#scalar-field-override-semantics))". Parallel update to any sibling sentences that mention grouped-choices rejection or `ArrayField` shape rejection — those continue to raise for the non-override path, but the override path is now also a recourse. Read the whole entry during planning to find all affected sentences.
    - [`Definition-order independence`][glossary-definition-order-independence] → remove the "Manual scalar-field override semantics remain an implementation detail until [Scalar field override semantics](#scalar-field-override-semantics) ships." closing sentence; the contract is now part of the foundation.
    - [`DjangoType`][glossary-djangotype] — review the "Current alpha constraints" bullet list and remove any scalar-override-related entry. Today the list only has the relation-cardinality-validation deferral; verify nothing scalar-shaped is in there to drop.
    - [Index][glossary-index] → flip the status badge on `Scalar field override semantics` to `shipped (0.0.6)`.
  - [ ] `docs/TREE.md` — no further changes needed. The source-tree section's `types/base.py` and `types/definition.py` per-file annotations do not need updating: the new `consumer_annotated_scalar_fields` field on `DjangoTypeDefinition` is part of the same internal-metadata shape, and the existing `DjangoTypeDefinition` annotation already reads "canonical per-type metadata with [`Meta.primary`][glossary-metaprimary] flag and forward-reserved Layer-3 slots". The test-tree section's `tests/types/test_definition_order.py` description was broadened pre-Slice-1 from "definition-order-independent relation finalization" to "consumer override contract (four-corner matrix) + definition-order-independent relation finalization" to reflect the file's role as the override-contract host; verify via `grep` that no stale "definition-order-independent relation finalization" string remains as a sole description.
  - [ ] `TODAY.md` — add scalar override semantics to the "shipped today" section. The fakeshop example does not exercise scalar annotation overrides; mention under "available but not currently demonstrated in fakeshop" if that subsection exists.
  - [ ] `KANBAN.md` — the card lands in the Done section as `DONE-019-0.0.6`, and no in-flight entry for it remains. **Drop in the verbatim body below:**

    ```markdown
    ### DONE-019-0.0.6 — Consumer override semantics (scalar fields)

    Slice-by-slice scope (per `docs/SPECS/spec-019-consumer_overrides_scalar-0_0_6.md`):

    - `DjangoType.__init_subclass__` collected `consumer_annotated_scalar_fields`
      parallel to `consumer_annotated_relation_fields`. Annotation-only scalar
      overrides (e.g., `description: int` shadowing an auto-synthesized `str`)
      are added to the unified `consumer_authored_fields` frozenset and skip
      auto-synthesis in `_build_annotations`'s scalar branch via the existing
      `if field.name in consumer_authored_fields: continue` short-circuit.
    - `DjangoTypeDefinition` gained `consumer_annotated_scalar_fields: frozenset[str]`.
      The four `consumer_*_fields` sets are the introspection surface; the
      unified `consumer_authored_fields` is the single short-circuit input.
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
      for the field-level GraphQL metadata use case — the ban on
      `id = <StrawberryField>` on Relay-Node-shaped types eliminated the
      only path for attaching `description`/`deprecation_reason`/
      `directives` to the Relay-supplied `id` field, and the workaround
      must be resolver-backed: the metadata-only
      `display_id: ID = strawberry.field(description="…")` shape would
      build but fail at query time because Strawberry's default resolver
      looks up `display_id` as an attribute on the returned Django model
      instance). Without the guard the consumer would have seen a
      Strawberry-side `ValueError` only at `strawberry.Schema(...)`
      construction, which obscured the source.
      The guard is narrow: it fires only when the consumer authored an
      `id` entry on a Relay-Node-shaped type AND the annotation is not a
      `relay.NodeID[...]`-marked annotation. Detection reads
      `cls.__annotations__["id"]` directly and dispatches on the value's
      shape — a string is matched against the token-shaped regex
      `(?:^|\.)NodeID\[`, so `"relay.NodeID[int]"` and `"NodeID[int]"`
      pass while prefixed-substring lookalikes like `"NotNodeID[int]"`
      are rejected; a resolved object is checked for the
      `Annotated[T, NodeIDPrivate]` marker. No other annotation on the
      class is consulted, so a forward-referenced sibling annotation
      cannot affect the verdict. Accepting a NodeID-shaped string is
      package-level guard suppression only; Strawberry's downstream
      schema construction resolves the string itself and may still error
      if the consumer's module globals do not expose `relay`.
      `id: relay.NodeID[int]` and `id: "relay.NodeID[int]"` (the
      documented escape hatch in direct and stringified forms, with
      `relay` importable at module scope) are accepted end-to-end; non-
      `id` consumer scalar overrides (e.g., `description: int`, or `code:
      str` on a model with `code` as pk) pass through unchanged;
      **inherited `id` annotations on a subclass slip past the guard at
      class-creation time and are silently handled by `_build_annotations`'s
      pk-suppression branch** (the guard does not walk the MRO, but
      pk-suppression strips the synthesized `id` annotation for any
      Relay-Node-shaped type and the post-merge reassignment leaves the
      child without an `id` key; Strawberry applies the Relay-supplied
      `id: GlobalID!` and `resolve_id_attr()` falls back to `"pk"` —
      schema construction succeeds).
    - No new public API. No `Meta.field_overrides = {...}`-style key. Opt-out
      / removal continues to go through `Meta.exclude`. Field description /
      deprecation / default continues to go through the assigned
      `strawberry.field(...)` path that shipped in `0.0.5`. Field-level
      GraphQL metadata on the Relay-supplied `id` field is **not**
      configurable in `0.0.6`; the documented workaround is the
      resolver-backed sibling field named above.
    - Type-annotation overrides are the consumer's responsibility for runtime
      correctness. `description: int` against a `CharField` will surface a
      Strawberry-side serialization error at query time if the database returns
      a non-integer value; the package does not pre-check annotation/field-type
      compatibility (out of scope for this card).
    - 100% coverage was reached across `tests/types/test_definition_order.py`
      (the override-contract host, where the core + Relay-collision +
      cross-type-cache tests live) and `tests/types/test_converters.py`
      (the converter test host, where the nested-`ArrayField` bypass test
      lives).
    ```

  - [ ] `CHANGELOG.md` — five entries (**permission granted by this spec**, overriding [`AGENTS.md`][agents]'s default prohibition). They land under `[Unreleased]` while `0.0.6` is unreleased and move with the release cut; at `HEAD` they sit under `## [0.0.6] - 2026-05-19`:
    - `Added`: Annotation-only scalar field overrides on `DjangoType`. Writing `description: int` (or any other class-level scalar annotation that shadows a Django scalar column selected via [`Meta.fields`][glossary-metafields]) is now a stable public contract — the consumer's annotation wins over the auto-synthesized one and survives `finalize_django_types()` / `strawberry.type(...)` decoration. Mirrors the annotation-only relation-override path that has shipped since `0.0.4`.
    - `Added`: `DjangoTypeDefinition.consumer_annotated_scalar_fields: frozenset[str]` — introspection surface for the new override path; symmetric with the existing `consumer_annotated_relation_fields`, `consumer_assigned_relation_fields`, and `consumer_assigned_scalar_fields` sets.
    - `Changed`: Annotation-only and assigned scalar field overrides bypass `convert_scalar` validations and side effects for the overridden field — unsupported-field-type rejection, grouped-choices rejection, `ArrayField` shape rejection, `null=True` widening, and choice-enum registration are skipped. The consumer's annotation is authoritative. `Meta.exclude` and annotation override are now parallel consumer recourses for unsupported scalar fields.
    - `Added`: `ConfigurationError` raised at `DjangoType.__init_subclass__` time when a consumer authors an `id` annotation on a `Meta.interfaces = (relay.Node,)`-shaped type that is not a `relay.NodeID[...]`-marked annotation. Points at `strawberry.relay.NodeID[<pk_type>]` as the supported escape hatch. Replaces the downstream Strawberry-side `ValueError` ("Interface field Node.id expects type ID! but ...") that surfaced only at `strawberry.Schema(...)` construction. Narrow guard: `id: relay.NodeID[int]` is accepted in direct, stringified / PEP 563 / `from __future__ import annotations`, and mixed (resolved `id` alongside other unresolved annotations on the same class) forms; non-`id` consumer scalar overrides on Relay-Node-shaped types (including custom-named primary keys like `code: str` on `models.CharField(primary_key=True)`) are accepted; inherited `id` annotations on a Relay-Node-shaped subclass also pass through at class-creation time (the guard does not walk the MRO) and are silently handled by `_build_annotations`'s pk-suppression branch — Strawberry applies the Relay-supplied `id: GlobalID!` and `resolve_id_attr()` falls back to `"pk"`, so schema construction succeeds. Detection reads `cls.__annotations__["id"]` directly: a string annotation is accepted when it matches the token-shaped regex `(?:^|\.)NodeID\[` (so prefixed-substring lookalikes like `"NotNodeID[int]"` are rejected), and a resolved annotation is accepted when it carries the `Annotated[T, NodeIDPrivate]` marker. Accepting a NodeID-shaped string is package-level guard suppression only — Strawberry's downstream resolution against `cls`'s module globals still applies.
    - `Changed`: `id = <StrawberryField>` assignment on a `Meta.interfaces = (relay.Node,)`-shaped `DjangoType` now raises `ConfigurationError` at `__init_subclass__` time. Previously consumers could write `@strawberry.field def id(self) -> relay.GlobalID: ...` (or `id = strawberry.field(description="…")`) and the resulting schema would build because the assigned-field type matched `Node.id: ID!`; this card uniformly rejects assigned `id` overrides on Relay-Node-shaped types for consistency with the annotation-side guard. The supported alternatives are `@classmethod resolve_id` (custom id resolver), `id: relay.NodeID[<pk_type>]` (custom id annotation), and a **resolver-backed sibling field** for the field-level GraphQL metadata use case (declare a separate field with a resolver — e.g. `@strawberry.field(description="…") def display_id(self) -> strawberry.ID: return str(self.pk)` — carrying the metadata AND a value source; the Relay-supplied `id` stays undecorated). Field-level metadata on the Relay-supplied `id` field is not configurable in `0.0.6`; the resolver-backed sibling field is the documented alternative. **Note**: a metadata-only sibling like `display_id: ID = strawberry.field(description="…")` without a resolver would build but fail at query time because Strawberry's default resolver looks up `display_id` as an attribute on the returned Django model instance and does not find it.
  - [ ] **Archive.** The spec is archived at `docs/SPECS/spec-019-consumer_overrides_scalar-0_0_6.md`, its terms CSV and rationale companion at `docs/SPECS/appx/`, and its `<!-- LINK DEFINITIONS -->` block is re-relativized for that depth. The move was performed by a later spec author's `docs/SPECS/NEXT.md` Step 8 sweep, not by this card; the [Definition of done](#definition-of-done) does not gate on it.

## Problem statement

[`docs/GLOSSARY.md`][glossary]'s [`Definition-order independence`][glossary-definition-order-independence] entry closed with the sentence *"Manual scalar-field override semantics remain an implementation detail until [Scalar field override semantics](#scalar-field-override-semantics) ships."* The `DONE-010-0.0.4` foundation slice pinned the override contract for **relation fields only** — both the annotation-only path (`items: list["AdminItemType"]`) and the assigned-`strawberry.field` path are part of the stable surface and are exercised by the three tests at `tests/types/test_definition_order.py::test_annotation_only_relation_override_keeps_generated_resolver`, `tests/types/test_definition_order.py::test_assigned_relation_field_override_keeps_consumer_resolver`, and `tests/types/test_definition_order.py::test_decorator_relation_field_override_routes_schema_query_through_consumer_resolver`.

For scalar fields, the picture is asymmetric. The assigned-`strawberry.field` path landed during the `0.0.5` foundation extension (`tests/types/test_definition_order.py::test_assigned_scalar_field_override_keeps_consumer_resolver` — its docstring credits the fix that widened `_consumer_assigned_fields` to walk every selected Django field rather than only relations). The **annotation-only path** for scalars never got the same treatment: writing `description: int` on a `DjangoType` whose `CharField` `description` column is selected via [`Meta.fields`][glossary-metafields] lands the consumer's annotation in `cls.__annotations__` at `__init_subclass__` time (the merge at `django_strawberry_framework/types/base.py::DjangoType.__init_subclass__ #"cls.__annotations__ = {**synthesized, **consumer_annotations}"` puts `consumer_annotations` last so consumer wins), but the `consumer_authored_fields` set does NOT contain the name, so the synthesized scalar annotation is also computed and written into the same dict. The consumer's `int` lands over the synthesized `str` only because dict-merge order favors the consumer — the path is brittle and not a stable contract.

The skipped `tests/types/test_base.py::test_consumer_annotation_overrides_synthesized` (deleted in Slice 2) was the original placeholder for this contract. Its skip reason stated *"Strawberry's @strawberry.type decorator regenerates cls.__annotations__ from its own field metadata after our merge in DjangoType.__init_subclass__, so the consumer's class-level scalar annotation loses to the synthesized one."* Under the pre-card code the merge order already put the consumer's annotation last — the skip reason described a pre-foundation-slice state. The test would likely have passed for the simple pre-finalize case, but the contract was not part of the documented public surface, and the symmetric four-corner override matrix was incomplete.

This card closes the asymmetry by extending the existing `consumer_annotated_relation_fields` collection to a parallel `consumer_annotated_scalar_fields` set, unioning it into `consumer_authored_fields`, and landing the test as the stable proof.

## Current state

This section describes the **pre-card baseline** the Decisions are read against.

`DjangoType.__init_subclass__` (`django_strawberry_framework/types/base.py::DjangoType.__init_subclass__`) built the override-routing state as follows:

```python
# django_strawberry_framework/types/base.py::DjangoType.__init_subclass__ (pre-Slice-1)
consumer_annotations = dict(getattr(cls, "__annotations__", {}))
consumer_annotated_relation_fields = frozenset(
    field.name for field in fields if field.is_relation and field.name in consumer_annotations
)
consumer_assigned_relation_fields, consumer_assigned_scalar_fields = _consumer_assigned_fields(
    cls,
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

Note the asymmetry: `consumer_annotated_relation_fields` filters on `field.is_relation`, but there is no parallel `consumer_annotated_scalar_fields`. The unified `consumer_authored_fields` therefore covered three of the four override corners but not the fourth (scalar annotation only).

`_build_annotations` (`django_strawberry_framework/types/base.py::_build_annotations`) already had the right short-circuit shape — both branches check `if field.name in consumer_authored_fields: continue` (`django_strawberry_framework/types/base.py::_build_annotations #"if field.name in consumer_authored_fields:"` — relation branch and scalar branch). Once the fourth corner lands in `consumer_authored_fields`, the scalar branch skips synthesis for annotation-only-overridden scalars without further code change.

`DjangoTypeDefinition` (`django_strawberry_framework/types/definition.py::DjangoTypeDefinition`) carried the three existing introspection sets:

```python
# django_strawberry_framework/types/definition.py::DjangoTypeDefinition (pre-Slice-1)
consumer_authored_fields: frozenset[str] = frozenset()
consumer_annotated_relation_fields: frozenset[str] = frozenset()
consumer_assigned_relation_fields: frozenset[str] = frozenset()
consumer_assigned_scalar_fields: frozenset[str] = frozenset()
```

The `consumer_annotated_scalar_fields: frozenset[str] = frozenset()` field is the symmetric fourth corner.

`tests/types/test_definition_order.py` (the four-corner override test cluster) carried the matrix as of `0.0.5`:

| Field shape | Override style | Test |
|---|---|---|
| Relation | Annotation-only | `tests/types/test_definition_order.py::test_annotation_only_relation_override_keeps_generated_resolver` |
| Relation | Assigned `strawberry.field` | `tests/types/test_definition_order.py::test_assigned_relation_field_override_keeps_consumer_resolver` + decorator variant `tests/types/test_definition_order.py::test_decorator_relation_field_override_routes_schema_query_through_consumer_resolver` |
| Scalar | Assigned `strawberry.field` | `tests/types/test_definition_order.py::test_assigned_scalar_field_override_keeps_consumer_resolver` |
| Scalar | Annotation-only | **missing** — formerly the skipped `tests/types/test_base.py::test_consumer_annotation_overrides_synthesized` (deleted in Slice 2) |

This card lands the bottom-right cell.

## Goals

- Add `consumer_annotated_scalar_fields` collection in `DjangoType.__init_subclass__`, parallel to the existing `consumer_annotated_relation_fields` collection.
- Add `consumer_annotated_scalar_fields: frozenset[str] = frozenset()` field to `DjangoTypeDefinition`.
- Union the new set into `consumer_authored_fields` so the existing scalar-branch short-circuit in `_build_annotations` fires for the new override path.
- Pin the **converter-validation-bypass contract** for overridden scalar fields ([Decision 7a](#decision-7a--converter-validation-bypass)): consumer annotation overrides are authoritative, so `convert_scalar`'s unsupported-field-type rejection, grouped-choices rejection, `ArrayField` shape rejection, `null=True` widening, and choice-enum registration are all bypassed for an overridden field. Annotation override becomes a parallel recourse to [`Meta.exclude`][glossary-metaexclude] for unsupported scalar fields.
- Add the **Relay `id` collision guard** ([Decision 7](#decision-7--relay-id-override-collision)): raise [`ConfigurationError`][glossary-configurationerror] from `__init_subclass__` when the consumer authors an `id` entry (annotation or assigned `StrawberryField`) on a Relay-Node-shaped type, unless the annotation is a `relay.NodeID[...]` marker. Detection reads `cls.__annotations__["id"]` directly and dispatches on the value's shape — a token-shaped regex (`(?:^|\.)NodeID\[`) for the string form, the `Annotated[T, NodeIDPrivate]` marker for the resolved form. Replaces the downstream Strawberry-side `ValueError` at `strawberry.Schema(...)` construction.
- Retire the skipped `test_consumer_annotation_overrides_synthesized`; the Slice 1 test cluster on `tests/types/test_definition_order.py` covers the contract more thoroughly.
- Document the four-corner override contract, the converter-bypass contract, and the Relay collision guard in [`docs/GLOSSARY.md`][glossary]'s [`Scalar field override semantics`][glossary-scalar-field-override-semantics] entry, flipping its status to `shipped (0.0.6)`.
- 100% coverage on the new collection path, the new definition field, the Relay guard (including both arms of the `_id_annotation_is_relay_node_id` dispatch), the converter bypass, and the cross-type enum-cache behavior change. The 19-test Slice 1 cluster (4 core + 4 converter-bypass + 11 Relay) is the contract surface.

## Non-goals

- **No new `Meta.field_overrides = {...}` API.** The card's KANBAN entry lists `Meta.field_overrides` as a *design choice*, but the symmetric annotation-only + assigned-`strawberry.field` path is sufficient to close the contract gap. A future card may add a declarative override key if the assigned / annotation routes prove insufficient for some real consumer use case; that lives outside `0.0.6`.
- **No annotation/field-type compatibility pre-check.** Writing `description: int` against a `CharField` is the consumer's responsibility; the package does not assert that the consumer's annotation is type-compatible with the Django column. Runtime serialization errors at query time are the consumer-visible failure mode and are intentional — the package treats consumer overrides as authoritative.
- **No new opt-out / removal API.** The [`Meta.exclude`][glossary-metaexclude] path that shipped in `0.0.1` already covers "drop the field entirely". This card does not add a sentinel-value or `Skip`-typed annotation shape (e.g. `description: None` or `description: strawberry.SKIP`) — the design space is not justified by any pending consumer use case.
- **No new field metadata API.** Description / deprecation / default routing already work via the assigned `strawberry.field(...)` path (`description = strawberry.field(description="...", deprecation_reason="...")` is preserved by `_consumer_assigned_fields`'s scalar branch). This card adds no parallel route through annotation-only syntax.
- **No change to relation overrides.** All cells of the relation × {annotation, assigned} matrix shipped in `0.0.4` / `0.0.5` and stay unchanged.
- **No change to the post-merge annotation order at `django_strawberry_framework/types/base.py::DjangoType.__init_subclass__ #"cls.__annotations__ = {**synthesized, **consumer_annotations}"`.** The line continues to put consumer last; the only difference is that under this card the synthesized dict no longer contains entries for annotation-only-overridden scalars, so the merge degenerates to "consumer annotation only" for those keys.

## Architectural decisions

Each Decision below states the contract. The alternatives each one rejected, and why, live in [the rationale companion][spec-019-rationale].

### Decision 1 — Annotation-only scalar override collection

Symmetric to the existing relation collection. Two comprehensions rather than one, keeping the code shape symmetric with the relation collection one line above:

```python
# django_strawberry_framework/types/base.py::DjangoType.__init_subclass__ (post-Slice-1)
consumer_annotations = dict(getattr(cls, "__annotations__", {}))
consumer_annotated_relation_fields = frozenset(
    field.name
    for field in fields
    if field.is_relation
    and field.name in consumer_annotations
    and field.name not in auto_annotated_fields
)
consumer_annotated_scalar_fields = frozenset(
    field.name
    for field in fields
    if not field.is_relation
    and field.name in consumer_annotations
    and field.name not in auto_annotated_fields
)
```

Both filters walk the same `fields` tuple and read the same `consumer_annotations` dict; the only difference is the `field.is_relation` polarity. The two sets are disjoint by construction.

The `field.name not in auto_annotated_fields` clause is a later addition, landed with the `auto`-typed-annotations card: an `auto`-typed annotation is a request for the model-inferred type, not a consumer override, so it must not enter `consumer_authored_fields`. This card's contract is unaffected by it. The polarity filter uses `not field.is_relation` rather than an explicit `is False` comparison, matching the bare `if field.is_relation:` bool-coercion the existing `_build_annotations` code uses.

### Decision 2 — `consumer_authored_fields` union shape

A single `consumer_authored_fields` frozenset is the short-circuit input to `_build_annotations`, built at `django_strawberry_framework/types/base.py::DjangoType.__init_subclass__ #"consumer_authored_fields = frozenset"`:

```python
# django_strawberry_framework/types/base.py::DjangoType.__init_subclass__ (post-Slice-1)
consumer_authored_fields = frozenset(
    {
        *consumer_annotated_relation_fields,
        *consumer_annotated_scalar_fields,   # new
        *consumer_assigned_relation_fields,
        *consumer_assigned_scalar_fields,
    },
)
```

Order inside the set literal does not matter (frozenset is unordered). The line ordering keeps relations and scalars adjacent — relations first, then scalars, within each (annotated, assigned) pair.

`_build_annotations` needs only the union: it does not distinguish between the four corners. The same union is read by three later validators as well — `_validate_nullability_override_targets`, `_validate_filesystem_path_targets`, and `_validate_relation_shape_targets` (added by `0.0.9` / `0.0.14` cards) — each of which needs exactly the same "did the consumer author this name" question answered. One union is the shape every consumer of it wants.

### Decision 3 — `DjangoTypeDefinition.consumer_annotated_scalar_fields` field

Symmetric to the three existing sibling fields. The `consumer_*_fields` block in `django_strawberry_framework/types/definition.py::DjangoTypeDefinition` uses the **grouped-by-style** order — annotations group first, assignments group second, with relation and scalar adjacent within each:

```python
# django_strawberry_framework/types/definition.py::DjangoTypeDefinition (post-Slice-1)
consumer_authored_fields: frozenset[str] = frozenset()
consumer_annotated_relation_fields: frozenset[str] = frozenset()
consumer_annotated_scalar_fields: frozenset[str] = frozenset()      # new
consumer_assigned_relation_fields: frozenset[str] = frozenset()
consumer_assigned_scalar_fields: frozenset[str] = frozenset()
```

The cosmetic re-order of the existing two `consumer_assigned_*` lines lands in the same commit as the new field so the dataclass field order is internally consistent.

The field is read by tests for introspection (per the Slice 1 test cluster). No production code path consumes it directly — production routes through the unified `consumer_authored_fields`. The four-corner sets exist as the introspection surface and as a tested contract that the package will not silently change the bucketing.

### Decision 4 — `_build_annotations` body stays unchanged

The scalar branch in `django_strawberry_framework/types/base.py::_build_annotations` already does the right thing:

```python
# django_strawberry_framework/types/base.py::_build_annotations (scalar branch — unchanged)
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

The existing inline comment already mentions "annotation" in parallel with "assigned `StrawberryField`" — its *intent* covers the annotation-only path. What was missing is the upstream collection that adds annotation-only scalars to `consumer_authored_fields`. Slice 1 closes that gap with no body edit in `_build_annotations`.

### Decision 5 — Test placement and the skipped test's fate

The four-corner override matrix lives in `tests/types/test_definition_order.py` (the foundation-slice override-contract host) — three of the four cells are already there as `tests/types/test_definition_order.py::test_annotation_only_relation_override_keeps_generated_resolver`, `tests/types/test_definition_order.py::test_assigned_relation_field_override_keeps_consumer_resolver`, `tests/types/test_definition_order.py::test_decorator_relation_field_override_routes_schema_query_through_consumer_resolver`, and `tests/types/test_definition_order.py::test_assigned_scalar_field_override_keeps_consumer_resolver`. The fourth cell (annotation-only scalar) is the natural sibling and lands as a new test in the same file. **The override matrix lives in one file** — that is the rule a future override test follows too, rather than landing beside whatever converter it happens to exercise.

The previously-skipped `tests/types/test_base.py::test_consumer_annotation_overrides_synthesized` is thereby redundant and is deleted in Slice 2.

### Decision 6 — Why `_consumer_assigned_fields` stays the way it is

`_consumer_assigned_fields` (`django_strawberry_framework/types/base.py::_consumer_assigned_fields`) takes the class and walks `cls.__dict__`, bucketing assigned `StrawberryField` instances into a (relation, scalar) tuple. The function does NOT walk `consumer_annotations` — that is the parallel job of the annotation-collection lines in `django_strawberry_framework/types/base.py::DjangoType.__init_subclass__`. Symmetric responsibility split:

- `_consumer_assigned_fields` reads `cls.__dict__` → produces `(consumer_assigned_relation_fields, consumer_assigned_scalar_fields)`.
- The annotation-collection lines read `cls.__annotations__` → produce `(consumer_annotated_relation_fields, consumer_annotated_scalar_fields)`.

The two sources are independent: a consumer can write `description: int` annotation-only, OR `description = strawberry.field(...)` assigned, OR both — the four-corner matrix treats them as separate input channels. `_consumer_assigned_fields` stays unchanged by this card; the new collection is the annotation-side parallel.

### Decision 7 — Relay `id` override collision

`_build_annotations` processes each selected field in two ordered checks: first the consumer-authored short-circuit (`if field.name in consumer_authored_fields: continue`), then the `relay.Node` pk-suppression branch (`if suppress_pk_annotation and field.name == pk_name: continue`). The ordering matters: a consumer who writes an `id: int` annotation on a Relay-Node-shaped type lands `"id"` in `cls.__annotations__`, the consumer-authored short-circuit fires in the scalar branch, and the loop continues. The pk-suppression branch never executes for that field name. The merge at `django_strawberry_framework/types/base.py::DjangoType.__init_subclass__ #"cls.__annotations__ = {**synthesized, **consumer_annotations}"` then writes the consumer's `id: int` annotation onto `cls.__annotations__`.

The downstream behavior is broken in a way that surfaces far from the source: `finalize_django_types()` runs to completion (the `_build_annotations` skip is cooperative with the consumer override); `strawberry.Schema(query=Query, types=[ThatType])` then fails inside Strawberry's schema-validation pass with a `ValueError` because `Node.id` is `ID!` (the interface contract) while the concrete type's `id` is `Int!`. The error originates from Strawberry's interface-compliance check, not from any `DjangoType` code path — the user's traceback points at `strawberry/schema/schema.py` rather than at `types/base.py`, and the message ("Interface field Node.id expects type ID! but ImplementingType.id is of type Int!") leaves the consumer to reverse-engineer the connection back to their `DjangoType` declaration.

**Contract.** This card adds a package-owned [`ConfigurationError`][glossary-configurationerror] raised at `DjangoType.__init_subclass__` time when **and only when** the consumer authored an `"id"` entry on a Relay-Node-shaped type, AND the entry is not a `relay.NodeID[...]`-marked annotation. Assigned `id` overrides (any `StrawberryField`) are always rejected — the supported alternatives are the `@classmethod resolve_id` hook from Strawberry's Relay Node interface (custom id resolver) and `id: relay.NodeID[<pk_type>]` (custom id annotation). Consumers who previously wrote `id = strawberry.field(description="…")` purely to attach GraphQL field-level metadata to the Relay-supplied `id` lose that route; the workaround is a **resolver-backed sibling field** (e.g. `@strawberry.field(description="…") def display_id(self) -> strawberry.ID: return str(self.pk)`) that carries the metadata AND defines a value source. A metadata-only sibling (`display_id: ID = strawberry.field(description="…")`) without a resolver would build but fail at query time, because Strawberry's default resolver looks up `display_id` as an attribute on the returned Django model instance and does not find it. The Relay-supplied `id` stays undecorated; field-level metadata on it is not configurable in `0.0.6`.

**The predicate is keyed off the GraphQL field name `"id"`, not the model's pk name.** This is a prohibition on the obvious-looking implementation, and it has two independent reasons:

1. A pk-keyed predicate rejects `id: relay.NodeID[int]` — the advertised escape hatch. `id` is a model pk field, so a `NodeID[int]` annotation lands in `consumer_annotated_scalar_fields` through the same collection path, and the guard would fire against the exact pattern its own error message recommends.
2. A pk-keyed predicate rejects non-`id` primary-key overrides. On a model with `code = models.CharField(primary_key=True)`, a consumer `code: str` override produces `id: ID!` (from Relay) and `code: String!` (from the consumer) — no `Node.id` collision at all. The existing `tests/types/test_relay_interfaces.py::test_composite_pk_with_explicit_node_id_annotation_is_accepted` (which uses `name: relay.NodeID[str]`) confirms the framework's broader contract that `relay.NodeID` annotations land on any attribute, not just `"id"`.

**The guard lives in `__init_subclass__`, between collection and `_build_annotations`.** That is the only point in the lifecycle where `cls.__annotations__`, `cls.__dict__`, the collected `consumer_*_scalar_fields`, and the validated `interfaces` tuple are all in hand *and* the error can still fire at class-definition time — which the reject tests and the CHANGELOG both assert. A check placed in `_build_annotations` fires too late and entangles configuration validation with annotation synthesis inside a per-field loop.

```python
# In DjangoType.__init_subclass__, after consumer_*_scalar_fields collection
# and BEFORE _build_annotations runs (so the error fires at type-creation time).
relay_shaped = _is_relay_shaped(cls, validated.interfaces)
if relay_shaped:
    has_id_assignment = isinstance(cls.__dict__.get("id"), StrawberryField)
    # Key-presence rather than value-truthiness, so unusual annotations like
    # ``id: None`` (which Python evaluates to ``<class 'NoneType'>``, not to
    # the literal ``None``), ``id: Literal[None]``, and string forms that
    # evaluate to false-y types are all detected.
    has_id_annotation = "id" in cls.__annotations__
    if has_id_assignment:
        raise ConfigurationError(
            f"{cls.__name__}: cannot override the id field on a "
            "relay.Node-shaped type with an assigned strawberry.field. "
            "Use @classmethod resolve_id for a custom id resolver, "
            "id: relay.NodeID[<pk_type>] for a custom id annotation, "
            "or declare a resolver-backed sibling field - e.g., "
            "`@strawberry.field(description=...) def display_id(self) -> "
            "strawberry.ID: return str(self.pk)` - if you only need "
            "GraphQL field-level metadata on a custom identifier "
            "(a metadata-only sibling without a resolver builds but "
            "fails at query time); "
            "or remove relay.Node from Meta.interfaces.",
        )
    if has_id_annotation and not _id_annotation_is_relay_node_id(cls):
        raise ConfigurationError(
            f"{cls.__name__}: cannot override the id field on a "
            "relay.Node-shaped type without using strawberry.relay.NodeID[...]. "
            "The Relay interface supplies id: GlobalID! - declare the id "
            "field via relay.NodeID[<pk_type>] if you need a different id "
            "shape, or remove relay.Node from Meta.interfaces.",
        )


# Module-scope helpers, defined above ``DjangoType``. Imports needed at the top
# of types/base.py: ``re``, ``typing``, ``typing.Annotated``, and
# ``NodeIDPrivate`` from ``strawberry.relay.types``.

# The ``(?:^|\.)`` anchor accepts both the unqualified ``NodeID[int]`` and the
# dot-qualified ``relay.NodeID[int]`` / ``strawberry.relay.NodeID[int]`` forms
# while rejecting prefixed-substring lookalikes (``NotNodeID[int]``,
# ``MyNodeID[int]``). Module-scope, so it compiles once per process.
_NODEID_STRING_RE = re.compile(r"(?:^|\.)NodeID\[")


def _has_node_id_marker(hint: object) -> bool:
    """Return True when ``hint`` is ``Annotated[T, NodeIDPrivate()]``.

    In the installed Strawberry, ``relay.NodeID[T]`` IS
    ``typing.Annotated[T, NodeIDPrivate()]`` - the explicit ``Annotated``
    form and the ``relay.NodeID`` sugar collapse to the same shape, so
    ``typing.get_origin`` returns ``typing.Annotated`` for both and the
    ``NodeIDPrivate`` instance lives in ``typing.get_args(...)``'s
    metadata slot. There is no separate "direct ``relay.NodeID[T]``"
    branch to detect.
    """
    return typing.get_origin(hint) is Annotated and any(
        isinstance(arg, NodeIDPrivate) for arg in typing.get_args(hint)
    )


def _id_annotation_is_relay_node_id(cls: type) -> bool:
    """Return True when ``cls.__annotations__['id']`` is ``relay.NodeID[...]``.

    Reads ``cls.__annotations__`` directly - no ``typing.get_type_hints``
    call. Two consequences, both load-bearing. First, the result does not
    depend on whether any OTHER annotation on the class resolves: an
    unrelated forward reference on a sibling attribute cannot mask the
    ``id`` annotation, so no recovery path is needed for that case.
    Second, the function behaves identically on every supported Python
    version - ``typing.get_type_hints`` handles nested forward references
    differently across 3.10 vs 3.11+, which leaves a branch reachable
    only on the newer interpreter.

    Two annotation forms are accepted:

    1. **String form** (``id: "relay.NodeID[int]"`` or ``id: "NodeID[int]"``,
       typical under ``from __future__ import annotations`` or any
       explicit string annotation). Matched against ``_NODEID_STRING_RE``.
       Downstream Strawberry schema construction is responsible for
       resolving the string to a real ``NodeID[T]`` annotation; this
       function only confirms the shape so the collision guard can accept
       the escape hatch at class-creation time.
    2. **Resolved-object form** (``id: relay.NodeID[int]``, evaluated at
       class-creation time). Delegated to ``_has_node_id_marker``.

    Precondition: ``"id" in cls.__annotations__``. The only call site
    already gates on ``has_id_annotation``, so the subscript cannot
    ``KeyError`` from real flow; a future caller that violates the
    precondition gets a loud ``KeyError`` rather than a misleading
    ``False``.
    """
    raw = cls.__annotations__["id"]
    if isinstance(raw, str):
        return bool(_NODEID_STRING_RE.search(raw))
    return _has_node_id_marker(raw)


def _is_relay_shaped(cls: type, interfaces: tuple[type, ...]) -> bool:
    """Return True when ``cls`` or any entry in ``interfaces`` is Relay-Node-shaped.

    Single source of truth for the predicate that drives both the Relay
    ``id`` collision guard above and the synthesized-``id``-annotation
    suppression branch in ``_build_annotations``. Both call sites compute
    the same boolean from the same inputs at different timings
    (class-creation-time vs. annotation-synthesis-time); centralizing it
    keeps the Relay-shape contract single-sited. Both halves of the
    disjunction are required: ``Meta.interfaces = (relay.Node,)`` and a
    direct ``class X(DjangoType, relay.Node)`` declaration are both
    Relay-shaped.
    """
    return any(issubclass(i, relay.Node) for i in interfaces) or issubclass(cls, relay.Node)
```

**Accepting a NodeID-shaped string is package-level guard suppression only.** Strawberry's downstream schema-construction pass resolves the same string annotation against `cls`'s module globals using its own evaluation path; if the consumer's string is not resolvable in that scope, Strawberry's error will still fire later. The package's `ConfigurationError` is suppressed at class-creation time, not the entire end-to-end failure. A test that wants to pin **end-to-end** schema success must ensure `relay` (or whichever module supplies `NodeID`) is importable at the test class's module scope; a test that wants to pin **guard-only** suppression must assert class-creation acceptance only, not finalize / schema build. See the split tests under "Eleven Relay-collision tests" for the contract distinction.

**Why this is in scope for this card.** The card's headline contract is "consumer annotation override for scalars". Without the guard, the new annotation-only override path silently breaks `relay.Node`-shaped types in a way that points the consumer at the wrong code surface. The guard is the smallest correct UX surface for the new override behavior and fits inside the same `__init_subclass__` pass the collection itself lives in.

### Decision 7a — Converter validation bypass

Adding annotation-only scalar names to `consumer_authored_fields` skips the entire scalar branch of `django_strawberry_framework/types/base.py::_build_annotations` before `convert_scalar(...)` is called. `convert_scalar` (`django_strawberry_framework/types/converters.py::convert_scalar`) carries several validation and side-effect responsibilities beyond annotation synthesis:

1. **Unsupported field-type rejection.** Walks `type(field).__mro__` looking for a `SCALAR_MAP` match; raises `ConfigurationError` if nothing matches. The error message names [`Meta.exclude`][glossary-metaexclude] as the consumer recourse.
2. **Grouped-choices rejection.** `convert_choices_to_enum` raises `ConfigurationError("Meta.fields contains grouped-choices field ...")` when the Django field's `choices=` is the grouped `[(label, [(value, label), ...])]` shape.
3. **`ArrayField` shape validation.** Rejects nested `ArrayField` (recursive `base_field` walk hits a second `ArrayField`) and outer `choices=` declarations with `ConfigurationError`.
4. **`HStoreField` routing.** Sentinel-guarded branch that returns `strawberry.scalars.JSON` only when `django.contrib.postgres.fields` imports successfully; rejects outer `choices=` with `ConfigurationError`.
5. **`null=True` widening.** `T | None` wrapping for nullable scalar columns.
6. **Choice-enum registration.** Successful `convert_choices_to_enum` calls register the generated enum into `registry._enums[(model, field_name)]` so two `DjangoType`s reading the same choice column share one cached enum (the existing [`Choice enum generation`][glossary-choice-enum-generation] contract from `0.0.1`).

Under the short-circuit, **every one of these validations and side effects is bypassed for an annotation-overridden field.** The contract for this card:

- Consumer annotation overrides are **authoritative**. The consumer takes responsibility for the runtime shape of the annotation; the package does not pre-validate that the override is compatible with the underlying Django column.
- Unsupported scalar fields can be annotation-overridden as a recourse parallel to `Meta.exclude`. Before this card, the only recourse for an unsupported scalar was to drop the field via `Meta.exclude`; after this card, a consumer can also write a custom annotation. This aligns with the existing relation path: annotation-only relation overrides bypass `convert_relation` and its pending-relation routing.
- Grouped-choices, nested-`ArrayField`, and outer-`choices`-on-postgres-fields rejections **do not fire** when the consumer overrides those columns. The consumer's annotation replaces the package's auto-conversion entirely.
- Choice-enum registration **does not fire** when the consumer overrides a `choices=`-bearing column. The shared `(model, field_name)` enum cache is not populated for that field. A second `DjangoType` on the same model that selects the same column without an override triggers fresh enum generation. This is a behavior change worth flagging — pre-spec, two `DjangoType`s with one overriding and one not would have shared the auto-generated enum from whichever loaded first; post-spec, the overriding type contributes nothing to the cache.
- `null=True` widening is the consumer's responsibility — a consumer who writes `description: int` against a nullable `IntegerField(null=True)` gets the literal `int` annotation, not `int | None`. The consumer is expected to write `description: int | None` themselves.

**What this means for [`docs/GLOSSARY.md`][glossary].** The [`Scalar field conversion`][glossary-scalar-field-conversion] entry framed unsupported scalars as `ConfigurationError` cases with `Meta.exclude` as the recourse. Under this card, annotation-only override is a parallel recourse; Slice 5 updates the entry to list both paths.

**Mandatory tests pinning the bypass.** The four Slice 1 tests under the "Converter-bypass regressions" sub-checklist: unsupported field type, grouped choices, nested `ArrayField`, and cross-type enum cache (`test_annotation_override_does_not_populate_shared_enum_cache_for_co_resident_types`). Additional regressions for `HStoreField` choices, outer `ArrayField` choices, and the null-widening path are optional; the four listed cover the contract surface.

## Implementation plan

The slice ordering is **strict** — each slice depends on the previous. The plan deliberately keeps Slice 1 a one-commit change (collection + definition field + tests) so the historical staleness in `test_base.py` is cleared in a discrete Slice 2 commit and the doc / KANBAN / CHANGELOG churn lives entirely in Slice 5.

| Slice | Files | Tests landed | Notes |
|---|---|---|---|
| 1 | `types/base.py`, `types/definition.py`, `tests/types/test_definition_order.py`, `tests/types/test_converters.py` (the placement for the nested-`ArrayField` bypass test) | 19 new tests: 4 core overrides + 4 converter-bypass + 11 Relay collision (5 reject + 6 accept) | Headline change. Includes the Relay guard implementation and the four module-scope helpers (`_NODEID_STRING_RE`, `_has_node_id_marker`, `_id_annotation_is_relay_node_id`, `_is_relay_shaped`). |
| 2 | `tests/types/test_base.py` | None new; the skipped test is deleted | Full delete of the skipped test block. |
| 3 | `types/base.py` | None | Documentation only — the `_consumer_assigned_fields` docstring. |
| 4 | Version-bump quintet | None | No-op gate; every site is already at `0.0.6` from a prior `0.0.6` card. |
| 5 | Docs / KANBAN / CHANGELOG | None | Largest cosmetic churn; closeout. Adds the `Scalar field conversion` annotation-override-as-recourse update and the metadata-route-loss acknowledgment in the `Scalar field override semantics` body and the `Changed` CHANGELOG entry. |

No new source files. No new test files.

## Edge cases and constraints

- **`Meta.fields = "__all__"` interaction.** When [`Meta.fields`][glossary-metafields] is unspecified or `"__all__"`, every concrete Django field is selected. A consumer annotation that shadows any one of them — relation or scalar — lands in `consumer_authored_fields` under this card. The interaction with [`Meta.exclude`][glossary-metaexclude] is unchanged: a name listed in `Meta.exclude` is filtered out of `fields` upstream of the collection, so the `field.name in consumer_annotations` check never sees it. (Verify by reading `django_strawberry_framework/types/base.py::_select_fields`.)
- **`relay.Node` `id` collision.** Pinned as a behavior contract, not a flagged edge case — see [Decision 7](#decision-7--relay-id-override-collision). A consumer who writes `id: <non-NodeID-type>`, a non-NodeID stringified annotation (e.g. `id: "MissingType"`), a NodeID-lookalike string (e.g. `id: "NotNodeID[int]"`, rejected by the token-shaped regex), or assigns any `id = <StrawberryField>` on a Relay-Node-shaped type raises [`ConfigurationError`][glossary-configurationerror] at `__init_subclass__` time. The annotation-side errors point at `relay.NodeID[...]` as the supported escape hatch; the assigned-side error points at three alternatives — `relay.NodeID[<pk_type>]`, `@classmethod resolve_id`, and the **resolver-backed sibling-field workaround** (`@strawberry.field(description="…") def display_id(self) -> strawberry.ID: return str(self.pk)`; the metadata-only `display_id: ID = strawberry.field(description="…")` form is NOT recommended because it would build but fail at query time). The guard is narrow: `id: relay.NodeID[int]` passes in direct form, in resolved-string end-to-end form, in unresolved-NodeID-shaped-string guard-only form, and alongside any number of unresolvable sibling annotations (detection reads only `cls.__annotations__["id"]`, so no other annotation can influence the verdict); non-`id` consumer scalar overrides on Relay-Node-shaped types pass (no `Node.id` collision); inherited `id` annotations on a subclass slip past the guard at class-creation time AND are silently handled by `_build_annotations`'s pk-suppression branch — Strawberry applies the Relay-supplied `id: GlobalID!` and `resolve_id_attr()` falls back to `"pk"`, so schema construction succeeds (the guard does not walk the MRO). The eleven Slice 1 Relay-collision tests pin the reject + accept + inheritance-handled paths: `test_consumer_id_annotation_on_relay_node_type_raises`, `test_consumer_id_annotation_on_direct_relay_node_subclass_raises`, `test_consumer_id_assigned_strawberry_field_on_relay_node_type_raises`, `test_consumer_id_unresolved_non_nodeid_string_on_relay_node_type_raises`, `test_consumer_id_typo_lookalike_nodeid_string_on_relay_node_type_raises`, `test_consumer_id_relay_nodeid_annotation_on_relay_node_type_is_accepted`, `test_consumer_id_resolved_string_relay_nodeid_annotation_on_relay_node_type_is_accepted_end_to_end`, `test_consumer_id_unresolved_nodeid_shaped_string_on_relay_node_type_passes_guard_only`, `test_consumer_id_resolved_relay_nodeid_with_unresolved_sibling_annotation_is_accepted`, `test_consumer_non_id_scalar_override_on_relay_node_type_is_accepted`, and `test_inherited_id_annotation_on_relay_node_subclass_is_handled_by_pk_suppression`.
- **Choice-enum fields.** Pinned as a behavior contract, not a flagged edge case — see [Decision 7a](#decision-7a--converter-validation-bypass). A consumer annotation `status: MyEnum` on a `choices=`-bearing column bypasses `convert_choices_to_enum` entirely; `registry.get_enum(model, field_name)` returns `None` for the overridden field. Two `DjangoType`s on the same model where one overrides and one does not get the fresh enum from the non-overriding type alone; pre-spec they would have shared whichever loaded first. `test_annotation_override_of_grouped_choices_field_is_allowed` pins the **single-type** bypass; `test_annotation_override_does_not_populate_shared_enum_cache_for_co_resident_types` pins the **cross-type** cache behavior — the non-overriding co-resident type populates the cache, the overriding type's GraphQL surface uses the consumer's annotation.
- **Inheritance.** Inherited consumer annotations on a base `DjangoType` subclass are NOT in the subclass's own `cls.__annotations__` (Python returns only the class's own annotations dict). A subclass that inherits from a base with `description: int` and adds `class Meta: model = Category` sees `cls.__annotations__ = {}` at `__init_subclass__` time and the collection misses the inherited override. This matches the existing relation-annotation behavior (which also walks `cls.__annotations__` and also misses inherited annotations) — no asymmetry to fix here. It is not a bug; it is the same "per-subclass declaration" contract as relations, and Slice 5 documents it in the [`Scalar field override semantics`][glossary-scalar-field-override-semantics] entry.
- **Mutable-default-argument hazard.** `consumer_authored_fields: frozenset[str] = frozenset()` is the default-argument shape in `_build_annotations`'s signature. `frozenset()` is immutable, so the default is safe. The new `consumer_annotated_scalar_fields: frozenset[str] = frozenset()` field on `DjangoTypeDefinition` uses the same pattern — `DjangoTypeDefinition` is a `@dataclass`, where mutable defaults must use `field(default_factory=...)`, but `frozenset()` is immutable so the bare default is allowed. The spec uses `frozenset()` literals throughout to match the existing siblings.
- **`finalize_django_types()` interaction.** Annotation-only overrides land in `cls.__annotations__` at `__init_subclass__` time (before finalize). [`finalize_django_types`][glossary-finalize-django-types]`()` does not re-read `cls.__annotations__` for the override-routing decision — it only resolves pending relations and decorates with `strawberry.type(...)`. The Strawberry decorator reads `cls.__annotations__` to build `__strawberry_definition__.fields`; under this card the consumer's annotation is what is in the dict, so the resulting Strawberry field type matches the consumer's override. This is the end-to-end contract that `test_annotation_only_scalar_override_survives_strawberry_finalization` pins.

## Test strategy

All new tests land in `tests/types/test_definition_order.py` — the existing host for the override-contract matrix (per [Decision 5](#decision-5--test-placement-and-the-skipped-tests-fate)). The single exception is `test_annotation_override_of_arrayfield_with_nested_array_is_allowed`, which lives in `tests/types/test_converters.py` beside the existing `_FakeArrayField` fixture; the fixture's locality is a concrete reason to move that one test. `test_annotation_override_does_not_populate_shared_enum_cache_for_co_resident_types` lives in `tests/types/test_definition_order.py` — mandatory, because it exercises override-vs-non-override cross-talk rather than converter-internal behavior.

The Slice 1 test cluster has 19 tests total.

**Four core override tests** — cover the new annotation-only scalar override path:

- `test_annotation_only_scalar_field_override_wins_over_synthesized` — **pre-finalize annotation contents.** Assert `cls.__annotations__[field_name]` is the consumer's type immediately after `__init_subclass__`.
- `test_annotation_only_scalar_override_populates_definition_metadata` — **`consumer_*_fields` introspection.** Assert the new `consumer_annotated_scalar_fields` set on `DjangoTypeDefinition` contains exactly the overridden name, that `consumer_authored_fields` contains it (transitively, via the union), and that `consumer_assigned_scalar_fields` does NOT (because the override is annotation-only).
- `test_annotation_only_scalar_override_does_not_emit_synthesized_annotation` — **`_build_annotations` skip.** Assert the synthesized annotations dict — the first element of `_build_annotations`'s return tuple — does NOT contain the override-field key. Whitebox-but-stable: the synthesized dict is what feeds the post-merge line at `django_strawberry_framework/types/base.py::DjangoType.__init_subclass__ #"cls.__annotations__ = {**synthesized, **consumer_annotations}"`, so its shape is the contract under test.
- `test_annotation_only_scalar_override_survives_strawberry_finalization` — **end-to-end Strawberry schema.** Build a `strawberry.Schema(query=Query)` with a query field returning the type, execute an introspection query of shape `__type(name: "...") { fields { name type { kind name ofType { kind name } } } }`, unwrap through `kind == "NON_NULL"`, and assert the terminal `ofType.name` matches the consumer's annotation.

**Four converter-bypass tests** — pin the bypass contract from [Decision 7a](#decision-7a--converter-validation-bypass):

- `test_annotation_override_of_unsupported_scalar_field_type_is_allowed` — annotation override is a recourse parallel to `Meta.exclude` for unsupported scalar field types.
- `test_annotation_override_of_grouped_choices_field_is_allowed` — annotation override bypasses `convert_choices_to_enum`'s grouped-choices rejection; `registry.get_enum(model, field_name)` is `None` for the overridden field.
- `test_annotation_override_of_arrayfield_with_nested_array_is_allowed` — annotation override bypasses `convert_scalar`'s nested-`ArrayField` rejection. Placement: `tests/types/test_converters.py`.
- `test_annotation_override_does_not_populate_shared_enum_cache_for_co_resident_types` — pins the cross-type behavior change Decision 7a flags. Two `DjangoType`s on the same `choices=` column, one overriding and one not: the non-overriding type populates the shared enum cache, the overriding type does not (its GraphQL surface uses the consumer's annotation; the cache is populated by the non-overriding type alone).

**Eleven Relay-collision tests** — pin [Decision 7](#decision-7--relay-id-override-collision):

- `test_consumer_id_annotation_on_relay_node_type_raises` — `ConfigurationError` at class-creation time with message pointing at `relay.NodeID[...]` (annotation reject path, [`Meta.interfaces`][glossary-metainterfaces] declaration shape).
- `test_consumer_id_annotation_on_direct_relay_node_subclass_raises` — direct `class DirectRelayChild(DjangoType, relay.Node)` declaration (NO `Meta.interfaces` line) with `id: int`; same `ConfigurationError` message contract as the `Meta.interfaces` variant. Pins the `issubclass(cls, relay.Node)` half of `_is_relay_shaped`'s disjunction.
- `test_consumer_id_assigned_strawberry_field_on_relay_node_type_raises` — `ConfigurationError` at class-creation time with message naming `resolve_id`, `relay.NodeID[...]`, and the resolver-backed sibling-field workaround (assigned reject path; a small intentional behavior change).
- `test_consumer_id_unresolved_non_nodeid_string_on_relay_node_type_raises` — `id: "MissingType"` (a non-NodeID string) raises. Without this test, typos would slip past the guard at class-creation time.
- `test_consumer_id_typo_lookalike_nodeid_string_on_relay_node_type_raises` — `id: "NotNodeID[int]"` (and similar prefixed-substring lookalikes like `"MyNodeID[int]"`) raise via the token-shaped regex. Pins that `(?:^|\.)NodeID\[` rejects what a plain `"NodeID[" in raw` substring check would accept.
- `test_consumer_id_relay_nodeid_annotation_on_relay_node_type_is_accepted` — `id: relay.NodeID[int]` direct form passes the guard (escape-hatch accept path; end-to-end success).
- `test_consumer_id_resolved_string_relay_nodeid_annotation_on_relay_node_type_is_accepted_end_to_end` — `id: "relay.NodeID[int]"` stringified form with `relay` importable at module scope; assert class creation + finalize + schema build all succeed. Pins the resolved-string end-to-end path.
- `test_consumer_id_unresolved_nodeid_shaped_string_on_relay_node_type_passes_guard_only` — `id: "relay.NodeID[int]"` stringified form with `relay` NOT importable from the class's resolution scope; assert ONLY that class creation succeeds (the regex accepts by shape alone). Pins the guard-only-suppression contract; finalize / schema build are explicitly NOT asserted because Strawberry's downstream resolution operates against the same module globals and may still fail there. **The test name and its `spec015_`-prefixed stub-module identifier are the landed spelling**, drawn from the pre-renumber card number and from the retired detection mechanism's vocabulary; neither is renamed.
- `test_consumer_id_resolved_relay_nodeid_with_unresolved_sibling_annotation_is_accepted` — a directly-resolved `id: relay.NodeID[int]` alongside a forward-referenced sibling annotation passes the guard. Pins that the verdict on `id` is independent of every other annotation on the class. **The test name is the landed spelling** and predates the current detection mechanism, under which the independence is structural rather than a recovery path.
- `test_consumer_non_id_scalar_override_on_relay_node_type_is_accepted` — a non-`id` consumer override on a Relay-Node-shaped type passes the guard (custom-pk / non-collision accept path; recipe: `description: int`).
- `test_inherited_id_annotation_on_relay_node_subclass_is_handled_by_pk_suppression` — an inherited `id: int` annotation on a Relay-Node-shaped subclass does NOT trigger the guard at class-creation time, AND `strawberry.Schema(...)` succeeds because `_build_annotations`'s pk-suppression branch strips the synthesized `id` and the post-merge reassignment leaves the child without an `id` annotation; Strawberry applies the Relay-supplied `id: GlobalID!` and `resolve_id_attr()` falls back to `"pk"`.

Slice 2 has no new tests — it deletes the previously-skipped `test_consumer_annotation_overrides_synthesized`. The full-suite pass on Slice 2 is the only test-side contract.

Slices 3 / 4 / 5 are documentation-only and have no test deltas. Coverage stays at 100%: the new definition field is exercised by Slice 1 tests; the new collection branch in `__init_subclass__` is exercised by every override test in `tests/types/test_definition_order.py`; the Relay collision guard is exercised by all eleven Relay tests (five reject + six accept); `_id_annotation_is_relay_node_id`'s resolved-object accept arm is hit by `test_consumer_id_relay_nodeid_annotation_on_relay_node_type_is_accepted` and `test_consumer_id_resolved_relay_nodeid_with_unresolved_sibling_annotation_is_accepted`, its resolved-object reject arm by `test_consumer_id_annotation_on_relay_node_type_raises`, its string accept arm by `test_consumer_id_resolved_string_relay_nodeid_annotation_on_relay_node_type_is_accepted_end_to_end` and `test_consumer_id_unresolved_nodeid_shaped_string_on_relay_node_type_passes_guard_only`, and its string reject arm by `test_consumer_id_unresolved_non_nodeid_string_on_relay_node_type_raises` and `test_consumer_id_typo_lookalike_nodeid_string_on_relay_node_type_raises`; and the converter-bypass paths are exercised by the four bypass tests (unsupported / grouped-choices / nested-array / cross-type-cache).

## Definition of done

- [ ] Every Slice 1 / Slice 2 / Slice 3 checkbox in [Slice checklist](#slice-checklist) is checked.
- [ ] `tests/types/test_base.py::test_consumer_annotation_overrides_synthesized` is deleted per [Decision 5](#decision-5--test-placement-and-the-skipped-tests-fate); no `@pytest.mark.skip` block referencing "Deferred scalar-field override behavior" remains.
- [ ] All 19 Slice 1 tests pass (four core overrides + four converter-bypass + eleven Relay-collision tests — five reject + six accept). Test placement: the override-contract host (`tests/types/test_definition_order.py`) for the core overrides, the Relay-collision tests, and the cross-type cache test; the converter test host (`tests/types/test_converters.py`) for the nested-`ArrayField` bypass test.
- [ ] `uv run pytest` passes locally with 100% package coverage.
- [ ] `uv run ruff check .` passes.
- [ ] `uv run ruff format --check .` passes.
- [ ] `git diff --check` passes.
- [ ] [`docs/GLOSSARY.md`][glossary]'s [`Scalar field override semantics`][glossary-scalar-field-override-semantics] entry reads `shipped (0.0.6)` (Slice 5).
- [ ] `docs/GLOSSARY.md`'s [`Scalar field conversion`][glossary-scalar-field-conversion] entry names annotation override as a parallel recourse to [`Meta.exclude`][glossary-metaexclude] for unsupported scalar fields (Slice 5).
- [ ] `docs/GLOSSARY.md`'s `Scalar field override semantics` body names the metadata-route limitation: field-level GraphQL metadata on the Relay-supplied `id` is not configurable in `0.0.6`; the documented workaround is a **resolver-backed sibling field** (`@strawberry.field(description="…") def display_id(self) -> strawberry.ID: return str(self.pk)`) carrying the metadata AND a value source, with the Relay-supplied `id` left undecorated. A metadata-only sibling without a resolver would build but fail at query time and is NOT recommended (Slice 5).
- [ ] `KANBAN.md` carries `DONE-019-0.0.6` in the Done section with the verbatim body from Slice 5 above, and no in-flight entry for the card remains.
- [ ] `CHANGELOG.md` carries the five entries from Slice 5 (`Added` annotation-only, `Added` introspection field, `Changed` converter-bypass, `Added` Relay annotation-collision guard, `Changed` assigned-id rejection on Relay-Node-shaped types — the last with the sibling-field workaround acknowledgment), under `[Unreleased]` before the release cut and under `## [0.0.6] - 2026-05-19` after it.
- [ ] Slice 4 version-bump quintet is verified by `grep` rather than blind edits — every checkbox is a no-op if `spec-017-deferred_scalars-0_0_6.md` or `spec-018-meta_primary-0_0_6.md` already landed the bump.
- [ ] No new public top-level symbol; no new `Meta.*` key; `django_strawberry_framework/__init__.py.__all__` is unchanged.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../AGENTS.md
[contributing]: ../../CONTRIBUTING.md
[kanban]: ../../KANBAN.md

<!-- docs/ -->
[glossary-bigint-scalar]: ../GLOSSARY.md#bigint-scalar
[glossary-choice-enum-generation]: ../GLOSSARY.md#choice-enum-generation
[glossary-configurationerror]: ../GLOSSARY.md#configurationerror
[glossary-definition-order-independence]: ../GLOSSARY.md#definition-order-independence
[glossary-djangotype]: ../GLOSSARY.md#djangotype
[glossary-finalize-django-types]: ../GLOSSARY.md#finalize_django_types
[glossary-index]: ../GLOSSARY.md#index
[glossary-metaexclude]: ../GLOSSARY.md#metaexclude
[glossary-metafields]: ../GLOSSARY.md#metafields
[glossary-metainterfaces]: ../GLOSSARY.md#metainterfaces
[glossary-metaprimary]: ../GLOSSARY.md#metaprimary
[glossary-relation-handling]: ../GLOSSARY.md#relation-handling
[glossary-relay-node-integration]: ../GLOSSARY.md#relay-node-integration
[glossary-scalar-field-conversion]: ../GLOSSARY.md#scalar-field-conversion
[glossary-scalar-field-override-semantics]: ../GLOSSARY.md#scalar-field-override-semantics
[glossary-specialized-scalar-conversions]: ../GLOSSARY.md#specialized-scalar-conversions
[glossary]: ../GLOSSARY.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[spec-019-rationale]: appx/spec-019-consumer_overrides_scalar-0_0_6-rationale.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
