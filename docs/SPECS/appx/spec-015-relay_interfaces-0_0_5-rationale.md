# Rationale: spec-015 — Relay interfaces and Node foundation (deliberation, rejected alternatives)

Deliberative companion to [`spec-015-relay_interfaces-0_0_5.md`][spec-015]. The spec states the
contract; this file records the borrowing posture, the evidence for mutating `__bases__`, and the
alternatives each Decision rejected.

## Borrowing posture

Bears on [Decision 3][spec-015-decision-3] and [Decision 6][spec-015-decision-6].

**From strawberry-django — borrowed heavily.**

- **Resolver injection pattern** (`strawberry_django/type.py::_process_type`): replace each of the
  four `resolve_*` attributes only when it is absent or its `__func__` is `relay.Node`'s. The slice
  reuses an override-detection scheme already hardened against Strawberry version churn rather than
  inventing one.
- **`resolve_id` shape** (`strawberry_django/relay/utils.py::resolve_model_id`): read
  `root.__dict__` first, fall back to `getattr`, coerce to `str`, the same no-lazy-load philosophy
  as the rest of the optimizer cooperation.
- **`resolve_id_attr` shape** (`strawberry_django/relay/utils.py::resolve_model_id_attr`): one
  try/except around Strawberry's own scan with a `"pk"` fallback, so a consumer writes
  `relay.NodeID[...]` and the framework adds no `Meta` key.
- **`resolve_node` / `resolve_nodes` queryset shape** (`strawberry_django/relay/utils.py::resolve_model_node`
  and `::resolve_model_nodes`): every step has a counterpart here; the borrow is structural.
- **`MAP_AUTO_ID_AS_GLOBAL_ID` behavior**, tied to the per-type `Meta.interfaces` declaration
  instead of a global setting: a per-type opt-in keeps the contract local to the class declaration.
- **`is_type_of` virtual subclass** (`strawberry_django/type.py::_process_type`): root and relation
  resolvers return Django model instances, and Strawberry's interface dispatch uses `is_type_of` to
  identify the concrete type.

strawberry-django is not imported at runtime: a runtime dependency on it would bring back the
decorator-first plumbing the package exists to avoid.

**From django-graphene-filters / graphene-django — only the user-facing shape.** `class Meta:
interfaces = (Node,)` comes from the cookbook recipes schema, the shape [`GOAL.md`][goal] commits to
for the graphene-django users the package wants to migrate.

**Refused, and why each lost.** graphene-django's `__init_subclass_with_meta__` plumbing and `_meta`
options bag; its redacted-sentinel system and cascade FK resolution (the permissions subsystem
integrates through `get_queryset` instead); its connection-field auto-upgrade in
`convert_django_field`; strawberry-django's `_process_type` post-pass that rewrites `type_def.fields`
(the finalizer already attaches relation resolvers, so a second field-rewriting pass buys nothing);
strawberry-django's `StrawberryDjangoField` custom field class; decorator-style
`@strawberry_django.type(Model)`; and wrapping the model primary key in `relay.NodeID[py_type]` inside
`convert_scalar`, which lost because the `Node` interface already supplies `id: GlobalID!` and
resolves the attribute through `resolve_id_attr()`, so suppressing the synthesized scalar is the
simpler borrow.

## Decision 1: where interfaces are applied

Spec: [Decision 1][spec-015-decision-1].

**Why mutating `__bases__` is acceptable.** Mutating a class's bases before `strawberry.type(...)`
makes the class a `relay.Node` subclass and Strawberry records the interface on the object
definition:

```python
class Item(Base):
    name: str


Item.__bases__ = (Base, relay.Node)
strawberry.type(Item)
```

[`types/relay.py::apply_interfaces`][types-relay] performs exactly that assignment, wrapping a
rejected MRO or layout as a `ConfigurationError` that names the interface. It is the mechanism
graphene-django uses internally. Running the step between Phase 2 and Phase 3 means relation
resolvers attach to the still-undecorated class, which Phase 2 already requires.

**Rejected: requiring explicit `class Foo(DjangoType, relay.Node)` inheritance as the only path.** It
contradicts the `class Meta`-driven posture. The shipped code accepts direct inheritance as a second
entry path, because `implements_relay_node(type_cls)` gates the Relay work off the resolved MRO.

**A failed base assignment is attempted, not avoided:** the finalizer assigns the bases and will
surface any `TypeError` as a `ConfigurationError` naming the offending interface. Rejected fallbacks:
a replacement class with rewritten registry entries, or narrowing to explicit inheritance.

## Decision 2: id field handling

Spec: [Decision 2][spec-015-decision-2].

- **The trigger is the resolved Relay shape**, not tuple membership:
  [`types/base.py::_is_relay_shaped`][types-base] also fires for a consumer `@strawberry.interface`
  extending `relay.Node`, the canonical way to extend Relay-Node behavior, and for direct
  inheritance.
- **The suppressed key is the primary key's field name.** For a relation primary key the name
  (`user`) and attname (`user_id`) differ, and `_build_annotations` compares against `field.name`.
- **Rejected: a global id-mapping setting.** Activation stays per type on `relay.Node`.
  `Meta.globalid_strategy` and `RELAY_GLOBALID_STRATEGY` configure the GlobalID payload, not whether
  the mapping activates.
- **Rejected: rejecting composite primary keys unconditionally.** The error proposes an explicit
  `id: relay.NodeID[...]` annotation, so the gate honors it
  ([`types/relay.py::_check_composite_pk_for_relay_node`][types-relay]); a deterministic composite-key
  encoding is parked in `BACKLOG.md` as `composite_pk_globalid`. The gate asks Strawberry's scan
  directly because a Relay child of a Relay parent inherits the installed default, which swallows
  `NodeIDAnnotationError` into `"pk"`.

## Decision 3: Relay resolver injection

Spec: [Decision 3][spec-015-decision-3].

**Rejected: `super(cls, cls).resolve_id_attr()` with a `"pk"` fallback**, the faithful upstream port.
With `cls` bound at runtime, a Relay-shaped `DjangoType` subclassing another inherits the parent's
installed default, and the MRO walk from the child lands back on it re-bound to the child: infinite
recursion. The default instead reads the Phase-2.5 stamp `_stamp_relay_id_attr` writes, falling back
to a direct `relay.Node.resolve_id_attr.__func__(cls)` call for unstamped callers.

**Why the stamp.** Upstream caches the scan only on success, so the common `"pk"` fallback would re-run
the full MRO annotation scan on every `resolve_id` call, once per row. Seeding `_id_attr = None` on the
class itself also blinds Strawberry's inherited-cache read, which otherwise lets whichever class in a
chain resolved first decide the child's id attribute.

**Why `info` is keyword-only.** Strawberry's Relay machinery calls
`cls.resolve_node(node_id, info=info, required=...)`, so a positional `info` slot raises
`TypeError: got multiple values for argument 'info'`.

**Rejected: a `Meta.id_attr` key.** A parallel key would fragment the surface Strawberry's
`relay.NodeID[...]` annotation already provides.

**Rejected: consulting the optimizer extension inside `resolve_node`.** Upstream calls
`ext.optimize(qs, info=info)`; here the list paths get full optimizer treatment through the root-gated
extension, and the node defaults stay small so `DjangoNodeField` / `DjangoNodesField` and
`DjangoConnectionField` dispatch into them rather than replacing them.

## Decision 4: validation

Spec: [Decision 4][spec-015-decision-4].

The interface check is `hasattr(entry, "__strawberry_definition__") and
entry.__strawberry_definition__.is_interface`, which forces every accepted entry to be a real
Strawberry interface and is robust against changes to `relay.Node` itself. Duplicates are rejected
rather than tolerated: base injection no-ops idempotently, so tolerating them would only let typos
hide. The six `strawberry.relay` non-interface helpers are matched by identity before the generic
non-class branch because `relay.NodeID` is a `typing.Annotated` alias that would otherwise be rejected
without being named.

## Decision 5: lifecycle and idempotency

Spec: [Decision 5][spec-015-decision-5].

**Rejected: new tracking state on the definition.** Any such state would be redundant with
`cls.__bases__` and would have to be re-validated across clear/redefine cycles; the MRO is the source
of truth.

## Decision 6: compatibility with the override contract

Spec: [Decision 6][spec-015-decision-6].

**Rejected: `is_type_of` injection only for Relay-declared types.** Unconditional injection costs one
method per class and removes the "Cannot determine type for object of model X" failure an interface
field returning a Django model would otherwise hit once a type gains an interface. The `__func__`
precedence rule for the four `resolve_*` methods matches strawberry-django, so migrating consumers are
not surprised.

## Decision 7: optimizer and projection invariants

Spec: [Decision 7][spec-015-decision-7].

`resolve_id` reads `root.__dict__` before `getattr` because the optimizer keeps the pk attname in
`only()`; reversing the order costs a query per row. GlobalID handling lives entirely in the Relay
resolvers, so the walker sees the Django primary-key column it always saw, and the field map stays the
optimizer's source of truth because suppression happens later, in `_build_annotations`.

## Decision 8: registry implications and one-type-per-model

Spec: [Decision 8][spec-015-decision-8].

The node defaults resolve their model through the type's own definition, which needs no answer to
"which of several types per model owns node lookup". Leaving that question to `Meta.primary` and the
GlobalID payload strategies kept this slice to the interface seam; those specs answer it.

## Decision 9: async resolver support

Spec: [Decision 9][spec-015-decision-9].

`resolve_id_attr` and `resolve_id` stay sync because they touch no database, and promoting them would
force `await` plumbing through every node serialization. The node defaults materialize through
Django's native async ORM (`aget`, `afirst`, `async for`); **rejected: `sync_to_async` wrapping**, which
the native API makes unnecessary. A coroutine returned from `get_queryset` on the sync path raises
`SyncMisuseError` at the shared visibility boundary ([`utils/querysets.py`][utils-querysets]) rather
than surfacing as `AttributeError: 'coroutine' object has no attribute 'filter'`.

## `### Custom Relay resolver override` — the `relay.NodeID` spelling

Spec: [User-facing API][spec-015-user-facing-api].

The non-pk node id is a subscripted `relay.NodeID[str]` annotation on the target column. The bare
`Annotated[str, relay.NodeID]` spelling does not register, because Strawberry expects `NodeIDPrivate`
instances in the metadata, which only subscription produces. An assigned
`id = strawberry.field(...)` on a Relay-shaped type is refused by
[`types/base.py::DjangoType.__init_subclass__`][types-base], since the `id` name belongs to the
interface.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[goal]: ../../../GOAL.md

<!-- docs/ -->

<!-- docs/SPECS/ -->
[spec-015]: ../spec-015-relay_interfaces-0_0_5.md
[spec-015-decision-1]: ../spec-015-relay_interfaces-0_0_5.md#decision-1-where-interfaces-are-applied
[spec-015-decision-2]: ../spec-015-relay_interfaces-0_0_5.md#decision-2-id-field-handling
[spec-015-decision-3]: ../spec-015-relay_interfaces-0_0_5.md#decision-3-relay-resolver-injection
[spec-015-decision-4]: ../spec-015-relay_interfaces-0_0_5.md#decision-4-validation
[spec-015-decision-5]: ../spec-015-relay_interfaces-0_0_5.md#decision-5-lifecycle-and-idempotency
[spec-015-decision-6]: ../spec-015-relay_interfaces-0_0_5.md#decision-6-compatibility-with-the-override-contract
[spec-015-decision-7]: ../spec-015-relay_interfaces-0_0_5.md#decision-7-optimizer-and-projection-invariants
[spec-015-decision-8]: ../spec-015-relay_interfaces-0_0_5.md#decision-8-registry-implications-and-one-type-per-model
[spec-015-decision-9]: ../spec-015-relay_interfaces-0_0_5.md#decision-9-async-resolver-support
[spec-015-user-facing-api]: ../spec-015-relay_interfaces-0_0_5.md#user-facing-api

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[types-base]: ../../../django_strawberry_framework/types/base.py
[types-relay]: ../../../django_strawberry_framework/types/relay.py
[utils-querysets]: ../../../django_strawberry_framework/utils/querysets.py

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
