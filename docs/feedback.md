# Spec 036 implementation review

Scope: current implementation of [`spec-036-mutations-0_0_11.md`](spec-036-mutations-0_0_11.md),
reviewed against the revised spec, the mutation code, products live surface, and the package
tests. I did not run pytest, per repository instruction; this is a static/code-path review with
light source introspection.

Verdict: the implementation is close in shape, but it is not production-ready. The biggest
remaining issues are not cosmetic: the root mutation id path can mutate/delete by the wrong
GlobalID type, relation writes can attach hidden related rows, and delete payloads likely lose the
id the spec promises for cache eviction.

## Findings

### P1 - `update` / `delete` accept a wrong-type GlobalID as a raw pk

`django_strawberry_framework/mutations/resolvers.py::_coerce_lookup_id` decodes a base64
GlobalID with `relay.GlobalID.from_id(id).node_id` and discards the decoded type name. That means
`updateItem(id: <Category GlobalID>)` can update `Item(pk=<same numeric id>)` if the pks overlap.
Malformed strings also fall through as raw pk values, so an integer-pk model can raise a Django
coercion error instead of returning the mutation envelope.

This breaks the same no-cross-model rule the spec requires for relation ids and is worse on the
root id because it targets the object being mutated/deleted.

Required fix:

- Replace `_coerce_lookup_id` with a target-aware decoder, e.g. decode through
  `django_strawberry_framework/types/relay.py::decode_global_id`, verify the resolved model is the
  mutation target model, and return a `FieldError(field="id", ...)` on malformed or wrong-type ids.
- Do not run the queryset lookup after a wrong-type id.
- Add package and live coverage for `updateItem(id: <Category GlobalID>)` and
  `deleteItem(id: <Category GlobalID>)` where an `Item` with the same numeric pk exists.

### P1 - Relation id writes do not enforce target visibility

`django_strawberry_framework/mutations/resolvers.py::_decode_single_relation_id` type-checks a
Relay GlobalID, then returns `value.node_id`. It never resolves the related row through the related
target type's `get_queryset`. The later `full_clean()` FK validation uses Django's default manager,
not the GraphQL visibility queryset.

So a non-staff caller can create or update an `Item` pointing at a private `Category` they cannot
see, as long as they hold the write permission. The spec explicitly says a relation id for a row the
caller cannot see should become a `FieldError` on that relation field, with no existence leak. The
same issue applies to M2M id lists.

Required fix:

- During relation decode, after type validation, locate the related row through the related model's
  primary `DjangoType` visibility queryset (`initial_queryset` + `apply_type_visibility_sync`) and
  return a field-keyed error when it is absent/hidden.
- Apply this to FK, O2O, and M2M ids.
- Add live fakeshop coverage for `createItem(categoryId: <private category gid>)` as a non-staff
  permitted writer, plus package coverage for M2M hidden related ids.

### P1 - Delete payloads likely lose the deleted node id

`django_strawberry_framework/mutations/resolvers.py::_run_delete` fetches `snapshot`, then calls
`snapshot.delete()`, then returns that same instance in the payload. Django clears the instance's pk
after deletion. The live test query selects `node { id name category { name } }`, and the test
docstring says the id is preserved, but `examples/fakeshop/test_query/test_products_api.py::test_delete_item_happy_path`
never asserts the returned id.

The result is likely `node.id` encoding a `None` pk, or at least no guarantee of the original id.
That breaks the spec's cache-eviction promise for delete payloads.

Required fix:

- Preserve the original pk before deletion and return a detached snapshot whose pk/id attribute is
  restored after `delete()`, or delete through a separate instance/queryset while keeping the
  snapshot untouched.
- Assert the returned delete payload id decodes to the original id in both package and live tests.

### P2 - Public SDL contract drift: spec says `GlobalID!`, implementation emits `ID!`

`django_strawberry_framework/mutations/fields.py::_synthesized_mutation_signature` emits
`id: ID!` for update/delete, and the live tests use `ID!`. The spec's user-facing API and DoD still
say `id: GlobalID!`. This is not just cosmetic for clients or generated types: it changes where
malformed values are rejected and is part of the public GraphQL schema.

Required fix:

- Choose one contract. If server-side decoding via `ID!` is intentional, update the spec, glossary,
  README/TODAY examples, and tests to say `ID!` and document that the resolver performs GlobalID
  validation.
- If `GlobalID!` remains the contract, change the field signature and decide which malformed-id
  failures can realistically be in-band rather than Strawberry variable-coercion errors.

### P2 - `Meta.permission_classes` is not validated

The spec's DoD says an invalid permission class entry is rejected. In
`django_strawberry_framework/mutations/sets.py::_validate_mutation_meta`, `permission_classes` is
stored verbatim. The first real request then does `permission_class().has_permission(...)` in
`django_strawberry_framework/mutations/sets.py::DjangoMutation.check_permission`, so a bad entry
becomes a runtime `TypeError` / `AttributeError` instead of a class-creation `ConfigurationError`.

Required fix:

- Normalize `permission_classes` to a tuple/list and validate each entry is an instantiable class
  exposing `has_permission`.
- Add a `tests/mutations/test_sets.py` case for bad entries.

### P2 - Nullable M2M input can crash the resolver

Generated optional fields use `annotation | None` with `default=strawberry.UNSET`. For M2M this
means a client can send `genres: null`. `django_strawberry_framework/mutations/resolvers.py::_decode_relation_id_list`
then iterates `value` unconditionally, so `None` becomes a resolver exception instead of a typed
mutation error.

Required fix:

- Define the contract for explicit `null` on M2M: reject as a `FieldError`, treat as clear, or make
  the generated type non-null-list-but-omittable if Strawberry supports that shape cleanly.
- Add package coverage for omitted, empty list, valid list, wrong-type id, and explicit null.

### P2 - Malformed relation GlobalIDs are not pinned to the promised envelope

The resolver comments say malformed relation ids become `FieldError`, but generated relation inputs
use `strawberry.relay.GlobalID`. Strawberry can reject malformed GlobalID variable values during
argument coercion before `django_strawberry_framework/mutations/resolvers.py::_wrong_type_field_error`
ever runs. Existing tests pin valid-but-wrong-type ids, not malformed ids.

Required fix:

- Add an executable test for malformed `categoryId`.
- If Strawberry coercion prevents in-band handling, update the spec to reserve `FieldError` for
  well-formed-but-invalid/wrong-type ids and document malformed ids as top-level GraphQL errors.

### Process check - `CHANGELOG.md` was edited

The current tree contains `CHANGELOG.md` mutation bullets. That is only compliant if the Slice 5
maintainer prompt explicitly authorized a changelog edit. If that explicit instruction did not
happen, this violates the repo rule and the spec's own warning that design docs cannot grant
`CHANGELOG.md` permission.

Required fix:

- Verify the maintainer explicitly requested the changelog edit for this implementation pass.
- If not, remove or defer the changelog bullets until the joint `0.0.11` cut / authorized Slice 5
  prompt.

## What looks sound

- The earlier architecture corrections mostly landed: generated inputs derive from editable model
  fields, narrowed shapes use shape-derived names, payload slots are `node` / `result`, write auth
  is separate from visibility, and the optimizer payload-selection extractor exists.
- The live products surface follows the `examples/fakeshop/test_query/README.md` priority: core
  reachable behavior is tested over `/graphql/`, with package tests covering internals.
- The version boundary is preserved: package version remains `0.0.10`, with the joint `0.0.11` cut
  still owning the version bump.

## Bottom line

Fix the root id type-check, relation visibility checks, and delete id preservation before treating
036 as shipped. Those are public-contract and security/correctness issues; the remaining P2 items
are smaller but should be resolved before the mutation surface becomes a base for the form and
serializer cards.
