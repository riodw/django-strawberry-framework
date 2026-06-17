# Spec 036 architecture review

Scope: full reread of `docs/spec-036-mutations-0_0_11.md`, cross-checked against the
TODO anchors, the existing finalizer and registry shape, Relay global ID handling, settings
handling, and the fakeshop test placement rules.

Verdict: the spec direction is sound, but it is not ready for production implementation until
the high-severity contract gaps below are resolved. Most issues are not about whether the lines
can be reached; they are about whether the mutation foundation will keep the same contract pressure
as the existing query/filter/relay surface.

## Findings

### High - Generated input names conflict with mutation-level narrowing

Decision 6 says generated inputs use stable model names such as `CategoryInput` and
`CategoryPartialInput`, and that two mutations over one model share the same input type. The same
decision also allows each mutation to narrow editable fields with `Meta.fields` and `Meta.exclude`.

Those two requirements conflict. Two create mutations for the same model can have different field
sets, but GraphQL type names are schema-global. Reusing `CategoryInput` would either leak fields
that one mutation meant to exclude or accidentally make another mutation too narrow.

Required spec correction:

- Define the generated input cache key as the complete input shape, not only the model.
- Either include the mutation class name or a deterministic field-shape suffix in generated type
  names when `Meta.fields` or `Meta.exclude` narrows the model.
- If the release wants stable model-only names, then remove mutation-specific generated narrowing
  from 0.0.11 and require custom input classes for divergent shapes.

### High - Partial update validation can skip composite constraints

Decision 8 says partial updates call `full_clean(exclude=<fields the PartialInput did not
provide>)`. That is too broad for Django constraint validation. If `Item.name` is updated without
providing `category`, excluding `category` can skip validation of the `unique_item_per_category`
constraint even though the current instance has a category value.

This conflicts with the stated requirement that duplicate unique constraints produce `FieldError`
before save.

Required spec correction:

- Partial updates must validate the updated instance with current database values filled in.
- `exclude` must not exclude unprovided fields that participate in constraints with any provided
  field.
- Add an explicit acceptance case: updating only `Item.name` to collide with another item in the
  same category returns a field or non-field validation error before save.

### High - Create authorization contradicts the live test plan

Decision 9 explicitly defers create authorization and says create refetches by primary key without
visibility filtering. Decision 10 limits `get_queryset` authorization to update/delete lookup. The
test plan then asks for an anonymous request that cannot mutate at all.

That is not currently derivable from the foundation contract. Without a create-time permission hook,
anonymous create will succeed unless the example schema adds ad hoc product-specific checks, which
would undermine the reusable mutation API being specified.

Required spec correction:

- Either add a minimal mutation permission hook for 0.0.11, such as
  `check_permission(info, operation, input)` or a DRF-like `get_permissions`, and use it for create,
  update, and delete.
- Or remove the "anonymous request cannot mutate at all" acceptance case from 0.0.11 and make
  create authorization explicitly out of scope.

The first option is architecturally stronger because it avoids shipping write APIs that can only be
made safe with per-schema resolver workarounds.

### High - Relation GlobalID decoding must enforce target type

The spec says foreign key inputs use `<field>_id` and Relay targets accept GlobalIDs. It does not
explicitly require that the decoded GlobalID type matches the target relation model.

That is a correctness hole. A well-formed `Item` GlobalID passed to a `category_id` input must not
be treated as a raw primary key and looked up against `Category`, even if the numeric primary keys
happen to overlap.

Required spec correction:

- Relation ID decoding must verify the decoded type/model against the Django relation target before
  lookup.
- Wrong-type IDs must return `FieldError`, not `DoesNotExist`, and must not perform a cross-model
  primary-key lookup.
- Add live or package acceptance coverage for a valid but wrong-type GlobalID.

### High - Payload object field naming is underspecified

The example uses `CreateItemPayload { item: ItemType errors: [FieldError!]! }`, but the spec never
defines how the object field name is derived. This matters for `Category`, `Item`, `Property`, and
any future model whose lowercase model name collides with Python or GraphQL naming constraints.

Required spec correction:

- Define the payload object field naming rule.
- Define collision behavior.
- Pin the expected payload field names for the fakeshop models, including `Property`.

A uniform name such as `node` is simpler and avoids model-name edge cases. If the spec keeps
model-derived names, the generated class builder needs explicit collision guards and tests.

### Medium - Many-to-many write semantics are in scope but not defined

Decision 6 includes many-to-many fields in generated inputs, but the resolver pipeline never states
whether a provided list replaces the entire relation, appends to it, or clears it when the list is
empty.

Required spec correction:

- State that omitted many-to-many fields are unchanged on update.
- State whether a provided list replaces the complete relation set.
- State that an empty list clears the relation if the field is provided.
- State whether related object lookup uses the target model default manager or a mutation queryset
  hook.

This can remain package-internal test coverage because fakeshop products do not currently expose a
many-to-many model.

### Medium - Custom input classes need a mapping contract

The spec allows `input_class` to override generated inputs, but it only requires a Strawberry input
class. The resolver still needs a deterministic mapping from input attributes to Django model fields,
relation ID fields, and many-to-many fields.

Required spec correction:

- Either restrict custom inputs in 0.0.11 to the same generated field names and relation ID naming
  scheme.
- Or add an explicit mapping API for custom input fields.

Without this, a custom input can type-check as Strawberry input while still being impossible to
apply safely to the model.

### Medium - Non-field error sentinel is ambiguous

The spec says non-field validation errors use an "empty / sentinel" field value. That value must be
part of the public GraphQL contract.

Required spec correction:

- Pick one sentinel, preferably Django's `__all__`, and use it consistently for model-level and
  constraint-level errors.
- Add an acceptance test for a `UniqueConstraint` or `clean()` error that maps to the sentinel.

### Medium - Transaction and async write boundaries are under-specified

The resolver plan mentions sync and async pipelines and wrapping sync `get_queryset` with
`sync_to_async` in async paths. It does not specify the transaction boundary for decode, validation,
write, relation assignment, refetch, and payload construction.

Required spec correction:

- The write path should run inside `transaction.atomic()`.
- Relation assignments and payload refetch/snapshot should be inside the same transaction.
- The async path should either use a true async ORM path or run the synchronous ORM write pipeline
  in one `sync_to_async(..., thread_sensitive=True)` call.

Multiple sync ORM calls separated by awaits would be a fragile foundation and difficult to reason
about under concurrent requests.

### Medium - Delete payload semantics need deeper snapshot rules

The spec says delete returns a pre-delete object snapshot and loads selected relations before
deletion. It does not define how far nested selections, reverse relations, or connection children
must be materialized before the delete occurs.

Required spec correction:

- Define that the response selection snapshot must be fully evaluated before deletion.
- Include nested selected relations and connection children in that snapshot rule.
- Keep the snapshot and deletion in one transaction.

Without this, a resolver can appear to work for scalar fields while failing or silently changing
behavior for selected relations after cascading deletes.

### Medium - Generated payload and helper type collisions need a rule

Generated GraphQL type names are schema-global. The spec names `CreateItemPayload`, `UpdateItemInput`,
and similar helper classes, but it does not define behavior when two apps or modules declare mutation
classes that would generate the same GraphQL name.

Required spec correction:

- Define whether duplicate generated names are rejected with `ConfigurationError` or disambiguated
  by mutation class/module identity.
- Add a package-level collision test.

The existing framework tends to favor early configuration errors over silent schema drift; the
mutation spec should keep that posture.

### Medium - The live SQL assertions may be too brittle as written

The test plan asks live HTTP tests to prove mutation response optimization and no deferred loading.
Over `/graphql/`, SQL capture can prove broad behavior, but it is brittle for exact selected columns
and cannot directly inspect the returned Django instance's `deferred_loading` state.

Required spec correction:

- Keep the live fakeshop test responsible for real `/graphql/` behavior, response shape, bounded
  query count, and no accidental lazy query regressions visible through SQL capture.
- Put exact queryset/deferred-loading assertions in package-level tests around the optimizer or
  resolver internals.

This preserves real-world coverage without turning live tests into SQL string snapshots.

### Low - The "input target" wording can mislead implementation

Several passages say mutation input generation resolves the primary `DjangoType`. The primary type
is needed for return payloads and relation GlobalID strategy, but generated input fields should come
from editable Django model fields, not from the read-side `DjangoType` field list.

Required spec correction:

- State explicitly that the primary `DjangoType` is not the source of generated input fields.
- Generated input fields come from the model plus the mutation's write-side `Meta.fields`,
  `Meta.exclude`, and custom input settings.

## Configuration and performance note

The setting-read concern does not appear to belong to this mutation spec. Spec 036 says no new
settings key is added for mutations.

For the existing Relay global ID setting, the current placement is architecturally acceptable:

- `django_strawberry_framework/conf.py::Settings` reads and normalizes the consumer settings dict.
- Domain validation lives near the consuming feature in
  `django_strawberry_framework/types/base.py::_validate_globalid_strategy`.
- `django_strawberry_framework/types/relay.py::_resolve_globalid_strategy` reads
  `RELAY_GLOBALID_STRATEGY` during type finalization.
- `django_strawberry_framework/types/relay.py::install_globalid_typename_resolver` records the
  effective strategy on the finalized type definition and installs the resolver closure.

That means the setting is not repeatedly validated during query execution. It is evaluated at schema
construction/finalization time, which avoids the runtime overhead and thread-safety concerns raised
in the prompt. Moving this validation into `conf.py` would make the settings reader more coupled to
feature-specific semantics without improving request-time behavior.

No spec 036 correction is needed for this point, except to avoid adding mutation settings unless the
feature that needs them actually lands.

## Test and documentation corrections

Before implementation, update the spec test plan with these requirements:

- Live fakeshop mutation tests must start with `seed_data(N)` or `create_users(N)` as required by
  the repository rules.
- Live tests own behavior reachable through `/graphql/`: success payloads, validation payloads,
  permission behavior, GlobalID behavior, and response shape.
- Package tests own internals that cannot be robustly asserted over HTTP: generated class caches,
  duplicate name errors, exact deferred-loading state, custom input mapping failures, async pipeline
  internals, and many-to-many behavior if fakeshop has no many-to-many model.
- Documentation must define the final public names for generated inputs, payloads, `FieldError`,
  relation ID inputs, and non-field error sentinel values.

## Bottom line

The spec should be revised before production code starts. The highest-priority fixes are generated
input naming, partial update constraint validation, create authorization, relation GlobalID type
checking, and payload field naming. Those define the public contract; changing them after 0.0.11
would create avoidable compatibility debt.
