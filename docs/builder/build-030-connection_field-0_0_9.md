# Package build plan: connection_field / 0.0.9 (030)

Spec source: `docs/spec-030-connection_field-0_0_9.md`
Target release: `0.0.9`
Date created: 2026-06-06
Build rule: one slice at a time. Plan first, build second, review third, reconcile fourth.
DRY rule: every slice must justify shared/duplicated patterns before merging.

Pre-flight: passed on 2026-06-06; baseline: one dirty file (`docs/GLOSSARY.md`), carried baseline-dirty per maintainer decision; cleanup: old 029 artifacts removed, memory/shadow/temp-tests cleared.

Pre-flight detail (BUILD.md "Pre-flight checks"):
1. Working-tree baseline — `git status --short` showed only `M docs/GLOSSARY.md` (see baseline-dirty note below). Maintainer chose to carry it as baseline-dirty.
2. `scripts/review_inspect.py` — smoke ran clean against `django_strawberry_framework/list_field.py` (exit 0).
3. Build artifacts reset — deleted prior-cycle `build-029-consumer_dx_cleanup-0_0_9.md`, `bld-slice-1..4`, `bld-integration.md`, `bld-final.md`. New plan path + all `bld-*.md` paths confirmed free.
4. `.gitignore` — `docs/shadow/`, `docs/builder/worker-memory/`, `docs/builder/temp-tests/` all listed.
5. Scratch cleared — `docs/builder/worker-memory/` re-seeded with 4 empty files; `docs/shadow/` and `docs/builder/temp-tests/` empty.
6. Spec-doc consistency — `scripts/check_spec_glossary.py --spec docs/spec-030-connection_field-0_0_9.md` reports `OK: 51 terms` (exit 0).

## Baseline-dirty out-of-scope files (workers do not edit, do not revert)

- `docs/GLOSSARY.md` — uncommitted Revision-3 `Meta.connection` glossary anchoring (Index row, "Type generation" / "Relay" browse-by-category rows, and the `## Meta.connection` entry body, all `planned for 0.0.9`). This is the maintainer's spec-030 prerequisite, carried baseline-dirty.
  - **Exception:** Slice 5 is the one slice that legitimately edits `docs/GLOSSARY.md` (it flips `DjangoConnectionField` / `DjangoConnection` / `Meta.connection` from `planned for 0.0.9` → `shipped (0.0.9)`). Slice 5 builds **on top of** this anchoring — it must NOT revert the anchoring lines. No other slice touches the file.

## Build-wide context flags

- **Version-bump-owner = the joint `0.0.9` cut, NOT this card** (Decision 13). No slice edits `pyproject.toml`, `django_strawberry_framework/__init__.py::__version__`, `tests/base/test_init.py::test_version`, or `uv.lock`. On-disk version stays `0.0.8`. Slice 5 adds the `CHANGELOG.md` `[Unreleased]` `### Added` bullet but promotes **no** version release heading.
- **CHANGELOG.md edit is permitted only in Slice 5** (the per-card grant; `AGENTS.md` withholds it by default). No other slice touches `CHANGELOG.md`; the Slice 5 dispatch prompt must name the edit explicitly.
- **Public exports land in Slice 4, not earlier** (Decision 14). `DjangoConnectionField` / `DjangoConnection` are promoted to `django_strawberry_framework/__init__.py` in Slice 4, alongside the live fakeshop usage that proves the public shape. Slices 1–3 reference the symbols by their `connection.py` module path only; the Worker 3 public-surface check on Slices 1–3 must confirm `__init__.py` `__all__` is unchanged.
- **Slice 2 argument-injection contingency** (Decision 6 / Risks): preferred route is a synthesized resolver `__signature__` so Strawberry's native arg-derivation emits `filter:` / `orderBy:`; documented fallback is a custom `FieldExtension.apply(...)` appending `StrawberryArgument`s. Slice 2 picks whichever compiles against the locked Strawberry `0.316.0`; both produce identical SDL. Worker 1 plans for this fork; the route choice is a Slice 2 implementation-discretion / spec-reconciliation item.
- **Connection-aware optimizer planning is out of scope** — sibling card `WIP-ALPHA-033-0.0.9`. This card only *wires* the cooperation point (extracted `_optimize` helper) and guards the nested-`edges { node }` gap with a strictness `"raise"` test (Slice 3). No silent cap; the gap is named in `docs/GLOSSARY.md`.
- **KANBAN.md / docs/GLOSSARY.md are DB-generated** (see `docs/builder/worker-0.md` "Closing out a kanban card"): they render from `examples/fakeshop/db.sqlite3` via `scripts/build_*`. Slice 5's KANBAN-move and glossary-flip are **DB-edit-then-regenerate** operations (Django ORM, then regenerate), not hand-edits of the generated markdown. Worker 1 must plan Slice 5 accordingly.
- **Coverage is the maintainer's / CI's gate.** No worker pass runs `pytest` with `--cov*` flags or chases coverage. Worker-local validation is `uv run ruff format .` + `uv run ruff check --fix .`. The final gate runs `uv run pytest --no-cov` once (Worker 1).

## One-slice-at-a-time rule

Build only one slice at a time. Do not start the next slice until the current slice's plan → build → review → final-verification → spec-reconciliation cycle is complete and Worker 0 has marked its checkbox. After all five spec slices are accepted, run the cross-slice integration pass, then the final test-run gate. Slices 1→2→3→4 are sequential (each builds on the prior); Slice 5 lands last.

## DRY-first rule

Every plan, implementation, and review pass answers first: is this the maximally DRY shape that stays readable? Reuse the shipped `DjangoListField` resolver wrappers (`_apply_get_queryset_sync` / `_apply_get_queryset_async`, the `Manager`/`QuerySet`/iterable consumer-resolver contract), the `FilterSet` / `OrderSet` `apply_sync` / `apply_async` pairs and `filter_input_type` / `order_input_type` helpers, the `_helper_referenced_filtersets` / `_helper_referenced_ordersets` orphan ledgers, the `_validate_filterset_class` / `_validate_orderset_class` validator template, and the `_optimize` plan logic (extracted, not duplicated). Worker 1 plans for DRY before code; Worker 3 enforces it before acceptance; Worker 1 re-checks across slices at integration.

## Artifact list

- `docs/builder/bld-slice-1-connection_base.md`
- `docs/builder/bld-slice-2-connection_field.md`
- `docs/builder/bld-slice-3-optimizer_cooperation.md`
- `docs/builder/bld-slice-4-live_http_export.md`
- `docs/builder/bld-slice-5-doc_card_wrap.md`
- `docs/builder/bld-integration.md`
- `docs/builder/bld-final.md`

## Checklist

- [x] Slice 1: `DjangoConnection[T]` base + per-target concrete connection classes + `Meta.connection` validated and stored on the definition + the `first` + `last` guard (spec `## Slice checklist` Slice 1; Decision 3 / Decision 4 / Decision 8) -> `docs/builder/bld-slice-1-connection_base.md`
- [x] Slice 2: `DjangoConnectionField` factory + synthesized-signature argument injection + composition pipeline + consumer-resolver contract + optimizer cooperation point + sync/async (spec `## Slice checklist` Slice 2; Decision 5 / Decision 6 / Decision 7 / Decision 11) -> `docs/builder/bld-slice-2-connection_field.md`
- [x] Slice 3: verify optimizer cooperation; bound the connection-aware-planning gap (spec `## Slice checklist` Slice 3; Decision 11) -> `docs/builder/bld-slice-3-optimizer_cooperation.md`
- [x] Slice 4: live HTTP coverage on a Relay-Node-shaped fakeshop type + public-export promotion (spec `## Slice checklist` Slice 4; Decision 7 / Decision 14 / card DoD) -> `docs/builder/bld-slice-4-live_http_export.md`
- [x] Slice 5: doc updates + card-completion wrap (grants the per-card `CHANGELOG.md` edit permission) (spec `## Slice checklist` Slice 5) -> `docs/builder/bld-slice-5-doc_card_wrap.md`
- [x] Cross-slice integration pass -> `docs/builder/bld-integration.md`
- [x] Final test-run gate -> `docs/builder/bld-final.md`
