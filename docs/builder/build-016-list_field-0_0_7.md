# Package build plan: list_field / 0.0.7 (016)

Spec source: `docs/spec-016-list_field-0_0_7.md`
Target release: `0.0.7`
Date created: 2026-05-20
Build rule: one slice at a time. Plan first, build second, review third, reconcile fourth. Do not start the next slice until the current slice's plan/build/review/verification/spec-reconciliation cycle is complete.
DRY rule: every plan, every implementation, every review pass must answer one question before anything else — is this the maximally DRY shape that stays readable? Worker 1 plans for DRY before code is written; Worker 3 enforces DRY before code is accepted; Worker 1 re-checks DRY across slices at the integration pass.
Pre-flight: passed on 2026-05-20; baseline: clean (`git status --short` empty); cleanup: old spec-015 build artifacts removed (`build-015-*.md` + six `bld-*.md`), `docs/builder/worker-memory/`, `docs/shadow/`, and `docs/builder/temp-tests/` cleared and re-seeded empty; `scripts/review_inspect.py` smoke run against `django_strawberry_framework/conf.py` succeeded; `.gitignore` confirmed to list `docs/builder/worker-memory/`, `docs/shadow/`, and `docs/builder/temp-tests/`.

## Artifact list

- `docs/builder/bld-slice-0-preimpl_verification.md`
- `docs/builder/bld-slice-1-module_factory.md`
- `docs/builder/bld-slice-2-validation.md`
- `docs/builder/bld-slice-3-optimizer_get_queryset_tests.md`
- `docs/builder/bld-slice-4-live_http_coverage.md`
- `docs/builder/bld-slice-5-promotion_docs_version.md`
- `docs/builder/bld-integration.md`
- `docs/builder/bld-final.md`

## Checklist

- [x] Slice 0: Pre-implementation verification (rev3 H1; no code lands; throw-away spike) -> `docs/builder/bld-slice-0-preimpl_verification.md`
- [x] Slice 1: Module + factory function -> `docs/builder/bld-slice-1-module_factory.md`
- [x] Slice 2: Validation -> `docs/builder/bld-slice-2-validation.md`
- [x] Slice 3: Optimizer + `get_queryset` cooperation tests -> `docs/builder/bld-slice-3-optimizer_get_queryset_tests.md`
- [x] Slice 4: Live HTTP coverage -> `docs/builder/bld-slice-4-live_http_coverage.md`
- [x] Slice 5: Promotion + docs + version -> `docs/builder/bld-slice-5-promotion_docs_version.md`
- [x] Cross-slice integration pass -> `docs/builder/bld-integration.md`
- [x] Final test-run gate -> `docs/builder/bld-final.md`
