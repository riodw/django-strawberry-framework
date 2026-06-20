# Distilled Dicta: django_strawberry_framework
Use these prompts to explore one file at a time. They are priorities for investigation, not pass/fail rules; escalate only defects confirmed against the original source. This dicta is distilled from the `0.0.11` **upload file/image mapping** build cycle (card 037; Slices 1-4 + integration + final gate) and reflects the concrete pitfalls those cycles actually hit: the read/write/filter triple-path split, the single subfield storage guard, write-input parallelism, export-surface pins, the DB-backed generated-doc discipline, and the version cut.

The cardinal invariant behind almost every question below: **read side = structured `DjangoFileType`/`DjangoImageType` output object (via `FIELD_OUTPUT_TYPE_MAP` + `convert_field_output`); filter-input side = `str` (via the untouched `SCALAR_MAP`/`scalar_for_field` path); mutation-input side = the `Upload` scalar.** These are three paths that must never re-merge, and neither representation may leak into another's path. Probe for any crack in that wall first.

## Probing Questions for Code Exploration
The hunter should ask these questions while reading each file, focusing on exploration and hidden defects rather than simple checklist confirmation.

### 1. The Read/Write/Filter Triple-Path Split (the standing P0)
- **Does any path re-merge the three representations?** In `mutations/inputs.py`, does the import block still pull *only* `Upload` (from `..scalars`) plus the scalar-only `convert_scalar`/`scalar_for_field` — and NOT `convert_field_output`, `FIELD_OUTPUT_TYPE_MAP`, `DjangoFileType`, or `DjangoImageType`? Any of those four reaching the input path means read-output objects have leaked into the write path.
- **Has the write scalar drifted into the read map?** Does `Upload` appear anywhere in `types/converters.py` (it must not), and is it kept out of `FIELD_OUTPUT_TYPE_MAP` and out of `_PACKAGE_SCALAR_MAP` (still byte-unchanged `{BigInt: _BIGINT_SCALAR_DEFINITION}`)? `Upload` rides Strawberry's `DEFAULT_SCALAR_REGISTRY`, not the package scalar map.
- **Do file columns still yield `str` on the filter-input path?** Are `SCALAR_MAP[models.FileField]`/`[models.ImageField]` still `str`, byte-unchanged? Does `filters/inputs.py::_scalar_from_model_field` still walk *only* `scalar_for_field`/`SCALAR_MAP` and never `convert_field_output`/`FIELD_OUTPUT_TYPE_MAP`? A FilterSet over a file column must yield a `str` input, never an output object.
- **Is the MRO walk a single shared helper, not folded or copied?** Is `_field_output_type_for` the one walk in `converters.py`, imported top-level by `resolvers.py`? Folding it back into `convert_scalar`/`scalar_for_field` re-collapses the split; copying it into `resolvers.py` creates a parallel walk that can drift in ordering.
- **Is `ImageField` listed before `FileField` in `FIELD_OUTPUT_TYPE_MAP`?** `ImageField` subclasses `FileField`, so the MRO walk must hit `ImageField → DjangoImageType` first or an `ImageField` (and any consumer subclass) silently falls through to `DjangoFileType` (same hazard class as `PositiveBigIntegerField → BigInt` ordering).

### 2. The Single Subfield Storage Guard
- **Is `_safe_file_attr` still the only subfield guard, with the narrow catch?** Is it the *only* `try/except` for subfield reads, with the catch list still exactly `(ValueError, OSError, NotImplementedError)` — no broader (no bare `Exception`, no `SuspiciousOperation`)? A widened catch swallows genuine bugs. Has a second copy of the guard crept in?
- **Does `SuspiciousFileOperation` still propagate rather than degrade to `None`?** It's a `SuspiciousOperation`, deliberately *outside* the catch set (a security signal). Is the test pinning this still present and is the catch still excluding it?
- **Does the parent file resolver carry no `try/except`?** `resolvers.py::_make_file_resolver` must do object-level nullability only (empty file → whole object `None`); the per-property catch lives solely in `_safe_file_attr`. Has degrade-to-null logic migrated up into the parent and duplicated the responsibility?
- **Is the subfield contract intact?** Is `name` still the only non-null subfield while `path`/`size`/`url`/`width`/`height` are nullable? Has someone "fixed" the nullable subfields toward upstream parity and silently changed the contract? Does `DjangoImageType(DjangoFileType)` *inherit* the four base subfields rather than re-declaring them, with no literal `("name","path","size","url")` tuple appearing anywhere to keep in sync?

### 3. Read-Side Nullability and Write-Side Requiredness Composition
- **Does the read side widen on `null` OR `blank`?** Does `convert_field_output` widen a file column to `<object> | None` on `field.null` *or* `field.blank` (an absent file on a blank column must be representable), and does the `force_nullable` tri-state (`nullable_overrides`→True / `required_overrides`→False / else None) still win over `null`/`blank`?
- **Was the `convert_scalar`→`convert_field_output` swap nullability-preserving?** In `types/base.py::_build_annotations`, is the read-side `force_nullable` tri-state threaded through *unchanged* (same keyword shape as the old `convert_scalar` call), or did the swap introduce a divergent nullability path?
- **Is the write-input requiredness from the shared machinery only?** Does the `Upload` input field's requiredness come solely from the shared `input_field_required` (required only when `is_create and not is_m2m and input_field_required(field)`), `Upload | None` with `default=UNSET` otherwise and in every partial input — with no file-specific requiredness/widening/override-skip predicate duplicated for the file branch?
- **Is the write-side python attr the plain field name?** Is it `attachment`, never `attachment_id`? File columns are scalar inputs, not relations.

### 4. Write-Path Parallelism (no second machinery, no resolver branch)
- **Is the file-input branch a peer `elif` that falls through to shared machinery?** Does `inputs.py`'s `elif isinstance(field, (FileField, ImageField))` produce only the `(field.name, camel_name, Upload)` triple and then fall through to the shared override-skip / requiredness / `| None`-widening path? Watch for a re-introduced early `raise` or reordering that re-creates the spec-036 CR-6 carve-out the build removed by ordering alone.
- **Does the write resolver carry zero file-specific code?** Slice 2 was verify-first: the generic `model(**scalar_and_fk_attrs)` / `setattr` path in `mutations/resolvers.py` carries the `UploadedFile` with no dedicated file branch (only TODO comments were removed; production code byte-unchanged). Has a later "helpful" file branch been added — a divergent write path the spec rejects?
- **Are partial-update and explicit-null semantics intact?** Does an omitted file field (`UNSET`) still get stripped in `_decode_relations` so it never reaches `setattr` (stored file untouched on partial update)? Does explicit `null` on a `null=False` file column still route through `_explicit_null_error` to a field-keyed `FieldError` (clearing semantics are a Risks item, *not* promised)?

### 5. Resolver Attachment and the Consumer-Override Skip
- **Does `_attach_file_resolvers` run in the same Phase-2 window, before the freeze?** Is it called inside the same loop as `_attach_relation_resolvers` in `finalizer.py`, before `strawberry.type(...)` freezes the class?
- **Is the skip set the broader `consumer_authored_fields`?** The file pass deliberately skips both annotation *and* assigned overrides (broader than the relation pass's `consumer_assigned_relation_fields`) — a consumer `attachment: str` annotation-only override must get neither a generated resolver nor an object type. Does `_attach_file_resolvers` also skip relations (`field.is_relation`) and non-file columns (`_field_output_type_for(field) is None`)?
- **Is the override test non-vacuous, and does it inspect the right thing?** Is there a control case proving a *non-overridden* file column DOES get a generated `resolve_<field>`? Because `strawberry.type(...)` unwraps an assigned `StrawberryField` to the bare function and an annotation-only override leaves no `__dict__` entry, does the test assert on the surviving `__dict__` function name (`resolve_<f>` = generated vs the consumer's name) rather than `isinstance(StrawberryField)`?

### 6. Export Surface and Re-export Identity
- **Is `__all__` exactly the pre-build set plus the three authorized symbols?** Is `__init__.py` `__all__` the pre-build 20 + `DjangoFileType`, `DjangoImageType`, `Upload` (23 total), in true `sorted()` ASCII order (`Upload` falls between `SyncMisuseError` and `__version__`; capital `U` sorts before `_`)? Is `UploadDefinition` still *module-only* on `scalars.__all__` and NOT root-exported?
- **Is `Upload` a pure re-export from the one canonical site?** Is `Upload is strawberry.file_uploads.scalars.Upload` (a re-export from `.scalars`, not a wrapper `NewType`, not a second direct import in `inputs.py`)? Are `DjangoFileType`/`DjangoImageType` imported via a dedicated `from .types.converters import …` line, not by adding an unauthorized re-export to `types/__init__.py` just to shorten the import?
- **Are the pin tests exact and identity-based?** In `tests/base/test_init.py`, is `test_public_api_surface_is_pinned` an exact-tuple equality (drop-one fails, not loose membership), and do the export tests assert genuine `is`-identity (`Upload is ScalarsUpload`, `DjangoFileType is converters.DjangoFileType`) so the wiring can't drift to a parallel definition? (Re-export-identity test aliases must stay PascalCase — `ScalarsUpload` — or ruff N813 trips.)

### 7. Version Cut and Quintet Consistency
- **Do all five quintet sites carry the identical bare literal `0.0.11`?** Sites: `pyproject.toml` `[project].version`, `__init__.py` `__version__`, `tests/base/test_init.py::test_version`, the `docs/GLOSSARY.md` package-version line, and the `django-strawberry-framework` entry in `uv.lock`. No divergent form (`v0.0.11`, `0.0.11.dev`); `pyproject` `version` must equal `__init__` `__version__`.
- **Have all staged `TODO(spec-037 Slice 4)` anchors been discharged?** Does `grep -rn "TODO(spec-037" .` over the *whole tree* return nothing? This cycle missed exactly one anchor in `docs/TREE.md` (a flat hand-edited doc omitted from the spec's `## Doc updates` list) and it blocked `final-accepted` — anchors hide in docs the obvious quintet/GLOSSARY list omits.
- **Is the Pillow dev-dependency undisturbed?** Is `pyproject.toml` `"pillow>=10.0.0"` and the `uv.lock` Pillow block intact? A `uv add --dev`/`uv lock` regenerate strips nearby lock-file comments as a side effect — was a stripped TODO anchor restored by hand?

### 8. DB-Backed Generated Docs (DB is source of truth)
- **Do the generated docs regenerate byte-clean — twice?** Are `KANBAN.md`, `KANBAN.html`, and `docs/GLOSSARY.md` byte-identical to a fresh regenerate, and is a *second* consecutive regenerate md5-stable? (A single `git diff` shows only the cumulative HEAD diff, never second-regenerate stability.) A non-empty second-regenerate diff means a hand-edit was never synced to the DB.
- **Were GLOSSARY *body* edits made to the DB row, not the rendered file?** The DB-backed bodies extend beyond the obvious `upload-scalar`/`djangofiletype`/`djangoimagetype` trio to `scalar-field-conversion`, `specialized-scalar-conversions`, and `strawberry_config` (and the version line / status / Index / Public-exports list). A hand-edit to any DB-backed section is silently reverted on regenerate. Was any edit made with raw SQL (skipping the `post_save` `UUIDModel` side-row the GraphQL render needs)?
- **Which docs are flat hand-edited vs generated?** README, docs/README, GOAL, TODAY, CHANGELOG, and `docs/TREE.md` are flat hand-edited; the regenerate gate will NOT catch an undischarged anchor or stale phrasing there.

### 9. Card-Close Invariants and Terms-CSV
- **Do the card-close checks pass?** Does `import_spec_terms --check` report OK for all done cards, and `check_spec_glossary.py --spec …` report `OK: 20 terms`? Does `manage.py check` pass and `makemigrations --check --dry-run` report no model drift (DB *data* edits must not imply schema drift)?
- **Does every terms-CSV anchor resolve, with no duplicate anchor?** Does every anchor in the 037 `-terms.csv` resolve to an existing `GlossaryTerm` row? A *duplicate* anchor is a card-close blocker (`check_spec_glossary` tolerates dual rows but `import_spec_terms::_load_rows` raises `CommandError`).
- **Does card 37 satisfy the done-save signal invariant?** Status `done` requires *both* ≥1 `CardGlossaryTerm` link AND a linked `SpecDoc`. Is the `037` SpecDoc.url at the correct on-disk/committed location consistent with its siblings (`035`/`036`)?

### 10. Consumer/Live-Surface and Teaching-Example Drift
- **Is the live fakeshop upload surface wired correctly?** A post-ship review added a *live* surface: `MediaSpecimen` model + `MediaSpecimenType` + `createMediaSpecimen` in the `scalars` app, with live `/graphql/` read + real-multipart-upload tests in `examples/fakeshop/test_query/test_uploads_api.py`. Does `GraphQLView` still set `multipart_uploads_enabled=True`? Without it, real multipart uploads silently fail.
- **Is the three-way split stated once canonically and merely referenced elsewhere?** Is the read=object / filter=`str` / mutation=`Upload` split spelled once (GLOSSARY `Scalar field conversion`) and referenced — not re-spelled with drift across the `DjangoFileType`/`DjangoImageType` bodies, the CHANGELOG `### Changed` bullet, `TODAY.md`, and the `Specialized scalar conversions` row?
- **Does any "shipped" wording overstate scope?** Wherever `Upload` moves to "shipped" (README, docs/README, GOAL criterion 6, TODAY), is the caveat present that the scalar + generated mutation-field typing ship while full multipart HTTP ergonomics await the `0.0.14` `TestClient`? Was the stale `strawberry_config` "next: `Upload`" mention removed everywhere (`Upload` never rode through `strawberry_config` — it's a built-in)?
- **Do stale card/spec references get fixed both-or-neither?** The 037 card body's `TODO-ALPHA-034`/"Pairs with 028" were reconciled to `DONE-036`. Probe for *partial* fixes across single-surface `CardItem.text` — a one-surface correction diverging from un-editable copies is worse than uniformly-wrong.

### 11. Test Integrity, Isolation, and Placement
- **Are the storage-fault / corrupt-image arms genuinely exercised — unconditionally?** Do `tests/types/test_resolvers.py` exercise each catch arm of `_safe_file_attr`: `NotImplementedError` (`.path`), `OSError`/`FileNotFoundError` (vanished-file `.size` via real `os.remove` under `tmp_path`), and the dimension-read failure (`width`/`height` on `ContentFile(b"not an image")`)? Are dimension branches covered *unconditionally* (never `pytest.skip` when Pillow is absent — a conditional skip slips uncovered branches past the coverage gate)?
- **Do per-subfield-guard tests select ONE subfield at a time?** A test selecting all of `{ name path size url width height }` at once can let the guard silently migrate up to the parent and still pass. Is the failing subfield asserted `null` while `name` still resolves (per-subfield isolation)?
- **Does the chosen failure mechanism actually raise on the named subfield?** `FileSystemStorage.url`/`.path` are string-builders that never touch disk, so a vanished file degrades only `.size`/`.open`/dimension reads — NOT `.url`. Does any test name/docstring overstate which arm it pins (e.g. claiming a `url` degradation it never asserts)? Regression-guard labels are load-bearing documentation.
- **Are synthetic-model harnesses correct?** No in-repo FileField/ImageField column exists, so resolver coverage builds synthetic models at test time via `schema_editor` — these need `@pytest.mark.django_db(transaction=True)` (SQLite can't `schema_edit` inside a plain-`django_db` atomic block) and uniquified model *names* (`itertools.count`) with a real `app_label`. Query strings must derive from `model.__name__`, not a hardcoded type name.
- **Do file-content reads use the context manager?** A bare `row.attachment.read()` leaks an OS handle; the repo's `-W error` config escalates the `ResourceWarning` to a test failure. Reads must use `with row.attachment.open("rb") as fh:`. (Never weaken `-W error` to fix a leak — see the standing async-sqlite ResourceWarning discipline.)
- **Is throwaway verification kept out of the shipped suite?** Scratch probes belong under `docs/builder/temp-tests/` (or outside the repo), removed before handoff — never committed into the shipped test tree.

## Severity Calibration Priorities
The hunter should prioritize findings by severity, escalating confirmed critical issues immediately and documenting maintainability issues with clear follow-up conditions.

### Priority 1: High (Wire-Format Correctness, Security, & API Stability)
- Any leak across the read/write/filter split: read-output objects (`DjangoFileType`/`DjangoImageType`/`convert_field_output`/`FIELD_OUTPUT_TYPE_MAP`) reaching `mutations/inputs.py` or the filter-input path; `Upload` entering `FIELD_OUTPUT_TYPE_MAP` or `_PACKAGE_SCALAR_MAP`; `SCALAR_MAP` file rows ceasing to be `str`.
- The subfield guard catching too broadly and swallowing a genuine bug, or `SuspiciousFileOperation` silently degraded to `None` (a security signal).
- Wrong output-object nullability or wrong input requiredness (`null`/`blank`/`force_nullable` composition; required-on-create vs optional-on-partial); `attachment` vs `attachment_id` naming on the write input.
- MRO mis-ordering sending `ImageField` to `DjangoFileType` (wrong type on the wire).
- Public-API drift: unauthorized `__all__` growth/shrink (≠ 23, out of `sorted()` order), a broken re-export identity, `UploadDefinition` leaking to the root.
- `__version__`/version-quintet divergence; generated-doc drift (non-byte-clean regenerate, or a regenerate that regresses prior-card content); card-close invariant failures (missing SpecDoc/glossary link, duplicate-anchor CSV, `import_spec_terms --check` failing, raw-SQL edits); an undischarged Slice-named `TODO` anchor; a missing `multipart_uploads_enabled=True` on the live `GraphQLView`.

*Action:* Fix the root cause directly and back it with a robust, permanent pinning test unless the finding itself proves a test is impossible. Prefer the lowest-surface root-cause fix over a non-canonical shim. Note: a `pytest` failure of any kind blocks acceptance regardless of ownership — but a red in a subsystem outside this build's diff is a maintainer-baseline call, not something to "fix" by editing unrelated source (verify ownership with `git diff HEAD -- <files>`).

### Priority 2: Medium (DRY, Query-Shape, & Fragility)
- Duplicated guard/helper logic: a second copy of the empty-file guard, a parallel file-resolver attachment path, a copied/duplicated MRO walk, parallel write-input requiredness/widening machinery, or a repeated `("name","path","size","url")` literal. (The shadow "Repeated string literals" + "Imports" cross-file scan is the cheap decisive check — these names should appear in no file's repeated-literals section, and the boundary imports should not cross.)
- Non-distinguishing / vacuous tests: a per-subfield guard test that selects all subfields at once, an override test with no control case, an exact-pin that has silently weakened to membership.
- `build_mutation_input` complexity creep — a flagged hotspot; a new file branch is acceptable only if it falls through to shared machinery without deepening control flow.
- Cross-doc phrasing drift on the public split (read=object / filter=`str` / mutation=`Upload`), a missing multipart-scope caveat, a lingering "next: Upload" mention.

*Action:* Address during implementation when local to the prompted file, or record the exact sibling/spec dependency that blocks a one-file fix. Treat broken consumer-facing examples on a documented surface as more than cosmetic.

### Priority 3: Low (Locality, Clarity, & Polish)
- A test name/docstring that overstates which arm it pins (e.g. the `url`-degradation label) — load-bearing as regression-guard documentation, so worth a label-only fix, but no production defect and no assertion change.
- Stale/wrong comments or "planned"/old-version wording (`TODO-ALPHA-035` → `037`, "future scalar" / "next: Upload", stale spec filename or card-number refs) left in deliberately-updated docs.
- Per-file test-scaffold duplication where test-locality and isolation outweigh a shared fixture; redundant coverage (re-testing null/blank widening already pinned in Slice 1).

*Action:* Polish inline when safe and scoped, or frame with a clear, verbatim **trigger condition** (e.g. *"hoist the shared synthetic-model harness only if a fourth test file rebuilds it"*) so future passes can find and consolidate it.

## Review-Order Priorities (highest regression risk first)
1. **`types/converters.py`** — the keystone: `FIELD_OUTPUT_TYPE_MAP`, `convert_field_output`, `_field_output_type_for`, `_safe_file_attr`, AND the untouched `SCALAR_MAP`. The split, the guard, and MRO order all live here; any refactor that "tidies" the two parallel maps/walks is the single most likely regression source.
2. **`mutations/inputs.py::build_mutation_input`** — the `elif` file branch must produce only the `(python_attr, graphql_name, Upload)` triple and fall through to shared machinery; a flagged complexity hotspot.
3. **`types/resolvers.py` + `types/finalizer.py`** — attachment timing, the broader `consumer_authored_fields` skip, the object-nullability-only parent resolver.
4. **`types/base.py::_build_annotations`** — the `convert_scalar`→`convert_field_output` swap and the unchanged `force_nullable` tri-state.
5. **`mutations/resolvers.py`** — verify-first: still byte-unchanged, still no file branch.
6. **`scalars.py`** — re-export identity, no `_PACKAGE_SCALAR_MAP` entry, untouched `BigInt` collision test.
7. **`__init__.py` + `tests/base/test_init.py`** — exactly three new root exports, `sorted()` `__all__` (23), exact-tuple + `is`-identity pins, `test_version` == `0.0.11`.
8. **`filters/inputs.py::_scalar_from_model_field`** — the other end of the split; confirm it still delegates to `scalar_for_field` and yields `str` for file columns.
9. **Generated-doc + version surfaces** — the byte-clean (twice) regenerate gate, the version quintet, the whole-tree `TODO(spec-037` sweep, the Pillow dev-dep, the live `MediaSpecimen` surface and its `multipart_uploads_enabled` flag.
10. **`tests/types/test_resolvers.py`** — production logic unchanged this cycle, so the risk here is honest labeling, per-subfield isolation, and non-vacuity, not behavior.

## How to review a single file
Each prompt below targets exactly one source file. Treat it as a focused
review pass, not a tour:

- Read the `.overview.md` shadow first. It is a structural index -
  quick-scan counts, imports, symbols, control-flow hotspots, executable
  Django/ORM marker lines, calls of interest, and repeated executable
  string literals - pulled from the AST without executing the file. Use
  it to plan the read, not as the source of truth.
- Read the `.stripped.py` shadow next. Comments and docstring statements
  are removed, and other string literals are replaced, so the executable
  structure is easier to scan. **Line numbers in the stripped file are
  not canonical.** Cite original source-file line numbers in every
  finding and every fix.
- Open the original source file alongside (named in the prompt) and
  reconcile the shadow view against the real code before declaring a
  defect.
- Confirm every defect against the actual source. No speculation, no
  "this might be wrong". If you cannot reproduce the failure shape
  mentally or with a quick read, drop the finding and move on. Silence
  on a marker line is acceptable; speculative defects pollute the
  checklist.

For each confirmed defect:

- Classify severity using the criteria in the dicta header above.
- Edit the original source file directly. Stay within the file the
  prompt names - if the fix needs sibling changes, surface that as a
  question rather than expanding the diff unilaterally.
- For **High**-severity fixes, add or update a test that pins the
  corrected behavior under the correct test tree per AGENTS.md
  "Test placement is mandatory". Do not rely on validation alone.
- For **Medium** / **Low** fixes that change a documented contract,
  update the relevant docstring or comment in the same pass so the
  prose matches the final behavior.
- Run `uv run ruff format <file>` and `uv run ruff check <file>` on
  any source file you touched.

When the file is done, tick its checkbox `- [x]` so the next prompt is
obvious.

## Per-file prompts

- [x] django_strawberry_framework/_cross_web_patches.py
    - docs/shadow/current/django_strawberry_framework___cross_web_patches.stripped.py
    - docs/shadow/current/django_strawberry_framework___cross_web_patches.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework___cross_web_patches.stripped.py and docs/shadow/current/django_strawberry_framework___cross_web_patches.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/_cross_web_patches.py
    - Result: No issues. Files changed: none; validation: uv run pytest tests/test_cross_web_patches.py -q -> 9 passed (only the isolated-run 100% coverage gate trips, not a test failure); upstream `DjangoHTTPRequestAdapter.body` confirmed still `self.request.body.decode()`, patch premise holds.

- [x] django_strawberry_framework/_django_patches.py
    - docs/shadow/current/django_strawberry_framework___django_patches.stripped.py
    - docs/shadow/current/django_strawberry_framework___django_patches.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework___django_patches.stripped.py and docs/shadow/current/django_strawberry_framework___django_patches.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/_django_patches.py
    - Result: No issues. Files changed: none; validation: uv run pytest tests/test_django_patches.py -q -> 13 passed (isolated-run 100% coverage gate aside); `_remove_databases_failures` patch confirmed a faithful Django 6.0.5 mirror with a correct `_is_database_failure` guard.

- [x] django_strawberry_framework/_strawberry_patches.py
    - docs/shadow/current/django_strawberry_framework___strawberry_patches.stripped.py
    - docs/shadow/current/django_strawberry_framework___strawberry_patches.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework___strawberry_patches.stripped.py and docs/shadow/current/django_strawberry_framework___strawberry_patches.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/_strawberry_patches.py
    - Result: No issues. Files changed: none; validation: uv run ruff check -> All checks passed; `parse_json` UnicodeDecodeError->HTTPException(400) and scalar-rejection paths verified against installed Strawberry upstream.

- [x] django_strawberry_framework/apps.py
    - docs/shadow/current/django_strawberry_framework__apps.stripped.py
    - docs/shadow/current/django_strawberry_framework__apps.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__apps.stripped.py and docs/shadow/current/django_strawberry_framework__apps.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/apps.py
    - Result: No issues. Files changed: none; validation: confirmed all three sibling `apply()` patch modules exist and are called from `ready()`, and the documented `APPLY_UPSTREAM_PATCHES` self-gating contract holds; no code edited.

- [x] django_strawberry_framework/conf.py
    - docs/shadow/current/django_strawberry_framework__conf.stripped.py
    - docs/shadow/current/django_strawberry_framework__conf.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__conf.stripped.py and docs/shadow/current/django_strawberry_framework__conf.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/conf.py
    - Result: No issues. Files changed: none; validation: `_normalize_user_settings` branch order, `__getattr__` recursion guard, and fail-loud `ConfigurationError` propagation (non-`AttributeError`) reconciled against source + exceptions.py; no code edited.

- [x] django_strawberry_framework/connection.py
    - docs/shadow/current/django_strawberry_framework__connection.stripped.py
    - docs/shadow/current/django_strawberry_framework__connection.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__connection.stripped.py and docs/shadow/current/django_strawberry_framework__connection.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/connection.py
    - Result: No issues. Files changed: none; validation: windowed pageInfo/totalCount derivation, ambiguous-empty fallback, await-before-raise, `Meta.ordering` fallback, and sync/async dispatch reconciled against source; no code edited.

- [x] django_strawberry_framework/exceptions.py
    - docs/shadow/current/django_strawberry_framework__exceptions.stripped.py
    - docs/shadow/current/django_strawberry_framework__exceptions.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__exceptions.stripped.py and docs/shadow/current/django_strawberry_framework__exceptions.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/exceptions.py
    - Result: No issues. Files changed: none; validation: `__all__` confirmed in sorted() order and exactly matching the 3 classes; inheritance + docstring raise-site claims reconciled against source; no code edited.

- [x] django_strawberry_framework/filters/base.py
    - docs/shadow/current/django_strawberry_framework__filters__base.stripped.py
    - docs/shadow/current/django_strawberry_framework__filters__base.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__filters__base.stripped.py and docs/shadow/current/django_strawberry_framework__filters__base.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/filters/base.py
    - Result: No issues. Files changed: none; validation: ArrayFilter empty-list guard, `_accepted_globalid_type_names` round-trip vs encode-side strategy mapping, and RelatedFilter None-guard chains reconciled against source; no code edited.

- [x] django_strawberry_framework/filters/factories.py
    - docs/shadow/current/django_strawberry_framework__filters__factories.stripped.py
    - docs/shadow/current/django_strawberry_framework__filters__factories.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__filters__factories.stripped.py and docs/shadow/current/django_strawberry_framework__filters__factories.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/filters/factories.py
    - Result: No issues. Files changed: none; validation: uv run ruff check -> All checks passed, uv run pytest tests/filters/test_factories.py -q -> 22 passed; `_make_hashable`/`_make_cache_key` ordering + key=repr total-ordering defence reconciled.

- [x] django_strawberry_framework/filters/inputs.py
    - docs/shadow/current/django_strawberry_framework__filters__inputs.stripped.py
    - docs/shadow/current/django_strawberry_framework__filters__inputs.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__filters__inputs.stripped.py and docs/shadow/current/django_strawberry_framework__filters__inputs.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/filters/inputs.py
    - Result: No issues. Files changed: none; validation: confirmed `_scalar_from_model_field` delegates only to `scalar_for_field`/`SCALAR_MAP` (FileField/ImageField -> str) and never touches `convert_field_output`/`FIELD_OUTPUT_TYPE_MAP` — filter-input end of the split intact; branch ordering reconciled.

- [x] django_strawberry_framework/filters/sets.py
    - docs/shadow/current/django_strawberry_framework__filters__sets.stripped.py
    - docs/shadow/current/django_strawberry_framework__filters__sets.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__filters__sets.stripped.py and docs/shadow/current/django_strawberry_framework__filters__sets.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/filters/sets.py
    - Result: No issues. Files changed: none; validation: logic-tree depth caps, `_apply_related_constraints` field_name vs declared-name divergence, and own-PK narrowing reconciled; no read-output/Upload import leak (split intact); no code edited.

- [x] django_strawberry_framework/list_field.py
    - docs/shadow/current/django_strawberry_framework__list_field.stripped.py
    - docs/shadow/current/django_strawberry_framework__list_field.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__list_field.stripped.py and docs/shadow/current/django_strawberry_framework__list_field.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/list_field.py
    - Result: No issues. Files changed: none; validation: validation guard ordering, relay-target validator, and intentional async-detection asymmetry (`_default` per-call vs consumer-wrapper per-construction) reconciled; no upload-symbol imports; no code edited.

- [x] django_strawberry_framework/management/commands/_imports.py
    - docs/shadow/current/django_strawberry_framework__management__commands___imports.stripped.py
    - docs/shadow/current/django_strawberry_framework__management__commands___imports.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__management__commands___imports.stripped.py and docs/shadow/current/django_strawberry_framework__management__commands___imports.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/management/commands/_imports.py
    - Result: No issues. Files changed: none; validation: uv run pytest tests/management/test_imports.py -q -> 4 passed. Noted (not a defect): a `:`-prefixed selector yields a raw `ValueError` outside the deliberately-narrow `ImportError`/`AttributeError` catch — pinned as intentional by an existing test; not widened.

- [x] django_strawberry_framework/management/commands/export_schema.py
    - docs/shadow/current/django_strawberry_framework__management__commands__export_schema.stripped.py
    - docs/shadow/current/django_strawberry_framework__management__commands__export_schema.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__management__commands__export_schema.stripped.py and docs/shadow/current/django_strawberry_framework__management__commands__export_schema.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/management/commands/export_schema.py
    - Result: No issues. Files changed: none; validation: three `--path` branches (stdout / empty-string CommandError / UTF-8 write), non-Schema guard, importer-error and OSError->CommandError wrapping reconciled against source; no code edited.

- [x] django_strawberry_framework/management/commands/inspect_django_type.py
    - docs/shadow/current/django_strawberry_framework__management__commands__inspect_django_type.stripped.py
    - docs/shadow/current/django_strawberry_framework__management__commands__inspect_django_type.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__management__commands__inspect_django_type.stripped.py and docs/shadow/current/django_strawberry_framework__management__commands__inspect_django_type.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/management/commands/inspect_django_type.py
    - Result: Fixed Medium. `_scalar_row` mis-labeled a FileField/ImageField column's converter as `SCALAR_MAP[FileField]` when the displayed type is the `DjangoFileType`/`DjangoImageType` output object produced by `convert_field_output` via the shared `_field_output_type_for` walk; now labels `convert_field_output -> <OutputType>`. No wire-format/API change (diagnostic-only). Files changed: django_strawberry_framework/management/commands/inspect_django_type.py; tests/management/test_inspect_django_type.py (new parametrized pin). Validation: uv run ruff format -> unchanged, uv run ruff check -> All checks passed, uv run pytest tests/management/test_inspect_django_type.py -> 13 passed, fakeshop inspect+scalars tests -> 12 passed. SCOPE NOTE (maintainer): test added for a Medium fix exceeds the hunter's "High-only" test authorization — accepted as a correct, green pin. Hunter also observed stale `tests/types/__pycache__/test_inspect_tmp.cpython-*.pyc` with no source (leftover; out of scope).

- [x] django_strawberry_framework/mutations/fields.py
    - docs/shadow/current/django_strawberry_framework__mutations__fields.stripped.py
    - docs/shadow/current/django_strawberry_framework__mutations__fields.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__mutations__fields.stripped.py and docs/shadow/current/django_strawberry_framework__mutations__fields.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/mutations/fields.py
    - Result: No issues. Files changed: none; validation: `_validate_mutation_target`, `_input_type_name` single-sourcing, `_synthesized_mutation_signature` per-operation args, and `DjangoMutationField._resolve` sync/async dispatch reconciled; references no upload-build symbols; no code edited.

- [x] django_strawberry_framework/mutations/inputs.py
    - docs/shadow/current/django_strawberry_framework__mutations__inputs.stripped.py
    - docs/shadow/current/django_strawberry_framework__mutations__inputs.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__mutations__inputs.stripped.py and docs/shadow/current/django_strawberry_framework__mutations__inputs.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/mutations/inputs.py
    - Result: No issues. Files changed: none; validation: import block pulls only `Upload` (no read-output symbols); file `elif` branch emits only the `(attachment, camel_name, Upload)` triple and falls through to shared override-skip/`input_field_required`/`| None`-widening; CR-6 carve-out lifted by ordering (no early raise); confirmed `FileField/ImageField.is_relation` False. No code edited.

- [x] django_strawberry_framework/mutations/permissions.py
    - docs/shadow/current/django_strawberry_framework__mutations__permissions.stripped.py
    - docs/shadow/current/django_strawberry_framework__mutations__permissions.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__mutations__permissions.stripped.py and docs/shadow/current/django_strawberry_framework__mutations__permissions.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/mutations/permissions.py
    - Result: No issues. Files changed: none; validation: safe-default anonymous denial, single-sited `request_from_info`, operation->action map (no reachable KeyError), and codename format reconciled; `_resolve_model` None case guarded upstream at class creation; no code edited.

- [x] django_strawberry_framework/mutations/resolvers.py
    - docs/shadow/current/django_strawberry_framework__mutations__resolvers.stripped.py
    - docs/shadow/current/django_strawberry_framework__mutations__resolvers.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__mutations__resolvers.stripped.py and docs/shadow/current/django_strawberry_framework__mutations__resolvers.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/mutations/resolvers.py
    - Result: No issues. Files changed: none; validation: verify-first confirmed — no file-specific code (grep for upload/file symbols returns nothing), `UploadedFile` rides the generic `model(**attrs)`/`setattr` path, `UNSET` stripped in `_decode_relations`, explicit null on `null=False` routes through `_explicit_null_error` to a field-keyed `FieldError`. No code edited.

- [x] django_strawberry_framework/mutations/sets.py
    - docs/shadow/current/django_strawberry_framework__mutations__sets.stripped.py
    - docs/shadow/current/django_strawberry_framework__mutations__sets.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__mutations__sets.stripped.py and docs/shadow/current/django_strawberry_framework__mutations__sets.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/mutations/sets.py
    - Result: No issues. Files changed: none; validation: uv run pytest tests/mutations/test_sets.py -q -> 44 passed; field-sequence dedup, shape-walk cycle guard, relation-override shape-lock, and async-coroutine auth-bypass guard reconciled; no read-output/Upload leak.

- [x] django_strawberry_framework/optimizer/_context.py
    - docs/shadow/current/django_strawberry_framework__optimizer___context.stripped.py
    - docs/shadow/current/django_strawberry_framework__optimizer___context.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__optimizer___context.stripped.py and docs/shadow/current/django_strawberry_framework__optimizer___context.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/optimizer/_context.py
    - Result: No issues. Files changed: none; validation: uv run pytest tests/optimizer/test_extension.py -k "stash or context" -q -> 21 passed; read/write dict-first vs setattr-first symmetry and the deliberately-scoped catch sets reconciled against the pinning suite; no code edited.

- [x] django_strawberry_framework/optimizer/extension.py
    - docs/shadow/current/django_strawberry_framework__optimizer__extension.stripped.py
    - docs/shadow/current/django_strawberry_framework__optimizer__extension.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__optimizer__extension.stripped.py and docs/shadow/current/django_strawberry_framework__optimizer__extension.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/optimizer/extension.py
    - Result: No issues. Files changed: none; validation: depth-keyed fragment-var dedup, reachable-fragment recursion tail, schema-reachable-types walk, `_optimize` evaluated-queryset short-circuit, and LRU/cache-key memoization reconciled against source + selections/typing contracts; no code edited.

- [x] django_strawberry_framework/optimizer/field_meta.py
    - docs/shadow/current/django_strawberry_framework__optimizer__field_meta.stripped.py
    - docs/shadow/current/django_strawberry_framework__optimizer__field_meta.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__optimizer__field_meta.stripped.py and docs/shadow/current/django_strawberry_framework__optimizer__field_meta.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/optimizer/field_meta.py
    - Result: No issues. Files changed: none; validation: uv run pytest tests/optimizer/test_field_meta.py -q -> 17 passed; `_target_pk_name`/`_has_composite_pk` `_meta`/`pk` access confirmed guarded (empirically `_meta.pk` always set in Django 6.0), no `relation_kind` name-shadowing; no code edited.

- [x] django_strawberry_framework/optimizer/hints.py
    - docs/shadow/current/django_strawberry_framework__optimizer__hints.stripped.py
    - docs/shadow/current/django_strawberry_framework__optimizer__hints.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__optimizer__hints.stripped.py and docs/shadow/current/django_strawberry_framework__optimizer__hints.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/optimizer/hints.py
    - Result: No issues. Files changed: none; validation: uv run pytest tests/optimizer/test_hints.py -q -> 23 passed; `__post_init__` conflict guards, factory classmethods, `hint_is_skip` dispatch, and frozen-dataclass `SKIP` singleton idiom reconciled. PROCESS NOTE: hunter ran one read-only `git log` despite the no-git rule (no state change).

- [x] django_strawberry_framework/optimizer/plans.py
    - docs/shadow/current/django_strawberry_framework__optimizer__plans.stripped.py
    - docs/shadow/current/django_strawberry_framework__optimizer__plans.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__optimizer__plans.stripped.py and docs/shadow/current/django_strawberry_framework__optimizer__plans.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/optimizer/plans.py
    - Result: No issues. Files changed: none; validation: uv run pytest tests/optimizer/test_plans.py -q -> 86 passed; `_IndexedList` dedup, `finalize` idempotency, `diff_plan_for_queryset` early-return identity guard, window-pagination limit asymmetry, and bounded path walk reconciled; consumer contracts cross-checked; no code edited.

- [x] django_strawberry_framework/optimizer/selections.py
    - docs/shadow/current/django_strawberry_framework__optimizer__selections.stripped.py
    - docs/shadow/current/django_strawberry_framework__optimizer__selections.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__optimizer__selections.stripped.py and docs/shadow/current/django_strawberry_framework__optimizer__selections.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/optimizer/selections.py
    - Result: No issues. Files changed: none; validation: uv run pytest tests/optimizer/test_selections.py -q -> 14 passed, uv run ruff check -> All checks passed; `should_include` @skip/@include polarity, AST->converted mirror vs upstream nodes, and fragment-recursion guards reconciled; no code edited.

- [x] django_strawberry_framework/optimizer/walker.py
    - docs/shadow/current/django_strawberry_framework__optimizer__walker.stripped.py
    - docs/shadow/current/django_strawberry_framework__optimizer__walker.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__optimizer__walker.stripped.py and docs/shadow/current/django_strawberry_framework__optimizer__walker.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/optimizer/walker.py
    - Result: No issues. Files changed: none; validation: FK-id elision composite-PK guard, connector-column relation-kind dispatch, scalar-only order-column projection, connection-window fallback shapes, and `enable_only` gate threading reconciled; helper signatures cross-checked; no code edited.

- [x] django_strawberry_framework/orders/base.py
    - docs/shadow/current/django_strawberry_framework__orders__base.stripped.py
    - docs/shadow/current/django_strawberry_framework__orders__base.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__orders__base.stripped.py and docs/shadow/current/django_strawberry_framework__orders__base.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/orders/base.py
    - Result: No issues. Files changed: none; validation: thin `RelatedSetTargetMixin` port verified — `_target_attr`/`_owner_attr` slots, `bind_orderset`/`.orderset` property+setter delegations, and optional `field_name` all reconciled against the mixin and consumers; no code edited.

- [x] django_strawberry_framework/orders/factories.py
    - docs/shadow/current/django_strawberry_framework__orders__factories.stripped.py
    - docs/shadow/current/django_strawberry_framework__orders__factories.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__orders__factories.stripped.py and docs/shadow/current/django_strawberry_framework__orders__factories.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/orders/factories.py
    - Result: No issues. Files changed: none; validation: `OrderArgumentsFactory` verified a faithful peer of the filter factory — fresh ClassVar dicts, order-family hook attrs, `_build_input_triples` with no operator bag (Decision 8), `del type_name` intentional; lone TODO is a spec-028 deferral (not a spec-037 anchor); no code edited.

- [x] django_strawberry_framework/orders/inputs.py
    - docs/shadow/current/django_strawberry_framework__orders__inputs.stripped.py
    - docs/shadow/current/django_strawberry_framework__orders__inputs.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__orders__inputs.stripped.py and docs/shadow/current/django_strawberry_framework__orders__inputs.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/orders/inputs.py
    - Result: No issues. Files changed: none; validation: uv run pytest tests/orders/test_inputs.py -q -> 40 passed; `Ordering.resolve` substring/NULLS polarity traced exhaustively across all 6 enum members, concrete-field-names M2M/reverse exclusion, and python_attr keying consistency reconciled; no code edited.

- [x] django_strawberry_framework/orders/sets.py
    - docs/shadow/current/django_strawberry_framework__orders__sets.stripped.py
    - docs/shadow/current/django_strawberry_framework__orders__sets.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__orders__sets.stripped.py and docs/shadow/current/django_strawberry_framework__orders__sets.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/orders/sets.py
    - Result: No issues. Files changed: none; validation: uv run pytest tests/orders/test_sets.py -q -> 39 passed; to-many path walk, Min/Max ASC/DESC aggregate selection, alias uniqueness, MRO-safe cache gate, and family-neutral `request_from_info` reconciled. NOTE: the integration-pass "pre-existing red" (`test_orderset_request_from_info_raises_on_unrecognized_context_shape` asserting stale `OrderSet.apply`) does NOT reproduce at this HEAD — the test asserts the current "OrderSet could not resolve" message and passes.

- [x] django_strawberry_framework/permissions.py
    - docs/shadow/current/django_strawberry_framework__permissions.stripped.py
    - docs/shadow/current/django_strawberry_framework__permissions.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__permissions.stripped.py and docs/shadow/current/django_strawberry_framework__permissions.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/permissions.py
    - Result: No issues. Files changed: none; validation: uv run pytest tests/test_permissions.py --no-cov -> 33 passed, 1 skipped; `_is_cascadable_edge` four-predicate guard, `_validate_fields` ordering, cycle-guard finally-reset, `_walk` Q-composition + db-alias pin, and single-sync-walk async wrap reconciled. NOTE (not fixed): a runtime error string says "in 0.0.10" while at 0.0.11 — behaviorally accurate, outside the version-quintet, untouched by this cycle.

- [x] django_strawberry_framework/registry.py
    - docs/shadow/current/django_strawberry_framework__registry.stripped.py
    - docs/shadow/current/django_strawberry_framework__registry.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__registry.stripped.py and docs/shadow/current/django_strawberry_framework__registry.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/registry.py
    - Result: No issues. Files changed: none; validation: `unregister` lock-step invariant, `register_with_definition` atomic rollback, `discard_pending` identity-match, and `clear()` co-clear coverage reconciled — upload build added no new global ledger (DjangoFileType/ImageType ride `_definitions`/`_types`); no code edited.

- [x] django_strawberry_framework/relay.py
    - docs/shadow/current/django_strawberry_framework__relay.stripped.py
    - docs/shadow/current/django_strawberry_framework__relay.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__relay.stripped.py and docs/shadow/current/django_strawberry_framework__relay.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/relay.py
    - Result: No issues. Files changed: none; validation: uv run pytest tests/test_relay_node_field.py -q -> 37 passed; broad-vs-narrow decode catch split, `_coerce_pk_or_none` validator behavior, `_interleave` positional indexing + length guard, and async/sync dispatch reconciled; no code edited.

- [x] django_strawberry_framework/scalars.py
    - docs/shadow/current/django_strawberry_framework__scalars.stripped.py
    - docs/shadow/current/django_strawberry_framework__scalars.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__scalars.stripped.py and docs/shadow/current/django_strawberry_framework__scalars.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/scalars.py
    - Result: No issues. Files changed: none; validation: uv run ruff check -> All checks passed; runtime-confirmed `Upload`/`UploadDefinition` are pure re-exports (`is` identity True), `_PACKAGE_SCALAR_MAP == {BigInt: ...}` with no `Upload` key, and `__all__` is the module surface — all dicta priority #6 contracts hold; no code edited.

- [x] django_strawberry_framework/sets_mixins.py
    - docs/shadow/current/django_strawberry_framework__sets_mixins.stripped.py
    - docs/shadow/current/django_strawberry_framework__sets_mixins.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__sets_mixins.stripped.py and docs/shadow/current/django_strawberry_framework__sets_mixins.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/sets_mixins.py
    - Result: No issues. Files changed: none; validation: `expanded_once` `cls.__dict__.get` + `is not None` (serves cached empty OrderedDict, no MRO inheritance), idempotent `_bind_owner`, empty-token `ConfigurationError` guard, and sorted 6-tuple `__all__` reconciled against source + both consumers; no code edited.

- [x] django_strawberry_framework/types/base.py
    - docs/shadow/current/django_strawberry_framework__types__base.stripped.py
    - docs/shadow/current/django_strawberry_framework__types__base.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__types__base.stripped.py and docs/shadow/current/django_strawberry_framework__types__base.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/types/base.py
    - Result: Fixed Low. `_build_annotations` docstring still described the pre-spec-037 `convert_scalar` dispatch though the live call is now `convert_field_output(...)`; corrected the docstring (no behavior change). Verified the dicta #4 contract holds: `force_nullable` tri-state threaded through unchanged (identical keyword shape). Files changed: django_strawberry_framework/types/base.py (docstring only). Validation: uv run ruff format -> unchanged, uv run ruff check -> All checks passed.

- [x] django_strawberry_framework/types/converters.py
    - docs/shadow/current/django_strawberry_framework__types__converters.stripped.py
    - docs/shadow/current/django_strawberry_framework__types__converters.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__types__converters.stripped.py and docs/shadow/current/django_strawberry_framework__types__converters.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/types/converters.py
    - Result: No issues. Files changed: none; validation (keystone, all dicta #1 invariants confirmed against source): `Upload` absent; `SCALAR_MAP[File/Image]==str`; `FIELD_OUTPUT_TYPE_MAP=={ImageField: DjangoImageType, FileField: DjangoFileType}` (ImageField first); `_field_output_type_for` single shared walk; `_safe_file_attr` catch exactly `(ValueError, OSError, NotImplementedError)` with `SuspiciousFileOperation` propagating; `name` non-null / others nullable; `DjangoImageType` inherits 4 subfields. File output is unconditionally nullable-by-default (subsumes null/blank; required by the empty-FieldFile parent resolver) — not a defect. No code edited.

- [x] django_strawberry_framework/types/definition.py
    - docs/shadow/current/django_strawberry_framework__types__definition.stripped.py
    - docs/shadow/current/django_strawberry_framework__types__definition.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__types__definition.stripped.py and docs/shadow/current/django_strawberry_framework__types__definition.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/types/definition.py
    - Result: No issues. Files changed: none; validation: `related_target_for` finalize-gated memoization (None as valid cached value), membership-based `has_custom_id_resolver_for` cache, and the `__func__`-identity custom-id-resolver detection reconciled against callers; pk_name name/attname consistency confirmed. PROCESS NOTE: hunter ran two read-only `git log` queries despite the no-git rule (no state change).

- [x] django_strawberry_framework/types/finalizer.py
    - docs/shadow/current/django_strawberry_framework__types__finalizer.stripped.py
    - docs/shadow/current/django_strawberry_framework__types__finalizer.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__types__finalizer.stripped.py and docs/shadow/current/django_strawberry_framework__types__finalizer.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/types/finalizer.py
    - Result: No issues. Files changed: none; validation (dicta #3 confirmed): `_attach_file_resolvers` runs in the same Phase-2 loop as `_attach_relation_resolvers` (before the Phase-3 `strawberry.type(...)` freeze), uses the broader `consumer_authored_fields` skip set, and the relation/non-file skips live in resolvers.py. No code edited.

- [x] django_strawberry_framework/types/relations.py
    - docs/shadow/current/django_strawberry_framework__types__relations.stripped.py
    - docs/shadow/current/django_strawberry_framework__types__relations.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__types__relations.stripped.py and docs/shadow/current/django_strawberry_framework__types__relations.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/types/relations.py
    - Result: No issues. Files changed: none; validation: `PendingRelation.__hash__ is object.__hash__` confirmed True (identity hash, load-bearing since `django_field` may be unhashable); identity-based `discard_pending` contract and sentinel `__repr__` reconciled; no code edited.

- [x] django_strawberry_framework/types/relay.py
    - docs/shadow/current/django_strawberry_framework__types__relay.stripped.py
    - docs/shadow/current/django_strawberry_framework__types__relay.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__types__relay.stripped.py and docs/shadow/current/django_strawberry_framework__types__relay.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/types/relay.py
    - Result: No issues. Files changed: none; validation: uv run pytest tests/ -k "relay or globalid or node or typename" -> 337 passed (types/relay.py 100% line cov); `__func__`/marker custom-resolver discriminators, composite-pk stamp gate, GlobalID strategy encode/decode routing, and async/sync split reconciled; no code edited.

- [x] django_strawberry_framework/types/resolvers.py
    - docs/shadow/current/django_strawberry_framework__types__resolvers.stripped.py
    - docs/shadow/current/django_strawberry_framework__types__resolvers.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__types__resolvers.stripped.py and docs/shadow/current/django_strawberry_framework__types__resolvers.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/types/resolvers.py
    - Result: No issues. Files changed: none; validation (dicta #3 confirmed): `_make_file_resolver` does object-nullability only (`value if value else None`, no try/except — guard lives solely in `_safe_file_attr`); `_attach_file_resolvers` skips relations + non-file columns via the shared imported `_field_output_type_for`; non-overridden file column gets a generated `resolve_<field>`, consumer overrides skipped. uv run ruff check -> All checks passed; no code edited.

- [x] django_strawberry_framework/utils/connections.py
    - docs/shadow/current/django_strawberry_framework__utils__connections.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__connections.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__utils__connections.stripped.py and docs/shadow/current/django_strawberry_framework__utils__connections.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/utils/connections.py
    - Result: No issues. Files changed: none; validation: uv run pytest tests/utils/test_connections.py -q -> 9 passed (100% line cov); reverse-window predicate, `after`+`last` UnwindowableConnection rejection, and `limit` rule reconciled against both consumers; no code edited.

- [x] django_strawberry_framework/utils/input_values.py
    - docs/shadow/current/django_strawberry_framework__utils__input_values.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__input_values.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__utils__input_values.stripped.py and docs/shadow/current/django_strawberry_framework__utils__input_values.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/utils/input_values.py
    - Result: No issues. Files changed: none; validation: `iter_active_fields` early-return ordering (list-flatten before `iter_input_items`), defensive `related` lookup (`... or {}`), and disjoint logic/related/leaf classification reconciled against all three consumers; no code edited.

- [x] django_strawberry_framework/utils/inputs.py
    - docs/shadow/current/django_strawberry_framework__utils__inputs.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__inputs.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__utils__inputs.stripped.py and docs/shadow/current/django_strawberry_framework__utils__inputs.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/utils/inputs.py
    - Result: No issues. Files changed: none; validation: uv run pytest tests/utils/test_inputs.py -q -> 10 passed; idempotent materialization ledger + collision semantics, BFS `seen` gate, and cycle-safe `_safe_import` reconciled. Noted (dropped, not a defect): `graphql_camel_name` docstring says "lowercase the head" but leaves head untouched — accurate for all real (snake_case) callers. No code edited.

- [x] django_strawberry_framework/utils/permissions.py
    - docs/shadow/current/django_strawberry_framework__utils__permissions.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__permissions.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__utils__permissions.stripped.py and docs/shadow/current/django_strawberry_framework__utils__permissions.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/utils/permissions.py
    - Result: No issues. Files changed: none; validation: `request_from_info` confirmed resolving via context.request with bare-HttpRequest fallback then ConfigurationError (does not assume context.user); single-walk H3 partition, dedup `fired` map, and sorted 9-name `__all__` reconciled against consumers + `iter_active_fields`; no code edited.

- [x] django_strawberry_framework/utils/querysets.py
    - docs/shadow/current/django_strawberry_framework__utils__querysets.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__querysets.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__utils__querysets.stripped.py and docs/shadow/current/django_strawberry_framework__utils__querysets.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/utils/querysets.py
    - Result: No issues. Files changed: none; validation: uv run pytest tests/utils/test_querysets.py -q -> 12 passed (100% line cov); confirmed `apply_type_visibility_sync` is the SOLE sync-`get_queryset`/async-reject site (others delegate), with `.close()` before `raise SyncMisuseError`; iscoroutine(sync)/isawaitable(async) asymmetry intentional; no code edited.

- [x] django_strawberry_framework/utils/relations.py
    - docs/shadow/current/django_strawberry_framework__utils__relations.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__relations.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__utils__relations.stripped.py and docs/shadow/current/django_strawberry_framework__utils__relations.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/utils/relations.py
    - Result: No issues. Files changed: none; validation: uv run pytest tests/utils/test_relations.py -> 11 passed (100% line cov); `relation_kind` branch ordering verified against Django flag values (OneToOneRel.one_to_many=False), `one_to_many`+`not auto_created`->"many" fallback, and `instance_accessor` three-tier read reconciled; no code edited.

- [x] django_strawberry_framework/utils/strings.py
    - docs/shadow/current/django_strawberry_framework__utils__strings.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__strings.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__utils__strings.stripped.py and docs/shadow/current/django_strawberry_framework__utils__strings.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/utils/strings.py
    - Result: No issues. Files changed: none; validation: `snake_case`/`pascal_case` reconciled against all docstring examples incl. acronym edges (HTMLParser, my_HTTP_response) and empty-string; pure str->str, lru_cache sound; no code edited.

- [x] django_strawberry_framework/utils/typing.py
    - docs/shadow/current/django_strawberry_framework__utils__typing.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__typing.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__utils__typing.stripped.py and docs/shadow/current/django_strawberry_framework__utils__typing.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/utils/typing.py
    - Result: No issues. Files changed: none; validation: uv run pytest tests/utils/test_typing.py -q -> 17 passed (100% line cov); `is_async_callable` partial+`__call__` detection, `unwrap_graphql_type` bounded peel with cyclic-chain raise, and `unwrap_return_type` of_type-first + bare-list `Any` sentinel reconciled; no code edited.
