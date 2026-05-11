# Review: `django_strawberry_framework/optimizer/_context.py`

## High:

None.

## Medium:

### `stash_on_context` swallows legitimate write failures on dict contexts

The dict-fallback branch catches both `TypeError` and `KeyError` on `context[key] = value`. For a real `dict` (or any mutable mapping with a normal `__setitem__`), neither exception is expected on a plain string-keyed assignment — `KeyError` in particular is not raised by `dict.__setitem__`. Catching `KeyError` here is dead defensive code; catching `TypeError` is the right guard for `MappingProxyType` and frozen mappings, but pairing it with `KeyError` suggests the author was uncertain which exception fires for which frozen shape. The risk is that a *future* mapping subclass that raises a custom error (e.g., a `TypedDict`-like guarded mapping) gets silently swallowed when it should surface. Recommend narrowing to `TypeError` only and dropping `KeyError`, or documenting why `KeyError` is included.

```django_strawberry_framework/optimizer/_context.py:67:70
    try:
        context[key] = value
    except (TypeError, KeyError):
        return
```

### No test coverage cited for the frozen-context skip path

The module's docstring explicitly enumerates four context shapes (None, object, dict, frozen) and the write helper has three exception-swallowing branches. The package coverage gate is 100%, so every line is presumably hit, but the artifact should flag for the folder/project pass that the *behavioral* contract — "frozen context silently skips, does not raise" — needs an explicit test that constructs a `MappingProxyType` (or frozen dataclass) context and asserts the resolver chain continues. If coverage is hitting these `except` branches only via incidental paths rather than a named test, the contract is under-pinned. Follow-up for the optimizer folder pass once `extension.py` and `resolvers.py` are reviewed and their test surface is visible.

```django_strawberry_framework/optimizer/_context.py:45:70
def stash_on_context(context: Any, key: str, value: Any) -> None:
    ...
    try:
        setattr(context, key, value)
        return
    except (AttributeError, TypeError):
        pass
    try:
        context[key] = value
    except (TypeError, KeyError):
        return
```

## Low:

### Module-level constants would be clearer grouped or namespaced

Five `DST_OPTIMIZER_*` string constants live at module top with no grouping comment, no `__all__`, and no enum/dataclass container. They are the wire-keys for the optimizer↔resolver hand-off contract — arguably the most important surface in the file — yet they are visually indistinguishable from any other module global. Consider either an `__all__` listing them explicitly, a short "Context keys" comment header, or (heavier) a frozen dataclass / `Enum` to make the contract namespace explicit. Not a correctness issue; flagged because the folder-pass DRY check will compare these literals against `extension.py`, `walker.py`, and `types/resolvers.py`.

```django_strawberry_framework/optimizer/_context.py:24:28
DST_OPTIMIZER_PLAN = "dst_optimizer_plan"
DST_OPTIMIZER_FK_ID_ELISIONS = "dst_optimizer_fk_id_elisions"
DST_OPTIMIZER_PLANNED = "dst_optimizer_planned"
DST_OPTIMIZER_LOOKUP_PATHS = "dst_optimizer_lookup_paths"
DST_OPTIMIZER_STRICTNESS = "dst_optimizer_strictness"
```

### `get_context_value` dict-vs-object dispatch is order-sensitive but undocumented

`isinstance(context, dict)` is checked before the `getattr` fallback. A consumer that subclasses `dict` *and* exposes attribute access (e.g., a `Box`-style mapping) will take the dict branch, which is the right call for Strawberry's normal usage but worth a one-line inline comment so the next maintainer doesn't "fix" it by reversing the order. Pure docstring polish, no behavior change.

```django_strawberry_framework/optimizer/_context.py:38:42
    if context is None:
        return default
    if isinstance(context, dict):
        return context.get(key, default)
    return getattr(context, key, default)
```

## What looks solid

- Helper ran cleanly; no control-flow hotspots, no TODOs, no repeated literals within the file. The module is small (~70 lines) and single-purpose.
- The `None`-short-circuit on both helpers correctly matches Strawberry's "no context_value" default and removes the need for guard code at every call site.
- Read helper is genuinely read-only — no mutation, no exception handling needed — which matches the docstring's contract.
- Write helper's `setattr` → `__setitem__` → silent-skip fallback chain is the right shape for the documented four context kinds, and the docstring explicitly justifies the silent skip ("nice-to-have, not a correctness invariant"). That justification belongs in the source and is in the source.
- Module docstring explicitly names the centralization rationale ("a future broadening … only has to land in one place rather than across `optimizer/extension.py` and `types/resolvers.py`"), which is exactly the kind of cross-module ownership note the review process wants captured at the source site.

---

### Summary:

Small, well-scoped helper module with a clear centralization rationale. No High issues. One Medium calibration on the `KeyError` catch in the dict-fallback branch (likely dead defensive code), and one Medium follow-up routed to the optimizer folder pass to confirm the frozen-context skip path has a named behavioral test rather than incidental coverage. Lows are namespace/grouping polish on the five `DST_*` literals (which the folder pass should cross-check against sibling files for the wire-key contract) and a one-line comment on dispatch order in `get_context_value`. The leading-underscore module name signals package-private status; that intent should be confirmed during the optimizer folder pass when the `__init__.py` re-export contract is set.

## Verification

PASS — 2026-05-10.

- Medium 1 (KeyError narrowing): addressed. `except (TypeError, KeyError)` narrowed to `except TypeError`, with a source comment justifying the narrow. New test `test_stash_does_not_swallow_unexpected_exceptions_from_setitem` in `tests/optimizer/test_extension.py` pins the new contract via a `dict` subclass whose `__setitem__` raises `RuntimeError` and asserts the error surfaces.
- Medium 2 (named test for frozen-context skip path): deferred to the optimizer folder pass per the artifact's explicit "Follow-up for the optimizer folder pass" wording. Existing `test_stash_falls_back_to_setitem_on_typeerror` continues to exercise the typeerror branch; explicit `MappingProxyType` assertion is left for the folder-pass cycle.
- Low 1 (constants grouping / `__all__`): retained intentionally — artifact tagged it "Not a correctness issue" and routed cross-file literal comparison to the folder-pass DRY check.
- Low 2 (dispatch-order comment in `get_context_value`): addressed. Inline comment added explaining why `dict` is checked before the `getattr` fallback.
- Validation: `uv run pytest tests/optimizer/test_extension.py -q` → 87 passed. The focused-run coverage gate failure is a known harmless side effect of the global `fail_under=100`.
