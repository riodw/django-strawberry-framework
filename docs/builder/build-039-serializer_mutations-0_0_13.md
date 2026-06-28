# Package build plan: serializer_mutations / 0.0.13 (039)

Spec source: `docs/spec-039-serializer_mutations-0_0_13.md`
Target release: `0.0.13`
Date created: 2026-06-27
Build rule: one slice at a time. Plan first, build second, review third, reconcile fourth.
DRY rule: every slice must justify shared/duplicated patterns before merging — the maximally DRY shape that stays readable.

## Pre-flight outcome

Pre-flight: passed on 2026-06-27; baseline: one unrelated dirty file (`docs/feedback.md`),
recorded as baseline-dirty out-of-scope (concurrent maintainer work per `AGENTS.md` #34 —
workers do not edit, do not revert); cleanup: prior 038-cycle `build-*.md` + `bld-*.md`
artifacts removed, `docs/builder/worker-memory/` cleared and re-seeded (4 empty files),
`docs/builder/temp-tests/` already empty. `docs/shadow/` holds only the script-owned
sibling folders (`current/` / `old/` / `new/` / `diff/`, owned by the review/bug-hunt
scripts per `AGENTS.md`) — no builder shadow stems present; left intact (gitignored,
regenerable by their owners; never blanket-deleted per `AGENTS.md`).

Pre-flight checks:
1. Working-tree baseline explicit — `git status --short` shows only `M docs/feedback.md` (out-of-scope).
2. `scripts/review_inspect.py` runs — smoke `uv run python scripts/review_inspect.py django_strawberry_framework/registry.py --output-dir docs/shadow --stdout` OK.
3. Build artifacts reset — old `build-038-*` / `bld-*` deleted; new plan + `bld-*` paths verified non-existent.
4. `.gitignore` lists scratch paths — `docs/shadow/`, `docs/builder/worker-memory/`, `docs/builder/temp-tests/` all gitignored.
5. Scratch directories cleared — worker-memory re-seeded; temp-tests empty.
6. Spec-doc consistency — `uv run python scripts/check_spec_glossary.py --spec docs/spec-039-serializer_mutations-0_0_13.md` → `OK: 38 terms`. Companion `docs/spec-039-serializer_mutations-0_0_13-terms.csv` exists.

## Baseline-dirty out-of-scope files (workers do not edit, do not revert)

- `docs/feedback.md` — dirty at build start; presumptively concurrent maintainer work (`AGENTS.md` #34).

## Concurrent-writable tracked binary/generated files (churn ≠ build output)

A concurrent maintainer process can rewrite these mid-build; their dirty status is not by
itself this build's output (per `BUILD.md` "Tracked binary / generated files"):
- `examples/fakeshop/db.sqlite3` — DB-backed; Slice 4 legitimately diverges it (kanban card move).
- `KANBAN.md` / `KANBAN.html` — generated from the kanban DB; Slice 4 re-renders them.
- `docs/GLOSSARY.md` — generated from the glossary DB; Slice 4 edits its `SerializerMutation` body via the DB.

## Build-wide context flags

- **Version bump is NOT in this card (Decision 14).** The package stays `0.0.12`:
  `pyproject.toml [project].version`, `__version__`, `tests/base/test_init.py::test_version`,
  and the `django-strawberry-framework` `version` entry in `uv.lock` all stay `0.0.12`.
  The `0.0.12 → 0.0.13` bump is owned by the **joint `0.0.13` cut** shared with the sibling
  Auth-mutations card `TODO-ALPHA-040-0.0.13`. No slice here bumps the version.
- **Soft `djangorestframework` dependency (Decision 12).** DRF goes in `[dependency-groups].dev`
  ONLY (never `[project].dependencies`). `uv.lock` IS regenerated for the dev-group add (DRF
  entries only; package version entry stays `0.0.12`). The one net-new public symbol
  `SerializerMutation` is a **named lazy export** via a root `__getattr__` (PEP 562) behind the
  shared `require_drf()` guard, and is **NOT in `__all__`** while DRF is soft (so `from … import *`
  stays DRF-free — F1). `import django_strawberry_framework` must succeed without DRF.
- **Release-status docs split from implemented-on-main docs (F8).** Slice 4 lands only
  implemented-on-main docs (TREE / TODAY / GLOSSARY body marked "implemented on main, releasing
  in 0.0.13" / GOAL crit-6 correction). The `shipped (0.0.13)` GLOSSARY flip, the README/docs-README
  "Coming next" → "Shipped today" move (README Status → `0.0.13`), and the `CHANGELOG.md` release
  bullets all defer to the joint cut. `CHANGELOG.md` edits require an explicit maintainer prompt
  (`AGENTS.md` "Do not update CHANGELOG.md unless explicitly instructed" — the spec describes but
  cannot authorize the edit).
- **Live-first coverage mandate.** Slice 3 lands the resolver pipeline AND its products live
  `/graphql/` consumer surface in ONE commit so every consumer-reachable resolver line is earned
  by a real HTTP request, not a package test (`examples/fakeshop/test_query/README.md` "Coverage rule.").
- **DB-backed generated docs (Slice 4).** `KANBAN.md` / `KANBAN.html` / `docs/GLOSSARY.md` are
  GENERATED from `examples/fakeshop/db.sqlite3`. Slice 4 edits the DB via the Django ORM then
  regenerates — never hand-edits the rendered markdown. Worker 0 pre-verifies the live DB
  references (card status, SpecDoc existence, glossary anchors) and embeds the DB-backed
  procedure + DONE-card invariants into the Slice 4 dispatch prompts (workers 1–3 cannot read
  `worker-0.md` where that procedure lives).

## One-slice-at-a-time rule (copy)

Build only one slice at a time. Do not start the next slice until the current slice's
plan/build/review/verification/spec-reconciliation cycle is complete. After all in-spec slices
are built, run a cross-slice integration pass, then the final test-run gate.

## DRY-first rule (copy)

Every plan, every implementation, every review pass answers first: is this the maximally DRY
shape that stays readable? Duplicated logic, parallel data flows, near-copies between modules,
and repeated literals are build-time defects. This card carries an unusually heavy DRY contract
(spec `## Cross-flavor reuse and DRY obligations`: P1.1–P1.7 promotions, P2.1–P2.7 single-siting,
the `register_subsystem_clear` seam, import-manifest grep guards) — `rest_framework/` must
mirror `forms/` module-for-module and import the promoted shared helpers, not re-fork them.

## Artifact list

- `docs/builder/bld-slice-0-drf_dependency_gate.md`
- `docs/builder/bld-slice-1-serializer_converter_inputs.md`
- `docs/builder/bld-slice-2-serializermutation_base.md`
- `docs/builder/bld-slice-3-resolver_pipeline_live_surface.md`
- `docs/builder/bld-slice-4-docs_card_wrap.md`
- `docs/builder/bld-integration.md`
- `docs/builder/bld-final.md`

## Checklist

- [x] Slice 0: Pre-Slice-1 dependency gate (F11) — verify + pin the DRF floor, wire the dev dep + `uv.lock` regen + any `pytest.ini` ignore line (no version bump) -> `docs/builder/bld-slice-0-drf_dependency_gate.md`
- [x] Slice 1: DRF-field → Strawberry input mapping + the serializer-derived input generator (`rest_framework/serializer_converter.py` + `rest_framework/inputs.py`) -> `docs/builder/bld-slice-1-serializer_converter_inputs.md`
- [x] Slice 2: The `SerializerMutation` base + `Meta` validation + the phase-2.5 bind (`rest_framework/sets.py`, `register_subsystem_clear` seam, root `__getattr__` export) -> `docs/builder/bld-slice-2-serializermutation_base.md`
- [x] Slice 3: The serializer resolver pipeline + the products live serializer surface, landed in one commit (`rest_framework/resolvers.py` + products `ItemSerializer` + live `/graphql/` tests) -> `docs/builder/bld-slice-3-resolver_pipeline_live_surface.md`
- [x] Slice 4: Doc updates + card wrap (no version bump — implemented-on-main docs only; DB-backed KANBAN card move) -> `docs/builder/bld-slice-4-docs_card_wrap.md`
- [x] Cross-slice integration pass -> `docs/builder/bld-integration.md`
- [x] Final test-run gate -> `docs/builder/bld-final.md`
