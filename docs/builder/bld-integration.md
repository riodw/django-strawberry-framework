# Build: Cross-slice integration pass — upload_file_image_mapping / 0.0.11 (037)

Spec reference: `docs/spec-037-upload_file_image_mapping-0_0_11.md`
Build plan: `docs/builder/build-037-upload_file_image_mapping-0_0_11.md`
Status: final-accepted

Cross-slice integration pass (Worker 1), run after all four in-spec slices reached
`final-accepted`. Produces the verdict that gates Worker 0's integration checkbox.
This is the planner/QA pass — it describes consolidation if any is warranted; it
does not edit source.

## Pre-write requirements (BUILD.md `## Cross-slice integration pass`, steps 1–5)

### 1. Every prior slice artifact read in slice order — DONE

- `docs/builder/bld-slice-1-read_output_objects.md` (`final-accepted`) — read output
  objects `DjangoFileType` / `DjangoImageType`, `_safe_file_attr` guard,
  `FIELD_OUTPUT_TYPE_MAP`, `convert_field_output`, `_field_output_type_for`,
  `base.py::_build_annotations` swap, `resolvers.py::_attach_file_resolvers` +
  `_make_file_resolver`, `finalizer.py` call. Pillow added as a dev-only dep.
- `docs/builder/bld-slice-2-write_upload_input.md` (`final-accepted`) — `scalars.py`
  `Upload` / `UploadDefinition` re-export (+ module `__all__`), `inputs.py`
  seam→`Upload` `elif` branch, `resolvers.py` verify-first (NO branch added, two TODO
  anchors removed). CR-6 merge-override carve-out lifted by ordering alone.
- `docs/builder/bld-slice-3-exports_coverage.md` (`final-accepted` after one
  label-only re-loop) — three root re-exports + `__all__` (+3, exactly), two
  genuine-gap hardening tests. Pass-1 Low (a test name overstating the `url` arm)
  fixed by a zero-risk rename in pass 2.
- `docs/builder/bld-slice-4-docs_version_cut.md` (`final-accepted` after one
  TREE.md re-loop) — `0.0.11` version quintet, GLOSSARY promotions, README /
  docs-README / GOAL / TODAY / CHANGELOG edits, DB card-close (`DONE-037-0.0.11`),
  three DB drift clusters reconciled UP. Pass-1 `revision-needed` (undischarged
  `docs/TREE.md` Slice-4 anchor) fixed in pass 2.

### 2. Static inspection helper run for every touched Python file — DONE

Refreshed every package shadow overview with
`python scripts/review_inspect.py --all --output-dir docs/shadow` (63 files written).
The eight package `.py` files this build touched all have current overviews under
`docs/shadow/`:

| File | Helper | Disposition |
| --- | --- | --- |
| `types/converters.py` | run (`--all`) | reviewed Imports + Repeated literals |
| `types/base.py` | run (`--all`) | reviewed Imports + Repeated literals |
| `types/resolvers.py` | run (`--all`) | reviewed Imports + Repeated literals |
| `types/finalizer.py` | run (`--all`) | reviewed Imports + Repeated literals |
| `mutations/inputs.py` | run (`--all`) | reviewed Imports + Repeated literals |
| `mutations/resolvers.py` | run (`--all`) | reviewed Imports + Repeated literals |
| `scalars.py` | run (`--all`) | reviewed Imports + Repeated literals |
| `__init__.py` | **skip** | pure re-export (import + `__all__` widening, zero logic) — recorded skip per BUILD.md "Worker 1/3 may skip the helper for pure re-exports". Surface verified directly via `__all__` introspection (§ Export surface). |

### 3. Repeated string literals compared across overviews — DONE (no cross-slice DRY candidate)

The build plan flagged the file/image subfield names (`name` / `path` / `size` /
`url` / `width` / `height`) and any `Upload` / error-message strings as the cross-slice
DRY watch-list. Walking every touched file's **Repeated string literals** section:

- **`converters.py`: None. `scalars.py`: None. `__init__.py`: None.** No repeated
  executable string literal in any of the three files the read-output objects, the
  scalar re-export, or the public surface live in.
- **No file/image subfield-name literal appears in ANY file's repeated-literals
  section.** This confirms the build-plan DRY anchor held: the subfield names exist
  **only** as the resolver method names on `DjangoFileType` / `DjangoImageType`
  (`name` direct; `path` / `size` / `url` / `width` / `height` via `_safe_file_attr`),
  Strawberry derives the GraphQL fields from those methods, and `DjangoImageType`
  *inherits* the four base subfields rather than re-declaring them — so there is no
  `("name","path","size","url")` tuple to keep in sync anywhere. `_safe_file_attr`
  receives each attr name as the literal argument at its single call site per resolver,
  never as a shared iterated tuple. Confirmed in source: one `_safe_file_attr`
  definition (`converters.py::_safe_file_attr`), five call sites, no name tuple.
- **No `Upload` string literal repeats.** `Upload` flows as a *symbol* (imported from
  `..scalars` into `inputs.py`, re-exported from `__init__.py`), never as a duplicated
  string. `inputs.py`'s repeated literals are pre-existing (`DjangoMutation for`,
  `many_to_many`) and untouched by this build's three-line `elif` branch.
- **No file/image error-message string.** The write side reuses the shipped
  `_explicit_null_error` guard verbatim (no new file-null message); the read side
  degrades to `None` (no message). Nothing new to dedupe.

The only multi-file *literal* this build introduced is the prose phrasing in the
standing docs (the read=object / filter-input=`str` / mutation-input=`Upload` split
sentence and the `PositiveBigIntegerField → BigInt` breaking-change precedent), which
Slice 4 deliberately anchored to one canonical wording reused verbatim across GLOSSARY
/ CHANGELOG / TODAY (Worker 3 / Worker 1 confirmed no drift). That is documentation
consistency, not a code DRY defect.

### 4. Imports compared across overviews — one-way dependency direction CONFIRMED

The standing P0 read/write split is an import-direction invariant. Walking the
**Imports** section of every touched file:

- **Read side (`types/`) is self-contained on its own map.** `base.py` imports
  `from .converters import convert_field_output` (the read-output wrapper).
  `resolvers.py` imports `from .converters import _field_output_type_for` (the shared
  MRO-walk helper) — intra-`types/`, one-directional (`converters.py` imports nothing
  from `resolvers.py`). `finalizer.py` imports `_attach_file_resolvers` from
  `.resolvers`. No `types/` file imports `Upload` or anything from `mutations/` for
  the file path.
- **Write side (`mutations/inputs.py`) imports ONLY the scalar surface — NOT the read
  output map/objects.** Its converter import is `from ..types.converters import
  convert_scalar, scalar_for_field` (the **scalar-only** helpers) and `from ..scalars
  import Upload`. It does **NOT** import `convert_field_output`, `FIELD_OUTPUT_TYPE_MAP`,
  `DjangoFileType`, or `DjangoImageType`. The read output objects never reach the
  mutation input path. (Verified by grep: those four symbols return nothing in
  `mutations/inputs.py`.)
- **The filter-input path is untouched and never sees the read-output map.**
  `filters/inputs.py::_scalar_from_model_field` imports ONLY `scalar_for_field`
  (function-local import) and never `convert_field_output` / `FIELD_OUTPUT_TYPE_MAP` /
  the output objects (verified by grep — zero references). The standing P0 read/write
  split (the filter-input path must NOT import `FIELD_OUTPUT_TYPE_MAP` / the output
  objects) holds end-to-end.
- No sibling started importing across the documented boundary. The eight files' import
  blocks are the expected shape; the only build-added import lines are
  `base.py`'s `convert_field_output` (was `convert_scalar`), `resolvers.py`'s
  `_field_output_type_for`, `finalizer.py`'s `_attach_file_resolvers`, `inputs.py`'s
  `Upload`, `scalars.py`'s `Upload, UploadDefinition`, and `__init__.py`'s three
  re-exports — every one one-directional and on the correct side of the split.

### 5. Deferred follow-ups from `What looks solid` / `DRY findings` / `Notes for Worker 1` — walked

Walked every accepted slice artifact's `### What looks solid`, `### DRY findings`, and
`### Notes for Worker 1 (spec reconciliation)` sections. The deferred / follow-up items
surfaced are all non-blocking and belong to the final-gate deferred catalog, not a
consolidation pass:

- **Slice 1:** Pillow added as a dev-only dependency (test infra; package source never
  imports it). No follow-up — accepted by Slice 1 final verification.
- **Slice 2:** verify-first held — no resolver branch added; nothing deferred. The
  `scalars.py` module-level `__all__` is the genuine module surface (Decision 5).
- **Slice 3:** the `url`-degradation arm of `_safe_file_attr` is exercised through the
  single shared catch via `.size`; a separate `url`-raising mock was *rejected* as
  over-coverage (one shared clause, already pinned). Not a deferred item — a
  considered-and-closed decision. The `ValueError`-no-file arm is structurally
  unreachable from a populated object (parent resolver returns `None` first) — correctly
  not contrived a test for.
- **Slice 4:** three pre-existing DB drift clusters reconciled UP (036 SpecDoc.url →
  `docs/SPECS/`; `djangomodelpermission` body synced; 037 card-body `034`/`028` → `036`).
  `DONE-037` card-body `planningState` renders "In progress" — precedent-consistent with
  `DONE-036`; flagged as an optional maintainer follow-up (a separate `planningState`
  pass that would also re-touch `DONE-036`), explicitly NOT a card-close defect.

None of these is a cross-slice DRY opportunity or defect. They are catalogued for the
final gate's `### Deferred work catalog`.

## Integration checks (BUILD.md)

### Duplicated helpers across slices — NONE

- **`_safe_file_attr` is the single subfield storage guard** (`converters.py`), one
  narrow `except (ValueError, OSError, NotImplementedError)`, five call sites. No second
  copy; the parent resolver (`resolvers.py::_make_file_resolver`) carries no `try/except`
  (object nullability only). The two other `except` clauses in `converters.py`
  (`ImportError` for the postgres ArrayField/HStoreField branches) are pre-existing and
  unrelated.
- **`_field_output_type_for` is the single `FIELD_OUTPUT_TYPE_MAP` MRO walk**
  (`converters.py`), shared by both readers — `convert_field_output` (same module) and
  `resolvers._attach_file_resolvers` (top-level import). Not copied into `resolvers.py`.
  It is a deliberate *sibling* of `scalar_for_field`'s `SCALAR_MAP` walk, not a duplicate:
  two distinct maps with distinct responsibilities (read-output objects vs. shared
  scalar/filter-input). Folding them would re-merge the two paths the P0 split exists to
  keep apart — correctly NOT consolidated.
- **`convert_field_output` is the single read-output wrapper**; `convert_scalar` /
  `scalar_for_field` stay scalar-only.
- **`_attach_file_resolvers` is the structural twin of `_attach_relation_resolvers`**
  (same `selected_fields` iteration, same `_name_resolver` stamp, same
  `strawberry.field(resolver=...)` attach), differing only in what it selects (file/image
  columns via `FIELD_OUTPUT_TYPE_MAP`) and the broader skip set
  (`consumer_authored_fields`). Reuse, not a parallel path.
- **Write side adds no helper.** The `inputs.py` file branch is a three-line `elif`
  producing the `(python_attr, graphql_name, annotation=Upload)` triple, falling through
  to the shipped requiredness / override-skip / `| None`-widening machinery — no parallel
  file-only logic, no second override skip, no second requiredness predicate. The resolver
  added zero code (verify-first).

### Inconsistent naming / error handling between slices — NONE

- Read degradation: empty file → whole-object `None` (parent); per-subfield storage
  failure → `None` subfield (narrow catch). Write rejection: explicit `null` on a
  `null=False` column → the shipped `_explicit_null_error` `FieldError` (reused, not
  re-implemented). Each side uses its own established mechanism consistently; neither
  invents a new error shape for file/image.
- `SuspiciousFileOperation` deliberately propagates on read (security signal, not nulled)
  — consistent with the spec's Decision 4 narrow-catch rationale and pinned by a test.
- Naming is consistent: `attachment` (not `attachment_id`) on both the read object field
  and the mutation input (file columns are scalar, not relation, on both sides).

### Repeated ORM/queryset patterns that should be centralized — NONE

This card adds no queryset planning — a file column is a scalar column, correctly not
relation-planned. The read resolver is a thin attribute wrapper; the write path reuses
the shipped `model(**attrs)` / `setattr` generic scalar-assignment path verbatim. No
new ORM pattern to centralize.

### Misplaced responsibilities between modules — NONE

Module ownership is clean and one-directional: `converters.py` owns the read-output map +
wrapper + the two output objects + the subfield guard; `base.py` calls the wrapper;
`resolvers.py` owns the parent file resolver + the attach helper; `finalizer.py` calls the
attach in the relation-resolver phase; `scalars.py` owns the `Upload` re-export;
`inputs.py` owns the write mapping; `__init__.py` owns the public surface. No
responsibility leaked across the read/write boundary.

### Missing or too-broad exports — EXACT (`__all__` +3, nothing more)

`__init__.py` `__all__` introspected: **23 entries** = the pre-build 20 + exactly
`DjangoFileType`, `DjangoImageType`, `Upload`, in true `sorted()` slots. `UploadDefinition`
is NOT root-exported (it stays module-only on `scalars.__all__`, sanctioned by Decision 5).
No existing export removed or reordered. The export surface matches Decision 7 exactly —
three net-new root-exported symbols, nothing more, nothing less.

### Repeated string literals / dict keys / tuple shapes across slices — NONE NEW

Covered in pre-write step 3: no file/image subfield-name literal, no `Upload` string
literal, no error-message literal repeats across files. The two output maps
(`SCALAR_MAP`, `FIELD_OUTPUT_TYPE_MAP`) are distinct dicts with distinct keys/values by
design — not a repeated dict shape to merge.

### Comments tell one coherent story — YES

- All `TODO(spec-037 ...)` staged anchors are discharged across the entire tree (package
  source, tests, and `docs/TREE.md`) — grep returns nothing. No half-removed anchor.
- The stale `TODO-ALPHA-035-0.0.11` reference in `scalars.py` is fixed to `037` (no `035`
  ref remains in the module).
- The read-output-vs-filter-input split rationale is documented coherently and
  consistently in `converters.py` (the `SCALAR_MAP` "stay `str` on purpose" comment, the
  `FIELD_OUTPUT_TYPE_MAP` block comment, the `convert_field_output` / `_field_output_type_for`
  docstrings) and in `finalizer.py` (the `consumer_authored_fields` broader-skip comment).
  The same split is told identically in the standing docs (GLOSSARY / CHANGELOG / TODAY /
  TREE) — Slice 4 anchored one canonical phrasing.

### P0 read/write split re-confirmed end-to-end — HOLDS

Verified directly in current source, not just from the artifacts:

- The read objects never reach the mutation input path: `mutations/inputs.py` imports only
  `Upload` (from `..scalars`) and the scalar-only `convert_scalar` / `scalar_for_field`;
  it does NOT reference `convert_field_output` / `FIELD_OUTPUT_TYPE_MAP` / `DjangoFileType`
  / `DjangoImageType`.
- `Upload` never reaches `FIELD_OUTPUT_TYPE_MAP`: `grep Upload types/converters.py` returns
  nothing; `FIELD_OUTPUT_TYPE_MAP` holds only `ImageField → DjangoImageType` /
  `FileField → DjangoFileType` (ImageField first for MRO precedence).
- `Upload` never enters `_PACKAGE_SCALAR_MAP`: it is `{BigInt: ...}` only (Decision 5).
- `SCALAR_MAP` file/image rows stay `str`: `models.FileField: str`, `models.ImageField: str`,
  unchanged — and the filter-input path (`filters/inputs.py::_scalar_from_model_field`)
  walks only `scalar_for_field` / `SCALAR_MAP`, never the read-output map.

## Verdict

### Summary

The four-slice build is **maximally DRY and internally consistent across slices**. The
DRY anchors the build plan pinned (single `_safe_file_attr` guard, single
`convert_field_output` wrapper, single `_field_output_type_for` MRO walk, `DjangoImageType`
inheriting the four base subfields, no parallel file-resolver attach path, no parallel
write-input path) all held, and the integration scan surfaced **no new** duplicated helper,
repeated literal, inconsistent error/naming pattern, misplaced responsibility, or
too-broad export. The standing P0 read/write split holds end-to-end: the read objects never
reach the mutation input path, `Upload` is never in `FIELD_OUTPUT_TYPE_MAP` or
`_PACKAGE_SCALAR_MAP`, the `SCALAR_MAP` file/image rows stay `str`, and the filter-input
path is byte-for-byte on the scalar path. The public surface is exactly the three Decision-7
symbols (`__all__` +3, `UploadDefinition` correctly module-only). All staged TODO anchors
are discharged and the comments tell one coherent read=object / filter-input=`str` /
mutation-input=`Upload` story.

**No consolidation needed.** There are no cross-slice DRY opportunities or defects that
warrant a Worker 2 consolidation + Worker 3 review loop.

The artifact `Status:` is set to **`final-accepted`**. **Worker 0 may mark the cross-slice
integration checkbox `- [x]`** and proceed to the final test-run gate (`bld-final.md`).
