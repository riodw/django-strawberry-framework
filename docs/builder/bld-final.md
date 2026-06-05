# Build: Final test-run gate — spec-029 consumer_dx_cleanup (0.0.9)

Spec reference: `docs/spec-029-consumer_dx_cleanup-0_0_9.md`
Status: final-accepted

> Run note: performed **inline by Worker 0** at the maintainer's direction ("no more dispatching"), after the build commit (`2d1f296`). The pytest sweep ran against committed source + the working-tree follow-up changes (regenerated `KANBAN.md` / `KANBAN.html`, the reconciled `examples/fakeshop/db.sqlite3`, and the workflow-doc edits). Django tests use a fresh test database, so the `db.sqlite3` data edits do not affect test results.

## Post-feedback follow-up — 2026-06-05 (review of `2d1f296` in `docs/feedback.md`)

The maintainer's review flagged the pre-existing kanban-app baseline failures and noted the **100% coverage gate (DoD item 17) could not be confirmed green until those fixtures were reconciled**. Both are now resolved, along with the review's P3 polish notes. **New full-gate result (re-run after the fixes): `1391 passed, 3 skipped, 0 failed`, `Required test coverage of 100.0% reached`; `manage.py check`, `makemigrations --check`, `ruff format --check`, `ruff check`, `git diff --check` all clean.** The historical gate table below is retained as the `2d1f296`-snapshot reading (32 kanban failures / coverage unconfirmable).

- **Kanban baseline (32 failures) — FIXED, fixtures only.** The `done`-card glossary-link invariant in `apps/kanban/signals.py` is correct behavior and was kept untouched; the *test fixtures* seeded the link in the wrong order. `_seed_board` (`test_query/test_kanban_api.py`, 30 failures) and `test_dependency_reference_does_not_store_or_derive_blocked_badge` (`apps/kanban/tests/test_signals.py`) now attach the glossary link **before** the `done`-status flip; `test_done_card_last_glossary_link_cannot_be_deleted_or_moved` wraps its chained delete/move-protection assertions in `transaction.atomic()` savepoints (the first protected op's `ValidationError` was marking the test transaction broken before the second could run). No package source changed.
- **Coverage gap (unmasked by the kanban fix) — CLOSED.** With the suite no longer aborting at kanban setup, the gate ran to completion and exposed 4 uncovered lines in `inspect_django_type.py` — the `--schema` import-failure branch (92-93), the bare-name registry-miss branch (126), and the multi-member-union render path (267) — all committed at `2d1f296` but masked by the red suite. Three targeted tests now cover them; the command module is back to 100%.
- **P3 polish (review §"Low-severity polish") — APPLIED.** `_scalar_row` now names the matched `SCALAR_MAP` MRO ancestor instead of the concrete field class (P3 #1), which also retires the dead-defensive `scalar_for_field` guard (P3 #2); relation rows print the friendly `M2M` / `forward FK` / `reverse FK` / `reverse O2O` labels mirroring the spec's illustrative output (P3 #3).
- **Not done (deliberately):** the joint `0.0.9` version cut (Decision 11 — owned by the joint release, not this card) and Slice 3's *optional* README/TODAY capability mention (spec marked optional; review called it a non-issue).

## Gate commands

| Command | Result |
| --- | --- |
| `uv run pytest --no-cov` (full sweep, all 3 test trees) | **32 failed, 1355 passed, 3 skipped** — every failure is in the kanban app (recorded baseline exception below); all spec-029 tests pass |
| `uv run python examples/fakeshop/manage.py check` | **PASS** — "System check identified no issues (0 silenced)." |
| `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run` | **PASS** — "No changes detected" |
| `uv run ruff format --check .` | **PASS** — "231 files already formatted" (the `COM812`-vs-formatter line is a pre-existing benign config warning, not a failure) |
| `uv run ruff check .` | **PASS** — "All checks passed!" |
| `git diff --check` | **PASS** — no whitespace errors / conflict markers |

## Kanban baseline exception (recorded in the build plan preamble)

The 32 failures are **all** in the kanban example app — 30 in `examples/fakeshop/test_query/test_kanban_api.py` and 2 in `examples/fakeshop/apps/kanban/tests/test_signals.py` (`test_done_card_last_glossary_link_cannot_be_deleted_or_moved`, `test_dependency_reference_does_not_store_or_derive_blocked_badge`) — rooted in the `apps/kanban/signals.py` done-card glossary-link / dependency-reference signal subsystem.

**Confirmed pre-existing, NOT a spec-029 regression:**
- The build commit `2d1f296` touched **no** `apps/kanban/` file (verified: `git show 2d1f296 --name-only | grep apps/kanban` → empty). The kanban failures cannot be caused by a diff that does not touch the kanban app.
- Worker 2 independently stash-verified the `test_kanban_api.py` subset at HEAD during the Slice-3 build (recorded in `bld-slice-3-nullability_overrides.md`).
- The follow-up working-tree changes (regenerated KANBAN docs, `db.sqlite3` data, workflow docs) touch no kanban code and do not reach the test DB.

Per the build-plan "Maintainer decision — 2026-06-05" item 2, these do **not** block `final-accepted`. They remain an open **maintainer follow-up** outside spec-029 (see catalog).

**spec-029's own tests all pass** within the 1355 — the Slice-1 no-`DeprecationWarning` test, the Slice-2 `inspect_django_type` happy-path + failure-mode suites (`tests/management/` + `examples/fakeshop/tests/test_inspect_django_type.py` incl. the cross-slice `test_inspect_reads_resolved_annotation_not_field_null`), and the Slice-3 converter tri-state + validation + live-HTTP nullability-flip suites (`tests/types/` + `examples/fakeshop/test_query/test_library_api.py`).

## Deferred work catalog

Walked every per-slice + integration artifact's spec-reconciliation / `What looks solid` / `Notes for Worker 1` sections. Build-internal deferrals were all resolved within the build; the outstanding items are:

- **Resolved in-build (no longer outstanding):**
  - Cross-slice test `test_inspect_reads_resolved_annotation_not_field_null` — deferred Slice 2 → Slice 3 (the type it asserts over did not exist at Slice 2); landed in the Slice-3 cycle.
  - Slice-2 Low (the `subtitle` `"String"` substring assertion that could false-green against `"String!"`) — tightened in the Slice-3 cycle via the `_field_row` helper.
  - `check_spec_glossary` spec-body links for the 3 net-new anchors — added by Worker 1 at Slice-2/Slice-3 final verification (`OK: 44 terms`).
- **Deferred to the joint `0.0.9` cut (Decision 11):** the version bump (`pyproject.toml` / `__version__` / `tests/base/test_init.py::test_version` / `uv.lock`) and the CHANGELOG release-heading promotion (`[Unreleased]` → `## [0.0.9]`). No spec-029 slice touches these.
- **Deferred to future specs/cards (spec Out of scope):** relation-field nullability override (Decision 10 — scalar-only for 0.0.9; forward single-valued FK is the natural next extension); the `DjangoConnectionField` / full-Relay / connection-aware-optimizer cohort (`WIP-ALPHA-030/031/032-0.0.9`); `FieldSet` (`0.1.1`), `Meta.search_fields` (`0.1.2`), `AggregateSet` (`0.1.3`), `apply_cascade_permissions` (`0.0.10`); a `--json` / `--watch` mode on `inspect_django_type`; relocating the optimizer plan cache off the instance.
- **Maintainer follow-up (outside spec-029):**
  - ~~The ~32 kanban-app test failures (pre-existing `apps/kanban/signals.py` baseline) — needs a separate fix; not in scope here.~~ **RESOLVED 2026-06-05** (kanban test fixtures reordered to seed the glossary link before the `done`-flip; the signal subsystem was left untouched) — see the post-feedback follow-up at the top.
  - Card 029's Slice-2 DoD line in the kanban DB still carries stale `type_dotted_path` / `examples/fakeshop/tests/test_commands.py` wording. The spec wrap's named cleanup scope was only the `spec-021` filename + `## [0.0.8]` CHANGELOG refs, so it was left as-is; a one-field `CardItem.text` tweak if desired.
  - Process gap (now mitigated): the build's doc-update steps hand-edited the **generated** `KANBAN.md` / `docs/GLOSSARY.md`. This follow-up reconciled the source-of-truth DB so both regenerate cleanly, and `docs/builder/worker-0.md` now documents the DB-backed card-closeout procedure. Future specs' "edit KANBAN.md / GLOSSARY.md" steps should be DB edits + regenerate.

## Summary

The final gate is green on every command except the pre-existing, build-independent kanban-app baseline failures, which the build plan explicitly records as a non-blocking exception. spec-029 (Slices 1–4) ships its full contract: the `extensions=` singleton-factory migration, the `inspect_django_type` command, the `Meta.nullable_overrides` / `Meta.required_overrides` override, and the card-completion wrap (card 29 → `DONE-029-0.0.9`). `final-accepted`.
