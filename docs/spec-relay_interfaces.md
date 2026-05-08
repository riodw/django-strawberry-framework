# Spec: Relay Interfaces and Node Foundation

Target release: `0.0.5`

Status: primary target spec

## Purpose

`0.0.4` split `DjangoType` collection from Strawberry finalization and added `DjangoTypeDefinition.interfaces` as a reserved slot. `0.0.5` should use that seam to ship the first Relay-compatible foundation: `Meta.interfaces` on `DjangoType`, with model-backed defaults for Strawberry's `relay.Node`.

The target is not a full connection/query-field release. The target is to make model-backed Relay node types possible in the package's `class Meta` style, while preserving the existing manual-list-query surface and optimizer behavior.

## Problem

The north-star schema in `GOAL.md` depends on this shape:

```python
from strawberry import relay

from django_strawberry_framework import DjangoType


class ObjectTypeNode(DjangoType):
    class Meta:
        model = models.ObjectType
        fields = "__all__"
        interfaces = (relay.Node,)
```

Today `Meta.interfaces` is deliberately rejected as a deferred key. That was correct for `0.0.4` because accepting it without applying it would silently produce GraphQL types that look interface-bearing in Python but do not implement the requested Strawberry interface.

For `0.0.5`, the package should promote `Meta.interfaces` only if it can apply the interface before `strawberry.type(...)` and install the minimal Django-backed Relay defaults needed for `relay.Node` types.

## Goals

- Accept `Meta.interfaces` on concrete `DjangoType` subclasses.
- Apply interface bases during `finalize_django_types()` before Strawberry decoration.
- Support `interfaces = (relay.Node,)` as the primary 0.0.5 path.
- Preserve non-Relay `DjangoType` behavior exactly.
- Provide Django-backed defaults for Relay node identity and lookup:
  - `resolve_id_attr`
  - `resolve_id`
  - `resolve_node`
  - `resolve_nodes`
- Ensure node lookup runs through `DjangoType.get_queryset(...)` so visibility filters are not bypassed.
- Keep the API Meta-class-driven and compatible with future `DjangoConnectionField`, `DjangoNodeField`, permissions, and cascade visibility.
- Keep failures loud when an interface configuration cannot be applied.

## Non-goals

- No `DjangoConnectionField`.
- No `DjangoNodeField`.
- No Relay pagination or connection optimization.
- No cascade permissions.
- No field-level permissions.
- No sentinel/redaction behavior.
- No `Meta.primary`.
- No filter/order/aggregate/fieldset promotion.
- No package-wide setting such as `MAP_AUTO_ID_AS_GLOBAL_ID` unless the implementation proves it is necessary for the minimal Relay node path.
- No broad custom Strawberry field class. That remains a later fieldset/permission/optimizer architecture decision.

## Reference-library influence

### django-graphene-filters / Graphene-Django

Borrow the user-facing target, not the internals.

What to borrow:

- The schema author experience: `Meta.interfaces = (Node,)`.
- The expectation that model-backed node types become the foundation for node fields, connection fields, and permission-aware relation traversal.
- The cookbook-shaped end state where sidecar filters, orders, aggregates, fieldsets, search, and permissions all hang from the same model-backed type.

What not to borrow:

- Graphene metaclass internals.
- Graphene `_meta` mutation patterns.
- Graphene `Dynamic` conversion.
- Graphene connection machinery.
- Sentinel/cascade permission behavior in this slice.

Graphene tells this project what experience to recreate. It does not define the Strawberry implementation.

### strawberry-graphql-django

Borrow the Strawberry-native mechanics selectively.

The key pattern is in `strawberry_django/type.py`: when a processed type is a subclass of `strawberry.relay.Node`, Strawberry-Django installs default model-backed implementations for `resolve_id`, `resolve_id_attr`, `resolve_node`, and `resolve_nodes` unless the user already supplied them.

What to borrow:

- Relay behavior should be class-based: the final Strawberry type should actually be a subclass of `relay.Node`.
- If no explicit `NodeID` annotation exists, model-backed node types can fall back to the Django model primary key.
- Node lookup should start from the model manager, apply the type's queryset hook, then filter by the resolved ID attribute.
- Node resolver hooks should be installed only when the type implements `relay.Node`.
- User-authored Relay resolver methods should win over generated defaults.

What not to borrow:

- Decorator-first API shape.
- Full `StrawberryDjangoField`.
- Full optimizer store.
- Filter/order/pagination field stack.
- Broad settings surface.

Strawberry-Django informs the Relay mechanics; this package keeps its own collection/finalization lifecycle.

## Current architecture seam

`DjangoType.__init_subclass__` currently:

- validates `Meta`
- selects Django fields
- builds scalar/relation annotations
- creates a `DjangoTypeDefinition`
- registers the model/type pair
- defers relation finalization

`finalize_django_types()` currently:

- resolves pending relations
- attaches generated relation resolvers
- calls `strawberry.type(cls, name=..., description=...)`
- marks definitions and registry finalized

`DjangoTypeDefinition` already has:

```python
interfaces: tuple[type, ...] = ()
```

`0.0.5` should fill and consume that slot.

## Specific references and justifications

These references are the implementation anchors for the slice.

### Product and roadmap references

- `GOAL.md:19` establishes the project rule that the API should be Meta-class-driven, not decorator-first. This justifies keeping `interfaces` in `class Meta` instead of asking users to decorate or manually inherit for the common path.
- `GOAL.md:41` names Relay node support as part of the feature-complete target. This justifies treating Relay as foundation work, not optional polish.
- `GOAL.md:62` shows the north-star type declaration using `interfaces = (relay.Node,)`. This is the exact public shape this spec promotes.
- `GOAL.md:79` and `GOAL.md:80` show future `DjangoNodeField` and `DjangoConnectionField` usage. This justifies shipping Node/interface support before connection fields.
- `TODAY.md:18` and `TODAY.md:24` list `Meta.interfaces` and Relay node/connection integration as blockers for the rich fakeshop schema. This justifies making `0.0.5` a blocker-removal release.

### Current package references

- `django_strawberry_framework/types/base.py:41` starts `DEFERRED_META_KEYS`, and `django_strawberry_framework/types/base.py:50` explicitly says `interfaces` is deferred because base injection before `strawberry.type` has not landed. This is the direct code comment that `0.0.5` resolves.
- `django_strawberry_framework/types/base.py:58` starts `ALLOWED_META_KEYS`. This is where `interfaces` moves once validation and application are implemented.
- `django_strawberry_framework/types/base.py:77` starts `DjangoType.__init_subclass__`, the collection phase that reads `Meta`, builds annotations, creates `DjangoTypeDefinition`, and registers the type. This is where normalized `Meta.interfaces` must be captured.
- `django_strawberry_framework/types/base.py:116` constructs `DjangoTypeDefinition`. This call should pass the normalized interfaces tuple.
- `django_strawberry_framework/types/base.py:243`, `django_strawberry_framework/types/base.py:265`, and `django_strawberry_framework/types/base.py:271` define the current fail-loud Meta validation path. Interface validation should follow this style instead of deferring errors to Strawberry whenever the package can produce a clearer `ConfigurationError`.
- `django_strawberry_framework/types/base.py:382` starts `_build_annotations`, where selected Django scalar fields become Strawberry annotations. Relay primary-key suppression belongs around this collection path because generic `convert_scalar(...)` should keep non-Relay `id: int` behavior.
- `django_strawberry_framework/types/definition.py:36` already has `interfaces: tuple[type, ...] = ()`. This justifies not adding a separate metadata channel.
- `django_strawberry_framework/types/finalizer.py:31` starts `finalize_django_types()`, and `django_strawberry_framework/types/finalizer.py:80` calls `strawberry.type(...)`. The interface application phase must happen before line 80's decoration call.
- `django_strawberry_framework/types/converters.py:49` and `django_strawberry_framework/types/converters.py:79` define generic scalar conversion. This justifies keeping Relay ID behavior out of `SCALAR_MAP` and local to types that request `relay.Node`.
- `django_strawberry_framework/optimizer/walker.py:91` starts selection walking, `django_strawberry_framework/optimizer/walker.py:117` appends scalar selections to `only_fields`, and `django_strawberry_framework/optimizer/walker.py:183` starts relation select planning. These are the optimizer seams that must keep the concrete primary-key attname available when GraphQL selects Relay `id`.

### strawberry-graphql-django references

- `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/type.py:104` through `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/type.py:108` remove `id` from generated model fields when `MAP_AUTO_ID_AS_GLOBAL_ID` is active. This justifies the 0.0.5 rule that a Relay node type should not also synthesize a normal raw integer GraphQL `id`.
- `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/type.py:214` through `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/type.py:241` install model-backed Relay defaults only when the type is a `relay.Node`, and preserve user-defined methods. This is the closest implementation reference for `install_relay_node_resolvers(...)`.
- `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/type.py:246` decorates with `strawberry.type(...)` after the Relay defaults are installed. This supports this spec's order: apply interfaces, install Relay methods, then decorate.
- `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/relay/utils.py:102` starts `resolve_model_nodes`, `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/relay/utils.py:143` starts from the model default manager, `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/relay/utils.py:144` applies the type queryset hook, and `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/relay/utils.py:146` resolves the ID attribute. This justifies the same default lookup sequence for this package.
- `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/relay/utils.py:202` through `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/relay/utils.py:280` implement single-node lookup with `GlobalID` unwrapping, queryset filtering, optional optimizer integration, and `required` behavior. This is the reference for the eventual `resolve_model_node(...)` shape.
- `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/relay/utils.py:285` through `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/relay/utils.py:301` fall back to `pk` when Strawberry cannot find an explicit `NodeID` annotation. This justifies using the Django primary key as the default node identity.
- `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/relay/utils.py:306` through `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/relay/utils.py:339` resolve IDs from the concrete primary-key attname and prefer `root.__dict__` before normal Django attribute access. This justifies the no-extra-query invariant for `resolve_id`.

### django-graphene-filters references

- `/Users/riordenweber/projects/django-graphene-filters/examples/cookbook/cookbook/recipes/schema.py:20`, `/Users/riordenweber/projects/django-graphene-filters/examples/cookbook/cookbook/recipes/schema.py:45`, `/Users/riordenweber/projects/django-graphene-filters/examples/cookbook/cookbook/recipes/schema.py:72`, and `/Users/riordenweber/projects/django-graphene-filters/examples/cookbook/cookbook/recipes/schema.py:99` show every cookbook node using `interfaces = (Node,)`. This justifies making Relay interface support part of the package's cookbook-parity path.
- `/Users/riordenweber/projects/django-graphene-filters/examples/cookbook/cookbook/recipes/schema.py:132` and `/Users/riordenweber/projects/django-graphene-filters/examples/cookbook/cookbook/recipes/schema.py:134` show node fields and connection fields depending on those node types. This supports sequencing Relay before `DjangoNodeField` and `DjangoConnectionField`.
- `/Users/riordenweber/projects/django-graphene-filters/django_graphene_filters/object_type.py:183` through `/Users/riordenweber/projects/django-graphene-filters/django_graphene_filters/object_type.py:194` warn that sentinel/cascade permission behavior depends on Relay's node lookup path. This justifies treating cascade permissions as a later feature that should build on the 0.0.5 Node foundation, not ship inside it.

## Pre-implementation spike outcome

A minimal local spike against the installed Strawberry version showed that mutating bases before `strawberry.type(...)` can work:

```python
class Item(Base):
    name: str


Item.__bases__ = (Base, relay.Node)
strawberry.type(Item)
```

The resulting type is a subclass of `relay.Node`, and Strawberry records the `Node` interface on the object definition.

This supports the existing design comment in `types/base.py`: the missing interface pass can be a pre-decoration base application step. The implementation still needs package tests because real `DjangoType` classes also carry synthesized annotations, pending relations, generated resolvers, and optimizer metadata.

## Public API

### Basic Relay node type

```python
from strawberry import relay

from django_strawberry_framework import DjangoType


class BookType(DjangoType):
    class Meta:
        model = Book
        fields = ("id", "title")
        interfaces = (relay.Node,)
```

Expected GraphQL behavior:

- `BookType` implements the Relay `Node` interface.
- GraphQL exposes `id` as a Relay global ID.
- The model primary key remains the backing node ID by default.
- `title` remains a normal generated field.

### Custom Relay resolver override

Consumers may override Relay methods explicitly:

```python
class BookType(DjangoType):
    class Meta:
        model = Book
        fields = ("id", "title")
        interfaces = (relay.Node,)

    @classmethod
    def resolve_id_attr(cls) -> str:
        return "slug"
```

Generated defaults must not clobber user-authored Relay methods.

### Non-Relay interface classes

`Meta.interfaces` may contain non-Relay Strawberry interface classes if they can be applied as Python bases before decoration. `0.0.5` does not generate fields or resolvers for non-Relay interfaces; it only applies them and lets Strawberry validate compatibility.

If this proves too broad during implementation, 0.0.5 may narrow to `relay.Node` only, but the preferred target is to apply interface bases generically and special-case only Relay defaults.

## Meta validation

`interfaces` moves from `DEFERRED_META_KEYS` to `ALLOWED_META_KEYS`.

Validation rules:

- `Meta.interfaces` is optional.
- When present, it must be a sequence of classes.
- Strings are rejected.
- Non-class values are rejected.
- Duplicate interfaces are rejected or normalized deterministically.
- `DjangoType` itself is rejected as an interface.
- Interface application failures are raised as `ConfigurationError` with the source type name and interface names.

Open question:

- Whether to require every non-Relay interface to already be a Strawberry interface. The implementation can start permissive and rely on Strawberry's error, but the better consumer error may be to validate with Strawberry object-definition metadata where practical.

## ID field behavior

Relay node types need special handling for the Django primary key field.

Current behavior:

- `id` selected in `Meta.fields` becomes a normal scalar annotation, usually `int`.

Relay behavior:

- `relay.Node` exposes GraphQL `id` as a `GlobalID`.
- Strawberry's `Node` implementation normally expects a `NodeID` annotation or a resolver fallback.

0.0.5 rule:

- If `relay.Node` is in `Meta.interfaces`, the model primary-key field should not be synthesized as a normal scalar GraphQL `id` field.
- The primary key remains selected internally for optimizer/projection purposes.
- Relay `id` is resolved by generated `resolve_id` / `resolve_id_attr` defaults.
- If the consumer explicitly annotates or assigns an `id` field on a Relay node type, the package should fail loudly unless a safe override contract is deliberately added in the spec before implementation.

Rationale:

- Exposing both model `id: int` and Relay `id: GlobalID` under the same GraphQL name is ambiguous.
- Strawberry-Django avoids this class of bug by removing `id` from generated model fields when auto ID mapping is enabled.
- This package should make Relay ID behavior explicit and local to `relay.Node` participation.

## Generated Relay defaults

Add a small helper module, likely `django_strawberry_framework/types/relay.py`.

Responsibilities:

- detect Relay participation
- apply interface bases
- install model-backed Relay defaults
- resolve IDs
- resolve nodes

Proposed helpers:

```python
def apply_interfaces(type_cls: type, definition: DjangoTypeDefinition) -> None:
    ...


def implements_relay_node(type_cls: type, definition: DjangoTypeDefinition) -> bool:
    ...


def install_relay_node_resolvers(type_cls: type, definition: DjangoTypeDefinition) -> None:
    ...


def resolve_model_id_attr(cls: type) -> str:
    ...


def resolve_model_id(cls: type, root: models.Model, *, info: Any | None = None) -> str:
    ...


def resolve_model_node(
    cls: type,
    node_id: str | relay.GlobalID,
    *,
    info: Any | None = None,
    required: bool = False,
) -> models.Model | None:
    ...


def resolve_model_nodes(
    cls: type,
    *,
    info: Any | None = None,
    node_ids: Iterable[str | relay.GlobalID] | None = None,
    required: bool = False,
) -> Iterable[models.Model | None] | models.QuerySet:
    ...
```

The exact signatures should match Strawberry's `relay.Node` expectations.

Default behavior:

- `resolve_model_id_attr` returns Strawberry's explicit NodeID attr when one exists; otherwise it falls back to the Django primary key attname.
- For standard Django models, `pk` resolves through the concrete primary key attname, such as `id`.
- `resolve_model_id` should prefer `root.__dict__[attname]` when available to avoid unnecessary database access after `only()` projection.
- If the attr is missing from `__dict__`, fall back to normal Django attribute access.
- `resolve_model_node` and `resolve_model_nodes` should build from `definition.model._default_manager.all()`.
- If `info` is provided, apply `type_cls.get_queryset(queryset, info)` before filtering by ID.
- If `required=True`, missing IDs should raise according to Strawberry's expected behavior.
- If `required=False`, missing IDs should resolve to `None`.

User-authored methods:

- If the consumer defines `resolve_id`, `resolve_id_attr`, `resolve_node`, or `resolve_nodes`, do not replace it.
- If a method is inherited from `relay.Node` itself, replace it with the package default.
- If a method is inherited from another user base/interface, do not replace it unless it is exactly the unimplemented/default Relay method.

## Finalization flow

Add an interface phase before Strawberry decoration:

1. Resolve pending relations.
2. Rewrite pending relation annotations.
3. Attach generated relation resolvers.
4. Apply `Meta.interfaces` as class bases.
5. Install Relay node defaults when the finalized class implements `relay.Node`.
6. Call `strawberry.type(...)`.
7. Mark definitions finalized.

The interface phase must run after pending relation annotations are resolved but before `strawberry.type(...)`.

Failure behavior:

- If interface application fails, raise `ConfigurationError`.
- Phase 1 unresolved-target detection remains failure-atomic.
- Interface application mutates class bases, so failures after this phase follow the same rule as Strawberry decoration failures: tests must use `registry.clear()` and fresh classes.

## Optimizer and projection invariants

Relay node support must not regress optimizer behavior.

Required invariants:

- Selecting Relay `id` must preserve enough model primary-key data for `resolve_id`.
- `only()` projection must include the concrete primary-key attname when Relay `id` is selected.
- Existing connector-column preservation still works for relation traversal.
- FK-id elision remains scoped to relation selections and does not confuse Relay `GlobalID` with raw model FK IDs.
- Generated Relay resolvers should not trigger avoidable lazy loads when the primary key is already present on the model instance.

Potential implementation detail:

- Keep the primary key in `DjangoTypeDefinition.field_map` even if the normal scalar `id` annotation is suppressed for Relay node types.
- Ensure the optimizer walker treats the Relay `id` field as needing the model primary key column.

## Registry implications

No `Meta.primary` work ships in this slice.

Consequences:

- Node lookup remains one type per model, matching current registry behavior.
- Multiple `DjangoType`s per model still raise `ConfigurationError`.
- Future `Meta.primary` will decide which type owns relation conversion and node lookup when multiple types per model are allowed.

## Tests

Add or extend tests under `tests/types/`.

Suggested file:

- `tests/types/test_relay_interfaces.py`

Core tests:

- `Meta.interfaces` is accepted and stored on `DjangoTypeDefinition`.
- Non-sequence `Meta.interfaces` raises `ConfigurationError`.
- String entries raise `ConfigurationError`.
- Non-class entries raise `ConfigurationError`.
- A `DjangoType` with `interfaces = (relay.Node,)` finalizes and implements Strawberry's `Node` interface.
- Relay node type exposes GraphQL `id` as a global ID, not a raw integer model field.
- Relay node type can still expose normal scalar fields.
- `resolve_id_attr` falls back to the concrete Django primary-key attname.
- `resolve_id` returns the model primary key without an extra query when the value is already loaded.
- `resolve_node` applies `get_queryset`.
- `resolve_nodes` preserves input order and returns `None` for missing IDs when not required.
- Required node lookup raises for missing IDs.
- Consumer-authored `resolve_id_attr` is preserved.
- Consumer-authored `resolve_node` / `resolve_nodes` are preserved.
- Non-Relay types keep current `id: int` behavior.
- `registry.clear()` resets any Relay/interface state enough for fresh test classes.

Optimizer tests:

- A Relay node type selected through a root `QuerySet` can select `id` and another scalar with no lazy-load warning.
- `only()` projection includes the primary-key attname when Relay `id` is selected.
- Relation traversal to a Relay node target still plans `select_related` / `prefetch_related` correctly.

Example tests:

- Prefer package tests for the core slice.
- Add one fakeshop `library` HTTP test only if it catches behavior not visible in package tests, such as serialized `GlobalID` output through the real `/graphql/` endpoint.

## Documentation updates

When the slice ships:

- `docs/FEATURES.md`
  - mark `Meta.interfaces` as shipped alpha
  - document Relay Node support and current constraints
  - keep `DjangoConnectionField`, `DjangoNodeField`, and connection pagination as planned
- `docs/README.md`
  - mention Relay only in status or an optional short example, not the primary quickstart
- `TODAY.md`
  - remove Relay node support from the blocked list if the fakeshop example can use it
  - keep connection fields, filters, orders, aggregates, fieldsets, search, and permissions blocked
- `KANBAN.md`
  - move `READY-004` to Done
  - add any follow-up cards discovered during implementation
- `CHANGELOG.md`
  - add a concise `0.0.5` entry only when preparing the release

## Open questions

### Can interface bases always be mutated safely?

The local spike says yes for a minimal case. Real `DjangoType` classes need tests covering:

- inherited custom `get_queryset`
- consumer relation overrides
- pending relation annotations
- generated relation resolvers
- optimizer metadata

If base mutation is not safe, alternatives are:

- create a replacement class with the desired bases and update the registry to point at it
- require explicit inheritance from `relay.Node` for `0.0.5` and reserve `Meta.interfaces` for a later slice

The preferred target remains Meta-driven base application.

### Should non-Relay interfaces ship in 0.0.5?

Preferred answer: yes, but only as base application with Strawberry validation. Relay receives package-installed Django defaults; non-Relay interfaces do not.

Fallback answer: if generic interfaces complicate the slice, ship `relay.Node` only and keep non-Relay interfaces rejected with a narrower error.

### Should Relay ID mapping be configurable?

Preferred answer for 0.0.5: no.

Relay ID mapping is activated by `relay.Node` participation. Non-Relay types keep raw model `id` conversion.

A future setting can be added only if real use shows a need to decouple Node participation from ID field mapping.

### Should `resolve_node` use the optimizer?

Preferred answer for 0.0.5: apply `get_queryset`; leave deeper optimizer integration as a follow-up unless it is straightforward and well-tested.

Reason: root `QuerySet` optimization is already shipped. Node-field optimization will become more important when `DjangoNodeField` ships.

## Implementation phases

### Phase 1 — Meta collection

- Move `interfaces` out of `DEFERRED_META_KEYS`.
- Add validation helper for `Meta.interfaces`.
- Store normalized interfaces on `DjangoTypeDefinition`.
- Suppress normal scalar primary-key annotation when `relay.Node` is requested.
- Preserve the primary-key field in metadata for optimizer/projection use.

Primary references: `django_strawberry_framework/types/base.py:41`, `django_strawberry_framework/types/base.py:58`, `django_strawberry_framework/types/base.py:77`, `django_strawberry_framework/types/base.py:116`, `django_strawberry_framework/types/base.py:243`, `django_strawberry_framework/types/base.py:382`, `django_strawberry_framework/types/definition.py:36`.

### Phase 2 — Interface application

- Add `types/relay.py`.
- Apply interface bases before Strawberry decoration.
- Wrap base-application errors in `ConfigurationError`.
- Add registry lifecycle tests.

Primary references: `django_strawberry_framework/types/finalizer.py:31`, `django_strawberry_framework/types/finalizer.py:80`, `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/type.py:246`.

### Phase 3 — Relay defaults

- Detect finalized classes that implement `relay.Node`.
- Install generated Relay methods only where the consumer did not define one.
- Implement model ID attr, model ID, single-node lookup, and multi-node lookup.
- Ensure `get_queryset` is applied during lookup.

Primary references: `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/type.py:214`, `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/type.py:216`, `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/relay/utils.py:102`, `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/relay/utils.py:202`, `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/relay/utils.py:285`, `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/relay/utils.py:306`.

### Phase 4 — Optimizer and schema tests

- Add schema construction tests.
- Add GraphQL execution tests for global IDs.
- Add optimizer/projection tests for Relay `id`.
- Add relation traversal tests involving Relay node types.

Primary references: `django_strawberry_framework/optimizer/walker.py:91`, `django_strawberry_framework/optimizer/walker.py:117`, `django_strawberry_framework/optimizer/walker.py:183`, `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/type.py:104`.

### Phase 5 — Docs and release readiness

- Update feature docs and board state.
- Add changelog entry during release prep.
- Run formatting, linting, and full tests.

Primary references: `GOAL.md:62`, `TODAY.md:18`, `TODAY.md:24`, `docs/FEATURES.md`.

## Success criteria

`0.0.5` is complete when:

- `Meta.interfaces = (relay.Node,)` works for `DjangoType`.
- The generated GraphQL type implements Strawberry's `Node` interface.
- Relay `id` resolves from the Django model primary key as a global ID.
- Node lookup applies `get_queryset`.
- User-authored Relay resolver methods are preserved.
- Non-Relay `DjangoType` behavior is unchanged.
- The optimizer keeps enough primary-key data for Relay ID resolution.
- Docs clearly say that Relay Node foundation is shipped, while connection fields and rich query features are still planned.
