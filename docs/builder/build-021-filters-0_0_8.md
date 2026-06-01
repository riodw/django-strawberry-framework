# Package build plan: filters / 0.0.8 (021)

Spec source: `docs/spec-027-filters-0_0_8.md`
Target release: `0.0.8`
Date created: 2026-05-28
Build rule: one slice at a time. Plan first, build second, review third, reconcile fourth.
DRY rule: every slice must justify shared/duplicated patterns before merging. Worker 1 plans for DRY; Worker 3 enforces DRY; Worker 1 re-checks DRY across slices at the integration pass.
Pre-flight: passed on 2026-05-28; baseline: `M docs/feedback.md` present at task start, treated as the maintainer's in-progress review-iteration scratchpad per AGENTS.md ("Unexpected file modifications... are presumptively the maintainer's or another dev's in-progress work...ignore them as out-of-scope") — explicitly out of scope for this build; cleanup: no prior `build-*.md` or `bld-*.md` artifacts existed (clean slate), `docs/shadow/`, `docs/builder/worker-memory/`, and `docs/builder/temp-tests/` cleared, four empty worker-memory files re-seeded.

## Artifact list

- `docs/builder/bld-slice-1-foundation.md`
- `docs/builder/bld-slice-2-factories.md`
- `docs/builder/bld-slice-3-wiring.md`
- `docs/builder/bld-slice-4-live_http_coverage.md`
- `docs/builder/bld-slice-4a-tree_form_logic.md`
- `docs/builder/bld-slice-5-docs_kanban_changelog.md`
- `docs/builder/bld-slice-6-composition_smoke_test.md`
- `docs/builder/bld-integration.md`
- `docs/builder/bld-final.md`

## Checklist

- [x] Slice 1: Foundation — module layout + `Filter` primitives + `FilterSet` metaclass -> `docs/builder/bld-slice-1-foundation.md`
- [x] Slice 2: Factories — `FilterArgumentsFactory` BFS + dynamic-filterset cache -> `docs/builder/bld-slice-2-factories.md`
- [x] Slice 3: Wiring — `Meta.filterset_class` promotion + finalizer phase 2.5 binding -> `docs/builder/bld-slice-3-wiring.md`
- [x] Slice 4: Live HTTP coverage in fakeshop -> `docs/builder/bld-slice-4-live_http_coverage.md`
- [x] Slice 4a: Tree-form logic substrate — `FilterSet.filter_queryset` `django-filter` instance-method override -> `docs/builder/bld-slice-4a-tree_form_logic.md`
- [x] Slice 5: Docs + KANBAN + CHANGELOG -> `docs/builder/bld-slice-5-docs_kanban_changelog.md`
- [x] Slice 6: Sibling-card composition smoke tests (held until after `WIP-ALPHA-022-0.0.8` ships) -> `docs/builder/bld-slice-6-composition_smoke_test.md`
- [x] Cross-slice integration pass -> `docs/builder/bld-integration.md`
- [x] Final test-run gate -> `docs/builder/bld-final.md`
