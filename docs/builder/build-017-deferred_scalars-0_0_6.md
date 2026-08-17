# Package build plan: deferred_scalars / 0.0.6 (017) — residual-completion cycle

Spec source: `docs/SPECS/spec-017-deferred_scalars-0_0_6.md` (already archived; card `DONE-017-0.0.6`, 84,488 bytes).
Rationale companion: `docs/SPECS/appx/spec-017-deferred_scalars-0_0_6-rationale.md` — **does not exist**; creating it is this cycle's first obligation and the reason the cycle was opened.
Terms companion: `docs/SPECS/appx/spec-017-deferred_scalars-0_0_6-terms.csv` (exists, 16 rows, **one row per anchor** — importable shape; `check_spec_glossary` green: `OK: 16 terms - all have glossary entries and at least one spec link.`).
Target release: `0.0.6` (shipped 2026; the package is at `0.0.14` today). This cycle bumps no version and lands no feature.
Build rule: one round at a time. Plan first, build second, review third, reconcile fourth.
DRY rule: every round must justify shared/duplicated patterns before merging.

Ownership partition: **none; sequential rounds.** R1 writes the rationale companion and reconciles the spec; R3 audits the standing docs against what R1 established. R3 cannot precede R1 (it audits R1's output), and a contingent R2 code round would have to match the symbol vocabulary R1 fixes. Nothing runs concurrently.

Hot-path declaration: **none.** R1 and R3 write Markdown only. A contingent R2 would open `django_strawberry_framework/types/converters.py` / `scalars.py`, both of which sit on the type-**construction** path (per schema build), not a per-request / per-resolver / per-row path — so still `none`. If R2 is opened and its scope turns out to touch `convert_scalar` at resolve time, Worker 1 re-declares at R2 plan time.

Floor-verification scope: **none.** No round touches a Django / Strawberry / channels integration seam; R1 and R3 write Markdown. The floor, quoted from `docs/builder/BUILD.md` `## Floor verification` so no pass restates it from memory, is **Django 5.2.16 on Python 3.10 with strawberry-graphql 0.316.0**. If R2 is opened, Worker 1 re-declares the scope at R2 plan time — a change to `scalars.py`'s `strawberry.scalar(...)` overload usage *would* be a Strawberry integration seam.

Pre-flight: passed on 2026-08-17 with two recorded deviations (below); baseline: **dirty with a concurrent session's work** — see the out-of-scope list; cleanup: **not performed**, see step 3 / step 5 deviations.

## Pre-flight record

1. **Working-tree baseline is explicit.** `git status --short` shows a concurrent session's spec-016 residual cycle (deleted `bld-015-final.md` / `bld-016-*.md` / `build-016-*.md`, new `docs/builder/DONE/build-016-*.md`) and a concurrent review cycle (24 untracked `docs/review/rev-*.md`, modified package + test files). The maintainer instructed this cycle to ignore concurrent work. Per `AGENTS.md` rule 34 these files are **out of scope: never edited, never reverted** by any worker in this cycle. Full list under `## Baseline-dirty out-of-scope files`.
2. **`scripts/review_inspect.py` runs.** `uv run python scripts/review_inspect.py django_strawberry_framework/scalars.py --output-dir docs/shadow --stdout` → OK.
3. **Build artifacts reset — DEVIATED, deliberately.** `docs/builder/BUILD.md` `### Cohorting, naming, and closure` ("Pre-flight for a round") exempts a review round from the artifact reset, and this cycle is a round over already-shipped work. Additionally, the prior-cycle `bld-*.md` / `build-*.md` files in `docs/builder/` are a **concurrent session's live output**, so deleting them would destroy another session's work. Verified instead that every path this cycle intends to create is absent: `docs/builder/bld-017-*` and `docs/builder/build-017-*` did not exist before this plan was written.
4. **`.gitignore` lists the untracked scratch paths** — `docs/builder/worker-memory/` (`.gitignore:188`), `docs/shadow/` (`.gitignore:174`), `docs/builder/temp-tests/` (`.gitignore:192`). Confirmed.
5. **Scratch directories cleared — DEVIATED, deliberately.** `docs/shadow/` and `docs/builder/temp-tests/` may hold a concurrent session's in-flight output. Clearing them is destructive to that session and is not required for this cycle's correctness (no round consumes prior shadow output). Left untouched; this cycle's own shadow writes are additive.
6. **Spec-doc consistency check.** `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-017-deferred_scalars-0_0_6.md` → exit 0, `OK: 16 terms`. Terms CSV re-verified as one-row-per-anchor (16 distinct anchors, 16 rows), so it is importable by `import_spec_terms`, not merely green under the lenient authoring gate.
7. **Spec rationale extracted** — **not yet done. This is round R1's contract**, and no other round may be dispatched until R1 is `final-accepted`.

## Baseline-dirty out-of-scope files (never edit, never revert)

Package source: `connection.py`, `filters/inputs.py`, `forms/converter.py`, `mutations/resolvers.py`, `relay.py`, `templates/django_strawberry_framework/debug_toolbar.html`, `testing/relay.py`, `types/base.py`, `types/finalizer.py`, `utils/converters.py`.
Tests: `tests/filters/test_inputs.py`, `tests/middleware/test_debug_toolbar.py`, `tests/mutations/test_resolvers.py`, `tests/testing/test_relay.py`, `tests/types/test_base.py`, `tests/types/test_finalizer.py`, `tests/utils/test_converters.py`, `examples/fakeshop/test_query/test_multi_db.py`, `examples/fakeshop/test_query/test_optimizer_auto_api.py`.
Docs / artifacts: `docs/review/review-0_0_14.md`, all 24 untracked `docs/review/rev-*.md`, `docs/builder/bld-015-final.md`, `docs/builder/bld-016-*.md`, `docs/builder/build-016-*.md`, `docs/builder/DONE/build-016-fieldmeta_consolidation-0_0_6.md`.

**`examples/fakeshop/db.sqlite3` is concurrent-writable** and is the source of `KANBAN.md`, `KANBAN.html`, and `docs/GLOSSARY.md`. Churn on any of those four is presumed a concurrent writer's until a semantic diff proves otherwise (`docs/builder/BUILD.md` `### Tracked binary / generated files`). **No round in this cycle is authorized to write the DB or regenerate those three docs**; a needed DB-backed change is recorded as a maintainer follow-up instead (see R3).

## Build-wide context

- **What this cycle is.** The code for `DONE-017-0.0.6` shipped in `0.0.6`. Four later cards demonstrably reshaped what it landed — most visibly `DONE-025-0.0.7` (which deleted the `warnings.catch_warnings()` suppression this spec pins as a Decision) and `DONE-041-0.0.14` (which replaced the spec's two hand-rolled `_resolve_*_field()` helpers with the shared `utils/imports.py::import_attr_if_importable`). The spec still describes the `0.0.6` shape as current contract. The cycle's job is: (a) create the missing rationale companion by MOVING the spec's deliberative layer into it, (b) prove nothing the spec planned was skipped in the code, (c) reconcile the spec to state the contract that holds at `HEAD`, and (d) finish the documentation.
- **The spec never narrates its own history** (`docs/builder/BUILD.md` `## Spec rationale extraction`). Every explanation of what changed, when, and why — including everything in this cycle's findings — lands in the rationale companion, never in the spec. The spec reads as a clean current contract.
- **Version-bump owner:** none. `pyproject.toml` and `__init__.py` are not touched by this cycle.
- **Joint-cut path:** not applicable.

## Worker-0 pre-dispatch source verification

`docs/builder/BUILD.md` `### Worker 0 verifies every finding against source before dispatching` — every claim below was read at the worktree before this plan was written, and is handed to R1 as *verified starting evidence, not as a conclusion*. R1 re-derives and owns the final judgement.

**Holds — the spec's substantive contract shipped and is present at `HEAD`:**

- `django_strawberry_framework/scalars.py::_parse_bigint` and `::_serialize_bigint` exist with the spec's `^(0|-?[1-9][0-9]*)$` pattern (`django_strawberry_framework/scalars.py #"_BIGINT_STRING_PATTERN = re.compile"`).
- `django_strawberry_framework/types/converters.py::SCALAR_MAP` carries `models.BigIntegerField: BigInt`, `models.PositiveBigIntegerField: BigInt`, `models.JSONField: strawberry.scalars.JSON`, and `models.BigAutoField: int` (preserved).
- `SCALAR_MAP`'s declared value type is `dict[type[models.Field], Any]` (Decision 8, shipped).
- The sentinel-guarded `ArrayField` branch in `converters.py::convert_scalar` rejects nested arrays and outer `choices`, and recurses into `base_field`; the `HStoreField` branch rejects outer `choices` and returns `strawberry.scalars.JSON`. Both run before the `SCALAR_MAP` MRO walk.
- `BigInt` is in `django_strawberry_framework.__all__` and pinned in `tests/base/test_init.py`.
- No `TODO` comment remains in `types/converters.py`; a repo-wide sweep for `TODO(spec-017` / `TODO-(ALPHA|BETA|STABLE)-017` returns zero hits outside `KANBAN.md`.

**Does NOT hold — the spec describes a shape later work replaced (each is a spec-reconciliation item for R1, NOT a code defect):**

1. **The deprecation suppression is gone.** Decision 1's `with warnings.catch_warnings(): ... BigInt = strawberry.scalar(NewType("BigInt", int), ...)` block, Decision 6's "Import-time warning posture", the Goals bullet, the User-facing API note, and the Risks bullet all describe it as current. At `HEAD`, `scalars.py` defines `BigInt = NewType("BigInt", int)` plus a separate `_BIGINT_SCALAR_DEFINITION` registered through `_PACKAGE_SCALAR_MAP` and the public `strawberry_config()` factory — the exact migration `DONE-025-0.0.7` shipped, which this spec itself roadmapped.
2. **Decision 4's `_resolve_array_field()` / `_resolve_hstore_field()` helpers do not exist.** `converters.py #"_ARRAY_FIELD_CLS: type[models.Field] | None = import_attr_if_importable"` shows both sentinels now resolve through `django_strawberry_framework/utils/imports.py::import_attr_if_importable`. The four spec-named helper-resolver tests (`test_resolve_array_field_returns_class_when_postgres_fields_importable` and its three siblings) exist nowhere in the tree, because the branch they covered moved into the shared helper's own tests (`tests/utils/test_imports.py`).
3. **Nine spec-named schema-execution tests exist nowhere by that name** — `test_big_integer_field_maps_to_bigint_in_schema`, `test_big_integer_field_nullable_in_schema`, `test_positive_big_integer_field_maps_to_bigint_in_schema`, `test_bigint_serializes_query_result_as_string_via_schema_execution`, `test_bigint_parses_string_argument_via_schema_execution`, `test_bigint_parses_int_argument_via_schema_execution`, `test_json_field_maps_to_json_scalar_in_schema`, `test_json_field_nullable_in_schema`, `test_json_field_round_trips_dict_via_schema_execution`. The behaviour they pinned is covered at the **live `/graphql/` tier** in `examples/fakeshop/test_query/test_scalars_api.py` against the `apps.scalars` model columns `payload` (`JSONField`), `signed_big` (`BigIntegerField`), and `unsigned_big` (`PositiveBigIntegerField`) plus their nullable twins — the documented live-first promotion, not a coverage loss. R1 must verify this claim per-test rather than accept it; it is the single most load-bearing "nothing was skipped" finding in the cycle.
4. **The error-message construction changed.** Decision 2 and Decision 5's pseudocode interpolates `field.model.__name__}.{field.name`; `HEAD` interpolates `_field_label(field)` and tests choices through `_field_has_choices(field)` rather than a bare `field.choices` truth test.
5. **`convert_scalar` gained a `force_nullable` parameter** (the consumer-override contract from `DONE-019-0.0.6`), so the spec's `return result | None if field.null else result` is now `effective_null`-driven, with the `ArrayField` recursion deliberately left `force_nullable`-unset.
6. **Slice 5 / Slice 6's version work is long superseded.** The quintet targeted `0.0.6`; the package is at `0.0.14`.
7. **The follow-up card the spec forward-references is named three different ways in the same document** — `WIP-ALPHA-020-0.0.7`, `TODO-ALPHA-045`, and `DONE-025-0.0.7` — and the card that actually shipped it is `DONE-025-0.0.7`. Slice 6 also contains a self-contradicting instruction to move `DONE-017-0.0.6` → `DONE-017-0.0.6`, a residue of the card renumber.
8. **The spec's Slice 6 archive step and its `## Definition of done` archive item are already satisfied** — the spec sits at `docs/SPECS/spec-017-deferred_scalars-0_0_6.md` and its terms CSV at `docs/SPECS/appx/`. **No move is owed by this cycle.** Do not "re-archive".

**Known-wrong across multiple surfaces, deliberately NOT partial-fixed here:** `docs/SPECS/spec-025-scalar_map_helper-0_0_7.md` refers to this spec through the ref-id `[spec-013]` (a pre-renumber artifact) in five places. `KANBAN.md` line 349 already records that whole cluster as carded onto `TODO-ALPHA-051-0.0.15` / `TODO-ALPHA-052-0.1.0`, and `worker-0.md` "Verify card/glossary references against the DB" forbids correcting one surface of a multi-surface wrong reference. Out of scope; re-recorded in the final gate's deferred-work catalog.

## Artifact list

- `docs/builder/bld-017-r1-rationale_and_spec_reconciliation.md` — Worker 1 (procedural-closure shape: combined Plan + Final-verification, `docs/builder/BUILD.md` `### Procedural-closure slices`). Creates the rationale companion, performs the completeness audit, reconciles the spec.
- `docs/builder/bld-017-r2-<slug>.md` — **contingent.** Opened only if R1's audit finds a genuine code gap or defect. Full cycle: Worker 1 plan → Worker 2 build → Worker 3 review → Worker 1 final verification. Not created if R1 confirms the code is complete.
- `docs/builder/bld-017-r3-doc_completion_audit.md` — Worker 1 (procedural-closure shape). Standing-doc completion + archive audit.
- `docs/builder/bld-017-final.md` — Worker 1, the final test-run gate.

**No `bld-integration.md` for this cycle.** R1 and R3 land Markdown only and a contingent R2 would be a single narrow fix, so there is no cross-round DRY surface for a consolidation pass. The integration pass's two live obligations — `docs/builder/BUILD.md` `## Cross-slice integration pass` step 1 (read every closed artifact in full) and step 6 (the staged-anchor sweep for `TODO(spec-017` / `TODO-(ALPHA|BETA|STABLE)-017`) — are folded into the final gate, which records them explicitly.

## Checklist

- [x] R1: rationale companion (extraction move) + code-completeness audit + spec reconciliation -> `docs/builder/bld-017-r1-rationale_and_spec_reconciliation.md`
- [x] R2 — **not opened; no round is owed.** R1's audit resolved every slice sub-check, Goal, `## User-facing API` row, test-plan category 1-19 and DoD item to either (a) present at `HEAD` or (b) deliberately superseded by later work. **Zero (c) "never shipped" dispositions**, so there is no code gap for a builder to close. The box is ticked on that finding, not on work performed.
- [x] R3: documentation completion + archive audit -> `docs/builder/bld-017-r3-doc_completion_audit.md`
- [x] Final test-run gate -> `docs/builder/bld-017-final.md`

## Post-gate note (Worker 0)

Every checklist box is `- [x]`; all three round artifacts and `docs/builder/bld-017-final.md` read `final-accepted`. Worker 0 stops driving here and hands off to the maintainer (`docs/builder/BUILD.md` `## Slice handoff`). Closeout — the retrospective, the memory read, and the `docs/shadow/` / `docs/builder/temp-tests/` cleanup — runs only **after** the maintainer commits and supplies the build-cycle commit range, and this cycle must not clear those scratch paths in any case while a concurrent session's live output is in them.

**One custodian correction landed against R1 after the gate closed (MF-3).** The gate found that Decision 1's `BigAutoField` bullet still carried the falsified "No current-day consumer recourse … wait for [Scalar field override semantics]" clause — false since the sibling card `DONE-019-0.0.6` shipped the annotation override in the same release — which additionally falsified two of the rationale companion's own completeness sentences. Worker 1 was re-dispatched as the only role authorized to touch either file. Worker 0 re-verified the close:

- The false clause's two distinctive phrases (`no current-day`, `wait for [Scalar`) now measure **0 occurrences each** in the spec, so the claim is retired rather than reworded.
- Two sites were corrected (`## Key glossary references` and Decision 1); the other five `BigAutoField` occurrences were each read and dispositioned as true-at-`HEAD` rather than assumed.
- Worker 1 caught a **second instance of the same error class while measuring**: its own draft population table named `recourse` as the claim's token, which samples a shared vocabulary (`Meta.exclude` has an unrelated "recourse") rather than establishing this claim's population.
- Byte counts re-measured at the fixed point: spec **84,488 → 62,804**, companion **0 → 44,338**. The mid-pass figures R1 and the gate recorded (62,677 / 41,323 / 41,325) were taken while the files were still growing and are superseded.

The correction is Markdown-only, so it cannot invalidate the gate's `pytest` / Django / `ruff` results. The two gates it *could* affect were re-run after it landed and both pass: `git diff --check`, and `scripts/check_trailing_commas.py --check` over all six of this cycle's files. `scripts/check_spec_glossary.py` re-run on the corrected spec: exit 0, `OK: 16 terms`.

## Maintainer handoff

This cycle changed **no source and no tests**. It wrote exactly six files, all Markdown:

| File | State |
|---|---|
| `docs/SPECS/spec-017-deferred_scalars-0_0_6.md` | modified — deliberative layer removed, contract reconciled to `HEAD` |
| `docs/SPECS/appx/spec-017-deferred_scalars-0_0_6-rationale.md` | new — the companion this cycle existed to create |
| `docs/builder/build-017-deferred_scalars-0_0_6.md` | new — this plan |
| `docs/builder/bld-017-r1-rationale_and_spec_reconciliation.md` | new |
| `docs/builder/bld-017-r3-doc_completion_audit.md` | new |
| `docs/builder/bld-017-final.md` | new |

Everything else dirty in the tree is a concurrent session's and is listed under `## Baseline-dirty out-of-scope files`. Stage explicitly per `START.md` — never `git add -A`.

Three items need a maintainer decision rather than a worker, and each is enumerated inline in `docs/builder/bld-017-final.md`'s `### Deferred work catalog` so it survives that artifact's eventual retirement: the DB-backed `KANBAN.md` `DONE-017-0.0.6` suppression claim (**MF-1** — 4 occurrences: `CardItem` 703/713/715 plus `CardReference` 62 on card 39, with 715 and 62 byte-identical and amendable only together), the `CHANGELOG.md:210` pre-renumber label (**MF-2**), and the already-carded `[spec-013]` ref-id cluster in `docs/SPECS/spec-025-scalar_map_helper-0_0_7.md` (6 occurrences: 5 uses plus the definition line at `:706`). A fourth, `docs/TREE.md`'s pending regenerate, is owed by whoever commits the concurrent session's `django_strawberry_framework/utils/converters.py` docstring edit — not by this cycle.

**All three were subsequently homed on `TODO-ALPHA-052-0.1.0` at the maintainer's instruction (2026-08-17), so none of them now depends on this artifact surviving.** The board was read first to establish the routing: `TODO-ALPHA-051-0.0.15` takes only occurrences its WP batches open in live code, and every spec-017 residual is documentation-only, so nothing went to 051. Two `CardItem` writes plus a `scripts/build_kanban_md.py` / `scripts/build_kanban_html.py` regenerate:

- **MF-1** — a new `scope` bullet on card 052 (`CardItem` 1368, order 36), placed beside that card's board-DB spec-path-rot bullet because both are ORM-edit-plus-regenerate work. It carries the full population, the 715 ≡ 62 byte-identity constraint (re-verified by direct string comparison before the bullet was written, not carried on the gate's word), the FK-backed-placeholder warning, and the post-edit verification. It also records the grading difference from its neighbour: the spec-path-rot bullet's (c) sites are true as history, whereas this claim is present-tense and false.
- **MF-2 and the `[spec-013]` count correction** — folded into card 052's existing `[spec-011]` renumber-sweep bullet (`CardItem` 1345), which already owned the cluster. The bullet said "five links"; it now says **six occurrences — five uses plus the definition line all five depend on**, enumerated by section rather than by line, and names `CHANGELOG.md` as a fourth surface with the `AGENTS.md` rule 21 reason it cannot be fixed alone.

Both bullets cite by `path #"substring"` and section heading rather than `path:NN`: `KANBAN.md` is a standing doc, and `AGENTS.md` rule 27 confines raw line citations to per-cycle scratchpads. Gates after the regenerate: `scripts/build_kanban_tracked_path_constants.py --check` exit 0, `scripts/check_trailing_commas.py --check KANBAN.md` exit 0, `git diff --check` exit 0, and the kanban app's own suite `157 passed`. The rendered diff is exactly the two bullets, `KANBAN.html`'s change is confined to its data block, and the `DONE-017-0.0.6` card body still measures 4 `suppress*` occurrences — MF-1 is homed, not yet fixed.

## Worker memory

Namespaced per cycle so a concurrent session's build cannot read or clobber them: `docs/builder/worker-memory/spec-017-worker-0.md` … `spec-017-worker-3.md`, seeded empty at plan time. Gitignored (`.gitignore:188`). The four un-namespaced `worker-N.md` files in that directory belong to another cycle and are left untouched.
