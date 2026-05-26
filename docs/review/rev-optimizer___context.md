# Review: `django_strawberry_framework/optimizer/_context.py`

Status: verified

## DRY analysis

- **None — the file is already the canonical DRY shape it was extracted to be.** The five `DST_OPTIMIZER_*` constants and the two helpers `get_context_value` / `stash_on_context` are the consolidation of what previously lived (per the module docstring at `_context.py:14-17`) in both `optimizer/extension.py` and `types/resolvers.py`; both consumer sites now import from here (`optimizer/extension.py:47-56`, `types/resolvers.py:35-42`). The intentional "guard-around-setattr-then-shared-mapping-tail" shape inside `stash_on_context` (`_context.py:120-141`) is explicitly documented at `_context.py:113-118` as a chosen consolidation against a duplicated `try`/`except` per branch — the comment doubles as the DRY decision record.

## High:

None.

## Medium:

None.

## Low:

### `DST_OPTIMIZER_PLAN` and `DST_OPTIMIZER_LOOKUP_PATHS` are write-only constants — the read symmetry the module docstring promises is incomplete

`_context.py:34` (`DST_OPTIMIZER_PLAN`) and `_context.py:37` (`DST_OPTIMIZER_LOOKUP_PATHS`) are exported from this module, written by `extension.py:671` and `extension.py:679` respectively, and then never read back via `get_context_value`. Every other constant in the file has a documented read site: `DST_OPTIMIZER_FK_ID_ELISIONS` is read at `types/resolvers.py:61-65`, `DST_OPTIMIZER_PLANNED` at `types/resolvers.py:138`, `DST_OPTIMIZER_STRICTNESS` at `types/resolvers.py:150`. The module docstring at `_context.py:1-3` frames the file as "Shared context read/write helpers for optimizer ↔ resolver hand-off" — for two of the five keys, only the write side is internal; consumers reach in via attribute access (`tests/test_list_field.py:751,882`; `tests/optimizer/test_extension.py:205-206,320,360`; `tests/optimizer/test_relay_id_projection.py:55,116,198`). This is consistent with `docs/GLOSSARY.md:462` ("FK-id elisions are stashed on `info.context.dst_optimizer_plan` for introspection") and `docs/GLOSSARY.md:984` ("Planned resolver keys and lookup paths are stashed on `info.context` for introspection during strictness incidents") — both are introspection-only stashes, not internal hand-offs.

Trigger-gated deferral: defer until a second consumer of either constant lands inside the package (a debug helper, a strictness reporter, or anything not a test reading `ctx.dst_optimizer_plan` directly). At that point, the read site either (a) graduates to `get_context_value(context, DST_OPTIMIZER_PLAN)` and the module docstring's "read/write" framing becomes load-bearing for that constant too, or (b) the constant is downgraded to a private-write-only module symbol with a comment naming the introspection contract. Both are valid refactors; the current shape is fine because external introspection by attribute access is the contract.

### Module-level `_MISSING: Any = object()` sentinel could narrow its annotation for self-documentation

`_context.py:40` types `_MISSING` as `Any` and documents the role in the docstring at lines 41-42. The sentinel is used at one read site (`_context.py:79-80`) for an attribute-absent check, and `Any` is correct because `getattr(context, key, _MISSING)` accepts any default. The trade-off here is between (a) the `Any` shape that matches `getattr`'s signature noise and (b) a narrower `object` annotation that signals "intentionally a sentinel object, not a value". The sibling pattern in `optimizer/extension.py:603` (lazy import comment) shows the package prefers self-documenting annotations when the role is non-obvious; here, the docstring already carries that load, so the narrower annotation is cosmetic-only. Defer until a future cycle adds a second sentinel to this module — at that point a shared `_Sentinel = object` typing pattern becomes worth introducing across both sentinels.

## What looks solid

### DRY recap

- **Existing patterns reused.** The module is itself the canonical extraction site for what previously lived in two places. `optimizer/extension.py:54-56` imports `stash_on_context as _stash_on_context` to preserve the underscore-prefixed name tests already import; `types/resolvers.py:40-42` imports `get_context_value as _get_context_value` for the same name-stability reason. Both aliases preserve backwards compatibility without forcing test churn — that is the canonical "import-alias preserves API surface during a shared-helper extraction" pattern documented at `extension.py:63-67`.
- **New helpers considered.** A `_get_or_default(context, key, default)` wrapper that bundles the `None` short-circuit + `getattr` + `__getitem__` triple was considered and rejected — the triple is `get_context_value` itself; pulling it out would just rename the function. The "raise-only-the-narrow-set" exception catch (`TypeError`, `KeyError`, `AttributeError`) at `_context.py:86` was considered for extraction to a constant tuple; rejected because the comment at `_context.py:131-140` carries the load-bearing rationale for the exact set, and pulling it to a constant would split the rationale from the catch site.
- **Duplication risk in the current file.** The two `isinstance(context, dict)` checks in `get_context_value` at lines 78 and 83 are intentional sibling branches — the first gates the `getattr` short-circuit on non-dict contexts; the second routes the unified mapping-read path through `dict.get` instead of `__getitem__`. Collapsing them into a single dispatch would force one of the two branches to drop a documented behavior (the `getattr` short-circuit's documented note at lines 52-54 about subclass attribute access, or the `dict.get`-vs-`__getitem__` distinction at lines 53-61 about write/read symmetry with `stash_on_context`). The duplicate `isinstance(context, dict)` is not duplicate logic; it is a two-stage dispatch with one shared mapping-read tail.

### Other positives

- **Thread/process safety.** All five `DST_OPTIMIZER_*` constants at lines 34-38 are module-level immutable strings — safe to read concurrently without locking. The module imports nothing besides `typing.Any` and has no module-level mutable state beyond the `_MISSING` sentinel (an immutable object identity, used only as a default in `getattr`). No `ContextVar` here — the per-request state lives on `info.context` itself, owned by Strawberry / the consumer; the helpers only mediate read/write, never store.
- **Narrow-and-documented exception catches.** Both helpers catch a precisely enumerated set of exceptions (`get_context_value`: `TypeError`, `KeyError`, `AttributeError` at line 86; `stash_on_context`: `AttributeError`, `TypeError` at lines 126 and 130). The `stash_on_context` mapping-write comment at lines 131-140 records exactly which classes are NOT swallowed (`KeyError` from a guarded mapping, `RuntimeError` from a custom TypedDict-like wrapper) and why — this is the discriminator that prevents the "broad `except Exception`" anti-pattern. The `tests/optimizer/test_extension.py:2590-2609` test `test_stash_does_not_swallow_unexpected_exceptions_from_setitem` pins that exact narrow-catch contract.
- **Sentinel discrimination correctness.** The `_MISSING` sentinel at `_context.py:40` correctly distinguishes "attribute genuinely absent" from "attribute explicitly set to `None`" — if a consumer stashed `None` on the context as a meaningful absence marker, `get_context_value` returns it via the `getattr` branch at lines 79-81 instead of falling through to the `__getitem__` path; this matches the docstring at lines 41-42 ("distinguish a missing attribute from an attribute that was explicitly stashed as ``None``"). Using the module-level sentinel rather than re-allocating per call is also correct — identity comparison via `is not _MISSING` at line 80 is what makes the discrimination unforgeable.
- **Read/write symmetry pins.** The four `test_stash_*` / `test_get_context_value_*` tests at `tests/optimizer/test_extension.py:2416-2609` exercise every documented dispatch shape: plain `dict`, dict subclass with hostile `__setattr__`, non-dict mapping with `__slots__`, frozen `MappingProxyType`, immutable `dict` subclass that raises `AttributeError` from `__setitem__`, bridged-`__getitem__`/`__getattribute__` shape (Strawberry-django's `StrawberryDjangoContext`), and the `None` short-circuit. The `test_stash_does_not_swallow_unexpected_exceptions_from_setitem` test additionally pins the narrow-catch contract by feeding a `RuntimeError`-raising subclass and asserting the exception escapes. Coverage is complete against the documented context shapes.
- **Module docstring as design record.** The 28-line module docstring at lines 1-28 enumerates the four context shapes (`None`, object, dict, frozen), names the consolidation rationale ("a future broadening only has to land in one place"), and frames the defensive-coerce stance against `conf.py`'s opposite stance for consumer-supplied input. This is the canonical "why this file exists" record — the package's docstring discipline at its best.

### Summary

`_context.py` is a tightly-factored, well-tested consolidation of context read/write helpers shared between `optimizer/extension.py` (write side) and `types/resolvers.py` (read side). The five `DST_OPTIMIZER_*` constants are immutable module-level strings (thread-safe by construction); the two helpers correctly mediate four context shapes (`None`, object, dict, frozen) with precisely narrow exception catches that the test suite pins against the documented behaviors. No High or Medium findings: the canonical extraction is already in place, the docstring carries the design rationale, the catches are narrow, and the introspection-stash constants follow the contract documented in `docs/GLOSSARY.md`. Two trigger-gated Lows defer until a second internal consumer of `DST_OPTIMIZER_PLAN` / `DST_OPTIMIZER_LOOKUP_PATHS` lands (or until a second sentinel justifies introducing a shared typing pattern); both are cosmetic-only at this scale and would force premature consolidation if acted on now.

---

## Fix report (Worker 2)

### Files touched
- None — consolidated single-spawn no-op pass. Both Lows are explicitly trigger-gated/forward-looking per Worker 1's own prose ("Trigger-gated deferral: defer until a second consumer..." at line 23, "Defer until a future cycle adds a second sentinel..." at line 27); no in-cycle edit is required.

### Tests added or updated
- None.

### Validation run
- `uv run ruff format .` — 118 files left unchanged
- `uv run ruff check --fix .` — All checks passed
- No focused tests run; per `START.md` the standing rule is formatting only, and this consolidated spawn introduces no source edits.

### Notes for Worker 3
- Shadow file used: `docs/shadow/_context.overview.md` was the Worker 1 reference; not re-consulted this cycle because no source edits were planned.
- No intentionally-rejected findings — both Lows are accepted-but-deferred per Worker 1's verbatim deferral language; the file enters the cycle with zero in-scope edits required.
- Deferred findings and their trigger conditions:
  - **Low 1 (`DST_OPTIMIZER_PLAN` / `DST_OPTIMIZER_LOOKUP_PATHS` write-only constants)** — trigger: a second consumer of either constant lands inside the package (a debug helper, a strictness reporter, or anything not a test reading `ctx.dst_optimizer_plan` directly). At that point either the read site graduates to `get_context_value(context, DST_OPTIMIZER_PLAN)` (and the module docstring's "read/write" framing becomes load-bearing for that constant too) or the constant is downgraded to a private write-only module symbol with a comment naming the introspection contract.
  - **Low 2 (`_MISSING: Any = object()` could narrow to `object`)** — trigger: a future cycle adds a second sentinel to this module, at which point a shared `_Sentinel = object` typing pattern becomes worth introducing across both sentinels.

---

## Comment/docstring pass

### Files touched
- None — both Lows are deferrals, not in-cycle docstring edits. The module docstring at `_context.py:1-28`, the `_MISSING` docstring at `_context.py:41-42`, and the `stash_on_context` mapping-write rationale at `_context.py:113-118` and `_context.py:131-140` all already describe the final approved behavior accurately. No stale comments to remove; no obvious comments to drop; no forward-looking phase/slice labels in the file to retire.

### Per-finding dispositions
- Low 1 (`DST_OPTIMIZER_PLAN` / `DST_OPTIMIZER_LOOKUP_PATHS` write-only constants): **Deferred** — trigger-gated; the module docstring's "Shared context read/write helpers" framing accurately describes the contract for the three already-read constants and remains a correct shape for the two introspection-stash constants whose read side is external attribute access by design (per `docs/GLOSSARY.md:462,984`).
- Low 2 (`_MISSING: Any = object()` could narrow to `object`): **Deferred** — trigger-gated; the docstring at lines 41-42 already carries the role-as-sentinel load that a narrower annotation would only restate.

### Validation run
- `uv run ruff format .` — 118 files left unchanged
- `uv run ruff check --fix .` — All checks passed

### Notes for Worker 3
No comment-pass edits to verify; the artifact's two Lows entered and exited the cycle as Worker 1-authored deferrals.

---

## Changelog disposition

### State
`Not warranted`.

### Reason
Two citations apply per the worker-2.md three-state guidance:

1. **`AGENTS.md` ("Do not update CHANGELOG.md unless explicitly instructed")** — the rule that controls absent an explicit per-cycle authorization.
2. **The active plan `review-0_0_7.md` is silent on changelog authorization for this cycle** — the dispatch prompt names no changelog edit, and the cycle's only artifact-mandated work is a consolidated no-op single-spawn over two trigger-gated Lows. No source edit shipped this cycle means no consumer-visible delta to record.

Additionally, the 0.0.7 precedent chain now eleven cycles deep (rev-_django_patches, rev-apps, rev-conf, rev-exceptions, rev-list_field, rev-registry, rev-scalars, rev-management__commands__export_schema, rev-management__commands, rev-management — all closed `Not warranted`) is the strongest available third leg: every prior consolidated no-op single-spawn in this release closed `Not warranted` and no Worker 3 has overturned that disposition. The chain-length precedent reinforces the two-citation bar above; reversal would require an explicit maintainer instruction in the dispatch prompt to overturn the cumulative pattern.

### What was done
No `CHANGELOG.md` edit.

### Validation run
- `uv run ruff format .` — 118 files left unchanged
- `uv run ruff check --fix .` — All checks passed

---

## Verification (Worker 3)

### Logic verification outcome
- Both Lows are Worker 1-authored deferrals with verbatim trigger phrasing carried into Worker 2's `### Notes for Worker 3` (Low 1 trigger "a second consumer of either constant lands inside the package..." mirrors artifact line 23; Low 2 trigger "a future cycle adds a second sentinel to this module..." mirrors artifact line 27). Zero High, zero Medium — nothing to re-litigate.
- `git diff -- django_strawberry_framework/optimizer/_context.py` empty, matching `### Files touched: None`.

### DRY findings disposition
- DRY recap is the canonical "extraction site already in place" shape with three legs (existing patterns reused via import-alias preservation, new helpers considered-and-rejected with reason, in-file duplication rationalized as documented two-stage dispatch). No DRY edit warranted; precedent-aligned with prior consolidated no-ops in 0.0.7.

### Temp test verification
- None used. No source edit warranted creating one.

### Verification outcome
`cycle accepted; verified` — sets top-level `Status: verified` and marks the checklist box at `review-0_0_7.md:106`.

### Changelog disposition verification
- `git diff -- CHANGELOG.md` empty, matching the `Not warranted` claim.
- Two citations meet the bar (AGENTS.md line 21 + active plan silence); the nine-cycle precedent chain under 0.0.7 reinforces the disposition. Internal-only framing is honest — no public-API surface touched this cycle (zero source edits).
- `uv run ruff check django_strawberry_framework/optimizer/_context.py` — All checks passed (independent confirmation).
