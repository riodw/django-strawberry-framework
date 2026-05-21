# Package build plan: apps / 0.0.7 (017)

Spec source: `docs/SPECS/spec-017-apps-0_0_7.md`
Target release: `0.0.7`
Date created: 2026-05-21
Pre-flight: passed on 2026-05-21; baseline: clean; cleanup: old build-016 artifacts removed, memory/shadow/temp-tests cleared.
Build rule: one slice at a time. Plan first, build second, review third, reconcile fourth.
DRY rule: every plan, every implementation, every review pass must answer "is this the maximally DRY shape that stays readable?" before code is accepted.

## Artifact list

- `docs/builder/bld-slice-1-module_appconfig.md`
- `docs/builder/bld-slice-2-tests.md`
- `docs/builder/bld-slice-3-promotion_docs.md`
- `docs/builder/bld-integration.md`
- `docs/builder/bld-final.md`

## Checklist

- [x] Slice 1: Module + `AppConfig` subclass -> `docs/builder/bld-slice-1-module_appconfig.md`
- [x] Slice 2: Tests -> `docs/builder/bld-slice-2-tests.md`
- [x] Slice 3: Promotion + docs -> `docs/builder/bld-slice-3-promotion_docs.md`
- [x] Cross-slice integration pass -> `docs/builder/bld-integration.md`
- [x] Final test-run gate -> `docs/builder/bld-final.md`
