# DRY review: `django_strawberry_framework/forms/inputs.py`

Status: verified

## System trace

`django_strawberry_framework/forms/inputs.py` provides the form-derived `@strawberry.input` generation substrate for Django `Form` and `ModelForm` classes ([spec-038][spec-038] Decisions 7, 8).

1. **Architecture & Key Space Separation (spec-038 Decision 7):**
   - The module is pure, finalizer-free machinery: given a Django `Form` / `ModelForm` class, an operation kind (`CREATE`, `PARTIAL`, or `FORM`), and an effective field set (post `Meta.fields` / `Meta.exclude`), it dynamically constructs the `<FormClass>Input` (create) and `<FormClass>PartialInput` (update) `@strawberry.input` dataclasses from declared `form_class.base_fields`.
   - **No Instantiation Required:** Form fields are discovered directly from `form_class.base_fields` via [`get_form_fields`][forms-inputs] without instantiating the form. Forms whose constructors require runtime kwargs (e.g. `request`, `user`, tenant context) retain a stable, request-independent schema-time field shape.
   - **Strict Key Space Separation:** `forms.Field` and `models.Field` key spaces remain strictly separate. Where a `ModelForm` field has a backing model column, [`_model_column_for`][forms-inputs] resolves the concrete `models.Field` and routes annotation through [`model_column_input_annotation`][mutations-inputs], guaranteeing symmetric wire contracts with read-side `DjangoType` outputs. Column-less fields (plain `Form` fields, custom `ModelForm` extra fields, or fields reusing reverse relation / GenericForeignKey names) route through the model-less table in [`convert_form_field`][forms-converter].
   - **Module Global Namespace Materialization:** Generated input classes are registered as real module globals of `django_strawberry_framework.forms.inputs` via [`materialize_form_input_class`][forms-inputs] to support `strawberry.lazy("django_strawberry_framework.forms.inputs")` forward-reference resolution across GraphQL schema definitions.

2. **Target Symbols and Responsibilities:**
   - [`INPUTS_MODULE_PATH`][forms-inputs]: Pinned constant (`"django_strawberry_framework.forms.inputs"`) referenced by `strawberry.lazy(...)` forward references for the form input namespace, isolated from mutation and serializer input namespaces.
   - [`FORM`][forms-inputs]: Fixed operation-kind sentinel (`"form"`) for non-model `DjangoFormMutation` operations, providing a well-defined shape identity key `(form_class, "form", effective_set)`.
   - [`CREATE_SHAPED_KINDS`][forms-inputs]: Frozenset constant (`frozenset({CREATE, FORM})`) grouping all create-shaped operation kinds that enforce declared field requiredness rather than partial widening.
   - [`materialize_form_input_class`][forms-inputs]: Public wrapper delegating to the materializer produced by [`make_input_namespace`][utils-inputs], setting input classes into module globals with idempotency and duplicate-name collision detection.
   - [`clear_form_input_namespace`][forms-inputs]: Ledger reset helper registered as a pre-bind clear via [`register_subsystem_clear`][registry] (`owner="forms.input_namespace"`, `before_bind=True`), parking class objects in `module.__dict__` for safe lazy reference resolution during schema rebuilds.
   - [`get_form_fields`][forms-inputs]: Class-level declared field discovery reading `dict(form_class.base_fields)` with zero instantiation.
   - [`_form_field_basis`][forms-inputs]: Validates and copies the field basis mapping, ensuring string keys and `forms.Field` instances with typed diagnostics.
   - [`normalize_form_field_basis`][forms-inputs]: Validation wrapper ensuring mutation hooks return non-`None` mappings of `forms.Field` instances.
   - [`resolve_effective_form_fields`][forms-inputs]: Delegates to [`resolve_effective_fields`][utils-inputs] to compute effective field subsets after applying `Meta.fields` / `Meta.exclude`, rejecting unknown names and empty effective sets.
   - [`form_input_type_name`][forms-inputs]: Derives deterministic input class names delegating to [`name_set_input_type_name`][utils-inputs], mapping full shapes to canonical `<FormClass>Input` / `<FormClass>PartialInput` and narrowed shapes to deterministic shape-derived token names.
   - [`_model_column_for`][forms-inputs]: Resolves backing model columns for `ModelForm` fields via `model._meta.get_field(name)`, filtering out reverse relations (`ForeignObjectRel`), `GenericForeignKey`, and `GenericRelation` to ensure non-column fields remain on the model-less path.
   - [`_model_less_relation_annotation`][forms-inputs]: Maps column-less `ModelChoiceField` / `ModelMultipleChoiceField` instances to `(python_attr, annotation, related_model)` via [`annotate_queryset_relation`][mutations-inputs], failing loud if `queryset` is `None` at class definition time.
   - [`_simple_triple`][forms-inputs]: Helper standardizing `(name, graphql_camel_name(name), annotation, kind)` quadruples for non-relation form fields.
   - [`_field_triple_and_spec`][forms-inputs]: Resolves a single form field into `(python_attr, base_annotation, InputFieldSpec, required)` using unified [`form_field_required`][forms-converter], delegating column-backed fields to [`model_column_input_annotation`][mutations-inputs] and column-less fields to [`convert_form_field`][forms-converter].
   - [`_guard_input_attr_collisions`][forms-inputs]: Fail-loud validation checking for Python `input_attr` and GraphQL `graphql_name` collisions across generated fields using [`iter_input_field_collisions`][utils-inputs].
   - [`build_form_input_class`][forms-inputs]: Constructs a single `@strawberry.input` dataclass from effective form fields, applying partial optionality widening via [`optional_input_field`][utils-inputs] and minting the class via [`build_strawberry_input_class`][utils-inputs].
   - [`_required_form_field_names`][forms-inputs]: Computes the set of required form field names using [`form_field_required`][forms-converter] with backing column inspection.
   - [`guard_create_required_fields`][forms-inputs]: Fail-loud guard verifying that create narrowings (`Meta.fields` / `Meta.exclude`) do not drop declared required form fields, delegating set difference logic to [`guard_dropped_required`][utils-inputs].
   - [`guard_partial_required_column_less_fields`][forms-inputs]: Fail-loud guard verifying that partial narrowings do not drop required column-less fields (which cannot be reconstructed from database model instances), delegating set difference logic to [`guard_dropped_required`][utils-inputs].
   - [`build_form_inputs`][forms-inputs]: Main public builder producing both create and partial input classes along with their respective [`InputFieldSpec`][utils-inputs] lists, enforcing the create-required narrowing guard when `guard_required=True`.

Connected behavior examined:
- [`django_strawberry_framework/forms/converter.py`][forms-converter]: Form field conversion registry (`convert_form_field`, `form_field_required`, `FILE`, `RELATION_SINGLE`, `RELATION_MULTI`, `SCALAR`).
- [`django_strawberry_framework/forms/sets.py`][forms-sets]: Base mutation classes (`DjangoFormMutation`, `DjangoModelFormMutation`) consuming `build_form_inputs`, `materialize_form_input_class`, `get_form_fields`, and `form_input_type_name`.
- [`django_strawberry_framework/forms/resolvers.py`][forms-resolvers]: Mutation execution pipeline consuming `InputFieldSpec` records to deserialize GraphQL arguments into `form.data` and `form.files`.
- [`django_strawberry_framework/mutations/inputs.py`][mutations-inputs]: Shared write-side input machinery (`CREATE`, `PARTIAL`, `annotate_queryset_relation`, `model_column_input_annotation`, `model_column_write_kind`).
- [`django_strawberry_framework/rest_framework/inputs.py`][rest-framework-inputs]: Sibling serializer input generator sharing the unified input substrate in `utils/inputs.py`.
- [`django_strawberry_framework/utils/inputs.py`][utils-inputs]: Canonical root owner of `InputFieldSpec`, `build_strawberry_input_class`, `guard_dropped_required`, `iter_input_field_collisions`, `make_input_namespace`, `name_set_input_type_name`, `optional_input_field`, and `resolve_effective_fields`.
- [`django_strawberry_framework/utils/relations.py`][utils-relations]: Relation inspection helpers (`is_forward_concrete_relation`, `is_forward_many_to_many`).
- [`django_strawberry_framework/utils/strings.py`][utils-strings]: String casing utilities (`graphql_camel_name`).
- [`django_strawberry_framework/registry.py`][registry]: Central registry lifecycle (`register_subsystem_clear`, `registry`).
- [`tests/forms/test_inputs.py`][test-forms-inputs]: Comprehensive test suite covering form field discovery, input class generation, relation mapping, narrowing guards, and namespace materialization.
- [`tests/forms/test_sets.py`][test-forms-sets]: Integration tests for form mutation sets.
- [`tests/forms/test_resolvers.py`][test-forms-resolvers]: Tests for resolver argument decoding against `InputFieldSpec`.
- [`tests/forms/test_converter.py`][test-forms-converter]: Tests for form field conversion and requiredness.

## Verification

Static analysis and inventory (`export_dry_review.py check --target django_strawberry_framework/forms/inputs.py --review docs/dry/dry-file-forms__inputs.md --include-constants`):
- Parsed 1 target file, 758 lines, 20 target definitions (3 constants, 17 functions).
- Verified reverse references across `django_strawberry_framework/forms/sets.py`, `tests/forms/test_inputs.py`, `tests/forms/test_sets.py`, `tests/forms/test_converter.py`, and `tests/mutations/test_inputs.py`.

### Mandatory 5-axis duplication probing matrix

1. **Cross-flavor policy mirroring:**
   - **Write Subsystem Input Generation:** The framework generates GraphQL inputs across three mutation flavors: model mutations ([`mutations/inputs.py`][mutations-inputs]), form mutations ([`forms/inputs.py`][forms-inputs]), and DRF serializer mutations ([`rest_framework/inputs.py`][rest-framework-inputs]).
   - **Unified Substrate:** All three write flavors leverage the shared input primitives in [`django_strawberry_framework/utils/inputs.py`][utils-inputs]:
     - Namespace lifecycle management is single-sited in [`make_input_namespace`][utils-inputs];
     - Dataclass construction is single-sited in [`build_strawberry_input_class`][utils-inputs];
     - Required field drop detection is single-sited in [`guard_dropped_required`][utils-inputs];
     - Field attribute and GraphQL name collision auditing is single-sited in [`iter_input_field_collisions`][utils-inputs];
     - Field narrowing and error normalization are single-sited in [`resolve_effective_fields`][utils-inputs];
     - Optional field widening (`T | None`, `UNSET` default, `name=` alias) is single-sited in [`optional_input_field`][utils-inputs];
     - Reverse map specifications are standardized via [`InputFieldSpec`][utils-inputs].
   - **Strict Key Space Boundaries:** `forms.Field`, `serializers.Field`, and `models.Field` hierarchies remain cleanly partitioned. In `forms/inputs.py`, backing model columns are resolved via [`_model_column_for`][forms-inputs] before dispatching to [`model_column_input_annotation`][mutations-inputs], ensuring that model-backed form fields produce identical GraphQL types and enum definitions as read-side `DjangoType` fields, while column-less form fields route to [`convert_form_field`][forms-converter].
2. **Sync and async twins:**
   - Zero duplication. `forms/inputs.py` executes exclusively during schema construction and mutation binding (generating `@strawberry.input` classes and reverse-map specs). It contains no execution logic or sync/async branching.
   - Synchronous and asynchronous runtime mutation executions are completely isolated in [`django_strawberry_framework/forms/resolvers.py`][forms-resolvers] (`resolve_form_mutation_sync` and `resolve_form_mutation_async`).
3. **Derived rather than repeated knowledge:**
   - **Declared Field Discovery:** [`get_form_fields`][forms-inputs] derives the field basis directly from `form_class.base_fields` without instantiating the form, ensuring that forms requiring constructor kwargs (`request`, `user`) have deterministic, request-independent schema representations.
   - **Deterministic Shape Naming:** [`form_input_type_name`][forms-inputs] derives input type names via [`name_set_input_type_name`][utils-inputs] using `(form_class.__name__, is_partial, effective_field_names, full_field_names)`. Full shapes receive `<FormClass>Input` / `<FormClass>PartialInput`; narrowed shapes receive deterministic hash-appended tokens.
   - **Single Requiredness Authority:** Requiredness for both column-backed and column-less form fields derives from [`form_field_required`][forms-converter], preventing drift between input creation, narrowing guards, and conversion.
   - **Backing Column Derivation:** [`_model_column_for`][forms-inputs] derives model columns via Django's `model._meta.get_field(name)`, explicitly excluding reverse relations (`ForeignObjectRel`), `GenericForeignKey`, and `GenericRelation` to prevent accidental emission of relation IDs on non-model fields.
   - **Dropped Required Fields:** [`guard_create_required_fields`][forms-inputs] and [`guard_partial_required_column_less_fields`][forms-inputs] derive dropped required fields via [`guard_dropped_required`][utils-inputs].
4. **Inverse and round-trip pairs:**
   - Schema generation and resolver decoding form an exact round-trip pair:
     - `forms/inputs.py` assigns decode kinds ([`SCALAR`][forms-converter], [`RELATION_SINGLE`][forms-converter], [`RELATION_MULTI`][forms-converter], [`FILE`][forms-converter]) and emits [`InputFieldSpec`][utils-inputs] instances carrying `input_attr`, `graphql_name`, `target_name`, `kind`, and `related_model`.
     - `forms/resolvers.py` unpacks client arguments against these `InputFieldSpec` records, reconstructing `form.data` and `form.files` (resolving Relay GlobalIDs or raw PKs against `spec.related_model`, handling file uploads, and formatting scalar inputs).
   - Parked globals lifecycle round-trip:
     - [`materialize_form_input_class`][forms-inputs] registers generated input classes as module globals in `django_strawberry_framework.forms.inputs`.
     - [`clear_form_input_namespace`][forms-inputs] resets the internal ledger on `registry.clear()` while preserving parked classes in `__dict__`, ensuring lazy GraphQL references remain resolvable until overwritten during rebuild.
5. **Contracts restated in another medium:**
   - The form input generation contract is consistently codified across:
     - Production code: [`django_strawberry_framework/forms/inputs.py`][forms-inputs], [`django_strawberry_framework/forms/converter.py`][forms-converter], [`django_strawberry_framework/forms/sets.py`][forms-sets], [`django_strawberry_framework/forms/resolvers.py`][forms-resolvers], [`django_strawberry_framework/utils/inputs.py`][utils-inputs], [`django_strawberry_framework/mutations/inputs.py`][mutations-inputs];
     - Specifications: [`docs/SPECS/spec-038-form_mutations-0_0_12.md`][spec-038] (Decisions 7, 8), [`docs/SPECS/spec-036-mutation_sets-0_0_11.md`][spec-036], [`docs/SPECS/spec-039-drf_serializer_mutations-0_0_13.md`][spec-039] (Decisions 2, 7);
     - Test suites: [`tests/forms/test_inputs.py`][test-forms-inputs], [`tests/forms/test_sets.py`][test-forms-sets], [`tests/forms/test_resolvers.py`][test-forms-resolvers], [`tests/forms/test_converter.py`][test-forms-converter], [`tests/mutations/test_inputs.py`][test-mutations-inputs];
     - Standing documentation: [`docs/README.md`][readme], [`docs/GLOSSARY.md`][glossary], [`docs/TREE.md`][tree], [`docs/COOKBOOK.md`][cookbook].

### The single-edit-site test

- **Posited change 1 (Modifying input class naming convention or shape hashing for narrowed inputs):** Alter how shape tokens are derived for narrowed form inputs.
  - *Sites that must move:* Exactly 1 site at root owner: [`django_strawberry_framework/utils/inputs.py::name_set_input_type_name`][utils-inputs].
  - *Site count:* 1.
- **Posited change 2 (Altering required-field drop detection logic or error handling across write flavors):** Modify how dropped required fields are computed when applying `Meta.fields` / `Meta.exclude`.
  - *Sites that must move:* Exactly 1 site at root owner: [`django_strawberry_framework/utils/inputs.py::guard_dropped_required`][utils-inputs]. Both form and serializer create/partial guards immediately inherit the change.
  - *Site count:* 1.
- **Posited change 3 (Modifying collision detection mechanics for generated input attributes or GraphQL names):** Enhance collision auditing across input fields.
  - *Sites that must move:* Exactly 1 site at root owner: [`django_strawberry_framework/utils/inputs.py::iter_input_field_collisions`][utils-inputs].
  - *Site count:* 1.
- **Posited change 4 (Updating the module-dict materialization or clear lifecycle for input classes):** Change how generated input classes are parked or cleared in module namespaces.
  - *Sites that must move:* Exactly 1 site at root owner: [`django_strawberry_framework/utils/inputs.py::make_input_namespace`][utils-inputs].
  - *Site count:* 1.
- **Posited change 5 (Altering relation ID type resolution rules for column-less relation fields):** Change Relay-GlobalID-vs-raw-pk annotation mapping for unbacked `ModelChoiceField` instances.
  - *Sites that must move:* Exactly 1 site at root owner: [`django_strawberry_framework/mutations/inputs.py::annotate_queryset_relation`][mutations-inputs].
  - *Site count:* 1.
- **Posited change 6 (Modifying form field basis validation rules in `_form_field_basis`):** Adjust type validation or error formatting for `get_form_fields` basis mappings.
  - *Sites that must move:* Exactly 1 site: [`django_strawberry_framework/forms/inputs.py::_form_field_basis`][forms-inputs].
  - *Site count:* 1.

### Rejected candidates

1. **Merging `_model_column_for` with `mutations/inputs.py` model field resolution:**
   - Disproved per [spec-038][spec-038] Decision 7. `mutations/inputs.py` inspects Django models directly (`model._meta.get_field(name)`), whereas `forms/inputs.py` operates on `form_class` instances (which may be plain `Form` classes with no backing model). Furthermore, `forms/inputs.py` must filter out reverse relations (`ForeignObjectRel`), `GenericForeignKey`, and `GenericRelation` so that extra form fields reusing those names remain on the model-less path. Merging them would compromise key space separation and mis-route extra form fields.
2. **Unifying `_model_less_relation_annotation` with DRF serializer relation resolution:**
   - Disproved per [spec-038][spec-038] Decision 7 and [spec-039][spec-039] Decision 7. DRF serializer relation fields use `PrimaryKeyRelatedField` / `SlugRelatedField` and raise on missing primaries (spec-039 M3), whereas Django form fields (`ModelChoiceField`, `ModelMultipleChoiceField`) carry `queryset` directly and fall back to raw PK scalars when not in registry. Both delegate to [`mutations/inputs.py::annotate_queryset_relation`][mutations-inputs] for the Relay-vs-raw-pk annotation mapping.
3. **Inlining `make_input_namespace`, `build_strawberry_input_class`, or `resolve_effective_fields` in `forms/inputs.py`:**
   - Disproved per [spec-039][spec-039] Decision 2. All shared input generation, narrowing, collision detection, and namespace materialization mechanisms are consolidated at root owners in [`django_strawberry_framework/utils/inputs.py`][utils-inputs].

## Opportunities

None — `django_strawberry_framework/forms/inputs.py` is a clean, 758-line form input generation substrate. All shared namespace materialization, dataclass synthesis, collision auditing, field narrowing, optional widening, and dropped-required guarding mechanisms are consolidated at root owners in [`django_strawberry_framework/utils/inputs.py`][utils-inputs] and [`django_strawberry_framework/mutations/inputs.py`][mutations-inputs]. Form-specific declared field discovery, backing column resolution, and narrowing validation are precisely bounded.

## Judgment

Zero-edit review. `django_strawberry_framework/forms/inputs.py` contains zero duplicate policy or unowned invariants. All 5 axes of the mandatory duplication matrix are verified and discharged. Single-edit-site counts are 1 across all posited changes.

## Implementation (Worker 1)

No tracked code changes needed. The target file is verified clean and fully consolidated at root owners. Completeness verified with `docs/dry/export_dry_review.py check --target django_strawberry_framework/forms/inputs.py --review docs/dry/dry-file-forms__inputs.md --include-constants`. Setting `Status: fix-implemented`.

## Independent verification (Worker 2)

Independent review completed. Worker 1's findings are confirmed, all boundaries and equivalence claims were challenged and verified, and all 20 target definitions are fully accounted for.

### 1. Behavior Trace & Key Space Separation Verification
- **Uninstantiated Field Discovery:** Confirmed [`get_form_fields`][forms-inputs] reads `dict(form_class.base_fields)` directly without instantiating `form_class()`. Forms requiring constructor arguments (`request`, `user`, tenant context) retain deterministic, request-independent schema representations at build time ([spec-038][spec-038] Decision 7 P2).
- **Strict Key Space Separation:** Verified [`_model_column_for`][forms-inputs] inspects `model._meta.get_field(name)` and explicitly filters out reverse relations (`ForeignObjectRel`), `GenericForeignKey`, and `GenericRelation`. This boundary prevents extra form fields reusing model relation names (e.g. an extra `items = forms.CharField()`) from improperly routing to model relation ID converters. Backing concrete model columns route to [`model_column_input_annotation`][mutations-inputs] (ensuring symmetry with read-side `DjangoType` outputs), while column-less fields route through [`convert_form_field`][forms-converter] and [`_model_less_relation_annotation`][forms-inputs].
- **Model-less Relation Annotation:** Verified [`_model_less_relation_annotation`][forms-inputs] correctly leverages [`annotate_queryset_relation`][mutations-inputs]. In contrast to DRF serializer relation fields which fail loud when missing from registry ([spec-039][spec-039] M3), Django form relation fields fall back to raw PK scalars when no primary type is registered. A fail-loud `ConfigurationError` is raised if `field.queryset` is `None` at class definition time.
- **Unified Input Substrate:** Confirmed that shared input primitives are centralized at root owners in [`django_strawberry_framework/utils/inputs.py`][utils-inputs]:
  - Dataclass synthesis: [`build_strawberry_input_class`][utils-inputs];
  - Input type naming: [`name_set_input_type_name`][utils-inputs];
  - Optionality widening: [`optional_input_field`][utils-inputs];
  - Field narrowing and error formatting: [`resolve_effective_fields`][utils-inputs];
  - Input attribute / GraphQL name collision detection: [`iter_input_field_collisions`][utils-inputs];
  - Namespace lifecycle (materialization and clear): [`make_input_namespace`][utils-inputs];
  - Reverse map representation: [`InputFieldSpec`][utils-inputs].
- **Narrowing Guard Precision:**
  - [`guard_create_required_fields`][forms-inputs] delegates set-difference validation to [`guard_dropped_required`][utils-inputs].
  - [`guard_partial_required_column_less_fields`][forms-inputs] scopes required field detection strictly to column-less fields (`_model_column_for(...) is None`). Model-backed required fields are reconstructed from the database row via `model_to_dict` during update execution in [`forms/resolvers.py`][forms-resolvers], whereas column-less extra fields cannot be reconstructed and must not be silently dropped.

### 2. Probing Matrix & Single-Edit-Site Verification
- **5-Axis Probing Matrix:** All 5 axes verified and discharged (Cross-flavor policy mirroring, Sync/async twin separation, Derived knowledge, Inverse/round-trip pairs with resolver deserialization and parked globals lifecycle, and Multi-medium contract consistency).
- **Single-Edit-Site Counts:** All 6 posited changes verified to have exact site counts of 1 at their designated root owners.

### 3. Automated Validation & Test Suite
- Ran `uv run python docs/dry/export_dry_review.py check --target django_strawberry_framework/forms/inputs.py --review docs/dry/dry-file-forms__inputs.md --include-constants`: confirmed 20 target definitions covered with 0 errors.
- Ran test suite `uv run pytest tests/forms/ --no-cov`: all 221 tests passed cleanly.

Status updated to `verified`.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[cookbook]: ../COOKBOOK.md
[glossary]: ../GLOSSARY.md
[readme]: ../README.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[spec-036]: ../SPECS/spec-036-mutation_sets-0_0_11.md
[spec-038]: ../SPECS/spec-038-form_mutations-0_0_12.md
[spec-039]: ../SPECS/spec-039-drf_serializer_mutations-0_0_13.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[exceptions]: ../../django_strawberry_framework/exceptions.py
[filters-inputs]: ../../django_strawberry_framework/filters/inputs.py
[forms-converter]: ../../django_strawberry_framework/forms/converter.py
[forms-init]: ../../django_strawberry_framework/forms/__init__.py
[forms-inputs]: ../../django_strawberry_framework/forms/inputs.py
[forms-resolvers]: ../../django_strawberry_framework/forms/resolvers.py
[forms-sets]: ../../django_strawberry_framework/forms/sets.py
[mutations-inputs]: ../../django_strawberry_framework/mutations/inputs.py
[mutations-sets]: ../../django_strawberry_framework/mutations/sets.py
[orders-inputs]: ../../django_strawberry_framework/orders/inputs.py
[registry]: ../../django_strawberry_framework/registry.py
[rest-framework-inputs]: ../../django_strawberry_framework/rest_framework/inputs.py
[scalars]: ../../django_strawberry_framework/scalars.py
[types-converters]: ../../django_strawberry_framework/types/converters.py
[utils-converters]: ../../django_strawberry_framework/utils/converters.py
[utils-inputs]: ../../django_strawberry_framework/utils/inputs.py
[utils-relations]: ../../django_strawberry_framework/utils/relations.py
[utils-strings]: ../../django_strawberry_framework/utils/strings.py

<!-- tests/ -->
[test-forms-converter]: ../../tests/forms/test_converter.py
[test-forms-inputs]: ../../tests/forms/test_inputs.py
[test-forms-resolvers]: ../../tests/forms/test_resolvers.py
[test-forms-sets]: ../../tests/forms/test_sets.py
[test-mutations-inputs]: ../../tests/mutations/test_inputs.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
