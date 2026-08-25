# DRY review: `django_strawberry_framework/forms/converter.py`

Status: verified

## System trace

`django_strawberry_framework/forms/converter.py` provides the form-field-to-Strawberry-annotation conversion registry and input decode kind definitions for Django `forms.Field` instances ([spec-038][spec-038] Decisions 7, 8).

1. **Model-Less Conversion Domain & Key Space Separation:**
   - Plain `django.forms.Form` fields (such as `captcha`, `confirm_password`, or extra non-model form fields) have no backing Django model column and therefore cannot route through the read-side model converters in [`django_strawberry_framework/types/converters.py`][types-converters].
   - [`convert_form_field`][forms-converter] is the authoritative `forms.Field`-keyed conversion registry that translates unsupported and plain form fields into Strawberry GraphQL input annotations and decode kind constants.
   - For `ModelForm` fields with backing model columns, [`django_strawberry_framework/forms/inputs.py`][forms-inputs] routes resolution through the model column converters ([`convert_scalar`][types-converters], [`convert_choices_to_enum`][types-converters], [`model_column_input_annotation`][mutations-inputs]), preserving strict separation between the `forms.Field` and `models.Field` key spaces while enforcing symmetric wire contracts.

2. **Target Symbols and Responsibilities:**
   - [`FormFieldConversion`][forms-converter]: A lightweight value object subclassing [`FieldConversionBase`][utils-inputs], carrying the resolved `(annotation, kind, required)` triple for a converted form field.
   - [`form_field_required`][forms-converter]: The single authoritative source of requiredness logic for form fields across both column-backed and column-less paths. Handles the special case of `forms.NullBooleanField` where `field.required` is normally meaningless due to a no-op `validate()`, while GraphQL cannot express required-nullable inputs. Forces `required=False` for built-in `NullBooleanField` unless backed by a non-null model column or defined on a validating subclass.
   - [`_null_boolean_converter`][forms-converter]: Specialized converter for `NullBooleanField` instances that pairs the `bool` vs `bool | None` annotation directly with the evaluated `form_field_required` boolean.
   - [`_scalar_converter`][forms-converter]: Helper wrapping [`make_scalar_converter`][utils-converters] from `utils/converters.py`, binding [`FormFieldConversion`][forms-converter] and [`form_field_required`][forms-converter].
   - [`_kind_converter`][forms-converter]: Helper wrapping [`make_kind_converter`][utils-converters] from `utils/converters.py`, binding [`FormFieldConversion`][forms-converter] and [`form_field_required`][forms-converter] for non-scalar kinds.
   - [`_SCALAR_FORM_FIELDS`][forms-converter]: The static scalar mapping dictionary binding supported `forms.Field` types (`CharField`, `ChoiceField`, `IntegerField`, `FloatField`, `DecimalField`, `NullBooleanField`, `BooleanField`, `UUIDField`, `JSONField`, `DateTimeField`, `DateField`, `TimeField`) to their respective converter callables.
   - [`_bare_form_field`][forms-converter]: Precheck handler providing an exact-type special case for bare `forms.Field` -> `str`, returning [`MRO_CONTINUE`][utils-converters] for any subclass to ensure the MRO walk continues toward the scalar registry or the fail-loud fallthrough.
   - [`_CONVERT_RELATION_MULTI`][forms-converter]: Kind converter constant for multi-relation fields ([`RELATION_MULTI`][utils-inputs]).
   - [`_CONVERT_RELATION_SINGLE`][forms-converter]: Kind converter constant for single-relation fields ([`RELATION_SINGLE`][utils-inputs]).
   - [`_CONVERT_FILE`][forms-converter]: Kind converter constant for upload fields ([`FILE`][utils-inputs]).
   - [`_CONVERT_MULTIPLE_CHOICE`][forms-converter]: Kind converter constant for `MultipleChoiceField` mapping to `list[str]`.
   - [`convert_form_field`][forms-converter]: Main conversion entry point executing the shared [`convert_with_mro`][utils-converters] dispatch skeleton over ordered prechecks (`ModelMultipleChoiceField`, `ModelChoiceField`, `FileField`, `MultipleChoiceField`, bare `forms.Field`), the [`_SCALAR_FORM_FIELDS`][forms-converter] MRO walk, and the raising fallthrough, completed via [`finish_field_conversion`][utils-converters].
   - [`_unsupported_form_field`][forms-converter]: Error factory constructing a fail-loud [`ConfigurationError`][exceptions] when an unmapped `forms.Field` subclass with no supported ancestor is encountered, protected by [`_safe_type_name`][exceptions] and [`_safe_arg_repr`][exceptions].
   - Re-exported decode kind constants: [`SCALAR`][utils-inputs], [`RELATION_SINGLE`][utils-inputs], [`RELATION_MULTI`][utils-inputs], [`FILE`][utils-inputs] (re-exported from [`django_strawberry_framework/utils/inputs.py`][utils-inputs]).

Connected behavior examined:
- [`django_strawberry_framework/forms/inputs.py`][forms-inputs]: Consumes `convert_form_field` for column-less fields, `form_field_required` for required-field discovery and create/partial narrowing guards, and finalizes relation/file annotations at the input build site.
- [`django_strawberry_framework/forms/resolvers.py`][forms-resolvers]: Inspects decode kinds (`SCALAR`, `RELATION_SINGLE`, `RELATION_MULTI`, `FILE`) carried in `InputFieldSpec` records to unpack GraphQL arguments into `form.data` and `form.files`.
- [`django_strawberry_framework/forms/sets.py`][forms-sets]: Base classes `DjangoFormMutation` and `DjangoModelFormMutation`.
- [`django_strawberry_framework/forms/__init__.py`][forms-init]: Public export facade.
- [`django_strawberry_framework/utils/converters.py`][utils-converters]: Shared MRO dispatch engine (`convert_with_mro`, `finish_field_conversion`, `make_kind_converter`, `make_scalar_converter`, `MRO_CONTINUE`).
- [`django_strawberry_framework/utils/inputs.py`][utils-inputs]: Shared value object base (`FieldConversionBase`), reverse map record (`InputFieldSpec`), and decode kinds.
- [`django_strawberry_framework/rest_framework/serializer_converter.py`][rest-framework-serializer-converter]: Sibling converter for DRF serializer fields (`convert_serializer_field`).
- [`django_strawberry_framework/types/converters.py`][types-converters]: Read-side model field converter (`convert_scalar`, `convert_choices_to_enum`, `scalar_for_field`, `SCALAR_MAP`).
- [`tests/forms/test_converter.py`][test-forms-converter]: Unit tests verifying all scalar mappings, NullBoolean behaviors, MRO inheritance, precheck prioritization, and fail-loud unmapped field rejection.
- [`tests/forms/test_inputs.py`][test-forms-inputs]: Tests for form input generation, relation id type resolution, and narrowing guards.
- [`tests/utils/test_converters.py`][test-utils-converters]: Tests for the shared MRO converter dispatch engine.

## Verification

Static analysis and inventory (`export_dry_review.py check --target django_strawberry_framework/forms/converter.py --review docs/dry/dry-file-forms__converter.md --include-constants`):
- Parsed 1 target file, 293 lines, 13 target symbols (1 class, 7 functions, 5 constants), 4 re-exported decode kind constants.
- Verified reverse references across `django_strawberry_framework/forms/inputs.py`, `tests/forms/test_converter.py`, and `tests/forms/test_inputs.py`.

### Mandatory 5-axis duplication probing matrix

1. **Cross-flavor policy mirroring:**
   - The framework provides field conversion across multiple subsystems: forms ([`forms/converter.py`][forms-converter]), DRF serializers ([`rest_framework/serializer_converter.py`][rest-framework-serializer-converter]), models/types ([`types/converters.py`][types-converters]), and filter inputs ([`filters/inputs.py`][filters-inputs]).
   - **Unified dispatch skeleton:** The ordered-precheck -> MRO-walk -> raising-fallthrough control flow is fully unified in [`django_strawberry_framework/utils/converters.py`][utils-converters] ([`convert_with_mro`][utils-converters], [`finish_field_conversion`][utils-converters], [`make_scalar_converter`][utils-converters], [`make_kind_converter`][utils-converters]) per [spec-039][spec-039] Decision 4.
   - **Unified value object and decode kinds:** The return value contract [`FieldConversionBase`][utils-inputs] and the decode kinds ([`SCALAR`][utils-inputs], [`RELATION_SINGLE`][utils-inputs], [`RELATION_MULTI`][utils-inputs], [`FILE`][utils-inputs]) are single-sited in [`django_strawberry_framework/utils/inputs.py`][utils-inputs].
   - **Intentional key space separation:** `forms.Field`, `serializers.Field`, and `models.Field` key spaces remain strictly separate. Django forms have distinct inheritance structures (e.g. `NullBooleanField`, `FloatField` subclassing `IntegerField`, `JSONField` subclassing `CharField`). Merging key spaces would compromise type safety and fail-loud guarantees.
   - **Symmetric wire contracts:** When a form field is backed by a model column, `forms/inputs.py` delegates choice enum synthesis to [`convert_choices_to_enum`][types-converters], ensuring that form mutations and read `DjangoType` outputs use the identical GraphQL enum definition.
2. **Sync and async twins:**
   - Zero duplication. `forms/converter.py` operates exclusively at schema compilation time to inspect and map form field classes to GraphQL annotations and decode kinds. It contains no execution logic or sync/async branching.
   - Synchronous and asynchronous runtime execution pipelines are cleanly isolated in [`django_strawberry_framework/forms/resolvers.py`][forms-resolvers] (`resolve_form_mutation_sync` vs `resolve_form_mutation_async`).
3. **Derived rather than repeated knowledge:**
   - Requiredness calculation is single-sited in [`form_field_required`][forms-converter] and shared by [`convert_form_field`][forms-converter], [`_null_boolean_converter`][forms-converter], and [`forms/inputs.py`][forms-inputs] (for create/partial input generation and required field narrowing validation).
   - Form field subclasses (e.g. `EmailField`, `SlugField`, `URLField`, `RegexField`) automatically derive their mapping from `forms.CharField` via the MRO walk without redundant dictionary entries.
   - Explicit entries in [`_SCALAR_FORM_FIELDS`][forms-converter] for `FloatField`, `DecimalField`, `UUIDField`, and `JSONField` prevent accidental collapse into their parent classes (`IntegerField` and `CharField`).
4. **Inverse and round-trip pairs:**
   - Schema generation and resolver decoding form an exact round-trip pair:
     - `convert_form_field` categorizes form fields into decode kinds (`SCALAR`, `RELATION_SINGLE`, `RELATION_MULTI`, `FILE`).
     - `forms/inputs.py` records these into [`InputFieldSpec`][utils-inputs] instances.
     - `forms/resolvers.py` consumes these specs during mutation execution to deserialize GraphQL input arguments into the form's `data` dictionary and `files` dictionary.
5. **Contracts restated in another medium:**
   - The form field conversion contract is consistently codified across:
     - Production code: [`django_strawberry_framework/forms/converter.py`][forms-converter], [`django_strawberry_framework/forms/inputs.py`][forms-inputs], [`django_strawberry_framework/utils/converters.py`][utils-converters], [`django_strawberry_framework/utils/inputs.py`][utils-inputs];
     - Specifications: [`docs/SPECS/spec-038-form_mutations-0_0_12.md`][spec-038] (Decisions 7, 8), [`docs/SPECS/spec-039-drf_serializer_mutations-0_0_13.md`][spec-039] (Decision 4);
     - Test suites: [`tests/forms/test_converter.py`][test-forms-converter], [`tests/forms/test_inputs.py`][test-forms-inputs], [`tests/utils/test_converters.py`][test-utils-converters];
     - Standing documentation: [`docs/README.md`][readme], [`docs/GLOSSARY.md`][glossary], [`docs/TREE.md`][tree], [`docs/COOKBOOK.md`][cookbook].

### The single-edit-site test

- **Posited change 1 (Supporting a new Django built-in form field, e.g. `forms.ComboField` -> `str`):** Add `forms.ComboField` to the scalar table.
  - *Sites that must move:* Exactly 1 site: [`django_strawberry_framework/forms/converter.py`][forms-converter] in [`_SCALAR_FORM_FIELDS`][forms-converter].
  - *Site count:* 1.
- **Posited change 2 (Modifying form field requiredness rules, e.g. updating `NullBooleanField` policy):** Update the requiredness predicate.
  - *Sites that must move:* Exactly 1 site: [`django_strawberry_framework/forms/converter.py`][forms-converter] in [`form_field_required`][forms-converter]. Both `convert_form_field` and `forms/inputs.py` immediately reflect the change.
  - *Site count:* 1.
- **Posited change 3 (Modifying MRO dispatch or precheck handling mechanics across all write flavors):** Enhance or alter the fail-loud dispatch algorithm.
  - *Sites that must move:* Exactly 1 site at root owner: [`django_strawberry_framework/utils/converters.py`][utils-converters] in [`convert_with_mro`][utils-converters]. Both form and serializer converters inherit the change.
  - *Site count:* 1.
- **Posited change 4 (Introducing a new decode kind to the framework):** Add a new decode kind constant.
  - *Sites that must move:* Exactly 1 site at root owner: [`django_strawberry_framework/utils/inputs.py`][utils-inputs].
  - *Site count:* 1.

### Rejected candidates

1. **Merging `_SCALAR_FORM_FIELDS` with `types/converters.py::SCALAR_MAP` or DRF `_SERIALIZER_FIELD_CONVERTERS`:**
   - Disproved per [spec-038][spec-038] Decision 7 and [spec-039][spec-039] Decision 4. `django.forms.Field`, `rest_framework.serializers.Field`, and `django.db.models.Field` are completely distinct type hierarchies with unique inheritance chains and validation lifecycles. Merging them into a single polymorphic registry would introduce accidental cross-subsystem coupling, obscure ownership, and risk silent mis-mappings.
2. **Registering a catch-all `forms.Field -> str` in `_SCALAR_FORM_FIELDS`:**
   - Disproved per [spec-038][spec-038] Decision 7 and repository safety goals. A base `forms.Field -> str` registration would shadow the fail-loud fallthrough during the MRO walk, causing custom, unsupported form field classes to silently degrade to `String` rather than raising a clear [`ConfigurationError`][exceptions].
3. **Inlining MRO dispatch and converter factories in `forms/converter.py`:**
   - Disproved per [spec-039][spec-039] Decision 4. Dispatch control flow is already single-sited in [`django_strawberry_framework/utils/converters.py`][utils-converters] and shared with `rest_framework/serializer_converter.py` and `filters/inputs.py`.

## Opportunities

None — `django_strawberry_framework/forms/converter.py` is a clean, 293-line form field conversion registry. All shared dispatch algorithms and value object structures are consolidated at root owners in [`django_strawberry_framework/utils/converters.py`][utils-converters] and [`django_strawberry_framework/utils/inputs.py`][utils-inputs]. Form-specific requiredness, prechecks, scalar mappings, and fail-loud diagnostics are precisely bounded.

## Judgment

Zero-edit review. `django_strawberry_framework/forms/converter.py` contains zero duplicate policy or unowned invariants. All 5 axes of the mandatory duplication matrix are verified and discharged. Single-edit-site counts are 1 across all posited changes.

## Implementation (Worker 1)

No tracked code changes needed. The target file is verified clean and fully consolidated at root owners. Completeness verified with `docs/dry/export_dry_review.py check --target django_strawberry_framework/forms/converter.py --review docs/dry/dry-file-forms__converter.md --include-constants`. Setting `Status: fix-implemented`.

## Independent verification (Worker 2)

Independent verification conducted by Worker 2 for `django_strawberry_framework/forms/converter.py`.

### Independent behavioral trace and boundary challenge

1. **Model-Less Conversion Domain and Strict Key Space Separation:**
   - Evaluated the conversion mechanics in [`convert_form_field`][forms-converter]. For plain, model-less Django form fields (e.g. `captcha`, extra authentication fields, custom input fields), `convert_form_field` serves as the authoritative, standalone registry producing Strawberry GraphQL annotations and decode kind constants ([spec-038][spec-038] Decisions 7, 8).
   - Challenged key space boundaries against read-side model converters ([`django_strawberry_framework/types/converters.py`][types-converters]) and DRF serializer converters ([`django_strawberry_framework/rest_framework/serializer_converter.py`][rest-framework-serializer-converter]). Verified that key spaces are intentionally segregated: `django.forms.Field`, `rest_framework.serializers.Field`, and `django.db.models.Field` have fundamentally incompatible class hierarchies (e.g., `forms.FloatField` and `forms.DecimalField` subclass `forms.IntegerField`, whereas `models.DecimalField` subclasses `models.Field` directly; `forms.NullBooleanField` has unique no-op validation semantics). Merging these key spaces into a single registry would compromise type safety and violate fail-loud guarantees.
   - For `ModelForm` fields with backing model columns, verified that [`django_strawberry_framework/forms/inputs.py`][forms-inputs] routes column-backed choice enum resolution through [`convert_choices_to_enum`][types-converters], guaranteeing wire contract symmetry between read-side `DjangoType` outputs and write-side form mutations.

2. **MRO Dispatch Mechanics and Fail-Loud Fallthrough:**
   - Re-audited the dispatch engine in [`django_strawberry_framework/utils/converters.py`][utils-converters] ([`convert_with_mro`][utils-converters], [`finish_field_conversion`][utils-converters], [`make_scalar_converter`][utils-converters], [`make_kind_converter`][utils-converters]).
   - Verified that precheck order is strictly load-bearing: multi-relation fields ([`ModelMultipleChoiceField`][forms-converter]), single-relation fields ([`ModelChoiceField`][forms-converter]), upload fields ([`FileField`][forms-converter]), and multi-choice fields ([`MultipleChoiceField`][forms-converter]) all subclass `forms.ChoiceField` or `forms.Field`. Because `forms.ChoiceField` maps to `str` in the scalar registry, checking relation and file types in prechecks ensures they are correctly categorized with their respective decode kinds ([`RELATION_MULTI`][utils-inputs], [`RELATION_SINGLE`][utils-inputs], [`FILE`][utils-inputs]) before reaching the scalar MRO walk.
   - Verified exact-type handling for bare `forms.Field` via [`_bare_form_field`][forms-converter] returning [`MRO_CONTINUE`][utils-converters] for subclasses. Confirmed that custom, unregistered `forms.Field` subclasses hit [`_unsupported_form_field`][forms-converter] and fail loud with [`ConfigurationError`][exceptions] (safeguarded by [`_safe_type_name`][exceptions] and [`_safe_arg_repr`][exceptions]) rather than silently decaying to GraphQL `String`.

3. **Requiredness Logic and NullBooleanField Parity:**
   - Evaluated [`form_field_required`][forms-converter] across both column-backed and column-less pathways. Django's built-in `forms.NullBooleanField` has a no-op `validate()` method, rendering `field.required` meaningless for omission checks. Because GraphQL inputs cannot express required-nullable values, `form_field_required` forces `required=False` for built-in `NullBooleanField` instances unless backed by a non-null model column or defined on a validating subclass.
   - Confirmed that [`_null_boolean_converter`][forms-converter] pairs `bool` vs `bool | None` annotations with the evaluated `form_field_required` result, preventing Strawberry input constructor `TypeError` regressions.

4. **Duplication Probing Matrix and Single-Edit-Site Counts:**
   - Verified that all 5 axes of the mandatory duplication matrix are fully discharged with valid, verifiable rationales.
   - Re-evaluated posited change scenarios (supporting a new built-in form field, modifying requiredness rules, updating MRO dispatch mechanics, or introducing new decode kinds) and confirmed all site counts are exactly 1 at their authoritative root owners.

5. **Verification Tooling & Test Suite Run:**
   - Executed `uv run python docs/dry/export_dry_review.py check --target django_strawberry_framework/forms/converter.py --review docs/dry/dry-file-forms__converter.md --include-constants` — 13 target definitions and 0 missing topics confirmed (100% target coverage).
   - Ran `uv run pytest tests/forms/test_converter.py` — all 29 unit tests passed.
   - Ran full forms test suite `uv run pytest tests/forms/` — all 221 tests passed.

Conclusion: Verified. The review artifact is accurate, rigorous, and fully satisfies all repository DRY review standards.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[cookbook]: ../COOKBOOK.md
[glossary]: ../GLOSSARY.md
[readme]: ../README.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
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
[rest-framework-serializer-converter]: ../../django_strawberry_framework/rest_framework/serializer_converter.py
[types-converters]: ../../django_strawberry_framework/types/converters.py
[utils-converters]: ../../django_strawberry_framework/utils/converters.py
[utils-inputs]: ../../django_strawberry_framework/utils/inputs.py

<!-- tests/ -->
[test-forms-converter]: ../../tests/forms/test_converter.py
[test-forms-inputs]: ../../tests/forms/test_inputs.py
[test-utils-converters]: ../../tests/utils/test_converters.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
