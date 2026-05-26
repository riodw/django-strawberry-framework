# Review: `django_strawberry_framework/optimizer/hints.py`

Status: verified

## DRY analysis

- None — `hints.py` is at the right granularity (one `OptimizerHint` dataclass + one `SKIP` sentinel + one `hint_is_skip` dispatch helper); the consumer-facing factory-name error prose duplications inside `__post_init__` are intentional consumer-readable error messages, not dispatch keys, and the only cross-call-site helper needed today (`hint_is_skip`) is already extracted and consumed by both the walker (`optimizer/walker.py:425`) and the extension audit (`optimizer/extension.py:719`).

## High:

None.

## Medium:

None.

## Low:

### `SKIP` is not annotated `Final`, leaving the sentinel rebindable from any consumer module

Carry-forward from the 0.0.6 cycle on the same file (unchanged across the 0.0.6→0.0.7 boundary). `OptimizerHint.SKIP` is the documented sentinel identity. `hint_is_skip` performs an `is` check against it at `hints.py:144`, and the consumer-surface docstring at `hints.py:8-19` advertises `OptimizerHint.SKIP` as the canonical "skip this relation" value. The current declaration is `ClassVar[OptimizerHint]` (line 71) with a post-class-body bind at line 155 using `# type: ignore[misc]`. `ClassVar` blocks the dataclass decorator from treating `SKIP` as a field; it does not block rebinding from outside. A consumer (or a test fixture cleanup that miscounts state) writing `OptimizerHint.SKIP = OptimizerHint(skip=True)` would silently break every `hint is OptimizerHint.SKIP` identity check across the package — `hint_is_skip` still returns the right answer for skip-shaped hints because of the `getattr(hint, "skip", False)` fallback at `hints.py:146`, but the walker's planning path through `_apply_hint` would no longer match `True` on the first branch and any optimization-plan-cache key that included sentinel identity would diverge. `typing.Final[OptimizerHint]` (already used elsewhere in the codebase for module-level singletons) would make the rebind a mypy/ruff failure without changing runtime behavior. This stays Low because the `# type: ignore[misc]` already documents that the bind is unusual and no test today exercises rebinding. Defer until a second module-level singleton lands that would benefit from the same `Final` annotation pattern; consolidate both at that point.

```django_strawberry_framework/optimizer/hints.py:69:71
    # Populated after the class body via ``OptimizerHint(skip=True)``.
    # Declared here as a ClassVar so the dataclass decorator ignores it.
    SKIP: ClassVar[OptimizerHint]  # noqa: N815
```

```django_strawberry_framework/optimizer/hints.py:155:155
OptimizerHint.SKIP = OptimizerHint(skip=True)  # type: ignore[misc]
```

### `OptimizerHint()` with no flag set has no canonical "no-op hint" name, but two test sites construct exactly that shape

Carry-forward from the 0.0.6 cycle. `tests/optimizer/test_walker.py:1218-1234` documents that `OptimizerHint()` with no args is a deliberate no-op the walker falls back through. `_apply_hint` at `optimizer/walker.py:399-500` returns `False` in that case so the cardinality dispatch runs. The class has no factory method for this shape (e.g., no `OptimizerHint.default()` or class-level `OptimizerHint.NOOP`) and no docstring sentence on the class itself naming this shape — the four-shapes language at `__post_init__`'s docstring (lines 76-82) actually claims "four documented shapes" which under-counts: there are five reachable shapes (skip, prefetch_obj, force_select, force_prefetch, no-op-empty). The walker's `_apply_hint` docstring at `optimizer/walker.py:414-423` repeats the "four configurable hint shapes" framing but at least names "the no-op empty form" explicitly. This is Low because the no-op shape is genuinely the *absence* of intent and naming it would mostly invite consumers to set it where omitting the key is clearer. Defer until a consumer files a bug or doc question about the "fifth shape" — at that point either rename the framing to "four configurable shapes plus a no-op empty" or add a `# noqa: ERA001`-anchored TODO to the class docstring; do not invent a fifth factory name proactively.

```django_strawberry_framework/optimizer/hints.py:76:82
        The walker consumes flags in a strict priority order
        (``skip`` → ``prefetch_obj`` → ``force_select`` → ``force_prefetch``),
        so any combination beyond the four documented shapes silently
        loses the lower-priority directive.  Raising here surfaces the
        mistake at ``Meta.optimizer_hints`` build time instead of at
        query time.
```

### `__post_init__` re-validates `isinstance(prefetch_obj, Prefetch)` but the field annotation is `Prefetch | None`

Carry-forward from the 0.0.6 cycle. The dataclass annotation at line 62 (`prefetch_obj: Prefetch | None = field(default=None, repr=False)`) is stringified by `from __future__ import annotations`, so it has no runtime enforcement. The `isinstance` check at line 93 fills that gap and is the load-bearing guard documented at lines 35-39. That works. The Low-tier polish is that the `__post_init__` body silently re-checks the type *after* the `skip and (...)` branch above; if a consumer passes `OptimizerHint(skip=True, prefetch_obj="bad")`, the `skip` collision error fires first and the type error is never raised. The two messages cover overlapping but distinct mistakes, and the order is deliberate (skip-collision is the more useful diagnostic — it points the consumer at the SKIP factory rather than at the prefetch factory's `obj` shape). No change recommended — recording so a future "collapse the four guards" simplification pass remembers the layered priority is intentional. Defer until a fifth `__post_init__` guard lands; at that point re-evaluate whether a single `_validate_flag_shape()` helper with a priority-ordered checklist reads better than four sequential `if`s.

```django_strawberry_framework/optimizer/hints.py:83:97
        if self.skip and (self.force_select or self.force_prefetch or self.prefetch_obj is not None):
            raise ConfigurationError(
                "OptimizerHint.SKIP (skip=True) cannot be combined with "
                "select_related(), prefetch_related(), or prefetch(obj).",
            )
        if self.force_select and self.force_prefetch:
            raise ConfigurationError(
                "OptimizerHint cannot set both force_select and force_prefetch "
                "(use either select_related() or prefetch_related(), not both).",
            )
        if self.prefetch_obj is not None and not isinstance(self.prefetch_obj, Prefetch):
            raise ConfigurationError(
                "OptimizerHint.prefetch(obj) requires a django.db.models.Prefetch "
                f"instance; got {type(self.prefetch_obj).__name__}.",
            )
```

## What looks solid

### DRY recap

- **Existing patterns reused.** The file builds on `ConfigurationError` from `django_strawberry_framework/exceptions.py:1-45` (one of four documented exception types) and the runtime `Prefetch` import is consumed once at `hints.py:93` for the same validation pattern the walker re-applies at `optimizer/walker.py:511-516` (`_prefetch_hint_for_path` validating `prefetch_through`). The consumer surface in `types/base.py:383-398` (mapping-of-name-to-`OptimizerHint` shape gate) and `types/base.py:596-656` (key/value validation) is the matching gate on the `Meta.optimizer_hints` mapping shape; `hint_is_skip` is the canonical dispatch helper consumed at exactly two sites — `optimizer/walker.py:425` (planning) and `optimizer/extension.py:719` (schema audit). The `SKIP` sentinel pattern is parallel to (but distinct from) the `_MISSING` sentinel in `optimizer/_context.py`; both are module-level singletons that use object identity (`is`) for "no real value" dispatch.
- **New helpers considered.** None at this scope. A `Final[OptimizerHint]` annotation on `SKIP` would be the only structural change worth raising at the project pass (see Low §1). No new helpers required at the file-level granularity.
- **Duplication risk in the current file.** Two near-copies of the consumer-facing factory-name list inside `__post_init__` error messages: `"select_related(), prefetch_related(), or prefetch(obj)"` at `hints.py:86-87` and `"select_related() or prefetch_related()"` at `hints.py:91, 100-101`. These are intentional consumer-readable error prose, not dispatch keys, and they do not power any code path — collapsing them into a constant would actually hurt readability (each error names the specific subset of factories its collision rule covers). Flagged here for completeness; not a finding.

### Other positives

- Sentinel discipline is correct: `SKIP` is a frozen-dataclass singleton bound once after the class body (`hints.py:155`), every consumer uses identity-or-attribute via `hint_is_skip` (`hints.py:129-146`) rather than open-coding the check, and `tests/optimizer/test_extension.py:3063-3068` pins the contract across the supported shapes including `None`, the sentinel, a freshly-constructed skip-shaped hint, and an unrelated `object()`.
- The `hint_is_skip` defensive `getattr(hint, "skip", False)` fallback at `hints.py:146` is deliberately documented at `hints.py:130-138` as the schema audit's "never raises" pin, and `tests/optimizer/test_extension.py:3063-3068` exercises exactly that fallback. Same calibration the prior cycle's `_context.py` review called out — narrow-exception or defensive defaults documented *and* test-pinned are a positive pattern.
- `__post_init__` is the single source of truth for flag-combination validation. The four documented combination guards (`hints.py:83-102`) collectively prevent every shape the walker's priority dispatch (`optimizer/walker.py:425-499`) would silently drop. `tests/optimizer/test_hints.py:120-177` covers all four collision paths plus the `prefetch_obj`-must-be-`Prefetch` shape with one test per branch, naming the failure modes the way consumers see them.
- Public-API surface is correctly placed: `OptimizerHint` is re-exported from the top-level `django_strawberry_framework/__init__.py:22,33`, matching the consumer-facing import line shown in the module docstring (`hints.py:10`); only the helper `hint_is_skip` stays private to the optimizer subpackage (consumed at `walker.py:425` and `extension.py:719`), which is the right boundary — consumers should set hints, not read them.
- Cross-module consistency: `types/base.py:383-398` rejects non-`Mapping` shapes for `Meta.optimizer_hints` and `types/base.py:651-656` rejects non-`OptimizerHint` values. The two gates together with `__post_init__` cover every shape error before any optimization runs, and the error messages mention "OptimizerHint" consistently. GLOSSARY's `Meta.optimizer_hints` entry at `docs/GLOSSARY.md:625-648` documents exactly this layered validation contract ("hint field names must exist on the model; hint values must be `OptimizerHint` instances; invalid hints fail at type creation with `ConfigurationError`").
- `Prefetch` is imported at runtime rather than under `TYPE_CHECKING`, and the inline comment (`hints.py:35-39`) explains exactly why — the `isinstance` check at line 93 needs it. This is the kind of non-obvious-decision comment the comment-review pass usually flags as *missing*; here it is present and accurate.
- Static helper ran cleanly: one hotspot (`__post_init__`, 10 branch nodes at line 73) is justified — every branch is a flag-collision guard with its own test in `tests/optimizer/test_hints.py:130-177`. No TODOs, no repeated string literals, no ORM markers outside docstrings and the load-bearing `isinstance(prefetch_obj, Prefetch)` site at line 93.
- File fully unchanged across the 0.0.6→0.0.7 release boundary (last touch `1377802` in the 0.0.5 cycle that shipped the stale-comment fix); `tests/optimizer/test_hints.py` also unchanged. The 0.0.6 cycle reached `Status: verified` with three Lows recorded as project-pass calibration notes — the same three are carried forward here unchanged per the "Unchanged-file releases" worker-memory pattern.

### Summary

`optimizer/hints.py` is a small, focused public-API module that defines the typed `OptimizerHint` dataclass, four documented factory shapes (`SKIP`, `select_related()`, `prefetch_related()`, `prefetch(obj)`), and the canonical `hint_is_skip` dispatch helper. The construction-time validation at `__post_init__` rejects every flag combination the walker would silently drop, the sentinel is bound exactly once after the class body using the standard `ClassVar` + `# type: ignore[misc]` workaround, and downstream consumers (the walker's planning path, the extension's schema audit, and `types/base.py`'s `Meta.optimizer_hints` gates) all route through the documented surface. No High or Medium findings; the three Lows are calibration notes carried forward from the 0.0.6 cycle (file unchanged): `Final` on `SKIP` for tooling enforcement of the no-rebind invariant, the under-counted "four shapes" docstring framing that omits the deliberate no-op-empty shape, and a polish note on the layered priority of the four `__post_init__` guards. Test coverage in `tests/optimizer/test_hints.py` plus the cross-module pins in `tests/optimizer/test_extension.py:3063-3068` and `tests/types/test_base.py` is comprehensive.

---

## Fix report (Worker 2)

Consolidated single-spawn no-op pass. 0H/0M/3L — every Low is an explicit forward-looking deferral per Worker 1's own framing, and all three are carry-forwards from the 0.0.6 cycle (file unchanged across the 0.0.6→0.0.7 boundary; last touch `1377802` in 0.0.5).

### Files touched
- None. No source edit, no test edit, no docstring edit. Per the consolidated-single-spawn shape in `docs/review/worker-2.md:159-180` (all Lows explicitly forward-looking, no in-cycle edit required), this cycle collapses logic + comment + changelog into one spawn.

### Tests added or updated
- None. Worker 1's own dispositions defer all three Lows pending external triggers:
  - **Low 1 (`Final[OptimizerHint]` on `SKIP`)**: "Defer until a second module-level singleton lands that would benefit from the same `Final` annotation pattern; consolidate both at that point" (`rev-optimizer__hints.md:21`).
  - **Low 2 ("four shapes" docstring under-counts the no-op-empty fifth shape)**: "Defer until a consumer files a bug or doc question about the 'fifth shape'" (`rev-optimizer__hints.md:35`).
  - **Low 3 (`__post_init__` layered priority is intentional; "no change recommended")**: "Defer until a fifth `__post_init__` guard lands; at that point re-evaluate whether a single `_validate_flag_shape()` helper with a priority-ordered checklist reads better than four sequential `if`s" (`rev-optimizer__hints.md:48`).

### Validation run
- `uv run ruff format .` — pass, 118 files left unchanged (no-changes).
- `uv run ruff check --fix .` — pass, all checks passed (no-changes).
- No pytest run per `START.md` standing rule (no source edit, no test edit, no fix that requires focused-test confirmation).

### Notes for Worker 3
- **Shadow file**: not used. The artifact's citations were verified by direct Read of `django_strawberry_framework/optimizer/hints.py` against the line ranges Worker 1 quoted (lines 8-19, 35-39, 62, 69-71, 76-82, 83-102, 130-138, 144-146, 155). No re-grep needed for this cycle; no edits to verify.
- **No-op rationale**: This is the canonical "structurally stable file" no-op shape from worker-memory pattern (8) in the cycles 2-12 merge (`worker-memory/worker-2.md:15`) plus the `rev-optimizer__field_meta.md` cycle-13 carry-forward pattern (`worker-memory/worker-2.md:18-19`). Three citations support the no-op:
  - Worker 1's own line ("File fully unchanged across the 0.0.6→0.0.7 release boundary (last touch `1377802` in the 0.0.5 cycle that shipped the stale-comment fix); `tests/optimizer/test_hints.py` also unchanged. The 0.0.6 cycle reached `Status: verified` with three Lows recorded as project-pass calibration notes — the same three are carried forward here unchanged per the 'Unchanged-file releases' worker-memory pattern" at `rev-optimizer__hints.md:85`).
  - The DRY analysis line: "None — `hints.py` is at the right granularity" (`rev-optimizer__hints.md:7`) — no DRY delegation in scope, no helper extraction warranted, and the consumer-facing factory-name error prose duplications inside `__post_init__` are explicitly called out as "intentional consumer-readable error messages, not dispatch keys."
  - The cycle 13 precedent: `rev-optimizer__field_meta.md` closed `Not warranted` on identical grounds (zero-edit consolidated single-spawn, all Lows forward-looking, file structurally stable).
- **Intentionally-rejected findings with contradicting evidence**: none. All three Lows are explicitly forward-looking per Worker 1's own prose; this is not a false-premise rejection but a trigger-gated defer, which Worker 1 framed correctly. No rejection citation needed.
- **Deferred findings and their trigger conditions** (verbatim from Worker 1's dispositions, grep-discoverable for the project pass or a future cycle that satisfies a trigger):
  - **Low 1 trigger**: "a second module-level singleton lands that would benefit from the same `Final` annotation pattern" — at that point consolidate both. The parallel `_MISSING` sentinel in `optimizer/_context.py` already exists (called out at `rev-optimizer__hints.md:72`) but is internal-only, so it does not satisfy the trigger; the trigger fires when a **second public-API** singleton ships.
  - **Low 2 trigger**: "a consumer files a bug or doc question about the 'fifth shape'" — at that point either rename the framing to "four configurable shapes plus a no-op empty" or add a `# noqa: ERA001`-anchored TODO to the class docstring. Do not invent a fifth factory name proactively.
  - **Low 3 trigger**: "a fifth `__post_init__` guard lands" — at that point re-evaluate the four-sequential-`if`s shape vs. a `_validate_flag_shape()` helper with a priority-ordered checklist.

---

## Verification (Worker 3)

### Logic verification outcome
- Zero High, zero Medium, three Lows — all explicitly forward-looking per Worker 1's verbatim deferral prose, preserved by Worker 2 in `### Notes for Worker 3` with grep-discoverable triggers (Low 1: second public-API singleton; Low 2: consumer bug/doc question about fifth shape; Low 3: fifth `__post_init__` guard).
- `git diff -- django_strawberry_framework/optimizer/hints.py` empty; consistent with the "structurally stable file" no-op shape and Worker 1's "file fully unchanged across the 0.0.6→0.0.7 release boundary" claim at `rev-optimizer__hints.md:85`.

### DRY findings disposition
- DRY analysis reads "None — `hints.py` is at the right granularity" (`rev-optimizer__hints.md:7`); the consumer-facing factory-name error-prose duplications inside `__post_init__` are intentional consumer-readable messages, not dispatch keys. `hint_is_skip` is already extracted and consumed at exactly two sites (`walker.py:425`, `extension.py:719`). No helper extraction warranted; no carry-forward.

### Temp test verification
- No temp tests created; the no-op shape with zero source edits did not require behavior-pinning verification.

### Verification outcome
- `cycle accepted; verified` — terminal acceptance. Top-level `Status:` set to `verified`; `review-0_0_7.md` checkbox marked complete.

---

## Comment/docstring pass

No comment-pass edits in this cycle. All three Lows are explicitly forward-looking deferrals (no in-cycle action), and no logic fix landed that would change a docstring contract. The consolidated-single-spawn shape (`docs/review/worker-2.md:159-180`) explicitly covers this case: "All Lows are explicitly forward-looking per Worker 1's own prose [...]; no in-cycle edit required."

### Files touched
- None.

### Per-finding dispositions
- **Low 1 (`Final[OptimizerHint]` on `SKIP`)**: deferred per Worker 1's "Defer until a second module-level singleton lands that would benefit from the same `Final` annotation pattern; consolidate both at that point" (`rev-optimizer__hints.md:21`). No docstring edit warranted — the existing `# type: ignore[misc]` at line 155 already documents the unusual bind.
- **Low 2 ("four shapes" docstring under-counts no-op-empty fifth shape)**: deferred per Worker 1's "Defer until a consumer files a bug or doc question about the 'fifth shape'" (`rev-optimizer__hints.md:35`). The walker's `_apply_hint` docstring at `optimizer/walker.py:414-423` already names "the no-op empty form" explicitly, so the asymmetry between the two docstrings is acknowledged and intentional pending the trigger.
- **Low 3 (`__post_init__` layered priority guards)**: explicitly tagged "No change recommended — recording so a future 'collapse the four guards' simplification pass remembers the layered priority is intentional" (`rev-optimizer__hints.md:48`). Zero edit warranted by definition.

### Validation run
- `uv run ruff format .` — pass, no-changes (118 files left unchanged).
- `uv run ruff check --fix .` — pass, no-changes (all checks passed).

### Notes for Worker 3
- Same shape as the comment pass in `rev-optimizer__field_meta.md` (cycle 13): zero edits, all dispositions are forward-looking carry-forwards from the prior cycle. No docstring contract changed because no logic changed.

---

## Changelog disposition

### State
`Not warranted`.

### Reason
Two-citation bar (per `docs/review/worker-2.md:248-258`):

1. `AGENTS.md` line 21: "Do not update CHANGELOG.md unless explicitly instructed."
2. The active plan `docs/review/review-0_0_7.md` is silent on changelog authorization for this cycle (cycle 14: `rev-optimizer__hints.md`). The dispatch prompt for this spawn says "Changelog (Not warranted)" verbatim, which records the maintainer's expectation but does not authorize an edit — only state-2 `Warranted and edited` carries an edit authorization, and the dispatch is explicit that this is state 1.

Reinforcing the no-op disposition is the precedent chain: cycles 1-13 of 0.0.7 all closed `Not warranted`, building a thirteen-deep chain (per `worker-memory/worker-2.md:14`). This cycle extends that chain to fourteen-deep on the same controlling argument: no source edit, no test edit, no docstring edit, no consumer-visible behavior change.

Worker 1's verbatim positioning of all three Lows as forward-looking deferrals (Low 1: "Defer until a second module-level singleton lands"; Low 2: "Defer until a consumer files a bug or doc question"; Low 3: "Defer until a fifth `__post_init__` guard lands") is itself the strongest argument that no consumer-visible change occurred in this cycle.

### What was done
No `CHANGELOG.md` edit. The cycle closes with the artifact's Worker 2 sections filled and `Status: fix-implemented`; no other file in the working tree changed.

### Validation run
- `uv run ruff format .` — pass, no-changes.
- `uv run ruff check --fix .` — pass, no-changes.

---

## Iteration log

- (Append-only as re-passes occur)
