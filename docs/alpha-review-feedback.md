# Review Feedback: Optimizer Scaffold Diff

## Scope reviewed

- `django_strawberry_framework/optimizer/__init__.py`
- `django_strawberry_framework/optimizer/plans.py`
- `django_strawberry_framework/optimizer/walker.py`
- `tests/optimizer/test_plans.py`
- `tests/optimizer/test_walker.py`

This review only covers the current optimizer-scaffolding diff.

## Findings

### 1. Re-exporting `plan_optimizations` from `optimizer/__init__.py` is likely to create a coverage/regression trap before O2 lands

Priority: P1

`django_strawberry_framework/optimizer/__init__.py` now imports and re-exports `plan_optimizations` from `walker.py`. That looks harmless, but it has two side effects:

- it makes the unimplemented walker look like stable subpackage API instead of scaffolding
- it imports `walker.py` any time code imports `django_strawberry_framework.optimizer`

That second part matters because `tests/optimizer/test_extension.py` already imports `logger` from the subpackage root. So this scaffold now gets imported by existing optimizer tests even though `tests/optimizer/test_walker.py` has no executable tests yet, only comments. With package coverage still gated at 100%, this is an easy way to punch holes in coverage before O2 is actually implemented.

Recommended fix:

- keep `OptimizationPlan` and `plan_optimizations` at their dotted module paths until O2 is implemented and tested, or
- add real smoke tests for the new modules in the same change so importing them does not create an uncovered surface

### 2. The walker API shape is inconsistent across the scaffold, the extension TODO, and the spec

Priority: P1

There are now three different descriptions of the walker entry point:

- `docs/spec-optimizer.md` says `plan_optimizations(info, model) -> OptimizationPlan`
- `optimizer/extension.py` still says the extracted helper will be `plan_optimizations(info, model) -> OptimizationPlan`
- `optimizer/walker.py` implements `plan_optimizations(selected_fields, model) -> OptimizationPlan`

This is exactly the kind of drift scaffolding is supposed to prevent. You should pick one contract now before other modules and tests start coding against different call signatures.

My recommendation is to decide explicitly between:

- `plan_optimizations(info, model)` if the helper owns the `selected_fields[0].selections` peel, or
- `plan_optimizations(selected_fields, model)` if the helper is meant to stay narrower and purely selection-list based

Either choice is fine, but the spec, the TODO anchors, and the scaffold should all say the same thing.

### 3. `tests/optimizer/test_walker.py` is only commentary, so the scaffold does not yet pin any contract for the new module

Priority: P2

The comments in `tests/optimizer/test_walker.py` are useful as a checklist, but they are not tests. Right now the repo has a real source module and a mirrored test file, but no executable contract for the walker at all.

That is an oversight specifically because the spec for O2 says the walker is valuable partly because it is a pure function that can be unit-tested in isolation. If you want this commit to remain "scaffolding only", that is fine, but then the safer move is not to expose the walker from `optimizer/__init__.py` yet. If you do want to expose it now, add at least one smoke-level test that pins the current scaffold behavior, for example that calling it raises the expected `NotImplementedError`.

## Overall assessment

The module split itself is good. `plans.py` and `walker.py` are the right seams for O2/O4/O5/O6 work. The main oversights are about discipline around the scaffold:

- avoid exporting unfinished helpers too early
- keep the spec and scaffold on one API signature
- either add a minimal executable contract now or keep the new helper private until O2 lands
