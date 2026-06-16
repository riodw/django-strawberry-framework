# Package build plan: optimizer_hardening / 0.0.10 (035)

Spec source: `docs/spec-035-optimizer_hardening-0_0_10.md`
Target release: `0.0.10`
Date created: 2026-06-16
Build rule: one slice at a time. Plan first, build second, review third, reconcile fourth.
DRY rule: every slice must justify shared/duplicated patterns before merging — the maximally DRY shape that stays readable. Worker 1 plans for DRY, Worker 3 enforces it, Worker 1 re-checks across slices at the integration pass.

Pre-flight: passed on 2026-06-16; baseline: clean (only this cleanup is in the tree); cleanup: old artifacts removed, memory/shadow/temp-tests cleared.

- (1) `git status --short`: clean working tree on `main` before cleanup.
- (2) `scripts/review_inspect.py` smoke: `uv run python scripts/review_inspect.py django_strawberry_framework/optimizer/walker.py --output-dir docs/shadow --stdout` → ran, exit 0.
- (3) Build artifacts reset: deleted prior `034` cycle artifacts (`build-034-permissions-0_0_10.md` + `bld-final.md` / `bld-integration.md` / `bld-slice-1..5-*.md`). New plan path and all intended `bld-*.md` paths verified absent.
- (4) `.gitignore` lists `docs/shadow/`, `docs/builder/worker-memory/`, `docs/builder/temp-tests/` (lines 166/180/184).
- (5) Scratch dirs cleared: `docs/builder/worker-memory/`, `docs/shadow/`, `docs/builder/temp-tests/` all emptied; four memory files reseeded empty.
- (6) `uv run python scripts/check_spec_glossary.py --spec docs/spec-035-optimizer_hardening-0_0_10.md` → `OK: 23 terms`, exit 0.

## Baseline-dirty out-of-scope files

None. The only working-tree changes at plan creation are this build's own pre-flight cleanup (deletion of the eight prior-`034`-cycle `build-*.md` / `bld-*.md` artifacts). Workers do not edit or revert anything else; if files appear modified mid-build that no worker touched, treat per `AGENTS.md` as concurrent maintainer work and leave them alone.

## Build-wide context flags

- **Joint-cut version boundary (Decision 9).** This card shares the `0.0.10` patch line with `DONE-034-0.0.10` (permissions, build-complete). The version bump (`pyproject.toml`, `django_strawberry_framework/__init__.py __version__`, `tests/base/test_init.py::test_version`, `uv.lock`) is owned by the **joint `0.0.10` cut**, NOT by any slice here. On-disk `__version__` reads `0.0.9`. No slice edits version files; no `CHANGELOG.md` release heading is promoted. The card adds no public symbol, so `__all__` is also untouched.
- **CHANGELOG.md edit AUTHORIZED.** The maintainer explicitly authorized the Slice 4 `CHANGELOG.md` edit at build kickoff (2026-06-16). Per `AGENTS.md` #"Do not update CHANGELOG.md unless explicitly instructed" and spec §Doc updates, the spec alone cannot grant this; the maintainer's explicit instruction does. Slice 4 adds the **G1 + G2** bullets under `[Unreleased]` (`### Changed` / `### Fixed`); **no version-heading promotion** (joint cut owns the bump); **no G3 bullet** (G3 ships nothing). The Slice 4 dispatch prompt must carry this explicit authorization.
- **G1 (Slice 1) already shipped — recorded, not built.** Commit `d1dea2fd` landed the G1 `_optimize` `_result_cache` early-return plus four tests before this spec was finalized (spec Revision 2). Slice 1's spec contract is therefore *shipped and recorded*; its only remaining work (the GLOSSARY note) lives in Slice 4. **Slice 1 is a procedural-closure slice** (BUILD.md "Procedural-closure slices"): a single Worker 1 pass sets `Status: final-accepted` directly, citing spec Decision 3 / Slice-1 checklist (no Worker 2 build, no Worker 3 review).
- **G3 (Slice 3) DEFERRED — ships no runtime code (Decision 6 / Decision 7, spec Revision 3).** G3's fragment type-condition narrowing has no reachable production trigger today (an abstract interface/union root never enters the walker — `registry.model_for_type` returns `None` for the abstract origin, so `_optimize` passes through). Its full design is retained in the spec as carry-forward requirements (R1–R3) for the follow-up abstract-return optimizer entry card. **Slice 3 is a procedural-closure slice**: a single Worker 1 pass sets `Status: final-accepted` directly, citing spec Decision 6/7 and the deferral clause (no Worker 2 build, no Worker 3 review).
- **Functional build remaining = Slice 2 (G2) only.** Slice 2 runs the full cycle (plan → build → review → reconcile → final). Slice 4 (docs + card wrap) runs the full cycle. Slices 1 and 3 are procedural closures.
- **DB-backed generated docs (Slice 4).** `KANBAN.md` / `KANBAN.html` / `docs/GLOSSARY.md` are GENERATED from `examples/fakeshop/db.sqlite3` via the `scripts/build_*.py` scripts. Slice 4's KANBAN move and GLOSSARY edits mean **edit the DB via the Django ORM, then regenerate** — never hand-edit the rendered markdown. Full DONE-card move procedure in `docs/builder/worker-0.md` "Closing out a kanban card".
- **No new module / no new test file / no settings key / no public symbol** (Decision 8). Source edits this card: `optimizer/walker.py` (G2 gate) and `types/resolvers.py` (Decision 5 elision loaded-check); G1's `optimizer/extension.py` already shipped. Tests extend `tests/optimizer/test_walker.py` + `tests/optimizer/test_extension.py` only.

## One-slice-at-a-time rule

Build only one slice at a time. Do not start the next slice until the current slice's plan/build/review/verification/spec-reconciliation cycle is complete and Worker 1 has set the artifact to `final-accepted`. After all in-spec slices are built, run the cross-slice integration pass, then the final test-run gate. The build runs end-to-end with no maintainer pause between slices (genuine blockers still escalate immediately).

## DRY-first rule

Every plan, implementation, and review pass answers one question before anything else: is this the maximally DRY shape that stays readable? Duplicated logic, parallel data flows, near-copies between modules, and repeated literals/keys/tuples are build-time defects. Worker 1 plans for DRY before code is written; Worker 3 enforces DRY before code is accepted; Worker 1 re-checks DRY across slices at the integration pass.

## Artifact list

- `docs/builder/bld-slice-1-g1_evaluated_queryset_guard.md`
- `docs/builder/bld-slice-2-g2_only_operation_gating.md`
- `docs/builder/bld-slice-3-g3_fragment_narrowing.md`
- `docs/builder/bld-slice-4-doc_wrap.md`
- `docs/builder/bld-integration.md`
- `docs/builder/bld-final.md`

## Checklist

- [x] Slice 1: G1 — evaluated-queryset guard (**shipped in `d1dea2fd`; procedural-closure record**) — spec Slice-1 checklist (lines 48-51) / Decision 3 (lines 164-183) -> `docs/builder/bld-slice-1-g1_evaluated_queryset_guard.md`
- [x] Slice 2: G2 — operation-type gating of `.only()` (+ Decision 5 FK-id-elision loaded-check) — spec Slice-2 checklist (lines 52-55) / Decision 4 (lines 185-209) / Decision 5 (lines 211-221) -> `docs/builder/bld-slice-2-g2_only_operation_gating.md`
- [x] Slice 3: G3 — fragment type-condition narrowing (**DEFERRED — no runtime code; procedural-closure record**) — spec Slice-3 checklist (line 56) / Decision 6 (lines 223-258) / Decision 7 (lines 260-272) -> `docs/builder/bld-slice-3-g3_fragment_narrowing.md`
- [x] Slice 4: doc updates + card-completion wrap (CHANGELOG edit authorized) — spec Slice-4 checklist (lines 57-58) / Doc updates (lines 383-398) -> `docs/builder/bld-slice-4-doc_wrap.md`
- [x] Cross-slice integration pass -> `docs/builder/bld-integration.md`
- [x] Final test-run gate -> `docs/builder/bld-final.md`
