# Review: `django_strawberry_framework/optimizer/hints.py`

Status: verified

## DRY analysis

- **Existing patterns reused.** The file builds on `ConfigurationError` from `django_strawberry_framework/exceptions.py:1-45` (one of four documented exception types) and the runtime `Prefetch` import is consumed once at `hints.py:93` for the same validation pattern the walker re-applies at `optimizer/walker.py:471-491`. The consumer surface in `types/base.py:382-387` and `types/base.py:593-598` is the matching gate on the `Meta.optimizer_hints` mapping shape (mapping-of-name-to-`OptimizerHint`); `hint_is_skip` is the canonical dispatch helper consumed at exactly two sites — `optimizer/walker.py:412` (planning) and `optimizer/extension.py:683` (schema audit). The `SKIP` sentinel pattern is parallel to (but distinct from) the `_MISSING` sentinel in `optimizer/_context.py:40-42`; both are module-level singletons that use object identity (`is`) for "no real value" dispatch.
- **New helpers a fix might justify.** None at this scope. A `Final[OptimizerHint]` annotation on `SKIP` would be the only structural change worth raising at the project pass (see Low §1). No new helpers required.
- **Duplication risk in the current file.** Two near-copies of the consumer-facing factory-name list inside `__post_init__` error messages: `"select_related(), prefetch_related(), or prefetch(obj)"` at `hints.py:86` and `"select_related() or prefetch_related()"` at `hints.py:91, 101`. These are intentional consumer-readable error prose, not dispatch keys, and they do not power any code path — collapsing them into a constant would actually hurt readability. Flagged here for completeness; not a finding.

## High:

None.

## Medium:

None.

## Low:

### `SKIP` is not annotated `Final`, leaving the sentinel rebindable from any consumer module

`OptimizerHint.SKIP` is the documented sentinel identity. `hint_is_skip` performs an `is` check against it at `hints.py:144`, and the consumer-surface docstring at `hints.py:8-19` advertises `OptimizerHint.SKIP` as the canonical "skip this relation" value. The current declaration is `ClassVar[OptimizerHint]` (line 71) with a post-class-body bind at line 155 using `# type: ignore[misc]`. `ClassVar` blocks the dataclass decorator from treating `SKIP` as a field; it does not block rebinding from outside. A consumer (or a test fixture cleanup that miscounts state) writing `OptimizerHint.SKIP = OptimizerHint(skip=True)` would silently break every `hint is OptimizerHint.SKIP` identity check across the package — `hint_is_skip` still returns the right answer for skip-shaped hints because of the `getattr(hint, "skip", False)` fallback, but the walker's planning path through `_apply_hint` would no longer match `True` on the first branch and any optimization-plan-cache key that included sentinel identity would diverge. `typing.Final[OptimizerHint]` (already used elsewhere in the codebase for module-level singletons) would make the rebind a mypy/ruff failure without changing runtime behavior. This is Low because the `# type: ignore[misc]` already documents that the bind is unusual and no test today exercises rebinding; promote if a second sentinel lands and the pattern duplicates.

```django_strawberry_framework/optimizer/hints.py:69:71
    # Populated after the class body via ``OptimizerHint(skip=True)``.
    # Declared here as a ClassVar so the dataclass decorator ignores it.
    SKIP: ClassVar[OptimizerHint]  # noqa: N815
```

```django_strawberry_framework/optimizer/hints.py:155:155
OptimizerHint.SKIP = OptimizerHint(skip=True)  # type: ignore[misc]
```

### `OptimizerHint()` with no flag set has no canonical "no-op hint" name, but two test sites construct exactly that shape

`tests/optimizer/test_walker.py:1188-1204` documents that `OptimizerHint()` with no args is a deliberate no-op the walker falls back through. `_apply_hint` at `optimizer/walker.py:412-468` returns `False` in that case so the cardinality dispatch runs. The class has no factory method for this shape (e.g., no `OptimizerHint.default()` or class-level `OptimizerHint.NOOP`) and no docstring sentence on the class itself naming this shape — the four-shapes language at `__post_init__`'s docstring (line 76-82) actually claims "four documented shapes" which under-counts: there are five reachable shapes (skip, prefetch_obj, force_select, force_prefetch, no-op-empty). The walker's `_apply_hint` docstring at `optimizer/walker.py:404-410` repeats the "four documented hint shapes" framing. This is Low because the no-op shape is genuinely the *absence* of intent and naming it would mostly invite consumers to set it where omitting the key is clearer. Worth recording so the next maintainer who reads `_apply_hint`'s comment doesn't go looking for a missing fifth branch.

```django_strawberry_framework/optimizer/hints.py:76:82
        The walker consumes flags in a strict priority order
        (``skip`` → ``prefetch_obj`` → ``force_select`` → ``force_prefetch``),
        so any combination beyond the four documented shapes silently
        loses the lower-priority directive.  Raising here surfaces the
        mistake at ``Meta.optimizer_hints`` build time instead of at
        query time.
```

### `__post_init__` re-validates `isinstance(prefetch_obj, Prefetch)` but the field annotation is `Prefetch | None`

The dataclass annotation at line 62 (`prefetch_obj: Prefetch | None = field(default=None, repr=False)`) is stringified by `from __future__ import annotations`, so it has no runtime enforcement. The `isinstance` check at line 93 fills that gap and is the load-bearing guard documented at lines 35-39. That works. The Low-tier polish is that the `__post_init__` body silently re-checks the type *after* the `skip and (...)` branch above; if a consumer passes `OptimizerHint(skip=True, prefetch_obj="bad")`, the `skip` collision error fires first and the type error is never raised. The two messages cover overlapping but distinct mistakes, and the order is deliberate (skip-collision is the more useful diagnostic). No change recommended — recording so a future "collapse the four guards" simplification pass remembers the layered priority is intentional.

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

- Sentinel discipline is correct: `SKIP` is a frozen-dataclass singleton bound once after the class body (`hints.py:155`), every consumer uses identity-or-attribute via `hint_is_skip` (`hints.py:129-146`) rather than open-coding the check, and `tests/optimizer/test_extension.py:2961-2971` pins the contract across the supported shapes including `None`, the sentinel, a freshly-constructed skip-shaped hint, and an unrelated `object()`.
- The `hint_is_skip` defensive `getattr(hint, "skip", False)` fallback at `hints.py:146` is deliberately documented at `hints.py:130-138` as the schema audit's "never raises" pin, and `tests/optimizer/test_extension.py:2971` (`assert hint_is_skip(object()) is False`) exercises exactly that fallback. This is the same calibration the prior cycle's `_context.py` review called out — narrow-exception or defensive defaults documented *and* test-pinned are a positive pattern worth carrying forward.
- `__post_init__` is the single source of truth for flag-combination validation. The four documented combination guards (`hints.py:83-102`) collectively prevent every shape the walker's priority dispatch (`optimizer/walker.py:412-468`) would silently drop. `tests/optimizer/test_hints.py:130-160` covers all four collision paths plus the `prefetch_obj`-must-be-`Prefetch` shape with one test per branch, naming the failure modes the way consumers see them.
- Public-API surface is correctly placed: `OptimizerHint` is re-exported from the top-level `django_strawberry_framework/__init__.py:21,31`, matching the consumer-facing import line shown in the module docstring (`hints.py:10`); only the helper `hint_is_skip` stays private to the optimizer subpackage (consumed at `walker.py:412` and `extension.py:683`), which is the right boundary — consumers should set hints, not read them.
- Cross-module consistency: `types/base.py:382-387` rejects non-`Mapping` shapes for `Meta.optimizer_hints` and `types/base.py:593-598` rejects non-`OptimizerHint` values. The two gates together with `__post_init__` cover every shape error before any optimization runs, and the error messages mention "OptimizerHint" consistently (key matching point for `tests/optimizer/test_extension.py:2208` and `tests/types/test_base.py:153,256,266`).
- `Prefetch` is imported at runtime rather than under `TYPE_CHECKING`, and the inline comment (`hints.py:35-39`) explains exactly why — the `isinstance` check at line 93 needs it. This is the kind of non-obvious-decision comment the comment-review pass usually flags as *missing*; here it is present and accurate.
- Static helper ran cleanly: one hotspot (`__post_init__`, 10 branch nodes at line 73) is justified — every branch is a flag-collision guard with its own test in `tests/optimizer/test_hints.py:121-160`. No TODOs, no repeated string literals, no ORM markers outside docstrings and the load-bearing `isinstance(prefetch_obj, Prefetch)` site.

### Summary

`optimizer/hints.py` is a small, focused public-API module that defines the typed `OptimizerHint` dataclass, four documented factory shapes (`SKIP`, `select_related()`, `prefetch_related()`, `prefetch(obj)`), and the canonical `hint_is_skip` dispatch helper. The construction-time validation at `__post_init__` rejects every flag combination the walker would silently drop, the sentinel is bound exactly once after the class body using the standard `ClassVar` + `# type: ignore[misc]` workaround, and downstream consumers (the walker's planning path, the extension's schema audit, and `types/base.py`'s `Meta.optimizer_hints` gates) all route through the documented surface. No High or Medium findings; the three Low items are calibration notes for the project pass: `Final` on `SKIP` for tooling enforcement of the no-rebind invariant, the under-counted "four shapes" docstring framing that omits the deliberate no-op-empty shape, and a polish note on the layered priority of the four `__post_init__` guards. Test coverage in `tests/optimizer/test_hints.py` plus the cross-module pins in `tests/optimizer/test_extension.py:2961-2971` and `tests/types/test_base.py:153-266` is comprehensive.

---

## Fix report (Worker 2)

### Files touched

- None. All three Low findings are recording-only / forward-looking per Worker 1's explicit prose in the artifact.

### Tests added or updated

- None.

### Validation run

- `uv run ruff format .` — pass (no changes; "100 files left unchanged").
- `uv run ruff check --fix .` — pass (no changes; "All checks passed!").
- No `pytest` run per worker-2 dicta on no-op cycles.

### Notes for Worker 3

- No shadow file used; no in-cycle edits warranted by the artifact.
- Consolidated single-pass no-op cycle: 0H / 0M / 3L, all three Lows recording-only or forward-looking — see Comment/docstring pass below for the per-finding disposition and Changelog disposition below for the no-changelog reason.

---

## Comment/docstring pass

### Files touched

- None.

### Low findings disposition

- **L1 — `SKIP` not annotated `Final`:** Deferred. Worker 1's prose explicitly says "the `# type: ignore[misc]` already documents that the bind is unusual and no test today exercises rebinding; promote if a second sentinel lands and the pattern duplicates." No in-cycle edit.
- **L2 — under-counted "four shapes" docstring framing:** Recording-only. Worker 1's prose explicitly says "Worth recording so the next maintainer who reads `_apply_hint`'s comment doesn't go looking for a missing fifth branch." No in-cycle edit.
- **L3 — layered priority of the four `__post_init__` guards:** Recording-only. Worker 1's prose explicitly says "No change recommended — recording so a future 'collapse the four guards' simplification pass remembers the layered priority is intentional." No in-cycle edit.

---

## Changelog disposition

- **Warranted?** Not warranted.
- **Reason:** No source changes were made; the entire cycle is recording-only per the artifact's own Low-finding dispositions. Per `AGENTS.md` ("Do not update CHANGELOG.md unless explicitly instructed.") and the active plan (no changelog authorization for this cycle item), no `CHANGELOG.md` edit is appropriate.
- **What was done:** No edit.
- **Validation:** `uv run ruff format .` pass (no changes); `uv run ruff check --fix .` pass (no changes).

---

## Verification (Worker 3)

### Logic verification outcome

- **High:** None — accepted.
- **Medium:** None — accepted.
- **L1 — `SKIP` not annotated `Final`:** accepted as recording-only per Worker 1's prose ("promote if a second sentinel lands and the pattern duplicates"). Spot-checked source: `SKIP` is declared `ClassVar[OptimizerHint]` at line 71 and bound exactly once at line 155 via `OptimizerHint(skip=True)` with `# type: ignore[misc]`. The `hint_is_skip` getattr-fallback at line 146 (`bool(getattr(hint, "skip", False))`) preserves correct dispatch even if a rebind ever happened, which is exactly the calibration Worker 1 cites for keeping this Low.
- **L2 — under-counted "four shapes" docstring framing:** accepted as recording-only per Worker 1's prose ("Worth recording so the next maintainer ... doesn't go looking for a missing fifth branch"). No source change appropriate; the deliberate no-op-empty shape is the *absence* of intent, and naming it in the class docstring would invite consumers to set it where omitting the key is clearer.
- **L3 — layered priority of the four `__post_init__` guards:** accepted as recording-only per Worker 1's prose ("No change recommended"). Verified the four guards at lines 83-102 cover (skip + any other), (force_select + force_prefetch), (prefetch_obj is not Prefetch), and (prefetch_obj + force_*); priority is intentional so the more useful diagnostic fires first.

### DRY findings disposition

No in-file duplication beyond the deliberately-parallel error prose at lines 86, 91, and 101 (consumer-readable factory names in `ConfigurationError` messages). The SKIP-vs-`_MISSING` sentinel pattern noted in the DRY analysis is parallel-by-design across `optimizer/hints.py` and `optimizer/_context.py:40-42` — both are module-level singletons using identity dispatch, and collapsing them would couple two unrelated abstractions. Accepted.

### Temp test verification

None used.

### Verification outcome

cycle accepted; verified.
