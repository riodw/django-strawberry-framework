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

## Post-gate addendum - D14 (found after the final gate had accepted)

The cycle was reopened once, after the final gate, on a Worker 0 re-derivation of the deferred-work catalog. It produced a fourteenth divergence the whole cycle had missed, and a correction to two figures in this plan's own hand-off.

**D14 - `## Decision 9`'s schema-construction census.** The spec asserted `examples/fakeshop/config/schema.py` is "the project's sole schema-construction site" and that "schema construction happens once, in `config/schema.py`", with a matching "the one fakeshop schema-construction call" in `## Risks`. `examples/fakeshop/strategy_schemas.py` constructs a second one, and does it with `config=strawberry_config()`. It was added post-ship by `8fe01840` (2026-07-07), six weeks after the ship commit; `git merge-base --is-ancestor b1a6d01f 8fe01840` exits 0. Non-test schema-construction sites in the repo are now two, not one. Discharged by Slice 3.

**No code gap here either.** The rule this card established propagated to `strategy_schemas.py` unprompted, by an unrelated optimizer DRY pass that had no reason to know about it - which is evidence for Decision 9 rather than against it. What was false is the spec's description of the tree, not the tree.

**Why no pass in this cycle had it in view.** The `### Verified post-ship divergences handed to Worker 1` table below was built by sweeping the spec's claims against `HEAD` file-by-file, over the files the Definition of done names. `strategy_schemas.py` is not one of them - it did not exist at ship - so a file-by-file sweep could not reach it, and Slice 2 then swept for the divergences it was handed. The instrument that would have caught it is a sweep of the spec's own positive census vocabulary (`sole`, `only`, `happens once`, `every ... added later`) resolved against the tree. That is the same blind spot the corpus-wide lesson names twice over: a census spelled positively is invisible to a negative-vocabulary sweep, and a census whose population lies outside the DoD's file list is invisible to a per-file one.

**Two figures in Worker 0's dispatch brief were wrong, and Slice 3 corrected them.** They were asserted in the brief that carried D14 to Slice 3, not in the table below, so the correction lands here rather than as an edit to that table. The fakeshop modules that build schemas are **nine**, not the six the brief claimed (seven `test_query/` modules plus `apps/library/tests/test_generic_connection.py` and its `_sharded` sibling), and **two of them build with no `config=` at all** - `test_query/test_products_visibility_api.py` (7 builds, 0) and `test_query/test_transport_api.py` (1 of 2). Neither is a gap: neither resolves `BigInt`, and Decision 5's rule is owed by a `BigInt`-resolving schema, not by every schema - a stronger fact than the compliance census the brief claimed. Both instruments used to measure it are traps: `grep -c strawberry_config` counts the import line into the total, and `grep -oE 'config=strawberry_config\(\)'` with empty parens under-reports `test_optimizer_auto_api.py`, which passes `config=strawberry_config(extra_scalar_map={...})`.

## Final gate record

`docs/builder/bld-final-025.md` was **deleted at close** (maintainer instruction, 2026-08-19). This section is what
survives of it; the deferred-work catalog it carried is folded in below, and the two spec-side findings with forward
value live in the committed rationale rather than here.

**Verdict: `final-accepted`**, returned once on the original thirteen-divergence record and again after Slice 3.
Nothing failed, so no slice owns a failing behavior.

**The gate, verbatim.** Full sweep `6179 passed, 40 skipped` at exit 0. `manage.py check` clean.
`makemigrations --check --dry-run` -> `No changes detected`. `ruff format --check .` -> 424 files already formatted.
`ruff check .` -> All checks passed. `git diff --check` -> no output. `check_spec_glossary` -> `OK: 17 terms` exit 0,
the count Definition-of-done item 9a pins.

**Floor verification: scope `none`, and no floor venv was built.** Confirmed against a diff that contains no
executable line - a Markdown-only cycle cannot regress a floor, so no run was owed. The same reasoning retires the
`pytest` obligation for Slice 3.

**The gate's substantive finding was about this cycle's own instruments.** The absent integration pass was correctly
absent for DRY and insufficient for claim coherence: three defects survived Slice 2 into the durable rationale and
only the gate caught them - a mechanical `python3.10` -> `python3.14` sweep that swept the one sentence naming the old
spelling on purpose and left it self-contradictory; a present-tense byte count that a later slice falsified by
appending to the same file; and a dead `KANBAN.md` substring citation, pre-existing at `HEAD`, that survived because
the substring audit ran on the spec and not on the file the spec's own text had been moved into. One rule covers all
three: **run every sweep on both files of the spec/rationale pair, not on the file the slice happens to be editing.**
The corollary is why no byte count appears in this section: never write a present-tense measurement of a file a later
pass will edit.

**Counts, adjudicated rather than bumped.** Nothing in the original pass was falsified by Slice 3, because every
count in it is scoped to a pass that genuinely ended at thirteen - including "three coherence defects", which counts
defects this gate found, not divergences. The record heading moved `(D1-D13)` -> `(D1-D14)` with its slug moved at
both use sites, while the two "thirteen" statements scoped to Slice 2's own action were deliberately kept.

**Two spec-side rules the gate verified, both durable in the rationale, both easy to break by "fixing" them.** The
spec's **9** unresolved in-page anchors are deliberate: every one sits in text the spec pins verbatim for
`docs/GLOSSARY.md`, resolves in that file, and rewriting them as reference links would make the pinned bodies differ
from the file they pin - the exact defect the pin exists to prevent. The gate also confirmed the pin is currently
exact, diffing the blockquoted `## strawberry_config` body IDENTICAL against the live entry. See the rationale's
`## Verification performed by the spec reconciliation (Slice 2)`.

## Deferred-work homing

The next spec author's reading list, moved here verbatim from the final-gate artifact when that artifact was deleted at close. **Revised at the reopening**: every homing target below was verified against `KANBAN.md` before being written, and two of Worker 0's proposed attributions were wrong and are corrected in place. Every population was re-derived; where a figure differs from the artifact or message that supplied it, the difference is stated. **Everything here is outside this cycle's scope fence** (spec files and `.py` source only) except where noted.

**Card ids verified on the board before use** — `grep -nE '^#+ .*(ALPHA-05[012])' KANBAN.md`: `TODO-ALPHA-050-0.0.15 - Extract DjangoDebugExtension into the standalone django-strawberry-debug package` (L157), `TODO-ALPHA-051-0.0.15 - Boundary hardening and system-wide DRY squeeze` (L211), `TODO-ALPHA-052-0.1.0 - Beta release (cleanup, verification, alpha -> beta)` (L315). All three exist with those titles.

**Two corrections to the homing proposal, both about card ownership.** `KANBAN.md` lines 353 and 364 were proposed as `TODO-ALPHA-051-0.0.15`'s in the original catalog and are **card 052's**: the heading at L315 is `TODO-ALPHA-052-0.1.0` and `awk`-scanning L315-L400 for `^#+ \[` returns no further heading, so both lines sit inside card 052's section. The original catalog's "board-side residue for whoever owns `TODO-ALPHA-051-0.0.15`" on the CHANGELOG item is therefore wrong; it is 052's own bullet, which makes both items self-corrections on that card rather than cross-card hand-offs.

**Maintainer decisions — both home on `TODO-ALPHA-052-0.1.0`, flagged as contract calls**

Homing verified: card 052's board-DB spec-path-rot bullet (`KANBAN.md` L359) already carries the twin question in its own words — "Whether a Done card's DoD should stay a historical record or become navigable is a maintainer contract call" — so both items below land beside an open question of the same kind rather than opening a new one.

- **Should a spec pin a verbatim body for a DB-generated file at all?** (Slice 2's artifact `### Notes for Worker 1`.) The spec's `## Doc updates` pins a long past-tense Done body for `KANBAN.md`, and Definition-of-done item 15 requires `KANBAN.md` to carry it. `KANBAN.md` is rendered from the fakeshop kanban DB, and the live `DONE-025-0.0.7` card carries a generated body instead — verified by the final gate by reading the card: Priority / Status / Relative size / Labels / Spec, a 17-row glossary-terms table, two package files, a `#### Verified in upstream` line, and a one-line `#### Note`. Not fixable from the spec side: the fix is either a DB edit plus a regenerate (`KANBAN.md` is fenced, and DB-backed per `AGENTS.md`) or the general decision that a spec should not pin a verbatim body for a generated file, which applies corpus-wide rather than to `025`. Rejected alternatives the slices recorded: Slice 2 narrowed DoD 15 to pin the **body** rather than the card **number** (as far as the spec side can go) and explicitly declined to delete the pinned body, since deleting it would drop the only record of what the card claimed to have written. No slice recorded an alternative of hand-editing `KANBAN.md`, which the scope fence and `AGENTS.md` both forbid.
- **`KANBAN.md`'s live version-bump policy contradicts the one this spec's Decision 8 rests on.** New at the final gate. Decision 8's moved justification cited `KANBAN.md #"The last \`0.0.7\` card to ship owns the version bump"`; that substring exists nowhere in `KANBAN.md`, at `HEAD` or now. The nearest live statement is `KANBAN.md` line 64 — "The version bump from `0.0.8` is owned by the joint `0.0.9` cut, **not any single card**, per Decision 11 of `docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md`" — which is the opposite ownership rule. The final gate dropped the dead substring anchor and kept the citation (its third coherence defect, recorded under `## Final gate record` above); reconciling *which* policy is current is a maintainer contract call spanning `spec-025`, `spec-029` and the board, not a link repair a rationale companion may make.

**Fenced-file doc residue (this cycle's scope fence closed these; the catalog is their only route to the maintainer)**

The five terms-CSV rows in the next two entries are **one edit** and home together on `TODO-ALPHA-052-0.1.0`. Reason to record: the fix is a CSV edit plus an `import_spec_terms` re-run, the same ORM-edit-plus-regenerate instrument as that card's board-DB spec-path-rot bullet (`KANBAN.md` L359) and its `CardItem` 723 bullet (L363), which names that instrument explicitly — "DB-backed, so the fix is an ORM edit plus regenerate - the same instrument as this card's board-DB spec-path-rot bullet".

**Checker gap worth adding to the same card, all three legs verified rather than asserted.** The CSV's `notes` column is a value no gate compares and nothing renders:

- **Written** by `import_spec_terms` into `GlossarySpecMention.notes` — `examples/fakeshop/apps/glossary/management/commands/import_spec_terms.py` reads `row.get("notes")` and passes it in the `update_or_create` defaults of `_sync_spec_mentions`; `GlossarySpecMention.notes` is a `TextField(blank=True, default="")` in `examples/fakeshop/apps/glossary/models.py`.
- **Not read** by `check_spec_glossary` — `grep -n 'notes' scripts/check_spec_glossary.py` returns exactly **two** hits, a docstring line and an `--help` string. `load_terms` is typed `-> list[tuple[str, str]]` and appends `(term, anchor)` only.
- **Fetched but never rendered** by `scripts/build_glossary_md.py` — its GraphQL query selects `notes` inside `allGlossarySpecMentions`, but the only reads out of that payload are `specPath` (a set comprehension) and `len()` for a progress line. `grep -n '"notes"' scripts/build_glossary_md.py` returns nothing.

So a stale `notes` row cannot fail a gate and cannot appear in a rendered doc, which is why all five rows below rotted silently. That is the durable half of this item; the five row fixes are the cheap half.

- **`docs/SPECS/appx/spec-025-scalar_map_helper-0_0_7-terms.csv`: the `DjangoFileType` and `DjangoImageType` rows cite `TODO-ALPHA-028-0.0.11`, which shipped as `DONE-037-0.0.11`.** (Slice 1's artifact and Slice 2's artifact `### Notes for Worker 1`; this plan's `### Verified NOT defects` above.) Re-derived: **2** occurrences, one per row. The live `DONE-025-0.0.7` KANBAN card's own glossary table already records both terms as `shipped (0.0.11)`, so the CSV is the last surface carrying the TODO id. The CSV is not a spec file, and Slice 2's reason for not touching it stands: editing one surface of a multi-surface cluster leaves it divergently rather than uniformly wrong.
- **Three further stale rows in the same CSV, not recorded by either slice.** New this pass, and they belong with the item above because they land in the same file and the same edit. (a) The `Upload scalar` row reads "Next package-defined scalar (planned for `0.0.11`); reuses this card's helper unchanged" — `Upload` shipped, and D3 established that it is *not* package-defined and needs no `_PACKAGE_SCALAR_MAP` entry, so the row states the mechanism D3 retired. (b) The `DjangoOptimizerExtension` row cites the consumer pattern as `extensions=[DjangoOptimizerExtension()]`, the instance shape D9 replaced with `extensions=[lambda: _optimizer]` throughout the spec. (c) The `Strictness mode` row reads "the new GLOSSARY entry `strawberry_config` **ought to be ordered** between ..." — future tense for something Slice 4 did in `0.0.7`.
- **A KANBAN bullet still describes six `[spec-013]` occurrences in this spec -> `TODO-ALPHA-052-0.1.0`, as a self-correction.** (Both slices' `### Notes for Worker 1`; this plan's `### Verified NOT defects` above.) **Card attribution corrected at the reopening:** the original catalog and both slice artifacts named `TODO-ALPHA-051-0.0.15`; the bullet is at `KANBAN.md` **line 353, inside card 052's section** (heading at L315, no further `^#+ \[` heading through L400), so it is that card's own bullet and the fix is a self-correction, not a hand-off. Re-derived: `grep -o 'spec-013' | wc -l` and `grep -o 'spec-011' | wc -l` both report **0** in `docs/SPECS/spec-025-scalar_map_helper-0_0_7.md`. The label rot is repaired here; the L353 description of it is what is stale. Two clauses of that bullet decay with it: its claim that this spec "carries **six occurrences - five uses plus the definition line all five depend on**", and its instruction that the `[spec-013]` half "lands whole on this sweep, with no half for `TODO-ALPHA-051-0.0.15`" — which no longer has an `025` component to land. Note the bullet's own warning against carrying the smaller figure (five) forward: neither figure has a referent now.
- **The spec's quoted `CHANGELOG.md` `### Added` body omits a trailing clause the landed bullet carries.** (Slice 2's artifact `### Notes for Worker 1`.) Verified: `CHANGELOG.md` line 174 ends `... See [\`strawberry_config\`][glossary-strawberry-config]. Tracked as [025-warning_free_scalar_registration_via_strawberryconfigscalar_map-0.0.7][card-...] in [\`KANBAN.md\`][kanban].`; the spec's quote stops at the `See ...` sentence. The clause is appended by the kanban tooling rather than authored, so quoting the authored text is defensible — recorded so the next reader does not rediscover it as a defect. `CHANGELOG.md` is fenced.
- **`docs/README.md`'s `DjangoSchema(...)` error-policy snippets omit `config=`.** (Build plan `### Verified NOT defects`.) Confirmed as **not** a `spec-025` migration gap: they are spec-048 illustrations scoped to `error_policy=`. `docs/README.md` carries `strawberry_config` in 9 places. Left as a recorded non-defect so a future sweep does not re-raise it; docs are fenced regardless.

**Already discharged — do NOT carry forward**

- **`CHANGELOG.md`'s `## [0.0.7]` pre-renumber card labels.** (Slice 2's artifact `### Notes for Worker 1`, which recorded the `047-...` label at 3 occurrences as open; and `KANBAN.md` line 364, which measures the whole population at 14 across 7 labels.) **Fixed in the working tree by a concurrent session.** At `HEAD` the section carries 14 pre-renumber labels; in the worktree it carries **0** — re-confirmed at the reopening, `grep -oE '\[0(1[6-9]\|4[6-8])-[a-z0-9_]+-0\.0\.7\]' CHANGELOG.md` returns nothing — all seven now post-renumber. **The residual is the board's own measurement, and its card attribution is corrected at the reopening:** `KANBAN.md` line 364 is inside card **052**'s section, not card 051's as this catalog first said, so its now-stale figure of 14 is a self-correction for `TODO-ALPHA-052-0.1.0` and should ride the same edit as the L353 `[spec-013]` bullet above — same card, same file, same class of stale measurement. Not open work for a spec author either way.

**Package docstring schema examples split on `config=strawberry_config()` -> `TODO-ALPHA-051-0.0.15`, as a maintainer doc-style call**

New at the reopening, Worker 0's finding, and the only catalog item touching `.py` files. Re-derived rather than accepted — "4 examples, 1 compliant" is a claim, and it reproduces. The package's multi-line `strawberry.Schema(...)` **construction examples** in docstrings number exactly four, and one carries the registration:

| Site | `config=strawberry_config()` |
|---|---|
| `django_strawberry_framework/extensions/debug.py` (module docstring) | **yes** |
| `django_strawberry_framework/extensions/resource_policy.py::DjangoResourcePolicyExtension` (class docstring) | no |
| `django_strawberry_framework/optimizer/extension.py` (module docstring) | no |
| `django_strawberry_framework/optimizer/extension.py` (method docstring, the singleton-in-a-factory example) | no |

Population boundary, since the greppable token over-collects: a package-wide grep for `(strawberry\.Schema|DjangoSchema)\(` returns 25 hits, of which 21 are inline prose mentions in the `` ``strawberry.Schema(...)`` `` form, a `class DjangoSchema(strawberry.Schema):` definition, or an error-message string. Only the four above open a multi-line constructor block. Adjacent but not in the population: `django_strawberry_framework/scalars.py`'s `strawberry_config` docstring, which names the pattern inline (`pass it as ``strawberry.Schema(query=..., config=...``) without building an example.

**The precedent-setting file is the one that goes away.** `TODO-ALPHA-050-0.0.15` Slice 2 (`KANBAN.md` L172) opens "delete `extensions/debug.py` + `tests/extensions/test_debug.py`" — verified — so the only compliant example will not exist after that card ships, leaving the population at **three** non-compliant sites and no in-package precedent.

**Homed, not fixed, and deliberately so:** whether a topic-scoped illustration (an optimizer example, a resource-policy example) should carry an unrelated `config=` line is a doc-style decision for the maintainer, not a defect a spec cycle may settle. It is also outside this cycle's fence, which owes no `.py` edit.

**One correction to the homing rationale.** Card 051's convention is verified verbatim and repeatedly — "Fold into whichever WP batch legitimately opens `<file>`" appears at `KANBAN.md` L248, L250, L252, L255, L258 and L260 — but its batches do **not** currently name two of the three target files: card 051's section mentions `extensions/resource_policy.py` **once** and `optimizer/extension.py` **zero** times. So the "batches already open the file" half of the rationale is not established by the board text for the optimizer sites; 051 remains the right home on its convention and its boundary-hardening scope, and the batch coverage is something that card's own planning must establish. Worker 0's "already carries three same-class docstring-precision items" also does not reproduce: by the narrow reading — a docstring whose prose misdescribes the code it documents — card 051 carries at least **five** (L233 `_package_view_instance`, L235 `send_revalidated_operation_frame`, L237 `MAX_REQUEST_BODY_BYTES`, L246 `ConfigurationError`, L247 `_format_unknown_fields_error`), plus a sixth docstring surface at L253 that is stale spec *paths* rather than imprecision. The class is real and well-populated; the count of three is not.

**Two corrections to the homing message's own populations, recorded because a wrong population is what gets inherited**

- **The fakeshop schema-building module count is nine, not six.** Seven `test_query/` modules (`test_debug_extension_api`, `test_error_policy_api`, `test_multi_db`, `test_optimizer_auto_api`, `test_products_visibility_api`, `test_resource_policy_api`, `test_transport_api`) plus two under `apps/library/tests/` (`test_generic_connection`, `test_generic_connection_sharded`), plus `strategy_schemas.py`.
- **Two of them build schemas with no `config=strawberry_config` at all, and that is not a gap.** `test_query/test_products_visibility_api.py` (seven builds, zero) and `test_query/test_transport_api.py` (two builds, one). Neither resolves `BigInt` — the first over `apps.products` types with no `Big` anywhere in `apps/products/models.py`, the second over a pure-Strawberry query with no Django model — so Decision 5's rule does not reach them: the registration is owed by a `BigInt`-resolving schema, not by every schema. A future sweep for "sites missing the registration" must not re-raise these two.
- **Instrument trap behind both figures.** `config=strawberry_config()` **with the empty parens** under-reports: it misses `test_query/test_optimizer_auto_api.py`'s `config=strawberry_config(extra_scalar_map={BombValue: bomb_scalar})`. Count on `config=strawberry_config`. The mirror trap produced the six-module figure — `grep -c strawberry_config` counts the import line as a build. Two instruments, two wrong populations, same root: the token is not the population.

**Not worker-verifiable — escalated to the maintainer**

- **The rationale's moved-text `python3.10` population, stated as 6 by Slice 2.** The rationale is untracked at `HEAD`, so no read-only reference exists for its intermediate state and the figure can be neither confirmed nor refuted without the tree at an intermediate point. Derivable bounds put it at 4 or 5. The claim is recorded with its evidence and escalated; nothing depends on it — the spec-side figure of 14 is confirmed, and both files now report `python3.10` at 0 live occurrences.

**Artifact-local, closes with the cycle (recorded, no action)**

- Slice 2's artifact §3's per-anchor breakdown of the 9 unresolved anchors sums to 10 (`#upload-scalar` is x1, not x2); its total of 9 is right, and the durable record carries no counts. Same artifact's "2 descriptive `python3.10` mentions remain" is 4, both extras being sentences the pass wrote after measuring.

## Artifact list

- `docs/builder/bld-slice-1-025-rationale_authoring.md`
- `docs/builder/bld-slice-2-025-spec_reconciliation.md`
- `docs/builder/bld-final-025.md` (deleted at close)
- `docs/builder/bld-slice-3-025-decision_9_census.md`

The three `bld-slice-*-025-*.md` artifacts were **deleted at close** (maintainer instruction, 2026-08-19) and are listed above as the record of what the cycle produced. `docs/builder/bld-final-025.md` was deleted at close too, so this plan is the sole surviving artifact: its `## Final gate record` and `## Deferred-work homing` above carry every finding those four artifacts held.

## Checklist

- [x] Slice 1: Rationale authoring (`docs/SPECS/appx/spec-025-scalar_map_helper-0_0_7-rationale.md`) -> `docs/builder/bld-slice-1-025-rationale_authoring.md`
- [x] Slice 2: Spec reconciliation (D1-D13) -> `docs/builder/bld-slice-2-025-spec_reconciliation.md`
- [x] Final test-run gate -> `docs/builder/bld-final-025.md`, deleted at close; folded into `## Final gate record` + `## Deferred-work homing` above
- [x] Slice 3: Decision 9 census repair (D14) -> `docs/builder/bld-slice-3-025-decision_9_census.md`

No cross-slice integration pass artifact: with one writing role and Markdown-only slices there is no cross-slice DRY surface to scan. That judgement held for DRY and for rationale/spec coherence, which Slice 2's own pass and then the final gate did resolve - the final gate found and fixed three coherence defects Slice 2 had left. What neither covered is a different axis: whether the set of divergences handed to Slice 2 was complete. D14 was found only by re-deriving the catalog after the gate, so treat the divergence *inventory* as the surface an integration pass owes a reconciliation cycle - not the consistency of the text that discharges it.
