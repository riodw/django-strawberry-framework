# Package build plan: orders / 0.0.8 (028)

Spec source: `docs/spec-028-orders-0_0_8.md`
Target release: `0.0.8` (no package-version-file edits unless the maintainer explicitly gives the version-bump command; see Decision 10)
Date created: 2026-06-01

Pre-flight: passed on 2026-06-01; baseline: dirty (out-of-scope changes recorded below); cleanup: old `build-021-filters-0_0_8.md` removed, `docs/shadow/` cleared, `docs/builder/temp-tests/` and `docs/builder/worker-memory/` already empty (about to be seeded).

Baseline-dirty out-of-scope files (workers MUST NOT edit, MUST NOT revert; recorded per the maintainer's "Treat as baseline-dirty out-of-scope" instruction at plan creation time; updated mid-build when maintainer concurrent work surfaces additional files per AGENTS.md "Unexpected file modifications"):

- `TODAY.md`
- `django_strawberry_framework/management/commands/export_schema.py`
- `django_strawberry_framework/optimizer/_context.py` (surfaced mid-build via maintainer concurrent work)
- `django_strawberry_framework/optimizer/extension.py` (surfaced mid-build via maintainer concurrent work)
- `docs/GLOSSARY.md`
- `docs/TREE.md`
- `docs/review/rev-filters.md`
- `docs/review/review-0_0_7.md`
- `docs/review/rev-management.md` (untracked)
- `docs/review/rev-management__commands.md` (untracked)
- `docs/review/rev-management__commands__export_schema.md` (untracked)
- `docs/review/rev-optimizer___context.md` (untracked)
- `docs/review/rev-optimizer__extension.md` (untracked; surfaced mid-build)
- `django_strawberry_framework/optimizer/field_meta.py` (surfaced mid-build via maintainer concurrent work)
- `django_strawberry_framework/optimizer/hints.py` (surfaced mid-build via maintainer concurrent work)
- `docs/GLOSSARY2.md` (untracked; surfaced mid-build)
- `docs/review/rev-optimizer__field_meta.md` (untracked; surfaced mid-build)
- `docs/review/rev-optimizer__hints.md` (untracked; surfaced mid-build)
- `scripts/build_glossary_md.py` (surfaced mid-build via maintainer concurrent work)
- `django_strawberry_framework/optimizer/plans.py` (surfaced mid-build via maintainer concurrent work)
- `django_strawberry_framework/optimizer/walker.py` (surfaced mid-build via maintainer concurrent work)
- `tests/optimizer/test_walker.py` (surfaced mid-build via maintainer concurrent work)
- `examples/fakeshop/apps/glossary/admin.py` (surfaced mid-build)
- `examples/fakeshop/apps/glossary/filters.py` (surfaced mid-build)
- `examples/fakeshop/apps/glossary/models.py` (surfaced mid-build)
- `examples/fakeshop/apps/glossary/schema.py` (surfaced mid-build)
- `examples/fakeshop/apps/kanban/admin.py` (surfaced mid-build)
- `examples/fakeshop/apps/kanban/filters.py` (surfaced mid-build)
- `examples/fakeshop/apps/kanban/models.py` (surfaced mid-build)
- `examples/fakeshop/apps/kanban/schema.py` (surfaced mid-build)
- `examples/fakeshop/test_query/test_glossary_api.py` (surfaced mid-build)
- `examples/fakeshop/README.md`
- `examples/fakeshop/apps/glossary/migrations/0001_initial.py`
- `examples/fakeshop/db.sqlite3`
- `scripts/import_glossary_md.py`

Pre-flight deletions (expected, not a workers-must-revert state):

- `docs/builder/build-021-filters-0_0_8.md` (deleted by pre-flight #3 cleanup of prior-cycle artifacts; the tracked file shows as `D` in `git status` until the maintainer commits)

Slice 5 must still edit `docs/GLOSSARY.md`, `docs/TREE.md`, and `TODAY.md` (per the spec's Slice 5 contract). Worker 1 / Worker 2 / Worker 3 should treat those three files as in-scope for Slice 5 only and additive (do not revert maintainer changes already in the working tree at plan time; layer Slice 5's diffs on top). The other baseline-dirty paths are strictly out of scope for every slice.

Build-wide context flags:

- **No version bump in this card.** `pyproject.toml`, `django_strawberry_framework/__init__.py::__version__`, `tests/base/test_init.py::test_version`, and `CHANGELOG.md` release-heading promotion are all explicitly forbidden unless the maintainer gives the version-bump command (Spec Decision 10 / Revision 5). Workers do not touch version fields and do not promote `[Unreleased]`. Slice 5 may append `### Added` / `### Changed` bullets under `[Unreleased]`.
- **CHANGELOG-edit permission.** Slice 5 carries the spec's explicit-instruction permission to edit `CHANGELOG.md` per AGENTS.md "Do not update CHANGELOG.md unless explicitly instructed". No other slice may touch the changelog.
- **Filter subsystem is shipped.** Five of six lazy-resolution layers port verbatim from `django_strawberry_framework/filters/`. Workers should mirror the shipped filter shape one-for-one — every divergence is a finding.
- **Shared mixins live in the neutral module.** `django_strawberry_framework/sets_mixins.py` already carries `LazyRelatedClassMixin` and `ClassBasedTypeNameMixin`. `orders/base.py` and `orders/sets.py` import from `sets_mixins`, NOT from `filters/base.py` (Spec Revision 4 H1).
- **Coverage is the maintainer's gate.** Workers never run `pytest --cov*`. The only permitted coverage-shaped flag is `--no-cov` to opt out of `pytest.ini`'s auto-applied `--cov`.
- **Composition slice (6) ships in THIS card.** The filter spec's "carried by sibling" Slice 6 is satisfied here.

## Rules in force

- **One slice at a time.** Plan → build → review → final-verification → next slice. No starting Slice N+1 before Slice N's artifact reaches `final-accepted`.
- **DRY first.** Worker 1 plans for DRY before code is written; Worker 3 enforces DRY before code is accepted; Worker 1 re-checks DRY at the integration pass.
- **Workers never commit.** Only the maintainer commits, even if asked.

## Artifact list

- `docs/builder/bld-slice-1-foundation.md`
- `docs/builder/bld-slice-2-factories.md`
- `docs/builder/bld-slice-3-wiring.md`
- `docs/builder/bld-slice-4-live_http.md`
- `docs/builder/bld-slice-5-docs_kanban_changelog.md`
- `docs/builder/bld-slice-6-composition_smoke.md`
- `docs/builder/bld-integration.md`
- `docs/builder/bld-final.md`

## Checklist

- [x] Slice 1: Foundation — module layout + `Order` / `RelatedOrder` primitives + `OrderSet` metaclass -> `docs/builder/bld-slice-1-foundation.md`
- [x] Slice 2: Factories — `OrderArgumentsFactory` BFS + inputs adapters -> `docs/builder/bld-slice-2-factories.md`
- [x] Slice 3: Wiring — `Meta.orderset_class` promotion + finalizer phase 2.5 binding -> `docs/builder/bld-slice-3-wiring.md`
- [x] Slice 4: Live HTTP coverage in fakeshop (exactly 14 new `/graphql/` tests) -> `docs/builder/bld-slice-4-live_http.md`
- [x] Slice 5: Docs + KANBAN + CHANGELOG status updates (no version bump) -> `docs/builder/bld-slice-5-docs_kanban_changelog.md`
- [x] Slice 6: Cross-card composition smoke test with shipped Filtering subsystem -> `docs/builder/bld-slice-6-composition_smoke.md`
- [x] Cross-slice integration pass -> `docs/builder/bld-integration.md`
- [ ] Final test-run gate -> `docs/builder/bld-final.md`
