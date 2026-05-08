# Relay interfaces and `Meta.interfaces` foundation (0.0.5)

Status: draft, primary spec for the `0.0.5` slice.
Owner: package maintainer.
Predecessors: `docs/FEATURES.md`, `GOAL.md`, `KANBAN.md` card `READY-004`.
Influences: the local checkouts at `/Users/riordenweber/projects/strawberry-django-main/strawberry_django` and `/Users/riordenweber/projects/django-graphene-filters/django_graphene_filters` (referenced from `docs/TREE.md`).

## Problem statement
`DjangoType` users cannot declare GraphQL interfaces (Relay `Node` or otherwise) through `class Meta`. Today `Meta.interfaces` is rejected with `ConfigurationError` because the package does not apply it end-to-end. The result is that:
- `GOAL.md`'s target API (`interfaces = (relay.Node,)`) is unreachable today.
- `TODAY.md` lists Relay node and connection support as a hard blocker for the rich fakeshop schema.
- `docs/FEATURES.md` lists `Meta.interfaces` and `GlobalID` mapping in the deferred set.
- `KANBAN.md` `READY-004` and `BACKLOG-005` cannot land without a Relay foundation.
- `NEXT-005` (`DjangoConnectionField`) and `NEXT-006` (permissions) cannot start a stable design until interface application is decided.

`0.0.4` shipped the architectural seam this slice needs: `DjangoTypeDefinition.interfaces`, the three-phase `finalize_django_types()` finalizer, and the consumer-override contract for relation fields. `0.0.5` should populate and apply that seam.

## Current state
- `django_strawberry_framework/types/base.py:41-56` keeps `interfaces` in `DEFERRED_META_KEYS`. The block comment at `types/base.py:48-54` explicitly identifies the missing work: "the relay-interface application pass (`cls.__bases__` injection before `strawberry.type`) has not landed yet." This spec is the answer to that comment.
- `django_strawberry_framework/types/definition.py:36` already declares `interfaces: tuple[type, ...] = ()` on `DjangoTypeDefinition`. The `0.0.4` foundation slice reserved this slot specifically for this work.
- `django_strawberry_framework/types/finalizer.py:31-83` runs three loops with no interface awareness today: Phase 1 (`finalizer.py:42-66`) resolves pending relations; Phase 2 (`finalizer.py:68-75`) calls `_attach_relation_resolvers`; Phase 3 (`finalizer.py:77-82`) calls `strawberry.type(cls, name=..., description=...)` and marks the definition finalized.
- `django_strawberry_framework/types/converters.py:49-116` synthesizes `id` from `AutoField` / `BigAutoField` / `SmallAutoField` (`SCALAR_MAP` at `converters.py:49-76`, applied via `convert_scalar` at `converters.py:79-116`). Until this slice, every Django auto-id column produces a GraphQL `id: Int!`, which collides with Strawberry's `Node._id -> id: GlobalID!`.
- `DjangoType.get_queryset(cls, queryset, info, **kwargs)` (`types/base.py:140-154`) is the existing visibility hook. It is stable through `0.1.0` per `README.md:16` and `docs/README.md:98`, so the Relay node resolvers can call into it without compatibility risk.
- `DjangoOptimizerExtension` is consultable through `info.context` (`optimizer/extension.py`); the four Relay resolvers can opt into optimizer cooperation the same way root resolvers do today.
- The `0.0.4` lifecycle contract is pinned in `docs/FEATURES.md:93`: "Declaring a new concrete `DjangoType` after finalization raises `ConfigurationError`; tests should use `registry.clear()` and fresh type classes when they need a new registry lifecycle." The Relay slice must preserve this contract bit-for-bit.

## Goals
1. Accept `Meta.interfaces` end-to-end so a `DjangoType` can declare any Strawberry-compatible interface (Relay `Node` or otherwise).
2. Make `interfaces = (relay.Node,)` produce a working Relay-node-shaped GraphQL type with `id: GlobalID!`, `resolve_id`, `resolve_id_attr`, `resolve_node`, and `resolve_nodes` wired to Django's ORM and our existing `get_queryset` / optimizer surfaces.
3. Preserve the existing relation-finalization, optimizer, and override contracts shipped in `0.0.4`. Nothing about Phase 1/2/3 lifecycle changes for non-Relay types.
4. Stay tight: no `DjangoConnectionField`, no cascade permissions, no FK redaction sentinels, no node-aware filters, no node-aware optimizer changes in `0.0.5`.
5. Promote `Meta.interfaces` from `DEFERRED_META_KEYS` to `ALLOWED_META_KEYS` only when each behavior listed here is implemented and tested.

## Non-goals
- `DjangoConnectionField` and `DjangoNodeField` (planned for a later slice; this spec only lays the groundwork).
- `Prefetch`-aware Relay edge planning (tracked under `BACKLOG-012`).
- Cascade permissions, redacted-FK sentinels, or `is_redacted` (graphene-django's territory; revisit during the permissions slice).
- Connection-field-driven auto-upgrade of reverse FK / M2M fields (planned for `NEXT-005`).
- Stable `GlobalID`-typed filter inputs (planned for the filters slice).
- Multiple `DjangoType`s per Django model / `Meta.primary` (`READY-002`, separate slice).

## Borrowing posture
The two reference packages at the paths given in `docs/TREE.md` show two different ways to build this. The slice should borrow patterns (not implementations).

### From `strawberry-django` — borrow heavily
Local source path: `/Users/riordenweber/projects/strawberry-django-main/strawberry_django` (referenced from `docs/TREE.md:80-158`).

- **Resolver injection pattern** — `strawberry_django/type.py:213-236`. The `if issubclass(cls, relay.Node):` loop iterates `("resolve_id", "resolve_id_attr", "resolve_node", "resolve_nodes")` and replaces the attribute only if `existing_resolver is None or existing_resolver.__func__ is getattr(relay.Node, attr).__func__`. That exact `__func__` identity check is the consumer-override discriminator we should copy because comparing against `cls.__dict__` alone misses inherited Strawberry defaults from `relay.Node` itself. Justification: this slice does not invent a new override-detection scheme; it reuses one that has already been hardened against Strawberry version churn.
- **`resolve_id` shape** — `strawberry_django/relay/utils.py:306-339`. Read from `root.__dict__[id_attr]` first, fall back to `getattr(root, id_attr)`, coerce to `str`. The dict-cache check is what avoids an extra ORM hit when the row was already loaded into the Django identity map. Justification: matches our `_will_lazy_load` philosophy in `types/resolvers.py:67-90` and the rest of our optimizer cooperation story.
- **`resolve_id_attr` shape** — `strawberry_django/relay/utils.py:285-303`. Calls `super(source, source).resolve_id_attr()` and catches `NodeIDAnnotationError` to fall back to `"pk"`. This single try/except is what lets a consumer write `id: relay.NodeID[str]` (e.g. for a slug column) and have it work without our framework adding any new `Meta` key. Justification: zero extra surface, exact alignment with Strawberry's documented `NodeID` mechanism.
- **`resolve_node` / `resolve_nodes` queryset shape** — `strawberry_django/relay/utils.py:102-198` and `:223-282`. Use `_default_manager.all()`, pass through `run_type_get_queryset(qs, origin, info)`, filter on `id_attr` when ids are supplied, then consult the optimizer extension. Justification: every step has a direct counterpart already shipped (`cls.get_queryset(...)` for `run_type_get_queryset`, our `DjangoOptimizerExtension` for theirs). The borrow is structural, not implementation-level.
- **`MAP_AUTO_ID_AS_GLOBAL_ID` behavior** — `strawberry_django/type.py:104-109`. We borrow the *behavior* of stripping the Django `id` from generated annotations when `relay.Node` is in play, but tie it to the per-type `Meta.interfaces` declaration instead of a global setting. Justification: a global setting fights the existing "loud rejection of unshipped behavior" posture documented in `docs/FEATURES.md:53-54`; per-type opt-in keeps the contract local to the class declaration.
- **`is_type_of` virtual subclass** — `strawberry_django/type.py:204-211`. We commit to borrowing this. Justification: our root resolvers and relation resolvers (`types/resolvers.py:142-173`) return Django model instances, not Strawberry-typed wrappers. Strawberry's interface dispatch uses `is_type_of` to identify the concrete type at runtime; without it, an ORM instance returned through a Node-typed field can fail the isinstance check Strawberry uses for interfaces. Strawberry-django chose this exact borrow for the exact same reason; we have no architectural daylight from them on that point.

### From `django-graphene-filters` and `graphene-django` — borrow only the user-facing shape and the validation philosophy
Local source path: `/Users/riordenweber/projects/django-graphene-filters/django_graphene_filters` (referenced from `docs/TREE.md:160-186`).

- **`class Meta: interfaces = (Node,)` shape** — `django-graphene-filters/examples/cookbook/cookbook/recipes/schema.py:17-29`. Every node type in the cookbook recipes uses this exact `Meta` shape. Justification: `GOAL.md:62` and `GOAL.md:94` already commit us to this shape; the cookbook is what makes that shape concrete for graphene-django users we want to migrate.
- **"Warn loud when Relay-shaped behavior is configured without `Node`"** — `django_graphene_filters/object_type.py:186-198`. The warning fires when sentinel/cascade FK behavior is configured but `Node` is missing. Justification for *not* shipping the warning in `0.0.5`: there is no consumer code path in `0.0.5` that requires Relay (no connection field, no FK redaction). Adding the warning now would warn about behavior that does not yet exist. Defer to the connection or permissions slice.

### Explicitly do not borrow in `0.0.5`
- Graphene-django's `__init_subclass_with_meta__` plumbing or its `_meta` options bag.
- Graphene-django's redacted-sentinel system (`AdvancedDjangoObjectType._make_sentinel`) and cascade FK resolution.
- Graphene-django's connection-field auto-upgrade in `convert_django_field`.
- Strawberry-django's full `_process_type` post-pass that mutates `type_def.fields`. Our finalizer already handles relation finalization through `_attach_relation_resolvers`; we do not need a second field-rewriting pass for the Relay slice.
- Strawberry-django's `StrawberryDjangoField` custom field class. That is a much larger architectural commitment and is tracked separately in `BACKLOG-011`.
- Decorator-style `@strawberry_django.type(Model)`. We keep `class DjangoType` + `class Meta`.

## User-facing API
The shipped consumer surface in `0.0.5`:

```python
import strawberry
from strawberry import relay
from django_strawberry_framework import DjangoType, finalize_django_types
from myapp.models import Item


class ItemType(DjangoType):
    class Meta:
        model = Item
        fields = ("id", "name", "category")
        interfaces = (relay.Node,)


finalize_django_types()
```

Result:
- The schema exposes `ItemType` implementing the `Node` interface.
- `ItemType.id` is `GlobalID!`, supplied by the Relay `Node` interface — not the Django `AutoField`.
- `ItemType.resolve_id_attr()` returns `"pk"` by default.
- `ItemType.resolve_node(info, node_id)` returns the matching row, with `cls.get_queryset(...)` applied and the optimizer extension consulted if present.
- `ItemType.resolve_nodes(info, node_ids=...)` returns the matching rows, same hooks.
- A consumer can override any of `resolve_id_attr`, `resolve_id`, `resolve_node`, `resolve_nodes` in the class body, and the framework will not clobber them.

Non-Relay interfaces (plain `@strawberry.interface` classes) also work:

```python
@strawberry.interface
class Auditable:
    created_date: datetime
    updated_date: datetime


class ItemType(DjangoType):
    class Meta:
        model = Item
        fields = ("id", "name", "created_date", "updated_date")
        interfaces = (Auditable,)
```

Same shape, no Relay-specific wiring runs.

## Architectural decisions

### Decision 1: where interfaces are applied
Interfaces are applied in `finalize_django_types()` in a new step that runs after Phase 2 (`_attach_relation_resolvers`) and before Phase 3 (`strawberry.type(cls, ...)`). The deferred-key comment at `types/base.py:48-54` already names this seam. Reference: `finalizer.py:77-82`.

Mechanics: Strawberry treats interfaces through normal class inheritance (`strawberry.relay.Node` is decorated with `@interface(...)` upstream; `hasattr(cls, "__strawberry_definition__")` and `__strawberry_definition__.is_interface` is `True` for any declared interface). We mutate `cls.__bases__` to include each declared interface that is not already in the MRO. After mutation, `strawberry.type(cls, ...)` picks the interfaces up at decoration time without us touching Strawberry internals.

Justification:
- The only alternative — forcing consumers to write `class ItemType(DjangoType, relay.Node):` — contradicts the `class Meta`-driven posture in `GOAL.md:55-83` and the public-surface promise in `README.md:16`.
- `cls.__bases__` mutation is the same mechanism graphene-django uses internally; it is well-trodden Python with one real constraint (see Risks).
- Running this between Phase 2 and Phase 3 means relation-resolver attachment (`_attach_relation_resolvers` at `resolvers.py:176-196`) runs against the still-pre-decoration class, which is the point the existing Phase 2 already requires.

### Decision 2: id field handling
When `relay.Node` is among `Meta.interfaces` for a given `DjangoType`:
- `id` is removed from synthesized scalar annotations during `_build_annotations` so the Relay-supplied `id: GlobalID!` is not shadowed by a Django `int` field.
- The Django `id` column itself is still selected for ORM/optimizer purposes (it is the connector column the optimizer relies on); only the Strawberry annotation is suppressed.
- If the consumer includes `"id"` in `Meta.fields` while declaring `relay.Node`, the slice does not raise — the field is simply not generated on the GraphQL side. Document this clearly in `docs/FEATURES.md`.
- If `relay.Node` is not in `Meta.interfaces`, behavior is unchanged from `0.0.4`: `id: int!` is generated as before.

This mirrors strawberry-django's `MAP_AUTO_ID_AS_GLOBAL_ID` behavior but is opt-in per type rather than a global setting. A global setting can be added later if real-world adopters need it.

### Decision 3: Relay resolver injection
After interface injection and id suppression, but before `strawberry.type(cls, ...)`, the finalizer runs:

```python path=null start=null
if issubclass(cls, relay.Node):
    for attr, default_impl in (
        ("resolve_id_attr", _resolve_id_attr_default),
        ("resolve_id", _resolve_id_default),
        ("resolve_node", _resolve_node_default),
        ("resolve_nodes", _resolve_nodes_default),
    ):
        existing = getattr(cls, attr, None)
        node_default = getattr(relay.Node, attr, None)
        if existing is None or (
            getattr(existing, "__func__", None)
            is getattr(node_default, "__func__", None)
        ):
            setattr(cls, attr, classmethod(default_impl))
```

This is a direct copy of strawberry-django's check at `strawberry_django/type.py:222-225`. Justification for copying the `__func__` identity test rather than a `cls.__dict__[attr]` membership test: when the consumer does **not** override, `getattr(cls, attr)` resolves through the MRO to `relay.Node`'s default, which is exactly the case we want to overwrite. A `cls.__dict__` check would never see that and would skip injection forever.

The four default implementations live in a new module `django_strawberry_framework/types/relay.py`. The shapes are direct ports of strawberry-django's `relay/utils.py`:

- `_resolve_id_attr_default(cls)` — `try: return super(cls, cls).resolve_id_attr() except NodeIDAnnotationError: return "pk"`. Direct port of `strawberry_django/relay/utils.py:285-303`. Justification: the `super()` call delegates to Strawberry's own `Node.resolve_id_attr()` (see Strawberry's `relay/types.py` Node implementation), which scans the class for an `Annotated[..., relay.NodeID]` attribute. Falling back to `"pk"` when none is declared matches the most common Django case (auto pk). No new `DjangoTypeDefinition.id_attr` slot is needed; Strawberry already owns that detection.
- `_resolve_id_default(cls, root, info)` — `try: return str(root.__dict__[id_attr]) except KeyError: return django_getattr(root, id_attr)`. Port of `strawberry_django/relay/utils.py:306-339`. Justification: the `__dict__` cache hit is what avoids redundant ORM lookups when the row was loaded by the optimizer.
- `_resolve_node_default(cls, info, node_id, required=False)` — `qs = cls.__django_strawberry_definition__.model._default_manager.all(); qs = cls.get_queryset(qs, info); qs = qs.filter(**{id_attr: node_id}); ext = optimizer extension on info.context; if ext: qs = ext.optimize(qs, info=info); return qs.get() if required else qs.first()`. Port of `strawberry_django/relay/utils.py:223-282`, adapted to read the model from our `DjangoTypeDefinition` (`types/definition.py:19`) instead of strawberry-django's `StrawberryDjangoDefinition.model`.
- `_resolve_nodes_default(cls, info, node_ids=None, required=False)` — same queryset shape, optionally filtering on `node_ids` via `id_attr__in`. Port of `strawberry_django/relay/utils.py:102-198`.

We do not import strawberry-django at runtime; we copy the patterns and cite the source at the implementation site. Justification: adding a runtime dependency on strawberry-django would re-introduce decorator-first plumbing the package has explicitly avoided per `pyproject.toml:28-33` and the dependency-boundary note in `KANBAN.md:14`.

### Decision 4: validation
`_validate_meta` (in `types/base.py:243-295`) gains an interface validator that runs when `interfaces` is declared. Reference: the existing `_format_unknown_fields_error` helper at `types/base.py:232-240` is the canonical error-shape pattern; new errors here reuse the same `model.Meta.<key> ...` shape so consumer-visible failures stay consistent.

Validation rules:

- `interfaces` must be a tuple (or list, normalized to a tuple). An empty tuple is the same as not declaring the key at all (no-op).
- Each entry must satisfy `hasattr(entry, "__strawberry_definition__") and entry.__strawberry_definition__.is_interface`. `relay.Node` already satisfies this — it is decorated with `@interface(...)` upstream — so no special-casing is required. Justification: writing the check this way is robust against future Strawberry changes to `relay.Node` and forces every accepted entry to be a real Strawberry interface.
- Duplicates raise `ConfigurationError`. The `__bases__` injection step can no-op idempotently, but tolerating duplicates here would let typos hide.
- A class that already inherits from one of the listed interfaces directly (e.g. consumer wrote `class Foo(DjangoType, relay.Node): class Meta: interfaces = (relay.Node,)`) is accepted — the base-injection step is then a structural no-op (`relay.Node in cls.__bases__` is already true).

Composition with `Meta.optimizer_hints`: the two keys are independent. `optimizer_hints` continues to apply unchanged. Suppressing the synthesized `id` annotation when `relay.Node` is declared has no effect on the optimizer field map (`FieldMeta` is keyed off Django's field selection, not Strawberry's annotations) — `id` is still selected as the connector column.

### Decision 5: lifecycle and idempotency
- Calling `finalize_django_types()` twice is still a no-op via the existing short-circuit at `finalizer.py:39-40`.
- `registry.clear()` (`registry.py:172-185`) already drops `_definitions`, `_pending`, and `_finalized`. Test isolation continues to require **fresh class objects** after `clear()`, exactly as documented in `docs/FEATURES.md:93`. No new tracking state is added on `DjangoTypeDefinition` for the Relay slice — the source of truth is `cls.__bases__` itself for interface injection and the `relay.Node` MRO check for resolver injection. Justification: any new state would be redundant with `cls.__bases__` and would have to be re-validated for clear/redefine cycles, increasing the surface this slice has to test.
- New finalizer step ordering relative to the existing three-loop structure at `finalizer.py:42-83`:
  - Phase 1 unchanged (`finalizer.py:42-66`): resolve pending relations.
  - Phase 2 unchanged (`finalizer.py:68-75`): `_attach_relation_resolvers` for every non-finalized definition.
  - **NEW** Phase 2.5: for each non-finalized definition, if `definition.interfaces` is non-empty, inject those interfaces into `cls.__bases__` (only those not already present in `cls.__mro__`); if `relay.Node` is among the resolved bases, inject the four `resolve_*` defaults using the `__func__` identity test from Decision 3.
  - Phase 3 unchanged (`finalizer.py:77-82`): `strawberry.type(cls, name=definition.name, description=definition.description)`; mark `definition.finalized = True`.

The `id` suppression in Decision 2 happens earlier — during `__init_subclass__` collection (`types/base.py:110-115`, inside `_build_annotations`) — because that is where the synthesized annotation map is assembled. Justification for splitting suppression (collection-time) and base injection (finalization-time): collection is where `cls.__annotations__` is written; the synthesized annotation map is read by Strawberry at decoration time. Keeping suppression at the same site as annotation synthesis keeps the data flow local. Base injection has to wait for finalization because relation finalization in Phase 1 still needs to mutate `cls.__annotations__` and we do not want a partially-finalized class to also be a partially-interface-injected class.

### Decision 6: compatibility with the override contract
The `0.0.4` relation-field consumer-override contract (`DjangoTypeDefinition.consumer_annotated_relation_fields` and `consumer_assigned_relation_fields`, see `types/base.py:96-109` and `types/finalizer.py:46-66`) is preserved unchanged.

The new `Meta.interfaces` consumer-override contract is:

- Annotations and fields the interface itself declares (e.g. `Node._id`, which renders as the `id: GlobalID!` field) are owned by the interface. Consumers must not shadow them on the `DjangoType` subclass; doing so will produce a Strawberry-level error at decoration time, which the spec leaves to Strawberry rather than re-implementing.
- `resolve_id_attr` / `resolve_id` / `resolve_node` / `resolve_nodes` declared anywhere in the consumer's MRO above `relay.Node` take precedence over framework defaults via the `__func__` identity test. Justification: matches strawberry-django's semantics so migration from that package does not surprise consumers.
- Setting `interfaces = ()` or omitting the key keeps `0.0.4` behavior bit-for-bit. Justification: the validation rule from Decision 4 makes the empty/absent case a true no-op, including for the id-suppression step.
- `is_type_of` injection (Decision-1 borrow) is added unconditionally for every `DjangoType`, not only Relay-declared ones. Justification: the cost is one method on the class; it removes a class of subtle interface-dispatch bugs that would otherwise only surface once `Meta.interfaces` is added later. If the consumer declares their own `is_type_of`, we do not overwrite it, matching `strawberry_django/type.py:204-211`.

## Implementation plan

The slice is small enough to implement as a single PR but easier to review as five commits. Each commit cites the exact file:line touched.

1. **Validation + storage**
   - `types/base.py:41-56`: keep `"interfaces"` in `DEFERRED_META_KEYS` for now (promotion is the last step).
   - `types/base.py:243-295` (`_validate_meta`): add the interface tuple/duplicate/Strawberry-interface check from Decision 4.
   - `types/base.py:116-130` (the `DjangoTypeDefinition(...)` construction): pass `interfaces=tuple(getattr(meta, "interfaces", ()))` through to the existing `interfaces` slot at `types/definition.py:36`.
   No new slot on `DjangoTypeDefinition`. Justification: Decision 3 explicitly relies on Strawberry's `NodeID` annotation rather than a per-type `id_attr` Meta key, so the slot would be dead state.

2. **`is_type_of` injection**
   - New helper in `types/base.py` invoked from the existing `__init_subclass__` flow at `types/base.py:77-138`, applied to every `DjangoType` subclass that does not declare its own `is_type_of`. Direct port of `strawberry_django/type.py:204-211`. Justification: applied to all `DjangoType`s (Relay or not) per Decision 6.

3. **`id` suppression**
   - `types/base.py:382-431` (`_build_annotations`): when the source `Meta` declares `relay.Node` among its `interfaces`, drop the `id` key from the synthesized annotations dict before assignment. The selected-field list itself is unchanged so `FieldMeta` and the optimizer still see `id` as a connector column.

4. **Interface base-class injection + Relay resolver defaults**
   - New module `django_strawberry_framework/types/relay.py` containing `_resolve_id_attr_default`, `_resolve_id_default`, `_resolve_node_default`, `_resolve_nodes_default` per Decision 3.
   - `types/finalizer.py:31-83`: insert the new Phase 2.5 step from Decision 5 between the existing `_attach_relation_resolvers` loop and the `strawberry.type(...)` loop. The new step uses `registry.iter_definitions()` exactly the same way the existing loops do (`finalizer.py:68` and `finalizer.py:77`), so the change is structural rather than algorithmic.

5. **Promotion + docs + version**
   - `types/base.py:41-56`: move `"interfaces"` from `DEFERRED_META_KEYS` to `ALLOWED_META_KEYS`. Justification: the promotion rule in `KANBAN.md:925-941` (`BLOCKED-002`) requires every other step to be applied end-to-end first.
   - Doc updates as listed in the "Doc updates" section.
   - Version bump in `pyproject.toml:4` and `django_strawberry_framework/__init__.py:14`; update `tests/base/test_init.py` assertion; regenerate `uv.lock` via `uv lock`.

The five commits can be squashed into a single PR; the per-commit breakdown exists for review legibility.

## Test plan

Tests live in two trees, matching the rules in `docs/TREE.md` and `AGENTS.md`.

### `tests/types/test_relay_interfaces.py` (new)
Package-internal tests, system-under-test is `django_strawberry_framework`.

- `test_meta_interfaces_accepted` — declaring `Meta.interfaces = (relay.Node,)` does not raise.
- `test_meta_interfaces_rejects_non_interface_classes` — passing a plain class raises `ConfigurationError`.
- `test_meta_interfaces_rejects_duplicates` — `(Node, Node)` raises `ConfigurationError`.
- `test_meta_interfaces_empty_tuple_treated_as_unset` — `interfaces = ()` produces unchanged `0.0.4` behavior.
- `test_relay_node_strips_django_id_annotation` — when `relay.Node` is declared, `cls.__annotations__["id"]` is absent after finalization.
- `test_relay_node_injects_default_resolvers` — after finalization the type has classmethods `resolve_id_attr`, `resolve_id`, `resolve_node`, `resolve_nodes`.
- `test_consumer_resolve_id_attr_wins` — declaring `resolve_id_attr` on the subclass keeps the consumer version.
- `test_consumer_resolve_node_wins` — same for `resolve_node`.
- `test_non_relay_interface_works` — declaring a plain `@strawberry.interface` works and skips the Relay-only injection.
- `test_class_already_inherits_relay_node_directly` — `class Foo(DjangoType, relay.Node): class Meta: interfaces = (relay.Node,)` is a no-op duplicate, no error.

### `tests/types/test_definition_order_schema.py` (extend)
- Extend the existing schema-construction tests to assert the GraphQL schema includes `Node` interface and an `id: GlobalID!` field on a Relay-declared type.

### `tests/test_registry.py` (extend)
- After `registry.clear()`, redefining a Relay-declared `DjangoType` and finalizing again works (idempotency / clean-state).

### `examples/fakeshop/test_query/test_library_api.py` (extend)
- Add one HTTP test where a `library` model declares `interfaces = (relay.Node,)` and a `/graphql/` query selects `id` (`GlobalID`) and a scalar field. Assert the response decodes the GlobalID back to the expected database id.

Test-tree placement is mandatory per `AGENTS.md` "Test placement is mandatory"; the spec's pinning is a deliberate copy of that rule.

Coverage: the slice must keep the package coverage gate at 100% (`fail_under = 100`).

## Doc updates

- `docs/FEATURES.md`
  - Move `Meta.interfaces` and `Relay GlobalID mapping for auto IDs` from deferred to shipped.
  - Add a "Relay Node integration" subsection under "DRF-shaped GraphQL API" describing the four `resolve_*` methods and the id suppression behavior.
  - Update the `0.0.5` version mention.

- `docs/README.md`
  - Add a short Node example next to the quick start, gated behind a "Relay Node" subsection so the simple example stays simple.

- `TODAY.md`
  - Drop `Meta.interfaces` and `Relay node and connection integration` from the "wait for" list once Node-only support ships. Connection support stays on the list.
  - Update the fakeshop guidance if any library schema starts using `relay.Node`.

- `KANBAN.md`
  - Move `READY-004` to Done with a `DONE-011` card describing the shipped scope, the borrowed patterns, and the test files.
  - Update the recommended hybrid sequence to advance to `NEXT-001` (`FieldSet`) or `NEXT-002` (filters) for `0.0.6`.

- `CHANGELOG.md`
  - `[0.0.5]` `### Added`: Relay Node interface support, `Meta.interfaces` accepted for any Strawberry interface, default `resolve_id_attr` / `resolve_id` / `resolve_node` / `resolve_nodes` for Relay-declared types, automatic id suppression when `relay.Node` is declared.
  - `### Changed`: `Meta.interfaces` promoted from `DEFERRED_META_KEYS` to `ALLOWED_META_KEYS`.
  - Version bump.

## Risks and open questions

- **Strawberry version compatibility.** The slice depends on `strawberry.relay.Node`, `strawberry.relay.NodeID`, `strawberry.relay.GlobalID`, and `strawberry.relay.ListConnection` being importable, and on `relay.Node` being decorated with `@interface(...)`. The current `pyproject.toml:30` lower bound is `strawberry-graphql>=0.262.0`, which already exposes the full Relay surface. Justification for not bumping the lower bound: nothing in the borrowed code requires a newer Strawberry. If a future borrow does, document the bump in `CHANGELOG.md` and bump `pyproject.toml:30` accordingly.

- **`cls.__bases__` mutation constraints.** Python permits assigning to `cls.__bases__` only when the resulting MRO and instance layout are compatible. In practice this is fine for `DjangoType` + Strawberry interfaces because all interfaces are zero-attribute classes. The implementation must validate the assignment by attempting it and surfacing any `TypeError` from the runtime as a `ConfigurationError` that names the offending interface so the consumer can read the failure. Justification: the failure mode is rare but must surface clearly.

- **Base-class injection vs Strawberry decoration cache.** Strawberry caches `__strawberry_definition__` on classes during `strawberry.type(cls, ...)`. The base-injection step must run **before** `strawberry.type(cls, ...)` for every class on every finalization pass, and `registry.clear()` (`registry.py:172-185`) must continue to release `_definitions` so a redefined class starts fresh. Justification: the existing `clear()` already drops `_definitions`; the slice does not introduce additional state, so this risk reduces to the existing `0.0.4` clear-and-redefine contract.

- **`relay.Node` `is_type_of` interaction.** Decision 6 commits to injecting `is_type_of` for every `DjangoType`. Strawberry's interface dispatch uses `is_type_of` to map a returned ORM instance to the right concrete type. Justification: not borrowing this risks runtime errors like `Cannot determine type for object of model X` when an interface field returns an ORM instance through a Relay-typed field. The cost is one method per class; the failure mode without it is hard to debug post-mortem.

- **`relay.NodeID` annotation discovery.** The default `_resolve_id_attr_default` calls `super(cls, cls).resolve_id_attr()` and falls back to `"pk"`. Strawberry's `Node.resolve_id_attr()` walks `cls.__annotations__` looking for `Annotated[..., relay.NodeID]` (see Strawberry's `relay/types.py`). For a `DjangoType`, the consumer can therefore declare `id: relay.NodeID[str] = strawberry.field(...)` to use, e.g., a slug column. Justification: this is the Strawberry-native mechanism; introducing a parallel `Meta.id_attr` key would fragment the surface.

- **Connection-field stability.** Once `DjangoConnectionField` (`NEXT-005` in `KANBAN.md`) lands, the resolver-injection contract may need hooks for connection fields to call. The four default implementations are intentionally small (one queryset shape, one optimizer call, one filter step) so the connection slice can wrap or replace them without churn.

- **Sentinel/cascade behavior.** Graphene-django routes FK target resolution through `get_node` so its sentinel system works (`django_graphene_filters/object_type.py:186-198`). `0.0.5` deliberately does not adopt that pattern. When the permissions slice (`NEXT-006`) lands, decide whether `apply_cascade_permissions` integrates with `resolve_node` or with our existing `Prefetch` downgrade in the optimizer. That decision belongs to the permissions spec, not this one.

## Out of scope (explicitly tracked elsewhere)

- `DjangoConnectionField` and `DjangoNodeField`: `NEXT-005`.
- Cascade permissions and field-level permissions: `NEXT-006`.
- Connection-aware optimizer planning: `BACKLOG-012`.
- `Meta.primary` / multiple types per model: `READY-002`.
- Stable consumer override semantics for scalar fields: `READY-003`.
- Deferred scalar conversions (`BigIntegerField`, `JSONField`, etc.): `READY-005`.
- Stable choice enum naming: `BACKLOG-007`.
- Layered manual override-test policy: `BACKLOG-011`.
- Migration/adoption guides: `BACKLOG-009`.

## Definition of done

The `0.0.5` slice is complete when all of the following are true:

1. `"interfaces"` is in `ALLOWED_META_KEYS` (`types/base.py:58-67`), validated by `_validate_meta` per Decision 4, and stored on the existing `DjangoTypeDefinition.interfaces` slot at `types/definition.py:36`. No new fields are added to `DjangoTypeDefinition`.
2. `finalize_django_types()` (`types/finalizer.py:31-83`) injects declared interfaces into `cls.__bases__` and runs the `relay.Node` resolver injection (Decision 3) before the existing `strawberry.type(cls, ...)` Phase 3 loop. `0.0.4` behavior is preserved bit-for-bit for types that omit `Meta.interfaces`, verified by the existing test suite passing unchanged.
3. Declaring `interfaces = (relay.Node,)` produces a working Relay-Node GraphQL type with `id: GlobalID!`, the four injected `resolve_*` methods, the `is_type_of` virtual subclass behavior, and consumer override support per Decision 6.
4. Tests in `tests/types/test_relay_interfaces.py` (new), and the extensions to `tests/types/test_definition_order_schema.py`, `tests/test_registry.py`, and `examples/fakeshop/test_query/test_library_api.py` listed in the Test plan all pass.
5. Package coverage stays at 100% (`pyproject.toml:118-129` `[tool.coverage.report] fail_under = 100`).
6. `docs/FEATURES.md`, `docs/README.md`, `TODAY.md`, `KANBAN.md`, and `CHANGELOG.md` reflect the shipped state per the "Doc updates" section.
7. Version bumped to `0.0.5` in `pyproject.toml:4`, `django_strawberry_framework/__init__.py:14`, and the assertion in `tests/base/test_init.py`; `uv.lock` regenerated by running `uv lock`.
8. `KANBAN.md` `READY-004` moves to a new Done card describing the shipped scope (the next available `DONE-NNN` id), and the recommended hybrid sequence in `KANBAN.md:981-993` advances past Relay/`Meta.interfaces`.
9. No new public exports. The public surface stays `DjangoType`, `DjangoOptimizerExtension`, `OptimizerHint`, `finalize_django_types`, `auto`, `__version__` (`django_strawberry_framework/__init__.py:16-23`). Justification: the public-surface promise in `README.md:16` says today's names remain stable through `0.1.0`; `0.0.5` only changes what `Meta.interfaces` enables, not the import surface.
