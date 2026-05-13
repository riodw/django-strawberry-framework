# Package build plan: relay_interfaces / 0.0.5

Spec source: `docs/spec-relay_interfaces.md`
Target release: `0.0.5`
Date created: 2026-05-13
Build rule: one slice at a time. Plan first, build second, review third, reconcile fourth.
DRY rule: every slice must justify shared/duplicated patterns before merging.

## Artifact list

- `docs/build/bld-slice-1-validation_and_storage.md`
- `docs/build/bld-slice-2-is_type_of_injection.md`
- `docs/build/bld-slice-3-id_suppression.md`
- `docs/build/bld-slice-4-interface_injection_and_relay_resolvers.md`
- `docs/build/bld-slice-5-promotion_docs_version.md`
- `docs/build/bld-integration.md`
- `docs/build/bld-final.md`

## Checklist

- [x] Slice 1: Validation + storage -> `docs/build/bld-slice-1-validation_and_storage.md`
- [x] Slice 2: `is_type_of` injection -> `docs/build/bld-slice-2-is_type_of_injection.md`
- [x] Slice 3: `id` suppression -> `docs/build/bld-slice-3-id_suppression.md`
- [x] Slice 4: Interface base-class injection + Relay resolver defaults -> `docs/build/bld-slice-4-interface_injection_and_relay_resolvers.md`
- [x] Slice 5: Promotion + docs + version -> `docs/build/bld-slice-5-promotion_docs_version.md`
- [x] Cross-slice integration pass -> `docs/build/bld-integration.md`
- [x] Final test-run gate -> `docs/build/bld-final.md`
