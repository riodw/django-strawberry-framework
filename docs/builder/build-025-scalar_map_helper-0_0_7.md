# Package build plan: scalar_map_helper / 0.0.7 (025)

Spec source: `docs/SPECS/spec-025-scalar_map_helper-0_0_7.md` (already archived; the active-spec path `docs/spec-025-scalar_map_helper-0_0_7.md` does not exist and is not recreated)
Target release: `0.0.7` (shipped 2026-05-27; tag `0.0.7` at commit `72f6cd9`)
Build rule: one slice at a time. Plan first, build second, review third, reconcile fourth.
DRY rule: every slice must justify shared/duplicated patterns before merging.
Ownership partition: none; sequential slices. Worker 1 is the sole writing role in this cycle.
Hot-path declaration: none. No production code is planned; nothing this cycle writes runs per request, per resolver, per row, per connection, or per outbound message.
Floor-verification scope: none. No slice touches a Django / Strawberry / channels integration seam; the cycle writes Markdown only. (The one version-dependent CLAIM the spec makes — that Strawberry's `cls is None and name is not None` overload returns a `ScalarDefinition` without emitting `DeprecationWarning` — was re-verified by Worker 0 at the installed version, recorded below; it is a citation fix, not a behavioral change needing a floor run.)
Pre-flight: passed on 2026-08-18 with two recorded deviations (below); baseline: DIRTY with a concurrent session's work.

## Cycle shape — residual reconciliation, not a fresh build

`DONE-025-0.0.7` shipped inside the `0.0.7` joint cut at commit `b1a6d01f` ("Finish docs/spec-020-scalar_map_helper-0_0_7.md" — the spec still carried its pre-renumber number 020 at ship time). Worker 0 verified every Definition-of-done item against HEAD before writing this plan (evidence in `## Pre-dispatch verification`): **nothing was skipped in the code, and the shipped `scalars.py` matched the spec's pinned code block byte-for-byte.**

What did NOT land is the spec's `-rationale.md` sibling. And the spec has since drifted from HEAD, because five later cards changed surfaces it makes present-tense factual claims about. So this cycle has exactly two units of work, both Markdown, both Worker 1's:

1. The rationale MOVE / authoring that `docs/builder/BUILD.md` `## Spec rationale extraction` requires (pre-flight step 7, deferred into Slice 1 because the extraction IS this cycle's work rather than its precondition).
2. Spec reconciliation: rewrite every drifted claim so the spec states the CURRENT contract directly, with no chronology, no amendment block, no "as of" hedge. Every change is recorded in the rationale file, never in the spec.

Per the maintainer's dispatch instruction, Workers 2 and 3 are dispatched only if a slice turns out to need a **code** change. Nothing Worker 0 found needs one: the focused suites are green and the spec's pinned contract still holds in `django_strawberry_framework/scalars.py`.

**Scope fence (maintainer instruction):** this cycle edits **spec files and `.py` source only**. No closeout-agentflow edits. No `KANBAN.md` / `KANBAN.html` / `docs/GLOSSARY.md` / `CHANGELOG.md` / `docs/TREE.md` / `docs/README.md` / `GOAL.md` / `TODAY.md` / `README.md` edits, and no `examples/fakeshop/db.sqlite3` writes — the doc-side residue Worker 0 found in those files is catalogued for the maintainer in the final gate's deferred-work catalog instead. No archival step: the spec and its `-terms.csv` are **already** at `docs/SPECS/` and `docs/SPECS/appx/`, so the "archive the spec" instruction is discharged by verification, not by a move. Every artifact this cycle creates carries `025` in its filename.

## Pre-flight outcome and deviations

- Step 1 (baseline): DIRTY. Another session is mid-cycle on `spec-024` (its `worker-memory/worker-2-024.md` and `worker-3-024.md` were written 2026-08-18 23:36 / 23:43, during this pre-flight). A THIRD cycle on `spec-026` appeared on the tree during Slice 1 — flagged by the Slice 1 final-verification pass, which dirtied `examples/fakeshop/apps/scalars/models.py` and `examples/fakeshop/test_query/test_scalars_api.py`; untouched and out of scope. Baseline-dirty out-of-scope files are listed below.
- Step 2 (`scripts/review_inspect.py`): smoke run on `django_strawberry_framework/scalars.py` exited 0, writing `docs/shadow/django_strawberry_framework__scalars.overview.md` + `.stripped.py`.
- Step 3 (artifact reset): **DEVIATION — old `bld-*.md` / `build-*.md` were NOT deleted.** `bld-003-final.md`, `bld-slice-1a-024-planned_vs_head.md`, `bld-slice-1b-024-divergence_and_floor.md`, `bld-slice-3-024-rename_rot_sweep.md`, `build-023-multi_db-0_0_7.md`, and `build-024-django_trac_37064_hardening-0_0_7.md` are live records — the last four belong to the concurrent `spec-024` cycle. Deleting them is the one irreversible pre-flight mistake and `AGENTS.md` rule 34 forbids reverting concurrent work. This cycle therefore uses `-025`-suffixed artifact paths, verified absent.
- Step 4 (`.gitignore`): `docs/shadow/`, `docs/builder/worker-memory/`, `docs/builder/temp-tests/` all listed.
- Step 5 (scratch cleared): **DEVIATION — scratch was NOT cleared**, same reason as step 3. `worker-memory/worker-2-024.md` and `worker-3-024.md` are the concurrent cycle's live notebooks. This cycle's workers write `docs/builder/worker-memory/worker-<N>-025.md`, which Worker 0 created empty.
- Step 6 (`check_spec_glossary`): `OK: 17 terms - all have glossary entries and at least one spec link.` (exit 0) — the count the spec's own DoD 9a pins.
- Step 7 (rationale extraction): NOT yet done — it is Slice 1 of this cycle.

### Baseline-dirty out-of-scope files (never edit, never revert)

`CHANGELOG.md`, `KANBAN.html`, `KANBAN.md`, `django_strawberry_framework/_strawberry_patches.py`, `django_strawberry_framework/optimizer/hints.py`, `docs/GLOSSARY.md`, `docs/SPECS/appx/spec-021-apps-0_0_7-terms.csv`, `docs/SPECS/spec-021-apps-0_0_7.md`, `docs/SPECS/spec-022-export_schema-0_0_7.md`, `docs/bug_hunt/*`, `docs/feedback.md`, `examples/fakeshop/apps/scalars/models.py`, `examples/fakeshop/db.sqlite3`, `examples/fakeshop/test_query/test_scalars_api.py`, `tests/optimizer/test_hints.py`, every `docs/builder/` artifact named under step 3, `docs/builder/DONE/`, and the untracked `docs/SPECS/appx/spec-022-export_schema-0_0_7-rationale.md`.

**Concurrent-writable tracked binary / generated files:** `examples/fakeshop/db.sqlite3`, `KANBAN.md`, `KANBAN.html`, `docs/GLOSSARY.md`. This cycle plans NO edit to any of them, so any churn observed in them is the other session's and must be left alone.

## Pre-dispatch verification (Worker 0, against HEAD)

Every Definition-of-done item read against source before dispatch. Findings are handed to Worker 1 as verified inputs, not as hypotheses.

### Delivered in full — no code gap

Ship commit `b1a6d01f` (2026-05-27) touched every file the spec's DoD names: `django_strawberry_framework/scalars.py`, `django_strawberry_framework/__init__.py`, `tests/test_scalars.py`, `tests/base/test_init.py`, `tests/types/test_converters.py`, `examples/fakeshop/config/schema.py`, `docs/README.md`, `docs/GLOSSARY.md`, `GOAL.md`, `TODAY.md`, `KANBAN.md`, `CHANGELOG.md`, and the terms CSV.

| DoD | Verified at | Result |
| --- | --- | --- |
| 1 — canonical spec filename + terms CSV | `docs/SPECS/spec-025-scalar_map_helper-0_0_7.md`, `docs/SPECS/appx/spec-025-scalar_map_helper-0_0_7-terms.csv` | both present at the archived paths; `check_spec_glossary` reports `OK: 17 terms` |
| 2 — bare `NewType`, `_BIGINT_SCALAR_DEFINITION`, `_PACKAGE_SCALAR_MAP`, `strawberry_config`, suppression removed | `django_strawberry_framework/scalars.py` | all present; signature is `(*, extra_scalar_map=None, **config_kwargs)`; no `import warnings`, no `catch_warnings` anywhere in the file |
| 3 — `__init__.py` re-export + `__all__` | `django_strawberry_framework/__init__.py` #"from .scalars import" and #"__all__" | `strawberry_config` imported and last in `__all__` |
| 4 — 13 factory + 2 integration tests | `tests/test_scalars.py` | all 15 present under the spec-pinned names, single pytest item each, no `parametrize` |
| 5 — deprecation regression unchanged | `tests/test_scalars.py::test_package_import_does_not_emit_strawberry_deprecation_warning` | present; still the `-W error::DeprecationWarning` subprocess shape |
| 6 — `__all__` export pin | `tests/base/test_init.py` #"strawberry_config" | present in the pinned tuple |
| 6a — `tests/types/test_converters.py` migration | ship commit `b1a6d01f` diffstat (`22 +-`) | all 10 spec-named sites migrated at ship; 6 have since MOVED live (see divergence D8) |
| 6b — `tests/test_scalars.py` module docstring | file header | carries the appended two-integration-test sentence verbatim |
| 7 — fakeshop schema migration | `examples/fakeshop/config/schema.py` | `strawberry_config` imported and passed as `config=` (constructor has since become `DjangoSchema` — divergence D9) |
| 8 — per-app schemas unmodified | `apps/library/schema.py`, `apps/products/schema.py` | neither constructs a schema |
| 9 / 9a — GLOSSARY entry + index + exports + CSV row | `docs/GLOSSARY.md` `## strawberry_config`, index table, Public exports; terms CSV | entry sits between `## Specialized scalar conversions` and `## Strictness mode` as pinned; CSV row present |
| 10 / 11 / 12 — `docs/README.md`, `GOAL.md`, `TODAY.md` | each file | `config=strawberry_config()` present in every schema-construction block the spec named that still exists |
| 16 — CHANGELOG Added / Changed / Removed + `[0.0.6]` Notes removal | `CHANGELOG.md` | all three bullets present verbatim; `grep -c "Migration to a"` reports 0 |
| 18 — `__all__` widened by exactly one name | ship commit `b1a6d01f` `__init__.py` diff (`3 +-`) | one name added at ship |
| 20 — ruff clean | working tree | verified below |

**The shipped `scalars.py` matched the spec's pinned code block exactly**, including the two constructs later hardening replaced: `extra = dict(extra_scalar_map) if extra_scalar_map else {}` and `', '.join(sorted(getattr(k, '__name__', repr(k)) for k in collisions))`. There is therefore no ship-time gap to chase — every divergence below is post-ship.

### Contract still holds at the installed version

- `.venv/lib/python3.14/site-packages/strawberry/types/scalar.py #"if cls is None and name is not None"` still returns a `ScalarDefinition` directly (line 259).
- The `DeprecationWarning` still lives only on the `cls is not None` path (`#"Passing a class to strawberry.scalar"`, line 280).
- Installed: `strawberry-graphql 0.323.2`, `django 6.1`, Python 3.14. Declared floors: `strawberry-graphql>=0.316.0`, `Django>=5.2.16`, `requires-python >=3.10,<4.0`.

### Test evidence

- `uv run pytest tests/test_scalars.py tests/base/test_init.py tests/types/test_converters.py --no-cov -q` → **134 passed**.
- `uv run pytest examples/fakeshop/test_query/test_scalars_api.py --no-cov -q` → **29 passed**.

### Verified post-ship divergences handed to Worker 1

Each is a place the spec makes a present-tense claim that is false at HEAD. Worker 1 rewrites the spec to the current contract and records the change in the rationale file.

| # | Spec surface | Claim | Reality at HEAD | Attribution |
| --- | --- | --- | --- | --- |
| D1 | header line 3, Decision 8, Slice 5, DoD 16/17, Risks item 1 | the card lands under `[Unreleased]`, to be promoted to `[0.0.8]`; `0.0.7` was cut 2026-05-23 | the three bullets landed under `## [0.0.7] - 2026-05-27`; the card shipped **inside** the `0.0.7` cut. `docs/GLOSSARY.md` index reads `shipped (0.0.7)`, not the `shipped ([Unreleased])` placeholder the spec pins | ship commit `b1a6d01f`; `KANBAN.md` line 62 records seven `0.0.7` cards incl. `DONE-025-0.0.7`, tag `0.0.7` at `72f6cd9` |
| D2 | Decision 3 pinned block, Slice 1 import-surface bullet | `scalars.py` has no module `__all__` | the module now declares `__all__ = ["BigInt", "Upload", "UploadDefinition", "strawberry_config"]` | spec-037 (`4a25bf42` / `aec1bd4e` / `66d01b4a`) |
| D3 | Non-goals #3, Decision 2 justification, Risks item 5 | `Upload` "slots in by appending to `_PACKAGE_SCALAR_MAP`" | **false.** `Upload` is Strawberry's own `NewType("Upload", bytes)`, already in `DEFAULT_SCALAR_REGISTRY`, so it is re-exported with **no** `_PACKAGE_SCALAR_MAP` entry — pinned by `tests/test_scalars.py::test_strawberry_config_scalar_map_excludes_upload` and `::test_upload_field_resolves_under_plain_strawberry_config`. The forward-compatibility prediction this card made was wrong in mechanism while right in outcome (no change to `strawberry_config` was needed) | spec-037 |
| D4 | DoD 2, Decision 3 justification bullet 3 | `_parse_bigint` / `_serialize_bigint` "unchanged from `0.0.6`" | both hardened against hostile subclasses: `int.__int__(value)`, `str.__str__(value)`, `int.__str__(value)`, `_safe_arg_repr` / `_safe_type_name` in messages, `# noqa: TRY004` on the bool raise. The wire format is unchanged; the bodies are not | `f274b2a4` (REVIEW 0.0.7 corrections), `dc00f4a6` (hostile-metadata guard) |
| D5 | Decision 3 pinned block; Edge case #"extra_scalar_map={}" is equivalent | `extra = dict(extra_scalar_map) if extra_scalar_map else {}` | now an explicit `if extra_scalar_map is None:` branch plus a `try/except BaseException` materialization guard raising `ValueError("strawberry_config(extra_scalar_map=...) must be materializable; ...")`. The old form was a **truthiness test on a value that can be absent** (`docs/builder/BUILD.md` `### Fail-open shapes`) and it let a hostile mapping's own exception escape the promised factory boundary. New error shape absent from `## Error shapes` | `dc00f4a6` |
| D6 | Edge case #"Collision-error message stability" | the `repr(k)` fallback "is not separately tested" | `getattr(k, '__name__', repr(k))` was replaced by `_safe_scalar_map_key_label`, which swallows a raising `__name__` descriptor and rejects a non-`str` `__name__`; it **is** now tested, by `tests/test_scalars.py::test_strawberry_config_collision_message_survives_hostile_key` | `dc00f4a6` |
| D7 | Decision 7 test count, Test plan headings, DoD 4, Edge case #"tests/test_scalars.py test count" | "fifteen new pytest items"; file carries "22+15 = 37+" | two further factory tests landed post-ship (`test_strawberry_config_rejects_unmaterializable_extra_scalar_map`, `test_strawberry_config_collision_message_survives_hostile_key`); the file now holds 53 `def test_` items, four of them spec-037's `Upload` pins | `dc00f4a6`, spec-037 |
| D8 | Slice 2 `tests/types/test_converters.py` bullet, DoD 6a, Decision 7 rejected alternative #3, Risks item #"The example fakeshop schema does not exercise `BigInt`" | 10 migrated sites in the BigInt section; a live `test_query/` BigInt test "Rejected for `0.0.7`" because "the fakeshop models do not include `BigIntegerField`" | **reversed by `DONE-026-0.0.7`.** Six of the ten (`test_big_integer_field_maps_to_bigint_in_schema`, `..._nullable_in_schema`, `test_positive_big_integer_field_maps_to_bigint_in_schema`, `test_bigint_serializes_query_result_as_string_via_schema_execution`, `test_bigint_parses_string_argument_via_schema_execution`, `test_bigint_parses_int_argument_via_schema_execution`) no longer exist anywhere — they were promoted to live `/graphql/` coverage on the new `apps.scalars` app (`examples/fakeshop/test_query/test_scalars_api.py`), the file's own banner comment records the move, and four rejection/edge tests remain. `apps.scalars.models` now carries `signed_big = BigIntegerField` / `unsigned_big = PositiveBigIntegerField`, and `apps.library.models` a `lifetime_fines_cents = BigIntegerField` | `DONE-026-0.0.7` (spec-026) |
| D9 | Decision 9, Slice 3, DoD 7, and every `strawberry.Schema(query=Query, config=strawberry_config(), extensions=[DjangoOptimizerExtension()])` example in `## User-facing API` | fakeshop constructs `strawberry.Schema(...)`; the optimizer is passed as an instance | `examples/fakeshop/config/schema.py` now builds `DjangoSchema(...)` (required for generated mutations since `0.0.14`), and the documented optimizer shape is a factory `extensions=[lambda: _optimizer]` (an instance is deprecated engine usage). `config=strawberry_config()` is unchanged in both | spec-036 / spec-044 era; `docs/README.md` #"The optimizer is a module-level singleton wrapped in a factory" |
| D10 | DoD 3, DoD 18, Edge case #"Final tuple reads:" | `from .scalars import BigInt, strawberry_config`; `__all__` = the nine-name tuple enumerated verbatim | the import line is `from .scalars import BigInt, Upload, strawberry_config` and `__all__` now holds 30+ names. `strawberry_config` is still **last** in the tuple, so the ASCII-sort rule the Decision rests on still holds — only the enumeration is stale | many later cards |
| D11 | Risks item 1 fallback; Decision 8 alternative #2 | a re-tag would move the spec to `docs/spec-020-scalar_map_helper-0_0_8.md` / `WIP-ALPHA-020-0.0.8` | pre-renumber artifact. The 2026-07-30 board renumber made `020` `DjangoListField`; this card is permanently `DONE-025-0.0.7` and the spec is at its archived structured path. The hypothetical is dead, not merely stale | card renumber 2026-07-30 |
| D12 | link definitions `[config]`, `[scalar]`, and every inline `.venv/lib/python3.10/site-packages/...` citation; Risks item #"Strawberry version pin compatibility" | paths under `python3.10`; pinned constraint `strawberry-graphql>=0.262.0` | the on-disk venv is `.venv/lib/python3.14/`, so every one of those citations is a dead path. Every recently reconciled spec (023, 042, 043, 044) uses `python3.14`. `pyproject.toml` declares `strawberry-graphql>=0.316.0` and `Django>=5.2.16` | dependency bumps; spec-049 |
| D13 | Slice 4 `docs/TREE.md` bullet ("the entry stays as-is"); DoD 13; DoD 14 (`README.md` is NOT edited); Slice 4 `docs/README.md` Relay-Node bullet | TREE's `scalars.py` line reads "`BigInt` public scalar"; root `README.md` untouched; the Relay Node example constructs a schema | TREE (script-rendered from the module docstring) now reads "Public GraphQL scalars + the ``strawberry_config()`` schema-config factory"; root `README.md` line 80 names `strawberry_config()` in its `0.0.7` status bullet; the `docs/README.md` Relay Node example no longer constructs a schema at all, so that sub-bullet's target is gone | later doc work |

### Verified NOT defects (do not re-raise)

- **`[spec-013]` / `[spec-011]` label rot:** already repaired. `grep -c 'spec-013'` and `grep -c 'spec-011'` both report **0** in this spec. The `TODO-ALPHA-051-0.0.15` KANBAN bullet still describes six occurrences here; that description is itself stale and is catalogued for the maintainer, not fixed by this cycle.
- **Card ids:** every `DONE-NNN` in the spec (`DONE-025-0.0.7`, `DONE-024-0.0.7`, `DONE-037-0.0.11`) is the live post-renumber id. No card-id rot to sweep.
- **`docs/SPECS/appx/spec-025-...-terms.csv` rows for `DjangoFileType` / `DjangoImageType`** cite `TODO-ALPHA-028-0.0.11`, which shipped as `DONE-037-0.0.11`. Out of this cycle's scope fence (the CSV is not a spec file and edits to it would diverge one surface of a multi-surface cluster); catalogued for the maintainer.
- **`docs/README.md` `DjangoSchema(...)` error-policy snippets omitting `config=`** are spec-048 illustrations scoped to `error_policy=`, not a spec-025 migration gap. Docs are outside the scope fence regardless.

## Post-gate addendum - D14 (found after `bld-final-025.md` was accepted)

The cycle was reopened once, after the final gate, on a Worker 0 re-derivation of the deferred-work catalog. It produced a fourteenth divergence the whole cycle had missed, and a correction to two figures in this plan's own hand-off.

**D14 - `## Decision 9`'s schema-construction census.** The spec asserted `examples/fakeshop/config/schema.py` is "the project's sole schema-construction site" and that "schema construction happens once, in `config/schema.py`", with a matching "the one fakeshop schema-construction call" in `## Risks`. `examples/fakeshop/strategy_schemas.py` constructs a second one, and does it with `config=strawberry_config()`. It was added post-ship by `8fe01840` (2026-07-07), six weeks after the ship commit; `git merge-base --is-ancestor b1a6d01f 8fe01840` exits 0. Non-test schema-construction sites in the repo are now two, not one. Discharged by Slice 3.

**No code gap here either.** The rule this card established propagated to `strategy_schemas.py` unprompted, by an unrelated optimizer DRY pass that had no reason to know about it - which is evidence for Decision 9 rather than against it. What was false is the spec's description of the tree, not the tree.

**Why no pass in this cycle had it in view.** The `### Verified post-ship divergences handed to Worker 1` table below was built by sweeping the spec's claims against `HEAD` file-by-file, over the files the Definition of done names. `strategy_schemas.py` is not one of them - it did not exist at ship - so a file-by-file sweep could not reach it, and Slice 2 then swept for the divergences it was handed. The instrument that would have caught it is a sweep of the spec's own positive census vocabulary (`sole`, `only`, `happens once`, `every ... added later`) resolved against the tree. That is the same blind spot the corpus-wide lesson names twice over: a census spelled positively is invisible to a negative-vocabulary sweep, and a census whose population lies outside the DoD's file list is invisible to a per-file one.

**Two figures in Worker 0's dispatch brief were wrong, and Slice 3 corrected them.** They were asserted in the brief that carried D14 to Slice 3, not in the table below, so the correction lands here rather than as an edit to that table. The fakeshop modules that build schemas are **nine**, not the six the brief claimed (seven `test_query/` modules plus `apps/library/tests/test_generic_connection.py` and its `_sharded` sibling), and **two of them build with no `config=` at all** - `test_query/test_products_visibility_api.py` (7 builds, 0) and `test_query/test_transport_api.py` (1 of 2). Neither is a gap: neither resolves `BigInt`, and Decision 5's rule is owed by a `BigInt`-resolving schema, not by every schema - a stronger fact than the compliance census the brief claimed. Both instruments used to measure it are traps: `grep -c strawberry_config` counts the import line into the total, and `grep -oE 'config=strawberry_config\(\)'` with empty parens under-reports `test_optimizer_auto_api.py`, which passes `config=strawberry_config(extra_scalar_map={...})`.

## Artifact list

- `docs/builder/bld-slice-1-025-rationale_authoring.md`
- `docs/builder/bld-slice-2-025-spec_reconciliation.md`
- `docs/builder/bld-final-025.md`
- `docs/builder/bld-slice-3-025-decision_9_census.md`

## Checklist

- [x] Slice 1: Rationale authoring (`docs/SPECS/appx/spec-025-scalar_map_helper-0_0_7-rationale.md`) -> `docs/builder/bld-slice-1-025-rationale_authoring.md`
- [x] Slice 2: Spec reconciliation (D1-D13) -> `docs/builder/bld-slice-2-025-spec_reconciliation.md`
- [x] Final test-run gate -> `docs/builder/bld-final-025.md`
- [x] Slice 3: Decision 9 census repair (D14) -> `docs/builder/bld-slice-3-025-decision_9_census.md`

No cross-slice integration pass artifact: with one writing role and Markdown-only slices there is no cross-slice DRY surface to scan. That judgement held for DRY and for rationale/spec coherence, which Slice 2's own pass and then the final gate did resolve - the final gate found and fixed three coherence defects Slice 2 had left. What neither covered is a different axis: whether the set of divergences handed to Slice 2 was complete. D14 was found only by re-deriving the catalog after the gate, so treat the divergence *inventory* as the surface an integration pass owes a reconciliation cycle - not the consistency of the text that discharges it.
