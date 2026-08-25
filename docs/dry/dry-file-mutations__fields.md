# DRY review: `django_strawberry_framework/mutations/fields.py`

Status: verified

## System trace

`django_strawberry_framework/mutations/fields.py` is the write-side root-field factory module of the framework ([spec-036][spec-036]). It defines [`DjangoMutationField`][mutations-fields], the write-side counterpart to [`DjangoConnectionField`][types-connection] and [`DjangoNodeField`][relay] ([spec-036][spec-036] Decision 5). Assigned as class attributes on an `@strawberry.type class Mutation`, it converts declarative mutation classes into Strawberry root mutation fields with forward-referenced lazy return types, GraphQL argument signatures, server-side Relay GlobalID coercion, lifecycle target validation, completion-spanning atomicity marking, and runtime sync/async execution dispatch.

1. **Write-Side Field Synthesis & No-Class-Attribute-Annotation Architecture:**
   - [`DjangoMutationField`][mutations-fields]: Root-field factory exposing a [`DjangoMutation`][mutations-sets], [`DjangoFormMutation`][forms-sets], [`DjangoModelFormMutation`][forms-sets], or [`SerializerMutation`][rest-framework-sets] on the GraphQL `Mutation` type ([spec-036][spec-036] Decision 5). Unlike read-side query factories that read consumer class annotations at import time, write mutations generate `<Name>Payload` return types during `finalize_django_types()` phase 2.5 (after `@strawberry.type class Mutation` annotations evaluate). `DjangoMutationField` allows consumers to write `create_item = DjangoMutationField(CreateItem)` with no class attribute annotation, typing the field via a `strawberry.lazy` forward reference on the synthesized resolver's return annotation resolved at schema build time ([spec-036][spec-036] Decisions 5, 7).
   - [`build_lazy_field_signature`][mutations-fields]: Builds the `(inspect.Signature, __annotations__)` pair required for fixed root-field dispatchers whose return types only materialize at phase 2.5. Injects `root` (`inspect.Parameter.POSITIONAL_OR_KEYWORD`, default=`None`), `info` (`inspect.Parameter.KEYWORD_ONLY`, annotation=`strawberry.types.Info`), keyword-only GraphQL arguments, and lazy return type annotation. Promoted to shared field-factory machinery ([spec-040][spec-040] Helper-reuse D12, P1, P2) and reused by auth fixed-field factories ([`auth/mutations.py`][auth-mutations], [`auth/queries.py`][auth-queries]).
   - [`_lazy_ref`][mutations-fields]: Helper returning `Annotated[<type_name>, strawberry.lazy(<module_path>)]` for schema-build lazy forward resolution. Parameterized by `module_path` so `data:` arguments can resolve to per-flavor input namespaces (`mutations.inputs`, `forms.inputs`, `rest_framework.inputs`), while payload return types resolve to `mutations.inputs` ([`INPUTS_MODULE_PATH`][mutations-inputs]). Reused across write and auth field factories ([spec-040][spec-040] D12).
   - [`_synthesized_mutation_signature`][mutations-fields]: Builds the operation-specific argument signature and return annotation:
     - `create`: `data: <Model>Input!` (non-null, no default).
     - `update`: `id: ID!` (raw `strawberry.ID` string) + `data: <Model>PartialInput!`.
     - `delete`: `id: ID!` only.
     - `form`: `data: <Form>Input!` only (no `id` parameter).
     - Return: `_lazy_ref(f"{mutation_cls.__name__}Payload", INPUTS_MODULE_PATH)`.

2. **Construction-Time Target Guard & Lifecycle Validation:**
   - [`_validate_mutation_target`][mutations-fields]: Validates the target mutation class eagerly at the construction line ([spec-036][spec-036] Decision 5, [spec-038][spec-038] Decision 5). Rejects non-classes, non-mutation classes, abstract base classes without a concrete `_mutation_meta`, unregistered subclass declarations that merely inherit a parent's `Meta` without declaring their own, and stale declarations created prior to the most recent `registry.clear()`. Raises [`ConfigurationError`][exceptions] with clear remediation instructions naming `DjangoMutationField`.
   - [`_has_mutation_protocol`][mutations-fields]: Duck-typed protocol predicate checking for `_mutation_meta`, callable `resolve_sync` / `resolve_async`, callable `input_type_name`, and `input_module_path`. Duck typing permits model mutations, model form mutations, plain form mutations, and serializer mutations to share `DjangoMutationField` without inheritance coupling or circular import cycles.
   - [`_is_registered_mutation_target`][mutations-fields]: Verifies whether the mutation class is currently registered in active phase-2.5 declaration ledgers (`iter_mutations()` from [`mutations/sets.py`][mutations-sets] or `iter_form_mutations()` from [`forms/sets.py`][forms-sets]).

3. **Runtime Async-vs-Sync Resolution Dispatch:**
   - Inside [`DjangoMutationField`][mutations-fields], the generated resolver closure `_resolve(root, info, **kwargs)` dispatches dynamically at call time via `in_async_context()` ([spec-036][spec-036] Decision 8). Calls `mutation_cls.resolve_async(info, **call_kwargs)` under async execution (e.g. `await schema.execute()`) or `mutation_cls.resolve_sync(info, **call_kwargs)` under sync execution (`schema.execute_sync()`), allowing a single field factory output to operate uniformly across sync and async contexts.
   - Gating `takes_id = mutation_cls._mutation_meta.operation != "form"` ensures plain form mutations (which accept only `data:`) do not receive an unneeded `id` kwarg.

4. **Transaction Atomicity Marker:**
   - [`MUTATION_CLASS_MARKER`][mutations-fields]: Module constant `"_django_mutation_cls"` stamped onto `_resolve`. Read by [`schema.py::DjangoMutationExecutionContext`][schema] via Strawberry field extensions to identify top-level mutation fields and wrap execution in a completion-spanning database transaction ([spec-036][spec-036] / [spec-046][spec-046] mutation atomicity).

Connected behavior examined:
- [`django_strawberry_framework/mutations/inputs.py`][mutations-inputs]: Input type classes, `INPUTS_MODULE_PATH`, `FieldError`, and payload wrappers.
- [`django_strawberry_framework/mutations/sets.py`][mutations-sets]: `DjangoMutation` class definition, `_mutation_meta`, `iter_mutations()`, `make_declaration_registry()`.
- [`django_strawberry_framework/mutations/resolvers.py`][mutations-resolvers]: Sync and async write pipelines (`resolve_mutation_sync`, `resolve_mutation_async`), Relay GlobalID decoding (`coerce_lookup_id`).
- [`django_strawberry_framework/forms/sets.py`][forms-sets]: `DjangoFormMutation`, `DjangoModelFormMutation`, `iter_form_mutations()`.
- [`django_strawberry_framework/rest_framework/sets.py`][rest-framework-sets]: `SerializerMutation` extending `DjangoMutation`.
- [`django_strawberry_framework/auth/mutations.py`][auth-mutations]: Session auth mutation factories reusing `_lazy_ref` and `build_lazy_field_signature`.
- [`django_strawberry_framework/auth/queries.py`][auth-queries]: `current_user` query factory reusing `_lazy_ref` and `build_lazy_field_signature`.
- [`django_strawberry_framework/schema.py`][schema]: `DjangoMutationExecutionContext` reading `MUTATION_CLASS_MARKER`.
- [`django_strawberry_framework/registry.py`][registry]: Global registry managing lifecycle clearing hooks for declaration ledgers.
- [`django_strawberry_framework/relay.py`][relay]: `DjangoNodeField` / `DjangoNodesField` server-side GlobalID decode precedents and `_resolve` async dispatch.
- [`django_strawberry_framework/connection.py`][types-connection]: `DjangoConnectionField` read-side factory parity.
- [`tests/mutations/test_fields.py`][test-mutations-fields]: Comprehensive test suite covering argument signatures, lazy payload resolution, sync/async dispatch, target validation, and multi-flavor generalization.

## Verification

Static analysis and symbol inventory (`docs/dry/export_dry_review.py check --target django_strawberry_framework/mutations/fields.py --include-constants`):
- Parsed 1 target file, 309 lines, 1 constant ([`MUTATION_CLASS_MARKER`][mutations-fields]), and 7 functions ([`_validate_mutation_target`][mutations-fields], [`_has_mutation_protocol`][mutations-fields], [`_is_registered_mutation_target`][mutations-fields], [`_lazy_ref`][mutations-fields], [`build_lazy_field_signature`][mutations-fields], [`_synthesized_mutation_signature`][mutations-fields], [`DjangoMutationField`][mutations-fields]).
- Verified reverse references across `django_strawberry_framework/schema.py`, `django_strawberry_framework/auth/mutations.py`, `django_strawberry_framework/auth/queries.py`, and test suites.

### Mandatory 5-axis duplication probing matrix

1. **Cross-flavor policy mirroring:**
   The framework provides multiple mutation flavors: model mutations ([`mutations/sets.py`][mutations-sets]), form mutations ([`forms/sets.py`][forms-sets]), serializer mutations ([`rest_framework/sets.py`][rest-framework-sets]), and session auth mutations ([`auth/mutations.py`][auth-mutations]).
   - **Unified Mutation Field Factory:** Rather than authoring separate `DjangoFormMutationField` or `SerializerMutationField` factories, [`DjangoMutationField`][mutations-fields] serves as the single field factory across all four mutation flavors. It duck-types the target class via [`_has_mutation_protocol`][mutations-fields] and delegates input type naming to `mutation_cls.input_type_name(meta)` and input module routing to `mutation_cls.input_module_path`.
   - **Shared Signature Machinery:** The lazy signature builder [`build_lazy_field_signature`][mutations-fields] and forward-reference creator [`_lazy_ref`][mutations-fields] were promoted to shared field-factory utilities ([spec-040][spec-040] Helper-reuse D12), eliminating duplicated `inspect.Signature` synthesis and `strawberry.lazy` annotation generation in [`auth/mutations.py`][auth-mutations] and [`auth/queries.py`][auth-queries].
   - **Single-Sited Error Payload Envelope:** All mutation flavors return the uniform payload envelope (`{ node/result, errors: [FieldError] }`) defined in [`mutations/inputs.py`][mutations-inputs].

2. **Sync and async twins:**
   Zero duplicate field factories. Dynamic runtime dispatch is encapsulated within [`DjangoMutationField`][mutations-fields]:
   - Inside `_resolve`, `in_async_context()` selects between `mutation_cls.resolve_async(info, **call_kwargs)` and `mutation_cls.resolve_sync(info, **call_kwargs)`.
   - This eliminates the need for parallel `DjangoAsyncMutationField` classes or static inspection of consumer resolvers.
   - Sibling auth fields in [`auth/mutations.py`][auth-mutations] (`_make_auth_field`) mirror this exact runtime dispatch pattern.

3. **Derived rather than repeated knowledge:**
   All field metadata is derived directly from the declarative mutation target:
   - GraphQL arguments (`id`, `data`) and their nullability are derived from `mutation_cls._mutation_meta.operation` (`create`, `update`, `delete`, `form`).
   - Input type names and modules are derived from `mutation_cls.input_type_name(meta)` and `mutation_cls.input_module_path`.
   - Return payload names are derived deterministically as `f"{mutation_cls.__name__}Payload"` in [`INPUTS_MODULE_PATH`][mutations-inputs].
   - Schema execution transaction boundaries derive their mutation class directly from the [`MUTATION_CLASS_MARKER`][mutations-fields] stamped onto `_resolve`, eliminating parallel field-to-class lookup tables in `schema.py`.

4. **Inverse and round-trip pairs:**
   - **Declaration Registration & Construction Guard Pairing:** Concrete mutations register with declaration ledgers upon class definition (`iter_mutations()` / `iter_form_mutations()`). [`_validate_mutation_target`][mutations-fields] and [`_is_registered_mutation_target`][mutations-fields] verify active registration; calling `registry.clear()` drains declarations, and any subsequent attempt to construct a field from a stale class is immediately rejected.
   - **Forward Reference & Schema Materialization Pairing:** Field definition constructs `_lazy_ref` annotations at import time; phase 2.5 finalization materializes the target classes in global module dictionaries; Strawberry schema construction resolves lazy references into schema types.
   - **Atomicity Marker & Execution Context Pairing:** [`DjangoMutationField`][mutations-fields] stamps [`MUTATION_CLASS_MARKER`][mutations-fields] on `_resolve`, and [`schema.py::DjangoMutationExecutionContext`][schema] reads it to open completion-spanning transactions.

5. **Contracts restated in another medium:**
   The `DjangoMutationField` contract is codified across:
   - Code: [`django_strawberry_framework/mutations/fields.py`][mutations-fields], [`django_strawberry_framework/mutations/inputs.py`][mutations-inputs], [`django_strawberry_framework/mutations/sets.py`][mutations-sets], [`django_strawberry_framework/mutations/resolvers.py`][mutations-resolvers], [`django_strawberry_framework/forms/sets.py`][forms-sets], [`django_strawberry_framework/rest_framework/sets.py`][rest-framework-sets], [`django_strawberry_framework/auth/mutations.py`][auth-mutations], [`django_strawberry_framework/schema.py`][schema], [`django_strawberry_framework/__init__.py`][django-strawberry-framework-init];
   - Specifications: [`docs/SPECS/spec-036-mutations-0_0_11.md`][spec-036] (Decisions 5, 7, 8, 14), [`docs/SPECS/spec-038-form_mutations-0_0_12.md`][spec-038] (Decision 5), [`docs/SPECS/spec-039-serializer_mutations-0_0_13.md`][spec-039] (Decision 5), [`docs/SPECS/spec-040-auth_mutations-0_0_13.md`][spec-040] (Helper-reuse D12, P1, P2), [`docs/SPECS/spec-041-channels_router-0_0_14.md`][spec-041];
   - Test suites: [`tests/mutations/test_fields.py`][test-mutations-fields], [`tests/forms/test_resolvers.py`][test-forms-resolvers], [`tests/rest_framework/test_resolvers.py`][test-rest-framework-resolvers], [`tests/auth/test_mutations.py`][test-auth-mutations], [`examples/fakeshop/test_query/test_products_api.py`][test-products-api];
   - Standing documentation: [`docs/README.md`][readme], [`docs/GLOSSARY.md`][glossary], [`docs/TREE.md`][tree], [`docs/COOKBOOK.md`][cookbook], [`TODAY.md`][today], [`LIFECYCLE.html`][lifecycle].

### The single-edit-site test

- **Posited change 1 (Adding a new mutation operation type, e.g. `upsert`):** Introduce an `upsert` operation requiring optional `id: ID` and `data: <Model>Input!`.
  - *Sites that must move:* Exactly 1 site in field signature generation: [`django_strawberry_framework/mutations/fields.py::_synthesized_mutation_signature`][mutations-fields].
  - *Site count:* 1.
- **Posited change 2 (Modifying root-field lazy signature parameter conventions):** Update parameter injection conventions (e.g. adding trace context) for lazy-typed fields across write and auth subsystems.
  - *Sites that must move:* Exactly 1 site at root owner: [`django_strawberry_framework/mutations/fields.py::build_lazy_field_signature`][mutations-fields]. All mutation and auth field factories inherit the update automatically.
  - *Site count:* 1.
- **Posited change 3 (Modifying mutation execution transaction marker name):** Change the marker attribute name read by `DjangoMutationExecutionContext`.
  - *Sites that must move:* Exactly 1 site: [`django_strawberry_framework/mutations/fields.py::MUTATION_CLASS_MARKER`][mutations-fields] (imported directly by `schema.py`).
  - *Site count:* 1.
- **Posited change 4 (Adding a new declarative mutation flavor, e.g. `DjangoBulkMutation`):** Introduce a new bulk write mutation class implementing the duck-typed mutation protocol.
  - *Sites that must move:* 0 sites in `mutations/fields.py`. The duck-typed protocol check in [`_has_mutation_protocol`][mutations-fields] accepts any class carrying `_mutation_meta`, `resolve_sync`, `resolve_async`, `input_type_name`, and `input_module_path`.
  - *Site count:* 0.

### Rejected candidates

1. **Creating separate field factories for each mutation flavor (`DjangoFormMutationField`, `SerializerMutationField`):**
   - Disproved per [spec-038][spec-038] Decision 5 and [spec-039][spec-039] Decision 5. `DjangoMutationField`'s duck-typed protocol inspection seamlessly accommodates model mutations, model form mutations, plain form mutations, and serializer mutations without duplication.
2. **Duplicating lazy signature builders in `auth/mutations.py`:**
   - Disproved per [spec-040][spec-040] Helper-reuse D12. Promoting [`build_lazy_field_signature`][mutations-fields] and [`_lazy_ref`][mutations-fields] to shared utilities guarantees signature and forward-ref consistency across the entire framework.
3. **Hardcoding `input_module_path` in `_synthesized_mutation_signature`:**
   - Disproved per [spec-038][spec-038] Decision 5. Form and serializer mutations materialize inputs in `forms.inputs` and `rest_framework.inputs` respectively, while payloads materialize in `mutations.inputs`. Deriving the input module path via `mutation_cls.input_module_path` maintains clean namespace separation.
4. **Inspecting consumer resolvers at field construction time for sync vs async dispatch:**
   - Disproved per [spec-036][spec-036] Decision 8. Mutation execution pipelines are package-owned without a consumer-provided resolver parameter. Runtime dispatch via `in_async_context()` inside `_resolve` ensures clean, single-sited execution for both sync and async query runners.

## Opportunities

None — `django_strawberry_framework/mutations/fields.py` is fully consolidated, single-sited, and adheres strictly to repository DRY principles. Shared field-building machinery is cleanly exported, target validation is duck-typed and lifecycle-aware, and runtime execution dispatch is unified.

## Judgment

Zero-edit review. `django_strawberry_framework/mutations/fields.py` contains zero duplicate logic or unowned policy. All 5 axes of the mandatory duplication matrix are verified and discharged. Single-edit-site counts are 1 across all posited changes.

## Implementation (Worker 1)

No tracked code changes needed. The target file is verified clean and fully consolidated at root owners. Completeness verified with `docs/dry/export_dry_review.py check --target django_strawberry_framework/mutations/fields.py --review docs/dry/dry-file-mutations__fields.md --include-constants`. Setting `Status: fix-implemented`.

## Independent verification (Worker 2)

Independent verification confirms Worker 1's DRY analysis of `django_strawberry_framework/mutations/fields.py` is accurate, thorough, and fully discharged.

### Behavior and Boundary Challenges

1. **Shared Field-Building Machinery (`build_lazy_field_signature` and `_lazy_ref`):**
   - Verified that [`build_lazy_field_signature`][mutations-fields] and [`_lazy_ref`][mutations-fields] are consumed directly by [`auth/mutations.py`][auth-mutations] (`login_mutation`, `logout_mutation`) and [`auth/queries.py`][auth-queries] (`current_user`).
   - Challenged whether signature synthesis could drift between write fields and auth fields. It cannot: all lazy root fields inject standard `root`, `info`, keyword-only arguments, and lazy return type annotations through this single builder.

2. **Duck-Typed Mutation Protocol Parity:**
   - Challenged whether `DjangoMutationField` creates hidden coupling across flavors. Verified that duck-typing via [`_has_mutation_protocol`][mutations-fields] avoids any circular import dependencies with `forms/` or `rest_framework/` while allowing [`DjangoMutation`][mutations-sets], [`DjangoFormMutation`][forms-sets], [`DjangoModelFormMutation`][forms-sets], and [`SerializerMutation`][rest-framework-sets] to share field synthesis cleanly.

3. **Runtime Async Dispatch (`in_async_context`):**
   - Verified that write operations have no consumer `resolver=` parameter to inspect at construction time, so dynamic call-time selection via `in_async_context()` inside `_resolve` is the exact correct design. All 13 test cases in [`tests/mutations/test_fields.py`][test-mutations-fields] pass cleanly under both sync and async query execution.

4. **Atomicity Marker Boundary:**
   - Verified that [`MUTATION_CLASS_MARKER`][mutations-fields] cleanly connects field construction in `mutations/fields.py` to transaction demarcation in [`schema.py::DjangoMutationExecutionContext`][schema] without maintaining redundant field registries.

### Probing Matrix & Single-Edit-Site Confirmation

- All 5 axes of the duplication probing matrix are independently re-checked and confirmed fully discharged.
- Single-edit-site counts are confirmed at 1 or 0 across all evaluated changes.
- AST and symbol coverage verified via `export_dry_review.py check` (8 definitions covered).

Status upgraded to `Status: verified`.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[lifecycle]: ../../LIFECYCLE.html
[today]: ../../TODAY.md

<!-- docs/ -->
[cookbook]: ../COOKBOOK.md
[glossary]: ../GLOSSARY.md
[readme]: ../README.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[spec-036]: ../SPECS/spec-036-mutations-0_0_11.md
[spec-038]: ../SPECS/spec-038-form_mutations-0_0_12.md
[spec-039]: ../SPECS/spec-039-serializer_mutations-0_0_13.md
[spec-040]: ../SPECS/spec-040-auth_mutations-0_0_13.md
[spec-041]: ../SPECS/spec-041-channels_router-0_0_14.md
[spec-046]: ../SPECS/spec-046-channels_auth_hardening-0_0_14.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[auth-mutations]: ../../django_strawberry_framework/auth/mutations.py
[auth-queries]: ../../django_strawberry_framework/auth/queries.py
[django-strawberry-framework-init]: ../../django_strawberry_framework/__init__.py
[exceptions]: ../../django_strawberry_framework/exceptions.py
[forms-sets]: ../../django_strawberry_framework/forms/sets.py
[mutations-fields]: ../../django_strawberry_framework/mutations/fields.py
[mutations-init]: ../../django_strawberry_framework/mutations/__init__.py
[mutations-inputs]: ../../django_strawberry_framework/mutations/inputs.py
[mutations-permissions]: ../../django_strawberry_framework/mutations/permissions.py
[mutations-resolvers]: ../../django_strawberry_framework/mutations/resolvers.py
[mutations-sets]: ../../django_strawberry_framework/mutations/sets.py
[registry]: ../../django_strawberry_framework/registry.py
[relay]: ../../django_strawberry_framework/relay.py
[rest-framework-sets]: ../../django_strawberry_framework/rest_framework/sets.py
[schema]: ../../django_strawberry_framework/schema.py
[types-connection]: ../../django_strawberry_framework/connection.py
[types-finalizer]: ../../django_strawberry_framework/types/finalizer.py

<!-- tests/ -->
[test-auth-mutations]: ../../tests/auth/test_mutations.py
[test-forms-resolvers]: ../../tests/forms/test_resolvers.py
[test-mutations-fields]: ../../tests/mutations/test_fields.py
[test-mutations-resolvers]: ../../tests/mutations/test_resolvers.py
[test-mutations-sets]: ../../tests/mutations/test_sets.py
[test-rest-framework-resolvers]: ../../tests/rest_framework/test_resolvers.py

<!-- examples/ -->
[test-products-api]: ../../examples/fakeshop/test_query/test_products_api.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->

