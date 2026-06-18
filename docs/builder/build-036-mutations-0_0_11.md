# Package build plan: mutations / 0.0.11 (036)

Spec source: `docs/spec-036-mutations-0_0_11.md`
Target release: `0.0.11`
Date created: 2026-06-17
Build rule: one slice at a time. Plan first (Worker 1), build second (Worker 2), review third (Worker 3), reconcile/final-verify fourth (Worker 1). Do not start the next slice until the current slice's artifact reaches `final-accepted`.
DRY rule: every plan, build, and review pass must first answer "is this the maximally DRY shape that stays readable?" Worker 1 plans for DRY, Worker 3 enforces it, Worker 1 re-checks it across slices at the integration pass. Duplicated logic, parallel data flows, near-copies, and repeated string/key/tuple literals are build-time defects.

Pre-flight: passed on 2026-06-17; baseline: clean (`git status --short` empty); cleanup: old artifact `build-035-optimizer_hardening-0_0_10.md` removed (no `bld-*.md` existed), `docs/shadow/` cleared, `docs/builder/worker-memory/` seeded with four empty files, `docs/builder/temp-tests/` empty. `scripts/review_inspect.py` smoke-runs (`django_strawberry_framework/permissions.py` → EXIT 0). `.gitignore` lists `docs/shadow/`, `docs/builder/worker-memory/`, `docs/builder/temp-tests/`. `scripts/check_spec_glossary.py --spec docs/spec-036-mutations-0_0_11.md` → `OK: 38 terms`.

## Baseline-dirty out-of-scope files

None. The working tree was clean at pre-flight. Any file that appears modified mid-build without a worker's edit is presumptively the maintainer's concurrent work (per `AGENTS.md`): workers do not edit or revert it; surface it, do not absorb it into the slice.

## Build-wide context flags

- **Joint `0.0.11` cut owns the version bump — NO slice edits version files** (spec Decision 13). `pyproject.toml`, `django_strawberry_framework/__init__.py` `__version__`, `tests/base/test_init.py::test_version`, and `uv.lock` are byte-unchanged across every slice. This card shares `0.0.11` with `TODO-ALPHA-037-0.0.11` (the `Upload` scalar sibling); the bump belongs to the joint cut, not this card. A worker that finds itself bumping a version string has drifted out of scope.
- **`CHANGELOG.md` edit is gated on an explicit Slice 5 maintainer prompt** (`AGENTS.md` #"Do not update CHANGELOG.md unless explicitly instructed"). The spec *describes* the `[Unreleased] ### Added` bullets but cannot itself grant the permission. Worker 0's Slice 5 dispatch prompt must explicitly include the `CHANGELOG.md` edit for it to be authorized; otherwise Slice 5 leaves `CHANGELOG.md` untouched. No version-heading promotion regardless.
- **`KANBAN.md` / `KANBAN.html` / `docs/GLOSSARY.md` are DB-generated, not hand-authored** (`BUILD.md` "Generated docs are DB-backed", `worker-0.md` "Closing out a kanban card"). Slice 5's GLOSSARY promotions and the card-to-Done move are **DB edits via the Django ORM, then regenerate** (`scripts/build_kanban_md.py` / `build_kanban_html.py` / `build_glossary_md.py`), never hand-edits of the rendered markdown. The DONE-card invariants (`SpecDoc` + ≥1 `CardGlossaryTerm`) and `import_spec_terms` anchor rule apply.
- **Four net-new public symbols** land in `django_strawberry_framework/__init__.py` `__all__` across the build: `DjangoMutation` (Slice 2), `DjangoMutationField` (Slice 3), `FieldError` (Slice 1), `DjangoModelPermission` (Slice 2) — spec Decision 5 / Decision 15. The `tests/base/test_init.py` `__all__` exports pin updates accordingly (this is the public-surface change, NOT a version change). Worker 3's per-slice public-surface check confirms each `__init__.py` change is spec-authorized.
- **`DjangoMutationField` and `DjangoModelPermission` are intentionally absent from `spec-036-mutations-0_0_11-terms.csv`** (they have no glossary heading until Slice 5 adds it; listing them would fail `check_spec_glossary.py`). Slice 5 adds their glossary entries; the CSV is not re-checked to include them within this card.
- **Slice 4 discharges the `spec-035` G2 live-test handoff** (spec Decision 9 / AR-M7): the live tier (`test_products_api.py`) owns the behavioral `CaptureQueriesContext` bounded-count assertion; the package tier (`tests/optimizer/test_walker.py`) owns the exact empty-`only_fields` plan-state mirror. Both tiers are required to close the handoff.
- **No `DjangoType` `Meta` key added** (spec Decision 12): `DEFERRED_META_KEYS` / `ALLOWED_META_KEYS` in `types/base.py` stay byte-unchanged. A mutation `Meta` is the mutation class's own validation namespace.
- **Coverage is the maintainer's gate, not a worker's tool.** No worker pass runs `pytest` with `--cov*` flags. The final gate runs `uv run pytest --no-cov` once (the `--no-cov` is required because `pytest.ini` auto-applies `--cov`). Missing-branch discovery is done by comparing the diff against the spec, not by reading coverage output.

## One-slice-at-a-time rule (copy)

Build only one slice at a time, in the spec's declared order. Do not start the next slice until the current slice's full plan → build → review → (re-pass loop) → final-verification cycle is complete and Worker 0 has marked its checkbox `- [x]` (which happens only after Worker 1 sets the artifact `final-accepted`). After all five spec slices are accepted, run the cross-slice integration pass, then the final test-run gate. No maintainer pause between slices — the happy path runs end-to-end; only genuine blockers stop the cycle.

## DRY-first rule (copy)

Before any code is written or accepted, answer: is this the maximally DRY shape that stays readable? Reuse the set-family lifecycle precedent (`filters/` / `orders/`, `sets_mixins.py`, `utils/inputs.py`, the phase-2.5 finalizer seam) and the read-side scalar/relation converters rather than re-deriving them. Repeated literals/keys/tuples become named constants. Worker 1 plans DRY, Worker 3 enforces DRY, Worker 1 re-checks DRY across slices at integration.

## Artifact list

- `docs/builder/bld-slice-1-input_generation.md`
- `docs/builder/bld-slice-2-mutation_base.md`
- `docs/builder/bld-slice-3-resolvers.md`
- `docs/builder/bld-slice-4-products_live.md`
- `docs/builder/bld-slice-5-docs_wrap.md`
- `docs/builder/bld-integration.md`
- `docs/builder/bld-final.md`

## Checklist

- [x] Slice 1: input-type generation + the `FieldError` envelope + the payload wrapper (spec Slice 1, Decision 6 / Decision 7) -> `docs/builder/bld-slice-1-input_generation.md`
- [x] Slice 2: the `DjangoMutation` base + `Meta` validation + finalizer binding (spec Slice 2, Decision 5 / Decision 12) -> `docs/builder/bld-slice-2-mutation_base.md`
- [x] Slice 3: the write resolvers + `DjangoMutationField` + optimizer / permission composition (spec Slice 3, Decision 8 / Decision 9 / Decision 10) -> `docs/builder/bld-slice-3-resolvers.md`
- [x] Slice 4: the products live write surface — discharges the `spec-035` G2 live-test handoff (spec Slice 4, Decision 9) -> `docs/builder/bld-slice-4-products_live.md`
- [x] Slice 5: doc updates + card-completion wrap (spec Slice 5, Doc updates) -> `docs/builder/bld-slice-5-docs_wrap.md`
- [x] Cross-slice integration pass -> `docs/builder/bld-integration.md`
- [x] Final test-run gate -> `docs/builder/bld-final.md`
