# Spec: Upload scalar and file / image field mapping — `FileField` / `ImageField` output objects, mutation `Upload` inputs, and the final `0.0.11` cut

Planned for `0.0.11` (card [`TODO-ALPHA-037-0.0.11`][kanban]). This card
completes the package's file/image story across both directions of the wire
contract: on the **read** side it replaces the placeholder `FileField` /
`ImageField` → `str` mapping (the earliest [`spec-001`][spec-001] "URL/path
string" simplification) with structured
[`DjangoFileType`][glossary-djangofiletype] /
[`DjangoImageType`][glossary-djangoimagetype] output objects (`name` / `path` /
`size` / `url`, plus `width` / `height` for images); on the **write** side it
plugs Strawberry's [`Upload` scalar][glossary-upload-scalar] into the
[auto-generated mutation `Input` types][glossary-input-type-generation] that
[`DONE-036-0.0.11`][kanban] ([`spec-036`][spec-036]) built — turning the
staged-seam `NotImplementedError` that card left at
[`mutations/inputs.py`][mutations-inputs] #"Upload staged seam
(TODO-ALPHA-037-0.0.11)" into a real `Upload`-typed input field. It is a
Required [`strawberry-graphql-django`][upstream-field-types] parity item (the
card's own 🍓 Required tag): upstream's `field_type_map` maps `files.FileField` →
`DjangoFileType`, `files.ImageField` → `DjangoImageType`, and both → `Upload` in
`input_field_type_map`, and without this every consumer touching user uploads
hand-rolls the mapping. `Upload` itself needs no registration: it is a Strawberry built-in
(`NewType("Upload", bytes)` + a `ScalarDefinition`) that Strawberry already
registers in its built-in `DEFAULT_SCALAR_REGISTRY`, so an `Upload`-annotated
field resolves in any schema — the public-surface change is **re-exporting**
`Upload` from the package root. This is the contrast with the package-custom
[`BigInt`][glossary-bigint-scalar] scalar, which is absent from the default
registry and must be bound through
[`strawberry_config`][glossary-strawberry-config].
**Version boundary** (see
[Decision 10](#decision-10--this-card-owns-the-final-0011-version-bump)): unlike
[`spec-036`][spec-036] (which shared its patch line with an unstarted sibling
and so deferred), this card is the **last** `0.0.11` card — `036` is already
`DONE` and 037 is the lone `## In progress` entry on `0.0.11` — so the
`pyproject.toml` / `__version__` /
[`tests/base/test_init.py::test_version`][test-base-init] bump that `036`
deferred to the joint cut **lands here**.

Status: **IN PROGRESS** — authored for `TODO-ALPHA-037-0.0.11` via the
[`docs/SPECS/NEXT.md`][next] flow; **all four slices final-accepted** (the
in-spec build is complete; the cross-slice integration pass + final gate still
follow). The `docs/TREE.md` summary anchor that blocked Slice 4 was discharged
(summaries updated, anchor removed); see the Slice 4 build artifact. Slices: Slice
1 (**read-side output objects** — `DjangoFileType` / `DjangoImageType`, the two
`SCALAR_MAP` rows, and the empty-file resolver guard;
[Decision 3](#decision-3--read-side-output-types-djangofiletype--djangoimagetype-mirroring-upstream)
/
[Decision 4](#decision-4--read-side-resolution-empty-file-as-null-and-storage-safe-subfield-nullability)),
Slice 2 (**write-side `Upload` input** — the `Upload` re-export in
[`scalars.py`][scalars] and the [`mutations/inputs.py`][mutations-inputs]
seam-to-`Upload` swap plus the write-resolver file assignment;
[Decision 5](#decision-5--re-export-upload-rather-than-register-it)
/
[Decision 6](#decision-6--write-side-input-mapping-the-mutation-seam-becomes-upload)),
Slice 3 (**public exports + coverage hardening** — `Upload` / `DjangoFileType` /
`DjangoImageType` re-exported and pinned, plus the synthetic-model
read/write/storage-failure tests;
[Decision 7](#decision-7--public-surface-three-net-new-root-exported-symbols) /
[Decision 9](#decision-9--test-placement-package-tests-own-synthetic-fileimage-models)),
and Slice 4 (**docs + the `0.0.11` version cut + card wrap**; the per-card
[`CHANGELOG.md`][changelog] edit must be named explicitly in the Slice 4
maintainer prompt — this spec describes the edit but cannot grant the permission
[`AGENTS.md`][agents] reserves for an explicit instruction). The card's hard
dependency is satisfied: [`DONE-036-0.0.11`][kanban] (the mutation foundation
whose input generator this card extends, leaving the `Upload` seam this card
consumes) has shipped.

Owner: package maintainer.

Predecessors: [`spec-036-mutations-0_0_11.md`][spec-036] (the sibling `0.0.11`
mutations card this card plugs into — its [Decision 6][spec-036] left "a thin
input-converter seam … so 037 plugs `Upload` in without re-opening the
generator", realized as the [`mutations/inputs.py`][mutations-inputs]
`NotImplementedError` this card replaces; the most-recently-authored spec and
the canonical voice / depth / section-layout reference);
[`spec-025-scalar_map_helper-0_0_7.md`][spec-025] (the
[`strawberry_config`][glossary-strawberry-config] / `_PACKAGE_SCALAR_MAP`
registration path — its Decision 3 redefined `BigInt` as a bare
`NewType` + `ScalarDefinition`, the exact structural shape `Upload` already has,
though `Upload` is a built-in that needs no such registration);
[`spec-017-deferred_scalars-0_0_6.md`][spec-017] (the converter-table-addition
precedent — it added `BigInt` / `JSON` / `ArrayField` / `HStoreField` to
[`SCALAR_MAP`][types-converters], the same table this card extends, and
pioneered the synthetic-model test strategy);
[`spec-026-scalar_conversion_fakeshop-0_0_7.md`][spec-026] (the
scalar-conversion coverage posture); and
[`spec-001-django_types-0_0_1.md`][spec-001] (the original `FileField` /
`ImageField` read-side `str` mapping this card replaces).
[`docs/GLOSSARY.md`][glossary] carries
[`Upload` scalar][glossary-upload-scalar],
[`DjangoFileType`][glossary-djangofiletype], and
[`DjangoImageType`][glossary-djangoimagetype] as `planned for 0.0.11`; Slice 4
promotes all three to `shipped (0.0.11)`, rewrites the
[Scalar field conversion][glossary-scalar-field-conversion] file/image row (and
adds a file/image row to
[Specialized scalar conversions][glossary-specialized-scalar-conversions]), and
moves the package-version line to `0.0.11`.

Revision history (kept inline so the spec is self-contained):

- **Revision 1** — initial draft authored from the
  [`TODO-ALPHA-037-0.0.11`][kanban] card body via the
  [`docs/SPECS/NEXT.md`][next] flow (2026-06-19). Pinned: the canonical
  structured filename
  ([Decision 1](#decision-1--spec-filename-and-canonical-naming)); the
  card-scope boundary as a file/image conversion card, not a multipart-transport
  or storage-abstraction card
  ([Decision 2](#decision-2--card-scope-boundary-fileimage-conversion-only-not-transport-or-storage-abstraction));
  the `DjangoFileType` / `DjangoImageType` output shapes mirroring
  [`strawberry-graphql-django`][upstream-field-types] with an empty-file
  resolver guard
  ([Decision 3](#decision-3--read-side-output-types-djangofiletype--djangoimagetype-mirroring-upstream));
  **storage-safe nullable subfields** (`path` / `size` / `url` / `width` /
  `height` nullable; `name` non-null) so a non-filesystem backend or a vanished
  file degrades to `null` rather than a GraphQL 500, and the default-nullable
  object shape (file/image output is `<object> | None` by default to match the
  empty-file resolver `None`)
  ([Decision 4](#decision-4--read-side-resolution-empty-file-as-null-and-storage-safe-subfield-nullability));
  the `Upload` re-export from the package root — no `_PACKAGE_SCALAR_MAP` entry,
  since `Upload` is already in Strawberry's built-in scalar registry (the
  contrast with the package-custom [`BigInt`][glossary-bigint-scalar])
  ([Decision 5](#decision-5--re-export-upload-rather-than-register-it));
  the write-side seam-to-`Upload` swap and the write-resolver file assignment,
  lifting the `036` file-column merge-override exception
  ([Decision 6](#decision-6--write-side-input-mapping-the-mutation-seam-becomes-upload));
  the three net-new root-exported public symbols
  ([Decision 7](#decision-7--public-surface-three-net-new-root-exported-symbols));
  no new `DjangoType` `Meta` key or settings key
  ([Decision 8](#decision-8--no-new-meta-key-no-new-setting-no-dynamic-storage-policy));
  the synthetic-model test strategy with live coverage only where a real
  fakeshop path exists
  ([Decision 9](#decision-9--test-placement-package-tests-own-synthetic-fileimage-models));
  and **this card owning the final `0.0.11` version bump**
  ([Decision 10](#decision-10--this-card-owns-the-final-0011-version-bump)).
  Three card-body conflicts are carried into
  [Risks and open questions](#risks-and-open-questions) rather than silently
  reconciled (the stale `"Pairs with 028"` note, the stale
  `mutations/ (planned)` predicted-file annotation, and the stale
  `TODO-ALPHA-035-0.0.11` reference in the [`scalars.py`][scalars] docstring),
  each with a preferred reading.

## Key glossary references

Skim these [`docs/GLOSSARY.md`][glossary] entries first — they anchor the
vocabulary used throughout the spec:

- [`Upload` scalar][glossary-upload-scalar] — the write-side subject. The
  glossary pins its planned contract: a Strawberry `Upload` scalar mapping for
  `FileField` / `ImageField` on mutation inputs, paired with
  [`DjangoFileType`][glossary-djangofiletype] /
  [`DjangoImageType`][glossary-djangoimagetype] on the output side. This card
  ships exactly that; the entry is promoted from `planned for 0.0.11` to
  `shipped (0.0.11)` in Slice 4.
- [`DjangoFileType`][glossary-djangofiletype] /
  [`DjangoImageType`][glossary-djangoimagetype] — the read-side subjects.
  `DjangoFileType` carries `name` / `path` / `size` / `url`; `DjangoImageType`
  adds `width` / `height` image dimensions (the dimension-test dependency is
  settled in [Risks](#risks-and-open-questions)).
  [Decision 3](#decision-3--read-side-output-types-djangofiletype--djangoimagetype-mirroring-upstream)
  /
  [Decision 4](#decision-4--read-side-resolution-empty-file-as-null-and-storage-safe-subfield-nullability)
  realize both.
- [Scalar field conversion][glossary-scalar-field-conversion] /
  [Specialized scalar conversions][glossary-specialized-scalar-conversions] —
  the converter tables this card touches. Today the
  [Scalar field conversion][glossary-scalar-field-conversion] table lists
  `FileField` / `ImageField` → `str` (string path / URL); this card updates that
  row to reflect the split — **read** output → the structured objects (via the
  new `FIELD_OUTPUT_TYPE_MAP`), while the **filter / scalar-input** value stays
  `str` in `SCALAR_MAP` — and adds a file/image row to
  [Specialized scalar conversions][glossary-specialized-scalar-conversions]
  (which has none today), documenting the
  [breaking wire-format change][glossary-specialized-scalar-conversions]
  ([Decision 3](#decision-3--read-side-output-types-djangofiletype--djangoimagetype-mirroring-upstream)).
- [`BigInt` scalar][glossary-bigint-scalar] /
  [`strawberry_config`][glossary-strawberry-config] — the precedent for
  root-exporting a package scalar. Unlike `BigInt` (a package-custom scalar
  bound through the [`strawberry_config`][glossary-strawberry-config] factory),
  `Upload` is already in Strawberry's built-in `DEFAULT_SCALAR_REGISTRY`, so it
  needs no `_PACKAGE_SCALAR_MAP` entry — only a re-export
  ([Decision 5](#decision-5--re-export-upload-rather-than-register-it)). The
  glossary's `strawberry_config` entry's stray "next: `Upload`" mention is
  removed in Slice 4.
- [`DjangoMutation`][glossary-djangomutation] /
  [Input type generation][glossary-input-type-generation] /
  [`DjangoMutationField`][glossary-djangomutationfield] /
  [`FieldError` envelope][glossary-fielderror-envelope] — the shipped
  [`spec-036`][spec-036] write side this card extends; the input generator
  already produces `<Model>Input` / `<Model>PartialInput`, and this card teaches
  it to map a file/image column to `Upload` instead of failing loud
  ([Decision 6](#decision-6--write-side-input-mapping-the-mutation-seam-becomes-upload)).
- [Scalar field override semantics][glossary-scalar-field-override-semantics] /
  [`auto`-typed annotations][glossary-auto-typed-annotations] — the consumer
  opt-out. A consumer who wants the legacy `str` (URL) read shape keeps it with
  a concrete annotation override (`avatar: str`), which bypasses
  `convert_scalar`; the override contract is unchanged
  ([Decision 3](#decision-3--read-side-output-types-djangofiletype--djangoimagetype-mirroring-upstream)).
- [`Meta.fields`][glossary-metafields] / [`Meta.exclude`][glossary-metaexclude]
  / [`DjangoType`][glossary-djangotype] / [`Meta.model`][glossary-metamodel] —
  the type-system surface the conversions ride; a file column is selected /
  excluded by the same `Meta.fields` / `Meta.exclude` rules as any column, and
  the input generator narrows by the mutation's own `Meta.fields` /
  `Meta.exclude` ([`spec-036`][spec-036] Decision 6).
- [`Meta.nullable_overrides`][glossary-metanullable-overrides] /
  [`Meta.required_overrides`][glossary-metarequired-overrides] — the existing
  `force_nullable` tri-state in [`convert_scalar`][types-converters] that this
  card's default-nullable file output composes with
  ([Decision 4](#decision-4--read-side-resolution-empty-file-as-null-and-storage-safe-subfield-nullability)).
- [`ConfigurationError`][glossary-configurationerror] — the validation exception
  the read path keeps raising for an unsupported field; the file/image branch
  makes `FileField` / `ImageField` supported on both read and write, so a
  previously-`NotImplementedError`-raising write input over a file column now
  generates a valid `Upload` field.
- [`DjangoFormMutation`][glossary-djangoformmutation] /
  [`SerializerMutation`][glossary-serializermutation] — the downstream `0.0.12`
  / `0.0.13` flavor cards that inherit the `Upload` input mapping for free,
  because they reuse the same
  [Input type generation][glossary-input-type-generation] and
  [`FieldError` envelope][glossary-fielderror-envelope] this card extends.
- [`TestClient`][glossary-testclient] — the `0.0.14` multipart test-client card
  that *depends on* this card: it must send multipart requests once `Upload`
  exists. The dependency is one-directional — this card ships the scalar, that
  card ships the transport helper ([Non-goals](#non-goals)).
- [relation handling][glossary-relation-handling] /
  [`DjangoOptimizerExtension`][glossary-djangooptimizerextension] — context for
  why a file column is a **scalar** column, not a relation: it carries no FK and
  needs no optimizer planning; the read resolver is a thin scalar-column
  wrapper, not a relation resolver.

Project conventions to follow:

- [`AGENTS.md`][agents] — the test-placement rule (package-internal converter /
  scalar / input mechanics under [`tests/types/`][test-types] /
  [`tests/`][test-scalars] / [`tests/mutations/`][test-mutations] mirroring
  source; live consumer behavior over `/graphql/` only when a realistic request
  reaches it —
  [Decision 9](#decision-9--test-placement-package-tests-own-synthetic-fileimage-models));
  the settings-keys-only-when-needed rule (this card adds no settings key); the
  no-pytest-after-edits rule; the CHANGELOG-edit-permission rule at
  [`AGENTS.md`][agents] #"Do not update CHANGELOG.md unless explicitly
  instructed" — Slice 4's release-note edit must be named in its maintainer
  prompt.
- [`START.md`][start] — the "behaviorally we copy `strawberry-graphql-django`'s
  good ideas, surface-wise we copy `django-graphene-filters`" rule (this card
  borrows upstream's file/image output shapes and `Upload` mapping at the
  *outcome* level); the "do both libraries provide it? → foundational" test; and
  the reference-style markdown link convention (defs at the bottom under the 10
  canonical group headers).
- [`CONTRIBUTING.md`][contributing] — the 100% coverage target
  (`fail_under = 100`); every converter branch, the read resolver's empty-file /
  storage-failure guard, the `Upload` re-export, and the write-input mapping
  earn coverage in the package test trees.
- [`docs/TREE.md`][tree] — the conversion-table rows the package documents; this
  card touches [`types/converters.py`][types-converters] (read),
  [`scalars.py`][scalars] (the `Upload` scalar), and
  [`mutations/inputs.py`][mutations-inputs] (write) and adds no module outside
  the existing trees.
- [`GOAL.md`][goal] — success-criterion 6 ("Write mutations declaratively … plus
  `Upload` scalar for `FileField` / `ImageField`") names the `Upload` scalar
  explicitly; this card satisfies the upload half of that criterion.

## Slice checklist

Each top-level item maps to one commit / PR. **Four slices: read output objects
(Slice 1), write `Upload` input (Slice 2), exports + coverage (Slice 3), docs +
the `0.0.11` cut (Slice 4).** Slices 1–2 are independent (read vs write modules)
and can land in either order; Slice 3 depends on both; Slice 4 is doc +
version-cut only.

- [ ] Slice 1: read-side output objects + the `FIELD_OUTPUT_TYPE_MAP` read map +
  the file-column resolver (per
  [Decision 3](#decision-3--read-side-output-types-djangofiletype--djangoimagetype-mirroring-upstream)
  /
  [Decision 4](#decision-4--read-side-resolution-empty-file-as-null-and-storage-safe-subfield-nullability))
  - [ ] [`types/converters.py`][types-converters]: define `DjangoFileType`
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
  - [ ] [`types/base.py`][types-base]: `_build_annotations` calls the new
    `convert_field_output` wrapper for non-relation columns (replacing the direct
    `convert_scalar` call) and applies the default-nullable object shape
    (file/image output is `| None` by default, independent of `blank` / `null`).
  - [ ] [`types/resolvers.py`][types-resolvers] / [`types/finalizer.py`][types-finalizer]:
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
  - [ ] Output object nullability: a file/image column maps to
    `DjangoFileType | None` **by default**, independent of `null` / `blank` (the
    parent resolver returns `None` for an empty `FieldFile`, reachable even on a
    `null=False, blank=False` column), composing with the
    [`Meta.nullable_overrides`][glossary-metanullable-overrides] /
    [`Meta.required_overrides`][glossary-metarequired-overrides]
    `force_nullable` tri-state — `required_overrides` (`force_nullable=False`)
    is the opt-in to the stricter `DjangoFileType!` contract.
  - [ ] Package coverage: [`tests/types/test_converters.py`][test-types] (the
    card's named test file) — `FileField` → `DjangoFileType`, `ImageField` →
    `DjangoImageType` via `FIELD_OUTPUT_TYPE_MAP`, MRO precedence, default
    `| None` (independent of `blank` / `null`), `force_nullable` compose, **and** the package's
    filter-input scalar lookup over a synthetic `FileField` / `ImageField` still
    yields a scalar (`str`) — `scalar_for_field` /
    [`filters/inputs.py`][filters-inputs] `_scalar_from_model_field` both return
    `str`, and the [`SCALAR_MAP`][types-converters] rows stay `str` — never
    `DjangoFileType` (the P0 split; this pins the package's own delegation path
    because django_filter's auto `Meta.fields` filter for a bare `FileField`
    raises before package code runs);
    [`tests/types/test_resolvers.py`][test-types] — the empty-file → `None`
    parent guard, the populated-`FieldFile` pass-through, and **per-subfield
    isolation** (a failing `path` returns `null` while `url` / `name` still
    resolve, each selected one subfield at a time);
    [`tests/types/test_base.py`][test-types] — the consumer-annotation override
    (`avatar: str`) gets no generated resolver or object type.
- [ ] Slice 2: write-side `Upload` input + the `Upload` re-export (per
  [Decision 5](#decision-5--re-export-upload-rather-than-register-it)
  /
  [Decision 6](#decision-6--write-side-input-mapping-the-mutation-seam-becomes-upload))
  - [ ] [`scalars.py`][scalars]: re-export `Upload` (and `UploadDefinition`)
    from `strawberry.file_uploads.scalars` for the public surface. **Do not**
    add it to `_PACKAGE_SCALAR_MAP` — `Upload` already resolves via Strawberry's
    built-in `DEFAULT_SCALAR_REGISTRY`
    ([Decision 5](#decision-5--re-export-upload-rather-than-register-it)); fix
    the stale `TODO-ALPHA-035-0.0.11` reference in the module docstring to
    `TODO-ALPHA-037-0.0.11`.
  - [ ] [`mutations/inputs.py`][mutations-inputs]: remove the staged seam at
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
  - [ ] [`mutations/resolvers.py`][mutations-resolvers]: **verify** the existing
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
  - [ ] Package coverage: [`tests/test_scalars.py`][test-scalars] — an
    `Upload`-annotated field resolves through a schema built with
    `strawberry_config()` **and** through a plain `StrawberryConfig` (proving
    `Upload` rides Strawberry's default registry, not the package map); the
    existing `BigInt` collision test is untouched;
    [`tests/mutations/test_inputs.py`][test-mutations] — replace the
    staged-`NotImplementedError` tests with positive `FileField` / `ImageField`
    → `Upload` required/optional shapes, `| None` widening, and the lifted CR-6
    override; [`tests/mutations/test_resolvers.py`][test-mutations] — file
    assignment on create / partial update.
- [ ] Slice 3: public exports + coverage hardening (per
  [Decision 7](#decision-7--public-surface-three-net-new-root-exported-symbols)
  /
  [Decision 9](#decision-9--test-placement-package-tests-own-synthetic-fileimage-models))
  - [ ] [`__init__.py`][init]: re-export `Upload` (from [`scalars.py`][scalars])
    and `DjangoFileType` / `DjangoImageType` (from
    [`types/converters.py`][types-converters]); add all three to `__all__`.
  - [ ] Package coverage: [`tests/base/test_init.py`][test-base-init] — the
    public-export and `__all__` assertions add the three symbols (`test_version`
    moves to `0.0.11` in Slice 4,
    [Decision 10](#decision-10--this-card-owns-the-final-0011-version-bump)).
    Storage-failure / null-blank / image-dimension edge tests harden the
    synthetic-model coverage.
- [ ] Slice 4: docs + the `0.0.11` version cut + card wrap (per
  [Doc updates](#doc-updates) /
  [Decision 10](#decision-10--this-card-owns-the-final-0011-version-bump))
  - [ ] **Version files to `0.0.11`**
    ([Decision 10](#decision-10--this-card-owns-the-final-0011-version-bump)):
    [`pyproject.toml`][pyproject], `__version__` in [`__init__.py`][init],
    [`tests/base/test_init.py::test_version`][test-base-init], the
    [`docs/GLOSSARY.md`][glossary] package-version line, and `uv.lock` if it
    carries the package version.
  - [ ] [`docs/GLOSSARY.md`][glossary] (promote
    [`Upload` scalar][glossary-upload-scalar] /
    [`DjangoFileType`][glossary-djangofiletype] /
    [`DjangoImageType`][glossary-djangoimagetype] to `shipped (0.0.11)`; rewrite
    the [Scalar field conversion][glossary-scalar-field-conversion] file/image
    row and **add** a file/image row to
    [Specialized scalar conversions][glossary-specialized-scalar-conversions]
    (which has none today); add the three to **Public exports** + the **Index** +
    the **File / image uploads** browse-by-category row; record the read-side
    breaking-wire-format change; remove the
    [`strawberry_config`][glossary-strawberry-config] entry's stray "next:
    `Upload`" mention), [`docs/README.md`][docs-readme] /
    [`README.md`][readme] (move the `Upload` scalar + generated file/image field
    typing from "Coming next (`0.0.11`)" to "Shipped today" — wording the
    *scalar and generated mutation-field typing*, **not** full multipart HTTP
    upload ergonomics, which await the `0.0.14` [`TestClient`][glossary-testclient]
    — and the README **Status** line from `0.0.10` to `0.0.11`), [`GOAL.md`][goal]
    (note that criterion 6's `Upload` / `FileField` / `ImageField` part ships for
    generated `DjangoMutation` inputs — the `ModelForm` / `ModelSerializer`
    flavors in that same criterion still land later), [`TODAY.md`][today] (rewrite the
    scalar-conversion table's `FileField` / `ImageField` → `str` row to the
    structured output objects and note upload mutation inputs as a package
    capability not exercised by products), [`CHANGELOG.md`][changelog] (only if
    the Slice 4 maintainer prompt explicitly requests it), [`KANBAN.md`][kanban]
    (card → Done via the kanban DB + re-render).

## Problem statement

`django-strawberry-framework` treats file/image columns asymmetrically and
incompletely:

- On the **read side**, [`types/converters.py`][types-converters] maps
  `models.FileField` and `models.ImageField` to `str`, preserving the earliest
  [`spec-001`][spec-001] "URL/path string" simplification. A `str`-typed file
  field serializes to the file's name (`str(FieldFile)`), discarding the `url` a
  client needs to fetch the file, the `size`, the storage `path`, and — for
  images — the dimensions. [`strawberry-graphql-django`][upstream-field-types]
  returns a `DjangoFileType` / `DjangoImageType` so the client gets the whole
  picture in one selection; a consumer migrating from upstream and selecting
  `{ avatar { url width } }` hits a schema error against this package today.
- On the **write side**, [`mutations/inputs.py`][mutations-inputs] deliberately
  rejects `FileField` / `ImageField` before scalar conversion (a
  `NotImplementedError` naming this card). That was the correct
  [`spec-036`][spec-036] staged seam — silently inheriting the read-side `str`
  mapping would have created a wrong mutation contract — but after
  [`DjangoMutation`][glossary-djangomutation] shipped, the seam is now the
  blocker: any model with an editable file/image column cannot use generated
  mutation inputs unless the consumer excludes the column.
- `Upload` already resolves, but the package does not expose it. Strawberry
  registers `Upload` in its built-in `DEFAULT_SCALAR_REGISTRY`, so an
  `Upload`-annotated field resolves without any package registration; the only
  public-surface gap is that the package does not re-export `Upload` for
  consumers hand-writing upload fields (in contrast to
  [`BigInt`][glossary-bigint-scalar], a package-custom scalar that does need
  [`strawberry_config`][glossary-strawberry-config]).

The card matters because upload fields are ordinary Django model fields. A
package that claims DRF-shaped model-to-GraphQL generation cannot require every
user-upload model to hand-roll both output object fields and mutation input
scalars. This is a Required `strawberry-graphql-django` parity item,
foundational by the [`START.md`][start] "do both libraries provide it?" test —
both upstreams map file/image fields, but only `strawberry-graphql-django` ships
the structured output object; `graphene-django` maps `FileField` to a bare
`String` (the weaker form this card does not copy), so the rich file/image shape
is a `strawberry-graphql-django` borrow, not a Graphene one.

## Current state

A true description of the repo as this spec is authored:

- **`FileField` / `ImageField` → `str` on read.**
  [`types/converters.py`][types-converters] #"models.FileField: str" maps both
  to `str` in [`SCALAR_MAP`][types-converters];
  [`convert_scalar`][types-converters] resolves them through the shared
  `scalar_for_field` MRO walk and widens to `str | None` on `field.null` (or a
  `Meta.nullable_overrides` / `Meta.required_overrides` `force_nullable`
  tri-state). There is **no** `DjangoFileType` / `DjangoImageType` symbol and no
  file-column read resolver — a file column rides Strawberry's default attribute
  resolver and serializes via `str(FieldFile)`. Critically,
  [`filters/inputs.py`][filters-inputs]'s `_scalar_from_model_field` walks the
  **same** `scalar_for_field` / [`SCALAR_MAP`][types-converters], so `SCALAR_MAP`
  is the shared scalar/filter-input map — the read change cannot simply rewrite
  its rows ([Decision 3](#decision-3--read-side-output-types-djangofiletype--djangoimagetype-mirroring-upstream)).
- **The write generator refuses file columns.**
  [`mutations/inputs.py`][mutations-inputs] #"Upload staged seam
  (TODO-ALPHA-037-0.0.11)" raises `NotImplementedError` for a `FileField` /
  `ImageField`, with a `TODO(spec-036 Slice 1)` comment naming this card;
  [`tests/mutations/test_inputs.py`][test-mutations] pins that fail-loud
  behavior. The `036` review (CR-6) pinned that file columns are "the one
  exception to the merge override" precisely because this `NotImplementedError`
  precedes the `Meta.input_class` override skip — an exception this card lifts.
- **`Upload` is not re-exported.** [`scalars.py`][scalars] holds `BigInt` (a
  `NewType("BigInt", int)` + a `ScalarDefinition`) and
  `_PACKAGE_SCALAR_MAP = {BigInt: _BIGINT_SCALAR_DEFINITION}`. Strawberry already
  ships `Upload = NewType("Upload", bytes)` + `UploadDefinition` at
  `strawberry.file_uploads.scalars` **and** registers it in
  `DEFAULT_SCALAR_REGISTRY`, so `Upload` already resolves in every schema — the
  package simply does not re-export it (unlike `BigInt`, which is absent from the
  default registry and so needs its `_PACKAGE_SCALAR_MAP` entry). The
  module docstring's "Future scalars (e.g. `Upload` per TODO-ALPHA-035-0.0.11)"
  carries a **stale card number** (`035` is the optimizer-hardening card; the
  real owner is this card, `037`).
- **The version line still reads `0.0.10`.** [`__init__.py`][init] exports the
  `0.0.11` mutation symbols but reports `__version__ = "0.0.10"`;
  [`pyproject.toml`][pyproject] and
  [`tests/base/test_init.py::test_version`][test-base-init] are also `0.0.10`,
  and [`docs/GLOSSARY.md`][glossary]'s package-version line is `0.0.10` while
  `DjangoMutation` is already `shipped (0.0.11)` — the joint cut
  [`spec-036`][spec-036] deferred has not landed
  ([Decision 10](#decision-10--this-card-owns-the-final-0011-version-bump)).
- **The mutation subpackage exists.** The card's "Predicted files" annotates
  `django_strawberry_framework/mutations/ (planned)`, but `mutations/` shipped
  with [`DONE-036-0.0.11`][kanban]; [`mutations/inputs.py`][mutations-inputs] /
  [`mutations/resolvers.py`][mutations-resolvers] are on disk. The annotation is
  stale ([Risks](#risks-and-open-questions)).
- **No example app uses a file/image column.**
  `grep -rln "FileField\|ImageField" examples/` returns nothing — `products` /
  `library` / `scalars` carry no file column, so the read-side break invalidates
  no in-repo schema and the card's "synthetic-model tests" scoping is sufficient
  for coverage
  ([Decision 9](#decision-9--test-placement-package-tests-own-synthetic-fileimage-models)).

## Goals

1. **Expose file/image output as structured objects.** The read converter
   returns [`DjangoFileType`][glossary-djangofiletype] /
   [`DjangoImageType`][glossary-djangoimagetype] via a new `FIELD_OUTPUT_TYPE_MAP`
   (kept off the shared `SCALAR_MAP` / filter-input path), mirroring
   [`strawberry-graphql-django`][upstream-field-types], so a client gets `name` /
   `path` / `size` / `url` (+ `width` / `height`) in one selection
   ([Decision 3](#decision-3--read-side-output-types-djangofiletype--djangoimagetype-mirroring-upstream)).
2. **Handle empty / unreadable files deliberately.** An absent file resolves to
   `null` (the whole object); a storage property that cannot be produced degrades
   to a `null` subfield (guarded on the subfield resolver, not the parent) — never
   a `FieldFile.url` / `.path` exception surfacing as a GraphQL 500
   ([Decision 4](#decision-4--read-side-resolution-empty-file-as-null-and-storage-safe-subfield-nullability)).
3. **Re-export `Upload` from the package root.** `Upload` already resolves via
   Strawberry's built-in `DEFAULT_SCALAR_REGISTRY`, so the package exposes it as
   a public symbol (for consumer-authored upload fields) rather than registering
   it in `_PACKAGE_SCALAR_MAP` — the contrast with the package-custom
   [`BigInt`][glossary-bigint-scalar] scalar
   ([Decision 5](#decision-5--re-export-upload-rather-than-register-it)).
4. **Map `FileField` / `ImageField` to `Upload` on the mutation input side.**
   The [`spec-036`][spec-036] staged seam becomes a real `Upload`-typed input
   field, required per the shipped per-field rule, and the existing write
   pipeline's scalar-assignment path carries the uploaded file (verified, not a
   new file branch)
   ([Decision 6](#decision-6--write-side-input-mapping-the-mutation-seam-becomes-upload)).
5. **Keep read and write contracts distinct.** Output is an object type; input
   is `Upload`; neither side leaks the other's representation.
6. **Export `Upload` / `DjangoFileType` / `DjangoImageType` from the package
   root**
   ([Decision 7](#decision-7--public-surface-three-net-new-root-exported-symbols)).
7. **Complete the `0.0.11` cut.** Since `037` is the only active WIP card on
   `0.0.11` and `036` deferred the bump, Slice 4 owns the version-file alignment
   ([Decision 10](#decision-10--this-card-owns-the-final-0011-version-bump)).

## Non-goals

- **Multipart test-client helper.** The future
  [`TestClient`][glossary-testclient] card (`0.0.14`) references
  `TODO-ALPHA-037` because it must send multipart requests once `Upload` exists;
  the helper itself is `0.0.14`, not this card
  ([Out of scope](#out-of-scope-explicitly-tracked-elsewhere)).
- **A new fakeshop upload domain.** This card does not add a fake image/product
  app or unrelated model just to force live HTTP coverage; if a real file/image
  field is later added to fakeshop, it earns live coverage then
  ([Decision 9](#decision-9--test-placement-package-tests-own-synthetic-fileimage-models)).
- **Nested writes / file-replacement policy beyond the direct field.** This card
  maps the scalar and lets the shipped mutation pipeline assign Django's
  uploaded file object to the model field; complex replace/delete semantics
  beyond "provided value sets the field, omitted value leaves it alone on
  partial update" stay out
  ([Out of scope](#out-of-scope-explicitly-tracked-elsewhere)).
- **Storage abstraction / signed URLs / image processing.** The package does not
  wrap every Django storage backend; it exposes safe nullable subfields where
  storage properties may be unavailable and lets Django's storage object answer
  `url` / `path` / `size` ([Edge cases](#edge-cases-and-constraints)).
- **`DurationField` / `BinaryField` and other unmapped scalars.** They remain
  intentionally absent from [`SCALAR_MAP`][types-converters] with their
  documented custom-scalar plugs.
- **A new `DjangoType` `Meta` key or settings key**
  ([Decision 8](#decision-8--no-new-meta-key-no-new-setting-no-dynamic-storage-policy)).

## Borrowing posture

Per the [`START.md`][start] "do both libraries provide it? → foundational" test,
file/image mapping is **Required `strawberry-graphql-django` parity** (the
card's own 🍓 Required tag) and `graphene-django` provides a weaker form. The
borrowing splits along the package's standing line — *behaviorally* copy
`strawberry-graphql-django`'s output shapes and `Upload` mapping; *surface-wise*
keep the package's automatic `class Meta`-driven conversion (the consumer
declares no decorator and no upload helper — a file column is converted by the
same `Meta.fields` / `Meta.exclude` selection as any column). `graphene-django`
maps `FileField` to a `String` output (matching this package's original
`spec-001` simplification, but not the card's target); we follow the richer
Strawberry output object because the engine is Strawberry.

### Reference-package parity checkpoint

| Upstream | `django-strawberry-framework` | Status |
| --- | --- | --- |
| [`strawberry_django.fields.types.DjangoFileType`][upstream-field-types] (`name` / `path` / `size` / `url`) | [`DjangoFileType`][glossary-djangofiletype] public output type; `FIELD_OUTPUT_TYPE_MAP[models.FileField]` read row ([Decision 3](#decision-3--read-side-output-types-djangofiletype--djangoimagetype-mirroring-upstream)) | this card — required parity |
| [`strawberry_django.fields.types.DjangoImageType`][upstream-field-types] (file fields + dimensions) | [`DjangoImageType`][glossary-djangoimagetype] public output type; `FIELD_OUTPUT_TYPE_MAP[models.ImageField]` read row ([Decision 3](#decision-3--read-side-output-types-djangofiletype--djangoimagetype-mirroring-upstream)) | this card — required parity (subfields widened nullable, field-level guard, [Decision 4](#decision-4--read-side-resolution-empty-file-as-null-and-storage-safe-subfield-nullability)) |
| [`strawberry_django` `input_field_type_map` maps file/image → `Upload`][upstream-field-types] | the [`mutations/inputs.py`][mutations-inputs] generator maps both to [`Upload`][glossary-upload-scalar] ([Decision 6](#decision-6--write-side-input-mapping-the-mutation-seam-becomes-upload)) | this card — required parity |
| `strawberry.file_uploads.scalars.Upload` | re-exported from the package root; resolves via Strawberry's built-in default registry — no `_PACKAGE_SCALAR_MAP` entry ([Decision 5](#decision-5--re-export-upload-rather-than-register-it)) | this card — adopt upstream scalar; like upstream, rely on the built-in registry |
| `graphene_django.converter.convert_field_to_string` for `FileField` | rejected as too weak for this package's Strawberry output shape | deliberately not borrowed |

### From `strawberry-graphql-django` — borrow the output shapes and the input mapping

- **Output types.** `DjangoFileType` (`name` / `path` / `size` / `url`) and
  `DjangoImageType(DjangoFileType)` (+ `width` / `height`) — adopted
  field-for-field, so a migrating consumer's `{ avatar { url width } }`
  selection ports unchanged. The one deliberate divergence is subfield
  nullability
  ([Decision 4](#decision-4--read-side-resolution-empty-file-as-null-and-storage-safe-subfield-nullability)).
- **Input mapping.** `FileField` / `ImageField` → `Upload` on the mutation input
  — adopted; the empty-file / partial-update write semantics are the package's
  own
  ([Decision 6](#decision-6--write-side-input-mapping-the-mutation-seam-becomes-upload)).

### From `graphene-django` / DRF — borrow the user-facing shape

- **Automatic, `Meta`-driven conversion.** No `Upload` helper, no decorator, no
  per-field declaration — a file column is converted because it is in the type's
  `Meta.fields` selection, exactly as every other column.
- **Editable / `blank` / `null` / `default` metadata** drives whether an upload
  input is required (the DRF `required=False`-from-metadata rule the shipped
  generator already uses).

### Explicitly do not borrow

- **A single flagged file type with an `is_image` runtime check.** Rejected: two
  distinct types (`DjangoFileType` / `DjangoImageType`) is the upstream shape,
  keeps dimension fields off non-image files, and the MRO walk selects the right
  one automatically.
- **A bespoke package-defined `Upload` scalar.** Rejected: Strawberry ships
  `Upload` (`strawberry.file_uploads.scalars`); re-using it keeps multipart
  parsing on the engine and avoids a parallel scalar incompatible with the
  built-in multipart conventions
  ([Decision 5](#decision-5--re-export-upload-rather-than-register-it)).
- **`graphene-django`'s `FileField` → `String` output.** Rejected: too weak; it
  matches the old `spec-001` simplification this card replaces.
- **Storage-backend abstraction / signed-URL generation.** Out of scope
  ([Non-goals](#non-goals)).

## User-facing API

No new `DjangoType` `Meta` key, no new constructor argument — a file/image
column is converted automatically by being in the type's `Meta.fields`
selection. Three net-new public symbols are added to the package root
([Decision 7](#decision-7--public-surface-three-net-new-root-exported-symbols)).

Read side — a `DjangoType` over a model with file/image columns:

```python
from django.db import models

from django_strawberry_framework import DjangoFileType, DjangoImageType, DjangoType, finalize_django_types


class Asset(models.Model):
    attachment = models.FileField(upload_to="files/")          # required column, but output is nullable by default
    preview = models.ImageField(upload_to="previews/", blank=True)  # optional: blank=True


class AssetType(DjangoType):
    class Meta:
        model = Asset
        fields = ("id", "attachment", "preview")


finalize_django_types()
```

generates:

```graphql
type AssetType {
  id: Int!
  attachment: DjangoFileType
  preview: DjangoImageType
}

type DjangoFileType {
  name: String!
  path: String
  size: Int
  url: String
}

type DjangoImageType {
  name: String!
  path: String
  size: Int
  url: String
  width: Int
  height: Int
}
```

The object field is **nullable by default**, regardless of `null` / `blank`: the
generated parent resolver returns `None` for an empty / falsy `FieldFile`, and an
empty value is reachable even on a `null=False, blank=False` column (legacy rows,
direct `Model.objects.create()`, fixtures, and manual SQL all store `""`), so the
SDL must be nullable to represent it.
[`Meta.required_overrides`][glossary-metarequired-overrides] is the explicit
opt-in for a caller asserting a stronger non-empty contract (`DjangoFileType!`).
`name` is non-null for a present file; `path` / `size` / `url` /
`width` / `height` are **nullable** because storage backends and
corrupt/vanished rows can make individual properties unavailable even when a
file name exists
([Decision 4](#decision-4--read-side-resolution-empty-file-as-null-and-storage-safe-subfield-nullability)).
A missing/empty file resolves the whole object as `null`, never a
`FieldFile.url` `ValueError`. A consumer who wants the legacy `str` (URL/name)
shape keeps it with a concrete annotation override (`attachment: str`), which
bypasses generated field conversion (`convert_field_output` / `convert_scalar`)
per [Scalar field override semantics][glossary-scalar-field-override-semantics].

Write side — a [`DjangoMutation`][glossary-djangomutation] over the same model
generates an `Upload`-typed input field:

```python
import strawberry

from django_strawberry_framework import DjangoMutation, DjangoMutationField


class CreateAsset(DjangoMutation):
    class Meta:
        model = Asset
        operation = "create"


class UpdateAsset(DjangoMutation):
    class Meta:
        model = Asset
        operation = "update"


@strawberry.type
class Mutation:
    create_asset = DjangoMutationField(CreateAsset)
    update_asset = DjangoMutationField(UpdateAsset)
```

generates:

```graphql
scalar Upload

input AssetInput {
  attachment: Upload!
  preview: Upload
}

input AssetPartialInput {
  attachment: Upload
  preview: Upload
}
```

The same per-field requiredness rule applies (a create-input field is required
only when the model field has no usable `default`, is not `null=True`, and is
not `blank=True`); partial inputs are all-optional `UNSET`. A provided upload is
assigned through Django's normal model-field path before `full_clean()` /
`save()`; an omitted upload on update leaves the current file untouched. An
explicit `null` on a `null=False` file column is a field-keyed `FieldError` (the
shipped `_explicit_null_error` guard), **not** a silent clear
([Decision 6](#decision-6--write-side-input-mapping-the-mutation-seam-becomes-upload)). The
schema uses the package's standard `strawberry_config()` (required by `BigInt`);
`Upload` itself needs no special binding — Strawberry resolves it from its
built-in default scalar registry:

```python
schema = strawberry.Schema(query=Query, mutation=Mutation, config=strawberry_config())
```

### Error shapes

- A file column over an **unsupported subclass** with no registered ancestor
  still raises [`ConfigurationError`][glossary-configurationerror] at type
  creation (unchanged — `FileField` / `ImageField` are now supported, but a
  hypothetical unrelated field class is not).
- On write, a missing required `Upload` fails at the GraphQL layer as a missing
  required argument; a model `full_clean()` failure — a declared field validator
  or a model-field / `constraints` violation (e.g. a consumer-attached file
  validator) — populates the
  [`FieldError` envelope][glossary-fielderror-envelope] keyed to the file field,
  returning a null object, not a top-level `GraphQLError`
  ([`spec-036`][spec-036] Decision 7). The generated `DjangoMutation` does
  **not** itself reject arbitrary non-image bytes: Django's *model* `ImageField`
  runs model-field validation and any declared validators, **not** the image
  content sniffing `forms.ImageField` performs. So upload content validation is a
  model-validator concern today and a future
  [`DjangoFormMutation`][glossary-djangoformmutation] /
  [`SerializerMutation`][glossary-serializermutation] concern tomorrow — this
  card does not promise content validation it cannot honestly enforce.
- Reading a populated file whose storage cannot produce a property (a
  non-filesystem `path`, a vanished file) degrades that **subfield** to `null`
  via the narrow per-subfield guard
  ([Decision 4](#decision-4--read-side-resolution-empty-file-as-null-and-storage-safe-subfield-nullability))
  — not a top-level error and not a swallowed resolver bug (the catch list is
  `ValueError` / `OSError` / storage `NotImplementedError`).
## Architectural decisions

### Decision 1 — Spec filename and canonical naming

The spec file lives at **`docs/spec-037-upload_file_image_mapping-0_0_11.md`**.

Justification:

- The structured `spec-<NNN>-<topic>-<0_0_X>.md` convention pinned in
  [`docs/SPECS/NEXT.md`][next] Step 6 bakes the card's NNN (`037`) and target
  patch (`0_0_11`) into the filename.
- The topic slug is `upload_file_image_mapping` — short, snake-case, and broad
  enough to name **both** halves of the card (the write-side `Upload` scalar
  *and* the read-side file/image output objects), which a slug like `uploads` or
  `upload_scalar` undersells.

Alternatives considered (and rejected):

- **`spec-037-upload_scalar-0_0_11.md` / `spec-037-uploads-0_0_11.md`.**
  Rejected: narrows the filename to the write half, while the read-side
  `DjangoFileType` / `DjangoImageType` change is equally in the card DoD.
- **`spec-037-files-0_0_11.md`.** Rejected: too vague; it does not name the
  write-side `Upload` scalar.

### Decision 2 — Card-scope boundary: file/image conversion only, not transport or storage abstraction

This card ships three tightly related artifacts: (1) `FileField` / `ImageField`
output object types; (2) the `Upload` re-export and mutation input
mapping; (3) the version/doc wrap for the now-complete `0.0.11` patch. It does
**not** ship multipart test helpers, an example upload app, remote-storage
policies, image processing, or nested upload writes — each named in
[Non-goals](#non-goals) /
[Out of scope](#out-of-scope-explicitly-tracked-elsewhere).

Justification: the card is sized **S** and its DoD is a converter-table change,
a mutation-input mapping, synthetic-model tests, and glossary docs. The `0.0.14`
[`TestClient`][glossary-testclient] card already owns multipart helper
ergonomics and explicitly depends on this card for the scalar, not vice versa.
Keeping scope here small prevents a file-upload transport design from delaying
the foundational mapping ([`START.md`][start] scope-creep rule).

Alternatives considered (and rejected):

- **Ship only the read side now, write later.** Rejected: the card pairs read
  and write (its DoD names both), and the write seam already exists as a `036`
  `NotImplementedError` waiting to be filled — splitting would leave a
  half-mapped field type and a dangling seam.
- **Add a live fakeshop file model in this card.** Rejected: a `FileField` on a
  fakeshop model needs a media-root fixture and multipart HTTP plumbing —
  heavier than an S card; synthetic-model tests give full coverage
  ([Decision 9](#decision-9--test-placement-package-tests-own-synthetic-fileimage-models)).

### Decision 3 — Read-side output types: `DjangoFileType` / `DjangoImageType` mirroring upstream

[`types/converters.py`][types-converters] defines two `@strawberry.type` output
types and a **new read-output field-type map**, kept separate from
[`SCALAR_MAP`][types-converters]:

- `DjangoFileType` — `name`, `path`, `size`, `url` (the four fields
  [`strawberry-graphql-django`][upstream-field-types] ships), as
  **resolver-backed** Strawberry fields (Decision 4 explains why the subfields
  are resolvers, not bare annotations).
- `DjangoImageType(DjangoFileType)` — adds `width`, `height`.
- `FIELD_OUTPUT_TYPE_MAP[models.FileField] = DjangoFileType`;
  `FIELD_OUTPUT_TYPE_MAP[models.ImageField] = DjangoImageType` — a new
  module-level map the **read** converter consults; *not* a `SCALAR_MAP` row.

**Why a separate map, not a `SCALAR_MAP` rewrite.**
[`SCALAR_MAP`][types-converters] is shared: the read path
([`convert_scalar`][types-converters]) *and* the **filter-input** path
([`filters/inputs.py`][filters-inputs] `_scalar_from_model_field`, which
delegates to [`scalar_for_field`][types-converters]) both walk it. If
`SCALAR_MAP[models.FileField]` returned `DjangoFileType`, a
[`FilterSet`][glossary-filterset] over a file column would generate a GraphQL
**input** field typed as an **output** object — an invalid schema shape and a
regression outside this card's surface. So the read side gains a
`FIELD_OUTPUT_TYPE_MAP` MRO lookup — owned by a dedicated read-only wrapper, not
folded into `convert_scalar` (below) — consulted *before* `SCALAR_MAP` for a
file/image column; `SCALAR_MAP[models.FileField]` / `[models.ImageField]` stay
`str`, so filter-input generation keeps calling `scalar_for_field`, still sees
`str`, and never produces an output-typed input (a file column still filters as
a scalar string, unchanged).

**The read-side lookup is a thin wrapper, not an expansion of `convert_scalar`.**
A function still named [`convert_scalar`][types-converters] returning a
`DjangoFileType` / `DjangoImageType` *object* type would blur an abstraction the
filter-input path also depends on. So [`convert_scalar`][types-converters] and
[`scalar_for_field`][types-converters] stay scalar-shaped, and a new read-only
helper `convert_field_output(field, type_name, *, force_nullable=None)` in
[`types/converters.py`][types-converters] owns the `FIELD_OUTPUT_TYPE_MAP` MRO
lookup: for a file/image column it returns the matching output object (nullable
by default as `<object> | None`, independent of `blank` / `null`, per
[Decision 4](#decision-4--read-side-resolution-empty-file-as-null-and-storage-safe-subfield-nullability)),
and otherwise delegates to [`convert_scalar`][types-converters] for true scalar
columns. [`types/base.py`][types-base] `_build_annotations` calls
`convert_field_output` for non-relation columns (where it calls
[`convert_scalar`][types-converters] directly today), so "scalar conversion"
never emits an object type and the scalar/output split stays legible to future
maintainers.

`ImageField` is a `FileField` subclass, so lookup order matters in the new map
exactly as in `SCALAR_MAP`: the MRO walk tests `type(field).__mro__` and
`ImageField` appears in its own MRO *before* `FileField`, so an `ImageField`
(and a consumer `ImageField` subclass) resolves to `DjangoImageType`, never
falling through to `DjangoFileType`.

The map lookup alone is insufficient: a Django model attribute for a file column
returns a falsy `FieldFile` / `ImageFieldFile` descriptor even when no file is
attached, and accessing `url` / `path` / `size` on it raises. So this card adds
a generated **file-column read resolver**, attached at `DjangoType`
finalization in the **same phase as the relation resolvers**:
[`types/resolvers.py`][types-resolvers] defines the `_attach_file_resolvers`
helper, and [`types/finalizer.py`][types-finalizer] calls it inside the same
finalizer loop that runs `_attach_relation_resolvers` (the only place resolvers
attach before `strawberry.type(...)` freezes the class), immediately after the
relation pass and before interface injection.
The parent resolver does object nullability only — `return None if not value
else value` — and Strawberry then resolves the subfields off the returned
`FieldFile` through `DjangoFileType`'s own **resolver-backed** fields (the
per-subfield guard, [Decision 4](#decision-4--read-side-resolution-empty-file-as-null-and-storage-safe-subfield-nullability)).
The attachment **skips `definition.consumer_authored_fields`** (the override
union — annotation-only *and* assigned-`strawberry.field` overrides — that
`_build_annotations` honors, stored on [`DjangoTypeDefinition`][types-base]).
This skip is deliberately **broader** than the relation pass's: the finalizer
calls `_attach_relation_resolvers` with `skip_field_names=`
`definition.consumer_assigned_relation_fields` (assigned relation overrides
only), but the file pass must pass `definition.consumer_authored_fields`, so a
consumer annotation *or* `strawberry.field` for a file column — e.g.
`attachment: str`
([Scalar field override semantics][glossary-scalar-field-override-semantics]) —
keeps the legacy `str` shape and receives **no** generated resolver and no
object type. Skipping only assigned `strawberry.field(...)` overrides (not
annotation-only ones) would silently clobber an annotation opt-out, so the skip
keys on the full `consumer_authored_fields` union, not on the assignment alone.

Changing `FileField` / `ImageField` **read** output from `str` to an object
type is a **breaking wire-format change** — parallel to the
[`PositiveBigIntegerField → BigInt`][glossary-specialized-scalar-conversions]
(`0.0.6`) and model-anchored `GlobalID` (`0.0.9`) precedents — acceptable
pre-`1.0.0`, recorded in the glossary, with the consumer-annotation override
(`attachment: str`,
[Scalar field override semantics][glossary-scalar-field-override-semantics]) as
the one-line opt-out. The **filter** input shape for a file column is unchanged
(still scalar `str`), so no filter schema breaks. No in-repo example breaks (no
fakeshop model uses a file column).

Justification: structured output is the read-side parity goal and the lossy
`str` was always a placeholder; mirroring upstream's field names lets a
migrating consumer's selection port unchanged. Two distinct types keep dimension
fields off non-image files. A separate output map keeps the read change off the
shared scalar/filter surface.

Alternatives considered (and rejected):

- **Put the object types directly in `SCALAR_MAP`.** Rejected (the P0 finding):
  a [`FilterSet`][glossary-filterset] over a file column would emit an output
  object as a filter input — an invalid schema. The read-output map keeps the
  read change off the shared scalar/filter path; a package test pins the
  filter-input scalar lookup over a synthetic `FileField` / `ImageField` to a
  scalar `str` (`scalar_for_field` and `_scalar_from_model_field` both return
  `str`, `SCALAR_MAP` rows untouched) so this cannot regress silently. (The test
  pins the delegation path the FilterSet input generator uses rather than a full
  `FilterSet.Meta.fields` materialization, because django_filter raises an
  `AssertionError` on an auto-generated bare-`FileField` filter — an
  unrecognized field type — before any package code runs; the scalar-lookup pin
  is equally distinguishing.)
- **Reject file/image filters with `ConfigurationError` and route reads through
  a renamed converter.** Considered: cleaner once file filtering has a
  deliberate contract, but it is a behavior change for any consumer filtering on
  a file column's stored name today. Deferred — file columns keep their scalar
  `str` filter mapping until a file-filter contract is designed
  ([Risks](#risks-and-open-questions)).
- **Leave output as `str` and ship only `Upload`.** Rejected: fails the
  read-side DoD and leaves consumers hand-rolling file metadata.
- **Map output to `str | None` but document custom resolvers for metadata.**
  Rejected: preserves the weak contract and ignores the upstream parity target.
- **One `DjangoFileType` with nullable `width` / `height`.** Rejected: a
  non-image `FileField` has no dimensions; the `DjangoImageType` subclass scopes
  them to images, matching upstream.
- **Add a settings flag to keep `str` globally.** Rejected: a settings key for a
  one-line per-field override is over-engineering ([`AGENTS.md`][agents]); the
  annotation override is the finer-grained opt-out.

### Decision 4 — Read-side resolution: empty file as `null` and storage-safe subfield nullability

Two layers, at two different levels:

- **Object-field nullability (parent level).** A file/image column maps to
  `DjangoFileType | None` **by default**, independent of `null` / `blank`. The
  generated parent resolver
  ([Decision 3](#decision-3--read-side-output-types-djangofiletype--djangoimagetype-mirroring-upstream))
  returns `None` for an empty / falsy `FieldFile`, and an empty value is
  reachable even on a `null=False, blank=False` column — Django stores `""` for
  "no file", and legacy rows, direct `Model.objects.create()`, fixtures, and
  manual SQL can all leave it empty (a `blank=False` column is a form-validation
  constraint, **not** a database non-empty invariant). A non-null SDL would turn
  that `None` into a top-level `Cannot return null for non-nullable field` error,
  so the field must be nullable to represent what the resolver can return. This
  composes with the [`Meta.nullable_overrides`][glossary-metanullable-overrides] /
  [`Meta.required_overrides`][glossary-metarequired-overrides] `force_nullable`
  tri-state — `required_overrides` (`force_nullable=False`) is the explicit
  opt-in to the stricter `DjangoFileType!` contract, for a consumer that
  guarantees a file is always present (the "contract, not data" caveat the
  override entry documents).
- **Subfield nullability (field level).** `path` / `size` / `url` (and `width` /
  `height` on images) are **nullable**, while `name` stays non-null — a
  deliberate divergence from upstream's all-non-null `path: str`.

**The guard must live on the subfields, not the parent resolver.** The parent
resolver returns the bound `FieldFile`; Strawberry then resolves each *selected*
subfield by `getattr(file_file, "path" | "url" | …)` **after** and **outside**
the parent resolver — and those property accesses are exactly what raise on a
non-filesystem backend (S3 `FieldFile.path` → `NotImplementedError`) or a
vanished file (`.size` → `OSError`; `.url` on local storage is string-built from
`MEDIA_URL` and does *not* raise). A `try/except` in
the parent resolver cannot reach them. So `DjangoFileType` / `DjangoImageType`
are defined with **resolver-backed** fields, each delegating to a shared
`_safe_file_attr(file_file, attr)` helper that performs the **narrow** catch
(`ValueError` / `OSError` / storage `NotImplementedError` → `None`). The parent
resolver decides only object nullability (`not value` → `None`); each subfield
owns its own guard, so selecting only `{ url }`, only `{ path }`, or several
subfields each degrade **independently**. `name` is read without the guard (a
stored string, always present whenever the object is non-null).

**Django path-safety exceptions are *not* silently nulled.** A corrupt or
hostile stored name can make storage raise
`django.core.exceptions.SuspiciousFileOperation` — a `SuspiciousOperation`
subclass, **not** a `ValueError` / `OSError`, so the narrow catch does not cover
it. `_safe_file_attr` deliberately does **not** catch it: a path-traversal /
escaped-name condition is a security signal that should surface as a top-level
error, not hide as a `null` subfield. This is an intentional decision, not an
accidental gap. Fallback: if operators prefer graceful degradation over
visibility, `SuspiciousFileOperation` can be added to the helper's catch set,
but the default is to let it propagate
([Risks](#risks-and-open-questions)).

Justification: a file field with no file must resolve to `null`, not raise; a
storage quirk on one property must not take down the query; and the guard must
sit where the raising access happens (the subfield), which the parent resolver
cannot reach. The narrow catch list keeps the guard from swallowing genuine
resolver bugs and from masking security-relevant path errors. `name` is reliably
present whenever the object exists (the object is `null` for an absent file), so
it stays non-null.

Alternatives considered (and rejected):

- **Guard only in the parent resolver (return the `FieldFile`, catch there).**
  Rejected (the P0 finding): subfield property access happens later, in
  Strawberry's default per-field resolution, outside the parent's `try/except`;
  a blank or vanished-file selection of `{ url }` would still 500. The guard
  must be at the field level.
- **A wrapper object whose properties perform the catch.** Considered and
  equivalent; resolver-backed `@strawberry.field`s on the two types are the
  chosen shape because they keep the guard in the type definition and need no
  extra wrapper class. Either satisfies the field-level requirement.
- **Match upstream's all-non-null subfields and document the `path` caveat.**
  Rejected: it leaves a latent 500 on non-filesystem storage / vanished files;
  the nullable-subfield contract is the safer engineering choice and the SDL
  divergence is small and documented.
- **Widen the object on `field.null` only — or on `null` / `blank`.** Rejected:
  the resolver returns `None` for *any* empty `FieldFile`, including on a
  `null=False, blank=False` column (legacy rows, direct `Model.objects.create()`,
  fixtures, and manual SQL all store `""`), so keying nullability on the column
  flags at all leaves a guaranteed non-null violation. The object is **nullable
  by default**; `required_overrides` is the explicit opt-in to a non-null
  contract.
- **Catch a broad `Exception` (or fold `SuspiciousFileOperation` into the
  guard) by default.** Rejected: it would hide real bugs and mask path-traversal
  signals; the catch list is narrowed to storage-shaped errors.

### Decision 5 — Re-export `Upload` rather than register it

`Upload` is a Strawberry **built-in**: Strawberry registers
`Upload: UploadDefinition` in its `DEFAULT_SCALAR_REGISTRY`, and the schema
converter seeds that registry into every schema (`{**DEFAULT_SCALAR_REGISTRY}`)
*before* merging any package `scalar_map`. So an `Upload`-annotated field
resolves in **any** schema — with or without
[`strawberry_config`][glossary-strawberry-config].
[`scalars.py`][scalars] (and the package root, [`__init__.py`][init]) therefore
only **re-export** `Upload` (and `UploadDefinition`) from
`strawberry.file_uploads.scalars` for the public surface; the package adds **no**
`_PACKAGE_SCALAR_MAP` entry for it.

This is the deliberate contrast with [`BigInt`][glossary-bigint-scalar]:
`BigInt = NewType("BigInt", int)` is a package-custom scalar **absent** from
`DEFAULT_SCALAR_REGISTRY`, so it genuinely needs its `_PACKAGE_SCALAR_MAP` entry
to resolve. `Upload` shares BigInt's structural shape (a `NewType` paired with a
`scalar(...)` `ScalarDefinition`) but **not** its registration need — it is
already a pre-registered scalar.

Justification: registering `Upload` in `_PACKAGE_SCALAR_MAP` would be redundant
(it already resolves) and misleading (it would imply a binding requirement that
does not exist). [`strawberry-graphql-django`][upstream-field-types] takes
exactly this approach — its `input_field_type_map` maps `FileField` /
`ImageField` to the bare `Upload` `NewType` with no custom scalar registration,
relying on the built-in registry. Re-using Strawberry's scalar also keeps
multipart-request parsing on the engine.

Alternatives considered (and rejected):

- **Add `Upload` to `_PACKAGE_SCALAR_MAP` for symmetry with `BigInt`.**
  Rejected: redundant (the default registry already resolves it) and
  misleading; it would also manufacture an `extra_scalar_map={Upload: ...}`
  collision contract for a scalar the package does not own.
- **Define a wrapper `NewType` instead of re-exporting Strawberry's `Upload`.**
  Rejected: a second upload scalar would be incompatible with the engine's
  built-in multipart conventions and force clients to special-case it.
- **Do not export `Upload` at all; let consumers import it from Strawberry.**
  Rejected: generated inputs reference `Upload`, and a consumer hand-writing an
  upload field should reach for it at the package root alongside
  [`BigInt`][glossary-bigint-scalar] — re-export is the public-surface
  convenience ([Decision 7](#decision-7--public-surface-three-net-new-root-exported-symbols)).

### Decision 6 — Write-side input mapping: the mutation seam becomes `Upload`

The [`spec-036`][spec-036] fail-loud branch in
[`mutations/inputs.py`][mutations-inputs] #"Upload staged seam
(TODO-ALPHA-037-0.0.11)" is removed and replaced with a real mapping:
`FileField` / `ImageField` → `Upload`, required per the shipped per-field rule
(a `blank=False` / `null=False` / no-default file column is required in the
create `<Model>Input`, optional with `strawberry.UNSET` otherwise and in
`<Model>PartialInput`), widened to `Upload | None` on `blank` / `null`.
File/image fields are **scalar** input fields for naming: the Python attribute
is the model field name (`attachment`, not `attachment_id`), and the GraphQL
name follows the normal camel-case converter. The generator continues to own
requiredness, `UNSET`, partial-update omission, `Meta.fields` / `Meta.exclude`
narrowing, and custom-input merge. **On the write side, no new resolver code is
presumed:** the shipped pipeline already passes scalar attrs into `model(**attrs)`
(create) / `setattr` (update) before `full_clean()` / `save()`, and Django's
`FileField` descriptor accepts an `UploadedFile` directly — so a file column
flows through the generic scalar-assignment path. Slice 2 *verifies* this with a
test and adds a file-specific branch in [`mutations/resolvers.py`][mutations-resolvers]
only if that test proves the generic path fails.

**Omittable is not nullable — explicit `null` is a field error, not a file
clear.** A `blank=True` / `null=True` / defaulted file column widens to
`Upload | None` and may be **omitted** (`strawberry.UNSET` → the stored file is
left unchanged). But the optional-input machinery that widens the annotation to
`| None` does **not** make an explicit `null` a clear instruction. The shipped
resolver's `_explicit_null_error` decode-time guard
([`mutations/resolvers.py`][mutations-resolvers]) already returns a
[`FieldError`][glossary-fielderror-envelope] (`"This field cannot be null."`) for
a provided `None` on **any** `null=False` column — including the common
`blank=True, null=False` shape, which `full_clean()` alone would let slip to a
`save()`-time `IntegrityError` — before any DB work. File columns are scalar
inputs, so they inherit this guard for free: omitting the field leaves the file
untouched, while sending explicit `null` on a `null=False` file column is a
field-keyed error, not a silent clear. A `null=True` file column treats `None` as
a valid clear only insofar as the model field and shipped pipeline already accept
it; clearing is otherwise out of scope ([Risks](#risks-and-open-questions)).

**The `036` file-column merge-override exception is lifted.**
[`spec-036`][spec-036] CR-6 pinned that file columns were "the one exception to
the merge override" because the `NotImplementedError` ran *before* the
`Meta.input_class` override skip. With `Upload` wired, the file-column branch
emits a valid field, so a file column now participates in the
[`Meta.input_class`][glossary-input-type-generation] /
`Meta.partial_input_class` merge override like any scalar; Slice 2 removes the
CR-6 carve-out and updates its `test_inputs.py` coverage.

Justification: the seam was built for exactly this card; reusing the generator
prevents a second write-input path just for uploads and keeps custom-input merge
consistent with every other scalar.

Alternatives considered (and rejected):

- **Keep the `NotImplementedError` and require `Meta.exclude`.** Rejected: that
  was the staging guard before `037`; after this card it would make the card a
  no-op for generated mutation inputs.
- **Require a consumer-authored `input_class` for upload fields.** Rejected:
  violates the generated-input goal and creates a bespoke escape hatch where the
  core package should know the mapping.
- **Represent uploads as `str` paths.** Rejected: unsafe and not a GraphQL
  upload contract; the client sends multipart upload values, not server paths.
- **Add a dedicated file-assignment branch in the write resolver up front.**
  Rejected by default (the P2 finding): the existing scalar `setattr` /
  `model(**attrs)` path already assigns an `UploadedFile`, so a branch is added
  only if a test proves the generic path fails — avoiding a divergent write path
  for files.

### Decision 7 — Public surface: three net-new root-exported symbols

[`__init__.py`][init] re-exports and adds to `__all__`: `Upload` (the scalar,
from [`scalars.py`][scalars]), `DjangoFileType`, and `DjangoImageType` (from
[`types/converters.py`][types-converters]). All three already have
[`docs/GLOSSARY.md`][glossary] entries (`planned for 0.0.11`), so Slice 4
promotes the existing entries to `shipped (0.0.11)` and adds the three to the
glossary **Public exports** list; no net-new glossary *heading* is created by
this card.

Justification: root export matches the audience — `Upload` is referenced
wherever a consumer hand-writes an input field, and the two output types are the
field types a consumer names in custom resolvers / `strawberry.field`
annotations; all belong at the root alongside [`BigInt`][glossary-bigint-scalar]
/ [`DjangoType`][glossary-djangotype], parallel to how
[`BigInt`][glossary-bigint-scalar] ([`spec-017`][spec-017]) is root-exported.
These are **framework-provided generated / helper output types**, not a new
consumer-authored decorator API — they stay within the package's `class
Meta`-driven, DRF-first posture ([`GOAL.md`][goal]) and add no decorator-first
consumer surface.

Alternatives considered (and rejected):

- **Export only from a `scalars` / `types` namespace.** Rejected: the symbols
  are referenced inside schema modules alongside root-exported types; the
  package's settled posture is to root-export consumer-facing scalars and types.
- **Do not export the output types (auto-generated, never named).** Rejected: a
  consumer overriding a file field's resolver, or annotating a computed file
  field, must be able to name them; the glossary already lists them as public.

### Decision 8 — No new `Meta` key, no new setting, no dynamic storage policy

This card changes existing conversion behavior; it adds no new `DjangoType`
`Meta` key and no `DJANGO_STRAWBERRY_FRAMEWORK` setting.
[`Meta.fields`][glossary-metafields] / [`Meta.exclude`][glossary-metaexclude]
remain the opt-in / opt-out selectors;
[`Meta.nullable_overrides`][glossary-metanullable-overrides] /
[`Meta.required_overrides`][glossary-metarequired-overrides] remain the
nullability overrides; consumer-authored scalar overrides still bypass generated
conversion.

Justification: the repository rule is explicit — add settings keys only when the
feature needs them ([`AGENTS.md`][agents]). The file/image mapping has no
project-wide policy knob; the existing scalar-override semantics already provide
the escape hatch.

This card reads **no** setting, so it adds no settings-read or per-query
validation overhead. For the record, the standing architectural line — should a
future file/image spec ever need a setting — is the existing
[`RELAY_GLOBALID_STRATEGY`][types-relay] shape: [`conf.py`][conf] owns top-level
settings-dict normalization and reload wiring; a domain module owns key-specific
validation where that validation needs local domain concepts (avoiding import
cycles); and any setting that affects request behavior is
**resolved / validated / stamped once at schema build / finalization** — as
[`types/relay.py`][types-relay] reads `RELAY_GLOBALID_STRATEGY` and stamps
`definition.effective_globalid_strategy`, which per-query resolvers then read
without re-reading or re-validating the setting. A query-time settings read is
not introduced here and would be rejected if proposed.

### Decision 9 — Test placement: package tests own synthetic file/image models

> **Superseded (post-ship, 2026-06-20 round-4 review).** A live fakeshop
> file/image acceptance surface was added after all. The `scalars` app gained a
> `MediaSpecimen` model (`FileField` + `ImageField`), a `MediaSpecimenType`, and a
> file-backed `createMediaSpecimen` mutation, with live `/graphql/` tests in
> `examples/fakeshop/test_query/test_uploads_api.py`: the read output objects, the
> default-nullable SDL shape (a *required* column rendering nullable), the
> empty-file object-`null` case, the `Upload` input SDL, and a **real multipart
> upload** (the fakeshop `GraphQLView` enables `multipart_uploads_enabled=True`).
> The [`examples/fakeshop/test_query/README.md`][test-query-readme] live-coverage
> rule prevailed over the "prefer the card" deferral recorded below: file/image
> output IS SQLite-reachable, so its public HTTP contract must be earned live. The
> synthetic-model package tests below **remain** for the storage-backend
> fault-injection and corrupt-image-dimension edges, which need a mocked
> non-filesystem backend and so are genuinely unreachable from a live request. The
> broader products/fakeshop activation stays [`TODO-BETA-051-0.1.5`][kanban]. The
> original (now-historical) deferral rationale follows.

No fakeshop model has a file/image field, and adding one solely for this card
would be example-app churn, not a real acceptance path. Therefore:

- converter and generated-output behavior live in [`tests/types/`][test-types];
- generated mutation input behavior lives in
  [`tests/mutations/`][test-mutations];
- scalar registration / resolution and root-export pins live in
  [`tests/test_scalars.py`][test-scalars] /
  [`tests/base/test_init.py`][test-base-init];
- live `/graphql/` tests are added **only** if implementation naturally exposes
  a file/image field through an existing fakeshop app.

Coverage uses **synthetic models** (a test-only model with `FileField` /
`ImageField` columns over a `tmp_path` storage) — the [`spec-017`][spec-017]
converter-table precedent. Per the
[`examples/fakeshop/test_query/README.md`][test-query-readme] rule, a line
reachable through a real fakeshop query belongs in live HTTP; a synthetic
file/image model that exists only for a converter branch belongs in package
tests. Per the [`docs/SPECS/NEXT.md`][next] "prefer the card" rule (the card DoD
scopes to synthetic-model tests), the synthetic-model strategy wins and a live
fakeshop file-upload surface is deferred to fakeshop activation
([`TODO-BETA-051-0.1.5`][kanban]); the tension is recorded, not silently
resolved.

**Fixture shape.** Converter-only tests can use an unmanaged synthetic model with
no table, but resolver and mutation tests need real rows and real storage side
effects. Reuse the repo's established `connection.schema_editor()` create/delete
pattern (`tests/test_relay_connection.py`, `tests/test_permissions.py`): a
test-only model under a unique `app_label` with `managed = False`, given a real
table via `connection.schema_editor().create_model(...)` (dropped in reverse on
teardown), and `override_settings(MEDIA_ROOT=tmp_path)` (or a field-level temp
`storage=`) so writes land in a throwaway directory. This keeps the file/image
tests local to [`tests/`][test-types] with **no** migrations and **no** fakeshop
app churn, and exercises `FieldFile.path` / `.size` / `.url` (and image
dimensions) over honest temp storage.

Alternatives considered (and rejected):

- **Add a live fakeshop file model + multipart HTTP test now.** Rejected: out of
  scope for an S converter card.
- **Mock the storage backend instead of a real `tmp_path` storage.** Rejected: a
  real temp-dir storage exercises `FieldFile.path` / `.size` / `.url` honestly;
  mock only the non-filesystem-`path` case, where a real backend is impractical,
  to cover the
  [Decision 4](#decision-4--read-side-resolution-empty-file-as-null-and-storage-safe-subfield-nullability)
  guard.

### Decision 10 — This card owns the final `0.0.11` version bump

Unlike [`spec-036`][spec-036] (which shared `0.0.11` with this then-unstarted
sibling and so deferred the bump to "the joint cut"), **this card is the joint
cut.** [`docs/SPECS/NEXT.md`][next] Step 3 scopes "multiple WIP cards share the
patch" to the `## In progress` column; `036` is already `DONE` and `037` is the
**lone** `## In progress` entry on `0.0.11`, so the deferral condition is not
met for `037`. Leaving the version at `0.0.10` after `037` ships would make the
docs and public exports claim `0.0.11` behavior under a `0.0.10` identity, and
nobody would ever bump it (both cards would have deferred). Slice 4 therefore
aligns the version quintet:

- [`pyproject.toml`][pyproject]
- `__version__` in [`__init__.py`][init]
- [`tests/base/test_init.py::test_version`][test-base-init]
- the [`docs/GLOSSARY.md`][glossary] package-version line
- `uv.lock` if it carries the package version

Justification: `037` closes the `0.0.11` feature set, so it owns the cut —
exactly the card `036` Decision 13 deferred to. The bump moves only after the
mapping, tests, and docs are complete (Slice 4), never in Slice 1.

Alternatives considered (and rejected):

- **Defer again to a separate release-alignment card.** Rejected: no such WIP
  card exists, and `036` already deferred to this joint cut; a second deferral
  would orphan the bump.
- **Treat `036` (DONE) as a co-WIP card and defer per the multi-card rule.**
  Rejected: the NEXT.md rule keys on the `## In progress` column, where `037`
  stands alone; a DONE card is not a WIP co-owner.
- **Bump in Slice 1.** Rejected: the version should move only after the feature
  and docs are complete.

## Implementation plan

Four slices. Slices 1–2 are independent (read vs write modules); Slice 3 depends
on both; Slice 4 is doc + version-cut only. Line deltas are planning estimates.

| Slice | Files touched | New / changed tests | Approx. delta |
| --- | --- | --- | --- |
| 1 — read output objects + `FIELD_OUTPUT_TYPE_MAP` + file-column resolver | [`types/converters.py`][types-converters] (resolver-backed `DjangoFileType` / `DjangoImageType` + `_safe_file_attr` + new `FIELD_OUTPUT_TYPE_MAP` + read-only `convert_field_output` wrapper; `convert_scalar` / `scalar_for_field` / `SCALAR_MAP` file rows stay scalar-only), [`types/base.py`][types-base] (`_build_annotations` calls `convert_field_output` + default-nullable file/image shape), [`types/resolvers.py`][types-resolvers] (define `_attach_file_resolvers` parent empty-file resolver), [`types/finalizer.py`][types-finalizer] (call `_attach_file_resolvers` in the relation-resolver loop, passing `consumer_authored_fields`), [`pyproject.toml`][pyproject] (add Pillow to the dev/test extras for image-dimension tests, unless the [Risks](#risks-and-open-questions) stand-in fallback is taken) | [`tests/types/test_converters.py`][test-types] (~11 — incl. `FilterSet` over `FileField` stays scalar) + [`tests/types/test_resolvers.py`][test-types] (~8 — empty→null, populated subfields, per-subfield isolation, image dims) + [`tests/types/test_base.py`][test-types] (~2 — `attachment: str` gets no resolver) | `+190 / -10` |
| 2 — `Upload` re-export + mutation input (+ verify write path) | [`scalars.py`][scalars] (re-export + docstring fix), [`mutations/inputs.py`][mutations-inputs] (seam → `Upload`), [`mutations/resolvers.py`][mutations-resolvers] (verify generic scalar path; branch only if a test proves a gap) | [`tests/test_scalars.py`][test-scalars] (~3 — incl. resolves with/without `strawberry_config()`) + [`tests/mutations/test_inputs.py`][test-mutations] (~6 — file→`Upload` required/optional, `| None`, lifted CR-6) + [`tests/mutations/test_resolvers.py`][test-mutations] (~5 — create/partial via the generic path, no `NotImplementedError`) | `+110 / -40` |
| 3 — public exports + coverage hardening | [`__init__.py`][init] (3 exports + `__all__`) | [`tests/base/test_init.py`][test-base-init] (~3 exports) + storage/null/dimension hardening | `+50 / -0` |
| 4 — docs + `0.0.11` version cut + card wrap | [`docs/GLOSSARY.md`][glossary], [`docs/README.md`][docs-readme], [`README.md`][readme], [`GOAL.md`][goal], [`TODAY.md`][today], [`CHANGELOG.md`][changelog], [`KANBAN.md`][kanban], version files ([`pyproject.toml`][pyproject], [`__init__.py`][init], [`tests/base/test_init.py`][test-base-init]) | `test_version` → `0.0.11` | `+90 / -45` |

Total expected delta: ~`+460 / -95` — an S–M cut (the version cut, the
`FIELD_OUTPUT_TYPE_MAP` split, and the field-level subfield guard add a little
over the bare table change), matching the card's relative size. Staged
`spec-036` TODO anchors naming the upload seam are removed in the change that
ships Slice 2; the [`scalars.py`][scalars] docstring's stale
`TODO-ALPHA-035-0.0.11` reference is corrected in the same slice. New source
comments should be minimal — only the `FIELD_OUTPUT_TYPE_MAP` / `SCALAR_MAP`
split rationale, the field-level `_safe_file_attr` guard, and the
nullable-subfield rationale need explanatory comments.

## Edge cases and constraints

- **Empty file descriptor.** A `FieldFile` is falsy when no file name is stored;
  the generated output returns `None` for the whole field, so selecting
  `attachment { url }` on an empty file does not raise.
- **Empty value on a `null=False, blank=False` column.** File columns store `""`
  (a falsy `FieldFile`) for "no file", reachable even when neither `null` nor
  `blank` is set — `blank=False` is a form-validation constraint, not a database
  non-empty invariant (legacy rows, direct `Model.objects.create()`, fixtures,
  and manual SQL can all leave it empty). File/image output is therefore
  **nullable by default**, independent of `null` / `blank`, unless
  [`Meta.required_overrides`][glossary-metarequired-overrides] forces the
  stricter contract.
- **`Meta.required_overrides` on a blank file field.** Allowed, but the consumer
  owns the invariant; if the row contains an empty value, Strawberry's ordinary
  non-null violation is the correct signal ("contract, not data").
- **Storage without local `path`.** `path` is nullable; a backend that cannot
  provide a filesystem path degrades that subfield to `null`, not a top-level
  failure.
- **Missing file in storage.** `size` / `url` / `width` / `height` are nullable
  so a storage lookup failure degrades to a `null` subfield via the narrow catch
  (`ValueError` / `OSError` / storage `NotImplementedError`) on each subfield
  resolver rather than a 500.
- **Storage-metadata cost at list scale.** Resolving `size` (and sometimes `url`
  / `width` / `height`) asks Django storage for per-object metadata, which can
  hit a remote backend once per selected object and subfield. The subfields are
  selection-gated (only a selected subfield resolves), but the optimizer
  **cannot** prefetch object-store metadata and file columns are correctly not
  relation-planned. This card guards storage-shaped failures (degrade-to-`null`)
  but does **not** cache or batch storage calls; selecting file metadata over a
  large connection is a read-side cost the consumer weighs
  ([Risks](#risks-and-open-questions)).
- **Path-safety errors are not nulled.**
  `django.core.exceptions.SuspiciousFileOperation` from a corrupt / hostile
  stored name is **not** caught by `_safe_file_attr` (it is a
  `SuspiciousOperation`, not a `ValueError` / `OSError`); it propagates as a
  top-level error for security visibility, by design
  ([Decision 4](#decision-4--read-side-resolution-empty-file-as-null-and-storage-safe-subfield-nullability)).
- **Image dimensions at read time.** `width` / `height` are nullable and degrade
  to `null` via `_safe_file_attr` when the stored image is missing / corrupt or
  the backend cannot read dimensions; they are not forced to validate the image
  during schema resolution. A consumer using `ImageField` already has Pillow
  (Django requires it for the field); the Pillow **test** dependency is settled
  in [Risks](#risks-and-open-questions).
- **Consumer scalar override.** A consumer annotation *or* `strawberry.field` on
  a file/image column lands in `consumer_authored_fields`, which the file-resolver
  attachment skips — so `attachment: str` bypasses both the `FIELD_OUTPUT_TYPE_MAP`
  output mapping and the generated resolver, exactly like every other scalar
  override; on the write side, a consumer `Meta.input_class` field for a file
  column is now honored via the merge override (lifted CR-6 exception,
  [Decision 6](#decision-6--write-side-input-mapping-the-mutation-seam-becomes-upload)).
- **MRO precedence (`ImageField` is a `FileField`).** Both `FIELD_OUTPUT_TYPE_MAP`
  rows are explicit; the MRO walk hits `ImageField`'s own row before `FileField`,
  so an `ImageField` (and a consumer subclass) resolves to `DjangoImageType`.
- **File-column filter input.** A [`FilterSet`][glossary-filterset] over a file
  column still generates a **scalar** (`str`) filter input: the output-object
  mapping lives in `FIELD_OUTPUT_TYPE_MAP` (consulted only by the read converter),
  while filter inputs keep walking `SCALAR_MAP` via `scalar_for_field`, so no
  output type leaks into a filter input. The semantics are filtering the **stored
  file name / path string**, not the file metadata (`url` / `size` / `width` /
  `height`) — those object subfields are read-only output, never filter inputs
  ([Decision 3](#decision-3--read-side-output-types-djangofiletype--djangoimagetype-mirroring-upstream)).
- **Mutation partial update.** Omitted upload fields stay `UNSET` and leave the
  stored file unchanged; a provided upload replaces the file through Django's
  normal assignment path. An explicit `null` on a `null=False` file column is
  rejected with a field-keyed `FieldError` by the existing `_explicit_null_error`
  decode guard (omittable ≠ nullable); clearing with `null` is not guaranteed by
  this card unless the field is `null=True` and the shipped pipeline accepts it
  ([Risks](#risks-and-open-questions)).
- **Multipart transport.** The package exposes `Upload` without shipping a
  test-client helper; consumers use Strawberry/Django's existing multipart
  request handling until the `0.0.14` [`TestClient`][glossary-testclient] helper
  lands.
- **`Upload` resolves without extra config.** `Upload` is in Strawberry's
  built-in `DEFAULT_SCALAR_REGISTRY`, so an `Upload`-annotated field resolves in
  any schema, with or without `config=strawberry_config()`. The config factory
  is still required by the package-custom [`BigInt`][glossary-bigint-scalar]
  scalar, which is absent from the default registry.
- **No `DjangoType` `Meta` key added.** [`DEFERRED_META_KEYS`][types-base] /
  `ALLOWED_META_KEYS` are byte-unchanged; the conversion is automatic from the
  column type.

## Test plan

Test placement follows the [`AGENTS.md`][agents] mirror rule; coverage uses
**synthetic models** (a test-only model with `FileField` / `ImageField` columns
over a `tmp_path` storage), with no live fakeshop surface
([Decision 9](#decision-9--test-placement-package-tests-own-synthetic-fileimage-models)).

- **Converter / map tests** ([`tests/types/test_converters.py`][test-types]):
  `FileField` → `DjangoFileType`, `ImageField` → `DjangoImageType` via
  `FIELD_OUTPUT_TYPE_MAP`, MRO precedence (incl. a consumer `ImageField`
  subclass), file/image output is `| None` by default (independent of `null` /
  `blank`), `Meta.nullable_overrides` / `Meta.required_overrides` still win, `Meta.exclude`
  remains the opt-out; **and a [`FilterSet`][glossary-filterset] over a synthetic
  `FileField` still produces a scalar (`str`) filter input, never
  `DjangoFileType`** (the P0 split regression guard).
- **Generated output resolver tests**
  ([`tests/types/test_resolvers.py`][test-types]): a synthetic model with
  non-empty file/image values resolves `name` / `path` / `size` / `url` (+
  `width` / `height`) through schema execution; an empty file resolves the
  object as `null` (including on a required `null=False, blank=False` column —
  the default-nullable regression guard for the empty-required-file edge);
  **per-subfield isolation** — a failing `path` returns `null`
  while `url` / `name` still resolve, selecting one subfield at a time (each
  subfield resolver guards independently, not the parent); the
  consumer-annotation override (`attachment: str`) receives **no** generated
  resolver or object type (the attachment skips `consumer_authored_fields`).
  Image dimensions (`width` / `height`) are covered against a tiny valid
  in-memory image via the dev-only Pillow dependency (or the lightweight stand-in
  of the [Risks](#risks-and-open-questions) fallback) — never a Pillow-conditional
  `skip`, which would slip uncovered branches past `fail_under = 100`.
- **Mutation input tests** ([`tests/mutations/test_inputs.py`][test-mutations]):
  replace the staged `NotImplementedError` tests with positive `Upload`
  annotation tests for create and partial inputs; requiredness follows `default`
  / `blank` / `null`; `Meta.fields` / `Meta.exclude` narrowing includes/excludes
  file/image fields; the custom-input merge honors an overridden upload field by
  generated field name (lifted CR-6).
- **Mutation resolver tests**
  ([`tests/mutations/test_resolvers.py`][test-mutations]): a provided `Upload`
  is assigned on create **through the existing generic scalar path** (verifying
  no dedicated file branch is needed — or pinning one if a gap is found); an
  `UNSET` leaves the file unchanged on partial update; an explicit `null` on a
  `null=False` file column returns a field-keyed `FieldError`
  (`_explicit_null_error`), not a silent clear; the
  previously-`NotImplementedError` path now succeeds.
- **Scalar config tests** ([`tests/test_scalars.py`][test-scalars]):
  `strawberry_config()` includes `BigInt` (`Upload` is **not** a package
  `scalar_map` key); an `Upload`-annotated field resolves through both a
  `strawberry_config()` schema and a plain `StrawberryConfig` schema; the
  existing `BigInt` `extra_scalar_map` collision `ValueError` is unchanged; every
  call returns a fresh scalar-map dict.
- **Public export / version tests**
  ([`tests/base/test_init.py`][test-base-init]): `__all__` includes
  `DjangoFileType` / `DjangoImageType` / `Upload`; `test_version` moves to
  `0.0.11`
  ([Decision 10](#decision-10--this-card-owns-the-final-0011-version-bump)).
- **Live HTTP tests.** None required unless implementation adds or discovers a
  genuine fakeshop file/image field; do not add a fake upload domain solely for
  coverage.
- **Cross-cutting — no regression.** The full suite is green at the 100%
  coverage gate (`fail_under = 100`); `ruff format` + `ruff check` are clean; no
  other converter row changes and no read-side regression for non-file scalars.

## Doc updates

Each slice owns its doc edits. [`AGENTS.md`][agents] #"Do not update
CHANGELOG.md unless explicitly instructed" requires `CHANGELOG.md` edits to be
explicitly instructed — and a standing design doc cannot itself grant that
permission. This spec only *describes* the release-note work; the **Slice 4
maintainer prompt must explicitly include the `CHANGELOG.md` edit** for it to be
authorized.

- **Slice 4 — version cut**
  ([Decision 10](#decision-10--this-card-owns-the-final-0011-version-bump)):
  align [`pyproject.toml`][pyproject], `__version__` in [`__init__.py`][init],
  [`tests/base/test_init.py::test_version`][test-base-init], the
  [`docs/GLOSSARY.md`][glossary] package-version line, and `uv.lock` (if
  applicable) on `0.0.11`.
- **Slice 4 — GLOSSARY** ([`docs/GLOSSARY.md`][glossary]): promote
  [`Upload` scalar][glossary-upload-scalar] /
  [`DjangoFileType`][glossary-djangofiletype] /
  [`DjangoImageType`][glossary-djangoimagetype] to `shipped (0.0.11)` (updating
  each body to the shipped contract — the output fields, the `Upload`
  re-export, the empty-file → null resolution, the nullable-subfield
  rationale); document the new `FIELD_OUTPUT_TYPE_MAP` (read-output map) and
  update the `FileField` / `ImageField` line in
  [Scalar field conversion][glossary-scalar-field-conversion] to make the split
  explicit — **read** output is now `DjangoFileType` / `DjangoImageType` (via
  `FIELD_OUTPUT_TYPE_MAP`), the **filter / scalar-input** value stays `str` in
  `SCALAR_MAP`, and the **mutation input** is `Upload`; **add** a file/image row
  to [Specialized scalar conversions][glossary-specialized-scalar-conversions]
  (which has none today), recording the read-side **breaking wire-format
  change** alongside the
  [`PositiveBigIntegerField → BigInt`][glossary-specialized-scalar-conversions]
  precedent; add the three symbols to **Public exports** and update the
  **Index** + **File / image uploads** browse-by-category row; remove the
  [`strawberry_config`][glossary-strawberry-config] entry's stray "next:
  `Upload`" mention (leaving only `BigInt`).
- **Slice 4 — package docs**: [`docs/README.md`][docs-readme] /
  [`README.md`][readme] move the `Upload` scalar + generated file/image field
  typing from "Coming next (`0.0.11`)" to "Shipped today" — wording the **scalar
  and generated file/image mutation-field typing**, not full multipart HTTP
  test-client ergonomics (those await the `0.0.14` [`TestClient`][glossary-testclient]) — and
  move the README **Status** line from `0.0.10` to `0.0.11`; [`GOAL.md`][goal] —
  criterion 6's `Upload` / `FileField` / `ImageField` part ships for generated
  `DjangoMutation` inputs, while the `ModelForm` / `ModelSerializer` flavors in
  that same criterion still land later; [`TODAY.md`][today] rewrites the
  scalar-conversion table's `FileField` / `ImageField` → `str` row to the
  structured output objects and notes upload mutation inputs as a package
  capability not exercised by products; [`docs/TREE.md`][tree] updates the
  `scalars.py` / `types/converters.py` / `types/resolvers.py` (and the matching
  test) summary lines for the shipped Upload re-export /
  `DjangoFileType` / `DjangoImageType` / `FIELD_OUTPUT_TYPE_MAP` /
  file-column resolvers, **discharging the pre-placed `TODO(spec-037 Slice 4)`
  source-site anchor there** ([`AGENTS.md`][agents] folds shipped behavior into
  `docs/TREE.md` and removes the staged anchor in the slice that ships it);
  [`CHANGELOG.md`][changelog] carries the
  `[Unreleased]` → `0.0.11` bullets **only when the Slice 4 maintainer prompt
  explicitly requests it**.
- **Slice 4 — card wrap**: [`KANBAN.md`][kanban] moves
  [`TODO-ALPHA-037-0.0.11`][kanban] to Done with the next `DONE-NNN-0.0.11` id,
  keeping its `SpecDoc` pointing at the canonical card spec (a `SpecDoc` DB edit
  re-rendered via `scripts/build_kanban_md.py`, never a hand-edit).

## Risks and open questions

Each item names a preferred answer for the `0.0.11` cut and a fallback if
implementation reveals it is wrong.

- **Clearing an existing file via mutation input.** Preferred answer
  ([Decision 6](#decision-6--write-side-input-mapping-the-mutation-seam-becomes-upload)):
  omitted upload leaves unchanged; provided upload replaces; an explicit `null`
  on a `null=False` file column is already a field-keyed `FieldError`
  (`_explicit_null_error`), so it can never be an accidental clear; clearing is
  not promised unless a `null=True` field plus `null` assignment already works
  through the shipped mutation pipeline. Fallback: add an explicit clear-file
  sentinel in a future form/serializer flavor if real users need it — do not
  overload empty upload values in this card.
- **Output subfield nullability vs upstream parity.** Preferred answer
  ([Decision 4](#decision-4--read-side-resolution-empty-file-as-null-and-storage-safe-subfield-nullability)):
  `path` / `size` / `url` / `width` / `height` nullable (storage-safe), `name`
  non-null — a deliberate, documented divergence from upstream's all-non-null
  `path: str`. Fallback: if nullable subfields prove awkward in
  Strawberry/Django, keep `path` nullable at minimum and document
  local-storage-only behavior for the others, but never let an empty/unreadable
  file descriptor raise.
- **Where to define `DjangoFileType` / `DjangoImageType`.** Preferred answer
  ([Decision 3](#decision-3--read-side-output-types-djangofiletype--djangoimagetype-mirroring-upstream)):
  define them in [`types/converters.py`][types-converters], where the
  field-class mapping lives, and root-export them. Fallback: a tiny
  `types/files.py` module if importing them from `converters.py` creates a cycle
  — do not create a broad `fields/` package that collides conceptually with the
  planned `FieldSet`.
- **Image dimension dependency + test strategy.** Production `width` / `height`
  stay nullable and resolve from Django's image-file object
  (`ImageFieldFile.width` / `.height`) through the same `_safe_file_attr` guard.
  The card must pick a *test* strategy up front, because Django's **model**
  `ImageField` and its dimension accessors require Pillow, and the project does
  **not** currently declare Pillow in runtime or dev dependencies. **Preferred
  answer: add Pillow as a dev/test-only dependency** — it joins `pytest-django`
  in the dev extras (the package itself never imports it, so no runtime surface
  changes) — and exercise `width` / `height` against a tiny valid in-memory image
  (a few-byte PNG) over the synthetic-model `tmp_path` storage. Fallback: if
  adding Pillow is undesirable, keep the production fields nullable and unit-test
  the resolver logic with a lightweight stand-in object exposing `width` /
  `height`, marking real image parsing out of scope. Either way, do **not**
  `pytest.skip` the dimension tests when Pillow is absent: under
  `fail_under = 100` a conditional skip would let the gate pass over uncovered
  dimension branches. Pillow (preferred) or the stand-in (fallback) makes the
  coverage unconditional.
- **File-column filtering contract.** Preferred answer
  ([Decision 3](#decision-3--read-side-output-types-djangofiletype--djangoimagetype-mirroring-upstream)):
  file columns keep their scalar `str` filter mapping in `SCALAR_MAP` (no
  regression) — i.e. filtering the stored **name / path string**, not file
  metadata (`url` / `size` / `width` / `height`) — and the read-output objects
  live in a separate `FIELD_OUTPUT_TYPE_MAP`, so no output type leaks into a
  [`FilterSet`][glossary-filterset] input. Fallback: if string-filtering a file
  column proves meaningless, reject file/image filters with a
  [`ConfigurationError`][glossary-configurationerror] once a deliberate
  file-filter contract is designed — a follow-up, not this card.
- **Path-safety exception policy.** Preferred answer
  ([Decision 4](#decision-4--read-side-resolution-empty-file-as-null-and-storage-safe-subfield-nullability)):
  `SuspiciousFileOperation` is **not** folded into the `_safe_file_attr`
  degrade-to-`null` catch; it propagates as a top-level error so a
  path-traversal / hostile-name condition stays visible. Fallback: if operators
  prefer graceful degradation, add it to the catch set — but the default is
  visibility.
- **Storage-metadata read cost.** Preferred answer
  ([Decision 4](#decision-4--read-side-resolution-empty-file-as-null-and-storage-safe-subfield-nullability)):
  selecting `size` / `url` / `width` / `height` asks Django storage for metadata
  per selected object and subfield; the framework guards storage-shaped failures
  but does **not** cache or batch storage calls in this card, and the optimizer
  cannot prefetch object-store metadata. Fallback: a batching / caching layer (or
  a storage-metadata dataloader) is a follow-up if profiling shows it matters —
  not this card.
- **Card conflict — stale `"Pairs with 028"` note.** The card's "Other" section
  says "Pairs with 028", but `028` is the
  [ordering subsystem][glossary-orderset] (`DONE-028-0.0.8`), unrelated to
  uploads. Preferred reading: the genuine pairing is with the mutations card
  [`DONE-036-0.0.11`][kanban] (whose input seam this card fills) — the `028`
  reference is a stale copy-paste. Recorded per the [`docs/SPECS/NEXT.md`][next]
  "prefer the card, surface the conflict" rule.
- **Card conflict — stale `mutations/ (planned)` predicted file.** The card's
  "Predicted files" annotates
  `django_strawberry_framework/mutations/ (planned)`, but `mutations/` shipped
  with [`DONE-036-0.0.11`][kanban]. Preferred reading: the directory exists;
  this card edits [`mutations/inputs.py`][mutations-inputs] /
  [`mutations/resolvers.py`][mutations-resolvers] in place.
- **Card conflict — stale `TODO-ALPHA-035-0.0.11` in the `scalars.py`
  docstring.** [`scalars.py`][scalars] #"Future scalars (e.g. ``Upload`` per
  TODO-ALPHA-035-0.0.11) land here." names `035`, but `035` is the
  optimizer-hardening card; the real `Upload` owner is this card, `037`.
  Preferred reading: a stale number — Slice 2 corrects the docstring to
  `TODO-ALPHA-037-0.0.11`. (The [`mutations/inputs.py`][mutations-inputs] seam
  already names `037` correctly.)

## Out of scope (explicitly tracked elsewhere)

- **Multipart request helper** — [`TestClient`][glossary-testclient]
  (`TODO-ALPHA-043-0.0.14`); depends on this scalar existing but is not
  implemented here.
- **Form-based mutations** ([`DjangoFormMutation`][glossary-djangoformmutation])
  — `0.0.12` (`TODO-ALPHA-038-0.0.12`); reuses `Upload` through the same
  scalar-map helper where form fields need it.
- **DRF serializer mutations + auth mutations**
  ([`SerializerMutation`][glossary-serializermutation]) — `0.0.13`; serializer
  upload handling builds on this scalar.
- **A live fakeshop file-upload surface** — deferred to fakeshop activation
  ([`TODO-BETA-051-0.1.5`][kanban]); this card covers both directions with
  synthetic-model tests
  ([Decision 9](#decision-9--test-placement-package-tests-own-synthetic-fileimage-models)).
- **Field-level read gates** — `FieldSet` / per-field permission hooks in
  `0.1.1`; file-metadata permissions are not special-cased here.
- **Remote-storage adapters, thumbnailing, image validation, and signed-URL
  policies** — consumer/storage concerns beyond a model-field conversion card.

## Definition of done

The completion contract the card is built against. Items map onto the card's own
DoD bullets: item 1 (read converter), 2 (write input mapping), 3
(synthetic-model tests), 4 (glossary) — plus the spec / exports / version-cut
the [`docs/SPECS/NEXT.md`][next] flow adds.

**Spec + companion CSV**

1. `docs/spec-037-upload_file_image_mapping-0_0_11.md` (the canonical card spec)
   and its companion `spec-037-upload_file_image_mapping-0_0_11-terms.csv`
   exist;
   `uv run python scripts/check_spec_glossary.py --spec docs/spec-037-upload_file_image_mapping-0_0_11.md`
   reports `OK: <N> terms`.

**Slice 1 — read output objects**

2. [`types/converters.py`][types-converters] defines `DjangoFileType` (`name`
   non-null; `path` / `size` / `url` nullable, **resolver-backed**) and
   `DjangoImageType(DjangoFileType)` (+ nullable `width` / `height`) and adds a
   new `FIELD_OUTPUT_TYPE_MAP` (`FileField` → `DjangoFileType`, `ImageField` →
   `DjangoImageType`) consulted by a new read-only `convert_field_output` wrapper
   (called from [`types/base.py`][types-base] `_build_annotations`; `convert_scalar`
   / `scalar_for_field` stay scalar-only), **leaving** the shared
   [`SCALAR_MAP`][types-converters] file rows as `str` so filter inputs are
   unaffected
   ([Decision 3](#decision-3--read-side-output-types-djangofiletype--djangoimagetype-mirroring-upstream));
   a file column resolves to `DjangoFileType | None` on `blank` / `null`, the
   parent resolver returns `None` for an empty `FieldFile`, and each subfield's
   own `_safe_file_attr` guard degrades storage failures to `null`
   ([Decision 4](#decision-4--read-side-resolution-empty-file-as-null-and-storage-safe-subfield-nullability));
   the file-resolver attachment — wired in [`types/finalizer.py`][types-finalizer]'s
   relation-resolver loop — is passed `consumer_authored_fields` (broader than the
   relation pass's `consumer_assigned_relation_fields`) so a consumer
   `attachment: str` override still wins (no resolver, no object type), and a
   package test pins that a `FilterSet` over a `FileField` yields a scalar filter
   input, not `DjangoFileType`.

**Slice 2 — write `Upload` input**

3. [`scalars.py`][scalars] re-exports `Upload` (no `_PACKAGE_SCALAR_MAP` entry —
   `Upload` already resolves via Strawberry's built-in `DEFAULT_SCALAR_REGISTRY`)
   ([Decision 5](#decision-5--re-export-upload-rather-than-register-it));
   [`mutations/inputs.py`][mutations-inputs] maps `FileField` / `ImageField` to
   `Upload` (required per the shipped per-field rule, `| None` on `blank` /
   `null`), the `NotImplementedError` seam and its tests are removed, and file
   columns participate in the
   [`Meta.input_class`][glossary-input-type-generation] merge override (CR-6
   exception lifted); the existing generic scalar-assignment path in
   [`mutations/resolvers.py`][mutations-resolvers] is verified to assign the
   uploaded file before `full_clean()` / `save()` (a dedicated file branch is
   added only if a test proves the generic path fails)
   ([Decision 6](#decision-6--write-side-input-mapping-the-mutation-seam-becomes-upload)).

**Slice 3 — public exports + coverage**

4. [`__init__.py`][init] re-exports `Upload` / `DjangoFileType` /
   `DjangoImageType` and adds all three to `__all__`
   ([Decision 7](#decision-7--public-surface-three-net-new-root-exported-symbols));
   [`tests/base/test_init.py`][test-base-init] pins them; synthetic-model tests
   cover the read converter / resolver (incl. storage-failure → null subfield),
   the `Upload` re-export and resolution, and the write mapping
   ([Decision 9](#decision-9--test-placement-package-tests-own-synthetic-fileimage-models)).

**Cross-cutting — no regression**

5. The full suite is green at the 100% coverage gate (`fail_under = 100`);
   `ruff format` + `ruff check` are clean; no other converter row changes and no
   read-side regression for non-file scalars.

**Slice 4 — docs + the `0.0.11` cut + card wrap**

6. [`docs/GLOSSARY.md`][glossary] promotes
   [`Upload` scalar][glossary-upload-scalar] /
   [`DjangoFileType`][glossary-djangofiletype] /
   [`DjangoImageType`][glossary-djangoimagetype] to `shipped (0.0.11)`, rewrites
   the [Scalar field conversion][glossary-scalar-field-conversion] file/image
   row and adds a file/image row to
   [Specialized scalar conversions][glossary-specialized-scalar-conversions],
   adds the three to Public exports, records the read-side
   breaking-wire-format change, and moves the package-version line to `0.0.11`;
   [`docs/README.md`][docs-readme] / [`README.md`][readme] move the `Upload`
   scalar **and generated file/image mutation-field typing** (not full multipart
   HTTP test-client ergonomics, which await the `0.0.14` [`TestClient`][glossary-testclient]) to
   "Shipped today" and the Status to `0.0.11`; [`GOAL.md`][goal] /
   [`TODAY.md`][today] reflect that scalar + generated-typing capability and the
   rewritten scalar table; [`CHANGELOG.md`][changelog] carries the bullets **only when the
   Slice 4 maintainer prompt explicitly requests the edit**;
   [`KANBAN.md`][kanban] records the card `DONE-NNN-0.0.11` with the `SpecDoc`
   reference at the canonical card spec (kanban DB + re-render).
7. **The `0.0.11` version bump lands in this card**
   ([Decision 10](#decision-10--this-card-owns-the-final-0011-version-bump)):
   [`pyproject.toml`][pyproject], `__version__` in [`__init__.py`][init],
   [`tests/base/test_init.py::test_version`][test-base-init], the
   [`docs/GLOSSARY.md`][glossary] package-version line, and `uv.lock` (if
   applicable) align on `0.0.11`. The three net-new public symbols (`Upload`,
   `DjangoFileType`, `DjangoImageType`) are added to `__all__` and the export
   pin updated accordingly.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../AGENTS.md
[changelog]: ../CHANGELOG.md
[contributing]: ../CONTRIBUTING.md
[goal]: ../GOAL.md
[kanban]: ../KANBAN.md
[pyproject]: ../pyproject.toml
[readme]: ../README.md
[start]: ../START.md
[today]: ../TODAY.md

<!-- docs/ -->
[docs-readme]: README.md
[glossary]: GLOSSARY.md
[glossary-auto-typed-annotations]: GLOSSARY.md#auto-typed-annotations
[glossary-bigint-scalar]: GLOSSARY.md#bigint-scalar
[glossary-configurationerror]: GLOSSARY.md#configurationerror
[glossary-djangofiletype]: GLOSSARY.md#djangofiletype
[glossary-djangoformmutation]: GLOSSARY.md#djangoformmutation
[glossary-djangoimagetype]: GLOSSARY.md#djangoimagetype
[glossary-djangomutation]: GLOSSARY.md#djangomutation
[glossary-djangomutationfield]: GLOSSARY.md#djangomutationfield
[glossary-djangooptimizerextension]: GLOSSARY.md#djangooptimizerextension
[glossary-djangotype]: GLOSSARY.md#djangotype
[glossary-fielderror-envelope]: GLOSSARY.md#fielderror-envelope
[glossary-filterset]: GLOSSARY.md#filterset
[glossary-input-type-generation]: GLOSSARY.md#input-type-generation
[glossary-metaexclude]: GLOSSARY.md#metaexclude
[glossary-metafields]: GLOSSARY.md#metafields
[glossary-metamodel]: GLOSSARY.md#metamodel
[glossary-metanullable-overrides]: GLOSSARY.md#metanullable_overrides
[glossary-metarequired-overrides]: GLOSSARY.md#metarequired_overrides
[glossary-orderset]: GLOSSARY.md#orderset
[glossary-relation-handling]: GLOSSARY.md#relation-handling
[glossary-scalar-field-conversion]: GLOSSARY.md#scalar-field-conversion
[glossary-scalar-field-override-semantics]: GLOSSARY.md#scalar-field-override-semantics
[glossary-serializermutation]: GLOSSARY.md#serializermutation
[glossary-specialized-scalar-conversions]: GLOSSARY.md#specialized-scalar-conversions
[glossary-strawberry-config]: GLOSSARY.md#strawberry_config
[glossary-testclient]: GLOSSARY.md#testclient
[glossary-upload-scalar]: GLOSSARY.md#upload-scalar
[tree]: TREE.md

<!-- docs/SPECS/ -->
[next]: SPECS/NEXT.md
[spec-001]: SPECS/spec-001-django_types-0_0_1.md
[spec-017]: SPECS/spec-017-deferred_scalars-0_0_6.md
[spec-025]: SPECS/spec-025-scalar_map_helper-0_0_7.md
[spec-026]: SPECS/spec-026-scalar_conversion_fakeshop-0_0_7.md
[spec-036]: SPECS/spec-036-mutations-0_0_11.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[filters-inputs]: ../django_strawberry_framework/filters/inputs.py
[init]: ../django_strawberry_framework/__init__.py
[mutations-inputs]: ../django_strawberry_framework/mutations/inputs.py
[mutations-resolvers]: ../django_strawberry_framework/mutations/resolvers.py
[scalars]: ../django_strawberry_framework/scalars.py
[conf]: ../django_strawberry_framework/conf.py
[types-base]: ../django_strawberry_framework/types/base.py
[types-converters]: ../django_strawberry_framework/types/converters.py
[types-finalizer]: ../django_strawberry_framework/types/finalizer.py
[types-relay]: ../django_strawberry_framework/types/relay.py
[types-resolvers]: ../django_strawberry_framework/types/resolvers.py

<!-- tests/ -->
[test-base-init]: ../tests/base/test_init.py
[test-mutations]: ../tests/mutations/
[test-scalars]: ../tests/test_scalars.py
[test-types]: ../tests/types/

<!-- examples/ -->
[test-query-readme]: ../examples/fakeshop/test_query/README.md

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
[upstream-field-types]: https://github.com/strawberry-graphql/strawberry-django/blob/main/strawberry_django/fields/types.py