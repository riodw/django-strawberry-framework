# Build: Slice 3 — public exports + coverage hardening

Spec reference: `docs/spec-037-upload_file_image_mapping-0_0_11.md` (lines 375-387, the `## Slice checklist` Slice 3 item; governed by Decision 7 lines 1167-1195 and Decision 9 lines 1226-1273)
Status: final-accepted

## Plan (Worker 1)

This slice lifts the three symbols Slices 1–2 already built into modules onto the package ROOT public surface, and hardens the synthetic-model coverage. It is the ONLY net-new public surface in the whole card (Decision 7 — three net-new root-exported symbols). It is NOT the version bump — `test_version` stays `0.0.10` here; the `0.0.11` cut is Slice 4 (Decision 10).

### DRY analysis

- **Existing patterns reused.**
  - The root re-export follows the existing `django_strawberry_framework/__init__.py` import/`__all__` convention EXACTLY — no parallel grouping. Imports are grouped by source subpackage, one `from .<module> import ...` per module, each carrying `# noqa: E402` (the package defers all imports below the `logger` declaration). `__all__` is a single alphabetically-sorted tuple of string literals (`__init__.py:45-66`, currently 20 entries; the assertion mirror is `tests/base/test_init.py::test_public_api_surface_is_pinned` at `test_init.py:46-67`). Slice 3 adds exactly three symbols into both, in their alphabetical slots — no new structural shape.
  - `Upload` is already module-level public in `scalars.py` — `from strawberry.file_uploads.scalars import Upload, UploadDefinition` (`scalars.py:25`) and `__all__ = ["BigInt", "Upload", "UploadDefinition", "strawberry_config"]` (`scalars.py:35`), landed by Slice 2. The root import re-exports `Upload` FROM `.scalars` (not from `strawberry.file_uploads.scalars` directly), so the package has one canonical import site. Carry-forward from Slice 2 final-verification confirmed `scalars.__all__` already lists `Upload`/`UploadDefinition`, so the root export does not double-declare.
  - `DjangoFileType` / `DjangoImageType` are already defined and module-public in `types/converters.py` (`converters.py::DjangoFileType` line 100, `converters.py::DjangoImageType` line 142), landed by Slice 1. The root import re-exports them FROM `.types.converters`.
  - The hardening tests REUSE the Slice 1 synthetic-model fixtures rather than re-defining synthetic models: `tests/types/test_resolvers.py::_make_asset_model` (line 1030 — `managed=False` FileField+ImageField under `app_label="products"`, name uniquified per call), `_asset_type` (1054), `_asset_schema` (1059), `_tiny_png_bytes` (1010, the real Pillow PNG), and the `connection.schema_editor()` create/delete + `override_settings(MEDIA_ROOT=tmp_path)` harness pattern (Decision 9 line 1252-1262). No new synthetic model is introduced.
- **New helpers justified.** None. The root re-export is pure import + `__all__` widening (no logic). The hardening tests add functions to existing test modules and reuse existing fixtures; no new test helper or fixture is justified (the Slice 1 `_make_asset_model` / `_asset_schema` / `_tiny_png_bytes` trio already cover every shape the new tests need — a corrupt-image stand-in is the only new test datum, an inline byte string, not a reusable helper).
- **Duplication risk avoided.**
  - **Risk: re-importing `Upload` from `strawberry.file_uploads.scalars` at the root** instead of from `.scalars`. Avoided: the plan re-exports from `.scalars` so the third-party import path lives in exactly one source location (matching how `BigInt` rides through `.scalars` per `__init__.py:32`).
  - **Risk: duplicating Slice 1's already-covered edge cases** (populated subfields, empty-file parent guard, `.path` `NotImplementedError` isolation, `SuspiciousFileOperation` non-swallow, the converter null/blank/force_nullable matrix). Avoided: the gap analysis below pins ONLY the two genuinely-uncovered `_safe_file_attr` catch arms (`ValueError`/`OSError` on a vanished file's `.size`/`.url`, and a dimension read failure on `width`/`height`). The new tests select those subfields one at a time over the SAME synthetic asset model, so they cannot accidentally re-pin a Slice 1 assertion.
  - **Risk: a second `__all__` assertion shape in `test_init.py`.** Avoided: the existing `test_public_api_surface_is_pinned` already asserts the full tuple; Slice 3 inserts the three new literals into that same tuple in alphabetical position (and may add a focused import-succeeds assertion), not a parallel pinning test.

### Implementation steps

Line numbers are pin-at-write-time navigational hints; verify against current source before editing.

1. **`django_strawberry_framework/__init__.py` — add the three root re-exports.** (`__init__.py:17-33` import block; `__init__.py:45-66` `__all__`.)
   - In the deferred-import block (the `from .<module> import ...` group below `logger`, lines 17-33), add `DjangoFileType` and `DjangoImageType` imported from `.types.converters`, and add `Upload` to the existing `from .scalars import ...` line. Concretely:
     - Change `from .scalars import BigInt, strawberry_config  # noqa: E402` (line 32) to `from .scalars import BigInt, Upload, strawberry_config  # noqa: E402`.
     - Add a new line `from .types.converters import DjangoFileType, DjangoImageType  # noqa: E402`. Place it adjacent to the existing `from .types import ...` line (line 33) so the two `.types`-rooted imports sit together, matching the file's source-grouped import convention. (Both `.types` and `.types.converters` are valid distinct modules; `DjangoType` / `finalize_django_types` / `SyncMisuseError` come from the `types` package `__init__`, while the two output objects live in the `types.converters` submodule — keep them on their own line rather than forcing them through `types/__init__.py`, unless Worker 2 finds `types/__init__.py` already re-exports them, in which case a single `from .types import ...` line is the DRYer site. See Implementation discretion items.)
   - Add `"DjangoFileType"`, `"DjangoImageType"`, and `"Upload"` to the `__all__` tuple (lines 45-66) in their alphabetical slots: `"DjangoFileType"` after `"DjangoConnectionField"` / before `"DjangoImageType"`; `"DjangoImageType"` before `"DjangoListField"`; `"Upload"` is uppercase-U so it sorts among the capitalized names — between `"SyncMisuseError"` and `"__version__"` (capital letters sort before `_`; verify the exact slot against the file's existing ordering, which is plain ASCII/`sorted()` order: all capitalized names, then `__version__`, then the lowercase block). Match the existing one-literal-per-line trailing-comma layout (`AGENTS.md` trailing-comma rule; this tuple is already exploded).
   - **Remove the staged TODO anchor** at `__init__.py:35-42` (`# TODO(spec-037 Slice 3/4): add the new public symbols and final 0.0.11 cut here.` and its pseudo-code block). The Slice 3 half (the three exports) lands now; the Slice 4 half (the `0.0.11` bump) is a SEPARATE concern. Worker 2 must decide: the cleanest move is to remove the whole anchor now AND leave a one-line `# TODO(spec-037 Slice 4): bump __version__ to 0.0.11 ...` so the version-cut reminder survives for Slice 4. Do NOT touch `__version__ = "0.0.10"` (line 43) — that is Slice 4's exclusive job (Decision 10; my memory carry-forward: re-confirm version is STILL 0.0.10 at this slice's final-verification).
   - **Do NOT export `UploadDefinition` from the root.** The spec Slice 3 sub-bullet (line 379-381) names exactly `Upload` / `DjangoFileType` / `DjangoImageType` — three symbols. `UploadDefinition` is re-exported at the `scalars.py` MODULE surface only (Slice 2, sanctioned by Decision 5), not the root. Decision 7 (lines 1169-1170) lists exactly the same three. No ambiguity — plan exactly three.

2. **`tests/base/test_init.py` — pin the three new exports and `__all__`.** (`test_init.py:37-67` `test_public_api_surface_is_pinned`; `test_init.py:17-18` `test_version`.)
   - Insert `"DjangoFileType"`, `"DjangoImageType"`, and `"Upload"` into the `__all__` equality tuple in `test_public_api_surface_is_pinned` (lines 46-67), in the SAME alphabetical slots as the source so the two stay in lockstep.
   - Add an import-succeeds assertion that the three names import from `django_strawberry_framework` and are the SAME objects as their source-module definitions (e.g. `from django_strawberry_framework import DjangoFileType, DjangoImageType, Upload` resolves and `DjangoFileType is converters.DjangoFileType`, etc.) — pins the re-export identity, not just `__all__` membership. Worker 2's discretion on whether this is a new focused test or extra asserts inside the surface test (see discretion items).
   - Update the explanatory comment block at `test_init.py:42-45` (which currently narrates only the four-symbol mutation surface from spec-036) to also note the three file/upload symbols landed by spec-037 Slice 3, and KEEP the `# test_version is untouched ...` sentence (re-anchor it to Decision 10 / the 0.0.11 joint cut).
   - **`test_version` (lines 17-18) is NOT touched in this slice.** It stays `assert __version__ == "0.0.10"`. The version bump is Slice 4 (Decision 10). Also remove (or re-scope to Slice 4) the file-top `# TODO(spec-037 Slice 3/4):` anchor (lines 3-8): the export-pinning half lands now; leave a one-line Slice 4 version-cut reminder if Worker 2 judges it useful, mirroring the `__init__.py` anchor disposition.

3. **`tests/types/test_resolvers.py` — harden the two uncovered `_safe_file_attr` catch arms.** (Append after the existing file/image resolver block, which ends at `test_suspicious_file_operation_is_not_swallowed`, `test_resolvers.py:1173-1205`. Reuse `_make_asset_model` / `_asset_type` / `_asset_schema` / `_tiny_png_bytes` and the `schema_editor` + `override_settings(MEDIA_ROOT=tmp_path)` harness.)
   - **Test A — vanished-file `.size`/`.url` degrade to `null` (the `OSError`/`ValueError` arms).** Save a populated `attachment`, then delete the underlying file on disk (or monkeypatch `FileSystemStorage.size` / `.open` to raise `OSError`/`FileNotFoundError`) so resolving `attachment { size url }` exercises `_safe_file_attr`'s `except (ValueError, OSError, NotImplementedError)` via the `OSError` path (Slice 1 fired only `NotImplementedError` on `.path`). Assert `errors is None` and the failed subfield(s) resolve to `null` while `name` still resolves. The realistic real path: `os.remove` the saved file under `tmp_path` then select `size` — a vanished file makes `FieldFile.size` raise `FileNotFoundError` (an `OSError` subclass). Prefer the real-deletion path over a monkeypatch where it works (Decision 9 prefers real `tmp_path` storage; mock only the impractical non-filesystem case). This is the spec "Missing file in storage" edge (lines 1345-1348) and directly covers the `OSError`/`ValueError` arms the `path`-only Slice 1 test left cold.
   - **Test B — image dimension (`width`/`height`) read failure degrades to `null`.** Save the `preview` ImageField with bytes that are NOT a valid image (a few non-PNG bytes via `ContentFile(b"not an image")`, written with `save=False` so Pillow never validates at save time), then select `preview { width height }`. `ImageFieldFile.width` / `.height` ask Pillow to read dimensions, which raises on un-parseable bytes; `_safe_file_attr` degrades each to `null`. Assert `errors is None` and `width`/`height` are `null` while `name` still resolves. This is the spec "Image dimensions at read time ... degrade to null via _safe_file_attr when the stored image is missing / corrupt" edge (lines 1364-1369) — Slice 1 read dimensions only from a VALID image (success path at `test_populated_file_and_image_resolve_all_subfields`, lines 1071-1098), leaving the dimension FAILURE path uncovered.
   - Both tests carry `@pytest.mark.django_db(transaction=True)` and the `try/finally` `schema_editor.delete_model` teardown matching the existing block. NO new synthetic model — reuse `_make_asset_model`.

### Test additions / updates

- `tests/base/test_init.py::test_public_api_surface_is_pinned` — `__all__` tuple gains `"DjangoFileType"`, `"DjangoImageType"`, `"Upload"` in alphabetical slots; pins the package public surface against silent widening/narrowing. Plus an import-identity assertion (the three names import from the root and are the same objects as their source-module definitions).
- `tests/base/test_init.py::test_version` — UNCHANGED; stays `assert __version__ == "0.0.10"` (Slice 4 owns the bump). Worker 3 / Worker 1 final-verification must confirm it was NOT touched.
- `tests/types/test_resolvers.py` — two NEW tests appended to the spec-037 file/image block:
  - Test A (vanished-file `.size`/`.url` → `null`): pins the `OSError`/`ValueError` arms of `_safe_file_attr` (Slice 1 covered only `NotImplementedError`). Assertion shape: `result.errors is None`; the deleted-file subfield(s) are `null`; `name` still resolves.
  - Test B (corrupt-image `width`/`height` → `null`): pins the dimension-read FAILURE path through `_safe_file_attr` (Slice 1 covered only the valid-image dimension success). Assertion shape: `result.errors is None`; `width`/`height` are `null`; `name` still resolves.
- **Edge cases the plan deliberately does NOT re-test (already covered by Slice 1 — Worker 3 should confirm no duplication):** converter `FileField`→`DjangoFileType` / `ImageField`→`DjangoImageType` mapping, MRO precedence (`test_field_output_map_mro_precedence_image_subclass_wins`), the `blank`/`null` → `| None` widen matrix (`test_convert_field_output_blank_and_null_widen_to_optional`, `test_converters.py:1732`), `force_nullable` compose (`test_convert_field_output_force_nullable_overrides_blank_null`, `:1756`), filter-input-stays-scalar (`test_file_columns_stay_scalar_on_the_filter_input_path`, `:1801`), populated subfields incl. valid-image `width`/`height`=2/3 (`test_populated_file_and_image_resolve_all_subfields`, `test_resolvers.py:1071`), empty-file → null parent guard (`test_empty_file_resolves_parent_object_to_null`, `:1105`), per-subfield `.path` `NotImplementedError` isolation (`test_per_subfield_guard_isolates_storage_failure`, `:1129`), `SuspiciousFileOperation` non-swallow (`test_suspicious_file_operation_is_not_swallowed`, `:1174`), and the `attachment: str` override → no resolver/object (`test_consumer_annotation_override_on_file_column_keeps_str_and_no_resolver`, `test_base.py:1820`).
- **Temp/scratch tests:** none expected. The two hardening tests are permanent additions to `tests/types/test_resolvers.py`. Worker 2 writes them in the same change (per `AGENTS.md` add-tests-with-code and BUILD.md coverage-is-the-maintainer's-gate — NO `--cov*` flags; the gaps are pinned by reading the diff against Decision 4's catch list, not by running coverage).

### Implementation discretion items

These are stylistic/equivalent-shape choices I have ASSESSED and decided belong to Worker 2 — not architectural escape hatches:

- **`DjangoFileType` / `DjangoImageType` import line.** Re-export from `.types.converters` on its own import line (the plan's default, since that submodule is the canonical definition site) OR — if Worker 2 confirms `types/__init__.py` already re-exports both — fold them into the existing `from .types import ...` line (line 33) for one DRYer import site. Either is correct; pick the one that keeps the import grouped with its siblings without inventing a new re-export in `types/__init__.py` just to enable the single-line form. (Do NOT add a re-export to `types/__init__.py` solely for this; that would be net-new surface churn the spec did not authorize.)
- **`test_init.py` import-identity assertion placement.** Add the `is`-identity / import-succeeds asserts as extra lines inside `test_public_api_surface_is_pinned`, OR as a small dedicated `test_file_upload_exports_are_importable` test in the same file. Both satisfy the spec sub-bullet ("the public-export and `__all__` assertions add the three symbols"). The `tests/base/` placement is fixed (`AGENTS.md`: `tests/base/` holds exactly `test_init.py` and `test_conf.py`, both may grow — no NEW file).
- **TODO-anchor disposition** in `__init__.py` and `test_init.py`: whether to leave a trimmed one-line `# TODO(spec-037 Slice 4): bump __version__ ...` reminder after removing the Slice-3 half of each anchor, or remove the whole anchor and rely on the build plan. Leaving a one-line Slice-4 reminder is mildly preferred (keeps the version-cut site self-documenting), but removal is acceptable since the build plan tracks Slice 4.
- **Test A failure mechanism.** Real on-disk file deletion (`os.remove` / `pathlib.unlink` under `tmp_path`) to make `.size` raise `FileNotFoundError` is preferred (Decision 9: real temp storage over mocks). A `monkeypatch.setattr(FileSystemStorage, "size", ...)` raising `OSError`/`ValueError` is the acceptable fallback if the real-deletion path proves flaky under `transaction=True`. Either exercises the same catch arm.

### Spec slice checklist (verbatim)

The spec's nested sub-bullets for Slice 3 from `## Slice checklist` (lines 375-387), copied verbatim:

- [x] [`__init__.py`][init]: re-export `Upload` (from [`scalars.py`][scalars])
  and `DjangoFileType` / `DjangoImageType` (from
  [`types/converters.py`][types-converters]); add all three to `__all__`.
- [x] Package coverage: [`tests/base/test_init.py`][test-base-init] — the
  public-export and `__all__` assertions add the three symbols (`test_version`
  moves to `0.0.11` in Slice 4,
  [Decision 10](#decision-10--this-card-owns-the-final-0011-version-bump)).
  Storage-failure / null-blank / image-dimension edge tests harden the
  synthetic-model coverage.

### Notes for Worker 1 (spec reconciliation) — recorded at planning, NOT a spec edit

- **The Slice 3 sub-bullet names three hardening categories: "storage-failure / null-blank / image-dimension". Only TWO are genuine gaps after Slice 1.** My read of the Slice 1 diff (`tests/types/test_converters.py` and `tests/types/test_resolvers.py`) found:
  - **null-blank — ALREADY FULLY COVERED by Slice 1**, not a Slice 3 gap. `test_convert_field_output_blank_and_null_widen_to_optional` (`test_converters.py:1732`) pins the required/`blank=True`/`null=True` → `| None` matrix, and `test_convert_field_output_force_nullable_overrides_blank_null` (`:1756`) pins the `force_nullable` compose. Re-testing null/blank in Slice 3 would DUPLICATE Slice 1 (a DRY defect). Plan deliberately does NOT add a null/blank test.
  - **storage-failure — PARTIAL gap.** Slice 1 covered the `.path` `NotImplementedError` arm only (`test_per_subfield_guard_isolates_storage_failure`) and the `SuspiciousFileOperation` non-swallow. The `OSError`/`ValueError` arms of `_safe_file_attr`'s `except (ValueError, OSError, NotImplementedError)` (`converters.py::_safe_file_attr` line 96) — a vanished-file `.size`/`.url` — are UNCOVERED. Slice 3 Test A pins them.
  - **image-dimension — PARTIAL gap.** Slice 1 read `width`/`height` only from a VALID Pillow image (success path). The dimension-READ-FAILURE path (corrupt/missing image → `_safe_file_attr` degrades to `null`) is UNCOVERED. Slice 3 Test B pins it.
  This is the spec's own intent (the sub-bullet says "harden ... coverage", and Decision 9 forbids `pytest.skip`-style gaps under `fail_under = 100`), so I read the three-category list as naming the SURFACE to harden, not three mandatory net-new tests. The verbatim box stays as-is and ticks when Test A + Test B + the export pins land; null/blank is satisfied by the pre-existing Slice 1 coverage. No spec wording change is needed — flagging here so Worker 2 does not add a redundant null/blank test and Worker 3 does not read its absence as a silently-unaddressed sub-check.

### Notes for Worker 3

- This slice's `git diff -- django_strawberry_framework/__init__.py` DOES change `__all__` and the re-export list — that change is AUTHORIZED by spec Decision 7 (lines 1167-1195) and the Slice 3 sub-bullet (lines 379-381): exactly three net-new root exports (`Upload`, `DjangoFileType`, `DjangoImageType`). The Public-surface check should confirm exactly these three (and ONLY these three — `UploadDefinition` must NOT appear at the root) and cite Decision 7.
- `__version__` MUST remain `"0.0.10"` and `test_version` MUST remain unchanged in this slice (Decision 10 — the bump is Slice 4). A version change here is a finding.
- Static inspection helper: SKIPPED for `__init__.py`. Per BUILD.md ("Worker 1/3 may skip the helper for pure re-exports") — the `__init__.py` change is pure import + `__all__` widening with ZERO new logic. Recorded skip + reason here. No slice file gains ≥30 lines of new logic (the only source file touched, `__init__.py`, gains ~4 lines, all re-export/`__all__`).

---

## Build report (Worker 2)

Implemented the plan exactly. The slice landed as: three root re-exports in `__init__.py` (+ `__all__` widening), the matching pins in `tests/base/test_init.py`, and the two genuine-gap hardening tests in `tests/types/test_resolvers.py`. No production logic changed beyond the import block (pure re-export). `__version__` stays `0.0.10` (Slice 4 owns the bump). Both verbatim sub-checks ticked — their contracts landed in this diff.

### Files touched

- `django_strawberry_framework/__init__.py` — added the three root re-exports: `Upload` folded into the existing `from .scalars import BigInt, Upload, strawberry_config` line (re-exported FROM `.scalars`, the one canonical site, not from `strawberry.file_uploads.scalars` directly); `DjangoFileType` / `DjangoImageType` on a new `from .types.converters import DjangoFileType, DjangoImageType` line adjacent to the `.types` import. Added `"DjangoFileType"`, `"DjangoImageType"`, `"Upload"` to `__all__` in their ASCII-`sorted()` slots (the two `Django*` names between `"DjangoConnectionField"` and `"DjangoListField"`; `"Upload"` between `"SyncMisuseError"` and `"__version__"` — capital `U` sorts before `_`). Replaced the staged `# TODO(spec-037 Slice 3/4)` pseudo-block with a one-line `# TODO(spec-037 Slice 4): bump __version__ ...` reminder (discretion item — keeps the version-cut site self-documenting). `UploadDefinition` is NOT root-exported (stays module-only on `scalars.__all__`). `__version__ = "0.0.10"` untouched.
- `tests/base/test_init.py` — imported the three symbols from the package root plus `Upload as ScalarsUpload` from `.scalars` and the `types.converters` module for the identity check. Inserted the three literals into the `test_public_api_surface_is_pinned` `__all__` equality tuple in the SAME alphabetical slots as the source. Added a new focused test `test_file_upload_exports_resolve_to_their_source_definitions` pinning re-export IDENTITY (`Upload is ScalarsUpload`, `DjangoFileType is converters.DjangoFileType`, `DjangoImageType is converters.DjangoImageType`). Updated the surface-test comment to name the three spec-037 symbols and re-anchored the `test_version` note to Decision 10 / the 0.0.11 Slice 4 cut. Rewrote the file-top TODO anchor to a one-line Slice 4 version-cut reminder. `test_version` body unchanged (`assert __version__ == "0.0.10"`).
- `tests/types/test_resolvers.py` — appended two permanent tests after `test_suspicious_file_operation_is_not_swallowed`, reusing the Slice 1 `_make_asset_model` / `_asset_type` / `_asset_schema` / `_tiny_png_bytes` fixtures and the `schema_editor` + `override_settings(MEDIA_ROOT=tmp_path)` + `try/finally` `delete_model` harness. No new synthetic model.

### Tests added or updated

- `tests/base/test_init.py::test_public_api_surface_is_pinned` — `__all__` equality tuple gains `"DjangoFileType"`, `"DjangoImageType"`, `"Upload"`; pins the package public surface against silent widening/narrowing.
- `tests/base/test_init.py::test_file_upload_exports_resolve_to_their_source_definitions` — NEW; pins that the three root names ARE their source-module definitions (re-export identity), not parallel definitions.
- `tests/base/test_init.py::test_version` — UNCHANGED; still `assert __version__ == "0.0.10"`. Confirmed not touched (Slice 4 owns the bump).
- `tests/types/test_resolvers.py::test_vanished_file_degrades_size_and_url_to_null` — NEW; pins the `OSError`/`ValueError` arms of `_safe_file_attr`. Saves a real file under `tmp_path`, `os.remove`s it on disk, selects `{ attachment { name size } }`; asserts `errors is None`, `size` is `null` (the read raised `FileNotFoundError`, an `OSError` subclass), and `name` still resolves. Real-deletion path (Decision 9 prefers real temp storage over a monkeypatch).
- `tests/types/test_resolvers.py::test_corrupt_image_degrades_width_and_height_to_null` — NEW; pins the image-dimension-read FAILURE path through `_safe_file_attr`. Saves non-image bytes (`ContentFile(b"not an image")`, `save=False`) on the ImageField, selects `{ preview { name width height } }`; asserts `errors is None`, `width`/`height` are `null` (Pillow cannot parse), and `name` still resolves.
- **Deliberately NOT added (per planner's DRY finding, Notes for Worker 1):** a null/blank converter edge test — that is ALREADY fully covered by Slice 1 (`test_convert_field_output_blank_and_null_widen_to_optional` / `test_convert_field_output_force_nullable_overrides_blank_null` in `tests/types/test_converters.py`). Re-testing it here would be a DRY defect. Only the two genuine gaps (storage-failure `OSError`/`ValueError` arms, image-dimension FAILURE path) were added.

### Validation run

- `uv run ruff format .` — pass (287 files left unchanged; the one-time `COM812`-with-formatter warning is the repo's standing config notice, not a failure).
- `uv run ruff check --fix .` — pass on the second run. First run flagged `N813 Camelcase 'Upload' imported as lowercase 'scalars_upload'` in `test_init.py`; fixed by renaming the alias to `ScalarsUpload` (keeps the camelcase contract). "All checks passed!" after the rename.
- `git status --short` after both ruff invocations — modified set is the prior-slice baseline (`mutations/*`, `scalars.py`, `types/*`, `tests/mutations/*`, `tests/test_scalars.py`, `tests/types/test_base.py`, `tests/types/test_converters.py`, `pyproject.toml`, `uv.lock`, the spec edit) PLUS my three slice-intended files: `django_strawberry_framework/__init__.py`, `tests/base/test_init.py`, `tests/types/test_resolvers.py`. The four untracked `docs/builder/*.md` are prior-slice / current artifacts. NO unrelated tool churn appeared — ruff touched nothing outside my three files (no `git checkout --` reverts needed). `tests/types/test_resolvers.py` was already baseline-dirty from Slice 1; my change is the two appended tests only (confirmed via `git diff` — only the two new `def test_...` functions are mine).
- Focused tests (no `--cov*`): `uv run pytest tests/base/test_init.py tests/types/test_resolvers.py --no-cov -q` → 43 passed. Broader scope `uv run pytest tests/base/test_init.py tests/types/ --no-cov -q` → 403 passed, 2 skipped (pre-existing skips). Both green.

### Implementation notes

- **`DjangoFileType` / `DjangoImageType` import line.** Chose the plan's DEFAULT: a dedicated `from .types.converters import DjangoFileType, DjangoImageType` line. Confirmed `types/__init__.py` does NOT re-export the two output objects (it re-exports only `DjangoType` / `SyncMisuseError` / `finalize_django_types`), so the single-line `from .types import ...` form was not available without adding net-new surface to `types/__init__.py` — which the discretion item explicitly forbids. The dedicated line sits adjacent to the existing `.types` import, matching the source-grouped convention.
- **Import-identity assertion placement.** Chose a small dedicated `test_file_upload_exports_resolve_to_their_source_definitions` test (one of the two sanctioned shapes) rather than folding `is`-asserts into the surface-pinning test, because the identity check is a distinct concern (re-export wiring) from the `__all__` membership pin and reads cleaner isolated. `tests/base/` placement honored (no new file — added to the existing `test_init.py`).
- **`ScalarsUpload` alias.** The identity assertion needs a reference to the `.scalars` module's `Upload` distinct from the root `Upload`; `from ... import Upload as scalars_upload` tripped `N813` (camelcase-as-lowercase), so the alias is `ScalarsUpload` (PascalCase satisfies the rule and reads as "the scalars-module Upload").
- **TODO-anchor disposition.** Left a trimmed one-line `# TODO(spec-037 Slice 4): bump __version__ ...` in both `__init__.py` and `test_init.py` (the mildly-preferred discretion option) so the version-cut site stays self-documenting for the next slice.
- **Test A failure mechanism.** Used the preferred real on-disk `os.remove(asset.attachment.path)` under `tmp_path` (Decision 9 real-storage preference); it fired `FileNotFoundError` cleanly under `transaction=True` with no flakiness, so the monkeypatch fallback was not needed.

### Notes for Worker 3

- No shadow file / static-inspection helper used — the only source change is `__init__.py` (pure import + `__all__` widening, zero new logic; helper-skip is recorded in the Plan's Notes for Worker 3 and remains correct).
- Public-surface check expectation: `git diff -- django_strawberry_framework/__init__.py` DOES change `__all__` and the re-export list — exactly three net-new root exports (`Upload`, `DjangoFileType`, `DjangoImageType`), authorized by Decision 7 / the Slice 3 sub-bullet. `UploadDefinition` is NOT at the root (verify it does not appear). This is the one slice where an `__init__.py` change is correct (unlike Slices 1–2).
- `__version__` remains `"0.0.10"` and `test_version` is byte-unchanged — confirm both.
- The two new resolver tests select the failing subfield alongside `name` so the assertion proves per-subfield isolation (failed subfield `null`, `name` still resolves), matching the Slice 1 isolation pattern. No null/blank test was added (Slice 1 covers it — see Tests-added note above); its absence is intentional, not a silently-unaddressed sub-check.

### Notes for Worker 1 (spec reconciliation)

- No spec gap, conflict, or unstated assumption surfaced. The plan's Notes-for-Worker-1 DRY finding (null/blank is Slice-1-covered; only the `OSError`/`ValueError` arms and the dimension FAILURE path are genuine Slice 3 gaps) held exactly — both new tests target those two arms and nothing else. No spec edit needed.
- Confirm at final verification: `__version__` is STILL `"0.0.10"` and `tests/base/test_init.py::test_version` is unchanged (the Slice 4 bump must not have leaked into this slice).

---

## Review (Worker 3)

Reviewed ONLY the Slice 3 contribution: `git diff -- django_strawberry_framework/__init__.py tests/base/test_init.py` and the TWO new appended functions in `tests/types/test_resolvers.py` (`test_vanished_file_degrades_size_and_url_to_null`, `test_corrupt_image_degrades_width_and_height_to_null`). The rest of `test_resolvers.py` (the Slice 1 file/image block, fixtures `_make_asset_model` / `_asset_type` / `_asset_schema` / `_tiny_png_bytes`, and the four Slice 1 resolver tests) is accepted prior-slice work and was read only as the reuse surface, not re-reviewed. The other working-tree dirt (`mutations/*`, `scalars.py`, `types/*` except the two new resolver tests, `tests/test_scalars.py`, `tests/mutations/*`, `tests/types/test_base.py`, `tests/types/test_converters.py`, `pyproject.toml`, `uv.lock`, the spec edit) is prior-accepted Slice 1+2 work and out of scope.

### High:

None.

### Medium:

None.

### Low:

- **`test_vanished_file_degrades_size_and_url_to_null` name/docstring overstate the `url` arm.** Low. `tests/types/test_resolvers.py::test_vanished_file_degrades_size_and_url_to_null` (test body at the `os.remove(asset.attachment.path)` line through the `assert attachment["size"] is None` line). The test name and docstring claim it nulls "`size` / `url`", but the selection is `{ assets { attachment { name size } } }` and it asserts only `attachment["size"] is None` (plus `name` still resolves) — `url` is never selected or asserted. I verified with `FileSystemStorage` on a real vanished file (override_settings temp dir, `os.remove`, then read `.url` / `.size`): `.url` returns `/media/x.txt` and does NOT raise (it builds the URL from `MEDIA_URL` + name without touching disk), while `.size` raises `FileNotFoundError` (an `OSError` subclass) and correctly degrades to `null` via `_safe_file_attr` at `django_strawberry_framework/types/converters.py::_safe_file_attr #"except (ValueError, OSError, NotImplementedError)"`. So on this real-deletion path a `url` selection would resolve non-null, NOT null — the test cannot honestly assert a `url` degradation here and correctly does not. Why it matters: the name/docstring imply a `url`-degradation contract the test does not (and on `FileSystemStorage` cannot) pin; a future reader could believe `url` degradation is regression-guarded when it is not. The behavior is correct; only the label is inaccurate. Recommended change (label only, no behavior): rename to `test_vanished_file_degrades_size_to_null` and reword the docstring to describe only the `.size` → `OSError` arm (drop the `/ url` and the "nulls `size` / `url`" phrasing). No test-expectation change — the assertion shape (`size` null, `name` resolves) is already correct. Escalated to Worker 1 below since the planner's wording (and the spec sub-bullet) used the "`.size`/`.url`" framing; Worker 1 may instead choose to genuinely cover the `url`-degradation arm by mocking a storage whose `.url` raises `OSError`/`ValueError` if it wants the `url` arm pinned by behavior rather than dropping the claim.

### DRY findings

Clean — no DRY defect. Confirmed:

- **Root re-exports follow the existing `__init__.py` pattern with no parallel grouping.** `Upload` is folded into the existing `from .scalars import BigInt, Upload, strawberry_config  # noqa: E402` line (re-exported FROM `.scalars`, the one canonical site, NOT from `strawberry.file_uploads.scalars` directly — matching how `BigInt` rides through `.scalars`). `DjangoFileType` / `DjangoImageType` sit on a dedicated `from .types.converters import DjangoFileType, DjangoImageType  # noqa: E402` line adjacent to the `from .types import ...` line, source-grouped. Worker 2 confirmed `types/__init__.py` does NOT re-export the two output objects, so folding into `from .types import ...` was not available without net-new surface in `types/__init__.py` (which the discretion item forbids); the dedicated line is the correct DRY choice. No new import-grouping shape introduced.
- **The two hardening tests reuse the Slice 1 fixtures.** Both call `_make_asset_model()` / `_asset_type()` / `_asset_schema()` and the `_tiny_png_bytes` family via the existing `schema_editor().create_model` + `override_settings(MEDIA_ROOT=tmp_path)` + `try/finally` `delete_model` harness. NO new synthetic model; the only new test datum is the inline `ContentFile(b"not an image")` corrupt-image stand-in (not a reusable helper — correctly inline).
- **No duplication of Slice 1 coverage.** The two new tests do NOT re-pin null/blank widening (Slice 1: `test_convert_field_output_blank_and_null_widen_to_optional` / `..._force_nullable_overrides_blank_null` in `test_converters.py`), the populated-subfield success path, the empty-file parent guard, the `.path`/`NotImplementedError` isolation, or the `SuspiciousFileOperation` non-swallow. Each new test selects its failing subfield specifically (`size` alongside `name`; `width`/`height` alongside `name`) and pins a genuinely different runtime arm.
- **`test_init.py` adds no parallel `__all__` shape.** The three literals go into the SAME `test_public_api_surface_is_pinned` exact-tuple; the identity check is a separate focused test (`test_file_upload_exports_resolve_to_their_source_definitions`), a distinct concern (re-export wiring vs surface membership), correctly not folded.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` DOES change `__all__` and the re-export list. UNLIKE Slices 1–2, this change IS authorized — spec Decision 7 (`docs/spec-037-...md` lines 1167-1170): "[`__init__.py`][init] re-exports and adds to `__all__`: `Upload` (the scalar, from [`scalars.py`][scalars]), `DjangoFileType`, and `DjangoImageType` (from [`types/converters.py`][types-converters])" and the Slice 3 sub-bullet (lines 379-381). Confirmed:

- **Exactly three net-new root exports**, no more, no fewer: `Upload` (from `.scalars`), `DjangoFileType` / `DjangoImageType` (from `.types.converters`). The import diff adds exactly these three (Upload onto the existing `.scalars` line, the two output objects on one new line).
- **`UploadDefinition` is NOT root-exported.** Confirmed absent from both the import block and `__all__`; it stays module-only on `scalars.__all__` (Slice 2, Decision 5). Probe `_PACKAGE_SCALAR_MAP` check confirmed `Upload not in _PACKAGE_SCALAR_MAP` and `Upload is strawberry.file_uploads.scalars.Upload` (rides the built-in `DEFAULT_SCALAR_REGISTRY`, not the package map — Decision 5).
- **No existing export removed or reordered.** The 20-entry pre-Slice-3 surface is intact; the three additions land in their `sorted()` slots — `"DjangoFileType"` / `"DjangoImageType"` between `"DjangoConnectionField"` and `"DjangoListField"`; `"Upload"` between `"SyncMisuseError"` and `"__version__"` (capital `U` sorts before `_`). I verified the full 23-tuple is exactly `sorted()` order via a Python check (`list(__all__) == sorted(__all__)` → True). `test_init.py`'s `test_public_api_surface_is_pinned` uses an exact-tuple equality assertion (not loose membership) mirroring the source tuple in lockstep — a temp probe confirmed dropping any one of the three (or adding an extra) breaks the equality, so it is genuinely a pin.
- **Re-export identity is genuine (non-vacuous).** `test_file_upload_exports_resolve_to_their_source_definitions` asserts `Upload is ScalarsUpload`, `DjangoFileType is converters.DjangoFileType`, `DjangoImageType is converters.DjangoImageType`. A temp probe confirmed these hold AND that a deliberately-wrong identity (`DjangoFileType is converters.DjangoImageType`) fails — so the `is` checks discriminate, not vacuously pass.

### CHANGELOG sanity

Not applicable; slice did not modify `CHANGELOG.md`. (The card's `CHANGELOG.md` edit is Slice 4 and gated on an explicit maintainer prompt per `AGENTS.md`.)

### Documentation / release sanity

In scope for this slice's review: the VERSION GUARD (Decision 10 — the `0.0.11` bump is Slice 4, NOT here). Confirmed:

- **`__version__` is byte-unchanged at `"0.0.10"`** (`django_strawberry_framework/__init__.py` line 38). The diff does not touch it.
- **`tests/base/test_init.py::test_version` is byte-unchanged** — still `assert __version__ == "0.0.10"`. The diff hunk shows `def test_version():` only as unchanged context; the edited lines are all inside `test_public_api_surface_is_pinned`'s comment + tuple and the new identity test. No version-bump leak into this slice.
- **The replaced TODO pseudo-block still names the Slice 4 version cut** in BOTH files — `__init__.py` now carries `# TODO(spec-037 Slice 4): bump __version__ to 0.0.11 here with pyproject.toml, uv.lock, docs/GLOSSARY.md, and tests/base/test_init.py::test_version aligned.` and `test_init.py` the mirroring one-line Slice 4 reminder. No staged-work loss — the version-cut site stays self-documenting (the mildly-preferred discretion option).
- The `test_public_api_surface_is_pinned` explanatory comment was updated to name the three spec-037 symbols and re-anchored the `test_version`-untouched note to Decision 10 / the Slice 4 joint cut. Accurate.
- No standing doc (`docs/GLOSSARY.md`, READMEs, `TODAY.md`) is touched by this slice — correct; all doc promotion is Slice 4.

### What looks solid

- **The export wiring is minimal and correct.** Three re-exports, three `__all__` entries, all in canonical `sorted()` slots, all from the one canonical source site each (`.scalars` for `Upload`, `.types.converters` for the two objects). Pure import + `__all__` widening, zero new logic.
- **Both hardening tests pin genuine, previously-uncovered runtime arms.** I traced control flow against `converters.py::_safe_file_attr` (catch `(ValueError, OSError, NotImplementedError)`): Slice 1 fired only `NotImplementedError` (the `.path` non-filesystem case) and the valid-image dimension success. Test A's real `os.remove` makes `FieldFile.size` raise `FileNotFoundError` (`OSError` subclass) → the `OSError` arm, degrading `size` to `null`. Test B's `ContentFile(b"not an image")` (saved `save=False` so Pillow never validates at save) makes `ImageFieldFile.width`/`.height` raise on the Pillow dimension read → degrades each to `null`. Both select the failing subfield ALONGSIDE the un-guarded `name` (which reads `self.name` directly, no guard) so the assertion proves per-subfield isolation (failed subfield `null`, `name` still resolves) — matching the Slice 1 isolation pattern.
- **The tests are distinguishing, not vacuous.** Temp probes confirmed: `size` is non-null (== 11) with the file present and `null` only after `os.remove`; `width`/`height` are `2`/`3` for a valid PNG and `null` only for corrupt bytes. So the permanent null-assertions can pass ONLY on the genuine failure arm.
- **The `ValueError`-no-file arm is correctly NOT separately tested.** The parent resolver `_make_file_resolver` returns `None` for a falsy `FieldFile` (`return value if value else None`, `resolvers.py` line 456) before any subfield runs, so the "no file associated" `ValueError` is structurally unreachable from a populated object — there is no honest synthetic path to it via the subfield resolvers. Not adding a contrived test for an unreachable arm is the right call; the `except` clause line itself is exercised by the `OSError`/`NotImplementedError` arms.
- **The DRY-finding-by-omission (no null/blank re-test) is correct and the planner's Notes-for-Worker-1 reasoning held** — null/blank is fully covered by Slice 1; re-testing would be a DRY defect. Its absence is intentional, not a silently-unaddressed sub-check.

### Temp test verification

Created `docs/builder/temp-tests/slice-3/test_nonvacuity_probe.py` (gitignored; confirmed via `git check-ignore`), ran with `--no-cov` (never `--cov*`). Five probes, all passed:

1. `test_all_tuple_assertion_is_exact_not_membership` — dropping any one of the three exports (or adding an extra) breaks the exact-tuple equality → the permanent `__all__` assertion is a genuine pin, not loose membership.
2. `test_reexport_identity_is_genuine_source_object` — the three root names ARE their source objects, and a wrong identity fails `is` → the permanent identity test discriminates.
3. `test_upload_is_strawberry_builtin_not_package_mapped` — `Upload is strawberry.file_uploads.scalars.Upload` and `Upload not in _PACKAGE_SCALAR_MAP` (Decision 5 confirmed).
4. `test_size_is_NONNULL_when_file_present_then_null_when_removed` — `size` == 11 present, `None` after `os.remove`; `name` survives → Test A's null-assertion is distinguishing.
5. `test_width_is_NONNULL_for_valid_image_then_null_for_corrupt` — `width`/`height` == 2/3 for valid PNG, `None` for corrupt bytes → Test B's null-assertion is distinguishing.

(One probe initially failed with `ConfigurationError: finalize_django_types() already ran` — a probe-only isolation gap because I omitted the `_isolate_registry` autouse fixture that `test_resolvers.py` defines at its top; added the fixture and all five passed. NOT a defect in the permanent tests, which inherit that fixture.)

The probe caught no behavior bug — it only confirmed the permanent assertions are load-bearing. Per BUILD.md temp-test rules, nothing to promote; the probe was deleted after verification (disposition: discarded, no permanent test owed).

Focused permanent-test runs (no `--cov*`): the two new resolver tests + all of `test_init.py` → 7 passed; broader `tests/base/test_init.py tests/types/` → 403 passed, 2 skipped (the 2 skips are pre-existing). Matches Worker 2's reported run.

Static inspection helper: SKIPPED for `__init__.py` — it is a pure re-export module (only re-exports + `__all__`, zero logic; ~4 net new lines, all import/`__all__`), per BUILD.md "Worker 1/3 may skip the helper for pure re-exports." Recorded skip + reason. The two new tests are test code; no helper required (each is straight-line synthetic-model setup + schema execute + asserts, no review-worthy logic). No source file under `types/` or `optimizer/` was touched by THIS slice (the only source change is the root `__init__.py`).

### Notes for Worker 1 (spec reconciliation)

- **Escalated (Low): `test_vanished_file_degrades_size_and_url_to_null` name/docstring overstate the `url` arm.** The test pins only `size` → `OSError`; on `FileSystemStorage` a vanished file's `.url` does not raise (verified empirically), so a `url` degradation is not — and on this real-deletion path cannot be — asserted. Two resolution paths for Worker 1 to pick between at final verification: (a) **label-only** — rename to `test_vanished_file_degrades_size_to_null` and drop the `/ url` wording from the docstring (no behavior/assertion change; the `OSError` arm is already correctly pinned); or (b) **behavior** — add a focused mock of a storage whose `.url` raises `OSError`/`ValueError` to genuinely pin the `url`-degradation arm, if the spec's "`size` / `url` / `width` / `height` are nullable" intent (spec line 1345) is read as requiring each subfield's degradation be regression-guarded. (a) is sufficient for correctness and DRY-cleaner; (b) is the maximalist coverage-of-intent reading. The shipped code is correct under both — this is a test-label/coverage-breadth question, not a production defect, so it does not block acceptance.
- No spec gap, conflict, or unstated assumption surfaced in the export wiring. Decision 7 (three root exports, `UploadDefinition` module-only) and Decision 10 (version stays `0.0.10`; bump is Slice 4) both landed exactly. The planner's three-category hardening read ("storage-failure / null-blank / image-dimension" → only TWO genuine gaps after Slice 1, null/blank already covered) held — no redundant null/blank test was added and its absence is not a silently-unaddressed sub-check.
- Confirm at Slice 4 final verification (carry-forward, unchanged from Worker 2's note): `__version__` is STILL `"0.0.10"` and `test_version` byte-unchanged through this slice — verified TRUE here.

### Review outcome

**review-accepted.** Both verbatim Slice 3 sub-checks landed in the diff (the three root re-exports + `__all__` entries; the `test_init.py` export/`__all__` pins + the import-identity test; the two genuine-gap hardening tests). Exactly three root exports, `UploadDefinition` correctly module-only, `__all__` in true `sorted()` order with an exact-tuple pin, re-export identity non-vacuous. VERSION GUARD holds (`0.0.10` untouched, `test_version` byte-unchanged, Slice 4 reminder preserved). No High or Medium findings. One Low (test-name/docstring overstates the `url` arm) is escalated to Worker 1 with two resolution paths — it is a label/coverage-breadth question, not a production defect, so acceptance stands per the gate ("may set `review-accepted` WITH a Medium+ finding escalated"; this is below that bar — a Low — and is escalated only because the planner's and spec's "`.size`/`.url`" framing makes the wording a reconciliation call).

---

## Final verification (Worker 1)

Audited the verbatim sub-checks against the actual diff (`git diff -- django_strawberry_framework/__init__.py tests/base/test_init.py` + the two new appended functions in `tests/types/test_resolvers.py`), ran the focused gate, resolved Worker 3's escalated Low, and re-verified the VERSION GUARD and the standing P0 read/write split.

### 1. Spec slice checklist audit

The Plan's `### Spec slice checklist (verbatim)` carries two `- [x]` boxes; both contracts truly landed in the diff:

- **Box 1 — `__init__.py` re-exports `Upload` / `DjangoFileType` / `DjangoImageType` + `__all__`.** Confirmed in the diff: `Upload` folded into `from .scalars import BigInt, Upload, strawberry_config  # noqa: E402` (re-exported FROM `.scalars`, the one canonical site — not `strawberry.file_uploads.scalars` directly); `DjangoFileType` / `DjangoImageType` on a dedicated `from .types.converters import DjangoFileType, DjangoImageType  # noqa: E402` line adjacent to the `.types` import; all three added to `__all__` in true `sorted()` slots (`DjangoFileType`/`DjangoImageType` between `DjangoConnectionField` and `DjangoListField`; `Upload` between `SyncMisuseError` and `__version__`). Exactly three net-new root exports; `UploadDefinition` is NOT at the root (confirmed absent from both the import block and `__all__`). **Stays `- [x]`.**
- **Box 2 — `tests/base/test_init.py` public-export + `__all__` assertions add the three symbols; storage-failure / null-blank / image-dimension edge tests harden the synthetic-model coverage.** Confirmed: the `test_public_api_surface_is_pinned` exact-tuple gains the three literals in lockstep with the source; a new focused `test_file_upload_exports_resolve_to_their_source_definitions` pins re-export identity (`Upload is ScalarsUpload`, the two objects `is converters.*`); two new resolver tests in `tests/types/test_resolvers.py` harden the genuine gaps. The planner's three-category read (storage-failure / null-blank / image-dimension → only TWO genuine gaps after Slice 1, because null/blank is already fully covered by Slice 1's `test_convert_field_output_blank_and_null_widen_to_optional` / `..._force_nullable_overrides_blank_null`) is correct — re-testing null/blank would be a DRY defect, so its deliberate absence is NOT a silently-unaddressed sub-check. **Stays `- [x]`** (the contract landed; see §5 for the Low test-label correction it requires before final acceptance).

No box was over-ticked (every `- [x]` has matching implementation) and none was left un-ticked that landed. No `- [ ]` remains.

### 2. VERSION GUARD

- `__version__` is byte-unchanged at `"0.0.10"` — the diff does not touch the `__version__ = "0.0.10"` line.
- `tests/base/test_init.py::test_version` is **byte-unchanged**: its body is still `assert __version__ == "0.0.10"`. Verified mechanically — `git diff -U0` shows NO hunk touching the `def test_version()` body (the only nearby hunks are the file-top TODO-anchor rewrite and the comment/tuple edits *inside* `test_public_api_surface_is_pinned`). The Slice 4 bump (Decision 10) has not leaked. **GUARD HOLDS — no blocker.**

### 3. DRY check (Slice 3 + accepted Slices 1–2)

- **Re-exports follow the existing `__init__.py` convention, no parallel grouping.** `Upload` rides the existing `.scalars` import line (matching how `BigInt` rides through `.scalars`); the two output objects sit on one dedicated `.types.converters` line grouped with the sibling `.types` import. Worker 2 correctly did NOT add a net-new re-export to `types/__init__.py` solely to enable a single-line form (that would be unauthorized surface churn). No new import-grouping shape.
- **The two new tests reuse the Slice 1 synthetic-model fixtures (`_make_asset_model` / `_asset_type` / `_asset_schema` / `_tiny_png_bytes`) + the `schema_editor` + `override_settings(MEDIA_ROOT=tmp_path)` + `try/finally delete_model` harness — no new synthetic model.** The only new datum is the inline `ContentFile(b"not an image")` corrupt-image stand-in, correctly inline (not a reusable helper).
- **No re-test of null/blank already covered by Slice 1** (verified — neither new test touches the widen matrix or `force_nullable`).
- **Standing P0 read/write split still holds.** Re-confirmed: `Upload` never enters `FIELD_OUTPUT_TYPE_MAP`; the read output objects never reach the filter-input path; `SCALAR_MAP`'s `FileField: str` / `ImageField: str` rows are untouched by this slice (Slice 3 changes only `__init__.py` + tests — zero converter/scalar source change). No new duplication introduced across the three accepted slices.

### 4. Existing tests still pass

`uv run pytest tests/base/test_init.py tests/types/ --no-cov` → **403 passed, 2 skipped** (the 2 skips are pre-existing PostgreSQL-only scalar rows, unrelated to this slice). Focused scope, `--no-cov` as required; no `--cov*` flag used.

### 5. Resolution of Worker 3's escalated Low — `revision-needed` (label-only test edit, routed to Worker 2)

**Decision: option (a) — label-only rename/reword — is correct, and because it is a `.py` test edit I (Worker 1, final QA) do not make it; this sets `revision-needed` for a Worker 0 → Worker 2 apply-changes pass.** Rationale:

- **The finding is genuinely Low and the production code is correct.** `tests/types/test_resolvers.py::test_vanished_file_degrades_size_and_url_to_null` selects `{ assets { attachment { name size } } }` and asserts only `attachment["size"] is None` (+ `name` resolves). `url` is never selected or asserted. The name and docstring ("nulls `size` / `url`", "the `OSError` arm") overstate by naming `url`. Per BUILD.md severity defs this is Low: "comments or docstrings that are stale or wrong but not load-bearing."
- **Empirically re-verified Worker 3's claim** (`FileSystemStorage` over a real `override_settings(MEDIA_ROOT=...)` temp dir, `os.remove` the saved file, then read both): `.url` returns `/media/x.txt` and does **NOT** raise (it builds the URL from `MEDIA_URL` + name without touching disk), while `.size` raises `FileNotFoundError` (an `OSError` subclass). So on the real-deletion path a `url` selection resolves **non-null** — the test cannot honestly assert a `url` degradation here, and correctly does not. The label is the only defect.
- **Option (b) rejected as over-coverage.** `_safe_file_attr` (`django_strawberry_framework/types/converters.py::_safe_file_attr #"except (ValueError, OSError, NotImplementedError)"`) is a **single shared catch clause** consulted by every subfield resolver (`path` / `size` / `url` / `width` / `height`). The `OSError` / `ValueError` arm is already exercised by Test A via `.size`; the `url` subfield resolver routes through the byte-identical clause. Adding a contrived mock-storage test whose `.url` raises would pin no new production line — it would re-exercise one already-covered branch through a different attribute, contradicting the slice's own DRY posture and Decision 9's real-storage-over-mocks preference. The spec's Decision-4 intent (spec lines 995-1012, 1004) frames degradation as `.url` / `.size` → `OSError` / `ValueError` sharing one narrow catch and describes independent per-subfield degradation as a *design capability*, not a per-subfield behavioral-test mandate; the shared guard is honestly pinned. So (b) is the maximalist reading the spec does not require.
- **Directive for Worker 2 (apply-changes pass):** rename `tests/types/test_resolvers.py::test_vanished_file_degrades_size_and_url_to_null` → `test_vanished_file_degrades_size_to_null` and reword its docstring to describe ONLY the `.size` → `FileNotFoundError`/`OSError` arm (drop the `/ url` and the "nulls `size` / `url`" phrasing). **No test-expectation / assertion / selection change** — the assertion shape (`size` null, `name` resolves) is already correct. After Worker 2 lands the rename and Worker 3 re-reviews (no other findings outstanding), Worker 1 re-runs final verification to set `final-accepted`.

Why `revision-needed` rather than accept-as-a-known-minor: the inaccurate label is load-bearing as documentation of what the regression guard pins — a future reader could believe `url` degradation is regression-guarded when it is not. The fix is a pure, mechanical, zero-risk rename that costs one Worker 2 pass; the package is held to the highest standard (AGENTS.md), and a one-line honest-label fix is the root-cause correction, not a deferred follow-up. I am not editing the `.py` test myself (Worker 1 scope forbids editing tests).

### 6. Spec reconciliation

None. The spec status/header lines (lines 38-40) accurately read "Slices 1–2 final-accepted, Slices 3–4 pending" — Slice 3 is not yet final-accepted at this spawn, so the header is correct and needs no per-spawn refresh. The Decision-4 subfield-nullability language (spec lines 995-1012) already correctly describes the shared narrow catch (`.url` / `.size` → `OSError` / `ValueError`) and the production code matches it; the `url`-doesn't-raise reality is a property of `FileSystemStorage`, not a spec gap — the spec promises subfield *nullability* (a `T | None` type shape that degrades via the guard), which the code delivers. No spec edit warranted.

### Final status: `revision-needed`

The artifact's top-level `Status:` is set to `revision-needed`. One outstanding item: the label-only rename of `test_vanished_file_degrades_size_and_url_to_null` (§5). Everything else is verified-correct (exports, `__all__` lockstep, re-export identity, VERSION GUARD, DRY, focused tests green) and will not need re-touching.

### Summary

Slice 3 lifts the three file/upload symbols (`Upload`, `DjangoFileType`, `DjangoImageType`) onto the package-root public surface — exactly three net-new root exports, `UploadDefinition` correctly module-only, `__all__` in true `sorted()` order with an exact-tuple pin and a non-vacuous re-export-identity test — and hardens the synthetic-model coverage with two genuine-gap resolver tests (the `OSError`/`ValueError` `_safe_file_attr` arm via a vanished file's `.size`, and the image-dimension read-failure path via corrupt bytes). No production logic changed beyond the `__init__.py` import block. VERSION GUARD holds (`__version__` and `test_version` byte-unchanged at `0.0.10`; the bump is Slice 4). The slice is one mechanical test-label rename away from `final-accepted`: the test name/docstring claim a `url` degradation arm that, on the real-deletion path, `FileSystemStorage.url` cannot raise (verified empirically), so the test honestly pins only `.size`. Routed to Worker 2 as a label-only fix.

### Spec changes made (Worker 1 only)

None.

---

## Build report (Worker 2, pass 2)

Applied Worker 1's §5 directive (option a — label-only) verbatim: renamed the mislabeled hardening test and dropped the `url` wording from its docstring. No selection, assertion, or any other code changed. Scope was exactly this one mechanical fix; nothing else in the tree was touched by this pass.

### Files touched

- `tests/types/test_resolvers.py` — renamed the test function `test_vanished_file_degrades_size_and_url_to_null` → `test_vanished_file_degrades_size_to_null`, and changed its docstring first line from "A vanished-on-disk file nulls ``size`` / ``url`` (the ``OSError`` arm)." to "A vanished-on-disk file nulls ``size`` (the ``OSError`` arm)." — the only `url` mention in the function's name/docstring. The test body (the `os.remove(asset.attachment.path)` deletion, the `{ assets { attachment { name size } } }` selection, and the `assert attachment["size"] is None` / `assert attachment["name"].endswith("doc.txt")` assertions) is byte-unchanged. The rest of the file's dirtiness (the Slice 1 file/image block, the Slice 3 appended `test_corrupt_image_degrades_width_and_height_to_null`, fixtures) is accepted prior-slice work, untouched by this pass.

### Validation run

- `uv run ruff format .` — pass (287 files left unchanged; the standing `COM812`-with-formatter config warning is the repo's notice, not a failure). The label-only edit did not change line layout, so nothing reformatted.
- `uv run ruff check --fix .` — "All checks passed!" on the first run (the rename is a valid snake_case identifier; the docstring stays one line). No auto-fix churn.
- `git status --short` after both ruff invocations — the only NEW change from this pass is to `tests/types/test_resolvers.py` (already baseline-dirty from Slice 1/3; this pass adds the rename to it). The rest of the modified set (`django_strawberry_framework/*`, `scalars.py`, `types/*`, `pyproject.toml`, `uv.lock`, the spec edit, the other `tests/*` files) and the four `?? docs/builder/*.md` untracked artifacts are accepted prior-slice work — NOT reverted, NOT listed as mine. No unrelated tool churn appeared (ruff touched nothing); no `git checkout --` revert needed.
- Focused test (no `--cov*`): `uv run pytest tests/types/test_resolvers.py --no-cov -q` → 38 passed. The renamed `test_vanished_file_degrades_size_to_null` is green.
- Grep-sweep: `grep -rn "test_vanished_file_degrades_size_and_url_to_null"` over the whole tree finds the old name ONLY in this slice-3 artifact's prior (historical) sections — Build report (Worker 2), Review (Worker 3), Final verification (Worker 1) — which are append-only contract history I must not rewrite. NO live `.py` reference to the old name remains, so the rename orphans nothing. The new name `test_vanished_file_degrades_size_to_null` resolves at `tests/types/test_resolvers.py:1209`.

### Implementation notes

- Label-only, zero behavior change: the rename + the single docstring-line reword are the entire diff for this pass. No assertion, selection, fixture, marker, or production line was touched — the `.size` → `OSError`/`ValueError` arm the test already pinned is unchanged; only the name and docstring now match what it pins. Option (b) (a mock-storage `url`-raises test) was NOT added — Worker 1 rejected it as over-coverage (DRY + Decision 9; `_safe_file_attr`'s single shared catch is already exercised by the `.size` arm). The verbatim spec sub-checks remain `- [x]` (this pass changes no contract).

---

## Review (Worker 3, pass 2)

Narrow re-review of Worker 2's pass-2 label-only fix per Worker 1's §5 directive. Verified via `git diff -- tests/types/test_resolvers.py` (focusing on the renamed function), a repo-wide grep for the old name, and a focused test run. Did not re-litigate the already-accepted Slice 3 content (exports, `__all__` lockstep, re-export identity, VERSION GUARD, the two hardening tests) — confirmed only that the fix landed cleanly and introduced no regression.

### High:

None.

### Medium:

None.

### Low:

None. My prior Low (`test_vanished_file_degrades_size_and_url_to_null` name/docstring overstating the `url` arm) is **RESOLVED** by the rename. Confirmed in the diff: the function is now `def test_vanished_file_degrades_size_to_null(tmp_path)` and the docstring first line reads "A vanished-on-disk file nulls ``size`` (the ``OSError`` arm)." — the `/ url` and the "nulls `size` / `url`" phrasing are gone; `url` no longer appears anywhere in the function's name or docstring. The label now matches exactly what the test pins (`.size` → `FileNotFoundError`/`OSError`), so a future reader can no longer believe a `url` degradation is regression-guarded.

### What looks solid

- **The fix is byte-exact label-only, as directed.** The test BODY is unchanged: the `os.remove(asset.attachment.path)` deletion, the `{ assets { attachment { name size } } }` selection, and the `assert attachment["size"] is None` / `assert attachment["name"].endswith("doc.txt")` assertions are all intact. The `OSError`/`ValueError` arm of `_safe_file_attr` is still pinned via `.size` — option (b) (a contrived `url`-raises mock) correctly NOT added.
- **No orphaned reference to the old name.** `grep -rn test_vanished_file_degrades_size_and_url_to_null --include="*.py"` returns nothing; the old name survives only in this artifact's append-only historical sections (Build report W2 pass 1, Review W3 pass 1, Final verification W1) — never in live `.py`. The rename orphans nothing. The new name resolves at `tests/types/test_resolvers.py` (the renamed `def`).
- **No other Slice 3 file changed in this pass.** Pass 2's only new edit is to `tests/types/test_resolvers.py` (the rename + docstring). `django_strawberry_framework/__init__.py` and `tests/base/test_init.py` carry only their pass-1 Slice 3 diffs (unchanged this pass). The VERSION GUARD holds: `__version__ = "0.0.10"` (`__init__.py:38`) byte-unchanged and `tests/base/test_init.py::test_version` body still `assert __version__ == "0.0.10"` (`git diff -U0` shows no hunk touching the `test_version` body; the only `__version__`-matching diff line is the Slice 4 TODO-comment text). The Slice 4 bump (Decision 10) has not leaked.

### Temp test verification

None needed. The change is a pure mechanical rename + docstring reword with no behavior change; the assertion shape was already verified non-vacuous in pass 1's temp probes (now discarded). The focused run `uv run pytest tests/types/test_resolvers.py --no-cov` → **38 passed** (the renamed `test_vanished_file_degrades_size_to_null` is green). No `--cov*` flag used.

### Notes for Worker 1 (spec reconciliation)

- Nothing outstanding. My prior escalated Low is resolved by the label-only rename (option a), exactly as Worker 1's §5 directive specified; option (b) was correctly not pursued. No spec gap, conflict, or unstated assumption surfaced. The shipped production code was correct throughout — this was a test-label correction only.
- Carry-forward (unchanged): `__version__` is STILL `"0.0.10"` and `test_version` byte-unchanged through Slice 3 — re-verified TRUE this pass. The `0.0.11` cut remains Slice 4's exclusive job.

### Review outcome

**review-accepted.** Worker 2's pass-2 label-only fix landed cleanly: the test is renamed to `test_vanished_file_degrades_size_to_null`, the docstring no longer overstates `url`, and the test body (deletion + `{ name size }` selection + `size`-null / `name`-resolves assertions) is byte-unchanged — the `OSError`/`ValueError` arm of `_safe_file_attr` is still pinned via `.size`. No orphaned reference to the old name remains in any live `.py`. No other Slice 3 file changed this pass; the VERSION GUARD holds (`0.0.10`, `test_version` untouched). My prior Low is RESOLVED. No High/Medium/Low findings remain. The artifact's top-level `Status:` is set to `review-accepted`.

---

## Final verification (Worker 1, pass 2)

Re-verification after the apply-changes fix. My pass-1 final verification returned `revision-needed` for one label-only test rename (§5); Worker 2 (pass 2) applied it and Worker 3 (pass 2) re-accepted. This pass confirms the fix landed exactly, re-confirms the full Slice 3 contract still holds, runs the focused gate, reconciles the spec header, and sets `final-accepted`.

### 1. The §5 directive was applied exactly (verified via `git diff -- tests/types/test_resolvers.py` + grep + the renamed function body)

- **Function renamed.** `test_vanished_file_degrades_size_and_url_to_null` → `test_vanished_file_degrades_size_to_null`. The new name resolves at `tests/types/test_resolvers.py` (the renamed `def`, line 1209); a repo-wide `grep -rn "test_vanished_file_degrades_size_and_url_to_null" --include="*.py"` returns NOTHING — the old name survives only in this artifact's append-only historical sections (Build report W2 pass 1, Review W3 pass 1, Final verification W1 pass 1), never in live `.py`. The rename orphans nothing.
- **Docstring no longer overstates `url`.** The docstring first line is now "A vanished-on-disk file nulls ``size`` (the ``OSError`` arm)." — the `/ url` and the "nulls `size` / `url`" phrasing are gone; `url` appears nowhere in the function's name or docstring. The label now matches exactly what the test pins.
- **Test body byte-unchanged — the `OSError`/`ValueError` arm still pinned via `.size`.** Confirmed: the `os.remove(asset.attachment.path)` deletion, the `{ assets { attachment { name size } } }` selection, and the `assert attachment["size"] is None` / `assert attachment["name"].endswith("doc.txt")` assertions are all intact. No selection, assertion, fixture, marker, or production line changed. The vanished-file `.size` → `FileNotFoundError` (an `OSError` subclass) → `_safe_file_attr` degrade-to-null arm is still the thing this test pins.
- **No other Slice 3 file changed in pass 2.** `git diff --stat` shows the three Slice 3 files (`__init__.py`, `tests/base/test_init.py`, `tests/types/test_resolvers.py`); `__init__.py` and `test_init.py` carry only their pass-1 diffs (not re-touched in pass 2), and `test_resolvers.py`'s only new pass-2 edit is the rename + the one-line docstring reword. Worker 3 pass 2 confirmed the same.

### 2. Full Slice 3 contract re-confirmed

- **Both verbatim sub-checks `- [x]` and landed.** Box 1 (`__init__.py` re-exports `Upload` / `DjangoFileType` / `DjangoImageType` + `__all__`) and Box 2 (`tests/base/test_init.py` export/`__all__` pins + the storage-failure / image-dimension hardening tests) both have matching implementation in the diff. No over-tick, no silently un-ticked box, no remaining `- [ ]`. The deliberate absence of a null/blank re-test is NOT a silent gap (Slice 1's `test_convert_field_output_blank_and_null_widen_to_optional` / `..._force_nullable_overrides_blank_null` already cover it; re-testing would be a DRY defect).
- **Three root exports present with the exact-tuple `__all__` assertion.** Verified mechanically (`django.setup()` + import): `Upload` / `DjangoFileType` / `DjangoImageType` all in `__all__`; `list(__all__) == sorted(__all__)` is True (the three additions are in their true `sorted()` slots — `DjangoFileType`/`DjangoImageType` between `DjangoConnectionField` and `DjangoListField`; `Upload` between `SyncMisuseError` and `__version__`); `UploadDefinition` is NOT at the root; `Upload is strawberry.file_uploads.scalars.Upload` (rides the built-in registry, Decision 5). `test_public_api_surface_is_pinned` uses an exact-tuple equality pin, and `test_file_upload_exports_resolve_to_their_source_definitions` pins re-export identity — both confirmed in the diff.
- **VERSION GUARD holds.** `__version__ = "0.0.10"` byte-unchanged (`__init__.py:38`). `tests/base/test_init.py::test_version` body is still `assert __version__ == "0.0.10"` (line 22) — `git diff -U0 -- tests/base/test_init.py` shows the ONLY `0.0.11`-matching diff lines are the Slice 4 TODO-comment text and the surface-test comment; NO hunk touches the `def test_version()` body. The Slice 4 bump (Decision 10) has not leaked.
- **DRY + P0 read/write split intact.** Slice 3 touches only `__init__.py` + tests (zero converter/scalar source change), so the P0 split is structurally untouched: `Upload` never enters `FIELD_OUTPUT_TYPE_MAP`; the read output objects never reach the filter-input path; `SCALAR_MAP`'s `FileField: str` / `ImageField: str` rows are unchanged. The two hardening tests reuse the Slice 1 `_make_asset_model` / `_asset_type` / `_asset_schema` / `_tiny_png_bytes` fixtures + the `schema_editor` + `override_settings(MEDIA_ROOT=tmp_path)` + `try/finally delete_model` harness — no new synthetic model, no duplicated guard, the only new datum the inline `ContentFile(b"not an image")` corrupt-image stand-in.

### 3. Existing tests still pass

`uv run pytest tests/base/test_init.py tests/types/ --no-cov` → **403 passed, 2 skipped** (the 2 skips are pre-existing PostgreSQL-only scalar rows, unrelated to this slice). Focused scope, `--no-cov` as required; no `--cov*` flag used.

### 4. Spec reconciliation

Per-spawn status-line refresh made: spec line 39 advanced from "Slices 1–2 final-accepted, Slices 3–4 pending" to "Slices 1–3 final-accepted, Slice 4 pending", since this pass sets Slice 3 `final-accepted`. `scripts/check_spec_glossary.py --spec docs/spec-037-upload_file_image_mapping-0_0_11.md` re-run after the edit → exit 0 ("OK: 20 terms"). No other spec edit warranted — Decision 4's subfield-nullability language already correctly describes the shared narrow catch and the code matches it; the `url`-doesn't-raise reality is a `FileSystemStorage` property, not a spec gap (resolved by the label-only fix, not a spec change).

### Final status: `final-accepted`

The artifact's top-level `Status:` is set to `final-accepted`. The §5 directive (label-only rename + docstring reword) landed exactly — function renamed, docstring no longer overstates `url`, test body byte-unchanged with the `OSError`/`ValueError` arm still pinned via `.size`. The full Slice 3 contract holds: three root exports with the exact-tuple `__all__` pin and non-vacuous identity test, VERSION GUARD intact (`0.0.10`, `test_version` byte-unchanged), DRY + P0 split clean, focused gate green (403 passed, 2 pre-existing skips). No outstanding findings.

### Summary

Slice 3 lifts the three file/upload symbols (`Upload`, `DjangoFileType`, `DjangoImageType`) onto the package-root public surface — exactly three net-new root exports, `UploadDefinition` correctly module-only, `__all__` in true `sorted()` order with an exact-tuple pin and a non-vacuous re-export-identity test — and hardens the synthetic-model coverage with two genuine-gap resolver tests (the `OSError`/`ValueError` `_safe_file_attr` arm via a vanished file's `.size`, and the image-dimension read-failure path via corrupt bytes), reusing the Slice 1 fixtures with no new synthetic model. No production logic changed beyond the `__init__.py` import block (pure re-export). The pass-1 `revision-needed` Low — a test name/docstring that overstated a `url` degradation arm the test never selected or asserted — was fixed in pass 2 by a zero-risk label-only rename to `test_vanished_file_degrades_size_to_null` (Worker 2) and re-accepted (Worker 3); the test body and the `.size`-pinned `OSError` arm are byte-unchanged. VERSION GUARD held throughout (`__version__` and `test_version` byte-unchanged at `0.0.10`; the bump is Slice 4's exclusive job). Slice 3 is `final-accepted`.

### Spec changes made (Worker 1 only)

- `docs/spec-037-upload_file_image_mapping-0_0_11.md` line 39 — per-spawn status-line refresh: "Slices 1–2 final-accepted, Slices 3–4 pending" → "Slices 1–3 final-accepted, Slice 4 pending". Reason: this pass sets Slice 3 `final-accepted`, so the header must reflect reality (Worker 1 per-spawn status-line rule); catching it now avoids a stale header for the rest of the build. `scripts/check_spec_glossary.py` exits 0 after the edit.
