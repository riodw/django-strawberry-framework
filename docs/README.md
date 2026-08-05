# django-strawberry-framework

`django-strawberry-framework` is a DRF-shaped Django integration for Strawberry GraphQL. It lets Django teams build GraphQL APIs from Django models using the familiar `class Meta` style instead of a decorator-heavy surface.

For the project pitch, migration context, and the canonical documentation map, start from [`../README.md`][readme]. For the long-term destination, see [`../GOAL.md`][goal]. For the current capability snapshot, see [`../TODAY.md`][today]. For contributor / maintainer workflow (dev setup, format, test, build, publish), see [`../CONTRIBUTING.md`][contributing].

## Installation

```shell
# pip
pip install django-strawberry-framework
# uv
uv add django-strawberry-framework
```

## Quick start

```python
import strawberry
from django_strawberry_framework import DjangoOptimizerExtension, DjangoType, finalize_django_types, strawberry_config
from myapp.models import Category, Item


class CategoryType(DjangoType):
    class Meta:
        model = Category
        fields = ("id", "name", "items")


class ItemType(DjangoType):
    class Meta:
        model = Item
        fields = ("id", "name", "category")


@strawberry.type
class Query:
    @strawberry.field
    def all_items(self) -> list[ItemType]:
        return Item.objects.all()


finalize_django_types()

_optimizer = DjangoOptimizerExtension()
schema = strawberry.Schema(
    query=Query,
    config=strawberry_config(),
    extensions=[lambda: _optimizer],
)
```

The optimizer is a module-level singleton wrapped in a factory — that preserves the instance-bound [Plan cache][glossary-plan-cache] (Strawberry runs the callable per request and gets the same instance back) and emits no deprecation warning (the entry is a callable, not an instance).

That is the shipped surface: `class Meta` configures the type, `finalize_django_types()` resolves relations after all `DjangoType` modules are imported, and the optimizer extension turns nested selections into Django ORM `select_related`, `prefetch_related`, and `only` calls. Relation fields can point at target types declared earlier or later, as long as every target type is registered before finalization.

### Relay Node

Add `Meta.interfaces = (relay.Node,)` to declare a Relay-node-shaped type. The package wires `id: GlobalID!`, the four `resolve_*` defaults, and `is_type_of` injection without any decorators on the consumer class.

```python
import strawberry
from strawberry import relay
from django_strawberry_framework import DjangoType, finalize_django_types
from myapp.models import Category


class CategoryNode(DjangoType):
    class Meta:
        model = Category
        fields = ("id", "name")
        interfaces = (relay.Node,)


finalize_django_types()
```

See [`GLOSSARY.md`'s Relay Node integration subsection][glossary-relay-node-integration] for the resolver list, composite-pk constraint, and the `is_type_of` injection contract.

As of `0.0.9` the default Relay `GlobalID` payload is the Django model label (`app_label.modelname:<pk>`, e.g. `products.item:42`) rather than the GraphQL type name, so renaming a GraphQL type no longer invalidates cached IDs. `Meta.globalid_strategy` (per type) and `RELAY_GLOBALID_STRATEGY` (schema-wide) select `model` (default), `type` (the legacy GraphQL-type-name opt-out), `type+model` (transitional decode of old type-anchored IDs while emitting model-anchored ones), or a callable encoder. See [`GLOSSARY.md`'s `Meta.globalid_strategy` subsection][glossary-metaglobalid_strategy].

> **Multiple `DjangoType`s per model under the `model` default.** A model-label payload is shared by every `DjangoType` over that model and always decodes to the model's **primary** type (`Meta.primary`). So if two Relay-Node types over one model both use the `model` default, the secondary's `GlobalID`s refetch as the primary — its distinct identity and `get_queryset` scope collapse onto the primary's (under the pre-`0.0.9` type-name default they were distinct and self-routing). This is intentional (a model-anchored ID cannot distinguish secondaries), and finalization emits a warning naming the collapsing secondaries; give a secondary disjoint identity with `Meta.globalid_strategy = "type"`.

## What just happened?

- `class Meta` tells the package which Django model and fields become a Strawberry type.
- Returning a Django `QuerySet` from the root resolver gives the optimizer something it can shape.
- `DjangoOptimizerExtension()` walks the selected GraphQL fields once at the root and applies one ORM plan.
- Nested relations become joins, prefetches, projections, and strictness checks without replacing your queryset.

## Today and coming next

For the current capability snapshot — what the package can actually do in the example project right now — see [`../TODAY.md`][today]. For the per-feature glossary covering every shipped / planned / deferred capability (deep-linkable by anchor — `GLOSSARY.md#filterset`, `GLOSSARY.md#fk-id-elision`, …), see [`GLOSSARY.md`][glossary]. For the long-term destination and the migration-shape diffs against `graphene-django` and `strawberry-graphql-django`, see [`../GOAL.md`][goal].

A quick summary:

**Shipped today** (`0.0.14`):
- `DjangoType` — model-backed Strawberry types via `class Meta`
- scalar conversion (text, integer, boolean, float, decimal, date/time, UUID, binary, choice enums; file/image read output as the structured `DjangoFileType` / `DjangoImageType` objects — `name` / `size` / `url`, plus `width` / `height` on images, with the server's absolute filesystem path deliberately absent from the default and available per column through `Meta.filesystem_path_fields` — nullable by default, so an empty stored file resolves to `null` regardless of the column's `null` / `blank` — with the filter / scalar-input value staying `str`)
- specialized scalar conversions (`BigIntegerField` / `PositiveBigIntegerField` → `BigInt`, `JSONField` → `JSON`, PostgreSQL `ArrayField` → `list[T]`, PostgreSQL `HStoreField` → `JSON`)
- relation conversion (forward / reverse FK, forward / reverse OneToOne, forward / reverse M2M)
- `Meta.interfaces = (relay.Node,)` for Relay-node-shaped types with `id: GlobalID!`
- generated relation resolvers, with annotation-only and `strawberry.field` consumer overrides preserved
- definition-order-independent relation finalization via `finalize_django_types()`
- `get_queryset` visibility hook (cooperates with the optimizer via `Prefetch` downgrade). As of the visibility-boundary hardening on `main`, every framework-owned invocation of the hook runs through one shared hardened boundary (`django_strawberry_framework/utils/querysets.py::apply_type_visibility_sync` / `apply_type_visibility_async`) built on a **sealed execution queryset** contract: the hook or source object is treated as *untrusted query state*, never as a trusted executable object. The boundary validates the extracted SQL state — the registered-type concrete model (proxy siblings compose, MTI children do not), the actual base table recomputed from the first alias of the initialized `Query.alias_map` (never the poisonable `base_table` cached property, which `Query.clone` itself discards and recomputes) including every combined-query (`union()`/`intersection()`/`difference()`) branch rather than the mutable `QuerySet.model` / `Query.model`, the database alias, and (on read surfaces) the projection shape — and then rebuilds a framework-owned plain `django.db.models.QuerySet` from that validated state. Filters, annotations, joins, ordering, database routing, query hints, and (where the surface permits) `.values()` / `.values_list()` projections are preserved; every `prefetch_related` entry is rebuilt as an exact `django.db.models.Prefetch` (including the no-queryset case, so a consumer `Prefetch` subclass cannot keep an executable `get_current_querysets` override) and only an exact-`str` lookup passes through; a `Prefetch` carrying a consumer queryset is itself recursively sealed against the outer effective alias (a child pinned to a divergent alias fails closed, an unrouted child inherits the outer alias, and — when the parent itself is unrouted so the effective alias is unresolved — an explicitly routed child also fails closed, so a single resolution never schedules a parent and its related rows across two database connections), and an unsealable child fails the whole seal closed; the consumer object's executable behavior is never dispatched — and because `sql.Query.clone` is itself not a no-dispatch boundary (its body calls `where.clone()`, the containers' `.copy()`, and, at compile time, `as_sql` on the graph), the seal proves the *entire* query graph trusted before it clones: a structural check rejects any query instance that shadows a callable `sql.Query` method in its `__dict__` (a replaced `chain` / `clone` would otherwise ride through `sql.Query.clone`'s shallow `__dict__` copy and dispatch on the first post-seal transform); every container the clone copies must be an exact builtin `dict` / `set` (a subclass `.copy()` would otherwise dispatch mid-clone) and `combined_queries` must be an exact `tuple` (a `tuple` subclass with a stateful `__iter__` could otherwise yield the registered model's branches during validation and a foreign model's branches during the clone / compile); and a complete, recursive, identity-memoized walk proves every compiler-reachable node — the `where` / `having` trees **and their leaf operands**, annotations including nested `Func` / `Case` / `Subquery` operands, `order_by` / `group_by` / `distinct` / `select` sequences, `alias_map` joins (and any join's `filtered_relation` resolved condition), each expression's SQL-template metadata (`arg_joiner` / `template` / `function` / `connector`, which the compiler interpolates straight into the emitted SQL), the `extra_order_by` / `extra_tables` raw-SQL sequences, and `select_related` — is an exact genuine Django type (proven by object identity against `sys.modules`, read through `type.__getattribute__` so a consumer metaclass cannot run during the provenance check, never the spoofable `__module__` string) with no instance-`__dict__` method shadow, so a consumer `WhereNode` subclass, a consumer expression anywhere in the graph (including a lookup RHS operand or a node buried inside a subquery), an exact Django node with a shadowed `as_sql` or a dynamically-resolved `as_<vendor>` compiler method, a consumer join, or a foreign `select_related` all fail closed alongside a foreign `Query` class, a foreign combined-query branch, and a custom iterable class. A pending relation `_deferred_filter` is baked onto the framework-owned *detached clone* (never the candidate, which is left unmutated) through the unbound `sql.Query.add_q` only after every filter argument is proven inert (by exact leaf type, so a `str` / `int` / `datetime` subclass carrying a `resolve_expression` is not mistaken for a bound parameter) or genuine-Django — with a model-instance argument that shadows `resolve_expression` at the class or instance level failing closed — so no consumer `resolve_expression` runs mid-seal. The retained `QuerySet` state the seal carries forward — `_db` routing, `_hints`, `_fields`, `_sticky_filter`, `_for_write`, and `_prefetch_related_lookups` — is each pinned to its exact Django shape before any truthiness test, comparison, or copy runs on it, so a consumer `__bool__` / `__eq__` / `__iter__` on one of those fields cannot dispatch during the rebuild. A subclass is accepted as *input* (its query state is preserved) but its identity and behavior are deliberately dropped; a custom `Query` class or an unrecognized iterable class fails closed with a typed `ConfigurationError`. `None`, lists, generators, and other non-queryset returns fail closed, as does a queryset off the registered type's concrete table, one whose SQL-bearing `Query.model` (outer or any combined-query branch) is missing or non-model (a model-row select with no model escapes as malformed SQL otherwise), one whose combined-query branch reads another table's rows or is itself a foreign `Query` subclass, and (on read surfaces) an already-sliced queryset that the surface could not refilter or reorder without a raw Django error. On read surfaces a `.values()` / custom-iterable projection fails closed (the read contract composes over model rows), while the cascade deliberately accepts a projection return and re-projects it to the edge's target column. A `Manager` return is coerced through `.all()` with its explicit database routing preserved (a Manager whose `.all()` degrades into a non-queryset, or drifts from the manager's explicit `_db` alias, fails closed). Under a pinned resolution (an active write pipeline, or a source explicitly routed with `.using(...)`) an unrouted hook return is repinned onto the pinned alias while an explicitly divergent one fails closed; and every downstream framework operation (Relay node filtering, connection ordering/slicing/counting, filter/order sets, optimizer, cascade re-projection, and terminal evaluation sync and async) therefore runs on the sealed framework-owned queryset. A hook that returns the source object verbatim is re-sealed too — object identity is not immutability, so there is no identity fast path and an injected result cache (a synthetic unsaved row) cannot cross the boundary. An async `get_queryset` resolving to a nested awaitable (and an async consumer resolver resolving to a residual awaitable) also fails closed rather than skipping visibility.
- `DjangoOptimizerExtension` — automatic ORM optimization: one selection-tree walk produces a `select_related` / `prefetch_related` / `only()` plan that cooperates with querysets you've already shaped (consumer entries are respected, not clobbered). Plan caching, FK-id elision for `{ relation { id } }`, `get_queryset` → `Prefetch` downgrade so visibility filters survive joins, and strictness mode (`off` / `warn` / `raise`) for accidental-N+1 detection are all in the box. As of `0.0.9` the walk is connection-aware: a nested `<field>Connection`'s `edges { node }` selection gets a windowed `Prefetch` (one window-function query per relation per request instead of one per parent) and strictness flags an unplanned, unserved nested-connection access. As of `0.0.14`, *how* a recognized nested connection is fetched is a pluggable strategy seam: the windowed prefetch is the default backend (`"windowed"`), a Postgres `CROSS JOIN LATERAL` backend pages per parent (O(parents × page) instead of the window's O(all children)), and the backend is selected per extension instance via the `nested_connection_strategy=` constructor kwarg, the `NESTED_CONNECTION_STRATEGY` setting, or `"auto"`; auto keeps one cache-stable lateral-capable window plan, selects lateral only when the nested queryset's effective routed alias is PostgreSQL, and executes the same bounded window on every other vendor. A consumer-authored `NestedConnectionStrategy` instance is also accepted. A keyset-mode nested connection always orders by its target type's declared `Meta.cursor_field`, matching root keyset cursor bytes; supplying that field's `orderBy:` sidecar deliberately leaves it unplanned for the per-parent pipeline rather than overriding the cursor order. As of `0.0.10` the optimizer will not touch a queryset the consumer already evaluated (it passes an evaluated root queryset through unchanged rather than re-executing a clone — though as of the visibility-boundary hardening on `main` this pass-through holds only for querysets that do NOT cross a `get_queryset` visibility hook: an evaluated queryset supplied to or returned by the hook is refreshed to a lazy clone before it can serve rows, an intentional security carve-out, so it may be re-executed and optimized later and object identity is not preserved) and applies no column projection on non-query operations (mutation / subscription querysets keep `select_related` / `prefetch_related` but carry no `.only()` deferral). See [`GLOSSARY.md`][glossary] for the full optimizer surface.
- `DjangoListField` — non-Relay `list[T]` factory for root Query fields (new in `0.0.7`); default resolver pulls `model._default_manager.all()` and applies the type's `get_queryset` in sync + async contexts. **Row-bounded since `0.0.16`**: the request policy's `max_list_rows` always applies and `max_rows=` narrows it further (`trusted_max_rows=True` is the only widening). See [`GLOSSARY.md#djangolistfield`][glossary-djangolistfield].
- `OptimizerHint` — per-relation overrides (`SKIP`, `select_related`, `prefetch_related`, custom `Prefetch`)
- model / type registry and `auto` re-export from Strawberry
- `Meta.primary` — multiple `DjangoType` subclasses per Django model with explicit primary-flag opt-in
- annotation-only and `strawberry.field` consumer overrides for scalar fields, symmetric with the shipped relation-override contract (consumer overrides bypass `convert_scalar` validations; `relay.Node` `id` collisions raise `ConfigurationError` at type-creation time)
- `Django AppConfig` — `django_strawberry_framework/apps.py` ships `DjangoStrawberryFrameworkConfig` so consumers can list `"django_strawberry_framework"` in `INSTALLED_APPS` and Django's check / signal hooks resolve through it (new in `0.0.7`).
- `manage.py export_schema` — Django management command that prints or writes the GraphQL SDL for a `strawberry.Schema` symbol (positional dotted path, optional `--path`); migration-parity with `strawberry-django`'s command of the same name. See [`GLOSSARY.md#schema-export-management-command`][glossary-schema-export-management-command].
- filtering subsystem (new in `0.0.8`) — `FilterSet` declarative filter classes with `Meta.fields` (dict / `"__all__"` shorthand) and the full `django-filter` lookup surface; `RelatedFilter` for cross-relation traversal (class / absolute import path / unqualified-name); `Meta.filterset_class` consumer wiring; the `filter_input_type` resolver-argument helper; finalizer phase-2.5 binding with orphan validation; per-field `check_*_permission` denial gates with active-input-only scope; clean composition with `get_queryset` visibility and the optimizer. See [`GLOSSARY.md#filterset`][glossary-filterset].
- ordering subsystem (new in `0.0.8`) — `OrderSet` declarative ordering classes with `Meta.fields` (list form or `"__all__"` shorthand for every column-backed model field); `RelatedOrder` cross-relation ordering traversal (class / absolute import path / unqualified-name); `Meta.orderset_class` consumer wiring (promoted out of `DEFERRED_META_KEYS`); the public `Ordering` enum (six members with NULLS positioning); the `order_input_type` resolver-argument helper; finalizer phase-2.5 binding with orphan validation; per-field `check_*_permission` denial gates with active-input-only scope plus active-branch dispatch on `RelatedOrder` branches; row-preserving `Min` / `Max` ordering across to-many paths; omitted fields and explicit `null` directions both contribute no ordering term; clean composition with the shipped filter subsystem, root connection cursor pages, and the optimizer's deliberate per-parent fallback for nested connections carrying `orderBy:`. See [`GLOSSARY.md#orderset`][glossary-orderset].
- `DjangoConnectionField` (new in `0.0.9`) — Relay connection field over a Relay-Node-shaped `DjangoType`: `edges` / `node` / `pageInfo` cursor pagination on Strawberry's native `relay.connection()`, with `filter:` / `orderBy:` arguments derived from the wrapped type's `Meta.filterset_class` / `Meta.orderset_class` sidecars (no hand-written list resolver, no parallel argument declarations) and an opt-in `totalCount` via `Meta.connection = {"total_count": True}` (counted on the post-filter pre-slice queryset, selection-gated, per connection instance). Composition pipeline runs `get_queryset` visibility → `filter` → `orderBy` → default deterministic pk-ordering → optimizer-plan → cursor slice; the field owns its own optimizer cooperation point. `DjangoConnection[T]` is the generic return-type alias. See [`GLOSSARY.md#djangoconnectionfield`][glossary-djangoconnectionfield].
- `DjangoNodeField` / `DjangoNodesField` (new in `0.0.9`) — root Relay refetch fields, bare interface (`node: relay.Node | None = DjangoNodeField()`, `nodes: list[relay.Node | None] = DjangoNodesField()`) and typed (`genre: GenreType | None = DjangoNodeField(GenreType)`) forms; `id: ID!` raw-string arguments decoded server-side via the strategy-aware dispatch; dispatch to the type's `resolve_node` / `resolve_nodes` honoring `get_queryset`; `null` for hidden/missing/uncoercible-pk ids (no existence leak), `GraphQLError` with `extensions={"code": "GLOBALID_INVALID"}` for malformed ids; `nodes` is per-type-batched, order-preserving, with `null` holes and duplicate-id support. See [`GLOSSARY.md#djangonodefield`][glossary-djangonodefield].
- relation-as-Connection upgrade + `Meta.relation_shapes` (new in `0.0.9`) — every Relay-Node-shaped type's many-side relations whose target is also Relay-Node-shaped render as a `<field>Connection` **alone** since `0.0.16` (the default moved from `"both"` to `"connection"`, because a raw list sibling has no page of its own and was a way around the connection's cap); `Meta.relation_shapes = {"<field>": "list" | "connection" | "both"}` selects per relation, and an opted-in raw list is row-bounded by the resource policy; synthesized at finalization Phase 2.5 reusing the shipped connection machinery (per-target connection classes, sidecar `filter:` / `orderBy:` arguments, target-driven `totalCount`). See [`GLOSSARY.md#metarelation_shapes`][glossary-metarelation_shapes].
- `testing.relay` helpers (new in `0.0.9`) — `django_strawberry_framework.testing.relay.global_id_for(type_cls, id)` (the strategy-aware encoded `GlobalID` a finalized Relay-Node-shaped type emits) and `decode_global_id(gid)` (public re-export of the decode dispatch). See the [`GLOSSARY.md#djangonodefield`][glossary-djangonodefield] cross-refs (the helpers have no own entry; the spec does not create one).
- `Meta.nullable_overrides` / `Meta.required_overrides` (new in `0.0.9`) — two tuple-set `Meta` keys that decouple a non-relation field's GraphQL nullability from its Django column (`T!`→`T` or `T`→`T!`) without an `AlterField` migration or a consumer-authored annotation. Validated at type-creation (unknown / excluded / consumer-authored / relation / Relay-suppressed-pk targets and the both-sets collision raise `ConfigurationError`); the scope is non-relation model fields — scalar columns and, as of `0.0.11`, the file/image output objects — and the override flips a choice field's generated enum nullability for free. See [`GLOSSARY.md#metanullable_overrides`][glossary-metanullable_overrides].
- `manage.py inspect_django_type` (new in `0.0.9`) — diagnostic command printing a finalized `DjangoType`'s per-field GraphQL resolution table (Django field → resolved GraphQL type → nullability → converter row). Dispatches the positional arg by shape (dotted path vs unique bare-name registry lookup) and accepts `--schema <selector>` to register + finalize on a cold CLI process. See [`GLOSSARY.md#schema-introspection-management-command`][glossary-inspect-django-type].
- `apply_cascade_permissions` / `aapply_cascade_permissions` (new in `0.0.10`) — cascade-permissions subsystem: one call inside a type's `get_queryset` cascades that type's visibility across its single-column concrete forward FK / OneToOne edges, dropping parent rows whose targets a target type's own `get_queryset` hides. Loud `fields=` validation, a sync + `sync_to_async` async pair, and zero added query round-trips (the `__in` subqueries compile into the caller's single `SELECT`); composes with the shipped `check_<field>_permission` gates, connections, node refetch, and list fields through their existing seams. Exported from the package root. As of the cascade-hardening work on `main`, the traversal contract fails closed on every boundary the composed SQL depends on: recursive graphs raise a path-rich `ConfigurationError` (an explicit `fields=[]` nested application is the one permitted re-entrant shape), MTI parent links cascade, every registered target composes from its `_default_manager` (identity hooks included), `GenericForeignKey` / composite forward relations preflight closed, and hook returns run the shared visibility boundary (a `Manager` return is coerced, an unrouted return is repinned onto the pinned root alias, an explicitly re-routed one fails closed) before the cascade's own SQL-composability validation normalizes them to the edge's target column. See [`GLOSSARY.md#apply_cascade_permissions`][glossary-apply-cascade-permissions] for the full contract.
- mutations + auto-generated `Input` types (new in `0.0.11`) — the package's write side: a `DjangoMutation` base configured through a nested `class Meta` (`model` + `operation` ∈ `{"create", "update", "delete"}`, the DRF shape, not Strawberry decorators), exposed on the schema's `Mutation` type through the `DjangoMutationField` factory (the write-side sibling of `DjangoConnectionField`). Auto-generated `<Model>Input` (each editable field required only when it has no usable Django `default` / `blank` / `null`, else optional) / `<Model>PartialInput` (all-optional) derive from `Meta.model` reusing the read-side scalar / relation converters (forward FK / OneToOne → `<field>_id`, M2M → `list[id]`); the shared `FieldError` envelope (`field` + `messages`) surfaces `full_clean()` validation through a `<Name>Payload` carrying the mutated object in a uniform `node` / `result` slot plus `errors: list[FieldError]!`. Write authorization is a separate, DRF-shaped contract — `Meta.permission_classes` (default `[DjangoModelPermission]`, the Django `add` / `change` / `delete` model perms) plus an overridable `check_permission` — kept distinct from `get_queryset` visibility (can-view ≠ can-write). `update` / `delete` lookups run through the target type's `get_queryset` (a hidden row is not-found, no existence leak); the post-write row is re-fetched and optimizer-planned (`select_related` / `prefetch_related`, no `.only()` under the mutation operation). Sync + async. As of `0.0.14`, generated mutations require the schema to be built as `DjangoSchema` (its execution context holds each mutation's transaction open through GraphQL response completion — an unserializable payload rolls the write back; plain `strawberry.Schema` execution fails before writing), every model-backed flavor locks its target and relation rows by default (`Meta.select_for_update`, base-manager `FOR UPDATE` under a visibility pk subquery; explicit `False` opts out), and a row that disappears mid-operation returns the in-band `conflict` `FieldError` instead of a silent success. `DjangoMutation` / `DjangoMutationField` / `FieldError` / `DjangoModelPermission` / `DjangoSchema` / `DjangoMutationExecutionContext` are exported from the package root. See [`GLOSSARY.md#djangomutation`][glossary-djangomutation].
- `Upload` scalar + file/image field mapping (new in `0.0.11`) — the `Upload` scalar (Strawberry's built-in, re-exported from the package root) and the generated `DjangoMutation` input mapping of `FileField` / `ImageField` editable columns → `Upload` (required per the shipped per-field rule, `Upload | None` on `blank` / `null`); on the read side, `FileField` / `ImageField` columns convert to the structured `DjangoFileType` / `DjangoImageType` output objects — the object itself is nullable by default in the generated SDL regardless of the Django column's `null` / `blank` (an empty stored file resolves to `null`; `required_overrides` opts into a non-null `DjangoFileType!`), with `name` non-null and `path` / `size` / `url`, plus image `width` / `height`, nullable and storage-safe inside it — via the new `FIELD_OUTPUT_TYPE_MAP`. This is the scalar and generated mutation-field typing — not full multipart HTTP upload ergonomics, which arrived with the `0.0.14` `TestClient`. `Upload` / `DjangoFileType` / `DjangoImageType` are exported from the package root. See [`GLOSSARY.md#upload-scalar`][glossary-upload-scalar].
- form-based mutations (new in `0.0.12`) — the form-validated write flavor on the same `class Meta` surface: `DjangoModelFormMutation` (a `ModelForm`, subclassing `DjangoMutation` via the `_resolve_model` seam so it returns the post-save object in the uniform `node` / `result` slot) and `DjangoFormMutation` (a plain model-less `Form` sibling — its own metaclass, returning the pinned `ok: Boolean!` + `errors: [FieldError!]!` payload, with a `perform_mutate` write hook), both declared through `Meta.form_class` (+ optional `fields` / `exclude`). The input shape is derived from the form's declared fields via `forms/converter.py` (reusing the read-side scalar / choice-enum / `Upload` converters where the field types overlap, so a plain `Form` can declare fields a model does not have), and `form.errors` maps onto the same frozen `FieldError` envelope (the form's `NON_FIELD_ERRORS` bucket keyed to `"__all__"`). Relation ids are visibility-checked through the related primary type's `get_queryset` before the form runs; the `ModelForm` `update` locates its row through the target type's `get_queryset` (a hidden row is not-found, no existence leak) and re-fetches optimizer-planned. Sync + async, inside the one `transaction.atomic()` boundary. Both bases are exported from the package root. See [`GLOSSARY.md#djangoformmutation`][glossary-djangoformmutation].
- DRF serializer mutations (new in `0.0.13`) — `SerializerMutation`, the serializer-validated write flavor via `Meta.serializer_class` over a DRF `Serializer` / `ModelSerializer`. It rides the shipped `DjangoMutation` write pipeline and the same frozen `FieldError` envelope (a `serializer.is_valid()` field error keys to its field; the serializer's non-field errors key to `"__all__"`); `djangorestframework` is a **soft** dependency — `import django_strawberry_framework` and `from django_strawberry_framework import *` both stay DRF-free, and `SerializerMutation` is a lazy root export resolved through the package `__getattr__`, deliberately **not** in `__all__`. See [`GLOSSARY.md#serializermutation`][glossary-serializermutation].
- session-auth mutations (new in `0.0.13`) — opt-in `login` / `logout` / `register` field factories plus a `current_user` query helper, imported from the `django_strawberry_framework.auth` submodule (**no** package-root re-export — they are absent from `__all__`). All ride the shared `FieldError` envelope; `register` is a `DjangoMutation` rider adding `validate_password` + `set_password` over the shipped create pipeline (the plaintext password is never persisted). The family defaults to `AllowAny` — the documented inversion of the write family's deny-by-default `DjangoModelPermission`, since login/register must serve the anonymous caller — with per-schema `permission_classes=` still available on every factory. `login` and `logout` are supported on Django HTTP and Channels HTTP; over a WebSocket, `login` is rejected (an established socket cannot return the rotated session cookie) and `logout` is supported only on a server-side session engine (signed-cookie WebSocket logout is rejected) — see the transport contract in [Session-auth deployment boundary](#session-auth-deployment-boundary). The user type's field selection is the authenticated read surface, so exclude `password` and privilege columns from it. See [`GLOSSARY.md#auth-mutations`][glossary-auth-mutations].
- Channels ASGI router (new in `0.0.14`, `DONE-041`; **redesigned on `main`** by the transport-security card, `046`) — `DjangoGraphQLProtocolRouter`, imported from `django_strawberry_framework.routers` (a lazy PEP 562 submodule export, never a package-root export): a `channels.routing.ProtocolTypeRouter` subclass whose `"http"` value **is** the required `django_application` you pass it, dispatched directly, and whose `"websocket"` value is the package's own three-wrapper composition — `DjangoWebSocketHostValidator` (the `Host` check, a **private** validator in `django_strawberry_framework.consumers`, not a symbol a consumer imports or configures) over `AllowedHostsOriginValidator` (the `Origin` check) over `AuthMiddlewareStack` over a `URLRouter` holding one exact-matched `re_path` onto a GraphQL WebSocket consumer. It no longer serves GraphQL over HTTP and is no longer constructor-compatible with upstream `strawberry_django.routers.AuthGraphQLProtocolTypeRouter`: `django_application` is required, `url_pattern` is renamed to `websocket_url_pattern` (exact, `r"^graphql/?$"`), and the Channels HTTP branch is gone. `channels` is the package's second **soft** dependency (after `djangorestframework`): importing the package or the submodule stays channels-free, and only symbol access raises the install-hint `ImportError`. See [Transport: the GraphQL HTTP endpoint and the ASGI router](#transport-the-graphql-http-endpoint-and-the-asgi-router) for the migration note, and [`GLOSSARY.md#djangographqlprotocolrouter`][glossary-djangographqlprotocolrouter].
- the package GraphQL HTTP view (**new on `main`**, `046`) — `DjangoGraphQLView` / `AsyncDjangoGraphQLView`, imported from `django_strawberry_framework.views` (a leaf-module import, never a package-root export) and declared in your own `urlpatterns`. Subclasses of Strawberry's Django views adding two boundary policies over the raw request body: a cumulative byte cap enforced before JSON parsing or schema execution (`MAX_REQUEST_BODY_BYTES`, default 1 MiB, per-mount `as_view(max_request_body_bytes=...)`, returning `413`, measured rather than materialized) and a strict UTF-8 wire contract (UTF-16 / UTF-32 and a leading UTF-8 BOM are a controlled `400`), neither of which rides the `APPLY_UPSTREAM_PATCHES` kill switch. The module is `channels`-free, so a WSGI-only project adopts it without the soft dependency.
- debug-toolbar middleware (new in `0.0.14`, `DONE-042`) — `DebugToolbarMiddleware`, imported from `django_strawberry_framework.middleware.debug_toolbar` (the leaf-module import is the opt-in boundary, never a package-root export): a subclass of the stock `debug_toolbar.middleware.DebugToolbarMiddleware` that teaches `django-debug-toolbar`'s SQL panel to see Strawberry `/graphql/` traffic — `process_view` tags Strawberry-view requests and `_postprocess` appends the GraphiQL bridge template to the IDE's HTML and injects a `debugToolbar` panel payload (per-panel `title` / `nav_subtitle` + the toolbar `requestId`) into JSON operation responses (`IntrospectionQuery` skipped). `django-debug-toolbar` is the package's third **soft** dependency (after `djangorestframework` and `channels`): importing the package stays toolbar-free and only importing this leaf raises the install-hint `ImportError`, while omitting `"debug_toolbar"` from `INSTALLED_APPS` raises `ImproperlyConfigured` at leaf import. See [`GLOSSARY.md#debug-toolbar-middleware`][glossary-debug-toolbar-middleware].
- test-client family (new in `0.0.14`, `DONE-043`) — `TestClient` / `AsyncTestClient` (sync + async) plus the `GraphQLTestMixin` / `GraphQLTestCase` unittest family, imported from `django_strawberry_framework.testing`: each drives Django's in-process test client against `/graphql/`, decodes the GraphQL response, and returns a typed `Response` carrying `errors` / `data` / `extensions` / the raw Django response. Endpoint selection follows a documented precedence (per-call `url=` → constructor `path=` → `GRAPHQL_URL` → the `TESTING_ENDPOINT` setting → `"/graphql/"`); `TestClient` / `AsyncTestClient` default to `assert_no_errors=True` while the mixin defaults to `False` for `assertResponseNoErrors()` / `assertResponseHasErrors()`, and the helpers carry the multipart-upload ergonomics the `Upload` scalar awaited. See the "Testing GraphQL endpoints" section below and [`GLOSSARY.md#testclient`][glossary-testclient].
- `DjangoDebugExtension` (new in `0.0.14`, `DONE-044`) — a Strawberry `SchemaExtension` that captures a GraphQL operation's SQL (through Django's own debug cursor, one bracket per `connections.all()` alias) and raised resolver exceptions into the response's `extensions.debug` map — the Strawberry-native equivalent of graphene-django's `DjangoDebugMiddleware` / `_debug` field, which `strawberry-graphql-django` offers nothing to borrow back. It is opt-in by adding the class to the aggregate `strawberry.Schema(...)`'s `extensions=` list (never a package-root export, imported from `django_strawberry_framework.extensions`), one fresh instance per operation (`strawberry-graphql>=0.316.0`). Never enable it on an internet-facing production schema: it returns interpolated SQL values and unmasked exception messages and tracebacks. See the "GraphQL response extension" section below and [`GLOSSARY.md#djangodebugextension`][glossary-djangodebugextension].

**`0.1.0`** — beta release: feature parity with `graphene-django` and `strawberry-graphql-django` (alpha → beta cut-over).

**Beta (`0.1.x`)** — Layer-3 depth on the road to `1.0.0`:
- `0.1.1` — `FieldSet` (declarative `fields_class`)
- `0.1.2` — `Meta.search_fields` + Postgres full-text-search filter primitives
- `0.1.3` — `AggregateSet` (`Sum` / `Count` / `Avg` / `Min` / `Max` / `GroupBy`, `aggregate_class`) + Layer-3 `Meta`-key promotion
- `0.1.4` — stable choice-enum naming overrides
- `0.1.5` — fakeshop GraphQL schema activation end-to-end + product-catalog Layer-3 HTTP tests + optimizer explain mode
- `0.1.6` — mutation idempotency keys + configurable filter/logic key namespace
- `0.1.7` — migration and adoption guides + adversarial non-live test suite

**`1.0.0`** — stable release: full `django-graphene-filters` depth + **API freeze** (strict SemVer applies from `1.0.0` forward).

## File and image output: the filesystem path is opt-in

### Migrating from `0.0.16` — an intentional breaking change

`DjangoFileType` and `DjangoImageType` no longer carry `path`. The default output of every generated `FileField` / `ImageField` column is now `name` / `size` / `url` (plus `width` / `height` on images), and the server's absolute filesystem path is not among them.

The path is deployment metadata, not client data. Wherever the storage backend can produce one it can carry usernames, release directories, container mounts, tenant layout, and storage conventions — none of which a client needs to render a file, and all of which are useful to someone chaining a later traversal or template defect. The package's API freeze begins at `1.0.0`; removing an unnecessary disclosure from a default during alpha is preferred over preserving it for migration convenience, and card `046` set that precedent.

**If a client selection breaks**, it was selecting `path`. Two supported routes:

- **Drop it.** `url` is what a client needs to fetch the file, and `name` is the stored key. Most selections of `path` were selecting it because it was there.
- **Opt the column in.** Name it in the wrapping type's `Meta.filesystem_path_fields`, and that column alone resolves to the path-bearing output object:

```python
class MediaSpecimenType(DjangoType):
    class Meta:
        model = MediaSpecimen
        fields = ("id", "label", "attachment", "image")
        # `attachment` gains `path`; `image` does not.
        filesystem_path_fields = ("attachment",)
```

The opt-in is per column and lives in the type's own `Meta`, so one class shows every path it publishes. The opted-in column's GraphQL type name changes with it — `DjangoFileType` becomes `DjangoFilePathType`, `DjangoImageType` becomes `DjangoImagePathType` — and the `path` field carries a security description in the generated SDL. Every other subfield is unchanged, so a selection of `{ attachment { name path url } }` ports as written once the opt-in is declared.

Naming something that cannot work raises `ConfigurationError` at type creation rather than doing nothing: an unknown field, a field excluded from the selected set, a column that is not a `FileField` / `ImageField`, or a column whose annotation or `strawberry.field` you already own. A security opt-in that silently no-ops reads to a reviewer as "the path is exposed" and "the path is not exposed" with equal plausibility.

Storage failures are unchanged. `path` still degrades to `null` on a backend that cannot produce one (an S3-style `NotImplementedError`), and a `SuspiciousFileOperation` still surfaces as a top-level error rather than hiding as a null subfield — removing the field from the default is not a substitute for that guard.

## Nested connection indexing

`OptimizerHint.strategy(...)` overrides the nested-connection fetch backend for **one** Relay connection field, taking precedence over the extension-wide default (`nested_connection_strategy=` on `DjangoOptimizerExtension`, the `NESTED_CONNECTION_STRATEGY` setting, or `"auto"`):

```python
from django_strawberry_framework import DjangoType, OptimizerHint

class ShelfType(DjangoType):
    class Meta:
        model = Shelf
        fields = "__all__"
        optimizer_hints = {
            # Force the Postgres LATERAL backend for this field only; every
            # other connection keeps the extension-wide strategy.
            "books": OptimizerHint.strategy("lateral"),
        }
```

The name (`"windowed"`, `"lateral"`, `"auto"`, or a `NestedConnectionStrategy` instance) is validated at `Meta.optimizer_hints` build time, so a typo raises `ConfigurationError` immediately rather than at query time. The override is schema-static and never enters the plan cache key.

Both the default windowed prefetch and the LATERAL backend partition each parent's page by the child connector column and order by the connection's deterministic order. The database can serve each page **from an index** instead of sorting per partition when a composite index leads with the window's leading columns:

- **reverse FK / M2M:** `(connector, order columns…, pk)` — e.g. an `ORDER BY title, id` window on `Book.shelf_id` is served by an index on `(shelf_id, title, id)`.
- **direction matters:** a B-tree serves the requested order **or its full reverse** after the equality-constrained prefix, never a partial flip. A mixed `ORDER BY title ASC, id DESC` needs `(shelf_id, title, -id)` (or the full `(shelf_id, -title, id)` reverse); a plain `(shelf_id, title, id)` cannot serve it.
- **`GenericRelation`:** the morph `content_type_id` is an equality predicate on every query, so the useful prefix is `(content_type_id, object_id, order columns…, pk)` — not `object_id` alone.

When `settings.DEBUG` is on, the optimizer logs a one-time **advisory** warning per plan shape naming the recommended composite index if the model's *represented* metadata does not already contain a covering one. The check inventories every physical index shape Django model metadata represents — not only `Meta.indexes`, but also field-based `Meta.constraints` `UniqueConstraint`s, legacy `unique_together`, and field-level primary-key / unique / `db_index` columns — so a covering `UniqueConstraint` correctly silences the advisory. It is advisory only: it never raises, drops to `debug` level with `DEBUG` off, and stays **silent** when it cannot prove absence. Coverage is claimed only for ordinary B-tree indexes (a plain `models.Index` or PostgreSQL `BTreeIndex`); a non-B-tree access method (`GinIndex`, `GistIndex`, `HashIndex`, `BrinIndex`, `SpGistIndex`), a custom `Index` subclass, a non-default opclass (on an `Index` **or** a `UniqueConstraint`), an expression or partial index, or any shape the metadata cannot classify leaves coverage **unknown** (silent, never falsely covered). A descending index column is trusted only when **every** configured database supports index-column ordering (a backend-neutral cached plan may run on a shard that would silently drop the direction). An index absent from Django model metadata entirely — a DBA-managed index created only in the database — is not visible to the check. See [`GLOSSARY.md`][glossary] for the full optimizer surface.

### Single-parent fast path

The windowed backend numbers **every** child of a partition (`ROW_NUMBER() OVER (PARTITION BY fk)`) before filtering to the page — the right trade across many parents, but wasteful when a prefetch runs for exactly one parent (e.g. a root list filtered to a single row), where a plain `WHERE fk = x ORDER BY … LIMIT n` is a bounded index walk. A **default-on** runtime optimization handles that degenerate case: when the parent `IN` list Django injects has length one and the query is exactly the shape that was planned, the fast path runs the plain filtered `LIMIT` from the pristine child queryset and synthesizes the row numbers in Python, instead of the whole-partition window.

- **Eligible shape:** a single parent id, a direct FK (reverse FK / reverse one-to-one), and a count-free bounded first page.
- **Still windowed (never eligible):** a counted (`totalCount`), reversed (`last:`), offset (`after:`), or keyset-seek page; an M2M / `GenericRelation` join; and any fetch-time query carrying a visibility filter or other predicate that is not exactly the planned window — every such case, and any Django-internals drift, degrades to the identical windowed body (a performance downgrade, never a wrong page).
- **Disable it:** set `DJANGO_STRAWBERRY_FRAMEWORK["SINGLE_PARENT_FAST_PATH"] = False`. The flag is read at **fetch time**, so it is `override_settings`-testable and never baked into the plan cache.
- **Strategy composition:** it is a `"windowed"`-strategy feature. Under `"lateral"` / `"auto"` the lateral backend handles the clean eligible shape at plan time; a lateral plan that *downgrades* through the windowed floor (for example a child queryset carrying `select_related`, which lateral refuses) can still receive this wrapper.

## Schema setup boundary

`finalize_django_types()` must run once during single-threaded import/schema setup, after every module that defines `DjangoType` classes has been imported and before `strawberry.Schema(...)` is constructed. The most common failure mode is forgetting to import a module that contains a related type before finalization.

Recommended:

```python
from django_strawberry_framework import finalize_django_types, strawberry_config

from myapp import types as _types  # noqa: F401

finalize_django_types()
_optimizer = DjangoOptimizerExtension()
schema = strawberry.Schema(query=Query, config=strawberry_config(), extensions=[lambda: _optimizer])
```

Wrong order:

```python
_optimizer = DjangoOptimizerExtension()
schema = strawberry.Schema(query=Query, config=strawberry_config(), extensions=[lambda: _optimizer])
finalize_django_types()
```

The second form constructs the Strawberry schema before relation targets are finalized, so exposed relations whose target type was still pending cannot be resolved into concrete `DjangoType`s.

### `DjangoSchema` is required for generated mutations

A schema that exposes any generated mutation (`DjangoMutationField` over a `DjangoMutation` / `DjangoModelFormMutation` / `DjangoFormMutation` / `SerializerMutation`) must be constructed as `DjangoSchema`, not plain `strawberry.Schema`:

```python
from django_strawberry_framework import DjangoSchema

schema = DjangoSchema(
    query=Query,
    mutation=Mutation,
    config=strawberry_config(),
    extensions=[lambda: _optimizer],
)
```

`DjangoSchema` installs `DjangoMutationExecutionContext`, which holds each generated top-level mutation field's `transaction.atomic()` open **through GraphQL response completion**: a payload that cannot be serialized (a non-nullable field completing `null`, a corrupt scalar) rolls the write back instead of committing behind a `data: null` response. Under plain `strawberry.Schema` the write pipeline refuses to run — the mutation fails with a `ConfigurationError` naming this requirement before any database work. Serial top-level mutation fields in one operation each get an independent transaction, per the GraphQL spec's serial-mutation semantics. Query-only schemas are unaffected. A consumer with its own execution context subclasses `DjangoMutationExecutionContext` and passes it via `execution_context_class=`.

### Production error policy

`DjangoSchema` also resolves a **production error policy** once, at construction, and installs the extension that applies it. Under `settings.DEBUG = False` an **unexpected** resolver or hook exception no longer puts its own message on the wire: the client receives a stable, non-sensitive message plus a correlation identifier, and the original exception (with its traceback) is logged server-side under that same identifier through the `django_strawberry_framework` logger at `ERROR`.

```json
{
  "errors": [
    {
      "message": "An unexpected error occurred.",
      "path": [
        "someField"
      ],
      "extensions": {
        "correlationId": "6f1a2c8d4b0e4f26a1c3d5e7f9b0a2c4"
      }
    }
  ]
}
```

Deliberate client-facing errors keep their contract, and the rule that decides is structural rather than an allowlist of codes:

| Error shape | Reaches the client as |
|---|---|
| parse / syntax / validation error (no originating exception) | unchanged |
| a raised `GraphQLError` — every framework rejection (`GLOBALID_INVALID`, `RESOURCE_LIMIT_EXCEEDED`, the connection / keyset / filter argument rejections, the `Not authorized to ...` denial) and any you raise yourself | unchanged, `extensions.code` included |
| any other exception escaping a resolver or hook | the policy message + a fresh `correlationId` |

A validation envelope (`FieldError` rows on a mutation payload) is `data`, not an error, and is untouched. Under `settings.DEBUG` the policy is a pass-through, so local development keeps its messages.

Configure it with `DjangoSchema(error_policy=...)` or the `DJANGO_STRAWBERRY_FRAMEWORK["ERROR_POLICY"]` mapping (the constructor argument wins), and opt out explicitly:

```python
schema = DjangoSchema(
    query=Query,
    error_policy={
        "message": "Something went wrong. Quote the correlation id when you report it.",
        "correlation_extension_key": "traceId",
    },
)

# Explicit opt-out for a consumer who owns their own masking:
schema = DjangoSchema(query=Query, error_policy={"enabled": False})
```

The extension is **prepended** to the schema's `extensions=` list. Strawberry unwinds `on_operation` teardowns LIFO, so the first-listed extension finishes last; masking has to happen after every extension that reads `GraphQLError.original_error` — `DjangoDebugExtension` in particular — has had its turn. Supplying your own `DjangoErrorPolicyExtension` entry suppresses the prepend and keeps your position.

**Subscriptions are covered per event.** A query or mutation produces one result, so the extension's teardown is the whole response for it; a subscription delivers one result per event, and the teardown only runs when the operation ends. So the policy is applied again at the package's own subscription result source, immediately before each event's frame is written — every event carries the policy message and its own `correlationId`, with one server-side log record each. The event the engine built keeps its original exception, so a `DjangoDebugExtension` on the same schema still reports the real type and traceback. This applies to subscriptions served through the package's ASGI router (`DjangoGraphQLProtocolRouter`), which is the supported mount; a hand-rolled Channels consumer masks only at the operation's end.

## Transport: the GraphQL HTTP endpoint and the ASGI router

GraphQL over **HTTP** is a normal Django view declared in your own URLconf. GraphQL over **WebSocket** is the Channels router. Splitting them is the whole point (spec-046): the router no longer serves HTTP, so every GraphQL HTTP request traverses your project's real `MIDDLEWARE` — the `ALLOWED_HOSTS` host check, `CsrfViewMiddleware`, `SecurityMiddleware`'s headers, `SessionMiddleware` / `AuthenticationMiddleware`, cache policy, and anything you wrote — exactly as it does under WSGI.

You do **not** need `channels` for the HTTP half. `django_strawberry_framework.views` is channels-free; a WSGI-only project adopts `DjangoGraphQLView` without the soft dependency and never imports `routers.py` at all.

### Migrating from `0.0.14` — an intentional breaking change

The `0.0.14` `DjangoGraphQLProtocolRouter` constructor is deliberately broken in three ways. The package's API freeze begins at `1.0.0`; correcting a security-boundary error during alpha is preferred over preserving an unsafe migration convenience.

| `0.0.14` | now | what a migrant hits |
|---|---|---|
| `django_application=None`, optional | `django_application`, **required** | omitting it is a `TypeError`; passing `None` (or any non-callable) is a `ConfigurationError` whose message names this migration |
| `url_pattern="^graphql"` — a prefix, applied to **both** protocols | `websocket_url_pattern=r"^graphql/?$"` — exact at both ends, **WebSocket only** | the keyword is renamed; the default no longer matches `/graphql-admin`, `/graphqlanything`, or `/graphql/extra` |
| the router served GraphQL over HTTP through Strawberry's `GraphQLHTTPConsumer`, with `django_application` appended behind it as a `^` fallback | the router's `"http"` value **is** your Django ASGI application, dispatched directly with no wrapper | nothing serves GraphQL over HTTP until you add the `urlpatterns` entry below — this is the step with no automatic equivalent |

**Old `asgi.py` (`0.0.14`):**

```python
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myproject.settings")

from django.core.asgi import get_asgi_application

django_asgi_app = get_asgi_application()

from django_strawberry_framework.routers import DjangoGraphQLProtocolRouter

from myproject.schema import schema

# The router owned GraphQL on BOTH protocols. `django_application` was an
# optional `^` fallback appended AFTER the router's own `^graphql` HTTP route,
# so a GraphQL POST never reached Django's middleware at all. Both of these
# were valid 0.0.14 spellings:
application = DjangoGraphQLProtocolRouter(schema)
application = DjangoGraphQLProtocolRouter(schema, django_asgi_app, url_pattern=r"^graphql")
```

**New `asgi.py`:**

```python
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myproject.settings")

from django.core.asgi import get_asgi_application

django_asgi_app = get_asgi_application()

from django_strawberry_framework.routers import DjangoGraphQLProtocolRouter

from myproject.schema import schema

# `django_asgi_app` IS the "http" value: every HTTP request, GraphQL included,
# goes through Django. The router composes WebSocket only — Host check >
# AllowedHostsOriginValidator > AuthMiddlewareStack > URLRouter > the consumer.
application = DjangoGraphQLProtocolRouter(
    schema,
    django_asgi_app,
    websocket_url_pattern=r"^graphql/?$",  # the default; shown for the rename
)
```

**The `urlpatterns` entry the new `asgi.py` depends on** — without it, `/graphql/` is a `404`:

```python
# myproject/urls.py
from django.urls import path

from django_strawberry_framework.views import DjangoGraphQLView

from myproject.schema import schema

urlpatterns = [
    path("graphql/", DjangoGraphQLView.as_view(schema=schema)),
]
```

`AsyncDjangoGraphQLView` is the async twin, mounted identically; it is the shape an ASGI deployment generally wants, since `as_view()` returns a coroutine function Django dispatches on the event loop without a thread hop. Both classes are leaf-module imports from `django_strawberry_framework.views` and are deliberately **not** package-root exports.

The Channels ASGI router only becomes necessary when you want GraphQL **subscriptions over WebSocket**. An HTTP-only deployment can drop `asgi.py`'s router entirely and serve `get_asgi_application()` (or WSGI) with just the `urlpatterns` entry above.

**`APPEND_SLASH`.** Mounting at `"graphql/"` means a client that POSTs to `/graphql` (no trailing slash) gets Django's `CommonMiddleware` `301` to `/graphql/` under `DEBUG=False`, and a `RuntimeError` under `DEBUG=True` telling you the POST data would be lost. Most HTTP clients do not re-POST a redirect, so **point your clients at the exact mounted path**. The WebSocket default `r"^graphql/?$"` deliberately accepts both spellings, because a WebSocket handshake has no body to lose. If you prefer the slash-less HTTP spelling, mount at `path("graphql", ...)` and set `TESTING_ENDPOINT` to match.

### Transport deployment guidance

Routing GraphQL through Django restores the authoritative middleware lifecycle. It does **not** automatically supply every transport resource bound — the sections below are the ones a deployment still owns.

**CSRF.** The GraphQL endpoint is now an ordinary CSRF-protected Django view, so cookie-backed session authentication is protected by `CsrfViewMiddleware` on the same terms as the rest of your site. Keep it enabled, follow [Django's CSRF guidance][django-csrf], and exercise the deployed view with `Client(enforce_csrf_checks=True)` ([Django's test-client CSRF checks][django-test-client-csrf]). If you serve the in-browser IDE, wrap the mount in `ensure_csrf_cookie` so the GET that serves GraphiQL sets the `csrftoken` cookie the subsequent POST needs.

One detail of the view's own plumbing reads like a relaxation and is the opposite of one. The view callback is marked `csrf_exempt` on the outside — an **ordering mechanism, not a CSRF bypass**. Its only effect is that the global middleware's `process_view` cannot touch `request.POST`, and so cannot run Django's multipart parser, *before* the body cap has decided whether to accept the request at all. Every request that passes the cap immediately enters a package-owned continuation wrapped in Django's own public `csrf_protect`, so Django's complete CSRF implementation still runs on it, with the same tokens, the same referer checks, and the same `403`. The net effect is stricter than the ordinary arrangement, not looser: because the protection is applied by the view rather than borrowed from the middleware stack, this endpoint stays CSRF-protected even in a project that has omitted `CsrfViewMiddleware` from `MIDDLEWARE` altogether.

WebSocket is the exception and always was: a Channels consumer runs no `CsrfViewMiddleware`, so on that protocol the router's handshake defences are `DjangoWebSocketHostValidator` (`Host`) and `AllowedHostsOriginValidator` (`Origin`) rather than a CSRF token — two separate checks, both reading your project's `ALLOWED_HOSTS`, neither standing in for the other. Keep that setting tight.

**Cache and `Vary`.** An authenticated GraphQL response must never be served from a shared cache to a different actor. Django already patches `Vary: Cookie` once the session is read or the CSRF cookie is set, but a reverse proxy or CDN in front of the endpoint has to honor it. The safest posture for a cookie-authenticated schema is to mark the GraphQL location uncacheable at the edge and let the application decide.

**Security headers.** `SecurityMiddleware`'s configured headers (`X-Content-Type-Options`, `Referrer-Policy`, and HSTS via `SECURE_HSTS_SECONDS` on an HTTPS request) now apply to the GraphQL route because the route is a Django view. Under `0.0.14`'s Channels HTTP branch they did not — verify yours actually land after migrating.

**The IDE and GET queries.** Both are on by default in Strawberry's view. For a production mount, turn them off:

```python
path(
    "graphql/",
    DjangoGraphQLView.as_view(
        schema=schema,
        graphql_ide=None,            # no GraphiQL / Pathfinder HTML
        allow_queries_via_get=False, # POST-only; no query in a URL, no CDN caching of it
    ),
),
```

`multipart_uploads_enabled` is off by default and should stay off unless the schema actually takes an `Upload`.

**The request-body cap is two layers, and you need both.** The package's view enforces a cumulative byte cap before JSON parsing or schema execution (`MAX_REQUEST_BODY_BYTES`, default 1 MiB, overridable per mount with `as_view(max_request_body_bytes=...)`), returning `413`. What that guarantees is precise and limited: the application never parses, allocates a document from, or executes a schema against an over-limit body, it never allocates or reads more than `limit + 1` bytes of one, and the refusal is itself bounded. What it **cannot** guarantee is that the bytes were never received — `django.core.handlers.asgi.ASGIHandler.read_body` has already drained the entire request into a spooled temporary file, rolling to disk past `FILE_UPLOAD_MAX_MEMORY_SIZE`, before any application-level cap can run. The application cap bounds what the application *processes*; only the deployment can bound what the server *accepts*.

So a reverse-proxy / ASGI-server cap is a **co-requirement of the application cap, never an alternative to it**. Set both:

```nginx
# nginx: refuse the body at the edge, before Django is entered.
location /graphql/ {
    client_max_body_size 1m;   # nginx answers 413 itself
    proxy_pass http://asgi_upstream;
}
```

```apache
# Apache in front of an ASGI upstream:
LimitRequestBody 1048576
```

Be aware of what the ASGI servers do and do not give you here. Uvicorn, Hypercorn, and Daphne ship **no total-request-body limit**; the size knobs they do expose bound something else. Uvicorn's `--h11-max-incomplete-event-size`, and Gunicorn's `--limit-request-line` / `--limit-request-field_size` when it fronts an ASGI worker, bound the request line and headers, not the body. Daphne's `request_buffer_size` (a `daphne.server.Server` keyword, default `8192`, with no CLI flag) sets the chunk size Daphne delivers `http.request` fragments in — it changes fragment *delivery*, never the total body the server will accept. That is why the proxy line above is load-bearing rather than belt-and-braces: on a Daphne or Uvicorn deployment with no proxy cap, there is no layer below the application that will stop an oversized body from being spooled.

**Multipart is a carve-out, not a byte count.** For a `multipart/form-data` **POST** the bound is the declared `Content-Length` plus Django's own `MultiPartParser`, and nothing else — the carve-out is POST-scoped, and a multipart content type on any other method is counted like any other body, which is the stricter direction. The body is deliberately never materialized: reading it would defeat Django's streaming upload handlers and break the `Upload`-scalar path this package ships. The declaration is nonetheless enforced **before** that parser and its upload handlers run — an over-limit `Content-Length` on a multipart POST is refused with the same `413`, with no part parsed, no file written, and no upload handler entered. That ordering is a property of the `csrf_exempt` / `csrf_protect` arrangement described under **CSRF** above rather than of the cap itself: without it, the global middleware's CSRF `process_view` would have read `request.POST` and driven the entire parse before the cap could speak. Per-file count, per-file size, and aggregate upload size are **not** bounded by `MAX_REQUEST_BODY_BYTES` — bound them at the proxy, with Django's `DATA_UPLOAD_MAX_NUMBER_FILES` / `FILE_UPLOAD_MAX_MEMORY_SIZE`, or in your own upload validation.

**One UTF-8 wire.** A package view accepts UTF-8 request bodies and only UTF-8. UTF-16 / UTF-32 (BOM'd or BOM-less) and a leading UTF-8 BOM are rejected with the same controlled `400` that a malformed body gets. This is permanent package policy on the view and does not ride the `APPLY_UPSTREAM_PATCHES` kill switch. If a client is sending anything but UTF-8 today, fix the client — the alternative is `strawberry.django.views.GraphQLView`, which keeps upstream's RFC 8259 auto-detection.

**Multipart control documents.** The wire contract reaches the two control fields of a `multipart/form-data` GraphQL request — `operations` and `map` — which Django decodes to text before this package sees them. Two things must hold or the request gets the same controlled `400`. First, the form's **effective** encoding must be UTF-8: an explicit non-UTF-8 `charset` on the form is refused, and so is a `request.encoding` that consumer middleware set to a non-UTF-8 codec, because that attribute — not the declaration — is what `MultiPartParser` decodes with. Second, the decoded value must **survive Django's decode without a replacement marker**: Django decodes form fields with `errors="replace"`, so a malformed byte sequence does not raise, it silently becomes `U+FFFD`. A control value arriving with that marker in it is therefore refused rather than parsed. Both checks run before either value is parsed as JSON. Ordinary browser `JSON.stringify` output is unaffected and genuine multibyte UTF-8 passes through intact; a client that legitimately needs a literal replacement character in its document sends the ASCII JSON escape `\ufffd` instead of the raw character, which is the supported way to carry `U+FFFD` through this boundary. Django's `MultiPartParser`, `request.POST` / `request.FILES`, and the configured upload handlers remain the sole owners of multipart parsing — the package adds these two refusals and nothing else.

**The WebSocket handshake is validated on `Host` and on `Origin`.** Two separate checks, applied by two separate router-owned wrappers, and neither substitutes for the other. `Origin` is Channels' `AllowedHostsOriginValidator`, as it was in `0.0.14`. `Host` is the package's own `DjangoWebSocketHostValidator`, composed outermost: it projects the handshake's host metadata into a minimal Django `HttpRequest` and calls the public `request.get_host()`, so your project's existing `ALLOWED_HOSTS` and `USE_X_FORWARDED_HOST` govern a WebSocket handshake exactly as they govern an HTTP request. **No new setting exists.** Only a `DisallowedHost` becomes a denial, and the denial precedes authentication and consumer construction, so a hostile `Host` never reaches your session middleware or your consumer at all. The validator is private — the router composes it; a project neither imports nor configures it, and an injected consumer cannot escape it.

**WebSocket freshness and revocation.** The package's default WebSocket consumer revalidates the session actor at **two** checkpoints and writes the refreshed actor back onto `scope["user"]`: when an operation is **admitted** (`subscribe` on `graphql-transport-ws`, `start` on legacy `graphql-ws`), and again before every **information-bearing operation frame** an already-admitted operation puts on the wire (`next`, `data`, and the operation-scoped `error` both protocols use). Two checkpoints rather than one because admission alone never sees a running subscription again — both protocols park an admitted operation in their own result loop and keep sending from there without returning through the admission path. What the pair guarantees is that **a revoked actor can neither admit another operation nor emit another information-bearing operation frame** over an already-established socket.

Detection is **event-boundary-driven**: it happens the next time the socket does something, not at the instant an external logout lands. At whichever checkpoint notices first, the *whole connection* is closed with `4403` / `"Forbidden"` — upstream's own code and reason, with no preceding operation error and no reconnect — because the actor is connection-scoped, so the close is the rejection. `websocket_revalidation_window=` (seconds, default `0.0` = revalidate every time) now means the same thing at both checkpoints: the maximum age of a successful validation that may still authorize a new operation or an outbound information-bearing frame. It prices the session read against a named revocation delay:

```python
application = DjangoGraphQLProtocolRouter(
    schema,
    django_asgi_app,
    websocket_revalidation_window=5.0,  # at most 5s of revocation delay
)
```

**The idle-socket residue**, stated rather than left to be inferred: because detection is event-boundary-driven, a revoked socket that never produces another event stays physically open. Its subscription task, its session object, and its stale actor reference keep occupying the server until something makes it act. That is a resource-exhaustion concern and worth budgeting for, and it is **not** an authorization hole — an idle socket exercises no authorization, and the first thing it tries to do is refused and closed. The bound on it is the deployment's, and it is the same set of knobs as connection lifetime below.

**Connection lifetime.** The package does **not** impose a maximum connection lifetime, because there is no correct default: a dashboard subscription and a short-lived request-response socket differ by orders of magnitude. Enforce it in the deployment — Daphne's `--websocket_timeout` (maximum seconds a socket may stay connected; `-1` is infinite) and `--websocket_connect_timeout`, nginx's `proxy_read_timeout` on the WebSocket location, plus Daphne's `--websocket-max-message-size` / `--websocket-max-frame-size`, which are the only body-shaped bounds on the WebSocket side (the HTTP `MAX_REQUEST_BODY_BYTES` cap does not apply to a socket). Upstream's own `connection_init_wait_timeout`, `keep_alive` / `keep_alive_interval`, and `max_subscriptions_per_connection` are set on the consumer class, which you supply through `websocket_consumer_class=`:

```python
from datetime import timedelta

from strawberry.channels import GraphQLWSConsumer

class MyConsumer(GraphQLWSConsumer):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("connection_init_wait_timeout", timedelta(seconds=10))
        kwargs.setdefault("keep_alive", True)
        super().__init__(*args, **kwargs)

application = DjangoGraphQLProtocolRouter(
    schema,
    django_asgi_app,
    websocket_consumer_class=MyConsumer,
)
```

An injected consumer still sits inside all three of `DjangoWebSocketHostValidator`, `AllowedHostsOriginValidator`, and `AuthMiddlewareStack` by construction — the wrappers are the router's, not the consumer's — but it opts **out** of the package's revalidation, which is why injecting a class alongside a positive `websocket_revalidation_window` is a construction error rather than a silently ignored argument. With revalidation on, the freshness bound is the revalidation window rather than the connection lifetime.

**Development-only surfaces.** `DjangoDebugExtension` and `DebugToolbarMiddleware` return interpolated SQL and unmasked exception messages. Neither belongs on an internet-facing schema; see [Development debug responses](#development-debug-responses).

## Session-auth deployment boundary

The opt-in `login_mutation()` authenticates and establishes a Django session, but the framework does **not** provide brute-force throttling, lockout, or rate limiting. Attach a consumer-owned `permission_classes` gate or middleware before exposing login publicly. The login permission gate receives the attempted username for account-scoped controls but never receives the password.

CSRF enforcement also belongs to the HTTP transport: it depends on the view and Django middleware around the GraphQL endpoint, not the auth field resolver. Since spec-046 the GraphQL HTTP endpoint is a Django view in your own URLconf, so `CsrfViewMiddleware` runs on it like any other view — keep Django's CSRF protection enabled for cookie-backed session authentication, follow [Django's CSRF guidance][django-csrf], and exercise the deployed GraphQL view with `Client(enforce_csrf_checks=True)` as described by [Django's test-client CSRF checks][django-test-client-csrf]. CSRF-token rotation on login applies only to the Django HTTP transport (Django's `login` rotates the token); `channels.auth.login` does not rotate the CSRF token (Channels' own behavior). **WebSocket** is where CSRF is genuinely absent: a Channels consumer runs no `CsrfViewMiddleware`, so the handshake defences on that protocol are the router's own `DjangoWebSocketHostValidator` (`Host`) and `AllowedHostsOriginValidator` (`Origin`) rather than a token — two separate checks, neither standing in for the other; see [Transport: the GraphQL HTTP endpoint and the ASGI router](#transport-the-graphql-http-endpoint-and-the-asgi-router).

`register_mutation()` derives its input from the user model's `USERNAME_FIELD`, distinct `REQUIRED_FIELDS`, and `password`. It refuses to auto-expose Django's account-control fields (`is_active`, `is_staff`, `is_superuser`, `groups`, and `user_permissions`); custom registration flows must initialize privileges and activation state in server-owned logic.

### Transport support matrix

`login` and `logout` classify the request transport before any credential or session work and support exactly the transports they can serve truthfully:

| Transport | `login` | `logout` | Persistence rule |
|---|---|---|---|
| Django `HttpRequest` (sync or async) | supported | supported | `login` saves the session explicitly before the success payload; the session stays modified so `SessionMiddleware` saves again and still owns the response cookie |
| Channels HTTP scope | supported | supported | native `channels.auth.login` / `logout`; `login` persists explicitly with an `asave()`, and Channels' response middleware sends or deletes the cookie |
| Channels WebSocket, server-side session engine | **rejected before authentication** | supported | `flush()` durably deletes the server-side record, so the old cookie is anonymous on reconnect; the same-scope actor becomes anonymous |
| Channels WebSocket, signed-cookie session engine | **rejected before authentication** | **rejected before mutation** | an established socket cannot rotate or revoke the browser cookie, and the engine keeps no server-side record to delete |
| Missing session middleware | rejected before authentication | rejected before reporting an actor | actionable, transport-specific configuration error (the message keeps the substring `session`) |

WebSocket `login` is rejected because login rotates the session key and an established socket cannot return the replacement cookie — a "success" would establish a server-side session the browser could never claim. WebSocket `logout` is rejected on the signed-cookie engine because there is no server-side record to revoke and the browser cookie cannot be replaced over an open socket; it is supported on server-side engines, where deleting the record invalidates the old cookie without sending a new one. The WebSocket-logout capability check keys on Django's signed-cookie store class — it resolves the configured engine's `SessionStore` and rejects logout only when it is an `issubclass` of `SignedCookieSessionStore`; a third-party or custom client-side session engine that does not subclass it is treated as server-side and must not be used with WebSocket logout. Both rejections are top-level GraphQL execution errors (transport-capability configuration errors), distinct from the byte-identical failed-login envelope.

The signed-cookie engine has an inherent HTTP limitation worth stating: over HTTP, `logout` returns `ok: true` and middleware replaces the browser cookie, but a *captured* old signed cookie remains replayable because Django has no server-side record to revoke. That is the engine's limitation, not the framework's, and it is exactly why signed-cookie WebSocket logout is rejected rather than reported as durable.

`logout` returns `ok: true` only when an authenticated actor existed under the lock before teardown; an anonymous logout returns `ok: false` after still flushing any residual session data (idempotent teardown with an observational result). Every failure after successful authentication is fail-closed: no success payload is returned, the local actor is made anonymous, partial durable state is flushed, and a cleanup failure chains onto the primary error rather than claiming a clean state.

### Concurrency and storage failures

Session mutations multiplexed on **one** Channels scope are serialized by a per-scope `asyncio.Lock` (actor capture, mutation, persistence, and compensation are atomic under it). Independent HTTP requests, separate WebSocket connections, processes, and hosts are **not** globally serialized: their conflict behavior is the configured Django session backend's contract. A concurrent deletion of a session another request is mutating surfaces as the backend's own interruption error, propagated rather than papered over — the framework does not recreate or overwrite a logged-out session, and stores no process-global or cross-process lock.

### Enumeration posture

Wrong password, unknown user, inactive-under-`ModelBackend`, and backend `PermissionDenied` all collapse to one byte-identical failed-login envelope with no framework-added account lookup. Brute-force protection, rate limiting, lockout, and fine-grained timing behavior belong to the Django or custom authentication backend; the framework guarantees response indistinguishability and adds no user-existence oracle, but makes **no** constant-time guarantee across arbitrary custom backends.

### Observable Django HTTP persistence change

On Django HTTP, `login` now saves the session explicitly inside the resolver before constructing any success payload, so a session-store failure can surface as a GraphQL execution error *before* a success payload — earlier than a middleware-only save would. The session is deliberately left marked modified so Django's response middleware performs its normal save and emits the rotated cookie; this can produce a second save. The modified flag is not cleared to suppress that write, because doing so would also suppress the cookie transition that makes the durable session usable by the client.

## Production security profile

One auditable list for taking a schema built on this package from "runs" to "internet-facing". Everything here is either enforced by the package, stated in another section of this guide, or owned by Django and the deployment — this section assembles it so a review walks a single list instead of re-deriving the boundary. Start with Django's own [deployment checklist and `manage.py check --deploy`][django-deploy-checklist]: it mechanically audits the Django-settings half — `DEBUG`, `SECRET_KEY` provenance, `ALLOWED_HOSTS`, HTTPS/HSTS (`SECURE_SSL_REDIRECT` / `SECURE_HSTS_SECONDS`), and the secure/`SameSite` cookie flags (`SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`) — and nothing below repeats what it already reports. Two settings it will not flag for you: set `SECURE_PROXY_SSL_HEADER` and `USE_X_FORWARDED_HOST` **only** behind a proxy you control that strips the client's own values for those headers, and never otherwise — each turns a client-forgeable header into trusted fact.

### The declared Django floor is not a secure-version recommendation

`pyproject.toml` declares `Django>=5.2.16`. That is an **API-compatibility statement frozen at release time** — the oldest Django this package's code is written against and tested on — and it is not advice about which Django is safe to run. Production deployments must install the **newest security patch in whichever supported Django series they have chosen** (`5.2.x` or `6.0.x`), which will move past any floor this package can encode: a floor is a lower bound written once, while the secure version changes whenever the Django project publishes a release. The floor was deliberately raised to a patched release (`5.2.16`, which carries the CVE-2026-48588 fix) so that no supported configuration starts out behind a published advisory, but that only aligns the two numbers on the day of the raise — the first `5.2.17` makes "the floor" and "the secure version" diverge again, permanently and by design. Resolve Django from its own release stream and treat this floor as the compatibility bound it is; the project's CI carries an exact-floor matrix cell labelled `[compatibility floor]` for the same reason, and that cell is never a deployment target.

### What the package already defaults to safe

Verify these hold on the deployed endpoint rather than configuring them. Each row names a mechanical check; the two SDL rows read the export from the [schema-export management command][glossary-schema-export-management-command]:

| Guarantee | Since | Mechanical check |
|---|---|---|
| Unexpected resolver/hook exceptions are masked under `DEBUG=False` — see [Production error policy](#production-error-policy) | `0.0.17` | force one; the response carries the policy message + `correlationId`, never the exception's own text |
| `DjangoDebugExtension` fails closed under `DEBUG=False` | `0.0.17` | a schema listing it answers with no `extensions.debug` unless `allow_unsafe_production=True` was written into the code |
| One execution resource budget (document tokens / depth / selections / aliases, variable-value cardinality, list rows, uploads, deadline), resolved once at `DjangoSchema` construction | `0.0.16` | an over-budget document or variable payload is refused with `extensions.code = "RESOURCE_LIMIT_EXCEEDED"` before ORM work |
| Cumulative request-body cap applied before parsing — see [the two layers](#transport-deployment-guidance) | `0.0.15` | POST `MAX_REQUEST_BODY_BYTES` + 1 junk bytes → `413` |
| Strict UTF-8 wire contract | `0.0.15` | a UTF-16 body → the controlled `400` |
| Many-side relations expose the bounded connection only (`Meta.relation_shapes` defaults to `"connection"`) | `0.0.16` | the exported SDL carries no raw list sibling you did not opt into |
| File/image output carries no filesystem `path` unless `Meta.filesystem_path_fields` names the column | `0.0.17` | grep the exported SDL for `path` |
| Generated writes deny by default (`Meta.permission_classes` required; `[]` is the explicit opt-out) | `0.0.11` | an unauthorized generated mutation → the `Not authorized to ...` error |
| WebSocket handshakes validate `Host` **and** `Origin`; established sockets revalidate the session actor | `0.0.15` | a hostile handshake is denied; a socket surviving an external logout closes `4403` on its next operation frame |

### The production GraphQL mount

The [transport deployment guidance](#transport-deployment-guidance) covers each knob; assembled, the production mount is:

```python
from graphql import NoSchemaIntrospectionCustomRule
from strawberry.extensions import AddValidationRules

from django_strawberry_framework import DjangoSchema, strawberry_config
from django_strawberry_framework.views import DjangoGraphQLView

schema = DjangoSchema(
    query=Query,
    mutation=Mutation,
    config=strawberry_config(),
    # A factory, not an instance: Strawberry deprecates passing extension
    # instances (one would be shared across every request).
    extensions=[lambda: AddValidationRules([NoSchemaIntrospectionCustomRule])],
)

urlpatterns = [
    path(
        "graphql/",
        DjangoGraphQLView.as_view(
            schema=schema,
            graphql_ide=None,            # no GraphiQL / Pathfinder HTML
            allow_queries_via_get=False, # POST-only
        ),
    ),
]
```

Disabling introspection narrows reconnaissance — it is **not** an authorization boundary. `__typename` still answers (the rule's scope is `__schema` / `__type`), field names leak through error messages, and a client that already knows the schema loses nothing. Row visibility and permission classes remain the boundary whether or not introspection is served. The whole recipe is exercised as one unit by the live transport suite, so it is a supported configuration, not a suggestion.

**CORS.** The package adds no CORS headers and needs none for same-origin use — the strongest configuration is not installing CORS middleware on this endpoint at all. If cross-origin browser clients are real, scope the middleware precisely: explicit origins (never `*` with credentials), only the headers the client sends, and keep in mind that a permissive credentialed CORS policy re-opens exactly the cross-site request class that CSRF protection and JSON-preflight behavior otherwise close.

**Edge cache and rate limiting.** Mark the GraphQL location uncacheable at the edge (an authenticated POST endpoint has nothing safely shareable; the `Vary: Cookie` detail is under [Transport deployment guidance](#transport-deployment-guidance)) and rate-limit it there too — the resource budget above bounds what one operation may cost, not how many operations a client may send.

### Relay GlobalIDs are encodings, not capabilities

A `GlobalID` is an addressing scheme. Under the default `model` strategy it decodes to a Django model label and a predictable primary key (`products.item:42`), and any client can mint the ID of any row by guessing small integers. That is by design: possession of a `GlobalID` **must never be treated as permission**. The authorization boundary is the type's visibility policy (`get_queryset` and the permission surface) — node refetch, connections, and generated mutations all locate through it, and hidden rows collapse to `null` indistinguishably from missing ones. If application code accepts a `GlobalID` from a client and touches the ORM with it directly, it has stepped around that boundary and owns the check itself.

### Uploads: the package bounds bytes, the deployment owns content

With `multipart_uploads_enabled=True`, the package bounds what it can see: the declared multipart request size (`413` before Django's parser runs), and the resource budget's upload count / per-file bytes / aggregate bytes. Everything about the *content* of an accepted file is a deployment responsibility, exactly as it is for any Django file upload:

- extension / content-type / magic-byte validation, and malware scanning or quarantine where the threat model calls for it;
- storage permissions and a storage location that is never served as executable content;
- `Content-Disposition: attachment` (or an equivalent sandboxed domain) on downloads a browser can reach, so a stored HTML/SVG file cannot become stored XSS on your origin;
- signed or private URL policy on the storage backend, plus Django's `DATA_UPLOAD_MAX_NUMBER_FILES` / `FILE_UPLOAD_MAX_MEMORY_SIZE` and the proxy-level body cap from the transport section.

### File output metadata is data you are publishing

Of the default file/image output, `name` is the **storage object key** — under many storage layouts it embeds user-supplied filenames, upload paths, or tenant conventions, so treat it as application data with the same scrutiny as any other exposed column. `url` is whatever the storage backend builds: public and permanent on some backends, signed and expiring on others — know which yours is before a client caches it. The absolute filesystem `path` is [opt-in per column](#file-and-image-output-the-filesystem-path-is-opt-in) and should stay unset for remote clients.

### Login and registration are anonymous surfaces — throttle them

`login_mutation()` / `register_mutation()` default to `AllowAny` (the documented inversion of the write family's deny-by-default), the framework adds [no brute-force protection](#enumeration-posture), and the login gate receives the attempted username but never the password. Throttling is deliberately consumer-owned; the smallest real gate is a permission class over Django's cache:

```python
from django.core.cache import cache

from django_strawberry_framework.auth import login_mutation


class LoginAttemptThrottle:
    """At most 5 login attempts per username per 5 minutes, fail-closed."""

    def has_permission(self, info, mutation, operation, data, instance=None):
        key = f"login-attempts:{data['username']}"
        if cache.add(key, 1, timeout=300):
            return True
        return cache.incr(key) <= 5


class Mutation:
    login = login_mutation(permission_classes=[LoginAttemptThrottle])
```

A cache-keyed counter is a floor, not a ceiling — it resets on cache eviction and counts attempts, not outcomes. A deployment that needs lockout, per-IP dimensions, or audit trails should reach for its existing rate-limiting middleware at the edge and keep this gate as defense in depth.

### The example project is a fixture, never a deployment

`examples/fakeshop/` exists to exercise the package: `DEBUG=True`, a checked-in `SECRET_KEY`, GraphiQL, the debug toolbar, multipart uploads, and intentional `permission_classes = []` demonstrations are all deliberate. It must never be deployed, and it cannot be made production-ready by editing its settings — its settings module refuses to load with `DEBUG` off (`ImproperlyConfigured`, pinned by a test), precisely so the most likely accident fails loudly instead of shipping the rest of the fixture. Build a separate project and copy the mount recipe above, not the fakeshop settings.

## Form mutation contracts

The two form mutation bases intentionally return different payload shapes. A model-backed `DjangoModelFormMutation` returns the same object payload as `DjangoMutation`: the saved object in `node` or `result`, plus `errors`. A model-less `DjangoFormMutation` has no object slot and always returns exactly `ok: Boolean!` and `errors: [FieldError!]!`; validation or write failure sets `ok` to `false`, while success sets it to `true`. See the [`DjangoFormMutation`][glossary-djangoformmutation] and [`DjangoModelFormMutation`][glossary-djangomodelformmutation] contracts.

A `DjangoModelFormMutation` update is partial only at the GraphQL input boundary. The resolver reconstructs omitted fields from the current instance and binds a complete `ModelForm`, so Django revalidates every declared form field. If an untouched stored value no longer satisfies the form -- for example, after a validator is tightened -- the mutation fails without writing the requested change. Send a valid replacement for that field in the same request; if `Meta.fields` / `Meta.exclude` removed it from the generated input, broaden the mutation input or repair the row out of band first.

## Model mutation write contracts

`DjangoMutation` authorizes before decoding relation IDs. For updates and deletes,
the target row is first located through the target type's `get_queryset`; a hidden
row is therefore not-found before authorization can reveal that it exists.
Permission denial then raises a top-level `GraphQLError` and nulls the mutation
field. It is not returned in the payload's typed `errors` list, which is reserved
for relation decoding, validation, and database-constraint failures.

Relation visibility exists only when the related model has a registered primary
`DjangoType`. Global IDs and raw primary keys for such targets are resolved through
that type's `get_queryset`, so hidden and missing rows produce the same field-keyed
relation error. If the related model has no registered primary type, there is no
GraphQL visibility policy to apply: raw primary keys are existence-checked through
the model's default manager, and any existing row may be attached. Do not assume
that a target model's application-level visibility rules protect a relation unless
those rules are implemented by its registered primary type.

Many-to-many inputs use replace semantics. Providing a list on create or update
sets the complete membership to exactly that list; omitted members are removed.
An empty list clears the relation, omitting the field leaves it unchanged on
update, and explicit `null` is a field error. There is no additive `add` / `remove`
input shape.

After a successful write, the payload object is re-fetched through the model's
default manager rather than the target type's visibility-scoped queryset. This is
intentional: the actor can round-trip the row it just wrote. Consequently, an
update that moves a previously visible row outside the actor's `get_queryset`
scope still returns that row in the success payload; subsequent read operations
apply normal visibility and may no longer return it.

### Concurrency: row locks and the `conflict` error

Every model-backed mutation flavor defaults to `Meta.select_for_update = True` (as of the `0.0.14` work on `main`): the update / delete locate and every FK / M2M relation-target check acquire a `SELECT ... FOR UPDATE` inside the write transaction. The lock rides the model's **base manager** constrained by the visibility queryset reduced to a primary-key subquery — never `select_for_update()` attached to a custom `get_queryset` result, whose joins, unions, or annotations could not legally carry the lock. On a backend without `FOR UPDATE` support (SQLite) Django skips the clause silently. An explicit `Meta.select_for_update = False` opts into weaker concurrency.

A row that disappears mid-operation anyway — a concurrent delete under the opt-out or on a lockless backend — is never a silent success or a resurrecting insert. Direct model updates save with `force_update=True`; a zero-row forced update, a delete whose target row was already gone, and a missing post-write re-fetch all return the in-band `FieldError` on `id` with code `conflict` (retryable, distinct from `not_found`), and the transaction rolls back. Every error envelope marks the transaction for rollback, so visibility-hook or custom-`delete()` side effects never outlive a failed operation.

### One write alias; no distributed transactions

The database router's write alias is resolved once per operation and the whole pipeline — locate, relation visibility checks, validation, the write, M2M assignment, the re-fetch, and rollback — is pinned to it. A custom `get_queryset` hook that explicitly re-routes to a different alias (`.using("other")`) fails closed with a `ConfigurationError`, as does an instance-sensitive router whose answer changes once the row is known: the package offers single-transaction atomicity on one alias and will not pretend to coordinate a cross-database write.

### Authorization is a point-in-time decision

`check_permission`, each `Meta.permission_classes` entry, and `user.has_perm` run exactly once per operation — after the target row is located and locked, before relation decoding — and must return an actual `bool` (a truthy non-bool return is a `ConfigurationError`, never a silent allow). The decision is point-in-time: a permission revoked by a concurrent transaction after the check is not re-observed. A custom policy that needs revocation-linearizable behavior must lock or re-read its own policy rows inside the transaction from its permission class. Side-effectful hooks are not re-run. Because the transaction now spans response completion, any external effect (email, webhook, queue publish) triggered by a mutation must be scheduled with `transaction.on_commit(...)`, never fired inline.

## Serializer mutation contracts

`SerializerMutation`'s construction hooks are hardened (an intentional pre-`1.0` security break, no compatibility shim): `get_serializer_kwargs` is **constructor-only**. The framework builds the serializer's `data` itself from the decoded client input plus the declared injection, locates and authorizes the update `instance`, injects `partial=True` on update, and sets `context["request"]` (the authorized actor's request) and `context["write_alias"]` (the pinned write alias) — all five are framework-owned. Consumer hooks never receive the live located instance: every hook (`get_serializer_kwargs`, `get_serializer_injected_data`, `get_serializer_save_kwargs`) takes a frozen `SerializerHookContext(operation, write_alias, instance_pk)` plus an **immutable data view** — dicts as read-only mapping proxies, lists and tuples as tuples, sets as frozensets, `bytearray` as `bytes`, and each uploaded file replaced by a frozen `UploadMetadata(name, size, content_type)` descriptor, so the stateful authoritative upload objects reach only the serializer's own validation. Genuinely-immutable scalar leaves (str, int, `Decimal`, `datetime`, `UUID`, …) pass through by reference; an opaque, possibly-mutable leaf with no immutable rendering **fails closed** with a `ConfigurationError` rather than being aliased under a false promise of immutability (a hook could otherwise mutate it and thereby mutate the authoritative data). The reserved returns are checked by omission-sentinel plus object identity, never deep equality (a deep comparison recurses on deep valid payloads, and a plain `pop` default would make an explicit `None` indistinguishable from omission) — a returned `data` must be omitted or the exact frozen object the hook received, and *any* returned `instance` key is rejected outright (the framework injects the authorized row itself); anything else — an explicit `data=None`, a rebuilt-equal copy, any `partial`, a different `context["request"]` object, a conflicting `context["write_alias"]` — is a `ConfigurationError` before any write. The previous behavior let an override replace the located, authorized row or the decoded client data, which was an authorization bypass.

Narrowing a required field out of a create input pairs `Meta.injected_fields` with `get_serializer_injected_data(info, *, data, hook_context)`: its returned keys must exactly match the declaration (missing or extra keys fail loud), and every declared field must be writable on the same schema-time basis used by input generation (`read_only` and `HiddenField` entries are rejected). An injected field must also be narrowed out of the GraphQL input. `get_serializer_save_kwargs` may carry **only non-model custom arguments**: a key colliding with the serializer's actual `validated_data` (renamed `source=`, injected, defaulted, and `HiddenField` keys included) or naming *any* model field is rejected — model-field injection goes exclusively through the declared, validated, visibility-checked `Meta.injected_fields` channel. A writable serializer `source` must be unique across the whole write surface (input fields and `Meta.injected_fields`): the shared collision detector rejects two differently-named fields feeding one model attribute at class creation, since DRF resolves the collision last-write-wins and an injected value could silently replace the client's. A whole-object `source="*"` writable field is rejected outright — it owns no single key, so DRF merges its returned mapping into `validated_data` and it could overwrite any client or injected key; the model-column converter only catches an *exposed* star field, so the runtime-field guard additionally rejects narrowed-out, `HiddenField`, or defaulted `source="*"` fields that never reach the converter. The frozen data views are built iteratively: client-controlled JSON nesting depth cannot crash the pipeline with a `RecursionError`, a cyclic container fails loud as a `ConfigurationError` instead of looping forever, and a merely shared (diamond) reference freezes once and stays shared. The DRF error flattener is iterative, cycle-rejecting, and budget-capped the same way — pathological error fan-out ends in a single `"__all__"`-keyed `truncated` marker.

The pipeline is phase-separated. Every consumer-reachable phase — the permission hook, relation decode, validation with author validators, the hooks, and save-kwargs preparation — is **database-read-only**: the pipeline-wide alias guard (shared by all three write flavors, delete included) rejects every SQL statement on a non-pinned configured connection with no read/write classification (a lexical keyword test is bypassable via leading SQL comments, PostgreSQL `EXPLAIN ANALYZE UPDATE`, and write-capable functions invoked through `SELECT`), and rejects write-shaped SQL on the *pinned* connection outside the flavor's write phase (there the conservative comment-stripped allow-list is phase-ordering enforcement, not the atomicity boundary — a false negative still rolls back with the pinned transaction). Writes are permitted only inside the flavor's save step (`serializer.save()`, `Model.save()` + the M2M assignment, `form.save()`, `instance.delete()`); side effects belong in `transaction.on_commit(...)`. The guard is thread-scoped, and grants exactly one narrow, phase-scoped exception: a dedicated authorization phase wraps only the single permission-evaluation call and permits statements on the explicitly identified auth aliases (the router's read answer for the user model, `auth.Permission` / `Group`, and `contenttypes`), so a divergent read/write router that keeps auth off the write alias can resolve the user and permission set. The boundary there is transactional and database-enforced, not lexical — each non-pinned auth alias runs inside a transaction placed in a backend-enforced read-only mode (PostgreSQL `SET TRANSACTION READ ONLY`, SQLite `PRAGMA query_only` — read and restored to its prior value on exit, so a pre-existing setting or an enclosing barrier survives) and unconditionally rolled back when the phase ends, so an *ordinary* write a permission backend attempts on it is refused by the database itself and discarded on rollback. Forced rollback alone is not a portable barrier even against ordinary writes — non-transactional tables and implicitly-committed DDL can escape it — so a backend that cannot provide the read-only guarantee fails closed (the pipeline raises rather than route auth there), with the forced rollback kept as additional containment. This is *not* a complete sandbox against a hostile permission backend: backend read-only mode is a high-level restriction that still permits side-effecting functions (PostgreSQL `nextval`/`setval` advance a sequence and are never rolled back; a session-scope advisory lock outlives the transaction). The security model therefore **trusts permission backends to perform reads only** — the barrier contains ordinary/accidental writes as defense-in-depth, not deliberate volatile side effects; a deployment that cannot make that trust assumption must give divergent-router authorization genuinely capability-restricted database credentials. The exception closes the instant authorization returns — decode, hooks, and validation cannot reach the auth alias, and evaluating permissions there fills the per-user cache as a side effect. It is gated on the mutation declaring permission classes: the explicit `permission_classes = []` opt-out grants no auth-alias access and never resolves the lazy user. `serializer.save()` runs inside its own savepoint, rolled back *before* a caught DRF/Django `ValidationError` or `IntegrityError` converts into the `FieldError` envelope — a custom `save()` that wrote rows and then raised leaves no partial write.

The authorized target is protected end to end. Its canonical pk **and** loaded concrete field values are snapshotted immediately after the locked locate — before the permission hook, the first consumer-controlled code, can touch the mutable instance — and published on the write-pipeline context; immediately before the save, the serializer flavor rejects any in-memory drift of the located row (permission methods, hooks, and validators must treat the target as read-only). Mutable container values (`JSONField`/`ArrayField`) are snapshotted as iterative structural fingerprints and a `FieldFile` by its database-relevant `name` string — not aliased by reference — so an in-place mutation (`instance.data["x"] = …`, `instance.file.name = …`) on the same object is still detected as drift. Pk equality everywhere goes through the model pk field's own `to_python` canonicalization, never string comparison (a `UUID` pk spells the same row several ways; a forged pk of the wrong shape reads as a mismatch). After authorization — never before — the write step snapshots the target's write-surface direct-M2M memberships. Every top-level and nested DRF relation field's queryset is scoped to the author's own queryset AND the target type's visibility, pinned to the operation's write alias, and locked when `Meta.select_for_update` locks; queryset-backed DRF validators are shallow-copied per request and pinned recursively as well. On top of that scoping sits the **relation-intent ledger**: each relation field's `run_validation()` return (top-level and nested, one record per `many=True` list item, custom `pk_field` implementations included) is recorded before field- or object-level validators can replace it, and the final `validated_data` must carry those exact objects by identity — covering renamed sources, injected fields, single relations, lists (length + pairwise identity, so DRF's duplicate and explicit-empty-list set semantics pass through), and nested paths; a validator may reject or pop a relation, never substitute or inject one. After the save, the returned top-level row is **attested against the database**: every supplied FK/OneToOne column is read back and must hold the validated target's pk, every supplied M2M must match the validated pk set (explicit `[]` means cleared; duplicates collapse per DRF `.set()` semantics), and every omitted partial-update M2M on the write surface must equal its pre-save snapshot — a custom `create()`/`update()` that ignored or replaced validated relations is a loud `ConfigurationError`, never a plausible payload (arbitrary same-alias behavior inside custom write code otherwise remains trusted). The serializer write phase additionally runs under a thread-scoped write witness recording every actual write of the backing model with a pk snapshot taken at the `post_save` signal; the `serializer.save()` result must be `serializer.instance` itself, a persisted instance of the backing model (non-null pk, not `_state.adding`) living exactly on the pinned alias, matching a witnessed `created=True` write on create or the immutable authorized-pk snapshot on update (enforced again by a flavor-independent backstop, and by the delete branch for pk drift during authorization). Returning the existing instance without saving it is rejected rather than reported as a successful no-op. Custom serializer code that queries should use `context["write_alias"]`.

## Filter membership semantics

For `ListFilter` and Relay-aware `GlobalIDMultipleChoiceFilter` membership lookups, an explicit empty list means membership in the empty set and therefore matches no rows. Omitting the filter or sending `null` remains the no-constraint form. An excluded empty membership predicate matches every row.

Generated integer `in` filters coerce every member through the Django model field before binding it to the database. Members that fail model-field coercion or range validation are discarded; a mixed list filters on its valid members, while a non-empty list whose members all fail validation matches no rows. This prevents an invalid or out-of-range integer from reaching the backend without widening an all-invalid restrictive filter into an unfiltered query.

Generated flat filter paths that cross a reverse foreign key or many-to-many relation automatically apply `distinct`, so multiple matching related rows cannot duplicate a parent in list or connection results.

## Development debug responses

### django-debug-toolbar middleware

The optional `DebugToolbarMiddleware` integrates Strawberry's Django view with
`django-debug-toolbar`. Install `django-debug-toolbar>=7.0.0`, then wire the
toolbar's normal prerequisites with one package-specific replacement:

```python
from debug_toolbar.toolbar import debug_toolbar_urls

INSTALLED_APPS = [
    # ...
    "django.contrib.staticfiles",
    "debug_toolbar",
    "django_strawberry_framework",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django_strawberry_framework.middleware.debug_toolbar.DebugToolbarMiddleware",
    # ...
]

INTERNAL_IPS = ["127.0.0.1"]

urlpatterns = [
    # ...
]
urlpatterns += debug_toolbar_urls()
```

The package middleware **replaces**
`"debug_toolbar.middleware.DebugToolbarMiddleware"`; never list both, because
the subclass already runs the stock toolbar pipeline and stacking them runs it
twice. Keep `debug_toolbar_urls()` in the URLconf while the middleware is
active: the stock postprocessor reverses its panel routes for every processed
response, so omitting them raises `NoReverseMatch` rather than merely breaking
panel links.

The integration inherits the stock toolbar's `DEBUG`,
`SHOW_TOOLBAR_CALLBACK`, and `INTERNAL_IPS` gating. Injection is view-scoped,
not GraphiQL-client-scoped: whenever that gate enables the toolbar, every JSON
response from a Strawberry Django view except an `IntrospectionQuery` gains a
top-level `debugToolbar` key, including responses to programmatic clients. The
GraphiQL bridge removes the key only inside the IDE. Consequently this remains
a development-only integration; production exposure requires the stock toolbar
to be misconfigured to run there. If a tagged response declares
`application/json` but contains malformed or undecodable content, the package
performs no package-specific body or `Content-Length` rewrite.

See the [Debug-toolbar middleware glossary entry][glossary-debug-toolbar-middleware]
for the complete import, template, and failure-mode contract.

### GraphQL response extension

`DjangoDebugExtension` is an opt-in development diagnostic imported from `django_strawberry_framework.extensions`. Pass the **class**, not a constructed instance, in Strawberry's `extensions=` list:

```python
from django_strawberry_framework.extensions import DjangoDebugExtension

_optimizer = DjangoOptimizerExtension()
schema = strawberry.Schema(
    query=Query,
    config=strawberry_config(),
    extensions=[
        lambda: _optimizer,
        DjangoDebugExtension,
    ],
)
```

Strawberry constructs the class with zero arguments for every operation, keeping its capture state operation-local. A pre-constructed instance is deprecated engine usage and would share the engine-assigned execution context and completed payload across operations; the optimizer intentionally uses the different singleton-in-a-factory shape to retain its plan cache.

Executed operations add `extensions["debug"]` with `sql` and `exceptions` lists. The extension brackets every configured Django database connection separately and aggregates rows from every alias used during the operation into that one `sql` list; each row's `alias` and `vendor` identify its source. Rows retain per-connection log order and the per-connection groups follow Django's `connections.all()` order, so the combined list is not a cross-database execution timeline. An alias the operation never uses contributes no rows and is not forced open.

Never enable this extension on an internet-facing production schema: it returns interpolated SQL values and unmasked exception messages and tracebacks.

**It fails closed if you do.** At operation start the extension reads `settings.DEBUG`; when it is false and the deployment has not acknowledged the disclosure, the extension withholds the whole payload — it acquires no debug cursor, snapshots no query log, publishes no `debug` key — and logs one warning naming the misconfiguration. The operation itself runs normally, because a diagnostic that refuses to disclose must not also refuse the request. Documentation is not a guard for a feature whose purpose is to publish secrets; this is.

If you have a controlled reason to run it with `DEBUG` off, say so explicitly. The factory form is what keeps the fresh-per-operation instance:

```python
extensions=[
    lambda: DjangoDebugExtension(allow_unsafe_production=True),
]
```

The payload is also **capped**, deterministically: at most 100 SQL rows and 25 exception rows (earliest kept), each row's SQL text cut at 4096 characters, exception messages at 4096 and tracebacks at 16384, every cut marked with `... [truncated]`, and one shared 262144-character budget spent on exception rows before SQL rows. Both lists are always present whether or not a cap bit, so the wire contract is unchanged. The caps are package invariants, not settings: a deployment that wants a different ceiling is a deployment running this extension in production.

See the [`DjangoDebugExtension` glossary entry][glossary-djangodebugextension] for the complete payload and lifecycle contract.

## Testing GraphQL endpoints

Import the sync or async HTTP helper from `django_strawberry_framework.testing`. Both drive
Django's in-process test client, decode the GraphQL response, and return a typed
`Response` carrying `errors`, `data`, `extensions`, and the raw Django response:

```python
from django_strawberry_framework.testing import TestClient


def test_items():
    response = TestClient().query("{ allItems(first: 1) { edges { node { name } } } }")

    assert response.errors is None
    assert response.response.status_code == 200
```

Endpoint selection follows this precedence order:

1. Per-call `query(..., url=...)`.
2. `TestClient(path=...)` / `AsyncTestClient(path=...)`.
3. `GraphQLTestMixin.GRAPHQL_URL` for the unittest family.
4. `DJANGO_STRAWBERRY_FRAMEWORK["TESTING_ENDPOINT"]`.
5. `"/graphql/"`.

The constructor and class-attribute rungs belong to their respective client flavors; both
outrank the project setting, and a per-call URL outranks every stored choice without mutating
it.

The two flavors intentionally have different error-assertion defaults. `TestClient.query()`
and `AsyncTestClient.query()` default to `assert_no_errors=True` and raise `AssertionError`
when the GraphQL response carries `errors`. `GraphQLTestMixin.query()` defaults to
`assert_no_errors=False`, returning the response so unittest-style tests can call
`assertResponseNoErrors()` or `assertResponseHasErrors()`. Pass the flag explicitly when a
test switches styles.

An endpoint typo is a transport misconfiguration, not a GraphQL error. The client deliberately
does not wrap it: Django returns an HTML 404, then `response.json()` raises `ValueError` naming
the non-JSON `Content-Type`. If the response declares JSON but contains malformed JSON,
`json.JSONDecodeError` surfaces instead. Check the endpoint and URLconf rather than catching
either error as an application-level GraphQL result.

See the [`TestClient`][glossary-testclient] and
[`GraphQLTestCase`][glossary-graphqltestcase] glossary entries for multipart uploads,
authentication brackets, async usage, and the complete unittest-family contract.

## Running the example project

The repository ships with a fakeshop example project that exercises the shipped surface against a real Django app.

```shell
# Apply migrations to the example app
uv run python examples/fakeshop/manage.py migrate

# Start the dev server (admin + GraphiQL at /graphql/)
uv run python examples/fakeshop/manage.py runserver
```

The dev landing page at `/` links to GraphiQL, the admin, and the seed/delete query-param triggers. For the full example walkthrough see [`../examples/fakeshop/README.md`][fakeshop-readme].

### Seeding the example database

The fakeshop example dynamically discovers **all** Faker providers at runtime and seeds the database accordingly. The command is idempotent — it ensures at least N items exist per provider and only creates the shortfall.

```shell
# Ensure 5 items per provider (default)
uv run python examples/fakeshop/manage.py seed_data

# Ensure 50 items per provider
uv run python examples/fakeshop/manage.py seed_data 50

# Delete the first 10 items (and their cascading entries)
uv run python examples/fakeshop/manage.py delete_data 10

# Delete all items and entries
uv run python examples/fakeshop/manage.py delete_data all

# Wipe all four tables (Category, Property, Item, Entry)
uv run python examples/fakeshop/manage.py delete_data everything
```

The same actions are reachable from the admin via query-param triggers — see the dev landing page at `/` for clickable links.

### Test users

Create test users with individual Django `view_*` permissions for exercising `get_queryset` permission branches. Each set creates 6 users: 1 staff, 1 regular (no perms), and 4 per-model permission users (`view_category`, `view_item`, `view_property`, `view_entry`). All share password `admin`. Superusers are never deleted.

```shell
# Create 1 set of test users (6 users)
uv run python examples/fakeshop/manage.py create_users

# Create 3 sets (18 users)
uv run python examples/fakeshop/manage.py create_users 3

# Delete all non-superusers
uv run python examples/fakeshop/manage.py delete_users all

# Delete the first 5 non-superusers
uv run python examples/fakeshop/manage.py delete_users 5
```

### Sharded mode (multi-DB)

The example ships with an additive two-alias layout for exercising multi-database scenarios. Toggle the secondary shard via `FAKESHOP_SHARDED=1`:

```shell
# Materialize the secondary shard SQLite file (idempotent)
FAKESHOP_SHARDED=1 uv run python examples/fakeshop/manage.py seed_shards

# Larger seed for stress testing
FAKESHOP_SHARDED=1 uv run python examples/fakeshop/manage.py seed_shards --count 5000
```

In sharded mode `default` keeps pointing at `db.sqlite3` (same file as single-DB mode) and `shard_b` adds `db_shard_b.sqlite3`. The two modes share the same `default` file, so a single dev workflow (`manage.py seed_data`, etc.) populates the default alias either way; the sharded mode only ADDS the secondary shard. The committed `db_shard_b.sqlite3` ships with a minimal seed via `seed_shards` so the sharded mode works out of the box.

For the cooperation contract these shards run against — explicit `.using()` `_db` preservation, FK-id elision router hints, consumer-provided `Prefetch(queryset=…)` alias round-trips, and strictness-mode behavior under non-default aliases — see [`GLOSSARY.md#multi-database-cooperation`][glossary-multi-database-cooperation].

## Using the package in your own project

If you want to develop against a local checkout of this package from another Django project:

1. Go to the project you want to install the package in.
2. Add `django-strawberry-framework` to your `pyproject.toml` dependencies.
3. Point it at your local checkout:

```toml
# In your project's pyproject.toml
[tool.uv.sources]
django-strawberry-framework = { path = "../django-strawberry-framework", editable = true }
```

Then run:

```shell
uv sync
```

For status, the milestone roadmap, and contributor signposts, see [`../README.md`'s status section][readme-status] and [`../CONTRIBUTING.md`][contributing].

<!-- LINK DEFINITIONS -->

<!-- Root -->
[contributing]: ../CONTRIBUTING.md
[goal]: ../GOAL.md
[readme]: ../README.md
[readme-status]: ../README.md#status
[today]: ../TODAY.md

<!-- docs/ -->
[glossary]: GLOSSARY.md
[glossary-apply-cascade-permissions]: GLOSSARY.md#apply_cascade_permissions
[glossary-auth-mutations]: GLOSSARY.md#auth-mutations
[glossary-debug-toolbar-middleware]: GLOSSARY.md#debug-toolbar-middleware
[glossary-djangoconnectionfield]: GLOSSARY.md#djangoconnectionfield
[glossary-djangodebugextension]: GLOSSARY.md#djangodebugextension
[glossary-djangoformmutation]: GLOSSARY.md#djangoformmutation
[glossary-djangographqlprotocolrouter]: GLOSSARY.md#djangographqlprotocolrouter
[glossary-djangolistfield]: GLOSSARY.md#djangolistfield
[glossary-djangomodelformmutation]: GLOSSARY.md#djangomodelformmutation
[glossary-djangomutation]: GLOSSARY.md#djangomutation
[glossary-djangonodefield]: GLOSSARY.md#djangonodefield
[glossary-filterset]: GLOSSARY.md#filterset
[glossary-graphqltestcase]: GLOSSARY.md#graphqltestcase
[glossary-inspect-django-type]: GLOSSARY.md#schema-introspection-management-command
[glossary-metaglobalid_strategy]: GLOSSARY.md#metaglobalid_strategy
[glossary-metanullable_overrides]: GLOSSARY.md#metanullable_overrides
[glossary-metarelation_shapes]: GLOSSARY.md#metarelation_shapes
[glossary-multi-database-cooperation]: GLOSSARY.md#multi-database-cooperation
[glossary-orderset]: GLOSSARY.md#orderset
[glossary-plan-cache]: GLOSSARY.md#plan-cache
[glossary-relay-node-integration]: GLOSSARY.md#relay-node-integration
[glossary-schema-export-management-command]: GLOSSARY.md#schema-export-management-command
[glossary-serializermutation]: GLOSSARY.md#serializermutation
[glossary-testclient]: GLOSSARY.md#testclient
[glossary-upload-scalar]: GLOSSARY.md#upload-scalar

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->
[fakeshop-readme]: ../examples/fakeshop/README.md

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
[django-csrf]: https://docs.djangoproject.com/en/5.2/howto/csrf/
[django-deploy-checklist]: https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/
[django-test-client-csrf]: https://docs.djangoproject.com/en/5.2/topics/testing/tools/#the-test-client
