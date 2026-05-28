# Review feedback for `docs/spec-021-filters-0_0_8.md`

## High priority

### H1. Owner binding must be a complete pre-pass before any filter expansion

Decision 6 / Slice 3 currently says to iterate each `DjangoType`, assign
`filterset_class._owner_definition = definition`, then call `filterset_cls.get_filters()` for that
same class.

That sequencing is order-dependent. If `BookFilter.get_filters()` expands
`RelatedFilter("GenreFilter")` before the finalizer loop reaches `GenreType`, then
`GenreFilter._owner_definition` is still unset. Any owner-aware work done during that expansion can
fall back to `registry.get(target_model)` or cache filter state against the wrong owner. This is
especially risky for `Meta.primary` and GlobalID validation, where the expected GraphQL type name is
owner-specific.

Fix the spec to require distinct phase-2.5 subpasses:

1. collect all `definition.filterset_class` values and bind/validate every owner first;
2. after every owner is bound, call `get_filters()` for every wired filterset;
3. then materialize input types with `FilterArgumentsFactory`;
4. then run orphan `filter_input_type` validation.

Relevant spec anchors:
`docs/spec-021-filters-0_0_8.md #"For each DjangoType with definition.filterset_class is not None"`
and
`docs/spec-021-filters-0_0_8.md #"Call filterset_cls.get_filters() to trigger Layer-4 expansion"`.

### H2. Reusing one FilterSet class across multiple owners is unsafe with only Relay/scalar shape checks

The spec allows a second owner to bind the same `FilterSet` class when every related target has a
compatible Relay/scalar shape, while keeping the first `_owner_definition`.

That is not strong enough. Relay GlobalID runtime validation depends on the concrete GraphQL type
name, not just whether the target is Relay-shaped. Two owners can both expose Relay nodes but use
different GraphQL names for the same model or relation, such as a public type and an admin type.
Using the first owner's `_owner_definition` for the second owner will validate or encode against the
wrong type name.

Fix the spec to either make owner binding and generated input classes owner-specific, preferably by
caching by `(filterset_class, owner_definition)`, or reject reuse unless every owner-sensitive target
resolves to the exact same `DjangoTypeDefinition` / GraphQL type name. Relay-vs-scalar compatibility
alone is not enough.

Relevant spec anchors:
`docs/spec-021-filters-0_0_8.md #"Two owners with compatible Relay shapes"` and
`docs/spec-021-filters-0_0_8.md #"The expected name is resolved through owner_definition.related_target_for(field_name).graphql_type_name"`.

### H3. The apply pipeline constructs the FilterSet before related constraints are applied

Decision 8 constructs the filterset with `cls(data=normalized_data, queryset=queryset,
request=request)`, then later applies explicit related constraints to `queryset`, and finally
returns `filterset.qs`.

In `django-filter`, `.qs` is derived from the filterset instance's stored queryset. If the code
constrains a separate local queryset variable after construction, `filterset.qs` can ignore those
related constraints. The spec needs to make the queryset ownership explicit.

Fix the flow so explicit related constraints are applied before constructing the production
`FilterSet` instance. If form validation requires an instance before constraints can be calculated,
the design should either use a validation-only instance or assign the constrained queryset back onto
the filterset before `.qs` is touched.

Relevant spec anchors:
`docs/spec-021-filters-0_0_8.md #"The filterset is then instantiated as cls(data=normalized_data, queryset=queryset, request=request)"`
and `docs/spec-021-filters-0_0_8.md #"The instance's .qs property runs"`.

### H4. The invalid-form acceptance test will be caught by GraphQL enum coercion first

The test plan says `test_apply_raises_graphqlerror_on_invalid_filter_input` should send
`circulationStatus: { exact: "NOT_A_REAL_ENUM_VALUE" }` to exercise
`FilterSet._validate_form_or_raise`.

That will not reach django-filter form validation if the converter maps
`ChoiceFilter` / `TypedChoiceFilter` to a Strawberry enum. GraphQL input coercion rejects the invalid
enum literal before the resolver and before `filterset.form.is_valid()` can run.

Fix the test plan so form-validation coverage uses an input value that passes GraphQL coercion but
fails the django-filter form. A narrow fakeshop-only custom filter with a string input and a form
validator would keep this as a live `/graphql` test. If no natural live path exists, move this
specific validation pin to `tests/filters/test_sets.py` and keep a separate live test for GraphQL
enum coercion.

Relevant spec anchors:
`docs/spec-021-filters-0_0_8.md #"test_apply_raises_graphqlerror_on_invalid_filter_input"` and
`docs/spec-021-filters-0_0_8.md #"ChoiceFilter / TypedChoiceFilter"`.

## Medium priority

### M1. The fakeshop root `get_queryset` test references a nonexistent `Branch.is_private` field

The acceptance-test plan seeds `branch_public(is_private=False)` and
`branch_private(is_private=True)`, but `examples/fakeshop/apps/library/models.py::Branch` has only
`name`, `city`, and `tags`.

Fix the spec to use an existing field for the visibility predicate, for example hiding a branch with
`city == "restricted"` or a `name` marker in `BranchType.get_queryset`. This keeps the test focused
on root-queryset ordering without requiring a model migration.
