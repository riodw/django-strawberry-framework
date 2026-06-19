# Build: Slice 2 — write-side Upload input + Upload re-export

Spec reference: `docs/spec-037-upload_file_image_mapping-0_0_11.md` (lines 330-374, the Slice 2 block of `## Slice checklist`; governed by Decision 5 lines 1057-1098 and Decision 6 lines 1100-1165)
Status: final-accepted

## Plan (Worker 1)

This slice ships the **write** half of the file/image story plus the public
`Upload` re-export. Three source files, each landing a pre-placed
`TODO(spec-037 Slice 2)` anchor:

- `scalars.py` — re-export `Upload` / `UploadDefinition` from
  `strawberry.file_uploads.scalars` (no `_PACKAGE_SCALAR_MAP` entry) and fix the
  stale `TODO-ALPHA-035-0.0.11` docstring reference to `TODO-ALPHA-037-0.0.11`.
- `mutations/inputs.py` — replace the `NotImplementedError` staged seam in
  `build_mutation_input` with a real `FileField` / `ImageField` → `Upload`
  mapping that falls through to the **existing** requiredness / `| None`-widening
  / override-skip machinery (lifting the `036` CR-6 file-column merge-override
  carve-out by ordering alone).
- `mutations/resolvers.py` — **VERIFY-FIRST**: the spec's working hypothesis is
  that the shipped generic scalar-assignment path already carries an uploaded
  file. Plan to add NO branch; remove the two `TODO(spec-037 Slice 2)` anchors
  only after a test proves the generic `model(**attrs)` (create) / `setattr`
  (update) path works. Add a file-specific branch ONLY if that test fails.

The P0 read/write split is the standing invariant: this slice must NOT add
`Upload` to `FIELD_OUTPUT_TYPE_MAP` (that is the read map, Slice 1) and must NOT
leak the read output objects (`DjangoFileType` / `DjangoImageType`) into the
input path. The write side maps to `Upload`; `SCALAR_MAP`'s `FileField: str` /
`ImageField: str` rows stay untouched (they serve only the filter-input path).
The root `__init__.py` re-export + `__all__` is **Slice 3**, NOT here — this
slice plans only the `scalars.py`-level re-export.

The pre-placed anchors that land this slice:
- `scalars.py` #"TODO(spec-037 Slice 2)" (lines 24-31, before `_BIGINT_STRING_PATTERN`) plus the stale docstring ref at `scalars.py:3`.
- `mutations/inputs.py::build_mutation_input` #"Upload staged seam (TODO-ALPHA-037-0.0.11)" (lines 476-496).
- `mutations/resolvers.py::_run_create` #"TODO(spec-037 Slice 2)" (lines 913-916) and `mutations/resolvers.py::_run_update` #"TODO(spec-037 Slice 2)" (lines 955-958).
- Test anchors: `tests/test_scalars.py:14-20`, `tests/mutations/test_inputs.py:531-540` (replace the seam tests at `test_inputs.py:543-576`), `tests/mutations/test_resolvers.py:21-28`.

### DRY analysis

- **Existing patterns reused.**
  - **Requiredness + optional widening + override skip in `build_mutation_input`.**
    The file/image branch reuses the SAME post-`else` machinery the scalar branch
    already runs: `if python_attr in overrides: continue`
    (`inputs.py:501-502`), `required = is_create and not is_m2m and
    input_field_required(field)` (`inputs.py:511-512`), the
    `if python_attr != graphql_name: field_kwargs["name"] = graphql_name`
    alias rule (`inputs.py:514-515`), and the
    `if not required: annotation = annotation | None;
    field_kwargs["default"] = strawberry.UNSET` widening (`inputs.py:516-518`).
    The file branch's ONLY job is to produce the `(python_attr, graphql_name,
    annotation)` triple (`python_attr = field.name`,
    `graphql_name = graphql_camel_name(python_attr)`, `annotation = Upload`) and
    then fall through — exactly the shape the existing scalar branch produces
    (`inputs.py:497-499`). No new requiredness predicate, no parallel optional
    widening, no second override skip.
  - **`graphql_camel_name`** is already imported and used by the scalar branch
    (`inputs.py:52`, `inputs.py:498`); the file branch reuses it verbatim, so
    file/image inputs camel-case identically to every other scalar input
    (`attachment` → `attachment`, `cover_art` → `coverArt`).
  - **`input_field_required`** (`inputs.py:223-239`) is the single requiredness
    rule. A `FileField` reports `null` / `blank` / `has_default()` like any
    column, so the same predicate gives the spec's contract: a
    `blank=False`/`null=False`/no-default file column is required in the create
    input, optional otherwise and in every partial input. No file-specific
    requiredness logic.
  - **`UploadDefinition` import shape mirrors the `BigInt` scalar-definition
    pattern.** `scalars.py` already imports a `ScalarDefinition` and pairs the
    `NewType` with it (`BigInt` / `_BIGINT_SCALAR_DEFINITION`, `scalars.py:98-104`).
    `Upload` / `UploadDefinition` are upstream's already-built equivalent
    (`Upload = NewType("Upload", bytes)` + a `ScalarDefinition`), so the
    re-export is a pure `from strawberry.file_uploads.scalars import Upload,
    UploadDefinition` — no new scalar construction, and deliberately NO
    `_PACKAGE_SCALAR_MAP` entry (Decision 5).
  - **`_explicit_null_error`** (`resolvers.py:191-215`) already keys an explicit
    `null` on ANY `null=False` scalar column to a `FieldError`
    (`"This field cannot be null."`). A file column is a scalar input (not a
    relation), so it reaches this guard via the existing `_decode_relations`
    scalar branch (`resolvers.py:180-186`) for free — no new file-null guard. The
    plan VERIFIES this with a test rather than adding code.
  - **The generic scalar assignment path** in `_run_create`
    (`model(**scalar_and_fk_attrs)`, `resolvers.py:917`) and `_run_update`
    (`setattr(instance, attr, value)`, `resolvers.py:959-960`) is the path the
    spec hypothesizes already carries an `UploadedFile` (Django's `FileField`
    descriptor accepts it). The plan reuses it unchanged; a test proves it.
  - **Synthetic-model + resolver test infra** is the established
    `@pytest.mark.django_db(transaction=True)` + `connection.schema_editor()` +
    `override_settings(MEDIA_ROOT=tmp_path)` + `_unique_app_label()` pattern
    Slice 1 used in `tests/types/test_resolvers.py` and that
    `tests/mutations/test_inputs.py` (`_unique_app_label`, `itertools.count`,
    `test_inputs.py:76-81`) and `tests/mutations/test_resolvers.py`
    (`itertools.count`, `test_resolvers.py:32`, `68-79`) already use. The
    `SimpleUploadedFile` helper (`django.core.files.uploadedfile`) is the standard
    way to materialize an uploaded file in a test. Pillow is already a dev-only
    dependency (added in Slice 1) for the image case.

- **New helpers justified.** **None.** This slice adds no new helper, no new
  module, and (by the verify-first contract) no new resolver branch. The
  `scalars.py` change is a re-export (two imported names); the `inputs.py` change
  replaces a `raise` block with a three-line triple assignment inside the
  existing `else` branch; the `resolvers.py` change is a comment removal once the
  generic path is verified. If — and only if — the verify-first test proves the
  generic path fails, Worker 2 surfaces that under `### Notes for Worker 1` and a
  minimal file-assignment branch becomes justified (single responsibility:
  assign the `UploadedFile` to the model field); that is contingent, not planned.

- **Duplication risk avoided.**
  - **A parallel file-only requiredness / optional / override path.** Risk: the
    naive implementation writes its own `required = ...`, its own
    `annotation | None`, its own `if python_attr in overrides` inside the file
    branch. Avoided: the file branch produces ONLY the triple and falls through
    to the shared machinery (`inputs.py:501-519`) — the same fall-through the
    scalar branch uses. This is also what lifts the CR-6 carve-out: the old
    `raise` ran BEFORE the override skip at `inputs.py:501`; reordering so the
    file branch assigns `python_attr` and falls through means file columns now hit
    the `if python_attr in overrides: continue` like any scalar, with no separate
    code.
  - **A second `Upload` definition / a `_PACKAGE_SCALAR_MAP` entry.** Risk:
    defining a wrapper `NewType` or registering `Upload` in the package scalar map
    "for symmetry with `BigInt`". Avoided by Decision 5: re-export upstream's
    `Upload` verbatim; add NO map entry (it already resolves via
    `DEFAULT_SCALAR_REGISTRY` — VERIFIED: `Upload in DEFAULT_SCALAR_REGISTRY` is
    `True` at the pinned upstream version).
  - **A divergent write path for files.** Risk: adding a dedicated file branch in
    the resolver up front (the P2 finding the spec rejects, Decision 6 lines
    1161-1165). Avoided by the verify-first rule: no branch unless a test forces
    one.
  - **Read objects leaking into the input path.** Risk: importing
    `convert_field_output` / `FIELD_OUTPUT_TYPE_MAP` into `inputs.py`, or adding
    `Upload` to `FIELD_OUTPUT_TYPE_MAP`. Avoided: the input mapping is a literal
    `Upload` annotation in the seam; the read map is never consulted on the write
    side, and `Upload` is never added to the read map. The standing P0 split.

### Implementation steps

Line numbers are pin-at-write-time navigational hints; verify against current
source before editing (a prior pass may have shifted the file).

1. **`django_strawberry_framework/scalars.py` — re-export `Upload` and fix the
   stale card ref.**
   - Fix the docstring at `scalars.py:3`: change
     `Future scalars (e.g. ``Upload`` per TODO-ALPHA-035-0.0.11) land here.` to
     reflect that `Upload` is re-exported here per `TODO-ALPHA-037-0.0.11`
     (the stale `035` is the optimizer-hardening card; the real owner is `037`).
     Worker 2 may reword the sentence as long as the card number becomes
     `TODO-ALPHA-037-0.0.11` and the docstring no longer calls `Upload` a
     "future" scalar.
   - Replace the `TODO(spec-037 Slice 2)` anchor block at `scalars.py:24-31`
     with `from strawberry.file_uploads.scalars import Upload, UploadDefinition`.
     Place it with the other imports (after the existing
     `from strawberry.types.scalar import ScalarDefinition` at `scalars.py:22`),
     so the module re-exports both names. CONFIRMED import path:
     `strawberry.file_uploads.scalars` exposes both `Upload` (a
     `NewType("Upload", bytes)`) and `UploadDefinition` (a `ScalarDefinition`).
   - Do **NOT** add `Upload` to `_PACKAGE_SCALAR_MAP` (`scalars.py:106-108`) —
     leave that dict as `{BigInt: _BIGINT_SCALAR_DEFINITION}` byte-unchanged
     (Decision 5; the deliberate contrast with package-custom `BigInt`).
   - `__init__.py` is NOT touched here (root re-export + `__all__` is Slice 3).
     The `scalars.py` module simply makes `Upload` / `UploadDefinition`
     importable from it.

2. **`django_strawberry_framework/mutations/inputs.py::build_mutation_input` —
   replace the staged seam with the `Upload` mapping.** At the `else` branch
   (`inputs.py:475-499`), replace the `Upload staged seam` comment block and the
   `if isinstance(field, (models.FileField, models.ImageField)): raise
   NotImplementedError(...)` (`inputs.py:476-496`) with the mapping the seam's own
   pseudo-code describes (`inputs.py:481-488`):
   - `if isinstance(field, (models.FileField, models.ImageField)):` set
     `python_attr = field.name`, `graphql_name = graphql_camel_name(python_attr)`,
     `annotation = Upload`.
   - `else:` keep the existing scalar path
     (`python_attr = field.name`, `graphql_name = graphql_camel_name(python_attr)`,
     `annotation = _scalar_input_annotation(field, type_name)`,
     `inputs.py:497-499`).
   - Add `from .scalars import Upload` to the imports (or
     `from ..scalars import Upload` — `inputs.py` is one level deeper, so the
     parent-package form matches the existing `from ..exceptions import
     ConfigurationError` / `from ..types.converters import ...` style at
     `inputs.py:46-48`). Import the re-exported `Upload` from the package
     `scalars` module so there is one package-internal source of the symbol, not
     a direct upstream import duplicated here.
   - **Do nothing else in the loop body.** Control falls through to the existing
     `if python_attr in overrides: continue` (`inputs.py:501-502`) — which is what
     lifts the CR-6 carve-out (the file column now participates in the
     `Meta.input_class` / `Meta.partial_input_class` merge override like any
     scalar) — then through `input_field_required` / the alias rule / the
     `| None` widening (`inputs.py:504-519`) unchanged. Required only when
     `is_create and input_field_required(field)`; widened to `Upload | None` with
     `default=UNSET` otherwise and in every partial input.
   - The `_scalar_input_annotation` docstring's stale closing sentence
     (`inputs.py:295-296`: "The ``FileField`` / ``ImageField`` Upload seam is
     handled by the caller before this runs.") stays accurate — the caller still
     handles file/image before `_scalar_input_annotation`; Worker 2 may leave it
     or tighten it to "is now mapped to ``Upload`` by the caller" (cosmetic,
     discretion item).
   - Update the `overrides` param docstring at `inputs.py:445-449` only if its
     "In Slice 1 the seam is exercised directly; Slice 2 wires it from
     ``Meta.input_class``" wording is now stale relative to the shipped `036`
     wiring — confirm against the current `sets.py` override computation; if the
     wiring already shipped in `036`, reword to present tense. Cosmetic; not a
     contract change (discretion item).

3. **`django_strawberry_framework/mutations/resolvers.py` — VERIFY, do not add a
   branch.** The generic path already assigns provided scalars:
   `_decode_relations` (`resolvers.py:120-188`) routes a non-relation column
   through `scalar_and_fk_attrs[python_name] = ...` (`resolvers.py:186`) after the
   `_explicit_null_error` guard (`resolvers.py:180-182`); `_run_create` builds
   `model(**scalar_and_fk_attrs)` (`resolvers.py:917`) and `_run_update` does
   `setattr(instance, attr, value)` (`resolvers.py:959-960`). Django's `FileField`
   descriptor accepts an `UploadedFile`, so a file column flows through unchanged.
   - **Plan: write the resolver tests first (step in Test additions), confirm the
     generic path carries the file, then REMOVE the two `TODO(spec-037 Slice 2)`
     anchor comments** at `resolvers.py:913-916` (`_run_create`) and
     `resolvers.py:955-958` (`_run_update`) — leaving the production code lines
     (`model(**scalar_and_fk_attrs)`, the `setattr` loop) **unchanged**. The
     anchors are removed because the slice they named has shipped (the
     verification), not because code changed.
   - **Add a file-specific branch ONLY if a test proves the generic path fails.**
     If Worker 2's create / partial-update file test fails on the generic path,
     Worker 2 records the failure mode under `### Notes for Worker 1 (spec
     reconciliation)` and adds the minimal branch needed; otherwise no production
     code in `resolvers.py` changes. This is the spec's explicit verify-first
     contract (Decision 6 lines 1113-1119, 1161-1165).
   - `UNSET`-leaves-file-unchanged is already the partial-update contract: an
     omitted field is stripped in `_decode_relations` (`value is strawberry.UNSET:
     continue`, `resolvers.py:155-156`), so it never reaches the `setattr` loop
     and the stored file is untouched. The test pins this; no code change.
   - explicit-`null`-on-`null=False` → `FieldError` is already delivered by
     `_explicit_null_error` (`resolvers.py:191-215`) for the file column (it is a
     scalar input). The test pins this; no code change. Clearing semantics stay a
     Risks item, NOT promised (Decision 6 lines 1134-1136, Risks lines 1527-1535).

### Test additions / updates

Tests are written by Worker 2 in the same change as the code (BUILD.md "Coverage
is the maintainer's gate"). All Slice 2 coverage is package tests. Do **NOT**
plan any `--cov*` invocation; no live `/graphql/` surface (no fakeshop file
column, Decision 9). The resolver file tests use synthetic models with
`@pytest.mark.django_db(transaction=True)` + `connection.schema_editor()` +
`override_settings(MEDIA_ROOT=tmp_path)`, matching Slice 1's
`tests/types/test_resolvers.py` shape and `tests/mutations/test_resolvers.py`'s
existing `itertools.count` app-label idiom.

- **`tests/test_scalars.py`** (replace the `TODO(spec-037 Slice 2)` anchor at
  `test_scalars.py:14-20`; spec Slice 2 "Package coverage" lines 365-368, Test
  plan lines 1450-1455):
  - `Upload` is importable from `django_strawberry_framework.scalars` (and is
    identical to Strawberry's built-in `strawberry.file_uploads.scalars.Upload` —
    `assert Upload is strawberry.file_uploads.scalars.Upload`), proving it is a
    re-export, not a wrapper.
  - `strawberry_config().scalar_map` contains `BigInt` but **NOT** `Upload`
    (`Upload not in strawberry_config().scalar_map`) — pins Decision 5: `Upload`
    is not a package `scalar_map` key.
  - An `Upload`-annotated field resolves through a schema built with
    `config=strawberry_config()` **AND** through a schema built with a plain
    `StrawberryConfig()` (no package config) — proving `Upload` rides
    Strawberry's `DEFAULT_SCALAR_REGISTRY`, not the package map. Assertion shape:
    build a tiny `@strawberry.type` with an `Upload`-typed input or field, build
    the schema both ways, and assert the schema builds and the `Upload` scalar
    appears in the SDL (`"scalar Upload"` in `str(schema)`), under each config.
    (A full multipart round trip is NOT required — the `0.0.14` `TestClient` card
    owns transport; this test pins that the scalar is registered/resolvable.)
  - The existing `BigInt` `extra_scalar_map` collision `ValueError` test
    (`test_strawberry_config_collision_with_package_scalar_raises_value_error`,
    `test_scalars.py:330-336`) is **untouched** — explicitly do not modify it.

- **`tests/mutations/test_inputs.py`** (replace the two staged-seam tests at
  `test_inputs.py:543-576` — `test_file_field_raises_not_implemented_error`
  and `test_image_field_raises_not_implemented_error` — and the
  `TODO(spec-037 Slice 2)` anchor at `test_inputs.py:531-540`; spec Slice 2
  lines 369-372, Test plan lines 1436-1441):
  - **`FileField` → `Upload` (required)**: a synthetic model with a plain
    required `FileField` (`attachment = models.FileField()`, no default/blank/null)
    builds a create input whose `attachment` field has inner type `Upload` and is
    NOT optional (`not _is_optional(fields["attachment"])`, `_inner_type(...) is
    Upload`). The python attr is `attachment` (NOT `attachment_id`); the GraphQL
    name camel-cases normally.
  - **`ImageField` → `Upload` (required)**: same shape for `avatar =
    models.ImageField()` — inner type `Upload`, required.
  - **`blank=True` / `null=True` widen to `Upload | None`**: a `blank=True` (or
    `null=True`) file column in the create input is optional with
    `default is UNSET` and inner type `Upload`; pin both the `blank=True` and the
    `null=True` cases (they take separate branches of `input_field_required`).
  - **Every partial input is `Upload | None`**: the same model's
    `operation_kind=PARTIAL` input has the file field optional + `UNSET`-defaulted
    regardless of requiredness (mirrors
    `test_partial_input_all_fields_optional_and_unset`,
    `test_inputs.py:222-233`).
  - **`Meta.fields` / `Meta.exclude` narrowing** includes/excludes the file
    column by model field name (a `fields=("id",)` drops the file column; a
    `fields=("id","attachment")` keeps it) — reuses the
    `editable_input_fields` narrowing already covered, applied to a file model.
  - **Lifted CR-6 merge override (the load-bearing new assertion)**: a file
    column whose python attr is in `overrides` is SKIPPED, exactly like a scalar
    — `build_mutation_input(FileModel, operation_kind=CREATE,
    primary_type=..., overrides=frozenset({"attachment"}))` produces an input
    with `"attachment" not in fields` while a non-overridden column still
    generates. This proves the file column now participates in the
    `Meta.input_class` merge override (the `036` carve-out is lifted). Mirror
    `test_consumer_override_skips_generated_field` (`test_inputs.py:402-413`) with
    a file column.
  - Update the file header comment block (`test_inputs.py:6-21`) so the
    "``Upload`` staged-seam ``NotImplementedError``" bullet (`test_inputs.py:14`)
    reflects the shipped positive mapping (cosmetic, in the same change).

- **`tests/mutations/test_resolvers.py`** (replace the
  `TODO(spec-037 Slice 2)` anchor at `test_resolvers.py:21-28`; spec Slice 2
  line 373, Test plan lines 1442-1449):
  - **Create assigns the file through the generic path (the verify-first
    assertion)**: a synthetic model with a `FileField` over `tmp_path` storage,
    driven through a `DjangoMutation(operation="create")` with a
    `SimpleUploadedFile` (`django.core.files.uploadedfile.SimpleUploadedFile`),
    writes the row and the saved `FieldFile` carries the uploaded name/content
    (assert the model row's `.attachment.name` / `.attachment.read()` after the
    mutation). This is the test that PROVES the generic `model(**attrs)` path
    carries the upload — if it passes, no resolver branch is added.
    NOTE: the existing `_schema` helper (`test_resolvers.py:103-109`) builds the
    schema **without** `config=strawberry_config()`; `Upload` still resolves
    because it is in `DEFAULT_SCALAR_REGISTRY` (Decision 5 / spec lines
    1399-1403). Worker 2 may reuse `_schema` as-is for file models, or build a
    local schema — either works; the no-config case is itself corroborating
    evidence for Decision 5 and need not be forced to use `strawberry_config()`.
  - **Partial update with `UNSET` leaves the stored file unchanged**: seed a row
    with a file, run a partial update that omits the file field (sets some other
    field), assert the stored `FieldFile` is byte-identical afterward.
  - **Partial update with a new upload replaces the file through the generic
    `setattr` path**: same row, partial update providing a new
    `SimpleUploadedFile`, assert the stored file is the new one.
  - **Explicit `null` on a `null=False` file column → field-keyed `FieldError`**:
    a partial update sending `null` for a `null=False` file column returns a
    `FieldError` keyed to the file field (via `_explicit_null_error`), null
    object slot, no top-level GraphQL error. Reuse `assert_mutation_field_error`
    (`test_resolvers.py:190-202`).
  - (Optional, if cheap) the `ImageField` model-validation failure path: a
    `DjangoMutation` over an `ImageField` does NOT itself sniff image content
    (spec lines 784-790) — so this is a *model-validator* concern, not promised;
    do not assert content rejection unless a model validator is declared. Skip
    unless Worker 2 finds it trivially in-scope.

Temp/scratch tests for Worker 3: none planned. If Worker 2 needs a scratch
harness to characterize whether the generic resolver path carries the
`SimpleUploadedFile` (the verify-first step), note it under
`docs/builder/temp-tests/slice-2/` for Worker 3 and delete before `built` — but
the permanent `test_resolvers.py` create test IS the verification, so a temp
harness is likely unnecessary.

### Implementation discretion items

- **`from ..scalars import Upload` vs `from .scalars import Upload` in
  `inputs.py`.** `inputs.py` lives at `mutations/inputs.py`; `scalars.py` is at
  the package root, so the correct relative form is `from ..scalars import
  Upload` (two dots), matching the existing `from ..exceptions import
  ConfigurationError` style. Worker 2 confirms the dot count against the actual
  module depth; the requirement is that `inputs.py` imports `Upload` from the
  package `scalars` module (one internal source), not directly from
  `strawberry.file_uploads.scalars`.
- **Docstring tightening on `_scalar_input_annotation` and the `overrides`
  param.** Whether to reword the now-shipped "Upload seam is handled by the
  caller" / "Slice 2 wires it" sentences (`inputs.py:295-296`, `inputs.py:448-449`)
  is Worker 2's call — both are accurate-enough as-is; tighten only if it reads
  cleaner. No contract change either way.
- **`Upload` test-field shape in `test_scalars.py`** (an `Upload`-typed argument
  on a query field vs. a field returning `Upload` vs. an input type) — any shape
  that forces Strawberry to register/resolve the `Upload` scalar under both
  configs is acceptable; Worker 2 picks the lightest. The load-bearing assertion
  is "schema builds and `Upload` is in the SDL under BOTH `strawberry_config()`
  and plain `StrawberryConfig()`".
- **Reusing `_schema` (no config) vs. a local `strawberry_config()` schema for
  the resolver file tests.** Worker 1 has assessed this: either is correct
  because `Upload` resolves from the default registry. Worker 2's choice; the
  no-config path is the more faithful demonstration of Decision 5 but is not
  mandated.
- **Docstring reword of `scalars.py:3`.** The exact replacement sentence is
  Worker 2's, provided the card number becomes `TODO-ALPHA-037-0.0.11` and
  `Upload` is described as re-exported (not "future").

### Spec slice checklist (verbatim)

- [x] Slice 2: write-side `Upload` input + the `Upload` re-export (per
  [Decision 5](#decision-5--re-export-upload-rather-than-register-it)
  /
  [Decision 6](#decision-6--write-side-input-mapping-the-mutation-seam-becomes-upload))
  - [x] [`scalars.py`][scalars]: re-export `Upload` (and `UploadDefinition`)
    from `strawberry.file_uploads.scalars` for the public surface. **Do not**
    add it to `_PACKAGE_SCALAR_MAP` — `Upload` already resolves via Strawberry's
    built-in `DEFAULT_SCALAR_REGISTRY`
    ([Decision 5](#decision-5--re-export-upload-rather-than-register-it)); fix
    the stale `TODO-ALPHA-035-0.0.11` reference in the module docstring to
    `TODO-ALPHA-037-0.0.11`.
  - [x] [`mutations/inputs.py`][mutations-inputs]: remove the staged seam at
    #"Upload staged seam (TODO-ALPHA-037-0.0.11)" — a `FileField` / `ImageField`
    input field now maps to `Upload`, required per the shipped per-field rule (a
    `blank=False` / `null=False` / no-default file column is required in the
    create `<Model>Input`, optional otherwise and in `<Model>PartialInput`),
    widened to `Upload | None` on `blank` / `null`. The Python attribute is the
    model field name (`attachment`, not `attachment_id` — file columns are
    scalar, not relation, inputs). The `036` file-column merge-override
    exception (the `NotImplementedError` preceding the override skip) is lifted:
    file columns now participate in the
    [`Meta.input_class`][glossary-input-type-generation] merge override like any
    scalar.
  - [x] [`mutations/resolvers.py`][mutations-resolvers]: **verify** the existing
    scalar assignment path already handles an uploaded file — the shipped
    pipeline passes scalar attrs into `model(**attrs)` (create) and `setattr`
    (update) before `full_clean()` / `save()`, and Django's `FileField`
    descriptor accepts an `UploadedFile` directly, so a file column likely needs
    **no** dedicated branch. Add a file-specific branch only if a test proves the
    generic scalar path fails ([Decision 6](#decision-6--write-side-input-mapping-the-mutation-seam-becomes-upload)).
    An omitted field (`UNSET`) leaves the file unchanged on partial update;
    explicit `null` on a `null=False` file column returns a `FieldError` via the
    shipped `_explicit_null_error` guard (omittable ≠ nullable — not a silent
    clear), and clearing is a [Risks](#risks-and-open-questions) item, not
    promised here.
  - [x] Package coverage: [`tests/test_scalars.py`][test-scalars] — an
    `Upload`-annotated field resolves through a schema built with
    `strawberry_config()` **and** through a plain `StrawberryConfig` (proving
    `Upload` rides Strawberry's default registry, not the package map); the
    existing `BigInt` collision test is untouched;
    [`tests/mutations/test_inputs.py`][test-mutations] — replace the
    staged-`NotImplementedError` tests with positive `FileField` / `ImageField`
    → `Upload` required/optional shapes, `| None` widening, and the lifted CR-6
    override; [`tests/mutations/test_resolvers.py`][test-mutations] — file
    assignment on create / partial update.

---

## Build report (Worker 2)

### Files touched

- `django_strawberry_framework/scalars.py` — added
  `from strawberry.file_uploads.scalars import Upload, UploadDefinition` to the
  import block; added a module `__all__ = ["BigInt", "Upload", "UploadDefinition",
  "strawberry_config"]` so the re-export is explicit at the module surface
  (the root `__init__.py` re-export + its `__all__` stay Slice 3 — untouched
  here). Rewrote the module docstring so it no longer calls `Upload` a "future"
  scalar and references `TODO-ALPHA-037-0.0.11` (not the stale `035`), noting the
  deliberate `BigInt`-vs-`Upload` registration contrast. `_PACKAGE_SCALAR_MAP`
  left byte-unchanged as `{BigInt: _BIGINT_SCALAR_DEFINITION}` (Decision 5).
- `django_strawberry_framework/mutations/inputs.py` — added
  `from ..scalars import Upload` (the package-internal source, two dots — matches
  the existing `from ..exceptions import ConfigurationError` style). In
  `build_mutation_input`, replaced the `Upload staged seam` comment block + the
  `isinstance(field, (FileField, ImageField)): raise NotImplementedError(...)`
  with an `elif isinstance(field, (models.FileField, models.ImageField)):` branch
  that sets `python_attr = field.name`, `graphql_name =
  graphql_camel_name(python_attr)`, `annotation = Upload` and falls through to the
  shared override-skip / `input_field_required` / `| None`-widening machinery —
  no parallel file-only logic. Tightened the now-accurate `_scalar_input_annotation`
  docstring sentence and the `overrides` param docstring (the latter's stale
  "Slice 1 … Slice 2 wires it" wording referred to spec-036's slices and the
  override wiring already shipped in `036`; reworded to present tense and noted
  the lifted CR-6 carve-out).
- `django_strawberry_framework/mutations/resolvers.py` — removed the two
  `TODO(spec-037 Slice 2)` anchor comment blocks in `_run_create` (before
  `model(**scalar_and_fk_attrs)`) and `_run_update` (before the `setattr` loop).
  **No production code changed** — the anchors were removed because the slice they
  named has shipped (the verification), per the verify-first contract.
- `tests/test_scalars.py` — removed the `TODO(spec-037 Slice 2)` anchor; added
  `Upload` to the `scalars` import and `import strawberry.file_uploads.scalars`;
  added six `Upload` tests (re-export identity, importable-from-scalars-module,
  `scalar_map` excludes `Upload`, resolves under `strawberry_config()`, resolves
  under plain `StrawberryConfig`). The `BigInt` collision test is untouched.
- `tests/mutations/test_inputs.py` — replaced the two staged-seam
  `NotImplementedError` tests + the `TODO(spec-037 Slice 2)` anchor with eight
  positive `Upload`-mapping tests; added `from
  django_strawberry_framework.scalars import Upload`; updated the file-header
  docstring bullet from the staged-seam wording to the positive mapping.
- `tests/mutations/test_resolvers.py` — removed the `TODO(spec-037 Slice 2)`
  anchor; added `SimpleUploadedFile` / `connection` / `models as djmodels` /
  `override_settings` imports; added the synthetic-`FileField`-model harness
  (`_make_asset_model` / `_build_asset_schema`) and four resolver tests proving
  the generic path (create assign, partial-update omit-unchanged, partial-update
  replace, explicit-null `FieldError`).

### Tests added or updated

- `tests/test_scalars.py::test_upload_is_strawberry_builtin_re_export_not_a_wrapper`
  — `Upload is strawberry.file_uploads.scalars.Upload` (a re-export, not a wrapper).
- `tests/test_scalars.py::test_upload_is_importable_from_top_level_scalars_module`
  — importable from `django_strawberry_framework.scalars`.
- `tests/test_scalars.py::test_strawberry_config_scalar_map_excludes_upload`
  — `BigInt in scalar_map` and `Upload not in scalar_map` (Decision 5).
- `tests/test_scalars.py::test_upload_field_resolves_under_strawberry_config_schema`
  and `…::test_upload_field_resolves_under_plain_strawberry_config` — an
  `Upload`-typed field builds + `"scalar Upload"` appears in the SDL under BOTH
  configs (the load-bearing default-registry pin).
- `tests/mutations/test_inputs.py` — `test_required_file_field_maps_to_upload`,
  `test_required_image_field_maps_to_upload`,
  `test_file_field_camel_cases_graphql_name`,
  `test_blank_file_field_widens_to_upload_optional`,
  `test_null_file_field_widens_to_upload_optional`,
  `test_partial_input_file_field_always_optional_upload`,
  `test_file_field_narrowed_by_meta_fields_and_exclude`,
  `test_file_field_consumer_override_skips_generated_upload_field` (the
  load-bearing lifted-CR-6 assertion). All pin inner type `Upload`, the
  `attachment`-not-`attachment_id` scalar attr, requiredness (both `blank` and
  `null` branches of `input_field_required`), and `UNSET` defaulting.
- `tests/mutations/test_resolvers.py` —
  `test_create_assigns_uploaded_file_through_generic_path`,
  `test_partial_update_omitting_file_leaves_stored_file_unchanged`,
  `test_partial_update_with_new_upload_replaces_file_through_setattr_path`,
  `test_explicit_null_on_non_nullable_file_column_is_field_error`. The first /
  third are the verify-first assertions proving `model(**attrs)` (create) and the
  `setattr` loop (update) carry a `SimpleUploadedFile` with no file-specific branch.

### Validation run

- `uv run ruff format .` — pass (1 file reformatted: `tests/mutations/test_resolvers.py`).
- `uv run ruff check --fix .` — pass (3 errors auto-fixed in
  `tests/mutations/test_resolvers.py`: import placement / trailing-comma layout;
  all in a file this slice owns).
- `git status --short` after both ruff invocations — modified:
  - **Slice-intended (stay; in `### Files touched`):**
    `django_strawberry_framework/mutations/inputs.py`,
    `django_strawberry_framework/mutations/resolvers.py`,
    `django_strawberry_framework/scalars.py`, `tests/test_scalars.py`,
    `tests/mutations/test_inputs.py`, `tests/mutations/test_resolvers.py`.
  - **Prior-slice work (Slice 1 baseline; NOT my churn — left untouched, not
    reverted, not owned here per the dispatch):**
    `django_strawberry_framework/types/base.py`,
    `django_strawberry_framework/types/converters.py`,
    `django_strawberry_framework/types/finalizer.py`,
    `django_strawberry_framework/types/resolvers.py`,
    `tests/types/test_base.py`, `tests/types/test_converters.py`,
    `tests/types/test_resolvers.py`, `pyproject.toml` (Pillow), `uv.lock`
    (Pillow), `docs/spec-037-upload_file_image_mapping-0_0_11.md` (Worker 1 /
    Slice 1 final-verify edits). Confirmed via `git diff --stat` that this slice
    made NO edit to any of these.
  - No unrelated tool churn to revert; ruff only touched a file this slice owns.
- Focused tests (no `--cov*`): `uv run pytest tests/test_scalars.py
  tests/mutations/test_inputs.py tests/mutations/test_resolvers.py --no-cov` —
  **132 passed**, no warnings. Broader permitted scope `uv run pytest
  tests/mutations/ tests/test_scalars.py --no-cov` — **199 passed**.

### Implementation notes

- **`elif` instead of a nested `if` inside the `else`.** The plan sketched the
  file branch inside the existing `else`; I lifted it to an `elif` peer of the
  `_is_relation(field)` branch (`if relation / elif file / else scalar`). This is
  cleaner than nesting a new `if/else` inside the old `else` and keeps all three
  triple-producing branches at one indent level. Behaviorally identical — the
  triple still falls through to the shared override-skip / requiredness /
  widening block below.
- **Resolver verify-first outcome: NO branch added.** The four resolver tests pass
  against the unchanged generic path — `model(**scalar_and_fk_attrs)` (create) and
  `setattr(instance, attr, value)` (update) feed Django's `FileField` descriptor a
  `SimpleUploadedFile` directly, `full_clean()` / `save()` accept it, and the saved
  `FieldFile` carries the uploaded name + content. Only the two TODO anchor
  comments were removed; production code is byte-unchanged.
- **Module `__all__` added to `scalars.py`.** The module had no `__all__`; I added
  one listing `BigInt` / `Upload` / `UploadDefinition` / `strawberry_config` so the
  public surface of the `scalars` module is explicit now that it re-exports an
  upstream symbol. This is the module-level surface only; the root `__init__.py`
  export is Slice 3.
- **`with row.attachment.open("rb") as fh:` for content reads.** A bare
  `FieldFile.read()` leaves the OS file handle open, which the suite's `-W error`
  ResourceWarning config (see worker memory) escalates to a test error. Wrapping
  the read in the `FieldFile`'s context manager closes the handle deterministically.
- **Per-call query strings in the resolver tests.** The synthetic model name is
  uniquified per call (`MutAsset<N>`), so the generated input type names are
  `MutAsset<N>Input` / `MutAsset<N>PartialInput`. `_build_asset_schema` returns the
  create/update query strings built from `model.__name__` rather than hardcoding a
  fixed `MutAssetInput` (which failed with `Unknown type 'MutAssetInput'`).
- **No-config `_schema` reuse for the resolver file tests** (Worker 1 discretion
  item). Used the existing `_schema` helper (builds WITHOUT
  `config=strawberry_config()`); `Upload` still resolves via the default registry,
  which is the more faithful demonstration of Decision 5.

### Notes for Worker 3

- The verify-first contract was honored: a resolver branch was added ONLY if a test
  proved the generic path failed; it did not fail, so no branch was added and the
  two TODO anchors were removed with production code unchanged. The create /
  partial-update file tests are the proof.
- The P0 read/write split is intact: `Upload` is NOT in `FIELD_OUTPUT_TYPE_MAP`,
  `inputs.py` imports only `Upload` (no `convert_field_output` /
  `FIELD_OUTPUT_TYPE_MAP`), and the read objects (`DjangoFileType` /
  `DjangoImageType`) never reach the input path.
- `_PACKAGE_SCALAR_MAP` is byte-unchanged (no `Upload` entry) — `test_scalars.py`
  pins `Upload not in strawberry_config().scalar_map`.
- The lifted-CR-6 carve-out is pinned by
  `test_file_field_consumer_override_skips_generated_upload_field` — a file column
  in `overrides` is now skipped exactly like a scalar.
- `__init__.py` was deliberately NOT touched (root re-export + `__all__` is Slice 3).
- No shadow file / `review_inspect.py` used (the changes are a re-export, a
  three-line annotation branch, and comment removals — below the helper trigger).
- No temp tests created (`docs/builder/temp-tests/slice-2/` is empty); the permanent
  `test_resolvers.py` create test IS the verification.

### Notes for Worker 1 (spec reconciliation)

- No spec gaps, conflicts, or unstated assumptions surfaced. The spec's
  verify-first hypothesis held exactly: the generic scalar-assignment path carries
  the upload with no dedicated branch.
- Minor: I added a module-level `__all__` to `scalars.py` (the plan did not
  explicitly call for it; it makes the `scalars` module surface explicit). The root
  `__init__.py` `__all__` change remains Slice 3 as planned — flagging only so the
  Slice 3 author knows `scalars.__all__` already lists `Upload` / `UploadDefinition`.

---

## Review (Worker 3)

Reviewed the Slice 2 diff (`scalars.py`, `mutations/inputs.py`, `mutations/resolvers.py`,
`tests/test_scalars.py`, `tests/mutations/test_inputs.py`, `tests/mutations/test_resolvers.py`)
against the spec's Slice 2 checklist (lines 330-374) and Decisions 5 (1057-1098) / 6 (1100-1165).
Slice 1's accepted source/test/`pyproject`/`uv.lock`/spec changes were filtered out via the
`### Files touched` list and confirmed not touched by this slice (`git diff --stat`). Static
inspection helper run on all three `mutations/`-adjacent source files (see `### Temp test
verification`). All findings below are resolved or `None.`; outcome is `review-accepted`.

### High:

None.

### Medium:

None.

### Low:

None.

### DRY findings

No DRY defects. The slice is a model of minimal-branch reuse:

- **`build_mutation_input` file branch reuses the shared machinery (`inputs.py::build_mutation_input`).**
  The new `elif isinstance(field, (models.FileField, models.ImageField))` branch produces only the
  `(python_attr, graphql_name, annotation)` triple (`field.name` / `graphql_camel_name(...)` /
  `Upload`) and falls through to the SAME `if python_attr in overrides: continue` skip,
  `input_field_required`, alias rule, and `annotation | None` + `default=UNSET` widening the scalar
  branch uses. There is NO parallel file-only requiredness predicate, no second optional widening, no
  second override skip — exactly the lifted-CR-6 mechanism (the old `raise` ran before the override
  skip; the triple now reaches it like any scalar). Worker 2's `elif`-peer-of-the-relation-branch
  shaping (vs the plan's nested-`if`) is cleaner and behaviorally identical.
- **`Upload` has one package-internal source.** `inputs.py` imports `Upload` from `..scalars`
  (the re-export), not a second direct `strawberry.file_uploads.scalars` import — one internal source
  of the symbol.
- **No second `Upload` scalar / no `_PACKAGE_SCALAR_MAP` entry.** `_PACKAGE_SCALAR_MAP` is
  byte-unchanged `{BigInt: _BIGINT_SCALAR_DEFINITION}` (`scalars.py #"_PACKAGE_SCALAR_MAP"`); the
  re-export is a pure `from strawberry.file_uploads.scalars import Upload, UploadDefinition`.
- **No divergent write path.** Verify-first honored: the four resolver tests pass against the unchanged
  generic `model(**attrs)` (create) / `setattr` (update) path; only the two TODO anchor comments were
  removed, production code byte-unchanged. No file-specific resolver branch was added.
- **P0 read/write split intact.** `Upload` is NOT in `FIELD_OUTPUT_TYPE_MAP`; `inputs.py` imports only
  `Upload` (not `convert_field_output` / `FIELD_OUTPUT_TYPE_MAP`); the read objects never reach the
  input path; `SCALAR_MAP`'s `FileField: str` / `ImageField: str` rows are untouched.
- **`UploadDefinition` re-export with no live reader** is intentional and spec-mandated (Decision 5
  line 1066 requires re-exporting both names) — verified as a deliberate public-surface re-export, not
  dead code. Not a finding.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` is EMPTY — Slice 2 adds no root export (the root
`Upload` / `DjangoFileType` / `DjangoImageType` re-export + `__all__` is Slice 3, spec line 379-381).
Correct.

Worker 2 added a module-level `__all__ = ["BigInt", "Upload", "UploadDefinition", "strawberry_config"]`
to `scalars.py` itself (`scalars.py #"__all__"`). This is the `scalars` MODULE surface, not the root
`__init__.py` public surface, so it does not breach the "no new root export this slice" gate. It is
appropriate: all four names are the genuine importable surface of the module, and Decision 5 (line 1066)
explicitly directs `scalars.py` to re-export both `Upload` and `UploadDefinition`. It does not pre-empt
Slice 3 (which adds the ROOT export). No issue; flagged for the Slice 3 author's awareness only (already
recorded in Worker 2's notes to Worker 1).

### CHANGELOG sanity

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces. (The `scalars.py` /
`inputs.py` docstring rewrites and the test-file header-comment edits are code-comment cosmetics within
the slice's own source files, not the standing doc / release / KANBAN surfaces this subsection governs.
Confirmed the stale `TODO-ALPHA-035-0.0.11` docstring ref in `scalars.py` is fixed to
`TODO-ALPHA-037-0.0.11`, and no stale `035` reference remains in any slice file.)

### What looks solid

- **Spec sub-checklist fully landed.** All four `- [x]` boxes in the Plan's verbatim checklist are
  truly reflected in the diff: (1) `scalars.py` re-export + no `_PACKAGE_SCALAR_MAP` entry + `035`→`037`
  docstring fix; (2) `inputs.py` seam→`Upload` with the per-field requiredness rule, `attachment` (not
  `attachment_id`) scalar naming, and the lifted CR-6 carve-out; (3) `resolvers.py` verify-first
  (production byte-unchanged, anchors removed); (4) the three test files' coverage. No over-tick, no
  silent un-addressed sub-check.
- **The load-bearing Decision-5 test is NOT vacuous.** I confirmed by temp test (see below) that an
  unregistered `NewType` scalar field FAILS to build under a plain `StrawberryConfig()`, while the real
  `Upload` builds and `"scalar Upload"` appears in the SDL — so
  `test_upload_field_resolves_under_plain_strawberry_config` would genuinely fail if `Upload` were not
  in `DEFAULT_SCALAR_REGISTRY`. `Upload in DEFAULT_SCALAR_REGISTRY` confirmed `True` at the pinned
  upstream version. The existing `BigInt` `extra_scalar_map` collision test
  (`test_strawberry_config_collision_with_package_scalar_raises_value_error`, `test_scalars.py:323`) is
  untouched.
- **Requiredness tests pin the actual nullability, not field existence.** `test_inputs.py` asserts
  `_inner_type(fields["attachment"]) is Upload` AND `not _is_optional(...)` for required, and
  `_is_optional(...)` + `default is UNSET` for the widened cases — `_is_optional` checks
  `StrawberryOptional`, so these distinguish `Upload!` from `Upload`. Both `blank=True` and `null=True`
  branches of `input_field_required` are pinned separately; the partial-input case is pinned for a
  required-on-create column; `attachment_id` is asserted absent.
- **The lifted-CR-6 test has a control assertion.**
  `test_file_field_consumer_override_skips_generated_upload_field` asserts the overridden file column is
  ABSENT (`"attachment" not in fields`) AND that a non-overridden column still generates
  (`"name" in fields`) — non-vacuous.
- **Verify-first is backed by real pipeline tests, not prose.** The four `test_resolvers.py` tests drive
  `schema.execute_sync` end-to-end over a synthetic `managed=False` `FileField` model with
  `override_settings(MEDIA_ROOT=tmp_path)`, and read back the saved `FieldFile` content
  (`with row.attachment.open("rb")`), proving create assignment and partial-update replacement through
  the generic path. The `UNSET`-leaves-unchanged and explicit-`null`→`FieldError` (via
  `_explicit_null_error`) contracts are both pinned, the latter additionally asserting the stored file
  is untouched.
- **Tests REPLACED, not appended.** The two staged-`NotImplementedError` tests and the
  `TODO(spec-037 Slice 2)` anchors are removed from `test_inputs.py` / `test_scalars.py` /
  `test_resolvers.py` (confirmed in the diff) — no stale fail-loud assertion left alongside the positive
  shapes. Cross-tree grep found no other test tree referencing the old seam behavior.
- **`_explicit_null_error` behavioral claim traced, not trusted.** I traced
  `_decode_relations` (`resolvers.py`): a file column (plain `field.name`, not `<name>_id`) is absent
  from both `m2m_by_name` and `fk_by_attr`, so it reaches the scalar branch and `_explicit_null_error`
  fires on a provided `None` over a `null=False` column before any DB work — no earlier short-circuit
  swallows it. `UNSET` is stripped at the top of the loop, so an omitted file never reaches `setattr`.

### Temp test verification

- Static inspection helper run (required — slice touches `mutations/`):
  `python scripts/review_inspect.py django_strawberry_framework/mutations/inputs.py --output-dir docs/shadow`
  (and `resolvers.py` / `scalars.py`). Walked every Django/ORM marker: in `inputs.py` (lines 184, 276)
  and `resolvers.py` (lines 213, 307, 519, 646, 668, 672, 675) every `_meta` marker is pre-existing
  code untouched by this slice (the diff only added one `elif` triple to `inputs.py` and removed two
  comment blocks from `resolvers.py`). The `build_mutation_input` hotspot (107 lines / 12 branches) got
  Medium-tier complexity attention: the added `elif` is 3 logic lines that fall through to shared
  machinery and do not deepen the control flow. The new `isinstance()` call of interest (`inputs.py`
  line 479) is the file-field discriminator — appropriate. No new repeated string literal introduced.
- Temp test: `docs/builder/temp-tests/slice-2/test_nonvacuity.py` (created during review, deleted
  after) — proved the Decision-5 default-registry test is distinguishing: an unregistered `NewType`
  scalar field raises on a plain `StrawberryConfig()` schema build, the real `Upload` builds, and
  `Upload in DEFAULT_SCALAR_REGISTRY`. 3/3 passed. Disposition: DELETED — the permanent
  `test_scalars.py` tests already pin the positive behavior; the temp test only confirmed
  non-vacuity, which needs no permanent home (a negative-control test asserting an unrelated NewType
  fails is not a Slice-2 contract).
- Focused permanent-suite runs (no `--cov*`):
  `uv run pytest tests/test_scalars.py tests/mutations/test_inputs.py tests/mutations/test_resolvers.py --no-cov`
  → 132 passed. `ruff format --check` and `ruff check` clean on all six slice files.

### Notes for Worker 1 (spec reconciliation)

- No spec reconciliation required. The spec's verify-first hypothesis (Decision 6 lines 1113-1119) held
  exactly: the generic scalar-assignment path carries the `UploadedFile` with no dedicated resolver
  branch, backed by real `execute_sync` tests.
- For final-verification awareness only (no action): Worker 2 added a module-level `__all__` to
  `scalars.py` that already lists `Upload` / `UploadDefinition`; the Slice 3 root `__init__.py` export
  is still pending as planned. This is spec-aligned (Decision 5 line 1066) and not a drift.

### Review outcome

`review-accepted`. All spec-required Slice 2 behaviors are reflected in the diff with load-bearing
tests; the four sub-checklist boxes truly landed; the P0 read/write split, the no-`_PACKAGE_SCALAR_MAP`
contract, the lifted CR-6 carve-out, and the verify-first no-branch outcome are all pinned. No High,
Medium, or Low findings. No findings escalated to Worker 1.

---

## Final verification (Worker 1)

Audited the six-file Slice 2 diff (`git diff -- django_strawberry_framework/scalars.py
django_strawberry_framework/mutations/inputs.py django_strawberry_framework/mutations/resolvers.py
tests/test_scalars.py tests/mutations/test_inputs.py tests/mutations/test_resolvers.py`) against the
Plan's verbatim checklist, the DRY contract, and Decisions 5 / 6. Confirmed Slice 1's accepted
`types/*` + `tests/types/*` + `pyproject.toml`/`uv.lock` + Slice 1 spec edit are prior-accepted work,
not part of this verification.

### 1. Spec slice checklist audit (verbatim boxes)

All four `- [x]` sub-checks in the Plan's `### Spec slice checklist (verbatim)` were ticked by Worker 2.
I audited each against the diff — every contract truly landed; no box un-ticked, no box over-ticked, no
remaining `- [ ]`:

- **`scalars.py` re-export `- [x]` — CONFIRMED.** `from strawberry.file_uploads.scalars import Upload,
  UploadDefinition` lands at `scalars.py #"from strawberry.file_uploads.scalars import"`;
  `_PACKAGE_SCALAR_MAP` is byte-unchanged `{BigInt: _BIGINT_SCALAR_DEFINITION}` (no `Upload` entry,
  Decision 5); the module docstring no longer calls `Upload` "future" and the stale
  `TODO-ALPHA-035-0.0.11` ref is fixed to `TODO-ALPHA-037-0.0.11` (`scalars.py:3-7`,
  `scalars.py #"TODO-ALPHA-037-0.0.11"`). No stale `035` ref remains anywhere in the slice files.
- **`mutations/inputs.py` seam → `Upload` `- [x]` — CONFIRMED.** The `NotImplementedError` staged seam
  is gone; `build_mutation_input` now carries an `elif isinstance(field, (models.FileField,
  models.ImageField))` branch (`inputs.py::build_mutation_input #"elif isinstance(field, (models.FileField"`)
  producing only the `(python_attr=field.name, graphql_name=graphql_camel_name(...), annotation=Upload)`
  triple and falling through to the shared `if python_attr in overrides: continue` skip +
  `input_field_required` + `annotation | None` / `default=UNSET` widening. Python attr is the plain field
  name (`attachment`, never `attachment_id`); the CR-6 carve-out is lifted by ordering alone.
- **`mutations/resolvers.py` verify-first `- [x]` — CONFIRMED.** Production code is byte-unchanged:
  `_run_create` still builds `model(**scalar_and_fk_attrs)` and `_run_update` still runs the
  `setattr(instance, attr, value)` loop. Only the two `TODO(spec-037 Slice 2)` anchor comment blocks
  were removed. The verify-first outcome (generic path proven sufficient, NO branch added) is backed by
  four real `execute_sync` resolver tests — exactly the spec's `Add a file-specific branch only if a
  test proves the generic scalar path fails` contract.
- **Package coverage `- [x]` — CONFIRMED.** `tests/test_scalars.py` adds the re-export-identity,
  importable-from-module, `scalar_map`-excludes-`Upload`, and resolves-under-both-configs tests; the
  `BigInt` collision test is untouched. `tests/mutations/test_inputs.py` REPLACES the two
  `NotImplementedError` tests with eight positive `Upload`-mapping tests (required, image-required,
  camelCase alias, `blank` widen, `null` widen, partial always-optional, `Meta.fields`/`exclude`
  narrowing, and the load-bearing lifted-CR-6 override skip). `tests/mutations/test_resolvers.py` adds
  the create-assign / partial-omit-unchanged / partial-replace / explicit-null-`FieldError` tests.

### 2. DRY check (across Slice 2 and against accepted Slice 1)

No new duplication. The file branch in `build_mutation_input` reuses the shipped
requiredness/override/widening machinery verbatim — it produces only the triple and falls through to the
single `if python_attr in overrides: continue` skip, the single `input_field_required` predicate, and
the single `annotation | None` + `default=UNSET` widening the scalar branch uses. No parallel file-only
requiredness predicate, no second optional widening, no second override skip. `Upload` has one
package-internal source (`inputs.py` imports from `..scalars`, the re-export — not a second direct
`strawberry.file_uploads.scalars` import).

The standing P0 read/write split holds, verified by grep against accepted Slice 1:

- `Upload` is **never** in `FIELD_OUTPUT_TYPE_MAP` — `grep "Upload" types/converters.py` returns nothing.
- The read objects (`DjangoFileType` / `DjangoImageType` / `convert_field_output` / `FIELD_OUTPUT_TYPE_MAP`)
  **never** reach the input path — `inputs.py` imports only `Upload` from `..scalars`.
- `SCALAR_MAP`'s `FileField: str` / `ImageField: str` rows (`types/converters.py:195-196`) stay in place,
  serving only the filter-input path; the read map (`FIELD_OUTPUT_TYPE_MAP`, `types/converters.py:207-208`)
  is separate. Neither side leaks the other's representation.

### 3. Existing tests still pass

`uv run pytest tests/mutations/ tests/test_scalars.py --no-cov` → **199 passed** (no warnings, no
`--cov*` flag). Includes the 13 net-new Slice 2 tests across the three test files.

Boundary checks (Slice 3 / Slice 4 scope not crossed): `git diff -- django_strawberry_framework/__init__.py`
is **empty** (root re-export + root `__all__` correctly deferred to Slice 3); `pyproject.toml` `version`
is still `0.0.10` and `__init__.py` `__version__` is still `0.0.10` (the `0.0.11` bump is Slice 4's
exclusive job — correct).

### 4. Spec reconciliation

The spec's Slice 2 `mutations/resolvers.py` sub-bullet (spec lines 353-359) already reads
"**verify** … so a file column likely needs **no** dedicated branch. Add a file-specific branch **only
if a test proves the generic scalar path fails**." That phrasing accurately reflects the shipped reality
— the generic `model(**attrs)` / `setattr` path was proven sufficient by the four resolver tests and no
branch was added. **No tightening note is needed**: the conditional ("only if a test proves … fails") is
the correct contract for the as-shipped outcome, and a "the generic path was proven sufficient" claim
already lives in the build/review/verification artifact (the per-cycle record), which is the right home
for the build-outcome fact rather than the standing spec. Decision 6 (spec lines 1113-1119, 1161-1165)
likewise states the verify-first contract correctly.

Worker 2's module-level `__all__` on `scalars.py` (`["BigInt", "Upload", "UploadDefinition",
"strawberry_config"]`) warrants **no spec note**: it is the `scalars` MODULE surface, not the root
`__init__.py` public surface the spec's Decision 7 / Slice 3 governs, and Decision 5 (spec line 1066)
already directs `scalars.py` to re-export both `Upload` and `UploadDefinition` — so all four listed names
are the genuine, spec-sanctioned importable surface of the module. It does not pre-empt Slice 3's root
export. No contract drift.

The only spec edit this pass is the per-spawn status-line refresh (see below).

### Final status: `final-accepted`

### Summary

Slice 2 ships the write half of the file/image story plus the public `Upload` re-export.
`scalars.py` re-exports Strawberry's built-in `Upload` / `UploadDefinition` (with a module `__all__`) and
deliberately adds NO `_PACKAGE_SCALAR_MAP` entry — `Upload` rides Strawberry's `DEFAULT_SCALAR_REGISTRY`
(the contrast with package-custom `BigInt`). `build_mutation_input` maps `FileField` / `ImageField` to
`Upload` via a minimal `elif` branch that falls through to the shared requiredness / override-skip /
`| None`-widening machinery, lifting the spec-036 CR-6 file-column merge-override carve-out by ordering
alone. The write resolver is byte-unchanged: the verify-first hypothesis held — the generic
`model(**attrs)` (create) / `setattr` (update) path carries an `UploadedFile` directly through Django's
`FileField` descriptor, proven by four `execute_sync` resolver tests, so no file-specific branch was
added (the two TODO anchors were removed because the slice they named shipped). The P0 read/write split
is intact and 199 focused tests pass.

### Spec changes made (Worker 1 only)

- `docs/spec-037-upload_file_image_mapping-0_0_11.md` line 39 (status/header block): changed
  `build under way (Slice 1 final-accepted, Slices 2–4 pending)` →
  `build under way (Slices 1–2 final-accepted, Slices 3–4 pending)`. Reason: per-spawn status-line
  re-verification (worker-1.md "Spec status-line re-verification") — Slice 2 reaches `final-accepted`
  in this pass, so the prior line listing it as pending is now stale. Prose-only; no Decision contract
  changed.
- No other spec edit. The resolver sub-bullet's "verify … add a branch only if a test proves the generic
  scalar path fails" wording already matches the shipped reality (generic path proven sufficient, no
  branch); Worker 2's module-level `scalars.__all__` is the module surface Decision 5 already sanctions
  and needs no spec note. (See "Spec reconciliation" above.)
