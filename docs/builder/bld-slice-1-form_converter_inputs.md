# Build: Slice 1 — form-field → Strawberry input mapping + the form-derived input generator

Spec reference: `docs/SPECS/spec-038-form_mutations-0_0_12.md` (Slice 1 checklist lines 269-322; Decision 7 lines 1179-1430)
Status: final-accepted

## Plan (Worker 1)

This slice creates three net-new package modules — `forms/converter.py`, `forms/inputs.py`, `forms/__init__.py` — plus two package test files under `tests/forms/`. It touches **no** existing `.py` file. The two consumer-facing form-mutation bases, the metaclass, the `_validate_meta` / `Meta` validation, the resolver pipeline, and the finalizer bind are **Slice 2 / Slice 3** work — this slice ships only the converter registry, the reverse map, and the two `@strawberry.input` generators built from `form_class.base_fields`, all callable and unit-testable in isolation (the same posture `mutations/inputs.py` had at its own Slice 1: "callable and unit-testable in isolation; Slice 2 calls them from the bind", `mutations/inputs.py` module docstring).

Scope discipline for Worker 2: do **not** write `DjangoFormMutation` / `DjangoModelFormMutation`, a metaclass, `_validate_meta`, `bind_form_mutations()`, `get_form_kwargs`, or any resolver in this slice. Those are named in the spec for context but belong to later slices. Where this slice needs a "form base validates X at class creation" behavior (the `Meta.fields`/`Meta.exclude` normalization, the create-required guard), it ships that as a **pure function in `forms/inputs.py`** (or `forms/converter.py`) that Slice 2's `_validate_meta` override will call — mirroring how `mutations/inputs.py::editable_input_fields` carries the narrow+fail-loud logic that `mutations/sets.py` calls, rather than embedding it in the base.

### DRY analysis

**Existing patterns reused (cite file:line):**

- `django_strawberry_framework/utils/inputs.py:66-100` — `build_strawberry_input_class(name, field_specs)`: the single-sited `(python_attr, annotation, field_kwargs)`-triple → `@strawberry.input` constructor. `forms/inputs.py` builds its triples and calls this, exactly as `mutations/inputs.py:536` (`build_mutation_input`) and `orders/inputs.py` do. No hand-rolled `setattr`/`type(...)` in `forms/inputs.py`.
- `django_strawberry_framework/utils/inputs.py:103-139` — `materialize_generated_input_class(name, cls, *, module_path, family_label, ledger)`: the module-global pin + idempotent-dedupe + distinct-class collision raise. Its ledger gives the Decision 7 finalize-time `ConfigurationError` (two distinct shapes on one name; two different form classes sharing a `__name__`) **for free** — `forms/inputs.py` wraps it as a thin `materialize_form_input_class(name, cls)` with `module_path="django_strawberry_framework.forms.inputs"`, `family_label="DjangoFormMutation"`, and a module-level `_materialized_names: dict[str, type] = {}` ledger, byte-for-byte the wrapper shape `mutations/inputs.py:106-125` (`materialize_mutation_input_class`) uses.
- `django_strawberry_framework/utils/inputs.py:53-63` — `graphql_camel_name(name)`: `category_id` → `categoryId`. The form converter's relation branch and every scalar field's GraphQL alias route through this (same call site shape as `mutations/inputs.py:285`, `:492`, `:496`).
- `django_strawberry_framework/mutations/inputs.py:249-286` — `relation_input_annotation(field, *, related_primary_type)`: the FK/O2O → `<field>_id` + M2M → `list[<id>]` annotation strategy, **keyed on a `models.Field`** with the related model's primary `DjangoType` resolved via `registry.get(field.related_model)`. **Reused only for a `ModelForm` field that has a backing column** (Decision 7 lines 1208-1214): the converter resolves the column via `form_class._meta.model._meta.get_field(name)` and hands that `models.Field` to `relation_input_annotation`. This gives the Relay-`GlobalID`-vs-raw-pk id type and the `categoryId`/`category_id` naming identical to the read side and the `036` model-driven input — no parallel relation table.
- `django_strawberry_framework/types/converters.py:272-395` — `convert_scalar(field, type_name, *, force_nullable)` / `:249-269` `scalar_for_field(field)` / `:493-570` `convert_choices_to_enum(field, type_name)`: the read-side scalar/enum registry, **keyed on `models.Field` subclasses (MRO walk), not `forms.Field`** (Decision 7 lines 1208-1213). **Reused only for a `ModelForm` field with a backing column** — resolve the column and route it through `convert_scalar` (which itself delegates to `convert_choices_to_enum` when `field.choices` is set), so a `ChoiceField` over model `choices` resolves to the **same** generated enum the read `DjangoType` synthesizes (the symmetric wire contract). `force_nullable=False` suppresses the column's own null-widening so the form generator owns required-ness via `field.required` — same tri-state use as `mutations/inputs.py:301`.
- `django_strawberry_framework/scalars.py` (`Upload`, lines ~25-38) — the `0.0.11`/spec-037 `Upload` scalar. `forms.FileField` / `forms.ImageField` map to it, identical to the `mutations/inputs.py:493` file-column branch (`annotation = Upload`).
- `django_strawberry_framework/mutations/sets.py:271-299` — `_normalize_field_sequence(value, *, label)`: the bare-string / duplicate-name fail-loud normalizer for `Meta.fields` / `Meta.exclude`. The spec (Slice 1 sub-bullet 2, lines 310-312; Decision 7 lines 1350-1356) says "mirroring `036`'s `_normalize_field_sequence`". This function is **module-private to `mutations/sets.py`** and its messages name "DjangoMutation". See "New helpers justified" below for the resolution (do NOT import the private symbol cross-package, and do NOT duplicate its body).
- `django_strawberry_framework/types/relay.py:53` — `implements_relay_node(type_cls)`: used transitively inside `relation_input_annotation`; the converter never calls it directly (the reuse is through `relation_input_annotation`).
- Test-shape precedent: `tests/mutations/test_inputs.py:91` (`{f.python_name: f for f in input_cls.__strawberry_definition__.fields}`), `:94` (`_is_optional` via `strawberry.types.base.StrawberryOptional`), the `.default is UNSET` / `.graphql_name` assertions, and the `_make_relay_target` / `_make_non_relay_target` fixtures (`:258-290`). `tests/forms/test_converter.py` / `test_inputs.py` mirror these helpers verbatim in spirit — the converter/input tests resolve required-ness and id-type the same way.

**New helpers justified (single responsibility each):**

1. `forms/converter.py::convert_form_field(field)` — **the genuinely net-new machinery** (Decision 7 lines 1214-1219): the `forms.Field`-keyed → Strawberry-annotation + required-ness registry, *for the model-less case* (a plain `Form` field — `captcha`, `confirm_email` — has no Django column and so no read-side equivalent). Single responsibility: given a `forms.Field` instance, return `(annotation, required)`. This is **not** a parallel copy of the `convert_scalar` table: the `ModelForm`-backed-column path defers to `convert_scalar`/`relation_input_annotation` (above); only the no-column path uses this table. It is the explicit spec guard against the over-DRY-into-drift trap (lines 1217-1219, and the rejected Alternative at lines 1427-1429). Fail-loud dispatch detail under Implementation steps.
2. `forms/converter.py` reverse-map record — the per-generated-input-field `(input_attr, graphql_name) → (form_field_name, kind)` metadata, `kind ∈ {scalar, relation_single, relation_multi, file}` (Decision 7 lines 1239-1260, P1). Single responsibility: let Slice 3's resolver build a **form-field-keyed** payload (`{"category": pk}`, never `{"category_id": pk}`). A small frozen dataclass (e.g. `FormInputFieldSpec(input_attr, graphql_name, form_field_name, kind)`) — structurally a sibling of `utils/inputs.py:38-50`'s `GeneratedInputFieldSpec`, but with a `form_field_name` + `kind` instead of `django_source_path` (the form needs the form-field key and the decode kind, not an ORM lookup path). Worker 2 may instead reuse `GeneratedInputFieldSpec` if a clean mapping fits; see Implementation discretion items.
3. `forms/inputs.py::build_form_input_class(form_class, operation_kind, *, fields, exclude)` (name at W2 discretion) — builds **one** `@strawberry.input` from the form's declared fields for a given operation kind, returning `(input_cls, type_name, field_specs)`. Single responsibility: walk the effective form-field set, produce triples, call `build_strawberry_input_class`. The create vs partial requiredness split lives here.
4. `forms/inputs.py` form-shape identity / name helper — `form_input_type_name(form_class, operation_kind, effective_field_names, *, full_field_names)` mirroring `mutations/inputs.py:326-359` `mutation_input_type_name`: canonical `<FormClass.__name__>Input` / `<FormClass.__name__>PartialInput` for the full effective shape, deterministic shape-derived token name for a narrowing. The token scheme (`_pascalize_token`) is in `mutations/inputs.py:304-323` — see "Duplication risk avoided" for how to reuse rather than re-spell.
5. `forms/inputs.py::normalize_form_field_sequence(value, *, label)` — the form-flavored `_normalize_field_sequence`. Justified because the `036` original (`mutations/sets.py:271`) is module-private and its `ConfigurationError` text hard-codes "DjangoMutation"; the form flavor needs "DjangoFormMutation / DjangoModelFormMutation" wording and validation against `form_class.base_fields` (not model columns). This is a thin, intentional near-twin — its *body* (bare-string raise, duplicate raise) is small; the divergence is the message wording + the field-existence basis. Note for Worker 3: this is a **deliberate** near-copy the spec mandates ("mirroring `036`'s `_normalize_field_sequence`"); the alternative (extract a shared param-driven normalizer into `utils/`) is a viable consolidation but is **out of scope for this slice** — flag it for the integration pass, do not pre-extract here (the `036` symbol is private and only one other family would consume it, so the shared-extraction call is the integration pass's to make once both sites exist and are accepted).
6. `forms/inputs.py::get_form_fields(form_class)` / the discovery helper reading `form_class.base_fields` — Decision 7 lines 1398-1411 (P2). Single responsibility: return the `dict[str, forms.Field]` the input derives from, with **no instantiation** (so a kwarg-requiring form still has a discoverable shape). The spec names an overridable classmethod `get_form_fields(cls)` on the base (default `form_class.base_fields`); since the base does not exist until Slice 2, this slice ships the **discovery function** that Slice 2's base method will delegate to (default = read `base_fields`). Worker 2: a module-level `get_form_fields(form_class)` returning `dict(form_class.base_fields)` is the Slice-1 surface; do not add a base classmethod.

**Duplication risk avoided:**

- **A parallel scalar/enum table.** The naive implementation would re-list `CharField → str`, `ChoiceField → enum`, etc. for `ModelForm` fields, drifting from `types/converters.py`. Prevented by routing every `ModelForm`-backed-column field through `convert_scalar`/`convert_choices_to_enum`/`relation_input_annotation` (resolve the column via `model._meta.get_field(name)`); `convert_form_field`'s own table is reached **only** for fields with no backing column. The spec elevates this to a tested guard (the `ChoiceField`-over-model-`choices` symmetric-enum edge case, lines 1900-1903; the rejected Alternative, lines 1427-1429).
- **Re-spelling the injective token-name scheme.** `forms/inputs.py`'s narrowed-shape name must be injective per field set exactly as `mutation_input_type_name` is. Risk: copying the `_pascalize_token` + sorted-concat logic into `forms/inputs.py` (two copies of a subtle injectivity-critical algorithm). Prevention: `_pascalize_token` (`mutations/inputs.py:304`) is module-private but importable; reuse the token primitive. Worker 2 chooses between (a) importing `_pascalize_token` from `mutations.inputs` (a one-symbol cross-module reach — acceptable, the function is pure and named in the spec's name-scheme reference) or (b) flagging it for an integration-pass lift into `utils/inputs.py` alongside `graphql_camel_name`. Recommended for this slice: import `_pascalize_token` (and reuse `CREATE`/`PARTIAL` operation-kind constants from `mutations.inputs` if the create/partial split keys on them), and record the cross-module import in `### Notes for Worker 3` so the integration pass can decide whether to promote both into `utils/inputs.py`. Do NOT re-implement the token scheme.
- **Re-deriving the collision raise.** The two collision cases (distinct shapes on one name; two forms sharing `__name__`) must raise. Risk: writing a bespoke name-collision check in `forms/inputs.py`. Prevention: it comes free from `materialize_generated_input_class`'s ledger (lines 1343-1348) — the form flavor must route every materialization through `materialize_form_input_class` and never maintain its own name set.
- **`forms.Field` vs `models.Field` confusion.** The converter is keyed on `forms.Field`; the reused converters are keyed on `models.Field`. Risk: passing a `forms.Field` to `convert_scalar` (silent wrong dispatch / raise). Prevention: the `ModelForm`-overlap path **resolves the model column first** (`model._meta.get_field(name)` → a `models.Field`) before calling `convert_scalar`/`relation_input_annotation`; the `forms.Field` only ever reaches `convert_form_field`. Worker 2 keeps the two key spaces strictly separated.

### Implementation steps

Line numbers are pin-at-write-time navigational hints. Verify against current source before editing.

1. **`django_strawberry_framework/forms/__init__.py` (new).** A short module docstring describing the four-module `forms/` subpackage (mirroring `mutations/__init__.py`'s docstring shape) and naming which module each slice ships (`converter.py` + `inputs.py` this slice; `sets.py` Slice 2; `resolvers.py` Slice 3). **No re-exports of form-mutation bases this slice** (they do not exist yet) — `__all__` empty or omitted. Do **not** touch the package-root `django_strawberry_framework/__init__.py` (`__init__.py` exports are a Slice 2 concern; the Public-surface check must stay green). Pure docstring module → no review-worthy logic.

2. **`django_strawberry_framework/forms/converter.py` (new).** Module docstring framing the net-new-for-model-less-case posture (Decision 7 lines 1214-1219) and the fail-loud-no-catch-all contract (lines 1224-1237). Ship:
   - The reverse-map record type (helper #2) — a frozen dataclass carrying `input_attr`, `graphql_name`, `form_field_name`, `kind`. Pin the four `kind` string values as module constants (`SCALAR = "scalar"`, `RELATION_SINGLE = "relation_single"`, `RELATION_MULTI = "relation_multi"`, `FILE = "file"`) so the resolver (Slice 3) and the tests address one source of truth — avoid bare-string `kind` literals scattered across the converter.
   - `convert_form_field(field)` (helper #1): a registry keyed on `forms.Field` subclasses with a **fail-loud (raising) fallthrough default** and **no base-`forms.Field` catch-all** (Decision 7 lines 1224-1237, P2). Supported classes registered *individually* so subclasses map via MRO (`EmailField`/`SlugField`/`URLField`/`RegexField` under `CharField`); a bare `forms.Field` is an **explicit exact-type special case → `str`** (NOT a catch-all registration); an unregistered `forms.Field` subclass with no supported ancestor **raises `ConfigurationError`** naming the field and class (the graphene-django `convert_form_field` `ImproperlyConfigured` parity, raised as the package's own `ConfigurationError`). Mapping table (Decision 7 lines 1188-1200): text-like (`CharField`/`EmailField`/`SlugField`/`URLField`/`RegexField`/`ChoiceField`/bare `Field`) → `str`; `IntegerField` → `int`; `BooleanField` → `bool`; `NullBooleanField` → `bool | None`; `FloatField` → `float`; `DecimalField` → `Decimal`; `UUIDField` → `uuid.UUID`; `DateField`/`DateTimeField`/`TimeField` → `datetime.date`/`datetime.datetime`/`datetime.time`; `MultipleChoiceField` → `list[str]`; `ModelChoiceField` → the target id (Relay-`GlobalID` vs raw pk — see step 3 for how this overlaps `relation_input_annotation`); `ModelMultipleChoiceField` → `list[<id>]`; `forms.FileField`/`forms.ImageField` → `Upload`. **Implementation note for the dispatch:** the spec warns a naive `functools.singledispatch` with `forms.Field` registered → `str` makes the raise unreachable (lines 1224-1228). The exact-type special-case for bare `Field` + the raising default is the contract; whether realized via `singledispatch` (register the supported classes, special-case `type(field) is forms.Field`, and let the unregistered default raise) or an explicit MRO walk over an ordered registry with a raising fallthrough is W2's discretion (see discretion items) — but the **observable contract** (bare `Field` → `str`, `EmailField` maps via MRO, `CustomField(forms.Field)` raises) is fixed.
   - For `ChoiceField`/`ModelChoiceField`/`ModelMultipleChoiceField`/file, `required` comes from `field.required`; the annotation for the relation/choice cases is finalized at the input-build site (step 3) where the backing column (if any) is known, because the Relay-vs-raw-pk id type needs the related primary `DjangoType`. `convert_form_field` returns the model-less annotation + `kind` + `required`; the model-backed overlap is resolved in `forms/inputs.py`.

3. **`django_strawberry_framework/forms/inputs.py` (new).** Module docstring mirroring `mutations/inputs.py:1-35` (callable, finalizer-free generation substrate; module globals required for `strawberry.lazy`; thin domain wrapper over `utils/inputs.py`). Ship:
   - `INPUTS_MODULE_PATH = "django_strawberry_framework.forms.inputs"` (mirrors `mutations/inputs.py:62`).
   - `_materialized_names: dict[str, type] = {}` ledger + `materialize_form_input_class(name, cls)` thin wrapper over `materialize_generated_input_class(..., family_label="DjangoFormMutation", ledger=_materialized_names)` (mirrors `mutations/inputs.py:103-125`).
   - `clear_form_input_namespace()` (mirrors `mutations/inputs.py:128-148`): `_materialized_names.clear()`. Ship it this slice (the materialization lifecycle needs it; the `registry.clear()` wiring is Slice 2 — leave a `# wired into registry.clear() in Slice 2 (spec-038)` note, no `TODO(spec-038 ...)` anchor needed since this slice ships the function and Slice 2 only wires the call).
   - `get_form_fields(form_class)` (helper #6): `dict(form_class.base_fields)` — no instantiation (Decision 7 lines 1398-1411, P2).
   - `normalize_form_field_sequence(value, *, label)` (helper #5): bare-string / duplicate-name fail-loud, message naming the form-mutation flavor; mirrors `mutations/sets.py:271-299` body, form-flavored wording.
   - The effective-field resolution: given `form_class`, `fields`, `exclude`, validate via `normalize_form_field_sequence`, enforce mutual exclusion (`fields` xor `exclude`), validate every named field exists in `get_form_fields(form_class)` else `ConfigurationError` naming the unknown name (Decision 7 lines 1350-1356, P3), reject an empty effective set (`fields=()`, an `exclude` dropping all, or a form with no fields) with `ConfigurationError` at this resolution point (lines 1357-1360; the `036` empty-input guard, `mutations/inputs.py:519-535`, applied to `form.base_fields`).
   - `form_input_type_name(...)` (helper #4): canonical vs shape-derived narrowed name, reusing `_pascalize_token` from `mutations.inputs` (see Duplication risk avoided). Identity tuple `(form_class, operation_kind, frozenset(effective_field_names))` (Decision 7 lines 1315-1326) — keyed on the **form class object**, not its `__name__`.
   - `build_form_input_class(form_class, operation_kind, *, fields, exclude)` (helper #3): walk the effective form-field set; for each field build the triple:
     - If the form is a `ModelForm` AND the field name resolves to a backing model column (`form_class._meta.model._meta.get_field(name)` succeeds and yields a concrete column): a relation column → `relation_input_annotation(column, related_primary_type=registry.get(column.related_model))` (gives `<name>_id`/`categoryId` + Relay/raw-pk id, `kind=relation_single`/`relation_multi`); a file/image column → `Upload` (`kind=file`); else `convert_scalar(column, type_name, force_nullable=False)` (`kind=scalar`, symmetric enum for `choices`).
     - Else (plain `Form` field, or a `ModelForm` extra field with no column): `convert_form_field(field)` → the model-less annotation + `kind` + `required`.
     - Record one reverse-map spec per generated field (`form_field_name` = the form's declared name; `input_attr`/`graphql_name` from the relation `<name>_id`/camel-name scheme for relations, identity-camel for scalars/files).
     - **Create vs partial requiredness:** create input — `required` from `field.required` for non-model fields, and for model-backed fields the form's `field.required` governs (graphene-django parity, lines 1303-1305); partial input — model-backed fields forced optional (`| None`, default `UNSET`), but a **non-model extra field keeps its declared `field.required`** (Decision 7 lines 1306-1313 / Edge case lines 1919-1922, P2). Optional fields widen `annotation | None` + `default=strawberry.UNSET`, the `mutations/inputs.py:514-516` shape.
     - Build via `build_strawberry_input_class(type_name, triples)`.
   - `build_form_inputs(form_class, *, operation_kind, fields, exclude)` (or a two-call create/partial pair — W2 discretion) returning the create + partial classes + their reverse maps, so a single entry point produces both `<FormClass>Input` and `<FormClass>PartialInput`. The **create-required-narrowing guard** (Decision 7 lines 1362-1376, P2): a `create` whose effective field set omits a still-declared `field.required` form field raises `ConfigurationError` naming the missing field(s) — covering both `Meta.fields` and `Meta.exclude`. Ship the guard as a pure check here keyed on `operation_kind == "create"` and the effective set vs the required-field set; the **`get_form_kwargs`-override waiver** (lines 1370-1374) is a Slice 2/3 concern (the base hook does not exist yet) — ship the guard with a parameter or a documented seam (e.g. `build_form_inputs(..., guard_required=True)`) so Slice 2 can pass `guard_required=False` when the consumer has overridden the hook. Worker 2: surface the waiver as an explicit parameter, do not hard-code the guard always-on (Slice 2's test asserts the waiver).

4. **Operation-kind constants.** Reuse `CREATE` / `PARTIAL` from `mutations.inputs` (`:76-77`) for the generator's create-vs-partial distinction, OR define form-local equivalents if importing them reads as a coupling smell — W2 discretion (the values are the same two-state "build a create input" vs "build a partial input" the generator distinguishes; the mutation `operation` `Meta` verb — `"create"`/`"update"`/`"form"` sentinel — is Slice 2's identity-component namespace, NOT this slice's generator kind). Record the choice in `### Implementation notes`.

### Test additions / updates

Tests live under `tests/forms/` per the AGENTS.md mirror rule (package-internal converter/input mechanics). Create `tests/forms/__init__.py` (the dir is a package, mirroring `tests/mutations/__init__.py`). System-under-test is the converter/generator run against the products `Item`/`Category` FK fixtures plus minimal package-local fixture models/forms for the M2M, non-Relay-target, `Upload`, and plain-`Form`-only shapes products does not carry — the exact fixture posture `tests/mutations/test_inputs.py` uses (`_make_relay_target`/`_make_non_relay_target`, `:258-290`; the registry-isolation autouse fixture `:65-77`). Resolve required-ness via a local `_is_optional` (`StrawberryOptional`) and the `{f.python_name: f for f in cls.__strawberry_definition__.fields}` map, mirroring `tests/mutations/test_inputs.py:91-94`.

**`tests/forms/test_converter.py`** (Test plan lines 1991-2000; Slice 1 checklist lines 313-318):

- Each supported form-field class → its annotation + required-ness: `CharField`/`EmailField`/`SlugField`/`URLField`/`RegexField`/`ChoiceField`/bare `forms.Field` → `str`; `IntegerField` → `int`; `BooleanField` → `bool`; `NullBooleanField` → `bool | None`; `FloatField` → `float`; `DecimalField` → `Decimal`; `UUIDField` → `uuid.UUID`; `DateField`/`DateTimeField`/`TimeField` → the native types; `MultipleChoiceField` → `list[str]`. `required` reflects `field.required` (assert a `required=False` field comes back optional).
- `ModelChoiceField` / `ModelMultipleChoiceField` id mapping: Relay-`GlobalID` when the target's primary `DjangoType` is Relay-Node-shaped vs raw-pk scalar otherwise (drive both via `_make_relay_target` / `_make_non_relay_target`-style fixtures; the id type is pinned at the input-build site, so this assertion may live in `test_inputs.py` if the converter alone returns only the `kind` for relations — keep the Relay-vs-raw-pk assertion wherever the id type is finalized, and pin it for **both** single and multi).
- `forms.FileField` / `forms.ImageField` → `Upload`, `kind=file`.
- **The reverse map (P1):** a `ModelChoiceField` named `category` → `input_attr="category_id"`, `graphql_name="categoryId"`, `form_field_name="category"`, `kind="relation_single"`; an `Upload` field flagged `kind="file"`; a plain scalar identity (`name` → `name`, `kind="scalar"`); a `ModelMultipleChoiceField` → `kind="relation_multi"`.
- **Field discovery from `form_class.base_fields` (P2):** a form whose `__init__` requires a kwarg (e.g. `def __init__(self, *, user, **kw)`) still yields a shape via `base_fields` — assert `get_form_fields(KwargForm)` succeeds with **no instantiation**.
- **The fail-loud dispatch regression (P2):** a bare `forms.Field` → `str`; a known subclass (`EmailField`) maps via MRO; a `class CustomField(forms.Field)` with no supported ancestor raises `ConfigurationError` naming the field/class (the catch-all-shadowing test — this is the load-bearing assertion that no base-`forms.Field` catch-all is registered).

**`tests/forms/test_inputs.py`** (Test plan lines 2001-2012; Slice 1 checklist lines 318-322):

- The **two generated inputs**: `<FormClass>Input` (create) — `field.required` requiredness, a required field non-optional, an optional field `| None` + `default is UNSET`; `<FormClass>PartialInput` — model-backed fields all optional + `UNSET`, but **a required non-model extra field still required** (P2, the load-bearing partial assertion).
- Fields from `form_class.base_fields` (no instantiation; `get_form_fields()` discovery honored), narrowed by `Meta.fields` / `Meta.exclude` (assert the narrowed input omits the dropped field).
- A **form-only (non-model) field included** in the input (a `ModelForm` declaring an extra `confirm` field, or a plain `Form` field) — proves the input derives from the form, not the model columns.
- Materialization as a **module global** of `forms.inputs` (`getattr(sys.modules["django_strawberry_framework.forms.inputs"], "<FormClass>Input")` is the built class; mirrors `tests/mutations/test_inputs.py` materialize assertions).
- **Shape identity (P1):** the same form with two different `Meta.fields` narrowings → two **distinct** generated names; two repeats of the **same** `(form_class, op, effective set)` → **dedupe** (one materialized class, idempotent ledger); two **different** form classes with the **same `__name__`** → finalize-time `ConfigurationError` collision **always** (distinct `form_class` identities never dedupe, even with matching field shapes) — assert via `materialize_form_input_class`.
- An **empty effective field set** (`Meta.fields=()`, an `exclude` dropping all, a fieldless form) → `ConfigurationError`.
- `Meta.fields` / `Meta.exclude` fail-loud (P3): bare string, duplicate name, unknown name against `form.base_fields`, both `fields` + `exclude` set → `ConfigurationError` each.
- The **create-required-narrowing guard (P2):** a `create` narrowing (`Meta.fields` *or* `Meta.exclude`) dropping a `field.required` form field → `ConfigurationError` naming the missing field(s); assert the **waiver** parameter path (`guard_required=False`) does NOT raise. (The `get_form_kwargs`-override semantics that drive the waiver are Slice 2's test; this slice tests the guard + the waiver parameter mechanically.)
- A `ChoiceField` over a `ModelForm` model's `choices` resolves to the **same** generated enum the read `DjangoType` uses (the symmetric-enum edge case, lines 1900-1903) — proves the overlap reuse, not a parallel table.

No temp/scratch tests anticipated; these are permanent package tests Worker 2 writes in the same change as the code.

### Static-inspection helper disposition (planning pass)

Skipped. BUILD.md "When to run the helper during build" requires Worker 1 to run `scripts/review_inspect.py` during planning only when the plan adds logic to an existing `.py` file ≥150 source lines, or to any file under `optimizer/` or `types/`. Slice 1 adds logic exclusively to **net-new** files (`forms/converter.py`, `forms/inputs.py`, `forms/__init__.py`) and touches **no** existing `.py` file (it reuses `utils/inputs.py` / `mutations/inputs.py` / `types/converters.py` read-only, importing their public helpers — no edits). No trigger fires for a planning pass. Worker 3 owns the helper run at review time for the new `forms/converter.py` / `forms/inputs.py` (both carry logic, so not the pure-class-definition skip).

### Implementation discretion items

Genuinely Worker-2-discretion (the design is settled; these are equivalent-shape / naming choices):

- **Dispatch mechanism for `convert_form_field`** — `functools.singledispatch` (register supported classes, special-case `type(field) is forms.Field` → `str`, raising default) vs an explicit ordered-registry MRO walk with a raising fallthrough. Both satisfy the fixed observable contract (bare `Field` → `str`; `EmailField` via MRO; `CustomField(forms.Field)` raises). Pick whichever reads cleaner; the spec's only hard constraint is **no base-`forms.Field` catch-all registration** (lines 1224-1237).
- **Reverse-map record type** — a new frozen `FormInputFieldSpec(input_attr, graphql_name, form_field_name, kind)` dataclass vs reusing `utils/inputs.py::GeneratedInputFieldSpec` (`django_source_path` repurposed). Recommended: a new small dataclass (the `kind` flag has no `GeneratedInputFieldSpec` slot); but if a clean mapping onto the existing spec fits, that is acceptable. Record the choice for Worker 3.
- **`CREATE`/`PARTIAL` constant reuse** — import from `mutations.inputs` vs define form-local equivalents (see step 4).
- **`build_form_inputs` entry-point shape** — one function returning the create+partial pair, vs two `build_form_input_class` calls the caller pairs. Either is fine; keep the create-required guard + the waiver parameter wherever the create input is built.
- **Whether to import `_pascalize_token` from `mutations.inputs` or stage it for an integration-pass lift** — recommended: import it this slice and flag the lift for the integration pass (do NOT re-implement). The cross-module import is acceptable for a pure name-scheme primitive; the consolidation decision is the integration pass's once both sites exist.

### Spec slice checklist (verbatim)

- [x] Slice 1: form-field → Strawberry input mapping + the form-derived input
  generator (per
  [Decision 7](#decision-7--form-field--strawberry-input-mapping-the-form-is-the-input-source-of-truth))
  - [x] [`forms/converter.py`][forms-converter]: a `convert_form_field(field)`
    registry (the graphene-django [`convert_form_field`][upstream-forms-converter]
    parity shape) returning the Strawberry annotation + required-ness for each
    supported form-field class (`CharField` / `ChoiceField` → `str`, `IntegerField` →
    `int`, `BooleanField` → `bool`, `FloatField` → `float`, `DecimalField` → `Decimal`,
    `DateField` / `DateTimeField` / `TimeField` → Python-native, `UUIDField` →
    `uuid.UUID`, `ModelChoiceField` → the target's id, `ModelMultipleChoiceField` /
    `MultipleChoiceField` → `list[<id>]` / `list[str]`, `forms.FileField` /
    `forms.ImageField` → [`Upload`][glossary-upload-scalar]). **Fail-loud dispatch
    (P2):** the fallthrough default **raises** — supported classes are registered
    individually (subclasses map via MRO), bare `forms.Field` is an explicit exact-type
    special case → `str`, and **no base-`forms.Field` catch-all** is registered (which
    would shadow the raise), so a custom `forms.Field` subclass with no supported
    ancestor raises [`ConfigurationError`][glossary-configurationerror] naming the field
    and class. Where a form field maps to a Django column type the read side already
    converts, reuse the [Scalar field conversion][glossary-scalar-field-conversion] /
    [Choice enum generation][glossary-choice-enum-generation] registry rather than
    re-deriving the scalar.
    Record, per generated input field, the `input_attr → (form_field_name, kind)`
    reverse map (`kind ∈ {scalar, relation_single, relation_multi, file}`) the
    resolver needs to build a form-field-keyed payload — `categoryId` / `category_id`
    → `category` / `relation_single`, an `Upload` field flagged `file`
    ([Decision 7](#decision-7--form-field--strawberry-input-mapping-the-form-is-the-input-source-of-truth), P1).
  - [x] [`forms/inputs.py`][forms-inputs] (its own module, per the committed
    four-module `forms/` layout — [Decision 4](#decision-4--module-and-test-locations-forms-subpackage-mirroring-mutations)):
    build **two** `@strawberry.input` classes from the **form's declared fields**
    (`form_class.base_fields`, narrowed by `Meta.fields` / `Meta.exclude`) — `<FormClass>Input`
    (create; each field's requiredness from `field.required`, graphene-django parity)
    and `<FormClass>PartialInput` (update; model-backed fields optional, a **non-model
    extra field keeps its `field.required`**, P2) — under the **shape-identity +
    naming + collision discipline** of `036` adapted to forms: identity `(form_class,
    operation kind, frozenset(effective field names))`, canonical `<FormClass>Input` /
    shape-derived narrowed names, identical shapes dedupe, two distinct shapes on one
    name → finalize-time [`ConfigurationError`][glossary-configurationerror] (P1).
    Reuse [`utils/inputs.py`][utils-inputs]'s `build_strawberry_input_class` +
    `materialize_generated_input_class` core (the latter's ledger gives the collision
    raise for free) and materialize as module globals of the `forms` input namespace
    for the [`strawberry.lazy`][glossary-djangomutationfield] forward-ref. Normalize +
    fail-loud `Meta.fields` / `Meta.exclude` against `form_class.base_fields` (bare string,
    duplicates, unknown names, empty effective set → `ConfigurationError`, mirroring
    `036`'s `_normalize_field_sequence`, P3).
  - [x] Package coverage: [`tests/forms/test_converter.py`][test-forms] — each
    supported form-field class → its annotation + required-ness; the
    `ModelChoiceField` / `ModelMultipleChoiceField` id mapping (Relay-`GlobalID`
    vs raw pk by the target's primary [`DjangoType`][glossary-djangotype]); the
    `forms.FileField` → [`Upload`][glossary-upload-scalar] mapping; the unknown
    form-field [`ConfigurationError`][glossary-configurationerror]. And
    [`tests/forms/test_inputs.py`][test-forms] — the form-derived input shape (fields
    from `form_class.base_fields`, required-ness from `field.required`, `Meta.fields` /
    `Meta.exclude` narrowing, a form-only non-model field included), materialized as a
    module global.

---

## Build report (Worker 2)

### Files touched

Grounded in `git status --short` (only files I created; no existing `.py` edited,
matching the plan's "touches no existing `.py` file"):

- `django_strawberry_framework/forms/__init__.py` (new) — four-module subpackage
  docstring; no re-exports this slice (bases do not exist yet); package-root
  `__init__.py` left untouched per the plan.
- `django_strawberry_framework/forms/converter.py` (new) — the four `kind`
  constants (`SCALAR` / `RELATION_SINGLE` / `RELATION_MULTI` / `FILE`), the frozen
  `FormInputFieldSpec` reverse-map record, the `FormFieldConversion` carrier, and
  `convert_form_field(field)` with the fail-loud no-catch-all dispatch.
- `django_strawberry_framework/forms/inputs.py` (new) — `INPUTS_MODULE_PATH`,
  the `FORM` sentinel + `CREATE_SHAPED_KINDS`, the `_materialized_names` ledger +
  `materialize_form_input_class` / `clear_form_input_namespace` wrappers,
  `get_form_fields`, `normalize_form_field_sequence`,
  `resolve_effective_form_fields`, `form_input_type_name`, the per-field triple
  resolver, `build_form_input_class`, and `build_form_inputs` (create+partial pair
  with the create-required guard + waiver).
- `tests/forms/__init__.py` (new) — package marker (sibling `tests/mutations/`
  has one).
- `tests/forms/test_converter.py` (new).
- `tests/forms/test_inputs.py` (new).

Out-of-scope baseline churn NOT touched by this pass (present at task start or
from concurrent work; left as-is per the validation-run rule and AGENTS.md
"don't auto-revert maintainer/concurrent work"): `docs/feedback.md` (M),
`examples/fakeshop/db.sqlite3` (M), and the deleted `docs/builder/bld-*.md` /
`docs/builder/build-037-*.md` (D). The two `038` artifact files
(`bld-slice-1-form_converter_inputs.md`, `build-038-…md`) are the active build's
own artifacts.

### Tests added or updated

- `tests/forms/test_converter.py` — every supported scalar form-field class →
  annotation + kind (parametrized); `NullBooleanField` → `bool | None`;
  required-ness from `field.required`; `EmailField` maps via MRO under
  `CharField`; the `FloatField`/`DecimalField`/`UUIDField`
  do-not-collapse-to-parent regression; relation/file kind flags; bare
  `forms.Field` → `str`; the custom-`forms.Field`-subclass raise (the
  catch-all-shadowing regression); `FormInputFieldSpec` frozen-record shape.
- `tests/forms/test_inputs.py` — `get_form_fields` discovery incl. a
  kwarg-requiring form (no instantiation); the two input shapes (create
  requiredness, partial model-backed-optional with a required non-model extra
  field staying required); FK raw-pk id (products non-Relay) + model-less
  `ModelChoiceField`/`ModelMultipleChoiceField` Relay-GlobalID vs raw-pk for both
  single and multi; `FileField` → `Upload` (`kind=file`); the symmetric
  enum-reuse over a `ModelForm` `choices` column; `Meta.fields`/`exclude`
  narrowing + all four fail-loud cases; empty-effective-set (3 variants);
  create-required guard via `fields` and `exclude` + the `guard_required=False`
  waiver; canonical + shape-derived names; dedupe; the distinct-shape and
  same-`__name__` collision raises; module-global materialization; the scalar
  identity reverse-map.

Focused run (no `--cov*` flags, AGENTS.md): `uv run pytest
tests/forms/test_converter.py tests/forms/test_inputs.py --no-cov` → **57
passed**. (The `pytest.ini` default appends `--cov`/`fail_under=100`; that gate
is the maintainer's, run with `--no-cov` per the worker rules — coverage is not a
worker tool.)

### Validation run

1. `uv run ruff format .` → 1 file reformatted on the first sweep (a test file),
   then `271 files left unchanged` on the final sweep.
2. `uv run ruff check --fix .` → `All checks passed!` (4 auto-fixes applied to the
   new test files mid-pass: import-sort + an unused-import; all in my own
   slice-intended files).
3. `uv run python scripts/check_trailing_commas.py django_strawberry_framework/forms/
   tests/forms/` → reformatted `tests/forms/test_inputs.py` once (slice-intended,
   stays in the diff).
4. `git status --short` after both ruff invocations: my slice-intended files are
   `django_strawberry_framework/forms/` + `tests/forms/` (untracked, new). The
   `M docs/feedback.md`, `M examples/fakeshop/db.sqlite3`, and the `D
   docs/builder/bld-*.md` / `build-037-*.md` entries are pre-existing baseline /
   concurrent churn — NOT produced by my edits, and `docs/feedback.md` is the
   explicitly-named out-of-scope baseline-dirty file. No unrelated tool churn was
   introduced; nothing reverted (no authorization to touch the baseline-dirty
   files).

### Implementation notes

Only deltas the plan did not pin:

- **Converter dispatch is a `type(field).__mro__` walk over a `dict`, not a
  linear `isinstance` tuple walk.** The plan left the mechanism to W2 discretion
  ("ordered-registry MRO walk … vs singledispatch"). A linear ordered-tuple
  `isinstance` walk is WRONG for forms because `FloatField`/`DecimalField`
  subclass `IntegerField` and `UUIDField` subclasses `CharField`: a parent entry
  would match first and mis-map them. The `__mro__`-against-dict idiom (the same
  shape as `types/converters.py::scalar_for_field`) makes the field's own class
  win. Regression-tested
  (`test_float_and_decimal_do_not_collapse_to_integer_parent`).
- **`NullBooleanField` is a registry entry, not a special-case branch.** It sits
  in `_SCALAR_FORM_FIELDS` mapped to `bool | None`; the MRO walk visits it before
  its `BooleanField` parent, so no separate `isinstance` check is needed.
- **`convert_form_field` returns a small `FormFieldConversion` object, not a
  tuple.** Carries `annotation` / `kind` / `required`; `annotation=None` for the
  relation/file kinds (finalized at the build site where the related primary
  `DjangoType` / `Upload` is known). Chosen over a 3-tuple so the relation/file
  "annotation deferred" contract is explicit at the type level.
- **A `_model_less_relation_annotation` helper handles a plain-`Form`
  `ModelChoiceField`/`ModelMultipleChoiceField`.** Such a field has no model
  column (so it cannot reach `relation_input_annotation`, which is
  `models.Field`-keyed), but its related model is `field.queryset.model`; the
  helper applies the same Relay-vs-raw-pk id rule and `<name>_id`/`list[<id>]`
  scheme. This is the model-less analogue the converter's `relation_*` kinds
  required; the spec's worked examples are all `ModelForm`-backed, so this is the
  minimal completion of the model-less relation path the converter promised. See
  the spec-reconciliation note below.
- **Entry-point shape:** `build_form_inputs(...)` returns the create+partial pair
  `(create_cls, create_specs, partial_cls, partial_specs)`; `build_form_input_class`
  builds one. The create-required guard + the `guard_required` waiver live in
  `build_form_inputs` (where the create input is built), per the plan.
- **Operation-kind constants:** reused `CREATE`/`PARTIAL` from `mutations.inputs`
  (the plan's recommended choice) and added the `FORM` sentinel locally;
  `CREATE_SHAPED_KINDS = frozenset({CREATE, FORM})` names the create-shaped set in
  one place (and binds the imported `CREATE` into use).
- **`_pascalize_token` imported from `mutations.inputs`** (the plan's recommended
  choice — do not re-implement the injective token scheme). Flagged for the
  integration-pass lift below.

### Notes for Worker 3

- No `scripts/review_inspect.py` shadow file was used (the plan's static-helper
  disposition deferred the run to your review pass; both new modules carry logic,
  so they are not the pure-class-definition skip). Source references above are to
  current source, not shadow files.
- **Cross-module private import:** `forms/inputs.py` imports
  `_pascalize_token` and `relation_input_annotation` from
  `django_strawberry_framework.mutations.inputs` (the latter is public; the former
  is module-private). This is the plan-sanctioned reuse of the injective
  name-token scheme. **Integration-pass candidate:** lift `_pascalize_token`
  (and possibly the `CREATE`/`PARTIAL` constants + `relation_input_annotation`)
  into `utils/inputs.py` alongside `graphql_camel_name` once both the mutation and
  form flavors are accepted — the consolidation decision is the integration pass's
  to make, not this slice's.
- **`normalize_form_field_sequence` is a deliberate near-twin of
  `mutations/sets.py::_normalize_field_sequence`** (the plan's helper #5 — the
  `036` original is module-private and hard-codes "DjangoMutation" wording). The
  shared param-driven extraction into `utils/` is the same integration-pass call;
  do not pre-extract.
- The focused suite passed; coverage was intentionally NOT measured (worker rule).
  The maintainer's 100% gate will run at the normal test pass.

### Notes for Worker 1 (spec reconciliation)

- **Model-less relation id-type (small, mechanically-obvious drift, implemented).**
  Decision 7's relation worked examples (`category`, `genres`, `avatar`) are all
  `ModelForm`-backed, where the column resolves the related primary `DjangoType`.
  The converter's `relation_single`/`relation_multi` kinds, however, also fire for
  a **plain-`Form`** `ModelChoiceField`/`ModelMultipleChoiceField` (a form-declared
  relation with no model column). For that case I resolve the related model via
  `field.queryset.model` and apply the identical Relay-`GlobalID`-vs-raw-pk rule +
  `<name>_id`/`list[<id>]` scheme (`forms/inputs.py::_model_less_relation_annotation`).
  This stays within the slice contract (the converter already returns those kinds
  for such fields) and is the natural completion of the model-less relation path;
  it is tested for both single and multi over Relay and non-Relay targets. Flagging
  it because the spec prose does not explicitly state how a model-less relation
  field resolves its id type — confirm this is the intended behavior, or refine in
  a later slice if the resolver decode (Slice 3) needs a different basis.

---

## Review (Worker 3)

Scope reviewed: the Slice 1 untracked diff only — `django_strawberry_framework/forms/{__init__,converter,inputs}.py` and `tests/forms/{__init__,test_converter,test_inputs}.py`. The `M docs/feedback.md` and the deleted prior-cycle `bld-*.md` / `build-037-*.md` are out of scope and ignored per the task framing. `examples/fakeshop/db.sqlite3` is clean in the current working tree (not modified) and untouched regardless.

**Static-inspection helper:** run for both new logic-bearing files (neither is pure-class-definition):
- `python scripts/review_inspect.py django_strawberry_framework/forms/converter.py --output-dir docs/shadow`
- `python scripts/review_inspect.py django_strawberry_framework/forms/inputs.py --output-dir docs/shadow`

Walked every Django/ORM marker: `converter.py` has none in executable code (the `_meta` mentions are docstring-only). `inputs.py` has two — `model._meta.get_field(name)` (`_model_column_for`, wrapped in a `FieldDoesNotExist` try/except, correct) and `scalar_for_field(related_model._meta.pk)` (`_model_less_relation_annotation`, the raw-pk fallback, correct). All `getattr`/`isinstance`/`frozenset` calls of interest were traced and are justified below. Control-flow hotspots (`resolve_effective_form_fields`, `_field_triple_and_spec`, `build_form_input_class`, `build_form_inputs`) each carry a single clear responsibility and read linearly. (Shadow line numbers are non-canonical and are not cited; findings use symbol-qualified paths.)

### High:

None.

### Medium:

None.

### Low:

#### Model-less relation with `queryset=None` raises a raw `AttributeError`, not a `ConfigurationError`

Severity: Low. Source: `django_strawberry_framework/forms/inputs.py::_model_less_relation_annotation #"related_model = field.queryset.model"`.

A plain-`Form` `ModelChoiceField` / `ModelMultipleChoiceField` constructed with `queryset=None` reaches `_model_less_relation_annotation` at the build site, where `field.queryset.model` raises `AttributeError: 'NoneType' object has no attribute 'model'` (verified by temp probe — see Temp test verification). Such a field is an unusable misconfiguration (a `queryset=None` `ModelChoiceField` cannot validate at runtime either), and the spec mandates no coverage for it, so this is not load-bearing. But the package's standing fail-loud posture (AGENTS.md "always recommend the root-cause fix"; the converter itself raises a clean `ConfigurationError` for an unknown field) would prefer a `ConfigurationError` naming the field over a raw `AttributeError` from an internal attribute access. Recommended (optional, deferrable to the integration pass or Slice 3 when the resolver decode for model-less relations lands): guard `field.queryset is None` and raise `ConfigurationError` naming the field, mirroring the converter's unknown-field message shape. No test expectation is required to accept; if addressed, a `test_inputs.py` case asserting the `ConfigurationError` for a `queryset=None` model-less relation field would pin it. Recorded as a non-blocking Low; rejection-to-defer reason: out-of-the-spec edge, unusable input shape, and the cleaner basis may be informed by the Slice 3 resolver decode (which Worker 2 already flagged for Worker 1 reconciliation).

### DRY findings

The slice is strongly DRY-disciplined and the plan's reuse map was honored end-to-end. Verified against current source:

- `forms/inputs.py` routes model-backed columns through the read-side `convert_scalar` / `convert_choices_to_enum` (via `convert_scalar`) and `relation_input_annotation` (`mutations/inputs.py::relation_input_annotation`, confirmed read at lines 249-286) — NOT a parallel scalar table. The `test_choices_modelform_field_resolves_to_read_side_enum` test pins the symmetric-enum object identity (`wrapped_cls is read_enum`), proving the overlap reuse rather than a copy.
- `convert_form_field`'s `_SCALAR_FORM_FIELDS` MRO walk is the genuinely net-new model-less table, reached only for column-less fields — the explicit spec guard against the over-DRY-into-drift trap. Correctly scoped; not a duplication of the read side.
- `materialize_form_input_class` / `clear_form_input_namespace` are thin wrappers over `utils/inputs.py::materialize_generated_input_class` (confirmed read at lines 103-139) with a disjoint per-subsystem ledger; the dedupe + collision raise come for free from the shared ledger (`existing is cls` → no-op; second distinct class → `ConfigurationError`). No hand-rolled name set.
- `_pascalize_token` and `relation_input_annotation` are imported from `mutations.inputs` rather than re-spelt (the injectivity-critical token scheme is reused, not copied). The cross-module private import (`_pascalize_token`) is plan-sanctioned and flagged by Worker 2 for the integration-pass lift into `utils/inputs.py` — agreed, that is the integration pass's call once both flavors are accepted; do not pre-extract here.
- `normalize_form_field_sequence` is a deliberate near-twin of `mutations/sets.py::_normalize_field_sequence` (confirmed read at lines 271-299). The body is byte-equivalent (the duplicate-detection idiom `{name for name in names if name in seen or seen.add(name)}` is identical); the divergence is only the message wording (names the form bases) and the field-existence basis (deferred to `resolve_effective_form_fields` against `base_fields`). The spec mandates this near-copy ("mirroring `036`'s `_normalize_field_sequence`"); the shared param-driven extraction is correctly deferred to the integration pass (the `036` symbol is module-private and only one other family would consume it). Not a finding.

One minor repeated-literal observation (NOT a finding, below the bar): the static helper flags `"DjangoFormMutation for "` appearing 3x as the leading fragment of three distinct `ConfigurationError` messages in `resolve_effective_form_fields` / `build_form_inputs`. These are full, distinct human-readable sentences (not a reused key/constant), so extracting the prefix would harm readability rather than help — leaving inline is correct.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` is **empty** — the package-root `__init__.py` is unchanged and adds NO form symbols (`grep` confirms no `DjangoForm*` / `forms` re-export and `__all__` untouched). This is correct: Slice 1 ships no public exports; root exports are Slice 2's job. The `forms/__init__.py` own surface is a pure module docstring with no `__all__` and no re-exports of bases (they do not exist yet) — appropriate for this slice. Public-surface check: PASS.

### CHANGELOG sanity

Not applicable; slice did not modify `CHANGELOG.md`.

### Documentation / release sanity

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces (Slice 1 is package-internal only; the version bump and doc updates are Slice 5).

### What looks solid

- **The fail-loud dispatch (Decision 7 P2) is exactly right.** `convert_form_field` registers supported classes individually in `_SCALAR_FORM_FIELDS` and walks `type(field).__mro__` (so `EmailField`/`SlugField`/`URLField`/`RegexField` map under `CharField`); bare `forms.Field` is an explicit `type(field) is forms.Field` special case → `str`; there is **no** base-`forms.Field` catch-all registration, so an unregistered `forms.Field` subclass hits the raising `ConfigurationError` default. The catch-all-shadowing regression is pinned by `test_unknown_custom_field_subclass_raises`. I traced the control flow: the relation/file/multi `isinstance` pre-checks run before the scalar MRO walk (correct — `ModelChoiceField`/`ModelMultipleChoiceField`/`MultipleChoiceField` all subclass `ChoiceField`, so the more-specific kind must win), and `NullBooleanField → bool | None` sits in the registry before its `BooleanField` parent so the MRO walk visits it first. The `FloatField`/`DecimalField`/`UUIDField` do-not-collapse-to-parent hazard (they subclass `IntegerField`/`CharField`) is real and correctly handled by the MRO-against-dict idiom (mirrors `types/converters.py::scalar_for_field`), regression-tested.
- **The reverse map (P1)** `FormInputFieldSpec(input_attr, graphql_name, form_field_name, kind)` is a frozen dataclass with the four `kind` values pinned as module constants (`SCALAR`/`RELATION_SINGLE`/`RELATION_MULTI`/`FILE`) — one source of truth for the Slice 3 resolver. `form_field_name` is always the form's declared name (never the `<name>_id` relation attr), which is the load-bearing fix for the `categoryId`-exposed-but-`category`-keyed decode. Verified `category` → `input_attr="category_id"`, `graphql_name="categoryId"`, `kind="relation_single"`; `Upload` → `kind="file"`; scalar identity; M2M → `kind="relation_multi"`.
- **The two generated inputs.** Create honors `field.required`; partial forces model-backed fields optional (`column is not None`) but a non-model extra field keeps `field.required` — `required = False if (is_partial and column is not None) else field.required` is precisely the P2 rule. The load-bearing partial assertion (`confirm` extra still required) is pinned. Discovery is via `form_class.base_fields` with NO instantiation (`get_form_fields` = `dict(form_class.base_fields)`); the kwarg-requiring-form test confirms a shape is discoverable without `form_class()`.
- **Shape identity + naming + dedupe + collision.** Identity is `(form_class, operation_kind, frozenset(effective field names))` keyed on the form class object (not `__name__`); `form_input_type_name` reuses `_pascalize_token` for the injective narrowed-name suffix, and the `FORM` sentinel correctly falls under the `Input` suffix (verified by probe + `test_canonical_name_for_full_shape`). The finalize-time collision raise (distinct shapes on one name; two different forms sharing a `__name__`) comes from the shared materialize ledger — confirmed both collision cases raise `ConfigurationError`. I verified by probe that two `build_form_input_class` calls on the same form produce distinct class objects that DO collide at materialize — this is the correct ledger semantics (dedupe is `existing is cls` identity-based; Slice 2's bind owns calling materialize once per shape, exactly as the `036` bind does).
- **`Meta.fields`/`Meta.exclude` normalization + fail-loud** against `base_fields`: bare string, duplicate, unknown name, mutual exclusion, and empty effective set (three variants) all raise `ConfigurationError` — every branch is tested.
- **The create-required guard with its waiver seam.** `build_form_inputs(..., guard_required=True)` raises naming the dropped required field(s), covering both `Meta.fields` and `Meta.exclude`; `guard_required=False` is the explicit `get_form_kwargs`-override waiver Slice 2 will pass, surfaced as a parameter (never hard-coded always-on) — both paths tested.
- **DRY guard:** model-backed `ModelForm` fields reuse the read-side converters; only column-less fields hit the net-new `convert_form_field` table. The symmetric-enum test proves identity reuse, not a parallel copy.

### Temp test verification

- `docs/builder/temp-tests/slice-1/test_probe.py` (5 probes) and `test_probe2.py` (1 probe) — created during review, all passed, then **deleted** (no real bug caught; they confirmed expected behavior). Findings folded into the review above:
  - model-less relation in a PARTIAL input correctly keeps `required` (column-less → honors `field.required`);
  - two `build_form_input_class` calls on one form produce distinct class objects that collide at materialize (correct ledger semantics — `REBUILD_SAME_FORM_COLLIDES=True`, expected; dedupe is by class identity, Slice 2's bind owns single-materialize-per-shape);
  - M2M model-less relation sets no spurious GraphQL alias (`graphql_name=None`, plain `targets`);
  - a `ModelForm` optional non-model extra field is optional in partial (no crash);
  - the `FORM` sentinel uses the `Input` suffix (not `PartialInput`);
  - `test_probe2.py`: a `queryset=None` model-less `ModelChoiceField` raises a raw `AttributeError` at the build site → recorded as the single Low finding above.
- No temp test caught a behavior bug requiring promotion; the permanent suite (`tests/forms/test_converter.py` + `test_inputs.py`, 57 tests) already pins every Slice-1 behavior. Focused run confirmed: `uv run pytest tests/forms/test_converter.py tests/forms/test_inputs.py --no-cov` → **57 passed**. Lint/format/trailing-comma checks on the new files are clean.

### Spec slice checklist audit

Walked all four verbatim `- [x]` boxes against the diff:

- `forms/converter.py` `convert_form_field` registry + fail-loud dispatch + reverse map — landed (`converter.py`); box correctly ticked.
- `forms/inputs.py` two `@strawberry.input` generators + shape-identity/naming/collision + reuse of `utils/inputs.py` core + `Meta.fields`/`Meta.exclude` fail-loud — landed (`inputs.py`); box correctly ticked.
- `tests/forms/test_converter.py` — landed, covers every supported class + the fail-loud regression + relation/file kinds + the frozen-record; box correctly ticked.
- `tests/forms/test_inputs.py` — landed, covers the two input shapes + Relay/raw-pk id (single+multi) + narrowing + collision/dedupe + module-global materialization + the symmetric enum + the create-required guard/waiver; box correctly ticked.

No over-ticked boxes (every `- [x]` has matching implementation) and no silently-unaddressed sub-checks. The slice over-delivers slightly relative to the converter checklist's narrowest reading (the Relay-vs-raw-pk id assertions live in `test_inputs.py` where the id type is finalized, which the plan explicitly authorized) — not a finding.

### Notes for Worker 1 (spec reconciliation)

- **Escalated (Low, non-blocking): model-less relation id-type basis (`field.queryset.model`).** Worker 2 flagged this; I assessed it and it is a **clean reconciliation note, not a finding**. The implementation (`forms/inputs.py::_model_less_relation_annotation`) resolves a plain-`Form` `ModelChoiceField`/`ModelMultipleChoiceField`'s related model via `field.queryset.model` and applies the identical Relay-`GlobalID`-vs-raw-pk + `<name>_id`/`list[<id>]` scheme the model-backed path uses — the natural and only correct completion of the model-less relation path (the converter already returns `relation_single`/`relation_multi` for these fields, so an id type must be derived; Django's `ModelChoiceField` always carries a `.queryset.model` when usably configured, verified). It is tested for both single and multi over Relay and non-Relay targets and is consistent with the spec's reverse-map/decode discussion (which is `ModelForm`-keyed only because its worked examples happen to be). Resolution path for Worker 1: **confirm the `field.queryset.model` basis in the spec prose** (a one-line Decision 7 addition stating how a column-less relation field resolves its related primary `DjangoType`), and verify the **Slice 3 resolver decode uses the same basis** — if Slice 3's decode needs the related model from a different source for a model-less relation, reconcile both sites together. No spec edit is required to accept Slice 1.
- The single Low finding (raw `AttributeError` for `queryset=None`) is deferrable; weigh it alongside the Slice 3 decode if you touch this path.

### Review outcome

`review-accepted` — zero High, zero Medium findings; one Low finding recorded with a deferral reason (non-blocking, out-of-spec edge). The verbatim checklist boxes all match the implementation. Worker 2's spec-reconciliation item is assessed as a clean reconciliation note (not a defect) and escalated transparently to Worker 1 for a one-line Decision 7 confirmation + Slice 3 cross-check; it does not require a spec edit to accept this slice.

---

## Final verification (Worker 1)

- **Spec slice checklist audit:** all four `- [x]` boxes in the Plan's `### Spec slice checklist (verbatim)` audited against the untracked diff. Each landed; no over-ticks, no silently un-ticked boxes. Detail:
  - `forms/converter.py` — `convert_form_field` registry + fail-loud no-catch-all dispatch (`type(field).__mro__` walk over `_SCALAR_FORM_FIELDS`, bare-`Field` exact-type special case → `str`, raising `ConfigurationError` fallthrough) + the `FormInputFieldSpec` reverse-map record with the four `kind` constants. Landed.
  - `forms/inputs.py` — the two `@strawberry.input` generators (`build_form_input_class` / `build_form_inputs`) over `form_class.base_fields`, `(form_class, op, frozenset(effective))` shape identity, canonical-vs-shape-derived naming (`_pascalize_token` reuse), the collision/dedupe raise free from the shared `materialize_generated_input_class` ledger, `utils/inputs.py` core reuse, and `Meta.fields`/`exclude` fail-loud (`normalize_form_field_sequence` + `resolve_effective_form_fields`). Landed.
  - `tests/forms/test_converter.py` — every supported class + the catch-all-shadowing raise + relation/file kinds + the frozen record. Landed.
  - `tests/forms/test_inputs.py` — the two input shapes (create requiredness, partial model-backed-optional with a required non-model extra staying required), Relay/raw-pk id single+multi, narrowing, empty-set, the create-required guard + `guard_required=False` waiver, dedupe + both collision cases, module-global materialization, the symmetric-enum reuse. Landed.
- **DRY check (this slice; no prior accepted slices):** no new in-slice duplication. The model-backed path routes through the read-side `convert_scalar` / `convert_choices_to_enum` / `relation_input_annotation` (verified: `_field_triple_and_spec` resolves the `models.Field` first, never re-lists a scalar table); the symmetric-enum test pins object identity, proving reuse. `materialize_form_input_class` / `clear_form_input_namespace` are thin wrappers over the shared `utils/inputs.py` ledger. The two flagged near-twins are **correctly deferred to the integration pass, not Slice-1 blockers**: (a) `normalize_form_field_sequence` is the spec-mandated near-copy of the module-private `mutations/sets.py::_normalize_field_sequence` ("mirroring `036`'s `_normalize_field_sequence`") — the shared param-driven lift into `utils/` is the integration pass's call once both sites exist and are accepted; (b) `_pascalize_token` is **imported** from `mutations.inputs` (not re-spelled), flagged for a possible integration-pass lift into `utils/inputs.py` alongside `graphql_camel_name`. Both deferrals are correct: the `036` symbols are private and only one other family would consume a shared form, so the consolidation decision is the integration pass's, not this slice's.
- **Existing tests still pass:** `uv run pytest tests/forms/ --no-cov` → **57 passed**. No `--cov*` flag used (coverage is the maintainer's gate).
- **Worker 3's escalated reconciliation item — resolved with a spec edit (see below).** The model-less relation id-basis (`field.queryset.model`) is the natural and only-correct completion of the relation path the converter opens for a plain-`Form` `ModelChoiceField`/`ModelMultipleChoiceField` (the converter returns `relation_single`/`relation_multi`, so an id type must be derived; Decision 7's worked examples are all `ModelForm`-backed only because that is what they happen to use). I judged a one-line Decision 7 clarification **warranted** rather than a silent implementation detail: documenting the basis keeps the spec accurate to what shipped and, more importantly, pins the contract Slice 3's resolver decode must align to (the visibility query must resolve the same related primary type by the same basis — `column.related_model` for model-backed, `field.queryset.model` for model-less). The edit touches no Slice-1 code contract (the implementation already does this and is tested single+multi over Relay/non-Relay targets), so it does not trigger a Worker 2 re-pass.
- **The single Low finding (`queryset=None` raw `AttributeError`)** is left deferred per Worker 3's recorded reason: an unusable input shape, out of spec, and the cleaner fail-loud basis may be informed by the Slice 3 resolver decode. Carried to the deferred-work catalog via the integration/final pass. Not a `final-accepted` blocker.
- **Final status: `final-accepted`.** The slice delivers its Decision 7 Slice-1 contract; tests pass; DRY is disciplined with the two near-twins correctly deferred.

### Summary

Slice 1 ships the form-mutations generation substrate as three net-new package modules and two package test files, touching no existing tracked `.py`:

- `forms/__init__.py` — the four-module subpackage docstring; no public re-exports (bases are Slice 2), package-root `__init__.py` untouched.
- `forms/converter.py` — `convert_form_field(field)`, the `forms.Field`-keyed → Strawberry-annotation + required-ness registry for the **model-less case**, with the fail-loud no-base-`Field`-catch-all dispatch (the graphene-django `ImproperlyConfigured` parity raised as `ConfigurationError`); the `FormInputFieldSpec` reverse-map record and the four `kind` module constants the Slice 3 resolver will consult.
- `forms/inputs.py` — the `@strawberry.input` generation substrate: `get_form_fields` (no-instantiation `base_fields` discovery), `normalize_form_field_sequence` + `resolve_effective_form_fields` (`Meta.fields`/`exclude` fail-loud), `form_input_type_name` (shape-identity naming), `build_form_input_class` / `build_form_inputs` (the create+partial pair with the create-required guard + waiver), and the `materialize_form_input_class` / `clear_form_input_namespace` lifecycle over the shared `utils/inputs.py` ledger. Model-backed `ModelForm` columns route through the read-side converters for a symmetric wire contract; only column-less fields use the net-new converter table.

The bases, the metaclass, `_validate_meta`, the phase-2.5 bind, `registry.clear()` wiring, and the resolver pipeline are Slice 2 / Slice 3.

### Spec changes made (Worker 1 only)

- **`docs/SPECS/spec-038-form_mutations-0_0_12.md` Decision 7 (inserted after the relation-mapping bullet at ~line 1200).** Added a one-paragraph "The related model for a relation field's id basis" clarification (triggered by Slice 1): documents that a model-backed relation resolves its related model via `column.related_model` while a model-less plain-`Form` `ModelChoiceField`/`ModelMultipleChoiceField` uses `field.queryset.model`, and states the Slice 3 `forms/resolvers.py` decode must resolve the related primary type by the **same basis** so the input id type and the decode's visibility query agree. Reason: the shipped converter returns `relation_single`/`relation_multi` for column-less relation fields, so an id basis is required; the spec prose only covered `ModelForm`-backed relations. Confirms Worker 2's implemented behavior and pins the Slice 3 contract. No Slice-1 code contract changed.
- **`docs/SPECS/spec-038-form_mutations-0_0_12.md` spec self-reference path discrepancy (lines 852, ~2227, ~2289, ~2291 after the Decision 7 insertion shifted line numbers).** Reconciled the four prose self-references from `docs/spec-038-form_mutations-0_0_12.md` to `docs/SPECS/spec-038-form_mutations-0_0_12.md` (Decision 1 statement, the card-citation note, and DoD item 1's two occurrences incl. the `check_spec_glossary.py` command). Reason: the build-plan preamble flagged this as a spec-internal inconsistency (the real file and its reference-style link defs resolve from `docs/SPECS/`); reconciling it on this spec-touching pass is in scope for a Slice-1 final verification (touches no Slice-1 code contract). `check_spec_glossary.py --spec docs/SPECS/spec-038-form_mutations-0_0_12.md` re-run after the edits → `OK: 31 terms`.
