# Review: `django_strawberry_framework/optimizer/_context.py`

Status: verified

## DRY analysis

- **Existing patterns reused.** The five `DST_OPTIMIZER_*` constants (lines 34-38) are the single source of truth for the optimizer's context-key namespace and are correctly imported (not redefined) at every write site (`optimizer/extension.py:46-51`, with stash calls at `optimizer/extension.py:619-628`) and read site (`types/resolvers.py:31-38`, with reads at `types/resolvers.py:57-61, 133, 145`). The two helpers `get_context_value` and `stash_on_context` are the single entry points for read/write — `types/resolvers.py:37` aliases the read helper as `_get_context_value`, and `optimizer/extension.py:54` aliases the write helper as `_stash_on_context` with a deliberate test-compatibility re-export (`optimizer/extension.py:67`).
- **New helpers a fix might justify.** None. The two helpers already encapsulate the full read/write dispatch; the constants centralize the key namespace. The module is the DRY landing zone for the rest of the optimizer/resolver hand-off and does not itself call anything that would justify a further helper.
- **Duplication risk in the current file.** None at the file level. The two helpers are deliberately *parallel* (dispatch order mirrors each other per docstring lines 48-51 and 88-90); the parallelism is correctness-load-bearing, not a near-copy DRY violation. The `isinstance(context, dict)` test is repeated twice in `get_context_value` (lines 73 and 78) and twice in `stash_on_context` (line 117 only; the second call site moved to the unconditional tail), which is the minimal shape needed for the dict-first/object-fallback dispatch. No repeated string literals (per shadow overview "Repeated string literals: None"). No `# noqa` markers, no TODOs.

## High:

None.

## Medium:

None.

## Low:

### `get_context_value` dict branch silently skips `getattr` attribute fallback

For non-`dict` contexts the read helper tries `getattr` first then falls through to `__getitem__` (lines 73-80). For `dict` contexts it goes straight to `context.get(key, default)` (line 79) and never consults attribute access. The asymmetry is *intentional and correct* per the module's read/write symmetry contract (the write helper routes `dict` through `__setitem__`, so a value stashed via this module's helpers is always retrievable via the same branch). The risk is purely external: if a future caller mutates a dict-typed context with `setattr` *outside* `stash_on_context` (e.g. consumer code populating its own state via attribute access on a `Box`-style dict subclass before passing the context in), the read helper will not see those values. This is not a bug today — no in-package call site does that — but the docstring (lines 53-57) describes the dict branch as "matches Strawberry's normal usage" without spelling out the "values stashed by code outside this module via `setattr` on a dict subclass are invisible to the read helper" implication. A one-line docstring clarification at the dict bullet would close the gap without changing behavior.

```django_strawberry_framework/optimizer/_context.py:71:82
    if context is None:
        return default
    if not isinstance(context, dict):
        val = getattr(context, key, _MISSING)
        if val is not _MISSING:
            return val
    try:
        if isinstance(context, dict):
            return context.get(key, default)
        return context[key]
    except (TypeError, KeyError, AttributeError):
        return default
```

### Filename prefix vs the rest of `optimizer/`

The leading underscore on `_context.py` signals "private to the optimizer subpackage", which is correct — both production consumers import via fully-qualified `from ..optimizer._context import …` (`types/resolvers.py:31`, `optimizer/extension.py:46`). No `optimizer/__init__.py` re-export exists today, and none should (the helpers are an inter-module implementation detail, not a public API). The file is the *only* module in `optimizer/` whose name starts with a leading underscore, so the convention is currently a sample of one. Worth flagging at the **folder pass** (`rev-optimizer.md`) whether the convention should be applied to any other implementation-detail-only module in the same folder, or whether a single underscore-prefixed file is the right shape for an otherwise-public subpackage. No local change here; folder-pass follow-up only.

```django_strawberry_framework/optimizer/_context.py:1:1
"""Shared context read/write helpers for optimizer ↔ resolver hand-off.
```

## What looks solid

- Static helper ran cleanly per the mandatory `optimizer/` rule. Two symbols, one control-flow hotspot (`stash_on_context` at 52 lines / 6 branches — branchy but every branch is exercised by a dedicated test; see test inventory below). No Django ORM markers beyond docstring/constant mentions of `dst_optimizer_*` and the word "only". No repeated string literals across the file. No TODOs.
- **Constants live with the helpers that consume them.** The five `DST_OPTIMIZER_*` literals are defined exactly once (lines 34-38) and every in-package consumer imports the symbol, not the bare string. `grep '"dst_optimizer' django_strawberry_framework/optimizer/extension.py django_strawberry_framework/types/resolvers.py` returns zero hits — no drifted literal anywhere in production code. This is the textbook "name the magic string once, import it everywhere" shape.
- **Sentinel discipline for `get_context_value`.** Using a private `_MISSING = object()` sentinel (line 40) to distinguish "attribute absent" from "attribute explicitly stashed as `None`" is the right call — a naive `getattr(context, key, None) or context[key]` would mis-handle an intentionally-stashed `None`. The sentinel is module-private (no `__all__`, leading-underscore name).
- **Branch coverage is comprehensive.** Every dispatch branch in both helpers has a dedicated test in `tests/optimizer/test_extension.py`: `test_plan_stashed_on_dict_context` (line 2269), `test_stash_on_dict_subclass_writes_mapping_before_attributes` (line 2281), `test_stash_on_non_dict_mapping_reads_correctly` (line 2303), `test_get_context_value_swallows_attribute_error_from_getitem` (line 2331), `test_stash_on_none_context_is_silent` (line 2354), `test_plan_stashed_on_object_context_unit` (line 2364), `test_stash_on_read_only_mapping_is_silent` (line 2376), `test_stash_falls_back_to_setitem_on_typeerror` (line 2397), `test_stash_on_immutable_dict_subclass_is_silent` (line 2417), and the negative-coverage pin `test_stash_does_not_swallow_unexpected_exceptions_from_setitem` (line 2443) that locks the `except (TypeError, AttributeError)` tuple to exactly two error classes — a `RuntimeError` from a custom mapping is intentionally NOT swallowed. This last test is the kind of "narrow exception tuple" pin that prevents future drift toward a bare `except Exception:` that would silently lose stashes.
- **Read/write symmetry is documented and load-bearing.** Both docstrings explicitly call out that the dispatch order mirrors the other helper (lines 48-51 and 88-90), and the dict-first decision is explained as a "guard *around* `setattr`, not a parallel try/except" with the rationale (lines 108-113). Future maintainers reading the file will understand *why* the parallelism cannot be refactored away.
- **No request-scope / contextvar / thread-safety surface.** Despite the worker-1 prompt's concern about "request-scope state" and "contextvars vs threadlocals", this module is genuinely pure: it has no module-level mutable state, no `contextvars.ContextVar`, no `threading.local`, no caches, no registries. Every read and write is on the caller-supplied `context` object. The five `DST_OPTIMIZER_*` constants and `_MISSING` are module-level but are immutable strings / a sentinel `object()` — no async or thread hazards. Import-time side-effects: none beyond constant initialization. The "centralizes the dispatch" claim in the module docstring (lines 14-17) is accurate.
- **Defensive-coerce posture is documented.** The module docstring (lines 19-27) explicitly contrasts the "absent-or-None is legitimate upstream" stance taken in the optimizer with the "validate consumer input" stance taken in `conf.py`. Cross-module invariant prose lives in two places (here and `conf.py`); the present file correctly stays local to its own posture.
- **Reflective-access audit (mandated by REVIEW.md).** The shadow overview lists four sites of interest: `isinstance(context, dict)` at lines 73, 78, 117 — all narrow type guards with no default to mask anything; `getattr(context, key, _MISSING)` at line 74 — uses a sentinel rather than `None`, which is the correct shape; `setattr(context, key, value)` at line 119 — wrapped in `try` with the explicitly-documented `(AttributeError, TypeError)` tuple covering both `__slots__` classes and frozen dataclasses. None of the four are shape-contract bugs; all four are deliberately narrow.

### Summary

`_context.py` is the optimizer subpackage's single source of truth for the read/write contract against `info.context`. The five `DST_OPTIMIZER_*` constants and two helpers are the textbook "name the magic string once, centralize the dispatch once" shape, and every production consumer imports rather than redefines. No High or Medium findings. Two Low items: a minor docstring gap on the dict-branch read asymmetry (purely descriptive, not behavioral), and a folder-pass follow-up to decide whether the `_context.py` underscore convention applies to any other implementation-detail module in `optimizer/`. Test coverage spans every dispatch branch and includes a negative pin against an over-broad `except` — this file is one of the better-pinned modules in the package and should serve as the reference pattern for "narrow exception tuples on reflective writes".

---

## Fix report (Worker 2)

### Files touched

- None (no logic-pass edit). Both Low findings are non-logic: Low 1 is a docstring clarification owned by the comment pass, Low 2 is a folder-pass follow-up.

### Tests added or updated

- None.

### Validation run

- `uv run ruff format .` — pass (100 files left unchanged).
- `uv run ruff check --fix .` — pass (All checks passed).

### Notes for Worker 3

- No shadow file used during fix.
- Consolidated single-pass shape: the only in-cycle source edit is the docstring clarification (Low 1) recorded under the comment pass below; Low 2 is forwarded to the folder pass with no local edit. Logic + comment + changelog disposition recorded in this single Worker 2 spawn.

---

## Verification (Worker 3)

### Logic verification outcome

- High: None — accepted.
- Medium: None — accepted.
- Low 1: docstring sentence added to `get_context_value`'s dict-branch bullet (5 lines inserted between source lines 56 and 62) naming the read/write symmetry implication that values stashed by code outside this module via ``setattr`` on a dict subclass are intentionally invisible to the dict branch because `stash_on_context` routes ``dict`` writes through ``__setitem__``. Accepted.
- Low 2: forwarded to folder pass `docs/review/rev-optimizer.md` per the artifact instruction. Accepted.

### DRY findings disposition

Worker 1's DRY analysis (the five `DST_OPTIMIZER_*` constants on lines 34-38 are the single source of truth for the optimizer's context-key namespace and every in-package consumer imports the symbol rather than redefining the literal; no in-file duplication) re-verified against the source. The two helpers remain the single entry points for read/write dispatch; the dict-first/object-fallback parallelism between `get_context_value` and `stash_on_context` is correctness-load-bearing rather than near-copy duplication. Accepted.

### Temp test verification

None used — the docstring-only edit does not justify temp-test scaffolding; the existing branch-coverage tests in `tests/optimizer/test_extension.py` enumerated under "What looks solid" already pin every dispatch branch.

### Verification outcome

cycle accepted; verified.

Diff boundary check: `git diff -- django_strawberry_framework/optimizer/_context.py` shows exactly five lines added inside the `get_context_value` docstring's dict-branch bullet — no logic change, no dispatch reorder, no surface change. `git diff -- tests/ CHANGELOG.md` is empty (in-cycle no-op). `git diff -- django_strawberry_framework/optimizer/ django_strawberry_framework/types/` is confined to the docstring insertion above. Validation re-checked: ruff format + ruff check both pass / no changes per the artifact's recorded runs. Sentence style matches the surrounding Google-convention bullet voice, ≤110 chars, and explicitly cites both `setattr` (the failure mode it warns against) and `stash_on_context`'s `__setitem__` routing (the symmetry source).

---

## Comment/docstring pass

### Files touched

- `django_strawberry_framework/optimizer/_context.py` — appended one sentence to `get_context_value`'s docstring inside the dict-branch bullet (around source lines 53-61) naming the read/write symmetry implication: values stashed by code outside this module via `setattr` on a dict subclass are intentionally invisible to the dict branch because the read helper preserves write/read symmetry with `stash_on_context`, which routes `dict` writes through `__setitem__`. No other line in the file was touched. Google docstring convention preserved; line length ≤110.

### Low 1 disposition

- Docstring updated as described above.

### Low 2 disposition

- Forwarded to folder pass `docs/review/rev-optimizer.md` per the artifact instruction. No local edit; the underscore-prefix convention question is folder-scope, not file-scope.

---

## Changelog disposition

### Warranted?

- Not warranted.

### Reason

- The cycle's only source change is a one-sentence docstring clarification on an existing intentional behavior (the read/write symmetry contract was already load-bearing and test-pinned before this cycle; the sentence merely names the implication for future maintainers). No logic, API, behavior, or test surface change. Per `AGENTS.md` ("Do not update CHANGELOG.md unless explicitly instructed.") and the active plan (no changelog authorization for this cycle item), no `CHANGELOG.md` edit was made.

### What was done

- No `CHANGELOG.md` edit. The maintainer may fold the docstring clarification into a future user-visible entry at their discretion.

### Validation run

- `uv run ruff format .` — pass (100 files left unchanged).
- `uv run ruff check --fix .` — pass (All checks passed).

---

## Iteration log
