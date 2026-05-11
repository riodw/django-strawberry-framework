# Review: `django_strawberry_framework/optimizer/field_meta.py`

## High:

None.

## Medium:

### `from_django_field` accepts non-Django objects silently

`field.name` and `field.is_relation` are accessed directly with the comment that "every Django ``Field`` / reverse-relation descriptor guarantees them", but the parameter is typed `object` and there is no runtime guard. If anything other than a Django field descriptor is ever passed (e.g. a `GenericForeignKey`, a property descriptor surfaced via a future `_meta.get_fields()` shape, or test-double), the failure mode is an `AttributeError` deep inside the optimizer walker's class-creation path rather than a loud `OptimizerError` / `ConfigurationError` at the call site. Either tighten the annotation to the Django `Field` union (or a `Protocol` covering `name` + `is_relation`) and rely on type-check, or add an explicit `isinstance` / `hasattr("name")` guard that raises a typed exception with the field repr. Pairs with the `getattr(..., default) or default` calibration carried over from `conf.py` — a defensive default on the two load-bearing attributes would also flip a future Django internal-shape change from "crashes mid-walk" to "explicit at build time".

```django_strawberry_framework/optimizer/field_meta.py:57:78
def from_django_field(cls, field: object) -> FieldMeta:
    ...
    return cls(
        name=field.name,
        is_relation=bool(field.is_relation),
        many_to_many=bool(getattr(field, "many_to_many", False)),
        ...
    )
```

Test expectation if accepted: a unit test feeding a stub object missing `name`/`is_relation` asserts a typed exception (or the chosen behavior) rather than `AttributeError`, plus the existing happy-path coverage from forward FK, reverse FK, M2M, O2O, non-relation field.

### Missing per-shape unit coverage for `from_django_field`

The docstring lists four input shapes the method must build cleanly without per-shape branching: forward fields, reverse relations, the M2M shapes, and reverse FK. The double-`getattr` chains for `target_field` (lines 74-75) and `field` (line 76, the reverse FK's forward-side descriptor) are the only places where the dataclass diverges across shapes; if any one of those returns the wrong attname the optimizer plan silently emits the wrong `only=`/`select_related` shape downstream. This is per-spec a Medium "missing tests for important branches": confirm a direct unit test of `FieldMeta.from_django_field` covers each of the four shapes against the example-project models (e.g. `Item.category`, `Item.entries`, `Category.items`, `Property.entries` M2M-through-`Entry`, `MembershipCard.patron` O2O) and asserts the exact `attname` / `target_field_*` / `reverse_connector_attname` values. If only walker-level integration tests cover this, the connector contract is documented in the docstring but pinned only incidentally.

```django_strawberry_framework/optimizer/field_meta.py:73:76
attname=getattr(field, "attname", None),
target_field_name=getattr(getattr(field, "target_field", None), "name", None),
target_field_attname=getattr(getattr(field, "target_field", None), "attname", None),
reverse_connector_attname=getattr(getattr(field, "field", None), "attname", None),
```

Test expectation if accepted: a `tests/test_field_meta.py` (or extension of `tests/test_optimizer.py`) with one parametrize entry per shape, building each `FieldMeta` directly from `Model._meta.get_field(...)` and asserting the dataclass values. No source change required if coverage already exists; this is a coverage-audit finding.

## Low:

### Repeated `getattr(field, "target_field", None)` walk

`target_field` is read twice (lines 74-75) to extract `name` and `attname`. The repeated literal also shows up in the helper's "Repeated string literals" section. A local `target = getattr(field, "target_field", None)` would compute it once and read marginally better; the cost today is trivial because field metadata builds happen at class-creation time, but the pattern recurs and consolidating it once here is cheap.

```django_strawberry_framework/optimizer/field_meta.py:74:75
target_field_name=getattr(getattr(field, "target_field", None), "name", None),
target_field_attname=getattr(getattr(field, "target_field", None), "attname", None),
```

### Docstring "legacy mirror" anchor

The module docstring states that `cls._optimizer_field_map` is a legacy mirror retained for the 0.0.x line. There is no TODO comment naming the spec that will retire that mirror, which is the AGENTS.md convention for staged removals. Add a TODO anchor next to (or referencing) the mirror writer so the mirror gets removed in the same change that ships the deprecation slice.

```django_strawberry_framework/optimizer/field_meta.py:1:10
"""``FieldMeta`` — precomputed Django field metadata for the optimizer walker.
...
``DjangoTypeDefinition.field_map``. The legacy
``cls._optimizer_field_map`` mirror remains for the 0.0.x line while the
optimizer reads from the definition-backed metadata.
"""
```

### `field: object` annotation is looser than the contract

`from_django_field` is documented to accept a Django field descriptor. `object` invites callers to pass anything; a `Protocol` with `name: str` and `is_relation: bool` (or a union of `django.db.models.Field | ForeignObjectRel | ManyToManyRel | ...`) would make the contract type-check-visible. This is the same calibration as the `conf.py` "missing guard for shape contract" Low.

## What looks solid

- Frozen-slotted dataclass with `__future__ annotations` makes the snapshot immutable, hashable-by-identity, and cheap — exactly right for "built once per `DjangoType`" cache values.
- `TYPE_CHECKING`-gated `django.db.models` import keeps the module free of import-time Django coupling, so the optimizer subpackage stays cold-importable from environments that have not configured settings yet.
- `bool(...)` coercion on every flag field defends against Django returning truthy non-bool values for `many_to_many`/`one_to_many`/`one_to_one`/`auto_created`, preserving `frozen=True` `__eq__` reliability across Django versions.
- The double-`getattr` pattern correctly returns `None` when the intermediate is missing rather than raising — necessary because reverse-side descriptors do not carry `target_field` and forward fields do not carry `field`.
- Helper run: `python scripts/review_inspect.py django_strawberry_framework/optimizer/field_meta.py` produced no control-flow hotspots and confirmed the only repeated literal is the `target_field` access flagged above.

---

### Summary:

`field_meta.py` is a small, well-shaped dataclass + factory whose risk is concentrated in `from_django_field`'s reflective construction. Two Medium items: tighten the `field: object` contract so a malformed input fails loudly rather than mid-walk, and confirm direct unit coverage exists for each documented input shape (forward FK, reverse FK, M2M, O2O, non-relation). Three Lows on `target_field` access deduplication, a missing TODO anchor for the legacy `_optimizer_field_map` mirror, and a too-loose `object` annotation. Folder-pass follow-ups: cross-check that the `cls._optimizer_field_map` mirror has a single writer site and a documented retirement slice, and confirm `FieldMeta`'s flag-set contract (`many_to_many`/`one_to_many`/`one_to_one`/`auto_created`) is the canonical source the walker reads — duplication between this dataclass and any ad-hoc per-walker introspection would be a folder-level DRY finding.

## Verification

PASS — 2026-05-10 (Worker 3).

- Medium 1 (silent non-Django input): `from_django_field` now guards with `hasattr(field, "name")`/`hasattr(field, "is_relation")` and raises `OptimizerError` naming the bad input. Pinned by `test_from_django_field_rejects_non_django_input` and `test_from_django_field_rejects_partial_shape`.
- Medium 2 (per-shape coverage): direct unit tests added for scalar, forward FK, reverse FK (`one_to_many`), M2M (`Book.genres`), and O2O (`MembershipCard.patron`) shapes asserting `attname` / `target_field_name` / `target_field_attname` values.
- Low 1 (`target_field` repeated walk): consolidated to a local `target_field = getattr(field, "target_field", None)` read once.
- Low 2 (legacy mirror TODO anchor): `TODO(spec-fieldmeta-mirror-retirement)` added in the module docstring naming the retirement slice and the writer site in `types/base.py`.
- Low 3 (`field: object` annotation too loose): replaced with `_DjangoFieldLike` `runtime_checkable` `Protocol` declaring `name: str` and `is_relation: bool`.
- `uv run pytest tests/optimizer -q`: 227 passed. Coverage gate fails as expected on a focused run (global `fail_under=100` against package-wide coverage); `field_meta.py` itself reports 100%.
