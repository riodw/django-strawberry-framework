# Package build plan: consumer_dx_cleanup / 0.0.9 (029)

Spec source: `docs/spec-029-consumer_dx_cleanup-0_0_9.md`
Target release: `0.0.9`
Date created: 2026-06-05
Build rule: one slice at a time. Plan first, build second, review third, reconcile fourth. Do not start the next slice until the current slice's plan/build/review/verification/spec-reconciliation cycle is complete.
DRY rule: every plan, every implementation, every review pass answers first — is this the maximally DRY shape that stays readable? Duplicated logic, parallel data flows, near-copies between modules, and repeated string/key/tuple literals are build-time defects. Worker 1 plans for DRY, Worker 3 enforces it, Worker 1 re-checks across slices at integration.

Pre-flight: passed on 2026-06-05; baseline: clean (`git status --short` empty); cleanup: prior build plan `build-028-orders-0_0_8.md` removed, no stale `bld-*.md`, memory/shadow/temp-tests cleared and four empty worker-memory files seeded.

Pre-flight detail:
- Working-tree baseline: clean — no unrelated uncommitted changes; no baseline-dirty out-of-scope files to protect.
- `scripts/review_inspect.py`: smoke run OK (`django_strawberry_framework/types/converters.py --output-dir docs/shadow --stdout`).
- Build artifacts reset: deleted `docs/builder/build-028-orders-0_0_8.md`; no `bld-*.md` present; the new plan path and all intended `bld-*.md` paths did not pre-exist.
- `.gitignore`: `docs/shadow/`, `docs/builder/worker-memory/`, `docs/builder/temp-tests/` all listed.
- Scratch dirs cleared: `docs/builder/worker-memory/` (re-seeded empty x4), `docs/shadow/`, `docs/builder/temp-tests/` empty.
- Spec-doc consistency: `uv run python scripts/check_spec_glossary.py --spec docs/spec-029-consumer_dx_cleanup-0_0_9.md` → `OK: 41 terms` (exit 0).

### Baseline exception (surfaced mid-build, not at pre-flight)

- **Pre-existing, unrelated `examples/fakeshop/test_query/test_kanban_api.py` failures (~30).** Surfaced by Worker 2 during the Slice 3 build pass and verified by Worker 2 to exist at HEAD via `git stash` (i.e. present WITHOUT any build-029 change). Worker 0 independently confirmed this build touches **no** file under `apps/kanban/` (`git status --short -- apps/kanban/` empty). Root cause per Worker 2: a kanban `pre_save` glossary-link signal at `apps/kanban/signals.py`. This is a committed-state baseline condition, NOT a spec-029 regression. The final test-run gate (full `pytest --no-cov` sweep) will encounter it — it must be treated as a recorded baseline exception, not as a build failure, and surfaced to the maintainer at handoff. Worker 0 / Worker 1 re-confirm at the final gate that the kanban failures are identical with and without the build diff before accepting the gate. Pre-flight check 1 only ran `git status --short` (clean) and did not run the suite, so this was not visible at pre-flight.

## Build-wide context flags

- **Version-bump owner = the joint `0.0.9` cut, NOT this card** (spec Decision 11, DoD item 16). No slice in this build edits `pyproject.toml`, `django_strawberry_framework/__init__.py` `__version__`, `tests/base/test_init.py::test_version`, or `uv.lock`, and no slice promotes a CHANGELOG release heading. Every CHANGELOG bullet lands under `[Unreleased]` (Slice 1 → `### Changed`; Slices 2 + 3 → `### Added`). A CHANGELOG-sanity / final-gate check keyed on "version line matches `pyproject.toml`" must treat the deliberate `[Unreleased]` + unchanged version as expected, not drift.
- **Cross-slice test deferral (canonical 1→2→3 order).** `test_inspect_reads_resolved_annotation_not_field_null` is a Slice-2 command assertion over the Slice-3 `NullabilityOverrideBookType` type. Under 1→2→3 order it CANNOT pass at Slice 2 verification (the type does not exist yet), so it is deferred to the **Slice 3** cycle. At Slice 2 final verification this spec sub-check stays unticked with the one-line deferral reason "waits on `NullabilityOverrideBookType`, Slice 3" — it does NOT flip Slice 2 to `revision-needed` (spec "Implementation scaffolding & staging notes", Test plan `test_inspect_reads_resolved_annotation_not_field_null`).
- **Per-slice CHANGELOG edit permission.** Each slice's doc-update step grants that slice the explicit permission to edit `CHANGELOG.md` (overriding `AGENTS.md` "Do not update CHANGELOG.md unless explicitly instructed"), scoped to a `[Unreleased]` bullet only.
- **Slice independence + Slice-3 carve-off contingency (Decision 12).** The three functional slices ship in any order and none depends on another; the build runs them in declared order. If the schedule forces Slice 3 to defer it carves off as its own follow-up card — not expected here, this build delivers all three plus the wrap.
- **Slice 1 migration gate is the broad audit, not a `DjangoOptimizerExtension()` literal grep.** Audit every `extensions=[...]` construction site (`rg 'extensions=\['`, ≈48 entries across 5 package test files incl. two `_CaptureExt()` subclass instances), per construction site not per file; then the forbidden-form grep (`extensions=[DjangoOptimizerExtension()]` / `[DjangoOptimizerExtension]` / `[ext]` / `[_CaptureExt()]` / `lambda: DjangoOptimizerExtension()`) must find zero hits in active source/docs.

## One-slice-at-a-time rule

Build only one slice at a time. Do not start the next slice until the current slice's full cycle (plan → build → review → final-verification → spec-reconciliation) is complete and Worker 0 has marked its checkbox. After all in-spec slices are built, run the cross-slice integration pass, then the final test-run gate.

## DRY-first rule

Every plan, implementation, and review pass must justify any shared or duplicated pattern before merging. New duplication, parallel data flows, near-copies, and repeated literals are defects. Worker 1 re-checks DRY across slices at the integration pass.

## Artifact list

- `docs/builder/bld-slice-1-extensions_singleton_factory.md`
- `docs/builder/bld-slice-2-inspect_django_type.md`
- `docs/builder/bld-slice-3-nullability_overrides.md`
- `docs/builder/bld-slice-4-card_completion_wrap.md`
- `docs/builder/bld-integration.md`
- `docs/builder/bld-final.md`

## Checklist

- [x] Slice 1: migrate `extensions=` construction sites to the singleton-factory form (spec "Slice checklist" Slice 1; Decision 3) -> `docs/builder/bld-slice-1-extensions_singleton_factory.md`
- [x] Slice 2: `inspect_django_type` diagnostic command (spec "Slice checklist" Slice 2; Decision 4) -> `docs/builder/bld-slice-2-inspect_django_type.md`
- [x] Slice 3: `Meta.nullable_overrides` / `Meta.required_overrides` (spec "Slice checklist" Slice 3; Decisions 5–10) -> `docs/builder/bld-slice-3-nullability_overrides.md`
- [x] Slice 4: card-completion wrap — closed **DB-backed** on 2026-06-05 (maintainer later authorized the DB close-out, superseding the "maintainer-owned" deferral below). Card 29 moved to `DONE-029-0.0.9` via the kanban DB + regenerate; `bld-slice-4-card_completion_wrap.md` `final-accepted`. -> `docs/builder/bld-slice-4-card_completion_wrap.md`
- [x] Cross-slice integration pass (over Slices 1–3) -> `docs/builder/bld-integration.md`
- [x] Final test-run gate -> `docs/builder/bld-final.md`

## Maintainer decision — 2026-06-05 (Slice 4 + kanban baseline)

Worker 1's Slice-4 planning found that `KANBAN.md` and `KANBAN.html` are **generated artifacts** rendered from the committed `examples/fakeshop/db.sqlite3` via `scripts/build_kanban_md.py` / `scripts/build_kanban_html.py` (the repo's documented workflow is edit-the-DB-then-regenerate; the card body's own embedded TODO says "move WIP-ALPHA-029-0.0.9 to DONE-029-0.0.9"). The spec's card-completion wrap describes a direct `KANBAN.md` text edit. Worker 0 escalated the Path-A/Path-B choice plus the pre-existing kanban baseline failure to the maintainer. Decisions:

1. **Slice 4 is maintainer-owned.** No worker cycle builds it. Worker 0 proceeds to the cross-slice integration pass and final test-run gate over Slices 1–3 and hands off; the maintainer performs the KANBAN move (`WIP-ALPHA-029-0.0.9` → `DONE-029-0.0.9`, fix the card body's stale `docs/spec-021-nullable_overrides-0_0_8.md` reference and `## [0.0.8]` CHANGELOG references) via the DB-edit + regenerate workflow, and addresses the `apps/kanban/signals.py` baseline failure, as part of their commit. The `bld-slice-4-card_completion_wrap.md` plan (Done id `DONE-029-0.0.9` pinned, exact edits enumerated, Path-A vs Path-B documented) is left for the maintainer's reference. Slice 4 checkbox stays `[~]` (maintainer-owned, not worker-completed) — it is intentionally not `[x]`.
2. **Kanban baseline failures are a recorded baseline exception.** The final test-run gate runs the full `pytest --no-cov` sweep, reports the ~30 `test_kanban_api.py` failures as the known pre-existing baseline exception (above), confirms they are identical with and without the build diff, and does NOT block `final-accepted` on them. spec-029's own tests (Slices 1–3) must all pass.
