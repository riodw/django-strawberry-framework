# Review: `django_strawberry_framework/utils/relations.py`

## High:

None.

## Medium:

None.

## Low:

### `field: Any` weakens the documented contract

The docstring says "Classify a Django relation field", but the parameter is annotated `Any`. Every caller in the package (`types/base.py:493`, `types/converters.py:224`, `types/resolvers.py:178`, `optimizer/walker.py:60`) hands in a real Django relation field descriptor whose shape always exposes the four flags being read. A narrower annotation (or at least a `Protocol` capturing the four read attributes `many_to_many`, `one_to_many`, `one_to_one`, `auto_created`) would make the public contract match the consumer-visible promise. This is the same shape-guard-asymmetry calibration carried forward from `field_meta.py`/`converters.py` per worker memory — recording it here as Low because the file's behaviour is correct and `getattr(..., False)` already defends against missing attributes.

```django_strawberry_framework/utils/relations.py:10:16
def relation_kind(field: Any) -> RelationKind:
    """Classify a Django relation field by GraphQL/runtime cardinality."""
    if getattr(field, "many_to_many", False) or getattr(field, "one_to_many", False):
        return "many"
    if getattr(field, "one_to_one", False) and getattr(field, "auto_created", False):
        return "reverse_one_to_one"
    return "forward_single"
```

### `RelationKind` excludes a documented fourth shape used by tests

The `Literal` enumerates three kinds: `"many"`, `"reverse_one_to_one"`, `"forward_single"`. However `tests/test_registry.py:566` passes `relation_kind="reverse_many_to_one"` to a `PendingRelation` construction, indicating callers can produce a fourth kind that this central classifier cannot. Either the `Literal` should grow to cover that shape and `relation_kind()` should learn to detect it (auto-created + `one_to_many`, i.e. reverse FK), or that test value is wrong and should be reconciled. Worth flagging as a Low for the folder pass / types folder cross-check rather than a per-file defect since the classifier itself is internally consistent.

```django_strawberry_framework/utils/relations.py:7:7
RelationKind: TypeAlias = Literal["many", "reverse_one_to_one", "forward_single"]
```

## What looks solid

- Helper is a single 7-line pure function with clear branch order: many-side first, then reverse-O2O via `auto_created`, then forward-single fallback. The ordering matches the four-flag Django relation matrix.
- Dedicated unit tests at `tests/utils/test_relations.py` name each branch (M2M, O2M, auto-created O2O, forward single) — branch coverage is pinned by named tests, addressing the "missing tests for important branches" calibration carried forward from converters/walker hotspots.
- The module has zero Django/Strawberry imports — it is a stdlib-leaf typing helper, safe to import from any layer (converters, base, resolvers, walker all do, no circular risk).
- `RelationKind: TypeAlias` is exported via the `..utils.relations import RelationKind` path used by `types/relations.py:9` and feeds into `PendingRelation.relation_kind`, giving a single string-literal source of truth for relation cardinality across the package.
- Static helper not run: file is 16 lines, well below the 150-line threshold and outside `optimizer/`/`types/`, so the helper is not mandatory per `docs/review/REVIEW.md` "When to run the helper".

---

### Summary:

`utils/relations.py` is a small, dependency-free classifier that does one job correctly and is exercised by named per-branch tests. No High or Medium findings. Two Lows worth carrying to the `utils/` folder pass and the project pass: (1) the `field: Any` annotation should tighten to a `Protocol` matching the four flags actually read, consistent with the package-wide shape-guard stance carry-forward; (2) the `RelationKind` `Literal` is missing a `"reverse_many_to_one"` value that `tests/test_registry.py:566` already constructs against `PendingRelation`, surfacing a cross-file inconsistency that the folder/project pass should reconcile (either extend the classifier + alias, or fix the test value). Worker memory's "documented contract not enforced" theme is *not* triggered here — the file's contract is small and the tests pin it.

## Verification

PASS. Worker 2 addressed Low 1 by introducing a `@runtime_checkable` `_RelationFieldLike` Protocol enumerating the four read flags and narrowing the `relation_kind(field: ...)` annotation; the docstring on the Protocol records that `getattr(..., False)` in the body still defends against shapes that omit a flag (matches the artifact's recommendation exactly). Low 2 (`RelationKind` missing `"reverse_many_to_one"`) is explicitly routed in the artifact body to the `utils/` folder pass / project pass, so retain-without-change is contract-sanctioned. `uv run pytest tests/utils -q --no-cov` → 9 passed (4 in `tests/utils/test_relations.py` covering each branch). No new test required — Low 1 is a pure type-annotation tightening with no runtime behaviour change, and existing per-branch tests still pin the classifier semantics. Checkbox marked complete in `docs/review/review-0_0_4.md`.
