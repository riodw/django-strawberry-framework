# Review - `docs/spec-030-connection_field-0_0_9.md` rev2

## Findings

### P1 - `ConnectionExtension` still breaks the planned sync/async dispatch

The revised spec keeps the `DjangoListField`-style runtime dispatch:
`DjangoConnectionField` has one default resolver that branches on
`in_async_context()`, returning `_apply_get_queryset_async(...)` on the async
path and `_apply_get_queryset_sync(...)` on the sync path. That works for
`DjangoListField` because there is no field extension between the resolver and
Strawberry's awaitable handling. It does not work through Strawberry's
`ConnectionExtension`.

`strawberry.relay.fields.py::ConnectionExtension.resolve` is the sync extension
path chosen when the resolver itself is a sync function. It calls
`next_(source, info, **kwargs)` and immediately passes the result to
`connection_type.resolve_connection(...)`; it does not check or await an
awaitable returned by a sync resolver. I verified this with a small
Strawberry-only connection field: a sync resolver that returns a coroutine under
`schema.execute(...)` reaches `ListConnection.resolve_connection` as a raw
coroutine, then fails and leaks an unawaited-coroutine warning.

So Decision 10 / Slice 2 cannot honestly say sync and async paths mirror
`DjangoListField` while also returning `relay.connection(...)` with the native
`ConnectionExtension`. Root-cause fix: either stop using
`relay.connection()` and install a package-owned connection field extension that
adds pagination args and handles `AwaitableOrValue` before slicing, or define a
different sync/async surface with separate resolver construction. A single
runtime-dispatched sync resolver plus Strawberry's native `ConnectionExtension`
is not viable.

### P1 - The optimizer helper still cannot plan `edges { node { ... } }`

Decision 11 fixes the earlier middleware-handoff bug by moving optimization
into the connection field before slicing, but it still claims useful root
planning against the existing flat walker. Passing `target_type` /
`target_model` directly is necessary, but not sufficient: the selected fields
for a connection root are still Relay wrapper fields like `edges`, `node`,
`pageInfo`, and `totalCount`.

`django_strawberry_framework/optimizer/walker.py::plan_optimizations` calls
`_walk_selections(...)`, which maps each selection name through
`snake_case(sel.name)` and looks it up in the target `DjangoTypeDefinition`
`field_map`. `edges` and `page_info` are not Django model fields, so the walker
skips them and never reaches `node { id name books { ... } }`. That means the
proposed helper will return an empty plan for the canonical live query unless
it first unwraps the connection selection down to the node selections.

The spec needs to choose one of two honest contracts:

- include a minimal root-connection selection adapter in this card that extracts
  `edges { node { ... } }` / relevant fragments and feeds the node selections
  into the existing flat walker; or
- state that root connection fields are functional but not optimizer-planned
  until `WIP-ALPHA-033-0.0.9`.

The current middle position, "root connection fields are planned, but
connection-aware planning is deferred," is not coherent with the existing
walker.

### P1 - `total_count: int` as an annotated field makes `resolve_connection` fail

Decision 4 and the Slice 1 checklist say the generated concrete connection
class declares `total_count: int`, attaches the captured count to a private
instance attribute, then delegates to `super().resolve_connection(...)`.
Implemented literally, this fails at runtime. A plain annotated Strawberry field
becomes a required `__init__` parameter, but
`strawberry.relay.types.py::ListConnection.resolve_connection` constructs
`cls(edges=..., page_info=...)` and does not pass `total_count`.

I verified the shape against Strawberry: a subclass with `total_count: int`
builds SDL with `totalCount`, then a query fails with
`__init__() missing 1 required keyword-only argument: 'total_count'`. A
resolver-backed field works:

```python
@strawberry.field
def total_count(self) -> int:
    return self._total_count
```

The spec should require `totalCount` to be a resolver-backed field (or require
the override to construct the connection instance itself with `total_count=...`
instead of delegating to `super()`). Given the instance-attribute design, the
resolver-backed field is the clean fit.

### P2 - Resolver signature synthesis must include the return annotation

Decision 6 now specifies synthesized `filter` / `order_by` parameters, but
`ConnectionExtension.apply` also validates the resolver return annotation. It
reads `field.base_resolver.signature.return_annotation`, unwraps optionals, and
requires the origin to be one of `Iterator`, `Iterable`, `AsyncIterator`, or
`AsyncIterable`. Missing return annotation, `Any`, or an unparameterized
`QuerySet` will raise `RelayWrongResolverAnnotationError` at schema build.

The synthesized signature therefore needs to include a valid return annotation
such as `Iterable[target_type]` for the sync wrapper and
`AsyncIterable[target_type]` for an async wrapper, even if the runtime value is a
Django `QuerySet`. It also needs the normal `root` / `info` annotations so
Strawberry does not raise missing-argument-annotation errors. Add this to
Decision 6 and the Slice 2 tests.

This finding intersects with the P1 async issue: if the final design replaces
`ConnectionExtension`, its validation rules may change, but the spec currently
commits to `relay.connection(...)`, so the native return-annotation constraint
must be spelled out.

### P2 - Default ordering is not enough for deterministic cursor pages

Decision 7 adds `order_by(pk)` only when `qs.ordered` is false. That fixes fully
unordered querysets, but it does not guarantee deterministic cursor pages. A
queryset ordered by a non-unique field, for example `name`, is marked ordered
while rows with the same `name` still have nondeterministic relative order.
Offset cursors over that order can skip or duplicate rows between requests
depending on database plan choices.

For cursor pagination, the package should enforce a total order. The practical
contract is to append the concrete primary-key `attname` as a final tie-breaker
for package-owned ordering paths when the pk is not already present:
sidecar `orderBy`, model `Meta.ordering`, and the default unordered case. For a
consumer resolver returning a pre-ordered queryset, either append the pk
tie-breaker as well or explicitly document that custom ordered querysets must
already be total orders. Add tests for duplicate ordered values, not just an
unordered queryset.

### P3 - Generated connection naming should use the GraphQL type name

The spec says generated classes are named `<TypeName>Connection`, but it does
not pin whether `<TypeName>` is the Python class name or
`DjangoTypeDefinition.graphql_type_name`. The latter is the correct source of
truth because `Meta.name` can rename the GraphQL type. A Python class
`InternalGenreType` with `Meta.name = "Genre"` should produce
`GenreConnection`, not `InternalGenreTypeConnection`.

Also note the runtime class-generation detail: subclassing a specialized
generic alias with `type("GenreConnection", (DjangoConnection[GenreType],), ...)`
does not work on Python; it requires `types.new_class(...)` or another
Strawberry-compatible generation path. That does not need to dominate the spec,
but the Slice 1 tests should include a generated class over a `Meta.name` type
so naming and generation are pinned.

## What looks solid

The rev2 spec correctly fixed the original false claims about Strawberry's
`first` + `last` guard, the static generic `totalCount` shape, context-stashed
counts, and the public export timing. The Meta-only API decision is also the
right call for `0.0.9`; it keeps the field aligned with the package's
DRF-shaped surface and avoids per-field connection-type variants.

## Validation run during review

- `uv run python scripts/check_spec_glossary.py --spec docs/spec-030-connection_field-0_0_9.md`
- Strawberry source inspection for `ConnectionExtension.apply`,
  `ConnectionExtension.resolve`, and `ListConnection.resolve_connection`.
- Small Strawberry-only probes for sync-resolver async execution,
  resolver-backed vs annotated `totalCount`, and generic connection naming.

I did not run pytest.
