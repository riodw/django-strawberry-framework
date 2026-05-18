# Package build plan: meta_primary / 0.0.6 (014)

Spec source: `docs/spec-014-meta_primary-0_0_6.md`
Target release: `0.0.6`
Build rule: one slice at a time. Plan first, build second, review third, reconcile fourth.
DRY rule: every slice must justify shared/duplicated patterns before merging.
Pre-flight: passed on 2026-05-18; baseline: clean.

## Pre-flight notes

1. **Working-tree baseline.** `git status --short` returns empty; tree clean. No uncommitted changes to reconcile against the build baseline.
2. **`scripts/review_inspect.py` smoke.** `uv run python scripts/review_inspect.py django_strawberry_framework/registry.py --output-dir docs/builder/shadow --stdout` prints the static overview and writes the shadow file under `docs/builder/shadow/`.
3. **Artifact name availability.** None of the planned `build-014-meta_primary-0_0_6.md`, `bld-slice-1-…` through `bld-slice-6-…`, `bld-integration.md`, or `bld-final.md` files exist at plan time.
4. **`.gitignore` scratch paths.** `docs/builder/worker-memory/`, `docs/builder/shadow/`, and `docs/builder/temp-tests/` are all listed.
5. **Scratch directories.** `shadow/` and `temp-tests/` are empty. `worker-memory/` carried over the four worker memory files from a prior cycle; Worker 0 truncates them at plan time per BUILD.md "Lifecycle".

## Artifact list

- `docs/builder/bld-slice-1-registry_multitype.md`
- `docs/builder/bld-slice-2-meta_primary_recognition.md`
- `docs/builder/bld-slice-3-ambiguity_audit.md`
- `docs/builder/bld-slice-4-consumer_site_updates.md`
- `docs/builder/bld-slice-5-version_bump.md`
- `docs/builder/bld-slice-6-docs_kanban_archive.md`
- `docs/builder/bld-integration.md`
- `docs/builder/bld-final.md`

## Checklist

- [x] Slice 1: Registry multi-type storage + primary tracking -> `docs/builder/bld-slice-1-registry_multitype.md`
- [x] Slice 2: `Meta.primary` recognition in `DjangoType.__init_subclass__` -> `docs/builder/bld-slice-2-meta_primary_recognition.md`
- [x] Slice 3: Cross-type ambiguity audit at finalization -> `docs/builder/bld-slice-3-ambiguity_audit.md`
- [x] Slice 4: Consumer-site updates (relation conversion + optimizer) -> `docs/builder/bld-slice-4-consumer_site_updates.md`
- [x] Slice 5: Atomic version-bump quintet (single commit) -> `docs/builder/bld-slice-5-version_bump.md`
- [x] Slice 6: Docs, KANBAN, CHANGELOG, archive -> `docs/builder/bld-slice-6-docs_kanban_archive.md`
- [x] Cross-slice integration pass -> `docs/builder/bld-integration.md`
- [x] Final test-run gate -> `docs/builder/bld-final.md`
