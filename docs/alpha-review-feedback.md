# Review Feedback: Contract-Spec Batch

## Scope reviewed

- `django_strawberry_framework/types/base.py`
- `tests/types/test_base.py`
- `docs/spec-django_type_contract.md`
- `docs/spec-public_surface.md`
- `docs/spec-optimizer.md`

This feedback replaces the earlier alpha-wide review and only covers the current contract/public-surface batch.

## Findings

### 1. `has_custom_get_queryset()` still misses the documented abstract-base pattern

Priority: P1

`DjangoType.__init_subclass__` returns immediately when a subclass has no `Meta` (`types/base.py` lines 106-110). That means an intermediate abstract base like:

- subclassing `DjangoType`
- defining `get_queryset`
- intentionally omitting `Meta`

never flips `_is_default_get_queryset` to `False`. A later concrete subclass with `Meta` but no own `get_queryset` then inherits `True`, so `has_custom_get_queryset()` incorrectly returns `False`.

That is not an edge case. It breaks the exact shared-base pattern the class docstring explicitly allows for tenant scoping / soft delete / visibility rules. It also means the future optimizer downgrade-to-`Prefetch` rule will miss one of the main intended override paths.

Recommended fix:

- flip the sentinel before the `meta is None` early return when `"get_queryset" in cls.__dict__`, or
- make `has_custom_get_queryset()` walk the MRO instead of relying only on the sentinel.

The current test named `test_has_custom_get_queryset_inherits_through_intermediate_base` does not catch this because the parent in that test defines its own `Meta`, so it is not exercising the documented abstract-base path.

### 2. The consumer-override claim is still present in `types/base.py`

Priority: P2

The new contract spec makes the right decision: remove the consumer-override promise for `0.0.3` and defer the real mechanism. But `types/base.py` still states the old promise in two places:

- the `__init_subclass__` pipeline docstring step about merging "consumer-provided overrides"
- the inline comment above `cls.__annotations__ = {**synthesized, **existing}`

That keeps the code comments out of sync with the new spec and with the skipped test that already documents the promise is not reliable. If the release intent is "not guaranteed yet", the implementation commentary should say exactly that.

Recommended fix:

- rewrite those comments/docstring lines to describe the merge as an implementation detail, not a supported override contract, until the future override spec lands.

### 3. `spec-django_type_contract.md` reintroduces import-order semantics in the future-direction section

Priority: P2

The one-model-one-type section correctly rejects bare "first-registered wins" as the wrong long-term rule. But the future-direction paragraph then says:

- "The primary-or-first-registered type wins..."

That fallback quietly reintroduces import-order semantics whenever multiple types exist and none declares `Meta.primary`. It cuts against the reason for choosing `Meta.primary` in the first place, and it leaves the future rule muddier than the current strict-collision behavior.

Recommended fix:

- make the future rule explicit and import-order-free now, even if the implementation is deferred
- for example: multiple types allowed only when exactly one declares `Meta.primary`, otherwise registration raises

That keeps the follow-on spec anchored to a crisp direction instead of carrying forward a contradictory fallback.

## Overall assessment

This batch is moving in the right direction. Rejecting `Meta.interfaces`, validating `Meta.fields` / `Meta.exclude`, and formalizing the public-surface rules are all good changes. The remaining gaps are mostly consistency issues:

- one real implementation bug around abstract `get_queryset` bases
- one unfinished wording cleanup around consumer overrides
- one spec-level contradiction around the future `Meta.primary` rule

I would fix those before treating this contract batch as settled.
