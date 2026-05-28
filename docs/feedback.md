# Review feedback for `docs/spec-021-filters-0_0_8.md`

## High

### H1. Nested `RelatedFilter` traversal can bypass the target `DjangoType.get_queryset`

`docs/spec-021-filters-0_0_8.md #"Filter applied to a relation that has a custom get_queryset"` says the optimizer's `Prefetch` downgrade preserves the target type's visibility hook and that the filter clause applies to the visibility-scoped queryset. That is true for relation output planning in `django_strawberry_framework/optimizer/walker.py::_build_child_queryset`, but it is not true for parent-row filtering. A nested filter compiles to ORM `WHERE` joins before the optimizer plans selected output relations, so `{ shelves: { code: ... } }` can match a `Branch` through a `Shelf` that `ShelfType.get_queryset` would hide.

Root fix: make `FilterSet.apply(input_value, queryset, info)` carry `info` into related-filter application. For each active `RelatedFilter`, derive the child visibility queryset from the related target `DjangoType.get_queryset(child_model._default_manager.all(), info)`, intersect it with an explicit `RelatedFilter(queryset=...)` when present, constrain the parent queryset to that child queryset, and only then apply child filter clauses. Reuse the existing sync/async `get_queryset` handling discipline from `django_strawberry_framework/types/relay.py::_apply_get_queryset_sync` and `django_strawberry_framework/types/relay.py::_apply_get_queryset_async`. Add a live HTTP test where a hidden related row would otherwise make the parent match.

### H2. The self-referential lazy list annotation shape will not resolve

Decision 3 says logical `and_` / `or_` fields use `Annotated[list["<TypeName>FilterInputType"], strawberry.lazy("django_strawberry_framework.filters.inputs")] | None`. Strawberry's lazy resolver only resolves the annotated argument when the annotated argument itself is a `ForwardRef`; wrapping `list["Foo"]` in `Annotated[..., strawberry.lazy(...)]` leaves the inner `"Foo"` unresolved.

Root fix: generate `list[Annotated["<TypeName>FilterInputType", strawberry.lazy("django_strawberry_framework.filters.inputs")]] | None` for `and_` and `or_`, and `Annotated["<TypeName>FilterInputType", strawberry.lazy(...)] | None` for `not_`. Keep the future-annotations test, but add a focused schema-construction test for the self-referential `and` / `or` fields because the current proposed shape can pass ordinary annotation construction and still fail during Strawberry type evaluation.

### H3. Lookup GraphQL names are not pinned, and the examples will not match Strawberry's default camel-casing

The spec's live queries use lookup names like `iContains`, but a generated Python attribute named `icontains` stays `icontains` under Strawberry's default auto-camel-case behavior because there is no underscore to transform. The same naming gap appears for Python keywords: the lookup `in` cannot be a dataclass field named `in`, but the spec only handles the logical keywords `and` / `or` / `not`.

Root fix: define a single lookup-name adapter for every generated lookup field. Examples: `icontains -> Python i_contains / GraphQL iContains`, `iexact -> i_exact / iExact`, `isnull -> is_null / isNull`, `in -> in_ / in`, and any other supported django-filter lookup. Use it in both `_build_input_fields` and input normalization. Add SDL or introspection assertions for at least `iContains`, `isNull`, and `in`, plus the existing live HTTP query using `iContains`.

### H4. Relay-vs-scalar ID shape cannot be decided only through `registry.get(target_model)`

Decision 4 says `FilterSet.filter_for_field` / `filter_for_lookup` should call `registry.get(target_model)` and inspect the primary target `DjangoType`. That loses the owner type. With `Meta.primary`, the primary type for a model can be non-Relay while a secondary type using the same model is Relay-shaped, or the inverse. A filterset bound to the secondary type would then expose the primary type's ID shape, not the actual GraphQL type's ID shape.

Root fix: make input generation owner-aware. Either bind each `filterset_class` to the owning `DjangoTypeDefinition` during finalizer phase 2.5 and include that owner in the filter/input factory context, or explicitly reject assigning the same filterset to owner types whose Relay ID shape would require different input contracts. The test plan should cover a model with both primary and secondary `DjangoType`s where only one implements `relay.Node`.

## Medium

### M1. The filter-instance-to-Strawberry-input conversion contract is still underspecified

`FilterArgumentsFactory._ensure_built` now derives input shape from resolved filter instances, which is the right direction, but the spec punts with `type(filter_instance).input_type — or whatever attr the per-primitive port exposes`. Standard `django-filter` filters do not expose an `input_type`; they expose Django form fields through `filter_instance.field`. The implementation needs a real conversion layer, not an implied attribute.

Root fix: add a named converter, for example `convert_filter_to_input_annotation(filter_instance, model_field, owner_type)`, and a matching runtime normalizer. It must handle choice enums (`Enum` member to DB value), Strawberry `relay.GlobalID` objects, `in` / `range` list shapes, nullable values, decimal/date/time values, and custom filter `method=` fields. The choice-enum and Relay GlobalID live HTTP tests should assert this path end-to-end.

### M2. Invalid django-filter form data will not automatically reject

The test plan says `FilterSet.apply` rejects normalized input that fails django-filter form validation, but `django_filters.filterset.BaseFilterSet.qs` only touches `self.errors` before calling `filter_queryset`; it does not raise on invalid form data. If `apply` just returns `filterset.qs`, invalid filter values can degrade into a partially-filtered or unfiltered queryset instead of a GraphQL error.

Root fix: `FilterSet.apply` should explicitly call `filterset.form.is_valid()` after permission checks and before `.qs`, then raise a `GraphQLError` with a stable, compact error shape when validation fails. Add a package test proving invalid normalized data does not return rows.

### M3. `Meta.fields = "__all__"` is described as matching django-filter, but the described behavior differs

The spec says `"__all__"` expands to scalar fields plus FK / PK columns, excludes implicit relation traversal, and "matches django-filter's own" behavior. In `django-filter`, `get_all_model_fields` includes `opts.fields + opts.many_to_many` and excludes `AutoField` primary keys. That is the opposite of two important parts of the spec: the spec wants primary keys included and M2M relations excluded unless declared through `RelatedFilter`.

Root fix: state the package is intentionally overriding django-filter's `"__all__"` expansion, then pin the override in `FilterSet.get_fields` / `_get_fields`. Add tests that `id` is generated for `"__all__"` and that a M2M relation is not generated without an explicit `RelatedFilter`.

### M4. The `RelatedFilter(queryset=...)` boundary is inconsistent about when it applies

Decision 8 says "for each `RelatedFilter` in the input" the explicit queryset bounds the child queryset. The cookbook method the spec cites, `_apply_related_queryset_constraints`, applies every explicit related-filter queryset unconditionally to the parent queryset. If copied literally, a `BranchFilter` with `shelves = RelatedFilter(..., queryset=permanent_shelves)` would exclude branches without permanent shelves even for `filter: { name: ... }` or possibly for an empty filter.

Root fix: pin one behavior. The better behavior is active-branch scoping: apply the explicit related queryset only when the related filter branch is present in the normalized input. If the intended behavior is global scoping, rename and document it as a global parent-scope constraint, then add tests for empty-filter and unrelated-field-filter cases so the row-loss is deliberate.

### M5. The resolver examples bypass the existing visibility hook

Decision 8 correctly says root visibility scoping runs before filters, but the user-facing resolver example and Slice 4 fakeshop instructions show `models.<Model>.objects...` followed directly by `FilterSet.apply(...)`. That skips `DjangoType.get_queryset`, which `TODAY.md #"If a root fakeshop list should apply public/staff visibility rules"` explicitly says manual root resolvers must call themselves.

Root fix: update every resolver example and Slice 4 instruction to call the owning type's `get_queryset` before `FilterSet.apply`, e.g. `queryset = BranchType.get_queryset(models.Branch.objects.order_by("id"), info)`. Add a live HTTP test with a root type-level `get_queryset` filter and a filter clause that would otherwise return hidden rows.

### M6. The Relay GlobalID primitive needs Strawberry-specific parsing and type validation

The graphene primitive parses a raw string and discards the decoded type name. Strawberry resolver inputs annotated as `relay.GlobalID` arrive as `strawberry.relay.GlobalID` objects, and accepting the wrong `type_name` would let a `GenreType` filter accept an encoded ID for some other type with the same database primary key.

Root fix: the ported `GlobalIDFilter` / `GlobalIDMultipleChoiceFilter` should accept both raw strings and `relay.GlobalID` objects, validate the decoded type name against the expected target GraphQL type name, and then pass only `node_id` to django-filter. Add tests for wrong-type GlobalIDs and mixed-type multiple-choice lists.

## Low

### L1. The `galaxy__name` input-shape note conflicts with the cookbook tree builder

The edge-case section says `Meta.fields = {"galaxy__name": ["exact"]}` renders as a flat input field and does not expand the path into nested input types. The cookbook's `FilterArgumentsFactory.filterset_to_trees` splits `field_name` on Django's lookup separator and builds nested path nodes. Pin the intended GraphQL shape explicitly; otherwise an implementer can reasonably choose either `galaxy__name: { exact: ... }` or `galaxy: { name: { exact: ... } }`.

### L2. The CHANGELOG doc-update block still says "6-8 tests"

Most of the spec now pins exactly 9 live HTTP tests, but the proposed `CHANGELOG.md` Added bullet still says "6-8 tests". Update that prose to exactly 9 so the Slice 5 docs do not reintroduce the earlier count drift.
