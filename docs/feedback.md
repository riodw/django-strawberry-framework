# DRY deep-dive review

## Executive Verdict

I found more than three major production DRY opportunities. The strongest
ones are not in the already-fixed connection-window helpers; they are broader
framework patterns that now exist twice because filters and orders evolved as
parallel subsystems:

1. The generated input-class/factory/namespace lifecycle is duplicated across
   filters and orders.
2. The finalizer phase-2.5 binding flow is duplicated across FilterSet and
   OrderSet.
3. Active-input permission traversal is duplicated across FilterSet and
   OrderSet.
4. Public field/refetch factory scaffolding and async-callable detection are
   repeated across list, connection, node, and GlobalID strategy surfaces.

The earlier optimizer-specific DRY findings around connection window bounds,
connection sidecar kwarg names, and cache-relevant variable AST traversal appear
to have been addressed: `django_strawberry_framework/utils/connections.py` now
owns the window and sidecar contracts, and
`django_strawberry_framework/optimizer/extension.py::_walk_cache_relevant_vars`
now performs the combined directive plus nested-pagination variable traversal.
Do not spend time reworking those again unless a new behavior gap appears.

Recommended implementation order:

1. Extract the filter/order generated-input substrate first. It is foundational
   and will simplify factory, namespace-clear, and finalizer changes.
2. Extract the finalizer binding harness next, keeping filter-only checks as
   explicit hooks.
3. Extract shared active-input permission helpers after the binding and input
   shape is cleaner.
4. Then clean up field-factory scaffolding, registry clear helpers, and smaller
   repeated test/example code.

## Major 1: Generated Input Factories And Namespaces

Verdict: valid, major, high priority.

The filter and order generated-input layers repeat the same class-generation,
materialization, cache, and reset mechanics with only domain-specific leaf
conversion differences.

Evidence:

- `django_strawberry_framework/filters/inputs.py::FieldSpec`
- `django_strawberry_framework/orders/inputs.py::FieldSpec`
- `django_strawberry_framework/filters/inputs.py::build_input_class`
- `django_strawberry_framework/orders/inputs.py::build_input_class`
- `django_strawberry_framework/filters/inputs.py::_camel_case`
- `django_strawberry_framework/orders/inputs.py::_camel_case`
- `django_strawberry_framework/filters/inputs.py::materialize_input_class`
- `django_strawberry_framework/orders/inputs.py::materialize_input_class`
- `django_strawberry_framework/filters/inputs.py::_iter_filterset_subclasses`
- `django_strawberry_framework/orders/inputs.py::_iter_orderset_subclasses`
- `django_strawberry_framework/filters/inputs.py::clear_filter_input_namespace`
- `django_strawberry_framework/orders/inputs.py::clear_order_input_namespace`
- `django_strawberry_framework/filters/factories.py::FilterArgumentsFactory`
- `django_strawberry_framework/orders/factories.py::OrderArgumentsFactory`

Why this matters:

This is a lifecycle correctness surface, not cosmetic duplication. Both
subsystems build real module globals for Strawberry lazy references, keep
class-level factory caches, detect duplicate generated input names, and reset
stale owner/expanded state during `registry.clear()`. Any bug fix in one half
can easily be missed in the other. A future aggregate/search sidecar would
almost certainly copy the pattern a third time unless the shared substrate lands
first.

Best fix:

Introduce a cycle-safe private helper module, likely near the existing set
foundation, such as `django_strawberry_framework/sets_inputs.py` or
`django_strawberry_framework/utils/inputs.py`. It should own only the neutral
mechanics:

- A shared frozen field-spec value object, e.g. `GeneratedInputFieldSpec`.
- A shared Strawberry input-class builder, e.g. `build_strawberry_input_class`.
- A shared GraphQL camel-name helper.
- A shared materialization helper parameterized by module path, family label,
  and ledger.
- A shared subclass iterator.
- A shared namespace-clear helper that takes the root set class, factory cache
  attributes, field-spec ledger, materialization ledger, and per-subclass attrs
  to delete.
- A small BFS factory base/template that accepts hooks for root class,
  related-collection attr, related-target resolver, type-name resolver, and
  field-triple builder.

Do not move filter-specific conversion logic such as
`django_strawberry_framework/filters/inputs.py::convert_filter_to_input_annotation`
into the shared layer. Do not move order-specific flattening such as
`django_strawberry_framework/orders/inputs.py::normalize_input_value` into the
shared layer. The shared layer should own mechanics, not domain semantics.

Tests to require:

- Existing filter/order SDL tests should stay unchanged.
- Add one direct unit test proving filter and order input classes both use the
  same builder path for `name=` aliases and `description=`.
- Add one registry-clear test proving both generated namespaces rebuild cleanly
  after `registry.clear()`.
- Keep a collision test for each family so error wording still names FilterSet
  vs OrderSet even though the machinery is shared.

## Major 2: Finalizer Binding Harness

Verdict: valid, major, high priority.

The finalizer repeats the same ordered phase-2.5 sidecar binding harness for
FilterSet and OrderSet. The differences are real, but they are hooks around a
shared binding skeleton.

Evidence:

- `django_strawberry_framework/types/finalizer.py::_bind_filtersets`
- `django_strawberry_framework/types/finalizer.py::_bind_ordersets`
- `django_strawberry_framework/types/finalizer.py::_bind_filterset_owner`
- `django_strawberry_framework/types/finalizer.py::_bind_orderset_owner`
- `django_strawberry_framework/types/finalizer.py::_format_orphan_filtersets_error`
- `django_strawberry_framework/types/finalizer.py::_format_orphan_ordersets_error`
- `django_strawberry_framework/types/finalizer.py::_format_owner_model_mismatch_error`
- `django_strawberry_framework/types/finalizer.py::_format_owner_orderset_model_mismatch_error`
- `django_strawberry_framework/types/base.py::_validate_filterset_class`
- `django_strawberry_framework/types/base.py::_validate_orderset_class`

The repeated skeleton is:

- Walk definitions and collect wired classes.
- Bind owner before any expansion runs.
- Reject first-bind model mismatch.
- Treat same owner rebinding as idempotent.
- On second distinct owner, compare declared related targets.
- Expand lazy related declarations and rewrap expansion errors as
  `ConfigurationError`.
- Validate helper-referenced orphan sidecars.
- Build and materialize every generated input class.

Filter-only differences:

- FilterSet owner binding also checks the Relay own-PK GlobalID identity axis.
- FilterSet binding has the transitive unregistered `RelatedFilter` target audit
  because related filtering derives target visibility querysets.

Order-only differences:

- OrderSet does not need the own-PK Relay identity check because ordering by
  `id` is column ordering, not GraphQL GlobalID decoding.
- OrderSet does not need the unregistered target visibility audit in the same
  form because related ordering emits ORM paths rather than child queryset
  visibility derivation.

Best fix:

Keep this in `django_strawberry_framework/types/finalizer.py` or move only a
small private helper to a cycle-safe module. The finalizer is already the owner
of this lifecycle, so a local generic harness is acceptable.

Suggested shape:

- A small config object, e.g. `_SidecarBindingSpec`, with:
  `family_label`, `definition_attr`, `meta_attr_name`, `related_attr`,
  `helper_ledger`, `bind_owner`, `expand`, `factory_cls`, `materialize`,
  `format_orphans`, and optional `post_expand_audit`.
- A generic `_bind_sidecar_sets(spec)` implementing the ordered subpasses.
- A generic owner helper, e.g. `_bind_set_owner_common(...)`, that performs
  first-bind, idempotency, model compatibility, and related-target agreement.
- Filter passes a `before_second_owner_check` hook for the own-PK Relay axis.
- Filter passes a `post_expand_audit` hook for unregistered related targets.

This keeps the public error surface family-specific while single-siting the
ordering guarantees. The ordering is the load-bearing part; it should not remain
hand-copied.

Tests to require:

- Existing filter/order finalizer tests should stay behavior-identical.
- Add or keep tests for both single-orphan and multi-orphan error text.
- Add one paired test showing filter and order both recover cleanly after an
  expansion failure followed by a corrected re-run.
- Add one filter-only test proving the own-PK Relay mismatch still fires after
  the common owner binder extraction.

## Major 3: Active-Input Permission Traversal

Verdict: valid, major, high priority because this is an authorization surface.

FilterSet and OrderSet independently implement the same active-input permission
contract: resolve request from `info`, walk only supplied input fields, dedupe
`check_<field>_permission` calls by class, recurse into active related branches,
and fire both child gates and parent branch gates.

Evidence:

- `django_strawberry_framework/filters/sets.py::FilterSet._request_from_info`
- `django_strawberry_framework/orders/sets.py::OrderSet._request_from_info`
- `django_strawberry_framework/filters/sets.py::FilterSet._extract_branch_value`
- `django_strawberry_framework/orders/sets.py::OrderSet._extract_branch_value`
- `django_strawberry_framework/filters/sets.py::FilterSet._iter_active_related_branches`
- `django_strawberry_framework/orders/sets.py::OrderSet._iter_active_related_branches`
- `django_strawberry_framework/filters/sets.py::FilterSet._active_permission_field_paths`
- `django_strawberry_framework/orders/sets.py::OrderSet._active_permission_field_paths`
- `django_strawberry_framework/filters/sets.py::FilterSet._invoke_permission_method`
- `django_strawberry_framework/orders/sets.py::OrderSet._invoke_permission_method`
- `django_strawberry_framework/filters/sets.py::FilterSet._run_permission_checks`
- `django_strawberry_framework/orders/sets.py::OrderSet._run_permission_checks`

Why this matters:

A permission-gate divergence is a real security bug class. Today the two
implementations are similar enough that a fix to one side can be missed on the
other. The filter side has extra logical-branch recursion and `UNSET` handling;
the order side has top-level list handling. Those differences should be
configuration points, not reasons to duplicate the entire permission engine.

Best fix:

Extract neutral active-input helpers, likely in a private root module such as
`django_strawberry_framework/sets_permissions.py`.

Good extraction boundaries:

- `iter_input_items(input_value)`: dict-or-Strawberry-dataclass walker.
- `extract_branch_value(input_value, field_name, *, unset_sentinel=None)`.
- `invoke_permission_method(bare_instance, field_path, request, *, fired=None)`.
- `active_related_branches(cls, input_value, *, related_attr, related_target_attr, unset_sentinel)`.
- `active_permission_field_paths(...)`, parameterized by the field-spec map,
  related keys, logic keys, unset sentinel, and fallback source-path resolver.
- A shared `run_permission_checks(...)` that owns the `_fired` map, bare-instance
  allocation, child-recursion, and parent branch-gate dispatch, with a filter
  hook for logical `and` / `or` / `not` recursion.

Do not hide the filter side's logical-tree depth cap inside an order-shaped
abstraction. The common helper should accept a filter-specific logical recursion
hook or keep that tail in `FilterSet._run_permission_checks` while moving the
shared field/related dispatch underneath it.

Tests to require:

- A paired filter/order test proving a repeated field in multiple input arms
  fires its permission method once per class.
- A filter-only test proving logical branch recursion still gates nested fields.
- An order-only test proving list input still aggregates active fields across
  elements and dedupes.
- A related-branch test for both families proving parent branch gate and child
  field gate both fire.

## Major 4: Public Field Factory Scaffolding And Async Callable Detection

Verdict: valid, major but narrower than the first three.

The public field factories have intentionally different resolver semantics, but
they repeat several construction-time and callable-inspection utilities.

Evidence:

- `django_strawberry_framework/list_field.py::_is_async_callable`
- `django_strawberry_framework/types/base.py::_is_async_globalid_callable`
- `django_strawberry_framework/list_field.py::_validate_djangotype_target`
- `django_strawberry_framework/relay.py::_validate_node_target`
- `django_strawberry_framework/connection.py::DjangoConnectionField`
- `django_strawberry_framework/list_field.py::DjangoListField`
- `django_strawberry_framework/relay.py::DjangoNodeField`
- `django_strawberry_framework/relay.py::DjangoNodesField`

The async-callable functions both unwrap one `functools.partial` layer and then
check both the target and an async `__call__`. One is used for resolver
classification; one is used for GlobalID callable-strategy validation. The
domain error messages differ, but the predicate is the same.

The field factories also repeat:

- Pass-through `description`, `deprecation_reason`, and `directives` into
  `strawberry.field`.
- Shared DjangoType target validation plus family-specific Relay-shaped guards.
- Factory-name-specific error text around the same guard sequence.

Best fix:

- Move the async predicate to a neutral helper such as
  `django_strawberry_framework/utils/typing.py::is_async_callable`.
- Keep domain-specific error formatting at call sites.
- Extract a small Relay-shaped target guard, e.g.
  `_validate_relay_djangotype_target(target_type, *, field, remediation_tail)`,
  used by `DjangoConnectionField`, `DjangoNodeField`, and `DjangoNodesField`.
- Consider a tiny `_strawberry_field(resolver, *, description, deprecation_reason, directives)`
  wrapper only if it removes real duplication without hiding Strawberry's
  public API call.

Do not merge the resolver bodies of `DjangoListField`, `DjangoConnectionField`,
and the node fields. Their sync/async contracts are intentionally different:
list default dispatches per call, connection commits sync/async at construction,
and node refetch has decode/batch semantics. The DRY target is scaffolding, not
resolver behavior.

Tests to require:

- Keep the existing async callable object and partial-wrapped callable tests.
- Add one shared-predicate test in `tests/utils/` and shrink the domain tests to
  prove the error surfaces still name their domain.

## Additional Opportunities

### Registry Clear Optional-Callback Pattern

Verdict: valid, medium priority.

`django_strawberry_framework/registry.py::TypeRegistry.clear` repeats the same
best-effort local-import pattern for filter input namespace, filter helper
ledger, order input namespace, order helper ledger, connection cache, and root
node-field ledger.

Best fix:

Add a private helper such as `_clear_if_importable(module_path, attr_name,
action)` or a table-driven loop of clear callbacks. Keep the lazy/cycle-safe
import behavior and keep each clear independent: one missing subsystem must not
skip later cleanup. This is a maintainability win now and a stronger win before
aggregate/search ledgers add more blocks.

### Stage-2 Meta Target Validation

Verdict: valid, medium priority.

`django_strawberry_framework/types/base.py::_validate_nullability_override_targets`
and `django_strawberry_framework/types/base.py::_validate_relation_shape_targets`
share the same first half:

- Build all model field names.
- Reject unknown names through `_format_unknown_fields_error`.
- Build selected fields by name.
- Reject fields excluded by `Meta.fields` / `Meta.exclude`.
- Iterate sorted known selected targets for domain-specific checks.

Best fix:

Extract a helper such as `_selected_meta_targets(model, selected_fields, attr,
targets)` returning `selected_by_name` and sorted target names after the
unknown/excluded guards. Keep the consumer-authored, scalar-only, Relay-pk, and
many-side relation checks in their domain validators.

This will also help future `Meta.*` features avoid copying the same unknown vs
excluded distinction.

### Filter And Order Helper Annotation Functions

Verdict: valid, medium priority.

`django_strawberry_framework/filters/__init__.py::filter_input_type` and
`django_strawberry_framework/orders/__init__.py::order_input_type` repeat the
same helper-reference ledger update and `Annotated[name, strawberry.lazy(...)]`
construction with only family-specific validation and docs.

Best fix:

After the generated-input substrate is extracted, add a small helper:
`build_lazy_input_annotation(set_class, *, expected_base, family_name, ledger,
input_type_name_for, module_path)`. Keep the public functions as the only
consumer-facing entry points and preserve their TypeError wording.

### Exact Duplicate Filter Method Classes

Verdict: valid, low priority.

`django_strawberry_framework/filters/base.py::ArrayFilterMethod.__call__` and
`django_strawberry_framework/filters/base.py::ListFilterMethod.__call__` are
exact duplicates. A shared base class or single `_ListLikeFilterMethod` would
remove the copy.

This is not a major item because the duplicated body is tiny and purely local.
It should not be prioritized ahead of the lifecycle/permission abstractions.

### Test Registry-Isolation Fixtures

Verdict: valid, test-only, low priority.

The exact-copy scan found the same `_isolate_registry` fixture in many package
test modules, including:

- `tests/types/test_definition_order.py::_isolate_registry`
- `tests/types/test_definition_order_schema.py::_isolate_registry`
- `tests/types/test_relay_interfaces.py::_isolate_registry`
- `tests/types/test_generic_foreign_key.py::_isolate_registry`
- `tests/types/test_base.py::_isolate_registry`
- `tests/types/test_resolvers.py::_isolate_registry`
- `tests/optimizer/test_extension.py::_isolate_registry`
- `tests/optimizer/test_definition_order.py::_isolate_registry`
- `tests/optimizer/test_relay_id_projection.py::_isolate_registry`
- `tests/optimizer/test_field_meta.py::_isolate_registry`
- `tests/management/test_inspect_django_type.py::_isolate_registry`
- `tests/testing/test_relay.py::_isolate_registry`

Best fix:

Prefer a shared fixture only if it preserves the tests' explicit isolation
boundaries. A root `tests/conftest.py` autouse fixture would affect every test
and may hide state-lifecycle bugs, so the safer option is a named fixture/helper
imported where needed or a narrowly scoped package-level conftest.

### Example Kanban Import Commands

Verdict: valid, example-only, low priority.

`examples/fakeshop/apps/kanban/management/commands/import_card_changed_files.py`
and
`examples/fakeshop/apps/kanban/management/commands/import_card_predicted_files.py`
duplicate command loading and card identifier logic.

Best fix:

Extract a small example-app helper in `examples/fakeshop/apps/kanban/management/`
or `examples/fakeshop/apps/kanban/services.py` if both commands remain active.
This is not package-critical and should stay behind production framework DRY
work.

### Example Product FieldSet Display Resolvers

Verdict: valid, example-only, low priority.

`examples/fakeshop/apps/products/fields.py` has three identical
`resolve_display_name` methods across example fieldsets.

Best fix:

Use a small shared mixin or helper only if those example fieldsets continue to
grow. Do not prioritize this over package internals.

## Areas I Would Not DRY Further Right Now

- Do not rework `django_strawberry_framework/utils/connections.py`; it already
  centralizes connection window bounds and sidecar kwarg names.
- Do not re-split the cache variable traversal in
  `django_strawberry_framework/optimizer/extension.py`; the unified traversal
  is the desired shape.
- Do not force one generic sync/async connection pipeline abstraction in
  `django_strawberry_framework/connection.py`. The current shared
  `_prepare_pipeline_source` and `_finalize_queryset` helpers capture the
  color-agnostic pieces while keeping sync and async hook calls readable.
- Do not collapse `FilterSet` and `OrderSet` into one base class wholesale.
  They share lifecycle and permission substrate, but their leaf semantics are
  legitimately different.
- Do not turn test-only duplicates into a global autouse fixture without first
  auditing which tests intentionally exercise stale registry state.

## Bottom Line

The highest-value DRY work is to formalize the package's emerging "set family"
substrate. Filters and orders already share naming, lazy input materialization,
owner binding, orphan validation, and permission traversal. Those are
framework-level contracts and should be single-sited before another sidecar
family is added.
