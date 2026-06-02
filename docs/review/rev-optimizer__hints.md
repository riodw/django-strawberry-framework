# Review: `django_strawberry_framework/optimizer/hints.py`

Status: verified

## DRY analysis

- Defer until a second non-walker, non-schema-audit consumer of the four-flag dispatch lands — at that point extract a `hint_kind(hint) -> Literal["skip", "prefetch_obj", "force_select", "force_prefetch", "noop"]` classifier from `optimizer/walker.py:433-460` (`_apply_hint`'s if-chain) and `hint_is_skip` (`hints.py:131-148`), and route all three callers through it. Today's two-call-site footprint (`extension.py:721` schema audit + `walker.py:433` `_apply_hint`) is exactly the shape `hint_is_skip` was extracted for; adding a classifier for the other three branches would over-engineer against the second use case. The trigger phrase to grep is `hint_is_skip` — when a third site appears, re-triage at that point.
- Defer until the SKIP sentinel pattern reappears for a second `dataclass(frozen=True)` in the package — at that point factor the post-class-body `Cls.SKIP = Cls(skip=True)  # type: ignore[misc]` sentinel installation (`hints.py:71` + `hints.py:157`) into a shared `freeze_sentinel(cls, name, **kwargs)` helper or a `@with_sentinels` decorator under `utils/`. Today the dataclass + ClassVar + post-body rebind is well-commented (`hints.py:69-70`, `hints.py:151-156`) and load-bearing — collapsing it now would obscure the rationale.

## High:

None.

## Medium:

### GLOSSARY drift on `OptimizerHint` — construction-time conflict rejection unmentioned

The shipped `__post_init__` (`hints.py:73-104`) rejects four conflict shapes at `OptimizerHint(...)` construction time (`skip` with any of the other three flags; `force_select` with `force_prefetch`; `prefetch_obj` with a non-`Prefetch` value; `prefetch_obj` with `force_select`/`force_prefetch`), raising `ConfigurationError`. This behaviour shipped in `0.0.4` (`CHANGELOG.md:137`: "`OptimizerHint` now rejects conflicting flag combinations …") but the GLOSSARY entry at `docs/GLOSSARY.md:758-771` lists only the four supported modes — no mention that out-of-shape direct constructions are rejected at instance-creation time. Consumers who construct via factories never see this guard, but consumers who write `OptimizerHint(skip=True, force_select=True)` directly (the dataclass is explicitly documented as non-hidden in `hints.py:46-50`) will catch the `ConfigurationError` and key against it. Same calibration as `rev-management__commands__export_schema.md::Schema export management command` GLOSSARY drift and `rev-optimizer__extension.md::DjangoOptimizerExtension` GLOSSARY drift: a multi-mode public-contract entry that cumulatively lags a shipped `### Fixed` entry adding a `ConfigurationError`-shape contract is Medium, not Low.

Verbatim replacement prose for Worker 2 to lift directly (insert as a new paragraph between the four-mode bullet list and `**See also:**` at `docs/GLOSSARY.md:769-771`):

```
Validation: ``OptimizerHint(...)`` rejects conflicting flag combinations at
construction time and raises [`ConfigurationError`](#configurationerror).
The factories (`SKIP`, `select_related()`, `prefetch_related()`,
`prefetch(Prefetch(...))`) are the documented consumer API; direct
construction is supported but the same four shapes are the only ones the
walker dispatches, and any other combination — `skip=True` with any of the
three other flags, `force_select=True` with `force_prefetch=True`,
`prefetch_obj=` set with `force_select=True` or `force_prefetch=True`, or a
`prefetch_obj=` value that is not a `django.db.models.Prefetch` instance —
is rejected before the hint can reach `Meta.optimizer_hints`.
```

```docs/GLOSSARY.md:758-771
## `OptimizerHint`

**Status:** shipped (`0.0.3`).

Typed wrapper for per-relation optimizer overrides. Pass instances through [`Meta.optimizer_hints`](#metaoptimizer_hints).

Supported modes:

- `OptimizerHint.SKIP` — exclude a relation from automatic planning (the optimizer leaves it alone).
- `OptimizerHint.select_related()` — force `select_related`.
- `OptimizerHint.prefetch_related()` — force `prefetch_related`.
- `OptimizerHint.prefetch(Prefetch(...))` — use a consumer-provided `Prefetch` object and stop walking below that relation.

**See also:** [`Meta.optimizer_hints`](#metaoptimizer_hints) · [`DjangoOptimizerExtension`](#djangooptimizerextension).
```

## Low:

### `prefetch_obj` excluded from `repr` hides the only distinguishing field of `prefetch(obj)` hints

`hints.py:62` declares `prefetch_obj: Prefetch | None = field(default=None, repr=False)`. That `repr=False` cleanly hides `prefetch_obj=None` in the repr of `OptimizerHint.SKIP` / `select_related()` / `prefetch_related()` (which all share `prefetch_obj=None`), but it ALSO hides the `Prefetch` instance on `OptimizerHint.prefetch(Prefetch("items", queryset=...))`. The visible repr of a `prefetch(obj)` hint collapses to `OptimizerHint(force_select=False, force_prefetch=False, skip=False)` — visually indistinguishable from an empty `OptimizerHint()` and stripping the load-bearing `Prefetch` object that makes the hint useful. Recommend `repr=True` (the default) and accepting the `prefetch_obj=None` noise on the three other shapes, since debugging a misrouted `prefetch(obj)` hint is the more likely failure mode than the noise of seeing `prefetch_obj=None` in a `SKIP` repr. Same severity as the `field_meta.py:140-152` inline-comment-vs-docstring duplication Low — a small consumer-debug-surface tightening.

```django_strawberry_framework/optimizer/hints.py:60-63
    force_select: bool = False
    force_prefetch: bool = False
    prefetch_obj: Prefetch | None = field(default=None, repr=False)
    skip: bool = False
```

### `hint_is_skip` parameter type `Any` over-broadens the documented input shape

`hints.py:131` declares `def hint_is_skip(hint: Any) -> bool:`. Both shipped call sites pass either `OptimizerHint` or `None` — `optimizer/walker.py:433` (`_apply_hint(hint: OptimizerHint, ...)` passes `hint` directly) and `optimizer/extension.py:721` (passes `hints.get(field_name)` whose value type is `OptimizerHint | None` per `types/definition.py:79`'s `optimizer_hints: dict[str, OptimizerHint]`). The `Any` annotation is paired with the defensive `getattr(hint, "skip", False)` fallback at `hints.py:148` and the test pin `test_hint_is_skip_handles_sentinel_record_and_unknown_shapes` at `tests/optimizer/test_extension.py:2996-3006` (which calls `hint_is_skip(object())`), so the broad annotation is intentional forward-looking room for a future hint surface. Defer until either (a) the third call site lands and forces a contract decision, or (b) a non-`OptimizerHint` hint surface ships — at that point tighten to `OptimizerHint | None` and drop the `getattr` fallback, OR keep `Any` and document the contract on the docstring. Today the asymmetry between the narrow walker-side type contract (`OptimizerHint`) and the broad helper-side type contract (`Any`) is the smaller defect than either change would create.

### `__post_init__` docstring frames the priority order as load-bearing for the validation rationale

`hints.py:73-82` docstring says: "The walker consumes flags in a strict priority order (`skip` → `prefetch_obj` → `force_select` → `force_prefetch`), so any combination beyond the four documented shapes silently loses the lower-priority directive. Raising here surfaces the mistake at `Meta.optimizer_hints` build time instead of at query time." That priority order WAS load-bearing pre-`0.0.4`-fix (when `__post_init__` did not reject conflicts); post-fix, the walker's `_apply_hint` at `walker.py:407-432` documents the priority as "documentation, not collision arbitration" (`walker.py:430-431`) because `__post_init__` already rejects every combination the priority order would have arbitrated. The docstring's framing is therefore stale: the silent-drop reasoning describes pre-fix behaviour. Comment-pass fix: rewrite the docstring to lead with the construction-time-rejection contract and frame the priority order as the historical/walker-documentation rationale, mirroring the inverse framing already present at `walker.py:429-431` ("`OptimizerHint.__post_init__` already rejects conflicting flag combinations, so the priority order here is documentation, not collision arbitration").

```django_strawberry_framework/optimizer/hints.py:73-82
    def __post_init__(self) -> None:
        """Reject conflicting flag combinations at construction time.

        The walker consumes flags in a strict priority order
        (``skip`` → ``prefetch_obj`` → ``force_select`` → ``force_prefetch``),
        so any combination beyond the four documented shapes silently
        loses the lower-priority directive.  Raising here surfaces the
        mistake at ``Meta.optimizer_hints`` build time instead of at
        query time.
        """
```

### Module docstring "earlier exploratory design" reference is unanchored historical context

`hints.py:4-7` says "Replaces the earlier exploratory design that mixed raw strings (`"skip"`), `Prefetch` objects, and dicts (`{"select_related": True}`) in the same field-value position." This reads as audit-trail without a citation anchor — the migration is not in any current spec (`docs/SPECS/` grep shows no `spec-` referencing the pre-`OptimizerHint` design) and is not visible in `CHANGELOG.md` either (the `0.0.3` `### Added` entry at `CHANGELOG.md:149` introduces `OptimizerHint` without naming the pre-existing shape). Either anchor the claim to a spec/changelog citation per the symbol-qualified path convention in `AGENTS.md` rule 27, OR drop the paragraph since the consumer-surface paragraph above it (lines 8-19) already documents the current shape. Defer-with-trigger: if a future spec retroactively documents the migration (e.g. a `docs/SPECS/spec-NNN-optimizer_hint_typed_wrapper.md` archival), anchor the citation; otherwise drop the paragraph at the next comment-pass touch of this file. Same calibration as the `list_field.py::spec-016 → spec-020` and `scalars.py::TODO-ALPHA-028 → TODO-ALPHA-035` citation-hygiene Lows.

## What looks solid

### DRY recap

- **Existing patterns reused.** `hint_is_skip` (`hints.py:131-148`) is the canonical dispatch helper consumed by both `walker.py:433` (`_apply_hint`) and `extension.py:721` (schema audit relation walk); no other site open-codes the `hint is OptimizerHint.SKIP or hint.skip` check. `__post_init__` (`hints.py:73-104`) is the single construction-time validator — the Meta-level validator at `types/base.py:737-741` only checks `isinstance(v, OptimizerHint)`, never the inner flag combinations, because `__post_init__` already did. The `ClassVar`-then-post-body-rebind sentinel pattern (`hints.py:71` + `hints.py:157`) is the documented load-bearing shape per the inline comment block at `hints.py:151-156`.
- **New helpers considered.** A `hint_kind(hint)` classifier covering all four configurable shapes (not just `skip`) was considered — rejected at this scope because today's two callers each need different downstream dispatch (walker dispatches to four branches, schema audit dispatches only to the skip branch), so a single classifier doesn't shrink either site by more than one line. Recorded as defer-with-trigger in `## DRY analysis` above. A shared `freeze_sentinel(cls, name, **kwargs)` helper for the `ClassVar` + post-body rebind pattern was also considered — rejected at this scope because the pattern appears once in the package. Recorded as defer-with-trigger.
- **Duplication risk in the current file.** The `__post_init__` validator's four `raise ConfigurationError(...)` arms (`hints.py:86-104`) are intentionally separate to give each conflict its own message text — folding them through a shared `_reject(reason: str)` helper would obscure the per-conflict guidance that is the load-bearing UX property here ("use either select_related() or prefetch_related(), not both" guides the consumer to the right factory).

### Other positives

- The dataclass is `frozen=True` (`hints.py:42`) and the SKIP sentinel + the three factory results are all immutable — pinned by `tests/optimizer/test_hints.py:89-102` (`TestFrozenImmutability`) for both factory-produced hints and the `SKIP` sentinel. Equality + identity contracts pinned by `tests/optimizer/test_hints.py:31-37` (`SKIP` identity) and `tests/optimizer/test_hints.py:104-117` (`TestEquality`).
- All four `__post_init__` reject branches are pinned by `tests/optimizer/test_hints.py:120-177` (`TestConflictingFlagsRejected`), including the `prefetch_obj`-with-non-`Prefetch`-value branch on both the factory (`OptimizerHint.prefetch("entries__items")`) and the direct-construction (`OptimizerHint(prefetch_obj="entries__items")`) paths.
- The `hint_is_skip` defensive `getattr` fallback (`hints.py:148`) is reachable and pinned by `tests/optimizer/test_extension.py:2996-3006`'s `hint_is_skip(object())` assertion — the "never raises" contract the docstring claims is test-anchored, not just code-anchored.
- Inline comment block at `hints.py:35-39` correctly documents why `Prefetch` is a runtime (not `TYPE_CHECKING`) import — the `isinstance` check at `hints.py:95` consumes the runtime symbol. This is the inverse of the `field_meta.py:20` `from __future__ import annotations` carry-forward I recorded last cycle: when a runtime check needs a Django symbol, the import stays runtime even though the type annotation alone would tolerate `TYPE_CHECKING`. Good audit-trail comment.
- The `# noqa: N815` at `hints.py:71` is correctly scoped to the single `SKIP` ClassVar declaration; no broader noqa.
- GLOSSARY drift quick-check on the dispatched grep set (`OptimizerHint`, `OptimizerHint.SKIP`, `OptimizerHint.select_related`, `OptimizerHint.prefetch_related`, `OptimizerHint.prefetch`): the `OptimizerHint` entry at `docs/GLOSSARY.md:758-771` documents all four modes including `SKIP`, `select_related()`, `prefetch_related()`, `prefetch(Prefetch(...))`. The only drift item is the construction-time conflict rejection contract (filed as Medium above) — no other GLOSSARY drift.

### Summary

`hints.py` is a 157-line typed-wrapper module on a six-symbol shape: one frozen dataclass (`OptimizerHint`) with one ClassVar sentinel + three factory classmethods + one `__post_init__` validator, plus one module-level `hint_is_skip` dispatch helper that's the single source of truth for the skip-shape dispatch consumed at two sites in `optimizer/`. Zero High, one Medium (GLOSSARY drift on construction-time conflict rejection — verbatim replacement prose preserved for Worker 2), four Lows (one logic-shape tightening on `repr=False`, three comment/docstring/citation hygiene). Two defer-with-explicit-trigger DRY items, no act-now opportunity. Standard three-spawn cycle (shape #4 consolidated single-spawn at Worker 2 because of the GLOSSARY-bearing Medium, per `worker-1.md` "GLOSSARY-only fixes do NOT qualify [for shape #5] — they need a real edit; route through shape #4"). `Status: under-review`.

---

## Fix report (Worker 2)

### Files touched
- `docs/GLOSSARY.md:771-781` — inserted the artifact's verbatim Validation paragraph between the four-mode bullet list and the `**See also:**` line of the `OptimizerHint` entry (Medium GLOSSARY drift on construction-time conflict rejection).
- `django_strawberry_framework/optimizer/hints.py:62` — flipped `prefetch_obj: Prefetch | None = field(default=None, repr=False)` to `prefetch_obj: Prefetch | None = None` so a `prefetch(Prefetch(...))` hint's repr no longer collapses to the same shape as `OptimizerHint.SKIP` / `select_related()` / `prefetch_related()` (Low #1). Dropped the now-unused `field` import from `dataclasses`.
- `django_strawberry_framework/optimizer/hints.py:131` — tightened `hint_is_skip(hint: Any)` to `hint_is_skip(hint: OptimizerHint | None)` matching both real call sites (`walker.py:433` passes `OptimizerHint`; `extension.py:721` passes `OptimizerHint | None` via `hints.get(field_name)`). Defensive `getattr(hint, "skip", False)` fallback preserved at runtime (Python type annotations are not enforced at runtime, so `test_hint_is_skip_handles_sentinel_record_and_unknown_shapes`'s `hint_is_skip(object())` still returns `False` via the fallback) (Low #2). Dropped the now-unused `Any` import from `typing`.
- `django_strawberry_framework/optimizer/hints.py:73-86` — rewrote `__post_init__` docstring to lead with the construction-time-rejection contract and frame the walker's priority order as documentation of the dispatch sequence rather than collision arbitration, mirroring the inverse framing at `walker.py:429-431` (Low #3).
- `django_strawberry_framework/optimizer/hints.py:1-6` — dropped the unanchored "Replaces the earlier exploratory design that mixed raw strings..." paragraph from the module docstring; the consumer-surface paragraph above it already documents the current shape and the migration narrative has no spec/changelog citation anchor (Low #4).

### Tests added or updated
- None. Logic surface unchanged at the public-contract level: `__post_init__` still rejects the same four conflict shapes (all pinned by `tests/optimizer/test_hints.py::TestConflictingFlagsRejected`); `hint_is_skip` runtime contract preserved (the `object()` test passes through the `getattr` fallback). The `repr=False` → default flip is a debug-surface widening; no test pins the prior repr-elision shape (grep on `tests/optimizer/test_hints.py` for `repr` returns nothing).

### Validation run
- `uv run ruff format .` — pass, 211 files unchanged
- `uv run ruff check --fix .` — pass (All checks passed!)

### Notes for Worker 3
- Shadow file: none used this cycle.
- Low #2 caveat: the dispatch prompt asked to "tighten `hint_is_skip(hint: OptimizerHint)` annotation"; applied `OptimizerHint | None` (not bare `OptimizerHint`) because both shipped call sites pass that union — `walker.py:433` `_apply_hint(hint: OptimizerHint, ...)` is `OptimizerHint`, but `extension.py:721`'s `hints.get(field_name)` returns `OptimizerHint | None` per `types/definition.py:79`'s `optimizer_hints: dict[str, OptimizerHint]`. Bare `OptimizerHint` would mistype the schema-audit call site. The `getattr` fallback stays in place so the `object()` test at `tests/optimizer/test_extension.py:2996-3006` still returns `False` at runtime (Python type annotations are advisory).
- DRY analysis: both items remain defer-with-explicit-trigger; no source change to the `hint_kind(hint)` classifier or to the `freeze_sentinel` extraction this cycle (third-call-site / second-frozen-sentinel triggers unchanged).
- `uv.lock` not touched.

---

## Comment/docstring pass

(Consolidated into single-spawn — applied alongside logic edits.)

### Files touched
- `django_strawberry_framework/optimizer/hints.py:73-86` — `__post_init__` docstring rewrite (Low #3 above).
- `django_strawberry_framework/optimizer/hints.py:1-6` — module docstring paragraph drop (Low #4 above).

### Per-finding dispositions
- Medium (GLOSSARY drift on `OptimizerHint`): applied — verbatim Validation paragraph lifted into `docs/GLOSSARY.md` between the four-mode bullet list and `**See also:**`.
- Low #1 (`prefetch_obj` excluded from `repr`): applied — switched to default `repr=True` per artifact recommendation.
- Low #2 (`hint_is_skip` parameter type `Any`): applied — tightened to `OptimizerHint | None` per dispatch prompt; `getattr` fallback retained so `object()` test contract holds at runtime.
- Low #3 (`__post_init__` docstring framing): applied — rewrote to lead with construction-time-rejection contract, frame priority order as walker documentation rather than collision arbitration, mirroring `walker.py:429-431` inverse framing.
- Low #4 (module docstring "earlier exploratory design"): applied — dropped the unanchored paragraph; consumer-surface paragraph above it already documents the current shape.

### Validation run
- `uv run ruff format .` — pass, 211 files unchanged
- `uv run ruff check --fix .` — pass

### Notes for Worker 3
Consolidated single-spawn (shape #4): logic and comment passes applied together since every edit is either a verbatim GLOSSARY lift, a single-line annotation tightening, a `repr=False`-flag flip, or docstring polish — no logic surface change requires a separate logic-then-comment dispatch.

---

## Changelog disposition

### State
`Not warranted`.

### Reason
- `AGENTS.md` rule 21: "Do not update CHANGELOG.md unless explicitly instructed."
- The active plan `docs/review/review-0_0_7.md` is silent on changelog authorization for this cycle item.

Both halves cited per `worker-2.md` "Not warranted" disposition gate. The cycle's edits are internal documentation polish (verbatim GLOSSARY prose lift; module/`__post_init__` docstring rewrites; one-token annotation tightening; one `field(repr=False)` → default flip with no public-contract behaviour change). No consumer-visible behaviour change — `__post_init__` still rejects the same four conflict shapes; `hint_is_skip` still returns the same runtime values; the `repr` widening is a debug-surface improvement, not an API change.

### What was done
No `CHANGELOG.md` edit.

### Validation run
- `uv run ruff format .` — pass, 211 files unchanged
- `uv run ruff check --fix .` — pass

---

## Verification (Worker 3)

### Logic verification outcome
- Medium (GLOSSARY drift on `OptimizerHint`): accepted — verbatim Validation paragraph applied at `docs/GLOSSARY.md:771-780` between the four-mode bullet list and the `**See also:**` line, char-for-char matching the artifact's preserved replacement prose.
- Low #1 (`prefetch_obj` excluded from repr): accepted — `prefetch_obj: Prefetch | None = None` at `hints.py:60` (the `field(default=None, repr=False)` form is gone); `field` symbol dropped from `from dataclasses import dataclass` import at `hints.py:26`. A `prefetch(Prefetch(...))` hint's repr now distinguishes from `SKIP`/`select_related()`/`prefetch_related()`.
- Low #2 (`hint_is_skip` parameter type): accepted — `hint_is_skip(hint: OptimizerHint | None) -> bool` at `hints.py:133`; `Any` import dropped from `typing`; defensive `getattr(hint, "skip", False)` fallback preserved at `hints.py:150` so the `test_hint_is_skip_handles_sentinel_record_and_unknown_shapes` `object()` contract still passes via runtime fallback. Worker 2's `OptimizerHint | None` (not bare `OptimizerHint`) is the correct widening — `extension.py:721` passes `hints.get(field_name)` which is `OptimizerHint | None`.
- Low #3 (`__post_init__` docstring framing): accepted — rewritten at `hints.py:71-84` to lead with "Construction-time rejection is the load-bearing contract" and frame the walker's priority order as "documentation of the dispatch sequence, not collision arbitration", mirroring the inverse framing at `walker.py:429-431`.
- Low #4 (module docstring "earlier exploratory design"): accepted — the unanchored paragraph is gone from `hints.py:1-4`; the consumer-surface paragraph above already documents the current shape.
- Logic regression check: `__post_init__` at `hints.py:85-106` still raises `ConfigurationError` on the same four conflict shapes — skip+(force_select|force_prefetch|prefetch_obj), force_select+force_prefetch, prefetch_obj non-`Prefetch` value, prefetch_obj+(force_select|force_prefetch). All seven `TestConflictingFlagsRejected` tests at `tests/optimizer/test_hints.py:120-177` (skip+force_select, skip+force_prefetch, skip+prefetch_obj, force_select+force_prefetch, prefetch_obj+force_select, prefetch_obj+force_prefetch, prefetch_obj non-`Prefetch`) still grep-match and still target the same raise sites unchanged.

### DRY findings disposition
Both DRY items remain defer-with-explicit-trigger as recorded in the artifact: (1) `hint_kind(hint)` classifier — defer until a third call site lands beyond `walker.py:433` and `extension.py:721` (trigger: grep `hint_is_skip`); (2) `freeze_sentinel(cls, name, **kwargs)` helper — defer until a second `dataclass(frozen=True)` SKIP-sentinel pattern appears in the package. No source change to either today.

### Temp test verification
None used this cycle.

### Verification outcome
`cycle accepted; verified`.

### Notes for Worker 3 self-review
- `git diff -- docs/GLOSSARY.md django_strawberry_framework/optimizer/hints.py CHANGELOG.md` confirmed all five Fix-report claims and the empty `CHANGELOG.md` diff.
- Ruff spot-verify on `hints.py`: `uv run ruff format --check` → "1 file already formatted"; `uv run ruff check` → "All checks passed!". Both gates clean.
- Worker 2's `OptimizerHint | None` widening over the dispatch prompt's bare `OptimizerHint` was the right call (recorded as a Low #2 caveat in `Notes for Worker 3`); bare `OptimizerHint` would mistype the `extension.py:721` schema-audit call site that legitimately passes `None`. The runtime `getattr` fallback is the audit's "never raises" insurance, separate from the static annotation.
