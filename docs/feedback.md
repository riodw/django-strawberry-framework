# Foundation slice review — follow-up after fixes

Re-reviewed against the previous round's feedback. Test suite: **303 passed, 4 skipped, 0 failed** under `uv run pytest tests --no-cov -q`. The slice is now in a green state.

## Previous-round feedback: status

### P1 — must-fix items

- **P1-1 (annotation-only override silently broken for many-side relations).** **Fixed.** `DjangoTypeDefinition` now carries `consumer_annotated_relation_fields` and `consumer_assigned_relation_fields` as separate sets, with `consumer_authored_fields` kept as the union for compatibility. `finalize_django_types()` phase 2 passes only `consumer_assigned_relation_fields` as `skip_field_names`, so annotation-only overrides keep their generated relation resolver. Verified by the new tests `test_annotation_only_relation_override_keeps_generated_resolver` and `test_assigned_relation_field_override_keeps_consumer_resolver` in `tests/types/test_base.py`. The annotation-only test asserts `items_field.base_resolver.wrapped_func.__name__ == "resolve_items"`, the assigned-override test asserts the consumer's method is the resolver. Good split, good coverage.

- **P1-2 (CI red).** **Fixed.** Existing optimizer tests in `tests/optimizer/test_extension.py`, `tests/optimizer/test_field_meta.py`, `tests/types/test_resolvers.py`, and `tests/types/test_base.py` now call `finalize_django_types()` between class declaration and `strawberry.Schema(...)`. Full suite passes.

- **P1-3 (silent class-attribute shadow disables resolver).** **Fixed.** `_consumer_assigned_relation_fields` validates that any class-dict value on a relation field name is a `StrawberryField`; anything else (e.g., `items = None`) raises `ConfigurationError("… shadows a Django relation field with an unsupported class attribute …")` with explicit guidance to use an annotation override or `strawberry.field(resolver=...)`. New test `test_relation_field_class_attribute_shadowing_raises` pins the contract.

### P2 — should-fix items

- **P2-1 (stale `_attach_relation_resolvers` docstring).** **Fixed.** Docstring now points at `finalize_django_types()` and documents `skip_field_names`.
- **P2-2 (duplicate registry lookup in collection path).** **Fixed.** `_build_annotations` now does a single `target_type = registry.get(...)` and inlines the resolved-vs-pending branch using `PendingRelationAnnotation` directly; `convert_relation` is no longer called from this path. Imports in `base.py` were updated to drop `convert_relation` and pull `resolved_relation_annotation` instead.
- **P2-3 (confusing failure when finalize is forgotten).** **Fixed via metaclass.** `PendingRelationAnnotation` uses a metaclass whose `__repr__` returns `<unfinalized DjangoType relation; call finalize_django_types() before constructing strawberry.Schema>`. Strawberry's `TypeError(f"Unexpected type '{type_}'")` interpolates that repr, so the user sees a self-explanatory error if they forget to finalize. Asserted by `test_relation_unregistered_target_raises`.
- **P2-4 (`_is_default_get_queryset` set twice).** **Fixed.** The duplicate assignment after the definition was removed; only the early single assignment remains.
- **P2-5 (`list[Any]` vs `tuple[Any, ...]` drift).** **Fixed.** `_select_fields` now returns `tuple[Any, ...]`. `_validate_optimizer_hints_against_selected_fields` and `_build_annotations` updated to match. The whole pipeline is tuple-shaped end-to-end.
- **P2-6 (`convert_relation` docstring).** **Fixed.** Docstring now warns: "Callers must record a `PendingRelation` for any field that returns `PendingRelationAnnotation`; otherwise `finalize_django_types()` cannot rewrite the annotation and Strawberry will raise during schema construction."

### P3 — small/optional items

- **P3-1 (README "most common production failure mode" wording).** Not applied; README still uses the alternate phrasing. Optional.
- **P3-2 (`PendingRelationAnnotation` as sentinel).** **Fixed via metaclass approach** — different from the two options I suggested, but accomplishes the same goal cleanly (the class itself is the sentinel; the metaclass gives it a useful repr). Good choice because Strawberry already does `repr(class)` and never tries to instantiate it.
- **P3-3 (naming drift `_resolved_relation_annotation_from_pending` vs `resolved_relation_annotation`).** Not applied; spec wording vs code wording still drift slightly. Trivial; can land in the phase-10 docs sweep.
- **P3-4 (finalizer imports from converters).** Not applied; `finalizer.py` still imports `resolved_relation_annotation` from `.converters`. Forward-compat hint, not a blocker.
- **P3-5 (`discard_pending` filtering).** **Partially fixed but introduced a small regression.** The implementation moved from identity-based filtering (`{id(p) for p in resolved}` → O(N+M)) to membership-based (`pending not in resolved_list` → O(N×M) because it scans the list per pending entry). Since `PendingRelation` is `frozen=True` and hashable, the idiomatic shape is a `set`:
```python path=null start=null
def discard_pending(self, resolved: Iterable[PendingRelation]) -> None:
    resolved_set = set(resolved)
    self._pending = [pending for pending in self._pending if pending not in resolved_set]
```
This is a one-line change and gets back to O(N+M). It will not bite at current scale, but for projects with many pending relations the list-scan version is meaningfully slower than the original.

## What's still left from the spec's phased order

Re-checked against `docs/spec-foundation.md` "Phased implementation order":

- **Phase 7 — cardinality fixture.** Not started. `tests/fixtures/cardinality_models.py` does not exist. The OneToOne / reverse OneToOne / forward M2M / reverse M2M acceptance cases the spec calls out (`docs/spec-foundation.md:467-476` and `:477-484`) cannot run without these unmanaged fixture models. The new override tests in `tests/types/test_base.py` use the FK fakeshop graph only.

- **Phase 9 — new acceptance test files.** Partial. The annotation-only / assigned-override / shadowing tests landed in `tests/types/test_base.py` rather than the dedicated `tests/types/test_definition_order.py`. The dedicated files the spec names — `tests/types/test_definition_order.py`, `tests/types/test_definition_order_schema.py`, `tests/optimizer/test_definition_order.py` — and the `tests/test_registry.py` extensions for idempotency / phase-1 atomicity / phase-2/3 partial-mutation contract / pending-set cleanup / class-mutation residue still need to land.

- **Phase 10 — docs sweep.** Not started except for `README.md`. `TODAY.md`, `docs/FEATURES.md`, `docs/README.md`, and `CHANGELOG.md` still contain `TODO(spec-foundation 0.0.4)` markers. None of them yet describe the new public symbol or the import-boundary contract.

- **Phase 12 — version bump.** Not started. `pyproject.toml` and `django_strawberry_framework/__init__.py` still pin `0.0.3`.

## New observations after the latest changes

These are small items I did not raise in the prior round.

### N-1. `consumer_annotations` source moved from `__dict__` to `getattr`

`base.py:96` now reads `consumer_annotations = dict(getattr(cls, "__annotations__", {}))` (was `cls.__dict__.get("__annotations__", {})`). On modern Python (3.10+) the class always carries its own `__annotations__` (even empty), so the two forms are equivalent in practice. The change is more robust against an unusual class-creation path that omits the dict entry, but in exchange `getattr` walks the MRO; if a future intermediate base ever sets class-level annotations the subclass would inherit them. Today it does not matter; flagging only so the next refactor knows the trade-off. If you want to keep MRO inheritance out of the consumer-authored detection explicitly, switch back to `cls.__dict__.get("__annotations__", {})`.

### N-2. `consumer_authored_fields` is now redundant on the definition

The definition carries three sets:
- `consumer_authored_fields` (union)
- `consumer_annotated_relation_fields`
- `consumer_assigned_relation_fields`

The union can always be derived (`annotated | assigned`). The finalizer reads `consumer_authored_fields` in phase 1 (line 47) to skip annotation-rewrites for either kind of override; it reads `consumer_assigned_relation_fields` in phase 2. So the union is actually still consumed. Keep it, but consider documenting on `DjangoTypeDefinition` that the union is provided as a convenience derived from the other two — otherwise a future contributor will reach for the union when they should reach for one of the precise sets and reintroduce P1-1.

### N-3. The new `test_relation_unregistered_target_raises` asserts via `repr(PendingRelationAnnotation)`

The assertion `assert "finalize_django_types()" in repr(PendingRelationAnnotation)` relies on the metaclass `__repr__`. That is fine, but it is also worth pinning the exact end-to-end shape — namely, that Strawberry's "Unexpected type" message includes the helpful repr — with a tiny test that constructs a schema before finalization and asserts the substring is in the raised `TypeError`. That's the actual user-facing behavior P2-3 was solving for. Good candidate for `tests/types/test_definition_order_schema.py` when phase 9 lands.

### N-4. New tests do not yet exercise the optimizer + manual-override interaction

`test_annotation_only_relation_override_keeps_generated_resolver` only checks the field metadata (`base_resolver.wrapped_func.__name__`). It does not run a query through `DjangoOptimizerExtension` to verify that the generated resolver still cooperates with the optimizer for an annotation-only override (e.g., that `category.items` plans as a prefetch and resolves to the cached list). That coverage belongs in the optimizer test file added in phase 9, but it is worth listing it explicitly in that file's checklist so it does not slip.

### N-5. `discard_pending` (see P3-5 above)

Repeating because it is the only outright regression introduced this round. Switch the list to a set when the test work in phase 9 is in flight.

## Recommended order from here

1. Apply the `discard_pending` set fix (one line; covers N-5 / P3-5).
2. Land Phase 7 (`tests/fixtures/cardinality_models.py`) so the OneToOne / M2M acceptance tests are unblocked.
3. Land Phase 9: dedicated `tests/types/test_definition_order.py`, `test_definition_order_schema.py`, `tests/optimizer/test_definition_order.py`, and the `tests/test_registry.py` extensions. Pull the three override tests already in `tests/types/test_base.py` into the new files where they belong, leaving the `test_base.py` cases focused on Meta validation and scalar synthesis.
4. Add the missing optimizer interaction coverage from N-4 to the new optimizer file.
5. Land Phase 10 docs sweep — clear the `TODO(spec-foundation 0.0.4)` markers in `TODAY.md`, `docs/FEATURES.md`, `docs/README.md`, and `CHANGELOG.md`. Document the supported forward-reference shapes (the spec calls these out at `docs/spec-foundation.md:485-493`).
6. Phase 12 version bump.

## Things the latest changes got right

- The split-set design (`consumer_annotated_relation_fields` vs `consumer_assigned_relation_fields`) matches the spec's explicit two-case contract at `docs/spec-foundation.md:67-72`. The finalizer correctly consumes the precise set.
- The shadowing error is loud and informative — exactly the right posture for a foundation-level invariant.
- The metaclass `__repr__` for `PendingRelationAnnotation` is the most economical fix for the "forgot to finalize" failure mode and improves the no-extension path too.
- Tuple-shaped `selected_fields` flows cleanly from `_select_fields` through the definition and into the finalizer's `_attach_relation_resolvers` call.
- The `convert_relation` docstring is now self-protecting — future contributors who reuse the helper outside `_build_annotations` will know they need to record a `PendingRelation`.
- All 303 existing tests pass; the slice has not regressed any pre-existing behavior.
