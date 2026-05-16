# DRY Feedback

## DRY.md Compared To Project-Level Review

`docs/DRY.md` does not match `docs/review/rev-django_strawberry_framework.md` as a whole. It is an aggregate of every `docs/review/rev-*.md` DRY section, while `rev-django_strawberry_framework.md` is only the package-level pass.

The `# Review: django_strawberry_framework/` block inside `docs/DRY.md` does match the project-level artifact's DRY conclusion: there are no unanchored package-level DRY findings. The remaining useful redundancy is already concentrated in the two FieldMeta follow-up areas below.

## Real DRY Opportunities

### 1. Make `FieldMeta` The Only Relation-Shape Reader

`FieldMeta` already documents itself as the single source of truth for relation shape, nullability, connector columns, and target metadata in `django_strawberry_framework/optimizer/field_meta.py`. It already stores the values consumers need: `nullable`, `attname`, `related_model`, `target_field_attname`, and `reverse_connector_attname`.

Three type-layer sites still recompute pieces of that same relation shape from raw Django fields:

- `django_strawberry_framework/types/base.py::_record_pending_relation` recomputes `kind` and `nullable`.
- `django_strawberry_framework/types/converters.py::resolved_relation_annotation` recomputes cardinality and nullability.
- `django_strawberry_framework/types/resolvers.py::_make_relation_resolver` recomputes cardinality and `attname`.

This is real redundancy because a future relation-shape change must keep `FieldMeta.from_django_field()` and those three readers aligned. The many-side helper reduced one repeated grouping, but the broader derivation still exists in multiple places.

Useful reduction:

- Thread or look up the relevant `FieldMeta` from `DjangoTypeDefinition.field_map` at the three TODO-anchored sites.
- Keep raw Django fields only where Django descriptors or exception classes are still needed.
- Let `FieldMeta.nullable` decide annotation/nullability behavior instead of rechecking `relation_kind(field)` and `field.null`.
- Let `FieldMeta.attname` decide FK-id elision resolver behavior instead of `getattr(field, "attname", None)`.
- Remove the three `TODO(spec-fieldmeta-ssot)` anchors and trim the `field_meta.py` docstring once the migration lands.

Definition of done:

- One cardinality/nullability/attname source feeds pending relation records, relation annotations, and generated relation resolvers.
- Tests still cover forward FK, forward OneToOne, reverse OneToOne, reverse FK, and M2M behavior.
- No new public API is introduced.

### 2. Retire The Legacy Optimizer Metadata Mirrors

`DjangoTypeDefinition` already carries the canonical optimizer metadata: `field_map` and `optimizer_hints`. `DjangoType.__init_subclass__` still mirrors those values onto private class attributes:

- `cls._optimizer_field_map`
- `cls._optimizer_hints`

The optimizer still reads those mirrors in `optimizer/walker.py` and `optimizer/extension.py`. That leaves two metadata paths for the same state: definition-backed registry metadata and class-attribute compatibility mirrors.

This is real redundancy because the class attributes are written from the canonical definition data and then read back later as if they were the source. They also survive as class-level residue after registry lifecycle resets, which increases the surface area tests and future code need to reason about.

Useful reduction:

- Have walker code resolve `registry.get_definition(type_cls)` and read `definition.field_map` / `definition.optimizer_hints`.
- Have schema reachability and schema audit code identify Django types through registry definitions instead of `hasattr(origin, "_optimizer_field_map")`.
- Preserve the current fallback for unregistered models where the walker currently tolerates `model._meta.get_fields()`.
- Remove the mirror writer in `types/base.py`.
- Remove the `TODO(spec-fieldmeta-mirror-retirement)` anchors and the mirror-retirement paragraph in `field_meta.py`.

Definition of done:

- Optimizer metadata has one canonical storage path: `DjangoTypeDefinition`.
- No optimizer source reads `_optimizer_field_map` or `_optimizer_hints`.
- Existing optimizer and fakeshop tests still pass without adding public surface.
