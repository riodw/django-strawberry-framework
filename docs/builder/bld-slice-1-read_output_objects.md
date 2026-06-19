# Build: Slice 1 — read-side output objects + FIELD_OUTPUT_TYPE_MAP + file-column resolver

Spec reference: `docs/spec-037-upload_file_image_mapping-0_0_11.md` (lines 265-323, the Slice 1 block of `## Slice checklist`; governed by Decision 3 lines 843-966 and Decision 4 lines 968-1043)
Status: final-accepted

## Plan (Worker 1)

This slice ships the **read** half of the file/image story: two resolver-backed
output objects (`DjangoFileType` / `DjangoImageType`), a NEW read-only
`FIELD_OUTPUT_TYPE_MAP` consulted by a NEW `convert_field_output` wrapper, the
`blank`-aware object nullability in `_build_annotations`, and a generated
file-column parent resolver attached in the same finalizer window as the
relation resolvers. The P0 invariant for the whole slice: the file mapping lives
on a NEW map and a NEW wrapper, kept **off** `SCALAR_MAP` / `scalar_for_field`,
so the shared filter-input path is byte-for-byte unaffected and no output object
ever reaches a GraphQL input.

The four `types/` files carry pre-placed TODO anchors naming this slice, which
land the implementation:
- `converters.py` #"TODO(spec-037 Slice 1)" (two anchors: one before `SCALAR_MAP`, one inside `convert_scalar`)
- `base.py::_build_annotations` #"TODO(spec-037 Slice 1)"
- `resolvers.py` #"TODO(spec-037 Slice 1)" (two anchors)
- `finalizer.py::finalize_django_types` #"TODO(spec-037 Slice 1)"
The matching test-file anchors are in `tests/types/test_converters.py`,
`tests/types/test_resolvers.py`, `tests/types/test_base.py`.

### DRY analysis

- **Existing patterns reused.**
  - The `type(field).__mro__` walk for field-class → value lookup already exists
    twice: `django_strawberry_framework/types/converters.py::scalar_for_field`
    (`converters.py:146-148`) and the equivalent walk inside
    `convert_scalar`. `FIELD_OUTPUT_TYPE_MAP`'s lookup mirrors this MRO walk
    exactly (test `type(field).__mro__`, return the first class found in the new
    map), so `ImageField` (a `FileField` subclass) resolves to `DjangoImageType`
    because its own row precedes `FileField` in its MRO — identical mechanics to
    why `models.PositiveBigIntegerField` resolves to `BigInt` before
    `IntegerField` in `SCALAR_MAP`. The new lookup is a small private helper
    (e.g. `_field_output_type_for(field)`) so the walk is written once, not
    inlined into both `convert_field_output` and any future caller.
  - The `force_nullable` tri-state is already computed per field in
    `django_strawberry_framework/types/base.py::_build_annotations`
    (`base.py:1624-1629`: `nullable_overrides` → `True`, `required_overrides` →
    `False`, else `None`) and threaded into `convert_scalar(...,
    force_nullable=force_nullable)` (`base.py:1638-1642`). `convert_field_output`
    takes the **same** keyword-only `force_nullable: bool | None = None` shape as
    `convert_scalar` (`converters.py:156-161`), so `_build_annotations` swaps one
    call for the other with the tri-state passed through unchanged — no new
    nullability code path in `base.py`.
  - The resolver-attachment mechanics are established by
    `django_strawberry_framework/types/resolvers.py::_attach_relation_resolvers`
    (`resolvers.py:418-438`): iterate `definition.selected_fields`, skip
    `skip_field_names`, `setattr(cls, field.name,
    strawberry.field(resolver=resolver))`. `_attach_file_resolvers` is the
    structural twin (iterate the same `selected_fields`, skip non-file and
    skipped names, attach a generated parent resolver). The resolver name-stamp
    helper `resolvers.py::_name_resolver` (`resolvers.py:255-265`,
    `resolver.__name__ = f"resolve_<field_name>"`) is reused so GraphiQL traces
    stay readable, matching the three relation-resolver rename sites.
  - The finalizer call site is the existing Phase-2 relation-resolver loop
    `django_strawberry_framework/types/finalizer.py::finalize_django_types`
    (`finalizer.py:622-638`); `_attach_file_resolvers` is called inside the
    **same loop body** immediately after `_attach_relation_resolvers`, before
    Phase 2.5 interface injection (`finalizer.py:640-649`) and Phase 3
    `strawberry.type(...)` freeze (`finalizer.py:709-713`). No new loop, no new
    finalizer phase.
  - `DjangoTypeDefinition` already records both `selected_fields`
    (`base.py:628`) and `consumer_authored_fields` (`base.py:632`) and
    `consumer_assigned_relation_fields` (`base.py:635`), so the file pass reads
    existing definition state — nothing new is stored on the definition.
  - Synthetic-model test infrastructure is the established
    `connection.schema_editor().create_model(...)` /
    `delete_model(...)` pattern under a `managed = False` model with a unique
    `app_label` (`tests/test_relay_connection.py:197-247`,
    `tests/test_permissions.py`), reused verbatim for the resolver / storage
    tests; converter-only tests need no table (Decision 9, spec lines 1240-1250).

- **New helpers justified.** Four net-new symbols, each with one responsibility,
  all in `types/converters.py` except the resolver pair:
  - `_safe_file_attr(file_file, attr)` — **the single subfield storage guard**
    shared by every nullable subfield resolver on both `DjangoFileType` and
    `DjangoImageType`. Single responsibility: read `getattr(file_file, attr)` and
    return `None` on the **narrow** catch (`ValueError` / `OSError` / storage
    `NotImplementedError`), letting everything else (including
    `SuspiciousFileOperation`, a `SuspiciousOperation` not a `ValueError`/`OSError`)
    propagate. Call sites: `path` / `size` / `url` on `DjangoFileType`, plus
    `width` / `height` on `DjangoImageType` — five sites, one guard. This is the
    DRY anchor the build plan pins (`build-037` line 28).
  - `DjangoFileType` / `DjangoImageType` — the two `@strawberry.type` output
    objects with resolver-backed fields. `DjangoImageType(DjangoFileType)`
    inherits `name`/`path`/`size`/`url` and only adds `width`/`height`, so the
    four shared subfields are defined once (the subclass avoids a second copy of
    `name`/`path`/`size`/`url`).
  - `FIELD_OUTPUT_TYPE_MAP` — module-level `dict[type[models.Field], type]`
    (`models.ImageField → DjangoImageType` **before** `models.FileField →
    DjangoFileType`). The single source of "which Django file column → which
    output object", consulted only by `convert_field_output` and
    `_attach_file_resolvers` (both via the shared `_field_output_type_for`
    helper).
  - `convert_field_output(field, type_name, *, force_nullable=None)` — **the
    single read-output wrapper** the build plan pins (`build-037` line 28). Single
    responsibility: if the column resolves via `FIELD_OUTPUT_TYPE_MAP`, return the
    output object widened to `<object> | None` on the file-aware effective
    nullability; otherwise **delegate to `convert_scalar`** for true scalars.
    This keeps `convert_scalar` / `scalar_for_field` scalar-only.

- **Duplication risk avoided.**
  - **A second copy of the empty-file guard.** Risk: the parent resolver and the
    subfield resolvers both writing `try/except`. Avoided by the Decision 4 split
    — the parent resolver does object nullability only (`return None if not value
    else value`, no `try/except`), and the per-property catch lives **only** in
    `_safe_file_attr`, called by every nullable subfield. One catch list, one
    place.
  - **The `("name", "path", "size", "url")` literal repeated.** Risk: listing the
    subfield names in the type body, in the resolver attach, in a map, etc.
    Avoided: subfield names exist **only** as the resolver method names on
    `DjangoFileType` / `DjangoImageType`; Strawberry derives the GraphQL fields
    from those methods. There is no separate name tuple to keep in sync, and
    `DjangoImageType` inherits the four base subfields rather than re-declaring
    them. `_safe_file_attr` receives each attr name as the literal argument at the
    single call site inside each subfield resolver — never as a shared tuple
    iterated elsewhere.
  - **A parallel file-resolver attachment path.** Risk: `_attach_file_resolvers`
    diverging from `_attach_relation_resolvers` (different skip semantics,
    different name-stamping). Avoided: `_attach_file_resolvers` is the structural
    twin — same `selected_fields` iteration, same `_name_resolver` stamp, same
    `strawberry.field(resolver=...)` attach — differing only in **what it
    selects** (file/image columns in `FIELD_OUTPUT_TYPE_MAP`) and **what it
    skips** (`consumer_authored_fields`, deliberately broader than the relation
    pass's `consumer_assigned_relation_fields`).
  - **File logic drifting into the scalar/filter path.** Risk: adding the
    `FIELD_OUTPUT_TYPE_MAP` lookup inside `convert_scalar` or `scalar_for_field`.
    Avoided by Decision 3: the lookup is owned by the new `convert_field_output`
    wrapper; `convert_scalar` / `scalar_for_field` / the `FileField: str` /
    `ImageField: str` `SCALAR_MAP` rows stay exactly as they are. The
    filter-input converter
    (`django_strawberry_framework/filters/inputs.py::_scalar_from_model_field`,
    `inputs.py:253-269`) calls `scalar_for_field` (`inputs.py:267-269`), which
    walks `SCALAR_MAP` only and never sees `FIELD_OUTPUT_TYPE_MAP` — so a
    `FilterSet` over a file column still yields `str`. A package test pins this
    (named below).

### Implementation steps

Line numbers are pin-at-write-time navigational hints; verify against current
source before editing (Worker 2 may find them shifted).

1. **`django_strawberry_framework/types/converters.py` — define the read-output
   surface.** Replace the TODO anchor at `converters.py:54-64` (before
   `SCALAR_MAP`) with:
   - `_safe_file_attr(file_file, attr)` — the shared subfield guard. Narrow catch
     `(ValueError, OSError, NotImplementedError) → None`; everything else
     propagates. A short comment notes the deliberate exclusion of
     `SuspiciousFileOperation` (Decision 4, spec lines 1002-1012) and why the
     catch list is narrow (spec lines 1017-1018). This is one of the three
     comment sites the spec authorizes (spec lines 1314-1316).
   - `DjangoFileType` (`@strawberry.type`) with resolver-backed fields: `name:
     str` reads the bound file directly (a stored string, present whenever the
     object is non-null — no guard); `path: str | None`, `size: int | None`,
     `url: str | None` each `return _safe_file_attr(self, "<attr>")`. The `self`
     of each subfield resolver IS the bound `FieldFile` the parent resolver
     returned (Decision 4, spec lines 987-1000). Confirm the resolver-backed
     `@strawberry.field`-method shape produces the correct nullability; the
     subfield resolver's return annotation (`str | None` etc.) carries it.
   - `DjangoImageType(DjangoFileType)` — adds `width: int | None`, `height: int |
     None`, each through `_safe_file_attr(self, "<attr>")`. Inherits the four base
     subfields.
   - A short comment on the nullable-subfield rationale (spec lines 1314-1316,
     the second authorized comment site).
2. **`converters.py` — add the read map.** After the two types, add
   `FIELD_OUTPUT_TYPE_MAP: dict[type[models.Field], type] = {models.ImageField:
   DjangoImageType, models.FileField: DjangoFileType}` (ImageField first so the
   MRO walk hits it before `FileField`). Keep the existing `SCALAR_MAP`
   `models.FileField: str` / `models.ImageField: str` rows (`converters.py:93-94`)
   unchanged; trim the now-satisfied TODO note at `converters.py:90-92` to a
   one-line rationale comment explaining the split (the third authorized comment
   site).
3. **`converters.py` — add `convert_field_output` + the lookup helper.** Add a
   private `_field_output_type_for(field)` doing the MRO walk over
   `FIELD_OUTPUT_TYPE_MAP` (returns the matched output type or `None`), and the
   public `convert_field_output(field, type_name, *, force_nullable=None)`:
   - `output_type = _field_output_type_for(field)`.
   - If `output_type is None`: `return convert_scalar(field, type_name,
     force_nullable=force_nullable)` (delegation — the scalar path is unchanged).
   - Else compute file-effective nullability: `force_nullable` when set, else
     `bool(field.null or field.blank)` (Decision 4 object nullability, spec lines
     972-982). Return `output_type | None` when nullable, else `output_type`.
   - Remove the in-`convert_scalar` TODO anchor at `converters.py:233-240`
     **without adding any file logic to `convert_scalar`** — the routing lives in
     `convert_field_output`, called from `_build_annotations` (step 4), so
     `convert_scalar` stays scalar-only. Update the module docstring's
     "Public surface" list (`converters.py:3-32`) to add `convert_field_output` /
     `FIELD_OUTPUT_TYPE_MAP` / `DjangoFileType` / `DjangoImageType` and to state
     that file/image columns are read-output-only (off the scalar/filter path).
4. **`django_strawberry_framework/types/base.py::_build_annotations` — call the
   wrapper.** At `base.py:1638-1642`, change the non-relation-column call from
   `convert_scalar(field, cls.__name__, force_nullable=force_nullable)` to
   `convert_field_output(field, cls.__name__, force_nullable=force_nullable)`,
   and update the `from .converters import convert_scalar` import
   (`base.py:58`) to import `convert_field_output` (keep `convert_scalar` import
   only if still referenced elsewhere; grep — `base.py` references it at
   `base.py:1638` and in docstrings/comments at 452, 1486, 1510, 1620, so the
   import stays). The `force_nullable` tri-state at `base.py:1624-1629` is
   **unchanged** (it is computed exactly as today and passed through). Replace the
   TODO anchor at `base.py:1630-1637` with a one-line note that
   `convert_field_output` owns the file/image branch. The `consumer_authored_fields`
   short-circuit at `base.py:1603-1609` already skips a consumer `attachment: str`
   override, so no object type is generated for it.
5. **`django_strawberry_framework/types/resolvers.py` — define the file parent
   resolver + attach helper.** Replace the two TODO anchors (`resolvers.py:268-275`
   and `resolvers.py:441-444`) with:
   - `_make_file_resolver(field)` → a `def file_resolver(root, info)` closure
     that returns `None` for a falsy `FieldFile` (`value = getattr(root,
     field.name); return value if value else None`) and otherwise the bound
     `FieldFile` (object nullability only — no subfield access, no `try/except`).
     Stamp it via `_name_resolver(file_resolver, field.name)` for trace
     stability. The resolver takes `(root, info)` to match the relation-resolver
     signature even though `info` is unused here (Strawberry injects it).
   - `_attach_file_resolvers(cls, fields, *, skip_field_names=frozenset())` — the
     twin of `_attach_relation_resolvers` (`resolvers.py:418-438`): iterate
     `fields`, `continue` for relations (`field.is_relation`), `continue` for
     `field.name in skip_field_names`, `continue` when
     `_field_output_type_for(field) is None` (not a file/image column), else
     `setattr(cls, field.name, strawberry.field(resolver=_make_file_resolver(field)))`.
     Import `_field_output_type_for` (or `FIELD_OUTPUT_TYPE_MAP` + a local walk —
     prefer importing the shared helper) from `.converters`. Confirm no import
     cycle: `resolvers.py` currently imports nothing from `converters.py`; a
     `from .converters import _field_output_type_for` is one-directional
     (`converters.py` does not import `resolvers.py`), so it is cycle-safe — if a
     cycle is discovered at build time, fall back to a function-local import
     inside `_attach_file_resolvers` (note for Worker 2).
6. **`django_strawberry_framework/types/finalizer.py::finalize_django_types` —
   call the file pass.** Replace the TODO anchor at `finalizer.py:630-638`
   (inside the Phase-2 loop, immediately after the `_attach_relation_resolvers`
   call at `finalizer.py:625-629`) with a `_attach_file_resolvers(type_cls,
   definition.selected_fields, skip_field_names=definition.consumer_authored_fields)`
   call. Add `_attach_file_resolvers` to the `from .resolvers import
   _attach_relation_resolvers` import (`finalizer.py:78`). The skip set is
   `consumer_authored_fields` (annotation **and** assigned overrides), deliberately
   **broader** than the relation pass's `consumer_assigned_relation_fields`
   (`finalizer.py:628`) — so a consumer `attachment: str` annotation-only override
   (already skipped in `_build_annotations`) also gets no generated file resolver
   (Decision 3, spec lines 911-924). Interface-injection order (`finalizer.py:640-649`)
   is unchanged.
7. **Pillow test dependency (test-infra prerequisite for the image-dimension
   tests, not a checklist sub-bullet).** Pillow is NOT currently installed
   (verified: `import PIL` → `ModuleNotFoundError`) and is NOT in
   `pyproject.toml`'s `[dependency-groups] dev` (`pyproject.toml:43-48`). The
   `width`/`height` resolver tests need either (a) a real tiny in-memory image,
   which requires Pillow because Django's **model** `ImageField` and its
   dimension accessors require it, or (b) a lightweight stand-in object exposing
   `width`/`height` to unit-test the resolver logic. The spec's preferred answer
   (Risks, spec lines 1539-1555) is **add Pillow as a dev/test-only dependency**;
   the fallback is the stand-in. Either way the dimension branches must be covered
   **unconditionally** — never `pytest.skip` when Pillow is absent (a conditional
   skip would slip uncovered branches past `fail_under = 100`). See
   `### Implementation discretion items` for which option Worker 2 takes.

### Test additions / updates

Tests are written by Worker 2 in the same change as the code (per BUILD.md
"Coverage is the maintainer's gate"). All Slice 1 coverage is synthetic-model
package tests (Decision 9); no live `/graphql/` surface (no fakeshop file
column). Coverage uses unmanaged synthetic models — converter-only tests need no
table; resolver/storage tests use the `connection.schema_editor().create_model`
pattern (`tests/test_relay_connection.py:197-247`) with
`override_settings(MEDIA_ROOT=tmp_path)` (or a field-level temp `storage=`) so
writes land in a throwaway dir (spec lines 1240-1250). Do **NOT** plan any
`--cov*` invocation.

- **`tests/types/test_converters.py`** (replace the TODO anchor at
  `test_converters.py:21-28`; spec Slice 1 "Package coverage" bullet, spec lines
  312-318):
  - `FileField` → `DjangoFileType` via `FIELD_OUTPUT_TYPE_MAP` (assert
    `convert_field_output(file_field, "T")` returns `DjangoFileType`).
  - `ImageField` → `DjangoImageType` via the map.
  - **MRO precedence**: a synthetic `ImageField` subclass still resolves to
    `DjangoImageType`, never falling through to `DjangoFileType` (assert the
    output type identity).
  - `blank=True` / `null=True` each widen the result to `<object> | None`;
    a plain required file column returns the bare object.
  - `force_nullable=True` / `force_nullable=False` compose (override wins over
    `field.null` / `field.blank`).
  - **P0 split guard (the load-bearing test the build plan names,
    `build-037` line 16):** a `FilterSet` over a synthetic `FileField` still
    yields a **scalar `str`** filter input, never `DjangoFileType`. Pin via
    `scalar_for_field(file_field) is str` AND, ideally, a `FilterSet.Meta.fields`
    over the synthetic `FileField` materializing a `str`-typed input (the spec
    pins this as the regression guard, spec lines 945-950). Also assert
    `SCALAR_MAP[models.FileField] is str` / `SCALAR_MAP[models.ImageField] is str`
    are untouched.
- **`tests/types/test_resolvers.py`** (replace the TODO anchor at
  `test_resolvers.py:19-22`; spec lines 318-321 and Test plan lines 1411-1423):
  - Populated file/image values resolve `name` / `path` / `size` / `url` (and
    `width` / `height` for images) through `schema.execute_sync(...)` over a
    synthetic model with real `tmp_path` storage (reuse the
    `@pytest.mark.django_db` + `strawberry.Schema` + `execute_sync` shape at
    `test_resolvers.py:532-565`).
  - **Empty-file → `None` parent guard**: an empty/falsy `FieldFile` resolves the
    whole object to `null` (select `attachment { url }` on an empty file — no
    raise, object is `null`).
  - **Per-subfield isolation** (the load-bearing distinguishing assertion): a
    storage failure on `path` returns `null` for `path` while `url` / `name`
    still resolve — **selecting one subfield at a time** so each subfield's own
    guard is exercised independently, proving the guard is at the field level not
    the parent. Mock only the non-filesystem-`path` case (a real backend is
    impractical), per spec lines 1256-1261; use real `tmp_path` storage for the
    success paths.
  - Image dimensions (`width` / `height`) covered against a valid tiny image (or
    stand-in per the discretion item) — unconditionally, never a Pillow-gated
    `skip`.
- **`tests/types/test_base.py`** (replace the TODO anchor at
  `test_base.py:28-29`; spec lines 322-323):
  - A consumer annotation override `attachment: str` on a synthetic file column
    keeps the `str` annotation (not `DjangoFileType`) AND receives **no** generated
    file resolver (assert the class attribute is not a generated
    `strawberry.field` file resolver / the annotation stays `str`), proving the
    `_attach_file_resolvers` skip on `consumer_authored_fields` covers
    annotation-only overrides.

Temp/scratch tests for Worker 3: none planned; the synthetic-model fixtures above
are the permanent tests. If Worker 2 needs a scratch harness to characterize the
resolver-backed-`@strawberry.field`-on-`FieldFile` resolution shape (step 1
"confirm"), note it under `docs/builder/temp-tests/slice-1/` for Worker 3 and
delete before `built`.

### Implementation discretion items

- **Pillow dev dependency vs. lightweight stand-in for the image-dimension
  tests.** Worker 1 has assessed this and leaves the choice to Worker 2 because
  both satisfy the unconditional-coverage requirement and the spec explicitly
  frames them as a preferred/fallback pair (Risks, spec lines 1539-1555). **If
  Worker 2 adds Pillow**, it goes in `pyproject.toml` `[dependency-groups] dev`
  beside `pytest-django` (`pyproject.toml:43-48`) — test-only, the package itself
  never imports it, so no runtime surface changes; this is the spec's *preferred*
  answer and lets the dimension tests use a real few-byte PNG over `tmp_path`
  storage. **If Worker 2 uses a stand-in**, the `width`/`height` resolvers are
  unit-tested against a lightweight object exposing `width`/`height` (no real
  image parse). Worker 2 picks one and records the choice in its build report.
  Note: `pyproject.toml` is NOT a Slice 1 *checklist sub-bullet* — only the
  Implementation-plan table (spec line 1303) anticipates it as a possible Slice 1
  file. Adding Pillow here is in-scope as test infrastructure for the
  spec-mandated dimension coverage; the version bump in `pyproject.toml` stays
  Slice 4's job.
- **`_make_file_resolver` empty-file test idiom.** `return value if value else
  None` vs. `return None if not value else value` — equivalent; Worker 2's
  preference. Decision 4 specifies the semantic (falsy `FieldFile` → `None`),
  not the spelling.
- **Sharing the MRO-walk helper between `convert_field_output` and
  `_attach_file_resolvers`.** Worker 1 recommends a single private
  `_field_output_type_for(field)` in `converters.py` imported by `resolvers.py`;
  if a circular import surfaces at build time, a function-local import inside
  `_attach_file_resolvers` is the acceptable fallback (the walk stays in
  `converters.py` either way — do not copy the map walk into `resolvers.py`).

### Spec slice checklist (verbatim)

- [x] Slice 1: read-side output objects + the `FIELD_OUTPUT_TYPE_MAP` read map +
  the file-column resolver (per
  [Decision 3](#decision-3--read-side-output-types-djangofiletype--djangoimagetype-mirroring-upstream)
  /
  [Decision 4](#decision-4--read-side-resolution-empty-file-as-null-and-storage-safe-subfield-nullability))
  - [x] [`types/converters.py`][types-converters]: define `DjangoFileType`
    (`@strawberry.type` with **resolver-backed** fields `name: str`,
    `path: str | None`, `size: int | None`, `url: str | None`) and
    `DjangoImageType(DjangoFileType)` (adds `width: int | None`,
    `height: int | None`), each subfield delegating to a shared `_safe_file_attr`
    guard ([Decision 4](#decision-4--read-side-resolution-empty-file-as-null-and-storage-safe-subfield-nullability)).
    Add a new `FIELD_OUTPUT_TYPE_MAP` (`models.FileField → DjangoFileType`,
    `models.ImageField → DjangoImageType`) consulted by a new read-only
    `convert_field_output(field, type_name, *, force_nullable=None)` wrapper
    (which delegates to `convert_scalar` for scalar columns, keeping
    `convert_scalar` / `scalar_for_field` scalar-only so no output object can
    reach the filter-input path); **leave** [`SCALAR_MAP`][types-converters]'s
    `FileField: str` / `ImageField: str` rows in place so the shared filter-input
    path is unaffected ([Decision 3](#decision-3--read-side-output-types-djangofiletype--djangoimagetype-mirroring-upstream)).
    The new map's MRO walk keeps an `ImageField` (a `FileField` subclass)
    resolving to `DjangoImageType` because its own row precedes the `FileField`
    row.
  - [x] [`types/base.py`][types-base]: `_build_annotations` calls the new
    `convert_field_output` wrapper for non-relation columns (replacing the direct
    `convert_scalar` call) and applies the `blank`-aware object nullability.
  - [x] [`types/resolvers.py`][types-resolvers] / [`types/finalizer.py`][types-finalizer]:
    define `_attach_file_resolvers` in [`types/resolvers.py`][types-resolvers] and
    call it from the [`types/finalizer.py`][types-finalizer] loop that attaches
    the relation resolvers (the only place resolvers attach before
    `strawberry.type(...)` freezes the class), for any column resolving via
    `FIELD_OUTPUT_TYPE_MAP` — the generated parent resolver returns `None` for an
    empty / falsy `FieldFile` (`not value`) and otherwise the bound `FieldFile`
    (**object nullability only**). The per-subfield exception guard lives on
    `DjangoFileType` / `DjangoImageType`'s own resolvers, **not** here
    ([Decision 4](#decision-4--read-side-resolution-empty-file-as-null-and-storage-safe-subfield-nullability)).
    The attachment is passed **`definition.consumer_authored_fields`** (annotation
    *and* assigned-`strawberry.field` overrides — deliberately **broader** than
    the relation pass's `consumer_assigned_relation_fields`), so a consumer
    `attachment: str` keeps the legacy `str` shape and gets no generated resolver
    or object type
    ([Scalar field override semantics][glossary-scalar-field-override-semantics]).
  - [x] Output object nullability: a file column widens to
    `DjangoFileType | None` when the column is `null=True` **or** `blank=True`
    (an absent file is representable for a blank column), composing with the
    [`Meta.nullable_overrides`][glossary-metanullable-overrides] /
    [`Meta.required_overrides`][glossary-metarequired-overrides]
    `force_nullable` tri-state.
  - [x] Package coverage: [`tests/types/test_converters.py`][test-types] (the
    card's named test file) — `FileField` → `DjangoFileType`, `ImageField` →
    `DjangoImageType` via `FIELD_OUTPUT_TYPE_MAP`, MRO precedence, `blank` /
    `null` → `| None`, `force_nullable` compose, **and** a
    [`FilterSet`][glossary-filterset] over a synthetic `FileField` still yields a
    scalar (`str`) filter input, never `DjangoFileType` (the P0 split);
    [`tests/types/test_resolvers.py`][test-types] — the empty-file → `None`
    parent guard, the populated-`FieldFile` pass-through, and **per-subfield
    isolation** (a failing `path` returns `null` while `url` / `name` still
    resolve, each selected one subfield at a time);
    [`tests/types/test_base.py`][test-types] — the consumer-annotation override
    (`avatar: str`) gets no generated resolver or object type.

---

## Build report (Worker 2)

### Files touched

- `django_strawberry_framework/types/converters.py` — added the read-output
  surface: `_safe_file_attr` (the single narrow subfield storage guard), the
  resolver-backed `@strawberry.type` `DjangoFileType` (`name: str` direct,
  `path`/`size`/`url: ... | None` via the guard) and `DjangoImageType(DjangoFileType)`
  (adds `width`/`height: int | None`), the read-only `FIELD_OUTPUT_TYPE_MAP`
  (`ImageField` before `FileField`), the shared `_field_output_type_for` MRO-walk
  helper, and the public `convert_field_output(field, type_name, *, force_nullable=None)`
  wrapper (routes file/image columns to the output object widened on the
  `blank`-aware nullability, delegates everything else to `convert_scalar`).
  Removed the two `TODO(spec-037 Slice 1)` anchors; the `SCALAR_MAP`
  `FileField: str` / `ImageField: str` rows are left in place (comment rewritten
  to explain the P0 split). Module docstring "Public surface" updated.
- `django_strawberry_framework/types/base.py` — `_build_annotations` now calls
  `convert_field_output` (was `convert_scalar`) for non-relation columns; the
  `from .converters import convert_scalar` import became
  `convert_field_output` (the only runtime `convert_scalar(...)` call in the file
  was the one swapped — verified by grep). The `force_nullable` tri-state is
  unchanged and threaded through. TODO anchor replaced with a one-line note.
- `django_strawberry_framework/types/resolvers.py` — added `_make_file_resolver`
  (object-nullability-only parent resolver: `value if value else None`, stamped
  `resolve_<field>` via `_name_resolver`, no `try/except`) and
  `_attach_file_resolvers` (the structural twin of `_attach_relation_resolvers`:
  skip relations / skipped names / non-file columns, attach via
  `FIELD_OUTPUT_TYPE_MAP`). Added `from .converters import _field_output_type_for`
  (top-level, cycle-safe — converters imports nothing from resolvers). Both TODO
  anchors removed.
- `django_strawberry_framework/types/finalizer.py` — added `_attach_file_resolvers`
  to the `from .resolvers import ...` import and called it inside the same Phase-2
  loop body immediately after `_attach_relation_resolvers`, with
  `skip_field_names=definition.consumer_authored_fields` (broader than the relation
  pass). TODO anchor replaced with the rationale comment.
- `tests/types/test_converters.py` — added the file/image converter coverage
  (see below); imports extended with the new converter symbols.
- `tests/types/test_resolvers.py` — added the file/image resolver coverage (see
  below); imports extended (`itertools`, `connection`, `models as djmodels`,
  `override_settings`).
- `tests/types/test_base.py` — added the consumer-override coverage (see below).
- `pyproject.toml` — added `pillow>=10.0.0` to `[dependency-groups] dev`
  (test-only; the package never imports Pillow). See Implementation notes.
- `uv.lock` — Pillow lock entry added by `uv add --dev pillow` (purely additive,
  100 insertions / 0 deletions). `uv add` stripped the `TODO(spec-037 Slice 4)`
  comment from the `django-strawberry-framework` package entry as a side effect;
  I restored it by hand so the Slice-4 anchor survives.

### Tests added or updated

- `tests/types/test_converters.py`:
  - `test_convert_field_output_filefield_to_djangofiletype` /
    `test_convert_field_output_imagefield_to_djangoimagetype` — the map lookup.
  - `test_field_output_map_mro_precedence_image_subclass_wins` — a synthetic
    `ImageField` subclass resolves to `DjangoImageType`, never `DjangoFileType`.
  - `test_convert_field_output_blank_and_null_widen_to_optional` — `blank=True`
    OR `null=True` → `<object> | None`; plain required → bare object.
  - `test_convert_field_output_force_nullable_overrides_blank_null` —
    `force_nullable` True/False wins over `field.null` / `field.blank`.
  - `test_convert_field_output_delegates_scalar_columns` — non-file columns
    delegate to `convert_scalar` (tri-state still threads through).
  - `test_file_columns_stay_scalar_on_the_filter_input_path` — **the P0 split
    guard**: `scalar_for_field` AND `_scalar_from_model_field` both return `str`
    for file/image columns; `SCALAR_MAP` rows untouched; `FIELD_OUTPUT_TYPE_MAP`
    holds the objects. (See Implementation notes for why this pins the package
    converter rather than a full FilterSet materialization.)
- `tests/types/test_resolvers.py` (all `@pytest.mark.django_db(transaction=True)`
  + `schema_editor` synthetic model with `override_settings(MEDIA_ROOT=tmp_path)`):
  - `test_populated_file_and_image_resolve_all_subfields` — populated FileField
    resolves `name`/`path`/`size`/`url`; populated ImageField resolves
    `width`/`height` against a real Pillow-built 2x3 PNG.
  - `test_empty_file_resolves_parent_object_to_null` — empty `ImageFieldFile`
    (blank, unset) → the whole object is `null` (parent guard).
  - `test_per_subfield_guard_isolates_storage_failure` — monkeypatch
    `FileSystemStorage.path` to raise `NotImplementedError`; `path` selected
    ALONE → `null`, while `url` and `name` selected ALONE still resolve
    (proves the guard is per-subfield, not parent).
  - `test_suspicious_file_operation_is_not_swallowed` — a `SuspiciousFileOperation`
    on `path` surfaces as a GraphQL error, not a `null` subfield (Decision 4).
- `tests/types/test_base.py`:
  - `test_consumer_annotation_override_on_file_column_keeps_str_and_no_resolver`
    — `attachment: str` keeps the `str` annotation AND leaves no resolver in
    `__dict__` (no generated `resolve_attachment`).
  - `test_no_override_file_column_gets_generated_resolver` — control case: with
    no override, `__dict__["attachment"]` IS a generated `resolve_attachment`.
  - `test_consumer_assigned_field_resolver_on_file_column_is_not_clobbered` — an
    assigned `strawberry.field(resolver=attachment_resolver)` survives finalize
    (the surviving `__dict__` function is `attachment_resolver`, not
    `resolve_attachment`).

### Validation run

- `uv run ruff format .` — pass (1 file reformatted on the first run, then clean).
- `uv run ruff check --fix .` — surfaced `D102` (missing docstrings on the six
  resolver-backed subfield methods) and `ARG001` (unused `info` in the file
  parent resolver). Fixed: added one-line docstrings to each subfield method;
  added `# noqa: ARG001 - info injected by Strawberry, unused here.` to
  `file_resolver` (matching the established pattern at
  `connection.py` / `list_field.py` / `mutations/fields.py`). Re-run: **All checks passed!**
- `uv run python scripts/check_trailing_commas.py <the 7 touched .py files>` —
  `Fixed 0 file(s).` (clean).
- `git status --short` after both ruff invocations — modified: the 4 source files,
  the 3 test files, `pyproject.toml`, `uv.lock`. All slice-intended (listed under
  `### Files touched`). The two untracked `docs/builder/*.md` are Worker 0/1
  artifacts, not my edits. No unrelated tool churn to revert.
  `django_strawberry_framework/__init__.py` confirmed untouched (the public
  re-export is Slice 3's job).
- Focused tests (no `--cov*` flags): `uv run pytest tests/types/test_converters.py
  tests/types/test_base.py tests/types/test_resolvers.py --no-cov` →
  **212 passed, 2 skipped** (the 2 skips are pre-existing in these files).

### Implementation notes

- **Pillow chosen over the stand-in** (the discretion item). Added `pillow>=10.0.0`
  to `[dependency-groups] dev` and built a real tiny 2x3 PNG via
  `PIL.Image.new(...).save(buffer, "PNG")` for the `width`/`height` resolver test.
  This is the spec's *preferred* answer (Risks) and the more realistic path:
  Django's *model* `ImageField` dimension accessors require Pillow, so a real
  `ImageField` over `tmp_path` storage exercises the genuine dimension read end
  to end. The package source never imports Pillow; it is test-only. The
  `width`/`height` branches are covered unconditionally (no `pytest.skip`).
- **P0-split test form.** The spec sketched a `FilterSet.Meta.fields` over a
  synthetic `FileField` materializing a `str` input. django_filter's own
  `filter_for_field` raises `AssertionError` ("unrecognized field type FileField")
  when auto-generating a filter for a bare `FileField` via `Meta.fields`, so the
  full-FilterSet materialization is not reachable without a `Meta.filter_overrides`.
  The achievable and equally distinguishing form pins the package's OWN
  filter-input scalar path: `scalar_for_field(file_field) is str` AND
  `filters.inputs._scalar_from_model_field(file_field) is str` (the exact lookup
  the FilterSet input generator delegates to), plus `SCALAR_MAP` rows untouched.
  This proves no output object can reach the filter-input path. Flagged for
  Worker 1 below in case the spec wants its wording reconciled.
- **`_make_file_resolver` empty-file idiom**: chose `value if value else None`
  (Decision 4 specifies the falsy-FieldFile → None semantic, not the spelling).
- **`_field_output_type_for` shared helper**: lives in `converters.py` and is
  imported top-level by `resolvers.py`. No import cycle surfaced (converters
  imports nothing from resolvers), so the function-local-import fallback the plan
  allowed was not needed.
- **Post-finalize override detection**: `strawberry.type(...)` rewrites a class
  attribute — an assigned `StrawberryField` is unwrapped back to its bare
  resolver function, and an annotation-only field has no `__dict__` entry at all.
  The override tests therefore assert on the surviving `__dict__` function name
  (`resolve_<field>` = generated vs the consumer's own name) and annotation
  identity, which is robust to Strawberry's attribute rewriting. Added a
  no-override control test so "no generated resolver" is distinguishing, not
  vacuous.
- **`test_resolvers.py` synthetic models** use `@pytest.mark.django_db(transaction=True)`
  (not plain `django_db`) because SQLite's `schema_editor` cannot run inside the
  atomic wrapper plain `django_db` installs — matching the established
  `tests/test_relay_connection.py` pattern. Model class names are uniquified via
  an `itertools.count` so Django's app registry does not warn
  `Model 'products.assetN' was already registered` across tests.

### Notes for Worker 3

- No shadow file / `review_inspect.py` used during build.
- No temp tests created; all coverage is permanent (no `docs/builder/temp-tests/`).
- The P0-split invariant is pinned by
  `test_converters.py::test_file_columns_stay_scalar_on_the_filter_input_path`.
- The per-subfield isolation assertion selects ONE subfield at a time
  (`{ attachment { path } }`, then `{ url }`, then `{ name }`) so a passing `url`
  cannot mask a guard that actually sits on the parent.
- `pyproject.toml` + `uv.lock` carry the new Pillow dev dependency (test infra).
  Note that `uv add` stripped the Slice-4 `uv.lock` TODO comment; I restored it.

### Notes for Worker 1 (spec reconciliation)

- **P0-split test wording (Decision 3 / spec lines 945-950, 312-318).** The spec's
  "a `FilterSet.Meta.fields` over the synthetic `FileField` materializing a
  `str`-typed input" is not directly reachable: django_filter raises
  `AssertionError` for an auto-generated `FileField` filter (unrecognized field
  type) before any package code runs. The shipped test instead pins the package's
  own filter-input scalar lookup (`scalar_for_field` and
  `_scalar_from_model_field` both return `str`) plus untouched `SCALAR_MAP` rows —
  the exact path the FilterSet input generator delegates to, and an equally
  distinguishing guard. Recommend the spec's checklist phrasing be reconciled to
  "the filter-input scalar lookup over a `FileField` still yields `str`" rather
  than implying a full FilterSet materialization. No behavior change implied.
- **Pillow dev dependency (Implementation discretion item / Risks lines 1539-1555).**
  Added `pillow>=10.0.0` to `pyproject.toml` `[dependency-groups] dev` and the
  matching `uv.lock` entry. The plan explicitly framed `pyproject.toml` as a
  possible Slice-1 file for this test infra (not a checklist sub-bullet) and left
  the choice to Worker 2; flagging it so Worker 1 can confirm the dev-dependency
  addition is acceptable at this slice (the package-version bump in `pyproject.toml`
  remains Slice 4's job and was NOT touched).

---

## Review (Worker 3)

Reviewed the working-tree diff for the four slice-intended source files
(`types/converters.py`, `types/base.py`, `types/resolvers.py`,
`types/finalizer.py`), the three test files, and `pyproject.toml` / `uv.lock`
against the spec (Decisions 3 & 4 and the Slice 1 verbatim checklist) and the
plan. Static helper run on all four `types/` files (required — slice touches
`types/`). Focused tests run without `--cov*` (212 passed, 2 pre-existing
postgres skips). Two temp tests run and deleted (see `### Temp test
verification`). Public surface confirmed unchanged.

### High:

None.

### Medium:

None.

### Low:

None.

### DRY findings

All DRY anchors the build plan pins (`build-037` line 28) are honored; no live
duplication found.

- **Single MRO walk for the output map.** `_field_output_type_for`
  (`django_strawberry_framework/types/converters.py::_field_output_type_for`) is
  the only `FIELD_OUTPUT_TYPE_MAP` walk and is shared by both readers —
  `convert_field_output` (same module) and
  `resolvers._attach_file_resolvers` (top-level `from .converters import
  _field_output_type_for`). It is a deliberate sibling of, not a copy of,
  `scalar_for_field`'s `SCALAR_MAP` walk: two distinct maps with distinct
  responsibilities (read-output objects vs. shared scalar/filter-input). Not a
  consolidation target — folding them would re-merge the read-output and
  filter-input paths the spec's P0 split exists to keep apart.
- **Single subfield guard.** Exactly one narrow
  `except (ValueError, OSError, NotImplementedError)` exists, in
  `converters.py::_safe_file_attr`, called by all five nullable subfield
  resolvers (`path`/`size`/`url` on `DjangoFileType`, `width`/`height` on
  `DjangoImageType`). The parent resolver
  (`resolvers.py::_make_file_resolver.file_resolver`) carries no `try/except` —
  the empty-file guard is object-nullability-only (`value if value else None`).
  No second copy of the guard.
- **No repeated `("name","path","size","url")` literal.** Subfield names exist
  only as resolver method names; `DjangoImageType(DjangoFileType)` inherits the
  four base subfields rather than re-declaring them (confirmed in the generated
  SDL — see `### What looks solid`). `_safe_file_attr` takes each attr as the
  literal argument at its single call site, never as a shared tuple.
- **No parallel attachment path.** `_attach_file_resolvers` is the structural
  twin of `_attach_relation_resolvers` (same `selected_fields` iteration, same
  `strawberry.field(resolver=...)` attach, `_make_file_resolver` stamped via the
  shared `_name_resolver`), differing only in what it selects (file/image
  columns) and the broader skip set (`consumer_authored_fields`).

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` is empty. `__all__` and
the re-export list are unchanged. Correct: Slice 1 adds no public exports — the
`Upload` / `DjangoFileType` / `DjangoImageType` re-export is Slice 3
(spec `## Slice checklist` Slice 3, Decision 7). The matches for those names in
`__init__.py` are pre-placed `TODO(... Slice 3)` comment lines, not live
exports.

### CHANGELOG sanity

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces. (The
module docstring in `converters.py` and the inline rationale comments are source,
not standing docs; the `pyproject.toml` `version` line is unchanged at `0.0.10`
— the version cut is correctly deferred to Slice 4, Decision 10.)

### What looks solid

- **P0 read/write split (the slice's highest-priority invariant).** The new
  `FIELD_OUTPUT_TYPE_MAP` and `convert_field_output`
  (`converters.py::convert_field_output`) are entirely off the shared
  `scalar_for_field` / `SCALAR_MAP` filter-input path; `SCALAR_MAP`'s
  `FileField: str` / `ImageField: str` rows are untouched (verified in the
  diff). `convert_field_output` routes file/image columns to the output object
  and delegates everything else verbatim to `convert_scalar`. The package's own
  filter-input lookup (`filters/inputs._scalar_from_model_field`, which delegates
  to `scalar_for_field` — verified at
  `django_strawberry_framework/filters/inputs.py:267-269`) still yields a scalar
  `str` for a `FileField`/`ImageField`. The regression guard
  (`test_converters.py::test_file_columns_stay_scalar_on_the_filter_input_path`)
  pins both `scalar_for_field` and `_scalar_from_model_field` to `str` and asserts
  the `SCALAR_MAP` rows are unchanged — distinguishing, not vacuous.
- **Subfield guard placement and narrowness.** `_safe_file_attr` catches exactly
  `ValueError` / `OSError` / `NotImplementedError` and nothing broader. I verified
  the catch is genuinely narrow with a temp test: a `KeyError` (a genuine-bug
  proxy) propagates, while the three storage-shaped errors degrade to `None`.
  `SuspiciousFileOperation` (a `SuspiciousOperation`, not in the catch set)
  surfaces — pinned by `test_resolvers.py::test_suspicious_file_operation_is_not_swallowed`.
  The parent resolver handles object nullability only and catches no subfield
  exceptions.
- **Per-subfield isolation test is honestly distinguishing.**
  `test_resolvers.py::test_per_subfield_guard_isolates_storage_failure` selects
  one subfield at a time (`{ path }`, then `{ url }`, then `{ name }`) under a
  monkeypatched `FileSystemStorage.path` that raises `NotImplementedError`:
  `path` degrades to `null` while `url`/`name` still resolve. A passing `url`
  cannot mask a parent-level guard, so the test can only exercise the field-level
  path it claims (per BUILD.md "Query-shape tests must pin the load-bearing
  property").
- **Resolver attachment uses the broader skip set.** The finalizer passes
  `definition.consumer_authored_fields` (annotation + assigned overrides),
  deliberately broader than the relation pass's
  `consumer_assigned_relation_fields`. Three tests pin this with a control case
  (`test_base.py::test_no_override_file_column_gets_generated_resolver` proves the
  no-override column DOES get a `resolve_attachment`, so the override case's
  absence is the override's doing): annotation-only `attachment: str` gets no
  resolver and keeps `str`; an assigned `strawberry.field` survives unclobbered.
- **MRO precedence.** `FIELD_OUTPUT_TYPE_MAP` lists `ImageField` before
  `FileField`, so `_field_output_type_for` resolves an `ImageField` (and a
  consumer `ImageField` subclass) to `DjangoImageType` — pinned by
  `test_converters.py::test_field_output_map_mro_precedence_image_subclass_wins`
  with a real `models.ImageField` subclass.
- **Generated SDL matches the spec User-facing API (lines 675-689).** I built a
  throwaway schema over both output types: `DjangoFileType` is `name: String!` /
  `path|size|url` nullable; `DjangoImageType` inherits those four and adds
  `width|height` nullable — exactly the spec's contract, confirming the
  resolver-backed `name`/subfield nullability resolves correctly (and that
  `DjangoImageType`'s inheritance avoids a second copy of the base subfields).
- **`blank`-aware object nullability and `force_nullable` compose.**
  `convert_field_output` widens to `<object> | None` on
  `bool(field.null or field.blank)` when `force_nullable is None`, else honors
  the override — pinned by `test_convert_field_output_blank_and_null_widen_to_optional`
  and `test_convert_field_output_force_nullable_overrides_blank_null`.

### Spec slice checklist walk (verbatim sub-checks)

Every `- [x]` Worker 2 ticked has matching implementation in the diff; no
over-ticking, no silently-unaddressed sub-check:

- `converters.py` (`DjangoFileType` / `DjangoImageType` / `_safe_file_attr` /
  `FIELD_OUTPUT_TYPE_MAP` / `convert_field_output`; `SCALAR_MAP` rows left in
  place; MRO precedence) — landed.
- `base.py::_build_annotations` calls `convert_field_output` for non-relation
  columns; `blank`-aware nullability applied via the wrapper — landed.
- `resolvers.py::_attach_file_resolvers` + `finalizer.py` call inside the
  relation-resolver loop with `consumer_authored_fields` skip; parent resolver is
  object-nullability-only; subfield guard on the output types — landed.
- Output-object nullability (`null=True` OR `blank=True`, composing with
  `force_nullable`) — landed.
- Package coverage across `test_converters.py` / `test_resolvers.py` /
  `test_base.py` (incl. the P0 split, per-subfield isolation, override) — landed.

### Temp test verification

- `docs/builder/temp-tests/slice-1/test_name_subfield.py` (created, run,
  **deleted**). Two checks, both passed: (1) `DjangoFileType.name`'s resolver
  reads the bound `FieldFile`'s `.name` (no recursion / descriptor surprise — it
  returned the stored string); (2) `_safe_file_attr`'s catch is exactly narrow —
  `OSError`/`NotImplementedError`/`ValueError` → `None`, while `KeyError`
  propagates. Both behaviors are already pinned by permanent tests
  (`test_populated_file_and_image_resolve_all_subfields`,
  `test_suspicious_file_operation_is_not_swallowed`,
  `test_per_subfield_guard_isolates_storage_failure`), so no promotion needed —
  the temp tests only corroborated the guard's narrowness and the `name` read
  during review.

### Notes for Worker 1 (spec reconciliation)

- **Escalated (Low / cosmetic — spec phrasing, no behavior change): the P0-split
  checklist phrasing is literally unreachable.** Spec Slice 1 "Package coverage"
  (lines 312-318) and Decision 3 (lines 945-950) call for "a `FilterSet` over a
  synthetic `FileField` still yields a scalar (`str`) filter input" / "a package
  test pins `FilterSet.Meta.fields` over a synthetic `FileField` to a scalar
  input". I independently reproduced that this is **not reachable**: django_filter
  raises `AssertionError("...resolved field 'attachment' with 'exact' lookup to an
  unrecognized field type FileField. Try adding an override to
  'Meta.filter_overrides'...")` when auto-generating a filter for a bare
  `FileField` via `Meta.fields`, before any package code runs. Worker 2's
  substitute test pins the package's own filter-input lookup directly
  (`scalar_for_field(file_field) is str` AND
  `filters.inputs._scalar_from_model_field(file_field) is str`, plus `SCALAR_MAP`
  rows untouched) — the exact delegation path the FilterSet input generator uses
  (verified: `_scalar_from_model_field` → `scalar_for_field`), and it is **equally
  distinguishing**: an output object reaching the filter-input path is precisely
  what these assertions would catch. The substitute is sound; only the spec's
  checklist/Decision-3 wording overstates what django_filter permits. Recommended
  reconciliation: reword the spec to "the filter-input scalar lookup over a
  `FileField`/`ImageField` still yields `str`" rather than implying a full
  FilterSet materialization. This is the same item Worker 2 raised; I have now
  verified the unreachability claim. No behavior change, no re-pass needed.
- **Pillow dev dependency (Implementation discretion item / spec Risks
  lines 1539-1555).** `pillow>=10.0.0` added to `pyproject.toml`
  `[dependency-groups] dev` (the spec's *preferred* option) plus its `uv.lock`
  entry; the package source never imports Pillow (test-only). The plan explicitly
  authorized `pyproject.toml` as in-scope Slice-1 test infra (not a checklist
  sub-bullet) and the version line was correctly NOT bumped (Slice 4 owns that).
  Worker 2 noted `uv add` stripped the `uv.lock` Slice-4 TODO comment and restored
  it by hand — I confirmed `# TODO(spec-037 Slice 4)` is present in `uv.lock`
  (line 218). Flagged for Worker 1 to confirm the dev-dep addition is acceptable
  at this slice; nothing blocks acceptance.

### Review outcome

`review-accepted`. No High/Medium/Low findings. The diff delivers every Slice 1
spec sub-check; the P0 read/write split, the narrow subfield guard, the
field-level per-subfield isolation, the broader-skip resolver attachment, and the
MRO precedence are all correct and pinned by distinguishing tests. One Low-tier
spec-phrasing item is escalated to Worker 1 for reconciliation (the unreachable
`FilterSet.Meta.fields` phrasing); it carries no behavior change and needs no
re-pass — final-verification owns whether to edit the spec.

---

## Final verification (Worker 1)

Fresh subagent, final-verification pass. Read the full artifact (Plan / Build
report / Review), the working-tree diff for all nine touched files, the active
spec, the build plan, and my planning-pass memory. Ran the focused
`tests/types/` suite. Audited every `- [x]` box against the diff; ran the DRY
check; reconciled the spec for the P0-split phrasing both downstream workers
flagged.

### 1. Spec slice checklist audit (every `- [x]` confirmed against the diff)

All five ticked boxes have matching implementation in the working-tree diff. No
box was over-ticked; none was left silently un-ticked. No un-tick, no deferral
needed.

- **`converters.py` box** — landed. `django_strawberry_framework/types/converters.py::_safe_file_attr`
  (narrow `except (ValueError, OSError, NotImplementedError)`), the
  resolver-backed `converters.py::DjangoFileType` (`name: str` direct;
  `path` / `size` / `url: ... | None` via the guard) and
  `converters.py::DjangoImageType` subclassing it with `width` / `height`,
  `converters.py #"FIELD_OUTPUT_TYPE_MAP"` (`ImageField` before `FileField`),
  `converters.py::convert_field_output`, and the shared
  `converters.py::_field_output_type_for` MRO walk are all in the diff.
  `SCALAR_MAP`'s `FileField: str` / `ImageField: str` rows are untouched (the
  diff only rewrites the surrounding comment). MRO precedence is correct.
- **`base.py::_build_annotations` box** — landed. The import flipped from
  `convert_scalar` to `convert_field_output`; the non-relation-column call site
  now calls `convert_field_output(field, cls.__name__, force_nullable=force_nullable)`
  with the `force_nullable` tri-state threaded through unchanged.
- **`resolvers.py` / `finalizer.py` box** — landed.
  `resolvers.py::_make_file_resolver` is object-nullability-only
  (`value if value else None`, no `try/except`), stamped via `_name_resolver`;
  `resolvers.py::_attach_file_resolvers` is the structural twin of
  `_attach_relation_resolvers`, skipping relations / skipped names / non-file
  columns. `finalizer.py::finalize_django_types` calls it inside the same
  Phase-2 loop with `skip_field_names=definition.consumer_authored_fields`
  (broader than the relation pass's `consumer_assigned_relation_fields`).
- **Output-object nullability box** — landed.
  `convert_field_output` widens to `<object> | None` on
  `bool(field.null or field.blank)` when `force_nullable is None`, else honors
  the override.
- **Package-coverage box** — landed. `tests/types/test_converters.py`,
  `tests/types/test_resolvers.py`, and `tests/types/test_base.py` carry the
  file/image coverage, including the P0-split guard, per-subfield isolation, and
  the consumer-override tests (with an added no-override control so the override
  assertions are distinguishing, not vacuous).

### 2. DRY check (no prior accepted slices yet — this is the first)

No new duplication. The three DRY anchors the build plan pinned are honored:

- **Single `_safe_file_attr` guard.** Exactly one narrow
  `except (ValueError, OSError, NotImplementedError)` in
  `converters.py::_safe_file_attr`, called by all five nullable subfield
  resolvers. The parent resolver (`resolvers.py::_make_file_resolver`) carries
  no `try/except`. One catch list, one place.
- **Single `convert_field_output` wrapper.** The only `FIELD_OUTPUT_TYPE_MAP`
  consumer on the read path; `convert_scalar` / `scalar_for_field` stay
  scalar-only. The MRO walk lives once in `converters.py::_field_output_type_for`,
  imported (not copied) by `resolvers.py`.
- **`DjangoImageType(DjangoFileType)` inheritance.** The four base subfields
  (`name` / `path` / `size` / `url`) are defined once; the subclass adds only
  `width` / `height`. No repeated `("name", "path", "size", "url")` literal —
  subfield names exist only as resolver method names.
- **No parallel attachment path.** `_attach_file_resolvers` reuses the
  `selected_fields` iteration, the `_name_resolver` stamp, and the
  `strawberry.field(resolver=...)` attach shape of `_attach_relation_resolvers`,
  differing only in what it selects and the broader skip set.

### 3. Existing tests still pass

`uv run pytest tests/types/ --no-cov` → **396 passed, 2 skipped** (the 2 skips
are pre-existing postgres-only converter cases, unrelated to this slice).
No `--cov*` flag used.

### 4. Spec reconciliation — P0-split phrasing reworded (spec edited)

Both Worker 2 (Notes for Worker 1) and Worker 3 (Escalated, Low/cosmetic)
flagged that the spec's literal "`FilterSet.Meta.fields` over a synthetic
`FileField` → scalar `str` input" phrasing is unreachable: django_filter raises
`AssertionError` ("unrecognized field type FileField") when auto-generating a
filter for a bare `FileField` via `Meta.fields`, **before** any package code
runs. I reproduced this independently with a throwaway `django_filters.FilterSet`
over a synthetic `FileField` — confirmed the `AssertionError` fires.

The shipped substitute test
(`test_converters.py::test_file_columns_stay_scalar_on_the_filter_input_path`)
pins the package's own delegation path — `scalar_for_field(file_field) is str`
**and** `filters.inputs._scalar_from_model_field(file_field) is str` (the exact
lookup the FilterSet input generator delegates to), plus the `SCALAR_MAP` rows
untouched. This is the equally-distinguishing, actually-reachable form of the
same guard: an output object reaching the filter-input path is precisely what
these assertions catch. The substitute is sound; only the spec's prose
overstated what django_filter permits.

I edited the spec to reword the two sites that implied a full `FilterSet`
materialization. The **contract is unchanged** (file columns stay scalar `str`
on the shared filter-input path; no output object reaches a GraphQL input), so
the artifact's verbatim checklist box stays `- [x]` — only the test-description
prose moved to match what is honestly testable. See `### Spec changes made
(Worker 1 only)` for the cited lines.

### 5. Planner's earlier flags (Pillow, DRAFT header)

- **Pillow dev dependency.** `pillow>=10.0.0` added to `pyproject.toml`
  `[dependency-groups] dev` plus its additive `uv.lock` entry (100 insertions /
  0 deletions). Acceptable test infrastructure: the spec's *preferred* answer
  (Risks "Image dimension dependency"), the package source never imports Pillow
  (test-only), and the `width` / `height` branches are covered unconditionally
  (a real 2x3 PNG over `tmp_path` storage, no `pytest.skip`). The
  package-version bump stays Slice 4's job and was correctly NOT touched
  (`pyproject.toml`'s `version` line is still `0.0.10` in the diff). Worker 2
  noted `uv add` stripped the Slice-4 `uv.lock` TODO comment and restored it by
  hand; I confirmed `# TODO(spec-037 Slice 4)` is present in `uv.lock`.
- **Spec DRAFT header.** Stale after Slice 1 landed: the line read "DRAFT …
  implementation not yet started." Per the Worker 1 "Spec status-line
  re-verification" rule (stale status compounds across slices), I edited it to
  "IN PROGRESS … build under way (Slice 1 final-accepted, Slices 2–4 pending)."
  Recorded below. This is a per-spawn correctness edit, not deferred to Slice 4.

### Final status: `final-accepted`

The diff delivers every Slice 1 spec sub-check. The P0 read/write split, the
narrow per-subfield guard, the field-level per-subfield isolation, the
broader-skip resolver attachment, and the MRO precedence are correct and pinned
by distinguishing tests. DRY is clean (single guard, single wrapper, single MRO
walk, type inheritance). Focused tests pass. The one spec-phrasing
inconsistency both downstream workers flagged is reconciled by a prose-only spec
edit that leaves the contract — and the artifact's verbatim checklist — intact.

### Summary

Slice 1 ships the **read** half of the file/image story: two resolver-backed
Strawberry output objects (`DjangoFileType` with `name` / `path` / `size` /
`url`; `DjangoImageType(DjangoFileType)` adding `width` / `height`), a new
read-only `FIELD_OUTPUT_TYPE_MAP` (`ImageField` before `FileField`) consulted
by a new `convert_field_output` wrapper that delegates non-file columns to
`convert_scalar` unchanged, the `blank`-aware object nullability in
`_build_annotations`, and a generated file-column parent resolver attached in
the same finalizer Phase-2 window as the relation resolvers (skipping the
broader `consumer_authored_fields` set so an `attachment: str` override keeps
its legacy scalar shape). The P0 invariant holds: the file mapping is entirely
off the shared `SCALAR_MAP` / `scalar_for_field` filter-input path, so a file
column still filters as a scalar `str`. Storage failures degrade per-subfield to
`null` via the narrow `_safe_file_attr` guard; an empty file resolves the whole
object to `null`; `SuspiciousFileOperation` deliberately propagates. Pillow was
added as a test-only dev dependency for real image-dimension coverage. No public
exports changed (Slice 3 owns the root re-export). No version bump (Slice 4).

### Spec changes made (Worker 1 only)

Three edits to `docs/spec-037-upload_file_image_mapping-0_0_11.md`, all
prose-only (no contract change), triggered by Slice 1:

- **Slice 1 checklist "Package coverage" bullet** (the P0-split test
  description, formerly spec lines ~315-317). Reworded "a `FilterSet` over a
  synthetic `FileField` still yields a scalar (`str`) filter input" to pin the
  package's own filter-input scalar lookup (`scalar_for_field` /
  `_scalar_from_model_field` both return `str`, `SCALAR_MAP` rows stay `str`),
  with a parenthetical noting django_filter's auto `Meta.fields` filter for a
  bare `FileField` raises before package code runs. Reason: the literal
  full-`FilterSet`-materialization phrasing is unreachable (verified:
  django_filter raises `AssertionError`); the reworded form matches the shipped,
  equally-distinguishing test. Contract unchanged.
- **Decision 3 "Put the object types directly in `SCALAR_MAP`" rejected
  alternative** (formerly spec lines ~945-950). Same rewording: the regression
  guard now reads as the filter-input scalar-lookup pin plus a one-sentence
  explanation of why the full `FilterSet.Meta.fields` materialization is not
  reachable. Reason: keep Decision 3's stated regression guard consistent with
  the checklist and with what django_filter permits. Contract unchanged.
- **Spec header status line** (spec lines ~38-39). Changed "Status: **DRAFT** …
  implementation not yet started" to "Status: **IN PROGRESS** … build under way
  (Slice 1 final-accepted, Slices 2–4 pending)." Reason: Slice 1 has shipped, so
  the DRAFT / not-started wording is stale; per the Worker 1 spec status-line
  re-verification rule, caught per-spawn rather than left for Slice 4.

The spec-glossary consistency check (`scripts/check_spec_glossary.py --spec
docs/spec-037-upload_file_image_mapping-0_0_11.md`) still exits 0 ("OK: 20
terms") after all three edits.
