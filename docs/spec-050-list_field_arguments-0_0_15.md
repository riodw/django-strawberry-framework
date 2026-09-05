# Spec: `DjangoListField` argument surface (`offset`, `limit`, and `orderBy`)

Target card: [`WIP-ALPHA-050-0.0.15`][kanban]
Status: in flight (`0.0.15`)
Revision: 2026-09-04 - implementation remediation complete; full and sharded verification
pending (`0.0.15`) (revision history moved to
[`spec-050-list_field_arguments-0_0_15-rationale.md`][rationale]).

Deliberation, rejected alternatives, and this spec's change record live in its companion
[`spec-050-list_field_arguments-0_0_15-rationale.md`][rationale].

Predecessors: [`spec-020`][spec-020] (the shipped non-Relay list field),
[`spec-028`][spec-028] (the shipped ordering subsystem and its explicit list-field
deferral), [`spec-030`][spec-030] (the connection field's Meta-derived sidecar signature),
and [`spec-047`][spec-047] (the shipped execution resource policy and raw-list bound).

Version boundary: this card does **not** move
[`django_strawberry_framework.__version__`][package-init], its
[`tests/base/test_init.py`][test-base-init] assertion, or the glossary package-version row.
It also makes no version edit to [`pyproject.toml`][pyproject], whose package version is
dynamic from that one literal, or to `uv.lock`, which records no editable-root version.
Cards 051, 052, and 053 remain non-Done on the `0.0.15` line, and
[`TODO-ALPHA-053-0.0.15`][kanban] / [`spec-053`][spec-053] own the joint version cut after
the line is complete. This card also does not edit [`CHANGELOG.md`][changelog]:
[`AGENTS.md`][agents] reserves it to the maintainer, and the joint-cut owner already carries
the release wording.

## Key glossary references

- [`DjangoListField`][glossary-djangolistfield] - the public field factory extended here.
- [`DjangoType`][glossary-djangotype] - the Meta-first model type that owns the ordering
  sidecar.
- [`Meta.model`][glossary-metamodel] and [`Meta.fields`][glossary-metafields] - the existing
  declaration keys used by the consumer example; this card adds no new Meta key.
- [`OrderSet`][glossary-orderset], [`Meta.orderset_class`][glossary-metaorderset_class],
  [`order_input_type`][glossary-order_input_type], and [`Ordering`][glossary-ordering] - the
  shipped ordering pipeline reused without a second input system.
- [`get_queryset` visibility hook][glossary-get_queryset] - the row-visibility boundary that
  must run before ordering and slicing.
- [Execution resource policy][glossary-execution-resource-policy] and
  [`ResourcePolicy`][glossary-resourcepolicy] - the request ceiling from which both accepted
  limit and maximum skip are derived.
- [`DjangoResourcePolicyExtension`][glossary-djangoresourcepolicyextension] - the
  pre-execution document-cost guard that deliberately continues to charge a raw list at its
  conservative policy ceiling rather than trusting an arbitrary argument named `limit`.
- [`DjangoConnectionField`][glossary-djangoconnectionfield], its
  [`DjangoConnection`][glossary-djangoconnection] return shape, and
  [connection-aware optimizer planning][glossary-connection-aware] - permanent boundaries:
  this card does not add offset pagination to connections or nested windows.
- [Live-first coverage mandate][glossary-live-first] - every wire-reachable branch lands in
  the fakeshop HTTP suite.
- [`DjangoOptimizerExtension`][glossary-djangooptimizerextension] - the existing root-list
  planning path that must receive the final sliced queryset unchanged.
- [`strawberry_config`][glossary-strawberry_config] - the supported schema naming boundary;
  error payloads use the argument spelling selected by its active name converter.
- [Joint version cut][glossary-joint-version-cut] - why card 053, not this card, owns the
  `0.0.15` release state.
- The [visibility boundary][glossary-visibility-boundary] and its
  [sealed execution queryset][glossary-sealed-execution-queryset] - the shared seam this card
  extends with the reject-combined and require-unevaluated options.
- [`ListArgumentError`][glossary-listargumenterror], the
  [list offset order precondition][glossary-list-offset-order-precondition], and the
  [async queryset completion adapter][glossary-async-queryset-completion-adapter] - this
  card's three planned glossary concepts, `shipped` at the joint cut.

## Slice checklist

- [ ] **Slice 1 - argument normalization and typed runtime rejection**
  - [ ] [`django_strawberry_framework/list_field.py`][list-field] synthesizes `offset: Int` and
        `limit: Int` on every `DjangoListField`; both are nullable and optional.
  - [ ] A package-owned [`ListArgumentError`][glossary-listargumenterror] rejects negative
        and over-ceiling runtime values with stable `extensions`; GraphQL's standard `Int` coercion owns wire type
        rejection before the resolver.
  - [ ] That class is exported from
        [`django_strawberry_framework/__init__.py`][package-init], and
        [`tests/base/test_init.py`][test-base-init]'s pinned `__all__` tuple, star-import row,
        and export-identity row are updated with it; the version literal and its own assertion
        stay with card 053.
  - [ ] Argument wire names are resolved only while building an error, never on a successful
        request.
  - [ ] The offset ceiling is `ResourcePolicy.max_list_rows`; no setting key is added.
  - [ ] Error payloads derive argument names from the active Strawberry schema rather than
        assuming the default camel-case converter.
- [ ] **Slice 2 - Meta-derived `orderBy` and list pipeline**
  - [ ] A target carrying `Meta.orderset_class` gains nullable, optional
        `orderBy: [<OrderSet>InputType!]`; a target without that sidecar does not publish a
        meaningless order input.
  - [ ] Sync and async paths run visibility, then `OrderSet`, then the offset/order guard,
        then the one raw-list slice.
  - [ ] The result of a public `OrderSet.apply_*` override is validated as an unevaluated,
        unsliced, non-projection, non-combined model queryset before the final window; the
        seal gains the new `unevaluated` option, reuses the shipped `reject_combined` one,
        and both new-to-this-boundary codes gain arms at the two visibility message sites.
  - [ ] Nonzero offset requires a materially active `orderBy` or still-effective model
        `Meta.ordering` on the post-visibility queryset; no pk tiebreaker and no `DISTINCT`
        are injected.
- [ ] **Slice 3 - SQL and unit contracts**
  - [ ] [`tests/test_list_field.py`][test-list-field] pins signature shape, cap arithmetic,
        direct-call runtime errors, helper mechanics, model-ordering state, and no-argument
        SQL parity; wire-reachable sync and async wrapper behavior stays in the live tier.
  - [ ] Remove adapter-relevant `DJANGO_ALLOW_ASYNC_UNSAFE` setup from existing package
        tests so it cannot mask a regression in safe async queryset completion; retain an
        override only where a separately named legacy behavior genuinely still requires it.
  - [ ] Order input construction continues to use the shipped `OrderSet` factory and orphan
        ledger rather than a list-field-specific input class.
- [ ] **Slice 4 - live acceptance**
  - [ ] A dedicated `examples/fakeshop/test_query/test_list_field_api.py` drives the sync
        surface over `/graphql/`: ordered offset pages, `orderBy` lists,
        visibility-before-order, limit/cap/error cases, converter naming, and the exceptional
        holder-mounted source shapes. It is the sync counterpart of the async suite rather
        than nineteen more rows inside the broad library application suite.
  - [ ] [`examples/fakeshop/test_query/test_resource_policy_api.py`][fakeshop-test-resource-policy]
        pins request-policy narrowing over the same field surface.
  - [ ] A test-local [`AsyncDjangoGraphQLView`][glossary-djangographqlview] mount proves safe
        async queryset completion,
        configured argument names, async iterable cleanup, and async pipeline parity over
        HTTP without `DJANGO_ALLOW_ASYNC_UNSAFE`.
  - [ ] Add the new async live-test path to the card's predicted files, then regenerate the
        tracked-path constants after the path is in the index so governance sees the file.
  - [ ] Add the new suite and its shared-helper exemption to
        [`examples/fakeshop/test_query/README.md`][fakeshop-test-query-readme].
- [ ] **Slice 5 - documentation fold-in**
  - [ ] Update the list-field docstring and the shipped-surface descriptions in
        [`docs/GLOSSARY.md`][glossary], [`docs/README.md`][docs-readme],
        [`docs/TREE.md`][tree], and [`README.md`][readme] where the new arguments are
        enumerated.
  - [ ] Update `ResourcePolicy` and bounding-helper docstrings to distinguish returned/skip
        ceilings from total database rows scanned.
  - [ ] Update the KANBAN database when the implementation card closes;
        [`TODAY.md`][today] is deliberately not edited (no waiting entry exists to move - see
        Doc updates).
  - [ ] Leave the version literal, version assertion, package-version glossary row, release
        wording, and [`CHANGELOG.md`][changelog] to card 053's joint cut; `pyproject.toml`
        and `uv.lock` have no duplicate root-package version to bump.

## Problem statement

`DjangoListField` is the package's bounded non-Relay collection field, but clients cannot
select an ordered subset of its result. A schema author can manually write a Strawberry
resolver accepting `orderBy`, can manually slice a queryset, or can change the field into a
Relay connection. None is the DRF-shaped answer expected from the package's public field
factory. The first duplicates the shipped sidecar machinery, the second moves resource
validation into consumer code, and the third changes the response shape rather than adding
a list argument.

Both upstream families make offset pagination available, though their shapes differ.
`graphene-django` publishes `offset: Int` on every connection and converts it into an
`after` cursor in
[`graphene_django/fields.py::DjangoConnectionField.resolve_connection`][upstream-graphene-fields].
The package refuses that connection surface because it preserves the cursor response shape
while retaining the instability and scan cost of skip pagination.
`strawberry-graphql-django` instead ships `OffsetPaginationInput`, `OffsetPaginated[T]`, and
windowed relation pagination in
[`strawberry_django/pagination.py`][upstream-strawberry-pagination].
This package keeps its existing `list[T]` response and adds bounded list arguments; nested
pagination remains a connection concern.

The same field seam also owes an older debt. [`spec-028`][spec-028] shipped `OrderSet` but
explicitly deferred `DjangoListField` argument injection because the field wrapper then
exposed only `(root, info)`. `DjangoConnectionField` later proved the signature-synthesis
approach for Meta-derived sidecars. Opening the list wrapper once for pagination and once
later for ordering would create two signature builders and two subtly different pipelines.
This card closes both gaps together.

## Current state

At `0.0.14`,
[`django_strawberry_framework/list_field.py::DjangoListField`][list-field] creates either a
default resolver or a consumer-resolver wrapper and hands it directly to `strawberry.field`.
The wrapper has no synthesized `__signature__`, so its GraphQL field has no package-owned
arguments. Every resolver shape applies `get_queryset` before
[`django_strawberry_framework/resource_policy.py::bounded_rows`][resource-policy], giving
the request policy the final raw-list slice.

That final slice is already visible in SQL. With no client arguments, the default policy
produces a queryset high mark and therefore a `LIMIT`; `max_rows` narrows it, and
`trusted_max_rows=True` may deliberately widen past the request policy. The new design must
not remove, duplicate, or move that slice. "No arguments means unchanged SQL" therefore
means the same low mark, high mark, ordering, and parameters as `0.0.14` - not an absence of
`LIMIT`, which is not today's behavior.

Ordering already has a complete public and runtime pipeline. `Meta.orderset_class` is
validated and bound at finalization, [`order_input_type`][glossary-order_input_type] creates
the lazy Strawberry input annotation and records its orphan reference, and
[`django_strawberry_framework/orders/sets.py::OrderSet.apply_sync`][orders-sets] /
[`django_strawberry_framework/orders/sets.py::OrderSet.apply_async`][orders-sets] perform
active-input permission checks before queryset mutation.
Connections synthesize an `order_by` Python parameter only when the target definition
carries the sidecar, then apply visibility before the order. The list field reuses that
contract.

## Goals

1. Give every `DjangoListField` nullable optional `offset` and `limit` GraphQL arguments
   without changing its `list[T]` return shape.
2. Publish a Meta-derived `orderBy` argument wherever the target `DjangoType` declares
   `Meta.orderset_class`, using the exact input type and permission pipeline connections
   already use.
3. Bound requested rows by the existing effective raw-list ceiling and bound skipped rows
   by the request policy, rejecting invalid requests rather than silently clamping them.
4. Require [an active order for nonzero offset][glossary-list-offset-order-precondition],
   because a skip counted over an undefined order names no particular page. What ships is
   **ordered offset**, not stable or repeatable pagination; Decision 7 records why, and the
   distinction is carried into the docstring, the glossary, and the migration note.
5. Preserve byte-identical sync resolver behavior and SQL when `offset`, `limit`, and
   `orderBy` are all omitted; the async path deliberately replaces unsafe direct queryset
   completion with the representation adapter while preserving its query and data.
6. Keep visibility before ordering and every slice after both for queryset/manager sources;
   preserve the shipped visibility bypass for plain iterable returns while bounding them.
7. Complete bounded querysets safely through sync and async GraphQL views, so that
   framework-owned final queryset completion performs no synchronous ORM evaluation inside
   the event loop. The field neither can nor does promise the same of a consumer resolver or
   `get_queryset` hook that runs synchronous ORM calls in its own body.
8. Earn the reachable production coverage through live GraphQL HTTP tests and retain
   package tests only for construction and execution shapes unavailable from that mount.

## North-star and cookbook fit

This card advances success criteria 2, 5, and 7 in the project [`GOAL.md`][goal]: schema
authors can expose a model collection through `DjangoListField` without a hand-written list
resolver, the optimizer continues to receive the consumer-shaped lazy queryset, and a
Graphene migration retains its one-line field declaration and Meta-owned order sidecar. It
does not by itself establish the separate [cookbook-parity][glossary-cookbook-parity] target.

The working cookbook's
[`django-graphene-filters/examples/cookbook/cookbook/recipes/schema.py::Query`][cookbook-schema]
declares all four root collections as `AdvancedDjangoFilterConnectionField`, while each node
owns `filterset_class`, `orderset_class`, `aggregate_class`, `fields_class`, `search_fields`,
through its nested `Meta` declaration and defines `get_queryset` as a class hook beside that
declaration. The clean parity path for those fields is therefore this package's
`DjangoConnectionField` and cursor response, not silently changing them into flat lists.
`DjangoListField` is the other collection shape explicitly required by the north star: it is
chosen when the schema author wants a direct `list[T]` response.

For valid requests, the ordering established here preserves the reference's security
boundary. The cookbook
[`AdvancedDjangoFilterConnectionField.resolve_queryset`][cookbook-connection-field]
implementation applies the node's `get_queryset` before filtering and ordering, then the
Graphene connection paginates; this card applies `get_queryset` before `OrderSet` and the one
list window. The cookbook's staff / model-permission / cascade branches remain
consumer-authored hook behavior rather than roles hard-coded into the field factory.
Filtering, search, aggregates, and [fieldset][glossary-fieldset] behavior remain
connection/parity work and are not inferred onto a raw list by this card.

Two pagination differences are deliberate. Graphene's connection-level `offset` accepts an
unordered source and the cookbook connection adds its own duplicate-removal behavior after
filtering/order application. This flat-list surface instead requires a visible declared order
for nonzero offset and never injects `DISTINCT`. Those choices make the page coordinate
meaningful and preserve the shipped `OrderSet` result-row contract; neither claims
wire-compatible Graphene connection pagination, and neither promises a repeatable page when
the declared order contains ties (Decision 7). Decision 11 records the required migration
choice between a flat list with direct offset arguments and a Relay connection with cursors.

## Non-goals

- **Offset on a Relay connection.** Permanent refusal. Neither
  `DjangoConnectionField` nor synthesized relation connections gain an `offset` argument.
  Positional and keyset cursors stay the only connection page coordinates.
- **Nested/windowed raw-list pagination.** A nested collection that needs its own page uses
  the shipped relation connection. This card does not port
  [`strawberry_django/pagination.py::apply_window_pagination`][upstream-strawberry-pagination]
  to generated raw-list relations. `DjangoListField` remains the documented root Query
  factory, and nested planning is not promised - but this card does not RETRACT the shipped
  glossary sentence that manually assigned nested usage is "functional but not
  root-optimized", which has stood since `0.0.7`. That no-argument nested behavior is
  preserved unchanged and is not deprecated here. What is left unspecified, and said to be
  unspecified rather than silently narrowed, is the new arguments in that position: they are
  neither supported nor tested nested, and a consumer relying on them there is outside the
  contract. Retracting or confirming the nested promise is a separate decision carrying its
  own deprecation cost, not a side effect of adding root arguments.
- **An `OffsetPaginated[T]` envelope.** `DjangoListField` keeps returning `list[T]`; there is
  no new `pageInfo`, `totalCount`, or `results` object.
- **Filtering or search on `DjangoListField`.** They are separate public-surface decisions.
  This card does not infer a filter argument merely because a target has
  [`Meta.filterset_class`][glossary-metafilterset-class].
- **Dynamic `OrderSet` generation.** A target without `Meta.orderset_class` gets no
  `orderBy`.
  [`django_strawberry_framework/orders/factories.py::get_orderset_class`][orders-factories]
  remains build-and-test plumbing, not a public auto-generation path.
- **A total-order proof.** The card requires an active order, not a mathematical uniqueness
  proof. Lists do not mint cursors, and this surface does not append a pk tiebreaker.
- **A new offset-policy setting.** `ResourcePolicy.max_list_rows` bounds both returned raw
  rows and maximum skip; [`django_strawberry_framework/conf.py`][conf] is untouched.
- **A client-limit discount in document collection-cost accounting.** The generic raw-list
  walker continues to charge `ResourcePolicy.max_list_rows`; recognizing an argument named
  `limit` as this field's validated runtime contract requires field metadata the walker does
  not carry, and applying that assumption to arbitrary GraphQL lists would undercharge them.
- **Silent clamping.** A client value wider than its effective ceiling is an error. The
  package does not pretend the request was honored while returning a different page.
- **Version or release-note ownership.** Card 053 owns the shared `0.0.15` cut.

## Borrowing posture

### From `graphene-django` - borrow discoverability, refuse connection semantics

The installed source at
[`graphene_django/fields.py::DjangoConnectionField.__init__`][upstream-graphene-fields]
adds `offset: Int` to every connection.
[`graphene_django/fields.py::DjangoConnectionField.resolve_connection`][upstream-graphene-fields]
pops it, combines it with `after`, and converts the result back to a Relay offset cursor;
[`graphene_django/fields.py::DjangoConnectionField.connection_resolver`][upstream-graphene-fields]
additionally rejects `before` plus `offset`. The useful migration property is
discoverability: a migrant expects `offset` to be a normal nullable integer argument. The
package borrows that spelling on the flat-list field only. It refuses cursor conversion,
`before` composition, and the connection-wide publication (*why each was declined: see the
[rationale][rationale-borrowing]*).

### From `strawberry-graphql-django` - borrow offset arithmetic, keep this package's shape

The checkout at
[`strawberry_django/pagination.py::OffsetPaginationInput`][upstream-strawberry-pagination]
uses `offset=0` and optional `limit`;
[`strawberry_django/pagination.py::apply`][upstream-strawberry-pagination] slices a root
queryset as `[offset:offset + limit]`, while
[`strawberry_django/pagination.py::apply_window_pagination`][upstream-strawberry-pagination]
expresses the same bounds with `RowNumber` for nested prefetches. The root arithmetic is the
part borrowed. Its silent max-limit clamp, negative-limit unbounded spelling, generated
result envelope, decorator surface, and nested raw-list window are refused (*why each was
declined: see the [rationale][rationale-borrowing]*). This package has a fail-closed resource
policy, a Meta-class public API, and connections for nested windows.

### From this package - reuse the connection signature proof, not its page rules

[`django_strawberry_framework/connection.py::_synthesized_signature`][connection] proves
that Strawberry will publish Meta-derived lazy sidecar inputs from a wrapper's assigned
`__signature__` and `__annotations__`. The list field borrows that mechanism and the
`order_input_type` call. It does not import the connection's filter input, total-order
tiebreaker, cursor codec, [`ConnectionExtension`][connection], or page-size rules (*see the
[rationale][rationale-borrowing]*).

## User-facing API

The consumer declaration stays Meta-first. Its existing
[`Meta.model`][glossary-metamodel] and [`Meta.fields`][glossary-metafields] keys keep their
shipped meanings:

```python
class BranchOrder(OrderSet):
    class Meta:
        model = Branch
        fields = ("id", "name", "city")


class BranchType(DjangoType):
    class Meta:
        model = Branch
        fields = ("id", "name", "city")
        orderset_class = BranchOrder


@strawberry.type
class Query:
    branches: list[BranchType] = DjangoListField(BranchType, max_rows=50)
```

With the default [`strawberry_config()`][glossary-strawberry_config] name converter, its SDL
is:

```graphql
type Query {
  branches(offset: Int = null, limit: Int = null, orderBy: [BranchOrderInputType!] = null): [BranchType!]!
}
```

A target without `Meta.orderset_class` publishes only `offset` and `limit`. With
`auto_camel_case=False`, the Python `order_by` parameter renders as `order_by`; a custom
Strawberry name converter may rename all three arguments. The examples in this document use
the default spelling, while runtime error payloads always report the active schema spelling.
This is the one
necessary qualification to the card body's "three arguments on every field" sentence:
GraphQL arguments require a concrete input type, and the package has deliberately refused
both untyped JSON ordering and automatic `OrderSet` generation. Publishing a dummy or
always-rejected `orderBy` would make SDL introspection lie. Slice 5 amends that Scope
sentence in the card rather than leaving the board demanding a different surface.

`offset` is published universally, and that has an honest cost this spec states rather than
buries. On a target with neither `Meta.orderset_class` nor still-effective model
`Meta.ordering`, `offset: 0` is accepted and every positive value fails `order_required`,
permanently. The capability rule chosen for `0.0.15` is therefore **publish the coordinate
universally and gate it at runtime**: a published `offset` is a runtime-precondition
argument, not a claim that the field can page. Decision 2 records the two rejected
alternatives. The field docstring, the glossary entry, and the migration note must each say
so in those terms, and the acceptance suite pins both shapes - a target with no order source,
where positive offset is always rejected, and a target with stable model `Meta.ordering` and
no `OrderSet`, where offset is usable without `orderBy` ever being published.

The client shape is direct:

```graphql
{
  branches(
    offset: 20
    limit: 10
    orderBy: [
      {
        name: ASC
      }
      {
        id: ASC
      }
    ]
  ) {
    id
    name
  }
}
```

`offset: 0` is valid and WINDOW-identical to omission - the same rows in the same order -
but it is not MODE-identical. Any non-null argument, `offset: 0` and `limit: 0` and
`orderBy: []` included, selects the argument-bearing pipeline, whose source seal rejects a
combined queryset that the omitted/all-null legacy branch still accepts (Decision 5). The
identity claim therefore holds for ordinary composable querysets and for every non-queryset
source, and fails exactly on a combined source; `limit` equal to the effective ceiling is
window-identical on the same terms. `limit: 0` is valid and the pagination seam consumes or
fetches no row from a lazy queryset/iterator; work a consumer resolver already performed to
build a materialized list cannot be undone. The operation must also pass the independent
pre-execution document budget before the field runs. `null` and omission are equivalent for
all three arguments. The consumer `resolver=` is still invoked as `resolver(root, info)`;
the wrapper owns the new arguments and does not forward them into a consumer function. An
async consumer return is awaited exactly once; residual awaitables fail closed rather than
being recursively awaited.

## Caps and error table

Let `P = info`'s `ResourcePolicy.max_list_rows`, `F = max_rows`, and
`T = trusted_max_rows`.

| Quantity | Effective ceiling | Accepted values | Rejection |
|---|---|---|---|
| Returned rows, no client `limit` | `F` when `T` and `F` is set; otherwise `min(P, F)` when `F` is set; otherwise `P` | Derived, always positive | Existing [`ConfigurationError`][glossary-configurationerror] validation owns invalid declarations. |
| Client `limit` | The same effective returned-row ceiling | GraphQL `Int` coercing to `0..ceiling`, or null/omitted | Negative or over ceiling: `ListArgumentError`; other values follow standard GraphQL `Int` coercion. |
| Client `offset` | `P`, regardless of trusted field widening | GraphQL `Int` coercing to `0..P`, or null/omitted | Negative or over `P`: `ListArgumentError`; other values follow standard GraphQL `Int` coercion. |
| Result window | `[offset:offset + limit]`; omitted limit uses the effective returned-row ceiling | At most the effective returned-row ceiling | No clamp after validation. |

`trusted_max_rows` keeps exactly its shipped meaning for returned rows. It does not become a
trusted skip declaration: a field may deliberately return more than the request policy but
may not force the database to discard an arbitrarily large prefix. That asymmetry keeps the
existing opt-in unchanged while bounding the new cost this card introduces.

Runtime package rejections use one internal type:

```python
class ListArgumentError(GraphQLError, DjangoStrawberryFrameworkError):
    ...
```

The declaration carries no `# noqa: N818`, and adding one is a lint error rather than a
harmless precaution. N818 fires only on an exception name that does not end in `Error`, which
is why the
[`django_strawberry_framework/resource_policy.py::ResourceLimitExceeded`][resource-policy]
precedent must suppress it; `ListArgumentError` already ends in `Error`, so the suppression
would be unused and `RUF100`, which [`pyproject.toml`][pyproject] selects through its `RUF`
block, would reject the file. The precedent this class inherits is the dual-base shape and the
pickle contract, not the neighbour's noqa comment.

Like that same precedent and the package's other dual-base errors, the concrete class defines
`__reduce__` to preserve its constructor arguments and instance state across pickle round
trips; default pickling is not trusted across the `GraphQLError` plus package-error
inheritance shape. The reduce tuple matches the shipped shape exactly: the class, the complete
constructor argument list, and `self.__dict__`. `extensions` is a `GraphQLError` slot rather
than an instance-dictionary entry, so it is rebuilt by the reconstructing `__init__` from those
arguments rather than carried in the state mapping; a variant that pickles only the message and
restores `extensions` through state round-trips too, but duplicates the constructor's own
derivation and is not the precedent.

`ListArgumentError` is PUBLIC and catchable, exported from
[`django_strawberry_framework/__init__.py`][package-init] beside `ResourceLimitExceeded` and
`SyncMisuseError`. Calling it internal while giving it a stable name, a glossary entry, a
pickle contract, and a documented `extensions` payload would be incoherent, because every one
of those only matters to someone who can name the class. A consumer writing a custom view, an
error formatter, or middleware that separates an invalid page request from a genuine failure
needs `except ListArgumentError`, and directing them to string-match `extensions["code"]`
instead would be a weaker contract than the two shipped precedents already offer. Slice 1
therefore adds the import and the `__all__` entry and updates the pinned `__all__` tuple in
[`tests/base/test_init.py`][test-base-init], together with that file's star-import and
export-identity rows and the stale comment there asserting that the `0.0.15` cut leaves the
public surface unchanged. That is the `__all__` assertion in that file and is unrelated to its
VERSION assertion, which stays with card 053's joint cut (see Version boundary). The supported
catch surface is therefore `ListArgumentError` itself, its `GraphQLError` base, or
`extensions["code"] == "LIST_ARGUMENT_INVALID"` - all three deliberately. The package's
`DjangoStrawberryFrameworkError` base is a second base rather than a supported root import;
this card does not export it.

Its `extensions` are stable:

```json
{
  "code": "LIST_ARGUMENT_INVALID",
  "argument": "offset",
  "reason": "over_ceiling",
  "ceiling": 100,
  "value": 101
}
```

For numeric-domain failures, `reason` is `negative` or `over_ceiling`; both carry `value`
and only the latter carries `ceiling`. A direct Python call that bypasses GraphQL coercion
uses `non_integer` and a safe string value rendered by
[`django_strawberry_framework/exceptions.py::describe_value`][exceptions].
`order_required` carries the rejected offset as `value`. The source-shape reason
`queryset_required` carries neither `value` nor `ceiling`, because serializing an order input
is not a stable wire contract. Pre-sliced querysets remain the shared sealed visibility
boundary's existing `ConfigurationError`, not a second list-field classification.
`argument` always uses the active schema's GraphQL wire spelling. The wrapper starts from the
Python parameter name (`offset`, `limit`, or `order_by`), obtains its Strawberry argument
definition from
[`strawberry/types/info.py::Info.get_argument_definition`][strawberry-info], and passes that
definition through
[`strawberry/schema/name_converter.py::NameConverter.from_argument`][strawberry-name-converter]
on the active schema config. A direct helper call without a real schema falls back to the
default spelling (`offset`, `limit`, or `orderBy`) and tests identify that fallback
explicitly. The wire message names the
field, argument, requested value when the payload carries one, and the accepted contract. A
string, boolean, out-of-range integer, non-integral/non-finite float variable, or float
literal never reaches this constructor: GraphQL declares both numeric arguments as `Int`, so
graphql-core rejects the operation during validation/coercion with a `GraphQLError`.
[`graphql/type/scalars.py::coerce_int`][graphql-scalars] in graphql-core 3.2.8 deliberately
accepts a finite integral-valued float variable such as `1.0` and delivers the integer `1` to
the resolver; the acceptance suite pins that upstream contract instead of falsely promising
origin-type rejection after coercion. Replacing `Int` with a stricter custom scalar merely
to attach the package code would change the requested SDL and is rejected.

## Architectural decisions

### Decision 1 — synthesize one resolver signature; do not widen consumer resolvers

`DjangoListField` gains a private signature builder parallel in mechanism to
[`django_strawberry_framework/connection.py::_synthesized_signature`][connection]. It
starts with the same reserved `root` positional parameter and keyword-only `info: Info`,
then always adds keyword-only `offset: int | None = None` and `limit: int | None = None`.
It conditionally adds `order_by: list[order_input_type(...)] | None = None` when the target
definition has `orderset_class`. Strawberry's active schema converter maps those Python
names to wire names; the default converter produces `offset`, `limit`, and `orderBy`, while
`auto_camel_case=False` produces `order_by` and a custom converter may rename any argument.
Assigning both `__signature__` and `__annotations__` is mandatory because Strawberry
inspects the callable once during schema construction. The executable wrapper accepts the
generated keywords (through an explicit `**kwargs` intake or equivalent named parameters),
pops them itself, and calls a consumer resolver with only `(root, info)`; changing
`__signature__` alone does not change Python's call acceptance.

Unlike the connection builder, the list signature does not install its own return
annotation: the synthesized signature keeps `inspect.Signature.empty` and the assigned
annotation map omits `return`. The consumer's class-attribute annotation remains the single owner of
`list[T]` versus `list[T] | None`; synthesizing `list[target_type]` here would silently
erase the shipped nullable-outer spelling even though this card changes only arguments.

The wrapper, not the consumer resolver, consumes all three arguments. Existing consumers
continue to implement `resolver(root, info)`. *Alternatives rejected: see the
[rationale][rationale-d1] (forwarding arguments to consumer resolvers, inspecting consumer
signatures).*

The signature builder calls
[`django_strawberry_framework/orders/__init__.py::order_input_type`][orders-init] with
`definition.orderset_class` rather than constructing an annotation itself. That call is
load-bearing: it registers the helper reference in the shipped orphan ledger and ensures
[finalization][glossary-finalize_django_types] materializes the same input class a
hand-written resolver or connection uses.
The import stays inside the signature builder, mirroring the connection implementation;
that module is imported from the package root, so a module-level `.orders` import would
break the shipped [lazy-subpackage contract][glossary-pep-562-lazy-export] even for
consumers that never construct an order-capable field.

The builder is parallel code, not an import from
[`django_strawberry_framework/connection.py::_synthesized_signature`][connection]: the
connection module already imports the shared DjangoType target guards from
[`django_strawberry_framework/list_field.py::_validate_relay_djangotype_target`][list-field], so
reversing that edge would close a module cycle. A neutral parameter-construction helper is
extractable only if it is genuinely smaller and lives below both modules; the list field
never imports the connection module merely to avoid a few `inspect.Parameter` calls.

### Decision 2 — sidecar-conditional `orderBy` is the only truthful Meta-first surface

The card asks for three optional arguments on every `DjangoListField`, but its same Scope
section says ordering comes from the target's `orderset_class`. Those requirements cannot
both hold for a type without that sidecar. This spec resolves the collision in favor of the
package's DRF-first public API and [`spec-028`][spec-028] Decision 12: `offset` and `limit`
are universal; `orderBy` is present exactly when `Meta.orderset_class` supplies its type and
semantics.

*Alternatives rejected: see the [rationale][rationale-d2] (auto-generating OrderSets, JSON
argument, dummy input, mandatory orderset_class, conditional offset publication).*

The card body's universal-three-argument sentence is amended by this card rather than
reinterpreted around it: Slice 5 rewrites that Scope bullet in the KANBAN database to state
that `offset` and `limit` are universal, `orderBy` is sidecar-conditional, and a published
`offset` is a runtime-precondition coordinate. This qualification is recorded again under
Risks so implementation review cannot mistake it for an accidental omission.

### Decision 3 — one validation record computes both window and errors

A private immutable normalized-arguments record holds `offset`, `limit`,
`effective_ceiling`, the order input, and whether that input was supplied. Material
order activity comes from the `OrderSet`-owned
`_input_has_active_terms(input_value) -> bool` helper, not a list-field input walker. One
list-argument normalizer runs after `info` is available and before any queryset slicing. It
treats `None` and `strawberry.UNSET` as omission, rejects `bool` explicitly despite Python's
`bool < int` relationship, and performs the cap checks in the table above. It validates
`offset` before `limit`, matching the synthesized signature and SDL order, so a direct call
with both values invalid has one deterministic first failure.

The record answers four separate questions with four separate fields, and no consumer of one
may read another as a proxy for it. `any_argument_supplied` is true when any of the three
arrived non-null; it selects the argument-bearing pipeline and nothing else, which is also
what turns on reject-combined source admissibility. The `window` fields (`offset`, `limit`,
`effective_ceiling`) say which rows are returned, and `offset: 0` with an omitted limit
produces the same window as omission - which is why Decision 9's fast path is a MODE decision
and never a window comparison. `order_by_supplied` says whether an order argument arrived at
all, and it, never material activity, drives the `queryset_required` source check, because an
empty list is still a supplied order argument. Material order activity is the fourth question
and is answered only after public apply succeeds. Collapsing any pair of these into one bit is
precisely what makes `offset: 0` look identical to omission while behaving differently, so the
record keeps them apart by construction and the package tier pins each field's independent
effect.

Argument wire names are resolved LAZILY, only while constructing a `ListArgumentError`. A
successful request must perform zero name conversions.
[`strawberry/schema/name_converter.py::NameConverter.from_argument`][strawberry-name-converter]
is a consumer-supplied hook on custom-converter schemas, normally exercised once per argument
during schema construction; calling it on every resolver invocation would add redundant
per-request work and would invoke a shared, possibly stateful consumer object concurrently at
runtime, where a non-deterministic converter could report a spelling the already-built schema
does not use. The error constructor is therefore its only caller, and a package test asserts
an instrumented converter records zero runtime calls across a batch of successful
argument-bearing requests and exactly one on a rejection. Converters are still required to be
deterministic; laziness narrows where that requirement has to hold rather than replacing it.

The record lives in [`django_strawberry_framework/list_field.py`][list-field], the argument
owner. The shared resource-policy module does not import a list-field type (which would
reverse the existing dependency and create a cycle); the wrapper passes only validated
`offset` / `limit` scalars into the extended bounding helpers. Their signatures retain the
existing positional-or-keyword third parameter `declared` so every shipped positional call
continues to bind identically; the new `offset` and `requested_limit` parameters are
keyword-only after `declared`, alongside the existing keyword-only `trusted` option. Those
helpers still call the one `effective_bound` implementation when they build the final slice.

Extending these two helpers also inherits the request deadline, which this card must not
relocate or duplicate. Both raw-list spellings reach `effective_bound` through the shared
[`django_strawberry_framework/resource_policy.py::_raw_list_bound`][resource-policy] helper,
whose first statement is `check_deadline(info)` - the documented "last look at the clock
before rows are fetched", and the reason `ResourcePolicy.execution_deadline_seconds` names
`bounded_rows` (both spellings) among its cooperative seams. Routing the client `offset` /
`limit` through the same helpers therefore keeps one deadline check in the same position
relative to row fetching. The list field must not add a second `check_deadline` call of its
own, and the window arithmetic must not move ahead of that one: an argument-bearing request
gets the same clock behavior as a bare one. The pre-bound rejection paths in Decision 8 hand
no work to the database and correctly reach no deadline check at all.

The client coordinate handed to the bounding helper is a distinct `requested_limit`
parameter; it must not be routed through the existing positive-only field-declaration
validator. `limit=0` is a valid client coordinate while `max_rows=0` remains an invalid
schema declaration. The effective returned-row ceiling comes from the existing
[`django_strawberry_framework/resource_policy.py::effective_bound`][resource-policy]; no
second `min(policy, field)` implementation is allowed. Validation rejects
`limit > effective_ceiling` before constructing the window. The subsequent minimum is
therefore mathematically the client value when supplied and the effective ceiling when
omitted. This satisfies the card's minimum rule without a silent clamp: a client can ask
for less, never more.

### Decision 4 — `max_list_rows` also bounds skip; trusted widening does not

The maximum accepted offset is the request's `max_list_rows`. *Alternatives rejected: see the
[rationale][rationale-d4] (a dedicated max_list_offset setting).*

`trusted_max_rows` is deliberately not consulted for offset. It states that a schema author
trusts a field to return more rows; it says nothing about the cost of making the database
discard rows. Treating it as both declarations would widen a new resource dimension under
an old option without consumer consent.

An offset greater than the result set is valid when it is within the policy ceiling and
returns an empty list. It is not an error: the request stayed inside the accepted
coordinate ceiling, and concurrent deletes can make any previously valid page overshoot.

Skip and return ceilings are independent dimensions. The request may therefore have
`offset + effective_limit > max_list_rows`; the maximum untrusted endpoint is twice the
policy value, while each of the two kinds of work remains separately bounded. Trusted field
widening can raise the return half but never the skip half. *Why requiring the sum to fit
under max_list_rows and single scan budgets were rejected: see the [rationale][rationale-d4].*

Accordingly, `max_list_rows` retains a returned/materialized-row meaning on the return
dimension and is reused as a separate accepted-skip ceiling. Both are ACCEPTED COORDINATE
CEILINGS, not scan budgets: they bound what a client may ask for, never what the backend plan
does to satisfy it. This spec therefore says "accepted coordinate ceiling" rather than "work
budget" for both dimensions, and the `ResourcePolicy`, `bounded_rows`, and
`bounded_rows_async` docstrings are updated in this card so "evaluate" cannot be read as a
total scan guarantee. *Derivation: see the [rationale][rationale-d4].*

The pre-execution collection-cost walker keeps its shipped charge unchanged: a raw list costs
`ResourcePolicy.max_list_rows` whatever the operation supplies. That charge is a
SCHEMA-GENERIC FIXED ESTIMATE. Runtime row fetch and serialization still honor the smaller
client limit. *Derivation of the fixed estimate and why argument-name matching was rejected:
see the [rationale][rationale-d4].*

### Decision 5 — validate, then visibility, ordering, and exactly one slice

For a request carrying any non-null list argument, the color-specific queryset pipeline is:

1. Derive the active wire names and validate/normalize `offset` / `limit` from `info` before
   invoking a consumer resolver.
2. Invoke the default or consumer resolver and normalize a `Manager` to a `QuerySet`.
   Preserve the existing guards: a sync resolver returning an awaitable is disposed and
   rejected, while an async resolver is awaited once and a residual awaitable is disposed
   and rejected rather than recursively awaited.
3. Apply the target's `get_queryset` visibility hook through the shared sealed boundary. Its
   source seal rejects an already-sliced queryset before the consumer hook runs, and its
   result seal rejects a hook-returned sliced queryset before later ordering or pagination.
   In the argument-bearing mode, the same source/result seal also rejects a combined queryset
   (`union`, `intersection`, or `difference`) with `ConfigurationError`: source rejection
   occurs before invoking a hook that may illegally filter the combination; result rejection
   occurs before OrderSet/optimizer operations. The all-null/omitted fast path keeps the
   existing combined-query behavior. The caller selects the `reject_combined` seal option,
   which already ships on
   [`django_strawberry_framework/utils/querysets.py::_SealPolicy`][querysets] and emits the
   `combined` defect inside `_seal_or_defect` as part of the existing pre-clone and post-bake
   `_combined_query_table_defect` proof passes, not by a list-field pre-check. The seal is a
   rebuild boundary whose complete combined-branch proof runs twice when deferred filters are
   baked, so argument mode must not weaken it into a one-off validator.

   The option exists but has never been reachable from this boundary, and that is the card's
   actual work here. `combined` is set today only by `_CASCADE_SEAL_POLICY`, and the cascade
   always supplies its own `render_error`, so the code's two visibility message sites render
   every defect EXCEPT `combined` - a reachability invariant
   [`django_strawberry_framework/utils/querysets.py::_visibility_result_error`][querysets]
   states outright in its own docstring. Selecting `reject_combined` for list-field
   visibility makes `combined` reachable at both sites for the first time, so this card owes
   a `combined` arm at each of them and a correction to that docstring's reachability
   sentence, exactly as the new `unevaluated` code below owes its own arms. Without them the
   rejection still fails closed - `_defect_message` dispatches exhaustively and an unrendered
   code names itself as a framework defect - but the schema author is told a code is
   unhandled instead of being told their source is a `union` / `intersection` / `difference`.
4. If supplied, run the canonical public `OrderSet.apply_sync` / `apply_async` path. The
   async wrapper calls `apply_async` without assuming that an override retained `async def`:
   a non-awaitable return is a schema-author defect and raises the same actionable
   `ConfigurationError` naming `OrderSet.apply_async`; an awaitable is awaited exactly once,
   and a residual awaitable is disposed and rejected rather than recursively awaited.
   Validate the resulting value before consulting active order state through the shared
   queryset sealing machinery, with surface-specific error text and an added
   require-unevaluated option. The requirement is on the SEALED OUTPUT, never on the
   candidate's class. The shared seal accepts a sealable `QuerySet` SUBCLASS and rebuilds it
   into a framework-owned plain `models.QuerySet` - a central architectural feature of that
   boundary, not an accident, and not narrowed here. A custom `OrderSet.apply_*` returning a
   project's own `QuerySet` subclass is therefore accepted, and what the pipeline carries
   forward is the plain sealed rebuild rather than the subclass itself. That sealed output
   must be unevaluated, unsliced, non-projection, non-combined, and over the same model and
   concrete table, preserving the input's effective database routing. A `Manager`, list,
   `None`, wrong-model queryset, values/values-list queryset, populated `_result_cache`, or
   malformed query state is a schema-author defect and raises an actionable
   `ConfigurationError` naming the public apply method. The one subclass that still fails is
   the seal's shipped rule rather than a new one: a subclass carrying an unresolved
   `_deferred_filter` cannot be safely baked and fails closed as `untrusted`. A sync-path
   awaitable is likewise disposed and rejected under the existing one-await policy. Like
   `reject_combined`, the require-unevaluated option is enforced inside
   [`django_strawberry_framework/utils/querysets.py::_seal_or_defect`][querysets] and is a new
   defect rather than a reuse of an existing code: the seal is a rebuild boundary that never
   copies `_result_cache`, so today an evaluated candidate is silently normalized into a fresh
   unevaluated queryset - an override that ran its own SQL and returned rows would be turned
   into a second identical query instead of rejected. Both options default off, so no shipped
   seal verdict changes.

   A new code owes two things the shipped codes already have. First, a fixed position in the
   seal's documented canonical ordering, which today runs `type`, `table`, `untrusted`,
   `sliced`, `combined`, `projection`, `alias`. `unevaluated` is taken immediately before
   `sliced` so the trust-family proofs still run first and the two execution-state rejections
   sit together. Decision 13's routing check is the third new code and takes the position
   immediately after `untrusted`, so every trust-family proof still runs first and no
   reconstructed queryset is returned before routing intent is proven, making the shipped
   order `type`, `table`, `untrusted`, `routing`, `unevaluated`, `sliced`, `combined`,
   `projection`, `alias`. Second, its own arm at both message-building
   sites,
   [`django_strawberry_framework/utils/querysets.py::_visibility_result_error`][querysets] and
   [`django_strawberry_framework/utils/querysets.py::_prepared_visibility_source`][querysets],
   each of which renders only the subset it can reach. Those ladders no longer end in an
   unconditional branch for their last code - `_defect_message` dispatches exhaustively, so a
   code added without an arm self-names as a framework defect rather than mislabelling an
   evaluated-result rejection as an alias mismatch or a wrong-table error. The failure is
   therefore legible rather than silent, but an unarmed code still reaches the schema author
   as an unactionable message, so both new codes owe both arms. The retained-state
   helper `_queryset_state_defect` is not its home: that helper pins the `QuerySet.__dict__`
   fields the seal carries forward (`_db`, `_hints`, `_fields`, `_sticky_filter`, `_for_write`)
   and emits only `untrusted`, and `_result_cache` is not among them.

   Same-route needs its own definition, because `_db` equality alone is not it. Django
   resolves an unrouted queryset's alias through the database router using both the model and
   `_hints`, so two querysets can each carry `_db is None` and still resolve to different
   databases when their hints differ - and the seal preserves whatever hints the candidate
   carried, copying them into the rebuild. The enforced invariant is therefore ROUTING INTENT:
   the post-apply candidate's `_db` equals the pre-order sealed source's `_db`, `None`
   included, AND its `_hints` mapping equals that source's. Intent equality is stricter,
   deterministic, and dispatches no consumer code (*alternatives rejected: see the
   [rationale][rationale-d5]*). The shipped
   seal already compares `_db` against a required alias and already proves `_hints` is `None`
   or an exact `dict`, so this is one added comparison at an already-proven-shape site rather
   than a new state read. The sharded live suite covers the unrouted/hint-driven mismatch as
   well as `.using("default")` versus `.using("shard_b")`; explicit-alias cases alone would
   leave the hint half of the invariant unpinned.
5. Ask that same `OrderSet` implementation whether its normalized input contains an active
   term, then enforce the nonzero-offset ordering precondition.
6. Apply one combined raw-list window.
7. Return the lazy result for the existing
   [`DjangoOptimizerExtension`][glossary-djangooptimizerextension] and GraphQL completion
   path.

Visibility must precede order permissions and the page window: an order permission may use
request context, and slicing before visibility is both a data leak and illegal to refilter
in Django. Ordering must precede slicing so the page coordinates refer to the ordered set.
The window stays last so queryset SQL receives one `LIMIT/OFFSET` pair and no intermediate
query is evaluated. Scalar/cap validation runs first because it needs no source and an
invalid package-owned argument must not invoke a consumer resolver with possible side
effects.

Mechanical post-apply validation proves result shape, model/table, routing, laziness, and
slice safety. It cannot prove that arbitrary custom Python preserved the incoming `WHERE`
predicates. Overriding `OrderSet.apply_sync` or `apply_async` is therefore an explicit trusted
schema-author boundary, like writing `get_queryset`: the override must derive from the
[sealed queryset][glossary-sealed-execution-queryset] it receives and preserve its
visibility predicates and routing. The base
implementation and conforming overrides retain the framework visibility guarantee; a
malicious override that discards the input and starts from a fresh manager is outside it.
The tests prove conforming delegation and every mechanically enforceable violation rather
than claiming to authenticate arbitrary consumer code.

This third seal is not a cheap `isinstance` guard. The cost of a third full walk and rebuild
is accepted (*derivation: see the [rationale][rationale-d5]*). Slice 3 benchmarks the
post-apply seal on at least a complex annotated query, a to-many aggregate order, and a
queryset carrying prefetch metadata, and the numbers are recorded at card close. A fast path
is not adopted on intuition: it requires that evidence, and until then the full seal stays for
every overridable public method. What the list field must not do under any circumstance is
duplicate the seal's state reads locally in order to skip it.

The implementation extends
[`django_strawberry_framework/resource_policy.py::bounded_rows`][resource-policy] and its
[`django_strawberry_framework/resource_policy.py::bounded_rows_async`][resource-policy]
sibling with optional validated `offset` / `limit` values rather than slicing locally in
[`django_strawberry_framework/list_field.py`][list-field]. `bounded_rows` remains the one
raw-list bound for root and relation lists; callers without client arguments take its exact
existing branch. *Alternatives rejected: see the [rationale][rationale-d5] (a fresh
pagination helper).*

Async queryset completion needs one additional representation boundary.
[`graphql/execution/execute.py::ExecutionContext.complete_list_value`][graphql-execute]
checks synchronous `Iterable` before `AsyncIterable`, while Django querysets implement both;
returning a queryset directly from `AsyncDjangoGraphQLView` therefore invokes synchronous ORM
iteration inside the event loop. After the final slice, the async list path wraps a queryset
in a package-internal
[async-only queryset-row adapter][glossary-async-queryset-completion-adapter] whose
`__aiter__` delegates to Django's safe
[`django/db/models/query.py::QuerySet.__aiter__`][django-queryset] iteration. The adapter is
not a public collection type, and it deliberately does not implement `__iter__`: a synchronous
iterator on it would put it straight back on the branch this boundary exists to leave.

[`DjangoOptimizerExtension`][glossary-djangooptimizerextension] recognizes it, applies the
root plan to its inner final sliced queryset, and rewraps the optimized queryset; without the
optimizer the same adapter still completes safely. Thus optimization sees the low/high marks
and async HTTP tests require no `DJANGO_ALLOW_ASYNC_UNSAFE` escape hatch.

That recognition has one exact seam, and naming it is load-bearing because the failure mode is
silent. The unwrap/rewrap arm belongs in
[`django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension._optimize`][optimizer-extension],
ahead of that method's documented step 1, so its `normalize_query_source` coercion, its
evaluated-queryset guard, and its return-type resolution all read the inner queryset rather
than the wrapper. An adapter reaching an unmodified `_optimize` instead takes that method's
documented step 2, where a non-`QuerySet` result passes through unchanged: every row and every
SQL assertion still succeeds while root-list optimization is silently gone, which is why the
package tier pins the unwrap identity and the inner queryset's low/high marks rather than only
asserting the response.

Rewrapping is an obligation of every return path out of `_optimize`, not only the optimized
tail. That method also returns early and unchanged on an already-evaluated queryset and again
when the return type resolves to no registered [`DjangoType`][glossary-djangotype]; both paths
are reachable for an argument-bearing async list, and each would hand graphql-core the bare
inner queryset - the synchronous-`Iterable` completion this adapter exists to prevent - if only
the plan-applying tail rewrapped. The arm therefore wraps whatever `_optimize` returns for an
adapter input, and the package tier asserts the wrapper survives both early returns, not just
the optimized one. The sibling
[`django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension.resolve`][optimizer-extension]
already awaits an async resolver result before calling `_optimize`, so the arm needs no second
async branch of its own.

The adapter exists precisely to keep the final sliced queryset lazy across the resolver
boundary; a package test pins that the optimizer still reaches the inner queryset.
*Alternatives rejected: see the [rationale][rationale-d5] (in-coroutine list materialization
via many_resolver).* Sync execution, materialized values, `None`, and genuine async-only
consumer sources retain their existing result shapes. Adapter selection keys off the runtime
execution context for every final queryset, including a plain `def` consumer returning a
`Manager`/`QuerySet` under an async view; it does not change the shipped callable-color rule
for whether a consumer or visibility hook is awaited.

The safety claim is scoped to FRAMEWORK-OWNED FINAL QUERYSET COMPLETION and must be written
that way everywhere it appears. The adapter removes the one iteration the framework itself
hands to graphql-core. It cannot stop a plain `def` consumer resolver or a synchronous
`get_queryset` hook from calling `list(qs)`, `.exists()`, `.count()`, or any other synchronous
ORM method while already running on the event-loop thread, and this card deliberately
preserves the shipped callable-color behavior for those hooks. The async acceptance suite
accordingly exercises a CONFORMING lazy sync resolver - one that returns a queryset without
evaluating it - and never implies that an evaluating sync resolver is made safe by the
adapter's presence.

### Decision 6 — nonzero offset requires a materially active order

`offset > 0` succeeds only when at least one of these is true on the post-visibility
queryset:

- a supplied `orderBy` contains at least one non-null `Ordering` leaf that survives
  `OrderSet` normalization and the validated post-apply queryset reports an effective SQL
  order with no recognized random term; or
- the target model declares non-empty `Meta.ordering` that is not random ordering, and the
  sealed queryset still has that default ordering materially enabled.

`orderBy: []` and `orderBy: [{ name: null }]` are no-ops under the shipped order contract
and therefore do not satisfy the explicit-order branch. They do not disable the independent
model-default branch: an actually effective stable `Meta.ordering` may still satisfy the
guard. Merely declaring `Meta.orderset_class` is not an order. A resolver-returned queryset
carrying ad hoc `.order_by(...)` does not satisfy the model-default branch: the card
specifically makes the page's order contract VISIBLE through `orderBy` or model metadata, and
hidden resolver order alone cannot explain why one otherwise-identical field accepts offset
and another rejects it. When active input is supplied, the public `OrderSet.apply_*` contract
requires a custom override to honor it; mechanical validation can prove that the returned
queryset is ordered but cannot prove which arbitrary Python statements produced that order,
the same trusted-override limitation Decision 5 records for visibility lineage.

The model declaration is not enough when the actual query has stopped using it. After
visibility, the plain sealed queryset must report ordered through Django's default-ordering
path: default ordering remains enabled, no explicit or extra ordering has replaced it, and a
grouping shape has not suppressed it. A consumer resolver or `get_queryset` hook that calls
`.order_by()` clears the model default; one that installs a private explicit order replaces
it. Neither can cite `Meta.ordering` as the public offset guarantee. This state is read only
after the visibility boundary has rebuilt a framework-owned plain queryset, so the list
field does not inspect hostile consumer queryset internals or create another source
classifier.

Two named predicates keep these branches separate. The post-apply explicit-order check
accepts an active normalized input only when its mechanically validated queryset is ordered
and its effective terms contain no recognized random order; an explicitly ordered,
known-empty `.none()` queryset may satisfy this branch vacuously because the client-visible
order contract still exists. The model-default predicate is Django's own default-ordering rule
plus a stability requirement, not a parallel reimplementation of it. It requires all of:
non-empty stable ordering on the query's own meta, `query.default_ordering is True`, empty
`query.order_by`, and empty `query.extra_order_by` - and then Django's grouping rule spelled
exactly as
[`django/db/models/query.py::QuerySet.ordered`][django-queryset] spells it, `not
query.group_by`. That last condition is written as a falsiness test, never as
`query.group_by is None`: `group_by` is `None` on a plain query but a tuple of expressions
once a `values().annotate()` grouping exists, and Django itself builds it through
`tuple(...)`, so an identity test against `None` would reject a queryset Django considers
ordered the moment that tuple is empty. Reading the query's meta rather than
`model._meta` directly matches the same upstream property and keeps inherited and proxy
models on one rule.

The predicate never uses `QuerySet.ordered` alone, because that property short-circuits
`True` for an `EmptyQuerySet` regardless of ordering - a `Branch.objects.none()` on a model
declaring no `Meta.ordering` reports ordered. `query.standard_ordering is False` is not a
rejection: `.reverse()` simply reverses the deterministic model terms and remains a valid
visible order. Package tests pin both empty queryset branches and reversed stable/random
defaults.

Django permits `Meta.ordering = ("?",)` and expression-based random ordering. Those terms
are active SQL ordering but cannot make an offset page repeatable, so a literal `"?"` or a
recognized Django `Random()` expression does not satisfy the guard, alone or mixed with
other terms, whether they came from model metadata or a custom apply override. The exact
string is `"?"` and only `"?"`. The comparison lives in
[`django/db/models/sql/compiler.py::SQLCompiler._order_by_pairs`][django-compiler], the
generator that `SQLCompiler.get_order_by` consumes, and it tests `field == "?"` exactly, so a
descending spelling such as `"-?"` is not a random order at all - Django resolves it as a
column named `?` and raises `FieldError`. The implementation must not carry a `"-?"` arm; a
term that is not exactly `"?"` and not a recognized `Random()` expression is either an ordinary
field order or already a hard Django error. The shared
post-apply seal rejects consumer-defined expression classes as untrusted query state. For
other genuine Django expression compositions that pass the seal, volatility beyond the
recognized `Random()` form remains the schema author's responsibility under Decision 7's
deliberately weaker-than-total-order contract; the list field does not attempt to
reverse-engineer arbitrary SQL. The shipped `OrderSet` input itself emits only declared field
orders.

Django model default ordering may traverse a to-many relation and duplicate parent model
instances. This card preserves that documented ORM result-row behavior: offset counts SQL
result rows, not distinct parent identities, and no `DISTINCT` is injected. A consumer that
requires one row per parent uses an aggregate `OrderSet` term (the shipped `Min`/`Max`
behavior) or a connection rather than relying on a to-many `Meta.ordering` fallback.

The rejection is
`ListArgumentError(argument=<active offset wire name>, reason="order_required")`, with the
same stable code and no ceiling. Offset zero never requires ordering. Omitted offset does not
require ordering even when a limit is supplied.

*Alternatives rejected: see the [rationale][rationale-d6] (unordered offset as shipped in
Graphene-Django, primary-key tiebreaker injection as shipped in
Strawberry-GraphQL-Django).*

### Decision 7 — active order is not total order; no pk tiebreaker is appended

An active `orderBy` or `Meta.ordering` may contain ties. The list field preserves the exact
declared terms and does not append primary key. This is intentionally weaker than
`DjangoConnectionField`, whose positional cursor contract requires a deterministic total order
and obtains one in
[`django_strawberry_framework/connection.py::_finalize_queryset`][connection].

That gap is a contract limit, and it is named here once so the rest of this document, the
docstring, the glossary, and the tests can use the same words for it. What this card delivers
is **ordered offset**: the skip is counted over an order the client can see and reason about.
It is NOT stable or repeatable pagination. Ordering by `city` alone is a deterministic
ordering EXPRESSION, but it does not determine which of two tied rows falls on either side of
an offset boundary; a database may return tied rows in either order between equivalent
executions, and no concurrent write is required for that. Concurrent inserts and deletes make
the problem worse but are not its cause. Nothing in this spec, the field docstring, the
glossary entry, or the error text may promise a stable or repeatable page, and Slice 5 sweeps
the shipped docs for that wording rather than only adding new sentences beside it.

Keeping the active-order guard while declining the stronger promise is the card's stated minimal
shape, and it makes a unique final term a CONSUMER obligation the framework documents and does
not enforce. *Alternatives rejected: see the [rationale][rationale-d7] (requiring a provably
total order, appending a deterministic terminal pk tiebreaker).*

Django 6.1 ships a `QuerySet.totally_ordered` helper covering common field cases. It is not a
portable substitute for the declared policy: the package supports Django 5.2 through latest,
and the helper cannot speak for arbitrary expressions on any version. It is named here so a
future reader does not mistake its availability for a shipped guarantee.

Consumers that page through tied values add a unique final term themselves, for example
`orderBy: [{ city: ASC }, { id: ASC }]`, or declare it in model `Meta.ordering`. The field
docstring and migration note carry that as the recommendation it is.

### Decision 8 — queryset and iterable sources have explicit, different capabilities

`limit` and zero offset work on querysets, materialized sequences, and ordinary iterables.
The public list-field pipeline permits nonzero offset only for a queryset carrying the
visible order guarantee below; an opaque Python iterable cannot establish it. Once the
single bounding seam is handed validated coordinates, a queryset receives `[start:stop]`,
a sequence receives the same slice, and a non-subscriptable iterable uses
`itertools.islice(start, stop)`. That lower-level arithmetic remains shape-complete and is
unit-pinned, but it does not widen the list field's order precondition, and the two tiers must
not be blurred: positive-offset arithmetic over an async iterator is pinned against the helper
directly in [`tests/test_resource_policy.py`][test-resource-policy], while every LIVE
async-only-source success case through the public field is limit-only or `offset: 0`, because
the field rejects positive offset there. A live case pairing an async generator with a
positive offset would contradict this decision rather than exercise it. `limit == 0`
short-circuits before any of those operations: it must not call `islice`, `__next__`, or
`__anext__`; an async source may only have its iterator acquired and optional `aclose`
invoked as part of the shared cleanup contract.

`orderBy` is a queryset operation. Supplying it when a consumer resolver returns a
non-queryset raises
`ListArgumentError(argument=<active wire name>, reason="queryset_required")` rather than silently
ignoring the argument; this applies even to an empty, otherwise-no-op list, matching the
connection sidecar guard. A nonzero offset over a non-queryset fails the active-order
precondition: model `Meta.ordering` cannot establish the ordering of an arbitrary Python
iterable. Limit-only and zero-offset requests remain valid for every iterable shape. A
nullable resolver result of `None` follows the same rule: limit/zero-offset preserve `None`,
nonzero offset requires order, and non-null `orderBy` requires a queryset.

That `None` rule is a deliberate product choice rather than an oversight of GraphQL null
propagation: argument validation is CAPABILITY validation and outranks the nullable result. A
client that always sends pagination variables can therefore turn a legitimate `null` into an
error, and that is the intended behavior. `orderBy` over a source that cannot be ordered, and
a positive `offset` over a source whose order cannot be established, are both requests the
field cannot honor; answering them with `null` would report success for a page that was never
produced. *Why short-circuiting None was rejected: see the [rationale][rationale-d8].*
Because the surprise is real, both outer annotations are pinned
live: a nullable outer list and a non-null outer list over the same `None`-returning source,
each with a limit-only request (which preserves `null`) and with a rejected argument (which
errors, propagating through whichever nullability the consumer annotation declares).

Error precedence follows the pipeline rather than incidental exception timing. Numeric
validation (`offset`, then `limit`) runs before the consumer resolver. After source
normalization, a supplied `orderBy` over a non-queryset raises `queryset_required` before a
nonzero-offset `order_required` check. On a queryset, the argument-aware source seal rejects a
combined/sliced source before invoking visibility; the hook and result seal then run;
`OrderSet` permission/application and its result validation follow; the offset guard is last
before the window. Thus an argument-bearing combined source wins over a simultaneous hook or
order-permission failure, a hook-returned combination wins before OrderSet, and malformed
post-apply output wins over offset rejection. Tests with two simultaneously-invalid
conditions pin these boundaries so later refactors cannot reverse them accidentally. This is
resolver-local precedence after GraphQL validation and the schema's pre-execution
resource-policy checks; a document-level budget rejection can necessarily stop the operation
before any field wrapper runs.

If an async-only source is rejected for supplied ordering or nonzero offset before it reaches
`bounded_rows_async`, the list pipeline obtains its iterator and invokes/awaits `aclose` when
that optional method exists without calling `__anext__`. The `ListArgumentError` remains the
primary exception; failure to obtain or close the iterator is attached as a diagnostic note.
This uses the same package-private cleanup utility and primary-error precedence as
`bounded_rows_async`, so rejection cannot leak a generator or grow a second cleanup policy.

The symmetric SYNC contract is deliberately DECLINED in this card, and declining it is stated
rather than left as an implied promise. A retained sync generator consumed through
`list(islice(generator, start, stop))` stays suspended after the accepted stop: its `finally`
block does not run until something closes or exhausts it, and CPython reference counting is
not a cross-runtime resource-management contract - it does nothing at all while the caller
keeps its own reference. *Why sync early-exit close() was rejected for 0.0.15: see the
[rationale][rationale-d8].* The Definition of done is narrowed to match: leak-free
early-exit cleanup is promised for async-only sources only. A resource-policy unit test pins
the declined behavior explicitly - a retained sync generator remains suspended and resumable
after truncation - so it is a recorded decision rather than an accident, and a later
symmetric-cleanup card can flip that test deliberately.

An already-sliced queryset stays under the shipped sealed visibility contract. Its source
seal rejects the query before invoking `get_queryset`; its result seal also rejects a hook
that returns a sliced queryset. Both are existing `ConfigurationError` paths in
[`django_strawberry_framework/utils/querysets.py::apply_type_visibility_sync`][querysets]
and its async sibling, and they apply whether arguments are active or omitted. The list
field must not directly read `source.query.is_sliced`, import the private seal, or translate
the failure into a new list-argument reason (*alternatives rejected: see the
[rationale][rationale-d8]*). This also rejects limit-only composition safely. Django can narrow an
existing slice, but `get_queryset` may need to filter first and cannot legally filter a
sliced query; accepting it only for identity hooks would make one public argument
source-dependent and could bypass visibility.

### Decision 9 — no-argument sync behavior takes the old branch; async only adapts completion

When all three arguments are omitted or null, the resolver executes the same visibility and
`bounded_rows(result, info, max_rows, trusted=trusted_max_rows)` logic as `0.0.14`. The new
normalizer must have an explicit fast path that delegates there; it must not calculate
`offset=0` and rebuild an equivalent slice. The sync branch returns that result exactly as
before. The async branch wraps a final queryset in Decision 5's async-only completion adapter,
including when arguments are omitted; that intentional representation change fixes the
existing event-loop-unsafe graphql-core completion and cannot honestly be called byte-for-byte
resolver parity. Tests compare `str(queryset.query)`, `query.low_mark`, `query.high_mark`,
result data, and query count against the pre-card baseline, and separately prove the new
adapter's safe transport.

The SDL necessarily changes by adding optional arguments. Sync resolver behavior, SQL,
ordering, nullability, and response data do not; async response data/SQL stay the same while
the unsafe raw-queryset result representation changes. The card's phrase "LIMIT/OFFSET present
exactly when supplied" is FALSE against shipped behavior: no-argument raw lists already carry
a policy `LIMIT` through
[`django_strawberry_framework/resource_policy.py::bounded_rows`][resource-policy], and have
since [`spec-047`][spec-047]. A spec may not silently redefine its parent Definition of done
while the board still demands the opposite result, so Slice 5 AMENDS that card DoD row in the
KANBAN database to the shipped contract: omission preserves the existing policy `LIMIT`
unchanged, a smaller client limit lowers the high mark, and a positive offset raises the low
mark (*card amendment derivation: see the [rationale][rationale-d9]*). Tests pin exactly those
three. The neighbouring Scope claim that no-argument SQL is byte-for-byte today's survives
the amendment unchanged and stays a live assertion.

### Decision 10 — coercion errors stay GraphQL-owned; runtime domain errors are package-owned

GraphQL `Int` rejects strings, booleans, integers outside the signed 32-bit wire range, float
literals, and non-integral or non-finite float variables before a field resolver runs. Those
failures are already typed `GraphQLError` instances but cannot carry
`LIST_ARGUMENT_INVALID` without replacing the scalar or adding a schema-wide error-rewrite
layer. [`graphql/type/scalars.py::coerce_int`][graphql-scalars] accepts finite integral float
variables and coerces them to Python `int`, so `{"offset": 1.0}` reaches the wrapper as `1`;
origin-type rejection is impossible after standard coercion and is not promised. The spec
promises standard GraphQL error shape for actual coercion failures, not a package extension
code.

Negative and over-ceiling values are valid GraphQL integers but invalid list arguments, so
the wrapper raises `ListArgumentError` with package extensions. Direct unit calls that
bypass GraphQL also reject non-integers and bools through the same type, because internal
callers do not receive GraphQL coercion for free.

*Alternatives rejected: see the [rationale][rationale-d10] (a custom stricter integer scalar,
a schema extension rewriting all Int coercion errors).*

### Decision 11 — migration maps upstream roots here and nested pagination to connections

The future migration guide records:

| Upstream surface | Package mapping |
|---|---|
| `graphene_django.DjangoConnectionField(..., offset:)` | Prefer `DjangoListField(..., offset:, limit:, orderBy:)` when a flat list is the desired response; otherwise keep `DjangoConnectionField` and migrate to cursor arguments. |
| `strawberry_django.field(pagination=True)` / `OffsetPaginationInput` | `DjangoListField` with direct `offset` and `limit` arguments; no wrapper input object. |
| `OffsetPaginated[T]` / `offset_paginated()` | No envelope-equivalent in this card; choose flat `DjangoListField` or a connection when count/page metadata is required. |
| Nested [`apply_window_pagination`][upstream-strawberry-pagination] | A synthesized nested `DjangoConnectionField`; raw nested offset windows are not shipped. |

The note also calls out the order precondition and recommends a unique final order term.
Card [`TODO-BETA-071-0.1.8`][kanban], not this flow, owns the eventual guide text; this spec
pins its required content without editing the card body or future guide now.

### Decision 12 — the version bump belongs to the `0.0.15` joint cut

Cards 050, 051, 052, and 053 are all non-Done at the target patch version. Under the joint
version-cut rule the last card owns the single
[`django_strawberry_framework.__version__`][package-init] literal, the
[`tests/base/test_init.py`][test-base-init] assertion, glossary package-version state, and
release wording. [`spec-053`][spec-053] and card 053's board definition already claim that
ownership. *Derivation of the joint-cut version boundary: see the [rationale][rationale-d12].*

[`pyproject.toml`][pyproject] derives the package version dynamically from the literal, and
`uv.lock` records no editable-root version. Joint-cut deferral therefore means those files
remain untouched rather than receiving synchronized duplicate values; the actual release
state is the triplet above.

This card's Slice 5 folds its shipped surface into docs but does not move version state or
create a [`CHANGELOG.md`][changelog] entry. This spec grants no exception to the
maintainer-only changelog rule.

### Decision 13 — graphql-core workarounds have a dependency-owned lifecycle

The async-only queryset adapter exposes an upstream executor defect rather than creating it:
the installed graphql-core `ExecutionContext.complete_list_value` materializes an
`AsyncIterable`, recursively completes the list, and returns the recursive completion
awaitable without awaiting it. The workaround belongs to
`django_strawberry_framework/_graphql_core_patches.py::apply`, not Strawberry's HTTP-view
patch module. `DjangoStrawberryFrameworkConfig.ready` dispatches it independently, and
`APPLY_UPSTREAM_PATCHES = {"graphql_core": False}` disables only this dependency boundary.

The retirement sentinel calls the captured upstream method on the actual bug shape and asserts
that awaiting it once still yields a residual awaitable. When upstream fixes the defect, that
sentinel fails and the module can be removed without disturbing Strawberry body parsing. See
the [rationale][rationale-d13] for the rejected shared-gate design.

## Implementation plan

| Slice | Files | Delta |
|---|---|---|
| 1 | [`django_strawberry_framework/list_field.py`][list-field], [`django_strawberry_framework/resource_policy.py`][resource-policy], [`django_strawberry_framework/__init__.py`][package-init] | Synthesized list signature; error-lazy schema-derived wire names; normalized list arguments with independent supplied/window/order fields; `ListArgumentError` plus its root export; window-aware extension of the one raw-list bounding seam; shared async-iterator cleanup; no-argument fast path. |
| 2 | [`django_strawberry_framework/list_field.py`][list-field], [`django_strawberry_framework/orders/sets.py`][orders-sets], [`django_strawberry_framework/utils/querysets.py`][querysets], [`django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension._optimize`][optimizer-extension] | Sync/async Meta-order pipeline, OrderSet-owned active-term detection, post-apply and combined-query guards, async-only queryset completion adapter, optimizer preservation, combined offset/limit application. |
| 3 | [`tests/test_list_field.py`][test-list-field], [`tests/test_resource_policy.py`][test-resource-policy], [`tests/orders/test_sets.py`][test-orders-sets], [`tests/base/test_init.py`][test-base-init] | Construction/direct-call mechanics, naming fallback, `ListArgumentError` pickle round trip, active-term/override call-count, post-apply validator arms, exact iterator consumption/cleanup precedence, model-order state, query low/high marks, and removal of adapter-masking async-unsafe setup where HTTP cannot isolate the mechanic. |
| 4 | Planned `examples/fakeshop/test_query/test_list_field_api.py` and `examples/fakeshop/test_query/test_list_field_async_api.py`, [`examples/fakeshop/test_query/test_resource_policy_api.py`][fakeshop-test-resource-policy], [`examples/fakeshop/test_query/test_multi_db.py`][fakeshop-test-multi-db], [`examples/fakeshop/apps/kanban/constants.py`][fakeshop-kanban-constants] | Dogfood arguments on the three existing shipped Branch list fields from a dedicated sync suite, mount exceptional fields only in test-local schemas, cover ordered pages/visibility/caps/errors/naming/sync-async shapes/routing/SQL, and regenerate tracked paths after both new files enter the index. No new field is added to the shipped library schema. |
| 5 | [`django_strawberry_framework/resource_policy.py`][resource-policy], [`docs/GLOSSARY.md`][glossary] (DB), [`docs/README.md`][docs-readme], [`docs/TREE.md`][tree], [`README.md`][readme], [`examples/fakeshop/test_query/README.md`][fakeshop-test-query-readme], KANBAN DB/exports | Fold in the shipped argument/returned-row/skip semantics, add the new async suite and its shared-helper exemption to the live-tier guide, include the new async test in the generated tree, and close the card; no version, `TODAY.md`, or changelog edit. |

## Helper-reuse obligations (DRY)

- [`django_strawberry_framework/resource_policy.py::effective_bound`][resource-policy]
  remains the only field/policy ceiling rule.
- [`django_strawberry_framework/resource_policy.py::bounded_rows`][resource-policy] and
  [`django_strawberry_framework/resource_policy.py::bounded_rows_async`][resource-policy]
  remain the only raw-list window implementation. Relation-list callers pass no client
  window and retain current behavior. Their iterator-close/error-note logic is extracted to
  one package-private utility reused when the list pipeline rejects an async-only source
  before bounding; no second cleanup implementation is allowed.
- [`django_strawberry_framework/orders/__init__.py::order_input_type`][orders-init] remains
  the only lazy order-input annotation builder and orphan-ledger writer.
- [`django_strawberry_framework/orders/sets.py::OrderSet.apply_sync`][orders-sets] /
  [`django_strawberry_framework/orders/sets.py::OrderSet.apply_async`][orders-sets] remain
  the consumer-facing order permission and queryset application pipeline, and the list field
  calls those exact methods so a subclass override keeps the same behavior it has on a
  connection or hand-written resolver. The order module adds one package-internal
  `_input_has_active_terms(input_value) -> bool` classmethod that reuses its own normalization
  and flat-order machinery; the list field never walks an order input itself. The helper
  runs only after public apply succeeds,
  preserving permission and validation precedence. Re-normalizing the small input is the
  deliberate compatibility cost of honoring an overridden public apply method; bypassing
  that override through a parallel state-returning entry point was rejected. Active input
  must also leave the returned queryset materially ordered, so a malformed no-op override
  cannot satisfy the offset guard on an otherwise unordered source merely by receiving a
  non-null input. `_normalize_input` overrides are therefore required to be pure and
  deterministic, and that is an explicit COMPATIBILITY CONSTRAINT on the method rather than
  merely a test counter: an argument-bearing request may invoke normalization once inside
  public apply and once inside the active-term helper, so a stateful override can otherwise
  produce different application and activity verdicts from one request. The requirement is
  documented on the method itself, its input is capped through the existing value policy, and
  an override whose second normalization disagrees with its first must surface an actionable
  `ConfigurationError` naming the method rather than silently deciding the offset guard on an
  incidental verdict. Instrumented tests pin the call counts, the purity requirement, and the
  disagreement error. One immutable normalized-order record shared by both callers is the
  cleaner long-term shape; it is not adopted here because it can only be reached by bypassing
  the public `apply_*` override this card exists to honor, and changing that is an `OrderSet`
  API decision of its own.
- [`django_strawberry_framework/utils/typing.py::schema_config_from_info`][typing-utils]
  remains the neutral schema-config lookup. Argument error names combine it with Strawberry
  `Info.get_argument_definition` and `name_converter.from_argument`; list code does not
  reimplement wrapped/direct schema traversal.
- Manager-to-queryset coercion and visibility stay in
  [`django_strawberry_framework/utils/querysets.py`][querysets]; pagination does not grow
  another source classifier. Post-OrderSet validation extends/reuses the same hardened seal
  with a new require-unevaluated option and the shipped `_SealPolicy.reject_combined` one,
  plus a surface-specific `ConfigurationError` renderer; argument-bearing visibility uses
  reject-combined at both source and result seals - which makes `combined` reachable outside
  the cascade for the first time and so owes a message arm at each visibility site - and list
  code never reads hostile queryset state itself.
  That module also owns the internal async-only queryset-row adapter shared with the
  optimizer; the optimizer side of that pair is one unwrap/rewrap arm inside
  [`django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension._optimize`][optimizer-extension],
  never a second adapter class or a parallel planning path.
- The list-field signature builder owns list arguments. It may share a neutral parameter
  constructor with the connection builder if extraction is genuinely smaller, but the
  connection's filter argument and return annotation must not leak into the list field.
- One `ListArgumentError` constructor owns every runtime domain rejection and extension
  payload.

## Edge cases and constraints

- `offset: null`, `limit: null`, and `orderBy: null` are omission, not zero or empty input.
- `offset: 0` is accepted without ordering; `limit: 0` yields an empty list.
- GraphQL `Int` is signed 32-bit. A larger literal/variable fails coercion before the policy
  ceiling is consulted.
- `True` is rejected in direct calls even though Python treats it as integer `1`.
- `offset == max_list_rows` is accepted; `offset == max_list_rows + 1` is rejected.
- `limit == effective_ceiling` is accepted; the next integer is rejected.
- An offset beyond the available row count returns `[]` when it remains within policy.
- `trusted_max_rows=True` with no `max_rows` remains inert, matching shipped behavior.
- `trusted_max_rows=True, max_rows=P+N` widens returned rows but not accepted offset.
- Empty and all-null order inputs do not satisfy the explicit-order branch; an independently
  effective stable model default may still satisfy the guard.
- A model `Meta.ordering = []` is not active; a non-empty non-random tuple is active only
  while the post-visibility queryset still uses Django's default-ordering path.
- A model ordering containing `"?"` or a recognized `Random()` expression is not an active
  stability order, even when another term follows it.
- Reversing a stable model default remains stable; `standard_ordering=False` changes direction
  and does not by itself disable the fallback.
- A to-many model default may duplicate parent instances; offset counts SQL result rows.
- A consumer queryset's private `.order_by(...)` does not substitute for the public order
  precondition.
- To-many `OrderSet` terms keep their shipped `Min`/`Max` aggregate behavior. Pagination
  adds no `DISTINCT`, before or after the order.
- Ordering permission denial happens before any slice and retains its existing error.
- A non-queryset with `orderBy` fails rather than returning input-order rows.
- `None` from a nullable resolver stays `None` under limit/zero-offset, but it cannot satisfy
  `orderBy` or a nonzero-offset order precondition.
- The shared [visibility boundary][glossary-visibility-boundary] rejects a pre-sliced source
  before the hook and a sliced hook result afterward, under active and omitted arguments alike; the list field adds no
  parallel slice-state classifier.
- A combined queryset is rejected for any non-null argument, including `offset: 0`,
  `limit: 0`, and `orderBy: []`; the omitted/all-null legacy branch is unchanged.
- A custom `OrderSet.apply_*` result must SEAL to a lazy, unsliced, model-row-shaped,
  non-combined, same-model, same-route plain queryset. A sealable `QuerySet` SUBCLASS is
  accepted and normalized into that plain rebuild rather than rejected for its class;
  same-route means equal `_db` (`None` included) and equal `_hints`. Arbitrary custom code is
  trusted to preserve the sealed source predicates.
- An async-only iterable's iterator is closed when it exposes `aclose` and consumption does
  not reach natural exhaustion: the accepted exclusive stop (`offset + effective_limit`) is
  reached, iteration errors, or the source is otherwise stopped/rejected early. A naturally
  exhausted iterator is deliberately left alone. Cleanup failure precedence stays exactly as
  [`django_strawberry_framework/resource_policy.py::bounded_rows_async`][resource-policy]
  currently specifies.
- `limit: 0` guarantees framework-owned work only: after the resolver returns, no source
  advancement and no row-fetch query occurs. It consumes no lazy sync or async iterable item
  and still invokes `aclose` when available. It is not a guarantee of zero database work - the
  resolver is still invoked and may query internally, and visibility hooks and permission
  checks still run - and the pre-execution document budget may reject the operation before
  this seam.
- A retained sync generator truncated by a client window stays SUSPENDED; its `finally` does
  not run. Early-exit cleanup is promised for async-only sources only (Decision 8).
- Rejected async-only sources are not advanced and are closed when possible; the domain
  error stays primary if cleanup fails.
- Async consumer results are awaited once. Sync-path awaitables and residual async-path
  awaitables are disposed and rejected before visibility/order/window handling.
- A nullable outer list keeps its consumer annotation; arguments do not alter nullability.
- The optimizer must observe the final sliced queryset without cloning away low/high marks.
- Multiple aliases with different arguments are independent resolver invocations; there is
  no connection-window merge or shared prefetch plan for root list fields.
- [Multi-database cooperation][glossary-multi-database] stays on the source queryset. Slice
  arithmetic must not evaluate or recreate it from the target model's default manager.
- Existing [relation handling][glossary-relation-handling] keeps nested raw-list pagination
  out of this root-only slice; nested pages remain connections.

## Test plan

### Live HTTP tier

The sync surface gets its own module, `examples/fakeshop/test_query/test_list_field_api.py`,
rather than nineteen more rows inside
[`examples/fakeshop/test_query/test_library_api.py`][fakeshop-test-library]. That file is
already the broad library APPLICATION suite - FK and reverse-FK traversal, M2M, enum and
nullable scalar serialization, optimizer SQL shape, the `filter:` / `orderBy:` surfaces,
GlobalID rejection, and the row-preserving predicate oracle - and folding a field factory's
whole argument matrix into it would make the feature hard to discover and harder to maintain.
The live-tier guide permits cross-cutting suites, the async half of this card already has its
own module, and a dedicated sync module makes the pair symmetric. The new suite drives the
same already-registered library types and inline library models the library rows use, so the
split costs no fixtures.

Both new modules create `Branch`, `Shelf`, and library users inline with
`Model.objects.create(...)` / `create_user(...)`, following the library tier's explicit
repository exception; they must not import `apps.products.services` merely to satisfy the
products catalog/auth seed rule. A genuinely mixed row that also creates products catalog
models begins with [`seed_data(N)`][glossary-seed-data] for that products half, as
[`test_resource_policy_api.py`][fakeshop-test-resource-policy] already demonstrates.

The shipped fakeshop SDL changes only through the factory behavior on these already-declared
fields in [`examples/fakeshop/apps/library/schema.py::Query`][fakeshop-library-schema]:
`all_library_branches_via_list_field`,
`all_library_branches_via_list_field_nullable`, and
`all_library_branches_via_list_field_manager_resolver`. No new root field is added to that
schema. The first field is the primary paging surface and already anchors the shipped
`max_list_rows` acceptance row in
[`test_resource_policy_api.py`][fakeshop-test-resource-policy]; the nullable and manager
variants retain their outer-nullability and manager-coercion roles while gaining the same
arguments. Exceptional source shapes and custom converters live only in
[holder-mounted][glossary-probe-urlconf] test-local schemas and therefore do not expand
the shipped SDL.

1. Introspection shows `offset`, `limit`, and `orderBy` on
   `allLibraryBranchesViaListField`, with nullable `Int`, nullable `Int`, and the existing
   Branch order input respectively under the default schema naming config; the nullable and
   manager-resolver siblings publish the same arguments without changing their return shapes.
2. Under staff context, `orderBy: [{ name: ASC }, { id: ASC }], offset: 1, limit: 2`
   returns the second and third visible rows in that exact order.
3. An anonymous request orders by the unguarded `city`, then `id`, and proves a restricted
   Branch is removed by `get_queryset` before offset is counted; using `city` avoids the
   example's staff-only `name` order gate while keeping visibility active.
4. `orderBy` alone arranges the whole policy-bounded list and exercises the shipped order
   permission path under staff context.
5. Nonzero offset with no order returns `LIST_ARGUMENT_INVALID` and
   `reason=order_required`.
6. Negative and over-ceiling offset return the package error extensions.
7. Negative and over-ceiling limit return the package error extensions.
8. String, bool, out-of-range integer, non-integral/non-finite float variables, and float
   literals produce GraphQL `Int` coercion errors and no resolver SQL; integral-valued float
   variables are coerced to integers and execute with the resulting coordinate.
9. `limit: 0` returns an empty list and performs no row-fetch query where Django's empty
   slice short-circuits.
10. `offset: 1, limit: 0` still obeys the order precondition; with an active order it
    returns an empty list without fetching a row.
11. A trusted widened field can return beyond policy when no client limit is supplied, but
    its offset is still rejected beyond policy.
12. Holder-mounted test-local fields named `branches_materialized`, `branches_nullable_none`,
    `branches_presliced`, `branches_trusted`, and `branches_combined` provide the exceptional
    source shapes without altering the shipped fakeshop SDL. The materialized/`None` fields
    prove limit/zero-offset behavior, while any non-null `orderBy` (including `[]`) returns
    `queryset_required` and nonzero offset returns `order_required`; the nullable field
    preserves `None` under limit/zero offset.
13. `branches_presliced` proves, under the
    [error-policy pass-through][glossary-production-error-policy] fixture, that both
    omitted and active arguments retain the shared visibility boundary's actionable
    `ConfigurationError` before the hook runs. A separate test-local conforming custom
    `OrderSet` override proves public dispatch; malformed overrides returning sliced,
    evaluated, projection, combined, wrong-model, non-queryset, sync-awaitable,
    async-method-non-awaitable, or residual-async-awaitable results prove post-apply
    `ConfigurationError` and disposal. The
    wrong-route override runs in the established `FAKESHOP_SHARDED=1`
    [`test_multi_db.py`][fakeshop-test-multi-db] mount so it reaches a real `shard_b` alias;
    default and sharded invocations retain their existing mutually exclusive test modes.
14. On Branch's no-default-order model, empty/all-null order input plus nonzero offset returns
    `order_required`; an anonymous staff-gated `name` order plus nonzero offset returns the
    existing order-permission denial first, pinning permission-before-offset precedence.
15. Under staff context, a to-many aggregate order through `shelves` plus limit/offset
    returns one row per Branch, and captured SQL contains one `LIMIT/OFFSET` pair and no
    `DISTINCT`.
16. Two numeric domain failures in one request report `offset` first; `orderBy` plus nonzero
    offset over the materialized-list field reports `queryset_required`; order input over the
    pre-sliced field reports the visibility-boundary error. These are the wire-reachable
    precedence pairs from Decision 8.
17. `branches_combined` preserves the omitted/all-null legacy behavior but every non-null
    argument, including zero/empty values, rejects at the source seal before the visibility
    hook, OrderSet permission, or windowing; a hook-returned combination rejects at the result
    seal.
18. Test-local schemas using `strawberry_config(auto_camel_case=False)` and a custom
    `NameConverter` prove SDL/query spelling and `ListArgumentError.argument` follow the
    active converter for all three Python parameters rather than hard-coded literals.
19. The accepting half of Decision 6's model-default branch is wire-reachable and is earned
    here rather than in the package tier. A holder-mounted `branches_default_ordered` field
    targets a registered type whose model declares a stable non-random `Meta.ordering` - the
    kanban and glossary apps both ship such models, while `Branch` declares none - and proves
    nonzero offset succeeds with no `orderBy` and with no injected pk term. A sibling field
    whose consumer resolver calls `.order_by()` on the same model clears that default and
    flips the identical request to `order_required`, so both verdicts of the predicate are
    live rather than only its rejection in row 14. The exhaustive state matrix (grouping
    suppression, `extra_order_by`, recognized random terms, unreadable query state) stays in
    the package tier, which is the only place those states can be constructed.
20. The capability rule is pinned from both sides. A holder-mounted field over a registered
    type that declares neither `Meta.orderset_class` nor model default ordering publishes
    `offset` and `limit` and NO `orderBy` in introspection, and every positive offset on it
    returns `order_required` - the permanently-unusable coordinate Decision 2 accepts, proven
    rather than merely conceded. Its counterpart is row 19's `branches_default_ordered`, whose
    target publishes no `orderBy` either yet accepts a positive offset from model
    `Meta.ordering` alone. Together they show that a published `offset` is a runtime
    precondition, not a capability claim.
21. Offset alone, with `limit` omitted, returns `[offset:offset + effective_ceiling]` rather
    than only the combined offset-plus-limit shape of row 2; the captured SQL carries the
    raised low mark and the unchanged policy high mark. A resource-policy unit row pins the
    same arithmetic at the bounding seam.
22. `branches_combined`'s legacy branch is asserted against a NAMED BASELINE HELPER, not
    against the absence of the new error. That helper captures what the omitted/all-null
    request produces before the card - the exact result data or exception class and message
    policy, the captured SQL, and the `get_queryset` call count - and the legacy row asserts
    equality with it. "Not `LIST_ARGUMENT_INVALID`" is not a sufficient oracle here, because a
    combined Branch queryset also meets `BranchType.get_queryset` filtering before pagination
    and can legitimately produce either data or a pre-existing error.
23. Two aliases of the same field in one document, with different `offset` / `limit` pairs,
    return independent pages. Root list fields share no window state and no merged plan, and
    this row exists so an accidental per-field cache cannot pass unnoticed.
24. A nullable outer list and a non-null outer list over the same `None`-returning holder field
    each preserve `null` under a limit-only request and each error under a rejected argument,
    with the response nullability the consumer annotation declares. This is the surprising
    half of Decision 8's capability-over-null-propagation choice and is earned live.
25. A conforming test-local `OrderSet` override that returns a `QuerySet` SUBCLASS derived from
    its sealed input succeeds and returns the correct ordered page, proving the seal normalizes
    a sealable subclass into a plain queryset rather than rejecting it for its class.
26. Under `FAKESHOP_SHARDED=1`, the same-route invariant is proven on its HARDER half: an
    override returning a candidate whose `_db` is `None` on both sides but whose `_hints`
    differ from the sealed source's is rejected, alongside the existing explicit
    `.using("default")` versus `.using("shard_b")` mismatch. An explicit-alias row alone would
    leave routing-intent equality unpinned.

Every test-local sync/async schema mount uses the established module-level current-schema
holder under `override_settings(ROOT_URLCONF=...)`, resets that holder and Django's URL caches
in `finally`, and uses the repository's registry/finalization cleanup fixtures under the
established [schema reload discipline][glossary-schema-reload-discipline]. Test-local fields
are declared over already-registered app `DjangoType`s; a throwaway `DjangoType` would mutate
the registry and trip the acceptance conftest's registration identity guard. Any future mixed
row that also touches products or auth models begins with the required
[`seed_data(N)`][glossary-seed-data] or `create_users(N)` call. The exceptional fields and
custom converters therefore never leak into the shipped app schema or a later test.

Live-first placement is fixed per branch rather than left to implementation drift. The package
tier may assert internal identity and exact call counts for any of these, but the FINAL verdict
of each of the following must also be reachable live and must stay live: every public
`ListArgumentError.reason`; custom name-converter spelling; both verdicts of the model-default
order predicate; order permission denial preceding offset rejection; combined-source and
hook-result rejections; post-order evaluated / projection / combined / wrong-model result
classification; and optimizer-on and optimizer-off async queryset completion. Each test TODO
names its tier explicitly so coverage cannot migrate back into package-only execution during
implementation.

The supported-version matrix is part of this test plan, not an afterthought. The
implementation reads private or semi-private behavior in three dependencies - Django query
state (`default_ordering`, `order_by`, `extra_order_by`, `group_by`, `combinator`,
`_result_cache`, `_hints`), Strawberry argument definitions and name conversion, and
graphql-core list completion - while this document's source links point at one local Python
3.14 environment. That is evidence, not the contract. The new async completion rows, the
model-order predicate, the two new seal axes, and the argument-signature tests must pass on
the repository's existing CI matrix from the declared Django and Python floors through latest;
a local proof on one interpreter does not discharge the requirement.

The resource-policy mount adds a small-policy row proving a legal client limit narrows the
field, the first over-ceiling value rejects, and offset consults the request-specific policy
rather than
[`django_strawberry_framework/resource_policy.py::DEFAULT_RESOURCE_POLICY`][resource-policy].
It also pins that the independent pre-execution collection-cost charge remains the raw-list
policy ceiling when the operation supplies a smaller `limit`; runtime row narrowing must not
silently weaken document-shape accounting.

`examples/fakeshop/test_query/test_list_field_async_api.py` mounts a test-local schema through
`AsyncDjangoGraphQLView` and `AsyncClient`, following the established fakeshop async-test
pattern in
[`examples/fakeshop/test_query/test_relations_async_api.py`][fakeshop-test-relations-async]:
the shipped fakeshop URLconf mounts the sync view, so the module supplies its own async mount
over the apps' already-registered types and declares only test-local fields, never throwaway
`DjangoType`s that would mutate the registry and trip the acceptance conftest's registration
identity guard on every test. Every case carries
`@pytest.mark.django_db(transaction=True)`, which the tier's existing async suites require for
ORM access inside the event loop. This module is a documented exemption from the shared
[`examples/fakeshop/graphql_client.py`][fakeshop-graphql-client] helpers, and the exemption is
stated in its docstring rather than left to be inferred: those helpers are synchronous by
construction ([`django_strawberry_framework.testing.TestClient`][glossary-testclient] over
`django.test.Client`) and expose no async post, exactly as the two shipped async live suites already document. Widening
`graphql_client.py` with an `AsyncTestClient`-backed helper is a separate tier-wide change and
is not smuggled into this card. It proves, without `DJANGO_ALLOW_ASYNC_UNSAFE`, the default
resolver, a CONFORMING LAZY sync consumer returning `Manager`/`QuerySet` - one that does not
evaluate, since the adapter cannot make an evaluating sync resolver safe (Decision 5) - an
`async def` consumer returning `QuerySet`, visibility -> order -> window, nullable/materialized
behavior, limit-only and `offset: 0` async-generator and sync-returned async-only iterable
bounds, and serialized source-shape/order errors. Positive offset over an async-only source
appears here only as the `order_required` rejection Decision 8 requires; its accepted
arithmetic is pinned against the bounding helper in
[`tests/test_resource_policy.py`][test-resource-policy].

Finalization assertions must respect Python's async-generator semantics, and an earlier draft
of this plan did not. `aclose()` on an async generator that has never been advanced does NOT
enter its body: neither its setup nor its `finally` block runs, so a body-level `finally`
witness after zero advances is unobservable, and advancing the generator to make it observable
would destroy the zero-consumption guarantee those same rows exist to prove. The plan therefore
separates two different facts. That `aclose()` WAS INVOKED is proven with a custom async
iterator whose own externally implemented `aclose()` increments a counter, and that is what the
`limit: 0` and pre-bound-rejection rows assert beside zero `__anext__` calls. That a generator
BODY FINALIZED is proven with a real async generator only after at least one item has been
requested, which is the accepted-stop row. Each test's prose states which of the two it
asserts, and neither wording is used for the other.

Cleanup diagnostics stay out of the HTTP assertions. The production GraphQL JSON error envelope
does not serialize `BaseException.__notes__`, so exact note content and precedence are
package-tier subjects; live HTTP asserts the complete public `extensions` payload and that a
cleanup failure did not displace the primary domain error. The live result proves the async-only
queryset adapter works with and without `DjangoOptimizerExtension`; package-level adapter
inspection pins the optimized inner queryset's SQL/low/high marks without pretending a
[thread-local async DB capture][glossary-async-sql-capture-boundary] observes
worker-thread SQL.

Because that module is a new tracked path, Slice 4 adds it to the card's predicted files and,
after the file is added to the index, runs
[`scripts/build_kanban_tracked_path_constants.py`][build-kanban-tracked-paths] so
[`examples/fakeshop/apps/kanban/constants.py`][fakeshop-kanban-constants] includes it. Slice 5
regenerates [`docs/TREE.md`][tree] after the file exists. Omitting either generated view would
make the implementation's documented/test layout disagree with repository governance.

### Package tier

[`tests/test_list_field.py`][test-list-field] covers construction and exact mechanics a real
sync or async HTTP request cannot isolate:

- generated callable signatures with and without `Meta.orderset_class`;
- continued lazy top-level package import: constructing the signature may import orders, but
  importing `django_strawberry_framework` alone must not;
- nullable outer annotation preservation after argument synthesis;
- direct-call non-integer and bool rejection;
- `ListArgumentError.__reduce__` preserving constructor arguments, extensions, and instance
  state across a pickle round trip, matching the existing dual-base error precedent;
- direct-call schema-name fallback and argument-definition lookup mechanics;
- exact sync-awaitable/residual-async-awaitable disposal and one-await call counts, paired
  with the live serialized behavior;
- post-OrderSet validator arms for plain-queryset type, cache, slice, iterable class,
  combinator, model/table, routing, and unreadable state; the cache and combinator arms assert
  on the message text, not only on the exception class, because an unarmed defect code reaches
  the schema author as `_defect_message`'s self-naming framework-defect wording instead of an
  actionable one;
- exact rejected-async-iterator no-advance and optional-`aclose` counts, witnessed by a custom
  async iterator whose own `aclose()` increments a counter rather than by an async generator's
  body `finally`, which cannot run after zero advances; plus primary-versus-cleanup exception
  notes, whose exact `__notes__` content and precedence live only here because the production
  GraphQL JSON envelope does not serialize them;
- async-only queryset adapter protocol - `__aiter__` present, `__iter__` absent - and the
  `DjangoOptimizerExtension._optimize` unwrap/rewrap identity and inner low/high marks, which
  must be asserted directly because an unrecognized adapter falls through that method's
  non-`QuerySet` branch with every row and SQL assertion still passing; the same rewrap pinned
  on that method's two early returns, an already-evaluated inner queryset and an unresolvable
  return type, either of which would otherwise emit a bare queryset into async completion;
  paired with live safe completion;
- one `check_deadline` call per argument-bearing request, in the same position relative to row
  fetching as the shipped no-argument path;
- the already-shipped
  [`tests/utils/test_querysets.py::test_sliced_hook_result_fails_closed_with_typed_error`][test-querysets]
  remains the owner of sliced hook-result rejection; the live pre-sliced consumer field
  proves this list surface routes through that shared boundary rather than duplicating it;
- the model-default predicate's remaining states, which a live mount cannot construct as
  distinct verdicts: grouping suppression, `extra_order_by`, recognized-random model ordering
  (alone and mixed), and unreadable query state all fail it; `.reverse()` remains valid,
  explicit active order may satisfy a known-empty queryset vacuously, and an unordered empty
  queryset cannot; a to-many model default preserves and counts Django's duplicate result
  rows. The predicate's two plain verdicts - a stable `Meta.ordering` satisfying the guard
  without a pk append, and a resolver `.order_by()` clearing or replacing it - are live-tier
  rows 19 and 14 and are not duplicated here;
- policy, field, trusted-field, and client-limit cap matrix;
- exact no-argument/null-argument `str(qs.query)`, `low_mark`, and `high_mark` parity;
- supplied limit changing only `high_mark`, and supplied offset changing `low_mark` plus the
  corresponding high mark;
- an explicit sweep of existing adapter-relevant `DJANGO_ALLOW_ASYNC_UNSAFE` setup: queryset
  completion tests run with the variable absent once the adapter ships, while any retained
  setup names the unrelated behavior that still needs it so it cannot silently mask this
  regression class;
- the four normalized-record fields' independent effects: `any_argument_supplied` selecting
  argument mode (and only that), the window fields producing an omission-identical window for
  `offset: 0`, `order_by_supplied` driving `queryset_required` for an empty list, and material
  activity being consulted only after apply. A test collapses none of them into another;
- error-lazy wire-name resolution: an instrumented `NameConverter` records ZERO
  `from_argument` calls across a batch of successful argument-bearing requests and exactly one
  on a rejection, so a shared consumer converter is never invoked concurrently at runtime;
- seal-axis mechanics the live tier cannot isolate: a sealable `QuerySet` SUBCLASS post-apply
  result is normalized into a plain queryset and accepted, while a subclass carrying an
  unresolved `_deferred_filter` still fails closed as `untrusted`; and routing-INTENT
  equality, where two candidates both carrying `_db is None` are accepted when their `_hints`
  match the sealed source's and rejected when they differ;
- a retained sync generator truncated by a client window is still suspended and resumable
  afterward - the sync cleanup contract Decision 8 explicitly declines - pinned so a later
  card flips it deliberately rather than discovering it;
- an async source holding exactly `offset + limit` rows versus fewer, distinguishing an
  accepted-stop close from an observed natural exhaustion that must leave the iterator alone;
- a benchmark of the post-apply seal over a complex annotated query, a to-many aggregate
  order, and a queryset carrying prefetch metadata, recording the cost Decision 5 accepts
  rather than asserting a threshold.

[`tests/test_resource_policy.py`][test-resource-policy] already pins the generic sequence,
non-subscriptable iterable, and async-iterable behavior at the one raw-list seam: sequence
slicing, the non-subscriptable-iterable bound, trusted widening, `None` preservation on both
colors, `aclose` after the effective prefix, an exhausted iterator that is left untruncated,
and the two cleanup-failure precedence arms. This card adds the window arms that seam has
never had, and they are new pins rather than an audit of existing ones: no zero-length window
is reachable today, because
[`django_strawberry_framework/resource_policy.py::validate_collection_bound`][resource-policy]
and `ResourcePolicy` construction both reject a bound below `1`, so an accepted client
`limit: 0` is the first spelling that can produce one. The new rows therefore pin
zero-limit/no-consumption on sequence, non-subscriptable, and async-only sources - no
`islice`, no `__next__`, no `__anext__` - with the optional `aclose` still invoked on the
async source, plus nonzero-offset window arithmetic at the same seam. That arithmetic is
pinned here for every shape INCLUDING async iterators, which is where positive-offset async
behavior belongs: the public field refuses it, the helper supports it, and the two facts live
in different tiers on purpose. The offset-only window (`limit` omitted, so the stop is
`offset + effective_ceiling`) is pinned here as well as live. Existing relation resolver tests
remain unchanged and prove callers without client windows still receive their old prefix
bound.
[`tests/orders/test_sets.py`][test-orders-sets] pins that the active-term helper shares the
canonical normalization/flat-order rules, reports false for empty/all-null input, and does
not replace either public apply method. List-field tests use instrumented sync and async
`OrderSet` overrides to prove each wrapper color still dispatches through the corresponding
public override and to pin the documented double normalization of pure/deterministic
`_normalize_input` overrides.

### Failability and commands

Each SQL test is proven to fail if slice order is reversed, the offset is ignored, the
policy is bypassed, or a pk/`DISTINCT` clause is injected. Each error row asserts the class
through [`original_error`][glossary-structural-error-classification] where available and the
complete extension payload over HTTP.

The implementation card runs the repository-required full suite when the maintainer requests
it. This spec-authoring correction does not run pytest; it runs the repository-required ruff
format/check pair plus the [`scripts/check_spec_glossary.py`][check-spec-glossary] checker,
structural checks, and link/kanban verification prescribed by
[`docs/SPECS/NEXT.md`][next].

## Doc updates

- [`django_strawberry_framework/list_field.py::DjangoListField`][list-field] - replace the
  entire present-tense ordering-contract paragraph: before this card it falsely promises an
  `orderBy` argument the field cannot accept, and its unconditional claim that an unordered
  flat-list sequence is acceptable becomes true only for offset-free requests. Document the
  shipped argument and nonzero-offset precondition, conditional default-named `orderBy`
  publication, active name conversion, cap behavior, no pk append, and the recommendation for
  a unique final order term. It must state the contract as ORDERED OFFSET rather than stable
  or repeatable pagination, and must say that a published `offset` is a runtime precondition -
  usable only where an order source exists - not a promise that the field can page.
- [`django_strawberry_framework/resource_policy.py`][resource-policy] - correct
  `ResourcePolicy` and bounding-helper docstrings so returned/accepted-skip ceilings are not
  described as a total database scan guarantee. That rewrite must preserve the
  `execution_deadline_seconds` docstring's enumeration of cooperative seams, which names
  `bounded_rows` in both raw-list spellings; the helpers gain client coordinates in this card
  but do not stop being deadline seams, so the enumeration stays true rather than being
  rewritten around.
- [`docs/GLOSSARY.md`][glossary] (DB-backed) - update `DjangoListField`, `OrderSet`, and
  execution resource policy bodies. The card's three planned entries -
  [`ListArgumentError`][glossary-listargumenterror], the
  [list offset order precondition][glossary-list-offset-order-precondition], and the
  [async queryset completion adapter][glossary-async-queryset-completion-adapter] - already
  exist in the glossary DB with `planned for 0.0.15` status; their flip to `shipped` belongs
  to the joint cut, and Slice 5 only reconciles their bodies against the built behavior.
  Three reconciliations are already known. The adapter entry must scope its safety claim to
  framework-owned final queryset completion rather than to async safety generally. The
  `DjangoListField` entry gains the argument surface and the ordered-offset contract, and
  must not acquire stable/repeatable wording; its shipped nested-usage sentence stays.
  The offset-precondition entry states that a published `offset` is a runtime precondition
  rather than a per-field capability claim.
- [`docs/README.md`][docs-readme] - add the direct list pagination/order capability to the
  current shipped surface after the implementation lands.
- [`docs/TREE.md`][tree] - regenerate for any test-layout changes.
- [`examples/fakeshop/apps/kanban/constants.py`][fakeshop-kanban-constants] - regenerate after
  the new async live-test path is tracked; the card's predicted-path rows name that file.
- [`examples/fakeshop/test_query/README.md`][fakeshop-test-query-readme] - add BOTH new
  suites to the tier guide's suite enumeration and record the async module's shared-helper
  exemption, which that guide requires be stated outright rather than inferred from a missing
  row. The guide's GOVERNING paragraph must also be widened, not merely appended to: it
  currently says the only reason to leave
  [`examples/fakeshop/graphql_client.py`][fakeshop-graphql-client] is a raw request-envelope
  subject, and this card's async suite leaves it for EXECUTION COLOR instead. The rule becomes
  "use the shared helper unless the test specifically requires an async view/client boundary
  or a raw transport shape the helper cannot express", so future async feature suites inherit
  it rather than each arguing its own exception. This card adds its own rows only; the guide's
  pre-existing omission of ten other shipped suites is standing tier debt and is not silently
  absorbed here.
- [`README.md`][readme] - update the collection-field example if it enumerates list arguments.
- [`TODAY.md`][today] - **not touched, deliberately.** There is no waiting entry to move: the
  file mentions `offset` nowhere, and its "What products is still waiting for" section
  enumerates only [`Meta.fields_class`][glossary-metafields-class],
  [`Meta.search_fields`][glossary-metasearch-fields], and
  [`Meta.aggregate_class`][glossary-metaaggregate-class].
  `DjangoListField` appears once, in the sentence attributing capabilities that ship but are
  not exercised by products to the sibling apps, and this card's arguments do not falsify it.
  Card 051's parity close owns whatever `TODAY.md` prose the offset/limit gap eventually owes.
  A Slice 5 executor must not invent an edit to satisfy a checklist row.
- [`django_strawberry_framework/__init__.py`][package-init] and
  [`tests/base/test_init.py`][test-base-init] - the `ListArgumentError` root export and the
  pinned `__all__` tuple, star-import, and export-identity rows, plus the stale comment there
  asserting that the `0.0.15` cut leaves the public surface unchanged. The version literal and
  the version assertion in that same file are untouched and belong to card 053.
- KANBAN DB and generated exports - card 050's Scope sentence on universal argument
  publication and its `LIMIT`/`OFFSET` Definition-of-done row are AMENDED here (Decisions 2 and
  9), alongside ordinary card/spec state.
- [`CHANGELOG.md`][changelog] - not touched; card 053 and the maintainer own the joint
  release wording.

## Risks and open questions

*Preferred answers stay in the spec; fallbacks moved to the companion [rationale][rationale-risks].*

- **The card's universal-three-argument sentence conflicts with its Meta-derived-order
  requirement.** Preferred answer for `0.0.15`: the truthful conditional `orderBy` surface
  in Decision 2. *Fallback: see the [rationale][rationale-risks].*
- **GraphQL coercion errors cannot carry the package runtime code.** Preferred answer:
  Decision 10's honest split - all cases are `GraphQLError`, while only field-domain errors
  carry package extensions. *Fallback: see the [rationale][rationale-risks].*
- **Active order does not prove uniqueness, so the delivered contract is weaker than the
  words "stable subset" suggest.** Preferred answer: name the contract ORDERED OFFSET
  everywhere (Decision 7), require a visible order, document the unique-final-term
  recommendation, and sweep stable/repeatable wording out of the shipped docs rather than
  layering a caveat beside it. *Fallback: see the [rationale][rationale-risks].*
- **The sync early-exit cleanup contract is declined, not solved.** Preferred answer: promise
  leak-free early exit for async-only sources only, pin the declined sync behavior in a test,
  and say so in the Definition of done. *Fallback: see the [rationale][rationale-risks].*
- **Document collection-cost accounting and the runtime coordinate ceilings are two different
  budgets and now visibly disagree.** Preferred answer: describe the document charge as a
  schema-generic fixed estimate, state the accepted logical window bounds outright (Decision
  4), and change neither mechanism. *Fallback: see the [rationale][rationale-risks].*
- **Nested `DjangoListField` usage has a shipped glossary promise this card neither keeps nor
  retracts.** Preferred answer: preserve the no-argument nested behavior exactly, declare the
  new arguments unspecified in that position, and change nothing about the promise. *Fallback:
  see the [rationale][rationale-risks].*
- **`max_list_rows` may be too small as a migration offset ceiling.** Preferred answer:
  derive it as the card requests and gather real use. *Fallback: see the
  [rationale][rationale-risks].*
- **Ordering an already-sliced consumer queryset is a migration trap.** Preferred answer:
  preserve the shared sealed visibility boundary's fail-closed rejection before the hook,
  under active and omitted arguments alike. *Fallback: see the [rationale][rationale-risks].*
- **Arbitrary custom `OrderSet.apply_*` code can discard visibility predicates.** Preferred
  answer: mechanically reject unsafe output shapes and document the override as a trusted
  schema-author boundary that must transform the supplied sealed queryset. *Fallback: see the
  [rationale][rationale-risks].*
- **Django combined querysets do not compose uniformly with order and optimizer operations.**
  Preferred answer: reject every non-null argument on a combined source while preserving the
  all-null/omitted legacy branch. *Fallback: see the [rationale][rationale-risks].*

## Out of scope (explicitly tracked elsewhere)

- The other upstream parity gaps and typed connection argument rejections belong to
  [`TODO-ALPHA-051-0.0.15`][kanban].
- Debug-extension extraction belongs to [`TODO-ALPHA-052-0.0.15`][kanban].
- Boundary/DRY squeeze, the version literal, glossary status flip, and release wording belong
  to [`TODO-ALPHA-053-0.0.15`][kanban] / [`spec-053`][spec-053].
- The complete migration/adoption guide, including the mapping table in Decision 11,
  belongs to [`TODO-BETA-071-0.1.8`][kanban].
- Beta-release verification and the final parity claim belong to
  [`TODO-ALPHA-057-0.1.0`][kanban].
- Filtering/search arguments on `DjangoListField`, response envelopes, list `totalCount`,
  and nested raw-list windows are uncarded and deliberately not implied by this work.

## Definition of done

- [ ] Every `DjangoListField` publishes nullable optional `offset` and `limit`; targets with
      `Meta.orderset_class` also publish the shipped typed `orderBy` input.
- [ ] With all arguments omitted/null, sync resolver behavior, queryset low/high marks, SQL,
      query count, ordering, and response bytes match `0.0.14`; async data/query shape also
      matches while its result uses the required safe completion adapter; SDL gains arguments.
- [ ] Limit is accepted through the effective policy/field/trusted ceiling and rejected
      above it; offset is accepted through request `max_list_rows` and rejected above it.
- [ ] Negative and over-ceiling values raise `ListArgumentError` with stable extensions;
      active schema naming determines `argument`; actual GraphQL `Int` coercion failures
      perform no SQL, while integral float variables retain graphql-core's standard coercion.
- [ ] Nonzero offset requires a materially active `orderBy` or still-effective model
      `Meta.ordering` on the post-visibility queryset; empty/null order input, cleared or
      replaced model ordering, random ordering, grouping that suppresses the default, and
      opaque Python iterables cannot fake the condition. The shipped contract is stated as
      ORDERED OFFSET; no spec, docstring, glossary, or error text promises a stable or
      repeatable page, and a published `offset` is documented as a runtime precondition rather
      than a per-field pagination capability.
- [ ] Visibility runs before order; order runs before one combined slice; order permission
      failures occur before slicing.
- [ ] Public `OrderSet.apply_*` results are mechanically validated as unevaluated, unsliced,
      non-projection, non-combined, same-model/same-route plain querysets; custom overrides
      are documented as trusted to preserve the sealed input's predicates.
- [ ] The shared visibility boundary rejects a pre-sliced source before the hook and a sliced
      hook result afterward for both active and omitted arguments; the list field adds no
      parallel query-state classifier. Non-queryset/`None` sources follow the explicit
      limit/order contracts and never silently ignore `orderBy`.
- [ ] No pk tiebreaker and no `DISTINCT` are injected; to-many ordering preserves the shipped
      aggregate behavior.
- [ ] Querysets retain SQL `LIMIT/OFFSET`; sequences, iterables, and async-only iterables are
      bounded without over-consuming beyond the accepted window. Leak-free early-exit cleanup
      is promised for ASYNC-ONLY sources; a retained sync generator is documented and tested as
      still suspended after truncation, and the symmetric sync contract is deliberately
      deferred.
- [ ] Async queryset results complete over `AsyncDjangoGraphQLView` through an async-only
      adapter, with optimizer-on/off parity and no `DJANGO_ALLOW_ASYNC_UNSAFE` override.
- [ ] Live HTTP coverage exercises ordered paging, `orderBy`, visibility, cap interplay, and
      runtime/coercion errors under default and configured naming, plus both verdicts of the
      model-default order predicate, with wire-reachable async behavior in
      `examples/fakeshop/test_query/test_list_field_async_api.py`; package-only coverage is
      limited to construction, exact helper mechanics, and predicate states no live mount can
      construct.
- [ ] `ListArgumentError` is exported from the package root beside its two precedents, and
      the pinned `__all__`, star-import, and export-identity governance rows are updated with
      it; wire names are resolved only on the error path, proven by a zero-call converter
      assertion on successful requests.
- [ ] Card 050's universal-three-argument Scope sentence and its `LIMIT`/`OFFSET`
      Definition-of-done row are amended in the KANBAN database to the contracts this spec
      ships, rather than left contradicting them.
- [ ] The new async completion, model-order predicate, seal-axis, and argument-signature tests
      pass on the repository's existing CI matrix from the declared Django and Python floors
      through latest; a local single-interpreter run is evidence, not the contract.
- [ ] List-field docstring and shipped docs state the argument, cap, order-contract, and
      migration contracts.
- [ ] Full implementation suite passes at `fail_under = 100` with formatting and structural
      checks clean.
- [ ] No version literal, version assertion, package-version glossary row,
      [`pyproject.toml`][pyproject] / `uv.lock` pseudo-bump, or
      [`CHANGELOG.md`][changelog] entry is changed; card 053 owns the joint `0.0.15` cut.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../AGENTS.md
[changelog]: ../CHANGELOG.md
[goal]: ../GOAL.md
[kanban]: ../KANBAN.md
[pyproject]: ../pyproject.toml
[readme]: ../README.md
[today]: ../TODAY.md

<!-- docs/ -->

[docs-readme]: README.md
[glossary]: GLOSSARY.md
[glossary-async-queryset-completion-adapter]: GLOSSARY.md#async-queryset-completion-adapter
[glossary-async-sql-capture-boundary]: GLOSSARY.md#async-sql-capture-boundary
[glossary-configurationerror]: GLOSSARY.md#configurationerror
[glossary-connection-aware]: GLOSSARY.md#connection-aware-optimizer-planning
[glossary-cookbook-parity]: GLOSSARY.md#cookbook-parity
[glossary-djangoconnection]: GLOSSARY.md#djangoconnection
[glossary-djangoconnectionfield]: GLOSSARY.md#djangoconnectionfield
[glossary-djangographqlview]: GLOSSARY.md#djangographqlview
[glossary-djangolistfield]: GLOSSARY.md#djangolistfield
[glossary-djangooptimizerextension]: GLOSSARY.md#djangooptimizerextension
[glossary-djangoresourcepolicyextension]: GLOSSARY.md#djangoresourcepolicyextension
[glossary-djangotype]: GLOSSARY.md#djangotype
[glossary-execution-resource-policy]: GLOSSARY.md#execution-resource-policy
[glossary-fieldset]: GLOSSARY.md#fieldset
[glossary-finalize_django_types]: GLOSSARY.md#finalize_django_types
[glossary-get_queryset]: GLOSSARY.md#get_queryset-visibility-hook
[glossary-joint-version-cut]: GLOSSARY.md#joint-version-cut
[glossary-list-offset-order-precondition]: GLOSSARY.md#list-offset-order-precondition
[glossary-listargumenterror]: GLOSSARY.md#listargumenterror
[glossary-live-first]: GLOSSARY.md#live-first-coverage-mandate
[glossary-metaaggregate-class]: GLOSSARY.md#metaaggregate_class
[glossary-metafields]: GLOSSARY.md#metafields
[glossary-metafields-class]: GLOSSARY.md#metafields_class
[glossary-metafilterset-class]: GLOSSARY.md#metafilterset_class
[glossary-metamodel]: GLOSSARY.md#metamodel
[glossary-metaorderset_class]: GLOSSARY.md#metaorderset_class
[glossary-metasearch-fields]: GLOSSARY.md#metasearch_fields
[glossary-multi-database]: GLOSSARY.md#multi-database-cooperation
[glossary-order_input_type]: GLOSSARY.md#order_input_type
[glossary-ordering]: GLOSSARY.md#ordering
[glossary-orderset]: GLOSSARY.md#orderset
[glossary-pep-562-lazy-export]: GLOSSARY.md#pep-562-lazy-export
[glossary-probe-urlconf]: GLOSSARY.md#probe-urlconf
[glossary-production-error-policy]: GLOSSARY.md#production-error-policy
[glossary-relation-handling]: GLOSSARY.md#relation-handling
[glossary-resourcepolicy]: GLOSSARY.md#resourcepolicy
[glossary-schema-reload-discipline]: GLOSSARY.md#schema-reload-discipline
[glossary-sealed-execution-queryset]: GLOSSARY.md#sealed-execution-queryset
[glossary-seed-data]: GLOSSARY.md#seed_data
[glossary-strawberry_config]: GLOSSARY.md#strawberry_config
[glossary-structural-error-classification]: GLOSSARY.md#structural-error-classification
[glossary-testclient]: GLOSSARY.md#testclient
[glossary-visibility-boundary]: GLOSSARY.md#visibility-boundary
[next]: SPECS/NEXT.md
[rationale]: spec-050-list_field_arguments-0_0_15-rationale.md
[rationale-borrowing]: spec-050-list_field_arguments-0_0_15-rationale.md#borrowing-posture--what-was-deliberately-not-borrowed-and-why
[rationale-d1]: spec-050-list_field_arguments-0_0_15-rationale.md#decision-1--synthesize-one-resolver-signature-do-not-widen-consumer-resolvers
[rationale-d2]: spec-050-list_field_arguments-0_0_15-rationale.md#decision-2--sidecar-conditional-orderby-is-the-only-truthful-meta-first-surface
[rationale-d4]: spec-050-list_field_arguments-0_0_15-rationale.md#decision-4--max_list_rows-also-bounds-skip-trusted-widening-does-not
[rationale-d5]: spec-050-list_field_arguments-0_0_15-rationale.md#decision-5--validate-then-visibility-ordering-and-exactly-one-slice
[rationale-d6]: spec-050-list_field_arguments-0_0_15-rationale.md#decision-6--nonzero-offset-requires-a-materially-active-order
[rationale-d7]: spec-050-list_field_arguments-0_0_15-rationale.md#decision-7--active-order-is-not-total-order-no-pk-tiebreaker-is-appended
[rationale-d8]: spec-050-list_field_arguments-0_0_15-rationale.md#decision-8--queryset-and-iterable-sources-have-explicit-different-capabilities
[rationale-d9]: spec-050-list_field_arguments-0_0_15-rationale.md#decision-9--no-argument-sync-behavior-takes-the-old-branch-async-only-adapts-completion
[rationale-d10]: spec-050-list_field_arguments-0_0_15-rationale.md#decision-10--coercion-errors-stay-graphql-owned-runtime-domain-errors-are-package-owned
[rationale-d12]: spec-050-list_field_arguments-0_0_15-rationale.md#decision-12--the-version-bump-belongs-to-the-0015-joint-cut
[rationale-d13]: spec-050-list_field_arguments-0_0_15-rationale.md#decision-13--graphql-core-workarounds-have-a-dependency-owned-lifecycle
[rationale-risks]: spec-050-list_field_arguments-0_0_15-rationale.md#risks-and-open-questions--the-fallback-positions
[tree]: TREE.md

<!-- docs/SPECS/ -->
[spec-020]: SPECS/spec-020-list_field-0_0_7.md
[spec-028]: SPECS/spec-028-orders-0_0_8.md
[spec-030]: SPECS/spec-030-connection_field-0_0_9.md
[spec-047]: SPECS/spec-047-resource_policy-0_0_14.md
[spec-053]: SPECS/spec-053-boundary_dry_squeeze-0_0_15.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[conf]: ../django_strawberry_framework/conf.py
[connection]: ../django_strawberry_framework/connection.py
[exceptions]: ../django_strawberry_framework/exceptions.py
[list-field]: ../django_strawberry_framework/list_field.py
[optimizer-extension]: ../django_strawberry_framework/optimizer/extension.py
[orders-factories]: ../django_strawberry_framework/orders/factories.py
[orders-init]: ../django_strawberry_framework/orders/__init__.py
[orders-sets]: ../django_strawberry_framework/orders/sets.py
[package-init]: ../django_strawberry_framework/__init__.py
[querysets]: ../django_strawberry_framework/utils/querysets.py
[resource-policy]: ../django_strawberry_framework/resource_policy.py
[resource-policy-extension]: ../django_strawberry_framework/extensions/resource_policy.py
[types-resolvers]: ../django_strawberry_framework/types/resolvers.py
[typing-utils]: ../django_strawberry_framework/utils/typing.py

<!-- tests/ -->
[test-base-init]: ../tests/base/test_init.py
[test-list-field]: ../tests/test_list_field.py
[test-orders-sets]: ../tests/orders/test_sets.py
[test-querysets]: ../tests/utils/test_querysets.py
[test-resource-policy]: ../tests/test_resource_policy.py

<!-- examples/ -->
[fakeshop-graphql-client]: ../examples/fakeshop/graphql_client.py
[fakeshop-kanban-constants]: ../examples/fakeshop/apps/kanban/constants.py
[fakeshop-library-schema]: ../examples/fakeshop/apps/library/schema.py
[fakeshop-test-library]: ../examples/fakeshop/test_query/test_library_api.py
[fakeshop-test-multi-db]: ../examples/fakeshop/test_query/test_multi_db.py
[fakeshop-test-query-readme]: ../examples/fakeshop/test_query/README.md
[fakeshop-test-relations-async]: ../examples/fakeshop/test_query/test_relations_async_api.py
[fakeshop-test-resource-policy]: ../examples/fakeshop/test_query/test_resource_policy_api.py

<!-- scripts/ -->
[build-kanban-tracked-paths]: ../scripts/build_kanban_tracked_path_constants.py
[check-spec-glossary]: ../scripts/check_spec_glossary.py

<!-- .venv/ -->
[django-compiler]: ../.venv/lib/python3.14/site-packages/django/db/models/sql/compiler.py
[django-queryset]: ../.venv/lib/python3.14/site-packages/django/db/models/query.py
[graphql-execute]: ../.venv/lib/python3.14/site-packages/graphql/execution/execute.py
[graphql-scalars]: ../.venv/lib/python3.14/site-packages/graphql/type/scalars.py
[strawberry-info]: ../.venv/lib/python3.14/site-packages/strawberry/types/info.py
[strawberry-name-converter]: ../.venv/lib/python3.14/site-packages/strawberry/schema/name_converter.py

<!-- External -->
[cookbook-connection-field]: ../../django-graphene-filters/django_graphene_filters/connection_field.py
[cookbook-schema]: ../../django-graphene-filters/examples/cookbook/cookbook/recipes/schema.py
[upstream-graphene-fields]: ../../django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/fields.py
[upstream-strawberry-pagination]: ../../strawberry-django-main/strawberry_django/pagination.py
