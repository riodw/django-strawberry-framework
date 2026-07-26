# Package build plan: transport_security / 0.0.15 (065)

Spec source: `docs/spec-065-transport_security-0_0_15.md`
Target release: `0.0.15`
Date created: 2026-07-25
Build rule: one slice at a time. Plan first, build second, review third, reconcile fourth.
DRY rule: every slice must justify shared/duplicated patterns before merging.

Pre-flight: passed on 2026-07-25; baseline: dirty with unrelated concurrent work (recorded
below, NOT in scope); cleanup: no prior `build-*.md` / `bld-*.md` artifacts existed (clean
slate), `docs/builder/worker-memory/` + `docs/builder/temp-tests/` empty and seeded,
`docs/shadow/` holds only this build's own `review_inspect.py` output.
`scripts/review_inspect.py` smoke-ran against `django_strawberry_framework/routers.py`.
`scripts/check_spec_glossary.py --spec docs/spec-065-transport_security-0_0_15.md` exits 0
(`OK: 37 terms`).

## Baseline-dirty, OUT OF SCOPE — do not edit, do not revert

These files were already modified when this build started. They are another dev's / the
maintainer's concurrent in-flight work (the row-preserving-predicates remediation) plus this
program's own card/spec authoring. Per `AGENTS.md` #"Unexpected file modifications" they are
presumptively concurrent work: **never auto-revert, never `git checkout --` them, and do not
edit them unless this build's own slice contract names them.**

- `django_strawberry_framework/filters/sets.py` — row-preserving remediation (concurrent)
- `tests/filters/test_sets.py` — row-preserving remediation (concurrent)
- `docs/row-preserving-predicates-part1-plan.md` — concurrent
- `docs/feedback.md` — the prior review, maintainer-owned (never touch)
- `drys.md`, `vulns.md` (untracked) — maintainer scoping notes (never touch)
- `docs/GLOSSARY.md` — **generated** from the glossary DB; currently carries the concurrent
  row-preserving FilterSet edit. Slice 5 legitimately adds to it, but ONLY via the DB +
  `scripts/build_glossary_md.py` re-render, applied ON TOP of the concurrent state.
- `examples/fakeshop/db.sqlite3` — **concurrent-writable tracked binary.** Carries this
  program's card rows + the concurrent glossary edit. Never reset. Apply writes on top.
- `KANBAN.md` / `KANBAN.html` — **generated exports** of that DB (this program's card
  creation + SpecDoc link are already exported into them).
- `docs/spec-065-transport_security-0_0_15.md` + `-terms.csv` — this build's input contract
  (authored by the NEXT.md flow). Only Worker 1 may mutate the spec.

### Tracked binary / generated files that a concurrent writer can rewrite mid-build

`examples/fakeshop/db.sqlite3`, `KANBAN.md`, `KANBAN.html`, `docs/GLOSSARY.md`. A dirty
report on any of these is **not** proof this build caused it, and a same-size binary diff is
**not** proof of a no-op. Diff semantic content (`iterdump()` for the DB, a fresh regenerate
for a rendered doc) before treating churn as revertible. DB-backed slices verify by
**two-consecutive-regenerate byte-stability**, not by a clean `git diff`.

## Build-wide context flags

- **Joint version cut — the bump is NOT ours.** Card `TODO-ALPHA-045-0.0.15` is a non-Done
  card sharing target version `0.0.15`, so per `docs/SPECS/NEXT.md` Step 3 the version
  quintet (`pyproject.toml` `[project].version`, `django_strawberry_framework/__init__.py`
  `__version__`, `tests/base/test_init.py`, and the `CHANGELOG.md` entry) is owned by the
  **last card of the `0.0.15` line to land**. Card 065 is built first, so **no slice in this
  build moves the version quintet and no slice edits `CHANGELOG.md`**
  (spec Decision 15).
- **Known stale prose, NOT this build's to fix:** `spec-045` Decision 7 and `spec-046`
  Decision 11 each assert they are the "only card" at `0.0.15` / `0.0.16`. Cards 065 / 066
  joined those lines, so that justification is now stale — though the *conclusion* (045 owns
  the `0.0.15` cut, as the last to land) remains correct and is exactly what spec-065 defers
  to. Surfaced to the maintainer; out of scope here.
- **Breaking change, deliberately.** This build breaks the shipped `0.0.14`
  `DjangoGraphQLProtocolRouter` constructor contract three ways (required
  `django_application`, `url_pattern` -> `websocket_url_pattern`, no Channels HTTP mode).
  The API freeze begins at `1.0.0`; spec Decision 5 authorizes the break. Worker 3's
  public-surface check must measure the diff against **spec Decision 5**, not against
  "no API breakage".
- **Coverage is the maintainer's gate.** No worker runs `--cov`. `--no-cov` is the only
  permitted coverage-shaped flag.
- **Only the maintainer commits.** No worker commits, branches, stashes, or `git add`s.

## One slice at a time

Build only one slice at a time. Do not start the next slice until the current slice's
plan / build / review / verification / spec-reconciliation cycle is complete. After all
in-spec slices are built, run the cross-slice integration pass, then the final test-run gate.

## DRY first

Every plan, implementation, and review answers one question before anything else: is this the
maximally DRY shape that stays readable? Duplicated logic, parallel data flows, near-copies
between modules, and repeated string/key/tuple literals are build-time defects.

## Artifact list

- `docs/builder/bld-slice-1-protocol_split.md`
- `docs/builder/bld-slice-2-body_cap.md`
- `docs/builder/bld-slice-3-utf8_wire.md`
- `docs/builder/bld-slice-4-ws_revalidation.md`
- `docs/builder/bld-slice-5-docs_foldin.md`
- `docs/builder/bld-integration.md`
- `docs/builder/bld-final.md`

## Checklist

- [x] Slice 1: S1 — the protocol split (Django owns HTTP) -> `docs/builder/bld-slice-1-protocol_split.md`
- [x] Slice 2: S2 — the cumulative request-body cap -> `docs/builder/bld-slice-2-body_cap.md`
- [x] Slice 3: S9 — one UTF-8 wire contract -> `docs/builder/bld-slice-3-utf8_wire.md`
- [ ] Slice 4: S11 — WebSocket actor revalidation through an injection seam -> `docs/builder/bld-slice-4-ws_revalidation.md`
- [ ] Slice 5: S12 transport slice — migration note, deployment guidance, doc fold-in -> `docs/builder/bld-slice-5-docs_foldin.md`
- [ ] Cross-slice integration pass -> `docs/builder/bld-integration.md`
- [ ] Final test-run gate -> `docs/builder/bld-final.md`
