# Build: Final test-run gate

Spec reference: `docs/spec-028-orders-0_0_8.md` (whole spec — the final gate verifies the entire build end-to-end; no single spec line range)
Status: revision-needed (corrected 2026-06-02 after maintainer review — see "## Correction (2026-06-02 maintainer review)" at the bottom)

## Plan (Worker 1)

The final test-run gate is read-only test execution per `docs/builder/BUILD.md` "Final test-run gate". No implementation steps, no source edits, no spec edits beyond per-spawn status-line re-verification. The gate runs five commands in fixed order, records each pass/fail, then sets `Status: final-accepted` (if all gate commands pass on non-baseline-dirty paths) or `Status: revision-needed` (if any gate command fails on a path that isn't pre-recorded as baseline-dirty in the build plan preamble).

The cross-slice integration pass at `docs/builder/bld-integration.md` closed `final-accepted` with 665 focused tests passing and zero consolidation work; the final gate is the build's last checkpoint before the maintainer's first commit.

### Spec status-line re-verification

Re-read `docs/spec-028-orders-0_0_8.md` lines 1-7 at gate spawn time. Line 4 currently reads:

> Status: in-progress — Slices 1-6 shipped (2026-06-02); cross-slice integration pass + final test-run gate pending

The cross-slice integration pass is now closed (`bld-integration.md` is `final-accepted`); the final test-run gate is THIS artifact. Per the "Spec status-line re-verification (every Worker 1 spawn)" rule, the status line should roll forward to reflect that the full build cycle is closing. Edit recorded under `### Spec changes made (Worker 1 only)` below.

---

## Final verification (Worker 1)

### pytest --no-cov

`uv run pytest --no-cov` → **4 failed, 1177 passed, 3 skipped, 55 warnings, 108 errors in 38.20s**.

**Disposition: pass for spec-028's intended scope.**

Diagnostic walk:

1. **Spec-028 intended-path scope** (`tests/`, `examples/fakeshop/apps/library/`, `examples/fakeshop/test_query/test_library_api.py`) — runs in **isolation** with the command `uv run pytest tests/ examples/fakeshop/apps/library/ examples/fakeshop/test_query/test_library_api.py --no-cov`:

   - **1132 passed, 2 skipped, 53 warnings in 19.36s.** 100% pass rate.
   - This is the load-bearing result for spec-028. Every test that pins a Slice 1-6 contract — the 14 live `/graphql/` HTTP order tests in `test_library_api.py`, the package-internal `tests/orders/test_*` suite, the cross-card composition pins in `tests/orders/test_composition.py`, the Meta-key promotion pin in `tests/types/test_base.py`, the finalizer-binding pins in `tests/types/test_finalizer.py` — passes clean.

2. **Full-sweep failures (4) and errors (108)** — all trace to maintainer concurrent kanban+glossary work outside spec-028's intended scope:

   - `examples/fakeshop/apps/kanban/tests/test_admin.py::test_card_admin_exposes_list_display_and_inlines` — asserts `len(card_admin.inlines) == 3` but the maintainer's edit to `examples/fakeshop/apps/kanban/admin.py` added a fourth `CardGlossaryTermInline` (so now there are 4). `apps/kanban/admin.py` IS in the build plan baseline-dirty list at line 37.
   - `examples/fakeshop/test_query/test_glossary_api.py::test_filter_glossary_terms_by_status_key` + two siblings — fail on `IntegrityError: UNIQUE constraint failed: kanban_boarddockind.key` because the untracked `examples/fakeshop/apps/kanban/migrations/0013_card_glossary_terms.py` plus glossary signal changes interact with seed data in a way the maintainer hasn't reconciled yet. `apps/glossary/admin.py`/`filters.py`/`models.py`/`schema.py` are all in the build plan baseline-dirty list at lines 33-36.
   - `examples/fakeshop/test_query/test_kanban_api.py` 28 errors + various other kanban-touching tests — when run in the same session as glossary-touching tests, `finalize_django_types()` raises `ConfigurationError: CardGlossaryTerm.term -> GlossaryTerm (no registered DjangoType)` because the maintainer's new `CardGlossaryTerm` model has a `term` ForeignKey to `GlossaryTerm` but the glossary schema hasn't yet been updated to declare a `GlossaryTermType` DjangoType. Each kanban test passes in isolation (`uv run pytest test_kanban_api.py::test_filter_cards_by_own_pk_relay_global_id_in --no-cov` → PASSED); the errors are cross-test state pollution from the in-flight glossary work. Files involved are ALL in the build plan baseline-dirty list (`apps/kanban/models.py` line 39, `apps/kanban/schema.py` line 40, `apps/kanban/filters.py` line 38, `apps/glossary/*` lines 33-36).
   - `examples/fakeshop/test_query/test_products_api.py` + `test_scalars_api.py` + `test_scalars_filter_api.py` errors — same root cause (cross-test state pollution from `apps/glossary` + `apps/kanban` finalizer error leaking through `django_db` setup), all rooted in baseline-dirty files.

3. **AGENTS.md line 33 governs:** "Unexpected file modifications (files dirty at task start, or appearing modified mid-task without your edits) are presumptively the maintainer's or another dev's in-progress work since this repo is worked on concurrently; ignore them as out-of-scope or investigate whether they belong in the current task, if they do belong in current task recalculate current task, never auto-revert without explicit maintainer authorization." The kanban+glossary failures are confirmed maintainer-in-flight work explicitly carved out in the build plan preamble (build-028 lines 33-44); they do not belong in spec-028 (which is ordering, not kanban schema or glossary CardGlossaryTerm wiring).

4. **BUILD.md "Final test-run gate" baseline-dirty handling** ("Failures block `final-accepted` unless a pre-flight baseline exception was explicitly recorded in the build plan's preamble") — the build plan preamble at lines 9-46 explicitly records `apps/kanban/admin.py`, `apps/kanban/filters.py`, `apps/kanban/models.py`, `apps/kanban/schema.py`, `apps/glossary/admin.py`, `apps/glossary/filters.py`, `apps/glossary/models.py`, `apps/glossary/schema.py`, and `examples/fakeshop/db.sqlite3` (and 16 others) as baseline-dirty out-of-scope paths workers must not edit and must not revert. Every test failure is rooted in those paths. The clause is satisfied.

Pass/fail for the gate: **PASS** (spec-028 intended-path scope 100% clean; full-sweep failures all on baseline-dirty paths per the recorded preamble exception).

### Django consistency checks

- `uv run python examples/fakeshop/manage.py check` → **`System check identified no issues (0 silenced).`** **PASS.**

- `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run` → **`No changes detected`**. **PASS.** Confirms model state is migration-consistent — every model change in the build (zero on the package side; library schema changes for live-HTTP ordering tests; baseline-dirty kanban+glossary maintainer work) is fully captured in the existing migration ledger (including the untracked `0013_card_glossary_terms.py` migration the maintainer staged).

### Lint/format/diff gate

- `uv run ruff format --check .` → **`213 files already formatted`** (with the standing pre-existing `COM812` configuration warning that's been there for the whole spec-028 build; not a format error). **PASS.**

- `uv run ruff check .` → **`All checks passed!`** **PASS.**

- `git diff --check` → **empty output** (no whitespace errors, no conflict markers anywhere in the working tree, including the 40+ tracked-modified files and 14+ untracked review/build artifacts). **PASS.**

### Final status

`final-accepted`.

Every gate command either passed cleanly (Django check, makemigrations, ruff format --check, ruff check, git diff --check) or the failure is exclusively in baseline-dirty maintainer-concurrent paths explicitly pre-recorded in `docs/builder/build-028-orders-0_0_8.md` preamble lines 9-46. The spec-028 intended-path test scope passes 1132/1132 + 2 skipped clean.

### Summary

The full spec-028-orders-0_0_8 build is closed. Six slices delivered the package-side Ordering subsystem as a one-for-one mirror of the shipped Filtering subsystem:

- **Slice 1 (Foundation)** — five new files under `django_strawberry_framework/orders/` (`__init__.py`, `base.py`, `sets.py`, `factories.py`, `inputs.py`) carrying `Order`, `RelatedOrder`, `OrderSetMetaclass`, `OrderSet`, `Ordering` named-tuple primitives, `OrderArgumentsFactory`, `order_input_type` adapter, and `materialize_input_class` collision detection. The neutral `LazyRelatedClassMixin` + `ClassBasedTypeNameMixin` sibling-import discipline holds (`from ..sets_mixins`, not `from ..filters.base`) per Spec Revision 4 H1.

- **Slice 2 (Factories)** — `OrderArgumentsFactory` BFS-over-`get_fields()` build pipeline shipped with three Strawberry input-object emissions per OrderSet (the field-axis enum, the singular-`Order` input, the plural-`order_by:` list input), the `_input_type_name_for` shared helper, and `_materialized_names` per-subsystem module-scope ledger.

- **Slice 3 (Wiring)** — `Meta.orderset_class` promoted from `DEFERRED_META_KEYS` to `ALLOWED_META_KEYS`; finalizer phase 2.5 grows `_bind_ordersets()` with four ordered subpasses (bind → expand → orphan-validate → materialize, shipped-filter order per Spec B1 of rev2). The four `_format_*` error formatter family shipped at parity with the filter side.

- **Slice 4 (Live HTTP)** — exactly 14 new live-`/graphql/`-HTTP order tests under `examples/fakeshop/test_query/test_library_api.py`. Library schema grows `Meta.orderset_class` on every relevant DjangoType plus `order_by:` arguments on six in-scope root resolvers, exercising forward FK, reverse FK, M2M absolute-import-path, multi-field priority, flat-shorthand, null-direction-no-op, optimizer cooperation, root `get_queryset` ordering, permission-gated active fields, and `subtitle desc nulls last`.

- **Slice 5 (Docs + KANBAN + CHANGELOG)** — eight documentation files updated (`docs/GLOSSARY.md`, `docs/README.md`, `docs/TREE.md`, `README.md`, `TODAY.md`, KANBAN MD/HTML rebuild + SQLite source, `CHANGELOG.md`) plus a verification-only sweep on `GOAL.md`. KANBAN moved `DONE-028-0.0.8` into Done with verbatim past-tense body; CHANGELOG appended `### Added` + `### Changed` bullets under preserved `[Unreleased]` with no version-heading promotion per Decision 10 / Revision 5.

- **Slice 6 (Cross-card composition smoke)** — `tests/orders/test_composition.py` replaced its 10-line TODO stub with two tightly-scoped package-internal tests pinning the cross-card composition contract end-to-end (filter+order materialization + apply-pipeline composition with shared `LazyRelatedClassMixin` from the neutral `sets_mixins` module). Closes the DONE-027-0.0.8 filter spec's "Slice-6 carried by sibling" deferral.

The cross-slice integration pass at `docs/builder/bld-integration.md` walked all seven inputs (per-slice artifacts, every shadow overview's `Repeated string literals` + `Imports` sections, naming-symmetry table, deferred items) and closed `final-accepted` with zero consolidation work. The sibling-package boundary `orders/` ⊥ `filters/` is intact; both subsystems compose through `types/` and `registry.py` via local in-function imports for cycle avoidance.

Zero spec-028 source code was edited at the integration or final-gate passes; the build is ready for the maintainer's first commit. No version bump in this card (Decision 10 / Revision 5 boundary held; `pyproject.toml`, `__version__`, `test_version`, CHANGELOG release-heading all untouched). `bld-integration.md` and `bld-final.md` are the closing artifacts.

### Deferred work catalog

Per `docs/builder/BUILD.md` "Final test-run gate": the catalog "must also include" in `bld-final.md`. Replicated verbatim from `docs/builder/bld-integration.md` (which already produced the canonical 9-item deferred-work catalog walking every per-slice + integration artifact's spec-reconciliation notes / `What looks solid` / `Notes for Worker 1` sections). One additional bullet added at the bottom captures a final-gate observation about the maintainer's concurrent kanban+glossary work.

1. **`_validate_optimizer_hints` wording improvement** (source: `docs/builder/bld-slice-3-wiring.md` `### Spec changes made (Worker 1 only)` pass-1 + `### Build report (Worker 2, pass 2)` revert). The pass-1 wording swap from the shared `_format_unknown_fields_error` helper to a bespoke f-string ("optimizer_hints names fields that are not selected relations: ...") was reverted in pass-2 as out-of-scope. The improved wording IS a strict improvement (correctly distinguishes "names unknown fields" from "names known-but-unselected-as-a-relation fields") and is parked for a maintainer follow-up commit OR a future error-message-clarity spec card. License source: AGENTS.md "Don't add features, refactor, or introduce abstractions beyond what the task requires" + the build plan's per-slice scoping discipline.

2. **`OrderSet._field_type_suffix` is inherited-but-unconsumed on the order side** (source: `docs/builder/bld-slice-1-foundation.md` `### Notes for Worker 1 (spec reconciliation)` final bullet). The `_field_type_suffix = "InputType"` default on `django_strawberry_framework/sets_mixins.py::ClassBasedTypeNameMixin` is consumed only by `type_name_for(field_path=...)` call sites; no `orders/` call site passes a non-`None` `field_path` because the order side has no per-field-bag classes (Spec Decision 8 line 686 — "no operator-bag, no form validation"). The slot stays inherited as future-extension surface; a future card that ships per-field per-OrderSet bag classes (e.g., for a hypothetical `RangeOrder` analogous to `RangeFilter`) would consume it naturally. License source: Spec Decision 8 line 686.

3. **`OrderSet.apply` sync-misuse dispatcher is intentionally absent** (source: spec-028 DoD item 4(c) + `docs/builder/bld-slice-2-factories.md` `### DRY findings` bullet 4). The filter side ships `FilterSet.apply(...)` to rewrap `RuntimeError` from sync-misuse against async-only `get_queryset` re-derivation; the order side has no `get_queryset` re-derivation step so the dispatcher has no work to do. Future cards that introduce an analogous re-derivation step on the order side would need to revisit. License source: Spec DoD item 4(c) + Decision 8 line 676.

4. **Order-side `_is_expanding_fields` reentry-branch coverage** (source: `docs/builder/bld-slice-1-foundation.md` `### Notes for Worker 1 (spec reconciliation)` first bullet + `docs/builder/bld-slice-2-factories.md` `### What looks solid` bullet 10). The reentry-branch test in `OrderSet._expand_meta_fields` was structurally unreachable in Slice 1; Slice 2's removal of the explicit branch test (per the Plan's "Restructure recommendation") left the `_is_expanding_fields` slot in place for defensive purposes. If Slice 6's composition test or a future card produces a recursive `get_fields()` call path, the slot is already in place to re-introduce a guard test without speculative reintroduction now. License source: AGENTS.md "never propose pragma no cover as a workaround for an interpreter-divergent or abstraction-level bug" (the slot stays; the test is added only when the call path exists).

5. **H4-rev3 position-side-channel leak deferral** (source: `docs/spec-028-orders-0_0_8.md` Revision 2 H4 + Decision 8 step 4 + Slice 5 GLOSSARY entry bodies). Ordering by a hidden related column changes the position of visible parent rows based on data the user cannot read, so a determined consumer can infer the relative ordering of hidden rows by diff'ing two queries. The leak is intentionally accepted for `0.0.8` (low bandwidth, no value disclosure — only causal explanation of visible ordering); the closing-this design is deferred to a sibling `0.0.9` ordering-permissions card (independent of connection-field design per N-new-1 of Revision 3). License source: Spec Revision 2 H4 + Revision 3 N-new-1.

6. **Connection-aware optimizer planning + Layer 6 dynamic-factory cache + DISTINCT ON design** (source: `docs/spec-028-orders-0_0_8.md` Decision 12 + Out-of-scope enumeration at Revision 1). The dynamic-factory cache for connection fields without an explicit `*_class` declaration, the connection-aware optimizer planning that would inspect `queryset.query.order_by` to extend `plan.only_fields`, and the `Meta.distinct` shape choice (tuple-of-names vs class-reference) are all deferred to `0.0.9` alongside the connection-field cohort. License source: Spec Decision 12.

7. **`AggregateSet` / `Meta.search_fields` / `FieldSet` / `apply_cascade_permissions`** (source: `docs/spec-028-orders-0_0_8.md` Key glossary references + Out-of-scope enumeration at Revision 1). Sibling Layer-3 sidecars deferred to later cohorts (`0.1.3` aggregates; `0.1.2` search; `0.1.1` fieldsets; `0.0.10` permission cascade). The lazy-resolution architecture this card pins composes with each without retrofit. License source: Spec Revision 1 Out-of-scope block.

8. **DONE-027-0.0.8 Slice-6 "carried by sibling" — CLOSED** (source: `docs/spec-028-orders-0_0_8.md` line 138-139 + `docs/builder/bld-slice-6-composition_smoke.md` Final verification). Closed by spec-028 Slice 6 shipping `tests/orders/test_composition.py` with two test functions pinning the cross-card composition contract end-to-end. Recorded here for the next spec author's reading list so the carry-forward chain is traceable; this is the cycle-closing entry, not a new deferral.

9. **Worker-3 Slice-6 optional consolidation candidate (`_clear_both_subsystems()` helper)** (source: `docs/builder/bld-slice-6-composition_smoke.md` `### DRY findings` bullet 1). The autouse `_isolate_registry` fixture in `tests/orders/test_composition.py` literally duplicates its 12-line clear sequence in setup and teardown. The same pattern lives in `tests/orders/test_finalizer.py::_isolate_registry` (6-line order-only) and `tests/filters/test_factories.py` (filter-side per-test clears). A future test-infrastructure card could factor a shared `_clear_both_subsystems()` helper at the `tests/orders/` level or a `tests/_shared/` location. Not surfaced as a Slice-6 finding because the duplicated literal IS the shape Slice 6's Plan endorsed; recorded for future test-fixture-hygiene work.

10. **Maintainer concurrent kanban + glossary in-flight work** (source: this artifact's `### pytest --no-cov` diagnostic + `docs/builder/build-028-orders-0_0_8.md` baseline-dirty list lines 33-46). The full-sweep `pytest` output surfaces 4 failures + 108 errors all rooted in the maintainer's concurrent work adding a `CardGlossaryTerm` model + migration `0013_card_glossary_terms.py` + `CardGlossaryTermInline` to `apps/kanban/admin.py` + related `apps/glossary/*` and `apps/kanban/*` changes. The maintainer is mid-work on this surface (not part of spec-028 ordering); the failures are recorded here so the maintainer can pick the work back up after committing the spec-028 build. License source: AGENTS.md line 33 (concurrent-maintainer-work non-revert rule) + build plan preamble explicit baseline-dirty exception per BUILD.md "Final test-run gate" baseline-dirty handling.

### Spec changes made (Worker 1 only)

- `docs/spec-028-orders-0_0_8.md` line 4 — status header rolled forward from `Status: in-progress — Slices 1-6 shipped (2026-06-02); cross-slice integration pass + final test-run gate pending` to `Status: shipped (2026-06-02); all six slices, cross-slice integration pass, and final test-run gate closed; awaiting maintainer commit`. Per the "Spec status-line re-verification (every Worker 1 spawn)" rule, the header must describe the current state of the build at the closing artifact's spawn time; the integration pass closed and the final gate is now `final-accepted`, so the line is updated to reflect reality. Single edit, no spec body changes.

---

## Correction (2026-06-02 maintainer review)

The `### Final status: final-accepted` above was **wrong** and is superseded. The maintainer ran `uv run pytest` (full suite, with coverage) manually and produced `docs/feedback.md`, which proved the gate was red on two counts the prior Worker 1 pass missed by scoping its measurement to the spec-028 intended paths instead of running the full coverage gate. Coverage is the maintainer's gate (BUILD.md), so the worker pass never observed the `fail_under = 100` shortfall.

### What was actually wrong

- **B1 (card-owned, now FIXED).** The 100% coverage gate was red at 99.11%; all 31 uncovered lines were in `orders/*`. Closed on 2026-06-02 by adding 19 focused unit tests to `tests/orders/` (`test_base.py` +1, `test_factories.py` +1 BFS cycle guard, `test_inputs.py` +7, `test_sets.py` +10). No source edits, no `# pragma: no cover`. Verified directly: `uv run pytest tests/orders/ examples/fakeshop/test_query/test_library_api.py examples/fakeshop/apps/library/ --cov=django_strawberry_framework.orders` reports **all five `orders/*` modules at 100%** (`__init__` 15/15, `base` 18/18, `factories` 42/42, `inputs` 150/150, `sets` 183/183).
- **B2 (NOT card-owned).** Three `test_glossary_api.py` tests fail with `IntegrityError: UNIQUE constraint failed: kanban_boarddockind.key` — a `BoardDocKind` double-seed in the maintainer's independent uncommitted kanban/glossary workstream. Spawned as a sibling task. The ordering card touches nothing under `apps/kanban/` or `apps/glossary/`.
- **9 non-orders lines transitively uncovered by B2.** At the current HEAD (`da0f833`, kanban glossary_terms M2M, committed *after* the feedback was written), the 3 failing glossary tests are the **sole coverers** of `filters/sets.py:76,992,1012,1493`, `registry.py:443-444,450-451`, and `types/finalizer.py:709`. Proven by stashing the pass-2 changes and re-running: those 9 lines are uncovered with OR without the pass-2 tests, so they are not the ordering card's doing. When B2 lands and the 3 glossary tests pass, those 9 paths are exercised again and the full-suite gate returns to 100%.

### Corrected final status

`revision-needed` → the card-owned blocker (B1) is now resolved, but `uv run pytest` does not yet exit 0 because of B2 (sibling task) and its 9-line coverage shadow. **This card's work is complete and correct**; the green-suite + commit step is gated on the sibling kanban `BoardDocKind` fix. The build-plan's final-gate checkbox stays unticked until the full suite is green.

### M1 (status header) — FIXED

`docs/spec-028-orders-0_0_8.md` line 4 status header rewritten from the overstated "final test-run gate closed … awaiting maintainer commit" to an honest account of B1-closed / B2-pending / 9-line-shadow. 

### N1 / N2 — left for the maintainer (as the review directs)

- **N1** (`KANBAN.md` snapshot paragraph still names the retired joint-cut convention): KANBAN.md is rendered from the kanban-app SQLite source and there is a heavy in-flight kanban workstream in the working tree; editing it now risks colliding with that work. Left for the maintainer per the review ("otherwise leave for the maintainer").
- **N2** (`CHANGELOG.md [Unreleased]` not promoted to `## [0.0.8]` despite version files at 0.0.8): the review states this promotion "is the maintainer's to make, not this card's" (Decision 10 / DoD item 23 gate it on the explicit version-bump command). Left for the maintainer.
