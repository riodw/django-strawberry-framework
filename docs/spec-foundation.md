# Foundation slice: definition-order independence

## Purpose
This document is the implementation contract for the 0.0.4 foundation slice. It is the single source of truth for what ships in this release. It is intentionally narrower than the broader design specs:
- [`docs/spec-definition_order_independence.md`](spec-definition_order_independence.md) discusses the relation-resolution problem space and prior art at length. This spec narrows that into one shippable slice and resolves the open design questions raised there.
- [`docs/spec-rich_schema_architecture.md`](spec-rich_schema_architecture.md) describes the long-term architecture (filters, orders, aggregates, connections, permissions, custom field classes). This spec implements only the type/registry/finalization layer that everything in that document later sits on top of.
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
- `DjangoSchema`, `DjangoConnectionField`, `DjangoNodeField`. Rich-schema spec layer 5+. The foundation only exposes the explicit `finalize_django_types()` entry point; helpers wrap it in later releases.
- Filters, orders, aggregates, fieldsets, permissions, sentinel redaction, field-level optimizer stores. Rich-schema spec layers 6–11.
- Strawberry-Django's decorator API surface and `DjangoModelType` generic relation fallback.
- `Meta.primary` for multiple `DjangoType`s per model. The current registry hard-fails on duplicate models, and that stays.
- A general consumer manual-annotation override contract. The 0.0.4 contract is narrower and explicit (see "Manual annotation contract for relation fields" below): for relation fields only, a consumer-supplied annotation suppresses both placeholder synthesis and pending-relation recording, so the user's annotation flows through unchanged. Validation that a consumer annotation matches the Django relation cardinality is deferred. Manual override on scalar fields remains the same documented "implementation detail" with the same warning as today.
## Invariants this slice must protect
The following are the invariants every reviewer should test the design against. Any change that violates one of them is a rejected change.
- `Meta.fields = "__all__"` produces concrete rich related `DjangoType`s by default, regardless of declaration order.
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
Pass criteria: a passing or failing assertion. If Spike A passes cleanly, Spike B is documented as "not required" and Option B from `spec-definition_order_independence.md (400-414)` is closed out as rejected.
### Spike C: same-module forward references
Goal: confirm that `Annotated[T, strawberry.lazy("module.path")]` cannot be used as the default mechanism for cyclic relations in the same module (it requires a real importable path and breaks single-file examples).
Pass criteria: documented confirmation that `strawberry.lazy(...)` stays only as an *optional explicit escape hatch*, never as the default.
### Spike outcome (gates implementation)
Spikes A–C resolve the four-option choice in `spec-definition_order_independence.md (400-414)`. **No production code in this slice may be written until Spike A's five pass criteria are satisfied.** A contributor cannot skip the spike and assume Strawberry finalization timing will work. The expected outcome — and the strategy this spec assumes — is that Spike A passes cleanly, so the foundation slice will commit to **Strategy 1: defer `strawberry.type(cls)` until finalization**. The earliest safe call point for `finalize_django_types()` is whichever boundary Spike A criteria 4 and 5 prove is required; that boundary is then pinned in the strategy section below and in `README.md`. If Spike A fails, the slice is paused and re-planned around Strategy 2 before any production code lands.

## Strawberry finalization strategy (assumed pending Spike A)
The foundation slice will commit to the following once Spike A passes (see "Pre-implementation spikes" gate above). Until then this is the **preferred** strategy, not a contract.
- `DjangoType.__init_subclass__` collects metadata only. It does **not** call `strawberry.type(cls)`.
- `finalize_django_types()` is the single point that resolves pending relations, attaches relation resolvers, and calls `strawberry.type(cls, ...)` for each registered type.
- **Earliest safe call point**: `finalize_django_types()` must run **before any `@strawberry.type` decorator processes a class that references a `DjangoType`** — including resolver return annotations such as `list[ItemType]`, field annotations such as `item: ItemType`, and any future `DjangoConnectionField(ItemType)` helper. This is *earlier* than `strawberry.Schema(...)` construction. The exact boundary is pinned by Spike A criterion 4/5 and documented in `README.md` with both a worked correct example and a worked wrong-order example so users can recognize the failure mode immediately.
- **Lifecycle window**: `finalize_django_types()` must be called **once during single-threaded import / app / schema setup, before serving requests**. It is **not** safe to call from a request thread, an async resolver, or any concurrent context. The function mutates a process-global registry **and** mutates class objects (annotations, attached fields, `__strawberry_definition__`, `__django_strawberry_definition__`); the foundation slice's registry is intentionally lockless (see `registry.py:28-33`) and concurrent finalization can produce partial Strawberry definitions. This window is restated in `README.md`.
- **Module discovery is the consumer's responsibility**: the foundation slice does not ship `apps.py`, autodiscovery, or any helper that imports project modules on the user's behalf. Every Python module that defines a `DjangoType` must be imported (directly or transitively) **before** `finalize_django_types()` runs. A `CategoryType` that exists in code but lives in a never-imported module will be reported as unresolved by the finalizer with the standard error format. The README setup snippet must explicitly show the import boundary (e.g., `from myapp.types import *  # noqa: F401`) immediately before the finalizer call, alongside an explicit doc note that this is the most common production failure mode in 0.0.4. Autodiscovery is a later-phase wrapper concern.
- Auto-trigger via `DjangoSchema(...)` and `DjangoConnectionField(Type)` is a later-phase wrapper around this same entry point — see `spec-rich_schema_architecture.md (670-687)`. Any future helper that auto-triggers finalization must also enforce the single-threaded-setup window: either by being constrained to schema construction time, or by acquiring a real lock around the finalizer.
- `Annotated[..., strawberry.lazy("module.path")]` remains a documented optional override path for users who want a non-primary target type or who want to defer a relation across modules. It is not the default and not required for normal `Meta.fields = "__all__"`.
### Manual annotation contract for relation fields (0.0.4)
For relation fields only, the foundation slice pins this contract:
- **Annotation override**: if the consumer has supplied an annotation on the same Python name as a Django relation field (`items: list["ItemType"]`, `items: Annotated[list["ItemType"], strawberry.lazy("...")]`, etc.), the collection phase **skips both** placeholder synthesis and pending-relation recording for that field. The user's annotation is left untouched and flows through Strawberry's normal annotation handling at finalization time.
- **Field / resolver override**: if the consumer assigns a Strawberry field or resolver to the same Python name (`items: list["ItemType"] = strawberry.field(resolver=custom_items)`, `@strawberry.field def items(...) -> list["ItemType"]`, or any pre-existing `cls.<field_name>` value that is not the default Django attribute), the collection phase records the field name on `DjangoTypeDefinition.consumer_authored_fields` and the **finalizer's resolver-attachment phase skips that field**. `_attach_relation_resolvers` must consult this set and `setattr(cls, field.name, ...)` only for relation fields the consumer did not author. The consumer-authored field/resolver wins; the finalizer never clobbers it.
- **Detection rule**: a relation field is treated as consumer-authored if either (a) `field.name` is present in `cls.__dict__` and the value is not a Django manager/descriptor (i.e., it was assigned by the consumer, not by Django's class machinery), or (b) `field.name` appears in the consumer's pre-collection `__annotations__`. The two sets are unioned; both feed `consumer_authored_fields`.
- The finalizer **never** rewrites a relation annotation that was consumer-supplied and **never** attaches a resolver to a consumer-authored relation field.
- Validation that a consumer-supplied annotation matches the Django relation cardinality (`many_to_many` → `list[T]`, nullable FK → `T | None`, etc.) is **deferred**. The 0.0.4 contract is "trust the user's annotation; do not silently overwrite."
- Tests cover all four shapes:
  - annotation-only override (`items: list["ItemType"]`)
  - `Annotated[..., strawberry.lazy("...")]` cross-module override
  - explicit `strawberry.field(resolver=...)` assignment on a relation field
  - `@strawberry.field` decorator on a relation field
- Manual override on *scalar* fields continues to follow the existing implementation-detail caveat at `base.py:151-159` and is not pinned in this slice.
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
    # Field metadata (migrated from class attrs)
    field_map: dict[str, FieldMeta]           # was cls._optimizer_field_map
    optimizer_hints: dict[str, OptimizerHint] # was cls._optimizer_hints
    # Get-queryset signal — populated by the MRO-walking helper (see
    # collection pseudocode), not just by `"get_queryset" in cls.__dict__`,
    # so abstract bases that override get_queryset propagate the flag to
    # concrete subclasses exactly as today's _is_default_get_queryset
    # sentinel does.
    has_custom_get_queryset: bool             # was cls._is_default_get_queryset (negated)
    # Names of relation fields whose annotation OR field/resolver was
    # supplied by the consumer (see "Manual annotation contract for
    # relation fields"). The collection phase populates this from both
    # sources (pre-existing annotation OR pre-existing class-dict value).
    # The finalizer's annotation-rewrite phase skips these field names
    # when rewriting annotations, AND _attach_relation_resolvers skips
    # them when attaching resolvers, so consumer-authored
    # `strawberry.field(resolver=...)` / `@strawberry.field` shapes are
    # never clobbered.
    consumer_authored_fields: frozenset[str] = frozenset()
    # Forward-reserved slots (declared but unused in 0.0.4)
    # These exist so later subsystems plug in without reshaping the dataclass.
    # Validation in _validate_meta still rejects the matching Meta keys until
    # their owning subsystem ships, so consumers cannot set these in 0.0.4.
    filterset_class: Any | None = None
    orderset_class: Any | None = None
    aggregate_class: Any | None = None
    fields_class: Any | None = None
    search_fields: tuple[str, ...] = ()
    interfaces: tuple[type, ...] = ()
    # Lifecycle
    finalized: bool = False
```
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
        # Existing maps stay.
        self._types: dict[type[models.Model], type] = {}
        self._models: dict[type, type[models.Model]] = {}
        self._enums: dict[tuple[type[models.Model], str], type[Enum]] = {}
        # New maps for the foundation slice.
        self._definitions: dict[type, DjangoTypeDefinition] = {}
        self._pending: list[PendingRelation] = []
        self._finalized: bool = False
    # Existing API unchanged: register, get, model_for_type, iter_types,
    # register_enum, get_enum.
    # New API.
    def register_definition(self, type_cls: type, definition: DjangoTypeDefinition) -> None: ...
    def get_definition(self, type_cls: type) -> DjangoTypeDefinition | None: ...
    def iter_definitions(self) -> Iterator[tuple[type, DjangoTypeDefinition]]: ...
    def add_pending_relation(self, pending: PendingRelation) -> None: ...
    def iter_pending_relations(self) -> Iterator[PendingRelation]: ...
    def is_finalized(self) -> bool: ...
    def mark_finalized(self) -> None: ...
    # clear() is extended (not redone): in addition to today's three maps,
    # it also resets _definitions, _pending, and _finalized.
    def clear(self) -> None:
        self._types.clear()
        self._models.clear()
        self._enums.clear()
        self._definitions.clear()
        self._pending.clear()
        self._finalized = False
    # Deleted: lazy_ref. The placeholder NotImplementedError stub is removed
    # outright; see "Migration of current code" below.
```
### Collection phase: `DjangoType.__init_subclass__`
After the rewrite, `__init_subclass__` performs collection only. Pseudocode:
```python path=null start=null
def __init_subclass__(cls, **kwargs):
    super().__init_subclass__(**kwargs)
    # 1. MRO-aware custom get_queryset detection. Walks the new class's
    #    MRO so an abstract base that overrides get_queryset propagates
    #    the flag to concrete subclasses exactly the way today's
    #    `_is_default_get_queryset` class-attribute sentinel does. This
    #    runs unconditionally — before the meta-is-None opt-out — so an
    #    abstract base without Meta but with its own get_queryset still
    #    flips the sentinel for downstream concrete subclasses.
    has_custom_get_queryset = _detect_custom_get_queryset(cls)
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
    #    union feeds DjangoTypeDefinition.consumer_authored_fields and
    #    is consulted by both the annotation rewrite path and the
    #    resolver attachment path so neither overwrites consumer code.
    consumer_annotations = dict(cls.__dict__.get("__annotations__", {}))
    consumer_class_dict = cls.__dict__
    consumer_authored_fields = frozenset(
        f.name for f in fields
        if f.is_relation and (
            f.name in consumer_annotations
            or _is_consumer_authored_class_attr(consumer_class_dict, f.name)
        )
    )
    # 8. Build annotations. Scalars resolve immediately; relations either
    #    resolve immediately if their target is registered, defer if the
    #    target is unknown, or get left alone if the consumer pre-supplied
    #    an annotation or a field/resolver assignment.
    synthesized: dict[str, Any] = {}
    pending: list[PendingRelation] = []
    for field in fields:
        if field.is_relation:
            if field.name in consumer_authored_fields:
                # Consumer wins; do not synthesize, do not record pending,
                # and the finalizer's resolver-attachment phase will also
                # skip this field.
                continue
            target_type = registry.get(field.related_model)
            if target_type is not None:
                synthesized[field.name] = _resolved_relation_annotation(field, target_type)
            else:
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
    )
    # 10. Register early so later siblings can resolve us.
    registry.register(meta.model, cls)
    registry.register_definition(cls, definition)
    for p in pending:
        registry.add_pending_relation(p)
    # 11. Stage annotations on the class. Consumer-declared annotations
    #     are merged on top so the consumer wins for any field name they
    #     explicitly annotated (relation OR scalar). Scalar override
    #     remains an implementation detail with the same warning as
    #     today; relation override is the documented contract above.
    cls.__annotations__ = {**synthesized, **consumer_annotations}
    # 12. Stash the definition on the class for fast lookup.
    cls.__django_strawberry_definition__ = definition
    # 13. Synchronize legacy class attributes for one minor version so
    #     out-of-tree code reading cls._optimizer_field_map /
    #     _optimizer_hints / _is_default_get_queryset keeps working. The
    #     walker reads via getattr(type_cls, "_optimizer_field_map", None)
    #     at walker.py:64; a class-level @property cannot return the
    #     underlying dict from a `getattr(cls, ...)` call (it returns the
    #     descriptor object itself), so we mirror values directly onto
    #     the class instead. Removed in the next minor.
    cls._optimizer_field_map = field_map
    cls._optimizer_hints = optimizer_hints
    cls._is_default_get_queryset = not has_custom_get_queryset
    # NOTE: strawberry.type(cls) is NOT called here. _attach_relation_resolvers
    # is also NOT called here. Both move to finalize_django_types().
```
### Finalization phase: `finalize_django_types()`
Lives at `django_strawberry_framework/types/finalizer.py` (new). Public, importable from the package root.
```python path=null start=null
def finalize_django_types() -> None:
    """Resolve pending relations, attach resolvers, and finalize types.

    Failure-atomic boundary: phase 1 (unresolved-target detection)
    completes without mutating any class object. If phase 1 raises,
    `registry.is_finalized()` stays False, no `definition.finalized` is
    True, and no `_attach_relation_resolvers` / `strawberry.type(...)`
    side effects have occurred yet. Tests catch the error, register the
    missing target, and call this function again for a clean retry.

    Phases 2 and 3 are NOT failure-atomic: `_attach_relation_resolvers`
    sets attributes on classes, and `strawberry.type(...)` builds
    `__strawberry_definition__` per class. If a Strawberry-side failure
    occurs in phase 2 or 3 (forward-ref error, duplicate field, bad
    annotation, etc.), the process is partially mutated:
      - some classes have relation resolvers attached, others do not
      - some types have `__strawberry_definition__` set, others do not
      - `definition.finalized` flags reflect whichever types finalized
        before the failure
      - `registry.is_finalized()` stays False because
        `mark_finalized()` runs only after phase 3 completes.
    Recovery from a phase 2/3 failure REQUIRES calling `registry.clear()`
    and recreating fresh `DjangoType` classes from scratch. Re-calling
    `finalize_django_types()` on partially mutated classes is
    unsupported. This contract is documented in the idempotency /
    lifecycle section below and pinned by the
    `test_phase3_strawberry_failure_requires_full_restart` acceptance
    test.
    """
    if registry.is_finalized():
        return  # idempotent
    # Phase 1 (resolve pending relations). Skip any field whose owning
    # DjangoTypeDefinition recorded a consumer-authored relation — that
    # field's annotation was never replaced by a placeholder in
    # collection and must not be overwritten now.
    unresolved: list[PendingRelation] = []
    resolved: list[PendingRelation] = []
    for p in registry.iter_pending_relations():
        owning_def = registry.get_definition(p.source_type)
        if owning_def is not None and p.field_name in owning_def.consumer_authored_fields:
            resolved.append(p)  # consumer-authored: nothing to resolve, but not unresolved
            continue
        target_type = registry.get(p.related_model)
        if target_type is None:
            unresolved.append(p)
            continue
        p.source_type.__annotations__[p.field_name] = (
            _resolved_relation_annotation_from_pending(p, target_type)
        )
        resolved.append(p)
    # Phase 1 fail-loud: no class mutation runs and no type is marked
    # finalized if there are unresolved targets. This is the ONLY
    # failure-atomic boundary in finalize_django_types(); see docstring.
    if unresolved:
        raise ConfigurationError(_format_unresolved_targets_error(unresolved))
    # All pending relations either resolved or were claimed by the
    # consumer-authored escape hatch. Drop them from the pending list so
    # post-finalization diagnostics (and any retry-after-clear scenario)
    # see an empty pending set.
    registry.discard_pending(resolved)
    # Phase 2 (attach relation resolvers). Uses definition.selected_fields
    # — the real Django field objects — not field_map (FieldMeta), because
    # _make_relation_resolver needs `attname`, `related_model.DoesNotExist`,
    # cardinality flags, etc. (see `types/resolvers.py:111-165`). Skip
    # any relation field whose name is in the consumer-authored set so
    # consumer-supplied resolvers / @strawberry.field decorators are
    # never clobbered.
    for type_cls, definition in registry.iter_definitions():
        if definition.finalized:
            continue
        _attach_relation_resolvers(
            type_cls,
            definition.selected_fields,
            skip_field_names=definition.consumer_authored_fields,
        )
    # Phase 3 (finalize each type with strawberry.type). NOT atomic; see
    # docstring. A Strawberry-side failure here leaves the registry and
    # class objects partially mutated and requires registry.clear() +
    # fresh class recreation to recover.
    for type_cls, definition in registry.iter_definitions():
        if definition.finalized:
            continue
        strawberry.type(type_cls, name=definition.name, description=definition.description)
        definition.finalized = True
    registry.mark_finalized()
```
### Unresolved-target error format
The error is the load-bearing fail-loud signal. It must name the source model, source field, and target model, exactly as required by `spec-definition_order_independence.md (397-505)` and `spec-rich_schema_architecture.md (1076-1077)`.
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
We borrow concepts and shapes, not the decorator API or the generic-fallback default. References point at the actual files we inspected for this spec.
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
- `django_strawberry_framework/types/converters.py:211 (convert_relation)`. Currently raises immediately on missing target. Becomes a thin "if registered, return concrete annotation; otherwise the caller has already recorded a pending relation" helper. The eager `raise ConfigurationError` is removed; the same error message format moves into `_format_unresolved_targets_error` at finalization.
- `django_strawberry_framework/types/base.py:80 (__init_subclass__)`. Split into the collection-only pseudocode above. The trailing `strawberry.type(cls, name=name, description=description)` call at `base.py:181` is **removed**; the call moves to `finalize_django_types()`.
- `django_strawberry_framework/types/base.py:377 (_build_annotations)`. Becomes a per-field dispatch over `convert_scalar` and a relation branch that either resolves through the registry or appends to the caller's pending list. Today's monolithic loop is replaced.
- `django_strawberry_framework/registry.py:93 (TypeRegistry.lazy_ref)`. **Deleted.** The placeholder `raise NotImplementedError(...)` and its three-option docstring are misleading; the actual pending-relation API supersedes them.
- `django_strawberry_framework/registry.py:154 (TypeRegistry.clear)`. Extended to also reset `_definitions`, `_pending`, and `_finalized`. Required for test isolation; without it, pending relations and finalized markers leak between tests.
- `tests/types/test_converters.py` and `tests/types/test_base.py`. Any test that pins "creating a `DjangoType` whose target is not yet registered raises `ConfigurationError`" is rewritten. New behavior: class creation succeeds; `finalize_django_types()` raises with the unresolved-targets format.
### Should redo now (cheap to do, expensive to defer)
- `django_strawberry_framework/types/base.py:147 (cls._optimizer_field_map)` and `:149 (cls._optimizer_hints)`. The canonical store moves to `DjangoTypeDefinition.field_map` and `.optimizer_hints`. The walker keeps reading `getattr(type_cls, "_optimizer_field_map", None)` at `walker.py:64` and `getattr(type_cls, "_optimizer_hints", {})` at `walker.py:130` for one minor version. The compat surface is **direct class-attribute mirroring** in `__init_subclass__` (see step 13 of the collection pseudocode), **not** a `@property` — a normal instance property returns the descriptor object itself when the walker does `getattr(type_cls, "_optimizer_field_map", None)` (because `type_cls` is the class, not an instance), which would silently break the walker and the schema audit. The mirrored attributes are removed in the next minor once the walker reads through `registry.get_definition(...)`.
- `django_strawberry_framework/types/base.py:71 (_is_default_get_queryset)`. Migrated onto `DjangoTypeDefinition.has_custom_get_queryset`, but populated by an MRO-walking helper (`_detect_custom_get_queryset(cls)`), **not** by `"get_queryset" in cls.__dict__` alone. The MRO walk is required so an abstract base that overrides `get_queryset` (e.g., a tenant-scoped mixin) propagates the flag to concrete subclasses exactly as today's class-attribute sentinel does at `base.py:128-131`. The `has_custom_get_queryset()` classmethod stays as a thin lookup (`return cls.__django_strawberry_definition__.has_custom_get_queryset`) so `walker.py:42` keeps reading the same shape. The legacy `cls._is_default_get_queryset` is mirrored from the definition for one minor version (collection pseudocode step 13).
- `django_strawberry_framework/types/base.py (_build_annotations)` callers and `_attach_relation_resolvers` callers now consume `DjangoTypeDefinition.selected_fields` — the real Django field objects — rather than receiving them as a separate argument. This is required because resolver attachment runs in `finalize_django_types()` and no longer has the original `_select_fields` return value at hand; the definition object is the only source of truth at that point. `FieldMeta` is **not** sufficient for resolver bodies because they need `attname`, `related_model.DoesNotExist`, and cardinality flags.
- `django_strawberry_framework/types/resolvers.py:168 (_attach_relation_resolvers)`. The function body stays. Its call site moves from `__init_subclass__` to `finalize_django_types()` and reads `definition.selected_fields` instead of receiving a fresh field list. Today's resolvers do not look up the registry at construction time — they call `getattr(root, field_name)` — so deferring attachment is purely a timing change.
### Stays unchanged (additive only)
- `TypeRegistry.register / get / model_for_type / iter_types`. Augment with calls to `register_definition`; no signature change.
- `TypeRegistry.register_enum / get_enum`. Orthogonal to relations.
- `_validate_meta`, `_select_fields`, `_validate_optimizer_hints_against_selected_fields`. Already collection-phase.
- `convert_scalar`, `convert_choices_to_enum`. Orthogonal to relations.
- `optimizer/extension.py`, `optimizer/walker.py`, `optimizer/plans.py`, `optimizer/hints.py`, `optimizer/field_meta.py`. The walker continues to read concrete relation metadata; only the *source* of `_optimizer_field_map` shifts (item under "Should redo now").
- `utils/relations.py`, `utils/strings.py`, `utils/typing.py`, `exceptions.py`, `conf.py`.
- `_make_relation_resolver` bodies. Only their attach-time changes.
### Stays deferred (do not touch in this slice)
- `DEFERRED_META_KEYS` at `types/base.py:38-53` keeps rejecting `filterset_class`, `orderset_class`, `aggregate_class`, `fields_class`, `search_fields`, `interfaces`. The `DjangoTypeDefinition` slots for them are declared but unused; consumers cannot set them yet because `_validate_meta` still raises.
- The `cls.__annotations__ = {**synthesized, **existing}` merge stays as today, with the existing implementation-detail caveat. Manual-override semantics are not pinned in this slice.
- Multi-`DjangoType`-per-model support. Today's `register` hard-fails on duplicates; that behavior survives the slice.
## Idempotency and lifecycle contract
- `finalize_django_types()` is **idempotent**. The first call resolves pending relations, attaches resolvers, calls `strawberry.type(cls, ...)` on every unfinalized type, and sets `registry._finalized = True`. Subsequent calls return immediately.
- **Failure-atomicity is bounded to phase 1.** A phase 1 failure (unresolved targets) leaves `registry.is_finalized() == False`, no `definition.finalized` flipped to True, and no class mutation — the consumer can register the missing target and call `finalize_django_types()` again for a clean retry. **Phase 2 and phase 3 are not failure-atomic**: `_attach_relation_resolvers` and `strawberry.type(...)` mutate class objects in-place. A Strawberry-side failure during those phases (forward-ref error, duplicate field, bad consumer annotation, etc.) leaves the process partially mutated and the only supported recovery is `registry.clear()` followed by recreating the affected `DjangoType` classes from scratch. Re-calling `finalize_django_types()` after a phase 2/3 failure on the same classes is unsupported and may produce inconsistent Strawberry definitions.
- **Single-threaded setup window.** `finalize_django_types()` must be called once during single-threaded import / app / schema construction, before any request handling begins. The function mutates a process-global registry **and** mutates class objects (annotations, attached fields, `__strawberry_definition__`, `__django_strawberry_definition__`); the registry is intentionally lockless (see `registry.py:28-33`) and concurrent finalization can produce partial Strawberry definitions. Calling the finalizer from a request thread, async resolver, or any other concurrent context is **not supported**. Future helpers that auto-trigger finalization must be constrained to schema construction time or must acquire a real lock around the finalizer.
- A `DjangoType` declared **after** `finalize_django_types()` returns raises `ConfigurationError` from `__init_subclass__` with the message "`finalize_django_types()` already ran; cannot register `<TypeName>` after finalization. Call `registry.clear()` first if this is a test." This is the contract that makes test isolation predictable: tests use the autouse fixture pattern at `tests/types/test_base.py:46-51` (`registry.clear(); yield; registry.clear()`) and never see a stale pending-relation set.
- **`registry.clear()` resets registry state for fresh type classes; it does not roll back class mutation.** `clear()` resets `_types`, `_models`, `_enums`, `_definitions`, `_pending`, and `_finalized`, so the next test's `__init_subclass__` and `finalize_django_types()` calls behave like a fresh process *for newly created classes*. It cannot remove `__strawberry_definition__` from already-finalized classes, cannot remove relation resolver attributes from mutated classes, and cannot remove `__django_strawberry_definition__` or rewritten `__annotations__`. Tests must not reuse finalized `DjangoType` classes after `clear()`; the autouse fixture pattern naturally avoids this because each test redefines its types inside the test function or fixture.
- **Pending records are dropped after a successful resolution.** The finalizer calls `registry.discard_pending(resolved)` once phase 1 has matched every pending entry to either a target type or the consumer-authored escape hatch. Post-finalization, `registry.iter_pending_relations()` returns an empty iterator. This keeps schema-audit and diagnostic code from seeing historical records that are no longer pending.
## Test fixtures and acceptance criteria
### Fakeshop coverage gap
The fakeshop product graph (`examples/fakeshop/fakeshop/products/models.py`) covers FK and reverse FK only:
- `Item.category` / `Category.items`
- `Property.category` / `Category.properties`
- `Entry.item` / `Item.entries`
- `Entry.property` / `Property.entries`
It has **no OneToOne and no M2M relations**. The acceptance criteria require all five cardinalities. To close this gap, add unmanaged synthetic Django models under `tests/fixtures/cardinality_models.py`:
- `User` and `Profile(OneToOneField(User))` — covers forward OneToOne and reverse OneToOne.
- `Author`, `Tag`, and `Book(ForeignKey(Author), tags=ManyToManyField(Tag))` — covers forward M2M and reverse M2M.
Implementation rules (informed by the existing in-test pattern at `tests/types/test_converters.py:41-72` and `tests/optimizer/test_field_meta.py:82-146`):
- Each model declares an explicit `class Meta: app_label = "tests_cardinality"; managed = False`. The `managed = False` flag avoids creating database tables; resolver-execution tests that need persistence either monkeypatch a queryset or are scoped under a separate fixture (out of foundation scope).
- Models are module-scoped so Django's app registry sees one copy each; per-test inline declarations create the model-registration warning storm visible across the rest of `tests/types/test_base.py`.
- **No `tests/conftest.py`** and **no `apps.get_app_config(...)` mutation** by default — the existing tests work without either, and the autouse `_isolate_registry` fixture pattern at `tests/types/test_base.py:46-51` is replicated per-file. If reverse-relation discovery requires an additional Django app to be registered, prove it in a small spike before adding `apps.get_app_config(...)` calls.
### Cyclic acceptance tests (new)
Under `tests/types/test_definition_order.py`:
- `Category` declared before `Item`; `Item.category` resolves to `CategoryType`; `Category.items` resolves to `list[ItemType]`.
- `Item` declared before `Category`; same assertions hold.
- `Profile` declared before its target; reverse OneToOne resolves to `target_type | None`.
- M2M cycle (`Author <-> Book` via `tags`); both sides resolve.
- Multi-cycle (`Category <-> Item <-> Entry <-> Property <-> Category`) finalizes successfully and produces concrete types on every edge.
- Unresolved target (`ItemType` declared but `CategoryType` never registered) raises `ConfigurationError` from `finalize_django_types()` with the source model, source field, and target model named.
- **Annotation-only override**: consumer-supplied relation annotation (`items: Annotated[list["ItemType"], strawberry.lazy("...")]`) survives finalization unchanged: the annotation on the class equals what the consumer wrote, no pending-relation rewrite occurs, and `DjangoTypeDefinition.consumer_authored_fields` contains the field name.
- **Field/resolver override**: consumer-assigned `items: list["ItemType"] = strawberry.field(resolver=custom_items)` survives finalization unchanged: `_attach_relation_resolvers` skips the field, the consumer's resolver remains attached on the class, `DjangoTypeDefinition.consumer_authored_fields` contains the field name, and an in-process schema query routes through the consumer's resolver.
- **Decorator override**: same shape with `@strawberry.field` decorating a method; resolver attachment skips the field; the consumer's method body executes during a query.
- **Forward-reference shapes** (one acceptance test per shape; documents which forms are supported in 0.0.4):
  - same-module string annotation: `items: list["ItemType"]` with both `ItemType` declared in the same module.
  - `from __future__ import annotations` stringified ref: every annotation becomes a string at class-body time.
  - cross-module `Annotated[list["OtherType"], strawberry.lazy("other.module")]`.
  - manual annotation referencing a non-primary target type (test pinned to skip with a clear reason if multi-type-per-model support is not yet implemented).
  Any shape that does not work in 0.0.4 is documented as such in the test docstring and in `docs/FEATURES.md`, not silently skipped.
### End-to-end schema tests (new)
Under `tests/types/test_definition_order_schema.py`:
- Declare a cyclic `DjangoType` graph in "bad" import order on the FK fakeshop graph (which has real database tables via the example app). Call `finalize_django_types()`, decorate a `@strawberry.type Query` with a list resolver returning `list[ItemType]`, construct `strawberry.Schema(query=Query)`, and execute a nested query (`{ allItems { name category { name } } }`) against seeded fakeshop data. Pass when the response contains the expected nested data. This is the test that proves the foundation works for users, not just for internal metadata.
- **M2M test (metadata-only)**: the cardinality fixture's M2M models are unmanaged (`managed = False`), so a real `{ allBooks { title tags { name } } }` execution would require creating the through table at test time. The foundation slice keeps the M2M test **schema-shape-only**: it asserts that the Strawberry schema builds, the GraphQL type for `Book.tags` is `[Tag!]!`, and the introspection query (`{ __type(name: "Book") { fields { name type { kind ofType { name } } } } }`) returns the expected shape. DB-backed M2M execution belongs in a later slice that creates the through table or adds an M2M relation to fakeshop.
- **Boundary regression**: declare a `@strawberry.type Query` *before* `finalize_django_types()`. Whether this passes or fails is decided by Spike A; the test is written to match the documented behavior. If the boundary requires finalization-before-decoration, this test asserts the documented `ConfigurationError` (or the documented Strawberry-side error).
- **Phase 2/3 partial-mutation regression**: deliberately construct a graph that resolves cleanly in phase 1 but causes a Strawberry-side error in phase 3 (e.g., a consumer annotation that points at a type Strawberry cannot resolve). Catch the error, assert `registry.is_finalized() is False`, then assert that calling `finalize_django_types()` again on the same partially-mutated classes is **not** documented to recover — the recovery path is `registry.clear()` plus fresh class recreation. This pins the partial-mutation contract from the finalizer docstring.
- **Module-not-imported regression**: define a `DjangoType` in a separate module that is never imported, declare a sibling type that references its model, call `finalize_django_types()`, and assert `ConfigurationError` with the unresolved-targets format. Then import the missing module, call `registry.clear()` and recreate types, and assert finalization succeeds. Pins the import-discovery contract.
### Optimizer regression tests (new)
Under `tests/optimizer/test_definition_order.py`:
- `walker.plan_relation(field, target_type, info)` returns the same `("select", "default")` / `("prefetch", "default")` / `("prefetch", "custom_get_queryset")` decisions for cyclic graphs after finalization.
- `DjangoOptimizerExtension.check_schema(schema)` returns no warnings for any reachable type whose relation targets are registered.
- `_optimizer_field_map` reads via `cls.__django_strawberry_definition__.field_map` produce identical content to today's class-attribute reads.
### Idempotency / isolation tests (extends existing `tests/test_registry.py`)
The file `tests/test_registry.py` already exists (it is currently sparse; most registry coverage lives in `tests/types/test_base.py:55-86`). The slice **extends** that existing file with:
- Calling `finalize_django_types()` twice mutates state once (asserts a side-effect counter incremented by the call only ticks on the first invocation).
- A new `DjangoType` registered after finalization raises with the documented message ("finalize_django_types() already ran; cannot register …").
- `registry.clear()` returns the package to a state where `finalize_django_types()` runs cleanly again on a fresh set of types.
- A leaked `_finalized=True` from a previous test does not affect the next test (verified through paired tests where the first installs and finalizes, the autouse fixture clears, and the second declares a new type without raising).
- **Phase 1 failure-atomicity**: declare one resolvable type and one type whose relation target is intentionally never registered. Call `finalize_django_types()` and catch `ConfigurationError`. Assert `registry.is_finalized()` is `False`, no `DjangoTypeDefinition.finalized` is `True`, and a follow-up call after registering the missing target completes successfully. This protects phase-1 retry behavior.
- **Phase 2/3 partial-mutation contract**: declare a graph that passes phase 1 but fails phase 3, catch the Strawberry-side error, assert `registry.is_finalized()` is `False`, and assert that calling `finalize_django_types()` again on the same classes is documented as unsupported (pins the contract from the finalizer docstring; the test does not assert recovery, it asserts that the documented recovery path is `registry.clear()` + fresh class recreation).
- **Pending-set cleanup**: after a successful `finalize_django_types()`, `list(registry.iter_pending_relations())` returns `[]`. After a phase-1 failure, the unresolved entries remain in `_pending` so the consumer can retry without re-declaring types.
- **Class-mutation residue**: after `registry.clear()`, the previously finalized classes still carry their mutated `__strawberry_definition__` and `__django_strawberry_definition__`; the test pins this as documented behavior so contributors do not file it as a bug.
### Existing tests that must change
- Any test in `tests/types/test_converters.py` and `tests/types/test_base.py` asserting that `convert_relation` raises immediately on a missing target is rewritten to assert finalization-time failure. Per the verification report this is the rewrite cost; expect 2-4 tests to be touched.
## Phased implementation order (within the slice)
The slice is ordered so each step lands a passing test suite. **Phase 0 is the spike gate; production code begins at Phase 1.**
0. **Phase 0 — Spike gate.** Write Spike A, B, and C under `scripts/spikes/`. Run them. Record the outcome inline in this spec's "Spike outcome (gates implementation)" section and in `README.md`'s schema-setup section. Delete the spike scripts only after their conclusions are captured. **No production-code phase below begins until Spike A's five pass criteria are recorded as passed.**
1. Add `DjangoTypeDefinition` dataclass at `types/definition.py` and the `PendingRelation` dataclass at `types/relations.py`. No behavior change yet.
2. Extend `TypeRegistry` with `register_definition`, `get_definition`, `iter_definitions`, `add_pending_relation`, `iter_pending_relations`, `discard_pending`, `is_finalized`, `mark_finalized`, and the extended `clear`. Delete `lazy_ref`.
3. Implement `finalize_django_types()` at `types/finalizer.py`. No collection changes yet; the function runs against an empty pending list.
4. Split `__init_subclass__` into the collection-only pseudocode. Move the `strawberry.type(cls, ...)` call out and into `finalize_django_types()`. Move `_attach_relation_resolvers` out and into `finalize_django_types()` (consuming `definition.selected_fields` and skipping `definition.consumer_authored_fields`). Add the post-finalization registration guard and the consumer-authored detection (annotation OR class-dict assignment).
5. Replace the eager `cls.__dict__` get_queryset detection with `_detect_custom_get_queryset(cls)` (MRO-aware) so abstract bases keep propagating the sentinel.
6. Migrate `_optimizer_field_map`, `_optimizer_hints`, `_is_default_get_queryset` reads to live on the definition. Mirror them as plain class attributes in `__init_subclass__` (not `@property`) for one minor version so the walker's `getattr(type_cls, ...)` reads keep working.
7. Add the cardinality fixture under `tests/fixtures/cardinality_models.py` (unmanaged models with explicit `app_label`; no `conftest.py` / app-registry mutation unless a spike proves it is required).
8. Rewrite the affected `tests/types/test_converters.py` / `tests/types/test_base.py` cases (relation-target-not-registered now succeeds at class creation, fails at finalization).
9. Add the new acceptance test files under `tests/types/test_definition_order.py`, `tests/types/test_definition_order_schema.py`, `tests/optimizer/test_definition_order.py`, and extend the existing `tests/test_registry.py` with the new idempotency / isolation / failure-atomicity sections.
10. Update documentation:
    - `README.md` — public-API list, the schema-setup snippet that shows the new `finalize_django_types()` call site (with both a correct example and a wrong-order example that surfaces the failure mode), and an explicit "import every module that defines `DjangoType` classes before calling `finalize_django_types()`" note with the most-common-failure-mode framing.
    - `docs/README.md` — quick-start snippet.
    - `docs/FEATURES.md` — capability catalog entry, including which forward-reference shapes are supported in 0.0.4.
    - `TODAY.md` — capability snapshot.
    - `CHANGELOG.md` — release entry summarizing the new capability and the new public API.
11. Update export points:
    - `django_strawberry_framework/__init__.py` — re-export `finalize_django_types`, add it to `__all__`.
    - `django_strawberry_framework/types/__init__.py` — re-export `finalize_django_types` so it is reachable as `from django_strawberry_framework.types import finalize_django_types` for symmetry with `DjangoType`.
12. Bump version metadata to `0.0.4`:
    - `pyproject.toml` (`version = "0.0.4"`).
    - `django_strawberry_framework/__init__.py` (`__version__ = "0.0.4"`).
## Public API delta
After this slice the public surface gains exactly one new symbol:
- `finalize_django_types: Callable[[], None]` — re-exported from both `django_strawberry_framework` (top-level) and `django_strawberry_framework.types` (subpackage), so consumers can import it the same way they import `DjangoType`.
Existing public names — `DjangoType`, `DjangoOptimizerExtension`, `OptimizerHint`, `auto` — are unchanged.
Version metadata bumps from `0.0.3` to `0.0.4` in both `pyproject.toml` and `django_strawberry_framework/__init__.py:__version__`.
The `__django_strawberry_definition__` attribute is *not* part of the public API surface but is documented as a stable internal hook for the optimizer and future subsystems.

## Failure modes and rollback
- If Spike A fails (deferred `strawberry.type(cls)` proves unsafe), the slice pauses. The fallback is Strategy 2 (post-`__strawberry_definition__` patching). Rollback cost: rewrite the finalizer; collection phase and registry extensions are reusable.
- If Spike B exposes a Strawberry behavior we cannot work around, the foundation slice degrades to a documented "two-pass" requirement: users call `finalize_django_types()` *before* schema construction. This is already the foundation strategy; the failure simply delays the future auto-trigger work.
- If a reviewer can demonstrate that any of the seven invariants in "Invariants this slice must protect" is violated by the proposed design, the slice is re-planned before code lands. The current review feedback in [`docs/feedback.md`](feedback.md) forms the live review checklist until each item is resolved; the count and wording of items is expected to evolve until the slice ships.
## Note on source line references
This spec includes line numbers for some current source files (e.g., `walker.py:64`, `base.py:147`). Those are accurate at the time of writing but the optimizer subsystem and `__init_subclass__` are still moving, so reviewers should treat in-repo line references as soft hints and verify against the symbol names (`_optimizer_field_map`, `_attach_relation_resolvers`, `plan_relation`, etc.). Exact line references are reliable for **external** prior-art snapshots (`strawberry_django/...`, `graphene_django/...`, `graphene/...`) because those repos are pinned. Before implementation begins, the assigned author should refresh the in-repo lines in this spec's "Migration of current code" section against `main` so the contributor's edit targets are not stale.
## Cross-references
- Definition-order problem space, prior art, decision options: [`docs/spec-definition_order_independence.md`](spec-definition_order_independence.md).
- Long-term architecture, layered subsystems, prior-art line references: [`docs/spec-rich_schema_architecture.md`](spec-rich_schema_architecture.md).
- Operational entry point, install/test/build: [`README.md`](../README.md).
- North star and goal: [`GOAL.md`](../GOAL.md).
- Today's shipped surface: [`TODAY.md`](../TODAY.md).
- Tree layout: [`docs/TREE.md`](TREE.md).
