# Review feedback for `django_strawberry_framework/` filter implementation

Scope: implementation review of the `django_strawberry_framework/` changes made for
`docs/spec-021-filters-0_0_8.md`. This pass focused on behavior against the spec's highest-risk
contracts: owner-aware Relay-vs-scalar resolution, nested `RelatedFilter` visibility scoping,
permission-gate dispatch, input-shape conversion, and finalizer binding.

I did not run pytest. I used targeted source inspection and small runtime probes against the
fakeshop schema to confirm the concrete failure modes below.

## High priority

### H1. Expanded `RelatedFilter` leaves are exposed as flat root fields, bypassing child visibility and permissions

`django_strawberry_framework/filters/inputs.py::_build_input_fields` walks
`filterset_cls.get_filters()` and groups every expanded child leaf into a root input field. For
`BookFilter`, the generated input contains both nested relation branches such as `genres` and flat
expanded leaves such as `genresName`, `genresBooksTitle`, `shelfBranchCity`, and similar fields.

That shape is unsafe with the spec's Decision 8 visibility contract. The apply pipeline only treats
a related branch as active when `django_strawberry_framework/filters/sets.py::FilterSet._iter_active_related_branches`
finds the declared `RelatedFilter` key in the input. A consumer can send the flat field
`genresName` instead of the nested `genres` branch; `FilterSet._normalize_input` then turns it into
the parent form key `genres__name`, and django-filter applies the SQL join directly on the parent
filterset. The related target's `DjangoType.get_queryset(...)` is not called for that branch, and
the child filterset's `check_*_permission` hooks do not run.

Impact:

- A nested filter can match parent rows through related rows that the target `DjangoType.get_queryset`
  would have hidden.
- Child filter permission gates can be bypassed by choosing the flat expanded field instead of the
  nested `RelatedFilter` branch.
- The public GraphQL surface becomes confusing because it exposes both the intended nested relation
  input and duplicate flattened paths for the same relation.

Concrete evidence:

- `FilterArgumentsFactory(BookFilter).arguments` currently exposes root fields like `genres`,
  `genresName`, `genresBooksTitle`, `shelf`, `shelfBranchCity`, and `loansNote`.
- `_iter_active_related_branches` only checks declared related branch names, so the flat fields never
  enter `_derive_related_visibility_querysets_sync` / `_derive_related_visibility_querysets_async`.

Recommended fix:

Skip expanded child leaves whenever the first path segment is a declared `RelatedFilter`. Keep the
single nested `RelatedFilter` field as the GraphQL surface for that branch. Flat fields should remain
only for explicit consumer-authored traversal declarations such as `Meta.fields = {"galaxy__name":
["exact"]}` where there is no declared `RelatedFilter` boundary for `galaxy`.

Add tests that assert `BookFilterInputType` exposes `genres` but not `genresName`, while a standalone
explicit traversal filter still exposes the flat `galaxyName` / `branchName` field and normalizes it
back to the correct Django source path.

Relevant code:

- `django_strawberry_framework/filters/inputs.py::_build_input_fields`
- `django_strawberry_framework/filters/sets.py::FilterSet._normalize_input`
- `django_strawberry_framework/filters/sets.py::FilterSet._iter_active_related_branches`
- `django_strawberry_framework/filters/sets.py::FilterSet._derive_related_visibility_querysets_sync`
- `django_strawberry_framework/filters/sets.py::FilterSet._derive_related_visibility_querysets_async`

### H2. Permission hooks are dispatched with lookup-suffixed form keys, so non-`exact` lookups bypass field gates

`django_strawberry_framework/filters/sets.py::FilterSet._run_permission_checks` first calls
`_normalize_input(input_value)` and then invokes permission methods for each normalized form key.
For an input like `name: { iContains: "x" }`, normalization emits `name__icontains`, so permission
dispatch looks for `check_name_icontains_permission`.

The spec's active-input-only permission contract is field-based: a `check_name_permission` gate
should fire when the consumer uses the `name` field, regardless of whether the lookup is `exact`,
`iContains`, `in`, or another supported lookup. The current behavior only hits the field-level gate
for `exact`, because exact normalizes to the bare source path.

Impact:

- Consumers who define `check_<field>_permission` get protection for `exact` but not for other
  lookups on the same field.
- The bypass also applies recursively inside nested logical branches because those branches reuse
  `_run_permission_checks`.
- Once H1 is fixed, this still matters for intended nested relation usage: child filtersets need
  `check_code_permission` to fire for `code: { iContains: ... }`, not only `code: { exact: ... }`.

Recommended fix:

Dispatch permission checks against the source field path, not the fully-suffixed form key. The
normalizer already has enough context through `_field_specs`, operator-bag attrs, and resolved
filter instances to distinguish the field path from the lookup token. A robust design is to collect
active permission field paths while walking the original input tree, then invoke gates from that
set. This avoids reverse-parsing django-filter form keys after lookup mapping has already collapsed
GraphQL names into Django names.

If lookup-specific permission hooks are desired later, add them as an explicit extension on top of
the field gate. Do not make lookup-specific names the only hook that fires.

Add tests for:

- `name: { iContains: "x" }` fires `check_name_permission`;
- `id: { in: [...] }` fires `check_id_permission`;
- nested `shelves: { code: { iContains: "A" } }` fires `ShelfFilter.check_code_permission`;
- logical `or` arms deduplicate the field gate without skipping it.

Relevant code:

- `django_strawberry_framework/filters/sets.py::FilterSet._run_permission_checks`
- `django_strawberry_framework/filters/sets.py::FilterSet._invoke_permission_method`
- `django_strawberry_framework/filters/sets.py::FilterSet._normalize_input`

### H3. Owner-aware relation resolution discards `DjangoTypeDefinition.origin` and falls back to the global registry

`django_strawberry_framework/filters/sets.py::FilterSet._resolve_relation_target_type` correctly
calls `owner.related_target_for(field_name)`, but then returns
`getattr(target_definition, "type", None) or getattr(target_definition, "type_cls", None)`. The
actual field on `DjangoTypeDefinition` is `origin`.

Because both attempted attribute names are absent, the method falls through to
`registry.primary_for(related_model) or registry.get(related_model)`. That is the exact global
fallback the spec tightened away for bound filtersets under `Meta.primary`.

Impact:

- A secondary owner whose related field intentionally points at a non-primary `DjangoType` can still
  generate filters using the primary type's Relay/scalar shape.
- GlobalID expected type-name validation can use the wrong type when multiple `DjangoType`s exist
  for a model.
- The finalizer appears to bind `_owner_definition`, but the runtime branch that needs that owner
  ignores the result.

Recommended fix:

Return `target_definition.origin` from `_resolve_relation_target_type`. Keep the registry fallback
only for the unbound pre-finalizer path. Then add a test where a bound owner resolves a relation to a
secondary target whose Relay shape differs from the model's primary type; `filter_for_field` and
`filter_for_lookup` should use the owner-resolved target, not the registry fallback.

Relevant code:

- `django_strawberry_framework/filters/sets.py::FilterSet._resolve_relation_target_type`
- `django_strawberry_framework/types/definition.py::DjangoTypeDefinition.related_target_for`

### H4. Multi-owner `FilterSet` validation checks only declared `RelatedFilter`s, not every owner-sensitive field

`django_strawberry_framework/types/finalizer.py::_bind_filterset_owner` validates second-owner
binding by iterating `filterset_cls.related_filters`. The spec's current rule is broader: second
owner binding is allowed only when every owner-sensitive target resolves to the exact same
`DjangoTypeDefinition` and `graphql_type_name`.

Owner-sensitive targets include more than declared `RelatedFilter`s:

- the owner model's own PK when the owner is Relay-shaped;
- FK, OneToOne, M2M, and reverse relation fields declared through `Meta.fields`;
- relation paths declared by custom filter instances through `field_name=...`;
- any lookup that can hit `GlobalIDFilter` / `GlobalIDMultipleChoiceFilter` validation.

Impact:

- A single shared filterset with only `Meta.fields = {"id": ["exact"]}` can bind first to a Relay
  owner and then to a non-Relay owner, or vice versa, without rejection.
- A shared filterset with only FK fields in `Meta.fields` can bind to owners whose related targets
  differ, because no `RelatedFilter` entry exists to compare.
- Since the class stores only the first `_owner_definition`, the second owner can get the first
  owner's input shape and GlobalID type-name validation.

Recommended fix:

Broaden `_bind_filterset_owner` to compare every owner-sensitive field path without calling
`get_filters()` during subpass 1. The comparison can be derived from the filterset's declared
`Meta.fields`, `get_fields()` output, and declared custom filters' `field_name` values:

- compare own-PK behavior for the two owners;
- for every relation-root source path, compare `previous.related_target_for(root)` and
  `definition.related_target_for(root)`;
- require both `DjangoTypeDefinition` identity and `graphql_type_name` equality;
- keep the current declared-`RelatedFilter` comparison as one input into that broader set.

Add tests where one shared filterset has no `RelatedFilter`s and still rejects divergent owner
bindings for `id`, a forward FK, and an M2M field.

Relevant code:

- `django_strawberry_framework/types/finalizer.py::_bind_filterset_owner`
- `django_strawberry_framework/filters/sets.py::FilterSet.get_fields`
- `django_strawberry_framework/filters/sets.py::FilterSet.filter_for_field`
- `django_strawberry_framework/filters/sets.py::FilterSet.filter_for_lookup`

### H5. Multi-value lookup conversion is incomplete for `in`, `range`, and Relay GlobalID lists

`django-filter` generates lookup-specific filter classes for `in` and `range`, such as
`BaseInFilter` / `ConcreteInFilter` and `BaseRangeFilter` / `ConcreteRangeFilter`. The converter in
`django_strawberry_framework/filters/inputs.py::convert_filter_to_input_annotation` does not
recognize those generated classes. They fall through to scalar form-field mapping.

The same issue appears in normalization:
`django_strawberry_framework/filters/inputs.py::normalize_input_value` does not recognize the
generated `BaseInFilter` / `BaseRangeFilter` classes either.

There is an additional Relay-specific problem:
`django_strawberry_framework/filters/sets.py::FilterSet.filter_for_lookup` maps a Relay owner PK
with lookup `in` to `GlobalIDFilter`, not `GlobalIDMultipleChoiceFilter`. For a Relay relation path
like `genres__id__in`, the generated input currently exposes `in: String` rather than
`in: [String!]`, so the spec's mixed-type multiple-choice GlobalID test is not actually covered by
the input shape.

Impact:

- Non-Relay `id__in` and other generated `in` lookups expose scalar inputs rather than `list[T]`.
- Generated `range` lookups expose the wrong input shape and do not normalize to the positional
  form keys django-filter expects.
- Relay `id.in` / relation `id.in` cannot validate each element's GlobalID type name because they
  are not represented as list-shaped GlobalID filters.
- The declared `GlobalIDMultipleChoiceFilter` class is currently unusable as a form filter because
  it inherits django-filter's `MultipleChoiceFilter` field behavior without supplying a non-choice
  list field; submitted GlobalID values are rejected as invalid choices before the filter method can
  decode them.

Recommended fix:

Treat lookup expression and filter base class as part of the conversion contract:

- `lookup_expr == "in"` or `isinstance(filter_instance, BaseInFilter)` should expose `list[inner]`
  and normalize each item;
- `lookup_expr == "range"` or `isinstance(filter_instance, BaseRangeFilter)` should expose the
  same range input shape as the explicit `RangeFilter` path and normalize to the positional
  `{<field>_0, <field>_1}` keys;
- Relay GlobalID `in` lookups should use `GlobalIDMultipleChoiceFilter`, including for own PK and
  single-valued FK fields where the lookup itself is multi-valued;
- `GlobalIDMultipleChoiceFilter` needs a field class that accepts arbitrary list values rather than
  validating against an empty choice set.

Add tests that inspect both generated SDL/input annotations and runtime apply behavior for:

- scalar `id: { in: [1, 2] }`;
- scalar `id: { range: { start: 1, end: 10 } }`;
- Relay owner `id: { in: ["<gid>"] }`;
- Relay relation `genres: { id: { in: ["<wrong>", "<right>"] } }` rejecting the wrong type with the
  offending index named.

Relevant code:

- `django_strawberry_framework/filters/inputs.py::convert_filter_to_input_annotation`
- `django_strawberry_framework/filters/inputs.py::normalize_input_value`
- `django_strawberry_framework/filters/sets.py::FilterSet.filter_for_lookup`
- `django_strawberry_framework/filters/base.py::GlobalIDMultipleChoiceFilter`

## Medium priority

### M1. Normalization decodes `relay.GlobalID` objects before the instance-bound filter can validate type names

`django_strawberry_framework/filters/inputs.py::normalize_input_value` returns `value.node_id` when
the raw input is a `strawberry.relay.GlobalID` object. That strips the `type_name` before
`django_strawberry_framework/filters/base.py::GlobalIDFilter.filter` or
`GlobalIDMultipleChoiceFilter.filter` can run `_decode_and_validate_global_id(...)`.

Raw string inputs still reach the filter method and can be validated because `_decode_global_id`
passes strings through unchanged. The object input path does not.

Impact:

- Direct Python usage of `FilterSet.apply_sync(...)` / `apply_async(...)` with `relay.GlobalID`
  objects can bypass wrong-type validation.
- The behavior contradicts the spec language that both raw strings and `relay.GlobalID` objects are
  accepted and validated.

Recommended fix:

Do not decode `relay.GlobalID` objects in the pre-instantiation normalizer. Preserve the object or
string form until the instance-bound filter method runs, because the bound filter is where
`filter_instance.parent._owner_definition` is available for type-name validation. If form-field
coercion requires a string, convert the object with `str(value)` so the encoded type name survives.

Add tests for direct `FilterSet.apply_sync(...)` with a wrong-type `relay.GlobalID` object, not only
with an encoded string.

Relevant code:

- `django_strawberry_framework/filters/inputs.py::normalize_input_value`
- `django_strawberry_framework/filters/inputs.py::_decode_global_id`
- `django_strawberry_framework/filters/base.py::GlobalIDFilter.filter`
- `django_strawberry_framework/filters/base.py::GlobalIDMultipleChoiceFilter.filter`

### M2. Tests should assert the absence of bypass fields, not just the presence of intended fields

Several current tests verify that intended fields exist, such as the nested `genres` branch or the
flat explicit traversal case. They do not assert that unintended expanded relation leaves are
absent. That gap allowed H1 to ship even though the schema contains both safe and unsafe shapes.

Recommended fix:

For every generated input surface that has a `RelatedFilter`, assert the field set exactly enough to
exclude expanded descendants from the root input. The important assertion is not merely that
`genres` exists; it is that `genresName`, `genresBooksTitle`, and equivalent expanded descendants do
not exist at the root. Keep a separate test proving explicit non-`RelatedFilter` traversals still
produce the intended flat field.

Relevant tests:

- `tests/filters/test_inputs.py`
- `tests/filters/test_factories.py`
- `examples/fakeshop/test_query/test_library_api.py`
