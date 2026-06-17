# Review: `django_strawberry_framework/optimizer/_context.py`

Status: verified

## DRY analysis

- None — this module *is* the DRY consolidation point. Its module docstring (`_context.py:14-17`) states the intent explicitly: centralizing the object-vs-dict-vs-frozen context dispatch here means a new context shape or new swallow-class lands in one place rather than across `optimizer/extension.py` and `types/resolvers.py`. Both consumers already alias the two helpers (`extension.py:52-62`, `resolvers.py:39-45`) and the five `DST_OPTIMIZER_*` string keys are defined once here and imported everywhere they are used (`extension.py:53-57`, `resolvers.py:40-42`) — zero duplicated literals. The read/write dispatch ladders in `get_context_value` (`_context.py:81-92`) and `stash_on_context` (`_context.py:125-160`) are deliberate mirror images, not accidental near-copies; folding them into one shared "walk the context shapes" helper would fuse a read tail (`__getitem__` + return) with a write tail (`__setitem__` + skip) that have opposite return/exception contracts, so the parallel structure is correct.

## High:

None.

## Medium:

None.

## Low:

None.

## What looks solid

### DRY recap

- **Existing patterns reused.** The five request-scope stash keys are single-sourced as module constants (`_context.py:34-38`) and imported by both the write side (`extension.py:53-57`) and the read side (`resolvers.py:40-42`); no consumer hard-codes the string. The two helpers are the sole context-shape dispatch primitives — `extension.py` and `resolvers.py` import them under `_`-aliases rather than re-implementing object/dict/frozen handling.
- **New helpers considered.** A single unified `_walk_context_shapes(context, key, op)` collapsing both functions was evaluated and rejected: the read path must *return* a value and fall through `getattr`→`__getitem__`, while the write path must *skip silently* and fall through `setattr`→`__setitem__` with a different swallow tuple (`get` catches `TypeError/KeyError/AttributeError`; `stash` catches `TypeError/AttributeError` and deliberately lets `KeyError`/`RuntimeError` surface). Fusing them would require threading op-specific callables and exception tuples through one body — strictly less readable for no line saving.
- **Duplication risk in the current file.** The two `isinstance(context, dict)` checks in `get_context_value` (`_context.py:83,88`) read as a near-repeat but are load-bearing: the first short-circuits the attribute-read branch for dicts, the second routes the shared `try` block to `.get` vs `__getitem__`. The dict-first guard shape is mirrored in `stash_on_context` (`_context.py:127`) by intent (read/write symmetry, documented at `_context.py:51-53` and `_context.py:99-103`), not by copy-paste.

### Other positives

- **Stateless and request-scoped by construction.** Both helpers operate only on the passed-in `info.context` (request-scoped) and the immutable `default` argument. The only module-level state is five `str` constants and the `_MISSING` sentinel (`_context.py:40`), all read-only — identity-checked, never mutated. There is no module-level cache, no `ContextVar`, no mutable default argument, so per-request isolation and thread/async safety hold trivially. Accumulation semantics that *could* race (union-merge across resolvers) correctly live one layer up in `extension.py::_stash_union` (`extension.py:963`), not here.
- **Write/read symmetry is real and pinned.** `stash_on_context`'s dict-first dispatch and `setattr`→`__setitem__` fallback round-trips with `get_context_value`'s `getattr`→`__getitem__` fallback. The non-dict `__slots__`/bridged-mapping round trip is pinned by `tests/optimizer/test_extension.py::test_stash_on_non_dict_mapping_reads_correctly`; the dict-subclass-with-hostile-`setattr` round trip by `::test_stash_falls_back_to_setitem_on_typeerror`.
- **Frozen-context error modes are exhaustively pinned, narrowly scoped.** `MappingProxyType` `TypeError` (`::test_stash_on_read_only_mapping_is_silent`), Django locked-`QueryDict` `AttributeError` on `__setitem__` (`::test_stash_on_immutable_dict_subclass_is_silent`), and the `None` context (`::test_stash_on_none_context_is_silent`) all confirm silent-skip. Critically, `::test_stash_does_not_swallow_unexpected_exceptions_from_setitem` pins that a `RuntimeError` from a guarded mapping is *not* swallowed — the swallow tuple is deliberately minimal, so a genuine programming-error write surfaces rather than silently losing the stash.
- **Read-side `AttributeError`-from-`__getitem__` swallow is pinned.** `::test_get_context_value_swallows_attribute_error_from_getitem` covers the `StrawberryDjangoContext` bridged-item-access shape where a missing key raises `AttributeError` out of `__getitem__`; the read helper returns `default` instead of leaking it. The `_MISSING` sentinel (`_context.py:40-42`) correctly distinguishes an absent attribute from one explicitly stashed as `None`, so a stashed `None` is returned faithfully rather than being re-treated as missing.
- **Comments earn their length.** The inline blocks at `_context.py:131-146` (catch-and-chain vs catch-and-return distinction) and `_context.py:149-159` (exactly which frozen error classes are swallowed and why `KeyError`/`RuntimeError` are not) document non-obvious cross-shape dispatch behavior that the static overview flags as the file's only hotspots. No stale comments, no restating-the-obvious, no TODOs (shadow overview: 0 TODO, 0 ORM markers, 0 repeated literals).

### Summary

`_context.py` is the single, deliberately-DRY dispatch point for reading and writing optimizer hand-off state on Strawberry's polymorphic `info.context` (object / dict / frozen-mapping / `None`). It is stateless, request-scoped, and free of any module-level mutable state or default-argument trap, so request isolation and thread/async safety hold by construction; the only racy semantics (union accumulation) correctly live one layer up in `extension.py`. Every branch of both helpers — including the narrow, intentional swallow tuples and the write/read round-trip across `__slots__`, bridged, and frozen contexts — is pinned by named tests in `tests/optimizer/test_extension.py`. No changes since baseline `14910230`, empty cycle diff. No High/Medium/Low findings; DRY is already at its target shape. No-source-edit cycle (shape #5).

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — 270 files left unchanged.
- `uv run ruff check --fix .` — All checks passed (only the pre-existing COM812-vs-formatter config notice).

### Notes for Worker 3
- No-findings file: all severities `None.`. Empty cycle diff (`git diff HEAD -- django_strawberry_framework/optimizer/_context.py` empty); no changes since baseline `14910230`.
- No GLOSSARY-only fix in scope. The one GLOSSARY reference (`docs/GLOSSARY.md:563`) names the stash *key value* `dst_optimizer_plan`, which equals the `DST_OPTIMIZER_PLAN` constant value — accurate, not stale.
- Helpers fully test-pinned in `tests/optimizer/test_extension.py` (see `### Other positives` for the per-branch mapping).

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern.

No comment or docstring changes warranted. The module/function docstrings and the two inline blocks (`_context.py:131-146`, `_context.py:149-159`) are accurate, non-stale, and document genuinely non-obvious cross-shape dispatch behavior; the shadow overview reports 0 TODO anchors and 0 stale-comment candidates.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern.

Not warranted — no source edit was made; the cycle is review-only. Per AGENTS.md ("Do not update CHANGELOG.md unless explicitly instructed") and the active plan (`docs/review/review-0_0_10.md`) carrying no changelog directive for this item, no changelog entry is warranted.

---

## Verification (Worker 3)

### Logic verification outcome

No-source-edit cycle (shape #5). All severities `None.`; nothing to address or reject. Independently confirmed the no-findings premise holds:

- **Empty cycle diff.** `git diff HEAD -- django_strawberry_framework/optimizer/_context.py` is empty. The artifact's baseline string `14910230` predates concurrent maintainer commits (HEAD is now `5724429c`), but the file is genuinely unchanged: `git log -1 -- _context.py` = `e6389922` ("Make all .py source ASCII"), older than both, and `git diff 14910230 HEAD -- _context.py` is also empty. Baseline-SHA drift is cosmetic, not a stale-artifact rejection.
- **Stateless / request-scoped (verified).** Module-level state is exactly five `str` constants (`_context.py:34-38`) + `_MISSING` sentinel (`_context.py:40`). No `ContextVar`, no module cache, no mutable default argument (`default: Any = None`). Both helpers read/write only the passed-in `context` and the immutable `default`. Per-request isolation and thread/async safety hold by construction.
- **Sentinel identity-checked, never mutated (verified).** `_MISSING = object()` is consumed solely via identity (`val is not _MISSING` at `:85`, implicit via fall-through). Grep shows no rebind/mutation. It correctly distinguishes an absent attribute from a stashed `None`.
- **Swallow tuples genuinely exclude RuntimeError (verified).** Read path catches `(TypeError, KeyError, AttributeError)` (`:91`); write paths catch `(AttributeError, TypeError)` (`:131`) and `(TypeError, AttributeError)` (`:149`). None include `RuntimeError`. Directly pinned by `tests/optimizer/test_extension.py::test_stash_does_not_swallow_unexpected_exceptions_from_setitem` (`:3287`): a `GuardedMapping.__setitem__` raising `RuntimeError("guarded write rejected")` is asserted to propagate via `pytest.raises(RuntimeError, ...)`. The narrow-swallow claim is falsifiable and holds.
- **Constants single-sourced (verified).** `grep -rn 'DST_OPTIMIZER_*\s*='` over the package returns only the five definitions in `_context.py:34-38` — zero duplicate literals. Read side imports `DST_OPTIMIZER_{FK_ID_ELISIONS,PLANNED,STRICTNESS}` + `get_context_value as _get_context_value` (`types/resolvers.py:39-45`); write side imports all five + both helpers under `_`-aliases (`optimizer/extension.py:52-63`). Both consumers alias the helpers rather than re-implementing object/dict/frozen dispatch.

### DRY findings disposition

DRY analysis is correct: this module IS the consolidation point (module docstring `_context.py:14-17`). The proposed `_walk_context_shapes` fusion was evaluated and rightly rejected — read tail (`__getitem__`+return, 3-class catch) and write tail (`__setitem__`+skip, 2-class catch) have opposite return/exception contracts; fusing them threads op-specific callables + exception tuples through one body for no line saving. The parallel structure is intentional, documented (`:118-123`), and load-bearing. Nothing carried forward.

### Temp test verification

- None. The RuntimeError-exclusion, sentinel, and round-trip claims are already pinned by named tests in `tests/optimizer/test_extension.py` (all seven cited pins grep-confirmed at lines 3147/3175/3198/3220/3241/3261/3287); no temp test needed.

### Shape #5 checks

1. `git diff --stat "$CYCLE_BASELINE" -- django_strawberry_framework/ tests/ docs/GLOSSARY.md CHANGELOG.md` shows only `management/commands/{_imports.py,export_schema.py,inspect_django_type.py}` + `tests/management/test_imports.py`. Those hunks attribute to the CLOSED sibling cycle `rev-management__commands.md` (Status: verified; `[x]` at `review-0_0_10.md:90`) — not a rejection trigger. `_context.py` (this cycle) has an empty diff; "Files touched: None" holds against the file's own diff.
2. Each Worker 2 section opens with `Filled by Worker 1 per no-source-edit cycle pattern.` — present.
3. All severities `None.`; no Lows to phrase/forward; no GLOSSARY-only fix. The one GLOSSARY reference (`docs/GLOSSARY.md:563`) names the key *value* `dst_optimizer_plan`, accurate.
4. Changelog `Not warranted` with both citations (AGENTS.md + active-plan silence); `git diff -- CHANGELOG.md` empty. Internal-only framing matches scope (zero diff).
5. `uv run ruff format --check` = already formatted; `uv run ruff check` = All checks passed (only the pre-existing COM812-vs-formatter notice).

### Verification outcome

`cycle accepted; verified` — sets top-level `Status: verified` AND marks the `optimizer/_context.py` checklist box in `docs/review/review-0_0_10.md`.
