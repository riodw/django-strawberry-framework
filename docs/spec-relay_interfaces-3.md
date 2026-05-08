# Spec: Relay Interfaces (0.0.5)

## Problem statement
`DjangoType` users cannot declare GraphQL interfaces (Relay `Node` or otherwise) through `class Meta`. Today `Meta.interfaces` is rejected with `ConfigurationError` because the package does not apply it end-to-end. The result is that:
- `GOAL.md`'s target API (`interfaces = (relay.Node,)`) is unreachable today.
- `TODAY.md` lists Relay node and connection support as a hard blocker for the rich fakeshop schema.
- `docs/FEATURES.md` lists `Meta.interfaces` and `GlobalID` mapping in the deferred set.
- `KANBAN.md` `READY-004` and `BACKLOG-005` cannot land without a Relay foundation.
- `NEXT-005` (`DjangoConnectionField`) and `NEXT-006` (permissions) cannot start a stable design until interface application is decided.

`0.0.4` shipped the architectural seam this slice needs: `DjangoTypeDefinition.interfaces`, the three-phase `finalize_django_types()` finalizer, and the consumer-override contract for relation fields. `0.0.5` should populate and apply that seam.

The target is not a full connection/query-field release. The target is to make model-backed Relay node types possible in the package's `class Meta` style, while preserving the existing manual-list-query surface and optimizer behavior.

## Upstream Inspiration & Behavior
Our subpackage layout and design philosophy draw heavily from the reference trees mapped in `docs/TREE.md`:

- **`django_graphene_filters` / `graphene_django`**: These frameworks use `class Meta: interfaces = (relay.Node, )`. The primary key is automatically mapped to a Base64 encoded Global ID. A class method (`get_node(info, id)`) handles instance retrieval using the Django ORM. This sets the gold standard for ergonomics.
- **`strawberry_django`**: Integrates closely with `strawberry.relay.Node` (often through its `relay/` subpackage). However, instead of a `Meta.interfaces` tuple, it relies heavily on decorator arguments and subclassing `strawberry.relay.Node` directly, often overriding `resolve_node(node_id, info, required)` using the underlying Django ORM.

We want to achieve the Graphene-level ergonomics (`Meta.interfaces`) using the native `strawberry.relay.Node` machinery under the hood, hooking cleanly into our existing `DjangoType` finalizer.

## Target API (0.0.5)

Consumers should be able to declare `relay.Node` compliance directly in `Meta`:

```python
import strawberry
from strawberry import relay
from django_strawberry_framework import DjangoType
from .models import ObjectType

class ObjectTypeNode(DjangoType):
    class Meta:
        model = ObjectType
        fields = "__all__"
        interfaces = (relay.Node,)
        
    # Optional consumer override for visibility
    @classmethod
    def get_queryset(cls, queryset, info, **kwargs):
        user = getattr(info.context, "user", None)
        if user and user.is_staff:
            return queryset
        return queryset.filter(is_private=False)
```

## Implementation Strategy

### 1. `Meta.interfaces` Promotion
- Move `interfaces` out of `DEFERRED_META_KEYS` and into `ALLOWED_META_KEYS`.
- In `_validate_meta` / `_build_annotations`, capture the provided tuple of interfaces and store them on the existing slot in `DjangoTypeDefinition.interfaces`.

### 2. Auto-Mapping the Primary Key to `NodeID`
- When `relay.Node` (or any `Node` subclass) is present in `Meta.interfaces`, the model's primary key (`AutoField`, `BigAutoField`, `UUIDField`, etc.) must be mapped to Strawberry's Relay ID type instead of the raw scalar.
- Modify `django_strawberry_framework/types/converters.py:convert_scalar` so that if the field is the model's primary key (`field.primary_key == True`) and the `DjangoType` is a Node, it wraps the base scalar in `strawberry.relay.NodeID[py_type]`.

### 3. Finalizer Phase 3 Injection
- During `finalize_django_types()`, before `strawberry.type(...)` is called, we must ensure the `DjangoType` subclass actually inherits from the declared interfaces.
- Dynamically inject the interfaces into the class `__bases__`.
- Modifying `cls.__bases__ = cls.__bases__ + definition.interfaces` works natively with `strawberry.type`.

### 4. Default `resolve_node` Behavior
- Strawberry's `relay.Node` requires a `resolve_node(cls, info, node_id, required)` method to retrieve the instance by ID.
- `DjangoType` should conditionally synthesize a default `resolve_node` classmethod if `relay.Node` is in `interfaces` and the consumer hasn't authored their own.
- **Queryset Cooperation**: The default `resolve_node` must route through `cls.get_queryset(model._default_manager.all(), info)` to ensure that row-level visibility filters applied by the consumer are respected during node fetches.

## Edge Cases & Constraints
- **Composite Primary Keys:** Django 5.2+ introduces composite primary keys. For 0.0.5, we should explicitly document that `GlobalID` mapping for composite keys is unsupported and raise a `ConfigurationError` if `relay.Node` is combined with a composite PK model.

## Definition of Done (Testing)
1. **Validation**: Test that `Meta.interfaces` accepts a tuple of interfaces.
2. **Schema Output**: A `DjangoType` with `interfaces = (relay.Node,)` generates a valid GraphQL type that implements the `Node` interface.
3. **PK Mapping**: The primary key is generated as `GlobalID` (via `NodeID[...]`).
4. **Resolution**: `resolve_node` correctly fetches instances using the underlying model and respects `get_queryset` filters (i.e. returning `None` or failing if the node is filtered out).
5. **Consumer Override**: A consumer who manually declares `@classmethod def resolve_node(...)` is not clobbered by the synthesized default.
6. **Documentation**: Update `FEATURES.md` and KANBAN `READY-004` to reflect completion.
