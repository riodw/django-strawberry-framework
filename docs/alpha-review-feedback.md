# Review Feedback: Optimizer Beyond Diff

## Scope reviewed

- `docs/spec-optimizer_beyond.md`
- `django_strawberry_framework/optimizer/extension.py`
- `django_strawberry_framework/optimizer/walker.py`
- `django_strawberry_framework/types/base.py`
- `django_strawberry_framework/types/resolvers.py`

This feedback only covers the current diff.

## Findings

### 1. `extension.py`'s B6 pseudo-code still points at the old audit design

Priority: P1

`docs/spec-optimizer_beyond.md` now settles B6 on a schema-reachable audit plus a public `registry.iter_types()` helper. But the source-site TODO in `django_strawberry_framework/optimizer/extension.py` still sketches the superseded version:

- iterating `registry._types.items()` directly
- auditing every registered type instead of only schema-reachable ones
- describing a generic “strict mode” instead of the settled `strictness` API

Since these TODO blocks exist to anchor future implementation, this one is now actively misleading. If someone implements B6 from the source comment instead of the spec, they will build the wrong audit and get false positives for registered-but-unexposed types.

Recommended fix:

- update the B6 TODO block in `extension.py` to match the spec’s settled shape
- reference `registry.iter_types()`
- mention schema reachability explicitly
- use `strictness == "raise"` instead of the older “strict mode” phrasing

### 2. The B4 pseudo-code in `walker.py` and `types/base.py` still reflects the pre-`OptimizerHint` design

Priority: P2

The spec now makes a clear call: `Meta.optimizer_hints` values are `OptimizerHint` instances, not a loose mix of strings, dicts, and raw `Prefetch` objects. But the source-site guidance still sketches the older API:

- `walker.py` checks for `"skip"`, raw `Prefetch`, and `{"select_related": True}`
- `types/base.py` only mentions unknown-field validation and does not mention type validation for `OptimizerHint`

That drift matters because these comments sit exactly where the implementation will land. They should steer future work toward the settled public contract, not back toward the discarded exploratory shape.

Recommended fix:

- update the walker TODO to use `OptimizerHint.SKIP`, `.force_select`, `.force_prefetch`, and `.prefetch_obj`
- update the `types/base.py` TODO to mention both unknown-field validation and `OptimizerHint` instance validation

### 3. The B3/B5 source comments still use the older context/strict API shape

Priority: P2

The finalized spec now says:

- B3 uses `strictness: Literal["off", "warn", "raise"]`
- B5 stashes onto `info.context` with `setattr(...)` first and dict fallback second

But the source TODOs still preserve older versions of the design:

- `extension.py` says `when strict=True`
- `types/resolvers.py` says `DjangoOptimizerExtension(strict=True)`
- `extension.py`'s B5 pseudo-code only shows `setattr(...)`, not the dict fallback

These are not runtime bugs today, but they are implementation traps. The next person wiring B3/B5 from the nearby comment could easily reintroduce the older boolean API or forget the dict-context fallback that the spec now treats as part of the contract.

Recommended fix:

- change all B3 TODO wording to `strictness`, not `strict`
- update the B5 pseudo-code in `extension.py` to show the `setattr` / `__setitem__` fallback pattern
- keep the resolver-side B3 example aligned with the same terminology

## Overall assessment

The spec itself is in much better shape now. The remaining issue is mostly one of source-site guidance: several TODO-anchored pseudo-code blocks have drifted behind the spec that is supposed to govern them. I would sync those comments now while the decisions are fresh, so the next implementation pass does not accidentally follow obsolete scaffolding.
