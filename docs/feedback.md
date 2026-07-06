# DRY Review: `django_strawberry_framework/utils`

Review target: every existing method/class in `django_strawberry_framework/utils/`,
plus the in-package call sites that consume those helpers.

Verdict: the utility layer is already doing a lot of the right work. The strongest
DRY wins are `utils/input_values.py`, `utils/permissions.py`,
`utils/querysets.py`, `utils/inputs.py`, `utils/connections.py`, and
`utils/converters.py`: they single-site several contracts that would otherwise be
security bugs if duplicated. The next implementation should not create a larger
"generic everything" abstraction. It should add a few narrow utility owners and then
force all new code through them.

The highest-impact DRY rule is this: every future feature should first ask whether
it is re-spelling request resolution, generated-input lifecycle, active-input
traversal, relation visibility, relation-id coercion, field-error construction,
case conversion, or optional-dependency import handling. If yes, add or extend the
single utility owner instead of adding a local helper beside the feature.

## Current DRY Wins To Preserve

- `django_strawberry_framework/utils/input_values.py::iter_active_fields` is the
  correct owner for dict-vs-dataclass walking, `None` / `UNSET` inactive checks,
  and leaf / related / logic classification.
- `django_strawberry_framework/utils/permissions.py::active_permission_targets`
  correctly fuses leaf-gate paths and related branches into one traversal.
- `django_strawberry_framework/utils/querysets.py::apply_type_visibility_sync` and
  `django_strawberry_framework/utils/querysets.py::apply_type_visibility_async`
  correctly single-site the `DjangoType.get_queryset` visibility hook.
- `django_strawberry_framework/utils/querysets.py::reject_async_in_sync_context`
  is the right shared guard for sync seams that might receive an async hook result.
- `django_strawberry_framework/utils/inputs.py::make_input_namespace`,
  `django_strawberry_framework/utils/inputs.py::make_shape_build_cache`, and
  `django_strawberry_framework/utils/inputs.py::clear_generated_input_namespace`
  are the right lifecycle primitives for generated input classes and registries.
- `django_strawberry_framework/utils/inputs.py::resolve_effective_fields`,
  `django_strawberry_framework/utils/inputs.py::normalize_field_name_sequence`, and
  `django_strawberry_framework/utils/inputs.py::guard_dropped_required` are the
  correct shared `Meta.fields` / `Meta.exclude` validation spine.
- `django_strawberry_framework/utils/converters.py::convert_with_mro` is the right
  skeleton for ordered prechecks plus MRO scalar dispatch plus fail-loud fallthrough.
- `django_strawberry_framework/utils/connections.py::derive_connection_window_bounds`
  and the sidecar helpers are the correct single source for plan-time and
  resolve-time connection-window agreement.
- `django_strawberry_framework/utils/relations.py::relation_kind`,
  `django_strawberry_framework/utils/relations.py::is_forward_many_to_many`, and
  `django_strawberry_framework/utils/relations.py::instance_accessor` are the right
  relation-shape owners.
- `django_strawberry_framework/utils/typing.py::is_async_callable`,
  `django_strawberry_framework/utils/typing.py::unwrap_graphql_type`, and
  `django_strawberry_framework/utils/typing.py::unwrap_return_type` should be the
  only new-code entry points for those inspections.

## P1 DRY Actions

### P1.1 - Keep request/context resolution in one helper

All request-bearing surfaces should continue to call
`django_strawberry_framework/utils/permissions.py::request_from_info`, and any new
request shape should be supported there only.

Current consumers already route through this helper:

- `django_strawberry_framework/auth/queries.py`
- `django_strawberry_framework/auth/mutations.py`
- `django_strawberry_framework/mutations/permissions.py`
- `django_strawberry_framework/filters/sets.py`
- `django_strawberry_framework/orders/sets.py`
- `django_strawberry_framework/rest_framework/resolvers.py`

Spec 041 makes this urgent. Channels/ASGI integration must not add local request
decoders in routers, auth queries, auth mutations, serializer mutation kwargs, or
permission gates. If Strawberry Channels provides `info.context` as a dict or a
Channels request wrapper, adapt that shape once in `request_from_info()`.

Recommended shape:

- keep accepting `info.context.request`;
- keep accepting a bare `django.http.HttpRequest`;
- add a dict-context branch if Strawberry Channels exposes `{"request": ...}`;
- add a Channels-scope branch only if it can return a stable request-like object
  with `.user` and session behavior, or make auth mutations branch through a
  dedicated shared helper that still lives beside `request_from_info()`;
- keep the `family_label` parameter so all surfaces retain good error messages.

Do not implement Channels request fixes in `auth/queries.py`, `auth/mutations.py`,
or `rest_framework/resolvers.py` separately. That would guarantee drift.

### P1.2 - Move cross-flavor write error/value helpers out of `mutations/resolvers.py`

Several helpers in `django_strawberry_framework/mutations/resolvers.py` are already
cross-flavor utilities, because the form and serializer resolvers import them:

- `field_error`
- `relation_field_error`
- `validation_error_to_field_errors`
- `save_or_field_errors`
- `raw_choice_value`
- `_unencodable_text_error`
- `type_check_relation_id`

That works today, but it is the wrong ownership boundary for future DRY. The model
mutation resolver should not be the utility module for form, serializer, auth, and
future write flavors.

Recommended refactor:

- create a neutral utility module such as `django_strawberry_framework/utils/errors.py`
  or `django_strawberry_framework/utils/write_errors.py`;
- move `field_error`, `relation_field_error`, and
  `validation_error_to_field_errors` there;
- create `django_strawberry_framework/utils/write_values.py` only if needed for
  `raw_choice_value`, text storability checks, and relation-id structural checks;
- leave compatibility aliases in `mutations/resolvers.py` if tests or consumers
  import the old private names;
- have model, form, serializer, and auth code import from the neutral utility.

This is the cleanest way to keep FieldError leaf shape, message coercion, structured
`path`, `codes`, relation-error wording, enum unwrapping, and invalid-Unicode
preflight single-sited.

### P1.3 - Single-site GraphQL error path joining and re-keying

`django_strawberry_framework/rest_framework/resolvers.py::_join_path`,
`_rekey_segment`, `_build_reverse_map`, and
`serializer_errors_to_field_errors` currently own nested DRF error flattening. That
is fine while only DRF has nested write errors, but the path mechanics are not
DRF-specific:

- dotted path joining;
- root `__all__` vs nested `.__all__`;
- GraphQL-name re-keying by reverse map;
- structured `FieldError.path` derivation.

Recommended DRY boundary:

- keep DRF-specific `ErrorDetail.code` extraction in the DRF resolver or a DRF-named
  helper;
- move generic path construction to the same neutral error utility as `field_error`;
- define a small reverse-map record shape if another write flavor needs nested
  errors;
- make all nested write error mappers call the same path joiner.

This avoids having the serializer path become the template that future nested form
or custom mutation features copy by hand.

### P1.4 - Move raw relation primitives to relation/queryset utilities before adding another write flavor

The model, form, and serializer paths now share pieces of relation-id work, but the
shared pieces are split between `mutations/resolvers.py` and `utils/querysets.py`.
Before a fourth write flavor lands, promote the neutral primitives:

- `_coerce_relation_pk_or_none` belongs in a utility module, because raw-pk
  coercion is not model-mutation-specific.
- `_relation_membership_error` is FieldError-shaped, so either it moves with the
  FieldError utilities or becomes a lower-level boolean helper over
  `utils/querysets.py::stringified_pks_present` and
  `utils/querysets.py::pks_all_present`.
- `_is_forward_concrete_relation` and `_relation_field_index` are relation-shape
  helpers. They should move to `utils/relations.py` if another generator/decoder
  needs the same FK/M2M indexing rule.

Do not move `_decode_relation_id_set` wholesale unless another flavor truly needs
the model path's exact semantics. Its raw-pk FK/M2M behavior is model-mutation
specific. Move the smaller primitives first.

### P1.5 - Centralize optional import and optional dependency error handling

There are currently three related import-clear patterns:

- `django_strawberry_framework/registry.py::_clear_if_importable`
- `django_strawberry_framework/registry.py::_clear_if_loaded`
- `django_strawberry_framework/utils/inputs.py::_safe_import`

Spec 041 will likely add optional Channels import handling too. Do not add a fourth
pattern in `routers.py`.

Recommended utility owner:

- add `django_strawberry_framework/utils/imports.py`;
- provide `import_attr_if_importable(module_path, attr_name)`;
- provide `loaded_attr(module_path, attr_name)`;
- provide `require_optional_module(module_name, *, install_hint, feature_label)`;
- if version checks are needed, add `require_optional_distribution()` or keep the
  version gate beside the router but still use the common error message builder.

Then update registry, generated-input namespace clearing, and router optional
dependency checks to use the same primitives.

This keeps "missing optional dependency", "submodule partially unavailable", and
"skip if not loaded" behavior from drifting.

### P1.6 - Add one helper for FilterSet logical branch iteration

`django_strawberry_framework/filters/sets.py` repeats the logical branch walk in at
least three places:

- `_collect_nested_visibility_querysets_async`
- `_run_permission_checks`
- `_evaluate_logic_tree`

The loops are not identical because their tails differ, but the extraction of
`and`, `or`, and `not` children is repeated. That is exactly the kind of small
logic drift that becomes a permission bug.

Recommended helper:

- add a filter-local helper first, not necessarily a generic package utility:
  `iter_logic_branch_inputs(input_value, *, include_wire_keys, unset_sentinel)`;
- if order/aggregate/future set families gain logical operators, move that helper
  to `utils/input_values.py`;
- make it return typed records such as `LogicBranch(kind="and", child=...)`, or
  separate iterators for `and`, `or`, `not` if the Q-building code stays clearer.

Do not hide the Q semantics inside a generic helper. Only single-site child
extraction and depth-guard invocation.

### P1.7 - Do not create new thin class wrappers unless preserving compatibility

`FilterSet` and `OrderSet` still carry private wrapper methods such as
`_request_from_info`, `_extract_branch_value`, `_active_permission_targets`, and
`_invoke_permission_method`. They are thin delegates to the utility layer.

That is acceptable for backward-compatible private API stability and for tests that
address those methods directly. It should not become the pattern for new code.

Future code should call the utility directly unless there is a real compatibility
reason to keep a class-shaped delegate. Otherwise the repo will have two names for
every concept and reviewers will have to inspect both to prove they are identical.

## P2 DRY Actions

### P2.1 - Move `graphql_camel_name` to `utils/strings.py`

`django_strawberry_framework/utils/inputs.py::graphql_camel_name` is used outside
generated-input code:

- mutation relation decode fallback names;
- form input generation;
- serializer input generation;
- serializer converter input-name derivation;
- order input generation.

It is now a general string-boundary helper, not an input-only helper. Move it to
`django_strawberry_framework/utils/strings.py` beside `snake_case` and
`pascal_case`, and leave an import alias in `utils/inputs.py` if needed for
compatibility.

Do not inline `name.split("_")` camelization anywhere else.

### P2.2 - Add a checked Pascal helper instead of repeating no-token guards

There are two related no-token guards today:

- `django_strawberry_framework/sets_mixins.py::ClassBasedTypeNameMixin.type_name_for`
- `django_strawberry_framework/filters/inputs.py::_pascal_case`

Both wrap `django_strawberry_framework/utils/strings.py::pascal_case` and raise when
the result is empty. Keep their error messages consumer-specific, but single-site
the no-token check.

Recommended helper:

```python
def checked_pascal_case(name: str, *, make_error: Callable[[str], Exception]) -> str:
    pascal = pascal_case(name)
    if not pascal:
        raise make_error(name)
    return pascal
```

or, if that feels too abstract, add `pascal_case_or_raise(name, *, message: str)`.

Do not merge `pascal_case` and `pascalize_token`. They have intentionally different
collision properties.

### P2.3 - Keep generated-input lifecycle on `make_input_namespace`

Any future generated input family, including auth or Channels-adjacent helpers if
they ever generate Strawberry inputs, should use:

- `django_strawberry_framework/utils/inputs.py::make_input_namespace`
- `django_strawberry_framework/utils/inputs.py::materialize_generated_input_class`
- `django_strawberry_framework/utils/inputs.py::make_shape_build_cache`

Do not hand-roll `_materialized_names`, `_materialize_input`, or
`clear_*_input_namespace` again. The mutation, form, serializer, auth-query, filter,
and order code already prove the shared lifecycle is the right abstraction.

### P2.4 - Keep field-set validation on `resolve_effective_fields`

Every new `Meta.fields` / `Meta.exclude` consumer should use:

- `normalize_field_name_sequence`
- `resolve_effective_fields`
- `guard_dropped_required`

No new code should re-spell:

- reject bare strings;
- reject duplicate names;
- reject simultaneous `fields` and `exclude`;
- compute unknown names;
- raise empty-effective-set errors.

If a new surface needs a different unknown-name noun or subject label, pass it in.
Do not fork the validation body.

### P2.5 - Keep converter dispatch on `convert_with_mro`, but replace `None` fallthrough if it grows

`convert_with_mro()` currently treats a precheck result of `None` as "continue to
the MRO walk". That is fine for the current form converter's exact `forms.Field`
special case, but it is an implicit sentinel.

If a future converter has a valid conversion whose value can be `None`, add an
explicit sentinel such as `CONTINUE_CONVERSION` and update the two current callers.

Until then, every new field converter should use `convert_with_mro()` rather than
copying ordered prechecks and an MRO loop.

### P2.6 - Keep relation cardinality checks in `utils/relations.py`

New code should never inspect Django relation flags directly when one of the
existing helpers answers the question:

- `relation_kind()`
- `is_many_side_relation_kind()`
- `is_forward_many_to_many()`
- `instance_accessor()`
- `has_composite_pk()`

If a new repeated predicate appears, add it here. Likely candidates are:

- `is_forward_concrete_relation(field)`;
- `relation_input_attr(field)` for the `<field>_id` naming rule;
- `relation_field_index(model)` if another write decoder needs the same FK/M2M map.

### P2.7 - Keep relation visibility on `utils/querysets.py`

New relation reads/writes should compose these helpers:

- `related_visibility_queryset()`
- `visibility_scoped_related_queryset()`
- `visible_related_object()`
- `visible_related_objects()`
- `stringified_pks_present()`
- `pks_all_present()`

Do not add local `registry.get(...) -> initial_queryset(...) -> get_queryset(...)`
chains in form, serializer, auth, or router code. That chain is a data-visibility
contract and must stay single-sited.

If a caller needs `registry.primary_for(...)` rather than `registry.get(...)`, add a
new utility with a name that says so. Do not hide a primary-only behavior change
inside `related_visibility_queryset()`.

### P2.8 - Use `sync_pipeline_recourse` for every sync write flavor

`django_strawberry_framework/utils/querysets.py::sync_pipeline_recourse` already
single-sites the async-`get_queryset` recourse sentence for model, form, and
serializer mutation pipelines.

Any future sync write flavor should compute its recourse through that helper. Do
not introduce a new `_X_ASYNC_RECOURSE` string by copy/paste.

### P2.9 - Consider a sidecar dataclass before adding a third connection sidecar

`connection_sidecar_inputs_from_kwargs()` currently returns `(filter_input,
order_by_input)`. That tuple is simple and correct for two sidecars.

If a third sidecar lands, such as `search`, switch to a frozen dataclass before the
new call sites spread:

```python
@dataclass(frozen=True)
class ConnectionSidecarInputs:
    filter_input: Any
    order_by_input: Any
    search_input: Any = None
```

Then `has_connection_sidecar_input()` can accept the dataclass and the arity no
longer becomes a package-wide edit.

### P2.10 - Use type-unwrapping utilities everywhere

No new code should open-code:

- `while hasattr(type_, "of_type")`;
- `get_origin(x) is list` plus `get_args(x)`;
- `inspect.iscoroutinefunction(...)` plus partial/callable-instance checks.

Use `unwrap_graphql_type`, `unwrap_return_type`, and `is_async_callable`. If a new
wrapper shape appears, extend those helpers once.

### P2.11 - Keep `iter_provided_input_fields` as the only UNSET-stripping write walk

Model, form, and serializer decoders all correctly call
`django_strawberry_framework/utils/inputs.py::iter_provided_input_fields`.

Future write decoders must do the same. Do not iterate
`data.__strawberry_definition__.fields` locally, and do not check
`strawberry.UNSET` in a new loop.

If a future decoder needs field metadata not currently yielded, extend the tuple or
introduce a small record object rather than adding another loop.

### P2.12 - Keep active-input `None` / `UNSET` semantics single-sited

New filter/order/permission code should use:

- `is_inactive_value()`
- `extract_branch_value()`
- `iter_active_fields()`

Do not write new checks like `if value is None or value is UNSET` outside the helper
unless the semantics are intentionally different and documented at the call site.

### P2.13 - Split `utils/inputs.py` only when a new feature makes it harder to review

`django_strawberry_framework/utils/inputs.py` is now broad. It owns:

- generated input metadata records;
- namespace materialization;
- shape caches;
- case-name helpers;
- field-set validation;
- Strawberry input class construction;
- lazy annotations;
- clear lifecycle;
- generated arguments BFS factory.

This is still coherent because all of it serves generated inputs. Do not split it
just for aesthetics. But if another generated-input family lands and this file grows
again, split by responsibility:

- `utils/input_names.py` for `graphql_camel_name`, `pascalize_token`,
  `generated_input_type_name`;
- `utils/input_lifecycle.py` for namespace/materialization/clear helpers;
- `utils/input_fields.py` for field-set validation and class construction.

Keep import aliases to avoid churn.

## P3 Cleanup And Documentation DRY

### P3.1 - Remove durable references to `docs/feedback.md` from code comments over time

Many utility docstrings mention `docs/feedback.md` findings, for example "the 0.0.9
DRY pass, `docs/feedback.md` Major 1". This file is a live feedback scratchpad and
has already been overwritten for later reviews. It is not a durable source of truth.

As files are touched, replace those references with:

- the relevant spec id;
- the owning helper name;
- or no historical reference at all if the code now explains itself.

This is documentation DRY: source comments should point to stable contracts, not to
a reused review document.

### P3.2 - Prefer primary-owner references over compatibility re-export references

`utils/permissions.py` re-exports `iter_input_items` for compatibility, but the real
owner is `utils/input_values.py`.

Future comments and docs should refer to:

- `django_strawberry_framework/utils/input_values.py::iter_input_items`
- `django_strawberry_framework/utils/input_values.py::iter_active_fields`

not the compatibility import path. Re-export paths are useful for old imports, but
they should not become the documented owner.

### P3.3 - Keep `utils/__init__.py` conservative

`django_strawberry_framework/utils/__init__.py` currently re-exports only a small
set of older utility helpers. Do not dump every utility into the package-level
`utils` namespace. That makes imports shorter but ownership fuzzier.

Prefer explicit submodule imports:

- `from django_strawberry_framework.utils.querysets import ...`
- `from django_strawberry_framework.utils.inputs import ...`
- `from django_strawberry_framework.utils.permissions import ...`

Add re-exports only for stable, broadly used helpers.

### P3.4 - Keep intentional sync/async duplication

Do not over-DRY these pairs into a maybe-await abstraction:

- `apply_type_visibility_sync` / `apply_type_visibility_async`
- `post_process_queryset_result_sync` / `post_process_queryset_result_async`
- sync write pipeline body / async wrapper

The explicit split is better because the sync side must reject orphaned coroutines,
while the async side must await them. A generic maybe-await helper would hide the
security property.

### P3.5 - Do not merge the casing helpers into one configurable mega-helper

Keep these separate:

- `snake_case`
- `pascal_case`
- `graphql_camel_name`
- `pascalize_token`

They have different collision and acronym contracts. The DRY improvement is moving
`graphql_camel_name` to `utils/strings.py` and adding a small checked-Pascal wrapper,
not inventing a parameterized `convert_case(style=...)` function.

### P3.6 - Do not genericize the whole write decode pipeline

Model, form, and serializer decoders share important primitives, but their tails are
materially different:

- model writes assign model attrs and defer M2M;
- forms split `data=` and `files=` and may reconstruct partial update data;
- serializers preserve serializer field names, nested serializers, DRF context, and
  `partial=True`.

Keep sharing primitives and the existing `run_write_pipeline_sync` skeleton. Do not
try to make one giant configurable decode engine. That would reduce duplicated lines
but increase complexity and make the security ordering harder to audit.

## File-by-File Utility Notes

| Utility file | DRY status | Recommended action |
|---|---|---|
| `utils/strings.py` | Good but incomplete as the naming hub. | Move `graphql_camel_name` here; add a checked-Pascal helper; keep `pascalize_token` distinct. |
| `utils/typing.py` | Good. | Extend these helpers for any new wrapper/callable shape; do not add local unwrap loops. |
| `utils/converters.py` | Good skeleton. | Use it for every converter; add an explicit continue sentinel if `None` becomes a legitimate conversion value. |
| `utils/connections.py` | Good. | Keep sidecar keys and window derivation here; switch tuple sidecars to a dataclass if sidecars grow. |
| `utils/relations.py` | Good core relation owner. | Move repeated forward-concrete relation/index helpers here if another caller needs them. |
| `utils/input_values.py` | Strong DRY win. | Add a logical-branch child iterator only if the FilterSet loops continue to grow or another set family gets logical branches. |
| `utils/permissions.py` | Strong DRY win. | Extend `request_from_info` for new context shapes; avoid new class wrappers; keep permission traversal here. |
| `utils/querysets.py` | Strong DRY/security owner. | Keep all visibility queryset composition here; add primary-only variants explicitly if needed. |
| `utils/inputs.py` | Strong but large. | Keep generated-input lifecycle here; split later by naming/lifecycle/field validation only if growth makes review harder. |
| `utils/__init__.py` | Appropriately conservative. | Do not re-export every helper; keep ownership visible through submodule imports. |

## DRY Checklist For Future Implementation

- If code needs a request, call or extend `request_from_info`.
- If code needs generated input materialization, use `make_input_namespace`.
- If code needs a generated input shape cache, use `make_shape_build_cache`.
- If code needs to walk provided write-input fields, use `iter_provided_input_fields`.
- If code needs to walk filter/order input values, use `iter_active_fields`.
- If code needs permission gate targets, use `active_permission_targets`.
- If code needs `Meta.fields` / `Meta.exclude`, use `resolve_effective_fields`.
- If code needs relation shape/cardinality, use `utils/relations.py`.
- If code needs related visibility, use `utils/querysets.py`.
- If code needs FieldError leaves, move/use the neutral FieldError utility.
- If code needs enum unwrap or invalid-text preflight, move/use the neutral write-value utility.
- If code needs optional dependency imports, add/use `utils/imports.py`.
- If code needs GraphQL path joins, add/use a neutral error-path helper.
- If code needs string case conversion, use `utils/strings.py`.
- If code needs type unwrapping or async-callable detection, use `utils/typing.py`.
- If code needs converter dispatch, use `convert_with_mro`.
- If code needs connection sidecar or window logic, use `utils/connections.py`.

## Suggested Refactor Order

1. Extend `request_from_info()` for any new transport/context shape before changing
   auth, router, filter, order, mutation, or serializer code.
2. Move FieldError construction and write-value helpers out of
   `mutations/resolvers.py` into neutral utility modules.
3. Add `utils/imports.py` and migrate registry/generated-input/router optional import
   code to it.
4. Move `graphql_camel_name` to `utils/strings.py` and add a checked-Pascal helper.
5. Add a FilterSet logical-branch iterator if the current three loops are touched by
   the next implementation.
6. Promote relation pk/index primitives only when another caller needs the exact same
   behavior.
7. Clean stale `docs/feedback.md` references from docstrings opportunistically when
   touching those files.

## Verification Performed

- Read every file under `django_strawberry_framework/utils/`.
- Checked consumers of the key utility helpers with `rg`.
- Inspected filter/order permission wrappers, write resolver imports, converter
  callers, registry clear helpers, and naming call sites.
- Did not run pytest; repo instructions say not to run pytest unless explicitly asked.
