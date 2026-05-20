# Package build plan: consumer_overrides_scalar / 0.0.6 (015)

Spec source: `docs/spec-015-consumer_overrides_scalar-0_0_6.md`
Target release: `0.0.6`
Date created: 2026-05-19
Build rule: one slice at a time. Plan first, build second, review third, reconcile fourth.
DRY rule: every slice must justify shared/duplicated patterns before merging.
Pre-flight: passed on 2026-05-19 after archiving build-014 artifacts; baseline: clean (after `git rm` of `build-014-meta_primary-0_0_6.md`, `bld-integration.md`, `bld-final.md`, and the six build-014 `bld-slice-*.md` artifacts — committed by maintainer alongside this plan, per pre-flight check 3 and the precedent commit 6407e91 for spec-013 archival; helper smoke `scripts/review_inspect.py django_strawberry_framework/optimizer/walker.py --output-dir docs/shadow --stdout` produced overview and stripped shadow file; `.gitignore` already lists `docs/builder/worker-memory/`, `docs/shadow/`, and `docs/builder/temp-tests/`; scratch directories empty or to-be-recreated; planned artifact names now free).

## Artifact list

- `docs/builder/bld-slice-1-annotation_scalar_overrides.md`
- `docs/builder/bld-slice-2-unskip_consumer_annotation_test.md`
- `docs/builder/bld-slice-3-document_override_contract.md`
- `docs/builder/bld-slice-4-version_bump_quintet.md`
- `docs/builder/bld-slice-5-docs_kanban_changelog_archive.md`
- `docs/builder/bld-integration.md`
- `docs/builder/bld-final.md`

## Checklist

- [x] Slice 1: Track annotation-only scalar overrides on `DjangoTypeDefinition` -> `docs/builder/bld-slice-1-annotation_scalar_overrides.md`
- [x] Slice 2: Unskip / replace `test_consumer_annotation_overrides_synthesized` -> `docs/builder/bld-slice-2-unskip_consumer_annotation_test.md`
- [x] Slice 3: Document the four-corner override contract in `_consumer_assigned_fields`'s docstring -> `docs/builder/bld-slice-3-document_override_contract.md`
- [x] Slice 4: Atomic version-bump quintet (single commit) -> `docs/builder/bld-slice-4-version_bump_quintet.md`
- [x] Slice 5: Docs, KANBAN, CHANGELOG, archive (separate commit; may follow Slice 4 by any interval) -> `docs/builder/bld-slice-5-docs_kanban_changelog_archive.md`
- [x] Cross-slice integration pass -> `docs/builder/bld-integration.md`
- [x] Final test-run gate -> `docs/builder/bld-final.md`
