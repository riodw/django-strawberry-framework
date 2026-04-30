# Review Feedback: O3 Optimizer Diff

## Scope reviewed

- `docs/spec-optimizer.md`
- `django_strawberry_framework/optimizer/extension.py`
- `tests/optimizer/test_extension.py`

This feedback only covers the current O3-oriented diff on `main`.

## Findings

### 1. O3 drops `aresolve`, so async root resolvers are no longer covered by the optimizer contract

Priority: P1

The updated spec still defines O3 as a `resolve` / `aresolve` pair with async parity:

- `docs/spec-optimizer.md` says both hooks call into a shared `_optimize(result, info)` helper
- the O3 definition of done explicitly requires an async-parity test

But `django_strawberry_framework/optimizer/extension.py` now only implements `resolve`; `aresolve` is gone entirely.

That is not just a test gap. It changes behavior. If a consumer defines an async root resolver that returns a `QuerySet`, this implementation no longer has an optimizer hook for that code path. The spec still treats async parity as part of O3, so the diff is currently short of its own target contract.

Recommended fix:

- restore `aresolve` and route it through the same `_optimize(...)` helper after awaiting `_next(...)`, or
- explicitly narrow the spec and docs if async optimization is no longer part of O3

Right now the code and spec disagree, and the code is the weaker of the two.

### 2. The rewritten tests overstate O3 coverage: root-gate behavior and async parity are still not pinned

Priority: P2

`tests/optimizer/test_extension.py` now says it covers:

- root-field gate behavior
- type tracing
- `on_execute` context-var lifecycle

The type-tracing and context-var parts are there, but two O3 commitments are still untested:

1. **Root-field gate.** There is no test that a non-root resolver returning a `QuerySet` passes through unchanged and does not trigger planning.
2. **Async parity.** The previous direct `aresolve` coverage is gone, and there is no replacement async test.

This matters because these are the two main architectural claims of the O3 rewrite:

- optimization runs only once at the root
- async resolvers behave the same as sync resolvers

Recommended fix:

- add one direct unit test for the root gate (`info.path.prev is not None` returns `_next(...)` unchanged)
- add one async test covering `aresolve` once it is restored

## Overall assessment

The diff is moving in the right direction: the type-tracing rewrite is much closer to the spec, and the tests are now aimed at the right architecture instead of the old per-resolver planner. The remaining issue is that the implementation and tests have not fully caught up to the O3 contract yet. I would not treat O3 as "landed" until async parity and the root-gate behavior are both implemented and pinned.
