# Build: Slice 1 — code conformance (spec-037 graded against `HEAD`)

Spec reference: `docs/SPECS/spec-037-upload_file_image_mapping-0_0_11.md` (whole file; `## Slice checklist` 223-390, `## Architectural decisions` 769-1119, `## Edge cases and constraints` 1142-1223, `## Test plan` 1224-1285, `## Definition of done` 1375-1470)
Status: final-accepted

Cycle: the `037` residual-reconciliation cycle (`docs/builder/build-037-upload_file_image_mapping-0_0_11.md` `## Cycle shape`). This pass answers the maintainer's question — **did the code drop, skip, or deviate from anything the spec planned?** — for every Decision, every `## Slice checklist` sub-check, every `## Definition of done` item, every `## Edge cases and constraints` guarantee, and every `## Test plan` bullet.

**Verdict vocabulary** (from the plan's `## Cycle shape`): **BUILT-CONFORMANT** (code does what the spec says; nothing changes) · **DROPPED / DEVIATED** (spec planned it, code does not do it; **the code changes**) · **SUPERSEDED** (a later card deliberately changed the contract; **the code stands, the spec is Slice 2's**).

Hot-path declaration: **none** (copied from the plan as written). The one planned change is a test; it adds no runtime code.
Floor-verification scope: **re-declared in this artifact** because a code change is planned — see `### Floor-verification scope (re-declared)`.

Raw `path:NN` references are used below under `AGENTS.md` rule 27's per-cycle-artifact carve-out; symbol-qualified anchors are given wherever the symbol is stable.

---

## Plan (Worker 1)

### How every claim below was proven

`docs/builder/BUILD.md` `## Claims are proven mechanically, never accepted on prose`. `git stash` / `git checkout` / `git restore` / `git worktree` were **not used at any point** — this tree carries a concurrent session's uncommitted work.

**Baseline: which of the graded files are dirty.** The build plan's `## Baseline-dirty out-of-scope files` predicted `types/converters.py`, `types/resolvers.py`, `types/finalizer.py`, `types/base.py` and `scalars.py` clean, and `mutations/inputs.py` / `mutations/resolvers.py` dirty. **The plan is wrong about one file: `types/finalizer.py` is dirty.** Measured:

```shell
for p in types/converters.py types/resolvers.py types/finalizer.py types/base.py scalars.py __init__.py mutations/inputs.py mutations/resolvers.py; do
  out=<scratch>/head/$(echo $p | tr '/' '_'); git show HEAD:django_strawberry_framework/$p > $out
  if diff -q $out django_strawberry_framework/$p >/dev/null; then echo "SAME  $p"; else echo "DIFF  $p"; fi
done
```

```text
SAME  types/converters.py
SAME  types/resolvers.py
DIFF  types/finalizer.py
SAME  types/base.py
SAME  scalars.py
SAME  __init__.py
DIFF  mutations/inputs.py
DIFF  mutations/resolvers.py
```

So: **`types/converters.py`, `types/resolvers.py`, `types/base.py`, `scalars.py` and `__init__.py` are byte-identical to `HEAD` and are graded against the working copy directly.** `types/finalizer.py`, `mutations/inputs.py` and `mutations/resolvers.py` are graded **only** against `git show HEAD:<path>` into `<scratch>/head/`, and every line number for those three is a `HEAD`-blob line number.

The `types/finalizer.py` divergence is a concurrent session's work on a **model-mismatch error path** (`_safe_class_name` vs `_safe_arg_repr` for a non-class `Meta.model`, and its docstring). It does not touch `_attach_file_resolvers` or its call site; recorded, not reverted (`AGENTS.md` rule 34).

`django_strawberry_framework/conf.py` is also dirty and was likewise read only from `<scratch>/head/conf.py` for the Decision-8 settings-key grade.

### The one open conformance question: `Meta.required_overrides` → `force_nullable` → file branch

**The audit's claim is CONFIRMED as a test gap and REFUTED as a behavior gap.** The threading works at `HEAD`; nothing pins it end-to-end.

**Behavior: proven to work.** A read-only probe (no repo file written; run from `<scratch>/probe_meta_thread.py` against the clean `types/base.py` + `types/converters.py`):

```python
class _Probe(models.Model):
    attachment = models.FileField()
    preview = models.ImageField(blank=True)
    class Meta: managed = False; app_label = "probe_meta_thread"

meta = type("Meta", (), {"model": _Probe, "fields": ("id", "attachment", "preview"),
                         "required_overrides": ("attachment",)})
T = type("ProbeType", (DjangoType,), {"Meta": meta})
```

```text
attachment -> <class 'django_strawberry_framework.types.converters.DjangoFileType'>
preview    -> django_strawberry_framework.types.converters.DjangoImageType | None
bare non-null? True
preview (required_overrides) -> <class '…converters.DjangoImageType'> bare? True
```

The path is `types/base.py::_build_annotations` (`django_strawberry_framework/types/base.py:1931-1953`: `if field.name in nullable_overrides: force_nullable = True / elif field.name in required_overrides: force_nullable = False / else None`, then `convert_field_output(..., force_nullable=force_nullable, expose_filesystem_path=...)`) into `types/converters.py::convert_field_output` #"file_effective_null = True if force_nullable is None else force_nullable". No file-specific branch sits between them, and `types/base.py::_validate_nullability_override_targets` does **not** reject a file column — its relation-reject message even says the scope is "(scalar columns and file/image output objects)".

**Tests: the gap is real. The test bodies read, not their names.**

- `tests/types/test_converters.py::test_convert_field_output_force_nullable_overrides_default` (`tests/types/test_converters.py:2024-2049`) — asserts `convert_field_output(blank_file, "OwnerType", force_nullable=False) is DjangoFileType` and `convert_field_output(required, "OwnerType", force_nullable=True) == (DjangoFileType | None)`. It calls the **converter seam directly with the keyword**; the string `Meta` appears only in the synthetic model's `class Meta`. It never constructs a `DjangoType`.
- `tests/types/test_base.py::test_nullable_override_flips_annotation` (`tests/types/test_base.py:1936-1949`) — the only `Meta.required_overrides`-through-a-`DjangoType` assertion. Its model is `_make_override_model` (`tests/types/test_base.py:1888-1912`): `text_value` / `note` / `status` / `nullable_status` (`TextField`s) and `partner` (a self-FK). **No file or image column.**
- `tests/types/test_base.py::test_override_flips_choice_field_enum_nullability`, `::test_override_redundant_is_no_op` — same scalar-only model.
- `tests/types/test_base.py`'s spec-037 file block (`tests/types/test_base.py:2078-2172`) uses `_make_file_override_model_type` (`tests/types/test_base.py:2164-2167`), whose signature is `(model, *, namespace=None)` — **it accepts no `Meta` attributes at all**, so no override can be declared through it.
- `tests/types/test_base.py::test_the_sibling_collection_keys_accept_a_frozenset_too` (`tests/types/test_base.py:2365-2372`) does use a file-bearing model (`_make_path_optin_model`) — but its override target is `"title"`, the `TextField`.

Whole-tree measurement, occurrences not lines:

```shell
grep -rn --include='*.py' 'required_overrides' tests/ examples/ | wc -l   # -> 24
```

All 24 were opened. Override targets across them: `note`, `text_value`, `status`, `nullable_status`, `partner`, `id`, `title`, `subtitle`. **Zero name a file or image column.** The live fakeshop file/image types (`examples/fakeshop/apps/scalars/schema.py::MediaSpecimenType`, `::MediaSpecimenWithPathType`) declare no override key either.

**Verdict.** Not DROPPED (the contract landed and executes), not SUPERSEDED (nothing later changed it — `docs/GLOSSARY.md` still documents it twice, at the `Meta.required_overrides` entry #"On a file/image column it is also the opt-out from the **default-nullable** output object" and at #"as of `0.0.11`, the file/image output objects (`required_overrides` forces a non-null `DjangoFileType!`)"). It is **BUILT-CONFORMANT with a Medium test gap**: a documented public `Meta` contract, named by the Slice-1 sub-check and by `## Test plan`, whose only pin is at a seam one layer below the contract's own spelling. `BUILD.md` `## Severity definitions` — "missing tests for important branches" — Medium. **This is the single item that owes code in this cycle**; the fix is `### Fix checklist` item 1.

### The two narrowly-covered items the audit raised: both CONFIRMED conformant

- **No end-to-end `FilterSet` + `filter_input_type()` test over a file column — CONFORMANT, refuting nothing.** The Slice-1 sub-check itself (spec:284-291) narrows the requirement to the *delegation path*, in its own words: "this pins the package's own delegation path because django_filter's auto `Meta.fields` filter for a bare `FileField` raises before package code runs". `tests/types/test_converters.py::test_file_columns_stay_scalar_on_the_filter_input_path` (`tests/types/test_converters.py:2069-2100`) asserts exactly that surface — `scalar_for_field(attachment) is str`, `scalar_for_field(preview) is str`, `_scalar_from_model_field(attachment) is str`, `_scalar_from_model_field(preview) is str`, `SCALAR_MAP[models.FileField] is str`, `SCALAR_MAP[models.ImageField] is str`, `FIELD_OUTPUT_TYPE_MAP[models.FileField] is DjangoFileType`. The reasoning still holds; no code owed. (`## Test plan`'s converter bullet spells the same requirement as a `FilterSet` test — a spec-internal inconsistency, recorded as **N14** for Slice 2.)
- **No live-HTTP `<Model>PartialInput` upload test — CONFORMANT, cannot be a drop.** Decision 9 as authored required no live coverage at all. What shipped is *more* than the spec asked: `examples/fakeshop/test_query/test_uploads_api.py` carries 9 live tests, including `::test_multipart_create_uploads_real_files_over_http`. `grep -n '^def test_'` over that file returns 9 names, none of them a partial-input upload. Not owed.

### Also graded, per the dispatch

- **Every `## Edge cases and constraints` guarantee** — 15 bullets (`grep -c '^- \*\*'` over spec:1142-1223 → `15`). Table below.
- **`## Test plan`'s "Cross-cutting — no regression"** — table below.
- **Decision 2's card-scope boundary and Decision 8's "no new setting"** — table below. `DJANGO_STRAWBERRY_FRAMEWORK` carries 9 feature keys at `HEAD` (`grep -E '^[A-Z_]+_KEY = ' <scratch>/head/conf.py` → 10 lines, one of which is `DJANGO_SETTINGS_KEY` itself): `APPLY_UPSTREAM_PATCHES`, `NESTED_CONNECTION_STRATEGY`, `SINGLE_PARENT_FAST_PATH`, `TESTING_ENDPOINT`, `HIDE_FLAT_FILTERS`, `RELAY_GLOBALID_STRATEGY`, `MAX_REQUEST_BODY_BYTES`, `RESOURCE_POLICY`, `ERROR_POLICY`. **None is file/image-related**; the only file/upload words in `HEAD`'s `conf.py` are 4 comment lines inside the `MAX_REQUEST_BODY_BYTES` block. `Meta.filesystem_path_fields` is a `Meta` key, not a setting — so Decision 8's *"no new setting"* half is **true**, and its *"no new `Meta` key"* half is **false** (Worker 0's D4).
- **Staged-anchor sweep** — below.

### Staged-anchor sweep (`BUILD.md` `## Cross-slice integration pass` step 6)

Population printed first, because a zero must be distinguishable from an unrun sweep. zsh does **not** word-split `$FILES`, so an array is used:

```shell
srcfiles=("${(@f)$(git ls-files 'django_strawberry_framework/**' 'tests/**' 'examples/**' 'scripts/**')}")
print -r -- "source/test/example/script files scanned: ${#srcfiles[@]}"
grep -rEn 'TODO\(spec-037|TODO-(ALPHA|BETA|STABLE)-037' django_strawberry_framework tests examples scripts | wc -l
```

```text
source/test/example/script files scanned: 440
anchor occurrences in that population: 0
```

Untracked files in the same trees were swept too — `git ls-files --others --exclude-standard` returns exactly one, `django_strawberry_framework/utils/canonical.py`, whose anchor count is `0`.

Repo-wide (excluding `.git/`, and excluding `KANBAN.md` / `KANBAN.html` / `BACKLOG.md` per the step's own carve-out) there are **11 occurrences**, every one inside a spec or rationale `.md` — `docs/SPECS/spec-037-…md` (7), `docs/SPECS/appx/spec-037-…-rationale.md` (2), `docs/SPECS/appx/spec-036-…-rationale.md` (1), `docs/builder/build-037-…md` (1). These are prose references to a discharged seam and to the card's own pre-`DONE` id, not staged anchors. **No finding.**

The related Slice-2 sub-check (spec:307-308) told `scalars.py` to *rewrite* its stale `TODO-ALPHA-035-0.0.11` docstring reference to `TODO-ALPHA-037-0.0.11`. At `HEAD`, `grep -c 'TODO' django_strawberry_framework/scalars.py` → `0`, and `TODO-ALPHA-035` has **zero** occurrences anywhere in `django_strawberry_framework/`, `tests/`, `examples/` or `scripts/` (12 repo-wide, all in `.md` and `KANBAN.*`). Removing the anchor rather than re-pointing it is what `BUILD.md` step 6 requires once the seam ships; the *sub-check as written* would today create the very finding that step exists to catch. Code stands; sub-check is Slice 2's (**N12**).

### Per-item grading table

Legend: **BC** = BUILT-CONFORMANT · **DEV** = DROPPED / DEVIATED · **SUP** = SUPERSEDED.

#### Architectural decisions (10)

| # | Item | Verdict | Evidence |
| --- | --- | --- | --- |
| D-1 | Decision 1 — spec lives at `docs/spec-037-…md` | **SUP** | The file is at `docs/SPECS/spec-037-upload_file_image_mapping-0_0_11.md`; the `NEXT.md` Step 8 archive sweep moved it deliberately. Spec text false at spec:773. Slice 2 (Worker 0's D8, Slice 0's N4). |
| D-2 | Decision 2 — card-scope boundary: no multipart helper, no example upload app, no remote-storage policy, no image processing, no nested upload writes | **BC** | `grep -rn 'Upload' django_strawberry_framework/` (excluding `UploadMetadata` / `UploadedFile` / `upload_handlers`) resolves to five classes and no sixth: the scalar re-export (`scalars.py`, `__init__.py`); the three write-side annotation seams (`mutations/inputs.py`, `forms/inputs.py`, `rest_framework/serializer_converter.py` — the `0.0.12` / `0.0.13` reusers `## Out of scope` predicted); `utils/write_values.py` #"FILE handler: store the Upload under"; the value-budget's name-keyed `extensions/resource_policy.py` #"_UPLOAD_SCALAR_NAME = \"Upload\"" (spec-046 resource policy, not storage policy); and comment-only mentions in `views.py` / `conf.py`. **No image-processing, thumbnailing, signed-URL or remote-storage-adapter code exists anywhere in the package.** `TestClient` is spec-043 / `0.0.14`, not this card. `MediaSpecimen` (`examples/fakeshop/apps/scalars/models.py::MediaSpecimen`) is a model added to an existing app, not a new upload app. |
| D-3 | Decision 3 — read-side output types, `FIELD_OUTPUT_TYPE_MAP`, `SCALAR_MAP` untouched, thin wrapper, MRO precedence, broader consumer skip, breaking wire change | **SUP** (2 clauses) / BC (rest) | BC: `types/converters.py::FIELD_OUTPUT_TYPE_MAP` (`converters.py:266-269`, `ImageField` row first), `::_field_output_type_for`, `::convert_field_output` delegating to `convert_scalar` for non-file columns, `SCALAR_MAP[models.FileField] is str`, `types/base.py::_build_annotations` #"annotations[field.name] = convert_field_output(", `types/finalizer.py` (HEAD blob 968-972) passing `definition.consumer_authored_fields`. **SUP clause 1:** the four-field default `name` / `path` / `size` / `url` — `path` is not on `DjangoFileType` at `HEAD` (spec-048 Decision 1); the default is `name` / `size` / `url` and `path` lives on `DjangoFilePathType` / `DjangoImagePathType`. **SUP clause 2:** the wrapper signature `convert_field_output(field, type_name, *, force_nullable=None)` at spec:244 and spec:827 — `HEAD` has a fourth parameter `expose_filesystem_path=False`. |
| D-4 | Decision 4 — default-nullable parent object, per-subfield `_safe_file_attr` guard, narrow catch, `SuspiciousFileOperation` propagates, `required_overrides` opt-in | **BC** (test gap on the last clause) | `types/converters.py::_safe_file_attr` catches exactly `(ValueError, OSError, NotImplementedError)` and its docstring pins the `SuspiciousFileOperation` carve-out; `types/resolvers.py::_make_file_resolver` #"return value if value else None" with no `try/except`; `converters.py::convert_field_output` #"file_effective_null = True if force_nullable is None else force_nullable". The `path`-is-nullable clause is SUP (now on the opt-in siblings only). The `required_overrides` opt-in executes but is unpinned end-to-end — `### Fix checklist` item 1. |
| D-5 | Decision 5 — re-export `Upload`, do not register it | **BC** | `scalars.py` #"from strawberry.file_uploads.scalars import Upload, UploadDefinition"; both in the module `__all__`; `_PACKAGE_SCALAR_MAP` (`scalars.py:129`) carries no `Upload` key. Pinned by `tests/test_scalars.py::test_strawberry_config_scalar_map_excludes_upload`, `::test_upload_is_strawberry_builtin_re_export_not_a_wrapper`, `::test_upload_field_resolves_under_plain_strawberry_config`. |
| D-6 | Decision 6 — write-side seam becomes `Upload`; scalar attr name; no new resolver branch; explicit-`null` guard; CR-6 carve-out lifted | **BC** | HEAD blob: `mutations/inputs.py::model_column_write_kind` (`inputs.py:465-466`) `isinstance(field, (models.FileField, models.ImageField)) -> FILE`; `::model_column_write_annotation` (`inputs.py:581-582`) `if kind == FILE: return Upload`; `::model_column_input_annotation` (`inputs.py:614`) `python_attr = field.name`, never `<name>_id`. `mutations/resolvers.py` (`resolvers.py:433`) `FILE: scalar_handler` — no file-specific assignment branch, and `_explicit_null_error` (`resolvers.py:425`) runs on the same path. No `NotImplementedError` seam survives (`grep -n 'NotImplementedError' <HEAD blob>` → only the docstring at `inputs.py:601` recording that it was lifted). |
| D-7 | Decision 7 — three net-new root-exported symbols | **SUP** | `__init__.py` exports `Upload` / `DjangoFileType` / `DjangoImageType` **and** `DjangoFilePathType` / `DjangoImagePathType` (`__init__.py:49-52`, `:132-136`, `:155`), all five in `__all__`. Three is still true *of this card*; the surface sentence is not true unqualified. Worker 0's D2. |
| D-8 | Decision 8 — no new `Meta` key, no new setting, no dynamic storage policy | **SUP** (`Meta` half) / **BC** (setting half) | `types/base.py::ALLOWED_META_KEYS` (`base.py:70-89`) contains `filesystem_path_fields` — the `Meta` half is false at `HEAD` (Worker 0's D4). The setting half holds: 9 feature keys in `HEAD`'s `conf.py`, none file/image; no query-time settings read was introduced. |
| D-9 | Decision 9 — package tests own synthetic file/image models; live tests only if implementation exposes one; live fakeshop upload surface deferred | **SUP** | `examples/fakeshop/apps/scalars/models.py::MediaSpecimen` and `examples/fakeshop/test_query/test_uploads_api.py` (9 tests) shipped in this card's own final commit `4dca5ec9`. Decision 9's surviving body now states the retracted contract with **no marker** — Slice 0's **N1**, the highest-priority Slice-2 item. The synthetic-model half is BC (`tests/types/test_resolvers.py:1288-1560`, `tests/types/test_base.py:2078-2172`). |
| D-10 | Decision 10 — this card owns the final `0.0.11` bump | **BC** | The cut happened; `__version__` has since moved to `0.0.15` through four later cards. Explicitly **not a finding** (plan's `## Worker-0 verification pass`, "Not a finding"). |

#### `## Slice checklist` — 4 top-level rows + 13 sub-checks (17)

| # | Item | Verdict | Evidence |
| --- | --- | --- | --- |
| S1 | Slice 1 (top-level) — read output objects + read map + file resolver | **BC** | Rows S1a-S1e below. |
| S1a | `types/converters.py`: `DjangoFileType` (`name`/`path`/`size`/`url`), `DjangoImageType`, `_safe_file_attr`, `FIELD_OUTPUT_TYPE_MAP`, 3-param `convert_field_output`, `SCALAR_MAP` rows left `str`, MRO order | **SUP** (2 clauses) / BC (rest) | Same two SUP clauses as D-3 (`path` not a default subfield; the wrapper has a 4th parameter). Everything else present: `converters.py:110-172` (types), `:82-106` (`_safe_file_attr`), `:266-269` (map, `ImageField` first), `:229-232` (`SCALAR_MAP` file rows `str`). |
| S1b | `types/base.py`: `_build_annotations` calls `convert_field_output` for non-relation columns, applies default-nullable object shape | **BC** | `types/base.py:1948-1953`. |
| S1c | `types/resolvers.py` / `types/finalizer.py`: `_attach_file_resolvers` defined and called from the relation-resolver loop, parent-level nullability only, passed `consumer_authored_fields` | **BC** | `types/resolvers.py::_attach_file_resolvers` (`resolvers.py:789-818`), `::_make_file_resolver` (`resolvers.py:762-786`). HEAD `types/finalizer.py:954-972`: `_attach_relation_resolvers(..., skip_field_names=definition.consumer_assigned_relation_fields)` immediately followed by `_attach_file_resolvers(..., skip_field_names=definition.consumer_authored_fields)`, in the same loop body, before the interface-injection loop at `finalizer.py:974`. |
| S1d | Output object nullability: `DjangoFileType \| None` by default, composing with the `nullable_overrides` / `required_overrides` `force_nullable` tri-state; `required_overrides` is the opt-in to `DjangoFileType!` | **BC** (behavior) — **test gap, Medium** | Default half pinned by `tests/types/test_converters.py::test_convert_field_output_file_image_nullable_by_default` and `tests/types/test_resolvers.py::test_empty_required_file_resolves_to_null_without_error`. Compose half executes (probe above) but is pinned only at the converter seam. **`### Fix checklist` item 1.** |
| S1e | Package coverage: `test_converters.py` (map, MRO, default `\| None`, `force_nullable` compose, filter-input delegation), `test_resolvers.py` (empty→`None`, pass-through, per-subfield isolation), `test_base.py` (`avatar: str` override) | **BC** | `tests/types/test_converters.py:1939, :1958, :1975, :1995, :2024, :2069`; `tests/types/test_resolvers.py:1288, :1330, :1387`; `tests/types/test_base.py:2095`. The `force_nullable` compose test the sub-check names is in the file the sub-check names — the sub-check's letter is met; S1d's Meta-level gap is the contract one level up. |
| S2 | Slice 2 (top-level) — write `Upload` input + re-export | **BC** | Rows S2a-S2d. |
| S2a | `scalars.py`: re-export `Upload` + `UploadDefinition`, not in `_PACKAGE_SCALAR_MAP`; fix the stale docstring anchor to `TODO-ALPHA-037-0.0.11` | **SUP** (anchor clause) / **BC** (rest) | Re-export and non-registration confirmed (D-5). The anchor was **removed**, not re-pointed — 0 `TODO` in `scalars.py`, 0 `TODO-ALPHA-035` in any source tree. That is `BUILD.md` step 6's required outcome; the sub-check's spelling is stale (**N12**). |
| S2b | `mutations/inputs.py`: remove the staged seam, map to `Upload`, requiredness rule, `\| None` widening, plain field-name attr, lift the `036` CR-6 carve-out | **BC** | HEAD blob `inputs.py:465-466`, `:581-582`, `:614`, `:597-601`. Pinned by `tests/mutations/test_inputs.py::test_required_file_field_maps_to_upload`, `::test_required_image_field_maps_to_upload`, `::test_file_field_camel_cases_graphql_name`, `::test_blank_file_field_widens_to_upload_optional`, `::test_null_file_field_widens_to_upload_optional`, `::test_partial_input_file_field_always_optional_upload`, `::test_file_field_consumer_override_skips_generated_upload_field`. |
| S2c | `mutations/resolvers.py`: **verify** the generic scalar path handles an upload; add a branch only if a test proves it fails; `UNSET` leaves the file; explicit `null` on `null=False` is a `FieldError` | **BC** | HEAD blob `resolvers.py:378-380`, `:433`. No file-specific branch exists — the "verify, do not add" instruction was followed. Pinned by `tests/mutations/test_resolvers.py::test_create_assigns_uploaded_file_through_generic_path`, `::test_partial_update_omitting_file_leaves_stored_file_unchanged`, `::test_partial_update_with_new_upload_replaces_file_through_setattr_path`, `::test_explicit_null_on_non_nullable_file_column_is_field_error`. |
| S2d | Package coverage: `test_scalars.py` (both schema shapes, `BigInt` collision untouched); `test_inputs.py` (replace the staged tests); `test_resolvers.py` (create / partial update) | **BC** | `tests/test_scalars.py:587, :592, :599, :619, :625` plus the untouched `::test_strawberry_config_collision_with_package_scalar_raises_value_error` at `:437`; `tests/mutations/test_inputs.py:1166-1370`; `tests/mutations/test_resolvers.py:2197-2340`. |
| S3 | Slice 3 (top-level) — public exports + coverage hardening | **BC** | Rows S3a-S3b. |
| S3a | `__init__.py`: re-export `Upload` + `DjangoFileType` + `DjangoImageType`; all three in `__all__` | **BC** | `__init__.py:45`, `:49-52`, `:132-136`, `:155`. (Two further path-bearing exports were added later — D-7, spec-side only.) |
| S3b | `tests/base/test_init.py` pins the three; storage-failure / null-blank / image-dimension edge tests harden synthetic coverage | **BC** | `tests/base/test_init.py:77, :80, :99, :116-118`; `tests/types/test_resolvers.py::test_vanished_file_degrades_size_to_null`, `::test_corrupt_image_degrades_width_and_height_to_null`, `::test_suspicious_file_operation_is_not_swallowed`, `::test_empty_required_file_resolves_to_null_without_error`. |
| S4 | Slice 4 (top-level) — docs + the `0.0.11` cut + card wrap | **BC** | Rows S4a-S4b. |
| S4a | Version files to `0.0.11` (`pyproject.toml`, `__version__`, `test_version`, GLOSSARY version line, `uv.lock`) | **BC** | The cut landed; the quintet has since moved together to `0.0.15` (`__init__.py:61`, `tests/base/test_init.py:21`). Not a finding (D-10). |
| S4b | Doc updates (GLOSSARY promotions, README / docs/README, GOAL, TODAY, CHANGELOG-if-asked, KANBAN) | **BC** | Read-only confirmation at `HEAD`: `docs/GLOSSARY.md` carries `DjangoFileType` / `DjangoImageType` at `shipped (0.0.11)` (`GLOSSARY.md:123, :128`), the three in the **File / image uploads** browse row (`:256`), and full entries at `:604`, `:654`. These surfaces are **fenced out of this cycle** (plan `## Cycle shape`, "Scope fence"); graded read-only, not edited. |

#### `## Definition of done` (7)

| # | Item | Verdict | Evidence |
| --- | --- | --- | --- |
| DoD-1 | Spec + `-terms.csv` exist; `check_spec_glossary.py --spec docs/spec-037-…md` reports `OK: <N> terms` | **SUP** (path) / **BC** (substance) | Both files exist (`docs/SPECS/spec-037-…md`, `docs/SPECS/appx/spec-037-…-terms.csv`, 1,920 bytes). `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-037-upload_file_image_mapping-0_0_11.md` → `OK: 20 terms - all have glossary entries and at least one spec link.`, exit 0. The item's own `docs/spec-037-…` path is pre-archive (Slice 0's N4, three sites). |
| DoD-2 | Slice 1 read converter contract (types, map, wrapper, `SCALAR_MAP` untouched, default-nullable, `_safe_file_attr`, `consumer_authored_fields` skip, `FilterSet` scalar pin) | **SUP** (`path` subfield clause) / **BC** (rest) | Per D-3 / S1a-S1e. The DoD's `name` non-null; `path` / `size` / `url` nullable, resolver-backed" clause (spec:1393) is the third home of the `path` rot. |
| DoD-3 | Slice 2 write contract (`scalars.py` re-export, `mutations/inputs.py` mapping, seam + tests removed, CR-6 lifted, generic assignment verified) | **BC** | Per D-5 / D-6 / S2a-S2d. |
| DoD-4 | Slice 3 exports + synthetic-model coverage | **BC** | Per D-7 / S3a-S3b. |
| DoD-5 | Cross-cutting — full suite green at `fail_under = 100`; `ruff format` + `ruff check` clean; no other converter row changes; no read-side regression for non-file scalars | **BC** (as gradeable here) | `SCALAR_MAP` diff vs the pre-037 shape: the file/image rows are still `str` and no other row is file-related (`converters.py:229-232`). Focused run: `uv run pytest tests/types/test_converters.py tests/types/test_resolvers.py tests/types/test_base.py tests/mutations/test_inputs.py tests/mutations/test_resolvers.py tests/test_scalars.py tests/base/test_init.py --no-cov -q -n auto` → **498 passed, 2 skipped**. `uv run pytest examples/fakeshop/test_query/test_uploads_api.py --no-cov` → **9 passed**. `uv run ruff format --check` and `uv run ruff check` over the 11 spec-037 source and test files → `11 files already formatted` / `All checks passed!`. The `fail_under = 100` half is **the maintainer's gate, not a worker's** (`BUILD.md` `## Coverage is the maintainer's gate, not a worker's tool`) and no `--cov*` flag was run in this pass; the full sweep is the final gate's. |
| DoD-6 | Slice 4 doc surfaces + `KANBAN.md` records `DONE-NNN-0.0.11` | **BC** (docs) / **SUP** (placeholder) | Doc surfaces landed (S4b). The literal `DONE-NNN-0.0.11` is a two-site placeholder in the spec (Slice 0's N3) — spec-side only. |
| DoD-7 | The `0.0.11` bump lands in this card; the three net-new symbols in `__all__` | **BC** / **SUP** (the "three" count, per D-7) | Per D-10 / S3a. |

#### `## Edge cases and constraints` (15)

| # | Bullet | Verdict | Pinned by |
| --- | --- | --- | --- |
| E1 | Empty file descriptor → whole field `None` | **BC** | `tests/types/test_resolvers.py::test_empty_file_resolves_parent_object_to_null` |
| E2 | Empty value on `null=False, blank=False` → nullable by default | **BC** | `::test_empty_required_file_resolves_to_null_without_error`; `tests/types/test_converters.py::test_convert_field_output_file_image_nullable_by_default` |
| E3 | `Meta.required_overrides` on a blank file field is allowed; consumer owns the invariant | **BC** (behavior) — **unpinned** | Executes (probe above); no test declares it. **`### Fix checklist` item 1.** |
| E4 | Storage without local `path` → that subfield degrades to `null` | **SUP** | True only on `DjangoFilePathType` / `DjangoImagePathType` at `HEAD`; `path` is not a default subfield. Pinned there by `tests/types/test_resolvers.py::test_per_subfield_guard_isolates_storage_failure`, which opts `attachment` into `Meta.filesystem_path_fields`. Spec sentence needs the opt-in qualifier. |
| E5 | Missing file in storage → `size` / `url` / `width` / `height` degrade | **BC** | `::test_vanished_file_degrades_size_to_null`, `::test_corrupt_image_degrades_width_and_height_to_null` |
| E6 | Storage-metadata cost at list scale — not cached, not batched | **BC** | A non-guarantee. `converters.py::_safe_file_attr` and `::DjangoFileType` carry no cache or batch; nothing to pin. |
| E7 | Path-safety errors are not nulled (`SuspiciousFileOperation` propagates) | **BC** | `::test_suspicious_file_operation_is_not_swallowed`; catch list `(ValueError, OSError, NotImplementedError)` at `converters.py:105`. |
| E8 | Image dimensions degrade to `null`; never a Pillow-conditional skip | **BC** | `::test_corrupt_image_degrades_width_and_height_to_null` — no `skipif`. `pyproject.toml:57` declares `pillow>=10.0.0` in the `dev` group (the *preferred* answer; both Risks-fallback hedges in the spec are stale — Slice 0's N5). |
| E9 | Consumer scalar override bypasses map + resolver, both directions | **BC** | `tests/types/test_base.py::test_consumer_annotation_override_on_file_column_keeps_str_and_no_resolver`, `::test_consumer_assigned_field_resolver_on_file_column_is_not_clobbered`, and the control `::test_no_override_file_column_gets_generated_resolver`; write side `tests/mutations/test_inputs.py::test_file_field_consumer_override_skips_generated_upload_field`. |
| E10 | MRO precedence (`ImageField` before `FileField`) | **BC** | `tests/types/test_converters.py::test_field_output_map_mro_precedence_image_subclass_wins`; map order at `converters.py:266-269`. |
| E11 | File-column filter input stays scalar `str` | **BC** | `::test_file_columns_stay_scalar_on_the_filter_input_path` |
| E12 | Mutation partial update: `UNSET` leaves the file; explicit `null` on `null=False` is a `FieldError` | **BC** | `tests/mutations/test_resolvers.py::test_partial_update_omitting_file_leaves_stored_file_unchanged`, `::test_partial_update_with_new_upload_replaces_file_through_setattr_path`, `::test_explicit_null_on_non_nullable_file_column_is_field_error` |
| E13 | Multipart transport: consumers use existing handling "until the `0.0.14` `TestClient` helper lands" | **SUP** | `TestClient` shipped (spec-043); `examples/fakeshop/test_query/test_uploads_api.py` imports it (`from django_strawberry_framework.testing import TestClient`) and drives real multipart uploads. The forward-looking present tense is falsified (**N15**). |
| E14 | `Upload` resolves without extra config | **BC** | `tests/test_scalars.py::test_upload_field_resolves_under_plain_strawberry_config`, `::test_upload_field_resolves_under_strawberry_config_schema` |
| E15 | No `DjangoType` `Meta` key added; `DEFERRED_META_KEYS` / `ALLOWED_META_KEYS` **byte-unchanged** | **SUP** | `filesystem_path_fields` is in `ALLOWED_META_KEYS` (`types/base.py:77`). **This is a SECOND site for Worker 0's D4**, which named only Decision 8's title/body (**N10**). |

#### `## Test plan` (8)

| # | Bullet | Verdict | Note |
| --- | --- | --- | --- |
| T1 | Converter / map tests | **BC** with **two spec-internal inconsistencies** | Map, MRO (incl. consumer subclass), default `\| None`, delegation-path pin all present. But the bullet names *`Meta.nullable_overrides` / `Meta.required_overrides` still win* inside the **converter-seam** test file, whose entry point takes `force_nullable`, not `Meta` — the mis-homing that let the end-to-end pin fall through (**N13**). It also spells the delegation pin as a `FilterSet` test where the Slice-1 sub-check narrows it (**N14**). "`Meta.exclude` remains the opt-out" has no file-column-specific read-side test; `Meta.exclude` is name-keyed with no file branch in `types/base.py::_select_fields`, and the write side is pinned by `tests/mutations/test_inputs.py::test_file_field_narrowed_by_meta_fields_and_exclude` — **Low**, no code planned. |
| T2 | Generated output resolver tests | **BC** | All six named behaviors pinned (`tests/types/test_resolvers.py:1288-1560`), including per-subfield isolation one subfield at a time and non-`skip` image-dimension coverage. |
| T3 | Mutation input tests | **BC** | `tests/mutations/test_inputs.py:1166-1370`; `Meta.fields` / `Meta.exclude` narrowing and the lifted CR-6 merge both present. |
| T4 | Mutation resolver tests | **BC** | `tests/mutations/test_resolvers.py:2197-2340`; the generic-path verification is explicit in the test name and body. |
| T5 | Scalar config tests | **BC** | `tests/test_scalars.py:345-640`; fresh-dict, collision, both schema shapes. |
| T6 | Public export / version tests | **BC** | `tests/base/test_init.py:18-121`. |
| T7 | Live HTTP tests — "None required unless implementation adds or discovers a genuine fakeshop file/image field" | **SUP** | Nine live tests ship. Fourth site of Slice 0's N2 population; reconfirmed here. |
| T8 | Cross-cutting — no regression | **BC** (as gradeable) | See DoD-5. Coverage is the maintainer's gate; the full sweep is the final gate's. |

**Totals: 57 items graded** — 10 Decisions, 17 `## Slice checklist` rows, 7 `## Definition of done` items, 15 `## Edge cases` bullets, 8 `## Test plan` bullets.

**Verdict distribution: 42 BUILT-CONFORMANT · 0 DROPPED / DEVIATED · 15 carrying a SUPERSEDED clause.** Counted per table: Decisions 5 BC / 5 SUP; Slice checklist 15 BC / 2 SUP; Definition of done 3 BC / 4 SUP; Edge cases 12 BC / 3 SUP; Test plan 7 BC / 1 SUP. The 15 SUP rows, listed so the count is re-derivable: D-1, D-3, D-7, D-8, D-9, S1a, S2a, DoD-1, DoD-2, DoD-6, DoD-7, E4, E13, E15, T7.

Two of the BC rows — **D-4** and **S1d**, the same contract seen from the Decision and from the Slice checklist — carry the **Medium test gap** that is this slice's only code obligation; they are BC because the behavior landed and executes.

**No spec-planned behavior was dropped and no shipped behavior deviates from the spec's intent.** Every divergence is a later card's deliberate change (spec-048's `filesystem_path_fields` / default-`path` removal, spec-043's `TestClient`, this card's own final commit `4dca5ec9`) plus doc-path rot — all Slice 2's.

### DRY analysis

- **Helper inventory checked.** Refreshed for the **whole package** (`django_strawberry_framework/`, not `utils/` alone) with the `worker-1.md` `### Package-wide helper inventory before helper planning` command, into `docs/shadow/helper-inventory.md` — **2,006 lines** this run. Grepped, not read end to end: `grep -inE 'file_attr|field_output|file_resolver|force_nullable|override_targets|_output_type_for|filesystem_path'` → **9 hits**, every one opened at source: `types/converters.py::_safe_file_attr`, `::_field_output_type_for`, `::convert_field_output(field, type_name, *, force_nullable, expose_filesystem_path)`, `::convert_scalar`; `types/resolvers.py::_make_file_resolver`, `::_attach_file_resolvers`; `types/base.py::_build_annotations`, `::_validate_nullability_override_targets`, `::_validate_filesystem_path_targets`. **No second site anywhere in the package duplicates the file/image output or override-threading logic** — the inventory shows one owner per shape, which is why this pass proposes no consolidation. **It also proposes no new package helper**: the one planned change is a test.
- **Existing patterns reused.** The planned test needs a synthetic model carrying a `FileField` **and** an `ImageField` **and** a scalar, and a type factory that threads arbitrary `Meta` attributes. Both already exist, adjacent to where the test belongs: `tests/types/test_base.py::_make_path_optin_model` (`test_base.py:2175-2188` — `attachment` `FileField`, `preview` `ImageField(blank=True)`, `title` `TextField`) and `::_make_path_optin_type` (`test_base.py:2190-2207`, signature `(model, *, namespace=None, fields=None, **meta_attrs)`). **The plan reuses both verbatim.**
- **New helpers justified.** **None.** The obvious-but-wrong move is to extend `tests/types/test_base.py::_make_file_override_model_type` (`test_base.py:2164-2167`) with `**meta_attrs` so it matches `::_make_override_type` (`test_base.py:1914`) — that would produce a **third** near-identical `(model, *, namespace, **meta_attrs) -> type(..., (DjangoType,), ...)` factory in one file. Rejected. The condition that would justify extracting a single shared factory later: a **fourth** such factory being proposed; at that point collapse `_make_override_type` / `_make_file_override_model_type` / `_make_path_optin_type` into one parameterized builder in the same change.
- **Duplication risk avoided.** Two near-copies a naive implementation would introduce: (a) a fourth synthetic file-bearing model factory — avoided by reusing `_make_path_optin_model`; (b) a second copy of the `required_overrides`-flips-the-annotation assertion shape already in `::test_nullable_override_flips_annotation` — avoided by making the new test's subject the **file/image branch specifically** (bare object type vs `| None`), not the generic override mechanism, and by citing the scalar test rather than restating it.

### Boundary count and the split question

`BUILD.md` `### Slice splitting`. **Estimated new boundaries: zero.** The planned change adds no guard, cap, rejection path or validation branch — it is one test function over an existing, already-executing code path. The unit is one coherent diff in one file; **no split.**

### Hot-path declaration

**None**, unchanged from the plan. The planned change is a test; it adds no runtime code, no per-request/per-resolver/per-row work, no lock and no serialization point.

### Floor-verification scope (re-declared)

The plan declared `none by default` and required Worker 1 to re-declare if a code change is planned. Re-declared:

- **Scope:** the single new test node id in `tests/types/test_base.py` (`### Fix checklist` item 1) plus the existing `tests/types/test_base.py` spec-037 file-override block, re-run at the floor. Rationale for declaring a scope rather than `none`: `BUILD.md` `### When it is required` lists "schema and type construction against Strawberry internals", and the test constructs a `DjangoType` subclass through `__init_subclass__` and reads the annotations Strawberry will consume. The scope is deliberately narrow — this is not a second sweep.
- **Floor versions:** taken from `BUILD.md` `## Floor verification`, the single canonical statement. Not restated here.
- **Owning pass:** the **Worker 2 build pass** for this slice, in an isolated throwaway venv outside the repo, per `BUILD.md` `### How to build the floor venv`. Never the shared `.venv`. The final gate confirms it happened; it is not a second owner.

### Fix checklist

Written in the `### Spec slice checklist (verbatim)` position and under the same tick-and-audit discipline. `spec-037`'s `## Slice checklist` sub-checks are not copied verbatim here because they are already graded row-by-row above; these are the **contracts this slice owes**, one box each.

- [x] **Pin the `Meta` → `force_nullable` → file/image-branch threading end to end.** File: `tests/types/test_base.py`, inside the existing `# Consumer file/image override (spec-037 Decision 3)` block (`test_base.py:2078-2172`), after `::test_consumer_assigned_field_resolver_on_file_column_is_not_clobbered`. Test: `test_meta_required_overrides_forces_non_null_file_output`. It **must reuse** `::_make_path_optin_model` and `::_make_path_optin_type` (`test_base.py:2175-2207`) and add **no new model or type factory**. The assertions must prove, in one type built through the public `Meta` surface:
  - `Meta.required_overrides = ("attachment",)` on the `FileField` column → `__annotations__["attachment"] is DjangoFileType` — the **bare, non-null** object, not `DjangoFileType | None`. This is the contract `docs/GLOSSARY.md` publishes and the only assertion that pins `types/base.py:1933-1934` reaching `types/converters.py::convert_field_output` #"file_effective_null = True if force_nullable is None else force_nullable" for a file column.
  - The same override on the `ImageField` column (`preview`) → `is DjangoImageType`, proving the branch is not `FileField`-only.
  - **The control:** a sibling file/image column **not** named in the override, in the same type, still `== (Djangoᐧ… | None)`. Without it the first assertion cannot distinguish "the override did it" from "file columns are non-null". This control is the failability half — mirroring `::test_no_override_file_column_gets_generated_resolver`, the control the existing block already carries for the resolver-skip case.
  - `Meta.nullable_overrides = ("attachment",)` on a file column stays `DjangoFileType | None` — the redundant-override no-op direction, matching `::test_override_redundant_is_no_op`'s shape for scalars.
  - The test asserts **annotations**, not SDL, so it needs no schema build and no `finalize_django_types()` beyond what the surrounding block already does.
- [x] **Failability proof for the new pin.** `BUILD.md` `## Failability proofs`. This slice adds no new *boundary*, so the proof obligation is the test's own: mutate `types/converters.py::convert_field_output` to ignore `force_nullable` in the file branch (replace the `file_effective_null` expression with a literal `True`), run the focused scope, record the failing node ids, revert, and prove the revert by **byte comparison** (`md5`/`diff` against `git show HEAD:django_strawberry_framework/types/converters.py`), never by `git status`. A zero-row or one-row result is `revision-needed`, not an exception.
- [x] **Floor run.** Execute the `### Floor-verification scope (re-declared)` scope in an isolated venv outside the repo and record the venv path, the resolved Django / Python / strawberry-graphql versions as read by `uv pip list --python <venv>/bin/python`, and pass/fail. No `--cov*` flags.

**Nothing else in this cycle owes code.** Every other divergence found is spec-side and belongs to Slice 2.

### Implementation discretion items

- The exact test-function name, docstring wording, and whether the four assertions live in one test or two (one per override direction). Both shapes are valid; the surrounding block uses one-behavior-per-test, so two is the likelier fit — Worker 2's call.
- Whether `fields=` is passed to `_make_path_optin_type` explicitly or left at its default four-column tuple.

### Test additions / updates

One new test (or two, per the discretion item) in `tests/types/test_base.py`. **No production `.py` change is planned or authorized by this slice.** No temp/scratch tests are needed — the fixture surface already exists.

---

### Notes for Worker 1 (spec reconciliation)

Slice 0 recorded **N1-N7**; they stand unchanged and are **not** restated. This pass adds **N8-N16**. Worker 0's D1-D8 are given.

- **N8. The `path`-as-a-default-subfield claim has 17 lines / 18 code-span occurrences, and they are NOT uniform.** Measured: `grep -c '`path`'` → 17 lines; `grep -o '`path`' | wc -l` → 18 occurrences. Worker 0's D1 said "roughly twenty sites… several unaffected". Re-derived line by line, they fall into three classes, and Slice 2 must grade each rather than sweep:
  - **False at `HEAD` — `path` named as one of the default subfields:** spec:9, :118, :567, :575, :673, :797, :909, :1393 (8 sites).
  - **False as written but true if re-homed on the opt-in siblings:** spec:494, :542, :1158, :1241 (4 sites) — these describe a selection or a guarantee that now belongs to `DjangoFilePathType` / `DjangoImagePathType`.
  - **Still true unqualified:** spec:294, :764, :847, :1245 (4 sites) — the per-subfield-isolation and `FieldFile`-raises statements, which hold on the opt-in types and are what `tests/types/test_resolvers.py::test_per_subfield_guard_isolates_storage_failure` still pins. One further site (spec:400) is `## Problem statement` prose. Note the spec contains **zero** occurrences of `DjangoFilePathType` and **zero** of `filesystem_path_fields`, so the replacement vocabulary is entirely net-new to the file.
- **N9. The three-parameter `convert_field_output` signature is quoted at two sites and implied at a third.** spec:244 (Slice-1 sub-check) and spec:827 (Decision 3 body) both write `convert_field_output(field, type_name, *, force_nullable=None)`; `HEAD` is `(field, type_name, *, force_nullable=None, expose_filesystem_path=False)`. DoD item 2 (spec:1393-1400) names the wrapper without a signature and needs no edit for this reason alone. `grep -o 'convert_field_output' <spec> | wc -l` → 8 occurrences total.
- **N10. `## Edge cases`' final bullet is a SECOND site for Worker 0's D4.** spec:1221-1223: "`DEFERRED_META_KEYS` / `ALLOWED_META_KEYS` are **byte-unchanged**". False at `HEAD` — `filesystem_path_fields` sits in `ALLOWED_META_KEYS` (`types/base.py:77`). Worker 0's D4 named only Decision 8's title and body (spec:1030-1034). Fixing Decision 8 alone is the partial claim fix this corpus keeps re-learning.
- **N11. Decision 7's "three net-new root-exported symbols" is true of the card and false of the surface.** Five file/image-related symbols are root-exported at `HEAD`. The heading itself (spec:1017) carries the count, so the fix touches a heading — check its in-page anchor before renaming (Slice 0 hit exactly this hazard).
- **N12. The Slice-2 `scalars.py` sub-check (spec:307-308) asks for a staged anchor the shipped code correctly has none of.** It says to "fix the stale `TODO-ALPHA-035-0.0.11` reference in the module docstring to `TODO-ALPHA-037-0.0.11`". `HEAD`'s `scalars.py` carries **zero** `TODO`s, and `TODO-ALPHA-035` has zero occurrences across `django_strawberry_framework/`, `tests/`, `examples/`, `scripts/`. Removal is what `BUILD.md` `## Cross-slice integration pass` step 6 requires once the seam ships — the sub-check as written would today create a finding. Rewrite it to "remove the stale `TODO-ALPHA-035-0.0.11` docstring reference; the seam ships in this slice so no anchor replaces it."
- **N13. `## Test plan`'s converter bullet mis-homes the `Meta`-level requirement, and that mis-homing is why this cycle found a gap.** spec:1236-1238 puts "`Meta.nullable_overrides` / `Meta.required_overrides` still win" inside the `tests/types/test_converters.py` bullet — but that file tests `convert_field_output`, whose parameter is `force_nullable`; `Meta` never reaches it. Slice 2 should split the clause: the `force_nullable` half stays on `tests/types/test_converters.py`, the `Meta.*_overrides` half moves to `tests/types/test_base.py`, which is where this cycle's fix lands. **This is the highest-value spec edit in the reconciliation** — it is the sentence that, written correctly, would have prevented the gap.
- **N14. The same bullet spells the filter-input pin two different ways from the Slice-1 sub-check.** `## Test plan` (spec:1239-1241) asks for "a `FilterSet` over a synthetic `FileField`"; the Slice-1 sub-check (spec:284-291) narrows it to the delegation path *because* django_filter raises on a bare-`FileField` auto filter before package code runs. The narrowed form is what shipped and is correct. Reconcile the `## Test plan` bullet to the delegation spelling; do not "restore" the `FilterSet` form.
- **N15. `## Edge cases`' multipart bullet (spec:1211-1214) is in a falsified future tense.** "consumers use Strawberry/Django's existing multipart request handling until the `0.0.14` `TestClient` helper lands" — it landed (spec-043), and `examples/fakeshop/test_query/test_uploads_api.py` imports and drives it. Same class as Slice 0's N5 hedges. Related: `## Out of scope`' first bullet (spec:1357-1359) calls `TestClient` `TODO-ALPHA-043-0.0.14`, a card id that is now `DONE`.
- **N16. Decision 2 survives intact and should be left alone.** Every clause of its boundary still holds at `HEAD` (see the D-2 row). It is the one Decision in this spec that needs no Slice-2 edit, and saying so explicitly is cheaper than a future pass re-deriving it.
- **Not a finding, do not re-raise.** (a) `__version__ == "0.0.15"` while this card cut `0.0.11` — settled by the plan's `## Worker-0 verification pass`. (b) No file-column-specific read-side `Meta.exclude` test — `Meta.exclude` is name-keyed with no file branch in `types/base.py::_select_fields`, and the write side is pinned; **Low**, deliberately not planned. (c) `types/finalizer.py` is dirty with a concurrent session's model-mismatch error work — recorded above, out of scope by `AGENTS.md` rule 34, and it does not touch the file-resolver call site.

---

## Build report (Worker 2)

### Files touched

Grounded in `git status --short` after both ruff invocations, not memory. **Exactly one tracked file in the whole tree changed under this pass:**

- `tests/types/test_base.py` — three new tests appended to the end of the `# Consumer file/image override (spec-037 Decision 3)` block (immediately after `::_make_file_override_model_type`, before the `# Meta.filesystem_path_fields (spec-048 Decision 2)` header), plus a four-line comment naming why they reach forward to the next block's fixtures. **No production `.py` file changed** — this slice authorized none, and none was needed.
- `docs/builder/temp-tests/037/proofs.json` (+ the tool's `proofs.md` beside it) — the failability manifest, scratch per `BUILD.md` `### Mechanized: scripts/prove_failability.py`; cleared per cycle by `scripts/clean_up.py`.
- `docs/builder/bld-037-slice-1-code_conformance.md` — this section, the three `### Fix checklist` ticks, and `Status: built`.
- `docs/builder/worker-memory/worker-2.md` — appended entry.

**Baseline state of the file I own, confirmed before editing.** `tests/types/test_base.py` was **byte-identical to `HEAD`** at pass start, so it is *not* one of the ~103 baseline-dirty paths and every byte now in its diff is this pass's. Measured with a HEAD-blob byte compare, never `git stash` / `git checkout`:

```shell
for p in tests/types/test_base.py django_strawberry_framework/types/converters.py; do
  git show HEAD:$p > /tmp/dsf-base-$(echo $p | tr '/' '_')
  cmp -s /tmp/dsf-base-$(echo $p | tr '/' '_') $p && echo "SAME  $p" || echo "DIFF  $p"
done
```

```text
SAME  tests/types/test_base.py
SAME  django_strawberry_framework/types/converters.py
```

`django_strawberry_framework/types/converters.py` — the failability-proof target — was **also clean at baseline**, which is the precondition the dispatch required before proving against it. It is clean again now (see `### Failability proofs`).

### Tests added or updated

Three added, none updated. All reuse `tests/types/test_base.py::_make_path_optin_model` and `::_make_path_optin_type` verbatim; **no new model factory and no new type factory was introduced**, per the plan's `### DRY analysis` (which rejected a fourth `(model, *, namespace, **meta_attrs)` builder outright).

- `tests/types/test_base.py::test_meta_required_overrides_forces_non_null_file_output` — pins `Meta.required_overrides = ("attachment",)` on a `FileField` → `__annotations__["attachment"] is DjangoFileType`, the **bare** object. This is the end-to-end `Meta` → `types/base.py::_build_annotations` (`force_nullable=False`) → `types/converters.py::convert_field_output` #"file_effective_null = True if force_nullable is None else force_nullable" path that nothing pinned at `HEAD`. **Carries the control** in the same type and the same row: `preview`, an `ImageField` **not** named in the override, still `== (DjangoImageType | None)`.
- `tests/types/test_base.py::test_meta_required_overrides_forces_non_null_image_output` — the same override on the `ImageField` → `preview is DjangoImageType`, proving the branch is not `FileField`-only. **Control mirrored:** the unnamed `attachment` stays `== (DjangoFileType | None)`.
- `tests/types/test_base.py::test_meta_nullable_overrides_on_a_file_column_is_a_no_op` — `Meta.nullable_overrides = ("attachment",)` on an already-nullable file column stays `== (DjangoFileType | None)`; the redundant-declaration direction, matching `::test_override_redundant_is_no_op`'s shape for scalars.

Between them the three cover all four assertions the `### Fix checklist` item 1 enumerated. Every one asserts `__annotations__`, not SDL; `finalize_django_types()` is called only to match the surrounding block and to keep the synthetic types from leaking unfinalized into the registry for later rows.

### Validation run

- `uv run ruff format tests/types/test_base.py` — pass (`1 file left unchanged`). Scoped to the one file this pass touched; **never `.`**, which would have rewritten ~55 concurrently-dirty package files.
- `uv run ruff check --fix tests/types/test_base.py` — pass (`All checks passed!`, 0 fixes).
- `uv run python scripts/check_trailing_commas.py tests/types/test_base.py` — pass (`Fixed 0 file(s)`, exit 0). Trailing-comma / brace-explosion layout and ASCII-only, which ruff does not own.
- `git status --short` after both ruff invocations — `tests/types/test_base.py` is the **only** entry attributable to this pass. Every other ` M` / `??` row is the ~103-path baseline-dirty population the build plan enumerates (a concurrent session's work): not edited, not reverted, not staged (`AGENTS.md` rule 34). Nothing unexpected appeared, so there is no stop-and-report.
- Focused runs, all **without** any `--cov*` flag (`--no-cov` throughout, required because `pytest.ini`'s `addopts` auto-applies `--cov`):
  - `uv run pytest <the three new node ids> --no-cov -q` → **3 passed**.
  - `uv run pytest tests/types/test_base.py --no-cov` → **170 passed** (this doubles as the failability proof's pre-mutation baseline, below).
  - `uv run pytest tests/types/ --no-cov -q` → **536 passed, 2 skipped**. Run because this pass adds three more classes named `PathOptInType` to a module that already builds several, and registry-name collisions in this repo are order-dependent and invisible to a single-node run. No pollution.

**Test-staleness sweep: not owed, and why.** `BUILD.md` `### Test staleness a focused run cannot see` triggers on a changed model field set or a changed wire shape. This pass changes neither — it adds three test functions over synthetic in-test models and touches no production module, no example model, and no field/connection envelope. Stated rather than silently skipped.

### Failability proofs

Performed with `uv run python scripts/prove_failability.py docs/builder/temp-tests/037/proofs.json --output docs/builder/temp-tests/037/proofs.md` — the supported mechanization, which enforces the loop's order and refuses the shortcuts. **Exit code 0.** `git` was never invoked by the tool for the mutation, the restore, or the proof.

The anchor check ran **first and separately** (`--check-anchors-only`, exit 0, `anchor matches exactly once`) before any copy was taken, so a live prior mutation could not have been copied as the pristine reference. Independently: `grep -c '    file_effective_null = True if force_nullable is None else force_nullable' django_strawberry_framework/types/converters.py` → `1`. The scratch root is `/private/tmp/dsf-failability-037` — **outside the repository**, not `docs/builder/temp-tests/`.

- `django_strawberry_framework/types/converters.py::convert_field_output` — **mutation applied:** `    file_effective_null = True if force_nullable is None else force_nullable` → `    file_effective_null = True`, so the file/image branch ignores `force_nullable` entirely and `Meta.required_overrides` (`force_nullable=False`) can no longer make a file/image output object non-null. This removes the boundary rather than perturbing code near it. **Scope as run:** `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/types/test_base.py`. **Pre-mutation state of that same scope:** green — `170 passed in 1.51s`, pytest exit code 0, **0 pre-existing failing rows differenced out**. **Failing node ids (the count is `len()` of this list, = 2):**
  - `tests/types/test_base.py::test_meta_required_overrides_forces_non_null_file_output`
  - `tests/types/test_base.py::test_meta_required_overrides_forces_non_null_image_output`

  **Collection / setup errors: 0** (recorded separately; mutant run `2 failed, 168 passed`, pytest exit code 1 — inside the valid `{0, 1}` band, so the count is a valid count). **Revert proved by byte comparison:** the tool's own `filecmp.cmp(shallow=False)` → `True` plus `sha256 581dfd7d8b480e2e… == 581dfd7d8b480e2e…` against the pre-mutation copy. Independently re-proved after the run against the `HEAD` blob, since this file was clean at baseline: `git show HEAD:django_strawberry_framework/types/converters.py > /tmp/dsf-conv-head.py && cmp /tmp/dsf-conv-head.py django_strawberry_framework/types/converters.py` → exit 0, byte-identical. `git checkout -- <path>` was **not** used. No `ACTIVE-MUTATION.json` remains in the scratch root; only `pristine/`.

**Not weakly pinned.** 2 rows > the 0-or-1 threshold, so no `revision-needed` on this ground and no zero-row `why 0` slot to fill. 2 rows *is* inside Worker 3's mandatory independent re-run floor (3 or fewer) — the tool says so explicitly, and Worker 3 should re-run at **exactly the scope recorded above** and compare node-id sets, not numbers.

**Why the third test is not in the failing set, stated so its absence is not read as a gap.** The mutation forces the file branch permanently nullable, which is what `::test_meta_nullable_overrides_on_a_file_column_is_a_no_op` already asserts, so it cannot fail under *this* mutation. It pins the opposite direction and is failable under the inverse mutation (a literal `False`); it is deliberately not the subject of this proof, whose boundary is the `force_nullable` honouring itself.

### Hot-path budget

`Not applicable; plan declares no hot path.` Copied from the plan as written — the change is a test and adds no runtime code, no per-request or per-resolver work, no lock and no serialization point.

### Floor verification

Owned by this pass per the plan's `### Floor-verification scope (re-declared)`. Built outside the repo with an explicit `--python`, per `BUILD.md` `### How to build the floor venv`; the shared `.venv` was **not** mutated.

- **Scratch venv:** `/tmp/dsf-floor-037` (outside the working tree; no `.gitignore` entry needed).
- **Build commands:** `uv venv /tmp/dsf-floor-037 --python 3.10`; `uv pip install --python /tmp/dsf-floor-037/bin/python -e . --group dev`; `uv pip install --python /tmp/dsf-floor-037/bin/python 'django==5.2.16' 'strawberry-graphql==0.316.0'` (the floor point read from `BUILD.md` `## Floor verification`, its single canonical statement — not restated from memory or from a number written elsewhere).
- **Resolved versions, as read by `uv pip list --python /tmp/dsf-floor-037/bin/python`:** `django 5.2.16`, `strawberry-graphql 0.316.0`, `django-filter 26.1`, `djangorestframework 3.18.0`, `channels 4.3.2`, `pytest 9.1.1`, `pytest-django 4.14.0`; interpreter `Python 3.10.19` (`/tmp/dsf-floor-037/bin/python -V`). The second install step downgraded `django 5.2.17 -> 5.2.16` and `strawberry-graphql 0.327.1 -> 0.316.0`, confirming the pin took.
- **Shared `.venv` unmutated, verified rather than asserted:** `.venv/bin/python -c "import django, sys; ..."` still reports **Django 6.1 on Python 3.14.2** after every install above. Had `--python` leaked, that reading would have moved.
- **Focused scope run:** `/tmp/dsf-floor-037/bin/python -m pytest tests/types/test_base.py::test_meta_required_overrides_forces_non_null_file_output ::test_meta_required_overrides_forces_non_null_image_output ::test_meta_nullable_overrides_on_a_file_column_is_a_no_op ::test_consumer_annotation_override_on_file_column_keeps_str_and_no_resolver ::test_no_override_file_column_gets_generated_resolver ::test_consumer_assigned_field_resolver_on_file_column_is_not_clobbered --no-cov -q` (the three new node ids plus the existing spec-037 file-override block, exactly the re-declared scope; node ids given in full on the command line).
- **Result: PASS — `6 passed in 1.30s`**, session header confirming `Python 3.10.19` / `django: version: 5.2.16`. No `--cov*` flag.

### Implementation notes

- **Three tests, not one or two.** The plan left the count to discretion and predicted two. Three is what the four required assertions decompose into once the control is taken seriously: each `required_overrides` direction needs its *own* type so the unnamed sibling in that same type is a real control, and building two types inside one test would have put two same-named `PathOptInType` classes through the registry in one row for no gain. The surrounding block is one-behaviour-per-test throughout; three matches it.
- **`fields=` left at the factory default.** `_make_path_optin_type`'s default `("id", "attachment", "preview", "title")` is exactly the four columns these tests need — the file column, the image column, the scalar, and the pk — so passing `fields=` explicitly would have restated the default. (The plan's second discretion item.)
- **`is` for the bare object, `==` for the union.** `DjangoFileType | None` is a `types.UnionType` and compares by equality, not identity; the bare non-null case is a class and `is` is the assertion that cannot be satisfied by a coincidentally-equal union. Mirrors `::test_override_redundant_is_no_op`, which already uses both spellings for the same reason.
- **Placement follows the plan literally, with one added comment.** The tests sit in the spec-037 Decision 3 block as instructed, while `_make_path_optin_model` / `_make_path_optin_type` are defined in the spec-048 block *below* them. Python resolves module-level names at call time, so this works — but it reads as an error to someone scanning top-down, so a four-line comment above the tests names the fixtures and says why that pair specifically (it is the only fixture model carrying a file column, an image column and a scalar together, and a per-column override is meaningless without an unnamed sibling). No process provenance in it: it states the invariant, not how the tests came to be here.
- **No production change was needed or made.** Worker 1's read-only probe held: the `Meta` → `force_nullable` → file-branch threading already works at `HEAD`, and the three tests pass against unmodified production code. Nothing in this pass came close to the plan-level architectural call that would have forced `Status: revision-needed`.

### Notes for Worker 3

- **Re-run scope for the independent failability check:** `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/types/test_base.py`, the scope recorded above verbatim. At 2 rows this boundary is inside your mandatory re-run floor. The manifest is committed-in-scratch at `docs/builder/temp-tests/037/proofs.json` and re-runs the whole loop with `uv run python scripts/prove_failability.py docs/builder/temp-tests/037/proofs.json`; the tool's own report is beside it at `proofs.md`.
- **`django_strawberry_framework/types/converters.py` is byte-identical to `HEAD` right now.** If you find it otherwise, that is either a concurrent session's edit or an unreverted mutation — check `/private/tmp/dsf-failability-037/ACTIVE-MUTATION.json` first (absent as of this writing; only `pristine/` remains).
- **The whole tree except `tests/types/test_base.py` is out of scope for this diff.** ~103 tracked paths are baseline-dirty with a concurrent session's work, including `docs/SPECS/spec-037-…md` itself. None was edited or reverted by this pass. Read the diff as `git diff HEAD -- tests/types/test_base.py`, not as `git status`.
- **No shadow file and no `scripts/review_inspect.py` run was used in this pass.** Nothing to cross-reference.
- **The third test's absence from the failing set is explained above, not an oversight** — it pins the inverse direction and is failable only under the inverse mutation.

### Notes for Worker 1 (spec reconciliation)

**No new N-items.** Nothing this pass touched surfaced a spec gap beyond the N8-N16 the plan already routed to Slice 2, and no plan-vs-implementation drift occurred: the plan's fixture reuse, its no-new-helper call, its assertion list and its zero-production-change boundary all held exactly as written. The three-tests-instead-of-two shape is an `### Implementation discretion items` choice the plan explicitly delegated, not drift.

One thing worth carrying into Slice 2's N13 edit, as confirmation rather than a new finding: N13 predicted that moving the `Meta.*_overrides` half of `## Test plan`'s converter bullet onto `tests/types/test_base.py` is where the fix lands. It is — all three tests landed in `tests/types/test_base.py`, and the failability proof shows the pin reaching `types/converters.py::convert_field_output` from there. N13's recommended replacement can be written with the node ids above as its citation.

---

## Final verification (Worker 1) — planning-pass placeholder, superseded

**This heading is the planning spawn's deferral note, kept as the record of what that pass owed and to whom. The authoritative final verification is the `## Final verification (Worker 1)` section at the end of this file**, written after `review-accepted`. Everything below in this placeholder describes the pass that wrote it, not the closeout.

Deferred. This slice is `Status: planned`, not a procedural closure: the `Meta.required_overrides` test gap is a real Medium that owes a diff, so Worker 0 dispatches Worker 2 (build) and Worker 3 (review), and Worker 1 returns for final verification. Procedural closure (`BUILD.md` `### Procedural-closure slices`) was considered and **rejected** — it applies only when the slice ships nothing, and this one ships a test.

### Failability proofs

`None; this planning pass introduced no new boundary.` The proofs this slice owes are assigned in `### Fix checklist` item 2 and belong to the Worker 2 build pass. The proof obligations this **planning** pass carried are the conformance measurements above, each with its command and real output quoted; the `Meta.required_overrides` verdict's control is the probe's second half (a sibling column *not* named in the override resolving to `… | None`), which is what makes the first half mean "the override did it".

### Hot-path budget

`Not applicable; plan declares no hot path.`

### Floor verification

`Owned by the Worker 2 build pass per the re-declared scope above.` Not run in this pass.

### Spec changes made (Worker 1 only)

**None.** This pass edited no spec file. `docs/SPECS/spec-037-upload_file_image_mapping-0_0_11.md` and `docs/SPECS/appx/spec-037-upload_file_image_mapping-0_0_11-rationale.md` are **Slice 2's**; every divergence found here is routed there as N8-N16 rather than acted on. Proved by non-edit: both files are byte-identical to the state Slice 0 left them in, and `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-037-upload_file_image_mapping-0_0_11.md` still exits 0 with `OK: 20 terms`.

### Spec status-line re-verification (this spawn)

`worker-1.md` `## Spec status-line re-verification (every Worker 1 spawn)`. Read spec:1-20. The header names the card, the `0.0.11` target and the predecessor `spec-036`; it carries no "not yet shipped" / "remains to be" claim this build has falsified, and it references no predecessor doc this build deleted. **No edit owed this spawn.** Its one stale element — the `#"Upload staged seam (TODO-ALPHA-037-0.0.11)"` citation at spec:15, pointing at a seam that no longer exists in `mutations/inputs.py` — is a **contract-body** statement, not a status line, and is Slice 2's under N12's neighbourhood.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->

---

## Review (Worker 3)

### Independent failability re-run — mutations recorded BEFORE they were made

`worker-3.md` "Reading is necessary, not sufficient": Worker 2 recorded **2 failing rows**, inside the
mandatory floor (3 or fewer), so this re-run is not optional. Two mutations are recorded here in
advance, each applied and reverted one at a time (`BUILD.md` `### Mutations are transient`), the
scratch reference held at `/private/tmp/dsf-r3-037/` — **outside the repository**.

**Precondition, measured before either mutation:** `django_strawberry_framework/types/converters.py`
and `types/base.py` are both byte-identical to `HEAD`
(`git show HEAD:<path> > /tmp/dsf-r3-head-… && cmp` → exit 0 for both), so this proof is not being
run against a file a concurrent session is moving. The anchor
`grep -c '    file_effective_null = True if force_nullable is None else force_nullable' django_strawberry_framework/types/converters.py`
→ `1`, checked **before** the pristine copy was taken. `/private/tmp/dsf-failability-037/` holds no
`ACTIVE-MUTATION.json` (only `pristine/`), so no prior proof was left live.

- **Mutation A (Worker 2's, re-run verbatim at Worker 2's recorded scope).**
  `django_strawberry_framework/types/converters.py::convert_field_output`:
  `    file_effective_null = True if force_nullable is None else force_nullable` →
  `    file_effective_null = True`. The file/image branch then ignores `force_nullable` entirely, so
  the boundary — `Meta.required_overrides` reaching a non-null file output — is *removed*, not
  perturbed.
- **Mutation B (this review's own, to grade the third test).** Same line →
  `    file_effective_null = False`, the inverse direction. Its only purpose is to answer whether
  `::test_meta_nullable_overrides_on_a_file_column_is_a_no_op` is pinned by anything at all, and
  whether it is pinned by anything the pre-existing rows do not already pin.

Results are recorded under `### Failability re-run: results` below.

### Failability re-run: results

**Scope, verbatim as Worker 2 recorded it** (a wider scope would inflate the count and silently
shrink this mandatory subset): `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/types/test_base.py`.

**Pre-mutation state of that same scope:** green — `170 passed in 1.61s`, matching Worker 2's `170 passed`
row for row (`0` pre-existing failures to difference out, so no count here is inflated by one).

**Mutation A — node-id set beside Worker 2's. Identical, both members:**

| Node id | Worker 2 | This re-run |
| --- | --- | --- |
| `tests/types/test_base.py::test_meta_required_overrides_forces_non_null_file_output` | yes | yes |
| `tests/types/test_base.py::test_meta_required_overrides_forces_non_null_image_output` | yes | yes |

`2 failed, 168 passed` — `168 + 2 = 170`, the same 170 items collected, so **collection / setup errors: 0**
and the count is a valid count. `len()` of the set is **2**, above the weakly-pinned band `{0, 1}`, and
the two rows are the **right** two: they are precisely the rows asserting the bare non-null object,
and every row that does not depend on `force_nullable` reaching the file branch survives. Revert
proved by byte comparison, not prose: `cmp /private/tmp/dsf-r3-037/converters.orig django_strawberry_framework/types/converters.py`
→ exit 0, and independently `cmp /tmp/dsf-r3-head-…converters.py django_strawberry_framework/types/converters.py`
→ exit 0. `git checkout` / `git restore` / `git stash` were not used at any point.

**Mutation B — what it establishes about the third test, and about the control.** `file_effective_null = False`
(the inverse) fails **10** rows, `10 failed, 160 passed`, 0 collection errors:

- `::test_meta_required_overrides_forces_non_null_file_output`, `::test_meta_required_overrides_forces_non_null_image_output`
  — they fail here **on their control assertions**, since the mutant makes the *unnamed sibling* bare
  too. That is the decisive evidence for the review's second question: the controls are not
  decorative, they carry their own failability, and no mutation of this line leaves both halves of
  either test passing.
- `::test_meta_nullable_overrides_on_a_file_column_is_a_no_op` — so the third test **is** pinned by
  something; its absence from Mutation A's set is explained exactly as Worker 2 says, not by being
  unfailable. It is not a `### Harness-impossible interleavings` case.
- Seven pre-existing rows (`::test_filesystem_path_fields_swaps_only_the_named_columns`,
  `::test_filesystem_path_fields_absent_leaves_every_column_pathless`,
  `::test_filesystem_path_fields_opts_an_image_column_into_the_image_sibling`, and the four
  `::test_filesystem_path_fields_accepts_every_collection_literal[...]` cases) fail alongside it —
  which is the Low DRY finding below: the third test's *annotation-shape* assertion is subsumed by
  rows that shipped before this pass.

Revert re-proved by byte comparison after Mutation B as well: `cmp` against both the pristine copy and
the `HEAD` blob → exit 0 each. `django_strawberry_framework/types/converters.py` is byte-identical to
`HEAD` as this section is written, and `/private/tmp/dsf-r3-037/` holds only `converters.orig`.

**Where the second pair of eyes landed.** One boundary exists in this pass's proof set and it was
**re-run**, not accepted on the record: `types/converters.py::convert_field_output`'s
`force_nullable` honouring in the file/image branch. Nothing was accepted on Worker 2's record alone.

### High:

None.

### Medium:

None.

### Low:

#### The third test's annotation assertion is subsumed by a row that shipped before this pass

`tests/types/test_base.py::test_meta_nullable_overrides_on_a_file_column_is_a_no_op` asserts
`__annotations__["attachment"] == (DjangoFileType | None)` for a type declaring
`nullable_overrides=("attachment",)`. `::test_filesystem_path_fields_absent_leaves_every_column_pathless`
(same file, same fixture pair, no override at all) already asserts the identical annotation for the
identical column. Mutation B is the evidence: both fail together, and no mutation of
`convert_field_output`'s file branch can fail one without the other, because for a file column
`force_nullable=True` and `force_nullable=None` compute the same answer by construction.

What the row does still hold on its own is **not** the annotation but the *validator* accept-path:
it is the only row in the tree that puts a file/image column through
`types/base.py::_validate_nullability_override_targets` on the `nullable_overrides` side and expects
no `ConfigurationError`, which is the spec's `## Edge cases and constraints` "redundant declaration is
allowed" direction. That is a thin but real contract, and the test's own docstring frames it as the
annotation claim rather than the acceptance claim.

Recommended change (non-blocking, and **not** a deletion this review is empowered to order): keep the
row and make its load-bearing half explicit — say in the docstring that the distinguishing content is
that declaring the redundant override is *accepted*, the annotation half being the same default the
`filesystem_path_fields`-absent control already pins. Routed to Worker 1 below, because the assertion
was required verbatim by the Plan's `### Fix checklist` item 1 and dropping or re-aiming it is a
plan-level call, not Worker 2's.

### DRY findings

- **No new factory was introduced, as required — verified, not accepted on prose.** All three tests
  call `tests/types/test_base.py::_make_path_optin_model` and `::_make_path_optin_type`; the diff
  adds no `def _make_*`. `grep -c '^def _make_' tests/types/test_base.py` is unchanged from `HEAD`
  (the diff's only added top-level `def`s are the three `test_` functions). The plan's rejected
  fourth `(model, *, namespace, **meta_attrs)` builder did not sneak back in.
- **Tests 1 and 2 are structural mirrors, and parametrizing them would fight the file's own
  precedent — considered and rejected.** They differ only in which column is named and which
  output object is expected. The adjacent spec-048 block keeps exactly that file-vs-image pair as two
  separate rows (`::test_filesystem_path_fields_swaps_only_the_named_columns` /
  `::test_filesystem_path_fields_opts_an_image_column_into_the_image_sibling`), and the file reserves
  `@pytest.mark.parametrize` for a literal axis (collection spellings, key names) rather than for two
  distinct behaviours. Recording the rejection so the next reader does not re-fight it.
- **The existence challenge, asked and answered.** The unit adds no abstraction — no helper, no
  registry, no indirection — so there is nothing whose deletion could be the larger win; the only
  "should this exist at all" question in the diff is the third test, filed as the Low above.
- **The four-line comment above the tests is not duplication.** It names why the block reaches
  forward to the next block's fixtures. It states the invariant (that pair is the only fixture with a
  file column, an image column and a scalar together) and carries no process provenance — no worker
  name, round number, or review tag.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` → **empty**. `__all__` and the re-export list are
unchanged; this slice adds no public export, which is what its Definition-of-done position requires.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces. (The cycle's scope fence puts
those out of reach for every worker, and the diff respects it: one tracked file, `tests/types/test_base.py`.)

### Static inspection helper: decision recorded either way

**Not run, deliberately.** `BUILD.md` `### When to run the helper during build` triggers Worker 3 on a
new `.py` file (none), a file under `optimizer/` or `types/` **within the package** (`tests/types/` is
not `django_strawberry_framework/types/`), 30+ new logic lines inside the package (no package file
changed at all), or 50+ new logic lines outside it. The diff is +57 lines of which the executable
statements are 18 — three fixture calls, three `finalize_django_types()` calls, five `assert`s and
their bindings; the remaining 39 are docstrings, comments and blank lines. Below the threshold on the
only clause that could apply, so the helper's repeated-literal and control-flow output would have
nothing to say about this diff.

### What looks solid

- **The pin reaches the contract's own spelling, not one layer below it.** The gap Worker 1 proved was
  that `Meta.required_overrides` was pinned only at `convert_field_output(force_nullable=...)`. All
  three new rows go in through the public `Meta` surface (`_make_path_optin_type(model, required_overrides=…)`),
  so the assertion exercises `types/base.py::_build_annotations`' tri-state selection
  **and** `types/converters.py::convert_field_output`'s file branch as one path. Mutation A confirms
  the second half is genuinely on the path: removing it fails these rows and nothing else in the file.
- **The control is real in both directions and it is failable.** Each `required_overrides` direction
  gets its own type, and the sibling column in that same type is genuinely un-named in the override —
  `preview` in test 1, `attachment` in test 2. Neither sibling is `| None` for an incidental reason:
  the file branch ignores `null` / `blank` entirely, so the control's `| None` can only come from the
  absence of the override. Mutation B proves the controls carry weight rather than reading along.
- **`is` for the bare class, `==` for the union** is the right pair of spellings: `DjangoFileType | None`
  is a `types.UnionType` that compares by equality, so `is` on the non-null case cannot be satisfied
  by a coincidentally-equal union. It also matches `::test_override_redundant_is_no_op`'s existing use.
- **Failability record is complete and honest.** Anchor check before the copy, scratch path outside the
  repo (`/private/tmp/dsf-failability-037`), pre-mutation baseline at the same scope, node ids listed
  rather than counted, collection/setup errors called out as `0`, revert proved by `filecmp` + `sha256`
  and re-proved against the `HEAD` blob. The third test's absence from the failing set is explained
  *before* a reviewer can read it as a gap — and the explanation holds under measurement (Mutation B).
- **Floor run is verifiable later, and was verified now.** `/tmp/dsf-floor-037/bin/python -V` → `Python 3.10.19`;
  `uv pip list --python /tmp/dsf-floor-037/bin/python` → `django 5.2.16`, `strawberry-graphql 0.316.0` —
  the point `BUILD.md` `## Floor verification` names, read from that section and not restated from
  memory. Re-running the three new node ids in that venv: `3 passed in 1.16s`. The shared `.venv` is
  **unmutated** — it still reports `django 6.1` / `Python 3.14.2`, which a leaked `--python` would have moved.
- **Style and repo rules pass, scoped to the reviewed file.** `uv run ruff format --check tests/types/test_base.py`
  → `1 file already formatted`; `uv run ruff check tests/types/test_base.py` → `All checks passed!`;
  `uv run python scripts/check_trailing_commas.py --check tests/types/test_base.py` → exit `0`. Zero
  non-ASCII characters in the file; longest added line is under 99. Ruff was never run against `.`.

### Temp test verification

**None written.** The one thing a temp test could have demonstrated here — whether the third test's
assertion is distinguishing — was answered directly by Mutation B, which is stronger evidence than a
temp row would have been. `docs/builder/temp-tests/037/` was not written to by this review; Worker 2's
`proofs.json` / `proofs.md` were read, not modified.

### Test-staleness sweep, run independently

`worker-3.md`: the sweep is run independently, never against the slice's enumerated file list. Full
package tree: `uv run pytest tests/ --no-cov -q` → **4 failed, 6188 passed, 40 skipped**. Every one of
the four sits in the concurrent session's baseline-dirty population and none is reachable from this
diff:

- `tests/optimizer/test_walker.py::test_divergent_key_windows_shared_payload_uses_none_key` (`optimizer/walker.py` is ` M`)
- `tests/orders/test_inputs.py::test_ensure_field_specs_derives_the_unset_sentinel_from_the_family_declaration` (`orders/base.py`, `orders/sets.py` are ` M`)
- `tests/test_sets_mixins.py::test_permission_family_config_stays_on_each_set_class` (`sets_mixins.py` **and** the test file are ` M`)
- `tests/test_sets_mixins.py::test_filter_normalizer_honors_a_subclass_unset_sentinel_override` (same pair)

`tests/types/` is entirely green, including every row that builds a `PathOptInType` — so the three new
types introduce no registry-name pollution. Per `BUILD.md` `## Claims are proven mechanically, never
accepted on prose`, a failing row in a tree this dirty is **not worker-verifiable at `HEAD`**: it needs
a clean checkout, which no worker may produce here. Recorded and escalated below rather than
investigated, edited, or reverted (`AGENTS.md` rule 34).

### Notes for Worker 1 (spec reconciliation)

- **Escalated (maintainer / Worker 1 decision, not blocking):** the Low above —
  `::test_meta_nullable_overrides_on_a_file_column_is_a_no_op`'s annotation assertion duplicates
  `::test_filesystem_path_fields_absent_leaves_every_column_pathless`, proved by Mutation B failing
  both together and by the arithmetic that `force_nullable=True` and `force_nullable=None` are the same
  answer in the file branch. Resolution paths: **(a)** keep it and re-aim its docstring at the claim it
  uniquely holds (the redundant `nullable_overrides` declaration on a file column is *accepted* by
  `types/base.py::_validate_nullability_override_targets`); **(b)** keep it verbatim as the Plan wrote
  it, accepting the overlap as the price of stating the spec's redundant-declaration edge case in the
  block that owns the file branch; **(c)** drop it. The Plan's `### Fix checklist` item 1 required the
  assertion verbatim, so re-aiming or dropping it is a plan-level call — which is why this is a Low
  routed here and not a Medium held against Worker 2.
- **Escalated (needs a clean tree, which no worker has):** four package rows fail in the full `tests/`
  sweep, listed under `### Test-staleness sweep, run independently`. All four are in the concurrent
  session's dirty surface and none touches this diff, but only the maintainer can run a clean `HEAD`
  tree to confirm they are pre-existing rather than a regression that session is mid-way through.
  Flagging so the final gate's full sweep is not read as this build's failure.
- **Confirmation, not a new finding:** Worker 2's N13 note holds — the three rows landed in
  `tests/types/test_base.py`, and Mutation A demonstrates the pin reaching
  `types/converters.py::convert_field_output` from there. Slice 2's N13 rewrite can cite the two node
  ids in Mutation A's table as the replacement's evidence.
- **No new N-items.** Nothing in this diff surfaced a spec gap beyond N8-N16.

### Review outcome

`review-accepted`. The Plan's three `### Fix checklist` boxes each carry a landed contract: the
end-to-end `Meta` pin with a real, failable control in both directions (item 1); a failability proof
whose node-id set this review reproduced exactly at the recorded scope, with a byte-proved revert
(item 2); and a floor run recorded with its venv path, its resolved versions and its result, still
reproducible in that venv today (item 3). No High and no Medium finding. The single Low is a
subsumed assertion routed to Worker 1 with three resolution paths, not a defect in what shipped.

---

## Final verification (Worker 1)

Written after `review-accepted`, on a fresh spawn. Every number below was measured as it was written; nothing is inherited from the Plan, the Build report, or the Review. `git stash` / `git checkout` / `git restore` / `git worktree` were **not used at any point**, and no `--cov*` flag was passed to any run. This pass wrote exactly two files: this artifact and `docs/builder/worker-memory/worker-1.md`. It edited no `.py` file, no test, no spec.

### The diff this pass verified

```shell
git diff HEAD --stat -- tests/types/test_base.py
git diff HEAD -- tests/types/test_base.py | grep -c '^+[^+]'      # non-blank added lines
git diff HEAD -- tests/types/test_base.py | grep '^+def '
```

```text
 tests/types/test_base.py | 57 +++
 42
+def test_meta_required_overrides_forces_non_null_file_output():
+def test_meta_required_overrides_forces_non_null_image_output():
+def test_meta_nullable_overrides_on_a_file_column_is_a_no_op():
```

57 insertions, 42 of them non-blank, 3 added top-level `def`s — all three `test_`. **Zero added `def _make_`**; `grep -c '^def _make_'` is `6` against the `HEAD` blob and `6` in the working copy, so the Plan's rejected fourth factory did not appear. `django_strawberry_framework/types/converters.py` and `types/base.py` are both **byte-identical to `HEAD`** right now (`git show HEAD:<path>` into a scratch path outside the repo, then `cmp` → exit 0 for both), so no production code changed and no failability mutation was left live. `/private/tmp/dsf-failability-037/` holds only `pristine/` and `/private/tmp/dsf-r3-037/` only `converters.orig` — no `ACTIVE-MUTATION.json` anywhere.

### Fix-checklist tick audit

`BUILD.md` `### Dispatched findings checklist` discipline, which the Plan applied in the `### Spec slice checklist (verbatim)` position. The list carries **3 boxes, every one ticked, and a checkbox grep over this artifact finds exactly those 3 and no un-ticked box** — so nothing owes a deferral reason. (The grep pattern itself is deliberately not written out here: an un-ticked-box literal in prose is indistinguishable from a real one to the next audit's sweep.) Each tick was audited against the diff, not against the Build report's prose.

| Box | Contract as the Plan wrote it | Landed? | Evidence |
| --- | --- | --- | --- |
| 1 | `Meta.required_overrides` on a `FileField` → `__annotations__["attachment"] is DjangoFileType` (bare) | **yes** | `test_base.py:2194` |
| 1 | Same override on the `ImageField` → `is DjangoImageType`, proving the branch is not `FileField`-only | **yes** | `test_base.py:2208` |
| 1 | A sibling file/image column **not** named in the override, in the same type, still `== (… \| None)` — the control | **yes** | `test_base.py:2195` (`preview`), `test_base.py:2209` (`attachment`), mirrored so each direction's control is a different column |
| 1 | `Meta.nullable_overrides` on a file column stays `DjangoFileType \| None` | **yes** | `test_base.py:2224` |
| 1 | Reuse `::_make_path_optin_model` / `::_make_path_optin_type`, **no new model or type factory** | **yes** | all three call the pair; added-`_make_` count is 0, total unchanged 6 → 6 |
| 1 | Assert `__annotations__`, not SDL — no schema build | **yes** | no `execute` / `strawberry.Schema` / SDL string in the diff; the only non-assert calls are the two factories and `finalize_django_types()` |
| 1 | Placement: inside the `# Consumer file/image override (spec-037 Decision 3)` block, after `::test_consumer_assigned_field_resolver_on_file_column_is_not_clobbered` | **yes** | that test is `test_base.py:2136`; the three new rows are `:2176`, `:2198`, `:2212`; the `# Meta.filesystem_path_fields (spec-048 Decision 2)` header that closes the block is `:2227` |
| 2 | Failability proof: mutate the file branch to ignore `force_nullable`, record node ids, revert, prove the revert by byte comparison | **yes** | record complete against `BUILD.md` `### What gets recorded` — see below |
| 3 | Floor run in an isolated venv outside the repo, venv path + resolved versions + result recorded, no `--cov*` | **yes** | record complete and still reproducible — see below |

**No over-tick and no under-tick. No box needed un-ticking, none needed ticking, and nothing is deferred.** Three additional Plan-level requirements that are not their own boxes also held: the test name in box 1 (`test_meta_required_overrides_forces_non_null_file_output`) is the name that shipped, and both `### Implementation discretion items` were exercised inside the discretion the Plan granted (three tests rather than the predicted two; `fields=` left at the factory default).

**Failability record, audited field by field** against `BUILD.md` `### What gets recorded`: boundary by symbol-qualified path (`types/converters.py::convert_field_output`) ✔; exact mutation, and it *removes* the boundary rather than perturbing it (the `file_effective_null` expression → a literal `True`) ✔; failing node ids **listed**, not counted, plus the focused scope as run ✔; collection / setup errors recorded **separately** as `0`, with `168 + 2 = 170` arithmetic making that auditable ✔; pre-mutation state of that same scope recorded as green with `0` pre-existing failures differenced out ✔; revert proved by byte comparison (`filecmp` + `sha256`, re-proved against the `HEAD` blob) ✔; no zero-row result, so no `why 0` slot is owed ✔. Two rows is above the weakly-pinned band `{0, 1}` and inside Worker 3's mandatory re-run floor, and Worker 3 did re-run it at the recorded scope and compared **node-id sets**, not numbers. The record exists, is complete, and is the strongest form the mechanism asks for.

**Floor record, audited and re-read rather than re-run** (the dispatch scopes this pass to confirming the record). The venv is still on disk and still carries what the Build report says: `/tmp/dsf-floor-037/bin/python -V` → `Python 3.10.19`; `uv pip list --python /tmp/dsf-floor-037/bin/python` → `django 5.2.16`, `strawberry-graphql 0.316.0`. Those are the point `BUILD.md` `## Floor verification` names as canonical — read from that section in this pass, not restated from the Build report. The shared `.venv` is unmutated: `.venv/bin/python` still reports `django 6.1` on `Python 3.14.2`, which a leaked `--python` would have moved. The re-declared scope (three new node ids plus the existing spec-037 file-override block) matches what the Build report ran, and `BUILD.md` `### When it is required` genuinely covers it — the tests construct a `DjangoType` through `__init_subclass__` and read the annotations Strawberry consumes.

### Ruling on the Low finding: **accept as-is**, and one clause of the finding is refuted

Worker 3's Low, routed here because the Plan's box 1 required the assertion verbatim. Verified at source first, because a review's prescribed remediation is a hypothesis, never an instruction.

**Confirmed at source, exactly as far as Worker 3 scoped it.** `types/converters.py::convert_field_output` #"file_effective_null = True if force_nullable is None else force_nullable" computes the same answer for `force_nullable=True` and `force_nullable=None`, so within that expression a `nullable_overrides` file column is indistinguishable from an un-overridden one. And `::test_filesystem_path_fields_absent_leaves_every_column_pathless` (`test_base.py:2290-2297`) does assert the identical annotation for the identical column on the identical fixture — `default_type.__annotations__["attachment"] == (DjangoFileType | None)`. Both halves check out.

**Refuted, first clause: the assertion is not globally subsumed — it is subsumed only against mutations confined to the converter's file branch,** which is the scope Worker 3's own sentence claimed and the scope its Mutation B could see. A distinguishing mutation exists one layer up, in `types/base.py::_build_annotations` #"if field.name in nullable_overrides": flip that arm to `force_nullable = False`. The overridden column then resolves bare and `::test_meta_nullable_overrides_on_a_file_column_is_a_no_op` fails, while `::test_filesystem_path_fields_absent_leaves_every_column_pathless` — which declares no override at all, so it takes the `else: force_nullable = None` arm — still passes. Derived from the two sites read verbatim (`types/base.py:1931-1934`, `types/converters.py:552-553`), **not executed**: this pass may not write a `.py` file, and mutating one to settle a Low would be a worse trade than the finding. Sibling scalar rows would also catch that mutation, so the row is not the *unique* catcher — but "failable through a path the finding's mutation cannot reach" is a different and weaker claim than "subsumed", and the difference is what decides the ruling.

**Refuted, second clause: the docstring does state the accept-path claim.** Worker 3 wrote that "the test's own docstring frames it as the annotation claim rather than the acceptance claim". Its second paragraph reads `so naming it must neither raise nor widen it twice` — *neither raise* **is** the acceptance claim, stated in the same sentence as the annotation claim. The remediation Worker 3 recommended (path **(a)**, re-aim the docstring at the accept-path) would therefore be re-writing the docstring to say something it already says.

**Ruling: path (b), accept as-is, no code edit, no `revision-needed`.** The row holds a real and otherwise-unpinned contract — it is the **only** row in the tree that puts a file or image column through `types/base.py::_validate_nullability_override_targets` on the `nullable_overrides` accept path and expects no `ConfigurationError`. Measured, not assumed: `grep -rn 'nullable_overrides' tests/ examples/` returns **28 lines carrying 28 occurrences**; every one was opened, and the only other file-bearing fixture that reaches the validator's accept path is `::test_the_sibling_collection_keys_accept_a_frozenset_too` (`test_base.py:2423-2431`), whose target is `"title"`, a `TextField`. Dropping the row (**(c)**) would retire that pin for an overlap that costs three lines; re-aiming the docstring (**(a)**) would restate a sentence already present. The spec's `## Edge cases and constraints` redundant-declaration direction keeps its only file-branch witness, and the annotation assertion stays as the postcondition that makes "accepted" mean something more than "did not raise".

Recorded so the next reader does not re-open it: **the overlap with `::test_filesystem_path_fields_absent_leaves_every_column_pathless` is known, deliberate, and the price of stating the redundant-declaration edge case in the block that owns the file branch.** Worker 3 graded it Low and non-blocking, and that grade is correct.

### Escalation to the maintainer: four failing rows in the full package sweep

`BUILD.md` `## Claims are proven mechanically, never accepted on prose` — a failing test at `HEAD` is **not worker-verifiable at all**; reproducing it needs the whole tree at `HEAD`, and this tree is legitimately dirty with a concurrent session's work. Recording the claim plus the available evidence and escalating discharges the obligation. **This does not block `final-accepted` for this slice**, and the dependency is stated plainly rather than assumed away: *the maintainer's clean-tree run is what settles whether these four are pre-existing, and until it happens this slice is accepted on a tree that is not green.*

**The claim, re-measured independently in this pass** (not inherited from the Review):

```shell
uv run pytest tests/ --no-cov -q
```

```text
FAILED tests/optimizer/test_walker.py::test_divergent_key_windows_shared_payload_uses_none_key
FAILED tests/orders/test_inputs.py::test_ensure_field_specs_derives_the_unset_sentinel_from_the_family_declaration
FAILED tests/test_sets_mixins.py::test_permission_family_config_stays_on_each_set_class
FAILED tests/test_sets_mixins.py::test_filter_normalizer_honors_a_subclass_unset_sentinel_override
4 failed, 6188 passed, 40 skipped in 32.13s
```

Same four node ids as Worker 3's sweep, same totals.

**The control Worker 3 did not run, and the one measurement that makes "not reachable from this diff" a fact rather than an argument.** The same full sweep with this slice's three rows deselected:

```shell
uv run pytest tests/ --no-cov -q \
  --deselect tests/types/test_base.py::test_meta_required_overrides_forces_non_null_file_output \
  --deselect tests/types/test_base.py::test_meta_required_overrides_forces_non_null_image_output \
  --deselect tests/types/test_base.py::test_meta_nullable_overrides_on_a_file_column_is_a_no_op
```

```text
<the identical four FAILED lines>
4 failed, 6185 passed, 40 skipped in 21.12s
```

`6188 - 3 = 6185`, the failing set is byte-identical, and the failures survive the removal of everything this slice added. **This diff neither causes nor masks them** — which also closes the registry-name-pollution question this repo's history makes worth asking, since the three new types are the only new `PathOptInType` registrations in the tree.

**Evidence available to a worker, recorded because the verdict is not:**

- **Whether the failing test or its code is in this slice's diff:** no, on both counts. This slice's diff is one file, `tests/types/test_base.py`; the four rows live in `tests/optimizer/`, `tests/orders/` and `tests/test_sets_mixins.py`, and none of them imports anything this diff touches.
- **`HEAD` content obtained read-only** (`git show HEAD:<path>` into a scratch path outside the repo, then `cmp`): the four rows' production modules are all dirty — `optimizer/walker.py` `DIFF`, `orders/base.py` `DIFF`, `orders/sets.py` `DIFF`, `sets_mixins.py` `DIFF`. Two of the three failing test files are themselves clean (`tests/optimizer/test_walker.py` `SAME`, `tests/orders/test_inputs.py` `SAME`), so those rows are `HEAD` tests running against mid-flight production code.
- **The traceback names the seam:** `TypeError: ActiveInputPermissionAttrs.__init__() got an unexpected keyword argument 'unset_sentinel'`, raised from `dataclasses.replace`. `ActiveInputPermissionAttrs` is defined at `django_strawberry_framework/sets_mixins.py:400`, and `grep -c 'unset_sentinel'` over that file gives **7 at `HEAD`** and **5 in the working copy** — a field being removed or renamed while a `replace(...)` call still passes it. That is the signature of a concurrent session mid-refactor, not of a regression this build could have introduced.
- **What a worker still cannot say:** whether these four are green at a clean `HEAD`. Only the maintainer can run that tree. Not investigated, not edited, not reverted (`AGENTS.md` rule 34).

### The slice's contract, confirmed delivered

The gap this slice existed to close was that `Meta.required_overrides` — the contract `docs/GLOSSARY.md` publishes for a file/image column — was pinned only at `convert_field_output(force_nullable=...)`, one layer below its own spelling. It is now pinned end to end through the public `Meta` surface, with a real control:

- **The entry point is the contract's own.** All three rows build a `DjangoType` subclass through `_make_path_optin_type(model, required_overrides=…)`, i.e. through `__init_subclass__` and the `Meta` validator, not by calling the converter with a keyword.
- **The path is whole.** `types/base.py::_build_annotations` #"if field.name in nullable_overrides" computes the tri-state and hands it to `types/converters.py::convert_field_output`, whose file branch resolves it at #"file_effective_null = True if force_nullable is None else force_nullable". Mutation A shows the second half is genuinely on the path: removing it fails these rows and **only** these rows in a 170-row file.
- **The control is real and it is failable.** Each `required_overrides` direction has its own type and its own un-named sibling (`preview` in the file test, `attachment` in the image test), so a passing first assertion cannot be explained by "file columns are non-null". Mutation B fails both rows *on their control assertions*, which is what distinguishes a control from a decoration.
- **Both branches are covered**, so the behaviour is not `FileField`-only, and the redundant-declaration direction has its witness.

`uv run pytest tests/types/test_base.py --no-cov -q` in this pass → **170 passed in 3.42s**. Style gates re-run scoped to the one changed file, never against `.`: `ruff format --check` → `1 file already formatted`; `ruff check` → `All checks passed!`; `scripts/check_trailing_commas.py --check` → exit 0; non-ASCII characters in the file → **0**.

### DRY check across this slice and prior accepted slices

No new duplication. The slice adds no helper, no constant, no indirection and no fourth model/type factory (measured above: added-`_make_` count 0, total 6 → 6). Against Slice 0, which moved spec text and touched no code, there is no shared shape to collide with. The one genuine overlap in the diff is the third test's annotation assertion, graded above and deliberately kept. Worker 3's DRY findings — the rejected parametrization of tests 1 and 2, and the four-line fixture comment carrying no process provenance — were re-read against the diff and are accurate.

### Failability proofs

`None; this verification pass introduced no new boundary.` The slice's one proof belongs to the Worker 2 build pass, was re-run independently by Worker 3 at the recorded scope with an identical node-id set, and is audited field-by-field above. No fail-open shape landed: the diff contains no expression, guard, or default that could silently substitute a permissive answer — it is three test functions and five assertions over an unchanged code path.

### Hot-path budget

`Not applicable; plan declares no hot path.` Copied from the plan as written. The slice ships a test and adds no runtime code, no per-request or per-resolver work, no lock and no serialization point.

### Floor verification

Confirmed, not re-run, per the dispatch. `/tmp/dsf-floor-037` — `Python 3.10.19`, `django 5.2.16`, `strawberry-graphql 0.316.0`, matching `BUILD.md` `## Floor verification`'s canonical point; the recorded scope ran there green (`6 passed`), and the shared `.venv` is unmutated (`django 6.1` / `Python 3.14.2`). The declared scope has an owning pass that ran it, so the final gate's backstop has something to confirm rather than a claim to chase.

### Spec changes made (Worker 1 only)

**None.** Slice 2 owns every spec edit in this cycle, so nothing found in this pass was acted on; it is routed below instead. Proved by non-edit rather than asserted: `docs/SPECS/spec-037-upload_file_image_mapping-0_0_11.md` (`md5 51662b10dd4aa6c74800fa61a697c33e`, mtime `2026-09-01 20:17:40`) and `docs/SPECS/appx/spec-037-upload_file_image_mapping-0_0_11-rationale.md` (`md5 69e34ddc33b364ee31f55d34b39534ee`, mtime `2026-09-01 20:19:18`) both predate the Worker 2 build pass (`tests/types/test_base.py`, mtime `20:45:16`) and this pass entirely, and `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-037-upload_file_image_mapping-0_0_11.md` still exits 0 with `OK: 20 terms`. The build plan, `bld-037-slice-0-*.md`, `bld-003-final.md`, `BUILD.md` and the `worker-*.md` role files were likewise read and not written.

**No deferral reasons are owed**: every `### Fix checklist` box is ticked with its contract landed, and this artifact carries no un-ticked box.

### Spec status-line re-verification (this spawn)

`worker-1.md` `## Spec status-line re-verification (every Worker 1 spawn)`. Read spec:1-20 again in this spawn. The header states `Shipped in 0.0.11 (card DONE-037-0.0.11)` and names the predecessors `spec-036` and `spec-001`; `docs/SPECS/spec-036-mutations-0_0_11.md` exists on disk. It carries no "not yet shipped" / "remains to be" claim, and this build falsified nothing in it — the slice landed tests only. **No edit owed this spawn.** Its one stale element is unchanged from the planning spawn's reading: the `#"Upload staged seam (TODO-ALPHA-037-0.0.11)"` citation at spec:15 points at a seam with **0 occurrences** in `HEAD`'s `mutations/inputs.py`. That is a contract-body statement, not a status line, and stays Slice 2's under N12's neighbourhood.

### Notes for Worker 1 (spec reconciliation)

Slice 0 recorded **N1-N7**; the Slice-1 plan recorded **N8-N16**. All sixteen stand unchanged and are **not** restated. Workers 2 and 3 each recorded "no new N-items", and re-reading their sections against the diff confirms that. This pass adds two, both small and both Slice 2's:

- **N17. `## Edge cases and constraints`' redundant-declaration bullet now has a named witness — cite it.** The Slice-2 edit that touches that bullet should name `tests/types/test_base.py::test_meta_nullable_overrides_on_a_file_column_is_a_no_op` as its pin. It is the only row in the tree putting a file/image column through `types/base.py::_validate_nullability_override_targets` on the `nullable_overrides` accept path, and this cycle formally accepted the annotation-assertion overlap that comes with it (see the Low ruling above). Writing the citation into the spec is what stops a later DRY pass re-opening the deletion question from scratch.
- **N18. N13's replacement clause can now be written with node ids.** N13 is the highest-value edit in the reconciliation — `## Test plan`'s converter bullet (spec:1236-1238) mis-homes the `Meta.*_overrides` requirement on `tests/types/test_converters.py`, and that mis-homing is why the gap survived to this cycle. The three rows that discharge it are `tests/types/test_base.py::test_meta_required_overrides_forces_non_null_file_output`, `::test_meta_required_overrides_forces_non_null_image_output` and `::test_meta_nullable_overrides_on_a_file_column_is_a_no_op`. Slice 2 should cite them by node id rather than re-describing the requirement in prose, so the sentence and its pin cannot drift apart again.

**Not a finding, do not re-raise.** (a) The four failing rows in the full sweep — escalated to the maintainer above, out of every worker's reach, and proven not to originate in this diff. (b) The third test's annotation overlap — ruled on above; the decision is *keep*, and the reasoning is recorded so it need not be re-derived. (c) `types/finalizer.py` and the other ~103 baseline-dirty paths — concurrent work, recorded, never edited or reverted (`AGENTS.md` rule 34).

### Summary

Slice 1 asked whether the shipped code dropped, skipped, or deviated from anything `spec-037` planned. It graded 57 items and found **zero dropped features and zero deviations** — every divergence is a later card's deliberate change and belongs to Slice 2's spec edits. The single thing that owed code was a **test gap, not a behaviour gap**: `Meta.required_overrides` on a file or image column worked at `HEAD` but was pinned only at the converter seam one layer below the contract's own spelling. Three tests in `tests/types/test_base.py` now pin it end to end through the public `Meta` surface, in both the `FileField` and `ImageField` directions, each with a failable control, plus the redundant-`nullable_overrides` direction. No production code changed; no public surface changed; the floor run is green at Django 5.2.16 / Python 3.10.19 / strawberry-graphql 0.316.0.

**Final status: `final-accepted`.** All three `### Fix checklist` boxes are correctly ticked with their contracts landed; the one Low is ruled on as *keep as-is*, with the clause of the finding that overreached refuted at source; and the four failing rows in the full package sweep are recorded, measured, proven independent of this diff, and escalated to the maintainer as the only party who can run a clean `HEAD`.
