# Review: `django_strawberry_framework/types/relations.py`

Status: verified

## Understanding

`PendingRelation` is the immutable handoff record between class collection and finalization. It snapshots source/target models, field identity, relation kind, and nullability while `PendingRelationAnnotation` is the deliberately visible placeholder rewritten before Strawberry decoration. The registry removes records by identity after successful resolution.

## Verification

- Traced record creation in `types/base.py::_build_annotations`, consumption in `types/finalizer.py`, and identity removal in `registry.py`.
- Checked cyclic and definition-order relation graphs, unresolved targets, consumer annotation bypasses, malformed records, and the sentinel representation.
- `uv run pytest --no-cov -q tests/types`: 506 passed.
- Live library and products relation paths passed.

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

The module stays intentionally small: immutable pending state and a schema-construction diagnostic sentinel, with lifecycle ownership correctly remaining in the registry/finalizer.

## Implementation (Worker 1)

No implementation change was warranted.

## Independent verification (Worker 2)

Relation cycles, unresolved targets, consumer-owned annotations, and pending-record cleanup were rechecked. No defect was found.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
