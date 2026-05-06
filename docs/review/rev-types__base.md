# Review: `django_strawberry_framework/types/base.py`

## High:

None.

## Medium:

### `optimizer_hints` validation accepts hints for fields the type does not expose

`_validate_meta` validates that every key in `optimizer_hints` names a *Django* field on `meta.model._meta.get_fields()`, but does not check that the key is also in the `Meta.fields`-filtered selection. A consumer who writes:

```
class CategoryType(DjangoType):
    class Meta:
        model = Category
        fields = ("name",)
        optimizer_hints = {"items": OptimizerHint.prefetch_related()}
```

passes validation, but `items` is not in the selected fields and the walker never visits it, so the hint is silently dead code. The consumer's optimization intent is lost without any signal.

Recommended: after the existing field-name check, intersect `set(hints)` with the *selected* field names (computed once via `_select_fields(meta)`) and raise `ConfigurationError` listing the dead hint keys. Add a unit test pinning the new check.

```django_strawberry_framework/types/base.py:241:257
hints = getattr(meta, "optimizer_hints", None)
if hints is not None:
    model = meta.model
    valid_field_names = {f.name for f in model._meta.get_fields()}
    unknown_hint_fields = sorted(set(hints) - valid_field_names)
    if unknown_hint_fields:
        raise ConfigurationError(...)
```

## Low:

### Inherited `Meta` classes pass the existence check but bypass the unknown-key guard

`_validate_meta` builds `declared = {k for k in meta.__dict__ if not k.startswith("_")}`, which only enumerates the *child* `Meta` class's own attributes. If a consumer factors common settings into a `class BaseMeta:` and inherits, `getattr(meta, "model", ...)` still resolves through MRO (so the existence check passes), but unknown keys declared on the parent are not caught. This is a small surface-area hazard for the alpha posture.

Recommended (defensive): walk `meta.__mro__` (excluding `object`) when computing `declared`, or explicitly document that `Meta` inheritance is not supported and reject if `meta` has bases other than `object`. Comment polish — defer.

```django_strawberry_framework/types/base.py:226:226
declared = {k for k in meta.__dict__ if not k.startswith("_")}
```

### `_optimizer_field_map` and `_optimizer_hints` are set without class-level defaults

`__init_subclass__` writes `cls._optimizer_field_map = {...}` and `cls._optimizer_hints = ...` on each concrete `DjangoType`, but `DjangoType` itself does not declare them as `ClassVar`s with empty defaults. Code that walks the MRO (e.g., the walker's `getattr(type_cls, "_optimizer_field_map", None)`) handles the absence correctly, but explicit class-level defaults of `{}` would make the attribute contract self-documenting and protect against a future code path that does `cls._optimizer_field_map.get(...)` without the `getattr(..., None)` guard.

```django_strawberry_framework/types/base.py:67:71
class DjangoType:
    """Base class for Django-model-backed Strawberry GraphQL types."""

    # Sentinel so ``has_custom_get_queryset`` can detect overrides.
    _is_default_get_queryset: ClassVar[bool] = True
```

### `cls.__annotations__ = {**synthesized, **existing}` merge is documented as not-a-contract

The merge order (synthesized first, consumer-declared second) gives the *appearance* of consumer override semantics, but the docstring and the in-source comment both say `@strawberry.type` rewrites `cls.__annotations__` from its own field metadata downstream, so the merge does not reliably preserve the override. There is also a skipped test pinning the limitation. The current shape is deliberate and well-flagged.

Worth tracking for a future spec; no action this pass.

```django_strawberry_framework/types/base.py:152:153
existing = dict(cls.__dict__.get("__annotations__", {}))
cls.__annotations__ = {**synthesized, **existing}
```

## What looks solid

- Pipeline order in `__init_subclass__` is documented in detail and matches the implementation step-for-step.
- `_is_default_get_queryset` flag is flipped *before* the `meta is None` early return, so intermediate abstract bases that override `get_queryset` propagate the override to concrete subclasses through MRO.
- `_select_fields` is called once and the resulting list is reused for `_build_annotations` and `_attach_relation_resolvers`, avoiding a duplicate field walk and keeping the dependency direction one-way (`base` → `resolvers`, never the reverse).
- `_validate_meta` enforces the four declared rules in order: required `model`, `fields`/`exclude` exclusivity, deferred-key rejection (with `interfaces` explicitly enumerated), unknown-key typo guard.
- Unknown-field error messages name the model, the unknown values, and the full available field set, so typos surface loudly.
- `DEFERRED_META_KEYS` enumerates the future-spec keys (`filterset_class`, `orderset_class`, `aggregate_class`, `fields_class`, `search_fields`, `interfaces`) and the per-key `interfaces` comment explains why it is deferred — that matches AGENTS.md's "deferred-surface keys" rule.
- `has_custom_get_queryset` is a constant-time attribute read of the `_is_default_get_queryset` flag — no MRO walk per call.
- `optimizer_hints` value-type validation rejects non-`OptimizerHint` values with a clear message, matching the typed-wrapper contract `OptimizerHint` was created to enforce.
- 25% line coverage in this file's own unit tests; full coverage via integration tests across the suite (100% gate met).
- Two Scoops of Django shape: small focused module, single-responsibility helpers, explicit settings/Meta boundaries, no module-level magic beyond the documented `__init_subclass__` pipeline.

---

### Summary:

`base.py` is the consumer-facing entry point and the most behavior-rich file in the package; the `__init_subclass__` pipeline is well-documented and consistently honored. The single Medium item is a real silent-dead-code hazard: `optimizer_hints` accepts keys that are valid Django field names but not in the type's selected fields. Add the intersection check and a test. Low items are a defensive MRO walk for `Meta` inheritance, explicit class-level defaults for `_optimizer_field_map` / `_optimizer_hints`, and the well-flagged-but-not-yet-stable `__annotations__` merge contract.

---

### Worker 3 verification

- Medium fix: new `_validate_optimizer_hints_against_selected_fields(meta, fields)` helper runs after `_select_fields` in `__init_subclass__` and raises `ConfigurationError` with the model name, the offending hint keys, and the full selected-field list.
- Test added: `test_meta_optimizer_hints_for_excluded_field_raises` in `tests/types/test_base.py` pins the new check; before the fix the test fails because the hint silently no-ops.
- Low fix 2 applied: `DjangoType` now declares class-level defaults `_optimizer_field_map: ClassVar[dict[str, FieldMeta]] = {}` and `_optimizer_hints: ClassVar[dict[str, OptimizerHint]] = {}`. Consumers and the walker can read these on the base class or on intermediate abstract subclasses without `getattr(..., None)` guards.
- Low fix 1 (Meta inheritance MRO walk) and Low note (`__annotations__` merge contract): not addressed in this cycle.
  - The MRO walk would change the unknown-key validation surface and risks breaking consumer Meta classes that inherit from a typo-laden parent. Defer until a Meta-inheritance design decision lands.
  - The `__annotations__` merge is a known limitation tracked by a skipped consumer-override test; addressing it requires a separate spec.
- Validation: `uv run ruff format` and `uv run ruff check` clean; `uv run pytest -q` -> 352 passed, 4 skipped, 100% coverage (one new test in `tests/types/test_base.py`).
- CHANGELOG: not updated. The new validation rejects only previously-silent-dead-code configurations; AGENTS.md forbids changelog edits without explicit instruction.
- Scope: changes confined to `django_strawberry_framework/types/base.py` and `tests/types/test_base.py`.
- Checkbox in `docs/review/review-0_0_3.md`: marked `- [x]`.

---

### Helper-surfaced follow-ups (post-cycle audit)

This section was added after the cycle was reviewed. Running `scripts/review_inspect.py` on `types/base.py` post-cycle surfaced two additional follow-ups for the next release.

- **Repeated literal `optimizer_hints` (4x).** Used as a string key in `ALLOWED_META_KEYS`, `getattr(meta, "optimizer_hints", None)` inside `__init_subclass__`, the same `getattr` inside `_validate_meta`, and the same `getattr` inside `_validate_optimizer_hints_against_selected_fields`. The Meta key name is part of the documented public API, so a module constant `_OPTIMIZER_HINTS_META_KEY = "optimizer_hints"` is debatable, but at minimum a small `_meta_optimizer_hints(meta)` helper that returns `getattr(meta, "optimizer_hints", None) or {}` would centralize the three identical `getattr` call sites and make the validation flow easier to read.
- **Repeated `. Available:` error fragment (3x).** `_validate_meta` (unknown Meta keys), `_select_fields` (unknown `fields`/`exclude` names), and the model-name-prefixed error in optimizer-hints validation all share the "unknown values: …. Available: …" message shape. A small `_format_unknown_fields_error(*, model, attr, unknown, available)` helper would centralize the error format and ensure consistency if a future spec adds more typo guards. Cosmetic; no behaviour change.
- Note: `__init_subclass__` is reported as a 102-line hotspot but only 3 branches; that is the documented sequential-pipeline shape (one path through the steps for every concrete subclass). No decomposition recommended — the function reads top-to-bottom as the pipeline it documents.

**Status (post-audit implementation pass):** both follow-ups addressed.

- `_meta_optimizer_hints(meta)` helper added; the three `getattr(meta, "optimizer_hints", None) or {}` call sites in `__init_subclass__`, `_validate_meta`, and `_validate_optimizer_hints_against_selected_fields` all route through the helper. The `"optimizer_hints"` key still appears once in `ALLOWED_META_KEYS` (where it must, as the literal Meta-key whitelist) and once inside the helper itself.
- `_format_unknown_fields_error(*, model, attr, unknown, available)` helper added; both `_select_fields` typo-guard branches and the optimizer-hints validation use it. The error shape "`<Model>.Meta.<attr>` names unknown fields: `[…]`. Available: `[…]`." is now produced from one place.
- Validation: `uv run pytest -q` -> 354 passed, 100% coverage.
