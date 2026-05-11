# Spec: Relay Interfaces (0.0.5)

## Audience and purpose
This is the business-facing version of `docs/spec-relay_interfaces.md`. The primary spec remains the implementation source of truth; this document explains why the `0.0.5` Relay interfaces slice matters, what users will be able to do after it ships, and how the work fits into the larger product roadmap.

The short version: `0.0.5` makes model-backed GraphQL types compatible with Relay's standard `Node` interface while keeping this package's DRF-shaped `class Meta` API. That unlocks stable object identity, better client caching, future connection fields, and a cleaner path for teams migrating from Graphene or Strawberry-Django.

## Plain-language summary
GraphQL APIs need a consistent way to identify objects. A `Book`, `Category`, or `Loan` may appear in many different queries, but client applications still need to know when two results refer to the same database row. Relay's `Node` interface solves that by giving every object a globally unique `id`.

Today this package can expose Django models as Strawberry GraphQL types, but it cannot yet say: "this model-backed type participates in the standard Relay identity system." Users can write fields and relationships, but they cannot declare Relay compatibility through the package's preferred `class Meta` style.

The `0.0.5` release fixes that foundation. A user will be able to add `interfaces = (relay.Node,)` to a `DjangoType.Meta` class and get a Relay-compatible GraphQL type with a global ID and default lookup behavior.

## Why this matters
This slice is important even though it is not a full connection-field release.

- **It gives API objects stable identity.** Frontend clients can reliably recognize the same object across different queries because Relay `Node` exposes a standard global ID.
- **It moves the package toward ecosystem parity.** Graphene-Django users already expect `class Meta: interfaces = (Node,)`. Supporting the same shape makes migration more familiar without adopting Graphene's internals.
- **It protects the package's main differentiator.** The public API remains DRF-shaped and Meta-class-driven. Users do not need to switch to Strawberry-Django's decorator-first model just to get Relay basics.
- **It unblocks future roadmap items.** Connection fields, pagination, richer fakeshop examples, and permission-aware object lookup all need a stable answer for interfaces and object identity first.
- **It reduces custom code for consumers.** The framework can provide safe default `resolve_id`, `resolve_node`, and related Relay methods instead of making every project write the same ORM lookup logic.
- **It keeps visibility rules centralized.** Node lookups route through `DjangoType.get_queryset`, so business rules such as privacy, tenant scoping, or staff-only access are applied consistently.

## Problem statement
`DjangoType` users cannot declare GraphQL interfaces, including Relay `Node`, through `class Meta`. Today `Meta.interfaces` is rejected with `ConfigurationError` because the package does not apply it end-to-end. The result is that:

- `GOAL.md`'s target API (`interfaces = (relay.Node,)`) is unreachable today.
- `TODAY.md` lists Relay node and connection support as a blocker for the richer fakeshop schema.
- `docs/FEATURES.md` lists `Meta.interfaces` and Relay GlobalID mapping as deferred.
- `KANBAN.md` cannot move the Relay foundation work to Done.
- Later connection and permission designs cannot be finalized until interface application is decided.

`0.0.4` shipped the architectural seam this slice needs: `DjangoTypeDefinition.interfaces`, the three-phase `finalize_django_types()` finalizer, and the consumer override contract for relation fields. `0.0.5` fills and applies that seam.

The target is not a full query, connection, pagination, or permissions release. The target is to make model-backed Relay node types possible in the package's `class Meta` style while preserving the existing list-query and optimizer behavior.

## What ships in 0.0.5
`0.0.5` ships the Relay/interface foundation only.

- `Meta.interfaces` is accepted, validated, and stored on the existing type definition object.
- Any real Strawberry interface can be declared through `Meta.interfaces`.
- `interfaces = (relay.Node,)` makes a `DjangoType` implement Relay's standard `Node` interface.
- Relay-declared types expose `id` as `GlobalID!` instead of the raw Django integer ID.
- The framework installs safe defaults for Relay's `resolve_id_attr`, `resolve_id`, `resolve_node`, and `resolve_nodes` methods when the consumer has not written their own.
- Node lookup uses the Django model manager plus `cls.get_queryset(...)`, so existing visibility and scoping rules apply.
- The optimizer still sees the underlying primary-key column, so Relay `id` should not introduce avoidable lazy database loads.
- `is_type_of` is installed for `DjangoType` classes so Strawberry can map returned Django model instances to the correct GraphQL type.
- Composite primary keys are rejected for Relay Node types with a clear `ConfigurationError` until a future slice defines a safe encoding.

## What does not ship in 0.0.5
Keeping this release narrow is deliberate.

- No `DjangoConnectionField` yet.
- No full Relay pagination story yet.
- No automatic connection-field upgrade for reverse FK or many-to-many fields.
- No permission system or cascade-permission integration yet.
- No multiple-`DjangoType`-per-model support or `Meta.primary` yet.
- No new top-level public exports.
- No broad replacement of Strawberry internals or dependency on Strawberry-Django.

This release creates the foundation those features can build on.

## Upstream inspiration and behavior
Our design borrows proven behavior from existing Django GraphQL libraries while preserving this package's API shape.

- **Graphene-Django and django-graphene-filters** prove the ergonomics. Their users can write `class Meta: interfaces = (Node,)`, and that is the level of convenience we want here.
- **Strawberry-Django** proves the Relay resolver mechanics. It already handles default Relay node lookup, ID resolution, and consumer override detection against Strawberry's native `relay.Node` machinery.
- **django-strawberry-framework** keeps the DRF-shaped surface. We borrow patterns, not the decorator-first API and not a runtime dependency on Strawberry-Django.

In business terms: this gives users the familiar Graphene-style declaration shape, the Strawberry-native Relay behavior under the hood, and this package's own Meta-class-first product identity.

## Target API
Consumers should be able to declare Relay Node compatibility directly in `Meta`:

```python
from strawberry import relay
from django_strawberry_framework import DjangoType, finalize_django_types
from .models import Book


class BookType(DjangoType):
    class Meta:
        model = Book
        fields = ("id", "title")
        interfaces = (relay.Node,)

    @classmethod
    def get_queryset(cls, queryset, info, **kwargs):
        user = getattr(info.context, "user", None)
        if user and user.is_staff:
            return queryset
        return queryset.filter(is_private=False)


finalize_django_types()
```

`interfaces = (relay.Node,)` is the canonical spelling. For user ergonomics, the package also accepts `interfaces = relay.Node` and the common missing-comma spelling `interfaces = (relay.Node)` when the value is one real Strawberry interface class.

Expected behavior:

- `BookType` implements Relay `Node`.
- GraphQL exposes `id` as a Relay `GlobalID!`.
- The Django primary key remains the backing value by default.
- `title` and other normal fields keep working as before.
- Node lookup respects `BookType.get_queryset(...)`.
- A consumer can override Relay methods if they need custom lookup behavior.

## Implementation strategy
This section keeps enough technical detail for engineering review while staying aligned with the primary spec.

### 1. Validate and store `Meta.interfaces`
`interfaces` moves from a rejected deferred key to a supported Meta key only after the full behavior is implemented.

Validation should reject malformed inputs early with `ConfigurationError`:

- strings such as `"Node"`
- sets or generators
- non-interface classes
- `DjangoType` classes used as if they were interfaces
- duplicate entries

Valid tuple/list entries are normalized to a tuple and stored on `DjangoTypeDefinition.interfaces`. A single real Strawberry interface class is also accepted and normalized to a one-item tuple, so `interfaces = relay.Node` and `interfaces = (relay.Node)` both behave like `interfaces = (relay.Node,)`.

### 2. Apply interfaces before Strawberry finalization
`finalize_django_types()` already has the right lifecycle seam. The new Relay step runs after relation resolvers are attached and before `strawberry.type(...)` decorates the class.

At that point the framework injects the declared interfaces into the class bases. If Python rejects the base change, the framework converts the failure into a clear `ConfigurationError` naming the problematic interface.

### 3. Let Relay own the GraphQL `id`
The final spec does **not** wrap Django's scalar converter in `relay.NodeID[...]` for this slice. Instead, when a type declares `relay.Node`, the framework suppresses the synthesized Django `id` annotation so Strawberry's Relay `Node` interface supplies the GraphQL `id: GlobalID!` field.

The underlying Django primary-key field still remains in the internal field map. That matters because the optimizer and resolver defaults still need the real database column to avoid extra queries.

### 4. Install Relay resolver defaults
For Relay Node types, the framework installs default implementations for:

- `resolve_id_attr`
- `resolve_id`
- `resolve_node`
- `resolve_nodes`

These defaults are only installed when the consumer has not provided their own method. The override detection follows Strawberry-Django's proven `__func__` identity-check pattern so inherited Relay defaults can be replaced while user-authored overrides are preserved.

### 5. Respect existing visibility and optimizer behavior
The default node lookup starts from the model's default manager, applies `cls.get_queryset(queryset, info)`, and then fetches by ID. That means the same visibility rules used by list and relation queries apply to Relay node lookup.

The optimizer invariants are preserved: Relay `id` selection still keeps the concrete primary-key column available, and relation planning across Relay-declared types should behave the same as it did for non-Relay types.

## Business outcome
After `0.0.5`, the package can credibly say it supports the first piece of Relay: object identity through `Node`.

That does not mean every Relay feature is complete. It means the most important foundation is in place:

- backend teams can model Relay identity without leaving the `DjangoType.Meta` API
- frontend teams get globally stable IDs for cache normalization
- future pagination and connection work has a stable base
- the fakeshop example can start moving from placeholder GraphQL toward realistic model-backed API examples
- migration conversations from Graphene-Django become easier because the familiar `Meta.interfaces` shape exists

## Edge cases and constraints
- **Composite primary keys:** Unsupported for Relay Node in `0.0.5`; finalization raises `ConfigurationError` with a clear message.
- **Non-Relay interfaces:** Supported when they are real Strawberry interfaces, but they do not receive Relay-specific resolver defaults.
- **Consumer overrides:** Explicit consumer `resolve_*` methods win over framework defaults.
- **Empty interfaces:** `interfaces = ()` behaves the same as omitting the key.
- **Existing non-Relay types:** Behavior stays unchanged.
- **Test isolation:** `registry.clear()` plus fresh class definitions remains the supported test reset path.

## Definition of done
The business-facing definition of done is:

1. A `DjangoType` can declare `Meta.interfaces = (relay.Node,)` without leaving the Meta-class API, and the single-interface forms `interfaces = relay.Node` / `interfaces = (relay.Node)` normalize to the same stored tuple.
2. The generated GraphQL type implements Relay `Node` and exposes `id: GlobalID!`.
3. The raw Django `id` field no longer conflicts with Relay's `id` field on Node types.
4. Default Relay lookup methods fetch Django model instances and respect `get_queryset` filters.
5. Consumer-authored Relay resolver methods are not overwritten.
6. Non-Relay Strawberry interfaces can also be declared through `Meta.interfaces`.
7. Composite primary keys fail loudly with a clear configuration error.
8. Optimizer behavior does not regress for primary-key projection or relation traversal.
9. Tests cover validation, schema output, resolver behavior, overrides, optimizer invariants, registry reset behavior, and one live HTTP GlobalID round trip.
10. `docs/FEATURES.md`, `docs/README.md`, `TODAY.md`, `KANBAN.md`, and `CHANGELOG.md` describe the shipped state.
11. Version metadata is bumped to `0.0.5` and coverage remains at 100%.
12. No new top-level public exports are added.

## One-sentence release pitch
`0.0.5` gives django-strawberry-framework the Relay identity foundation: model-backed types can declare `interfaces = (relay.Node,)`, expose stable global IDs, and keep Django visibility rules intact through the existing `DjangoType.Meta` API.
