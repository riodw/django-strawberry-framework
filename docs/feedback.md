Spec-039 implementation review
==============================

Review scope: the implemented spec-039 diff through `HEAD`, with emphasis on the
new `SerializerMutation` public surface, generated input binding, serializer
resolver path, and the fakeshop/live-test coverage implied by the spec.

Overall assessment: not ready to merge as-is. The broad architecture is on the
right track, especially the reuse of the shared mutation pipeline and the DRF soft
dependency guard, but several implementation choices break explicit spec
contracts or create public hooks that do not do what they claim. The most
important problems are semantic, not formatting issues.

Findings
--------

### Critical: `Meta.optional_fields` is read from the serializer, not the mutation

The spec repeatedly defines `optional_fields` as part of the consumer-facing
`SerializerMutation.Meta` namespace:

- `docs/spec-039-serializer_mutations-0_0_13.md` says the public surface is
  `serializer_class` plus `operation` and optional `fields` / `exclude` /
  `optional_fields`.
- It says `Meta.optional_fields` changes create-input requiredness, is a no-op on
  update, is validated against the effective serializer field set, and participates
  in serializer input shape identity.

The implementation allows `SerializerMutation.Meta.optional_fields`, but does not
use it:

- `django_strawberry_framework/rest_framework/sets.py::SerializerMutation._validate_meta`
  accepts the key but does not normalize it or store it.
- `django_strawberry_framework/mutations/sets.py::_ValidatedMutationMeta.__init__`
  has no `optional_fields` slot and explicitly says the generator re-reads it from
  the serializer's own `Meta`.
- `django_strawberry_framework/rest_framework/inputs.py::resolve_optional_fields`
  reads `serializer_class.Meta.optional_fields`.

That means a consumer writing the API the spec documents gets no effect:

```python
class CreateItem(SerializerMutation):
    class Meta:
        serializer_class = ItemSerializer
        operation = "create"
        optional_fields = ("name",)
```

`name` still behaves as required, and a bad mutation-level value such as
`optional_fields = "__all__"` is silently ignored after the allowed-key check. The
tests currently mask this by putting `optional_fields` on the serializer class's
own `Meta`, which is a different API.

Required correction: move `optional_fields` into the validated mutation meta
snapshot, normalize and validate it against the effective serializer field set at
class creation or bind, pass it into `build_serializer_input_class`, and include it
in the serializer input shape/cache identity. Do not read
`serializer_class.Meta.optional_fields` unless the spec is changed to make that
the public contract.

### Critical: the `get_serializer_for_schema()` classmethod hook is missing

Decision 7 requires an overridable `get_serializer_for_schema()` classmethod on
the mutation, with the default no-arg serializer discovery as the fallback. The
implementation only provides a module-level helper:

- `django_strawberry_framework/rest_framework/inputs.py::get_serializer_for_schema`
- `django_strawberry_framework/rest_framework/inputs.py::resolve_effective_serializer_fields`
- `django_strawberry_framework/rest_framework/sets.py::SerializerMutation.build_input`

There is no `SerializerMutation.get_serializer_for_schema()` for consumers to
override. As a result, serializers whose fields require stable schema-time context
cannot implement the spec's escape hatch. The tests simulate the hook by
monkeypatching the module-level function, so they do not prove the public API.

This also interacts with caching. `SerializerMutation.build_input` keys the
serializer shape cache by `(serializer_class, operation_kind, effective_names)`.
The spec says shape identity includes the emitted field specs and normalized
`optional_fields`, so two mutation declarations using the same serializer and same
field names but different hook-returned specs or optionalness must not reuse the
same input class.

Required correction: add the classmethod on `SerializerMutation`, make the bind
path call the mutation class hook rather than the module helper directly, and key
the cache with the actual normalized shape descriptor or with all inputs needed to
derive it. Add tests with a concrete mutation subclass overriding the classmethod;
do not rely on monkeypatching `rest_framework.inputs.get_serializer_for_schema`.

### High: `required=True, allow_null=True` can fail before DRF validation

The spec's M2 contract is precise: `required=True, allow_null=True` should produce
a nullable GraphQL annotation, preserve explicit `null`, and still let omission
reach DRF as a missing key so `serializer.is_valid()` returns the field-keyed
required error.

The current builder widens the annotation but only assigns
`default=strawberry.UNSET` when the field is not required:

- `django_strawberry_framework/rest_framework/inputs.py::build_serializer_input_class`

For a required nullable Strawberry input field with no default, omitting the key
can fail during input dataclass construction before the resolver gets to DRF. I
confirmed this with a minimal Strawberry schema: `{ data: {} }` against an input
field typed `str | None` with no default raises a top-level constructor error
instead of an in-band serializer `FieldError`.

Required correction: required nullable fields need an input shape that allows the
key to be omitted at GraphQL coercion time while preserving omission as
`strawberry.UNSET` for the resolver. The resolver should then skip `UNSET` values
so DRF sees the field as missing and raises its normal required error. Add live or
resolver-level tests for both omission and explicit `null`.

### High: relation target models are rediscovered on every request

The serializer input build already computes per-field specs and stashes them on
the mutation. The resolver then ignores those bind-time facts for target-model
lookup and re-materializes the serializer field set during each mutation request:

- `django_strawberry_framework/rest_framework/resolvers.py::_relation_target_models`
- `django_strawberry_framework/rest_framework/resolvers.py::_decode_serializer_data`

This has two problems. First, it adds avoidable per-request serializer discovery
and validation overhead on the hot path. Second, once the schema-time classmethod
hook is implemented, runtime rediscovery can drift from the field map that
generated the input or fail for serializers that only support schema-time field
discovery through the hook.

Required correction: carry the relation target model in the bind-time reverse-map
data, either by extending `InputFieldSpec` or by stashing a parallel immutable map
on the mutation class. `_decode_serializer_data` should decode from the stashed
specs only and should not call schema discovery during query execution.

### High: non-PK DRF relation fields are accepted but decoded as primary keys

The spec supports `PrimaryKeyRelatedField` and DRF's `ManyRelatedField` wrapper
for `PrimaryKeyRelatedField(many=True)`. The converter currently accepts every
subclass of `serializers.RelatedField`:

- `django_strawberry_framework/rest_framework/serializer_converter.py::convert_serializer_field`
- `django_strawberry_framework/rest_framework/serializer_converter.py::resolve_serializer_field`
- `django_strawberry_framework/rest_framework/resolvers.py::_decode_relation_single`

That silently treats `SlugRelatedField`, `HyperlinkedRelatedField`, and custom
writeable `RelatedField` subclasses as `GlobalID`/raw-pk inputs. The resolver then
passes a pk into a DRF field that may expect a slug, URL, or custom representation.
This is worse than fail-loud because the generated GraphQL contract is wrong for
the serializer's declared semantics.

Required correction: narrow support to `serializers.PrimaryKeyRelatedField` and to
`serializers.ManyRelatedField` whose `child_relation` is a
`PrimaryKeyRelatedField`. Raise `ConfigurationError` for other writable
`RelatedField` subclasses until the spec intentionally defines their input shape
and decode semantics. Add tests for `SlugRelatedField` and a `ManyRelatedField`
wrapping a non-PK child.

### High: save-time validation errors can commit partial writes

The shared write skeleton wraps the pipeline in `transaction.atomic()`:

- `django_strawberry_framework/mutations/resolvers.py::run_write_pipeline_sync`

The serializer write step catches save-time DRF and Django validation exceptions
and returns a `FieldError` list:

- `django_strawberry_framework/rest_framework/resolvers.py::_serializer_write_step`

If a custom `serializer.save()` writes to the database and then raises
`serializers.ValidationError` or `django.core.exceptions.ValidationError`, the
exception is swallowed inside the atomic block and no rollback is requested. The
mutation returns an error payload, but the earlier write can still commit.

Required correction: when mapping save-time validation exceptions to the envelope
inside the atomic block, explicitly mark the transaction for rollback before
returning the error payload, or move exception-to-envelope conversion outside the
atomic boundary while preserving the null-object payload contract. Add a test with
a serializer whose `save()` creates a row and then raises validation, and assert
that the row is not persisted.

### Medium: `get_serializer()` is a public dead hook

`SerializerMutation` defines and documents `get_serializer()` as the coarse
construction hook:

- `django_strawberry_framework/rest_framework/sets.py::SerializerMutation.get_serializer`

The resolver never calls it; it calls `get_serializer_kwargs()` directly and then
constructs `serializer_class(**kwargs)` itself:

- `django_strawberry_framework/rest_framework/resolvers.py::_serializer_write_step`
- `django_strawberry_framework/rest_framework/resolvers.py::_merged_serializer_kwargs`

The current docstring says the Slice-3 resolver routes through `get_serializer()`,
which is false. A consumer override of `get_serializer()` is silently ignored.
This also makes the create-required guard waiver narrower than the implementation
comments imply.

Required correction: either remove `get_serializer()` from the public surface and
docs, or route construction through it after applying the framework-owned
`partial` and `context["request"]` invariants. If the hook stays, the guard waiver
must consider either `get_serializer_kwargs` or `get_serializer`, and tests should
prove that a `get_serializer()` override is honored.

### Medium: live coverage does not yet prove the renamed-field error path

The spec's test plan calls out live fakeshop coverage for a serializer renamed
`PrimaryKeyRelatedField`, including validation/error reporting through the GraphQL
wire name. The current live coverage exercises the normal `category` relation
shape and the happy-path reverse map, but I did not find a live `/graphql` test
that drives a renamed serializer relation or renamed scalar validation failure
through the payload error envelope.

Relevant areas:

- `examples/fakeshop/test_query/test_products_api.py`
- `django_strawberry_framework/rest_framework/resolvers.py::serializer_errors_to_field_errors`
- `django_strawberry_framework/rest_framework/serializer_converter.py::resolve_serializer_field`

Required correction: add a real fakeshop GraphQL test with a serializer field such
as `category_pk = PrimaryKeyRelatedField(source="category", ...)` exposed as
`categoryPk`, then assert that hidden/wrong/missing ids and DRF validation errors
are keyed to the GraphQL field name.

Test gaps to close
------------------

Add tests that fail on the current implementation before applying fixes:

- Mutation-level `Meta.optional_fields` forces create optionalness; serializer-level
  `Meta.optional_fields` does not accidentally become the public API.
- Mutation-level `Meta.optional_fields = "__all__"` is rejected as a bare string.
- Two declarations with the same serializer and effective field names but different
  `optional_fields` or schema-hook field specs produce distinct deterministic input
  names and do not reuse a stale cached class.
- A concrete `SerializerMutation.get_serializer_for_schema()` classmethod override
  is used by bind/finalize; no monkeypatching of the module helper.
- `required=True, allow_null=True` omission returns an in-band DRF required error,
  while explicit `null` reaches DRF as `None`.
- `SlugRelatedField` and non-PK `ManyRelatedField` fail loudly at schema bind.
- Save-time DRF/Django validation after a partial database write rolls back the
  write.
- If retained, `get_serializer()` override is called by the resolver.

Notes
-----

I am not flagging the unchanged package version. The spec explicitly defers the
0.0.13 version bump until the joint card-039/card-040 release cut.

I did not run pytest for this review because the repository instructions say not
to run pytest unless explicitly asked.
