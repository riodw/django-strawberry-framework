# Review - spec-031 GlobalID encoding

## Findings

### P1 - Callable encoder contract does not fit the chosen `resolve_typename` seam

The spec defines callable strategy as `my_encoder(type_cls, model, node_id, info) -> str`, but the selected Strawberry seam calls `resolve_typename(root, info)` before it calls `resolve_id(root, info=info)`. Supplying `node_id` to the callable would force the framework to call `resolve_id` from inside `resolve_typename`, then Strawberry would call it again. That is both extra work and a correctness break for async/custom `resolve_id`: Strawberry can await an awaitable `node_id` after `resolve_typename`, but `resolve_typename` itself must synchronously return `str`.

This contradicts the spec's own edge-case claim that async `resolve_id` is unaffected. The root fix is to make callable match the actual seam, for example `my_encoder(type_cls, model, root, info) -> str` or `my_encoder(definition, root, info) -> str`, and explicitly validate that it returns a `str` acceptable to Strawberry's `<type_name>:<node_id>` encoding. If node-id-dependent custom type-name slots are truly required, that is not compatible with the `resolve_typename` seam without a fuller custom `id` resolver design.

### P1 - Decode does not define strategy-shape enforcement

`decode_global_id(gid)` is specified as a payload-shape dispatcher: model-label payloads resolve through `apps.get_model(...)->registry.get(...)`, and type-name payloads resolve through the registry. Separately, the strategy table says `"model"` accepts model-label only, `"type"` accepts type-name only, and `"type+model"` accepts both. The spec never states the required second step: after a candidate type is resolved, inspect that type's effective strategy and reject payload shapes the strategy does not permit.

Without that rule, an implementation will likely accept every resolvable model-label or type-name ID globally. That makes `type+model` indistinguishable from the default decoder behavior, lets `"model"` keep accepting old type-anchored IDs, and weakens the documented type-scoped identity use case for `"type"`.

The spec should require decode to resolve a candidate type first, then validate the input shape against `_resolve_globalid_strategy(candidate_definition)`: model-label only for `"model"` / `"type+model"`, type-name only for `"type"` / `"type+model"`, and callable only through an explicitly specified decoder contract. Add negative tests for model-strategy rejecting a type-name ID and type-strategy rejecting a model-label ID.

### P1 - Type-name decode must key on GraphQL name, not class `__name__`

Decision 4 correctly says the `"type"` strategy payload is the GraphQL type name, including `Meta.name`. Decision 8 and the test plan then say type-name decode uses a `__name__` registry lookup. Those are not equivalent. A class `ItemType` with `Meta.name = "Item"` would emit `Item:<pk>` under the `"type"` strategy, but a `__name__` lookup for `Item` cannot find `ItemType`.

The decode side needs a lookup by `DjangoTypeDefinition.graphql_type_name`, not by `type_cls.__name__`. The spec should name the required registry helper or index, and the Slice 3 tests should include a `Meta.name` type-strategy round-trip so this cannot regress.

### P2 - Callable decode is required by the test plan but left as an open question

The risks section says callable decoder registration is still open, but Slice 3 requires callable decode paths and `test_encode_decode_round_trip_all_strategies`. That is not implementable from the current spec unless the callable happens to emit a model label or GraphQL type name.

Either remove callable from decode symmetry in this card and document it as encode-only until `032`, or specify the paired decoder API now. Leaving it as both required and unresolved will push the ambiguity into code.

### P3 - Decode examples blur raw payloads and encoded GlobalIDs

The API and test-plan examples use shorthand like `decode_global_id("products.item:42")`, but the actual input is presumably a Relay base64 GlobalID string or a `relay.GlobalID` instance. The spec should say exactly which input shapes `decode_global_id` accepts, and tests should use encoded values except where a lower-level helper is explicitly under test.

## Validation

`uv run python scripts/check_spec_glossary.py --spec docs/spec-031-globalid_encoding-0_0_9.md` passes: `OK: 27 terms`.
