# DRY Follow-Up Review

## Executive Verdict

The last round of DRY work materially fixed the previous major targets. I do
not recommend reopening those items as-is:

- Query source normalization and visibility now have a shared home in
  `django_strawberry_framework/utils/querysets.py`.
- Connection window bounds and connection sidecar kwarg names now have a shared
  home in `django_strawberry_framework/utils/connections.py`.
- AST and converted-selection traversal now have a shared home in
  `django_strawberry_framework/optimizer/selections.py`.
- FilterSet/OrderSet related-target lifecycle now has shared machinery in
  `django_strawberry_framework/sets_mixins.py`.
- The connection `resolve_connection` head is now shared through
  `django_strawberry_framework/connection.py::_resolve_connection_fast_path`.

I found one remaining major production DRY opportunity. It is not copy-paste
duplication; it is a repeated runtime contract: walking a Strawberry input value
through dict/dataclass/list shapes, deciding which values are active, resolving
`FieldSpec` metadata, and recursing into related set inputs. Today that contract
is split across filter normalization, order normalization, permission walking,
and filter async visibility pre-walking.

Recommended priority:

1. Extract the set-input traversal substrate first.
2. Then consider the model-field selection profiles.
3. Treat example-project and command/test duplication as cleanup, not core
   package work.

## Major 1: Set-Input Runtime Traversal Is Still Split

Verdict: valid, major, high priority.

The package now shares generated input class creation, set lifecycle, and
permission dispatch, but the runtime walk over generated input values is still
implemented in several places with overlapping rules:

- `django_strawberry_framework/filters/sets.py::FilterSet._normalize_input`
- `django_strawberry_framework/orders/inputs.py::normalize_input_value`
- `django_strawberry_framework/utils/permissions.py::iter_input_items`
- `django_strawberry_framework/utils/permissions.py::active_permission_field_paths`
- `django_strawberry_framework/utils/permissions.py::active_related_branches`
- `django_strawberry_framework/filters/sets.py::FilterSet._operator_bag_items`
- `django_strawberry_framework/filters/sets.py::FilterSet._collect_nested_visibility_querysets_async`

The repeated mechanics are:

- Dict vs Strawberry input dataclass detection through `__dataclass_fields__`.
- Active-value rules, especially `None` vs `strawberry.UNSET`.
- Lookup of `_field_specs[(set_cls, python_attr)]`.
- Related-branch recognition through `related_filters` / `related_orders`.
- Recursive descent into child set inputs.
- Order-only top-level list traversal.
- Filter-only logical branch traversal.
- Filter-specific distinction between an operator-bag dict and a value dict
  such as a range input.

Why this matters:

This sits on correctness-sensitive surfaces. The same active-input decision
drives form data, permissions, related visibility, and ordering. If one path
treats `UNSET`, `None`, dict input, list input, or related branches differently,
the package can apply a filter without its permission gate, run a permission gate
without applying the corresponding filter/order, skip a related visibility hook,
or do extra work on inactive input. It also matters for optimizer efficiency
because related visibility pre-walks can duplicate traversal work before the
queryset is ever evaluated.

Best fix:

Add a neutral helper module, likely
`django_strawberry_framework/utils/input_values.py` or
`django_strawberry_framework/sets_values.py`, that owns the traversal mechanics
but not the filter/order leaf semantics.

Recommended shape:

- A small config object carrying `field_specs`, `related_attr`,
  `unset_sentinel`, `logic_keys`, and `handle_top_level_list`.
- A shared `iter_input_items(value)` moved out of `utils/permissions.py` or
  re-exported from the new helper.
- A shared `is_inactive_value(value, unset_sentinel=...)`.
- A shared iterator such as `iter_active_fields(set_cls, input_value, config)`
  yielding records with `python_attr`, `raw_value`, `FieldSpec | None`, and an
  active-kind marker such as `leaf`, `related`, or `logic`.
- Optional hook callbacks for family-specific leaves:
  `FilterSet` keeps operator-bag normalization and range patches local;
  `OrderSet` keeps `Ordering` direction handling local.
- Permission helpers should consume this traversal instead of doing a parallel
  active-field walk.
- Filter async nested-visibility pre-walk should consume the same logical and
  related branch iteration rules rather than partially re-deriving them.

Keep out of the shared helper:

- `django-filter` form-key construction.
- Filter operator-bag lookup mapping.
- Range-filter positional patching.
- Order `Ordering.resolve(...)`.
- The actual sync/async `apply_*` calls.

Tests to require:

- Filter input dataclass and raw dict forms produce identical normalized form
  data for the same active fields.
- Order input dataclass, raw dict, and top-level list forms produce identical
  flattened order tuples where applicable.
- Filter `UNSET` and `None` are both inactive; order `None` remains inactive
  without importing Strawberry into the order normalizer.
- Related branch permissions still fire once for parent and child sets.
- Filter operator-bag dicts are still distinguished from value dicts such as
  `{"start": ..., "end": ...}` for ranges.
- Async nested logical filter visibility still derives child querysets before
  the synchronous `.qs` path can encounter an async `get_queryset`.

## Additional Opportunities

### Model Field Selection Profiles

Verdict: valid, medium priority.

Several surfaces walk `model._meta.get_fields()` and derive related but not
identical selected-name sets:

- `django_strawberry_framework/types/base.py::_select_fields`
- `django_strawberry_framework/types/base.py::_selected_meta_targets`
- `django_strawberry_framework/types/base.py::_validate_optimizer_hints`
- `django_strawberry_framework/filters/sets.py::FilterSet.get_fields`
- `django_strawberry_framework/orders/sets.py::OrderSet._expand_meta_fields`
- `django_strawberry_framework/orders/inputs.py::_get_concrete_field_names_for_order`

These are not all the same rule. `DjangoType` selects concrete and relation
fields; filter `__all__` deliberately adds the pk and removes M2M fields; order
`__all__` selects column-backed local fields. That means a naive shared
`select_fields()` would be wrong.

The useful extraction is a profile-based model-field helper:

- `model_field_names(model)` for unknown-name checks.
- `select_djangotype_fields(model, fields_spec, exclude_spec)`.
- `filter_all_field_lookup_names(model)` or a narrower helper for the
  filter `__all__` adjustments.
- `orderable_concrete_field_names(model)`.
- `selected_name_map(selected_fields)` for Meta-target validators.

The value is consistency of typo guards and future set families, not fewer
lines. Keep each profile explicit so the different public contracts remain
visible.

### Example List Resolver Sidecar Pipeline

Verdict: valid, medium priority for example maintenance; not a package-core
refactor unless a future spec wants list sidecars.

The example project still hand-writes the same resolver skeleton many times:
start from an ordered queryset, apply `FilterSet.apply_sync(...)` when `filter`
is present, apply `OrderSet.apply_sync(...)` when `order_by` is present, and
return the queryset.

Evidence:

- `examples/fakeshop/apps/library/schema.py::Query.all_library_branches`
- `examples/fakeshop/apps/library/schema.py::Query.all_library_shelves`
- `examples/fakeshop/apps/library/schema.py::Query.all_library_books`
- `examples/fakeshop/apps/library/schema.py::Query.all_library_genres`
- `examples/fakeshop/apps/glossary/schema.py::Query.all_glossary_terms`
- `examples/fakeshop/apps/glossary/schema.py::Query.all_glossary_statuses`
- `examples/fakeshop/apps/glossary/schema.py::Query.all_glossary_documents`
- `examples/fakeshop/apps/scalars/schema.py::Query.all_scalar_specimens`
- `examples/fakeshop/apps/scalars/schema.py::Query.all_nullable_scalar_specimens`
- `examples/fakeshop/apps/scalars/schema.py::Query.all_scalar_specimen_tags`

Best fix:

For the example project, add an example-local helper that takes
`queryset`, `info`, `filter_input`, `order_by_input`, `filterset_class`, and
`orderset_class`, then applies the two sidecars in the canonical order. This
keeps the example readable without expanding the public package API.

Do not turn this into a public `DjangoListField` sidecar feature without a
focused spec. Connections already own the Meta-derived sidecar public surface;
list fields currently have a different, simpler contract.

### Finalizer Sidecar Error Formatting

Verdict: valid, low-medium priority.

The finalizer has family-specific formatter pairs that are structurally the
same but differ in nouns and remediation text:

- `django_strawberry_framework/types/finalizer.py::_format_orphan_filtersets_error`
- `django_strawberry_framework/types/finalizer.py::_format_orphan_ordersets_error`
- `django_strawberry_framework/types/finalizer.py::_format_owner_mismatch_error`
- `django_strawberry_framework/types/finalizer.py::_format_owner_ordersets_mismatch_error`
- `django_strawberry_framework/types/finalizer.py::_format_owner_model_mismatch_error`
- `django_strawberry_framework/types/finalizer.py::_format_owner_orderset_model_mismatch_error`

This is not a hot path and not a correctness issue today. If another set family
lands, move these into a sidecar error-message spec object used by the existing
`_SidecarBindingSpec`. Until then, leave them unless editing nearby code.

### Management Command Import And Dotted-Object Helpers

Verdict: valid, low priority.

The management commands have small repeated command-level patterns:

- `django_strawberry_framework/management/commands/export_schema.py::Command.handle`
- `django_strawberry_framework/management/commands/inspect_django_type.py::Command.handle`
- `django_strawberry_framework/management/commands/inspect_django_type.py::Command._resolve_type`

Both commands convert import failures into `CommandError`, and the inspect
command adds bare-name registry lookup on top. A tiny
`django_strawberry_framework/management/utils.py` helper could own
`import_schema_symbol(...)` and `resolve_dotted_object(...)`.

This is not major. The command code is small and user-facing error text is
already clear.

### Test And Example Boilerplate

Verdict: valid, low priority.

The broad duplicate scan still finds repeated registry-isolation fixtures,
project-schema reload helpers, and simple example helpers:

- `tests/*::_isolate_registry`
- `tests/*::_isolate_global_registry`
- `examples/fakeshop/test_query/*::_reload_project_schema_for_acceptance_tests`
- `examples/fakeshop/apps/kanban/management/commands/import_card_changed_files.py::Command._load`
- `examples/fakeshop/apps/kanban/management/commands/import_card_predicted_files.py::Command._load`
- `examples/fakeshop/apps/products/fields.py::*FieldSet.resolve_display_name`

Move only the test fixtures that truly share one contract. Do not force every
test into a global helper if local setup improves readability or avoids import
side effects. The Kanban command duplication is example-app code and can wait
for a Kanban service cleanup.

## Areas I Would Not Spend Time On

- Reopening query-source / visibility DRY. The current `utils/querysets.py`
  extraction is the right shape.
- Reopening connection window and sidecar kwarg DRY. The current
  `utils/connections.py` extraction is the right shape.
- Reopening selection traversal DRY. The current `optimizer/selections.py`
  adapter split is the right shape.
- Fully merging `FilterSet` and `OrderSet`. They now share the right
  foundations, and their leaf semantics are intentionally different.
- Hiding sync/async branches behind a generic maybe-await abstraction. The
  current explicit split is clearer and safer for Django ORM behavior.
- Treating example-only duplicate root fields as a package API problem without a
  spec. Use an example-local helper first if this cleanup is desired.
