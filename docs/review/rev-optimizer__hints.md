# Review: `django_strawberry_framework/optimizer/hints.py`

## High:

None.

## Medium:

### Walker bypasses the `hint_is_skip` contract helper

`hint_is_skip` is documented as the single dispatch site for "is this a skip directive?" so the walker, schema audit, and any future caller never duplicate the `hint is OptimizerHint.SKIP or hint.skip` test. The schema audit in `optimizer/extension.py` uses it, but `optimizer/walker.py:294` open-codes the same expression. That defeats the centralisation the helper was added for: a future change to skip semantics (e.g. recognising a new sentinel, or tightening the defensive `getattr` fallback) silently diverges between the two call sites. Either route the walker through `hint_is_skip` or downgrade the helper to private and update its docstring to drop the "walker" claim — current state is the worst of both worlds.

```django_strawberry_framework/optimizer/hints.py:117:131
def hint_is_skip(hint: Any) -> bool:
    """... so callers (the walker, the schema audit) never duplicate the
    ``hint is OptimizerHint.SKIP or hint.skip`` dispatch."""
```

```django_strawberry_framework/optimizer/walker.py:294
if hint is OptimizerHint.SKIP or hint.skip:
```

### `prefetch_obj: Any` widens the documented `Prefetch | None` contract

The dataclass field is annotated `Prefetch | None`, validated only by `__post_init__` flag-combination checks, and `prefetch(cls, obj)` accepts `obj: Any` and assigns it directly to `prefetch_obj`. So `OptimizerHint.prefetch("entries__items")` constructs a hint that passes `__post_init__`, fails type checking only under a strict checker (which the codebase does not gate on), and then crashes in the walker when it appends a non-`Prefetch` to `plan.prefetch_related`. The factory either should type `obj: Prefetch` (matching the field annotation and the docstring's "specific Prefetch object") or validate `isinstance(obj, Prefetch)` in `__post_init__` so the failure surfaces at `Meta` build time — the same justification given in the existing post-init docstring for the other flag combinations.

```django_strawberry_framework/optimizer/hints.py:106:114
@classmethod
def prefetch(cls, obj: Any) -> OptimizerHint:
    """Use a specific ``Prefetch`` object for this field. ..."""
    return cls(prefetch_obj=obj)
```

## Low:

### `Prefetch` is `TYPE_CHECKING`-only but used in a runtime field annotation

`from __future__ import annotations` makes the `Prefetch | None` annotation on the dataclass field deferred-string evaluated, so the `TYPE_CHECKING` import is fine today — but `dataclass(frozen=True)` does not currently call `typing.get_type_hints`, so any later refactor that turns on `eq=True`-with-hash-recompute or that introspects `__dataclass_fields__[...].type` via `get_type_hints` will need `Prefetch` at runtime and fail. A one-line comment by the `TYPE_CHECKING` guard noting the dependency on PEP 563 + dataclass internals would prevent a future quiet regression.

```django_strawberry_framework/optimizer/hints.py:33:34
if TYPE_CHECKING:  # pragma: no cover
    from django.db.models import Prefetch
```

### Error messages name `force_select`/`force_prefetch` but factory names are `select_related`/`prefetch_related`

`ConfigurationError` messages use the internal flag names (`force_select`, `force_prefetch`), but the documented consumer surface is `OptimizerHint.select_related()` / `OptimizerHint.prefetch_related()`. A consumer who only ever uses the factories will see an exception that names attributes they did not set. Rephrasing the messages around the factory names (or pointing at both) lowers the cognitive cost of the error.

```django_strawberry_framework/optimizer/hints.py:78:90
raise ConfigurationError(
    "OptimizerHint cannot set both force_select and force_prefetch.",
)
```

### `hint_is_skip(None) -> False` is unreachable through the documented surface

The walker calls `hint_is_skip` (via `extension.py`) only after `hints.get(field_name)` returns a non-`None` value (the optimizer iterates `hints.items()` in the audit path). The `if hint is None: return False` guard is defensive and harmless, but worth a `# pragma: no cover` or a comment noting why it stays, since coverage is gated at 100% and any future refactor that drops the call site will leave it as dead code without explanation.

```django_strawberry_framework/optimizer/hints.py:127:128
if hint is None:
    return False
```

## What looks solid

- Static helper (`scripts/review_inspect.py`) was run; overview lives at `docs/review/shadow/django_strawberry_framework__optimizer__hints.overview.md`.
- `@dataclass(frozen=True)` plus `__post_init__` validation is the right shape: immutability for hashing/identity (`OptimizerHint.SKIP` sentinel), and conflicting-flag rejection happens at `Meta` build time, not query time, per the post-init docstring.
- The class-level `SKIP: ClassVar[OptimizerHint]` + post-body rebind pattern is unusual but is explained by the inline comment block at lines 134-140 and is the only way to reconcile the dataclass decorator with a single canonical sentinel — keep the comment.
- `Repeated string literals` section is empty; no folder-pass DRY signal from this file in isolation.
- Module docstring carries the consumer-facing example and the architectural justification ("lives in optimizer because the walker is the primary consumer") — exactly the right surface for a re-exported public API.

---

### Summary:

`hints.py` is the typed-wrapper rewrite of the earlier string/dict/`Prefetch` polymorphic hint surface and is correctly small and frozen. Two Medium findings: the centralisation helper `hint_is_skip` is bypassed by the walker that the docstring names as its primary caller (so it currently centralises nothing), and the `prefetch(obj: Any)` factory escapes the `Prefetch | None` contract that the rest of the module enforces. Folder-pass follow-ups: confirm at the optimizer folder pass that `hint_is_skip` becomes the single dispatch site (walker + extension agree), and check whether other callers of `OptimizerHint.SKIP` identity tests exist in `plans.py` / `walker.py` that should also route through the helper.

## Verification

PASS — Worker 3, 2026-05-10.

- Medium 1 (walker bypass): `optimizer/walker.py:294` now calls `hint_is_skip(hint)`; `hint_is_skip` imported alongside `OptimizerHint`. Centralisation contract restored.
- Medium 2 (prefetch obj Any): `prefetch(cls, obj: Prefetch)` retyped; `__post_init__` now does `isinstance(self.prefetch_obj, Prefetch)` and raises `ConfigurationError` at build time. New `test_prefetch_obj_rejects_non_prefetch_value` pins both factory and direct-construction rejection.
- Low 1 (TYPE_CHECKING-only): `Prefetch` moved to runtime import; explanatory comment block added at lines 35-39 noting the `isinstance` dependency.
- Low 2 (error message naming): all four `ConfigurationError` messages rephrased to cite factory names (`SKIP`, `select_related()`, `prefetch_related()`, `prefetch(obj)`).
- Low 3 (`hint_is_skip(None) -> False`): intentional retain documented inline (lines 139-143) explaining the defensive-`getattr`-style shape choice.
- `uv run pytest tests/optimizer -q` → 229 passed; hints.py file coverage 100%. Repo-wide `fail_under=100` exits non-zero under focused tests as expected (carry-forward from prior memory).
