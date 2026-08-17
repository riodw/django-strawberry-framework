# Review: `django_strawberry_framework/optimizer/field_meta.py`

Status: verified

## Understanding

`FieldMeta` snapshots Django relation cardinality, nullability, connector/target columns,
accessors, GenericRelation morph columns, and FK-id-elision eligibility at type creation. The
registered definition map is the canonical walker source; raw Django fields remain a defensive
fallback for unregistered/test shapes.

## Verification

Read the complete metadata builder and traced `types/definition.py`, finalizer relation wiring,
`optimizer/walker.py`, `join_taxonomy.py`, generated resolvers, custom `to_field`/composite-PK
guards, reverse accessors, GenericRelation attach projections, and sharded models. Focused
field-meta, relation-cardinality, definition-order, relay-projection, and walker tests are
included in the 781 passing optimizer tests; live relation and keyset paths also passed.

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

Cardinality-gated nullability and FK-id-elision metadata agree with Django descriptors and the
shared join taxonomy. No source or permanent-test change was justified.

## Implementation (Worker 1)

None — zero-edit cycle. Existing permanent tests provide the complete relation-shape and
projection evidence; no formatting/linting was required for this item.

## Independent verification (Worker 2)

Re-read metadata construction and traced forward/reverse cardinality, accessor, GenericRelation,
custom `to_field`, composite-PK, and projection consumers. Focused optimizer tests passed
(`781 passed`), and reachable HTTP optimizer tests passed (`350 passed, 1 skipped`). No defect was
reproduced in this target.

