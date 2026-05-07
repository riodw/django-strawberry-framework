# Feedback on `docs/spec-foundation.md`
## Overall assessment
`docs/spec-foundation.md` is a strong implementation contract for the first foundation slice. It correctly narrows the broader architecture into the type-definition, registry, pending-relation, finalization, cyclic-test, fail-loud-error, and optimizer-preservation work needed before filters, orders, aggregates, fieldsets, permissions, and connection fields can be built safely.
The best parts of the spec are:
- clear release scope and explicit non-scope
- strong invariants against silent schema degradation
- a concrete finalization strategy instead of vague lazy-reference language
- explicit migration points from the current source
- acceptance coverage for declaration-order cycles and optimizer regressions
- a public API delta limited to `finalize_django_types()`
I would treat the spec as close to implementable, but I would fix the issues below before writing production code.
## Highest-priority feedback
### 1. Clarify the real finalization boundary
The spec says users call `finalize_django_types()` before constructing the Strawberry schema. That may be too late.
In the current package, consumers usually reference `DjangoType` classes inside `@strawberry.type` query classes:
- resolver return annotations such as `list[ItemType]`
- field annotations such as `item: ItemType`
- future `DjangoConnectionField(ItemType)` helpers
Strawberry may need `ItemType.__strawberry_definition__` when the query class itself is decorated, not only when `strawberry.Schema(query=Query)` is constructed. The spikes should explicitly test this shape:
- define several `DjangoType` classes without finalizing them
- call `finalize_django_types()`
- then decorate a `Query` class that returns `list[ItemType]`
- construct and execute a `strawberry.Schema`
Also test the reverse ordering:
- decorate `Query` before `finalize_django_types()`
- prove whether it fails, works, or stores enough lazy annotation state
The public contract should say the exact safe point. If the safe point is “before any Strawberry decorator processes a class that references these `DjangoType`s,” the docs and examples need to say that directly.
### 2. The spec calls deferred `strawberry.type` both “gated by spikes” and “committed”
The pre-implementation spike section says implementation must pause if Spike A fails. Later, “Strawberry finalization strategy (committed)” says the slice commits to deferring `strawberry.type(cls)`.
That is fine if Spike A has already passed. If it has not passed, the wording should be softened:
- “assumed strategy pending Spike A”
- “preferred strategy”
- “committed only after Spike A passes”
This matters because almost every production change depends on that outcome. A contributor should not be able to skip the spike and assume Strawberry finalization timing will work.
### 3. Preserve inherited `get_queryset` behavior
The collection pseudocode stores:
```python path=null start=null
has_custom_get_queryset = "get_queryset" in cls.__dict__
```
That is not equivalent to today’s behavior.
Current behavior intentionally supports abstract bases without `Meta` that override `get_queryset`; concrete subclasses inherit the flipped `_is_default_get_queryset` sentinel through normal MRO lookup. If the new definition object stores only `"get_queryset" in cls.__dict__`, this supported case regresses:
```python path=null start=null
class TenantScopedType(DjangoType):
    @classmethod
    def get_queryset(cls, queryset, info, **kwargs):
        return queryset.filter(tenant=info.context.tenant)

class ItemType(TenantScopedType):
    class Meta:
        model = Item
        fields = "__all__"
```
`ItemType` must still report custom queryset behavior. The spec should compute `has_custom_get_queryset` from the inherited sentinel or an MRO-aware helper, not only from `cls.__dict__`.
### 4. The optimizer backward-compat shim cannot be a normal `@property`
The spec suggests retaining:
```python path=null start=null
@property
def _optimizer_field_map(self):
    return self.__django_strawberry_definition__.field_map
```
The optimizer reads this from the class:
```python path=null start=null
getattr(type_cls, "_optimizer_field_map", None)
```
A normal instance property returns the `property` object when accessed on the class, not the field map. That would break the walker and schema audit.
Better options:
- keep assigning class attributes for one minor version and mirror the definition object values into them
- introduce a class-level descriptor
- update every read path to the definition object and do not promise a class-level shim
The simplest safe migration is to keep `_optimizer_field_map`, `_optimizer_hints`, and `_is_default_get_queryset` class attributes synchronized while the internal definition object becomes canonical.
### 5. Store selected Django field objects or make resolver generation explicitly `FieldMeta`-compatible
The finalizer pseudocode calls `_attach_relation_resolvers_for_definition(type_cls, definition)`, but `DjangoTypeDefinition` only stores `field_map: dict[str, FieldMeta]`.
Today `_attach_relation_resolvers(cls, fields)` receives real Django field objects. `_make_relation_resolver` needs field attributes such as:
- `name`
- relation cardinality flags
- `related_model.DoesNotExist` for reverse OneToOne
- `attname` for FK-id elision stubs
`FieldMeta` may be enough if resolver code is intentionally refactored to accept it, but the spec should say that. Otherwise, store `selected_fields: tuple[Any, ...]` on `DjangoTypeDefinition` and keep the resolver path closer to today’s behavior.
My recommendation: store selected Django fields now. They are useful for future rich field generation too, and they avoid losing metadata before `DjangoModelField` exists.
### 6. Manual annotations and pending relation finalization conflict
The spec keeps the current merge:
```python path=null start=null
cls.__annotations__ = {**synthesized, **existing}
```
But the finalizer later rewrites:
```python path=null start=null
p.source_type.__annotations__[p.field_name] = resolved_annotation
```
That will overwrite a user-authored annotation for the same relation field if a pending relation was recorded before the merge.
The spec should choose one of these contracts for 0.0.4:
- user annotations are not a stable override contract, and relation overrides are explicitly unsupported
- user annotations on relation fields are preserved and validated
- user annotations skip pending automatic relation resolution for that field
Because the spec also says `Annotated[..., strawberry.lazy(...)]` remains an optional explicit override path, I would make that path real and add tests for it. At minimum, do not silently overwrite user-authored relation annotations at finalization.
### 7. Align relation-kind vocabulary
The `PendingRelation` pseudocode uses:
```python path=null start=null
relation_kind: Literal["one", "many", "reverse_one_to_one"]
```
The current shared utility returns:
```python path=null start=null
Literal["many", "reverse_one_to_one", "forward_single"]
```
Pick one vocabulary and use it everywhere. I recommend keeping the current `forward_single` name because it is more precise than `one` and already matches `utils/relations.py`.
### 8. Add the post-finalization registration guard to the pseudocode
The lifecycle contract says a `DjangoType` declared after `finalize_django_types()` raises `ConfigurationError`, but the `__init_subclass__` pseudocode does not include that guard.
Add it explicitly near the start of the concrete-type path:
- abstract subclasses without `Meta` can still opt out cleanly
- concrete subclasses with `Meta` raise if the registry is already finalized
This prevents contributors from missing one of the most important lifecycle rules.
## Test and fixture feedback
### 9. Reconsider the proposed `tests/conftest.py` app-registration strategy
The spec proposes `tests/fixtures/cardinality_models.py` plus `apps.get_app_config(...)` registration in `tests/conftest.py`. There is no current `tests/conftest.py`, and manual app registration can become brittle with Django’s global app registry.
Current tests already use inline unmanaged synthetic models with `app_label` for specialized cases. The fixture strategy should be specific:
- define unmanaged test models with a unique `app_label`
- keep them module-scoped where possible to avoid repeated model-registration warnings
- only create database tables if resolver execution truly needs persistence
- avoid manual app-registry mutation unless a spike proves it is necessary
If reverse relation discovery requires registered test models, pin that in a small test before building the larger fixture suite.
### 10. Add schema integration tests, not only annotation tests
The new acceptance tests should assert more than `__annotations__` contents.
Add at least one end-to-end schema test that:
- declares a cyclic graph in “bad” import order
- calls `finalize_django_types()`
- exposes a list field through `@strawberry.type Query`
- constructs `strawberry.Schema`
- executes a nested query successfully
This is the test that proves the foundation actually works for users, not just for internal metadata.
### 11. Add a failure atomicity test
If `finalize_django_types()` raises because unresolved targets remain, the registry should not be left half-finalized.
Add a test that:
- declares one resolvable type and one unresolved relation
- calls `finalize_django_types()` and catches `ConfigurationError`
- verifies `registry.is_finalized()` is still false
- verifies no definition has been marked finalized unless the whole pass succeeded
This protects retry behavior in tests and avoids confusing partial state.
### 12. Keep existing registry test locations in mind
The spec says to add idempotency/isolation tests under `tests/test_registry.py`. Current registry coverage lives mostly in `tests/types/test_base.py`. Creating a new root test file is fine, but the spec should be explicit that this is a new file, not an existing one.
## Documentation and release feedback
### 13. Update `README.md` as well as docs pages
The phased implementation section says to update `TODAY.md`, `docs/README.md`, and `docs/FEATURES.md`. Since `finalize_django_types()` becomes public API, the root `README.md` should also be updated wherever it lists exported names or shows schema setup.
### 14. Include all export points
The public API delta mentions a top-level re-export in `django_strawberry_framework/__init__.py`. Also update `django_strawberry_framework/types/__init__.py` if `finalize_django_types()` should be available from the type subsystem.
### 15. Decide whether this slice bumps package version metadata
The spec calls this the `0.0.4` foundation slice, while the current project metadata is still `0.0.3` in `pyproject.toml` and `django_strawberry_framework/__init__.py`.
If implementation is meant to ship as `0.0.4`, include version updates in the implementation checklist. If not, remove the release-number language from the spec and call it the “next foundation slice.”
## Suggested spec edits before implementation
I would update `docs/spec-foundation.md` before code begins to:
1. clarify that the deferred Strawberry strategy is conditional until Spike A passes
2. define the exact point where users must call `finalize_django_types()`
3. preserve inherited `get_queryset` detection
4. replace the invalid `@property` optimizer shim guidance
5. store selected Django field objects or explicitly refactor resolver generation to consume `FieldMeta`
6. define the 0.0.4 manual-annotation contract for relation fields
7. align `PendingRelation.relation_kind` with `utils.relations.relation_kind`
8. add the post-finalization registration guard to the pseudocode
9. add schema-level and failure-atomicity tests
10. add `README.md`, export-point, and version metadata updates to the documentation/release work
## Bottom line
The spec is pointed in the right direction and is much stronger than the broader exploratory specs for implementation purposes. I would not start coding until the Strawberry timing spike is proven and the lifecycle/compatibility issues above are resolved in the text. After that, this is a solid first implementation slice for the larger `GOAL.md` architecture.