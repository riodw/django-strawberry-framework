# Foundation slice: [definition-order independence][glossary-definition-order-independence]

Deliberation, rejected alternatives, and this spec's change record live in the companion file [`spec-010-foundation-0_0_4-rationale.md`][spec-010-rationale]: why the source-line-reference convention was retired rather than refreshed, why the surviving third-party line citations are not debt, why two citations naming since-retired symbols were kept as history instead of repointed, and — for every contract below that a later card or spec reshaped — what this document used to claim, which change replaced it, and which alternative that change rejected.

## Purpose
This document is the implementation contract for the 0.0.4 foundation slice. It is the single source of truth for what ships in this release. It is intentionally narrower than the broader design specs:
- [`docs/SPECS/spec-008-definition_order_independence-0_0_4.md`][spec-008] discusses the relation-resolution problem space and prior art at length. This spec narrows that into one shippable slice and resolves the open design questions raised there.
- [`docs/SPECS/spec-009-rich_schema_architecture-0_0_4.md`][spec-009] describes the long-term architecture (filters, orders, aggregates, connections, permissions, custom field classes). This spec implements only the type/registry/finalization layer that everything in that document later sits on top of.
This file should be read on its own and is feature-complete for the foundation slice. Where it borrows directly from the broader specs, the reference is explicit.

## What ships
The foundation slice ships six things and only six things:
1. A package-owned **type-definition object** (`DjangoTypeDefinition`) that becomes the canonical source of truth for everything the type, the optimizer, and future subsystems read.
2. A **pending-relation registry** so relations whose target is not yet declared do not break class creation.
3. A **finalization lifecycle** (`finalize_django_types()`) that resolves pending relations, attaches relation resolvers, and runs `strawberry.type(cls, ...)` once the registry is complete.
4. **Cyclic relation tests** for FK, reverse FK, OneToOne, reverse OneToOne, and M2M cardinalities.
5. **Fail-loud unresolved-target errors** that name the source model, source field, and target model.
6. The **optimizer continues to see concrete relation metadata** after finalization, with no regression to `walker.plan_relation` / `walker._plan_prefetch_relation` / `DjangoOptimizerExtension.check_schema`.

## What does not ship in this slice
The foundation slice deliberately skips:
- Custom Strawberry field class (`DjangoModelField`). Rich-schema spec layer 4. We keep today's `_attach_relation_resolvers` pattern.
- `DjangoSchema`, [`DjangoConnectionField`][glossary-djangoconnectionfield], [`DjangoNodeField`][glossary-djangonodefield]. Rich-schema spec layer 5+. The foundation only exposes the explicit `finalize_django_types()` entry point; no shipped helper wraps it — the explicit consumer call remains the only trigger.
- Filters, orders, aggregates, fieldsets, permissions, sentinel redaction, field-level optimizer stores. Rich-schema spec layers 6–11.
- Strawberry-Django's decorator API surface and `DjangoModelType` generic relation fallback.
- The rule for choosing among several [`DjangoType`][glossary-djangotype]s registered against one model. The registry's type map is many-valued so that layer sits on top of the foundation without reshaping it (see "TypeRegistry extensions"), but the [`Meta.primary`][glossary-metaprimary] declaration, the ambiguity audit that enforces it, and the resolution order `registry.get()` applies are `spec-018-meta_primary-0_0_6.md`'s contract, not this one's.
- The *scalar* half of the consumer-override contract. This spec pins the relation half (see "Manual annotation contract for relation fields" below): a consumer-supplied annotation on a relation field suppresses both placeholder synthesis and pending-relation recording, and a consumer-assigned Strawberry field additionally suppresses generated resolver attachment. Both halves feed one union, `DjangoTypeDefinition.consumer_authored_fields`, which is the single short-circuit the collection phase reads; what a scalar override means, and what the `auto` declare-but-infer marker means beside it, belong to `spec-019-consumer_overrides_scalar-0_0_6.md` and to the later `auto`-typed-annotation surface catalogued in `docs/GLOSSARY.md`. Validation that a consumer annotation matches the Django relation cardinality is deferred.
## Invariants this slice must protect
The following are the invariants every reviewer should test the design against. Any change that violates one of them is a rejected change.
- `[Meta.fields][glossary-metafields] = "__all__"` produces concrete rich related `DjangoType`s by default, regardless of declaration order.
- Schema shape never silently degrades based on import order.
- Unresolved exposed relation targets fail loud at finalization, not silently and not at class creation.
- The optimizer always sees concrete relation metadata after finalization; `registry.get(target_model)` returns the registered `DjangoType` for every relation field that survived selection.
- `registry.clear()` returns the package to a fully clean state; no test ever sees pending relations or finalized markers from a previous test.
- Calling `finalize_django_types()` twice is a no-op on the second call.
- A `DjangoType` whose `Meta` is omitted (intermediate abstract subclass) still skips the pipeline cleanly, exactly as today.
## Pre-implementation spikes (gate before code) — Phase 0
The biggest design risk is Strawberry finalization timing. Three throwaway scripts must run and produce passing assertions before any production code is written. Each lives in `scripts/spikes/`, is committed long enough for review, and is deleted once its conclusions are recorded in this spec and `README.md`.
This is **Phase 0** of the phased implementation order at the bottom of this document. The numbered phases (1+) start production code; Phase 0 is the gate that blocks them.
### Spike A: deferred `strawberry.type(cls)` and the real finalization boundary
Goal: prove that `strawberry.type(cls)` can be deferred from class creation to a later finalization function, and identify the *exact* call point at which `finalize_django_types()` must have run for a real schema build to succeed.
Pass criteria (all five must succeed):
1. Two `DjangoType` subclasses with cyclic relations declared in either order successfully build a schema after `finalize_django_types()` runs.
2. `info.return_type` resolution and `__strawberry_definition__` lookup work normally.
3. `strawberry.Schema(query=Query)` accepts the types without warnings.
4. **Boundary test (forward path)**: declare several `DjangoType`s without finalizing, call `finalize_django_types()`, **then** decorate a `@strawberry.type Query` class whose resolvers return `list[ItemType]`, then construct and execute the schema with a nested query. Pass when the response contains the expected nested data.
5. **Boundary test (reverse path)**: declare several `DjangoType`s without finalizing, decorate the `Query` class **before** `finalize_django_types()`, then call `finalize_django_types()`, then construct and execute. Document whether this raises, works, or stores enough lazy-annotation state to recover. Whichever it does becomes the canonical "earliest safe call point" written into `README.md`.
### Spike B: post-`__strawberry_definition__` patching
Goal: prove (or disprove) that calling `strawberry.type(cls)` at class creation with placeholder annotations and patching `__strawberry_definition__.fields` at finalization is safe.
Pass criteria: a passing or failing assertion. If Spike A passes cleanly, Spike B is documented as "not required" and Option B from `spec-008-definition_order_independence-0_0_4.md` #"### The finalization trigger" is closed out as rejected.
### Spike C: same-module forward references
Goal: confirm that `Annotated[T, strawberry.lazy("module.path")]` cannot be used as the default mechanism for cyclic relations in the same module (it requires a real importable path and breaks single-file examples).
Pass criteria: documented confirmation that `strawberry.lazy(...)` stays only as an *optional explicit escape hatch*, never as the default.
### Spike outcome (Phase 0 complete)
Spikes A–C ran successfully before production code began.
Spike A proved the foundation slice can use **Strategy 1: defer `strawberry.type(cls)` until finalization**. The prototype collected cyclic fakeshop `Category` / `Item` types in both declaration orders, resolved pending relations, called `strawberry.type(cls, ...)` during finalization, built a Strawberry schema without warnings, resolved `info.return_type`, and executed `{ allItems { name category { name } } }` with the expected nested data. The forward boundary passed: calling `finalize_django_types()` before decorating `Query` works. The reverse boundary also passed: decorating `Query` first, then calling `finalize_django_types()`, then constructing `strawberry.Schema(...)` works. The canonical required boundary for 0.0.4 is therefore **after every module defining `DjangoType` classes has been imported, and before `strawberry.Schema(...)` construction**. The README still recommends the earlier `finalize_django_types()`-before-`Query` pattern because it makes the setup boundary explicit.
Spike B confirmed that mutating `cls.__annotations__` after `strawberry.type(cls)` does not update Strawberry field metadata. Full `__strawberry_definition__` field patching is rejected as unnecessary because Spike A passed cleanly.
Spike C confirmed same-module string forward references work without `strawberry.lazy(...)`, while the correct list-of-lazy-target shape (`list[Annotated["Target", strawberry.lazy("module.path")]]`) requires a real importable module path. `strawberry.lazy(...)` remains an optional explicit escape hatch, not the default same-module strategy.

## Strawberry finalization strategy
Phase 0 confirmed the following strategy.
- `DjangoType.__init_subclass__` collects metadata only. It does **not** call `strawberry.type(cls)`.
- `finalize_django_types()` is the single point that resolves pending relations, attaches relation resolvers, and calls `strawberry.type(cls, ...)` for each registered type.
- **Earliest safe call point**: `finalize_django_types()` must run **after every module that defines `DjangoType` classes has been imported, and before `strawberry.Schema(...)` construction**. Spike A proved both orders around `@strawberry.type Query` are viable: the recommended setup calls `finalize_django_types()` before decorating `Query`, while the later-but-still-safe setup decorates `Query` first and finalizes before schema construction. Constructing `strawberry.Schema(...)` before finalization is the wrong-order failure mode documented in `docs/README.md`, which carries the correct and wrong-order snippets as a pair.
- **Lifecycle window**: `finalize_django_types()` must be called **once during single-threaded import / app / schema setup, before serving requests**. It is **not** safe to call from a request thread, an async resolver, or any concurrent context. The function mutates a process-global registry **and** mutates class objects (annotations, attached fields, `__strawberry_definition__`, `__django_strawberry_definition__`); the foundation slice's registry is intentionally lockless (see `registry.py::TypeRegistry`) and concurrent finalization can produce partial Strawberry definitions. This window is restated in `docs/README.md`.
- **Module discovery is the consumer's responsibility**: the foundation slice does not ship `apps.py`, autodiscovery, or any helper that imports project modules on the user's behalf. Every Python module that defines a `DjangoType` must be imported (directly or transitively) **before** `finalize_django_types()` runs. A `CategoryType` that exists in code but lives in a never-imported module will be reported as unresolved by the finalizer with the standard error format. The `docs/README.md` setup snippet shows the import boundary explicitly (e.g., `from myapp.types import *  # noqa: F401`) immediately before the finalizer call, alongside the note that a missing import is the most common production failure mode. Autodiscovery is a later-phase wrapper concern.
- No shipped helper auto-triggers finalization: `DjangoSchema`, `DjangoConnectionField`, and `DjangoNodeField` do not call `finalize_django_types()`; the explicit consumer call is the only trigger. The auto-trigger direction in `spec-009-rich_schema_architecture-0_0_4.md` #"### Layer 3: Finalization trigger" was not adopted. Any future helper that auto-triggers finalization must also enforce the single-threaded-setup window: either by being constrained to schema construction time, or by acquiring a real lock around the finalizer.
- `Annotated[..., strawberry.lazy("module.path")]` remains a documented optional override path for users who want a non-primary target type or who want to defer a relation across modules. It is not the default and not required for normal `Meta.fields = "__all__"`.
### Manual annotation contract for relation fields
For relation fields, the foundation slice pins this contract:
- **Annotation override**: if the consumer has supplied an annotation on the same Python name as a Django relation field (`items: list["ItemType"]`, `items: list[Annotated["ItemType", strawberry.lazy("module.path")]]`, etc.), the collection phase **skips both** placeholder synthesis and pending-relation recording for that field. The user's annotation is left untouched and flows through Strawberry's normal annotation handling at finalization time.
- **`strawberry.lazy` marker placement is load-bearing**: the marker must annotate the **target type itself**, inside the collection parameter — `list[Annotated["ItemType", strawberry.lazy("module.path")]]` for a to-many relation, `Annotated["ItemType", strawberry.lazy("module.path")] | None` for a nullable FK. Wrapping the collection instead (`Annotated[list["ItemType"], strawberry.lazy("module.path")]`) does not defer anything: Strawberry converts a lazy reference into a `LazyType` only when the annotated type is itself a `ForwardRef`, so in that position the marker is discarded and `"ItemType"` degrades to a plain string forward reference resolved against the declaring module's namespace. It therefore fails with `UnresolvedFieldTypeError` at `strawberry.Schema(...)` construction in exactly the cross-module case the escape hatch exists for, and appears to work only when the target was importable at module scope anyway.
- **Field / resolver override**: if the consumer assigns a Strawberry field or resolver to the same Python name (`items: list["ItemType"] = strawberry.field(resolver=custom_items)`, `@strawberry.field def items(...) -> list["ItemType"]`, or any pre-existing `cls.<field_name>` value that is not the default Django attribute), the collection phase records the field name on `DjangoTypeDefinition.consumer_assigned_relation_fields` and the **finalizer's resolver-attachment phase skips that field**. `_attach_relation_resolvers` must consult this set and `setattr(cls, field.name, ...)` only for relation fields the consumer did not assign. The consumer-assigned field/resolver wins; the finalizer never clobbers it.
- **Detection rule**: a relation field is treated as consumer-authored if either (a) `field.name` appears in the consumer's pre-collection `__annotations__`, or (b) `field.name` is present in `cls.__dict__` **and the value is a `StrawberryField`**. Any other class-attribute shadow of a selected Django field name is a `ConfigurationError` at class creation, naming the field and pointing at the two supported override forms — an annotation for a type override, `strawberry.field(resolver=...)` / `@strawberry.field` for a resolver override. The detection is positive rather than exclusionary on purpose: an "anything that is not Django's own descriptor" test admits every accidental shadow as a silent override and defers the failure to schema build, where it no longer names the field that caused it. The two sets are unioned into `consumer_authored_fields`, while `consumer_annotated_relation_fields` and `consumer_assigned_relation_fields` preserve the split for finalization.
- The finalizer **never** rewrites a relation annotation that was consumer-supplied and **never** attaches a resolver to a consumer-assigned relation field. Annotation-only overrides still receive generated relation resolvers.
- Validation that a consumer-supplied annotation matches the Django relation cardinality (`many_to_many` → `list[T]`, nullable FK → `T | None`, etc.) is **deferred**. The 0.0.4 contract is "trust the user's annotation; do not silently overwrite."
- Tests cover all four shapes:
  - annotation-only override (`items: list["ItemType"]`)
  - `list[Annotated["ItemType", strawberry.lazy("module.path")]]` cross-module override
  - explicit `strawberry.field(resolver=...)` assignment on a relation field
  - `@strawberry.field` decorator on a relation field
- The scalar branch is symmetric and is **not** this spec's contract. Collection detects consumer-annotated and consumer-assigned scalar fields with the same two rules, stores them on the definition as `consumer_annotated_scalar_fields` / `consumer_assigned_scalar_fields`, and folds them into the same `consumer_authored_fields` union — so `_build_annotations` short-circuits identically on both branches. What a scalar override is permitted to do to the package's scalar conversion is `spec-019-consumer_overrides_scalar-0_0_6.md`'s; the union is the seam between the two documents, and it is the only part of the scalar branch this spec asserts.
## Architecture (canonical, with pseudocode)
### `DjangoTypeDefinition`
Lives at `django_strawberry_framework/types/definition.py`. The single canonical place for per-type metadata. Replaces the current scatter of class attributes.
```python path=null start=null
@dataclass
class DjangoTypeDefinition:
    # Identity
    origin: type                              # the DjangoType subclass
    model: type[models.Model]
    name: str | None
    description: str | None
    # Selection (kept verbatim from Meta for diagnostics)
    fields_spec: tuple[str, ...] | Literal["__all__"] | None
    exclude_spec: tuple[str, ...] | None
    # Selected Django field objects, in iteration order. Stored alongside
    # field_map because resolver attachment, future DjangoModelField
    # construction, and several optimizer paths need real Django field
    # objects (attname, related_model.DoesNotExist, cardinality flags),
    # not just FieldMeta. FieldMeta is a precomputed projection;
    # selected_fields is the source of truth.
    selected_fields: tuple[Any, ...]          # tuple[models.Field | ForeignObjectRel, ...]
    # Field metadata. This object is the only store for both; nothing
    # mirrors them onto the class.
    field_map: dict[str, FieldMeta]           # the optimizer's canonical source
    optimizer_hints: dict[str, OptimizerHint]
    # Get-queryset signal — populated by the MRO-walking helper (see
    # collection pseudocode), not just by `"get_queryset" in cls.__dict__`,
    # so abstract bases that override get_queryset propagate the flag to
    # concrete subclasses. This is the definition-side reading; the
    # class-level `_is_default_get_queryset` sentinel remains the carrier
    # for classes that never reach a definition (see "Should redo now").
    has_custom_get_queryset: bool
    # Names of fields whose annotation OR Strawberry-field assignment was
    # supplied by the consumer (see "Manual annotation contract for
    # relation fields"). The collection phase stores the union and all
    # four split views: annotation-only overrides suppress placeholder
    # synthesis and pending-relation rewrites, while assigned Strawberry
    # fields/resolvers also suppress generated resolver attachment. The
    # union is the single short-circuit `_build_annotations` reads on
    # both its relation and its scalar branch.
    consumer_authored_fields: frozenset[str] = frozenset()
    consumer_annotated_relation_fields: frozenset[str] = frozenset()
    consumer_annotated_scalar_fields: frozenset[str] = frozenset()
    consumer_assigned_relation_fields: frozenset[str] = frozenset()
    consumer_assigned_scalar_fields: frozenset[str] = frozenset()
    # Forward-reserved slot: declared so its subsystem plugs in without
    # reshaping the dataclass, and `_validate_meta` still rejects the
    # matching Meta key, so consumers cannot set it.
    fields_class: Any | None = None
    # Lifecycle
    finalized: bool = False
```
The dataclass is an **extension point**, and later subsystems have taken it up. Each added slot is owned by the spec that shipped it, which is where its semantics are stated; this spec asserts only that they hang off this object rather than off scattered class attributes, and that adding one never reshapes the fields above:

| Slot | Owning spec |
|---|---|
| `interfaces` | `spec-015-relay_interfaces-0_0_5.md` |
| `primary` | `spec-018-meta_primary-0_0_6.md` |
| `filterset_class` | `spec-027-filters-0_0_8.md` |
| `orderset_class` | `spec-028-orders-0_0_8.md` |
| `connection` | `spec-030-connection_field-0_0_9.md` |
| `globalid_strategy`, `effective_globalid_strategy` | `spec-031-globalid_encoding-0_0_9.md` |
| `relation_shapes`, `relation_connections` | `spec-032-full_relay-0_0_9.md` |
| `cursor_field` | the `stable_cursor_field` keyset-cursor opt-in |

`aggregate_class` and `search_fields` are **not** slots. They stay in `DEFERRED_META_KEYS` — `_validate_meta` rejects them — and the dataclass carries nothing for them, because a reserved slot only earns its place when the shape it will hold is already known.
The instance is stored on the class as `cls.__django_strawberry_definition__` (mirrors strawberry-graphql-django's `__strawberry_django_definition__` at `strawberry_django/type.py:410`, kept namespace-distinct to avoid collisions).
Borrowed shape: `StrawberryDjangoDefinition` at `strawberry_django/type.py:425`. We do **not** borrow its `is_input` / `is_partial` / `is_filter` slots — those are mutation/input concerns out of foundation scope.
### `PendingRelation`
Lives at `django_strawberry_framework/types/relations.py` (new). Frozen so the registry can stash and iterate without aliasing bugs.
```python path=null start=null
@dataclass(frozen=True)
class PendingRelation:
    source_type: type                # the DjangoType subclass that owns the field
    source_model: type[models.Model]
    field_name: str                  # snake_case Django name, also the GraphQL key
    django_field: Any                # models.Field | ForeignObjectRel
    related_model: type[models.Model]
    relation_kind: Literal["forward_single", "many", "reverse_one_to_one"]  # mirrors utils.relations.RelationKind
    nullable: bool
```
This is the package's equivalent of Graphene-Django's `Dynamic` (`graphene/types/dynamic.py:7`) — the same idea (record now, resolve later) without the Graphene runtime, the `Dynamic` mounted-type machinery, or the silent-skip behavior at `graphene/types/schema.py:308-310`.
### `TypeRegistry` extensions
Lives at `django_strawberry_framework/registry.py`. Existing public methods stay.
```python path=null start=null
class TypeRegistry:
    def __init__(self) -> None:
        # The model map is many-valued: several DjangoTypes may register
        # against one model. Which of them a relation resolves to is
        # spec-018-meta_primary-0_0_6.md's rule, expressed through the
        # sibling _primaries map that spec owns; the foundation owns only
        # the shape that makes more than one registration representable.
        self._types: dict[type[models.Model], list[type]] = {}
        self._models: dict[type, type[models.Model]] = {}
        self._enums: dict[tuple[type[models.Model], str], type[Enum]] = {}
        # Maps for the foundation slice.
        self._definitions: dict[type, DjangoTypeDefinition] = {}
        self._pending: list[PendingRelation] = []
        self._finalized: bool = False
    # Carried over: register, get, model_for_type, iter_types,
    # register_enum, get_enum. register/get grew the primary-selection
    # keyword and the multi-type resolution order in
    # spec-018-meta_primary-0_0_6.md; both signatures are that spec's.
    # New API.
    def register_definition(self, type_cls: type, definition: DjangoTypeDefinition) -> None: ...
    def register_with_definition(
        self,
        model: type[models.Model],
        type_cls: type,
        definition: DjangoTypeDefinition,
        *,
        primary: bool = False,   # forwarded to register; spec-018's keyword
    ) -> None: ...
    def get_definition(self, type_cls: type) -> DjangoTypeDefinition | None: ...
    def iter_definitions(self) -> Iterator[tuple[type, DjangoTypeDefinition]]: ...
    def add_pending_relation(self, pending: PendingRelation) -> None: ...
    def iter_pending_relations(self) -> Iterator[PendingRelation]: ...
    def discard_pending(self, resolved: Iterable[PendingRelation]) -> None: ...
    def is_finalized(self) -> bool: ...
    def mark_finalized(self) -> None: ...
    # Post-finalization mutation guard, at the registry boundary. Every
    # mutator calls it; clear() is the single deliberate exception, so test
    # teardown can reset a finalized registry.
    def _check_mutable(self) -> None: ...
    # clear() is extended (not redone): beyond the three carried-over maps it resets
    # _definitions, _pending, and _finalized, and it runs every registered
    # type teardown and subsystem teardown first, so class-level artifacts
    # framework subsystems installed are undone before the maps are dropped.
    # Slots later specs added to the registry are reset here too, by the
    # spec that added them.
    def clear(self) -> None: ...
    # Deleted: lazy_ref. The placeholder NotImplementedError stub is removed
    # outright; see "Migration of current code" below.
```
**Registration is one atomic call.** `DjangoType.__init_subclass__` calls `register_with_definition(...)`, never `register(...)` followed by `register_definition(...)`. The pair must not be separable: a registration whose definition failed to attach leaves a type visible to relation resolution with no metadata behind it, and the failure surfaces later, somewhere else. `register_with_definition` snapshots the pre-call state, and if `register_definition` raises it rolls back **only what its own call added** — an idempotent re-registration of an already-stored type survives a failed re-register with a different definition intact.

**The post-finalization guard is stated twice, deliberately.** `__init_subclass__` rejects a new `DjangoType` after `finalize_django_types()` has run, and `_check_mutable` rejects the same class of mutation at the registry boundary. The second is not redundant: `__init_subclass__` only sees consumers who arrive through class creation, and any other route into the registry — a late import triggered from a request handler, a subsystem writing directly — would otherwise corrupt a finalized snapshot silently.
### Collection phase: `DjangoType.__init_subclass__`
`__init_subclass__` performs collection only. Pseudocode:
```python path=null start=null
def __init_subclass__(cls, **kwargs):
    super().__init_subclass__(**kwargs)
    # 1. MRO-aware custom get_queryset detection, and the sentinel stamp.
    #    Walks the new class's MRO so an abstract base that overrides
    #    get_queryset propagates the flag to concrete subclasses. Both
    #    lines run unconditionally, BEFORE the meta-is-None opt-out and
    #    before the finalized-registry guard, because an abstract base
    #    without Meta returns at step 2 and therefore never acquires a
    #    definition object to carry the flag on. The class attribute is
    #    the carrier for exactly that case; see "Should redo now".
    has_custom_get_queryset = _detect_custom_get_queryset(cls)
    cls._is_default_get_queryset = not has_custom_get_queryset
    # 2. Resolve Meta; intermediate abstract bases without Meta opt out.
    #    This branch must remain reachable AFTER finalization so abstract
    #    bases never trip the post-finalization guard below.
    meta = cls.__dict__.get("Meta")
    if meta is None:
        return
    # 3. Post-finalization registration guard. Concrete subclasses with
    #    Meta declared after finalize_django_types() ran are a programmer
    #    error: the schema has already been finalized and cannot accept
    #    new types. Tests recover by calling registry.clear() in their
    #    autouse fixture; production callers should never hit this.
    if registry.is_finalized():
        raise ConfigurationError(
            f"finalize_django_types() already ran; cannot register "
            f"{cls.__name__} after finalization. Call registry.clear() "
            f"first if this is a test."
        )
    # 4. Validate Meta.
    _validate_meta(meta)
    # 5. Select Django fields once, for reuse below.
    fields = _select_fields(meta)
    _validate_optimizer_hints_against_selected_fields(meta, fields)
    # 6. Pre-compute the field map and hints.
    field_map = {snake_case(f.name): FieldMeta.from_django_field(f) for f in fields}
    optimizer_hints = _meta_optimizer_hints(meta)
    # 7. Snapshot consumer-authored relation fields BEFORE we synthesize
    #    anything. A field is consumer-authored if either (a) the
    #    consumer pre-supplied an annotation on the same name, or (b)
    #    the consumer assigned a value (typically strawberry.field(...)
    #    or a @strawberry.field decorator result) on the same name. The
    #    union feeds DjangoTypeDefinition.consumer_authored_fields, while
    #    the split sets let finalization distinguish annotation-only
    #    overrides from assigned Strawberry field/resolver overrides.
    consumer_annotations = dict(cls.__dict__.get("__annotations__", {}))
    consumer_class_dict = cls.__dict__
    consumer_annotated_relation_fields = frozenset(
        f.name for f in fields
        if f.is_relation and f.name in consumer_annotations
    )
    consumer_assigned_relation_fields = frozenset(
        f.name for f in fields
        if f.is_relation and _is_consumer_authored_class_attr(consumer_class_dict, f.name)
    )
    consumer_authored_fields = frozenset({
        *consumer_annotated_relation_fields,
        *consumer_assigned_relation_fields,
    })
    # 8. Build annotations. Scalars resolve immediately. Every
    #    auto-synthesized relation defers UNCONDITIONALLY — the target's
    #    registration state at this moment is not consulted. A consumer-
    #    authored name is left alone on either branch.
    synthesized: dict[str, Any] = {}
    pending: list[PendingRelation] = []
    for field in fields:
        if field.is_relation:
            if field.name in consumer_authored_fields:
                # Consumer wins; do not synthesize, do not record pending,
                # and the finalizer's resolver-attachment phase will also
                # skip this field.
                continue
            pending.append(_record_pending_relation(cls, field))
            # Sentinel placeholder. Finalization rewrites this entry
            # before strawberry.type(cls) is called.
            synthesized[field.name] = _PendingRelationAnnotation
        else:
            synthesized[field.name] = convert_scalar(field, cls.__name__)
    # 9. Build the definition.
    definition = DjangoTypeDefinition(
        origin=cls,
        model=meta.model,
        name=getattr(meta, "name", None),
        description=getattr(meta, "description", None),
        fields_spec=getattr(meta, "fields", None),
        exclude_spec=getattr(meta, "exclude", None),
        selected_fields=tuple(fields),
        field_map=field_map,
        optimizer_hints=optimizer_hints,
        has_custom_get_queryset=has_custom_get_queryset,
        consumer_authored_fields=consumer_authored_fields,
        consumer_annotated_relation_fields=consumer_annotated_relation_fields,
        consumer_assigned_relation_fields=consumer_assigned_relation_fields,
    )
    # 10. Register early so later siblings can resolve us. One atomic
    #     call: a registration whose definition failed to attach must not
    #     be observable (see "TypeRegistry extensions").
    registry.register_with_definition(meta.model, cls, definition)
    for p in pending:
        registry.add_pending_relation(p)
    # 11. Stage annotations on the class. Consumer-declared annotations
    #     are merged on top so the consumer wins for any field name they
    #     explicitly annotated (relation OR scalar). Scalar override
    #     remains an implementation detail with the same warning as
    #     today; relation override is the documented contract above.
    cls.__annotations__ = {**synthesized, **consumer_annotations}
    # 12. Stash the definition on the class for fast lookup. It is the
    #     ONLY store for the field map and the optimizer hints: nothing
    #     mirrors them back onto the class. Every reader goes through the
    #     definition (the walker resolves it per entry; the schema audit
    #     reads registry.get_definition(...).field_map).
    cls.__django_strawberry_definition__ = definition
    # 13. Install is_type_of so an interface- or union-resolved value can
    #     be attributed to this type at execution time.
    install_is_type_of(cls)
    # NOTE: strawberry.type(cls) is NOT called here. _attach_relation_resolvers
    # is also NOT called here. Both move to finalize_django_types().
```
**The unconditional deferral at step 8 is the load-bearing part of this phase, and it is not an optimization to undo.** Consulting `registry.get(field.related_model)` here and binding when it answers would make the resulting schema a function of import order: the annotation freezes against whichever type happened to be registered at the moment this class body executed, which is not necessarily the type the relation should resolve to once every module has been imported. Deferring every auto-synthesized relation to finalization means one resolution rule runs once, over a settled registry, for every relation in the schema.
### Finalization phase: `finalize_django_types()`
Lives at `django_strawberry_framework/types/finalizer.py` (new). Public, importable from the package root.

This slice's base lifecycle is the three phases below, and it is a skeleton later slices insert into rather than a closed list. Phase 1 additionally carries a primary-type ambiguity audit (`spec-018-meta_primary-0_0_6.md`), phase 2 attaches file/image resolvers beside the relation ones (`spec-037-upload_file_image_mapping-0_0_11.md`), and a phase runs between resolver attachment and `strawberry.type` decoration carrying work owned by the specs that shipped it — interface application, relation-as-Connection synthesis, sidecar binding, and GlobalID wiring. Their contents belong to those specs; what this spec owns is the base lifecycle and the ordering constraint that any insertion must preserve.
```python path=null start=null
def finalize_django_types() -> None:
    """Resolve pending relations, attach resolvers, and finalize types.

    Failure-atomic boundary: phase 1 (unresolved-target detection)
    completes without mutating any class object. If phase 1 raises,
    `registry.is_finalized()` stays False, no `definition.finalized` is
    True, and no `_attach_relation_resolvers` / `strawberry.type(...)`
    side effects have occurred yet. Tests catch the error, register the
    missing target, and call this function again for a clean retry.

    The boundary is over CLASS objects, and one registry write precedes
    it: a per-build settings snapshot taken before phase 1 (the GlobalID
    strategy snapshot, `spec-031-globalid_encoding-0_0_9.md`) is a pure
    read that may raise, and on success it records state on the registry
    rather than on any class. `registry.clear()` resets it, which is what
    keeps the retry path clean.

    The later phases are NOT failure-atomic: `_attach_relation_resolvers`
    sets attributes on classes, and `strawberry.type(...)` builds
    `__strawberry_definition__` per class. If a Strawberry-side failure
    occurs after phase 1 (forward-ref error, duplicate field, bad
    annotation, etc.), the process is partially mutated:
      - some classes have relation resolvers attached, others do not
      - some types have `__strawberry_definition__` set, others do not
      - `definition.finalized` flags reflect whichever types finalized
        before the failure
      - `registry.is_finalized()` stays False because
        `mark_finalized()` runs only after the final phase completes.
    A rerun is supported from that state: each phase loop skips
    already-finalized entries through a per-entry `definition.finalized`
    guard, so fixing the offending type in place and calling
    `finalize_django_types()` again recovers at per-type granularity.
    `registry.clear()` plus fresh classes is the escape hatch for a type
    that cannot be fixed in place. This contract is documented in the
    idempotency / lifecycle section below.
    """
    if registry.is_finalized():
        return  # idempotent
    # Phase 1 (resolve pending relations). First collect every resolvable
    # and unresolved pending record without mutating classes.
    unresolved: list[PendingRelation] = []
    resolved: list[tuple[PendingRelation, type, FieldMeta]] = []
    consumer_authored: list[PendingRelation] = []
    for p in registry.iter_pending_relations():
        owning_def = registry.get_definition(p.source_type)
        # Defense-in-depth, and unreachable under the documented call
        # graph: collection never appends a pending record for a
        # consumer-authored name, so no such record can arrive here. Kept
        # because the invariant lives in another function — a future
        # collection path that DOES record pending for an overridden name
        # (a lazy or forward-reference route, say) would otherwise
        # overwrite the consumer's annotation below with no guard between.
        if owning_def is not None and p.field_name in owning_def.consumer_authored_fields:
            consumer_authored.append(p)  # nothing to resolve, but not unresolved
            continue
        target_type = registry.get(p.related_model)
        if target_type is None:
            unresolved.append(p)
            continue
        # The precomputed projection, not a re-derivation: cardinality and
        # nullability come from the owning definition's field_map so the
        # annotation the finalizer writes cannot disagree with the metadata
        # the optimizer plans against.
        resolved.append((p, target_type, owning_def.field_map[snake_case(p.field_name)]))
    # Phase 1 fail-loud: no class mutation runs and no type is marked
    # finalized if there are unresolved targets. This is the ONLY
    # failure-atomic boundary in finalize_django_types(); see docstring.
    if unresolved:
        raise ConfigurationError(_format_unresolved_targets_error(unresolved))
    resolved_pending = [*consumer_authored]
    for p, target_type, field_meta in resolved:
        p.source_type.__annotations__[p.field_name] = resolved_relation_annotation(
            p.django_field,
            target_type,
            field_meta=field_meta,
        )
        resolved_pending.append(p)
    # All pending relations either resolved or were claimed by the
    # consumer-authored escape hatch. Drop them from the pending list so
    # post-finalization diagnostics (and any retry-after-clear scenario)
    # see an empty pending set.
    registry.discard_pending(resolved_pending)
    # Phase 2 (attach generated resolvers). Uses definition.selected_fields
    # — the real Django field objects — not field_map (FieldMeta), because
    # _make_relation_resolver needs `attname`, `related_model.DoesNotExist`,
    # cardinality flags, etc. (see types/resolvers.py::_make_relation_resolver).
    # This is the only window in which resolvers may attach: it runs after
    # phase 1 has settled every annotation and before the final phase
    # freezes the class. The relation pass skips consumer-ASSIGNED
    # Strawberry fields/resolvers so generated resolvers never clobber
    # them; annotation-only overrides still get generated resolvers. The
    # file/image pass (spec-037-upload_file_image_mapping-0_0_11.md) shares
    # the window and takes the BROADER consumer_authored_fields skip set —
    # the two skip sets differ on purpose and neither is a typo for the
    # other.
    for type_cls, definition in registry.iter_definitions():
        if definition.finalized:
            continue
        _attach_relation_resolvers(
            type_cls,
            definition.selected_fields,
            skip_field_names=definition.consumer_assigned_relation_fields,
        )
        _attach_file_resolvers(
            type_cls,
            definition.selected_fields,
            skip_field_names=definition.consumer_authored_fields,
        )
    # Final phase (finalize each type with strawberry.type). NOT atomic;
    # see docstring. A Strawberry-side failure here leaves the registry
    # and class objects partially mutated; the per-entry
    # definition.finalized guard below is what makes a rerun recover at
    # per-type granularity.
    for type_cls, definition in registry.iter_definitions():
        if definition.finalized:
            continue
        strawberry.type(type_cls, name=definition.name, description=definition.description)
        definition.finalized = True
    registry.mark_finalized()
```
### Unresolved-target error format
The error is the load-bearing fail-loud signal. It must name the source model, source field, and target model, exactly as required by `spec-008-definition_order_independence-0_0_4.md` #"### The shape that shipped" and `spec-009-rich_schema_architecture-0_0_4.md` #"### Decision 6: fail loudly". Those citations are the **source of the requirement** and nothing more: the design constraint that all three be named is spec-008's, and this spec owns the canonical wording, the message format, and the substring-test contract that pin it. The split is deliberate and is stated in both documents.
```python path=null start=null
def _format_unresolved_targets_error(unresolved: list[PendingRelation]) -> str:
    lines = []
    for p in unresolved:
        lines.append(
            f"  - {p.source_model.__name__}.{p.field_name} -> "
            f"{p.related_model.__name__} (no registered DjangoType)"
        )
    body = "\n".join(lines)
    return (
        "Cannot finalize Django types: the following relation targets are unresolved.\n"
        f"{body}\n\n"
        "Declare a DjangoType for each unresolved target model, or exclude these "
        "relation fields via Meta.exclude / Meta.fields."
    )
```
The message above is the canonical wording. Tests assert against substrings (`"Cannot finalize"`, `"no registered DjangoType"`, the source `Model.field` format).

## What we take from strawberry-graphql-django
We borrow concepts and shapes, not the decorator API or the generic-fallback default. References point at the actual files we inspected for this spec. Line numbers here address pinned third-party snapshots, so they are exact and stay exact. That is the whole of this spec's line-addressing convention, and it holds wherever a third-party file is cited, including the few citations outside this section and the graphene-django one below: a line is addressed only when the file it addresses cannot move. Every in-repo citation is symbol-qualified instead.
- **Definition-object pattern**: mirror `StrawberryDjangoDefinition` at `strawberry_django/type.py:425` as our `DjangoTypeDefinition`. Same idea (one canonical metadata object stashed on the class), but stored under our own attribute name.
- **Lifecycle split**: take the *shape* of `_process_type` at `strawberry_django/type.py:73` — collect, inject auto annotations, finalize via `strawberry.type(cls, **kwargs)` (`type.py:246`), post-process `type_def.fields` (`type.py:252`). Invert the timing: we collect at class creation but only finalize when `finalize_django_types()` runs.
- **Annotation namespace preservation**: `get_strawberry_annotations` at `strawberry_django/utils/typing.py:105` is the right helper for the day a stable consumer-override contract lands. **Out of scope for 0.0.4**; flagged here so it is not reinvented later.
- **Reverse-relation lookup quirks**: `get_model_field` at `strawberry_django/fields/types.py:584` and `resolve_model_field_name` at `:569` know that reverse relations cannot be reached via `model._meta.get_field(name)` directly. We borrow this *concept* in `_select_fields` and `_record_pending_relation`. Our existing `_select_fields` already iterates `_meta.get_fields()` in field order, so the reverse-relation case already works — we only need to be careful when constructing `PendingRelation.field_name` to match the iterated `field.name`.
- **`is_optional`**: `strawberry_django/fields/types.py:607` centralizes nullability rules. Our `convert_relation` already handles forward-FK `field.null` and reverse OneToOne specially. We keep our smaller version inline; we do not import the strawberry-django function.
- **Generic `DjangoModelType` fallback** at `strawberry_django/fields/types.py:73` is *deliberately not borrowed* as the default. Concrete relations are the load-bearing invariant.
- **Custom `StrawberryDjangoFieldBase` / `StrawberryDjangoField`** at `strawberry_django/fields/base.py:50` and `strawberry_django/fields/field.py:97` is *deliberately not borrowed in this slice*. Today's `_make_relation_resolver` plus `strawberry.field(resolver=...)` is good enough for foundation; the rich-schema spec layer 4 introduces `DjangoModelField` later.
- **Optimizer store / connection extension / async resolver** patterns at `strawberry_django/optimizer.py:136-275` and `strawberry_django/fields/field.py:424-475` are *not borrowed in this slice*. Our optimizer is already root-gated, plan-cached, strict-mode aware.

## What we take from graphene-django
We take one concept and explicitly reject everything else.
- **Take**: deferred relation resolution. Graphene-Django records relations during type construction (`graphene_django/converter.py:274/342/381`) and resolves them at schema build time (`graphene/types/schema.py:308-310`). Our `PendingRelation` is the package-owned, Strawberry-native equivalent.
- **Reject**: `Dynamic` (`graphene/types/dynamic.py:7`) as a runtime substrate — we do not depend on Graphene.
- **Reject**: silent skip on unresolved targets (`if not field: continue` at `graphene/types/schema.py:309`) — we fail loud.
- **Reject**: Graphene's connection / mounted-type / `MountedType` lifecycle.

## Migration of current code (per the verification report)
Every change below is mapped to a specific symbol in the current source.
### Must redo (not augment)
- `django_strawberry_framework/types/converters.py::convert_relation`. Currently raises immediately on missing target. Becomes a thin "if registered, return concrete annotation; otherwise the caller has already recorded a pending relation" helper. The eager `raise ConfigurationError` is removed; the same error message format moves into `_format_unresolved_targets_error` at finalization.
- `django_strawberry_framework/types/base.py::DjangoType.__init_subclass__`. Split into the collection-only pseudocode above. Its trailing `strawberry.type(cls, name=name, description=description)` call is **removed**; the call moves to `finalize_django_types()`.
- `django_strawberry_framework/types/base.py::_build_annotations`. Becomes a per-field dispatch over `convert_scalar` and a relation branch that either resolves through the registry or appends to the caller's pending list. Today's monolithic loop is replaced.
- `django_strawberry_framework/registry.py::TypeRegistry.lazy_ref`. **Deleted.** The placeholder `raise NotImplementedError(...)` and its three-option docstring are misleading; the actual pending-relation API supersedes them.
- `django_strawberry_framework/registry.py::TypeRegistry.clear`. Extended to also reset `_definitions`, `_pending`, and `_finalized`. Required for test isolation; without it, pending relations and finalized markers leak between tests.
- `tests/types/test_converters.py` and `tests/types/test_base.py`. Any test that pins "creating a `DjangoType` whose target is not yet registered raises [`ConfigurationError`][glossary-configurationerror]" is rewritten. New behavior: class creation succeeds; `finalize_django_types()` raises with the unresolved-targets format.
### Should redo now (cheap to do, expensive to defer)
- `django_strawberry_framework/types/base.py`'s `cls._optimizer_field_map` and `cls._optimizer_hints` class attributes. The canonical store is `DjangoTypeDefinition.field_map` and `.optimizer_hints`, and it is the **only** store: neither name exists as a class attribute, and no reader reaches for one. The walker resolves both through the registered definition per planning entry (`optimizer/walker.py::_resolve_field_map`, `::_resolve_optimizer_hints`), and the [schema audit][glossary-schema-audit] reads `registry.get_definition(type_cls).field_map` directly. Resolving per entry rather than off the class is what lets a nested branch plan against the metadata of the type it is descending into rather than the root's.
- `django_strawberry_framework/types/base.py`'s `_is_default_get_queryset` class attribute. The definition carries the signal as `DjangoTypeDefinition.has_custom_get_queryset`, populated by an MRO-walking helper (`_detect_custom_get_queryset(cls)`), **not** by `"get_queryset" in cls.__dict__` alone: the MRO walk is what lets an abstract base that overrides `get_queryset` (a tenant-scoped mixin, say) propagate the flag to concrete subclasses. The class attribute survives beside it, as a `ClassVar` stamped at collection step 1 — **before** the `Meta` opt-out — because that opt-out is exactly the case the definition cannot serve: an abstract base without `Meta` returns before any `DjangoTypeDefinition` is built, so there is no definition on which to record its `get_queryset` override, and its concrete subclasses would inherit nothing. `has_custom_get_queryset()` reflects the split: it reads the definition when the class has one and falls back to the negated sentinel when it does not, so `optimizer/walker.py::_target_has_custom_get_queryset` sees one shape either way.
- `django_strawberry_framework/types/base.py (_build_annotations)` callers and `_attach_relation_resolvers` callers now consume `DjangoTypeDefinition.selected_fields` — the real Django field objects — rather than receiving them as a separate argument. This is required because resolver attachment runs in `finalize_django_types()` and no longer has the original `_select_fields` return value at hand; the definition object is the only source of truth at that point. `FieldMeta` is **not** sufficient for resolver bodies because they need `attname`, `related_model.DoesNotExist`, and cardinality flags.
- `django_strawberry_framework/types/resolvers.py::_attach_relation_resolvers`. The function body stays. Its call site moves from `__init_subclass__` to `finalize_django_types()` and reads `definition.selected_fields` instead of receiving a fresh field list. Today's resolvers do not look up the registry at construction time — they call `getattr(root, field_name)` — so deferring attachment is purely a timing change.
### Stays unchanged (additive only)
- `TypeRegistry.register / get / model_for_type / iter_types`. Reached through `register_with_definition` rather than called directly by collection; the foundation adds no argument to any of them (`register` and `get` later took on the primary-selection keyword and resolution order that `spec-018-meta_primary-0_0_6.md` owns).
- `TypeRegistry.register_enum / get_enum`. Orthogonal to relations.
- `_validate_meta`, `_select_fields`, `_validate_optimizer_hints_against_selected_fields`. Already collection-phase.
- `convert_scalar`, `convert_choices_to_enum`. Orthogonal to relations.
- `optimizer/extension.py`, `optimizer/walker.py`, `optimizer/plans.py`, `optimizer/hints.py`, `optimizer/field_meta.py`. The walker continues to read concrete relation metadata; only its *source* shifts, from a class attribute to the registered definition's `field_map` (item under "Should redo now").
- `utils/relations.py`, `utils/strings.py`, `utils/typing.py`, `exceptions.py`, `conf.py`.
- `_make_relation_resolver` bodies. Only their attach-time changes.
### Stays deferred (owned elsewhere, or not yet owned)
- `types/base.py::DEFERRED_META_KEYS` rejects `aggregate_class`, `fields_class`, and `search_fields`, and nothing else. A key leaves that set only when the subsystem that applies it end-to-end ships — never as a reservation — so `filterset_class`, `orderset_class`, and `interfaces` are now accepted `Meta` keys belonging to the specs listed under "DjangoTypeDefinition", and the three above stay rejected until theirs land.
- The `cls.__annotations__ = {**synthesized, **consumer_annotations}` merge, consumer last so the consumer wins. This spec pins what the merge does for relation names; the scalar half of the override semantics is `spec-019-consumer_overrides_scalar-0_0_6.md`'s.
- Multi-`DjangoType`-per-model **selection**. The registry represents it (see "TypeRegistry extensions"); the declaration that resolves it and the audit that refuses to guess are `spec-018-meta_primary-0_0_6.md`'s.
## Idempotency and lifecycle contract
- `finalize_django_types()` is **idempotent**. The first call resolves pending relations, attaches resolvers, calls `strawberry.type(cls, ...)` on every unfinalized type, and sets `registry._finalized = True`. Subsequent calls return immediately.
- **Failure-atomicity is bounded to phase 1, and is a claim about class objects.** A phase 1 failure (unresolved targets, or the ambiguity audit) leaves `registry.is_finalized() == False`, no `definition.finalized` flipped to True, and no class mutation — the consumer can register the missing target and call `finalize_django_types()` again for a clean retry. The one thing that is *not* untouched is the registry's own per-build settings snapshot, taken before phase 1; it is reset by `registry.clear()` and re-validated on every call, so the retry path stays clean, but a reader who needs "nothing at all has happened yet" should read this bullet rather than assume it. **The later phases are not failure-atomic**: `_attach_relation_resolvers` and `strawberry.type(...)` mutate class objects in-place, so a Strawberry-side failure (forward-ref error, duplicate field, bad consumer annotation, etc.) leaves the process partially mutated, with some classes carrying attached resolvers or `__strawberry_definition__` and others not.
- **A rerun after a later-phase failure is supported, and is the recommended recovery.** The registry's finalized flag flips only after every type's final phase returns, so a raise inside any phase after phase 1 leaves it False. Each phase loop re-entered on the rerun skips already-decorated types through a per-entry `definition.finalized` guard, giving a fine-grained partial recovery: fix the offending type in place and call `finalize_django_types()` again. `registry.clear()` plus recreating the affected classes from scratch remains the escape hatch for the case where the offending type cannot be fixed in place — it is no longer the only supported route.
- **Single-threaded setup window.** `finalize_django_types()` must be called once during single-threaded import / app / schema construction, before any request handling begins. The function mutates a process-global registry **and** mutates class objects (annotations, attached fields, `__strawberry_definition__`, `__django_strawberry_definition__`); the registry is intentionally lockless (see `registry.py::TypeRegistry`) and concurrent finalization can produce partial Strawberry definitions. Calling the finalizer from a request thread, async resolver, or any other concurrent context is **not supported**. Future helpers that auto-trigger finalization must be constrained to schema construction time or must acquire a real lock around the finalizer.
- A `DjangoType` declared **after** `finalize_django_types()` returns raises `ConfigurationError` from `__init_subclass__` with the message "`finalize_django_types()` already ran; cannot register `<TypeName>` after finalization. Call `registry.clear()` first if this is a test." This is the contract that makes test isolation predictable: tests use the autouse fixture pattern of `tests/types/test_base.py::_isolate_registry` (`registry.clear(); yield; registry.clear()`) and never see a stale pending-relation set.
- **`registry.clear()` resets registry state for fresh type classes; it does not roll back class mutation.** `clear()` resets every map it owns — `_types`, `_models`, `_enums`, `_definitions`, `_pending`, `_finalized`, and the slots later specs added beside them — so the next test's `__init_subclass__` and `finalize_django_types()` calls behave like a fresh process *for newly created classes*. Before dropping those maps it runs the teardown callbacks that registered types and loaded subsystems supplied, which undoes the class-level artifacts the framework itself installed and explicitly registered. What it still cannot undo is everything nobody registered a teardown for: it cannot remove `__strawberry_definition__` from already-finalized classes, cannot remove relation resolver attributes from mutated classes, and cannot remove `__django_strawberry_definition__` or rewritten `__annotations__`. Tests must not reuse finalized `DjangoType` classes after `clear()`; the autouse fixture pattern naturally avoids this because each test redefines its types inside the test function or fixture.
- **Pending records are dropped after a successful resolution.** The finalizer calls `registry.discard_pending(resolved_pending)` once phase 1 has matched every pending entry to either a target type or the consumer-authored escape hatch. Post-finalization, `registry.iter_pending_relations()` returns an empty iterator. This keeps schema-audit and diagnostic code from seeing historical records that are no longer pending.
## Test fixtures and acceptance criteria
### Implemented model substrate
The foundation slice originally identified a cardinality gap in the fakeshop product graph: products covered forward FK and reverse FK, but not OneToOne or M2M. The shipped 0.0.4 state closes that gap with the real `library` example app instead of a test-only fixture app.
`examples/fakeshop/apps/library/models.py` now provides `Branch`, `Shelf`, `Genre`, `Book`, `Patron`, `MembershipCard`, and `Loan`. Together they cover forward FK, reverse FK, forward OneToOne, reverse OneToOne, forward M2M, reverse M2M, a choice field, and a nullable scalar field.
Package tests that need cardinality coverage import the real example-project models from `apps.products.models` and `apps.library.models`. Live GraphQL acceptance tests exercise the same model surface through `/graphql/` under `examples/fakeshop/test_query/test_library_api.py`.
The example project uses the standard explicit-package layout under `examples/fakeshop/`: project setup lives in `config/settings.py`, `config/schema.py`, `config/urls.py`, and `config/wsgi.py`, while domain apps live under `apps/products/` and `apps/library/`. The project schema imports all app schema modules, composes the top-level query type, calls `finalize_django_types()` once, and then constructs the Strawberry schema.
### Cyclic acceptance tests
Under `tests/types/test_definition_order.py`:
- `Category` declared before `Item`; `Item.category` resolves to `CategoryType`; `Category.items` resolves to `list[ItemType]`.
- `Item` declared before `Category`; the same assertions hold.
- `MembershipCard` / `Patron` cover forward and reverse OneToOne.
- `Book` / `Genre` cover forward and reverse M2M.
- The multi-cycle product graph (`Category <-> Item <-> Entry <-> Property <-> Category`) finalizes successfully and produces concrete types on every edge.
- Unresolved targets raise `ConfigurationError` from `finalize_django_types()` with the source model, source field, and target model named.
- Annotation-only relation overrides preserve the consumer annotation while keeping the generated relation resolver.
- Field/resolver and decorator overrides suppress generated resolver attachment and route execution through the consumer resolver.
- Supported forward-reference shapes are pinned by tests and documented in the shipped feature docs.
### End-to-end schema and HTTP tests
Under `examples/fakeshop/apps/library/tests/test_schema.py` — per-app, beside the app whose coverage it is:
- In-process schema execution proves the fakeshop query composition path still works.
- The project schema includes the real library types.
- The library `DjangoType` declaration order is intentionally awkward and is pinned so future reordering does not erase definition-order coverage.

Under `tests/types/test_definition_order_schema.py`:
- The pending-relation sentinel's repr is pinned, so a type decorated with `strawberry.type` before finalization reports the placeholder recognizably instead of leaking an opaque object into a Strawberry error.
Under `examples/fakeshop/test_query/test_library_api.py`:
- Live `/graphql/` tests cover nested traversal through `Branch -> Shelf -> Book -> Loan -> Patron`.
- Reverse OneToOne nullability, reverse M2M traversal, [choice enum][glossary-choice-enum-generation] wire values, and nullable scalar wire values are asserted over HTTP.
- Forward FK, reverse FK, and M2M optimizer SQL shapes are asserted with Django query capture.
- Consumer-shaped queryset cooperation, `OptimizerHint.prefetch_related()`, `OptimizerHint.SKIP`, and consumer-authored relation overrides are observable through the HTTP layer.
### Optimizer regression tests
Under `tests/optimizer/test_definition_order.py`:
- `walker.plan_relation(field, target_type, info)` returns the same `("select", "default")` / `("prefetch", "default")` / `("prefetch", "custom_get_queryset")` decisions for cyclic graphs after finalization.
- `DjangoOptimizerExtension.check_schema(schema)` returns no warnings for reachable types whose relation targets are registered.
- The registered `DjangoTypeDefinition.field_map` carries an entry for every selected field, relation and scalar alike — the optimizer's canonical source, asserted directly rather than through any class-attribute proxy.
### Idempotency / isolation tests
`tests/test_registry.py` pins the finalizer lifecycle:
- Calling `finalize_django_types()` twice mutates state once.
- A new `DjangoType` registered after finalization raises with the documented message.
- `registry.clear()` resets the package to a fresh state for newly created classes.
- Phase 1 failure atomicity, phase 2/3 partial-mutation limits, pending-set cleanup, and class-mutation residue are all covered as explicit contracts.
### Existing tests that changed
Tests that used to assert eager relation-target failure now assert finalization-time failure. Package-level cardinality tests now use the real example app models, while live HTTP tests pin the consumer-visible GraphQL behavior.
## Phased implementation order (within the slice)
The slice is ordered so each step lands a passing test suite. **Phase 0 is the spike gate; production code begins at Phase 1.**
0. **Phase 0 — Spike gate.** Write Spike A, B, and C under `scripts/spikes/`. Run them. Record the outcome inline in this spec's "Spike outcome (gates implementation)" section and in `README.md`'s schema-setup section. Delete the spike scripts only after their conclusions are captured. **No production-code phase below begins until Spike A's five pass criteria are recorded as passed.**
1. Add `DjangoTypeDefinition` dataclass at `types/definition.py` and the `PendingRelation` dataclass at `types/relations.py`. No behavior change yet.
2. Extend `TypeRegistry` with `register_definition`, `get_definition`, `iter_definitions`, `add_pending_relation`, `iter_pending_relations`, `discard_pending`, `is_finalized`, `mark_finalized`, and the extended `clear`. Delete `lazy_ref`.
3. Implement `finalize_django_types()` at `types/finalizer.py`. No collection changes yet; the function runs against an empty pending list.
4. Split `__init_subclass__` into the collection-only pseudocode. Move the `strawberry.type(cls, ...)` call out and into `finalize_django_types()`. Move `_attach_relation_resolvers` out and into `finalize_django_types()` (consuming `definition.selected_fields` and skipping `definition.consumer_assigned_relation_fields`). Add the post-finalization registration guard on both sides (the `__init_subclass__` rejection and the registry-boundary `_check_mutable`), and the consumer-authored detection (annotation, or a class-dict value that is a `StrawberryField`).
5. Replace the eager `cls.__dict__` get_queryset detection with `_detect_custom_get_queryset(cls)` (MRO-aware) so abstract bases keep propagating the sentinel.
6. Move the field-map and optimizer-hint reads onto the definition, and route the walker and the schema audit through `registry.get_definition(...)`; no class-attribute copy of either survives the step. Keep `_is_default_get_queryset` as the class-level carrier for the definition-less abstract-base case (step 1 of the collection phase), with the definition as the reading every other caller gets.
7. Add real cardinality coverage through the example project model substrate. In the shipped 0.0.4 implementation this is the `apps.library` app under `examples/fakeshop/apps/`, not a test-only fixture app.
8. Rewrite the affected `tests/types/test_converters.py` / `tests/types/test_base.py` cases (relation-target-not-registered now succeeds at class creation, fails at finalization).
9. Add the new acceptance test files under `tests/types/test_definition_order.py`, `tests/types/test_definition_order_schema.py`, `tests/optimizer/test_definition_order.py`, and extend the existing `tests/test_registry.py` with the new idempotency / isolation / failure-atomicity sections.
10. Update documentation:
    - `README.md` — public-API list and the landing snippet that shows the `finalize_django_types()` call site.
    - `docs/README.md` — quick-start snippet, plus the schema-setup boundary section: the correct and wrong-order examples as a pair, and the explicit "import every module that defines `DjangoType` classes before calling `finalize_django_types()`" note with the most-common-failure-mode framing.
    - `docs/GLOSSARY.md` — capability catalog entry, including which forward-reference shapes are supported.
    - `TODAY.md` — capability snapshot.
    - `CHANGELOG.md` — release entry summarizing the new capability and the new public API.
11. Update export points:
    - `django_strawberry_framework/__init__.py` — re-export [`finalize_django_types`][glossary-finalize-django-types], add it to `__all__`.
    - `django_strawberry_framework/types/__init__.py` — re-export `finalize_django_types` so it is reachable as `from django_strawberry_framework.types import finalize_django_types` for symmetry with `DjangoType`.
12. Bump version metadata to `0.0.4`:
    - `pyproject.toml` (`version = "0.0.4"`).
    - `django_strawberry_framework/__init__.py` (`__version__ = "0.0.4"`).
## Public API delta
After this slice the public surface gains exactly one new symbol:
- `finalize_django_types: Callable[[], None]` — re-exported from both `django_strawberry_framework` (top-level) and `django_strawberry_framework.types` (subpackage), so consumers can import it the same way they import `DjangoType`.
Existing public names — `DjangoType`, [`DjangoOptimizerExtension`][glossary-djangooptimizerextension], [`OptimizerHint`][glossary-optimizerhint], `auto` — are unchanged.
Version metadata bumps from `0.0.3` to `0.0.4` in both `pyproject.toml` and `django_strawberry_framework/__init__.py:__version__`.
The `__django_strawberry_definition__` attribute is *not* part of the public API surface but is documented as a stable internal hook for the optimizer and future subsystems.

## Failure modes and rollback
- If Spike A fails (deferred `strawberry.type(cls)` proves unsafe), the slice pauses. The fallback is Strategy 2 (post-`__strawberry_definition__` patching). Rollback cost: rewrite the finalizer; collection phase and registry extensions are reusable.
- If Spike B exposes a Strawberry behavior we cannot work around, the foundation slice degrades to a documented "two-pass" requirement: users call `finalize_django_types()` *before* schema construction. This is already the foundation strategy; the failure simply delays the future auto-trigger work.
- If a reviewer can demonstrate that any of the seven invariants in "Invariants this slice must protect" is violated by the proposed design, the slice is re-planned before code lands. The maintainer's current incoming review document forms the live review checklist until each item is resolved; the count and wording of items is expected to evolve until the slice ships.
## Cross-references
- Definition-order problem space, prior art, decision options: [`docs/SPECS/spec-008-definition_order_independence-0_0_4.md`][spec-008].
- Long-term architecture, layered subsystems, prior-art line references: [`docs/SPECS/spec-009-rich_schema_architecture-0_0_4.md`][spec-009].
- Operational entry point — install, quick start, and the schema-setup boundary this slice defines: [`docs/README.md`][docs-readme]. Contributor workflow (dev setup, format, test, build, publish) is [`CONTRIBUTING.md`][contributing]'s; the root [`README.md`][readme] is positioning, and carries the public-API list and landing snippet phase 10 names.
- North star and goal: [`GOAL.md`][goal].
- Today's shipped surface: [`TODAY.md`][today].
- Tree layout: [`docs/TREE.md`][tree].

<!-- LINK DEFINITIONS -->

<!-- Root -->
[contributing]: ../../CONTRIBUTING.md
[goal]: ../../GOAL.md
[readme]: ../../README.md
[today]: ../../TODAY.md

<!-- docs/ -->
[docs-readme]: ../README.md
[glossary-choice-enum-generation]: ../GLOSSARY.md#choice-enum-generation
[glossary-configurationerror]: ../GLOSSARY.md#configurationerror
[glossary-definition-order-independence]: ../GLOSSARY.md#definition-order-independence
[glossary-djangoconnectionfield]: ../GLOSSARY.md#djangoconnectionfield
[glossary-djangonodefield]: ../GLOSSARY.md#djangonodefield
[glossary-djangooptimizerextension]: ../GLOSSARY.md#djangooptimizerextension
[glossary-djangotype]: ../GLOSSARY.md#djangotype
[glossary-finalize-django-types]: ../GLOSSARY.md#finalize_django_types
[glossary-metafields]: ../GLOSSARY.md#metafields
[glossary-metaprimary]: ../GLOSSARY.md#metaprimary
[glossary-optimizerhint]: ../GLOSSARY.md#optimizerhint
[glossary-schema-audit]: ../GLOSSARY.md#schema-audit
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[spec-008]: spec-008-definition_order_independence-0_0_4.md
[spec-009]: spec-009-rich_schema_architecture-0_0_4.md
[spec-010-rationale]: appx/spec-010-foundation-0_0_4-rationale.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
