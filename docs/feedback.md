# Review - spec-032 Full Relay (logic-only pass over stripped skeletons)

Method: this pass read ONLY the `*.stripped.py` snapshots in `docs/shadow/current/`
(no source files, no tests, no scripts run). Strings/docstrings/comments are `...`,
so everything below is reasoned from control flow, names, and types. Findings are
phrased as **suspicions with a verification scenario** - they're gut-check grade,
not confirmed repros. Coverage caveat: `testing/relay.py` has no snapshot in
`docs/shadow/current/` (the snapshot run skipped the `testing/` subpackage), so the
test-helper module is unreviewed in this pass.

Verdict on the previously-flagged items: the skeletons confirm all three prior
fixes landed and are logically sound - `_coerce_pk_or_none` now derives its
coercion field from `resolve_id_attr()` (pk vs `get_field`, `FieldDoesNotExist` ->
raw passthrough), `_check_nodes_result` enforces the 1:1 length contract before
`_interleave`, and the async gatherer is awaitable-or-value. The interleave
machinery is correct for duplicates (`positions` indexes are allocated before the
`pks.append`, and `_order_nodes` emits one entry per input key even when the DB
returns one row). What follows is new.

## Suspicions (highest confidence first)

### S1 - P2: inheriting one relay Node DjangoType from another likely causes infinite recursion in `resolve_id_attr`

`types/relay.py::install_relay_node_resolvers` installs a default only when the
existing attribute is absent **or is exactly `relay.Node`'s** classmethod
(`existing_func is node_func`). And `_resolve_id_attr_default` resolves upward via
`super(cls, cls).resolve_id_attr()` with the **runtime** cls.

Now take `class ChildType(ParentType)` where both are relay-shaped with their own
`Meta`. At finalize, the installer inspects `ChildType.resolve_id_attr`, finds the
framework default **inherited from ParentType**, sees it is not `relay.Node`'s
function, and skips installation (it's misclassified as a consumer override). At
runtime, `ChildType.resolve_id_attr()` binds `cls=ChildType`, executes
`super(ChildType, ChildType).resolve_id_attr()`, the MRO search lands back on
*ParentType's installed copy of the same default*, which re-binds `cls=ChildType`
and re-executes the identical `super()` call -> `RecursionError`. Because
`_resolve_id_default`, `_resolve_node_default`, and `_resolve_nodes_default` all
call `cls.resolve_id_attr()`, every id emission and every refetch on the child
type recurses - it fails loudly, at least.

The telling asymmetry: `resolve_typename` got exactly this treatment via
`_FRAMEWORK_CLOSURE_MARKER` - `_inherits_framework_closure` detects an inherited
framework closure and **re-installs** a fresh one bound to the child's definition.
The four `_RELAY_RESOLVER_DEFAULTS` have no equivalent marker, and they're the
ones whose default uses dynamic `super(cls, cls)`.

**Script to confirm:** two relay-shaped DjangoTypes in an inheritance chain
(child with its own `Meta.model`), finalize, then call
`ChildType.resolve_id_attr()`. If it recurses, the fix is the same marker pattern
the typename installer already uses (stamp the installed classmethods; on a
subclass, treat an inherited stamped default as "not a consumer override" and
re-install). If DjangoType-subclassing-DjangoType is meant to be unsupported,
`__init_subclass__` should say so instead - `_detect_custom_get_queryset` walking
the MRO suggests chains are anticipated.

### S2 - P2: untyped `node`/`nodes` on a multi-type model can resolve to the wrong `__typename`

The untyped `DjangoNodeField()` returns a **raw Django model instance** under the
`Node` interface annotation. Concrete-type selection then happens in
graphql-core's abstract-type resolution, which consults each candidate type's
`is_type_of`. The framework's installed hook
(`types/relay.py::install_is_type_of`) is `isinstance(obj, (type_cls, model))` -
for a model with two registered types (say `BookType` primary, `BookAdminType`
secondary), **both** hooks answer True for every `Book` row. Whichever type
graphql-core happens to test first wins, regardless of which type the GlobalID
named.

All the careful decode routing (`_audit_primary_ambiguity`,
`_audit_model_label_routing`, `definition_for_graphql_name`) governs which type's
*resolvers* fetch the row - but `_resolve(...)` drops `resolved` after fetching
and hands the schema a bare model instance, so the routing decision never reaches
type resolution. `node(id: <BookAdminType gid>)` could plausibly come back as
`__typename: "BookType"` (or vice versa, ordering-dependent). Connections don't
hit this because they're concretely typed; the Node interface refetch is the
first abstract-resolution surface the package ships, so this is in 032's scope.

**Script to confirm:** one model, two registered types (one primary), an untyped
`node: relay.Node | None = DjangoNodeField()`, query each type's gid and assert
`__typename`. If it misroutes, candidate fixes: have the node resolvers wrap or
annotate the instance with the decode-resolved type (e.g. a per-request
`resolve_type` hint), or tighten `is_type_of` for non-primary types - both need
design care, hence flagging rather than prescribing.

### S3 - P3 (inherited, widened by 032): reverse relations without `related_name` - field name vs instance accessor mismatch

Synthesis seeds the relation connection with
`_build_relation_connection_resolver(target_type, name)` where
`name = field.name`, and the resolver does `getattr(root, accessor_name).all()`.
For a reverse FK **without** `related_name`, Django's `ForeignObjectRel.name` is
the related *query* name (`"book"`) while the instance accessor is
`get_accessor_name()` (`"book_set"`) - `getattr(root, "book")` would
`AttributeError`. The same assumption predates 032
(`types/resolvers.py::many_resolver` uses `getattr(root, field_name)` too), which
is why I grade it inherited - but 032 both widens the exposure (every relay node's
many-relations now auto-synthesize connections) and bakes `field.name` into the
generated field name and the collision guard. Notably `FieldMeta` carries a
`reverse_connector_attname` slot, so the raw material for the correct accessor may
already exist.

**Script to confirm:** a model pair with a plain `ForeignKey` (no
`related_name`), parent type relay-shaped, query both the Phase-2 list field and
the synthesized connection. If your fixtures all set `related_name`, this has
been invisible to CI from the start.

### S4 - question, not a defect: where does the `node`/`nodes` field type come from?

Both `relay.py` resolvers are annotated `-> Any` (the skeleton preserves
annotations, so that's the real source). `strawberry.field(resolver=...)` can't
type a field from `Any`, so the schema type must come from the consumer's class
annotation at the assignment site (`node: BookType | None = DjangoNodeField(...)`).
Two things to verify: (a) the documented usage always annotates the assignment;
(b) the failure mode when a consumer writes a bare `node = DjangoNodeField()` is
strawberry's generic missing-annotation error, with no framework-named message.
If (b) is ugly, a one-line check or doc note is cheap. Also worth confirming the
typed variant's annotation is checked for compatibility with `target_type` -
nothing in the skeleton cross-validates `node: AuthorType = DjangoNodeField(BookType)`
(`_check_typed_match` would make every query error at runtime, which is loud but
late).

## Minor notes (no scripts needed unless you disagree)

- `_check_nodes_result` calls `len(result)` - a consumer `resolve_nodes` override
  returning a generator dies with a bare `TypeError` instead of the named
  `ConfigurationError`. One `list(result)`-or-message away from airtight.
- `decode_global_id` called before finalize (effective strategies unstamped)
  raises `ConfigurationError`, which the root fields translate to
  `GLOBALID_INVALID` - a configuration problem masquerading as a bad-id error.
  Unreachable through-schema (finalize precedes serving); only odd harnesses see it.
- The async gatherer awaits each per-type `resolve_nodes` **sequentially**.
  Correct, and defensible given Django's per-connection serialization, but it's a
  latency choice worth one docstring word so nobody "fixes" it into
  `asyncio.gather` against a single shared connection.
- Synthesized relation connections run per-parent: each parent row pays its own
  window query (plus `COUNT` when `totalCount` is exposed) - inherent to
  relation-seeded connections, but a nested-connection query-count pin in the
  fakeshop tests would document the cost contract.
- The synthesis collision guard compares against `to_camel_case` - i.e. the
  *default* name converter. A schema configured with a custom converter could
  collide post-guard. Fine to leave if custom converters are out of scope; worth
  a sentence somewhere if not.
- `registry.unregister` removes the definition but leaves
  `_connection_type_cache` entries for the type (only full `clear()` purges).
  Test-utility-only surface; cosmetic.

## Verified sound in this pass (logic traced, no action)

- **Decode boundary:** `_decode_or_graphql_error` wraps *only* the decode call;
  `SyncMisuseError` (a `ConfigurationError` subclass) cannot arise inside decode,
  so the narrow `except ConfigurationError` doesn't swallow it - the prior
  contract holds structurally, not just by test pin.
- **Interleave/dedup/duplicates:** position indexes allocated pre-append; default
  `resolve_nodes` -> `_order_nodes` emits exactly one entry per input key (string
  keys built from the same coerced values on both sides), so duplicate ids and
  missing rows both produce correct positional output; `_check_nodes_result`
  catches the override that breaks it.
- **Finalize ordering is load-bearing and correct:** `_audit_primary_ambiguity`
  runs before synthesis (so `registry.get(related_model)` can't return None for a
  multi-type model with no primary), interfaces are applied before
  `implements_relay_node` checks in the same loop, effective strategies are
  stamped before `_audit_model_label_routing` reads them, and synthesis precedes
  `_bind_filtersets` so sidecar registrations are orphan-validated in the same run.
- **Re-entrancy:** the synthesized-marker branch re-suppresses the list form a
  partial-finalize rerun re-attached; the once-discarded pendings mean the popped
  annotation is never restored, so the re-attached Phase-2 attr is inert and then
  deleted again - the end state is consistent for both `"connection"` and
  `"both"` shapes.
- **Sync/async split:** `in_async_context()` checked per call; the sync pipeline's
  lazy QuerySet flows through `ListConnection.resolve_connection`'s
  AsyncIterable path under ASGI (Django QuerySets are async-iterable), which is
  exactly why the relation resolver can be sync-only; `_apply_get_queryset_sync`
  closes the rejected coroutine before raising.
- **Connection generation:** always-concrete classes via `types.new_class` over
  `DjangoConnection[target]`, single cache keyed by target, `first`+`last` guard
  ahead of `super()`, `totalCount` attach guarded by countability and computed
  only when selected (fragment-recursive check).
- **Validation ladders:** `relation_shapes` stage-1 (isinstance-before-membership,
  defensive `dict()` copy) and stage-2 (unknown -> excluded -> non-relation ->
  single-valued -> consumer-authored, sorted messages) are complete and ordered
  so the most specific error wins; the relay `id` gate and the
  `_RELAY_NON_INTERFACE_HELPERS` identity table sit before the generic
  non-class rejection.
- **Registry hygiene:** `register_with_definition` rollback restores the exact
  pre-state including the prior primary; `clear()` co-clears the node-field
  ledger and connection cache cycle-safely; the no-Node-types contract check uses
  a plain import so it cannot silently skip.
