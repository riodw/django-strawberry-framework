# Review: `django_strawberry_framework/scalars.py`

Status: verified

## DRY analysis

- Defer the `_with_strawberry_compat(definition_fn)` extraction until a second scalar lands in this module. Today `scalars.py:91-102` is the only `strawberry.scalar(...)` call in the package (confirmed by `grep -n "strawberry.scalar(" django_strawberry_framework/scalars.py` returning exactly one hit; the `Upload` scalar promised at `scalars.py:3` exists only as a docstring forward-reference with no source body yet). Trigger: a second `strawberry.scalar(NewType(...), ...)` definition is added to this file. At that point both definitions duplicate the `with warnings.catch_warnings(): / warnings.filterwarnings("ignore", message="Passing a class to strawberry.scalar", category=DeprecationWarning)` block and the helper collapses them to one site. Until the second scalar lands the helper is a one-call indirection with no consolidation payoff. WIP-ALPHA-020-0.0.7 (the warning-free `StrawberryConfig.scalar_map` migration) supersedes this defer entirely — when that card ships, the suppression block disappears and this defer becomes moot.

## High:

None.

## Medium:

None.

## Low:

### L1 — Stale forward-reference card anchor in module docstring

`scalars.py:3` reads `Today: ``BigInt``. Future scalars (e.g. ``Upload`` per TODO-ALPHA-027) land here.`, but `KANBAN.md:407` reserves `TODO-ALPHA-027-0.0.11` for **Mutations + auto-generated Input types** (the `DjangoMutation` family). The `Upload` scalar is `TODO-ALPHA-028-0.0.11` at `KANBAN.md:445`. The anchor in the docstring sends a future reader to the wrong KANBAN card.

Recommended change: update the docstring to point at `TODO-ALPHA-028` (Upload scalar and file / image field mapping). No logic impact; pure documentation drift.

```django_strawberry_framework/scalars.py:1-3
"""Public scalars defined by django-strawberry-framework.

Today: ``BigInt``. Future scalars (e.g. ``Upload`` per TODO-ALPHA-027) land here.
```

### L2 — Version-anchored "For 0.0.6" wording in the suppression-block comment

`scalars.py:86` reads `# block entirely. For 0.0.6, the deprecation is suppressed at the definition` inside the 14-line explanatory comment that documents why the `warnings.catch_warnings()` filter is wrapped around the `strawberry.scalar(...)` definition. The wording pegs the suppression to a specific release (`0.0.6`) but the file is now shipped in `0.0.7` unchanged, and the actual exit condition for the comment block is the WIP-ALPHA-020 card (already cited correctly at `scalars.py:83`), not "the 0.0.6 release window". Reading the comment in `0.0.7` gives a future reader the false impression the suppression is a 0.0.6-only debt that should already have been retired.

Recommended change: drop the "For 0.0.6" prefix so the comment reads "Until WIP-ALPHA-020-0.0.7 lands, the deprecation is suppressed at the definition site so consumers importing `django_strawberry_framework` see no warning." The trigger condition is already named two lines above (`WIP-ALPHA-020-0.0.7` at `scalars.py:83`); re-stating it inline removes the version anchor and keeps the comment correct under any future release that ships before the warning-free design.

```django_strawberry_framework/scalars.py:86-90
# block entirely. For 0.0.6, the deprecation is suppressed at the definition
# site so consumers importing django_strawberry_framework see no warning. A
# regression test (test_package_import_does_not_emit_strawberry_deprecation_warning)
# pins the no-leak contract; if the suppression is accidentally removed or
# Strawberry tightens the deprecation, the test catches it.
```

## What looks solid

### DRY recap

- **Existing patterns reused.** Single canonical regex `_BIGINT_STRING_PATTERN` at `scalars.py:22` drives both the `_parse_bigint` string branch (`scalars.py:49`) and every documented rejection case in the docstring (`scalars.py:30-42`) — no duplicate string-shape validation elsewhere. `scalars.py:23` is the single `BigInt` definition site re-exported via `django_strawberry_framework/__init__.py:23` and consumed by `types/converters.py:51` for the `BigIntegerField` / `PositiveBigIntegerField` mappings (`types/converters.py:66,70`), so the wire-format contract has exactly one source of truth.
- **New helpers considered.** A `_with_strawberry_compat(definition_fn)` wrapper around the `warnings.catch_warnings()` block was evaluated and explicitly deferred — there is only one `strawberry.scalar(...)` call site today and the helper would be a one-call indirection. The defer is captured in `## DRY analysis` with a single-grep trigger condition; WIP-ALPHA-020-0.0.7 supersedes the defer entirely.
- **Duplication risk in the current file.** The bool-rejection branches at `scalars.py:44-45` and `scalars.py:73-74` look like duplicate `isinstance(value, bool)` checks but are sibling-by-design: `_parse_bigint` raises `ValueError` (per GraphQL `parse_value` contract) while `_serialize_bigint` raises `TypeError` (per GraphQL `serialize` contract), with deliberately distinct error messages. Same logical guard, two different contracts; collapsing them would erase the input/output asymmetry. Likewise the docstrings on `_parse_bigint` and `_serialize_bigint` enumerate symmetric accept/reject matrices — intentional documentation parallelism, not a DRY violation.

### Other positives

- **Strict input/output symmetry.** `_parse_bigint` accepts Python `int` (excluding `bool`) and decimal strings matching `^(0|-?[1-9][0-9]*)$`; `_serialize_bigint` accepts Python `int` (excluding `bool`) only. The "permissive `serialize=str` would let a schema emit values the parser rejects" comment at `scalars.py:69-71` correctly justifies the strict serializer side; without it the schema could emit `bool` (`str(True) == "True"`) or `float` (`str(1.9) == "1.9"`) and the parser would reject those on the way back in.
- **Regex correctness against the documented matrix.** Verified end-to-end against the docstring's accept-list and reject-list: `0`, `1`, `-1`, `42`, `-42`, signed-int64-min, signed-int64-max all match; the documented rejections (`""`, `"+1"`, `"01"`, `"-0"`, `"-01"`, `"1.9"`, `"1e3"`, `"1_000"`, `" 123 "`, `"\t123"`, `"abc"`, `"0x10"`, Unicode-digit strings) all fail `fullmatch`. The `(0|-?[1-9][0-9]*)` alternation correctly forbids `-0` while permitting `0`.
- **Bool-before-int ordering.** `isinstance(value, bool)` is checked **before** `isinstance(value, int)` in both functions (`scalars.py:44-46`, `scalars.py:73-75`). Without that ordering, `True` and `False` would slip through the `int` branch (bool subclasses int) and parse / serialize as `1` / `0` — the explicit guard pins this against accidental reordering.
- **Float silent-truncation guard.** Floats are rejected explicitly in `_parse_bigint`'s docstring (`scalars.py:34`) and in the test pin at `tests/test_scalars.py:133-140`. Without the guard, `1.9` would slip into the `int()` branch only if the parser had a fall-through — the type-shape ordering (`bool → int → str → reject`) means floats hit the trailing `raise ValueError` at `scalars.py:56` instead of being silently coerced, which is correct.
- **Strawberry deprecation suppression is tightly scoped.** `warnings.catch_warnings()` wraps **only** the `strawberry.scalar(...)` call at `scalars.py:91-102`; the explicit `warnings.filterwarnings("ignore", message="Passing a class to strawberry.scalar", category=DeprecationWarning)` matches Strawberry's deprecation message by its prefix and `DeprecationWarning` category, so no broader filter leaks into module-load time. A regression test (`tests/test_scalars.py:229-252`) reimports the package under `-W error::DeprecationWarning` in a subprocess and pins the no-leak contract — accidental removal of the filter, or Strawberry tightening the deprecation to a hard error, both flip the test red.
- **Wire-format contract is enforced both ways.** Schema-execution tests at `tests/types/test_converters.py:523-612` pin `BigIntegerField → BigInt!`, `BigIntegerField(null=True) → BigInt`, and `PositiveBigIntegerField → BigInt!` introspection shapes; the explicit `BigAutoField → Int` test at `tests/types/test_converters.py:615-644` documents the deliberate carve-out (no current-day recourse for the `2**31` boundary on `BigAutoField`). Combined with the strict parser/serializer unit pins at `tests/test_scalars.py:23-204`, both the internal-behavior and wire-format sides have direct coverage.
- **Public-export smoke test is intentionally type-shape agnostic.** `tests/test_scalars.py:212-221` asserts `BigInt is not None` and explicitly avoids `ScalarWrapper` type assertions per the docstring comment — `ScalarWrapper` is an undocumented internal Strawberry path and would break on any private-API churn. The test catches `__init__.py` import-order regressions without coupling to Strawberry internals.
- **Module-load thread-safety caveat is acknowledged in the spec.** `warnings.catch_warnings()` is not thread-safe per CPython docs, but the suppression block runs exactly once at module load time under the CPython import lock (see `spec-013-deferred_scalars-0_0_6.md:724`). A future re-architecture that imports `scalars.py` from a worker thread would need to revisit, but for the shipped single-threaded module-load path this is correct.

### Summary

`scalars.py` is a small (~100-line), tightly factored module: one regex constant, two strict parser/serializer functions with symmetric accept/reject matrices, and one Strawberry scalar definition guarded by a tightly scoped deprecation-suppression block. No logic findings emerged in this pass — the parser/serializer ordering (`bool → int → str → reject`) correctly handles every documented edge case, the regex matches the documented matrix end-to-end, and the deprecation suppression is regression-tested via subprocess-isolated reimport. Two Low documentation findings: the module docstring's `TODO-ALPHA-027` anchor for `Upload` points at the Mutations card (the correct anchor is `TODO-ALPHA-028`), and the suppression-block comment is version-anchored to `0.0.6` when the actual exit condition is the `WIP-ALPHA-020-0.0.7` card (already cited correctly two lines above). One single-bullet DRY defer pre-loaded with a one-grep trigger for the case where a second `strawberry.scalar(...)` definition lands in this file — but WIP-ALPHA-020-0.0.7 supersedes the defer entirely, so the next DRY cycle will most likely retire it rather than fire on the trigger.

---

## Fix report (Worker 2)

### Files touched

- `django_strawberry_framework/scalars.py:3` — no source-logic edits; this consolidated spawn lands the two Low documentation fixes under the Comment/docstring pass below. The Fix report is intentionally a no-op because both findings are doc-only and the artifact has no High/Medium/source-logic items.

### Tests added or updated

- None. Both findings are documentation-only edits that do not change runtime behavior. Existing regression tests (`tests/test_scalars.py:229-252` for the deprecation-suppression contract, `tests/test_scalars.py:23-204` for parser/serializer pinning) remain green by construction.

### Validation run

- `uv run ruff format .` — pass (`118 files left unchanged`)
- `uv run ruff check --fix .` — pass (`All checks passed!`)
- No focused tests were run per `AGENTS.md` "Do not run pytest after edits".

### Notes for Worker 3

- Shadow file used: none. The two Lows are localised single-line edits in `scalars.py`; reading the live source was sufficient.
- KANBAN-check verification: `grep -n "TODO-ALPHA-028" KANBAN.md` returns `445:### TODO-ALPHA-028-0.0.11 — Upload scalar and file / image field mapping` confirming the corrected anchor maps to the `Upload` card. `TODO-ALPHA-027-0.0.11` at `KANBAN.md:407` is `Mutations + auto-generated Input types` (the wrong card the prior docstring pointed at).
- DRY defer (single bullet at the head of the artifact) carried forward unchanged: the `_with_strawberry_compat(definition_fn)` helper is a one-call indirection today; WIP-ALPHA-020-0.0.7 supersedes the defer entirely when it lands.
- No false-premise rejections; both Lows landed exactly as Worker 1 recommended.

---

## Comment/docstring pass

### Files touched

- `django_strawberry_framework/scalars.py:3` — module docstring anchor `TODO-ALPHA-027` → `TODO-ALPHA-028` so the `Upload` forward-reference points at the correct KANBAN card (`Upload scalar and file / image field mapping` at `KANBAN.md:445`).
- `django_strawberry_framework/scalars.py:86-88` — drop the `For 0.0.6,` version-anchor prefix on the suppression-block explanatory comment and re-name the trigger inline (`Until WIP-ALPHA-020-0.0.7 lands, the deprecation is suppressed at the definition site so consumers importing django_strawberry_framework see no warning.`). The new wording reads continuous across releases that ship before WIP-ALPHA-020-0.0.7. Line count grew by one (86-87 → 86-88) because the longer sentence wraps under the 110-column limit.

### Per-finding dispositions

- Low 1 (L1, stale TODO anchor in module docstring): Accepted-and-edited. Anchor updated to `TODO-ALPHA-028` per Worker 1's recommendation; KANBAN-check grep confirms the corrected anchor maps to the `Upload` card.
- Low 2 (L2, "For 0.0.6, ..." version anchor in suppression-block comment): Accepted-and-edited. Re-worded to "Until WIP-ALPHA-020-0.0.7 lands, ..." per Worker 1's recommendation; the trigger condition is already named two lines above at `scalars.py:83`, so re-stating it inline keeps the comment correct under any future release that ships before the warning-free design.

### Validation run

- `uv run ruff format .` — pass (`118 files left unchanged`)
- `uv run ruff check --fix .` — pass (`All checks passed!`)

### Notes for Worker 3

The two Lows are localised to non-adjacent lines in `scalars.py` and do not interact. Logic surface unchanged; no tests touched. Comment-pass edits batched into the consolidated single-spawn under worker-2.md's "All Lows are explicitly forward-looking per Worker 1's own prose" / "single trivially-localised docstring sentence with no logic change" criteria — both Lows are pure documentation drift with Worker 1's recommended wording quoted verbatim in the artifact.

---

## Changelog disposition

### State

`Not warranted`.

### Reason

Both edits are pure documentation-only changes (a KANBAN anchor correction in the module docstring and a version-anchor rewording in an internal explanatory comment). No consumer-visible behavior changes; no public symbol added, removed, or re-typed; no error message reshaped. `AGENTS.md` line 21 reads "Do not update CHANGELOG.md unless explicitly instructed", and the active plan `docs/review/review-0_0_7.md` is silent on changelog authorization for this cycle. The 0.0.7 cycle precedent chain now spans six prior `Not warranted` dispositions (`_django_patches.md`, `apps.md`, `conf.md`, `exceptions.md`, `list_field.md`, `registry.md`) — all internal-only or documentation-only landings without CHANGELOG entries.

### What was done

No `CHANGELOG.md` edit. The two doc-only edits land in `scalars.py` only; the `0.0.7` CHANGELOG section is unchanged.

### Validation run

- `uv run ruff format .` — pass (`118 files left unchanged`)
- `uv run ruff check --fix .` — pass (`All checks passed!`)

---

## Verification (Worker 3)

### Logic verification outcome

- High / Medium: none — artifact had no logic findings.
- L1 (stale `TODO-ALPHA-027` anchor in module docstring at `scalars.py:3`): Accepted-and-edited. `git diff -- django_strawberry_framework/scalars.py` shows `TODO-ALPHA-027` → `TODO-ALPHA-028` at line 3 verbatim per Worker 1's recommendation. `grep -n "TODO-ALPHA-028" KANBAN.md` returns `445:### TODO-ALPHA-028-0.0.11 — Upload scalar and file / image field mapping` — corrected anchor maps to the `Upload` card. `grep -n "TODO-ALPHA-027" KANBAN.md` returns `407:### TODO-ALPHA-027-0.0.11 — Mutations + auto-generated Input types` — pre-edit anchor was indeed pointing at the wrong (Mutations) card. Logic surface unchanged.
- L2 (version-anchored `For 0.0.6` wording in suppression-block comment at `scalars.py:86-88`): Accepted-and-edited. Diff shows the `For 0.0.6, the deprecation is suppressed at the definition` line replaced by `Until WIP-ALPHA-020-0.0.7 lands, the deprecation is suppressed at the definition site so consumers importing django_strawberry_framework see no warning.` — Worker 1's recommended wording quoted near-verbatim, with the trigger condition re-stated inline (already named two lines above at `scalars.py:83`). Line count grew by one due to the longer sentence wrapping under the 110-column limit. Logic surface unchanged.

### DRY findings disposition

`_with_strawberry_compat(definition_fn)` defer carried forward unchanged. Single-grep trigger condition preserved at the head of the artifact (a second `strawberry.scalar(...)` call in this file); WIP-ALPHA-020-0.0.7 supersedes the defer entirely. No DRY action this cycle.

### Temp test verification

None used. Both findings are localised single-line documentation edits with no behavior surface; reading the live source diff was sufficient.

### Verification outcome

`cycle accepted; verified` — sets top-level `Status: verified` AND marks the checklist box.

- `git diff -- django_strawberry_framework/scalars.py` confirms only L1 (line 3 anchor) + L2 (lines 86-88 comment rewording) sites touched. No logic edits.
- `git diff -- CHANGELOG.md` empty — matches the artifact's `Not warranted` disposition.
- Changelog disposition cites both AGENTS.md ("Do not update CHANGELOG.md unless explicitly instructed") and the active plan `docs/review/review-0_0_7.md`'s silence on changelog authorization. Two-citation bar cleared; the additional six-prior-`Not warranted`-cycles precedent strengthens but is not load-bearing.
- "Internal-only" framing honest: both edits are pure documentation (a KANBAN anchor swap in the module docstring and a version-anchor rewording in an internal explanatory comment) — no public-API surface change, no consumer-visible behavior delta.
- `uv run ruff format --check .` — pass (`118 files already formatted`).
- `uv run ruff check .` — pass (`All checks passed!`).
