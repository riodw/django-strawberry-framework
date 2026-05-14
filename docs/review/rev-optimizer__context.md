# Review: `django_strawberry_framework/optimizer/_context.py`

Status: verified

## DRY analysis

- Existing patterns reused: `_context.py` centralizes context keys and the read/write helpers used by the optimizer write side and resolver read side; `DjangoOptimizerExtension._publish_plan_to_context` calls `stash_on_context` for every optimizer sentinel at `django_strawberry_framework/optimizer/extension.py:448-466`, while relation resolvers call `get_context_value` for FK elision and strictness at `django_strawberry_framework/types/resolvers.py:55-61` and `django_strawberry_framework/types/resolvers.py:127-144`.
- New helpers a fix might justify: none. The single responsibility already belongs in `stash_on_context`; the fix should make its dispatch order match `get_context_value` instead of adding another abstraction.
- Duplication risk in the current file: the read/write shape dispatch is duplicated and has drifted. `get_context_value` deliberately handles `dict` before attribute access at `django_strawberry_framework/optimizer/_context.py:50-56`, but `stash_on_context` tries `setattr` before mapping assignment at `django_strawberry_framework/optimizer/_context.py:76-82`.

## High:

None.

## Medium:

### Dict-subclass contexts can stash sentinels somewhere resolvers never read

`get_context_value` documents and implements a load-bearing rule: `dict` subclasses that also expose attribute access must be read through the mapping branch. `stash_on_context` does the opposite by trying `setattr` first and returning on success. For a `dict` subclass with separate attribute storage, the optimizer publishes `dst_optimizer_plan`, FK-id elisions, planned resolver keys, and strictness sentinels as attributes, but resolver reads then use `context.get(...)` and miss them. That disables the read-side hand-off for exactly the mapping shape the read helper calls out, which can turn FK-id elision back into lazy relation access and can make strictness fail to observe planned/unplanned state. Make the write dispatch mirror the read dispatch: handle `dict` instances with `context[key] = value` before the attribute path, then keep the existing object and frozen-context fallbacks. Add a focused test with a `dict` subclass whose `__setattr__` stores attributes separately, asserting `stash_on_context` writes the mapping key and `get_context_value` can read it.

```django_strawberry_framework/optimizer/_context.py:50:82
    # Dispatch order matters: ``dict`` is checked before the ``getattr``
    # fallback so that a ``dict`` subclass that *also* exposes attribute
    # access (e.g., a ``Box``-style mapping) takes the mapping branch,
    # which matches Strawberry's normal usage.  Do not reverse the order.
    if isinstance(context, dict):
        return context.get(key, default)
    return getattr(context, key, default)


def stash_on_context(context: Any, key: str, value: Any) -> None:
    ...
    try:
        setattr(context, key, value)
        return
    except (AttributeError, TypeError):
        pass
    try:
        context[key] = value
```

## Low:

None.

## What looks solid

- The helper was run before review because `_context.py` lives under `optimizer/`; it reported no control-flow hotspots and no repeated string literals.
- The context key literals are centralized in this module and imported by both optimizer publishing and resolver consumption paths.
- Frozen or read-only context write failures are intentionally narrow: `TypeError` from item assignment is skipped, while unexpected custom mapping errors are allowed to surface.

### Summary

The module is small and has the right ownership boundary, but the write-side dispatch order has drifted from the read-side contract. Fixing `stash_on_context` to treat `dict` instances as mappings first keeps the optimizer/resolver hand-off coherent without adding new helpers.

---

## Fix report (Worker 2)

### Files touched

- `django_strawberry_framework/optimizer/_context.py` — changed `stash_on_context` so `dict` instances write through mapping assignment before the attribute path, matching `get_context_value`.
- `tests/optimizer/test_extension.py` — added focused coverage for a dict subclass with separate attribute storage.

### Tests added or updated

- `tests/optimizer/test_extension.py::test_stash_on_dict_subclass_writes_mapping_before_attributes` — proves `stash_on_context` writes the mapping key, avoids separate attribute storage, and `get_context_value` reads the same value.

### Validation run

- `uv run ruff format .` — passed; 92 files left unchanged.
- `uv run ruff check --fix .` — passed.
- `uv run pytest tests/optimizer/test_extension.py::test_stash_on_dict_subclass_writes_mapping_before_attributes` — assertions passed, then exited nonzero because the single-test run hit the repo-wide `fail_under=100` coverage gate.
- `uv run pytest tests/optimizer/test_extension.py::test_stash_on_dict_subclass_writes_mapping_before_attributes --no-cov` — passed, 1 test.

### Notes for Worker 3

Static helper run: `python scripts/review_inspect.py django_strawberry_framework/optimizer/_context.py --output-dir docs/review/shadow --stdout`. Cite original source line numbers, not shadow line numbers.
Logic note: `stash_on_context` now preserves the existing narrow `TypeError` skip for mapping assignment and still surfaces non-`TypeError` custom mapping failures. The existing `stash_on_context` docstring now describes the old `setattr`-first order; I left that for the comment/docstring pass per Worker 2 process.

---

## Verification (Worker 3)

### Logic verification outcome

The Medium finding is addressed. `stash_on_context` now checks `isinstance(context, dict)` before the attribute-write path, so dict subclasses use mapping assignment and line up with `get_context_value`'s mapping-first read order. The object-context and frozen-context fallbacks remain scoped as before.

Worker 2 used a shadow helper output. Original source-file line numbers and this artifact's line references remain canonical; shadow line numbers were not used for verification feedback.

### DRY findings disposition

Accepted. No new helper is needed because the single responsibility already belongs in `stash_on_context`; the fix removes the read/write dispatch drift without adding another abstraction or parallel code path.

### Temp test verification

No temp tests used.

Permanent focused coverage was added in `tests/optimizer/test_extension.py::test_stash_on_dict_subclass_writes_mapping_before_attributes`. It proves that a dict subclass with separate attribute storage receives the optimizer sentinel in the mapping, does not receive a separate attribute write, and is readable through `get_context_value`.

Validation run by Worker 3:

- `uv run pytest tests/optimizer/test_extension.py::test_stash_on_dict_subclass_writes_mapping_before_attributes --no-cov` — passed, 1 test.

### Verification outcome

logic accepted; awaiting comment pass

The logic pass is accepted, but the `stash_on_context` docstring still describes `setattr` as the primary path and dict handling as a fallback after `setattr` raises. That comment/docstring lifecycle must be updated before this cycle can advance to changelog disposition or final verification.

---

## Comment/docstring pass

### Files touched

- `django_strawberry_framework/optimizer/_context.py` — updated `stash_on_context`'s docstring to describe the final accepted dispatch order: dict contexts write through mapping assignment first, object contexts use attributes, mapping-like fallback remains available, and read-only assignment failures are skipped narrowly.

### Tests/comments reviewed

- `tests/optimizer/test_extension.py` — reviewed the new dict-subclass test docstring/comments; no stale wording found.

### Validation run

- `uv run ruff format .` — passed; 92 files left unchanged.
- `uv run ruff check --fix .` — passed.

### Notes for Worker 3

The logic was not changed in this pass. Changelog disposition is not reached yet, so `CHANGELOG.md` and the `## Changelog disposition` section remain untouched.

---

## Changelog disposition

Changelog edit: warranted.

Reason: the accepted fix changes optimizer context hand-off behavior for `dict` subclasses. That can affect whether
published optimizer sentinels are visible to resolver-side reads, so it is release-note-worthy even though the changed
surface is an internal helper.

What was done: no `CHANGELOG.md` edit was made. `AGENTS.md` forbids changelog updates unless explicitly instructed, and
the active review plan did not authorize editing `CHANGELOG.md` for this cycle.

---

## Verification follow-up (Worker 3 comment/docstring pass)

### Comment/docstring verification outcome

comments accepted; awaiting changelog disposition

The updated `stash_on_context` docstring now describes the final accepted behavior: dict contexts write through mapping assignment first, object contexts use attributes, non-dict mapping-like objects remain on the fallback path, and read-only assignment failures are skipped narrowly. The new test docstring is scoped to the review artifact and does not describe stale behavior.

Validation run by Worker 3:

- `uv run pytest tests/optimizer/test_extension.py::test_stash_on_dict_subclass_writes_mapping_before_attributes --no-cov` — passed, 1 test.

At that pass, top-level `Status:` remained `fix-implemented` because `## Changelog disposition` was still pending. The active-plan checklist item was not marked.

---

## Iteration log

cycle accepted; verified

Final Worker 3 verification accepted the completed cycle after changelog disposition was recorded. Logic, DRY, comments/docstrings, focused validation, and changelog handling are all complete. No `CHANGELOG.md` edit was made because `AGENTS.md` forbids changelog updates unless explicitly instructed, and this cycle did not authorize one.

Final validation run by Worker 3:

- `uv run pytest tests/optimizer/test_extension.py::test_stash_on_dict_subclass_writes_mapping_before_attributes --no-cov` — passed, 1 test.

---

## Coverage follow-up (re-pass)

### Findings

The accepted two-branch shape introduced a duplicate `except TypeError: return` handler on the new dict path that was not exercised by any existing or added test. Worker 2's focused validation only ran with `--no-cov`; running the full suite under the package's `fail_under = 100` gate surfaced one missing line (the `return` inside the new dict path's `except TypeError`), dropping coverage to 99.93%. Pre-existing `MappingProxyType` fixtures continued to cover the bottom-path handler but did not flow through the new top-path handler because `MappingProxyType` is not a `dict` subclass.

### Fix

`stash_on_context` was restructured so the dict-first decision is expressed as a *guard around* the `setattr` block (skip `setattr` for `dict` instances) instead of as a parallel `try` / `except` arm. Observable behavior is unchanged:

- `dict` instances (including subclasses with separate attribute storage) bypass `setattr` and write directly through `__setitem__`, matching `get_context_value`'s mapping-first dispatch.
- Non-`dict` contexts still try `setattr` first and fall back to `__setitem__` for mapping-like objects.
- Frozen contexts (`MappingProxyType`, frozen dataclasses, `pydantic` `frozen=True` models, and any frozen `dict` subclass that raises `TypeError` on `__setitem__`) all flow through one shared `except TypeError` handler at the bottom of the function.

The consolidation removes the duplicate handler so the existing `MappingProxyType` test coverage subsumes the frozen-`dict`-subclass case without a new fixture.

### Files touched

- `django_strawberry_framework/optimizer/_context.py` — consolidated the two `except TypeError: return` arms; updated `stash_on_context` docstring with an implementation note describing the guard-and-shared-tail shape and the coverage rationale.

### Validation run

- `uv run ruff format django_strawberry_framework/optimizer/_context.py` — passed.
- `uv run ruff check django_strawberry_framework/optimizer/_context.py` — passed.
- `uv run pytest` (full suite, default coverage gate) — 533 passed, 1 skipped; package coverage 100.00% (`django_strawberry_framework/optimizer/_context.py` now reports 26/26 statements, 0 miss).

### Disposition

cycle accepted; verified. Logic, DRY, comments/docstrings, focused validation, full-suite validation, and changelog handling are now complete. No `CHANGELOG.md` edit was made for the same `AGENTS.md` reason as the original cycle.
