# Spec: Relay Interfaces and Node Foundation
Target release: `0.0.5`.
Status: shipped. Primary spec for the `0.0.5` Relay foundation and the single source of truth for card `DONE-015-0.0.5`.
Owner: package maintainer.
Predecessors: `docs/GLOSSARY.md`, `GOAL.md`, `KANBAN.md` card `DONE-015-0.0.5`.
Influences: the local checkouts referenced from `docs/TREE.md` — `/Users/riordenweber/projects/strawberry-django-main/strawberry_django` and `/Users/riordenweber/projects/django-graphene-filters/django_graphene_filters`.
Rationale companion: [`docs/SPECS/appx/spec-015-relay_interfaces-0_0_5-rationale.md`][spec-015-rationale] carries this spec's deliberative layer — the borrowing posture and its per-borrow justifications, the pre-implementation spike, the risk register, every rejected alternative, and the record of what later cards changed and why.
## Slice checklist
Each top-level item maps to one of the five commits in the "Implementation plan" section. Indented items are the discrete sub-parts to complete inside that slice.
- [ ] Slice 1: Validation + storage
  - [ ] Keep `"interfaces"` in `DEFERRED_META_KEYS` (`django_strawberry_framework/types/base.py #"DEFERRED_META_KEYS: frozenset[str]"`); promotion deferred to Slice 5
  - [ ] Extend `_validate_meta` (`django_strawberry_framework/types/base.py::_validate_meta`) with the interface validator (Decision 4)
    - [ ] Normalize tuple/list input and a single real Strawberry interface class; reject strings, sets, generators, and other invalid non-sequence values
    - [ ] Each entry satisfies `hasattr(entry, "__strawberry_definition__") and entry.__strawberry_definition__.is_interface`
    - [ ] Reject string entries
    - [ ] Reject [`DjangoType`][glossary-djangotype] self-reference and other `DjangoType` subclasses
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
- [ ] Slice 3: primary-key annotation suppression
  - [ ] In `_build_annotations` (`django_strawberry_framework/types/base.py::_build_annotations`), drop the primary-key field's name from the synthesized annotations dict for a Relay-shaped type — [`Meta.interfaces`][glossary-metainterfaces] carrying `relay.Node` (or any interface subclassing it), or direct `relay.Node` inheritance (Decision 2)
  - [ ] Keep the primary-key field in `DjangoTypeDefinition.field_map` (Decision 7) so the optimizer still sees the pk as a connector column
  - [ ] Tests
    - [ ] `test_relay_node_strips_django_id_annotation`
    - [ ] `test_non_relay_type_keeps_id_int`
- [ ] Slice 4: Interface base-class injection + Relay resolver defaults
  - [ ] Populate `django_strawberry_framework/types/relay.py` with the four `_resolve_*_default` implementations
    - [ ] `_resolve_id_attr_default(cls)` (sync; reads the Phase-2.5 id-attribute stamp, `"pk"` fallback)
    - [ ] `_resolve_id_default(cls, root, *, info)` (sync; `"pk"` → concrete pk attname, `__dict__` cache check then `getattr`)
    - [ ] `_resolve_node_default(cls, node_id, *, info, required=False)` (sync + async paths per Decision 9)
    - [ ] `_resolve_nodes_default(cls, *, info, node_ids=None, required=False)` (sync + async paths per Decision 9)
  - [ ] Add the helper surface in `types/relay.py`
    - [ ] `apply_interfaces(type_cls, definition)`
    - [ ] `implements_relay_node(type_cls)`
    - [ ] `install_relay_node_resolvers(type_cls)` (uses the `__func__` identity test from Decision 3)
    - [ ] `_check_composite_pk_for_relay_node(type_cls)` and `_stamp_relay_id_attr(type_cls)` (Decisions 2 and 3)
  - [ ] Insert Phase 2.5 in `finalize_django_types()` (`django_strawberry_framework/types/finalizer.py::finalize_django_types`) between Phase 2 and Phase 3
    - [ ] Inject each entry of `definition.interfaces` into `cls.__bases__` (skip those already in `cls.__mro__`)
    - [ ] Surface `TypeError` from base assignment as [`ConfigurationError`][glossary-configurationerror] naming the offending interface
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
  - [ ] Optimizer / projection tests (`tests/optimizer/test_relay_id_projection.py`, Decision 7)
    - [ ] `test_relay_id_only_projection_includes_pk_attname`
    - [ ] `test_relay_id_does_not_trigger_lazy_load`
    - [ ] `test_relay_resolve_id_uses_loaded_pk`
    - [ ] Relation traversal across Relay-declared targets, pinned live in `examples/fakeshop/test_query/test_products_api.py`
  - [ ] Schema-construction coverage, live in `examples/fakeshop/test_query/test_library_api.py`
    - [ ] Schema includes the `Node` interface and the GlobalID-scalar `id` on Relay-declared types
    - [ ] Mixed Relay / non-Relay types introspect cleanly (no interface bleed)
  - [ ] Registry idempotency extension (`tests/test_registry.py`): redefining a Relay-declared `DjangoType` after `registry.clear()` works
  - [ ] HTTP test in `examples/fakeshop/test_query/test_library_api.py` (one `library` model declares `interfaces = (relay.Node,)`; `/graphql/` query selects `id` and a scalar; assert GlobalID round-trip)
- [ ] Slice 5: Promotion + docs + version
  - [ ] Move `"interfaces"` from `DEFERRED_META_KEYS` to `ALLOWED_META_KEYS` (`django_strawberry_framework/types/base.py #"DEFERRED_META_KEYS: frozenset[str]"` and `django_strawberry_framework/types/base.py #"ALLOWED_META_KEYS: frozenset[str]"`)
  - [ ] Doc updates
    - [ ] `docs/GLOSSARY.md` — move `Meta.interfaces` and Relay GlobalID mapping from deferred to shipped; add the "[Relay Node integration][glossary-relay-node-integration]" subsection; update version mention
    - [ ] `docs/README.md` — add the gated "Relay Node" subsection with a short example next to the quick start
    - [ ] `TODAY.md` — drop `Meta.interfaces` and `Relay node` from the "wait for" list; update fakeshop guidance if a `library` schema starts using `relay.Node`
    - [ ] `KANBAN.md` — move this card to Done as `DONE-015-0.0.5` with shipped scope, borrowed patterns, and test-file evidence; advance the recommended hybrid sequence past Relay
    - [ ] `CHANGELOG.md` — `[0.0.5]` Added/Changed entries (see Doc updates section); version bump line
  - [ ] Version bump
    - [ ] `pyproject.toml #"version ="`
    - [ ] `django_strawberry_framework/__init__.py #"__version__ ="`
    - [ ] `tests/base/test_init.py` assertion
    - [ ] Regenerate `uv.lock` via `uv lock`
  - [ ] Final gates
    - [ ] `uv run ruff format .` passes
    - [ ] `uv run ruff check --fix .` passes
    - [ ] `uv run pytest` passes with 100% package coverage (`fail_under = 100`)
    - [ ] No new [public exports][glossary-public-exports] (Definition of done item 11)
## Problem statement
The problem this slice exists to solve, as it stood at `0.0.4`: a `DjangoType` user cannot declare GraphQL interfaces (Relay `Node` or otherwise) through `class Meta`, because `Meta.interfaces` is a deferred key rejected with `ConfigurationError` — the package does not apply it end-to-end. The consequences were:
- `GOAL.md`'s target API (`interfaces = (relay.Node,)`) is unreachable today.
- `TODAY.md` lists Relay node and connection support as a hard blocker for the rich fakeshop schema.
- `docs/GLOSSARY.md` lists `Meta.interfaces` and `GlobalID` mapping in the deferred set.
- The Relay-shaped cards on `KANBAN.md` cannot land without a Relay foundation.
- [`DjangoConnectionField`][glossary-djangoconnectionfield] and the permissions subsystem cannot start a stable design until interface application is decided.

`0.0.4` shipped the architectural seam this slice needs: `DjangoTypeDefinition.interfaces`, the three-phase `finalize_django_types()` finalizer, and the consumer-override contract for relation fields. `0.0.5` should populate and apply that seam.

The target is not a full connection/query-field release. The target is to make model-backed Relay node types possible in the package's `class Meta` style, while preserving the existing manual list-query surface and optimizer behavior.
## Current state
- `"interfaces"` is an accepted `Meta` key: it sits in `django_strawberry_framework/types/base.py #"ALLOWED_META_KEYS: frozenset[str]"`, validated by `django_strawberry_framework/types/base.py::_validate_interfaces` and stored on the definition. `DEFERRED_META_KEYS` holds only `aggregate_class`, `fields_class`, and `search_fields`.
- `django_strawberry_framework/types/definition.py::DjangoTypeDefinition #"interfaces: tuple[type, ...] = ()"` declares `interfaces: tuple[type, ...] = ()` on `DjangoTypeDefinition`. The `0.0.4` foundation slice reserved this slot specifically for this work; this slice fills it and adds no other.
- `django_strawberry_framework/types/finalizer.py::finalize_django_types` runs Phase 1 (resolve pending relations), Phase 2 (`_attach_relation_resolvers`), the Phase 2.5 interface pass this spec adds, and Phase 3 (`strawberry.type(cls, name=..., description=...)`, then mark the definition finalized).
- `django_strawberry_framework/types/converters.py::convert_scalar` synthesizes `id` from `AutoField` / `BigAutoField` / `SmallAutoField` (`django_strawberry_framework/types/converters.py #"SCALAR_MAP: dict[type[models.Field], Any]"`, applied via `django_strawberry_framework/types/converters.py::convert_scalar`), so a non-Relay `DjangoType` produces a GraphQL `id: Int!`. On a Relay-shaped type that annotation would collide with Strawberry's `Node._id -> id: GlobalID!`, which is what Decision 2 suppresses.
- `DjangoType.get_queryset(cls, queryset, info, **kwargs)` (`django_strawberry_framework/types/base.py::DjangoType.get_queryset`) is the shipped visibility hook, documented in `docs/README.md #"visibility hook (cooperates with the optimizer"`. Every framework-owned invocation of it — the Relay node resolvers included — runs through the shared hardened boundary at `django_strawberry_framework/utils/querysets.py::apply_type_visibility_sync` / `::apply_type_visibility_async`, so the Relay resolvers call into it through that seam rather than directly.
- [`DjangoOptimizerExtension`][glossary-djangooptimizerextension] is consultable through `info.context` (`optimizer/extension.py`), and root-level list resolvers receive full optimizer treatment. Per-node optimizer cooperation inside `resolve_node` / `resolve_nodes` is deliberately not wired (Decision 3).
- The `0.0.4` lifecycle contract is pinned in `docs/GLOSSARY.md #"Declaring a new concrete"`: "Declaring a new concrete `DjangoType` after finalization raises `ConfigurationError`; tests that need a new registry lifecycle should use `registry.clear()` and fresh type classes." The Relay slice preserves this contract bit-for-bit.
## Goals
1. Accept `Meta.interfaces` end-to-end so a `DjangoType` can declare any Strawberry-compatible interface (Relay `Node` or otherwise).
2. Make `interfaces = (relay.Node,)` produce a working Relay-node-shaped GraphQL type with `id: GlobalID!`, `resolve_id`, `resolve_id_attr`, `resolve_node`, and `resolve_nodes` wired to Django's ORM and our existing `get_queryset` / optimizer surfaces.
3. Preserve the existing relation-finalization, optimizer, and override contracts shipped in `0.0.4`. Nothing about Phase 1/2/3 lifecycle changes for non-Relay types.
4. Stay tight: no `DjangoConnectionField`, no cascade permissions, no FK redaction sentinels, no node-aware filters, and no broad node-aware optimizer feature work beyond preserving primary-key projection for Relay `id`.
5. Promote `Meta.interfaces` from `DEFERRED_META_KEYS` to `ALLOWED_META_KEYS` only when each behavior listed here is implemented and tested.
## Non-goals
- `DjangoConnectionField` and [`DjangoNodeField`][glossary-djangonodefield]; this spec only lays the groundwork they build on.
- `Prefetch`-aware Relay edge planning.
- Cascade permissions ([`apply_cascade_permissions`][glossary-apply-cascade-permissions]), redacted-FK sentinels, or `is_redacted`; that surface belongs to the permissions slice.
- Connection-field-driven auto-upgrade of reverse FK / M2M fields.
- Stable `GlobalID`-typed filter inputs; that surface belongs to the filters slice.
- Multiple `DjangoType`s per Django model / [`Meta.primary`][glossary-metaprimary], a separate slice.
- Composite-primary-key support for Relay node mapping (Django 5.2+); explicitly rejected with `ConfigurationError` for `0.0.5` and tracked as future work.
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
- `BookType.resolve_id_attr()` returns the literal `"pk"` by default (a consumer `relay.NodeID[...]` annotation returns that attribute's name instead).
- `BookType.resolve_id(root, info=info)` coerces `"pk"` to the model's concrete primary-key `attname` and returns `str(root.__dict__[attname])` when the row already carries it, falling back to `str(getattr(root, attname))` otherwise.
- `BookType.resolve_node(node_id, info=info)` returns the matching row, with the type's `get_queryset` visibility applied through the shared boundary.
- `BookType.resolve_nodes(info=info, node_ids=...)` returns the matching rows, same hook.
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

The override discriminator is the `__func__` identity check from Decision 3, not a simple `cls.__dict__` check. The same rule applies to `resolve_id`, `resolve_node`, and `resolve_nodes`. A consumer can also use Strawberry's native annotation mechanism to point Relay at a non-pk column without overriding any classmethod: annotate the target attribute as `slug: relay.NodeID[str]`, subscripted (the bare `Annotated[str, relay.NodeID]` form does not register). On a Relay-shaped type the `id` name itself is the interface's: an `id` annotation must be `relay.NodeID[...]`, and an assigned `id = strawberry.field(...)` is refused with `ConfigurationError` pointing at `resolve_id`, a `relay.NodeID[...]` annotation, or a resolver-backed sibling field.
### `get_queryset` cooperation
The default `resolve_node` / `resolve_nodes` apply `BookType.get_queryset(...)`, so a consumer that scopes visibility there sees those filters apply during node fetches:

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

Node lookups that filter the row out via `get_queryset` return `None` (or raise when `required=True`), matching strawberry-django's documented behavior. The hook is not invoked directly: both defaults route it through the shared visibility boundary (`django_strawberry_framework/utils/querysets.py::apply_type_visibility_sync` and `::apply_type_visibility_async`), which is what makes an `async def get_queryset` work on the async path and raise `SyncMisuseError` on the sync one (Decision 9).
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
Interfaces are applied in `finalize_django_types()` in a new step that runs after Phase 2 (`_attach_relation_resolvers`) and before Phase 3 (`strawberry.type(cls, ...)`). Reference: `django_strawberry_framework/types/finalizer.py::finalize_django_types`.

Mechanics: Strawberry treats interfaces through normal class inheritance (`strawberry.relay.Node` is decorated with `@interface(...)` upstream; `hasattr(cls, "__strawberry_definition__")` and `__strawberry_definition__.is_interface` is `True` for any declared interface). We mutate `cls.__bases__` to include each declared interface that is not already in the MRO. After mutation, `strawberry.type(cls, ...)` picks the interfaces up at decoration time without us touching Strawberry internals.

A `TypeError` from the base assignment — Python rejecting the resulting MRO or instance layout — is surfaced as a [`ConfigurationError`][glossary-configurationerror] naming the offending interface, never as a raw layout error.

`Meta.interfaces` is the declared path, not the only one. A consumer who writes `class ItemType(DjangoType, relay.Node):` directly reaches the same Relay wiring, because the Phase 2.5 Relay steps gate on the resolved MRO (`implements_relay_node`) rather than on the `Meta` tuple.

The spike that established `cls.__bases__` mutation is safe here, and the alternative designs this Decision rejected, are in the [rationale companion][spec-015-rationale].
### Decision 2: id field handling
Suppression is keyed to a single predicate, `django_strawberry_framework/types/base.py::_is_relay_shaped`, which is true when any entry of the validated `Meta.interfaces` tuple is a `relay.Node` subclass **or** the class itself already subclasses `relay.Node`. So it fires for `interfaces = (relay.Node,)`, for a consumer `@strawberry.interface` that extends `relay.Node`, and for direct `class Foo(DjangoType, relay.Node)` inheritance alike. For such a type:

- The **primary-key field's name** (`model._meta.pk.name`, not the literal `"id"`) is removed from synthesized scalar annotations during `_build_annotations`, so the Relay-supplied `id: GlobalID!` is not shadowed by a Django scalar field. Using the field name rather than the column attname is what makes a renamed pk and a relation primary key (`OneToOneField(primary_key=True)`, whose `name` is `user` while its `attname` is `user_id`) suppress correctly.
- The primary-key column itself is still selected for ORM/optimizer purposes (it is the connector column the optimizer relies on); only the Strawberry annotation is suppressed.
- If the consumer includes the pk in [`Meta.fields`][glossary-metafields] while declaring `relay.Node`, the slice does not raise — the field is simply not generated on the GraphQL side. Document this clearly in `docs/GLOSSARY.md`.
- If the type is not Relay-shaped, behavior is unchanged from `0.0.4`: `id: int!` is generated as before.

This mirrors strawberry-django's `MAP_AUTO_ID_AS_GLOBAL_ID` behavior but is opt-in per type rather than a global setting. A global setting can be added later if real-world adopters need it.

Composite primary keys (Django 5.2+) are explicitly out of scope for Relay node mapping. When a Relay-shaped type's model has a composite primary key, finalization raises `ConfigurationError` naming the model and recommending either an explicit `id: relay.NodeID[...]` annotation or removing `relay.Node` from `Meta.interfaces` — and it **honors the first of those remediations**: a type declaring an explicit `relay.NodeID[...]` attribute passes the gate, since it has named a single-column node id. Only the no-annotation case raises. Detection is `isinstance(model._meta.pk, CompositePrimaryKey)`, Django's native composite-pk type.

The gate asks Strawberry's annotation scan directly (`relay.Node.resolve_id_attr.__func__(type_cls)`) rather than calling `type_cls.resolve_id_attr()`. That is load-bearing: a Relay-shaped child of a Relay-shaped parent inherits the parent's installed framework default, which swallows `NodeIDAnnotationError` into the `"pk"` fallback and would let a composite-pk child slip the gate.

Rejected alternatives — the global-setting form, and an unconditional composite-pk rejection — are in the [rationale companion][spec-015-rationale].
### Decision 3: Relay resolver injection
After interface injection, and before `strawberry.type(cls, ...)`, the finalizer runs:

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
        existing_func = getattr(existing, "__func__", None)
        node_func = getattr(node_default, "__func__", None)
        if existing is None or (
            existing_func is not None and existing_func is node_func
        ):
            setattr(cls, attr, classmethod(default_impl))
```

The identity test is a direct copy of strawberry-django's check at `strawberry_django/type.py::_process_type #"existing_resolver.__func__ is getattr(relay.Node, attr).__func__"`; the added `existing_func is not None` clause is ours, so an existing attribute with no `__func__` at all (a plain function a consumer assigned) counts as an override rather than matching a `None` default. The `__func__` identity test is required rather than a `cls.__dict__[attr]` membership test: when the consumer does **not** override, `getattr(cls, attr)` resolves through the MRO to `relay.Node`'s default, which is exactly the case we want to overwrite. A `cls.__dict__` check would never see that and would skip injection forever.

Injection is preceded by one Phase-2.5 step, `_stamp_relay_id_attr`, which resolves the type's Relay id attribute **once** and pins it on the class's own `__dict__`. It seeds `_id_attr = None` on the class first so Strawberry's inherited-cache read cannot answer with a parent's value, then calls Strawberry's scan and records either the declared `relay.NodeID[...]` attribute name or `"pk"`. Without the stamp the `"pk"` fallback re-runs a full MRO annotation scan on every `resolve_id` call — once per row of every result set — because upstream caches only on success.

The four default implementations live in a new module `django_strawberry_framework/types/relay.py`. Their shapes port strawberry-django's `relay/utils.py`; we do not import strawberry-django at runtime, we copy the patterns and cite the source at the implementation site.

- `_resolve_id_attr_default(cls) -> str` — read the `_stamp_relay_id_attr` slot from `cls.__dict__`; when absent (a subclass defined after finalization, or a direct unit call) ask Strawberry's scan directly via `relay.Node.resolve_id_attr.__func__(cls)` and map `NodeIDAnnotationError` to `"pk"`. Behavioral port of `strawberry_django/relay/utils.py::resolve_model_id_attr`. **Not** `super(cls, cls).resolve_id_attr()`: with `cls` bound at runtime, a Relay-shaped `DjangoType` subclassing another Relay-shaped `DjangoType` inherits the parent's installed copy of this default and the MRO walk lands back on it re-bound to the child — infinite recursion. No `DjangoTypeDefinition.id_attr` slot is added; Strawberry owns the detection and the stamp owns the caching.
- `_resolve_id_default(cls, root, *, info) -> str` — `id_attr = cls.resolve_id_attr(); if id_attr == "pk": id_attr = root.__class__._meta.pk.attname; try: return str(root.__dict__[id_attr]) except KeyError: return str(getattr(root, id_attr))`. Port of `strawberry_django/relay/utils.py::resolve_model_id`. The `"pk"` → concrete `attname` coercion is load-bearing: Django stores the pk under its column attname (`"id"`, `"uuid_id"`, …), never under the literal `"pk"`, so without it `root.__dict__["pk"]` always misses and Decision 7's "no avoidable lazy loads on `resolve_id`" invariant is violated. The key is read off `root.__class__`, not off the definition's model, so a proxy-model row is not mis-keyed.
- `_resolve_node_default(cls, node_id, *, info, required=False)` — seed the queryset with `initial_queryset(cls)` (the model's `_default_manager.all()`, resolved through the definition), apply the type's visibility through `apply_type_visibility_sync`, filter on the resolved id attribute, and return `qs.get()` when `required` else `qs.first()`. Port of `strawberry_django/relay/utils.py::resolve_model_node`. The optimizer-extension consultation step upstream performs (`ext = optimizer extension on info.context; if ext: qs = ext.optimize(qs, info=info)`) is **deliberately not wired**: Decision 7's list-path invariants are exercised through the root-gated `DjangoOptimizerExtension`, and node-lookup optimizer cooperation becomes load-bearing only when a node field ships. The seam stays open at the same site.
- `_resolve_nodes_default(cls, *, info, node_ids=None, required=False)` — same seed and visibility step, optionally filtering on `node_ids` via `id_attr__in`. `node_ids=None` returns the visibility-filtered queryset; a supplied sequence returns a list whose indexes correspond 1:1 with the input, materialized once so a one-shot iterable survives both the `IN` filter and the ordering pass. `required=False` yields `None` for a missing id; `required=True` raises the model's `DoesNotExist`, homogeneous with `_resolve_node_default`'s `qs.get()` so consumers write a single `except Model.DoesNotExist:` clause. Port of `strawberry_django/relay/utils.py::resolve_model_nodes`, its `map_results` ordering pass included. The same optimizer deferral applies.

`info` is keyword-only on all three resolvers that take it. Strawberry's Relay machinery calls `cls.resolve_node(node_id, info=info, required=...)`, so a positional `info` slot raises `TypeError: got multiple values for argument 'info'`.

Neither node default calls `cls.get_queryset` directly. Both route it through the shared visibility boundary in `django_strawberry_framework/utils/querysets.py`, which treats the hook's return as untrusted query state, awaits an async hook on the async path, and rejects one on the sync path (Decision 9).

The rejected alternatives, the upstream borrow justifications, and the recursion the `super()` spelling would have shipped are in the [rationale companion][spec-015-rationale].
### Decision 4: validation
`_validate_meta` (in `django_strawberry_framework/types/base.py::_validate_meta`) gains an interface validator that runs when `interfaces` is declared. Reference: the existing `_format_unknown_fields_error` helper at `django_strawberry_framework/types/base.py::_format_unknown_fields_error` is the canonical error-shape pattern; new errors here reuse the same `model.Meta.<key> ...` shape so consumer-visible failures stay consistent.

Validation rules:

- `interfaces` may be a tuple/list of interface classes or a single real Strawberry interface class. Tuple/list values are normalized to a tuple as-is; a single interface class such as `interfaces = relay.Node` (or the common missing-comma spelling `interfaces = (relay.Node)`) is normalized to `(relay.Node,)`. Strings, sets, generators, and other invalid non-sequence values raise `ConfigurationError`.
- An empty tuple is the same as not declaring the key at all (no-op, identical to `0.0.4` behavior bit-for-bit).
- Each entry must satisfy `hasattr(entry, "__strawberry_definition__") and entry.__strawberry_definition__.is_interface`. `relay.Node` already satisfies this — it is decorated with `@interface(...)` upstream — so no special-casing is required.
- String entries (e.g. `interfaces = ("Node",)`) raise `ConfigurationError`. Lazy/forward-reference interface lookup is out of scope for `0.0.5`.
- The six `strawberry.relay` non-interface helpers — `GlobalID`, `NodeID`, `Connection`, `ListConnection`, `Edge`, `PageInfo` — are rejected by name, with a message saying what each one actually is. The check matches by object identity and runs **before** the non-class branch, because `relay.NodeID` is a `typing.Annotated` alias rather than a class and would otherwise die unnamed in the generic rejection.
- Passing `DjangoType` itself (or another consumer `DjangoType` subclass) as an interface entry raises `ConfigurationError`. `DjangoType` is not a Strawberry interface.
- Duplicates raise `ConfigurationError`. The `__bases__` injection step can no-op idempotently, but tolerating duplicates here would let typos hide.
- A class that already inherits from one of the listed interfaces directly (e.g. consumer wrote `class Foo(DjangoType, relay.Node): class Meta: interfaces = (relay.Node,)`) is accepted — the base-injection step is then a structural no-op (`relay.Node in cls.__bases__` is already true).
- The composite-pk constraint from Decision 2 is **not** enforced inside `_validate_meta`. It is enforced once during Phase 2.5 (Decision 5), which runs after `cls.__bases__` is resolved and therefore catches both `Meta.interfaces = (relay.Node,)` consumers and consumers who write `class Foo(DjangoType, relay.Node)` directly. Centralizing the check there avoids duplicating the `model._meta.pk` inspection.

Composition with [`Meta.optimizer_hints`][glossary-metaoptimizer-hints]: the two keys are independent. `optimizer_hints` continues to apply unchanged. Suppressing the synthesized primary-key annotation on a Relay-shaped type has no effect on the optimizer field map (`FieldMeta` is keyed off Django's field selection, not Strawberry's annotations) — the pk is still selected as the connector column.
### Decision 5: lifecycle and idempotency
- Calling `finalize_django_types()` twice is still a no-op via the existing short-circuit at `django_strawberry_framework/types/finalizer.py::finalize_django_types #"if registry.is_finalized():"`.
- `registry.clear()` (`django_strawberry_framework/registry.py::TypeRegistry.clear`) already drops `_definitions`, `_pending`, `_finalized`, `_types`, `_models`, and `_enums`. Test isolation continues to require **fresh class objects** after `clear()`, exactly as documented in `docs/GLOSSARY.md #"Declaring a new concrete"`. No new tracking state is added on `DjangoTypeDefinition` for the Relay slice — the source of truth is `cls.__bases__` itself for interface injection and the `relay.Node` MRO check for resolver injection.
- New finalizer step ordering relative to the existing three-loop structure at `django_strawberry_framework/types/finalizer.py::finalize_django_types`:
  - Phase 1 unchanged (`django_strawberry_framework/types/finalizer.py::finalize_django_types #"for pending in registry.iter_pending_relations():"`): resolve pending relations.
  - Phase 2 unchanged (`django_strawberry_framework/types/finalizer.py::finalize_django_types #"_attach_relation_resolvers"`): `_attach_relation_resolvers` for every non-finalized definition.
  - **NEW** Phase 2.5: for each non-finalized definition, if `definition.interfaces` is non-empty, inject those interfaces into `cls.__bases__` (only those not already present in `cls.__mro__`); if the resolved class is Relay-Node-shaped, run the composite-pk check (Decision 2) and inject the four `resolve_*` defaults using the `__func__` identity test from Decision 3. Gating the Relay half on the resolved MRO rather than on the `Meta` tuple is what makes a directly-inheriting `class Foo(DjangoType, relay.Node)` reach the same wiring. Later cards add further steps to this same window (the GlobalID type-name resolver, `Meta.cursor_field` validation); they run after this slice's and change nothing here.
  - Phase 3 unchanged (`django_strawberry_framework/types/finalizer.py::finalize_django_types #"strawberry.type(type_cls, name=definition.name"`): `strawberry.type(cls, name=definition.name, description=definition.description)`; mark `definition.finalized = True`.

The primary-key annotation suppression in Decision 2 happens earlier — during `__init_subclass__` collection (`django_strawberry_framework/types/base.py::DjangoType.__init_subclass__`, inside `_build_annotations`) — because that is where the synthesized annotation map is assembled. The split between suppression (collection-time) and base injection (finalization-time) is deliberate and constrains the implementation: collection is where `cls.__annotations__` is written, so keeping suppression beside annotation synthesis keeps that data flow local; base injection has to wait for finalization because Phase 1 relation resolution still mutates `cls.__annotations__`, and a partially-finalized class must not also be a partially-interface-injected one.
### Decision 6: compatibility with the override contract
The `0.0.4` relation-field consumer-override contract (`DjangoTypeDefinition.consumer_annotated_relation_fields` and `consumer_assigned_relation_fields`, see `django_strawberry_framework/types/base.py::DjangoType.__init_subclass__` and `django_strawberry_framework/types/finalizer.py::finalize_django_types`) is preserved unchanged.

The new `Meta.interfaces` consumer-override contract is:

- Annotations and fields the interface itself declares (e.g. `Node._id`, which renders as the `id: GlobalID!` field) are owned by the interface. Consumers must not shadow them on the `DjangoType` subclass; doing so will produce a Strawberry-level error at decoration time, which the spec leaves to Strawberry rather than re-implementing.
- `resolve_id_attr` / `resolve_id` / `resolve_node` / `resolve_nodes` declared anywhere in the consumer's MRO above `relay.Node` take precedence over framework defaults via the `__func__` identity test, matching strawberry-django's semantics so migration from that package does not surprise consumers.
- Setting `interfaces = ()` or omitting the key keeps `0.0.4` behavior bit-for-bit: Decision 4's validation makes the empty/absent case a true no-op, the primary-key suppression step included.
- `is_type_of` injection (Decision-1 borrow) is added unconditionally for every `DjangoType`, not only Relay-declared ones. If the consumer declares their own `is_type_of` we do not overwrite it, matching `strawberry_django/type.py::_process_type #"is_type_of"`; the discriminator here is `cls.__dict__` membership, not the `__func__` test, because there is no inherited framework default to distinguish.

Why unconditional injection was chosen over Relay-only injection is in the [rationale companion][spec-015-rationale].
### Decision 7: optimizer and projection invariants
Relay node support must not regress shipped optimizer behavior. Required invariants:

- **Primary-key projection.** When GraphQL selects Relay `id` on a Relay-declared `DjangoType`, the optimizer's [`only()`][glossary-only-projection] projection must include the concrete primary-key attname. Reference: `django_strawberry_framework/optimizer/walker.py::_walk_selections` (where scalar selections are appended to `only_fields`), and `django_strawberry_framework/optimizer/walker.py::_plan_select_relation` (relation select planning). Strawberry resolves Relay `id` via `_resolve_id_default`, which reads `root.__dict__[attname]` first, so the only way that path produces no extra query is if the optimizer kept `attname` in `only()`.
- **Connector-column preservation.** Existing connector-column behavior (`docs/GLOSSARY.md #"Connector columns required for"`) for `select_related`, reverse FK, FK/OneToOne, and M2M attachment paths is unchanged. The Relay slice does not modify the walker.
- **[FK-id elision][glossary-fk-id-elision] scoping.** B2 FK-id elision (`django_strawberry_framework/types/resolvers.py::_build_fk_id_stub`, `django_strawberry_framework/optimizer/walker.py::_can_elide_fk_id`) is scoped to forward relation selections. The Relay slice does not introduce a code path where `GlobalID` is fed into FK-id elision logic: GlobalID handling lives entirely in the Relay resolvers (`django_strawberry_framework/types/relay.py`) and the walker continues to see the Django primary-key column it always saw.
- **No avoidable lazy loads on `resolve_id`.** `_resolve_id_default` reads from `root.__dict__` first; if the optimizer kept the pk in `only()`, the `__dict__` cache hit avoids any lazy load. That cache-then-`getattr` order is the reason the resolver is written the way it is, and reversing it silently costs a query per row.
- **Relation traversal across Relay node targets.** Declaring a relation's target `DjangoType` Relay-shaped does not change how that relation is planned. The optimizer reads target metadata from `DjangoTypeDefinition`, not from the Strawberry `__strawberry_definition__`, so suppressing the synthesized scalar primary-key annotation is invisible to it; planning for a Relay-declared target is decided by exactly the rules that decide it for any other target, the `get_queryset` → `Prefetch` downgrade included. This slice does not modify the walker.

Implementation note: `DjangoTypeDefinition.field_map` (`django_strawberry_framework/types/definition.py::DjangoTypeDefinition #"field_map: dict[str, FieldMeta]"`) keeps every selected Django field including the primary key, regardless of whether the Strawberry annotation was suppressed — the field map is the optimizer's source of truth and suppression happens later in the data flow, in `_build_annotations`.
### Decision 8: registry implications and one-type-per-model
[`Meta.primary`][glossary-metaprimary] is out of scope for `0.0.5`.

Consequences for `0.0.5`:

- Node lookup remains one `DjangoType` per Django model (`django_strawberry_framework/registry.py::TypeRegistry.register`). `_resolve_node_default` and `_resolve_nodes_default` look up the model through the type's `DjangoTypeDefinition`; with one type per model that resolution is unambiguous.
- Multiple `DjangoType`s per model still raise `ConfigurationError` (`django_strawberry_framework/registry.py::TypeRegistry.register`). The Relay slice does not change that contract.
- Which of several types per model owns Relay node lookup is left to the slice that lands `Meta.primary`; deferring it keeps `0.0.5` tight. The [rationale companion][spec-015-rationale] records the answer that slice and its successors gave.
- `registry.clear()` continues to reset definitions and pending relations only; tests that need a clean lifecycle still create fresh class objects after clearing.
### Decision 9: async resolver support
The four `resolve_*` defaults must work in both sync and async resolver contexts because Strawberry permits either at every field, and a consumer's `DjangoType.get_queryset` may itself be sync or async. Without explicit async coverage, the Relay borrow ports only half of strawberry-django's resolver shape and forces every async consumer to re-implement the four defaults.

- `_resolve_id_attr_default(cls)` and `_resolve_id_default(cls, root, *, info)` are sync. They touch no database; they read class state, `root.__dict__`, and `getattr`. Promoting them to async would force `await` plumbing through every Relay node serialization for no benefit.
- `_resolve_node_default` and `_resolve_nodes_default` execute querysets and ship both paths. Context detection is `strawberry.utils.inspect.in_async_context()`; on the async branch each returns a coroutine that awaits the visibility hook, applies the id filter, and materializes through Django's native async ORM — `aget` / `afirst` for the singular path, `async for` for the plural one. No path wraps a sync call in `sync_to_async`.
- The seam between the two colors is the shared visibility boundary, not the resolvers: the async branch awaits `apply_type_visibility_async`, so a consumer's `async def get_queryset` is honored, and the sync branch calls `apply_type_visibility_sync`, which **rejects** a coroutine return with `SyncMisuseError` rather than letting it surface as `AttributeError: 'coroutine' object has no attribute 'filter'`. `SyncMisuseError` multiple-inherits `ConfigurationError` and `RuntimeError` so a consumer catching either base class still matches, and the unawaited coroutine is closed before the raise.
- Optimizer cooperation is not part of this contract on either color: per Decision 3 the node defaults consult no optimizer extension. The root-gated optimizer's own async support is unaffected because these resolvers do not call into it.
- A consumer-authored `async def resolve_node(...)` overrides the framework default per Decision 6's `__func__` identity test, exactly the same way a sync override does. The override discriminator does not care about the function's awaitability.
## Internal helper surface
The Relay machinery lives in a new module, `django_strawberry_framework/types/relay.py`. Its surface is internal — none of these helpers are re-exported from the top-level package, and the public surface (item 11 of the Definition of done) is unchanged.

```python path=null start=null
def apply_interfaces(type_cls: type, definition: DjangoTypeDefinition) -> None:
    """Inject ``definition.interfaces`` into ``type_cls.__bases__`` (Phase 2.5)."""


def implements_relay_node(type_cls: type) -> bool:
    """Return whether ``type_cls`` is a subclass of ``strawberry.relay.Node``."""


def install_relay_node_resolvers(type_cls: type) -> None:
    """Stamp the id attribute, then inject the four ``resolve_*`` defaults."""


def install_is_type_of(type_cls: type) -> None:
    """Borrow strawberry-django's ``is_type_of`` virtual subclass behavior."""


def _check_composite_pk_for_relay_node(type_cls: type) -> None:
    """Raise ``ConfigurationError`` for a composite pk with no ``NodeID`` escape."""


def _stamp_relay_id_attr(type_cls: type) -> None:
    """Resolve the Relay id attribute once and pin it on the class (Phase 2.5)."""


def _resolve_id_attr_default(cls: type) -> str:
    """Default ``Node.resolve_id_attr``; reads the stamp, falls back to ``\"pk\"``."""


def _resolve_id_default(cls: type, root: models.Model, *, info: Any) -> str:
    """Default ``Node.resolve_id`` with the ``__dict__`` cache check."""


def _resolve_node_default(
    cls: type,
    node_id: Any,
    *,
    info: Any,
    required: bool = False,
) -> Any:
    """Default ``Node.resolve_node``; visibility-aware, sync and async."""


def _resolve_nodes_default(
    cls: type,
    *,
    info: Any,
    node_ids: Any = None,
    required: bool = False,
) -> Any:
    """Default ``Node.resolve_nodes``; order-preserving and missing-aware."""
```

`info` is keyword-only on every resolver that takes it, and `node_id` is positional on `_resolve_node_default`, because that is the shape Strawberry's Relay machinery calls (Decision 3). The signatures attached to the class must match Strawberry's `relay.Node` expectations as they exist in the `strawberry-graphql>=0.316.0` lower bound declared in `pyproject.toml #"strawberry-graphql>=0.316.0"`; the Django floor is `Django>=5.2.16`.
## Implementation plan
The slice is small enough to implement as a single PR but easier to review as five commits. Each commit cites the exact symbol touched.
1. **Validation + storage**
   - `django_strawberry_framework/types/base.py #"DEFERRED_META_KEYS: frozenset[str]"`: keep `"interfaces"` in `DEFERRED_META_KEYS` for now (promotion is the last step).
   - `django_strawberry_framework/types/base.py::_validate_meta`: add the interface normalization / duplicate / Strawberry-interface check from Decision 4, including support for a single real interface class (`interfaces = relay.Node` or `interfaces = (relay.Node)`), string-entry rejection, and `DjangoType` self-reference rejection. The composite-pk check is **not** done here — it lives in Phase 2.5 (Slice 4) so a single check site catches both `Meta.interfaces = (relay.Node,)` consumers and consumers who write `class Foo(DjangoType, relay.Node)` directly.
   - `django_strawberry_framework/types/base.py::DjangoType.__init_subclass__ #"definition = DjangoTypeDefinition("` (the `DjangoTypeDefinition(...)` construction): pass the normalized interfaces tuple through to the existing `interfaces` slot at `django_strawberry_framework/types/definition.py::DjangoTypeDefinition #"interfaces: tuple[type, ...] = ()"`.
   No new slot on `DjangoTypeDefinition`: Decision 3 relies on Strawberry's `NodeID` annotation rather than a per-type `id_attr` Meta key, so the slot would be dead state.

2. **`is_type_of` injection**
   - New helper in `django_strawberry_framework/types/relay.py` invoked from the existing `__init_subclass__` flow at `django_strawberry_framework/types/base.py::DjangoType.__init_subclass__`, applied to every `DjangoType` subclass (Relay or not, per Decision 6) that does not declare its own `is_type_of`. Direct port of `strawberry_django/type.py::_process_type #"is_type_of"`.

3. **Primary-key annotation suppression**
   - `django_strawberry_framework/types/base.py::_build_annotations`: when the class is Relay-shaped per Decision 2's predicate, drop the primary-key field's name from the synthesized annotations dict before assignment. The selected-field list itself is unchanged so `FieldMeta` and the optimizer still see the pk as a connector column.
   - Preserve the primary-key field in metadata for optimizer/projection use (Decision 7).

4. **Interface base-class injection + Relay resolver defaults**
   - New module `django_strawberry_framework/types/relay.py` containing `_resolve_id_attr_default`, `_resolve_id_default`, `_resolve_node_default`, `_resolve_nodes_default`, `apply_interfaces`, `implements_relay_node`, `install_relay_node_resolvers`, `install_is_type_of`, `_check_composite_pk_for_relay_node`, and `_stamp_relay_id_attr` per Decision 3 and the helper surface above.
   - `_resolve_node_default` and `_resolve_nodes_default` ship sync and async paths per Decision 9; the two ID-shape defaults stay sync.
   - `django_strawberry_framework/types/finalizer.py::finalize_django_types`: insert the new Phase 2.5 step from Decision 5 between the existing `_attach_relation_resolvers` loop and the `strawberry.type(...)` loop. The new step uses `registry.iter_definitions()` exactly the same way the existing loops do (`django_strawberry_framework/types/finalizer.py::finalize_django_types #"_attach_relation_resolvers"` and `django_strawberry_framework/types/finalizer.py::finalize_django_types #"strawberry.type(type_cls, name=definition.name"`), so the change is structural rather than algorithmic. The composite-pk check fires here when `relay.Node` is in the resolved bases; it surfaces a `ConfigurationError` that names the model.
   - Add optimizer/projection tests for Relay `id` so Decision 7 is verified before promotion.

5. **Promotion + docs + version**
   - `django_strawberry_framework/types/base.py #"DEFERRED_META_KEYS: frozenset[str]"` and `django_strawberry_framework/types/base.py #"ALLOWED_META_KEYS: frozenset[str]"`: move `"interfaces"` from `DEFERRED_META_KEYS` to `ALLOWED_META_KEYS`. The promotion is last because a deferred key may only be promoted once every behavior it enables is applied end-to-end (Goal 5).
   - Doc updates as listed in the "Doc updates" section.
   - Version bump in `pyproject.toml #"version ="` and `django_strawberry_framework/__init__.py #"__version__ ="`; update `tests/base/test_init.py` assertion; regenerate `uv.lock` via `uv lock`.

The five commits can be squashed into a single PR; the per-commit breakdown exists for review legibility.
## Edge cases and constraints
- **Composite primary keys (Django 5.2+).** A Relay-shaped type over a composite-pk model raises `ConfigurationError` at finalization unless it declares an explicit `id: relay.NodeID[...]` annotation, which the gate accepts (Decision 2). The error names the model and points to that annotation or to removing `relay.Node` from `Meta.interfaces`. Deterministic composite-key encoding is future work, tracked for once Django stabilizes the composite-pk API.
- **Models without an `AutoField`/`BigAutoField`/`SmallAutoField` primary key.** The default `_resolve_id_attr_default` returns `"pk"`; Django resolves that to the actual primary-key attname (`UUIDField`, custom-typed pk, etc.). No special-casing is required as long as the column has a single-column pk.
- **Nullable primary keys.** Not supported by Django for normal models; out of scope.
- **Inherited interfaces via parent `DjangoType`.** A subclass of a Relay-declared `DjangoType` inherits `relay.Node` through `__bases__`. The validation rule in Decision 4 accepts this case as a no-op when the subclass also declares `Meta.interfaces = (relay.Node,)`.
- **Schema reload during tests.** `registry.clear()` plus fresh class definitions remains the only supported reset path. Any HTTP-level test that imports a Relay-declared `DjangoType` must follow the reload pattern documented in `docs/TREE.md` "What each folder holds" for `examples/fakeshop/test_query/`.
## Test plan
Tests are placed by the tree rules in `docs/TREE.md` and `AGENTS.md`: package-internal behavior in `tests/`, and anything reachable from a real GraphQL query in the live `examples/fakeshop/test_query/` tier. Test-tree placement is mandatory; the spec's pinning is a deliberate copy of that rule. Coverage: the slice must keep the package coverage gate at 100% (`fail_under = 100`).
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

- `test_relay_node_strips_django_id_annotation` — on a Relay-shaped type the synthesized primary-key annotation is absent from the built annotation map (the Relay-supplied `id: GlobalID!` field is owned by the interface).
- `test_non_relay_type_keeps_id_int` — control test: a `DjangoType` without `relay.Node` still produces `id: int!` (no regression vs `0.0.4`).
- `test_relay_node_injects_default_resolvers` — after finalization the type has classmethods `resolve_id_attr`, `resolve_id`, `resolve_node`, `resolve_nodes`.
- `test_resolve_id_attr_falls_back_to_pk` — with no `relay.NodeID[...]` annotation the default returns the literal `"pk"` (the coercion to the concrete attname happens one layer later, in `resolve_id`).
- `test_resolve_id_uses_dict_cache` — when the row is already loaded into `root.__dict__`, `resolve_id` returns the str without an extra query.
- `test_resolve_id_falls_back_to_getattr` — when the pk is not in `root.__dict__`, `resolve_id` reads via `getattr` and coerces to `str`.
- `test_resolve_node_applies_get_queryset` — a custom `get_queryset` filtering `is_private=False` is applied during node lookup; rows that the filter excludes return `None` (or raise when `required=True`).
- `test_resolve_nodes_preserves_order_and_missing` — passing `node_ids=[a, missing, b]` returns `[obj_a, None, obj_b]` when `required=False`.
- `test_resolve_nodes_required_raises_for_missing` — `required=True` raises the model's `DoesNotExist` for a missing id, the same exception the singular path raises.
- `test_resolve_node_async_context` — when invoked from an async resolver, `_resolve_node_default` resolves through Django's async ORM API (`afirst`, or `aget` under `required=True`) and returns the matching row.
- `test_resolve_nodes_async_context` — same for `_resolve_nodes_default`, including the order-preserving / missing-id behavior.
- `test_consumer_async_resolve_node_wins` — a consumer-authored `async def resolve_node(...)` is preserved by the `__func__` identity test exactly like a sync override.
- `test_consumer_resolve_id_attr_wins` — declaring `resolve_id_attr` on the subclass keeps the consumer version.
- `test_consumer_resolve_id_wins` — same for `resolve_id`.
- `test_consumer_resolve_node_wins` — same for `resolve_node`.
- `test_consumer_resolve_nodes_wins` — same for `resolve_nodes`.
- `test_node_id_annotation_overrides_default_id_attr` — annotating a non-pk column as `<column>: relay.NodeID[str]` wires Relay to it without overriding any classmethod.
- `test_non_relay_interface_works` — declaring a plain `@strawberry.interface` works and skips the Relay-only injection.
- `test_is_type_of_injected_for_all_djangotypes` — `is_type_of` is present on Relay and non-Relay `DjangoType`s alike, and a consumer-declared `is_type_of` is preserved.
### Schema-construction coverage (live)
Two assertions, both earned over live `/graphql/` HTTP against the `library` app per the repository's live-first placement rule:

- `examples/fakeshop/test_query/test_library_api.py::test_relay_genre_type_emits_node_interface_and_global_id_live` — introspection shows the `Node` interface on the Relay-declared `GenreType`, and its `id` renders as the GlobalID scalar.
- `examples/fakeshop/test_query/test_library_api.py::test_mixed_relay_and_non_relay_no_interface_bleed_live` — a schema mixing Relay `GenreType` and non-Relay `ShelfType` introspects cleanly: `Node` lands on the Relay type only, and the plain type's `id` is not the GlobalID scalar.
### `tests/optimizer/test_relay_id_projection.py`
These pin Decision 7's projection invariants:

- `test_relay_id_only_projection_includes_pk_attname` — selecting `{ allCategories { id } }` on a Relay-declared type produces an `only()` projection that includes the model's concrete pk attname.
- `test_relay_id_does_not_trigger_lazy_load` — selecting `{ allCategories { id name } }` produces zero N+1 warnings under the strictness sentinel.
- `test_relay_resolve_id_uses_loaded_pk` — `resolve_id` uses the loaded primary-key value without triggering an avoidable lazy load when the optimizer already selected it.

Decision 7's relation-traversal invariant is pinned live instead, across the four Relay-declared `products` types: `examples/fakeshop/test_query/test_products_api.py::test_products_optimizer_selects_nested_forward_fk_depth_2_over_http` (depth-2 forward FK) and `::test_products_optimizer_prefetches_nested_reverse_fk_depth_2_over_http` (depth-2 reverse FK) each pin a deterministic query count for a nested traversal whose targets are Relay-declared.
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
  - Move this card to Done as `DONE-015-0.0.5`, describing the shipped scope, the borrowed patterns, and the test files.
  - Advance the recommended hybrid sequence past Relay; the sidecar line ([`FieldSet`][glossary-fieldset] and filters) is what follows it.

- `CHANGELOG.md`
  - `[0.0.5]` `### Added`: Relay Node interface support, `Meta.interfaces` accepted for any Strawberry interface, default `resolve_id_attr` / `resolve_id` / `resolve_node` / `resolve_nodes` for Relay-declared types, automatic id suppression when `relay.Node` is declared, `is_type_of` injection for all `DjangoType`s.
  - `### Changed`: `Meta.interfaces` promoted from `DEFERRED_META_KEYS` to `ALLOWED_META_KEYS`.
  - `### Fixed` / `### Removed`: as needed by the implementation.
  - Version bump.
## Out of scope (owned elsewhere)
Each item below is outside the `0.0.5` slice and owned by its own card. `docs/GLOSSARY.md` is the durable catalog for whether one has since shipped; `KANBAN.md` carries the sequencing.

- `DjangoConnectionField` and `DjangoNodeField`.
- Cascade permissions and field-level permissions.
- [Connection-aware optimizer planning][glossary-connection-aware-optimizer-planning].
- `Meta.primary` / multiple types per model.
- Stable consumer override semantics for scalar fields.
- Deferred scalar conversions (`BigIntegerField`, `JSONField`, etc.).
- Stable [choice enum][glossary-choice-enum-generation] naming.
- Layered manual override-test policy.
- Migration and adoption guides.
- Composite-primary-key Relay node encoding.
## Definition of done
The `0.0.5` slice is complete when all of the following are true:

1. `"interfaces"` is in `ALLOWED_META_KEYS` (`django_strawberry_framework/types/base.py #"ALLOWED_META_KEYS: frozenset[str]"`), validated by `_validate_meta` per Decision 4, and stored on the existing `DjangoTypeDefinition.interfaces` slot at `django_strawberry_framework/types/definition.py::DjangoTypeDefinition #"interfaces: tuple[type, ...] = ()"`. No new fields are added to `DjangoTypeDefinition`.
2. `finalize_django_types()` (`django_strawberry_framework/types/finalizer.py::finalize_django_types`) injects declared interfaces into `cls.__bases__` and runs the `relay.Node` resolver injection (Decision 3) before the existing `strawberry.type(cls, ...)` Phase 3 loop. `0.0.4` behavior is preserved bit-for-bit for types that omit `Meta.interfaces`, verified by the existing test suite passing unchanged.
3. Declaring `interfaces = (relay.Node,)` produces a working Relay-Node GraphQL type with `id: GlobalID!`, the four injected `resolve_*` methods, the `is_type_of` virtual subclass behavior, and consumer override support per Decision 6. The single-interface forms `interfaces = relay.Node` and `interfaces = (relay.Node)` normalize to the same stored tuple.
4. A Relay-shaped type over a composite-pk model raises `ConfigurationError` at finalization with a message that names the model and proposes a remediation path, unless the type declares an explicit `id: relay.NodeID[...]` annotation — the first remediation the message proposes, which the gate honors (Decision 2).
5. Optimizer invariants in Decision 7 hold: `only()` includes the pk attname when Relay `id` is selected, `resolve_id` does not trigger an avoidable lazy load, and a target type's Relay declaration does not change how relations to it are planned.
6. Tests in `tests/types/test_relay_interfaces.py` (new), plus the extensions to `tests/optimizer/test_relay_id_projection.py`, `tests/test_registry.py`, `examples/fakeshop/test_query/test_library_api.py`, and `examples/fakeshop/test_query/test_products_api.py` listed in the Test plan all pass.
7. Package coverage stays at 100% (`pyproject.toml [tool.coverage.report] fail_under = 100`).
8. `docs/GLOSSARY.md`, `docs/README.md`, `TODAY.md`, `KANBAN.md`, and `CHANGELOG.md` reflect the shipped state per the "Doc updates" section.
9. Version bumped to `0.0.5` in `pyproject.toml #"version ="`, `django_strawberry_framework/__init__.py #"__version__ ="`, and the assertion in `tests/base/test_init.py`; `uv.lock` regenerated by running `uv lock`.
10. `KANBAN.md` carries this work as the Done card `DONE-015-0.0.5` describing the shipped scope, and the recommended hybrid sequence advances past Relay/`Meta.interfaces`.
11. No new public exports. The public surface stays `DjangoType`, `DjangoOptimizerExtension`, [`OptimizerHint`][glossary-optimizerhint], [`finalize_django_types`][glossary-finalize-django-types], `auto`, `__version__` (`django_strawberry_framework/__init__.py #"__all__ = ("`). `README.md #"The public names are stable"` is the promise this holds to; `0.0.5` only changes what `Meta.interfaces` enables, not the import surface.
12. `_resolve_node_default` and `_resolve_nodes_default` work in both sync and async resolver contexts per Decision 9. A consumer-authored `async def resolve_node(...)` is preserved by the override contract.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[glossary-apply-cascade-permissions]: ../GLOSSARY.md#apply_cascade_permissions
[glossary-choice-enum-generation]: ../GLOSSARY.md#choice-enum-generation
[glossary-configurationerror]: ../GLOSSARY.md#configurationerror
[glossary-connection-aware-optimizer-planning]: ../GLOSSARY.md#connection-aware-optimizer-planning
[glossary-djangoconnectionfield]: ../GLOSSARY.md#djangoconnectionfield
[glossary-djangonodefield]: ../GLOSSARY.md#djangonodefield
[glossary-djangooptimizerextension]: ../GLOSSARY.md#djangooptimizerextension
[glossary-djangotype]: ../GLOSSARY.md#djangotype
[glossary-fieldset]: ../GLOSSARY.md#fieldset
[glossary-finalize-django-types]: ../GLOSSARY.md#finalize_django_types
[glossary-fk-id-elision]: ../GLOSSARY.md#fk-id-elision
[glossary-metafields]: ../GLOSSARY.md#metafields
[glossary-metainterfaces]: ../GLOSSARY.md#metainterfaces
[glossary-metaoptimizer-hints]: ../GLOSSARY.md#metaoptimizer_hints
[glossary-metaprimary]: ../GLOSSARY.md#metaprimary
[glossary-only-projection]: ../GLOSSARY.md#only-projection
[glossary-optimizerhint]: ../GLOSSARY.md#optimizerhint
[glossary-public-exports]: ../GLOSSARY.md#public-exports
[glossary-relay-node-integration]: ../GLOSSARY.md#relay-node-integration

<!-- docs/SPECS/ -->
[spec-015-rationale]: appx/spec-015-relay_interfaces-0_0_5-rationale.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
