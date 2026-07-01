# Improvement pass: make serializer mutations better than graphene-django

Scope: reviewed the implemented serializer mutation lane in
`django_strawberry_framework/` against [spec-039][spec-039], the live-test policy in
[test_query/README.md][test-query-readme], and graphene-django's DRF integration under
`~/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django`.

Intent: this is not another parity review. Graphene-django is useful as a baseline, but the
goal should be a stricter, safer, more diagnosable implementation that follows this
package's DRF-first / fail-loud architecture.

I did not run pytest, per `AGENTS.md`; this is a static/code-path review.

## Highest-value improvements

### 1. Add a runtime schema/runtime serializer agreement guard

Graphene-django builds the schema and runtime serializer from the same no-arg serializer in
the common path, but it has no robust answer for schema-time hooks. This package added
`get_serializer_for_schema()`, which is the right extension point, but the framework can do
more: prove the schema-time field map and the runtime serializer still agree before
`serializer.is_valid()` runs.

Current risk: a schema hook can expose a field that the runtime serializer does not actually
declare, or declares with a different class/source/relation target. DRF may ignore unknown
incoming keys rather than failing in the way the GraphQL schema implies. The fakeshop
`TargetedShelfSerializer` fixture now avoids this, but the framework should enforce the
contract so users cannot recreate that bug.

Recommended design:

- After `_merged_serializer_kwargs()` constructs the runtime serializer in
  [`rest_framework/resolvers.py`][rf-resolvers] `::_serializer_write_step`, compare the
  bind-stashed `mutation_cls._input_field_specs` against `serializer.fields`.
- For every provided field, require the runtime serializer to contain `spec.target_name`,
  require it to be writable, and require its bound `source` to match the schema-time `source`.
- For relation fields, require the runtime field to still be `PrimaryKeyRelatedField` /
  `ManyRelatedField` over the same `related_model` recorded in the `InputFieldSpec`.
- For file/scalar fields, require the runtime kind to be compatible with the schema-time
  kind; if the runtime field moved from scalar to relation or file, raise a clear
  `ConfigurationError`.
- Run this before `is_valid()` so a schema/runtime mismatch is a framework configuration
  failure, not a serializer validation ambiguity.

This would be materially better than graphene-django because the schema hook becomes a
verified contract rather than a trust point.

### 2. Replace the broad `get_serializer_kwargs` create-required waiver with an explicit injection contract

[`rest_framework/sets.py`][rf-sets] `::SerializerMutation.build_input` currently waives the
create-required narrowing guard whenever a concrete mutation overrides
`get_serializer_kwargs`. That is safer than graphene-django's implicit behavior, but still
too broad: overriding the hook to add `context={"tenant": ...}` also waives required-field
coverage, even if the override does not supply the dropped required fields.

Recommended design:

- Add a declarative contract such as `Meta.injected_fields = ("tenant",)` or
  `Meta.supplied_serializer_fields = (...)`.
- `guard_create_required_serializer_fields()` should subtract only those declared injected
  fields, not every field whenever the hook is overridden.
- At runtime, verify that the final serializer kwargs/data actually include those injected
  fields before validation.
- Keep a compatibility path for the current broad waiver only if it raises a deprecation
  warning or is explicitly named as an unsafe legacy escape hatch.

This keeps the DRF hook, but makes it auditable. It is stricter than graphene-django and
better aligned with the package's "schema that can actually succeed" rule.

### 3. Make relation validation both visibility-scoped and query-efficient

The current implementation is much safer than graphene-django: it authorizes before decode,
type-checks `GlobalID`s, and visibility-checks relation ids through the target
`DjangoType.get_queryset`. The remaining improvement is performance and double validation.

Current shape: `_decode_relation_single()` fetches each visible object, then DRF's
`PrimaryKeyRelatedField` fetches it again during `serializer.is_valid()`. The live query
budget comments in fakeshop already show this duplicate relation SELECT.

Recommended design:

- Introduce a batched `visible_related_objects()` helper for multi relations and multiple
  same-target relation fields in one input. Decode/type-check all ids first, then perform
  one visibility-scoped `pk__in` query per target model/field.
- For runtime serializer validation, adapt relation field querysets to the same
  visibility-scoped queryset before `is_valid()` runs, so DRF's own lookup is the visibility
  lookup rather than an unscoped second fetch.
- Preserve the current no-existence-leak error surface: hidden, missing, wrong-type, and
  uncoercible relation ids still collapse to the same field-keyed relation error.
- Add live `assertNumQueries` coverage for single FK and many relation serializer mutations.

That would keep the security win over graphene-django while removing the performance cost
of doing the right thing.

### 4. Preserve DRF `ErrorDetail.code` in the GraphQL error envelope

Graphene-django flattens serializer errors to messages. This package already improves on
that with recursive paths, but it still drops DRF's structured error codes.

Recommended design:

- Extend the generated mutation error type additively with `codes: [String!]` or
  `details: [ValidationErrorDetail!]`.
- In `django_strawberry_framework/rest_framework/resolvers.py::serializer_errors_to_field_errors`,
  preserve each `ErrorDetail.code` alongside the message.
- For Django `ValidationError`, preserve `ValidationError.code` where available.
- Keep the existing `field` and `messages` fields intact for compatibility.

Clients should be able to branch on `required`, `invalid`, `unique`, etc. without parsing
localized human text. That would be a clear improvement over graphene-django.

### 5. Aggregate schema-time diagnostics instead of failing on the first bad field

The implementation currently fails loud, which is already better than graphene-django's
catch-all `serializers.Field -> String`. The next step is to fail loud with all actionable
errors at once.

Recommended design:

- During serializer input building, collect unsupported fields, non-PK relation fields,
  dotted/source-star fields, missing relation primary `DjangoType`s, GraphQL-name
  collisions, and source collisions.
- Raise one `ConfigurationError` with a bullet list grouped by serializer field name.
- Keep the existing precise messages as the per-field detail.

This matters for real serializers with many fields: the user should not have to fix one
field, rerun schema build, then discover the next unsupported field.

## Type-system improvements

### 6. Generate robust enums for serializer-only `ChoiceField`

Graphene-django generates enums for `ChoiceField`, but its approach is shallow. The local
implementation currently maps serializer-only `ChoiceField` to `str`, preserving runtime
validation but losing schema precision.

Recommended design:

- Keep the existing read-side model-choice enum reuse for model-backed fields.
- For serializer-only `ChoiceField`, generate a stable enum when choices are static and
  GraphQL-safe.
- For unsafe values, duplicate labels, dynamic choices, or values that cannot round-trip
  cleanly, fail with a precise `ConfigurationError` or explicitly fall back only when the
  mutation opts into a scalar choice field.
- Map `MultipleChoiceField` to `list[GeneratedEnum]` under the same rules.

This can be better than graphene-django by making enum generation deterministic,
descriptor-keyed, collision-safe, and explicit about fallback.

### 7. Expand known DRF scalar support without adding a catch-all

The previous review called out `serializers.DictField`; the broader improvement is a
capability matrix that intentionally supports common DRF scalar fields while keeping the
no-catch-all guarantee.

Candidates to evaluate explicitly:

- `serializers.DictField` and `serializers.HStoreField` -> `strawberry.scalars.JSON`.
- `serializers.IPAddressField`, `FilePathField`, and URL/path-like subclasses -> `str`.
- `serializers.DurationField` -> a deliberate scalar choice, not an accidental string.
- `serializers.ModelField` -> route through the wrapped Django model field when present,
  else fail loud.

Each mapping should have a live mutation test when reachable through fakeshop and a package
converter test as a narrow backstop. This gives users graphene-django's breadth without its
silent degradation.

### 8. Detect explicit model-backed serializer type overrides instead of silently choosing one source of truth

The previous parity review noted that explicit serializer field type overrides on
model-backed scalar fields are ignored because the current path routes scalars through the
model column converter. The better-than-graphene version should not simply copy graphene and
always trust the serializer field either; it should define a principled conflict policy.

Recommended design:

- Treat default `ModelSerializer`-generated fields as model-backed and use the read-side
  model converter for enum/read-write symmetry.
- Treat consumer-declared serializer fields as an explicit serializer contract.
- If the declared serializer field's GraphQL scalar disagrees with the model-column scalar,
  either honor the serializer field or raise a `ConfigurationError` requiring an explicit
  override policy. Do not silently pick the model column.
- Include `source` in the diagnostic so `display_name = CharField(source="name")` and true
  type mismatches are easy to tell apart.

That is better than both current behavior and graphene-django: the framework becomes
predictable instead of merely serializer-first or model-first.

## Schema and developer-experience improvements

### 9. Thread DRF field metadata into SDL deliberately

The shared input builder already supports field descriptions. Use that to expose DRF
metadata in a controlled way:

- `field.help_text` -> GraphQL input field description.
- `min_length`, `max_length`, `min_value`, `max_value`, `allow_blank`, and `allow_empty`
  can be appended to descriptions or surfaced through Strawberry extensions/directives if
  this project has a stable extension convention.
- Keep runtime validation in DRF; this is documentation/introspection, not a second
  validator.

Graphene-django only threads `help_text`. This package can do better by exposing a coherent
DRF validation summary without changing coercion semantics.

### 10. Fingerprint `get_serializer_for_schema()` for determinism

The spec requires schema-time hooks to return a stable, request-independent field shape.
The implementation calls the hook at class validation and again during binding. A
nondeterministic hook could validate one shape and bind another.

Recommended design:

- Compute a lightweight field-shape fingerprint at class validation: ordered field names,
  field classes, sources, read/write flags, relation target models, `required`,
  `allow_null`, and relevant converter discriminants.
- Recompute at bind and raise `ConfigurationError` if the hook drifted.
- Optionally store and reuse the class-validation field map when safe, but still guard
  against mutable field maps.

This turns a spec promise into an enforced contract. Graphene-django has no equivalent
because it has no schema/runtime hook split.

### 11. Add a public serializer-field converter registry

Fail-loud custom fields are correct, but consumers need a sanctioned way to support their
own DRF fields without patching the framework.

Recommended design:

- Provide `register_serializer_field_converter(FieldClass, converter, *, override=False)`.
- Keep the MRO dispatch and no base `serializers.Field` catch-all.
- Require converters to return the same structured conversion shape as built-in fields.
- Include a test proving a registered custom field maps, and an unregistered custom field
  still raises.

This is better than graphene-django's singledispatch plus catch-all because extension is
explicit and safe.

### 12. Add a serializer `save()` kwargs hook separate from constructor kwargs

DRF often expects request-derived data at `serializer.save(owner=...)`, not in
`serializer.__init__` or by mutating `data`. Graphene-django exposes `perform_mutate`, but
that bypasses too much framework-owned behavior.

Recommended design:

- Add `get_serializer_save_kwargs(info, data, instance=None) -> dict`.
- Call `serializer.save(**save_kwargs)` inside the existing value-preserving save closure.
- Validate that save kwargs do not shadow serializer input fields unless explicitly allowed.
- Keep `get_serializer_kwargs` for constructor/context customization only.

This gives consumers a DRF-native customization point while preserving transaction,
error-mapping, and refetch behavior.

### 13. Expose structured error paths in addition to dotted `field`

The current recursive flattener emits dotted paths like `items.0.name`. That is already
better than graphene-django's one-level mapping, but clients should not have to parse
strings.

Recommended design:

- Add an optional `path: [String!]` or `segments: [String!]` field to the error object.
- Keep `field` as the legacy dotted string.
- For root non-field errors, emit `field="__all__"` and `path=[]` or `["__all__"]` by a
  documented rule.

This is an additive client ergonomics improvement and pairs naturally with preserving DRF
error codes.

## Performance and correctness extensions

### 14. Add optional row locking for update mutations

The shared write pipeline runs inside `transaction.atomic()`, which is already stronger than
graphene-django. For high-contention updates, the framework could provide an opt-in
`select_for_update` path.

Recommended design:

- Add `Meta.select_for_update = True` or a hook returning lock options.
- Apply it only to update locate queries inside the existing transaction.
- Preserve visibility filtering before lock acquisition.
- Skip or clearly error on unsupported backends/options.

This is not needed for every app, but it is the kind of correctness control a production
mutation framework should expose.

### 15. Add a schema-shape debug/introspection registry for generated inputs

Descriptor-derived serializer input names can be long and hash-like by design. Debugging
would be easier if the framework exposed the shape reason.

Recommended design:

- Keep an internal registry from generated input name to `SerializerInputShape`.
- Provide a debug helper that prints the serializer class, operation, fields, sources,
  relation targets, requiredness, and why the canonical name was or was not used.
- Use it in `ConfigurationError` messages for materialization/name collisions.

Graphene-django's class-name cache can silently conflate shapes. This package already avoids
that; a debug registry would make the stronger behavior easier to understand.

### 16. Add golden SDL coverage for representative serializer inputs

The live tests introspect focused fields, which is good. A small golden SDL snapshot for the
serializer mutation input lane would catch cross-field drift more efficiently.

Recommended design:

- Keep it narrow: one products serializer mutation and one library schema-hook mutation.
- Assert generated input names, field names, nullability, descriptions, relation id scalar,
  and payload shape.
- Do not snapshot the whole schema.

This is especially valuable once enum generation, descriptions, error metadata, and custom
converter hooks are added.

## Keep these wins over graphene-django

Do not regress these while making the improvements above:

- Unsupported serializer fields fail loud instead of silently becoming `String`.
- Relation inputs are type-checked and visibility-checked before write.
- Authorization runs before relation decode.
- Runtime `context["request"]` is framework-owned and checked against the authorized actor.
- Update `partial=True` is framework-owned, not hook-owned.
- Serializer errors are recursively flattened and re-keyed to GraphQL wire names.
- Writes run inside the shared transaction boundary and refetch through the optimizer path.
- Serializer input shape identity is descriptor-based, not cached only by serializer class
  name.
- DRF remains a soft dependency at the package root.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[spec-039]: spec-039-serializer_mutations-0_0_13.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[rf-resolvers]: ../django_strawberry_framework/rest_framework/resolvers.py
[rf-sets]: ../django_strawberry_framework/rest_framework/sets.py

<!-- tests/ -->

<!-- examples/ -->
[test-query-readme]: ../examples/fakeshop/test_query/README.md

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
