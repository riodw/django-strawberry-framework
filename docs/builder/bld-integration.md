# Build: Cross-slice integration pass

Spec reference: `docs/spec-020-scalar_map_helper-0_0_7.md`
Build plan: `docs/builder/build-020-scalar_map_helper-0_0_7.md`
Status: final-accepted

## Pre-write checks

### Helper coverage

Every Python file with review-worthy logic touched by the build had `scripts/review_inspect.py` run, or the skip was recorded with an explicit reason:

- `django_strawberry_framework/scalars.py` (Slice 1, +~50 source lines of new logic) — helper RUN by Worker 3 during slice-1 review. Overview at `docs/shadow/django_strawberry_framework__scalars.overview.md`. 3 symbols, 0 control-flow hotspots, 0 Django/ORM markers, 0 TODOs, 0 repeated string literals.
- `tests/test_scalars.py` (Slice 2, +178 lines of test logic) — helper RUN by Worker 3 during slice-2 review (50+ lines outside `django_strawberry_framework/` threshold). Overview at `docs/shadow/tests__test_scalars.overview.md`. 48 symbols, 0 control-flow hotspots, 0 Django/ORM markers, 0 TODOs, 4 repeated string literals (all explicitly justified — see "Shadow overview review" below).
- `tests/types/test_converters.py` (Slice 2, 10-site mechanical migration, no new logic) — helper RUN by Worker 1 during slice-2 planning (1735 source lines, over the 150-line threshold). Overview at `docs/shadow/tests__types__test_converters.overview.md`. No new control-flow hotspots or Django/ORM markers introduced by the migration.
- `tests/base/test_init.py` (Slice 2, one-line tuple-append) — helper SKIPPED. Reason: 44 source lines (below the 150-line threshold) and the edit is a one-element append to the pinned `__all__` tuple (no logic added).
- `examples/fakeshop/config/schema.py` (Slice 3, two-line edit) — helper SKIPPED. Reason: 30 source lines (below the 50-line "added logic" / 150-line "existing file" thresholds for non-package files); not under `optimizer/` or `types/`.
- `django_strawberry_framework/__init__.py` (Slice 1, import widen + `__all__` append) — helper SKIPPED. Reason: pure re-export module — single import widening + single tuple-element append; no review-worthy logic added. BUILD.md "Worker 1 and Worker 3 may skip the helper for files where the artifact will be a 'no review-worthy logic' disposition (pure re-exports, single-line constants)" applies.
- Slices 4 (`docs/README.md`, `docs/GLOSSARY.md`, `GOAL.md`, `TODAY.md`, `docs/spec-020-scalar_map_helper-0_0_7-terms.csv`) and Slice 5 (`KANBAN.md`, `CHANGELOG.md`) — helper SKIPPED. Reason: Markdown / CSV only; `scripts/review_inspect.py` operates on Python source.

All required Python files have helper coverage or recorded skip reasons. No silent skips.

### Shadow overview review

Cross-shadow comparison per BUILD.md "Cross-slice integration pass" steps 3 and 4:

**Repeated string literals across `docs/shadow/`:**

- `docs/shadow/django_strawberry_framework__scalars.overview.md` — 0 repeated literals.
- `docs/shadow/tests__test_scalars.overview.md` — 4 repeated literals: `CustomScalar` x8 (locally-declared per-test `NewType` for the merge/no-mutate-caller/independent-instance/combined-with-kwargs tests, two declarations per test x 4 tests, authorized by Slice-2 plan DRY discretion item 3), `9223372036854775807` x4 (int64-max wire-format pin from spec-013 Decision 1; appears in two integration tests, twice each), `-9223372036854775808` x2 (pre-existing int64-min boundary pin, not introduced by this build), `AltBigInt` x2 (locally-declared `NewType` in the collision-raise and `scalar_map`-rejection tests).
- `docs/shadow/tests__types__test_converters.overview.md` — 25 repeated literals, ALL pre-existing in the file (`NON_NULL` x15, `test_arrayfield` x11, `_ARRAY_FIELD_CLS` x10, `django.contrib.postgres.fields` x8, `test_hstorefield` x7, etc.); none introduced by Slice 2's 10-site mechanical migration. The migration added only `config=strawberry_config()` substring per site, which is not a repeated literal per the helper's `--literal-min-length 8` default (the `()`/closing parens make the substring vary).

No literal appears in two or more shadow overviews. The locally-declared `CustomScalar` / `AltBigInt` `NewType` names in `tests/test_scalars.py` are file-scoped to the new factory tests; they do not recur in any other shadow output.

**Cross-shadow Imports comparison:**

- `django_strawberry_framework/scalars.py` imports (Slice 1 widening): `import re`, `from collections.abc import Mapping`, `from typing import Any, NewType`, `import strawberry`, `from strawberry.schema.config import StrawberryConfig`, `from strawberry.types.scalar import ScalarDefinition`. No first-party imports — `scalars.py` sits at the package's leaf level. Boundary clean.
- `tests/test_scalars.py` imports (Slice 2 widening): standard library + `strawberry` + `from django_strawberry_framework import BigInt, strawberry_config` + `from django_strawberry_framework.scalars import _parse_bigint, _serialize_bigint`. The private-symbol import (`_parse_bigint`, `_serialize_bigint`) is pre-existing per the file's strict-parser/serializer test surface; Slice 2 did not introduce a new private-symbol import (the new factory tests use only the public `BigInt`, `strawberry_config`, `StrawberryConfig`, `ScalarDefinition` surface). Boundary clean.
- `tests/types/test_converters.py` imports (Slice 2 one-symbol widening): `from django_strawberry_framework import BigInt, DjangoType, finalize_django_types, strawberry_config`. Sibling test file pulling from the package's public re-exports; matches the documented boundary.

No sibling module started importing from outside the documented boundary. No structural drift.

### Per-artifact walk results

Walked each `bld-slice-*.md` artifact's `### What looks solid` and `### DRY findings` sections to surface deferred follow-up:

- **bld-slice-1**: `### What looks solid` — no deferrals flagged for the integration pass; the optional forward link from `strawberry_config`'s docstring to `docs/GLOSSARY.md#strawberry_config` (Slice 4's anchor) was noted as a possible polish pass but not blocking. `### DRY findings` — none; helper output confirmed 0 repeated string literals at the slice level.
- **bld-slice-2**: `### What looks solid` — no deferrals. `### DRY findings` — `CustomScalar` x8 and `AltBigInt` x2 locally-declared per-test, authorized by Slice 2 plan DRY discretion item 3. No collapse opportunity.
- **bld-slice-3**: `### What looks solid` — no deferrals. `### DRY findings` — none; the `examples/fakeshop/test_query/test_multi_db.py` test-local schema construction (line 142) was noted as out-of-scope for Slice 3 per Decision 9, but it is not a Slice 3 finding to flag.
- **bld-slice-4**: `### What looks solid` — TWO deferrals flagged for `bld-final.md` Deferred work catalog: (1) `docs/TREE.md` lines 201/246 carry stale "Strawberry deprecation suppressed at definition site" wording obsoleted by Slice 1; spec DoD item 13 forbids editing `docs/TREE.md` in this card; (2) the `### In progress` summary paragraph in `KANBAN.md` line 50 carries a forward-looking "last `0.0.7` card to ship owns the version bump" sentence that is mildly stale post-Slice-5 (`DONE-047-0.0.7` is the last `0.0.7` card and deferred the bump per Decision 8). Worker 3 of Slice 5 dispositioned (2) as "no spec edit needed — forward-looking informational content". `### DRY findings` — none.
- **bld-slice-5**: `### What looks solid` — no new deferrals beyond what Slice 4 flagged. `### DRY findings` — none; the deliberate `KANBAN.md` Done body vs `CHANGELOG.md` `### Changed` Breaking-change bullet repetition is mandated by spec DoD items 15 and 16.

## Findings

### Cross-slice DRY (helpers, naming, error-handling, patterns, literals)

**Helpers introduced:** Slice 1 added one new public function (`strawberry_config`), one new module-level dict (`_PACKAGE_SCALAR_MAP`), and one new module-level `ScalarDefinition` (`_BIGINT_SCALAR_DEFINITION`). All three are colocated in `django_strawberry_framework/scalars.py`. No subsequent slice copied or paralleled any of these helpers — Slices 2/3/4/5 reference `strawberry_config` by name through the package re-export. Single source of truth; no consolidation needed.

**Naming consistency:** The factory's symbol name (`strawberry_config`), the `extra_scalar_map=` parameter name, the `_PACKAGE_SCALAR_MAP` private constant name, and the `_BIGINT_SCALAR_DEFINITION` private constant name appear identically across (a) Slice 1 source (`django_strawberry_framework/scalars.py`), (b) Slice 1 public re-export (`django_strawberry_framework/__init__.py` import line and `__all__` tuple), (c) Slice 2 tests (15 new pytest items + the `tests/base/test_init.py` `__all__` pin + 10 converter-table migrations), (d) Slice 3 example (`examples/fakeshop/config/schema.py`), (e) Slice 4 docs (`docs/README.md` Quick start + Schema setup boundary x2, `docs/GLOSSARY.md` new entry + existing-entry update + Public exports bullet + Index row, `GOAL.md` astronomy showcase, `TODAY.md` fakeshop block, terms CSV), (f) Slice 5 KANBAN past-tense Done body and CHANGELOG entries. No naming drift between slices.

**Error-handling consistency:** Two distinct `ValueError` shapes ship in Slice 1:

1. `ValueError("strawberry_config() owns scalar_map; pass consumer scalars with extra_scalar_map=...")` — `scalar_map=` rejection branch (`scalars.py:115-118`).
2. `ValueError("strawberry_config(extra_scalar_map=...) cannot redeclare package-defined scalars: <names>. Define a Strawberry custom scalar of a different NewType / class to register under a separate key.")` — collision branch (`scalars.py:121-127`).

Both raise `ValueError` (not `ConfigurationError`) per spec Decision 4 — the collision is a consumer-input mistake at helper-call time, not a `DjangoType`-creation or finalization-time error. Spec line 22 explicitly notes the deliberate choice. Slice 2 tests assert on substring `"BigInt"` AND `"cannot redeclare"` (collision branch) and substring `"scalar_map"` AND `"extra_scalar_map"` (rejection branch). Slice 5's CHANGELOG `### Changed` bullet at `CHANGELOG.md` line 27 references this surface with "Strawberry schema construction will fail with `Unexpected type ...BigInt` without it" — that wording references upstream Strawberry's own schema-construction error, not the helper's `ValueError`. The two distinct error-message texts are intentional and consistent across the build. No wording drift between slices.

**Repeated patterns:** The `config=strawberry_config()` consumer-migration shape appears across:

- Slice 2: 10 `tests/types/test_converters.py` sites + 2 integration tests in `tests/test_scalars.py`.
- Slice 3: 1 site in `examples/fakeshop/config/schema.py`.
- Slice 4: 6 sites across `docs/README.md` (Quick start + Schema setup boundary "Recommended" + Schema setup boundary "Wrong order"), `docs/GLOSSARY.md` (`## strawberry_config` first code block + `## BigInt scalar` registration paragraph), `GOAL.md` astronomy showcase, `TODAY.md` fakeshop block.
- Slice 5: 1 `diff` block inside the `CHANGELOG.md` `[Unreleased] ### Changed` Breaking-change bullet showing the migration before/after.

This repetition is **the canonical consumer-migration contract** per spec Decision 2 (which explicitly rejected a `dst.Schema(...)` wrapper to consolidate it) and Decision 5 (which pins "hard break in alpha" — every consumer schema adds this one-liner). Every slice's final-verification recorded this disposition: the pattern IS the demonstration consumers must read, NOT a DRY violation. Explicit confirmation, per task instructions: this repetition is the canonical post-migration consumer contract, not duplication that warrants consolidation.

**Repeated literals across slices:** No literal appears in two or more shadow overviews (per the cross-shadow comparison above). The locally-declared `CustomScalar` (x8) and `AltBigInt` (x2) `NewType` names in `tests/test_scalars.py` are file-scoped to the new factory tests; they do not recur in any sibling test file. The `9223372036854775807` int64-max boundary literal is a wire-format pin from spec-013, pre-existing in `tests/test_scalars.py` and used by the two new integration tests in Slice 2 — not a new cross-slice DRY hazard.

### Public-surface integration

`git diff -- django_strawberry_framework/__init__.py` shows exactly two changes, both authorized by spec DoD items 3 and 18:

1. Import line widened from `from .scalars import BigInt` to `from .scalars import BigInt, strawberry_config` (`__init__.py` line 23).
2. `__all__` tuple appended with `"strawberry_config"` as the last element after `"finalize_django_types"` (`__init__.py` line 37).

The final tuple matches the spec's pinned shape at spec line 448 character-for-character: `("BigInt", "DjangoListField", "DjangoOptimizerExtension", "DjangoType", "OptimizerHint", "__version__", "auto", "finalize_django_types", "strawberry_config")`. ASCII-sort ordering holds (`s`=115 > `f`=102). No other public exports added or removed; `auto`, `DjangoListField`, `DjangoOptimizerExtension`, `OptimizerHint`, `DjangoType`, `finalize_django_types` re-exports are untouched. Public-surface delta is exactly one name (`strawberry_config`), as the spec authorized.

### Cohesion / responsibility

- `django_strawberry_framework/scalars.py` is the single source of truth for package-defined scalar registration. `BigInt` (the symbol), `_BIGINT_SCALAR_DEFINITION` (its `ScalarDefinition`), `_PACKAGE_SCALAR_MAP` (the canonical defaults dict), and `strawberry_config` (the registration helper) all live in one module. Future scalars (`Upload`, `TODO-ALPHA-028-0.0.11`) extend the dict; the factory signature is forward-stable.
- `django_strawberry_framework/__init__.py` is the public-export manifest. Slice 1 widened it cleanly without re-organizing other re-exports.
- `examples/fakeshop/config/schema.py` is the single project-level schema-construction site for the example app. Per-app schemas (`apps/library/schema.py`, `apps/products/schema.py`) declare `@strawberry.type class Query` only; the kwarg ownership (`config=`, `extensions=`) is correctly localized to the project schema. No misplaced responsibility.
- Documentation surfaces (`docs/README.md`, `docs/GLOSSARY.md`, `GOAL.md`, `TODAY.md`) reference the helper through the public package boundary; no doc copy-paste of the implementation. The new `## strawberry_config` GLOSSARY entry is the canonical glossary anchor; every other doc surface links to it via Markdown anchor.

### Coherence-of-story across new docs/code

The post-migration story reads consistently across every touched surface:

- **Source contract** (`scalars.py`): the helper signature, the `_PACKAGE_SCALAR_MAP` content, the two `ValueError` branches.
- **Tests** (`test_scalars.py`, `test_converters.py`, `test_init.py`): 15 new pytest items pin every branch; the `__all__` pin closes Slice 1's deliberate handoff failure; 10 converter-table sites exercise the migration broadening per Decision 5.
- **Example** (`examples/fakeshop/config/schema.py`): the canonical "right shape" the consumer copies.
- **Docs** (`docs/README.md` Quick start + Schema setup boundary x2, `docs/GLOSSARY.md` `BigInt scalar` + new `## strawberry_config` + Public exports + Index, `GOAL.md` astronomy showcase, `TODAY.md` fakeshop block): every consumer-facing reference now demonstrates the post-migration pattern.
- **Release record** (`KANBAN.md` `DONE-047-0.0.7`, `CHANGELOG.md` `[Unreleased] ### Added` / `### Changed` / `### Removed`, removed `[0.0.6] ### Notes` line): the `[0.0.6]` "tracked as a follow-up" pointer is gone; `[Unreleased]` carries the breaking-change consumer migration with the exact before/after `diff` block.

Kwarg order is consistent (`query=`, `config=strawberry_config()`, `extensions=[...]`) across every site that has all three; sites with only `query=` and `config=` (the `GOAL.md` astronomy showcase) preserve their pre-edit shape.

## Deferred work surfaced

The cross-slice walk surfaced **TWO stale-wording sites in standing docs** that the build did not (and could not) edit because both are outside the spec's DoD scope. Both should be recorded in `bld-final.md`'s `### Deferred work catalog`:

1. **`docs/TREE.md` lines 201 and 246** carry the literal phrase `# BigInt public scalar (NewType-based; Strawberry deprecation suppressed at definition site)`. The "Strawberry deprecation suppressed at definition site" wording is **factually stale** post-Slice-1 — Slice 1 removed the `warnings.catch_warnings()` suppression block (Decision 6) and migrated to the no-warning `strawberry.scalar(name=..., serialize=..., parse_value=...)` overload. Spec DoD item 13 explicitly forbids `docs/TREE.md` edits in this card. Disposition: deferred-work catalog entry. Surfaced by Slice 4's planning pass, Slice 4's build-report `### Notes for Worker 1 (spec reconciliation)` #3, Slice 4's final-verification Worker 1 memory, and re-confirmed at the integration pass via `grep -n "scalars.py" docs/TREE.md`.

2. **`docs/GLOSSARY.md` line 40** carries the literal sentence `_Note:_ The import path is now clean — no Strawberry deprecation warning escapes (the deprecation is suppressed at the definition site in scalars.py).`. The "the deprecation is suppressed at the definition site" wording is **factually stale** post-Slice-1 for the same reason as the TREE.md entry above — the suppression block is gone; the import path is clean because the no-warning overload does not emit `DeprecationWarning` in the first place, not because of suppression. This site was NOT flagged by any prior slice artifact; surfaced for the first time in this integration pass via `grep -n "deprecation is suppressed" docs/GLOSSARY.md`. The note paragraph sits between the "## Public exports" symbol list and the "## Index" alphabetical table.

3. **`KANBAN.md` line 50** carries a forward-looking sentence: "The last `0.0.7` card to ship owns the version bump from `0.0.6` per Decision 10 of `docs/SPECS/spec-016-list_field-0_0_7.md`." `DONE-047-0.0.7` is now the last `0.0.7` card and deferred the bump per Decision 8; the sentence is forward-looking against a hypothetical future card. Slice 5 Worker 3 and Worker 1 dispositioned this as "no spec edit needed — informational maintainer-cut-time content". Surfaced here for traceability; the disposition stands.

**Recommendation:** finding #2 (`docs/GLOSSARY.md` line 40) is in-scope for cross-slice integration consolidation per BUILD.md "Cross-slice integration pass" check "Comments now tell one coherent story across the new code" — the GLOSSARY note paragraph is part of the same `## Public exports` section that Slice 4 already touched (the slice 4 plan added a new bullet to that section's bulleted list at lines 26-33). The stale `_Note:_` paragraph sits immediately after the bulleted list. Editing this single line during a Worker 2 consolidation pass keeps the consumer-facing GLOSSARY surface coherent post-migration with minimal risk.

Finding #1 (`docs/TREE.md`) is explicitly forbidden by spec DoD item 13 in this card and stays deferred to the catalog.

Finding #3 (`KANBAN.md`) was dispositioned by the slice 5 review pass and stays deferred to the catalog.

## Integration outcome

`revision-needed`.

Rationale: finding #2 (`docs/GLOSSARY.md` line 40 stale "deprecation suppressed at definition site" `_Note:_` paragraph) is a coherence-of-story finding under BUILD.md "Cross-slice integration pass" check 7 ("whether comments now tell one coherent story across the new code"). The note paragraph is consumer-facing prose inside the `## Public exports` section of `docs/GLOSSARY.md` and is now factually wrong post-Slice-1's removal of the `warnings.catch_warnings()` suppression block. Leaving it in place is a documented stale-wording site that the integration pass exists to catch.

Worker 0 should dispatch:

1. Worker 2 consolidation pass — edit `docs/GLOSSARY.md` line 40 to rewrite the `_Note:_` paragraph so the wording matches the post-migration reality (the no-warning `strawberry.scalar(name=..., ...)` overload does not emit `DeprecationWarning` in the first place; the import path is clean by construction, not by suppression). Suggested rewrite: `_Note:_ The import path is now clean — no Strawberry deprecation warning escapes (the registration uses Strawberry's no-warning `strawberry.scalar(name=..., serialize=..., parse_value=...)` overload via the `strawberry_config` factory).` Worker 2 may rephrase as appropriate; the contract is that the wording no longer claims suppression.
2. Worker 3 review pass — verify the GLOSSARY edit is the only change in the consolidation pass diff (no other docs / source / test touched), and that the rewritten paragraph is internally consistent with the existing `## strawberry_config` entry body and the existing `## BigInt scalar` entry body.
3. Worker 1 integration re-pass — re-confirm coherence-of-story across the new code, walk the deferred-work catalog (which should retain findings #1 and #3, drop #2), and set `Status: final-accepted` if the consolidation pass cleared the GLOSSARY note.

## Summary

The cross-slice integration pass confirms the build's mutation surface is internally consistent: helpers are not duplicated across slices, naming is uniform, the two `ValueError` branches use distinct-but-consistent wording, the `config=strawberry_config()` consumer-migration pattern repeats by design (not by mistake) as the canonical post-migration contract, public-surface delta is exactly one name (`strawberry_config`), responsibility is correctly localized to `django_strawberry_framework/scalars.py` and `django_strawberry_framework/__init__.py`, and the post-migration story reads coherently across source, tests, example, docs, and release records. Two stale-wording sites surfaced — `docs/TREE.md` line 201/246 (deferred to catalog per DoD item 13) and `docs/GLOSSARY.md` line 40 (`_Note:_` paragraph claiming the deprecation is still suppressed). The GLOSSARY site is a coherence-of-story finding the integration pass is exactly the right pass to address; the TREE.md site is a catalog entry. Setting `Status: revision-needed` so Worker 0 can dispatch a Worker 2 consolidation pass + Worker 3 review pass before re-spawning Worker 1 for an integration re-pass.

---

## Build report (Worker 2, consolidation pass)

### Files touched

- `docs/GLOSSARY.md` — rewrote the `_Note:_` paragraph in the `## Public exports` section (one-line edit) so the wording matches the post-Slice-1 reality. The line previously claimed the import is clean because "the deprecation is suppressed at the definition site in `scalars.py`"; Slice 1 removed the `warnings.catch_warnings()` block entirely and the no-warning `strawberry.scalar(name=..., serialize=..., parse_value=...)` overload does not emit `DeprecationWarning` in the first place. New wording: "_Note:_ The import path is clean by construction — the registration path uses Strawberry's no-warning `strawberry.scalar(name=..., serialize=..., parse_value=...)` overload via the [`strawberry_config`](#strawberry_config) factory, so no `DeprecationWarning` is emitted." The forward link to the existing `## strawberry_config` glossary entry threads the note into the canonical anchor Slice 4 already landed; coherence preserved with the `## BigInt scalar` entry body (which also calls the `strawberry.scalar(name=..., ...)` overload by name) and with the new `## strawberry_config` entry body (which is the linked target).

### Tests added or updated

None. The consolidation pass is a one-line documentation edit; the post-Slice-1 no-warning regression is already pinned by `tests/test_scalars.py::test_package_import_does_not_emit_strawberry_deprecation_warning` (the `-W error::DeprecationWarning` subprocess test), which continues to pass unchanged per Slice 2's contract.

### Validation run

- `uv run ruff format .` — pass (`118 files left unchanged`).
- `uv run ruff check --fix .` — pass (`All checks passed!`).
- `git status --short` after both ruff invocations:
  - `M docs/GLOSSARY.md` — slice-intended (this consolidation pass's one edit; appears in `### Files touched`).
  - `M CHANGELOG.md`, `M GOAL.md`, `M KANBAN.md`, `M TODAY.md`, `M django_strawberry_framework/__init__.py`, `M django_strawberry_framework/scalars.py`, `M docs/README.md`, `M docs/spec-020-scalar_map_helper-0_0_7-terms.csv`, `M docs/spec-020-scalar_map_helper-0_0_7.md`, `M examples/fakeshop/config/schema.py`, `M tests/base/test_init.py`, `M tests/test_scalars.py`, `M tests/types/test_converters.py` — pre-existing per-slice changes from Slices 1-5; NOT touched by this consolidation pass (verified by `git diff docs/GLOSSARY.md` showing only the targeted `_Note:_` line as a new delta beyond the Slice-4 changes already present).
  - `?? docs/builder/bld-integration.md`, `?? docs/builder/bld-slice-*.md`, `?? docs/builder/build-020-scalar_map_helper-0_0_7.md` — build artifacts (this consolidation pass appends to `bld-integration.md` only).
  - No unrelated tool churn.

### Implementation notes

- Chose option (b) (rewrite) over option (a) (remove) per Worker 0 discretion: the note pins a real consumer-facing property — "package import does not leak `DeprecationWarning`" — that the regression test in `tests/test_scalars.py` continues to enforce. Removing the line would drop a useful reader signpost. Rewriting it preserves the signpost and updates the mechanism the reader is told to expect.
- Added a Markdown anchor link to the existing `## strawberry_config` entry (`[strawberry_config](#strawberry_config)`) inside the note. The link uses the same anchor Slice 4's GLOSSARY edits and existing GLOSSARY entries already use; no new anchor introduced.
- Spelled the overload signature `strawberry.scalar(name=..., serialize=..., parse_value=...)` verbatim — same shape used in the `## BigInt scalar` entry body, the `## strawberry_config` entry body, the spec Decision 3 pinned shape, and Worker 1's suggested rewrite. No wording drift.
- Did NOT touch `docs/TREE.md` (deferred per spec DoD item 13; finding #1 stays in `bld-final.md`'s deferred-work catalog) and did NOT touch `KANBAN.md` line 50 (finding #3 already dispositioned by Slice 5 Worker 3 / Worker 1 as informational; stays in the catalog).

### Notes for Worker 3

The integration re-pass (Worker 1) should:
- Verify the single GLOSSARY diff is the only consolidation-pass change (the other 13 modified files are prior-slice changes; verifiable by `git diff docs/GLOSSARY.md` showing exactly one new delta beyond the Slice-4 content).
- Re-walk the deferred-work catalog: finding #2 is cleared; findings #1 (TREE.md) and #3 (KANBAN.md line 50) remain.
- Confirm coherence-of-story is now clean across `## Public exports` → `## BigInt scalar` → `## strawberry_config` in `docs/GLOSSARY.md` — all three reference the same `strawberry.scalar(name=..., ...)` overload shape.

### Notes for Worker 1 (spec reconciliation)

None. The edit is mechanical wording correction; no spec amendment required.

---

## Review (Worker 3, integration-consolidation pass)

### High:

None.

### Medium:

None.

### Low:

None.

### DRY findings

None. The consolidation pass is a one-line wording correction; no helper, literal, or pattern duplication introduced or available to surface.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` carries only the Slice 1 changes already authorized by spec DoD items 3 and 18 (the `strawberry_config` import widening at line 23 and the `__all__` tuple append at line 37). This consolidation pass did NOT touch `django_strawberry_framework/__init__.py` — verified by inspecting the pass's `git status --short` report in the Worker 2 build report, which lists `M docs/GLOSSARY.md` as the only file the consolidation modified beyond the prior-slice carry-forwards. No new public exports added by this pass.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; this consolidation pass did not modify `CHANGELOG.md`. The `CHANGELOG.md` modification in the working tree is the pre-existing Slice 5 change; verified by Worker 2's `git status --short` listing `M CHANGELOG.md` under "pre-existing per-slice changes from Slices 1-5; NOT touched by this consolidation pass".

### Documentation / release sanity (only when the slice touches docs, release metadata, KANBAN, or archived specs)

The consolidation pass modified one documentation surface: `docs/GLOSSARY.md` line 40 (the `_Note:_` paragraph at the end of the `## Public exports` section). Verified end-to-end:

1. **Stale wording removed.** `grep -n "suppressed at the definition site" docs/GLOSSARY.md` returns zero matches. The exact prior wording (`_Note:_ The import path is now clean — no Strawberry deprecation warning escapes (the deprecation is suppressed at the definition site in scalars.py).`) appears as the single `-` line in `git diff HEAD docs/GLOSSARY.md`; the new wording (`_Note:_ The import path is clean by construction — the registration path uses Strawberry's no-warning strawberry.scalar(name=..., serialize=..., parse_value=...) overload via the [strawberry_config](#strawberry_config) factory, so no DeprecationWarning is emitted.`) appears as the corresponding `+` line. The `KANBAN.md` lines 1400 and 1415 hits for `"suppressed at the definition site"` are inside the past-tense `DONE-013-0.0.6` card body — historical record, deliberately preserved by Slice 5's contract (which only removed the `[0.0.6] ### Notes` line from `CHANGELOG.md`, not the `KANBAN.md` Done body). Not stale; intentional snapshot of what `0.0.6` shipped. The cross-doc grep returns no other live-text occurrences.
2. **Replacement wording is factually correct.** The new sentence (a) attributes the clean import surface to construction via the no-warning overload rather than to suppression, (b) names the overload signature `strawberry.scalar(name=..., serialize=..., parse_value=...)` verbatim — same spelling used in spec Decision 3, the `## BigInt scalar` GLOSSARY entry body, and the `## strawberry_config` GLOSSARY entry body, (c) routes the reader to `strawberry_config` via the canonical anchor, (d) preserves the consumer-facing property the prior note pinned (no `DeprecationWarning` escapes at import time — still enforced by the unchanged `tests/test_scalars.py::test_package_import_does_not_emit_strawberry_deprecation_warning` `-W error::DeprecationWarning` subprocess regression). No new stale wording introduced; no claim about suppression remains.
3. **Markdown anchor link points at the existing heading slug.** `grep -n "^## strawberry_config" docs/GLOSSARY.md` returns `976:## strawberry_config` (the Slice 4 entry). The link `[strawberry_config](#strawberry_config)` uses the GitHub-style auto-generated slug for that `##` heading — same slug already in use by the Slice 4 Public exports bullet (`docs/GLOSSARY.md` line 32, `[strawberry_config](#strawberry_config)`) and the Slice 4 BigInt paragraph (`docs/GLOSSARY.md` line 179, `[strawberry_config](#strawberry_config)`). Anchor target exists; convention matches neighbors.
4. **No other lines in `docs/GLOSSARY.md` changed by the consolidation pass.** `git diff HEAD docs/GLOSSARY.md | grep "^-[^-]"` returns exactly one removed line — the stale `_Note:_` — confirming the consolidation contributes exactly one `-` / `+` swap on top of the Slice 4 carry-forward content. The other `+` hunks in `git diff HEAD` (the Public exports bullet add at line 32, the Index row at line 113, the BigInt registration paragraph at line 179, the entire `## strawberry_config` entry at lines 976+) are Slice 4's prior contributions, not this consolidation pass's.
5. **No other files modified by this consolidation pass.** Worker 2's `### Validation run` enumerates every `M` entry in `git status --short` and classifies the 13 non-GLOSSARY `M` entries as Slice 1-5 carry-forwards. Cross-checked against the integration artifact's `### Per-artifact walk results` and the build plan's checklist — every `M` entry maps to a completed prior-slice artifact. The new `??` entries are the build artifacts themselves. Pass scope: one file, one line. Matches Worker 1's finding.
6. **Coherence-of-story across `## Public exports` → `## BigInt scalar` → `## strawberry_config` is clean.** All three reference the `strawberry.scalar(name=..., serialize=..., parse_value=...)` overload identically by name; the registration path is now consistently described as "no-warning by construction" rather than "deprecation suppressed". The `_Note:_` paragraph now reads as a forward-pointer to the `## strawberry_config` entry the reader can follow for the full contract; the `## BigInt scalar` entry already linked the same anchor in its registration paragraph at line 179.

No obsolete "coming soon" / "planned" / old-version wording introduced. No anchors broken. The single intended edit is the only edit; the deferred-work catalog can drop finding #2 (this finding) and retain findings #1 (`docs/TREE.md`) and #3 (`KANBAN.md` line 50) as the slice 5 review-pass dispositions already require.

### What looks solid

- One-line scope: the consolidation pass contributes exactly one line removal + one line replacement to `docs/GLOSSARY.md` and nothing else, matching Worker 1's integration finding contract.
- Option-(b) (rewrite) over option-(a) (remove) preserves a useful consumer-facing signpost (the "no `DeprecationWarning` escapes at import time" property) and rethreads it through the canonical Slice 4 anchor — Worker 2's `### Implementation notes` justifies the choice cleanly.
- Anchor link target verified to exist via grep against `^## strawberry_config`, and the slug convention matches both the Slice 4 Public exports bullet and the Slice 4 BigInt paragraph already using `[strawberry_config](#strawberry_config)` — no anchor proliferation.
- Wording aligns with the spec's overload signature spelling (`strawberry.scalar(name=..., serialize=..., parse_value=...)`) verbatim per spec Decision 3, the `## BigInt scalar` body, and the `## strawberry_config` body — no wording drift across surfaces.
- Worker 2's `### Validation run` explicitly classifies the 13 non-GLOSSARY `M` entries as prior-slice carry-forwards; the cumulative-diff trap is correctly applied at the integration-pass scope.
- `ruff format` / `ruff check --fix` both reported clean (no Python touched; format/check are no-ops on the Markdown edit, which is expected).

### Temp test verification

None used. The consolidation pass is a Markdown-only edit; the post-Slice-1 no-warning regression remains pinned by `tests/test_scalars.py::test_package_import_does_not_emit_strawberry_deprecation_warning` (unchanged). No new behavior to pin and no review suspicion that called for a temp test.

### Notes for Worker 1 (spec reconciliation)

None. The consolidation edit is a documentation wording correction inside a section the spec does not pin verbatim. The spec's GLOSSARY-touching DoD items (Slice 4) named the Public exports bullet, the Index row, the `## strawberry_config` entry body, and the `## BigInt scalar` registration paragraph — none of which named the `_Note:_` paragraph. The integration pass's authority to consolidate stale wording inside touched surfaces stands without spec amendment.

When Worker 1 re-runs the integration pass, the deferred-work catalog should drop finding #2 (cleared by this consolidation pass) and retain findings #1 (`docs/TREE.md` stale wording, blocked by spec DoD item 13) and #3 (`KANBAN.md` line 50 forward-looking sentence, dispositioned by Slice 5 Worker 3 / Worker 1 as informational) for `bld-final.md`'s `### Deferred work catalog`.

### Static inspection helper

Skipped. The consolidation pass is a Markdown-only edit to `docs/GLOSSARY.md`; `scripts/review_inspect.py` operates on Python source. No new `.py` files touched, no existing `.py` file under `optimizer/` or `types/` modified, no 30/50-line logic additions to any `.py` file. BUILD.md "When to run the helper during build" thresholds not crossed.

### Review outcome

`review-accepted`. The consolidation pass cleared finding #2 from the integration artifact with a one-line edit scoped to `docs/GLOSSARY.md` line 40 exactly as Worker 1's contract specified. Stale wording is gone (`grep "suppressed at the definition site" docs/GLOSSARY.md` returns zero), the replacement is factually correct and threads through the `strawberry_config` factory and the no-warning overload signature, the Markdown anchor resolves to the existing `## strawberry_config` heading, no other lines in `docs/GLOSSARY.md` changed, and no other files were modified by this consolidation pass. Worker 0 should dispatch Worker 1 for the integration re-pass; the deferred-work catalog hands off with findings #1 and #3 only.

---

## Final verification (Worker 1, integration re-pass)

### Original finding clearance

- **Stale wording removed.** `grep -n "suppressed at the definition site" docs/GLOSSARY.md` returns zero matches (exit 0, no output). The prior `_Note:_` paragraph at the end of the `## Public exports` section is gone.
- **Replacement wording correct at the same location.** `docs/GLOSSARY.md` line 40 now reads `_Note:_ The import path is clean by construction — the registration path uses Strawberry's no-warning strawberry.scalar(name=..., serialize=..., parse_value=...) overload via the [strawberry_config](#strawberry_config) factory, so no DeprecationWarning is emitted.` The wording (a) attributes the clean import surface to construction rather than suppression, (b) names the no-warning overload signature verbatim (matches `## BigInt scalar` body, `## strawberry_config` body, spec Decision 3), (c) routes the reader to the canonical `strawberry_config` glossary entry, (d) preserves the consumer-facing property the prior note pinned (no `DeprecationWarning` at package import time — still enforced by the unchanged `tests/test_scalars.py::test_package_import_does_not_emit_strawberry_deprecation_warning` regression).
- **Markdown anchor resolves.** `grep -n "^## strawberry_config" docs/GLOSSARY.md` returns `976:## strawberry_config`. The `[strawberry_config](#strawberry_config)` link uses the same slug already in use by the Slice 4 Public exports bullet and the Slice 4 BigInt registration paragraph.

### Cross-slice integration re-walk

Re-walked the BUILD.md "Cross-slice integration pass" checks against the consolidation-pass diff:

- **Repeated literals (shadow overviews).** Unchanged from the original integration pass — no Python touched by the consolidation pass, so the cross-shadow comparison stands as recorded above. No new repeated-literal cross-slice hazards.
- **Imports (one-way dependency direction).** Unchanged — no Python touched. The Slice 1 `from .scalars import BigInt, strawberry_config` widening in `django_strawberry_framework/__init__.py` is the only import-line change in the build, and it remains within the documented public-export boundary.
- **Public surface delta.** `git diff -- django_strawberry_framework/__init__.py` shows exactly two changes, both authorized by spec DoD items 3 and 18: the import line widened to add `strawberry_config`, and `__all__` appended with `"strawberry_config"`. Final tuple matches the spec-pinned shape character-for-character. Public-surface delta is exactly one new name (`strawberry_config`).
- **Coherence-of-story across docs/code.** The `_Note:_` paragraph at `docs/GLOSSARY.md` line 40 now threads consistently with the `## Public exports` bullet for `strawberry_config` (line 32), the `## BigInt scalar` registration paragraph (line 179), and the `## strawberry_config` entry body (line 976+). All three reference the `strawberry.scalar(name=..., serialize=..., parse_value=...)` overload by name; the registration path is uniformly described as "no-warning by construction" rather than "deprecation suppressed". No remaining wording drift.

### Consolidation-pass scope confirmation

`git diff HEAD docs/GLOSSARY.md` shows the consolidation contributes exactly one `-` / `+` swap on top of the Slice 4 carry-forward content (the prior `_Note:_` line removed, the new `_Note:_` line added at the same location). Every other `+` hunk in the GLOSSARY diff (the Public exports bullet at line 32, the Index row at line 113, the BigInt registration paragraph at line 179, and the entire `## strawberry_config` entry at lines 976+) is Slice 4's prior contribution. `git status --short` lists no consolidation-pass changes beyond `docs/GLOSSARY.md`; the 13 other `M` entries are Slices 1–5 carry-forwards already enumerated in the per-artifact walk.

### Deferred-work catalog hand-off

Per the consolidation-pass review and the task contract, the deferred-work catalog for `bld-final.md` retains:

1. **`docs/TREE.md` lines 201 / 246** — stale `# BigInt public scalar (NewType-based; Strawberry deprecation suppressed at definition site)` wording. Spec DoD item 13 forbids `docs/TREE.md` edits in this card; deferred as a future-card concern.
2. **`KANBAN.md` line 50** — forward-looking "last `0.0.7` card to ship owns the version bump" sentence; dispositioned by Slice 5 review as informational. Stays in the catalog for traceability.

**Dropped** from the catalog: the GLOSSARY line 40 stale-note finding, cleared by the consolidation pass.

### Spec status-line refresh

Spec line 4 refreshed from `Status: shipped — Slices 1–5 all landed (helper module + BigInt redefinition; tests; example-app migration; docs; KANBAN + CHANGELOG). Only the cross-slice integration pass and the final test-run gate remain (workflow gates, not slices).` to `Status: shipped — Slices 1–5 all landed (helper module + BigInt redefinition; tests; example-app migration; docs; KANBAN + CHANGELOG) and the cross-slice integration pass is final-accepted. Only the final test-run gate remains (workflow gate, not a slice).` to reflect post-integration-pass reality.

### Spec changes made (Worker 1 only)

- `docs/spec-020-scalar_map_helper-0_0_7.md` line 4 — status-line refresh; reflects that the cross-slice integration pass is final-accepted post-consolidation. Triggered by this integration re-pass.

### Final status

`final-accepted`. The integration artifact's original Worker 1 finding is cleared by the consolidation pass; cross-slice integration checks (helpers, naming, error-handling, repeated patterns, repeated literals, public surface, cohesion / responsibility, coherence-of-story) are now clean across every touched surface; the deferred-work catalog hands off two retained findings to `bld-final.md`. Worker 0 may dispatch Worker 1 for the final test-run gate.
