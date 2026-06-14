# Review: `django_strawberry_framework/optimizer/_context.py`

Status: verified

## DRY analysis

- **Defer GLOSSARY stash-key documentation until the read helper goes public OR a sixth `dst_optimizer_*` key lands.** The five canonical stash-key constants live at `_context.py #"DST_OPTIMIZER_PLAN ="` through `#"DST_OPTIMIZER_STRICTNESS ="` and are the single source of truth — `optimizer/extension.py:52-62` and `types/resolvers.py:40-45` both import the names rather than re-spelling the literals (the helper's `## What looks solid` recap confirms zero re-spelled literals, matching the shadow overview's "Repeated string literals: None"). No source-level DRY remains. The only open consolidation is documentation: `docs/GLOSSARY.md:541` names `dst_optimizer_plan` / `dst_optimizer_fk_id_elisions`, and `docs/GLOSSARY.md:1265` says "Planned resolver keys and lookup paths are stashed on `info.context`" without citing `dst_optimizer_planned` / `dst_optimizer_lookup_paths` / `dst_optimizer_strictness`. Defer until either (a) the `_context` module loses its underscore prefix and `get_context_value` / `stash_on_context` become public consumer API (today both are imported under the `_get_context_value` / `_stash_on_context` aliases by their only two consumers — internal-only signal), OR (b) the next consumer-facing optimizer feature adds a sixth `dst_optimizer_*` key. The correct GLOSSARY home is the Strictness-mode / extension entry, not this underscore-prefixed module — forwarded to `rev-optimizer.md` for paired consideration with the `rev-optimizer__extension.md` / `rev-types__resolvers.md` quick-checks. Not a `_context.py` edit.

## High:

None.

## Medium:

None.

## Low:

### GLOSSARY stash keys partially undocumented (forward-looking, not a `_context.py` defect)

`docs/GLOSSARY.md:1265` ("Planned resolver keys and lookup paths are stashed on `info.context` for introspection during strictness incidents") advertises an introspection use-case but never names the three keys a consumer would read: `dst_optimizer_planned`, `dst_optimizer_lookup_paths`, `dst_optimizer_strictness` (the constants at `_context.py #"DST_OPTIMIZER_PLANNED ="`, `#"DST_OPTIMIZER_LOOKUP_PATHS ="`, `#"DST_OPTIMIZER_STRICTNESS ="`). `dst_optimizer_plan` and `dst_optimizer_fk_id_elisions` are named once at `docs/GLOSSARY.md:541`.

This is forward-looking, not act-now, for two reasons. (1) Trigger gating: both defer conditions from the prior cycle remain unfired — the module is still underscore-prefixed `_context`, the helpers are still imported under `_`-aliases by both consumers (internal-only), and there are still exactly five keys. (2) Ownership: the natural GLOSSARY home is the Strictness-mode / `DjangoOptimizerExtension` entry that does the stashing and advertises the introspection contract, not this module's (nonexistent) entry — an underscore-prefixed dispatch helper has no consumer-facing GLOSSARY surface of its own. Routed to `rev-optimizer.md` (folder pass) rather than fixed here so it lands in one sweep with the extension/resolvers GLOSSARY checks. No `_context.py` source edit warranted.

## What looks solid

### DRY recap

- **Existing patterns reused.** The five stash-key literals are centralized as module constants (`_context.py #"DST_OPTIMIZER_PLAN ="` ff.) and imported by name at `optimizer/extension.py:52-62` and `types/resolvers.py:40-45` — the module *is* the package's anti-duplication home for context-key strings, which the module docstring states as its raison d'être ("a future broadening ... only has to land in one place"). Shadow overview confirms zero repeated string literals in the file.
- **New helpers considered.** A helper to collapse the read-side `(TypeError, KeyError, AttributeError)` catch and the write-side `(TypeError, AttributeError)` catch was considered and rejected — the two tuples are deliberately different (read must additionally absorb `KeyError` from a missing-key `__getitem__`; write must NOT swallow `KeyError`, which a real `dict` never raises on assignment, so a guarded mapping's signal surfaces). The asymmetry is the contract, not duplication, and is documented inline at `_context.py #"are NOT swallowed"`.
- **Duplication risk in the current file.** The non-dict `setattr` catch `(AttributeError, TypeError)` and the dict-write catch `(TypeError, AttributeError)` list the same two classes in opposite order, but their *behavior* diverges by design — the first is catch-and-chain (fall through to `__setitem__`), the second is catch-and-return (silently skip). The 14-line comment block at `_context.py #"Chain into the dict-write path"` and `#"catch-and-return pattern; this one is the"` explicitly distinguishes the two patterns. Intentional, not a near-copy to fold.

### Other positives

- **Read/write symmetry is sound and explicitly reasoned.** `get_context_value` and `stash_on_context` mirror each other's dispatch order: `None` short-circuits; `dict` (and subclasses, incl. `QueryDict`) route through `get`/`__setitem__` first; non-`dict` route through `getattr`/`setattr` first with a mapping fallback. A value `setattr`'d externally onto a `dict` subclass is intentionally invisible to the read path because the write path also routes dict subclasses through `__setitem__` — round-trip preserved, documented at `_context.py #"Values stashed by code outside this module"`.
- **Every documented branch is test-pinned.** The two docstring-named pins exist and exercise the exact shapes: `tests/optimizer/test_extension.py::test_stash_on_non_dict_mapping_reads_correctly` (`__slots__` mapping, setattr-fails-then-`__setitem__`-succeeds round trip) and `::test_get_context_value_swallows_attribute_error_from_getitem` (bridged-`AttributeError` `__getitem__`). The frozen write modes are pinned too: `MappingProxyType` `TypeError` (`::test_*mappingproxy*`), locked-`QueryDict`-style `AttributeError` from a `dict`-subclass `__setitem__`, the negative pin `::test_stash_does_not_swallow_unexpected_exceptions_from_setitem` (a `RuntimeError` from `__setitem__` must propagate, proving the catch tuple stays narrow), and `::test_stash_on_none_context_is_silent`.
- **`_MISSING` sentinel is correct.** Using a module-level `object()` sentinel as the `getattr` default lets the helper distinguish a genuinely-absent attribute from one explicitly stashed as `None`, so a `None`-valued stash is returned rather than collapsing to the item-access fallback. Documented at `_context.py #"distinguish a missing attribute"`.
- **No Django/ORM coupling, no import-time side effects.** Shadow overview reports zero ORM markers and two stdlib-only imports (`__future__`, `typing.Any`); the module is pure dispatch with no first-party imports, so no circular-import risk despite being consumed by both `optimizer/extension.py` and `types/resolvers.py`.
- **Defensive-coerce stance is correctly scoped.** The module docstring distinguishes the reflective `getattr(obj, name, None) or {}` posture used across the optimizer (upstream contract genuinely allows absent/`None`) from the strict consumer-input posture in `conf.py`, warning against conflating the two during refactors — an accurate, useful boundary note.

### Summary

`_context.py` is a 161-line pure-dispatch module: five stash-key constants plus a symmetric `get_context_value` / `stash_on_context` pair that hand optimizer plan/elision/strictness state across `info.context` between the write side (`optimizer/extension.py`) and the read side (`types/resolvers.py`). Logic is correct: read/write dispatch mirrors, the two catch tuples differ exactly where the contract requires (`KeyError` swallowed on read, surfaced on write), the `_MISSING` sentinel handles the `None`-stash edge, and every branch is pinned by a named test — several of which already cite `rev-optimizer__context` as their motivating finding. No High/Medium; the single Low is forward-looking GLOSSARY drift whose defer triggers remain unfired and whose fix belongs to the folder pass, not this module. The prior 0.0.7 artifact's three Lows are all resolved or correctly-still-deferred in live source (the `setattr`-catch comment Low is fully merged as the 14-line block at lines 132-145; the "unreachable branch" Low is superseded by the now-documented `__slots__`/bridged-context justification with two pins). Zero source/test/GLOSSARY/CHANGELOG edits — a no-source-edit (shape #5) cycle.

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — pass, 265 files left unchanged.
- `uv run ruff check .` — pass, "All checks passed!".

### Notes for Worker 3
- Single Low (GLOSSARY stash keys partially undocumented) is forward-looking and forwarded to `rev-optimizer.md` (folder pass); both defer triggers — module de-underscored / public helper, or a sixth `dst_optimizer_*` key — remain unfired, and the GLOSSARY home is the extension/strictness entry, not this module. No local edit.
- No High, no Medium, no behavior-changing finding.
- No GLOSSARY-only fix in scope for this file (the GLOSSARY item targets the folder pass and is not this module's entry).
- Prior 0.0.7 artifact's three Lows all resolved/correctly-deferred in live source — verified, not re-raised.

---

## Verification (Worker 3)

### Logic verification outcome

No-source-edit (shape #5) cycle. `git diff --stat 0872a20 -- optimizer/_context.py` is empty (exit 0) — the target is byte-unchanged from baseline. No High/Medium. The lone Low (GLOSSARY stash keys partially undocumented) is forward-looking and forwarded to the folder pass `rev-optimizer.md`: both defer triggers remain unfired (module still underscore-prefixed `_context`, both consumers still import under `_get_context_value`/`_stash_on_context` aliases, still exactly five `dst_optimizer_*` keys), and the natural GLOSSARY home is the Strictness/`DjangoOptimizerExtension` entry, not this module's (nonexistent) entry. Not a `_context.py` defect — correctly deferred, not a GLOSSARY-only fix in this file's scope.

Independently drove the asymmetric-catch contract live (`uv run python`, Django importable):
- Read swallows `KeyError`/`TypeError`/`AttributeError` from `__getitem__` -> `default` (guarded mapping + `None` context both return default).
- `_MISSING` sentinel preserves a `None`-valued stash (object with `k=None` returns `None`, not the fallback `default`) — the sentinel edge.
- Write absorbs only `TypeError` (`MappingProxyType`) and `AttributeError` (locked-`QueryDict`-shape `dict` subclass `__setitem__`); silently skips both.
- Write does NOT swallow an unexpected `RuntimeError` from `__setitem__` — it surfaces (negative pin behavior confirmed live), proving the catch tuple stays narrow.
- `__slots__` mapping round-trips: `setattr` fails -> chains to `__setitem__`, and the read fallback resolves it back (42 in, 42 out).

All six checks pass. The asymmetry (read swallows `KeyError`, write surfaces it) is the documented contract, not duplication. Cited pins all grep-match: `test_stash_on_non_dict_mapping_reads_correctly` (:2860), `test_get_context_value_swallows_attribute_error_from_getitem` (:2888), `test_stash_on_none_context_is_silent` (:2911), `test_stash_does_not_swallow_unexpected_exceptions_from_setitem` (:3000); frozen-write pins `test_stash_on_immutable_dict_subclass_is_silent` (:2974) and the `MappingProxyType` B5 pin (:2934) exist under their own names. Ruff format-check + check pass on the target (COM812 warning is the standing config note, not a failure).

### DRY findings disposition

Single DRY item carried forward (not a `_context.py` edit): the GLOSSARY stash-key documentation defers to `rev-optimizer.md` (folder pass) for paired consideration with the extension/resolvers quick-checks. Source-level DRY is none — the five stash-key literals are centralized as module constants and imported by name by both consumers (`extension.py`, `resolvers.py`); the two catch tuples differ by design (read absorbs `KeyError`, write does not), documented in the 14-line block at `#"Chain into the dict-write path"`. Accepted as carried-forward, no action this cycle.

### Temp test verification

None — no temp test files created. Live verification used inline `uv run python` probes only (not persisted).

### Verification outcome

cycle accepted; verified

Sibling attribution: dirty hunks in the baseline diff stat (`conf.py`, `exceptions.py`, `filters/factories.py`, `filters/sets.py`, `list_field.py`, `management/commands/inspect_django_type.py`, `docs/GLOSSARY.md`) all attribute to CLOSED sibling cycles — each is `[x]` in `docs/review/review-0_0_9.md` (conf :70, exceptions :72, list_field :73, filters/factories :80, filters/sets :82, inspect_django_type :87); GLOSSARY hunks belong to rev-connection/rev-filters/inspect closed cycles. None owned by this cycle. The cycle's own "Files touched: None" holds — `optimizer/_context.py` is byte-unchanged.

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern. No comment/docstring edits — the module's docstrings and the 14-line dict-write/catch-and-chain comment block already document every non-obvious branch (sentinel rationale, read/write symmetry, narrow-catch reasoning) accurately against live behavior.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern.

Not warranted — zero source edits this cycle (`AGENTS.md` "Do not update CHANGELOG.md unless explicitly instructed"; active plan `docs/review/review-0_0_9.md` records no changelog action for this item).
