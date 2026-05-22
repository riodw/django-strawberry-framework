# Package build plan: export_schema / 0.0.7 (018)

Spec source: `docs/SPECS/spec-018-export_schema-0_0_7.md`
Target release: `0.0.7`
Date created: 2026-05-22
Build rule: one slice at a time. Plan first, build second, review third, reconcile fourth.
DRY rule: every slice must justify shared/duplicated patterns before merging.
Pre-flight: passed on 2026-05-22; baseline: `M docs/feedback.md` recorded as out-of-scope maintainer working file (spec revision history cites it as the feedback source for revs 1-5; presumptively maintainer's in-progress work per `AGENTS.md` line 31; workers must not touch it). `scripts/review_inspect.py` smoke-tested against `django_strawberry_framework/list_field.py`; cleanup: old `build-017-apps-0_0_7.md` and `bld-*.md` artifacts removed; `docs/builder/worker-memory/`, `docs/shadow/`, and `docs/builder/temp-tests/` cleared.

Mid-build baseline drift (recorded 2026-05-22, after Slice 1 final-accepted and Slice 2 build-pass `built`): `M KANBAN.md` appeared without any Worker-2-attributable edit. The diff is a maintainer-driven NNN renumbering (e.g., `WIP-ALPHA-020-0.0.7` → `WIP-ALPHA-020-0.0.7`, `TODO-BETA-036-0.1.0` → `TODO-BETA-036-0.1.0`, `TODO-ALPHA-025-0.0.9` → `TODO-ALPHA-025-0.0.9`) — exactly the kind of recomputation KANBAN.md documents as expected ("Unlike status, milestone, and version, this number is not stable — it is recomputed whenever a card's position in the shipping sequence changes"). Per `AGENTS.md` line 31, this is presumptively maintainer in-progress work; workers must not touch `KANBAN.md` outside their slice's explicit contract. Slice 3's KANBAN.md edit (move `WIP-ALPHA-018-0.0.7` to Done) must read the file's then-current state and respect any concurrent maintainer renumbering.

Mid-build baseline drift addendum (recorded 2026-05-22, after Slice 3 build-pass `built` and Slice 3 review `review-accepted`): the maintainer landed two commits during the build between Slice 2 final-acceptance and Slice 3's build pass:

- `d2a10de remove 017 artifacts` — maintainer-side commit that absorbed Worker 0's pre-flight cleanup of old `build-017-*.md` and `bld-*.md` artifacts. Expected; not a contract drift.
- `216e6ba update card names` — maintainer-side commit that landed the `WIP-ALPHA-018-0.0.7` → `DONE-018-0.0.7` KANBAN move + the `### In progress` summary rewrite + the `CHANGELOG.md` `### Added` bullet on `main` BEFORE Worker 2's Slice 3 build pass ran. Worker 2's working-tree-diff contribution to `KANBAN.md` is therefore only a single-line cleanup at line 62 (removal of `management/commands/export_schema.py` from the "Still not implemented" Layer-3-planned list — a downstream consistency cleanup tied to the move-to-Done, in scope per Worker 2's `### Implementation notes`). Slice 3's other doc updates (`docs/GLOSSARY.md`, `docs/README.md`, `docs/TREE.md`) and the `CHANGELOG.md` append are still Worker-2-attributable as the maintainer commit landed only the KANBAN-side and CHANGELOG bullet, not the GLOSSARY/README/TREE edits. Per Worker 3's review, the slice-final state matches the spec contract exactly; only the delivery happened in two passes (maintainer-side + Worker-2-side).

Out-of-scope modified files appearing in `git status --short` (presumptively maintainer in-progress work per AGENTS.md line 31; workers must not touch):

- `M django_strawberry_framework/scalars.py`
- `M docs/review/rev-django_strawberry_framework.md`
- `M docs/review/rev-scalars.md`

None are in Slice 1/2/3 scope; the integration pass and final test-run gate should not flag these as build issues.

## Artifact list

- `docs/builder/bld-slice-1-module.md`
- `docs/builder/bld-slice-2-tests.md`
- `docs/builder/bld-slice-3-promotion_docs.md`
- `docs/builder/bld-integration.md`
- `docs/builder/bld-final.md`

## Checklist

- [x] Slice 1: Module + `Command` subclass -> `docs/builder/bld-slice-1-module.md`
- [x] Slice 2: Tests -> `docs/builder/bld-slice-2-tests.md`
- [x] Slice 3: Promotion + docs -> `docs/builder/bld-slice-3-promotion_docs.md`
- [x] Cross-slice integration pass -> `docs/builder/bld-integration.md`
- [x] Final test-run gate -> `docs/builder/bld-final.md`
