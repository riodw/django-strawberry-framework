# Review - spec-031 GlobalID encoding, rev4 critical pass

## Findings

### P1 - `GlobalIDFilter` currently validates `type_name`, so model-label IDs will not round-trip through filters

The spec repeatedly states that filtering uses only the `node_id` slot and can stay unchanged. That conflicts with the current filter implementation. `django_strawberry_framework/filters/base.py::_decode_and_validate_global_id` decodes the incoming GlobalID and compares its `type_name` against `_expected_global_id_type_name`, which returns the owner or related target definition's `graphql_type_name`.

That means the planned default flip breaks a core live workflow: an emitted `ItemType.id` becomes `products.item:<pk>`, then `filter: { id: { exact: "<that id>" } }` reaches `GlobalIDFilter`, which still expects `ItemType` and raises `GraphQLError("GlobalID type mismatch...")`. The same issue applies to `GlobalIDMultipleChoiceFilter` and relation filters.

The spec needs to add the filter layer to the implementation plan instead of treating it as compatible. Recommended root fix: replace the single expected GraphQL type-name check with strategy-aware target validation. For an expected owner/target definition, the accepted payload shape should be defined explicitly:

- `model`: accept the model label for that model.
- `type`: accept the expected `graphql_type_name`.
- `type+model`: accept both.
- `callable` / `custom`: explicitly decide whether package `GlobalIDFilter` is unsupported for returned IDs, requires a consumer-owned validator, or falls back to node-id-only behavior.

Then add package tests under `tests/filters/` for own-PK, relation, multi-value, wrong-model/type rejection, and the callable/custom case. Slice 4's live HTTP filter round-trip should prove the returned model-label ID works through the real products API. Without this change, the spec's headline emitted-ID workflow regresses an already-shipped filter surface.

### P2 - Project-wide callable settings are accepted but not fully validated

Decision 7 says a callable `RELAY_GLOBALID_STRATEGY` setting is accepted as a project-wide custom encoder. Decision 6 validates callable arity and sync-ness only for `Meta.globalid_strategy` at type creation. The setting path currently only pins an unknown-string `ConfigurationError`, so a wrong-arity or `async def` callable supplied through settings can survive finalization and fail later from the installed `resolve_typename` closure.

The spec should make `_validate_globalid_strategy` reusable for both sources, with source-specific error text:

- `Meta.globalid_strategy`: type-creation error naming the type.
- `RELAY_GLOBALID_STRATEGY`: finalization error naming the setting.

Add tests for a well-formed callable setting, a wrong-arity callable setting, and an async callable setting. This keeps the fail-loud build-time posture consistent across the two configuration entry points.

### P2 - `decode_global_id` needs a runtime input-type and empty-payload contract

The spec covers malformed base64 / non-`type:id` strings, but it does not say what happens for arbitrary runtime values outside the annotation, such as `None`, `int`, a lazy object, or any non-`str` / non-`relay.GlobalID` value passed by future root-node code or tests. Without a guard, those paths can leak `AttributeError` / `TypeError` instead of the promised uniform `ConfigurationError`.

The spec should add an initial runtime gate:

```python
if not isinstance(gid, (relay.GlobalID, str)):
    raise ConfigurationError(...)
```

It should also decide whether empty `type_name` or empty `node_id` are valid after parsing. The callable encoder already rejects an empty type-name slot, so decode should at least reject empty `type_name`; rejecting an empty `node_id` is the safer root-node contract unless the package intentionally supports blank-string primary keys. Add tests for `None`, a non-string object, empty type-name, and empty node-id.

### P2 - `type+model` migration prose overpromises across GraphQL type renames

The `type+model` strategy accepts old type-anchored IDs only when the old GraphQL type name still resolves through `registry.definition_for_graphql_name`. If a consumer simultaneously renames `ItemType` / `Meta.name = "Item"` to a new GraphQL name, old cached IDs with the old type name still become undecodable. That is consistent with the stated "no rename-history alias map" non-goal, but the migration prose currently reads broader than the implementation can deliver.

The spec should tighten the upgrade sequence:

- First deploy `type+model` while the old GraphQL type names still exist.
- Let clients receive model-label IDs and age out old type-name IDs.
- Only then rename GraphQL type names, or provide a consumer alias/callable migration until `BACKLOG.md` item 39 exists.

This clarification belongs in Decision 9, Slice 5 docs, and the CHANGELOG/TODAY upgrade note.

### P3 - The live `type` opt-out test needs a deterministic schema-reload plan

Slice 4 says the live HTTP suite can prove the `type` opt-out either with `Meta.globalid_strategy = "type"` on one fakeshop type or with `RELAY_GLOBALID_STRATEGY = "type"`. The existing acceptance fixtures reload schemas at import/finalization time, so a settings override must be active before the schema reload; otherwise the test will accidentally exercise the default schema. Permanently changing an existing products type to `"type"` would also churn unrelated expected IDs and weaken the default-flip coverage.

The spec should pick a deterministic test shape. Preferred: factor the products reload fixture into a callable helper like the library suite already has, then use a test-local settings override plus `registry.clear()` / schema reload inside that test. Alternative: add a dedicated opt-out type/root field whose IDs are intentionally type-anchored. Either way, the implementation plan should name the setup so Slice 4 does not become a brittle import-order exercise.

## Confirmed Sound

The decision to keep `RELAY_GLOBALID_STRATEGY` domain validation out of `conf.py` is consistent with the existing settings architecture. There is no query-time overhead or thread-safety issue as long as `_resolve_globalid_strategy(definition)` runs only during finalization and the resolved `effective_globalid_strategy` is recorded on the definition. Decode and encode hot paths should read the recorded value / installed closure, not re-read settings per request.

One small spec cleanup: remove or rewrite any stale wording that says decode enforcement uses `_resolve_globalid_strategy`; the durable contract is now the recorded `effective_globalid_strategy`.
