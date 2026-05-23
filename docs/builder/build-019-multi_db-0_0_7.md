# Package build plan: multi_db / 0.0.7 (019)

Spec source: `docs/spec-019-multi_db-0_0_7.md`
Target release: `0.0.7`
Date created: 2026-05-22
Build rule: one slice at a time. Plan first, build second, review third, reconcile fourth. Do not start the next slice until the current slice is `final-accepted`.
DRY rule: every slice — and the integration pass — must justify shared or duplicated patterns before merging. Worker 1 plans for DRY, Worker 3 enforces it, Worker 1 re-checks across slices.
Pre-flight: passed on 2026-05-22; baseline: clean (`git status --short` empty at plan time); cleanup: deleted prior build plan `docs/builder/build-018-export_schema-0_0_7.md` and its `bld-*.md` artifacts (`bld-slice-1-module.md`, `bld-slice-2-tests.md`, `bld-slice-3-promotion_docs.md`, `bld-integration.md`, `bld-final.md`); recreated `docs/builder/worker-memory/` and seeded `worker-0.md` / `worker-1.md` / `worker-2.md` / `worker-3.md` empty; cleared `docs/shadow/` and `docs/builder/temp-tests/`; `review_inspect.py` smoke invocation against `django_strawberry_framework/types/resolvers.py` succeeded.

## Artifact list

- `docs/builder/bld-slice-1-package_tests.md`
- `docs/builder/bld-slice-2-fakeshop_live.md`
- `docs/builder/bld-slice-3-promotion_docs.md`
- `docs/builder/bld-integration.md`
- `docs/builder/bld-final.md`

## Checklist

- [x] Slice 1: Package-internal tests (extend `tests/types/test_resolvers.py` with five resolver-level tests; new `tests/optimizer/test_multi_db.py` with two optimizer-plan-level tests) -> `docs/builder/bld-slice-1-package_tests.md`
- [x] Slice 2: Fakeshop live coverage under `FAKESHOP_SHARDED=1` (new `examples/fakeshop/test_query/test_multi_db.py` with two live `/graphql/` HTTP tests, holder-pattern URLConf, `Branch → Shelf → Book` seeding) -> `docs/builder/bld-slice-2-fakeshop_live.md`
- [x] Slice 3: Promotion + docs (flip `Multi-database cooperation` to `shipped (0.0.7)` in `docs/GLOSSARY.md`; one-line forward-pointer in `docs/README.md`; move `WIP-ALPHA-019-0.0.7` to Done in `KANBAN.md`; append fourth bullet under `[0.0.7]` `### Added` in `CHANGELOG.md`; NO version bump per Decision 9 joint cut; no public-surface change; final ruff/pytest gates) -> `docs/builder/bld-slice-3-promotion_docs.md`
- [x] Cross-slice integration pass -> `docs/builder/bld-integration.md`
- [x] Final test-run gate -> `docs/builder/bld-final.md`
