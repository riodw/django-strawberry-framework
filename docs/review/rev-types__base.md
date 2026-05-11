# Review: `django_strawberry_framework/types/base.py`

## High:

None.

## Medium:

### Partial registry state when `register_definition` raises after `register`

`__init_subclass__` calls `registry.register(meta.model, cls)` and then `registry.register_definition(cls, definition)` as two separate steps. If `register_definition` raises (its precondition guard or any future invariant — and per `rev-registry.md` the registry contract explicitly flags this asymmetry), the prior `register` write is already committed: the model→type entry persists in the live registry while no definition exists for that origin. A subsequent re-import or test rerun then hits "already registered" instead of the real underlying error, and `finalize_django_types()` will iterate over a `cls` with no definition. Either bind the two writes into a single registry method that is all-or-nothing, or wrap the pair so that a `register_definition` failure rolls back the `register` entry. Tests should pin both shapes: `register_definition` raising leaves no orphaned model→type entry, and re-defining the type after the failure does not collide.

```django_strawberry_framework/types/base.py:141:144
        registry.register(meta.model, cls)
        registry.register_definition(cls, definition)
        for pending_relation in pending:
            registry.add_pending_relation(pending_relation)
```

### Consumer-assigned `StrawberryField` on scalar fields is silently overwritten

`_consumer_assigned_relation_fields` only inspects `field.is_relation` entries; scalar fields that the consumer assigned a `StrawberryField` to (e.g., to override the resolver or rename via `strawberry.field(...)`) are not collected into `consumer_authored_fields`. `_build_annotations` then always routes scalars through `convert_scalar(field, cls.__name__)` and the resulting synthesized annotation is merged into `cls.__annotations__` ahead of `consumer_annotations` on line 145. Net effect: a consumer who writes `name = strawberry.field(resolver=...)` on a scalar gets the resolver attribute kept on the class but their intent silently shadowed by an auto-synthesized scalar annotation, which Strawberry then resolves differently. Either widen the assignment guard to scalars (skip the auto-annotation when the consumer assigned a `StrawberryField` to a scalar) or document that scalar overrides require an annotation, not an assignment, and raise the same `ConfigurationError` that relations raise when a non-`StrawberryField` non-annotation override is detected. Tests should pin: scalar field with `StrawberryField` assignment preserves the consumer's resolver in the final type.

```django_strawberry_framework/types/base.py:211:229
def _consumer_assigned_relation_fields(
    class_dict: dict[str, Any],
    fields: tuple[Any, ...],
) -> frozenset[str]:
    """Return relation names assigned to explicit Strawberry field objects."""
    assigned = set()
    for field in fields:
        if not field.is_relation or field.name not in class_dict:
            continue
```

### `_validate_meta` and `_validate_optimizer_hints_against_selected_fields` walk hints twice

`_validate_meta` validates hint keys against `model._meta.get_fields()` and `_validate_optimizer_hints_against_selected_fields` then re-validates against the selected subset. Two passes over the same hints dict, two `_meta_optimizer_hints(meta)` calls, two separate error sites with different message shapes (one routes through `_format_unknown_fields_error`, the other open-codes its own string). When the second check fires, the consumer sees an error message that does not match the centralized format helper introduced specifically to keep these messages consistent. Either merge the second check into `_validate_meta` once `fields` is known (delay `_validate_meta` until after `_select_fields`, or pass `selected_names` into a single combined validator), or route the second message through `_format_unknown_fields_error` so consumers see the same shape. The bigger issue is the split ownership — a future contributor adding a third hint check will have a third location to keep in sync. Tests should pin that both "real-but-unselected" and "unknown-field" produce the same `attr="optimizer_hints"` message frame.

```django_strawberry_framework/types/base.py:290:331
    # B4: validate optimizer_hints field names and value types.
    hints = _meta_optimizer_hints(meta)
    if hints:
        model = meta.model
        valid_field_names = {f.name for f in model._meta.get_fields()}
```

### `_validate_meta` is a 58-line / 8-branch hotspot doing four distinct jobs

The helper `scripts/review_inspect.py` flags `_validate_meta` as the file's busiest function (lines 253–310). It mixes (1) the required-key check, (2) the mutual-exclusion check, (3) the deferred/typo-guard check, and (4) the optimizer_hints shape-and-value validation. The hints block accounts for the bulk of the branchiness and is conceptually independent — it depends on `meta.model._meta.get_fields()` which the other checks do not touch. Splitting it out (and merging it with `_validate_optimizer_hints_against_selected_fields` per the previous finding) shrinks the hotspot, gives each sub-check a named test target, and makes the "key validation" / "value validation" / "name validation" boundary explicit. Tests for `_validate_meta` should name each sub-check rather than relying on incidental coverage through full subclass creation.

```django_strawberry_framework/types/base.py:253:310
def _validate_meta(meta: type) -> None:
    """Validate a ``DjangoType`` subclass's nested ``Meta`` class.
    ...
```

## Low:

### Class-level mutable default `_optimizer_field_map = {}` / `_optimizer_hints = {}`

Both `ClassVar[dict[...]] = {}` definitions on `DjangoType` itself are mutable defaults shared by every subclass that never executes the assignment on lines 147–148 (i.e., intermediate abstract bases without `Meta`). If any code path ever mutates the dict in-place rather than rebinding via `cls._optimizer_hints = ...`, the mutation would leak into every other DjangoType subclass that still points at the base dict. Today every writer rebinds, so this is latent rather than active, but the safer shape is `MappingProxyType(MappingProxyType({}))` as the class-level sentinel (or `None`-default + lazy property) so accidental in-place mutation in a future patch raises instead of contaminating siblings. Folder-pass cross-check: confirm `optimizer/walker.py` reads via `getattr(...)` rather than `obj._optimizer_hints[...]` so the sentinel switch would not break the reader.

```django_strawberry_framework/types/base.py:77:79
    _is_default_get_queryset: ClassVar[bool] = True
    _optimizer_field_map: ClassVar[dict[str, FieldMeta]] = {}
    _optimizer_hints: ClassVar[dict[str, OptimizerHint]] = {}
```

### `_meta_optimizer_hints` return type is `dict[str, Any]` while every reader assumes `OptimizerHint` values

The helper's signature says `dict[str, Any]`, which is honest for the raw read (consumers can assign anything), but the value-shape contract is enforced in `_validate_meta` and then assumed by walker/extension callers downstream. The helper sits between those two and erases the post-validation guarantee. Either tighten the post-validation return type (e.g., a second helper `_meta_optimizer_hints_validated(meta) -> dict[str, OptimizerHint]` called after `_validate_meta`) or annotate this helper as the "raw, pre-validation" shape so a reader can tell at a glance which side of the guard they are on. Same calibration as the optimizer-folder mirror-reader shape-guard pattern flagged across `field_meta.py` / `walker.py`.

```django_strawberry_framework/types/base.py:232:239
def _meta_optimizer_hints(meta: type) -> dict[str, Any]:
    """Return ``meta.optimizer_hints`` as a dict, or ``{}`` when unset/empty.
    ...
    return getattr(meta, "optimizer_hints", None) or {}
```

### `or {}` defensive coerce — same package-wide pattern flagged in `conf.py` and `optimizer/extension.py`

`getattr(meta, "optimizer_hints", None) or {}` swallows a misconfigured `optimizer_hints = None` (or `0`, `False`, etc.) silently. The package has now hit this pattern in `conf.py` (`or {}` on settings), `optimizer/extension.py`, `optimizer/_context.py`, and here. The folder pass should decide a package-wide stance — strict (raise `ConfigurationError` on a misconfigured non-dict-non-None value) or lenient (current behavior). Either way, a single shared helper would centralize the choice. Carry-forward note for the project-level pass per `worker-memory/worker-1.md`.

```django_strawberry_framework/types/base.py:239:239
    return getattr(meta, "optimizer_hints", None) or {}
```

### `B4:` comment marker is a legacy spec label

Line 290's `# B4: validate optimizer_hints field names and value types.` looks like a slice marker from a prior plan document and is no longer actionable. Per the AGENTS.md TODO-anchor convention, source markers should either name an active design doc and slice or be removed. Either re-anchor to the relevant section of an active doc or drop the prefix and keep just the descriptive comment.

```django_strawberry_framework/types/base.py:290:290
    # B4: validate optimizer_hints field names and value types.
```

### `_record_pending_relation` `nullable` formula special-cases reverse one-to-one inline

`nullable=kind == "reverse_one_to_one" or bool(getattr(field, "null", False))` mixes two unrelated nullable sources (Django's `null` flag vs. the synthetic "reverse O2O is always nullable" rule) on a single expression line. The rule itself is correct but reads as "either this string-typed kind constant matches *or* the field is null-by-attribute," which is brittle if relation kinds ever subdivide (e.g., a future `reverse_generic_one_to_one`). Pull the kind→nullable lookup into `utils.relations` next to `relation_kind` so the two stay co-located and the formula reads as a named helper. Low-priority polish; folder-pass cross-check against `utils/relations.py` is appropriate.

```django_strawberry_framework/types/base.py:459:468
    return PendingRelation(
        ...
        nullable=kind == "reverse_one_to_one" or bool(getattr(field, "null", False)),
    )
```

### Five `TODO(0.0.5 relay interfaces; …)` anchors in one file

Lines 54, 84, 123, 285, 445 all carry the same relay-interfaces spec anchor. Each is independently actionable, so the count itself is fine, but when the slice lands all five need to be removed in the same change (per AGENTS.md "remove the anchor in the same change that ships the slice"). Worth noting in the spec checklist so none are forgotten — a stray TODO referencing a shipped spec would be a regression. No source change here; just a forward-looking note for the slice author.

```django_strawberry_framework/types/base.py:54:57
# TODO(0.0.5 relay interfaces; see docs/spec-relay_interfaces.md):
# move ``interfaces`` to ALLOWED_META_KEYS only after validation,
# storage, base injection, Relay resolver defaults, id suppression,
# tests, docs, and the version bump all land.
```

## What looks solid

- `scripts/review_inspect.py` was run on the file (required for any file under `types/`); the overview's Imports, Symbols, Control-flow hotspots, Django/ORM markers, and Calls-of-interest sections all matched the source and informed this artifact.
- `__init_subclass__` correctly sets `_is_default_get_queryset` before the `Meta` short-circuit so abstract intermediate bases still expose the right flag.
- `_detect_custom_get_queryset` walks the MRO and stops at `DjangoType` itself — correct for the "inherits parent's override" case noted in `has_custom_get_queryset`'s docstring.
- `_format_unknown_fields_error` centralizes the typo-guard message shape across three call sites (`Meta.fields`, `Meta.exclude`, `Meta.optimizer_hints` in `_validate_meta`).
- `_normalize_fields_spec` / `_normalize_sequence_spec` are small, single-purpose, and keep the `DjangoTypeDefinition` storage shape stable.
- The `DEFERRED_META_KEYS` block for `interfaces` carries an explicit, well-justified comment explaining why the key is in the deferred set rather than the allowed set — exactly the alpha-posture justification AGENTS.md asks for.
- The selection-order guarantee in `_select_fields` (iterates `all_fields` after intersecting names) preserves Django's declared field order in the generated GraphQL type.
- Public API docstrings on `DjangoType`, `get_queryset`, and `has_custom_get_queryset` describe consumer-visible behavior and are not stale.

---

### Summary:

Four Mediums, six Lows. The Mediums cluster around two themes: partial-state on error (registry write pair on lines 141–142 is not atomic) and split ownership of the `optimizer_hints` validation (split between `_validate_meta` and `_validate_optimizer_hints_against_selected_fields`, with inconsistent message framing). Consumer-assigned `StrawberryField` on scalar fields is silently overwritten — the relation-only guard in `_consumer_assigned_relation_fields` should either widen to scalars or the asymmetry should be documented and tested. Lows mirror two folder-wide themes already captured in worker memory: `or {}` defensive-coerce stance (folder/project pass), and shape-guard looseness on the `_optimizer_*` legacy mirrors (folder pass with `optimizer/`). The five repeated `TODO(0.0.5 relay interfaces)` anchors are correct per AGENTS.md TODO-anchor rules but need a same-change removal when the slice ships.

## Verification

PASS (2026-05-11).

- Medium 1 (atomic register/register_definition): addressed in `registry.py` via new `register_with_definition` that rolls back the model->type and type->model entries when `register_definition` raises. `types/base.py.__init_subclass__` now calls this single method. Tested in `tests/test_registry.py`.
- Medium 2 (consumer-assigned scalar `StrawberryField` overwritten): `_consumer_assigned_relation_fields` renamed to `_consumer_assigned_fields`, now returns `(relation, scalar)` frozensets; `_build_annotations` skips synthesizing when the scalar name is in `consumer_authored_fields`; `DjangoTypeDefinition` carries a new `consumer_assigned_scalar_fields` slot; non-`StrawberryField` shadow on a scalar raises `ConfigurationError` mirroring the relation guard. New tests in `tests/types/test_definition_order.py`: `test_assigned_scalar_field_override_keeps_consumer_resolver` and `test_scalar_field_class_attribute_shadowing_raises`.
- Medium 3 (split hint validation / inconsistent messages): hint validation removed from `_validate_meta` and consolidated into a single `_validate_optimizer_hints(meta, fields)` helper that runs the typo guard, the selected-subset guard, and the value-type guard in order. Both name-guard sites now route through `_format_unknown_fields_error`. Test `test_meta_optimizer_hints_for_excluded_field_raises` updated to match the new message frame.
- Medium 4 (`_validate_meta` hotspot): the B4 hints block has been extracted out of `_validate_meta`; the function is now strictly required-key + mutual-exclusion + deferred-typo-guard, and the hints validation is the named `_validate_optimizer_hints` target above. The legacy `B4:` comment marker is removed in the same diff.
- Lows: all six explicitly framed in-artifact as folder/project-pass calibration or no-source-change forward notes; no source change required for this cycle.
- Validation: `uv run pytest tests/ --no-cov` -> 371 passed, 1 skipped. Focused `tests/types tests/test_registry.py` -> 109 passed, 1 skipped (coverage exit code ignored per worker-memory note that focused runs trip `fail_under=100` harmlessly).
