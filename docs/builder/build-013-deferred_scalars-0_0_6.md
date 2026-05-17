# Package build plan: deferred_scalars / 0.0.6

Spec source: `docs/spec-013-deferred_scalars-0_0_6.md`
Target release: `0.0.6`
Date created: 2026-05-17
Build rule: one slice at a time. Plan first, build second, review third, reconcile fourth.
DRY rule: every slice must justify shared/duplicated patterns before merging.
Pre-flight: passed on 2026-05-17; baseline: `docs/builder/BUILD.md` modification intentionally included (workflow-doc refinement only — adds the baseline pre-flight rule, switches helper smoke to `uv run python`, adds the documentation/release-sanity review section, loosens integration-pass helper-skip language; no source-tree impact). Working tree otherwise clean. Stale empty worker-memory files re-seeded fresh.

## Artifact list

- `docs/builder/bld-slice-1-bigint_scalar.md`
- `docs/builder/bld-slice-2-jsonfield.md`
- `docs/builder/bld-slice-3-arrayfield.md`
- `docs/builder/bld-slice-4-hstorefield.md`
- `docs/builder/bld-slice-5-version_bump.md`
- `docs/builder/bld-slice-6-docs_archive.md`
- `docs/builder/bld-integration.md`
- `docs/builder/bld-final.md`

## Checklist

- [x] Slice 1: `BigInt` scalar + 64-bit integer field mappings -> `docs/builder/bld-slice-1-bigint_scalar.md`
- [x] Slice 2: `JSONField` mapping -> `docs/builder/bld-slice-2-jsonfield.md`
- [x] Slice 3: `ArrayField` recursion (sentinel-based) -> `docs/builder/bld-slice-3-arrayfield.md`
- [x] Slice 4: `HStoreField` conditional registration via sentinel + `strawberry.scalars.JSON` target -> `docs/builder/bld-slice-4-hstorefield.md`
- [x] Slice 5: Atomic version-bump quintet (single commit) -> `docs/builder/bld-slice-5-version_bump.md`
- [x] Slice 6: Docs, KANBAN, CHANGELOG, archive -> `docs/builder/bld-slice-6-docs_archive.md`
- [x] Cross-slice integration pass -> `docs/builder/bld-integration.md`
- [x] Final test-run gate -> `docs/builder/bld-final.md`
