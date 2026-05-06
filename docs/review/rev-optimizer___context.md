# Review: `django_strawberry_framework/optimizer/_context.py`

## High:

None.

## Medium:

None.

## Low:

None.

## What looks solid

- Centralizes the optimizer/resolver context contract in one module instead of leaving read/write dispatch split between `optimizer/extension.py` and `types/resolvers.py`.
- Keeps context sentinel key names as constants so producer and consumer code import the same values.
- Treats context inspection as best-effort: reads return defaults for missing contexts and writes skip frozen or unsupported contexts without interrupting resolver execution.
- Has focused tests through the existing optimizer extension and resolver suites; the constants preserve the existing public sentinel strings.

---

### Summary:

Small shared helper module with no outstanding review findings. It resolves the previously noted context-shape and sentinel-key duplication while preserving the existing context behavior.
