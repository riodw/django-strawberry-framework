# Review: `django_strawberry_framework/types/relations.py`

## High:

None.

## Medium:

None.

## Low:

### `django_field: Any` weakens the frozen-dataclass hashability invariant

`PendingRelation` is `@dataclass(frozen=True)` and its docstring (lines 16-19) names hashability as a load-bearing contract for `TypeRegistry.discard_pending()`'s `set(resolved)` coercion. Frozen dataclass auto-`__hash__` hashes every field; `django_field: Any` (line 24) admits any object, including Django field instances that are reference-hashable today but offer no documented hash contract. If a future caller threads a non-hashable surrogate into this slot (a dict-shaped descriptor, an unfrozen wrapper), `set(resolved)` raises `TypeError` deep inside finalization rather than at construction. Tightening the annotation to `models.Field` (or a narrow union covering forward/reverse descriptors) and/or asserting `hash(django_field)` in `__post_init__` would surface the contract violation at the registration call site instead.

```django_strawberry_framework/types/relations.py:13:27
@dataclass(frozen=True)
class PendingRelation:
    """Relation field whose target ``DjangoType`` was not registered during collection.

    Fields must remain hashable because ``TypeRegistry.discard_pending()`` builds
    ``set(resolved)`` when removing records after successful finalization.
    """

    source_type: type
    source_model: type[models.Model]
    field_name: str
    django_field: Any
    related_model: type[models.Model]
    relation_kind: RelationKind
    nullable: bool
```

### Metaclass `__repr__` is the only consumer-facing surface and lacks an anchor to its emitter

`_PendingRelationAnnotationMeta.__repr__` exists exclusively so the schema-construction `TypeError` Strawberry raises when it encounters `PendingRelationAnnotation` reads sensibly. That coupling is invisible from this file — there is no comment naming the call site (`strawberry.type(...)` inside `finalize_django_types`) or pointing back to the rewrite step in `types/finalizer.py` that is meant to replace the sentinel before Strawberry ever sees it. A one-line comment on the metaclass class declaration naming the rewrite responsibility and the failure mode it documents would close the loop for the next reader.

```django_strawberry_framework/types/relations.py:30:41
class _PendingRelationAnnotationMeta(type):
    """Metaclass that gives the sentinel a useful schema-construction error repr."""

    def __repr__(cls) -> str:
        return (
            "<unfinalized DjangoType relation; call finalize_django_types() before constructing "
            "strawberry.Schema>"
        )


class PendingRelationAnnotation(metaclass=_PendingRelationAnnotationMeta):
    """Sentinel annotation rewritten before ``strawberry.type`` sees the class."""
```

## What looks solid

- Module is a pure data/contract surface: one frozen dataclass + one sentinel-with-metaclass, no logic, no imports beyond stdlib + `django.db.models` + a sibling enum. The static helper was run (mandatory under `types/`) and confirmed no control-flow hotspots, no reflective access, no TODOs, no repeated literals.
- The frozen-dataclass + explicit hashability docstring is exactly the right shape for a record consumed by `set()` coercion; the contract is at least documented in-file (contrast with the "documented contract, not enforced" theme seen in registry/plans/base — here the contract is small enough that the dataclass `frozen=True` carries most of it).
- `PendingRelationAnnotation` lives next to `PendingRelation` rather than being orphaned in `converters.py` or `finalizer.py`; the two pieces of the pending-relation protocol are colocated.
- Import surface is minimal and one-way (no back-edges into `types/base` or `types/finalizer`), so the module is safe to import from any phase of finalization without circular-import risk.

---

### Summary:

Pure contract module — one frozen dataclass recording pending relations and one sentinel annotation type used by the finalizer's rewrite step. No High/Medium findings. Two Lows: (1) `django_field: Any` is wider than the docstring's hashability contract and would benefit from a narrower annotation or a `__post_init__` hash check, (2) the metaclass `__repr__` is consumer-facing only via Strawberry's `TypeError` and would be easier to maintain with a one-line comment naming the rewrite site in `types/finalizer.py`. Both defer cleanly to the types folder pass if a package-wide stance on "narrow contract surfaces" emerges; neither blocks any current consumer.

## Verification

PASS — Worker 3, 2026-05-11.

- Low 1 (`django_field: Any` weakens hashability invariant): addressed. Annotation narrowed to `models.Field | models.ForeignObjectRel` and `PendingRelation.__post_init__` probes `hash(self.django_field)` so a non-hashable surrogate raises at the registration call site, not deep in `discard_pending()`. Docstring updated to name the probe.
- Low 2 (metaclass `__repr__` anchor): addressed. Comment block added on `_PendingRelationAnnotationMeta` naming `finalize_django_types()` and the `source_type.__annotations__` rewrite, plus the failure mode the `__repr__` documents.
- Validation: `uv run pytest tests/types tests/test_registry.py -q --no-cov` → 113 passed, 1 skipped. No new dedicated test required — both Lows are typing/comment polish on a pure contract surface; existing relation-finalization tests already exercise the `set(resolved)` path.
- Scope discipline: changes confined to `django_strawberry_framework/types/relations.py`. No comment-pass or changelog update needed (internal-only polish).
