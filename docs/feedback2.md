# Spec-044 DRY review, round 3

## Verdict

This review covers the current
`docs/spec-044-debug_extension-0_0_14.md`, all thirteen modules under
`django_strawberry_framework/utils/`, the package's existing Strawberry
extension, the fakeshop schema/reload/probe-URLconf patterns, and the live
`TestClient` surface.

The new audit workflow was exercised directly:

- target: `django_strawberry_framework/utils`;
- scan roots: `django_strawberry_framework`, `tests`, `examples`, and
  `scripts`;
- context: `docs/spec-044-debug_extension-0_0_14.md`;
- forbidden inputs: `docs/feedback.md` and this review file;
- result: 13 target files, 136 definitions/constants, 343 parsed Python
  files, and zero parse/read failures.

Revision 4 and Revision 5 have successfully incorporated nearly all prior DRY
advice. The planned production module still should import **nothing** from
`django_strawberry_framework.utils`: no existing utility owns operation-level
database instrumentation or debug-wire serialization. Reusing an unrelated
utility would be false DRY.

Three corrections remain. The first changes a test's integration shape; the
other two close small single-source ambiguities before implementation.

## Findings

### F1 — P0: test optimizer composition through the canonical singleton factory

Test-plan scenario 2 currently says the probe schema carries
`DjangoOptimizerExtension` as a “fresh instance.” That conflicts with both
`django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension`
and `examples/fakeshop/config/schema.py`, which deliberately retain one
module-local optimizer and return it from a factory so the instance-bound plan
cache survives requests:

- construct `_optimizer = DjangoOptimizerExtension()` once;
- pass `lambda: _optimizer` in `extensions=`;
- place `DjangoDebugExtension` beside that factory as the class entry.

The composition test should use exactly that consumer shape. A fresh optimizer
per operation may still optimize correctly, but it discards the cross-request
cache and teaches a noncanonical integration in the test intended to prove the
two extensions compose.

This is also the cleanest division of lifecycle ownership:

- the optimizer factory deliberately returns one shared cached instance;
- the debug class deliberately produces one fresh uncached instance per
  operation.

Do not introduce a schema helper that normalizes both entries into one common
factory form. Their visible difference documents their intentionally different
lifetimes.

### F2 — P1: activate the probe URLconf once, not around every request

Decision 11 correctly chooses a module-level holder/view/`urlpatterns`
pattern, but the spec does not yet single-site activation of that URLconf.
Without an explicit pin, seven request-driving scenarios can each grow their
own `override_settings(ROOT_URLCONF=__name__)` and
`clear_url_caches()` enter/exit block, repeating the boilerplate already
visible in `examples/fakeshop/test_query/test_multi_db.py`.

Use one module-level `pytest.mark.urls(__name__)` application for
`test_debug_extension_api.py`. If the implementation cannot use that marker,
one fixture must own the equivalent settings override and URL-cache cleanup
for the whole test body. Do not put routing setup in each test and do not hide
it inside `TestClient`.

Keep the other responsibilities separate:

- one module-level schema holder/view/`urlpatterns`;
- one fixture that swaps the held schema and restores it;
- one module-level URLconf activation rule;
- ordinary `TestClient.query(...)` calls in tests.

The holder is still correctly local to the new test module. The audit found no
second always-collected production-quality probe abstraction worth promoting.

### F3 — P1: make the no-`__init__` stash sentinel concrete

Decision 7 and D6 require no `DjangoDebugExtension.__init__`, while scenario
11 requires `get_results()` on a fresh instance to return `{}`. The spec says
the absent sentinel is `None`, but does not say where that value exists before
the first operation teardown.

Pin one immutable class default for the instance-overridden stash, for example
an annotated `_payload = None`, and have `get_results()` read that attribute
directly. Successful teardown assigns the fresh payload dictionary on the
instance.

This preserves every existing decision:

- no constructor duplicated from `SchemaExtension`;
- no `getattr(self, "_payload", None)` fallback repeated at read sites;
- no separate “has payload” boolean;
- no mutable class-level payload;
- no eager empty dictionary that would incorrectly publish `debug` before
  execution;
- one absent sentinel and one completed payload attribute.

The supported class-form opt-in provides a fresh extension instance per
operation. There is no need to add machinery for a deprecated shared bare
instance.

## Confirmed production DRY shape

No additional production abstraction is justified. Keep the spec's current
shape:

1. Strawberry owns hook entry/exit, execution-context assignment, hook
   ordering, and response-extension merging through `SchemaExtension`,
   `on_operation`, and `get_results`.
2. Django owns SQL execution instrumentation through
   `force_debug_cursor`, `CursorDebugWrapper`, and `queries_log`.
3. `extensions/debug.py` owns one concrete reference-counted database-cursor
   coordinator, keyed by database connection object identity.
4. One `ExitStack` owns every acquired alias and all partial/exceptional
   unwind paths.
5. One immutable query-log snapshot retains the exact database connection and
   starting length.
6. One log-slice helper owns deque materialization and shortened-log clamping.
7. One SQL serializer owns the six fixed wire keys, float conversion,
   `_SLOW_QUERY_SECONDS`, and the graphene-compatible select sniff.
8. One cycle-safe `GraphQLError.original_error` walk and one exception
   serializer own terminal exception discovery and the exception triple.
9. One collector owns `result is None`, `errors is None`, ordering, and the
   no-dedup policy.
10. One payload builder owns the two-list aggregate.
11. `get_results` is a pure absent-or-stash read.

Do not extract any of these into a generic `ReferenceCountedFlag`, generic
cycle walker, debug-row dispatcher, package base extension, or public row
dataclass. There is still only one production payer.

## Audit evidence classification

### Existing package reuse

- `django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension`
  is a structural and integration precedent only. Reuse its documented schema
  wiring and generator-hook discipline, not its `ContextVar`s, resolver hook,
  cache, strictness configuration, or constructor.
- `django_strawberry_framework/testing/client.py::TestClient` owns request
  envelope construction, HTTP posting, decoding, `Response.extensions`,
  expected-error handling, and login lifecycle.
- `examples/fakeshop/schema_reload.py::reload_all_project_schemas` and the
  acceptance fixtures own registry/schema isolation.
- `examples/fakeshop/apps/products/services.py::seed_data` and
  `examples/fakeshop/apps/products/services.py::create_users` own domain
  setup.
- `examples/fakeshop/test_query/test_multi_db.py` is only a local
  probe-URLconf pattern. Copy the small holder boundary once; do not copy its
  hand-rolled HTTP or per-request URL override blocks.

### Exact-body duplicate candidates

The audit found no exact duplicate body that belongs in the planned debug
module.

- The 32 `_isolate_registry` copies are a warning not to add another one; the
  debug live tests already inherit the acceptance reload fixtures.
- Repeated generated-input helpers, permission test methods, image builders,
  GlobalID helpers, kanban import commands, and script Git wrappers belong to
  unrelated domains.
- The existing repeated fakeshop test setup is not a reason to make debug
  instrumentation depend on test infrastructure.

### Repeated literals

The high-frequency literals are primarily GraphQL selections, generated-input
names, model fields, and test identifiers. None belongs in
`extensions/debug.py`.

The planned protocol literals are deliberately local:

- `debug`, `sql`, and `exceptions` belong to the extension/payload boundary;
- `vendor`, `alias`, `sql`, `duration`, `isSlow`, and `isSelect` belong in the
  SQL serializer;
- `excType`, `message`, and `stack` belong in the exception serializer.

Tests should independently re-spell these wire keys. Importing expected values
from production would make protocol-renaming regressions self-fulfilling.

## Complete utility classification

Every inventoried target definition is classified below. “No reuse” means the
symbol was considered and rejected on semantic ownership, not overlooked.

### `django_strawberry_framework/utils/__init__.py`

No definitions. Its re-exports are relation, casing, and type-unwrapping
helpers. Do not export the debug extension or its private implementation here.

### `django_strawberry_framework/utils/connections.py`

No reuse:

- `CONNECTION_FILTER_KWARG`, `CONNECTION_ORDER_KWARG`,
  `CONNECTION_ORDER_KWARG_GRAPHQL`, `CONNECTION_SIDECAR_KWARGS`;
- `UnwindowableConnection`;
- `connection_sidecar_inputs_from_kwargs`,
  `has_connection_sidecar_input`, `has_connection_sidecar_kwargs`;
- `is_ambiguous_empty_window`;
- `WindowRangePlan`, `WindowRangePlan._probe_increment`,
  `WindowRangePlan.fetch_upper_bound`, `WindowRangePlan.fetch_limit`,
  `WindowRangePlan.wants_next_page_probe`, `window_range_plan`,
  `assert_window_fetch_mode`, `assert_window_fetch_mode_for`,
  `split_window_rows`;
- `ConnectionWindowBounds`, `derive_connection_window_bounds`,
  `_RELAY_MAX_RESULTS_DEFAULT`, `resolve_relay_max_results`,
  `derive_keyset_window_bounds`.

This module owns Relay connection pagination. It does not own
`django.db.connections`. Keep “query-log snapshot” vocabulary so the two
contracts do not converge by name.

### `django_strawberry_framework/utils/converters.py`

`convert_with_mro` is not reusable. Debug rows have two fixed serializers, not
a polymorphic converter registry.

### `django_strawberry_framework/utils/errors.py`

No reuse: `field_error`, `_str_list`, `relation_field_error`,
`validation_error_to_field_errors`, and `join_error_path` own the mutation
`FieldError` protocol. Raw debug exceptions are a different wire contract.

### `django_strawberry_framework/utils/imports.py`

No reuse: `import_attr_if_importable`, `loaded_attr`, `import_attr`, and
`require_optional_module` serve optional/deferred import boundaries. Django,
Strawberry, and graphql-core are hard dependencies and should be imported
directly.

### `django_strawberry_framework/utils/input_values.py`

No reuse: `LOGIC`, `RELATED`, `LEAF`, `iter_input_items`,
`input_field_value`, `is_inactive_value`, `SetInputTraversal`, `ActiveField`,
and `iter_active_fields` own generated-input traversal. Response metadata is
not consumer input.

### `django_strawberry_framework/utils/inputs.py`

No reuse:

- `GeneratedInputFieldSpec`, `optional_field_kwargs`,
  `optional_input_field`, `emit_set_input_field_triples`;
- `SCALAR`, `RELATION_SINGLE`, `RELATION_MULTI`, `FILE`,
  `FieldConversionBase`, `FieldConversionBase.__init__`, `InputFieldSpec`;
- `make_input_namespace`, `make_shape_build_cache`, `pascalize_token`,
  `generated_input_type_name`, `normalize_field_name_sequence`,
  `resolve_effective_fields`, `guard_dropped_required`,
  `iter_provided_input_fields`;
- `build_strawberry_input_class`, `materialize_generated_input_class`,
  `duplicate_name_message`, `iter_input_field_collisions`,
  `build_lazy_input_annotation`, `iter_set_subclasses`, `_safe_import`,
  `clear_generated_input_namespace`;
- `GeneratedInputArgumentsFactory`,
  `GeneratedInputArgumentsFactory.__init_subclass__`,
  `GeneratedInputArgumentsFactory.__init__`,
  `GeneratedInputArgumentsFactory._collision_registry`,
  `GeneratedInputArgumentsFactory.arguments`,
  `GeneratedInputArgumentsFactory._ensure_built`,
  `GeneratedInputArgumentsFactory._build_class_type`,
  `GeneratedInputArgumentsFactory._build_input_triples`.

The debug payload must remain plain response metadata, invisible to schema
input generation, naming ledgers, collision registries, and shape caches.

### `django_strawberry_framework/utils/permissions.py`

No reuse:

- `_check_method_name`;
- `ChannelsRequestAdapter`, `ChannelsRequestAdapter.__init__`,
  `ChannelsRequestAdapter.scope`, `ChannelsRequestAdapter.user`,
  `ChannelsRequestAdapter.session`, `ChannelsRequestAdapter.__getattr__`,
  `_channels_request_adapter`, `request_from_info`;
- `extract_branch_value`, `invoke_permission_method`, `verbatim_path`,
  `active_permission_targets`, `active_related_branches`,
  `active_permission_field_paths`, `run_active_input_permission_checks`.

The extension has no request authorization or input-permission traversal in
v1. Developer-only safety remains an explicit schema-enable/documentation
boundary.

### `django_strawberry_framework/utils/querysets.py`

No reuse:

- `SyncMisuseError`, `reject_async_in_sync_context`;
- `model_for`, `initial_queryset`, `normalize_query_source`;
- `_RELAY_ASYNC_RECOURSE`, `sync_pipeline_recourse`;
- `apply_type_visibility_sync`, `visibility_scoped_related_queryset`,
  `related_visibility_queryset`, `related_visibility_queryset_or_default`;
- `_stringified`, `stringified_pks_present`, `pks_all_present`;
- `visible_related_object`, `visible_related_objects`,
  `apply_type_visibility_async`, `post_process_queryset_result_sync`,
  `post_process_queryset_result_async`.

The extension observes executed SQL. It must not normalize query sources,
apply visibility, resolve models, or recolor resolver hooks.

### `django_strawberry_framework/utils/relations.py`

No reuse: `MANY_SIDE_RELATION_KINDS`, `_RelationFieldLike`, `relation_kind`,
`is_many_side_relation_kind`, `is_forward_many_to_many`,
`instance_accessor`, and `has_composite_pk` own model-relation shape. SQL
capture is database-connection based and model-agnostic.

### `django_strawberry_framework/utils/strings.py`

No reuse: `snake_case`, `pascal_case`, `pascal_case_or_raise`,
`graphql_camel_name`, and `flatten_lookup_path`.

In particular, do not derive `isSlow`, `isSelect`, or `excType` with
`graphql_camel_name`; they are fixed compatibility bytes. The select-prefix
sniff is graphene behavior and should remain inside the SQL serializer, not
be promoted as general string normalization.

### `django_strawberry_framework/utils/typing.py`

No callable reuse: `is_async_callable`, `unwrap_graphql_type`,
`unwrap_container_type`, and `unwrap_return_type` solve callable/type-wrapper
problems that the engine already handles for extension hooks.

`_MAX_TYPE_WRAPPER_DEPTH` is a posture precedent only: the
`original_error` walk must be bounded/cycle-safe. Do not generalize the two
different traversals into a shared attribute-chain walker.

### `django_strawberry_framework/utils/write_values.py`

No reuse: `unencodable_text_error`, `raw_choice_value`,
`coerce_relation_pk_or_none`, `type_check_relation_id`,
`decode_scalar_leaf`, `decode_visible_relation`, and
`decode_provided_fields` own write-input decoding and visibility. Debug rows
report behavior after execution and must not enter that pipeline.

## Required spec edits

Before Slice 1 implementation:

1. Change test-plan scenario 2 to the canonical module-local optimizer
   singleton returned by `lambda: _optimizer`, beside the debug class entry.
2. Add one module-level URLconf activation rule for all request-driving tests,
   preferably `pytest.mark.urls(__name__)`.
3. State that the no-constructor payload stash has one immutable class default
   of `None`, overridden on the instance only after payload assembly.

No new production utility, base class, mixin, shared test package, or
dependency is warranted.

## Implementation review gates

- No production import from `django_strawberry_framework.utils`.
- No direct `CaptureQueriesContext` construction.
- No custom cursor wrapper, SQL timer, parameter interpolator, or query
  recorder.
- One active-capture map, lock, and coordinator.
- Active state keyed by database connection object, not alias.
- One `ExitStack`, snapshot record, log-slice helper, SQL serializer,
  terminal-error walk, exception serializer/collector, payload builder, and
  stash.
- Pure and idempotent `get_results`.
- Fresh list/dict containers per completed operation.
- Class-form `DjangoDebugExtension` opt-in.
- Canonical singleton-factory `DjangoOptimizerExtension` composition.
- One module-level probe URLconf activation.
- Live HTTP through `TestClient`; no POST/decode copy.
- Expected errors use `assert_no_errors=False`.
- Login uses `TestClient.login`.
- Fakeshop types are imported inside the post-reload schema fixture.
- Product rows/users come from `seed_data` and `create_users`.
- No new registry-isolation helper.
- Real `GraphQLError`, `MaskErrors`, Strawberry execution, Django connection,
  and bounded-deque objects wherever practical.
- The exact Strawberry-floor run selects the same concurrency test by node
  id; it does not copy the test into a script.
- Tests independently spell protocol expectations rather than importing
  production constants or rebuilding expected rows with production helpers.