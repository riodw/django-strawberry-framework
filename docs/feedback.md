# Review feedback - `docs/spec-028-orders-0_0_8.md`

Reviewed the current on-disk spec against the shipped filter subsystem, the
current fakeshop library app, and the local upstream references the spec names.
`git diff -- docs/spec-028-orders-0_0_8.md` was empty at review time, so this
review is against the current repository copy of the spec.

The spec still needs a contract pass before implementation. Several issues would
produce the wrong GraphQL surface or break the same reload/finalizer lifecycle
the filter subsystem already stabilized.

## Blocking

### B1. `order_input_type` still returns one input object, but `orderBy` is specified as a list

Locations:

- Decision 5, GraphQL argument shape.
- Decision 11, `order_input_type(OrderSet)`.
- User-facing resolver examples under "Exposing the `orderBy:` argument" and
  "Composing with the shipped Filtering subsystem".
- DoD item 7 and the `test_order_input_type_returns_forwardref_in_annotation_args`
  test-plan bullet.

Decision 5 and every GraphQL query example require:

```graphql
orderBy: [<TypeName>OrderInputType!]
```

But Decision 11 still returns:

```python
Annotated["GalaxyOrderInputType", strawberry.lazy("django_strawberry_framework.orders.inputs")]
```

and the resolver examples use:

```python
order_by: order_input_type(GalaxyOrder) | None = None
```

That annotation yields a nullable single input object, not a nullable list. The
documented queries such as `orderBy: [{ name: ASC }]` would fail GraphQL input
coercion before `OrderSet.apply_sync(...)` ever runs.

Root-cause fix: make the helper own the actual resolver argument type:

```python
list[Annotated["GalaxyOrderInputType", strawberry.lazy(INPUTS_MODULE_PATH)]]
```

Then `order_by: order_input_type(GalaxyOrder) | None = None` matches the SDL.
If the intended helper contract is only "return the element type", then every
resolver example and test must say `list[order_input_type(GalaxyOrder)] | None`
and Decision 11 must stop calling the helper itself the resolver-argument shape.

### B2. The order input namespace clear lifecycle still diverges from the shipped filter lifecycle

Locations:

- Decision 9 lifecycle contract.
- Slice 3 checklist and DoD item 10.
- `tests/orders/test_inputs.py` and `tests/orders/test_finalizer.py` test-plan
  bullets around `clear_order_input_namespace`.
- Shipped reference: `django_strawberry_framework/filters/inputs.py::clear_filter_input_namespace`.

The spec says the order side mirrors the filter lifecycle, but it still narrows
the clear behavior to `_materialized_names`, `_helper_referenced_ordersets`, and
removing materialized module globals. That is not the filter side's actual
contract.

The filter clear path also clears factory caches and per-class binding/expansion
state, and it intentionally leaves materialized input classes parked in the
module namespace. Parking is load-bearing: existing `strawberry.lazy(...)`
references held by modules that were not reloaded continue to resolve until the
next successful finalize overwrites them.

If the order side follows the current spec:

- `OrderArgumentsFactory.input_object_types` can keep stale input classes after
  `registry.clear()`, so `_ensure_built()` may skip rebuilding against a fresh
  registry.
- `OrderSet` subclasses can retain `_owner_definition`, `_expanded_fields`, and
  `_is_expanding_fields` across reloads.
- Deleting module globals can break lazy annotations captured by resolver modules
  that were not reloaded.

Root-cause fix: define `clear_order_input_namespace()` as the order analogue of
`clear_filter_input_namespace()`:

- Clear `_materialized_names` and the order field-spec/provenance map.
- Clear `OrderArgumentsFactory.input_object_types` and its type-to-orderset
  collision registry.
- Reset every live `OrderSet` subclass's directly-set `_owner_definition`,
  `_expanded_fields`, and `_is_expanding_fields`.
- Leave already-materialized module globals parked.
- Keep `_helper_referenced_ordersets.clear()` as a separate `registry.clear()`
  block.

The test plan should assert those resets and should stop expecting
`clear_order_input_namespace()` to remove module globals.

### B3. The NULLS-positioning live test targets fields that cannot satisfy it

Locations:

- Slice 4 checklist, live HTTP coverage bullet.
- Decision 13 live HTTP coverage summary.
- `examples/fakeshop/test_query/test_library_api.py` test-plan subsection.
- Current model reference: `examples/fakeshop/apps/library/models.py::Book`.

The spec uses two incompatible fields for the NULLS-positioning test:

- Slice 4 names `description: DESC_NULLS_LAST`.
- The test plan names `title: DESC_NULLS_LAST` and expects `title=NULL` rows.

Current `Book` has no `description` field, and `Book.title` is non-null. The
current nullable text field is `subtitle`.

Root-cause fix: use `subtitle` consistently:

- `BookOrder.Meta.fields` includes `subtitle`.
- The query is `orderBy: [{ subtitle: DESC_NULLS_LAST }]`.
- The fixture seeds at least one `subtitle=None` row and one non-null subtitle
  row.
- Assertions verify nulls last against `subtitle`.

### B4. `"__all__"` still claims cookbook parity while excluding forward relation columns

Locations:

- Decision 3, "`Meta.fields = "__all__"` scope".
- Edge cases, "`Meta.fields = "__all__"`".
- Upstream reference: `django_graphene_filters/mixins.py::get_concrete_field_names`.

The spec says `"__all__"` expands to concrete fields and that "relations are NOT
included." The cookbook helper it cites returns fields with a `column` attribute.
That excludes reverse relations and M2M managers, but it includes forward FK and
forward OneToOne columns. For current fakeshop, `Book.shelf` is column-backed and
would be included by cookbook parity.

This affects the generated input shape. With cookbook parity,
`BookOrder.Meta.fields = "__all__"` exposes a leaf `shelf: Ordering` unless an
explicit `RelatedOrder` overrides the same name. If the package wants to exclude
all relation fields, that is a deliberate divergence and needs different prose
and tests.

Root-cause fix: choose one rule. Given the spec repeatedly says "cookbook
parity", the cleaner rule is:

- `"__all__"` means every column-backed model field, including forward FK/O2O
  columns, excluding reverse relations and M2M managers.
- An explicit same-name `RelatedOrder` overrides the column leaf when the
  consumer wants nested traversal.
- Package tests pin both the forward-FK leaf and the explicit override case.

## High

### H1. The shared mixin import path is stale

Locations:

- Decision 2, `base.py` bullet and rejected alternative.
- Decision 3 Layer 2.
- KANBAN past-tense body in Doc updates.
- Current code reference: `django_strawberry_framework/sets_mixins.py::LazyRelatedClassMixin`.

The spec still says the shared `LazyRelatedClassMixin` lives at
`django_strawberry_framework/filters/base.py` and that `orders/base.py` should
import it from the filter package. In the current codebase, the neutral shared
home is already `django_strawberry_framework/sets_mixins.py`, which also carries
`ClassBasedTypeNameMixin` for the future set family.

Importing through `filters.base` would load the filter subsystem just to build
orders and would re-couple sibling Layer-3 packages after the codebase already
created a neutral module.

Root-cause fix:

- `orders.base` imports `LazyRelatedClassMixin` from
  `django_strawberry_framework.sets_mixins`.
- `orders.sets.OrderSet` inherits `ClassBasedTypeNameMixin`.
- `orders.inputs._input_type_name_for()` delegates to
  `orderset_class.type_name_for()`, matching the filter side.
- The rejected-alternative prose should be rewritten because the move is already
  done.

### H2. Owner/model mismatch validation is still underspecified for ordersets

Locations:

- Decision 6 subpass 1.
- Risks, "Multi-`DjangoType`-per-model orderset binding".
- `tests/orders/test_finalizer.py` test-plan paragraph.
- Shipped reference: `django_strawberry_framework/types/finalizer.py::_bind_filterset_owner`.

Decision 6 says owner binding runs "own-PK + related-target validation", then
narrows the owner-sensitive order question to related-target agreement. It does
not clearly require first-bind model compatibility: the `OrderSet.Meta.model`
must match, or be a base of, the owning `DjangoType` model.

That check is still necessary. A `BookOrder` wired onto `BranchType` can build a
valid-looking order input from `Book` fields and then apply those field paths to
a `Branch` queryset, surfacing as a late Django `FieldError` instead of a
finalize-time `ConfigurationError`.

Root-cause fix: add an order-side `_bind_orderset_owner()` with the first-bind
model compatibility check from `_bind_filterset_owner()`:

- `definition.model` must be the orderset `Meta.model` or derive from it.
- Otherwise raise `ConfigurationError` naming the owner type, owner model,
  orderset class, and orderset model.
- Add a finalizer test for this mismatch.

The order side can omit the filter side's Relay own-PK identity check, but model
compatibility is not optional.

### H3. Relation-level permission gates are named as the security defense but not specified or tested

Locations:

- Decision 8 step 4, `check_shelves_permission(request)` example.
- Decision 8 step 6, `check_permissions`.
- `tests/orders/test_sets.py` and live permission test-plan bullets.
- Shipped reference: `django_strawberry_framework/filters/sets.py::FilterSet._run_permission_checks`.

The spec accepts the hidden-related-order position side channel for `0.0.8` and
says the consumer defense is a parent relation gate such as
`check_shelves_permission(request)`. But the algorithm text and tests only pin
scalar active/inactive gates like `check_name_permission`.

Following the cookbook flat-path permission logic would tend to fire
`check_shelves_code_permission` on the parent and `check_code_permission` on the
child for `orderBy: [{ shelves: { code: ASC } }]`; it does not necessarily fire
`check_shelves_permission`. That would make the documented defense ineffective.

Root-cause fix:

- Define order permission dispatch as the filter side's active-branch
  double-dispatch adapted to order inputs.
- For an active `RelatedOrder` branch, fire the parent
  `check_<branch>_permission(request)` once and recurse into the child orderset
  to fire child field gates.
- Deduplicate per `(OrderSet class, method name)` across list elements.
- Add package tests for parent relation gate denial, child field gate denial,
  inactive relation branch quiet behavior, and repeated-list-entry dedup.
- Add or retarget one live HTTP permission test to exercise an active
  `RelatedOrder` gate, not only a scalar field gate.

### H4. One filter+order live query uses the wrong enum literal casing for the current schema

Location:

- `examples/fakeshop/test_query/test_library_api.py` test-plan subsection,
  `test_library_books_filter_and_order_compose`.
- Current acceptance reference:
  `examples/fakeshop/test_query/test_library_api.py::test_library_books_filter_by_choice_enum`.

The spec's composition test uses:

```graphql
circulationStatus: { exact: AVAILABLE }
```

The current live fakeshop tests use lower-case enum values such as `available`
and `checked_out` for `BookTypeCirculationStatusEnum`. Implementing the spec as
written would make this live test fail at GraphQL enum coercion before the order
path is exercised.

Root-cause fix: use the current enum literal:

```graphql
circulationStatus: { exact: available }
```

Also update the assertion prose to say "available books" instead of implying the
wire enum value is `AVAILABLE`.

## Medium

### M1. The materialization ledger is typed as `name -> OrderSet`, but the materializer receives an input class

Locations:

- Decision 9 lifecycle contract.
- Decision 6 materialization subpass.
- DoD item 6.

The spec says `_materialized_names` is `dict[str, type[OrderSet]]` and that
`materialize_input_class(name, cls)` is idempotent for `(name, orderset_class)`.
But the two-argument materializer receives the generated input class as `cls`,
not the source `OrderSet`. The shipped filter side stores the materialized input
class in the materialization ledger and leaves source-class collision detection
to the factory.

Root-cause fix: mirror the filter split:

- `OrderArgumentsFactory` owns `input type name -> OrderSet class` collision
  detection.
- `orders.inputs._materialized_names` owns `input type name -> input class`
  idempotent materialization.
- `materialize_input_class(name, input_cls)` checks the `(name, input_cls)` pair.

If the order side wants materialization to validate the source orderset, change
the signature to include `orderset_class`; do not keep a two-argument signature
that cannot populate the documented ledger.

### M2. The duplicate-field ordering edge case claims a live HTTP test that is not in the exact-13 plan

Location:

- Edge cases, `orderBy: [{ name: ASC }, { name: DESC }]`.

The edge-case bullet says a live HTTP test pins duplicate/conflicting field
ordering behavior. The exact-13 live test list does not include that test.

Root-cause fix: either add the test and update every count, or reword the edge
case as documented behavior covered by package-level parsing/queryset tests only.

### M3. Slice-5 doc-update symbol lists are inconsistent

Locations:

- Slice 5 checklist.
- Doc updates.
- DoD items 16, 19, 20, and 21.

Some doc-update bullets include `Ordering`; others list only `OrderSet`,
`RelatedOrder`, `order_input_type`, and `Meta.orderset_class`. Decision 2 makes
`Ordering` part of the public subpackage surface, so the shipped-symbol sweeps
should include it consistently unless a document intentionally omits enum
entries.

Root-cause fix: sync the Slice 5 checklist, Doc updates, and DoD lists. At
minimum, `README.md`, `docs/README.md`, and `TODAY.md` should all include
`Ordering` alongside `order_input_type`.

### M4. Standing-spec source references still use raw line numbers

Locations:

- Revision history entries for B1/B3/H3/M3/M9/N3/R1-R4/N-new-2/N-new-3.
- Decision 3, Decision 6, Decision 8, Decision 9, Decision 12, and DoD item 9.

The standing-doc rule in `AGENTS.md` says raw `path:NN` references are allowed
only in per-cycle scratchpad artifacts. This spec is a standing design doc, so
references like `finalizer.py:478-600`, `registry.py:43-50`,
`filters/inputs.py:53,183`, and prose such as "line 635" should be replaced
with symbol-qualified references or unique-substring references.

Root-cause fix: use forms like:

- `django_strawberry_framework/types/finalizer.py::_bind_filtersets`
- `django_strawberry_framework/registry.py::TypeRegistry.clear`
- `django_strawberry_framework/filters/inputs.py::INPUTS_MODULE_PATH`
- `django_strawberry_framework/filters/__init__.py::_helper_referenced_filtersets`

For revision-history bookkeeping, finding IDs and section names are more stable
than stale line numbers.

### M5. The abstract-model edge case relies on a validator the current code does not have

Location:

- Decision 3, "Proxy / multi-table-inheritance semantics".

The spec says abstract models are irrelevant because
`DjangoType.Meta.model` rejects abstract models at `_validate_meta` time. Current
`django_strawberry_framework/types/base.py::_validate_meta` checks that
`Meta.model` is a Django model class, but it does not reject
`model._meta.abstract`.

Root-cause fix: either add an explicit abstract-model validator and test as part
of this card, or remove the claim and mark abstract-model `OrderSet` targets as
out of scope/undefined for this card. Do not leave the spec relying on a
nonexistent existing guard.

## Nit

### N1. `GraphQLError` links to the `ConfigurationError` glossary anchor

Location:

- Decision 8 step 4, the sentence about `check_shelves_permission(request)`.

The text says a gate raises `GraphQLError` but links through
`glossary-configurationerror`. Leave `GraphQLError` unlinked or add the correct
glossary entry if one is intended.

### N2. `apply_async` return annotation prose is imprecise

Locations:

- Decision 2, `sets.py` bullet.
- DoD item 4.

The spec writes `apply_async(...) -> Awaitable[QuerySet]`. If the implementation
is an `async def`, the function annotation should be `-> QuerySet`; the call
expression is awaitable. The filter side uses `async def apply_async(...) -> models.QuerySet`.

## Summary

The highest-priority fixes are the list-shaped `order_input_type` contract, the
order namespace clear lifecycle, the impossible NULLS-positioning test, and the
`"__all__"` concrete-field semantics. The next tier is tightening owner/model
validation and relation-level permission dispatch so the order subsystem matches
the shipped filter subsystem's finalizer and security quality.
