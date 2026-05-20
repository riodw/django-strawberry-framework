# Review: `django_strawberry_framework/scalars.py`

Status: verified

## DRY analysis

- Defer until a second scalar lands in this module (e.g., the `Upload` TODO-ALPHA-027 scalar named in the module docstring): extract a shared `_with_strawberry_compat(...)` helper so both definitions live inside one shared `warnings.catch_warnings()` suppression context rather than parallel `with warnings.catch_warnings():` blocks. The current cross-module deprecation-suppression block at `scalars.py:91-102` is the only site in the package today.

## High:

None.

## Medium:

None.

## Low:

### `_parse_bigint` error message embeds the rejected value verbatim

`scalars.py:50-54` constructs `ValueError(f"... got {value!r}")` for any non-matching string. If a hostile consumer sends a multi-megabyte string the entire payload lands in the exception message and any structured logger downstream (`django_strawberry_framework` logger or upstream Strawberry error formatting). Strawberry error masking in production typically swaps the message for a generic string, so the practical blast radius is small, but the repr is unbounded. Low-tier polish only — truncate the embedded value to a reasonable cap (e.g. first 64 chars + `...`) the next time the parser is touched.

```django_strawberry_framework/scalars.py:50:54
            raise ValueError(
                f"BigInt requires a plain ASCII decimal integer string "
                f"(optional leading minus for non-zero, no leading zeroes, "
                f"no underscores, no plus sign, no Unicode digits); got {value!r}",
            )
```

### Module docstring's forward-looking scalar list will drift

`scalars.py:3` names `Upload` per `TODO-ALPHA-027` as a near-term resident. The package has no other in-flight scalar work, and the docstring will need a sweep the moment a second scalar lands here. Not a defect today; record for the comment pass that lands alongside the next scalar add to confirm the list still reflects the on-disk surface.

```django_strawberry_framework/scalars.py:1:11
"""Public scalars defined by django-strawberry-framework.

Today: ``BigInt``. Future scalars (e.g. ``Upload`` per TODO-ALPHA-027) land here.
...
"""
```

## What looks solid

### DRY recap

- **Existing patterns reused.** `scalars.py` reuses `strawberry.scalar(...)` registration (the only call site in the package at `django_strawberry_framework/scalars.py:97-102`) and is consumed in exactly one downstream site: `django_strawberry_framework/types/converters.py:29` (`from ..scalars import BigInt`) feeding the `_SCALAR_MAP` entries at `types/converters.py:45` (`models.BigIntegerField: BigInt`) and `types/converters.py:49` (`models.PositiveBigIntegerField: BigInt`). The strict parser/serializer pair (`_parse_bigint` / `_serialize_bigint` at `scalars.py:25-77`) is the only Python-level coercion the scalar registers; no other scalar in the package owns custom parse/serialize functions. The top-level re-export at `django_strawberry_framework/__init__.py:22,28` is the package's public surface for the value.
- **Duplication risk in the current file.** None inside the file. The `BigInt cannot parse {type(value).__name__}` (`scalars.py:56`) / `BigInt cannot serialize {type(value).__name__}` (`scalars.py:77`) message templates are parallel by design (input/output symmetry contract) and are intentionally not collapsed — the exception types differ (`ValueError` vs `TypeError`) and the framing prose (`cannot parse` vs `cannot serialize`) is the load-bearing distinction for consumers reading error logs. The repeated `isinstance(value, bool)` short-circuit at `scalars.py:44` and `scalars.py:73` is also intentional — both gates need to reject `bool` before any `isinstance(value, int)` branch (bool subclasses int); collapsing would require routing through a single dispatcher and would obscure the asymmetric exception-type contract.

### Other positives

- Static helper ran cleanly — no control-flow hotspots, no Django/ORM markers beyond an incidental `only` substring in a docstring bullet, no repeated string literals, and a clean import list (stdlib + `strawberry`, no first-party imports so zero circular-import surface).
- Parser/serializer symmetry is well-documented and pinned: the strict regex at `scalars.py:22` rejects every PEP 515 / Unicode-digit / leading-zero / hex / scientific shape, and `tests/test_scalars.py` lines 23-204 walk every documented accept/reject pair across the int64 boundary, including the `bool`-subclass-of-`int` short-circuit on both sides and the defense-in-depth `None` rejection.
- The deprecation-suppression block at `scalars.py:91-102` is precisely scoped (single `filterwarnings("ignore", message="Passing a class to strawberry.scalar", category=DeprecationWarning)` matcher, wrapped around exactly the one offending call), and the import-time contract is pinned by `tests/test_scalars.py:229-252`'s subprocess regression test running `-W error::DeprecationWarning`. The TODO comment at `scalars.py:80-90` correctly anchors the remediation card (`TODO-ALPHA-045-0.0.7`).
- The module's surface is consumer-overridable per spec-015's annotation-only contract: a consumer can write `myfield: int` on a `BigIntegerField` column and bypass the `BigInt` scalar entirely (the spec's H2 converter-bypass contract handles unsupported and supported field types alike), and the public `BigInt` symbol can be substituted explicitly via `myfield: SomeOtherScalar` if a consumer needs custom precision semantics. No spec-015 work touches this file directly; the override path runs through `_build_annotations` in `types/base.py` and `convert_scalar` in `types/converters.py`.
- Cross-module DRY: `BigInt` is defined exactly once and consumed at exactly two `_SCALAR_MAP` entries (`types/converters.py:45,49`). No parallel scalar-shaped declarations exist elsewhere in the package — `types/converters.py:57` uses Strawberry's stock `strawberry.scalars.JSON` for `models.JSONField`, not a custom `strawberry.scalar(...)` call.

### Summary

`scalars.py` is a tight 102-line module hosting the single `BigInt` scalar plus its strict parser/serializer pair. Logic is correct, test surface in `tests/test_scalars.py` is exhaustive across both gates and the import-time deprecation contract, and cross-module consumption is funneled through a single `_SCALAR_MAP` pair in `types/converters.py`. Spec-015's consumer-override contract for scalar fields lives in `types/base.py` and `types/converters.py`, not here — the `BigInt` scalar itself is already consumer-overridable per the annotation-only path it covers. No High or Medium findings; two Low items are forward-looking polish for the next pass that touches the module.

---

## Fix report (Worker 2)

### Files touched

- None. Both Low findings are explicitly forward-looking per the artifact: Low 1 says "the next time the parser is touched" and Low 2 says "record for the comment pass that lands alongside the next scalar add". No in-cycle edit is recommended for either, so no source change in this pass.

### Tests added or updated

- None.

### Validation run

- `uv run ruff format .` — pass (100 files left unchanged).
- `uv run ruff check --fix .` — pass (all checks passed).
- `pytest` not run per Worker 2 standing dicta (`AGENTS.md` / `START.md`).

### Notes for Worker 3

- No shadow file used in this pass.
- Both Low findings are intentionally not addressed because the artifact itself defers them: Low 1 is "Low-tier polish only — truncate ... the next time the parser is touched"; Low 2 is "record for the comment pass that lands alongside the next scalar add". No High/Medium findings. This is a consolidated no-op cycle.
- The artifact's `What looks solid` section confirms the existing docstrings/comments already describe the current surface accurately, so the comment pass is also a no-op (recorded below).

---

## Verification (Worker 3)

### Logic verification outcome

- High: None — accepted.
- Medium: None — accepted.
- Low 1 (forward-looking parser polish — truncate the embedded value in `_parse_bigint` the next time the parser is touched): deferred per artifact prose — accepted.
- Low 2 (forward-looking module docstring sweep for the next scalar add): deferred per artifact prose — accepted.

### DRY findings disposition

All three DRY bullets accurate. Spot-checked: `BigInt` is registered at exactly one site (`scalars.py:97-102`), consumed at exactly two `_SCALAR_MAP` entries (`types/converters.py:45,49`), and the in-file parallel structures (parse/serialize messages, `isinstance(value, bool)` short-circuits at `scalars.py:44,73`) are intentionally symmetric per the input/output contract. No in-file duplication; no cross-module duplication. Accepted.

### Temp test verification

- None used. No source change to verify; ruff format + check were already run by Worker 2 and the diff against `scalars.py`, `tests/`, and `CHANGELOG.md` is empty.

### Verification outcome

cycle accepted; verified

---

## Comment/docstring pass

No-op cycle. The artifact's two Low items are forward-looking and not actionable in this cycle. The existing module docstring and parser/serializer docstrings already accurately describe the surface per the artifact's `What looks solid` section.

---

## Changelog disposition

- **Warranted?** Not warranted.
- **Reason:** No source change in this cycle. Zero High/Medium findings and both Lows are forward-looking per the artifact's own prose. Per `AGENTS.md` ("Do not update CHANGELOG.md unless explicitly instructed.") and the active plan (no changelog authorization for this cycle item), no `CHANGELOG.md` edit is made.
- **What was done:** No `CHANGELOG.md` edit.
- **Validation:** Same two ruff commands recorded once above are sufficient (no source change to re-validate).

---

## Iteration log
