# Spec: Consumer override semantics for scalar fields

Target release: `0.0.6`.
Status: shipped (`0.0.6`, 2026-05-19); archived. Card `DONE-019-0.0.6`.
Owner: package maintainer.
Predecessors: [`docs/GLOSSARY.md`][glossary] (entries [`DjangoType`][glossary-djangotype], [`Scalar field conversion`][glossary-scalar-field-conversion], [`Scalar field override semantics`][glossary-scalar-field-override-semantics], [`Definition-order independence`][glossary-definition-order-independence], [`Relation handling`][glossary-relation-handling]), [`KANBAN.md`][kanban] card `DONE-019-0.0.6`.
Card line: ["Consumer override semantics (scalar fields) — extends the `DONE-010-0.0.4` relation-field override contract to scalar fields and closes out the remaining `0.0.6` patch."][kanban]
The reasons behind each Decision and the alternatives it rejected live in [`docs/SPECS/appx/spec-019-consumer_overrides_scalar-0_0_6-rationale.md`][spec-019-rationale]. This file states the contract.

## Key glossary references

Skim these [`docs/GLOSSARY.md`][glossary] entries first — they anchor the vocabulary used throughout the spec:

- [`DjangoType`][glossary-djangotype] — the base class whose scalar fields this spec lets consumers override.
- [`Scalar field conversion`][glossary-scalar-field-conversion] — the auto-synthesized scalar annotation path a consumer override replaces.
- [`Scalar field override semantics`][glossary-scalar-field-override-semantics] — `shipped (0.0.6)`; the entry this spec owns.
- [`Specialized scalar conversions`][glossary-specialized-scalar-conversions] — home of the `ArrayField`, `HStoreField`, and [`BigInt`][glossary-bigint-scalar] mappings whose rejection paths the converter-bypass contract explicitly skips for overridden fields.
- [`Relation handling`][glossary-relation-handling] — the relation-override path whose annotation-only contract the scalar path mirrors.
- [`Relay Node integration`][glossary-relay-node-integration] — the broader Relay contract the `id` collision guard protects; documents `relay.NodeID[...]` as the supported consumer escape hatch.
- [`Definition-order independence`][glossary-definition-order-independence] — the foundation slice (`DONE-010-0.0.4`) that pinned the relation-field override contract; the scalar path has the same shape.
- [`ConfigurationError`][glossary-configurationerror] — raised at type-creation time for unsupported shadow shapes, including the Relay `id` collision guard ([Decision 7](#decision-7--relay-id-override-collision)).

Project conventions to follow:

- [`AGENTS.md`][agents] — test placement: a line a real fakeshop query reaches is pinned at the live `/graphql/` tier.
- [`CONTRIBUTING.md`][contributing] — 100% coverage gate; the single-sourced version.
- [`KANBAN.md`][kanban] — the `DONE-019-0.0.6` card.
- [`docs/TREE.md`][tree] — package and test layout.

## Slice checklist

Each top-level item maps to one commit in the [Implementation plan](#implementation-plan).

- [ ] Slice 1: Track annotation-only scalar overrides on `DjangoTypeDefinition`
  - [ ] In `django_strawberry_framework/types/base.py::DjangoType.__init_subclass__` (consumer-field collection block beginning with `consumer_annotations = dict(cls.__annotations__)`), collect `consumer_annotated_scalar_fields` parallel to `consumer_annotated_relation_fields`: the same `consumer_annotations` mapping, filtered on `not field.is_relation` instead of `field.is_relation`. (See [Decision 1](#decision-1--annotation-only-scalar-override-collection).)
  - [ ] `django_strawberry_framework/types/definition.py::DjangoTypeDefinition` carries `consumer_annotated_scalar_fields: frozenset[str] = frozenset()` in the **grouped-by-style** order (Decision 3): annotated-relation, annotated-scalar, assigned-relation, assigned-scalar.
  - [ ] The set is unioned into `consumer_authored_fields` at `django_strawberry_framework/types/base.py::DjangoType.__init_subclass__ #"consumer_authored_fields = frozenset"`. The scalar branch of `_build_annotations` short-circuits on `consumer_authored_fields` membership, so synthesis is skipped for annotation-only scalars, and the post-merge line at `django_strawberry_framework/types/base.py::DjangoType.__init_subclass__ #"cls.__annotations__ = {**synthesized, **consumer_annotations}"` leaves the consumer's annotation untouched.
  - [ ] The set is passed to `DjangoTypeDefinition` at the registration call site (`django_strawberry_framework/types/base.py::DjangoType.__init_subclass__ #"definition = DjangoTypeDefinition("`).
  - [ ] **Module-scope helpers for the Relay guard**, in `django_strawberry_framework/types/base.py` **above** `DjangoType`'s class definition. The guard body calls `_id_annotation_is_relay_node_id(cls)`, which calls `_has_node_id_marker(...)`, which uses `_NODEID_STRING_RE` — all three exist at module scope when the guard executes. Full bodies in [Decision 7](#decision-7--relay-id-override-collision)'s code block.
    - [ ] `_NODEID_STRING_RE = re.compile(r"(?:^|\.)NodeID\[")` — module-scope (compiled once per process).
    - [ ] `def _has_node_id_marker(hint: object) -> bool:` returning `typing.get_origin(hint) is Annotated and any(isinstance(arg, NodeIDPrivate) for arg in typing.get_args(hint))`.
    - [ ] `def _id_annotation_is_relay_node_id(cls: "type[DjangoType]") -> bool:` reading `cls.__annotations__["id"]` directly and dispatching on `isinstance(raw, str)` — string form to the regex, resolved form to `_has_node_id_marker`.
    - [ ] `def _is_relay_shaped(cls: "type[DjangoType]", interfaces: tuple[type[object], ...]) -> bool:` returning `any(issubclass(i, relay.Node) for i in interfaces) or issubclass(cls, relay.Node)` — the single source of truth for the Relay-shape predicate, read by both this card's collision guard and `_build_annotations`'s `suppress_pk_annotation`.
  - [ ] **Relay `id` collision guard.** After the `consumer_annotated_scalar_fields` / `consumer_assigned_scalar_fields` collections are built but before `_build_annotations` is invoked, detect: (a) `_is_relay_shaped(cls, validated.interfaces)` is True for the `interfaces` tuple returned by `_validate_meta`; AND (b) the consumer authored an entry for the GraphQL field name `"id"` — either an annotation (`"id" in cls.__annotations__`; key-presence rather than value-truthiness, so unusual annotations like `id: None`, `id: Literal[None]`, or string forms that evaluate to false-y types are also detected) or an assignment (`isinstance(cls.__dict__.get("id"), StrawberryField)`). Two reject paths:
    - **Assigned `id = <StrawberryField>`**: always rejected on a Relay-Node-shaped type. The error message names three supported alternatives: `@classmethod resolve_id` for a custom id resolver, `id: relay.NodeID[<pk_type>]` for a custom id annotation, and a **resolver-backed sibling field** — e.g. `@strawberry.field(description="…") def display_id(self) -> strawberry.ID: return str(self.pk)` — for the field-level GraphQL metadata use case. Assigned `id` overrides — including `@strawberry.field def id(self) -> relay.GlobalID: ...`, which Strawberry itself would accept — are banned uniformly on Relay-Node-shaped types.
    - **Annotation `id: <type>` where `<type>` is not `relay.NodeID[...]`**: rejected. Detection reads `cls.__annotations__["id"]` and dispatches on the value's shape — a string is matched against the token-shaped regex `(?:^|\.)NodeID\[` (so `"relay.NodeID[int]"`, `"strawberry.relay.NodeID[int]"`, and `"NodeID[int]"` pass while prefixed-substring lookalikes such as `"NotNodeID[int]"` and `"MyNodeID[int]"` are rejected); a resolved object is checked for the `Annotated[T, NodeIDPrivate]` marker. Accepting a NodeID-shaped string is package-level guard suppression only — Strawberry's downstream schema construction resolves the same string against `cls`'s module globals and may still fail there if the consumer has not made the symbol importable. The error message points at `relay.NodeID[<pk_type>]` as the supported escape hatch. (See [Decision 7](#decision-7--relay-id-override-collision) for the helper bodies.) **Important: the predicate is keyed off the GraphQL field name `"id"`, not the model's pk name.** A model with `code = models.CharField(primary_key=True)` and a consumer `code: str` override does NOT trigger the guard — the GraphQL fields are `id: ID!` (from Relay) and `code: String!` (from the consumer), no collision.
  - [ ] Tests in `tests/types/test_definition_order.py` (the override-contract host, home of the relation-override tests and `test_assigned_scalar_field_override_keeps_consumer_resolver`), plus the live `/graphql/` tier for the SDL a real query observes:
    - [ ] `test_annotation_only_scalar_field_override_wins_over_synthesized` (the headline test): declare a `DjangoType` with a Django `CharField` selected and a consumer annotation `description: int` shadowing it. Pre-finalize, assert `cls.__annotations__["description"] is int`. Post-finalize, assert the same — and assert the Strawberry definition's field type matches the consumer's annotation, not the auto-synthesized `str`.
    - [ ] `test_annotation_only_scalar_override_populates_definition_metadata`: assert `definition.consumer_annotated_scalar_fields == frozenset({"description"})`, `definition.consumer_authored_fields >= frozenset({"description"})`, and `definition.consumer_assigned_scalar_fields == frozenset()` (annotation-only, no assignment).
    - [ ] `test_annotation_only_scalar_override_does_not_emit_synthesized_annotation`: assert the synthesized annotations dict returned by `_build_annotations` does NOT contain `"description"` for the override case. (Pins that the short-circuit fires; without this we could still merge consumer-over-synthesized but the side-effect of double-walking the field path could regress later.)
    - [ ] `examples/fakeshop/test_query/test_scalars_api.py::test_override_specimen_consumer_field_overrides_resolve_over_http` (live tier): `OverriddenScalarSpecimenType` in `examples/fakeshop/apps/scalars/schema.py` carries an annotation-only widening override (`quantity`, an `IntegerField` annotated as nullable `Float`) and an annotation escape hatch over an unsupported column (`token`); the test resolves them over `/graphql/` after [`finalize_django_types`][glossary-finalize-django-types]`()` and introspects the SDL (`quantity: Float`). Pins the end-to-end contract: the override survives `strawberry.type(...)` decoration.
    - [ ] **Converter-bypass regressions (four tests).** The short-circuit skips `convert_field_output(...)` (and so `convert_scalar(...)`) for the overridden field, which means every converter-side validation and side effect is bypassed for that field. The bypass is the intended consumer-authoritative contract (see [Decision 7a](#decision-7a--converter-validation-bypass)), but it needs explicit tests so future readers understand the surface and so converter changes do not silently re-introduce validation against an overridden field:
      - [ ] `test_annotation_override_of_unsupported_scalar_field_type_is_allowed`: uses the `_FakeUnsupportedField(models.Field)` fixture in `tests/types/test_definition_order.py`, a one-line `Field` subclass whose MRO has no `SCALAR_MAP` match. Declare a `DjangoType` selecting that field. Without the override, `convert_scalar` raises [`ConfigurationError`][glossary-configurationerror]. With a consumer `myfield: str` annotation (or `int` — any Strawberry-supported scalar annotation; **NOT** `bytes`, which Strawberry's schema-construction pass rejects as an unexpected Python type and would create a false failure unrelated to the bypass contract), assert: (a) no error is raised at class-creation time, (b) `definition.consumer_annotated_scalar_fields` contains the field name, and (c) `finalize_django_types()` succeeds. The consumer's override is the recourse for unsupported scalars; [`Meta.exclude`][glossary-metaexclude] is still the recourse for "drop the field entirely".
      - [ ] `test_annotation_override_of_grouped_choices_field_is_allowed`: declare a `DjangoType` selecting a Django `CharField` with grouped `choices=[("group1", [("a", "A"), ("b", "B")])]`. Without the override, `convert_choices_to_enum` raises `ConfigurationError` containing `"grouped-choices"` (`tests/types/test_converters.py::test_grouped_choices_form_rejected` pins this). With a consumer `status: str` annotation, assert no error is raised, the type is finalizable, and `registry.get_enum(model, "status")` is `None` (enum registration is bypassed along with annotation synthesis).
      - [ ] `test_annotation_override_of_arrayfield_with_nested_array_is_allowed`: real `django.contrib.postgres.fields.ArrayField` testing requires the `_ARRAY_FIELD_CLS` monkeypatch + `_FakeArrayField` fixture pattern that lives in `tests/types/test_converters.py::_FakeArrayField` (every `ArrayField` test uses it; the production code soft-imports the real class at `django_strawberry_framework/types/converters.py #"_ARRAY_FIELD_CLS = cast("` and CI environment-dependence is the failure mode without the monkeypatch). **Place this single test in `tests/types/test_converters.py`** beside the existing `_FakeArrayField` tests so the fixture lookup stays local. **The model-field name and the consumer-annotation name MUST match** — mirror the existing converter tests' `arr`-named field, so the consumer annotation is `arr: list[list[int]]`. A name mismatch means the override-collection path never fires (the consumer annotation does not name a selected model field) and the test exercises the rejection path instead — false-passing for the wrong reason. Test body: `monkeypatch.setattr(converters, "_ARRAY_FIELD_CLS", _FakeArrayField)`; build a `_FakeArrayField(_FakeArrayField(models.IntegerField()))` instance registered as a model field named `arr`; declare a `DjangoType` selecting that field with a consumer `arr: list[list[int]]` annotation; assert no error is raised at class-creation time and `finalize_django_types()` succeeds. `tests/types/test_converters.py::test_array_field_multidim_rejected_via_fake_sentinel` pins that un-overridden nested arrays still raise.
      - [ ] `test_annotation_override_does_not_populate_shared_enum_cache_for_co_resident_types`: pins the Decision 7a cross-type flag that two `DjangoType`s on the same model with the same `choices=` column — one overriding and one not — get the fresh enum from the non-overriding type alone. Declare a single Django model with a non-grouped `status` `CharField(choices=[...])`. Declare two `DjangoType`s on that model: `OverrideType` with `class Meta: model = M; primary = True; fields = ("status",)` and a consumer `status: str` annotation (override); `NonOverrideType` with `class Meta: model = M; fields = ("status",)` (no override). Two types on one model need a [`Meta.primary`][glossary-metaprimary]; `OverrideType` carries it. `finalize_django_types()`. Assert: (a) `registry.get_enum(model, "status")` returns a non-`None` enum class (populated by `NonOverrideType`'s `convert_scalar` call); (b) building a `strawberry.Schema` and introspecting `NonOverrideType.status` returns the generated enum's GraphQL name; (c) introspecting `OverrideType.status` returns `String!` (the consumer's annotation). Pins both halves of the contract — the bypass on the overriding type does not poison the cache for the non-overriding type, and the cache entry from the non-overriding type does not leak into the overriding type's GraphQL surface. **Test placement: `tests/types/test_definition_order.py`, mandatory** — the test exercises override-vs-non-override cross-talk, not converter-internal behavior, so it belongs with the rest of the override-contract matrix.
  - [ ] **Relay collision tests (eleven)** in `tests/types/test_definition_order.py` alongside the four-corner cluster:
    - [ ] `test_consumer_id_annotation_on_relay_node_type_raises`: declare a `DjangoType` with [`Meta.interfaces`][glossary-metainterfaces]` = (relay.Node,)` and an `id: int` (or `id: str`) consumer annotation. Assert `ConfigurationError` raised at class-creation time (before `finalize_django_types()`), with message containing both `"relay.NodeID"` and `"GlobalID"`. Pins the early-raise contract for the `Meta.interfaces` declaration shape; without the guard, the consumer would see a Strawberry-side `ValueError` only at `strawberry.Schema(...)` construction, which is the wrong UX surface.
    - [ ] `test_consumer_id_annotation_on_direct_relay_node_subclass_raises`: declare a `DjangoType` that directly subclasses `relay.Node` — i.e. `class DirectRelayChild(DjangoType, relay.Node): id: int; class Meta: model = Category; fields = ("id", "name")` (NO `Meta.interfaces` line). Assert `ConfigurationError` raised at class-creation time with the same message contract as the `Meta.interfaces` variant. Pins the second half of `_is_relay_shaped`'s disjunction — without this test, an implementation wiring only the `interfaces` half would pass every other Relay-collision test while leaving `class CategoryNode(DjangoType, relay.Node): id: int` to fall through to the downstream Strawberry `ValueError`. Parametrizing `test_consumer_id_annotation_on_relay_node_type_raises` over both declaration styles is an equivalent discharge; the contract is "the annotation reject path fires for both shapes". Note: the assigned-`id` reject path is deliberately NOT parametrized over the direct-inheritance shape — the high-value pin is annotation-side.
    - [ ] `test_consumer_id_assigned_strawberry_field_on_relay_node_type_raises`: declare a `DjangoType` with `Meta.interfaces = (relay.Node,)` and an assigned `id = strawberry.field(resolver=...)` (or `@strawberry.field def id(self) -> relay.GlobalID: ...` decorator-style). Assert `ConfigurationError` raised at class-creation time with message containing **all three** of `"resolve_id"`, `"relay.NodeID"`, and one of `"display_id"` / `"sibling field"`. Pins the intentional ban on assigned `id` overrides on Relay-Node-shaped types and the resolver-backed sibling-field workaround in the error message.
    - [ ] `test_consumer_id_unresolved_non_nodeid_string_on_relay_node_type_raises`: declare a `DjangoType` with `Meta.interfaces = (relay.Node,)` and a stringified `id: "MissingType"` annotation (a typo, or a forward reference to a non-existent class). Assert `ConfigurationError` raised at class-creation time with message containing both `"relay.NodeID"` and `"GlobalID"`. The helper sees a string that does not match `(?:^|\.)NodeID\[` and rejects. Without this test, a typo like `id: "Stirng"` would slip past the guard at class-creation time and surface only as a Strawberry schema-construction error later — exactly the failure mode the guard exists to prevent.
    - [ ] `test_consumer_id_typo_lookalike_nodeid_string_on_relay_node_type_raises`: declare a `DjangoType` with `Meta.interfaces = (relay.Node,)` and a stringified `id: "NotNodeID[int]"` annotation — the prefix means the string DOES contain `"NodeID["` as a substring but is NOT a token-shaped NodeID reference. Assert `ConfigurationError` raised at class-creation time with message containing both `"relay.NodeID"` and `"GlobalID"`. Verify a `"MyNodeID[int]"` variant in the same test (parametrize or add a second assertion). Pins that `_NODEID_STRING_RE` requires a start-of-string or dot boundary before `NodeID[`; a plain substring test would accept these false positives.
    - [ ] `test_consumer_id_relay_nodeid_annotation_on_relay_node_type_is_accepted`: declare a `DjangoType` with `Meta.interfaces = (relay.Node,)` and an `id: relay.NodeID[int]` consumer annotation. Assert no `ConfigurationError` at class-creation time; assert `finalize_django_types()` succeeds; assert `strawberry.Schema(...)` builds. Pins that the guard does NOT reject the advertised escape hatch. Mirrors the `tests/types/test_relay_interfaces.py::test_composite_pk_with_explicit_node_id_annotation_is_accepted` pattern, applied to a plain (non-composite-pk) Relay-Node-shaped type to exercise this card's guard specifically.
    - [ ] `test_consumer_id_resolved_string_relay_nodeid_annotation_on_relay_node_type_is_accepted_end_to_end`: declare a `DjangoType` with `Meta.interfaces = (relay.Node,)` and an explicit stringified `id: "relay.NodeID[int]"` consumer annotation, **with `relay` imported at module scope** so the string resolves cleanly under Strawberry's downstream schema-construction resolution. Assert no `ConfigurationError` at class-creation time; assert `finalize_django_types()` succeeds; assert `strawberry.Schema(...)` builds; assert the introspected `id` field is `ID!` (the Relay-supplied interface field). Pins that the string form passes the package guard **and** that Strawberry's downstream pipeline accepts the same string.
    - [ ] `test_consumer_id_unresolved_nodeid_shaped_string_on_relay_node_type_passes_guard_only`: declare a `DjangoType` with `Meta.interfaces = (relay.Node,)` and an explicit stringified `id: "relay.NodeID[int]"` consumer annotation, **with `relay` NOT importable** from the class's resolution scope. Assert ONLY that class creation succeeds — no `ConfigurationError` at `__init_subclass__` time — because the regex match on the raw string accepts by shape alone. **Do NOT assert** `finalize_django_types()` or `strawberry.Schema(...)` succeed; Strawberry's downstream resolution operates against the same module globals and will fail with its own error if the consumer has not made `relay` resolvable. The spec contract for this case is "package guard suppressed at class-creation time"; full end-to-end resolution is the consumer's responsibility. **Recipe:** (1) generate a unique synthetic module name via `stub_name = f"spec015_unresolved_relay_stub_{uuid.uuid4().hex}"`; (2) register `sys.modules[stub_name] = types.ModuleType(stub_name)` and **assert** the stub module's `__dict__` has no `"relay"` key; (3) build the `DjangoType` via `types.new_class("UnresolvedRelayChild", (DjangoType,), {}, _body)` where `_body` mutates the class namespace to set `__module__ = stub_name`, `__annotations__ = {"id": "relay.NodeID[int]"}`, and a `Meta` class with `model = Category` and `interfaces = (relay.Node,)`; (4) assert ONLY that `types.new_class(...)` returns without raising; (5) wrap the body in `try/finally` so **both** `sys.modules.pop(stub_name, None)` **and** `registry.clear()` run even if the assertion fails — the synthetic type registers against `Category` the moment class creation passes the guard, and a stale co-resident type poisons the cross-type cache test if it runs later in the same session.
    - [ ] `test_consumer_id_resolved_relay_nodeid_with_unresolved_sibling_annotation_is_accepted`: declare a `DjangoType` with `Meta.interfaces = (relay.Node,)`, a directly-resolved `id: relay.NodeID[int]` consumer annotation, AND a forward-referenced sibling annotation like `items: list["AdminItemType"]` that does not resolve at class-creation time. Assert no `ConfigurationError` at class-creation time. Pins that the guard's verdict on `id` is **independent of every other annotation on the class**: the helper reads `cls.__annotations__["id"]` and nothing else, so an unresolvable sibling cannot influence the outcome. This is a realistic pattern for `DjangoType`s with forward-referenced relation annotations, and a detection mechanism that evaluated the whole class would have to recover from it explicitly.
    - [ ] `test_consumer_non_id_scalar_override_on_relay_node_type_is_accepted`: declare a `DjangoType` on a Relay-Node-shaped type with a non-`id` consumer scalar override (recipe: `description: int`). Assert no `ConfigurationError` is raised. Pins that the guard is keyed off the GraphQL field name `"id"`, not the model's pk name — a consumer who overrides a non-`id` field on a Relay-Node-shaped type does not collide with `Node.id` and must not be rejected.
    - [ ] `test_inherited_id_annotation_on_relay_node_subclass_is_handled_by_pk_suppression`: declare a base `DjangoType` subclass `BaseWithId` with an `id: int` annotation but no `Meta` (so `__init_subclass__` short-circuits the collection pipeline for the base). Then declare a child `ChildRelayType(BaseWithId)` with `class Meta: model = M; interfaces = (relay.Node,)`. Assert: (a) no `ConfigurationError` at class-creation time — the guard's `"id" in cls.__annotations__` predicate is False for the child, because inherited annotations do not land in the subclass's own `__annotations__` dict; (b) **`strawberry.Schema(query=Query, types=[ChildRelayType])` SUCCEEDS**. `_build_annotations`'s `suppress_pk_annotation and field.name == pk_name` branch suppresses the synthesized scalar `id` annotation for the child, and the post-merge line `cls.__annotations__ = {**synthesized, **consumer_annotations}` replaces the child's `__annotations__` with a dict containing neither the inherited `id: int` nor a synthesized one. Strawberry's `@strawberry.type` reads the child's assigned `__annotations__`, sees no `id`, applies Relay's `id: GlobalID!`, and `resolve_id_attr()` falls back to `"pk"`; (c) the introspected `id` field type is `ID!` (the Relay-supplied interface field), not `Int!`; (d) optionally, `ChildRelayType.resolve_id_attr() == "pk"`. Pins the inheritance behavior: the guard does NOT walk the MRO, and pk-suppression in `_build_annotations` silently handles the inherited `id: int` case, so no Strawberry `ValueError` fires. Without this test, future changes to the pk-suppression branch could regress the inherited-`id` corner without surfacing.
- [ ] Slice 2: One home for the override matrix
  - [ ] `tests/types/test_base.py` carries no override-contract test and no skipped placeholder for one; the matrix lives in `tests/types/test_definition_order.py` and the live tier. (See [Decision 5](#decision-5--test-placement-and-the-skipped-tests-fate).)
- [ ] Slice 3: Document the four-corner override contract in `_consumer_assigned_fields`'s docstring
  - [ ] The four-corner override matrix (`relation × annotation`, `relation × assigned`, `scalar × annotation`, `scalar × assigned`) is symmetric and complete. The `_consumer_assigned_fields` docstring at `django_strawberry_framework/types/base.py::_consumer_assigned_fields` names the parallel `consumer_annotated_relation_fields` / `consumer_annotated_scalar_fields` collection sites in `__init_subclass__`, the four `consumer_*_fields` sets on `DjangoTypeDefinition`, and the single `consumer_authored_fields` short-circuit in `_build_annotations`. Documentation only.
- [ ] Slice 4: Version at `0.0.6`
  - [ ] `django_strawberry_framework/__init__.py` `__version__` (the single version source) and the pinned `__version__` assertion in `tests/base/test_init.py` read `0.0.6`. The `0.0.6` line carries `DONE-016-0.0.6`, `DONE-017-0.0.6`, `DONE-018-0.0.6`, and this card; the bump is one change for the release.
- [ ] Slice 5: Docs and board
  - [ ] `docs/GLOSSARY.md` (rendered from the fakeshop glossary database; edit the database, then re-render):
    - [`Scalar field override semantics`][glossary-scalar-field-override-semantics] → `shipped (0.0.6)`: annotation-only and assigned-`strawberry.field` scalar overrides both supported, with the same `consumer_authored_fields` short-circuit; opt-out via [`Meta.exclude`][glossary-metaexclude]; field metadata via the assigned-`strawberry.field(...)` path; **converter validations bypassed for overridden fields** (consumer-authoritative contract — unsupported-scalar override, grouped-choices override, and nested-`ArrayField` override are the three behaviors worth highlighting); **`relay.Node` `id` collision rejected at type-creation time**, with two sub-restrictions: (1) assigned `id = <StrawberryField>` overrides are uniformly rejected on Relay-Node-shaped types (the supported alternatives are `relay.NodeID[<pk_type>]` for a custom id annotation, `@classmethod resolve_id` for a custom id resolver, and a **resolver-backed sibling field** — `@strawberry.field(description="…") def display_id(self) -> strawberry.ID: return str(self.pk)` — for the field-level GraphQL metadata use case, since the ban removes the only path for attaching `description`/`deprecation_reason`/`directives` to the Relay-supplied `id`; a metadata-only sibling like `display_id: ID = strawberry.field(description="…")` without a resolver would build but fail at query time because Strawberry's default resolver looks up `display_id` as an attribute on the returned model instance); (2) inherited `id` annotations on a Relay-Node-shaped subclass slip past the guard at class-creation time, and `_build_annotations`'s pk-suppression branch silently handles them — Strawberry sees no `id` annotation on the child, applies the Relay-supplied `id: GlobalID!`, and `resolve_id_attr()` falls back to `"pk"`, so schema construction succeeds. Annotation `id: relay.NodeID[...]` is accepted in direct, PEP 563 / stringified, and mixed (resolved-`id`-alongside-unresolved-sibling) forms; non-`id` overrides are accepted.
    - [`Scalar field conversion`][glossary-scalar-field-conversion] — unsupported scalar fields raise `ConfigurationError` with two consumer recourses: [`Meta.exclude`][glossary-metaexclude], or a consumer annotation override (see [Scalar field override semantics][glossary-scalar-field-override-semantics]). The grouped-choices and `ArrayField` shape rejections fire on the non-override path; the override path is a recourse for them too.
    - [`Definition-order independence`][glossary-definition-order-independence] — scalar override semantics are part of the foundation contract.
    - [Index][glossary-index] → the `Scalar field override semantics` status badge reads `shipped (0.0.6)`.
  - [ ] `KANBAN.md` carries the shipped `DONE-019-0.0.6` card (rendered from the fakeshop kanban database; the body is authored in the DB and never reproduced verbatim here, where a copy would drift against the live card).
  - [ ] `CHANGELOG.md` `## [0.0.6] - 2026-05-19` — five entries:
    - `Added`: Annotation-only scalar field overrides on `DjangoType`. Writing `description: int` (or any other class-level scalar annotation that shadows a Django scalar column selected via [`Meta.fields`][glossary-metafields]) is a stable public contract — the consumer's annotation wins over the auto-synthesized one and survives `finalize_django_types()` / `strawberry.type(...)` decoration. Mirrors the annotation-only relation-override path.
    - `Added`: `DjangoTypeDefinition.consumer_annotated_scalar_fields: frozenset[str]` — introspection surface for the override path; symmetric with `consumer_annotated_relation_fields`, `consumer_assigned_relation_fields`, and `consumer_assigned_scalar_fields`.
    - `Changed`: Annotation-only and assigned scalar field overrides bypass `convert_scalar` validations and side effects for the overridden field — unsupported-field-type rejection, grouped-choices rejection, `ArrayField` shape rejection, `null=True` widening, and choice-enum registration are skipped. The consumer's annotation is authoritative. `Meta.exclude` and annotation override are parallel consumer recourses for unsupported scalar fields.
    - `Added`: `ConfigurationError` raised at `DjangoType.__init_subclass__` time when a consumer authors an `id` annotation on a `Meta.interfaces = (relay.Node,)`-shaped type that is not a `relay.NodeID[...]`-marked annotation, pointing at `strawberry.relay.NodeID[<pk_type>]` as the supported escape hatch, in place of Strawberry's `ValueError` ("Interface field Node.id expects type ID! but ...") at `strawberry.Schema(...)` construction. The guard's accept forms are those of [Decision 7](#decision-7--relay-id-override-collision).
    - `Changed`: `id = <StrawberryField>` assignment on a `Meta.interfaces = (relay.Node,)`-shaped `DjangoType` raises `ConfigurationError` at `__init_subclass__` time, for consistency with the annotation-side guard; the supported alternatives are `@classmethod resolve_id`, `id: relay.NodeID[<pk_type>]`, and a **resolver-backed sibling field** for field-level GraphQL metadata.

## Problem statement

The `DONE-010-0.0.4` foundation slice pins the override contract for **relation fields** — both the annotation-only path (`items: list["AdminItemType"]`) and the assigned-`strawberry.field` path, exercised by `tests/types/test_definition_order.py::test_annotation_only_relation_override_keeps_generated_resolver`, `tests/types/test_definition_order.py::test_assigned_relation_field_override_keeps_consumer_resolver`, and `examples/fakeshop/test_query/test_library_api.py::test_library_relation_override_shapes_http_response_data`. The assigned-`strawberry.field` path for scalars is pinned by `tests/types/test_definition_order.py::test_assigned_scalar_field_override_keeps_consumer_resolver`.

The **annotation-only path** for scalars needs the same treatment. Writing `description: int` on a `DjangoType` whose `CharField` `description` column is selected via [`Meta.fields`][glossary-metafields] lands the consumer's annotation in `cls.__annotations__` at `__init_subclass__` time (the merge at `django_strawberry_framework/types/base.py::DjangoType.__init_subclass__ #"cls.__annotations__ = {**synthesized, **consumer_annotations}"` puts `consumer_annotations` last so consumer wins). Unless the name is in `consumer_authored_fields`, the synthesized scalar annotation is also computed — running every converter validation against a column the consumer has taken over — and the consumer's type wins only because dict-merge order favors it, which is not a stable contract.

This spec collects a `consumer_annotated_scalar_fields` set parallel to `consumer_annotated_relation_fields`, unions it into `consumer_authored_fields`, and pins the result with tests.

## Goals

- Collect `consumer_annotated_scalar_fields` in `DjangoType.__init_subclass__`, parallel to `consumer_annotated_relation_fields`.
- Carry `consumer_annotated_scalar_fields: frozenset[str] = frozenset()` on `DjangoTypeDefinition`.
- Union the set into `consumer_authored_fields` so the scalar-branch short-circuit in `_build_annotations` fires for the annotation-only override path.
- Pin the **converter-validation-bypass contract** for overridden scalar fields ([Decision 7a](#decision-7a--converter-validation-bypass)): consumer annotation overrides are authoritative, so `convert_scalar`'s unsupported-field-type rejection, grouped-choices rejection, `ArrayField` shape rejection, `null=True` widening, and choice-enum registration are all bypassed for an overridden field. Annotation override is a parallel recourse to [`Meta.exclude`][glossary-metaexclude] for unsupported scalar fields.
- Add the **Relay `id` collision guard** ([Decision 7](#decision-7--relay-id-override-collision)): raise [`ConfigurationError`][glossary-configurationerror] from `__init_subclass__` when the consumer authors an `id` entry (annotation or assigned `StrawberryField`) on a Relay-Node-shaped type, unless the annotation is a `relay.NodeID[...]` marker. Detection reads `cls.__annotations__["id"]` directly and dispatches on the value's shape — a token-shaped regex (`(?:^|\.)NodeID\[`) for the string form, the `Annotated[T, NodeIDPrivate]` marker for the resolved form. Replaces the downstream Strawberry-side `ValueError` at `strawberry.Schema(...)` construction.
- Keep the override matrix in one home (Decision 5).
- Document the four-corner override contract, the converter-bypass contract, and the Relay collision guard in [`docs/GLOSSARY.md`][glossary]'s [`Scalar field override semantics`][glossary-scalar-field-override-semantics] entry, flipping its status to `shipped (0.0.6)`.
- 100% coverage on the collection path, the definition field, the Relay guard (including both arms of the `_id_annotation_is_relay_node_id` dispatch), the converter bypass, and the cross-type enum-cache behavior. The 19-test Slice 1 cluster (4 core, one of them live + 4 converter-bypass + 11 Relay) is the contract surface.

## Non-goals

- **No `Meta.field_overrides = {...}` API.** The symmetric annotation-only + assigned-`strawberry.field` path covers the override contract; a declarative override key is out of scope.
- **No annotation/field-type compatibility pre-check.** Writing `description: int` against a `CharField` is the consumer's responsibility; the package does not assert that the consumer's annotation is type-compatible with the Django column. Runtime serialization errors at query time are the consumer-visible failure mode and are intentional — the package treats consumer overrides as authoritative.
- **No opt-out / removal API.** The [`Meta.exclude`][glossary-metaexclude] path covers "drop the field entirely". There is no sentinel-value or `Skip`-typed annotation shape (e.g. `description: None` or `description: strawberry.SKIP`) — the design space is not justified by any pending consumer use case.
- **No field metadata API on the annotation path.** Description / deprecation / default routing goes through the assigned `strawberry.field(...)` path (`description = strawberry.field(description="...", deprecation_reason="...")` is preserved by `_consumer_assigned_fields`'s scalar branch).
- **Relation overrides are the foundation contract.** The relation × {annotation, assigned} cells belong to `DONE-010-0.0.4`.
- **The post-merge annotation order at `django_strawberry_framework/types/base.py::DjangoType.__init_subclass__ #"cls.__annotations__ = {**synthesized, **consumer_annotations}"` puts consumer last.** The synthesized dict carries no entries for annotation-only-overridden scalars, so the merge is "consumer annotation only" for those keys.

## Architectural decisions

Each Decision below states the contract. The alternatives each one rejected, and why, live in [the rationale companion][spec-019-rationale].

### Decision 1 — Annotation-only scalar override collection

Symmetric to the relation collection. Two comprehensions rather than one, keeping the code shape symmetric with the relation collection one line above:

```python
# django_strawberry_framework/types/base.py::DjangoType.__init_subclass__
consumer_annotations = dict(cls.__annotations__)
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

The `field.name not in auto_annotated_fields` clause keeps an `auto`-typed annotation — a request for the model-inferred type, not a consumer override — out of `consumer_authored_fields`. The polarity filter uses `not field.is_relation` rather than an explicit `is False` comparison, matching the bare `if field.is_relation:` bool-coercion in `_build_annotations`.

### Decision 2 — `consumer_authored_fields` union shape

A single `consumer_authored_fields` frozenset is the short-circuit input to `_build_annotations`, built at `django_strawberry_framework/types/base.py::DjangoType.__init_subclass__ #"consumer_authored_fields = frozenset"`:

```python
# django_strawberry_framework/types/base.py::DjangoType.__init_subclass__
consumer_authored_fields = frozenset(
    {
        *consumer_annotated_relation_fields,
        *consumer_annotated_scalar_fields,
        *consumer_assigned_relation_fields,
        *consumer_assigned_scalar_fields,
    },
)
```

Order inside the set literal does not matter (frozenset is unordered). The line ordering keeps relations and scalars adjacent — relations first, then scalars, within each (annotated, assigned) pair.

`_build_annotations` needs only the union: it does not distinguish between the four corners. The same union is read by three validators as well — `_validate_nullability_override_targets`, `_validate_filesystem_path_targets`, and `_validate_relation_shape_targets` — each of which needs exactly the same "did the consumer author this name" question answered. One union is the shape every consumer of it wants.

### Decision 3 — `DjangoTypeDefinition.consumer_annotated_scalar_fields` field

Symmetric to the three sibling fields. The `consumer_*_fields` block in `django_strawberry_framework/types/definition.py::DjangoTypeDefinition` uses the **grouped-by-style** order — annotations group first, assignments group second, with relation and scalar adjacent within each:

```python
# django_strawberry_framework/types/definition.py::DjangoTypeDefinition
consumer_authored_fields: frozenset[str] = frozenset()
consumer_annotated_relation_fields: frozenset[str] = frozenset()
consumer_annotated_scalar_fields: frozenset[str] = frozenset()
consumer_assigned_relation_fields: frozenset[str] = frozenset()
consumer_assigned_scalar_fields: frozenset[str] = frozenset()
```

The field is read by tests for introspection (per the Slice 1 test cluster). No production code path consumes it directly — production routes through the unified `consumer_authored_fields`. The four-corner sets exist as the introspection surface and as a tested contract that the package will not silently change the bucketing.

### Decision 4 — `_build_annotations` body stays unchanged

The scalar branch in `django_strawberry_framework/types/base.py::_build_annotations` needs nothing override-specific beyond the membership test:

```python
# django_strawberry_framework/types/base.py::_build_annotations (scalar branch, abridged)
else:
    if field.name in consumer_authored_fields:
        # A consumer-assigned ``StrawberryField`` (or annotation) on a
        # scalar column wins over the auto-synthesized annotation.
        continue
    if suppress_pk_annotation and field.name == pk_name:
        continue
    # ... per-field nullability override tri-state -> force_nullable ...
    annotations[field.name] = convert_field_output(field, cls.__name__, ...)
```

The inline comment names "annotation" in parallel with "assigned `StrawberryField`": the one short-circuit covers both, and the annotation-only path is reached purely by the upstream collection adding annotation-only scalars to `consumer_authored_fields`.

### Decision 5 — Test placement and the skipped test's fate

The four-corner override matrix lives in `tests/types/test_definition_order.py` (the override-contract host), with the request-observable SDL at the live tier:

| Field shape | Override style | Test |
|---|---|---|
| Relation | Annotation-only | `tests/types/test_definition_order.py::test_annotation_only_relation_override_keeps_generated_resolver` |
| Relation | Assigned `strawberry.field` | `tests/types/test_definition_order.py::test_assigned_relation_field_override_keeps_consumer_resolver` + decorator variant `examples/fakeshop/test_query/test_library_api.py::test_library_relation_override_shapes_http_response_data` |
| Scalar | Assigned `strawberry.field` | `tests/types/test_definition_order.py::test_assigned_scalar_field_override_keeps_consumer_resolver` |
| Scalar | Annotation-only | `tests/types/test_definition_order.py::test_annotation_only_scalar_field_override_wins_over_synthesized` + live SDL `examples/fakeshop/test_query/test_scalars_api.py::test_override_specimen_consumer_field_overrides_resolve_over_http` |

**The package-tier override matrix lives in one file** — that is the rule a future override test follows too, rather than landing beside whatever converter it happens to exercise; `tests/types/test_base.py` holds no copy of it.

### Decision 6 — Why `_consumer_assigned_fields` stays the way it is

`_consumer_assigned_fields` (`django_strawberry_framework/types/base.py::_consumer_assigned_fields`) takes the class and walks `cls.__dict__`, bucketing assigned `StrawberryField` instances into a (relation, scalar) tuple. The function does NOT walk `consumer_annotations` — that is the parallel job of the annotation-collection lines in `django_strawberry_framework/types/base.py::DjangoType.__init_subclass__`. Symmetric responsibility split:

- `_consumer_assigned_fields` reads `cls.__dict__` → produces `(consumer_assigned_relation_fields, consumer_assigned_scalar_fields)`.
- The annotation-collection lines read `cls.__annotations__` → produce `(consumer_annotated_relation_fields, consumer_annotated_scalar_fields)`.

The two sources are independent: a consumer can write `description: int` annotation-only, OR `description = strawberry.field(...)` assigned, OR both — the four-corner matrix treats them as separate input channels, and the annotation collection is the parallel of `_consumer_assigned_fields`, not an extension of it.

### Decision 7 — Relay `id` override collision

`_build_annotations` processes each selected field in two ordered checks: first the consumer-authored short-circuit (`if field.name in consumer_authored_fields: continue`), then the `relay.Node` pk-suppression branch (`if suppress_pk_annotation and field.name == pk_name: continue`). The ordering matters: a consumer who writes an `id: int` annotation on a Relay-Node-shaped type lands `"id"` in `cls.__annotations__`, the consumer-authored short-circuit fires in the scalar branch, and the loop continues. The pk-suppression branch never executes for that field name. The merge at `django_strawberry_framework/types/base.py::DjangoType.__init_subclass__ #"cls.__annotations__ = {**synthesized, **consumer_annotations}"` then writes the consumer's `id: int` annotation onto `cls.__annotations__`.

Without a guard the downstream behavior is broken in a way that surfaces far from the source: `finalize_django_types()` runs to completion (the `_build_annotations` skip is cooperative with the consumer override); `strawberry.Schema(query=Query, types=[ThatType])` then fails inside Strawberry's schema-validation pass with a `ValueError` because `Node.id` is `ID!` (the interface contract) while the concrete type's `id` is `Int!`. The error originates from Strawberry's interface-compliance check, not from any `DjangoType` code path — the user's traceback points at `strawberry/schema/schema.py` rather than at `types/base.py`, and the message ("Interface field Node.id expects type ID! but ImplementingType.id is of type Int!") leaves the consumer to reverse-engineer the connection back to their `DjangoType` declaration.

**Contract.** A package-owned [`ConfigurationError`][glossary-configurationerror] is raised at `DjangoType.__init_subclass__` time when **and only when** the consumer authored an `"id"` entry on a Relay-Node-shaped type, AND the entry is not a `relay.NodeID[...]`-marked annotation. Assigned `id` overrides (any `StrawberryField`) are always rejected — the supported alternatives are the `@classmethod resolve_id` hook from Strawberry's Relay Node interface (custom id resolver) and `id: relay.NodeID[<pk_type>]` (custom id annotation). `id = strawberry.field(description="…")` therefore cannot attach GraphQL field-level metadata to the Relay-supplied `id`; the workaround is a **resolver-backed sibling field** (e.g. `@strawberry.field(description="…") def display_id(self) -> strawberry.ID: return str(self.pk)`) that carries the metadata AND defines a value source. A metadata-only sibling (`display_id: ID = strawberry.field(description="…")`) without a resolver would build but fail at query time, because Strawberry's default resolver looks up `display_id` as an attribute on the returned Django model instance and does not find it. The Relay-supplied `id` stays undecorated; field-level metadata on it is not configurable in `0.0.6`.

**The predicate is keyed off the GraphQL field name `"id"`, not the model's pk name.** This is a prohibition on the obvious-looking implementation, and it has two independent reasons:

1. A pk-keyed predicate rejects `id: relay.NodeID[int]` — the advertised escape hatch. `id` is a model pk field, so a `NodeID[int]` annotation lands in `consumer_annotated_scalar_fields` through the same collection path, and the guard would fire against the exact pattern its own error message recommends.
2. A pk-keyed predicate rejects non-`id` primary-key overrides. On a model with `code = models.CharField(primary_key=True)`, a consumer `code: str` override produces `id: ID!` (from Relay) and `code: String!` (from the consumer) — no `Node.id` collision at all. The existing `tests/types/test_relay_interfaces.py::test_composite_pk_with_explicit_node_id_annotation_is_accepted` (which uses `name: relay.NodeID[str]`) confirms the framework's broader contract that `relay.NodeID` annotations land on any attribute, not just `"id"`.

**The guard lives in `__init_subclass__`, between collection and `_build_annotations`.** That is the only point in the lifecycle where `cls.__annotations__`, `cls.__dict__`, the collected `consumer_*_scalar_fields`, and the validated `interfaces` tuple are all in hand *and* the error can still fire at class-definition time — which the reject tests and the CHANGELOG both assert. A check placed in `_build_annotations` fires too late and entangles configuration validation with annotation synthesis inside a per-field loop.

```python
# In DjangoType.__init_subclass__, after consumer_*_scalar_fields collection
# and BEFORE _build_annotations runs (so the error fires at type-creation time).
# ``relay_shaped`` is computed once and also feeds the override-target validators.
relay_shaped = _is_relay_shaped(cls, validated.interfaces)
if relay_shaped:
    has_id_assignment = isinstance(cls.__dict__.get("id"), StrawberryField)
    # Key-presence rather than value-truthiness, so unusual annotations like
    # ``id: None``, ``id: Literal[None]``, and string forms that evaluate to
    # false-y types are all detected.
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


# Module-scope helpers, defined above ``DjangoType`` (docstrings trimmed).

# The ``(?:^|\.)`` anchor accepts both the unqualified ``NodeID[int]`` and the
# dot-qualified ``relay.NodeID[int]`` / ``strawberry.relay.NodeID[int]`` forms
# while rejecting prefixed-substring lookalikes (``NotNodeID[int]``,
# ``MyNodeID[int]``). Module-scope, so it compiles once per process.
_NODEID_STRING_RE = re.compile(r"(?:^|\.)NodeID\[")


def _has_node_id_marker(hint: object) -> bool:
    # ``relay.NodeID[T]`` IS ``typing.Annotated[T, NodeIDPrivate()]``: the explicit
    # ``Annotated`` form and the sugar collapse to the same shape.
    if typing.get_origin(hint) is not Annotated:
        return False
    args: tuple[object, ...] = typing.get_args(hint)
    return any(isinstance(arg, NodeIDPrivate) for arg in args)


def _id_annotation_is_relay_node_id(cls: "type[DjangoType]") -> bool:
    # Reads ``cls.__annotations__`` directly - no ``typing.get_type_hints`` - so
    # no sibling annotation can influence the verdict and the behavior is the
    # same on every supported Python. Precondition: ``"id" in cls.__annotations__``.
    raw = cls.__annotations__["id"]
    if isinstance(raw, str):
        return bool(_NODEID_STRING_RE.search(raw))
    return _has_node_id_marker(raw)


def _is_relay_shaped(cls: "type[DjangoType]", interfaces: tuple[type[object], ...]) -> bool:
    # Single source of truth for the Relay-shape predicate, read by the collision
    # guard and by ``_build_annotations``'s pk-suppression branch. Both halves are
    # required: ``Meta.interfaces = (relay.Node,)`` and a direct
    # ``class X(DjangoType, relay.Node)`` declaration are both Relay-shaped.
    return any(issubclass(i, relay.Node) for i in interfaces) or issubclass(cls, relay.Node)
```

**Accepting a NodeID-shaped string is package-level guard suppression only.** Strawberry's downstream schema-construction pass resolves the same string annotation against `cls`'s module globals using its own evaluation path; if the consumer's string is not resolvable in that scope, Strawberry's error will still fire later. The package's `ConfigurationError` is suppressed at class-creation time, not the entire end-to-end failure. A test that wants to pin **end-to-end** schema success must ensure `relay` (or whichever module supplies `NodeID`) is importable at the test class's module scope; a test that wants to pin **guard-only** suppression must assert class-creation acceptance only, not finalize / schema build. See the split tests under "Eleven Relay-collision tests" for the contract distinction.

**Why the guard belongs to this contract.** Without it, the annotation-only override path silently breaks `relay.Node`-shaped types in a way that points the consumer at the wrong code surface. The guard is the smallest correct UX surface for the override behavior and fits inside the same `__init_subclass__` pass the collection itself lives in.

### Decision 7a — Converter validation bypass

Adding annotation-only scalar names to `consumer_authored_fields` skips the entire scalar branch of `django_strawberry_framework/types/base.py::_build_annotations` before `convert_field_output(...)` — and through it `convert_scalar(...)` — is called. `convert_scalar` (`django_strawberry_framework/types/converters.py::convert_scalar`) carries several validation and side-effect responsibilities beyond annotation synthesis:

1. **Unsupported field-type rejection.** Walks `type(field).__mro__` looking for a `SCALAR_MAP` match; raises `ConfigurationError` if nothing matches. The error message names [`Meta.exclude`][glossary-metaexclude] as the consumer recourse.
2. **Grouped-choices rejection.** `convert_choices_to_enum` raises `ConfigurationError("Meta.fields contains grouped-choices field ...")` when the Django field's `choices=` is the grouped `[(label, [(value, label), ...])]` shape.
3. **`ArrayField` shape validation.** Rejects nested `ArrayField` (recursive `base_field` walk hits a second `ArrayField`) and outer `choices=` declarations with `ConfigurationError`.
4. **`HStoreField` routing.** Sentinel-guarded branch that returns `strawberry.scalars.JSON` only when `django.contrib.postgres.fields` imports successfully; rejects outer `choices=` with `ConfigurationError`.
5. **`null=True` widening.** `T | None` wrapping for nullable scalar columns.
6. **Choice-enum registration.** Successful `convert_choices_to_enum` calls register the generated enum into `registry._enums[(model, field_name)]` so two `DjangoType`s reading the same choice column share one cached enum (the [`Choice enum generation`][glossary-choice-enum-generation] contract).

Under the short-circuit, **every one of these validations and side effects is bypassed for an annotation-overridden field.** The contract:

- Consumer annotation overrides are **authoritative**. The consumer takes responsibility for the runtime shape of the annotation; the package does not pre-validate that the override is compatible with the underlying Django column.
- Unsupported scalar fields can be annotation-overridden as a recourse parallel to `Meta.exclude`: a consumer can drop the field via `Meta.exclude` or write a custom annotation. This aligns with the relation path: annotation-only relation overrides bypass `convert_relation` and its pending-relation routing.
- Grouped-choices, nested-`ArrayField`, and outer-`choices`-on-postgres-fields rejections **do not fire** when the consumer overrides those columns. The consumer's annotation replaces the package's auto-conversion entirely.
- Choice-enum registration **does not fire** when the consumer overrides a `choices=`-bearing column. The shared `(model, field_name)` enum cache is not populated for that field. A second `DjangoType` on the same model that selects the same column without an override triggers fresh enum generation; the overriding type contributes nothing to the cache.
- `null=True` widening is the consumer's responsibility — a consumer who writes `description: int` against a nullable `IntegerField(null=True)` gets the literal `int` annotation, not `int | None`. The consumer is expected to write `description: int | None` themselves.

**What this means for [`docs/GLOSSARY.md`][glossary].** The [`Scalar field conversion`][glossary-scalar-field-conversion] entry lists both recourses for an unsupported scalar — `Meta.exclude` and annotation-only override (Slice 5).

**Mandatory tests pinning the bypass.** The four Slice 1 tests under the "Converter-bypass regressions" sub-checklist: unsupported field type, grouped choices, nested `ArrayField`, and cross-type enum cache (`test_annotation_override_does_not_populate_shared_enum_cache_for_co_resident_types`). Additional regressions for `HStoreField` choices, outer `ArrayField` choices, and the null-widening path are optional; the four listed cover the contract surface.

## Implementation plan

Slice 1 holds the code and its tests (collection + definition field + guard); Slices 2-5 are placement, docstring, version, and docs.

| Slice | Files | Tests | Notes |
|---|---|---|---|
| 1 | `types/base.py`, `types/definition.py`, `tests/types/test_definition_order.py`, `tests/types/test_converters.py` (the nested-`ArrayField` bypass test), `examples/fakeshop/test_query/test_scalars_api.py` (the live SDL test) | 19 tests: 4 core overrides (one live) + 4 converter-bypass + 11 Relay collision (5 reject + 6 accept) | The Relay guard and the four module-scope helpers (`_NODEID_STRING_RE`, `_has_node_id_marker`, `_id_annotation_is_relay_node_id`, `_is_relay_shaped`). |
| 2 | `tests/types/test_base.py` | None | No override-contract copy outside the matrix home. |
| 3 | `types/base.py` | None | Documentation only — the `_consumer_assigned_fields` docstring. |
| 4 | `__init__.py`, `tests/base/test_init.py` | None | One version bump for the whole `0.0.6` release. |
| 5 | `docs/GLOSSARY.md`, `KANBAN.md`, `CHANGELOG.md` | None | The `Scalar field conversion` recourse wording and the metadata-route limitation in the `Scalar field override semantics` body and the `Changed` CHANGELOG entry. |

## Edge cases and constraints

- **`Meta.fields = "__all__"` interaction.** When [`Meta.fields`][glossary-metafields] is unspecified or `"__all__"`, every concrete Django field is selected. A consumer annotation that shadows any one of them — relation or scalar — lands in `consumer_authored_fields` under this card. With [`Meta.exclude`][glossary-metaexclude], a name listed in `Meta.exclude` is filtered out of `fields` upstream of the collection, so the `field.name in consumer_annotations` check never sees it. (Verify by reading `django_strawberry_framework/types/base.py::_select_fields`.)
- **`relay.Node` `id` collision.** Pinned as a behavior contract, not a flagged edge case — see [Decision 7](#decision-7--relay-id-override-collision). A consumer who writes `id: <non-NodeID-type>`, a non-NodeID stringified annotation (e.g. `id: "MissingType"`), a NodeID-lookalike string (e.g. `id: "NotNodeID[int]"`, rejected by the token-shaped regex), or assigns any `id = <StrawberryField>` on a Relay-Node-shaped type raises [`ConfigurationError`][glossary-configurationerror] at `__init_subclass__` time. The annotation-side errors point at `relay.NodeID[...]` as the supported escape hatch; the assigned-side error points at three alternatives — `relay.NodeID[<pk_type>]`, `@classmethod resolve_id`, and the **resolver-backed sibling-field workaround** (`@strawberry.field(description="…") def display_id(self) -> strawberry.ID: return str(self.pk)`; the metadata-only `display_id: ID = strawberry.field(description="…")` form is NOT recommended because it would build but fail at query time). The guard is narrow: `id: relay.NodeID[int]` passes in direct form, in resolved-string end-to-end form, in unresolved-NodeID-shaped-string guard-only form, and alongside any number of unresolvable sibling annotations (detection reads only `cls.__annotations__["id"]`, so no other annotation can influence the verdict); non-`id` consumer scalar overrides on Relay-Node-shaped types pass (no `Node.id` collision); inherited `id` annotations on a subclass slip past the guard at class-creation time AND are silently handled by `_build_annotations`'s pk-suppression branch — Strawberry applies the Relay-supplied `id: GlobalID!` and `resolve_id_attr()` falls back to `"pk"`, so schema construction succeeds (the guard does not walk the MRO). The eleven Slice 1 Relay-collision tests pin the reject + accept + inheritance-handled paths: `test_consumer_id_annotation_on_relay_node_type_raises`, `test_consumer_id_annotation_on_direct_relay_node_subclass_raises`, `test_consumer_id_assigned_strawberry_field_on_relay_node_type_raises`, `test_consumer_id_unresolved_non_nodeid_string_on_relay_node_type_raises`, `test_consumer_id_typo_lookalike_nodeid_string_on_relay_node_type_raises`, `test_consumer_id_relay_nodeid_annotation_on_relay_node_type_is_accepted`, `test_consumer_id_resolved_string_relay_nodeid_annotation_on_relay_node_type_is_accepted_end_to_end`, `test_consumer_id_unresolved_nodeid_shaped_string_on_relay_node_type_passes_guard_only`, `test_consumer_id_resolved_relay_nodeid_with_unresolved_sibling_annotation_is_accepted`, `test_consumer_non_id_scalar_override_on_relay_node_type_is_accepted`, and `test_inherited_id_annotation_on_relay_node_subclass_is_handled_by_pk_suppression`.
- **Choice-enum fields.** Pinned as a behavior contract, not a flagged edge case — see [Decision 7a](#decision-7a--converter-validation-bypass). A consumer annotation `status: MyEnum` on a `choices=`-bearing column bypasses `convert_choices_to_enum` entirely; `registry.get_enum(model, field_name)` returns `None` for the overridden field. Two `DjangoType`s on the same model where one overrides and one does not get the fresh enum from the non-overriding type alone. `test_annotation_override_of_grouped_choices_field_is_allowed` pins the **single-type** bypass; `test_annotation_override_does_not_populate_shared_enum_cache_for_co_resident_types` pins the **cross-type** cache behavior — the non-overriding co-resident type populates the cache, the overriding type's GraphQL surface uses the consumer's annotation.
- **Inheritance.** Inherited consumer annotations on a base `DjangoType` subclass are NOT in the subclass's own `cls.__annotations__` (Python returns only the class's own annotations dict). A subclass that inherits from a base with `description: int` and adds `class Meta: model = Category` sees `cls.__annotations__ = {}` at `__init_subclass__` time and the collection misses the inherited override. This matches the relation-annotation behavior (which also walks `cls.__annotations__` and also misses inherited annotations). It is not a bug; it is the same "per-subclass declaration" contract as relations, and Slice 5 documents it in the [`Scalar field override semantics`][glossary-scalar-field-override-semantics] entry.
- **Mutable-default-argument hazard.** `consumer_authored_fields: frozenset[str] = frozenset()` is the default-argument shape in `_build_annotations`'s signature. `frozenset()` is immutable, so the default is safe. The `consumer_annotated_scalar_fields: frozenset[str] = frozenset()` field on `DjangoTypeDefinition` uses the same pattern — `DjangoTypeDefinition` is a `@dataclass`, where mutable defaults must use `field(default_factory=...)`, but `frozenset()` is immutable so the bare default is allowed. The `frozenset()` literal matches the siblings.
- **`finalize_django_types()` interaction.** Annotation-only overrides land in `cls.__annotations__` at `__init_subclass__` time (before finalize). [`finalize_django_types`][glossary-finalize-django-types]`()` does not re-read `cls.__annotations__` for the override-routing decision — it only resolves pending relations and decorates with `strawberry.type(...)`. The Strawberry decorator reads `cls.__annotations__` to build `__strawberry_definition__.fields`; the consumer's annotation is what is in the dict, so the resulting Strawberry field type matches the consumer's override. This is the end-to-end contract `examples/fakeshop/test_query/test_scalars_api.py::test_override_specimen_consumer_field_overrides_resolve_over_http` pins.

## Test strategy

The package-tier tests live in `tests/types/test_definition_order.py` — the host for the override-contract matrix (per [Decision 5](#decision-5--test-placement-and-the-skipped-tests-fate)). Two exceptions: `test_annotation_override_of_arrayfield_with_nested_array_is_allowed` lives in `tests/types/test_converters.py` beside the `_FakeArrayField` fixture (fixture locality), and the end-to-end SDL test lives at the live tier because a real query observes it. `test_annotation_override_does_not_populate_shared_enum_cache_for_co_resident_types` lives in `tests/types/test_definition_order.py` — mandatory, because it exercises override-vs-non-override cross-talk rather than converter-internal behavior.

The Slice 1 test cluster has 19 tests total.

**Four core override tests** — cover the annotation-only scalar override path:

- `test_annotation_only_scalar_field_override_wins_over_synthesized` — **pre-finalize annotation contents.** Assert `cls.__annotations__[field_name]` is the consumer's type immediately after `__init_subclass__`.
- `test_annotation_only_scalar_override_populates_definition_metadata` — **`consumer_*_fields` introspection.** Assert the `consumer_annotated_scalar_fields` set on `DjangoTypeDefinition` contains exactly the overridden name, that `consumer_authored_fields` contains it (transitively, via the union), and that `consumer_assigned_scalar_fields` does NOT (because the override is annotation-only).
- `test_annotation_only_scalar_override_does_not_emit_synthesized_annotation` — **`_build_annotations` skip.** Assert the synthesized annotations dict — the first element of `_build_annotations`'s return tuple — does NOT contain the override-field key. Whitebox-but-stable: the synthesized dict is what feeds the post-merge line at `django_strawberry_framework/types/base.py::DjangoType.__init_subclass__ #"cls.__annotations__ = {**synthesized, **consumer_annotations}"`, so its shape is the contract under test.
- `examples/fakeshop/test_query/test_scalars_api.py::test_override_specimen_consumer_field_overrides_resolve_over_http` — **end-to-end over `/graphql/`.** Resolve the fakeshop `OverriddenScalarSpecimenType` override columns and introspect the SDL; the annotation-only `quantity` override surfaces as the consumer's nullable `Float`.

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
- `test_consumer_id_unresolved_nodeid_shaped_string_on_relay_node_type_passes_guard_only` — `id: "relay.NodeID[int]"` stringified form with `relay` NOT importable from the class's resolution scope; assert ONLY that class creation succeeds (the regex accepts by shape alone). Pins the guard-only-suppression contract; finalize / schema build are explicitly NOT asserted because Strawberry's downstream resolution operates against the same module globals and may still fail there.
- `test_consumer_id_resolved_relay_nodeid_with_unresolved_sibling_annotation_is_accepted` — a directly-resolved `id: relay.NodeID[int]` alongside a forward-referenced sibling annotation passes the guard. Pins that the verdict on `id` is independent of every other annotation on the class.
- `test_consumer_non_id_scalar_override_on_relay_node_type_is_accepted` — a non-`id` consumer override on a Relay-Node-shaped type passes the guard (custom-pk / non-collision accept path; recipe: `description: int`).
- `test_inherited_id_annotation_on_relay_node_subclass_is_handled_by_pk_suppression` — an inherited `id: int` annotation on a Relay-Node-shaped subclass does NOT trigger the guard at class-creation time, AND `strawberry.Schema(...)` succeeds because `_build_annotations`'s pk-suppression branch strips the synthesized `id` and the post-merge reassignment leaves the child without an `id` annotation; Strawberry applies the Relay-supplied `id: GlobalID!` and `resolve_id_attr()` falls back to `"pk"`.

Slices 2-5 carry no tests of their own. Coverage stays at 100%: the definition field is exercised by Slice 1 tests; the collection branch in `__init_subclass__` is exercised by every override test in `tests/types/test_definition_order.py`; the Relay collision guard is exercised by all eleven Relay tests (five reject + six accept); `_id_annotation_is_relay_node_id`'s resolved-object accept arm is hit by `test_consumer_id_relay_nodeid_annotation_on_relay_node_type_is_accepted` and `test_consumer_id_resolved_relay_nodeid_with_unresolved_sibling_annotation_is_accepted`, its resolved-object reject arm by `test_consumer_id_annotation_on_relay_node_type_raises`, its string accept arm by `test_consumer_id_resolved_string_relay_nodeid_annotation_on_relay_node_type_is_accepted_end_to_end` and `test_consumer_id_unresolved_nodeid_shaped_string_on_relay_node_type_passes_guard_only`, and its string reject arm by `test_consumer_id_unresolved_non_nodeid_string_on_relay_node_type_raises` and `test_consumer_id_typo_lookalike_nodeid_string_on_relay_node_type_raises`; and the converter-bypass paths are exercised by the four bypass tests (unsupported / grouped-choices / nested-array / cross-type-cache).

## Definition of done

- [ ] Every Slice 1 / Slice 2 / Slice 3 checkbox in [Slice checklist](#slice-checklist) is checked.
- [ ] No `@pytest.mark.skip` override placeholder exists; the annotation-only scalar cell is a running test per [Decision 5](#decision-5--test-placement-and-the-skipped-tests-fate).
- [ ] All 19 Slice 1 tests pass (four core overrides + four converter-bypass + eleven Relay-collision tests — five reject + six accept). Test placement: the override-contract host (`tests/types/test_definition_order.py`) for three core overrides, the Relay-collision tests, and the cross-type cache test; the converter test host (`tests/types/test_converters.py`) for the nested-`ArrayField` bypass test; `examples/fakeshop/test_query/test_scalars_api.py` for the end-to-end SDL test.
- [ ] `uv run pytest` passes locally with 100% package coverage.
- [ ] `uv run ruff check .` passes.
- [ ] `uv run ruff format --check .` passes.
- [ ] `git diff --check` passes.
- [ ] [`docs/GLOSSARY.md`][glossary]'s [`Scalar field override semantics`][glossary-scalar-field-override-semantics] entry reads `shipped (0.0.6)` (Slice 5).
- [ ] `docs/GLOSSARY.md`'s [`Scalar field conversion`][glossary-scalar-field-conversion] entry names annotation override as a parallel recourse to [`Meta.exclude`][glossary-metaexclude] for unsupported scalar fields (Slice 5).
- [ ] `docs/GLOSSARY.md`'s `Scalar field override semantics` body names the metadata-route limitation: field-level GraphQL metadata on the Relay-supplied `id` is not configurable in `0.0.6`; the documented workaround is a **resolver-backed sibling field** (`@strawberry.field(description="…") def display_id(self) -> strawberry.ID: return str(self.pk)`) carrying the metadata AND a value source, with the Relay-supplied `id` left undecorated. A metadata-only sibling without a resolver would build but fail at query time and is NOT recommended (Slice 5).
- [ ] `KANBAN.md` carries `DONE-019-0.0.6` in the Done section.
- [ ] `CHANGELOG.md` carries the five entries from Slice 5 (`Added` annotation-only, `Added` introspection field, `Changed` converter-bypass, `Added` Relay annotation-collision guard, `Changed` assigned-id rejection on Relay-Node-shaped types — the last with the sibling-field workaround acknowledgment) under `## [0.0.6] - 2026-05-19`.
- [ ] `__version__` and its `tests/base/test_init.py` pin at `0.0.6`.
- [ ] No public top-level symbol and no `Meta.*` key belong to this spec.

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
