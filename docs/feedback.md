# Review Feedback for Relay Interfaces Diff

Overall, the implementation of the Relay interfaces slice is robust and correctly handles the complex intersection of Strawberry's interface machinery with Django query optimization. However, I have identified two significant bugs that contradict the design spec and cause incorrect behavior in edge cases.

## 1. Optimizer misses projecting custom primary keys for Relay nodes (Violates Decision 7)

**Location**: `django_strawberry_framework/optimizer/walker.py`

In `_walk_selections`, there is a comment claiming that `snake_case("id")` resolves to the model's pk `attname`. This is incorrect. `snake_case("id")` literally resolves to `"id"`. 

If a Django model has a custom primary key name (e.g., `"uuid"`), the `field_map` will be keyed by `"uuid"`. When a GraphQL query requests the `id` field (the Relay global ID), `field_map.get("id")` evaluates to `None`, causing the optimizer to completely skip projecting the primary key column into the `only()` clause. 

Because the primary key wasn't projected, `_resolve_id_default` cannot find the value in `root.__dict__` and falls back to `getattr(root, id_attr)`. This triggers a deferred load (an N+1 query per node), directly violating Decision 7 (no avoidable lazy loads on `resolve_id`).

**Recommended Fix**:
In `_walk_selections`, if `django_field` is `None`, add a specific check for Relay nodes requesting `id`. If it's a Relay node, resolve the actual `id_attr` (via `type_cls.resolve_id_attr()` falling back to the model's pk name) and append it to `plan.only_fields`.

## 2. Unconditional composite PK rejection ignores explicit `NodeID` annotations

**Location**: `django_strawberry_framework/types/relay.py`

The `_check_composite_pk_for_relay_node` function unconditionally raises a `ConfigurationError` if the underlying Django model uses a `CompositePrimaryKey`. However, the error message correctly suggests: *"Either declare an explicit id: relay.NodeID[...] annotation on the DjangoType or remove relay.Node from Meta.interfaces."*

The code contradicts the error message because it fails to check whether the consumer actually provided an explicit `relay.NodeID` annotation to bypass the composite PK issue! If a consumer provides a valid explicit `NodeID` annotation, they still get the `ConfigurationError`.

**Recommended Fix**:
Before raising the `ConfigurationError`, check if the consumer has overridden the ID attribute. You can do this by calling `type_cls.resolve_id_attr()` and catching `NodeIDAnnotationError`. Only raise the `ConfigurationError` if the resolved `id_attr` falls back to the default `"pk"`.
