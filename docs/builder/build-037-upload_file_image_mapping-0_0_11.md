# Package build plan: upload_file_image_mapping / 0.0.11 (037)

Spec source: `docs/spec-037-upload_file_image_mapping-0_0_11.md`
Target release: `0.0.11`
Date created: 2026-06-19
Build rule: one slice at a time. Plan first (Worker 1), build second (Worker 2), review third (Worker 3), reconcile fourth (Worker 1 final verification). Do not start the next slice until the current slice reaches `final-accepted`.
DRY rule: every plan, every implementation, every review pass answers first — is this the maximally DRY shape that stays readable? Duplicated logic, parallel data flows, near-copies between modules, and repeated string/key/tuple literals are build-time defects. Worker 1 plans for DRY; Worker 3 enforces it; Worker 1 re-checks across slices at integration.

Pre-flight: passed on 2026-06-19; baseline: clean (`git status --short` empty); cleanup: no old `build-*.md`/`bld-*.md` artifacts existed; `docs/builder/worker-memory/`, `docs/shadow/`, `docs/builder/temp-tests/` confirmed empty (shadow output from the `review_inspect.py` smoke test was removed after the check). `scripts/review_inspect.py` smoke ran clean (exit 0). `scripts/check_spec_glossary.py --spec docs/spec-037-upload_file_image_mapping-0_0_11.md` exits 0 ("OK: 20 terms").

Baseline-dirty out-of-scope files: none (working tree was clean at baseline). Workers neither edit nor revert anything outside their slice's scope.

## Build-wide context flags

- **Version-bump owner: THIS card.** `037` is the lone active `0.0.11` WIP card and `036` is already `DONE`; `036` deferred the patch bump to the joint cut, which lands in Slice 4 (Decision 10). Slice 4 moves `pyproject.toml`, `__version__` in `__init__.py`, `tests/base/test_init.py::test_version`, the `docs/GLOSSARY.md` package-version line, and `uv.lock` (if it carries the package version) to `0.0.11`. Version-bump correctness is the maintainer's responsibility, not a worker gate.
- **Read/write contract split.** The read side returns structured `DjangoFileType` / `DjangoImageType` output objects via a NEW `FIELD_OUTPUT_TYPE_MAP` kept OFF the shared `SCALAR_MAP` / filter-input path; the write side maps `FileField` / `ImageField` to the `Upload` scalar. `SCALAR_MAP`'s `FileField: str` / `ImageField: str` rows stay in place (the filter-input path is unaffected). Neither side leaks the other's representation. This split is the P0 invariant Worker 3 must guard each slice.
- **`Upload` needs no registration.** `Upload` is a Strawberry built-in already in `DEFAULT_SCALAR_REGISTRY`; the package only RE-EXPORTS it — no `_PACKAGE_SCALAR_MAP` entry (contrast with the package-custom `BigInt`).
- **CHANGELOG permission gate.** Per `AGENTS.md` #"Do not update CHANGELOG.md unless explicitly instructed", the Slice 4 `CHANGELOG.md` edit may only be made if the maintainer's Slice 4 dispatch prompt explicitly requests it. The spec describes the edit but cannot grant the permission.
- **DB-backed generated docs.** `KANBAN.md`, `KANBAN.html`, `docs/GLOSSARY.md` are RENDERED from `examples/fakeshop/db.sqlite3`. Slice 4 edits the DB via the Django ORM then regenerates — never hand-edits the rendered markdown. See `docs/builder/worker-0.md` "Closing out a kanban card".
- **No example file/image column exists.** `grep -rln "FileField\|ImageField" examples/` returns nothing, so the read-side wire-format break invalidates no in-repo schema and synthetic-model tests are the correct coverage strategy (Decision 9). Live `/graphql/` coverage is added only if a real fakeshop file column later exists.

## One-slice-at-a-time rule (short copy)

Build exactly one slice at a time, in the spec's declared order. Do not start the next slice until the current slice's plan → build → review → final-verification → spec-reconciliation cycle is complete and Worker 1 set the artifact to `final-accepted`. After all in-spec slices are built, run the cross-slice integration pass, then the final test-run gate.

## DRY-first rule (short copy)

Before any plan/implementation/review is accepted, answer: is this the maximally DRY shape that stays readable? `_safe_file_attr` is the single subfield guard shared across both output types; `convert_field_output` is the single read-output wrapper delegating to `convert_scalar`. Watch for: a second copy of the empty-file guard, a parallel file-resolver attachment path, repeated `("name", "path", "size", "url")` literals, and any drift of file logic into the scalar/filter-input path.

## Artifact list

- `docs/builder/bld-slice-1-read_output_objects.md`
- `docs/builder/bld-slice-2-write_upload_input.md`
- `docs/builder/bld-slice-3-exports_coverage.md`
- `docs/builder/bld-slice-4-docs_version_cut.md`
- `docs/builder/bld-integration.md`
- `docs/builder/bld-final.md`

## Checklist

- [x] Slice 1: read-side output objects + the `FIELD_OUTPUT_TYPE_MAP` read map + the file-column resolver (spec `## Slice checklist` Slice 1; Decision 3 / Decision 4) -> `docs/builder/bld-slice-1-read_output_objects.md`
- [x] Slice 2: write-side `Upload` input + the `Upload` re-export (spec `## Slice checklist` Slice 2; Decision 5 / Decision 6) -> `docs/builder/bld-slice-2-write_upload_input.md`
- [x] Slice 3: public exports + coverage hardening (spec `## Slice checklist` Slice 3; Decision 7 / Decision 9) -> `docs/builder/bld-slice-3-exports_coverage.md`
- [x] Slice 4: docs + the `0.0.11` version cut + card wrap (spec `## Slice checklist` Slice 4; Doc updates / Decision 10) -> `docs/builder/bld-slice-4-docs_version_cut.md`
- [x] Cross-slice integration pass -> `docs/builder/bld-integration.md`
- [x] Final test-run gate -> `docs/builder/bld-final.md`
