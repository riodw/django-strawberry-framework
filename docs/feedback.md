# Review: docs/diff-spec-relay_interfaces.diff
Status: revision-needed
## DRY analysis
- Existing patterns reused: The diff extends the existing `DjangoType.__init_subclass__` collection pipeline rather than adding a parallel registration path: validation, field selection, annotation synthesis, `DjangoTypeDefinition` construction, registry registration, and class mirrors remain centralized in `django_strawberry_framework/types/base.py:73-137`. The new interface validator follows the existing Meta validation/error-shape locality around `_format_unknown_fields_error` and `_validate_meta` in `django_strawberry_framework/types/base.py:251-393`. Finalization reuses the established `registry.iter_definitions()` phase-loop shape and keeps relation resolver attachment in `_attach_relation_resolvers` instead of introducing a second relation path, matching `django_strawberry_framework/types/finalizer.py:84-112` and `django_strawberry_framework/types/resolvers.py:225-245`. Optimizer compatibility is preserved by continuing to rely on the precomputed field map resolved through `django_strawberry_framework/optimizer/walker.py:65-74`.
- New helpers a fix might justify: A small Phase 2.5 helper with one responsibility, for example `apply_relay_node_contract(type_cls)`, would serve `finalize_django_types()` after optional interface injection and would run the composite-pk check plus resolver injection whenever `implements_relay_node(type_cls)` is true. That avoids repeating the resolved-base check while fixing the direct-inheritance bypass. No new helper is required for the `resolve_node` signature bug; the installed function signature and tests should be corrected in place.
- Duplication risk in the current file: `tests/types/test_relay_interfaces.py` repeats the same local `CategoryNode` declaration with `model = Category`, `fields = ("id", "name")`, and `interfaces = (relay.Node,)` across most behavior tests. A local factory such as `build_category_node(...)` would reduce fixture drift and would have made it easier to add the missing Strawberry-call-shape tests. There is also documentation drift: `docs/FEATURES.md:66` says Relay defaults are wired through the optimizer extension, while `django_strawberry_framework/types/relay.py:187-190` explicitly defers node-lookup optimizer cooperation.
## High:
### `resolve_node` default has the wrong bound signature
`relay.Node.resolve_node` in Strawberry is called as `resolve_node(node_id, *, info, required=False)`. The installed classmethod wraps `_resolve_node_default(cls, info, node_id, required=False)`, so a Strawberry-style call passes the node id positionally into `info` and then passes `info` again as a keyword, raising `TypeError: _resolve_node_default() got multiple values for argument 'info'`. The current tests call `CategoryNode.resolve_node(info=None, node_id=...)`, which exercises a friendly keyword-only shape but not Strawberry's runtime shape.
Why it matters: Node lookups through Strawberry's Relay machinery will fail even though list-field `id` selection and direct helper calls pass. This violates `docs/spec-relay_interfaces.md`'s requirement that the attached public method signatures match Strawberry's `relay.Node` expectations.
Recommended change: Change the default signatures to mirror Strawberry exactly after `classmethod` binding, especially `def _resolve_node_default(cls, node_id, *, info, required=False)`. Prefer also aligning `resolve_id` and `resolve_nodes` to `def _resolve_id_default(cls, root, *, info)` and `def _resolve_nodes_default(cls, *, info, node_ids=None, required=False)`. Add regression tests that call `CategoryNode.resolve_node(str(pk), info=None)` and, ideally, one schema-level Relay node lookup path.
```django_strawberry_framework/types/relay.py:241:259
def _resolve_node_default(
    cls: type,
    info: Any,
    node_id: Any,
    required: bool = False,
) -> Any:
    ...
    qs = _assemble_node_queryset(cls, info, id_attr, node_id=node_id)
    if in_async_context():
        return qs.aget() if required else qs.afirst()
    return qs.get() if required else qs.first()
```
```django_strawberry_framework/types/relay.py:324:330
for attr, default_impl in _RELAY_RESOLVER_DEFAULTS:
    existing = getattr(type_cls, attr, None)
    node_default = getattr(relay.Node, attr, None)
    existing_func = getattr(existing, "__func__", None)
    node_func = getattr(node_default, "__func__", None)
    if existing is None or (existing_func is not None and existing_func is node_func):
        setattr(type_cls, attr, classmethod(default_impl))
```
### Direct `relay.Node` inheritance bypasses Relay finalization
The spec accepts `class Foo(DjangoType, relay.Node)` as a no-op duplicate when `Meta.interfaces` is also declared, and Decision 4 says the composite-pk check belongs in Phase 2.5 so it catches both `Meta.interfaces = (relay.Node,)` and direct `relay.Node` inheritance. The implementation short-circuits Phase 2.5 when `definition.interfaces` is empty, so a class that directly inherits `relay.Node` but omits `Meta.interfaces` keeps `relay.Node` in its MRO but never receives the composite-pk gate or the four resolver defaults. It also never suppresses the synthesized Django pk annotation, so schema construction can fail with Strawberry's `NodeIDAnnotationError`.
Why it matters: The resolved-base behavior is inconsistent. A consumer following Strawberry's native inheritance style gets a broken Relay type instead of either full support or a loud framework error. Composite-pk direct inheritance also misses the required `ConfigurationError`.
Recommended change: In Phase 2.5, run `apply_interfaces(...)` only when `definition.interfaces` is non-empty, but run `implements_relay_node(type_cls)` / composite-pk / resolver injection for every non-finalized definition after that. For id suppression, include direct inheritance in the collection-time predicate, for example `relay.Node in interfaces or issubclass(cls, relay.Node)`, or explicitly reject direct `relay.Node` inheritance without `Meta.interfaces` during validation. The former matches the spec more closely.
```django_strawberry_framework/types/finalizer.py:96:104
for type_cls, definition in registry.iter_definitions():
    if definition.finalized:
        continue
    if not definition.interfaces:
        continue
    apply_interfaces(type_cls, definition)
    if implements_relay_node(type_cls):
        _check_composite_pk_for_relay_node(type_cls)
        install_relay_node_resolvers(type_cls)
```
```django_strawberry_framework/types/base.py:557:584
suppress_pk_annotation = relay.Node in interfaces
pk_attname = source_model._meta.pk.name if suppress_pk_annotation else None
...
if suppress_pk_annotation and field.name == pk_attname:
    continue
annotations[field.name] = convert_scalar(field, cls.__name__)
```
## Medium:
### Relay Node docs overstate optimizer-extension integration
The feature docs say the four Relay defaults are wired through `cls.get_queryset` and the optimizer extension, but the implementation deliberately does not consult the optimizer extension in `_assemble_node_queryset`; the spec diff also changed Decision 3 to defer optimizer-extension consultation for node lookup. The docs should match the shipped behavior.
Why it matters: Consumers may expect node lookups to receive the same optimizer treatment as root list resolvers, but the current implementation only applies the default manager, `get_queryset`, and id filtering.
Recommended change: Update `docs/FEATURES.md` and any release/changelog wording that says node resolvers are optimizer-extension-backed. Phrase it as `get_queryset`-aware, with optimizer cooperation deferred to a follow-up slice.
```docs/FEATURES.md:66:66
Meta.interfaces accepts a tuple of Strawberry interface classes; when relay.Node is among them, the DjangoType becomes a Relay-node-shaped GraphQL type with id: GlobalID! and the four resolve_* defaults wired through cls.get_queryset and the optimizer extension.
```
```django_strawberry_framework/types/relay.py:187:190
The Relay-node-lookup path is not yet on the optimizer's hot path in
``0.0.5``; Decision 7's list-path invariants flow through the existing
root-gated ``DjangoOptimizerExtension``. A future slice can wire an
optimizer-extension lookup here without changing the four-step shape.
```
## Low:
### Unrelated `.gitignore` change makes root build artifacts trackable
The Relay interfaces spec does not call for packaging-ignore changes, but the diff removes `/build/` from `.gitignore`. That makes root build artifacts eligible for accidental commits while `pyproject.toml` still excludes `build` from Ruff and the repository already adds several docs under `docs/build/` explicitly.
Why it matters: This is unrelated release-surface churn and can cause future packaging artifacts to appear in `git status`.
Recommended change: Keep `/build/` ignored unless there is a separate, documented reason to start tracking root build outputs.
```.gitignore:17:21
# Distribution / packaging
.Python
-/build/
develop-eggs/
dist/
downloads/
```
## What looks solid
- The full repository test suite passes with the current checkout: `516 passed, 1 skipped`, and package coverage remains at 100%.
- `Meta.interfaces` validation is thorough for the intended `class Meta` path: single interface classes normalize correctly, invalid shapes are rejected, duplicate entries are rejected, and accepted interfaces are stored on `DjangoTypeDefinition`.
- The implementation preserves the important optimizer invariant that the Django pk remains in `DjangoTypeDefinition.field_map` even when the GraphQL `id` annotation is suppressed for `relay.Node`.
- The `is_type_of` injection is scoped and consumer-preserving, and the four resolver names are centralized in `_RELAY_RESOLVER_DEFAULTS` rather than duplicated across the installer.
### Summary
The implementation is close and the standard suite is green, but it needs revision before verification. The two blocking fixes are to make the injected `resolve_node` signature match Strawberry's actual call contract and to apply Relay-node finalization to direct `relay.Node` inheritance, not only to classes with a non-empty stored `Meta.interfaces` tuple. After those fixes, update the optimizer wording in the docs and restore the unrelated `/build/` ignore unless intentionally changed.