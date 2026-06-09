# Review - spec-031 GlobalID encoding, rev2

## Findings

### P1 - Preserved `resolve_typename` overrides are not part of the decode contract

The rev2 fixes correctly move callable strategy onto the `resolve_typename(root, info)` seam, but the spec still preserves consumer-declared `resolve_typename` overrides without defining how they interact with `decode_global_id`.

That creates a concrete self-inconsistency. A type can override `resolve_typename` and emit `"LegacyItem"` or any custom label. Because the framework skips installing its strategy closure, that custom label is what Strawberry emits. But `_resolve_globalid_strategy(definition)` still resolves from `Meta.globalid_strategy` / setting / default, usually `"model"`, and Decision 8 Step 2 then rejects the emitted type-name payload as strategy-forbidden. In other words, a preserved override can make the framework emit IDs its own decoder refuses.

The spec needs a first-class rule here. Best root fix: detect a consumer `resolve_typename` override during Phase 2.5 and classify that type as custom/encode-only for framework decode unless the spec adds an explicit compatibility contract. If mixing an override with `Meta.globalid_strategy` is allowed, the spec must state which one wins and add tests proving decode either rejects with a clear `ConfigurationError` or round-trips only when the override returns the exact shape the strategy promises.

### P1 - Mixed primary/secondary strategies can emit model-label IDs that Step 2 rejects

Decision 8 says a model-label payload resolves through `registry.get(model)` to the primary type, then Step 2 enforces the primary candidate's effective strategy. The edge-case section says a model-strategy ID for a multi-type model decodes to the primary, while a sibling can opt into `type`.

Those two rules conflict when the primary is `type` and a secondary is left at the new default `model` (or explicitly uses `model` / `type+model`). The secondary emits `app_label.modelname:<pk>`, but decode resolves the label to the primary and rejects it because the primary's strategy is `type`. This is not exotic: the default is now `model`, so any secondary omitted from the strategy audit can mint undecodable IDs.

The spec should choose a single invariant and test it. Reasonable root fixes are either:

- validate at finalization that if any registered type for a model can emit model-label IDs, the primary type must accept model-label decode (`model` or `type+model`), or
- change Step 2 for model-label payloads to authorize the shape from the set of registered definitions for that model while still routing to the primary.

The first option is stricter and easier to reason about. Either way, add a multi-type test where the primary is `type` and a secondary is default `model`; the current prose leaves that case broken.

### P2 - Malformed string input and non-string callable output need pinned errors

`decode_global_id(gid: relay.GlobalID | str)` now rejects raw payloads and accepts base64 strings, but the spec does not say what happens when the string is malformed base64 or decodes to a non-`type:id` shape. Strawberry raises `GlobalIDValueError` / `ValueError` in those paths, while the spec otherwise standardizes decode failures on `ConfigurationError`.

Likewise, callable strategy says the callable "must synchronously return `str`", but there is no required wrapper behavior or test for a non-string return. Without an explicit package check, Strawberry's `_id` assertion is the likely failure mode.

Pin both as `ConfigurationError` with tests, or deliberately allow the Strawberry exceptions. The current spec leaves implementation and consumer-facing errors ambiguous.

## Resolved From Prior Pass

The previous P1/P2 items are fixed in rev2: callable no longer receives `node_id`, decode now has strategy-shape enforcement, type-name lookup keys on `graphql_type_name`, callable decode is explicitly encode-only, and `decode_global_id` no longer accepts raw payload strings.

## Validation

`uv run python scripts/check_spec_glossary.py --spec docs/spec-031-globalid_encoding-0_0_9.md` passes: `OK: 27 terms`.
