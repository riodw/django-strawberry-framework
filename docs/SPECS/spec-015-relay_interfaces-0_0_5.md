# Spec: Relay Interfaces and Node Foundation
Target release: `0.0.5`.
Status: final, primary spec for the `0.0.5` slice. This document is the merged, canonical result of three superseded drafts (`-1.md`, `-2.md`, and `-3.md`), all of which have been deleted; this file is the single source of truth for the `READY-004` slice.
Owner: package maintainer.
Predecessors: `docs/GLOSSARY.md`, `GOAL.md`, `KANBAN.md` card `READY-004`.
Influences: the local checkouts referenced from `docs/TREE.md` — `/Users/riordenweber/projects/strawberry-django-main/strawberry_django` and `/Users/riordenweber/projects/django-graphene-filters/django_graphene_filters`.
## Slice checklist
Each top-level item maps to one of the five commits in the "Implementation plan" section. Indented items are the discrete sub-parts to complete inside that slice.
- [ ] Slice 1: Validation + storage
  - [ ] Keep `"interfaces"` in `DEFERRED_META_KEYS` (`django_strawberry_framework/types/base.py #"DEFERRED_META_KEYS: frozenset[str]"`); promotion deferred to Slice 5
  - [ ] Extend `_validate_meta` (`django_strawberry_framework/types/base.py::_validate_meta`) with the interface validator (Decision 4)
    - [ ] Normalize tuple/list input and a single real Strawberry interface class; reject strings, sets, generators, and other invalid non-sequence values
    - [ ] Each entry satisfies `hasattr(entry, "__strawberry_definition__") and entry.__strawberry_definition__.is_interface`
    - [ ] Reject string entries
    - [ ] Reject `DjangoType` self-reference and other `DjangoType` subclasses
    - [ ] Reject duplicates
  - [ ] Pass the normalized interfaces tuple to `DjangoTypeDefinition` at `django_strawberry_framework/types/base.py::DjangoType.__init_subclass__ #"definition = DjangoTypeDefinition("`
  - [ ] Validation and lifecycle tests in `tests/types/test_relay_interfaces.py`
    - [ ] `test_meta_interfaces_accepted`
    - [ ] `test_meta_interfaces_accepts_single_interface_class`
    - [ ] `test_meta_interfaces_rejects_non_sequence`
    - [ ] `test_meta_interfaces_rejects_string_entries`
    - [ ] `test_meta_interfaces_rejects_non_interface_classes`
    - [ ] `test_meta_interfaces_rejects_djangotype_self_reference`
    - [ ] `test_meta_interfaces_rejects_duplicates`
    - [ ] `test_meta_interfaces_empty_tuple_treated_as_unset`
    - [ ] `test_meta_interfaces_stored_on_definition`
    - [ ] `test_class_already_inherits_relay_node_directly`
    - [ ] `test_relay_node_with_composite_pk_raises`
- [ ] Slice 2: `is_type_of` injection
  - [ ] Add `install_is_type_of` helper in new `django_strawberry_framework/types/relay.py`
  - [ ] Invoke from `DjangoType.__init_subclass__` (`django_strawberry_framework/types/base.py::DjangoType.__init_subclass__`) for every `DjangoType` subclass
  - [ ] Preserve consumer-declared `is_type_of` (do not overwrite when present)
  - [ ] Test: `test_is_type_of_injected_for_all_djangotypes`
- [ ] Slice 3: `id` suppression
  - [ ] In `_build_annotations` (`django_strawberry_framework/types/base.py::_build_annotations`), drop the `id` key from the synthesized annotations dict when `relay.Node` is among `Meta.interfaces`
  - [ ] Keep the primary-key field in `DjangoTypeDefinition.field_map` (Decision 7) so the optimizer still sees `id` as a connector column
  - [ ] Tests
    - [ ] `test_relay_node_strips_django_id_annotation`
    - [ ] `test_non_relay_type_keeps_id_int`
- [ ] Slice 4: Interface base-class injection + Relay resolver defaults
  - [ ] Populate `django_strawberry_framework/types/relay.py` with the four `_resolve_*_default` implementations
    - [ ] `_resolve_id_attr_default(cls)` (sync; `super().resolve_id_attr()` with `"pk"` fallback)
    - [ ] `_resolve_id_default(cls, root, info)` (sync; `__dict__` cache check then `getattr`)
    - [ ] `_resolve_node_default(cls, info, node_id, required=False)` (sync + async paths per Decision 9)
    - [ ] `_resolve_nodes_default(cls, info, node_ids=None, required=False)` (sync + async paths per Decision 9)
  - [ ] Add the helper surface in `types/relay.py`
    - [ ] `apply_interfaces(type_cls, definition)`
    - [ ] `implements_relay_node(type_cls)`
    - [ ] `install_relay_node_resolvers(type_cls)` (uses the `__func__` identity test from Decision 3)
  - [ ] Insert Phase 2.5 in `finalize_django_types()` (`django_strawberry_framework/types/finalizer.py::finalize_django_types`) between Phase 2 and Phase 3
    - [ ] Inject each entry of `definition.interfaces` into `cls.__bases__` (skip those already in `cls.__mro__`)
    - [ ] Surface `TypeError` from base assignment as `ConfigurationError` naming the offending interface
    - [ ] Run the composite-pk check when `relay.Node` is among the resolved bases
    - [ ] Inject the four `resolve_*` defaults via the `__func__` identity test
  - [ ] Relay Node behavior tests (`tests/types/test_relay_interfaces.py`)
    - [ ] `test_relay_node_injects_default_resolvers`
    - [ ] `test_resolve_id_attr_falls_back_to_pk`
    - [ ] `test_resolve_id_uses_dict_cache`
    - [ ] `test_resolve_id_falls_back_to_getattr`
    - [ ] `test_resolve_node_applies_get_queryset`
    - [ ] `test_resolve_nodes_preserves_order_and_missing`
    - [ ] `test_resolve_nodes_required_raises_for_missing`
    - [ ] `test_resolve_node_async_context`
    - [ ] `test_resolve_nodes_async_context`
    - [ ] `test_consumer_async_resolve_node_wins`
    - [ ] `test_consumer_resolve_id_attr_wins`
    - [ ] `test_consumer_resolve_id_wins`
    - [ ] `test_consumer_resolve_node_wins`
    - [ ] `test_consumer_resolve_nodes_wins`
    - [ ] `test_node_id_annotation_overrides_default_id_attr`
    - [ ] `test_non_relay_interface_works`
  - [ ] Optimizer / projection tests (`tests/optimizer/`, Decision 7)
    - [ ] `test_relay_id_only_projection_includes_pk_attname`
    - [ ] `test_relay_id_does_not_trigger_lazy_load`
    - [ ] `test_relay_target_relation_planning_unchanged`
    - [ ] `test_relay_resolve_id_uses_loaded_pk`
  - [ ] Schema-construction extensions (`tests/types/test_definition_order_schema.py`)
    - [ ] Schema includes `Node` interface and `id: GlobalID!` on Relay-declared types
    - [ ] Mixed Relay / non-Relay types introspect cleanly (no interface bleed)
  - [ ] Registry idempotency extension (`tests/test_registry.py`): redefining a Relay-declared `DjangoType` after `registry.clear()` works
  - [ ] HTTP test in `examples/fakeshop/test_query/test_library_api.py` (one `library` model declares `interfaces = (relay.Node,)`; `/graphql/` query selects `id` and a scalar; assert GlobalID round-trip)
- [ ] Slice 5: Promotion + docs + version
  - [ ] Move `"interfaces"` from `DEFERRED_META_KEYS` to `ALLOWED_META_KEYS` (`django_strawberry_framework/types/base.py #"DEFERRED_META_KEYS: frozenset[str]"` and `django_strawberry_framework/types/base.py #"ALLOWED_META_KEYS: frozenset[str]"`)
  - [ ] Doc updates
    - [ ] `docs/GLOSSARY.md` — move `Meta.interfaces` and Relay GlobalID mapping from deferred to shipped; add the "Relay Node integration" subsection; update version mention
    - [ ] `docs/README.md` — add the gated "Relay Node" subsection with a short example next to the quick start
    - [ ] `TODAY.md` — drop `Meta.interfaces` and `Relay node` from the "wait for" list; update fakeshop guidance if a `library` schema starts using `relay.Node`
    - [ ] `KANBAN.md` — move `IN-PROGRESS-001` to `DONE-011` with shipped scope, borrowed patterns, and test-file evidence; advance the recommended hybrid sequence past Relay
    - [ ] `CHANGELOG.md` — `[0.0.5]` Added/Changed entries (see Doc updates section); version bump line
  - [ ] Version bump
    - [ ] `pyproject.toml #"version ="`
    - [ ] `django_strawberry_framework/__init__.py #"__version__ ="`
    - [ ] `tests/base/test_init.py` assertion
    - [ ] Regenerate `uv.lock` via `uv lock`
  - [ ] Cleanup
    - [ ] Delete `docs/spec-relay_interfaces-3.md` (drafts `-1.md` and `-2.md` were already removed in an earlier cleanup)
  - [ ] Final gates
    - [ ] `uv run ruff format .` passes
    - [ ] `uv run ruff check --fix .` passes
    - [ ] `uv run pytest` passes with 100% package coverage (`fail_under = 100`)
    - [ ] No new public exports (Definition of done item 11)
## Problem statement
`DjangoType` users cannot declare GraphQL interfaces (Relay `Node` or otherwise) through `class Meta`. Today `Meta.interfaces` is rejected with `ConfigurationError` because the package does not apply it end-to-end. The result is that:
- `GOAL.md`'s target API (`interfaces = (relay.Node,)`) is unreachable today.
- `TODAY.md` lists Relay node and connection support as a hard blocker for the rich fakeshop schema.
- `docs/GLOSSARY.md` lists `Meta.interfaces` and `GlobalID` mapping in the deferred set.
- `KANBAN.md` `READY-004` and `BACKLOG-005` cannot land without a Relay foundation.
- `NEXT-005` (`DjangoConnectionField`) and `NEXT-006` (permissions) cannot start a stable design until interface application is decided.

`0.0.4` shipped the architectural seam this slice needs: `DjangoTypeDefinition.interfaces`, the three-phase `finalize_django_types()` finalizer, and the consumer-override contract for relation fields. `0.0.5` should populate and apply that seam.

The target is not a full connection/query-field release. The target is to make model-backed Relay node types possible in the package's `class Meta` style, while preserving the existing manual list-query surface and optimizer behavior.
## Current state
- `django_strawberry_framework/types/base.py #"DEFERRED_META_KEYS: frozenset[str]"` keeps `interfaces` in `DEFERRED_META_KEYS` (historically — by `0.0.5` the key is already in `ALLOWED_META_KEYS` per the historical comment block in the same file). The historical block comment explicitly identified the missing work: "the relay-interface application pass (`cls.__bases__` injection before `strawberry.type`) has not landed yet." This spec is the answer to that comment.
- `django_strawberry_framework/types/definition.py::DjangoTypeDefinition #"interfaces: tuple[type, ...] = ()"` already declares `interfaces: tuple[type, ...] = ()` on `DjangoTypeDefinition`. The `0.0.4` foundation slice reserved this slot specifically for this work.
- `django_strawberry_framework/types/finalizer.py::finalize_django_types` runs three loops with no interface awareness today: Phase 1 resolves pending relations; Phase 2 calls `_attach_relation_resolvers`; Phase 3 calls `strawberry.type(cls, name=..., description=...)` and marks the definition finalized.
- `django_strawberry_framework/types/converters.py::convert_scalar` synthesizes `id` from `AutoField` / `BigAutoField` / `SmallAutoField` (`django_strawberry_framework/types/converters.py #"SCALAR_MAP: dict[type[models.Field], Any]"`, applied via `django_strawberry_framework/types/converters.py::convert_scalar`). Until this slice, every Django auto-id column produces a GraphQL `id: Int!`, which collides with Strawberry's `Node._id -> id: GlobalID!`.
- `DjangoType.get_queryset(cls, queryset, info, **kwargs)` (`django_strawberry_framework/types/base.py::DjangoType.get_queryset`) is the existing visibility hook. It is stable through `0.1.0` per `README.md #"For the current capability snapshot"` and `docs/README.md #"DjangoOptimizerExtension"`, so the Relay node resolvers can call into it without compatibility risk.
- `DjangoOptimizerExtension` is consultable through `info.context` (`optimizer/extension.py`); the four Relay resolvers can opt into optimizer cooperation the same way root resolvers do today.
- The `0.0.4` lifecycle contract is pinned in `docs/GLOSSARY.md #"Declaring a new concrete"`: "Declaring a new concrete `DjangoType` after finalization raises `ConfigurationError`; tests should use `registry.clear()` and fresh type classes when they need a new registry lifecycle." The Relay slice must preserve this contract bit-for-bit.
## Pre-implementation spike outcome
A minimal local spike against the installed Strawberry version showed that mutating bases before `strawberry.type(...)` works:

```python path=null start=null
class Item(Base):
    name: str


Item.__bases__ = (Base, relay.Node)
strawberry.type(Item)
```

The resulting type is a subclass of `relay.Node`, and Strawberry records the `Node` interface on the object definition. This is the empirical anchor for Decision 1's `cls.__bases__` mutation step and supports the existing design comment in `django_strawberry_framework/types/base.py #"DEFERRED_META_KEYS: frozenset[str]"`. Real `DjangoType` classes carry synthesized annotations, pending relations, generated resolvers, optimizer metadata, inherited `get_queryset`, and consumer-authored relation overrides, so Decision 5 still pins the order of operations explicitly and the test plan covers the full surface.
## Goals
1. Accept `Meta.interfaces` end-to-end so a `DjangoType` can declare any Strawberry-compatible interface (Relay `Node` or otherwise).
2. Make `interfaces = (relay.Node,)` produce a working Relay-node-shaped GraphQL type with `id: GlobalID!`, `resolve_id`, `resolve_id_attr`, `resolve_node`, and `resolve_nodes` wired to Django's ORM and our existing `get_queryset` / optimizer surfaces.
3. Preserve the existing relation-finalization, optimizer, and override contracts shipped in `0.0.4`. Nothing about Phase 1/2/3 lifecycle changes for non-Relay types.
4. Stay tight: no `DjangoConnectionField`, no cascade permissions, no FK redaction sentinels, no node-aware filters, and no broad node-aware optimizer feature work beyond preserving primary-key projection for Relay `id`.
5. Promote `Meta.interfaces` from `DEFERRED_META_KEYS` to `ALLOWED_META_KEYS` only when each behavior listed here is implemented and tested.
## Non-goals
- `DjangoConnectionField` and `DjangoNodeField` (planned for a later slice; this spec only lays the groundwork).
- `Prefetch`-aware Relay edge planning (tracked under `BACKLOG-012`).
- Cascade permissions, redacted-FK sentinels, or `is_redacted` (graphene-django's territory; revisit during the permissions slice).
- Connection-field-driven auto-upgrade of reverse FK / M2M fields (planned for `NEXT-005`).
- Stable `GlobalID`-typed filter inputs (planned for the filters slice).
- Multiple `DjangoType`s per Django model / `Meta.primary` (`READY-002`, separate slice).
- Composite-primary-key support for Relay node mapping (Django 5.2+); explicitly rejected with `ConfigurationError` for `0.0.5` and tracked as future work.
## Borrowing posture
The two reference packages at the paths given in `docs/TREE.md` show two different ways to build this. The slice should borrow patterns (not implementations).
### From `strawberry-django` — borrow heavily
Local source path: `/Users/riordenweber/projects/strawberry-django-main/strawberry_django` (referenced from `docs/TREE.md #"## strawberry_django"`).

- **Resolver injection pattern** — `strawberry_django/type.py::_process_type #"Default querying methods for relay"`. The `if issubclass(cls, relay.Node):` loop iterates `("resolve_id", "resolve_id_attr", "resolve_node", "resolve_nodes")` and replaces the attribute only if `existing_resolver is None or existing_resolver.__func__ is getattr(relay.Node, attr).__func__`. That exact `__func__` identity check is the consumer-override discriminator we should copy because comparing against `cls.__dict__` alone misses inherited Strawberry defaults from `relay.Node` itself. Justification: this slice does not invent a new override-detection scheme; it reuses one that has already been hardened against Strawberry version churn.
- **`resolve_id` shape** — `strawberry_django/relay/utils.py::resolve_model_id`. Read from `root.__dict__[id_attr]` first, fall back to `getattr(root, id_attr)`, coerce to `str`. The dict-cache check is what avoids an extra ORM hit when the row was already loaded into the Django identity map. Justification: matches our `_will_lazy_load` philosophy in `django_strawberry_framework/types/resolvers.py::_will_lazy_load_single` and `django_strawberry_framework/types/resolvers.py::_will_lazy_load_many` and the rest of our optimizer cooperation story.
- **`resolve_id_attr` shape** — `strawberry_django/relay/utils.py::resolve_model_id_attr`. Calls `super(source, source).resolve_id_attr()` and catches `NodeIDAnnotationError` to fall back to `"pk"`. This single try/except is what lets a consumer write `id: relay.NodeID[str]` (e.g. for a slug column) and have it work without our framework adding any new `Meta` key. Justification: zero extra surface, exact alignment with Strawberry's documented `NodeID` mechanism.
- **`resolve_node` / `resolve_nodes` queryset shape** — `strawberry_django/relay/utils.py::resolve_model_nodes` and `strawberry_django/relay/utils.py::resolve_model_node`. Use `_default_manager.all()`, pass through `run_type_get_queryset(qs, origin, info)`, filter on `id_attr` when ids are supplied, then consult the optimizer extension. Justification: every step has a direct counterpart already shipped (`cls.get_queryset(...)` for `run_type_get_queryset`, our `DjangoOptimizerExtension` for theirs). The borrow is structural, not implementation-level.
- **`MAP_AUTO_ID_AS_GLOBAL_ID` behavior** — `strawberry_django/type.py::_process_type #"MAP_AUTO_ID_AS_GLOBAL_ID"`. We borrow the *behavior* of stripping the Django `id` from generated annotations when `relay.Node` is in play, but tie it to the per-type `Meta.interfaces` declaration instead of a global setting. Justification: a global setting fights the existing "loud rejection of unshipped behavior" posture documented in `docs/GLOSSARY.md`; per-type opt-in keeps the contract local to the class declaration.
- **`is_type_of` virtual subclass** — `strawberry_django/type.py::_process_type #"is_type_of"`. We commit to borrowing this. Justification: our root resolvers and relation resolvers (`django_strawberry_framework/types/resolvers.py::_make_relation_resolver`) return Django model instances, not Strawberry-typed wrappers. Strawberry's interface dispatch uses `is_type_of` to identify the concrete type at runtime; without it, an ORM instance returned through a Node-typed field can fail the isinstance check Strawberry uses for interfaces. Strawberry-django chose this exact borrow for the exact same reason; we have no architectural daylight from them on that point.
### From `django-graphene-filters` and `graphene-django` — borrow only the user-facing shape and the validation philosophy
Local source path: `/Users/riordenweber/projects/django-graphene-filters/django_graphene_filters` (referenced from `docs/TREE.md #"## django_graphene_filters"`).

- **`class Meta: interfaces = (Node,)` shape** — `django-graphene-filters/examples/cookbook/cookbook/recipes/schema.py #"class Meta"`. Every node type in the cookbook recipes uses this exact `Meta` shape. Justification: `GOAL.md` already commits us to this shape; the cookbook is what makes that shape concrete for graphene-django users we want to migrate.
- **"Warn loud when Relay-shaped behavior is configured without `Node`"** — `django_graphene_filters/object_type.py #"sentinel"`. The warning fires when sentinel/cascade FK behavior is configured but `Node` is missing. Justification for *not* shipping the warning in `0.0.5`: there is no consumer code path in `0.0.5` that requires Relay (no connection field, no FK redaction). Adding the warning now would warn about behavior that does not yet exist. Defer to the connection or permissions slice.
### Explicitly do not borrow in `0.0.5`
- Graphene-django's `__init_subclass_with_meta__` plumbing or its `_meta` options bag.
- Graphene-django's redacted-sentinel system (`AdvancedDjangoObjectType._make_sentinel`) and cascade FK resolution.
- Graphene-django's connection-field auto-upgrade in `convert_django_field`.
- Strawberry-django's full `_process_type` post-pass that mutates `type_def.fields`. Our finalizer already handles relation finalization through `_attach_relation_resolvers`; we do not need a second field-rewriting pass for the Relay slice.
- Strawberry-django's `StrawberryDjangoField` custom field class. That is a much larger architectural commitment and is tracked separately in `BACKLOG-011`.
- Decorator-style `@strawberry_django.type(Model)`. We keep `class DjangoType` + `class Meta`.
- Wrapping the model primary key directly in `relay.NodeID[py_type]` inside `convert_scalar` (an early draft proposed this). Strawberry's `Node` interface already provides `id: GlobalID!` and resolves the underlying attribute via `resolve_id_attr()`; the simpler borrow is to suppress the synthesized scalar `id` annotation and let the interface-supplied field win, matching `MAP_AUTO_ID_AS_GLOBAL_ID`.
## User-facing API
The shipped consumer surface in `0.0.5` is still `class DjangoType` + `class Meta`. No new public exports are added.
### Basic Relay node type

```python path=null start=null
import strawberry
from strawberry import relay
from django_strawberry_framework import DjangoType, finalize_django_types
from myapp.models import Book


class BookType(DjangoType):
    class Meta:
        model = Book
        fields = ("id", "title")
        interfaces = (relay.Node,)


finalize_django_types()
```
`interfaces = (relay.Node,)` is the canonical spelling. For user ergonomics, `interfaces = relay.Node` and the common missing-comma spelling `interfaces = (relay.Node)` are also accepted and normalized to `(relay.Node,)` when the value is a real Strawberry interface class.

Expected GraphQL behavior:
- `BookType` implements the Relay `Node` interface.
- GraphQL exposes `id` as `GlobalID!`, supplied by the Relay `Node` interface — not the Django `AutoField`.
- The model primary key remains the backing node ID by default (via `resolve_id_attr() -> "pk"`).
- `BookType.resolve_id_attr()` returns `"pk"` by default.
- `BookType.resolve_id(root, info)` returns `str(root.__dict__["pk"])` when the primary key is loaded into the row, falling back to `str(getattr(root, "pk"))` otherwise.
- `BookType.resolve_node(info, node_id)` returns the matching row, with `cls.get_queryset(...)` applied and the optimizer extension consulted if present.
- `BookType.resolve_nodes(info, node_ids=...)` returns the matching rows, same hooks.
- `title` remains a normal generated field.
### Custom Relay resolver override
Consumers may override Relay methods explicitly, and the framework defaults must not clobber them:

```python path=null start=null
from strawberry import relay
from django_strawberry_framework import DjangoType
from myapp.models import Book


class BookType(DjangoType):
    class Meta:
        model = Book
        fields = ("id", "title", "slug")
        interfaces = (relay.Node,)

    @classmethod
    def resolve_id_attr(cls) -> str:
        return "slug"
```

The override discriminator is the `__func__` identity check from Decision 3, not a simple `cls.__dict__` check. The same rule applies to `resolve_id`, `resolve_node`, and `resolve_nodes`. A consumer can also use Strawberry's native annotation mechanism (`id: relay.NodeID[str] = strawberry.field(...)`) to point Relay at a non-pk column without overriding any classmethod.
### `get_queryset` cooperation
`BookType.get_queryset(...)` is invoked from the default `resolve_node` / `resolve_nodes`. A consumer that scopes visibility there will see those filters apply during node fetches:

```python path=null start=null
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
```

Node lookups that filter the row out via `get_queryset` return `None` (or raise when `required=True`), matching strawberry-django's documented behavior.
### Non-Relay interface classes
`Meta.interfaces` may contain any real Strawberry interface class. `0.0.5` applies those interfaces as Python bases before Strawberry decoration; it does not generate extra fields or resolvers for non-Relay interfaces.

```python path=null start=null
from datetime import datetime
import strawberry
from django_strawberry_framework import DjangoType
from myapp.models import Item


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

Same shape, no Relay-specific wiring runs. Non-Relay interface entries are still validated as Strawberry interfaces so the package can fail with `ConfigurationError` before Strawberry decoration when the `Meta` value is malformed.
## Architectural decisions
### Decision 1: where interfaces are applied
Interfaces are applied in `finalize_django_types()` in a new step that runs after Phase 2 (`_attach_relation_resolvers`) and before Phase 3 (`strawberry.type(cls, ...)`). The deferred-key comment at `django_strawberry_framework/types/base.py #"DEFERRED_META_KEYS: frozenset[str]"` already names this seam. Reference: `django_strawberry_framework/types/finalizer.py::finalize_django_types`.

Mechanics: Strawberry treats interfaces through normal class inheritance (`strawberry.relay.Node` is decorated with `@interface(...)` upstream; `hasattr(cls, "__strawberry_definition__")` and `__strawberry_definition__.is_interface` is `True` for any declared interface). We mutate `cls.__bases__` to include each declared interface that is not already in the MRO. After mutation, `strawberry.type(cls, ...)` picks the interfaces up at decoration time without us touching Strawberry internals.

Justification:
- The only alternative — forcing consumers to write `class ItemType(DjangoType, relay.Node):` — contradicts the `class Meta`-driven posture in `GOAL.md` and the public-surface promise in `README.md #"For the current capability snapshot"`.
- `cls.__bases__` mutation is the same mechanism graphene-django uses internally; it is well-trodden Python with one real constraint (see Risks).
- Running this between Phase 2 and Phase 3 means relation-resolver attachment (`_attach_relation_resolvers` at `django_strawberry_framework/types/resolvers.py::_attach_relation_resolvers`) runs against the still-pre-decoration class, which is the point the existing Phase 2 already requires.
### Decision 2: id field handling
When `relay.Node` is among `Meta.interfaces` for a given `DjangoType`:
- `id` is removed from synthesized scalar annotations during `_build_annotations` so the Relay-supplied `id: GlobalID!` is not shadowed by a Django `int` field.
- The Django `id` column itself is still selected for ORM/optimizer purposes (it is the connector column the optimizer relies on); only the Strawberry annotation is suppressed.
- If the consumer includes `"id"` in `Meta.fields` while declaring `relay.Node`, the slice does not raise — the field is simply not generated on the GraphQL side. Document this clearly in `docs/GLOSSARY.md`.
- If `relay.Node` is not in `Meta.interfaces`, behavior is unchanged from `0.0.4`: `id: int!` is generated as before.

This mirrors strawberry-django's `MAP_AUTO_ID_AS_GLOBAL_ID` behavior but is opt-in per type rather than a global setting. A global setting can be added later if real-world adopters need it.

Composite primary keys (Django 5.2+) are explicitly out of scope. When `relay.Node` is declared and the model's primary key is a composite key, finalization raises `ConfigurationError` naming the model and recommending either an explicit `id: relay.NodeID[...]` annotation or removing `relay.Node` from `Meta.interfaces`. Detection uses Django's `model._meta.pk` shape; if Django introduces a stable composite-pk API, the detection should call into it directly.
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

This is a direct copy of strawberry-django's check at `strawberry_django/type.py::_process_type #"existing_resolver.__func__ is getattr(relay.Node, attr).__func__"`. Justification for copying the `__func__` identity test rather than a `cls.__dict__[attr]` membership test: when the consumer does **not** override, `getattr(cls, attr)` resolves through the MRO to `relay.Node`'s default, which is exactly the case we want to overwrite. A `cls.__dict__` check would never see that and would skip injection forever.

The four default implementations live in a new module `django_strawberry_framework/types/relay.py`. The shapes are direct ports of strawberry-django's `relay/utils.py`:

- `_resolve_id_attr_default(cls)` — `try: return super(cls, cls).resolve_id_attr() except NodeIDAnnotationError: return "pk"`. Direct port of `strawberry_django/relay/utils.py::resolve_model_id_attr`. Justification: the `super()` call delegates to Strawberry's own `Node.resolve_id_attr()` (see Strawberry's `relay/types.py` Node implementation), which scans the class for an `Annotated[..., relay.NodeID]` attribute. Falling back to `"pk"` when none is declared matches the most common Django case (auto pk). No new `DjangoTypeDefinition.id_attr` slot is needed; Strawberry already owns that detection.
- `_resolve_id_default(cls, root, info)` — `id_attr = cls.resolve_id_attr(); if id_attr == "pk": id_attr = root.__class__._meta.pk.attname; try: return str(root.__dict__[id_attr]) except KeyError: return str(getattr(root, id_attr))`. Port of `strawberry_django/relay/utils.py::resolve_model_id` (the full port site, including the `"pk"` → concrete pk `attname` coercion at the top — Django stores the pk under its column attname (`"id"`, `"uuid_id"`, etc.), never under the literal `"pk"`, so without the coercion `root.__dict__["pk"]` always misses and Decision 7's "no avoidable lazy loads on `resolve_id`" invariant is violated). Justification: the `__dict__` cache hit is what avoids redundant ORM lookups when the row was loaded by the optimizer.
- `_resolve_node_default(cls, info, node_id, required=False)` — `qs = cls.__django_strawberry_definition__.model._default_manager.all(); qs = cls.get_queryset(qs, info); qs = qs.filter(**{id_attr: node_id}); return qs.get() if required else qs.first()`. Port of `strawberry_django/relay/utils.py::resolve_model_node`, adapted to read the model from our `DjangoTypeDefinition` (`django_strawberry_framework/types/definition.py::DjangoTypeDefinition`) instead of strawberry-django's `StrawberryDjangoDefinition.model`. The optimizer-extension consultation step (upstream's `ext = optimizer extension on info.context; if ext: qs = ext.optimize(qs, info=info)`) is deferred to a follow-up slice per the "Should `resolve_node` use the optimizer?" open question — Decision 7's list-path invariants are exercised through the existing root-gated `DjangoOptimizerExtension` and do not require node-lookup optimizer cooperation in `0.0.5`. The four-step queryset assembly leaves the seam open at the same site for the future slice.
- `_resolve_nodes_default(cls, info, node_ids=None, required=False)` — same queryset shape, optionally filtering on `node_ids` via `id_attr__in`. Order-preserving and missing-id-aware behavior follows strawberry-django's documented contract: when `required=False`, missing ids produce `None` at the matching index in the returned sequence; when `required=True`, missing ids raise `Model.DoesNotExist` (homogeneous with `_resolve_node_default`'s `qs.get()` so consumers can write a single `except Model.DoesNotExist:` clause). Port of `strawberry_django/relay/utils.py::resolve_model_nodes`. The same optimizer-extension deferral noted for `_resolve_node_default` applies here.

We do not import strawberry-django at runtime; we copy the patterns and cite the source at the implementation site. Justification: adding a runtime dependency on strawberry-django would re-introduce decorator-first plumbing the package has explicitly avoided per `pyproject.toml #"dependencies = ["` and the dependency-boundary note in `KANBAN.md`.
### Decision 4: validation
`_validate_meta` (in `django_strawberry_framework/types/base.py::_validate_meta`) gains an interface validator that runs when `interfaces` is declared. Reference: the existing `_format_unknown_fields_error` helper at `django_strawberry_framework/types/base.py::_format_unknown_fields_error` is the canonical error-shape pattern; new errors here reuse the same `model.Meta.<key> ...` shape so consumer-visible failures stay consistent.

Validation rules:

- `interfaces` may be a tuple/list of interface classes or a single real Strawberry interface class. Tuple/list values are normalized to a tuple as-is; a single interface class such as `interfaces = relay.Node` (or the common missing-comma spelling `interfaces = (relay.Node)`) is normalized to `(relay.Node,)`. Strings, sets, generators, and other invalid non-sequence values raise `ConfigurationError`.
- An empty tuple is the same as not declaring the key at all (no-op, identical to `0.0.4` behavior bit-for-bit).
- Each entry must satisfy `hasattr(entry, "__strawberry_definition__") and entry.__strawberry_definition__.is_interface`. `relay.Node` already satisfies this — it is decorated with `@interface(...)` upstream — so no special-casing is required. Justification: writing the check this way is robust against future Strawberry changes to `relay.Node` and forces every accepted entry to be a real Strawberry interface.
- String entries (e.g. `interfaces = ("Node",)`) raise `ConfigurationError`. Lazy/forward-reference interface lookup is out of scope for `0.0.5`.
- Passing `DjangoType` itself (or another consumer `DjangoType` subclass) as an interface entry raises `ConfigurationError`. `DjangoType` is not a Strawberry interface.
- Duplicates raise `ConfigurationError`. The `__bases__` injection step can no-op idempotently, but tolerating duplicates here would let typos hide.
- A class that already inherits from one of the listed interfaces directly (e.g. consumer wrote `class Foo(DjangoType, relay.Node): class Meta: interfaces = (relay.Node,)`) is accepted — the base-injection step is then a structural no-op (`relay.Node in cls.__bases__` is already true).
- The composite-pk constraint from Decision 2 is **not** enforced inside `_validate_meta`. It is enforced once during Phase 2.5 (Decision 5), which runs after `cls.__bases__` is resolved and therefore catches both `Meta.interfaces = (relay.Node,)` consumers and consumers who write `class Foo(DjangoType, relay.Node)` directly. Centralizing the check there avoids duplicating the `model._meta.pk` inspection.

Composition with `Meta.optimizer_hints`: the two keys are independent. `optimizer_hints` continues to apply unchanged. Suppressing the synthesized `id` annotation when `relay.Node` is declared has no effect on the optimizer field map (`FieldMeta` is keyed off Django's field selection, not Strawberry's annotations) — `id` is still selected as the connector column.
### Decision 5: lifecycle and idempotency
- Calling `finalize_django_types()` twice is still a no-op via the existing short-circuit at `django_strawberry_framework/types/finalizer.py::finalize_django_types #"if registry.is_finalized():"`.
- `registry.clear()` (`django_strawberry_framework/registry.py::TypeRegistry.clear`) already drops `_definitions`, `_pending`, `_finalized`, `_types`, `_models`, and `_enums`. Test isolation continues to require **fresh class objects** after `clear()`, exactly as documented in `docs/GLOSSARY.md #"Declaring a new concrete"`. No new tracking state is added on `DjangoTypeDefinition` for the Relay slice — the source of truth is `cls.__bases__` itself for interface injection and the `relay.Node` MRO check for resolver injection. Justification: any new state would be redundant with `cls.__bases__` and would have to be re-validated for clear/redefine cycles, increasing the surface this slice has to test.
- New finalizer step ordering relative to the existing three-loop structure at `django_strawberry_framework/types/finalizer.py::finalize_django_types`:
  - Phase 1 unchanged (`django_strawberry_framework/types/finalizer.py::finalize_django_types #"for pending in registry.iter_pending_relations():"`): resolve pending relations.
  - Phase 2 unchanged (`django_strawberry_framework/types/finalizer.py::finalize_django_types #"_attach_relation_resolvers"`): `_attach_relation_resolvers` for every non-finalized definition.
  - **NEW** Phase 2.5: for each non-finalized definition, if `definition.interfaces` is non-empty, inject those interfaces into `cls.__bases__` (only those not already present in `cls.__mro__`); if `relay.Node` is among the resolved bases, run the composite-pk check (Decision 2) and inject the four `resolve_*` defaults using the `__func__` identity test from Decision 3.
  - Phase 3 unchanged (`django_strawberry_framework/types/finalizer.py::finalize_django_types #"strawberry.type(type_cls, name=definition.name"`): `strawberry.type(cls, name=definition.name, description=definition.description)`; mark `definition.finalized = True`.

The `id` suppression in Decision 2 happens earlier — during `__init_subclass__` collection (`django_strawberry_framework/types/base.py::DjangoType.__init_subclass__`, inside `_build_annotations`) — because that is where the synthesized annotation map is assembled. Justification for splitting suppression (collection-time) and base injection (finalization-time): collection is where `cls.__annotations__` is written; the synthesized annotation map is read by Strawberry at decoration time. Keeping suppression at the same site as annotation synthesis keeps the data flow local. Base injection has to wait for finalization because relation finalization in Phase 1 still needs to mutate `cls.__annotations__` and we do not want a partially-finalized class to also be a partially-interface-injected class.
### Decision 6: compatibility with the override contract
The `0.0.4` relation-field consumer-override contract (`DjangoTypeDefinition.consumer_annotated_relation_fields` and `consumer_assigned_relation_fields`, see `django_strawberry_framework/types/base.py::DjangoType.__init_subclass__` and `django_strawberry_framework/types/finalizer.py::finalize_django_types`) is preserved unchanged.

The new `Meta.interfaces` consumer-override contract is:

- Annotations and fields the interface itself declares (e.g. `Node._id`, which renders as the `id: GlobalID!` field) are owned by the interface. Consumers must not shadow them on the `DjangoType` subclass; doing so will produce a Strawberry-level error at decoration time, which the spec leaves to Strawberry rather than re-implementing.
- `resolve_id_attr` / `resolve_id` / `resolve_node` / `resolve_nodes` declared anywhere in the consumer's MRO above `relay.Node` take precedence over framework defaults via the `__func__` identity test. Justification: matches strawberry-django's semantics so migration from that package does not surprise consumers.
- Setting `interfaces = ()` or omitting the key keeps `0.0.4` behavior bit-for-bit. Justification: the validation rule from Decision 4 makes the empty/absent case a true no-op, including for the id-suppression step.
- `is_type_of` injection (Decision-1 borrow) is added unconditionally for every `DjangoType`, not only Relay-declared ones. Justification: the cost is one method on the class; it removes a class of subtle interface-dispatch bugs that would otherwise only surface once `Meta.interfaces` is added later. If the consumer declares their own `is_type_of`, we do not overwrite it, matching `strawberry_django/type.py::_process_type #"is_type_of"`.
### Decision 7: optimizer and projection invariants
Relay node support must not regress shipped optimizer behavior. Required invariants:

- **Primary-key projection.** When GraphQL selects Relay `id` on a Relay-declared `DjangoType`, the optimizer's `only()` projection must include the concrete primary-key attname. Reference: `django_strawberry_framework/optimizer/walker.py::_walk_selections` (where scalar selections are appended to `only_fields`), and `django_strawberry_framework/optimizer/walker.py::_plan_select_relation` (relation select planning). Justification: Strawberry resolves Relay `id` via `_resolve_id_default`, which reads `root.__dict__[attname]` first; the only way that path produces no extra query is if the optimizer kept `attname` in `only()`.
- **Connector-column preservation.** Existing connector-column behavior (`docs/GLOSSARY.md #"Connector columns required for"`) for `select_related`, reverse FK, FK/OneToOne, and M2M attachment paths is unchanged. The Relay slice does not modify the walker.
- **FK-id elision scoping.** B2 FK-id elision (`django_strawberry_framework/types/resolvers.py::_is_fk_id_elided`, `django_strawberry_framework/optimizer/walker.py::_can_elide_fk_id`) is scoped to forward relation selections. The Relay slice does not introduce a code path where `GlobalID` is fed into FK-id elision logic. Justification: GlobalID handling lives entirely in the Relay resolvers (`django_strawberry_framework/types/relay.py`); the walker continues to see the Django primary-key column it always saw.
- **No avoidable lazy loads on `resolve_id`.** `_resolve_id_default` reads from `root.__dict__` first; if the optimizer kept the pk in `only()`, the `__dict__` cache hit avoids any lazy load. The cache-then-`getattr` order in `strawberry_django/relay/utils.py::resolve_model_id` is the exact reason we chose that borrow.
- **Relation traversal across Relay node targets.** `select_related` / `prefetch_related` planning for relations whose target is a Relay-declared `DjangoType` continues to work unchanged. The optimizer reads target metadata from `DjangoTypeDefinition`, not from the Strawberry `__strawberry_definition__`, so suppressing the synthesized scalar `id` annotation does not affect the optimizer's view of the model.

Implementation note: `DjangoTypeDefinition.field_map` (`django_strawberry_framework/types/definition.py::DjangoTypeDefinition #"field_map: dict[str, FieldMeta]"`) keeps every selected Django field including the primary key, regardless of whether the Strawberry `id` annotation was suppressed. Justification: the field map is the optimizer's source of truth; suppression happens later in the data flow, in `_build_annotations`.
### Decision 8: registry implications and one-type-per-model
`Meta.primary` is out of scope for `0.0.5`. Reference: `KANBAN.md` `READY-002`.

Consequences for `0.0.5`:

- Node lookup remains one `DjangoType` per Django model (`django_strawberry_framework/registry.py::TypeRegistry.register`). Justification: `_resolve_node_default` and `_resolve_nodes_default` look up the model via `cls.__django_strawberry_definition__.model`; without `Meta.primary`, that resolution is unambiguous.
- Multiple `DjangoType`s per model still raise `ConfigurationError` (`django_strawberry_framework/registry.py::TypeRegistry.register`). The Relay slice does not change that contract.
- When `Meta.primary` lands (`READY-002`), the spec for that slice must decide which of multiple types per model owns Relay node lookup. Justification: deferring this decision keeps `0.0.5` tight.
- `registry.clear()` continues to reset definitions and pending relations only; tests that need a clean lifecycle still create fresh class objects after clearing.
### Decision 9: async resolver support
The four `resolve_*` defaults must work in both sync and async resolver contexts because Strawberry permits either at every field, and a consumer's `DjangoType.get_queryset` may itself be sync or async. Without explicit async coverage, the Relay borrow ports only half of strawberry-django's resolver shape and forces every async consumer to re-implement the four defaults.

- `_resolve_id_attr_default(cls)` and `_resolve_id_default(cls, root, info)` are sync. They do not touch the database; they read class state, `root.__dict__`, and `getattr`. Justification: matches strawberry-django's `get_node_id_attr` / `get_node_id` shape; promoting these to async would force `await` plumbing through every Relay node serialization for no benefit.
- `_resolve_node_default` and `_resolve_nodes_default` execute querysets and ship both sync and async paths. Implementation: detect the resolver context (Strawberry's `info` carries an `is_awaitable` signal; `asgiref.sync.iscoroutinefunction` is the fallback), and route through Django's native async queryset API (`aget`, `afirst`, `aiter`, `acount`) when async, falling back to `sync_to_async(qs.first)` / `sync_to_async(qs.get)` for operations that do not yet have native async equivalents. Justification: this is the exact pattern strawberry-django ships in `strawberry_django/relay/utils.py::resolve_model_nodes` and `strawberry_django/relay/utils.py::resolve_model_node` and the only one that survives ASGI / Channels contexts cleanly.
- The optimizer's existing async resolver support (`docs/GLOSSARY.md` Optimizer extension entry, "async resolver support") carries through unchanged because the new resolvers call `ext.optimize(qs, info=info)` with the same signature the existing root-gated optimizer uses.
- A consumer-authored `async def resolve_node(...)` overrides the framework default per Decision 6's `__func__` identity test, exactly the same way a sync override does. The override discriminator does not care about the function's awaitability.

Risk: Django's async ORM is still maturing (Django 4.2+). If a needed async ORM API is missing in the supported Django range, fall back to `sync_to_async` wrapping the equivalent sync call. The package does not need to bump its Django lower bound for `0.0.5`.
## Internal helper surface
The Relay machinery lives in a new module, `django_strawberry_framework/types/relay.py`. Its surface is internal — none of these helpers are re-exported from the top-level package. The signatures below are implementation anchors and may evolve during review; the public surface (item 11 of the Definition of done) stays exactly as it is today.

```python path=null start=null
def apply_interfaces(type_cls: type, definition: DjangoTypeDefinition) -> None:
    """Inject ``definition.interfaces`` into ``type_cls.__bases__`` (Phase 2.5)."""


def implements_relay_node(type_cls: type) -> bool:
    """Return whether ``type_cls`` is a subclass of ``strawberry.relay.Node``."""


def install_relay_node_resolvers(type_cls: type) -> None:
    """Inject the four ``resolve_*`` defaults using the ``__func__`` identity test."""


def install_is_type_of(type_cls: type) -> None:
    """Borrow strawberry-django's ``is_type_of`` virtual subclass behavior."""


def _resolve_id_attr_default(cls: type) -> str:
    """Default ``Node.resolve_id_attr`` implementation; falls back to ``\"pk\"``."""


def _resolve_id_default(cls: type, root: models.Model, info: Any) -> str:
    """Default ``Node.resolve_id`` implementation with ``__dict__`` cache check."""


def _resolve_node_default(
    cls: type,
    info: Any,
    node_id: str | relay.GlobalID,
    required: bool = False,
) -> models.Model | None:
    """Default ``Node.resolve_node`` implementation, ``get_queryset``-aware."""


def _resolve_nodes_default(
    cls: type,
    info: Any,
    node_ids: Iterable[str | relay.GlobalID] | None = None,
    required: bool = False,
) -> Iterable[models.Model | None] | models.QuerySet:
    """Default ``Node.resolve_nodes`` implementation."""
```

The exact public method signatures attached to the class must match Strawberry's `relay.Node` expectations as they exist in the pinned `strawberry-graphql>=0.262.0` lower bound.
## Implementation plan
The slice is small enough to implement as a single PR but easier to review as five commits. Each commit cites the exact `file:line` touched.
1. **Validation + storage**
   - `django_strawberry_framework/types/base.py #"DEFERRED_META_KEYS: frozenset[str]"`: keep `"interfaces"` in `DEFERRED_META_KEYS` for now (promotion is the last step).
   - `django_strawberry_framework/types/base.py::_validate_meta`: add the interface normalization / duplicate / Strawberry-interface check from Decision 4, including support for a single real interface class (`interfaces = relay.Node` or `interfaces = (relay.Node)`), string-entry rejection, and `DjangoType` self-reference rejection. The composite-pk check is **not** done here — it lives in Phase 2.5 (Slice 4) so a single check site catches both `Meta.interfaces = (relay.Node,)` consumers and consumers who write `class Foo(DjangoType, relay.Node)` directly.
   - `django_strawberry_framework/types/base.py::DjangoType.__init_subclass__ #"definition = DjangoTypeDefinition("` (the `DjangoTypeDefinition(...)` construction): pass the normalized interfaces tuple through to the existing `interfaces` slot at `django_strawberry_framework/types/definition.py::DjangoTypeDefinition #"interfaces: tuple[type, ...] = ()"`.
   No new slot on `DjangoTypeDefinition`. Justification: Decision 3 explicitly relies on Strawberry's `NodeID` annotation rather than a per-type `id_attr` Meta key, so the slot would be dead state.

2. **`is_type_of` injection**
   - New helper in `django_strawberry_framework/types/relay.py` invoked from the existing `__init_subclass__` flow at `django_strawberry_framework/types/base.py::DjangoType.__init_subclass__`, applied to every `DjangoType` subclass that does not declare its own `is_type_of`. Direct port of `strawberry_django/type.py::_process_type #"is_type_of"`. Justification: applied to all `DjangoType`s (Relay or not) per Decision 6.

3. **`id` suppression**
   - `django_strawberry_framework/types/base.py::_build_annotations`: when the source `Meta` declares `relay.Node` among its `interfaces`, drop the `id` key from the synthesized annotations dict before assignment. The selected-field list itself is unchanged so `FieldMeta` and the optimizer still see `id` as a connector column.
   - Preserve the primary-key field in metadata for optimizer/projection use (Decision 7).

4. **Interface base-class injection + Relay resolver defaults**
   - New module `django_strawberry_framework/types/relay.py` containing `_resolve_id_attr_default`, `_resolve_id_default`, `_resolve_node_default`, `_resolve_nodes_default`, `apply_interfaces`, `implements_relay_node`, `install_relay_node_resolvers`, and `install_is_type_of` per Decision 3 and the helper sketch above.
   - `_resolve_node_default` and `_resolve_nodes_default` ship sync and async paths per Decision 9; the two ID-shape defaults stay sync.
   - `django_strawberry_framework/types/finalizer.py::finalize_django_types`: insert the new Phase 2.5 step from Decision 5 between the existing `_attach_relation_resolvers` loop and the `strawberry.type(...)` loop. The new step uses `registry.iter_definitions()` exactly the same way the existing loops do (`django_strawberry_framework/types/finalizer.py::finalize_django_types #"_attach_relation_resolvers"` and `django_strawberry_framework/types/finalizer.py::finalize_django_types #"strawberry.type(type_cls, name=definition.name"`), so the change is structural rather than algorithmic. The composite-pk check fires here when `relay.Node` is in the resolved bases; it surfaces a `ConfigurationError` that names the model.
   - Add optimizer/projection tests for Relay `id` so Decision 7 is verified before promotion.

5. **Promotion + docs + version**
   - `django_strawberry_framework/types/base.py #"DEFERRED_META_KEYS: frozenset[str]"` and `django_strawberry_framework/types/base.py #"ALLOWED_META_KEYS: frozenset[str]"`: move `"interfaces"` from `DEFERRED_META_KEYS` to `ALLOWED_META_KEYS`. Justification: the promotion rule in `KANBAN.md` (`BLOCKED-002`) requires every other step to be applied end-to-end first.
   - Doc updates as listed in the "Doc updates" section.
   - Version bump in `pyproject.toml #"version ="` and `django_strawberry_framework/__init__.py #"__version__ ="`; update `tests/base/test_init.py` assertion; regenerate `uv.lock` via `uv lock`.

The five commits can be squashed into a single PR; the per-commit breakdown exists for review legibility.
## Edge cases and constraints
- **Composite primary keys (Django 5.2+).** Combining `relay.Node` with a model whose primary key is a composite raises `ConfigurationError` at finalization. The error names the model and points to either declaring an explicit `id: relay.NodeID[...]` annotation or removing `relay.Node` from `Meta.interfaces`. Tracked as future work; a follow-up slice can add deterministic encoding once Django stabilizes the composite-pk API.
- **Models without an `AutoField`/`BigAutoField`/`SmallAutoField` primary key.** The default `_resolve_id_attr_default` returns `"pk"`; Django resolves that to the actual primary-key attname (`UUIDField`, custom-typed pk, etc.). No special-casing is required as long as the column has a single-column pk.
- **Nullable primary keys.** Not supported by Django for normal models; out of scope.
- **Inherited interfaces via parent `DjangoType`.** A subclass of a Relay-declared `DjangoType` inherits `relay.Node` through `__bases__`. The validation rule in Decision 4 accepts this case as a no-op when the subclass also declares `Meta.interfaces = (relay.Node,)`.
- **Schema reload during tests.** `registry.clear()` plus fresh class definitions remains the only supported reset path. Any HTTP-level test that imports a Relay-declared `DjangoType` must follow the reload pattern documented in `docs/TREE.md` "What each folder holds" for `examples/fakeshop/test_query/`.
## Test plan
Tests live in two trees, matching the rules in `docs/TREE.md` and `AGENTS.md`. Test-tree placement is mandatory; the spec's pinning is a deliberate copy of that rule. Coverage: the slice must keep the package coverage gate at 100% (`fail_under = 100`).
### `tests/types/test_relay_interfaces.py` (new)
Package-internal tests, system-under-test is `django_strawberry_framework`.

Validation and lifecycle:

- `test_meta_interfaces_accepted` — declaring `Meta.interfaces = (relay.Node,)` does not raise.
- `test_meta_interfaces_accepts_single_interface_class` — `interfaces = relay.Node` and `interfaces = (relay.Node)` normalize to `(relay.Node,)` so the missing-comma case is forgiving.
- `test_meta_interfaces_rejects_non_sequence` — invalid non-sequence values, sets, and generators raise `ConfigurationError`.
- `test_meta_interfaces_rejects_string_entries` — string entries raise `ConfigurationError`.
- `test_meta_interfaces_rejects_non_interface_classes` — passing a plain class raises `ConfigurationError`.
- `test_meta_interfaces_rejects_djangotype_self_reference` — passing `DjangoType` (or another `DjangoType` subclass) raises `ConfigurationError`.
- `test_meta_interfaces_rejects_duplicates` — `(Node, Node)` raises `ConfigurationError`.
- `test_meta_interfaces_empty_tuple_treated_as_unset` — `interfaces = ()` produces unchanged `0.0.4` behavior bit-for-bit.
- `test_meta_interfaces_stored_on_definition` — accepted interfaces tuple is stored on `DjangoTypeDefinition.interfaces`.
- `test_class_already_inherits_relay_node_directly` — `class Foo(DjangoType, relay.Node): class Meta: interfaces = (relay.Node,)` is a no-op duplicate, no error.
- `test_relay_node_with_composite_pk_raises` — composite primary key combined with `relay.Node` raises `ConfigurationError` at finalization.

Relay Node behavior:

- `test_relay_node_strips_django_id_annotation` — when `relay.Node` is declared, `cls.__annotations__["id"]` is absent after finalization (the Relay-supplied `id: GlobalID!` field is owned by the interface).
- `test_non_relay_type_keeps_id_int` — control test: a `DjangoType` without `relay.Node` still produces `id: int!` (no regression vs `0.0.4`).
- `test_relay_node_injects_default_resolvers` — after finalization the type has classmethods `resolve_id_attr`, `resolve_id`, `resolve_node`, `resolve_nodes`.
- `test_resolve_id_attr_falls_back_to_pk` — default returns the model's concrete pk attname (e.g. `"id"` after Django resolves `"pk"`).
- `test_resolve_id_uses_dict_cache` — when the row is already loaded into `root.__dict__`, `resolve_id` returns the str without an extra query.
- `test_resolve_id_falls_back_to_getattr` — when the pk is not in `root.__dict__`, `resolve_id` reads via `getattr` and coerces to `str`.
- `test_resolve_node_applies_get_queryset` — a custom `get_queryset` filtering `is_private=False` is applied during node lookup; rows that the filter excludes return `None` (or raise when `required=True`).
- `test_resolve_nodes_preserves_order_and_missing` — passing `node_ids=[a, missing, b]` returns `[obj_a, None, obj_b]` when `required=False`.
- `test_resolve_nodes_required_raises_for_missing` — `required=True` raises for missing ids.
- `test_resolve_node_async_context` — when invoked from an async resolver, `_resolve_node_default` resolves through Django's async ORM API (or `sync_to_async` fallback) and returns the matching row.
- `test_resolve_nodes_async_context` — same for `_resolve_nodes_default`, including the order-preserving / missing-id behavior.
- `test_consumer_async_resolve_node_wins` — a consumer-authored `async def resolve_node(...)` is preserved by the `__func__` identity test exactly like a sync override.
- `test_consumer_resolve_id_attr_wins` — declaring `resolve_id_attr` on the subclass keeps the consumer version.
- `test_consumer_resolve_id_wins` — same for `resolve_id`.
- `test_consumer_resolve_node_wins` — same for `resolve_node`.
- `test_consumer_resolve_nodes_wins` — same for `resolve_nodes`.
- `test_node_id_annotation_overrides_default_id_attr` — declaring `id: relay.NodeID[str] = strawberry.field(...)` wires Relay to a non-pk column without overriding any classmethod.
- `test_non_relay_interface_works` — declaring a plain `@strawberry.interface` works and skips the Relay-only injection.
- `test_is_type_of_injected_for_all_djangotypes` — `is_type_of` is present on Relay and non-Relay `DjangoType`s alike, and a consumer-declared `is_type_of` is preserved.
### `tests/types/test_definition_order_schema.py` (extend)
- Extend the existing schema-construction tests to assert the GraphQL schema includes the `Node` interface and an `id: GlobalID!` field on a Relay-declared type.
- Verify that a schema mixing Relay and non-Relay `DjangoType`s introspects cleanly (no interface bleed).
### `tests/optimizer/` (extend)
These pin Decision 7's invariants:

- `test_relay_id_only_projection_includes_pk_attname` — selecting `{ allItems { id } }` on a Relay-declared type produces an `only()` projection that includes the model's concrete pk attname.
- `test_relay_id_does_not_trigger_lazy_load` — selecting `{ allItems { id otherScalar } }` produces zero N+1 warnings under the strictness sentinel.
- `test_relay_target_relation_planning_unchanged` — relation traversal whose target is a Relay-declared `DjangoType` still plans `select_related` / `prefetch_related` correctly (no regression vs `0.0.4`).
- `test_relay_resolve_id_uses_loaded_pk` — `resolve_id` uses the loaded primary-key value without triggering an avoidable lazy load when the optimizer already selected it.
### `tests/test_registry.py` (extend)
- After `registry.clear()`, redefining a Relay-declared `DjangoType` and finalizing again works (idempotency / clean-state). The redefined class must produce a fresh `Node` interface registration.
### `examples/fakeshop/test_query/test_library_api.py` (extend)
- Add one HTTP test where a `library` model declares `interfaces = (relay.Node,)` and a `/graphql/` query selects `id` (`GlobalID`) and a scalar field. Assert the response decodes the GlobalID back to the expected database id. Follow the existing reload pattern at the top of `test_library_api.py` (clear the global registry, reload app schema modules, then reload the project schema and URLconf).
## Doc updates
- `docs/GLOSSARY.md`
  - Move `Meta.interfaces` and `Relay GlobalID mapping for auto IDs` from deferred to shipped.
  - Add a "Relay Node integration" subsection under "DRF-shaped GraphQL API" describing the four `resolve_*` methods, the id suppression behavior, and the composite-pk constraint.
  - Update the `0.0.5` version mention.

- `docs/README.md`
  - Add a short Node example next to the quick start, gated behind a "Relay Node" subsection so the simple example stays simple.

- `TODAY.md`
  - Drop `Meta.interfaces` and `Relay node` from the "wait for" list once Node-only support ships. Connection support stays on the list.
  - Update the fakeshop guidance if any library schema starts using `relay.Node`.

- `KANBAN.md`
  - Move `READY-004` to Done with a new `DONE-NNN` card describing the shipped scope, the borrowed patterns, and the test files.
  - Update the recommended hybrid sequence to advance to `NEXT-001` (`FieldSet`) or `NEXT-002` (filters) for `0.0.6`.

- `CHANGELOG.md`
  - `[0.0.5]` `### Added`: Relay Node interface support, `Meta.interfaces` accepted for any Strawberry interface, default `resolve_id_attr` / `resolve_id` / `resolve_node` / `resolve_nodes` for Relay-declared types, automatic id suppression when `relay.Node` is declared, `is_type_of` injection for all `DjangoType`s.
  - `### Changed`: `Meta.interfaces` promoted from `DEFERRED_META_KEYS` to `ALLOWED_META_KEYS`.
  - `### Fixed` / `### Removed`: as needed by the implementation.
  - Version bump.
## Risks and open questions
Each item names a preferred answer for `0.0.5` and a fallback if implementation reveals the preferred answer is wrong.

- **Strawberry version compatibility.** The slice depends on `strawberry.relay.Node`, `strawberry.relay.NodeID`, `strawberry.relay.GlobalID`, and `strawberry.relay.ListConnection` being importable, and on `relay.Node` being decorated with `@interface(...)`. The current `pyproject.toml #"strawberry-graphql>=0.262.0"` lower bound is `strawberry-graphql>=0.262.0`, which already exposes the full Relay surface. Preferred answer: do not bump the lower bound. Fallback: if a future borrow forces a newer Strawberry version, bump `pyproject.toml #"strawberry-graphql>=0.262.0"` and document the bump in `CHANGELOG.md`.

- **`cls.__bases__` mutation constraints.** Python permits assigning to `cls.__bases__` only when the resulting MRO and instance layout are compatible. In practice this is fine for `DjangoType` + Strawberry interfaces because all interfaces are zero-attribute classes. Preferred answer: attempt the assignment and surface any `TypeError` as a `ConfigurationError` that names the offending interface. Fallback: if base mutation is unsafe for some real `DjangoType` shape, the implementation creates a replacement class with the desired bases and updates `registry._types` / `_definitions` to point at it, or narrows the slice to require explicit `class Foo(DjangoType, relay.Node):` and reserves `Meta.interfaces` for a later slice. The Meta-driven path is preferred; the fallbacks exist so the slice can ship even if a corner case turns up.

- **Should non-Relay interfaces ship in 0.0.5?** Preferred answer: yes. Generic interface base application with Strawberry validation is in scope; Relay receives the package-installed Django defaults; non-Relay interfaces do not. Fallback: if generic interfaces complicate the slice, narrow to `relay.Node` only and keep non-Relay interfaces rejected with a focused error.

- **Should Relay ID mapping be configurable globally?** Preferred answer for `0.0.5`: no. Relay ID mapping activates per-type when `relay.Node` is declared. Fallback: a future setting can be added if real-world adopters need to decouple Node participation from `id` field mapping; until then, the per-type opt-in matches `docs/GLOSSARY.md`'s loud-rejection posture.

- **Should `resolve_node` use the optimizer?** Preferred answer for `0.0.5`: apply `cls.get_queryset(...)` and consult the optimizer extension only if it is straightforward. Justification: root `QuerySet` optimization is already shipped and well-tested; deeper Node-field optimization becomes load-bearing when `DjangoNodeField` ships.

- **Base-class injection vs Strawberry decoration cache.** Strawberry caches `__strawberry_definition__` on classes during `strawberry.type(cls, ...)`. The base-injection step must run **before** `strawberry.type(cls, ...)` for every class on every finalization pass, and `registry.clear()` (`django_strawberry_framework/registry.py::TypeRegistry.clear`) must continue to release `_definitions` so a redefined class starts fresh. Justification: the existing `clear()` already drops `_definitions`; the slice does not introduce additional state, so this risk reduces to the existing `0.0.4` clear-and-redefine contract.

- **`relay.Node` `is_type_of` interaction.** Decision 6 commits to injecting `is_type_of` for every `DjangoType`. Strawberry's interface dispatch uses `is_type_of` to map a returned ORM instance to the right concrete type. Justification: not borrowing this risks runtime errors like `Cannot determine type for object of model X` when an interface field returns an ORM instance through a Relay-typed field. The cost is one method per class; the failure mode without it is hard to debug post-mortem.

- **`relay.NodeID` annotation discovery.** The default `_resolve_id_attr_default` calls `super(cls, cls).resolve_id_attr()` and falls back to `"pk"`. Strawberry's `Node.resolve_id_attr()` walks `cls.__annotations__` looking for `Annotated[..., relay.NodeID]` (see Strawberry's `relay/types.py`). For a `DjangoType`, the consumer can therefore declare `id: relay.NodeID[str] = strawberry.field(...)` to use, e.g., a slug column. Justification: this is the Strawberry-native mechanism; introducing a parallel `Meta.id_attr` key would fragment the surface.

- **Composite primary keys (Django 5.2+).** Preferred answer for `0.0.5`: reject at finalization with a clear `ConfigurationError`. Fallback: if real-world adopters need composite-pk Relay nodes urgently, a follow-up slice can add a deterministic encode/decode contract for composite keys; that contract is non-trivial and out of scope here.

- **Connection-field stability.** Once `DjangoConnectionField` (`NEXT-005` in `KANBAN.md`) lands, the resolver-injection contract may need hooks for connection fields to call. The four default implementations are intentionally small (one queryset shape, one optimizer call, one filter step) so the connection slice can wrap or replace them without churn.

- **Sentinel/cascade behavior.** Graphene-django routes FK target resolution through `get_node` so its sentinel system works (`django_graphene_filters/object_type.py #"sentinel"`). `0.0.5` deliberately does not adopt that pattern. When the permissions slice (`NEXT-006`) lands, decide whether `apply_cascade_permissions` integrates with `resolve_node` or with our existing `Prefetch` downgrade in the optimizer. That decision belongs to the permissions spec, not this one.
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
- Composite-primary-key Relay node encoding: future slice.
## Definition of done
The `0.0.5` slice is complete when all of the following are true:

1. `"interfaces"` is in `ALLOWED_META_KEYS` (`django_strawberry_framework/types/base.py #"ALLOWED_META_KEYS: frozenset[str]"`), validated by `_validate_meta` per Decision 4, and stored on the existing `DjangoTypeDefinition.interfaces` slot at `django_strawberry_framework/types/definition.py::DjangoTypeDefinition #"interfaces: tuple[type, ...] = ()"`. No new fields are added to `DjangoTypeDefinition`.
2. `finalize_django_types()` (`django_strawberry_framework/types/finalizer.py::finalize_django_types`) injects declared interfaces into `cls.__bases__` and runs the `relay.Node` resolver injection (Decision 3) before the existing `strawberry.type(cls, ...)` Phase 3 loop. `0.0.4` behavior is preserved bit-for-bit for types that omit `Meta.interfaces`, verified by the existing test suite passing unchanged.
3. Declaring `interfaces = (relay.Node,)` produces a working Relay-Node GraphQL type with `id: GlobalID!`, the four injected `resolve_*` methods, the `is_type_of` virtual subclass behavior, and consumer override support per Decision 6. The single-interface forms `interfaces = relay.Node` and `interfaces = (relay.Node)` normalize to the same stored tuple.
4. Composite-pk models combined with `relay.Node` raise `ConfigurationError` at finalization with a message that names the model and proposes a remediation path.
5. Optimizer invariants in Decision 7 hold: `only()` includes the pk attname when Relay `id` is selected, `resolve_id` does not trigger an avoidable lazy load, and relation traversal across Relay-declared targets is unchanged.
6. Tests in `tests/types/test_relay_interfaces.py` (new), and the extensions to `tests/types/test_definition_order_schema.py`, `tests/optimizer/`, `tests/test_registry.py`, and `examples/fakeshop/test_query/test_library_api.py` listed in the Test plan all pass.
7. Package coverage stays at 100% (`pyproject.toml [tool.coverage.report] fail_under = 100`).
8. `docs/GLOSSARY.md`, `docs/README.md`, `TODAY.md`, `KANBAN.md`, and `CHANGELOG.md` reflect the shipped state per the "Doc updates" section.
9. Version bumped to `0.0.5` in `pyproject.toml #"version ="`, `django_strawberry_framework/__init__.py #"__version__ ="`, and the assertion in `tests/base/test_init.py`; `uv.lock` regenerated by running `uv lock`.
10. `KANBAN.md` `READY-004` moves to a new Done card describing the shipped scope (the next available `DONE-NNN` id), and the recommended hybrid sequence advances past Relay/`Meta.interfaces`.
11. No new public exports. The public surface stays `DjangoType`, `DjangoOptimizerExtension`, `OptimizerHint`, `finalize_django_types`, `auto`, `__version__` (`django_strawberry_framework/__init__.py #"__all__ = ("`). Justification: the public-surface promise in `README.md #"For the current capability snapshot"` says today's names remain stable through `0.1.0`; `0.0.5` only changes what `Meta.interfaces` enables, not the import surface.
12. `_resolve_node_default` and `_resolve_nodes_default` work in both sync and async resolver contexts per Decision 9. A consumer-authored `async def resolve_node(...)` is preserved by the override contract.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
