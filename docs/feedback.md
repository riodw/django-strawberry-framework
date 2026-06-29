Spec-039 verification review
============================

Review scope: the current `HEAD` implementation after the feedback-fix commit
`7511949c`, with `docs/feedback.md` replaced from the prior review. I focused on
the areas that changed since the last review: mutation-level `optional_fields`,
schema-time serializer discovery, generated input identity/name generation,
relation conversion, resolver decode, rollback behavior, and fakeshop live
coverage.

Overall assessment: the previous review items are mostly addressed. The
implementation now uses mutation-level `Meta.optional_fields`, exposes the
`get_serializer_for_schema()` classmethod hook, stashes relation target models at
bind time, rejects non-PK relation fields, rolls back error-envelope writes from
the shared atomic skeleton, removes the dead `get_serializer()` hook, and adds
renamed-field live coverage.

There are still two concrete issues before I would call this fully closed. The
first is a spec-contract bug in input type naming for hook-varied shapes; the
second is a class-creation timing bug for subclasses of concrete serializer
mutations.

Findings
--------

### High: hook-varied full shapes can still collide on the canonical input name

The cache key was correctly moved to the full `SerializerInputShape` descriptor,
but the generated type name can still stay canonical for a hook-produced "full"
shape:

- `django_strawberry_framework/rest_framework/sets.py::SerializerMutation.build_input`
  calls the concrete `get_serializer_for_schema()` hook and passes that field map
  into `build_serializer_input_class`.
- `django_strawberry_framework/rest_framework/inputs.py::build_serializer_input_class`
  computes `is_full_shape` relative to that same hook-returned field map.
- `django_strawberry_framework/rest_framework/inputs.py::serializer_input_type_name`
  returns `<Serializer>Input` whenever `is_full_shape` is true.

That means two mutations over the same serializer class can have distinct
descriptor/cache identities but still try to materialize the same canonical class
name. I verified this with a local probe: two `SerializerMutation` classes using
the same `HookSer` serializer but overriding `get_serializer_for_schema()` so the
same `target` field points at different related models. Finalization fails with:

```text
ConfigurationError 'HookSerInput' is materialized by two distinct SerializerMutation input classes
```

This violates the spec requirement that same serializer/effective-field-name
inputs with different hook-returned field specs get distinct deterministic names
instead of stale reuse or materialization collision.

There is a second naming gap in the same area:
`django_strawberry_framework/rest_framework/inputs.py::_shape_token` includes the
annotation, requiredness, kind, and source, but not the new
`InputFieldSpec.related_model`. Two relation shapes with the same field name and
same GraphQL annotation but different target models can therefore produce the same
descriptor-derived suffix even when they are not considered canonical.

Required correction: allow the canonical `<Serializer>Input` name only for the
actual default full serializer shape, not for arbitrary hook-returned full shapes.
For overridden schema hooks, or for any descriptor that differs from the default
descriptor, use a descriptor-derived name. Also fold the full field-spec identity
needed by runtime behavior into the token, including `input_attr`, `graphql_name`,
`source`, `kind`, and `related_model`.

Add tests that declare two mutations over the same serializer class with the same
field names but different hook-returned relation targets, then assert finalization
succeeds and the generated input names are distinct.

### Medium: the default schema hook can read an inherited parent mutation snapshot

`SerializerMutation.get_serializer_for_schema()` reads `cls._mutation_meta` when
it is non-`None`:

- `django_strawberry_framework/rest_framework/sets.py::SerializerMutation.get_serializer_for_schema`

During class creation, `DjangoMutationMetaclass.__new__` calls `_validate_meta`
before assigning the new class's own `_mutation_meta`:

- `django_strawberry_framework/mutations/sets.py::DjangoMutationMetaclass.__new__`
- `django_strawberry_framework/rest_framework/sets.py::SerializerMutation._validate_meta`

For a subclass of an existing concrete serializer mutation, `cls._mutation_meta`
can therefore be inherited from the parent during the child class's validation.
The default hook then discovers fields from the parent serializer while validating
the child's `Meta.serializer_class`.

I verified this with a local probe: a child mutation overriding
`Meta.serializer_class` to an `Item` serializer and `Meta.fields = ("category",)`
was rejected as unknown/non-writable because the hook had read the parent
`Category` serializer's field map.

Required correction: during default schema discovery, use only an own validated
snapshot, not an inherited one. For example, read
`cls.__dict__.get("_mutation_meta")`; if no own snapshot exists yet, fall back to
`cls.Meta.serializer_class`. Add a test where a concrete `SerializerMutation`
subclass defines a new `Meta.serializer_class` and validates against the child
serializer, not the parent.

Resolved items verified
-----------------------

- Mutation-level `Meta.optional_fields` is now normalized, validated, stored on
  `_ValidatedMutationMeta`, threaded into input generation, and serializer-level
  `Meta.optional_fields` is ignored.
- `get_serializer_for_schema()` now exists as a concrete classmethod hook and is
  used by validation/bind paths.
- `required=True, allow_null=True` fields now get an omittable nullable generated
  field so omission can reach DRF as missing while explicit `null` is preserved.
- Relation target models are recorded on `InputFieldSpec.related_model`, so the
  request path no longer re-runs schema discovery.
- Non-PK `RelatedField` variants now fail loud instead of being treated as
  pk-decoded relation inputs.
- Error-envelope paths now call `transaction.set_rollback(True)` in the shared
  write skeleton before returning a null-object payload.
- The dead public `get_serializer()` hook was removed.
- Fakeshop now has live renamed scalar/relation coverage keyed to `displayName`
  and `categoryPk`.

Validation notes
----------------

I ran two targeted `uv run python` probes for the remaining edge cases above. I
did not run pytest because the repository instructions say not to run pytest
unless explicitly asked.
