# Spec-044 DRY review: `DjangoDebugExtension`

## Scope and conclusion

This review covers the complete current
`docs/spec-044-debug_extension-0_0_14.md`, every method and class in
`django_strawberry_framework/utils/`, the utility call sites relevant to the
new extension, the existing optimizer extension, the debug-toolbar
middleware, Strawberry's extension lifecycle/merge machinery, Django's query
logger and `CaptureQueriesContext`, and the existing fakeshop test helpers.
`docs/feedback.md` was deliberately excluded.

The central conclusion is:

> Spec-044 should reuse framework-owned behavior aggressively, but should not
> import any current `django_strawberry_framework.utils` helper in the
> production debug module.

That is not a failure to be DRY. The existing utility layer is already divided
by semantic ownership: Relay pagination, generated inputs, permissions,
queryset visibility, write decoding, relation classification, string/type
normalization, converter dispatch, and optional imports. None owns
operation-scoped query-log capture or exception serialization. Reusing one
because its name sounds adjacent would couple unrelated contracts and make the
code less maintainable.

The highest-quality DRY shape is:

1. Reuse Strawberry's `SchemaExtension.on_operation` and `get_results`
   lifecycle exactly once.
2. Reuse Django's `force_debug_cursor`, `CursorDebugWrapper`, and
   `queries_log` rather than implementing SQL instrumentation.
3. Put the minimal overlap-safe bracket, snapshots, serializers, exception
   walk, and payload assembly in private helpers in
   `django_strawberry_framework/extensions/debug.py`.
4. Keep one source for every debug-specific rule inside that module.
5. Reuse the package's existing testing, schema-reload, and seed helpers.
6. Do not promote a debug-specific helper into `utils/` until a second real
   production consumer needs the same contract.

## Priority DRY obligations

### P0. Ride the engine lifecycle; do not create another orchestration layer

`DjangoDebugExtension` should implement only:

- one synchronous generator `on_operation`; and
- one synchronous, pure `get_results`.

Strawberry already:

- turns the generator into a context manager;
- enters the same sync hook in both sync and async execution;
- unwinds extension hooks in LIFO order;
- assigns the operation's `execution_context`;
- calls `get_results`; and
- merges returned dictionaries into the response extensions map in extension
  list order.

Do not add any of the following:

- a `resolve` hook;
- an `on_execute` twin;
- separate sync and async extension classes;
- a view wrapper;
- Django middleware;
- response JSON mutation;
- context mutation;
- a custom extensions merger; or
- a transport-specific hook.

Each would duplicate an engine seam and create another lifecycle to keep in
sync.

### P0. Reuse Django's query logger, not a package-owned query recorder

The extension should use each Django connection's existing:

- `force_debug_cursor` flag;
- `CursorDebugWrapper`;
- `queries_log` bounded deque;
- backend-specific `last_executed_query` formatting;
- transaction-statement logging; and
- duration formatting.

Do not copy or port:

- graphene's cursor wrapper;
- `execute_wrapper`;
- a custom cursor class;
- manual timing;
- parameter interpolation;
- transaction introspection;
- a SQL parser; or
- query event objects.

Django already owns these backend-sensitive behaviors. The package should only
own the lifecycle bracket and response serialization.

### P0. Do not instantiate `CaptureQueriesContext`

`CaptureQueriesContext` is the semantic precedent, not the reusable object for
this feature. Direct use would also:

- call `ensure_connection()` for every alias;
- force-open unused databases;
- disconnect and reconnect the global `request_started -> reset_queries`
  signal per operation;
- restore `force_debug_cursor` without overlap reference counting; and
- expose a single-context start/end shape that is not safe for overlapping
  async operation contexts sharing one connection wrapper.

Reuse its small semantic contract—save the flag, enable logging, snapshot the
log length, restore the saved flag—without reusing its test-oriented connection
and signal side effects.

### P0. Single-site the reference-counted cursor bracket

There should be exactly one private context-manager helper for acquiring and
releasing a debug-cursor token for one connection. It should be the only code
that reads or writes:

- the module-private active-capture map;
- the module-private lock;
- the reference count;
- the saved original `force_debug_cursor` value; and
- `connection.force_debug_cursor`.

A compact private state record should carry:

- the original flag value; and
- the active depth.

The helper's contract should be:

1. Lock.
2. On the first acquire for that connection object, save the flag, set it to
   `True`, and create state at depth one.
3. On an overlapping acquire, increment depth without replacing the original
   saved value.
4. Snapshot `len(connection.queries_log)` for this operation.
5. Yield the operation-local snapshot.
6. In `finally`, lock, decrement, and only at depth zero restore the saved
   value and delete the map entry.

Do not duplicate entry/exit logic inside `on_operation`, per-alias loops, test
helpers, or serializers. Do not key the map by alias: aliases identify settings
entries, while the mutable flag belongs to a concrete connection wrapper. The
connection object is the correct coordination identity.

### P0. Let `ExitStack` own the multi-alias unwind

`on_operation` should materialize `connections.all()` once, preserve that
order, and enter one private capture context per connection through a single
`contextlib.ExitStack`.

That gives one implementation of:

- partial-setup unwind when a later alias fails;
- reverse-order release;
- normal-operation release;
- exceptional-operation release; and
- serializer-failure release.

Do not write a second manual `acquired = []` / reverse loop. Do not call
`connections.all()` again during teardown and attempt to match by position:
configured aliases or thread-local wrappers could differ, and the snapshots
already own the exact connection objects acquired.

### P0. Make one operation-local snapshot record

Use one private immutable record for the query-log snapshot. It should retain
only what teardown needs:

- the connection object; and
- the starting log length.

Alias and vendor should be read from that same retained connection when rows
are serialized. Do not store a parallel alias list, vendor map, or look
connections up again through `connections[alias]`.

One helper should turn a snapshot into its operation entries:

1. Materialize `list(connection.queries_log)` exactly once.
2. Clamp the starting index with `min(start, len(entries))`.
3. Return the suffix.

This single-sites the non-sliceable-deque conversion, reset-shortening guard,
and documented best-effort rollover behavior.

### P0. Single-site SQL row serialization

Use one private SQL-row serializer for every database alias and every test. It
should be the only code that:

- converts `entry["time"]` to `float`;
- preserves `entry["sql"]` verbatim;
- derives `isSlow`;
- derives `isSelect`;
- emits the six wire keys; and
- reads the connection's `vendor` and `alias`.

Compute `duration` once and normalize the SQL string for the selection sniff
once. Put the graphene-compatible threshold in one private named constant,
for example `_SLOW_QUERY_SECONDS = 10.0`.

Do not:

- derive `isSlow` and `isSelect` in separate later passes;
- use `utils.strings.graphql_camel_name` to manufacture fixed protocol keys;
- copy the serializer into tests;
- normalize `executemany` SQL;
- add a second raw Django-log representation; or
- emit an extra `time` field duplicating `duration`.

The fixed response dictionary itself is the one source of the wire spelling.
Turning every key into a module constant would add indirection without
eliminating duplication, provided the dictionary construction remains
single-sited.

### P0. Single-site terminal exception discovery

Use one private helper to map an outer result `GraphQLError` to the terminal
execution exception:

1. Reject an outer error whose `original_error` is `None`.
2. Start from the first non-`None` original.
3. Follow `GraphQLError.original_error` while another original exists.
4. Track object identities so malformed cycles terminate.
5. Retain an explicitly raised terminal `GraphQLError`.

Use one collector over `execution_context.result.errors` that:

- handles `result is None`;
- handles `errors is None`;
- calls the terminal helper once per outer error;
- preserves result-error order; and
- emits one row per qualifying result error without speculative
  deduplication.

Do not place chain walking inside the serializer, `on_operation`, and tests as
three copies. Do not catch resolver exceptions in a `resolve` hook; graphql-core
has already accumulated them.

### P0. Single-site exception row serialization

Use one private exception serializer that emits:

- `excType = str(type(exc))`;
- `message = str(exc)`; and
- `stack = "".join(traceback.format_exception(type(exc), exc,
  exc.__traceback__))`.

Do not:

- use `traceback.format_exc()` after the `except` scope;
- duplicate the traceback call for chained and unchained errors;
- use the mutation `FieldError` envelope;
- route through Django validation-error utilities;
- create Strawberry output types; or
- use Django's `force_str` unless a demonstrated lazy-string case requires it.

The debug row is a wire dictionary, not a mutation validation leaf.

### P0. Build the payload in one place

Use one private payload builder that receives:

- the ordered snapshots; and
- the operation result.

It should return exactly:

- one `sql` list assembled in connection order and log order; and
- one `exceptions` list assembled in result-error order.

This is the only place that should know the two-list payload shape. The
extension hook should orchestrate acquisition/yield/teardown; it should not
inline row construction.

Never use class-level empty lists or a shared module-level empty payload. Each
completed operation needs fresh containers.

### P0. Use one absent-stash sentinel and a pure `get_results`

The instance should have exactly one operation payload attribute. `None` is a
sufficient absent sentinel because a completed payload is always a dictionary,
even when both lists are empty.

`get_results` should:

- return `{}` while the stash is absent;
- return `{"debug": self._payload}` after teardown;
- never build the payload;
- never pop or clear the payload;
- never mutate `execution_context`;
- never mutate an existing `ExecutionResult.extensions`; and
- return the same result on repeated calls.

This preserves the engine's merge behavior and coerced-exception double-call
idempotence without a second state machine.

### P0. Rely on per-operation extension instances

At the Strawberry `>=0.316.0` floor, the class entry in `extensions=` is the
instance factory. Use plain instance state.

Do not reuse:

- `DjangoOptimizerExtension`'s singleton factory;
- optimizer `ContextVar`s;
- optimizer context-stash helpers;
- a process-global current payload;
- thread-local payload state; or
- request-context attributes.

The optimizer needs a shared instance to preserve its plan cache. The debug
extension has no cross-operation cache and should not inherit the machinery
that makes that exceptional lifecycle safe.

If the class needs no constructor beyond Strawberry's base behavior, do not
add one. If an explicit constructor is required for typing or stash
initialization, accept and pass through only the engine-owned
`execution_context` keyword and initialize the one stash; do not introduce a
generic `**kwargs` sink.

## Recommended private module shape

The exact names may change, but the implementation should converge on one
owner per rule:

```python
_SLOW_QUERY_SECONDS = 10.0
_cursor_capture_lock
_active_cursor_captures

_CursorCaptureState
_QueryLogSnapshot

_capture_query_log(connection)
_snapshot_entries(snapshot)
_serialize_sql_row(connection, entry)
_terminal_original_error(error)
_serialize_exception(exc)
_collect_exception_rows(result)
_build_debug_payload(snapshots, result)

DjangoDebugExtension.on_operation()
DjangoDebugExtension.get_results()
```

This is intentionally not a generic framework. It is the minimum set that
prevents duplicated debug semantics:

- coordinator state;
- operation snapshot;
- SQL leaf;
- exception leaf;
- exception-chain traversal;
- payload aggregate; and
- engine adapter.

Combining all of it into `on_operation` would be less DRY because tests would
have to reproduce or indirectly tease apart each rule. Splitting it further
into files or public classes would create more API than the one feature needs.

## Exhaustive audit of `django_strawberry_framework/utils`

### `utils/__init__.py`

Current exports are relation classification, string casing, and type
unwrapping. None applies. Do not add `DjangoDebugExtension` or its private
capture helpers here. The extension belongs to
`django_strawberry_framework.extensions`, and exporting internals from the
cross-cutting utility namespace would make them look supported.

### `utils/connections.py`

Despite the filename, this module owns GraphQL Relay connection pagination,
not Django database connections.

Reviewed symbols:

- `connection_sidecar_inputs_from_kwargs`
- `has_connection_sidecar_input`
- `has_connection_sidecar_kwargs`
- `is_ambiguous_empty_window`
- `WindowRangePlan`
- `WindowRangePlan._probe_increment`
- `WindowRangePlan.fetch_upper_bound`
- `WindowRangePlan.fetch_limit`
- `WindowRangePlan.wants_next_page_probe`
- `window_range_plan`
- `assert_window_fetch_mode`
- `assert_window_fetch_mode_for`
- `split_window_rows`
- `ConnectionWindowBounds`
- `derive_connection_window_bounds`
- `resolve_relay_max_results`
- `derive_keyset_window_bounds`
- `UnwindowableConnection`

None should be imported. SQL capture must not reuse pagination range plans,
window snapshots, sentinel-row logic, Relay caps, or sidecar predicates.
Naming a debug query-log record `ConnectionWindow` would also invite the wrong
association; prefer `QueryLogSnapshot` or equivalent.

### `utils/converters.py`

`convert_with_mro` owns ordered field-converter dispatch. Debug SQL and
exception rows have fixed shapes, not polymorphic form/serializer field
registries. Do not model the two serializers as an MRO registry or generic
converter table.

### `utils/errors.py`

Reviewed symbols:

- `field_error`
- `_str_list`
- `relation_field_error`
- `validation_error_to_field_errors`
- `join_error_path`

These construct the write mutation's `FieldError` envelope. A debug exception
row is intentionally raw and client-visible, has different keys, and is not a
validation result. Reuse would conflate two public protocols. Plain `str` calls
inside the private exception serializer are the correct local behavior; do not
promote `_str_list` or force the debug triple through it.

### `utils/imports.py`

Reviewed symbols:

- `import_attr_if_importable`
- `loaded_attr`
- `import_attr`
- `require_optional_module`

The debug extension imports only hard dependencies: Django, Strawberry, and
graphql-core. Import them directly. There is no absent-package state, install
hint, opt-in-preserving loaded-module state, or cycle requiring deferred
attribute import. Using an import helper would falsely advertise a soft
dependency and weaken failures.

### `utils/input_values.py`

Reviewed symbols:

- `iter_input_items`
- `input_field_value`
- `is_inactive_value`
- `SetInputTraversal`
- `ActiveField`
- `iter_active_fields`
- `LOGIC`, `RELATED`, and `LEAF`

These traverse generated filter/order input dataclasses. Query-log dictionaries
are not consumer inputs, and `None` in an exception or SQL record is not the
package's `UNSET`/inactive-input concept. Do not generalize these walkers into a
generic dictionary traversal for the payload.

### `utils/inputs.py`

Reviewed symbols:

- `GeneratedInputFieldSpec`
- `optional_field_kwargs`
- `optional_input_field`
- `emit_set_input_field_triples`
- `FieldConversionBase`
- `FieldConversionBase.__init__`
- `InputFieldSpec`
- `make_input_namespace`
- `make_shape_build_cache`
- `pascalize_token`
- `generated_input_type_name`
- `normalize_field_name_sequence`
- `resolve_effective_fields`
- `guard_dropped_required`
- `iter_provided_input_fields`
- `build_strawberry_input_class`
- `materialize_generated_input_class`
- `duplicate_name_message`
- `iter_input_field_collisions`
- `build_lazy_input_annotation`
- `iter_set_subclasses`
- `_safe_import`
- `clear_generated_input_namespace`
- `GeneratedInputArgumentsFactory`
- `GeneratedInputArgumentsFactory.__init_subclass__`
- `GeneratedInputArgumentsFactory.__init__`
- `GeneratedInputArgumentsFactory._collision_registry`
- `GeneratedInputArgumentsFactory.arguments`
- `GeneratedInputArgumentsFactory._ensure_built`
- `GeneratedInputArgumentsFactory._build_class_type`
- `GeneratedInputArgumentsFactory._build_input_triples`
- `SCALAR`, `RELATION_SINGLE`, `RELATION_MULTI`, and `FILE`

None applies. The debug payload is response metadata, not a generated
Strawberry input, and it must stay invisible to schema introspection. Do not
generate input/output dataclasses for it, materialize module globals, add a
shape cache, reuse decode-kind strings, or run collision/name machinery.

### `utils/permissions.py`

Reviewed symbols:

- `ChannelsRequestAdapter`
- `ChannelsRequestAdapter.__init__`
- `ChannelsRequestAdapter.scope`
- `ChannelsRequestAdapter.user`
- `ChannelsRequestAdapter.session`
- `ChannelsRequestAdapter.__getattr__`
- `_channels_request_adapter`
- `request_from_info`
- `extract_branch_value`
- `invoke_permission_method`
- `verbatim_path`
- `active_permission_targets`
- `active_related_branches`
- `active_permission_field_paths`
- `run_active_input_permission_checks`
- `_check_method_name`

The extension requires no request object and has no per-field permission hook.
Do not resolve `info.context`, wrap Channels requests, or add a permission
traversal. Developer-only safety is an enablement/documentation boundary in
v1, not a request authorization feature. Avoid touching context entirely; that
is both simpler and transport-neutral.

### `utils/querysets.py`

Reviewed symbols:

- `SyncMisuseError`
- `reject_async_in_sync_context`
- `model_for`
- `initial_queryset`
- `normalize_query_source`
- `sync_pipeline_recourse`
- `apply_type_visibility_sync`
- `visibility_scoped_related_queryset`
- `related_visibility_queryset`
- `related_visibility_queryset_or_default`
- `_stringified`
- `stringified_pks_present`
- `pks_all_present`
- `visible_related_object`
- `visible_related_objects`
- `apply_type_visibility_async`
- `post_process_queryset_result_sync`
- `post_process_queryset_result_async`

None applies to capture. The extension observes SQL after resolvers and
optimizers have made their queryset decisions; it must not normalize query
sources, apply visibility, inspect models, or bridge async hooks. A SQL log row
is not a `QuerySet`. Calling `normalize_query_source` or a visibility helper
would change behavior instead of observe it.

`reject_async_in_sync_context` is also not needed: `on_operation` is
deliberately a sync generator accepted by both engine colors, and it does not
call a consumer-overridable async hook.

### `utils/relations.py`

Reviewed symbols:

- `relation_kind`
- `is_many_side_relation_kind`
- `is_forward_many_to_many`
- `instance_accessor`
- `has_composite_pk`
- `RelationKind`
- `MANY_SIDE_RELATION_KINDS`
- `_RelationFieldLike`

None applies. SQL capture is backend/connection based and must not inspect
model relation shapes. The optimizer composition test should prove the
optimizer's behavior through emitted SQL, not duplicate relation
classification in the extension.

### `utils/strings.py`

Reviewed symbols:

- `snake_case`
- `pascal_case`
- `pascal_case_or_raise`
- `graphql_camel_name`
- `flatten_lookup_path`

Do not derive fixed response protocol keys through casing helpers. The exact
wire names `isSlow`, `isSelect`, and `excType` are compatibility contracts and
should be written once in their serializers. A casing algorithm could silently
change wire behavior if its acronym/underscore rules evolve.

No query classification helper exists here, and one should not be added:
`sql.lower().strip().startswith("select")` is a graphene-compatibility sniff,
not general string normalization.

### `utils/typing.py`

Reviewed symbols:

- `is_async_callable`
- `unwrap_graphql_type`
- `unwrap_container_type`
- `unwrap_return_type`

None applies. The extension does not inspect resolver callable color, GraphQL
return wrappers, Strawberry containers, or list annotations. Strawberry's
extension runner already recognizes the sync generator. Calling
`is_async_callable` would duplicate engine hook detection and would not solve
the async Django connection boundary.

### `utils/write_values.py`

Reviewed symbols:

- `unencodable_text_error`
- `raw_choice_value`
- `coerce_relation_pk_or_none`
- `type_check_relation_id`
- `decode_scalar_leaf`
- `decode_visible_relation`
- `decode_provided_fields`

None applies. Debug rows report already-executed behavior and must not validate,
coerce, unwrap, visibility-filter, or decode consumer input. In particular,
exception message stringification must not use the write scalar decoder: a raw
debug exception is not storable model input and must not become a
`FieldError`.

## DRY reuse outside `utils/`

### Reuse `DjangoOptimizerExtension` only as a structural example

Valid reuse:

- import `SchemaExtension` from Strawberry in the same direct style;
- follow the package's docstring quality;
- accept engine-owned lifecycle semantics;
- keep engine hooks small and delegate to private helpers; and
- test composition with the optimizer.

Deliberate non-reuse:

- the optimizer singleton factory;
- the plan cache;
- `_context` helpers;
- `ContextVar` state;
- `resolve`;
- root-field detection;
- type unwrapping;
- queryset normalization; and
- plan logging.

The lifecycle difference is fundamental, not an opportunity to build a common
base class. A package-specific `BaseDjangoSchemaExtension` would contain no
meaningful shared policy beyond Strawberry's existing base and should not be
introduced.

### Do not share implementation with `middleware/debug_toolbar.py`

The only shared concept is developer observability. The owning seams differ:

- toolbar: optional third-party Django middleware, HTTP request/response,
  toolbar panels/history, JSON body mutation;
- debug extension: hard-dependency Strawberry operation lifecycle,
  `ExecutionResult`, Django query log, response extensions merge.

Do not extract:

- a generic debug payload builder;
- JSON response helpers;
- content-type helpers;
- operation-name parsing;
- optional import guards;
- toolbar cache state;
- request tagging; or
- shared settings gates.

Sharing any of those would couple two features that the spec correctly defines
as independent and composable.

### Direct imports are the DRY hard-dependency posture

Use direct imports from:

- `contextlib`;
- `dataclasses` or `typing` if private records/types are useful;
- `threading`;
- `traceback`;
- `django.db`;
- `graphql`;
- `strawberry.extensions`.

Do not add wrapper functions around stable hard-dependency imports. One direct
import is already the least duplicated form.

## Test-code DRY obligations

### Reuse `django_strawberry_framework.testing.TestClient`

Every live request should use `TestClient.query`, not:

- `django.test.Client.post`;
- manual JSON envelope construction;
- manual response decoding;
- the old `graphql_client` helper; or
- direct `schema.execute_sync`.

Use the returned `Response` directly:

- `res.data`;
- `res.errors`;
- `res.extensions`;
- `res.response` only for raw HTTP assertions.

Expected-error cases should pass `assert_no_errors=False`. Mutation
authorization should use `with client.login(user):`, not paired manual
login/logout calls.

### Reuse the existing fakeshop schema-reload lifecycle

The new live module already receives the module-level and function-level
reload discipline from `examples/fakeshop/test_query/conftest.py`. Its schema
fixture should depend on
`_reload_project_schema_for_acceptance_tests`, import freshly reloaded app
types inside the fixture body, and let the autouse guard restore registry state.

Do not:

- call `registry.clear()` locally;
- write another module reload list;
- reload only `config.schema`;
- import app schema types at module import time; or
- duplicate the registration fingerprint.

### Reuse domain seed helpers

For products-backed live scenarios:

- call `seed_data(N)` as the first domain setup line;
- call `create_users(N)` for ordinary users;
- grant only the permission the mutation scenario needs; and
- query existing seeded rows instead of hand-building
  `Category`/`Item`/`Property`/`Entry` objects.

The debug tests should observe the application's real query behavior, not
construct a second miniature product fixture graph.

### Keep one probe schema holder in the new live module

Within `test_debug_extension_api.py`, use one module-level schema holder, one
view, and one `urlpatterns` list. A single fixture can replace the held schema
for scenarios that need:

- debug only;
- optimizer plus debug;
- no debug; or
- a custom raising/completion field.

Do not duplicate a holder/view/URL pattern per scenario.

The `test_multi_db.py` holder pattern is the behavioral precedent, but it is
not yet worth moving into a global shared helper automatically. Its module is
import-gated by `FAKESHOP_SHARDED`, while the debug module is always collected,
and URLconf modules must expose real module-level `urlpatterns`. Copying the
small declarative boundary once is safer than creating a stateful universal
probe registry.

If a third always-collected test module later needs the exact same mutable
schema URLconf, promote a narrowly named test helper/URLconf then. Do not
preemptively add production API for a test-only pattern.

### Single-site schema construction inside the test module

Use one local schema factory or fixture parameter seam that always supplies:

- `strawberry_config()`;
- the query type;
- the extension list; and
- the module holder assignment/cleanup.

Keep extension lists explicit at each behavior boundary so class-vs-instance
and masking order remain visible. The helper should not sort, normalize, or
deduplicate extensions because order is part of the contract.

### Single-site response access without hiding assertions

A tiny local helper may validate and return
`(res.extensions or {})["debug"]` for happy executed-operation cases used
repeatedly. Do not use it for validation-error/off-by-default cases, because
those tests must explicitly assert the key is absent.

Do not write a large assertion helper that checks every SQL-row field in every
test. Assert the full row contract once, then assert only scenario-specific
facts elsewhere. That keeps failures local and avoids copying the six-key
shape.

### Parameterize repeated mechanics

Use parameterization where the body is genuinely identical:

- prior `force_debug_cursor` value: `False` and `True`;
- masking order: mask-before-debug and debug-before-mask;
- shorter/reset log and bounded-rollover log shapes;
- SQL serializer select/non-select/executemany cases;
- exception collector validation/wrapped/nested/cyclic cases; and
- repeated `get_results` calls.

Do not combine live query, mutation, exception, and off-by-default scenarios
into one parameterized mega-test. Their setup and failure meanings differ.

### Test helpers directly; do not copy their logic into assertions

The package-tier tests should directly exercise the private:

- one-connection capture context;
- snapshot suffix helper;
- SQL serializer;
- terminal-error helper;
- exception serializer/collector; and
- payload/get-results behavior.

Assertions should use expected literals, not a second test-side
implementation. For example, do not compute expected `isSelect` by copying the
production sniff into the test; state the expected boolean for each canned SQL
string.

### Reuse real engine and Django objects where practical

Use:

- real `GraphQLError` wrappers for chain tests;
- real `MaskErrors` for teardown-order tests;
- real Strawberry execution for lifecycle/idempotence tests;
- real Django connection wrappers for saved-value restoration; and
- a real bounded `deque` shape for rollover behavior.

Mock only the behavior that cannot be produced safely through a real request,
notably a later-alias acquisition failure. Keep the fake at the private bracket
boundary rather than mocking Strawberry's whole runner.

### Single-site concurrency orchestration

The sync isolation test should have one small local coordination helper using a
barrier/events and one `ThreadPoolExecutor`. Both resolver variants should be
parameterized by distinguishable marker/message values rather than defined as
two copied resolver bodies.

The async overlap test should reuse the same conceptual markers but retain its
own async coordination primitives; forcing sync and async scheduling through a
generic abstraction would obscure the behavior being tested.

The exact floor check should run the same concurrency test in the isolated
`strawberry-graphql==0.316.0` environment. Do not copy the test into a script.
Select the existing test by node id so the normal and floor validations prove
one implementation.

## Avoid these premature abstractions

### Do not add a generic `ReferenceCountedFlag`

The coordinator's correct key, saved value, cleanup, lock scope, and failure
behavior are tied to Django connection wrappers and
`force_debug_cursor`. A generic callback-driven flag manager would have more
surface than its only consumer and make the critical restore rule harder to
audit.

Keep it private and concrete. Promote only when another production feature has
the same overlap semantics, not merely another `try/finally`.

### Do not add a generic response-extension base class

Strawberry's `SchemaExtension` plus `get_results` is already that abstraction.
A package base that stores a key/payload would save a few lines while hiding:

- the absent-before-teardown rule;
- the double-call idempotence requirement;
- the masking order;
- the operation hook; and
- the security posture.

Those are the feature, not boilerplate.

### Do not add debug row dataclasses to the public surface

Private `TypedDict`s may be used if they materially improve static readability,
but runtime dataclass instances would then need a second conversion pass before
JSON serialization. Plain dictionaries built once are simpler and already
match the response protocol.

Do not create Strawberry types: that would duplicate the rejected `_debug`
schema surface.

### Do not over-constantize protocol keys

One serializer dictionary for SQL rows, one serializer dictionary for
exception rows, and one payload builder are enough. Defining a constant for
every string key would scatter the wire shape across declarations and uses.

Use named constants only for values with independent semantics, such as the
10-second slow threshold and possibly the top-level `"debug"` key if it is
otherwise repeated in both production methods.

### Do not merge SQL and exception serializers

Both return dictionaries, but they have different inputs, keys, normalization,
ordering, and security properties. A generic `serialize_debug_row(kind, value)`
would be a branch-dispatch wrapper around two unrelated leaves and would make
tests less direct.

### Do not create a generic cycle walker

The terminal-error traversal follows exactly one typed edge:
`GraphQLError.original_error`, and it retains a terminal `GraphQLError`.
Generic graph traversal would obscure those semantics. Keep the identity-cycle
guard in the exception helper.

### Do not share the query snapshot with Relay window snapshots

The shared word “window” is accidental:

- Relay windows select model rows according to cursor arguments.
- Query-log snapshots mark a position in a bounded diagnostic deque.

They have different rollover, ordering, bounds, and error contracts. Sharing a
record or helper would be false DRY.

## Suggested additions to the spec's DRY checklist

The current D1-D3 and D-N1-D-N4 obligations are correct but incomplete. Add
the following implementation obligations, either to the spec or the Slice-1
handoff:

- **D4** — one private one-connection reference-counted capture context owns
  all active-map, lock, flag save/enable/restore, depth, and cleanup behavior.
- **D5** — `ExitStack` owns the every-alias acquire/unwind; one immutable
  operation snapshot retains each exact connection and starting log length.
- **D6** — one snapshot reader owns deque materialization, shortened-log
  clamping, and best-effort rollover semantics.
- **D7** — one SQL serializer owns float conversion, the slow threshold,
  select sniff, and the six fixed wire keys.
- **D8** — one cycle-safe terminal-original helper plus one exception
  serializer/collector owns the complete exception path.
- **D9** — one payload builder owns the two-list aggregate; `get_results` is a
  pure absent-or-stash read and never performs assembly.
- **D10** — the implementation imports no current package utility helper; the
  utility audit above is the deliberate non-reuse rationale.
- **D11** — live tests reuse `TestClient`, its `Response.extensions`,
  `TestClient.login`, the acceptance-suite schema reload fixtures, and
  `seed_data`/`create_users`.
- **D12** — mechanics tests directly test each private rule and parameterize
  repeated shapes; the floor environment runs the same concurrency test by
  node id rather than maintaining a copy.

## Implementation review checklist

Before Slice 1 is accepted, verify:

- no production import from `django_strawberry_framework.utils`;
- no new generic utility or base extension;
- no `resolve`, view, middleware, context, or response-body mutation path;
- no direct `CaptureQueriesContext` construction;
- no eager `ensure_connection`;
- no query recorder or cursor wrapper;
- one active-capture map and one lock;
- one connection-token context manager;
- one `ExitStack`;
- one snapshot suffix implementation;
- one SQL serializer;
- one terminal-error walk;
- one exception serializer/collector;
- one payload builder;
- one stash;
- pure, idempotent `get_results`;
- fresh lists/dicts per completed operation;
- direct hard-dependency imports;
- class-form schema opt-in;
- no optimizer `ContextVar` reuse;
- no toolbar helper reuse;
- live HTTP through `TestClient`;
- expected errors use `assert_no_errors=False`;
- login uses the client context manager;
- fakeshop types import inside the post-reload fixture;
- product data comes from seed helpers;
- masking tests use real `MaskErrors`;
- the floor run selects the same concurrency test;
- no duplicated expected-value algorithm in tests; and
- no helper promoted into `utils/` without a second production payer.